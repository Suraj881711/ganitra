"""Wave 124: chat-based test / exam (Suraj, 17 Nov 2026).

A student can ask for a test INSIDE the chat ("test do") and
take it there: one question at a time, instant exact
checking, score at the end — plus the in-test commands
skip / stop / "answer batao" (answer only, 0 marks, counted
as "Answer dekha") / "solve karke do" (the full solution as
the normal solved card, 0 marks, then the test advances).

Pinned here:
- the intent battery (positives incl. Hindi/Hinglish,
  negatives incl. "latest" / "test tube" / concept asks /
  exam-advice asks / maths phrases containing "test");
- count / class / topic parsing (incl. "class 10 ka test"
  NOT reading the class number as a count);
- a full simulated run through the real /api/solve path:
  start → 3 answers with 1 deliberately wrong → the result
  card shows 2/3 and the weak topic;
- skip, answer-batao, solve-karke-do, stop-mid-test partial
  result, resume-after-reload (server-side per-chat state),
  per-chat isolation;
- the guarantee check: every served question is
  solver-checkable (practice items pass test_mode's own
  checker with their stored answer; starter items re-verify
  against the live solver at serve time);
- test turns are plain (no chips in w122, plain result), so
  Wave 122/123's box / chips / step labels stay off them.
"""
import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")

SIGNUP = {"name": "W124 Tester", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w124-test-pass"}


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
            "SELECT state_json FROM chat_test_state"
            " WHERE chat_id = ?", (str(chat_id),)).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def _lines(data):
    result = data.get("result") or {}
    return [result.get("answer", "")] + list(result.get("steps")
                                             or [])


# --- Intent battery ------------------------------------------

POSITIVE = [
    "test do", "test lo", "mera test lo", "quiz do", "exam lo",
    "mock test", "test chahiye", "sawaal puchho mujhse",
    "मेरा टेस्ट लो", "टेस्ट दो", "टेस्ट चाहिए", "प्रैक्टिस टेस्ट",
    "exam hai mera test karao", "trigonometry ka test",
    "Algebra ka test", "class 10 ka test", "10 sawal ka test",
    "test", "mera test",
]

NEGATIVE = [
    "latest", "test tube", "test kya hota hai",
    "What is a test?", "exam ki taiyari kaise karu",
    "divisibility test for 3", "ratio test",
    "Find the test value",
    "Exam me maths ke question kaise solve karne chahiye?",
    "Find the HCF of 12 and 18", "2x + 3 = 7 solve karo",
    "test series", "What is the capital of France?",
]


def test_intent_battery():
    import chat_test
    for text in POSITIVE:
        assert chat_test.parse_test_request(text) is not None, \
            text
    for text in NEGATIVE:
        assert chat_test.parse_test_request(text) is None, text


def test_parsing_battery():
    import chat_test
    r = chat_test.parse_test_request("class 10 ka test")
    assert r["class_num"] == 10 and r["count"] == 5
    r = chat_test.parse_test_request("10 sawal ka test")
    assert r["count"] == 10 and r["class_num"] is None
    r = chat_test.parse_test_request("10 sawal ka test class 10")
    assert r["count"] == 10 and r["class_num"] == 10
    r = chat_test.parse_test_request("25 sawal ka test do")
    assert r["count"] == 20  # capped
    r = chat_test.parse_test_request("5 question ka test do")
    assert r["count"] == 5
    r = chat_test.parse_test_request("Algebra ka test")
    assert r["topic_key"] == "algebra"
    assert r["topic_label"] == "Algebra"
    r = chat_test.parse_test_request("trigonometry ka test")
    assert r["topic_query"] == "trigonometry"
    r = chat_test.parse_test_request("टेस्ट दो")
    assert r["count"] == 5 and r["topic_key"] is None


def test_command_phrase_battery():
    import chat_test
    for text in ("answer batao", "jawab batao", "उत्तर बताओ",
                 "answer kya hai", "answer bata do"):
        assert chat_test.is_seen_command(text), text
        assert not chat_test.is_solve_command(text), text
    for text in ("solve karke do", "solve kar do",
                 "pura solution do", "हल करके दो",
                 "solve karke batao", "solve"):
        assert chat_test.is_solve_command(text), text
    for text in ("skip", "chhod do", "छोड़ दो", "next question"):
        assert chat_test.is_skip_command(text), text
    for text in ("stop", "band karo", "ruk jao", "बंद करो"):
        assert chat_test.is_stop_command(text), text


# --- Full simulated run through the real solve path ----------

def test_full_run_two_of_three_with_weak_topic(env):
    client, db = env
    chat_id = _new_chat(client)
    data = _solve(client, "3 sawal ka test do", chat_id)
    assert data["ok"] is True
    result = data["result"]
    assert result["fallback_kind"] == "chat_test"
    assert result["plain"] is True
    assert data["w122"]["chips"] == []
    lines = _lines(data)
    assert "Test started" in lines[0] or "Test shuru" in lines[0]
    assert any("Question 1/3" in ln or "Sawal 1/3" in ln
               for ln in lines)
    state = _state(db, chat_id)
    assert state is not None and len(state["items"]) == 3
    answers = [i["answer"] for i in state["items"]]
    weak_topic = state["items"][1]["topic_label"]
    # Q1 correct
    data = _solve(client, answers[0], chat_id)
    assert _lines(data)[0].startswith(("Correct", "Sahi"))
    # Q2 deliberately wrong
    data = _solve(client, "987654321", chat_id)
    assert _lines(data)[0].startswith(("Wrong", "Galat"))
    # Q3 correct -> result card
    data = _solve(client, answers[2], chat_id)
    lines = _lines(data)
    joined = "\n".join(lines)
    assert "Score: 2/3" in joined
    assert ("Correct 2" in joined or "Sahi 2" in joined) \
        and ("Wrong 1" in joined or "Galat 1" in joined)
    assert weak_topic in joined  # the weak topic is named
    assert _state(db, chat_id) is None  # state cleared


def test_skip_and_seen_counted_separately(env):
    client, db = env
    chat_id = _new_chat(client)
    _solve(client, "2 sawal ka test do", chat_id)
    state = _state(db, chat_id)
    first_answer = state["items"][0]["answer"]
    data = _solve(client, "skip", chat_id)
    lines = _lines(data)
    assert lines[0].startswith("Skip")
    assert first_answer in lines[0]  # correct answer shown
    state = _state(db, chat_id)
    second_answer = state["items"][1]["answer"]
    data = _solve(client, "answer batao", chat_id)
    lines = _lines(data)
    assert second_answer in lines[0]
    joined = "\n".join(lines)
    assert "Score: 0/2" in joined
    assert "Answer dekha 1" in joined
    assert "Skip 1" in joined


def test_solve_karke_do_shows_solution_and_scores_zero(env):
    client, db = env
    chat_id = _new_chat(client)
    _solve(client, "2 sawal ka test do", chat_id)
    data = _solve(client, "solve karke do", chat_id)
    result = data["result"]
    # The normal solved card — NOT a plain test turn.
    assert not result.get("plain")
    assert result.get("answer")
    assert result.get("steps")
    assert data["w122"]["chips"] == []  # chips stay OFF in test
    # The test advances underneath the card.
    nxt = data.get("w124_next") or []
    assert any("Question 2/2" in ln or "Sawal 2/2" in ln
               for ln in nxt)
    state = _state(db, chat_id)
    assert state["outcomes"][0]["outcome"] == "solved"
    # Finish: answer Q2 wrong -> result counts the solved one
    # under "Answer dekha", score 0.
    data = _solve(client, "987654321", chat_id)
    joined = "\n".join(_lines(data))
    assert "Score: 0/2" in joined
    assert "Answer dekha 1" in joined


def test_stop_mid_test_partial_result(env):
    client, db = env
    chat_id = _new_chat(client)
    _solve(client, "test do", chat_id)
    state = _state(db, chat_id)
    data = _solve(client, state["items"][0]["answer"], chat_id)
    assert _lines(data)[0].startswith(("Correct", "Sahi"))
    data = _solve(client, "band karo", chat_id)
    joined = "\n".join(_lines(data))
    assert "stopped" in joined or "roka gaya" in joined
    assert "Score: 1/1" in joined  # partial: reached = 1
    assert _state(db, chat_id) is None
    # After the test, a normal question solves normally again.
    data = _solve(client, "Find the HCF of 12 and 18", chat_id)
    assert (data["result"].get("fallback_kind")
            != "chat_test")


def test_resume_after_reload(env):
    client, db = env
    chat_id = _new_chat(client)
    _solve(client, "3 sawal ka test do", chat_id)
    state = _state(db, chat_id)
    _solve(client, state["items"][0]["answer"], chat_id)
    # "Reload": a brand-new client (fresh session cookie)
    # signs in again and answers in the same chat — the
    # server-side state resumes at Question 2.
    from app import create_app
    import os
    app2 = create_app()
    app2.config["TESTING"] = True
    c2 = app2.test_client()
    r = c2.post("/login", data={"name": SIGNUP["name"],
                                "password": SIGNUP["password"]})
    assert r.status_code in (200, 302)
    state = _state(db, chat_id)
    assert state["index"] == 1
    data = _solve(c2, state["items"][1]["answer"], chat_id)
    assert _lines(data)[0].startswith(("Correct", "Sahi"))
    state = _state(db, chat_id)
    assert state["index"] == 2


def test_per_chat_isolation(env):
    client, db = env
    chat_a = _new_chat(client)
    chat_b = _new_chat(client)
    _solve(client, "test do", chat_a)
    # A plain maths question in chat B is a normal solve, NOT
    # an answer attempt on chat A's test.
    data = _solve(client, "Find the HCF of 12 and 18", chat_b)
    assert (data["result"].get("fallback_kind")
            != "chat_test")
    assert _state(db, chat_b) is None
    state_a = _state(db, chat_a)
    assert state_a is not None and state_a["index"] == 0


def test_negatives_do_not_start_a_test(env):
    client, db = env
    chat_id = _new_chat(client)
    for text in ("latest", "test tube"):
        data = _solve(client, text, chat_id)
        assert (data.get("result") or {}).get(
            "fallback_kind") != "chat_test"
        assert _state(db, chat_id) is None


def test_hindi_test_flow(env):
    client, db = env
    chat_id = _new_chat(client)
    data = _solve(client, "टेस्ट दो", chat_id)
    lines = _lines(data)
    assert lines[0].startswith("टेस्ट शुरू")
    assert any(ln.startswith("सवाल 1/") for ln in lines)


# --- The guarantee: every served question is checkable -------

def test_every_served_question_is_checkable():
    import random
    import chat_test
    import test_mode
    from full_paper import answers_match
    from i18n import solve_failed
    from solver.router import solve_question
    rng = random.Random(124)
    for class_num, topic_key in ((10, None), (10, "algebra"),
                                 (8, None)):
        req = {"count": 5, "class_num": class_num,
               "topic_key": topic_key, "topic_query": None,
               "topic_label": None}
        items, _note = chat_test._generate(req, class_num, rng)
        assert items
        for item in items:
            assert test_mode.check_test_answer(
                item["check"], item["answer"]), item
    # Starter path (named topic + a young class): re-verify
    # each served starter against the live solver.
    req = {"count": 3, "class_num": 10, "topic_key": None,
           "topic_query": "trigonometry", "topic_label": "X"}
    items, _note = chat_test._generate(req, 10, rng)
    assert items
    for item in items:
        result = solve_question(item["question"])
        assert not solve_failed(item["question"], result)
        assert answers_match(item["answer"],
                             result.get("answer", ""))
    req = {"count": 3, "class_num": 3, "topic_key": None,
           "topic_query": None, "topic_label": None}
    items, _note = chat_test._generate(req, 3, rng)
    assert items
    for item in items:
        result = solve_question(item["question"])
        assert not solve_failed(item["question"], result)
        assert answers_match(item["answer"],
                             result.get("answer", ""))


# --- Client wiring -------------------------------------------

def test_client_sends_chat_id_and_renders_w124_next():
    assert "chat_id: chatId" in INDEX
    assert INDEX.count("chat_id: chatId") == 2
    assert "w124AppendNext" in INDEX
    assert 'result.op !== "chat_test_solve"' in INDEX
