"""Wave 79: spelling-chaos tolerance, round 2.

The Wave 71 audit's family 7 held 17 heavy-misspelling
Hinglish/English variants of core schemas (SDT, triangle &
circle area, mean-of-list, percent-of): 14 NOT_FOUND + 3
CONCEPT misroutes. Per-item diagnosis (see
~/workspace/ganitra-wave79-notes.md):

- Already folding before this wave (skeleton/variant layer):
  ktna, ispid, trijya, nikaloo, tren, triangel, ghantay.
- Missing entries for common student spellings: avrej -> ausat,
  kia -> kya (Hinglish variants); eria -> area, circal -> circle
  (English typos, siblings of aera / cirle from earlier waves).
- Missing generalisable RULES, now in _fold_word:
  (a) soft-c: s -> c before e/i when the c-form is a known word
      ("parsent" -> "parcent" -> pratishat, "persent" ->
      "percent", "sircle" -> "circle"); real s-words never move.
  (b) Roman-Hindi -ay/-aw endings fold to -ai/-ao when the
      result is a known Hinglish word ("hay" -> hai,
      "bataw" -> batao); English day/way/saw never move.
- One normaliser gate widening (not a solver change): the
  Roman-Hindi time-from-distance+speed rewrite now also fires
  on the hours ask "kitne ghante lagenge", not only on
  "time"/"samay".
- SEALED honesty markers stay sealed: "parsent" was never
  added as a map entry (the soft-c RULE reaches it via the
  pre-existing "parcent" variant), and "mesn" (Wave 65 English
  held-out) is still NOT folded — it remains not-found, as
  designed in Waves 57/65.
"""
import re

import pytest

from api import _solve_friendly
from solver.router import _EN_TYPOS, _HINGLISH_VARIANTS, \
    normalize_spelling


def _num(ans):
    m = re.findall(r"-?\d+(?:\.\d+)?", str(ans).replace(",", ""))
    return float(m[-1]) if m else None


def _solved_value(question):
    r = _solve_friendly(question)
    assert not r.get("fallback_kind"), (
        f"{question!r} fell to fallback: {r.get('answer')!r}")
    return _num(r.get("answer", ""))


# --- The audit family, fixed --------------------------------

FAMILY_FIXED = [
    ("240 ka 15 parsent ktna hoga?", 36),
    ("240 ka 15 parsent kitnaaa hoga?", 36),
    ("tren ko 360 km jana hay aur ispid 60 km/h hay, "
     "kitne ghantay lagenge bataw?", 6),
    ("tren ko 450 km jana hay aur ispid 75 km/h hay, "
     "kitne ghantay lagenge bataw?", 6),
    ("tren ko 280 km jana hay aur ispid 70 km/h hay, "
     "kitne ghantay lagenge bataw?", 4),
    ("triangel ka aadhar 10 cm aur unchai 6 cm hay, "
     "eria bataw?", 30),
    ("triangel ka aadhar 12 cm aur unchai 8 cm hay, "
     "eria bataw?", 48),
    ("triangel ka aadhar 15 cm aur unchai 5 cm hay, "
     "eria bataw?", 37.5),
    ("circal ki trijya 7 cm hay, uska eria nikaloo?", 153.938),
    ("circal ki trijya 14 cm hay, uska eria nikaloo?", 615.7522),
    ("circal ki trijya 10 cm hay, uska eria nikaloo?", 314.1593),
    ("in sankhyao ka avrej kia hay: 2, 4, 6, 8, 10 "
     "— anser bataw?", 6),
    ("in sankhyao ka avrej kia hay: 5, 10, 15, 20, 25 "
     "— anser bataw?", 15),
    ("in sankhyao ka avrej kia hay: 3, 7, 9, 12, 14 "
     "— anser bataw?", 9),
    ("in sankhyao ka avrej kia hay: 10, 20, 30, 40 "
     "— anser bataw?", 25),
    ("7, 14, 21, 28 ka avrej nikaloo?", 17.5),
]


@pytest.mark.parametrize("question,want", FAMILY_FIXED)
def test_family7_items_now_solve(question, want):
    got = _solved_value(question)
    assert got is not None
    assert abs(got - want) < 0.01 * max(1, abs(want))


# --- Sealed spellings stay sealed ----------------------------

def test_mesn_is_still_not_found():
    # Wave 65's sealed English held-out spelling: no map entry,
    # and the soft-c rule cannot reach it (s is not before e/i).
    assert "mesn" not in _EN_TYPOS
    assert normalize_spelling("find the mesn of 5, 15, 25") == \
        "find the mesn of 5, 15, 25"
    r = _solve_friendly("find the mesn of 5, 15, 25, 35, 45")
    assert r.get("fallback_kind") == "not_found"


def test_parsent_folded_by_rule_not_by_entry():
    # The sealed word itself was never added to any map; the
    # general soft-c rule folds it onto the pre-existing
    # "parcent" variant, which then maps to pratishat.
    assert "parsent" not in _HINGLISH_VARIANTS
    assert "parsent" not in _EN_TYPOS
    assert normalize_spelling("240 ka 15 parsent ktna hoga?") == \
        "240 ka 15 pratishat kitna hoga?"


# --- The rules generalise (fresh spellings, not in any battery)

def test_soft_c_rule_fresh_forms():
    assert normalize_spelling("sircle") == "circle"
    # "persent" folds to "percent", which the pre-existing
    # N-percent -> N% rewrite then converts.
    assert normalize_spelling("find 40 persent of 750") == \
        "find 40% of 750"


def test_ay_aw_rule_fresh_forms():
    assert normalize_spelling("jawab bataw") == "jawab batao"
    assert normalize_spelling("ye train hay") == "ye train hai"


def test_fresh_heldout_solves():
    assert _solved_value("900 ka 25 persent ktna hoga?") == 225
    assert _solved_value(
        "bus ko 200 km jana hay aur ispid 40 km/h hay, "
        "kitne ghantay lagenge bataw?") == 5
    assert _solved_value(
        "4, 8, 15, 16, 23, 42 ka avrej kia hay?") == 18


# --- Corruption guards: clean text passes through -----------

CLEAN = [
    "find the simple interest on rs 1000 for 2 years",
    "what is the area of a circle with radius 7 cm",
    "a train travels 240 km in 4 hours, find its speed",
    "mujhe 500 paise chahiye",
    "samay kitna hua",
    "aise hi batao",
    "ram goes to school by bus every day",
    "since morning the sell of pens is high",
]


@pytest.mark.parametrize("text", CLEAN)
def test_clean_text_unchanged(text):
    assert normalize_spelling(text) == text


def test_risk_tokens_never_fold():
    # s-before-e/i words and -ay/-aw words that are already
    # correct must not move.
    for tok in ("since", "simple", "sell", "paise", "samay",
                "day", "way", "saw", "aise", "kaise"):
        assert normalize_spelling(tok) == tok


# --- Fallback discipline intact ------------------------------

def test_gibberish_still_one_line_not_found():
    r = _solve_friendly("flibberty gibbet snizzle frazzle")
    assert r.get("fallback_kind") == "not_found"
    assert "\n" not in str(r.get("answer", "")).strip()


def test_non_maths_hinglish_still_not_found():
    r = _solve_friendly("hay bataw kia scene hay yr")
    assert r.get("fallback_kind") == "not_found"
