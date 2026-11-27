"""Wave 225 (Suraj, 27 Nov 2026): Group Study — WhatsApp-style
creation flow + the 23 Nov behaviour spec nuance.

1. Creation ORDER is WhatsApp's: Step 1 members select/add
   (by mobile number), Step 2 group name, then Create. The
   backend contract (name + member_phones -> /groups/create)
   is unchanged, so this pins the page order and the route.
2. Ganitra speaks in a group only when (a) a maths question
   is asked, or (b) it is called by name — any topic. A
   follow-up to Ganitra's OWN last answer ("samjhao",
   "galat hai, phir se karo", or any reply aimed at its
   answer post) counts as addressed to it. Everything else
   earns silence.

Isolation follows the Wave-213 pattern: throwaway DB via
GANITRA_DB_PATH, answer cache cleared around each test, AI
legs unconfigured; pipeline-level cases use the deterministic
native solver, topic cases stub groups._solve directly.
"""
import pytest

import groups as study_groups
import solver.answer_cache as cache


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
        "password": "test-pass-225"})
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


# ---------------------------------------------------------------------------
# 1. WhatsApp-order creation page
# ---------------------------------------------------------------------------

def test_create_page_members_step_comes_before_name_step(app, trio):
    owner, _a, _b = trio
    body = owner.get("/groups").get_data(as_text=True)
    members_at = body.index('id="gs-step-members"')
    name_at = body.index('id="gs-step-name"')
    assert members_at < name_at
    # The backend contract is untouched: one form posting
    # name + member_phones to /groups/create.
    assert 'action="/groups/create"' in body
    assert 'name="member_phones"' in body
    assert 'name="name"' in body


def test_create_group_route_unchanged(app, trio):
    owner, a, b = trio
    r = owner.post("/groups/create", data={
        "name": "Maths Dost",
        "member_phones": "9811111111, 9822222222"})
    assert r.status_code in (200, 302)
    groups = study_groups.list_groups_for(_uid(a))
    assert len(groups) == 1 and groups[0]["member_count"] == 3


# ---------------------------------------------------------------------------
# 2. Name trigger — any topic; silence otherwise
# ---------------------------------------------------------------------------

def test_name_called_general_question_is_answered(app, group_ab,
                                                   monkeypatch):
    gid, _owner, a_id, _b = group_ab
    monkeypatch.setattr(study_groups, "_solve", lambda text: {
        "answer": "Bharat ki rajdhani New Delhi hai.",
        "steps": [], "fallback_kind": "gemini"})
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, Bharat ki rajdhani kya hai?")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "New Delhi" in ganitra[0]["body"]


def test_name_called_nonmaths_gets_the_maths_only_line(app, group_ab,
                                                       monkeypatch):
    gid, _owner, a_id, _b = group_ab
    monkeypatch.setattr(study_groups, "_solve", lambda text: {
        "answer": "Ganitra only solves Maths questions.",
        "steps": [], "fallback_kind": "nonmaths", "plain": True})
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "Ganitra, ek kahani sunao")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra_note"
    assert "only solves Maths" in ganitra[0]["body"]


def test_unaddressed_general_chat_stays_silent(app, group_ab,
                                               monkeypatch):
    gid, _owner, a_id, _b = group_ab
    monkeypatch.setattr(study_groups, "_solve", lambda text: {
        "answer": "Ganitra only solves Maths questions.",
        "steps": [], "fallback_kind": "nonmaths", "plain": True})
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "koi ek kahani sunao na")
    assert err is None and ganitra == []


# ---------------------------------------------------------------------------
# 3. Follow-ups to Ganitra's own answer count as addressed
# ---------------------------------------------------------------------------

def _ask_and_answer(gid, uid, text="12 + 8"):
    post, ganitra, err = study_groups.post_message(gid, uid, text)
    assert err is None and len(ganitra) == 1
    assert "Answer: 20" in ganitra[0]["body"]
    return post, ganitra[0]


def test_followup_redo_by_reply_to_ganitra_answer(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _q, answer = _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "galat hai, phir se karo",
        reply_to=answer["id"])
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "Answer: 20" in ganitra[0]["body"]


def test_followup_explain_bare_right_after_answer(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "samjhao")
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "Answer: 20" in ganitra[0]["body"]


def test_followup_explain_with_name_after_answer(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "Ganitra, samjhao")
    assert err is None
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_followup_redo_by_reply_to_correction_note(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    question, _answer = _ask_and_answer(gid, a_id)
    _p, notes, err = study_groups.post_message(
        gid, b_id, "jawab 25 hai", reply_to=question["id"])
    assert err is None and len(notes) == 1
    assert notes[0]["kind"] == "ganitra_note"
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "phir se karo", reply_to=notes[0]["id"])
    assert err is None
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_reply_to_ganitra_with_fresh_question_is_answered(
        app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _q, answer = _ask_and_answer(gid, a_id)
    _post, ganitra, err = study_groups.post_message(
        gid, b_id, "15 + 5 kitna hota hai?",
        reply_to=answer["id"])
    assert err is None
    assert len(ganitra) == 1 and "Answer: 20" in ganitra[0]["body"]


def test_bare_samjhao_after_member_chat_is_not_claimed(app, group_ab):
    gid, _owner, a_id, b_id = group_ab
    _ask_and_answer(gid, a_id)
    _p, g1, err = study_groups.post_message(
        gid, b_id, "kal match hai doston, sab aana")
    assert err is None and g1 == []
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "samjhao")
    assert err is None and ganitra == []
