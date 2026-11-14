"""Wave 42 (15 Nov 2026): probability leftovers from the
Wave-35 audit.

1. Exact-event coin phrasings (audit #227, top-15 #5).
   The Wave-31 enumeration required a quantifier word
   (at least / at most / exactly), so bare counted events
   — "getting two heads", "getting two tails", "three
   coins ... two heads" — fell to the legacy single-coin
   shortcut and answered 1/2. Also: "a coin is tossed
   three times" stated the repeat count as "<verb> <num>
   times", which the count detection missed, so n stayed
   1 and "exactly two heads" counted 0 favourable
   outcomes (answer: literally 0). Mixed events ("one
   head and two tails") are now bound when the counts
   add up to the number of coins.

2. Hindi balls in a bag. The audit's colour swap (#458:
   red asked, black's 3/5 returned) was already fixed by
   the final Wave-33 state — battery #458 and both
   लाल/नीली directions are regression-locked here. One
   form still failed: the colour-first count order
   "नीली गेंदें 3 हैं" (count AFTER गेंदें), which yielded
   no counts at all; the counting loop now reads it.
"""
import pytest

from api import _solve_friendly


def _prob(question, expected):
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    assert res.get("value") == pytest.approx(expected), (
        f"{question!r} -> {res.get('answer')!r}, "
        f"expected {expected}")


TWO = "Two coins are tossed simultaneously. What is the " \
      "probability of getting "


# --- Bare counted events (were all 1/2) ------------------------
def test_two_coins_two_heads_battery_227():
    _prob(TWO + "two heads?", 1 / 4)


def test_two_coins_two_tails():
    _prob(TWO + "two tails?", 1 / 4)


def test_coin_tossed_twice_two_heads():
    _prob("A coin is tossed twice. What is the "
          "probability of getting two heads?", 1 / 4)


def test_three_coins_two_heads():
    _prob("Three coins are tossed simultaneously. What "
          "is the probability of getting two heads?", 3 / 8)


def test_three_coins_one_tail():
    _prob("Three coins are tossed. What is the "
          "probability of getting one tail?", 3 / 8)


# --- Repeat count as "<verb> <num> times" (was 0) ---------------
def test_tossed_three_times_exactly_two_heads():
    _prob("A coin is tossed three times. What is the "
          "probability of getting exactly two heads?", 3 / 8)


def test_tossed_thrice_at_least_one_head():
    _prob("A coin is tossed thrice. What is the "
          "probability of getting at least one head?", 7 / 8)


# --- Mixed exact events -----------------------------------------
def test_one_head_and_two_tails():
    _prob("Three coins are tossed. What is the "
          "probability of getting one head and two "
          "tails?", 3 / 8)


def test_two_tails_and_one_head():
    _prob("Three coins are tossed. What is the "
          "probability of getting two tails and one "
          "head?", 3 / 8)


def test_a_head_and_a_tail_two_coins():
    _prob("Two coins are tossed. What is the "
          "probability of getting a head and a tail?",
          1 / 2)


# --- Controls: Wave-30/31/33 coin coverage unchanged ------------
def test_control_exactly_one_head():
    _prob(TWO.replace("simultaneously. ", "") +
          "exactly one head?", 1 / 2)


def test_control_exactly_two_heads_words():
    _prob(TWO.replace("simultaneously. ", "") +
          "exactly two heads?", 1 / 4)


def test_control_both_heads():
    _prob(TWO.replace("simultaneously. ", "") +
          "both heads?", 1 / 4)


def test_control_no_head():
    _prob(TWO.replace("simultaneously. ", "") +
          "no head?", 1 / 4)


def test_control_at_most_one_head():
    _prob(TWO.replace("simultaneously. ", "") +
          "at most one head?", 3 / 4)


def test_control_at_least_one_head():
    _prob(TWO.replace("simultaneously. ", "") +
          "at least one head?", 3 / 4)


def test_control_single_coin_head():
    _prob("A coin is tossed. What is the probability of "
          "getting a head?", 1 / 2)


def test_control_exactly_k_heads_in_n_tosses_digits():
    _prob("What is the probability of getting exactly "
          "2 heads in 3 tosses?", 3 / 8)


def test_control_empirical_probability():
    _prob("A coin is tossed 1000 times and head appears "
          "450 times. What is the probability of getting "
          "a head?", 0.45)


# --- Hindi balls: swap regression locks (audit #458) ------------
def test_hindi_balls_red_battery_458():
    _prob("एक थैले में 4 लाल और 6 काली गेंदें हैं। एक गेंद "
          "निकाली जाती है। लाल गेंद आने की प्रायिकता ज्ञात "
          "कीजिए।", 2 / 5)


def test_hindi_balls_blue_asked():
    _prob("एक थैले में 5 लाल और 3 नीली गेंदें हैं। एक गेंद "
          "निकाली जाती है। नीली गेंद आने की प्रायिकता ज्ञात "
          "कीजिए।", 3 / 8)


def test_hindi_balls_red_asked_same_bag():
    _prob("एक थैले में 5 लाल और 3 नीली गेंदें हैं। एक गेंद "
          "निकाली जाती है। लाल गेंद आने की प्रायिकता ज्ञात "
          "कीजिए।", 5 / 8)


def test_hindi_balls_three_colours():
    _prob("एक थैले में 3 लाल, 2 नीली और 5 हरी गेंदें हैं। "
          "हरी गेंद आने की प्रायिकता क्या है?", 1 / 2)


def test_hindi_balls_black_asked():
    _prob("एक थैले में 6 काली और 4 लाल गेंदें हैं। काली "
          "गेंद आने की प्रायिकता ज्ञात कीजिए।", 3 / 5)


def test_hindi_balls_rang_ki_form():
    _prob("एक थैले में 4 लाल रंग की और 6 काले रंग की "
          "गेंदें हैं। लाल गेंद आने की प्रायिकता ज्ञात "
          "कीजिए।", 2 / 5)


def test_roman_hindi_balls():
    _prob("Ek thaile mein 4 laal aur 6 kaali gendein "
          "hain. Laal gend aane ki sambhavna kya hai?",
          2 / 5)


# --- Hindi balls: colour-first count order (was fallback) -------
def test_hindi_balls_colour_first_count_order():
    _prob("एक थैले में नीली गेंदें 3 और लाल गेंदें 5 हैं। "
          "नीली गेंद आने की प्रायिकता ज्ञात कीजिए।", 3 / 8)


def test_hindi_balls_colour_first_other_colour_asked():
    _prob("एक थैले में नीली गेंदें 3 और लाल गेंदें 5 हैं। "
          "लाल गेंद आने की प्रायिकता ज्ञात कीजिए।", 5 / 8)
