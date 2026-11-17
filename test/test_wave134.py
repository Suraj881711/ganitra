"""Wave 134: the deep-solve stage (deep_solve.py) — Ganitra
tries HARDER to solve the question itself before giving up.

Suraj's order (17 Nov 2026): Ganitra must have its OWN
solve power — when the AI legs fail or an AI answer is
wrong, Ganitra should solve the question itself instead of
serving the AI's numbers or collapsing to not-found.

Proven here:

- a rescue battery of questions the STOCK chain (AI legs
  disabled) ends at the concept card / not-found line for,
  each now self-solved through the real chain with the
  expected value and a deep_solve mechanism tag;
- the near-miss guards: variant shapes that would answer a
  DIFFERENT question (the difference-of-percent-ofs trap,
  the multi-leg distance trap, the Hindi verb "do", the
  English idiom "one of") never produce a wrong rescue;
- method transfer against stub AI results: a right method
  with an arithmetic slip is recomputed to Ganitra's OWN
  correct answer; a wrong method is never rescued; vague
  steps rescue nothing; an agreeing recomputation leaves
  the AI answer byte-identical;
- byte-identical regression pins: questions the stock path
  already solves return dicts identical to the deep stage
  switched off, and a correct AI answer is served
  byte-identical with the stage on and off;
- budgets: the stage is bounded (MAX_SOLVES / MAX_SECONDS)
  and the kill switch GANITRA_DEEP_SOLVE=0 restores the
  exact stock behaviour;
- telemetry: rescues land in deep_solve_log (question text
  + mechanism only — no identity field of any kind).
"""
import time

import pytest

import deep_solve
import fallback
from deep_solve import deep_solve as run_deep
from fallback import fallback_answer


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w134.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_DEEP_SOLVE", raising=False)
    monkeypatch.delenv("GANITRA_DEEP_SOLVE_LOG", raising=False)
    return path


@pytest.fixture()
def no_ai(monkeypatch):
    """The AI chain unavailable (the Wave 117 pattern):
    every leg returns None, so the chain's own outcome
    stands — this is the 'AI failed' world the deep stage
    exists for."""
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


def _ai(answer, steps, kind="gemini"):
    return {"type": "Ganitra", "op": kind, "answer": answer,
            "steps": steps, "fallback": True,
            "fallback_kind": kind, "ai_generated": True}


# ---------------------------------------------------------------------------
# The rescue battery: stock misses, deep self-solves
# ---------------------------------------------------------------------------

RESCUES = [
    # (question, expected substring of the served answer,
    #  mechanism prefix)
    ("three x plus five equals twenty", "x = 5", "equation"),
    ("Solve for x: two x plus three is equal to eleven",
     "x = 4", "equation"),
    ("What is the sum of forty five and thirty six?", "81",
     "numbers"),
    ("What is fifteen multiplied by six?", "90", "numbers"),
    ("What is twenty five percent of two hundred forty?",
     "60", "numbers"),
    ("What is half of two hundred forty?", "120", "numbers"),
    ("How many minutes are there in two hours?", "120",
     "numbers"),
    ("240 ka pachis pratishat kitna hoga?", "60", "numbers"),
    ("do sau chalis ka pachis pratishat kitna hoga", "60",
     "numbers"),
    ("one lakh ka ten percent kitna hoga", "10000",
     "numbers"),
    ("A shopkeeper bought a cycle for rupees four thousand "
     "and sold it for rupees four thousand six hundred. "
     "Find his profit percent.", "15", "numbers"),
    ("Find the simple interest on rupees five thousand at "
     "six percent per annum for three years", "900",
     "numbers"),
    ("What is the area of a square whose side is nine cm?",
     "81", "numbers"),
    ("If the cost of 5 pens is rupees seventy five, what "
     "is the cost of 8 pens?", "120", "numbers"),
    ("15 ka 6 se guna karo", "90", "phrase"),
    ("What is the cost of 8 pens if 5 pens cost rupees 75?",
     "120", "reorder"),
    ("Yesterday Priya went to a fair with her mother. "
     "There were many stalls and games and lots of people "
     "enjoying themselves the whole day. At one stall she "
     "saw a beautiful ribbon. She bought a ribbon 450 cm "
     "long and cut it into 9 equal pieces. Tell me the "
     "length of each piece, my friend, because I could "
     "not do it at home.", "50", "core:equal_share"),
    ("A man had 500 rupees and spent 200 rupees. How much "
     "money is left with him?", "300", "core:money_left"),
    ("ek aadmi ke paas paanch sau rupaye hai, usne do sau "
     "rupaye kharch kar diye, kitne bache", "300",
     "core:money_left"),
    ("bhaiya ek notebook ka daam bees rupaye hai, paanch "
     "notebook ka kitna hoga", "100", "core:unitary"),
    ("Find the area and perimeter of a rectangle whose "
     "length is thirteen cm and breadth is seven cm", "91",
     "split"),
    ("A car travels at sixty km per hour for two hours "
     "and then at forty km per hour for one hour. Find "
     "the total distance travelled.", "160",
     "schema:multileg_distance"),
    ("What is the difference between twenty five percent "
     "of 240 and twenty percent of 200?", "20",
     "schema:percent_difference"),
]


@pytest.mark.parametrize("question,want,mech", RESCUES)
def test_rescue_battery(db, no_ai, question, want, mech):
    result = fallback_answer(question)
    assert result.get("fallback_kind") == "deep_solve", \
        result.get("answer")
    assert result.get("deep_mechanism", "").startswith(mech)
    assert want in str(result.get("answer"))


def test_split_rescue_carries_both_parts(db, no_ai):
    result = fallback_answer(
        "Find the area and perimeter of a rectangle whose "
        "length is thirteen cm and breadth is seven cm")
    assert result["deep_mechanism"] == "split"
    assert "91" in result["answer"]
    assert "40" in result["answer"]


# ---------------------------------------------------------------------------
# Near-miss guards: a variant must never answer a
# different question
# ---------------------------------------------------------------------------

def test_guard_difference_of_percents_not_first_part(db,
                                                     no_ai):
    # The stock solver answers this digits shape with the
    # FIRST part only (60) — a variant must never launder
    # that into a rescue; the guard schema computes the
    # true difference (20) itself.
    result = fallback_answer(
        "What is the difference between twenty five "
        "percent of 240 and twenty percent of 200?")
    assert result.get("deep_mechanism") == \
        "schema:percent_difference"
    assert str(result["answer"]) == "20"


def test_guard_multileg_not_first_leg(db, no_ai):
    # Same trap, distance shape. (The digits twin of this
    # question is served upstream as a "real" solver answer
    # — the first leg only — so the chain never consults
    # the deep stage for it; that partial answer is a stock
    # solver matter outside this wave's seam, recorded in
    # the wave notes. What is pinned here is the STAGE's
    # own behaviour whenever it IS consulted: the schema
    # computes the true total, 160, never the first leg.)
    own = run_deep(
        "A car travels at 60 km per hour for 2 hours and "
        "then at 40 km per hour for 1 hour. Find the total "
        "distance travelled.")
    assert own is not None
    assert own.get("deep_mechanism") == \
        "schema:multileg_distance"
    assert str(own["answer"]) == "160"


def test_guard_multileg_with_extra_condition_refused(db):
    # A "25% faster" second leg carries a number outside
    # the leg pattern: the schema refuses, and no variant
    # may invent an answer either.
    assert run_deep(
        "A car travels at 60 km per hour for 2 hours and "
        "then at a speed 25% faster for 1 hour. Find the "
        "total distance travelled.") is None


def test_guard_hindi_do_is_a_verb_not_a_number(db):
    # "answer do" = "give the answer": the digitiser must
    # never turn the verb into the number 2.
    assert deep_solve.digitise("mujhe iska answer do") == \
        "mujhe iska answer do"
    assert run_deep("mujhe iska answer do") is None


def test_guard_english_one_of_idiom(db):
    assert "1 of the" not in deep_solve.digitise(
        "One of the two numbers is 12 and the other is 18.")


def test_guard_and_separates_two_numbers(db):
    # "forty five and thirty six" is 45 and 36 — the "and"
    # may only join a phrase after a scale word.
    assert deep_solve.digitise(
        "What is the sum of forty five and thirty six?") == \
        "What is the sum of 45 and 36?"
    assert deep_solve.digitise(
        "What is twenty five percent of two hundred and "
        "forty?") == "What is 25 percent of 240?"


def test_guard_money_left_with_third_number_refused(db):
    # An earning leg after the spending changes the
    # question; the two-number core must refuse.
    assert run_deep(
        "A man had 500 rupees. He spent 200 rupees and "
        "then earned 150 rupees. How much money is left "
        "with him?") is None


def test_guard_still_not_found(db, no_ai):
    for q in ("gibberishhh xyzzy plover",
              "What is the capital of France?"):
        result = fallback_answer(q)
        assert result.get("fallback_kind") in (
            "not_found", "nonmaths")
        assert result.get("deep_mechanism") is None


# ---------------------------------------------------------------------------
# Method transfer
# ---------------------------------------------------------------------------

TRANSFER_SLIPS = [
    ("What is 24% of 450?",
     _ai("118", ["24% of 450 = 450 × 24/100 = 118"]),
     "108", "transfer:percent_of"),
    ("A shirt has a price of rupees 850. It is sold at a "
     "discount of 12%. Find the selling price.",
     _ai("738", ["Discount = 12% of 850 = 112",
                 "Selling price = 850 - 112 = 738"]),
     "748", "transfer:discount"),
    ("Find the simple interest on rupees 6000 at 5 percent "
     "per annum for 4 years.",
     _ai("1300", ["SI = (P × R × T) / 100",
                  "SI = (6000 × 5 × 4) / 100 = 1300"]),
     "1200", "transfer:simple_interest"),
    ("Find the area of a rectangle whose length is 14 cm "
     "and breadth is 9 cm.",
     _ai("116", ["Area = length × breadth",
                 "Area = 14 × 9 = 116"]),
     "126", "transfer:area_rectangle"),
    ("Find the HCF of 24 and 36.",
     _ai("18", ["The factors of 24 are 1, 2, 3, 4, 6, 8, "
                "12, 24", "HCF of 24 and 36 = 18"]),
     "12", "transfer:hcf"),
    ("Solve: 3x + 5 = 20",
     _ai("6", ["3x + 5 = 20", "3x = 20 - 5 = 15",
               "x = 15/3 = 6"]),
     "x = 5", "transfer:equation"),
    ("Find the average of 12, 15, 20 and 25.",
     _ai("17.5", ["Sum = 12 + 15 + 20 + 25 = 70",
                  "Average = 70 / 4 = 17.5"]),
     "18", "transfer:average"),
    ("A shopkeeper buys 15 kg of rice at rupees 40 per "
     "kg. What is the total cost?",
     _ai("650", ["Total cost = 15 × 40 = 650"]),
     "600", "transfer:arith_steps"),
    ("240 ka 25 pratishat kitna hoga?",
     _ai("65", ["25% of 240 = 240 × 25/100 = 65"]),
     "60", "transfer:percent_of"),
]


@pytest.mark.parametrize("question,fixture,want,mech",
                         TRANSFER_SLIPS)
def test_transfer_slip_rescued(db, question, fixture, want,
                               mech):
    own = run_deep(question, ai_result=fixture)
    assert own is not None
    assert own["deep_mechanism"] == mech
    assert str(own["answer"]) == want
    # Ganitra's own answer carries no AI flags.
    assert not own.get("ai_generated")
    assert own["fallback_kind"] == "deep_solve"


def test_transfer_agreement_stands(db):
    fixture = _ai("108", ["24% of 450 = 450 × 24/100 = 108"])
    assert run_deep("What is 24% of 450?",
                    ai_result=fixture) is None


def test_transfer_wrong_method_never_rescued(db):
    perimeter = _ai("40", ["Perimeter = 2 × (12 + 8) = 40"])
    assert run_deep(
        "Find the area of a rectangle whose length is "
        "12 cm and breadth is 8 cm.",
        ai_result=perimeter) is None
    hcf_for_lcm = _ai("6", ["HCF of 12 and 18 = 6",
                            "So the answer is 6"])
    assert run_deep("Find the LCM of 12 and 18.",
                    ai_result=hcf_for_lcm) is None


def test_transfer_vague_steps_rescue_nothing(db):
    vague = _ai("4", ["Use the division method carefully "
                      "and you will get the result.",
                      "The answer is given below."])
    assert run_deep("Find the HCF of 12 and 18.",
                    ai_result=vague) is None
    assert run_deep("What is 24% of 450?",
                    ai_result=_ai("118", [])) is None


def test_transfer_invented_problem_refused(db):
    # The steps solve a DIFFERENT equation (7x + 2 = 65)
    # whose numbers are not in the student's question.
    fixture = _ai("9", ["7x + 2 = 65", "x = 9"])
    assert run_deep("Solve: 3x + 5 = 20",
                    ai_result=fixture) is None


def test_transfer_never_hijacks_intermediate_equation(db):
    # The Wave 119 probe, replayed at the transfer seam:
    # the AI's steps contain an INTERMEDIATE equation
    # (x^2 = x, the intersection step of an area working)
    # and a CORRECT final answer (the area, 1/6). The
    # equation is not the AI's method for the asked
    # quantity — the transfer must not replace the area
    # with the roots.
    fixture = _ai("1/6 square units", [
        "y = x^2", "y = x", "x^2 = x", "x^2 - x = 0",
        "x(x - 1) = 0", "x = 0 and x = 1",
        "Area = integral from 0 to 1 of (x - x^2) dx",
        "Area = [x^2/2 - x^3/3] from 0 to 1",
        "Area = (1/2 - 1/3) - (0 - 0)", "Area = 1/2 - 1/3",
        "Area = 1/6"])
    assert run_deep(
        "Find the area between the curves y = x^2 and "
        "y = x", ai_result=fixture) is None


def test_transfer_equation_multi_root_sets(db):
    q = "Solve: x^2 - 5x + 6 = 0"
    steps = ["x^2 - 5x + 6 = 0", "(x - 2)(x - 3) = 0"]
    agree = _ai("x = 2, x = 3", steps)
    assert run_deep(q, ai_result=agree) is None
    slipped = _ai("x = 2, x = 4", steps)
    own = run_deep(q, ai_result=slipped)
    assert own is not None
    assert own["answer"] == "x = 2, x = 3"
    assert own["deep_mechanism"] == "transfer:equation"


def test_transfer_discount_amount_ask(db):
    # The ask is the discount AMOUNT, not the selling
    # price: the transfer must recompute the amount, not
    # serve a selling price the student never asked for.
    fixture = _ai("112", ["Discount = 12% of 850 = 112"])
    own = run_deep(
        "A shirt has a price of rupees 850. It is sold at "
        "a discount of 12%. How much discount does the "
        "customer get?", ai_result=fixture)
    assert own is not None
    assert own["answer"] == "102"


def test_transfer_percent_subpart_not_hijacked(db):
    # A percent-of that is only a sub-part of a selling
    # price question: the bare percent value (102) must
    # never replace the AI's selling-price answer; the
    # discount schema owns the recompute.
    fixture = _ai("758", ["Discount = 12% of 850 = 102",
                          "Selling price = 850 - 102 = 758"])
    own = run_deep(
        "A jacket costs rupees 850 and is sold at 12% "
        "discount. What is the selling price?",
        ai_result=fixture)
    assert own is not None
    assert own["answer"] == "748"
    assert own["deep_mechanism"] == "transfer:discount"


def test_transfer_arith_producing_line_only(db):
    # The producing line agrees with the claim and is
    # internally right: nothing to rescue, even though an
    # earlier intermediate line exists.
    fixture = _ai("1500", ["Rice cost = 15 × 40 = 600",
                           "Dal cost = 10 × 90 = 900",
                           "Total = 600 + 900 = 1500"])
    assert run_deep(
        "What is the total cost of 15 kg rice at 40 "
        "rupees per kg and 10 kg dal at 90 rupees per kg?",
        ai_result=fixture) is None


def test_transfer_wired_at_the_ai_seam(db, monkeypatch):
    # End to end: the question reaches the AI seam (its
    # variants disabled here so the transfer is what is
    # exercised), Gemini returns a slipped percent answer,
    # and the chain serves Ganitra's OWN recomputation.
    monkeypatch.setattr(deep_solve, "_variants",
                        lambda q: [])
    monkeypatch.setattr(deep_solve, "_SCHEMAS", ())
    monkeypatch.setattr(deep_solve, "_split_parts",
                        lambda t: None)
    slipped = _ai("950", ["SI = (P × R × T) / 100",
                          "SI = (5000 × 6 × 3) / 100 = 950"])
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: slipped)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)
    # The spelled SI question stands at a concepts.py card
    # (not a topics card), so it reaches the AI seam; the
    # digits form is solver-solved upstream.
    result = fallback_answer(
        "Find the simple interest on rupees five thousand "
        "at six percent per annum for three years")
    assert result.get("deep_mechanism") == \
        "transfer:simple_interest"
    assert str(result["answer"]) == "900"


# ---------------------------------------------------------------------------
# Byte-identical regression pins
# ---------------------------------------------------------------------------

SOLVED_CONTROLS = [
    "What is 25 percent of 240?",
    "Find the HCF of 12 and 18",
    "One of the two numbers is 12 and the other is 18. "
    "Find their HCF.",
    "Find x and y: x + y = 10 and x - y = 4",
    "What is 18 × 12?",
    "The sum of two numbers is 48 and their difference "
    "is 12. Find the numbers.",
]


@pytest.mark.parametrize("question", SOLVED_CONTROLS)
def test_solved_questions_byte_identical(db, no_ai,
                                         monkeypatch,
                                         question):
    with_deep = fallback_answer(question)
    monkeypatch.setenv("GANITRA_DEEP_SOLVE", "0")
    without_deep = fallback_answer(question)
    assert with_deep == without_deep
    assert with_deep.get("deep_mechanism") is None


def test_correct_ai_answer_byte_identical(db, monkeypatch):
    good = _ai("900", ["SI = (P × R × T) / 100",
                       "SI = (5000 × 6 × 3) / 100 = 900"])
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: good)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(deep_solve, "_variants",
                        lambda q: [])
    monkeypatch.setattr(deep_solve, "_SCHEMAS", ())
    monkeypatch.setattr(deep_solve, "_split_parts",
                        lambda t: None)
    q = ("Find the simple interest on rupees five thousand "
         "at six percent per annum for three years")
    with_deep = fallback_answer(q)
    monkeypatch.setenv("GANITRA_DEEP_SOLVE", "0")
    without_deep = fallback_answer(q)
    assert with_deep == without_deep
    # Deploy-27 merge: Wave 133 verification stamps every
    # served AI result with its two marks (ai_verification /
    # ai_verify_check) — the one sanctioned difference from
    # the leg's raw dict. Everything else must still be
    # byte-identical to the AI's own answer: deep-solve does
    # not touch a correct answer.
    served = {k: v for k, v in without_deep.items()
              if k not in ("ai_verification",
                           "ai_verify_check")}
    assert served == good
    assert without_deep["ai_verification"] in (
        "deterministic", "consensus", "single")


def test_kill_switch_restores_stock(db, no_ai, monkeypatch):
    q = "What is fifteen multiplied by six?"
    monkeypatch.setenv("GANITRA_DEEP_SOLVE", "0")
    assert run_deep(q) is None
    result = fallback_answer(q)
    assert result.get("fallback_kind") == "not_found"


# ---------------------------------------------------------------------------
# Budgets + telemetry
# ---------------------------------------------------------------------------

def test_stage_is_bounded(db):
    start = time.monotonic()
    run_deep("Yesterday Priya went to a fair with her "
             "mother. There were many stalls and games and "
             "lots of people enjoying themselves the whole "
             "day. At one stall she saw a beautiful ribbon. "
             "She bought a ribbon 450 cm long and cut it "
             "into 9 equal pieces. Tell me the length of "
             "each piece, my friend, because I could not do "
             "it at home.")
    run_deep("gibberishhh xyzzy plover quantum bananas")
    elapsed = time.monotonic() - start
    # Two worst-case invocations together must stay well
    # inside two stage budgets (plus cold-import slack).
    assert elapsed < 2 * deep_solve.MAX_SECONDS + 5


def test_telemetry_records_mechanism_only(db, no_ai):
    fallback_answer("What is fifteen multiplied by six?")
    rows = deep_solve.rescue_rows(db_path=str(db))
    assert rows, "the rescue was not logged"
    row = rows[0]
    assert row["mechanism"] == "numbers"
    assert set(row) == {"question_norm", "question_text",
                        "mechanism", "hits", "first_seen",
                        "last_seen"}
