"""Student accounts for Ganitra (Wave 10) — stdlib only.

Suraj's sign-in design has NO phone number and NO email: a student
creates an account with his name, class, board, three "favourite
things" (goal, hobby, favourite) and a password. Later he logs in
with name + password; if he forgets the password, typing ANY ONE of
his three favourite things (matching what he wrote at sign-up) logs
him in and lets him set a new password.

Storage is a small SQLite database via the stdlib ``sqlite3``
module. The path comes from the GANITRA_DB_PATH environment
variable, defaulting to ``ganitra_users.db`` beside this file.

IMPORTANT deployment honesty: Render's free filesystem is
EPHEMERAL — the database file vanishes on redeploy/restart, so
accounts are effectively per-deployment until a hosted database
is added (see README "Notes & honest limits").

Security: passwords and favourite answers are NEVER stored in
plain text. Each secret is hashed with hashlib.pbkdf2_hmac
(SHA-256, per-user random salt, 120k iterations) and verified with
hmac.compare_digest. Favourite answers are normalised before
hashing (lowercase, trim, collapse internal whitespace) so
"Cricket", "cricket" and "  Cricket  " all match.

Known limitation, by design of the no-phone/no-email identity: the
account key is the student's NAME (lowercased, whitespace
collapsed). Two different students with the exact same name cannot
both register — sign-up with an existing name is refused (never
overwritten) with a friendly message asking for a slightly
different name, e.g. "Aarav S.".
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from pathlib import Path

_PBKDF2_ITERATIONS = 120_000
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name_key    TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    class_text  TEXT NOT NULL,
    board_text  TEXT NOT NULL,
    class_num   INTEGER NOT NULL,
    board       TEXT NOT NULL DEFAULT 'other-state-board',
    pw_hash     TEXT NOT NULL,
    goal_hash   TEXT NOT NULL,
    hobby_hash  TEXT NOT NULL,
    fav_hash    TEXT NOT NULL,
    created_at  INTEGER NOT NULL
)
"""


def db_path():
    """Account DB path: GANITRA_DB_PATH env wins, else beside here."""
    env = os.environ.get("GANITRA_DB_PATH", "").strip()
    if env:
        return env
    return str(Path(__file__).with_name("ganitra_users.db"))


# Wave 17b (pen-test fix F1): SERVER-SIDE failed-login tracking.
# The Wave-10 lockout counter lived in the visitor's own session
# cookie, so discarding the cookie reset it — unlimited fresh
# batches of 8 guesses, and a guessed favourite answer means a
# full takeover (it also sets a new password). This table is the
# authoritative counter: one row per submitted name_key (the
# account need not exist — name-guessing is throttled too),
# shared by password login AND favourite recovery, persistent
# across sessions. After LOGIN_ATTEMPT_LIMIT cumulative failures
# the name_key is locked for LOGIN_LOCKOUT_SECONDS.
LOGIN_ATTEMPT_LIMIT = 8
LOGIN_LOCKOUT_SECONDS = 30 * 60

_LOGIN_SCHEMA = """
CREATE TABLE IF NOT EXISTS login_attempts (
    name_key     TEXT PRIMARY KEY,
    fails        INTEGER NOT NULL DEFAULT 0,
    locked_until INTEGER NOT NULL DEFAULT 0
)
"""


# Wave 12: the student's own profile photo (My Account page) lives
# in the same SQLite file — one row per account, replaced on every
# new upload. Created lazily here, the same pattern chats.py uses
# for its table, so older database files gain it automatically.
_PHOTO_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_photos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL UNIQUE,
    data        BLOB NOT NULL,
    updated_at  INTEGER NOT NULL
)
"""


# Wave 14 (speed): hot-lookup indexes, created idempotently on
# every connect so old and new database files alike gain them.
# (users.name_key is already UNIQUE-indexed by the schema; these
# cover the photo lookup and make the intent explicit.)
_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_users_name_key"
    " ON users(name_key)",
    "CREATE INDEX IF NOT EXISTS idx_user_photos_user"
    " ON user_photos(user_id)",
)


def _connect():
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    # Wave 14: WAL mode — readers (menu stats, chat lists) no
    # longer block behind a writer (a chat save), and vice versa.
    # Harmless on :memory:/fresh files; re-asserting is a no-op
    # once set. Never let a pragma failure break the app.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except sqlite3.Error:
        pass
    conn.execute(_SCHEMA)
    conn.execute(_LOGIN_SCHEMA)
    conn.execute(_PHOTO_SCHEMA)
    for statement in _INDEXES:
        conn.execute(statement)
    return conn


def init_db():
    """Wave 14: create the schema + indexes (and WAL) up front,
    called by the app's start-up warm-up so the first real
    request pays none of the setup cost."""
    conn = _connect()
    conn.close()


# ------------------------------------------------------------------ text
def normalise_name_key(name):
    """Account lookup key: lowercase, whitespace-collapsed name."""
    return re.sub(r"\s+", " ", str(name or "")).strip().lower()


def normalise_answer(value):
    """Favourite-answer normalisation, applied BOTH at sign-up and
    at favourite-login so the comparison is forgiving about case
    and spacing (and only about those)."""
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def parse_class(value):
    """Accept "8", "Class 8", "8th", "class-8" -> 8. Only 6..12 are
    valid for Ganitra's first page; anything else returns None."""
    if value is None:
        return None
    match = re.search(r"\d{1,2}", str(value))
    if not match:
        return None
    number = int(match.group())
    return number if 6 <= number <= 12 else None


def board_slug_for(board_text):
    """Map the free-typed board name onto the Board Mode slugs
    (board_data.BOARDS). Suraj's rule: cbse->CBSE, icse->ICSE,
    mp->MP, rajasthan->Rajasthan, up->UP, else Other."""
    text = f" {normalise_answer(board_text)} "
    if "cbse" in text:
        return "cbse"
    if "icse" in text:
        return "icse"
    if " mp" in text or "madhya" in text:
        return "mp-board"
    if "rajasthan" in text or " rbse" in text:
        return "rajasthan-board"
    if " up" in text or "uttar" in text:
        return "up-board"
    return "other-state-board"


# ------------------------------------------------------------------ hash
def _hash_secret(secret):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def _check_secret(secret, stored):
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest, expected)


# ------------------------------------------------------------------ CRUD
def get_user(name):
    """Fetch one account row (sqlite3.Row) by name, or None."""
    key = normalise_name_key(name)
    if not key:
        return None
    conn = _connect()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE name_key = ?", (key,)).fetchone()
    finally:
        conn.close()


def create_user(name, class_text, board_text, class_num,
                password, goal, hobby, favourite):
    """Create an account.

    Returns (user_id, None) on success or (None, "exists") when the
    name is already taken — an existing account is NEVER
    overwritten by a new sign-up.
    """
    key = normalise_name_key(name)
    conn = _connect()
    try:
        if conn.execute("SELECT 1 FROM users WHERE name_key = ?",
                        (key,)).fetchone():
            return None, "exists"
        cur = conn.execute(
            "INSERT INTO users (name_key, name, class_text, board_text,"
            " class_num, board, pw_hash, goal_hash, hobby_hash,"
            " fav_hash, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (key, re.sub(r"\s+", " ", str(name)).strip(),
             str(class_text).strip(), str(board_text).strip(),
             class_num, board_slug_for(board_text),
             _hash_secret(password),
             _hash_secret(normalise_answer(goal)),
             _hash_secret(normalise_answer(hobby)),
             _hash_secret(normalise_answer(favourite)),
             int(time.time())))
        conn.commit()
        return cur.lastrowid, None
    finally:
        conn.close()


def verify_password(user, password):
    return _check_secret(str(password or ""), user["pw_hash"])


def verify_favourite(user, typed):
    """True when the typed text matches ANY ONE of the student's
    three favourite things (normalised both sides)."""
    answer = normalise_answer(typed)
    if len(answer) < 2:
        return False
    return any(_check_secret(answer, user[column])
               for column in ("goal_hash", "hobby_hash", "fav_hash"))


def update_password(user_id, new_password):
    conn = _connect()
    try:
        conn.execute("UPDATE users SET pw_hash = ? WHERE id = ?",
                     (_hash_secret(new_password), user_id))
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------- wave 17b login lockout
# Server-side failed-login tracking (see _LOGIN_SCHEMA). The app
# layer keys everything by the same normalised name_key used for
# account lookup; the helpers take that key as-is.

def is_locked(name_key):
    """True while name_key is inside its lockout window."""
    key = str(name_key or "")
    if not key:
        return False
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT locked_until FROM login_attempts"
            " WHERE name_key = ?", (key,)).fetchone()
        return bool(row and row["locked_until"] > int(time.time()))
    finally:
        conn.close()


def record_failed_login(name_key):
    """Count one more failed password/favourite attempt for
    name_key. Returns True when the name is locked afterwards
    (this failure reached LOGIN_ATTEMPT_LIMIT, or a lock was
    already running — a running lock is NOT extended by further
    attempts, so it always ends LOGIN_LOCKOUT_SECONDS after the
    failure that tripped it).

    Wave 46 (audit F2): when a lock has EXPIRED, its stale fail
    count is reset BEFORE this failure is counted. The old
    behaviour kept the count, so ONE failure after expiry
    re-locked instantly — and since a student's login name is
    public by design, anyone could keep a classmate locked out
    forever at the cost of ~1 request every 30 minutes. Now a
    fresh failure window starts at expiry: re-locking costs the
    full LOGIN_ATTEMPT_LIMIT failures again. (A successful login
    still clears the slate via clear_login_failures.)"""
    key = str(name_key or "")
    if not key:
        return False
    now = int(time.time())
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT fails, locked_until FROM login_attempts"
            " WHERE name_key = ?", (key,)).fetchone()
        fails = row["fails"] if row else 0
        locked_until = row["locked_until"] if row else 0
        if locked_until > now:
            return True
        if locked_until:
            # A lock exists but is in the past: it has expired,
            # so its fail count is stale — start a fresh window.
            fails = 0
            locked_until = 0
        fails += 1
        if fails >= LOGIN_ATTEMPT_LIMIT:
            locked_until = now + LOGIN_LOCKOUT_SECONDS
        conn.execute(
            "INSERT INTO login_attempts (name_key, fails,"
            " locked_until) VALUES (?, ?, ?)"
            " ON CONFLICT(name_key) DO UPDATE SET"
            " fails = excluded.fails,"
            " locked_until = excluded.locked_until",
            (key, fails, locked_until))
        conn.commit()
        return locked_until > now
    finally:
        conn.close()


def clear_login_failures(name_key):
    """Forget all recorded failures for name_key (called on any
    successful login, password or favourite)."""
    key = str(name_key or "")
    if not key:
        return
    conn = _connect()
    try:
        conn.execute("DELETE FROM login_attempts WHERE name_key = ?",
                     (key,))
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------- wave 12 account
# My Account (Wave 12): the student can change EVERYTHING later —
# name, class, board, any of the 3 favourite things, the password
# (above), and add his own photo. Favourites stay write-only
# secrets: update_favourites replaces a hash; no function here ever
# returns a favourite's value.

_FAVOURITE_COLUMNS = {"goal": "goal_hash", "hobby": "hobby_hash",
                      "favourite": "fav_hash"}


def get_user_by_id(user_id):
    """Fetch one account row by primary key, or None."""
    if not user_id:
        return None
    conn = _connect()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?",
                            (user_id,)).fetchone()
    finally:
        conn.close()


def rename_user(user_id, new_name):
    """Change an account's login/display name.

    The name IS the login key, so a rename is refused (returns
    "exists") when ANOTHER account already owns the new name_key —
    the existing account is never touched. Returns None on success.
    """
    key = normalise_name_key(new_name)
    display = re.sub(r"\s+", " ", str(new_name)).strip()
    conn = _connect()
    try:
        clash = conn.execute(
            "SELECT id FROM users WHERE name_key = ? AND id != ?",
            (key, user_id)).fetchone()
        if clash:
            return "exists"
        conn.execute(
            "UPDATE users SET name_key = ?, name = ? WHERE id = ?",
            (key, display, user_id))
        conn.commit()
        return None
    finally:
        conn.close()


def update_profile(user_id, class_text, class_num, board_text):
    """Update class + board (the typed texts stay for display; the
    board slug is re-derived exactly like at sign-up)."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE users SET class_text = ?, class_num = ?,"
            " board_text = ?, board = ? WHERE id = ?",
            (str(class_text).strip(), class_num,
             str(board_text).strip(), board_slug_for(board_text),
             user_id))
        conn.commit()
    finally:
        conn.close()


def update_favourites(user_id, field, value):
    """Replace ONE favourite thing's hash (field is goal, hobby or
    favourite; anything else is ignored). The value is normalised
    and PBKDF2-hashed exactly like at sign-up — never stored raw."""
    column = _FAVOURITE_COLUMNS.get(field)
    if column is None:
        return
    conn = _connect()
    try:
        conn.execute(
            f"UPDATE users SET {column} = ? WHERE id = ?",
            (_hash_secret(normalise_answer(value)), user_id))
        conn.commit()
    finally:
        conn.close()


def set_photo(user_id, data_bytes):
    """Store (or replace) the student's profile photo bytes."""
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO user_photos (user_id, data, updated_at)"
            " VALUES (?, ?, ?)"
            " ON CONFLICT(user_id) DO UPDATE SET data = excluded.data,"
            " updated_at = excluded.updated_at",
            (user_id, sqlite3.Binary(bytes(data_bytes)),
             int(time.time())))
        conn.commit()
    finally:
        conn.close()


def get_photo(user_id):
    """The stored photo bytes for user_id, or None."""
    if not user_id:
        return None
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT data FROM user_photos WHERE user_id = ?",
            (user_id,)).fetchone()
        return bytes(row["data"]) if row else None
    finally:
        conn.close()


def delete_photo(user_id):
    conn = _connect()
    try:
        conn.execute("DELETE FROM user_photos WHERE user_id = ?",
                     (user_id,))
        conn.commit()
    finally:
        conn.close()


def _chat_rows(user_id):
    """All of the user's stored chat threads (parsed message lists).

    The chats table belongs to chats.py and is created lazily by
    it; before the first chat exists there may be no table at all,
    so a missing table simply means zero (never an error)."""
    import json as _json

    conn = _connect()
    try:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table'"
            " AND name = 'chats'").fetchone()
        if not exists:
            return []
        rows = conn.execute(
            "SELECT messages_json FROM chats WHERE user_id = ?",
            (user_id,)).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()
    threads = []
    for row in rows:
        try:
            data = _json.loads(row["messages_json"] or "[]")
        except (ValueError, TypeError):
            data = []
        if isinstance(data, list):
            threads.append(data)
    return threads


def questions_count(user_id):
    """How many questions the student has asked across ALL his
    saved chats (stored user turns). Feeds the menu stats line."""
    return sum(1 for thread in _chat_rows(user_id) for msg in thread
               if isinstance(msg, dict) and msg.get("role") == "user")


def chats_count(user_id):
    """How many chats the student has (menu stats line)."""
    return len(_chat_rows(user_id))
