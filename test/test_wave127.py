"""Wave 127 — conversation context ("baat-cheet wali samajh").

After an answer, a student refers back to earlier turns of the
SAME chat: "uska answer batao", "usi ka ek aur example do",
"dusra tarika batao", "ye wala phir se samjhao". This wave
resolves those references from the chat's own solved-turn log
instead of treating them as new questions.

Proven here, through the real chat path (/api/solve):
- answer re-show is BYTE-IDENTICAL to the answer first given
  (latest turn by default, a named topic's turn on request);
- "ek aur example" serves a NEW solver-verified example on
  the same question (one number nudged, different answer);
- "dusra tarika" serves the Wave 12 alternate method, and a
  question with honestly one method gets an honest line;
- "phir se samjhao" re-serves the same answer's steps with a
  simpler-words opener;
- step references still belong to Wave 96 doubt — the context
  layer never hijacks them, and a context reply never
  overwrites the last solution doubt points at;
- ambiguity ("pehle wale ka..." into two different earlier
  topics) gets ONE clarifying question, never a guess;
- per-chat isolation: two chat ids in one session keep
  separate turn logs — references never cross;
- veto battery: fresh questions that merely contain
  reference-like words (digits, a topic named without a
  possessive, "uska" inside a longer message) are NEVER
  claimed and solve normally.
"""
import pytest

from context_ref import parse_context_ref
from solver.router import solve_question

HCF_Q = "Find the HCF of 12 and 18"
LCM_Q = "Find the LCM of 4 and 6"
PCT_Q = "What is 15% of 240?"
EQ_Q = "solve 3x + 5 = 20"
PRIME_Q = "Is 29 a prime number?"

CONTEXT_OPS = {"show_answer", "alt_method", "no_alt_method",
               "reexplain", "clarify"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def solve(client, question, chat_id=None):
    body = {"question": question}
    if chat_id is not None:
        body["chat_id"] = chat_id
    return client.post("/api/solve", json=body).get_json()


def ask(client, question, chat_id=None):
    data = solve(client, question, chat_id=chat_id)
    assert data["ok"] is True, (question, data)
    return data["result"]


# --- 1. Answer re-show ------------------------------------------

def test_answer_reshow_latest_byte_identical(client):
    first = ask(client, HCF_Q)
    assert first["answer"] == "6"
    second = ask(client, LCM_Q)
    assert second["answer"] == "12"
    result = ask(client, "uska answer batao")
    assert result["op"] == "show_answer"
    assert result["answer"] == second["answer"]


def test_answer_reshow_named_topic_turn(client):
    ask(client, HCF_Q)
    ask(client, LCM_Q)
    result = ask(client, "HCF wale ka answer batao")
    assert result["op"] == "show_answer"
    assert result["answer"] == "6"
    assert result["context_question"] == HCF_Q


def test_answer_reshow_hindi(client):
    first = ask(client, "12 aur 18 ka HCF nikalo")
    assert first["answer"] == "6"
    result = ask(client, "उसका उत्तर बताओ")
    assert result["op"] == "show_answer"
    assert result["answer"] == "6"


def test_reference_with_no_turns_falls_through(client):
    data = solve(client, "uska answer batao")
    result = data.get("result") or {}
    assert result.get("op") not in CONTEXT_OPS


# --- 2. Another example ------------------------------------------

def test_example_same_question_new_answer(client):
    ask(client, HCF_Q)
    result = ask(client, "usi ka ek aur example do")
    assert result.get("example_of") == HCF_Q
    new_q = result["example_question"]
    assert new_q != HCF_Q
    # The served example is solver-verified: re-solving its
    # question reproduces its answer, and the answer is new.
    assert solve_question(new_q)["answer"] == result["answer"]
    assert result["answer"] != "6"


def test_example_of_older_turn_by_topic(client):
    ask(client, HCF_Q)
    ask(client, LCM_Q)
    result = ask(client, "HCF wale ka ek aur example do")
    assert result.get("example_of") == HCF_Q
    assert result["answer"] != "6"


def test_example_not_regenerable_falls_through(client):
    # A concept turn's question carries no number to nudge.
    ask(client, "HCF kya hota hai")
    data = solve(client, "usi ka ek aur example do")
    result = data.get("result") or {}
    assert result.get("example_of") is None


# --- 3. Another method -------------------------------------------

def test_alt_method_served(client):
    ask(client, HCF_Q)
    result = ask(client, "dusra tarika batao")
    assert result["op"] == "alt_method"
    assert result["answer"] == "6"  # agrees with the primary
    assert result["steps"]


def test_alt_method_honest_line_when_only_one(client):
    first = ask(client, PRIME_Q)
    result = ask(client, "iska dusra tarika batao")
    assert result["op"] == "no_alt_method"
    assert result["answer"] == first["answer"]
    assert result["steps"]  # the honest line itself


# --- 4. Re-explain ------------------------------------------------

def test_reexplain_last_turn(client):
    first = ask(client, EQ_Q)
    result = ask(client, "ye wala phir se samjhao")
    assert result["op"] == "reexplain"
    assert result["answer"] == first["answer"] == "x = 5"
    joined = " ".join(result["steps"])
    assert "3x + 5 = 20" in joined or "3·x" in joined \
        or "x = 5" in joined


def test_reexplain_older_turn_recovers_by_resolve(client):
    first = ask(client, EQ_Q)
    ask(client, HCF_Q)
    result = ask(client, "equation wale ko phir se samjhao")
    # Topic-named re-explain of the older turn: recovered only
    # because the solver reproduces the stored answer exactly.
    assert result["op"] in ("reexplain", "show_answer")
    assert result["answer"] == first["answer"]


# --- 5. Wave 96 doubt keeps its territory -------------------------

def test_step_references_still_go_to_doubt(client):
    ask(client, EQ_Q)
    for msg in ("dusra step samjhao", "step 2 samajh nahi aaya",
                "pichla step samjhao"):
        result = ask(client, msg)
        assert result["op"] == "explain_step", msg


def test_context_reply_does_not_overwrite_last_solution(client):
    ask(client, EQ_Q)
    ask(client, "uska answer batao")  # context reply in between
    result = ask(client, "dusra step samjhao")
    assert result["op"] == "explain_step"
    assert result["step_number"] == 2


def test_context_turns_are_not_themselves_recorded(client):
    ask(client, HCF_Q)
    ask(client, "uska answer batao")
    result = ask(client, "usi ka ek aur example do")
    # The example still points at the real solve, not at the
    # re-show turn in between.
    assert result.get("example_of") == HCF_Q


# --- 6. Ambiguity: one clarifying question ------------------------

def test_ambiguous_pehle_wala_asks_one_question(client):
    ask(client, HCF_Q)
    ask(client, LCM_Q)
    ask(client, PCT_Q)
    result = ask(client, "pehle wale ka answer batao")
    assert result["op"] == "clarify"
    assert "HCF" in result["answer"]
    assert "LCM" in result["answer"]


def test_pehle_wala_single_earlier_turn_resolves(client):
    ask(client, HCF_Q)
    ask(client, LCM_Q)
    result = ask(client, "pichle wale ka answer batao")
    assert result["op"] == "show_answer"
    assert result["answer"] == "6"


# --- 7. Per-chat isolation ----------------------------------------

def test_references_never_cross_chats(client):
    ask(client, HCF_Q, chat_id=1)
    ask(client, LCM_Q, chat_id=2)
    in_two = ask(client, "uska answer batao", chat_id=2)
    assert in_two["op"] == "show_answer"
    assert in_two["answer"] == "12"
    in_one = ask(client, "uska answer batao", chat_id=1)
    assert in_one["op"] == "show_answer"
    assert in_one["answer"] == "6"
    # A topic discussed only in chat 1 is unknown in chat 2.
    data = solve(client, "HCF wale ka answer batao", chat_id=2)
    result = data.get("result") or {}
    assert result.get("op") != "show_answer"


# --- 8. Veto battery ----------------------------------------------

VETO_CASES = [
    # A fresh solve that merely ENDS in "answer batao" — the
    # digits make it a self-contained new question.
    ("12 aur 18 ke HCF ka answer batao", "gcd", "6"),
    # A fresh percentage ask containing "answer".
    ("What is the answer of 15% of 240?", "percentage", "36"),
]


@pytest.mark.parametrize("msg,op,answer", VETO_CASES)
def test_veto_fresh_solves_unaffected(client, msg, op, answer):
    ask(client, HCF_Q)  # a previous turn exists to point at
    result = ask(client, msg)
    assert result.get("op") == op
    assert result.get("answer") == answer
    assert not result.get("context")


def test_veto_concept_ask_with_example_word(client):
    ask(client, HCF_Q)
    result = ask(client, "example ke saath HCF samjhao")
    assert result.get("fallback_kind") == "concept"
    assert not result.get("context")


def test_veto_topic_named_without_reference(client):
    ask(client, LCM_Q)
    result = ask(client, "HCF ka answer batao")
    # No pronoun, no possessive — a fresh ask about HCF, never
    # a reference to the LCM turn (and never its answer).
    assert result.get("op") != "show_answer"
    assert result.get("answer") != "12"


@pytest.mark.parametrize("msg", [
    "uska answer batao kal wala",       # leftover payload word
    "uska answer batao aur LCM bhi",    # second topic, no ref
    "Ram ne uska beta ko 50 rupaye diye",  # narrative "uska"
    "dusra example do fresh wala naya",    # leftover payload
])
def test_veto_leftover_payload_never_claimed(client, msg):
    ask(client, HCF_Q)
    data = solve(client, msg)
    result = data.get("result") or {}
    assert result.get("op") not in CONTEXT_OPS
    assert not result.get("context")


# --- 9. Detector unit battery --------------------------------------

@pytest.mark.parametrize("msg,intent", [
    ("uska answer batao", "answer"),
    ("uska jawab batao", "answer"),
    ("उसका उत्तर बताओ", "answer"),
    ("HCF wale ka answer batao", "answer"),
    ("pichle wale ka answer batao", "answer"),
    ("usi ka ek aur example do", "example"),
    ("iska dusra example do", "example"),
    ("ek aur example do", "example"),
    ("dusra tarika batao", "method"),
    ("iska koi aur method hai", None),  # "hai" alone: no verb
    ("ye wala phir se samjhao", "reexplain"),
    ("dobara samjhao", "reexplain"),
    ("aur aasan me samjhao", "reexplain"),
])
def test_parse_positives(msg, intent):
    ref = parse_context_ref(msg)
    if intent is None:
        assert ref is None
    else:
        assert ref is not None and ref["intent"] == intent, msg


@pytest.mark.parametrize("msg", [
    "Find the HCF of 12 and 18",         # digits: fresh solve
    "12 aur 18 ke HCF ka answer batao",  # digits: fresh solve
    "dusra step samjhao",                # Wave 96 territory
    "step 2 samajh nahi aaya",           # Wave 96 territory
    "pichla step samjhao",               # Wave 96 territory
    "example ke saath HCF samjhao",      # fresh concept ask
    "HCF kya hota hai",                  # fresh concept ask
    "HCF ka answer batao",               # topic, no reference
    "What is the answer of 15% of 240?",  # operator + digits
    "Ram ne uska paisa rakha",           # narrative, no intent
    "uska answer batao kal wala",        # leftover payload
    "solve 3x + 5 = 20",                 # fresh equation
    "ye step samjhao",                   # Wave 96 territory
])
def test_parse_negatives(msg):
    assert parse_context_ref(msg) is None, msg
