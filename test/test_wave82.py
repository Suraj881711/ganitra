"""Wave 82: paper formats — OR bundles, Assertion–Reason,
case-study sets.

The Wave 71 audit counted ~19 papers-sample failures that
are format bundles, not missing mathematics: OR questions
("Solve A OR Solve B" / "… अथवा …"), Assertion–Reason
items, and case-study sets (passage + labelled
sub-questions). formats.py now sits in fallback.with_fallback
after the MCQ layer (fall-through) and beside mcq_preferred
in the real-result branch (formats_preferred):

* OR: alternatives are solved through the ordinary
  machinery; exactly one solving serves it (labelled), both
  solving serves the first with a note, neither falls
  through. A whole-text fragment "solve" of a bundle is
  overruled only when an alternative verifiably solves and
  the whole-text answer matches none of the solved parts.
* Assertion–Reason: only the computable subset — both
  statements must be decided by formats' deciders, the
  explanation judgement needs a structural link or clear
  independence, and an option is never guessed.
* Case study: sub-questions are solved independently
  (passage binder for the defined-function + point
  pattern); unsolved parts carry the one-line not-found;
  no part solving falls through.

The audit questions below are quoted from
ganitra-wave71-results.jsonl (families "Multi-part /
OR-bundle…", "Assertion–Reason format questions", and the
case-study rows).
"""
import pytest

from api import _solve_friendly
from formats import (_part_sanity, assertion_reason_result,
                     case_study_result, extract_ar,
                     extract_case_study, extract_or,
                     formats_result)


# --- The audit questions -------------------------------------

OR_HINDI_PAIRS = (
    "किसी समान्तर श्रेणी का प्रथम पद 5, अन्तिम पद 64 और सभी "
    "पदों का योगफल 400 है। पदों की संख्या एवं सार्व अंतर ज्ञात "
    "कीजिए। अथवा निम्नलिखित समीकरणों को हल कीजिए: "
    "(a) x + y = 5 और 2x - 3y = 4 "
    "(b) 3x + 4y = 10 और 2x - 2y = 2")

OR_HINDI_SYSTEM = (
    "(क) यदि A = [[1, 2, −2], [−1, 3, 0], [0, −2, 1]] तथा "
    "B⁻¹ = [[3, −1, 1], [−15, 6, −5], [5, −2, 2]] है, तो "
    "(AB)⁻¹ ज्ञात कीजिए। अथवा (ख) आव्यूह विधि द्वारा निम्न "
    "समीकरण निकाय को हल कीजिए : x + 2y + 3z = 6, "
    "2x − y + z = 2, 3x + 2y − 2z = 3")

OR_NEITHER = (
    "The difference of squares of two numbers is 180. The "
    "square of the smaller number is eight times the larger "
    "number. Find both the numbers. OR Find two consecutive "
    "positive integers, whose sum of squares is 365.")

AR_P_VALUE = (
    "Assertion (A): The value of p for which the system of "
    "equations 4x + py + 8 = 0 and 2x + 2y + 2 = 0 is "
    "consistent is 4. Reason (R): The system of equations "
    "a1x + b1y = c1 and a2x + b2y = c2 is consistent with "
    "infinitely many solutions, if a1/a2 = b1/b2 = c1/c2. "
    "(A) Both A and R are true and R is the correct "
    "explanation of A (B) Both A and R are true, but R is "
    "not the correct explanation of A (C) A is true, but R "
    "is false (D) A is false, but R is true")

AR_SQRT_HINDI = (
    "अभिकथन (A): √3 एक अपरिमेय संख्या का उदाहरण है। "
    "कारण (R): सभी धनात्मक पूर्णांकों के वर्गमूल अपरिमेय "
    "संख्या होती हैं। "
    "(a) अभिकथन (A) और कारण (R) दोनों सही हैं और कारण (R), "
    "अभिकथन (A) की सही व्याख्या करता है। "
    "(b) अभिकथन (A) और कारण (R) दोनों सही हैं, लेकिन कारण "
    "(R), अभिकथन (A) की सही व्याख्या नहीं है। "
    "(c) अभिकथन (A) सही है, लेकिन कारण (R) गलत है। "
    "(d) अभिकथन (A) गलत है, लेकिन कारण (R) सही है।")

AR_BIJECTIVE = (
    "Assertion (A): Let Z be the set of integers. A function "
    "f : Z → Z defined as f(x) = 3x − 5, for all x ∈ Z, is "
    "bijective. Reason (R): A function is bijective if it "
    "is both surjective and injective. "
    "(Assertion-Reason question)")

AR_AXES = (
    "Assertion (A): A line in space cannot be drawn "
    "perpendicular to x, y and z axes simultaneously. "
    "Reason (R): For any line making angles α, β, γ with "
    "the positive directions of x, y and z axes "
    "respectively, cos²α + cos²β + cos²γ = 1. "
    "(Assertion-Reason question)")

AR_AXES_HINDI = (
    "अभिकथन (A) : अंतरिक्ष में एक रेखा कभी भी एक साथ x, y "
    "और z अक्षों के लंबवत नहीं हो सकती है। तर्क (R) : किसी "
    "रेखा द्वारा x, y और z अक्षों की धनात्मक दिशाओं के साथ "
    "क्रमशः α, β और γ के कोण बनाने पर cos²α + cos²β + "
    "cos²γ = 1 है। (अभिकथन-तर्क प्रश्न)")

CASE_ROLLER = (
    "Case study: The equation of the path traced by a "
    "roller-coaster is given by the polynomial "
    "f(x) = a(x + 9)(x + 1)(x − 3). If the roller-coaster "
    "crosses the y-axis at the point (0, 1), answer the "
    "following: (i) Find the value of a. "
    "(ii) Find f′(x) at x = 1.")

CASE_RWA = (
    "Case study: Resident Welfare Association (RWA) of a "
    "society put up three electric poles A, B and C in a "
    "society's park. Despite these three poles, some part "
    "of the park are still in dark, so RWA decides to have "
    "one more electric pole D in the park. Based on the "
    "above information, answer the following questions: "
    "(i) Find the position of the pole C. (ii) Find the "
    "distance of the pole B from corner O of the park. "
    "(iii)(a) Find the position of the fourth pole D so "
    "that four points A, B, C and D form a parallelogram. "
    "or (b) Find the distance between poles A and C. "
    "(Positions are read from the park diagram printed in "
    "the paper.)")

CASE_PARTIAL = (
    "Case study: A school canteen sells pens and notebooks. "
    "Based on the above information, answer the following "
    "questions: (i) Find 15% of 200. "
    "(ii) Find the HCF of 12 and 18. "
    "(iii) Evaluate the integral of x^x dx.")


# --- Extraction ----------------------------------------------

def test_extract_or_labels():
    alts = extract_or(OR_HINDI_SYSTEM)
    assert [label for label, _t in alts] == ["क", "ख"]
    assert "समीकरण निकाय" in alts[1][1]


def test_extract_or_rejects_plain_questions_and_mcqs():
    assert extract_or("What is 2 + 2?") is None
    assert extract_or(
        "What is 25% of 80? (a) 10 (b) 20 (c) 25 (d) 40"
    ) is None


def test_extract_ar_with_options():
    a_text, r_text, options = extract_ar(AR_P_VALUE)
    assert "value of p" in a_text
    assert "a1/a2" in r_text
    assert [label for label, _t in options] == \
        ["A", "B", "C", "D"]


def test_extract_case_study_parts():
    passage, parts = extract_case_study(CASE_ROLLER)
    assert "f(x) = a(x + 9)" in passage
    assert [label for label, _s in parts] == ["i", "ii"]


# --- OR bundles ------------------------------------------------

def test_or_one_alternative_solves_hindi_pairs():
    result = _solve_friendly(OR_HINDI_PAIRS)
    assert result.get("source") == "or"
    assert result["or"]["both_solved"] is False
    assert "19/5" in result["answer"]
    assert "x = 2, y = 1" in result["answer"]


def test_or_system_alternative_beats_fragment_solve():
    # In the pre-wave tree the whole bundle "solves" to the
    # fragment 2*x - y + 6; the (ख) alternative really solves
    # and must be served instead.
    result = _solve_friendly(OR_HINDI_SYSTEM)
    assert result.get("source") == "or"
    assert "x = 1" in result["answer"]
    assert "z = 1" in result["answer"]


def test_or_both_alternatives_solve_serves_first():
    result = _solve_friendly(
        "Solve 2x + 3 = 11 OR Solve 3x - 5 = 10")
    assert result.get("source") == "or"
    assert result["or"]["both_solved"] is True
    assert result["answer"] == "x = 4"


def test_or_exactly_one_solves_english():
    result = _solve_friendly(
        "Find the HCF of 12 and 18 OR Evaluate the integral "
        "of x^x dx")
    assert result.get("source") == "or"
    assert result["or"]["both_solved"] is False
    assert result["answer"] == "6"


def test_or_neither_solves_falls_through():
    result = _solve_friendly(OR_NEITHER)
    assert result.get("source") != "or"
    assert result.get("fallback_kind") == "not_found"


def test_part_sanity_rejects_matrix_add_for_inverse_ask():
    # The router's matrix fallback "solves" the (AB)^-1
    # alternative of OR_HINDI_SYSTEM by adding A + B^-1
    # entry by entry. An entrywise add/subtract can never
    # answer an inverse or determinant ask, so the part
    # layer must reject that shape — while a genuine add
    # ask, or a real inverse result, still passes.
    added = {"op": "add",
             "answer": "[[4, 1, -1], [-16, 9, -5], [5, -4, 3]]"}
    inverse_ask = ("यदि A = [[1, 2, −2]] तथा "
                   "B⁻¹ = [[3, −1, 1]] है, तो (AB)⁻¹ ज्ञात कीजिए")
    assert _part_sanity(inverse_ask, added) is False
    assert _part_sanity(
        "Find the determinant of A = [[1, 2]] and "
        "B = [[3, 4]]", added) is False
    assert _part_sanity(
        "Add A = [[1, 2]] and B = [[3, 4]]", added) is True
    assert _part_sanity(
        inverse_ask, {"op": "inverse", "answer": "[[1]]"}
    ) is True


# --- Assertion–Reason ------------------------------------------

def test_ar_p_value_is_false_reason_true():
    # At p = 4 the pair is parallel (no solution), so the
    # assertion that p = 4 makes it consistent is FALSE;
    # R states the standard infinitely-many condition.
    result = assertion_reason_result(AR_P_VALUE)
    assert result is not None
    assert result["answer"].startswith("(D)")
    assert result["assertion_reason"]["a_true"] is False
    assert result["assertion_reason"]["r_true"] is True


def test_ar_sqrt_hindi_option_c():
    result = assertion_reason_result(AR_SQRT_HINDI)
    assert result is not None
    assert result["answer"].startswith("(c)")
    assert result["assertion_reason"]["combo"] == "TF"


def test_ar_bijective_standard_wording():
    result = assertion_reason_result(AR_BIJECTIVE)
    assert result is not None
    assert result["answer"].startswith("(d)")
    assert result["assertion_reason"]["a_true"] is False


def test_ar_axes_both_true_and_explains():
    result = assertion_reason_result(AR_AXES)
    assert result is not None
    assert result["answer"].startswith("(a)")
    assert result["assertion_reason"]["combo"] == "TT_exp"


def test_ar_axes_hindi():
    result = assertion_reason_result(AR_AXES_HINDI)
    assert result is not None
    assert result["answer"].startswith("(a)")


def test_ar_both_true_independent_facts():
    result = assertion_reason_result(
        "Assertion (A): HCF of 12 and 18 is 6. "
        "Reason (R): LCM of 12 and 18 is 36.")
    assert result is not None
    assert result["answer"].startswith("(b)")
    assert result["assertion_reason"]["combo"] == "TT_noexp"


def test_ar_false_value_claim():
    result = assertion_reason_result(
        "Assertion (A): HCF of 12 and 18 is 9. "
        "Reason (R): LCM of 12 and 18 is 36.")
    assert result is not None
    assert result["answer"].startswith("(d)")
    assert result["assertion_reason"]["a_true"] is False


def test_ar_undecidable_never_guesses():
    # A is in fact false (2 is an even prime) and R true —
    # but neither statement is in the computable subset, so
    # the layer must fall through rather than guess (d).
    assert assertion_reason_result(
        "Assertion (A): Every prime number is odd. "
        "Reason (R): 2 is the only even prime number."
    ) is None
    result = _solve_friendly(
        "Assertion (A): Every prime number is odd. "
        "Reason (R): 2 is the only even prime number.")
    assert result.get("source") != "assertion_reason"


def test_ar_end_to_end_through_chat_path():
    result = _solve_friendly(AR_P_VALUE)
    assert result.get("source") == "assertion_reason"
    assert result["answer"].startswith("(D)")


# --- Case-study sets ---------------------------------------------

def test_case_study_roller_coaster_both_parts():
    result = _solve_friendly(CASE_ROLLER)
    assert result.get("source") == "case_study"
    assert "-1/27" in result["answer"]
    assert "4/27" in result["answer"]
    assert [p["solved"] for p in
            result["case_study"]["parts"]] == [True, True]


def test_case_study_partial_marks_unsolved_part():
    result = case_study_result(CASE_PARTIAL)
    assert result is not None
    assert [p["solved"] for p in
            result["case_study"]["parts"]] == \
        [True, True, False]
    assert "30" in result["answer"]
    assert "6" in result["answer"]
    # Wave 204 (Suraj, 20 Nov): ans not found hamesha ke liye band
    # — the unsolved part's line is the clarification line.
    assert "I didn't understand that — type your maths " \
        "question a little clearly and I'll solve it " \
        "right away." in result["answer"]


def test_case_study_diagram_only_falls_through():
    # Every RWA sub-question needs the printed park diagram;
    # nothing is textually solvable, so the set falls
    # through unchanged.
    assert case_study_result(CASE_RWA) is None
    result = _solve_friendly(CASE_RWA)
    assert result.get("source") != "case_study"


def test_formats_result_ignores_ordinary_questions():
    assert formats_result("What is 2 + 2?") is None
    assert formats_result(
        "What is 25% of 80? (a) 10 (b) 20 (c) 25 (d) 40"
    ) is None
