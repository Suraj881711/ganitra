"""Wave 53 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (alternates only — solver/methods.py
+ i18n labels; NO primary answer or step changed, no
template/CSS/JS touched): MORE SOLUTION METHODS per answer,
Suraj's direct pick ("Har sawal ke jawab me aur tarike
(methods) dikhao"). The answer card's More (•••) menu gains
a genuine second (and where natural, third) method for
~20 more question families:

1. Pairs of linear equations — substitution / elimination
   (with NCERT-style fraction clearing) / cross-multipli-
   cation, whichever the primary did not itself work.
2. AP sum — Gauss pairing; GP sum — adding the terms.
3. Compound interest — year by year (id yearly_breakup).
4. Profit/loss percent and reverse profit/loss — unitary;
   discount — direct percent; successive discounts — the
   single equivalent discount D = d1 + d2 - d1*d2/100.
5. Marks percent and "what percent" — unitary / fraction;
   unitary cost — proportion; ratio division — fraction
   of the whole.
6. LCM — the division method alongside the HCF relation
   (2 and 3 numbers); HCF+LCM — Euclid + a*b = HCF*LCM.
7. Median — the position formula (odd and even n).
8. Probability — the complement rule for die events, one
   and two coins, coloured balls and the standard card
   facts (face card / suits / red-black / ranks).
9. Trig ratio-from-ratio — the identity route (sin^2+cos^2
   = 1, sec^2 = 1 + tan^2); standard trig values derived
   from the two standard triangles (incl. the "degrees"
   wording and ^2 forms).
10. Mensuration decompositions — circle area and circum-
    ference via the diameter; rectangle/square area by
    counting unit squares; perimeter by adding the sides;
    cuboid/cube volume by layers; cylinder volume as base
    area x height; cone volume as one-third of the
    cylinder.
11. Reach fixes for existing alternates: grouped BODMAS
    now tolerates an "Evaluate/Calculate ..." lead-in;
    AP pairing reads the verbal "first term is ..., common
    difference is ..." form.

Every alternate is independently computed and ships only
when its final answer EQUALS the primary answer (the
_answer_check / value gates) — a method that would
contradict the primary is withheld, never shown.

Measured: pytest 620 -> 661 passed / 5 skipped (41 new
tests in test/test_wave53_fixes.py, each asserting the
new method's answer equals the primary's). The 515-
question Wave 35 battery is IDENTICAL before/after —
335 EXACT / 151 FALLBACK / 29 WRONG / 0 ERROR with ZERO
per-item diffs in verdict or primary answer; only the
alternates field grew: battery questions carrying at
least one alternate 52 -> 121, total alternates served
97 -> 175. A 151-question representative pattern suite
across all families (varied numbers and phrasings) is
covered 148/151.

Deliberately NOT taken: the 3 pattern-suite misses are
(i) the AP nth-term listing cap at n <= 12 (Wave 13
design — a 15-term listing is unwieldy), (ii) "Divide
1500 rupees in the ratio 1 : 2", whose primary is the
ratio-echo op rather than ratio_divide, and (iii) die
"at least 5", whose PRIMARY answer is itself wrong
(1/6) — the correct complement (1/3) is withheld by the
answer-equality rule rather than shown contradicting
the card; fixing that primary belongs to a solver wave,
not a methods wave. The die "not getting a 6" primary
has the same limitation and is likewise withheld.
Hindi/Hinglish primaries that route to fallback/concept
answers carry no verifiable answer, so no alternate can
attach (same rule as before this wave).
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


from solver.methods import alternate_methods  # noqa: E402
from solver.router import solve_question  # noqa: E402


def _check(q, want_id):
    primary = solve_question(q)
    ms = {m["id"]: m for m in alternate_methods(q, primary)}
    return want_id in ms and \
        ms[want_id]["answer"] == primary.get("answer")


print("== 1. systems ==")
check("generic primary -> substitution",
      _check("Solve for x and y: 2x + 3y = 11, "
             "2x - 4y = -24", "substitution"))
check("generic primary -> cross-multiplication",
      _check("Solve for x and y: 2x + 3y = 11, "
             "2x - 4y = -24", "cross_multiplication"))
check("substitution primary -> elimination (fractions "
      "cleared)",
      _check("Solve: x/2 + y/3 = 4, x - y = 2",
             "elimination"))

print("== 2. sequences ==")
check("AP sum -> pairing",
      _check("Find the sum of first 20 terms of the AP: "
             "3, 7, 11, 15, ...", "pairing"))
check("AP sum (verbal a/d) -> pairing",
      _check("Find the sum of the first 12 terms of an AP "
             "whose first term is 5 and common difference "
             "is 3", "pairing"))
check("GP sum -> term addition",
      _check("Find the sum of the first 5 terms of the "
             "GP: 3, 6, 12, 24, ...", "term_addition"))

print("== 3. interest and applied ==")
check("CI -> year by year",
      _check("Find the compound interest on Rs 8000 at 5% "
             "per annum for 2 years", "yearly_breakup"))
check("profit percent -> unitary",
      _check("Find the profit percent if CP is Rs 400 "
             "and SP is Rs 460", "unitary"))
check("reverse profit -> unitary",
      _check("A book was sold for Rs 270 with a profit "
             "of 8%. Find its cost price", "unitary"))
check("successive discounts -> equivalent discount",
      _check("The marked price of an article is Rs 3000. "
             "Two successive discounts of 15% and 10% are "
             "offered.", "equivalent_discount"))
check("marks percent -> unitary",
      _check("Rahul scored 45 marks out of 60. Find his "
             "percentage of marks.", "unitary"))
check("what percent -> fraction",
      _check("What percent of 250 is 50?", "fraction"))
check("unitary cost -> proportion",
      _check("If the cost of 5 pens is Rs 100, find the "
             "cost of 8 pens.", "proportion"))
check("ratio divide -> fraction of the whole",
      _check("Divide Rs 1200 in the ratio 2 : 3",
             "fraction_of_whole"))

print("== 4. number theory ==")
check("LCM -> division method",
      _check("Find the LCM of 15, 20 and 30",
             "division_method"))
check("HCF and LCM -> Euclid relation",
      _check("Find the HCF and LCM of 26 and 91",
             "euclid_relation"))

print("== 5. statistics ==")
check("median odd -> position formula",
      _check("Find the median of 3, 7, 5, 9, 11",
             "position_formula"))
check("median even -> position formula",
      _check("Find the median of 6, 3, 9, 5, 2, 7",
             "position_formula"))

print("== 6. probability (complement) ==")
check("die -> complement",
      _check("A die is thrown once. Find the probability "
             "of getting a number greater than 4",
             "complement"))
check("two coins -> complement",
      _check("Two coins are tossed. Find the probability "
             "of getting two heads", "complement"))
check("balls NOT -> complement",
      _check("A bag contains 4 red and 6 blue balls. "
             "What is the probability of NOT getting a "
             "red ball?", "complement"))
check("cards -> complement",
      _check("Find the probability of getting a king "
             "from a pack of 52 cards", "complement"))
_q = ("A die is thrown once. Find the probability of "
      "not getting a 6")
# Merge-3: this check originally asserted the complement is
# WITHHELD because the die primary ignored "not" (1/6).
# Wave 58 fixed that primary (5/6) — the complement now
# agrees with it and legitimately attaches.
check("complement attaches now that Wave 58 fixed the "
      "die-negation primary (was: withheld, rule c)",
      "5/6" in str(solve_question(_q).get("answer"))
      and any(m["id"] == "complement"
              for m in alternate_methods(
                  _q, solve_question(_q))))

print("== 7. trigonometry ==")
check("ratio from tan -> identity route",
      _check("If tan A = 4/3, find sin A and cos A",
             "identity"))
check("values -> standard triangles",
      _check("Evaluate cos^2 30 + sin^2 30",
             "standard_triangles"))
check("values (degrees wording) -> standard triangles",
      _check("Evaluate 2 sin^2 30 degrees + 3 cos^2 60 "
             "degrees.", "standard_triangles"))

print("== 8. mensuration ==")
check("circle area -> via diameter",
      _check("Find the area of a circle with radius "
             "7 cm", "diameter"))
check("rectangle area -> grid counting",
      _check("Find the area of a rectangle with length "
             "15 cm and breadth 8 cm", "grid_counting"))
check("perimeter -> side addition",
      _check("Find the perimeter of a square with side "
             "9 cm", "side_addition"))
check("cuboid volume -> layers",
      _check("Find the volume of a cuboid with length "
             "10 cm, breadth 8 cm and height 5 cm",
             "layers"))
check("cylinder volume -> base area x height",
      _check("Find the volume of a cylinder with radius "
             "7 cm and height 10 cm", "base_area"))
check("cone volume -> one-third of cylinder",
      _check("Find the volume of a cone with radius "
             "7 cm and height 10 cm", "cone_third"))

print("== 9. discount via the served pipeline ==")
from api import _solve_friendly  # noqa: E402
_q = ("Find the selling price of an article with marked "
      "price Rs 1500 and a discount of 20%")
_p = _solve_friendly(_q)
_ms = {m["id"]: m for m in alternate_methods(_q, _p)}
check("discount -> direct percent",
      "direct_percent" in _ms and
      _ms["direct_percent"]["answer"] == _p.get("answer"))

print("== 10. labels in all 6 languages ==")
import i18n  # noqa: E402
_ids = ["elimination", "substitution",
        "cross_multiplication", "pairing", "term_addition",
        "complement", "identity", "standard_triangles",
        "position_formula", "division_method",
        "euclid_relation", "diameter", "layers",
        "base_area", "cone_third", "grid_counting",
        "side_addition", "direct_percent",
        "fraction_of_whole", "equivalent_discount"]
check("all Wave 53 mm_label_ keys present x6 languages",
      all(i18n.STRINGS[lang].get(f"mm_label_{mid}")
          for lang in ("en", "hi", "bn", "mr", "ta", "te")
          for mid in _ids))

print("== hygiene: pins + frozen logo ==")
TPL = open(os.path.join("templates", "base.html"),
           encoding="utf-8").read()
SW = open(os.path.join("static", "sw.js"),
          encoding="utf-8").read()
# Merge-3: Wave 55 legitimately bumped the pins to
# ?v=35 / ganitra-static-v13; assertions updated.
check("stylesheet pin after Wave 55 (?v=35)",
      "stylesheet?v=35" in TPL or "?v=35" in TPL)
check("sw cache pin after Wave 55 (v9)",
      'GANITRA_CACHE = "ganitra-static-v13"' in SW)
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
