"""Wave 90: the not-found learning log (notfound_log.py).

Every question that ends at the Wave 67 one-line "Answer not
found" is recorded — question text (normalised), detected
language, the student's class when known, and how the chain
gave up — so future waves target real student failures.
Proven here:

- a not-found question creates ONE row; the same question
  again (any casing/punctuation — bank normalisation decides
  sameness) increments its counter instead of adding a row;
- a solved / concept / greeting answer creates NO row;
- the recorded fields are exactly the promised set (question,
  language, class, stage, terminal kind, hits, timestamps) —
  and the schema holds NO account data (privacy pin);
- the owner report groups and orders correctly, and its
  JSONL export carries the same rows;
- the log is observational: answers are byte-identical with
  logging on and off, and a logging failure (raising logger,
  unwritable DB) never breaks or alters the chat answer;
- migration safety: a pre-Wave-90 DB (accounts tables only)
  gains the table on first use, existing tables untouched.
"""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import notfound_log
from fallback import fallback_answer

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "nf.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_NFLOG", raising=False)
    return path


def _rows():
    return notfound_log.all_rows()


# --- 1. A not-found question is logged; repeats dedupe ------

def test_not_found_question_creates_row(db):
    res = fallback_answer("If tu gfuf")
    assert res["fallback_kind"] == "not_found"
    rows = _rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["question_norm"] == "if tu gfuf"
    assert row["question_text"] == "If tu gfuf"
    assert row["language"] == "en"
    assert row["student_class"] is None
    assert row["stage"] == "all_missed"
    assert row["terminal_kind"] in ("gibberish", "guide")
    assert row["hits"] == 1
    assert row["first_seen"] > 0
    assert row["last_seen"] >= row["first_seen"]


def test_repeat_increments_counter_not_rows(db):
    fallback_answer("If tu gfuf")
    fallback_answer("if tu gfuf!")
    fallback_answer("IF TU GFUF")
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["hits"] == 3
    # First-seen raw text is the kept example.
    assert rows[0]["question_text"] == "If tu gfuf"


def test_hindi_not_found_logs_hindi(db):
    res = fallback_answer("कुछ भी लिख दिया बकवास")
    assert res["fallback_kind"] == "not_found"
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["language"] == "hi"


def test_student_class_recorded_when_known(db):
    fallback_answer("asdf qwer", student_class=7)
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["student_class"] == 7


def test_bad_class_values_become_none(db):
    assert notfound_log.log_not_found("zxq vbt plok",
                                      student_class="abc")
    assert notfound_log.log_not_found("mnb lkj poi",
                                      student_class=42)
    rows = _rows()
    assert len(rows) == 2
    assert all(r["student_class"] is None for r in rows)


# --- 2. Non-not-found outcomes log nothing -------------------

@pytest.mark.parametrize("question", [
    "2 + 2 = ?",                                  # solver
    "what is the formula for area of a circle",   # concept card
    "hello",                                      # greeting line
    "samjhao",                                    # vague line
])
def test_other_outcomes_create_no_row(db, question):
    fallback_answer(question)
    assert _rows() == []


# --- 3. Privacy: the schema is exactly the promised set -----

def test_schema_columns_are_exactly_the_promised_set(db):
    notfound_log.log_not_found("zxq vbt plok")
    conn = sqlite3.connect(str(db))
    try:
        cols = {r[1] for r in conn.execute(
            "PRAGMA table_info(not_found_log)")}
    finally:
        conn.close()
    assert cols == {
        "id", "question_norm", "question_text", "language",
        "student_class", "stage", "terminal_kind", "hits",
        "first_seen", "last_seen",
    }
    # No account/credential-shaped field can ever sneak in.
    for col in cols:
        for banned in ("pw", "pass", "fav", "goal", "hobby",
                       "name", "user", "hash"):
            assert banned not in col


# --- 4. Report grouping + JSONL export -----------------------

def test_report_groups_orders_and_exports(db, tmp_path):
    for _ in range(3):
        notfound_log.log_not_found("question alpha unsolved")
    notfound_log.log_not_found("question beta unsolved")
    notfound_log.log_not_found("question beta unsolved")
    notfound_log.log_not_found("question gamma unsolved")

    top = notfound_log.top_failures(limit=2)
    assert [r["question_norm"] for r in top] == [
        "question alpha unsolved", "question beta unsolved"]
    assert [r["hits"] for r in top] == [3, 2]

    out = tmp_path / "nf.jsonl"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" /
                             "notfound_report.py"),
         "--limit", "5", "--export", str(out)],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PATH": "/usr/bin:/bin:/usr/local/bin",
             "GANITRA_DB_PATH": str(db),
             "HOME": str(tmp_path)})
    assert proc.returncode == 0, proc.stderr
    assert "3 distinct questions, 6 total asks" in proc.stdout
    # Most-asked first in the printed report.
    assert proc.stdout.index("question alpha unsolved") < \
        proc.stdout.index("question beta unsolved")
    exported = [json.loads(line)
                for line in out.read_text(encoding="utf-8")
                .splitlines() if line.strip()]
    assert len(exported) == 3
    assert exported[0]["question_norm"] == \
        "question alpha unsolved"
    assert exported[0]["hits"] == 3


def test_report_on_empty_log_is_calm(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" /
                             "notfound_report.py")],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PATH": "/usr/bin:/bin:/usr/local/bin",
             "GANITRA_DB_PATH": str(tmp_path / "missing.db"),
             "HOME": str(tmp_path)})
    assert proc.returncode == 0, proc.stderr
    assert "No not-found questions logged yet." in proc.stdout
    # Reading must not create the DB file.
    assert not (tmp_path / "missing.db").exists()


# --- 5. Observational: answers never change ------------------

_BATTERY = [
    "If tu gfuf",
    "asdf qwer",
    "कुछ भी लिख दिया बकवास",
    "2 + 2 = ?",
    "what is the formula for area of a circle",
    "hello",
    "samjhao",
]


def test_answers_byte_identical_logging_on_and_off(
        db, tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_NFLOG", "0")
    off = [fallback_answer(q) for q in _BATTERY]
    assert _rows() == []  # off means off

    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "on.db"))
    monkeypatch.delenv("GANITRA_NFLOG")
    on = [fallback_answer(q) for q in _BATTERY]
    assert on == off
    # …and the on-run really did log the not-found subset.
    assert len(_rows()) == 3


def test_raising_logger_never_breaks_the_answer(
        db, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("log exploded")

    monkeypatch.setattr(notfound_log, "log_not_found", boom)
    res = fallback_answer("If tu gfuf")
    assert res["fallback_kind"] == "not_found"
    # Wave 204 (Suraj, 20 Nov): ans not found hamesha ke liye band
    assert res["answer"] == \
        "I didn't understand that — type your maths " \
        "question a little clearly and I'll solve it " \
        "right away."
    assert res["steps"] == []


def test_unwritable_db_never_breaks_the_answer(
        tmp_path, monkeypatch):
    # A directory where the DB file should be: connect fails.
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    assert notfound_log.log_not_found("zxq vbt plok") is False
    res = fallback_answer("If tu gfuf")
    assert res["fallback_kind"] == "not_found"
    # Wave 204 (Suraj, 20 Nov): ans not found hamesha ke liye band
    assert res["answer"] == \
        "I didn't understand that — type your maths " \
        "question a little clearly and I'll solve it " \
        "right away."


def test_log_write_is_a_silent_noop_when_disabled(
        db, monkeypatch):
    monkeypatch.setenv("GANITRA_NFLOG", "0")
    assert notfound_log.log_not_found("zxq vbt plok") is False
    assert _rows() == []
    assert not db.exists()  # not even the file is created


# --- 6. Migration safety on a pre-Wave-90 database -----------

def test_old_db_gains_table_existing_tables_untouched(
        db, monkeypatch):
    import accounts
    accounts.init_db()  # a pre-Wave-90 DB: accounts tables only
    conn = sqlite3.connect(str(db))
    try:
        before = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE"
            " type='table'")}
    finally:
        conn.close()
    assert "users" in before and "not_found_log" not in before

    assert notfound_log.log_not_found("zxq vbt plok") is True

    conn = sqlite3.connect(str(db))
    try:
        after = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE"
            " type='table'")}
        users = conn.execute(
            "SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()
    assert "not_found_log" in after
    assert before <= after  # nothing was dropped or renamed
    assert users == 0
