"""Wave 229 — answer depth + the papers' original-paper look
(Suraj's orders: definition answers must teach, not just
recite; and "paper kaa orginal photo jaisa dikhana chahiye",
with screenshot case 7's glued options — "(a)2(b)6(c)20(d)1"
— as the specific defect).

Pinned here:

1. DEFINITION DEPTH (concepts.py + fallback._concept_result):
   the deepened cards serve, after the worked example, a
   worked COUNTERexample ("Not an example:" block, with the
   failing reason shown in its steps) and the standard test
   for the concept ("Quick check:" — horizontal line test,
   vertical line test, put-the-value-in, ...). The one-one /
   onto family goes first (the Deploy-69 live evidence: the
   one-one part was thin), then polynomial / vector, then
   the rest of the audited definition cards. Cards WITHOUT
   the depth fields render byte-identically to before.

2. PAPERS LOOK (app.py _paper_q_lines/_option_run_lines,
   templates/_paper_sheet.html, static/style.css +
   templates/papers_print.html): a stored MCQ option run —
   lowercase on an English paper (never split before this
   wave) or stored glued with no spaces at all — renders as
   one spaced line per option inside a .q-opts wrapper, in
   the in-app sheet AND the standalone print view; the sheet
   keeps its exam header block (set line, subject, class /
   board / year, Maximum Marks row) and the Wave 63/64 pins
   (option lines are still <p class="q-line">, the Hindi
   sheets unchanged). Presentation only: every stored word
   still reaches the page.
"""
import re
from pathlib import Path

import pytest

import fallback
import papers_data
from concepts import get_concept
from fallback import fallback_answer

ROOT = Path(__file__).resolve().parent.parent

CANNED = (
    "I didn't understand that",
    "Samajh nahi aaya",
    "समझ नहीं आया",
    "Answer not found",
)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w229.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    monkeypatch.delenv("GANITRA_AIVERIFY", raising=False)
    monkeypatch.delenv("GANITRA_DEEP_SOLVE", raising=False)
    return path


@pytest.fixture()
def no_legs(monkeypatch):
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


def _steps_text(res):
    return "\n".join(str(s) for s in res.get("steps") or [])


def _route_to(entry):
    """A keyword of `entry` that find_concept resolves to
    THIS card (first-match order respected), or None."""
    from concepts import find_concept
    for kw in entry["keywords"]:
        if find_concept(kw) is entry:
            return kw
    return None


def _card_result(concept_id):
    entry = get_concept(concept_id)
    assert entry is not None
    kw = _route_to(entry)
    assert kw is not None, concept_id
    res = fallback._concept_result(kw, False)
    assert res is not None and res["concept_id"] == concept_id
    return res


# ---------------------------------------------------------------------------
# 1. Definition depth — the one-one / onto family
# ---------------------------------------------------------------------------

def test_one_one_onto_combined_has_example_non_example_and_test(
        db, no_legs):
    # The Deploy-69 live-evidence question, verbatim.
    res = fallback_answer(
        "Define one-one and onto functions with examples.",
        lang="en")
    assert res.get("concept_id") == "one_one_onto_concept", res
    steps = _steps_text(res)
    # A real worked example that CHECKS both halves...
    assert "Example:" in steps
    assert "One-one:" in steps and "Onto:" in steps
    assert "bijective" in steps
    # ...a worked counterexample whose steps show BOTH
    # failures (two inputs one output; a codomain value
    # never hit)...
    assert "Not an example:" in steps
    ne = steps.split("Not an example:", 1)[1]
    assert "f(2) = 4" in ne and "−4" in ne
    assert "neither one-one nor onto" in ne
    # ...and the standard tests are named.
    assert "Quick check:" in steps
    assert "horizontal line" in steps.lower()
    for bad in CANNED:
        assert bad not in str(res.get("answer") or "")


def test_one_one_card_depth(db, no_legs):
    res = _card_result("one_one_concept")
    steps = _steps_text(res)
    # Worked example (a function that passes)...
    assert "Example:" in steps and "3x − 5" in steps
    # ...worked non-example (a function that fails, with
    # the collision shown)...
    assert "Not an example:" in steps
    assert "f(3) = 3" in steps and "f(−3) = 3" in steps
    # ...and the standard test.
    assert "horizontal line test" in steps.lower()


def test_onto_card_depth(db, no_legs):
    res = _card_result("onto_concept")
    steps = _steps_text(res)
    assert "Example:" in steps
    # Non-example beyond restating the definition: e^x
    # never reaches a negative codomain value.
    assert "Not an example:" in steps
    assert "e^x" in steps and "−1" in steps
    # The standard check: solve y = f(x) for x.
    assert "Quick check:" in steps and "solve y = f(x)" in steps


def test_bijective_ties_both_together(db, no_legs):
    res = _card_result("bijective_concept")
    steps = _steps_text(res)
    low = steps.lower()
    # The definition itself ties the two halves together...
    assert "one-one" in str(res.get("answer") or "").lower()
    assert "onto" in str(res.get("answer") or "").lower()
    # ...the example checks both halves...
    assert "One-one:" in steps and "Onto:" in steps
    # ...the non-example fails BOTH, each for its own
    # shown reason...
    ne = steps.split("Not an example:", 1)[1]
    assert "Not one-one" in ne and "Not onto" in ne
    # ...and the method is exactly "check the two halves".
    assert "two halves" in low and "inverse" in low


# ---------------------------------------------------------------------------
# 1b. Definition depth — Wave 226 cards + the audited rest
# ---------------------------------------------------------------------------

DEEPENED = [
    # (concept_id, not-example marker, method marker or None)
    ("polynomial_concept", "√x + 2", "whole number"),
    ("vector_concept", "speed is a scalar", "direction"),
    ("function_basics", "not a function", "vertical line"),
    ("domain_range", "x ≥ 0", "denominator"),
    ("ap_gp", "it is a GP", "Subtract neighbours"),
    ("subset_concept", "not a subset", "element by element"),
    ("pi_concept", "approximation", None),
    ("log_concept", "Not defined", "power question"),
    ("factors_concept", "not a factor of 18", None),
    ("tangent_concept", "secant", None),
    ("poly_zeroes", "not a zero", "Put the value in"),
    ("quadratic_equation_concept", "linear equation",
     "highest power"),
]


@pytest.mark.parametrize(
    "concept_id,ne_marker,method_marker", DEEPENED,
    ids=[d[0] for d in DEEPENED])
def test_deepened_cards_carry_counterexample(
        concept_id, ne_marker, method_marker):
    res = _card_result(concept_id)
    steps = _steps_text(res)
    # Worked example still served, then the counterexample
    # block with its verdict marker, then the method when
    # the card carries one.
    assert "Example:" in steps
    assert "Not an example:" in steps
    assert ne_marker in steps
    if method_marker is not None:
        assert "Quick check:" in steps
        assert method_marker in steps


def test_undeepened_card_renders_as_before():
    # A card without the depth fields: exactly the Wave 18
    # rendering — explain, Hinglish line, example block,
    # nothing else.
    entry = get_concept("pythagoras")
    assert "not_example" not in entry and "method" not in entry
    res = fallback._concept_result("pythagoras theorem", False)
    steps = res["steps"]
    assert steps[0] == entry["explain"]
    assert steps[1] == f"Hinglish me: {entry['hinglish']}"
    assert steps[2] == f"Example: {entry['example']['q']}"
    assert steps[-1] == (f"Example answer: "
                         f"{entry['example']['answer']}")
    assert not any(s.startswith("Not an example:")
                   for s in steps)
    assert not any(s.startswith("Quick check:") for s in steps)


def test_depth_fields_are_well_formed():
    for entry_id, _ne, _m in DEEPENED:
        entry = get_concept(entry_id)
        ne = entry["not_example"]
        assert ne["q"] and ne["steps"] and ne["answer"]
    for cid in ("one_one_onto_concept", "one_one_concept",
                "onto_concept", "bijective_concept"):
        entry = get_concept(cid)
        assert entry["not_example"]["q"]
        assert entry["not_example"]["steps"]
        assert entry["method"]


# ---------------------------------------------------------------------------
# 2. Papers — options layout + the exam-sheet look
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W229 Test Tester", "class": "12", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w229-test-pass"})
    return c


def _page(client, paper_id):
    r = client.get("/papers/" + paper_id)
    assert r.status_code == 200
    return r.get_data(as_text=True)


def test_english_lowercase_options_get_own_spaced_lines(client):
    # cbse-12-2023 Q1 is stored as one running line:
    # "... x + y is: (a) −2 (b) 2 (c) −3 (d) 3" — before
    # Wave 229 an English sheet never split lowercase runs.
    body = _page(client, "cbse-12-2023")
    for opt in ("(a) −2", "(b) 2", "(c) −3", "(d) 3"):
        assert f'<p class="q-line">{opt}</p>' in body
    # The options sit inside ONE .q-opts grid block...
    assert '<div class="q-opts">' in body
    # ...and the glued one-line form is gone from the sheet.
    assert "(a) −2 (b) 2" not in body


def test_glued_options_in_stored_text_are_unglued(client,
                                                  monkeypatch):
    # The screenshot shape itself: options stored with NO
    # spaces at all. (No stored paper carries this shape —
    # the census is in the build packet — so a synthetic
    # paper exercises the splitter end to end.)
    synthetic = {
        "id": "w229-synthetic",
        "set_label": "Question Paper Code No. 000/1/1",
        "subject_label": "Mathematics",
        "class_num": 10, "board": "CBSE", "year": 2025,
        "questions": [{
            "section": "A", "number": 1, "marks": 1,
            "text": "The value of 2 × 3 × 5 + 1 is:"
                    "(a)29(b)31(c)30(d)32",
        }],
    }
    monkeypatch.setitem(papers_data.PAPER_BY_ID,
                        "w229-synthetic", synthetic)
    body = _page(client, "w229-synthetic")
    for opt in ("(a) 29", "(b) 31", "(c) 30", "(d) 32"):
        assert f'<p class="q-line">{opt}</p>' in body
    assert "(a)29(b)31" not in body
    assert '<div class="q-opts">' in body


def test_assertion_reason_stem_is_not_an_option_run(client):
    # cbse-10-2025-basic Q19: "Assertion (A): ... Reason
    # (R): ..." followed by the question's REAL options
    # "(A) Both A and R are true ... (D) ...". The single
    # (A)/(R) labels in the stem must never be read as an
    # option run (the splitter needs 3+ sequential labels,
    # and a label after a letter — "P(A)", "f(a)" — never
    # counts); the genuine run at the end splits as before.
    body = _page(client, "cbse-10-2025-basic")
    stem = body.split("Assertion (A):", 1)[1]
    stem = stem.split('<div class="q-opts">', 1)[0]
    assert "Reason (R):" in stem
    assert ('<p class="q-line">(A) Both A and R are true and '
            'R is the correct explanation of A</p>') in body


def test_sheet_header_block_and_look_hooks(client):
    body = _page(client, "cbse-12-2023")
    assert 'class="exam-sheet"' in body
    assert 'class="sheet-code"' in body
    assert 'class="sheet-subject"' in body
    assert 'class="sheet-marksrow"' in body
    assert "Maximum Marks : 80" in body
    assert 'class="sheet-section"' in body
    css = (ROOT / "static" / "style.css").read_text()
    # The original-paper furniture lives in the sheet CSS:
    # off-white paper, the double rule, the options grid.
    assert ".exam-sheet .q-opts" in css
    assert "3px double" in css
    assert "#fffdf6" in css
    # Version pins moved with the CSS change.
    base = (ROOT / "templates" / "base.html").read_text()
    sw = (ROOT / "static" / "sw.js").read_text()
    assert "v='65'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v41"' in sw
    assert '"/static/style.css?v=65"' in sw


def test_print_view_keeps_the_paper_look(client):
    r = client.get("/papers/print?paper=cbse-12-2023")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert '<div class="q-opts">' in body
    assert '<p class="q-line">(a) −2</p>' in body
    assert "Maximum Marks : 80" in body
    # The print view's inline copy carries the same grid +
    # double-rule rules as style.css.
    assert ".q-opts" in body and "3px double" in body


def test_hindi_sheet_options_still_own_lines(client):
    # The Wave 64 pins, unchanged by the new wrapper: the
    # option lines render exactly as before, now grouped.
    body = _page(client, "cbse-10-2024-hindi")
    assert '<p class="q-line">(a) √2</p>' in body
    assert '<p class="q-line">(d) 1/2</p>' in body
    assert '<div class="q-opts">' in body
    body = _page(client, "cbse-12-2023-hindi")
    assert '<p class="q-line">(d) 8 अथवा −8</p>' in body


def test_no_stored_word_is_lost_by_the_split(client):
    # Presentation only: for a paper dense with option
    # runs, every stored question text still reaches the
    # page whole (whitespace-normalised), exactly as the
    # Wave 63 census asserts for the whole library.
    import html as _html
    body = _page(client, "cbse-12-2023")
    flat = _html.unescape(re.sub(r"<[^>]+>", " ", body))
    flat = " ".join(flat.split())
    paper = papers_data.get_paper("cbse-12-2023")
    for q in paper["questions"]:
        assert " ".join(q["text"].split()) in flat, q["number"]
