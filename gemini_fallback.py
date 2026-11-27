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

Wave 41: the Wave-37 build hardcoded gemini-2.5-flash, which
Google has since gated OFF for new users (it returns 404 for
Suraj's key). MODELS is now an ordered chain of the models
verified working on his key: a model-level failure (HTTP
404/429/503, raised or returned as an error body) moves on to
the next model; any other failure (no key, timeout, a 400,
an unusable reply) still degrades silently to None exactly
as before.

Wave 119: the chain's primary model (gemini-3-flash-preview)
is a THINKING model — its reasoning tokens count against
maxOutputTokens. The Wave-37 cap of 1024 could be almost
entirely consumed by thinking (measured live 17 Nov 2026:
839-979 thoughts tokens for one worked answer), leaving a
few dozen tokens of visible answer, so replies arrived cut
mid-line ("Answer: Area = (1^2/2 -", "x = 0 and") and were
served as if complete — the app never looked at
finishReason. Two fixes: the budget is now
MAX_OUTPUT_TOKENS (8192), and a reply whose finishReason is
MAX_TOKENS is treated like a model failure — the chain moves
on, and if every model truncates, the honest fallback is
served instead of a cut answer.

Wave 132: GANITRA'S OWN VOICE. Suraj's standing rule
(17 Nov 2026): when Ganitra takes an answer from an AI, it
must give it in its OWN language — never the other AI's
answer same-to-same; Ganitra has its own separate, simple,
normal language. The prompt below now instructs that voice
explicitly (plain blackboard lines, simple everyday words,
no greetings/openers/closers, no self-reference, no
decoration), and _shape_result runs every reply through
ganitra_voice.normalize_ai_text — a deterministic
re-voicing pass that strips markdown and AI-isms, splits
walls of text into plain step lines and leaves the final
answer to be forced into the one "Answer: ..." line here.
The normalizer carries a hard invariant (it verifies,
per reply, that no maths value was lost or invented, and
declines to the raw text otherwise), so re-voicing can
never corrupt the working. All three legs share this
prompt and this shaping, so all three speak with the one
voice.

Wave 131: stream_gemini_answer below is the TRANSPORT-ONLY
streamed twin of try_gemini_answer — the same prompt, the
same payload, the same model chain and the same shaping
(_shape_result); the only difference is that the reply text
is yielded in pieces as the provider produces it, via the
streamGenerateContent SSE endpoint. It changes nothing
about WHAT is answered, only WHEN the pieces arrive.
"""
import json
import os
import re
import urllib.error
import urllib.request

from ganitra_voice import normalize_ai_text

# Wave 41: ordered model chain (see module docstring). The
# first model is tried first; a model-level failure moves to
# the next. MODEL stays as the primary for anything that
# imported it.
MODELS = ["gemini-3-flash-preview", "gemini-3.1-flash-lite"]
MODEL = MODELS[0]
_API_BASE = ("https://generativelanguage.googleapis.com/"
             "v1beta/models")
API_URL = f"{_API_BASE}/{MODEL}:generateContent"
ENV_KEY = "GANITRA_GEMINI_API_KEY"
TIMEOUT_SECONDS = 15
# Wave 119: the output-token budget (see the module
# docstring). A ceiling, not a target — a reply costs only
# the tokens it actually uses; the headroom exists so a
# thinking model's reasoning can never starve the visible
# worked answer the prompt demands.
MAX_OUTPUT_TOKENS = 8192

# HTTP statuses that mean "this MODEL cannot serve right now"
# (gated off / free-tier quota / transient overload) — the
# chain's cue to try the next model. Anything else (400 bad
# request, auth errors, timeouts) is not model-specific and
# keeps the old fail-silent behaviour.
_CHAIN_STATUSES = (404, 429, 503)

# Wave 131: the sentinel a streaming leg yields when it
# restarts on the next model AFTER some of its text was
# already shown — the consumer clears its live text before
# the new attempt's pieces arrive. One shared object, so
# every leg and the orchestrator (ai_stream) test identity.
STREAM_RESET = object()


def _api_url(model):
    return f"{_API_BASE}/{model}:generateContent"


def _is_model_failure(exc=None, response=None):
    """True when a failure is model-level: an HTTPError-style
    exception carrying a chain status, or an error body whose
    code is one."""
    if exc is not None:
        return getattr(exc, "code", None) in _CHAIN_STATUSES
    if isinstance(response, dict):
        error = response.get("error")
        if isinstance(error, dict):
            return error.get("code") in _CHAIN_STATUSES
    return False

_LANG_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "mr": "Marathi",
    "ta": "Tamil",
    "te": "Telugu",
    # Wave 107: an explicit "hinglish me samjhao" request is a
    # distinct instruction from Hindi — Roman script, not
    # Devanagari — so it gets its own prompt name.
    "hinglish": "Hinglish (Hindi written in Roman/English "
                "letters)",
}

# Wave 132: the prompt now instructs GANITRA'S OWN VOICE
# explicitly — the answer must read like Ganitra's own
# solver answers (a school teacher writing plainly on a
# blackboard), not like a chatbot. The deterministic
# normalizer in ganitra_voice.py (applied in _shape_result)
# is the guarantee behind this instruction; the prompt is
# the first line of discipline, not the only one.
_PROMPT = """You are the maths engine of Ganitra, a maths-only tutor for Indian school students (Classes 0-12, NCERT pattern).

Solve the student's question below, using the student's own numbers exactly as given.

Write the answer in Ganitra's own voice — the voice of a school teacher writing on a blackboard:
- Simple, normal words that a Class 6 student uses every day. Short plain lines, one step per line, the way the teacher writes the working on the board.
- No greetings and no openers: no "Sure", no "Of course", no "Certainly", no "Great question", no "Here is the solution", no "Let's solve". Start straight with the working.
- No closing lines: no "Hope this helps", no "Let me know", no "Happy learning". Stop at the answer.
- Never talk about yourself: no "As an AI", no "I will solve", no "we will see". Write only the steps.
- No headings, no markdown, no bullet points, no bold or italics, no emojis. No step numbers and no labels like "Step 1".
- Use small everyday words: "take" not "consider", "so" not "therefore", "find" not "determine".
- Maths only. If the question is not a maths question, reply with exactly this one word: NOT_MATHS
- Finish with exactly one last line in this form: Answer: <the final answer>
- Reply in the SAME language and the SAME script as the student's question. A Hindi question gets a Hindi answer, a Hinglish (Roman Hindi) question gets a Hinglish answer, an English question gets an English answer.
- Use simple notation: x^2 for squares, sqrt(x) for roots, / for division, and Rs for rupees when money is involved.{lang_line}{detail_block}

Student's question:
{question}"""

# Wave 136: the DETAIL variant's extra rules (see the module
# docstring). Inserted into the prompt only when the student
# explicitly asked for a long / detailed answer; every house
# rule above stays in force — Ganitra's own simple language,
# no openers or AI-isms, exactly one final Answer: line for
# the student's OWN question, in the student's language.
_DETAIL_RULES = (
    "\n- The student has asked for a DETAILED answer: break "
    "the working into smaller steps than usual."
    "\n- With each step, add a short reason — a few simple "
    "words after a dash — saying why that step is done."
    "\n- After the working, add one small example of the "
    "same type, worked in the same way. Write the example's "
    "result as a plain line, never in Answer: form — the "
    "one Answer: line at the end is only for the student's "
    "own question.")


# Wave 228 (Deploy-71 fix): the GENERAL prompt — the same
# voice, the same one-Answer-line format, but NO maths-only
# rule. It exists for exactly one caller shape: a group
# member who calls Ganitra BY NAME with a question on any
# topic (Suraj's 23 Nov 2026 group spec — a name-called
# question is answered for real). The maths prompt above
# orders a leg to reply NOT_MATHS to such a question, and
# _shape_result maps that sentinel to None, so under the
# maths prompt a healthy leg can NEVER answer a general
# question — the Deploy-71 live failure ("Ganitra, Bharat
# ki rajdhani kya hai?" -> the canned line, twice, with the
# legs alive) was this rule working as written, reached
# through a route whose tests had stubbed the legs with a
# double that answers capital questions. The 1:1 chain
# never uses this prompt: its legs keep the maths prompt
# and its NOT_MATHS discipline byte-identically.
_GENERAL_PROMPT = """You are Ganitra, a friendly tutor for Indian school students (Classes 0-12, NCERT pattern).

Answer the student's question below correctly. The question can be about ANY topic — general knowledge, science, language, history, geography, maths, anything. If it is a maths question, solve it using the student's own numbers exactly as given, showing the working in short plain lines.

Write the answer in Ganitra's own voice — the voice of a school teacher writing on a blackboard:
- Simple, normal words that a Class 6 student uses every day. Short plain lines.
- No greetings and no openers: no "Sure", no "Of course", no "Certainly", no "Great question", no "Here is the answer". Start straight with the answer.
- No closing lines: no "Hope this helps", no "Let me know". Stop at the answer.
- Never talk about yourself: no "As an AI". Write only the answer.
- No headings, no markdown, no bullet points, no bold or italics, no emojis.
- Keep it short: for a fact question, one or two lines are enough.
- Finish with exactly one last line in this form: Answer: <the final answer>
- Reply in the SAME language and the SAME script as the student's question. A Hindi question gets a Hindi answer, a Hinglish (Roman Hindi) question gets a Hinglish answer, an English question gets an English answer.{lang_line}

Student's question:
{question}"""


def _build_prompt(question, lang=None, detail=False,
                  general=False):
    name = _LANG_NAMES.get(str(lang or "").strip().lower())
    lang_line = (f"\n- The student's language is {name}; "
                 f"answer in {name}." if name else "")
    if general:
        # Wave 228 (Deploy-71 fix): the group name-call
        # route asks through the GENERAL prompt — the maths
        # prompt's NOT_MATHS rule makes every leg refuse a
        # general question by design, which is exactly the
        # live failure this variant exists to end.
        return _GENERAL_PROMPT.format(
            lang_line=lang_line, question=question)
    return _PROMPT.format(
        lang_line=lang_line,
        detail_block=_DETAIL_RULES if detail else "",
        question=question)


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


def _was_truncated(payload):
    """Wave 119: True when the model's reply was cut off by
    the output-token cap (finishReason MAX_TOKENS). Such a
    reply ends mid-line and must never be shaped and served
    as a complete answer."""
    for candidate in (payload or {}).get("candidates", []) or []:
        if candidate.get("finishReason") == "MAX_TOKENS":
            return True
    return False


# Wave 132: the answer-line patterns grew beyond the
# colon forms. AIs state the final answer in many dresses
# ("The final answer is X", "So, the answer is X",
# "उत्तर है X", "jawab hai X") — each must land in the one
# Ganitra final line, carrying the reply's OWN stated
# value, never a reworded one. The scan in _shape_result
# still takes the LAST matching line, exactly as before.
_ANSWER_LINE = re.compile(
    r"^\s*(?:"
    r"(?:the\s+)?(?:final\s+)?answer\s*(?:is\s+|[:\-–]\s*)"
    r"|(?:so|therefore|hence|thus),?\s+(?:the\s+)?"
    r"(?:final\s+)?answer\s+is\s+"
    r"|(?:final\s+)?jawab\s*(?:hai\s+|[:\-–]\s*)"
    r"|(?:अंतिम\s+)?उत्तर\s*(?:है\s+|[:\-–]\s*)"
    r")(.+?)\s*$",
    re.IGNORECASE)
# The value-in-the-middle forms: "Jawab 12 hai",
# "Answer 12 hai", "उत्तर 60 है" — the stated value sits
# before the closing hai/है, so they need their own
# pattern (checked alongside _ANSWER_LINE by
# _answer_value).
_ANSWER_HAI_LINE = re.compile(
    r"^\s*(?:jawab|answer|उत्तर)\s+(.+?)\s+"
    r"(?:hai|है)\s*[.!।]?\s*$",
    re.IGNORECASE)


def _answer_value(line):
    """The final answer stated on `line`, or None when the
    line states none — either pattern (the value-last
    forms of _ANSWER_LINE, or the value-in-the-middle
    hai/है forms)."""
    m = _ANSWER_LINE.match(line)
    if m:
        return m.group(1)
    m = _ANSWER_HAI_LINE.match(line)
    if m:
        return m.group(1)
    return None
_STEP_PREFIX = re.compile(
    r"^\s*(?:step\s*\d+\s*[:\.)\-]?\s*|\d+\s*[\.)]\s+|[-•*]\s+)",
    re.IGNORECASE)


def _clean_line(line):
    line = str(line or "").replace("**", "").replace("`", "")
    line = _STEP_PREFIX.sub("", line.strip())
    return line.strip()


def _tidy_answer(answer):
    """The final line's text, tidied: no trailing sentence
    stop ("." or "।") and no trailing copula (" hai" /
    " है") on a value-bearing answer — Ganitra's own final
    lines carry neither — and no surrounding whitespace."""
    answer = str(answer or "").strip()
    if len(answer) > 1 and answer.endswith(("।", ".")):
        answer = answer[:-1].strip()
    if any(ch.isdigit() for ch in answer):
        for tail in (" है", " hai"):
            if answer.lower().endswith(tail):
                answer = answer[:-len(tail)].strip()
                break
    return answer


def _shape_result(text):
    """Shape an AI leg's plain-text reply into a Ganitra
    result dict, or None when there is nothing usable
    (empty reply, a reply of pure dressing, or the
    NOT_MATHS sentinel — the caller then serves the old
    fallback instead).

    Wave 132: the raw reply is first re-voiced by
    ganitra_voice.normalize_ai_text (Ganitra's own voice —
    see that module), which also surfaces a NOT_MATHS
    sentinel hiding on its own line mid-reply. The
    extraction below then forces exactly one final line:
    the reply's own stated final answer, tidied."""
    text = (text or "").strip()
    if not text or text.upper().startswith("NOT_MATHS"):
        return None
    text = normalize_ai_text(text)
    if not text or text.upper().startswith("NOT_MATHS"):
        return None
    lines = [ln for ln in
             (_clean_line(raw) for raw in text.splitlines()) if ln]
    if not lines:
        return None
    answer = None
    for i in range(len(lines) - 1, -1, -1):
        stated = _answer_value(lines[i])
        if stated is not None:
            answer = stated.strip()
            lines = lines[:i] + lines[i + 1:]
            break
    if answer is None:
        answer = lines.pop()
    answer = _tidy_answer(answer)
    if not answer:
        return None
    # Wave 132: a step line that merely RESTATES the final
    # answer in answer-phrasing ("So, the answer is 5"
    # sitting above the "Answer: 5" line) is not a step —
    # the one final line already says it. A bare step that
    # happens to equal the answer ("x = 2" above
    # "Answer: x = 2") is a real last step and stays.
    steps = []
    for ln in lines:
        stated = _answer_value(ln)
        if stated is not None and \
                _tidy_answer(stated) == answer:
            continue
        steps.append(ln)
    return {
        "type": "Ganitra",
        "op": "gemini",
        "answer": answer,
        "steps": steps,
        "fallback": True,
        "fallback_kind": "gemini",
        "ai_generated": True,
    }


def try_gemini_answer(question, lang=None, detail=False,
                      general=False):
    """Ask Gemini to solve `question` and return a shaped
    Ganitra result dict — or None on ANY problem (no key,
    timeout, HTTP/API error, empty or non-maths reply). Never
    raises: the caller falls back to the Wave-18 answer.
    `detail` (Wave 136) selects the prompt's DETAIL variant
    for a student who explicitly asked for a long answer;
    the default False builds the prompt byte-identically to
    before. `general` (Wave 228, Deploy-71 fix) selects the
    GENERAL prompt (any topic, no NOT_MATHS rule) for the
    group name-call route; the default False is again
    byte-identical to before."""
    question = str(question or "").strip()
    if not question:
        return None
    api_key = (os.environ.get(ENV_KEY) or "").strip()
    if not api_key:
        return None
    _bkw = {"general": True} if general else {}
    payload = {
        "contents": [{"parts": [
            {"text": _build_prompt(question, lang,
                                   detail=detail, **_bkw)}]}],
        "generationConfig": {"temperature": 0.2,
                             "maxOutputTokens": MAX_OUTPUT_TOKENS},
    }
    # Wave 41: walk the model chain. A model-level failure
    # (404/429/503) tries the next model; every other failure
    # returns None at once, as Wave 37 did.
    for model in MODELS:
        try:
            response = _post_json(_api_url(model), payload,
                                  api_key, TIMEOUT_SECONDS)
        except Exception as exc:
            if _is_model_failure(exc=exc):
                continue
            return None
        if not isinstance(response, dict):
            return None
        if response.get("error"):
            if _is_model_failure(response=response):
                continue
            return None
        # Wave 119: a reply cut off by the token cap is not an
        # answer — move to the next model exactly like a
        # model-level failure. If every model truncates, the
        # loop ends in None and the caller serves the honest
        # Wave-18 fallback rather than a cut answer.
        if _was_truncated(response):
            continue
        return _shape_result(_extract_text(response))
    return None


def _stream_url(model):
    return f"{_API_BASE}/{model}:streamGenerateContent?alt=sse"


def _post_sse(url, payload, api_key, timeout):
    """One STREAMING POST of JSON with the key in the
    x-goog-api-key header. Returns the raw response object —
    the caller iterates its lines as they arrive. Raises on
    any transport or HTTP error before the stream opens (an
    HTTPError for a bad status, exactly like _post_json), so
    the model-chain rules apply unchanged. Kept as a separate
    module-level function so tests can mock the whole HTTP
    layer."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Content-Type", "application/json")
    request.add_header("x-goog-api-key", api_key)
    return urllib.request.urlopen(request, timeout=timeout)


def _iter_sse_payloads(resp):
    """Yield the parsed JSON object of every `data:` line of
    an SSE response, in arrival order. Blank lines, comment
    lines and the `data: [DONE]` terminator are skipped (the
    providers' events are one complete JSON object per data
    line). A data line that is not valid JSON raises
    ValueError — the caller treats a malformed stream like
    any other transport failure, exactly as _post_json's
    json.loads raising ends the non-streamed call."""
    for raw in resp:
        if isinstance(raw, (bytes, bytearray)):
            line = raw.decode("utf-8", "replace").strip()
        else:
            line = str(raw).strip()
        if not line or line.startswith(":"):
            continue
        if not line.startswith("data:"):
            continue
        data = line[len("data:"):].strip()
        if not data or data == "[DONE]":
            continue
        yield json.loads(data)


def _extract_delta(payload):
    """One streamed chunk's reply text — _extract_text's
    per-payload twin (every candidate's every part, in
    order), so the assembled stream is the same text the
    non-streamed call would have extracted."""
    parts = []
    for candidate in (payload or {}).get("candidates", []) or []:
        content = candidate.get("content", {}) or {}
        for part in content.get("parts", []) or []:
            text = part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


def _finish_reason(payload):
    for candidate in (payload or {}).get("candidates", []) or []:
        reason = candidate.get("finishReason")
        if reason:
            return reason
    return None


def stream_gemini_answer(question, lang=None):
    """The streamed twin of try_gemini_answer (Wave 131,
    transport only): same prompt, same payload, same model
    chain, same Wave-119 truncation guard, same shaping.

    Yields reply-text pieces (str) as the provider produces
    them. Yields STREAM_RESET when the chain restarts on the
    next model after pieces were already shown (a truncation
    — the only mid-stream restart this leg can make). Returns
    (status, shaped) as the generator's return value:

    - "ok"         clean finish; shaped is the result dict
                   _shape_result makes of the assembled text
                   (byte-identical to try_gemini_answer's
                   result for the same reply text);
    - "miss"       clean finish but nothing usable (empty
                   reply / NOT_MATHS) — like try_ returning
                   None from _shape_result, the leg ends at
                   once without trying the next model;
    - "truncated"  every model was cut at MAX_TOKENS;
    - "error"      a transport/HTTP failure that is not
                   model-level (the leg ends, as try_ does);
    - "unavailable" no key / no question.

    Never raises."""
    question = str(question or "").strip()
    if not question:
        return ("unavailable", None)
    api_key = (os.environ.get(ENV_KEY) or "").strip()
    if not api_key:
        return ("unavailable", None)
    payload = {
        "contents": [{"parts": [
            {"text": _build_prompt(question, lang)}]}],
        "generationConfig": {"temperature": 0.2,
                             "maxOutputTokens": MAX_OUTPUT_TOKENS},
    }
    shown = False
    last_status = "error"
    for model in MODELS:
        try:
            resp = _post_sse(_stream_url(model), payload,
                             api_key, TIMEOUT_SECONDS)
        except Exception as exc:
            if _is_model_failure(exc=exc):
                last_status = "error"
                continue
            return ("error", None)
        pieces = []
        truncated = False
        failure = None  # None | "chain" | "fatal"
        try:
            for chunk in _iter_sse_payloads(resp):
                if not isinstance(chunk, dict):
                    failure = "fatal"
                    break
                if chunk.get("error"):
                    failure = ("chain" if _is_model_failure(
                        response=chunk) else "fatal")
                    break
                text = _extract_delta(chunk)
                if text:
                    pieces.append(text)
                    shown = True
                    yield text
                reason = _finish_reason(chunk)
                if reason == "MAX_TOKENS":
                    truncated = True
                    break
                if reason:
                    break
        except Exception:
            failure = "fatal"
        finally:
            try:
                resp.close()
            except Exception:
                pass
        if failure == "fatal":
            return ("error", None)
        if failure == "chain":
            last_status = "error"
            if shown:
                yield STREAM_RESET
                shown = False
            continue
        if truncated:
            last_status = "truncated"
            if shown:
                yield STREAM_RESET
                shown = False
            continue
        shaped = _shape_result("".join(pieces))
        if shaped is None:
            return ("miss", None)
        return ("ok", shaped)
    return (last_status, None)


__all__ = ["try_gemini_answer", "stream_gemini_answer",
           "STREAM_RESET", "MODEL", "MODELS", "ENV_KEY",
           "TIMEOUT_SECONDS", "MAX_OUTPUT_TOKENS"]
