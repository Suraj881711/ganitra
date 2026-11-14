"""Wave 33 verification (14 Nov 2026).

WHAT THIS WAVE ADDED (all solver-side):
1. Hindi / Hinglish probability — solver/statistics.py
   _probability_hindi: coins (at-most / at-least / exactly /
   both / none, Devanagari + Roman-Hinglish), dice events
   and sums, cards, balls; router statistics tokens and the
   _probability gate widened (प्रायिकता / संभावना /
   sambhavna / experiment tokens / "chance"). Before: every
   Hindi probability question fell to arithmetic
   letter-soup or the guide fallback.
2. LP from raw inequalities — solver/applied.py
   _lp_inequalities + a router pre-check gate: objective +
   constraints -> feasible corners -> exact rational
   max/min, honest "unbounded" when the region runs away.
3. Ogive median — statistics._ogive_median + router ogive
   gate: "less than / more than B: cf" pairs -> classes ->
   grouped-median formula (was: raw-list median 22.5/18.5).
4. Probe extras (68-question EN/HI battery, Class 9-12:
   13 exact / 28 wrong / 27 fallback BEFORE -> 68/68 exact
   AFTER): English die events, doublet, empirical
   probability, defective items, 53-weekday years, "not a
   red ball" complement, specific cards (king of hearts,
   black queen), mean-excluded, frequency-table mean with
   unknown f, nth term from S_n, collinear find-k,
   concentric-ring area, rectangle-diagonal word form,
   equation lead-in / method stripping (+ domain
   restriction tails), sin theta -> tan theta, Hindi
   descriptive statistics (माध्य / माध्यक / बहुलक / औसत).

No template/CSS/JS changed: the ?v=29 / ganitra-static-v6
pins deliberately stay put and this script asserts they did
NOT move, and that the frozen logo files are untouched.

Deliberately NOT taken: the pi convention (owner's
undecided call — solver keeps true pi), proof/verify
identity asks, free-form multi-condition word problems,
Hindi AP phrasing, drawing the ogive itself (median only),
single-GM hijack.
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

TRAIN_HINDI = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। यदि यह "
    "चाल 5 km/h अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय "
    "लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
COINS = ("Two coins are tossed simultaneously. What is the "
         "probability of getting at most one head?")


def _op(q):
    return str(solve_question(q).get("op", ""))


def _ans(q):
    return str(solve_question(q).get("answer", ""))


def _fans(q):
    return str(_solve_friendly(q).get("answer", ""))


def _exact(q):
    res = _solve_friendly(q)
    return "fallback" not in res


# --- 1. Hindi probability: coins ----------------------------------
print("== Hindi probability: coins")
for q, want in (
    ("दो सिक्के एक साथ उछाले जाते हैं। कम से कम एक चित आने की "
     "प्रायिकता ज्ञात कीजिए।", "3/4"),
    ("दो सिक्के उछाले जाते हैं। अधिक से अधिक एक चित आने की "
     "प्रायिकता क्या है?", "3/4"),
    ("तीन सिक्के एक साथ उछाले जाते हैं। ठीक दो चित आने की "
     "प्रायिकता ज्ञात कीजिए।", "3/8"),
    ("एक सिक्का उछाला जाता है। चित आने की प्रायिकता क्या है?",
     "1/2"),
    ("एक सिक्का उछाला जाता है। पट आने की प्रायिकता ज्ञात "
     "कीजिए।", "1/2"),
    ("दो सिक्के उछाले जाते हैं। कोई चित न आने की प्रायिकता "
     "ज्ञात कीजिए।", "1/4"),
    ("दो सिक्के उछाले जाते हैं। दोनों पट आने की प्रायिकता क्या "
     "है?", "1/4"),
):
    check(f"HI coins -> {want}", _exact(q)
          and _fans(q).startswith(want), _fans(q))

# --- 2. Hindi probability: dice / cards / balls --------------------
print("== Hindi probability: dice, cards, balls")
for q, want in (
    ("एक पासा फेंका जाता है। एक सम संख्या आने की प्रायिकता "
     "ज्ञात कीजिए।", "1/2"),
    ("एक पासा फेंका जाता है। एक अभाज्य संख्या आने की प्रायिकता "
     "क्या है?", "1/2"),
    ("एक पासा फेंका जाता है। संख्या 5 आने की प्रायिकता ज्ञात "
     "कीजिए।", "1/6"),
    ("एक पासा फेंका जाता है। 4 से बड़ी संख्या आने की प्रायिकता "
     "क्या है?", "1/3"),
    ("दो पासे एक साथ फेंके जाते हैं। अंकों का योग 7 आने की "
     "प्रायिकता ज्ञात कीजिए।", "1/6"),
    ("52 पत्तों की एक गड्डी में से एक पत्ता निकाला जाता है। "
     "इक्का आने की प्रायिकता ज्ञात कीजिए।", "1/13"),
    ("ताश के 52 पत्तों में से एक पत्ता निकाला जाता है। बादशाह "
     "आने की प्रायिकता क्या है?", "1/13"),
    ("52 पत्तों की गड्डी से एक पत्ता निकाला जाता है। लाल "
     "पत्ता आने की प्रायिकता ज्ञात कीजिए।", "1/2"),
    ("52 पत्तों की गड्डी से एक पत्ता निकाला जाता है। हुकुम का "
     "पत्ता आने की प्रायिकता क्या है?", "1/4"),
    ("एक थैले में 5 लाल और 3 नीली गेंदें हैं। एक गेंद "
     "यादृच्छिक रूप से निकाली जाती है। प्रायिकता ज्ञात कीजिए "
     "कि गेंद लाल है।", "5/8"),
    ("एक थैले में 4 लाल, 5 हरी और 6 सफेद गेंदें हैं। एक गेंद "
     "निकाली जाती है। हरी गेंद आने की प्रायिकता क्या है?",
     "1/3"),
):
    check(f"HI prob -> {want}", _exact(q)
          and _fans(q).startswith(want), _fans(q))

# --- 3. Hinglish probability ---------------------------------------
print("== Hinglish probability")
for q, want in (
    ("Do sikke ek saath uchhale jate hain. Kam se kam ek "
     "chit aane ki probability kya hai?", "3/4"),
    ("Ek sikka uchhala jata hai. Pat aane ki probability "
     "kya hai?", "1/2"),
    ("Ek pasa phenka jata hai. Sam sankhya aane ki "
     "probability batao.", "1/2"),
    ("Ek pasa phenka jata hai. Visham sankhya aane ki "
     "sambhavna kya hai?", "1/2"),
):
    check(f"HING prob -> {want}", _exact(q)
          and _fans(q).startswith(want), _fans(q))

# --- 4. LP from raw inequalities ------------------------------------
print("== LP from raw inequalities")
check("LP op", _op("Maximise Z = 3x + 4y subject to x + y "
                   "≤ 4, x ≥ 0, y ≥ 0.") == "lp_maximise")
for q, want in (
    ("Maximise Z = 3x + 4y subject to x + y ≤ 4, x ≥ 0, "
     "y ≥ 0.", "Maximum Z = 16 at (0, 4)"),
    ("Maximise Z = 5x + 3y subject to 3x + 5y ≤ 15, "
     "5x + 2y ≤ 10, x ≥ 0, y ≥ 0.",
     "Maximum Z = 235/19 at (20/19, 45/19)"),
    ("Minimise Z = 3x + 5y subject to x + 3y ≥ 3, x + y ≥ 2, "
     "x ≥ 0, y ≥ 0.", "Minimum Z = 7 at (3/2, 1/2)"),
    ("Maximise Z = x + 2y subject to 2x + y ≤ 4, x + y ≤ 3, "
     "x, y ≥ 0.", "Maximum Z = 6 at (0, 3)"),
):
    check(f"LP -> {want}", _exact(q) and _fans(q) == want,
          _fans(q))

# --- 5. Ogive median --------------------------------------------------
print("== Ogive median")
check("ogive op", _op("From the less than ogive, find the "
                      "median: less than 10: 5, less than "
                      "20: 13, less than 30: 25, less than "
                      "40: 30.") == "ogive_median")
check("ogive less-than", _fans(
    "Convert the data into a less than type cumulative "
    "frequency distribution and find the median from the "
    "ogive: less than 10: 5, less than 20: 13, less than "
    "30: 25, less than 40: 30.") == "21.6667")
check("ogive more-than", _fans(
    "From the more than ogive of the data, find the "
    "median: more than 0: 30, more than 10: 25, more than "
    "20: 17, more than 30: 5.") == "21.6667")

# --- 6. English probability extras ------------------------------------
print("== English probability extras")
for q, want in (
    ("A die is thrown once. Find the probability of getting "
     "an even number.", "1/2"),
    ("A die is thrown once. Find the probability of getting "
     "a prime number.", "1/2"),
    ("A die is thrown once. Find the probability of getting "
     "a number greater than 4.", "1/3"),
    ("A die is thrown once. Find the probability of getting "
     "a number less than 3.", "1/3"),
    ("Two dice are thrown together. Find the probability "
     "of getting a doublet.", "1/6"),
    ("A coin is tossed 1000 times. Head appears 450 times. "
     "Find the probability of getting a head.", "9/20"),
    ("A die is thrown 100 times and the outcome 6 appears "
     "20 times. Find the probability of getting a 6.", "1/5"),
    ("A lot of 20 bulbs contains 4 defective ones. One bulb "
     "is drawn at random. What is the probability that it "
     "is not defective?", "4/5"),
    ("Find the probability that a leap year has 53 "
     "Sundays.", "2/7"),
    ("Find the probability that a non-leap year has 53 "
     "Mondays.", "1/7"),
    ("A bag contains 5 red balls and 3 black balls. A ball "
     "is drawn at random. What is the probability that the "
     "ball drawn is not a red ball?", "3/8"),
    ("One card is drawn from a well-shuffled deck of 52 "
     "cards. Find the probability of getting a king of "
     "hearts.", "1/52"),
    ("A card is drawn from a pack of 52 cards. Find the "
     "probability of getting a black queen.", "1/26"),
    ("One card is drawn from a deck of 52 cards. Find the "
     "probability of getting a face card.", "3/13"),
):
    check(f"EN prob -> {want}", _exact(q)
          and _fans(q).startswith(want), _fans(q))

# --- 7. Statistics / algebra / geometry extras -------------------------
print("== Probe extras")
check("mean excluded", _fans(
    "The mean of 6 numbers is 15. If one number is "
    "excluded, the mean of the remaining numbers is 14. "
    "Find the excluded number.") == "20")
check("freq mean unknown", _fans(
    "If the mean of the following data is 30, find the "
    "value of p: x: 10, 20, 30, 40, 50 and f: 3, 5, 4, p, "
    "3.") == "p = 5")
check("nth term from S_n", "n + 2" in _fans(
    "The sum of the first n terms of an AP is 3n^2 + 5n. "
    "Find the nth term of the AP."))
check("collinear find k", _fans(
    "Find the value of k for which the points (2, 3), "
    "(4, k) and (6, -3) are collinear.") == "k = 0")
check("ring area", _fans(
    "Find the area between two concentric circles of radii "
    "7 cm and 14 cm.").startswith("461.81"))
_rd = _fans("The diagonal of a rectangle is 60 m more than "
            "the shorter side and the longer side is 30 m "
            "more than the shorter side. Find the sides of "
            "the rectangle.")
check("rectangle diagonal", "90" in _rd and "120" in _rd, _rd)
_q1 = _fans("Solve the quadratic equation 2x^2 - 7x + 3 = 0.")
check("solve-the-equation lead-in",
      "3" in _q1 and "1/2" in _q1, _q1)
_q2 = _fans("Find the roots of 1/(x+4) - 1/(x-7) = 11/30, "
            "x not equal to -4 and 7.")
check("roots-of rational + restriction",
      "x = 1" in _q2 and "x = 2" in _q2, _q2)
check("sin theta -> tan theta", _fans(
    "If sin theta = 3/5, find the value of tan theta."
    ) == "tan θ = 3/4")
check("HI mean", _fans("संख्याओं 5, 7, 9, 11, 13 का माध्य "
                       "ज्ञात कीजिए।") == "9")
check("HI median", _fans("3, 5, 7, 2, 8 का माध्यक ज्ञात "
                         "कीजिए।") == "5")
check("HI mode", _fans("2, 4, 4, 6, 4 का बहुलक ज्ञात कीजिए।"
                       ) == "4")
check("HI average", _fans("4, 8, 15, 16, 23, 42 का औसत "
                          "ज्ञात कीजिए।") == "18")

# --- 8. Regression guards ----------------------------------------------
print("== Regression guards")
check("Wave 30 Hindi train", _fans(TRAIN_HINDI) == "40 km/h",
      _fans(TRAIN_HINDI))
check("Wave 31 coins at most", _fans(COINS).startswith("3/4"),
      _fans(COINS))
check("Wave 32 grouped median", _fans(
    "Find the median of the data with class intervals "
    "0-10, 10-20, 20-30, 30-40 and frequencies 5, 8, 12, "
    "5.") == "21.6667")
check("Wave 32 LP corners", _ans(
    "Find the maximum value of Z = 5x + 4y at the corner "
    "points (0, 0), (0, 4), (3, 4) and (5, 0)."
    ).startswith("Maximum Z = 31"))
check("Wave 32 Bayes bags", _fans(
    "Bag A contains 3 red balls and 2 black balls. Bag B "
    "contains 2 red balls and 3 black balls. A bag is "
    "chosen at random and a ball is drawn from it, which "
    "is found to be red. Find the probability that the "
    "ball was drawn from bag A.").startswith("3/5"))
check("Wave 32 depression", "103.92" in _fans(
    "From the top of a 60 m high building, the angle of "
    "depression of a car on the ground is 30 degrees. "
    "Find the distance of the car from the foot of the "
    "building."))

# --- 9. Delivery pins + frozen logo (solver-only wave) -----------------
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf8").read()
check("stylesheet pin deliberately unchanged (?v=29)",
      "stylesheet?v=29" in TPL or 'stylesheet")}?v=29' in TPL
      or "?v=29" in TPL)
check("service-worker cache deliberately unchanged (v6)",
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
