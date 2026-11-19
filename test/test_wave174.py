"""Wave 174: paper-request routing (Suraj's live test,
19 Nov 2026).

Suraj typed into the chat:

    "Mp board ka maths ka paper chahiye 12th class ka 2025"
    "Mp board ke exams paper 12th class"

and got the bare not-found line both times — although the
exact paper (MP Board Class 12 Maths 2025) sits in the
Previous Papers library. Root cause: no intent layer
recognised a paper request. The solver parsed the sentence
as an expression (op "error"), greeting / non-maths / meta
/ guidance all passed, and the chain ended at the not-found
line.

Fix: paper_requests.py — a strict intent layer (paper word
+ board or class + a problem-payload veto + maths-only
subject check) hooked into fallback's chain after the
non-maths guard and before maths_meta. Serves:
  (a) the exact paper as a typed-sheet answer card,
  (b) the closest year with a one-line note when the asked
      year is missing from the library,
  (c) an honest availability line (never the bare
      not-found) when the board/class has no paper,
  (d) a short which-board / which-class line when one of
      them is missing.
"paper" joins followups._NOT_SOLVED_KINDS and the chat JS
mirror W122_NOT_SOLVED_KINDS (a paper card is library
content, not a solve — no answer box, no follow-up chips);
delivery pins moved with the deploys (final after the
Deploy-44 merge: ?v=60 / ganitra-static-v37).
"""
import re
from pathlib import Path

import pytest

import papers_data
from fallback import fallback_answer
from followups import is_solved_result
from paper_requests import paper_result

ROOT = Path(__file__).resolve().parent.parent

LIVE_1 = "Mp board ka maths ka paper chahiye 12th class ka 2025"
LIVE_2 = "Mp board ke exams paper 12th class"
# Wave 204 (Suraj, 20 Nov): ans not found hamesha ke liye band
# — the terminal lines a paper serve must never be are the
# clarification lines now.
NOT_FOUND = {
    "I didn't understand that — type your maths question "
    "a little clearly and I'll solve it right away.",
    "Samajh nahi aaya — maths ka sawal thoda saaf likh kar "
    "bhejo, main turant solve kar dunga.",
    "समझ नहीं आया — गणित का सवाल थोड़ा साफ़ लिखकर भेजिए, "
    "मैं तुरंत हल कर दूँगा।"}


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the AI legs must stay inert — a paper
    request must never reach them anyway."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _serve(q):
    r = fallback_answer(q)
    assert r.get("answer") not in NOT_FOUND, q
    return r


# ---------------------------------------------------------------------------
# 1. The two live requests, verbatim
# ---------------------------------------------------------------------------

def test_live_request_1_serves_the_exact_mp_paper():
    r = _serve(LIVE_1)
    assert r["fallback_kind"] == "paper"
    assert r["paper_id"] == "mpbse-12-2025"
    paper = papers_data.get_paper("mpbse-12-2025")
    assert str(paper["year"]) in r["answer"]
    # The typed sheet: header + every stored question.
    body = "\n".join(r["steps"])
    assert paper["questions"][0]["text"][:40] in body
    assert paper["questions"][-1]["text"][:40] in body
    assert "Maximum Marks: 80" in body
    assert not r.get("plain_reply")


def test_live_request_2_serves_the_mp_paper():
    r = _serve(LIVE_2)
    assert r["fallback_kind"] == "paper"
    assert r["paper_id"] == "mpbse-12-2025"


def test_live_requests_end_to_end_via_api(client):
    for q in (LIVE_1, LIVE_2):
        data = client.post(
            "/api/solve", json={"question": q}).get_json()
        result = data.get("result") or data
        assert result.get("fallback_kind") == "paper", q
        assert result.get("paper_id") == "mpbse-12-2025", q


# ---------------------------------------------------------------------------
# 2. English / Hinglish / Devanagari variants
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,pid", [
    ("CBSE class 10 maths paper 2024", "cbse-10-2024"),
    ("MP board 12th maths paper 2025", "mpbse-12-2025"),
    ("class 12 mp board paper", "mpbse-12-2025"),
    ("UP board ka paper chahiye 10th class ka", "up-10-2025"),
    ("haryana board 12th paper 2024", "hbse-12-2024"),
    ("Give me the CBSE Class 12 Mathematics paper of 2025",
     "cbse-12-2025"),
    ("rbse 12th ka paper hindi medium", "rbse-12-2025-hindi"),
    ("Kerala board class 6 paper", "kerala-6-2025-annual"),
    ("JAC class 10 maths paper", "jac-10-2026-model"),
    ("CBSE class 10 maths sample paper 2026",
     "cbse-10-sample-2026"),
])
def test_variants_serve_the_right_paper(q, pid):
    r = _serve(q)
    assert r["fallback_kind"] == "paper", q
    assert r["paper_id"] == pid, q


@pytest.mark.parametrize("q,pid", [
    ("एमपी बोर्ड का गणित का प्रश्न पत्र चाहिए कक्षा 12 का 2025",
     "mpbse-12-2025-hindi"),
    ("एमपी बोर्ड कक्षा १२ गणित पेपर २०२५", "mpbse-12-2025-hindi"),
    ("मुझे सीबीएसई कक्षा 10 का गणित का पेपर चाहिए",
     "cbse-10-2025"),
    ("मध्य प्रदेश बोर्ड बारहवीं का पेपर", "mpbse-12-2025-hindi"),
])
def test_devanagari_variants_serve_hindi_medium(q, pid):
    r = _serve(q)
    assert r["fallback_kind"] == "paper", q
    assert r["paper_id"] == pid, q


def test_no_year_serves_latest_real_not_sample():
    r = _serve("class 10 maths paper cbse")
    assert r["paper_id"] == "cbse-10-2025"


# ---------------------------------------------------------------------------
# 3. Year asked but unavailable -> closest year + the note
# ---------------------------------------------------------------------------

def test_missing_year_serves_closest_with_note():
    r = _serve("CBSE class 12 maths paper 2021")
    assert r["fallback_kind"] == "paper"
    assert r["paper_id"] == "cbse-12-2022-term1"
    note = r["steps"][0]
    assert "2021" in note and "2022" in note


def test_exact_year_has_no_substitution_note():
    r = _serve("CBSE class 10 maths paper 2024")
    assert "not in the library" not in r["steps"][0]


# ---------------------------------------------------------------------------
# 4. No paper for the board/class -> honest availability line
# ---------------------------------------------------------------------------

def test_board_without_that_class_names_available_boards():
    # Wave 179 CHANGED THE TRUTH: GSEB Class 12 now HAS a
    # paper (gseb-12-2025), so the missing-class case moves
    # to Class 11, which GSEB does not have.
    r = _serve("Gujarat board class 11 maths paper")
    assert r["fallback_kind"] == "paper"
    assert r.get("plain_reply")
    assert "Jharkhand" in r["answer"]
    assert "GSEB" in r["answer"] or "Gujarat" in r["answer"]


def test_board_with_no_papers_at_all_names_available_boards():
    # Wave 179 CHANGED THE TRUTH: West Bengal Class 10 now
    # HAS a paper (wbbse-10-2025) — every recognised board
    # has papers now, so the no-papers-at-all case no
    # longer exists. The honest line is exercised via a
    # class the board does not have (Class 9).
    r = _serve("West Bengal board class 9 maths paper")
    assert r["fallback_kind"] == "paper"
    assert r.get("plain_reply")
    assert "Jharkhand" in r["answer"]


def test_class_without_any_paper_names_available_classes():
    r = _serve("CBSE class 5 maths paper")
    assert r["fallback_kind"] == "paper"
    assert "10" in r["answer"] and "12" in r["answer"]


def test_missing_board_asks_and_lists():
    r = _serve("class 10 maths paper chahiye")
    assert r["fallback_kind"] == "paper"
    assert "CBSE" in r["answer"]


def test_missing_class_asks_and_lists():
    r = _serve("CBSE maths paper")
    assert r["fallback_kind"] == "paper"
    assert "10" in r["answer"] and "12" in r["answer"]


def test_other_subject_gets_the_maths_only_line():
    r = _serve("CBSE class 10 science paper")
    assert r["fallback_kind"] == "paper"
    assert "Mathematics" in r["answer"] or "Maths" in r["answer"]


# ---------------------------------------------------------------------------
# 5. Guards: "paper" in a maths sense still solves normally
# ---------------------------------------------------------------------------

def test_rectangular_paper_sheet_solves_normally():
    r = fallback_answer(
        "A rectangular sheet of paper is 22 cm long and 10 cm "
        "wide. Find its area.")
    assert r.get("fallback_kind") != "paper"
    assert "220" in str(r.get("answer"))


def test_pasted_paper_context_with_a_problem_solves_it():
    r = fallback_answer(
        "In the CBSE class 10 paper, find the area of a "
        "circle with radius 7 cm")
    assert r.get("fallback_kind") != "paper"
    assert "154" in str(r.get("answer"))


def test_plain_maths_question_untouched():
    r = fallback_answer("Find the area of a circle with "
                        "radius 7 cm")
    assert r.get("fallback_kind") != "paper"
    assert "154" in str(r.get("answer"))


@pytest.mark.parametrize("q", [
    "paper",
    "what is a question paper",
    "paper paper paper",
    "2 + 3 = ?",
    "Find the HCF of 12 and 18",
])
def test_non_requests_decline_at_the_layer(q):
    assert paper_result(q) is None, q


# ---------------------------------------------------------------------------
# 6. Card treatment + delivery pins
# ---------------------------------------------------------------------------

def test_paper_card_is_not_a_solved_result():
    r = _serve(LIVE_1)
    assert is_solved_result(r) is False
    js = (ROOT / "templates" / "index.html").read_text(
        encoding="utf-8")
    m = re.search(r"W122_NOT_SOLVED_KINDS = \[(.*?)\];", js, re.S)
    assert m and '"paper"' in m.group(1)


def test_pins_v58_v35():
    base = (ROOT / "templates" / "base.html").read_text(
        encoding="utf-8")
    sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
    assert "filename='style.css', v='60'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in sw
    assert '"/static/style.css?v=60"' in sw
