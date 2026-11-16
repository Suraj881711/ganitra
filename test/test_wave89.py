"""Wave 89: My Progress — a per-student record page built only
from data the app already stores.

Pins: the answered taxonomy (progress.is_answered), the
account totals against seeded chats (asked/answered/chats and
the weekly series, exact numbers), privacy (another student's
data never leaks into the page), the empty state for a new
student, the session-side pieces (Mistake Notebook weak
topics, last test report), the print view, the menu entry
(appended last, approved order untouched) and the login gate.
"""
import sqlite3
import time
from datetime import datetime, timedelta

import pytest


@pytest.fixture()
def app_env(tmp_path, monkeypatch):
    db = tmp_path / "users.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(db))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app, db


def _signup(app, name):
    c = app.test_client()
    resp = c.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w89-test-pass"})
    assert resp.status_code in (200, 302)
    with c.session_transaction() as sess:
        uid = sess.get("user_id")
    assert uid
    return c, uid


def _monday_ts(weeks_ago=0):
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday() + 7 * weeks_ago)
    return int(datetime(monday.year, monday.month, monday.day,
                        10, 0).timestamp())


def _seed_chat(db, uid, messages, updated_ts):
    import chats
    chat = chats.create_chat(uid)
    chats.save_chat(uid, chat["id"], messages)
    conn = sqlite3.connect(db)
    conn.execute("UPDATE chats SET created_at = ?, updated_at = ?"
                 " WHERE id = ?", (updated_ts - 60, updated_ts,
                                   chat["id"]))
    conn.commit()
    conn.close()
    return chat["id"]


def _user(text):
    return {"role": "user", "text": text}


def _bot(data):
    return {"role": "bot", "data": data}


SOLVED = {"answer": "42", "op": "arithmetic", "steps": ["40 + 2"]}
BANKED = {"answer": "7", "op": "bank", "fallback": True,
          "fallback_kind": "bank", "source": "bank"}
TOPIC = {"answer": "HCF — 6", "op": "hcf", "fallback": True,
         "fallback_kind": "concept", "source": "topics"}
NOT_FOUND = {"answer": "Answer not found", "fallback": True,
             "fallback_kind": "not_found"}
SIMILAR = {"answer": "Similar example", "fallback": True,
           "fallback_kind": "similar"}
GREETING = {"answer": "Hello!", "fallback": True,
            "fallback_kind": "greeting", "plain_reply": True}


def _seed_student_a(app, db):
    """Student A: 6 questions asked across 3 chats (3 this
    week, 2 two weeks ago... see per-chat layout), 3 answered."""
    client, uid = _signup(app, "W89 Progress Tester")
    # This week: a greeting (not a question answered) + a
    # concept-topic answer.
    _seed_chat(db, uid, [_user("hello"), _bot(GREETING),
                         _user("HCF kya hota hai?"), _bot(TOPIC)],
               _monday_ts(0) + 3600)
    # Last week: a similar-example reply — NOT an answer.
    _seed_chat(db, uid, [_user("tough integral"), _bot(SIMILAR)],
               _monday_ts(1) + 3600)
    # Two weeks ago: one solved, one banked, one not found.
    _seed_chat(db, uid, [_user("40 + 2?"), _bot(SOLVED),
                         _user("banked question"), _bot(BANKED),
                         _user("gibberish xyz"), _bot(NOT_FOUND)],
               _monday_ts(2) + 3600)
    return client, uid


# --- the answered taxonomy ------------------------------------

def test_is_answered_taxonomy():
    import progress
    assert progress.is_answered(SOLVED)
    assert progress.is_answered(BANKED)
    assert progress.is_answered(TOPIC)
    assert progress.is_answered(
        {"answer": "x", "fallback_kind": "gemini"})
    assert progress.is_answered(
        {"answer": "x", "fallback_kind": "salvage"})
    assert not progress.is_answered(NOT_FOUND)
    assert not progress.is_answered(SIMILAR)
    assert not progress.is_answered(GREETING)
    assert not progress.is_answered(
        {"answer": "card", "fallback_kind": "concept"})
    assert not progress.is_answered(
        {"answer": "guide", "fallback_kind": "guide"})
    assert not progress.is_answered(None)
    assert not progress.is_answered("not a dict")


# --- account totals -------------------------------------------

def test_collect_progress_exact_numbers(app_env):
    app, db = app_env
    _client, uid = _seed_student_a(app, db)
    import progress
    record = progress.collect_progress(uid)
    assert record["asked"] == 6
    assert record["answered"] == 3
    assert record["chats"] == 3
    assert record["answered_pct"] == 50
    weeks = {w["label"]: w["count"] for w in record["weeks"]}
    fmt = "%d %b"
    this_monday = datetime.fromtimestamp(_monday_ts(0)).strftime(fmt)
    last_monday = datetime.fromtimestamp(_monday_ts(1)).strftime(fmt)
    older_monday = datetime.fromtimestamp(_monday_ts(2)).strftime(fmt)
    assert weeks[this_monday] == 2
    assert weeks[last_monday] == 1
    assert weeks[older_monday] == 3
    assert sum(weeks.values()) == 6
    assert len(record["weeks"]) == 8
    assert record["weeks"][-1]["current"] is True


def test_progress_page_renders_seeded_numbers(app_env):
    app, db = app_env
    client, _uid = _seed_student_a(app, db)
    body = client.get("/progress").get_data(as_text=True)
    assert 'data-asked="6"' in body
    assert 'data-answered="3"' in body
    assert 'data-chats="3"' in body
    assert "W89 Progress Tester" in body
    assert "<svg" in body  # the weekly chart


# --- privacy ----------------------------------------------------

def test_other_students_data_never_leaks(app_env):
    app, db = app_env
    client_a, _uid_a = _seed_student_a(app, db)
    client_b, uid_b = _signup(app, "W89 Other Student")
    _seed_chat(db, uid_b, [_user("2+2?"), _bot(SOLVED),
                           _user("3+3?"), _bot(SOLVED)],
               _monday_ts(0) + 7200)
    body_a = client_a.get("/progress").get_data(as_text=True)
    assert 'data-asked="6"' in body_a  # unchanged by B's chats
    assert "W89 Other Student" not in body_a
    body_b = client_b.get("/progress").get_data(as_text=True)
    assert 'data-asked="2"' in body_b
    assert 'data-answered="2"' in body_b
    assert "W89 Progress Tester" not in body_b


def test_progress_requires_login(app_env):
    app, _db = app_env
    anon = app.test_client()
    assert anon.get("/progress").status_code == 302
    assert anon.get("/progress/print").status_code == 302


# --- empty state -------------------------------------------------

def test_empty_state_for_new_student(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W89 Brand New")
    body = client.get("/progress").get_data(as_text=True)
    assert 'data-asked="0"' in body
    assert "Your progress story starts here" in body
    assert "<svg" not in body  # no chart before any question
    assert "No weak topics yet" in body


# --- session-side pieces -----------------------------------------

def test_weak_topics_and_last_test_from_session(app_env):
    app, db = app_env
    client, _uid = _seed_student_a(app, db)
    with client.session_transaction() as sess:
        sess["mistakes"] = [
            {"question": "q1", "expected": "3", "given": "2",
             "topic": "algebra", "source": "quiz"},
            {"question": "q2", "expected": "5", "given": "4",
             "topic": "algebra", "source": "quiz"},
            {"question": "q3", "expected": "9", "given": "1",
             "topic": None, "source": "Class 8 · Triangles"},
            {"question": "q4", "expected": "9", "given": "2",
             "topic": None, "source": "Class 8 · Triangles"},
            {"question": "q5", "expected": "9", "given": "3",
             "topic": None, "source": "Class 8 · Triangles"},
        ]
        sess["last_test_report"] = {
            "score": 7, "total": 10, "remark_key": "remark_good",
            "lost_topics": ["Algebra"], "chapter": None,
            "celebrate": False}
    body = client.get("/progress").get_data(as_text=True)
    assert "Class 8 · Triangles — 3" in body
    assert "Algebra — 2" in body
    # most-missed topic first
    assert body.index("Triangles") < body.index("Algebra — 2")
    assert "7 / 10" in body


# --- print view ---------------------------------------------------

def test_print_view_renders(app_env):
    app, db = app_env
    client, _uid = _seed_student_a(app, db)
    resp = client.get("/progress/print")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'id="print-asked">6<' in body
    assert 'id="print-answered">3<' in body
    assert "W89 Progress Tester" in body
    assert "window.print" in body


# --- placement: menu (appended last) + back pill ------------------

def test_menu_link_appended_after_parent_report(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W89 Menu Check")
    body = client.get("/").get_data(as_text=True)
    assert 'href="/progress"' in body
    assert (body.index('href="/parent-report"')
            < body.index('href="/progress"'))


def test_backnav_covers_progress():
    from app import _backnav_for_path
    assert _backnav_for_path("/progress") == ("/", None)
    assert _backnav_for_path("/progress/print") == ("/", None)
