"""Wave 117: the Live Bank — questions students actually ask
join the bank the moment they are answered.

Suraj's order (17 Nov 2026): "user jo question puche woh bhi
turant add karo apni bank ke andar" — a question a student
asks must enter the bank immediately, not wait for the
offline databank pipeline to happen upon it. This module is
that runtime store. It sits beside the two existing layers:

  * bank.py — the master Verified Data Bank: a static
    snapshot (bank_data.jsonl) of items that were
    independently SymPy-verified OFFLINE before banking.
    Nothing in this module ever writes to it.
  * notfound_log.py (Wave 90) — the learning log for
    questions NOBODY could answer. This module is its mirror
    image: it records questions that WERE answered, so a
    repeat ask can be served instantly. Not-found outcomes
    are never stored here (the Wave 90 log owns them).

STORAGE CHOICE: a `live_bank` table in the existing accounts
DB (accounts.db_path — GANITRA_DB_PATH env wins, as
everywhere), created with CREATE TABLE IF NOT EXISTS on the
write path. That is the codebase's established pattern for
runtime state (notfound_log.py, chats.py, accounts.py all do
exactly this): it survives deploys on PythonAnywhere because
the DB file lives outside the code tree, it needs no new
file management, and one short-timeout connection per write
keeps it safe next to the accounts tables. An append-only
JSONL was rejected: dedupe + hit counts + a status flip need
random-access updates, which JSONL does badly, and the read
path would have to scan the whole file per question.

WHAT IS STORED (and nothing else): the question text (first-
seen raw form, capped at the app's own 500-char limit), its
normalised form (bank.normalise_question — the same
normalisation the master bank indexes by), the answer payload
(the full result dict as JSON, so it can be re-served through
every existing renderer unchanged), the result's kind and
source, a language key (see below), a status, hit count and
timestamps. PRIVACY: question text only — no name, no user
id, no class, no session field of any kind is read or
stored; this module never imports an account record, only
the DB *path* helper. The schema below is the whole record;
test_wave117 pins its column set.

STATUS — the quality gate (Suraj's zero-mistake rule):
  * "verified" — the answer came from a deterministic layer:
    the solver itself, the master bank, or one of the
    deterministic fall-through layers (MCQ / multipart /
    formats / proofs / salvage / concept cards). Those are
    pure functions of the question text, so re-serving the
    stored payload for the identical question reproduces
    exactly what the chain would answer today. Only
    verified rows are ever served.
  * "pending" — the answer came from an AI brain (Gemini /
    Groq / OpenRouter; ai_generated / fallback_kind in
    {gemini, groq, openrouter}). AI answers can be wrong, so
    a pending row is NEVER served to anyone. It waits for
    the offline databank pipeline: pending_items() /
    write_pending_export() expose it in the master bank's
    own item shape, the 2-hourly databank cron runs it
    through verify.py, and passing items are promoted into
    the master bank (and flipped here via set_status()).

LANGUAGE: every row carries a lang_key computed by the
caller (fallback.py, which owns the Wave 107 language
rules): an explicit in-message request ("hi" / "en" /
"hinglish") wins; a bn/mr/ta/te session language keys under
itself; otherwise the question's own flavour decides
(Devanagari -> "hi", Roman Hindi -> "hinglish", else "en").
A stored answer is served ONLY to an ask whose lang_key
matches exactly — Wave 107's rule that a Hindi-requested
answer must never leak into an English ask (and vice versa).
When in doubt, the keys differ and nothing is served.

SAFETY: like the Wave 90 log, this layer is purely an
accelerator. record_answer() and lookup_live_result() NEVER
raise: any failure (DB locked, disk full, table gone,
corrupt payload, stale graph file) is a silent no-op / miss,
and the solve flow continues exactly as it did before this
wave. The write happens AFTER the answer is final, so a
store failure can never slow or break the answer itself.
Set GANITRA_LIVEBANK=0 to switch the whole layer off
(answers are then byte-identical to pre-Wave-117).
"""
import json
import os
import sqlite3
import time

_SCHEMA = """
CREATE TABLE IF NOT EXISTS live_bank (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_norm TEXT NOT NULL,
    lang_key      TEXT NOT NULL DEFAULT 'en',
    question_text TEXT NOT NULL,
    answer_json   TEXT NOT NULL,
    kind          TEXT,
    source        TEXT,
    status        TEXT NOT NULL DEFAULT 'verified',
    hits          INTEGER NOT NULL DEFAULT 1,
    first_seen    INTEGER NOT NULL,
    last_seen     INTEGER NOT NULL,
    UNIQUE(question_norm, lang_key)
)
"""

_INDEX_STATUS = ("CREATE INDEX IF NOT EXISTS idx_live_bank_status"
                 " ON live_bank(status)")
_INDEX_LAST_SEEN = ("CREATE INDEX IF NOT EXISTS"
                    " idx_live_bank_last_seen"
                    " ON live_bank(last_seen)")

_TEXT_CAP = 500        # the app's own question limit (api/app)
_PAYLOAD_CAP = 65536   # bytes; bigger payloads are reduced/skip

VERIFIED = "verified"
PENDING = "pending"

# One-line outcomes that are NOT answers to a question —
# friendly guard lines and the not-found collapse. They are
# never stored (the not-found ones are Wave 90's to log).
_SKIP_KINDS = frozenset({
    "not_found", "nonmaths", "greeting", "vague", "science",
})
_AI_KINDS = frozenset({"gemini", "groq", "openrouter"})

# The reduced payload kept when a full result dict will not
# JSON-serialise (or is oversized): exactly the fields the
# renderers need to re-serve an answer.
_SAFE_KEYS = ("type", "op", "answer", "steps", "fallback",
              "fallback_kind", "source", "verified",
              "concept_id", "topic_slug", "topic_class",
              "bank_id")


def _enabled():
    return os.environ.get("GANITRA_LIVEBANK", "1").strip() != "0"


def _db_path():
    # Lazy import, same pattern as notfound_log.py: accounts.py
    # is stdlib-only, and keeping the import inside the call
    # can never create an import cycle.
    from accounts import db_path
    return db_path()


def _normalise(text):
    """bank.normalise_question when available (it always is
    in the app); the same local fallback notfound_log uses,
    so grouping stays sane if the bank module ever fails."""
    try:
        from bank import normalise_question
        return normalise_question(text)
    except Exception:
        import re
        import unicodedata
        t = unicodedata.normalize("NFC", str(text or "")).lower()
        return re.sub(r"\s+", " ", t).strip()


def _in_master_bank(question):
    """True when the master bank already answers this exact
    question — those are never duplicated into the live
    store. Any bank failure reads as "not in the bank" (the
    record then proceeds; a duplicate row is harmless next
    to a lost one)."""
    try:
        from bank import lookup
        return lookup(question) is not None
    except Exception:
        return False


def classify_result(result):
    """The store decision for one finished solve outcome:
    "verified", "pending", or None (do not store).

    A result is storeable only when it carries a real answer
    text. AI-brain results are pending (never served until
    offline verification promotes them); the friendly
    one-line outcomes (plain_reply / plain flags, or a kind
    in _SKIP_KINDS) and raw solver errors are not answers
    and are refused; everything else that reaches here came
    from a deterministic layer and is verified."""
    if not isinstance(result, dict):
        return None
    answer = result.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return None
    if result.get("op") == "error":
        return None
    kind = result.get("fallback_kind")
    op = result.get("op")
    if kind in _SKIP_KINDS or op in _SKIP_KINDS:
        return None
    if result.get("plain_reply") or result.get("plain"):
        # Wave 68's one-line replies (greeting / guard /
        # not-found) are plain by flag as well as by kind.
        return None
    if result.get("ai_generated") or kind in _AI_KINDS:
        return PENDING
    return VERIFIED


def _payload_json(result):
    """The result dict as a JSON string, or None when it
    cannot be stored. Oversized or non-serialisable results
    fall back to the reduced renderer-safe payload; if even
    that fails, the answer is simply not stored."""
    try:
        text = json.dumps(result, ensure_ascii=False)
        if len(text.encode("utf-8")) <= _PAYLOAD_CAP:
            return text
    except (TypeError, ValueError):
        pass
    try:
        reduced = {k: result[k] for k in _SAFE_KEYS
                   if k in result}
        text = json.dumps(reduced, ensure_ascii=False)
        if len(text.encode("utf-8")) <= _PAYLOAD_CAP:
            return text
    except (TypeError, ValueError):
        pass
    return None


def record_answer(question, result, lang_key=None):
    """Store one answered question. Returns True when a row
    was created or refreshed, False for any no-op (layer
    off, unstoreable outcome, master-bank duplicate, empty
    or over-long question, ANY error). Never raises: the
    answer is already final when this runs, and a store
    failure must not slow, break or alter it — the write is
    one indexed upsert on a short-timeout connection, and
    the whole body is guarded.

    A repeat ask of an already-stored question bumps its
    hit count instead of duplicating the row. A verified
    row is never downgraded by a later pending outcome for
    the same question (the deterministic answer stays the
    served truth); a pending row IS refreshed by a newer
    outcome (a fresher AI attempt, or a verified answer
    upgrading it)."""
    if not _enabled():
        return False
    try:
        status = classify_result(result)
        if status is None:
            return False
        raw = str(question or "")
        if len(raw) > _TEXT_CAP:
            return False
        norm = _normalise(raw)
        if not norm:
            return False
        if _in_master_bank(raw):
            return False
        payload = _payload_json(result)
        if payload is None:
            return False
        key = str(lang_key or "en")
        kind = result.get("fallback_kind") or result.get("op")
        source = (result.get("source")
                  or result.get("fallback_kind")
                  or result.get("op") or "")
        now = int(time.time())
        conn = sqlite3.connect(_db_path(), timeout=2.0)
        try:
            conn.execute(_SCHEMA)
            conn.execute(_INDEX_STATUS)
            conn.execute(_INDEX_LAST_SEEN)
            row = conn.execute(
                "SELECT status FROM live_bank"
                " WHERE question_norm = ? AND lang_key = ?",
                (norm, key)).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO live_bank (question_norm,"
                    " lang_key, question_text, answer_json,"
                    " kind, source, status, hits, first_seen,"
                    " last_seen) VALUES (?, ?, ?, ?, ?, ?, ?,"
                    " 1, ?, ?)",
                    (norm, key, raw.strip()[:_TEXT_CAP],
                     payload, kind, source, status, now, now))
            elif row[0] == VERIFIED and status == PENDING:
                # Never downgrade: bump the counters only.
                conn.execute(
                    "UPDATE live_bank SET hits = hits + 1,"
                    " last_seen = ? WHERE question_norm = ?"
                    " AND lang_key = ?", (now, norm, key))
            else:
                conn.execute(
                    "UPDATE live_bank SET hits = hits + 1,"
                    " last_seen = ?, answer_json = ?,"
                    " kind = ?, source = ?, status = ?"
                    " WHERE question_norm = ? AND lang_key = ?",
                    (now, payload, kind, source, status,
                     norm, key))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def _graphs_still_exist(result):
    """A stored payload that names graph image files is
    served only while those files are still on disk — the
    same staleness rule the answer cache applies
    (solver.answer_cache._graphs_exist). If the check
    itself cannot run, do not serve what cannot be
    validated."""
    try:
        from solver.answer_cache import _graphs_exist
        return bool(_graphs_exist(result))
    except Exception:
        return False


def lookup_live_result(question, lang_key=None):
    """The stored VERIFIED answer for this exact question +
    language key, shaped for serving, or None.

    The returned dict is the stored payload byte-identical
    to the answer the chain produced when the question was
    first asked, plus one marker field — live_bank=True.
    The original `source` is deliberately PRESERVED (the
    app's other caches — the answer cache, the negative
    cache — likewise return stored results without
    restamping their source: the field names the layer that
    PRODUCED the answer, and the live bank is only its
    store). Pending
    rows are invisible here by construction (status =
    'verified' is in the WHERE clause). A hit bumps the
    row's counters on a best-effort basis. Any problem —
    layer off, no DB file, no table, corrupt payload,
    stale graph — is a plain miss, and the caller's chain
    runs exactly as it did before this wave."""
    if not _enabled():
        return None
    try:
        norm = _normalise(question)
        if not norm:
            return None
        path = _db_path()
        if not os.path.isfile(path):
            return None
        key = str(lang_key or "en")
        conn = sqlite3.connect(path, timeout=2.0)
        try:
            found = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table'"
                " AND name='live_bank'").fetchone()
            if not found:
                return None
            row = conn.execute(
                "SELECT id, answer_json FROM live_bank"
                " WHERE question_norm = ? AND lang_key = ?"
                " AND status = ?",
                (norm, key, VERIFIED)).fetchone()
            if row is None:
                return None
            try:
                payload = json.loads(row[1])
            except ValueError:
                return None
            if not isinstance(payload, dict):
                return None
            answer = payload.get("answer")
            if not isinstance(answer, str) or not answer.strip():
                return None
            if not _graphs_still_exist(payload):
                return None
            try:
                conn.execute(
                    "UPDATE live_bank SET hits = hits + 1,"
                    " last_seen = ? WHERE id = ?",
                    (int(time.time()), row[0]))
                conn.commit()
            except Exception:
                pass
        finally:
            conn.close()
        result = dict(payload)
        result["live_bank"] = True
        return result
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Owner / pipeline side: the pending-verification export
# ---------------------------------------------------------------------------

def _read_rows(db_path=None, status=None, limit=None):
    """Stored rows as dicts, most-hit first (then most
    recent). Read-only in spirit: a missing DB file or a
    not-yet-created table reads as an empty store, never an
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
                " AND name='live_bank'").fetchone()
            if not found:
                return []
            sql = ("SELECT id, question_norm, lang_key,"
                   " question_text, answer_json, kind, source,"
                   " status, hits, first_seen, last_seen"
                   " FROM live_bank")
            args = []
            if status is not None:
                sql += " WHERE status = ?"
                args.append(status)
            sql += " ORDER BY hits DESC, last_seen DESC"
            if limit is not None:
                sql += " LIMIT ?"
                args.append(int(limit))
            rows = conn.execute(sql, args).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def all_rows(db_path=None):
    """Every stored row (owner tooling / tests)."""
    return _read_rows(db_path=db_path)


def row_count(db_path=None, status=None):
    """Stored questions (optionally one status only)."""
    return len(_read_rows(db_path=db_path, status=status))


def pending_items(limit=None, db_path=None):
    """The PENDING (AI-answered) items in the master bank's
    own item shape — the export contract for the databank
    pipeline. Each item:

        {live_bank_id, question, question_norm, lang,
         steps, final_answer, kind, source, hits,
         first_seen, last_seen}

    The cron feeds `question` + `final_answer` through
    verify.py exactly as it does generated items; items
    that pass are imported into the master bank and flipped
    here with set_status(question_norm, lang, "verified").
    Items whose stored payload no longer parses are skipped
    (they can never be promoted on a broken record)."""
    items = []
    for row in _read_rows(db_path=db_path, status=PENDING,
                          limit=limit):
        try:
            payload = json.loads(row["answer_json"])
        except (ValueError, TypeError):
            continue
        if not isinstance(payload, dict):
            continue
        items.append({
            "live_bank_id": row["id"],
            "question": row["question_text"],
            "question_norm": row["question_norm"],
            "lang": row["lang_key"],
            "steps": payload.get("steps") or [],
            "final_answer": payload.get("answer") or "",
            "kind": row["kind"],
            "source": row["source"],
            "hits": row["hits"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
        })
    return items


def write_pending_export(path, limit=None, db_path=None):
    """Write pending_items() as JSONL (one item per line)
    to `path`; returns how many items were written. This
    file is the hand-off point the 2-hourly databank cron
    consumes."""
    items = pending_items(limit=limit, db_path=db_path)
    with open(path, "w", encoding="utf-8") as fh:
        for item in items:
            fh.write(json.dumps(item, ensure_ascii=False))
            fh.write("\n")
    return len(items)


def set_status(question_norm, lang_key, status, db_path=None):
    """Flip one stored row's status — the pipeline's
    promotion hook after verify.py has passed a pending
    item (status="verified"), or a demotion if a verified
    row is ever found wrong (status="pending" takes it out
    of serving immediately). Returns True when a row was
    updated. Guarded like everything else here: any failure
    is a plain False."""
    if status not in (VERIFIED, PENDING):
        return False
    try:
        path = db_path or _db_path()
        if not os.path.isfile(path):
            return False
        conn = sqlite3.connect(path, timeout=2.0)
        try:
            found = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table'"
                " AND name='live_bank'").fetchone()
            if not found:
                return False
            cur = conn.execute(
                "UPDATE live_bank SET status = ?"
                " WHERE question_norm = ? AND lang_key = ?",
                (status, question_norm, str(lang_key or "en")))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()
    except Exception:
        return False


__all__ = ["VERIFIED", "PENDING", "classify_result",
           "record_answer", "lookup_live_result",
           "pending_items", "write_pending_export",
           "set_status", "all_rows", "row_count"]
