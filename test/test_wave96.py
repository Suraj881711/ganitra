"""Wave 96 — doubt follow-up ("ye step samjhao").

After an answer, the student can ask about THAT answer in the
same chat ("dusra step samjhao", "step 2 samajh nahi aaya",
"why did you divide by 3", "ye wala step phir se samjhao") and
gets JUST that step re-explained more simply — what was done,
why, with a tiny example — in their own language.

Proven here, through the real chat path (/api/solve):
- two-turn conversations: solve -> follow-up variants -> the
  referenced step of the FIRST answer is explained (explicit
  number, ordinal, operation hint, unspecified -> last step,
  next-step chaining);
- steps are recovered from the stored result payload — the same
  payload the client persists in the chats DB (round-trip via
  /api/chats proves a reopened chat keeps recoverable steps);
- no previous answer / out-of-range step -> NO invented step:
  the message falls through to the normal path and the app's
  honest one-liner;
- veto battery: fresh questions that merely start with
  "samjhao"/"explain" are NEVER mistaken for follow-ups, even
  right after a solve;
- gibberish still gets exactly the Wave 67 one-liner.
"""
import pytest

from doubt import (build_doubt_response, eligible_result,
                   parse_followup, working_steps)

BASE_Q = "solve 3x + 5 = 20"
# The solver's own steps for BASE_Q (verified against the live
# solver): the last line merely restates the answer, so the
# working steps a student counts are the first two.
# Wave 149: BASE_Q is the simple a·x + b = c shape, whose
# primary steps are now school-style — move the constant,
# then divide — so the divide step is step 2 (it was step 3
# under the old standard-form narration, whose extra first
# line "Bring all terms to one side: 3·x + -15 = 0" is gone).
STEP1_BODY = "3·x = 15"
STEP2_BODY = "x = 5"

SIGNUP = {"name": "W96 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w96-pass"}


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


def solve_base(client):
    data = solve(client, BASE_Q)
    assert data["ok"] is True
    assert data["result"]["answer"] == "x = 5"
    return data


def assert_explains(data, body, step_number=None):
    assert data["ok"] is True
    result = data["result"]
    assert result["op"] == "explain_step"
    assert result["type"] == "doubt"
    assert result["answer"] == body
    if step_number is not None:
        assert result["step_number"] == step_number
    joined = " ".join(result["steps"])
    assert body in joined  # the quoted step itself is shown
    return result


# --- 1. Two-turn conversations through the chat path -----------

def test_ordinal_step_followup(client):
    solve_base(client)
    data = solve(client, "pehla step samjhao")
    result = assert_explains(data, STEP1_BODY, step_number=1)
    # The explanation offers the next step in one line.
    assert "agla step samjhao" in " ".join(result["steps"])


def test_numbered_step_confusion_followup(client):
    solve_base(client)
    data = solve(client, "step 2 samajh nahi aaya")
    assert_explains(data, STEP2_BODY, step_number=2)


def test_why_did_you_divide_finds_the_divide_step(client):
    solve_base(client)
    data = solve(client, "why did you divide by 3")
    result = assert_explains(data, STEP2_BODY, step_number=2)
    joined = " ".join(result["steps"]).lower()
    assert "divide" in joined or "bhaag" in joined


def test_unspecified_followup_explains_last_step(client):
    solve_base(client)
    data = solve(client, "ye step samajh nahi aaya")
    assert_explains(data, STEP2_BODY, step_number=2)


def test_again_followup_explains_last_step(client):
    solve_base(client)
    data = solve(client, "ye wala step phir se samjhao")
    assert_explains(data, STEP2_BODY, step_number=2)


def test_bare_samjhao_with_context_explains_last_step(client):
    solve_base(client)
    data = solve(client, "samjhao")
    assert_explains(data, STEP2_BODY, step_number=2)


def test_explain_this_step_english(client):
    solve_base(client)
    data = solve(client, "explain this step")
    result = assert_explains(data, STEP2_BODY, step_number=2)
    assert result["steps"][0].startswith("Step 2:")


def test_hindi_followup_gets_hindi_explanation(client):
    solve_base(client)
    data = solve(client, "दूसरा चरण समझाओ")
    result = assert_explains(data, STEP2_BODY, step_number=2)
    assert result["steps"][0].startswith("चरण 2:")


def test_next_step_chaining(client):
    solve_base(client)
    assert_explains(solve(client, "pehla step samjhao"),
                    STEP1_BODY, step_number=1)
    # "agla step" continues from the step just explained, and
    # still points at the ORIGINAL answer's steps.
    assert_explains(solve(client, "agla step samjhao"),
                    STEP2_BODY, step_number=2)


def test_followup_does_not_replace_the_answer(client):
    solve_base(client)
    assert_explains(solve(client, "step 1 samjhao"),
                    STEP1_BODY, step_number=1)
    # A second, different follow-up still refers to the same
    # original solution (the doubt turn is not a new "answer").
    assert_explains(solve(client, "step 2 samjhao"),
                    STEP2_BODY, step_number=2)


# --- 2. No context / impossible reference -> no invented step --

def test_followup_without_previous_answer_invents_nothing(client):
    # Very first message of a fresh chat: nothing to point at.
    data = solve(client, "ye step samajh nahi aaya")
    result = data.get("result") or {}
    assert result.get("op") != "explain_step"
    assert "3·x" not in str(data)


def test_out_of_range_step_invents_nothing(client):
    solve_base(client)
    data = solve(client, "step 9 samjhao")
    result = data.get("result") or {}
    assert result.get("op") != "explain_step"


def test_missing_operation_invents_nothing(client):
    solve_base(client)
    # No step of 3x + 5 = 20 multiplies by 7.
    data = solve(client, "why did you multiply by 7")
    result = data.get("result") or {}
    assert result.get("op") != "explain_step"


def test_followup_after_not_found_invents_nothing(client):
    data = solve(client, "asdf qwer")
    assert (data.get("result") or {}).get("fallback_kind") \
        == "not_found"
    data = solve(client, "ye step samajh nahi aaya")
    result = data.get("result") or {}
    assert result.get("op") != "explain_step"


# --- 3. Veto battery: fresh questions are never follow-ups -----

@pytest.mark.parametrize("question", [
    "samjhao HCF kya hota hai",       # concept ask, not a doubt
    "HCF samjhao",                    # topic name = new payload
    "explain the pythagorean theorem",
    "what is step deviation method",  # 'step' inside a topic name
    "step by step samjhao HCF",
    "samjhao photosynthesis kya hai",
    "solve 2x + 3 = 7",               # a brand-new question
    "2 + 2 = ?",
])
def test_veto_battery_after_a_solve(client, question):
    solve_base(client)
    data = solve(client, question)
    result = data.get("result") or {}
    assert result.get("op") != "explain_step", question


def test_vetoed_concept_question_still_answers_the_concept(client):
    solve_base(client)
    data = solve(client, "samjhao HCF kya hota hai")
    result = data.get("result") or {}
    assert result.get("op") != "explain_step"
    assert "HCF" in str(result.get("answer", ""))


def test_new_question_after_followup_solves_normally(client):
    solve_base(client)
    assert_explains(solve(client, "dusra step samjhao"),
                    STEP2_BODY, step_number=2)
    data = solve(client, "solve 2x + 3 = 7")
    assert data["ok"] is True
    assert data["result"]["answer"] == "x = 2"
    # ...and follow-ups now point at the NEW answer (2 working
    # steps + the restated-answer line).
    data = solve(client, "pehla step samjhao")
    assert (data.get("result") or {}).get("op") == "explain_step"


# --- 4. Gibberish: the one-line fallback is unchanged ----------

def test_gibberish_still_one_line(client):
    data = solve(client, "If tu gfuf")
    result = data.get("result") or {}
    if result:
        assert result.get("fallback_kind") == "not_found"
        assert result.get("answer") == "Answer not found."
        assert result.get("steps") == []


# --- 5. DB persistence: steps survive in the saved chat --------

def test_steps_recoverable_from_saved_chat_payload(client):
    client.post("/signup", data=SIGNUP)
    chat = client.post("/api/chats").get_json()["chat"]
    first = solve_base(client)
    messages = [
        {"role": "user", "text": BASE_Q},
        {"role": "bot", "data": first},
    ]
    saved = client.put(f"/api/chats/{chat['id']}",
                       json={"messages": messages})
    assert saved.get_json()["ok"] is True
    # Reopen the chat exactly as the client would.
    reopened = client.get(f"/api/chats/{chat['id']}").get_json()
    bot = [m for m in reopened["chat"]["messages"]
           if m.get("role") == "bot"][0]
    stored_result = bot["data"]["result"]
    # The stored payload still carries the steps structurally,
    # and the Wave 96 recovery works on it unchanged.
    assert eligible_result(stored_result)
    steps = working_steps(stored_result)
    assert len(steps) == 2
    assert STEP2_BODY in steps[1]
    built = build_doubt_response(
        "dusra step samjhao", parse_followup("dusra step samjhao"),
        stored_result, lang="hi")
    assert built is not None
    result, index = built
    assert index == 1 and result["answer"] == STEP2_BODY
    # And the live session still answers the follow-up too.
    assert_explains(solve(client, "dusra step samjhao"),
                    STEP2_BODY, step_number=2)


# --- 6. Detector unit battery ----------------------------------

@pytest.mark.parametrize("question", [
    "ye step samajh nahi aaya", "dusra step samjhao",
    "step 2 samajh nahi aaya", "why did you divide by 3",
    "ye kaise aaya", "samjhao", "explain this step",
    "ye wala step phir se samjhao", "samajh nahi aaya",
    "दूसरा चरण समझाओ", "तीसरा चरण समझ नहीं आया",
    "agla step samjhao", "aakhri step samjhao",
    "step 3 samjhao", "pehla step samajh nahi aaya",
    "3 se bhaag kyun diya", "explain step 1",
])
def test_parse_followup_positive(question):
    assert parse_followup(question) is not None, question


@pytest.mark.parametrize("question", [
    "samjhao HCF kya hota hai", "HCF samjhao",
    "explain the pythagorean theorem",
    "what is step deviation method", "step by step samjhao HCF",
    "solve 2x + 3 = 7", "2 + 2 = ?", "hello bro",
    "find the area of a circle with radius 7",
    "photosynthesis samjhao", "what is a prime number",
    "train 360 km jati hai 40 km/h se kitna time lagega",
])
def test_parse_followup_vetoes(question):
    assert parse_followup(question) is None, question
