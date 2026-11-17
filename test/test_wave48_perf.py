"""Wave 48 (performance round; Wave-45 audit Part B items 3 + 5):

- Negative cache: a question whose final outcome is a fallback
  answer is served identically for a short TTL instead of
  re-paying solve x2 + fallback layers on every re-ask.
- Positive answer-cache LRU raised 200 -> 1000 entries.
- Account stats are O(1): questions_count is one indexed SUM
  over per-chat user_turns counters; chats_count is COUNT(*).
  No stored thread is parsed to answer either.
"""
import json
import sqlite3

import pytest

import accounts
import chats
import solver.answer_cache as cache
from api import _solve_friendly
import api


@pytest.fixture(autouse=True)
def _clean_caches():
    cache.clear_cache()
    yield
    cache.clear_cache()


def _fallback_result(kind="guide"):
    return {"type": "Ganitra", "op": "guide",
            "answer": "Ek baar sawal ko thoda saaf likh kar bhejo",
            "steps": [], "fallback": True, "fallback_kind": kind}


# --- Negative cache: unit ---------------------------------------

def test_negative_roundtrip_and_key_normalisation():
    assert cache.put_negative("What is x if x + y = 10?",
                              _fallback_result()) is True
    hit = cache.get_negative("  what   is x if x + y = 10? ")
    assert hit == _fallback_result()
    assert cache.cache_stats()["negative_hits"] == 1
    assert cache.cache_stats()["negative_entries"] == 1


def test_negative_refuses_real_and_unflagged_results():
    real = {"type": "arithmetic", "op": "evaluate", "answer": "4",
            "steps": []}
    assert cache.put_negative("2+2", real) is False
    assert cache.put_negative("q", {"answer": "x"}) is False
    assert cache.put_negative("q", "not a dict") is False
    assert cache.cache_stats()["negative_entries"] == 0


def test_negative_refuses_bank_verified_answers():
    bank = _fallback_result(kind="bank")
    bank["verified"] = True
    assert cache.put_negative("bank q", bank) is False
    flagged = _fallback_result(kind="bank")
    assert cache.put_negative("bank q", flagged) is False


def test_negative_refuses_ai_seam_answers():
    ai = _fallback_result(kind="gemini")
    ai["ai_generated"] = True
    assert cache.put_negative("ai q", ai) is False
    assert cache.put_negative("ai q", _fallback_result(kind="groq")) \
        is False
    assert cache.cache_stats()["negative_entries"] == 0


def test_negative_ttl_expiry(monkeypatch):
    cache.put_negative("q", _fallback_result())
    assert cache.get_negative("q") is not None
    monkeypatch.setattr(cache, "_NEG_TTL_SECONDS", -1)
    assert cache.get_negative("q") is None
    # The expired entry was dropped, not just ignored.
    assert cache.cache_stats()["negative_entries"] == 0


def test_negative_evicts_oldest_when_full(monkeypatch):
    monkeypatch.setattr(cache, "_NEG_MAX_ENTRIES", 2)
    for i in range(3):
        assert cache.put_negative(f"q{i}", _fallback_result())
    assert cache.get_negative("q0") is None
    assert cache.get_negative("q1") is not None
    assert cache.get_negative("q2") is not None


def test_negative_served_copy_cannot_poison_the_store():
    cache.put_negative("q", _fallback_result())
    served = cache.get_negative("q")
    served["answer"] = "tampered"
    assert cache.get_negative("q")["answer"] != "tampered"


def test_clear_cache_also_clears_negative():
    cache.put_negative("q", _fallback_result())
    cache.clear_cache()
    assert cache.get_negative("q") is None
    assert cache.cache_stats()["negative_entries"] == 0


# --- Positive LRU size ------------------------------------------

def test_positive_lru_bound_is_1000():
    assert cache.cache_stats()["max_entries"] == 1000
    for i in range(1001):
        cache.put_cached(f"q{i}", {"type": "arithmetic",
                                   "answer": str(i), "steps": []})
    assert cache.cache_stats()["entries"] == 1000
    assert cache.get_cached("q0") is None
    assert cache.get_cached("q1000")["answer"] == "1000"


# --- _solve_friendly integration --------------------------------

def test_solve_friendly_serves_repeat_failure_from_negative(monkeypatch):
    calls = {"solve": 0, "fallback": 0}

    def fake_solve(question):
        calls["solve"] += 1
        return {"type": "solver", "op": "error",
                "answer": "Could not solve", "steps": []}

    def fake_fallback(question, result, lang=None,
                      student_class=None, lang_request=None):
        # Wave 67: with_fallback grew the optional lang kwarg.
        # Wave 107: and the optional lang_request kwarg.
        calls["fallback"] += 1
        return _fallback_result()

    monkeypatch.setattr(api, "solve_question", fake_solve)
    monkeypatch.setattr(api, "with_fallback", fake_fallback)

    first = _solve_friendly("an unsolvable ask")
    # First ask pays solve + hinted retry + fallback, once each layer.
    assert calls == {"solve": 2, "fallback": 1}
    second = _solve_friendly("  AN   UNSOLVABLE ASK ")
    assert second == first
    assert calls == {"solve": 2, "fallback": 1}  # nothing re-ran


def test_solve_friendly_never_negative_caches_real_answers(monkeypatch):
    calls = {"solve": 0}
    real = {"type": "arithmetic", "op": "evaluate", "answer": "4",
            "steps": ["2 + 2 = 4"]}

    def fake_solve(question):
        calls["solve"] += 1
        return dict(real)

    monkeypatch.setattr(api, "solve_question", fake_solve)
    monkeypatch.setattr(api, "with_fallback",
                        lambda question, result, lang=None,
        student_class=None, lang_request=None: result)
    assert _solve_friendly("2+2") == real
    assert _solve_friendly("2+2") == real
    assert calls["solve"] == 2  # re-solved (positive cache's domain)
    assert cache.cache_stats()["negative_entries"] == 0


def test_solve_friendly_real_fallback_question_repeats_identically():
    q = "Why does the moon change shape every night?"
    first = _solve_friendly(q)
    assert first.get("fallback") is True
    second = _solve_friendly(q)
    assert second == first
    assert cache.cache_stats()["negative_hits"] >= 1


# --- O(1) account stats ------------------------------------------

@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = str(tmp_path / "users.db")
    monkeypatch.setenv("GANITRA_DB_PATH", path)
    return path


def _turns(user_turns):
    msgs = []
    for i in range(user_turns):
        msgs.append({"role": "user", "text": f"q{i}"})
        msgs.append({"role": "bot", "data": {"result": {"answer": "a"}}})
    return msgs


def _legacy_questions(user_id):
    return sum(1 for thread in accounts._chat_rows(user_id)
               for msg in thread
               if isinstance(msg, dict) and msg.get("role") == "user")


def test_stats_match_legacy_parse_and_track_writes(db):
    uid = 7
    c1 = chats.create_chat(uid)
    chats.save_chat(uid, c1["id"], _turns(3))
    c2 = chats.create_chat(uid)
    chats.save_chat(uid, c2["id"],
                    [{"role": "bot", "data": {"result": {}}}])
    c3 = chats.create_chat(uid)
    chats.save_chat(uid, c3["id"], _turns(5) + ["junk", 42])

    assert accounts.chats_count(uid) == 3
    assert accounts.questions_count(uid) == 8
    assert accounts.questions_count(uid) == _legacy_questions(uid)

    # Rewriting a thread re-counts it (no double counting).
    chats.save_chat(uid, c1["id"], _turns(10))
    assert accounts.questions_count(uid) == 15
    assert accounts.questions_count(uid) == _legacy_questions(uid)

    # The 200-message cap is reflected in the counter.
    big = chats.create_chat(uid)
    chats.save_chat(uid, big["id"], _turns(125))
    assert accounts.questions_count(uid) == 15 + 100

    # Deletes take their counts with them.
    chats.delete_chat(uid, c3["id"])
    assert accounts.chats_count(uid) == 3
    assert accounts.questions_count(uid) == 15 + 100 - 5
    chats.delete_all_chats(uid)
    assert accounts.chats_count(uid) == 0
    assert accounts.questions_count(uid) == 0


def test_stats_are_scoped_per_user(db):
    chats.save_chat(8, chats.create_chat(8)["id"], _turns(2))
    chats.save_chat(9, chats.create_chat(9)["id"], _turns(4))
    assert accounts.questions_count(8) == 2
    assert accounts.questions_count(9) == 4
    assert accounts.chats_count(8) == 1


def test_stats_on_empty_and_missing_tables(db):
    assert accounts.questions_count(123) == 0
    assert accounts.chats_count(123) == 0


def test_stats_migration_backfills_pre_wave48_database(db):
    # A database written by the pre-Wave-48 code: chats table
    # WITHOUT the user_turns column.
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE chats (id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_id INTEGER NOT NULL, title TEXT NOT NULL DEFAULT '',"
        " messages_json TEXT NOT NULL DEFAULT '[]',"
        " created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL)")
    legacy_msgs = _turns(4)
    conn.execute(
        "INSERT INTO chats (user_id, title, messages_json,"
        " created_at, updated_at) VALUES (5, '', ?, 1, 1)",
        (json.dumps(legacy_msgs),))
    conn.commit()
    conn.close()

    # Before chats.py ever connects, the legacy parse still answers.
    assert accounts.questions_count(5) == 4
    assert accounts.chats_count(5) == 1

    # First chats.py connect migrates + backfills.
    listed = chats.list_chats(5)
    assert len(listed) == 1
    conn = sqlite3.connect(db)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(chats)")}
    stored = conn.execute(
        "SELECT user_turns FROM chats WHERE user_id = 5").fetchone()[0]
    conn.close()
    assert "user_turns" in cols
    assert stored == 4
    assert accounts.questions_count(5) == 4

    # And new writes keep the migrated counter correct.
    chats.save_chat(5, listed[0]["id"], _turns(6))
    assert accounts.questions_count(5) == 6
    assert accounts.questions_count(5) == _legacy_questions(5)
