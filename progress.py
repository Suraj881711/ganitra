"""Wave 89: My Progress — aggregation over the data the app
already stores for the signed-in student, nothing invented.

Data sources (all pre-existing; this module adds NO storage):

- the chats table (chats.py): every saved thread holds the
  student's turns ({"role": "user", "text"}) and Ganitra's
  replies ({"role": "bot", "data": <the /api/solve result>}),
  plus created_at / updated_at epoch seconds per thread.
  From it: questions asked (user turns — the same count
  accounts.questions_count feeds the menu), questions
  answered (bot results that answered the student's OWN
  question, per is_answered below), chat count, and a
  per-week activity series.
- the users table (accounts.py): the account's created_at
  ("learning since").

Deliberately NOT here (no stored data source exists — see
ganitra-wave89-notes.md): a full test-score history (only
the LAST test report exists, in the session — the /progress
route adds it from there, like the Wave 6 Parent Report),
per-question timestamps (stored messages carry none, so
the weekly series groups a chat's questions by the week of
that chat's last activity), and study minutes (the Dhyaan
record is browser-localStorage, per day and per browser).

Every query is scoped by user_id: a student only ever sees
their own record. A missing chats table (an account that
has never chatted) simply means zeroes, never an error —
the same defensive posture as accounts._chat_rows.
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta

import accounts

# Bot results whose fallback_kind means "the student's own
# question WAS answered": the verified bank's exact match,
# an AI brain's answer to the question itself (Wave 37/41),
# and a salvage solve of the maths part (Wave 18+). A plain
# solver result carries fallback_kind None and is answered
# by definition; Wave 75 concept answers are answered too,
# but they keep fallback_kind "concept", so they are told
# apart by source == "topics" (the generic concepts.py card
# without that source is a guide, not an answer). Everything
# else — "not_found", "similar", "guide", greetings, vague
# and science/guard plain replies — is NOT an answer.
_ANSWERED_KINDS = ("bank", "gemini", "groq", "salvage")
_WEEKS_SHOWN = 8


def is_answered(data):
    """True when one stored bot result answered the student's
    own question (see the taxonomy note above)."""
    if not isinstance(data, dict):
        return False
    if data.get("plain_reply") or data.get("plain"):
        return False
    kind = data.get("fallback_kind")
    if kind is None:
        return True
    if kind in _ANSWERED_KINDS:
        return True
    if data.get("source") in ("topics", "mcq"):
        return True
    return False


def _thread_rows(user_id):
    """(messages, created_at, updated_at) for the student's
    own threads only. [] when the chats table does not exist
    yet or cannot be read."""
    conn = sqlite3.connect(accounts.db_path())
    conn.row_factory = sqlite3.Row
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table'"
            " AND name = 'chats'").fetchone()
        if not exists:
            return []
        rows = conn.execute(
            "SELECT messages_json, created_at, updated_at"
            " FROM chats WHERE user_id = ?", (user_id,)).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    threads = []
    for row in rows:
        try:
            data = json.loads(row["messages_json"] or "[]")
        except (ValueError, TypeError):
            data = []
        if not isinstance(data, list):
            data = []
        threads.append((data, row["created_at"] or 0,
                        row["updated_at"] or 0))
    return threads


def _week_start(ts):
    """The Monday (local time) of the week holding epoch `ts`,
    as a date."""
    day = datetime.fromtimestamp(ts).date()
    return day - timedelta(days=day.weekday())


def weekly_series(threads, now=None):
    """Questions asked per week for the last _WEEKS_SHOWN
    weeks (oldest first, current week last). A thread's user
    turns are grouped into the week of the thread's
    updated_at — stored messages carry no timestamps of
    their own (see module docstring). Each entry: {"label",
    "count", "pct", "current"} where pct is the bar height
    as a percentage of the busiest week."""
    now = time.time() if now is None else now
    current_start = _week_start(now)
    starts = [current_start - timedelta(weeks=i)
              for i in range(_WEEKS_SHOWN - 1, -1, -1)]
    counts = {start: 0 for start in starts}
    for messages, _created, updated in threads:
        start = _week_start(updated)
        if start in counts:
            counts[start] += sum(
                1 for m in messages
                if isinstance(m, dict) and m.get("role") == "user")
    busiest = max(counts.values()) if counts else 0
    series = []
    for start in starts:
        count = counts[start]
        series.append({
            "label": start.strftime("%d %b"),
            "count": count,
            "pct": round(100 * count / busiest) if busiest else 0,
            "current": start == current_start,
        })
    return series


def format_date(ts):
    """'16 Nov 2026' for an epoch-seconds timestamp (local
    time), or None for a missing/zero value."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts).strftime("%d %b %Y")


def collect_progress(user_id, now=None):
    """The full account-side progress record for ONE student:
    totals, answered share and the weekly series. Asked is
    accounts.questions_count itself, so this page can never
    disagree with the menu's own stats line."""
    threads = _thread_rows(user_id)
    asked = accounts.questions_count(user_id)
    answered = 0
    for messages, _created, _updated in threads:
        answered += sum(
            1 for m in messages
            if isinstance(m, dict) and m.get("role") == "bot"
            and is_answered(m.get("data")))
    return {
        "asked": asked,
        "answered": answered,
        "chats": accounts.chats_count(user_id),
        "answered_pct": round(100 * answered / asked) if asked else 0,
        "weeks": weekly_series(threads, now=now),
    }
