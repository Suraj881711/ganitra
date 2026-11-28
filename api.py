import os
import re
import time

from flask import Blueprint, Response, current_app, request, \
    jsonify, session, stream_with_context
from i18n import (LANG_NAMES, SPEECH_LANGS, advice_for,
                  explanation_for, get_strings, normalise_lang,
                  result_is_plain, result_unsolvable,
                  solve_failed, teach_for)
from langdetect_local import detect_detail_request, \
    detect_language_confident, detect_language_request
from context_ref import build_context_response, make_turn, \
    parse_context_ref
from detail import expand_detail
from doubt import build_doubt_response, parse_followup
from fallback import log_deferred_not_found, record_outcome, \
    with_fallback
from followups import w122_payload
from notation import annotate_method, annotate_result
from solver.answer_cache import get_negative, put_negative
from solver.methods import alternate_methods
from solver.router import solve_question
from speedups import methods_nonblocking

api_bp = Blueprint("api", __name__)

_HISTORY_LIMIT = 30
_QUESTION_LIMIT = 500

# Wave 227 (Suraj's screenshot case 6 + the external audit's
# DoS row): the 500-char line used to REJECT a pasted paper
# outright — "That question is a bit long, keep it under
# about 500 characters", again and again, for a student who
# had pasted a whole paper.  The solve pipeline itself
# splits a long paste part-wise (the multipart layer), so a
# long question is no longer refused: it flows into the
# solve and is answered part by part.  Only an absurd
# payload past this hard ceiling keeps the old too-long
# reply, purely as a payload-size guard.
_QUESTION_HARD_LIMIT = 8000

# Wave 227: a basic per-client rate limit for /api/solve —
# the audit found none at all.  At most this many solves per
# rolling minute per logged-in user (per IP when anonymous):
# a student never comes close, a hammering script is capped.
# The budget clock lives on the app instance, so every fresh
# app (each test run) starts clean.  Set the env var to 0 to
# disable.
_SOLVE_RATE_PER_MINUTE = int(
    os.environ.get("GANITRA_SOLVE_RATE_LIMIT", "300"))
_SOLVE_RATE_WINDOW = 60.0


def _solve_rate_limited():
    """True when this client has spent its per-minute solve
    budget.  Fail-open on any bookkeeping error: a limiter
    bug must never block a student's question."""
    if _SOLVE_RATE_PER_MINUTE <= 0:
        return False
    try:
        store = current_app.extensions.setdefault(
            "ganitra_solve_rate", {})
        key = session.get("user_id") or \
            request.remote_addr or "anonymous"
        now = time.monotonic()
        hits = [t for t in store.get(key, [])
                if now - t < _SOLVE_RATE_WINDOW]
        if len(hits) >= _SOLVE_RATE_PER_MINUTE:
            store[key] = hits
            return True
        hits.append(now)
        store[key] = hits
        return False
    except Exception:
        return False


def trimmed_history_entry(question, result):
    """Wave 46 (audit F4): the session-history copy of a solve.

    The /history page renders only the question and the final
    answer (templates/history.html reads e.question and
    e.result.answer), but entries used to store the FULL result
    dict — steps, latex, fallback payloads and all — so the
    client-side session cookie crossed the ~4,096 B browser
    limit after ~30 ordinary solves and the browser silently
    dropped it (the student looked logged out and lost history
    mid-session). Entries now keep exactly what the UI reads —
    question, answer, op, fallback_kind — in the same
    {"question": ..., "result": {...}} shape.

    session["last_result"] is NOT removed: /download and
    /solution/print read the full result (steps included) from
    it, so it is a real consumer, not a duplicate — the
    duplication disappears because history no longer carries a
    second full copy."""
    result = result or {}
    return {
        "question": question,
        "result": {
            "answer": result.get("answer", ""),
            "op": result.get("op", ""),
            "fallback_kind": result.get("fallback_kind"),
        },
    }


def _solve_friendly(question, lang=None, student_class=None,
                    lang_request=None, detail=False,
                    defer_ai=False):
    """Wave 5b: solve, and on failure gently re-ask once with a hint
    appended (same behaviour as the classic /solve route), so the
    chat never shows a raw solver failure when a small nudge fixes
    it. Returns the final result dict. (`lang`, Wave 67, is the
    UI/detected language forwarded to the fallback layer so the
    one-line not-found answer can use it. `student_class`,
    Wave 90, is forwarded the same way for the not-found
    learning log only. `lang_request`, Wave 107, is an explicit
    answer-language request from the message, forwarded to the
    fallback layer unchanged. `detail`, Wave 136, is an explicit
    long-answer request from the message: it selects the AI
    legs' DETAIL prompt variant inside the fallback layer and
    expands a deterministic answer with the topic's why block
    + one verified worked example (detail.expand_detail) —
    only ever when the student asked; the default False is
    byte-identical to before this wave.)

    Wave 18: the result then passes through the no-dead-end
    layer (fallback.with_fallback) — real solver answers come
    back untouched; failures, letter-soup "answers", soft
    non-answers, greetings and non-maths asks become an honest
    fallback answer instead of the error card.

    Wave 48: a question whose final outcome was a fallback
    answer is remembered in the answer cache's negative store
    for a few minutes — a Retry tap (or a classmate asking the
    same unsolved question) is then served the identical result
    instead of re-paying solve x2 + fallback layers every time.
    Real solver answers never enter that store; they keep the
    positive answer-cache behaviour inside solve_question.

    Wave 131: `defer_ai` is forwarded to with_fallback — the
    streaming endpoint's solves stop at the AI legs and come
    back with the chain's deferred marker instead of a
    finished answer (see api_solve_stream)."""
    # Wave 85: the step checker ("meri galti kahan hai"). A
    # message carrying the student's own working after a
    # Wave 212: the request clock starts here.  The whole
    # solve (native attempts + the fallback chain) is
    # bounded by one deadline — 38 s, a safety margin under
    # the browser's 45 s abort — so no question can spin
    # into a "Server is slow" any more (Suraj's phone test,
    # 21 Nov 2026).  The deadline is handed to the fallback
    # layer below via fallback.set_solve_deadline.
    _w212_t0 = time.monotonic()
    # "my solution:" marker is CHECKED against the solver's
    # solution instead of being solved as a question. The
    # gate is strict — marker + reference solve + checkable
    # working — and stepcheck returns None for everything
    # else, so the normal flow below is untouched.
    from stepcheck import step_check_result
    checked = step_check_result(question, lang=lang)
    if checked is not None:
        return checked
    # Wave 129: the same checker, reached the natural way —
    # "maine aise kiya hai, galti kahan hai?" with the working
    # in the same message, no marker line needed. galti only
    # splits the message and hands it to the unchanged Wave 85
    # machinery; no intent phrase or no usable steps -> None,
    # and the normal flow below is untouched.
    from galti import natural_check_result
    natural = natural_check_result(question, lang=lang)
    if natural is not None:
        return natural
    # Wave 147: the kind-tone pre-pass ("pyar se baat"). A
    # frustrated student's message is cleaned of exactly its
    # abusive words and the CLEANED text is solved, so the
    # answer is the polite question's answer, byte for byte,
    # with the abuse never mentioned; a message that is ONLY
    # venting earns one short kind line instead of the
    # not-found line. No abuse/frustration -> prepass returns
    # None and everything below is exactly the pre-Wave-147
    # flow. The step checkers above run first on purpose: a
    # "my solution:" message is checked as working even when
    # the student is annoyed. (Deploy-28 merge: the pre-pass
    # sits after BOTH step-check hooks — Wave 85's marker
    # check and Wave 129's natural check — and before the
    # negative cache, preserving Wave 147's design intent.)
    from tone import prepass as _tone_prepass
    _tone = _tone_prepass(question, lang_request=lang_request)
    if _tone is not None:
        if "result" in _tone:
            return _tone["result"]
        question = _tone["question"]
    # Wave 207: the PRACTICE-REQUEST intent (Wave 201) is
    # owned by the chat route (api_solve), which runs
    # practice_req.handle_message on the real session
    # before this function is ever called — that path is
    # unchanged.  But callers WITHOUT a chat session (the
    # audit harness, the test loop, any direct caller)
    # reach _solve_friendly straight, and a class-named
    # request ("class 10 ke practice questions do") fell
    # through to the practice-ADVICE card although the
    # matcher already parses it (live evidence: the route
    # serves op=practice_req in ~0.2 s).  A request that
    # NAMES its class needs no parked state, so it is
    # served here too — one-shot, through practice_req's
    # own handler on an ephemeral session, vetoes and all.
    # A request without a class still belongs to the
    # route's parked ask-which-class flow alone, and in
    # the route flow this block is unreachable (the route
    # returns the intent's payload first).
    try:
        import practice_req as _practice207
        _req207 = _practice207.parse_practice_request(
            question)
    except Exception:
        _req207 = None
    if _req207 is not None \
            and _req207.get("class_num") is not None:
        try:
            _pay207 = _practice207.handle_message(
                {}, None, None, question,
                lang=lang or "en",
                lang_request=lang_request,
                student_class=student_class)
        except Exception:
            _pay207 = None
        if _pay207 is not None \
                and _pay207.get("result") is not None:
            return _pay207["result"]
    # Wave 212: the NOTES-REQUEST intent (notes_req.py),
    # session-less path — mirrors the Wave-207 practice
    # hook above.  A request that NAMES its topic
    # ("trigonometry ke notes do") needs no parked state,
    # so direct callers (the audit harness, the test loop)
    # are served here too; a topic-less notes ask belongs
    # to the route's flow alone (it can fall back to the
    # chat's last topic there).
    try:
        import notes_req as _notes212
        _parsed212 = _notes212.parse_notes_request(question)
    except Exception:
        _parsed212 = None
    if _parsed212 is not None \
            and _parsed212.get("topic_query"):
        try:
            _pay212 = _notes212.handle_message(
                {}, None, None, question,
                lang=lang or "en",
                lang_request=lang_request,
                student_class=student_class)
        except Exception:
            _pay212 = None
        if _pay212 is not None \
                and _pay212.get("result") is not None:
            return _pay212["result"]
    # Wave 107: when the message carried an explicit language
    # request, the negative cache is keyed per request — a
    # fallback outcome's one-line texts are shaped by it, so
    # the same question asked with two different requests (or
    # with and without one) must not share one pinned outcome.
    # No request -> the plain pre-Wave-107 key, exactly as
    # before.
    # Wave 136: a detail outcome is a DIFFERENT (longer)
    # answer to the same question, so it is keyed apart the
    # same way — a plain ask never inherits a pinned detailed
    # outcome, and a detail ask never inherits the plain one.
    # No detail request -> the key is exactly the Wave-107
    # one.
    neg_variant = lang_request
    if detail:
        neg_variant = f"{lang_request or ''}|w136detail"
    cached = get_negative(question, variant=neg_variant)
    if cached is not None:
        return cached
    result = solve_question(question)
    if solve_failed(question, result):
        # Wave 212: the hint re-ask is a second full solver
        # budget (10 s) — it is skipped when the first
        # attempt already ate most of the request budget,
        # so the fallback chain keeps its share.
        if time.monotonic() - _w212_t0 < 12.0:
            retry = solve_question(
                f"{question} find the value")
            if not solve_failed(question, retry):
                result = retry
    # Wave 136: the detail flag rides along ONLY when it is
    # on, so with detail off this call is byte-identical to
    # before the wave — the pre-136 test doubles for
    # with_fallback (e.g. Wave 48's, which predate the
    # detail parameter) keep working unchanged. Wave 131:
    # the defer_ai flag follows the same discipline — it is
    # passed only on the streaming path, so the classic call
    # stays byte-identical to the pre-131 one (test_wave48
    # caught exactly that).
    extra = {}
    if detail:
        extra["detail"] = True
    if defer_ai:
        extra["defer_ai"] = True
    # Wave 212: hand the chain the request deadline (38 s
    # from the request start).  Set via the fallback
    # module's own setter so the with_fallback call below
    # keeps its exact pre-Wave-212 signature for every
    # existing test double.
    try:
        import fallback as _fallback212
        _fallback212.set_solve_deadline(_w212_t0 + 38.0)
    except Exception:
        pass
    result = with_fallback(question, result, lang=lang,
                           student_class=student_class,
                           lang_request=lang_request,
                           **extra)
    if detail:
        # Wave 136: expand AFTER the fallback layer (so the
        # Live Bank, recorded inside with_fallback, stores
        # the plain outcome) and BEFORE the negative cache
        # files this outcome under the detail key.
        result = expand_detail(question, result, lang=lang,
                               lang_request=lang_request)
    # Wave 131: a deferred-AI marker is not an outcome — the
    # streaming layer writes the negative cache itself once
    # the AI legs have answered or missed, with the FINAL
    # result. Every finished outcome is cached exactly as
    # before.
    if not (isinstance(result, dict)
            and result.get("ai_deferred")):
        put_negative(question, result, variant=neg_variant)
    return result


# --- Wave 68: the opening framing line ---------------------------------
# The chat card used to open with the i18n "explanation"
# sentence, which merely restates the final answer ("The
# final answer is X — follow the steps above") — so the
# answer appeared twice and the card opened with clutter.
# Wave 68 replaces it with the solver's OWN first step when
# that step is a givens/framing line of a word problem
# ("Let the original speed be x km/h…", "Cost price (CP) =
# Rs 800, selling price (SP) = Rs 920"): the line that says
# what is given and what is being set up, in the solver's
# own words — never paraphrased, never invented. Bare
# computations get no intro; their first step IS the work.

_WORD_TYPES = {"applied", "word_problem"}


def _intro_for(result, question):
    """The framing first step of a solved word problem, or
    None. Conservative on purpose: a real solve only (never
    a fallback result), at least two steps (the intro is
    lifted OUT of the steps list in the chat, so the working
    must remain), a word-problem shape, and a first step
    that is a "Let …" / "Given …" framing or a clean list
    of labelled assignments whose values contain no
    computation."""
    if not isinstance(result, dict):
        return None
    if result.get("fallback") or result.get("fallback_kind"):
        return None
    steps = result.get("steps") or []
    if len(steps) < 2:
        return None
    first = str(steps[0]).strip()
    if not first or len(first) > 180:
        return None
    if result.get("type") not in _WORD_TYPES \
            and len(str(question or "").split()) < 6:
        return None
    if first.startswith(("Let ", "Given ")):
        return first
    parts = first.split(", ")
    if len(parts) <= 4 and all(
            re.match(r"^[^=]+=[^=]+$", p) for p in parts) \
            and not any(mark in first
                        for mark in ("×", "÷", "·")) \
            and not re.search(r"\d\s*[-+]\s*\d", first):
        # No computed value either: "Add all values: 3 + 6 +
        # 9 + 12 = 30" is a working step, not a givens line.
        return first
    return None


# --- Wave 9: auto language ---------------------------------------------
# The site language stays English by default; when a chat message is
# solidly detected in another supported language, the session
# language switches to it automatically and THIS response is already
# rendered in the new language. Every response gains
# language_switched/language; on a switch it also carries `ui` (the
# chat page's strings in the new language, so the client can re-skin
# without a reload). Wave 139 (Suraj's order): the switch is
# SILENT — the localised `lang_notice` toast line Wave 9 added
# here is removed; nothing announces the change to the student. A
# manual language pick is never overridden by anything except a
# later chat message in yet another language.

_UI_PREFIXES = ("js_", "error_", "chat_", "nav_")
_UI_EXTRA_KEYS = {
    "explanation_heading", "advice_heading",
    "listen_btn", "listen_stop_btn", "handwriting_btn",
    "print_copy_link", "question_placeholder", "enter_question",
    "chat_guided",
    "solve_btn", "voice_btn", "voice_call_btn", "voice_call_end",
    "photo_btn", "lang_label", "menu_label",
    "chat_waking_note",
    "flash_too_long", "chat_empty_sub", "chat_welcome",
    "chat_greeting_plain", "saathi_welcome_name",
}


def _lang_fields(lang, strings, switched):
    """The Wave-9 fields added to every /api/solve response."""
    fields = {"language_switched": bool(switched), "language": lang}
    if switched:
        ui = {k: v for k, v in strings.items()
              if k.startswith(_UI_PREFIXES) or k in _UI_EXTRA_KEYS}
        ui["speech_lang"] = SPEECH_LANGS[lang]
        fields["ui"] = ui
        # Wave 139: no `lang_notice` — the switch is never announced.
    return fields


# --- Wave 17b: JSON type guards (pen-test F2) ---------------------------
# A non-string "question"/"method" (int, list, dict, bool) used to
# crash .strip() into an HTTP 500, and a non-object JSON body did
# the same to .get(). The rule now: a body that is not a JSON
# object, or a field that is present but not a string, is a
# friendly HTTP 400 — never a 500. A missing/null field keeps the
# old behaviour (treated as empty).

def _json_object():
    """The request's JSON body as a dict: {} when there is no
    usable body at all, None when a body WAS sent but is not a
    JSON object."""
    data = request.get_json(silent=True)
    if data is None:
        return {}
    return data if isinstance(data, dict) else None


def _json_str(data, field):
    """data[field] as text: missing/null -> "", a string ->
    itself, anything else -> None (the caller answers 400)."""
    value = data.get(field)
    if value is None:
        return ""
    return value if isinstance(value, str) else None


def _methods_localised(question, result, lang_request):
    """Wave 130: the alternate-method payload with its steps
    rendered in an explicitly requested language. Methods are
    generated in English (solver/methods.py); a Hindi or
    Hinglish request relanguages their boilerplate lines (and,
    for Hindi, the method labels) through steplang — the same
    template layer that fixes the main steps. No request (or
    an English one) returns the payload exactly as computed.
    Guarded like every other hook: any failure leaves the
    methods untouched."""
    methods = methods_nonblocking(question, result)
    if lang_request in ("hi", "hinglish"):
        try:
            from steplang import relanguage_methods
            methods = relanguage_methods(methods, lang_request)
        except Exception:
            pass
    return methods


# --- Wave 127: per-chat solved-turn log --------------------------------
# The context resolver (context_ref.py) answers references to
# earlier turns ("uska answer batao", "usi ka ek aur example
# do") from a small log of THIS chat's solved turns, kept in
# the session next to last_result/history. The chat page sends
# its chat id with every solve (Wave 11 chats), so the log is
# namespaced per chat — references never cross chats. A caller
# that sends no chat id (the classic flows, tests) shares the
# "default" bucket, exactly the scoping Wave 96's doubt layer
# has always had. Entries are trimmed like history entries
# (question + final answer + type/op/topic) because the log
# rides in the session cookie; only the LAST turn's full
# result lives in session["last_result"], as before.

_CTX_TURNS_PER_CHAT = 8
_CTX_CHATS_KEPT = 3


def _chat_key(data):
    """The context-log bucket for this request: "c<id>" when
    the body carries a usable chat id, else "default"."""
    raw = data.get("chat_id")
    if isinstance(raw, bool):
        return "default"
    if isinstance(raw, int) and raw > 0:
        return f"c{raw}"
    if isinstance(raw, str) and raw.strip().isdigit() \
            and int(raw.strip()) > 0:
        return f"c{int(raw.strip())}"
    return "default"


def _ctx_turns(chat_key):
    """This chat's solved-turn log (oldest first)."""
    store = session.get("ctx_turns")
    if not isinstance(store, dict):
        return []
    turns = store.get(chat_key)
    return turns if isinstance(turns, list) else []


def _ctx_record(chat_key, question, result):
    """Append a fresh solve to the chat's turn log. Only real
    answers are recorded — plain one-liners (not-found, maths-
    only guard, greetings) and solver errors are not turns a
    student can point back at."""
    if not isinstance(result, dict):
        return
    if result.get("op") == "error" or result.get("plain"):
        return
    if result.get("fallback_kind") not in (None, "concept"):
        return
    if not str(result.get("answer", "") or "").strip():
        return
    store = session.get("ctx_turns")
    if not isinstance(store, dict):
        store = {}
    turns = store.get(chat_key)
    if not isinstance(turns, list):
        turns = []
    turns.append(make_turn(question, result))
    store[chat_key] = turns[-_CTX_TURNS_PER_CHAT:]
    # Keep only the most recently used chat buckets (cookie).
    while len(store) > _CTX_CHATS_KEPT:
        store.pop(next(iter(store)))
    session["ctx_turns"] = store


@api_bp.post("/solve")
def api_solve():
    data = _json_object()
    lang = normalise_lang(session.get("lang", "en"))
    strings = get_strings(lang)
    if data is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = _json_str(data, "question")
    if question is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = question.strip()
    if not question:
        # Wave 5b: friendly localised message, never a bare error.
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)})
    if len(question) > _QUESTION_HARD_LIMIT:
        return jsonify({"ok": False,
                        "message": strings["flash_too_long"],
                        **_lang_fields(lang, strings, False)})
    # Wave 227: a paste between the old 500-char line and the
    # hard ceiling is NOT refused any more — it flows into
    # the solve below, whose multipart layer splits it and
    # solves it part-wise (screenshot case 6).
    if _solve_rate_limited():
        return jsonify({"ok": False,
                        # Wave 233: localised (was a hard-coded
                        # English line — it renders as a chat
                        # bubble, so it follows the language).
                        "message": strings["api_rate_limited"],
                        **_lang_fields(lang, strings,
                                        False)}), 429

    # Wave 216: per-chat follow-up anchoring. If the session's
    # last_result belongs to a DIFFERENT chat than this request,
    # restore this chat's anchor (silently re-solve its last
    # question) or clear the slot when this chat has solved
    # nothing yet — a follow-up must never point at another
    # chat's answer. Runs before every layer that reads
    # last_result (chips, doubt, context, human brain).
    _w216_key = _chat_key(data)
    if _w216_key != session.get("last_result_chat"):
        _w216_q = (session.get("anchor_by_chat") or {}).get(
            _w216_key)
        _w216_restored = None
        if _w216_q:
            try:
                _w216_restored = _solve_friendly(
                    _w216_q, lang=lang,
                    student_class=session.get("saathi_class"))
            except Exception:
                _w216_restored = None
        if isinstance(_w216_restored, dict) and \
                _w216_restored.get("answer"):
            session["last_question"] = _w216_q
            session["last_result"] = _w216_restored
        else:
            session.pop("last_question", None)
            session.pop("last_result", None)
        session.pop("doubt_step", None)
        session["last_result_chat"] = _w216_key

    # Wave 220: if the session still holds no usable anchor
    # for this chat (the browser dropped the cookie state —
    # see _restore_anchor_from_db), rebuild it from the chat's
    # saved thread before any follow-up layer reads it.
    _w220_lr = session.get("last_result")
    if not (session.get("last_question")
            and isinstance(_w220_lr, dict)
            and _w220_lr.get("answer")):
        _restore_anchor_from_db(_w216_key)

    # Wave 122: a follow-up chip tap (see followups.py). The
    # visible message is only the chip's label; the kind and
    # the ORIGINAL question ride as hidden context fields, and
    # the answer is built deterministically from the session's
    # last solution. This runs BEFORE the Wave-9 language
    # detection on purpose: a chip label ("Give one more
    # example") is not a new question and must never switch the
    # session language or be solved as one. When there is no
    # honest follow-up (no solved last answer, no perturbation
    # solves, no simpler route), build_followup_response
    # returns None and the normal path below answers the label
    # text as an ordinary message — the honest one-liner.
    followup_kind = _json_str(data, "followup") or ""
    if followup_kind in ("example", "test", "simpler"):
        from followups import build_followup_response
        context_question = _json_str(data, "context_question") \
            or ""
        built = build_followup_response(
            followup_kind, context_question,
            session.get("last_result"),
            session.get("last_question"),
            lang=lang,
            student_class=session.get("saathi_class"))
        if built is not None:
            result, fu_note, fu_advice, fu_new_question = built
            if fu_new_question:
                # The example IS a fresh solve of a new
                # question: it becomes the last solution, so a
                # doubt follow-up after it points at the
                # example, exactly as after a typed question.
                session["last_question"] = fu_new_question
                session["last_result"] = result
                _note_anchor(_chat_key(data), fu_new_question)
                session.pop("doubt_step", None)
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                "result": result,
                "intro": None,
                "followup_note": fu_note,
                "explanation": explanation_for(result, lang),
                "advice": (fu_advice if fu_advice is not None
                           else advice_for(result, lang)),
                "methods": (methods_nonblocking(fu_new_question,
                                                result)
                            if fu_new_question else []),
                "teach": teach_for(result, lang),
                # Wave 123: a chip-thread answer keeps its
                # chips (followup=True); its step-label gate
                # reads the ORIGINAL question, so a thread
                # that began with "step by step" stays
                # labelled and a plain thread stays plain.
                "w122": w122_payload(
                    result, lang=lang,
                    question=fu_new_question or context_question,
                    ask_text=context_question
                    or session.get("last_question") or "",
                    followup=True),
                **_lang_fields(lang, strings, False),
            })

    # Wave 9: auto language — detect from the question itself. A
    # solid detection in a different language moves the session to
    # that language BEFORE solving, so the answer, explanation,
    # advice and any error card below are all in the new language.
    # Wave 107 (Suraj, 17 Nov 2026): an explicit language request
    # inside the message ("answer in Hindi", "hindi me batao",
    # "हिंदी में जवाब दो") outranks detection — the answer comes
    # in the REQUESTED language whatever the question's language
    # is. The request phrase is stripped from the text that is
    # solved (solve_text), so it can never pollute the solver,
    # the bank's exact match or the fallback layers; the
    # student's original message is still what history, the
    # doubt follow-up and the response echo carry. A Hinglish
    # request maps to the "hi" session language (the same place
    # a Hinglish question lands today) and rides to the fallback
    # layer as lang_request="hinglish" so its one-line replies
    # and the AI prompt use Roman Hindi, not Devanagari.
    lang_request = None
    solve_text = question
    req = detect_language_request(question)
    if req is not None:
        lang_request, req_cleaned = req
        if req_cleaned:
            solve_text = req_cleaned
        req_lang = ("hi" if lang_request in ("hi", "hinglish")
                    else "en")
        switched = req_lang != lang
        if switched:
            lang = req_lang
            session["lang"] = lang
            strings = get_strings(lang)
    else:
        detected, solid = detect_language_confident(question)
        switched = False
        if solid and detected != lang:
            lang = detected
            session["lang"] = lang
            strings = get_strings(lang)
            switched = True
    fields = _lang_fields(lang, strings, switched)

    # Wave 214 (human brain, phase 1): meaning-first
    # normalisation of the text that gets solved — the word
    # "degree" becomes "°" and conversational filler tails
    # ("ka value kya hai", "kitna hoga") are stripped, so a
    # question asked the way a student SPEAKS it reaches the
    # solver the way a human listener would hand it over. The
    # student's original message (history, echoes) is untouched;
    # texts without those patterns come back byte-identical.
    from human_brain import normalize_human_text
    solve_text = normalize_human_text(solve_text)

    # Wave 124: chat-based test / exam (chat_test.py). A test
    # request starts a per-chat test; while one is active in
    # THIS chat, every later message belongs to the test flow
    # (an answer attempt, or a skip / stop / answer-batao /
    # solve-karke-do command) until the test ends. This runs
    # AFTER the language detection above (the whole test
    # follows the student's language, incl. the Wave-107
    # override) and BEFORE the Wave-96 doubt block (mid-test,
    # a message is an answer attempt, never a step doubt —
    # the documented rule). The chat id rides in the request
    # body (Wave 124 added it to the client's two /api/solve
    # posts); state is keyed by (user, chat), so a test never
    # leaks into another chat of the same student.
    _ct_raw = data.get("chat_id")
    chat_id = str(_ct_raw) if isinstance(_ct_raw, (str, int)) \
        and str(_ct_raw) != "" else None
    import chat_test
    ct_payload = chat_test.handle_message(
        session, session.get("user_id"), chat_id, question,
        lang=lang, lang_request=lang_request,
        student_class=session.get("saathi_class"),
        solve_fn=lambda q: _solve_friendly(
            q, lang=lang,
            student_class=session.get("saathi_class"),
            lang_request=lang_request))
    if ct_payload is not None:
        ct_result = ct_payload["result"]
        if ct_payload.pop("w124_set_last", False):
            # The solve-command card IS a fresh solve of the
            # test question: it becomes the last solution, so
            # a doubt follow-up after the test points at it.
            session["last_question"] = ct_payload.pop(
                "w124_solved_question", question)
            session["last_result"] = ct_result
            _note_anchor(_chat_key(data),
                         session["last_question"])
            session.pop("doubt_step", None)
        else:
            ct_payload.pop("w124_solved_question", None)
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                ct_result))
        session["history"] = history[:_HISTORY_LIMIT]
        # Test turns NEVER carry follow-up chips (Wave 122/123
        # interplay): plain test turns get none from
        # w122_payload itself, and the solve-command card's
        # are stripped here.
        ct_w122 = w122_payload(ct_result, lang=lang,
                               lang_request=lang_request,
                               question=question)
        ct_w122["chips"] = []
        return jsonify({
            **ct_payload,
            "explanation": explanation_for(ct_result, lang),
            "advice": None,
            "methods": [],
            "teach": teach_for(ct_result, lang),
            "w122": ct_w122,
            **fields,
        })

    # Wave 163: hint-first guided solve ("Seekh ke solve
    # karo", guided.py). Entry is the student's own learn
    # ask in the message ("hint do", "seekh ke solve karo",
    # "khud try karna hai"), a bare learn ask about the
    # last question, or a •••-menu tap (followup="guided"
    # with the card's question riding as context, exactly
    # like a Wave-122 chip tap). While a guided flow is
    # active in THIS chat, its messages belong to the flow
    # (an attempt, "agla step", or the "jawab bata do"
    # escape) until the flow completes or exits. This runs
    # AFTER the Wave-124 chat test (a test in progress owns
    # its messages) and BEFORE the Wave-129 galti block (a
    # guided attempt is never a step doubt). handle_message
    # returns None for everything else, so a plain question
    # keeps the normal path byte-for-byte.
    import guided as _guided_mod
    _g_start_q = None
    if followup_kind == "guided":
        _g_start_q = _json_str(data, "context_question") or ""
    g_payload = _guided_mod.handle_message(
        session, session.get("user_id"), chat_id, question,
        lang=lang, lang_request=lang_request,
        start_question=_g_start_q,
        solve_fn=lambda q: _solve_friendly(
            q, lang=lang,
            student_class=session.get("saathi_class"),
            lang_request=lang_request))
    if g_payload is not None:
        g_result = g_payload["result"]
        g_full = bool(g_payload.pop("w163_full", False))
        if g_payload.pop("w163_set_last", False):
            session["last_question"] = g_payload.pop(
                "w163_question", question)
            session["last_result"] = g_result
            _note_anchor(_chat_key(data),
                         session["last_question"])
            session.pop("doubt_step", None)
        else:
            g_payload.pop("w163_question", None)
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                g_result))
        session["history"] = history[:_HISTORY_LIMIT]
        if g_full:
            # The escape / completion serve: the stored full
            # answer, served exactly as a normal solve serves
            # it (Wave-138 annotation on a copy, methods,
            # teach, w122 reading the student's own message
            # as the ask).
            return jsonify({
                "ok": True,
                "result": annotate_result(dict(g_result)),
                "intro": g_payload.get("intro"),
                "explanation": explanation_for(g_result, lang),
                "advice": advice_for(g_result, lang),
                "methods": _methods_localised(
                    session.get("last_question") or question,
                    g_result, lang_request),
                "teach": teach_for(g_result, lang),
                "w122": w122_payload(
                    g_result, lang=lang,
                    lang_request=lang_request,
                    question=session.get("last_question")
                    or question,
                    ask_text=question),
                **fields,
            })
        # A guided step turn: plain, like a chat-test turn —
        # no chips ever (stripped here as well as by kind).
        g_w122 = w122_payload(g_result, lang=lang,
                              lang_request=lang_request,
                              question=question)
        g_w122["chips"] = []
        return jsonify({
            **g_payload,
            "explanation": explanation_for(g_result, lang),
            "advice": None,
            "methods": [],
            "teach": teach_for(g_result, lang),
            "w122": g_w122,
            **fields,
        })

    # Wave 165: "ek aur aisa hi sawal" — the in-chat practice
    # loop (practice_loop.py). Runs AFTER the chat-test block
    # (while a test is active in this chat, every message
    # belongs to the test — the loop never competes) and
    # BEFORE the Wave-129 galti block. The loop claims only
    # its own messages: a practice trigger right after a
    # solved answer, an answer attempt on its open question,
    # and its in-loop commands. A fresh question asked
    # mid-loop makes handle_message return None (the loop
    # closes), so the normal path below answers it exactly
    # as if the loop never existed. Loop turns are plain and
    # never carry follow-up chips, like test turns.
    import practice_loop
    pl_payload = practice_loop.handle_message(
        session, session.get("user_id"), chat_id, question,
        lang=lang, lang_request=lang_request,
        student_class=session.get("saathi_class"),
        last_question=session.get("last_question"),
        last_result=session.get("last_result"))
    if pl_payload is not None:
        pl_result = pl_payload["result"]
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                pl_result))
        session["history"] = history[:_HISTORY_LIMIT]
        pl_w122 = w122_payload(pl_result, lang=lang,
                               lang_request=lang_request,
                               question=question)
        pl_w122["chips"] = []
        return jsonify({
            **pl_payload,
            "explanation": explanation_for(pl_result, lang),
            "advice": None,
            "methods": [],
            "teach": teach_for(pl_result, lang),
            "w122": pl_w122,
            **fields,
        })

    # Wave 201: the PRACTICE-REQUEST intent
    # (practice_req.py) — "12th class ke kuch qustin
    # milinge solve karane ke liye" asks FOR questions to
    # solve and used to earn the bare not-found line: no
    # layer recognised a request for questions (guidance
    # only advises HOW to practice). Runs AFTER the
    # chat-test, guided and practice-loop blocks (a test
    # in progress and an open loop own their messages,
    # and the loop's own "aur ek" is never stolen) and
    # BEFORE the Wave-129 galti block (a practice request
    # is a fresh intent, never a step doubt). The module
    # claims only its own messages — a practice request,
    # the class reply to its parked ask, and "aur do"
    # while its state lives in this chat; its vetoes keep
    # paper asks, test asks, fact asks, advice asks and
    # concrete problems on their existing paths, so every
    # other message reaches the normal path below exactly
    # as before this wave. Its turns never carry chips.
    import practice_req
    pr_payload = practice_req.handle_message(
        session, session.get("user_id"), chat_id, question,
        lang=lang, lang_request=lang_request,
        student_class=session.get("saathi_class"))
    if pr_payload is not None:
        pr_result = pr_payload["result"]
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                pr_result))
        session["history"] = history[:_HISTORY_LIMIT]
        pr_w122 = w122_payload(pr_result, lang=lang,
                               lang_request=lang_request,
                               question=question)
        pr_w122["chips"] = []
        return jsonify({
            **pr_payload,
            "explanation": explanation_for(pr_result, lang),
            "advice": None,
            "methods": [],
            "teach": teach_for(pr_result, lang),
            "w122": pr_w122,
            **fields,
        })

    # Wave 212: the NOTES-REQUEST intent (notes_req.py) —
    # "trigonometry ke notes do" / "notes chahiye" asks for
    # revision notes and used to fall through to the
    # not-found line: no layer recognised a request FOR
    # notes.  Runs right after the practice-request block
    # (the two intents are disjoint — questions vs notes)
    # and before the Wave-129 galti block (a notes request
    # is a fresh intent, never a step doubt).  The module
    # claims only its own messages; its vetoes keep
    # concrete problems on their existing path.  Its turns
    # never carry chips.
    import notes_req
    nr_payload = notes_req.handle_message(
        session, session.get("user_id"), chat_id, question,
        lang=lang, lang_request=lang_request,
        student_class=session.get("saathi_class"))
    if nr_payload is not None:
        nr_result = nr_payload["result"]
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                nr_result))
        session["history"] = history[:_HISTORY_LIMIT]
        nr_w122 = w122_payload(nr_result, lang=lang,
                               lang_request=lang_request,
                               question=question)
        nr_w122["chips"] = []
        return jsonify({
            **nr_payload,
            "explanation": explanation_for(nr_result, lang),
            "advice": None,
            "methods": [],
            "teach": teach_for(nr_result, lang),
            "w122": nr_w122,
            **fields,
        })

    # Wave 129: "meri galti kahan hai" — the two-turn flow
    # around the Wave 85 step checker.
    # (a) A parked "apne steps bhejo" prompt is waiting: this
    # message is read as the student's steps first. When it
    # cannot be read as steps (or it is itself a fresh
    # check-my-work message), the parked state simply expires
    # and the message is answered normally below — the student
    # is never trapped in the flow.
    # (b) A fresh check-my-work intent carrying NO steps: park
    # the question (the message's own question line, else the
    # chat's last question — e.g. when the steps arrived alone
    # for a question just solved here) and answer with the
    # one-line prompt. An intent that DOES carry its steps
    # falls through: _solve_friendly's Wave 85 / Wave 129
    # hooks produce the verdict there.
    from galti import (check_pending_steps, flavour_of,
                       prompt_result, split_intent_message)
    from stepcheck import _split_message as _marker_split
    galti_reply = None
    pending = session.get("galti_pending")
    if pending is not None:
        session.pop("galti_pending", None)
        if split_intent_message(question) is None:
            verdict = check_pending_steps(
                pending.get("question")
                if isinstance(pending, dict) else None,
                question, lang=lang,
                flavour_hint=pending.get("flavour")
                if isinstance(pending, dict) else None)
            if verdict is not None:
                galti_reply = verdict
    if galti_reply is None and _marker_split(question) is None:
        split = split_intent_message(question)
        if split is not None and split.get("steps_only"):
            last_q = session.get("last_question")
            if last_q:
                verdict = check_pending_steps(
                    last_q, "\n".join(split["steps"]), lang=lang,
                    flavour_hint=flavour_of(question))
                if verdict is not None:
                    galti_reply = verdict
        elif split is not None and not split.get("steps"):
            park_q = split.get("question") \
                or session.get("last_question")
            session["galti_pending"] = {
                "question": park_q, "flavour": flavour_of(question)}
            galti_reply = prompt_result(question, bool(park_q))
    if galti_reply is not None:
        history = session.get("history", [])
        history.insert(0, trimmed_history_entry(question,
                                                galti_reply))
        session["history"] = history[:_HISTORY_LIMIT]
        return jsonify({
            "ok": True,
            "result": galti_reply,
            "intro": None,
            "explanation": explanation_for(galti_reply, lang),
            "advice": advice_for(galti_reply, lang),
            "methods": [],
            "teach": teach_for(galti_reply, lang),
            **fields,
        })

    # Wave 127: conversation context ("uska answer batao",
    # "usi ka ek aur example do", "dusra tarika batao", "ye
    # wala phir se samjhao") — a REFERENCE to an earlier turn
    # of THIS chat, resolved from the per-chat turn log before
    # anything solves it as a new question. The detector is
    # deliberately narrow (see context_ref.py): a message
    # carrying a self-contained new question is never claimed,
    # and step references are never claimed either — they fall
    # through to the Wave 96 doubt layer right below, which
    # owns them. When the reference cannot be honoured (no
    # earlier turn, topic never discussed, example cannot be
    # regenerated), build_context_response returns None and
    # the normal path answers — never an invented answer. A
    # context reply does NOT overwrite the last solution and
    # is NOT recorded as a turn, so references keep pointing
    # at the real solves.
    chat_key = _chat_key(data)
    ctx_ref = parse_context_ref(solve_text)
    if ctx_ref is not None:
        built = build_context_response(
            question, ctx_ref, _ctx_turns(chat_key),
            prev_question=session.get("last_question"),
            prev_result=session.get("last_result"), lang=lang)
        if built is not None:
            result, advice_source = built
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question, result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                "result": result,
                "intro": None,
                "explanation": "" if result.get("op") in (
                    "clarify", "show_answer")
                    else explanation_for(result, lang),
                "advice": advice_for(advice_source, lang)
                          if advice_source else "",
                "methods": [],
                "teach": teach_for(advice_source, lang)
                         if advice_source else [],
                **fields,
            })

    # Wave 147: anger about the last answer ("tumne galat
    # jawab diya", "ye app bekar hai") with a real previous
    # answer in this chat — never argued with, never scolded:
    # one short apology line and that same answer served once
    # more, so the student can point at the step they doubt
    # (the Wave-96 machinery below then takes over). This
    # branch only fires when the message carries NO new
    # question — a fresh question riding along is cleaned of
    # its frustration and solved normally by the tone
    # pre-pass inside _solve_friendly. A step-level complaint
    # ("step 2 galat hai") matches none of the answer-level
    # phrases and stays with the doubt block. With no real
    # previous answer there is nothing to re-serve: the
    # message falls through, and the pre-pass answers pure
    # venting with its one kind line. (Deploy-28 merge: the
    # branch sits after the Wave-127 context block and
    # immediately before the Wave-96 doubt block — the
    # Wave-129 galti block above has already had its chance
    # to expire/consume a parked pending on this message,
    # exactly as its spec requires, and a context reference
    # is never an anger message, so the two never compete.)
    from tone import analyse as _tone_analyse, apology_line
    _tone = _tone_analyse(question)
    if (_tone["anger"] or _tone["app_directed"]) \
            and not _tone["has_question"]:
        _prev_q = session.get("last_question")
        _prev_r = session.get("last_result")
        if isinstance(_prev_r, dict) and _prev_r.get("answer") \
                and not result_is_plain(_prev_r) \
                and not result_unsolvable(_prev_r):
            session.pop("doubt_step", None)
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    _prev_r))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                # Deploy-28 merge: the re-served result carries
                # the Wave-138 typeset twins on a copy, exactly
                # like the main/doubt response boundaries — the
                # session's stored dict stays pristine, and the
                # response matches what the original solve
                # returned for this same answer.
                "result": annotate_result(dict(_prev_r)),
                "intro": apology_line(question,
                                      lang_request=lang_request),
                "explanation": explanation_for(_prev_r, lang),
                "advice": advice_for(_prev_r, lang),
                "methods": (methods_nonblocking(_prev_q, _prev_r)
                            if _prev_q else []),
                "teach": teach_for(_prev_r, lang),
                "w122": w122_payload(
                    _prev_r, lang=lang,
                    lang_request=lang_request,
                    question=_prev_q or question,
                    ask_text=_prev_q or question),
                **fields,
            })

    # Wave 136: an explicit long-answer request in the message
    # ("detail me samjhao", "vistar se batao", "explain in
    # detail") — detected on the student's ORIGINAL message,
    # like Wave 123's gates read the original ask. The phrase
    # is NOT stripped from solve_text (the solver tolerates
    # request filler, exactly as it does Wave 123's step
    # phrases); the flag alone rides into the solve, where it
    # selects the AI legs' detail prompt variant and expands
    # a deterministic answer with the why block + one worked
    # example. No request -> the flag is False and every byte
    # below is the pre-Wave-136 behaviour.
    detail = detect_detail_request(question)

    # Wave 148: a BARE steps / detail request ("step by step
    # batao", "detail me batao", "vistar se samjhao") sent
    # ALONE right after an answer is a request ABOUT that
    # answer, not a new question — the Wave-122/123 design
    # applies an explicit request to the answer it belongs
    # to. Re-serve the stored answer: for a steps ask the
    # w122 payload below reads THIS message as the ask, so
    # the labels gate opens on the same steps; for a detail
    # ask the stored answer is first expanded by Wave 136.
    # With no previous solved answer there is nothing to
    # re-serve and the normal path below answers (the honest
    # one-liner) — nothing is invented. The stored last
    # solution is NOT overwritten, exactly like the doubt
    # block below: later follow-ups keep pointing at the
    # same answer. A question+request in ONE message ("12
    # aur 18 ka HCF step by step batao") is not bare (see
    # followups.parse_bare_view_request) and keeps its
    # Wave-123 path byte-for-byte.
    from followups import is_solved_result, \
        parse_bare_view_request
    _view = parse_bare_view_request(question)
    if _view is not None:
        _prev_r = session.get("last_result")
        _prev_q = session.get("last_question")
        # Wave 154: a bare DETAIL ask after a GUIDANCE card
        # re-serves that card too — expanded by detail.py's
        # guidance branch — although a guidance card is
        # not a solved answer. The detail view only: a
        # steps ask after a guidance card keeps the normal
        # path, and w122_payload still gates itself (no
        # chips on a guidance card).
        _w154_guidance_prev = (
            _view == "detail"
            and isinstance(_prev_r, dict)
            and _prev_r.get("fallback_kind") == "guidance")
        if (is_solved_result(_prev_r)
                or _w154_guidance_prev) \
                and (_prev_r.get("steps") or []):
            if _view == "detail":
                result = expand_detail(
                    _prev_q or question, _prev_r, lang=lang,
                    lang_request=lang_request)
            else:
                result = _prev_r
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                # Wave 138 annotation on a copy, like every
                # re-serve boundary (the session's stored
                # dict stays pristine).
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(_prev_r, lang),
                "methods": [],
                "teach": teach_for(_prev_r, lang),
                "w122": w122_payload(
                    result, lang=lang,
                    lang_request=lang_request,
                    question=_prev_q or question,
                    ask_text=question),
                **fields,
            })

    # Wave 166: a BARE simpler request ("aur asaan batao",
    # "samajh nahi aaya, easy me batao", "simpler please",
    # "आसान भाषा में बताओ") sent ALONE right after an
    # answer is a request ABOUT that answer — re-serve the
    # stored answer in simpler words (simpler.py: the same
    # verified answer re-presented, every value locked by
    # the Wave-132 invariant), or the stored answer itself
    # when no value-locked simplification exists. Nothing
    # is re-solved and nothing is invented. The detector's
    # discipline keeps every neighbour's path intact: a
    # bare "samajh nahi aaya" carries no simpler phrase and
    # stays with the Wave-96 doubt block below; a step ask
    # stays with Wave 148 / doubt; "detail me batao" stays
    # Wave 136/148; a question+request in one message is
    # not bare and keeps its normal path. The stored last
    # solution is NOT overwritten, exactly like the
    # Wave-148 block above.
    from followups import is_solved_result as \
        _is_solved_166
    from simpler import parse_bare_simple_request, \
        simplify_result
    if parse_bare_simple_request(question):
        _prev_r = session.get("last_result")
        _prev_q = session.get("last_question")
        if _is_solved_166(_prev_r) \
                and (_prev_r.get("steps") or []):
            result = simplify_result(
                _prev_r, _prev_q or "",
                lang=lang, lang_request=lang_request) \
                or _prev_r
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                # Wave 138 annotation on a copy, like every
                # re-serve boundary (the session's stored
                # dict stays pristine).
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(_prev_r, lang),
                "methods": [],
                "teach": teach_for(_prev_r, lang),
                "w122": w122_payload(
                    result, lang=lang,
                    lang_request=lang_request,
                    question=_prev_q or question,
                    ask_text=question),
                **fields,
            })

    # Wave 212 (item 10): SELECT-AND-REPLY.  The student
    # tapped the reply affordance on ONE step of an earlier
    # answer (or on the whole answer) and typed a follow-up
    # about exactly that selection; the client rides the
    # selection as hidden context (the chip pattern): the
    # answer's question, its answer and its steps, plus the
    # step index when a single step was selected.  A
    # teach-like follow-up ("ye samajh nahi aaya",
    # "samjhao", or an empty text on a step selection) is
    # answered SCOPED to the selection — a step selection
    # through Wave 96's doubt machinery run on the
    # SELECTED answer (which need not be the session's
    # last), a whole-answer selection through the teach
    # expansion of that answer.  A follow-up carrying a
    # fresh computation is NOT scoped: it falls through
    # to the normal solve below, untouched.
    _rc = data.get("reply_context")
    if isinstance(_rc, dict) and _rc.get("steps"):
        from followups import parse_bare_teach_request \
            as _rc_teach_parse
        _rc_steps = [str(s) for s in
                     (_rc.get("steps") or [])][:40]
        _rc_prev = {
            "answer": str(_rc.get("answer") or ""),
            "steps": _rc_steps,
            "op": "reply_context",
            "type": "word_problem",
        }
        _rc_idx = _rc.get("step_index")
        _rc_teachlike = bool(
            _rc_teach_parse(question)
            or parse_followup(question) is not None
            or not question.strip())
        _rc_built = None
        if isinstance(_rc_idx, int) and _rc_teachlike:
            _rc_built = build_doubt_response(
                question, {"index": _rc_idx}, _rc_prev,
                lang=lang)
            if _rc_built is not None:
                result, _rc_step = _rc_built
                history = session.get("history", [])
                history.insert(
                    0, trimmed_history_entry(question,
                                             result))
                session["history"] = \
                    history[:_HISTORY_LIMIT]
                return jsonify({
                    "ok": True,
                    "result": annotate_result(dict(result)),
                    "intro": None,
                    "explanation": explanation_for(
                        result, lang),
                    "advice": advice_for(_rc_prev, lang),
                    "methods": [],
                    "teach": teach_for(_rc_prev, lang),
                    "w122": w122_payload(
                        result, lang=lang,
                        question=question),
                    **fields,
                })
        elif _rc_idx is None and _rc_teachlike:
            result = expand_detail(
                str(_rc.get("question") or "") or question,
                _rc_prev, lang=lang,
                lang_request=lang_request) or _rc_prev
            _rc_lines = teach_for(_rc_prev, lang)
            if _rc_lines:
                result = dict(result)
                result["steps"] = list(_rc_lines) + [
                    s for s in (result.get("steps") or [])
                    if s not in _rc_lines]
            history = session.get("history", [])
            history.insert(
                0, trimmed_history_entry(question, result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(_rc_prev, lang),
                "methods": [],
                "teach": teach_for(_rc_prev, lang),
                "w122": w122_payload(
                    result, lang=lang,
                    lang_request=lang_request,
                    question=str(_rc.get("question") or "")
                    or question,
                    ask_text=question),
                **fields,
            })

    # Wave 212: a BARE teach-me ask ("teach me", "samjhao
    # ise", "mujhe samajhna hai", "इसे समझाओ") sent ALONE
    # right after an answer is a request to be TAUGHT that
    # answer — before this wave it fell through to the
    # solver and earned the not-found line.  The serve is
    # the stored answer in teaching form: the Wave-12 teach
    # lines lead, then the detail expansion (why + worked
    # example) of the SAME verified answer — nothing is
    # re-solved and nothing is invented.  The detector's
    # discipline keeps the neighbours intact: "samajh nahi
    # aaya" is not a teach form (Wave 96 / 166 keep it), a
    # step ask stays with Wave 148 / doubt, and a teach ask
    # carrying a question is not bare.  With no solved last
    # answer the message falls through to the normal path.
    # The stored last solution is NOT overwritten, exactly
    # like the Wave-148/166 blocks above.
    from followups import parse_bare_teach_request
    if parse_bare_teach_request(question):
        _prev_r = session.get("last_result")
        _prev_q = session.get("last_question")
        if _is_solved_166(_prev_r) \
                and (_prev_r.get("steps") or []):
            result = expand_detail(
                _prev_q or question, _prev_r, lang=lang,
                lang_request=lang_request) or _prev_r
            _teach_lines = teach_for(_prev_r, lang)
            if _teach_lines:
                result = dict(result)
                result["steps"] = list(_teach_lines) + [
                    s for s in (result.get("steps") or [])
                    if s not in _teach_lines]
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(_prev_r, lang),
                "methods": [],
                "teach": teach_for(_prev_r, lang),
                "w122": w122_payload(
                    result, lang=lang,
                    lang_request=lang_request,
                    question=_prev_q or question,
                    ask_text=question),
                **fields,
            })

    # Wave 96: doubt follow-up ("ye step samjhao") — answered
    # from the session's last solution (its steps are also what
    # the client stores inside the saved chat thread), never by
    # re-solving. When there is nothing honest to explain (no
    # previous answer, step number out of range, operation not
    # in any step), build_doubt_response returns None and the
    # normal path below answers with the app's honest one-liner
    # — a step is never invented. The last solution itself is
    # NOT overwritten, so a chain of follow-ups ("agla step
    # samjhao") keeps pointing at the same answer.
    doubt_ref = parse_followup(question)
    if doubt_ref is not None:
        prev_result = session.get("last_result")
        built = build_doubt_response(
            question, doubt_ref, prev_result, lang=lang,
            last_step=session.get("doubt_step"))
        if built is not None:
            result, step_index = built
            session["doubt_step"] = step_index
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question, result))
            session["history"] = history[:_HISTORY_LIMIT]
            return jsonify({
                "ok": True,
                # Wave 138: the typeset variants are a DISPLAY
                # concern, added on a copy at this response
                # boundary only — the solver's own dict (and
                # the session's last_result) stays pristine.
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(prev_result, lang),
                "methods": [],
                "teach": teach_for(prev_result, lang),
                # Wave 122: label word only — a doubt card is
                # not a solved answer, so it never gets chips
                # (w122_payload enforces that itself).
                "w122": w122_payload(result, lang=lang,
                                     question=question),
                **fields,
            })

    # Wave 214 (human brain, phase 1): bare conversational
    # follow-ups a human teacher would never fail on — "galat
    # hai, phir se karo" (redo) and a bare "samjhao" (explain).
    # A real-student test (22 Nov 2026) showed both falling
    # through every layer to the generic line. ORDER (fixed
    # 23 Nov 2026 after the route-level regression pass): this
    # block sits AFTER the Wave-96 doubt block on purpose —
    # when the doubt layer can explain a step of the last
    # answer, its pinned behaviour keeps first claim on a bare
    # "samjhao"; Wave 214 is the safety net for when doubt
    # declines (a previous answer with nothing it can explain)
    # and for "redo", which no earlier layer claims. The
    # detector (human_brain.parse_human_followup) is
    # deliberately narrow: no fresh payload, no step reference
    # (Wave 96 owns those), short messages only. Service = the
    # SAME previous question re-solved with detail on, opened
    # by one kind line in the student's language; the turn is
    # recorded in history but last_question/last_result keep
    # pointing at the real solve, exactly like the context
    # replies above. With no real previous answer, the message
    # falls through untouched.
    from human_brain import parse_human_followup, intro_line
    _hb_kind = parse_human_followup(question)
    if _hb_kind is not None:
        _hb_prev_q = session.get("last_question")
        _hb_prev_r = session.get("last_result")
        if _hb_prev_q and isinstance(_hb_prev_r, dict) \
                and _hb_prev_r.get("answer") \
                and not result_is_plain(_hb_prev_r) \
                and not result_unsolvable(_hb_prev_r):
            _hb_result = _solve_friendly(
                _hb_prev_q, lang=lang, lang_request=lang_request,
                detail=True)
            if _hb_result is not None and _hb_result.get("answer"):
                history = session.get("history", [])
                history.insert(0, trimmed_history_entry(
                    question, _hb_result))
                session["history"] = history[:_HISTORY_LIMIT]
                return jsonify({
                    "ok": True,
                    "result": _hb_result,
                    "intro": intro_line(_hb_kind, lang),
                    "explanation": explanation_for(_hb_result, lang),
                    "advice": advice_for(_hb_result, lang),
                    "methods": [],
                    "teach": teach_for(_hb_result, lang),
                    **fields,
                })

    result = _solve_friendly(
        solve_text, lang=lang,
        student_class=session.get("saathi_class"),
        lang_request=lang_request, detail=detail)

    # Wave 5 (additive): a chat solve on the homepage counts exactly
    # like a classic /solve — it lands in the session history and
    # becomes the "last solution" for /history, /download and the
    # print/PDF page. Existing response fields are unchanged.
    # (Wave 131: the writes live in _commit_solve_session and
    # the payload in _solve_response_payload, shared with the
    # streaming endpoint so both paths serve identical bytes.)
    _commit_solve_session(question, result, chat_key=chat_key)
    payload = _solve_response_payload(
        question, solve_text, result, lang, strings, fields,
        lang_request=lang_request)
    # Wave 178: a REPEAT ask of the same topic / question in
    # this chat is shown a varied copy of the answer (never
    # the same copy-paste twice — Suraj's standing rule).
    # The payload's chrome (intro, explanation, methods,
    # w122) was built from the base result above and the
    # session keeps the base result too; only the displayed
    # card body is swapped. An explicit detail ask is the
    # student's own follow-up channel (Wave 136), never a
    # repeat, so it is neither counted nor varied.
    if not detail:
        shown = _w178_shown(solve_text, result, chat_key,
                            lang_request=lang_request,
                            lang=lang)
        if shown is not None:
            payload["result"] = annotate_result(dict(shown))
    return jsonify(payload)


def _w178_shown(question, result, chat_key, lang_request=None,
                lang=None):
    """Wave 178: the repeat-varied copy of a finished
    answer for DISPLAY, or None — a first ask, an
    uncountable outcome, or any failure, in which case the
    base result is served exactly as before this wave.
    Counting + wording live in repeat.py (the session
    store rides the cookie like the Wave-127 turn log).
    An explicit language request (Wave 107/130) is the
    student's own presentation channel, like the detail
    ask: the same question re-asked in another language
    is served exactly, never counted and never varied."""
    if lang_request:
        return None
    try:
        from repeat import flavour_for, session_variation
        flavour = flavour_for(question, result,
                              lang_request=lang_request,
                              lang=lang)
        return session_variation(session, chat_key, question,
                                 result, flavour)
    except Exception:
        return None


def _note_anchor(chat_key, question):
    """Wave 216: remember THIS chat's last solved question.
    session["last_result"] is a single slot shared by every
    chat in the session, so a solve in chat B used to hijack
    follow-ups ("phir se karo", "samjhao") typed in chat A —
    they re-solved or explained B's answer (live Deploy-58
    check: chat A's percent follow-up re-solved chat B's 350).
    Only the question is kept per chat (small); api_solve
    restores the full result by re-solving it (solver answers
    are deterministic) when the student returns to the chat."""
    if not chat_key or not question:
        return
    anchors = session.get("anchor_by_chat")
    if not isinstance(anchors, dict):
        anchors = {}
    anchors[chat_key] = question
    while len(anchors) > _CTX_CHATS_KEPT:
        anchors.pop(next(iter(anchors)))
    session["anchor_by_chat"] = anchors
    session["last_result_chat"] = chat_key


def _restore_anchor_from_db(chat_key):
    """Wave 220: rebuild this chat's last_question/last_result
    from its SAVED THREAD (chats table) when the session cookie
    no longer holds them.

    Root cause (live, 23 Nov 2026): every cookie-based check
    passed (curl, test client), yet in a real browser the
    follow-ups "galat hai, phir se karo" / "samjhao" fell to
    the generic lines even inside a single chat that was never
    left — the browser had silently stopped carrying the
    session state the follow-up layers read (the Wave-46 audit
    already met this family: a session cookie that outgrows
    the browser's ~4,096 B limit is dropped without a word).
    The chat thread itself is saved server-side on every turn
    (recordTurn -> PUT /api/chats/<id>), so the honest anchor
    for a follow-up is the thread, not the fragile cookie.
    Only the signed-in owner's own chat is read (chats.get_chat
    enforces ownership); anything unexpected returns False and
    the caller continues exactly as before this wave."""
    try:
        uid = session.get("user_id")
        if not uid or not chat_key or not chat_key.startswith("c"):
            return False
        chat_id = int(chat_key[1:])
        if chat_id <= 0:
            return False
        import chats as _chats
        chat = _chats.get_chat(uid, chat_id)
        if not chat:
            return False
        messages = chat.get("messages") or []
        for i in range(len(messages) - 1, -1, -1):
            msg = messages[i]
            if not isinstance(msg, dict) \
                    or msg.get("role") != "bot":
                continue
            data = msg.get("data") or {}
            result = data.get("result")
            if not isinstance(result, dict):
                # A bot bubble with no result payload (a plain
                # message line) — not a turn a follow-up can
                # point at; keep walking to the last real solve.
                continue
            if not result.get("answer") \
                    or result_is_plain(result) \
                    or result_unsolvable(result):
                # The last real solve is not explainable —
                # nothing honest to anchor to.
                return False
            q = data.get("_q") or data.get("question")
            if not q:
                for j in range(i - 1, -1, -1):
                    prev = messages[j]
                    if isinstance(prev, dict) \
                            and prev.get("role") == "user":
                        q = prev.get("text")
                        break
            if not q:
                return False
            session["last_question"] = q
            session["last_result"] = result
            _note_anchor(chat_key, q)
            return True
        return False
    except Exception:
        return False


def _commit_solve_session(question, result, chat_key=None):
    """The session writes of a finished chat solve (Wave 5 +
    Wave 96 + Wave 46): the question and its full result
    become the session's last solution (for /history,
    /download, the print/PDF page and doubt follow-ups), the
    explained-step cursor resets, and a trimmed entry joins
    the session history."""
    session["last_question"] = question
    session["last_result"] = result
    _note_anchor(chat_key or "default", question)
    # Wave 127: the fresh solve joins THIS chat's turn log —
    # the log later references ("uska...", "usi ka...") point
    # into. (Filtered inside: plain/fallback outcomes are not
    # recorded.) (Wave 219: the streaming callers pass their
    # chat key too — the stream request and the stream-commit
    # body both carry chat_id since Wave 219 — so a streamed
    # solve anchors and turn-logs under its own chat exactly
    # like a classic one. The older note here claimed the
    # stream path was inert in production; it is not —
    # GANITRA_AI_STREAM is on in production.)
    if chat_key is not None:
        _ctx_record(chat_key, question, result)
    # Wave 96: a fresh solve replaces the answer any follow-up
    # points at, so the explained-step cursor resets with it.
    session.pop("doubt_step", None)
    history = session.get("history", [])
    # Wave 46 (audit F4): trimmed entry — see trimmed_history_entry.
    history.insert(0, trimmed_history_entry(question, result))
    session["history"] = history[:_HISTORY_LIMIT]


# --- Wave 167: board-aware chapter grounding --------------------
# Adoption #5 of the Wave-162 comparison: a finished solve's
# payload may carry ONE extra field, "grounding" — the short
# line naming the chapter this answer belongs to in the
# STUDENT'S OWN board book ("RBSE · Class 8 · Mensuration",
# board_context.py). It is computed here, at the one payload
# boundary every fresh solve passes through (the classic
# /api/solve, the stream's final event and the stream-commit),
# and nowhere else: follow-up re-serves, doubt cards, galti
# verdicts and chat-test turns build their own payloads and
# never carry it. The gate is followups.is_solved_result —
# the same predicate behind the Wave-122 answer box — so
# plain replies (small talk, guidance, the maths-only guard,
# the not-found line) and every fallback outcome stay
# byte-identical to before this wave. The student's board is
# the account's free-typed board_text (the login slug is only
# board_context's fallback); every failure is silent and the
# result dict itself is never touched.
def _grounding_for(result):
    try:
        from followups import is_solved_result
        if not is_solved_result(result):
            return None
        board_text = None
        user_id = session.get("user_id")
        if user_id:
            from accounts import get_user_by_id
            row = get_user_by_id(user_id)
            if row is not None:
                board_text = row["board_text"]
        from board_context import grounding_line
        return grounding_line(
            board_text, session.get("saathi_class"), result,
            slug=session.get("board"))
    except Exception:
        return None


def _solve_response_payload(question, solve_text, result, lang,
                            strings, fields, lang_request=None):
    """The JSON payload of a finished chat solve: the Wave-5b
    friendly error card when the solve failed, else the
    success payload. Pure construction — the caller owns the
    session writes (_commit_solve_session) and the wrapping
    (jsonify for /api/solve, a final SSE event for
    /api/solve/stream), so both paths serve the same dict."""
    if solve_failed(solve_text, result):
        # Wave 5b: the friendly error contract for the chat — the
        # client renders the localised error card + Retry in a
        # Ganitra bubble. No raw solver text leaves the server.
        # Wave 6: the same gentle card also carries the personal
        # Mera Saathi encouragement line (named when a name is set).
        saathi_name = session.get("saathi_name", "")
        if not isinstance(saathi_name, str):
            saathi_name = ""
        saathi_name = saathi_name[:30]
        if saathi_name:
            try:
                encouragement = strings[
                    "error_encourage_name"].format(name=saathi_name)
            except (IndexError, KeyError, ValueError):
                encouragement = strings["error_encourage_name"]
        else:
            encouragement = strings["error_encourage"]
        return {
            "ok": False,
            "unsolvable": True,
            "question": question,
            "error": {
                "heading": strings["error_heading"],
                "intro": strings["error_intro"],
                "encouragement": encouragement,
                "tips": [strings["error_tip1"], strings["error_tip2"],
                         strings["error_tip3"]],
                "retry_label": strings["error_retry_btn"],
            },
            **fields,
        }
    payload = {
        "ok": True,
        # Wave 138: display-only typeset variants on a copy
        # (see the doubt path above).
        "result": annotate_result(dict(result)),
        # Wave 68: "intro" is the card's opening line (the
        # solver's own givens/framing step for word problems,
        # else None). "explanation" is still sent for payload
        # compatibility (stored chats, the classic pages) but
        # the chat no longer renders it — it restated the
        # final answer, duplicating the answer line.
        "intro": _intro_for(result, solve_text),
        "explanation": explanation_for(result, lang),
        "advice": advice_for(result, lang),
        # Wave 12: genuinely-different extra methods for this
        # question (possibly none) + the "Teach me" concept lines.
        # The chat renders them as the small side chips; both are
        # stored with the bot turn, so a reopened account chat
        # shows exactly the same options.
        # Wave 14: the auto-teach methods pass runs with a hard
        # time budget (speedups.methods_nonblocking) — same data
        # in every normal case, but it can never delay the answer.
        "methods": [annotate_method(m) for m in
                    _methods_localised(solve_text, result,
                                       lang_request)],
        "teach": teach_for(result, lang),
        # Wave 122: the conditional-features payload — the
        # localised step-label word, and the follow-up chips
        # (only when this result is a solved maths answer).
        # Wave 123: the on-demand gates read the student's
        # ORIGINAL message (ask_text) — step labels only on
        # a steps request or a proof, chips only on a
        # more-intent ask; a plain question stays plain.
        "w122": w122_payload(result, lang=lang,
                             lang_request=lang_request,
                             question=solve_text,
                             ask_text=question),
        **fields,
    }
    # Wave 167: the board grounding line rides as its own
    # payload field (see _grounding_for above) — attached
    # after construction so a payload without it is
    # byte-identical to the pre-Wave-167 one.
    _grounding = _grounding_for(result)
    if _grounding:
        payload["grounding"] = _grounding
    return payload


def _sse_response(body):
    """A text/event-stream response with the headers
    progressive delivery needs: no-cache, and
    X-Accel-Buffering: no — the header PythonAnywhere's own
    Buffering help page prescribes so its nginx layers flush
    each event as it is yielded instead of buffering the
    whole answer (see ganitra-wave131-notes.md)."""
    resp = Response(body, mimetype="text/event-stream")
    resp.headers["X-Accel-Buffering"] = "no"
    resp.headers["Cache-Control"] = "no-cache"
    return resp


@api_bp.post("/solve/stream")
def api_solve_stream():
    """Wave 131: /api/solve, streamed — the same solve, with
    the AI fallback leg delivered piece by piece as the
    provider produces it (ai_stream.py; the deterministic
    layers answer in ~0.13 s and are served as one final
    event, there is nothing real to stream there).

    PROTOTYPE, flag-gated: with GANITRA_AI_STREAM unset (the
    default) this endpoint answers 404 and the chat uses
    /api/solve exactly as before. Progressive delivery is
    proven on the local stack and plausible on
    PythonAnywhere by its own documented buffering rules,
    but UNVERIFIED on PA's free tier until a live deploy
    watches an AI answer arrive progressively — see
    ganitra-wave131-notes.md. The client falls back to
    /api/solve on ANY problem with this endpoint (non-200,
    no readable stream, a stream that ends without a final
    event), so enabling the flag can never make the chat
    worse than the classic path.

    Events (SSE, one JSON object per data: frame):
    {"type": "delta", "text": ...} — a piece of the AI
    leg's reply, shown live; {"type": "reset"} — the leg on
    screen failed/truncated and the next leg is starting,
    clear the live text; {"type": "final", "payload": {...}}
    — the finished solve, the very dict /api/solve would
    have returned (built by _solve_response_payload from the
    same result), plus "commit_required": true when the
    result was finished inside the stream and the client
    must hand it to /api/solve/stream-commit for the session
    writes (a streaming response's session cookie is fixed
    before the first chunk leaves, so those writes cannot
    happen here)."""
    from ai_stream import sse_event, stream_ai_events, \
        stream_enabled
    if not stream_enabled():
        return jsonify({"ok": False,
                        "message": "streaming is off"}), 404
    data = _json_object()
    lang = normalise_lang(session.get("lang", "en"))
    strings = get_strings(lang)
    if data is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = _json_str(data, "question")
    if question is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = question.strip()
    if not question:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)})
    if len(question) > _QUESTION_HARD_LIMIT:
        return jsonify({"ok": False,
                        "message": strings["flash_too_long"],
                        **_lang_fields(lang, strings, False)})
    if _solve_rate_limited():
        return jsonify({"ok": False,
                        # Wave 233: localised — see api_solve.
                        "message": strings["api_rate_limited"],
                        **_lang_fields(lang, strings,
                                        False)}), 429

    # Language handling identical to api_solve (Wave 9
    # auto-detect + the Wave 107 explicit-request override) —
    # see the long comment there; the same fields result.
    lang_request = None
    solve_text = question
    req = detect_language_request(question)
    if req is not None:
        lang_request, req_cleaned = req
        if req_cleaned:
            solve_text = req_cleaned
        req_lang = ("hi" if lang_request in ("hi", "hinglish")
                    else "en")
        switched = req_lang != lang
        if switched:
            lang = req_lang
            session["lang"] = lang
            strings = get_strings(lang)
    else:
        detected, solid = detect_language_confident(question)
        switched = False
        if solid and detected != lang:
            lang = detected
            session["lang"] = lang
            strings = get_strings(lang)
            switched = True
    fields = _lang_fields(lang, strings, switched)

    # Wave 219: the Wave 216 per-chat anchor restore,
    # mirrored from api_solve (see there) — this endpoint
    # predates Wave 216 and never received it, so its
    # follow-up layers (Wave 148 / doubt / Wave 214 below)
    # read a last_result that could belong to another chat,
    # or none at all once the classic path had cleared it.
    _w216_key = _chat_key(data)
    if _w216_key != session.get("last_result_chat"):
        _w216_q = (session.get("anchor_by_chat") or {}).get(
            _w216_key)
        _w216_restored = None
        if _w216_q:
            try:
                _w216_restored = _solve_friendly(
                    _w216_q, lang=lang,
                    student_class=session.get("saathi_class"))
            except Exception:
                _w216_restored = None
        if isinstance(_w216_restored, dict) and \
                _w216_restored.get("answer"):
            session["last_question"] = _w216_q
            session["last_result"] = _w216_restored
        else:
            session.pop("last_question", None)
            session.pop("last_result", None)
        session.pop("doubt_step", None)
        session["last_result_chat"] = _w216_key

    # Wave 220: same saved-thread anchor restore as api_solve
    # (see there) — the stream path's follow-up layers read the
    # same last_result slot.
    _w220_lr = session.get("last_result")
    if not (session.get("last_question")
            and isinstance(_w220_lr, dict)
            and _w220_lr.get("answer")):
        _restore_anchor_from_db(_w216_key)

    # Wave 148: a BARE steps / detail request re-serves the
    # session's last answer (see api_solve) — one final
    # event with the classic payload, never the AI legs.
    from followups import is_solved_result as _is_solved_148, \
        parse_bare_view_request as _bare_view_148
    _view = _bare_view_148(question)
    if _view is not None:
        _prev_r = session.get("last_result")
        _prev_q = session.get("last_question")
        # Wave 154: the guidance-card detail re-serve,
        # mirrored from api_solve (see there).
        _w154_guidance_prev = (
            _view == "detail"
            and isinstance(_prev_r, dict)
            and _prev_r.get("fallback_kind") == "guidance")
        if (_is_solved_148(_prev_r)
                or _w154_guidance_prev) \
                and (_prev_r.get("steps") or []):
            if _view == "detail":
                result = expand_detail(
                    _prev_q or question, _prev_r, lang=lang,
                    lang_request=lang_request)
            else:
                result = _prev_r
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question,
                                                    result))
            session["history"] = history[:_HISTORY_LIMIT]
            payload = {
                "ok": True,
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(_prev_r, lang),
                "methods": [],
                "teach": teach_for(_prev_r, lang),
                "w122": w122_payload(
                    result, lang=lang,
                    lang_request=lang_request,
                    question=_prev_q or question,
                    ask_text=question),
                **fields,
            }
            return _sse_response(sse_event(
                {"type": "final", "payload": payload}))

    # Wave 96 doubt follow-up: answered from the session's
    # last solution, never by the AI legs — served as one
    # final event with api_solve's exact payload, its
    # session writes done here, before the response starts.
    doubt_ref = parse_followup(question)
    if doubt_ref is not None:
        prev_result = session.get("last_result")
        built = build_doubt_response(
            question, doubt_ref, prev_result, lang=lang,
            last_step=session.get("doubt_step"))
        if built is not None:
            result, step_index = built
            session["doubt_step"] = step_index
            history = session.get("history", [])
            history.insert(0, trimmed_history_entry(question, result))
            session["history"] = history[:_HISTORY_LIMIT]
            payload = {
                "ok": True,
                # Deploy-27 merge: mirrors the classic doubt
                # payload exactly (Wave 138 annotation on a
                # copy + the Wave 122 label-only w122 field).
                "result": annotate_result(dict(result)),
                "intro": None,
                "explanation": explanation_for(result, lang),
                "advice": advice_for(prev_result, lang),
                "methods": [],
                "teach": teach_for(prev_result, lang),
                "w122": w122_payload(result, lang=lang,
                                     question=question),
                **fields,
            }
            return _sse_response(sse_event(
                {"type": "final", "payload": payload}))

    # Wave 219: the Wave 214 human-brain follow-up block,
    # mirrored from api_solve (see there) — this endpoint
    # predates Wave 214 and never received it, so on the
    # live site a typed "galat hai, phir se karo" or a bare
    # "samjhao" fell through to the generic clarify line
    # while the classic path answered both. Served as one
    # final event; the session writes happen here, before
    # the response starts, exactly like the doubt block.
    from human_brain import parse_human_followup, intro_line
    _hb_kind = parse_human_followup(question)
    if _hb_kind is not None:
        _hb_prev_q = session.get("last_question")
        _hb_prev_r = session.get("last_result")
        if _hb_prev_q and isinstance(_hb_prev_r, dict) \
                and _hb_prev_r.get("answer") \
                and not result_is_plain(_hb_prev_r) \
                and not result_unsolvable(_hb_prev_r):
            _hb_result = _solve_friendly(
                _hb_prev_q, lang=lang, lang_request=lang_request,
                detail=True)
            if _hb_result is not None and _hb_result.get("answer"):
                history = session.get("history", [])
                history.insert(0, trimmed_history_entry(
                    question, _hb_result))
                session["history"] = history[:_HISTORY_LIMIT]
                payload = {
                    "ok": True,
                    "result": _hb_result,
                    "intro": intro_line(_hb_kind, lang),
                    "explanation": explanation_for(_hb_result, lang),
                    "advice": advice_for(_hb_result, lang),
                    "methods": [],
                    "teach": teach_for(_hb_result, lang),
                    **fields,
                }
                return _sse_response(sse_event(
                    {"type": "final", "payload": payload}))

    student_class = session.get("saathi_class")
    result = _solve_friendly(
        solve_text, lang=lang, student_class=student_class,
        lang_request=lang_request, defer_ai=True)

    if not (isinstance(result, dict)
            and result.get("ai_deferred")):
        # A finished outcome (solver, bank, concept, step
        # check, cached fallback...): the session writes
        # happen now, before the response starts, exactly as
        # api_solve does them, and the payload rides as the
        # single final event.
        _commit_solve_session(question, result,
                              chat_key=_chat_key(data))
        payload = _solve_response_payload(
            question, solve_text, result, lang, strings, fields,
            lang_request=lang_request)
        # Wave 178: same repeat-variation swap as /api/solve
        # (see api_solve) — the deterministic outcomes that
        # finish here are exactly the countable ones; the
        # deferred-AI path below never carries a guidance /
        # knowledge / solved-deterministic card.
        shown = _w178_shown(solve_text, result,
                            _chat_key(data),
                            lang_request=lang_request,
                            lang=lang)
        if shown is not None:
            payload["result"] = annotate_result(dict(shown))
        return _sse_response(sse_event(
            {"type": "final", "payload": payload}))

    # The chain stopped at the AI legs. Everything the
    # stream needs is captured in plain values now — the
    # generator below runs after the response (and its
    # session cookie) has been fixed, so it must not touch
    # the session; the writes that remain possible (the
    # Wave-117 record, the Wave-48 negative cache, the
    # Wave-90 log) are server-side stores and are done
    # there, with the FINAL result, exactly as the classic
    # path does them for a finished outcome.
    honest = result["ai_honest"]
    hindi = result["ai_hindi"]

    def generate():
        final_result = None
        try:
            events = stream_ai_events(solve_text, hindi,
                                      lang_request)
            while True:
                try:
                    event = next(events)
                except StopIteration as stop:
                    final_result = stop.value
                    break
                yield sse_event(event)
        except Exception:
            final_result = None
        if final_result is None:
            # Every leg missed or failed: the honest outcome
            # the classic chain would have served, with the
            # Wave-90 log fired now (and only now — an
            # AI-answered question is never logged not-found).
            final_result = honest
            try:
                log_deferred_not_found(
                    solve_text, result, lang=lang,
                    student_class=student_class,
                    lang_request=lang_request)
            except Exception:
                pass
        try:
            record_outcome(solve_text, final_result, lang,
                           lang_request)
        except Exception:
            pass
        try:
            put_negative(solve_text, final_result,
                         variant=lang_request)
        except Exception:
            pass
        payload = _solve_response_payload(
            question, solve_text, final_result, lang, strings,
            fields, lang_request=lang_request)
        yield sse_event({"type": "final",
                         "commit_required": True,
                         "payload": payload})

    return _sse_response(stream_with_context(generate()))


@api_bp.post("/solve/stream-commit")
def api_solve_stream_commit():
    """Wave 131: the session half of a streamed solve. A
    streaming response's session cookie is computed before
    the first chunk leaves, so the writes /api/solve does
    inline (_commit_solve_session) cannot happen inside the
    stream; the client hands the final result it was served
    (in the stream's final event) to this endpoint, which
    performs exactly those writes. The result only ever
    shapes the caller's OWN session (last solution, history)
    — the same trust the account-chat thread save already
    places in the client — and the server's own stores (Live
    Bank, negative cache, not-found log) were already
    written by the stream itself, from the server's own
    copy of the result."""
    from ai_stream import stream_enabled
    if not stream_enabled():
        return jsonify({"ok": False,
                        "message": "streaming is off"}), 404
    data = _json_object()
    if data is None:
        return jsonify({"ok": False,
                        "message": "bad request"}), 400
    question = _json_str(data, "question")
    result = data.get("result")
    if question is None or not question.strip() \
            or len(question) > _QUESTION_HARD_LIMIT \
            or not isinstance(result, dict) \
            or "answer" not in result:
        return jsonify({"ok": False,
                        "message": "bad request"}), 400
    _commit_solve_session(question.strip(), result,
                          chat_key=_chat_key(data))
    return jsonify({"ok": True})


@api_bp.post("/solve-method")
def api_solve_method():
    """Wave 12: re-serve ONE alternate method for a question.

    The methods already ride inside the /api/solve response (and
    inside saved chat threads), so this endpoint is the explicit
    contract the chips use when a method is opened: recompute the
    primary solve, look the method id up among ITS alternates,
    and return just that method (+ the teach lines). An unknown
    or unavailable method is a calm {ok: false}, never an error
    page.
    """
    data = _json_object()
    if data is None:
        return jsonify({"ok": False, "error": "bad-request"}), 400
    question = _json_str(data, "question")
    method_id = _json_str(data, "method")
    if question is None or method_id is None:
        return jsonify({"ok": False, "error": "bad-request"}), 400
    question = question.strip()
    method_id = method_id.strip()
    lang = normalise_lang(session.get("lang", "en"))
    if not question or not method_id \
            or len(question) > _QUESTION_HARD_LIMIT:
        return jsonify({"ok": False, "error": "method-unavailable"})
    primary = _solve_friendly(question)
    if solve_failed(question, primary):
        return jsonify({"ok": False, "error": "method-unavailable"})
    # Wave 130: the question may itself carry an explicit
    # language request ("... answer Hindi me chahiye") — the
    # re-served method's steps follow it, like /api/solve's.
    req = detect_language_request(question)
    req_target = req[0] if req else None
    for method in alternate_methods(question, primary):
        if method.get("id") == method_id:
            if req_target in ("hi", "hinglish"):
                try:
                    from steplang import relanguage_methods
                    method = relanguage_methods(
                        [method], req_target)[0]
                except Exception:
                    pass
            return jsonify({"ok": True,
                            "method": annotate_method(method),
                            "teach": teach_for(primary, lang)})
    return jsonify({"ok": False, "error": "method-unavailable"})
