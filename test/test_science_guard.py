"""Wave 20 (Suraj, 12 Nov 2026): Ganitra is MATHS-ONLY.

Bug (from Suraj's phone screenshot): a Physics refractive-index
question was answered by the junior "times_pair" solver with a
nonsense number — the Wave-18 salvage layer had carved the
fragment "2 x 10" out of "2 x 10^8" (scientific notation) and
"solved" it. Out-of-scope science must get the honest fallback
(Ganitra is for Maths + formula guidance), never a fake answer.

Guards proven here:
- the exact reported question returns fallback_kind="science",
  NOT a junior/times_pair result, through the full app path
  (solve_question + with_fallback);
- salvage no longer extracts a chain that runs into a "^";
- the router refuses the junior intent for science questions;
- genuine maths that uses "speed" (train speed-distance-time)
  still solves normally — bare "speed" is not a science signal.
"""
from fallback import _candidates, with_fallback
from solver.router import has_science_signal, route_intent, solve_question

PHYSICS_Q = (
    "A ray of light travels from medium A to medium B. The "
    "refractive index of medium B relative to medium A is 1.5, "
    "and the speed of light in medium A is 2 x 10^8 m/s. What "
    "is the speed of light in medium B?")


def test_reported_physics_question_gets_honest_science_reply():
    result = with_fallback(PHYSICS_Q, solve_question(PHYSICS_Q))
    assert result.get("fallback_kind") == "science"
    assert result.get("type") != "junior"
    assert result.get("op") != "times_pair"
    assert "216" not in str(result.get("answer", ""))
    assert "Maths" in str(result.get("answer", ""))
    # Guidance names the concept's formula (n = v_A / v_B style)
    # without presenting a solved numeric answer.
    joined = " ".join(result.get("steps") or [])
    assert "refractive index" in joined


def test_scientific_notation_is_not_a_salvage_chain():
    cands = _candidates(PHYSICS_Q)
    # The fragment carved out of "2 x 10^8" must be gone. (The
    # filler-stripped whole question may remain as a candidate;
    # it cannot solve, and _salvage refuses science outright.)
    assert "2 x 10" not in cands


def test_router_refuses_junior_for_science():
    assert has_science_signal(PHYSICS_Q)
    assert route_intent(PHYSICS_Q) != "junior"
    result = solve_question(PHYSICS_Q)
    assert result.get("type") != "junior"
    assert result.get("op") != "times_pair"


def test_genuine_speed_maths_still_solves():
    q = "A train travels 180 km in 3 hours. What is its speed?"
    assert not has_science_signal(q)
    result = solve_question(q)
    assert result.get("op") != "error"
    assert "60" in str(result.get("answer", ""))


def test_other_science_topics_also_guarded():
    for q in ("What is the voltage across a 4 ohm resistor "
              "carrying 2 ampere current?",
              "Define acceleration and give its SI unit.",
              "What is a chemical element?"):
        result = with_fallback(q, solve_question(q))
        assert result.get("fallback_kind") == "science", q
