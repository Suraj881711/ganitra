"""Wave 100: the Wave 93 audit's seven regressions, fixed at
the root cause.

The Wave 93 re-run of the Wave 71 battery (3,631 questions
through api._solve_friendly) found exactly seven questions
that were SOLVED in Wave 71 and failing after Waves 75-82+92:

  1. "x + 1/x = 3 … value of a - b + c is: (A) 5 (B) 2
     (C) 1 (D) -1" — served the Quadratic Formula CONCEPT
     card. Root cause, found by inspection: the topics layer
     (concept_topics) correctly VETOES options-bearing
     questions, but the older concepts.py card behind it
     (fallback._concept_result) had no such veto, and the
     MCQ layer could not read the stem's "expressed in the
     form ax^2 + bx + c = 0" shape. Fixes: a coefficient-form
     stem schema in mcq.py, and the concept layers now YIELD
     to any options-bearing question in with_fallback.
  2. Hindi diff-eq degree MCQ — ERROR_TIMEOUT. The ask is a
     fact about the equation's text, but solve_calculus sent
     it to dsolve, whose classify_ode factorisation explodes
     on the y·(y')² shape and burned the 10 s budget twice.
     Fix: order/degree are read off the text by inspection
     (solver/calculus.ode_order_degree) and answered before
     dsolve is ever consulted.
  3. Discus-throw case study — NOT_FOUND. No layer split
     the passage + sub-questions format (Wave 82's formats
     module never landed in the main tree). Fix: the case-
     study splitter in multipart.py, a tangent-from-angle
     schema in solver/geometry.py, and the MCQ layer no
     longer mistakes imperative sub-questions ("(a) Find
     the length of AB…") for answer options (that mistake
     alone burned ~19 s per case study).
  4. Zeroes "Hence, …" two-parter — NOT_FOUND. The second
     sentence poisoned the first's parse and nothing
     carried part 1's zeroes into part 2. Fix: the Hence
     chain in multipart.py (zeroes -> transformed zeroes ->
     the new polynomial from sum and product).
  5. ICSE 15-part mega-MCQ — ERROR_TIMEOUT / fragment.
     Treated as one question, a fragment of part (iv) was
     served ("x = -2/7"). Fix: the mega-bundle splitter in
     multipart.py (parts are the authority — it also sits
     in the real-result branch), per-part Wave 100 schemas
     for the board staples (nature of roots, RD maturity,
     probability range, matrix powers, dividend par, GST,
     integer inequality sets, sphere ratios, origin lines,
     common factors, similar triangles), and a soft budget
     so unsolved parts are marked, never hung on.
  6. "f : N -> N, f(x) = 2x is (A) one-one and onto …" —
     NOT_FOUND. Fix: the function-type claim schema in
     mcq.py (linear/monomial classification, exact).
  7. "O is the centre, ∠AOB = 30°, find ∠OBA" — NOT_FOUND.
     The facts are all in the text; no schema read them.
     Fix: the radii-isosceles schema in solver/geometry.py
     (plus a router geometry-first hook for "centre of the
     circle" texts).

Guards: genuine concept asks still get topics answers
(Wave 75/81 behaviour), ordinary MCQs and equations are
untouched, an option is still never guessed, and the
bundle/case-study/Hence detectors do not fire on ordinary
questions.
"""
import pytest

from api import _solve_friendly
from concept_topics import topic_concept_result
from mcq import extract_mcq, mcq_result
from multipart import (split_case_study, split_hence,
                       split_mega_bundle)
from solver.calculus import ode_order_degree
from solver.geometry import solve_geometry

REG1 = ("The equation x + 1/x = 3 (x ≠ 0) is expressed as "
        "a quadratic equation in the form ax2 + bx + c = 0. "
        "The value of a - b + c is: (A) 5 (B) 2 (C) 1 (D) -1")
REG2 = ("अवकल समीकरण x·(d²y/dx²) + xy(dy/dx)² − xy(dy/dx) = 0 "
        "का घात है (a) 1 (b) 2 (c) 0 (d) इनमें से कोई नहीं")
REG3 = ("The discus throw is an event in which an athlete "
        "attempts to throw a discus. The athlete spins "
        "anti-clockwise around one and a half times through "
        "a circle, then releases the throw. When released, "
        "the discus travels along the tangent to the "
        "circular spin orbit. In the given figure, AB is one "
        "such tangent to a circle of radius 75 cm. Point O "
        "is the centre of the circle and ∠ABO = 30°. PQ is "
        "parallel to OA. Based on the above information, "
        "answer the following questions: (a) Find the length "
        "of AB. (b) Find the length of OB. (c) Find the "
        "length of AP. OR Find the length of PQ.")
REG4 = ("Find the zeroes of the polynomial p(x) = 3x² − 4x "
        "− 4. Hence, write a polynomial whose each of the "
        "zeroes is 2 more than the zeroes of p(x).")
REG5 = ("Choose the correct answers to the questions from "
        "the given options. (Do not copy the questions, "
        "write the correct answers only.) "
        "(i) The given quadratic equation 3x² + √7x + 2 = 0 "
        "has: (a) two equal real roots. (b) two distinct "
        "real roots. (c) more than two real roots. (d) no "
        "real roots. "
        "(ii) Mr. Anuj deposits ₹500 per month for 18 months "
        "in a recurring deposit account at a certain rate. "
        "If he earns ₹570 as interest at the time of "
        "maturity, then his matured amount is: "
        "(a) ₹(500 × 18 + 570) (b) ₹(500 × 19 + 570) "
        "(c) ₹(500 × 18 × 19 + 570) (d) ₹(500 × 9 × 19 + 570) "
        "(iii) Which of the following cannot be the "
        "probability of any event? (a) 5/4 (b) 0.25 "
        "(c) 1/33 (d) 67% "
        "(iv) The equation of the line passing through "
        "origin and parallel to the line 3x + 4y + 7 = 0 "
        "is: (a) 3x + 4y + 5 = 0 (b) 4x − 3y − 5 = 0 "
        "(c) 4x − 3y = 0 (d) 3x + 4y = 0 "
        "(v) If A = [[0, 1], [1, 0]], then A² is equal to: "
        "(a) [[1, 1], [0, 0]] (b) [[0, 0], [1, 1]] "
        "(c) [[1, 0], [0, 1]] (d) [[0, 1], [1, 0]] "
        "(vi) In the given diagram, chords AC and BC are "
        "equal. If ∠ACD = 120°, then ∠AEC is: (a) 30° "
        "(b) 60° (c) 90° (d) 120° "
        "(vii) The factor common to the two polynomials "
        "x² − 4 and x³ − x² − 4x + 4 is: (a) (x + 1) "
        "(b) (x − 1) (c) (x − 2) (d) (x − 4) "
        "(viii) A man invested in a company paying 12% "
        "dividend on its share. If the percentage return "
        "on his investment is 10%, then the shares are: "
        "(a) at par (b) below par (c) above par "
        "(d) cannot be determined "
        "(ix) Statement 1: The point which is equidistant "
        "from three non-collinear points D, E and F is the "
        "circumcentre of the ΔDEF. Statement 2: The "
        "incentre of a triangle is the point where the "
        "bisector of the angles intersects. (a) Both the "
        "statements are true. (b) Both the statements are "
        "false. (c) Statement 1 is true, and Statement 2 "
        "is false. (d) Statement 1 is false, and Statement "
        "2 is true. "
        "(x) Assertion (A): If sin²A + sinA = 1 then "
        "cos⁴A + cos²A = 1 Reason (R): 1 − sin²A = cos²A "
        "(a) (A) is true, (R) is false. (b) (A) is false, "
        "(R) is true. (c) Both (A) and (R) are true, and "
        "(R) is the correct reason for (A). (d) Both (A) "
        "and (R) are true, and (R) is the incorrect reason "
        "for (A). "
        "(xi) In the given diagram ΔABC ~ ΔEFG. If ∠ABC = "
        "∠EFG = 60°, then the length of the side FG is: "
        "(In the diagram, AB = 15 cm, BC = 3 cm and "
        "FE = 75 cm.) (a) 15 cm (b) 20 cm (c) 25 cm "
        "(d) 30 cm "
        "(xii) If the volume of two spheres is in the "
        "ratio 27 : 64, then the ratio of their radii is: "
        "(a) 3 : 4 (b) 4 : 3 (c) 9 : 16 (d) 16 : 9 "
        "(xiii) The marked price of an article is ₹1375. "
        "If the CGST is charged at a rate of 4%, then the "
        "price of the article including GST is: (a) ₹55 "
        "(b) ₹110 (c) ₹1430 (d) ₹1485 "
        "(xiv) The solution set for 0 < −x/3 < 2, x ∈ Z "
        "is: (a) {−5, −4, −3, −2, −1} (b) {−6, −5, −4, "
        "−3, −2, −1} (c) {−5, −4, −3, −2, −1, 0} "
        "(d) {−6, −5, −4, −3, −2, −1, 0} "
        "(xv) Assertion (A): The mean of first 9 natural "
        "numbers is 4.5. Reason (R): Mean = (Sum of all "
        "the observations)/(Total number of observations) "
        "(a) (A) is true, (R) is false. (b) (A) is false, "
        "(R) is true. (c) Both (A) and (R) are true, and "
        "(R) is the correct reason for (A). (d) Both (A) "
        "and (R) are true, and (R) is the incorrect reason "
        "for (A).")
REG6 = ("Function f : N → N, f(x) = 2x is (A) one-one and "
        "onto (B) one-one but not onto (C) onto but not "
        "one-one (D) None of these")
REG7 = ("In the given figure point O is the centre of the "
        "circle and ∠AOB = 30° then the value of ∠OBA is "
        "(A) 30° (B) 60° (C) 75° (D) 90°")


# --- Regression 1: coefficient form + the concept yield ------

def test_reg1_mcq_schema_solves():
    out = mcq_result(REG1)
    assert out is not None
    assert out["answer"] == "(A) 5"
    assert out["op"] == "quadratic_coefficients"


def test_reg1_end_to_end_not_a_concept_card():
    out = _solve_friendly(REG1)
    assert out["answer"] == "(A) 5"
    assert out.get("fallback_kind") != "concept"
    assert "Quadratic Formula" not in out["answer"]


def test_reg1_topics_layer_still_vetoes():
    assert topic_concept_result(REG1) is None


def test_concept_layers_yield_to_options_bearing_questions():
    # An unsolvable MCQ whose words name a concept must get
    # the honest not-found line now, never a concept card.
    q = ("Which of the following is the quadratic formula "
         "used for? (A) Area of a circle (B) Roots of a "
         "quadratic equation (C) Volume of a cube "
         "(D) Speed of a train")
    out = _solve_friendly(q)
    assert out.get("fallback_kind") == "not_found"


def test_coeff_form_variant():
    out = mcq_result(
        "The equation x - 1/x = 4 (x ≠ 0) is expressed as a "
        "quadratic equation in the form ax2 + bx + c = 0. "
        "The value of a + b + c is: (A) -4 (B) 4 (C) -2 "
        "(D) 6")
    assert out is not None
    # x^2 - 4x - 1 = 0 -> a + b + c = 1 - 4 - 1 = -4
    assert out["answer"] == "(A) -4"


# --- Regression 2: order / degree by inspection --------------

def test_ode_order_degree_scan():
    assert ode_order_degree(REG2) == (2, 1)
    assert ode_order_degree(
        "[1 + (dy/dx)^2]^3 = d2y/dx2") == (2, 1)
    assert ode_order_degree("dy/dx + y = x") == (1, 1)
    assert ode_order_degree("2 + 2 = ?") is None


def test_ode_degree_undefined_inside_transcendental():
    order, degree = ode_order_degree(
        "sin(dy/dx) + y = 0, differential equation")
    assert order == 1
    assert degree is None


def test_reg2_end_to_end():
    out = _solve_friendly(REG2)
    assert out["answer"] == "(a) 1"


def test_ode_solve_asks_still_solve():
    from solver.calculus import solve_calculus
    out = solve_calculus("Solve the differential equation "
                         "dy/dx = 2x")
    assert out is not None
    assert out["op"] == "differential_equation"


def test_ode_fact_schema_in_mcq_layer():
    out = mcq_result(REG2)
    assert out is not None
    assert out["answer"] == "(a) 1"


# --- Regression 3: case study --------------------------------

def test_imperative_subquestions_are_not_options():
    assert extract_mcq(REG3) is None


def test_case_study_split():
    got = split_case_study(REG3)
    assert got is not None
    passage, parts = got
    assert "radius 75" in passage
    assert [lab for lab, _a in parts] == ["a", "b", "c"]
    assert len(parts[2][1]) == 2  # (c) carries its OR


def test_reg3_end_to_end():
    out = _solve_friendly(REG3)
    assert out.get("source") == "multipart"
    assert "75√3" in out["answer"]
    assert "150 cm" in out["answer"]
    steps = "\n".join(out["steps"])
    assert "(c) Answer not found." in steps


def test_case_study_needs_the_cue():
    q = ("(a) Find the HCF of 12 and 18. (b) Find the LCM "
         "of 12 and 18.")
    assert split_case_study(q) is None


# --- Regression 4: Hence chains ------------------------------

def test_hence_split():
    got = split_hence(REG4)
    assert got is not None
    assert "3x²" in got[0]
    assert "2 more" in got[1]


def test_reg4_end_to_end():
    out = _solve_friendly(REG4)
    assert out.get("source") == "multipart"
    assert "3x^2 - 16x + 16" in out["answer"]
    assert "-2/3" in out["answer"]


def test_hence_chain_reciprocal_variant():
    out = _solve_friendly(
        "Find the zeroes of the polynomial p(x) = x² - 3x "
        "- 4. Hence, write a polynomial whose zeroes are "
        "reciprocals of the zeroes of p(x).")
    assert out.get("source") == "multipart"
    # zeroes 4 and -1 -> reciprocals 1/4 and -1 -> sum -3/4,
    # product -1/4 -> 4x^2 + 3x - 1
    assert "4x^2 + 3x - 1" in out["answer"]


def test_hence_needs_zeroes_context():
    q = ("Prove that the sum of angles of a triangle is "
         "180°. Hence, show that the exterior angle equals "
         "the sum of the opposite interior angles.")
    from multipart import multipart_result
    assert multipart_result(q) is None


# --- Regression 5: the mega bundle ---------------------------

def test_mega_bundle_split():
    parts = split_mega_bundle(REG5)
    assert parts is not None
    assert len(parts) == 15
    assert parts[0][0] == "i"
    assert parts[-1][0] == "xv"


def test_mega_bundle_needs_three_parts():
    q = ("(i) What is 2 + 2? (a) 3 (b) 4 (ii) What is "
         "3 + 3? (a) 5 (b) 6")
    assert split_mega_bundle(q) is None


def test_reg5_end_to_end():
    out = _solve_friendly(REG5)
    assert out.get("source") == "multipart"
    info = out["multipart"]
    assert info["total"] == 15
    for lab in ("i", "ii", "iii", "iv", "v", "vii", "viii",
                "xi", "xii", "xiii", "xiv"):
        assert lab in info["solved"], lab
    for lab in ("vi", "ix", "x", "xv"):
        assert lab not in info["solved"], lab
    assert "-2/7" not in out["answer"]
    assert "(i) (d)" in out["answer"]
    assert "(xiii) (d)" in out["answer"]


# --- Regression 6: function type -----------------------------

def test_reg6_end_to_end():
    out = _solve_friendly(REG6)
    assert out["answer"] == "(B) one-one but not onto"


def test_function_type_variants():
    out = mcq_result(
        "Function f : R → R, f(x) = 2x is (A) one-one and "
        "onto (B) one-one but not onto (C) onto but not "
        "one-one (D) None of these")
    assert out["answer"].startswith("(A)")
    out = mcq_result(
        "Function f : R → R, f(x) = x^2 is (A) one-one and "
        "onto (B) one-one but not onto (C) onto but not "
        "one-one (D) neither one-one nor onto")
    assert out["answer"].startswith("(D)")


# --- Regression 7: radii isosceles ---------------------------

def test_reg7_end_to_end():
    out = _solve_friendly(REG7)
    assert out["answer"] == "(C) 75°"


def test_radii_angle_reverse_direction():
    out = solve_geometry(
        "Point O is the centre of the circle and ∠OBA = "
        "30° then find ∠AOB")
    assert out["answer"] == "120°"


def test_radii_angle_needs_centre_fact():
    out = solve_geometry(
        "In a triangle ∠AOB = 30° then the value of ∠OBA "
        "is")
    assert out["op"] == "unknown"


# --- Wave 100 schemas: spot variants -------------------------

def test_nature_of_roots_equal():
    out = mcq_result(
        "The given quadratic equation x² - 6x + 9 = 0 has: "
        "(a) two equal real roots (b) two distinct real "
        "roots (c) no real roots (d) more than two real "
        "roots")
    assert out["answer"].startswith("(a)")


def test_rd_maturity_variant():
    out = mcq_result(
        "Ritu deposits ₹200 per month for 12 months in a "
        "recurring deposit account. If she earns ₹150 as "
        "interest at the time of maturity, then her matured "
        "amount is: (a) ₹2400 (b) ₹2550 (c) ₹2250 "
        "(d) ₹2650")
    assert out["answer"].startswith("(b)")


def test_gst_plain_rate_variant():
    out = mcq_result(
        "The marked price of an article is ₹500. If the "
        "GST is charged at a rate of 10%, then the price "
        "of the article including GST is: (a) ₹50 "
        "(b) ₹450 (c) ₹550 (d) ₹600")
    assert out["answer"].startswith("(c)")


def test_matrix_cube_variant():
    out = mcq_result(
        "If A = [[1, 2], [0, 1]], then A² is equal to: "
        "(a) [[1, 4], [0, 1]] (b) [[1, 2], [0, 1]] "
        "(c) [[2, 4], [0, 2]] (d) [[1, 0], [0, 1]]")
    assert out["answer"].startswith("(a)")


def test_sphere_radii_to_volume_variant():
    out = mcq_result(
        "If the ratio of the radii of two spheres is "
        "2 : 3, then the ratio of their volumes is: "
        "(a) 4 : 9 (b) 8 : 27 (c) 2 : 3 (d) 27 : 8")
    assert out["answer"].startswith("(b)")


def test_line_perpendicular_variant():
    out = mcq_result(
        "The equation of the line passing through origin "
        "and perpendicular to the line 3x + 4y + 7 = 0 "
        "is: (a) 3x + 4y = 0 (b) 4x - 3y = 0 "
        "(c) 4x + 3y = 0 (d) 3x - 4y = 0")
    assert out["answer"].startswith("(b)")


def test_inequality_set_variant():
    out = mcq_result(
        "The solution set for -1 < x + 2 < 3, x ∈ Z is: "
        "(a) {-2, -1, 0} (b) {-3, -2, -1, 0} "
        "(c) {-2, -1, 0, 1} (d) {-1, 0, 1}")
    # -3 < x < 1 -> {-2, -1, 0}
    assert out["answer"].startswith("(a)")


def test_similar_triangles_variant():
    out = mcq_result(
        "In the given diagram ΔPQR ~ ΔXYZ. The length of "
        "the side YZ is: (In the diagram, PQ = 4 cm, "
        "QR = 6 cm and XY = 10 cm.) (a) 12 cm (b) 15 cm "
        "(c) 18 cm (d) 20 cm")
    # correspondence P<->X, Q<->Y, R<->Z: QR <-> YZ,
    # scale XY/PQ = 10/4 -> YZ = 6 * 2.5 = 15
    assert out["answer"].startswith("(b)")


# --- Guards: nothing else moved -------------------------------

def test_genuine_concept_ask_still_gets_topics():
    out = _solve_friendly("what is a prime number")
    assert out.get("source") == "topics"
    out = _solve_friendly("quadratic formula kya hai?")
    assert out.get("source") == "topics"


def test_ordinary_mcq_unchanged():
    out = mcq_result(
        "Find the HCF of 12 and 18 (A) 3 (B) 6 (C) 9 "
        "(D) 36")
    assert out["answer"] == "(B) 6"


def test_ordinary_equation_unchanged():
    out = _solve_friendly("solve 2x + 3 = 7")
    assert "2" in out["answer"]
    assert out.get("source") != "multipart"


def test_unsolvable_mcq_still_never_guessed():
    out = mcq_result(
        "The value of the determinant of a magic matrix "
        "of order 7 with entries from a poem is: (A) 3 "
        "(B) 6 (C) 9 (D) 36")
    assert out is None
