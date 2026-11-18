"""Wave 149 — school-style steps for simple linear equations.

After Deploy-29 the live check found that "Solve: 3x + 7 = 22"
still narrated its PRIMARY working from the standard form:

    Bring all terms to one side: 3·x + -15 = 0
    Add 15 to both sides: 3·x = 15
    Divide both sides by 3: x = 5

The answer was right, but no teacher writes it that way: for
a·x + b = c the first move is on the constant that is actually
in the equation — "Subtract 7 from both sides". The serving
stepper is solver/algebra.py::_solve_single_equation, whose
_linear_steps only ever sees the combined a·x + b = 0
coefficients. Wave 149 adds _school_linear_steps, gated to the
simple shape (variable on one side only, a plain rational
number on the other), narrating from the equation as asked.
Everything outside the gate — x on both sides, quadratics,
decimal coefficients — keeps the old narration byte-for-byte.
"""
import sympy as sp

from solver.algebra import _school_linear_steps, solve_algebra
from solver.router import solve_question
from steplang import translate_step

x = sp.Symbol("x")


def _steps(question):
    return solve_question(question)["steps"]


# ------------------------------------------------------------------ #
# The headline cases                                                  #
# ------------------------------------------------------------------ #

def test_3x_plus_7_school_steps():
    result = solve_question("Solve: 3x + 7 = 22")
    assert result["answer"] == "x = 5"
    assert result["steps"] == [
        "Subtract 7 from both sides: 3·x = 15",
        "Divide both sides by 3: x = 5",
        "Solution: x = 5",
    ]
    for step in result["steps"]:
        assert "Bring all terms to one side" not in step
        assert "Add 15" not in step


def test_3x_minus_7_adds_7():
    result = solve_question("Solve: 3x - 7 = 22")
    assert result["answer"] == "x = 29/3"
    assert "Add 7 to both sides: 3·x = 29" in result["steps"]
    assert "Divide both sides by 3: x = 29/3" in result["steps"]
    for step in result["steps"]:
        assert "Bring all terms to one side" not in step


def test_5x_plus_3_subtracts_3():
    result = solve_question("Solve: 5x + 3 = 18")
    assert result["answer"] == "x = 3"
    assert result["steps"] == [
        "Subtract 3 from both sides: 5·x = 15",
        "Divide both sides by 5: x = 3",
        "Solution: x = 3",
    ]


def test_coefficient_one_and_mirrored():
    # a == 1: no "1·x", no divide step.
    result = solve_question("Solve: x + 5 = 3")
    assert result["steps"] == [
        "Subtract 5 from both sides: x = -2",
        "Solution: x = -2",
    ]
    # Variable on the right narrates the same school steps.
    result = solve_question("Solve: 22 = 3x + 7")
    assert result["answer"] == "x = 5"
    assert "Subtract 7 from both sides: 3·x = 15" in \
        result["steps"]


# ------------------------------------------------------------------ #
# Hindi / Hinglish rendering (steplang idiom, no new rules)           #
# ------------------------------------------------------------------ #

def test_new_steps_translate_hi_and_hinglish():
    steps = solve_question("Solve: 3x + 7 = 22")["steps"]
    hi = [translate_step(s, "hi") for s in steps]
    assert hi[0] == "दोनों ओर से 7 घटाइए: 3·x = 15"
    assert hi[1] == "दोनों ओर 3 से भाग दीजिए: x = 5"
    hinglish = [translate_step(s, "hinglish") for s in steps]
    assert hinglish[0] == "Dono side se 7 subtract karo: 3·x = 15"
    assert hinglish[1] == "Dono side ko 3 se divide karo: x = 5"
    # The ax - b = c move translates too.
    assert translate_step("Add 7 to both sides: 3·x = 29", "hi") \
        == "दोनों ओर 7 जोड़िए: 3·x = 29"


# ------------------------------------------------------------------ #
# Outside the gate: narration UNCHANGED from main                     #
# ------------------------------------------------------------------ #

def test_x_on_both_sides_unchanged():
    result = solve_question("Solve: 3x + 7 = 2x + 22")
    assert result["answer"] == "x = 15"
    assert result["steps"] == [
        "Bring all terms to one side: 1·x + -15 = 0",
        "Add 15 to both sides: 1·x = 15",
        "Solution: x = 15",
    ]


def test_quadratic_unchanged():
    result = solve_question("Solve: x^2 - 5x + 6 = 0")
    assert result["answer"] == "x = 2, x = 3"
    assert result["steps"] == [
        "Write in standard form: 1·x^2 + -5·x + 6 = 0, "
        "so a = 1, b = -5, c = 6",
        "Discriminant D = b^2 - 4ac = (-5)^2 - 4·1·6 = 1",
        "D > 0, so there are two distinct real roots.",
        "Quadratic formula: x = (-b ± sqrt(D)) / (2a) = "
        "(5 ± sqrt(1)) / 2",
        "Solution: x = 2, x = 3",
    ]


def test_decimal_coefficients_unchanged():
    result = solve_algebra("Solve 2.5x + 1.5 = 7")
    assert result["steps"][0].startswith(
        "Bring all terms to one side")


# ------------------------------------------------------------------ #
# The gate itself                                                     #
# ------------------------------------------------------------------ #

def test_gate_declines_outside_shapes():
    # Variable on both sides.
    assert _school_linear_steps(
        3 * x + 7, 2 * x + 22, x) is None
    # Non-numeric side.
    assert _school_linear_steps(3 * x + 7, x + x, x) is None
    # Decimal (non-rational) coefficients.
    assert _school_linear_steps(
        sp.Float(2.5) * x + sp.Float(1.5), sp.Integer(7),
        x) is None
    # Nothing to narrate (x = 5): caller falls back.
    assert _school_linear_steps(
        x, sp.Integer(5), x) is None


def test_gate_accepts_fraction_coefficients():
    steps = _school_linear_steps(
        x / 3 + 2, sp.Integer(5), x)
    assert steps == [
        "Subtract 2 from both sides: 1/3·x = 3",
        "Divide both sides by 1/3: x = 9",
    ]
