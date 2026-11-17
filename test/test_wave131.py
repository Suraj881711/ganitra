"""Wave 131: REAL streaming — feasibility + the AI-leg
stream, transport only.

Feasibility verdict (full evidence in
ganitra-wave131-notes.md): progressive delivery through
PythonAnywhere's free-tier stack is UNVERIFIABLE until a
live deploy (PA's own Buffering help page prescribes the
X-Accel-Buffering: no header + newline-terminated yields,
which this build follows exactly); progressive delivery IS
proven on the local Flask stack. So the build is a
flag-gated prototype (GANITRA_AI_STREAM, default OFF): with
the flag off the app behaves exactly as before; with it on,
/api/solve/stream delivers the AI fallback leg's pieces as
the provider produces them, and the classic /api/solve
remains the client's automatic fallback on ANY failure.

Coordination (parent, 17 Nov 2026): Wave 132 owns the AI
prompt text and the shaping-path normalizer; Wave 131 is
TRANSPORT-ONLY. Every equality test below therefore runs
against FIXTURES defined in this file (a fixed reply text
fed through both the classic _post_json path and the
streamed _post_sse path) — never against the live prompt
or normalizer wording — so the two waves cannot produce
false merge conflicts.

Pinned here:
- per provider, the streamed assembly, passed through the
  SAME shaping function, is byte-identical to the
  non-streamed result for the same fixture reply;
- the Wave-119 truncation guard holds mid-stream: a leg
  cut at MAX_TOKENS / "length" is discarded (a reset is
  emitted for the text already shown) and the chain moves
  on; if every leg truncates, nothing cut is served;
- a mid-stream transport failure resets and the next leg
  serves;
- with every leg failing, the stream endpoint serves the
  honest not-found outcome, never a partial AI answer;
- the flag off: both stream endpoints 404 and the chat
  page renders AI_STREAM = false; flag on: the page
  renders true;
- a solver-answered question streams as exactly ONE final
  event (no fake token drip for a 0.13 s computation);
- the stream response carries text/event-stream +
  X-Accel-Buffering: no;
- the stream-commit endpoint performs the session writes
  a streamed solve cannot do inline (the response's
  session cookie is fixed before the first chunk leaves).
"""
import json

import pytest

import ai_stream
import gemini_fallback
import groq_fallback
import openrouter_fallback
import solver.answer_cache as cache


@pytest.fixture(autouse=True)
def _clean_caches():
    # Same isolation as test_wave119: the negative cache is
    # process-global and these tests mock the AI transport
    # per test for a shared probe question.
    cache.clear_cache()
    yield
    cache.clear_cache()


# Deploy-27 merge: the original EN probe is now solved
# DETERMINISTICALLY by Wave 125's area-between-curves
# solver, so it never reaches the AI legs these tests
# exercise. The Hinglish phrasing of the same question
# still routes to the legs (verified in the merge tree);
# the stub replies below are unchanged.
PROBE_Q = "Area between curve y = x^2 and line y = x nikalo"

# The fixture reply (identical wording to test_wave119's
# recorded complete answer): a multi-step integral working
# ending in a fraction. Streamed in uneven pieces below.
FULL_TEXT = (
    "y = x^2\n"
    "y = x\n"
    "x^2 = x\n"
    "x^2 - x = 0\n"
    "x(x - 1) = 0\n"
    "x = 0 and x = 1\n"
    "Area = integral from 0 to 1 of (x - x^2) dx\n"
    "Area = [x^2/2 - x^3/3] from 0 to 1\n"
    "Area = (1/2 - 1/3) - (0 - 0)\n"
    "Area = 1/2 - 1/3\n"
    "Area = 1/6\n"
    "Answer: 1/6 square units")

PIECES = [FULL_TEXT[:17], FULL_TEXT[17:60], FULL_TEXT[60:61],
          FULL_TEXT[61:150], FULL_TEXT[150:]]


class _FakeSSE:
    """A stand-in streamed HTTP response: iterating it
    yields the `data: ...` byte lines a provider's SSE
    endpoint would send. fail_after=N raises mid-stream
    after N lines, simulating a broken connection."""

    def __init__(self, payloads, fail_after=None):
        self._lines = [
            ("data: " + json.dumps(p) + "\n").encode("utf-8")
            for p in payloads]
        self._fail_after = fail_after

    def __iter__(self):
        for i, line in enumerate(self._lines):
            if self._fail_after is not None and i == self._fail_after:
                raise ConnectionError("stream broke mid-reply")
            yield line

    def close(self):
        pass


def _gemini_stream_payloads(pieces, finish_reason):
    out = [{"candidates": [{"content": {"parts": [{"text": p}]}}]}
           for p in pieces]
    out[-1]["candidates"][0]["finishReason"] = finish_reason
    return out


def _chat_stream_payloads(pieces, finish_reason):
    out = [{"choices": [{"delta": {"content": p},
                         "finish_reason": None}]}
           for p in pieces]
    out[-1]["choices"][0]["finish_reason"] = finish_reason
    return out


def _gemini_payload(text, finish_reason):
    return {"candidates": [{
        "content": {"parts": [{"text": text}]},
        "finishReason": finish_reason}]}


def _chat_payload(text, finish_reason):
    return {"choices": [{
        "message": {"content": text},
        "finish_reason": finish_reason}]}


def _drain(gen):
    """Run a provider stream generator to completion;
    returns (yielded pieces, (status, shaped))."""
    pieces = []
    while True:
        try:
            pieces.append(next(gen))
        except StopIteration as stop:
            return pieces, stop.value


# ---------------------------------------------------------------------------
# Stream assembly == non-stream assembly (fixtures only)
# ---------------------------------------------------------------------------

def test_gemini_stream_matches_nonstream(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _gemini_payload(FULL_TEXT, "STOP"))
    classic = gemini_fallback.try_gemini_answer(PROBE_Q)
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda url, payload, api_key, timeout:
            _FakeSSE(_gemini_stream_payloads(PIECES, "STOP")))
    pieces, (status, shaped) = _drain(
        gemini_fallback.stream_gemini_answer(PROBE_Q))
    assert status == "ok"
    # The raw reply is reassembled exactly...
    assert "".join(
        p for p in pieces if isinstance(p, str)) == FULL_TEXT
    # ...and the shaped result is byte-identical to the
    # classic path's for the same reply.
    assert shaped == classic
    assert shaped["answer"] == "1/6 square units"


def test_groq_stream_matches_nonstream(monkeypatch):
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(FULL_TEXT, "stop"))
    classic = groq_fallback.try_groq_answer(PROBE_Q)
    monkeypatch.setattr(
        groq_fallback, "_post_sse",
        lambda url, payload, api_key, timeout:
            _FakeSSE(_chat_stream_payloads(PIECES, "stop")))
    pieces, (status, shaped) = _drain(
        groq_fallback.stream_groq_answer(PROBE_Q))
    assert status == "ok"
    assert "".join(
        p for p in pieces if isinstance(p, str)) == FULL_TEXT
    assert shaped == classic


def test_openrouter_stream_matches_nonstream(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(FULL_TEXT, "stop"))
    classic = openrouter_fallback.try_openrouter_answer(PROBE_Q)
    monkeypatch.setattr(
        openrouter_fallback, "_post_sse",
        lambda url, payload, api_key, timeout:
            _FakeSSE(_chat_stream_payloads(PIECES, "stop")))
    pieces, (status, shaped) = _drain(
        openrouter_fallback.stream_openrouter_answer(PROBE_Q))
    assert status == "ok"
    assert "".join(
        p for p in pieces if isinstance(p, str)) == FULL_TEXT
    assert shaped == classic


def test_stream_requests_the_provider_stream_mode(monkeypatch):
    seen = {}

    def fake_sse(url, payload, api_key, timeout):
        seen["url"] = url
        seen["payload"] = payload
        return _FakeSSE(_gemini_stream_payloads(PIECES, "STOP"))

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_sse", fake_sse)
    _drain(gemini_fallback.stream_gemini_answer(PROBE_Q))
    assert "streamGenerateContent" in seen["url"]
    assert "alt=sse" in seen["url"]
    # The Wave-119 budget rides the streamed request too.
    cap = seen["payload"]["generationConfig"]["maxOutputTokens"]
    assert cap == gemini_fallback.MAX_OUTPUT_TOKENS == 8192


# ---------------------------------------------------------------------------
# The Wave-119 truncation guard, mid-stream
# ---------------------------------------------------------------------------

def test_gemini_stream_truncated_primary_moves_on(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")

    def dispatch(url, payload, api_key, timeout):
        if "gemini-3-flash-preview" in url:
            return _FakeSSE(_gemini_stream_payloads(
                ["partial ans"], "MAX_TOKENS"))
        return _FakeSSE(_gemini_stream_payloads(PIECES, "STOP"))

    monkeypatch.setattr(gemini_fallback, "_post_sse", dispatch)
    pieces, (status, shaped) = _drain(
        gemini_fallback.stream_gemini_answer(PROBE_Q))
    assert status == "ok"
    assert shaped["answer"] == "1/6 square units"
    # The cut leg HAD shown text, so a reset separates it
    # from the good leg's pieces.
    assert gemini_fallback.STREAM_RESET in pieces


def test_gemini_stream_all_truncated_serves_nothing(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda url, payload, api_key, timeout: _FakeSSE(
            _gemini_stream_payloads(["cut off"], "MAX_TOKENS")))
    _pieces, (status, shaped) = _drain(
        gemini_fallback.stream_gemini_answer(PROBE_Q))
    assert status == "truncated"
    assert shaped is None


def test_groq_stream_length_finish_is_truncated(monkeypatch):
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_fallback, "_post_sse",
        lambda url, payload, api_key, timeout: _FakeSSE(
            _chat_stream_payloads(["cut off"], "length")))
    _pieces, (status, shaped) = _drain(
        groq_fallback.stream_groq_answer(PROBE_Q))
    assert status == "truncated"
    assert shaped is None


def test_stream_no_key_is_unavailable(monkeypatch):
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    _pieces, (status, shaped) = _drain(
        gemini_fallback.stream_gemini_answer(PROBE_Q))
    assert status == "unavailable"
    assert shaped is None


# ---------------------------------------------------------------------------
# The orchestrator: leg order, reset on failure, honest end
# ---------------------------------------------------------------------------

def _mock_gemini_broken_groq_good(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda url, payload, api_key, timeout: _FakeSSE(
            _gemini_stream_payloads(PIECES, "STOP"), fail_after=2))
    monkeypatch.setattr(
        groq_fallback, "_post_sse",
        lambda url, payload, api_key, timeout: _FakeSSE(
            _chat_stream_payloads(PIECES, "stop")))


def test_orchestrator_mid_stream_failure_next_leg(monkeypatch):
    _mock_gemini_broken_groq_good(monkeypatch)
    events = []
    gen = ai_stream.stream_ai_events(PROBE_Q, False)
    while True:
        try:
            events.append(next(gen))
        except StopIteration as stop:
            result = stop.value
            break
    assert result is not None
    assert result["answer"] == "1/6 square units"
    kinds = [e["type"] for e in events]
    # Gemini's two shown pieces, then a reset, then Groq's.
    assert kinds[0] == "delta" and "reset" in kinds
    shown_after_reset = "".join(
        e["text"] for e in events[kinds.index("reset") + 1:]
        if e["type"] == "delta")
    assert shown_after_reset == FULL_TEXT


def test_orchestrator_all_legs_down_returns_none(monkeypatch):
    for env in ("GANITRA_GEMINI_API_KEY", "GANITRA_GROQ_API_KEY",
                "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(env, raising=False)
    gen = ai_stream.stream_ai_events(PROBE_Q, False)
    with pytest.raises(StopIteration) as exc:
        while True:
            next(gen)
    assert exc.value.value is None


# ---------------------------------------------------------------------------
# The endpoints (Flask test client)
# ---------------------------------------------------------------------------

def _client(tmp_path, monkeypatch, stream_on):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    if stream_on:
        monkeypatch.setenv("GANITRA_AI_STREAM", "1")
    else:
        monkeypatch.delenv("GANITRA_AI_STREAM", raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W131 Tester", "class": "10", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w131-test-pass"})
    return client


def _events(resp):
    body = resp.get_data(as_text=True)
    out = []
    for frame in body.split("\n\n"):
        frame = frame.strip()
        if frame.startswith("data:"):
            out.append(json.loads(frame[len("data:"):]))
    return out


def test_flag_off_endpoints_404_and_page_disarmed(
        tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=False)
    assert ai_stream.stream_enabled() is False
    resp = client.post("/api/solve/stream",
                       json={"question": "2 + 2"})
    assert resp.status_code == 404
    resp = client.post("/api/solve/stream-commit",
                       json={"question": "2 + 2",
                             "result": {"answer": "4"}})
    assert resp.status_code == 404
    page = client.get("/").get_data(as_text=True)
    assert "var AI_STREAM = false" in page


def test_flag_on_page_arms_streaming(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=True)
    page = client.get("/").get_data(as_text=True)
    assert "var AI_STREAM = true" in page
    assert "style.css?v=48" in page


def test_solver_question_streams_as_single_final(
        tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=True)
    resp = client.post(
        "/api/solve/stream",
        json={"question": "Find the HCF of 12 and 18"})
    assert resp.status_code == 200
    assert resp.headers["X-Accel-Buffering"] == "no"
    assert "text/event-stream" in resp.headers["Content-Type"]
    events = _events(resp)
    # Nothing fake: a sub-second deterministic answer is one
    # final event, zero delta events.
    assert [e["type"] for e in events] == ["final"]
    payload = events[0]["payload"]
    assert payload["ok"] is True
    assert payload["result"]["answer"] == "6"
    assert "commit_required" not in events[0]


def test_stream_endpoint_ai_answer_end_to_end(
        tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=True)
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda url, payload, api_key, timeout: _FakeSSE(
            _gemini_stream_payloads(PIECES, "STOP")))
    resp = client.post("/api/solve/stream",
                       json={"question": PROBE_Q})
    events = _events(resp)
    deltas = [e for e in events if e["type"] == "delta"]
    assert "".join(e["text"] for e in deltas) == FULL_TEXT
    final = events[-1]
    assert final["type"] == "final"
    assert final["commit_required"] is True
    payload = final["payload"]
    assert payload["ok"] is True
    assert payload["result"]["answer"] == "1/6 square units"
    # The session writes ride the commit call, exactly the
    # result the stream served.
    resp = client.post("/api/solve/stream-commit", json={
        "question": PROBE_Q, "result": payload["result"]})
    assert resp.get_json()["ok"] is True
    with client.session_transaction() as sess:
        assert sess["last_result"]["answer"] == "1/6 square units"
        assert sess["last_question"] == PROBE_Q
        assert sess["history"][0]["question"] == PROBE_Q


def test_stream_endpoint_all_legs_fail_honest_not_found(
        tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=True)
    for env in ("GANITRA_GEMINI_API_KEY", "GANITRA_GROQ_API_KEY",
                "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(env, raising=False)
    resp = client.post("/api/solve/stream",
                       json={"question": PROBE_Q})
    events = _events(resp)
    assert [e["type"] for e in events] == ["final"]
    payload = events[0]["payload"]
    assert payload["ok"] is True
    assert payload["result"]["fallback_kind"] == "not_found"


def test_stream_commit_rejects_bad_bodies(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, stream_on=True)
    resp = client.post("/api/solve/stream-commit",
                       json={"question": "", "result": {}})
    assert resp.status_code == 400
    resp = client.post("/api/solve/stream-commit",
                       json={"question": "2 + 2", "result": {}})
    assert resp.status_code == 400


def test_classic_path_untouched_by_the_flag(
        tmp_path, monkeypatch):
    # Flag ON must not change /api/solve itself.
    client = _client(tmp_path, monkeypatch, stream_on=True)
    resp = client.post(
        "/api/solve", json={"question": "Find the HCF of 12 and 18"})
    data = resp.get_json()
    assert data["ok"] is True
    assert data["result"]["answer"] == "6"
