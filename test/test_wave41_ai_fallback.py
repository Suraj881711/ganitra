"""Wave 41 (Suraj, 15 Nov 2026): AI fallback v2 — the Gemini
model chain, plus Groq as the second free brain.

Wave 37 hardcoded gemini-2.5-flash, which Google has gated
OFF for new users (404). These tests pin, with BOTH HTTP
layers MOCKED (gemini_fallback._post_json and
groq_fallback._post_json — no network, no real keys):

- the Gemini chain walks its ordered models: a model-level
  failure (404 / 429 / 503) moves to the next model, and the
  gated-off gemini-2.5-flash is never requested;
- a NON-model failure (timeout, 400 error body) does not
  waste the chain — Gemini returns None at once, as before;
- through the real user path (api._solve_friendly), Groq is
  consulted ONLY after Gemini returned None, and never when
  Gemini answered;
- with NEITHER key set, both modules are pure no-ops and the
  pre-Wave-37 fallback behaviour is unchanged;
- a science question is still refused by the science guard
  and reaches NEITHER provider.
"""
import urllib.error

import pytest

import gemini_fallback
import groq_fallback
from api import _solve_friendly

AGES_Q = ("The sum of the ages of a father and his son is "
          "45 years. Five years ago, the product of their ages "
          "was 124. Find their present ages.")

SCIENCE_Q = ("A ray of light travels from medium A to medium "
             "B. The refractive index of medium B relative to "
             "medium A is 1.5, and the speed of light in "
             "medium A is 2 x 10^8 m/s. What is the speed of "
             "light in medium B?")

GEMINI_TEXT = (
    "Let the son's age be x years\n"
    "Father's age = 45 - x\n"
    "x^2 - 45x + 324 = 0\n"
    "Answer: Son is 9 years old and father is 36 years old")

GROQ_TEXT = (
    "Let the son's age be x years\n"
    "Father's age = 45 - x\n"
    "x^2 - 45x + 324 = 0\n"
    "Answer: Son is 9 years old and father is 36 years old")


def _gemini_payload(text):
    return {"candidates": [
        {"content": {"parts": [{"text": text}]}}]}


def _groq_payload(text):
    return {"choices": [{"message": {"content": text}}]}


def _http_error(url, code):
    return urllib.error.HTTPError(url, code, "err", None, None)


# ---------------------------------------------------------------------------
# The Gemini model chain (module level, mocked transport)
# ---------------------------------------------------------------------------

def test_gemini_chain_falls_through_on_404(monkeypatch):
    calls = []

    def fake_post(url, payload, api_key, timeout):
        calls.append(url)
        if "gemini-3-flash-preview" in url:
            raise _http_error(url, 404)
        return _gemini_payload(GEMINI_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    out = gemini_fallback.try_gemini_answer(AGES_Q)
    assert out is not None
    assert out.get("fallback_kind") == "gemini"
    assert out.get("answer") == (
        "Son is 9 years old and father is 36 years old")
    # Order: preview first, lite second — and never 2.5-flash.
    assert len(calls) == 2
    assert "gemini-3-flash-preview" in calls[0]
    assert "gemini-3.1-flash-lite" in calls[1]
    assert all("gemini-2.5-flash" not in u for u in calls)
    assert gemini_fallback.MODELS == [
        "gemini-3-flash-preview", "gemini-3.1-flash-lite"]
    assert gemini_fallback.MODEL == gemini_fallback.MODELS[0]


def test_gemini_chain_falls_through_on_error_body(monkeypatch):
    calls = []

    def fake_post(url, payload, api_key, timeout):
        calls.append(url)
        if "gemini-3-flash-preview" in url:
            return {"error": {"code": 503,
                              "status": "UNAVAILABLE",
                              "message": "model overloaded"}}
        return _gemini_payload(GEMINI_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    out = gemini_fallback.try_gemini_answer(AGES_Q)
    assert out is not None and out.get("fallback_kind") == "gemini"
    assert len(calls) == 2


def test_gemini_chain_exhausted_returns_none(monkeypatch):
    calls = []

    def fake_post(url, payload, api_key, timeout):
        calls.append(url)
        raise _http_error(url, 429)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    assert gemini_fallback.try_gemini_answer(AGES_Q) is None
    assert len(calls) == len(gemini_fallback.MODELS)


def test_gemini_non_model_failure_does_not_chain(monkeypatch):
    calls = []

    def timeout_post(url, payload, api_key, timeout):
        calls.append(url)
        raise TimeoutError("timed out")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", timeout_post)
    assert gemini_fallback.try_gemini_answer(AGES_Q) is None
    assert len(calls) == 1  # a timeout is not model-specific

    calls.clear()

    def bad_request(url, payload, api_key, timeout):
        calls.append(url)
        return {"error": {"code": 400,
                          "status": "INVALID_ARGUMENT",
                          "message": "API key not valid."}}

    monkeypatch.setattr(gemini_fallback, "_post_json", bad_request)
    assert gemini_fallback.try_gemini_answer(AGES_Q) is None
    assert len(calls) == 1  # a 400 is not model-specific either


# ---------------------------------------------------------------------------
# Groq through the real user path: only after Gemini None
# ---------------------------------------------------------------------------

@pytest.fixture
def both_spies(monkeypatch):
    """Recording stand-ins for BOTH HTTP layers, dummy keys
    set, and a shared order log. Gemini times out by default
    (returns None); tests override behaviour via the dict."""
    order = []
    state = {"gemini": "timeout", "groq": "ok"}

    def fake_gemini(url, payload, api_key, timeout):
        order.append("gemini")
        if state["gemini"] == "timeout":
            raise TimeoutError("timed out")
        if state["gemini"] == "ok":
            return _gemini_payload(GEMINI_TEXT)
        raise AssertionError(state["gemini"])

    def fake_groq(url, payload, api_key, timeout):
        order.append("groq")
        if state["groq"] == "ok":
            return _groq_payload(GROQ_TEXT)
        raise AssertionError(state["groq"])

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_gemini)
    monkeypatch.setattr(groq_fallback, "_post_json", fake_groq)
    return order, state


def test_groq_used_only_after_gemini_none(both_spies):
    order, _state = both_spies
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "groq", result
    assert result.get("op") == "groq"
    assert result.get("ai_generated") is True
    assert result.get("fallback") is True
    assert result.get("answer") == (
        "Son is 9 years old and father is 36 years old")
    assert order == ["gemini", "groq"]  # Gemini first, Groq second


def test_groq_not_called_when_gemini_answers(both_spies):
    order, state = both_spies
    state["gemini"] = "ok"
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "gemini", result
    assert order == ["gemini"]


def test_groq_payload_and_shaping(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen.update(url=url, payload=payload, api_key=api_key,
                    timeout=timeout)
        return _groq_payload(
            "Step 1: 2x + 3 = 7\n"
            "2x = 4\n"
            "**Answer: x = 2**")

    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(groq_fallback, "_post_json", fake_post)
    out = groq_fallback.try_groq_answer("solve 2x + 3 = 7")
    assert out is not None
    assert out["fallback_kind"] == "groq" and out["op"] == "groq"
    assert out["answer"] == "x = 2"
    assert out["steps"] == ["2x + 3 = 7", "2x = 4"]
    assert out["fallback"] is True and out["ai_generated"] is True
    assert seen["url"] == groq_fallback.API_URL
    assert seen["payload"]["model"] == "openai/gpt-oss-120b"
    assert seen["payload"]["temperature"] == 0.2
    assert seen["payload"]["max_tokens"] == 1024
    sent = seen["payload"]["messages"][0]["content"]
    assert "solve 2x + 3 = 7" in sent and "NOT_MATHS" in sent
    assert seen["timeout"] == groq_fallback.TIMEOUT_SECONDS


def test_groq_not_maths_sentinel_returns_none(monkeypatch):
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(
        groq_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _groq_payload("NOT_MATHS"))
    assert groq_fallback.try_groq_answer(AGES_Q) is None


# ---------------------------------------------------------------------------
# No keys at all: pure no-op, pre-Wave-37 behaviour unchanged
# ---------------------------------------------------------------------------

def test_both_no_keys_pure_noop(monkeypatch):
    calls = []

    def recorder(tag):
        def fake(url, payload, api_key, timeout):
            calls.append(tag)
            return {}
        return fake

    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.setattr(gemini_fallback, "_post_json",
                        recorder("gemini"))
    monkeypatch.setattr(groq_fallback, "_post_json",
                        recorder("groq"))
    assert gemini_fallback.try_gemini_answer(AGES_Q) is None
    assert groq_fallback.try_groq_answer(AGES_Q) is None
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")
    assert calls == []


# ---------------------------------------------------------------------------
# The science guard still refuses before either provider
# ---------------------------------------------------------------------------

def test_science_question_reaches_neither_provider(both_spies):
    order, _state = both_spies
    result = _solve_friendly(SCIENCE_Q)
    assert result.get("fallback_kind") == "science", result
    assert "Maths" in str(result.get("answer", ""))
    assert order == []
