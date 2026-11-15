"""Wave 59 (15 Nov 2026): Hinglish deep training + the two
Deploy-3 live gaps.

Families: Hinglish train conditional (zyada/kam hoti-to-
lagta); Unicode superscripts in the cleaning layer;
Hinglish translations for sets/ages/probability/calculus/
sequences/interest/mensuration stories; story-dressing
non-maths guard exemption; skeleton-target overrides;
non-hijack controls for older waves (segment, grouped
data, specific cards, geometric mean, identities).
"""
from api import _solve_friendly


def _r(q):
    return _solve_friendly(q)


def _ans(q):
    return str(_r(q).get("answer", ""))


def _exact(q):
    return "fallback" not in _r(q)


def test_train_conditional_live_question():
    q = ("ek train 360 km jati hai, agar speed 5 km/h zyada "
         "hoti to 1 ghanta kam lgta, speed ktni hai btao")
    assert _exact(q) and _ans(q) == "40 km/h"


def test_train_conditional_variants():
    assert _ans("ek train 200 km jati hai, agar speed "
                "10 km/h zyada hoti to 1 ghanta kam lagta, "
                "speed kitni hai?") == "40 km/h"
    assert _ans("ek train 360 km jati hai, agar speed "
                "5 km/h kam hoti to 1 ghanta zyada lagta, "
                "speed kitni hai?") == "45 km/h"
    # the English NCERT twin keeps its schema
    assert _ans("A train travels a distance of 240 km at "
                "a uniform speed. If the speed had been "
                "20 km/h more, it would have taken 2 hours "
                "less for the same journey. Find the speed "
                "of the train.") == "40 km/h"


def test_unicode_superscripts():
    assert "x = 2" in _ans("x² - 5x + 6 = 0")
    assert "x = 3" in _ans("x² - 5x + 6 = 0")
    assert "-3/2" in _ans("2x² + 3x = 0")
    assert "x = 2" in _ans("x³ - 8 = 0")
    # the pre-pass retry must not resurrect the raw ² text
    assert "-4" in _ans("x² + 7x + 12 = 0 ke mool batao")
    assert "-12/7" not in _ans("x² + 7x + 12 = 0 ke mool batao")


def test_story_dressing_not_refused():
    assert _ans("ek class me 30 ladke cricket khelte hain, "
                "25 football khelte hain aur 10 dono khelte "
                "hain, kitne ladke khelte hain?") == "45"
    assert "1436" in _ans(
        "football gol (sphere) aakar ki hoti hai, ek gend "
        "ki trijya 7 cm hai to uska volume kitna hoga?")
    assert "25" in _ans(
        "ram aur shyam dono bhai hain, ram bada hai aur "
        "cricket khelta hai, dono ki umar ka yog 40 saal "
        "hai aur antar 10 saal hai, bade bhai ram ki umar "
        "kitni hai?")


def test_hinglish_families():
    assert _ans("240 ka15 persent kitna hogaa?") == "36"
    assert _ans("pehli 10 prakrit sankhyao (natural "
                "numbers) ka yog kitna hota hai?") == "55"
    assert _ans("do sikke uchale, kam se kam ek chit aane "
                "ki probability kitni hai?") == "3/4 ≈ 0.7500"
    assert _ans("agar 2 : 3 = x : 15 hai to x kitna "
                "hoga?") == "10"
    assert _ans("20 sankhyao ka mean 15 nikala gaya tha, "
                "baad me pata chala ek sankhya 25 ki jagah "
                "35 padhi gayi thi, sahi mean kitna "
                "hoga?") == "14.5"


def test_non_hijack_controls():
    assert _ans("Find the area of a segment of a circle "
                "with radius 10 cm and angle 90 degrees."
                ) == "28.5398"
    assert _ans("Find the mean of the data with class "
                "intervals 0-10, 10-20, 20-30, 30-40, "
                "40-50 and frequencies 6, 10, 14, 8, 2."
                ) == "22.5"
    assert _ans("Find the geometric mean of 2, 4 and 8."
                ) == "4"
    assert _ans("One card is drawn from a well-shuffled "
                "deck of 52 cards. Find the probability "
                "of getting a king of hearts."
                ).startswith("1/52")
    assert "2/13" in _ans(
        "A card is drawn from a well-shuffled deck of 52 "
        "cards. What is the probability of getting a "
        "king or a queen?")
    assert _ans("500 gram ka daam 40 rupaye hai, 2 kilo "
                "ka daam batao") == "Rs 160"
    assert _ans("Prove that sin^2 theta + cos^2 theta = 1"
                ) == "Identity verified ✔"
    assert _ans("limit x->0 of sin(x)/x") == "1"
