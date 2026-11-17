"""Wave 129 — "meri galti kahan hai", the natural way.

Wave 85 built the step checker behind a written convention
(question + "my solution:" marker + working). Students do not
write that way — they write like they talk. Wave 129 adds the
natural chat layer ON TOP of the unchanged checker:

- same-message flow: an intent phrase ("maine aise kiya hai,
  galti kahan hai?", "check my solution", "मेरी गलती बताओ")
  anywhere in the message — its own line, glued to the
  question, first or last — with the steps in the same
  message;
- two-turn flow: intent without steps gets ONE short prompt
  ("apne steps bhejo — ek line me ek step"), the question is
  parked per chat (session["galti_pending"], Wave 96-style),
  and the next message is read as the steps; any other next
  message quietly expires the flow;
- steps sent alone for the question just solved in this chat
  are checked against session["last_question"].

The verdicts themselves are Wave 85's, byte-for-byte: first
wrong step quoted + corrected, all-correct praised, a
different-but-valid method never flagged, out-of-scope types
get the honest line plus the solved answer. A fresh question
that merely contains "check" is vetoed — it solves normally.
"""
import pytest

from api import _solve_friendly
from galti import natural_check_result, split_intent_message

LINEAR = "Solve 2x + 3 = 11"
QUAD = "Solve x^2 - 5x + 6 = 0"
DISCOUNT = ("A shirt costs Rs 800 and is sold at 15% discount. "
            "What is the selling price?")


def _steps(result):
    return "\n".join(str(s) for s in result.get("steps") or [])


def _check(msg):
    r = _solve_friendly(msg)
    assert r.get("type") == "step_check", r
    assert r.get("step_check") is True
    return r


# --- the split -------------------------------------------------

def test_wave129_split_layouts():
    mid = split_intent_message(
        f"{LINEAR}\nmaine aise kiya hai, galti kahan hai?\n"
        "2x = 11 - 3\n2x = 9\nx = 4.5")
    assert mid["question"] == LINEAR
    assert mid["steps"] == ["2x = 11 - 3", "2x = 9", "x = 4.5"]

    first = split_intent_message(
        f"meri galti batao\n{QUAD}\n(x - 2)(x - 3) = 0\n"
        "x = 2, x = 4")
    assert first["question"] == QUAD
    assert first["steps"] == ["(x - 2)(x - 3) = 0", "x = 2, x = 4"]

    last = split_intent_message(
        f"{LINEAR}\n2x = 11 - 3\n2x = 9\nx = 4.5\ngalti kahan hai?")
    assert last["question"] == LINEAR
    assert last["steps"] == ["2x = 11 - 3", "2x = 9", "x = 4.5"]

    alone = split_intent_message(
        "maine aise kiya hai:\n2x = 11 - 3\n2x = 9\nx = 4.5")
    assert alone["steps_only"] is True
    assert alone["steps"] == ["2x = 11 - 3", "2x = 9", "x = 4.5"]

    bare = split_intent_message("mera solution check karo")
    assert bare["question"] is None and bare["steps"] is None


def test_wave129_split_vetoes():
    # No self-reference, no mistake ask -> no intent at all.
    assert split_intent_message(
        "check karo 15% of 240 kitna hoga") is None
    assert split_intent_message(
        "how to check if 29 is a prime number") is None
    assert split_intent_message("What is 15% of 800?") is None
    assert split_intent_message(LINEAR) is None


# --- same-message flow ------------------------------------------

def test_wave129_same_message_middle_intent():
    r = _check(f"{LINEAR}\nmaine aise kiya hai, galti kahan hai?\n"
               "2x = 11 - 3\n2x = 9\nx = 4.5")
    s = _steps(r)
    assert r["answer"] == "x = 4"
    assert "Step 1 tak tumhare saare step sahi hai" in s
    assert "Pehli galti step 2 par hai" in s
    assert '"2x = 9"' in s
    assert "2·x = 8" in s


def test_wave129_same_message_intent_first_line():
    r = _check(f"meri galti batao\n{QUAD}\n"
               "(x - 2)(x - 3) = 0\nx = 2, x = 4")
    s = _steps(r)
    # Hinglish intent -> Hinglish verdict.
    assert "Pehli galti step 2 par hai" in s
    assert '"x = 2, x = 4"' in s


def test_wave129_same_message_intent_at_end():
    r = _check(f"{LINEAR}\n2x = 11 - 3\n2x = 9\nx = 4.5\n"
               "galti kahan hai?")
    s = _steps(r)
    assert "Pehli galti step 2 par hai" in s
    assert "Ye step aisa hona chahiye tha: 2·x = 8" in s


def test_wave129_same_message_glued_intent_and_chain():
    r = _check(f"{LINEAR}, check my solution: 2x = 8 -> x = 4")
    assert "Every step is correct" in _steps(r)


# --- seeded errors ------------------------------------------------

def test_wave129_seeded_sign_error_is_first_step():
    # 3x - 5 = 10 -> the student moves -5 across WITHOUT
    # flipping its sign: "3x = 10 - 5".
    r = _check("Solve 3x - 5 = 10\nmera solution check karo\n"
               "3x = 10 - 5\n3x = 5\nx = 5/3")
    s = _steps(r)
    assert "Pehla step hi galat ho gaya hai" in s
    assert '"3x = 10 - 5"' in s
    assert "Ye step aisa hona chahiye tha: 3·x = 15" in s


def test_wave129_seeded_arithmetic_slip():
    r = _check(f"{DISCOUNT}\ncheck my solution\n"
               "Discount = 15% of 800 = 120\n"
               "Selling price = 800 - 120 = 700")
    s = _steps(r)
    assert "Step 2 is where it first goes wrong" in s
    assert "800 - 120 = 680" in s


def test_wave129_seeded_wrong_formula_step():
    # Expanding 3(x + 2) as 3x + 2 — the bracket is not
    # multiplied through.
    r = _check("Simplify 3(x + 2) + 2x\nmera hal check karo\n"
               "3x + 2 + 2x\n5x + 2")
    s = _steps(r)
    assert "Pehla step hi galat ho gaya hai" in s
    assert '"3x + 2 + 2x"' in s


# --- honest verdicts ----------------------------------------------

def test_wave129_all_correct_is_praised_not_flagged():
    r = _check(f"{LINEAR}\nye sahi hai kya?\n"
               "2x = 11 - 3\n2x = 8\nx = 4")
    assert "Har step sahi hai" in _steps(r)


def test_wave129_different_valid_method_is_not_flagged():
    r = _check(f"{QUAD}\ncheck my working\n"
               "(x - 2)(x - 3) = 0\n"
               "x - 2 = 0 or x - 3 = 0\n"
               "x = 2, x = 3")
    s = _steps(r)
    assert "Every step is correct" in s
    assert "different from mine" in s


def test_wave129_out_of_scope_gets_honest_line_plus_solution():
    r = _check("Find the value of sin 30 degrees\n"
               "meri galti batao\nsin 30 = 1/2\nanswer = 0.5")
    s = _steps(r)
    assert r["answer"] == "1/2"
    # The honest out-of-scope line, in the student's language.
    assert "Is type ke sawal ke steps main abhi check nahi" in s
    assert "standard values" in s  # the correct solution follows


def test_wave129_marker_convention_still_works():
    r = _check(f"{LINEAR}\nmy solution:\n2x = 8\nx = 4")
    assert "Every step is correct" in _steps(r)


# --- vetoes through the solve path ---------------------------------

def test_wave129_veto_check_karo_percentage_solves_normally():
    r = _solve_friendly("check karo 15% of 240 kitna hoga")
    assert r.get("type") != "step_check"
    assert r["answer"] == "36"


def test_wave129_veto_how_to_check_is_not_an_intent():
    assert natural_check_result(
        "how to check if 29 is a prime number") is None
    r = _solve_friendly("how to check if 29 is a prime number")
    assert r.get("type") != "step_check"


# --- two-turn flow through the real chat path -----------------------

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


def _ask_result(data):
    assert data["ok"] is True
    result = data["result"]
    assert result["op"] == "check_steps_ask"
    assert result["plain"] is True
    assert data["explanation"] == "" and data["advice"] == ""
    return result


def test_wave129_two_turn_intent_with_question_then_steps(client):
    data = solve(client, f"{LINEAR}, maine aise kiya hai, "
                         "galti kahan hai?")
    result = _ask_result(data)
    assert "steps bhejo" in result["steps"][0]

    data = solve(client, "2x = 11 - 3\n2x = 9\nx = 4.5")
    result = data["result"]
    assert result["type"] == "step_check"
    s = "\n".join(result["steps"])
    # The verdict speaks the intent message's language
    # (Hinglish), even though the steps are bare maths.
    assert "Pehli galti step 2 par hai" in s
    assert "2·x = 8" in s


def test_wave129_two_turn_bare_intent_then_question_and_steps(
        client):
    data = solve(client, "mera solution check karo")
    result = _ask_result(data)
    assert "Sawal aur apne steps bhejo" in result["steps"][0]

    data = solve(client, f"{LINEAR}\n2x = 11 - 3\n2x = 8\nx = 4")
    result = data["result"]
    assert result["type"] == "step_check"
    assert "Har step sahi hai" in "\n".join(result["steps"])


def test_wave129_two_turn_english(client):
    data = solve(client, "check my solution")
    result = _ask_result(data)
    assert "Send the question and your steps" in \
        result["steps"][0]

    data = solve(client, f"{LINEAR}\n2x = 11 - 3\n2x = 9\nx = 4.5")
    s = "\n".join(data["result"]["steps"])
    assert "Step 2 is where it first goes wrong" in s


def test_wave129_two_turn_hindi(client):
    data = solve(client, "2x + 3 = 11 हल करो, मेरी गलती कहाँ है?")
    result = _ask_result(data)
    assert "steps भेजो" in result["steps"][0]

    data = solve(client, "2x = 11 - 3\n2x = 10\nx = 5")
    s = "\n".join(data["result"]["steps"])
    assert "पहली गलती चरण 2 पर है" in s
    assert "2·x = 8" in s


def test_wave129_two_turn_out_of_scope(client):
    data = solve(client, "Find the value of sin 30 degrees, "
                         "meri galti batao")
    _ask_result(data)
    data = solve(client, "sin 30 = 1/2\nanswer = 0.5")
    s = "\n".join(data["result"]["steps"])
    # The honest line, in the intent message's language.
    assert "Is type ke sawal ke steps main abhi check nahi" in s


def test_wave129_pending_expires_on_a_fresh_question(client):
    _ask_result(solve(client, "check my solution"))
    data = solve(client, "What is 15% of 800?")
    assert data["result"]["answer"] == "120"
    assert data["result"].get("type") != "step_check"
    # The pending state is gone: bare steps are NOT read as a
    # solution to check any more.
    data = solve(client, "2x = 11 - 3\n2x = 8\nx = 4")
    assert data["result"].get("type") != "step_check"


def test_wave129_steps_only_for_the_last_question(client):
    data = solve(client, "Solve 3x - 5 = 10")
    assert data["result"]["answer"] == "x = 5"
    data = solve(client, "maine aise kiya hai:\n"
                         "3x = 10 - 5\n3x = 5\nx = 5/3")
    result = data["result"]
    assert result["type"] == "step_check"
    s = "\n".join(result["steps"])
    # Hinglish verdict — the intent phrase set the flavour.
    assert "Pehla step hi galat ho gaya hai" in s
    assert "3·x = 15" in s
