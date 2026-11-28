"""Wave 234 — maths quality: exact forms + coverage gaps.

Every case below was first reproduced through the real
pipeline (solve_question + with_fallback, the app's own
entry) before any fix; the packet records the before-state.
Pins marked PIN already worked and must never regress.

1. EXACT FORMS LEAD. sqrt(50) served "7.07107"; sphere
   r=3 volume served "≈ 113.0973 cm³" with no 36π; a
   3-4-5 triangle's area served "6.0000". Now the exact
   form leads and the decimal follows as an approximation
   ("5√2 ≈ 7.0711", "36·pi ≈ 113.0973 cm³", "6").
   22/7-branch answers (school mensuration) are untouched.

2. BOTH ROOTS. "ek sankhya ka varg 144 hai" and its
   English/roman/Devanagari variants were not-found; they
   now give x = ±12 with the reason (squaring removes the
   sign). Length contexts (side from area) stay positive-
   only, with the reason stated.

3. WORDED FACTORIAL. "5 factorial" / "What is 5
   factorial?" were unknown; they now serve 120 with the
   expansion, aligned with the already-working dresses.

4. COVERAGE GAPS (external audit list): |x − 2| = 3;
   "convert 0.75 to fraction"; ∫₀^π sin x dx (PIN);
   "find k so that x² + kx + 9 = 0 has equal roots";
   hexagon angle sum (PIN); hypotenuse dresses incl. the
   Hinglish "karn" form; √(−4) → 2i ("-4 ka square root"
   previously served 2 — the minus was dropped);
   undefined-WHY questions (1/0, 0/0, log 0); worded-
   operator algebra ("x squared minus 4" served a letter
   product of the words); Devanagari number-word
   arithmetic ("दो जमा तीन" — same garbage); check-type
   verdicts ("2 + 2 = 5 sahi hai?").

Non-regression: money / percent / unit answers where the
decimal IS the point stay exactly as they were.
"""
import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), ".."))

from fallback import with_fallback  # noqa: E402
from i18n import solve_failed  # noqa: E402
from solver.expression_parser import fmt_exact  # noqa: E402
from solver.router import solve_question  # noqa: E402
from solver.wave234 import solve_wave234  # noqa: E402


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for env in ("GANITRA_GEMINI_API_KEY",
                "GANITRA_GROQ_API_KEY",
                "GANITRA_OPENROUTER_API_KEY",
                "GEMINI_API_KEY"):
        monkeypatch.delenv(env, raising=False)


def solve(question):
    """The app's own flow: router first, fallback chain
    when the router reports failure."""
    r = solve_question(question)
    if solve_failed(question, r):
        r = with_fallback(question, r)
    return r


def ans(question):
    return str(solve(question).get("answer", ""))


def steps_text(question):
    return " ".join(str(s) for s in
                    solve(question).get("steps") or [])


# ---------------------------------------------------------------------------
# 1. Exact forms lead
# ---------------------------------------------------------------------------

def test_fmt_exact_units():
    import sympy as sp
    assert fmt_exact(sp.sqrt(50)) == "5√2"
    assert fmt_exact(36 * sp.pi) == "36π"
    assert fmt_exact(sp.Integer(6)) == "6"
    assert fmt_exact(sp.Rational(3, 4)) == "3/4"


def test_sqrt50_exact_leads():
    a = ans("sqrt(50)")
    assert "5√2" in a and "≈" in a
    assert "7.07107" not in a


def test_square_root_of_50_exact_leads():
    a = ans("What is the square root of 50?")
    assert "5√2" in a and "≈" in a


def test_sphere_volume_r3_exact_pi():
    a = ans("Find the volume of a sphere with radius 3 cm")
    assert "36·pi" in a and "113.0973" in a


def test_sphere_surface_r3_exact_pi():
    a = ans("Find the surface area of a sphere with "
            "radius 3 cm")
    assert "36·pi" in a and "113.0973" in a


def test_cylinder_volume_r3h5_exact_pi():
    a = ans("Find the volume of a cylinder with radius 3 "
            "and height 5")
    assert "45·pi" in a and "141.3717" in a


def test_cone_volume_r3h4_exact_pi():
    a = ans("Find the volume of a cone with radius 3 and "
            "height 4")
    assert "12·pi" in a and "37.6991" in a


def test_hemisphere_volume_r3_exact_pi():
    a = ans("volume of hemisphere radius 3")
    assert "18·pi" in a and "56.5487" in a


def test_heron_345_is_plain_6():
    a = ans("Find the area of a triangle with sides 3, 4 "
            "and 5")
    assert a.strip() == "6"


def test_triangle_base_height_plain_6():
    a = ans("Find the area of a triangle with base 3 and "
            "height 4")
    assert a.strip() == "6"


def test_circle_r7_22by7_pin():
    # PIN: the 22/7 school branch is untouched.
    assert ans("Find the area of a circle with radius "
               "7 cm").strip() == "154 cm²"


def test_sphere_r7_22by7_pin():
    # PIN: radius 7 takes the 22/7 branch; value unchanged.
    assert "1437.33" in ans("volume of a sphere of "
                             "radius 7")


def test_circumference_r5_exact_lead_pin():
    # PIN: already served the exact lead before Wave 234.
    a = ans("Find the circumference of a circle with "
            "radius 5 cm")
    assert "10·pi" in a and "31.4159" in a


# ---------------------------------------------------------------------------
# 2. Both roots — and positive-only where context is length
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "ek sankhya ka varg 144 hai, sankhya kya hai?",
    "ek sankhya ka varg 144 hai",
    "a number's square is 144, find the number",
    "kisi sankhya ka square 144 hai",
    "the square of a number is 144. find the number",
    "jiska varg 144 hai woh sankhya kya hai",
    "किसी संख्या का वर्ग 144 है, संख्या क्या है?",
])
def test_number_square_both_roots(q):
    a = ans(q)
    assert "±12" in a
    assert "144" in steps_text(q)


def test_number_square_reason_present():
    s = steps_text("ek sankhya ka varg 144 hai")
    assert "(−12)" in s or "(-12)" in s


def test_x2_eq_144_both_roots_pin():
    a = ans("x^2 = 144")
    assert "-12" in a and "12" in a


def test_square_root_of_144_principal_pin():
    # PIN: a bare root ask takes the principal root only.
    assert ans("What is the square root of 144?").strip() \
        == "12"


def test_side_from_area_positive_only():
    a = ans("side of a square with area 144")
    assert a.strip() == "12"
    assert "±" not in a


def test_side_from_area_whose_dress_with_unit():
    a = ans("Find the side of a square whose area is "
            "144 cm^2")
    assert a.strip() == "12 cm"  # length unit, not cm²


def test_side_from_area_with_dress_with_unit():
    a = ans("Find the side of a square with area 144 cm2")
    assert a.strip() == "12 cm"


# ---------------------------------------------------------------------------
# 3. Worded factorial
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "5 factorial",
    "What is 5 factorial?",
    "What is the value of 5 factorial",
])
def test_worded_factorial_value(q):
    r = solve(q)
    assert str(r.get("answer")).strip() == "120"
    assert "5 × 4 × 3 × 2 × 1" in " ".join(
        str(s) for s in r.get("steps") or [])


@pytest.mark.parametrize("q", [
    "factorial of 5",
    "5 ka factorial",
    "factorial 5",
    "7!",
    "7! kitna hota hai",
])
def test_factorial_existing_dresses_pin(q):
    expected = "5040" if q.startswith("7") else "120"
    assert str(solve(q).get("answer")).strip() == expected


def test_factorial_definition_ask_not_claimed():
    # A "matlab" (meaning) ask is a definition question —
    # the value gate must not claim it.
    assert solve_wave234(
        "5 factorial ka matlab kya hai") is None


# ---------------------------------------------------------------------------
# 4a. Absolute-value equations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "|x - 2| = 3",
    "Solve |x - 2| = 3",
    "find |x - 2| = 3",
    "modulus x minus 2 equals 3",
])
def test_abs_equation(q):
    a = ans(q)
    assert "-1" in a and "5" in a


def test_abs_equation_hinglish_dress():
    a = ans("|x + 1| = 5 solve karo")
    assert "-6" in a and "4" in a


# ---------------------------------------------------------------------------
# 4b. Decimal -> fraction dresses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "convert 0.75 to fraction",
    "convert 0.75 into a fraction",
    "0.75 to fraction",
    "0.75 ko fraction me badlo",
    "0.75 as a fraction",
    "write 0.75 as a fraction",
])
def test_decimal_to_fraction(q):
    assert ans(q).strip() == "3/4"


# ---------------------------------------------------------------------------
# 4c. Definite integral (PIN — already worked)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "Integrate sin x dx from 0 to pi",
    "Find the integral of sin x from 0 to pi",
])
def test_definite_integral_sin_pin(q):
    assert ans(q).strip() == "2"


# ---------------------------------------------------------------------------
# 4d. Equal roots — find k
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "Find k so that x^2 + kx + 9 = 0 has equal roots",
    "for what value of k does x^2 + kx + 9 = 0 have "
    "equal roots",
    "Find k if x^2 + kx + 9 = 0 has equal roots",
])
def test_find_k_so_that_dress(q):
    a = ans(q)
    assert "-6" in a and "6" in a


def test_find_k_pinned_dresses():
    a = ans("Find the value of k for which the equation "
            "2x^2 + kx + 3 = 0 has two equal roots")
    assert "sqrt(6)" in a
    a = ans("x^2 + 6x + k = 0 has equal roots find k")
    assert a.strip().endswith("9")


# ---------------------------------------------------------------------------
# 4e. Polygon angle sum (PIN — already worked)
# ---------------------------------------------------------------------------

def test_hexagon_angle_sum_pin():
    assert "720" in ans("sum of interior angles of a "
                        "hexagon")


# ---------------------------------------------------------------------------
# 4f. Hypotenuse dresses
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "hypotenuse of right triangle with sides 5 and 12",
    "Find the hypotenuse of a right triangle with sides "
    "5 and 12",
    "In a right triangle, the two sides are 5 cm and "
    "12 cm. Find the hypotenuse.",
    "right triangle me karn nikalo, sides 5 aur 12",
])
def test_hypotenuse_5_12(q):
    assert ans(q).strip() == "13"


# ---------------------------------------------------------------------------
# 4g. Square root of a negative
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "sqrt(-4)",
    "sqrt of -4",
    "square root of -4",
    "square root of minus 4",
    "-4 ka square root",
])
def test_negative_square_root(q):
    a = ans(q)
    assert "2i" in a
    assert a.strip() != "2"  # the dropped-minus bug


def test_negative_root_explains_i():
    s = steps_text("sqrt(-4)")
    assert "i² = −1" in s or "i^2 = -1" in s


# ---------------------------------------------------------------------------
# 4h. Undefined-WHY explanations
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "1/0 kyun undefined hota hai",
    "Why is 1/0 undefined?",
    "1 by 0 undefined kyun hai",
])
def test_division_by_zero_why(q):
    a = ans(q)
    assert "undefined" in a.lower()


@pytest.mark.parametrize("q", [
    "0/0 kitna hota hai",
    "0/0 kya hota hai",
    "What is 0/0?",
])
def test_zero_by_zero_why(q):
    assert "undefined" in ans(q).lower()


@pytest.mark.parametrize("q", [
    "log 0 kitna hota hai",
    "what is log 0",
    "log of 0",
])
def test_log_zero_why(q):
    assert "undefined" in ans(q).lower()


def test_undefined_gate_does_not_steal_expressions():
    # "1/0" riding inside a bigger expression is not the
    # why-family; the gate must decline it.
    assert solve_wave234("1/0 + 2") is None


# ---------------------------------------------------------------------------
# 4i. Worded-operator algebra
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "x squared minus 4 solve karo",
    "Solve x squared minus 4",
    "x squared minus 4 = 0",
])
def test_worded_equation_difference_of_squares(q):
    a = ans(q)
    assert "-2" in a and "2" in a


def test_worded_equation_trinomial():
    a = ans("x squared minus 5x plus 6 = 0")
    assert "2" in a and "3" in a


def test_worded_equation_solve_cue_no_equals():
    a = ans("x squared plus 5x plus 6 solve karo")
    assert "-3" in a and "-2" in a


# ---------------------------------------------------------------------------
# 4j. Devanagari number-word arithmetic
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("दो जमा तीन", "5"),
    ("तीन जमा चार", "7"),
    ("पाँच घटा दो", "3"),
    ("दो गुना तीन", "6"),
    ("दो जमा तीन कितना होता है", "5"),
])
def test_devanagari_arith(q, expected):
    assert ans(q).strip() == expected


# ---------------------------------------------------------------------------
# 4k. Check / verdict asks
# ---------------------------------------------------------------------------

def test_verdict_wrong_statement():
    a = ans("2 + 2 = 5 sahi hai?")
    assert "Galat" in a and "4" in a


def test_verdict_right_statement_hinglish():
    a = ans("3 + 3 = 6 sahi hai?")
    assert "Sahi" in a


def test_verdict_check_karo_with_x_multiply():
    a = ans("check karo 5 x 3 = 15 sahi hai")
    assert "Sahi" in a and "15" in a


@pytest.mark.parametrize("q", [
    "verify 2 + 2 = 4",
    "is 10 / 2 = 5 true",
    "Is 2 + 2 = 5 correct?",
])
def test_verdict_english_dresses(q):
    a = ans(q)
    if "5 correct" in q:
        assert "Not correct" in a
    else:
        assert "Correct" in a


# ---------------------------------------------------------------------------
# Non-regression: decimals that ARE the point stay decimal
# ---------------------------------------------------------------------------

def test_percent_decimal_pin():
    assert ans("12.5% of 80").strip() == "10"


def test_money_decimal_pin():
    assert ans("3 pens at Rs 12.50 each, total "
               "cost").strip() == "37.5"


def test_unit_conversion_pin():
    assert "2500" in ans("convert 2.5 kg to grams")


def test_percent_plain_pin():
    assert ans("What is 15% of 200?").strip() == "30"


def test_gate_declines_plain_arithmetic():
    # The Wave 234 dispatcher must never swallow questions
    # the classic paths own.
    assert solve_wave234("2 + 2") is None
    assert solve_wave234(
        "Find the area of a circle with radius 5") is None
    assert solve_wave234(
        "What is the capital of France?") is None


def test_gate_declines_linear_worded_equation():
    # A plain linear worded equation belongs to the
    # fallback deep-solve rescue (Wave 134 pins its
    # mechanism); the worded-algebra gate owns only the
    # squared/cubed dresses.
    assert solve_wave234("3 x plus 5 equals 20") is None
    assert solve_wave234("x plus 5 equals 12") is None
