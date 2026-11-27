"""Wave 227 — phase-2 root fixes (Suraj's screenshot cases
5 and 6 + the ChatGPT code audit's BUG-004/005/007/008 and
the external audit's DoS row, all 27 Nov 2026):

1. SCREENSHOT CASE 5 — a multipart question whose text was
   DOUBLED by OCR ("Check the continuity of a function at
   x = 0 x=0. Differentiate y = x 2 sin x y=x2 sinx.") died
   on the canned "I didn't understand".  The parts are now
   de-duplicated, the OCR power spelling ("x 2" / "x2" for
   x^2) is repaired, the parts are split and solved
   part-wise — and the part that is genuinely incomplete
   (a continuity check naming NO function) gets a plain
   note saying exactly what is missing, while the complete
   part is still solved.  Never the canned line.

2. SCREENSHOT CASE 6 — a pasted paper over the old
   500-char line was REJECTED with "keep it under about
   500 characters".  Long questions are no longer refused:
   they flow into the solve, whose multipart layer splits
   them and solves them part-wise.  Only an absurd payload
   past the hard ceiling keeps the too-long reply.

3. BUG-004 — deep_solve._fmt truncated fractions with
   denominator > 100 to 4 decimals with no approximation
   mark (1/101 -> "0.0099").  Fractions stay exact now;
   only a monster denominator becomes a decimal, marked ≈.

4. BUG-005 — deep_solve._NUM_RE captured no sign, so -5
   was parsed as 5 (and a claimed "x = -5" verified as 5).
   Signed parsing now, with the binary-minus shapes
   ("5-3", "x-3", "5 -3") still reading as subtraction.

5. BUG-007 — verify_all's single-substring expectations
   passed INCOMPLETE solution sets ("x^2 - 5x + 6 = 0"
   expected only "x = 2"; a missing root x = 3 still
   passed).  Set-valued samples now require EVERY member.

6. BUG-008 + DoS — every timed-out solve used to leave a
   daemon thread burning CPU forever, threads piling up
   without bound, and /api/solve had no rate limit at all
   (one expand (x+1)^3000 ran ~46 s).  Solves now run on
   one bounded pool with a fail-fast saturation refusal,
   the (x+1)^3000 shape is refused by the pre-guard, and
   /api/solve carries a per-client rate limit.

Legs are stubbed at the fallback seams throughout (no
network, no keys) — routing/verification logic is what's
under test; solver-side cases pass for real.
"""
import time
from fractions import Fraction

import pytest

import api
import deep_solve
import fallback
import verify_all
from solver import multipart223
from solver import router as solver_router

CANNED = (
    "I didn't understand that",
    "Samajh nahi aaya",
    "समझ नहीं आया",
    "Answer not found",
)

CASE5 = ("Check the continuity of a function at x = 0 x=0. "
         "Differentiate y = x 2 sin x y=x2 sinx.")


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w227.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    monkeypatch.delenv("GANITRA_AIVERIFY", raising=False)
    monkeypatch.delenv("GANITRA_DEEP_SOLVE", raising=False)
    return path


@pytest.fixture()
def no_legs(monkeypatch):
    def _none(question, hindi, lang_request=None, **kwargs):
        return None

    def _none_or(question, hindi, **kwargs):
        return None

    monkeypatch.setattr(fallback, "_gemini_answer", _none)
    monkeypatch.setattr(fallback, "_groq_answer", _none)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        _none_or)


def _assert_not_canned(res):
    text = str(res.get("answer") or "")
    assert res.get("fallback_kind") != "not_found", res
    for bad in CANNED:
        assert bad not in text, (bad, text[:160])


# ---------------------------------------------------------------------------
# 1. Screenshot case 5 — OCR-doubled multipart calculus
# ---------------------------------------------------------------------------

def test_case5_dedup_drops_glued_restatements():
    out = multipart223._dedup_ocr_restatements(CASE5)
    assert out == ("Check the continuity of a function "
                   "at x = 0. Differentiate y = x 2 sin x.")


def test_case5_dedup_leaves_clean_text_alone():
    clean = "Find the area of a circle with radius 7 cm."
    assert multipart223._dedup_ocr_restatements(clean) \
        == clean


def test_case5_power_repair_spaced_and_glued():
    assert multipart223._repair_ocr_powers(
        "Differentiate y = x 2 sin x") == \
        "Differentiate y = x^2 sin x"
    assert multipart223._repair_ocr_powers(
        "Differentiate y = x2 sin x") == \
        "Differentiate y = x^2 sin x"
    # No trig/log neighbour -> no repair, nothing invented.
    assert multipart223._repair_ocr_powers(
        "Find x 2 + 3") == "Find x 2 + 3"


def test_case5_continuity_missing_function_detection():
    assert multipart223._continuity_missing_function(
        "Check the continuity of a function at x = 0") == "0"
    # A function IS given -> not the incomplete shape.
    assert multipart223._continuity_missing_function(
        "Check the continuity of f(x) = x^2 at x = 0") \
        is None
    assert multipart223._continuity_missing_function(
        "Check the continuity of sin x at x = 0") is None
    # Not a continuity ask at all.
    assert multipart223._continuity_missing_function(
        "Differentiate y = x^2 sin x") is None


def test_case5_full_question_note_plus_solved_part(
        db, no_legs):
    res = fallback.fallback_answer(CASE5, lang="en")
    _assert_not_canned(res)
    assert res["op"] == "multipart227"
    answer = str(res["answer"])
    # Part (a): the plain incomplete note, naming what is
    # missing — not a solve attempt, not the canned line.
    assert "(a) Function not given" in answer
    steps = " ".join(str(s) for s in res.get("steps") or [])
    assert "function itself is not given" in steps
    assert "only the point at x = 0" in steps
    # Part (b): really solved — d/dx (x^2 sin x), the
    # product rule, not the 2x sin x misread.
    assert "x^2·cos(x) + 2·x·sin(x)" in answer
    assert res["multipart"]["solved"] == ["a", "b"]


def test_case5_clean_two_part_same_shape(db, no_legs):
    # The same two asks typed cleanly (no OCR doubling):
    # the incomplete part is still noted, the complete
    # part still solved.
    res = fallback.fallback_answer(
        "Check the continuity of a function at x = 0. "
        "Differentiate y = x^2 sin x.", lang="en")
    _assert_not_canned(res)
    assert res["op"] == "multipart227"
    assert "Function not given" in str(res["answer"])
    assert "x^2·cos(x) + 2·x·sin(x)" in str(res["answer"])


def test_case5_family_declines_single_calculus_question():
    # One part only — the family must not steal the
    # ordinary single-question flow.
    assert multipart223._ocr_calculus_result(
        "Differentiate y = x^2 sin x") is None


def test_case5_family_declines_mixed_subjects():
    # A non-calculus part means this is not the family's
    # shape (the older families / flows decide).
    assert multipart223._ocr_calculus_result(
        "Find the area of a circle with radius 7. "
        "Differentiate y = x^2 sin x.") is None


# ---------------------------------------------------------------------------
# 2. Screenshot case 6 — long pasted papers are solved, not rejected
# ---------------------------------------------------------------------------

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
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    r = c.post("/signup", data={
        "name": "Wave227 Check", "class": "8",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave227pass"})
    assert r.status_code == 302, r.status_code
    return c


def test_case6_paste_over_500_chars_is_solved(client):
    assert len(LONG_PASTE) > 500  # past the old line
    r = client.post("/api/solve", json={"question": LONG_PASTE})
    data = r.get_json()
    assert r.status_code == 200, data
    assert data["ok"] is True, data
    # NOT the length rejection.
    assert "bit long" not in str(data.get("message") or "")
    res = data["result"]
    assert res["op"] == "multipart_general", res
    answer = str(res["answer"])
    for bit in ("40", "x = 2", "18", "25%", "1100"):
        assert bit in answer, (bit, answer[:200])


def test_case6_absurd_payload_still_refused(client):
    # The payload-size guard survives — only past the hard
    # ceiling, never at 500 any more.
    r = client.post(
        "/api/solve",
        json={"question": "2+2 " + "x" * 9000})
    data = r.get_json()
    assert data["ok"] is False
    assert "bit long" in str(data.get("message") or "")


def test_rate_limit_caps_a_hammering_client(
        client, monkeypatch):
    monkeypatch.setattr(api, "_SOLVE_RATE_PER_MINUTE", 3)
    codes = []
    for _ in range(5):
        r = client.post("/api/solve", json={"question": "2+2"})
        codes.append((r.status_code, r.get_json()["ok"]))
    assert codes[0] == (200, True)
    assert (429, False) in codes
    # Once limited, the client stays limited inside the
    # window — the cap is real, not a one-off.
    assert codes[-1] == (429, False)


# ---------------------------------------------------------------------------
# 3. BUG-004 — exact fractions, marked approximations
# ---------------------------------------------------------------------------

def test_bug004_fraction_over_100_stays_exact():
    assert deep_solve._fmt(Fraction(1, 101)) == "1/101"
    assert deep_solve._fmt(Fraction(-1, 101)) == "-1/101"
    assert deep_solve._fmt(Fraction(355, 113)) == "355/113"


def test_bug004_small_fractions_unchanged():
    assert deep_solve._fmt(Fraction(1, 3)) == "1/3"
    assert deep_solve._fmt(Fraction(22, 7)) == "22/7"
    assert deep_solve._fmt(Fraction(4, 1)) == "4"


def test_bug004_monster_denominator_marked_approx():
    out = deep_solve._fmt(Fraction(1, 999999937))
    assert out.startswith("≈"), out
    assert out != "0" and out != "0.0000", out
    # A value that rounds to zero at 4 decimals must not
    # print as a silent (or marked) plain zero either.
    assert out != "≈ 0", out


def test_bug004_no_silent_truncation_anywhere():
    # The audit's exact example, end to end through the
    # value formatter: 1/101 must never come out as the
    # bare "0.0099" again.
    assert deep_solve._fmt(Fraction(1, 101)) != "0.0099"


# ---------------------------------------------------------------------------
# 4. BUG-005 — signed number parsing
# ---------------------------------------------------------------------------

def test_bug005_negative_value_keeps_its_sign():
    assert deep_solve._numbers_in("x = -5") == [Fraction(-5)]
    assert deep_solve._parse_value("x = -5") == Fraction(-5)
    assert deep_solve._numbers_in("temp -5 and 3") == \
        [Fraction(-5), Fraction(3)]
    assert deep_solve._numbers_in("-3/4") == \
        [Fraction(-3, 4)]


def test_bug005_unicode_minus_counts():
    assert deep_solve._parse_value("x = −5") == Fraction(-5)


def test_bug005_binary_minus_still_subtraction():
    assert deep_solve._numbers_in("5-3") == \
        [Fraction(5), Fraction(3)]
    assert deep_solve._numbers_in("5 -3") == \
        [Fraction(5), Fraction(3)]
    assert deep_solve._numbers_in("x-3") == [Fraction(3)]
    assert deep_solve._numbers_in("5 - 3") == \
        [Fraction(5), Fraction(3)]


def test_bug005_scientific_notation_is_one_token():
    assert deep_solve._numbers_in("value 1.5e3") == \
        [Fraction(1500)]


# ---------------------------------------------------------------------------
# 5. BUG-007 — verify_all demands the complete solution set
# ---------------------------------------------------------------------------

def test_bug007_incomplete_root_set_no_longer_passes():
    # The audit's example: the old checker passed this.
    assert verify_all.check_sample(
        "x = 2", ["x = 2", "x = 3"]) is False
    assert verify_all.check_sample(
        "x = 2 or x = 3", ["x = 2", "x = 3"]) is True
    assert verify_all.check_sample("42", "42") is True
    assert verify_all.check_sample("41", "42") is False


def test_bug007_quadratic_sample_requires_both_roots():
    entry = [s for s in verify_all.SAMPLES
             if s[0] == "algebra-quadratic"]
    assert len(entry) == 1
    _cat, _q, expect = entry[0]
    assert isinstance(expect, list)
    assert "x = 2" in expect and "x = 3" in expect


def test_bug007_live_quadratic_passes_the_full_check(db):
    r = solver_router.solve_question("x^2 - 5x + 6 = 0")
    expect = [s[2] for s in verify_all.SAMPLES
              if s[0] == "algebra-quadratic"][0]
    assert verify_all.check_sample(
        str(r.get("answer", "")), expect) is True


# ---------------------------------------------------------------------------
# 6. BUG-008 + DoS — bounded pool, pre-guard, no thread leak
# ---------------------------------------------------------------------------

def test_bug008_binomial_bomb_refused_by_pre_guard():
    assert solver_router._dangerous_shape(
        "expand (x+1)^3000")
    assert solver_router._dangerous_shape(
        "expand (x + 1)^3000")
    # The teaching expansions stay allowed.
    assert solver_router._dangerous_shape(
        "expand (x + y)^100") is None
    assert solver_router._dangerous_shape(
        "expand (x + 1)^5") is None


def test_bug008_bomb_solve_returns_fast_with_refusal(db):
    t0 = time.monotonic()
    r = solver_router.solve_question("expand (x+1)^3000")
    elapsed = time.monotonic() - t0
    assert r.get("op") == "error"
    assert elapsed < 5.0, elapsed


def test_bug008_pool_is_bounded_and_saturation_refuses():
    assert solver_router._SOLVE_POOL_WORKERS >= 1
    assert solver_router._SOLVE_POOL_SLOTS >= \
        solver_router._SOLVE_POOL_WORKERS
    # Hold every slot: a new solve must be refused with the
    # standard too-big result, WITHOUT spawning work —
    # before Wave 227 this path created another daemon
    # thread every single time.
    held = 0
    try:
        for _ in range(50):
            if not solver_router._solve_slots.acquire(
                    blocking=False):
                break
            held += 1
        # Let any in-flight done-callbacks flush, then top
        # up to the full cap.
        time.sleep(0.2)
        while held < solver_router._SOLVE_POOL_SLOTS and \
                solver_router._solve_slots.acquire(
                        blocking=False):
            held += 1
        assert held == solver_router._SOLVE_POOL_SLOTS
        r = solver_router._solve_with_budget("2 + 2")
        assert r.get("op") == "error"
    finally:
        for _ in range(held):
            solver_router._solve_slots.release()


def test_bug008_normal_solve_still_runs_on_the_pool(db):
    r = solver_router.solve_question("347 + 258")
    assert r["answer"] == "605"
