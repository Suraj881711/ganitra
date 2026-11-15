"""Wave 47 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (all solver-side; solver coverage
round 3 — the Wave 38 left-open list, Wave 35 audit
#6, #10-#14, plus battery #123):

1. Statistics word problems (audit #6) —
   solver/statistics.py: wrongly-recorded mean (correct
   total = n*mean - wrong + right, #218), included-
   person weight (teacher = (n+1)*new - n*old, #225),
   and the generic list path no longer feeds the stated
   count ("of 15 students") or a colon-introduced list's
   lead-in into the data (#223 median).
2. Combined solids (audit #10) — solver/geometry.py:
   cylinder+cone reads the cone's height stated after
   the cone's name (#206); new hemisphere-combination
   volume patterns (cylinder+hemisphere,
   cone+hemisphere, diameter-stated).
3. Train/work hijacks (audit #11) — solver/applied.py:
   train-length-from-platform-crossing (#263) and
   together+solo work time (#259).
4. Factor counts (audit #12) — solver/number_theory.py
   + a narrow router pre-check: tau(n) from the prime
   factorisation (#314-#317).
5. Trigonometry (audit #13/#14) —
   solver/trigonometry.py: inverse-angle asks return
   the angle (#160, #163) while value-of-ratio asks keep
   returning ratios; sums of two asked ratios (#443);
   the identity verifier strips the filler "that" and
   the trailing full stop that made sec^2 into sec^2.0
   (#161); three-term arctan chains fold pairwise with
   the pi correction (#180).
6. GP sum+product (battery #123) — solver/sequences.py:
   a/r, a, ar -> a^3 = P, r + 1/r = S/a - 1.
7. Calculus (audit #14 + #268) — solver/calculus.py +
   router intents: "Find the derivative of ..." lead-in
   and trailing-dot hygiene (#268, #270, #274); bare e
   is Euler's number in e^... (#269); textbook trig
   derivative forms sec^2 / -csc^2 (#379); "dy/dx if
   y = ..." runs before the ODE block (#272); limits in
   words (#273, #275, #276); rate of change, named and
   general (#383); tangent/normal slope and equation
   (#286); maximum/minimum value of f(x) (#285).

Measured TWICE. Built on a Waves 1-38 copy: pytest
412 -> 440 passed (28 new tests in
test/test_wave47_fixes.py); the 515-question Wave 35
battery (same automated adjudication both runs) EXACT
301 -> 329, FALLBACK 168 -> 156, WRONG 46 -> 30,
ERROR 0 -> 0, ZERO per-item regressions. The Waves
39-46 merge then landed in the original tree mid-task,
so the wave was REBASED onto the merged tree: battery
308 -> 335 EXACT, 163 -> 151 FALLBACK, 44 -> 29
WRONG, 0 ERROR, again ZERO regressions (27 flips;
#161 was already fixed by Wave 42's own "that" strip —
Wave 47 adds only the trailing-dot strip there, which
the sec^2 identity still needed).

No template/CSS/JS changed by this wave: the merged
tree's ?v=30 / ganitra-static-v7 pins deliberately
stayed put in the wave itself. (Merge-2 later reconciled
the pins to ?v=31 / ganitra-static-v8 for Wave 49's CSS;
the hygiene checks below assert the CURRENT pins.) The
frozen logo files are untouched.

Deliberately NOT taken: audit #15 salvage quality /
fraction-addition promotion, audit #1 Hindi letter-
soup leftovers, the echo cases #32/#349/#437, the pi
convention (owner's undecided call), multi-letter
angle names ("theta") inside identity asks, sqrt-form
ratio values ("cos theta = sqrt(3)/2, find theta"),
circle/parabola tangent equations and the ODE
"solve the differential equation dy/dx = ..." parse
failure (all pre-existing, unchanged by this wave).
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


from solver.router import solve_question  # noqa: E402


def _op(q):
    return str(solve_question(q).get("op", ""))


def _ans(q):
    return str(solve_question(q).get("answer", ""))


print("== 1. statistics word problems ==")
check("wrongly recorded mean #218", _ans(
    "The mean of 10 observations is 25. If one "
    "observation 36 was wrongly recorded as 63, find "
    "the correct mean.") == "22.3")
check("included teacher #225", _ans(
    "The mean weight of 8 students is 50 kg. When the "
    "teacher's weight is included, the mean becomes "
    "52 kg. Find the teacher's weight.") == "68 kg")
check("median stated-count #223", _ans(
    "The marks of 15 students are: 41, 39, 48, 52, 46, "
    "62, 54, 40, 96, 52, 98, 40, 42, 52, 60. Find the "
    "median.") == "52")
check("plain mean unchanged",
      _ans("Find the mean of 2, 4, 6, 8, 10.") == "6")

print("== 2. combined solids ==")
check("cyl+cone own heights #206", "351.858" in _ans(
    "A solid consists of a cylinder of radius 4 cm and "
    "height 6 cm with a cone of the same radius and "
    "height 3 cm on top. Find the total volume."))
check("cyl+hemisphere", "254.469" in _ans(
    "A solid consists of a cylinder of radius 3 cm and "
    "height 7 cm with a hemisphere of the same radius "
    "on top. Find the total volume."))
check("cone+hemisphere", "94.2478" in _ans(
    "A solid consists of a cone of radius 3 cm and "
    "height 4 cm with a hemisphere of the same radius "
    "on top. Find the total volume."))
check("plain hemisphere unchanged", "718.378" in _ans(
    "Find the volume of a hemisphere of radius 7 cm."))

print("== 3. train / work ==")
check("train length #263", _ans(
    "A train crosses a platform 180 m long in 15 "
    "seconds travelling at 60 km/h. Find the length "
    "of the train.") == "70 m")
check("work together+solo #259", _ans(
    "A and B together can do a work in 8 days. A alone "
    "can do it in 12 days. In how many days can B "
    "alone do it?") == "24 days")
check("train speed neighbour #262", _ans(
    "A train 240 m long crosses a pole in 12 seconds. "
    "Find the speed of the train in km/h.") == "72 km/h")

print("== 4. factor counts ==")
for _n, _want in ((36, "9"), (48, "10"), (27, "4"),
                  (100, "9"), (720, "30")):
    check(f"factors of {_n}",
          _ans(f"How many factors does {_n} have?")
          == _want)
check("HCF unchanged",
      _ans("Find the HCF of 12 and 18.") == "6")

print("== 5. trigonometry ==")
check("inverse angle #160", _ans(
    "If sin theta = 1/2, find the value of theta in "
    "degrees.") == "θ = 30°")
check("inverse angle #163", _ans(
    "If tan A = 1, find the value of A in degrees.")
    == "A = 45°")
check("ratio ask stays ratio (Wave 33)", _ans(
    "If sin theta = 3/5, find the value of tan theta.")
    == "tan θ = 3/4")
check("ratio sum #443", _ans(
    "If sin A = 1/2 and A is acute, find cos A + tan A.")
    == "5·sqrt(3)/6")
check("identity #161", _ans(
    "Prove that sin^2 A + cos^2 A = 1.")
    == "Identity verified ✔")
check("identity sec form", _ans(
    "Prove that tan^2 A + 1 = sec^2 A.")
    == "Identity verified ✔")
check("false identity stays false", _ans(
    "Prove that sin^2 A = cos^2 A.") == "Not an identity")
check("arctan chain #180", _ans(
    "Evaluate tan^-1(1) + tan^-1(2) + tan^-1(3).")
    == "pi")
check("arctan pair contract (Wave 32)", "atan(3)" in
      _ans("Evaluate tan^-1(1) + tan^-1(1/2)."))

print("== 6. GP sum+product ==")
check("GP ratio #123", _ans(
    "The sum of the first three terms of a GP is 39 "
    "and their product is 729. Find the common ratio.")
    == "3 or 1/3")
check("GP terms", _ans(
    "The sum of the first three terms of a GP is 39 "
    "and their product is 729. Find the terms.")
    == "3, 9, 27")

print("== 7. calculus ==")
check("derivative of sin x #268",
      _ans("Find the derivative of sin x.") == "cos(x)")
check("derivative of log x #270",
      _ans("Find the derivative of log x.") == "1/x")
check("derivative of e^(3x) #269",
      _ans("Find the derivative of e^(3x).")
      == "3·exp(3·x)")
check("derivative of tan x #379",
      _ans("Find the derivative of tan x.") == "sec(x)^2")
check("dy/dx if y= #272", _ans(
    "Find dy/dx if y = (3x + 2)^5.") == "15·(3·x + 2)^4")
check("limit in words #273", _ans(
    "Evaluate the limit of (x^2 - 9)/(x - 3) as x "
    "tends to 3.") == "6")
check("limit notation lead-in #274", _ans(
    "Evaluate lim x->2 (x^3 - 8)/(x - 2).") == "12")
check("limit sin x/x #275", _ans(
    "Find the limit of sin x / x as x tends to 0.")
    == "1")
check("limit at infinity #276", _ans(
    "Evaluate the limit of (2x^2 + 3x)/(x^2 - 1) as "
    "x tends to infinity.") == "2")
check("rate of change #383", _ans(
    "Find the rate of change of the area of a circle "
    "with respect to its radius when r = 5 cm.")
    == "10·pi ≈ 31.4159")
check("tangent slope #286", _ans(
    "Find the slope of the tangent to the curve "
    "y = x^2 at x = 3.") == "6")
check("normal slope", _ans(
    "Find the slope of the normal to the curve "
    "y = x^2 at x = 3.") == "-1/6")
check("tangent equation", _ans(
    "Find the equation of the tangent to the curve "
    "y = x^2 at x = 3.") == "y = 6·x - 9")
check("maximum value #285", _ans(
    "Find the maximum value of the function "
    "f(x) = 2x^3 - 15x^2 + 36x + 1.") == "29")
check("minimum value", _ans(
    "Find the minimum value of the function "
    "f(x) = x^3 - 3x^2 + 2.") == "-2")
check("implicit neighbour unchanged",
      _ans("Find dy/dx for x^2 + y^2 = 25.") == "-x/y")
check("line slope neighbour unchanged", _ans(
    "Find the slope of the line joining (2, 3) and "
    "(5, 7).") == "1.33333")

print("== hygiene: pins + frozen logo ==")
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf-8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf-8").read()
# Merge-4: pins reconciled to ?v=37 / ganitra-static-v14
# (Wave 64's patch updated the SW assertion below but left
# this stylesheet assertion at ?v=35; updated here, same
# convention as the merge-3 reconciliation in wave52/56/58.)
check("stylesheet pin at merge-4 reconciliation (?v=37)",
      "stylesheet?v=37" in TPL or "?v=37" in TPL)
check("sw cache pin at merge-2 reconciliation (v8)",
      'GANITRA_CACHE = "ganitra-static-v14"' in SW)
for _name, _want in (
        ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"),
        ("logo-mark.png", "03bc03dc")):
    _p = os.path.join("static", _name)
    if os.path.exists(_p):
        _digest = hashlib.sha256(
            open(_p, "rb").read()).hexdigest()
        check(f"frozen logo {_name} untouched",
              _digest.startswith(_want), _digest[:12])

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
