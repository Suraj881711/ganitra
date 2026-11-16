"""Wave 80: Class 12 pack — vector glyphs, calculus core,
matrices in board text form.

Wave 71 audit background: Class 12 was the weakest area
(~21 calculus failures plus the papers-sample gaps), and 4
items carrying unit-vector Unicode (î × k̂ type questions)
each burned >20 s — the ERROR_TIMEOUT family. Root cause of
the timeouts: no solver understood the vector notation at
all, so the MCQ layer retried the unsolvable stem through
~11 full-pipeline candidates, each paying the router's
solve budget; separately, _ode letter-split the prose of
fact questions ("Integrating factor of ...") into symbol
soup and dsolve churned on it for ~39 s.

This wave: solver/vectors.py claims the glyph family in
milliseconds; calculus gains the ∫ glyph (Unicode limits,
glued forms sinx/logx/cosec/tan⁻¹), brace continuity incl.
Hindi संतत stems, implicit dy/dx, integrating factor,
order & degree, Hindi अवकलज derivatives, (d/dx)(...) form
and chain-rate areas; _ode refuses prose before dsolve;
linear algebra gains bar determinants, unnamed scalar x
matrix, symbolic determinants, A'A = I verification and
the matrix counting facts; mcq._solve_stem stops starting
new candidates after ~5 s.

Every expected answer below is hand-verified.
"""
import time

import pytest

from api import _solve_friendly
from solver.calculus import solve_calculus
from solver.linear_algebra import solve_linear_algebra
from solver.vectors import solve_vectors


def _ans(result):
    assert result is not None, "expected a result, got None"
    return str(result.get("answer", ""))


# --- Vectors: the timeout family, now milliseconds --------

def test_unit_cross_is_minus_j():
    r = solve_vectors("î × k̂ = (a) 0⃗ (b) ĵ (c) −ĵ (d) k̂ × î")
    assert _ans(r) == "-ĵ"


def test_dot_product_glyphs():
    r = solve_vectors("(2î + 3ĵ − 5k̂)·(7î − ĵ + 3k̂) = "
                      "(A) 32 (B) 2 (C) 4 (D) −4")
    assert _ans(r) == "-4"


def test_unit_vector_english_and_hindi():
    q_en = ("If a⃗ = 2î − ĵ + 2k̂ then unit vector in the "
            "direction of vector a⃗ is")
    q_hi = ("यदि a⃗ = 2î − ĵ + 2k̂ तो a⃗ की दिशा में संगत "
            "इकाई सदिश â है:")
    for q in (q_en, q_hi):
        assert _ans(solve_vectors(q)) == "(1/3)(2î - ĵ + 2k̂)"


def test_mixed_dot_cross_expression():
    r = solve_vectors("(î × ĵ) · ĵ + (ĵ × î) · k̂ का मान है :")
    assert _ans(r) == "-1"


def test_parallelogram_from_diagonal():
    r = solve_vectors(
        "In the given figure, ABCD is a parallelogram. "
        "If AB = 2î − 4ĵ + 5k̂ and DB = 3î − 6ĵ + 2k̂, "
        "find AD and the area of the parallelogram.")
    a = _ans(r)
    assert "AD = -î + 2ĵ + 3k̂" in a
    assert "11·sqrt(5)" in a  # |AB x AD| = sqrt(605) = 11 sqrt(5)


def test_unit_vectors_modulus_equation_angle():
    r = solve_vectors(
        "दो मात्रक सदिशों a⃗ और b⃗ के लिए |2a⃗ + 3b⃗| = "
        "|3a⃗ − 2b⃗| है। a⃗ तथा b⃗ के बीच का कोण ज्ञात कीजिए।")
    assert _ans(r) == "θ = 90°"


def test_direction_cosines_and_plane():
    r = solve_vectors(
        "If a line makes angle 30°, 60° and 90° with the "
        "positive direction of x, y and z axes, find its "
        "direction cosines.")
    assert _ans(r) == "(sqrt(3)/2, 1/2, 0)"
    r = solve_vectors("The equation of ZX-plane is "
                      "(A) x = 0 (B) y = 0 (C) z = 0 (D) None")
    assert _ans(r) == "y = 0"


def test_vector_basics_component_form():
    assert _ans(solve_vectors(
        "Find the magnitude of vector 3i + 4j")) == "5"
    assert _ans(solve_vectors(
        "Find a · b if a = 2i + j and b = i - 3j")) == "-1"
    assert _ans(solve_vectors("What is j × i?")) == "-k̂"
    assert _ans(solve_vectors(
        "Find |a| if a = (1, 2, 2)")) == "3"
    assert _ans(solve_vectors(
        "a = i + j, b = i - j, find the angle between a "
        "and b")) == "θ = 90°"
    assert _ans(solve_vectors(
        "Find the dot product of a and b if a = i + 2j and "
        "b = 3i - j")) == "1"


def test_vectors_reject_non_vector_text():
    assert solve_vectors("What is 2 + 2?") is None
    assert solve_vectors("gibberish zqx jkv nothing") is None


# --- Calculus ----------------------------------------------

def test_ddx_parenthesised_form():
    r = solve_calculus("(d/dx)(3x² − cosx + 2) = (a) 2x + sinx "
                       "(b) 6x − sinx (c) 6x + sinx (d) sinx − 6x")
    assert _ans(r) == "6·x + sin(x)"


def test_implicit_dydx_inverse_tan():
    r = solve_calculus("If tan⁻¹(x² + y²) = K then find dy/dx.")
    assert _ans(r) == "-x/y"


def test_integrating_factor_not_dsolve():
    t0 = time.monotonic()
    r = solve_calculus(
        "Integrating factor of the differential Equation "
        "dy/dx + y logx = cosx is")
    assert time.monotonic() - t0 < 5
    assert _ans(r) == "exp(x·log(x) - x)"


def test_order_and_degree():
    r = solve_calculus(
        "अवकल समीकरण [1 + (dy/dx)²]³ = d²y/dx² की कोटि और घात "
        "क्रमशः हैं : (A) 1, 2 (B) 2, 3 (C) 2, 1 (D) 1, 3")
    assert _ans(r) == "2, 1"


def test_integral_polynomial_division():
    r = solve_calculus("Integrate: ∫(x² + 2)/(x + 1) dx")
    assert _ans(r) == "x^2/2 - x + 3·log(x + 1) + C"


def test_definite_abs_hindi():
    r = solve_calculus("समाकलन करें: ∫₂⁸ |x − 5| dx")
    assert _ans(r) == "9"


def test_integral_substitution_cube_form():
    r = solve_calculus("∫ (7 + logx)²/x dx")
    assert _ans(r) == "(log(x) + 7)^3/3 + C"


def test_integral_cosec_standard_form():
    r = solve_calculus("∫ cosec x dx = (A) log|cosec x + cot x| "
                       "+ c (B) log|tan(x/2)| + C")
    assert _ans(r) == "log|tan(x/2)| + C"


def test_integral_exp_f_plus_fprime():
    r = solve_calculus("∫ e^x(1/√(1 − x²) + sin⁻¹x) dx")
    assert _ans(r) == "exp(x)·asin(x) + C"


def test_integral_simple_and_definite_forms():
    assert _ans(solve_calculus(
        "∫(5x⁴ + 2x + sinx)dx")) == "x^5 + x^2 - cos(x) + C"
    assert _ans(solve_calculus(
        "∫₀¹ dx/(1 + x²) = (a) π/4 (b) π/2")) == "pi/4"
    assert _ans(solve_calculus(
        "Evaluate : ∫(0 to 1) x (1 - x)^n dx.")) == \
        "1/((n + 1)·(n + 2))"
    assert _ans(solve_calculus(
        "∫(0 to π/6) sec²(x − π/6) dx")) == "sqrt(3)/3"


def test_brace_continuity_hindi():
    r = solve_calculus(
        "k का वह मान जिसके लिए f(x) = {3x + 5, x ≥ 2; kx², "
        "x < 2} एक संतत फलन है, है :")
    assert _ans(r) == "k = 11/4"


def test_hindi_derivative():
    r = solve_calculus("x के सापेक्ष sin(log x) का अवकलज है:")
    assert _ans(r) == "cos(log(x))/x"


def test_chain_rate_equilateral():
    r = solve_calculus(
        "The side of an equilateral triangle is increasing "
        "at the rate of 3 cm/s. At what rate is its area "
        "increasing when the side of the triangle is 15 cm?")
    assert _ans(r) == "45·sqrt(3)/2"


def test_separable_ode_still_solves():
    r = solve_calculus("Solve the differential equation "
                       "dy/dx = 2x")
    assert r is not None and "x^2" in _ans(r)


# --- Matrices ----------------------------------------------

def test_bar_determinant_proportional_rows():
    r = solve_linear_algebra("|11 7 9; 2 −1 5; 22 14 18| = "
                             "(a) 72 (b) −61 (c) 0 (d) 65")
    assert _ans(r) == "0"


def test_bar_determinant_symbolic():
    r = solve_linear_algebra(
        "The determinant | x + 1, x − 1 ; x² + x + 1, "
        "x² − x + 1 | is equal to:")
    assert _ans(r) == "2"


def test_unnamed_scalar_matrix():
    r = solve_linear_algebra("6[−2 1; 3 5] = (a) [12 6; −18 30] "
                             "(b) [−12 6; 18 30]")
    assert _ans(r) == "[[-12, 6], [18, 30]]"


def test_matrix_counting_facts():
    assert _ans(solve_linear_algebra(
        "The number of all possible matrices of order 2 × 2 "
        "with each entry 3 or 7 is")) == "16"
    assert _ans(solve_linear_algebra(
        "If a matrix has 36 elements, the number of possible "
        "orders it can have, is:")) == "9"


def test_verify_rotation_matrix_orthogonal():
    r = solve_linear_algebra(
        "If A = [[cos θ, sin θ], [-sin θ, cos θ]], then "
        "verify that: A'A = I")
    assert _ans(r) == "A'A = I"


# --- Chat path: latency + the timeout items ----------------

TIMEOUT_ITEMS = [
    "If a⃗ = 2î − ĵ + 2k̂ then unit vector in the direction "
    "of vector a⃗ is (A) (1/3)(−2î + ĵ − 2k̂) "
    "(B) (1/9)(2î − ĵ + 2k̂) (C) (1/9)(−2î + ĵ − 2k̂) "
    "(D) (1/3)(2î − ĵ + 2k̂)",
    "î × k̂ = (a) 0⃗ (b) ĵ (c) −ĵ (d) k̂ × î",
    "यदि a⃗ = 2î − ĵ + 2k̂ तो a⃗ की दिशा में संगत इकाई सदिश "
    "â है: (a) (1/3)(−2î + ĵ − 2k̂) (b) (1/9)(2î − ĵ + 2k̂) "
    "(c) (1/9)(−2î + ĵ − 2k̂) (d) (1/3)(2î − ĵ + 2k̂)",
    "Integrating factor of the differential Equation "
    "dy/dx + y logx = cosx is (A) x (B) e^(x logx − x) "
    "(C) e^(x(1 − logx)) (D) None of these",
]


@pytest.mark.parametrize("q", TIMEOUT_ITEMS)
def test_timeout_items_answer_fast_via_chat(q):
    t0 = time.monotonic()
    r = _solve_friendly(q)
    dt = time.monotonic() - t0
    assert dt < 10, f"took {dt:.1f}s"
    assert not r.get("fallback_kind"), r.get("answer")


def test_chat_vector_mcq_names_option():
    r = _solve_friendly("î × k̂ = (a) 0⃗ (b) ĵ (c) −ĵ (d) k̂ × î")
    assert not r.get("fallback_kind")
    assert "−ĵ" in str(r.get("answer", "")) or \
        "-ĵ" in str(r.get("answer", ""))


def test_gibberish_still_one_line_not_found():
    r = _solve_friendly("zqx jkv wobble trxk plim")
    assert r.get("fallback_kind") == "not_found"


def test_chat_folded_unicode_limits():
    # The router folds superscripts to caret form before
    # dispatch (∫₂⁸ reaches the solver as ∫₂^8, ∫₀¹ as
    # ∫₀^1); the limit parser must read the mixed forms.
    r = _solve_friendly("समाकलन करें: ∫₂⁸ |x − 5| dx")
    assert not r.get("fallback_kind")
    assert str(r.get("answer")) == "9"
    r = _solve_friendly("∫₀¹ dx/(1 + x²) = (a) π/4 (b) π/2 "
                        "(c) 0 (d) π")
    assert not r.get("fallback_kind")
    assert "π/4" in str(r.get("answer"))


def test_chat_chain_rate_reaches_calculus():
    # "increasing at the rate of" must route to calculus or
    # the chain-rate schema never sees the question.
    r = _solve_friendly(
        "The side of an equilateral triangle is increasing "
        "at the rate of 3 cm/s. At what rate is its area "
        "increasing when the side of the triangle is 15 cm?")
    assert not r.get("fallback_kind")
    assert "45·sqrt(3)/2" in str(r.get("answer"))


def test_chat_order_degree_names_correct_option():
    # Via solve_question the derivative arrives as d^2y/dx^2
    # (caret form); order/degree must still read 2, 1 and the
    # MCQ layer must name (C), not the swapped (A).
    r = _solve_friendly(
        "अवकल समीकरण [1 + (dy/dx)²]³ = d²y/dx² की कोटि और घात "
        "क्रमशः हैं : (A) 1, 2 (B) 2, 3 (C) 2, 1 (D) 2, 6")
    assert not r.get("fallback_kind")
    assert "(C)" in str(r.get("answer"))
