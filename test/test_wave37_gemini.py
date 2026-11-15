"""Wave 37 (Suraj, 14 Nov 2026: "paid kyu lena" — the FREE
Gemini route, delegated to Muse): solver first, Gemini only
as the fallback.

These tests pin the contract through the real user path
(api._solve_friendly), with the Gemini HTTP layer MOCKED
(gemini_fallback._post_json) — no network, no real key:

- an exact solver answer NEVER calls Gemini;
- a question the Wave-18 layers could only meet with a
  similar example / concept card / guide IS upgraded to a
  Gemini answer, shaped into the house format (plain steps,
  one plain final answer line, honesty flags set);
- a missing key, a timeout and an API error all degrade to
  the previous fallback behaviour, byte for byte in kind;
- a science question stays refused by the science guard and
  Gemini is never consulted for it.
"""
import urllib.error

import pytest

import gemini_fallback
import solver.answer_cache as cache
from api import _solve_friendly


@pytest.fixture(autouse=True)
def _clean_caches():
    # Merge-2: Wave 48's negative cache is process-global, and
    # these tests mock the Gemini transport per test for shared
    # probe questions — each test must start from a clean cache
    # (the same isolation Wave 48's own tests use), or a guide
    # result stored by a missing-key test would be served to a
    # later test before its mocked transport is ever consulted.
    cache.clear_cache()
    yield
    cache.clear_cache()

# Wave 56: the original fixture (sum 45, product 124 five
# years ago) is now solved DETERMINISTICALLY by the new
# ages schema in solver/applied.py — it is battery #88 —
# so it can no longer stand in for "a question the solver
# cannot answer". This two-condition ages question (still
# father-and-son present ages) remains unsolved by the
# pattern solver and keeps every assertion below honest.
AGES_Q = ("Ten years ago, a father was twelve times as "
          "old as his son and ten years hence, he will be "
          "twice as old as his son. Find their present ages.")

SCIENCE_Q = ("A ray of light travels from medium A to medium "
             "B. The refractive index of medium B relative to "
             "medium A is 1.5, and the speed of light in "
             "medium A is 2 x 10^8 m/s. What is the speed of "
             "light in medium B?")

GEMINI_TEXT = (
    "Let the son's age be x years\n"
    "Father's age = 45 - x\n"
    "Five years ago: (x - 5)(40 - x) = 124\n"
    "x^2 - 45x + 324 = 0\n"
    "(x - 9)(x - 36) = 0\n"
    "x = 9 or x = 36\n"
    "Answer: Son is 9 years old and father is 36 years old")


def _payload(text):
    return {"candidates": [
        {"content": {"parts": [{"text": text}]}}]}


@pytest.fixture
def gemini_spy(monkeypatch):
    """A recording stand-in for the HTTP layer, plus a dummy
    key in the environment. Returns the list of calls made."""
    calls = []

    def fake_post(url, payload, api_key, timeout):
        calls.append({"url": url, "payload": payload,
                      "api_key": api_key, "timeout": timeout})
        return _payload(GEMINI_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    return calls


def test_exact_solve_never_calls_gemini(gemini_spy):
    for q, expected in (("17 + 25", "42"),
                        ("solve 2x + 3 = 7", "x = 2")):
        result = _solve_friendly(q)
        assert not result.get("fallback"), (q, result)
        assert expected in str(result.get("answer", "")), (q, result)
    assert gemini_spy == []


def test_fallback_question_is_upgraded_by_gemini(gemini_spy):
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") == "gemini", result
    assert result.get("ai_generated") is True
    assert result.get("answer") == (
        "Son is 9 years old and father is 36 years old")
    steps = result.get("steps") or []
    assert len(steps) >= 3
    assert all("Answer:" not in s for s in steps)
    assert all(not s[:1].isdigit() or "x" in s[:3] for s in steps)
    assert len(gemini_spy) == 1
    sent = gemini_spy[0]["payload"]["contents"][0]["parts"][0]["text"]
    assert AGES_Q in sent
    assert "Answer:" in sent  # the house-style instruction rides along
    assert gemini_spy[0]["timeout"] == gemini_fallback.TIMEOUT_SECONDS


def test_missing_key_keeps_old_fallback(monkeypatch):
    calls = []

    def fake_post(url, payload, api_key, timeout):
        calls.append(1)
        return _payload(GEMINI_TEXT)

    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")
    assert calls == []


def test_timeout_keeps_old_fallback(monkeypatch):
    def boom(url, payload, api_key, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", boom)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")


def test_api_error_keeps_old_fallback(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")

    def error_payload(url, payload, api_key, timeout):
        return {"error": {"code": 400, "status": "INVALID_ARGUMENT",
                          "message": "API key not valid."}}

    monkeypatch.setattr(gemini_fallback, "_post_json", error_payload)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")

    def http_error(url, payload, api_key, timeout):
        raise urllib.error.HTTPError(url, 429, "quota", None, None)

    monkeypatch.setattr(gemini_fallback, "_post_json", http_error)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")


def test_not_maths_sentinel_keeps_old_fallback(monkeypatch):
    def sentinel(url, payload, api_key, timeout):
        return _payload("NOT_MATHS")

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", sentinel)
    result = _solve_friendly(AGES_Q)
    assert result.get("fallback_kind") in ("similar", "concept",
                                           "guide")


def test_science_question_stays_refused(gemini_spy):
    result = _solve_friendly(SCIENCE_Q)
    assert result.get("fallback_kind") == "science", result
    assert "Maths" in str(result.get("answer", ""))
    assert gemini_spy == []


def test_nonmaths_question_never_calls_gemini(gemini_spy):
    result = _solve_friendly("what is the capital of india")
    assert result.get("fallback_kind") == "nonmaths", result
    assert gemini_spy == []


def test_prompt_names_detected_language(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["text"] = payload["contents"][0]["parts"][0]["text"]
        return _payload(GEMINI_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json", fake_post)
    out = gemini_fallback.try_gemini_answer(
        "ek train 60 km/h se chalti hai", "hi")
    assert out is not None and out.get("fallback_kind") == "gemini"
    assert "Hindi" in seen["text"]


def test_shape_result_strips_labels_and_markdown():
    raw = ("Step 1: 2x + 3 = 7\n"
           "2. 2x = 4\n"
           "- x = 2\n"
           "**Answer: 2**")
    shaped = gemini_fallback._shape_result(raw)
    assert shaped is not None
    assert shaped["answer"] == "2"
    assert shaped["steps"] == ["2x + 3 = 7", "2x = 4", "x = 2"]
    assert gemini_fallback._shape_result("NOT_MATHS") is None
    assert gemini_fallback._shape_result("   ") is None
