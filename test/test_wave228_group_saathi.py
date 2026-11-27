"""Wave 228 — Group AI completion + Saathi mode + the
number-word pair fix (Suraj's orders, 28 Nov 2026).

1. GROUP AI COMPLETION (the two Deploy-68 live partials):
   (a) a name-called NON-maths question in a group got the
   canned / maths-only line — the native chain's guard
   refuses it before the AI legs are consulted, and a total
   miss ends at the not-found line. Now the name-call goes
   to fallback's verified AI chain (Wave 226) and the real
   answer is served; when the legs also have nothing, the
   standing line stands — never a fabricated answer.
   (b) a bare follow-up ("samjhao", "phir se karo",
   "details mai chahiye") as a PLAIN group message after
   Ganitra's own answer: the detail/steps view requests
   parsed as nothing here, a second follow-up in a row lost
   the question (the anchor walk was one hop), and a failed
   re-solve collapsed the follow-up to silence / the
   generic line. Now the view intents count, the thread
   anchor walks the reply chain, and a dead re-solve
   re-serves the stored answer of record.

2. SAATHI MODE (23 Nov spec): a personal / emotional share
   in the 1:1 chat earns a kind companion reply, never the
   maths-only / not-found line — while maths questions
   (including the word "tension" carrying numbers, and
   sad-sounding word problems) are never diverted, and
   other-subject study asks keep the maths-only rule.

3. NUMBER-WORDS PAIR FIX: human_brain._words_to_digits
   summed a number-word pair joined by "and" ("HCF of
   twelve and eighteen" -> "HCF of 30"); the "and" joins
   inside one quantity only after a scale word — the rule
   deep_solve.digitise already states.

Isolation follows the Wave-225 pattern: throwaway DB via
GANITRA_DB_PATH, answer cache cleared around each test,
AI legs stubbed at the fallback seams (no network, no
keys) or left unconfigured.
"""
import pytest

import fallback
import groups as study_groups
import livebank
import solver.answer_cache as cache
from api import _solve_friendly
from human_brain import normalize_human_text


@pytest.fixture(autouse=True)
def _clean_caches():
    cache.clear_cache()
    yield
    cache.clear_cache()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY", raising=False)
    from app import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


def _signup(app, name):
    client = app.test_client()
    r = client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "test-pass-228"})
    assert r.status_code == 302, (name, r.status_code)
    return client


def _uid(client):
    with client.session_transaction() as sess:
        return sess["user_id"]


@pytest.fixture()
def trio(app):
    owner = _signup(app, "Owner One")
    a = _signup(app, "Asha Verma")
    b = _signup(app, "Ravi Kumar")
    owner.post("/groups/phone", data={"phone": "9800000000"})
    a.post("/groups/phone", data={"phone": "9811111111"})
    b.post("/groups/phone", data={"phone": "9822222222"})
    return owner, a, b


@pytest.fixture()
def group_ab(app, trio):
    owner, a, b = trio
    r = owner.post("/groups/create", data={
        "name": "Maths Dost",
        "member_phones": "9811111111\n9822222222"})
    assert r.status_code in (200, 302)
    gid = study_groups.list_groups_for(_uid(a))[0]["id"]
    return gid, _uid(owner), _uid(a), _uid(b)


def _ai(kind, answer, steps=None):
    return {"type": "Ganitra", "op": kind, "answer": answer,
            "steps": steps if steps is not None else [answer],
            "fallback": True, "fallback_kind": kind,
            "ai_generated": True}


@pytest.fixture()
def capital_leg(monkeypatch):
    """A gemini leg that answers capital questions only."""
    def fake_gemini(question, hindi, lang_request=None, **kw):
        q = str(question).lower()
        if "rajdhani" in q or "capital" in q:
            return _ai("gemini", "Bharat ki rajdhani New Delhi hai.")
        return None
    monkeypatch.setattr(fallback, "_gemini_answer", fake_gemini)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


@pytest.fixture()
def dead_legs(monkeypatch):
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


# ---------------------------------------------------------------------------
# 3. The number-word pair fix
# ---------------------------------------------------------------------------

def test_number_pair_joined_by_and_stays_two_numbers():
    assert normalize_human_text(
        "HCF of twelve and eighteen") == "HCF of 12 and 18"
    assert normalize_human_text(
        "forty five and thirty six") == "45 and 36"
    assert normalize_human_text(
        "barah and atharah ka HCF") == "12 and 18 ka HCF"
    # "aur" was never summed; it stays a separator.
    assert normalize_human_text(
        "gyarah aur barah") == "11 aur 12"


def test_single_quantity_and_still_joins():
    assert normalize_human_text(
        "one hundred and twenty five") == "125"
    assert normalize_human_text("one hundred and five") == "105"
    assert normalize_human_text(
        "two thousand and twenty") == "2020"
    assert normalize_human_text(
        "one lakh and five thousand") == "105000"
    # Pre-existing conversions are untouched.
    assert normalize_human_text(
        "do sau pachas rupaye") == "250 rupaye"


def test_hcf_of_twelve_and_eighteen_route(client228):
    # The flagged defect, end to end through the real
    # route: the normaliser used to hand the solver
    # "HCF of 30" (one operand), now it hands it both.
    data = _route_solve(client228,
                        "What is the HCF of twelve and eighteen?")
    assert data["result"]["answer"] == "6"


# ---------------------------------------------------------------------------
# 1(a). Name-called general questions reach the AI legs
# ---------------------------------------------------------------------------

def test_name_called_capital_english_answered_via_legs(
        app, group_ab, capital_leg):
    # The guard-caught form: the native chain answers this
    # with the maths-only line and never consults a leg —
    # only the Wave 228 name-call route can answer it.
    gid, _owner, a_id, _b = group_ab
    post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, what is the capital of India?")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "New Delhi" in ganitra[0]["body"]
    assert "only solves Maths" not in ganitra[0]["body"]
    # A general question is not dressed up as a maths
    # question post (no peer-answer judging attaches).
    assert post["kind"] == "chat"
    # Prose is served once, not restated as an "Answer:".
    assert ganitra[0]["body"].count("New Delhi") == 1


def test_name_called_rajdhani_answered(app, group_ab, capital_leg):
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, Bharat ki rajdhani kya hai?")
    assert err is None
    assert len(ganitra) == 1 and "New Delhi" in ganitra[0]["body"]


def test_name_called_maths_still_native(app, group_ab, capital_leg):
    gid, _owner, a_id, _b = group_ab
    post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, 12 + 8 kitna hota hai?")
    assert err is None
    assert post["kind"] == "question"
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_name_called_gk_legs_dead_keeps_standing_line(
        app, group_ab, dead_legs):
    # No leg has an answer -> the standing maths-only line,
    # never a fabricated one.
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, what is the capital of India?")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra_note"
    assert "only solves Maths" in ganitra[0]["body"]
    assert "New Delhi" not in ganitra[0]["body"]


def test_name_called_capital_via_group_route(
        app, trio, group_ab, capital_leg):
    _owner, a, b = trio
    gid, _o, _a, _b_id = group_ab
    r = b.post(f"/groups/{gid}/post", data={
        "text": "Ganitra, what is the capital of India?"})
    assert r.status_code == 200
    assert "New Delhi" in r.get_data(as_text=True)


# ---------------------------------------------------------------------------
# 1(b). Bare follow-ups as plain group messages
# ---------------------------------------------------------------------------

def _ask_and_answer(gid, uid, text="12 + 8"):
    post, ganitra, err = study_groups.post_message(gid, uid, text)
    assert err is None and len(ganitra) == 1
    assert "Answer: 20" in ganitra[0]["body"]
    return post, ganitra[0]


def test_plain_details_request_after_answer(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "details mai chahiye")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "Answer: 20" in ganitra[0]["body"]


def test_plain_steps_request_after_answer(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "step by step batao")
    assert err is None
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_chained_followup_still_finds_the_question(app, group_ab):
    # "samjhao" is answered; a bare "phir se karo" after
    # THAT answer must still reach the original question —
    # the follow-up answer post points at the member's
    # follow-up message, not at the question (the one-hop
    # anchor lost it and the follow-up went silent).
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _p, g1, err = study_groups.post_message(gid, b_id, "samjhao")
    assert err is None and len(g1) == 1
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "phir se karo")
    assert err is None
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_followup_floor_when_the_resolve_dies(
        app, group_ab, monkeypatch):
    # The Deploy-68 live shape: the follow-up's fresh solve
    # cannot reproduce the answer (quota / cached miss) —
    # the follow-up must re-serve the answer of record from
    # the thread, not collapse to silence or the generic
    # line.
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    monkeypatch.setattr(study_groups, "_solve", lambda text: {
        "answer": "Samajh nahi aaya — maths ka sawal thoda "
                  "saaf likh kar bhejo.",
        "steps": [], "fallback_kind": "not_found",
        "plain": True})
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "samjhao")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "Answer: 20" in ganitra[0]["body"]


def test_bare_details_after_member_chat_stays_silent(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _p, g1, err = study_groups.post_message(
        gid, b_id, "kal match hai doston, sab aana")
    assert err is None and g1 == []
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "details mai chahiye")
    assert err is None and ganitra == []


def test_details_followup_via_group_route(app, trio, group_ab):
    _owner, a, b = trio
    gid, _o, _a, _b_id = group_ab
    a.post(f"/groups/{gid}/post", data={"text": "12 + 8"})
    r = b.post(f"/groups/{gid}/post",
               data={"text": "details mai chahiye"})
    assert r.status_code == 200
    # The original answer AND its detailed re-serve.
    assert r.get_data(as_text=True).count("Answer: 20") >= 2


# ---------------------------------------------------------------------------
# 2. Saathi mode
# ---------------------------------------------------------------------------

CANNED = ("I didn't understand that", "Samajh nahi aaya",
          "only solves Maths", "sirf Maths")


def _assert_saathi(res):
    assert res.get("fallback_kind") == "saathi", res
    assert res.get("plain_reply") is True, res
    for bad in CANNED:
        assert bad not in str(res.get("answer") or ""), res


def test_saathi_hinglish_distress():
    res = _solve_friendly(
        "mujhe bahut tension ho rahi hai, mann nahi lag "
        "raha padhai me")
    _assert_saathi(res)
    assert "sun raha hoon" in res["answer"]


def test_saathi_english_anxiety():
    res = _solve_friendly(
        "I feel very anxious and I can't stop overthinking")
    _assert_saathi(res)
    assert "I hear you" in res["answer"]


def test_saathi_devanagari_gets_devanagari_reply():
    res = _solve_friendly(
        "मुझे बहुत परेशानी है, किसी को बता नहीं सकता")
    _assert_saathi(res)
    assert "सुन रहा हूँ" in res["answer"]


def test_saathi_cant_tell_anyone_at_home():
    res = _solve_friendly(
        "main bahut pareshan hoon, ghar par kisi ko bata "
        "nahi sakta")
    _assert_saathi(res)
    assert "bharosa" in res["answer"]


def test_saathi_health_worry():
    res = _solve_friendly(
        "meri tabiyat kharab hai, bahut darr lag raha hai")
    _assert_saathi(res)


def test_saathi_crisis_encourages_a_trusted_adult():
    res = _solve_friendly(
        "mujhe mar jana hai, jeene ka mann nahi karta")
    _assert_saathi(res)
    # Kind, never frightening: a trusted adult today, and a
    # professional named as a right step — no lecture words.
    assert "aaj hi batao" in res["answer"]
    assert "counsellor" in res["answer"]
    for bad in ("khatarnak", "warning", "punish", "galat kar"):
        assert bad not in res["answer"]


def test_bare_mann_nahi_lag_stays_guidance():
    # The Wave 154 boundary: a wandering mind in studies,
    # alone, is the guidance layer's pinned motivation
    # case — saathi needs distress company.
    res = _solve_friendly("mann nahi lag raha padhai me")
    assert res.get("fallback_kind") == "guidance", res
    assert res.get("guidance_id") == "motivation", res


def test_mann_nahi_lag_with_distress_company_is_saathi():
    res = _solve_friendly(
        "mera kisi cheez me mann nahi lag raha")
    _assert_saathi(res)


def test_saathi_route_api_solve(client228):
    data = _route_solve(
        client228,
        "mujhe bahut tension ho rahi hai, mann nahi lag raha")
    res = data["result"]
    assert res.get("fallback_kind") == "saathi", data
    assert "sun raha hoon" in str(res.get("answer") or "")


def test_saathi_reply_is_never_banked():
    q = "mujhe bahut tension ho rahi hai, mann nahi lag raha"
    res = _solve_friendly(q)
    _assert_saathi(res)
    # The Live Bank's classifier refuses plain results, and
    # a record attempt is a no-op: the reply can never be
    # stored as — or later served as — a maths answer.
    assert livebank.classify_result(res) is None
    assert livebank.record_answer(q, res) is False


@pytest.mark.parametrize("text", [
    # "tension" as a physics word, carrying numbers: the
    # science path, exactly as before — never saathi.
    "A string under tension of 10 N is stretched, find "
    "the force if length doubles from 2 m to 4 m",
    # A sad-sounding word problem is a maths question.
    "Rahul is sad because he lost 15 marbles. He had 40 "
    "marbles, how many are left?",
    "Rahul is sad because he lost fifteen marbles. He had "
    "forty marbles. How many marbles are left now?",
    # Distress words WITH a maths payload solve the maths.
    "mujhe tension ho rahi hai, ye solve karo: 25% of 400 "
    "kitna hota hai?",
    # A straight study ask on another subject keeps the
    # maths-only rule (the scope boundary).
    "photosynthesis samjhao, mujhe bilkul samajh nahi aata",
    "What is the capital of India?",
])
def test_saathi_never_diverts_maths_or_study(text):
    res = _solve_friendly(text)
    assert res.get("fallback_kind") != "saathi", res
    assert res.get("op") != "saathi", res


def test_tension_payload_question_is_solved():
    res = _solve_friendly(
        "mujhe tension ho rahi hai, ye solve karo: 25% of "
        "400 kitna hota hai?")
    assert res.get("fallback_kind") != "saathi"
    assert "100" in str(res.get("answer") or "")


# ---------------------------------------------------------------------------
# Route fixture for /api/solve (Deploy-70 test style)
# ---------------------------------------------------------------------------

@pytest.fixture()
def client228(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_AI_STREAM", raising=False)
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    r = c.post("/signup", data={
        "name": "Wave228 Check", "class": "10",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave228pass"})
    assert r.status_code == 302, r.status_code
    return c


def _route_solve(client, question):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    chat_id = r.get_json()["chat"]["id"]
    r = client.post("/api/solve", json={
        "question": question, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    return r.get_json()
