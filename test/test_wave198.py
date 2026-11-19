"""Wave 198 (Suraj, 20 Nov 2026): zero ka shrey
Aryabhata ko — uska correction.

Suraj's live phone test (20 Nov 2026, ~00:36 IST): for
"0 ki khoj kisne ki" Ganitra served the history_zero
card, but its closing Answer line read "Zero — India
me bana; iske niyam sabse pehle Brahmagupta ne diye
(628 CE)" — leading with Brahmagupta. Suraj corrected
it: "Iska right ans ye nhi hai ki aaryabhat ne ki
thi" — the standard school answer is that ARYABHATA
discovered zero.

Fix (maths_meta.py, HISTORY entry id "zero", all three
flavours en / roman / dev rewritten consistently):
  * the answer line credits Aryabhata (आर्यभट) as the
    inventor of zero;
  * the first step credits Aryabhata with the khoj —
    he gave zero its place in the place-value system
    and used it as a real number;
  * Brahmagupta stays in the steps as the supporting
    detail: in Brahmasphutasiddhanta (628 CE) he gave
    the first clear rules for adding, subtracting and
    multiplying with zero;
  * the closing gist ("zero India ki den hai" /
    "zero is India's gift") is unchanged, and the
    Wave 183 WHY-line mechanism is untouched.

Pinned here: every common ask form serves the
history_zero card whose ANSWER line names Aryabhata,
with Brahmagupta present in the steps only.
"""
import pytest

from fallback import fallback_answer
from maths_meta import HISTORY, META_VARIATIONS, meta_result


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the curated card serves locally; the
    AI legs stay inert."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _entry(entry_id):
    return next(e for e in HISTORY if e["id"] == entry_id)


# ---------------------------------------------------------------------------
# The entry itself: all three flavours lead with Aryabhata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("flavour,inventor,rules_name", [
    ("en", "Aryabhata", "Brahmagupta"),
    ("roman", "Aryabhata", "Brahmagupta"),
    ("dev", "आर्यभट", "ब्रह्मगुप्त"),
])
def test_zero_entry_answer_credits_aryabhata(flavour, inventor,
                                             rules_name):
    card = _entry("zero")[flavour]
    # The answer line names the inventor...
    assert inventor in card["answer"]
    # ...and does NOT lead with the rules author.
    assert rules_name not in card["answer"]
    # Brahmagupta stays — in the steps, with his 628 CE rules.
    steps = " ".join(card["steps"])
    assert rules_name in steps
    assert "628" in steps
    # First step is the khoj, credited to Aryabhata.
    assert inventor in card["steps"][0]


# ---------------------------------------------------------------------------
# The served card, one test per common ask form
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,inventor,rules_name", [
    ("0 ki khoj kisne ki", "Aryabhata", "Brahmagupta"),
    ("Who discovered zero?", "Aryabhata", "Brahmagupta"),
    ("जीरो की खोज किसने की थी", "आर्यभट", "ब्रह्मगुप्त"),
    ("zero kisne banaya", "Aryabhata", "Brahmagupta"),
])
def test_served_zero_card_leads_with_aryabhata(question, inventor,
                                               rules_name):
    r = fallback_answer(question)
    assert r is not None, question
    assert r["fallback_kind"] == "history", question
    assert r["op"] == "history_zero", question
    # Answer line: Aryabhata the inventor, no Brahmagupta.
    assert inventor in str(r["answer"]), question
    assert rules_name not in str(r["answer"]), question
    # Steps: Brahmagupta still there as the rules detail.
    assert rules_name in " ".join(r["steps"]), question


def test_meta_result_zero_card_matches():
    m = meta_result("0 ki khoj kisne ki")
    assert m is not None and m["op"] == "history_zero"
    assert "Aryabhata" in str(m["answer"])
    assert "Brahmagupta" not in str(m["answer"])
    assert "Brahmagupta" in " ".join(m["steps"])
    # Card shape unchanged: 4 steps, gist last (Wave 183 pin).
    assert len(m["steps"]) == 4
    assert m["steps"][-1].startswith("Short me")


# ---------------------------------------------------------------------------
# Fix 2 (audit 20 Nov): the pi card leads with Aryabhata too
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("flavour,first,second", [
    ("en", "Aryabhata", "Archimedes"),
    ("roman", "Aryabhata", "Archimedes"),
    ("dev", "आर्यभट", "आर्किमिडीज़"),
])
def test_pi_entry_answer_leads_with_aryabhata(flavour, first,
                                              second):
    answer = _entry("pi")[flavour]["answer"]
    assert "3.1416" in answer
    # Aryabhata is named BEFORE Archimedes in the line.
    assert answer.index(first) < answer.index(second)


@pytest.mark.parametrize("question,first,second", [
    ("pi ki khoj kisne ki", "Aryabhata", "Archimedes"),
    ("who discovered pi", "Aryabhata", "Archimedes"),
])
def test_served_pi_card_leads_with_aryabhata(question, first,
                                             second):
    r = fallback_answer(question)
    assert r is not None, question
    assert r["fallback_kind"] == "history", question
    assert r["op"] == "history_pi", question
    answer = str(r["answer"])
    assert answer.index(first) < answer.index(second), question


def test_pi_again_line_drops_measuring_claim():
    # Wave 198 (audit 20 Nov): no "found it by measuring
    # circles" embellishment in any flavour.
    pi_var = META_VARIATIONS[("history", "pi")]
    assert "measuring" not in pi_var["en"]["again"][0]
    assert "naap" not in pi_var["roman"]["again"][0]
    assert "नाप" not in pi_var["dev"]["again"][0]
    for flavour in ("en", "roman", "dev"):
        assert "3.1416" in pi_var[flavour]["again"][0]


# ---------------------------------------------------------------------------
# Fix 3 (audit 20 Nov): bhaskara third-repeat line is consistent
# ---------------------------------------------------------------------------

def test_bhaskara_third_line_two_thirds():
    bh = META_VARIATIONS[("history", "bhaskara")]
    en = bh["en"]["third"][0]
    roman = bh["roman"]["third"][0]
    dev = bh["dev"]["third"][0]
    assert "two-thirds of them" in en
    assert "half of them" not in en
    assert "do-tihaai" in roman
    assert "aadhi" not in roman
    assert "दो-तिहाई" in dev
    assert "आधी" not in dev
    # The stated answer is now consistent with the
    # fraction: 15 bees, two-thirds on the flower = 10,
    # and 5 left over.
    assert 15 * 2 // 3 == 10
    assert "(Answer: 10.)" in en
    assert "(Jawab: 10.)" in roman
    assert "15" in en and "5 left over" in en
