"""Wave 57 (Suraj, 15 Nov 2026): "Jab log Ganitra use karte
hain toh log normal question karte hain" + "Hinglish language
par dhyan dena — spelling mistake karte hain, Hinglish mai
kuch bhi likh dete hain, isiliye is par JYADA focus karna."

Normal-question training: a 984-item battery of the way
students actually type (casual Hinglish, spelling chaos,
typos, OCR noise, half-questions, concept asks, Devanagari)
plus a 77-item HELD-OUT spelling set. Fixes are GENERAL:

1. solver/router.normalize_spelling — variant map +
   phonetic folding (doubled letters, long vowels) +
   consonant-skeleton matching against the canonical
   Hinglish maths wordlist, applied BEFORE pattern
   matching. Held-out spellings (ktna, btao, ghnte, osat)
   fold by RULE, never by map entry.
2. normalize_hinglish translations for Roman-Hindi word
   problems (train SDT, aayat/tribhuj/varg/vritt mensuration,
   SI, marks %, ratio share, discount), "% of" and
   Devanagari प्रतिशत / वर्गमूल forms, list-after-ausat.
3. Devanagari patterns: HCF/LCM (number_theory), mensuration
   (geometry), SDT + SI (applied) — and fallback._is_junk now
   recognises Devanagari letter-soup, so Hindi questions can
   no longer be "answered" with sympy word-products.
4. Roman-Hindi probability gaps (puchh = tail, teeno = all
   three, Roman se badi/chhoti, sama sankhya), English
   both-coins events, base/perpendicular Pythagoras,
   "length of a rectangle is ..." geometry, SI story form
   ("interest for Rs N"), anaphoric unit conversions.
5. Concept keywords for the asks students type (byaj, ausat,
   sambhavna, समकोण त्रिभुज, औसत, क्रमगुणित, prime no, ...).

Measured: normal battery EXACT 314 -> 863, acceptable
984/984; hinglish_spelling 153/386 -> 386/386; held-out
26/77 -> 75/77; textbook 515: 335 -> 342 EXACT, ZERO
per-item regressions; these tests pin the behaviour.
"""
import pytest

from api import _solve_friendly
from solver.router import normalize_spelling, solve_question


def _exact(question):
    """The full user path must return the student's OWN answer:
    a real solver result, never a fallback layer."""
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


def _ans(question):
    return str(_exact(question).get("answer", ""))


# --- 1. Hinglish spelling folding (the headline) --------------

@pytest.mark.parametrize("question,want", [
    ("240 ka 15 pratishat kitna hoga?", "36"),
    ("240 ka 15 parcent kitnaa hoga?", "36"),
    ("15 aur 27 ka jodd kitna hoga?", "42"),
    ("50 aur 18 ka ghaata btaao", "32"),
    ("17 ko 4 se gunna karo, kitna hoga?", "68"),
    ("60 ko 5 se bhaag do, kitna hoga?", "12"),
    ("mujhe 20 aur 30 ka HCF chaiye", "10"),
    ("ek tren 360 km 4 ghante me jati hai, speed kitni hai?", "90"),
    ("ek aayat ka khetrafal nikaalo jiska lambaai 12 cm aur "
     "chaudai 5 cm hai", "60"),
    ("varg ka parimaap kitna hoga agar side 9 cm hai", "36"),
    ("1000 rupaye ka 5 percent ki dar se 2 saal ka byaaj "
     "kitna hoga", "100"),
    ("in sankhyaa ka ausat batao: 5, 10, 15", "10"),
])
def test_hinglish_spelling_variants_solve(question, want):
    assert want in _ans(question)


@pytest.mark.parametrize("question,want", [
    # Held-out spellings: NO map entries exist for these —
    # the folding RULES (skeleton / vowel / doubling) catch them.
    ("250 ka 12% ktna hoga btao", "30"),
    ("ek train 360 km ki duree 4 ghnte me tay karti hai, "
     "speed kitnaaa hoga btao", "90"),
    ("in snkhya ka osat btao: 3, 6, 9, 12", "7.5"),
    # Wave 99: trijyaa 7 -> pi = 22/7 -> 154 (was 153.938).
    ("ek britt ka kshetrafal btao jiska trijyaa 7 cm hai",
     "154"),
    ("15 aur 27 ka joddd ktna hoga?", "42"),
    ("do sikke uchale jaye to kam se kam ek chitt aane ki "
     "praayikta kya hai?", "0.75"),
])
def test_held_out_spellings_fold_by_rule(question, want):
    assert want in _ans(question)


def test_fold_is_identity_on_clean_questions():
    for q in ("find the area of a circle with radius 7",
              "solve x^2 - 5x + 6 = 0",
              "what is the HCF of 12 and 18",
              "5 workers can finish a job in 12 days"):
        assert normalize_spelling(q) == q


def test_money_words_never_fold_to_a_die():
    # "paas" (has) and "paise" (money) share the pasa (die)
    # skeleton; they must survive folding untouched.
    # (Wave 57 pinned fallback_kind "similar" here; since
    # Wave 67 the unsolved outcome is the not-found line —
    # what matters here is that it stays an honest non-answer,
    # never a die-roll solve.)
    res = _solve_friendly(
        "ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 "
        "rupaye ki kharidi kitne bache")
    assert res.get("fallback_kind") == "not_found"


# --- 2. Devanagari: junk guard + real patterns -----------------

@pytest.mark.parametrize("question,want", [
    ("12 और 18 का महत्तम समापवर्तक बताओ", "6"),
    ("12 और 15 का लघुत्तम समापवर्त्य निकालो", "60"),
    ("१२ और १८ का महत्तम समापवर्तक क्या होगा?", "6"),
    # Wave 99: त्रिज्या 7 -> pi = 22/7 -> 154 / 44
    # (was 153.938 / 43.98 with true pi).
    ("एक वृत्त की त्रिज्या 7 सेमी है, उसका क्षेत्रफल निकालो",
     "154"),
    ("एक वृत्त की त्रिज्या 7 सेमी है, उसकी परिधि बताओ", "44"),
    ("एक आयत की लंबाई 12 सेमी और चौड़ाई 5 सेमी है, उसका "
     "क्षेत्रफल बताओ", "60"),
    ("एक वर्ग की भुजा 9 सेमी है, उसका परिमाप बताओ", "36"),
    ("एक त्रिभुज का आधार 10 सेमी और ऊँचाई 6 सेमी है, उसका "
     "क्षेत्रफल बताओ", "30"),
    ("एक रेलगाड़ी 360 किलोमीटर की दूरी 4 घंटे में तय करती है, "
     "उसकी चाल कितनी है?", "90"),
    ("एक कार की चाल 60 किलोमीटर प्रति घंटा है, वह 3 घंटे में "
     "कितनी दूरी तय करेगी?", "180"),
    ("1000 रुपये पर 5% वार्षिक ब्याज की दर से 2 वर्ष का "
     "साधारण ब्याज कितना होगा?", "100"),
    ("240 का 15 प्रतिशत कितना होगा?", "36"),
    ("144 का वर्गमूल क्या होगा?", "12"),
])
def test_devanagari_questions_solve(question, want):
    assert want in _ans(question)


@pytest.mark.parametrize("question", [
    "पाइथागोरस प्रमेय क्या होती है?",
    "प्रायिकता किसे कहते हैं?",
    "साधारण ब्याज कैसे निकालते हैं?",
    "समकोण त्रिभुज क्या होता है?",
    "औसत कैसे निकालते हैं?",
    "क्रमगुणित क्या होता है?",
])
def test_devanagari_concept_asks_get_concept_not_soup(question):
    res = _solve_friendly(question)
    assert res.get("fallback_kind") == "concept", res.get("answer")


# --- 3. Roman-Hindi word problems & probability ---------------

@pytest.mark.parametrize("question,want", [
    ("ek train 360 km jati hai 4 ghante me, speed kitni hai?",
     "90"),
    ("ek train ko 360 km jana hai, uski speed 60 km/h hai, "
     "kitna time lagega?", "6"),
    ("train 80 km/h ki speed se 240 km kitne ghante me "
     "jayegi?", "3"),
    ("500 me se 350 number mile, percent kitna hua?", "70"),
    ("1000 rupaye ko 2:3 ke anupat me banto, pehle wale ko "
     "kitna milega?", "400"),
    ("2000 rupaye wali cheez par 10% discount hai, kitne me "
     "milegi?", "1800"),
    ("ek ghanaab ki lambai 5 cm, chaudai 4 cm aur unchai "
     "3 cm hai, uska aayatan batao", "60"),
    ("in sankhyaon ka ausat batao: 3, 6, 9, 12", "7.5"),
    ("ek pasa feko to sama sankhya aane ki probability "
     "kya hai?", "0.5"),
    ("ek pasa feko to 3 se badi sankhya aane ki probability "
     "kya hai?", "0.5"),
    ("teen sikke uchale jaye to teeno chit aane ki sambhavna "
     "kya hai?", "0.125"),
    ("do sikke uchale jaye to kam se kam ek puchh aane ki "
     "sambhavna kya hai?", "0.75"),
    ("ek sikka uchalne par puchh aane ki sambhavna "
     "kya hai?", "0.5"),
])
def test_hinglish_word_problems_solve(question, want):
    assert want in _ans(question)


# --- 4. Typo / OCR English -------------------------------------

@pytest.mark.parametrize("question,want", [
    ("find the area of a rectangel with lenght 12 and "
     "breath 5", "60"),
    # Wave 99: radius 7 -> pi = 22/7 -> 44 (was 43.98).
    ("circumfrence of a circle with radius 7", "44"),
    ("find the mena of 3, 6, 9, 12", "7.5"),
    ("what is 15% of 24O", "36"),
    ("area of a square with side 1O cm", "100"),
    ("25% of 8OO", "200"),
    ("6O km/h for 3 hours", "180"),
    # Wave 99: rad1us 7 -> pi = 22/7 -> 154 (was 153.938).
    ("find the area of a circle with rad1us 7 cm", "154"),
    ("findtheareaofasquarewithside9cm", "81"),
    ("area of a rect angle with length 12 and breadth 5", "60"),
    ("sim ple interest on 1000 at 5% for 2 years", "100"),
    ("calculate simple intrest for 2000 rupees at 6 percent "
     "for 3 year", "360"),
    ("using pythagorus theorm find the hypotenuse if base "
     "is 3 and perpendicular is 4", "5"),
    ("the length of a rectangle is 2O cm and breadth is "
     "1O cm find its area", "200"),
    ("a rope is 3 rnetres long how many centimetres is "
     "that", "300"),
])
def test_typo_and_ocr_questions_solve(question, want):
    assert want in _ans(question)


@pytest.mark.parametrize("question", [
    "x2 - 5x + 6 = 0 solve karo",
    "ye wala samjha do: x2 - 5x + 6 = 0",
])
def test_typed_superscript_quadratic_gives_both_roots(question):
    # The trailing words send this through the fallback salvage
    # layer, which is fine — what matters is that the student's
    # OWN equation is answered with BOTH roots (before Wave 57
    # "x2" parsed as a separate symbol and only one root came
    # back).
    res = _solve_friendly(question)
    assert res.get("fallback_kind") not in ("similar", "guide",
                                            "vague")
    ans = str(res.get("answer", ""))
    assert "2" in ans and "3" in ans


def test_both_coins_events_without_toss_verb():
    assert "0.25" in _ans("probability that both coins "
                          "show heads")
    assert "0.25" in _ans("probability that both coins "
                          "show tails")


# --- 5. Concept asks & honesty ---------------------------------

@pytest.mark.parametrize("question", [
    "what is HCF",
    "AP kya hoti hai?",
    "byaj kaise nikalte hai?",
    "ausat kaise nikalte hai?",
    "tribhuj ka area kaise nikale?",
    "samikaran kaise hal karte hai?",
    "what is a quadratic equation",
    "what is a right angled triangle",
    "what is a prime no",
    "madhyika kya hoti hai?",
])
def test_concept_asks_get_concept_answers(question):
    res = _solve_friendly(question)
    assert res.get("fallback_kind") == "concept", res.get("answer")


@pytest.mark.parametrize("question", [
    "train wala question banao",
    "kuch bhi bata do",
    "maths",
])
def test_vague_asks_stay_honest(question):
    res = _solve_friendly(question)
    # Wave 67: "not_found" (the one-line answer) joins the
    # honest outcomes for a vague ask.
    assert res.get("fallback_kind") in ("similar", "guide",
                                        "vague", "concept",
                                        "not_found")
