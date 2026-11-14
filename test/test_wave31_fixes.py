"""Wave 31 (Suraj, 14 Nov 2026): a live spot-check after the
Wave 30 deploy caught this question returning 1/2 — it treats
two coins as ONE fair coin:

    "Two coins are tossed simultaneously. What is the
     probability of getting at most one head?"  ->  1/2  (WRONG)
    Correct: 3/4  (sample space HH, HT, TH, TT; at most one
    head = HT, TH, TT).

ROOT CAUSE (traced in solver/statistics.py::_probability):
the Wave 30 "coins tossed together" block enumerates the
sample space, but its event matcher only recognised "at
least / exactly ... heads / both / no head". For "at most
one head" no event matched, the block silently gave up, and
the LEGACY single-coin shortcut further down ("coin" and
"head" in the question -> 1/2) fired instead. Same hole for
"no tail", "at most ... tail" and "exactly ... tails", and
"a pair of coins" was not recognised as 2 coins at all.
A sibling hijack lived one pattern earlier: the
"exactly k heads in n tosses" shortcut has an OPTIONAL
"exactly", so "at least / at most k heads in n tosses" was
answered as exactly-k.

WHAT SHIPPED:
1. The enumeration block now matches the full standard event
   set for heads AND tails — at least / at most / exactly k,
   both, all, no head, no tail — with word or digit counts,
   and counts coins from "two coins", "a pair of coins",
   "in n tosses" and "tossed twice". Three-coin basics fall
   out of the same enumeration (n up to 5, as before).
2. The exactly-in-tosses shortcut no longer fires when the
   question says "at least" / "at most" before the count.
Solver-side only: no template/CSS/JS changed, so the ?v=29 /
ganitra-static-v6 delivery pins deliberately do NOT move.
Hindi/Hinglish coin asks have no patterns anywhere in the
solver (checked), so there is nothing to extend consistently
— out of scope for this wave.
"""
import pytest

from api import _solve_friendly
from solver.router import solve_question

FAILING = ("Two coins are tossed simultaneously. What is the "
           "probability of getting at most one head?")
TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")


def _exact(question):
    """The full user path must return the student's OWN answer:
    a real solver result, never a fallback layer."""
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


def _frac(question):
    res = solve_question(question)
    assert res.get("op") == "probability", res
    return str(res.get("answer", ""))


# --- 1. The live-verified failure, verbatim --------------------

def test_failing_question_returns_three_quarters():
    res = _exact(FAILING)
    assert str(res.get("answer", "")).startswith("3/4"), res


def test_failing_question_uses_the_four_outcome_sample_space():
    res = _exact(FAILING)
    steps = " ".join(res.get("steps") or [])
    assert "HH, HT, TH, TT" in steps, steps
    assert "at most one head" in steps, steps
    # The single-coin shortcut text must NOT be what answered.
    assert "A fair coin has 2 equally likely" not in steps, steps


# --- 2. Every standard two-coin event, exact -------------------

TWO_COIN = [
    ("at least one head", "3/4"),
    ("at most one head", "3/4"),
    ("exactly one head", "1/2"),
    ("exactly two heads", "1/4"),
    ("both heads", "1/4"),
    ("both tails", "1/4"),
    ("no head", "1/4"),
    ("no tail", "1/4"),
    ("at least one tail", "3/4"),
    ("at most one tail", "3/4"),
    ("exactly one tail", "1/2"),
    ("exactly two tails", "1/4"),
]


@pytest.mark.parametrize("event,want", TWO_COIN)
@pytest.mark.parametrize("frame", [
    "Two coins are tossed simultaneously. What is the "
    "probability of getting {event}?",
    "Two coins are tossed together. What is the "
    "probability of getting {event}?",
    "Two coins are thrown together. What is the "
    "probability of getting {event}?",
])
def test_two_coin_events(frame, event, want):
    ans = _frac(frame.format(event=event))
    assert ans.startswith(want), (frame, event, ans)


@pytest.mark.parametrize("event,want", [
    ("at least one head", "3/4"),
    ("at most one head", "3/4"),
    ("both tails", "1/4"),
    ("no tail", "1/4"),
])
def test_pair_of_coins_is_two_coins(event, want):
    q = (f"A pair of coins is tossed. What is the probability "
         f"of getting {event}?")
    assert _frac(q).startswith(want), q


def test_digit_counts():
    q = ("2 coins are tossed. What is the probability of "
         "getting at most 1 head?")
    assert _frac(q).startswith("3/4")


# --- 3. Three coins fall out of the same enumeration -----------

THREE_COIN = [
    ("at least one head", "7/8"),
    ("at most one head", "1/2"),
    ("at most two heads", "7/8"),
    ("at least two heads", "1/2"),
    ("exactly two heads", "3/8"),
    ("exactly one tail", "3/8"),
    ("all heads", "1/8"),
    ("no head", "1/8"),
    ("no tail", "1/8"),
]


@pytest.mark.parametrize("event,want", THREE_COIN)
def test_three_coin_events(event, want):
    q = (f"Three coins are tossed together. What is the "
         f"probability of getting {event}?")
    assert _frac(q).startswith(want), (q, _frac(q))


# --- 4. "in n tosses" quantifiers are no longer hijacked -------

IN_TOSSES = [
    ("exactly 2 heads in 3 tosses of a coin", "3/8"),  # unchanged
    ("2 heads in 3 tosses", "3/8"),                    # unchanged
    ("at least 2 heads in 3 tosses of a coin", "1/2"),
    ("at most 2 heads in 3 tosses of a coin", "7/8"),
    ("at most 1 head in 3 tosses of a coin", "1/2"),
    ("at least 1 head in 2 tosses of a coin", "3/4"),
    ("exactly 3 heads in 3 tosses", "1/8"),            # unchanged
]


@pytest.mark.parametrize("phrase,want", IN_TOSSES)
def test_in_tosses_quantifiers(phrase, want):
    q = f"What is the probability of getting {phrase}?"
    assert _frac(q).startswith(want), (q, _frac(q))


def test_coin_tossed_twice():
    q = ("A coin is tossed twice. What is the probability of "
         "getting at most one head?")
    assert _frac(q).startswith("3/4")


# --- 5. Previously-passing siblings stay exact -----------------

SIBLINGS = [
    ("A coin is tossed. What is the probability of getting "
     "a head?", "1/2"),
    ("A coin is tossed once. What is the probability of "
     "getting a tail?", "1/2"),
    ("A coin is tossed once. What is the probability of "
     "getting at least one head?", "1/2"),
    ("What is the probability of getting a 4 on a die?", "1/6"),
    ("What is the probability of getting a sum of 7 with "
     "two dice?", "1/6"),
    ("What is the probability of drawing a king from a pack "
     "of 52 cards?", "1/13"),
    ("A bag contains 5 red and 3 blue balls. A ball is drawn "
     "at random. What is the probability that it is a red "
     "ball?", "5/8"),
]


@pytest.mark.parametrize("question,want", SIBLINGS)
def test_probability_siblings_unchanged(question, want):
    assert _frac(question).startswith(want), question


def test_wave30_sibling_at_least_one_head_still_exact():
    res = _exact("Two coins are tossed together. What is the "
                 "probability of getting at least one head?")
    assert str(res.get("answer", "")).startswith("3/4"), res


def test_wave30_train_question_still_exact():
    res = _exact(TRAIN_HINDI)
    assert res.get("answer") == "40 km/h", res
