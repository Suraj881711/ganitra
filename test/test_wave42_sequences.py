"""Wave 42 (15 Nov 2026): Hindi / Hinglish AP phrasing +
next term. Wave 33 covered Hindi probability but left Hindi
AP behind: "समांतर श्रेढ़ी 5, 10, 15, ... का 12वां पद" and
Roman forms ("12va pad", "pehle 10 padon ka yog", "agla
pad") matched no pattern and fell to a concept/guide
fallback (audit #392, #472, #423 all FALLBACK).

Router gained the Hindi sequence tokens; sequences.py
gained a block mirroring the English AP coverage (nth term,
sum of n terms) for Devanagari + Roman-Hindi ordinals, and
a next-term answer for AP/GP in any language ("What is the
next term of the AP 2, 5, 8, ...?" was a guide fallback).
"""
import pytest

from api import _solve_friendly


def _exact(question, expected_value):
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    assert res.get("value") == pytest.approx(expected_value), (
        f"{question!r} -> {res.get('answer')!r}, "
        f"expected {expected_value}")


# --- Hindi (Devanagari) AP: nth term -------------------------
def test_hindi_ap_nth_term_battery_392():
    _exact("समांतर श्रेढ़ी 5, 10, 15, ... का 12वां पद "
           "ज्ञात कीजिए।", 60)


def test_hindi_ap_nth_term_battery_472():
    _exact("समांतर श्रेढ़ी 2, 5, 8, ... का 15वां पद "
           "ज्ञात कीजिए।", 44)


def test_hindi_ap_nth_term_shreni_spelling():
    _exact("समांतर श्रेणी 7, 13, 19, ... का 10वां पद "
           "ज्ञात कीजिए।", 61)


def test_hindi_ap_nth_term_negative_difference():
    _exact("समांतर श्रेढ़ी 20, 17, 14, ... का 9वां पद "
           "ज्ञात कीजिए।", -4)


# --- Hindi AP: sum of first n terms --------------------------
def test_hindi_ap_sum_pahle():
    _exact("समांतर श्रेढ़ी 2, 5, 8, ... के पहले 10 पदों का "
           "योग ज्ञात कीजिए।", 155)


def test_hindi_ap_sum_pratham():
    _exact("समांतर श्रेढ़ी 3, 8, 13, ... के प्रथम 20 पदों "
           "का योग ज्ञात कीजिए।", 1010)


# --- Roman-Hindi (Hinglish) AP -------------------------------
def test_hinglish_ap_nth_term_va_pad():
    _exact("AP 5, 10, 15 ka 12va pad kya hai?", 60)


def test_hinglish_ap_nth_term_samantar_shreni():
    _exact("samantar shreni 3, 7, 11, ... ka 8va pad batao",
           31)


def test_hinglish_ap_sum_padon_ka_yog():
    _exact("AP 2, 5, 8 ke pehle 10 padon ka yog kya hai?",
           155)


# --- Next term (any language) --------------------------------
def test_hinglish_next_term_battery_423():
    _exact("5, 8, 11, 14 ye kram hai, agla pad batao", 17)


def test_hindi_next_term_agla_pad():
    _exact("समांतर श्रेढ़ी 5, 10, 15, ... का अगला पद क्या "
           "है?", 20)


def test_english_next_term_ap():
    _exact("What is the next term of the AP 2, 5, 8, ...?",
           11)


def test_english_next_term_gp():
    _exact("What is the next term of the GP 3, 6, 12, ...?",
           24)


# --- Controls: English coverage unchanged --------------------
def test_control_english_ap_nth_term():
    _exact("Find the 10th term of the AP 2, 5, 8", 29)


def test_control_english_ap_sum():
    _exact("Find the sum of the first 10 terms of the AP "
           "2, 5, 8", 155)


def test_control_english_gp_sum():
    _exact("Find the sum of the first 10 terms of the GP "
           "3, 6, 12", 3069)
