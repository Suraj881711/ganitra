"""Wave 130 (Suraj, 17 Nov 2026 — "ye saare kaam start kar
do"): the STEPS language fix, the Wave 107 leftover.

Wave 107 made an explicit request in the message ("answer
Hindi me chahiye") switch the chrome, the explanation and the
AI prompt — but the solver's own STEP sentences still came
out in the QUESTION's language: an English question with a
Hindi request got English working lines under a Hindi card.

This wave adds a deterministic template layer (steplang.py):
the solver's recurring boilerplate step sentences are mined
(74-question battery: 189 step lines, 107 distinct skeletons)
and each template carries an English / Hindi (Devanagari) /
Hinglish (Roman) rendering. When — and only when — an
explicit Wave-107 request is in force, solver-family results
have their covered steps rendered in the requested language.
Formulas, numbers and answer values are never touched; a
step no template covers passes through unchanged. Alternate
methods ride the same layer; proofs (bilingual data) now
trust the caller's request-aware flag instead of overriding
it with the question's script. With no request, behaviour is
byte-identical to before this wave.
"""
import pytest

import steplang
from steplang import (analyse_steps, relanguage_methods,
                      relanguage_result, translate_step)


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


def _has_devanagari(text):
    return any("ऀ" <= ch <= "ॿ" for ch in str(text or ""))


QUAD = "Solve x^2 - 5x + 6 = 0"
QUAD_STEPS_PLAIN = [
    "Write in standard form: 1·x^2 + -5·x + 6 = 0, "
    "so a = 1, b = -5, c = 6",
    "Discriminant D = b^2 - 4ac = (-5)^2 - 4·1·6 = 1",
    "D > 0, so there are two distinct real roots.",
    "Quadratic formula: x = (-b ± sqrt(D)) / (2a) "
    "= (5 ± sqrt(1)) / 2",
    "Solution: x = 2, x = 3",
]
SI_HI = "5000 रुपये पर 8% वार्षिक दर से 3 वर्ष का साधारण ब्याज निकालो"
SI_HI_STEPS_PLAIN = [
    "मूलधन P = Rs 5000, दर R = 8%, समय T = 3 वर्ष",
    "साधारण ब्याज = (P × R × T) / 100 "
    "= (5000 × 8 × 3) / 100 = Rs 1200",
]


# --- 1. The template layer, unit level -------------------------

@pytest.mark.parametrize("step,expected", [
    ("Write in standard form: 1·x^2 + -5·x + 6 = 0, "
     "so a = 1, b = -5, c = 6",
     "मानक रूप में लिखिए: 1·x^2 + -5·x + 6 = 0, "
     "so a = 1, b = -5, c = 6"),
    ("D > 0, so there are two distinct real roots.",
     "D > 0 है, इसलिए दो भिन्न वास्तविक मूल हैं।"),
    ("D = 0, so there is one repeated real root.",
     "D = 0 है, इसलिए एक ही मूल दोहराया जाता है।"),
    ("Divide both sides by 3: x = 5",
     "दोनों ओर 3 से भाग दीजिए: x = 5"),
    ("Add 15 from both sides: 3·x = 15",
     "दोनों ओर 15 जोड़िए: 3·x = 15"),
    ("Subtract 5 from both sides: x = 2",
     "दोनों ओर से 5 घटाइए: x = 2"),
    ("Prime factorisation: 12 = 2^2 × 3",
     "अभाज्य गुणनखंड: 12 = 2^2 × 3"),
    ("Take the lowest power of each common prime factor.",
     "प्रत्येक उभयनिष्ठ अभाज्य गुणनखंड की सबसे छोटी घात "
     "लीजिए।"),
    ("Take pi = 22/7 here — radius 7 is a multiple of 7, "
     "so the answer comes out exact.",
     "यहाँ pi = 22/7 लीजिए — त्रिज्या 7 का गुणज है 7, "
     "इसलिए उत्तर ठीक-ठीक आएगा।"),
    ("15% means 15/100 = 0.15", "15% का अर्थ है 15/100 = 0.15"),
    ("25% of 80 = 20", "80 का 25% = 20"),
    ("Simple Interest = P × R × T / 100",
     "साधारण ब्याज = P × R × T / 100"),
    ("Total amount = P + SI = 6200", "कुल राशि = P + SI = 6200"),
    ("Add all values: 4 + 8 = 12",
     "सभी मानों को जोड़िए: 4 + 8 = 12"),
    ("Divide by the count (6): 108 ÷ 6 = 18",
     "संख्या (6) से भाग दीजिए: 108 ÷ 6 = 18"),
    ("Total = 10; red count = 4", "कुल = 10; लाल की संख्या = 4"),
    ("Probability = 4/10 = 2/5", "प्रायिकता = 4/10 = 2/5"),
    ("Area = pi·r^2 = 154", "क्षेत्रफल = pi·r^2 = 154"),
    ("Solution: x = 2, x = 3", "हल: x = 2, x = 3"),
])
def test_en_step_to_hindi(step, expected):
    assert translate_step(step, "hi") == expected


@pytest.mark.parametrize("step,expected", [
    (SI_HI_STEPS_PLAIN[0],
     "Principal P = Rs 5000, rate R = 8%, time T = 3 years"),
    (SI_HI_STEPS_PLAIN[1],
     "Simple interest = (P × R × T) / 100 "
     "= (5000 × 8 × 3) / 100 = Rs 1200"),
    ("यहाँ pi = 22/7 लिया है, इसलिए उत्तर ठीक-ठीक आएगा।",
     "Take pi = 22/7 here, so the answer comes out exact."),
    ("वृत्त का क्षेत्रफल = π × त्रिज्या²",
     "Area of the circle = π × radius²"),
    ("बिंदु (3, 4) की रेखा x + y = 1 से दूरी = 4√2",
     "Distance of point (3, 4) from the line x + y = 1 = 4√2"),
])
def test_hi_step_to_english(step, expected):
    assert translate_step(step, "en") == expected


def test_en_step_to_hinglish_is_roman():
    out = translate_step(
        "Take the lowest power of each common prime factor.",
        "hinglish")
    assert out == ("Har common prime factor ki sabse chhoti "
                   "power lo.")
    assert not _has_devanagari(out)
    out = translate_step("Divide both sides by 3: x = 5",
                         "hinglish")
    assert out == "Dono side ko 3 se divide karo: x = 5"


@pytest.mark.parametrize("step", [
    "= 154", "GCD = 6", "x = 2", "a² = 2b²",
    "x = (-b ± sqrt(D)) / (2a)", "108 ÷ 6 = 18",
])
@pytest.mark.parametrize("target", ["en", "hi", "hinglish"])
def test_formula_lines_never_touched(step, target):
    assert translate_step(step, target) == step


def test_uncovered_line_passes_through_unchanged():
    line = "Now compare the two triangles carefully with a diagram"
    assert translate_step(line, "hi") == line
    stats = analyse_steps([line, "Solution: x = 2"], "hi")
    assert stats == {"foreign": 2, "covered": 1}


def test_step_number_prefix_recurses():
    out = translate_step("Step 2: Divide both sides by 3: x = 5",
                         "hi")
    assert out == "चरण 2: दोनों ओर 3 से भाग दीजिए: x = 5"


# --- 2. relanguage_result: gates + cache safety ----------------

def _solver_result():
    return {"type": "solver", "op": "equation",
            "answer": "x = 2, x = 3",
            "steps": list(QUAD_STEPS_PLAIN)}


def test_relanguage_result_solver_family():
    result = _solver_result()
    out = relanguage_result(result, "hi")
    assert out is not result
    assert out["answer"] == "x = 2, x = 3"
    assert out["steps"][0].startswith("मानक रूप में लिखिए:")
    assert out["steps"][4] == "हल: x = 2, x = 3"
    # the input (which the solver cache may share) is untouched
    assert result["steps"] == QUAD_STEPS_PLAIN


@pytest.mark.parametrize("kind,extra", [
    ("gemini", {"ai_generated": True}),
    ("groq", {"ai_generated": True}),
    ("openrouter", {"ai_generated": True}),
    ("concept", {}),
    ("proof", {}),
])
def test_relanguage_result_skips_language_aware_kinds(kind,
                                                      extra):
    result = _solver_result()
    result["fallback_kind"] = kind
    result.update(extra)
    assert relanguage_result(result, "hi") is result


def test_relanguage_result_noop_returns_same_object():
    result = _solver_result()
    assert relanguage_result(result, "en") is result
    empty = {"type": "solver", "answer": "5", "steps": []}
    assert relanguage_result(empty, "hi") is empty


def test_relanguage_methods_hindi_label_and_steps():
    methods = [{"id": "euclid",
                "label": "Euclid's division method",
                "answer": "6",
                "steps": ["18 ÷ 12 = 1 remainder 6",
                          "The last non-zero divisor is "
                          "the HCF: 6"]}]
    out = relanguage_methods(methods, "hi")
    assert out[0]["label"] == "यूक्लिड की भाग विधि"
    assert out[0]["steps"][0] == "18 ÷ 12 = 1, शेषफल 6"
    assert methods[0]["label"] == "Euclid's division method"
    # English target: payload untouched
    assert relanguage_methods(methods, "en") is methods


# --- 3. End to end through /api/solve ---------------------------

def test_en_question_hindi_request_steps_hindi(client):
    plain = _ask(client, QUAD)["result"]
    req = _ask(client, QUAD + ". Answer in Hindi")["result"]
    assert req["answer"] == plain["answer"] == "x = 2, x = 3"
    steps = req["steps"]
    assert steps[0].startswith("मानक रूप में लिखिए:")
    assert steps[2] == "D > 0 है, इसलिए दो भिन्न वास्तविक मूल हैं।"
    assert steps[4] == "हल: x = 2, x = 3"
    joined = " ".join(steps)
    assert "Write in standard form" not in joined
    assert "Quadratic formula:" not in joined
    # formulas byte-identical to the plain answer's
    assert "1·x^2 + -5·x + 6 = 0" in steps[0]
    assert "(-5)^2 - 4·1·6 = 1" in steps[1]


def test_en_question_hinglish_request_steps_roman(client):
    req = _ask(client, "Find the HCF of 12 and 18. "
                       "Hinglish me jawab do")
    result = req["result"]
    assert result["answer"] == "6"
    joined = " ".join(result["steps"])
    assert not _has_devanagari(joined)
    assert "sabse chhoti power" in joined
    # Hinglish keeps the English method label (documented)
    assert req["methods"]
    assert req["methods"][0]["label"] == \
        "Euclid's division method"


def test_hindi_question_english_request_steps_english(client):
    plain = _ask(client, SI_HI)["result"]
    req = _ask(client, SI_HI + "। Answer in English")["result"]
    assert req["answer"] == plain["answer"] == "1200"
    assert req["steps"][0] == (
        "Principal P = Rs 5000, rate R = 8%, "
        "time T = 3 years")
    assert req["steps"][1].startswith("Simple interest =")
    assert not any(_has_devanagari(s) for s in req["steps"])


def test_hindi_circle_english_request(client):
    req = _ask(client, "त्रिज्या 7 cm वाले वृत्त का क्षेत्रफल "
                       "निकालो। Answer in English")["result"]
    assert req["answer"] == "154"
    assert req["steps"][0] == (
        "Take pi = 22/7 here, so the answer comes out exact.")
    assert req["steps"][1] == "Area of the circle = π × radius²"
    assert req["steps"][2] == "= π × 7² = 154"


def test_methods_follow_hindi_request(client):
    req = _ask(client, "Find the HCF of 12 and 18. "
                       "Answer in Hindi")
    assert req["result"]["answer"] == "6"
    methods = req["methods"]
    assert methods and methods[0]["id"] == "euclid"
    assert methods[0]["label"] == "यूक्लिड की भाग विधि"
    assert _has_devanagari(methods[0]["steps"][0])
    assert methods[0]["steps"][-1] == "उत्तर: 6"
    assert methods[0]["answer"] == "6"


def test_proof_follows_explicit_request(client):
    en = _ask(client, "Prove that root 2 is irrational")
    hi = _ask(client, "Prove that root 2 is irrational. "
                      "Answer in Hindi")
    assert "proved" in en["result"]["answer"]
    assert "सिद्ध हुआ" in hi["result"]["answer"]
    assert _has_devanagari(hi["result"]["steps"][0])
    back = _ask(client, "सिद्ध करो कि root 2 अपरिमेय है। "
                        "Answer in English")
    assert "proved" in back["result"]["answer"]
    assert not _has_devanagari(back["result"]["steps"][0])


# --- 4. No request: byte-identical regression pins --------------

def test_no_request_quadratic_steps_unchanged(client):
    result = _ask(client, QUAD)["result"]
    assert result["steps"] == QUAD_STEPS_PLAIN


def test_no_request_hindi_steps_unchanged(client):
    result = _ask(client, SI_HI)["result"]
    assert result["steps"] == SI_HI_STEPS_PLAIN


def test_no_request_methods_unchanged(client):
    req = _ask(client, "Find the HCF of 12 and 18")
    assert req["methods"][0]["label"] == \
        "Euclid's division method"
    assert req["methods"][0]["steps"][0].startswith(
        "Euclid's method: divide the bigger number")


@pytest.mark.parametrize("plain,requested", [
    (QUAD, QUAD + ". Answer in Hindi"),
    ("Find the area of a circle with radius 7 cm",
     "Find the area of a circle with radius 7 cm. "
     "Answer in Hindi"),
    ("Find the mean of 4, 8, 15, 16, 23 and 42",
     "Find the mean of 4, 8, 15, 16, 23 and 42. "
     "Answer Hindi me chahiye"),
    ("Solve 3x + 5 = 20",
     "Solve 3x + 5 = 20. Hinglish me jawab do"),
    (SI_HI, SI_HI + "। Answer in English"),
])
def test_answer_values_identical_with_and_without_request(
        client, plain, requested):
    a = _ask(client, plain)["result"]
    b = _ask(client, requested)["result"]
    assert a.get("answer") == b.get("answer")
    assert a.get("op") == b.get("op")
