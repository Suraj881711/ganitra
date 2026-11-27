"""Group Study for Ganitra (Wave 213) — stdlib only.

Suraj's design (21–22 Nov 2026): groups live inside the menu,
nowhere else. A group is CHAT + STUDY together: members chat
freely, and Ganitra sits quietly in the group — it speaks only
when (a) a member posts a maths question (detected by meaning,
via the real solve pipeline — no tag, no button needed),
(b) a peer's answer to a maths question is wrong (a polite
correction), or (c) a member addresses Ganitra by name — on
ANY topic: the name-called question is answered for real,
via the verified AI legs when the native pipeline has no
answer (Wave 228, completing Suraj's 23 Nov 2026 spec; the
Wave 213 maths-only line survives only as the outcome when
the legs also have nothing). A follow-up
to Ganitra's own last answer — "samjhao", "phir se karo",
"details mai chahiye", or
any reply aimed at its answer post — counts as addressed to
Ganitra (Wave 225, Suraj's 23 Nov 2026 spec nuance; the
plain-message path completed in Wave 228). Ordinary
member-to-member chat is never policed.

IDENTITY (Suraj's security condition, 22 Nov): group membership
is keyed to a MOBILE NUMBER, WhatsApp-style. The base app login
does NOT change (name + class + board + 3 favourites +
password; the app stays fully usable without a phone). But
group features require a mobile number on the account:

- a user sets a 10-digit Indian mobile number (stored in this
  module's own table in the same SQLite file — accounts.py is
  untouched, the chats.py lazy-table pattern);
- the admin adds members BY MOBILE NUMBER — the number
  identifies the account;
- EVERY member must have a number, no exceptions: a person
  whose account has no number can never be resolved by a
  number, so they can never be added — at creation or later.
  An unresolvable number fails with a clear message (the
  person may not have added their number yet) and creation
  proceeds with the number-holding members only, still
  respecting the minimum-2 rule;
- NO SMS OTP at launch (Suraj's standing no-money rule): the
  number is a DECLARED identity, not an OTP-verified one.
  OTP verification is a documented future upgrade.

LIMITS: 2–30 members per group; only the group admin adds or
removes members; the creator is the admin. Any member can
report a message; the owner account (id 1) sees all groups,
members, recent activity and reports, and can close a group
or remove a member.

STORAGE LEAN (PythonAnywhere free disk): text only, post
bodies capped, only the latest MAX_POSTS_KEPT posts are kept
per group (older ones pruned on write).

SOLVE + LEARNING: a detected maths question is answered by
api._solve_friendly — the real pipeline (native solver, then
the Gemini/Groq/OpenRouter legs with their verification
discipline, answers in Ganitra's own voice). AI-leg answers
and total misses flow into the app's existing learning
pipeline by themselves (livebank pending rows / Wave-90
not-found log, both inside that pipeline) — this module adds
no second format.
"""

import re
import sqlite3
import time
from fractions import Fraction

import accounts

OWNER_ID = 1
MIN_MEMBERS = 2
MAX_MEMBERS = 30
MAX_POSTS_KEPT = 200
MAX_POST_CHARS = 1000
MAX_ANSWER_CHARS = 1600
MAX_NAME_CHARS = 60

_SCHEMA = """
CREATE TABLE IF NOT EXISTS user_phones (
    user_id    INTEGER PRIMARY KEY,
    phone      TEXT NOT NULL UNIQUE,
    updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS study_groups (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    admin_id   INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    closed_at  INTEGER
);
CREATE TABLE IF NOT EXISTS group_members (
    group_id  INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    added_by  INTEGER NOT NULL,
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (group_id, user_id)
);
CREATE TABLE IF NOT EXISTS group_posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id   INTEGER NOT NULL,
    author_id  INTEGER,
    kind       TEXT NOT NULL,
    body       TEXT NOT NULL,
    reply_to   INTEGER,
    created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_group_posts_group
    ON group_posts (group_id, id);
CREATE TABLE IF NOT EXISTS group_reports (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id    INTEGER NOT NULL,
    post_id     INTEGER NOT NULL,
    reporter_id INTEGER NOT NULL,
    reason      TEXT NOT NULL DEFAULT '',
    created_at  INTEGER NOT NULL
);
"""

# Post kinds: chat (ordinary talk), question (a maths question
# Ganitra answered), peer_answer (an answer to a question post),
# ganitra (Ganitra's auto-answer), ganitra_note (a correction or
# the maths-only line — Ganitra speaking without a full answer).


def _connect():
    conn = sqlite3.connect(accounts.db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


# ---------------------------------------------------------------------------
# Mobile numbers
# ---------------------------------------------------------------------------

def normalise_phone(raw):
    """A 10-digit Indian mobile from typed input, or None.

    Accepts spaces, a leading +91 / 91 / 0. Indian mobiles start
    6–9. Anything else is not a usable group identity."""
    if raw is None:
        return None
    digits = re.sub(r"\D", "", str(raw))
    if len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if re.fullmatch(r"[6-9]\d{9}", digits):
        return digits
    return None


def get_phone(user_id):
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT phone FROM user_phones WHERE user_id = ?",
            (user_id,)).fetchone()
        return row["phone"] if row else None
    finally:
        conn.close()


def set_phone(user_id, raw):
    """Set/replace the account's mobile number.

    Returns (phone, None) on success, (None, error) otherwise.
    One number belongs to one account — a number already held
    by another account is refused."""
    phone = normalise_phone(raw)
    if phone is None:
        return None, ("Ye sahi mobile number nahi hai — "
                      "10 digit ka Indian mobile number likho.")
    conn = _connect()
    try:
        holder = conn.execute(
            "SELECT user_id FROM user_phones WHERE phone = ?",
            (phone,)).fetchone()
        if holder and holder["user_id"] != user_id:
            return None, ("Ye number kisi aur Ganitra account par "
                          "already hai.")
        conn.execute(
            "INSERT INTO user_phones (user_id, phone, updated_at) "
            "VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
            "phone = excluded.phone, updated_at = excluded.updated_at",
            (user_id, phone, int(time.time())))
        conn.commit()
        return phone, None
    finally:
        conn.close()


def user_by_phone(phone):
    """The account row holding this (normalised) number, or
    None. A number-less account can never be found here — that
    is exactly Suraj's every-member-has-a-number rule."""
    conn = _connect()
    try:
        return conn.execute(
            "SELECT u.* FROM user_phones p JOIN users u "
            "ON u.id = p.user_id WHERE p.phone = ?",
            (phone,)).fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Groups and members
# ---------------------------------------------------------------------------

def _group_row(conn, group_id):
    return conn.execute(
        "SELECT * FROM study_groups WHERE id = ?",
        (group_id,)).fetchone()


def _member_ids(conn, group_id):
    return [r["user_id"] for r in conn.execute(
        "SELECT user_id FROM group_members WHERE group_id = ? "
        "ORDER BY joined_at, user_id", (group_id,))]


def _resolve_numbers(phone_texts):
    """Resolve typed numbers to accounts.

    Returns (users, failures): users are account rows in input
    order (deduped); failures is a list of (typed, message) for
    every number that could not be added — not a valid number,
    or no account holds it (unregistered, OR the student has
    not added a mobile number to their account yet — from
    outside those two look the same, so the message says both
    plainly)."""
    users, failures, seen = [], [], set()
    for raw in phone_texts:
        phone = normalise_phone(raw)
        if phone is None:
            failures.append((raw, "ye sahi 10-digit mobile number "
                                  "nahi hai"))
            continue
        if phone in seen:
            continue
        seen.add(phone)
        row = user_by_phone(phone)
        if row is None:
            failures.append(
                (raw, "is number par koi Ganitra account nahi mila "
                      "— ya to ye number register nahi hai, ya us "
                      "student ne abhi apne account me mobile "
                      "number add hi nahi kiya hai. Pehle use apna "
                      "number add karne ko kaho."))
            continue
        users.append(row)
    return users, failures


def create_group(creator_id, name, member_phone_texts):
    """Create a group. Returns (group, failures, error).

    The creator is admin and counts as a member. EVERY member
    must have a mobile number: intended members are named by
    number, so a number-less person simply cannot be resolved
    and lands in `failures` with a clear message; the group is
    created with the resolvable members only, and only when
    the total still respects the 2–30 rule."""
    name = (name or "").strip()[:MAX_NAME_CHARS]
    if not name:
        return None, [], "Group ka naam likho."
    if get_phone(creator_id) is None:
        return None, [], ("Group banane ke liye pehle apna mobile "
                          "number add karo (upar wale box me).")
    users, failures = _resolve_numbers(member_phone_texts)
    others = [u for u in users if u["id"] != creator_id]
    total = 1 + len(others)
    if total < MIN_MEMBERS:
        return None, failures, (
            "Group ke liye kam se kam 2 log chahiye — ek aur "
            "member ka sahi mobile number add karo.")
    if total > MAX_MEMBERS:
        return None, failures, (
            f"Ek group me zyada se zyada {MAX_MEMBERS} log ho "
            "sakte hain.")
    conn = _connect()
    try:
        now = int(time.time())
        cur = conn.execute(
            "INSERT INTO study_groups (name, admin_id, created_at) "
            "VALUES (?, ?, ?)", (name, creator_id, now))
        gid = cur.lastrowid
        conn.execute(
            "INSERT INTO group_members (group_id, user_id, "
            "added_by, joined_at) VALUES (?, ?, ?, ?)",
            (gid, creator_id, creator_id, now))
        for u in others:
            conn.execute(
                "INSERT INTO group_members (group_id, user_id, "
                "added_by, joined_at) VALUES (?, ?, ?, ?)",
                (gid, u["id"], creator_id, now))
        conn.commit()
        group = _group_row(conn, gid)
        return dict(group), failures, None
    finally:
        conn.close()


def add_member(group_id, actor_id, phone_raw):
    """Admin-only add by mobile number. (ok, error)."""
    conn = _connect()
    try:
        group = _group_row(conn, group_id)
        if group is None:
            return False, "Group nahi mila."
        if group["closed_at"]:
            return False, "Ye group band ho chuka hai."
        if group["admin_id"] != actor_id:
            return False, "Sirf group admin hi member add kar sakta hai."
        users, failures = _resolve_numbers([phone_raw])
        if failures:
            return False, f"{phone_raw}: {failures[0][1]}"
        user = users[0]
        ids = _member_ids(conn, group_id)
        if user["id"] in ids:
            return False, "Ye member pehle se group me hai."
        if len(ids) >= MAX_MEMBERS:
            return False, (f"Group full hai — zyada se zyada "
                           f"{MAX_MEMBERS} members.")
        conn.execute(
            "INSERT INTO group_members (group_id, user_id, "
            "added_by, joined_at) VALUES (?, ?, ?, ?)",
            (group_id, user["id"], actor_id, int(time.time())))
        conn.commit()
        return True, None
    finally:
        conn.close()


def remove_member(group_id, actor_id, user_id, owner=False):
    """Remove a member. Admin-only (or the owner from the
    dashboard). The admin themselves cannot be removed — a
    group must keep its admin; close the group instead."""
    conn = _connect()
    try:
        group = _group_row(conn, group_id)
        if group is None:
            return False, "Group nahi mila."
        if not owner and group["admin_id"] != actor_id:
            return False, ("Sirf group admin hi member hata "
                           "sakta hai.")
        if user_id == group["admin_id"]:
            return False, ("Group admin ko nahi hataya ja sakta — "
                           "group band karna hai to close karo.")
        cur = conn.execute(
            "DELETE FROM group_members WHERE group_id = ? AND "
            "user_id = ?", (group_id, user_id))
        conn.commit()
        if cur.rowcount == 0:
            return False, "Ye member group me hai hi nahi."
        return True, None
    finally:
        conn.close()


def leave_group(group_id, user_id):
    """Wave 218: a member leaves on their own (Suraj's spec,
    22 Nov 2026 — har member ko leave ka option). If the
    admin leaves, admin passes to the earliest-joined
    remaining member; if nobody remains, the group closes."""
    conn = _connect()
    try:
        group = _group_row(conn, group_id)
        if group is None:
            return False, "Group nahi mila."
        cur = conn.execute(
            "DELETE FROM group_members WHERE group_id = ? AND "
            "user_id = ?", (group_id, user_id))
        if cur.rowcount == 0:
            conn.commit()
            return False, "Tum is group me ho hi nahi."
        if group["admin_id"] == user_id:
            nxt = conn.execute(
                "SELECT user_id FROM group_members WHERE "
                "group_id = ? ORDER BY joined_at, user_id "
                "LIMIT 1", (group_id,)).fetchone()
            if nxt is None:
                conn.execute(
                    "UPDATE study_groups SET closed_at = ? "
                    "WHERE id = ?", (int(time.time()), group_id))
            else:
                conn.execute(
                    "UPDATE study_groups SET admin_id = ? "
                    "WHERE id = ?", (nxt[0], group_id))
        conn.commit()
        return True, None
    finally:
        conn.close()


def close_group(group_id, actor_id, owner=False):
    conn = _connect()
    try:
        group = _group_row(conn, group_id)
        if group is None:
            return False, "Group nahi mila."
        if not owner and group["admin_id"] != actor_id:
            return False, "Sirf group admin hi group band kar sakta hai."
        if group["closed_at"]:
            return False, "Ye group pehle se band hai."
        conn.execute(
            "UPDATE study_groups SET closed_at = ? WHERE id = ?",
            (int(time.time()), group_id))
        conn.commit()
        return True, None
    finally:
        conn.close()


def is_member(group_id, user_id):
    conn = _connect()
    try:
        return conn.execute(
            "SELECT 1 FROM group_members WHERE group_id = ? AND "
            "user_id = ?", (group_id, user_id)).fetchone() is not None
    finally:
        conn.close()


def get_group(group_id):
    conn = _connect()
    try:
        row = _group_row(conn, group_id)
        return dict(row) if row else None
    finally:
        conn.close()


def list_members(group_id):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT u.id, u.name, u.class_text, p.phone "
            "FROM group_members m JOIN users u ON u.id = m.user_id "
            "LEFT JOIN user_phones p ON p.user_id = u.id "
            "WHERE m.group_id = ? ORDER BY m.joined_at, u.id",
            (group_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_groups_for(user_id):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT g.*, (SELECT COUNT(*) FROM group_members m "
            "WHERE m.group_id = g.id) AS member_count "
            "FROM study_groups g JOIN group_members mine "
            "ON mine.group_id = g.id AND mine.user_id = ? "
            "ORDER BY g.created_at DESC", (user_id,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Posts: chat, questions, peer answers, Ganitra's voice
# ---------------------------------------------------------------------------

def list_posts(group_id, limit=MAX_POSTS_KEPT):
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT p.*, u.name AS author_name FROM group_posts p "
            "LEFT JOIN users u ON u.id = p.author_id "
            "WHERE p.group_id = ? ORDER BY p.id DESC LIMIT ?",
            (group_id, limit)).fetchall()
        return [dict(r) for r in reversed(rows)]
    finally:
        conn.close()


def _insert_post(conn, group_id, author_id, kind, body, reply_to=None):
    body = (body or "")[:MAX_ANSWER_CHARS]
    cur = conn.execute(
        "INSERT INTO group_posts (group_id, author_id, kind, "
        "body, reply_to, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (group_id, author_id, kind, body, reply_to, int(time.time())))
    # Lean storage: keep only the latest MAX_POSTS_KEPT posts.
    conn.execute(
        "DELETE FROM group_posts WHERE group_id = ? AND id NOT IN "
        "(SELECT id FROM group_posts WHERE group_id = ? "
        "ORDER BY id DESC LIMIT ?)",
        (group_id, group_id, MAX_POSTS_KEPT))
    return cur.lastrowid


def _strip_markup(text):
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


def _answer_body(result, max_steps=6):
    """Ganitra's group answer as plain text: short steps, then
    the answer exactly once (the standing format lock)."""
    lines = []
    for step in (result.get("steps") or [])[:max_steps]:
        step = _strip_markup(step)
        if step:
            lines.append(step[:240])
    answer = _strip_markup(result.get("answer"))
    if answer:
        lines.append(f"Answer: {answer}")
    return "\n".join(lines)[:MAX_ANSWER_CHARS]


_AI_KINDS = frozenset({"gemini", "groq", "openrouter"})


def _classify(result):
    """What the solve pipeline's outcome means in a group:
    'answer' (a real answer, native or AI-leg), 'wrong_question'
    (a maths attempt with a defect — the plain call-out),
    'plain' (a one-line standing reply: nonmaths / greeting /
    science / not-found), or 'none'."""
    if not isinstance(result, dict):
        return "none"
    kind = result.get("fallback_kind")
    op = result.get("op")
    if kind == "wrong_question" or op == "wrong_question":
        return "wrong_question"
    if result.get("plain") or kind in ("nonmaths", "greeting",
                                       "not_found", "science") \
            or op in ("nonmaths", "science"):
        return "plain"
    answer = result.get("answer")
    if isinstance(answer, str) and answer.strip():
        return "answer"
    return "none"


def _solve(text):
    from api import _solve_friendly
    return _solve_friendly(text)


_NAME_RE = re.compile(r"\bganitra\b", re.I)


def _strip_name(text):
    """The question with Ganitra's name taken out — what the
    student is actually asking, once the call is removed."""
    q = _NAME_RE.sub(" ", str(text or ""))
    return re.sub(r"\s+", " ", q).strip(" ,:;—-").strip()


def _named_answer(text):
    """Wave 228: the name-call route to the AI legs.

    Suraj's 23 Nov 2026 behaviour spec: a member who calls
    Ganitra by name gets an answer on ANY topic. The native
    pipeline cannot promise that — its maths-only guard
    refuses a general question before the legs are ever
    consulted ("Ganitra, what is the capital of India?"),
    and a total miss ends at the not-found line even when a
    leg could have answered (the Deploy-68 live partial:
    the canned line for "Ganitra, Bharat ki rajdhani kya
    hai?"). So a name-called message with no native answer
    is put to fallback's verified AI chain directly (the
    Wave 226 gate: a prose question is served by the first
    sane leg; a valued one needs a deterministic pass or a
    cross-leg consensus — never one leg's unchecked word).
    Returns the AI result dict, or None when the legs also
    have nothing — the caller then keeps the standing
    one-line outcome, never a fabricated answer."""
    q = _strip_name(text)
    if not q:
        return None
    try:
        from fallback import _looks_hindi, _verified_ai_answer
        res = _verified_ai_answer(q, _looks_hindi(q), None)
    except Exception:
        return None
    if isinstance(res, dict) and _classify(res) == "answer":
        return res
    return None


def _named_body(result):
    """The named answer's post body: the full steps+answer
    format when the legs gave real working, the bare answer
    when they gave prose (whose single step merely restates
    the answer — the steps+answer format would print it
    twice)."""
    ans = _strip_markup(result.get("answer"))
    steps = [_strip_markup(s) for s in (result.get("steps")
                                        or [])]
    if not any(s and s != ans for s in steps):
        return ans[:MAX_ANSWER_CHARS]
    return _answer_body(result)


_NUMBER_RE = re.compile(r"-?\d+\s*/\s*\d+|-?\d+\.\d+|-?\d+")


def _values(text):
    """Numeric values in a text, as Fractions where possible."""
    out = []
    for tok in _NUMBER_RE.findall(str(text or "")):
        tok = tok.replace(" ", "")
        try:
            out.append(Fraction(tok))
        except (ValueError, ZeroDivisionError):
            continue
    return out


def _reference_answer(group_id, question_post):
    """Ganitra's known answer for a question post: its stored
    auto-answer when there is one, else a fresh solve. Returns
    the answer TEXT (short form) or None when Ganitra itself
    has no answer to judge against."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT body FROM group_posts WHERE group_id = ? AND "
            "reply_to = ? AND kind = 'ganitra' ORDER BY id LIMIT 1",
            (group_id, question_post["id"])).fetchone()
    finally:
        conn.close()
    if row:
        m = re.search(r"^Answer:\s*(.+)$", row["body"], re.M)
        if m:
            return m.group(1).strip()
    result = _solve(question_post["body"])
    if _classify(result) == "answer":
        return _strip_markup(result.get("answer"))
    return None


def _correction_body(question_text, reference_answer):
    try:
        from fallback import _looks_hindi
        hindi = _looks_hindi(question_text)
    except Exception:
        hindi = False
    if hindi:
        return ("Ek chhota sa correction — is sawal ka sahi jawab "
                f"{reference_answer} hai. Koi baat nahi, try karna "
                "hi seekhna hai, lage raho!")
    return ("A small correction — the correct answer to this "
            f"question is {reference_answer}. Good try, keep "
            "going!")


def post_message(group_id, author_id, text, reply_to=None):
    """Post one member message and let Ganitra react.

    Returns (post, ganitra_posts, error): the member's stored
    post, the list of Ganitra posts it triggered (usually
    empty — Ganitra stays silent in ordinary chat), and an
    error string when the post was refused."""
    text = (text or "").strip()
    if not text:
        return None, [], "Kuch likho pehle."
    text = text[:MAX_POST_CHARS]
    conn = _connect()
    try:
        group = _group_row(conn, group_id)
        if group is None:
            return None, [], "Group nahi mila."
        if group["closed_at"]:
            return None, [], "Ye group band ho chuka hai."
        if not conn.execute(
                "SELECT 1 FROM group_members WHERE group_id = ? "
                "AND user_id = ?", (group_id, author_id)).fetchone():
            return None, [], "Tum is group ke member nahi ho."
        target = None
        if reply_to:
            target = conn.execute(
                "SELECT * FROM group_posts WHERE id = ? AND "
                "group_id = ?", (reply_to, group_id)).fetchone()
            if target is not None:
                target = dict(target)
        kind = "peer_answer" if (target and target["kind"]
                                 == "question") else "chat"
        post_id = _insert_post(conn, group_id, author_id, kind,
                               text, reply_to if target else None)
        conn.commit()
        post = dict(conn.execute(
            "SELECT * FROM group_posts WHERE id = ?",
            (post_id,)).fetchone())
    finally:
        conn.close()

    ganitra_posts = []
    if kind == "peer_answer":
        note = _check_peer_answer(group_id, target, text)
        if note:
            ganitra_posts.append(note)
        return post, ganitra_posts, None

    # Wave 225 (Suraj's 23 Nov 2026 spec nuance): a follow-up
    # to Ganitra's OWN last answer counts as addressed to
    # Ganitra — "samjhao" / "galat hai, phir se karo" right
    # after its answer, or any reply aimed at its answer post,
    # must not earn silence. Redo/explain re-solve the original
    # question here; any other follow-up falls through to the
    # normal pipeline with addressed=True.
    follow = _own_answer_followup(group_id, post, target, text)
    if follow is not None and follow[0] in (
            "redo", "explain", "detail", "steps"):
        note = _answer_followup(group_id, post, follow[1],
                                follow[0], anchor_post=follow[2])
        if note:
            ganitra_posts.append(note)
            return post, ganitra_posts, None

    # A fresh message: Ganitra detects maths questions by
    # meaning through the real pipeline. Ordinary chat earns
    # silence — the pipeline's plain / not-found outcomes for
    # unaddressed chat are simply not posted.
    result = _solve(text)
    outcome = _classify(result)
    addressed = bool(re.search(r"\bganitra\b", text, re.I)) \
        or follow is not None
    # Wave 228: a member who calls Ganitra by name gets an
    # answer on any topic (23 Nov spec) — when the native
    # pipeline has none (the maths-only guard, or a total
    # miss), the question goes to the verified AI legs
    # before any guard line is posted. Greetings and the
    # science guidance keep their designed one-liners; a
    # maths question keeps its native answer exactly as
    # now. When the legs also have nothing, the standing
    # plain outcome below stands — never a fake answer.
    named = None
    if _NAME_RE.search(text) and outcome in ("plain", "none") \
            and not (isinstance(result, dict) and
                     result.get("fallback_kind") in
                     ("greeting", "science")):
        named = _named_answer(text)
    conn = _connect()
    try:
        if named is not None:
            pid = _insert_post(conn, group_id, None, "ganitra",
                               _named_body(named),
                               reply_to=post["id"])
            ganitra_posts.append(dict(conn.execute(
                "SELECT * FROM group_posts WHERE id = ?",
                (pid,)).fetchone()))
        elif outcome == "answer":
            conn.execute(
                "UPDATE group_posts SET kind = 'question' "
                "WHERE id = ?", (post["id"],))
            pid = _insert_post(conn, group_id, None, "ganitra",
                               _answer_body(result),
                               reply_to=post["id"])
            ganitra_posts.append(dict(conn.execute(
                "SELECT * FROM group_posts WHERE id = ?",
                (pid,)).fetchone()))
        elif outcome == "wrong_question":
            pid = _insert_post(
                conn, group_id, None, "ganitra_note",
                _strip_markup(result.get("answer")),
                reply_to=post["id"])
            ganitra_posts.append(dict(conn.execute(
                "SELECT * FROM group_posts WHERE id = ?",
                (pid,)).fetchone()))
        elif outcome == "plain" and addressed:
            # Asked to Ganitra by name and not maths (or a
            # greeting): the standing one-line reply.
            line = _strip_markup(result.get("answer"))
            if line:
                pid = _insert_post(conn, group_id, None,
                                   "ganitra_note", line,
                                   reply_to=post["id"])
                ganitra_posts.append(dict(conn.execute(
                    "SELECT * FROM group_posts WHERE id = ?",
                    (pid,)).fetchone()))
        conn.commit()
    finally:
        conn.close()
    conn = _connect()
    try:
        post = dict(conn.execute(
            "SELECT * FROM group_posts WHERE id = ?",
            (post["id"],)).fetchone())
    finally:
        conn.close()
    return post, ganitra_posts, None


def _followup_intent(text):
    """The follow-up classification for a group message, with
    Ganitra's name stripped first — a name mention must not
    stop "Ganitra, samjhao" from parsing. Wave 228: besides
    human_brain's redo/explain, the bare VIEW requests the
    1:1 chat has owned since Wave 148/226 — "details mai
    chahiye", "step by step batao" (followups'
    parse_bare_view_request) — count too; before this wave
    they parsed as nothing here and a plain group message
    asking for detail earned silence."""
    stripped = re.sub(r"\bganitra\b", " ", text or "", flags=re.I)
    try:
        from human_brain import parse_human_followup
        intent = parse_human_followup(stripped)
    except Exception:
        intent = None
    if intent is not None:
        return intent
    try:
        from followups import parse_bare_view_request
        return parse_bare_view_request(stripped)
    except Exception:
        return None


def _thread_question(group_id, anchor):
    """The original question post a Ganitra post belongs to,
    walking the reply chain (Wave 228 — the group thread
    anchor). One hop used to be all there was: a follow-up
    answer post points at the MEMBER's follow-up message,
    not at the question, so a second follow-up in a row
    ("samjhao" answered, then "phir se karo") lost the
    question and collapsed. The walk follows reply_to
    through Ganitra's own posts, and through a member post
    only when that post is itself a bare follow-up (the
    chain continues via the Ganitra answer that preceded
    it) — a fresh member message ends the walk, so an old
    unrelated answer is never claimed. Bounded and
    cycle-safe; None when the thread holds no question."""
    conn = _connect()
    try:
        cur = anchor
        seen = set()
        for _ in range(10):
            if cur is None or cur.get("id") in seen:
                return None
            seen.add(cur.get("id"))
            target_id = cur.get("reply_to")
            if not target_id:
                return None
            row = conn.execute(
                "SELECT * FROM group_posts WHERE id = ? AND "
                "group_id = ?", (target_id, group_id)).fetchone()
            if row is None:
                return None
            target = dict(row)
            if target["kind"] == "question":
                return target
            if target["kind"] in ("ganitra", "ganitra_note"):
                cur = target
                continue
            # A member post: the chain continues only when
            # it was itself a follow-up Ganitra answered —
            # via the latest Ganitra post before it.
            if _followup_intent(target["body"]) is None:
                return None
            row = conn.execute(
                "SELECT * FROM group_posts WHERE group_id = ? "
                "AND id < ? AND kind = 'ganitra' ORDER BY id "
                "DESC LIMIT 1", (group_id, target["id"])
                ).fetchone()
            if row is None:
                return None
            cur = dict(row)
        return None
    finally:
        conn.close()


def _own_answer_followup(group_id, post, target, text):
    """(intent, question_post, anchor_post) when this message
    follows up Ganitra's own last answer, else None
    (Wave 225, completed by Wave 228).

    Two shapes count: an explicit reply to Ganitra's answer
    post (or to its correction note), and a bare follow-up
    ask (redo / explain / detail / steps) posted right after
    Ganitra's answer — i.e. Ganitra's answer is the latest
    post in the group. The question is resolved through the
    thread anchor (_thread_question); when the thread holds
    no question post (Ganitra's answer was to a name-called
    general question), the anchor itself is returned so the
    caller can still re-serve from it. Anything else is
    ordinary chat and earns the usual silence."""
    intent = _followup_intent(text)
    anchor = None
    explicit = False
    if target is not None and target["kind"] in ("ganitra",
                                                 "ganitra_note"):
        anchor, explicit = target, True
    elif intent in ("redo", "explain", "detail", "steps"):
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM group_posts WHERE group_id = ? "
                "AND id < ? ORDER BY id DESC LIMIT 1",
                (group_id, post["id"])).fetchone()
        finally:
            conn.close()
        if row is not None and row["kind"] == "ganitra":
            anchor = dict(row)
    if anchor is None:
        return None
    if not explicit and intent not in (
            "redo", "explain", "detail", "steps"):
        return None
    question = _thread_question(group_id, anchor)
    if intent in ("redo", "explain", "detail", "steps") \
            and question is None and anchor["kind"] != "ganitra":
        # A redo/explain aimed at a mere note (whose thread
        # holds no question and which carries no answer of
        # its own to re-serve) is not a follow-up we can
        # honour — ordinary addressed chat, as before.
        return None
    return (intent or "chat"), question, anchor


def _answer_followup(group_id, member_post, question_post,
                     intent, anchor_post=None):
    """Re-serve Ganitra's answer to the question a follow-up
    points at (Wave 225, completed by Wave 228): 'redo'
    solves it fresh, 'explain' / 'detail' / 'steps' solve
    it with fuller steps, each redo/explain behind its kind
    opening line.

    Wave 228: when the fresh solve cannot reproduce an
    answer this time (a leg's quota is gone, a cached miss
    intervenes — the Deploy-68 live shape, where the
    follow-up collapsed to silence or the generic line),
    Ganitra re-serves the answer it ALREADY gave in this
    thread — the anchor post's stored body — instead of
    going quiet: the answer of record is in the thread."""
    qtext = None
    if question_post is not None:
        qtext = question_post["body"]
    elif anchor_post is not None and anchor_post.get("reply_to"):
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT body FROM group_posts WHERE id = ? "
                "AND group_id = ?",
                (anchor_post["reply_to"], group_id)).fetchone()
        finally:
            conn.close()
        if row is not None:
            qtext = row["body"]
    body = None
    if qtext:
        result = _solve(qtext)
        if _classify(result) == "answer":
            try:
                from fallback import _looks_hindi
                lang = "hi" if _looks_hindi(qtext) else "en"
            except Exception:
                lang = "en"
            body = _answer_body(
                result, max_steps=12 if intent in (
                    "explain", "detail", "steps") else 6)
            try:
                from human_brain import intro_line
                intro = intro_line(intent, lang)
            except Exception:
                intro = None
            if intro:
                body = f"{intro}\n{body}"
    if body is None and anchor_post is not None:
        stored = _strip_markup(anchor_post.get("body"))
        if stored:
            body = stored
            if intent in ("redo", "explain"):
                try:
                    from fallback import _looks_hindi
                    lang = "hi" if _looks_hindi(
                        qtext or "") else "en"
                except Exception:
                    lang = "en"
                try:
                    from human_brain import intro_line
                    intro = intro_line(intent, lang)
                except Exception:
                    intro = None
                if intro:
                    body = f"{intro}\n{body}"
    if body is None:
        return None
    conn = _connect()
    try:
        pid = _insert_post(conn, group_id, None, "ganitra", body,
                           reply_to=member_post["id"])
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM group_posts WHERE id = ?",
            (pid,)).fetchone())
    finally:
        conn.close()


def _check_peer_answer(group_id, question_post, peer_text):
    """Judge a peer answer against Ganitra's reference answer.
    Wrong → one polite correction post. Right, or unjudgeable
    (no numbers to compare, or Ganitra has no answer itself)
    → silence (None)."""
    reference = _reference_answer(group_id, question_post)
    if reference is None:
        return None
    ref_values = _values(reference)
    peer_values = _values(peer_text)
    if not ref_values or not peer_values:
        return None
    if any(v == ref_values[0] for v in peer_values):
        return None
    conn = _connect()
    try:
        pid = _insert_post(
            conn, group_id, None, "ganitra_note",
            _correction_body(question_post["body"], reference),
            reply_to=question_post["id"])
        conn.commit()
        return dict(conn.execute(
            "SELECT * FROM group_posts WHERE id = ?",
            (pid,)).fetchone())
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Reports + owner dashboard
# ---------------------------------------------------------------------------

def report_post(group_id, reporter_id, post_id, reason=""):
    conn = _connect()
    try:
        if not conn.execute(
                "SELECT 1 FROM group_members WHERE group_id = ? "
                "AND user_id = ?", (group_id, reporter_id)).fetchone():
            return False, "Tum is group ke member nahi ho."
        post = conn.execute(
            "SELECT id FROM group_posts WHERE id = ? AND "
            "group_id = ?", (post_id, group_id)).fetchone()
        if post is None:
            return False, "Message nahi mila."
        conn.execute(
            "INSERT INTO group_reports (group_id, post_id, "
            "reporter_id, reason, created_at) VALUES (?, ?, ?, "
            "?, ?)", (group_id, post_id, reporter_id,
                      (reason or "")[:200], int(time.time())))
        conn.commit()
        return True, None
    finally:
        conn.close()


def owner_overview():
    """Everything the owner dashboard shows: every group with
    its members and recent activity, plus all reports."""
    conn = _connect()
    try:
        groups = []
        for g in conn.execute(
                "SELECT * FROM study_groups ORDER BY "
                "created_at DESC"):
            g = dict(g)
            g["members"] = [dict(r) for r in conn.execute(
                "SELECT u.id, u.name, p.phone FROM group_members "
                "m JOIN users u ON u.id = m.user_id LEFT JOIN "
                "user_phones p ON p.user_id = u.id WHERE "
                "m.group_id = ? ORDER BY m.joined_at, u.id",
                (g["id"],))]
            g["recent"] = [dict(r) for r in conn.execute(
                "SELECT p.kind, p.body, p.created_at, "
                "u.name AS author_name FROM group_posts p LEFT "
                "JOIN users u ON u.id = p.author_id WHERE "
                "p.group_id = ? ORDER BY p.id DESC LIMIT 5",
                (g["id"],))]
            groups.append(g)
        reports = [dict(r) for r in conn.execute(
            "SELECT r.*, g.name AS group_name, p.body AS "
            "post_body, u.name AS reporter_name FROM "
            "group_reports r JOIN study_groups g ON g.id = "
            "r.group_id JOIN group_posts p ON p.id = r.post_id "
            "JOIN users u ON u.id = r.reporter_id ORDER BY "
            "r.id DESC LIMIT 100")]
        return groups, reports
    finally:
        conn.close()
