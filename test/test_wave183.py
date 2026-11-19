"""Wave 183 (Suraj, 19 Nov 2026, live test 13:52 IST +
his sharpening the same hour): "Prediction bhi karana
hota hai — agar prediction achhe se nhi ho paa rha hai
toh kis mtlb kaa ai hai." A student asks in natural,
imperfect wording; Ganitra must infer the INTENT, not
demand an exact pattern.

His three live failures (all served "Answer nahi mila"):
  * "Aryabhata ne kya kiya tha" — a CONTRIBUTION ask;
    the person entries only fired on WHO shapes
    ("kaun tha"), and the question classified as
    "gibberish", a kind the AI chain never sees.
  * "Brahmagupta ne kya kiya tha" — same family.
  * "जीरो की खोज किसने की थी और क्यों की थी क्यों बनाया
    था" — the SPOKEN zero: voice typing says "जीरो",
    which was not a keyword of the zero entry at all,
    and the extra क्यों clauses had no answer anywhere.

Pinned here:
  1. The three failures + variants serve the curated
     knowledge cards locally (no API keys) — patterns
     are the FAST PATH.
  2. Zero asks that also ask WHY carry one why line;
     a plain who-ask keeps the Wave 177 card untouched.
  3. The ROUTING guarantee (the priority): a knowledge
     question that MISSES the curated entries (Euler /
     Leibniz contribution asks) is AI-ELIGIBLE — with
     the legs stubbed it serves the AI answer, and the
     eligibility marker is is_meta_shaped /
     is_knowledge_shaped, the exact functions
     fallback.py consults at the gibberish branch.
  4. The guards do not move: true gibberish and a
     non-maths person (no maths anchor) never reach
     the AI legs; word problems that merely carry a
     name are not knowledge; concept asks keep their
     concept cards.
"""
import pytest

import fallback
from fallback import _is_gibberish, fallback_answer
from maths_meta import is_knowledge_shaped, is_meta_shaped, \
    meta_result


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the real AI legs stay inert (the routing
    tests patch the chain functions directly)."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _blob(out):
    return (str(out.get("answer") or "") + " "
            + " ".join(out.get("steps") or []))


def _patch_ai(monkeypatch, reply):
    """The Wave 111 harness: stub the three AI legs at
    fallback's own seams and record Gemini's calls."""
    calls = []

    def fake_gemini(question, hindi, lang_request=None):
        calls.append(question)
        return reply

    monkeypatch.setattr(fallback, "_gemini_answer",
                        fake_gemini)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)
    return calls


_SENTINEL = {
    "type": "AI", "op": "gemini", "answer": "AI sentinel",
    "steps": [], "fallback": True, "fallback_kind": "gemini",
}


# ---------------------------------------------------------------------------
# 1. Suraj's three live failures — the curated fast path
# ---------------------------------------------------------------------------

def test_live_aryabhata_contribution_serves_card():
    r = fallback_answer("Aryabhata ne kya kiya tha")
    assert r["fallback_kind"] == "history"
    assert r["op"] == "history_aryabhata"
    assert "Aryabhatiya" in _blob(r)


def test_live_brahmagupta_contribution_serves_card():
    r = fallback_answer("Brahmagupta ne kya kiya tha")
    assert r["fallback_kind"] == "history"
    assert r["op"] == "history_brahmagupta"
    assert "Brahmasphutasiddhanta" in _blob(r)


def test_live_spoken_zero_with_why_serves_card():
    q = "जीरो की खोज किसने की थी और क्यों की थी क्यों बनाया था"
    r = fallback_answer(q)
    assert r["fallback_kind"] == "history"
    assert r["op"] == "history_zero"
    blob = _blob(r)
    # The seed list's two-name rule, in the spoken form.
    assert "आर्यभट" in blob and "ब्रह्मगुप्त" in blob
    # ...and the WHY the student asked twice gets its line.
    assert "ज़रूरत" in blob


@pytest.mark.parametrize("question,op", [
    ("What did Aryabhata do?", "history_aryabhata"),
    ("Brahmagupta ne kya diya tha", "history_brahmagupta"),
    ("आर्यभट ने क्या किया था", "history_aryabhata"),
    ("Ramanujan ka yogdan kya hai", "history_ramanujan"),
    ("Bhaskara ke baare me batao", "history_bhaskara"),
    ("Shakuntala Devi kis liye mashhoor hai",
     "history_shakuntala_devi"),
    ("What did Gauss contribute?", "history_gauss"),
    ("Archimedes ne kya kiya tha", "history_archimedes"),
    ("Pythagoras ne kya kiya tha", "history_pythagoras"),
    ("Euclid ke baare me batao", "history_euclid"),
    ("Fibonacci ne kya kiya tha", "history_fibonacci"),
    ("zero kyon banaya gaya tha", "history_zero"),
    ("जीरो क्यों बनाया गया", "history_zero"),
    ("jeero ki khoj kisne ki", "history_zero"),
])
def test_contribution_and_origin_variants(question, op):
    r = fallback_answer(question)
    assert r["fallback_kind"] == "history", question
    assert r["op"] == op, question


# ---------------------------------------------------------------------------
# 2. The why line: present only when WHY is asked
# ---------------------------------------------------------------------------

def test_why_line_inserted_before_gist():
    m = meta_result("0 kisne banaya aur kyon")
    assert m is not None and m["op"] == "history_zero"
    assert len(m["steps"]) == 5
    assert "zaroorat" in m["steps"][-2]
    assert m["steps"][-1].startswith("Short me")


def test_plain_who_ask_keeps_wave177_card_untouched():
    m = meta_result("0 ki khoj kisne ki hai")
    assert m is not None and m["op"] == "history_zero"
    assert len(m["steps"]) == 4
    assert not any("zaroorat" in s for s in m["steps"])


# ---------------------------------------------------------------------------
# 2b. The detector itself: intent is never "gibberish"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Aryabhata ne kya kiya tha",
    "Brahmagupta ne kya kiya tha",
    "जीरो की खोज किसने की थी और क्यों की थी क्यों बनाया था",
])
def test_intent_questions_are_not_gibberish(question):
    # The core misclassification, pinned at the detector:
    # every word of "Aryabhata ne kya kiya tha" sits
    # outside the known-word list, yet the question is a
    # real, intent-bearing maths question — the
    # "gibberish" bucket is not AI-eligible, so the label
    # alone used to send it straight to not-found.
    assert _is_gibberish(question) is False
    assert is_knowledge_shaped(question) is True


def test_true_gibberish_still_gibberish():
    assert _is_gibberish("asdf qwer zxcv") is True


# ---------------------------------------------------------------------------
# 3. The routing guarantee: knowledge misses reach the AI chain
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Euler ne kya kiya tha",
    "Leibniz ne kya diya tha",
    "What did Euler contribute?",
])
def test_knowledge_miss_reaches_ai(monkeypatch, question):
    # No curated entry exists for Euler / Leibniz — the
    # intent must still reach the verified-AI chain.
    assert meta_result(question) is None
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert calls, "AI chain was never consulted"
    assert r.get("answer") == "AI sentinel"
    assert r.get("fallback_kind") != "not_found"


@pytest.mark.parametrize("question", [
    "Euler ne kya kiya tha",
    "Leibniz ne kya diya tha",
    "What did Euler contribute?",
])
def test_knowledge_miss_is_ai_eligible_marker(question):
    # Without any AI leg the serve may collapse locally,
    # but the classification fallback.py consults at the
    # gibberish branch must mark it AI-eligible ("guide"),
    # never "gibberish".
    assert is_meta_shaped(question) \
        or is_knowledge_shaped(question)


# ---------------------------------------------------------------------------
# 4. Guards: gibberish and non-maths never become AI-eligible
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "asdf qwer zxcv",
    # Contribution PHRASE, letter-soup name: no maths
    # anchor, so the anchor gate keeps it gibberish.
    "zxcv ne kya kiya tha qwer",
    # A real person, but not a maths person and no maths
    # anchor: the maths-only guard is not weakened.
    "Shakespeare ne kya kiya tha",
])
def test_unanchored_asks_never_reach_ai(monkeypatch, question):
    assert not (is_meta_shaped(question)
                or is_knowledge_shaped(question))
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert not calls, "AI chain must not see this"
    assert r.get("fallback_kind") == "not_found"


def test_nonmaths_still_refused(monkeypatch):
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer("What is the capital of France?")
    assert not calls
    assert r.get("fallback_kind") == "nonmaths"


# ---------------------------------------------------------------------------
# 5. Anti-hijack: names inside problems are not knowledge
# ---------------------------------------------------------------------------

def test_word_problem_with_name_is_not_knowledge():
    q = "Aryabhata school me 40 bache hai, 5 group banao"
    assert meta_result(q) is None
    r = fallback_answer(q)
    assert r.get("fallback_kind") not in ("history", "fact")


def test_arithmetic_with_name_still_solves():
    r = fallback_answer("Aryabhata ke sawal: 12 + 8 kitna "
                        "hota hai")
    assert r.get("fallback_kind") not in ("history", "fact")
    assert str(r.get("answer")) == "20"


def test_concept_ask_keeps_its_concept_card():
    # "me kya kiya jata hai" is a concept ask, not a
    # contribution ask — the "ne" frame is absent.
    q = "trigonometry me kya kiya jata hai"
    assert meta_result(q) is None
    r = fallback_answer(q)
    assert r.get("fallback_kind") == "concept"


# ---------------------------------------------------------------------------
# 6. Controls: the Wave 177 serves are unchanged
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,op", [
    ("0 ki khoj kisne ki hai", "history_zero"),
    ("Aryabhata kaun the", "history_aryabhata"),
    ("Who discovered 0?", "history_zero"),
])
def test_wave177_controls_unchanged(question, op):
    r = fallback_answer(question)
    assert r["fallback_kind"] == "history"
    assert r["op"] == op
