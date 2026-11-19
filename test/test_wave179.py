"""Wave 179: Papers Expansion Phase 1 (Suraj, 19 Nov 2026:
"Mp wala nhi — sabhi chahiye, kisi bhi class ka, kisi bhi
board ka").

The ten boards that had NO paper at all (West Bengal,
Punjab, Assam, Chhattisgarh, Himachal, J&K, Odisha, Andhra
Pradesh, Telangana, Goa) gain a real Class 10 AND Class 12
paper each, and the five big gaps inside covered boards
(GSEB-12, KSEAB-12, TN-12, UBSE-12, JAC-12) are filled.
29 papers / 911 questions; the library goes 73 -> 102
papers and 2,497 -> 3,408 questions. Every paper is a real
board paper transcribed in full from the board's official
booklet (AglaSem Docs mirrors of the official PDFs where
the board site itself serves no readable copy); the one
model paper (JAC Class 12, JCERT) is labelled model.

Known honest partials, recorded in each entry's note:
bsetelangana-10-2025 (Part A only — Part B is a separate
sheet absent from the official scan), bseodisha-10-2025
(Part-I Objective booklet only; 7 questions hidden under
the scan's booklet stamp omitted, never guessed),
cgbse-12-2025 (Q29 sits on a scan page the mirror lacks).
"""
import pytest

import papers_data
from paper_requests import paper_result

NEW_PAPERS = {
    # id: (class_num, year, n_questions)
    "wbbse-10-2025": (10, 2025, 17),
    "wbchse-12-2025": (12, 2025, 14),
    "pseb-10-2025": (10, 2025, 16),
    "pseb-12-2025": (12, 2025, 19),
    "seba-10-2025": (10, 2025, 61),
    "ahsec-12-2025": (12, 2025, 20),
    "cgbse-10-2025": (10, 2025, 18),
    "cgbse-10-2025-hindi": (10, 2025, 18),
    "cgbse-12-2025": (12, 2025, 28),
    "cgbse-12-2025-hindi": (12, 2025, 28),
    "hpbose-10-2025": (10, 2025, 37),
    "hpbose-10-2025-hindi": (10, 2025, 37),
    "hpbose-12-2025": (12, 2025, 34),
    "jkbose-10-2025": (10, 2025, 40),
    "jkbose-12-2025": (12, 2025, 31),
    "bseodisha-10-2025": (10, 2025, 43),
    "chseodisha-12-2025": (12, 2025, 4),
    "bseap-10-2025": (10, 2025, 32),
    "bieap-12-2025": (12, 2025, 24),
    "bsetelangana-10-2025": (10, 2025, 18),
    "tsbie-12-2024": (12, 2024, 23),
    "gbshse-10-2025": (10, 2025, 41),
    "gbshse-12-2025": (12, 2025, 36),
    "gseb-12-2025": (12, 2025, 77),
    "kseab-12-2025": (12, 2025, 48),
    "tn-12-2025": (12, 2025, 47),
    "ubse-12-2025": (12, 2025, 24),
    "ubse-12-2025-hindi": (12, 2025, 24),
    "jac-12-2026-model": (12, 2026, 52),
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    c.post("/signup", data={
        "name": "W179 Test Tester", "class": "12", "board": "CBSE",
        "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
        "password": "w179-test-pass"})
    return c


# ---------------------------------------------------------------------------
# 1. Catalogue integrity
# ---------------------------------------------------------------------------

def test_library_totals_after_wave179():
    assert len(papers_data.PAPERS) == 102
    assert sum(len(p["questions"])
               for p in papers_data.PAPERS) == 3408
    ids = [p["id"] for p in papers_data.PAPERS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_integrity(pid):
    class_num, year, nq = NEW_PAPERS[pid]
    p = papers_data.get_paper(pid)
    assert p is not None, pid
    assert p["class_num"] == class_num
    assert p["year"] == year
    assert len(p["questions"]) == nq
    assert p["source_url"].startswith("http")
    assert p["source_name"]
    assert p["set_label"]
    total = papers_data.paper_total_marks(p)
    maximum = p.get("max_marks") or total
    # Stored marks never fall below 80% of the printed
    # maximum (omissions are few and always noted), and
    # attempt-any papers legitimately store more.
    assert total >= 0.8 * maximum, pid
    assert 40 <= maximum <= 100, pid
    for q in p["questions"]:
        assert isinstance(q["number"], int), (pid, q["number"])
        assert q["section"] and q["chapter"]
        assert q["marks"] > 0
        assert len(q["text"]) >= 15, (pid, q["number"])


def test_only_jac12_is_a_model_paper():
    for pid in NEW_PAPERS:
        p = papers_data.get_paper(pid)
        if pid == "jac-12-2026-model":
            assert "model" in pid
            assert "model" in p["set_label"].lower()
        else:
            assert "model" not in pid
            assert "sample" not in pid


# ---------------------------------------------------------------------------
# 2. The chat serves every newly covered board x class
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,pid", [
    ("west bengal board class 10 maths paper", "wbbse-10-2025"),
    ("west bengal board class 12 maths paper", "wbchse-12-2025"),
    ("punjab board class 10 maths paper", "pseb-10-2025"),
    ("pseb class 12 maths paper chahiye", "pseb-12-2025"),
    ("assam board class 10 maths paper", "seba-10-2025"),
    ("assam board class 12 ka paper do", "ahsec-12-2025"),
    ("cgbse class 10 maths paper", "cgbse-10-2025"),
    ("chhattisgarh board class 12 maths paper", "cgbse-12-2025"),
    ("hpbose class 10 maths paper", "hpbose-10-2025"),
    ("himachal board class 12 maths paper", "hpbose-12-2025"),
    ("jkbose class 10 maths paper", "jkbose-10-2025"),
    ("j&k board class 12 maths paper", "jkbose-12-2025"),
    ("odisha board class 10 maths paper", "bseodisha-10-2025"),
    ("odisha board class 12 maths paper", "chseodisha-12-2025"),
    ("andhra pradesh board class 10 maths paper", "bseap-10-2025"),
    ("ap board class 12 maths paper", "bieap-12-2025"),
    ("telangana board class 10 maths paper", "bsetelangana-10-2025"),
    ("telangana board class 12 maths paper", "tsbie-12-2024"),
    ("goa board class 10 maths paper", "gbshse-10-2025"),
    ("goa board class 12 maths paper", "gbshse-12-2025"),
    ("gujarat board class 12 maths paper", "gseb-12-2025"),
    ("karnataka board class 12 maths paper", "kseab-12-2025"),
    ("tamil nadu board class 12 maths paper", "tn-12-2025"),
    ("uttarakhand board class 12 maths paper", "ubse-12-2025"),
    ("jharkhand board class 12 maths paper", "jac-12-2026-model"),
    ("cgbse class 10 maths paper hindi medium", "cgbse-10-2025-hindi"),
    ("hpbose class 10 maths paper hindi me", "hpbose-10-2025-hindi"),
    ("ubse class 12 maths paper hindi medium", "ubse-12-2025-hindi"),
])
def test_new_boards_serve_via_chat_layer(q, pid):
    r = paper_result(q)
    assert r is not None, q
    assert r.get("op") == "paper", q
    assert r.get("paper_id") == pid, q


def test_former_zero_board_missing_class_is_honest():
    r = paper_result("west bengal board class 9 maths paper")
    assert r is not None
    assert r.get("op") == "paper_none"
    assert "Jharkhand" in r["answer"]


# ---------------------------------------------------------------------------
# 3. Every new paper renders completely on its /papers page
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pid", sorted(NEW_PAPERS))
def test_new_paper_page_renders_fully(client, pid):
    import html as _html
    import re as _re
    paper = papers_data.get_paper(pid)
    body = client.get(f"/papers/{pid}").get_data(as_text=True)
    assert body.count('class="paper-q"') == len(paper["questions"])
    # set_label renders autoescaped (two new labels contain
    # "&": Telangana "15E & 16E", WBBSE "B & E").
    assert _html.escape(paper["set_label"]) in body
    # Full text survives (whitespace-normalised, exactly
    # like test_wave63: the sheet only adds display breaks).
    flat = _html.unescape(_re.sub(r"<[^>]+>", " ", body))
    flat = " ".join(flat.split())
    for q in paper["questions"]:
        assert " ".join(q["text"].split()) in flat, \
            (pid, q["number"])
