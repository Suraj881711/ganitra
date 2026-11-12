"""Answer cache (Kami audit 2c-1, 12 Nov 2026): repeat questions are
served from memory at zero CPU; errors are never cached; a cached
plot whose PNG was cleaned up is re-solved, never served broken."""
import solver.answer_cache as cache
from solver.router import solve_question


def test_repeat_question_served_from_cache():
    cache.clear_cache()
    first = solve_question("2+2")
    assert first["answer"] == "4"
    assert cache.cache_stats()["misses"] == 1
    second = solve_question("  2+2  ")
    assert second == first
    assert second is not first
    assert cache.cache_stats()["hits"] == 1


def test_mutating_a_result_does_not_poison_cache():
    cache.clear_cache()
    first = solve_question("3 * 4")
    first["answer"] = "tampered"
    first["steps"] = ["tampered"]
    second = solve_question("3 * 4")
    assert second["answer"] == "12"
    assert second["steps"] != ["tampered"]


def test_error_results_are_never_cached():
    cache.clear_cache()
    assert cache.put_cached("bad", {"type": "arithmetic", "op": "error",
                                    "answer": "Could not solve", "steps": []}) is False
    assert cache.put_cached("empty", {"type": "arithmetic",
                                      "answer": "", "steps": []}) is False
    assert cache.cache_stats()["entries"] == 0
    assert cache.get_cached("bad") is None


def test_plot_answer_cached_and_graph_file_exists():
    cache.clear_cache()
    result = solve_question("plot x^2")
    assert result.get("image", "").startswith("graphs/plot_")
    again = solve_question("plot x^2")
    assert again == result
    assert cache.cache_stats()["hits"] == 1


def test_cache_evicts_oldest_when_full(monkeypatch):
    cache.clear_cache()
    monkeypatch.setattr(cache, "_MAX_ENTRIES", 2)
    cache.put_cached("q1", {"type": "arithmetic", "answer": "1", "steps": []})
    cache.put_cached("q2", {"type": "arithmetic", "answer": "2", "steps": []})
    cache.put_cached("q3", {"type": "arithmetic", "answer": "3", "steps": []})
    assert cache.get_cached("q1") is None
    assert cache.get_cached("q2")["answer"] == "2"
    assert cache.get_cached("q3")["answer"] == "3"
    assert cache.cache_stats()["entries"] == 2
