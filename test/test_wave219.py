"""Wave 219 — the STREAMED solve path must honour follow-ups.

Root cause (live Deploy-60 verification, 23 Nov 2026): the
chat page tries /api/solve/stream first when GANITRA_AI_STREAM
is on (it IS on in production). That endpoint was built as a
mirror of /api/solve in Wave 131 — before Waves 214/216
existed — so it never received them:

- no per-chat anchor restore (Wave 216),
- no human-brain follow-up block (Wave 214),
- its request body carried NO chat_id, and its session
  commits anchored every solve under "default".

So on the live site a typed "galat hai, phir se karo" or
"samjhao" fell through the stream path to the generic
clarify line, while the classic path (and every route test)
passed. Fix: the client sends chat_id on both stream calls;
the stream endpoint runs the same Wave 216 restore and the
same Wave 214 block as /api/solve (served as one final SSE
event), and both commit sites pass the chat key through.
"""
import json

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.setenv("GANITRA_AI_STREAM", "1")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _stream_solve(client, question, chat_id=None):
    body = {"question": question}
    if chat_id is not None:
        body["chat_id"] = chat_id
    r = client.post("/api/solve/stream", json=body)
    assert r.status_code == 200
    final = None
    for line in r.get_data(as_text=True).splitlines():
        if line.startswith("data:"):
            ev = json.loads(line[5:])
            if ev.get("type") == "final":
                final = ev["payload"]
    assert final is not None, "stream sent no final event"
    if final.get("commit_required"):
        client.post("/api/solve/stream-commit", json={
            "question": question, "result": final["result"],
            "chat_id": chat_id})
    return final["result"]


def test_stream_redo_anchors_to_own_chat(client):
    assert _stream_solve(client, "15% of 200", 101)["answer"] == "30"
    assert _stream_solve(client, "25 x 14", 202)["answer"] == "350"
    redo = _stream_solve(client, "galat hai, phir se karo", 101)
    assert redo["answer"] == "30"


def test_stream_samjhao_anchors_to_own_chat(client):
    _stream_solve(client, "347 + 258", 101)
    _stream_solve(client, "12 x 12", 202)
    ex = _stream_solve(client, "samjhao", 101)
    assert "605" in str(ex["answer"])


def test_stream_fresh_chat_has_no_foreign_anchor(client):
    _stream_solve(client, "25 x 14", 202)
    ex = _stream_solve(client, "samjhao", 303)
    assert "350" not in str(ex.get("answer") or "")


def test_stream_commit_anchors_to_its_chat(client):
    r = client.post("/api/solve/stream-commit", json={
        "question": "15% of 200",
        "result": {"answer": "30"},
        "chat_id": 777})
    assert r.get_json()["ok"] is True
    # A classic-path follow-up in that chat must now find the
    # anchor the streamed solve left behind.
    r = client.post("/api/solve", json={
        "question": "galat hai, phir se karo", "chat_id": 777})
    assert r.get_json()["result"]["answer"] == "30"
