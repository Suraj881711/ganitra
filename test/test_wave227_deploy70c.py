"""Wave 227 — Deploy-70b check (a) regression tests.

Deploy-70b went live and the 5-part paste split into all
five parts — but part (4), "What is the HCF of 12 and 18?",
was answered 1 instead of 6, twice, in fresh chats: the
steps rendered "Prime factorisation: 1 = " (empty) twice,
then "GCD = 1". The other four parts were correct.

Root cause (mechanism, proven locally in this file): the
part-solve was handed the PREAMBLE-BOUND text — the
multipart layer's first candidate is always
"<preamble> <part>" — and the route had already run the
whole paste through human_brain.normalize_human_text,
whose _words_to_digits rewrites the idiom "one by one"
as the digits "1 by 1". So the HCF part-solve received
"Please solve all of these questions for me 1 by 1:
What is the HCF of 12 and 18?" — and
solver/number_theory.py's HCF/LCM branches read their
operands POSITIONALLY, as the first integers of the
whole text: [1, 1, 12, 18] -> a = 1, b = 1, and
_factor_str(1) is "" (factorint(1) == {}), hence the
empty factorisation lines and GCD = 1. The real operands
12 and 18 were never lost from the text; they were
simply read fourth and third. Round-2's local paste had
NO preamble (it started at "1)"), so its bound candidate
equalled the bare part and passed — the live paste's
preamble is the difference. The positional read is the
root, not the normaliser: a literal-digit dressing with
no number words at all ("Set 2: What is the HCF of 12
and 18?") answered 2, and "Chapter 5 exercise: LCM of
12 and 18" answered 180, before the fix.

Fix pinned here: number_theory._pair_operands anchors
the operands to the ask itself — the run listed right
after "<keyword> of", else the one clause carrying the
keyword, else the historical whole-text read — and all
five HCF/LCM consumers (gcd, lcm, together, product,
Devanagari) use it.
"""
import pytest

import fallback  # noqa: F401  (chain under test)
from multipart import split_general
from solver.number_theory import _pair_operands
from solver.router import solve_question

# The EXACT live paste (Deploy-70b check (a), verbatim).
PASTE = (
    "Please solve all of these questions for me one by one: "
    "1) What is 15% of 200? 2) Solve 2x + 3 = 11. "
    "3) Find the area of a circle with radius 7 cm. "
    "4) What is the HCF of 12 and 18? "
    "5) A train travels 120 km in 2 hours, what is its "
    "speed? Please show the working for each question "
    "separately so I can copy it into my notebook.")

PART_ANSWERS = ("(1) 30", "(2) x = 4", "(3) 154 cm²",
                "(4) 6", "(5) 60 km/h")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    monkeypatch.delenv("GANITRA_AI_STREAM", raising=False)
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    r = c.post("/signup", data={
        "name": "Wave227 Deploy70c", "class": "10",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave227pass"})
    assert r.status_code == 302, r.status_code
    return c


def _solve_classic(client, question):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    chat_id = r.get_json()["chat"]["id"]
    r = client.post("/api/solve", json={
        "question": question, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    return r.get_json()


# ---------------------------------------------------------------------------
# The exact live paste through the real route
# ---------------------------------------------------------------------------

def test_split_of_live_paste_keeps_part4_intact():
    # The segment itself was never mangled: the split hands
    # part 4 over whole, preamble separate. The corruption
    # happened inside the part-SOLVE, not the split.
    got = split_general(PASTE)
    assert got is not None
    preamble, parts = got
    assert preamble.startswith("Please solve all of these")
    assert parts[3][1] == "What is the HCF of 12 and 18?"


def test_live_paste_route_all_five_parts_hcf_is_six(client):
    # Before the fix this returned (4) 1 with the steps
    # "Prime factorisation: 1 = " twice and "GCD = 1".
    data = _solve_classic(client, PASTE)
    assert data["ok"] is True, data
    res = data["result"]
    assert res.get("op") == "multipart_general", res
    answer = str(res.get("answer") or "")
    for bit in PART_ANSWERS:
        assert bit in answer, (bit, answer[:240])
    steps = "\n".join(str(s) for s in res.get("steps") or [])
    assert "Prime factorisation: 12 = 2^2 × 3" in steps
    assert "Prime factorisation: 18 = 2 × 3^2" in steps
    assert "GCD = 6" in steps
    assert "Prime factorisation: 1 = " not in steps
    assert "GCD = 1" not in steps


# ---------------------------------------------------------------------------
# Standalone and sibling forms
# ---------------------------------------------------------------------------

def test_standalone_hcf_route(client):
    data = _solve_classic(client, "What is the HCF of 12 "
                                  "and 18?")
    assert data["ok"] is True, data
    res = data["result"]
    assert res.get("op") == "gcd", res
    assert str(res.get("answer")) == "6", res
    steps = "\n".join(str(s) for s in res.get("steps") or [])
    assert "Prime factorisation: 12 = 2^2 × 3" in steps
    assert "Prime factorisation: 18 = 2 × 3^2" in steps


def test_hcf_sibling_forms():
    cases = {
        # No "What is" wrapper.
        "HCF of 12 and 18": "6",
        # A different pair, "Find the …" wrapper.
        "Find the HCF of 24 and 36": "12",
        # The live mechanism itself: the preamble the route
        # normaliser produces ("one by one" -> "1 by 1")
        # bound into the part-solve.
        "Please solve all of these questions for me 1 by "
        "1: What is the HCF of 12 and 18?": "6",
        # The same positional trap with literal digits —
        # no normaliser anywhere near this one.
        "Set 2: What is the HCF of 12 and 18?": "6",
        # Operands before the keyword (Hinglish order).
        "12 aur 18 ka HCF batao": "6",
        # Operands in a keyword-less clause: the legacy
        # whole-text read must keep owning this shape.
        "The numbers are 12 and 18. Find their HCF.": "6",
        # Three operands after the anchor.
        "Find the HCF of 12, 18 and 24": "6",
    }
    for text, want in cases.items():
        res = solve_question(text)
        assert res.get("op") == "gcd", (text, res)
        assert str(res.get("answer")) == want, (text, res)


def test_lcm_forms_unaffected():
    res = solve_question("LCM of 12 and 18")
    assert res.get("op") == "lcm", res
    assert str(res.get("answer")) == "36", res
    # LCM folds every integer it is handed, so a digit
    # dressing changed its value too (180 before the fix).
    res = solve_question(
        "Chapter 5 exercise: What is the LCM of 12 "
        "and 18?")
    assert res.get("op") == "lcm", res
    assert str(res.get("answer")) == "36", res
    # The together ask keeps both values.
    res = solve_question("Find the HCF and LCM of 12 "
                         "and 18")
    assert res.get("op") == "hcf_lcm", res
    assert str(res.get("answer")) == "HCF = 6, LCM = 36", res


def test_pair_operands_anchor_directly():
    bound = ("please solve all of these questions for me "
             "1 by 1: what is the hcf of 12 and 18?")
    assert _pair_operands(bound, bound, "gcd") == [12, 18]
    dressed = "set 2: what is the hcf of 12 and 18?"
    assert _pair_operands(dressed, dressed, "gcd") == [12, 18]
    hinglish = "12 aur 18 ka hcf batao"
    assert _pair_operands(hinglish, hinglish, "gcd") == [12, 18]
    legacy = "the numbers are 12 and 18. find their hcf."
    assert _pair_operands(legacy, legacy, "gcd") == [12, 18]
