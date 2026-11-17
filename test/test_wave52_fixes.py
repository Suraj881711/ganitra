"""Wave 52 (15 Nov 2026): solver coverage round 4 — the
Wave 47 left-open list (Wave 35 audit #15 and #1, the echo
cases #32/#349/#437, and the trig/calculus variants).

1. SALVAGE QUALITY + FRACTION PROMOTION (audit #15).
   'Add 2/3 and 3/4' only worked via salvage, which solved
   one operand and echoed it ('2/3'); 31 of 52 salvage
   answers in the audit carried a wrong value. Fraction
   add/subtract is now a PRIMARY arithmetic pattern, the
   salvage layer refuses a result whose value is not the
   asked sum/difference, the junk detector also catches
   bare *-chains of 5+ single letters (the 'square' ->
   s*q*u*a*r*e product served for 'Find the square of
   15'), and square/cube-of-N is a primary pattern too.
2. HINDI LEFTOVERS (audit #1). The junk detector counted
   only Latin letters, so Devanagari letter-soup (the
   question's own letters multiplied together) was served
   as the answer for 17 battery questions. It now counts
   single-letter factors in any script, and the top Hindi
   statement forms (mensuration, SI, percentage, triangle
   angles, linear-equation and train-time stories) are
   strict patterns in solver/applied.py, reached through
   a Devanagari pre-check in the router.
3. ECHOES. 'Divide Rs 900 among A, B and C in the ratio
   2:3:4. How much does C get?' echoed '2 : 3' (#32);
   triangle angles in a ratio echoed the same (#349);
   'HCF is 12, LCM is 240, one number is 60, find the
   other' echoed the givens (#437).
4. THETA IDENTITIES. 'Prove that sin^2 theta + cos^2
   theta = 1' ERRORED — the parser read t*h*e*t*a. The
   identity verifier now maps the Greek names to single
   letters and cosec to csc before parsing.
5. SQRT-FORM RATIOS. 'If cos theta = sqrt(3)/2, find
   theta' had no pattern (the value group read only
   decimals/fractions). Sqrt values now parse, and the
   triangle sides come from sp.fraction so irrational
   values split into (numerator, denominator) pairs.
6. CONIC TANGENTS. 'Equation of the tangent to the
   circle x^2 + y^2 = 25 at (3, 4)' and the parabola
   y^2 = kx form errored; both are T = 0 patterns now,
   with the point verified on the conic first.
7. INTEGRAL OF e^(kx). The Wave 47 Euler swap covered
   the derivative paths only; 'Integrate e^(2x)' returned
   a Piecewise in log(e). The integral path swaps too.
"""
from api import _solve_friendly
from fallback import _fraction_ask_value, _is_junk
from solver.router import solve_question


def _ans(q):
    return str(solve_question(q).get("answer", ""))


def _op(q):
    return solve_question(q).get("op")


# --------------------------------------- 1. fractions (audit #15)
def test_fraction_add_battery_forms():
    assert _op("Add 2/3 and 3/4.") == "fraction_add"
    assert _ans("Add 2/3 and 3/4.") == "17/12"
    assert _ans("Add 1/2 and 2/3.") == "7/6"
    assert _ans("Add 3/5 and 1/5.") == "4/5"
    assert _ans("Add 5/6 and 1/3.") == "7/6"
    assert _ans("Add 7/8 and 1/4.") == "9/8"
    assert _ans("Add 2/5 and 3/10.") == "7/10"


def test_fraction_subtract_battery_forms():
    assert _op("Subtract 1/4 from 5/6.") == "fraction_subtract"
    assert _ans("Subtract 1/4 from 5/6.") == "7/12"
    assert _ans("Subtract 2/3 from 7/9.") == "1/9"
    assert _ans("Subtract 2/5 from 4/5.") == "2/5"


def test_fraction_add_filler_variant():
    assert _ans("Add the fractions 2/3 and 3/4.") == "17/12"
    assert _ans("Find the sum of 1/2 and 1/3.") == "5/6"


def test_fraction_ask_value_guard():
    from fractions import Fraction
    assert _fraction_ask_value("Add 2/3 and 3/4.") == \
        Fraction(17, 12)
    assert _fraction_ask_value(
        "Subtract 1/4 from 5/6.") == Fraction(7, 12)
    assert _fraction_ask_value("What is 2 + 2?") is None


def test_square_and_cube_of():
    assert _op("Find the square of 15.") == "square_of"
    assert _ans("Find the square of 15.") == "225"
    assert _ans("Find the square of 18.") == "324"
    assert _ans("Find the cube of 5.") == "125"
    # neighbours NOT hijacked: 'square root of' has 'root'
    # between, 'square of side' has 'side' between.
    assert _op("Find the square root of 16.") != "square_of"
    # Wave 140 pin flip: the area answer now carries the
    # question's unit ("225 cm²", was "225") — Suraj's
    # live-check defect 4; numerics unchanged.
    assert _ans("What is the area of a square of side 15 "
                "cm?") == "225 cm²"


def test_junk_detector_letter_chains():
    soup = {"answer": "15*a*e*q*r*s*u"}
    assert _is_junk("Find the square of 15.", soup)
    deva = {"answer": "12*c*m*इ*ए**2*क**4*ग*ज**3*ञ*त*प**2*भ"}
    assert _is_junk("एक वर्ग की भुजा 12 cm है।", deva)
    # genuine answers are not junk
    assert not _is_junk("Add 2/3 and 3/4.",
                        {"answer": "17/12"})
    assert not _is_junk("area of circle radius 10",
                        {"answer": "100·pi ≈ 314.159"})
    assert not _is_junk("hemisphere volume",
                        {"answer": "686·pi/3 ≈ 718.378"})
    assert not _is_junk("solve x", {"answer": "x = 5"})


# --------------------------------------- 2. Hindi patterns (audit #1)
def test_hindi_mensuration():
    assert _op("एक वर्ग की भुजा 12 cm है। इसका परिमाप ज्ञात "
               "कीजिए।") == "hindi_square_perimeter"
    assert _ans("एक वर्ग की भुजा 12 cm है। इसका परिमाप ज्ञात "
                "कीजिए।") == "48"
    assert _ans("एक आयत की लंबाई 15 cm और चौड़ाई 10 cm है। "
                "इसका क्षेत्रफल ज्ञात कीजिए।") == "150"
    assert "314.159" in _ans(
        "एक वृत्त की त्रिज्या 10 cm है। इसका क्षेत्रफल ज्ञात "
        "कीजिए।")
    # Wave 99 (pi policy): radii 14 / 21 / 7 are multiples of
    # 7, so these Hindi answers now use pi = 22/7 — clean
    # textbook values (616, 132, 220, 1540, 1437.33, 718.667)
    # instead of the true-pi decimals asserted before. The
    # radius-10 circle (314.159) and radius-3 cone (37.6991)
    # below/above stay on true pi, unchanged.
    assert "616" in _ans(
        "14 cm त्रिज्या वाले वृत्त का क्षेत्रफल ज्ञात कीजिए।")
    assert "132" in _ans(
        "वृत्त की त्रिज्या 21 cm है। इसका परिमाप ज्ञात कीजिए।")
    assert "220" in _ans(
        "एक बेलन का वक्र पृष्ठ क्षेत्रफल ज्ञात कीजिए जिसकी "
        "त्रिज्या 7 cm और ऊंचाई 5 cm है")
    assert "1540" in _ans(
        "एक बेलन की त्रिज्या 7 cm और ऊंचाई 10 cm है। बेलन का "
        "आयतन ज्ञात कीजिए।")
    assert "37.6991" in _ans(
        "एक शंकु की त्रिज्या 3 cm और ऊंचाई 4 cm है। शंकु का "
        "आयतन ज्ञात कीजिए।")
    assert "1437.33" in _ans(
        "7 cm त्रिज्या वाले गोले का आयतन ज्ञात कीजिए।")
    assert "718.667" in _ans(
        "एक अर्धगोले की त्रिज्या 7 cm है। इसका आयतन ज्ञात "
        "कीजिए।")
    assert _ans("9 cm भुजा वाले घन का आयतन ज्ञात कीजिए।") \
        == "729"
    assert _ans("त्रिभुज का क्षेत्रफल ज्ञात कीजिए जिसका "
                "आधार 10 cm और ऊंचाई 12 cm है।") == "60"


def test_hindi_si_percentage_angles_equation():
    assert _ans("12000 रुपये का 3 वर्ष के लिए 5% वार्षिक दर "
                "से साधारण ब्याज ज्ञात कीजिए।") == "1800"
    assert _ans("5000 रुपये का 2 वर्ष के लिए 6% वार्षिक दर "
                "से साधारण ब्याज ज्ञात कीजिए।") == "600"
    assert _ans("240 का 25 प्रतिशत ज्ञात कीजिए।") == "60"
    assert _ans("त्रिभुज के दो कोण 60 डिग्री और 70 डिग्री "
                "हैं। तीसरा कोण ज्ञात कीजिए।") == "50°"
    assert _ans("एक संख्या के तीन गुने में 7 जोड़ने पर 40 "
                "प्राप्त होता है। संख्या ज्ञात कीजिए।") == "11"
    assert _ans("एक मीनार के पाद से 50 m दूर बिंदु से मीनार "
                "की चोटी का उन्नयन कोण 45 डिग्री है। मीनार की "
                "ऊंचाई ज्ञात कीजिए।") == "50"


def test_hindi_train_time_and_quadratic_guard():
    assert _op("एक रेलगाड़ी 60 km/h की चाल से 300 km की दूरी "
               "कितने समय में तय करेगी?") == "hindi_train_time"
    assert _ans("एक रेलगाड़ी 60 km/h की चाल से 300 km की दूरी "
                "कितने समय में तय करेगी?") == "5"
    # the speed-increase quadratic story must NOT be read
    # as distance/speed (battery #450: 360/5 = 72 was the
    # first-cut regression; the true answer is 40 km/h).
    q450 = ("एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय "
            "करती है। यदि यह चाल 5 km/h अधिक होती, तो वह उसी "
            "यात्रा में 1 घंटा कम समय लेती। रेलगाड़ी की चाल "
            "ज्ञात कीजिए।")
    assert _op(q450) != "hindi_train_time"
    assert _ans(q450) == "40 km/h"


def test_hindi_concept_ask_falls_back_honestly():
    r = _solve_friendly("पाइथागोरस प्रमेय क्या है?")
    assert r.get("fallback_kind") == "concept"
    assert "प्रमेय" in str(r.get("answer")) or \
        "Pythagoras" in str(r.get("answer"))


# --------------------------------------- 3. echoes (#32, #349, #437)
def test_ratio_divide_among_named_ask():
    q = ("Divide Rs 900 among A, B and C in the ratio "
         "2:3:4. How much does C get?")
    assert _op(q) == "ratio_divide"
    assert _ans(q) == "Rs 400"
    assert _ans("Divide Rs 900 among A, B and C in the "
                "ratio 2:3:4. How much does A get?") \
        == "Rs 200"
    # the plain form is unchanged
    assert _ans("Divide Rs 600 in the ratio 2:3.") \
        == "Rs 240 and Rs 360"


def test_triangle_angles_ratio():
    q = ("The angles of a triangle are in the ratio 2:3:4. "
         "Find the largest angle.")
    assert _op(q) == "triangle_angles_ratio"
    assert _ans(q) == "80°"
    assert _ans("The angles of a triangle are in the ratio "
                "2:3:4. Find the smallest angle.") == "40°"
    assert _ans("The angles of a triangle are in the ratio "
                "2:3:4. Find all the angles.") \
        == "40°, 60°, 80°"


def test_hcf_lcm_other_number():
    q = ("The HCF of two numbers is 12 and their LCM is "
         "240. If one number is 60, find the other number.")
    assert _op(q) == "hcf_lcm_other"
    assert _ans(q) == "48"
    # the together ask is unchanged
    assert _ans("Find the HCF and LCM of 12 and 18.") \
        == "HCF = 6, LCM = 36"


# --------------------------------------- 4. theta identities
def test_theta_identities():
    for q in ("Prove that sin^2 theta + cos^2 theta = 1",
              "Prove that tan^2 theta + 1 = sec^2 theta",
              "Prove that sec^2 theta - tan^2 theta = 1",
              "Prove that (1 - cos theta)(1 + cos theta) "
              "= sin^2 theta",
              "Prove that cosec^2 theta - cot^2 theta = 1"):
        assert _op(q) == "identity", q
        assert _ans(q) == "Identity verified ✔", q


def test_identity_controls_unchanged():
    assert _ans("Prove that sin^2 A + cos^2 A = 1") \
        == "Identity verified ✔"
    # a false identity still answers honestly
    assert _ans("Prove that sin^2 theta + cos^2 theta = 2") \
        == "Not an identity"


# --------------------------------------- 5. sqrt-form ratios
def test_sqrt_ratio_inverse_angle():
    assert _ans("If cos theta = sqrt(3)/2, find theta.") \
        == "θ = 30°"
    assert _ans("If sin theta = sqrt(3)/2, find the value "
                "of theta in degrees.") == "θ = 60°"
    assert _ans("If tan theta = sqrt(3), find theta.") \
        == "θ = 60°"
    assert _ans("If sin theta = 1/sqrt(2), find theta.") \
        == "θ = 45°"


def test_sqrt_ratio_conversion():
    assert _ans("If cos theta = sqrt(3)/2, find sin theta "
                "and tan theta.") \
        == "sin θ = 1/2, tan θ = sqrt(3)/3"
    assert _ans("If sin A = sqrt(3)/2, find cos A.") \
        == "cos A = 1/2"
    # the rational path is unchanged
    assert _ans("If sin A = 3/5, find cos A.") == "cos A = 4/5"
    assert _ans("If sin theta = 1/2, find the value of "
                "theta in degrees.") == "θ = 30°"


# --------------------------------------- 6. conic tangents
def test_conic_tangent_circle():
    assert _op("Find the equation of the tangent to the "
               "circle x^2 + y^2 = 25 at the point (3, 4).") \
        == "conic_tangent_circle"
    assert _ans("Find the equation of the tangent to the "
                "circle x^2 + y^2 = 25 at the point (3, 4).") \
        == "3·x + 4·y = 25"
    assert _ans("Find the equation of the tangent to the "
                "circle x^2 + y^2 = 13 at (2, 3).") \
        == "2·x + 3·y = 13"
    # a point NOT on the circle must not earn a line
    assert _op("Find the equation of the tangent to the "
               "circle x^2 + y^2 = 25 at the point (1, 1).") \
        != "conic_tangent_circle"


def test_conic_tangent_parabola():
    assert _ans("Find the equation of the tangent to the "
                "parabola y^2 = 4x at the point (1, 2).") \
        == "y = x + 1"
    assert _ans("Find the equation of the tangent to the "
                "parabola y^2 = 8x at (2, 4).") == "y = x + 2"
    # the y = f(x) curve block is unchanged
    assert _ans("Find the equation of the tangent to the "
                "curve y = x^2 at x = 3.") == "y = 6·x - 9"


# --------------------------------------- 7. integral of e^(kx)
def test_integral_euler_swap():
    for q in ("Integrate e^(2x) with respect to x.",
              "Integrate e^(2x) dx",
              "Find the integral of e^(3x).",
              "Integrate e^x with respect to x."):
        r = solve_question(q)
        assert r.get("op") == "integral", q
        assert "Piecewise" not in str(r.get("answer")), q
        assert "log(e)" not in str(r.get("answer")), q
    assert _ans("Integrate e^(2x) with respect to x.") \
        == "exp(2·x)/2 + C"
    assert _ans("Find the integral of e^(3x).") \
        == "exp(3·x)/3 + C"
    # neighbours unchanged
    assert _ans("Integrate x^3 with respect to x.") \
        == "x^4/4 + C"
    assert _ans("Find the derivative of e^(3x).") \
        == "3·exp(3·x)"
