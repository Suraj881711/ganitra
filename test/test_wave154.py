"""Wave 154 (Suraj, 18 Nov 2026): the normal-baat +
maths GUIDANCE layer (guidance.py, hooked into
fallback.with_fallback right after the Wave 111 meta
layer).

Suraj's order: Ganitra should talk a little like a
person (small talk deserves a human reply, not the
not-found line), and when a student asks about the
future of maths — scope, 12th ke baad kya, maths lu ya
biology, entrance exams — or about exam preparation,
or says "mann nahi lag raha", Ganitra should GUIDE
them like a teacher.

Pinned here:
  1. the BAAT battery (small talk, EN/Hinglish/Hindi),
  2. the GUIDANCE battery (7 authored intents x 3
     flavours, incl. the first-class EXAM PREPARATION
     and MOTIVATION intents),
  3. content sanity: every career card names the main
     routes; NO salary figures / percentages /
     guarantees anywhere (scanned),
  4. the anti-hijack battery (Wave 148's lesson): a
     real problem, a concept ask, an MCQ set or a
     follow-up ALWAYS wins over both layers,
  5. routing guards: non-maths still refused, other
     fields' careers stay out of scope, Wave 111 meta
     keeps its own territory,
  6. detail on demand: a guidance card expands with
     its authored detail lines (one-message ask and
     the bare follow-up, Wave 136/148 machinery).
"""
import pytest

import fallback
from detail import expand_detail
from fallback import fallback_answer
from followups import is_solved_result
from guidance import BAAT, GUIDANCE, baat_result, \
    guidance_detail_steps, guidance_result, wave154_result

DEV = ("ऀ", "ॿ")


def _has_dev(text):
    return any(DEV[0] <= ch <= DEV[1] for ch in str(text or ""))


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the AI legs must stay inert in this
    battery."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _solve(client, question):
    return client.post(
        "/api/solve", json={"question": question}).get_json()


def _kind(result):
    return result.get("fallback_kind")


# ---------------------------------------------------------------------------
# 0. The curated data itself: coverage + content sanity
# ---------------------------------------------------------------------------

def test_guidance_coverage():
    ids = {e["id"] for e in GUIDANCE}
    assert ids == {
        "scope_career", "after_12th", "subject_choice",
        "entrance_exams", "improve", "exam_prep",
        "motivation",
    }
    for entry in GUIDANCE:
        for flavour in ("en", "roman", "dev"):
            text = entry[flavour]
            assert text["answer"].strip()
            assert len(text["steps"]) >= 3
            assert len(text["detail"]) >= 2
            assert guidance_detail_steps(
                entry["id"], flavour) == list(text["detail"])


def test_baat_coverage():
    ids = {e["id"] for e in BAAT}
    assert ids == {
        "haal", "doing", "can_do", "robot", "creator",
        "age_place", "compliment", "dost", "love", "bore",
        "tired", "fun", "mood",
    }
    for entry in BAAT:
        for flavour in ("en", "roman", "dev"):
            line = entry[flavour]
            assert line.strip()
            # 1-2 lines max, warm and short.
            assert len(line) <= 340


def _all_wave154_texts():
    texts = []
    for entry in GUIDANCE:
        for flavour in ("en", "roman", "dev"):
            texts.append(entry[flavour]["answer"])
            texts.extend(entry[flavour]["steps"])
            texts.extend(entry[flavour]["detail"])
    for entry in BAAT:
        for flavour in ("en", "roman", "dev"):
            texts.append(entry[flavour])
    return texts


def test_no_salary_no_guarantee_no_fake_stats():
    """Suraj's content rule: guidance stays qualitative
    — no invented salary figures, no percentages, no
    success guarantees, in ANY flavour."""
    banned = (
        "₹", "$", "lakh", "LPA", "salary", "तनख्वाह",
        "वेतन", "guarantee", "गारंटी", "pakka", "पक्का",
        "100%", "zaroor", "definitely",
    )
    for text in _all_wave154_texts():
        for word in banned:
            assert word not in text, (word, text[:60])


def test_career_cards_name_the_main_routes():
    scope = next(e for e in GUIDANCE
                 if e["id"] == "scope_career")
    blob = " ".join([scope["en"]["answer"]]
                    + scope["en"]["steps"]
                    + scope["en"]["detail"])
    for route in ("JEE", "Data Science", "B.Sc.",
                  "Actuarial", "ISI", "NDA"):
        assert route in blob
    after = next(e for e in GUIDANCE
                 if e["id"] == "after_12th")
    blob = " ".join([after["en"]["answer"]]
                    + after["en"]["steps"]
                    + after["en"]["detail"])
    for route in ("JEE Main", "JEE Advanced", "CUET",
                  "ISI", "NDA", "B.Arch"):
        assert route in blob
    exams = next(e for e in GUIDANCE
                 if e["id"] == "entrance_exams")
    blob = " ".join([exams["en"]["answer"]]
                    + exams["en"]["steps"]
                    + exams["en"]["detail"])
    for route in ("JEE Main", "JEE Advanced", "CUET",
                  "ISI", "CMI", "NDA", "BITSAT"):
        assert route in blob


def test_exam_prep_content_pins():
    """First-class intent 1 (Suraj, 18 Nov): practical
    exam preparation — weak chapters first, daily
    revision rounds, previous papers + mock tests via
    Ganitra's own Papers / Chapter Test / Practice,
    likh-likh practice, the mistake copy, a timetable
    in the detail lines."""
    entry = next(e for e in GUIDANCE
                 if e["id"] == "exam_prep")
    en = " ".join(entry["en"]["steps"]
                  + entry["en"]["detail"]).lower()
    assert "weak chapter" in en
    assert "mock" in en
    assert "mistake" in en
    assert "timetable" in en
    roman = " ".join(entry["roman"]["steps"]
                     + entry["roman"]["detail"]).lower()
    assert "weak chapter" in roman
    assert "galtiyon ki copy" in roman
    assert "timetable" in roman
    for flavour in ("en", "roman", "dev"):
        blob = " ".join(entry[flavour]["steps"]
                        + entry[flavour]["detail"])
        assert "Papers" in blob
        assert "Chapter Test" in blob


def test_motivation_content_pins():
    """First-class intent 2 (Suraj, 18 Nov): honest
    motivation — one small next step, and the
    talk-to-an-elder line, in every flavour."""
    entry = next(e for e in GUIDANCE
                 if e["id"] == "motivation")
    en = " ".join(entry["en"]["steps"])
    assert "5 questions" in en
    assert "parent" in en and "teacher" in en
    roman = " ".join(entry["roman"]["steps"])
    assert "5 sawal" in roman
    assert "maa-baap" in roman and "teacher" in roman
    dev = " ".join(entry["dev"]["steps"])
    assert "5 सवाल" in dev
    assert "माँ-बाप" in dev and "शिक्षक" in dev


# ---------------------------------------------------------------------------
# 1. BAAT battery — small talk in the student's language
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,baat_id,flavour", [
    ("kya haal hai", "haal", "roman"),
    ("what are you doing", "doing", "en"),
    ("tum kya kar sakte ho", "can_do", "roman"),
    ("तुम क्या कर सकते हो", "can_do", "dev"),
    ("are you a robot", "robot", "en"),
    ("kisne banaya tumhe", "creator", "roman"),
    ("tumhari age kya hai", "age_place", "roman"),
    ("tum bahut ache ho", "compliment", "roman"),
    ("tum mere dost ho", "dost", "roman"),
    ("i love you", "love", "en"),
    ("bore ho raha hai", "bore", "roman"),
    ("बोर हो रहा है", "bore", "dev"),
    ("neend aa rahi hai", "tired", "roman"),
    ("maza aa raha hai", "fun", "roman"),
    ("mood kharab hai", "mood", "roman"),
    ("thank you so much, you helped me a lot",
     "thanks", "en"),
])
def test_baat_intents(question, baat_id, flavour):
    r = baat_result(question)
    assert r is not None, question
    assert r["fallback_kind"] == "baat"
    assert r["baat_id"] == baat_id
    assert r["plain_reply"] is True
    assert r["steps"] == []
    if flavour == "dev":
        assert _has_dev(r["answer"])
    if flavour == "roman":
        assert not _has_dev(r["answer"])


def test_baat_lines_are_short():
    for question in ("bore ho raha hai",
                     "tum kya kar sakte ho",
                     "are you a robot"):
        r = baat_result(question)
        assert len(r["answer"]) <= 340


# ---------------------------------------------------------------------------
# 2. GUIDANCE battery — 7 intents x flavours
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,gid,flavour", [
    # scope / careers
    ("maths me kya scope hai", "scope_career", "roman"),
    ("what is the scope of maths", "scope_career", "en"),
    ("गणित में स्कोप क्या है", "scope_career", "dev"),
    # after 12th (Suraj's own phrasing first)
    ("12th ke baad maths leke kya kar sakte hai",
     "after_12th", "roman"),
    ("after 12th what can I do with maths",
     "after_12th", "en"),
    ("बारहवीं के बाद क्या कर सकते हैं",
     "after_12th", "dev"),
    ("12th ke baad kya kar sakte hai",
     "after_12th", "roman"),
    # subject choice
    ("11th me maths lu ya biology",
     "subject_choice", "roman"),
    ("should I take maths or biology",
     "subject_choice", "en"),
    ("गणित लूँ या जीव विज्ञान",
     "subject_choice", "dev"),
    ("pcm ya pcb lu", "subject_choice", "roman"),
    # entrance exams
    ("jee main kya hota hai", "entrance_exams", "roman"),
    ("what is JEE Main", "entrance_exams", "en"),
    ("प्रवेश परीक्षा कौन सी होती है",
     "entrance_exams", "dev"),
    # improve
    ("maths kaise improve karu", "improve", "roman"),
    ("mera maths weak hai", "improve", "roman"),
    ("गणित कैसे सुधार करूँ", "improve", "dev"),
    # exam preparation (first-class)
    ("exam aa gaye hai, kya karu", "exam_prep", "roman"),
    ("timetable kaise banau", "exam_prep", "roman"),
    ("कल परीक्षा है, क्या करूँ", "exam_prep", "dev"),
    ("how to make a timetable for exams",
     "exam_prep", "en"),
    # motivation (first-class)
    ("mann nahi lag raha padhai me", "motivation",
     "roman"),
    ("mai fail ho jaunga", "motivation", "roman"),
    ("exam ka stress hai", "motivation", "roman"),
    ("I feel demotivated", "motivation", "en"),
    ("मुझे पढ़ाई में मन नहीं लग रहा", "motivation",
     "dev"),
])
def test_guidance_intents(question, gid, flavour):
    r = guidance_result(question)
    assert r is not None, question
    assert r["fallback_kind"] == "guidance"
    assert r["guidance_id"] == gid
    assert r["guidance_flavour"] == flavour
    assert len(r["steps"]) >= 3
    if flavour == "dev":
        assert _has_dev(r["answer"])
    if flavour == "roman":
        assert not _has_dev(r["answer"])


def test_guidance_cards_are_not_solved_results():
    """No answer box, no follow-up chips on a guidance
    card or a baat line (the followups predicate every
    renderer gates on)."""
    g = guidance_result("maths me kya scope hai")
    assert is_solved_result(g) is False
    b = baat_result("bore ho raha hai")
    assert is_solved_result(b) is False


# ---------------------------------------------------------------------------
# 3. Anti-hijack battery — a real ask ALWAYS wins
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    # greeting + a real problem: the problem wins
    "hi, 2+2 kya hota hai",
    # guidance-shaped opener + a table request
    "maths me scope hai? aur 5 ka table batao",
    # exam-prep opener + a real computation
    "exam ki taiyari kar raha hu, 15% of 200 batao",
    # small-talk opener + a real problem
    "bore ho raha hai, HCF of 12 and 18 batao",
    # a bare solve-noun ask riding on small talk
    "kal exam hai, HCF batao",
    # concept asks are the concept/solver layers'
    "trigonometry samjhao",
    "circle ka area kya hai",
    # an exam-flavoured PROBLEM stays with the solver
    "jee main me aaya tha: derivative of x^2 batao",
    # a number-series ask is not a career ask
    "12 ke baad kya aayega",
    # an MCQ set is a problem, whatever words it carries
    "maths me scope hai? (a) 2 (b) 4 (c) 6 (d) 8",
    # follow-up / test shapes are not guidance
    "uska answer batao",
    "test do",
    "aur example do",
])
def test_wave154_never_hijacks(question):
    assert wave154_result(question) is None, question
    r = fallback_answer(question)
    assert _kind(r) not in ("baat", "guidance"), question


def test_hijack_battery_still_solves():
    r = fallback_answer("hi, 2+2 kya hota hai")
    assert "4" in str(r.get("answer"))
    r = fallback_answer(
        "exam ki taiyari kar raha hu, 15% of 200 batao")
    assert "30" in str(r.get("answer"))
    r = fallback_answer(
        "bore ho raha hai, HCF of 12 and 18 batao")
    assert "6" in str(r.get("answer"))


def test_exam_prep_with_real_question_question_wins():
    """The follow-up order's own anti-hijack shape: an
    'exam ki taiyari' message WITH a real question —
    the question is answered, not the guidance card."""
    r = fallback_answer(
        "exam ki taiyari kar raha hu, ye batao "
        "20% of 150 kitna hai")
    assert _kind(r) not in ("baat", "guidance")
    assert "30" in str(r.get("answer"))


# ---------------------------------------------------------------------------
# 4. Routing guards — scope discipline
# ---------------------------------------------------------------------------

def test_nonmaths_still_refused():
    r = fallback_answer("What is the capital of France?")
    assert _kind(r) == "nonmaths"


def test_other_field_careers_stay_out_of_scope():
    for question in ("doctor kaise bane",
                     "biology lekar kya kar sakte hai",
                     "12th ke baad doctor kaise bane",
                     "commerce me kya scope hai"):
        assert guidance_result(question) is None, question
        r = fallback_answer(question)
        assert _kind(r) not in ("baat", "guidance"), \
            question


def test_other_subject_prep_and_stress_stay_out():
    assert guidance_result(
        "history exam ka stress hai") is None
    # "timetable" must not smuggle a history ask past
    # the gate through the broad "table" maths signal.
    assert guidance_result(
        "history ki taiyari ke liye timetable batao") \
        is None
    r = fallback_answer("history exam ka stress hai")
    assert _kind(r) not in ("baat", "guidance")


def test_meta_keeps_its_territory():
    """Wave 111's cards are untouched: practice, weak
    (kamzor) and fear phrasings still serve the META
    advice cards, not Wave 154 guidance."""
    r = fallback_answer("maths ki practice kaise karu")
    assert _kind(r) == "advice"
    r = fallback_answer("maths me kamzor hu")
    assert _kind(r) == "advice"
    r = fallback_answer("maths se dar lagta hai")
    assert _kind(r) == "advice"
    r = fallback_answer(
        "Pythagoras theorem kisne banaya tha?")
    assert _kind(r) == "history"
    r = fallback_answer("hi")
    assert _kind(r) == "greeting"


def test_pipeline_serves_guidance_and_baat():
    r = fallback_answer("maths me kya scope hai")
    assert _kind(r) == "guidance"
    assert r["guidance_id"] == "scope_career"
    r = fallback_answer("exam aa gaye hai, kya karu")
    assert _kind(r) == "guidance"
    assert r["guidance_id"] == "exam_prep"
    r = fallback_answer("mann nahi lag raha padhai me")
    assert _kind(r) == "guidance"
    assert r["guidance_id"] == "motivation"
    r = fallback_answer("bore ho raha hai")
    assert _kind(r) == "baat"
    assert r["baat_id"] == "bore"


# ---------------------------------------------------------------------------
# 5. Detail on demand (Wave 136 machinery)
# ---------------------------------------------------------------------------

def test_expand_detail_appends_guidance_detail():
    card = guidance_result("maths me kya scope hai")
    short_steps = list(card["steps"])
    assert not any("ACET" in s for s in short_steps)
    expanded = expand_detail("maths me kya scope hai",
                             card)
    assert expanded is not card
    assert expanded["steps"][:len(short_steps)] \
        == short_steps
    assert any("ACET" in s for s in expanded["steps"])
    # the stored card itself is never mutated
    assert card["steps"] == short_steps


def test_expand_detail_keeps_the_cards_language():
    card = guidance_result("गणित में स्कोप क्या है")
    assert card["guidance_flavour"] == "dev"
    expanded = expand_detail("detail me batao", card)
    assert len(expanded["steps"]) > len(card["steps"])
    assert _has_dev(expanded["steps"][-1])


def test_client_detail_in_one_message(client):
    data = _solve(client, "maths me scope detail me "
                          "batao")
    result = data["result"]
    assert result["fallback_kind"] == "guidance"
    assert any("ACET" in s
               for s in result.get("steps") or [])


def test_client_bare_detail_followup_expands(client):
    first = _solve(client, "maths me kya scope hai")
    card = first["result"]
    assert card["fallback_kind"] == "guidance"
    short_len = len(card.get("steps") or [])
    assert not any("ACET" in s
                   for s in card.get("steps") or [])
    second = _solve(client, "detail me batao")
    result = second["result"]
    assert result["fallback_kind"] == "guidance"
    assert len(result.get("steps") or []) > short_len
    assert any("ACET" in s
               for s in result.get("steps") or [])


def test_client_bare_steps_after_guidance_not_reserved(
        client):
    """A bare STEPS ask after a guidance card is not
    the detail re-serve (guidance cards have no step
    labels to open) — it keeps the honest normal path,
    never crashes, and never expands the card."""
    _solve(client, "maths me kya scope hai")
    data = _solve(client, "step by step batao")
    assert data["ok"] is True
    result = data["result"]
    assert result["fallback_kind"] != "guidance"
    assert not any("ACET" in s
                   for s in result.get("steps") or [])
