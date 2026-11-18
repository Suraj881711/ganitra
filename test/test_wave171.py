"""Wave 171: Tier-A phrasing coverage (Wave 169 follow-up).

The Deploy-40 live check (19 Nov 2026) found "Find two
rational numbers between 3/5 and 4/5" answered correctly ONLY
via the Gemini fallback leg.  Root cause, in two layers:

  1. The Wave 169 between schema itself DID match the
     phrasing — but the router never reached it.  The primary
     arithmetic solver errors on the wordy question, the
     Wave 77 wrapper-core pass then extracts the bare
     fragment "3/5" and returns its evaluation (op
     "evaluate", answer "3/5"), and every failure-only gate
     below it — Wave 169 included — is bypassed.  (Integer /
     decimal endpoints worked in Wave 169's own router tests
     because no bare expression core exists to extract.)
  2. Sibling natural phrasings missed the schemas directly:
     a sentence-final "?", "lying between", a verb-less ask,
     the roman-Hinglish "… aur … ke beech … batao" forms,
     "whose arc is …", "… units to its left", "the line
     joining A and B", "with x-intercept" without "and
     having", bare "parallel to 3i + 2j - 2k", a probability
     table stated before its "is the distribution" words,
     "bought … for Rs X and sold it for Rs Y", "buys …
     sells", and "at 5% for 2 years".

Fix: solver/tierA169.py patterns broadened conservatively
(every pattern still strict — count + keyword + two clean
endpoints / complete shape, exact recomputation, decline on
ambiguity) and a Wave 171 fragment-hijack repair in
solver/router.py's gate area (_w171_fragment_hijack + an
intercept in the Wave 77 core return + a post-gate block):
a strict tierA169 answer displaces a primary/core result
ONLY when that result is a measured fragment shape
("evaluate" / "area" / perpendicular "line equation") with
a verifiably different answer.  Correct primary answers
(simple interest 180, profit percent 25%) are never
displaced — pinned below.
"""
from fractions import Fraction

from solver.router import solve_question
from solver.tierA169 import solve_tierA169

LIVE_Q = "Find two rational numbers between 3/5 and 4/5"


def ans(q):
    out = solve_tierA169(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_tierA169(q) is None, q


def _vals(a_str):
    return [Fraction(t) for t in a_str.split(", ")]


# ---------------------------------------------------------------------------
# The live-missed question, verbatim — schema and router
# ---------------------------------------------------------------------------

def test_live_question_schema_claims_it():
    out = solve_tierA169(LIVE_Q)
    assert out is not None
    assert out["op"] == "w169_rationals_between"
    # hand-computed: gap 1/5 split in 3 -> step 1/15;
    # 3/5 + 1/15 = 2/3, 3/5 + 2/15 = 11/15
    assert out["answer"] == "2/3, 11/15"


def test_live_question_router_serves_native_not_fragment():
    out = solve_question(LIVE_Q)
    assert out["op"] == "w169_rationals_between"
    assert out["answer"] == "2/3, 11/15"


def test_live_question_with_question_mark():
    assert ans(LIVE_Q + "?") == "2/3, 11/15"
    out = solve_question(LIVE_Q + "?")
    assert out["op"] == "w169_rationals_between"


def test_live_question_with_period_and_lowercase():
    assert ans(LIVE_Q + ".") == "2/3, 11/15"
    assert ans("find two rational numbers between 3/5 and 4/5") \
        == "2/3, 11/15"


# ---------------------------------------------------------------------------
# Between family: phrasing variants (hand-computed)
# ---------------------------------------------------------------------------

def test_between_word_count_three():
    # gap 3/4 - 2/3 = 1/12, step 1/48: 11/16, 17/24, 35/48
    assert ans("Write three rational numbers between 2/3 and 3/4") \
        == "11/16, 17/24, 35/48"


def test_between_digit_count():
    assert ans("Find 2 rational numbers between 3/5 and 4/5") \
        == "2/3, 11/15"


def test_between_give_me_and_bare_give():
    assert ans("Give me two rational numbers between 1/3 and 1/2") \
        == "7/18, 4/9"
    assert ans("Give two rational numbers between 3/5 and 4/5") \
        == "2/3, 11/15"
    assert ans("State two rational numbers between 3/5 and 4/5") \
        == "2/3, 11/15"


def test_between_single_with_a_and_one():
    assert ans("Find a rational number between 1/2 and 3/4") == "5/8"
    assert ans("Find one rational number between 2/5 and 3/5") == "1/2"


def test_between_insert_and_list_verbs():
    assert ans("Insert two rational numbers between 1/4 and 1/2") \
        == "1/3, 5/12"
    vals = _vals(ans("List three rational numbers between -2 and -1"))
    assert len(vals) == 3 and all(-2 < v < -1 for v in vals)


def test_between_decimal_endpoints():
    # 0.5 = 1/2, 0.75 = 3/4; step (1/4)/3 = 1/12
    assert ans("Find two rational numbers between 0.5 and 0.75") \
        == "7/12, 2/3"
    vals = _vals(ans("Find two rational numbers between 0.75 and 0.8"))
    assert all(Fraction(3, 4) < v < Fraction(4, 5) for v in vals)


def test_between_integer_endpoints():
    assert ans("Find three rational numbers between 2 and 3") \
        == "9/4, 5/2, 11/4"


def test_between_negative_endpoints():
    assert ans("Find two rational numbers between -3/4 and -1/4") \
        == "-7/12, -5/12"
    # the gate-blocked sibling: the primary evaluates "1/2"
    assert ans("Find two rational numbers between -1/2 and 1/2") \
        == "-1/6, 1/6"
    out = solve_question("Find two rational numbers between "
                         "-1/2 and 1/2")
    assert out["op"] == "w169_rationals_between"
    assert out["answer"] == "-1/6, 1/6"


def test_between_reversed_endpoints():
    assert ans("Find two rational numbers between 4/5 and 3/5") \
        == "2/3, 11/15"


def test_between_spaces_around_slash():
    assert ans("Find two rational numbers between 3 / 5 and 4 / 5") \
        == "2/3, 11/15"


def test_between_lying_and_verbless_and_please():
    assert ans("Find two rational numbers lying between "
               "3/5 and 4/5") == "2/3, 11/15"
    assert ans("two rational numbers between 3/5 and 4/5") \
        == "2/3, 11/15"
    assert ans("Find two rational numbers between 3/5 and 4/5 "
               "please") == "2/3, 11/15"
    assert ans("Please find two rational numbers between "
               "3/5 and 4/5") == "2/3, 11/15"


def test_between_hinglish_batao_before_endpoints():
    # ek = 1; midpoint of 1/2 and 3/4 is 5/8
    assert ans("ek rational number batao 1/2 aur 3/4 ke beech") \
        == "5/8"
    out = solve_question("ek rational number batao 1/2 aur "
                         "3/4 ke beech")
    assert out["op"] == "w169_rationals_between"


def test_between_hinglish_endpoints_first():
    assert ans("1/2 aur 3/4 ke beech ek rational number batao") \
        == "5/8"
    # do = 2; step (1/4)/3 = 1/12 -> 7/12, 2/3
    assert ans("1/2 aur 3/4 ke beech mein do rational numbers "
               "batao") == "7/12, 2/3"


def test_between_hinglish_count_first_batao_last():
    assert ans("do rational numbers 1/2 aur 3/4 ke beech batao") \
        == "7/12, 2/3"


def test_between_irrationals_with_fraction_endpoints():
    a = ans("Find two irrational numbers between 1/2 and 3/4")
    vals = [float(t) for t in a.split(", ")]
    assert len(vals) == 2 and all(0.5 < v < 0.75 for v in vals)
    out = solve_question("Find two irrational numbers between "
                         "1/2 and 3/4")
    assert out["op"] == "w169_irrationals_between"


def test_between_router_fraction_endpoints_five():
    out = solve_question("Find five rational numbers between "
                         "1/2 and 3/4.")
    assert out["op"] == "w169_rationals_between"
    vals = _vals(out["answer"])
    assert len(vals) == 5
    assert all(Fraction(1, 2) < v < Fraction(3, 4) for v in vals)


# ---------------------------------------------------------------------------
# Between family: declines
# ---------------------------------------------------------------------------

def test_between_nonmathematical_between_declines():
    declines("What is the distance between 3/5 and 4/5")
    declines("The meeting is between 3 and 4")
    declines("Find the rational number between us")


def test_between_missing_or_bad_endpoints_decline():
    declines("Find two rational numbers between 3/5")
    declines("Find two rational numbers between and")
    declines("Find two rational numbers between 5 and 5")


def test_between_absurd_counts_decline():
    declines("Find zero rational numbers between 1 and 2")
    declines("Find 0 rational numbers between 1 and 2")
    declines("Find 100 rational numbers between 1 and 2")
    declines("How many rational numbers are there between 1 and 2")


def test_between_three_endpoints_declines():
    # Wave 171: the third endpoint used to be silently dropped
    declines("Find two rational numbers between 3/5 and 4/5 "
             "and 5/6")


# ---------------------------------------------------------------------------
# Other families: natural phrasings the pool forms missed
# ---------------------------------------------------------------------------

def test_sector_whose_arc_is():
    assert ans("What is the area of a sector whose radius is "
               "14 mm and whose arc is 50 mm?") == "350"


def test_sector_of_a_circle_direct():
    # schema-level claim; the ROUTER still serves the geometry
    # pre-route's circle area for this exact phrasing (the
    # pre-route sits outside the Wave 171 gate area — a known
    # leftover, flagged in the wave notes, not pinned here).
    assert ans("Find the area of the sector of a circle with "
               "radius 3.5 cm and length of arc 2.2 cm.") == "77/20"


def test_line_axis_parallel_units_to_left():
    assert ans("Write the equation of the line parallel to the "
               "y-axis and 7 units to its left.") == "x + 7 = 0"
    out = solve_question("Write the equation of the line "
                         "parallel to the y-axis and 7 units to "
                         "its left.")
    assert out["op"] == "w169_line_axis_parallel"


def test_line_perpendicular_joining():
    # AB direction (2, 2); line through (1, 2): x + y = 3
    q = ("Find the equation of the line through (1, 2) "
         "perpendicular to the line joining (3, 4) and (5, 6).")
    assert ans(q) == "x + y - 3 = 0"
    out = solve_question(q)
    assert out["op"] == "w169_line_perp_two_points"
    assert out["answer"] == "x + y - 3 = 0"


def test_line_perpendicular_two_points_router():
    # the primary served "y = 0x + 5" (the point's own
    # horizontal) before Wave 171's fragment repair
    out = solve_question("Find the equation of the line passing "
                         "through (-3, 5) and perpendicular to "
                         "the line through the points (2, 5) "
                         "and (-3, 6).")
    assert out["op"] == "w169_line_perp_two_points"
    assert out["answer"] == "5x - y + 20 = 0"


def test_line_perpendicular_with_x_intercept_no_and_having():
    assert ans("Find the equation of the line perpendicular to "
               "the line x - 7y + 5 = 0 with x-intercept 3.") \
        == "7x + y - 21 = 0"


def test_line_3d_bare_parallel_to_vector():
    a = ans("Find the vector equation of a line passing through "
            "(1, 2, 3) and parallel to 3i + 2j - 2k.")
    assert "λ(3i + 2j - 2k)" in a and "(x - 1)/3" in a


def test_prob_dist_table_stated_before_distribution_words():
    a = ans("X 0 1 2 3 P(X) 0.1 0.2 0.3 0.4 is the probability "
            "distribution of X. Find P(X >= 2).")
    assert a == "P(X >= 2) = 7/10"          # 0.3 + 0.4


def test_prob_dist_table_first_numeric_extra_declines():
    # a numeric token after the row makes the row ambiguous
    declines("X 0 1 2 3 P(X) 0.1 0.2 0.3 0.4 0.5 is the "
             "probability distribution of X. Find P(X >= 2).")


def test_commercial_pair_for_rupees():
    # (2500 - 2000) / 2000 = 25%
    assert ans("Ramesh bought a cycle for Rs 2000 and sold it "
               "for Rs 2500. Find his profit percent.") == "25%"


def test_commercial_pair_buys_sells_present_tense():
    assert ans("A shopkeeper buys a book for Rs 10 and sells "
               "it for Rs 11. Find the profit percentage.") == "10%"


def test_commercial_si_at_percent_principal():
    # 1000 x 5 x 2 / 100 = 100
    assert ans("Calculate the simple interest for a principal "
               "of Rs 1000 at 5% for 2 years.") == "Rs 100"


def test_commercial_compound_interest_declines():
    declines("Find the compound interest on Rs 1000 at 5% "
             "for 2 years.")


# ---------------------------------------------------------------------------
# Router gate: fragment repair never displaces a correct answer
# ---------------------------------------------------------------------------

def test_gate_si_correct_primary_stands():
    out = solve_question("Find the simple interest on Rs 500 "
                         "at 12% per annum for 3 years.")
    assert out["op"] == "simple_interest"
    assert "180" in str(out["answer"])


def test_gate_pair_percent_correct_primary_stands():
    out = solve_question("Ramesh bought a cycle for Rs 2000 "
                         "and sold it for Rs 2500. Find his "
                         "profit percent.")
    assert out["answer"] == "25%"
    assert not str(out.get("op", "")).startswith("w169")


def test_gate_genuine_evaluate_stands():
    out = solve_question("Find the value of 3/5 + 4/5")
    assert out["op"] == "evaluate"
    assert out["answer"] == "7/5"


def test_gate_w77_wrapper_still_serves():
    out = solve_question("oye 1/2 + 1/3 kitna hoga plz")
    assert out["answer"] == "5/6"
    assert not str(out.get("op", "")).startswith("w169")


def test_gate_sector_fragment_repaired_through_router():
    out = solve_question("What is the area of a sector whose "
                         "radius is 14 mm and whose arc is "
                         "50 mm?")
    assert out["op"] == "w169_sector_arc_area"
    assert out["answer"] == "350"
