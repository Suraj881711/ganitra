"""Per-account chat threads for Ganitra (Wave 11) — stdlib only.

Suraj's approved multi-chat design (from his own Brave-browser
screenshot): a signed-in student can keep MANY chats, like browser
tabs. Tapping the plain "+" at the far right of the chat top bar
opens the all-chats view (count chip, "Search your chats", a
2-column grid of preview cards, a big blue "+" for a new chat,
and a ⋮ menu with "Close all chats"); each card opens its chat.

Storage lives in the SAME SQLite file as the Wave-10 accounts
(accounts.db_path()): one extra table,
``chats(id, user_id, title, messages_json, created_at,
updated_at)``, created lazily here so accounts.py needs no
changes. Every query is scoped by user_id — a chat is only ever
visible to the account that owns it.

A chat's thread is stored as a JSON list of portable message
records (see index.html): user turns keep the question text,
bot turns keep the SOLVE RESPONSE object (the same payload
/api/solve returns), so reopening a chat re-renders exactly the
bubbles the student saw. Failed (unsolvable) turns are stored too
and re-render as the friendly error card (without its Retry
button — the question is already in the box workflow).

Titles: a chat is "New chat" until its first question lands; the
title then becomes that first question (trimmed). Mirrors the
client-side derivation so list views agree everywhere.
"""

import json
import os
import sqlite3
import time

import accounts

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT NOT NULL DEFAULT '',
    messages_json TEXT NOT NULL DEFAULT '[]',
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL
)
"""

# A thread holds at most this many stored turns; older ones are
# dropped from the front on save (the live page keeps its own
# scrollback — this cap only bounds the saved copy).
MAX_MESSAGES = 200
# Bounds for one saved thread, so a runaway client cannot fill
# the DB: messages JSON is capped at ~2 MB per chat.
MAX_MESSAGES_BYTES = 2_000_000
TITLE_LIMIT = 80


# Wave 14 (speed): every chat query is scoped by user_id (list,
# get, save, delete, menu stats) — index it, plus the
# (user_id, updated_at) pair behind the most-recent-first list.
# Messages live INSIDE the chats row (messages_json), so these
# two indexes are also the message lookups' hot path.
_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_chats_user"
    " ON chats(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_chats_user_updated"
    " ON chats(user_id, updated_at)",
)


def _connect():
    conn = sqlite3.connect(accounts.db_path())
    conn.row_factory = sqlite3.Row
    # Wave 14: WAL, same reasoning as accounts._connect.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error:
        pass
    conn.execute(_SCHEMA)
    for statement in _INDEXES:
        conn.execute(statement)
    return conn


def init_db():
    """Wave 14: create the chats table + indexes up front (the
    app's start-up warm-up calls this)."""
    conn = _connect()
    conn.close()


def _now():
    return int(time.time())


def _title_for(messages):
    """Derive a chat title from its thread: the first user
    question, whitespace-collapsed and trimmed to TITLE_LIMIT."""
    for msg in messages or []:
        if isinstance(msg, dict) and msg.get("role") == "user":
            text = " ".join(str(msg.get("text", "")).split())
            if text:
                return text[:TITLE_LIMIT]
    return ""


def _parse_messages(raw):
    try:
        data = json.loads(raw or "[]")
    except (ValueError, TypeError):
        return []
    if not isinstance(data, list):
        return []
    return [m for m in data if isinstance(m, dict)]


def _row_to_chat(row, with_messages=False):
    messages = _parse_messages(row["messages_json"])
    chat = {
        "id": row["id"],
        "title": row["title"] or _title_for(messages),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": len(messages),
    }
    if with_messages:
        chat["messages"] = messages
    else:
        # Card preview (Wave 11 all-chats view): first question +
        # first bot answer text, extracted here so the client
        # never has to download whole threads just to draw cards.
        first_q = ""
        first_a = ""
        for msg in messages:
            role = msg.get("role")
            if role == "user" and not first_q:
                first_q = str(msg.get("text", ""))
            elif role == "bot":
                data = msg.get("data") or {}
                result = data.get("result") or {}
                first_a = str(result.get("answer", ""))
                if first_a:
                    break
        chat["first_question"] = first_q
        chat["first_answer"] = first_a
    return chat


def list_chats(user_id):
    """All chats owned by user_id, most recently updated first."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM chats WHERE user_id = ?"
            " ORDER BY updated_at DESC, id DESC",
            (user_id,)).fetchall()
        return [_row_to_chat(row) for row in rows]
    finally:
        conn.close()


def create_chat(user_id):
    now = _now()
    conn = _connect()
    try:
        cur = conn.execute(
            "INSERT INTO chats (user_id, title, messages_json,"
            " created_at, updated_at) VALUES (?, '', '[]', ?, ?)",
            (user_id, now, now))
        conn.commit()
        chat_id = cur.lastrowid
    finally:
        conn.close()
    return get_chat(user_id, chat_id)


def get_chat(user_id, chat_id):
    """One chat (with messages) — only when it belongs to
    user_id; otherwise None (ownership is never negotiable)."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id)).fetchone()
        return _row_to_chat(row, with_messages=True) if row else None
    finally:
        conn.close()


def save_chat(user_id, chat_id, messages):
    """Replace a chat's thread (whole-thread save, matching the
    client's debounced save-on-change). Returns the chat dict,
    or None when the chat does not belong to user_id. The title
    is re-derived from the first question on every save."""
    if not isinstance(messages, list):
        return None
    messages = [m for m in messages if isinstance(m, dict)]
    messages = messages[-MAX_MESSAGES:]
    payload = json.dumps(messages, ensure_ascii=False)
    if len(payload.encode("utf-8")) > MAX_MESSAGES_BYTES:
        return None
    title = _title_for(messages)
    conn = _connect()
    try:
        cur = conn.execute(
            "UPDATE chats SET messages_json = ?, title = ?,"
            " updated_at = ? WHERE id = ? AND user_id = ?",
            (payload, title, _now(), chat_id, user_id))
        conn.commit()
        if cur.rowcount == 0:
            return None
    finally:
        conn.close()
    return get_chat(user_id, chat_id)


def delete_chat(user_id, chat_id):
    """Delete one owned chat; True when a row was removed."""
    conn = _connect()
    try:
        cur = conn.execute(
            "DELETE FROM chats WHERE id = ? AND user_id = ?",
            (chat_id, user_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_all_chats(user_id):
    """Close ALL of the student's chats (the ⋮ menu action)."""
    conn = _connect()
    try:
        cur = conn.execute(
            "DELETE FROM chats WHERE user_id = ?", (user_id,))
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()
