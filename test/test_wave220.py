"""Wave 220 — follow-up anchor restored from the saved thread.

Bug (live, 23 Nov 2026, Deploy-60/61 verification): in a real
browser, "galat hai, phir se karo" and "samjhao" fell to the
generic lines even inside a SINGLE chat that was never left,
while the identical sequence passed over curl and in the test
client. The follow-up layers (Wave 96 doubt, Wave 214 human
brain, Wave 122 chips) all read session["last_result"] /
session["last_question"] from the client-side cookie, and in
the browser that state silently stops arriving (the Wave-46
audit met the same family: an over-limit session cookie is
dropped by the browser without a word). The chat thread,
though, is saved server-side on every turn, so api_solve now
rebuilds the anchor from the thread (owner's own chat only)
whenever the session holds no usable anchor for the chat.

These tests simulate the browser failure exactly: solve, save
the thread the way the page does (PUT /api/chats/<id>), then
WIPE the anchor keys from the session while staying logged
in, and ask the follow-up.
"""
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY", raising=False)
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _signup(client, name="Wave220 Check"):
    r = client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave220pass"})
    assert r.status_code == 302, r.status_code


def _solve(client, question, chat_id=None):
    body = {"question": question}
    if chat_id is not None:
        body["chat_id"] = chat_id
    r = client.post("/api/solve", json=body)
    return r.get_json()


def _new_chat(client):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    return r.get_json()["chat"]["id"]


def _save_thread(client, chat_id, messages):
    r = client.put(f"/api/chats/{chat_id}", json={"messages": messages})
    assert r.status_code == 200, r.status_code


def _bot_record(question, payload):
    data = dict(payload)
    data["_q"] = question
    return {"role": "bot", "data": data}


def _wipe_anchor(client):
    """The browser failure: logged in, but every follow-up
    anchor key is gone from the session."""
    with client.session_transaction() as sess:
        assert sess.get("user_id"), "test must stay logged in"
        for key in ("last_question", "last_result", "anchor_by_chat",
                    "last_result_chat", "ctx_turns", "doubt_step",
                    "history"):
            sess.pop(key, None)


def test_redo_restored_from_saved_thread(client):
    _signup(client)
    chat_id = _new_chat(client)
    first = _solve(client, "15% of 200", chat_id)
    assert first["result"]["answer"] == "30"
    _save_thread(client, chat_id, [
        {"role": "user", "text": "15% of 200"},
        _bot_record("15% of 200", first),
    ])
    _wipe_anchor(client)
    redo = _solve(client, "galat hai, phir se karo", chat_id)
    assert redo["result"]["answer"] == "30", redo
    assert redo.get("intro"), redo


def test_samjhao_restored_from_saved_thread(client):
    _signup(client)
    chat_id = _new_chat(client)
    first = _solve(client, "347 + 258", chat_id)
    assert first["result"]["answer"] == "605"
    _save_thread(client, chat_id, [
        {"role": "user", "text": "347 + 258"},
        _bot_record("347 + 258", first),
    ])
    _wipe_anchor(client)
    ex = _solve(client, "samjhao", chat_id)
    assert "605" in str(ex["result"]["answer"]), ex


def test_probe_a_sequence_end_to_end(client):
    """The exact live Probe-A sequence (23 Nov 2026) with the
    anchor wiped before EACH follow-up, as the browser lost
    it every time."""
    _signup(client)
    chat_id = _new_chat(client)
    thread = []
    a = _solve(client, "15% of 200", chat_id)
    assert a["result"]["answer"] == "30"
    thread += [{"role": "user", "text": "15% of 200"},
               _bot_record("15% of 200", a)]
    _save_thread(client, chat_id, thread)
    _wipe_anchor(client)
    b = _solve(client, "galat hai, phir se karo", chat_id)
    assert b["result"]["answer"] == "30", b
    thread += [{"role": "user", "text": "galat hai, phir se karo"},
               _bot_record("galat hai, phir se karo", b)]
    c = _solve(client, "347 + 258", chat_id)
    assert c["result"]["answer"] == "605"
    thread += [{"role": "user", "text": "347 + 258"},
               _bot_record("347 + 258", c)]
    _save_thread(client, chat_id, thread)
    _wipe_anchor(client)
    d = _solve(client, "samjhao", chat_id)
    assert "605" in str(d["result"]["answer"]), d


def test_other_users_chat_never_anchors(client):
    _signup(client, "Owner Wave220")
    chat_id = _new_chat(client)
    first = _solve(client, "15% of 200", chat_id)
    _save_thread(client, chat_id, [
        {"role": "user", "text": "15% of 200"},
        _bot_record("15% of 200", first),
    ])
    # A second student, logged in on their own account, asks a
    # follow-up pointing at the FIRST student's chat id.
    from app import create_app
    other = client  # same client factory pattern as wave213
    other.get("/logout")
    _signup(other, "Other Wave220")
    _wipe_anchor(other)
    redo = _solve(other, "galat hai, phir se karo", chat_id)
    assert (redo.get("result") or {}).get("answer") != "30", redo


def test_plain_last_turn_does_not_anchor(client):
    """If the thread's last real bot turn is a plain guard
    line, there is nothing honest to explain — the follow-up
    must NOT reach back past it to an older solve (mirrors
    the session behaviour guarded by result_is_plain)."""
    _signup(client)
    chat_id = _new_chat(client)
    first = _solve(client, "15% of 200", chat_id)
    assert first["result"]["answer"] == "30"
    plain_payload = {"ok": True, "result": {
        "answer": "Main sirf maths me madad karta hoon.",
        "plain": True}}
    _save_thread(client, chat_id, [
        {"role": "user", "text": "15% of 200"},
        _bot_record("15% of 200", first),
        {"role": "user", "text": "photosynthesis kya hota hai"},
        _bot_record("photosynthesis kya hota hai", plain_payload),
    ])
    _wipe_anchor(client)
    redo = _solve(client, "galat hai, phir se karo", chat_id)
    assert (redo.get("result") or {}).get("answer") != "30", redo


def test_healthy_session_unaffected(client):
    """No wipe: the ordinary in-session follow-up still works
    exactly as Waves 214/216 pinned it."""
    _signup(client)
    chat_id = _new_chat(client)
    assert _solve(client, "15% of 200", chat_id)[
        "result"]["answer"] == "30"
    redo = _solve(client, "galat hai, phir se karo", chat_id)
    assert redo["result"]["answer"] == "30", redo
