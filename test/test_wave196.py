"""Wave 196 (19 Nov 2026): Inverse Trigonometric
Functions CLEAN-TEXT RECHECK + regression pin.

The form audit (section C) showed the book pool at
31/31 CBSE unsolved for Class 12 Inverse Trig, but
proved that is an extraction artefact: the printed
arguments are stripped in the book text, and the two
clean-text audit probes (07 principal value, 08 sum)
were recorded as HITs. This wave re-measured with a
45-question clean-text battery (NCERT Ex 2.1 / 2.2
dresses a student actually types) through
solver.router.solve_question.

FINDING 1 — the audit's probe-08 expected value was
WRONG, and the native serve was wrong with it.
tan^-1(1) + cos^-1(-1/2) + sin^-1(-1/2)
  = pi/4 + 2pi/3 - pi/6 = 3pi/4  (135 degrees),
not pi/2. The audit recorded pi/2 because the Wave 32
pair shortcut (sin^-1 x + cos^-1 x = pi/2) matched the
cos/sin pair inside the question and silently DROPPED
the tan^-1(1) term. (Wave 142's c12gaps schema already
knew 3pi/4 and repaired this at the fallback layer;
the native router still served pi/2.) Every expected
value in this file was verified independently (hand
computation / principal-branch definitions) before
pinning.

FINDING 2 — more clean-text fragment/wrong serves in
the same family, all fixed at family level in
solver/trigonometry.py (+ one router topic gate):
  * sin^-1(1/sqrt(2)) served pi/2 (the argument was
    truncated to 1). Mixed sums served their FIRST
    term alone (cos^-1(1/2) + 2 sin^-1(1/2) -> pi/3).
    Pure tan^-1 chains in "Find the value of ..." dress
    fragment-served too (the Wave 47 rest-check filler
    list missed the word "the").
  * The Unicode root dress (cos^-1(√3/2), tan^-1(√3))
    parse-errored.
  * The word dress ("sin inverse (1/2)", "inverse sin
    (1/2)") fragment-served the bare argument "1/2",
    and "tan inverse (1)" errored demanding a matrix —
    the router's linear-algebra gate claims the word
    "inverse" before the trigonometry gate can run.
Fixes: a strict whole-expression inverse-trig
evaluator (signed fn^-1(number) terms with optional
coefficients, NCERT principal branches, served only
when the total is a standard multiple of 15 degrees),
dress normalisation local to the family (root sign,
word dress, arc dress), residual guards on the Wave
32 pair shortcut and the single-term schema, the
Wave 47 filler list completed, and a router gate
exception routing inverse-trig word dress to
trigonometry.

RESIDUALS (documented, NOT pinned as solves):
  * Equation dress "Solve tan^-1(2x) + tan^-1(3x) =
    pi/4" still misses natively (x = 1/6, verified by
    hand: 6x^2 + 5x - 1 = 0, x = -1 is extraneous).
    The sibling sin^-1 equation DOES solve (below).
  * Prove/identity dresses are a different family
    (no prover built, per the wave order): three
    parse-error; "Show that tan^-1(1/2) + tan^-1(2/11)
    = tan^-1(3/4)" is served atan(24/7) — the Wave 47
    fold sums all three tan^-1 terms including the
    RHS; it is not a proof and not the LHS value.
    Flagged for a future prove wave.
"""
import math

import pytest

from solver.router import solve_question

PI = math.pi


def _val(q):
    out = solve_question(q)
    assert isinstance(out, dict), q
    return out


def _assert_value(q, expected):
    out = _val(q)
    assert out.get("value") is not None, (q, out)
    assert abs(float(out["value"]) - expected) < 1e-6, \
        (q, out, expected)


# ------------------------------------------------------------------
# Controls — the audit's own probes 07 / 08, verbatim.
# 07 keeps solving identically. 08's pinned value is
# the independently verified 3pi/4 (see docstring).
# ------------------------------------------------------------------

def test_control_07_principal_sin_half():
    _assert_value("Find the principal value of "
                  "sin^-1(1/2)", PI / 6)


def test_control_08_sum_of_three_is_3pi_by_4():
    _assert_value("Find the value of tan^-1(1) + "
                  "cos^-1(-1/2) + sin^-1(-1/2)",
                  3 * PI / 4)


# ------------------------------------------------------------------
# Principal values, ASCII dress (Ex 2.1 forms).
# ------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("Find the principal value of sin^-1(-1/2)", -PI / 6),
    ("Find the principal value of cos^-1(√3/2)", PI / 6),
    ("Find the principal value of cos^-1(sqrt(3)/2)",
     PI / 6),
    ("Find the principal value of tan^-1(-1)", -PI / 4),
    ("Find the principal value of tan^-1(√3)", PI / 3),
    ("Find the principal value of tan^-1(sqrt(3))",
     PI / 3),
    ("Find the principal value of cosec^-1(2)", PI / 6),
    ("Find the principal value of sec^-1(2)", PI / 3),
    ("Find the principal value of cot^-1(√3)", PI / 6),
    ("Find the principal value of sin^-1(1/√2)", PI / 4),
    ("Find the principal value of sin^-1(1/sqrt(2))",
     PI / 4),
    ("Find the principal value of cos^-1(1/2)", PI / 3),
    ("Find the principal value of cos^-1(-1/2)",
     2 * PI / 3),
    ("Find the principal value of sec^-1(-2)", 2 * PI / 3),
    ("Find the principal value of cosec^-1(-2)", -PI / 6),
    ("Find the principal value of cot^-1(-1)", 3 * PI / 4),
    ("Find the principal value of tan^-1(1)", PI / 4),
    ("Find the principal value of sin^-1(1)", PI / 2),
    ("Find the principal value of cos^-1(0)", PI / 2),
    # Branch-critical extras (Wave 142 forms, now also
    # native): sec of a fraction, cot of a negative.
    ("Find the principal value of sec^-1(2/sqrt(3))",
     PI / 6),
    ("Find the principal value of cot^-1(-1/sqrt(3))",
     2 * PI / 3),
    ("Find the principal value of cos^-1(-1)", PI),
    ("Find the principal value of sin^-1(-1)", -PI / 2),
])
def test_principal_values_ascii(q, expected):
    _assert_value(q, expected)


# ------------------------------------------------------------------
# Principal values, word / arc dress.
# ------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("Find the principal value of sin inverse (1/2)",
     PI / 6),
    ("Find the principal value of inverse sin (1/2)",
     PI / 6),
    ("Find the principal value of cos inverse (1/2)",
     PI / 3),
    ("Find the principal value of tan inverse (1)",
     PI / 4),
    ("Find the principal value of tan inverse (-1)",
     -PI / 4),
    ("Find the principal value of sec inverse (2)",
     PI / 3),
    ("Find the principal value of cosec inverse (2)",
     PI / 6),
    ("Find the principal value of cot inverse (1)",
     PI / 4),
    ("What is arcsin(1/2)?", PI / 6),
    ("What is arccos(1/2)?", PI / 3),
])
def test_principal_values_word_dress(q, expected):
    _assert_value(q, expected)


def test_arctan_word_dress_answer_text():
    # Served by the pre-existing inverse_value op, whose
    # value field is in DEGREES; the answer text is the
    # pinned contract here.
    out = _val("What is arctan(1)?")
    assert "pi/4" in str(out.get("answer") or "")


# ------------------------------------------------------------------
# Sums and differences (Ex 2.1 / 2.2 forms).
# ------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("Find the value of tan^-1(√3) - sec^-1(-2)",
     -PI / 3),
    ("Find the value of cos^-1(1/2) + 2 sin^-1(1/2)",
     2 * PI / 3),
    ("Find the principal value of cos^-1(1/2) + "
     "2sin^-1(1/2)", 2 * PI / 3),
    ("Find the value of sin^-1(1/2) + cos^-1(1/2)",
     PI / 2),
    ("Find the value of cos^-1(1/2) + sin^-1(1/2)",
     PI / 2),
    ("Find the value of sin^-1(-1/2) + cos^-1(-1/2)",
     PI / 2),
    ("Find the value of tan^-1(1) + tan^-1(2) + "
     "tan^-1(3)", PI),
    ("Find the value of tan^-1(1/2) + tan^-1(1/3)",
     PI / 4),
])
def test_inverse_trig_sums(q, expected):
    _assert_value(q, expected)


# ------------------------------------------------------------------
# Equation dress (Ex 2.2 / Miscellaneous): the sin^-1
# equation solves; x = 0 verified by substitution
# (sin^-1(1) - 2 sin^-1(0) = pi/2).
# ------------------------------------------------------------------

def test_equation_sin_inverse_x_zero():
    out = _val("Solve sin^-1(1 - x) - 2 sin^-1(x) = pi/2")
    assert out.get("answer") == "x = 0"


def test_equation_sin_inverse_wave142_dress():
    out = _val("sin^-1(1-x) - 2sin^-1(x) = pi/2, "
               "then x is equal to")
    assert out.get("answer") == "x = 0"


# ------------------------------------------------------------------
# Guards: no fragment/wrong serve may come back.
# ------------------------------------------------------------------

def test_nonstandard_value_not_served_as_standard():
    # tan^-1(1/sqrt(2)) is not a standard angle; it must
    # never be served as one (it was asin-style
    # truncated before this wave's family fix).
    out = _val("Find the principal value of "
               "tan^-1(1/√2)")
    val = out.get("value")
    assert val is None or abs(
        float(val) - math.atan(1 / math.sqrt(2))) < 1e-6


def test_matrix_inverse_still_linear_algebra():
    # The router gate exception is only for inverse-TRIG
    # dress; a real matrix inverse still solves as one.
    out = _val("Find the inverse of the matrix "
               "[[1,2],[3,4]]")
    assert out.get("answer") == "[[-2, 1], [3/2, -1/2]]"
