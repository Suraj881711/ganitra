#!/usr/bin/env python3
"""Wave 30 (Suraj, 14 Nov 2026): "jo question diya uska ans
nhi mil raha hai, uss question ka similar de raha hai — ussi
question ko solve kyu nhi kar raha hai."

Suraj's exact question (Class 10 train sum, Hindi) is the
headline case. Diagnosis, reproduced before any fix:

1. CRASH: his sentence contains commas; SymPy parses comma
   text into a TUPLE and solver/arithmetic.py called
   .free_symbols on it -> op=error, "Could not solve this
   one: 'tuple' object has no attribute 'free_symbols'".
2. MASKING: the Wave-18 fallback layer covered the crash
   with a labelled similar example — the thing Suraj saw.
3. MISSING PATTERN: the English twin returned "No
   word-problem pattern matched" — the speed-time quadratic
   D/x - D/(x+k) = t was not implemented at all.
(The answer cache was ruled out: it keys on the exact
question text, numbers included, and never caches fallback
or error results.)

Fixes verified below: the parser rejects tuples with a
readable ValueError; the train pattern (Hindi + English,
faster/slower) solves the student's own numbers; a
50-question Classes 6-12 battery went from 15 exact answers
to 50 (see ~/workspace/ganitra-wave30-diagnosis.md); the
router gives failed intent results one pass through the
strict applied patterns before any similar example may be
offered. Solver-side only — templates/CSS/JS untouched, so
the ?v=29 / ganitra-static-v6 pins deliberately stay put,
and this script asserts they did NOT move.
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
from solver.expression_parser import parse_expression  # noqa: E402
from solver.router import solve_question  # noqa: E402

TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
TRAIN_ENGLISH = (
    "A train travels a distance of 360 km at a uniform speed. "
    "If the speed had been 5 km/h more, it would have taken "
    "1 hour less for the same journey. Find the speed of the "
    "train.")

# --- 1. The crash class is dead --------------------------------
try:
    parse_expression("ek sawal, do hisso mein, 360 km")
    _tuple_ok = False
except ValueError:
    _tuple_ok = True
except Exception:
    _tuple_ok = False
check("comma text raises a readable ValueError, never a tuple",
      _tuple_ok)
_r = solve_question(TRAIN_HINDI)
check("Hindi train question: no error op, no crash text",
      _r.get("op") != "error"
      and "tuple" not in str(_r.get("answer", ""))
      and "Could not solve" not in str(_r.get("answer", "")),
      f"op={_r.get('op')} ans={_r.get('answer')}")

# --- 2. Suraj's exact question, exact answer --------------------
for _name, _q in (("Hindi (his exact words)", TRAIN_HINDI),
                  ("English twin", TRAIN_ENGLISH)):
    _r = _solve_friendly(_q)
    check(f"train question [{_name}]: exact 40 km/h, "
          f"not a fallback",
          _r.get("answer") == "40 km/h"
          and "fallback" not in _r,
          f"ans={_r.get('answer')} kind={_r.get('fallback_kind')}")
    check(f"train question [{_name}]: op is the quadratic "
          f"word-problem solver",
          _r.get("op") == "speed_time_quadratic",
          f"op={_r.get('op')}")
_steps = " ".join(_solve_friendly(TRAIN_HINDI).get("steps") or [])
check("train steps show his own equation 360/x - 360/(x+5) = 1",
      "360/x - 360/(x + 5) = 1" in _steps)
check("train steps show the quadratic x^2 + 5x - 1800 = 0",
      "1800" in _steps and "x^2" in _steps)
_r = _solve_friendly(
    "A train travels a distance of 360 km at a uniform speed. "
    "If the speed had been 5 km/h less, it would have taken "
    "1 hour more for the same journey. Find the speed of the "
    "train.")
check("slower variant: exact 45 km/h",
      _r.get("answer") == "45 km/h" and "fallback" not in _r,
      f"ans={_r.get('answer')}")

# --- 3. Battery spot-checks: exact answers, no fallback ---------
BATTERY = [
    ("A shopkeeper gives a discount of 10% on a shirt marked "
     "Rs 800. What is the selling price?", "720"),
    ("Rahul scored 45 marks out of 60. What percentage did "
     "he score?", "75%"),
    ("The ratio of boys to girls in a class is 3:2. If there "
     "are 30 students in the class, how many girls are "
     "there?", "12"),
    ("Find the compound interest on Rs 10000 at 10% per "
     "annum for 2 years.", "2100"),
    ("The sum of two numbers is 50 and their difference is "
     "10. Find the numbers.", "30 and 20"),
    ("A father is 3 times as old as his son. After 10 years, "
     "the father will be twice as old as his son. Find "
     "their present ages.", "30"),
    ("The product of two consecutive integers is 56. Find "
     "the integers.", "7 and 8"),
    ("Which term of the AP 5, 10, 15, 20, ... is 50?",
     "10th"),
    ("If sin A = 3/5, find cos A.", "cos A = 4/5"),
    ("A ladder 10 m long leans against a wall making an "
     "angle of 60 degrees with the ground. How high up the "
     "wall does the ladder reach?", "8.66"),
    ("Find the coordinates of the point which divides the "
     "line segment joining (2, 3) and (8, 9) in the ratio "
     "1:2 internally.", "(4, 5)"),
    ("Two coins are tossed together. What is the "
     "probability of getting at least one head?", "3/4"),
    ("Find the HCF and LCM of 12 and 18.", "LCM = 36"),
    ("Find the zeroes of the polynomial x^2 - 3x - 10.",
     "x = -2, x = 5"),
    ("Divide x^3 + 3x^2 + 3x + 1 by x + 1.", "x^2 + 2·x + 1"),
    ("The mean of 5 numbers is 20. Four of the numbers are "
     "18, 22, 19 and 21. Find the fifth number.", "20"),
    ("Do sankhyaon ka jod 40 hai aur unka antar 8 hai. "
     "Sankhyayen batao.", "24 and 16"),
]
for _q, _want in BATTERY:
    _r = _solve_friendly(_q)
    check(f"exact: {_q[:44]!r}...",
          "fallback" not in _r
          and _want in str(_r.get("answer", "")),
          f"ans={_r.get('answer')} kind={_r.get('fallback_kind')}")

# --- 4. Honesty: unparseable input still gets the LABEL ---------
_r = _solve_friendly(
    "ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 "
    "rupaye ki kharidi kitne bache")
check("genuinely unparseable: similar example, still labelled",
      _r.get("fallback_kind") == "similar"
      and str(_r.get("answer", "")).startswith("Similar example"))

# --- 5. Delivery hygiene: solver-only wave, pins unmoved --------
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
