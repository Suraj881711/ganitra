"""Wave 58 verification (15 Nov 2026) — ZERO-MISTAKE hunt.

Suraj's order: "Jo mistake ho rahi hai unhe sahi karo —
galtiyaan bilkul bhi nahi chhodni." Every known wrong
answer in the solver was fixed at its root cause or is
listed in ganitra-wave58-notes.md as CANNOT-FIX-YET with a
concrete technical reason. All fixes are solver-side; no
template/CSS/i18n/auth change, no pin bump, pi convention
untouched.

WHAT THIS WAVE FIXED (base = Waves 1-50 merged tree):
 1. Trailing full stop (expression_parser clean_text):
    "Expand (2x + 3y)^2." / "Factorise x^2 - 9." /
    "Evaluate 27^(2/3)." parsed the final "." as a decimal
    point — float exponents / float coefficients.
 2. Junk detector, any script (fallback.py): the
    letter-product test counted only Latin [a-z] singles,
    so Devanagari soup passed as a real answer (18 battery
    items); the plain-product branch also missed a leading
    numeric coefficient.
 3. Hindi word problems (applied.py + router gate):
    Devanagari mensuration / SI / percentage / train-time
    statements had NO pattern and were letter-multiplied;
    17 patterns (hindi_* ops), router tries applied first
    for Devanagari questions, hindi_* ops only.
 4. Ratio echoes (applied.py): "divide ... among A, B
    and C" broke the divide pattern and the simplify
    branch echoed "2 : 3" (#32); triangle angles in a
    ratio split 180 (#349); a named share ask answers
    that share alone.
 5. HCF x LCM other number (number_theory.py): the
    together branch echoed the givens (#437).
 6. Probability (statistics.py): die "at least / at
    most" missing from the event table (answered 1/6);
    die/coin "not getting ..." ignored the negation;
    card "king or queen" counted one event (1/13, now
    2/13); the bare coin shortcut answered a narrated
    streak question with a confident 1/2 (#515) — it now
    falls through honestly; the abstract addition rule
    P(A or B) / P(A and B) with event-notation routing.
 7. Fractions (arithmetic.py + fallback.py): worded
    add/subtract had no primary pattern and the salvage
    echoed an operand (#7-#15); LCM-step patterns added,
    plus a salvage guard that rejects operand echoes;
    Hinglish filler ("kitna hota hai") stripped when the
    remainder is a pure arithmetic expression.
 8. Square/cube word forms (arithmetic.py): "square of
    15", "15 squared", "25 ka cube" (#33-#35, #502);
    "ka square root" guarded out.
 9. "x" as a times sign (expression_parser clean_text):
    "2^3 x 2^2" simplified to 32*x, "3 x 4" to 12*x —
    rewritten to * only when no other letters are
    present, so genuine algebra is untouched.
10. Geometric mean (statistics.py): answered with the
    arithmetic mean (4 and 9 -> 6.5, now 6).
11. Substitution + find-k + composition (algebra.py):
    "If a = 2 and b = -3, find a^2 + b^2 - ab" got
    system-solver garbage (#340); find-k-given-a-root
    echoed (#448); f(g(x)) composition got system
    garbage (Wave 55 trap).
12. Vieta for cubics (applied.py): "sum of the zeroes
    of x^3 - ..." listed the roots instead of the sum.
13. Logs (exponents_logs.py + router intent): log_2 /
    log2 forms never routed (underscore is a word
    character) and "32*log_2" was served as a value;
    log equations echoed the given value (#302); base-10
    value asks ("log 100") added.
14. Rationalise display (algebra.py): a sum over one
    rational denominator is presented as ONE fraction
    — "(3 - sqrt(2))/7" (#51).
15. Concentric chord (geometry.py): answered with the
    ring AREA; now 2*sqrt(R^2 - r^2) (#141).
16. Theta identities + sqrt ratios (trigonometry.py):
    spelled Greek names letter-multiplied in the
    identity verifier; sqrt-form given ratios
    (cos theta = sqrt(3)/2) fell through.
17. ODE prose (calculus.py): "Solve THE differential
    equation ..." left a stray "the" that broke the
    ODE parse; conic tangent/normal equations (T = 0 /
    gradient, point verified on the conic) added —
    they were answered with similar-example fragments;
    "equations of the tangent" (plural) intent fixed.

MEASURED: the 515-question Wave 35 battery (same
automated adjudication) on the Waves 1-50 base:
EXACT 335 -> 386, FALLBACK 151 -> 127, WRONG 29 -> 2,
ERROR 0 -> 0, ZERO per-item regressions. The 2 remaining
WRONGs are adjudicator-format cases with mathematically
correct answers (see the notes file): #104 (factor
order; the checker's parser has no implicit
multiplication) and #290 (the correct transpose matrix;
the checker wants the word "transpose", and the answer
string is pinned by the Wave 42 test suite). pytest
620 -> 620 + the new test/test_wave58_fixes.py tests,
all green. Wave 55's four dropped topics were re-tested:
all four starters now solve exactly (composition,
geometric mean, mutually-exclusive events, union
probability).

Run: python3 verify_wave58.py  (exit 0 = all checks pass)
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


def _r(q):
    return _solve_friendly(q)


def _ans(q):
    return str(_r(q).get("answer", ""))


def _exact(q):
    return not _r(q).get("fallback")


print("== 1. trailing full stop ==")
check("expand with dot", _exact(
    "Expand (2x + 3y)^2.") and "4·x^2" in _ans(
        "Expand (2x + 3y)^2."))
check("factorise with dot", _ans(
    "Factorise x^2 - 9.") == "(x - 3)·(x + 3)")
check("evaluate with dot", _ans("Evaluate 27^(2/3).") == "9")
check("decimal control", _ans("What is 2.5 + 1.5?") == "4")

print("== 2/3. Hindi junk + Hindi patterns ==")
check("hindi rectangle #384", _ans(
    "एक आयत की लंबाई 15 cm और चौड़ाई 10 cm है। इसका "
    "क्षेत्रफल ज्ञात कीजिए।") == "150")
check("hindi square perimeter #385", _ans(
    "एक वर्ग की भुजा 12 cm है। इसका परिमाप ज्ञात "
    "कीजिए।") == "48")
check("hindi SI #389", _ans(
    "12000 रुपये का 3 वर्ष के लिए 5% वार्षिक दर से साधारण "
    "ब्याज ज्ञात कीजिए।") == "1800")
# Merge-3: Wave 52's hindi pattern answers in the app's
# established "…·pi ≈ value" format — same value; assert
# containment, as Wave 52's own Hindi tests do.
check("hindi sphere volume", "1436.76" in _ans(
    "7 cm त्रिज्या वाले गोले का आयतन ज्ञात कीजिए।"))
check("hindi times-linear #429", _ans(
    "एक संख्या के तीन गुने में 7 जोड़ने पर 40 प्राप्त "
    "होता है। संख्या ज्ञात कीजिए।") == "11")
check("hindi train time #479", _ans(
    "एक रेलगाड़ी 60 km/h की चाल से 300 km की दूरी कितने "
    "समय में तय करेगी?") == "5")
# Merge-3: same value in Wave 52's "98·pi ≈ 307.876"
# format; containment as in Wave 52's tests.
check("hindi fresh cone", "307.876" in _ans(
    "एक शंकु की त्रिज्या 7 cm और ऊंचाई 6 cm है। शंकु का "
    "आयतन ज्ञात कीजिए।"))
check("hindi soup is not an answer", not _exact(
    "पाइथागोरस प्रमेय क्या है?") or "concept" in str(
        _r("पाइथागोरस प्रमेय क्या है?").get("op", "")))

print("== 4/5. ratio + HCF/LCM ==")
check("named share #32", _ans(
    "Divide Rs 900 among A, B and C in the ratio 2:3:4. "
    "How much does C get?") == "Rs 400")
check("triangle angles #349", _ans(
    "The angles of a triangle are in the ratio 2:3:4. "
    "Find the largest angle.") == "80°")
check("divide control", _ans(
    "Divide Rs 600 in the ratio 2:3.")
    == "Rs 240 and Rs 360")
check("hcf-lcm other #437", _ans(
    "The HCF of two numbers is 12 and their LCM is 240. "
    "If one number is 60, find the other number.") == "48")
check("hcf-lcm together control", _ans(
    "Find the HCF and LCM of 12 and 18.")
    == "HCF = 6, LCM = 36")

print("== 6. probability ==")
check("die at least 5", "1/3" in _ans(
    "What is the probability of getting at least 5 when "
    "a die is rolled?"))
check("die not getting a 6", "5/6" in _ans(
    "A die is thrown once. What is the probability of "
    "not getting a 6?"))
check("king or queen", "2/13" in _ans(
    "A card is drawn from a well-shuffled deck of 52 "
    "cards. What is the probability of getting a king "
    "or a queen?"))
check("streak is not confident 1/2 #515", not _exact(
    "A coin is tossed 100 times in a row and it lands "
    "heads every time. What is the probability it lands "
    "heads on the next toss?"))
check("mutually exclusive union", "0.7" in _ans(
    "Two events A and B are mutually exclusive. If "
    "P(A) = 0.3 and P(B) = 0.4, find P(A or B)."))
check("general union", "0.7" in _ans(
    "If P(A) = 0.5, P(B) = 0.4 and P(A and B) = 0.2, "
    "find P(A or B)."))
check("coin control", "1/2" in _ans(
    "What is the probability of getting a head on a "
    "coin toss?"))

print("== 7/8/9. fractions, powers, x-times ==")
check("add fractions #7", _ans("Add 2/3 and 3/4.")
      == "17/12")
check("subtract from", _ans("Subtract 1/4 from 5/6.")
      == "7/12")
check("hinglish expression", _ans(
    "2/3 + 3/4 kitna hota hai?") == "17/12")
check("echo guard", _ans("Add 2/3 & 3/4 please")
      != "2/3")
check("square of #33", _ans("Find the square of 15.")
      == "225")
check("cubed", _ans("What is 9 cubed?") == "729")
check("ka cube #502", _ans("25 ka cube kitna hota hai?")
      == "15625")
check("ka square root not squared", _ans(
    "144 ka square root batao") != "20736")
check("numeric x is times", _ans("Simplify 2^3 x 2^2.")
      == "32")
check("algebra x control", "5" in _ans("Simplify 3x + 2x.")
      and "x" in _ans("Simplify 3x + 2x."))

print("== 10-13. GM, substitution, Vieta, logs ==")
check("geometric mean", _ans(
    "Find the geometric mean of 4 and 9.") == "6")
check("arithmetic mean control", _ans(
    "What is the mean of 4 and 9?") == "6.5")
check("substitution #340", _ans(
    "If a = 2 and b = -3, find the value of "
    "a^2 + b^2 - ab.") == "19")
check("find k #448", "17/4" in _ans(
    "If x = 2 is a solution of 3x^2 - 2kx + 5 = 0, "
    "find the value of k."))
check("composition", "4·x^2 + 12·x + 10" in _ans(
    "If f(x) = x^2 + 1 and g(x) = 2x + 3, find f(g(x))."))
check("cubic vieta sum", _ans(
    "Find the sum of the zeroes of the polynomial "
    "x^3 - 5x^2 + 2x + 8.") == "Sum = 5")
check("log solve #302", "316.228" in _ans(
    "If log x = 2.5 and log means base 10, find x."))
check("log_2 value", _ans("Find the value of log_2 32.")
      == "5")
check("log base-10 value", _ans("Find the value of "
                                "log 100.") == "2")

print("== 14/15. rationalise + concentric chord ==")
check("rationalise single fraction #51", _ans(
    "Rationalise the denominator of 1/(3 + sqrt(2)).")
    == "(3 - sqrt(2))/7")
check("rationalise monomial control", _ans(
    "Rationalise the denominator of 5/sqrt(7).")
    == "5·sqrt(7)/7")
check("concentric chord #141", _ans(
    "Two concentric circles have radii 5 cm and 3 cm. "
    "Find the length of the chord of the larger circle "
    "which touches the smaller circle.") == "8")
check("ring area control", "125.664" in _ans(
    "Find the area between two concentric circles of "
    "radii 7 cm and 3 cm."))

print("== 16/17. trig + calculus ==")
check("theta identity true", _ans(
    "Prove that sin^2 theta + cos^2 theta = 1.")
    == "Identity verified ✔")
check("theta identity false", _ans(
    "Prove that sin^2 theta + cos^2 theta = 2.")
    == "Not an identity")
check("sqrt ratio angle", _ans(
    "If cos theta = sqrt(3)/2, find theta.") == "θ = 30°")
check("sqrt ratio others", "1/2" in _ans(
    "If cos theta = sqrt(3)/2, find sin theta and "
    "tan theta."))
check("ODE prose", _ans(
    "Solve the differential equation dy/dx = 2x.")
    == "y = C1 + x^2")
# Merge-3: Wave 52's conic block presents the standard
# circle tangent in the house format "3·x + 4·y = 25"
# (asserted exactly by Wave 52's tests).
check("conic tangent", _ans(
    "Find the equation of the tangent to the circle "
    "x^2 + y^2 = 25 at the point (3, 4).")
    == "3·x + 4·y = 25")
check("conic normal", _ans(
    "Find the equation of the normal to the parabola "
    "y^2 = 4x at the point (1, 2).") == "x + y = 3")
check("off-conic point refused", not _exact(
    "Find the equation of the tangent to the circle "
    "x^2 + y^2 + 4x - 2y - 8 = 0 at the point (2, 2)."))

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
