"""Wave 201: the PRACTICE-REQUEST intent (Suraj's live
test, 20 Nov 2026).

Suraj typed into the chat:

    "12th class ke kuch qustin milinge solve karane ke liye"

and got the bare not-found line — "solve karne ke liye
question kyu nhi de rha, ye kuch toh bole, ye koi baat
nhi hoti ans not found". Root cause (verified): no
recogniser existed for a practice-question REQUEST;
guidance only gives practice ADVICE.

Fix: practice_req.py — a first-class intent in api_solve
(after chat-test / guided / practice-loop, before the
galti block). It serves 4 real, verified questions for
the named class (practice_gen for Classes 6-10,
serve-time-verified concept starters for every class —
chat_test's own sources), asks the class in one friendly
line when none is named (never the not-found line), and
"aur do" serves the next, different set in the same
chat.

Pinned here:
- the recognition battery (EN / Hinglish / Devanagari
  positives; negatives for every neighbour: paper asks,
  test asks, fact asks, advice asks, concrete problems,
  the Wave-165 loop triggers);
- the live phrase end-to-end: a practice_req card with
  >= 3 numbered Class 12 questions, no answers shown, no
  not-found, not a solved result, no chips;
- EN + Devanagari serves; the class-less ask + class
  reply flow in both scripts;
- "aur do" serves a DIFFERENT set; a fresh chat's
  "aur do" serves nothing of this module;
- a chapter-named ask serves that chapter;
- every gathered item carries a checkable answer
  (practice items pass test_mode's own checker);
- non-hijack end-to-end: "test do" still starts the
  chat test, "class 12 ka paper do" still papers,
  a concrete problem still solves, "practice kaise
  karu" still lands on advice;
- the parked ask releases on any other message.
"""
import re
import sqlite3
from pathlib import Path

import pytest

import practice_req
import test_mode
from followups import is_solved_result
from practice_req import is_more_request, parse_practice_request

ROOT = Path(__file__).resolve().parent.parent

LIVE = "12th class ke kuch qustin milinge solve karane ke liye"
NOT_FOUND = {"Answer not found.", "Answer nahi mila.",
             "उत्तर नहीं मिला।"}

SIGNUP = {"name": "W201 Tester", "class": "12",
          "board": "CBSE", "goal": "Doctor",
          "hobby": "Cricket", "favourite": "Pizza",
          "password": "w201-test-pass"}


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the AI legs stay inert — a practice
    request must never reach them anyway."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


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


def _ask(client, question, chat_id=None):
    payload = {"question": question}
    if chat_id is not None:
        payload["chat_id"] = chat_id
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


def _result(payload):
    return payload.get("result") or {}


def _lines(payload):
    result = _result(payload)
    return [result.get("answer") or ""] \
        + list(result.get("steps") or [])


def _questions(payload):
    """The numbered question lines of a practice card."""
    return [line for line in _lines(payload)
            if re.match(r"^\d+\.\s", line)]


def _state(db, chat_id):
    conn = sqlite3.connect(str(db))
    try:
        row = conn.execute(
            "SELECT state_json FROM practice_req_state"
            " WHERE chat_id = ?", (str(chat_id),)).fetchone()
    finally:
        conn.close()
    import json
    return json.loads(row[0]) if row else None


# ------------------------------------------------------------------ #
# 1. Recognition battery (unit)
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("text,cls", [
    (LIVE, 12),
    ("give me some class 10 questions", 10),
    ("12th class ke questions do", 12),
    ("class 12 maths questions", 12),
    ("class 10 questions", 10),
    ("integrals ke questions do class 12", 12),
    ("मुझे अभ्यास के लिए प्रश्न दो कक्षा 9", 9),
])
def test_parse_positives_with_class(text, cls):
    req = parse_practice_request(text)
    assert req is not None, text
    assert req["class_num"] == cls, text


@pytest.mark.parametrize("text", [
    "practice questions chahiye",
    "sawal do practice ke liye",
    "practice karna hai questions do",
    "mujhe kuch questions chahiye",
    "questions do",
    "मुझे अभ्यास के लिए प्रश्न दो",
])
def test_parse_positives_without_class(text):
    req = parse_practice_request(text)
    assert req is not None, text
    assert req["class_num"] is None, text


def test_live_phrase_has_no_phantom_topic():
    # "milinge" (the student's spelling of milenge) is a
    # request verb, never a chapter name.
    req = parse_practice_request(LIVE)
    assert req["topic_query"] is None
    assert req["topic_key"] is None


def test_chapter_and_topic_parse():
    req = parse_practice_request(
        "integrals ke questions do class 12")
    assert req["topic_query"] == "integrals"
    req = parse_practice_request(
        "probability questions class 10")
    assert req["topic_key"] == "probability"


@pytest.mark.parametrize("text", [
    "test do",                              # Wave 124 owns it
    "class 10 ka test do",
    "class 12 ka paper do",                 # Wave 174 owns it
    "class 12 ka maths ka paper chahiye 2025",
    "practice kaise karu",                  # advice, not a request
    "maths ki practice kaise karu",
    "exam ki taiyari kaise karu",
    "2x + 3 = 11 solve karo",               # a concrete problem
    "find the value of x in the question 2x+3=11",
    "0 ki khoj kisne ki",                   # a fact ask
    "paper me kitne questions aate hai",    # a how-many ask
    "ye question kya hai",
    "questions kya hote hai",
    "ek aur aisa hi sawal",                 # Wave 165 owns it
    "aur practice karni hai",
    "one more like this",
    "hello",
])
def test_parse_negatives(text):
    assert parse_practice_request(text) is None, text


@pytest.mark.parametrize("text,expected", [
    ("aur do", True), ("more", True), ("और दो", True),
    ("mujhe aur do", True), ("aur do please", True),
    ("aur questions do", True),
    ("solve karo aur do", False),
    ("aur doosra question solve karo", False),
    ("2x + 3 = 11", False),
])
def test_more_request(text, expected):
    assert is_more_request(text) is expected, text


# ------------------------------------------------------------------ #
# 2. The live phrase, end to end
# ------------------------------------------------------------------ #

def test_live_phrase_serves_class12_card(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, LIVE, chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert result.get("answer") not in NOT_FOUND
    questions = _questions(payload)
    assert len(questions) >= 3, _lines(payload)
    # No answers are shown with the questions.
    body = "\n".join(_lines(payload))
    assert "Answer:" not in body
    # Library content, not a solve: no answer box / chips.
    assert is_solved_result(result) is False
    assert (payload.get("w122") or {}).get("chips") == []


def test_english_request_serves_card(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "give me some class 10 questions",
                   chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert "Class 10" in (result.get("answer") or "")
    assert len(_questions(payload)) >= 3


def test_devanagari_request_asks_then_serves(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "मुझे अभ्यास के लिए प्रश्न दो", chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert result.get("plain_reply")
    assert "कक्षा" in (result.get("answer") or "")
    payload = _ask(client, "कक्षा 12", chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert len(_questions(payload)) >= 3


# ------------------------------------------------------------------ #
# 3. Class-less flow
# ------------------------------------------------------------------ #

def test_classless_ask_then_class_reply(env):
    client, db = env
    chat = _new_chat(client)
    payload = _ask(client, "questions chahiye", chat)
    result = _result(payload)
    assert result.get("op") == "practice_req_ask"
    assert result.get("answer") not in NOT_FOUND
    assert _state(db, chat)["pending_class"] is True
    payload = _ask(client, "10", chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert "Class 10" in (result.get("answer") or "")
    assert len(_questions(payload)) >= 3
    assert _state(db, chat)["pending_class"] is False


def test_park_releases_on_a_real_question(env):
    client, db = env
    chat = _new_chat(client)
    _ask(client, "questions chahiye", chat)
    payload = _ask(client, "2x + 3 = 11 solve karo", chat)
    result = _result(payload)
    assert result.get("fallback_kind") != "practice_req"
    assert "4" in (result.get("answer") or "")
    assert _state(db, chat) is None


# ------------------------------------------------------------------ #
# 4. "aur do" — the next set, never a repeat
# ------------------------------------------------------------------ #

def test_aur_do_serves_a_different_set(env):
    client, _db = env
    chat = _new_chat(client)
    first = _ask(client, LIVE, chat)
    first_qs = set(_questions(first))
    assert len(first_qs) >= 3
    second = _ask(client, "aur do", chat)
    result = _result(second)
    assert result.get("fallback_kind") == "practice_req"
    second_qs = set(_questions(second))
    assert len(second_qs) >= 3
    assert not (first_qs & second_qs), (first_qs, second_qs)


def test_aur_do_in_a_fresh_chat_serves_nothing(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "aur do", chat)
    assert _result(payload).get("fallback_kind") \
        != "practice_req"


def test_fresh_request_replaces_the_set(env):
    client, _db = env
    chat = _new_chat(client)
    _ask(client, LIVE, chat)
    payload = _ask(client, "give me some class 10 questions",
                   chat)
    result = _result(payload)
    assert result.get("fallback_kind") == "practice_req"
    assert "Class 10" in (result.get("answer") or "")


# ------------------------------------------------------------------ #
# 5. Chapter-named + verified material (unit level)
# ------------------------------------------------------------------ #

def test_chapter_named_gather_serves_that_chapter():
    import random
    items, _note = practice_req._gather(
        12, None, "integrals", 4, random.Random(3), set())
    assert len(items) >= 3
    hits = [i for i in items
            if "ntegr" in i["question"]
            or "ntegr" in (i.get("topic_label") or "")]
    assert len(hits) >= 3, [i["question"] for i in items]


@pytest.mark.parametrize("cls", [4, 5, 6, 9, 10, 11, 12])
def test_every_class_has_verified_material(cls):
    import random
    items, _note = practice_req._gather(
        cls, None, None, 4, random.Random(11), set())
    assert len(items) >= 3, cls
    for item in items:
        # A known-correct answer rides with every served
        # question (never shown, always checkable).
        assert str(item.get("answer") or "").strip(), item
        if item.get("source") == "practice":
            assert test_mode.check_test_answer(
                item["check"], item["answer"]), item


# ------------------------------------------------------------------ #
# 6. Non-hijack, end to end
# ------------------------------------------------------------------ #

def test_test_do_still_starts_the_chat_test(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "test do", chat)
    assert _result(payload).get("fallback_kind") \
        == "chat_test"


def test_paper_ask_still_papers(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "class 12 ka paper do", chat)
    assert _result(payload).get("fallback_kind") == "paper"


def test_concrete_problem_still_solves(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "2x + 3 = 11 solve karo", chat)
    result = _result(payload)
    assert result.get("fallback_kind") != "practice_req"
    assert "4" in (result.get("answer") or "")


def test_practice_advice_still_advice(env):
    client, _db = env
    chat = _new_chat(client)
    payload = _ask(client, "practice kaise karu", chat)
    assert _result(payload).get("fallback_kind") in (
        "advice", "guidance")


# ------------------------------------------------------------------ #
# 7. Delivery pins
# ------------------------------------------------------------------ #

def test_practice_req_kind_registered():
    import followups
    assert "practice_req" in followups._NOT_SOLVED_KINDS
    js = (ROOT / "templates" / "index.html").read_text(
        encoding="utf-8")
    m = re.search(r"W122_NOT_SOLVED_KINDS = \[(.*?)\];", js,
                  re.S)
    assert m and '"practice_req"' in m.group(1)
