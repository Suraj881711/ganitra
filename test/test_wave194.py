"""Wave 194: differential equations in NCERT dress + the
verify-the-solution wrong-serve fix (form-audit top-10
item #9; audit rows 15-17, probes 14 and 15).

BEFORE (measured on main, Deploy-46 state):
* Probe 14 — "Find the general solution of the
  differential equation (x^2 + xy) dy = (x^2 + y^2) dx"
  -> op "error" (parse error).  The bracketed
  "(...) dy = (...) dx" dress (Ex 9.3/9.4) reached no
  schema; depth125's homogeneous family owns only the
  dy/dx dress.
* Probe 15 (WRONG SERVE) — "Verify that y = e^x + 1 is
  a solution of the differential equation y'' - y' = 0"
  -> op "equation", answer "e = (y - 1)^(1/x)": the
  equation "solved" for the letter e.  The Wave 77 core
  pass extracted the core "y = e^x + 1" and returned
  algebra's solve-for-e before any late gate could run.
* "Find the general solution of dy/dx + y = e^x" and
  "... dy/dx = e^(x+y)" -> op "implicit_derivative"
  letter-soup (the question's words letter-split into a
  product of symbols).

AFTER: solver/diffeq194.py — deterministic textbook
methods only (homogeneous y = vx separation, separable
factorisation, linear integrating factor; NO dsolve —
measured: dsolve dies with RecursionError on probe
14's family), every serve verified by differentiating
it back before serving, plus a verify-the-solution
schema whose verdicts are computed by differentiating
the candidate and substituting — never asserted, and
structurally unable to solve the DE for a variable.

Solution PROPERTY is pinned, not one literal string:
an implicit serve "REL = C" is checked by implicit
differentiation against the student's own f, and an
explicit serve by direct substitution — equivalent
solution forms are legitimate.
"""
import time

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor, implicit_multiplication_application,
    parse_expr, standard_transformations)

from solver.diffeq194 import (solve_diffeq194,
                              verify_solution_result)
from solver.router import solve_question

_X, _Y, _C1 = sp.symbols("x y C1")
_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application, convert_xor)


def _parse_answer_expr(text):
    t = str(text).replace("·", "*")
    return parse_expr(t, transformations=_TRANSFORMS,
                      local_dict={"x": _X, "y": _Y,
                                  "C1": _C1, "C": _C1})


def assert_implicit_solution(answer, f):
    """The served 'REL = C' must satisfy dy/dx = f by
    implicit differentiation: -REL_x / REL_y == f."""
    assert str(answer).rstrip().endswith("= C"), answer
    rel = _parse_answer_expr(
        str(answer).rsplit("= C", 1)[0])
    fy = sp.diff(rel, _Y)
    assert fy != 0
    assert sp.simplify(-sp.diff(rel, _X) / fy - f) == 0


def assert_explicit_solution(answer, f):
    """The served 'y = EXPR' must satisfy dy/dx = f by
    direct substitution."""
    assert str(answer).startswith("y = "), answer
    sol = _parse_answer_expr(str(answer)[4:])
    assert sp.simplify(
        sp.diff(sol, _X) - f.subs(_Y, sol)) == 0


PROBE14 = ("Find the general solution of the differential "
           "equation (x^2 + xy) dy = (x^2 + y^2) dx")
PROBE15 = ("Verify that y = e^x + 1 is a solution of the "
           "differential equation y'' - y' = 0")
F14 = (_X**2 + _Y**2) / (_X**2 + _X * _Y)


# ---------------------------------------------------------------------------
# Audit probes, verbatim
# ---------------------------------------------------------------------------

def test_probe14_bracket_homogeneous():
    t0 = time.monotonic()
    r = solve_question(PROBE14)
    dt = time.monotonic() - t0
    assert r["op"] == "differential_equation", r
    # -y/x - 2*log|1 - y/x| = log|x| + C is one legitimate
    # form; any equivalent implicit form passes the
    # property check.
    assert_implicit_solution(r["answer"], F14)
    assert dt < 4.0, dt


def test_probe15_verify_wrong_serve_fixed():
    t0 = time.monotonic()
    r = solve_question(PROBE15)
    dt = time.monotonic() - t0
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]
    # the nonsense class is gone: no solving for a letter
    assert "(y - 1)^(1/x)" not in r["answer"]
    assert not r["answer"].startswith("e =")
    # the differentiation steps are shown
    joined = " ".join(r["steps"])
    assert "y' = exp(x)" in joined, joined
    assert "y'' = exp(x)" in joined, joined
    assert dt < 4.0, dt


# ---------------------------------------------------------------------------
# (a) Bracket + dy/dx dress variants
# ---------------------------------------------------------------------------

def test_bracket_separable():
    r = solve_question(
        "Find the general solution of the differential "
        "equation x dy = e^y dx")
    assert r["op"] == "differential_equation", r
    assert_implicit_solution(r["answer"], sp.exp(_Y) / _X)


def test_bracket_homogeneous_variant():
    r = solve_question(
        "Find the general solution of the differential "
        "equation x dy = (x + y) dx")
    assert r["op"] == "differential_equation", r
    assert_implicit_solution(r["answer"],
                             (_X + _Y) / _X)


def test_bracket_reversed_orientation():
    r = solve_question(
        "Find the general solution of the differential "
        "equation (x^2 + y^2) dx = (x^2 + xy) dy")
    assert r["op"] == "differential_equation", r
    assert_implicit_solution(r["answer"], F14)


def test_dydx_separable():
    r = solve_question(
        "Find the general solution of the differential "
        "equation dy/dx = e^(x+y)")
    assert r["op"] == "differential_equation", r
    assert_implicit_solution(r["answer"],
                             sp.exp(_X + _Y))


def test_dydx_linear():
    r = solve_question(
        "Find the general solution of dy/dx + y = e^x")
    assert r["op"] == "differential_equation", r
    assert_explicit_solution(r["answer"], sp.exp(_X) - _Y)


def test_dydx_linear_coefficient_on_derivative():
    r = solve_question(
        "Find the general solution of the differential "
        "equation x dy/dx + 2y = x^2")
    assert r["op"] == "differential_equation", r
    assert_explicit_solution(
        r["answer"], _X - 2 * _Y / _X)


def test_unsolvable_de_declines_not_guesses():
    # dy/dx = x + sin y is none of homogeneous /
    # separable / linear: the module must decline
    # (fallback chain's job), never force a serve.
    assert solve_diffeq194(
        "Find the general solution of the differential "
        "equation dy/dx = x + sin y") is None


# ---------------------------------------------------------------------------
# (b) Verify-the-solution variants
# ---------------------------------------------------------------------------

def test_verify_true_second_order():
    r = solve_question(
        "Verify that y = cos x is a solution of the "
        "differential equation y'' + y = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]


def test_verify_true_first_order_dydx_dress():
    r = solve_question(
        "Verify that y = e^(-x) is a solution of the "
        "differential equation dy/dx + y = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]


def test_verify_false_computed_verdict():
    r = solve_question(
        "Verify that y = e^x + 1 is a solution of the "
        "differential equation y'' + y' = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("No"), r["answer"]
    # both sides shown: the computed difference is 2 e^x
    assert "2·exp(x)" in r["answer"], r["answer"]


def test_verify_without_differential_equation_phrase():
    r = solve_question(
        "Verify that y = e^x + 1 is a solution of "
        "y'' - y' = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]


def test_verify_show_that_dress():
    r = solve_question(
        "Show that y = sin x is a solution of the "
        "differential equation y'' + y = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]


def test_verify_with_arbitrary_constants():
    r = solve_question(
        "Verify that y = A cos x + B sin x is a solution "
        "of the differential equation y'' + y = 0")
    assert r["op"] == "de_verification", r
    assert r["answer"].startswith("Yes"), r["answer"]


def test_verify_algebra_question_not_hijacked():
    # "x = 4 is a solution of 2x + 3 = 11" is algebra's
    # verify dress (no derivative token, no DE): the
    # Wave 194 schema must decline and the primary
    # answer must stand byte-identical.
    assert verify_solution_result(
        "Verify that x = 4 is a solution of "
        "2x + 3 = 11") is None
    r = solve_question(
        "Verify that x = 4 is a solution of 2x + 3 = 11")
    assert r["op"] == "equation", r
    assert r["answer"] == "x = 4", r


# ---------------------------------------------------------------------------
# Controls — outcomes measured on main BEFORE this wave
# ---------------------------------------------------------------------------

def test_control_order_degree():
    r = solve_question(
        "Find the order and degree of the differential "
        "equation (d^2y/dx^2)^3 + (dy/dx)^2 + "
        "sin(dy/dx) + 1 = 0")
    assert r["op"] == "ode_order_degree", r
    assert r["answer"] == "Order = 2, Degree = 3", r
    r = solve_question(
        "Find the order and degree of the differential "
        "equation (dy/dx)^2 + (d^2y/dx^2) = 0")
    assert r["answer"] == "Order = 2, Degree = 1", r


def test_control_primary_dydx_solve():
    r = solve_question("Solve dy/dx = y/x")
    assert r["op"] == "differential_equation", r
    assert r["answer"] == "y = C1·x", r


def test_control_depth125_homogeneous_dresses():
    r = solve_question(
        "Find the general solution of the differential "
        "equation dy/dx = (x + y)/x")
    assert r["answer"] == "y = x·(C1 + log(x))", r
    r = solve_question("dy/dx = (x + y)/x ko hal karo")
    assert r["answer"] == "y = x·(C1 + log(x))", r


def test_control_coefficient_dress_primary():
    r = solve_question(
        "Solve the differential equation "
        "(x^2 - 1) dy/dx = 1")
    assert r["answer"] == (
        "y = C1 + log(x - 1)/2 - log(x + 1)/2"), r


def test_control_plain_differentiation_untouched():
    r = solve_question(
        "Differentiate e^x + 1 with respect to x")
    assert r["op"] == "derivative", r
    assert r["answer"] == "exp(x)", r


def test_control_implicit_differentiation_not_claimed():
    # "Find dy/dx if ..." is Wave 186's dress, not a DE
    # solve ask: the module declines it outright.
    assert solve_diffeq194(
        "Find dy/dx if 2x + 3y = sin x") is None
