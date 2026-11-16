"""Wave 97 (speed): response-time cuts with ZERO behaviour change.

What was slow (profiled on the Wave 71 audit battery, cold cache,
through api._solve_friendly):

1. Regex recompilation dominated everything: the pipeline uses
   600+ distinct patterns, the stdlib `re` cache holds 512 and
   CLEARS when full, so hard questions recompiled nearly every
   pattern on every search — 18,138 compiles / 24.5 s of one
   27.3 s answer. Fix: solver/__init__.py raises the `re` cache
   ceiling at package import (compiled patterns are the same
   objects `re` itself caches; semantics cannot change).
2. Raw solver failures (op == "error") were cached nowhere, so
   one chat question re-solved the same failing core through
   the router's wrapper pass, the MCQ stem forms and salvage —
   one stem was solved 8 times in a single request. Fix: a
   short-TTL failure memo in solver/answer_cache.py, wired into
   solver/router.solve_question (deterministic solver => the
   memoised error is byte-identical to re-solving).
3. The two pure normalisers (normalize_spelling's inner pass and
   normalize_hinglish) re-ran on every pipeline walk. Fix:
   functools.lru_cache on both.

These tests pin the mechanisms and the no-behaviour-change rule
on representative questions (fast solved, MCQ, unsolvable).
"""
import re
import time

import pytest

import solver  # noqa: F401  (importing the package applies Fix 1)
from api import _solve_friendly
from solver.answer_cache import (clear_cache, get_failure,
                                 put_failure)
from solver.router import (normalize_hinglish, normalize_spelling,
                           solve_question)

MCQ = "cos²27° − sin²63° = (A) −1 (B) 0 (C) 1 (D) 1/2"
UNSOLVABLE_MCQ = ("In ΔPQR if PR² = PQ² + QR² then ∠Q = "
                  "(A) 45° (B) 60° (C) 75° (D) 90°")
FAILING_CORE = "pr^2 = pq^2 + qr^2"


@pytest.fixture(autouse=True)
def _cold_caches():
    clear_cache()
    yield
    clear_cache()


def test_re_cache_ceiling_raised():
    """Fix 1 is in force once the solver package is imported."""
    assert getattr(re, "_MAXCACHE", 512) >= 32768


def test_failure_memo_roundtrip_and_selectivity():
    """Fix 2: only op == "error" dicts are memoised, and a hit
    returns an equal-but-independent copy."""
    err = {"type": "algebra", "op": "error",
           "answer": "Could not solve this one: boom", "steps": []}
    assert put_failure("some failing question", err) is True
    got = get_failure("some failing question")
    assert got == err
    got["answer"] = "mutated"
    assert get_failure("some failing question")["answer"] == \
        "Could not solve this one: boom"
    ok = {"type": "arithmetic", "op": "evaluate",
          "answer": "4", "steps": []}
    assert put_failure("2 + 2", ok) is False
    assert get_failure("2 + 2") is None


def test_failing_core_second_solve_is_memoised():
    """The same failing string solved twice: identical result,
    and the second serve comes from the memo (far faster than
    the full pipeline walk the first one paid)."""
    first = solve_question(FAILING_CORE)
    assert first.get("op") == "error"
    t0 = time.perf_counter()
    second = solve_question(FAILING_CORE)
    dt = time.perf_counter() - t0
    assert second == first
    assert dt < 0.5, f"memoised failure took {dt:.2f}s"


def test_normalisers_stable_under_memoisation():
    """Fix 3: repeated normalisation returns the known outputs
    (values pinned by the Wave 57/59/65/79 batteries)."""
    for _ in range(2):
        assert normalize_spelling("240 ka 15 parsent ktna hoga?") == \
            "240 ka 15 pratishat kitna hoga?"
        assert normalize_hinglish(
            "15 aur 27 ka jod kitna hoga") == "15 + 27"


def test_answers_unchanged_representative_set():
    """The no-behaviour-change rule on the shapes this wave
    profiled: a fast solve, an MCQ named by option, and an
    unsolvable MCQ collapsing to the one-line not-found."""
    assert _solve_friendly("What is 15% of 240?")["answer"] == "36"
    assert _solve_friendly(MCQ)["answer"] == "(B) 0"
    # Wave 94 superseded this test's premise: UNSOLVABLE_MCQ
    # (PR² = PQ² + QR² ⇒ ∠Q) is now derived by the papers10
    # converse-of-Pythagoras schema — the correct answer is
    # (D) 90°. The raw core still errors (see the failure-memo
    # tests above), so the speed behaviour this file guards is
    # unchanged.
    res = _solve_friendly(UNSOLVABLE_MCQ)
    assert res["answer"] == "(D) 90°"
