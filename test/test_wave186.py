"""Wave 186: implicit + logarithmic differentiation in the
"Find dy/dx if ..." dress (form-audit top-10 item #1).

Audit probes 09 / 10 (ganitra-formaudit-notes.md):

    "Find dy/dx if 2x + 3y = sin x" -> dy/dx = (cos x - 2)/3
    "Find dy/dx if x^y + y^x = 1"   -> logarithmic form

BEFORE: both burned the full 10 s solve budget and fell to
the fallback guide.  Measured root cause: c12gaps142's
implicit / log schemas settle both in < 0.6 s, but they sit
behind a failure-only gate at the END of
router._solve_question_uncached, and the primary path never
arrives in time — calculus reads the relation as a
differential equation and its dsolve call burns ~10.2 s in
odesimp / heurisch integration, so the Wave 46 budget
discards the correct late answer and serves the too-big
error dict.

Fix: solver/dydx186.py (strict dress-gated schema: implicit
relations in x and y via idiff, variable-power explicit
forms via factor-wise logarithmic differentiation, every
serve verified at solve time) behind an EARLY gate in
router._solve_question_uncached.

Every expected value below was derived independently of
the solver (hand total-derivative / log-differentiation,
cross-checked against SymPy idiff / diff and finite
differences) before being pinned.  Served answers are
parsed back and compared numerically against those
independent formulas, so a wrong serve fails here even if
its text looks plausible.
"""
import time

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor)

from solver.dydx186 import solve_dydx186
from solver.router import solve_question

x, y, a, b, k = sp.symbols("x y a b k")
_TR = standard_transformations + (
    implicit_multiplication_application, convert_xor)
_LOCALS = {"x": x, "y": y, "a": a, "b": b, "k": k,
           "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
           "log": sp.log, "sqrt": sp.sqrt, "exp": sp.exp,
           "pi": sp.pi, "e": sp.E}


def _back(answer_text):
    """Parse a served fmt() answer back to a SymPy expr."""
    return parse_expr(str(answer_text).replace("·", "*"),
                      local_dict=_LOCALS, transformations=_TR)


def _close_at(expr, subs_list):
    for subs in subs_list:
        got = complex(expr.subs(subs))
        assert abs(got.imag) < 1e-9, (expr, subs, got)
        yield float(got.real)


def assert_equiv(answer_text, expected, subs_list):
    served = _back(answer_text)
    diffs = [abs(g - e) for g, e in zip(
        _close_at(served, subs_list),
        _close_at(expected, subs_list))]
    assert max(diffs) < 1e-6, (answer_text, expected, diffs)


_XY_POINTS = [{x: 0.7, y: 1.1, a: 2, b: 3, k: 1},
              {x: 1.3, y: 0.6, a: 2, b: 3, k: 1},
              {x: 2.1, y: 1.7, a: 2, b: 3, k: 1}]
_X_POINTS = [{x: 1.3}, {x: 2.2}]


def mod(q):
    out = solve_dydx186(q)
    assert out is not None, q
    return out


def declines(q):
    assert solve_dydx186(q) is None, q


# ------------------------------------------------------------------
# The two audit probes, verbatim — module, router, timing
# ------------------------------------------------------------------

P09 = "Find dy/dx if 2x + 3y = sin x"
P10 = "Find dy/dx if x^y + y^x = 1"


def test_probe09_module():
    out = mod(P09)
    assert out["type"] == "calculus"
    assert out["op"] == "implicit_dydx"
    assert out["answer"] == "cos(x)/3 - 2/3"
    assert_equiv(out["answer"], (sp.cos(x) - 2) / 3,
                 _XY_POINTS)


def test_probe09_router_fast():
    t0 = time.time()
    out = solve_question(P09)
    dt = time.time() - t0
    assert out["op"] == "implicit_dydx"
    assert out["answer"] == "cos(x)/3 - 2/3"
    # BEFORE: 10.05 s -> the too-big error dict.
    assert dt < 4.0, dt


def test_probe10_module():
    out = mod(P10)
    assert out["op"] == "log_implicit_dydx"
    expected = (-(y ** x * sp.log(y) + y * x ** y / x)
                / (x * y ** x / y + x ** y * sp.log(x)))
    assert_equiv(out["answer"], expected, _XY_POINTS)


def test_probe10_router_fast():
    t0 = time.time()
    out = solve_question(P10)
    dt = time.time() - t0
    assert out["op"] == "log_implicit_dydx"
    # BEFORE: 10.06 s -> the too-big error dict.
    assert dt < 4.0, dt


# ------------------------------------------------------------------
# Implicit family variants (NCERT Ex 5.3 dresses)
# ------------------------------------------------------------------

def test_implicit_params_ax_by2_cos_y():
    # Declined by c12gaps142 itself (glued ax / by tokens).
    out = mod("Find dy/dx if ax + by^2 = cos y")
    assert out["op"] == "implicit_dydx"
    assert_equiv(out["answer"], -a / (2 * b * y + sp.sin(y)),
                 _XY_POINTS)


def test_implicit_sin2y_cosxy_k():
    # Declined by c12gaps142 itself (sin^2 parse error).
    out = mod("Find dy/dx if sin^2 y + cos xy = k")
    assert out["op"] == "implicit_dydx"
    expected = (y * sp.sin(x * y)
                / (sp.sin(2 * y) - x * sp.sin(x * y)))
    assert_equiv(out["answer"], expected, _XY_POINTS)


def test_implicit_sin2x_cos2y_1():
    out = mod("Find dy/dx if sin^2 x + cos^2 y = 1")
    assert out["answer"] == "sin(2·x)/sin(2·y)"
    assert_equiv(out["answer"], sp.sin(2 * x) / sp.sin(2 * y),
                 _XY_POINTS)


def test_implicit_cubic_relation():
    out = mod("Find dy/dx if x^3 + x^2 y + x y^2 + y^3 = 81")
    expected = (-(3 * x ** 2 + 2 * x * y + y ** 2)
                / (x ** 2 + 2 * x * y + 3 * y ** 2))
    assert_equiv(out["answer"], expected, _XY_POINTS)


def test_implicit_sin_y_variant():
    out = mod("Find dy/dx if 2x + 3y = sin y")
    assert out["answer"] == "2/(cos(y) - 3)"
    assert_equiv(out["answer"], 2 / (sp.cos(y) - 3),
                 _XY_POINTS)


def test_implicit_quadratic_relation():
    out = mod("Find dy/dx if x^2 + xy + y^2 = 100")
    assert_equiv(out["answer"], (-2 * x - y) / (x + 2 * y),
                 _XY_POINTS)


def test_implicit_xy_equals_4():
    out = mod("Find dy/dx if xy = 4")
    assert out["answer"] == "-y/x"


def test_implicit_exp_relation():
    out = mod("Find dy/dx if e^x + e^y = e^(x + y)")
    expected = (sp.exp(x + y) - sp.exp(x)) / (
        sp.exp(y) - sp.exp(x + y))
    assert_equiv(out["answer"], expected, _XY_POINTS)


# ------------------------------------------------------------------
# Logarithmic differentiation (NCERT Ex 5.5 / 5.7 dresses)
# ------------------------------------------------------------------

def test_logdiff_x_pow_x():
    out = mod("Find dy/dx of y = x^x")
    assert out["op"] == "log_differentiation"
    assert out["answer"] == "(x^x) * (log(x) + 1)"
    assert_equiv(out["answer"], x ** x * (sp.log(x) + 1),
                 _X_POINTS)


def test_logdiff_x_pow_sin_x():
    out = mod("Find dy/dx if y = x^sin x")
    assert out["op"] == "log_differentiation"
    expected = x ** sp.sin(x) * (
        sp.cos(x) * sp.log(x) + sp.sin(x) / x)
    assert_equiv(out["answer"], expected, _X_POINTS)


def test_logdiff_sin_x_pow_x():
    out = mod("Find dy/dx of y = (sin x)^x")
    assert out["op"] == "log_differentiation"
    expected = sp.sin(x) ** x * (
        sp.log(sp.sin(x)) + x / sp.tan(x))
    assert_equiv(out["answer"], expected, _X_POINTS)


def test_logdiff_log_x_pow_log_x():
    out = mod("Find dy/dx of y = (log x)^log x")
    assert out["op"] == "log_differentiation"
    assert out["answer"] == \
        "(log(x)^log(x)) * ((log(log(x)) + 1)/x)"
    expected = sp.log(x) ** sp.log(x) * (
        sp.log(sp.log(x)) + 1) / x
    assert_equiv(out["answer"], expected, _X_POINTS)


def test_logdiff_product_of_variable_powers():
    out = mod("Find dy/dx of y = x^x * (sin x)^x")
    assert out["op"] == "log_differentiation"
    expected = x ** x * sp.sin(x) ** x * (
        (sp.log(x) + 1)
        + (sp.log(sp.sin(x)) + x / sp.tan(x)))
    assert_equiv(out["answer"], expected, _X_POINTS)


def test_logdiff_quotient_of_variable_powers():
    out = mod("Find dy/dx of y = x^x / x^sin x")
    assert out["op"] == "log_differentiation"
    expected = (x ** x / x ** sp.sin(x)) * (
        (sp.log(x) + 1)
        - (sp.cos(x) * sp.log(x) + sp.sin(x) / x))
    assert_equiv(out["answer"], expected, _X_POINTS)


def test_logdiff_sum_of_variable_powers():
    out = mod("Find dy/dx of y = x^x + x^sin x")
    expected = (x ** x * (sp.log(x) + 1)
                + x ** sp.sin(x) * (
                    sp.cos(x) * sp.log(x) + sp.sin(x) / x))
    assert_equiv(out["answer"], expected, _X_POINTS)


# ------------------------------------------------------------------
# Dress variants: differentiate w.r.t. x, Hinglish, conditions
# ------------------------------------------------------------------

def test_dress_differentiate_wrt_x():
    out = mod("differentiate x^x w.r.t. x")
    assert out["answer"] == "(x^x) * (log(x) + 1)"


def test_dress_derivative_wrt_x():
    out = mod("Find the derivative of (log x)^log x "
              "w.r.t. x")
    assert out["op"] == "log_differentiation"


def test_dress_hinglish_nikalo_agar():
    out = mod("dy/dx nikalo agar 2x + 3y = sin x")
    assert out["answer"] == "cos(x)/3 - 2/3"


def test_dress_hinglish_ka_batao():
    out = mod("2x + 3y = sin x ka dy/dx batao")
    assert out["answer"] == "cos(x)/3 - 2/3"


def test_dress_hinglish_find_karo():
    out = mod("dy/dx find karo y = x^x ke liye")
    assert out["answer"] == "(x^x) * (log(x) + 1)"


def test_dress_trailing_domain_condition():
    out = mod("Find dy/dx if y = x^x, x > 0")
    assert out["answer"] == "(x^x) * (log(x) + 1)"


def test_router_hinglish_dress():
    out = solve_question("dy/dx nikalo agar 2x + 3y = sin x")
    assert out["op"] == "implicit_dydx"
    assert out["answer"] == "cos(x)/3 - 2/3"


# ------------------------------------------------------------------
# Controls: the module declines, routing is unchanged
# ------------------------------------------------------------------

def test_control_parametric_declines():
    # Probe 11: solves today via the primary path (t^2).
    declines("Find dy/dx if x = 2at^2, y = at^4")
    declines("Find dy/dx if x = a cos theta, "
             "y = b sin theta")


def test_control_plain_explicit_declines():
    declines("differentiate x^3 + sin x")
    declines("Find dy/dx of x^3 + sin x")
    declines("Find dy/dx of y = x^2 + 3x")
    declines("Find dy/dx of y = sin x + cos x")


def test_control_second_derivative_declines():
    declines("Find the second derivative of y = x^x")
    declines("Find d2y/dx2 if 2x + 3y = sin x")


def test_control_at_point_declines():
    declines("Find dy/dx of y = x^2 + 3x at x = 2")


def test_control_integration_declines():
    declines("integrate x^3 + sin x")
    declines("Find dy/dx of the integral of x^x")


def test_control_inverse_trig_declines():
    declines("Find dy/dx of sin^-1 x")
    declines("Find dy/dx if log(x^2 + y^2) = "
             "2 tan^-1(y/x)")


def test_control_non_asks_decline():
    declines("what is dy/dx")
    declines("solve 2x + 3 = 7")
    declines("Find dy/dx if y = x^2, x = 3")
    declines("prove that dy/dx of x^x is x^x (log x + 1)")


def test_router_control_parametric_unchanged():
    out = solve_question("Find dy/dx if x = 2at^2, "
                         "y = at^4")
    assert out["op"] == "parametric_dydx"
    assert out["answer"] == "t^2"


def test_router_control_plain_differentiate_unchanged():
    out = solve_question("differentiate x^3 + sin x")
    assert out["answer"] == "3·x^2 + cos(x)"


def test_router_control_at_point_unchanged():
    out = solve_question("Find dy/dx of y = x^2 + 3x "
                         "at x = 2")
    assert out["answer"] == "7"


def test_router_control_second_derivative_unchanged():
    out = solve_question("Find the second derivative "
                         "of y = x^x")
    assert out["op"] == "second_derivative"
    assert out["answer"] == \
        "(x^x + x^(x + 1)·(log(x) + 1)^2)/x"
