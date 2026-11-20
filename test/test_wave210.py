"""Wave 210 — differential-equation routing repairs.

Three measured routing bugs (Wave 209 survey):

  1. "e" read as a free symbol instead of Euler's
     number: "dy/dx = e^(x+y)" and "Solve dy/dx + y =
     e^x" served dsolve Piecewise forms conditioned on
     Eq(e, exp(-1)); the bare dress "dy/dx + y = e^x"
     was claimed by dydx186's early gate (and, behind
     it, c12gaps142's upgrade) as an implicit-
     differentiation ask and served exp(x).
  2. "Find the general solution of dy/dx + y/x = x^2"
     served op=equation — the dy/dx-stripped fragment
     solved FOR x — although diffeq194 settles it
     directly; the failure-only gates never fired
     because the equation result wears a "real" op.
  3. The initial-condition dresses "... given
     y(0) = 0" and "... where y = 1 when x = 0"
     returned not_found although depth125 settles
     both directly.

Expected answers below are hand-derived and, for the
general solutions, re-verified inside the tests by
differentiating the SERVED answer back against the
ODE numerically.  The regression pins are the
recorded pre-wave (Deploy-52 + Wave 209) serves,
byte-identical.
"""
import sympy as sp
import pytest
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor)

from api import _solve_friendly

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application, convert_xor)
_x, _y, _C1, _C2 = sp.symbols("x y C1 C2")
_LOCALS = {"x": _x, "y": _y, "C1": _C1, "C2": _C2}


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Same seam as test_wave209: a throwaway live-bank
    DB so no suite-order row can be re-served into an
    assertion."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "w210.db"))
    from solver.answer_cache import (clear_cache,
                                     clear_negative_cache)
    clear_cache()
    clear_negative_cache()
    yield


def _solve(q):
    res = _solve_friendly(q)
    assert res is not None
    return res


def _parse(text):
    return parse_expr(str(text).replace("·", "*"),
                      local_dict=_LOCALS,
                      transformations=_TRANSFORMS)


def _assert_solves(answer, f_text, consts, xs=(0.4, 1.1),
                   ic=None):
    """The served "y = ..." really solves dy/dx = f:
    differentiate the parsed answer back and compare
    against f(x, y(x)) numerically (complex-safe)."""
    assert str(answer).startswith("y =")
    ysol = _parse(str(answer).split("=", 1)[1])
    f = _parse(f_text)
    subs = dict(consts)
    for x0 in xs:
        s = {**subs, _x: x0}
        got = complex(sp.diff(ysol, _x).subs(s))
        want = complex(f.subs({_y: ysol}).subs(s))
        assert abs(got - want) < 1e-6, (answer, x0, got,
                                        want)
    if ic is not None:
        x0, y0 = ic
        got = complex(ysol.subs({**subs, _x: x0}))
        assert abs(got - y0) < 1e-9, (answer, ic, got)


# --- Bug 1: e is Euler's number in a DE ----------------

def test_bug1_separable_e_power_no_piecewise():
    res = _solve("dy/dx = e^(x+y)")
    assert res["op"] == "differential_equation"
    assert "Piecewise" not in res["answer"]
    assert "log(e)" not in res["answer"]
    _assert_solves(res["answer"], "exp(x + y)",
                   {_C1: -3})


def test_bug1_linear_e_rhs_solve_dress():
    res = _solve("Solve dy/dx + y = e^x")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = C1·exp(-x) + exp(x)/2"
    _assert_solves(res["answer"], "exp(x) - y",
                   {_C1: 2})


def test_bug1_linear_e_rhs_bare_dress():
    # The dydx186 / c12gaps142 misclaim: this used to
    # serve implicit_dydx "exp(x)".
    res = _solve("dy/dx + y = e^x")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = C1·exp(-x) + exp(x)/2"


def test_bug1_ode_unit_fold():
    from solver.calculus import _ode
    for q in ("dy/dx = e^(x+y)", "dy/dx + y = e^x"):
        out = _ode(q)
        assert out is not None
        assert "Piecewise" not in out["answer"]
        assert "log(e)" not in out["answer"]


def test_bug1_dydx186_declines_de_shapes():
    from solver.dydx186 import solve_dydx186
    assert solve_dydx186("dy/dx + y = e^x") is None
    assert solve_dydx186("dy/dx + y/x = x^2") is None
    assert solve_dydx186("x dy/dx + 2y = x^2") is None


def test_bug1_c12gaps142_upgrade_keeps_de_serve():
    from solver.c12gaps142 import c12gaps142_upgrade
    served = {"op": "differential_equation",
              "answer": "y = C1·exp(-x) + exp(x)/2",
              "steps": []}
    assert c12gaps142_upgrade("dy/dx + y = e^x",
                              served) is None


def test_bug1_e_stays_a_variable_in_algebra():
    # The fold is scoped to DE parsers: elsewhere 'e'
    # is an ordinary letter and its serves must not
    # move.
    res = _solve("Solve 3e + 5 = 20")
    assert res["op"] == "equation"
    assert res["answer"] == "e = 5"


def test_bug1_new_serves_get_real_steps():
    # Wave 209's enrich pass picks the repaired serves
    # up (its re-parse folds e the same way).
    res = _solve("dy/dx = e^(x+y)")
    steps = [str(s) for s in res.get("steps") or []]
    assert any("Separate the variables" in s
               for s in steps)
    res = _solve("Solve dy/dx + y = e^x")
    steps = [str(s) for s in res.get("steps") or []]
    assert any("Integrating factor" in s for s in steps)


# --- Bug 2: dy/dx + y/x = x^2 reaches the DE solver ---

def test_bug2_general_solution_dress():
    res = _solve("Find the general solution of "
                 "dy/dx + y/x = x^2")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = (C1 + x^4/4)/x"
    _assert_solves(res["answer"], "x**2 - y/x",
                   {_C1: 2})


def test_bug2_bare_dress():
    res = _solve("dy/dx + y/x = x^2")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = (C1 + x^4/4)/x"


def test_bug2_coefficient_dress():
    res = _solve("x dy/dx + 2y = x^2")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = (C1 + x^4/4)/x^2"
    _assert_solves(res["answer"], "x - 2*y/x",
                   {_C1: 2})


def test_bug2_second_linear_e_dress():
    res = _solve("dy/dx + 2y = e^x")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = C1·exp(-2·x) + exp(x)/3"
    _assert_solves(res["answer"], "exp(x) - 2*y",
                   {_C1: 2})


# --- Bug 3: initial-condition dresses serve -----------

def test_bug3_ic_given_dress():
    res = _solve("Find the particular solution of "
                 "dy/dx = (1+x^2)(1+y^2) given y(0) = 0")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = tan(x^3/3 + x)"


def test_bug3_ic_where_dress():
    res = _solve("Solve dy/dx = xy where y = 1 "
                 "when x = 0")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = exp(x^2/2)"


def test_bug3_ic_implicit_dress():
    res = _solve("Find the particular solution of "
                 "dy/dx + y/x = x^2 given y(1) = 1")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "y = (x^4/4 + 3/4)/x"
    _assert_solves(res["answer"], "x**2 - y/x", {},
                   ic=(1, 1))


def test_bug3_ic_e_dress():
    res = _solve("Find the particular solution of "
                 "dy/dx = e^(x+y) given y(0) = 0")
    assert res["op"] == "differential_equation"
    _assert_solves(res["answer"], "exp(x + y)", {},
                   ic=(0, 0))


def test_bug3_de_extract_where_rhs():
    from solver.depth125 import _de_extract
    got = _de_extract("Solve dy/dx = xy where y = 1 "
                      "when x = 0")
    assert got is not None
    rhs, ic = got
    assert rhs == "xy"
    assert ic == (0, 1)


# --- Gate discipline -----------------------------------

def test_gate_standing_de_serve_untouched():
    from solver.wave210 import solve_wave210
    standing = {"op": "differential_equation",
                "answer": "y = log(-1/(C1 + exp(x)))",
                "steps": ["..."]}
    assert solve_wave210("dy/dx = e^(x+y)",
                         standing) is None


def test_gate_piecewise_serve_displaced():
    from solver.wave210 import solve_wave210
    standing = {
        "op": "differential_equation",
        "answer": "y = Piecewise((log(-C1·x - "
                  "C1/log(e))/log(e), Ne(log(e), 0) & "
                  "Eq(C1·x·log(e) + C1, 0)), (nan, "
                  "True))",
        "steps": []}
    out = solve_wave210("dy/dx = e^(x+y)", standing)
    assert out is not None
    assert out["op"] == "differential_equation"
    assert "Piecewise" not in out["answer"]


def test_gate_declines_owned_dresses():
    from solver.wave210 import solve_wave210
    assert solve_wave210(
        "What is the order of the differential "
        "equation dy/dx + y = e^x?",
        {"op": "ode_order", "answer": "1"}) is None
    assert solve_wave210(
        "Verify that y = e^x + 1 is a solution of "
        "dy/dx = e^x",
        {"op": "de_verification", "answer": "Yes"}) \
        is None
    assert solve_wave210(
        "solve 2x + 3 = 7",
        {"op": "equation", "answer": "x = 2"}) is None
    assert solve_wave210(
        "Find dy/dx if 2x + 3y = sin x",
        {"op": "implicit_dydx",
         "answer": "cos(x)/3 - 2/3"}) is None


# --- Regression pins: neighbouring serves unchanged ---

def test_regression_headline_separable():
    res = _solve("Find the general solution of "
                 "dy/dx = (1+x^2)(1+y^2)")
    assert res["answer"] == "y = tan(C1 + x^3/3 + x)"


def test_regression_dressed_e_implicit_serve():
    # diffeq194's implicit-form serve for this dress
    # was already correct and must stand byte-identical.
    res = _solve("Find the general solution of "
                 "dy/dx = e^(x+y)")
    assert res["op"] == "differential_equation"
    assert res["answer"] == "exp(x) + exp(-y) = C"


def test_regression_direct_integration():
    res = _solve("dy/dx = cos x")
    assert res["answer"] == "y = C1 + sin(x)"


def test_regression_coefficient_solve_dress():
    res = _solve("Solve x dy/dx + 2y = x^2")
    assert res["answer"] == "y = (C1 + x^4/4)/x^2"


def test_regression_ic_comma_dress():
    res = _solve("Find the particular solution of "
                 "dy/dx = (1+x^2)(1+y^2), y(0) = 0")
    assert res["answer"] == "y = tan(x^3/3 + x)"


def test_regression_implicit_diff_ask():
    res = _solve("Find dy/dx if 2x + 3y = sin x")
    assert res["op"] == "implicit_dydx"
    assert res["answer"] == "cos(x)/3 - 2/3"


def test_regression_log_implicit_ask():
    res = _solve("Find dy/dx if x^y + y^x = 1")
    assert res["op"] == "log_implicit_dydx"


def test_regression_plain_equation():
    res = _solve("solve 2x + 3 = 7")
    assert res["op"] == "equation"
    assert res["answer"] == "x = 2"


def test_regression_order_ask():
    res = _solve("What is the order of the "
                 "differential equation dy/dx + y = e^x?")
    assert res["op"] == "ode_order"
    assert res["answer"] == "1"
