"""Wave 107 (Suraj, 17 Nov 2026): an explicit language request
inside a chat message OVERRIDES the question's language.

His words: "agar chat mai koi bolta hai ans hindi mai chahiye
toh hindi mai dena hai, chahe question english mai diya ho
usne." The standing Wave-20 rule (answer in the language the
student types in) is extended, not replaced:

- a request-shaped phrase naming Hindi / English / Hinglish
  (in English, Roman Hinglish or Devanagari) decides the
  answer language — UI strings, explanation, advice, the AI
  fallback prompt and the one-line not-found line all follow;
- the request phrase is stripped before solving, so it can
  never break the solver or the bank's exact match;
- a language name that is merely question CONTENT (a word
  problem about Hindi/English textbooks) must NOT fire — the
  matcher needs a request shape, not a keyword;
- with no request present, behaviour is the pre-Wave-107 one.
"""
import pytest

import fallback
import gemini_fallback
from fallback import _ai_lang, _not_found_line, fallback_answer
from langdetect_local import detect_language_request


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _ask(client, question):
    return client.post(
        "/api/solve", json={"question": question}).get_json()


TRIANGLE_EN = "What is the sum of angles of a triangle?"
TRIANGLE_HI = "त्रिभुज के कोणों का योग कितना होता है?"
TRAIN_HINGLISH = ("train 80 km/h ki speed se 240 km kitne "
                  "ghante me jayegi?")
AGES = ("Ten years ago, a father was twelve times as old as "
        "his son and ten years hence, he will be twice as old "
        "as his son. Find their present ages.")
DEVANAGARI = ("ऀ", "ॿ")


def _has_devanagari(text):
    return any(DEVANAGARI[0] <= ch <= DEVANAGARI[1]
               for ch in str(text or ""))


# --- 1. The matcher: request shapes fire, with cleaning ------

@pytest.mark.parametrize("question,target,cleaned", [
    ("What is the sum of angles of a triangle? Answer in Hindi",
     "hi", "What is the sum of angles of a triangle"),
    ("Hindi me answer do: 2+2 kitna hoga?",
     "hi", "2+2 kitna hoga"),
    ("2+2 batao hindi me", "hi", "2+2"),
    ("hindi mai chahiye, 5+5 kitna hoga", "hi", "5+5 kitna hoga"),
    ("हिंदी में जवाब दो: त्रिभुज के कोणों का योग कितना होता है?",
     "hi", "त्रिभुज के कोणों का योग कितना होता है"),
    ("hindi me samjhao — sin 30 ka value",
     "hi", "sin 30 ka value"),
    ("ans hindi me: 3x+5=20", "hi", "3x+5=20"),
    ("hindime batao 2+2", "hi", "2+2"),
    ("जवाब हिंदी में दीजिए। 2+2 कितना होगा?",
     "hi", "2+2 कितना होगा"),
    ("Hindi answer do — 7+8 kitna hoga", "hi", "7+8 kitna hoga"),
    ("What is 15% of 240? answer in English",
     "en", "What is 15% of 240"),
    ("त्रिभुज के कोणों का योग कितना होता है? answer in English",
     "en", "त्रिभुज के कोणों का योग कितना होता है"),
    ("English me batao, 2+2 kitna hoga?", "en", "2+2 kitna hoga"),
    ("in english please — what is 2+2?", "en", "what is 2+2"),
    ("अंग्रेज़ी में दो: 2+2 कितना होगा?", "en", "2+2 कितना होगा"),
    ("mujhe english jawab chahiye, 9+9 kitna hoga",
     "en", "mujhe 9+9 kitna hoga"),
    ("hinglish me samjhao, 2+2 kya hota hai",
     "hinglish", "2+2 kya hota hai"),
    ("Hinglish me answer do: 5+5", "hinglish", "5+5"),
])
def test_request_shapes_fire_and_clean(question, target, cleaned):
    got = detect_language_request(question)
    assert got is not None, question
    assert got[0] == target
    assert got[1] == cleaned


def test_request_only_message_cleans_to_empty():
    # The message is ONLY a request: callers keep the original
    # text for the pipeline and apply just the language.
    assert detect_language_request("Hindi me answer do") == \
        ("hi", "")


def test_last_request_wins():
    # A student correcting themselves mid-message: the later
    # request is the live one.
    got = detect_language_request(
        "pehle hindi me, nahi english me batao: 2+2")
    assert got is not None
    assert got[0] == "en"
    assert "english" not in got[1].lower()


# --- 2. The matcher: content mentions never fire -------------

@pytest.mark.parametrize("question", [
    # The textbook word problem: both language names are pure
    # content, the ask verb is far away from both.
    "A Hindi textbook costs Rs 200 and an English textbook "
    "costs Rs 150. What is the total cost?",
    "English book ki price batao — Rs 300 hai, total kitna?",
    # Sets problems: students studying IN Hindi / English —
    # the postposition is content, mid-message, no request
    # word near it.
    "एक कक्षा में 20 छात्र हिंदी में और 15 छात्र अंग्रेज़ी "
    "में पढ़ते हैं। कुल कितने छात्र हैं?",
    "20 ladke hindi me aur 15 english me padhte hain, kul "
    "kitne ladke hain?",
    "What is the Hindi word for angle?",
    # Plain questions in all three languages.
    "What is the sum of angles of a triangle?",
    "त्रिभुज के कोणों का योग बताओ",
    "2+2 kitna hoga batao",
    "Find 15% of 240, the number of Hindi books in a library",
])
def test_content_mentions_do_not_fire(question):
    assert detect_language_request(question) is None, question


# --- 3. End-to-end: the override decides the answer language -

def test_english_question_hindi_request_answers_in_hindi(client):
    body = _ask(client, TRIANGLE_EN + " Answer in Hindi")
    assert body["ok"] is True
    assert body["language"] == "hi"
    assert body["language_switched"] is True
    assert body["result"]["answer"] == "180°"
    assert _has_devanagari(body["explanation"])
    assert _has_devanagari(body["advice"])


def test_hindi_question_english_request_answers_in_english(
        client):
    body = _ask(client, TRIANGLE_HI + " answer in English")
    assert body["ok"] is True
    assert body["language"] == "en"
    assert body["result"]["answer"] == "180°"
    assert not _has_devanagari(body["explanation"])
    assert not _has_devanagari(body["advice"])


def test_hinglish_question_english_request_answers_in_english(
        client):
    body = _ask(client, TRAIN_HINGLISH + " answer in English")
    assert body["ok"] is True
    assert body["language"] == "en"
    assert "3 hours" in body["result"]["answer"]
    assert not _has_devanagari(body["explanation"])


def test_english_question_hinglish_request(client):
    # A Hinglish request lands where a Hinglish question lands
    # today: the "hi" session language.
    body = _ask(client, "What is 15% of 240? hinglish me samjhao")
    assert body["ok"] is True
    assert body["language"] == "hi"
    assert body["result"]["answer"] == "36"


def test_request_phrase_never_breaks_solving(client):
    # Same value with and without the phrase, on questions
    # whose phrasing the solvers are sensitive to.
    plain = _ask(client, TRIANGLE_EN)
    asked = _ask(client, TRIANGLE_EN + " Answer in Hindi")
    assert asked["result"]["answer"] == \
        plain["result"]["answer"] == "180°"
    body = _ask(client, "3x + 5 = 20, hindi me batao")
    assert body["result"]["answer"] == "x = 5"
    body = _ask(client, "What is 15% of 240? Answer in Hindi")
    assert body["result"]["answer"] == "36"


def test_request_switches_session_like_a_detection(client):
    # The request moves the session language (Wave 9's rule
    # for detections); a language-neutral follow-up keeps it,
    # a solidly-detected other language moves it back.
    _ask(client, TRIANGLE_EN + " Answer in Hindi")
    body = _ask(client, "15% of 240")
    assert body["language"] == "hi"
    assert _has_devanagari(body["explanation"])
    body = _ask(client, "What is 15% of 240?")
    assert body["language"] == "en"


def test_classic_solve_page_honours_the_request(client):
    html = client.post(
        "/solve",
        data={"question": TRIANGLE_EN + " Answer in Hindi"}
    ).get_data(as_text=True)
    assert "180" in html
    assert _has_devanagari(html)
    html = client.post(
        "/solve",
        data={"question": TRIANGLE_HI + " answer in English"}
    ).get_data(as_text=True)
    assert "Using the relevant area/volume formulae" in html
    assert "संबंधित क्षेत्रफल" not in html


# --- 4. The not-found line honours the request ---------------

def test_not_found_line_follows_the_request(client):
    # One client, one process: the sequence also proves the
    # negative cache is keyed per language — each ask must
    # get ITS line, including the repeats served from cache.
    body = _ask(client, AGES + " Answer in Hindi")
    assert body["result"]["answer"] == "उत्तर नहीं मिला।"
    body = _ask(client, AGES + " hinglish me batao")
    assert body["result"]["answer"] == "Answer nahi mila."
    body = _ask(client, AGES)
    assert body["result"]["answer"] == "Answer not found."
    body = _ask(client, AGES + " Answer in Hindi")
    assert body["result"]["answer"] == "उत्तर नहीं मिला।"
    body = _ask(client, AGES)
    assert body["result"]["answer"] == "Answer not found."


def test_not_found_line_unit_level():
    q = "some unsolved thing"
    assert _not_found_line(q, False, "en", "hi") == \
        "उत्तर नहीं मिला।"
    assert _not_found_line(q, True, "hi", "en") == \
        "Answer not found."
    assert _not_found_line(q, False, "en", "hinglish") == \
        "Answer nahi mila."
    # No request: the pre-Wave-107 choices, untouched.
    res = fallback_answer(AGES)
    assert res["answer"] == "Answer not found."
    res = fallback_answer(AGES, lang_request="hi")
    assert res["answer"] == "उत्तर नहीं मिला।"
    res = fallback_answer(AGES, lang_request="hinglish")
    assert res["answer"] == "Answer nahi mila."
    res = fallback_answer(AGES, lang_request="en")
    assert res["answer"] == "Answer not found."


# --- 5. The AI fallback prompt gets the requested language ---

def test_ai_lang_mapping():
    assert _ai_lang(True, None) == "hi"      # pre-107 rule
    assert _ai_lang(False, None) is None     # pre-107 rule
    assert _ai_lang(False, "hi") == "hi"
    assert _ai_lang(True, "en") == "en"
    assert _ai_lang(False, "hinglish") == "hinglish"


def test_gemini_prompt_names_the_requested_language():
    for lang, needle in (
            ("en", "answer in English"),
            ("hi", "answer in Hindi"),
            ("hinglish", "Hinglish (Hindi written in "
                         "Roman/English letters)")):
        prompt = gemini_fallback._build_prompt("2+2?", lang)
        assert needle in prompt
    # No language passed: no instruction line at all (the
    # prompt's own same-language rule governs), as before.
    prompt = gemini_fallback._build_prompt("2+2?", None)
    assert "student's language is" not in prompt


def test_with_fallback_forwards_request_to_ai_brain(monkeypatch):
    seen = {}

    def fake_gemini(question, hindi, lang_request=None):
        seen["lang_request"] = lang_request
        return {"type": "Ganitra", "op": "gemini",
                "answer": "42", "steps": ["working"],
                "fallback": True, "fallback_kind": "gemini",
                "ai_generated": True}

    monkeypatch.setattr(fallback, "_gemini_answer", fake_gemini)
    failed = {"op": "error",
              "answer": "Could not solve this one: x",
              "steps": []}
    res = fallback.with_fallback(AGES, dict(failed), lang="en",
                                 lang_request="hinglish")
    assert res["fallback_kind"] == "gemini"
    assert seen["lang_request"] == "hinglish"
    res = fallback.with_fallback(AGES, dict(failed), lang="en")
    assert seen["lang_request"] is None


# --- 6. No request: byte-identical old behaviour -------------

def test_no_request_regressions(client):
    body = _ask(client, TRIANGLE_EN)
    assert body["language"] == "en"
    assert body["language_switched"] is False
    assert body["result"]["answer"] == "180°"

    body = _ask(client, TRIANGLE_HI)
    assert body["language"] == "hi"
    assert body["result"]["answer"] == "180°"

    body = _ask(client, TRAIN_HINGLISH)
    assert body["language"] == "hi"
    assert "3 hours" in body["result"]["answer"]


def test_content_mention_end_to_end(client):
    # The textbook problem mentions both languages as content:
    # no override fires, the session stays English, and the
    # (unsolved) answer is the ENGLISH not-found line.
    body = _ask(client,
                "A Hindi textbook costs Rs 200 and an English "
                "textbook costs Rs 150. What is the total cost?")
    assert body["language"] == "en"
    assert body["result"]["answer"] == "Answer not found."
    # A solvable content mention solves normally, in English.
    body = _ask(client,
                "Find 15% of 240, the number of Hindi books "
                "in a library")
    assert body["language"] == "en"
    assert body["result"]["answer"] == "36"
