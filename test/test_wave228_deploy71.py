"""Wave 228, Deploy-71 fix — the group name-call live failure.

Deploy-71 check (d) failed TWICE, identically: in a study
group, "Ganitra, Bharat ki rajdhani kya hai?" earned the
canned not-found line ("Samajh nahi aaya — maths ka sawal
thoda saaf likh kar bhejo...") instead of a real answer.

ROOT CAUSE (probe-pinned, see the wave228 packet's
Deploy-71 section): the Wave 228 route DID fire and DID
call fallback._verified_ai_answer — but the three AI legs
share ONE prompt (gemini_fallback._PROMPT) whose rules
order the model to reply with exactly the word NOT_MATHS
to any non-maths question, and _shape_result maps that
sentinel to None. So a HEALTHY leg can never answer a
general question through that chain: the legs were not
dead, they were refusing by design. The Wave 228 tests
could not see it — they stubbed fallback._gemini_answer
with a double that happily answers capital questions, a
shape the real legs cannot produce under the shared
prompt; and for the Hindi form the stub let the NATIVE
chain serve the answer, so the new route was never the
thing being exercised.

THE FIX, pinned here at the live shape (the provider is
stubbed at the HTTP layer, faithful to the real prompt —
it replies NOT_MATHS when the maths prompt's rule is in
front of it and a real answer otherwise):
- the legs take a `general` prompt variant (any topic, no
  NOT_MATHS rule), threaded fallback._verified_ai_answer
  -> _gemini/_groq/_openrouter_answer -> try_*_answer ->
  _build_prompt, riding ONLY as a keyword when on (the
  Wave 136 seam discipline), and groups._named_answer
  asks with general=True;
- when the legs genuinely have nothing for a name-called
  question, the group posts a kind honest line ("jawab
  abhi la nahi paya — thodi der me phir se puchna") instead
  of the not-found clarification line, which falsely tells
  the student their clear question was unclear. The
  maths-only guard line (the nonmaths outcome) stands.

Isolation follows the Wave-228 pattern: throwaway DB via
GANITRA_DB_PATH, answer cache cleared around each test.
"""
import pytest

import fallback
import gemini_fallback
import groq_fallback
import groups as study_groups
import openrouter_fallback
import solver.answer_cache as cache

MSG_HI = "Ganitra, Bharat ki rajdhani kya hai?"
MSG_EN = "Ganitra, what is the capital of India?"
CANNED = "Samajh nahi aaya"
HONEST_MARK = "phir se puchna"


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


# ---------------------------------------------------------------------------
# The prompt-faithful provider: a HEALTHY Gemini. It obeys
# the prompt it is actually given — NOT_MATHS when the
# maths prompt's rule is in front of it (what the real
# model does with a GK question), a real answer otherwise.
# ---------------------------------------------------------------------------

def _faithful_gemini(monkeypatch):
    seen = []

    def fake_post_json(url, payload, api_key, timeout):
        text = payload["contents"][0]["parts"][0]["text"]
        seen.append(text)
        if "NOT_MATHS" in text:
            reply = "NOT_MATHS"
        else:
            reply = ("Bharat ki rajdhani New Delhi hai.\n"
                     "Answer: New Delhi")
        return {"candidates": [{
            "content": {"parts": [{"text": reply}]},
            "finishReason": "STOP"}]}

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json",
                        fake_post_json)
    return seen


def _faithful_openai_style(module, env_key, monkeypatch):
    """The same faithful provider for the OpenAI-shaped
    legs (Groq / OpenRouter)."""
    seen = []

    def fake_post_json(url, payload, api_key, timeout):
        text = payload["messages"][0]["content"]
        seen.append(text)
        if "NOT_MATHS" in text:
            reply = "NOT_MATHS"
        else:
            reply = ("Bharat ki rajdhani New Delhi hai.\n"
                     "Answer: New Delhi")
        return {"choices": [{
            "message": {"content": reply},
            "finish_reason": "stop"}]}

    monkeypatch.setenv(env_key, "test-key")
    monkeypatch.setattr(module, "_post_json", fake_post_json)
    return seen


@pytest.fixture()
def dead_legs(monkeypatch):
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


@pytest.fixture()
def raising_legs(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("provider down / quota error")
    monkeypatch.setattr(fallback, "_gemini_answer", boom)
    monkeypatch.setattr(fallback, "_groq_answer", boom)
    monkeypatch.setattr(fallback, "_openrouter_answer", boom)


# ---------------------------------------------------------------------------
# (i) With a working leg, the name-called general question
# is answered — at the LIVE shape, not the seam-stub shape.
# ---------------------------------------------------------------------------

def test_named_gk_hindi_answered_live_shape(
        app, group_ab, monkeypatch):
    seen = _faithful_gemini(monkeypatch)
    gid, _owner, a_id, _b = group_ab
    post, ganitra, err = study_groups.post_message(
        gid, a_id, MSG_HI)
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "New Delhi" in ganitra[0]["body"]
    assert CANNED not in ganitra[0]["body"]
    # A general question is not dressed up as a maths
    # question post.
    assert post["kind"] == "chat"
    # The route really reached the provider with the
    # GENERAL prompt (no NOT_MATHS rule) — the native
    # chain's own call still carried the maths prompt.
    assert any("NOT_MATHS" not in p for p in seen)
    assert any("NOT_MATHS" in p for p in seen)


def test_named_gk_english_answered_live_shape(
        app, group_ab, monkeypatch):
    # The guard-caught form: the native chain refuses it
    # with the maths-only guard, so ONLY the name-call
    # route (general prompt) can answer it.
    _faithful_gemini(monkeypatch)
    gid, _owner, a_id, _b = group_ab
    post, ganitra, err = study_groups.post_message(
        gid, a_id, MSG_EN)
    assert err is None
    assert len(ganitra) == 1 and ganitra[0]["kind"] == "ganitra"
    assert "New Delhi" in ganitra[0]["body"]
    assert "only solves Maths" not in ganitra[0]["body"]
    assert post["kind"] == "chat"


def test_named_gk_via_group_http_route(
        app, trio, group_ab, monkeypatch):
    _faithful_gemini(monkeypatch)
    _owner, a, _b = trio
    gid, _o, _a, _b_id = group_ab
    r = a.post(f"/groups/{gid}/post", data={"text": MSG_HI})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "New Delhi" in body
    assert CANNED not in body


def test_general_prompt_shape():
    maths = gemini_fallback._build_prompt(
        "Bharat ki rajdhani kya hai?")
    general = gemini_fallback._build_prompt(
        "Bharat ki rajdhani kya hai?", general=True)
    # The maths prompt keeps its NOT_MATHS discipline
    # byte-for-byte in spirit: the rule is still there.
    assert "NOT_MATHS" in maths
    # The general prompt has no such rule — any topic.
    assert "NOT_MATHS" not in general
    assert "ANY topic" in general


def test_maths_chain_still_gets_no_gk_answer(monkeypatch):
    # Without general=True the verified chain is exactly as
    # before: the faithful provider refuses the GK question
    # under the maths prompt and the chain returns None.
    _faithful_gemini(monkeypatch)
    assert fallback._verified_ai_answer(
        "Bharat ki rajdhani kya hai?", True, None) is None
    # And WITH general=True the same healthy provider
    # answers through the same verification gate.
    res = fallback._verified_ai_answer(
        "Bharat ki rajdhani kya hai?", True, None,
        general=True)
    assert res is not None
    assert "New Delhi" in str(res.get("answer"))


def test_groq_and_openrouter_thread_general(monkeypatch):
    # All three legs share the prompt builder; pin the
    # threading on the other two as well.
    _faithful_openai_style(groq_fallback,
                           "GANITRA_GROQ_API_KEY", monkeypatch)
    _faithful_openai_style(openrouter_fallback,
                           "GANITRA_OPENROUTER_API_KEY",
                           monkeypatch)
    q = "Bharat ki rajdhani kya hai?"
    assert groq_fallback.try_groq_answer(q) is None
    res = groq_fallback.try_groq_answer(q, general=True)
    assert res is not None
    assert "New Delhi" in str(res.get("answer"))
    assert openrouter_fallback.try_openrouter_answer(
        q) is None
    res = openrouter_fallback.try_openrouter_answer(
        q, general=True)
    assert res is not None
    assert "New Delhi" in str(res.get("answer"))


# ---------------------------------------------------------------------------
# (ii) Legs genuinely have nothing -> the kind honest line,
# never the canned "saaf likh kar bhejo" line.
# ---------------------------------------------------------------------------

def test_named_gk_legs_dead_honest_line(app, group_ab,
                                       dead_legs):
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, MSG_HI)
    assert err is None
    assert len(ganitra) == 1
    assert ganitra[0]["kind"] == "ganitra_note"
    body = ganitra[0]["body"]
    assert HONEST_MARK in body
    assert CANNED not in body
    assert "saaf likh" not in body
    assert "New Delhi" not in body


def test_named_gk_legs_raise_honest_line(app, group_ab,
                                         raising_legs):
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, MSG_HI)
    assert err is None
    assert len(ganitra) == 1
    assert ganitra[0]["kind"] == "ganitra_note"
    assert HONEST_MARK in ganitra[0]["body"]
    assert CANNED not in ganitra[0]["body"]


def test_named_english_gk_legs_dead_keeps_maths_only_line(
        app, group_ab, dead_legs):
    # The standing maths-only guard line is a DIFFERENT
    # outcome (kind "nonmaths") and is NOT replaced by the
    # honest line — the Wave 228 pin stands.
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, MSG_EN)
    assert err is None
    assert len(ganitra) == 1
    assert ganitra[0]["kind"] == "ganitra_note"
    assert "only solves Maths" in ganitra[0]["body"]
    assert HONEST_MARK not in ganitra[0]["body"]


def test_unnamed_gk_in_group_stays_silent(
        app, group_ab, monkeypatch):
    # No name call -> Ganitra does not butt in, exactly as
    # before (the faithful provider is healthy; the native
    # chain's plain outcome for unaddressed chat is simply
    # not posted).
    _faithful_gemini(monkeypatch)
    gid, _owner, a_id, _b = group_ab
    _post, ganitra, err = study_groups.post_message(
        gid, a_id, "Bharat ki rajdhani kya hai?")
    assert err is None
    assert ganitra == []
