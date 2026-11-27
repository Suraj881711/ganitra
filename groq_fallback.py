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

Wave 132: because the prompt and the shaping are shared,
this leg also speaks in GANITRA'S OWN VOICE — the shared
prompt instructs it, and the shared shaping runs the
reply through ganitra_voice.normalize_ai_text, so a Groq
reply is re-voiced into Ganitra's simple, normal language
and never served same-to-same (see gemini_fallback's
Wave 132 note).
"""
import json
import os
import urllib.request

from gemini_fallback import _build_prompt, _iter_sse_payloads, \
    _shape_result

MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
ENV_KEY = "GANITRA_GROQ_API_KEY"
TIMEOUT_SECONDS = 15
# Wave 119: the output-token budget. MODEL is a reasoning
# model whose reasoning counts toward this cap; the old 1024
# carried the same truncation risk fixed in gemini_fallback
# (a reply cut at the cap was served as if complete). 8192
# is a ceiling, not a target — a reply costs only the tokens
# it actually uses.
MAX_TOKENS = 8192


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


def try_groq_answer(question, lang=None, detail=False,
                    general=False):
    """Ask Groq to solve `question` and return a shaped
    Ganitra result dict — or None on ANY problem (no key,
    timeout, HTTP/API error, empty or non-maths reply). Never
    raises: the caller falls back to the Wave-18 answer.
    `detail` (Wave 136) selects the shared prompt's DETAIL
    variant; the default False is byte-identical to
    before. `general` (Wave 228, Deploy-71 fix) selects the
    shared GENERAL prompt (any topic, no NOT_MATHS rule)
    for the group name-call route."""
    question = str(question or "").strip()
    if not question:
        return None
    api_key = (os.environ.get(ENV_KEY) or "").strip()
    if not api_key:
        return None
    payload = {
        "model": MODEL,
        "messages": [{"role": "user",
                      "content": _build_prompt(
                          question, lang, detail=detail,
                          **({"general": True}
                             if general else {}))}],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
    }
    try:
        response = _post_json(API_URL, payload, api_key,
                              TIMEOUT_SECONDS)
    except Exception:
        return None
    if not isinstance(response, dict) or response.get("error"):
        return None
    # Wave 119: a reply the provider cut off at the token cap
    # (finish_reason "length") ends mid-answer — never serve
    # it; degrade to None exactly like any other failure.
    choices = response.get("choices") or []
    if choices and choices[0].get("finish_reason") == "length":
        return None
    return _shape_groq_result(_extract_text(response))


def _post_sse(url, payload, api_key, timeout):
    """One STREAMING POST of JSON with the key as a Bearer
    token. Returns the raw response object — the caller
    iterates its lines as they arrive. Raises on any
    transport or HTTP error before the stream opens, exactly
    like _post_json. Kept as a separate module-level function
    so tests can mock the whole HTTP layer."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("Authorization", f"Bearer {api_key}")
    return urllib.request.urlopen(request, timeout=timeout)


def stream_groq_answer(question, lang=None):
    """The streamed twin of try_groq_answer (Wave 131,
    transport only): same prompt, same payload plus
    "stream": true, same shaping (_shape_groq_result), same
    Wave-119 guard — a closing finish_reason of "length"
    means the reply was cut at the cap and is NEVER shaped
    or served.

    Yields reply-text pieces (str) as they arrive — only
    delta.content is accumulated, mirroring _extract_text's
    use of message.content (any reasoning fields a reasoning
    model streams alongside are ignored, as they are in the
    non-streamed reply). Returns (status, shaped) as the
    generator's return value, with the same status meanings
    as gemini_fallback.stream_gemini_answer ("ok" / "miss" /
    "truncated" / "error" / "unavailable"). Never raises."""
    question = str(question or "").strip()
    if not question:
        return ("unavailable", None)
    api_key = (os.environ.get(ENV_KEY) or "").strip()
    if not api_key:
        return ("unavailable", None)
    payload = {
        "model": MODEL,
        "messages": [{"role": "user",
                      "content": _build_prompt(question, lang)}],
        "temperature": 0.2,
        "max_tokens": MAX_TOKENS,
        "stream": True,
    }
    try:
        resp = _post_sse(API_URL, payload, api_key,
                         TIMEOUT_SECONDS)
    except Exception:
        return ("error", None)
    pieces = []
    try:
        for chunk in _iter_sse_payloads(resp):
            if not isinstance(chunk, dict) or chunk.get("error"):
                return ("error", None)
            choices = chunk.get("choices") or []
            if not choices:
                continue
            choice = choices[0] or {}
            delta = choice.get("delta") or {}
            content = delta.get("content")
            if isinstance(content, str) and content:
                pieces.append(content)
                yield content
            reason = choice.get("finish_reason")
            if reason == "length":
                # Wave 119: cut at the cap — never serve.
                return ("truncated", None)
            if reason:
                break
    except Exception:
        return ("error", None)
    finally:
        try:
            resp.close()
        except Exception:
            pass
    shaped = _shape_groq_result("".join(pieces))
    if shaped is None:
        return ("miss", None)
    return ("ok", shaped)


__all__ = ["try_groq_answer", "stream_groq_answer", "MODEL",
           "ENV_KEY", "TIMEOUT_SECONDS", "MAX_TOKENS"]
