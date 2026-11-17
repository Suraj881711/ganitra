"""Wave 108 (Suraj, 17 Nov 2026): OpenRouter — the THIRD
free AI brain, behind Gemini and Groq, for backup.

The chain is now solver -> Gemini -> Groq -> OpenRouter.
These tests pin, with ALL THREE HTTP layers MOCKED
(gemini_fallback._post_json, groq_fallback._post_json and
openrouter_fallback._post_json — no network, no real keys):

- with the OpenRouter key absent, the new module is a pure
  no-op: it returns None and makes NO network call, and the
  chain's behaviour is exactly the pre-Wave-108 behaviour;
- through the real user path (api._solve_friendly),
  OpenRouter is consulted ONLY after BOTH Gemini and Groq
  returned None, and never when either of them answered;
- OpenRouter's known stall hazard is contained: a timeout
  (or any transport/HTTP error, an error body, a non-dict or
  non-JSON reply) returns None and the chain still settles
  cleanly on the honest Wave-18 outcome;
- the shaped result matches the house format exactly — the
  same fields and flags the Gemini/Groq legs produce, with
  op / fallback_kind restamped to "openrouter";
- the model slug is OpenRouter's free router
  ("openrouter/free"), never a named ":free" slug, and the
  timeout is strictly shorter than the Gemini/Groq 15s.
"""
import json
import urllib.error

import pytest

import gemini_fallback
import groq_fallback
import openrouter_fallback
import solver.answer_cache as cache
from api import _solve_friendly


@pytest.fixture(autouse=True)
def _clean_caches():
    # Same isolation as test_wave41_ai_fallback: Wave 48's
    # negative cache is process-global, and these tests mock
    # the AI transports per test for shared probe questions.
    cache.clear_cache()
    yield
    cache.clear_cache()


# The same still-unsolved probe question Wave 41 uses (see
# its note: the two-condition ages question the pattern
# solver cannot answer deterministically).
AGES_Q = ("Ten years ago, a father was twelve times as "
          "old as his son and ten years hence, he will be "
          "twice as old as his son. Find their present ages.")

SCIENCE_Q = ("A ray of light travels from medium A to medium "
             "B. The refractive index of medium B relative to "
             "medium A is 1.5, and the speed of light in "
             "medium A is 2 x 10^8 m/s. What is the speed of "
             "light in medium B?")

OPENROUTER_TEXT = (
    "Let the son's age be x years\n"
    "Father's age = 45 - x\n"
    "x^2 - 45x + 324 = 0\n"
    "Answer: Son is 9 years old and father is 36 years old")

GROQ_TEXT = OPENROUTER_TEXT
GEMINI_TEXT = OPENROUTER_TEXT


def _gemini_payload(text):
    return {"candidates": [
        {"content": {"parts": [{"text": text}]}}]}


def _chat_payload(text):
    return {"choices": [{"message": {"content": text}}]}


def _http_error(url, code):
    return urllib.error.HTTPError(url, code, "err", None, None)


# ---------------------------------------------------------------------------
# Module level: key handling, payload, shaping (mocked transport)
# ---------------------------------------------------------------------------

def test_openrouter_no_key_returns_none_and_makes_no_call(monkeypatch):
    calls = []

    def recorder(url, payload, api_key, timeout):
        calls.append(url)
        return _chat_payload(OPENROUTER_TEXT)

    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        recorder)
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None
    assert calls == []


def test_openrouter_empty_question_returns_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda *a: (_ for _ in ()).throw(
            AssertionError("must not be called")))
    assert openrouter_fallback.try_openrouter_answer("") is None
    assert openrouter_fallback.try_openrouter_answer("   ") is None
    assert openrouter_fallback.try_openrouter_answer(None) is None


def test_openrouter_payload_and_shaping(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen.update(url=url, payload=payload, api_key=api_key,
                    timeout=timeout)
        return _chat_payload(
            "Step 1: 2x + 3 = 7\n"
            "2x = 4\n"
            "**Answer: x = 2**")

    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_fallback, "_post_json", fake_post)
    out = openrouter_fallback.try_openrouter_answer("solve 2x + 3 = 7")
    assert out is not None
    # House format: exactly the fields the other legs produce.
    assert set(out) == {"type", "op", "answer", "steps",
                        "fallback", "fallback_kind", "ai_generated"}
    assert out["type"] == "Ganitra"
    assert out["fallback_kind"] == "openrouter"
    assert out["op"] == "openrouter"
    assert out["answer"] == "x = 2"
    assert out["steps"] == ["2x + 3 = 7", "2x = 4"]
    assert out["fallback"] is True and out["ai_generated"] is True
    assert seen["url"] == openrouter_fallback.API_URL
    assert seen["url"] == (
        "https://openrouter.ai/api/v1/chat/completions")
    assert seen["api_key"] == "test-key"
    # The free ROUTER slug — never a named ":free" model.
    assert seen["payload"]["model"] == "openrouter/free"
    assert openrouter_fallback.MODEL == "openrouter/free"
    assert seen["payload"]["temperature"] == 0.2
    # Wave 119: the cap was raised 1024 -> 8192 (a reasoning
    # model's thinking counts toward it; 1024 truncated
    # worked answers mid-line).
    assert seen["payload"]["max_tokens"] == \
        openrouter_fallback.MAX_TOKENS
    sent = seen["payload"]["messages"][0]["content"]
    assert "solve 2x + 3 = 7" in sent and "NOT_MATHS" in sent
    # The stall guard: a strict timeout, no longer than the
    # Gemini/Groq legs' 15s.
    assert seen["timeout"] == openrouter_fallback.TIMEOUT_SECONDS
    assert openrouter_fallback.TIMEOUT_SECONDS <= 15
    assert openrouter_fallback.TIMEOUT_SECONDS <= (
        groq_fallback.TIMEOUT_SECONDS)


def test_openrouter_lang_flows_into_prompt(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["content"] = payload["messages"][0]["content"]
        return _chat_payload(OPENROUTER_TEXT)

    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter_fallback, "_post_json", fake_post)
    out = openrouter_fallback.try_openrouter_answer(AGES_Q, "hi")
    assert out is not None
    # Same lang handling as the other legs: gemini_fallback's
    # prompt builder names the requested language explicitly.
    assert "Hindi" in seen["content"]


def test_openrouter_timeout_and_stall_return_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")

    def timeout_post(url, payload, api_key, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        timeout_post)
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None

    def stall_post(url, payload, api_key, timeout):
        # The databank hazard: the read simply never answers —
        # urlopen surfaces it as a timeout/reset error.
        raise ConnectionResetError("connection reset")

    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        stall_post)
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None


def test_openrouter_http_and_error_body_return_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout: (_ for _ in ()).throw(
            _http_error(url, 429)))
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None

    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            {"error": {"code": 503, "message": "no free provider"}})
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None


def test_openrouter_non_dict_and_non_json_return_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout: ["not", "a", "dict"])
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None

    def garbage_post(url, payload, api_key, timeout):
        # What _post_json does when the body is not JSON at
        # all: json.loads raises, the module degrades to None.
        raise json.JSONDecodeError("Expecting value", "<html>", 0)

    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        garbage_post)
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None


def test_openrouter_post_json_rejects_non_json_body(monkeypatch):
    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b"<html>temporarily unavailable</html>"

    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout=None: _Resp())
    with pytest.raises(json.JSONDecodeError):
        openrouter_fallback._post_json(
            openrouter_fallback.API_URL, {"model": "x"},
            "test-key", 5)


def test_openrouter_not_maths_and_empty_return_none(monkeypatch):
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout:
            _chat_payload("NOT_MATHS"))
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None

    monkeypatch.setattr(
        openrouter_fallback, "_post_json",
        lambda url, payload, api_key, timeout: {"choices": []})
    assert openrouter_fallback.try_openrouter_answer(AGES_Q) is None


# ---------------------------------------------------------------------------
# Through the real user path: third in the chain after both
# Gemini and Groq returned None — and, since Wave 133, as a
# consensus second/third opinion when an earlier leg's answer
# carries an unverifiable-by-arithmetic value
# ---------------------------------------------------------------------------

@pytest.fixture
def three_spies(monkeypatch):
    """Recording stand-ins for ALL THREE HTTP layers, dummy
    keys set, and a shared order log. Gemini and Groq time
    out by default (return None); OpenRouter answers."""
    order = []
    state = {"gemini": "timeout", "groq": "timeout",
             "openrouter": "ok"}

    def fake_gemini(url, payload, api_key, timeout):
        order.append("gemini")
        if state["gemini"] == "timeout":
            raise TimeoutError("timed out")
        if state["gemini"] == "ok":
            return _gemini_payload(GEMINI_TEXT)
        raise AssertionError(state["gemini"])

    def fake_groq(url, payload, api_key, timeout):
        order.append("groq")
        if state["groq"] == "timeout":
            raise TimeoutError("timed out")
        if state["groq"] == "ok":
            return _chat_payload(GROQ_TEXT)
        raise AssertionError(state["groq"])

    def fake_openrouter(url, payload, api_key, timeout):
        order.append("openrouter")
        if state["openrouter"] == "ok":
            return _chat_payload(OPENROUTER_TEXT)
        if state["openrouter"] == "timeout":
            raise TimeoutError("timed out")
        raise AssertionError(state["openrouter"])

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_gemini)
    monkeypatch.setattr(groq_fallback, "_post_json", fake_groq)
    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        fake_openrouter)
    return order, state


def test_openrouter_used_only_after_gemini_and_groq_none(three_spies):
    order, _state = three_spies
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "openrouter", result
    assert result.get("op") == "openrouter"
    assert result.get("ai_generated") is True
    assert result.get("fallback") is True
    assert result.get("answer") == (
        "Son is 9 years old and father is 36 years old")
    # Full order: Gemini first, Groq second, OpenRouter third.
    assert order == ["gemini", "groq", "openrouter"]


def test_openrouter_consulted_for_consensus_when_groq_answers(
        three_spies):
    # Wave 133 DELIBERATE FLIP of the Wave 108 pin "OpenRouter
    # is never called when Groq answered": Groq's answer here
    # carries a final value no deterministic check can judge,
    # so the verification gate asks OpenRouter for a second
    # opinion before serving. Its text states the SAME final
    # ages, so Groq's answer is served, consensus-verified.
    order, state = three_spies
    state["groq"] = "ok"
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "groq", result
    assert result.get("ai_verification") == "consensus"
    assert order == ["gemini", "groq", "openrouter"]


def test_openrouter_consulted_for_consensus_when_gemini_answers(
        three_spies):
    # Wave 133 DELIBERATE FLIP, same reasoning: Gemini's
    # unverifiable-by-arithmetic answer is cross-checked —
    # Groq times out (no vote), OpenRouter agrees with
    # Gemini's stated ages, so Gemini's answer is served,
    # consensus-verified.
    order, state = three_spies
    state["gemini"] = "ok"
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "gemini", result
    assert result.get("ai_verification") == "consensus"
    assert order == ["gemini", "groq", "openrouter"]


def test_openrouter_timeout_chain_still_settles_cleanly(three_spies):
    order, state = three_spies
    state["openrouter"] = "timeout"
    result = _solve_friendly(AGES_Q)
    # All three brains missed: the honest Wave-18/67 outcome,
    # served exactly as before Wave 108.
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide", "not_found")
    assert result.get("ai_generated") is not True
    assert order == ["gemini", "groq", "openrouter"]


def test_openrouter_key_absent_chain_unchanged(three_spies,
                                               monkeypatch):
    order, _state = three_spies
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide", "not_found")
    # Gemini and Groq were consulted; OpenRouter's HTTP layer
    # was never touched without a key.
    assert order == ["gemini", "groq"]


def test_science_question_reaches_no_provider(three_spies):
    order, _state = three_spies
    result = _solve_friendly(SCIENCE_Q)
    assert result.get("fallback_kind") == "science", result
    assert "Maths" in str(result.get("answer", ""))
    assert order == []
