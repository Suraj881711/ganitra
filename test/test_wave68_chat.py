"""Wave 68 (Suraj, 15 Nov 2026): CHAT PAGE OVERHAUL.

Suraj's order: "Chat wale page par achhe se dhyan do — kya
puch raha hai insaan, kya ans dena hai... ans kaise dena hai,
kaise batana hai, sab cheej dekho achhe se." Plus his rule
from the gibberish screenshots: solve na ho ya kuch bhi
ulta-seedha likho to SIRF ek line — "Answer not found /
उत्तर नहीं मिला। / Answer nahi mila." — no long guide card,
no notebook panel, no advice.

What these tests pin:
1. THE INTENT GATE: greetings (EN / Hinglish / Devanagari),
   gibberish, non-maths questions and science questions get
   PLAIN one-line replies (result.plain_reply) in the
   question's own language/script — never a card payload
   with steps panels. Unsolved real questions settle on the
   same one-liner after the AI brains decline.
2. SOLVED ANSWERS keep their exact values; word problems
   gain the intro line (the solver's own givens/framing
   first step) via api._intro_for; bare computations get
   none; the final answer is never duplicated as a step or
   in the intro.
3. THE CHAT TEMPLATE: no explanation paragraph, no
   notebook/copy-style panel in the answer flow, NO example
   chips on the empty state (Wave-68 chips removed in Wave
   69 on Suraj's order), pins ?v=43 / ganitra-static-v31.
"""
from pathlib import Path

import pytest

from api import _intro_for, _solve_friendly

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _one_line(result):
    ans = str(result.get("answer", ""))
    return "\n" not in ans and len(ans) < 170


# --- 1. The intent gate: plain one-liners --------------------

@pytest.mark.parametrize("question", [
    "hi", "hello", "namaste", "kaise ho", "thank you",
    "tum kaun ho", "bye",
    "नमस्ते", "कैसे हो", "धन्यवाद", "तुम कौन हो",
])
def test_greetings_are_plain_one_liners(question):
    r = _solve_friendly(question)
    assert r.get("fallback_kind") == "greeting", r
    assert r.get("plain_reply") is True
    assert r.get("steps") == []
    assert _one_line(r)


def test_greeting_language_matches_question():
    assert _solve_friendly("नमस्ते")["answer"].startswith("नमस्ते")
    assert _solve_friendly("namaste")["answer"].startswith("Namaste")
    assert _solve_friendly("hi")["answer"].startswith("Hello")


@pytest.mark.parametrize("question,want", [
    ("If tu gfuf", "Answer not found."),
    ("asdf qwer zxq", "Answer not found."),
    ("xyzabc pqr stu", "Answer not found."),
    ("कखग घङच छजझ", "उत्तर नहीं मिला।"),
])
def test_gibberish_is_the_not_found_line(question, want):
    r = _solve_friendly(question)
    assert r.get("plain_reply") is True
    assert r.get("steps") == []
    assert r.get("answer") == want


def test_bare_hindi_word_is_not_letter_soup():
    # "बताओ" used to be "answered" with a Devanagari
    # letter-product (ओ*त*ब*ा). It is a vague ask and gets
    # the friendly one-liner instead.
    r = _solve_friendly("बताओ")
    assert r.get("plain_reply") is True
    assert "*" not in str(r.get("answer", ""))


@pytest.mark.parametrize("question", [
    "what is the capital of india",
    "who won the match",
    "aaj ka mausam kaisa hai",
])
def test_nonmaths_guard_is_one_line(question):
    r = _solve_friendly(question)
    assert r.get("fallback_kind") == "nonmaths", r
    assert r.get("plain_reply") is True
    assert r.get("steps") == []
    assert _one_line(r)


def test_nonmaths_devanagari_gets_devanagari_line():
    r = _solve_friendly("भारत की राजधानी क्या है?")
    assert r.get("fallback_kind") == "nonmaths", r
    assert r.get("plain_reply") is True
    assert "गणित" in r["answer"]


def test_science_guard_plain_with_guidance():
    q = ("A ray of light travels from medium A to medium B. "
         "The refractive index of medium B relative to "
         "medium A is 1.5, and the speed of light in medium "
         "A is 2 x 10^8 m/s. What is the speed of light in "
         "medium B?")
    r = _solve_friendly(q)
    assert r.get("fallback_kind") == "science", r
    assert r.get("plain_reply") is True
    assert "Maths" in r["answer"]
    assert "refractive index" in " ".join(r.get("steps") or [])


@pytest.mark.parametrize("question", [
    "maths", "kuch bhi bata do", "समझाओ",
])
def test_vague_asks_are_plain_one_liners(question):
    r = _solve_friendly(question)
    assert r.get("fallback_kind") == "vague", r
    assert r.get("plain_reply") is True
    assert r.get("steps") == []
    assert _one_line(r)


# --- 2. Solved answers: values, intro, no duplication --------

HINDI_TRAIN = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। "
    "यदि यह चाल 5 km/h अधिक होती तो वह उसी यात्रा में 1 घंटा "
    "कम लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
PROFIT_Q = ("A shopkeeper buys an article for Rs 800 and "
            "sells it for Rs 920. Find his profit percent.")


def test_solved_values_spot_set():
    assert "40 km/h" in _solve_friendly(HINDI_TRAIN)["answer"]
    assert _solve_friendly("Solve x^2 - 5x + 6 = 0")["answer"] \
        == "x = 2, x = 3"
    assert _solve_friendly("What is 15% of 240?")["answer"] == "36"
    # Wave 99 (pi policy): radius 7 -> pi = 22/7 -> "154"
    # (was "49·pi ≈ 153.9380", hence the old "49" check).
    assert "154" in _solve_friendly(
        "Find the area of a circle with radius 7 cm.")["answer"]
    assert "90 km/h" in _solve_friendly(
        "ek train 360 km jati hai 4 ghante me, "
        "speed kitni hai?")["answer"]
    assert _solve_friendly(PROFIT_Q)["answer"] == "15%"


def test_solved_answers_are_not_plain():
    for q in (HINDI_TRAIN, "What is 15% of 240?", PROFIT_Q):
        assert not _solve_friendly(q).get("plain_reply")


def test_intro_for_word_problems():
    r = _solve_friendly(HINDI_TRAIN)
    intro = _intro_for(r, HINDI_TRAIN)
    assert intro is not None
    assert intro == r["steps"][0]
    assert intro.startswith("Let ")
    r2 = _solve_friendly(PROFIT_Q)
    intro2 = _intro_for(r2, PROFIT_Q)
    assert intro2 is not None and "CP" in intro2


def test_no_intro_for_bare_computations():
    for q in ("What is 15% of 240?", "Solve x^2 - 5x + 6 = 0",
              "Find the area of a circle with radius 7 cm.",
              "Find the mean of 3, 6, 9, 12."):
        r = _solve_friendly(q)
        assert _intro_for(r, q) is None, q


def test_no_intro_for_fallback_results():
    r = _solve_friendly("what is HCF")
    assert r.get("fallback_kind") == "concept"
    assert _intro_for(r, "what is HCF") is None


def _rendered_steps(result):
    """The steps the chat actually shows: the Wave-25 rule
    (a trailing step that only restates the answer is
    dropped — the answer line carries it) plus the Wave-68
    intro lift (the framing first step moves above the
    list, shown once as the intro line)."""
    import re as _re
    steps = [str(s) for s in (result.get("steps") or [])]
    ans = str(result.get("answer", "")).strip()
    if steps and ans:
        last = _re.sub(r"^\s*(solution|answer)\s*:\s*", "",
                       steps[-1], flags=_re.I).strip()
        if last and last == ans:
            steps.pop()
    return steps


def test_answer_never_duplicated_in_intro_or_steps():
    for q in (HINDI_TRAIN, PROFIT_Q, "Solve x^2 - 5x + 6 = 0",
              "What is 15% of 240?"):
        r = _solve_friendly(q)
        ans = str(r["answer"]).strip()
        intro = _intro_for(r, q)
        assert not intro or ans not in intro
        shown = _rendered_steps(r)
        if intro and shown and shown[0] == intro:
            shown = shown[1:]
        for step in shown:
            s = step.strip()
            assert s != ans
            assert s.lower() not in (f"solution: {ans}".lower(),
                                     f"answer: {ans}".lower())


def test_api_solve_payload_carries_intro_and_plain(client):
    d = client.post("/api/solve",
                    json={"question": HINDI_TRAIN}).get_json()
    assert d["ok"] is True
    assert d["intro"] and d["intro"].startswith("Let ")
    assert not d["result"].get("plain_reply")
    d = client.post("/api/solve",
                    json={"question": "If tu gfuf"}).get_json()
    assert d["ok"] is True
    assert d["result"].get("plain_reply") is True
    assert d["result"]["answer"] == "Answer not found."
    assert d["intro"] is None


# --- 3. The chat template ------------------------------------

def test_chat_template_plain_and_intro_hooks():
    assert "plain-reply" in INDEX
    assert "answer-intro" in INDEX
    assert "result.plain_reply" in INDEX


def test_chat_template_no_explanation_or_notebook():
    # The answer-restating explanation paragraph and the
    # notebook/copy-style panel are out of the chat flow.
    assert 'className = "explain"' not in INDEX
    assert '"steps notebook"' not in INDEX
    assert "makeHwToggle" not in INDEX
    assert "steps-tools" not in INDEX


def test_chat_template_no_example_chips():
    # Wave 69 (Suraj): example-question chips removed — the
    # empty state must carry no pre-written questions at all.
    assert 'id="example-chips"' not in INDEX
    assert INDEX.count('class="example-chip"') == 0
    assert 'class="example-chip"' not in INDEX


def test_sample_questions_all_solve():
    assert _solve_friendly("Solve x² - 5x + 6 = 0")["answer"] \
        == "x = 2, x = 3"
    assert _solve_friendly("15% of 240 kitna hoga?")["answer"] \
        == "36"
    assert "90 km/h" in _solve_friendly(
        "एक ट्रेन 360 km की दूरी 4 घंटे में तय करती है। "
        "उसकी चाल ज्ञात कीजिए।")["answer"]
    # Wave 99: radius 7 -> pi = 22/7 -> "154" (was 49·pi).
    assert "154" in _solve_friendly(
        "Find the area of a circle with radius 7 cm.")["answer"]


def test_wave68_pins_and_css():
    assert "v='54'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v31"' in SW
    assert ".example-chip" not in CSS
    assert ".plain-reply" in CSS
    assert ".answer-intro" in CSS
    assert ".step-verify" in CSS
