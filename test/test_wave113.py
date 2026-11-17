"""Wave 113: MORE EXAM PAPERS — 11 new CBSE papers in the library.

Suraj's order (17 Nov 2026): "exam paper badao" / "abhi tak jitne exam
huye woh saare add karo" — grow the in-app paper library continuously.
Wave 113 is the first batch of the all-papers programme for the CBSE +
north-board side: CBSE Class 10 and 12 board papers 2017-2020, the
2021-22 Term 1 papers, and the official 2025-26 sample papers.

Every paper was transcribed from a real source actually read (see the
per-paper source_name/source_url and ganitra-wave113-notes.md); a paper
that could not be read fully was not added, and omissions inside a
paper are recorded in that entry's "note".

These tests pin the new paper ids, the library totals, and each new
paper's question count and stored marks.
"""
import papers_data

NEW_PAPERS = {
    # id: (class_num, year, question_count, stored_marks_sum)
    "cbse-10-2017": (10, 2017, 31, 90),
    "cbse-10-2018": (10, 2018, 30, 80),
    "cbse-10-2019": (10, 2019, 30, 80),
    "cbse-10-2022-term1-basic": (10, 2022, 46, 46),
    "cbse-10-sample-2026": (10, 2026, 38, 80),
    "cbse-12-2017": (12, 2017, 29, 100),
    "cbse-12-2018": (12, 2018, 29, 100),
    "cbse-12-2019": (12, 2019, 29, 100),
    "cbse-12-2020": (12, 2020, 36, 80),
    "cbse-12-2022-term1": (12, 2022, 48, 48),
    "cbse-12-sample-2026": (12, 2026, 35, 69),
}


def test_library_totals():
    # Deploy-25 merge: Wave 114's 15 state-board papers are
    # in the library too — combined totals 68 / 2,364 (this
    # wave alone took the library to 53 / 1,989).
    assert len(papers_data.PAPERS) == 68
    total = sum(len(p["questions"]) for p in papers_data.PAPERS)
    assert total == 2364


def test_new_papers_present_with_counts():
    for pid, (class_num, year, count, marks) in NEW_PAPERS.items():
        paper = papers_data.get_paper(pid)
        assert paper is not None, pid
        assert paper["board"] == "CBSE"
        assert paper["class_num"] == class_num
        assert paper["year"] == year
        assert len(paper["questions"]) == count, pid
        assert papers_data.paper_total_marks(paper) == marks, pid
        assert paper["source_url"].startswith("http"), pid


def test_new_paper_question_shape():
    for pid in NEW_PAPERS:
        paper = papers_data.get_paper(pid)
        numbers = [q["number"] for q in paper["questions"]]
        assert numbers == sorted(numbers), pid
        for q in paper["questions"]:
            assert q["section"] in ("A", "B", "C", "D", "E"), (pid, q)
            assert q["marks"] >= 1
            assert q["text"].strip(), (pid, q["number"])
            assert q["chapter"], (pid, q["number"])


def test_term1_papers_carry_attempt_any_note():
    # The Term 1 papers print 46/48 one-mark questions against a
    # 40-mark maximum (attempt-any pattern); the entry must say so.
    for pid in ("cbse-10-2022-term1-basic", "cbse-12-2022-term1"):
        paper = papers_data.get_paper(pid)
        assert paper["max_marks"] == 40
        assert "any 40" in paper["note"] or "any 16" in str(
            paper.get("section_titles"))


def test_sample12_omissions_are_noted():
    paper = papers_data.get_paper("cbse-12-sample-2026")
    assert "Q5" in paper["note"] and "Q34" in paper["note"]
    assert "Q35" in paper["note"]
    numbers = {q["number"] for q in paper["questions"]}
    assert 5 not in numbers and 34 not in numbers and 35 not in numbers


def test_papers_for_class_lists_new_papers():
    ids10 = {p["id"] for p in papers_data.papers_for_class(10)}
    ids12 = {p["id"] for p in papers_data.papers_for_class(12)}
    for pid, (class_num, *_rest) in NEW_PAPERS.items():
        assert pid in (ids10 if class_num == 10 else ids12), pid
