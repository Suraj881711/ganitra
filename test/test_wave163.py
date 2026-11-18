"""Wave 163: hint-first guided solve — "Seekh ke solve karo"
(the #1 adoption of the Wave 162 all-AI comparison: ChatGPT
Study Mode / Gemini Guided Learning, built Ganitra's own
way on its verified solver).

Pinned here:
- the trigger battery: learn-intent phrases in English,
  Hinglish (Roman) and Hindi (Devanagari), with and without
  a question in the same message; negatives — plain
  questions, Wave 123's "step by step batao", Wave 136's
  "detail me samjhao", step-check messages — are NEVER
  claimed;
- the flow through the real /api/solve path: start poses
  step 1 with its result MASKED (the full answer and the
  step's value appear nowhere), a correct attempt advances
  one step at a time, the final step completes with the
  NORMAL full answer (the same verified solution, served
  whole);
- the attempt checker: a legal-but-different equation move
  passes (the Wave 85 proportionality invariant), a wrong
  value is judged wrong and does NOT advance, an unreadable
  reply is never accused;
- the escape: "jawab bata do" at ANY point serves the full
  answer immediately (jawab milega hi — guidance is an
  offer, never a lock); jumping straight to the final
  answer completes the flow;
- "agla step" reveals the current step and poses the next;
  "band karo" stops kindly; a fresh question exits
  gracefully back to normal chat;
- a bare learn ask right after an answer guides the LAST
  question; the •••-menu tap (followup="guided") starts on
  the card's question;
- no hijack: a plain question with no learn-intent gets
  the normal answer on the normal path (unmasked steps,
  solved card, not a plain guided bubble);
- guided turns are plain (no chips, no answer box), and
  the menu row exists in the ••• panel JS gated on the
  solved predicate, after the Full Solution item.
"""
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(
    encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

import guided  # noqa: E402

SIGNUP = {"name": "W163 Tester", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w163-test-pass"}

Q_EQ = "3x + 7 = 22"
# The solver's own steps for Q_EQ (Wave 149 school form):
#   "Subtract 7 from both sides: 3·x = 15"
#   "Divide both sides by 3: x = 5"
#   "Solution: x = 5"   (trailing restatement — not a task)


@pytest.fixture()
def env(tmp_path, monkeypatch):
    db = tmp_path / "users.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(db))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code in (200, 302)
    return c, db


def _new_chat(client):
    r = client.post("/api/chats")
    assert r.status_code == 201
    return r.get_json()["chat"]["id"]


def _solve(client, question, chat_id=None, **extra):
    payload = {"question": question}
    if chat_id is not None:
        payload["chat_id"] = chat_id
    payload.update(extra)
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


def _state(db, chat_id):
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT state_json FROM guided_state"
            " WHERE chat_id = ?", (str(chat_id),)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def _all_text(payload):
    result = payload.get("result") or {}
    return "\n".join([str(result.get("answer") or "")]
                     + [str(s) for s in (result.get("steps")
                                         or [])])


def _start_eq(client, chat_id, message=None):
    return _solve(client, message or f"{Q_EQ} hint do", chat_id)


# ------------------------------------------------------------------
# Trigger battery (unit level)
# ------------------------------------------------------------------

@pytest.mark.parametrize("text,kind", [
    ("hint do 3x + 7 = 22", "question"),
    ("3x + 7 = 22, hint do", "question"),
    ("give me a hint for 3x + 7 = 22", "question"),
    ("seekh ke solve karo 3x + 7 = 22", "question"),
    ("3x + 7 = 22 seekh ke samjhao", "question"),
    ("mujhe khud try karna hai, HCF of 12 and 18", "question"),
    ("let me try 2x - 5 = 9", "question"),
    ("step by step sikhao 3x + 7 = 22", "question"),
    ("हिंट दो 3x + 7 = 22", "question"),
    ("hint do", "bare"),
    ("seekh ke solve karo", "bare"),
    ("khud try karna hai", "bare"),
    ("हिंट दो", "bare"),
    ("सीख के हल करो", "bare"),
])
def test_trigger_positives(text, kind):
    got = guided.detect_learn_trigger(text)
    assert got is not None and got[0] == kind, (text, got)
    if kind == "question":
        assert got[1] and "3x" in got[1] or "HCF" in got[1] \
            or "2x" in got[1]


@pytest.mark.parametrize("text", [
    "12 aur 18 ka HCF nikalo",
    "3x + 7 = 22 solve karo",
    "What is the HCF of 12 and 18?",
    "step by step batao 3x + 7 = 22",      # Wave 123's ask
    "3x + 7 = 22 step by step batao",      # Wave 123's ask
    "detail me samjhao 3x + 7 = 22",       # Wave 136's ask
    "vistar se batao",
    "test do",
    "meri galti kahan hai",
    "3x + 7 = 22\nmy solution:\n3x = 15\nx = 5",  # Wave 85
    "",
    "   ",
])
def test_trigger_negatives(text):
    assert guided.detect_learn_trigger(text) is None, text


def test_trigger_residue_is_the_question():
    kind, residue = guided.detect_learn_trigger(
        "mujhe khud try karna hai, HCF of 12 and 18 nikalo")
    assert kind == "question"
    assert "HCF of 12 and 18" in residue
    assert "khud" not in residue and "try" not in residue


# ------------------------------------------------------------------
# Commands + masking + attempt checking (unit level)
# ------------------------------------------------------------------

@pytest.mark.parametrize("text,cmd", [
    ("jawab bata do", "escape"),
    ("poora jawab dikhao", "escape"),
    ("show the answer", "escape"),
    ("full answer do", "escape"),
    ("पूरा जवाब दो", "escape"),
    ("nahi ho raha, jawab bata do", "escape"),
    ("agla step", "next"),
    ("next step", "next"),
    ("अगला step", "next"),
    ("band karo", "stop"),
    ("stop", "stop"),
    ("बंद करो", "stop"),
    ("15", None),
    ("3x = 15", None),
])
def test_commands(text, cmd):
    assert guided.parse_guided_command(text) == cmd, text


def test_masking_shapes():
    pose, expected = guided._mask_step(
        "Subtract 7 from both sides: 3x = 15")
    assert pose == "Subtract 7 from both sides: 3x = ?"
    assert expected == "15"
    pose, expected = guided._mask_step("15% of 800 = 120")
    assert pose == "15% of 800 = ?" and expected == "120"
    pose, expected = guided._mask_step(
        "Take the lowest power of each common prime factor.")
    assert expected is None  # framing line: shown, not posed


def _eq_state():
    return {"question": Q_EQ,
            "steps": ["Subtract 7 from both sides: 3·x = 15",
                      "Divide both sides by 3: x = 5"],
            "answer": "x = 5", "result": {}, "index": 0,
            "attempts": 0, "flavour": "en"}


def test_attempt_checking():
    state = _eq_state()
    # The masked value, bare or as the full line.
    assert guided._check_attempt("15", state) is True
    assert guided._check_attempt("3x = 15", state) is True
    # A legal different move (the intermediate line) passes
    # by the proportionality invariant.
    assert guided._check_attempt(
        "3x + 7 - 7 = 22 - 7", state) is True
    # A wrong value is judged wrong.
    assert guided._check_attempt("3x = 20", state) is False
    assert guided._check_attempt("20", state) is False
    # Prose is unreadable, never accused.
    assert guided._check_attempt("samajh nahi aaya", state) is None
    # Jumping straight to the final answer completes.
    assert guided._check_attempt("x = 5", state) == "complete"
    state["index"] = 1
    assert guided._check_attempt("x = 5", state) is True
    assert guided._check_attempt("5", state) is True


# ------------------------------------------------------------------
# The flow through /api/solve
# ------------------------------------------------------------------

def test_start_poses_masked_step_1(env):
    client, db = env
    chat = _new_chat(client)
    payload = _start_eq(client, chat)
    result = payload["result"]
    assert result["fallback_kind"] == "guided"
    assert result["plain"] is True
    text = _all_text(payload)
    assert "Step 1 of 2" in text
    assert "Subtract 7 from both sides: 3·x = ?" in text
    # The masked value and the final answer appear NOWHERE.
    assert "3·x = 15" not in text
    assert "x = 5" not in text
    # Guided turns never carry chips.
    assert payload["w122"]["chips"] == []
    state = _state(db, chat)
    assert state is not None and state["index"] == 0
    assert state["question"] == Q_EQ


def test_full_flow_attempt_by_attempt(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    # Correct attempt at step 1 -> praise + step 2 posed.
    payload = _solve(client, "3x = 15", chat)
    text = _all_text(payload)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "Correct" in text
    assert "Step 2 of 2" in text
    assert "Divide both sides by 3: x = ?" in text
    assert _state(db, chat)["index"] == 1
    # Correct attempt at step 2 -> the NORMAL full answer.
    payload = _solve(client, "x = 5", chat)
    result = payload["result"]
    assert result.get("fallback_kind") != "guided"
    assert result["answer"] == "x = 5"
    steps = [str(s) for s in result.get("steps") or []]
    assert any("3·x = 15" in s for s in steps)
    assert "very well done" in str(payload.get("intro") or "")
    # The flow is over: state cleared.
    assert _state(db, chat) is None


def test_wrong_attempt_does_not_advance(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    payload = _solve(client, "3x = 20", chat)
    text = _all_text(payload)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "Not quite" in text
    assert "Step 1 of 2" in text          # still on step 1
    assert "x = 5" not in text            # nothing leaked
    assert _state(db, chat)["index"] == 0
    # Second wrong attempt -> the options line appears.
    payload = _solve(client, "3x = 21", chat)
    text = _all_text(payload)
    assert "next step" in text and "show the answer" in text
    assert _state(db, chat)["index"] == 0


def test_escape_at_any_point(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    payload = _solve(client, "jawab bata do", chat)
    result = payload["result"]
    assert result.get("fallback_kind") != "guided"
    assert result["answer"] == "x = 5"
    steps = [str(s) for s in result.get("steps") or []]
    assert any("3·x = 15" in s for s in steps)  # full solution
    assert _state(db, chat) is None


def test_next_reveals_and_completes(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    payload = _solve(client, "agla step", chat)
    text = _all_text(payload)
    assert "3·x = 15" in text              # step 1 shown
    assert "Step 2 of 2" in text           # step 2 posed
    payload = _solve(client, "agla step", chat)
    result = payload["result"]
    assert result.get("fallback_kind") != "guided"
    assert result["answer"] == "x = 5"     # completed whole
    assert _state(db, chat) is None


def test_stop_exits_kindly(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    payload = _solve(client, "band karo", chat)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "learn mode is off" in _all_text(payload)
    assert _state(db, chat) is None
    # The next message is a completely normal solve.
    payload = _solve(client, Q_EQ, chat)
    assert payload["result"].get("fallback_kind") != "guided"
    assert payload["result"]["answer"] == "x = 5"


def test_new_question_exits_gracefully(env):
    client, db = env
    chat = _new_chat(client)
    _start_eq(client, chat)
    payload = _solve(client, "12 aur 18 ka HCF nikalo", chat)
    result = payload["result"]
    assert result.get("fallback_kind") != "guided"
    assert str(result["answer"]).strip() == "6"
    assert _state(db, chat) is None


def test_bare_trigger_guides_last_question(env):
    client, db = env
    chat = _new_chat(client)
    payload = _solve(client, Q_EQ, chat)
    assert payload["result"]["answer"] == "x = 5"  # normal
    payload = _solve(client, "seekh ke solve karo", chat)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "Step 1 of 2" in _all_text(payload)
    assert _state(db, chat)["question"] == Q_EQ


def test_menu_tap_starts_guided(env):
    client, db = env
    chat = _new_chat(client)
    payload = _solve(client, "Learn step by step", chat,
                     followup="guided", context_question=Q_EQ)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "Step 1 of 2" in _all_text(payload)
    assert _state(db, chat)["question"] == Q_EQ


def test_hinglish_trigger_and_escape_via_api(env):
    client, db = env
    chat = _new_chat(client)
    payload = _solve(client, f"{Q_EQ} seekh ke solve karo", chat)
    assert payload["result"]["fallback_kind"] == "guided"
    assert "Step 1 of 2" in _all_text(payload)
    payload = _solve(client, "jawab bata do", chat)
    assert payload["result"]["answer"] == "x = 5"
    assert _state(db, chat) is None


def _fake_solve(question):
    return {"type": "algebra", "op": "equation",
            "answer": "x = 5",
            "steps": ["Subtract 7 from both sides: 3x = 15",
                      "Divide both sides by 3: x = 5",
                      "Solution: x = 5"]}


def _unit_text(payload):
    result = payload["result"]
    return "\n".join([str(result.get("answer") or "")]
                     + [str(s) for s in (result.get("steps")
                                         or [])])


def test_flavours_follow_the_session_language():
    # A Hindi session (lang="hi") with a Roman message gets
    # the Hinglish (roman) lines; the same session with a
    # Devanagari message gets the Devanagari lines — the
    # app's standing flavour rule, via flavour_for.
    session = {}
    payload = guided.handle_message(
        session, None, None, f"{Q_EQ} seekh ke solve karo",
        lang="hi", solve_fn=_fake_solve)
    assert payload is not None
    assert "Seekh ke solve karte hain" in _unit_text(payload)
    payload = guided.handle_message(
        session, None, None, "jawab bata do", lang="hi",
        solve_fn=_fake_solve)
    assert payload["result"]["answer"] == "x = 5"
    assert payload.get("w163_full") is True

    session = {}
    payload = guided.handle_message(
        session, None, None, f"{Q_EQ} हिंट दो",
        lang="hi", solve_fn=_fake_solve)
    assert payload is not None
    assert "चरण 1 / 2" in _unit_text(payload)


def test_hindi_trigger_starts_guided(env):
    client, db = env
    chat = _new_chat(client)
    payload = _solve(client, f"{Q_EQ} हिंट दो", chat)
    assert payload["result"]["fallback_kind"] == "guided"
    assert _state(db, chat) is not None


def test_unsolvable_trigger_falls_through(env):
    client, db = env
    chat = _new_chat(client)
    # A learn ask about something with no guided-able
    # solution: the student still gets the normal path's
    # answer (here the honest one-liner), never a trap.
    payload = _solve(
        client, "hint do, what is the capital of France?", chat)
    assert payload["result"].get("fallback_kind") != "guided"
    assert _state(db, chat) is None


# ------------------------------------------------------------------
# No hijack: the plain path is untouched
# ------------------------------------------------------------------

def test_plain_question_byte_identical_path(env):
    client, db = env
    chat = _new_chat(client)
    payload = _solve(client, f"{Q_EQ} solve karo", chat)
    result = payload["result"]
    assert result.get("fallback_kind") != "guided"
    assert not result.get("plain")
    steps = [str(s) for s in result.get("steps") or []]
    # The normal card shows the working unmasked, at once.
    assert any("3·x = 15" in s for s in steps)
    assert result["answer"] == "x = 5"
    assert _state(db, chat) is None


def test_guided_is_per_chat(env):
    client, db = env
    chat_a = _new_chat(client)
    chat_b = _new_chat(client)
    _start_eq(client, chat_a)
    assert _state(db, chat_a) is not None
    assert _state(db, chat_b) is None
    # Chat B is unaffected: a bare number there is normal.
    payload = _solve(client, Q_EQ, chat_b)
    assert payload["result"]["answer"] == "x = 5"


# ------------------------------------------------------------------
# The visible surface: menu row + pins
# ------------------------------------------------------------------

def test_menu_row_in_panel_js():
    assert 'guidedSolve: {{ t.chat_guided | tojson }}' in INDEX
    # The row is gated on the solved predicate and rides the
    # chip-tap flow with the card's question as context.
    assert 'w122Solved(result) && CHAT.guidedSolve' in INDEX
    assert 'sendFollowup("guided", CHAT.guidedSolve,' in INDEX
    # It sits AFTER the Full Solution item in the panel.
    assert INDEX.index("methodsPanel.appendChild(full);") \
        < INDEX.index('sendFollowup("guided"')
    # A guided step bubble can never be a "solved" card.
    assert '"guided"' in INDEX.split(
        "W122_NOT_SOLVED_KINDS")[1].split("];")[0]


def test_pins_bumped():
    assert "v='53'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v30"' in SW
    assert '"/static/style.css?v=53"' in SW
