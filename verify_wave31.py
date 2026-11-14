#!/usr/bin/env python3
"""Wave 31 (Suraj, 14 Nov 2026): live spot-check after the
Wave 30 deploy found a probability bug the local battery had
claimed fixed:

    "Two coins are tossed simultaneously. What is the
     probability of getting at most one head?"
        LIVE (wrong): 1/2, steps about a SINGLE fair coin.
        Correct: 3/4 (HH, HT, TH, TT; at most one head
        = HT, TH, TT).

ROOT CAUSE (traced in solver/statistics.py::_probability,
reproduced locally through solve_question before fixing):
the Wave 30 "coins tossed together" enumeration block knew
only "at least / exactly ... heads / both / no head". For
"at most one head" no event matched, the block gave up, and
the legacy single-coin shortcut below it ("coin" + "head"
-> 1/2) fired. The "tossed together / at least one head"
sibling passed because that one phrase WAS in the matcher.
Also missing: "no tail", "at most ... tail(s)",
"exactly ... tail(s)", and "a pair of coins" (= 2 coins).
Sibling hijack: the "exactly k heads in n tosses" shortcut
has an OPTIONAL "exactly", so "at least / at most k heads
in n tosses" was answered as exactly-k.

FIX (solver-side only, statistics.py): the enumeration
block now matches the full standard event set for heads
and tails — at least / at most / exactly k, both, all,
no head, no tail — counts coins from "N coins", "a pair of
coins", "in n tosses" and "tossed twice"; three-coin
basics come from the same enumeration. The exactly-in-
tosses shortcut yields to "at least / at most". No
template/CSS/JS changed, so the ?v=29 / ganitra-static-v6
pins deliberately stay put, and this script asserts they
did NOT move. Hindi/Hinglish coin asks have no patterns
anywhere in the solver — nothing to extend; out of scope.
"""
import hashlib
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


from api import _solve_friendly  # noqa: E402
from solver.router import solve_question  # noqa: E402

FAILING = ("Two coins are tossed simultaneously. What is the "
           "probability of getting at most one head?")
TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")


def _ans(q):
    return str(solve_question(q).get("answer", ""))


# --- 1. The live-verified failure, verbatim ---------------------
_r = _solve_friendly(FAILING)
check("failing question: exact 3/4 via the user path, "
      "not a fallback",
      str(_r.get("answer", "")).startswith("3/4")
      and "fallback" not in _r,
      f"ans={_r.get('answer')} kind={_r.get('fallback_kind')}")
_steps = " ".join(_r.get("steps") or [])
check("failing question: steps enumerate HH, HT, TH, TT",
      "HH, HT, TH, TT" in _steps, _steps[:120])
check("failing question: favourable label is 'at most one head'",
      "at most one head" in _steps, _steps[:120])
check("failing question: single-coin shortcut did NOT answer",
      "A fair coin has 2 equally likely" not in _steps)

# --- 2. Every standard two-coin event ---------------------------
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
for _event, _want in TWO_COIN:
    _q = (f"Two coins are tossed simultaneously. What is the "
          f"probability of getting {_event}?")
    check(f"two coins [{_event}] = {_want}",
          _ans(_q).startswith(_want), _ans(_q))

# --- 3. The other common wordings --------------------------------
WORDINGS = [
    ("Two coins are thrown together. What is the probability "
     "of getting at most one head?", "3/4"),
    ("A pair of coins is tossed. What is the probability of "
     "getting at least one head?", "3/4"),
    ("A pair of coins is tossed. What is the probability of "
     "getting at most one head?", "3/4"),
    ("A pair of coins is tossed simultaneously. What is the "
     "probability of getting both tails?", "1/4"),
    ("2 coins are tossed. What is the probability of getting "
     "at most 1 head?", "3/4"),
    ("A coin is tossed twice. What is the probability of "
     "getting at most one head?", "3/4"),
]
for _q, _want in WORDINGS:
    check(f"wording: {_q[:52]!r}... = {_want}",
          _ans(_q).startswith(_want), _ans(_q))

# --- 4. Three-coin basics (same enumeration) ---------------------
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
for _event, _want in THREE_COIN:
    _q = (f"Three coins are tossed together. What is the "
          f"probability of getting {_event}?")
    check(f"three coins [{_event}] = {_want}",
          _ans(_q).startswith(_want), _ans(_q))

# --- 5. "in n tosses" quantifiers --------------------------------
IN_TOSSES = [
    ("exactly 2 heads in 3 tosses of a coin", "3/8"),
    ("2 heads in 3 tosses", "3/8"),
    ("at least 2 heads in 3 tosses of a coin", "1/2"),
    ("at most 2 heads in 3 tosses of a coin", "7/8"),
    ("at most 1 head in 3 tosses of a coin", "1/2"),
    ("at least 1 head in 2 tosses of a coin", "3/4"),
    ("exactly 3 heads in 3 tosses", "1/8"),
]
for _phrase, _want in IN_TOSSES:
    _q = f"What is the probability of getting {_phrase}?"
    check(f"in-tosses [{_phrase}] = {_want}",
          _ans(_q).startswith(_want), _ans(_q))

# --- 6. Previously-passing siblings stay exact -------------------
SIBLINGS = [
    ("A coin is tossed. What is the probability of getting "
     "a head?", "1/2"),
    ("A coin is tossed once. What is the probability of "
     "getting a tail?", "1/2"),
    ("What is the probability of getting a 4 on a die?", "1/6"),
    ("What is the probability of getting a sum of 7 with "
     "two dice?", "1/6"),
    ("What is the probability of drawing a king from a pack "
     "of 52 cards?", "1/13"),
    ("A bag contains 5 red and 3 blue balls. A ball is drawn "
     "at random. What is the probability that it is a red "
     "ball?", "5/8"),
    ("Two coins are tossed together. What is the "
     "probability of getting at least one head?", "3/4"),
]
for _q, _want in SIBLINGS:
    check(f"sibling: {_q[:52]!r}... = {_want}",
          _ans(_q).startswith(_want), _ans(_q))
_r = _solve_friendly(TRAIN_HINDI)
check("Wave 30 headline (Hindi train) still exact 40 km/h",
      _r.get("answer") == "40 km/h" and "fallback" not in _r,
      f"ans={_r.get('answer')}")

# --- 7. Delivery hygiene: solver-only wave, pins unmoved ---------
with open("templates/base.html", encoding="utf-8") as fh:
    BASE = fh.read()
with open("static/sw.js", encoding="utf-8") as fh:
    SW = fh.read()
check("stylesheet pin deliberately unchanged (?v=29)",
      "style.css?v=29" in BASE or "v='29'" in BASE)
check("service worker cache deliberately unchanged (v6)",
      'GANITRA_CACHE = "ganitra-static-v6"' in SW)
for _name, _want in (
        ("logo-full-t.png", "f18c8e42"),
        ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"),
        ("logo-mark.png", "03bc03dc")):
    _digest = hashlib.sha256(
        open(os.path.join("static", _name), "rb").read()
    ).hexdigest()
    check(f"frozen logo {_name} untouched",
          _digest.startswith(_want), _digest[:12])

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
