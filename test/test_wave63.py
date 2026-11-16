"""Wave 63: Previous Papers as real typed papers, NO links
(Suraj, 15 Nov 2026: "practice paper kaa link nhi chahiye,
paper ko download karake photo lagana hai but real paper ki
tarah khud type karo").

Pins: no source_url (or any external paper link) is rendered
anywhere in the papers flow; every stored paper page is the
complete typed paper — exam header (code/set line, subject,
class/board/year, derived Maximum Marks), a General
Instructions block derived from the paper's own sections,
sections in order, every stored question with its number and
marks, OR dividers for internal choices, [Figure] markers
where the printed paper's figure is not in the data; the
stored-paper print view (?paper=<id>) renders the same sheet;
the generated-paper flow is untouched; delivery pins
?v=35 / cache ganitra-static-v16.
"""
import re
from pathlib import Path

import pytest

import papers_data

ROOT = Path(__file__).resolve().parent.parent

# The figure-reference census (Wave 63): questions whose text
# leans on a figure printed in the real paper. Counted by hand
# from the stored texts — see ganitra-wave63-notes.md.
FIGURE_COUNTS = {
    "cbse-12-2024": 1, "cbse-12-2023": 1, "cbse-10-2024": 3,
    "hbse-10-2024": 3, "cbse-10-2025": 4, "cbse-12-2025": 0,
    "cbse-10-2024-basic": 3, "cbse-10-2023": 5,
    "cbse-10-2025-basic": 7, "cbse-10-2020": 4,
    "cbse-10-2022-term2": 2, "cbse-12-2022-term2": 0,
    "hbse-12-2024": 0,
    # Wave 64: Hindi-medium papers — hand census on the Hindi
    # texts (figure-reference phrases in Hindi; see
    # ganitra-wave64-notes.md).
    "cbse-12-2024-hindi": 2, "cbse-12-2023-hindi": 3,
    "cbse-10-2024-hindi": 4, "cbse-10-2022-term2-hindi": 3,
    # Wave 66: all-boards expansion — census counted from the
    # rendered sheets (see ganitra-wave66-notes.md). Hindi
    # counts can differ from the English half of the same
    # booklet where the Hindi figure-reference phrasing falls
    # outside the Hindi marker regex (accepted, documented).
    "rbse-10-2025": 3, "rbse-10-2025-hindi": 2,
    "rbse-12-2025": 0, "rbse-12-2025-hindi": 0,
    "cbse-12-2022-term2-hindi": 0,
    "isc-12-2025": 2, "icse-10-2025": 2,
    "up-10-2025": 1, "up-10-2025-hindi": 0,
    "up-12-2025": 0, "up-12-2025-hindi": 0,
    "hbse-10-2024-hindi": 2, "hbse-12-2024-hindi": 1,
    "mpbse-10-2025": 2, "mpbse-10-2025-hindi": 0,
    "bseb-10-2025": 2, "bseb-10-2025-hindi": 2,
    "mpbse-12-2025": 0, "mpbse-12-2025-hindi": 0,
    "bseb-12-2025": 0, "bseb-12-2025-hindi": 0,
    "msbshse-10-2025-algebra": 0,
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
        "name": "W63 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w63-test-pass"})
    return c


def _paper_page(client, paper_id):
    r = client.get("/papers/" + paper_id)
    assert r.status_code == 200
    return r.get_data(as_text=True)


# --- no external links anywhere in the flow ----------------------

def test_list_page_has_no_paper_links(client):
    import markupsafe
    body = client.get("/papers").get_data(as_text=True)
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body
        # provenance as (autoescaped) plain text
        assert str(markupsafe.escape(p["source_name"])) in body
        assert f'href="/papers/{p["id"]}"' in body


@pytest.mark.parametrize("paper", papers_data.PAPERS,
                         ids=[p["id"] for p in papers_data.PAPERS])
def test_paper_page_has_no_external_links(client, paper):
    body = _paper_page(client, paper["id"])
    assert paper["source_url"] not in body
    for other in papers_data.PAPERS:
        assert other["source_url"] not in body


def test_generate_flow_has_no_scheme_link(client):
    r = client.post("/papers/generate", data={"class_num": "10"})
    body = r.get_data(as_text=True)
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body
    r = client.get("/papers/print")
    body = r.get_data(as_text=True)
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


# --- the typed sheet ---------------------------------------------

@pytest.mark.parametrize("paper", papers_data.PAPERS,
                         ids=[p["id"] for p in papers_data.PAPERS])
def test_sheet_is_the_complete_typed_paper(client, paper):
    body = _paper_page(client, paper["id"])
    # every stored question rendered exactly once
    assert body.count('class="paper-q"') == len(paper["questions"])
    # header: code/set line + subject + instructions
    assert paper["set_label"] in body
    if paper.get("medium") == "hindi":
        # Wave 64: Hindi-medium sheets carry the instructions in
        # the paper's own language.
        assert "सामान्य निर्देश :" in body
        assert "सभी प्रश्न अनिवार्य हैं।" in body
    else:
        assert "General Instructions:" in body
        assert "All questions are compulsory." in body
    # every question's full text survives (whitespace-normalised:
    # the sheet only adds display line-breaks)
    import html as _html
    flat = _html.unescape(re.sub(r"<[^>]+>", " ", body))
    flat = " ".join(flat.split())
    for q in paper["questions"]:
        assert " ".join(q["text"].split()) in flat


def test_header_maximum_marks_are_the_real_totals(client):
    # 80 for every full CBSE/HBSE paper (incl. ones whose
    # transcription omits a question or two), 40 for the 2022
    # Term-2 papers. Wave 66: other boards print their own
    # totals (UP 70/100, MP 75, BSEB 100, Maharashtra 40) and
    # alternative-section papers carry a max_marks override —
    # the header must show each paper's own maximum. (For the
    # original CBSE/HBSE papers the builder's section totals
    # give the printed 80 even where a transcription omits a
    # question or two, so the raw stored sum is not the
    # oracle there.)
    wave66_ids = {
        "rbse-10-2025", "rbse-10-2025-hindi", "rbse-12-2025",
        "rbse-12-2025-hindi", "cbse-12-2022-term2-hindi",
        "isc-12-2025", "icse-10-2025", "up-10-2025",
        "up-10-2025-hindi", "up-12-2025", "up-12-2025-hindi",
        "hbse-10-2024-hindi", "hbse-12-2024-hindi",
        "mpbse-10-2025", "mpbse-10-2025-hindi", "mpbse-12-2025",
        "mpbse-12-2025-hindi", "bseb-10-2025",
        "bseb-10-2025-hindi", "bseb-12-2025",
        "bseb-12-2025-hindi", "msbshse-10-2025-algebra",
    }
    for p in papers_data.PAPERS:
        body = _paper_page(client, p["id"])
        if p["id"] in wave66_ids:
            want = p.get("max_marks",
                         papers_data.paper_total_marks(p))
        else:
            want = 40 if "term2" in p["id"] else 80
        label = ("अधिकतम अंक" if p.get("medium") == "hindi"
                 else "Maximum Marks")
        assert f"{label} : {want}" in body, p["id"]


def test_instructions_reflect_each_papers_sections(client):
    body = _paper_page(client, "cbse-10-2020")
    # the 2020 paper's own structure: A20 B6 C8 D6, no Section E
    assert "Section A contains 20 questions of 1 mark each." in body
    assert "Section D contains 6 questions of 4 marks each." in body
    assert "SECTION E" not in body
    body = _paper_page(client, "cbse-12-2024")
    assert "Section E contains 3 questions of 4 marks each." in body
    assert ("This question paper contains 38 questions."
            in body)


def test_internal_choice_or_dividers(client):
    body = _paper_page(client, "cbse-12-2024")
    assert 'class="q-or"' in body
    # Q21's two alternatives both present, on separate lines
    assert "differentiable at x = 0" in body
    assert "√tan x" in body


def test_figure_markers_match_census(client):
    total = 0
    for p in papers_data.PAPERS:
        body = _paper_page(client, p["id"])
        n = body.count("[Figure]")
        assert n == FIGURE_COUNTS[p["id"]], p["id"]
        total += n
    assert total == 64


def test_section_order_and_subjects(client):
    body = _paper_page(client, "cbse-10-2024-basic")
    assert "Mathematics (Basic)" in body
    order = [body.index(f"SECTION {s}") for s in "ABCDE"]
    assert order == sorted(order)
    body = _paper_page(client, "cbse-12-2024")
    assert "Mathematics" in body


# --- print view ----------------------------------------------------

def test_stored_paper_print_view(client):
    r = client.get("/papers/print?paper=cbse-12-2024")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert body.count('class="paper-q"') == 38
    assert "Maximum Marks : 80" in body
    assert "General Instructions:" in body
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


def test_generated_print_flow_unchanged(client):
    client.post("/papers/generate", data={"class_num": "10"})
    r = client.get("/papers/print")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Answer Key" in body or "answer" in body.lower()
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


# --- delivery pins -------------------------------------------------

def test_pins_bumped():
    base = (ROOT / "templates" / "base.html").read_text()
    sw = (ROOT / "static" / "sw.js").read_text()
    assert "v='39'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v16"' in sw


def test_sheet_css_present():
    css = (ROOT / "static" / "style.css").read_text()
    for sel in (".exam-sheet", ".sheet-section", ".q-figure",
                ".q-or", ".q-marks"):
        assert sel in css
