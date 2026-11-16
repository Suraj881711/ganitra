"""Wave 76: MCQ mode — solve the stem, match the option.

The Wave 71 solver-health audit found the board-papers
surface weakest (35/150 sample questions solved) with 75 of
its 115 failures carrying MCQ options the app could not use:
the full text (stem + options) defeats the solver, and the
honest layers could only salvage a fragment or serve a
concept card for a concrete problem.

mcq.py now sits in fallback.with_fallback in two places:
mcq_wrap names the matched option when the whole text solved
as-is, and mcq_result (after the science guard and the bank,
before salvage) extracts stem + options, solves the STEM
through the ordinary machinery, and serves the stem's own
steps with a final answer naming the one option the computed
value matches. No match, two matches, or an unsolvable stem
falls through to the previous behaviour — an option is never
guessed.

The questions below are real board-paper shapes sampled from
the Wave 71 papers battery plus hand-built guards.
"""
import pytest

from api import _solve_friendly
from mcq import extract_mcq, mcq_result


# --- Extraction ----------------------------------------------

def test_extract_paren_letters():
    stem, options = extract_mcq(
        "What is 25% of 80? (a) 10 (b) 20 (c) 25 (d) 40")
    assert stem.startswith("What is 25% of 80?")
    assert options == [("a", "10"), ("b", "20"),
                       ("c", "25"), ("d", "40")]


def test_extract_bare_letters_and_newlines():
    stem, options = extract_mcq(
        "Solve for x: 2x + 3 = 11 A. 3 B. 4 C. 5 D. 7")
    assert [t for _l, t in options] == ["3", "4", "5", "7"]
    stem, options = extract_mcq(
        "If x + 5 = 9, then x = ?\n(a) 2\n(b) 4\n(c) 5\n(d) 14")
    assert [t for _l, t in options] == ["2", "4", "5", "14"]


def test_extract_numbered_and_cued():
    stem, options = extract_mcq(
        "What is 3 + 4? (1) 6 (2) 7 (3) 8 (4) 9")
    assert [t for _l, t in options] == ["6", "7", "8", "9"]
    stem, options = extract_mcq(
        "The value of 5 + 3 is options are 6, 7, 8, 9")
    assert [t for _l, t in options] == ["6", "7", "8", "9"]


def test_extract_rejects_non_mcq_and_out_of_scope():
    assert extract_mcq("What is 2 + 2?") is None
    # Assertion–Reason is out of scope for this wave.
    assert extract_mcq(
        "Assertion (A): 2 is a prime number. Reason (R): 2 has "
        "exactly two factors. (a) Both A and R are true "
        "(b) A is true, R is false") is None
    # Sub-questions are not options (the labels are fine but
    # the "options" are questions, not values).
    got = extract_mcq("Find (a) HCF of 12 and 18? (b) LCM of "
                      "12 and 18?")
    assert got is None


# --- MCQ answers through the real chat path -------------------

MCQ_SOLVES = [
    # numeric
    ("What is 25% of 80? (a) 10 (b) 20 (c) 25 (d) 40", "(b) 20"),
    # fraction
    ("Simplify: 1/7 ÷ 2/7 (a) 1/2 (b) 2 (c) 1/49 (d) 49",
     "(a) 1/2"),
    # algebra
    ("Solve for x: 2x + 3 = 11 A. 3 B. 4 C. 5 D. 7", "(B) 4"),
    # number theory
    ("Find the HCF of 12 and 18. (A) 3 (B) 6 (C) 9 (D) 36",
     "(B) 6"),
    # trigonometry with unicode operators / superscripts
    ("cos²27° − sin²63° = (A) −1 (B) 0 (C) 1 (D) 1/2", "(B) 0"),
    # Hindi (Devanagari) stem
    ("80 का 25% कितना होगा? (a) 10 (b) 20 (c) 30 (d) 40",
     "(b) 20"),
    # Hinglish stem
    ("12 aur 18 ka HCF kya hai? (a) 3 (b) 6 (c) 9 (d) 12",
     "(b) 6"),
    # newline-separated options
    ("If x + 5 = 9, then x = ?\n(a) 2\n(b) 4\n(c) 5\n(d) 14",
     "(b) 4"),
    # cued comma list
    ("The value of 5 + 3 is options are 6, 7, 8, 9", "(c) 8"),
]


@pytest.mark.parametrize("question,want", MCQ_SOLVES)
def test_mcq_solves(question, want):
    result = _solve_friendly(question)
    assert result.get("source") == "mcq"
    assert result.get("answer") == want
    # The stem's own solving steps ride along.
    assert result.get("steps")


# --- The honesty guards ----------------------------------------

def test_unsolvable_stem_falls_through_without_guessing():
    # The stem asks for a formula in n; the solver cannot
    # produce it, so NO option may be named — the existing
    # layers answer (or honestly decline) as before.
    result = _solve_friendly(
        "The sum of first n odd natural numbers is "
        "(A) n² − 1 (B) n + 1 (C) 2n − 1 (D) n²")
    assert result.get("source") != "mcq"
    assert not str(result.get("answer", "")).startswith("(D)")


def test_stem_letters_do_not_break_extraction():
    # The stem's own parenthesised letters — P(E), P(F),
    # P(A/B) — are not options; the consecutive a–d run at
    # the end is. For independent events P(E | F') = P(E).
    result = _solve_friendly(
        "If E and F are two independent events such that "
        "P(E) = 2/3 and P(F) = 3/7, then P(E | F′) is equal "
        "to: (A) 1/6 (B) 1/2 (C) 2/3 (D) 7/9")
    assert result.get("source") == "mcq"
    assert result.get("answer") == "(C) 2/3"


def test_vector_unicode_junk_is_not_matched():
    # The solver shreds unit-vector notation into letter
    # products (the audit's vector-unicode family); such a
    # "value" must never be matched against an option — the
    # correct option here is (c) −ĵ, and the layer must stay
    # silent rather than name the junk-matching (d).
    assert mcq_result(
        "î × k̂ = (a) 0⃗ (b) ĵ (c) −ĵ (d) k̂ × î") is None


def test_knowledge_mcq_is_not_guessed():
    # A pure-recall item (ordinate of a point on the x-axis):
    # nothing to compute, so the layer must stay silent.
    assert mcq_result(
        "x-अक्ष पर स्थित सभी बिन्दुओं की कोटि होती है– "
        "(a) 0 (b) 1 (c) 2 (d) −1") is None


def test_duplicate_options_are_not_guessed():
    # Two identical options both match the value — ambiguous,
    # so the layer falls through instead of picking one.
    assert mcq_result(
        "What is 10 + 10? (a) 20 (b) 20 (c) 30 (d) 40") is None


def test_nonmaths_mcq_keeps_the_guard():
    result = _solve_friendly(
        "What is the capital of India? (a) Delhi (b) Mumbai "
        "(c) Jaipur (d) Kolkata")
    assert result.get("fallback_kind") == "nonmaths"
    assert result.get("source") != "mcq"


# --- Non-MCQ questions are untouched ---------------------------

def test_plain_questions_unaffected():
    result = _solve_friendly("What is 2 + 2?")
    assert result.get("answer") == "4"
    assert result.get("source") != "mcq"
    result = _solve_friendly("Find the HCF of 12 and 18")
    assert result.get("answer") == "6"
    assert result.get("source") != "mcq"


def test_concept_ask_unaffected():
    result = _solve_friendly("prime number kya hota hai?")
    assert result.get("fallback_kind") == "concept"
    assert result.get("source") != "mcq"


def test_gibberish_still_one_line():
    result = _solve_friendly("If tu gfuf")
    assert result.get("fallback_kind") == "not_found"
