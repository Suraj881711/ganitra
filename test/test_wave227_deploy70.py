"""Wave 227 — Deploy-70 live-failure regression tests.

Deploy-70 passed every pipeline-level test and the local
gate, then failed the LIVE check twice (fresh chats, after
a reload): the exact screenshot-case-5 question, asked
through the real chat, came back with the canned English
not-understood line ("I didn't understand that — type your
maths question a little clearly...").

Root cause (mechanism, proven locally in this file): the
question's only deterministic owner — the Wave 223
multipart gate, Family 5 included — sits deep inside
``solver.router._solve_question_uncached``, BEHIND the
expensive primary dispatch, and the whole uncached solve
runs under the router's 10-second wall-clock budget.  On
the CPU-throttled production host the primary dispatch on
the full messy string grinds past the budget, the solve
thread is cut, and ``solve_question`` returns the too-big
refusal.  Every later rescue pays the same death (the
hint retry, Wave 100's per-part sub-solves), the AI legs
were quota-exhausted, and the chain bottomed out at the
not-found line.  Locally, at full CPU, the identical solve
takes ~0.5 s — which is why every local probe passed.

The root fix (fallback.py, extending the Wave 125 hook):
when the primary result IS the budget refusal, the
fallback chain consults the strict deterministic gates —
``solve_wave226`` then ``solve_multipart223``, the
router's own order — once, before the bank.  Both are
strict full-shape gates (None on any doubt), and the
multipart gate's part-solves are small single asks with
their own budgets, so the question is settled without
re-paying the starved primary dispatch.

These tests are ROUTE-level (the Flask test client, the
exact routes + payload shape the chat page uses, chat_id
included) — the level the original wave's tests never
exercised for case 5.
"""
import json

import pytest

import fallback  # noqa: F401  (chain under test)
from solver import answer_cache
from solver import router as solver_router

CANNED = (
    "I didn't understand that",
    "Samajh nahi aaya",
    "समझ नहीं आया",
    "Answer not found",
)

CASE5 = ("Check the continuity of a function at x = 0 x=0. "
         "Differentiate y = x 2 sin x y=x2 sinx.")

LONG_PASTE = (
    "Q1. Find the area and perimeter of a rectangle whose "
    "length is 8 cm and breadth is 5 cm. Q2. Solve the "
    "equation 2x + 3 = 7 and find the value of x. Q3. What "
    "is the mean of the numbers 4, 8, 15, 16, 23 and 42? "
    "Q4. A shopkeeper buys a pen for 40 rupees and sells "
    "it for 50 rupees, find his profit percent. Q5. Find "
    "the simple interest on Rs 1000 at 5 percent per annum "
    "for 2 years and also find the total amount to be paid "
    "back at the end of the term with full steps shown "
    "clearly for the student reading.")


@pytest.fixture()
def client(tmp_path, monkeypatch):
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
        "name": "Wave227 Deploy70", "class": "12",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave227pass"})
    assert r.status_code == 302, r.status_code
    return c


def _fresh_chat(client):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    return r.get_json()["chat"]["id"]


def _solve_classic(client, question):
    chat_id = _fresh_chat(client)
    r = client.post("/api/solve", json={
        "question": question, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    return r.get_json()


def _assert_case5_answer(res):
    assert res.get("op") == "multipart227", res
    assert res.get("fallback_kind") != "not_found", res
    answer = str(res.get("answer") or "")
    assert "(a) Function not given" in answer, answer
    assert "x^2·cos(x) + 2·x·sin(x)" in answer, answer
    for bad in CANNED:
        assert bad not in answer, (bad, answer[:160])


def _clear_solve_caches():
    answer_cache.clear_cache()
    answer_cache.clear_negative_cache()
    answer_cache.clear_failure_cache()


def _throttle_primary(monkeypatch, needle_parts):
    """The throttled-host simulation: a solve whose text
    carries every needle gets an unmeetable budget (its
    primary dispatch is what starves on the tarpit host);
    every other solve — the rescue's small part-solves —
    keeps the real budget it would get in production."""
    orig = solver_router._solve_with_budget

    def _throttled(question, budget=10.0):
        text = str(question)
        if all(n in text for n in needle_parts):
            return orig(question, budget=0.05)
        return orig(question, budget=budget)

    monkeypatch.setattr(solver_router, "_solve_with_budget",
                        _throttled)


# ---------------------------------------------------------------------------
# Case 5 through the real routes (healthy host)
# ---------------------------------------------------------------------------

def test_case5_classic_route_with_chat_id(client):
    data = _solve_classic(client, CASE5)
    assert data["ok"] is True, data
    _assert_case5_answer(data["result"])


def test_case5_stream_route_final_event(client, monkeypatch):
    # The chat page prefers /api/solve/stream whenever the
    # server flag is on; its final event must carry the
    # same two-part answer the classic route serves.
    monkeypatch.setenv("GANITRA_AI_STREAM", "1")
    chat_id = _fresh_chat(client)
    r = client.post("/api/solve/stream", json={
        "question": CASE5, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    final = None
    for frame in r.get_data(as_text=True).split("\n\n"):
        for line in frame.split("\n"):
            if line.startswith("data:"):
                ev = json.loads(line[5:])
                if ev.get("type") == "final":
                    final = ev.get("payload") or {}
    assert final is not None, "no final event in stream"
    assert final["ok"] is True, final
    _assert_case5_answer(final["result"])


# ---------------------------------------------------------------------------
# The Deploy-70 mechanism: primary budget death must not
# sink the deterministic gates
# ---------------------------------------------------------------------------

def test_case5_route_survives_primary_budget_death(
        client, monkeypatch):
    _clear_solve_caches()
    _throttle_primary(monkeypatch,
                      ("continuity", "Differentiate"))
    data = _solve_classic(client, CASE5)
    assert data["ok"] is True, data
    # Before the fix this was exactly the live failure:
    # op "not_found" and the canned English line.
    _assert_case5_answer(data["result"])


def test_wave226_gate_route_survives_primary_budget_death(
        client, monkeypatch):
    # The second gate in the rescue hook: a Wave 226 shape
    # whose primary solve starved must still be served by
    # its strict gate, not the not-found line.
    _clear_solve_caches()
    _throttle_primary(monkeypatch, ("7!",))
    data = _solve_classic(client, "7! kitna hota hai")
    assert data["ok"] is True, data
    res = data["result"]
    assert str(res.get("answer")) == "5040", res
    assert res.get("fallback_kind") != "not_found", res


def test_bomb_route_is_not_rescued_into_a_fake_answer(
        client):
    # The rescue hook shares its trigger dict with the
    # pre-guard's genuine-bomb refusal; the strict gates
    # must decline it (None on any doubt) and the route
    # must never present an expansion as solved.
    _clear_solve_caches()
    data = _solve_classic(client, "expand (x+1)^3000")
    res = data.get("result") or {}
    assert res.get("op") != "multipart227", res
    assert res.get("op") != "multipart223", res
    answer = str(res.get("answer") or "")
    assert "x^3000" not in answer.replace(" ", ""), answer
    assert len(answer) < 2000, answer[:200]


# ---------------------------------------------------------------------------
# Case 6 re-verified at API level, with the chat_id the
# real chat sends (live check (b) was never run)
# ---------------------------------------------------------------------------

def test_case6_long_paste_route_with_chat_id(client):
    assert len(LONG_PASTE) > 500  # past the old line
    data = _solve_classic(client, LONG_PASTE)
    assert data["ok"] is True, data
    assert "bit long" not in str(data.get("message") or "")
    res = data["result"]
    assert res["op"] == "multipart_general", res
    answer = str(res["answer"])
    for bit in ("40", "x = 2", "18", "25%", "1100"):
        assert bit in answer, (bit, answer[:200])
