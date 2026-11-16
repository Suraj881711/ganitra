"""Wave 77: the chat-wrapper core pass — wrapper-stripping
normalisation inside the solver.

The Wave 71 audit counted 88 SALVAGE verdicts; ~67 of them
were one family: chat-phrased equations and discount problems
wrapped in conversation ("samikaran 2x + 3 = 7 hal karo",
"agar 2^x = 32 hai to x kitna hoga?", "800 rs wali cheez par
25% ki chhoot hai, final price batao?"). The intent solvers
read the wrapper words as extra variables and produced
letter-soup ("a = 0") or a parse error, so the questions fell
through to the fallback layer's salvage, which re-solved the
extracted core but served it flagged as a salvage.

solver/router.py now carries a Wave 77 pass at the end of
_solve_question_uncached: when the primary result is a
failure or letter-soup, it extracts the maths core (equation,
evaluate-at substitution, "% of", arithmetic chain,
filler-stripped whole) and solves it through the ordinary
pipeline, returning a genuine solver result. These tests pin
the family, the Wave 74 trap, and the non-guessing guards.
"""
import pytest

from api import _solve_friendly
from solver.router import _w77_candidates, _w77_evaluate_at, \
    solve_question


def _solver_answer(question):
    """The answer when the REAL solver claims the question
    (no fallback flag of any kind), else None."""
    result = _solve_friendly(question)
    if result.get("fallback_kind") is not None:
        return None
    return str(result.get("answer", ""))


# --- Chat-phrased linear equations ----------------------------

@pytest.mark.parametrize("question,expected", [
    ("samikaran 2x + 3 = 7 hal karo", "x = 2"),
    ("samikaran 5x + 3 = 18 hal karo", "x = 3"),
    ("my homework says find x when 3x + 7 = 22 please batao",
     "x = 5"),
    ("iska jawab batao 2x + 3 = 7", "x = 2"),
    ("plz solve 5x - 3 = 12", "x = 3"),
    ("bhai ye wala bata do 4x + 5 = 21", "x = 4"),
    ("homework: find the value of x in 12x - 7 = 29", "x = 3"),
    ("ek equation hai 5x + 9 = 2x + 24", "x = 5"),
    ("3x = 12 hai to x kitna hoga?", "x = 4"),
    ("7x = 35 hai to x kitna hoga?", "x = 5"),
    ("Solve karo agar 5x = 45 hai to x kitna hoga?", "x = 9"),
    ("bhai equation 2x = 14 me x ki value batao plz yr?",
     "x = 7"),
    ("7x - 5 = 30 hai to x ki value kya hogi?", "x = 5"),
    ("agar 4x + 9 = 45 h to x btao na", "x = 9"),
    ("eqation 6x + 4 = 34 me x ka jwab btao", "x = 5"),
    ("slove the eqation 6x - 7 = 29", "x = 6"),
])
def test_wrapped_linear_equations_solve_for_real(question,
                                                 expected):
    assert _solver_answer(question) == expected


# --- Chat-phrased quadratic equations -------------------------

@pytest.mark.parametrize("question,expected", [
    ("ye solve kar do x^2 - 7x + 12 = 0", "x = 3, x = 4"),
    ("doubt hai isme x2 - 3x - 10 = 0", "x = -2, x = 5"),
    ("ye samjha do x^2 + 2x - 15 = 0", "x = -5, x = 3"),
    ("Solve the quadratic x2 - 5x + 6 = 0 karo, roots batao?",
     "x = 2, x = 3"),
    ("oye equation x2 - 6x + 5 = 0 ko solve krke roots "
     "nikaalo?", "x = 1, x = 5"),
    ("samikaran x2 - 10x + 24 = 0 ke mool bta do",
     "x = 4, x = 6"),
    ("samikaran x2 - 3x - 40 = 0 ke mool kya hain?",
     "x = -5, x = 8"),
    ("solve karo x2 - 15x + 56 = 0 ko, roots batao",
     "x = 7, x = 8"),
])
def test_wrapped_quadratics_solve_for_real(question, expected):
    assert _solver_answer(question) == expected


# --- Exponential equations in Hinglish ------------------------

@pytest.mark.parametrize("question,expected_prefix", [
    ("agar 2^x = 32 hai to x kitna hoga?", "x = 5"),
    ("agar 3^x = 81 hai to x kitna hoga?", "x = 4"),
    ("agar 2^x = 64 hai to x kitna hoga?", "x = 6"),
    ("agar 5^x = 125 hai to x kitna hoga?", "x = 3"),
    ("agar 10^x = 1000 hai to x kitna hoga?", "x = 3"),
    ("agar 7^x = 49 hai to x kitna hoga?", "x = 2"),
    ("agar 2^x =32 haito x ktna hogaa?", "x = 5"),
])
def test_wrapped_exponentials_solve_for_real(question,
                                             expected_prefix):
    answer = _solver_answer(question)
    assert answer is not None
    assert answer.startswith(expected_prefix)


# --- Discount / final-price (Hinglish shop phrasing) ----------

@pytest.mark.parametrize("question,expected", [
    ("800 rs wali cheez par 25% ki chhoot hai, final price "
     "batao?", "Rs 600"),
    ("650 rs wali cheez par 10% ki chhoot hai, final price "
     "batao?", "Rs 585"),
    ("450 rs wali cheez par 40% ki chhoot hai, final price "
     "batao?", "Rs 270"),
    ("750 rs wali cheez par 20% ki chhoot hai, final price "
     "bataao?", "Rs 600"),
    ("500 rs wali cheez par 20% ki chhoot hay, kitnah dena "
     "hogah?", "Rs 400"),
    ("1200 rs wali cheez par 30% ki chhoot hay, kitnah dena "
     "hogah?", "Rs 840"),
    ("ek dukaan par 1200 rs ka joota rakha tha, sale me uspar "
     "30% ki chhoot mili aur dukaan par lambi line thi, joota "
     "kitne me milega?", "Rs 840"),
])
def test_wrapped_discounts_solve_for_real(question, expected):
    assert _solver_answer(question) == expected


# --- Simple wrapped arithmetic / mensuration ------------------

@pytest.mark.parametrize("question,expected", [
    ("oye 1/2 + 1/3 kitna hoga plz yr?", "5/6"),
    ("fractions 5/9 + 2/9 ?", "7/9"),
    ("mujhe sirf anser chahiey: 45 + 37 + 18 kitna hoga?",
     "100"),
    ("can u tell the volume of a cuboid 9 x 6 x 5 cm?", "270"),
    ("Evaluate: 27 + 2 × 12 − 6", "45"),
])
def test_wrapped_simple_items_solve_for_real(question,
                                             expected):
    answer = _solver_answer(question)
    assert answer is not None
    assert expected in answer


@pytest.mark.parametrize("question,expected", [
    # Decimal products/sums are served as exact fractions —
    # the same strings the salvage layer used to serve.
    ("Multiply: 2.9 × 6.8", "19.72"),
    ("Add: 16.06 + 81.4", "97.46"),
    ("Multiply: 4 × 7.7", "30.8"),
])
def test_wrapped_decimal_items_match_numerically(question,
                                                 expected):
    from fractions import Fraction
    answer = _solver_answer(question)
    assert answer is not None
    assert Fraction(answer) == Fraction(expected)


def test_wrapped_sphere_surface_area():
    answer = _solver_answer(
        "Sphere ka radius 7 cm hai to uska surface area find "
        "karo?")
    assert answer is not None
    assert "615.75" in answer


# --- The Wave 74 trap: evaluate-at ----------------------------

def test_evaluate_at_is_not_an_assignment_echo():
    """'find the value of 2x + 3 when x = 4' must be answered
    11 by the real solver — never the salvaged echo 'x = 4'
    and never a worse substitute."""
    result = _solve_friendly("find the value of 2x + 3 when "
                             "x = 4")
    assert result.get("fallback_kind") is None
    assert str(result.get("answer")) == "11"


def test_evaluate_at_helper_substitutes():
    assert _w77_evaluate_at(
        "find the value of 2x + 3 when x = 4") == "2*(4) + 3"
    assert _w77_evaluate_at(
        "find the value of x^2 + 2x when x = 4") == \
        "(4)^2 + 2*(4)"
    # A real equation is not an evaluate-at ask.
    assert _w77_evaluate_at("solve 2x + 3 = 7") is None
    # Two assignments: not this shape.
    assert _w77_evaluate_at(
        "find 2x + 3 when x = 4 and y = 2") is None


def test_assignment_is_never_a_candidate():
    cands = _w77_candidates("find the value of 2x + 3 when "
                            "x = 4")
    assert "x = 4" not in cands
    assert cands[0] == "2*(4) + 3"


# --- Fragment guards ------------------------------------------

def test_chain_inside_a_larger_expression_is_not_a_core():
    """'5 - 2' inside '5 - 2√3' is a fragment: the chain from
    the question's other half must win instead."""
    cands = _w77_candidates(
        "Show that the number 5 × 11 × 17 + 3 × 11 is a "
        "composite number, and 5 - 2√3 is irrational")
    assert "5 - 2" not in cands
    assert "5 × 11 × 17 + 3 × 11" in cands


def test_bracketed_hint_is_not_a_core():
    """'[Use π = 22/7]' is an instruction: its fraction must
    not pose as the question's arithmetic chain."""
    cands = _w77_candidates(
        "A wire is bent into an arc of a circle. Find the "
        "radius. [Use π = 22/7]")
    assert "22/7" not in cands


def test_scientific_notation_chain_still_refused():
    cands = _w77_candidates("speed of light is 3 x 10^8 m/s "
                            "batao")
    assert "3 x 10" not in cands


# --- Non-guessing / no-regression guards ----------------------

def test_gibberish_still_gets_the_one_line_not_found():
    result = _solve_friendly("If tu gfuf")
    assert result.get("fallback_kind") == "not_found"


def test_concept_ask_still_gets_the_concept_card():
    result = _solve_friendly("what is a prime number")
    assert result.get("fallback_kind") == "concept"


def test_genuine_no_solution_equation_unchanged():
    """A wrapped equation with no solution must not be
    'fixed' into a fake one: it stays exactly what the
    pristine solver says."""
    question = "bhai 2x + 3 = 2x + 5 solve karo"
    result = _solve_friendly(question)
    pristine = solve_question("2x + 3 = 2x + 5")
    assert str(result.get("answer")) == str(
        pristine.get("answer"))


def test_already_solved_questions_untouched():
    for question, expected in [("What is 15% of 240?", "36"),
                               ("solve 3x + 7 = 22", "x = 5"),
                               ("2 + 2", "4")]:
        result = _solve_friendly(question)
        assert result.get("fallback_kind") is None
        assert str(result.get("answer")) == expected


def test_mcq_questions_stay_with_the_mcq_layer():
    result = _solve_friendly(
        "What is 25% of 80? (a) 10 (b) 20 (c) 25 (d) 40")
    assert result.get("source") == "mcq"
    assert "(b) 20" in str(result.get("answer"))
