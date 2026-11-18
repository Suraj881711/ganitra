"""Wave 165: "Ek aur aisa hi sawal" — the in-chat practice loop.

Wave 162's all-AI comparison found the same gap in every big
AI's favour: the moment of highest motivation is right after a
student understands a solution, and the big AIs convert it into
one more question (Perplexity's Related, Gemini/ChatGPT quiz
offers). Ganitra's practice lived only in separate modes. This
module brings ONE same-type question into the chat itself:

  * the student, right after a solved answer, asks in their
    own words — "ek aur aisa hi sawal", "aur practice karni
    hai", "one more like this", "एक और ऐसा ही सवाल" — and
    Ganitra serves a fresh question of the same type with
    DIFFERENT numbers;
  * the student answers in chat; the reply is checked
    instantly (sahi / galat, the correct answer shown kindly
    on a miss — Wave 147 tone throughout);
  * "aur ek" serves another; any other message ends the
    loop cleanly and is answered by the normal path — a
    fresh question asked mid-loop is NEVER hijacked.

Question sources, in order (a question whose answer Ganitra
cannot verify is NEVER served — an unverifiable candidate is
discarded, not shown):

  1. a solver variant of the student's own question — one
     number nudged (followups._perturbations, the Wave-122
     example machinery), re-solved by the solver alone and
     kept only when the solve is a real solved result whose
     answer is numerically checkable (full_paper's number
     extraction). This preserves the question's own language
     and exact type.
  2. the verified practice generator (practice_gen — the
     same machinery Wave 87's weak-topic practice and Wave
     124's chat test serve; every answer correct by
     construction and re-checked by test_mode's exact
     Fraction checker), on the topic the last answer's
     op/type maps to.

(The verified bank has no topic-retrieval API — bank.lookup
is exact-question match only — so the generator machinery is
the honest second source; nothing is ever served from an
unverified store.)

State is per (user, chat), server-side, exactly like
chat_test: a sqlite table when both ids exist, else a
session key. Two phases: "open" (a question is waiting for
its answer) and "done" (the last question was answered /
revealed; a continuation phrase serves the next one, any
other message closes the loop and falls through).

Public API:
    handle_message(session, user_id, chat_id, text, lang,
                   lang_request, student_class,
                   last_question, last_result) -> payload | None
    is_practice_trigger(text) -> bool
    load_state / clear_state (mirroring chat_test)
"""

import json
import random
import re
import sqlite3
import time

import accounts
import practice_gen
import test_mode
from chat_test import _has_phrase, _tokens, is_seen_command, \
    is_skip_command, is_stop_command
from followups import flavour_for, is_solved_result

__all__ = ["handle_message", "is_practice_trigger",
           "load_state", "clear_state"]

# ------------------------------------------------------------------ #
# Language lines (flavour: en / roman / dev) — Wave 147 kind tone,
# house style aligned with chat_test's lines.
# ------------------------------------------------------------------ #

_LINES = {
    "en": {
        "serve_first": "One more like it — try this: {q}",
        "serve_next": "Next one: {q}",
        "hint": "Just write the answer.",
        "correct": "Correct ✅",
        "wrong": "Wrong — correct answer: {a}",
        "seen": "No problem — the correct answer is: {a}",
        "skip": "Skip — correct answer: {a}",
        "more": "Want one more? Say 'aur ek'.",
        "stopped": "Practice stopped. Ask me anything else.",
        "sorry": "Sorry — I could not prepare another "
                 "checkable question of this type right now.",
    },
    "roman": {
        "serve_first": "Isi type ka ek aur — ye try karo: {q}",
        "serve_next": "Agla sawal: {q}",
        "hint": "Sirf jawab likho.",
        "correct": "Sahi ✅",
        "wrong": "Galat — sahi jawab: {a}",
        "seen": "Koi baat nahi — sahi jawab: {a}",
        "skip": "Skip — sahi jawab: {a}",
        "more": "Ek aur chahiye? 'aur ek' bolo.",
        "stopped": "Practice band kar di. Kuch aur puchho.",
        "sorry": "Sorry — abhi is type ka aur checkable "
                 "sawal taiyaar nahi ho paya.",
    },
    "dev": {
        "serve_first": "इसी type का एक और — यह try करो: {q}",
        "serve_next": "अगला सवाल: {q}",
        "hint": "सिर्फ जवाब लिखो।",
        "correct": "सही ✅",
        "wrong": "गलत — सही जवाब: {a}",
        "seen": "कोई बात नहीं — सही जवाब: {a}",
        "skip": "छोड़ा गया — सही जवाब: {a}",
        "more": "एक और चाहिए? 'और एक' बोलो।",
        "stopped": "अभ्यास बंद कर दिया। कुछ और पूछो।",
        "sorry": "माफ़ करो — अभी इस type का और जाँच योग्य "
                 "सवाल तैयार नहीं हो पाया।",
    },
}


def _plain_payload(lines, verdict=None):
    """A plain chat result in chat_test's exact shape (the
    chat JS renders plain results as one simple bubble: no
    card, no answer box, no step labels, no chips). The
    Wave-160 laughing robot rides on verdict="correct",
    passed ONLY for a right answer."""
    result = {
        "type": "Practice",
        "op": "practice_loop",
        "answer": lines[0] if lines else "",
        "steps": lines[1:],
        "plain": True,
        "plain_reply": True,
        "fallback_kind": "practice_loop",
    }
    if verdict is not None:
        result["test_verdict"] = verdict
    return {"ok": True, "result": result, "intro": None,
            "followup_note": None}


# ------------------------------------------------------------------ #
# Intent detection
# ------------------------------------------------------------------ #

# The full "one more like this" ask. Matched on chat_test's
# tokeniser (Devanagari-safe). Deliberately narrower than
# followups.detect_more_intent: "example" asks belong to the
# Wave-122/127 example paths, and a bare "aur" is just the
# Hinglish word for "and".
_TRIGGER_PHRASES = (
    ["one", "more", "like", "this"],
    ["another", "one", "like", "this"],
    ["one", "more", "question"],
    ["another", "question"],
    ["one", "more", "practice"],
    ["more", "practice"],
    ["ek", "aur", "aisa", "hi", "sawal"],
    ["ek", "aur", "sawal"],
    ["aur", "ek", "sawal"],
    ["aisa", "hi", "sawal"],
    ["ek", "aur", "aisa"],
    ["aur", "practice"],
    ["practice", "karni"],
    ["practice", "karna"],
    ["practice", "karein"],
    ["practice", "karo"],
    ["abhyas", "karna"],
    ["abhyas", "karni"],
    ["aur", "abhyas"],
    ["एक", "और", "सवाल"],
    ["और", "एक", "सवाल"],
    ["ऐसा", "ही", "सवाल"],
    ["एक", "और", "ऐसा"],
    ["अभ्यास", "करना"],
    ["अभ्यास", "करनी"],
    ["और", "अभ्यास"],
    ["प्रैक्टिस", "करनी"],
    ["प्रैक्टिस", "करना"],
)
_TRIGGER_EXACT = (
    ["practice"], ["अभ्यास"], ["प्रैक्टिस"],
    ["one", "more"], ["another", "one"],
)

# Continuation while the loop is alive ("aur ek" after a
# verdict) — short messages only, checked by the caller.
_CONTINUE_PHRASES = (
    ["aur", "ek"], ["ek", "aur"], ["aur"],
    ["one", "more"], ["another"],
    ["और", "एक"], ["एक", "और"], ["और"],
    ["haan"], ["yes"], ["हां"], ["हाँ"],
)

# "I don't know" — reveal the answer kindly, never a "wrong".
_DONT_KNOW_PHRASES = (
    ["nahi", "aata"], ["nahi", "ata"], ["nahi", "pata"],
    ["pata", "nahi"], ["mujhe", "nahi"], ["nahi", "samajh"],
    ["don't", "know"], ["dont", "know"], ["do", "not", "know"],
    ["नहीं", "आता"], ["नहीं", "पता"], ["मुझे", "नहीं"],
    ["नहीं", "समझ"],
)

# Words that mark a message as some OTHER flow's business
# (a concept ask, a doubt, small talk) when it carries no
# digit — such a message ends the loop and is answered by
# the normal path, never read as a (wrong) answer attempt.
_EXIT_WORDS = {
    "kya", "kaise", "kyu", "kyon", "kyun", "what", "why",
    "how", "samjhao", "samjha", "explain", "step", "steps",
    "स्टेप", "चरण", "galti", "गलती", "doubt", "matlab",
    "मतलब", "define", "meaning", "hello", "hii", "hey",
    "namaste", "नमस्ते", "thank", "thanks", "shukriya",
    "धन्यवाद", "bye", "kaun", "tumhara", "naam",
}
_QUESTION_WORDS = {
    "find", "solve", "calculate", "what", "kitna", "kitne",
    "nikalo", "nikal", "batao", "बताओ", "निकालो", "कितना",
    "कितने",
}


def _matches(text, phrases, exact_too=()):
    tokens = _tokens(text)
    if not tokens:
        return False
    if tokens in [list(p) for p in exact_too]:
        return True
    return any(_has_phrase(tokens, list(p)) for p in phrases)


def is_practice_trigger(text):
    """True when the message IS a "one more like this / aur
    practice" ask: a trigger phrase, no digit anywhere (a
    digit makes it a question carrying a rider, which keeps
    its normal path), and short enough to be the ask itself
    rather than a sentence about practice."""
    text = str(text or "")
    if any(ch.isdigit() for ch in text):
        return False
    tokens = _tokens(text)
    if not tokens or len(tokens) > 8:
        return False
    return _matches(text, _TRIGGER_PHRASES,
                    exact_too=_TRIGGER_EXACT)


def _is_continuation(text):
    tokens = _tokens(text)
    if not tokens or len(tokens) > 3:
        return False
    return _matches(text, _CONTINUE_PHRASES,
                    exact_too=_CONTINUE_PHRASES)


def _looks_like_fresh_question(text):
    """True when a message arriving while a practice question
    is open is really a NEW question (or another flow's
    message) — the loop must exit and let the normal path
    answer it, never grade it as an attempt."""
    from context_ref import parse_context_ref
    if parse_context_ref(text) is not None:
        return True
    tokens = _tokens(text)
    if not tokens:
        return False
    wordset = set(tokens)
    has_digit = any(ch.isdigit() for ch in str(text or "")) \
        or any(ch in str(text or "")
               for ch in ("=", "%", "+", "×", "÷", "^"))
    if has_digit:
        # A question word in a wordy message ("Solve for x:
        # 2x + 3 = 9", "15% of 240 kitna hoga") is a fresh
        # question, whatever its numbers parse to.
        if wordset & _QUESTION_WORDS and len(tokens) >= 5:
            return True
        # A bare parseable answer ("42", "x = 5", "1 1/2")
        # is an attempt.
        if test_mode.parse_student_number(text) is not None:
            return False
        # A one-number reply in words ("jawab 42 hai",
        # "42 cm") is an attempt too — the checker reads
        # the number out of it.
        nums = [t for t in tokens
                if any(ch.isdigit() for ch in t)]
        if len(nums) <= 1 and len(tokens) <= 4:
            return False
        # Anything else wordy and digit-carrying is a new
        # question the normal path must answer.
        return len(tokens) >= 3
    # No digit: another flow's signal words (doubt / concept
    # / small talk) end the loop; anything else short is
    # read as an attempt and graded kindly.
    return bool(wordset & _EXIT_WORDS) and len(tokens) >= 2


# ------------------------------------------------------------------ #
# State storage — per chat, server-side (mirrors chat_test)
# ------------------------------------------------------------------ #

_SCHEMA = """
CREATE TABLE IF NOT EXISTS practice_loop_state (
    user_id     INTEGER NOT NULL,
    chat_id     TEXT NOT NULL,
    state_json  TEXT NOT NULL DEFAULT '{}',
    updated_at  INTEGER NOT NULL,
    PRIMARY KEY (user_id, chat_id)
)
"""


def _connect():
    conn = sqlite3.connect(accounts.db_path())
    conn.execute(_SCHEMA)
    return conn


def _session_key(chat_id):
    return f"practice_loop::{chat_id or 'local'}"


def load_state(session, user_id, chat_id):
    if user_id and chat_id:
        try:
            conn = _connect()
            try:
                row = conn.execute(
                    "SELECT state_json FROM practice_loop_state"
                    " WHERE user_id = ? AND chat_id = ?",
                    (user_id, str(chat_id))).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            row = None
        if row:
            try:
                state = json.loads(row[0])
            except (ValueError, TypeError):
                return None
            return state if isinstance(state, dict) else None
        return None
    state = session.get(_session_key(chat_id))
    return state if isinstance(state, dict) else None


def _save_state(session, user_id, chat_id, state):
    if user_id and chat_id:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO practice_loop_state (user_id,"
                " chat_id, state_json, updated_at) VALUES"
                " (?, ?, ?, ?) ON CONFLICT(user_id, chat_id)"
                " DO UPDATE SET state_json ="
                " excluded.state_json, updated_at ="
                " excluded.updated_at",
                (user_id, str(chat_id), json.dumps(state),
                 int(time.time())))
            conn.commit()
        finally:
            conn.close()
        return
    session[_session_key(chat_id)] = state


def clear_state(session, user_id, chat_id):
    if user_id and chat_id:
        try:
            conn = _connect()
            try:
                conn.execute(
                    "DELETE FROM practice_loop_state WHERE"
                    " user_id = ? AND chat_id = ?",
                    (user_id, str(chat_id)))
                conn.commit()
            finally:
                conn.close()
        except sqlite3.Error:
            pass
        return
    session.pop(_session_key(chat_id), None)


# ------------------------------------------------------------------ #
# Question sources — verified only
# ------------------------------------------------------------------ #

_TOPIC_BY_OP = (
    ("probab", "probability"),
    ("area", "mensuration"), ("volume", "mensuration"),
    ("perimeter", "mensuration"), ("surface", "mensuration"),
)
_TOPIC_BY_TYPE = {"algebra": "algebra",
                  "geometry": "geometry",
                  "arithmetic": "arithmetic",
                  "applied": "arithmetic"}


def _topic_for(result):
    """The practice_gen topic the last answer belongs to
    (the followups._test mapping, mirrored)."""
    result = result or {}
    op = str(result.get("op") or "").lower()
    for needle, mapped in _TOPIC_BY_OP:
        if needle in op:
            return mapped
    return _TOPIC_BY_TYPE.get(
        str(result.get("type") or "").lower(), "arithmetic")


def _variant_item(state):
    """Source 1: a solver variant of the student's own
    question — one number nudged, re-solved by the solver
    alone, kept only when the solve is real and its answer
    is numerically checkable. The candidate order rotates
    with how many questions this loop has already served,
    so "aur ek" does not always walk the same first nudge."""
    origin = state.get("origin_question") or ""
    if not origin:
        return None
    from followups import _perturbations
    from full_paper import _numbers_in
    from i18n import solve_failed
    from solver.router import solve_question
    candidates = [c for c in _perturbations(origin)
                  if c != origin
                  and c not in state.get("served", [])]
    if not candidates:
        return None
    k = len(state.get("served", [])) % len(candidates)
    candidates = candidates[k:] + candidates[:k]
    for candidate in candidates:
        try:
            result = solve_question(candidate)
        except Exception:
            continue
        if solve_failed(candidate, result):
            continue
        if not is_solved_result(result):
            continue
        answer = str(result.get("answer") or "").strip()
        if not answer or not _numbers_in(answer):
            # An answer with no number in it cannot be
            # checked exactly — never served.
            continue
        return {"source": "variant", "question": candidate,
                "answer": answer,
                "topic_label": state.get("topic_label")}
    return None


def _generated_item(state, student_class):
    """Source 2: a fresh practice_gen question on the same
    topic — correct by construction, checked by test_mode's
    exact checker (the Wave-87 / Wave-124 machinery)."""
    topic = state.get("topic") or "arithmetic"
    try:
        class_num = int(str(student_class).strip())
    except (TypeError, ValueError):
        class_num = None
    if class_num not in practice_gen.CLASSES:
        class_num = 8
    rng = random.Random()
    served = set(state.get("served", []))
    origin = state.get("origin_question") or ""
    for _ in range(10):
        try:
            item = practice_gen.generate_question(
                class_num, topic,
                seed=rng.randrange(1 << 30))
        except Exception:
            return None
        if item["question"] in served \
                or item["question"] == origin:
            continue
        return {"source": "practice",
                "question": item["question"],
                "answer": item["answer"],
                "topic_label": test_mode.TOPIC_LABELS[topic],
                "check": test_mode._project(item)}
    return None


def _next_item(state, student_class):
    """The next verified practice question for this loop, or
    None when neither source can produce one."""
    return _variant_item(state) \
        or _generated_item(state, student_class)


def _check(item, given):
    if item.get("source") == "practice":
        return test_mode.check_test_answer(item["check"],
                                           given)
    from full_paper import answers_match
    return answers_match(item.get("answer"), given)


def _record_mistake(session, item, given):
    """The Mistake Notebook entry, same shape as chat_test's
    (source "practice loop") — wrong answers only."""
    try:
        entry = {"question": item["question"],
                 "expected": item["answer"],
                 "given": str(given or ""),
                 "topic": item.get("topic_label"),
                 "source": "practice loop"}
        notebook = session.get("mistakes", [])
        if not isinstance(notebook, list):
            notebook = []
        session["mistakes"] = ([entry] + notebook)[:50]
    except Exception:
        pass


# ------------------------------------------------------------------ #
# The flow
# ------------------------------------------------------------------ #

def _serve(session, user_id, chat_id, state, student_class,
           first=False):
    """Serve the next verified question and park the loop in
    the open phase; when no source can produce one, the
    honest sorry line and the loop closes."""
    ln = _LINES[state["flavour"]]
    item = _next_item(state, student_class)
    if item is None:
        clear_state(session, user_id, chat_id)
        return _plain_payload([ln["sorry"]])
    state["item"] = item
    state["phase"] = "open"
    state.setdefault("served", []).append(item["question"])
    _save_state(session, user_id, chat_id, state)
    lead = ln["serve_first"] if first else ln["serve_next"]
    return _plain_payload(
        [lead.format(q=item["question"]), ln["hint"]])


def _reveal(session, user_id, chat_id, state, line_key):
    """Show the open question's answer and move to the done
    phase (the loop stays alive for an "aur ek")."""
    ln = _LINES[state["flavour"]]
    item = state.get("item") or {}
    state["item"] = None
    state["phase"] = "done"
    _save_state(session, user_id, chat_id, state)
    return _plain_payload(
        [ln[line_key].format(a=item.get("answer", "")),
         ln["more"]])


def handle_message(session, user_id, chat_id, text, lang="en",
                   lang_request=None, student_class=None,
                   last_question=None, last_result=None):
    """One chat message through the practice loop.

    Returns a payload dict (the api layer adds the language
    fields, explanation/teach and the w122 payload, exactly
    as for chat_test), or None when the message has nothing
    to do with the loop — including every fresh question
    asked mid-loop, which the normal path must answer.
    """
    state = load_state(session, user_id, chat_id)
    if state and state.get("phase") == "open" \
            and state.get("item"):
        ln = _LINES[state["flavour"]]
        item = state["item"]
        if is_stop_command(text):
            clear_state(session, user_id, chat_id)
            return _plain_payload([ln["stopped"]])
        if is_practice_trigger(text) or _is_continuation(text):
            # "Ek aur" while one is open: reveal this one's
            # answer (skip-style), then serve the next — one
            # bubble: reveal line, then the serve lines.
            reveal = ln["skip"].format(a=item["answer"])
            payload = _serve(session, user_id, chat_id, state,
                             student_class)
            served = payload["result"]
            lines = [reveal, served["answer"]] \
                + list(served["steps"])
            if served["answer"] == ln["sorry"]:
                # No next question could be prepared: just
                # the reveal (the loop is already closed).
                lines = [reveal]
            return _plain_payload(lines)
        if is_seen_command(text) \
                or _matches(text, _DONT_KNOW_PHRASES):
            return _reveal(session, user_id, chat_id, state,
                           "seen")
        if is_skip_command(text):
            return _reveal(session, user_id, chat_id, state,
                           "skip")
        given = str(text or "").strip()
        if _check(item, given):
            state["item"] = None
            state["phase"] = "done"
            _save_state(session, user_id, chat_id, state)
            return _plain_payload([ln["correct"], ln["more"]],
                                  verdict="correct")
        if _looks_like_fresh_question(text):
            clear_state(session, user_id, chat_id)
            return None
        _record_mistake(session, item, given)
        state["item"] = None
        state["phase"] = "done"
        _save_state(session, user_id, chat_id, state)
        return _plain_payload(
            [ln["wrong"].format(a=item["answer"]), ln["more"]])
    if state and state.get("phase") == "done":
        if is_practice_trigger(text) or _is_continuation(text):
            return _serve(session, user_id, chat_id, state,
                          student_class)
        # Anything else closes the loop and is answered by
        # the normal path.
        clear_state(session, user_id, chat_id)
        return None
    if state:
        # A stale / half-written state is no state at all.
        clear_state(session, user_id, chat_id)
    # No loop alive: a trigger ask starts one — but only off
    # a real solved answer in this session (the follow-up
    # chips' own condition), never out of thin air.
    if not is_practice_trigger(text):
        return None
    if not is_solved_result(last_result):
        return None
    origin = str(last_question or "").strip()
    if not origin:
        return None
    topic = _topic_for(last_result)
    state = {
        "v": 1,
        "phase": "open",
        "flavour": flavour_for(text, lang=lang,
                                lang_request=lang_request),
        "item": None,
        "origin_question": origin,
        "topic": topic,
        "topic_label": test_mode.TOPIC_LABELS.get(topic),
        "served": [],
    }
    return _serve(session, user_id, chat_id, state,
                  student_class, first=True)
