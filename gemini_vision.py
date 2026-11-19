"""Wave 144: Gemini-vision photo reading (the photo system's
primary path).

Why this module exists
----------------------
Up to Wave 137 a photo question was read by Tesseract.js in
the browser (server OCR in ocr.py has no engine on the free
host). On a phone that flow breaks down in practice (see
ganitra-wave144-notes.md for the full diagnosis): the camera's
multi-MB original is first POSTed to /photo-ocr, whose 2 MB
cap answers "too_large" and the script STOPS — the browser
flow that could have read the photo locally never runs; and
even under the cap, the first Tesseract recognise() downloads
the wasm core plus the eng+hin traineddata from the CDN and
runs a heavy WASM OCR on a phone CPU.

Wave 144 makes a server-side VISION read the primary path:
the browser shrinks the photo (canvas, ~1600 px long edge,
JPEG) and POSTs it to /photo-vision; this module asks Gemini
to TRANSCRIBE the question — never to solve it. The text then
rides the exact Wave 137 discipline: it lands in the editable
composer (with the partial-read reconstruction + at most one
confirmation line when photofix finds an unclear slot) and
the student confirms or fixes it before anything is solved.
A vision failure of any kind degrades silently to the old
chain (server OCR -> browser Tesseract), exactly as a missing
Gemini key degrades the Wave-37 answer fallback.

Quota discipline
----------------
The vision model is gemini-3.1-flash-lite — a DIFFERENT model
bucket from the answer fallback's primary
(gemini-3-flash-preview), so photo reads never eat the
answer quota. (flash-lite is also the fallback chain's second
model; its bucket is shared with that rarely-hit second leg
only.) One model, no chain: a model-level failure here means
"vision unavailable right now" and the client falls back —
there is no second vision model to burn quota on.

Key handling
------------
The API key is read from the GANITRA_GEMINI_API_KEY
environment variable, the same variable and the same HTTP
helper (gemini_fallback._post_json, key in the x-goog-api-key
header) the answer fallback uses. The key is never hardcoded,
never logged, and the uploaded image bytes live only in
memory for the duration of the call — nothing is written to
disk anywhere in this module.

Wave 203 (photo audit, 20 Nov 2026)
-----------------------------------
The audit found the skeleton right but three small-mistake
gaps on this path; this module now closes its share:

* NOT_MATHS: a photo whose question is perfectly readable
  but NOT maths used to collapse into the same NO_QUESTION
  sentinel as a blurry photo, so the student was told "no
  question found" and invited to re-send forever. The prompt
  now asks for a distinct NOT_MATHS reply (sentinel line +
  the question copied verbatim), and transcribe_detailed()
  reports outcome "not_maths" with the read text, so the
  route can serve the maths-only one-liner in that text's
  flavour instead.
* Uncertainty channel: the prompt asks the model to flag
  any digit/character it is unsure of on a trailing
  "UNSURE: ..." line. The server strips the line from the
  transcription and hands the spans to the route, which
  turns the first into photofix's ONE confirmation line —
  a vision misread is never silently solved on a guess.
  A trailing "MORE: YES" line likewise reports that the
  photo held further questions beyond the first (the route
  adds the one-line notice; first-question-only stands).
* One retry: a VisionFailed (transport / timeout / API
  error / truncation) is retried ONCE against the same
  model before the route degrades to the OCR chain — the
  audit measured ~1 in 4 live calls failing this way. A
  clean NO_QUESTION / NOT_MATHS outcome and a quota 429
  are never retried (no second bucket is burned either:
  the retry is the same model).
"""
import base64
import re

import gemini_fallback as _gf

VISION_MODEL = "gemini-3.1-flash-lite"
TIMEOUT_SECONDS = 20
MAX_OUTPUT_TOKENS = 2048
NO_QUESTION = "NO_QUESTION"
NOT_MATHS = "NOT_MATHS"

_PROMPT = """You are the photo reader for Ganitra, a maths tutor for Indian school students. A student has photographed a maths question. Transcribe the question EXACTLY as written — do NOT solve it.

Rules:
- Copy the words and numbers exactly as they appear, in the same language and script as the photo (English, Hindi in Devanagari, or Hinglish in Roman letters).
- Write typeset maths in plain text: a fraction as (a)/(b), a square root as √(…), a power as x^2, pi as π.
- Do NOT solve the question, do NOT show any working, do NOT add any explanation or extra words.
- If the photo shows more than one question, transcribe only the FIRST complete question, and then add one last line: MORE: YES
- If any digit, number or character is blurry or unclear, still write your best reading of it in the transcription, and then add one last line: UNSURE: followed by each unsure number or word exactly as you wrote it, separated by commas. Add this line only when you are genuinely unsure about something.
- If the photo clearly shows a readable question but it is NOT a maths question (for example a history, science or language question), reply with NOT_MATHS on the first line, then copy that question exactly on the next line.
- If there is no maths question in the photo and no readable question either, or the photo is too blurry to read, reply with exactly this one word: NO_QUESTION"""


class VisionUnavailable(Exception):
    """No API key is configured — vision cannot run at all."""


class VisionQuota(Exception):
    """The vision model's free quota is exhausted (HTTP 429)."""


class VisionFailed(Exception):
    """Vision was reachable/configured but this read failed."""


def _post_json(url, payload, api_key, timeout):
    """One Gemini POST — a thin seam over the answer
    fallback's own HTTP helper (same header, same transport),
    kept module-level so tests can mock the whole HTTP layer
    without touching gemini_fallback."""
    return _gf._post_json(url, payload, api_key, timeout)


_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")
_LABEL = re.compile(
    r"^(transcription|question|prashn|प्रश्न)\s*[:\-]\s*",
    re.IGNORECASE)


def _clean_transcription(text):
    """Light cleanup of the model's reply: drop code fences
    and a leading 'Transcription:'-style label, unwrap one
    pair of surrounding quotes, collapse blank runs. The
    words and numbers themselves are never rewritten here —
    this is not OCR garble, so normalize_ocr_text's
    digit-fenced corrections do not apply."""
    text = (text or "").strip()
    if not text:
        return ""
    lines = []
    for raw in text.splitlines():
        line = _FENCE.sub("", raw).strip()
        line = _LABEL.sub("", line).strip()
        lines.append(line)
    text = "\n".join(lines).strip()
    if len(text) >= 2 and text[0] == text[-1] and \
            text[0] in ("\"", "'"):
        text = text[1:-1].strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_UNSURE_LINE = re.compile(r"^unsure\s*:\s*(.+)$", re.IGNORECASE)
_MORE_LINE = re.compile(r"^more\s*:\s*(yes|true|1)\b", re.IGNORECASE)
_NOT_MATHS_LINE = re.compile(r"^NOT_MATHS\b\s*[:\-—]?\s*(.*)$",
                             re.IGNORECASE)


def _outcome(outcome, text=None, read=None, unsure=(), more=False):
    return {"outcome": outcome, "text": text, "read": read,
            "unsure": list(unsure), "more": bool(more)}


def _parse_reply(text):
    """Split a cleaned model reply into the outcome dict.

    Sentinels (Wave 203): NO_QUESTION (nothing readable),
    NOT_MATHS as the first line (a readable non-maths
    question — its verbatim copy follows and rides along as
    `read`, for flavour detection only; it is never solved
    or prefilled). Trailer lines UNSURE: / MORE: are
    stripped from the transcription and reported on the
    side; with no trailers the outcome is exactly the
    pre-Wave-203 behaviour."""
    if not text or text.upper().startswith(NO_QUESTION):
        return _outcome("no_question")
    lines = text.split("\n")
    m = _NOT_MATHS_LINE.match(lines[0].strip())
    if m:
        rest = [m.group(1)] + lines[1:]
        read = "\n".join(rest).strip()
        return _outcome("not_maths", read=read or None)
    unsure, more = [], False
    while lines and lines[-1].strip():
        last = lines[-1].strip()
        um = _UNSURE_LINE.match(last)
        if um:
            unsure = [s.strip() for s in
                      re.split(r"[,|]", um.group(1)) if s.strip()]
            lines.pop()
            continue
        if _MORE_LINE.match(last):
            more = True
            lines.pop()
            continue
        break
    clean = "\n".join(lines).strip()
    if not clean:
        return _outcome("no_question")
    return _outcome("text", text=clean, unsure=unsure, more=more)


def _attempt(data, mime_type, api_key):
    """One vision POST, mapped to an outcome dict. Raises
    VisionQuota / VisionFailed — never a fake read."""
    payload = {
        "contents": [{"parts": [
            {"text": _PROMPT},
            {"inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(data).decode("ascii"),
            }},
        ]}],
        "generationConfig": {"temperature": 0,
                             "maxOutputTokens": MAX_OUTPUT_TOKENS},
    }
    try:
        response = _post_json(_gf._api_url(VISION_MODEL), payload,
                              api_key, TIMEOUT_SECONDS)
    except Exception as exc:
        if getattr(exc, "code", None) == 429:
            raise VisionQuota("gemini vision quota (429)") from exc
        raise VisionFailed(f"gemini vision transport: {exc!r}") \
            from exc
    if not isinstance(response, dict):
        raise VisionFailed("gemini vision: non-dict response")
    error = response.get("error")
    if isinstance(error, dict):
        if error.get("code") == 429:
            raise VisionQuota("gemini vision quota (429)")
        raise VisionFailed(
            f"gemini vision api error {error.get('code')}")
    if _gf._was_truncated(response):
        raise VisionFailed("gemini vision reply truncated")
    return _parse_reply(_clean_transcription(
        _gf._extract_text(response)))


def transcribe_detailed(data, mime_type):
    """Transcribe the question in one photo, with the full
    outcome: {"outcome": "text" | "no_question" |
    "not_maths", "text", "read", "unsure", "more"}.

    `data` is the raw image bytes (already magic-byte verified
    by the caller); `mime_type` its IANA type. Raises
    VisionUnavailable / VisionQuota / VisionFailed — the
    caller maps each to its fallback, never to a fake read.

    Wave 203: a VisionFailed is retried ONCE against the
    same model (same quota bucket) before it propagates —
    transport/timeout failures were ~1 in 4 live calls.
    Clean outcomes (text / no_question / not_maths) and
    VisionQuota are never retried."""
    import os
    api_key = (os.environ.get(_gf.ENV_KEY) or "").strip()
    if not api_key:
        raise VisionUnavailable("no Gemini API key configured")
    try:
        return _attempt(data, mime_type, api_key)
    except VisionFailed:
        return _attempt(data, mime_type, api_key)


def transcribe_image(data, mime_type):
    """The Wave-144 contract, kept: the cleaned transcription,
    or None when the model read the photo fine but found no
    readable maths question in it (no_question AND not_maths
    both map to None here — callers that need the split use
    transcribe_detailed)."""
    outcome = transcribe_detailed(data, mime_type)
    if outcome["outcome"] == "text":
        return outcome["text"]
    return None


__all__ = ["transcribe_image", "transcribe_detailed",
           "VISION_MODEL", "TIMEOUT_SECONDS",
           "MAX_OUTPUT_TOKENS", "NO_QUESTION", "NOT_MATHS",
           "VisionUnavailable", "VisionQuota", "VisionFailed"]
