"""Wave 64: Hindi-medium Previous Papers (Suraj, 15 Nov 2026:
"hindi papers bhi chahiye").

Four genuine Hindi-medium CBSE papers join the typed-paper
library — the Hindi halves of the same printed bilingual
papers, transcribed question-by-question from the papers
themselves (never translated, never invented):
cbse-12-2024-hindi, cbse-12-2023-hindi, cbse-10-2024-hindi
(38 questions / 80 marks each) and cbse-10-2022-term2-hindi
(14 / 40) — 128 Hindi questions. The list labels every
paper's medium; a Hindi sheet renders in the paper's own
language (गणित subject line, सामान्य निर्देश, खण्ड headings,
अधिकतम अंक, अथवा dividers, lowercase (a)–(d) options split
onto their own lines). [Figure] census for the Hindi texts:
2 + 3 + 4 + 3 = 12. Pins ?v=43 / cache ganitra-static-v20.
"""
import html as _html
import re
from pathlib import Path

import pytest

import papers_data

ROOT = Path(__file__).resolve().parent.parent

HINDI_IDS = ["cbse-12-2024-hindi", "cbse-12-2023-hindi",
             "cbse-10-2024-hindi", "cbse-10-2022-term2-hindi"]
HINDI_FIGURES = {"cbse-12-2024-hindi": 2, "cbse-12-2023-hindi": 3,
                 "cbse-10-2024-hindi": 4,
                 "cbse-10-2022-term2-hindi": 3}
HINDI_PAPERS = [papers_data.get_paper(pid) for pid in HINDI_IDS]
DEV = re.compile(r"[\u0900-\u097F]")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W64 Test Tester", "class": "12", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w64-test-pass"})
    return c


def _page(client, paper_id):
    r = client.get("/papers/" + paper_id)
    assert r.status_code == 200
    return r.get_data(as_text=True)


# --- data ------------------------------------------------------

def test_hindi_papers_complete_and_real():
    total = 0
    for p in HINDI_PAPERS:
        total += len(p["questions"])
        assert p["medium"] == "hindi"
        assert p["subject_label"].startswith("गणित")
        want = 40 if "term2" in p["id"] else 80
        assert papers_data.paper_total_marks(p) == want
        assert [q["number"] for q in p["questions"]] == \
            list(range(1, len(p["questions"]) + 1))
        for q in p["questions"]:
            # genuine Hindi text, Hindi divider word only
            assert len(DEV.findall(q["text"])) >= 5
            assert " OR " not in q["text"]
    assert total == 128
    # Wave 66: library grew from 17 to 39 papers (all boards).
    # Wave 113: 53 papers (11 more CBSE English papers; the
    # Hindi count is unchanged at 16). Deploy-25 merge: Wave
    # 114 adds 15 more state-board papers — 68 in total.
    assert len(papers_data.PAPERS) == 68


def test_hindi_papers_restore_questions_the_english_entries_omit():
    hi10 = {q["number"] for q in
            papers_data.get_paper("cbse-10-2024-hindi")["questions"]}
    en10 = {q["number"] for q in
            papers_data.get_paper("cbse-10-2024")["questions"]}
    assert {12, 18} <= hi10 - en10
    hi12 = {q["number"] for q in
            papers_data.get_paper("cbse-12-2023-hindi")["questions"]}
    en12 = {q["number"] for q in
            papers_data.get_paper("cbse-12-2023")["questions"]}
    assert {13, 15} <= hi12 - en12


# --- list page ---------------------------------------------------

def test_list_labels_every_medium(client):
    body = client.get("/papers").get_data(as_text=True)
    # Wave 66: the library grew to 39 papers (15 Hindi-medium,
    # 24 English-medium) across 9 boards. Wave 94: 42 papers
    # (16 Hindi-medium, 26 English-medium). Counted via the
    # chip markup: two Wave-66 entry notes also contain the
    # words "English Medium" as plain text. Deploy-25 merge:
    # 68 papers (16 Hindi-medium, 52 English-medium — Wave 113
    # took English to 37, Wave 114's 15 are all English).
    assert body.count("हिंदी माध्यम · Hindi Medium</span>") == 16
    assert body.count("English Medium</span>") == 52
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


# --- Hindi sheets ------------------------------------------------

@pytest.mark.parametrize("paper", HINDI_PAPERS,
                         ids=[p["id"] for p in HINDI_PAPERS])
def test_hindi_sheet_is_the_complete_typed_paper(client, paper):
    body = _page(client, paper["id"])
    assert body.count('class="paper-q"') == len(paper["questions"])
    assert paper["set_label"] in body
    assert paper["subject_label"] in body
    assert "सामान्य निर्देश :" in body
    assert "सभी प्रश्न अनिवार्य हैं।" in body
    want = 40 if "term2" in paper["id"] else 80
    assert f"अधिकतम अंक : {want}" in body
    assert body.count("[Figure]") == HINDI_FIGURES[paper["id"]]
    flat = _html.unescape(re.sub(r"<[^>]+>", " ", body))
    flat = " ".join(flat.split())
    for q in paper["questions"]:
        assert " ".join(q["text"].split()) in flat
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


def test_hindi_sections_and_dividers(client):
    body = _page(client, "cbse-12-2024-hindi")
    heads = [body.index(f"खण्ड {s}") for s in "कखगघङ"]
    assert heads == sorted(heads)
    assert '<p class="q-or">अथवा</p>' in body
    # section instruction lines in Hindi
    assert "खण्ड क में 20 प्रश्न हैं" in body
    assert "खण्ड ङ में 3 प्रश्न हैं" in body


def test_lowercase_options_get_own_lines(client):
    body = _page(client, "cbse-10-2024-hindi")
    assert '<p class="q-line">(a) √2</p>' in body
    assert '<p class="q-line">(d) 1/2</p>' in body
    body = _page(client, "cbse-12-2023-hindi")
    assert '<p class="q-line">(a) −2</p>' in body


def test_athava_inside_an_option_is_not_a_divider(client):
    # 12-2023 Q.3's option (d) is "8 अथवा −8" ("8 or −8") — the
    # word अथवा inside an option must NOT become an OR divider;
    # only a labelled alternative ((क)/(ख)/(A)/(B)/(iii)…) may.
    body = _page(client, "cbse-12-2023-hindi")
    assert '<p class="q-line">(d) 8 अथवा −8</p>' in body
    q3 = [q for q in papers_data.get_paper(
        "cbse-12-2023-hindi")["questions"] if q["number"] == 3][0]
    assert "अथवा" in q3["text"]


def test_hindi_print_view(client):
    r = client.get("/papers/print?paper=cbse-10-2022-term2-hindi")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert body.count('class="paper-q"') == 14
    assert "सामान्य निर्देश :" in body
    assert "अधिकतम अंक : 40" in body
    for p in papers_data.PAPERS:
        assert p["source_url"] not in body


def test_english_sheet_unchanged(client):
    body = _page(client, "cbse-12-2024")
    assert "General Instructions:" in body
    assert "Maximum Marks : 80" in body
    assert '<p class="q-or">OR</p>' in body
    assert "SECTION A" in body


def test_pins_bumped_for_wave64():
    base = (ROOT / "templates" / "base.html").read_text()
    sw = (ROOT / "static" / "sw.js").read_text()
    css = (ROOT / "static" / "style.css").read_text()
    assert "v='43'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v20"' in sw
    assert ".paper-medium" in css
    assert "Noto Serif Devanagari" in css
