"""Wave 88: Full Paper Mode — attempt a whole stored board
paper like an exam (full_paper.py + the /papers/<id>/attempt
routes).

Pins:
- the duration rule (a paper's own stored duration when the
  data carries one, else the board-standard 3 hours), the
  duration label, and the deadline/remaining math the timer
  page is built from;
- classification honesty: assertion-reason, proof / long /
  case-study questions are self-check and are NEVER
  machine-marked; MCQs and short answers are auto-checked
  only when the solver settles them;
- real checking on a small fabricated paper through the REAL
  solver: an MCQ marked by its option letter, a short answer
  marked exactly, score math that counts only settled
  questions, a blank counted unattempted with the answer
  still shown;
- the HTTP flow with the solver stubbed at the full_paper
  seam (the real solver is covered above and by the solver's
  own suites): the Papers page carries the Attempt action,
  the intro shows count / marks / time, the attempt page
  renders every question with the Wave 60 discard-guard back
  bar, a tiny injected duration reaches the timer, submit
  grades and renders the result, and a wrong checked answer
  lands in the Mistake Notebook;
- the sign-in gate, like every papers page.
"""
import re
from pathlib import Path

import pytest

import full_paper
import papers_data
from test_mode import parse_student_number  # noqa: F401  (env check)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W88 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w88-test-pass"})
    return c


@pytest.fixture()
def anon_client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# --- duration -------------------------------------------------

def test_duration_defaults_to_board_standard_three_hours():
    paper = papers_data.get_paper("cbse-12-2024")
    assert "duration_seconds" not in paper
    assert full_paper.duration_for(paper) == 3 * 3600


def test_duration_uses_stored_duration_when_present():
    assert full_paper.duration_for({"duration_seconds": 600}) == 600
    assert full_paper.duration_for({"duration_minutes": 45}) == 2700
    assert full_paper.duration_for(
        {"time_allowed_minutes": 30}) == 1800


def test_duration_override_wins_and_must_be_positive():
    paper = papers_data.get_paper("cbse-12-2024")
    assert full_paper.duration_for(paper, override=2) == 2
    assert full_paper.duration_for(paper, override=0) == 3 * 3600
    assert full_paper.duration_for(paper, override="x") == 3 * 3600


def test_duration_label():
    assert full_paper.duration_label(10800) == "3 hours"
    assert full_paper.duration_label(3600) == "1 hour"
    assert full_paper.duration_label(2700) == "45 minutes"
    assert full_paper.duration_label(2) == "2 seconds"


def test_deadline_and_remaining_math():
    assert full_paper.attempt_deadline(1000, 90) == 1090
    assert full_paper.attempt_remaining(1000, 90, now=1000) == 90
    assert full_paper.attempt_remaining(1000, 90, now=1050) == 40
    assert full_paper.attempt_remaining(1000, 90, now=5000) == 0


# --- classification --------------------------------------------

def _q(section, marks, text, number=1):
    return {"number": number, "section": section, "marks": marks,
            "chapter": "real-numbers", "text": text}


def test_classify_kinds():
    assert full_paper.classify_question(_q(
        "A", 1, "What is the HCF of 12 and 18? "
                "(A) 3 (B) 6 (C) 9 (D) 36")) == "mcq"
    assert full_paper.classify_question(_q(
        "A", 1, "Assertion (A): 2 is a prime number. "
                "Reason (R): 2 has exactly two factors. "
                "(Assertion-Reason question)")) == "assertion_reason"
    assert full_paper.classify_question(_q(
        "D", 5, "State and prove the fundamental theorem "
                "of arithmetic.")) == "self"
    assert full_paper.classify_question(_q(
        "B", 2, "Prove that root 2 is irrational.")) == "self"
    assert full_paper.classify_question(_q(
        "C", 3, "Find the HCF of 12 and 18.")) == "auto"
    assert full_paper.classify_question(_q(
        "E", 4, "Case study: A garden is in the shape of a "
                "rectangle. (i) Find its area.")) == "self"


# --- answer comparison ------------------------------------------

def test_answers_match_exact_rules():
    assert full_paper.answers_match("6", "6")
    assert full_paper.answers_match("x = 5", "5")
    assert full_paper.answers_match("3/4", "0.75")
    assert full_paper.answers_match("Rs 680", "680")
    assert full_paper.answers_match("1/2", "50%")
    assert full_paper.answers_match("36", "36.0")
    assert not full_paper.answers_match("6", "7")
    assert not full_paper.answers_match("6", "")
    assert not full_paper.answers_match("6", "sixty")


# --- real checking on a fabricated paper (real solver) ----------

FAKE_PAPER = {
    "id": "fake-10", "class_num": 10, "board": "CBSE", "year": 2026,
    "questions": [
        _q("A", 1, "What is the HCF of 12 and 18? "
                   "(A) 3 (B) 6 (C) 9 (D) 36", number=1),
        _q("B", 2, "Find the HCF of 12 and 18.", number=2),
        _q("B", 2, "Find the LCM of 12 and 18.", number=3),
        _q("D", 5, "Prove that root 2 is irrational.", number=4),
        _q("C", 3, "Find the HCF of 24 and 36.", number=5),
    ],
}


def test_grade_attempt_real_solver_score_math():
    graded = full_paper.grade_attempt(
        FAKE_PAPER, ["B", "6", "35", "a long written proof", ""])
    rows = graded["rows"]
    assert [r["status"] for r in rows] == [
        "correct", "correct", "wrong", "self", "unattempted"]
    # The MCQ's expected names the settled option, verbatim.
    assert rows[0]["expected"] == "(B) 6"
    assert rows[2]["expected"] == "36"
    # A blank auto-checked question still shows its answer.
    assert rows[4]["expected"] == "12"
    summary = graded["summary"]
    assert summary["total_questions"] == 5
    assert summary["total_marks"] == 13
    # Only settled questions are scored: 1 + 2 of 1 + 2 + 2 + 3.
    assert summary["score_marks"] == 3
    assert summary["checked_marks"] == 8
    assert summary["counts"] == {"correct": 2, "wrong": 1,
                                 "unattempted": 1, "self": 1}


def test_grade_attempt_mcq_wrong_letter_is_wrong():
    graded = full_paper.grade_attempt(FAKE_PAPER, ["C", "", "", "", ""])
    assert graded["rows"][0]["status"] == "wrong"
    assert graded["rows"][0]["expected"] == "(B) 6"


def test_grade_attempt_budget_degrades_to_self_check():
    graded = full_paper.grade_attempt(
        FAKE_PAPER, ["B", "6", "36", "", ""], budget_seconds=-1)
    for row in graded["rows"]:
        assert row["status"] in ("self", "unattempted")
        assert not row["settled"]
    assert graded["summary"]["checked_marks"] == 0
    assert graded["summary"]["score_marks"] == 0


# --- HTTP flow (solver stubbed at the full_paper seam) ----------

@pytest.fixture()
def stub_solver(monkeypatch):
    """Deterministic stand-in for the solver at the seam
    full_paper grades through: every checkable question
    settles with the answer 6. The real solver's checking is
    proven by the module tests above; this fixture proves the
    routes, session, timer and notebook wiring."""
    def fake_solve(text):
        return {"op": "stub", "answer": "6",
                "steps": ["Stub working", "Answer: 6"]}
    monkeypatch.setattr(full_paper, "_solve_for_check", fake_solve)
    monkeypatch.setattr(full_paper, "_model_answer",
                        lambda text: None)


def test_papers_page_carries_attempt_action(client):
    body = client.get("/papers").get_data(as_text=True)
    assert 'href="/papers/cbse-12-2024/attempt"' in body


def test_attempt_pages_need_sign_in(anon_client):
    r = anon_client.get("/papers/cbse-12-2024/attempt")
    assert r.status_code == 302
    r = anon_client.post("/papers/cbse-12-2024/attempt/start")
    assert r.status_code == 302


def test_intro_shows_count_marks_and_time(client):
    body = client.get("/papers/cbse-12-2024/attempt") \
        .get_data(as_text=True)
    paper = papers_data.get_paper("cbse-12-2024")
    assert "Full Paper" in body
    assert f"{len(paper['questions'])}" in body
    assert "Time allowed" in body
    assert "3 hours" in body
    assert "self-check" in body
    assert 'action="/papers/cbse-12-2024/attempt/start"' in body


def test_start_renders_whole_paper_with_discard_guard(client):
    r = client.post("/papers/cbse-12-2024/attempt/start")
    body = r.get_data(as_text=True)
    paper = papers_data.get_paper("cbse-12-2024")
    assert r.status_code == 200
    # Every stored question gets exactly one answer field
    # (an MCQ's radios share their question's field name).
    indices = {int(n) for n in
               re.findall(r'name="answer_(\d+)"', body)}
    assert indices == set(range(len(paper["questions"])))
    # Paper order is the stored order: Q1 before Q38.
    assert body.index("Q1.") < body.index("Q38.")
    # Wave 60 discard guard: always-confirm back bar whose
    # fallback is this paper's page.
    assert 'data-fallback="/papers/cbse-12-2024"' in body
    assert "data-confirm-msg" in body
    # Timer: full duration rendered, auto-submit wired.
    assert "var total = 10800;" in body
    assert 'id="full-paper-form"' in body
    assert "form.submit()" in body
    with client.session_transaction() as sess:
        attempt = sess["full_paper_attempt"]
    assert attempt["paper_id"] == "cbse-12-2024"
    assert attempt["duration"] == 10800


def test_start_with_tiny_injected_duration(client):
    r = client.post("/papers/cbse-12-2024/attempt/start",
                    data={"duration_seconds": "2"})
    body = r.get_data(as_text=True)
    assert "var total = 2;" in body
    assert "var left = 2;" in body
    with client.session_transaction() as sess:
        assert sess["full_paper_attempt"]["duration"] == 2


def test_submit_without_start_redirects(client):
    r = client.post("/papers/cbse-10-2022-term2/attempt/submit",
                    data={})
    assert r.status_code == 302
    assert "/papers" in r.headers["Location"]


def test_submit_grades_and_records_mistakes(client, stub_solver):
    paper = papers_data.get_paper("cbse-10-2022-term2")
    client.post("/papers/cbse-10-2022-term2/attempt/start")
    answers = {f"answer_{i}": "" for i in range(len(paper["questions"]))}
    # Index 0 is an auto (OR) question: the stub settles it at
    # 6, so 7 is wrong and 6 (index 1, also auto) is correct.
    answers["answer_0"] = "7"
    answers["answer_1"] = "6"
    r = client.post("/papers/cbse-10-2022-term2/attempt/submit",
                    data=answers)
    body = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Auto-checked" in body
    # The wrong row shows the settled expected answer.
    assert "Find the sum of first 30 terms of AP" in body
    # The attempt is over: the session attempt is cleared.
    with client.session_transaction() as sess:
        assert "full_paper_attempt" not in sess
        mistakes = sess.get("mistakes") or []
    assert any("Find the sum of first 30 terms of AP"
               in m["question"] for m in mistakes)
    # ... and the notebook page renders it.
    notebook = client.get("/mistakes").get_data(as_text=True)
    assert "Find the sum of first 30 terms of AP" in notebook
