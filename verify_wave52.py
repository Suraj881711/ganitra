"""Wave 52 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (all solver-side; solver coverage
round 4 — the Wave 47 left-open list):

1. Salvage quality + fraction promotion (audit #15) —
   fallback.py + solver/arithmetic.py: 'Add a/b and c/d'
   / 'Subtract a/b from c/d' are PRIMARY patterns with
   LCM working (the salvage layer used to echo the first
   operand: 31 of 52 audit salvage answers carried a
   wrong value); salvage now refuses a result whose
   value is not the asked sum/difference; the junk
   detector catches bare *-chains of 5+ single letters
   ('Find the square of 15' -> '15*a*e*q*r*s*u', the word
   'square' letter-multiplied) and square/cube-of-N is a
   primary pattern.
2. Hindi leftovers (audit #1) — fallback.py,
   solver/applied.py, solver/router.py: the junk
   detector counts single-letter factors in ANY script
   (the Hindi soup is Devanagari and carried only ~2
   Latin letters, so it was served as the answer), and
   the top Hindi statement forms are strict patterns
   (square/rectangle/circle/cylinder/cone/sphere/
   hemisphere/cube mensuration, simple interest,
   percentage-of, triangle third angle and area, the
   'तीन गुने' linear equation, tower height, direct
   train time), reached via a Devanagari pre-check that
   accepts only hindi_* ops. The speed-increase train
   quadratic (#450-452) is explicitly NOT the train-time
   pattern — its first cut regressed those to 360/5=72
   and the battery diff caught it.
3. Echo cases — solver/applied.py (#32: divide-among
   with a named share ask; #349: triangle angles in a
   ratio) and solver/number_theory.py (#437: the other
   number from HCF x LCM / one number).
4. 'theta'-worded identities — solver/trigonometry.py:
   the identity verifier maps theta/alpha/beta/gamma to
   single letters and cosec to csc before parsing (the
   spelled-out name errored the whole ask).
5. Sqrt-form ratio values — solver/trigonometry.py:
   'cos theta = sqrt(3)/2' parses; triangle sides come
   from sp.fraction so irrational values split into
   (numerator, denominator) pairs.
6. Conic tangents — solver/calculus.py: T = 0 for the
   circle x^2 + y^2 = r^2 and the parabola y^2 = kx,
   the point verified on the conic first.
7. Integral of e^(kx) — solver/calculus.py: the Wave
   47 Euler swap mirrored into the integral path (was:
   a Piecewise in log(e)).

Measured: pytest 620 -> 640 passed / 5 skipped (20 new
tests in test/test_wave52_fixes.py); the 515-question
Wave 35 battery (same automated adjudication both runs)
moves EXACT 335 -> 367, FALLBACK 151 -> 140, WRONG
29 -> 8, ERROR 0 -> 0, with ZERO per-item regressions
(33 improvements; #384/#479 keep their EXACT verdicts
but their answers change from letter-soup to the clean
values, and #502's wrong-value salvage becomes an
honest guide fallback). verify_wave47.py stays 50/0.

No template/CSS/JS/i18n/auth changes; pins stay at the
merged tree's ?v=31 / ganitra-static-v8; the frozen
logo files are untouched. The pi convention is
unchanged (owner's open call).

Deliberately NOT taken (documented in
ganitra-wave52-topics.md): the remaining 8 battery
WRONGs (float-form factorise/expand answers, the
concentric-chord ask, the transpose format, the
a/b-substitution system garbage, the 100-toss
probability wording, the rationalise token form),
general-form conic tangents and conic normals,
Hinglish free-form fraction expressions, and the ODE
prose parse failure — all pre-existing.
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
from api import _solve_friendly  # noqa: E402
from fallback import _is_junk  # noqa: E402


def _op(q):
    return str(solve_question(q).get("op", ""))


def _ans(q):
    return str(solve_question(q).get("answer", ""))


print("== 1. fractions + salvage quality (audit #15) ==")
check("add 2/3 and 3/4 #7", _ans("Add 2/3 and 3/4.") == "17/12")
check("add 1/2 and 2/3 #8", _ans("Add 1/2 and 2/3.") == "7/6")
check("subtract #13", _ans("Subtract 1/4 from 5/6.") == "7/12")
check("subtract #14", _ans("Subtract 2/3 from 7/9.") == "1/9")
check("add with filler words",
      _ans("Add the fractions 2/3 and 3/4.") == "17/12")
check("square of 15 #33", _ans("Find the square of 15.") == "225")
check("square of 18 #34", _ans("Find the square of 18.") == "324")
check("square of 25 #35", _ans("Find the square of 25.") == "625")
check("junk: latin letter chain",
      _is_junk("Find the square of 15.",
               {"answer": "15*a*e*q*r*s*u"}))
check("junk: devanagari soup",
      _is_junk("एक वर्ग की भुजा 12 cm है।",
               {"answer": "12*c*m*इ*ए**2*क**4*ग*ज**3*ञ*त"}))
check("not junk: pi answer",
      not _is_junk("circle area", {"answer": "100·pi ≈ 314.159"}))

print("== 2. Hindi patterns (audit #1) ==")
check("square perimeter #385",
      _ans("एक वर्ग की भुजा 12 cm है। इसका परिमाप ज्ञात "
           "कीजिए।") == "48")
check("rectangle area #384",
      _ans("एक आयत की लंबाई 15 cm और चौड़ाई 10 cm है। इसका "
           "क्षेत्रफल ज्ञात कीजिए।") == "150")
check("SI #389", _ans(
    "12000 रुपये का 3 वर्ष के लिए 5% वार्षिक दर से साधारण "
    "ब्याज ज्ञात कीजिए।") == "1800")
check("SI #475", _ans(
    "5000 रुपये का 2 वर्ष के लिए 6% वार्षिक दर से साधारण "
    "ब्याज ज्ञात कीजिए।") == "600")
check("third angle #391", _ans(
    "त्रिभुज के दो कोण 60 डिग्री और 70 डिग्री हैं। तीसरा "
    "कोण ज्ञात कीजिए।") == "50°")
check("circle area #427", "314.159" in _ans(
    "एक वृत्त की त्रिज्या 10 cm है। इसका क्षेत्रफल ज्ञात "
    "कीजिए।"))
check("linear equation #429", _ans(
    "एक संख्या के तीन गुने में 7 जोड़ने पर 40 प्राप्त होता "
    "है। संख्या ज्ञात कीजिए।") == "11")
# Wave 99 (pi policy): radii 7/14/21 -> pi = 22/7 below.
check("cylinder CSA #432", "220" in _ans(
    "एक बेलन का वक्र पृष्ठ क्षेत्रफल ज्ञात कीजिए जिसकी "
    "त्रिज्या 7 cm और ऊंचाई 5 cm है"))
check("sphere volume #460", "1437.33" in _ans(
    "7 cm त्रिज्या वाले गोले का आयतन ज्ञात कीजिए।"))
check("cylinder volume #461", "1540" in _ans(
    "एक बेलन की त्रिज्या 7 cm और ऊंचाई 10 cm है। बेलन का "
    "आयतन ज्ञात कीजिए।"))
check("cone volume #462", "37.6991" in _ans(
    "एक शंकु की त्रिज्या 3 cm और ऊंचाई 4 cm है। शंकु का "
    "आयतन ज्ञात कीजिए।"))
check("cube volume #463",
      _ans("9 cm भुजा वाले घन का आयतन ज्ञात कीजिए।") == "729")
check("circle area #464", "616" in _ans(
    "14 cm त्रिज्या वाले वृत्त का क्षेत्रफल ज्ञात कीजिए।"))
check("hemisphere volume #465", "718.667" in _ans(
    "एक अर्धगोले की त्रिज्या 7 cm है। इसका आयतन ज्ञात "
    "कीजिए।"))
check("percentage #478",
      _ans("240 का 25 प्रतिशत ज्ञात कीजिए।") == "60")
check("tower height #480", _ans(
    "एक मीनार के पाद से 50 m दूर बिंदु से मीनार की चोटी का "
    "उन्नयन कोण 45 डिग्री है। मीनार की ऊंचाई ज्ञात कीजिए।")
    == "50")
check("triangle area #481", _ans(
    "त्रिभुज का क्षेत्रफल ज्ञात कीजिए जिसका आधार 10 cm और "
    "ऊंचाई 12 cm है।") == "60")
check("circle perimeter #483", "132" in _ans(
    "वृत्त की त्रिज्या 21 cm है। इसका परिमाप ज्ञात कीजिए।"))
check("train time #479", _ans(
    "एक रेलगाड़ी 60 km/h की चाल से 300 km की दूरी कितने "
    "समय में तय करेगी?") == "5")
check("train quadratic NOT hijacked #450", _ans(
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। "
    "यदि यह चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 "
    "घंटा कम समय लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
    == "40 km/h")
check("concept ask honest fallback #514",
      _solve_friendly("पाइथागोरस प्रमेय क्या है?").get(
          "fallback_kind") == "concept")

print("== 3. echo cases ==")
check("divide among, C's share #32", _ans(
    "Divide Rs 900 among A, B and C in the ratio 2:3:4. "
    "How much does C get?") == "Rs 400")
check("divide among, A's share", _ans(
    "Divide Rs 900 among A, B and C in the ratio 2:3:4. "
    "How much does A get?") == "Rs 200")
check("plain divide unchanged",
      _ans("Divide Rs 600 in the ratio 2:3.")
      == "Rs 240 and Rs 360")
check("triangle angles largest #349", _ans(
    "The angles of a triangle are in the ratio 2:3:4. "
    "Find the largest angle.") == "80°")
check("triangle angles smallest", _ans(
    "The angles of a triangle are in the ratio 2:3:4. "
    "Find the smallest angle.") == "40°")
check("HCF/LCM other number #437", _ans(
    "The HCF of two numbers is 12 and their LCM is 240. "
    "If one number is 60, find the other number.") == "48")
check("HCF and LCM together unchanged",
      _ans("Find the HCF and LCM of 12 and 18.")
      == "HCF = 6, LCM = 36")

print("== 4. theta identities ==")
check("sin^2+cos^2 theta",
      _ans("Prove that sin^2 theta + cos^2 theta = 1")
      == "Identity verified ✔")
check("tan^2+1 theta",
      _ans("Prove that tan^2 theta + 1 = sec^2 theta")
      == "Identity verified ✔")
check("product identity theta",
      _ans("Prove that (1 - cos theta)(1 + cos theta) "
           "= sin^2 theta") == "Identity verified ✔")
check("cosec^2 theta",
      _ans("Prove that cosec^2 theta - cot^2 theta = 1")
      == "Identity verified ✔")
check("false identity stays honest",
      _ans("Prove that sin^2 theta + cos^2 theta = 2")
      == "Not an identity")
check("letter-angle identity unchanged",
      _ans("Prove that sin^2 A + cos^2 A = 1")
      == "Identity verified ✔")

print("== 5. sqrt-form ratios ==")
check("cos theta sqrt -> angle",
      _ans("If cos theta = sqrt(3)/2, find theta.")
      == "θ = 30°")
check("sin theta sqrt -> angle",
      _ans("If sin theta = sqrt(3)/2, find the value of "
           "theta in degrees.") == "θ = 60°")
check("tan theta sqrt -> angle",
      _ans("If tan theta = sqrt(3), find theta.")
      == "θ = 60°")
check("sin theta 1/sqrt(2)",
      _ans("If sin theta = 1/sqrt(2), find theta.")
      == "θ = 45°")
check("sqrt ratio conversion",
      _ans("If cos theta = sqrt(3)/2, find sin theta and "
           "tan theta.") == "sin θ = 1/2, tan θ = sqrt(3)/3")
check("rational ratio unchanged",
      _ans("If sin A = 3/5, find cos A.") == "cos A = 4/5")

print("== 6. conic tangents ==")
check("circle tangent 3-4-5", _ans(
    "Find the equation of the tangent to the circle "
    "x^2 + y^2 = 25 at the point (3, 4).")
    == "3·x + 4·y = 25")
check("circle tangent r13", _ans(
    "Find the equation of the tangent to the circle "
    "x^2 + y^2 = 13 at (2, 3).") == "2·x + 3·y = 13")
check("point off circle falls through",
      _op("Find the equation of the tangent to the circle "
          "x^2 + y^2 = 25 at the point (1, 1).")
      != "conic_tangent_circle")
check("parabola tangent", _ans(
    "Find the equation of the tangent to the parabola "
    "y^2 = 4x at the point (1, 2).") == "y = x + 1")
check("parabola tangent 8x", _ans(
    "Find the equation of the tangent to the parabola "
    "y^2 = 8x at (2, 4).") == "y = x + 2")
check("curve tangent unchanged", _ans(
    "Find the equation of the tangent to the curve "
    "y = x^2 at x = 3.") == "y = 6·x - 9")

print("== 7. integral of e^(kx) ==")
check("integrate e^2x wrt",
      _ans("Integrate e^(2x) with respect to x.")
      == "exp(2·x)/2 + C")
check("integrate e^2x dx",
      _ans("Integrate e^(2x) dx") == "exp(2·x)/2 + C")
check("integral of e^3x",
      _ans("Find the integral of e^(3x).")
      == "exp(3·x)/3 + C")
check("integrate e^x",
      _ans("Integrate e^x with respect to x.")
      == "exp(x) + C")
check("no piecewise/log(e) residue",
      "Piecewise" not in _ans("Integrate e^(2x) dx")
      and "log(e)" not in _ans("Integrate e^(2x) dx"))
check("plain integral unchanged",
      _ans("Integrate x^3 with respect to x.")
      == "x^4/4 + C")
check("derivative of e^3x unchanged",
      _ans("Find the derivative of e^(3x).")
      == "3·exp(3·x)")

print("== hygiene: pins + frozen logo ==")
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf-8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf-8").read()
# Merge-3: Wave 55 legitimately bumped the pins to
# ?v=35 / ganitra-static-v15; assertions updated.
# Merge-4: pins reconciled to ?v=38 / ganitra-static-v15
# (Wave 64's CSS is the newest); assertion updated.
check("stylesheet pin (?v=38 after Wave 64)", "?v=38" in TPL)
check("sw cache pin (v9 after Wave 55)",
      'GANITRA_CACHE = "ganitra-static-v15"' in SW)
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
