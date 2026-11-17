"""Wave 119: AI fallback answers arrived TRUNCATED at the
final answer line (found in Deploy-24 live verification,
17 Nov 2026): "Find the area between the curves y = x^2 and
y = x" engaged Gemini, set up the integral correctly, then
cut off mid-expression — the value 1/6 never appeared, and
the full-solution page read "The final answer is x = 0 and
— follow the steps above…".

Root cause (proven against the real API with the app's own
prompt and payload): the chain's primary model,
gemini-3-flash-preview, is a THINKING model whose reasoning
tokens count against maxOutputTokens. The Wave-37 cap of
1024 was almost entirely consumed by thinking (979 thoughts
tokens measured), leaving 41 tokens of visible text —
finishReason MAX_TOKENS, the reply cut mid-line at
"x = 0 and" — and nothing in the app inspected finishReason,
so the cut text was shaped and served as a complete answer.

These tests pin the fix with the HTTP layer mocked
(gemini_fallback / groq_fallback / openrouter_fallback
._post_json) — no network, no real keys:

- the recorded truncated payload (finishReason MAX_TOKENS,
  text ending "x = 0 and") is NEVER served: the Gemini chain
  moves to the next model, and if every model truncates the
  leg returns None (the honest fallback), not a cut answer;
- a long multi-step reply ending in a fraction survives end
  to end — through api._solve_friendly, and into the
  full-solution page's summary sentence (i18n
  explanation_for) — with the final value 1/6 present;
- the request payloads carry the raised budget (8192) on all
  three legs;
- the Groq / OpenRouter legs refuse a reply the provider cut
  at the cap (finish_reason "length") the same way.
"""
import pytest

import gemini_fallback
import groq_fallback
import openrouter_fallback
import solver.answer_cache as cache
from api import _solve_friendly
from i18n import explanation_for


@pytest.fixture(autouse=True)
def _clean_caches():
    # Same isolation as test_wave37: the negative cache is
    # process-global and these tests mock the AI transport
    # per test for a shared probe question.
    cache.clear_cache()
    yield
    cache.clear_cache()


PROBE_Q = "Find the area between the curves y = x^2 and y = x"

# The reply the real API returned under the old 1024 cap
# (recorded live 17 Nov 2026): finishReason MAX_TOKENS,
# 979 thoughts tokens, the visible text cut mid-line.
TRUNCATED_TEXT = (
    "y = x^2\n"
    "y = x\n"
    "x^2 = x\n"
    "x^2 - x = 0\n"
    "x(x - 1) = 0\n"
    "x = 0 and")

# The same question answered completely (finishReason STOP):
# a multi-step integral working that ends in a fraction.
FULL_TEXT = (
    "y = x^2\n"
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


def _gemini_payload(text, finish_reason):
    return {"candidates": [{
        "content": {"parts": [{"text": text}]},
        "finishReason": finish_reason}]}


def _chat_payload(text, finish_reason):
    return {"choices": [{
        "message": {"content": text},
        "finish_reason": finish_reason}]}


# ---------------------------------------------------------------------------
# Gemini leg
# ---------------------------------------------------------------------------

def test_gemini_request_uses_raised_budget(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen.update(payload)
        return _gemini_payload(FULL_TEXT, "STOP")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    out = gemini_fallback.try_gemini_answer(PROBE_Q)
    assert out is not None
    cap = seen["generationConfig"]["maxOutputTokens"]
    assert cap == gemini_fallback.MAX_OUTPUT_TOKENS
    assert cap == 8192 and cap > 1024


def test_full_answer_survives_shaping(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _gemini_payload(FULL_TEXT, "STOP"))
    out = gemini_fallback.try_gemini_answer(PROBE_Q)
    assert out is not None
    assert out["answer"] == "1/6 square units"
    assert out["steps"][-1] == "Area = 1/6"
    assert "x = 0 and x = 1" in out["steps"]
    assert len(out["steps"]) == 11


def test_truncated_primary_moves_to_next_model(monkeypatch):
    calls = []

    def dispatch(url, payload, api_key, timeout):
        calls.append(url)
        if "gemini-3-flash-preview" in url:
            return _gemini_payload(TRUNCATED_TEXT, "MAX_TOKENS")
        return _gemini_payload(FULL_TEXT, "STOP")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", dispatch)
    out = gemini_fallback.try_gemini_answer(PROBE_Q)
    # The cut reply was NOT served; the chain walked on and
    # the complete answer came back instead.
    assert len(calls) == 2
    assert out is not None
    assert out["answer"] == "1/6 square units"


def test_all_models_truncated_returns_none(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(
        gemini_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _gemini_payload(TRUNCATED_TEXT, "MAX_TOKENS"))
    # Never serve a cut answer: the leg degrades to None and
    # the caller serves the honest Wave-18 fallback.
    assert gemini_fallback.try_gemini_answer(PROBE_Q) is None


def test_was_truncated_helper():
    assert gemini_fallback._was_truncated(
        _gemini_payload("x", "MAX_TOKENS")) is True
    assert gemini_fallback._was_truncated(
        _gemini_payload("x", "STOP")) is False
    assert gemini_fallback._was_truncated(
        {"candidates": [{"content": {"parts": []}}]}) is False
    assert gemini_fallback._was_truncated({}) is False
    assert gemini_fallback._was_truncated(None) is False


def test_probe_end_to_end_through_solve_friendly(monkeypatch):
    """The Deploy-24 live defect, replayed through the real
    user path: primary model truncates, the student must
    still receive the complete answer — in the chat result
    AND in the full-solution page's summary sentence."""

    def dispatch(url, payload, api_key, timeout):
        if "gemini-3-flash-preview" in url:
            return _gemini_payload(TRUNCATED_TEXT, "MAX_TOKENS")
        return _gemini_payload(FULL_TEXT, "STOP")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", dispatch)
    result = _solve_friendly(PROBE_Q)
    assert result["fallback_kind"] == "gemini"
    assert result["answer"] == "1/6 square units"
    assert result["steps"][-1] == "Area = 1/6"
    page_line = explanation_for(result, "en")
    assert "1/6 square units" in page_line
    assert "x = 0 and" not in page_line


# ---------------------------------------------------------------------------
# Groq leg (reasoning model, same latent pattern)
# ---------------------------------------------------------------------------

def test_groq_truncated_reply_returns_none(monkeypatch):
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(TRUNCATED_TEXT, "length"))
    assert groq_fallback.try_groq_answer(PROBE_Q) is None


def test_groq_full_answer_and_raised_budget(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen.update(payload)
        return _chat_payload(FULL_TEXT, "stop")

    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(groq_fallback, "_post_json", fake_post)
    out = groq_fallback.try_groq_answer(PROBE_Q)
    assert out is not None
    assert out["fallback_kind"] == "groq"
    assert out["answer"] == "1/6 square units"
    assert out["steps"][-1] == "Area = 1/6"
    assert seen["max_tokens"] == groq_fallback.MAX_TOKENS == 8192


# ---------------------------------------------------------------------------
# OpenRouter leg (free router can land on a reasoning model)
# ---------------------------------------------------------------------------

def test_openrouter_truncated_reply_returns_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload(TRUNCATED_TEXT, "length"))
    assert openrouter_fallback.try_openrouter_answer(PROBE_Q) is None


def test_openrouter_full_answer_and_raised_budget(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen.update(payload)
        return _chat_payload(FULL_TEXT, "stop")

    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_fallback, "_post_json", fake_post)
    out = openrouter_fallback.try_openrouter_answer(PROBE_Q)
    assert out is not None
    assert out["fallback_kind"] == "openrouter"
    assert out["answer"] == "1/6 square units"
    assert out["steps"][-1] == "Area = 1/6"
    assert seen["max_tokens"] == \
        openrouter_fallback.MAX_TOKENS == 8192
