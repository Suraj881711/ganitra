"""Wave 125 — solver depth.

Pins the method schemas of solver/depth125.py (LPP in
Hindi/Hinglish dress + the NCERT word templates, the P(...)
probability-relations family, conditional dice/card and
coin+die forms, homogeneous + initial-condition
differential equations, area between curves, and the
Wave 103 leftovers), the hijack repairs in
depth125_upgrade, the non-displacement of correct primary
answers, and the Band C routing-battery flake fix (the
calculus prose guard + deterministic symbol pick).

Battery evidence: ~/workspace/ganitra-wave125-audit/
(76 asks, EN + HI + Hinglish: before 10/62 auto + 8/14 DE
manual; after 62/62 auto + 14/14 DE verified).
"""
import pytest

from api import _solve_friendly
from solver.depth125 import (depth125_upgrade, solve_depth125)
from solver.router import solve_question


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Chat-path tests run against a throwaway live-bank DB
    (the test_wave117 seam), so no suite-order row can be
    re-served into an assertion."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "w125.db"))
    from solver.answer_cache import (clear_cache,
                                     clear_negative_cache)
    clear_cache()
    clear_negative_cache()
    yield


def _ans(res):
    return str(res.get("answer") or "")


# --- 1. LPP -------------------------------------------------

def test_lp_hindi_symbolic():
    res = solve_depth125(
        "अधिकतम कीजिए Z = 3x + 4y जबकि x + y ≤ 4, "
        "x ≥ 0, y ≥ 0")
    assert res is not None
    assert "16" in _ans(res) and "(0, 4)" in _ans(res)


def test_lp_hinglish_symbolic_min():
    res = solve_depth125(
        "Z = 4x + y ko nyoonatam karo jabki x + y ≥ 5, "
        "x + 2y ≥ 8, x, y ≥ 0")
    assert res is not None
    assert res["value"] == 5.0


def test_lp_roman_wrapper_form():
    res = solve_depth125(
        "rakhik kramadeshan (LPP) me Z = 5x + 3y ka "
        "adhiktam maan nikalo jabki 3x + 5y ≤ 15, "
        "5x + 2y ≤ 10, x, y ≥ 0")
    assert res is not None
    assert abs(res["value"] - 235 / 19) < 1e-9


def test_lp_cakes_template():
    res = solve_depth125(
        "One kind of cake requires 200 g of flour and 25 g "
        "of fat, and another kind of cake requires 100 g "
        "of flour and 50 g of fat. Find the maximum number "
        "of cakes which can be made from 5 kg of flour "
        "and 1 kg of fat.")
    assert res is not None and res["value"] == 30.0


def test_lp_toys_template_en_and_hinglish():
    en = solve_depth125(
        "A factory manufactures two types of toys A and "
        "B. Each toy A requires 2 hours on machine I and "
        "3 hours on machine II, and each toy B requires "
        "4 hours on machine I and 2 hours on machine II. "
        "Machine I is available for at most 20 hours and "
        "machine II for at most 18 hours. The profit is "
        "Rs 30 per toy A and Rs 40 per toy B. Find the "
        "maximum profit.")
    # corners: (4, 3) -> 240, (0, 5) -> 200, (6, 0) -> 180
    assert en is not None and en["value"] == 240.0
    hi = solve_depth125(
        "ek factory do prakar ke khilone A aur B banati "
        "hai. khilona A banane me 2 ghante machine I par "
        "aur 3 ghanta machine II par lagta hai, khilona B "
        "banane me 4 ghanta machine I par aur 2 ghante "
        "machine II par lagta hai. machine I adhik se "
        "adhik 20 ghante aur machine II adhik se adhik "
        "18 ghante uplabdh hai. prati khilona A par labh "
        "30 rupaye aur B par 40 rupaye hai. adhiktam labh "
        "gyat karo.")
    assert hi is not None and hi["value"] == 240.0


def test_lp_diet_template():
    res = solve_depth125(
        "A diet is to contain at least 80 units of "
        "vitamin A and 100 units of minerals. Food F1 "
        "costs Rs 4 per unit and food F2 costs Rs 6 per "
        "unit. One unit of food F1 contains 3 units of "
        "vitamin A and 4 units of minerals, and one unit "
        "of food F2 contains 6 units of vitamin A and 3 "
        "units of minerals. Find the minimum cost of the "
        "diet.")
    assert res is not None and res["value"] == 104.0


def test_lp_hijack_upgrade():
    q = ("Z = 3x + 5y ko adhiktam karo jabki x + 2y ≤ 10, "
         "x + y ≤ 6, x, y ≥ 0")
    fake = {"type": "algebra", "op": "hindi_equation",
            "answer": "z = 3", "steps": []}
    up = depth125_upgrade(q, fake)
    assert up is not None and up["value"] == 26.0


# --- 2. Probability relations -------------------------------

def test_prob_conditional_from_intersection():
    res = solve_depth125(
        "If P(A) = 0.4, P(B) = 0.5 and P(A ∩ B) = 0.2, "
        "find P(A|B).")
    assert res is not None and "2/5" in _ans(res)


def test_prob_intersection_from_conditional():
    res = solve_depth125(
        "If P(A) = 0.6, P(B) = 0.5 and P(A|B) = 0.4, "
        "find P(A ∩ B).")
    assert res is not None and "1/5" in _ans(res)


def test_prob_conditional_via_union():
    res = solve_depth125(
        "If P(A) = 0.3, P(B) = 0.4 and P(A ∪ B) = 0.5, "
        "find P(A|B).")
    assert res is not None and "1/2" in _ans(res)


def test_prob_independence_check_yes_and_no():
    yes = solve_depth125(
        "P(A) = 0.3, P(B) = 0.4 and P(A ∩ B) = 0.12. "
        "Are A and B independent?")
    assert yes is not None
    assert _ans(yes).startswith("Yes")
    no = solve_depth125(
        "Check whether A and B are independent if "
        "P(A) = 0.5, P(B) = 0.5 and P(A ∩ B) = 0.2")
    assert no is not None
    assert _ans(no).startswith("No")


def test_prob_given_independent_and_mutually_exclusive():
    ind = solve_depth125(
        "If A and B are independent events with "
        "P(A) = 0.4 and P(B) = 0.5, find P(A ∩ B).")
    assert ind is not None and "1/5" in _ans(ind)
    mut = solve_depth125(
        "If A and B are mutually exclusive events with "
        "P(A) = 0.3 and P(B) = 0.45, find P(A ∪ B).")
    assert mut is not None and "3/4" in _ans(mut)


def test_prob_bayes_and_total():
    bayes = solve_depth125(
        "If P(E1) = 0.3, P(E2) = 0.7, P(A|E1) = 0.9 "
        "and P(A|E2) = 0.4, find P(E1|A).")
    assert bayes is not None and "27/55" in _ans(bayes)
    total = solve_depth125(
        "If P(E1) = 0.4, P(E2) = 0.6, P(A|E1) = 0.8 "
        "and P(A|E2) = 0.5, find the probability of A.")
    assert total is not None and "31/50" in _ans(total)


def test_prob_factory_percent_bayes():
    res = solve_depth125(
        "In a factory, machine A produces 60% of the "
        "items and machine B produces 40%. 2% of items "
        "from machine A are defective and 3% from "
        "machine B are defective. An item is selected at "
        "random and found to be defective. Find the "
        "probability that it was produced by machine B.")
    assert res is not None and "1/2" in _ans(res)


def test_prob_two_bags_total():
    res = solve_depth125(
        "A bag contains 5 red and 3 black balls. A ball "
        "is drawn at random. Another bag contains 4 red "
        "and 6 black balls. A bag is chosen at random "
        "and a ball is drawn from it. Find the "
        "probability that the ball is red.")
    assert res is not None and "41/80" in _ans(res)


# --- 3. Conditional sample spaces + coin & die --------------

def test_prob_dice_given_first_die():
    q = ("A die is thrown twice. Find the probability "
         "that the sum of the numbers is 8, given that "
         "the first die shows 3.")
    res = solve_depth125(q)
    assert res is not None and "1/6" in _ans(res)
    # the hijack repair: the unconditional 5/36 the
    # primary serves must be replaced
    fake = {"type": "statistics", "op": "probability",
            "answer": "5/36 ≈ 0.1389", "steps": []}
    up = depth125_upgrade(q, fake)
    assert up is not None and "1/6" in _ans(up)


def test_prob_card_given_face_card():
    res = solve_depth125(
        "A card is drawn from a pack of 52 cards. Find "
        "the probability that it is a king, given that "
        "it is a face card.")
    assert res is not None and "1/3" in _ans(res)


def test_coin_die_count_and_joint():
    cnt = solve_depth125(
        "A coin is tossed and a die is rolled. How many "
        "outcomes are possible in all?")
    assert cnt is not None and _ans(cnt) == "12"
    joint = solve_depth125(
        "A coin is tossed and a die is thrown together. "
        "Find the probability of getting a head and a 5.")
    assert joint is not None and "1/12" in _ans(joint)


# --- 4. Differential equations ------------------------------

def test_de_homogeneous_explicit():
    res = solve_depth125(
        "Solve the differential equation dy/dx = (x + y)/x")
    assert res is not None
    assert _ans(res) == "y = x·(C1 + log(x))"


def test_de_particular_via_upgrade():
    q = ("Find the particular solution of the "
         "differential equation dy/dx = y/x, given that "
         "y = 2 when x = 2")
    fake = {"type": "algebra", "op": "equation",
            "answer": "y = 2", "steps": []}
    up = depth125_upgrade(q, fake)
    assert up is not None and _ans(up) == "y = x"


def test_de_implicit_pair_verified():
    res = solve_depth125("Solve dy/dx = (x + y)/(x - y)")
    assert res is not None and _ans(res).endswith("= C")
    assert "atan(y/x)" in _ans(res)


def test_de_hindi_and_wrapper_and_coefficient():
    hi = solve_depth125(
        "अवकल समीकरण dy/dx = y/x को हल कीजिए।")
    assert hi is not None and _ans(hi) == "y = C1·x"
    wrap = solve_depth125(
        "Find the general solution of dy/dx = e^(y/x) "
        "type nahi — solve dy/dx = (x^2 + xy)/x^2")
    assert wrap is not None
    assert _ans(wrap) == "y = x·(C1 + log(x))"
    coef = solve_depth125(
        "Solve the differential equation x dy/dx = "
        "y + x^2")
    assert coef is not None
    assert _ans(coef) == "y = x·(C1 + x)"


def test_de_implicit_primary_upgraded_via_chat_path():
    res = _solve_friendly(
        "अवकल समीकरण dy/dx = y/x को हल कीजिए।")
    assert _ans(res) == "y = C1·x"


# --- 5. Area between curves ---------------------------------

@pytest.mark.parametrize("q,frag", [
    ("Find the area between the curves y = x^2 and "
     "y = x", "1/6"),
    ("Find the area enclosed between the parabola "
     "y^2 = 4x and the line y = x", "8/3"),
    ("Find the area between the parabolas y^2 = 4x "
     "and x^2 = 4y", "16/3"),
    ("Find the area of the region bounded by the "
     "ellipse x^2/16 + y^2/9 = 1", "12·pi"),
    ("paravalay y = x^2 aur rekha y = x ke beech ka "
     "kshetrafal nikalo", "1/6"),
])
def test_area_pairs(q, frag):
    res = solve_depth125(q)
    assert res is not None and frag in _ans(res)
    assert _ans(res).endswith("square units")


def test_area_circle_line_and_sin_cos():
    circ = solve_depth125(
        "Find the area enclosed by the circle "
        "x^2 + y^2 = 4 and the line x = 1")
    assert circ is not None
    assert abs(circ["value"] - 2.4567) < 0.001
    sc = solve_depth125(
        "Find the area of the region bounded by "
        "y = sin x and y = cos x between x = 0 and "
        "x = pi/4")
    assert sc is not None
    assert abs(sc["value"] - 0.41421) < 0.001


# --- 6. Wave 103 leftovers ----------------------------------

def test_ratio_angles_all_languages():
    en = solve_depth125(
        "The angles of a quadrilateral are in the ratio "
        "2 : 4 : 5 : 7. Find the largest angle.")
    assert en is not None and _ans(en) == "140°"
    hin = solve_depth125(
        "chaturbhuj ke kon 2 : 3 : 5 : 8 ke anupat me "
        "hai. sabse bada kon kitna hoga?")
    assert hin is not None and _ans(hin) == "160°"
    dev = solve_depth125(
        "चतुर्भुज के कोण 3 : 5 : 9 : 13 के अनुपात में "
        "हैं। सबसे छोटा कोण ज्ञात कीजिए।")
    assert dev is not None and _ans(dev) == "36°"


def test_g_function_evaluation():
    hin = solve_depth125(
        "g(x) = 3x - 5 hai to g(-2) ka maan nikalo")
    assert hin is not None and _ans(hin) == "-11"
    en = solve_depth125(
        "If g(x) = 2x^2 - x + 1, find the value of g(0).")
    assert en is not None and _ans(en) == "1"


# --- non-displacement ----------------------------------------

def test_primary_answers_not_displaced():
    # gaps103 already owns this f-form; the chat path
    # answer must stay the primary's
    res = _solve_friendly("If g(x) = x^2 + 2x, find g(3).")
    assert "15" in _ans(res)
    # a plain derivative ask is untouched by the prose
    # guard
    res = solve_question("Find the second derivative "
                         "of x^4")
    assert res.get("op") == "higher_derivative"
    assert "12" in _ans(res)


# --- 5(b). the flake fix --------------------------------------

def test_flake_second_derivative_howto_is_deterministic():
    # the routing battery item that flaked: the prose
    # guard makes the solver decline every time, so the
    # topics concept card serves — in every process
    res = _solve_friendly(
        "second derivative kaise nikalte hai kisi "
        "function ka")
    assert res.get("source") == "topics"
    assert res.get("topic_slug") == \
        "second-derivative-of-x4"


def test_calculus_prose_guard_units():
    from solver.calculus import _guess_symbol, _is_prose_expr
    import sympy as sp
    assert _is_prose_expr("kaise nikalte hai kisi "
                          "function ka")
    assert not _is_prose_expr("x^4")
    assert not _is_prose_expr("sin x + log x")
    a, b, c = sp.symbols("a b c")
    # deterministic: x preferred, else alphabetical —
    # never set-iteration order
    assert _guess_symbol(a * b * c) == a
    x = sp.symbols("x")
    assert _guess_symbol(b * x) == x
