"""Wave 159 (tightening) — the stated-full-expression
candidate must be PURELY NUMERIC. The first full-suite
run caught two regressions: the extractor accepted
algebraic runs — "x^2 - 3x - 4" out of the translated
working text of a hence-chain zeroes question (which
displaced the multipart layer, test_wave100) and
"2x - 5 f(10)" out of a Hinglish f(x) question (which
displaced the f(n) schema, test_wave103). A variable or
a function call makes a run algebra, never a stated
arithmetic expression.
"""
from api import _solve_friendly
from fallback import _w159_full_expression as fb_expr
from solver.router import _w159_full_expression as rt_expr

HENCE = ("Find the zeroes of the polynomial p(x) = x² - 3x "
         "- 4. Hence, write a polynomial whose zeroes are "
         "reciprocals of the zeroes of p(x).")
HINGLISH_FN = "f(x) = 2x - 5 hai to f(10) ka maan kya hoga?"


def test_no_full_expression_for_algebra_runs():
    for extract in (rt_expr, fb_expr):
        assert extract("x^2 - 3x - 4") is None
        assert extract("2x - 5 f(10)") is None
        assert extract(HENCE) is None
        assert extract(HINGLISH_FN) is None


def test_numeric_full_expression_still_found():
    for extract in (rt_expr, fb_expr):
        assert extract("using the expression (12 * 9) - "
                       "(4 * 1)") == "(12 * 9) - (4 * 1)"
        assert extract("the total distance is (48 * 6) + "
                       "(24 * 3)") == "(48 * 6) + (24 * 3)"


def test_hence_chain_still_multipart():
    out = _solve_friendly(HENCE)
    assert out.get("source") == "multipart"


def test_hinglish_function_value_still_served():
    out = _solve_friendly(HINGLISH_FN)
    assert "f(10) = 15" in str(out.get("answer"))


# ---------------------------------------------------------------- #
# Fraction-echo veto: a serve that is one of the question's
# stated fractions verbatim, while the question states other
# numbers too, is an echo — it pre-empts the bank layer and
# the real schemas. (The first full-suite sweep re-run under
# the narrowed router gate lost 55 databank matches to
# exactly these serves: "3/4", "22/7", "1/5".)
# ---------------------------------------------------------------- #
from fallback import _w159_frac_echo

TRAIN_TIME = ("एक ट्रेन पहले 3/4 घंटे की दूरी 60 किमी/घंटा "
              "की गति से तय करती है, फिर 15 मिनट रुकती है, "
              "और फिर 120 किमी की दूरी 80 किमी/घंटा की गति "
              "से तय करती है। कुल यात्रा समय (घंटों में) "
              "कितना होगा?")


def test_frac_echo_veto_fires_on_stated_fraction():
    assert _w159_frac_echo(TRAIN_TIME, {"answer": "3/4"})
    assert _w159_frac_echo(
        "A circle has radius 14 m. Take pi = 22/7. Find "
        "its area.", {"answer": "22/7"})


def test_frac_echo_veto_silent_on_legit_serves():
    # the fraction IS the whole question's numeric content
    assert not _w159_frac_echo("Simplify 3/4",
                               {"answer": "3/4"})
    # a computed value that is not a stated literal
    assert not _w159_frac_echo(TRAIN_TIME, {"answer": "2.5"})
    assert not _w159_frac_echo(TRAIN_TIME, {"answer": "5/2"})
    # integer serves are out of this veto's scope
    assert not _w159_frac_echo(TRAIN_TIME, {"answer": "15"})


def test_train_time_question_not_echo_served():
    out = _solve_friendly(TRAIN_TIME)
    assert str(out.get("answer")).strip() != "3/4"


# ---------------------------------------------------------------- #
# Sub-expression echo veto: the serve equals the value of ONE
# stated leg of a multi-leg computation (the first bracket,
# the middle leg) while the question states more beyond it.
# ---------------------------------------------------------------- #
from fallback import _w159_subexpr_echo


def test_subexpr_echo_veto_fires_on_one_leg_serves():
    assert _w159_subexpr_echo(
        "In an exam, a score is calculated as (108 - 48) "
        "divided by 10, plus 13 times (17 - 5). Find the "
        "score.", {"answer": "60"})
    assert _w159_subexpr_echo(
        "A farmer harvests (5/8 + 1/4) of 24 sacks of "
        "wheat and then gives away 9 sacks. How many "
        "sacks are left?", {"answer": "7/8"})
    assert _w159_subexpr_echo(
        "एक छात्र ने परीक्षा में 80 अंक प्राप्त किए, फिर "
        "15 अंक घटाए गए, उसके बाद 2/3 × 48 अंक जोड़े गए "
        "और अंत में 5 अंक घटाए गए। अंतिम अंक क्या हैं?",
        {"answer": "32"})


def test_subexpr_echo_veto_silent_on_whole_computation():
    # the run covers every atom: serving its value is the
    # whole computation, not one leg of it
    assert not _w159_subexpr_echo(
        "Evaluate (12 * 9) - (4 * 1).", {"answer": "104"})
    # the bracket alone, before the division the question
    # asks for, IS the echo and must fire
    assert _w159_subexpr_echo(
        "Find the value of (108 - 48) divided by 10.",
        {"answer": "60"})
    assert not _w159_subexpr_echo(
        "Find the value of (108 - 48) divided by 10.",
        {"answer": "6"})
    # a serve equal to no stated leg's value
    assert not _w159_subexpr_echo(TRAIN_TIME,
                                  {"answer": "2.5"})
