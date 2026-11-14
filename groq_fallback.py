"""Wave 41: Groq — the SECOND free AI brain, behind Gemini.

Suraj's rule stands (14 Nov 2026): no paid AI. Wave 37 gave
Ganitra a Gemini (free tier) second brain for the questions
its own solver and honest layers cannot answer. This module
adds Groq (also free tier, verified working on Suraj's
account) as the next resort: fallback.py asks Gemini first
and consults Groq ONLY when Gemini returned None. A real
solver answer never reaches either module, and neither do
greetings, non-maths asks or science questions — those
layers return before this one is consulted (see fallback.py).

The live app calls Groq's OpenAI-compatible REST API
directly with the key from the GANITRA_GROQ_API_KEY
environment variable (set in the PythonAnywhere WSGI file,
the same pattern as GANITRA_GEMINI_API_KEY). No key, no
network, a timeout or an API error all degrade silently:
this module returns None and the previous Wave-18 fallback
is served unchanged.

The prompt and the result shaping are Gemini's own
(gemini_fallback._build_prompt / _shape_result), so both
brains speak in the same house style (Wave 24, FINAL):
plain solving lines — no step numbers, no labels — one
plain final answer line, the maths-only NOT_MATHS sentinel,
and the result flags set (fallback=True,
fallback_kind="groq", ai_generated=True).
"""
import json
import os
import urllib.request

from gemini_fallback import _build_prompt, _shape_result

MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
ENV_KEY = "GANITRA_GROQ_API_KEY"
TIMEOUT_SECONDS = 15


def _post_json(url, payload, api_key, timeout):
    """One POST of JSON with the key as a Bearer token.
    Returns the parsed response dict. Raises on any transport
    or HTTP error — the caller treats every raise as "Groq
    unavailable". Kept as a separate module-level function so
    tests can mock the whole HTTP layer."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_text(payload):
    """The assistant's reply text from an OpenAI-style
    chat-completions payload ("" when there is none)."""
    choices = (payload or {}).get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    return content.strip() if isinstance(content, str) else ""


def _shape_groq_result(text):
    """Shape Groq's plain-text reply exactly like a Gemini
    reply (same house style, same NOT_MATHS sentinel), then
    restamp the honesty flags for this provider."""
    shaped = _shape_result(text)
    if shaped is None:
        return None
    shaped = dict(shaped)
    shaped["op"] = "groq"
    shaped["fallback_kind"] = "groq"
    return shaped


def try_groq_answer(question, lang=None):
    """Ask Groq to solve `question` and return a shaped
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
        "model": MODEL,
        "messages": [{"role": "user",
                      "content": _build_prompt(question, lang)}],
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    try:
        response = _post_json(API_URL, payload, api_key,
                              TIMEOUT_SECONDS)
    except Exception:
        return None
    if not isinstance(response, dict) or response.get("error"):
        return None
    return _shape_groq_result(_extract_text(response))


__all__ = ["try_groq_answer", "MODEL", "ENV_KEY",
           "TIMEOUT_SECONDS"]
