"""Wave 33 (14 Nov 2026): three named gaps from the Wave 32
left-out list plus a 68-question probe battery (EN/HI,
Class 9-12 NCERT style) that found 28 wrong answers and 27
fallbacks on the pre-wave tree. After the wave the battery
is 68/68 exact.

1. HINDI / HINGLISH PROBABILITY (priority 1). solver/
   statistics.py had NO Hindi patterns at all: every
   Devanagari probability question routed onward to the
   arithmetic simplifier and came back as letter-soup, and
   Hinglish asks fell to the guide fallback. New
   _probability_hindi handles coins (at-most / at-least /
   exactly / both / none, Devanagari + Roman), dice
   (even/odd/prime/composite/square/greater/less/multiple,
   single + two-dice sums + doublet), cards (ranks, suits,
   face cards, red/black) and balls in a bag, routing to
   the same enumeration the English path uses. Router
   statistics tokens + the _probability gate were widened
   (प्रायिकता/संभावना/sambhavna, experiment tokens,
   "chance"). A stem-collision found while building: काल
   (black) occurs inside निकाली ("drawn") — stems now
   carry a Devanagari word-boundary lookbehind.
2. LP FROM RAW INEQUALITIES (priority 2). applied.py
   _lp_inequalities: objective + constraint set -> boundary
   intersections -> feasible corners -> exact rational
   optima (NCERT's 235/19 at (20/19, 45/19) included), with
   an honest "unbounded" answer when the region runs away.
   A router pre-check gate routes these to applied (they
   used to die in algebra's expression parser).
3. OGIVE MEDIAN (priority 3). statistics._ogive_median
   reads "less than B: cf" / "more than B: cf" pairs,
   rebuilds classes + frequencies and applies the grouped
   median formula (previously the raw-list median of the
   bounds answered 22.5 / 18.5 for data whose true median
   is 21.6667). Router ogive gate protects "Draw an
   ogive..." from the plot intent.

Probe extras fixed in the same wave: English single-die
EVENTS (even/prime/greater-than/less-than — the legacy
shortcut answered "greater than 4" as 1/6), empirical
probability from stated outcomes, defective-items, 53-
weekday years, "not a red ball" complement, specific
cards (king of hearts 1/52, black queen 1/26 — both were
hijacked to 1/13), mean-excluded form, frequency-table
mean with unknown f, nth term from S_n, collinear find-k,
concentric-ring area, rectangle diagonal word form,
"Solve the quadratic equation ..." / "... by completing
the square" lead-in stripping, sin theta -> tan theta.

Solver-only wave: no template/CSS/JS changed, so the
?v=29 / ganitra-static-v6 pins deliberately do NOT move.
Untouched by design: the pi convention (owner's call),
proof/verify questions, anything needing an LLM.
"""
from api import _solve_friendly
from solver.router import solve_question

TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")


def _exact(question):
    """The full user path must return the student's OWN
    answer: a real solver result, never a fallback layer."""
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


def _ans(question):
    return str(_exact(question).get("answer", ""))


# --- 1. Hindi probability (verbatim Class 10 forms) -----------

def test_hindi_two_coins_at_least_one_head():
    assert _ans("दो सिक्के एक साथ उछाले जाते हैं। कम से कम एक "
                "चित आने की प्रायिकता ज्ञात कीजिए।"
                ).startswith("3/4")


def test_hindi_two_coins_at_most_one_head():
    assert _ans("दो सिक्के उछाले जाते हैं। अधिक से अधिक एक चित "
                "आने की प्रायिकता क्या है?").startswith("3/4")


def test_hindi_three_coins_exactly_two_heads():
    assert _ans("तीन सिक्के एक साथ उछाले जाते हैं। ठीक दो चित "
                "आने की प्रायिकता ज्ञात कीजिए।"
                ).startswith("3/8")


def test_hindi_coin_head_and_tail():
    assert _ans("एक सिक्का उछाला जाता है। चित आने की प्रायिकता "
                "क्या है?").startswith("1/2")
    assert _ans("एक सिक्का उछाला जाता है। पट आने की प्रायिकता "
                "ज्ञात कीजिए।").startswith("1/2")


def test_hindi_coins_no_head_and_both_tails():
    assert _ans("दो सिक्के उछाले जाते हैं। कोई चित न आने की "
                "प्रायिकता ज्ञात कीजिए।").startswith("1/4")
    assert _ans("दो सिक्के उछाले जाते हैं। दोनों पट आने की "
                "प्रायिकता क्या है?").startswith("1/4")


def test_hindi_die_events():
    assert _ans("एक पासा फेंका जाता है। एक सम संख्या आने की "
                "प्रायिकता ज्ञात कीजिए।").startswith("1/2")
    assert _ans("एक पासा फेंका जाता है। एक अभाज्य संख्या आने "
                "की प्रायिकता क्या है?").startswith("1/2")
    assert _ans("एक पासा फेंका जाता है। संख्या 5 आने की "
                "प्रायिकता ज्ञात कीजिए।").startswith("1/6")
    assert _ans("एक पासा फेंका जाता है। 4 से बड़ी संख्या आने "
                "की प्रायिकता क्या है?").startswith("1/3")


def test_hindi_two_dice_sum():
    assert _ans("दो पासे एक साथ फेंके जाते हैं। अंकों का योग 7 "
                "आने की प्रायिकता ज्ञात कीजिए।"
                ).startswith("1/6")


def test_hindi_cards():
    assert _ans("52 पत्तों की एक गड्डी में से एक पत्ता निकाला "
                "जाता है। इक्का आने की प्रायिकता ज्ञात कीजिए।"
                ).startswith("1/13")
    assert _ans("ताश के 52 पत्तों में से एक पत्ता निकाला जाता "
                "है। बादशाह आने की प्रायिकता क्या है?"
                ).startswith("1/13")
    assert _ans("52 पत्तों की गड्डी से एक पत्ता निकाला जाता "
                "है। लाल पत्ता आने की प्रायिकता ज्ञात कीजिए।"
                ).startswith("1/2")
    assert _ans("52 पत्तों की गड्डी से एक पत्ता निकाला जाता "
                "है। हुकुम का पत्ता आने की प्रायिकता क्या है?"
                ).startswith("1/4")


def test_hindi_balls_two_and_three_colours():
    assert _ans("एक थैले में 5 लाल और 3 नीली गेंदें हैं। एक "
                "गेंद यादृच्छिक रूप से निकाली जाती है। "
                "प्रायिकता ज्ञात कीजिए कि गेंद लाल है।"
                ).startswith("5/8")
    assert _ans("एक थैले में 4 लाल, 5 हरी और 6 सफेद गेंदें "
                "हैं। एक गेंद निकाली जाती है। हरी गेंद आने "
                "की प्रायिकता क्या है?").startswith("1/3")


def test_hinglish_probability():
    assert _ans("Do sikke ek saath uchhale jate hain. Kam se "
                "kam ek chit aane ki probability kya hai?"
                ).startswith("3/4")
    assert _ans("Ek sikka uchhala jata hai. Pat aane ki "
                "probability kya hai?").startswith("1/2")
    assert _ans("Ek pasa phenka jata hai. Sam sankhya aane ki "
                "probability batao.").startswith("1/2")
    assert _ans("Ek pasa phenka jata hai. Visham sankhya aane "
                "ki sambhavna kya hai?").startswith("1/2")


# --- 2. LP from raw inequalities -------------------------------

def test_lp_maximise_simple():
    res = _exact("Maximise Z = 3x + 4y subject to x + y ≤ 4, "
                 "x ≥ 0, y ≥ 0.")
    assert res["answer"] == "Maximum Z = 16 at (0, 4)", res


def test_lp_maximise_ncert_fraction():
    res = _exact("Maximise Z = 5x + 3y subject to 3x + 5y ≤ "
                 "15, 5x + 2y ≤ 10, x ≥ 0, y ≥ 0.")
    assert res["answer"] == ("Maximum Z = 235/19 at "
                             "(20/19, 45/19)"), res


def test_lp_minimise_ncert():
    res = _exact("Minimise Z = 3x + 5y subject to x + 3y ≥ 3, "
                 "x + y ≥ 2, x ≥ 0, y ≥ 0.")
    assert res["answer"] == "Minimum Z = 7 at (3/2, 1/2)", res


def test_lp_maximise_two_constraints():
    res = _exact("Maximise Z = x + 2y subject to 2x + y ≤ 4, "
                 "x + y ≤ 3, x, y ≥ 0.")
    assert res["answer"] == "Maximum Z = 6 at (0, 3)", res


# --- 3. Ogive median --------------------------------------------

def test_ogive_less_than_median():
    a = _ans("The following distribution gives the daily "
             "income of 50 workers. Convert it into a less "
             "than type cumulative frequency distribution "
             "and find the median from the ogive: less than "
             "10: 5, less than 20: 13, less than 30: 25, "
             "less than 40: 30.")
    assert a == "21.6667", a


def test_ogive_more_than_median():
    a = _ans("From the more than ogive of the data, find "
             "the median: more than 0: 30, more than 10: "
             "25, more than 20: 17, more than 30: 5.")
    assert a == "21.6667", a


# --- 4. Probe extras ---------------------------------------------

def test_english_die_events_not_hijacked():
    assert _ans("A die is thrown once. Find the probability "
                "of getting an even number.").startswith("1/2")
    assert _ans("A die is thrown once. Find the probability "
                "of getting a prime number.").startswith("1/2")
    assert _ans("A die is thrown once. Find the probability "
                "of getting a number greater than 4."
                ).startswith("1/3")
    assert _ans("A die is thrown once. Find the probability "
                "of getting a number less than 3."
                ).startswith("1/3")
    assert _ans("Two dice are thrown together. Find the "
                "probability of getting a doublet."
                ).startswith("1/6")


def test_empirical_probability():
    assert _ans("A coin is tossed 1000 times. Head appears "
                "450 times. Find the probability of getting "
                "a head.").startswith("9/20")
    assert _ans("A die is thrown 100 times and the outcome "
                "6 appears 20 times. Find the probability of "
                "getting a 6.").startswith("1/5")


def test_defective_and_leap_year():
    assert _ans("A lot of 20 bulbs contains 4 defective "
                "ones. One bulb is drawn at random. What is "
                "the probability that it is not defective?"
                ).startswith("4/5")
    assert _ans("Find the probability that a leap year has "
                "53 Sundays.").startswith("2/7")
    assert _ans("Find the probability that a non-leap year "
                "has 53 Mondays.").startswith("1/7")


def test_not_red_ball_complement():
    assert _ans("A bag contains 5 red balls and 3 black "
                "balls. A ball is drawn at random. What is "
                "the probability that the ball drawn is not "
                "a red ball?").startswith("3/8")


def test_specific_cards_not_hijacked():
    assert _ans("One card is drawn from a well-shuffled "
                "deck of 52 cards. Find the probability of "
                "getting a king of hearts.").startswith("1/52")
    assert _ans("A card is drawn from a pack of 52 cards. "
                "Find the probability of getting a black "
                "queen.").startswith("1/26")
    assert _ans("One card is drawn from a deck of 52 cards. "
                "Find the probability of getting a face card."
                ).startswith("3/13")


def test_mean_excluded_and_freq_unknown():
    assert _ans("The mean of 6 numbers is 15. If one number "
                "is excluded, the mean of the remaining "
                "numbers is 14. Find the excluded number."
                ) == "20"
    assert _ans("If the mean of the following data is 30, "
                "find the value of p: x: 10, 20, 30, 40, 50 "
                "and f: 3, 5, 4, p, 3.") == "p = 5"


def test_nth_term_from_sum():
    a = _ans("The sum of the first n terms of an AP is "
             "3n^2 + 5n. Find the nth term of the AP.")
    assert "n + 2" in a, a


def test_collinear_find_k():
    assert _ans("Find the value of k for which the points "
                "(2, 3), (4, k) and (6, -3) are collinear."
                ) == "k = 0"


def test_ring_area_and_rectangle_diagonal():
    assert _ans("Find the area between two concentric "
                "circles of radii 7 cm and 14 cm."
                ).startswith("461.81")
    a = _ans("A rectangular park is to be designed whose "
             "breadth is 3 m less than its length. Its "
             "diagonal is 60 m more than the shorter side "
             "and the longer side is 30 m more than the "
             "shorter side. Find the sides of the park.")
    # probe form: diagonal +60, longer +30 over shorter
    assert "90" in a and "120" in a, a


def test_equation_lead_ins_and_methods():
    a = _ans("Solve the quadratic equation 2x^2 - 7x + 3 = 0.")
    assert "3" in a and "1/2" in a, a
    a = _ans("Solve 2x^2 - 7x + 3 = 0 by completing the "
             "square.")
    assert "3" in a and "1/2" in a, a
    a = _ans("Find the roots of 1/(x+4) - 1/(x-7) = 11/30, "
             "x not equal to -4 and 7.")
    assert "x = 1" in a and "x = 2" in a, a


def test_sin_theta_tan_theta():
    assert _ans("If sin theta = 3/5, find the value of tan "
                "theta.") == "tan θ = 3/4"


def test_hindi_descriptive_statistics():
    assert _ans("संख्याओं 5, 7, 9, 11, 13 का माध्य ज्ञात "
                "कीजिए।") == "9"
    assert _ans("3, 5, 7, 2, 8 का माध्यक ज्ञात कीजिए।") == "5"
    assert _ans("2, 4, 4, 6, 4 का बहुलक ज्ञात कीजिए।") == "4"
    assert _ans("4, 8, 15, 16, 23, 42 का औसत ज्ञात कीजिए।"
                ) == "18"


# --- 5. Regression guards ----------------------------------------

def test_guard_wave30_hindi_train():
    assert _ans(TRAIN_HINDI) == "40 km/h"


def test_guard_wave31_two_coins():
    assert _ans("Two coins are tossed simultaneously. What "
                "is the probability of getting at most one "
                "head?").startswith("3/4")


def test_guard_wave32_topics():
    assert _ans("Find the median of the data with class "
                "intervals 0-10, 10-20, 20-30, 30-40 and "
                "frequencies 5, 8, 12, 5.") == "21.6667"
    res = solve_question("Find the maximum value of Z = 5x "
                         "+ 4y at the corner points (0, 0), "
                         "(0, 4), (3, 4) and (5, 0).")
    assert str(res.get("answer", "")).startswith(
        "Maximum Z = 31"), res
    assert _ans("Bag A contains 3 red balls and 2 black "
                "balls. Bag B contains 2 red balls and 3 "
                "black balls. A bag is chosen at random and "
                "a ball is drawn from it, which is found to "
                "be red. Find the probability that the ball "
                "was drawn from bag A.").startswith("3/5")
