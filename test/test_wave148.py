"""Wave 148 — fixes for the four failures the Deploy-28
live benchmark + comparison audit found:

1. "Find: (i) 15% of 200 (ii) 3/5 of 45" was served the
   letter-soup "5400·f^2·i^2·o·(Mod(15·I, o))" — the
   multipart layer never split it ("of" segments failed its
   ask test) and the complex solver's generic evaluate
   expanded word-harvested symbols into an "answer".
   Fixed at both layers: the of-computation segment shape
   splits and solves, and the complex solver declines any
   parse carrying free symbols (soft-unknown) so harvested
   soup can never be served from that seam again.
2. "mujhe kuch samajh nahi aa raha, tum bhi bekaar ho,
   7 ka table hi bata do" was hijacked twice: the Wave-96
   doubt layer re-explained the previous (wrong) step, and
   the Wave-111 meta layer served its fear-advice card —
   the fresh table request was never served. The doubt
   layer now vetoes fresh requests (table asks always; a
   fresh computation in its own clause unless a step number
   is pinned), the meta layer's computation veto covers
   table / of-computation asks too, and the junior table
   family + router intent learned "ki table" / "pahada".
3. "3x + 7 = 22" narrated "Add 15 from both sides" — the
   linear-steps template hardcoded "from" for both verbs.
   The preposition now pairs with the verb ("Subtract …
   from", "Add … to"), and steplang's rule accepts both.
4. A bare "step by step batao" after an answer was treated
   as a brand-new question. It now re-serves the stored
   answer with step labels (and a bare "detail me batao" /
   "vistar se samjhao" re-serves its Wave-136 detailed
   version); with no previous answer it falls through to
   the normal path and nothing is invented.
"""
import pytest

from doubt import parse_followup
from followups import is_solved_result, parse_bare_view_request
from maths_meta import meta_result
from multipart import general_multipart_result, split_general
from solver.complex_numbers import solve_complex
from solver.router import solve_question

GARBAGE_1 = "5400·f^2·i^2·o·(Mod(15·I, o))"

SIGNUP = {"name": "W148 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w148-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def solve(client, question):
    return client.post("/api/solve",
                       json={"question": question}).get_json()


# ------------------------------------------------------------------ #
# Failure 1a: the of-computation multipart split
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question,answer", [
    ("Find: (i) 15% of 200 (ii) 3/5 of 45", "(i) 30; (ii) 27"),
    ("Find (i) 20% of 150 (ii) 2/3 of 90", "(i) 30; (ii) 60"),
    ("What is (i) 10% of 80 (ii) 1/4 of 60", "(i) 8; (ii) 15"),
    ("Find (i) 35% of 640 (ii) 5/8 of 96", "(i) 224; (ii) 60"),
])
def test_of_computation_multipart_splits_and_solves(question,
                                                    answer):
    got = split_general(question)
    assert got is not None, question
    result = general_multipart_result(question)
    assert result is not None, question
    assert result["answer"] == answer


def test_split_general_mcq_option_veto_intact():
    # The Wave 141x146 veto: segments under a
    # choose-the-correct instruction are OPTIONS, not parts.
    q = ("Choose the correct answer: (i) 15% of 200 is "
         "(a) 20 (b) 30 (c) 40 (d) 50 (ii) 3/5 of 45 is "
         "(a) 25 (b) 26 (c) 27 (d) 28")
    assert split_general(q) is None


# ------------------------------------------------------------------ #
# Failure 1b: the garbage guard — harvested symbols never serve
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question", [
    "Find: (i) 15% of 200 (ii) 3/5 of 45",
    "Find (i) 35% of 640 (ii) 5/8 of 96",
    # Different numbers/fractions than the live example:
    # whatever letters its words donate, the parse carries
    # free symbols and must decline, never expand-and-serve.
    "Find (i) 45% of 300 (ii) 2/7 of 84",
    "What is (i) 10% of 80 (ii) 1/4 of 60",
])
def test_complex_solver_declines_word_harvests(question):
    result = solve_complex(question)
    assert result["op"] == "unknown"
    assert result["answer"] == ""


@pytest.mark.parametrize("question,answer", [
    ("modulus of 3 + 4i", "5"),
    ("(2 + 3i) + (4 - 5i)", "6 - 2·I"),
    ("Express 1/i in the form a + ib", "-I"),
    ("Multiply (1 + i) by (1 - i)", "2"),
    ("Find the conjugate of 3 - 2i.", "3 + 2·I"),
])
def test_complex_solver_legit_questions_unchanged(question,
                                                  answer):
    result = solve_complex(question)
    assert result["answer"] == answer


def test_garbage_string_never_served_end_to_end(client):
    data = solve(client, "Find: (i) 15% of 200 (ii) 3/5 of 45")
    assert data["ok"] is True
    assert data["result"]["answer"] == "(i) 30; (ii) 27"
    assert GARBAGE_1 not in str(data)
    data = solve(client, "Find (i) 35% of 640 (ii) 5/8 of 96")
    assert data["ok"] is True
    assert data["result"]["answer"] == "(i) 224; (ii) 60"
    assert "Mod(" not in str(data["result"]["answer"])


# ------------------------------------------------------------------ #
# Failure 2a: the doubt layer never claims a fresh request
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question", [
    # The exact live failure message.
    "mujhe kuch samajh nahi aa raha, tum bhi bekaar ho, "
    "7 ka table hi bata do",
    "samajh nahi aaya, 15% of 200 batao",
    "samajh nahi aaya, 3/5 of 45 batao",
    "samajh nahi aaya, solve 3x + 7 = 22",
    "ye samajh nahi aaya, 2 + 3 kitna hoga",
    # A table ask vetoes even beside a pinned step reference.
    "dusra step samjhao, 7 ka table bhi bata do",
    "samajh nahi aaya, table of 9 batao",
    "samajh nahi aaya, 12 ka pahada batao",
])
def test_doubt_vetoes_fresh_requests(question):
    assert parse_followup(question) is None, question


@pytest.mark.parametrize("question", [
    "ye step samajh nahi aaya",
    "dusra step samjhao",
    "step 2 samajh nahi aaya",
    "why did you divide by 3",
    "3 se bhaag kyun diya",
    "12 / 3 wala step samajh nahi aaya",
    "samajh nahi aaya",
    "agla step samjhao",
])
def test_doubt_still_claims_real_doubts(question):
    assert parse_followup(question) is not None, question


# ------------------------------------------------------------------ #
# Failure 2b: table requests serve the full table
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question,n", [
    ("7 ka table bata do", 7),
    ("7 ki table", 7),
    ("7 ka pahada", 7),
    ("table of 7", 7),
    ("13 ki table batao", 13),
    ("19 ka pahada bata do", 19),
    ("30 ka table", 30),
])
def test_table_requests_serve_full_table(question, n):
    result = solve_question(question)
    assert result is not None and result["op"] == "table"
    assert result["steps"][0] == f"{n} × 1 = {n}"
    assert result["steps"][-1] == f"{n} × 10 = {n * 10}"
    assert result["answer"] == ", ".join(
        str(n * k) for k in range(1, 11))


def test_meta_layer_yields_to_a_table_request():
    # The cleaned form of the live failure message (the tone
    # pre-pass removes "bekaar" before the fallback layer).
    cleaned = ("mujhe kuch samajh nahi aa raha, "
               "7 ka table hi bata do")
    assert meta_result(cleaned, "roman") is None
    # ...while the pure frustration ask keeps its advice card.
    meta = meta_result("mujhe kuch samajh nahi aa raha",
                       "roman")
    assert meta is not None and meta["op"] == "advice_fear"


def test_frustrated_table_request_served_end_to_end(client):
    solve(client, "Find: (i) 15% of 200 (ii) 3/5 of 45")
    data = solve(
        client,
        "mujhe kuch samajh nahi aa raha, tum bhi bekaar ho, "
        "7 ka table hi bata do")
    assert data["ok"] is True
    result = data["result"]
    # The table — not a step re-explanation, not an advice
    # card, and no scolding anywhere in the reply.
    assert result["op"] == "table"
    assert result["answer"] == \
        "7, 14, 21, 28, 35, 42, 49, 56, 63, 70"
    assert result["steps"][0] == "7 × 1 = 7"
    assert result["steps"][-1] == "7 × 10 = 70"
    assert "bekaar" not in str(result)


# ------------------------------------------------------------------ #
# Failure 3: linear-step narration matches the algebra
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question,line,answer", [
    # Wave 149 superseded the standard-form narration for
    # the simple a·x ± b = c shape: the steps now narrate
    # the move on the equation AS ASKED (subtract/add the
    # constant that is actually there). Wave 148's intent —
    # the narrated move must be the actual move, with the
    # verb's own preposition — is preserved and pinned
    # below; _linear_steps itself (the fallback for other
    # shapes) is still pinned by test_linear_steps_unit.
    ("Solve: 3x + 7 = 22", "Subtract 7 from both sides: 3·x = 15",
     "x = 5"),
    ("Solve: 3x - 7 = 8", "Add 7 to both sides: 3·x = 15",
     "x = 5"),
    ("Solve: 2x + 5 = 9", "Subtract 5 from both sides: 2·x = 4",
     "x = 2"),
    ("Solve: x + 5 = 3", "Subtract 5 from both sides: x = -2",
     "x = -2"),
    ("Solve: 4x + 9 = 5", "Subtract 9 from both sides: 4·x = -4",
     "x = -1"),
])
def test_linear_steps_narrate_the_actual_move(question, line,
                                              answer):
    result = solve_question(question)
    assert result["answer"] == answer
    assert line in result["steps"]
    for step in result["steps"]:
        assert "Add" not in step or "from both sides" not in step
        assert "Subtract" not in step or "to both sides" not in step


def test_linear_steps_unit():
    import sympy as sp
    from solver.algebra import _linear_steps
    x = sp.Symbol("x")
    steps = _linear_steps(3, -15, x)
    assert "Add 15 to both sides: 3·x = 15" in steps
    steps = _linear_steps(1, 2, x)
    assert "Subtract 2 from both sides: 1·x = -2" in steps


def test_steplang_translates_both_prepositions():
    from steplang import translate_step
    assert translate_step(
        "Add 15 to both sides: 3·x = 15", "hi") == \
        "दोनों ओर 15 जोड़िए: 3·x = 15"
    # The pre-Wave-148 string still translates (the rule now
    # accepts both prepositions).
    assert translate_step(
        "Add 15 from both sides: 3·x = 15", "hi") == \
        "दोनों ओर 15 जोड़िए: 3·x = 15"
    assert translate_step(
        "Subtract 5 from both sides: x = 2", "hi") == \
        "दोनों ओर से 5 घटाइए: x = 2"


# ------------------------------------------------------------------ #
# Failure 4: a bare view request applies to the LAST answer
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("question,want", [
    ("step by step batao", "steps"),
    ("step by step samjhao", "steps"),
    ("steps me batao", "steps"),
    ("स्टेप बाय स्टेप बताओ", "steps"),
    ("detail me batao", "detail"),
    ("detail batao", "detail"),
    ("vistar se samjhao", "detail"),
    ("vistaar se batao", "detail"),
    ("डिटेल में बताओ", "detail"),
    ("full solution batao", "detail"),
])
def test_bare_view_request_detected(question, want):
    assert parse_bare_view_request(question) == want, question


@pytest.mark.parametrize("question", [
    # Question + request in ONE message — not bare.
    "12 aur 18 ka HCF step by step batao",
    "Find the HCF of 12 and 18, step by step batao",
    "HCF detail me batao hindi me",
    "step by step samjhao HCF",
    "solve 2x + 3 = 7",
    "one step me answer do",
    "hello",
    "",
])
def test_bare_view_request_rejects_questions(question):
    assert parse_bare_view_request(question) is None, question


def test_bare_steps_request_reserves_last_answer(client):
    first = solve(client, "Find the HCF of 12 and 18")
    assert first["result"]["answer"] == "6"
    assert first["w122"]["labels"] is False
    data = solve(client, "step by step batao")
    assert data["ok"] is True
    result = data["result"]
    # The SAME stored answer, re-served — not an explanation
    # of one step, not a new-question outcome.
    assert result["answer"] == "6"
    assert result["op"] == first["result"]["op"]
    assert result["steps"] == first["result"]["steps"]
    # ...and this time the labels gate is open.
    assert data["w122"]["labels"] is True
    assert data["w122"]["step_label"] == "Step"


def test_bare_detail_request_reserves_detailed(client):
    first = solve(client, "Find the HCF of 12 and 18")
    base_steps = len(first["result"]["steps"])
    data = solve(client, "detail me batao")
    assert data["ok"] is True
    result = data["result"]
    assert result["answer"] == "6"
    assert len(result["steps"]) > base_steps
    assert data["w122"]["labels"] is True


def test_bare_view_request_without_previous_answer(client):
    # Nothing to re-serve: the normal path answers and no
    # solved answer is invented.
    data = solve(client, "step by step batao")
    result = data.get("result") or {}
    assert is_solved_result(result) is False
    assert result.get("answer") != "6"
    # Also after a not-found turn (no solved answer stored).
    solve(client, "asdf qwer zxq")
    data = solve(client, "detail me batao")
    result = data.get("result") or {}
    assert is_solved_result(result) is False


def test_question_plus_steps_request_unchanged(client):
    # The Wave-123 contrast case: question + request in one
    # message still solves fresh, with labels on.
    data = solve(client, "12 aur 18 ka HCF step by step batao")
    assert data["ok"] is True
    assert data["result"]["answer"] == "6"
    assert data["w122"]["labels"] is True
