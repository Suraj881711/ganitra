"""Wave 66: Previous Papers — ALL boards, Hindi + English
(Suraj, 15 Nov 2026: "All paper sabhi board ke chahiye,
hindi or english dono ke").

The library grows 17 → 39 papers (567 → 1,486 questions)
across 9 boards. Every new paper is a REAL printed board
paper transcribed question-by-question from its full text
and cross-checked (second source or the bilingual other
half); nothing is invented and nothing is machine
translated — each Hindi entry is the printed Hindi text of
its booklet. Papers whose sections are alternatives or
whose printed attempt-rule differs from the stored sum
carry max_marks / section-title overrides so the sheet
shows the paper's own header (BSEB 100 not 200; ISC/ICSE
80). The English hbse-12-2024 entry's Q11/Q23/Q30 were
corrected against the printed pages. No CSS/JS changes —
the delivery pins stay whatever the tree carries. Gaps
(GSEB/UBSE located but
not transcribed, CGBSE/JAC not reached, CISCE has no Hindi
Maths) are documented in ganitra-wave66-notes.md.
"""
import html as _html
import re
from pathlib import Path

import pytest

import papers_data

ROOT = Path(__file__).resolve().parent.parent

# id -> (questions, stored marks, header marks)
EXPECTED = {
    "rbse-10-2025": (20, 80, 80), "rbse-10-2025-hindi": (20, 80, 80),
    "rbse-12-2025": (20, 80, 80), "rbse-12-2025-hindi": (20, 80, 80),
    "cbse-12-2022-term2-hindi": (14, 40, 40),
    "isc-12-2025": (22, 95, 80), "icse-10-2025": (10, 110, 80),
    "up-10-2025": (25, 70, 70), "up-10-2025-hindi": (25, 70, 70),
    "up-12-2025": (9, 100, 100), "up-12-2025-hindi": (9, 100, 100),
    "hbse-10-2024-hindi": (38, 80, 80),
    "hbse-12-2024-hindi": (38, 80, 80),
    "mpbse-10-2025": (23, 75, 75), "mpbse-10-2025-hindi": (23, 75, 75),
    "mpbse-12-2025": (23, 80, 80), "mpbse-12-2025-hindi": (23, 80, 80),
    "bseb-10-2025": (138, 200, 100),
    "bseb-10-2025-hindi": (138, 200, 100),
    "bseb-12-2025": (138, 200, 100),
    "bseb-12-2025-hindi": (138, 200, 100),
    "msbshse-10-2025-algebra": (5, 40, 40),
}
DEV = re.compile(r"[ऀ-ॿ]")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W66 Test Tester", "class": "12", "board": "RBSE",
        "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
        "password": "w66-test-pass"})
    return c


def test_library_totals():
    assert len(papers_data.PAPERS) == 39
    assert sum(len(p["questions"])
               for p in papers_data.PAPERS) == 1486
    assert sum(1 for p in papers_data.PAPERS
               if p.get("medium") == "hindi") == 15


@pytest.mark.parametrize("pid", sorted(EXPECTED))
def test_new_paper_shape(pid):
    nq, stored, header = EXPECTED[pid]
    p = papers_data.get_paper(pid)
    assert p is not None
    assert len(p["questions"]) == nq
    assert papers_data.paper_total_marks(p) == stored
    assert p.get("max_marks", stored) == header
    assert p["source_name"] and p["source_url"].startswith("https://")


@pytest.mark.parametrize("pid", [k for k in EXPECTED
                                 if k.endswith("hindi")])
def test_hindi_papers_carry_genuine_hindi(pid):
    p = papers_data.get_paper(pid)
    verbal = [q for q in p["questions"] if len(q["text"]) > 40]
    hindi_qs = [q for q in verbal
                if len(DEV.findall(q["text"])) >= 3]
    # BSEB-12 Hindi is the floor (74/127): most of its 100
    # objective questions are pure expressions printed once
    # for both mediums in the booklet itself.
    assert len(hindi_qs) >= 0.5 * len(verbal)
    assert sum(len(DEV.findall(q["text"]))
               for q in p["questions"]) >= 150


def test_hbse12_english_corrections():
    qmap = {q["number"]: q["text"] for q in
            papers_data.get_paper("hbse-12-2024")["questions"]}
    assert "[1 + (dy/dx)²]²" in qmap[11]
    assert "√((1 - cos x)/(1 + cos x))" in qmap[23]
    assert "π/4 < x < π/4" in qmap[23]
    assert "√tan x" in qmap[30]


def test_list_labels_boards_and_mediums(client):
    body = client.get("/papers").get_data(as_text=True)
    assert body.count("हिंदी माध्यम · Hindi Medium</span>") == 15
    assert body.count("English Medium</span>") == 24
    for p in papers_data.PAPERS:
        assert p["board"] in body
        assert p["source_url"] not in body


@pytest.mark.parametrize("pid", sorted(EXPECTED))
def test_paper_page_and_print_render(client, pid):
    p = papers_data.get_paper(pid)
    b = client.get("/papers/" + pid).get_data(as_text=True)
    assert b.count('class="paper-q"') == len(p["questions"])
    assert p["source_url"] not in b
    r = client.get("/papers/print?paper=" + pid)
    assert r.status_code == 200


def test_header_mark_overrides_render(client):
    b = client.get("/papers/bseb-10-2025").get_data(as_text=True)
    assert "Maximum Marks : 100" in b
    assert "Maximum Marks : 200" not in b
    b = client.get("/papers/isc-12-2025").get_data(as_text=True)
    assert "Maximum Marks : 80" in b
    b = client.get("/papers/icse-10-2025").get_data(as_text=True)
    assert "Maximum Marks : 80" in b


def test_rbse_section_c_not_inflated(client):
    # RBSE Section C holds 4 questions of 3 marks; the
    # builder's CBSE-standard inflation would claim 6 / 86 —
    # the entries carry full_count/full_marks overrides.
    b = client.get("/papers/rbse-10-2025").get_data(as_text=True)
    assert "Maximum Marks : 80" in b
    assert "Section C contains 4 questions of 3 marks each." in b


def test_up12_single_section_render(client):
    b = client.get("/papers/up-12-2025").get_data(as_text=True)
    assert "Complete Paper" in b
    assert b.count('class="paper-q"') == 9


def test_pins_unchanged():
    # Wave 66 changes no CSS/JS and moves no delivery pin:
    # the pins stay whatever the tree carries (?v=36 / v13 in
    # the Wave-66 copy; ?v=37 / v14 in the original tree after
    # Waves 67/68). Assert presence and format only.
    base = (ROOT / "templates" / "base.html").read_text()
    sw = (ROOT / "static" / "sw.js").read_text()
    assert re.search(r"v='\d+'", base)
    assert re.search(r'GANITRA_CACHE = "ganitra-static-v\d+"', sw)
