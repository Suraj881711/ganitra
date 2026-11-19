"""Wave 187: vector algebra in plain phone-typed (ASCII)
notation — form-audit top-10 item #2 (probe 16).

BEFORE (measured on main, Deploy-46 state): the audit probe

    "Find the angle between the vectors a = 2i + 3j - k
     and b = i - j + 2k"

died with a complex parse error (bare `i` read as I), and
the rest of the ASCII family either errored the same way
(dot / cross / scalar / vector product, direction ratios,
lambda dresses, a + b with named defs, |a|) or was served
FRAGMENTS by the geometry intent: the magnitude of
2i + 3j - k as 3.60555 (sqrt(13), a component dropped),
its unit vector as a 2D decimal pair, the dot product of
-i + 2j and 3i - j as 0 (correct: -5), an explicit
"vector projection" ask with the SCALAR projection, and a
combined ratios+cosines ask with the cosines alone.

Fix: solver/vectors187.py — strict ASCII schemas on a
per-term-sign literal parser (the shared vectors.py parser
negates a whole sum for a leading minus: -i + 2j read as
(-1, -2)), gated by real vector evidence (a j or k
component, or an explicit vector word) so complex-number
questions are never hijacked.  Wiring: the house
failure-only late gate after Wave 175, a Wave 172-style
exception inside the pre-intent geometry block, a Wave
171-style check inside the Wave 77 core block, a scoped
precedence block before the Wave 142 gate for the two
explicit wrong-form dresses, and a tail fragment-repair
block.  Every expected value below was verified
independently (hand dot/cross computation cross-checked
with SymPy) before pinning.
"""
from solver.router import solve_question
from solver.vectors187 import (repair_vectors187,
                               solve_vectors187)

PROBE16 = ("Find the angle between the vectors "
           "a = 2i + 3j - k and b = i - j + 2k")
A = "2i + 3j - k"      # (2, 3, -1): |a| = sqrt(14)
B = "i - j + 2k"       # (1, -1, 2): |b| = sqrt(6), a.b = -3


def ans(q):
    out = solve_question(q)
    assert out is not None, q
    return out


def schema_ans(q):
    out = solve_vectors187(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_vectors187(q) is None, q


# ------------------------------------------------------------------
# Audit probe 16, verbatim
# ------------------------------------------------------------------

def test_probe16_angle_between_defs():
    out = ans(PROBE16)
    assert out["op"] == "angle_between"
    assert out["answer"] == "cos θ = -sqrt(21)/14"
    # a.b = 2 - 3 - 2 = -3, |a| = sqrt(14), |b| = sqrt(6),
    # cos = -3/sqrt(84) = -sqrt(21)/14, theta ~ 109.1 deg.
    assert any("109.1" in s for s in out["steps"])


def test_probe16_answer_matches_unicode_dress():
    out = ans("Find the angle between the vectors "
              "a = 2î + 3ĵ - k̂ and b = î - ĵ + 2k̂")
    assert out["answer"] == "cos θ = -sqrt(21)/14"


def test_angle_bare_literals_no_spaces():
    out = ans(f"Find the angle between the vectors "
              f"2i+3j-k and i-j+2k")
    assert out["answer"] == "cos θ = -sqrt(21)/14"


def test_angle_leading_minus_standard_degrees():
    # a = (-1, 2, 0), b = (3, -1, 0): dot = -5,
    # cos = -5/sqrt(50) = -sqrt(2)/2 -> 135 degrees.
    out = ans("Find the angle between vectors "
              "a = -i + 2j and b = 3i - j")
    assert out["answer"] == "θ = 135°"


def test_angle_antiparallel_and_perpendicular():
    out = ans("Find the angle between the vectors "
              "a = -i + 2j and b = i - 2j")
    assert out["answer"] == "θ = 180°"
    out = ans("Find the angle between the vectors "
              "a = i + j and b = i - j")
    assert out["answer"] == "θ = 90°"


def test_angle_with_itself():
    out = ans(f"Find the angle between the vectors "
              f"a = {A} and b = {A}")
    assert out["answer"] == "θ = 0°"


def test_angle_zero_components():
    # a = (2, 0, -1), b = (1, -1, 0): dot = 2,
    # cos = 2/sqrt(10) = sqrt(10)/5.
    out = ans("Find the angle between the vectors "
              "a = 2i + 0j - k and b = i - j + 0k")
    assert out["answer"] == "cos θ = sqrt(10)/5"


# ------------------------------------------------------------------
# Magnitude / unit vector (incl. the geometry fragments)
# ------------------------------------------------------------------

def test_magnitude_fragment_repaired():
    out = ans(f"Find the magnitude of the vector {A}")
    assert out["answer"] == "sqrt(14)"  # was 3.60555


def test_magnitude_named_def_fragment_repaired():
    out = ans("Find the magnitude of vector a = 2i - j + 2k")
    assert out["answer"] == "3"  # was 2.82843


def test_magnitude_dresses():
    assert ans(f"Find the magnitude of {A}")["answer"] \
        == "sqrt(14)"
    assert ans(f"Find |{A}|")["answer"] == "sqrt(14)"
    assert ans("Find |a| if a = 3i - 4j")["answer"] == "5"
    assert ans(f"Find the modulus of the vector {A}")[
        "answer"] == "sqrt(14)"
    assert ans("Find the magnitude of the vector "
               "i - 2j + k")["answer"] == "sqrt(6)"
    assert ans("Find the magnitude of the vector "
               "-i + 2j")["answer"] == "sqrt(5)"
    assert ans("Find the magnitude of the vector "
               "0i + 3j - 4k")["answer"] == "5"


def test_magnitude_correct_geometry_serve_stands():
    # Geometry serves sqrt(17) correctly here (4.12311);
    # the repair must NOT displace a correct answer.
    out = ans("Find the magnitude of the vector "
              "2i + 3j - 2k")
    assert out["answer"] in ("4.12311", "sqrt(17)")


def test_unit_vector_fragment_repaired():
    out = ans(f"Find a unit vector in the direction of "
              f"the vector {A}")
    assert out["answer"] == \
        "sqrt(14)/7î + 3·sqrt(14)/14ĵ - sqrt(14)/14k̂"
    out = ans("Find the unit vector in the direction of "
              "a = i - 2j + k")
    assert out["answer"] == \
        "sqrt(6)/6î - sqrt(6)/3ĵ + sqrt(6)/6k̂"  # was '-1j'


def test_unit_vector_integer_magnitude_form():
    out = ans("Find a unit vector in the direction of "
              "2i - 2j + k")
    assert out["answer"] == "(1/3)(2î - 2ĵ + k̂)"


def test_unit_vector_leading_minus():
    out = ans("Find a unit vector in the direction of "
              "-2i + 3j - k")
    assert out["answer"] == \
        "-sqrt(14)/7î + 3·sqrt(14)/14ĵ - sqrt(14)/14k̂"


# ------------------------------------------------------------------
# Dot / cross / scalar / vector product, named expressions
# ------------------------------------------------------------------

def test_dot_and_cross_product():
    assert ans(f"Find the dot product of {A} and {B}")[
        "answer"] == "-3"
    assert ans(f"Find the cross product of {A} and {B}")[
        "answer"] == "5î - 5ĵ - 5k̂"
    assert ans(f"Find the scalar product of the vectors "
               f"{A} and {B}")["answer"] == "-3"
    assert ans(f"Find the vector product of the vectors "
               f"{A} and {B}")["answer"] == "5î - 5ĵ - 5k̂"


def test_dot_product_leading_minus_fragment_repaired():
    # Geometry served 0; correct: (-1)(3) + (2)(-1) = -5.
    out = ans("Find the dot product of -i + 2j and 3i - j")
    assert out["answer"] == "-5"


def test_named_expressions():
    base = f"If a = {A} and b = {B}"
    assert ans(base + ", find a + b")["answer"] == \
        "3î + 2ĵ + k̂"
    assert ans(base + " then find a . b")["answer"] == "-3"
    assert ans(base + " then find a x b")["answer"] == \
        "5î - 5ĵ - 5k̂"


# ------------------------------------------------------------------
# Projection: scalar keeps its serve, vector form is served
# ------------------------------------------------------------------

def test_scalar_projection_unchanged():
    out = ans(f"Find the projection of the vector {A} on "
              f"the vector {B}")
    assert out["answer"] == "-sqrt(6)/2"
    out = ans("Find the scalar projection of a on b if "
              f"a = {A} and b = {B}")
    assert out["answer"] == "-sqrt(6)/2"


def test_vector_projection_explicit():
    # ((a.b)/|b|^2) b = (-3/6)(1, -1, 2) = (-1/2, 1/2, -1)
    out = ans(f"Find the vector projection of {A} on {B}")
    assert out["op"] == "vector_projection"
    assert out["answer"] == "-1/2î + 1/2ĵ - k̂"
    out = ans("Find the projection vector of a on b "
              f"where a = {A} and b = {B}")
    assert out["answer"] == "-1/2î + 1/2ĵ - k̂"


# ------------------------------------------------------------------
# Collinear / parallel / perpendicular checks
# ------------------------------------------------------------------

def test_parallel_and_collinear_checks():
    out = ans(f"Show that the vectors {A} and "
              "4i + 6j - 2k are parallel")
    assert out["answer"] == "Yes, the vectors are parallel"
    out = ans(f"Are the vectors {A} and {B} collinear")
    assert out["answer"] == \
        "No, the vectors are not collinear"
    out = ans("Show that the vectors -2i + 3j - k and "
              "4i - 6j + 2k are parallel")
    assert out["answer"] == "Yes, the vectors are parallel"
    out = ans(f"Show that the vectors {A} and "
              "4i + 6j - 2k are collinear")
    assert out["answer"] == "Yes, the vectors are collinear"


def test_collinear_points():
    out = ans("Check whether the points A(1, 2, 3), "
              "B(2, 3, 4) and C(3, 4, 5) are collinear")
    assert out["answer"] == "Yes, the points are collinear"
    out = solve_vectors187(
        "Check whether the points A(1, 2, 3), B(2, 3, 4) "
        "and C(3, 4, 6) are collinear")
    assert out["answer"] == "No, the points are not " \
                             "collinear"


def test_perpendicular_check():
    out = ans("Show that the vectors i + j and i - j "
              "are perpendicular")
    assert out["answer"] == \
        "Yes, the vectors are perpendicular"
    out = ans(f"Are the vectors {A} and {B} perpendicular")
    assert out["answer"] == \
        "No, the vectors are not perpendicular"


# ------------------------------------------------------------------
# Lambda / unknown forms
# ------------------------------------------------------------------

def test_perpendicular_lambda_dresses():
    # a.b = 2 + 3*lambda - 2 = 3*lambda -> lambda = 0.
    out = ans("Find lambda so that the vectors "
              f"{A} and i + lambda j + 2k are perpendicular")
    assert out["answer"] == "lambda = 0"
    out = ans("For what value of lambda are the vectors "
              f"{A} and i + lambda j + 2k perpendicular")
    assert out["answer"] == "lambda = 0"


def test_perpendicular_lambda_named_dress_unchanged():
    # Wave 142 already served this dress; it must stand.
    out = ans("Find the value of lambda for which the "
              f"vectors a = {A} and b = i + lambda j + 2k "
              "are perpendicular")
    assert out["answer"] == "lambda = 0"
    out = ans("Find the value of lambda for which the "
              "vectors a = -i + 2j and b = 3i + lambda j "
              "are perpendicular")
    assert out["answer"] == "lambda = 3/2"


def test_perpendicular_unknown_letter():
    # a.b = 2x - 3 - 2 = 0 -> x = 5/2.
    out = ans(f"Find x so that the vectors {A} and "
              "xi - j + 2k are perpendicular")
    assert out["answer"] == "x = 5/2"


def test_parallel_lambda():
    # (4, 6, lambda) = 2*(2, 3, -1) -> lambda = -2.
    out = ans("Find the value of lambda for which vectors "
              f"{A} and 4i + 6j + lambda k are parallel")
    assert out["answer"] == "lambda = -2"
    # (2, lambda, -1) parallel (4, 2, -2) -> lambda = 1.
    out = ans("Find lambda if the vectors "
              "2i + lambda j - k and 4i + 2j - 2k "
              "are parallel")
    assert out["answer"] == "lambda = 1"
    # (x, 6, -2) parallel (2, 3, -1) -> x = 4.
    out = ans(f"Find x if the vectors {A} and "
              "xi + 6j - 2k are parallel")
    assert out["answer"] == "x = 4"


def test_parallel_lambda_no_solution_is_honest():
    # cross has a constant -5 component: no lambda works.
    out = ans("Find lambda if the vectors "
              "2i + lambda j - k and i - j + 2k are parallel")
    assert out["answer"] == \
        "No value of lambda makes the vectors parallel"


# ------------------------------------------------------------------
# Direction ratios / cosines
# ------------------------------------------------------------------

def test_direction_ratios():
    out = ans(f"Find the direction ratios of the vector {A}")
    assert out["answer"] == "(2, 3, -1)"


def test_direction_cosines_unchanged():
    out = ans(f"Find the direction cosines of the "
              f"vector {A}")
    assert out["answer"] == \
        "(sqrt(14)/7, 3·sqrt(14)/14, -sqrt(14)/14)"


def test_direction_ratios_and_cosines_combined():
    out = ans(f"Find direction ratios and direction "
              f"cosines of the vector {A}")
    assert out["answer"] == \
        "Direction ratios: (2, 3, -1), Direction cosines: " \
        "(sqrt(14)/7, 3·sqrt(14)/14, -sqrt(14)/14)"


# ------------------------------------------------------------------
# Hinglish / Hindi dresses (vectors.py's own triggers)
# ------------------------------------------------------------------

def test_hinglish_dresses():
    out = ans("do sadishon ke beech ka kon nikalo "
              f"a = {A} aur b = {B}")
    assert out["answer"] == "cos θ = -sqrt(21)/14"
    out = ans(f"sadish {A} ka pariman nikalo")
    assert out["answer"] == "sqrt(14)"
    out = ans(f"{A} ki disha me ikai sadish nikalo")
    assert out["op"] == "unit_vector"


def test_devanagari_dresses():
    out = ans("दो सदिशों के बीच का कोण निकालो "
              f"a = {A} और b = {B}")
    assert out["answer"] == "cos θ = -sqrt(21)/14"
    out = ans(f"सदिश {A} का परिमाण निकालो")
    assert out["answer"] == "sqrt(14)"


# ------------------------------------------------------------------
# Controls: complex numbers and other i-questions NEVER hijacked
# ------------------------------------------------------------------

def test_complex_family_declines_schema():
    for q in ("(2 + 3i)(1 - i)",
              "Find the modulus of 3 + 4i",
              "Express 2 + 3i in a + ib form",
              "Find the conjugate of 3 - 4i",
              "Simplify (1 + i)^2",
              "Find the value of i + i",
              "What is i^2",
              "Find the argument of 1 + i",
              "If z = 3 + 4i find |z|",
              "Multiply 2i by 3i"):
        declines(q)


def test_complex_family_router_outcomes_unchanged():
    assert ans("(2 + 3i)(1 - i)")["answer"] == "5 + I"
    assert ans("Find the modulus of 3 + 4i")["answer"] == "5"
    assert ans("Find the conjugate of 3 - 4i")["answer"] \
        == "3 + 4·I"
    assert ans("Simplify (1 + i)^2")["answer"] == "2·I"
    assert ans("Find the value of i + i")["answer"] == "2·I"
    assert ans("What is i^2")["answer"] == "-1"
    assert ans("Multiply 2i by 3i")["answer"] == "-6"
    assert ans("Find the argument of 1 + i")["answer"] \
        == "pi/4 rad ≈ 0.7854"
    out = ans("If z = 3 + 4i find |z|")
    assert out["op"] == "error"  # still the fallback's job


def test_non_vector_i_words_unchanged():
    assert ans("Find sin 30 degrees")["answer"] == "1/2"
    out = ans("What is the unit of force")
    assert out["op"] == "error"
    assert ans("Differentiate sin x with respect to x")[
        "answer"] == "cos(x)"


def test_unicode_dress_unchanged():
    out = ans("Find a unit vector in the direction of "
              "2î - ĵ + 2k̂")
    assert out["answer"] == "(1/3)(2î - ĵ + 2k̂)"


def test_already_solving_ascii_unchanged():
    out = ans(f"Find the scalar projection of a on b "
              f"if a = {A} and b = {B}")
    assert out["answer"] == "-sqrt(6)/2"
    out = ans("Find the area of the parallelogram whose "
              f"adjacent sides are {A} and {B}")
    assert out["answer"] == "5·sqrt(3) sq. units"
    out = ans("Find the position vector of the midpoint "
              "of the line joining the points (1, 2, 3) "
              "and (3, 4, 5)")
    assert out["answer"] == "(2, 3, 4)"


def test_multi_intent_declines():
    # Angle AND dot product in one question: a multi-part
    # ask is not ours to half-serve.
    declines(PROBE16 + " and also find their dot product")


def test_magnitude_given_not_asked_declines():
    # "A vector of magnitude 5 in the direction of ..." —
    # the magnitude is GIVEN (Wave 142's family); serving
    # |literal| would be a wrong answer.
    declines("Find a vector of magnitude 5 in the "
             "direction of 2i + 3j - k")


def test_repair_only_displaces_wrong_serves():
    wrong = {"type": "geometry", "op": "vector magnitude",
             "answer": "3.60555", "steps": []}
    out = repair_vectors187(
        f"Find the magnitude of the vector {A}", wrong)
    assert out is not None
    assert out["answer"] == "sqrt(14)"
    right = {"type": "geometry", "op": "vector magnitude",
             "answer": "4.12311", "steps": []}
    assert repair_vectors187(
        "Find the magnitude of the vector 2i + 3j - 2k",
        right) is None
    other = {"type": "arithmetic", "op": "evaluate",
             "answer": "5", "steps": []}
    assert repair_vectors187("(2 + 3i)(1 - i)", other) \
        is None
