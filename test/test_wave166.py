"""Wave 166 — "AUR ASAAN BATAO": the simpler re-serve.

Wave 162 adoption #4 (Claude's style system): when a
student says the answer was too hard — "aur asaan batao",
"samajh nahi aaya, easy me batao", "simpler please",
"आसान भाषा में बताओ" — Ganitra re-serves the SAME
verified answer in simpler words: one idea per line,
everyday words, and (only for a single whole-number
binary calculation) one daily-life example built from the
question's own numbers.

The pins below:
- the detector fires ONLY for a bare simpler request
  (Wave 148's bare discipline): a bare "samajh nahi aaya"
  stays with the Wave-96 doubt layer, "detail me batao"
  stays Wave 136/148, "step by step batao" stays Wave
  123/148, a step-targeted ask stays with doubt, and a
  question+request in one message keeps its normal path;
- the re-serve is a re-PRESENTATION: the answer field is
  byte-identical, every number in the simpler version
  already appeared in the question/answer (the Wave-132
  value invariant, ganitra_voice.extract_values), and the
  stored last solution is NOT overwritten;
- when no value-locked simplification exists, the stored
  answer itself is served, unchanged;
- the existing "simpler" follow-up CHIP keeps its
  Wave-122 semantics — this wave's phrase path is a
  separate route and the chip was not rerouted.
"""
import copy
import re

import pytest

from ganitra_voice import extract_values
from simpler import parse_bare_simple_request, \
    simplify_result

SIGNUP = {"name": "W166 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w166-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code in (200, 302)
    return c


def _solve(client, question, **extra):
    payload = {"question": question}
    payload.update(extra)
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _numbers(text):
    return set(_NUMBER_RE.findall(str(text or "")))


# ------------------------------------------------------------------ #
# The detector: bare simpler requests fire
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("message", [
    # English
    "simpler please",
    "explain more simply",
    "in simple words",
    "easy me batao",
    # Hinglish (Roman)
    "aur asaan batao",
    "aur asaan me samjhao",
    "aur asaan",
    "aur simple batao",
    "aur easy batao",
    "asaan bhasha me samjhao",
    "isko aur asaan karo",
    "thoda aur asaan batao",
    "chhoti class ke hisaab se samjhao",
    # Confusion + an explicit simpler ask (the brief's
    # named trigger): the simpler phrase claims it.
    "samajh nahi aaya, easy me batao",
    "mujhe samajh nahi aaya, aur asaan batao",
    "samajh nahi aaya asaan me batao",
    # Hindi (Devanagari)
    "आसान भाषा में बताओ",
    "सरल भाषा में बताओ",
    "और आसान बताओ",
])
def test_detector_fires_on_bare_simple_requests(message):
    assert parse_bare_simple_request(message) is True, message


@pytest.mark.parametrize("message", [
    # Bare confusion is the Wave-96 doubt layer's — no
    # simpler phrase, no fire.
    "samajh nahi aaya",
    "समझ नहीं आया",
    "mujhe samajh nahi aa raha",
    # Wave 136/148 detail asks and Wave 123/148 steps asks.
    "detail me batao",
    "vistar se samjhao",
    "HCF detail me batao",
    "step by step batao",
    # A step-targeted ask is doubt's, simpler phrase or
    # not; a steps compound keeps its pre-Wave-166 path.
    "ye step samajh nahi aaya",
    "dusra step asaan me samjhao",
    "agla step samjhao",
    "aur asaan step by step batao",
    # A question + request in ONE message is not bare.
    "12 aur 18 ka HCF asaan me batao",
    "percentage asaan me batao",
    "2 + 2 kitna hota hai",
    # "simple" alone is a topic word, not a request.
    "simple interest kya hai",
    "simple equation batao",
    # More-intent without a simpler phrase is not this
    # wave's (chips / Wave 148 own those).
    "aur batao",
    "ek aur example do",
    # Plain questions and the empty message.
    "What is 12 x 5?",
    "",
])
def test_detector_declines_everything_else(message):
    assert parse_bare_simple_request(message) is False, \
        message


# ------------------------------------------------------------------ #
# simplify_result: the value-locked re-presentation
# ------------------------------------------------------------------ #

HCF_RESULT = {
    "op": "gcd", "type": "number_theory", "answer": "6",
    "steps": ["Prime factorisation: 12 = 2^2 × 3",
              "Prime factorisation: 18 = 2 × 3^2",
              "Take the lowest power of each common prime "
              "factor.",
              "GCD = 6"],
}

BATTERY = [
    # (question, result) — fractions, decimals, units,
    # multi-step workings: the invariant must hold on all.
    ("Find the HCF of 12 and 18", HCF_RESULT),
    ("Find the area of a rectangle with length 12 cm and "
     "breadth 5 cm",
     {"op": "area", "type": "geometry", "answer": "60 cm²",
      "steps": ["Area = length × breadth = 12 × 5 = 60"]}),
    ("A train travels 60 km in 2 hours. Find its speed.",
     {"op": "speed", "type": "applied", "answer": "30 km/h",
      "steps": ["Speed = distance ÷ time = 60 km ÷ 2 hours",
                "= 30 km/h"]}),
    ("Find the simple interest on Rs 1000 at 5% per annum "
     "for 2 years",
     {"op": "simple_interest", "type": "word_problem",
      "answer": "100",
      "steps": ["Simple Interest = P × R × T / 100",
                "= 1000 × 5 × 2 / 100 = 100",
                "Total amount = P + SI = 1100"]}),
    ("Simplify: 3/4 + 1/2",
     {"op": "simplify", "type": "algebra", "answer": "5/4",
      "steps": ["Common denominator: 3/4 + 1/2 = 3/4 + 2/4",
                "Add: 3/4 + 2/4 = 5/4",
                "Therefore, the simplified form is 5/4"]}),
    ("What is 7.5 x 4?",
     {"op": "evaluate", "type": "arithmetic", "answer": "30",
      "steps": ["Evaluate: 30.0000000000000 = 30"]}),
    ("Find the mean of 2, 4, 6, 8, 10",
     {"op": "mean", "type": "statistics", "answer": "6",
      "steps": ["Add all values: 2 + 4 + 6 + 8 + 10 = 30",
                "Divide by the count (5): 30 ÷ 5 = 6"]}),
    ("Solve 3x + 7 = 22",
     {"op": "equation", "type": "algebra", "answer": "x = 5",
      "steps": ["Subtract 7 from both sides: 3·x = 15",
                "Divide both sides by 3: x = 5",
                "Solution: x = 5"]}),
    ("What is 15% of 200?",
     {"op": "percentage", "type": "arithmetic", "answer": "30",
      "steps": ["15% means 15/100 = 0.15",
                "Multiply by 200: 0.15 × 200 = 30"]}),
    ("Convert 2.5 km into metres",
     {"op": "length", "type": "units",
      "answer": "2500 metres",
      "steps": ["Convert to the base unit: 2.5 km = 2500 "
                "(base)",
                "Convert to metres: 2500 ÷ 1 = 2500"]}),
]


@pytest.mark.parametrize("question,result", BATTERY)
def test_value_preservation_battery(question, result):
    before = copy.deepcopy(result)
    out = simplify_result(result, question)
    assert result == before, "the input dict is never mutated"
    assert out is not None, question
    # The final answer is byte-identical — never touched.
    assert out["answer"] == result["answer"]
    # Every value of the original answer survives (the
    # Wave-132 invariant), and no number appears that the
    # question / answer did not already carry.
    must_keep = extract_values(
        "\n".join(result["steps"]) + "\n" + result["answer"])
    got = extract_values(
        "\n".join(out["steps"]) + "\n" + out["answer"])
    assert must_keep <= got
    allowed_numbers = _numbers(
        question + " " + " ".join(result["steps"])
        + " " + result["answer"])
    assert _numbers(" ".join(out["steps"])) <= allowed_numbers
    # It really is a different, simpler presentation.
    assert out["steps"] != result["steps"]
    assert out.get("followup") == "simpler"


def test_hcf_simplification_exact():
    out = simplify_result(copy.deepcopy(HCF_RESULT),
                          "Find the HCF of 12 and 18")
    assert out["steps"] == [
        "In simple words:",
        "Prime factors",
        "12 = 2^2 × 3",
        "Prime factors",
        "18 = 2 × 3^2",
        "Take the smallest power of each common prime "
        "factor.",
        "GCD = 6",
    ]
    assert out["answer"] == "6"


def test_area_chain_splits_in_house_style():
    out = simplify_result(
        {"op": "area", "type": "geometry", "answer": "60 cm²",
         "steps": ["Area = length × breadth = 12 × 5 = 60"]},
        "Find the area of a rectangle with length 12 cm and "
        "breadth 5 cm")
    assert out["steps"] == [
        "In simple words:",
        "Area = length × breadth",
        "= 12 × 5",
        "= 60",
    ]


def test_simpler_is_measurably_simpler():
    out = simplify_result(copy.deepcopy(HCF_RESULT),
                          "Find the HCF of 12 and 18")
    joined = " ".join(out["steps"]).lower()
    # The formal dressing is gone, the everyday word is in.
    assert "factorisation" not in joined
    assert "smallest" in joined
    # One idea per line: more, shorter lines than before.
    old_avg = sum(len(s.split())
                  for s in HCF_RESULT["steps"]) \
        / len(HCF_RESULT["steps"])
    new_body = out["steps"][1:]
    new_avg = sum(len(s.split()) for s in new_body) \
        / len(new_body)
    assert len(new_body) > len(HCF_RESULT["steps"])
    assert new_avg < old_avg


# ------------------------------------------------------------------ #
# The daily-life example line: narrow, verified, or absent
# ------------------------------------------------------------------ #

def test_example_line_for_a_single_multiplication():
    out = simplify_result(
        {"op": "evaluate", "type": "arithmetic",
         "answer": "60", "steps": ["Evaluate: 60 = 60"]},
        "What is 12 x 5?")
    assert out["steps"][-1] == (
        "Think of it like this: 12 boxes with 5 pencils in "
        "each box — 60 pencils in all.")
    # The story's numbers are the question's own numbers.
    assert _numbers(out["steps"][-1]) == {"12", "5", "60"}


def test_example_line_roman_and_devanagari():
    result = {"op": "evaluate", "type": "arithmetic",
              "answer": "60", "steps": ["Evaluate: 60 = 60"]}
    out = simplify_result(result, "12 x 5 kitna hota hai",
                          lang="hi")
    assert out["steps"][0] == "Asaan shabdon me:"
    assert out["steps"][-1] == (
        "Aise samjho: 12 dabbe, har dabbe me 5 pencils — "
        "kul 60 pencils.")
    out = simplify_result(result, "12 x 5 कितना होता है",
                          lang="hi")
    assert out["steps"][0] == "आसान शब्दों में:"
    assert "12 डिब्बे" in out["steps"][-1]
    assert "कुल 60 पेंसिल" in out["steps"][-1]


@pytest.mark.parametrize("question,result", [
    # No binary operation in the QUESTION (the 2 × 3 in a
    # factorisation step is not the question's calculation).
    ("Find the HCF of 12 and 18", HCF_RESULT),
    # The answer carries a unit — no bare-number story.
    ("Find the area of a rectangle with length 12 cm and "
     "breadth 5 cm",
     {"op": "area", "type": "geometry", "answer": "60 cm²",
      "steps": ["Area = length × breadth = 12 × 5 = 60"]}),
    # A decimal operand is not a whole-number story.
    ("What is 7.5 x 4?",
     {"op": "evaluate", "type": "arithmetic", "answer": "30",
      "steps": ["Evaluate: 30.0000000000000 = 30"]}),
    # Two operations in the question — no single story.
    ("What is 12 x 5 + 3?",
     {"op": "evaluate", "type": "arithmetic", "answer": "63",
      "steps": ["Evaluate: 12 × 5 + 3 = 63"]}),
    # The recompute must equal the served answer: a stored
    # answer the operation does not produce earns no story.
    ("What is 12 x 5?",
     {"op": "evaluate", "type": "arithmetic", "answer": "65",
      "steps": ["Evaluate: 65 = 65"]}),
])
def test_example_line_absent_when_it_cannot_be_verified(
        question, result):
    out = simplify_result(result, question)
    assert out is not None, question
    joined = " ".join(out["steps"])
    assert "Think of it like this" not in joined
    assert "Aise samjho" not in joined
    assert "ऐसे समझो" not in joined


# ------------------------------------------------------------------ #
# No simpler version -> None (api.py serves the original)
# ------------------------------------------------------------------ #

def test_none_for_proofs_and_non_solved_results():
    proof = {"op": "proof_identity", "fallback_kind": "proof",
             "answer": "True",
             "steps": ["Therefore LHS = RHS = 5 = 5"]}
    assert simplify_result(proof, "Prove the identity") \
        is None
    not_found = {"op": "not_found",
                 "fallback_kind": "not_found",
                 "answer": "Answer not found", "steps": []}
    assert simplify_result(not_found, "gibberish") is None
    assert simplify_result(None, "x") is None
    assert simplify_result({}, "x") is None


def test_none_when_nothing_can_change():
    # One short line, no label, no chain, no swap word, no
    # example shape: there is no simpler presentation, and
    # dressing the identical lines up as one would be a lie.
    result = {"op": "gcd", "type": "number_theory",
              "answer": "6", "steps": ["GCD = 6"]}
    assert simplify_result(result,
                           "Find the HCF of 12 and 18") is None


def test_none_when_the_value_gate_fails(monkeypatch):
    # The gate is wired: if the value check cannot prove
    # preservation, no simplification is served — ever.
    import simpler
    real = simpler.extract_values

    def fake(text):
        if "smallest" in str(text):
            return {"bogus-value"}
        return real(text)

    monkeypatch.setattr(simpler, "extract_values", fake)
    assert simplify_result(copy.deepcopy(HCF_RESULT),
                           "Find the HCF of 12 and 18") is None


# ------------------------------------------------------------------ #
# End to end through /api/solve
# ------------------------------------------------------------------ #

def test_simpler_reserve_end_to_end(client):
    first = _solve(client, "Find the HCF of 12 and 18")
    original_steps = first["result"]["steps"]
    assert first["result"]["answer"] == "6"
    d = _solve(client, "explain more simply")
    assert d["ok"] is True
    result = d["result"]
    assert result.get("followup") == "simpler"
    assert result["answer"] == "6"
    assert result["steps"][0] == "In simple words:"
    assert "Prime factors" in result["steps"]
    assert "factorisation" not in " ".join(result["steps"])
    # Every number served was already in the exchange.
    assert _numbers(" ".join(result["steps"])) <= _numbers(
        "Find the HCF of 12 and 18 "
        + " ".join(original_steps) + " 6")


def test_named_trigger_samajh_nahi_aaya_easy_me_batao(client):
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "samajh nahi aaya, easy me batao")
    result = d["result"]
    assert result.get("followup") == "simpler"
    # The follow-up is Hinglish, so the re-serve's framing
    # speaks Hinglish — the app's language rule (the
    # follow-up's language governs the re-serve).
    assert result["steps"][0] == "Asaan shabdon me:"
    assert result["answer"] == "6"


def test_simpler_reserve_does_not_overwrite_last_solution(
        client):
    first = _solve(client, "Find the HCF of 12 and 18")
    original_steps = first["result"]["steps"]
    _solve(client, "aur asaan batao")
    # A Wave-148 bare steps ask still re-serves the STORED
    # answer — the original steps, not the simplified copy.
    d = _solve(client, "step by step batao")
    assert d["result"]["steps"] == original_steps


def test_bare_confusion_stays_with_the_doubt_layer(client):
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "samajh nahi aaya")
    result = d["result"]
    # The doubt layer explains the last step (its card is
    # marked doubt=True) — Wave 166 does not claim a bare
    # confusion.
    assert result.get("followup") != "simpler"
    assert result.get("doubt") is True
    assert result["steps"][0] != "In simple words:"


def test_detail_and_steps_asks_keep_their_own_paths(client):
    first = _solve(client, "Find the HCF of 12 and 18")
    original_steps = first["result"]["steps"]
    d = _solve(client, "step by step batao")
    assert d["result"].get("followup") != "simpler"
    assert d["result"]["steps"] == original_steps
    d = _solve(client, "detail me batao")
    result = d["result"]
    assert result.get("followup") != "simpler"
    assert result["steps"][0] != "In simple words:"
    # The Wave-136 expansion appends to the same answer.
    assert result["steps"][:len(original_steps)] \
        == original_steps


def test_simpler_request_with_no_previous_answer(client):
    d = _solve(client, "aur asaan batao")
    result = d["result"]
    # Nothing to re-serve: the normal path answers and no
    # simpler card is fabricated.
    assert result.get("followup") != "simpler"
    assert "In simple words:" not in (
        result.get("steps") or [])


def test_question_plus_request_in_one_message_not_bare(
        client):
    d = _solve(client, "12 aur 18 ka HCF asaan me batao")
    result = d["result"]
    assert result["answer"] == "6"
    assert result.get("followup") != "simpler"
    assert "In simple words:" not in (
        result.get("steps") or [])


def test_hindi_simpler_flow(client):
    _solve(client, "12 और 18 का HCF निकालो")
    d = _solve(client, "आसान भाषा में बताओ")
    result = d["result"]
    assert result.get("followup") == "simpler"
    assert result["steps"][0] == "आसान शब्दों में:"
    assert result["answer"] == "6"


def test_hinglish_simpler_flow(client):
    _solve(client, "12 aur 18 ka HCF nikalo")
    d = _solve(client, "aur asaan batao")
    result = d["result"]
    assert result.get("followup") == "simpler"
    assert result["steps"][0] == "Asaan shabdon me:"
    assert result["answer"] == "6"


def test_chip_simpler_keeps_its_wave122_semantics(client):
    # The follow-up CHIP was not rerouted through Wave
    # 166: its note is the chip's own, exactly as Wave 122
    # pinned it.
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "Explain more simply",
               followup="simpler",
               context_question="Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["followup_note"] == "A simpler way:"
    assert d["result"].get("followup") == "simpler"
