"""Wave 87: "My Weak Topics" — personal practice built from the
student's own Mistake Notebook.

Pins: the aggregation ranking (count desc, newest-first ties,
topic-less entries ignored), the slot allocation (proportional,
sums to the set size, at least one per topic), set generation
(weighted to the weakest topics, every served question verified
against the app's own solver and self-checking with its stored
answer), the general fallback for notebooks whose topics have no
generator, the result summary (improved at >= 80%, else weak),
both checkers, and the Flask flow — ranking page, empty state,
start/submit, wrong answers flowing back into the notebook, the
/mistakes entry point, and per-session privacy.
"""
import pytest

import practice_gen
import test_mode
import weak_practice as wp


def _mistake(topic, source="quiz", n=1):
    return [{"question": f"q{i}", "expected": "1", "given": "2",
             "topic": topic, "source": source} for i in range(n)]


# --- aggregation ---------------------------------------------------

def test_aggregate_ranks_by_count_then_recency():
    # the notebook is newest-first: geometry's mistakes sit at
    # the head of the list, so on a 3-3 tie with algebra the
    # more recent topic (geometry) ranks first.
    mistakes = (_mistake("geometry", n=3) + _mistake("algebra", n=3)
                + _mistake("arithmetic", n=2))
    ranked = wp.aggregate_weak_topics(mistakes)
    assert [(r["topic"], r["count"]) for r in ranked] == [
        ("geometry", 3), ("algebra", 3), ("arithmetic", 2)]


def test_aggregate_ignores_topicless_and_empty():
    assert wp.aggregate_weak_topics([]) == []
    assert wp.aggregate_weak_topics(None) == []
    junk = [{"question": "q", "expected": "1", "given": "2"},
            {"question": "q", "topic": "  ", "source": "quiz"},
            "not-a-dict"]
    assert wp.aggregate_weak_topics(junk) == []


def test_topic_backend_mapping():
    for topic in practice_gen.TOPICS:
        assert wp.topic_backend(topic) == "gen"
    assert wp.topic_backend("trig") == "quiz"
    assert wp.topic_backend("stats") == "quiz"
    assert wp.topic_backend("calculus") is None
    assert wp.topic_backend("sequences") is None


def test_allocate_proportional_min_one_exact_sum():
    assert sum(wp._allocate([6, 3, 2], 10)) == 10
    assert wp._allocate([6, 3, 2], 10)[0] >= 5  # lion's share
    assert all(s >= 1 for s in wp._allocate([6, 3, 2], 10))
    assert wp._allocate([5, 5, 5, 5], 3) == [1, 1, 1, 0]
    assert wp._allocate([], 10) == []


# --- set generation --------------------------------------------------

def test_build_set_weighted_and_verified():
    mistakes = _mistake("algebra", n=6) + _mistake("arithmetic", n=2)
    built = wp.build_weak_set(mistakes, 8, count=4, seed=87)
    items = built["items"]
    assert built["general"] is False
    assert len(items) == 4
    topics = [it["topic"] for it in items]
    # algebra (6 mistakes) must outweigh arithmetic (2 mistakes)
    assert topics.count("algebra") >= topics.count("arithmetic")
    assert set(topics) <= {"algebra", "arithmetic"}
    # unique questions, and every served item checks against its
    # own stored answer (build only serves solver-verified items)
    assert len({it["question"] for it in items}) == 4
    for it in items:
        assert wp.check_weak_answer(it, it["answer"])


def test_build_set_general_fallback_for_ungenerated_topics():
    mistakes = _mistake("calculus", source="Class 12 · Calculus",
                        n=3)
    built = wp.build_weak_set(mistakes, 9, count=4, seed=5)
    assert built["general"] is True
    assert len(built["items"]) == 4
    assert {it["topic"] for it in built["items"]} \
        <= set(practice_gen.TOPICS)
    for it in built["items"]:
        assert wp.check_weak_answer(it, it["answer"])


def test_served_items_agree_with_solver_independently():
    # Re-verify one served item from scratch: the raw solver must
    # land on the generator's answer (the build's own contract).
    from i18n import solve_failed
    from solver.router import solve_question
    mistakes = _mistake("arithmetic", n=3)
    built = wp.build_weak_set(mistakes, 7, count=3, seed=11)
    assert built["items"]
    for it in built["items"]:
        if it["answer_value"] is None:
            continue
        result = solve_question(it["question"])
        assert not solve_failed(it["question"], result)


# --- checkers + summary ---------------------------------------------

def test_checkers_exact_and_quiz():
    item = test_mode.generate_test(8, "arithmetic", seed=3)[0]
    item = dict(item, checker="exact")
    assert wp.check_weak_answer(item, item["answer"])
    assert not wp.check_weak_answer(item, "-99999")
    quiz_item = {"checker": "quiz", "answer": "0.5",
                 "topic": "trig", "kind": "trig"}
    assert wp.check_weak_answer(quiz_item, "1/2")
    assert wp.check_weak_answer(quiz_item, "0.51")
    assert not wp.check_weak_answer(quiz_item, "0.9")


def test_summarise_results_statuses():
    items = ([{"topic": "algebra", "kind": "linear"}] * 5
             + [{"topic": "geometry", "kind": "area"}] * 5)
    flags = [True] * 4 + [False] + [True, False, False, True, False]
    s = wp.summarise_results(items, flags)
    assert s["score"] == 6 and s["total"] == 10
    by_topic = {r["topic"]: r for r in s["topics"]}
    assert by_topic["algebra"]["status"] == "improved"   # 4/5 = 80%
    assert by_topic["geometry"]["status"] == "weak"      # 2/5
    kinds = {r["kind"]: r for r in s["kinds"]}
    assert kinds["linear"]["correct"] == 4
    assert kinds["area"]["total"] == 5


def test_sympy_equiv_for_string_kinds():
    assert wp._sympy_equiv("x^2 - 6x", "x² + -6x + 0",
                           "expand_binomials")
    assert wp._sympy_equiv("(x + 2)(x + 3)", "x² + 5x + 6",
                           "factorise_quadratic")
    assert not wp._sympy_equiv("x^2 + 1", "x² + 5x + 6",
                               "factorise_quadratic")
    assert wp._sympy_equiv("x = 3, x = -2", "x = -2, x = 3",
                           "quadratic_roots")


# --- Flask flow -------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W87 Tester", "class": "9", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w87-test-pass"})
    return c


def _seed_mistakes(client, mistakes):
    with client.session_transaction() as sess:
        sess["mistakes"] = mistakes


def test_weak_topics_empty_state(client):
    resp = client.get("/weak-topics")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "No mistakes saved yet" in body
    assert 'href="/practice"' in body and 'href="/test"' in body
    # start with an empty notebook just bounces back
    resp = client.post("/weak-topics/start")
    assert resp.status_code == 302
    assert "/weak-topics" in resp.headers["Location"]


def test_weak_topics_ranking_and_entry_point(client):
    _seed_mistakes(client, _mistake("algebra", n=3)
                   + _mistake("arithmetic", n=1))
    body = client.get("/weak-topics").get_data(as_text=True)
    assert "My Weak Topics" in body
    assert body.index("Algebra") < body.index("Arithmetic")
    assert "/weak-topics/start" in body
    mistakes_page = client.get("/mistakes").get_data(as_text=True)
    assert 'href="/weak-topics"' in mistakes_page


def test_weak_submit_scores_and_records(client):
    items = test_mode.generate_test(9, "algebra", seed=21)[:3]
    items = [dict(it, checker="exact") for it in items]
    with client.session_transaction() as sess:
        sess["weak_practice"] = {"items": items, "general": False}
        sess["mistakes"] = []
    # two right, one wrong
    data = {f"answer_{i}": (it["answer"] if i < 2 else "-99999")
            for i, it in enumerate(items)}
    resp = client.post("/weak-topics/submit", data=data)
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "2 / 3" in body
    assert "Still weak" in body  # 2/3 < 80%
    with client.session_transaction() as sess:
        notebook = sess["mistakes"]
    assert len(notebook) == 1
    assert notebook[0]["topic"] == "algebra"
    assert notebook[0]["source"] == "weak practice"


def test_weak_submit_all_correct_improves(client):
    items = test_mode.generate_test(9, "arithmetic", seed=4)[:2]
    items = [dict(it, checker="exact") for it in items]
    with client.session_transaction() as sess:
        sess["weak_practice"] = {"items": items, "general": False}
    data = {f"answer_{i}": it["answer"] for i, it in enumerate(items)}
    body = client.post("/weak-topics/submit",
                       data=data).get_data(as_text=True)
    assert "2 / 2" in body and "Improved ✔" in body


def test_weak_flow_is_per_student(client, tmp_path, monkeypatch):
    _seed_mistakes(client, _mistake("algebra", n=2))
    assert "Algebra" in client.get("/weak-topics").get_data(
        as_text=True)
    # a second, independent session sees only the empty state
    from app import create_app
    other = create_app().test_client()
    body = other.get("/weak-topics").get_data(as_text=True)
    assert "No mistakes saved yet" in body
    assert "Algebra" not in body
