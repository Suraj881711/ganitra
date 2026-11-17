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
"""
import base64
import re

import gemini_fallback as _gf

VISION_MODEL = "gemini-3.1-flash-lite"
TIMEOUT_SECONDS = 20
MAX_OUTPUT_TOKENS = 2048
NO_QUESTION = "NO_QUESTION"

_PROMPT = """You are the photo reader for Ganitra, a maths tutor for Indian school students. A student has photographed a maths question. Transcribe the question EXACTLY as written — do NOT solve it.

Rules:
- Copy the words and numbers exactly as they appear, in the same language and script as the photo (English, Hindi in Devanagari, or Hinglish in Roman letters).
- Write typeset maths in plain text: a fraction as (a)/(b), a square root as √(…), a power as x^2, pi as π.
- Do NOT solve the question, do NOT show any working, do NOT add any explanation or extra words.
- If the photo shows more than one question, transcribe only the FIRST complete question.
- If there is no maths question in the photo, or the photo is too blurry to read, reply with exactly this one word: NO_QUESTION"""


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


def transcribe_image(data, mime_type):
    """Transcribe the maths question in one photo.

    `data` is the raw image bytes (already magic-byte verified
    by the caller); `mime_type` its IANA type. Returns the
    cleaned transcription, or None when the model read the
    photo fine but found no readable maths question in it.
    Raises VisionUnavailable / VisionQuota / VisionFailed —
    the caller maps each to its fallback, never to a fake
    read."""
    import os
    api_key = (os.environ.get(_gf.ENV_KEY) or "").strip()
    if not api_key:
        raise VisionUnavailable("no Gemini API key configured")
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
    text = _clean_transcription(_gf._extract_text(response))
    if not text or text.upper().startswith(NO_QUESTION):
        return None
    return text


__all__ = ["transcribe_image", "VISION_MODEL", "TIMEOUT_SECONDS",
           "MAX_OUTPUT_TOKENS", "NO_QUESTION",
           "VisionUnavailable", "VisionQuota", "VisionFailed"]
