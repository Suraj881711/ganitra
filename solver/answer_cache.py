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
- Bounded LRU: at most 200 entries; the oldest is dropped when
  full, so memory cannot grow without bound.
"""
import copy
import re
from collections import OrderedDict
from pathlib import Path

_MAX_ENTRIES = 200
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


def cache_stats():
    return {"entries": len(_cache), "hits": _stats["hits"],
            "misses": _stats["misses"], "max_entries": _MAX_ENTRIES}
