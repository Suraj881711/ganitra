"""Wave 90: the not-found learning log.

Every question that ends at the Wave 67 one-line "Answer not
found" is a real student failure the solver, the bank, the MCQ
layer, salvage, the concept layers and the AI chain ALL missed.
Until now those failures vanished — the next wave's targets
came from hand-built audits (Wave 71) instead of from what
students actually asked. This module records them so future
waves target real failures first.

WHAT IS LOGGED (and nothing else): the question text itself
(first-seen raw form, capped at the app's own 500-char question
limit), its normalised form (bank.normalise_question — the
same normalisation the bank indexes by, so a logged failure
can be matched against bank/solver work later), the detected
language, the student's class when the session knows it, a
timestamp, and how the chain gave up (`stage` = "all_missed";
`terminal_kind` = the honest layer that was standing when the
answer collapsed — similar / gibberish / guide).

PRIVACY: question text only. No name, no user id, no account
field of any kind is read or stored — passwords and the three
favourite answers are hashes in accounts.py and never leave
it; this module does not import a single account record, only
the DB *path* helper. The schema below is the whole record;
test_wave90 pins its column set.

DEDUPE: one row per normalised question. A repeat of the same
question (any casing/punctuation — the bank normalisation
decides sameness) increments `hits` and moves `last_seen`
instead of adding a row, via the UNIQUE index on
question_norm — the write stays one indexed upsert.

SAFETY: the log is purely observational. log_not_found()
NEVER raises and never changes an answer: any failure (DB
locked, disk full, table gone, bad input) is a silent no-op
returning False, and the chat flow wraps the call in its own
guard as well. Set GANITRA_NFLOG=0 to switch logging off
entirely (answers are byte-identical either way — proven in
test_wave90).

The table lives in the existing accounts DB (accounts.db_path
— GANITRA_DB_PATH env wins, as everywhere) and is created with
CREATE TABLE IF NOT EXISTS on the write path, the same
migration-safe pattern accounts.py / chats.py use: an old DB
file gains the table on the first logged failure, and no other
table is touched.

Owner tooling: scripts/notfound_report.py prints the top
grouped failures and exports them to JSONL for wave building.
"""
import os
import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS not_found_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_norm TEXT NOT NULL UNIQUE,
    question_text TEXT NOT NULL,
    language      TEXT,
    student_class INTEGER,
    stage         TEXT NOT NULL DEFAULT 'all_missed',
    terminal_kind TEXT,
    hits          INTEGER NOT NULL DEFAULT 1,
    first_seen    INTEGER NOT NULL,
    last_seen     INTEGER NOT NULL
)
"""

# The dedupe lookup rides the UNIQUE index on question_norm;
# this one serves the report's "most recent failures" order.
_INDEX = ("CREATE INDEX IF NOT EXISTS idx_not_found_last_seen"
          " ON not_found_log(last_seen)")

_TEXT_CAP = 500  # the app's own question limit (api/app)


def _enabled():
    return os.environ.get("GANITRA_NFLOG", "1").strip() != "0"


def _db_path():
    # Lazy import: accounts.py is stdlib-only, but keeping the
    # import inside the call matches bank.py's optional-layer
    # pattern and can never create an import cycle.
    from accounts import db_path
    return db_path()


def _normalise(text):
    """bank.normalise_question when available (it always is in
    the app); a local lowercase/collapse fallback so the log
    still groups sanely if the bank module ever fails to load."""
    try:
        from bank import normalise_question
        return normalise_question(text)
    except Exception:
        import re
        import unicodedata
        t = unicodedata.normalize("NFC", str(text or "")).lower()
        return re.sub(r"\s+", " ", t).strip()


def _clean_class(value):
    """The student's class as an int in the app's 0–12 range,
    else None (anonymous / unknown / unparsable)."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if 0 <= n <= 12 else None


def log_not_found(question, lang=None, student_class=None,
                  stage="all_missed", terminal_kind=None):
    """Record one not-found outcome. Returns True when a row
    was created or incremented, False for any no-op (logging
    off, empty question, ANY error). Never raises: a logging
    failure must not slow, break or alter the chat answer —
    the write is one indexed upsert on a short-timeout
    connection, and the whole body is guarded."""
    if not _enabled():
        return False
    try:
        norm = _normalise(question)
        if not norm:
            return False
        text = str(question or "").strip()[:_TEXT_CAP]
        if not text:
            return False
        now = int(time.time())
        conn = sqlite3.connect(_db_path(), timeout=2.0)
        try:
            conn.execute(_SCHEMA)
            conn.execute(_INDEX)
            try:
                conn.execute(
                    "INSERT INTO not_found_log (question_norm,"
                    " question_text, language, student_class,"
                    " stage, terminal_kind, hits, first_seen,"
                    " last_seen) VALUES (?, ?, ?, ?, ?, ?, 1,"
                    " ?, ?)"
                    " ON CONFLICT(question_norm) DO UPDATE SET"
                    " hits = hits + 1, last_seen = excluded"
                    ".last_seen",
                    (norm, text, lang, _clean_class(student_class),
                     stage, terminal_kind, now, now))
            except sqlite3.OperationalError:
                # Pre-3.24 SQLite has no UPSERT: two-step form.
                conn.execute(
                    "INSERT OR IGNORE INTO not_found_log"
                    " (question_norm, question_text, language,"
                    " student_class, stage, terminal_kind, hits,"
                    " first_seen, last_seen) VALUES (?, ?, ?, ?,"
                    " ?, ?, 1, ?, ?)",
                    (norm, text, lang, _clean_class(student_class),
                     stage, terminal_kind, now, now))
                conn.execute(
                    "UPDATE not_found_log SET hits = hits + 1,"
                    " last_seen = ? WHERE question_norm = ?",
                    (now, norm))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def _read_rows(db_path=None, limit=None):
    """All logged rows as dicts, most-hit first (then most
    recent). Read-only in spirit: a missing DB file or a
    not-yet-created table reads as an empty log, never an
    error, and reading never creates the file."""
    path = db_path or _db_path()
    if not os.path.isfile(path):
        return []
    try:
        conn = sqlite3.connect(path, timeout=2.0)
        try:
            conn.row_factory = sqlite3.Row
            found = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table'"
                " AND name='not_found_log'").fetchone()
            if not found:
                return []
            sql = ("SELECT question_norm, question_text,"
                   " language, student_class, stage,"
                   " terminal_kind, hits, first_seen, last_seen"
                   " FROM not_found_log ORDER BY hits DESC,"
                   " last_seen DESC")
            if limit is not None:
                rows = conn.execute(
                    sql + " LIMIT ?", (int(limit),)).fetchall()
            else:
                rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def top_failures(limit=20, db_path=None):
    """The top grouped failures for the owner report."""
    return _read_rows(db_path=db_path, limit=limit)


def all_rows(db_path=None):
    """Every logged row (report JSONL export)."""
    return _read_rows(db_path=db_path)


def row_count(db_path=None):
    """Distinct normalised questions logged so far."""
    return len(_read_rows(db_path=db_path))


__all__ = ["log_not_found", "top_failures", "all_rows",
           "row_count"]
