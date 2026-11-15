"""Wave 67 (Suraj, 15 Nov 2026): the SHORT not-found fallback.

His complaint, with phone screenshots: he typed gibberish
("If tu gfuf") and Ganitra answered with a HUGE card —
mixed-language guide text, a notebook-style "Questions I
solve for sure…" panel, a long final-answer paragraph and
Teacher's Advice. His order: "jab kuch bhi likh diya to itna
bada answer dene ki jarurat nahi hai — bas 'answer not found'
bol do, itna hi."

The rule proven here:
- anything NOT solved (gibberish, a similar-example/guide
  outcome, a real question the solver + bank + AI chain
  could not solve) -> fallback_kind == "not_found" and the
  ENTIRE answer is one short line in the question's
  language, with no steps and no extras;
- Merge-5 (decided rule 1): greetings / small talk and
  vague asks are the exception — they get Wave 68's friendly
  per-flavour ONE line (kinds "greeting" / "vague", plain
  rendering), NOT "Answer not found." — see
  test_merge5_greetings_and_vague_get_friendly_lines below;
- the maths-only guards keep their own one-line wording
  (plain=True): science keeps its formula-guidance steps in
  the payload (the guard is not broken), nonmaths is trimmed
  to the guard sentence;
- solved answers (solver / salvage / bank / concept / AI)
  are completely unchanged.
"""
import pytest

from api import _solve_friendly
from fallback import fallback_answer, with_fallback
from i18n import (advice_for, explanation_for, get_strings,
                  result_is_plain, teach_for)
from solver.router import solve_question


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


# --- 1. Gibberish -> the one line; greetings / vague -> ----
# --- Merge-5 rule 1: Wave 68's friendly one line ------------

@pytest.mark.parametrize("question,line", [
    ("If tu gfuf", "Answer not found."),
    ("asdf qwer", "Answer not found."),
    ("कुछ भी लिख दिया बकवास", "उत्तर नहीं मिला।"),
])
def test_not_solved_inputs_get_exactly_one_line(question, line):
    res = fallback_answer(question)
    assert res.get("fallback_kind") == "not_found"
    assert res.get("answer") == line
    assert res.get("steps") == []
    assert result_is_plain(res)


# Merge-5 (decided rule 1): the four cases Wave 67 used to
# collapse to the not-found line — two greetings and two
# vague asks — now get Wave 68's friendly per-flavour ONE
# line instead, still plain, still no steps or extras. A
# friendly hello deserves a friendly line, not "not found".
@pytest.mark.parametrize("question,kind,line", [
    ("hello bro", "greeting",
     "Hello! 😊 I'm doing great. Send me a maths question "
     "and I'll solve it step by step."),
    ("thank you", "greeting",
     "You're welcome! 😊 Send me another maths question "
     "any time."),
    ("नमस्ते", "greeting",
     "नमस्ते! 😊 मैं बिल्कुल ठीक हूँ। अपना गणित का सवाल "
     "भेजिए — मैं चरण-दर-चरण हल दूँगा।"),
    ("samjhao", "vague",
     "Bilkul! 😊 Apna maths ka sawal poora likh kar bhejo "
     "— jaise 'solve 2x + 3 = 7' — main step-by-step hal "
     "dunga."),
    ("ye wala samjhao", "vague",
     "Bilkul! 😊 Apna maths ka sawal poora likh kar bhejo "
     "— jaise 'solve 2x + 3 = 7' — main step-by-step hal "
     "dunga."),
])
def test_merge5_greetings_and_vague_get_friendly_lines(
        question, kind, line):
    res = fallback_answer(question)
    assert res.get("fallback_kind") == kind
    assert res.get("answer") == line
    assert res.get("steps") == []
    assert result_is_plain(res)
    assert res.get("plain_reply") is True


def test_unsolvable_real_question_gets_the_line():
    # The Wave 37/41 ages problem: a real-looking maths
    # question the solver + bank cannot solve and (with no AI
    # keys configured) the AI chain cannot either.
    res = fallback_answer(
        "Ten years ago, a father was twelve times as old as "
        "his son and ten years hence, he will be twice as old "
        "as his son. Find their present ages.")
    assert res.get("fallback_kind") == "not_found"
    assert res.get("answer") == "Answer not found."


def test_not_found_line_follows_ui_language():
    # A Roman gibberish question under a bn/ta/te UI still
    # gets that UI's one-liner (the i18n answer_not_found key).
    for lang, line in (("bn", "উত্তর পাওয়া যায়নি।"),
                       ("ta", "பதில் கிடைக்கவில்லை."),
                       ("te", "సమాధానం దొరకలేదు.")):
        res = fallback_answer("asdf qwer", lang=lang)
        assert res.get("answer") == line, lang
    # Devanagari beats the UI language; Marathi UI keeps its
    # own Devanagari line.
    res = fallback_answer("कुछ भी बकवास लिख दिया", lang="mr")
    assert res.get("answer") == "उत्तर सापडले नाही."
    res = fallback_answer("कुछ भी बकवास लिख दिया", lang="bn")
    assert res.get("answer") == "उत्तर नहीं मिला।"


def test_answer_not_found_key_in_all_six_languages():
    for lang in ("en", "hi", "bn", "mr", "ta", "te"):
        assert get_strings(lang)["answer_not_found"]
    assert get_strings("en")["answer_not_found"] == \
        "Answer not found."
    assert get_strings("hi")["answer_not_found"] == \
        "उत्तर नहीं मिला।"


# --- 2. The guards: one line, own wording, not broken ---------

def test_science_guard_one_line_in_chat_payload_intact():
    q = ("A ray of light travels from medium A to medium B. "
         "The refractive index of medium B relative to medium "
         "A is 1.5, and the speed of light in medium A is "
         "2 x 10^8 m/s. What is the speed of light in medium B?")
    res = with_fallback(q, solve_question(q))
    assert res.get("fallback_kind") == "science"
    assert res.get("plain") is True
    assert "Ganitra only solves Maths" in res["answer"]
    # The guard's formula guidance is still in the payload
    # (full-solution page); only the chat rendering shrank.
    assert "refractive index" in " ".join(res.get("steps") or [])


def test_nonmaths_guard_is_one_line():
    res = fallback_answer("what is the capital of india")
    assert res.get("fallback_kind") == "nonmaths"
    assert res.get("plain") is True
    assert res.get("answer") == (
        "That's not a maths question — Ganitra only "
        "solves Maths.")
    res = fallback_answer("capital of India kya hai")
    assert res.get("answer") == (
        "Ye sawal maths ka nahi hai — Ganitra sirf Maths "
        "ke sawal hal karta hai।")


# --- 3. No extras ride along with a one-line response ---------

def test_plain_results_get_no_explanation_advice_teach():
    for res in (fallback_answer("If tu gfuf"),
                fallback_answer("what is the speed of light"),
                fallback_answer("capital of India kya hai")):
        assert explanation_for(res, "en") == ""
        assert advice_for(res, "en") == ""
        assert teach_for(res, "en") == []


def test_api_gibberish_response_is_minimal(client):
    body = client.post(
        "/api/solve", json={"question": "If tu gfuf"}).get_json()
    assert body["ok"] is True
    result = body["result"]
    assert result.get("fallback_kind") == "not_found"
    assert result.get("answer") == "Answer not found."
    assert body["explanation"] == ""
    assert body["advice"] == ""
    assert body["methods"] == []
    assert body["teach"] == []


# --- 4. Solved answers are completely unchanged ---------------

def test_solved_answers_unchanged():
    res = _solve_friendly(
        "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती "
        "है। यदि यह चाल 5 km/h अधिक होती, तो वह उसी दूरी को "
        "तय करने में 1 घंटा कम समय लेती। रेलगाड़ी की चाल "
        "ज्ञात कीजिए।")
    assert "fallback" not in res
    assert "40 km/h" in str(res.get("answer", ""))
    assert res.get("steps")

    res = _solve_friendly("x² - 5x + 6 = 0")
    assert "fallback" not in res
    assert str(res.get("answer", "")) == "x = 2, x = 3"
    assert explanation_for(res, "en")
    assert advice_for(res, "en")
    assert teach_for(res, "en")

    res = _solve_friendly(
        "train 80 km/h ki speed se 240 km kitne ghante me "
        "jayegi?")
    assert "fallback" not in res
    assert "3 hours" in str(res.get("answer", ""))


def test_concept_card_unchanged():
    res = fallback_answer("pythagoras theorem kya hai")
    assert res.get("fallback_kind") == "concept"
    assert not result_is_plain(res)
    assert len(res.get("steps") or []) >= 3


def test_api_solved_response_keeps_full_payload(client):
    body = client.post(
        "/api/solve",
        json={"question": "x^2 - 5x + 6 = 0"}).get_json()
    assert body["ok"] is True
    result = body["result"]
    assert "fallback_kind" not in result or \
        not result.get("fallback_kind")
    assert result.get("steps")
    assert body["explanation"]
    assert body["advice"]
    assert body["methods"]  # alternate methods still offered
    assert body["teach"]
