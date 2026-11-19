"""Wave 111 (Suraj, 17 Nov 2026): the maths-META layer —
maths history/creator facts + study/practice/exam advice
(maths_meta.py, hooked into fallback.with_fallback).

Suraj's point: students ask maths questions that are not
computations — "maths kaise practice karu", "exam me
question kaise solve karne chahiye", "ye topic kisne
banaya", "ye theorem kisne prove ki". Before this wave:

  * "Pythagoras theorem kisne banaya tha?" got the theorem
    STATEMENT card (the concept layers match the topic
    keyword and never look at the shape) — WHAT, not WHO;
  * "Zero kisne invent kiya?", "Shakuntala Devi kaun thi?",
    "Maths ki practice kaise karu?" all collapsed to the
    one-line not-found;
  * a who/advice-shaped maths question that no layer could
    answer classified as "gibberish", a kind the AI chain
    never sees — so even in production Gemini got no chance.

Pinned here:
  1. the HISTORY battery (curated facts, EN/HI/Hinglish),
  2. the ADVICE battery (study behaviour, EN/HI/Hinglish),
  3. the routing guards: non-maths GK still refused,
     science still guarded, gibberish still one-line
     not-found, statement/concept asks and computations
     byte-for-byte the old behaviour,
  4. the AI flow: a meta-shaped maths question that misses
     the curated entries reaches the AI chain (kind
     "guide"); gibberish and non-maths never do.
"""
import pytest

import fallback
from fallback import fallback_answer
from maths_meta import ADVICE, HISTORY, is_meta_shaped, \
    meta_result

DEV = ("ऀ", "ॿ")


def _has_dev(text):
    return any(DEV[0] <= ch <= DEV[1] for ch in str(text or ""))


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the AI legs must stay inert in this battery
    (the AI-flow tests patch the chain functions directly)."""
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


def _meta(question):
    r = fallback_answer(question)
    return r


# ---------------------------------------------------------------------------
# 0. The curated data itself: coverage + fact spot-pins
# ---------------------------------------------------------------------------

def test_history_coverage():
    ids = {e["id"] for e in HISTORY}
    assert ids == {
        "zero", "pythagoras", "algebra", "euclid", "calculus",
        "fermat", "coordinate_geometry", "pi", "venn",
        "pascal_triangle", "trigonometry", "logarithm",
        "binary", "shakuntala_devi", "ramanujan", "aryabhata",
        "brahmagupta", "bhaskara",
        # Wave 177: three seed-list titles/persons added
        # (Archimedes = father of mathematics, Gauss =
        # number theory, Fibonacci).
        "archimedes", "gauss", "fibonacci",
    }
    for e in HISTORY:
        for flavour in ("en", "roman", "dev"):
            assert e[flavour]["answer"].strip()
            assert len(e[flavour]["steps"]) >= 2


def test_advice_coverage():
    ids = {e["id"] for e in ADVICE}
    assert ids == {
        "practice", "exam_solve", "fear", "formulae", "weak",
        "revision", "silly_mistakes", "speed",
    }
    for e in ADVICE:
        for flavour in ("en", "roman", "dev"):
            assert e[flavour]["answer"].strip()
            assert len(e[flavour]["steps"]) >= 3


def _entry(entry_id):
    return next(e for e in HISTORY if e["id"] == entry_id)


def test_fact_spot_pins():
    zero = _entry("zero")
    assert "628" in " ".join(zero["en"]["steps"])
    assert "Brahmagupta" in zero["en"]["answer"]
    fermat = _entry("fermat")
    assert "Wiles" in fermat["en"]["answer"]
    assert "1994" in fermat["en"]["answer"]
    assert "1637" in " ".join(fermat["en"]["steps"])
    algebra = _entry("algebra")
    assert "al-jabr" in algebra["en"]["answer"]
    calculus = _entry("calculus")
    blob = calculus["en"]["answer"] + " ".join(
        calculus["en"]["steps"])
    assert "Newton" in blob and "Leibniz" in blob
    pascal = _entry("pascal_triangle")
    assert "Meru" in " ".join(pascal["en"]["steps"])
    binary = _entry("binary")
    blob = " ".join(binary["en"]["steps"])
    assert "Pingala" in blob and "1703" in blob
    pyth = _entry("pythagoras")
    blob = " ".join(pyth["en"]["steps"])
    assert "Babylon" in blob and "Baudhayana" in blob
    shak = _entry("shakuntala_devi")
    assert "28 seconds" in " ".join(shak["en"]["steps"])


# ---------------------------------------------------------------------------
# 1. HISTORY battery — who questions get WHO answers
# ---------------------------------------------------------------------------

HISTORY_CASES = [
    # (question, meta_id, flavour)
    ("Who proved the Pythagoras theorem?", "pythagoras", "en"),
    ("Pythagoras theorem kisne banaya tha?", "pythagoras",
     "roman"),
    ("पाइथागोरस प्रमेय किसने दिया?", "pythagoras", "dev"),
    ("Who invented zero?", "zero", "en"),
    ("Zero kisne invent kiya?", "zero", "roman"),
    ("शून्य की खोज किसने की?", "zero", "dev"),
    ("Algebra kisne banaya?", "algebra", "roman"),
    ("Who is the father of geometry?", "euclid", "en"),
    ("Geometry ke father kaun hai?", "euclid", "roman"),
    ("Calculus kisne banaya?", "calculus", "roman"),
    ("Fermat's last theorem kisne prove kiya?", "fermat",
     "roman"),
    ("Who created coordinate geometry?",
     "coordinate_geometry", "en"),
    ("Descartes kaun tha?", "coordinate_geometry", "roman"),
    ("Who discovered pi?", "pi", "en"),
    ("Venn diagram kisne banaya?", "venn", "roman"),
    ("John Venn kaun the?", "venn", "roman"),
    ("Pascal ka triangle kisne banaya?", "pascal_triangle",
     "roman"),
    ("Trigonometry ke father kaun hai?", "trigonometry",
     "roman"),
    ("Logarithm kisne banaya?", "logarithm", "roman"),
    ("Napier kaun tha?", "logarithm", "roman"),
    ("Binary number system kisne diya?", "binary", "roman"),
    ("Shakuntala Devi kaun thi?", "shakuntala_devi", "roman"),
    ("Ramanujan kaun the?", "ramanujan", "roman"),
    ("आर्यभट कौन थे?", "aryabhata", "dev"),
    ("ब्रह्मगुप्त कौन थे?", "brahmagupta", "dev"),
    ("Bhaskara kaun the?", "bhaskara", "roman"),
    ("Lilavati kisne likhi?", "bhaskara", "roman"),
    ("Who wrote Lilavati?", "bhaskara", "en"),
]


@pytest.mark.parametrize("question,meta_id,flavour",
                         HISTORY_CASES)
def test_history_battery(question, meta_id, flavour):
    r = _meta(question)
    assert r.get("fallback_kind") == "history", r
    assert r.get("meta_id") == meta_id, r
    assert r.get("op") == f"history_{meta_id}"
    assert r.get("answer", "").strip()
    assert len(r.get("steps") or []) >= 2
    blob = r["answer"] + " " + " ".join(r["steps"])
    if flavour == "dev":
        assert _has_dev(blob)
    else:
        assert not _has_dev(blob)


def test_history_answers_the_who_not_the_what():
    # The flagship bug: the statement card must NOT be the
    # answer to a who question.
    r = _meta("Pythagoras theorem kisne banaya tha?")
    assert "c² = a² + b²" not in r["answer"]
    assert "Pythagoras" in r["answer"]
    r = _meta("Algebra kisne banaya?")
    assert "Al-Khwarizmi" in r["answer"]


# ---------------------------------------------------------------------------
# 2. ADVICE battery — study behaviour, language-matched
# ---------------------------------------------------------------------------

ADVICE_CASES = [
    ("Maths ki practice kaise karu?", "practice", "roman"),
    ("How to prepare for maths exam?", "practice", "en"),
    ("गणित की तैयारी कैसे करूँ?", "practice", "dev"),
    ("Exam me maths ke question kaise solve karne chahiye?",
     "exam_solve", "roman"),
    ("परीक्षा में प्रश्न कैसे हल करने चाहिए?", "exam_solve",
     "dev"),
    ("Maths se dar lagta hai", "fear", "roman"),
    ("Formula yaad kaise karu?", "formulae", "roman"),
    ("सूत्र याद कैसे करूँ?", "formulae", "dev"),
    ("Maths me bahut weak hu, kya karu?", "weak", "roman"),
    ("गणित में कमज़ोर हूँ, क्या करूँ?", "weak", "dev"),
    ("Revision kaise karna chahiye maths ka?", "revision",
     "roman"),
    ("Silly mistakes kaise kam karu?", "silly_mistakes",
     "roman"),
    ("Calculation bahut slow hai meri", "speed", "roman"),
]


@pytest.mark.parametrize("question,meta_id,flavour",
                         ADVICE_CASES)
def test_advice_battery(question, meta_id, flavour):
    r = _meta(question)
    assert r.get("fallback_kind") == "advice", r
    assert r.get("meta_id") == meta_id, r
    assert r.get("op") == f"advice_{meta_id}"
    assert len(r.get("steps") or []) >= 3
    blob = r["answer"] + " " + " ".join(r["steps"])
    if flavour == "dev":
        assert _has_dev(blob)
    else:
        assert not _has_dev(blob)


# ---------------------------------------------------------------------------
# 3. Guards — the old behaviour, untouched
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,kind", [
    ("What is the capital of France?", "nonmaths"),
    ("भारत की राजधानी क्या है?", "nonmaths"),
    ("What is photosynthesis?", "nonmaths"),
    ("Who is the president of India?", "nonmaths"),
    ("Who discovered gravity?", "science"),
    ("asdf qwer zxcv", "not_found"),
    ("History ki taiyaari kaise karu?", "not_found"),
    ("English ki practice kaise karu?", "not_found"),
])
def test_guards_unchanged(question, kind):
    r = _meta(question)
    assert r.get("fallback_kind") == kind, r
    assert r.get("fallback_kind") not in ("history", "advice")


@pytest.mark.parametrize("question", [
    "Pythagoras theorem kya hai?",       # statement ask
    "What is a prime number?",           # concept ask
    "Algebra kya hai?",                  # concept ask
    "Trigonometry me kaun sa formula lagta hai?",  # which-ask
    "Pythagoras theorem ka proof batao",  # proof ask
])
def test_concept_asks_unchanged(question):
    r = _meta(question)
    assert r.get("fallback_kind") == "concept", r
    assert r.get("fallback_kind") not in ("history", "advice")


@pytest.mark.parametrize("question,answer_part", [
    ("2 + 3 kitna hota hai?", "5"),
    ("Solve x^2 - 5x + 6 = 0", "x = 2, x = 3"),
    ("Find the zeros of x^2 - 5x + 6", "2"),
])
def test_computations_unchanged(question, answer_part):
    r = _meta(question)
    assert not r.get("fallback"), r
    assert answer_part in str(r.get("answer", "")), r


def test_area_computation_unchanged():
    r = _meta("What is the area of a circle with radius 7?")
    assert not r.get("fallback"), r
    assert "154" in str(r.get("answer", "")), r


# ---------------------------------------------------------------------------
# 4. The wide net: meta-shaped misses reach the AI chain
# ---------------------------------------------------------------------------

def test_is_meta_shaped():
    assert is_meta_shaped("Euler kaun the?")
    assert is_meta_shaped("Gauss kaun tha?")
    assert is_meta_shaped(
        "Maths olympiad ki taiyaari kaise karu?")
    assert not is_meta_shaped("asdf qwer zxcv")
    assert not is_meta_shaped("Who is the president of "
                              "India?")
    assert not is_meta_shaped("History ki taiyaari kaise "
                              "karu?")
    assert not is_meta_shaped("What is the capital of "
                              "France?")


def _patch_ai(monkeypatch, reply):
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


@pytest.mark.parametrize("question", [
    "Euler kaun the?",
    # Wave 177: "Gauss kaun tha?" is a curated HIT now
    # (the seed list's father-of-number-theory item), so
    # the canonical miss example moved to Leibniz
    # (meta-shaped, no entry, no other guard claims him;
    # Newton was tried first but the science guard claims
    # him as Physics).
    "Leibniz kaun the?",
])
def test_meta_miss_reaches_ai(monkeypatch, question):
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert calls, "AI chain was never consulted"
    assert r.get("answer") == "AI sentinel"


@pytest.mark.parametrize("question", [
    "Euler kaun the?",
    # Wave 177: see test_meta_miss_reaches_ai — Gauss is
    # curated now; Leibniz is the standing miss example.
    "Leibniz kaun the?",
])
def test_meta_miss_without_ai_still_not_found(monkeypatch,
                                              question):
    _patch_ai(monkeypatch, None)
    r = fallback_answer(question)
    assert r.get("fallback_kind") == "not_found", r


@pytest.mark.parametrize("question,kind", [
    ("asdf qwer zxcv", "not_found"),
    ("What is the capital of France?", "nonmaths"),
    ("Who discovered gravity?", "science"),
])
def test_ai_never_consulted_for_guards(monkeypatch, question,
                                       kind):
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert not calls
    assert r.get("fallback_kind") == kind, r


def test_meta_result_unit_gates():
    # The module's own gates, without the fallback chain:
    # computation veto, which-question veto, subject gate.
    assert meta_result("Pythagoras theorem kisne banaya "
                       "tha?", "roman") is not None
    assert meta_result("solve 2 + 3 kisne kiya", "en") is None
    assert meta_result("Trigonometry me kaun sa formula "
                       "lagta hai?", "roman") is None
    assert meta_result("History ki taiyaari kaise karu?",
                       "roman") is None
    assert meta_result("Pythagoras theorem kya hai?",
                       "roman") is None


def test_topic_confusion_is_not_fear_advice():
    # Wave-75 regression caught in this wave's own full-suite
    # run: "confused BETWEEN two topics" is a difference ask
    # owned by the topics library, not maths fear. The fear
    # entry must never fire on it (nor on a topic doubt).
    q = "guru AP aur GP me confuse ho gaya hu, fark bta do?"
    assert meta_result(q, "roman") is None
    r = _meta(q)
    assert r.get("source") == "topics", r
    assert r.get("fallback_kind") != "advice"
    assert meta_result("AP samajh nahi aata", "roman") is None
    assert meta_result(
        "compound interest aur simple interest me kya antar "
        "hai?", "roman") is None


# ---------------------------------------------------------------------------
# 5. End to end through /api/solve
# ---------------------------------------------------------------------------

def test_api_solve_meta_end_to_end(client):
    def ask(q):
        return client.post("/api/solve",
                           json={"question": q}).get_json()

    data = ask("Pythagoras theorem kisne banaya tha?")
    assert data["ok"] is True
    assert data["result"]["fallback_kind"] == "history"
    assert data["result"]["meta_id"] == "pythagoras"

    data = ask("Maths ki practice kaise karu?")
    assert data["ok"] is True
    assert data["result"]["fallback_kind"] == "advice"
    assert data["result"]["meta_id"] == "practice"

    data = ask("What is the capital of France?")
    assert data["result"]["fallback_kind"] == "nonmaths"

    data = ask("Pythagoras theorem kya hai?")
    assert data["result"]["fallback_kind"] == "concept"
