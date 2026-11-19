"""Wave 141: general multi-part answering.

The Wave 135 CBSE/NCERT audit found 301 real book questions
failing ONLY because they carry 3+ sub-parts — (i)/(ii)/
(iii), (a)/(b)/(c), Part 1/2, numbered asks — and Ganitra
treated the whole blob as one question. The Wave 100 layer
(multipart.py) already handled three strict paper formats
(mega-MCQ bundles, cued case studies, Hence chains); the
ordinary family — plain sub-questions under one shared
stem — had no layer at all.

Wave 141 adds that layer inside multipart.py:
split_general() detects the part structure (labelled runs
in five marker families, Part/Q blocks, boundary-numbered
asks, and unlabelled semicolon/newline ask lists), binds
the shared preamble into each part, solves each part
through the existing machinery (solve_question + the
stem-realness bar, mcq_result for option-carrying parts),
and assembles ONE card: each part's own short steps and
its own labelled final answer, an unsolved part carrying
the one-line not-found. No part solving -> the layer
returns None and today's behaviour runs byte-for-byte.

Fixtures are drawn from real NCERT questions in
~/workspace/ganitra-book-questions.jsonl (source ids in
comments) plus the shared-preamble / mixed / veto shapes
the brief names. The veto battery is the safety half of
the wave: single questions that merely LOOK segmented —
an MCQ's option list, a "which expression" stem, a word
problem's clauses, figure references, a bracketed
expression — must never split.
"""
import pytest

from api import _solve_friendly
from multipart import (general_multipart_result,
                       multipart_result, split_general)

# --- Real NCERT fixtures (ganitra-book-questions.jsonl) ---
# Class 9, Polynomials, Ex 2.2 Q1 — shared stem, value parts.
BOOK_POLY = ("Find the value of the polynomial "
             "5x – 4x2 + 3 at (i) x = 0 (ii) x = –1 "
             "(iii) x = 2")
# Class 11, Sets, Ex 1.1 Q4 — shared stem, set parts.
BOOK_SETS = ("Write the following sets in the set-builder "
             "form : (i) {3, 6, 9, 12} (ii) {2,4,8,16,32} "
             "(iii) {5, 25, 125, 625} (iv) {2, 4, 6, . . .} "
             "(v) {1,4,9, . . .,100}")
# Class 10, Arithmetic Progressions, Examples, Example 2.
BOOK_AP = ("Which of the following list of numbers form "
           "an AP? If they form an AP, write the next two "
           "terms : (i) 4, 10, 16, 22, . . . "
           "(ii) 1, – 1, – 3, – 5, . . . "
           "(iii) – 2, 2, – 2, 2, – 2, . . . "
           "(iv) 1, 1, 1, 2, 2, 2, 3, 3, 3, . . .")
# Class 6, Prime Time, Figure it Out 6 Q4 — divisor parts
# with the shared data list trailing the last part.
BOOK_REMAINDERS = (
    "Find the remainders obtained when each of the "
    "following numbers are divided by (a) 10, (b) 5, "
    "(c) 2. 78, 99, 173, 572, 980, 1111, 2345")
# Class 7, Large Numbers Around Us, Figure it Out 3 Q1 —
# six lettered parts (the cap shape, from a real book).
BOOK_NUMBERS = (
    "Read the following numbers in Indian place value "
    "notation and write their number names in both the "
    "Indian and American systems: (a) 4050678 "
    "(b) 48121620 (c) 20022002 (d) 246813579 "
    "(e) 345000543 (f) 1020304050")


# ---------------------------------------------------------------------------
# Splitting: the labelled families
# ---------------------------------------------------------------------------

def test_split_roman_shared_stem():
    got = split_general(BOOK_POLY)
    assert got is not None
    preamble, parts = got
    assert "polynomial" in preamble
    assert [lab for lab, _t in parts] == ["i", "ii", "iii"]
    assert parts[0][1] == "x = 0"


def test_split_letter_parts():
    got = split_general(
        "Calculate: (a) 12 + 18 (b) 25 - 9 (c) 6 x 7")
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["a", "b", "c"]


def test_split_devanagari_parts():
    got = split_general(
        "ज्ञात कीजिए: (क) 12 और 18 का HCF "
        "(ख) 12 और 18 का LCM")
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["क", "ख"]


def test_split_parennum_parts():
    got = split_general(
        "Solve the following: (1) 2x + 3 = 7 "
        "(2) 3x - 5 = 10")
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["1", "2"]


def test_split_part_blocks():
    got = split_general(
        "Part 1: Find the HCF of 12 and 18. "
        "Part 2: Find the LCM of 12 and 18.")
    assert got is not None
    assert len(got[1]) == 2


def test_split_q_blocks():
    got = split_general(
        "Q1. Find the HCF of 12 and 18. "
        "Q2. Find the LCM of 12 and 18.")
    assert got is not None
    assert len(got[1]) == 2


def test_split_numbered_asks():
    got = split_general(
        "1. Find the HCF of 12 and 18. "
        "2. Find the LCM of 12 and 18.")
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["1", "2"]


def test_split_unlabelled_semicolon():
    got = split_general(
        "Find the HCF of 12 and 18; find the LCM of "
        "12 and 18")
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["i", "ii"]


def test_split_unlabelled_newlines():
    got = split_general("Solve 2x + 3 = 7\nSolve x^2 - 5x + 6 = 0")
    assert got is not None
    assert len(got[1]) == 2


def test_split_shared_context_trailing():
    # "(i) area and (ii) perimeter of a rectangle…" — the
    # facts trail the LAST part; part (i) is a bare noun.
    got = split_general(
        "Find (i) area and (ii) perimeter of a rectangle "
        "with length 5 cm and breadth 3 cm")
    assert got is not None
    assert got[1][0] == ("i", "area")


def test_split_shared_context_preamble():
    got = split_general(
        "A rectangle has length 5 cm and breadth 3 cm. "
        "Find (i) its area (ii) its perimeter")
    assert got is not None
    assert [t for _l, t in got[1]] == ["its area",
                                       "its perimeter"]


def test_split_divisor_parts_with_data_tail():
    got = split_general(BOOK_REMAINDERS)
    assert got is not None
    assert [lab for lab, _t in got[1]] == ["a", "b", "c"]


def test_split_book_sets_and_ap():
    assert split_general(BOOK_SETS) is not None
    assert split_general(BOOK_AP) is not None


# ---------------------------------------------------------------------------
# Splitting: the veto battery — none of these may split
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    # an MCQ's option list is not a set of parts
    "Find the HCF of 12 and 18: (a) 6 (b) 12 (c) 3 (d) 36",
    "What is the HCF of 12 and 18? (A) 0 (B) 1 (C) 3 (D) 6",
    "Find the area: (a) 25 cm² (b) 30 cm² (c) 35 cm²",
    # a "which expression" stem: the expressions are options
    ("Melvin reads a two-page story every day. Which of "
     "the expressions below describes this scenario? "
     "(a) 5 × 2 × 8 (b) (7 – 2) × 8 (c) 8×7 (d) 7 × 2 × 8"),
    # a word problem's internal clauses are not parts
    "A train travels 60 km in 1 hour; find its speed",
    ("Ram has 5 apples and Shyam has 3 apples; how many "
     "apples do they have in all?"),
    # a single expression with brackets
    "Evaluate ((2 + 3) × (4 - 1)) / 5",
    "Solve the equation (x + 3)(x - 2) = 0",
    # figure references are not parts
    ("Measure all three angles of the triangle shown in "
     "Fig. 2.21 (a), and write the measures down. Do the "
     "same for Fig. 2.21 (b) and (c)."),
    "Fig. 1. shows a triangle with sides 3, 4, 5. 2. shows a square.",
    # one marker only is not a set
    "Find the value of f(x) at (i) x = 0",
    "Solve (a) 2x + 3 = 7",
    # ordinary single questions
    "Find the area of a rectangle with length 5 cm and breadth 3 cm",
    "What is the HCF of 12 and 18?",
    "12 aur 18 ka HCF batao",
    # Assertion–Reason belongs to formats.py
    ("Assertion (A): The HCF of 12 and 18 is 6. "
     "Reason (R): 6 divides both 12 and 18. "
     "(a) Both A and R are true (b) Only A is true"),
    # capital-letter MCQ options that are number PAIRS —
    # a pair is not a sequence, and (A)–(D) are options,
    # not parts (Wave 80's order/degree MCQ shape)
    ("अवकल समीकरण [1 + (dy/dx)²]³ = d²y/dx² की कोटि और "
     "घात क्रमशः हैं : (A) 1, 2 (B) 2, 3 (C) 2, 1 (D) 2, 6"),
    # a self-labelled case study belongs to the
    # case-study machinery (Wave 100 / Wave 82 formats)
    ("Case study: The equation of the path traced by a "
     "roller-coaster is given by the polynomial "
     "f(x) = a(x + 9)(x + 1)(x − 3). If the roller-coaster "
     "crosses the y-axis at the point (0, 1), answer the "
     "following: (i) Find the value of a. "
     "(ii) Find f′(x) at x = 1."),
    # an OR bundle belongs to formats.py
    "Solve 2x + 3 = 7 OR solve x^2 - 5x + 6 = 0",
    # a Hence chain belongs to the Wave 100 layer
    ("Find the zeroes of p(x) = 3x^2 - 4x - 4. Hence, "
     "write a polynomial whose zeroes are 2 more than "
     "the zeroes of p(x)."),
])
def test_veto_no_split(q):
    assert split_general(q) is None


# ---------------------------------------------------------------------------
# End to end: one card, part-wise answers
# ---------------------------------------------------------------------------

def test_e2e_polynomial_parts():
    out = _solve_friendly(BOOK_POLY)
    assert out.get("source") == "multipart"
    assert out["multipart"]["kind"] == "general"
    assert out["multipart"]["solved"] == ["i", "ii", "iii"]
    # 5x - 4x^2 + 3 at 0, -1, 2
    assert "(i) 3" in out["answer"]
    assert "(ii) -6" in out["answer"]
    assert "(iii) -3" in out["answer"]


def test_e2e_shared_trailing_context():
    out = _solve_friendly(
        "Find (i) area and (ii) perimeter of a rectangle "
        "with length 5 cm and breadth 3 cm")
    assert out.get("source") == "multipart"
    assert "(i) 15" in out["answer"]
    assert "(ii) 16" in out["answer"]


def test_e2e_shared_preamble_context():
    out = _solve_friendly(
        "A rectangle has length 5 cm and breadth 3 cm. "
        "Find (i) its area (ii) its perimeter")
    assert out.get("source") == "multipart"
    assert "(i) 15" in out["answer"]
    assert "(ii) 16" in out["answer"]


def test_e2e_semicolon_asks():
    out = _solve_friendly(
        "Find the HCF of 12 and 18; find the LCM of "
        "12 and 18")
    assert out.get("source") == "multipart"
    assert "(i) 6" in out["answer"]
    assert "(ii) 36" in out["answer"]


def test_e2e_letter_arithmetic():
    out = _solve_friendly(
        "Calculate: (a) 12 + 18 (b) 25 - 9 (c) 6 x 7")
    assert out.get("source") == "multipart"
    assert "(a) 30" in out["answer"]
    assert "(b) 16" in out["answer"]
    assert "(c) 42" in out["answer"]


def test_e2e_hindi_parts():
    out = _solve_friendly(
        "ज्ञात कीजिए: (क) 12 और 18 का HCF "
        "(ख) 12 और 18 का LCM")
    assert out.get("source") == "multipart"
    assert "(क) 6" in out["answer"]
    assert "(ख) 36" in out["answer"]


def test_e2e_mixed_solved_and_unsolved_parts():
    # Part (ii) asks for a figure that is not there; it
    # must carry the honest per-part line while (i) and
    # (iii) still serve — the card never sinks for one
    # bad part, and no part answer is invented.
    # Wave 204 (Suraj, 20 Nov): ans not found hamesha ke
    # liye band — the per-part line is now the
    # clarification line (fallback._not_found_line).
    q = ("Solve: (i) 2x + 3 = 7 "
         "(ii) find the length of AB in the given figure "
         "(iii) 10 + 5")
    out = _solve_friendly(q)
    assert out.get("source") == "multipart"
    info = out["multipart"]
    assert "i" in info["solved"]
    assert "iii" in info["solved"]
    assert "ii" not in info["solved"]
    steps = "\n".join(out.get("steps") or [])
    assert "(ii)" in steps
    # Wave 204 (Suraj, 20 Nov): ans not found hamesha ke
    # liye band — part (ii) carries the clarification line.
    assert "didn't understand" in steps.lower() \
        or "साफ़ लिखकर" in steps


def test_e2e_verdict_ask_not_answered_with_solutions():
    # NCERT Class 10, Quadratic Equations, Examples —
    # "Check whether the following are quadratic
    # equations": the parts are yes/no checks. An
    # equation's solution set is NOT a verdict, so the
    # layer must not dress solves up as answers here.
    q = ("Check whether the following are quadratic "
         "equations: (i) (x - 2)^2 + 1 = 2x - 3 "
         "(ii) x(x + 1) + 8 = (x + 2)(x - 2) "
         "(iii) x(2x + 3) = x^2 + 1")
    out = general_multipart_result(q)
    if out is not None:
        # Only acceptable if every served part answer is
        # itself a verdict.
        import re
        for bit in out["answer"].split(";"):
            assert re.search(r"\b(yes|no|true|false)\b",
                             bit, re.I), bit


def test_e2e_no_part_solves_returns_none():
    # A split whose parts are all beyond the solver keeps
    # today's behaviour exactly (the layer returns None).
    q = ("Discuss: (i) the role of symmetry in nature "
         "(ii) the role of symmetry in art")
    assert general_multipart_result(q) is None


def test_e2e_cap_five_parts():
    # Six solvable parts: only the first five are answered
    # and one plain line says so — nothing silently drops.
    q = ("Calculate: (a) 1 + 1 (b) 2 + 2 (c) 3 + 3 "
         "(d) 4 + 4 (e) 5 + 5 (f) 6 + 6")
    out = _solve_friendly(q)
    assert out.get("source") == "multipart"
    info = out["multipart"]
    assert info["total"] == 5
    assert info.get("truncated") is True
    assert info.get("parts_total") == 6
    steps = "\n".join(out.get("steps") or [])
    assert "first 5 parts" in steps
    assert "(f)" not in out["answer"]


# ---------------------------------------------------------------------------
# Byte-identical single-part behaviour
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,needle", [
    ("Find the area of a rectangle with length 5 cm and "
     "breadth 3 cm", "15"),
    ("Find the HCF of 12 and 18", "6"),
    ("Solve 2x + 3 = 7", "2"),
    ("12 aur 18 ka HCF batao", "6"),
])
def test_single_part_unchanged(q, needle):
    out = _solve_friendly(q)
    assert out.get("source") != "multipart"
    assert needle in str(out.get("answer"))


def test_mcq_still_mcqs():
    out = _solve_friendly(
        "Find the HCF of 12 and 18: (a) 6 (b) 12 "
        "(c) 3 (d) 36")
    assert out.get("source") == "mcq"
    assert "6" in str(out.get("answer"))


def test_wave100_shapes_still_theirs():
    # The Hence chain still resolves through the Wave 100
    # layer, not the general one.
    out = _solve_friendly(
        "Find the zeroes of the polynomial "
        "p(x) = x² - 3x - 4. Hence, write a polynomial "
        "whose zeroes are reciprocals of the zeroes of "
        "p(x).")
    assert out.get("source") == "multipart"
    assert out["multipart"]["kind"] == "hence_chain"
