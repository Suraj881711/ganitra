"""Wave 132 (Suraj, 17 Nov 2026: "Agar kisi AI se Ganitra
ans leta hai to usko apni hi language me ans de, na ki
kisi aur AI ka ans same de de — Ganitra ki ek apni
language honi chahiye, ek alag simple normal language"):
GANITRA'S OWN VOICE for AI-fallback answers.

When the AI chain (Gemini -> Groq -> OpenRouter) supplies
an answer, Ganitra must serve it re-expressed in its own
house style — simple, normal, plain school-teacher
language, like its solver answers — never the source AI's
answer same-to-same.

These tests pin, with recorded-style fixtures (realistic
raw outputs in Gemini/Groq/OpenRouter styles — no live
API calls):

- the shared prompt now instructs all three legs in the
  Ganitra Voice (gemini_fallback._PROMPT);
- the deterministic re-voicing normalizer
  (ganitra_voice.normalize_ai_text, wired into
  gemini_fallback._shape_result, which all three legs
  share) strips markdown, AI-isms, self-reference and
  closing chatter, splits walls of text into plain step
  lines, and forces the final line into "Answer: ..."
  form using the raw reply's OWN stated final answer;
- the HARD INVARIANT: the normalizer never alters maths
  content — every value (number, fraction, expression
  token, unit) in the raw reply survives in the served
  answer, checked per fixture with
  ganitra_voice.values_preserved, plus byte-identical
  pins for each fixture's key expressions;
- the SAMENESS proof: per fixture, the share of the raw
  reply's non-formula lines served verbatim
  (ganitra_voice.shared_line_ratio) stays low — the
  served answer is demonstrably not a copy;
- the veto paths are unchanged: NOT_MATHS (incl. the
  sentinel leaking mid-reply), empty replies, pure-fluff
  replies and truncated text (the Wave 119 guard lives at
  the payload level and is untouched);
- solver/bank/concept answers never pass through the
  normalizer (they are Ganitra's own already) — an exact
  solver answer through the real path stays untouched.
"""
import pytest

import gemini_fallback
import groq_fallback
import openrouter_fallback
import ganitra_voice
import solver.answer_cache as cache
from api import _solve_friendly
from ganitra_voice import (normalize_ai_text, extract_values,
                           values_preserved, shared_line_ratio,
                           word_overlap)


@pytest.fixture(autouse=True)
def _clean_caches():
    # Same isolation as test_wave37: the negative cache is
    # process-global and the end-to-end test below mocks
    # the AI transport.
    cache.clear_cache()
    yield
    cache.clear_cache()


# ---------------------------------------------------------------------------
# The fixture battery: realistic RAW replies in the three
# providers' styles. `steps` / `answer` are the SERVED
# shape (after _shape_result, i.e. after _clean_line has
# stripped the "Step 1:" numbering as it always has).
# `expressions` must survive byte-identical in the served
# text. `max_shared` caps the non-formula shared-line
# ratio (the sameness proof).
# ---------------------------------------------------------------------------

FIXTURES = [
    {
        "id": "gemini_area_between_curves",
        "style": "gemini",
        "question": "Find the area between the curves "
                    "y = x^2 and y = x",
        "raw": (
            "## Solution\n"
            "\n"
            "Sure! Let's solve this step by step. 😊\n"
            "\n"
            "First, we find the points where the curves meet:\n"
            "**x^2 = x**\n"
            "x^2 - x = 0\n"
            "x(x - 1) = 0\n"
            "So, x = 0 and x = 1\n"
            "\n"
            "Now we set up the integral:\n"
            "Area = integral from 0 to 1 of (x - x^2) dx\n"
            "Area = [x^2/2 - x^3/3] from 0 to 1\n"
            "Area = (1/2 - 1/3) - 0\n"
            "**Area = 1/6**\n"
            "\n"
            "Therefore, the final answer is **1/6 square units**.\n"
            "\n"
            "Hope this helps! Let me know if you have any "
            "questions. 👍"
        ),
        "answer": "1/6 square units",
        "steps": [
            "Find the points where the curves meet:",
            "x^2 = x",
            "x^2 - x = 0",
            "x(x - 1) = 0",
            "x = 0 and x = 1",
            "Set up the integral:",
            "Area = integral from 0 to 1 of (x - x^2) dx",
            "Area = [x^2/2 - x^3/3] from 0 to 1",
            "Area = (1/2 - 1/3) - 0",
            "Area = 1/6",
        ],
        "expressions": ["x^2 - x = 0", "x(x - 1) = 0",
                        "Area = (1/2 - 1/3) - 0", "Area = 1/6"],
        "max_shared": 0.5,
    },
    {
        "id": "groq_linear_equation",
        "style": "groq",
        "question": "Solve 3x - 5 = 10",
        "raw": (
            "Sure! Here's the solution:\n"
            "\n"
            "Step 1: Add 5 to both sides\n"
            "3x - 5 + 5 = 10 + 5\n"
            "3x = 15\n"
            "\n"
            "Step 2: Divide both sides by 3\n"
            "x = 15/3\n"
            "x = 5\n"
            "\n"
            "**Answer: x = 5**\n"
            "\n"
            "I hope this helps! 😊"
        ),
        "answer": "x = 5",
        "steps": [
            "Add 5 to both sides",
            "3x - 5 + 5 = 10 + 5",
            "3x = 15",
            "Divide both sides by 3",
            "x = 15/3",
            "x = 5",
        ],
        "expressions": ["3x - 5 + 5 = 10 + 5", "x = 15/3"],
        "max_shared": 0.5,
    },
    {
        "id": "openrouter_latex_identity",
        "style": "openrouter",
        "question": "If x + 1/x = 5, find the value of "
                    "x^2 + 1/x^2",
        "raw": (
            "Of course! Let's find the value step by step.\n"
            "\n"
            "We know that $(x + \\frac{1}{x})^2 = x^2 + 2 + "
            "\\frac{1}{x^2}$\n"
            "\n"
            "Putting the given value:\n"
            "$5^2 = x^2 + 2 + \\frac{1}{x^2}$\n"
            "$25 = x^2 + \\frac{1}{x^2} + 2$\n"
            "$x^2 + \\frac{1}{x^2} = 25 - 2$\n"
            "$x^2 + \\frac{1}{x^2} = 23$\n"
            "\n"
            "**The final answer is 23.**\n"
            "\n"
            "Feel free to ask if you have any doubts!"
        ),
        "answer": "23",
        "steps": [
            "Find the value step by step.",
            "(x + 1/x)^2 = x^2 + 2 + 1/x^2",
            "Putting the given value:",
            "5^2 = x^2 + 2 + 1/x^2",
            "25 = x^2 + 1/x^2 + 2",
            "x^2 + 1/x^2 = 25 - 2",
            "x^2 + 1/x^2 = 23",
        ],
        "expressions": ["(x + 1/x)^2 = x^2 + 2 + 1/x^2",
                        "x^2 + 1/x^2 = 23"],
        "max_shared": 0.5,
    },
    {
        "id": "hindi_rectangle_area",
        "style": "gemini",
        "question": "एक आयत की लंबाई 12 सेमी और चौड़ाई 5 "
                    "सेमी है। इसका क्षेत्रफल ज्ञात कीजिए।",
        "raw": (
            "बिल्कुल! आइए इसे हल करते हैं।\n"
            "\n"
            "**दिया है:**\n"
            "लंबाई = 12 सेमी\n"
            "चौड़ाई = 5 सेमी\n"
            "\n"
            "क्षेत्रफल = लंबाई × चौड़ाई\n"
            "क्षेत्रफल = 12 × 5\n"
            "क्षेत्रफल = 60 वर्ग सेमी\n"
            "\n"
            "**उत्तर: 60 वर्ग सेमी**\n"
            "\n"
            "आशा है यह मदद करेगा! 😊"
        ),
        "answer": "60 वर्ग सेमी",
        "steps": [
            "लंबाई = 12 सेमी",
            "चौड़ाई = 5 सेमी",
            "क्षेत्रफल = लंबाई × चौड़ाई",
            "क्षेत्रफल = 12 × 5",
            "क्षेत्रफल = 60 वर्ग सेमी",
        ],
        "expressions": ["क्षेत्रफल = 12 × 5",
                        "क्षेत्रफल = 60 वर्ग सेमी"],
        "max_shared": 0.5,
    },
    {
        "id": "hinglish_train_distance",
        "style": "groq",
        "question": "Train 72 km/h ki speed se chal rahi "
                    "hai. 3 ghante me kitni doori tay karegi?",
        "raw": (
            "Bilkul! Chalo dekhte hain.\n"
            "\n"
            "Doori = speed × time\n"
            "Doori = 72 × 3\n"
            "Doori = 216 km\n"
            "\n"
            "**Jawab: 216 km**\n"
            "\n"
            "Koi doubt ho to pucho! 😊"
        ),
        "answer": "216 km",
        "steps": [
            "Doori = speed × time",
            "Doori = 72 × 3",
            "Doori = 216 km",
        ],
        "expressions": ["Doori = 72 × 3", "Doori = 216 km"],
        "max_shared": 0.5,
    },
    {
        "id": "wall_of_text_profit",
        "style": "openrouter",
        "question": "A shopkeeper buys a shirt for Rs 800 "
                    "and sells it at a profit of 25%. Find "
                    "the selling price.",
        "raw": (
            "To find the selling price, first we find the "
            "profit. Profit = 25% of 800 = 25/100 × 800 = "
            "200. Selling price = cost price + profit = "
            "800 + 200 = 1000. So the selling price is "
            "Rs 1000."
        ),
        "answer": "The selling price is Rs 1000",
        "steps": [
            "To find the selling price, first we find the "
            "profit.",
            "Profit = 25% of 800 = 25/100 × 800 = 200.",
            "Selling price = cost price + profit = "
            "800 + 200 = 1000.",
        ],
        "expressions": ["25/100 × 800 = 200",
                        "800 + 200 = 1000"],
        "max_shared": 0.5,
    },
    {
        "id": "groq_quadratic_factor",
        "style": "groq",
        "question": "Solve x^2 - 5x + 6 = 0",
        "raw": (
            "Great question! Let's solve this quadratic "
            "equation.\n"
            "\n"
            "We need two numbers whose **product is 6** "
            "and **sum is -5**.\n"
            "x^2 - 5x + 6 = 0\n"
            "(x - 2)(x - 3) = 0\n"
            "x - 2 = 0 or x - 3 = 0\n"
            "**x = 2 or x = 3**\n"
            "\n"
            "Answer: x = 2 or x = 3\n"
            "\n"
            "That's all! Keep practicing! 📚"
        ),
        "answer": "x = 2 or x = 3",
        "steps": [
            "We need two numbers whose product is 6 and "
            "sum is -5.",
            "x^2 - 5x + 6 = 0",
            "(x - 2)(x - 3) = 0",
            "x - 2 = 0 or x - 3 = 0",
            "x = 2 or x = 3",
        ],
        "expressions": ["x^2 - 5x + 6 = 0",
                        "(x - 2)(x - 3) = 0"],
        "max_shared": 0.5,
    },
    {
        "id": "gemini_trig_values",
        "style": "gemini",
        "question": "Find the value of tan 45 + cot 45",
        "raw": (
            "Certainly! Here is the step-by-step solution.\n"
            "\n"
            "First, tan 45 = 1\n"
            "Second, cot 45 = 1\n"
            "Finally, tan 45 + cot 45 = 1 + 1 = 2\n"
            "\n"
            "Answer: 2\n"
            "\n"
            "Happy learning! 🎉"
        ),
        "answer": "2",
        "steps": [
            "tan 45 = 1",
            "cot 45 = 1",
            "tan 45 + cot 45 = 1 + 1 = 2",
        ],
        "expressions": ["tan 45 + cot 45 = 1 + 1 = 2"],
        "max_shared": 0.5,
    },
    {
        "id": "openrouter_mean_table",
        "style": "openrouter",
        "question": "Find the mean of this data: value "
                    "x = 1, 2, 3 with frequency f = 2, 3, 5",
        "raw": (
            "Let's calculate the mean.\n"
            "\n"
            "| x | f | fx |\n"
            "|---|---|----|\n"
            "| 1 | 2 | 2 |\n"
            "| 2 | 3 | 6 |\n"
            "| 3 | 5 | 15 |\n"
            "\n"
            "Sum of f = 2 + 3 + 5 = 10\n"
            "Sum of fx = 2 + 6 + 15 = 23\n"
            "Mean = 23/10 = 2.3\n"
            "\n"
            "Answer: 2.3"
        ),
        "answer": "2.3",
        "steps": [
            "Calculate the mean.",
            "x, f, fx",
            "1, 2, 2",
            "2, 3, 6",
            "3, 5, 15",
            "Sum of f = 2 + 3 + 5 = 10",
            "Sum of fx = 2 + 6 + 15 = 23",
            "Mean = 23/10 = 2.3",
        ],
        "expressions": ["Mean = 23/10 = 2.3",
                        "Sum of fx = 2 + 6 + 15 = 23"],
        "max_shared": 0.5,
    },
    {
        "id": "gemini_ages_word_problem",
        "style": "gemini",
        "question": "The sum of the ages of a father and "
                    "his son is 45 years. Five years ago, "
                    "the product of their ages was 124. "
                    "Find their present ages.",
        "raw": (
            "Of course! As an AI, I'll walk you through "
            "this.\n"
            "\n"
            "Let the son's age be x years\n"
            "Father's age = 45 - x\n"
            "Five years ago: (x - 5)(40 - x) = 124\n"
            "x^2 - 45x + 324 = 0\n"
            "(x - 9)(x - 36) = 0\n"
            "x = 9 or x = 36\n"
            "The son's age cannot be 36, so x = 9\n"
            "\n"
            "**Answer: Son is 9 years old and father is "
            "36 years old**\n"
            "\n"
            "Hope this helps!"
        ),
        "answer": "Son is 9 years old and father is "
                  "36 years old",
        "steps": [
            "Let the son's age be x years",
            "Father's age = 45 - x",
            "Five years ago: (x - 5)(40 - x) = 124",
            "x^2 - 45x + 324 = 0",
            "(x - 9)(x - 36) = 0",
            "x = 9 or x = 36",
            "The son's age cannot be 36, so x = 9",
        ],
        "expressions": ["x^2 - 45x + 324 = 0",
                        "(x - 5)(40 - x) = 124"],
        # This raw is only LIGHTLY dressed (most working
        # lines were already plain), so more of its lines
        # legitimately survive — the opener, the closer
        # and the bold still all go.
        "max_shared": 0.65,
    },
    {
        "id": "groq_triangle_angles",
        "style": "groq",
        "question": "In triangle ABC, angle A = 50 degrees "
                    "and angle B = 60 degrees. Find angle C.",
        "raw": (
            "Here's how to solve it:\n"
            "\n"
            "We know that the sum of angles of a triangle "
            "= 180 degrees\n"
            "A + B + C = 180\n"
            "50 + 60 + C = 180\n"
            "110 + C = 180\n"
            "C = 180 - 110\n"
            "C = 70\n"
            "\n"
            "So, the answer is **70 degrees**.\n"
            "\n"
            "Let me know if you have any other questions!"
        ),
        "answer": "70 degrees",
        "steps": [
            "The sum of angles of a triangle = 180 degrees",
            "A + B + C = 180",
            "50 + 60 + C = 180",
            "110 + C = 180",
            "C = 180 - 110",
            "C = 70",
        ],
        "expressions": ["50 + 60 + C = 180", "C = 180 - 110"],
        "max_shared": 0.5,
    },
    {
        "id": "openrouter_fraction_add",
        "style": "openrouter",
        "question": "Add 2/3 and 3/4",
        "raw": (
            "Sure, let's add these fractions!\n"
            "\n"
            "LCM of 3 and 4 = 12\n"
            "2/3 = 8/12\n"
            "3/4 = 9/12\n"
            "8/12 + 9/12 = 17/12\n"
            "\n"
            "**Final answer: 17/12**\n"
            "\n"
            "That's all! Keep practicing! 📚"
        ),
        "answer": "17/12",
        "steps": [
            "Add these fractions.",
            "LCM of 3 and 4 = 12",
            "2/3 = 8/12",
            "3/4 = 9/12",
            "8/12 + 9/12 = 17/12",
        ],
        "expressions": ["8/12 + 9/12 = 17/12",
                        "LCM of 3 and 4 = 12"],
        "max_shared": 0.5,
    },
]

_FIXTURE_IDS = [fx["id"] for fx in FIXTURES]


def _fixture(fx_id):
    return next(fx for fx in FIXTURES if fx["id"] == fx_id)


def _served_text(result):
    return "\n".join(list(result["steps"]) +
                     ["Answer: " + result["answer"]])


# Words/decoration that must never survive into a served
# AI answer — the voice, negatively.
_AI_ISM_MARKERS = (
    "sure", "of course", "certainly", "great question",
    "here's", "here is", "let's", "as an ai",
    "hope this helps", "i hope this helps", "let me know",
    "happy learning", "keep practicing", "feel free",
    "walk you through", "**", "##", "😊", "👍", "🎉", "📚",
    "\\frac", "\\sqrt",
)


# ---------------------------------------------------------------------------
# Per-fixture: shape, voice, values, sameness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fx", FIXTURES, ids=_FIXTURE_IDS)
def test_fixture_shapes_to_expected_answer_and_steps(fx):
    shaped = gemini_fallback._shape_result(fx["raw"])
    assert shaped is not None, fx["id"]
    assert shaped["answer"] == fx["answer"], fx["id"]
    assert shaped["steps"] == fx["steps"], fx["id"]
    # The honesty flags ride along exactly as before.
    assert shaped["type"] == "Ganitra"
    assert shaped["op"] == "gemini"
    assert shaped["fallback"] is True
    assert shaped["fallback_kind"] == "gemini"
    assert shaped["ai_generated"] is True


@pytest.mark.parametrize("fx", FIXTURES, ids=_FIXTURE_IDS)
def test_fixture_served_in_ganitra_voice(fx):
    shaped = gemini_fallback._shape_result(fx["raw"])
    served = _served_text(shaped)
    low = served.lower()
    for marker in _AI_ISM_MARKERS:
        assert marker not in low, (fx["id"], marker, served)
    # No step line carries the final-answer phrasing — the
    # one final line is the rendered "Answer: ..." itself.
    for step in shaped["steps"]:
        assert "answer:" not in step.lower(), (fx["id"], step)
        assert "the final answer is" not in step.lower()
        assert "the answer is" not in step.lower(), (
            fx["id"], step)


@pytest.mark.parametrize("fx", FIXTURES, ids=_FIXTURE_IDS)
def test_fixture_values_preserved(fx):
    shaped = gemini_fallback._shape_result(fx["raw"])
    served = _served_text(shaped)
    assert values_preserved(fx["raw"], served), (
        fx["id"], extract_values(fx["raw"]),
        extract_values(served))
    for expr in fx["expressions"]:
        assert expr in served, (fx["id"], expr, served)


@pytest.mark.parametrize("fx", FIXTURES, ids=_FIXTURE_IDS)
def test_fixture_not_a_verbatim_copy(fx):
    shaped = gemini_fallback._shape_result(fx["raw"])
    served = _served_text(shaped)
    assert served != fx["raw"], fx["id"]
    ratio = shared_line_ratio(fx["raw"], served)
    assert ratio is not None, fx["id"]
    assert ratio <= fx["max_shared"], (fx["id"], ratio)
    # The word-level overlap is reported in the wave notes;
    # here we only pin that a dressed reply is never a
    # near-total word copy (the wall-of-text fixture is the
    # honest exception: its words ARE the working, only the
    # line structure changes).
    if fx["id"] != "wall_of_text_profit":
        assert word_overlap(fx["raw"], served) < 0.97, (
            fx["id"], word_overlap(fx["raw"], served))


# ---------------------------------------------------------------------------
# The three legs end-to-end (HTTP mocked): each provider's
# dressed raw comes back in Ganitra's voice, restamped
# with that provider's honesty flags.
# ---------------------------------------------------------------------------

def _gemini_payload(text):
    return {"candidates": [{
        "content": {"parts": [{"text": text}]},
        "finishReason": "STOP"}]}


def _chat_payload(text):
    return {"choices": [{
        "message": {"content": text},
        "finish_reason": "stop"}]}


def test_gemini_leg_revoices(monkeypatch):
    fx = _fixture("gemini_area_between_curves")
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _gemini_payload(fx["raw"]))
    out = gemini_fallback.try_gemini_answer(fx["question"])
    assert out is not None
    assert out["fallback_kind"] == "gemini"
    assert out["answer"] == fx["answer"]
    assert out["steps"] == fx["steps"]


def test_groq_leg_revoices(monkeypatch):
    fx = _fixture("groq_linear_equation")
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(fx["raw"]))
    out = groq_fallback.try_groq_answer(fx["question"])
    assert out is not None
    assert out["fallback_kind"] == "groq"
    assert out["op"] == "groq"
    assert out["answer"] == fx["answer"]
    assert out["steps"] == fx["steps"]


def test_openrouter_leg_revoices(monkeypatch):
    fx = _fixture("openrouter_latex_identity")
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY",
                       "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(fx["raw"]))
    out = openrouter_fallback.try_openrouter_answer(
        fx["question"])
    assert out is not None
    assert out["fallback_kind"] == "openrouter"
    assert out["op"] == "openrouter"
    assert out["answer"] == fx["answer"]
    assert out["steps"] == fx["steps"]
    assert "\\frac" not in "\n".join(out["steps"])


# ---------------------------------------------------------------------------
# The prompt: all three legs share gemini_fallback's, and
# it now instructs the Ganitra Voice explicitly.
# ---------------------------------------------------------------------------

def test_prompt_instructs_ganitra_voice():
    prompt = gemini_fallback._build_prompt("2+2?", None)
    assert "Ganitra's own voice" in prompt
    assert "blackboard" in prompt
    assert "Simple, normal words" in prompt
    assert 'no "Sure"' in prompt
    assert 'no "Hope this helps"' in prompt
    assert 'no "As an AI"' in prompt
    assert "NOT_MATHS" in prompt
    assert "Answer:" in prompt
    assert "2+2?" in prompt
    # Wave 107 parity: the explicit-language line is
    # unchanged.
    hi = gemini_fallback._build_prompt("2+2?", "hi")
    assert "answer in Hindi" in hi


# ---------------------------------------------------------------------------
# Veto paths: unchanged by re-voicing
# ---------------------------------------------------------------------------

def test_veto_not_maths_sentinel():
    assert gemini_fallback._shape_result("NOT_MATHS") is None
    assert gemini_fallback._shape_result(
        "not_maths") is None


def test_veto_not_maths_leaking_mid_reply():
    # The sentinel on its own line anywhere is still the
    # sentinel — the honest fallback is served, never a
    # shaped "answer" built around the leak.
    raw = ("This question is about history, not maths.\n"
           "NOT_MATHS")
    assert gemini_fallback._shape_result(raw) is None
    raw2 = "Sure! NOT_MATHS"
    assert gemini_fallback._shape_result(raw2) is None


def test_veto_empty_and_pure_fluff():
    assert gemini_fallback._shape_result("") is None
    assert gemini_fallback._shape_result("   ") is None
    # A reply that is ONLY AI dressing has no answer in it.
    assert gemini_fallback._shape_result(
        "Sure! Hope this helps! 😊") is None
    assert gemini_fallback._shape_result(
        "Great question! Let's solve this step by step."
    ) is None


def test_veto_truncated_text_path_unchanged():
    # The Wave 119 guard refuses truncated replies at the
    # payload level (finishReason); at the TEXT level a
    # reply with no answer line keeps its pre-132 shape:
    # the last line becomes the answer. Pin that the
    # normalizer does not "fix" or drop any of it.
    raw = ("y = x^2\n"
           "y = x\n"
           "x^2 = x\n"
           "x^2 - x = 0\n"
           "x(x - 1) = 0\n"
           "x = 0 and")
    shaped = gemini_fallback._shape_result(raw)
    assert shaped is not None
    assert shaped["answer"] == "x = 0 and"
    assert shaped["steps"] == [
        "y = x^2", "y = x", "x^2 = x", "x^2 - x = 0",
        "x(x - 1) = 0"]


def test_clean_ai_text_shapes_exactly_as_before():
    # Wave 119's recorded full reply is already in the
    # house style — re-voicing must be a no-op on it.
    raw = ("y = x^2\n"
           "y = x\n"
           "x^2 = x\n"
           "x^2 - x = 0\n"
           "x(x - 1) = 0\n"
           "x = 0 and x = 1\n"
           "Area = integral from 0 to 1 of (x - x^2) dx\n"
           "Area = [x^2/2 - x^3/3] from 0 to 1\n"
           "Area = (1/2 - 1/3) - (0 - 0)\n"
           "Area = 1/2 - 1/3\n"
           "Area = 1/6\n"
           "Answer: 1/6 square units")
    shaped = gemini_fallback._shape_result(raw)
    assert shaped is not None
    assert shaped["answer"] == "1/6 square units"
    assert len(shaped["steps"]) == 11
    assert shaped["steps"][-1] == "Area = 1/6"


def test_answer_line_hai_forms():
    # The value-in-the-middle final lines of Hinglish and
    # Hindi replies land in the one final line too.
    shaped = gemini_fallback._shape_result(
        "3 × 4 = 12\nJawab 12 hai")
    assert shaped is not None
    assert shaped["answer"] == "12"
    assert shaped["steps"] == ["3 × 4 = 12"]
    shaped = gemini_fallback._shape_result(
        "क्षेत्रफल = 12 × 5 = 60\nउत्तर 60 वर्ग सेमी है")
    assert shaped is not None
    assert shaped["answer"] == "60 वर्ग सेमी"
    assert shaped["steps"] == ["क्षेत्रफल = 12 × 5 = 60"]
    # A hai-form line that is NOT the final statement (a
    # check mid-working) is left alone when a real final
    # line follows.
    shaped = gemini_fallback._shape_result(
        "Jawab 12 hai ya nahi, check karo\n"
        "3 × 4 = 12\nAnswer: 12")
    assert shaped is not None
    assert shaped["answer"] == "12"
    assert shaped["steps"][0].startswith("Jawab 12 hai")


def test_solver_answer_never_revoiced():
    # Ganitra's own answers are already in its voice — the
    # normalizer only ever runs inside the AI legs'
    # shaping. An exact solve through the real path is
    # untouched and never consults an AI leg.
    result = _solve_friendly("17 + 25")
    assert not result.get("fallback"), result
    assert result.get("answer") == "42"


# ---------------------------------------------------------------------------
# The value checker and the normalizer's self-guard
# ---------------------------------------------------------------------------

def test_value_checker_equivalences():
    # LaTeX and plain forms are the SAME value.
    assert extract_values(r"$\frac{1}{2}$") == \
        extract_values("1/2")
    assert extract_values(r"\sqrt{2}") == \
        extract_values("sqrt(2)")
    assert extract_values("1/x") == \
        extract_values(r"\frac{1}{x}")
    # List/step markers are numbering, not values.
    assert values_preserved("Step 1: x = 5\n2. x = 5",
                            "x = 5\nx = 5")
    # Real changes are caught.
    assert not values_preserved("x = 5", "x = 6")
    assert not values_preserved("Area = 1/2", "Area = 1/3")
    assert not values_preserved("Doori = 216 km",
                                "Doori = 216")
    assert not values_preserved("x = 5", "x = 5 and y = 7")


def test_latex_converts_to_plain_notation():
    raw = ("$(x + \\frac{1}{x})^2 = 25$\n"
           "Answer: 25")
    out = normalize_ai_text(raw)
    assert "(x + 1/x)^2 = 25" in out
    assert "\\frac" not in out and "$" not in out


def test_normalizer_declines_rather_than_lose_a_value(
        monkeypatch):
    # If the normalization itself ever lost a value, the
    # guard must serve the raw text instead of the lossy
    # output. Simulate a broken normalizer and pin the
    # guard's behaviour.
    monkeypatch.setattr(
        ganitra_voice, "_normalize",
        lambda text: "x = 2")
    raw = "x = 5\nAnswer: 5"
    assert normalize_ai_text(raw) == raw


def test_phrase_list_coverage():
    # The pinned lists are the spec: every category the
    # voice rule names must be represented.
    openers = " ".join(ganitra_voice.PREFIX_OPENERS).lower()
    for needle in ("sure", "of course", "certainly",
                   "great question", "here's the solution",
                   "let's solve", "as an ai",
                   "bilkul", "आइए"):
        assert needle in openers, needle
    fluff = " ".join(ganitra_voice.FLUFF_LINES).lower()
    for needle in ("hope this helps", "let me know",
                   "happy learning", "keep practicing",
                   "feel free to ask",
                   "koi doubt ho to pucho",
                   "आशा है यह मदद करेगा"):
        assert needle in fluff, needle
    labels = " ".join(ganitra_voice.LABEL_LINES).lower()
    for needle in ("solution", "working", "दिया है"):
        assert needle in labels, needle
