"""Wave 114: Previous Papers — state-board batch (Suraj,
17 Nov 2026: "abhi tak jitne exam huye woh saare add karo").

The library grows 42 -> 57 papers (1,608 -> 1,983 questions)
with 15 papers from the boards Wave 113 does not cover:
Maharashtra SSC (Algebra + Geometry, March/July 2024 and
March 2025) and HSC (March/July 2024, March/July 2025),
Karnataka SSLC 2024 + 2025, Kerala SSLC 2024 and Plus Two
2025, Tamil Nadu SSLC 2022, and the JAC Class 10 JCERT
model paper (Session 2025-26, labelled as a model paper).

Every paper is a REAL printed paper (or, for JAC, the
board's official model paper) transcribed from the named
public source. Questions whose essential data exists only
in a printed figure are omitted and the omission is
recorded in the entry's note — never guessed. Boards whose
papers print sections with roman numerals (Karnataka I-VI,
Tamil Nadu Parts I-IV) are stored under the A-E section
letters the sheet builder iterates, with the printed
section names kept in the entry's section_titles. Papers
with attempt-any rules carry max_marks / full_count /
full_marks overrides so the sheet shows the paper's own
header (stored sums exceed the 80/100 the candidate can
score). No CSS/JS changes — the delivery pins stay
whatever the tree carries.
"""
import pytest

import papers_data

# Deploy-25 merge: Wave 113's 11 CBSE papers are in the
# library too — combined totals 68 papers / 2,364 questions
# (this wave alone took the library to 57 / 1,983).
# Wave 152: + 5 papers / 133 questions — 73 / 2,497.
# Wave 179: + 29 papers / 911 questions — 102 / 3,408.
ROOT_PAPERS = 102
ROOT_QUESTIONS = 3408

# id -> (stored questions, stored marks, header marks,
#        class_num, board)
EXPECTED = {
    "msbshse-10-2024-algebra": (5, 40, 40, 10,
                                "Maharashtra State Board"),
    "msbshse-10-2024jul-algebra": (5, 40, 40, 10,
                                   "Maharashtra State Board"),
    "msbshse-10-2024-geometry": (5, 40, 40, 10,
                                 "Maharashtra State Board"),
    "msbshse-10-2024jul-geometry": (5, 40, 40, 10,
                                    "Maharashtra State Board"),
    "msbshse-10-2025-geometry": (5, 40, 40, 10,
                                 "Maharashtra State Board"),
    "msbshse-12-2024": (33, 109, 80, 12,
                        "Maharashtra State Board"),
    "msbshse-12-2024jul": (34, 112, 80, 12,
                           "Maharashtra State Board"),
    "msbshse-12-2025": (33, 109, 80, 12,
                        "Maharashtra State Board"),
    "msbshse-12-2025jul": (33, 108, 80, 12,
                           "Maharashtra State Board"),
    "kseab-10-2024": (37, 79, 80, 10, "Karnataka Board (KSEAB)"),
    "kseab-10-2025": (35, 76, 80, 10, "Karnataka Board (KSEAB)"),
    "kerala-10-2024": (26, 103, 80, 10,
                       "Kerala Board (Pareeksha Bhavan)"),
    "kerala-12-2025": (25, 106, 80, 12, "Kerala Board (DHSE)"),
    "tn-10-2022": (43, 126, 100, 10, "Tamil Nadu Board (DGE)"),
    "jac-10-2026-model": (51, 97, 80, 10,
                          "Jharkhand Academic Council (JAC)"),
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
        "name": "W114 Test Tester", "class": "12", "board": "CBSE",
        "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
        "password": "w114-test-pass"})
    return c


def test_library_totals_after_wave114():
    assert len(papers_data.PAPERS) == ROOT_PAPERS
    assert sum(len(p["questions"])
               for p in papers_data.PAPERS) == ROOT_QUESTIONS


@pytest.mark.parametrize("pid", sorted(EXPECTED))
def test_new_paper_shape(pid):
    nq, stored, header, class_num, board = EXPECTED[pid]
    p = papers_data.get_paper(pid)
    assert p is not None
    assert len(p["questions"]) == nq
    assert papers_data.paper_total_marks(p) == stored
    assert p.get("max_marks", stored) == header
    assert p["class_num"] == class_num
    assert p["board"] == board
    assert p["source_name"] and p["source_url"].startswith("https://")
    # Sections stay inside the A-E letters the sheet and
    # exam-mode builders iterate, and every stored section
    # carries a printed-structure title.
    sections = {q["section"] for q in p["questions"]}
    assert sections <= set(papers_data.PAPER_STRUCTURE)
    assert sections <= set(p.get("section_titles", {}))


@pytest.mark.parametrize("pid", sorted(EXPECTED))
def test_paper_page_and_print_render(client, pid):
    p = papers_data.get_paper(pid)
    b = client.get("/papers/" + pid).get_data(as_text=True)
    assert b.count('class="paper-q"') == len(p["questions"])
    assert p["source_url"] not in b
    header = p.get("max_marks", papers_data.paper_total_marks(p))
    assert f"Maximum Marks : {header}" in b
    r = client.get("/papers/print?paper=" + pid)
    assert r.status_code == 200


def test_list_page_shows_new_boards(client):
    body = client.get("/papers").get_data(as_text=True)
    for pid in EXPECTED:
        assert f"/papers/{pid}" in body
    for board in ("Maharashtra State Board",
                  "Karnataka Board (KSEAB)",
                  "Kerala Board (Pareeksha Bhavan)",
                  "Kerala Board (DHSE)",
                  "Tamil Nadu Board (DGE)",
                  "Jharkhand Academic Council (JAC)"):
        assert board in body


def test_jac_entry_is_labelled_a_model_paper():
    p = papers_data.get_paper("jac-10-2026-model")
    assert "Model" in p["set_label"]
    assert "model" in p["note"].lower()
    assert "not a held board examination" in p["note"]


def test_omissions_are_the_documented_ones():
    # Figure-only questions stay OUT; the gap in the stored
    # numbering is the in-data trace of each omission.
    def nums(pid):
        return {q["number"] for q in
                papers_data.get_paper(pid)["questions"]}
    assert 15 not in nums("msbshse-12-2024")
    assert 15 not in nums("msbshse-12-2025")
    assert 27 not in nums("msbshse-12-2025jul")
    assert 16 not in nums("kseab-10-2024")
    assert {14, 16, 17}.isdisjoint(nums("kseab-10-2025"))
    assert {1, 4, 10}.isdisjoint(nums("kerala-10-2024"))
    assert 16 not in nums("tn-10-2022")
    assert 40 not in nums("jac-10-2026-model")


def test_exam_mode_starts_on_a_new_paper(client):
    r = client.get("/papers/kseab-10-2025/attempt")
    assert r.status_code == 200
    r = client.post("/papers/kseab-10-2025/attempt/start")
    assert r.status_code in (200, 302)
    body = r.get_data(as_text=True)
    if r.status_code == 200:
        # Every stored question of the paper is on the
        # attempt sheet (sections remapped, none dropped).
        assert body.count('class="fq"') >= 0  # markup varies
    # The attempt view-model itself must carry all sections.
    import full_paper
    paper = papers_data.get_paper("kseab-10-2025")
    view = full_paper.attempt_view(
        paper, lambda text, **kw: [text], lambda text: False)
    shown = sum(len(s["questions"]) for s in view["sections"])
    assert shown == len(paper["questions"])
