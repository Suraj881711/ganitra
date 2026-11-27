"""Wave 227 — Deploy-70 check (b) regression tests.

Deploy-70's fix went live and the OCR multipart case
passed, but live check (b) came back PARTIAL twice (fresh
chats, identical): pasting a 541-char set of five numbered
questions returned ONLY the circle part's answer (154 cm²,
with working) — nothing for the other four, and the circle
figure even labelled the radius "7 km" although the
question said 7 cm.

Root cause (mechanism, proven locally in this file): the
paste was never split at all. split_general's numbered
family (_split_gen_numbered) only accepts a "2)" marker
when the text before it ends in ".", ";", ":", a newline or
"।" — but in a pasted set the parts themselves are
questions, so the markers after parts 1 and 4 follow a
"?", were discarded as mid-sentence numbers, and the
consecutive run from 1 broke (hits kept: 1, 3, 4 — run
length 1). No splitter owned the set, so
general_multipart_result returned None in BOTH fallback
branches. The primary, meanwhile, returns the circle
fragment as a REAL whole-question answer — on a healthy
host via the intent dispatch's mensuration claim on the
full text, and under budget death via the Wave 77 core
pass solving the filler-stripped whole — and the chain's
designed defence against exactly that fragment (Wave
100/141's multipart_preferred override) was dead because
the split was. The fragment stood, with a figure whose
unit came from _unit()'s whole-text majority vote: "7 cm"
vs the train's "120 km" tie 1-1, and the vote's set-order
tie-break served "km".

Fixes pinned here: _split_gen_numbered treats "?" as the
sentence boundary it is (multipart.py), and figures.py
takes the figure's unit from the dimension's own
neighbourhood (_dim_unit) before the whole-text vote.
"""
import pytest

import fallback  # noqa: F401  (chain under test)
from figures import figure_for
from multipart import split_general
from solver import answer_cache
from solver import router as solver_router
from solver.router import solve_question

PASTE = (
    "1) What is 15% of 200? 2) Solve 2x + 3 = 11. "
    "3) Find the area of a circle with radius 7 cm. "
    "4) What is the HCF of 12 and 18? 5) A train travels "
    "120 km in 2 hours, what is its speed? These are my "
    "homework questions from today's class and I have to "
    "submit the notebook tomorrow morning, so please "
    "solve all the questions given above one by one with "
    "full steps and proper working shown clearly for each "
    "one so that I can understand the method properly and "
    "copy them into my notebook neatly. It is from the "
    "exercise of my maths book chapter for this week.")

PART_ANSWERS = ("(1) 30", "(2) x = 4", "(3) 154 cm²",
                "(4) 6", "(5) 60 km/h")


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
        "name": "Wave227 Deploy70b", "class": "10",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave227pass"})
    assert r.status_code == 302, r.status_code
    return c


def _solve_classic(client, question):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    chat_id = r.get_json()["chat"]["id"]
    r = client.post("/api/solve", json={
        "question": question, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    return r.get_json()


def _assert_full_set(res):
    assert res.get("op") == "multipart_general", res
    answer = str(res.get("answer") or "")
    for bit in PART_ANSWERS:
        assert bit in answer, (bit, answer[:240])


def _clear_solve_caches():
    answer_cache.clear_cache()
    answer_cache.clear_negative_cache()
    answer_cache.clear_failure_cache()


def _throttle_primary(monkeypatch, needle_parts):
    """The Deploy-70 throttled-host simulation: a solve
    whose text carries every needle gets an unmeetable
    budget (its primary dispatch is what starves on the
    tarpit host); every other solve — the multipart
    layer's small part-solves — keeps the real budget."""
    orig = solver_router._solve_with_budget

    def _throttled(question, budget=10.0):
        text = str(question)
        if all(n in text for n in needle_parts):
            return orig(question, budget=0.05)
        return orig(question, budget=budget)

    monkeypatch.setattr(solver_router, "_solve_with_budget",
                        _throttled)


# ---------------------------------------------------------------------------
# The split itself: "?"-terminated parts are parts
# ---------------------------------------------------------------------------

def test_split_general_numbered_set_with_question_parts():
    assert len(PASTE) > 541  # the live paste's size class
    got = split_general(PASTE)
    assert got is not None
    _preamble, parts = got
    assert [label for label, _t in parts] == \
        ["1", "2", "3", "4", "5"]
    assert parts[0][1].startswith("What is 15% of 200")
    assert parts[2][1].startswith(
        "Find the area of a circle")
    assert parts[4][1].startswith("A train travels")


def test_numbered_splitter_still_refuses_decimals_and_prose():
    # The "?" boundary must not reopen the doors the
    # numbered family was built shut against: decimals are
    # not markers, and figure references in prose are not
    # a question set.
    assert split_general(
        "The length is 2.5 cm. Find the perimeter of a "
        "square of side 2.5 cm.") is None
    assert split_general(
        "Fig. 1. shows the set up. 2. is the second figure "
        "in the book.") is None
    assert split_general(
        "Solve 2x + 3 = 11. What is the value of x?") \
        is None


# ---------------------------------------------------------------------------
# The paste through the real route — healthy host and
# primary budget death (the two live failure conditions)
# ---------------------------------------------------------------------------

def test_numbered_paste_route_healthy_host(client):
    # Before the fix this returned op "area", answer
    # "154 cm²" — the circle fragment alone.
    data = _solve_classic(client, PASTE)
    assert data["ok"] is True, data
    _assert_full_set(data["result"])


def test_numbered_paste_route_survives_primary_budget_death(
        client, monkeypatch):
    _clear_solve_caches()
    _throttle_primary(monkeypatch,
                      ("15% of 200", "HCF of 12 and 18"))
    data = _solve_classic(client, PASTE)
    assert data["ok"] is True, data
    _assert_full_set(data["result"])


# ---------------------------------------------------------------------------
# The figure unit: the dimension's own unit, not the
# whole paste's loudest one
# ---------------------------------------------------------------------------

def test_circle_figure_unit_comes_from_its_own_dimension():
    _clear_solve_caches()
    frag = solve_question(PASTE)
    assert frag.get("op") == "area", frag
    fig = figure_for(PASTE, frag)
    assert fig is not None
    # "radius 7 cm" — never the train part's "120 km".
    assert fig["caption"] == "Circle: radius 7 cm", fig


def test_single_circle_question_route_unchanged(client):
    # The fragment serve itself is legitimate for a
    # genuinely single question — figure included.
    data = _solve_classic(
        client, "Find the area of a circle with radius 7 cm")
    assert data["ok"] is True, data
    res = data["result"]
    assert res.get("op") == "area", res
    assert str(res.get("answer")) == "154 cm²", res
    fig = res.get("figure") or {}
    assert fig.get("caption") == "Circle: radius 7 cm", res
