"""Wave 223 — multi-part questions, jad se (DeepSeek Job 9).

Bug (live checker, ChatGPT Jobs A/B/C, 23 Nov 2026): a
question asking for TWO things was served only the first:

    "ek aayat ka kshetrafal aur parimap batao, lambai
     8 cm, chaudai 5 cm"  ->  sirf area 40 (parimap 26 gayab)
    "Find the area and perimeter of a rectangle ..."
                          ->  sirf ek jawab (26 ya 40)
    "Find the sum and difference of 25 and 13"
                          ->  sirf difference 12
    "Ravi buys 4 notebooks at Rs 30 each. How much does
     he pay and how much change ... from Rs 200?"
                          ->  "Total spent = 30 + 4 = ₹34",
                              change ₹166 (dono galat)

ROOT CAUSE: every serving layer returns exactly ONE result
for the first ask it recognises — geometry's rectangle
branch is `if "perimeter" in q: return perimeter; return
area`, the Hinglish translator is first-match-wins (an
unconditional rectangle-area rule shadows the ask-sensitive
ones), and Wave 212's money_change reads the item count as
a second price (its "note" test fires inside "notebooks").

Fix: solver/multipart223.py splits ONLY on a provable
two-ask structure (Job 9 contract: sentence / semicolon /
aur / and candidates, before-part a complete clause,
after-part carrying its own ask signal), solves each part
through the ordinary pipeline, verifies each part's op
against its ask, and assembles the Wave 100 multipart
format.  The money family is computed exactly in-module
because the pipeline provably cannot (the pay dress errors;
the change schema misfires).  These tests pin the reported
failures, every family in English + Hinglish in both ask
orders, the Job 9 trap and the single-ask shapes that must
never split, and the Wave 221/222 regression guards.
"""
import pytest

from solver.multipart223 import split_parts, solve_multipart223
from solver.router import solve_question


def _full_text(result):
    parts = [str(result.get("answer") or "")]
    parts += [str(s) for s in result.get("steps") or []]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The reported failure, through every path that can serve it
# ---------------------------------------------------------------------------

def test_reported_failure_hinglish_full_pipeline():
    r = solve_question(
        "ek aayat ka kshetrafal aur parimap batao, "
        "lambai 8 cm, chaudai 5 cm")
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == "(a) 40 cm²; (b) 26"
    assert r["steps"] == [
        "(a) Area = length × breadth = 8 × 5 = 40",
        "(b) Perimeter = 2(l + b) = 2(8 + 5) = 26",
    ]


def test_reported_failure_english_full_pipeline():
    r = solve_question(
        "Find the area and perimeter of a rectangle whose "
        "length is 8 cm and breadth is 5 cm")
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == "(a) 40 cm²; (b) 26"
    text = _full_text(r)
    assert "Area = length × breadth = 8 × 5 = 40" in text
    assert "Perimeter = 2(l + b) = 2(8 + 5) = 26" in text


def test_reported_failure_chat_path():
    from api import _solve_friendly
    r = _solve_friendly(
        "ek aayat ka kshetrafal aur parimap batao, "
        "lambai 8 cm, chaudai 5 cm")
    assert r is not None
    assert "40" in str(r.get("answer"))
    assert "26" in str(r.get("answer"))


def test_reported_failure_split_parts_contract():
    parts = split_parts(
        "ek aayat ka kshetrafal aur parimap batao, "
        "lambai 8 cm, chaudai 5 cm")
    assert parts == {"parts": [
        "area of a rectangle with length 8 cm and breadth 5 cm",
        "perimeter of a rectangle with length 8 cm and breadth 5 cm",
    ]}


# ---------------------------------------------------------------------------
# Mensuration families — both orders, English + Hinglish + Devanagari
# ---------------------------------------------------------------------------

MENS_CASES = [
    ("Find the area and perimeter of a rectangle whose length "
     "is 8 cm and breadth is 5 cm", "(a) 40 cm²; (b) 26"),
    ("Find the perimeter and area of a rectangle whose length "
     "is 8 cm and breadth is 5 cm", "(a) 26; (b) 40 cm²"),
    ("ek aayat ka parimap aur kshetrafal batao, lambai 8 cm, "
     "chaudai 5 cm", "(a) 26; (b) 40 cm²"),
    ("एक आयत का क्षेत्रफल और परिमाप बताओ, लम्बाई 8 cm, "
     "चौड़ाई 5 cm", "(a) 40 cm²; (b) 26"),
    ("Find the area and perimeter of a square with side 6 cm",
     "(a) 36 cm²; (b) 24"),
    ("Find the perimeter and area of a square whose side is 9 cm",
     "(a) 36; (b) 81 cm²"),
    ("varg ka kshetrafal aur parimap batao, bhuja 6 cm hai",
     "(a) 36 cm²; (b) 24"),
    ("Find the circumference and area of a circle with radius "
     "7 cm", "(a) 44; (b) 154 cm²"),
    ("Find the area and circumference of a circle with diameter "
     "14 cm", "(a) 154 cm²; (b) 44"),
    ("Find the diameter and circumference of a circle with "
     "radius 7 cm", "(a) 14; (b) 44"),
    ("ek vritt ki paridhi aur kshetrafal batao, trijya 7 cm hai",
     "(a) 44; (b) 154 cm²"),
    ("A rectangle has length 10 cm and breadth 4 cm. Find its "
     "area and perimeter.", "(a) 40 cm²; (b) 28"),
]


@pytest.mark.parametrize("question,answer", MENS_CASES)
def test_mensuration_two_asks(question, answer):
    r = solve_question(question)
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == answer


# ---------------------------------------------------------------------------
# Sum / difference / product families
# ---------------------------------------------------------------------------

SUM_CASES = [
    ("Find the sum and difference of 25 and 13",
     "(a) 38; (b) 12"),
    ("Find the difference and sum of 25 and 13",
     "(a) 12; (b) 38"),
    ("Find the sum and product of 6 and 4",
     "(a) 10; (b) 24"),
    ("Find the sum, difference and product of 8 and 2",
     "(a) 10; (b) 6; (c) 16"),
    ("25 aur 13 ka yog aur antar batao",
     "(a) 38; (b) 12"),
]


@pytest.mark.parametrize("question,answer", SUM_CASES)
def test_sum_family_two_asks(question, answer):
    r = solve_question(question)
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == answer


# ---------------------------------------------------------------------------
# Money: cost of N items + change from a note
# ---------------------------------------------------------------------------

def test_money_cost_and_change():
    r = solve_question(
        "Ravi buys 4 notebooks at Rs 30 each. How much does "
        "he pay and how much change does he get from Rs 200?")
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == "(a) ₹120; (b) ₹80"
    text = _full_text(r)
    assert "Total cost = 4 × ₹30 = ₹120" in text
    assert "Change = ₹200 − ₹120 = ₹80" in text
    assert "166" not in text  # the old money_change misfire


def test_money_cost_and_left_variant():
    r = solve_question(
        "Ramesh has Rs 500. He buys 5 pens at Rs 20 each. "
        "How much does he pay and how much money is left "
        "with him?")
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == "(a) ₹100; (b) ₹400"


def test_money_chat_path():
    from api import _solve_friendly
    r = _solve_friendly(
        "Ravi buys 4 notebooks at Rs 30 each. How much does "
        "he pay and how much change does he get from Rs 200?")
    assert r is not None
    assert "₹120" in str(r.get("answer"))
    assert "₹80" in str(r.get("answer"))


# ---------------------------------------------------------------------------
# Generic two-clause split (Job 9 core)
# ---------------------------------------------------------------------------

def test_generic_two_independent_questions():
    r = solve_question(
        "Find the area of a square with side 6 cm. "
        "Find the perimeter of a square with side 6 cm.")
    assert r is not None
    assert r["type"] == "Multipart"
    assert r["answer"] == "(a) 36 cm²; (b) 24"


def test_generic_dependent_part_declines():
    # Part 2 needs part 1's x — a Hence chain (Wave 100's
    # family).  The gate must NOT serve the echo "3*x + 1".
    r = solve_question(
        "Find the value of x in 2x + 3 = 7. "
        "Also find the value of 3x + 1.")
    assert r is not None
    assert r.get("type") != "Multipart"
    assert r["answer"] == "x = 2"


def test_generic_indistinguishable_parts_decline():
    # The story solver answers both asks with the same
    # subtraction — serving it twice would be a lie, so the
    # gate declines and the single serve stands.
    r = solve_question(
        "Ravi has 10 marbles. He gives 3 to his friend. "
        "How many marbles are left and how many did he "
        "give away?")
    assert r is not None
    assert r.get("type") != "Multipart"


# ---------------------------------------------------------------------------
# No-split pins — single asks and data conjunctions stay single
# ---------------------------------------------------------------------------

NO_SPLIT = [
    # the Job 9 trap: "aur" joins DATA words, one ask only
    "lambai aur chaudai 12 aur 8 hai, area batao",
    "Find the area of a rectangle whose length is 8 cm and "
    "breadth is 5 cm",
    "Find the perimeter of a rectangle whose length is 8 cm "
    "and breadth is 5 cm",
    "Find the sum of 25 and 13",
    "A rectangle has length 8 cm and breadth 5 cm. "
    "Find its area.",
    "Find the HCF and LCM of 12 and 18",
    "A shopkeeper buys a pen for Rs 50 and sells it for "
    "Rs 60. Find his profit and loss.",
    # inverse mensuration (Job 8): the ask noun with a
    # number attached is DATA, not a second ask
    "The area of a circle is 154 cm2. Find its circumference.",
    "Convert 5 km into metres and find the area of a "
    "square with side 6 cm",
    "3 ghante me kitne minute",
    "347 + 258",
    "samjhao",
]


@pytest.mark.parametrize("question", NO_SPLIT)
def test_no_split(question):
    assert split_parts(question) is None
    r = solve_question(question)
    if r is not None:
        assert r.get("type") != "Multipart"


def test_single_ask_answers_unchanged():
    r = solve_question(
        "Find the area of a rectangle whose length is 8 cm "
        "and breadth is 5 cm")
    assert r["answer"] == "40 cm²"
    r = solve_question(
        "Find the perimeter of a rectangle whose length is "
        "8 cm and breadth is 5 cm")
    assert r["answer"] == "26"
    r = solve_question("Find the sum of 25 and 13")
    assert r["answer"] == "38"


# ---------------------------------------------------------------------------
# Regression guards — Waves 221 / 222 must stay byte-identical
# ---------------------------------------------------------------------------

def test_guard_wave221_addition_working():
    r = solve_question("347 + 258")
    assert r["answer"] == "605"
    assert r["steps"] == [
        "Write the expression: 347 + 258",
        "Ones column: 7 + 8 = 15 — write 5, carry 1",
        "Tens column: 4 + 5 + 1 (carry) = 10 — write 0, carry 1",
        "Hundreds column: 3 + 2 + 1 (carry) = 6 — write 6",
        "347 + 258 = 605",
    ]


def test_guard_wave221_subtraction_working():
    r = solve_question("502 - 178")
    assert r["answer"] == "324"
    assert r["steps"] == [
        "Write the expression: 502 - 178",
        "Ones column: 2 - 8 cannot be done, and the Tens "
        "column is 0, so borrow from the Hundreds column — "
        "Hundreds digit becomes 4, the columns in between "
        "become 9, and Ones becomes 12.",
        "Ones column: 12 - 8 = 4",
        "Tens column: 9 - 7 = 2",
        "Hundreds column: 4 - 1 = 3",
        "502 - 178 = 324",
    ]


def test_guard_wave222_unit_conversion():
    r = solve_question("3 ghante me kitne minute")
    assert r["answer"] == "180 minute"
    text = _full_text(r)
    assert "1 ghanta = 60 minute" in text
    assert "3 ghante = 3 × 60 = 180 minute" in text
    assert "0 hours" not in text


def test_gate_reentrancy_guard():
    # Solving a part re-enters the pipeline; the splitter
    # must never split a part again (thread-local guard).
    r = solve_multipart223(
        "Find the area and perimeter of a rectangle whose "
        "length is 8 cm and breadth is 5 cm")
    assert r is not None
    assert r["answer"] == "(a) 40 cm²; (b) 26"
