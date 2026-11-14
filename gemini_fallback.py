"""Wave 37: the Gemini free-tier second brain.

Suraj's decision (14 Nov 2026): no paid AI ("paid kyu lena")
— Ganitra's own rule-based solver stays FIRST and exact, and
Google's Gemini (free tier) is asked ONLY when the solver and
the honest Wave-18 layers could not answer the student's own
question (fallback kinds "similar", "concept", "guide"). A
real solver answer never reaches this module, and neither do
greetings, non-maths asks or science questions — those layers
return before this one is consulted (see fallback.py).

The live app calls the Gemini REST API directly with the key
from the GANITRA_GEMINI_API_KEY environment variable (set in
the PythonAnywhere WSGI file, the same pattern as
GANITRA_SECRET_KEY). No key, no network, a timeout or an API
error all degrade silently to the previous Wave-18 fallback:
this module returns None and nothing about the old behaviour
changes.

House style for the answer (Wave 24, FINAL): plain solving
lines — no step numbers, no labels — and the final answer as
one plain final line. The prompt demands exactly that, and
_shape_result also strips numbering/markdown defensively, so
what reaches the renderers is shaped like every other Ganitra
answer ({type, op, answer, steps, ...}) with the honesty flags
set (fallback=True, fallback_kind="gemini", ai_generated=True).
"""
import json
import os
import re
import urllib.error
import urllib.request

MODEL = "gemini-2.5-flash"
API_URL = ("https://generativelanguage.googleapis.com/v1beta/"
           f"models/{MODEL}:generateContent")
ENV_KEY = "GANITRA_GEMINI_API_KEY"
TIMEOUT_SECONDS = 15

_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
}

_PROMPT = """You are the maths engine of Ganitra, a maths-only tutor for Indian school students (Classes 0-12, NCERT pattern).

Solve the student's question below, using the student's own numbers exactly as given.

Rules:
- Maths only. If the question is not a maths question, reply with exactly this one word: NOT_MATHS
- Show the working as plain lines, one step per line. No step numbers, no labels like "Step 1", no headings, no markdown, no bullet points, no bold or italics.
- Keep every line short and plain, the way a teacher writes on a board.
- Finish with exactly one last line in this form: Answer: <the final answer>
- Reply in the SAME language and the SAME script as the student's question. A Hindi question gets a Hindi answer, a Hinglish (Roman Hindi) question gets a Hinglish answer, an English question gets an English answer.
- Use simple notation: x^2 for squares, sqrt(x) for roots, / for division, and Rs for rupees when money is involved.{lang_line}

Student's question:
{question}"""


def _build_prompt(question, lang=None):
    name = _LANG_NAMES.get(str(lang or "").strip().lower())
    lang_line = (f"\n- The student's language is {name}; "
                 f"answer in {name}." if name else "")
    return _PROMPT.format(lang_line=lang_line, question=question)


def _post_json(url, payload, api_key, timeout):
    """One POST of JSON with the key in the x-goog-api-key
    header. Returns the parsed response dict. Raises on any
    transport or HTTP error — the caller treats every raise as
    "Gemini unavailable". Kept as a separate module-level
    function so tests can mock the whole HTTP layer."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("x-goog-api-key", api_key)
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_text(payload):
    parts = []
    for candidate in (payload or {}).get("candidates", []) or []:
        content = candidate.get("content", {}) or {}
        for part in content.get("parts", []) or []:
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts).strip()


_ANSWER_LINE = re.compile(
    r"^\s*(?:final\s+answer|answer|उत्तर|jawab)\s*[:\-–]\s*(.+)$",
    re.IGNORECASE)
_STEP_PREFIX = re.compile(
    r"^\s*(?:step\s*\d+\s*[:\.)\-]?\s*|\d+\s*[\.)]\s+|[-•*]\s+)",
    re.IGNORECASE)


def _clean_line(line):
    line = str(line or "").replace("**", "").replace("`", "")
    line = _STEP_PREFIX.sub("", line.strip())
    return line.strip()


def _shape_result(text):
    """Shape Gemini's plain-text reply into a Ganitra result
    dict, or None when there is nothing usable (empty reply, or
    the NOT_MATHS sentinel — the caller then serves the old
    fallback instead)."""
    text = (text or "").strip()
    if not text or text.upper().startswith("NOT_MATHS"):
        return None
    lines = [ln for ln in
             (_clean_line(raw) for raw in text.splitlines()) if ln]
    if not lines:
        return None
    answer = None
    for i in range(len(lines) - 1, -1, -1):
        m = _ANSWER_LINE.match(lines[i])
        if m:
            answer = m.group(1).strip()
            lines = lines[:i] + lines[i + 1:]
            break
    if answer is None:
        answer = lines.pop()
    if not answer:
        return None
    return {
        "type": "Ganitra",
        "op": "gemini",
        "answer": answer,
        "steps": lines,
        "fallback": True,
        "fallback_kind": "gemini",
        "ai_generated": True,
    }


def try_gemini_answer(question, lang=None):
    """Ask Gemini to solve `question` and return a shaped
    Ganitra result dict — or None on ANY problem (no key,
    timeout, HTTP/API error, empty or non-maths reply). Never
    raises: the caller falls back to the Wave-18 answer."""
    question = str(question or "").strip()
    if not question:
        return None
    api_key = (os.environ.get(ENV_KEY) or "").strip()
    if not api_key:
        return None
    payload = {
        "contents": [{"parts": [
            {"text": _build_prompt(question, lang)}]}],
        "generationConfig": {"temperature": 0.2,
                             "maxOutputTokens": 1024},
    }
    try:
        response = _post_json(API_URL, payload, api_key,
                              TIMEOUT_SECONDS)
    except Exception:
        return None
    if not isinstance(response, dict) or response.get("error"):
        return None
    return _shape_result(_extract_text(response))


__all__ = ["try_gemini_answer", "MODEL", "ENV_KEY",
           "TIMEOUT_SECONDS"]
