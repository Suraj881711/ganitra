"""Wave 40: Practice Mode wired into the app.

/practice-mode serves one fresh practice_gen question at a
time (the older quiz keeps /practice). Pinned here:

- the page renders for a signed-in student and bounces
  anonymous visitors to the sign-in gate, like /papers;
- the generate endpoint returns a question for EVERY class
  6-10 whose answer the check endpoint accepts verbatim and
  rejects in a wrong form;
- the checker is Fraction-exact but form-tolerant: 0.75 is
  accepted for 3/4, a plainly wrong value is rejected;
- "one more" does not serve the same question twice in a row.
"""
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W40 Practice Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w40-practice-pass"})
    return c


@pytest.fixture()
def anon_client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "anon.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _generate(client, class_num, topic):
    r = client.post("/practice-mode/question",
                    json={"class_num": class_num, "topic": topic})
    assert r.status_code == 200
    d = r.get_json()
    assert d["ok"] is True
    assert isinstance(d["question"], str) and len(d["question"]) > 5
    assert d["class_num"] == class_num
    assert d["topic"] == topic
    return d


def _check(client, answer):
    r = client.post("/practice-mode/check", json={"answer": answer})
    assert r.status_code == 200
    return r.get_json()


# ---------------------------------------------------------------------------
# Page + auth pattern
# ---------------------------------------------------------------------------

def test_page_renders_for_signed_in_student(client):
    r = client.get("/practice-mode")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "Practice Mode" in html
    for topic in ("arithmetic", "algebra", "geometry",
                  "mensuration", "probability"):
        assert f'value="{topic}"' in html
    for n in (6, 7, 8, 9, 10):
        assert f'value="{n}"' in html
    # nav entry added next to Previous Papers in the shared menu
    assert 'href="/practice-mode"' in html


def test_anonymous_visitors_are_kept_out(anon_client):
    r = anon_client.get("/practice-mode")
    assert r.status_code == 302
    r = anon_client.post("/practice-mode/question",
                         json={"class_num": 8, "topic": "algebra"})
    assert r.status_code == 401
    assert r.get_json()["error"] == "login-required"
    r = anon_client.post("/practice-mode/check",
                         json={"answer": "3"})
    assert r.status_code == 401


def test_check_without_question_is_a_clean_error(client):
    d = client.post("/practice-mode/check",
                    json={"answer": "3"}).get_json()
    assert d["ok"] is False
    assert d["error"] == "no-question"


def test_bad_class_or_topic_rejected(client):
    r = client.post("/practice-mode/question",
                    json={"class_num": 5, "topic": "algebra"})
    assert r.status_code == 400
    r = client.post("/practice-mode/question",
                    json={"class_num": 8, "topic": "trigonometry"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Generate + check round trip, every class
# ---------------------------------------------------------------------------

def test_generate_and_check_for_every_class(client):
    for class_num in (6, 7, 8, 9, 10):
        _generate(client, class_num, "algebra")
        wrong = _check(client, "987654321")
        assert wrong["correct"] is False
        assert wrong["expected"]  # the worked answer is shown
        assert wrong["steps"]     # with working lines
        right = _check(client, wrong["expected"])
        assert right["correct"] is True, (class_num,
                                          wrong["expected"])


def test_generate_covers_every_topic(client):
    for topic in ("arithmetic", "geometry", "mensuration",
                  "probability"):
        _generate(client, 9, topic)
        wrong = _check(client, "-987654321")
        assert wrong["correct"] is False
        right = _check(client, wrong["expected"])
        assert right["correct"] is True, (topic, wrong["expected"])


def test_one_more_is_not_the_same_question(client):
    seen = [_generate(client, 10, "arithmetic")["question"]
            for _ in range(3)]
    assert not (seen[0] == seen[1] == seen[2])


# ---------------------------------------------------------------------------
# Fraction-exact, form-tolerant checking (state set directly)
# ---------------------------------------------------------------------------

def _set_item(client, **state):
    base = {"class_num": 10, "topic": "probability",
            "kind": "bag_probability",
            "question": "A bag contains 3 red balls and 1 blue "
                        "ball. One ball is drawn at random. Find "
                        "the probability that it is red.",
            "answer": "3/4", "answer_value": "3/4",
            "params": {"red": 3, "blue": 1}}
    base.update(state)
    with client.session_transaction() as sess:
        sess["pm_item"] = base


def test_fraction_and_decimal_forms_both_accepted(client):
    _set_item(client)
    assert _check(client, "3/4")["correct"] is True
    assert _check(client, "0.75")["correct"] is True
    assert _check(client, " 3 / 4 ")["correct"] is True
    assert _check(client, "6/8")["correct"] is True


def test_wrong_answers_rejected(client):
    _set_item(client)
    assert _check(client, "1/4")["correct"] is False
    assert _check(client, "0.5")["correct"] is False
    assert _check(client, "three")["correct"] is False
    assert _check(client, "")["correct"] is False


def test_integer_answers_accept_plain_ints(client):
    _set_item(client, kind="supplementary_angle",
              topic="geometry", answer="120",
              answer_value="120", params={"a": 60})
    assert _check(client, "120")["correct"] is True
    assert _check(client, "120.0")["correct"] is True
    assert _check(client, "119")["correct"] is False
    d = _check(client, "119")
    assert d["steps"] and d["expected"] == "120"


def test_quadratic_roots_accepted_in_any_order(client):
    _set_item(client, kind="quadratic_roots", topic="algebra",
              answer="x = 2 or x = 5", answer_value=None,
              params={"r1": 2, "r2": 5})
    assert _check(client, "x = 2 or x = 5")["correct"] is True
    assert _check(client, "5, 2")["correct"] is True
    assert _check(client, "2")["correct"] is False
    assert _check(client, "2 and 6")["correct"] is False


def test_expand_answer_compared_as_text(client):
    _set_item(client, kind="expand_binomials", topic="algebra",
              answer="x² + 5x + 6", answer_value=None,
              params={"a": 2, "b": 3})
    assert _check(client, "x² + 5x + 6")["correct"] is True
    assert _check(client, "x^2+5x+6")["correct"] is True
    assert _check(client, "x² + 5x + 7")["correct"] is False
