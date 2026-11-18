"""Wave 159 — bank-sweep fix wave (Wave 157 full-databank
sweep: 2,354 verified questions run through the solver;
325 serves disagreed with the verified answer).

Family 1 — arithmetic echo / partial serves. The carve
layers (the router's Wave 77 core pass, the fallback
salvage) served a SUB-EXPRESSION of the question: the
first fraction echoed verbatim ("(3/4 + 5/6) x 12 - 10"
answered "3/4") or the first term of a stated expression
("(48 * 6) + (24 * 3)" answered 288). Rules: a carved
candidate may serve only when it accounts for EVERY
numeric atom of the text it was carved from (coverage),
a question's own explicit full expression is offered as
a candidate ahead of any fragment, and a serve that
disagrees with a stated full expression's value is
vetoed (_w159_veto).

Family 2 — salvage partial serves (40/40 wrong in the
sweep): the same coverage gate at the salvage serve
point, so a fragment of the question can never be
served as the question's answer.

Family 3 — meta-card hijacks (29/29 wrong): a message
carrying a concrete solvable problem (>= 2 numbers + a
computation ask / schema keyword, in any script) must
never be answered by an advice / concept / non-maths
card. The Hindi trigger word "परीक्षा" sent real
problems to exam advice; a Hindi LCM problem was refused
as non-maths. Pure small-talk / guidance / concept asks
carry no such combination and are untouched.
"""
import pytest

from fallback import _is_nonmaths, _salvage, _w159_covers, \
    _w159_full_expression, _w159_problem_bearing, _w159_veto
from maths_meta import meta_result
from solver.router import _w77_candidates, solve_question

SIGNUP = {"name": "W159 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w159-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    c.post("/api/signup", json=SIGNUP)
    return c


def solve(client, question):
    data = client.post("/api/solve",
                       json={"question": question}).get_json()
    return data["result"]


# ------------------------------------------------------------------ #
# Family 1: coverage + full-expression helpers
# ------------------------------------------------------------------ #

def test_coverage_fragment_does_not_cover():
    q = ("एक ट्रेन ने पहले 3/4 किमी और फिर 5/6 किमी की दूरी "
         "तय की। इस कुल दूरी को 12 से गुणा करके 10 किमी घटाया "
         "गया। व्यंजक का मान ज्ञात कीजिए।")
    assert not _w159_covers(q, "3/4")
    assert not _w159_covers(q, "5/6")


def test_coverage_wrapped_single_problem_covers():
    assert _w159_covers("oye 1/2 + 1/3 kitna hoga plz yr?",
                        "1/2 + 1/3")
    assert _w159_covers("samikaran 2x + 3 = 7 hal karo",
                        "2x + 3 = 7")
    assert _w159_covers("find the value of 2x + 3 when x = 4",
                        "2*(4) + 3")


def test_coverage_question_label_is_not_content():
    assert _w159_covers("Question 5: Solve 3x + 7 = 22",
                        "3x + 7 = 22")


def test_full_expression_extraction():
    assert _w159_full_expression(
        "find their total score using the expression "
        "(12 * 9) - (4 * 1).") == "(12 * 9) - (4 * 1)"
    assert _w159_full_expression(
        "The expression is (9/3 + 12 + 1) - 7. Find its "
        "value.") == "(9/3 + 12 + 1) - 7"
    # a definition's right-hand side is not the ask
    assert _w159_full_expression("If x = (2 + 3), find 2x") \
        is None
    # a lone chain is the chain candidate's shape, not this
    assert _w159_full_expression("what is 2 + 3?") is None
    # a bracketed data list is not an expression
    assert _w159_full_expression(
        "the marks are (12, 15, 18), find the mean") is None
    # a Devanagari danda right after the last operand must
    # not truncate the run (the sweep's field question)
    assert _w159_full_expression(
        "एक खेत की लंबाई 16 मीटर है। यदि चौड़ाई 5/8 है और "
        "अतिरिक्त 7 मीटर जुड़े, तो expression: (5/8 * 16) + 7। "
        "इसका मान ज्ञात कीजिए।") == "(5/8 * 16) + 7"


def test_full_expression_candidate_lives_in_salvage():
    # Final design (settled against test_wave39_bank): the
    # router's core pass carries NO full-expression
    # candidate — a core-pass solve of a stated expression
    # would shadow the verified bank layer for banked
    # questions. The candidate lives in fallback's salvage
    # list instead, ahead of its own fragments, where the
    # bank cannot be pre-empted.
    from fallback import _candidates
    q = ("find their total score using the expression "
         "(12 * 9) - (4 * 1).")
    assert "(12 * 9) - (4 * 1)" not in _w77_candidates(q)
    cands = _candidates(q)
    assert cands[0] == "(12 * 9) - (4 * 1)"


# ------------------------------------------------------------------ #
# Family 1: end-to-end serves
# ------------------------------------------------------------------ #

def test_fraction_echo_hindi_not_served(client):
    q = ("एक ट्रेन ने पहले 3/4 किमी और फिर 5/6 किमी की दूरी "
         "तय की। इस कुल दूरी को 12 से गुणा करके 10 किमी घटाया "
         "गया। व्यंजक का मान ज्ञात कीजिए।")
    got = solve(client, q)
    # the sweep served the first fraction verbatim ("3/4");
    # the full value is 9 — anything else must be an honest
    # decline, never the echo
    assert got["answer"] != "3/4"
    assert "3/4" not in str(got.get("answer", "")) or \
        got["answer"] == "9"


def test_stated_expression_solved_wholly(client):
    got = solve(client, "A class has 9/3 chapters to read "
                        "and reads 7. Then 12 chapters and 1 "
                        "chapter are read. The expression is "
                        "(9/3 + 12 + 1) - 7. Find its value.")
    assert got["answer"] == "9"  # not 3 (the first term)


def test_stated_expression_beats_partial_schema(client):
    got = solve(client, "A train travels at 35 km per hour "
                        "for 4 hours and then at 16 km per "
                        "hour for 5 hours; the total distance "
                        "is (35 * 4) + (16 * 5). What is the "
                        "total distance?")
    assert "220" in str(got["answer"])  # not 140 (first leg)


def test_w159_veto_direct():
    q = ("A train travels at 35 km per hour for 4 hours and "
         "then at 16 km per hour for 5 hours; the total "
         "distance is (35 * 4) + (16 * 5). What is the total "
         "distance?")
    assert _w159_veto(q, {"answer": "140", "numeric": 140.0})
    assert not _w159_veto(q, {"answer": "220",
                              "numeric": 220.0})
    # no stated expression -> the veto stays silent
    assert not _w159_veto("What is 2 + 3?",
                          {"answer": "99", "numeric": 99.0})
    # the explicitly-introduced expression vetoes even when
    # a redundant given (11 = 7 + 4 coaches) sits outside it
    q2 = ("A train has 11 coaches with 80 seats each. 7 "
          "coaches are full, but 4 coaches have 18 empty "
          "seats each. Find the total number of passengers "
          "by evaluating: (7 * 80) + (4 * (80 - 18))")
    assert _w159_veto(q2, {"answer": "72", "numeric": 72.0})
    assert not _w159_veto(q2, {"answer": "808",
                               "numeric": 808.0})


def test_chat_wrapped_problems_still_solve(client):
    got = solve(client, "oye 1/2 + 1/3 kitna hoga plz yr?")
    assert got["answer"] == "5/6"
    got = solve(client, "samikaran 2x + 3 = 7 hal karo")
    assert got["answer"] == "x = 2"
    got = solve(client, "find the value of 2x + 3 when x = 4")
    assert got["answer"] == "11"


def test_router_direct_echo_guard():
    r = solve_question(
        "एक ट्रेन ने पहले 3/4 किमी और फिर 5/6 किमी की दूरी तय "
        "की। इस कुल दूरी को 12 से गुणा करके 10 किमी घटाया "
        "गया। व्यंजक का मान ज्ञात कीजिए।")
    assert r.get("answer") != "3/4"


# ------------------------------------------------------------------ #
# Family 2: salvage never serves a partial computation
# ------------------------------------------------------------------ #

def test_salvage_full_expression_not_first_bracket():
    r = _salvage(
        "In a quiz competition, a team earns 9 points for "
        "every correct answer and loses 1 point for every "
        "wrong answer. If the team gets 12 correct answers "
        "and 4 wrong answers, find their total score using "
        "the expression (12 * 9) - (4 * 1).", False)
    assert r is not None
    assert r["answer"] == "104"  # never 108 (the first bracket)


def test_salvage_fragment_only_question_declines():
    # every candidate is a fragment of a larger problem:
    # salvage must return None rather than echo one
    r = _salvage(
        "एक ट्रेन ने पहले 3/4 किमी और फिर 5/6 किमी की दूरी तय "
        "की। इस कुल दूरी को 12 से गुणा करके 10 किमी घटाया "
        "गया। व्यंजक का मान ज्ञात कीजिए।", True)
    assert r is None


def test_salvage_wrapped_equation_still_works():
    r = _salvage("please batao my homework says find x when "
                 "3x + 7 = 22 jaldi karo", False)
    assert r is not None
    assert "5" in str(r["answer"])


# ------------------------------------------------------------------ #
# Family 3: meta cards never hijack a concrete problem
# ------------------------------------------------------------------ #

PARIKSHA_MEAN = ("एक साप्ताहिक परीक्षा में 6 छात्रों के अंक "
                 "क्रमशः 12, 15, 18, 14, 16 और 15 हैं। इन अंकों "
                 "का माध्य ज्ञात कीजिए।")
HINDI_SI = "₹9000 पर 6% वार्षिक दर से 4 वर्ष का साधारण ब्याज कितना होगा?"
HINDI_LCM = ("एक माली एक क्यारी में फूलों के पौधे लगा रहा है। वह "
             "पौधों को 15 या 20 की पंक्तियों में लगाना चाहता है। "
             "पौधों की वह न्यूनतम संख्या क्या होगी जो दोनों स्थितियों "
             "में पूरी पंक्तियाँ बना सके?")


def test_problem_bearing_detector():
    assert _w159_problem_bearing(PARIKSHA_MEAN)
    assert _w159_problem_bearing(HINDI_SI)
    assert _w159_problem_bearing(HINDI_LCM)
    # the "क्या हैं" ask form (the sweep's Ravi-marks
    # problem was still hijacked without it)
    assert _w159_problem_bearing(
        "एक गणित की परीक्षा में, रवि के अंक एक अन्य छात्र के "
        "अंकों के दोगुने से 25 अधिक हैं। यदि रवि को 85 अंक "
        "मिले हैं, तो दूसरे छात्र के अंक क्या हैं?")
    assert _w159_problem_bearing(
        "For a school trip, a teacher wants to pack snack "
        "bags. She has 36 apples and 54 bananas. How many "
        "bags can she pack?")
    # pure guidance / small-talk carries no such combination
    assert not _w159_problem_bearing("परीक्षा की तैयारी कैसे करूँ?")
    assert not _w159_problem_bearing(
        "How to prepare for maths exam?")
    assert not _w159_problem_bearing(
        "Pythagoras theorem kisne banaya tha?")
    assert not _w159_problem_bearing(
        "मुझे गणित में डर लगता है, समझ नहीं आता")
    assert not _w159_problem_bearing(
        "What is the formula of simple interest?")


def test_meta_layer_refuses_problem_bearing():
    assert meta_result(PARIKSHA_MEAN) is None
    assert meta_result(HINDI_SI) is None
    # genuine advice asks still get their cards
    assert meta_result("परीक्षा की तैयारी कैसे करूँ?") is not None
    assert meta_result(
        "परीक्षा में सवाल कैसे हल करने चाहिए?") is not None
    assert meta_result(
        "How to prepare for maths exam?") is not None


def test_nonmaths_guard_refuses_problem_bearing():
    assert not _is_nonmaths(HINDI_LCM)
    assert _is_nonmaths("What is the capital of France?")


def test_pariksha_mean_solved_not_advised(client):
    got = solve(client, PARIKSHA_MEAN)
    assert got["answer"] == "15"
    assert got.get("fallback_kind") != "advice"


def test_hindi_si_not_a_bare_formula_card(client):
    got = solve(client, HINDI_SI)
    # the sweep served the SI formula card with no
    # computation; the question must now be solved (2160)
    # or honestly declined — never the bare card
    assert got.get("fallback_kind") != "concept"
    assert "2160" in str(got["answer"]) or \
        got.get("fallback_kind") == "not_found"


def test_hindi_lcm_not_refused_as_nonmaths(client):
    got = solve(client, HINDI_LCM)
    assert got.get("fallback_kind") != "nonmaths"
    assert "60" in str(got["answer"])


def test_genuine_meta_and_concept_asks_unchanged(client):
    got = solve(client, "परीक्षा में सवाल कैसे हल करने चाहिए?")
    assert got.get("fallback_kind") == "advice"
    got = solve(client, "What is the formula of simple "
                        "interest?")
    assert got.get("fallback_kind") == "concept"
    got = solve(client, "What is the capital of France?")
    assert got.get("fallback_kind") == "nonmaths"
