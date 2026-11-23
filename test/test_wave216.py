"""Wave 216 — per-chat follow-up anchoring.

Bug (live, Deploy-58 verification, 23 Nov 2026): the session's
last_result is a single slot shared by every chat, so a solve
in one chat hijacked follow-ups typed in another — chat A's
"galat hai, phir se karo" re-solved chat B's 25x14=350 instead
of A's own 15% of 200=30, and "samjhao" explained the 350.
Fix: each chat's last solved question is anchored
(session["anchor_by_chat"]); when a request's chat owns a
different anchor than the current last_result, api_solve
restores this chat's anchor (silent re-solve) or clears the
slot for a chat that has solved nothing yet.
"""
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _solve(client, question, chat_id=None):
    body = {"question": question}
    if chat_id is not None:
        body["chat_id"] = chat_id
    r = client.post("/api/solve", json=body)
    return r.get_json()["result"]


def test_redo_anchors_to_own_chat_not_latest_overall(client):
    assert _solve(client, "15% of 200 kitna hoga?", 101)[
        "answer"] == "30"
    assert _solve(client, "25 x 14 kitna hoga?", 202)[
        "answer"] == "350"
    redo = _solve(client, "galat hai, phir se karo", 101)
    assert redo["answer"] == "30"


def test_samjhao_anchors_to_own_chat(client):
    _solve(client, "347 + 258", 101)
    _solve(client, "25 x 14 kitna hoga?", 202)
    ex = _solve(client, "samjhao", 101)
    assert "605" in str(ex["answer"])


def test_fresh_chat_has_no_foreign_anchor(client):
    _solve(client, "25 x 14 kitna hoga?", 202)
    ex = _solve(client, "samjhao", 303)
    assert "350" not in str(ex.get("answer") or "")


def test_single_chat_followups_unchanged(client):
    assert _solve(client, "15% of 200 kitna hoga?")[
        "answer"] == "30"
    assert _solve(client, "galat hai, phir se karo")[
        "answer"] == "30"
