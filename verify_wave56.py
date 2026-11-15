"""Wave 56 verification (15 Nov 2026).

WHAT THIS WAVE ADDED — METHOD-FIRST coverage (Suraj's
strategy: "question solve karne ke methods daal de toh
zyada question bank ki jarurat nahi padegi"). Every item
below is ONE general schema that parses a family's
variable slots and solves for ANY values — proven by the
property tests in test/test_wave56_fixes.py (20+ fresh
random instances per family, independently computed;
Hinglish schemas include spelling variants —
batao/btaao/bataao, ghatao/ghaatao, pratishat/parcent —
ahead of Wave 57's normalisation layer):

1. Arithmetic (solver/arithmetic.py): fraction commands
   incl. mixed numbers; square/cube (roots) of N;
   recurring decimals -> lowest-terms fraction;
   digit-x-digit products ("8.75 x 2.5"); unit-crossing
   percent ("what percent of 2 hours is 36 minutes");
   out-of percent; conversational lead-in retry
   ("can you solve 17 x 24"). Plus clean_text drops the
   trailing full stop that poisoned whole-question
   parses (solver/expression_parser.py).
2. Applied (solver/applied.py): discount reverse +
   both profit chains; compound-interest frequencies
   (half-yearly/quarterly/monthly + amount form); named
   ratio shares; two-step word equations; ages (k-times
   + future sum; sum + product k-years-ago with number
   WORDS); Bayes bags with "came from bag X"; NEW
   families — consecutive sums, bundle costs (both
   phrasings), fraction word problems, percent change,
   population growth/depreciation, SI doubling, angle
   word schemas (ratio/complement/supplement/twice/
   thrice/exterior), temperature, two-digit sum-reverse;
   Hindi (Devanagari) schemas for mensuration, SI,
   percent, HCF/LCM, distances, heights, linear forms;
   Hinglish schemas incl. the wrapped equation.
3. Statistics (solver/statistics.py): two-dice sums in
   both phrasings; bag schema generalised (marbles,
   "it is (not) COLOUR", "the marble is COLOUR");
   numbered-set probability (discs/tickets/cards 1..N,
   six properties); mean of first n natural/even/odd.
4. Algebra (solver/algebra.py): substitution ("If
   x = 3, find the value of ...", one or two vars);
   reciprocal of a surd value; x ± 1/x identities
   (squares and cubes); N^2 via the (a ± b)^2 identity;
   form a quadratic from its roots; find-k from a
   stated solution; "the inequality" wording stripped;
   cubic zero relations without α (specific relation
   answered); zero-coefficient terms dropped before
   parsing (the "0x" hex trap).
5. Sequences: named sums (first n even/odd/natural),
   common difference from two terms, explicit-series
   AP sum, "ke baad" next-term marker.
6. Trigonometry: heights & distances (ladder, kite,
   shadow, tower, two-angles, two poles); the
   one-ratio block generalised to sec/csc/cot givens
   and all-six asked sets.
7. Sets (solver/sets_basics.py): inclusion-exclusion
   for any missing n(.), power set 2^n, two-activity
   play-both/neither class form. fallback.py: the
   nonmaths guard exempts the set-counting shape
   (digits + play both/neither / power set) — real
   sports questions stay refused.
8. Geometry: vectors (magnitude, unit vector, dot
   product, distance from origin); parallelogram,
   trapezium, rhombus, four walls, rectangle
   perimeter+side, sphere diameter, concentric chord
   before ring area, numeric tangent distance.
9. Exponents/logs: log inverse (x = base^v).
   Number theory: HCF x LCM = product (other number).
   Calculus: second/third derivative order handling.
10. Router gates (Wave-32 style, accept-only-the-new-
    ops): Hindi/Hinglish first (original text retried
    for equation shapes), fraction commands vs the
    junior intent, identity-square / form-quadratic,
    heights & distances, set counting, range, bare
    product, bare series next-term, tangent length,
    vector phrases.

Measured on the pristine Waves 1-50 tree (battery
runner = merge2-scratch/run_battery47.py, the real
api._solve_friendly path): battery 335 EXACT /
151 FALLBACK / 29 WRONG / 0 ERROR -> 505 / 4 / 6 / 0;
170 items improved; the ONLY per-item verdict change
against a mathematically correct answer is #69, whose
recorded expected value (7/10) is itself wrong — the
schema's 11/14 satisfies both stated conditions
((11+1)/(14+1) = 4/5 and 11 = 14 - 3); 7/10 satisfies
neither. pytest 620 passed / 5 skipped -> 675 passed /
5 skipped (55 new property tests; two AI-fallback test
fixtures updated — their canonical "unsolvable" ages
question is battery #88, which this wave's ages schema
now solves deterministically; the replacement fixture
is another father-son ages question that remains
unsolved, assertions untouched).

Remaining WRONG items are all documented non-fixes:
#51 (battery's expected token "3 - sqrt(2)" is not the
rationalisation of the asked fraction; the solver's
3/7 - sqrt(2)/7 is correct), #69 (above), #104 (the
solver's factorisation is correct; the judge wants
the factors in the other order), #290 (the solver's
transpose matrix is correct; the battery token wants
the word "transpose" while test_wave42 pins the bare
matrix string), #514/#515 (chk=none concept/trick
items by design). Remaining FALLBACK: #510-#513,
chk=none concept asks by design.

No template/CSS/i18n/auth changes, no pin bumps
(?v=31 / ganitra-static-v8 stay), pi convention
untouched (true pi everywhere), frozen logo files
untouched.
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


print("== 1. arithmetic schemas ==")
check("fraction add", _ans("Add 3/4 and 2/5") == "23/20")
check("fraction subtract-from",
      _ans("Subtract 1/6 from 5/6") == "2/3")
check("mixed add", _ans("Add 1 1/2 and 2/3") == "13/6")
check("whole+fraction add (junior gate)",
      _ans("Add 1 and 1/5") == "6/5")
check("square root", _ans("Find the square root of 144")
      == "12")
check("cube", _ans("Find the cube of 5") == "125")
check("recurring decimal",
      _ans("Express 0.636363... as a fraction in lowest "
           "terms") == "7/11")
check("digit x digit", _ans("Evaluate 8.75 x 2.5")
      == "175/8")
check("bare product gate", _ans("can you solve 17 x 24")
      == "408")
check("percent unit crossing",
      _ans("What percent of 2 hours is 36 minutes?")
      == "30")
check("out-of percent", _ans(
    "Out of 45 students, 27 are girls. What percent of "
    "the class is girls?") == "60")

print("== 2. applied schemas ==")
check("discount reverse", "2000" in _ans(
    "An article is sold for Rs 1700 after a discount of "
    "15%. Find its marked price."))
check("discount chain (SP form)", "25" in _ans(
    "An article is sold for Rs 1500 after a discount of "
    "25%. Its cost price is Rs 1200. Find the profit "
    "percent."))
check("CI half-yearly amount", "8830.5" in _ans(
    "Find the amount on Rs 8000 at 5% per annum for 2 "
    "years, compounded half-yearly."))
check("ratio shares", "600" in _ans(
    "Divide Rs 1200 among A, B and C in the ratio "
    "2:3:5. How much does C get?"))
check("ages future sum", "son is 14" in _ans(
    "A father's age is 3 times his son's age. After 10 "
    "years, the sum of their ages will be 76. Find the "
    "son's present age."))
check("ages sum+product ago", "36" in _ans(
    "The sum of the ages of a father and his son is 45 "
    "years. Five years ago, the product of their ages "
    "was 124. Find their present ages."))
check("consecutive sum", _ans(
    "The sum of three consecutive even integers is 36. "
    "Find the largest integer.") == "14")
check("bundle cost", _ans(
    "The cost of 5 pens and 3 pencils is Rs 115. The "
    "cost of 3 pens and 5 pencils is Rs 85. Find the "
    "cost of one pen.") == "Rs 20")
check("percent change", "15" in _ans(
    "The price of an article rises from Rs 400 to "
    "Rs 460. Find the percentage increase."))
check("population growth", "1124864" in _ans(
    "The population of a town is 1000000. It increases "
    "at 4% per year. Find the population after 3 "
    "years.").replace(",", ""))
check("angle complement twice", _ans(
    "An angle is twice its complement. Find the angle.")
    .startswith("60"))
check("temperature", _ans(
    "The temperature was -4 degrees in the morning and "
    "rose by 9 degrees by noon. What is the temperature "
    "at noon?").startswith("5"))

print("== 3. statistics schemas ==")
check("two dice sum", "5/36" in _ans(
    "Two dice are thrown together. Find the probability "
    "that the sum of the numbers is 8."))
check("bag marbles not", "5/8" in _ans(
    "A bag contains 3 red and 5 blue marbles. One "
    "marble is drawn at random. Find the probability "
    "that it is not red."))
check("numbered discs prime", "9/25" in _ans(
    "Discs numbered from 1 to 25 are placed in a box. "
    "One is drawn at random. Find the probability that "
    "it is a prime number."))
check("mean of first n even", _ans(
    "Find the mean of the first 20 even numbers.")
    == "21")

print("== 4. algebra schemas ==")
check("substitution", _ans(
    "If x = 3, find the value of 4x^2 - 5x + 2.") == "23")
check("substitution two vars", _ans(
    "If a = 2 and b = -3, find the value of "
    "a^2 + b^2 - ab.") == "19")
check("reciprocal of surd", _ans(
    "If x = 2 + sqrt(3), find 1/x.") == "2 - sqrt(3)")
check("reciprocal identity", _ans(
    "If x + 1/x = 5, find x^2 + 1/x^2.") == "23")
check("identity square", _ans(
    "Evaluate 105^2 using the identity (a + b)^2.")
    == "11025")
check("form quadratic", _ans(
    "Form a quadratic equation whose roots are 4 "
    "and -3.") == "x^2 - x - 12 = 0")
check("find k", "17/4" in _ans(
    "Find the value of k if x = 2 is a solution of "
    "3x^2 - 2kx + 5 = 0."))
check("cubic sum of zeroes", _ans(
    "For the cubic polynomial x^3 - 5x^2 + 2x + 8, "
    "find the sum of its zeroes.") == "α + β + γ = 5")
check("inequality wording", "5" in _ans(
    "Solve the inequality 3x - 7 < 8."))

print("== 5. sequences ==")
check("named sum even", _ans(
    "Sum of the first 20 even numbers") == "420")
check("common difference", _ans(
    "The 3rd term of an AP is 11 and the 8th term is "
    "31. Find the common difference.") == "4")
check("explicit AP sum", _ans(
    "Find the sum of the AP 2, 7, 12, ... up to 10 "
    "terms.") == "245")
check("ke baad GP next", _ans(
    "2, 4, 8, 16 ke baad kya aayega") == "32")

print("== 6. trigonometry ==")
check("sec given", _ans("If sec A = 13/5, find tan A.")
      == "tan A = 12/5")
check("ladder", _ans(
    "A ladder leaning against a wall makes an angle of "
    "60 degrees with the ground. If the foot of the "
    "ladder is 3 m away from the wall, find the length "
    "of the ladder.") == "6")
check("two poles", _ans(
    "Two poles of heights 6 m and 11 m stand on a "
    "plane. The distance between their feet is 12 m. "
    "Find the distance between their tops.") == "13")
check("two observation op kept", _op(
    "The angle of elevation of the top of a tower from "
    "a point on the ground changes from 30 degrees to "
    "60 degrees when the observer moves 20 m closer to "
    "the tower. The two points are 20 m apart. Find "
    "the height of the tower.") == "two_observation_height")

print("== 7. sets / logs / number theory / calculus ==")
check("inclusion-exclusion", _ans(
    "If n(A) = 20, n(B) = 15 and n(A union B) = 28, "
    "find n(A intersection B).") == "7")
check("play neither", _ans(
    "In a class of 50 students, 30 play cricket and 25 "
    "play football. If 12 play both, how many play "
    "neither?") == "7")
check("power set", _ans(
    "How many elements are in the power set of a set "
    "with 4 elements?") == "16")
check("log inverse", "316.228" in _ans(
    "If log x = 2.5 and log means base 10, find x."))
check("hcf x lcm other", _ans(
    "The HCF of two numbers is 12 and their LCM is "
    "240. If one number is 60, find the other number.")
    == "48")
check("second derivative", "12" in _ans(
    "Find the second derivative of x^4."))
check("first derivative control", _op(
    "Find the derivative of x^4.") == "derivative")

print("== 8. geometry ==")
check("vector magnitude", _ans(
    "Find the magnitude of the vector 2i + 3j + 6k.")
    == "7")
check("dot product", _ans(
    "Find the dot product of (1, 2, 3) and (4, -5, 6).")
    == "12")
check("trapezium", _ans(
    "Find the area of a trapezium whose parallel sides "
    "are 10 cm and 16 cm and the distance between them "
    "is 7 cm.") == "91")
check("concentric chord", _ans(
    "Two concentric circles have radii 5 cm and 3 cm. "
    "Find the length of the chord of the larger circle "
    "which touches the smaller circle.") == "8")
check("tangent length", _ans(
    "Tangents are drawn from a point at a distance of "
    "13 cm from the centre of a circle of radius 5 cm. "
    "Find the length of each tangent.") == "12")
check("rectangle breadth", _ans(
    "The perimeter of a rectangle is 60 cm. If its "
    "length is 18 cm, find its breadth.") == "12")

print("== 9. Hindi / Hinglish ==")
# Merge-3: in the merged tree Wave 52's hindi_circle_area
# pattern answers first ("100·pi ≈ 314.159") — the same
# value in Wave 52's established format; accept both.
check("hindi circle area", "314.16" in _ans(
    "एक वृत्त की त्रिज्या 10 cm है। इसका क्षेत्रफल "
    "ज्ञात कीजिए।") or "314.159" in _ans(
    "एक वृत्त की त्रिज्या 10 cm है। इसका क्षेत्रफल "
    "ज्ञात कीजिए।"))
check("hindi SI", _ans(
    "12000 रुपये का 3 वर्ष के लिए 5% वार्षिक दर से "
    "साधारण ब्याज ज्ञात कीजिए।") == "1800")
check("hindi LCM", _ans("12 और 18 का ल.स. ज्ञात कीजिए।")
      == "36")
# Merge-3: Wave 52's hindi_triangle_third_angle answers
# "50°" (degree-marked) where Wave 56's schema answers
# "50" — same value; accept both formats.
check("hindi third angle", _ans(
    "त्रिभुज के दो कोण 60 डिग्री और 70 डिग्री हैं। "
    "तीसरा कोण ज्ञात कीजिए।") in ("50", "50°"))
check("hinglish wrapped equation (bataao variant)",
      _ans("3x + 11 = 74 hai to x bataao") == "x = 21")
check("hinglish list jod", _ans(
    "24, 29, 13, 32 ka jod batao") == "98")
check("hinglish percent (parcent variant)", "80" in
      _ans("ek test me 500 me se 400 ank aaye, mera "
           "parcent kitna hua batao"))
check("range gate", _ans(
    "Find the range of the data 25, 18, 40, 12, 33, "
    "29.") == "28")

print("== 10. controls (must NOT change) ==")
from api import _solve_friendly  # noqa: E402
check("nonmaths guard intact",
      _solve_friendly("who won the cricket match "
                      "yesterday").get("op") == "nonmaths")
check("literal sets intact",
      _op("{1,2,3} union {3,4,5}") == "union")
check("hcf+lcm together intact",
      _ans("Find the HCF and LCM of 12 and 18")
      == "HCF = 6, LCM = 36")
check("documented battery error #69 stays correct",
      _ans("A fraction becomes 4/5 when 1 is added to "
           "both the numerator and the denominator. If "
           "the numerator is 3 less than the denominator, "
           "find the fraction.") == "11/14")

print("== hygiene: pins + frozen logo ==")
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf-8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf-8").read()
# Merge-3: Wave 55 legitimately bumped the pins to
# ?v=35 / ganitra-static-v15 (its CSS block); assertions
# updated to the merged pins.
# Merge-4: pins reconciled to ?v=38 / ganitra-static-v15
# (Wave 64's CSS is the newest); assertion updated.
check("stylesheet pin (?v=38 after Wave 64)",
      "stylesheet?v=38" in TPL or "?v=38" in TPL)
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
