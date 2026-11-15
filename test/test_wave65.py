"""Wave 65: deep trilingual training (Hindi + Hinglish +
English). Every rule is a general schema/normalisation —
these tests pin one representative per family plus the
regression guards for the families Wave 65 touched
(probability unions/complements, cone surface areas)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import _solve_friendly  # noqa: E402


def _nums(q):
    r = _solve_friendly(q)
    text = str(r.get("answer"))
    out = [int(a) / int(b) for a, b in
           re.findall(r"(\d+)/(\d+)", text)]
    text = re.sub(r"\d+/\d+", " ", text)
    out += [float(x) for x in re.findall(r"-?\d+\.?\d*", text)]
    return out


def _has(q, want, tol=0.02):
    return any(abs(n - want) < tol for n in _nums(q))


# --- Hindi (Devanagari) --------------------------------------
def test_hindi_distance_speed_first():
    assert _has("एक बस 55 किलोमीटर प्रति घंटे की चाल से 2 घंटे "
                "चलती है। वह कितनी दूरी तय करेगी?", 110)


def test_hindi_train_conditional():
    assert _has("एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय "
                "करती है। यदि यह चाल 5 km/h अधिक होती, तो वह "
                "उसी यात्रा में 1 घंटा कम समय लेती।", 40)


def test_hindi_compound_interest_not_simple():
    assert _has("5000 रुपये का 8% वार्षिक दर से 2 वर्ष का "
                "चक्रवृद्धि ब्याज ज्ञात करो।", 832)


def test_hindi_fraction_division_parenthesised():
    assert _has("भिन्न 3/4 और 1/2 का भागफल ज्ञात कीजिए।", 1.5)


def test_hindi_trig_value():
    assert _has("sin 30° का मान बताइए।", 0.5)


def test_hindi_range_and_median():
    assert _has("निम्न आँकड़ों का परिसर (range) बताइए: "
                "9, 14, 7, 21, 13", 14)
    assert _has("आँकड़ों का माध्यक ज्ञात करो: "
                "12, 15, 18, 20, 25", 18)


def test_hindi_concepts():
    for q in ("परिमेय संख्या क्या होती है?",
              "वृत्त की त्रिज्या किसे कहते हैं?",
              "समान्तर श्रेणी किसे कहते हैं?",
              "वर्ग और आयत में क्या अंतर है?"):
        r = _solve_friendly(q)
        assert r.get("fallback_kind") == "concept", q


# --- Hinglish (Roman Hindi) -----------------------------------
def test_hinglish_feesadi():
    assert _has("640 ka 40 feesadi kitna hoga?", 256)
    assert _has("240 ka 15 feesadi kia hoga bataw?", 36)


def test_hinglish_remainder_not_division():
    assert _has("347 ko 8 se bhaag dene par shesh kitna "
                "bachega?", 3)


def test_hinglish_times_a_number_not_product():
    assert _has("ek sankhya ka 3 guna 96 hai, wo sankhya "
                "konsi hai?", 32)


def test_hinglish_cuboid_not_rectangle():
    assert _has("cuboid ka aayatan btao, lambai 11 cm chaudai "
                "7 cm unchai 3 cm", 231)


def test_hinglish_clock_speed():
    assert _has("train raat 10 bje chali aur subah 6 bje "
                "pahunchi, usne 560 km ki doori tay ki, uski "
                "speed kitni thi?", 70)


def test_hinglish_sets_neither_structural():
    assert _has("ek samuh me 45 logo me se 30 ko gana pasand "
                "hai, 20 ko naach aur 12 ko dono, kitno ko "
                "dono me se kuch nahi pasand?", 7)


# --- English ----------------------------------------------------
def test_english_typos_and_terse():
    assert _has("wat is 25 percant of 640?", 160)
    assert _has("train 756 km 9 hours speed?", 84)
    assert _has("the lenght of a rectangle is 23 m and its "
                "width is 12 m, find the perimter", 70)


def test_english_scrambled_si():
    assert _has("on 9000 rupees at 5 percent for 4 years, "
                "interest the simple find", 1800)
    assert _has("1500 at 6% 3 years interest?", 270)


def test_english_zeroes_statement_form():
    assert _has("the zeroes of x^2 - 2x - 35 are?", 7)
    assert _has("the zeroes of x^2 - 2x - 35 are?", -5)


def test_english_repeated_root():
    assert _has("factorise x^2 - 12x + 36 and give the "
                "repeated root", 6)


def test_english_consecutive_even():
    assert _has("find two consecutive even numbers whose "
                "sum is 86", 42)


# --- Regression guards ------------------------------------------
def test_probability_union_and_complement_untouched():
    assert _has("52 patto me se ek patta nikala to raja ya "
                "rani (king or queen) hone ki probability "
                "batao?", 0.1538)
    assert _has("thaili me 3 laal aur 5 kaali gende hain, ek "
                "nikali to kaali na hone ki probability "
                "kitni hogi?", 0.375)


def test_probability_specific_and_combo_cards():
    assert _has("One card is drawn from a well-shuffled deck "
                "of 52 cards. Find the probability of getting "
                "a king of hearts.", 0.0192)
    assert _has("A card is drawn from a pack of 52 cards. "
                "What is the probability that it is a red "
                "queen?", 0.0385)


def test_cone_surface_area_not_slant():
    assert _has("Find the curved surface area of a cone with "
                "radius 6 cm and slant height 10 cm.", 188.5)
    assert _has("find the slant height of a cone with "
                "radius 3 cm and height 4 cm", 5)
