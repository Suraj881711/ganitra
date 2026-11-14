"""Wave 30 (Suraj, 14 Nov 2026): "jo question diya uska ans
nhi mil raha hai, uss question ka similar de raha hai — ussi
question ko solve kyu nhi kar raha hai."

ROOT CAUSE, in Suraj's own exact question (the Class 10 train
sum he finally sent, in Hindi): the sentence contains commas,
SymPy's parser turns comma text into a TUPLE, and
solver/arithmetic.py called .free_symbols on that tuple —
"'tuple' object has no attribute 'free_symbols'". The router
turned the crash into op=error, and the Wave-18 fallback layer
then masked it with a labelled similar example. That is the
whole complaint in one stack: crash + missing pattern +
fallback masking. The English twin did not crash but hit
"No word-problem pattern matched" — the speed-time quadratic
(D/x - D/(x+k) = t) was simply not implemented.

WHAT SHIPPED:
1. parse_expression REJECTS tuple results with the ordinary
   readable ValueError, so comma text can never hard-error a
   solver again; arithmetic guards .free_symbols too.
2. The train pattern (faster -> less time, slower -> more
   time) in solver/applied.py, English + Devanagari Hindi,
   built from the student's own numbers and solved exactly.
3. A 50-question battery (Classes 6-12) found the same shape
   of gap in 35 questions; the mechanically-solvable ones are
   now exact: sum & difference, ages (both canonical forms),
   consecutive-integer products, rectangle length/area,
   compound interest, discount -> SP, marks percentage,
   reverse profit/loss, SI story form, ratio share, inverse
   proportion, bells (LCM), train crossing a pole/platform,
   two-digit number, AP/GP "which term", trig ratio from a
   ratio, ladder + tower heights & distances, circle area
   from circumference, "radius of a cylinder is..." phrasing,
   Heron with units in the sentence, section formula,
   triangle area from vertices, third angle of a triangle,
   multi-coin probability, HCF+LCM together, missing value
   from a mean, polynomial zeroes and division, and three
   Roman-Hindi normalisations.
4. The router gives failed/unknown intent results one pass
   through the strict applied patterns before the fallback
   layer may offer a similar example, and wordy word-problems
   no longer die as letter-product "simplify" results.
Solver-side only: no template/CSS/JS changed, so the ?v=29 /
ganitra-static-v6 delivery pins deliberately do NOT move.
"""
import pytest

from api import _solve_friendly
from solver.expression_parser import parse_expression
from solver.router import solve_question

TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
TRAIN_ENGLISH = (
    "A train travels a distance of 360 km at a uniform speed. "
    "If the speed had been 5 km/h more, it would have taken "
    "1 hour less for the same journey. Find the speed of the "
    "train.")


def _exact(question):
    """The full user path must return the student's OWN answer:
    a real solver result, never a fallback layer."""
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


# --- 1. The crash can never come back -------------------------

def test_parse_expression_rejects_comma_tuples():
    with pytest.raises(ValueError):
        parse_expression("ek sawal, do hisso mein, 360 km")


def test_comma_sentence_never_shows_the_tuple_crash():
    res = solve_question(TRAIN_HINDI)
    assert res.get("op") != "error"
    assert "tuple" not in str(res.get("answer", ""))
    assert "Could not solve" not in str(res.get("answer", ""))


# --- 2. Suraj's exact question, solved exactly ----------------

def test_train_question_hindi_exact_answer():
    res = _exact(TRAIN_HINDI)
    assert res["answer"] == "40 km/h"
    assert res.get("op") == "speed_time_quadratic"
    steps = " ".join(res.get("steps") or [])
    assert "360/x - 360/(x + 5) = 1" in steps
    assert "1800" in steps  # x^2 + 5x - 1800 = 0


def test_train_question_english_exact_answer():
    res = _exact(TRAIN_ENGLISH)
    assert res["answer"] == "40 km/h"
    assert res.get("op") == "speed_time_quadratic"


def test_train_question_slower_variant():
    res = _exact(
        "A train travels a distance of 360 km at a uniform "
        "speed. If the speed had been 5 km/h less, it would "
        "have taken 1 hour more for the same journey. Find "
        "the speed of the train.")
    assert res["answer"] == "45 km/h"


def test_train_question_other_numbers():
    res = _exact(
        "A train travels a distance of 240 km at a uniform "
        "speed. If the speed had been 20 km/h more, it would "
        "have taken 2 hours less for the same journey. Find "
        "the speed of the train.")
    assert res["answer"] == "40 km/h"


# --- 3. The battery categories, each with its exact answer ----

CASES = [
    ("A shopkeeper gives a discount of 10% on a shirt marked "
     "Rs 800. What is the selling price?", "720"),
    ("Rahul scored 45 marks out of 60. What percentage did he "
     "score?", "75%"),
    ("The ratio of boys to girls in a class is 3:2. If there "
     "are 30 students in the class, how many girls are there?",
     "12"),
    ("15 workers can build a wall in 12 days. In how many "
     "days can 20 workers build the same wall?", "9 days"),
    ("A man borrowed Rs 12000 at 10% per annum simple "
     "interest for 2 years. How much interest will he pay?",
     "2400"),
    ("Find the compound interest on Rs 10000 at 10% per "
     "annum for 2 years.", "2100"),
    ("An article is sold at Rs 540 at a loss of 10%. Find "
     "its cost price.", "600"),
    ("The sum of two numbers is 50 and their difference is "
     "10. Find the numbers.", "30 and 20"),
    ("A father is 3 times as old as his son. After 10 years, "
     "the father will be twice as old as his son. Find their "
     "present ages.", "30"),
    ("Ravi is 5 years older than his sister. The sum of "
     "their ages is 25 years. Find Ravi's age.", "15"),
    ("A train 200 m long crosses a pole in 10 seconds. Find "
     "the speed of the train in km/h.", "72 km/h"),
    ("The sum of the digits of a two-digit number is 9. The "
     "number obtained by reversing the digits is 27 more "
     "than the original number. Find the number.", "36"),
    ("The product of two consecutive integers is 56. Find "
     "the integers.", "7 and 8"),
    ("A rectangular garden has length 5 m more than its "
     "breadth. The area of the garden is 84 square metres. "
     "Find its length and breadth.", "12"),
    ("Which term of the AP 5, 10, 15, 20, ... is 50?",
     "10th"),
    ("Which term of the GP 3, 6, 12, 24, ... is 96?", "6th"),
    ("If sin A = 3/5, find cos A.", "cos A = 4/5"),
    ("A ladder 10 m long leans against a wall making an "
     "angle of 60 degrees with the ground. How high up the "
     "wall does the ladder reach?", "8.66"),
    ("The angle of elevation of the top of a tower from a "
     "point 30 m away from the foot of the tower is 30 "
     "degrees. Find the height of the tower.", "17.32"),
    ("Find the area of a circle whose circumference is "
     "44 cm.", "154.06"),
    ("The radius of a cylinder is 7 cm and its height is "
     "10 cm. Find its total surface area.", "747.69"),
    ("The sides of a triangle are 5 cm, 12 cm and 13 cm. "
     "Find its area.", "30"),
    ("Find the coordinates of the point which divides the "
     "line segment joining (2, 3) and (8, 9) in the ratio "
     "1:2 internally.", "(4, 5)"),
    ("Find the area of the triangle with vertices (1, 2), "
     "(4, 6) and (5, 3).", "6.5"),
    ("In triangle ABC, angle A = 50 degrees and angle B = "
     "60 degrees. Find angle C.", "70"),
    ("Two coins are tossed together. What is the "
     "probability of getting at least one head?", "3/4"),
    ("Three coins are tossed together. What is the "
     "probability of getting at least one head?", "7/8"),
    ("Find the HCF and LCM of 12 and 18.", "LCM = 36"),
    ("Two bells toll at intervals of 12 minutes and 18 "
     "minutes respectively. They toll together at 10:00 am. "
     "At what time will they toll together again?", "10:36"),
    ("Find the zeroes of the polynomial x^2 - 3x - 10.",
     "x = -2, x = 5"),
    ("Divide x^3 + 3x^2 + 3x + 1 by x + 1.", "x^2 + 2·x + 1"),
    ("The mean of 5 numbers is 20. Four of the numbers are "
     "18, 22, 19 and 21. Find the fifth number.", "20"),
    ("Ek train 72 km/h ki speed se chalti hai. 3 ghante "
     "mein woh kitni doori tay karegi?", "216"),
    ("Do sankhyaon ka jod 40 hai aur unka antar 8 hai. "
     "Sankhyayen batao.", "24 and 16"),
    ("Ek number ko 5 se guna karne par 45 milta hai. Number "
     "kya hai?", "x = 9"),
]


@pytest.mark.parametrize("question,want", CASES)
def test_battery_category_exact(question, want):
    res = _exact(question)
    assert want in str(res.get("answer", "")), (
        f"{question!r}: answer {res.get('answer')!r} does not "
        f"contain {want!r}")


# --- 4. Honesty: the similar layer still exists, still last ---

def test_genuinely_unparseable_still_gets_labelled_fallback():
    res = _solve_friendly(
        "ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 "
        "rupaye ki kharidi kitne bache")
    assert res.get("fallback_kind") == "similar"
    assert str(res.get("answer", "")).startswith(
        "Similar example")
