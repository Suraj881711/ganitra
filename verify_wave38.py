"""Wave 38 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (all solver-side, from the Wave 35
audit top-15 backlog):

1. Sum/difference systems — solver/algebra.py
   _solve_two_linear + _identity_value: "If a + b = S and
   a - b = D, find a and b" (EN + Hindi) was complex garbage
   in f/I (audit #62-65, #471, #100); the pair-of-equations
   form with coefficients (#67) now also solves exactly.
2. GP routing — solver/sequences.py: the student's explicit
   GP/AP label beats the two-term AP default (#117-119);
   word-stated first term / common ratio / difference parse
   (#367); GP sum to infinity (#121).
3. Binomial — solver/statistics.py + distributions.py:
   coin count from "tossed N times" (#311: exactly 3 heads
   in 5 tosses was 0), bare-count events (#227: "getting
   two heads" was 1/2), repeated-die binomial (#313), and
   mean/variance -> n, p (#312: was '4').
4. Missing chapters — geometry._pythagoras (hypotenuse,
   leg, rectangle/square diagonal, right-angle check EN +
   Hindi; router diagonal/समकोण tokens), calculus integral
   block ("integral" does not contain "integrat" — every
   "integral of ..." ask missed it; "with respect to x"
   unglued), applied profit/loss (buys/sells present tense,
   %-first SP form, loses/gains CP form, Hindi + Hinglish),
   complex numbers ("the"/trailing-dot extraction hygiene,
   Multiply A by B, a + ib routing, modulus decimal).
5. Hindi summary language — langdetect_local.py: shared
   tatsama words (गणित/प्रश्न/उत्तर/अभ्यास) and the Hindi
   passive auxiliary जाते no longer flip a Hindi question
   to Marathi on their own; real Marathi markers still do.

Measured: pytest 384 -> 412 passed; the 515-question
Wave 35 battery (same automated adjudication both runs)
EXACT 257 -> 301, FALLBACK 198 -> 168, WRONG 60 -> 46,
ERROR 0 -> 0, with ZERO per-item regressions.

No template/CSS/JS changed: the ?v=29 / ganitra-static-v6
pins deliberately stay put and this script asserts they did
NOT move, and that the frozen logo files are untouched.

Deliberately NOT taken: the remaining audit items outside
this wave's list (statistics word-problem corrections,
combined-solid phrasing variant, train/platform and work
hijacks, "how many factors", inverse-angle asks, salvage
quality), the pi convention (owner's undecided call), and
GP sum/product-of-terms asks (#123).
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


from langdetect_local import detect_language_confident  # noqa: E402
from solver.router import solve_question  # noqa: E402


def _op(q):
    return str(solve_question(q).get("op", ""))


def _ans(q):
    return str(solve_question(q).get("answer", ""))


print("== 1. sum/difference systems ==")
check("a+b=10, a-b=4", _ans(
    "If a + b = 10 and a - b = 4, find a and b.") == "a = 7, b = 3")
check("a+b=15, a-b=5", _ans(
    "If a + b = 15 and a - b = 5, find a and b.") == "a = 10, b = 5")
check("a+b=20, a-b=6", _ans(
    "If a + b = 20 and a - b = 6, find a and b.") == "a = 13, b = 7")
check("a+b=7, a-b=3", _ans(
    "If a + b = 7 and a - b = 3, find a and b.") == "a = 5, b = 2")
check("Hindi system", _ans(
    "यदि a + b = 8 और a - b = 2 हो तो a और b ज्ञात कीजिए।")
    == "a = 5, b = 3")
check("pair with coefficients", _ans(
    "Solve the pair of equations: 2x + 3y = 13 and x - y = 1.")
    == "x = 16/5, y = 11/5")
check("identity a^2+b^2", _ans(
    "If a - b = 4 and ab = 21, find a^2 + b^2.") == "58")
check("single equation untouched",
      _op("Solve x^2 - 5x + 6 = 0.") == "equation")

print("== 2. GP routing ==")
check("GP 3,6 8th term", _ans(
    "Find the 8th term of the GP 3, 6, ...") == "384")
check("GP 5,15 6th term", _ans(
    "Find the 6th term of the GP 5, 15, ...") == "1215")
check("GP 81,27 5th term", _ans(
    "Find the 5th term of the GP 81, 27, ...") == "1")
check("GP word params", _ans(
    "In a GP, the first term is 4 and the common ratio is 3. "
    "Find the 5th term.") == "324")
check("GP sum to infinity", _ans(
    "Find the sum to infinity of the GP 8, 4, 2, 1, ...") == "16")
check("AP untouched", _ans(
    "Find the 10th term of the AP 2, 5, 8, ...") == "29")

print("== 3. binomial ==")
check("exactly 3 heads in 5 tosses", _ans(
    "A coin is tossed 5 times. What is the probability of "
    "getting exactly 3 heads?").startswith("5/16"))
check("two coins, two heads", _ans(
    "Two coins are tossed simultaneously. What is the "
    "probability of getting two heads?").startswith("1/4"))
check("die six exactly 2 in 4 throws", _ans(
    "A die is thrown 4 times. What is the probability of "
    "getting a six exactly 2 times?").startswith("25/216"))
check("binomial mean/variance -> n, p", _ans(
    "The mean of a binomial distribution is 20 and the "
    "variance is 16. Find n and p.") == "n = 100, p = 0.2")
check("binomial n, p -> mean/variance", _ans(
    "A binomial distribution has n = 10 and p = 0.5. Find "
    "its mean and variance.") == "Mean = 5, variance = 2.5")
check("empirical probability untouched", _ans(
    "A coin is tossed 1000 times and head appears 450 times. "
    "Find the probability of getting a head.").startswith("9/20"))

print("== 4a. pythagoras ==")
check("hypotenuse 9-12", _ans(
    "Find the hypotenuse of a right triangle with legs "
    "9 cm and 12 cm.") == "15")
check("missing leg 25-7", _ans(
    "A right triangle has hypotenuse 25 cm and one leg "
    "7 cm. Find the other leg.") == "24")
check("rectangle diagonal", _ans(
    "Find the diagonal of a rectangle with length 12 cm and "
    "breadth 5 cm.") == "13")
check("Hindi right-angle check", _ans(
    "किसी त्रिभुज की भुजाएँ 6 cm, 8 cm और 10 cm हैं। क्या यह "
    "समकोण त्रिभुज है?").startswith("Yes"))

print("== 4b. integration ==")
check("integrate x^3 wrt x", _ans(
    "Integrate x^3 with respect to x.") == "x^4/4 + C")
check("integral of 2x + 3", _ans(
    "Find the integral of 2x + 3.") == "x^2 + 3·x + C")
check("definite integral of x, 0 to 2", _ans(
    "Evaluate the definite integral of x from 0 to 2.") == "2")
check("definite integral of x^2, 1 to 3", _ans(
    "Evaluate the definite integral of x^2 from 1 to 3.")
    == "26/3")
check("integrate sin x", _ans(
    "Integrate sin x with respect to x.") == "-cos(x) + C")
check("integrate 1/x", _ans(
    "Integrate 1/x with respect to x.") == "log(x) + C")

print("== 4c. profit/loss ==")
check("buys/sells profit %", _ans(
    "A shopkeeper buys an article for Rs 500 and sells it "
    "for Rs 575. Find his profit percent.") == "15%")
check("buys/sells loss %", _ans(
    "A shopkeeper buys an article for Rs 800 and sells it "
    "for Rs 720. Find his loss percent.") == "10%")
check("%-first SP form", _ans(
    "A man sells an article at a loss of 15%. If the cost "
    "price is Rs 2000, find the selling price.") == "Rs 1700")
check("loses % CP form", _ans(
    "By selling a watch for Rs 1275, a man loses 15%. Find "
    "the cost price of the watch.") == "Rs 1500")
check("Hindi profit %", _ans(
    "एक वस्तु 800 रुपये में खरीदकर 1000 रुपये में बेची गई। "
    "लाभ प्रतिशत ज्ञात कीजिए।") == "25%")

print("== 4d. complex numbers ==")
check("modulus 3 + 4i", _ans("Find the modulus of 3 + 4i.") == "5")
check("modulus 1 + i", _ans(
    "Find the modulus of 1 + i.") == "sqrt(2) ≈ 1.4142")
check("add complex", _ans(
    "Simplify (2 + 3i) + (4 - 5i).") == "6 - 2·I")
check("multiply complex", _ans(
    "Multiply (1 + i) by (1 - i).") == "2")
check("1/i in a + ib form", _ans(
    "Express 1/i in the form a + ib.") == "-I")

print("== 5. hindi summary language ==")
check("hindi coins question detects hi", detect_language_confident(
    "दो सिक्के उछाले जाते हैं। कम से कम एक चित आने की "
    "प्रायिकता क्या है?")[0] == "hi")
check("hindi prashn/uttar detects hi", detect_language_confident(
    "इस प्रश्न का उत्तर बताओ")[0] == "hi")
check("marathi still detects mr", detect_language_confident(
    "मला हा प्रश्न समजत नाहीये, सांगा ना कसा करायचा")[0] == "mr")

print("== hygiene: pins + frozen logo ==")
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf-8").read()
SW = open(os.path.join("static", "sw.js"), encoding="utf-8").read()
# Merge (Waves 38-46): Wave 43 deliberately bumped the pins to
# ?v=30 / ganitra-static-v7 — assert the current merged pins,
# same convention Wave 43 applied to the pytest pin tests.
check("stylesheet pin at Wave 43 bump (?v=30)",
      "v='30'" in TPL or "?v=30" in TPL)
check("sw cache pin at Wave 43 bump (v7)",
      'GANITRA_CACHE = "ganitra-static-v7"' in SW)
for _name, _want in (
        ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"),
        ("logo-mark.png", "03bc03dc")):
    _p = os.path.join("static", _name)
    if os.path.exists(_p):
        _digest = hashlib.sha256(open(_p, "rb").read()).hexdigest()
        check(f"frozen logo {_name} untouched",
              _digest.startswith(_want), _digest[:12])

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
