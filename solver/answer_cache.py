"""Answer cache (Kami audit 2c-1, 12 Nov 2026): repeat questions cost
no CPU on PythonAnywhere's 100 CPU-second/day free plan.

Design — deliberately small and safe:
- In-memory only, per process. Nothing is written to disk, so no
  student data ever persists beyond the running process, and a
  restart simply starts with an empty cache.
- Key: the question normalised (strip, collapse whitespace, lower).
  solve_question() is deterministic for the same raw question —
  same solver, same steps, content-hash graph filenames — so a
  cached answer is the same answer.
- Only successful answers are cached: dicts with a non-empty
  ``answer`` and ``op`` != "error". Fallback/error answers are
  never stored, so a question that failed once is always re-tried
  fresh.
- Graph safety: a cached plot answer is only served when every
  ``graphs/plot_*.png`` it names still exists on disk. The K9
  graph cleanup may delete a file the cache (but no saved chat)
  referenced — in that case the hit is treated as a miss and the
  solve re-runs, regenerating the same deterministic filename.
- Deep copies both ways: callers mutate results (session history,
  fallback), so the stored copy can never be poisoned by a caller
  and a served copy can never corrupt the store.
- Bounded LRU: at most 1000 entries; the oldest is dropped when
  full, so memory cannot grow without bound. Wave 48 measured
  real result dicts at ~1.1 KB mean / ~1.6 KB max (deep size over
  a 65-question battery sample), so 1000 entries cost ~1-2 MB —
  a whole school re-asks the same NCERT questions, and the old
  200-entry bound evicted them long before the day was out.

Negative cache (Wave 48, Wave-45 audit Part B item 3):
- The positive cache above never stores fallback outcomes, so a
  question the solver cannot answer re-paid the full solve +
  fallback-layer cost on EVERY re-ask — and students re-ask
  unsolved questions (the chat UI has a Retry button).
- A separate, short-TTL store keeps the finished fallback result
  (the dict ``fallback.with_fallback`` produced, flagged
  ``fallback: True``) for 10 minutes under the SAME normalised
  key. ``with_fallback`` is a pure function of the question text
  — no user, session or account data ever enters these results
  (personalisation is layered on by the routes, outside the
  result dict) — so, like the positive cache, entries are shared
  across users and contain nothing user-specific.
  Wave 107: the one language-shaped exception — when a
  message carried an explicit answer-language request, the
  fallback result's one-line texts are shaped by that request,
  so the two solve routes pass it as a ``variant`` and it
  becomes part of the negative key. Without it, an unsolvable
  question asked with "answer in Hindi" would pin its Hindi
  not-found line onto the next ask of the same question (with
  a different request, or none) for the whole TTL. Callers
  that pass no variant — including every no-request ask —
  keep the exact pre-Wave-107 key.
- Real solver answers are never filed here (they keep the
  positive LRU behaviour), and neither are bank-verified answers
  if a future seam flags them as fallback-shaped: a verified
  answer is a real answer, not a failure.
- Same graph safety and deep-copy rules as the positive cache;
  bounded at 500 entries, LRU-evicted. The short TTL bounds how
  long an improved solver (or a newly-set AI key) takes to be
  re-tried on a previously-failed question.
"""
import copy
import re
import time
from collections import OrderedDict
from pathlib import Path

_MAX_ENTRIES = 1000
_NEG_MAX_ENTRIES = 500
_NEG_TTL_SECONDS = 600
_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "static" / "graphs"
_GRAPH_NAME_RE = re.compile(r"graphs/(plot_[A-Za-z0-9_.\-]+\.png)")

_cache = OrderedDict()
_stats = {"hits": 0, "misses": 0}


def _cache_key(question):
    return re.sub(r"\s+", " ", str(question).strip().lower())


def _graphs_exist(result):
    """Every graph file a cached result names must still be on disk."""
    text = repr(result)
    for name in _GRAPH_NAME_RE.findall(text):
        if not (_GRAPHS_DIR / name).is_file():
            return False
    return True


def _is_cacheable(result):
    if not isinstance(result, dict):
        return False
    if result.get("op") == "error":
        return False
    answer = result.get("answer")
    if not answer or (isinstance(answer, str) and not answer.strip()):
        return False
    return _graphs_exist(result)


def get_cached(question):
    """Return a deep copy of the cached answer, or None on a miss."""
    key = _cache_key(question)
    entry = _cache.get(key)
    if entry is None:
        _stats["misses"] += 1
        return None
    if not _graphs_exist(entry):
        # A graph file was cleaned up since this was stored — drop
        # the stale entry and re-solve instead of serving a broken
        # image.
        del _cache[key]
        _stats["misses"] += 1
        return None
    _stats["hits"] += 1
    _cache.move_to_end(key)
    return copy.deepcopy(entry)


def put_cached(question, result):
    """Store a deep copy of a successful answer; silently skip
    anything that is not cacheable."""
    if not _is_cacheable(result):
        return False
    key = _cache_key(question)
    _cache[key] = copy.deepcopy(result)
    _cache.move_to_end(key)
    while len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)
    return True


def clear_cache():
    _cache.clear()
    _stats["hits"] = 0
    _stats["misses"] = 0
    clear_negative_cache()
    clear_failure_cache()


def cache_stats():
    return {"entries": len(_cache), "hits": _stats["hits"],
            "misses": _stats["misses"], "max_entries": _MAX_ENTRIES,
            "negative_entries": len(_neg_cache),
            "negative_hits": _neg_stats["hits"],
            "negative_misses": _neg_stats["misses"],
            "negative_max_entries": _NEG_MAX_ENTRIES,
            "negative_ttl_seconds": _NEG_TTL_SECONDS,
            "failure_entries": len(_fail_cache),
            "failure_hits": _fail_stats["hits"],
            "failure_misses": _fail_stats["misses"],
            "failure_max_entries": _FAIL_MAX_ENTRIES,
            "failure_ttl_seconds": _FAIL_TTL_SECONDS}


# --- Negative cache: fallback outcomes, short TTL ----------------

_neg_cache = OrderedDict()
_neg_stats = {"hits": 0, "misses": 0}


def _is_negative_worthy(result):
    """Only finished fallback outcomes are stored: dicts the
    fallback layer flagged (``fallback: True``). Real solver
    answers never carry the flag; bank-verified answers (a later
    seam may flag them fallback-shaped) are real answers wearing
    the flag, so they are refused explicitly. AI-seam answers
    (Gemini/Groq) are refused too: they are produced by a live
    external service whose availability — key set or not, quota,
    failover chain — is decided per ask by the seam itself, so
    pinning one in the failure cache would serve an AI answer in
    contexts where the seam would now fail or refuse (and vice
    versa). The deterministic honest-layer outcomes underneath
    (similar / concept / guide / salvage / science / non-maths)
    are pure functions of the question and are what this cache
    exists for."""
    if not isinstance(result, dict):
        return False
    if not result.get("fallback"):
        return False
    if result.get("verified"):
        return False
    if result.get("ai_generated"):
        return False
    if result.get("fallback_kind") in ("bank", "gemini", "groq"):
        return False
    return _graphs_exist(result)


def _neg_key(question, variant=None):
    """The negative-cache key: the normalised question, plus
    the caller's language variant when it supplies one
    (Wave 107 — see the module docstring)."""
    key = _cache_key(question)
    if variant:
        key = key + "\x1f" + str(variant)
    return key


def get_negative(question, variant=None):
    """Return a deep copy of the cached fallback outcome for
    question, or None on a miss / expired / stale-graph entry."""
    key = _neg_key(question, variant)
    entry = _neg_cache.get(key)
    if entry is None:
        _neg_stats["misses"] += 1
        return None
    stored_at, result = entry
    if time.monotonic() - stored_at > _NEG_TTL_SECONDS \
            or not _graphs_exist(result):
        # Expired, or a graph file it names was cleaned up —
        # drop the entry and let the caller re-run the solve.
        del _neg_cache[key]
        _neg_stats["misses"] += 1
        return None
    _neg_stats["hits"] += 1
    _neg_cache.move_to_end(key)
    return copy.deepcopy(result)


def put_negative(question, result, variant=None):
    """Store a deep copy of a fallback outcome for the TTL;
    silently skip anything that is not one."""
    if not _is_negative_worthy(result):
        return False
    key = _neg_key(question, variant)
    _neg_cache[key] = (time.monotonic(), copy.deepcopy(result))
    _neg_cache.move_to_end(key)
    while len(_neg_cache) > _NEG_MAX_ENTRIES:
        _neg_cache.popitem(last=False)
    return True


def clear_negative_cache():
    _neg_cache.clear()
    _neg_stats["hits"] = 0
    _neg_stats["misses"] = 0


# --- Failure memo: solver error outcomes, very short TTL -------
#
# Wave 97 (speed): the positive cache above stores successes and
# the negative cache stores finished FALLBACK outcomes, but a raw
# solver failure (op == "error") was stored NOWHERE — and one
# chat question re-solves the same failing string many times
# through its layers (the router's wrapper-core candidates, the
# MCQ stem forms, the salvage candidates and the friendly retry
# all converge on the same normalised cores). Measured on one
# unsolvable MCQ: the same stem string was solved 8 times in a
# single request, each time paying the full pipeline walk for
# the identical error dict.
#
# solve_question() is deterministic for the same raw question
# (the positive cache's own design premise), so a stored error
# dict re-served within the TTL is byte-identical to re-solving.
# The TTL is deliberately much shorter than the negative
# cache's: an error can also mean "the solve budget ran out
# under load", and that must clear quickly — 60 seconds bounds
# the stickiness while covering every within-request repeat
# (a whole chat answer is built in seconds). Same graph-safety
# and deep-copy rules as the other stores; bounded LRU.

_FAIL_MAX_ENTRIES = 500
_FAIL_TTL_SECONDS = 60

_fail_cache = OrderedDict()
_fail_stats = {"hits": 0, "misses": 0}


def _is_failure_worthy(result):
    """Only raw solver failures: dicts with op == "error".
    Successes keep the positive cache; fallback outcomes keep
    the negative cache; this store is solely for the gap
    between them."""
    if not isinstance(result, dict):
        return False
    if result.get("op") != "error":
        return False
    return _graphs_exist(result)


def get_failure(question):
    """Return a deep copy of the memoised solver failure for
    question, or None on a miss / expired entry."""
    key = _cache_key(question)
    entry = _fail_cache.get(key)
    if entry is None:
        _fail_stats["misses"] += 1
        return None
    stored_at, result = entry
    if time.monotonic() - stored_at > _FAIL_TTL_SECONDS \
            or not _graphs_exist(result):
        del _fail_cache[key]
        _fail_stats["misses"] += 1
        return None
    _fail_stats["hits"] += 1
    _fail_cache.move_to_end(key)
    return copy.deepcopy(result)


def put_failure(question, result):
    """Memoise a solver failure for the TTL; silently skip
    anything that is not one."""
    if not _is_failure_worthy(result):
        return False
    key = _cache_key(question)
    _fail_cache[key] = (time.monotonic(), copy.deepcopy(result))
    _fail_cache.move_to_end(key)
    while len(_fail_cache) > _FAIL_MAX_ENTRIES:
        _fail_cache.popitem(last=False)
    return True


def clear_failure_cache():
    _fail_cache.clear()
    _fail_stats["hits"] = 0
    _fail_stats["misses"] = 0
