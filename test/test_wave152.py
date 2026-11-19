"""Wave 152: exam papers for ALL classes (Suraj's order, 18 Nov
2026 — "sabhi class ke hi exam paper chahiye").

The library was Classes 10/12 only (68 papers / 2,364 questions).
This wave adds the first official papers for the five classes
that had ZERO — 6, 7, 8, 9 and 11 — from official sources only
(JCERT/JAC model papers; Samagra Shiksha Kerala evaluation
papers), typed in full in the Wave 63 format.

Pins:
- every class 6-12 now has at least one paper, and the new
  classes carry exactly the counts this wave added;
- each new paper's identity (class, board, year, source URL),
  stored question count and stored marks;
- the omissions are real: questions that could not be read
  faithfully from the official copy (illegible options,
  figure-only data, one non-maths GK question) are absent, and
  the stored numbering keeps the printed gaps;
- structure honesty, as everywhere in the library: sections
  within A-E and within the paper's own section_titles, sorted
  unique question numbers, no external link anywhere in any
  paper's question text in the whole library;
- the new papers render on their paper page and print view;
- exam mode: a sample of MCQs from each new MCQ paper, answered
  with the paper's own printed key letter, is never marked wrong
  (the solver either settles it correct or it honestly falls to
  self-check), and whole-paper grading runs over every new
  paper.
"""
import pytest

import full_paper
import papers_data

# id -> (class_num, board, year, stored questions, stored marks,
#        header max marks, source url)
NEW_PAPERS = {
    "jac-9-2024-model": (
        9, "Jharkhand Academic Council (JAC)", 2024, 35, 35, 40,
        "https://docs.aglasem.com/view/"
        "4ea4f770-c805-11ee-922b-0a5e36bc6706"),
    "jac-8-2025-model": (
        8, "Jharkhand Academic Council (JAC)", 2025, 43, 43, 50,
        "https://docs.aglasem.com/view/"
        "6e347e9c-fbff-11ef-a4b3-0a5e36bc6706"),
    "jac-11-2024-model": (
        11, "Jharkhand Academic Council (JAC)", 2024, 40, 40, 40,
        "https://docs.aglasem.com/view/"
        "5b5b86aa-c805-11ee-8d6b-0a5e36bc6706"),
    "kerala-7-2025-second-term": (
        7, "Kerala Board (Pareeksha Bhavan)", 2025, 8, 40, 30,
        "https://docs.aglasem.com/view/"
        "b50cc17c-07d4-11f0-90a1-0a5e36bc6706"),
    "kerala-6-2025-annual": (
        6, "Kerala Board (Pareeksha Bhavan)", 2025, 7, 35, 30,
        "https://docs.aglasem.com/view/"
        "6d01fd6e-ec96-11f0-bff6-0a5e36bc6706"),
}

# Printed questions deliberately NOT stored (illegible options,
# figure-only data, or not mathematics) — see each entry's note.
OMITTED = {
    "jac-9-2024-model": {2, 16, 17, 18, 28},
    "jac-8-2025-model": {1, 2, 32, 41, 45, 47, 49},
    "kerala-6-2025-annual": {5},
}

# A spot sample per MCQ paper: question number -> the option
# letter the paper's own printed key gives (cross-check only;
# no key is stored anywhere in the app — Wave 88).
KEY_SAMPLE = {
    "jac-9-2024-model": {3: "d", 4: "c", 6: "b", 36: "c", 40: "c"},
    "jac-8-2025-model": {3: "a", 6: "d", 19: "a", 30: "d",
                         48: "c"},
    "jac-11-2024-model": {16: "c", 24: "a", 34: "b", 37: "b",
                          39: "a"},
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W152 Test Tester", "class": "9", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w152-test-pass"})
    return c


# --- coverage ---------------------------------------------------

def test_every_class_6_to_12_now_has_a_paper():
    assert papers_data.CLASSES_WITH_PAPERS == [6, 7, 8, 9, 10, 11, 12]
    counts = {}
    for p in papers_data.PAPERS:
        counts[p["class_num"]] = counts.get(p["class_num"], 0) + 1
    # The classes this wave serves, exactly as added:
    assert counts[6] == 1
    assert counts[7] == 1
    assert counts[8] == 1
    assert counts[9] == 1
    assert counts[11] == 1
    # The pre-existing bulk is untouched (Wave 179 grew
    # Classes 10 and 12 only: +12 and +17 papers):
    assert counts[10] == 51
    assert counts[12] == 46


def test_library_totals_after_wave152():
    # Wave 179: 102 papers / 3,408 questions.
    assert len(papers_data.PAPERS) == 102
    assert sum(len(p["questions"])
               for p in papers_data.PAPERS) == 3408


# --- the new papers ----------------------------------------------

@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_identity_counts_and_source(pid):
    class_num, board, year, count, marks, max_marks, url = \
        NEW_PAPERS[pid]
    p = papers_data.get_paper(pid)
    assert p is not None
    assert p["class_num"] == class_num
    assert p["board"] == board
    assert p["year"] == year
    assert len(p["questions"]) == count
    assert papers_data.paper_total_marks(p) == marks
    assert p["max_marks"] == max_marks
    assert p["source_url"] == url
    assert "AglaSem" in p["source_name"]


@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_structure(pid):
    p = papers_data.get_paper(pid)
    titles = p.get("section_titles") or {}
    numbers = [q["number"] for q in p["questions"]]
    assert numbers == sorted(numbers)
    assert len(set(numbers)) == len(numbers)
    for q in p["questions"]:
        assert q["section"] in set("ABCDE")
        if titles:
            assert q["section"] in titles
        assert q["marks"] > 0
        assert q["text"].strip()
        assert q["chapter"]


@pytest.mark.parametrize("pid", sorted(OMITTED))
def test_omitted_questions_are_absent_and_numbering_keeps_gaps(pid):
    p = papers_data.get_paper(pid)
    numbers = {q["number"] for q in p["questions"]}
    assert not (numbers & OMITTED[pid])
    full = set(range(1, (p.get("full_count") or {}).get("A", 0) + 1))
    if full:
        assert numbers == full - OMITTED[pid]


def test_no_external_links_anywhere_in_library_question_texts():
    for p in papers_data.PAPERS:
        for q in p["questions"]:
            assert "http" not in q["text"]
            assert "www." not in q["text"]


@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_full_count_overrides_match_the_printed_paper(pid):
    p = papers_data.get_paper(pid)
    assert sum((p.get("full_count") or {}).values()) == \
        p["max_questions"]
    assert sum((p.get("full_marks") or {}).values()) >= \
        papers_data.paper_total_marks(p)


# --- rendering ----------------------------------------------------

# The paper views split a question's sub-parts onto separate
# rendered lines, so the raw first-40-chars check needs a
# fragment that stays on one line for this paper.
FRAGMENT_OVERRIDE = {
    "kerala-7-2025-second-term":
        "In the table below, the height, width and their ratio",
}


@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_renders_on_paper_page_and_print_view(client, pid):
    p = papers_data.get_paper(pid)
    fragment = FRAGMENT_OVERRIDE.get(
        pid, p["questions"][0]["text"][:40])
    body = client.get("/papers/" + pid).get_data(as_text=True)
    assert p["board"] in body
    assert fragment in body
    printed = client.get("/papers/print?paper=" + pid)
    assert printed.status_code == 200
    pbody = printed.get_data(as_text=True)
    assert fragment in pbody
    # Wave 63: the stored source link never leaks into a view.
    assert p["source_url"] not in body
    assert p["source_url"] not in pbody


# --- exam mode ------------------------------------------------------

@pytest.mark.parametrize("pid", sorted(KEY_SAMPLE))
def test_exam_mode_spot_check_against_the_printed_key(pid):
    paper = papers_data.get_paper(pid)
    by_number = {q["number"]: q for q in paper["questions"]}
    settled_correct = 0
    for number, letter in KEY_SAMPLE[pid].items():
        row = full_paper.check_question(
            paper, by_number[number], letter)
        # A known-correct answer is never marked wrong: the
        # solver settles it correct, or the question honestly
        # stays self-check (Wave 88).
        assert row["status"] in ("correct", "self"), (pid, number, row)
        if row["status"] == "correct":
            settled_correct += 1
    # The solver genuinely settles at least part of each sample —
    # exam mode is solver-checked, not all self-check.
    assert settled_correct >= 1


@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_exam_mode_grades_the_whole_new_paper(pid):
    paper = papers_data.get_paper(pid)
    result = full_paper.grade_attempt(
        paper, [""] * len(paper["questions"]))
    assert len(result["rows"]) == len(paper["questions"])
    assert all(r["status"] == "unattempted" for r in result["rows"])
    view = full_paper.attempt_view(
        paper,
        lambda text, or_word="OR", lower_options=False: [text],
        lambda text: False)
    assert view["sections"]
