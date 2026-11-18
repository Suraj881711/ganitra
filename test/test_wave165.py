"""Wave 165: "Ek aur aisa hi sawal" — the in-chat practice
loop (Wave 162 adoption #3).

After a solved answer the student can ask for another
question LIKE it ("ek aur aisa hi sawal", "aur practice
karni hai", "one more like this", "एक और ऐसा ही सवाल"):
Ganitra serves a fresh same-type question with different
numbers, checks the student's reply in chat instantly
(sahi / galat, Wave 147 kind tone, laughing robot on a
correct answer via the Wave-160 verdict flag), "aur ek"
serves the next, and any other message closes the loop
and is answered normally.

Pinned here:
- the trigger battery (EN / Hinglish / Devanagari positives;
  negatives: digit-carrying asks, a bare "aur", example
  asks — those belong to the Wave-122/127 paths — long
  sentences, test asks);
- full runs through the real /api/solve path in all three
  languages: solve -> trigger -> a DIFFERENT question is
  served -> correct answer earns the verdict -> "aur ek"
  serves another different question;
- every served question is verifiable: the loop's own
  checker accepts the stored expected answer and rejects
  a wrong one; an origin whose variants cannot be verified
  never serves a variant;
- a wrong answer shows the correct answer kindly and lands
  in the Mistake Notebook with source "practice loop";
- "answer batao" / "nahi aata" reveal kindly; stop closes;
- no hijack: a fresh question asked mid-loop (open phase
  or after a verdict) is answered by the normal path and
  the loop state is gone;
- no loop without a solved answer: the trigger after a
  nonmaths / not-found reply starts nothing;
- loop turns are plain and carry no w122 chips;
- per-chat isolation of the loop state.
"""
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SIGNUP = {"name": "W165 Tester", "class": "10",
          "board": "CBSE", "goal": "Doctor",
          "hobby": "Cricket", "favourite": "Pizza",
          "password": "w165-test-pass"}


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


def _solve(client, question, chat_id=None):
    payload = {"question": question}
    if chat_id is not None:
        payload["chat_id"] = chat_id
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


def _state(db, chat_id):
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT state_json FROM practice_loop_state"
            " WHERE chat_id = ?", (str(chat_id),)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def _lines(payload):
    result = payload.get("result") or {}
    return [result.get("answer") or ""] \
        + list(result.get("steps") or [])


def _is_loop(payload):
    result = payload.get("result") or {}
    return result.get("op") == "practice_loop"


# ------------------------------------------------------------------ #
# Trigger battery (unit)
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("text", [
    "ek aur aisa hi sawal",
    "ek aur aisa hi sawal do",
    "mujhe ek aur aisa hi sawal do",
    "ek aur sawal",
    "aur ek sawal do",
    "aur practice karni hai",
    "practice karna hai",
    "practice",
    "one more like this",
    "one more question",
    "another question please",
    "more practice",
    "एक और ऐसा ही सवाल",
    "एक और सवाल दो",
    "और अभ्यास करना है",
    "अभ्यास करना है",
])
def test_trigger_positives(text):
    import practice_loop
    assert practice_loop.is_practice_trigger(text)


@pytest.mark.parametrize("text", [
    "12 aur 18 ka HCF nikalo",        # a plain question ("aur" = and)
    "ek aur example do",              # Wave-127 example path, not ours
    "usi ka ek aur example do",
    "Find the HCF of 12 and 18",
    "test do",                        # Wave-124 test ask
    "mujhe maths ki practice karni hai isliye main roz "
    "sawal karta hu",                 # a sentence ABOUT practice
    "latest",
    "",
    "aur",                            # a bare "aur" starts nothing
    "haan",
])
def test_trigger_negatives(text):
    import practice_loop
    assert not practice_loop.is_practice_trigger(text)


# ------------------------------------------------------------------ #
# Full runs through /api/solve
# ------------------------------------------------------------------ #

def test_full_loop_english(env):
    client, db = env
    chat = _new_chat(client)
    first = _solve(client, "Find the HCF of 12 and 18", chat)
    assert (first.get("result") or {}).get("answer") == "6"

    served = _solve(client, "one more like this", chat)
    assert _is_loop(served)
    assert served["w122"]["chips"] == []
    lines = _lines(served)
    assert lines[0].startswith("One more like it")
    state = _state(db, chat)
    assert state and state["phase"] == "open"
    item = state["item"]
    assert item["question"] != "Find the HCF of 12 and 18"
    assert item["question"] in lines[0]

    # The served question is verifiable: the loop's own
    # checker accepts its stored answer, rejects a wrong one.
    import practice_loop
    assert practice_loop._check(item, item["answer"])
    assert not practice_loop._check(item, "999999")

    verdict = _solve(client, item["answer"], chat)
    assert _is_loop(verdict)
    assert verdict["result"].get("test_verdict") == "correct"
    assert _lines(verdict)[0] == "Correct ✅"
    assert _state(db, chat)["phase"] == "done"

    # "aur ek" serves another, different question.
    nxt = _solve(client, "aur ek", chat)
    assert _is_loop(nxt)
    state2 = _state(db, chat)
    assert state2["phase"] == "open"
    assert state2["item"]["question"] != item["question"]
    assert state2["item"]["question"] \
        != "Find the HCF of 12 and 18"


def test_full_loop_roman_hinglish(env):
    client, db = env
    chat = _new_chat(client)
    first = _solve(client, "12 aur 18 ka HCF nikalo", chat)
    assert (first.get("result") or {}).get("answer") == "6"

    served = _solve(client, "ek aur aisa hi sawal", chat)
    assert _is_loop(served)
    lines = _lines(served)
    assert lines[0].startswith("Isi type ka ek aur")
    state = _state(db, chat)
    item = state["item"]
    # The variant keeps the student's own language.
    assert "HCF" in item["question"]
    assert item["question"] != "12 aur 18 ka HCF nikalo"

    verdict = _solve(client, item["answer"], chat)
    assert _lines(verdict)[0] == "Sahi ✅"
    assert verdict["result"].get("test_verdict") == "correct"


def test_full_loop_devanagari(env):
    client, db = env
    chat = _new_chat(client)
    first = _solve(client, "12 और 18 का HCF निकालो", chat)
    assert (first.get("result") or {}).get("answer") == "6"

    served = _solve(client, "एक और ऐसा ही सवाल", chat)
    assert _is_loop(served)
    lines = _lines(served)
    assert lines[0].startswith("इसी type का एक और")
    state = _state(db, chat)
    assert state["item"]["question"] != "12 और 18 का HCF निकालो"

    verdict = _solve(client, state["item"]["answer"], chat)
    assert _lines(verdict)[0] == "सही ✅"


def test_wrong_answer_kind_and_notebook(env):
    client, db = env
    chat = _new_chat(client)
    _solve(client, "12 aur 18 ka HCF nikalo", chat)
    _solve(client, "ek aur aisa hi sawal", chat)
    item = _state(db, chat)["item"]

    verdict = _solve(client, "999999", chat)
    assert _is_loop(verdict)
    lines = _lines(verdict)
    assert lines[0] == f"Galat — sahi jawab: {item['answer']}"
    assert verdict["result"].get("test_verdict") is None
    assert _state(db, chat)["phase"] == "done"

    with client.session_transaction() as sess:
        mistakes = sess.get("mistakes") or []
    assert mistakes and mistakes[0]["source"] == "practice loop"
    assert mistakes[0]["question"] == item["question"]
    assert mistakes[0]["expected"] == item["answer"]


def test_reveal_and_stop(env):
    client, db = env
    chat = _new_chat(client)
    _solve(client, "12 aur 18 ka HCF nikalo", chat)
    _solve(client, "ek aur aisa hi sawal", chat)
    item = _state(db, chat)["item"]

    reveal = _solve(client, "nahi aata", chat)
    assert _is_loop(reveal)
    assert _lines(reveal)[0] == \
        f"Koi baat nahi — sahi jawab: {item['answer']}"
    assert _state(db, chat)["phase"] == "done"

    nxt = _solve(client, "aur ek", chat)
    assert _is_loop(nxt)
    assert _state(db, chat)["phase"] == "open"

    stopped = _solve(client, "band karo", chat)
    assert _is_loop(stopped)
    assert _lines(stopped)[0].startswith("Practice band")
    assert _state(db, chat) is None


def test_fresh_question_mid_loop_not_hijacked(env):
    client, db = env
    chat = _new_chat(client)
    _solve(client, "Find the HCF of 12 and 18", chat)
    _solve(client, "one more like this", chat)
    assert _state(db, chat)["phase"] == "open"

    fresh = _solve(client, "Solve for x: 2x + 3 = 9", chat)
    assert not _is_loop(fresh)
    result = fresh.get("result") or {}
    assert result.get("answer") == "x = 3"
    assert not result.get("plain")
    assert _state(db, chat) is None


def test_fresh_question_after_verdict_not_hijacked(env):
    client, db = env
    chat = _new_chat(client)
    _solve(client, "Find the HCF of 12 and 18", chat)
    _solve(client, "one more like this", chat)
    item = _state(db, chat)["item"]
    _solve(client, item["answer"], chat)
    assert _state(db, chat)["phase"] == "done"

    fresh = _solve(client, "Find the LCM of 4 and 6", chat)
    assert not _is_loop(fresh)
    assert (fresh.get("result") or {}).get("answer") == "12"
    assert _state(db, chat) is None


def test_no_loop_without_solved_answer(env):
    client, db = env
    chat = _new_chat(client)
    # Nothing solved yet in this chat.
    out = _solve(client, "ek aur aisa hi sawal", chat)
    assert not _is_loop(out)
    assert _state(db, chat) is None

    # A nonmaths reply is not a solved answer either.
    _solve(client, "What is the capital of France?", chat)
    out = _solve(client, "ek aur aisa hi sawal", chat)
    assert not _is_loop(out)
    assert _state(db, chat) is None


def test_loop_state_is_per_chat(env):
    client, db = env
    chat_a = _new_chat(client)
    chat_b = _new_chat(client)
    _solve(client, "Find the HCF of 12 and 18", chat_a)
    _solve(client, "one more like this", chat_a)
    item = _state(db, chat_a)["item"]
    assert item

    # The same answer typed in another chat is not graded
    # by chat A's loop.
    out = _solve(client, item["answer"], chat_b)
    assert not _is_loop(out)
    assert _state(db, chat_a)["phase"] == "open"
    assert _state(db, chat_b) is None


def test_generated_source_when_no_variant(env):
    """An origin with no numbers to nudge (a solved concept-
    free arithmetic result is hard to fake through the API),
    exercised at the module level: the practice_gen source
    serves a same-topic, solver-checkable question."""
    import practice_loop
    session = {}
    state = {"v": 1, "phase": "open", "flavour": "en",
             "item": None,
             "origin_question": "What is the HCF of two "
                                "coprime numbers?",
             "topic": "arithmetic", "topic_label": "Arithmetic",
             "served": []}
    item = practice_loop._next_item(state, 10)
    assert item is not None
    assert item["source"] == "practice"
    assert practice_loop._check(item, item["answer"])
    assert not practice_loop._check(item, "999999")


@pytest.mark.parametrize("text,want", [
    ("Solve for x: 2x + 3 = 9", True),     # a fresh question
    ("Find the LCM of 4 and 6", True),
    ("15% of 240 kitna hoga", True),
    ("ye step samjhao", True),             # Wave-96 doubt turf
    ("kaise ho", True),                    # small talk
    ("999999", False),                     # an answer attempt
    ("42", False),
    ("x = 5", False),
    ("jawab 42 hai", False),               # one number, in words
    ("42 cm", False),
    ("1 1/2", False),
])
def test_fresh_question_classification(text, want):
    import practice_loop
    assert practice_loop._looks_like_fresh_question(text) \
        is want


# ------------------------------------------------------------------ #
# Verification discipline (unit)
# ------------------------------------------------------------------ #

def test_unverifiable_variant_never_served(monkeypatch):
    """When the solver's variant answers carry no checkable
    number — or the solver fails outright — the variant
    source serves nothing (the generated source may still
    serve; the variant itself is discarded, not shown)."""
    import practice_loop
    import solver.router

    state = {"v": 1, "phase": "open", "flavour": "en",
             "item": None,
             "origin_question": "Find the HCF of 12 and 18",
             "topic": "arithmetic", "topic_label": "Arithmetic",
             "served": []}

    def fake_solve(q):
        return {"type": "Ganitra", "op": "gcd",
                "answer": "Yes, always true", "steps": ["x"]}

    monkeypatch.setattr(solver.router, "solve_question",
                        fake_solve)
    assert practice_loop._variant_item(state) is None

    def boom(q):
        raise RuntimeError("nope")

    monkeypatch.setattr(solver.router, "solve_question", boom)
    assert practice_loop._variant_item(state) is None


def test_variant_is_different_and_verified():
    import practice_loop
    state = {"v": 1, "phase": "open", "flavour": "en",
             "item": None,
             "origin_question": "Find the HCF of 12 and 18",
             "topic": "arithmetic", "topic_label": None,
             "served": []}
    item = practice_loop._variant_item(state)
    assert item is not None
    assert item["source"] == "variant"
    assert item["question"] != "Find the HCF of 12 and 18"
    assert practice_loop._check(item, item["answer"])
    assert not practice_loop._check(item, "999999")


def test_handle_message_session_state_machine():
    """The whole loop on a bare session dict (no user/chat):
    start, wrong, continue, correct, exit on a fresh
    question."""
    import practice_loop
    from solver.router import solve_question
    session = {}
    last_result = solve_question("Find the HCF of 12 and 18")
    kwargs = dict(lang="en", lang_request=None,
                  student_class="10",
                  last_question="Find the HCF of 12 and 18",
                  last_result=last_result)

    out = practice_loop.handle_message(
        session, None, None, "one more like this", **kwargs)
    assert out is not None
    state = practice_loop.load_state(session, None, None)
    assert state["phase"] == "open"
    item = state["item"]

    out = practice_loop.handle_message(
        session, None, None, "999999", **kwargs)
    assert out["result"]["answer"].startswith("Wrong")
    assert practice_loop.load_state(
        session, None, None)["phase"] == "done"

    out = practice_loop.handle_message(
        session, None, None, "aur ek", **kwargs)
    assert out is not None
    state = practice_loop.load_state(session, None, None)
    assert state["phase"] == "open"
    assert state["item"]["question"] != item["question"]

    out = practice_loop.handle_message(
        session, None, None, state["item"]["answer"],
        **kwargs)
    assert out["result"].get("test_verdict") == "correct"

    out = practice_loop.handle_message(
        session, None, None, "Find the LCM of 4 and 6",
        **kwargs)
    assert out is None
    assert practice_loop.load_state(session, None, None) \
        is None
