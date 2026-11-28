"""Wave 233 (polish sweep): four live defects, fixed at the
root and pinned here.

1. STATS COUNTER — the menu line reads "{count} questions
   solved" but was fed by questions ASKED (user turns), and
   the My Progress "answered" count read result-level keys
   off the stored /api/solve PAYLOAD's top level, so every
   payload counted. Now one canonical predicate
   (accounts.is_answered_result) over the student's own
   chats defines a solved question — a served answer — and
   both surfaces use it.
2. AI PROSE PREFIX LEAK — bare answer labels ("उत्तर:",
   "Jawab:", "Answer:") in an AI leg's reply survived
   shaping and were served as a step line, as a trailing
   stray line, or (worst case) as the answer itself.
   gemini_fallback._shape_result (the one shaping layer all
   three legs share) drops them; ganitra_voice's label list
   learned the Hindi/Roman labels too.
3. GROUP CHAT DISPLAY — (a) the empty-group hint now states
   the actual rule (silence / maths answered / name-call
   answered on any topic) via i18n in all 6 languages;
   (b) group replies were hard-sliced mid-word (steps at
   240 chars, bodies at 1600) — truncation is now
   word-boundary aware and the Answer line is never cut.
4. HINDI PAGE ENGLISH LEAKS — the hard-coded English /
   Hinglish user-facing strings on the error/system surface
   (api.py rate-limit line, app.py group notices, security.py
   CSRF 403 texts, Flask's default error pages) now route
   through i18n with all-6 translations, and none of the new
   keys is swallowed by the Wave-139 system-message pin.

Isolation mirrors Wave 213/232: throwaway DB per test via
GANITRA_DB_PATH, AI-leg keys removed, answer cache cleared.
"""
import json
import sqlite3

import pytest

import solver.answer_cache as cache


@pytest.fixture(autouse=True)
def _clean_caches():
    cache.clear_cache()
    yield
    cache.clear_cache()


@pytest.fixture()
def app_env(tmp_path, monkeypatch):
    db = tmp_path / "users.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(db))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app, db


def _signup(app, name, lang=None):
    c = app.test_client()
    resp = c.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w233-test-pass"})
    assert resp.status_code in (200, 302)
    if lang:
        with c.session_transaction() as sess:
            sess["lang"] = lang
    with c.session_transaction() as sess:
        uid = sess.get("user_id")
    assert uid
    return c, uid


def _solve_and_record(client, chat_id, thread, question):
    """One chat turn exactly as the browser does it: POST
    /api/solve, then append the user record + the bot record
    carrying the whole response payload to the thread."""
    payload = client.post(
        "/api/solve",
        json={"question": question, "chat_id": chat_id}).get_json()
    thread.append({"role": "user", "text": question})
    thread.append({"role": "bot", "data": payload})
    return payload


def _save(client, chat_id, thread):
    resp = client.put(f"/api/chats/{chat_id}",
                      json={"messages": thread})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


# ---------------------------------------------------------------
# Item 1 — the stats counter counts served answers
# ---------------------------------------------------------------

SOLVED_PAYLOAD = {
    "ok": True,
    "result": {"answer": "4", "op": "evaluate",
               "steps": ["2 + 2 = 4"]},
}
GREETING_PAYLOAD = {
    "ok": True,
    "result": {"answer": "Hello! Send me a maths question.",
               "op": "greeting", "fallback_kind": "greeting",
               "plain": True},
}
NOT_FOUND_PAYLOAD = {
    "ok": True,
    "result": {"answer": "I didn't understand that.",
               "op": "not_found", "fallback_kind": "not_found",
               "plain": True},
}
ERROR_PAYLOAD = {
    "ok": False, "unsolvable": True,
    "error": {"heading": "Hmm", "intro": "try again"},
}
OPENROUTER_PAYLOAD = {
    "ok": True,
    "result": {"answer": "6", "op": "openrouter",
               "fallback_kind": "openrouter",
               "steps": ["12 = 2 x 2 x 3"]},
}
BANK_PAYLOAD = {
    "ok": True,
    "result": {"answer": "7", "op": "bank",
               "fallback_kind": "bank", "source": "bank"},
}


def test_is_answered_result_payload_shapes():
    import accounts
    assert accounts.is_answered_result(SOLVED_PAYLOAD)
    assert accounts.is_answered_result(OPENROUTER_PAYLOAD)
    assert accounts.is_answered_result(BANK_PAYLOAD)
    assert not accounts.is_answered_result(GREETING_PAYLOAD)
    assert not accounts.is_answered_result(NOT_FOUND_PAYLOAD)
    assert not accounts.is_answered_result(ERROR_PAYLOAD)
    assert not accounts.is_answered_result(None)
    assert not accounts.is_answered_result("not a dict")
    assert not accounts.is_answered_result({})


def test_is_answered_result_bare_result_shapes():
    """The Wave-89 seed shapes (bare result dicts) classify
    exactly as progress.is_answered always classified them."""
    import accounts
    assert accounts.is_answered_result(
        {"answer": "42", "op": "arithmetic"})
    assert accounts.is_answered_result(
        {"answer": "7", "fallback_kind": "bank"})
    assert accounts.is_answered_result(
        {"answer": "HCF — 6", "fallback_kind": "concept",
         "source": "topics"})
    assert not accounts.is_answered_result(
        {"answer": "card", "fallback_kind": "concept"})
    assert not accounts.is_answered_result(
        {"answer": "Similar", "fallback_kind": "similar"})
    assert not accounts.is_answered_result(
        {"answer": "Hello!", "fallback_kind": "greeting",
         "plain_reply": True})


def test_stats_counter_counts_served_answers_not_asks(app_env):
    app, _db = app_env
    client, uid = _signup(app, "W233 Counter Kid")
    chat = client.post("/api/chats").get_json()["chat"]
    thread = []
    _solve_and_record(client, chat["id"], thread, "2 + 2")
    _solve_and_record(client, chat["id"], thread, "347 + 258")
    _solve_and_record(client, chat["id"], thread, "hello")
    _solve_and_record(client, chat["id"], thread, "asdfqwer zzzx")
    _save(client, chat["id"], thread)
    stats = client.get("/account/stats.json").get_json()
    # 4 questions asked, exactly 2 served answers — the line
    # reads "questions solved", so it must say 2.
    assert stats["questions"] == 2
    assert stats["chats"] == 1
    import accounts, progress
    assert accounts.questions_count(uid) == 4  # asked, unchanged
    record = progress.collect_progress(uid)
    assert record["asked"] == 4
    assert record["answered"] == 2  # agrees with the menu line


def test_stats_counter_grows_exactly_with_real_solves(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W233 Counter Two")
    for expected, questions in (
            (3, ["5 + 5", "9 - 4", "3 x 3"]),
            (5, ["10 / 2", "7 + 8"])):
        chat = client.post("/api/chats").get_json()["chat"]
        thread = []
        for q in questions:
            _solve_and_record(client, chat["id"], thread, q)
        _save(client, chat["id"], thread)
        stats = client.get("/account/stats.json").get_json()
        assert stats["questions"] == expected


def test_solved_count_backfills_a_pre233_database(tmp_path,
                                                  monkeypatch):
    """A database whose chats table predates the solved_turns
    column: the parse fallback answers first, then the first
    chats connect backfills the column with the same number."""
    db = tmp_path / "old.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(db))
    thread = [
        {"role": "user", "text": "2 + 2"},
        {"role": "bot", "data": SOLVED_PAYLOAD},
        {"role": "user", "text": "hello"},
        {"role": "bot", "data": GREETING_PAYLOAD},
        {"role": "user", "text": "banked?"},
        {"role": "bot", "data": BANK_PAYLOAD},
    ]
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE chats ("
        " id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " user_id INTEGER NOT NULL,"
        " title TEXT NOT NULL DEFAULT '',"
        " messages_json TEXT NOT NULL DEFAULT '[]',"
        " created_at INTEGER NOT NULL,"
        " updated_at INTEGER NOT NULL,"
        " user_turns INTEGER NOT NULL DEFAULT 0)")
    conn.execute(
        "INSERT INTO chats (user_id, title, messages_json,"
        " created_at, updated_at, user_turns)"
        " VALUES (7, '', ?, 1, 2, 3)",
        (json.dumps(thread),))
    conn.commit()
    conn.close()

    import accounts
    assert accounts.solved_count(7) == 2  # parse fallback
    import chats
    chats.init_db()  # first connect: column added + backfilled
    conn = sqlite3.connect(db)
    cols = {row[1] for row in conn.execute("PRAGMA table_info(chats)")}
    assert "solved_turns" in cols
    stored = conn.execute(
        "SELECT solved_turns FROM chats WHERE user_id = 7"
    ).fetchone()[0]
    conn.close()
    assert stored == 2
    assert accounts.solved_count(7) == 2  # now the fast SUM


# ---------------------------------------------------------------
# Item 2 — bare answer labels never survive shaping
# ---------------------------------------------------------------

from gemini_fallback import _shape_result  # noqa: E402


def _assert_no_bare_label(result):
    assert result is not None
    for step in result["steps"]:
        assert step.strip().rstrip(":") not in (
            "उत्तर", "Jawab", "Answer", "अंतिम उत्तर")
    assert result["answer"].strip().rstrip(":") not in (
        "उत्तर", "Jawab", "Answer")


def test_bare_label_leading_hindi_dropped():
    r = _shape_result(
        "उत्तर:\nपहले 12 और 18 के गुणनखंड लिखो।\n"
        "12 = 2 × 2 × 3\n18 = 2 × 3 × 3\n"
        "सबसे बड़ा साझा गुणनखंड 6 है।\nउत्तर: 6")
    _assert_no_bare_label(r)
    assert r["answer"] == "6"
    assert r["steps"][0].startswith("पहले 12")


def test_bare_label_trailing_hindi_dropped():
    r = _shape_result(
        "12 = 2 × 2 × 3\n18 = 2 × 3 × 3\n"
        "सबसे बड़ा साझा गुणनखंड 6 है।\nउत्तर: 6\nउत्तर:")
    _assert_no_bare_label(r)
    assert r["answer"] == "6"
    assert r["steps"][-1].startswith("सबसे बड़ा")


def test_bare_label_never_becomes_the_answer():
    """The worst case: no real answer line, a bare label at
    the tail — the label used to be SERVED as the answer."""
    r = _shape_result(
        "12 और 18 का HCF निकालने के लिए गुणनखंड करो।\n"
        "12 = 2 × 2 × 3\n18 = 2 × 3 × 3\nउत्तर:")
    _assert_no_bare_label(r)


def test_bare_label_leading_english_and_roman_dropped():
    r = _shape_result(
        "Answer:\nFirst write the factors of 12 and 18.\n"
        "12 = 2 x 2 x 3\n18 = 2 x 3 x 3\n"
        "The greatest common factor is 6.\nAnswer: 6")
    _assert_no_bare_label(r)
    assert r["answer"] == "6"
    r = _shape_result(
        "Jawab:\nPehle 12 aur 18 ke factors likho.\n"
        "12 = 2 x 2 x 3\n18 = 2 x 3 x 3\n"
        "Sabse bada common factor 6 hai.\nJawab: 6")
    _assert_no_bare_label(r)
    assert r["answer"] == "6"


def test_bare_label_in_general_gk_reply_dropped():
    """The group name-call route's shape: a prose GK answer
    opened by a bare label."""
    r = _shape_result(
        "उत्तर:\nभारत की राजधानी नई दिल्ली है।\n"
        "यह यमुना नदी के किनारे स्थित है।\nउत्तर: नई दिल्ली")
    _assert_no_bare_label(r)
    assert r["answer"] == "नई दिल्ली"
    assert r["steps"][0].startswith("भारत की राजधानी")


def test_legit_lines_containing_the_word_survive():
    r = _shape_result(
        "उत्तर प्रदेश की राजधानी लखनऊ है।\n"
        "यह भारत का सबसे अधिक जनसंख्या वाला राज्य है।\n"
        "उत्तर: लखनऊ")
    assert r["steps"][0].startswith("उत्तर प्रदेश")
    assert r["answer"] == "लखनऊ"
    r = _shape_result(
        "Answer the question by comparing both sides.\n"
        "Left side = 2 + 3 = 5\nRight side = 5\n"
        "Both sides are equal.\nAnswer: 5")
    assert r["steps"][0].startswith("Answer the question")
    assert r["answer"] == "5"


def test_only_a_bare_label_is_nothing_usable():
    assert _shape_result("उत्तर:") is None
    assert _shape_result("Answer:") is None


def test_label_then_value_still_shapes():
    r = _shape_result("Answer:\n6")
    assert r["answer"] == "6"
    assert r["steps"] == []


def test_groq_and_openrouter_shaping_share_the_fix():
    from gemini_fallback import _shape_result as _s  # noqa: F401
    from groq_fallback import _shape_groq_result
    from openrouter_fallback import _shape_openrouter_result
    text = ("उत्तर:\n12 = 2 × 2 × 3\n18 = 2 × 3 × 3\n"
            "उत्तर: 6\nउत्तर:")
    for shape in (_shape_groq_result, _shape_openrouter_result):
        r = shape(text)
        _assert_no_bare_label(r)
        assert r["answer"] == "6"


def test_group_body_carries_no_bare_label():
    """Group serves consume shaped results — the shaped
    steps + the group body builder together must not let a
    bare label reach a group post."""
    import groups as study_groups
    r = _shape_result(
        "Jawab:\n12 = 2 x 2 x 3\n18 = 2 x 3 x 3\nJawab: 6")
    body = study_groups._answer_body(r)
    assert "Jawab:" not in body
    assert body.endswith("Answer: 6")


# ---------------------------------------------------------------
# Item 3 — group display: the hint + word-safe truncation
# ---------------------------------------------------------------

def _group_setup(app):
    admin, _a = _signup(app, "W233 Group Admin")
    member, _m = _signup(app, "W233 Group Member")
    admin.post("/groups/phone", data={"phone": "9811111111"})
    member.post("/groups/phone", data={"phone": "9822222222"})
    resp = admin.post("/groups/create", data={
        "name": "W233 Group", "member_phones": "9822222222"})
    assert resp.status_code in (200, 302)
    import groups as study_groups
    with admin.session_transaction() as sess:
        uid = sess["user_id"]
    groups = study_groups.list_groups_for(uid)
    assert groups
    return admin, member, groups[0]["id"]


def test_group_empty_hint_states_the_rule_en(app_env):
    app, _db = app_env
    admin, _member, gid = _group_setup(app)
    body = admin.get(f"/groups/{gid}").get_data(as_text=True)
    from i18n import STRINGS
    assert STRINGS["en"]["group_empty_hint"] in body
    hint = STRINGS["en"]["group_empty_hint"]
    assert "chup rehta hai" in hint       # Ganitra stays silent
    assert "maths ka sawal" in hint       # maths is answered
    assert "Ganitra, …" in hint           # name-call, any topic
    assert "kisi bhi topic" in hint


def test_group_empty_hint_in_hindi(app_env):
    app, _db = app_env
    admin, _member, gid = _group_setup(app)
    with admin.session_transaction() as sess:
        sess["lang"] = "hi"
    body = admin.get(f"/groups/{gid}").get_data(as_text=True)
    from i18n import STRINGS
    assert STRINGS["hi"]["group_empty_hint"] in body
    assert STRINGS["en"]["group_empty_hint"] not in body


def test_group_truncation_never_cuts_mid_word():
    import groups as study_groups
    step = ("Pehle dono sankhyaon ke gunankhand achhe se "
            "likhte hain aur phir unme se sabse bada saajha "
            "gunankhand chun lete hain jo dono ko poora "
            "bhaag de de aur koi shesh na bache bilkul "
            "theek se dekho to chhah aata hai pakka wala "
            "aur yahi tarika har baar kaam karta hai sada")
    assert len(step) > 240
    body = study_groups._answer_body(
        {"steps": [step], "answer": "6"})
    first = body.splitlines()[0]
    assert first.endswith("…")
    visible = first[:-1]
    # the visible part is a whole-word prefix of the step:
    # the very next character in the original is a space.
    assert step.startswith(visible)
    assert step[len(visible)] == " "
    assert body.endswith("Answer: 6")
    assert len(body) <= study_groups.MAX_ANSWER_CHARS


def test_group_truncation_keeps_answer_when_steps_overflow():
    import groups as study_groups
    steps = [("word " * 120).strip() for _ in range(6)]
    body = study_groups._answer_body(
        {"steps": steps, "answer": "42"})
    assert len(body) <= study_groups.MAX_ANSWER_CHARS
    assert body.rstrip().endswith("Answer: 42")


def test_group_short_body_is_byte_identical_to_before():
    import groups as study_groups
    body = study_groups._answer_body(
        {"steps": ["12 + 8 = 20"], "answer": "20"})
    assert body == "12 + 8 = 20\nAnswer: 20"


def test_insert_post_truncates_on_a_word_boundary(app_env):
    app, db = app_env
    _admin, _member, gid = _group_setup(app)
    import groups as study_groups
    long_body = ("ye ek bahut lamba sandesh hai jo seema se "
                 "zyada bada hai " * 60).strip()
    conn = study_groups._connect()
    try:
        pid = study_groups._insert_post(
            conn, gid, None, "ganitra", long_body)
        conn.commit()
        row = conn.execute(
            "SELECT body FROM group_posts WHERE id = ?",
            (pid,)).fetchone()
    finally:
        conn.close()
    stored = row[0]
    assert len(stored) <= study_groups.MAX_ANSWER_CHARS
    assert stored.endswith("…")
    assert long_body.startswith(stored[:-1])
    assert long_body[len(stored) - 1] == " "


# ---------------------------------------------------------------
# Item 4 — hard-coded strings now route through i18n
# ---------------------------------------------------------------

WAVE233_KEYS = (
    "group_empty_hint", "group_err_not_member",
    "group_notice_member_added", "group_notice_member_removed",
    "group_notice_closed", "group_notice_reported",
    "api_rate_limited", "csrf_not_verified", "csrf_page_text",
    "csrf_back_home", "error_page_not_found",
    "error_page_server", "error_page_home",
)


def test_wave233_keys_complete_and_translated():
    from i18n import STRINGS
    for key in WAVE233_KEYS:
        en = STRINGS["en"][key]
        assert en.strip()
        for lang in ("hi", "bn", "mr", "ta", "te"):
            value = STRINGS[lang][key]
            assert value.strip(), (key, lang)
            # a real translation, not the English text copied
            assert value != en, (key, lang)


def test_wave233_keys_escape_the_system_message_pin():
    """Wave 139 pins SYSTEM_MESSAGE_KEYS to English in every
    language — these keys must NOT be pinned, or a Hindi
    student would keep seeing English."""
    from i18n import SYSTEM_MESSAGE_KEYS, get_strings
    for key in WAVE233_KEYS:
        assert key not in SYSTEM_MESSAGE_KEYS
    assert get_strings("hi")["api_rate_limited"] != \
        get_strings("en")["api_rate_limited"]
    assert get_strings("hi")["group_empty_hint"].startswith("अभी")


def test_404_page_is_localised(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W233 Lost Kid", lang="hi")
    resp = client.get("/ye-page-nahi-hai")
    assert resp.status_code == 404
    body = resp.get_data(as_text=True)
    from i18n import STRINGS
    assert STRINGS["hi"]["error_page_not_found"] in body
    assert "could not be found" not in body
    anon = app.test_client()
    resp = anon.get("/ye-page-nahi-hai")
    assert resp.status_code == 404
    assert STRINGS["en"]["error_page_not_found"] in \
        resp.get_data(as_text=True)


def test_api_404_is_json_and_localised(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W233 Api Lost", lang="hi")
    resp = client.get("/api/koi-route-nahi")
    assert resp.status_code == 404
    body = resp.get_json()
    from i18n import STRINGS
    assert body["ok"] is False
    assert body["message"] == STRINGS["hi"]["error_page_not_found"]


def test_csrf_failure_is_localised(app_env):
    app, _db = app_env
    client, _uid = _signup(app, "W233 Csrf Kid", lang="hi")
    origin = {"Origin": "http://localhost"}
    resp = client.post("/api/solve", json={"question": "2+2"},
                       headers=origin)
    assert resp.status_code == 403
    from i18n import STRINGS
    assert resp.get_json()["message"] == \
        STRINGS["hi"]["csrf_not_verified"]
    resp = client.post("/groups/phone",
                       data={"phone": "9811111111"},
                       headers=origin)
    assert resp.status_code == 403
    assert STRINGS["hi"]["csrf_page_text"] in \
        resp.get_data(as_text=True)


def test_rate_limit_line_is_localised(app_env, monkeypatch):
    app, _db = app_env
    import api
    monkeypatch.setattr(api, "_solve_rate_limited",
                        lambda: True)
    client, _uid = _signup(app, "W233 Busy Kid", lang="hi")
    resp = client.post("/api/solve", json={"question": "2+2"})
    assert resp.status_code == 429
    from i18n import STRINGS
    assert resp.get_json()["message"] == \
        STRINGS["hi"]["api_rate_limited"]
    anon = app.test_client()
    resp = anon.post("/api/solve", json={"question": "2+2"})
    assert resp.status_code == 429
    # English keeps the exact pre-233 line, byte for byte.
    assert resp.get_json()["message"] == \
        "Too many questions at once — please wait a minute " \
        "and try again."


def test_group_notices_follow_the_language(app_env):
    app, _db = app_env
    admin, _member, gid = _group_setup(app)
    # default (Hinglish house voice — the Wave-213 pin's text)
    resp = admin.post(f"/groups/{gid}/close", data={})
    assert "Group band kar diya gaya." in \
        resp.get_data(as_text=True)


def test_group_notices_in_hindi(app_env):
    app, _db = app_env
    admin, _member, gid = _group_setup(app)
    with admin.session_transaction() as sess:
        sess["lang"] = "hi"
    resp = admin.post(f"/groups/{gid}/close", data={})
    from i18n import STRINGS
    assert STRINGS["hi"]["group_notice_closed"] in \
        resp.get_data(as_text=True)
