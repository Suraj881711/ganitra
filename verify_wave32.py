#!/usr/bin/env python3
"""Wave 32 (Suraj, 14 Nov 2026: "or bhi topics add karo,
karib 50 topics add karo"): ~50 NEW exact-solve topics —
76 shipped.

A probe battery of 89 candidate questions through the real
user path (api._solve_friendly) found 65 gaps. Two classes:
(a) fallback/concept-only (guide or similar example), and
(b) HIJACKED — a valid-looking op answering a DIFFERENT
question with a wrong number: hemisphere as sphere, cone CSA
as cone volume, cylinder CSA as TSA, sector as full circle,
annual CI ignoring "compounded half-yearly", combined
cylinder+cone dropping the cone, AP nth-from-end as nth-from-
start, identity evaluation as a garbage "system", insert
geometric mean as the arithmetic mean, sum/product of roots
as the roots themselves, grouped table frequencies averaged
as raw data.

FIX (solver-side only): new strict patterns in
solver/applied.py (money, Bayes, LP corners, pipes/work/
boats/trains, insert means, identity eval, find-k/sum-product
roots), solver/geometry.py (mensuration block running BEFORE
the generic shape branches, circle theorems, coordinate
additions, 3D geometry), solver/trigonometry.py (depression,
two-observation, inverse-trig evaluations, complementary
ratios, written-out-degrees standard values),
solver/sequences.py (AP nth-from-end, AP terms-for-sum),
solver/algebra.py (remainder/factor theorem, cubic zeroes
relations, verify zeroes, rationalisation), solver/
calculus.py (piecewise continuity + find-k, differentiability
checks, removable-discontinuity limits), solver/statistics.py
(grouped mean/median/mode from text tables — added LAST,
after the Wave 31 deploy released the file), plus narrow
router pre-checks (applied-first / geometry-first /
algebra-first, all fall-through-on-failure and
exception-shielded) for asks that an earlier solver
systematically hijacks, and one calculus routing keyword
(continu*/differentiab*).

No template/CSS/JS changed: the ?v=29 / ganitra-static-v6
pins deliberately stay put and this script asserts they did
NOT move, and that the frozen logo files are untouched.

Deliberately NOT taken: LP from raw inequalities (corners
not reliably computable from free text), single geometric
mean of two numbers, proof/verify identity asks,
cumulative-frequency ogive forms, surd simplification
without an ask, the pre-existing identity-verifier and
system-parser quirks (identical on the pristine tree).
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


from api import _solve_friendly  # noqa: E402
from solver.router import solve_question  # noqa: E402

TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
COINS = ("Two coins are tossed simultaneously. What is the "
         "probability of getting at most one head?")


def _op(q):
    return str(solve_question(q).get("op", ""))


def _ans(q):
    return str(solve_question(q).get("answer", ""))


# --- 1. Calculus: continuity / differentiability ------------------
check("continuity piecewise (continuous)",
      _op("Examine the continuity of the function "
          "f(x) = 2x + 3 for x <= 2, x + 5 for x > 2 at x = 2.")
      == "continuity_check"
      and "Continuous" in _ans(
          "Examine the continuity of the function "
          "f(x) = 2x + 3 for x <= 2, x + 5 for x > 2 at x = 2."))
check("continuity find k = 7/3",
      "7/3" in _ans("Find the value of k for which the "
                    "function f(x) = kx + 1, if x <= 3; "
                    "5x - 7, if x > 3 is continuous at x = 3."))
check("|x| not differentiable at 0",
      "Not differentiable" in _ans(
          "Check whether f(x) = |x| is differentiable "
          "at x = 0."))
check("removable discontinuity: limit 4 stated",
      "limit = 4" in _ans("Discuss the continuity of "
                          "f(x) = (x^2 - 4)/(x - 2) "
                          "at x = 2."))

# --- 2. Trigonometry ----------------------------------------------
check("angle of depression -> 103.92 m",
      "103.92" in _ans(
          "From the top of a 60 m high tower, the angle of "
          "depression of an object on the ground is "
          "30 degrees. Find the distance of the object from "
          "the foot of the tower."))
check("two observations -> 17.32 m",
      "17.32" in _ans(
          "The angle of elevation of the top of a tower from "
          "a point on the ground changes from 30 degrees to "
          "60 degrees when the observer moves 20 m closer "
          "to the tower. The two points are 20 m apart. "
          "Find the height of the tower."))
check("sec^-1(2) = pi/3",
      "pi/3" in _ans("Find the principal value of sec^-1(2)."))
check("cosec^-1(2) = pi/6",
      "pi/6" in _ans("Find the principal value of "
                     "cosec^-1(2)."))
check("cot^-1(sqrt(3)) = pi/6",
      "pi/6" in _ans("Find the principal value of "
                     "cot^-1(sqrt(3))."))
check("sin^-1(1/2) + cos^-1(1/2) = pi/2",
      "pi/2" in _ans("Evaluate sin^-1(1/2) + cos^-1(1/2)."))
check("sin^-1(sin 210 deg) = -30 deg",
      "-30" in _ans("Evaluate sin^-1(sin 210 degrees)."))
check("tan^-1(1) + tan^-1(1/2) = atan(3)",
      "atan(3)" in _ans("Evaluate tan^-1(1) + "
                        "tan^-1(1/2)."))
check("written-out degrees expression = 1",
      _ans("Evaluate sin 60 degrees cos 30 degrees + "
           "sin 30 degrees cos 60 degrees.") == "1")
check("complementary ratio tan65/cot25 = 1",
      _ans("Evaluate tan 65 degrees / cot 25 degrees.")
      == "1")

# --- 3. Mensuration -------------------------------------------------
MENS = [
    ("frustum volume", "Find the volume of a frustum of a "
     "cone with radii 10 cm and 6 cm and height 7 cm.",
     "1436.76"),
    ("frustum csa", "Find the curved surface area of a "
     "frustum of a cone with radii 8 cm and 4 cm and "
     "height 6 cm.", "271.85"),
    ("hemisphere volume (was: sphere)",
     "Find the volume of a hemisphere of radius 7 cm.",
     "718.378"),
    ("hemisphere tsa (was: sphere)",
     "Find the total surface area of a hemisphere of "
     "radius 7 cm.", "461.814"),
    ("cone csa (was: cone volume)",
     "Find the curved surface area of a cone with "
     "radius 7 cm and slant height 10 cm.", "219.911"),
    ("cone tsa (was: cone volume)",
     "Find the total surface area of a cone with "
     "radius 7 cm and slant height 10 cm.", "373.85"),
    ("cylinder csa (was: cylinder tsa)",
     "Find the curved surface area of a cylinder with "
     "radius 7 cm and height 10 cm.", "439.823"),
    ("cuboid volume", "Find the volume of a cuboid with "
     "length 10 cm, breadth 8 cm and height 6 cm.", "480"),
    ("cuboid tsa", "Find the total surface area of a "
     "cuboid with length 10 cm, breadth 8 cm and "
     "height 6 cm.", "376"),
    ("combined cylinder+cone (was: cylinder only)",
     "Find the total volume of a solid made of a cylinder "
     "of height 5 cm and a cone of height 4 cm mounted on "
     "it, both of radius 3 cm.", "179.071"),
    ("sector area (was: full circle)",
     "Find the area of a sector of a circle with "
     "radius 14 cm and angle 90 degrees.", "153.938"),
    ("segment area", "Find the area of a segment of a "
     "circle with radius 14 cm and angle 90 degrees.",
     "55.938"),
    ("arc length", "Find the length of an arc of a "
     "circle with radius 10 cm and angle 60 degrees.",
     "10.472"),
]
for _name, _q, _want in MENS:
    check(f"mensuration: {_name}", _want in _ans(_q),
          _ans(_q))
check("cylinder TSA still the generic branch's 747.6991",
      "747.6991" in _ans("Find the total surface area of a "
                         "cylinder with radius 7 cm and "
                         "height 10 cm."))

# --- 4. Circles + coordinate + 3D -----------------------------------
GEO = [
    ("tangent length", "Find the length of the tangent "
     "drawn from the point (5, 0) to the circle "
     "x^2 + y^2 = 16.", "3"),
    ("angle between tangents",
     "Tangents are drawn from a point at a distance of "
     "10 cm from the centre of a circle of radius 6 cm. "
     "Find the angle between the two tangents.", "73.74"),
    ("chord distance", "A chord of length 16 cm is drawn "
     "in a circle of radius 10 cm. Find the distance of "
     "the chord from the centre.", "6"),
    ("centroid", "Find the centroid of a triangle with "
     "vertices (2, 3), (4, 5) and (6, 7).", "(4.0, 5.0)"),
    ("quadrilateral area", "Find the area of a "
     "quadrilateral with vertices (0, 0), (4, 0), (6, 3) "
     "and (2, 5).", "18"),
    ("collinearity", "Check whether the points (1, 2), "
     "(2, 3) and (3, 4) are collinear.", "collinear"),
    ("distance from origin", "Find the distance of the "
     "point (3, 4) from the origin.", "5"),
    ("ratio x-axis divides", "In what ratio does the "
     "x-axis divide the line segment joining (3, 4) and "
     "(2, -5)?", "0.8 : 1"),
    ("equidistant on x-axis", "Find the point on the "
     "x-axis which is equidistant from the points (2, 3) "
     "and (4, 5).", "(7.0, 0)"),
    ("direction ratios", "Find the direction ratios of "
     "the line joining the points (1, 2, 3) and "
     "(4, 6, 8).", "(3, 4, 5)"),
    ("direction cosines", "Find the direction cosines of "
     "the line joining the points (1, 2, 3) and "
     "(4, 6, 8).", "0.4243"),
    ("angle between lines", "Find the angle between two "
     "lines whose direction ratios are 1, 2, 2 and "
     "2, 1, 2.", "27.27"),
    ("point-plane distance", "Find the distance of the "
     "point (1, 2, 3) from the plane 2x + 3y + 4z = 10.",
     "1.8569"),
    ("section formula 3d", "Find the point which divides "
     "the join of (1, 2, 3) and (3, 4, 5) internally in "
     "the ratio 2:1.", "2.333"),
]
for _name, _q, _want in GEO:
    check(f"geometry: {_name}", _want in _ans(_q), _ans(_q))

# --- 5. Applied -----------------------------------------------------
APP = [
    ("CI half-yearly (was: annual 2100)",
     "Find the compound interest on Rs 10000 at 10% per "
     "annum for 2 years, compounded half-yearly.",
     "2155.06"),
    ("CI quarterly (was: annual 960)",
     "Find the compound interest on Rs 8000 at 12% per "
     "annum for 1 year, compounded quarterly.", "1004.07"),
    ("GST forward", "An article costs Rs 5000. GST is "
     "charged at 18% on it. Find the GST amount and the "
     "total amount to be paid.", "5900"),
    ("GST reverse", "The total price of an item including "
     "28% GST is Rs 6400. Find the price before GST.",
     "5000"),
    ("successive discounts SP", "The marked price of an "
     "article is Rs 2000. Two successive discounts of 10% "
     "and 5% are offered. Find the selling price.", "1710"),
    ("successive discounts equivalent",
     "Find a single discount equivalent to two successive "
     "discounts of 20% and 10%.", "28%"),
    ("two articles same SP", "A shopkeeper sells two "
     "articles at Rs 999 each. On one he gains 10% and on "
     "the other he loses 10%. Find his overall gain or "
     "loss percent.", "Loss of 1%"),
    ("find k equal roots", "Find the value of k for which "
     "the equation x^2 - 4x + k = 0 has equal roots.",
     "k = 4"),
    ("sum and product of roots (was: the roots)",
     "Find the sum and product of roots of the equation "
     "3x^2 - 5x + 2 = 0.", "Sum = 5/3"),
    ("insert arithmetic means", "Insert two arithmetic "
     "means between 8 and 26.", "14, 20"),
    ("insert geometric mean (was: arithmetic mean 10)",
     "Insert one geometric mean between 4 and 16.", "8"),
    ("identity a^2+b^2 (was: garbage system)",
     "If a + b = 10 and ab = 21, find a^2 + b^2.", "58"),
    ("identity a^3+b^3", "If a + b = 5 and ab = 6, find "
     "a^3 + b^3.", "35"),
    ("pipes together", "Pipe A can fill a tank in 6 "
     "hours and pipe B can fill it in 8 hours. How long "
     "will they take to fill the tank together?", "24/7"),
    ("pipes fill vs empty", "A pipe can fill a tank in "
     "4 hours and another pipe can empty it in 6 hours. "
     "If both are opened together, in how many hours "
     "will the tank be filled?", "12"),
    ("work together", "A can do a piece of work in "
     "10 days and B can do it in 15 days. In how many "
     "days can they do it together?", "6"),
    ("work efficiency", "A is twice as efficient as B. "
     "Together they finish a work in 12 days. In how "
     "many days can A alone do the work?", "18"),
    ("boat and stream", "A boat goes 36 km downstream "
     "in 3 hours and 24 km upstream in 4 hours. Find "
     "the speed of the boat in still water and the "
     "speed of the stream.", "Boat 9"),
    ("two trains opposite", "Two trains of lengths "
     "120 m and 180 m run at 60 km/h and 40 km/h in "
     "opposite directions. In how much time will they "
     "cross each other?", "10.8"),
    ("two trains same direction", "Two trains of lengths "
     "150 m and 100 m run at 50 km/h and 30 km/h in the "
     "same direction. In how much time will they cross "
     "each other?", "45"),
    ("bayes bags", "Bag A contains 3 red balls and "
     "2 black balls. Bag B contains 2 red balls and "
     "3 black balls. A bag is chosen at random and a "
     "ball is drawn from it, which is found to be red. "
     "Find the probability that the ball was drawn from "
     "bag A.", "3/5"),
    ("bayes medical", "A test detects a disease with "
     "probability 0.99 when a person has it, and gives "
     "a false positive with probability 0.05 when a "
     "person does not have it. 1% of people have the "
     "disease. If a person tests positive, what is the "
     "probability that the person actually has the "
     "disease?", "1/6"),
    ("bayes factory", "Machine A produces 60% of items "
     "with 2% defective, machine B produces 40% with "
     "3% defective. An item is found defective. Find "
     "the probability it came from machine A.", "1/2"),
    ("LP maximise", "Maximise Z = 3x + 4y at the corner "
     "points (0, 0), (6, 0), (3, 4) and (0, 5).",
     "Maximum Z = 25"),
    ("LP minimise", "Minimise Z = x + 2y subject to "
     "constraints with corner points (2, 0), (2, 2), "
     "(0, 3) and (0, 0). Evaluate Z at the corner "
     "points.", "Minimum Z = 0"),
]
for _name, _q, _want in APP:
    check(f"applied: {_name}", _want in _ans(_q), _ans(_q))

# --- 6. Sequences ---------------------------------------------------
check("AP nth from the end (was: nth from start, 34)",
      _ans("Find the 10th term from the end of the AP "
           "7, 10, 13, ..., 184.") == "157")
check("AP how many terms for sum 636",
      _ans("How many terms of the AP 9, 17, 25, ... must "
           "be taken so that their sum is 636?") == "12")

# --- 7. Algebra theorems --------------------------------------------
ALG = [
    ("remainder theorem", "Find the remainder when "
     "x^3 + 3x^2 + 3x + 1 is divided by x + 1.", "0"),
    ("factor theorem check yes", "Is x + 1 a factor of "
     "x^3 + 3x^2 + 3x + 1?", "Yes"),
    ("factor theorem check no", "Is x + 2 a factor of "
     "x^2 - 5x + 6?", "No"),
    ("factor theorem find k", "Find the value of k for "
     "which (x - 1) is a factor of "
     "x^3 - 6x^2 + 11x + k.", "k = -6"),
    ("cubic zeroes relations", "For the cubic polynomial "
     "x^3 - 6x^2 + 11x - 6, find α + β + γ, "
     "αβ + βγ + γα and αβγ.", "α + β + γ = 6"),
    ("verify zeroes", "Verify that 1, 2 and 3 are zeroes "
     "of the cubic polynomial x^3 - 6x^2 + 11x - 6.",
     "Verified"),
    ("rationalise 1/(2+sqrt3)", "Rationalise the "
     "denominator of 1/(2 + sqrt(3)).", "2 - sqrt(3)"),
    ("rationalise 5/sqrt7", "Rationalise the denominator "
     "of 5/sqrt(7).", "5·sqrt(7)/7"),
]
for _name, _q, _want in ALG:
    check(f"algebra: {_name}", _want in _ans(_q), _ans(_q))

# --- 8. Grouped statistics ------------------------------------------
_TAB = ("of the data with class intervals 0-10, 10-20, "
        "20-30, 30-40 and frequencies 5, 8, 12, 5.")
check("grouped mean", "20.6667" in _ans("Find the mean "
                                        + _TAB))
check("grouped median", "21.6667" in _ans("Find the "
                                          "median " + _TAB))
check("grouped mode", "23.6364" in _ans("Find the mode "
                                        + _TAB))

# --- 9. Regression guards -------------------------------------------
check("Wave 30 Hindi train question still 40 km/h",
      "40" in str(_solve_friendly(TRAIN_HINDI)
                  .get("answer", "")))
check("Wave 31 coins question still 3/4",
      _ans(COINS).startswith("3/4"))
check("Wave 30 nature-of-roots direct form intact",
      "equal" in _ans("Find the nature of roots of "
                      "x^2 - 4x + 4 = 0"))
check("raw list mean intact",
      _ans("Find the mean of 4, 6, 8, 10.").startswith("7"))
check("trig ratio-from-ratio intact",
      _ans("If sin A = 3/5, find cos A.")
      .startswith("cos A = 4/5"))
check("plain system still routes to algebra's system op",
      _op("If a + b = 10 and a - b = 4, find a and b.")
      == "system")

# --- 10. Delivery pins + frozen logo (solver-only wave) -------------
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf8").read()
# Merge (Waves 38-46): Wave 43 deliberately bumped the pins to
# ?v=30 / ganitra-static-v7 — assert the current merged pins,
# same convention Wave 43 applied to the pytest pin tests.
check("stylesheet pin at Wave 43 bump (?v=30)",
      "v='30'" in TPL or "?v=30" in TPL)
check("service-worker cache at Wave 43 bump (v7)",
      'GANITRA_CACHE = "ganitra-static-v7"' in SW)
for _name, _want in (
        ("logo-full-t.png", "f18c8e42"),
        ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"),
        ("logo-mark.png", "03bc03dc")):
    _digest = hashlib.sha256(
        open(os.path.join("static", _name), "rb").read()
    ).hexdigest()
    check(f"frozen logo {_name} untouched",
          _digest.startswith(_want), _digest[:12])

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
