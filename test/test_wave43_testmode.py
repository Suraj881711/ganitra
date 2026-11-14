"""Wave 43: Chapter Test Mode — a timed 10-question test over the
practice_gen topics (Classes 6-10), scored exactly with fractions.

Pins: test generation (10 unique, checkable questions), the exact
checker (equivalent forms count, wrong answers don't), scoring
through the JSON endpoints (all-correct / all-wrong / mixed), the
Mistake Notebook hand-off, and /test rendering for a signed-in
student. The Board Mode chapter test (Wave 5) is a separate
feature and is untouched.
"""
import pytest

import practice_gen
import test_mode


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W43 Test Tester", "class": "9", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w43-test-pass"})
    return c


def _start(client, class_num=9, topic="algebra"):
    resp = client.post("/test/start", json={
        "class_num": class_num, "topic": topic})
    assert resp.status_code == 200
    return resp.get_json()


def _stored_items(client):
    with client.session_transaction() as sess:
        return sess["topic_test"]["items"]


# --- generation ---------------------------------------------------

def test_generate_test_ten_unique_checkable():
    for class_num in practice_gen.CLASSES:
        for topic in practice_gen.TOPICS:
            items = test_mode.generate_test(class_num, topic,
                                            seed=11)
            assert len(items) == test_mode.TEST_QUESTION_COUNT
            questions = [it["question"] for it in items]
            assert len(set(questions)) == len(questions)
            for it in items:
                # the generator's own answer always checks correct
                assert test_mode.check_test_answer(it, it["answer"])
                steps = test_mode.worked_steps(it)
                assert steps[-1] == f"Answer: {it['answer']}"


def test_generate_test_rejects_bad_inputs():
    with pytest.raises(ValueError):
        test_mode.generate_test(5, "algebra")
    with pytest.raises(ValueError):
        test_mode.generate_test(9, "trigonometry")


def test_time_limit_is_fifteen_minutes():
    assert test_mode.TEST_TIME_LIMIT == 15 * 60


def test_delivery_pins_bumped_for_new_css():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    base = (root / "templates" / "base.html").read_text(
        encoding="utf-8")
    sw = (root / "static" / "sw.js").read_text(encoding="utf-8")
    assert "v='30'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v7"' in sw


# --- the exact checker ---------------------------------------------

def test_checker_equivalent_fraction_forms():
    items = test_mode.generate_test(10, "probability", seed=3)
    item = next(it for it in items
                if it["answer_value"] not in (None, "0/1", "1/1"))
    from fractions import Fraction
    value = Fraction(item["answer_value"])
    assert test_mode.check_test_answer(item, item["answer"])
    assert test_mode.check_test_answer(item, str(float(value)))
    assert test_mode.check_test_answer(
        item, f"{value.numerator * 2}/{value.denominator * 2}")
    assert test_mode.check_test_answer(
        item, f"{float(value) * 100}%")
    assert not test_mode.check_test_answer(item, "0")
    assert not test_mode.check_test_answer(item, "")
    assert not test_mode.check_test_answer(item, "banana")


def test_checker_linear_equation_forms():
    item = None
    for seed in range(50):
        for it in test_mode.generate_test(8, "algebra", seed=seed):
            if it["kind"] == "linear_equation":
                item = it
                break
        if item:
            break
    assert item is not None
    assert test_mode.check_test_answer(item, item["answer"])
    assert test_mode.check_test_answer(item, f"x = {item['answer']}")
    assert test_mode.check_test_answer(item, item["answer"] + ".0")
    assert not test_mode.check_test_answer(
        item, str(int(item["answer"]) + 1))


def test_checker_string_answer_kinds():
    quad = expand = None
    for seed in range(200):
        for it in test_mode.generate_test(10, "algebra", seed=seed):
            if it["kind"] == "quadratic_roots":
                quad = it
            if it["kind"] == "expand_binomials":
                expand = it
        if quad and expand:
            break
    r1, r2 = quad["params"]["r1"], quad["params"]["r2"]
    assert test_mode.check_test_answer(quad, quad["answer"])
    assert test_mode.check_test_answer(quad, f"{r2}, {r1}")
    assert not test_mode.check_test_answer(quad, f"{r1}")
    assert test_mode.check_test_answer(
        expand, expand["answer"].replace("²", "^2"))
    s = expand["params"]["a"] + expand["params"]["b"]
    p = expand["params"]["a"] * expand["params"]["b"]
    assert not test_mode.check_test_answer(
        expand, f"x^2 + {s}x + {p + 1}")


# --- the HTTP flow --------------------------------------------------

def test_page_renders_for_signed_in_student(client):
    resp = client.get("/test")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Chapter Test" in html
    for topic in practice_gen.TOPICS:
        assert f'value="{topic}"' in html
    assert "/test/start" in html and "/test/submit" in html


def test_start_returns_questions_without_answers(client):
    data = _start(client)
    assert data["ok"] is True
    assert data["time_limit_seconds"] == 900
    assert len(data["questions"]) == 10
    for q in data["questions"]:
        assert set(q) == {"question"}


def test_start_rejects_bad_class_and_topic(client):
    assert client.post("/test/start", json={
        "class_num": 12, "topic": "algebra"}).status_code == 400
    assert client.post("/test/start", json={
        "class_num": 9, "topic": "trig"}).status_code == 400


def test_submit_without_start_is_400(client):
    resp = client.post("/test/submit", json={"answers": []})
    assert resp.status_code == 400


def test_scoring_all_correct(client):
    _start(client)
    items = _stored_items(client)
    resp = client.post("/test/submit", json={
        "answers": [it["answer"] for it in items],
        "time_taken": 300})
    data = resp.get_json()
    assert data["ok"] is True
    assert data["score"] == 10 and data["total"] == 10
    assert all(row["correct"] for row in data["rows"])
    for row in data["rows"]:
        assert row["steps"][-1] == f"Answer: {row['expected']}"
    with client.session_transaction() as sess:
        assert not sess.get("mistakes")


def test_scoring_all_wrong_goes_to_mistake_notebook(client):
    _start(client)
    items = _stored_items(client)
    resp = client.post("/test/submit", json={
        "answers": ["not-a-number"] * len(items),
        "time_taken": 900})
    data = resp.get_json()
    assert data["score"] == 0
    assert not any(row["correct"] for row in data["rows"])
    with client.session_transaction() as sess:
        mistakes = sess.get("mistakes") or []
    assert len(mistakes) == 10
    assert {m["question"] for m in mistakes} == {
        it["question"] for it in items}


def test_scoring_mixed(client):
    _start(client)
    items = _stored_items(client)
    answers = [it["answer"] if i % 2 == 0 else "not-a-number"
               for i, it in enumerate(items)]
    resp = client.post("/test/submit", json={
        "answers": answers, "time_taken": 123})
    data = resp.get_json()
    assert data["score"] == 5 and data["total"] == 10
    assert data["time_taken"] == 123
    assert [row["correct"] for row in data["rows"]] == [
        i % 2 == 0 for i in range(10)]
    with client.session_transaction() as sess:
        assert len(sess.get("mistakes") or []) == 5


def test_second_submit_after_finish_is_400(client):
    _start(client)
    items = _stored_items(client)
    client.post("/test/submit", json={
        "answers": [it["answer"] for it in items]})
    assert client.post("/test/submit", json={
        "answers": []}).status_code == 400
