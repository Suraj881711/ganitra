"""Wave 117: the Live Bank (livebank.py).

Questions students actually ask join a runtime bank the
moment they are answered (Suraj, 17 Nov 2026: "user jo
question puche woh bhi turant add karo apni bank ke
andar"). Proven here:

- a solver answer and a deterministic fall-through answer
  (topics concept card) are stored VERIFIED; a repeat ask
  bumps the hit count instead of duplicating the row, and a
  fall-through repeat is SERVED from the store (the
  live_bank=True marker; the original source is preserved,
  like the app's other caches) with the identical answer;
- an AI-brain answer (Gemini seam monkeypatched, the Wave
  41/107 pattern) is stored PENDING and is NEVER served —
  with the AI down, the same question falls back to the
  honest chain outcome, not the stored AI text;
- not-found / non-maths / greeting / science outcomes store
  NOTHING (Wave 90's log owns the not-found ones);
- a question the master bank already answers is not
  duplicated into the live store;
- the schema is exactly the promised field set — question
  text, payload, kind/source, language key, status, hits,
  timestamps — and holds NO identity field of any kind
  (privacy pin, mirroring test_wave90);
- the language key follows Wave 107: an explicit request
  keys the row, and a stored answer serves only a
  same-key ask (a Hindi-requested answer never leaks into
  an English ask);
- the pending export speaks the master bank's item shape
  (question / steps / final_answer) for the databank cron,
  and set_status() promotion makes a verified pending item
  servable (demotion unserves it);
- the layer is an accelerator only: a corrupt DB file, a
  corrupt payload row and the GANITRA_LIVEBANK=0 kill
  switch all degrade to exactly the pre-Wave-117 chain.
"""
import json
import sqlite3
from pathlib import Path

import pytest

import fallback
import livebank
from fallback import fallback_answer

ROOT = Path(__file__).resolve().parent.parent

PERCENT_Q = "What is 17% of 380?"
PRIME_Q = "What is a prime number?"
AGES_Q = ("Ten years ago, a father was twelve times as old "
          "as his son and ten years hence, he will be twice "
          "as old as his son. Find their present ages.")

_EXPECTED_COLUMNS = {
    "id", "question_norm", "lang_key", "question_text",
    "answer_json", "kind", "source", "status", "hits",
    "first_seen", "last_seen",
}


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "lb.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    return path


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _rows():
    return livebank.all_rows()


# --- 1. Recording: solver + deterministic answers -----------

def test_solver_answer_stored_verified(db):
    res = fallback_answer(PERCENT_Q)
    assert res["answer"] == "64.6"
    rows = _rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["question_norm"] == "what is 17 of 380"
    assert row["question_text"] == PERCENT_Q
    assert row["lang_key"] == "en"
    assert row["status"] == "verified"
    assert row["kind"] == "percentage"
    assert row["hits"] == 1
    assert row["first_seen"] > 0
    assert row["last_seen"] >= row["first_seen"]
    payload = json.loads(row["answer_json"])
    assert payload["answer"] == "64.6"


def test_repeat_ask_bumps_hits_not_rows(db):
    fallback_answer(PERCENT_Q)
    fallback_answer("what is 17% of 380")
    fallback_answer("WHAT IS 17% OF 380?!")
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["hits"] == 3
    # First-seen raw text is the kept example.
    assert rows[0]["question_text"] == PERCENT_Q


def test_concept_answer_stored_and_served(db):
    first = fallback_answer(PRIME_Q)
    assert first.get("source") == "topics"
    assert len(_rows()) == 1
    # The repeat is served from the store — the marker and
    # the identical answer prove it did not re-run the
    # fall-through layers. The original source ("topics")
    # is preserved, exactly as the answer cache and the
    # negative cache return stored results unrestamped.
    second = fallback_answer(PRIME_Q)
    assert second.get("live_bank") is True
    assert second.get("source") == "topics"
    assert second["answer"] == first["answer"]
    assert second["steps"] == first["steps"]
    hit = livebank.lookup_live_result(PRIME_Q, "en")
    assert hit is not None and hit["live_bank"] is True
    # One hit per ask: the first ask recorded, each serve
    # bumped (a served result is never re-recorded).
    assert _rows()[0]["hits"] == 3


# --- 2. AI answers: pending, never served --------------------

_AI_RESULT = {
    "type": "Ganitra", "op": "gemini",
    "answer": "The present ages are 42 and 17.",
    "steps": ["Let the son's age be x."],
    "fallback": True, "fallback_kind": "gemini",
    "ai_generated": True,
}


def test_ai_answer_pending_and_never_served(db, monkeypatch):
    monkeypatch.setattr(
        fallback, "_gemini_answer",
        lambda q, hindi, lang_request=None: dict(_AI_RESULT))
    failed = {"op": "error",
              "answer": "Could not solve this one: x",
              "steps": []}
    res = fallback.with_fallback(AGES_Q, dict(failed),
                                 lang="en")
    assert res["fallback_kind"] == "gemini"
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "pending"
    assert rows[0]["kind"] == "gemini"
    # The store itself refuses to serve a pending row...
    assert livebank.lookup_live_result(AGES_Q, "en") is None
    # ...and with the AI brain down, the repeat ask gets the
    # honest chain outcome — never the stored AI text.
    monkeypatch.setattr(
        fallback, "_gemini_answer",
        lambda q, hindi, lang_request=None: None)
    res2 = fallback.with_fallback(AGES_Q, dict(failed),
                                  lang="en")
    assert res2["fallback_kind"] == "not_found"
    assert res2.get("live_bank") is not True


# --- 3. Outcomes that store nothing --------------------------

@pytest.mark.parametrize("question,kind", [
    ("If tu gfuf", "not_found"),
    ("What is the capital of France?", "nonmaths"),
    ("hello", "greeting"),
    ("What is the refractive index of a medium?", "science"),
])
def test_unanswered_outcomes_store_nothing(db, question, kind):
    res = fallback_answer(question)
    assert res["fallback_kind"] == kind
    assert _rows() == []


def test_master_bank_question_not_duplicated(db):
    first_line = (ROOT / "bank_data.jsonl").read_text(
        encoding="utf-8").splitlines()[0]
    item = json.loads(first_line)
    res = fallback_answer(item["question"])
    # Answered (by the bank layer or the solver — either
    # way the master bank already owns this question)...
    assert res.get("answer")
    # ...and the live store did NOT duplicate it.
    assert _rows() == []


# --- 4. Privacy: the schema is the whole record --------------

def test_schema_columns_are_exactly_the_promised_set(db):
    fallback_answer(PERCENT_Q)
    conn = sqlite3.connect(db)
    try:
        cols = {r[1] for r in conn.execute(
            "PRAGMA table_info(live_bank)")}
    finally:
        conn.close()
    assert cols == _EXPECTED_COLUMNS
    for col in cols:
        for banned in ("user", "name", "session", "class",
                       "password", "favourite", "account"):
            assert banned not in col


def test_classify_result_units():
    assert livebank.classify_result(
        {"op": "percentage", "answer": "36"}) == "verified"
    assert livebank.classify_result(
        {"op": "gemini", "answer": "x", "fallback": True,
         "fallback_kind": "gemini",
         "ai_generated": True}) == "pending"
    assert livebank.classify_result(
        {"op": "not_found", "answer": "Answer not found.",
         "fallback_kind": "not_found"}) is None
    assert livebank.classify_result(
        {"op": "nonmaths", "answer": "guard",
         "fallback_kind": "nonmaths", "plain": True}) is None
    assert livebank.classify_result(
        {"op": "error", "answer": "Could not solve"}) is None
    assert livebank.classify_result({"op": "x"}) is None
    assert livebank.classify_result(None) is None
    assert livebank.classify_result("not a dict") is None


# --- 5. Language keys (Wave 107 discipline) ------------------

def test_lang_key_rules():
    key = fallback._livebank_lang_key
    assert key("What is 2+2?", "en", None) == "en"
    assert key("त्रिभुज का क्षेत्रफल क्या है?", "hi",
               None) == "hi"
    assert key("mujhe ye sawal batao", "hi", None) == "hinglish"
    # An explicit request outranks everything.
    assert key("What is 2+2?", "en", "hi") == "hi"
    assert key("What is 2+2?", "hi", "en") == "en"
    assert key("What is 2+2?", "en", "hinglish") == "hinglish"
    # A bn/mr/ta/te session keys under itself.
    assert key("What is 2+2?", "bn", None) == "bn"


def test_stored_answer_serves_only_matching_language(db):
    fallback_answer(PRIME_Q, lang_request="hi")
    rows = _rows()
    assert len(rows) == 1 and rows[0]["lang_key"] == "hi"
    # An English ask must NOT be served the Hindi-keyed row.
    assert livebank.lookup_live_result(PRIME_Q, "en") is None
    res_en = fallback_answer(PRIME_Q, lang_request="en")
    assert res_en.get("live_bank") is not True
    # The matching request IS served from the store.
    res_hi = fallback_answer(PRIME_Q, lang_request="hi")
    assert res_hi.get("live_bank") is True


# --- 6. Pending export + promotion ---------------------------

def test_pending_export_and_promotion(db):
    ai = dict(_AI_RESULT)
    assert livebank.record_answer(AGES_Q, ai, "en") is True
    assert livebank.lookup_live_result(AGES_Q, "en") is None
    items = livebank.pending_items()
    assert len(items) == 1
    item = items[0]
    assert item["question"] == AGES_Q
    assert item["final_answer"] == _AI_RESULT["answer"]
    assert item["steps"] == _AI_RESULT["steps"]
    assert item["lang"] == "en"
    out = db.parent / "pending.jsonl"
    assert livebank.write_pending_export(out) == 1
    lines = out.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["question"] == AGES_Q
    # Promotion (what the cron does after verify.py passes):
    # the item becomes servable; demotion unserves it.
    from bank import normalise_question
    norm = normalise_question(AGES_Q)
    assert livebank.set_status(norm, "en", "verified") is True
    served = livebank.lookup_live_result(AGES_Q, "en")
    assert served is not None
    assert served["answer"] == _AI_RESULT["answer"]
    assert livebank.set_status(norm, "en", "pending") is True
    assert livebank.lookup_live_result(AGES_Q, "en") is None
    assert livebank.set_status(norm, "en", "bogus") is False


def test_verified_row_never_downgraded_by_ai(db):
    solver = {"type": "Algebra", "op": "percentage",
              "answer": "64.6", "steps": ["17% of 380"]}
    assert livebank.record_answer(PERCENT_Q, solver,
                                  "en") is True
    assert livebank.record_answer(PERCENT_Q, dict(_AI_RESULT),
                                  "en") is True
    row = _rows()[0]
    assert row["status"] == "verified"
    assert json.loads(row["answer_json"])["answer"] == "64.6"
    assert row["hits"] == 2


# --- 7. Degradation: the layer can only ever no-op -----------

def test_corrupt_db_file_degrades(db):
    db.write_bytes(b"this is not a sqlite database")
    res = fallback_answer(PERCENT_Q)
    assert res["answer"] == "64.6"
    assert livebank.record_answer(
        PERCENT_Q, {"op": "percentage", "answer": "64.6"},
        "en") is False
    assert livebank.lookup_live_result(PERCENT_Q, "en") is None


def test_corrupt_payload_row_is_a_miss(db):
    fallback_answer(PRIME_Q)
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            "UPDATE live_bank SET answer_json = 'not json{{{ '")
        conn.commit()
    finally:
        conn.close()
    assert livebank.lookup_live_result(PRIME_Q, "en") is None
    res = fallback_answer(PRIME_Q)
    assert res.get("source") == "topics"


def test_kill_switch_turns_layer_off(db, monkeypatch):
    fallback_answer(PRIME_Q)
    assert len(_rows()) == 1
    monkeypatch.setenv("GANITRA_LIVEBANK", "0")
    assert livebank.lookup_live_result(PRIME_Q, "en") is None
    res = fallback_answer(PRIME_Q)
    assert res.get("source") == "topics"
    assert livebank.record_answer(
        PERCENT_Q, {"op": "percentage", "answer": "64.6"},
        "en") is False


def test_overlong_question_not_stored(db):
    long_q = "What is 2 + 2? " + "x" * 600
    assert livebank.record_answer(
        long_q, {"op": "add", "answer": "4"}, "en") is False
    assert _rows() == []


# --- 8. The real routes record too ---------------------------

def test_api_solve_route_records_and_serves(client):
    from solver.answer_cache import clear_cache, clear_negative_cache
    # Deploy-25 merge: Wave 111's battery asks PRIME_Q
    # through the solve path earlier in the suite, which
    # warms the shared answer cache; a cached first response
    # never reaches with_fallback, so nothing would record.
    # Clear it (the cache's own test seam) so the first post
    # runs the full chain.
    clear_cache()
    body = client.post(
        "/api/solve", json={"question": PRIME_Q}).get_json()
    assert body["ok"] is True
    assert len(_rows()) == 1
    # The first outcome rides the negative cache on a repeat;
    # clear it (Wave 48's own test seam) so the repeat must
    # come through the chain — where the live bank serves it.
    clear_negative_cache()
    body = client.post(
        "/api/solve", json={"question": PRIME_Q}).get_json()
    assert body["ok"] is True
    assert body["result"]["live_bank"] is True
    assert body["result"]["source"] == "topics"
    assert body["result"]["answer"]


def test_classic_solve_route_records(client):
    html = client.post(
        "/solve", data={"question": PERCENT_Q}
    ).get_data(as_text=True)
    assert "64.6" in html
    rows = _rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "verified"
