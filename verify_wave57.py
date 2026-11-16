"""Wave 57 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (normal-question training — Suraj:
"Jab log Ganitra use karte hain toh log normal question
karte hain" and "Hinglish language par dhyan dena —
spelling mistake karte hain, Hinglish mai kuch bhi likh
dete hain, isiliye is par JYADA focus karna"):

1. solver/router.normalize_spelling — Hinglish spelling
   normalisation applied BEFORE pattern matching: a
   variant map for the commonest misspellings, phonetic
   folding rules (doubled letters, long vowels aa/ee/oo)
   that only fire when the folded form is a known word,
   and consonant-skeleton matching against the canonical
   Hinglish maths wordlist for dropped-vowel forms
   (ktna -> kitna, btao -> batao, ghnte -> ghante),
   gated on the question actually looking Hinglish and
   never applied to ordinary English words. Plus English
   typo map, OCR repairs (24O -> 240, circ1e/rad1us,
   rnaximum, broken words, no-space strings) and typed
   superscripts (x2 -> x^2 in equations).
2. normalize_hinglish: Roman-Hindi word-problem
   translations (train speed/time, aayat/tribhuj/varg/
   vritt mensuration, cuboid, SI, marks percent, ratio
   share, discount), "N ka P%" percent-of, Devanagari
   प्रतिशत percent and वर्गमूल/घनमूल roots, the number
   list AFTER "ausat batao:".
3. Devanagari solver patterns: HCF/LCM
   (solver/number_theory.py), mensuration
   (solver/geometry.py), speed-distance-time + simple
   interest (solver/applied.py).
4. fallback._is_junk recognises Devanagari letter-soup
   and short single-letter products ("C·F·H"), so Hindi
   questions can no longer be "answered" with sympy
   word-products; concept/similar layers match on the
   spelling-folded text too.
5. Probability gaps: puchh (tail), teeno (all three),
   Roman se badi/chhoti, sama sankhya (statistics);
   English both-coins events incl. verb-less asks;
   base/perpendicular Pythagoras; "length of a rectangle
   is ..." geometry; SI story form "interest for Rs N";
   anaphoric unit conversion ("a rope is 3 metres long,
   how many centimetres is that").
6. Concept keywords for typed asks: byaj, ausat, औसत,
   sambhavna, madhyika, समकोण त्रिभुज, क्रमगुणित,
   चाल दूरी, prime no, right angled triangle,
   quadratic equation, द्विघात समीकरण, ...

MEASURED (api._solve_friendly throughout):
- Normal-question battery (984 items, built for this
  wave): EXACT 314 -> 863, CONCEPT_OK 36 -> 76,
  GUIDE_OK 45 -> 45, FALLBACK 521 -> 0, WRONG 9 -> 0,
  JUNK 59 -> 0. Acceptable 395/984 -> 984/984.
- HEADLINE hinglish_spelling tag (386 items, every core
  question in 4-6 real spelling variants):
  EXACT 153 (39.6%) -> 386 (100%).
- HELD-OUT spelling set (77 items, spellings excluded
  from the battery and from every map while developing;
  only the folding RULES may catch them):
  EXACT 26 (33.8%) -> 75 (97.4%). The 2 misses are
  "parsent" (for pratishat) — its consonant skeleton
  genuinely differs; left honest.
- Fresh rewordings written after the fixes (60 items,
  new numbers + novel spellings): 60/60 acceptable.
- Textbook 515 battery: EXACT 335 -> 342, FALLBACK
  151 -> 162, WRONG 29 -> 11, ERROR 0; per-item diff
  ZERO regressions, 21 improvements.
- pytest 620 -> 703 passed / 5 skipped (83 new tests
  in test/test_wave57.py).

No template/CSS/auth changes; pins untouched; pi
convention untouched; the one-favourite password
reset untouched (owner's decision, 15 Nov).

Deliberately NOT taken: "parsent"-type spellings whose
skeleton differs from every canonical word; English
"square root of N" word forms (pre-existing parse gap,
unchanged); Ganitra major-project pack (owner: plan
only for now).
"""
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
from solver.router import normalize_spelling  # noqa: E402


def _ans(q):
    return str(_solve_friendly(q).get("answer", ""))


def _kind(q):
    return str(_solve_friendly(q).get("fallback_kind", ""))


def _exact(q, want):
    res = _solve_friendly(q)
    return "fallback" not in res and want in str(
        res.get("answer", ""))


print("== 1. hinglish spelling: battery variants ==")
check("parcent + kitnaa", _exact("240 ka 15 parcent kitnaa hoga?", "36"))
check("jodd", _exact("15 aur 27 ka jodd kitna hoga?", "42"))
check("byaaj SI", _exact("1000 rupaye ka 5 percent ki dar se 2 saal ka byaaj kitna hoga", "100"))
check("khetrafal + lambaai", _exact("ek aayat ka khetrafal nikaalo jiska lambaai 12 cm aur chaudai 5 cm hai", "60"))
check("tren + ghante", _exact("ek tren 360 km 4 ghante me jati hai, speed kitni hai?", "90"))

print("== 2. hinglish spelling: held-out forms (rules only) ==")
check("ktna + btao", _exact("250 ka 12% ktna hoga btao", "30"))
check("ghnte + duree", _exact("ek train 360 km ki duree 4 ghnte me tay karti hai, speed kitnaaa hoga btao", "90"))
check("osat + snkhya", _exact("in snkhya ka osat btao: 3, 6, 9, 12", "7.5"))
# Wave 99: trijya 7 -> pi = 22/7 -> 154 (was 153.938).
check("britt (b/v fold)", _exact("ek britt ka kshetrafal btao jiska trijyaa 7 cm hai", "154"))
check("chetrafal (ch/ksh fold)", _exact("ek vritt ka chetrafal btao jiska trijya 7 cm hai", "154"))
check("uchai (nasal fold)", _exact("ek tribhuj ka kshetrafal batao jiska aadhar 10 cm aur uchai 6 cm hai", "30"))

print("== 3. fold safety ==")
check("clean English untouched", normalize_spelling("find the area of a circle with radius 7") == "find the area of a circle with radius 7")
check("clean equation untouched", normalize_spelling("solve x^2 - 5x + 6 = 0") == "solve x^2 - 5x + 6 = 0")
check("paas stays paas", "pasa" not in normalize_spelling("mere paas 50 rupaye hai"))
check("paise stays paise", "paise" in normalize_spelling("50 paise ka sawal"))

print("== 4. Devanagari ==")
check("HCF hindi", _exact("12 और 18 का महत्तम समापवर्तक बताओ", "6"))
check("LCM hindi", _exact("12 और 15 का लघुत्तम समापवर्त्य निकालो", "60"))
check("devanagari digits HCF", _exact("१२ और १८ का महत्तम समापवर्तक क्या होगा?", "6"))
check("circle area hindi", _exact("एक वृत्त की त्रिज्या 7 सेमी है, उसका क्षेत्रफल निकालो", "154"))
check("train speed hindi", _exact("एक रेलगाड़ी 360 किलोमीटर की दूरी 4 घंटे में तय करती है, उसकी चाल कितनी है?", "90"))
check("SI hindi", _exact("1000 रुपये पर 5% वार्षिक ब्याज की दर से 2 वर्ष का साधारण ब्याज कितना होगा?", "100"))
check("percent hindi", _exact("240 का 15 प्रतिशत कितना होगा?", "36"))
check("vargmul hindi", _exact("144 का वर्गमूल क्या होगा?", "12"))
check("pythagoras concept hindi", _kind("पाइथागोरस प्रमेय क्या होती है?") == "concept")
check("ausat concept hindi", _kind("औसत कैसे निकालते हैं?") == "concept")

print("== 5. Roman-Hindi word problems ==")
check("train time jana hai", _exact("ek train ko 360 km jana hai, uski speed 60 km/h hai, kitna time lagega?", "6"))
check("train time kitne ghante", _exact("train 80 km/h ki speed se 240 km kitne ghante me jayegi?", "3"))
check("marks percent", _exact("500 me se 350 number mile, percent kitna hua?", "70"))
check("ratio share", _exact("1000 rupaye ko 2:3 ke anupat me banto, pehle wale ko kitna milega?", "400"))
check("discount", _exact("2000 rupaye wali cheez par 10% discount hai, kitne me milegi?", "1800"))
check("ausat list after", _exact("in sankhyaon ka ausat batao: 3, 6, 9, 12", "7.5"))

print("== 6. probability gaps ==")
check("puchh at least one", _exact("do sikke uchale jaye to kam se kam ek puchh aane ki sambhavna kya hai?", "0.75"))
check("teeno chit", _exact("teen sikke uchale jaye to teeno chit aane ki sambhavna kya hai?", "0.125"))
check("se badi sankhya", _exact("ek pasa feko to 3 se badi sankhya aane ki probability kya hai?", "0.5"))
check("sama sankhya", _exact("ek pasa feko to sama sankhya aane ki probability kya hai?", "0.5"))
check("both coins no verb", _exact("probability that both coins show heads", "0.25"))

print("== 7. typo / OCR English ==")
check("rectangel + lenght + breath", _exact("find the area of a rectangel with lenght 12 and breath 5", "60"))
check("24O percent", _exact("what is 15% of 24O", "36"))
check("rad1us", _exact("find the area of a circle with rad1us 7 cm", "154"))
check("nospace string", _exact("findtheareaofasquarewithside9cm", "81"))
check("rect angle join", _exact("area of a rect angle with length 12 and breadth 5", "60"))
check("intrest story form", _exact("calculate simple intrest for 2000 rupees at 6 percent for 3 year", "360"))
check("pythagorus theorm", _exact("using pythagorus theorm find the hypotenuse if base is 3 and perpendicular is 4", "5"))
check("rnetres anaphoric units", _exact("a rope is 3 rnetres long how many centimetres is that", "300"))
check("x2 quadratic both roots", "2" in _ans("ye wala samjha do: x2 - 5x + 6 = 0") and "3" in _ans("ye wala samjha do: x2 - 5x + 6 = 0"))

print("== 8. concept asks & honesty ==")
check("what is HCF -> concept", _kind("what is HCF") == "concept")
check("AP kya hoti hai -> concept", _kind("AP kya hoti hai?") == "concept")
check("byaj kaise -> concept", _kind("byaj kaise nikalte hai?") == "concept")
check("unparseable -> one-line not-found (Wave 67)", _kind("ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 rupaye ki kharidi kitne bache") == "not_found")

print(f"\nWave 57 verify: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
