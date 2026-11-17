"""Wave 142: Class 12 book-gap families.

Built from the Wave 135 CBSE/NCERT audit (17 Nov 2026): on
real NCERT Class 12 book questions Ganitra scored Inverse
Trigonometric Functions 0.0% (0/31), Vector Algebra 10.0%
(7/70), Continuity and Differentiability 15.9% (13/82),
Application of Derivatives 26.2% (21/80), Application of
Integrals 50.0% (5/10) — and the topics directory had ZERO
'Application of Integrals' topics and only 2 'Conic
Sections' topics. Fixtures: ~/workspace/ganitra-book-
questions.jsonl (the audit population: class 12, NCERT,
extraction_reliable rows).

Wave 142 adds solver/c12gaps142.py — strict, SymPy-verified
schemas per family (principal-branch inverse trig, vector
algebra, piecewise continuity + find-k, parametric /
implicit / logarithmic differentiation, AoD rates and
word maxima, a minimal area family, conic facts) — wired
through a failure gate in solver/router.py and a
conservative wrong-answer upgrade in fallback.py. It also
adds 24 topics (10 Application of Integrals for C12, 14
Conic Sections fill for C11).

After this wave, on the identical audit population:
Inverse Trig 0/31 (raw rows are extraction-destroyed —
see the transcription tests below), Vectors 17/70
(24.3%), Continuity & Differentiability 39/82 (47.6%),
AoD 43/80 (53.8%), AoI 8/10 (80.0%); total 46/273 ->
107/273, zero previously-solved rows lost.

Raw book rows are quoted verbatim (including the NCERT
extraction's U+02C6 hat glyphs) with their exercise ids.
"""
import pytest

from solver.c12gaps142 import solve_c12gaps, \
    c12gaps142_upgrade


def ans(q):
    got = solve_c12gaps(q)
    return got["answer"] if got else None


_NEW_CONIC_SLUGS = {
    "focus-of-parabola-y2-12x",
    "focus-of-parabola-x2-8y",
    "directrix-of-parabola-y2-minus-8x",
    "latus-rectum-of-parabola-x2-minus-16y",
    "eccentricity-of-ellipse-16-9",
    "foci-of-ellipse-25-9",
    "latus-rectum-of-ellipse-16-9",
    "vertices-of-ellipse-9-25",
    "axes-of-ellipse-16-9",
    "foci-of-hyperbola-16-9",
    "eccentricity-of-hyperbola-16-9",
    "latus-rectum-of-hyperbola-9-16",
    "centre-and-radius-of-a-circle-from-general-form",
    "radius-of-a-circle-from-general-form",
}


# ------------------------------------------------------------------
# 1. Inverse Trigonometric Functions.
# The raw NCERT rows for this chapter are extraction-
# destroyed (fraction brackets scrambled into private-use
# glyphs), so these are faithful transcriptions of the
# same book questions (Ex 2.1 / Ex 2.2 / Miscellaneous).
# Principal-branch care is the point: a wrong-branch
# value is a WRONG answer.
# ------------------------------------------------------------------

def test_invtrig_composite_tan_sec():
    # Ex 2.1 family: tan^-1(sqrt(3)) - sec^-1(-2) = -pi/3.
    a = ans("Find the principal value of "
            "tan^-1(sqrt(3)) - sec^-1(-2)")
    assert a is not None and a.startswith("-pi/3")


def test_invtrig_sec_fraction_branch():
    # sec^-1(2/sqrt(3)) = pi/6 (the primary served pi/3).
    a = ans("Find the principal value of sec^-1(2/sqrt(3))")
    assert a is not None and a.startswith("pi/6")


def test_invtrig_cot_negative_branch():
    # cot^-1(-1/sqrt(3)) = 2pi/3 on the NCERT branch
    # (0, pi) — NOT -pi/3.
    a = ans("Find the principal value of "
            "cot^-1(-1/sqrt(3))")
    assert a is not None and a.startswith("2·pi/3")


def test_invtrig_sum_of_three():
    # tan^-1(1) + cos^-1(-1/2) + sin^-1(-1/2) = 3pi/4.
    a = ans("Find the principal value of tan^-1(1) + "
            "cos^-1(-1/2) + sin^-1(-1/2)")
    assert a is not None and a.startswith("3·pi/4")


def test_invtrig_cos_plus_two_sin():
    # cos^-1(1/2) + 2 sin^-1(1/2) = 2pi/3.
    a = ans("Find the principal value of cos^-1(1/2) + "
            "2sin^-1(1/2)")
    assert a is not None and a.startswith("2·pi/3")


def test_invtrig_equation_misc_q14():
    # NCERT Miscellaneous Ex Q14: sin^-1(1 - x) -
    # 2 sin^-1(x) = pi/2 has the single nice solution 0
    # (x = 1/2 satisfies the squared equation but not
    # the original — the schema verifies exactly).
    assert ans("sin^-1(1-x) - 2sin^-1(x) = pi/2, "
               "then x is equal to") == "x = 0"


# ------------------------------------------------------------------
# 2. Vector Algebra — raw book rows verbatim (jsonl idx
# in comments; the ˆ glyph is U+02C6 as extracted).
# ------------------------------------------------------------------

def test_vectors_equal_find_xy():
    # Ex 10.2 Q4 (idx 3108).
    assert ans("Find the values of x and y so that the "
               "vectors 2iˆ + 3 ˆj and xiˆ + yjˆ are "
               "equal.") == "x = 2, y = 3"


def test_vectors_collinear_hat_glyphs():
    # Ex 10.2 Q11 (idx 3115): b = -2a, so YES — an
    # earlier parse of the leading-minus vector said No.
    assert ans("Show that the vectors 2iˆ − 3 ˆj + 4kˆ "
               "and − 4iˆ + 6 ˆj − 8kˆ are collinear.") \
        == "Yes, the vectors are collinear"


def test_vectors_direction_cosines():
    # Ex 10.2 Q12 (idx 3116).
    assert ans("Find the direction cosines of the vector "
               "iˆ + 2 ˆj + 3kˆ .") == \
        "(sqrt(14)/14, sqrt(14)/7, 3·sqrt(14)/14)"


def test_vectors_midpoint_position():
    # Ex 10.2 Q16 (idx 3120).
    assert ans("Find the position vector of the mid "
               "point of the vector joining the points "
               "P(2, 3, 4) and Q(4, 1, –2).") == \
        "3î + 2ĵ + k̂"


def test_vectors_right_angled_position():
    # Ex 10.2 Q17 (idx 3121).
    assert ans("Show that the points A, B and C with "
               "position vectors, = 3iˆ − 4 ˆj − 4kˆ, "
               "= 2iˆ − ˆj + kˆ and = iˆ − 3 ˆj − 5kˆ , "
               "respectively form the vertices of a "
               "right angled triangle.") == \
        "Yes, it is a right angled triangle"


def test_vectors_collinear_points():
    # Ex 10.3 Q16 (idx 3150).
    assert ans("Show that the points A(1, 2, 7), "
               "B(2, 6, 3) and C(3, 10, –1) are "
               "collinear.") == \
        "Yes, the points are collinear"


def test_vectors_projection_zero():
    # Ex 10.3 Q3 (idx 3137): perpendicular vectors.
    assert ans("Find the projection of the vector "
               "iˆ − ˆj on the vector iˆ + ˆj .") == "0"


def test_vectors_projection_value():
    # Ex 10.3 Q4 (idx 3138): 60/sqrt(114) = 10 sqrt(114)/19.
    assert ans("Find the projection of the vector "
               "iˆ + 3 ˆj + 7kˆ on the vector "
               "7iˆ − ˆj + 8kˆ .") == "10·sqrt(114)/19"


def test_vectors_scalar_triple():
    # Scalar triple product of i+j+k, 2i-j+3k, i+2j-k = 5
    # (the primary served a fragment, "b = 2").
    assert ans("Find the scalar triple product of "
               "vectors a = i + j + k, b = 2i - j + 3k, "
               "c = i + 2j - k") == "5"


def test_vectors_four_position_vectors_decline():
    # Examples, Example 27 (idx 3173): the angle/collinear
    # ask is about AB and CD built from four position
    # vectors, and the extraction lost the vector names —
    # a two-vector verdict here would be a guess.
    assert ans("If iˆ + ˆj + kˆ, 2iˆ + 5 ˆj, 3iˆ + 2 ˆj "
               "− 3kˆ and iˆ − 6 ˆj − kˆ are the position "
               "vectors of points A, B, C and D "
               "respectively, then find the angle between "
               "and . Deduce that and are collinear.") \
        is None


# ------------------------------------------------------------------
# 3. Continuity & Differentiability — raw rows verbatim
# plus the parametric / find-k families.
# ------------------------------------------------------------------

def test_diff_implicit_linear_sin_x():
    # Ex 5.3 Q1 (idx 2775).
    assert ans("dy Find in the following: dx "
               "2x + 3y = sin x") == "cos(x)/3 - 2/3"


def test_diff_implicit_linear_sin_y():
    # Ex 5.3 Q2 (idx 2776).
    assert ans("dy Find in the following: dx "
               "2x + 3y = sin y") == "2/(cos(y) - 3)"


def test_diff_implicit_sin2_cos2():
    # Ex 5.3 Q8 (idx 2782): sin^2 x + cos^2 y = 1 in the
    # extraction's glued-power spelling.
    assert ans("dy Find in the following: dx "
               "sin2 x + cos2 y = 1") == \
        "sin(2·x)/sin(2·y)"


_PARAM_HEAD = ("If x and y are connected parametrically "
               "by the equations given in Exercises 1 "
               "to 10, dy without eliminating the "
               "parameter, Find . dx ")


def test_diff_parametric_at4():
    # Ex 5.6 Q1: x = 2at^2, y = at^4 -> dy/dx = t^2.
    assert ans(_PARAM_HEAD + "x = 2at2, y = at4") == "t^2"


def test_diff_parametric_cos_theta_constants():
    # Ex 5.6 Q2: x = a cos theta, y = b cos theta -> b/a.
    # (Needs the multi-letter argument fix in _fn_parens
    # and the a=1, b=1 numeric verification.)
    assert ans(_PARAM_HEAD + "x = a cos θ, y = b cos θ") \
        == "b/a"


def test_diff_parametric_cycloid():
    # Ex 5.6 Q6: x = a(theta - sin theta),
    # y = a(1 + cos theta) -> sin(theta)/(cos(theta) - 1).
    assert ans(_PARAM_HEAD
               + "x = a (θ – sin θ), y = a (1 + cos θ)") \
        == "sin(theta)/(cos(theta) - 1)"


def test_diff_find_k_continuity():
    # Ex 5.1 find-the-parameter family (clean
    # transcription): LHL 2k + 5 must equal RHL 1.
    assert ans("Find the value of k so that the function "
               "f(x) = kx + 5, if x ≤ 2; x - 1, if x > 2 "
               "is continuous at x = 2") == "k = -2"


def test_diff_find_dydx_of_phrasing():
    # The plain "find dy/dx of" wrapper must be stripped
    # before the pure-math guard sees the expression.
    assert ans("Find dy/dx of x^x - 2^(sin x)") == \
        "-2^sin(x)·log(2)·cos(x) + x^x·(log(x) + 1)"


def test_diff_second_derivative_logx_logx():
    # Ex 5.7 Q7 (idx 2822): y = (log x)^(log x). The
    # second derivative is verified numerically inside
    # the schema (simplify cannot prove the identity);
    # here we pin that it serves at all.
    got = solve_c12gaps(
        "Find the second order derivatives of the "
        "functions given in Exercises 1 to 10. "
        "(log x)log x, x > 1")
    assert got is not None
    assert "log(x)^log(x)" in got["answer"]


def test_diff_prove_question_declines():
    # Ex 5.7 Q15 shape: a prove-that ask must not be
    # answered with a bare dy/dx.
    assert ans("If (x - a)^2 + (y - b)^2 = c^2, for some "
               "c > 0, prove that the derivative is a "
               "constant independent of a and b") is None


# ------------------------------------------------------------------
# 4. Application of Derivatives — raw rows verbatim.
# ------------------------------------------------------------------

def test_aod_circle_circumference_rate():
    # Ex 6.1 Q6 (idx 2863): dC/dt = 2 pi x 0.7.
    assert ans("The radius of a circle is increasing at "
               "the rate of 0.7 cm/s. What is the rate of "
               "increase of its circumference?") == \
        "7·pi/5 cm/s"


def test_aod_balloon_dv_dr():
    # Ex 6.1 Q9 (idx 2866): dV/dr = 4 pi r^2 at r = 10.
    assert ans("A balloon, which always remains "
               "spherical has a variable radius. Find "
               "the rate at which its volume is "
               "increasing with the radius when the "
               "later is 10 cm.") == "400·pi cm^3/cm"


def test_aod_intervals_exp():
    # Ex 6.2 Q2 (idx 2877).
    assert ans("Show that the function given by "
               "f (x) = e2x is increasing on R.") == \
        "increasing in (-∞, ∞)"


def test_aod_abs_maxmin_interval():
    # Ex 6.3 Q7 (idx 2901).
    a = ans("Find both the maximum value and the "
            "minimum value of 3x4 – 8x3 + 12x2 – 48x + "
            "25 on the interval [0, 3].")
    assert a is not None
    assert a.startswith("Maximum value = 25 at x = 0")


def test_aod_sin_plus_cos_max():
    # Ex 6.3 Q9 (idx 2903): amplitude sqrt(2).
    assert ans("What is the maximum value of the "
               "function sin x + cos x?") == "sqrt(2)"


def test_aod_two_numbers_product():
    # Ex 6.3 Q13 (idx 2907).
    assert ans("Find two numbers whose sum is 24 and "
               "whose product is as large as possible.") \
        == "12 and 12"


def test_aod_two_numbers_xy3():
    # Ex 6.3 Q14 (idx 2908): x + y = 60, xy^3 max.
    assert ans("Find two positive numbers x and y such "
               "that x + y = 60 and xy3 is maximum.") == \
        "x = 15, y = 45"


def test_aod_two_numbers_cubes_min():
    # Ex 6.3 Q16 (idx 2910).
    assert ans("Find two positive numbers whose sum is "
               "16 and the sum of whose cubes is "
               "minimum.") == "8 and 8"


def test_aod_isosceles_area_rate():
    # Miscellaneous Ex Q2 (idx 2925): symbolic base b.
    assert ans("The two equal sides of an isosceles "
               "triangle with fixed base b are decreasing "
               "at the rate of 3 cm per second. How fast "
               "is the area decreasing when the two equal "
               "sides are equal to the base ?") == \
        "Decreasing at sqrt(3)·b cm^2/s"


def test_aod_multipart_abs_maxmin_declines():
    # Ex 6.3 Q5 (idx 2899): four functions in one row —
    # serving only part (i) would be a partial answer.
    assert ans("Find the absolute maximum value and "
               "the absolute minimum value of the "
               "following functions in the given "
               "intervals: (i) f (x) = x3, x ∈ [– 2, 2] "
               "(ii) f (x) = sin x + cos x , x ∈ [0, π] "
               "(iii) f (x) = 4 x − x 2 , x ∈ "
               "(iv) f ( x ) = ( x − 1) 2 + 3, x") is None


def test_aod_scrambled_intervals_decline():
    # Miscellaneous Ex 6.3 Q3 (idx 2926): the extraction
    # merged the fraction (4sin x - 2x - x cos x) /
    # (2 + cos x) around the "f (x) =" — parsing what
    # follows "=" as the whole function would answer a
    # different question.
    assert ans("Find the intervals in which the "
               "function f given by 4sin x − 2 x − "
               "x cos x f ( x) = 2 + cos x is "
               "(i) increasing (ii) decreasing.") is None


# ------------------------------------------------------------------
# 5. Application of Integrals + the new topics.
# ------------------------------------------------------------------

def test_aoi_circle_symbolic_area():
    # Examples, Example 1 (idx 3018): the prose must
    # reach the area schema — never an implicit dy/dx.
    assert ans("Find the area enclosed by the circle "
               "x2 + y2 = a2.") == "pi*a^2 sq. units"


def test_aoi_first_quadrant_mcq_row():
    # Ex 8.1 Q3 (idx 3011), options garbled in the
    # extraction; the region itself is unambiguous.
    a = ans("Area lying in the first quadrant and "
            "bounded by the circle x2 + y2 = 4 and the "
            "lines x = 0 and x = 2 is")
    assert a == "pi sq. units"


def test_topics_new_chapters_present():
    from topics_bandc import TOPICS_BANDC
    aoi = [t for t in TOPICS_BANDC[12]
           if t["chapter"] == "application-of-integrals"]
    assert len(aoi) == 10
    conic = [t for t in TOPICS_BANDC[11]
             if t["chapter"] == "conic-sections"]
    assert len(conic) >= 14


def test_topics_new_starters_solve_pure():
    # Every new topic's starter must be served by the
    # solver itself (no AI fallback) with exactly the
    # stored answer.
    from api import _solve_friendly
    from topics_bandc import TOPICS_BANDC
    new = [t for t in TOPICS_BANDC[12]
           if t["chapter"] == "application-of-integrals"]
    # Only this wave's 14 new Conic Sections topics: the
    # one pre-existing band-C conic topic (circle equation
    # from centre/radius) has a stored answer in a
    # different dress than the pipeline serves — a
    # pre-Wave-142 mismatch, not this wave's to pin.
    new += [t for t in TOPICS_BANDC[11]
            if t["chapter"] == "conic-sections"
            and t["slug"] in _NEW_CONIC_SLUGS]
    for t in new:
        got = _solve_friendly(t["starter"], lang=None,
                              student_class=12)
        assert not got.get("fallback"), t["slug"]
        assert got.get("fallback_kind") is None, t["slug"]
        assert got.get("answer") == t["answer"], t["slug"]


# ------------------------------------------------------------------
# 6. Pipeline: hijack repairs, the upgrade seam, and
# unchanged neighbours.
# ------------------------------------------------------------------

def test_pipeline_area_not_derivative():
    from api import _solve_friendly
    got = _solve_friendly(
        "Find the area enclosed by the circle "
        "x2 + y2 = a2.", lang=None, student_class=12)
    assert got.get("answer") == "pi*a^2 sq. units"


def test_pipeline_dydx_upgrade_replaces_integral_mess():
    from api import _solve_friendly
    got = _solve_friendly("Find dy/dx of x^x - 2^(sin x)",
                          lang=None, student_class=12)
    assert got.get("answer") == \
        "-2^sin(x)·log(2)·cos(x) + x^x·(log(x) + 1)"


def test_upgrade_integral_answer_replaced():
    mine = c12gaps142_upgrade(
        "Find dy/dx of x^x - 2^(sin x)",
        {"answer": "derivative: x·x^x; integral: "
                   "Integral(x^x) + C", "value": None})
    assert mine is not None
    assert mine["answer"].startswith("-2^sin(x)")


def test_upgrade_truncated_variant_replaced():
    # The primary served "b" for the Ex 5.6 Q2 parametric
    # question; the verified exact form is "b/a".
    mine = c12gaps142_upgrade(
        _PARAM_HEAD + "x = a cos θ, y = b cos θ",
        {"answer": "b", "value": None})
    assert mine is not None
    assert mine["answer"] == "b/a"


def test_pipeline_neighbour_hcf_unchanged():
    from api import _solve_friendly
    got = _solve_friendly("Find HCF of 135 and 225",
                          lang=None, student_class=12)
    assert got.get("answer") == "45"


def test_pipeline_neighbour_invtrig_unchanged():
    from api import _solve_friendly
    got = _solve_friendly("sin^-1(-1/2) ka maan batao",
                          lang=None, student_class=12)
    assert got.get("answer", "").startswith("-pi/6")
