"""Wave 209 — real step-by-step working for differential
equations.

The DE producers serve verified answers with SUMMARY
steps (depth125's dsolve fallback: "Solving the
differential equation ... gives the general solution:";
calculus's dsolve path: "Solve with SymPy's dsolve —
it classifies the equation ...").  Wave 209's
enrich_de_steps post-pass (fallback.with_fallback)
re-derives the textbook working — direct integration,
homogeneous (y = vx), variable separable, linear
(integrating factor), z = x ± y substitution — verifies
it three ways (the served answer satisfies the ODE;
the derived relation is a true first integral; the
relation is constant along the served solution) and
only then swaps the steps.  The answer is never
touched.

The expected answers below were recorded from the
pre-wave tree (Deploy-52) and hand-verified; the
regression test pins them byte-identical while the
steps change underneath.
"""
import pytest

from api import _solve_friendly
from solver.wave209 import enrich_de_steps


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Chat-path tests run against a throwaway live-bank
    DB (the test_wave117 seam), so no suite-order row
    can be re-served into an assertion."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "w209.db"))
    from solver.answer_cache import (clear_cache,
                                     clear_negative_cache)
    clear_cache()
    clear_negative_cache()
    yield


def _solve(q):
    res = _solve_friendly(q)
    assert res is not None
    return res


def _steps(res):
    return [str(s) for s in (res.get("steps") or [])]


# --- The headline case ---------------------------------------------

HEADLINE = ("Find the general solution of the "
            "differential equation: "
            "dy/dx = (1+x^2)(1+y^2)")


def test_headline_gets_real_separable_steps():
    res = _solve(HEADLINE)
    assert res.get("op") == "differential_equation"
    assert res.get("answer") == "y = tan(C1 + x^3/3 + x)"
    steps = _steps(res)
    assert len(steps) >= 3
    assert steps[0].startswith("Separate the variables")
    assert "dy/(y^2 + 1) = (x^2 + 1) dx" in steps[0]
    assert "atan(y) = x^3/3 + x + C" in steps[1]
    assert steps[-1] == ("So the general solution is: "
                         "y = tan(C1 + x^3/3 + x).")
    joined = "\n".join(steps)
    assert "dsolve" not in joined
    assert "gives the general solution" not in joined


# --- Families: >= 2 per family, hand-verified answers --------------
# separable: dy/y = x dx -> log y = x^2/2 + C
# separable: (y+2) dy = (x+1) dx -> (y+2)^2 = (x+1)^2 + C
# separable: dy/y = dx/x -> y = C x
# separable (Bernoulli dress): dy/(y^2-y) = dx
#   -> log((y-1)/y) = x + C -> y = C1/(C1 - e^x)

SEPARABLE = [
    ("Solve dy/dx = xy", "y = C1·exp(x^2/2)"),
    ("Find the general solution of dy/dx = (x + 1)/(y + 2)",
     "y = -sqrt(C1 + x^2 + 2·x) - 2"),
    ("dy/dx = y/x", "y = C1·x"),
    ("Solve dy/dx + y = y^2", "y = C1/(C1 - exp(x))"),
]

# homogeneous: y = vx; (x+y)/x -> v = log x + C
# homogeneous: (x^2+y^2)/(2xy) -> -log(v^2-1) = log x + C
#   -> y^2 = x^2 + C x (served branch: negative root)

HOMOGENEOUS = [
    ("Solve the differential equation dy/dx = (x+y)/x",
     "y = x·(C1 + log(x))"),
    ("Solve dy/dx = (x^2 + y^2)/(2xy)",
     "y = -sqrt(x·(C1 + x))"),
]

# linear: IF = sec x -> y sec x = tan x + C
# linear: standard form dy/dx + (2/x) y = x, IF = x^2
#   -> y x^2 = x^4/4 + C

LINEAR = [
    ("Solve dy/dx + y tan x = sec x",
     "y = C1·cos(x) + sin(x)"),
    ("Solve x dy/dx + 2y = x^2", "y = (C1 + x^4/4)/x^2"),
]

# direct: y = integral of the right side + C

DIRECT = [
    ("Solve dy/dx = x^2 + 3x", "y = C1 + x^3/3 + 3·x^2/2"),
    ("Find the general solution of dy/dx = cos x",
     "y = C1 + sin(x)"),
]

# substitution z = x + y: dz/(1 + cos z) = dx
#   -> tan(z/2) = x + C -> y = -x + 2 atan(C1 + x)

SUBSTITUTION = [
    ("Solve dy/dx = cos(x + y)", "y = -x + 2·atan(C1 + x)"),
]


@pytest.mark.parametrize("q,expected", SEPARABLE)
def test_separable_family(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
    steps = _steps(res)
    assert len(steps) >= 3
    assert "Separate the variables" in steps[0]
    assert "Integrating both sides" in steps[1]
    assert steps[-1].endswith(expected + ".")


@pytest.mark.parametrize("q,expected", HOMOGENEOUS)
def test_homogeneous_family(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
    steps = _steps(res)
    assert len(steps) >= 5
    assert steps[0].startswith("Check: f(tx, ty)")
    assert "Put y = vx" in steps[1]
    assert steps[-1].endswith(expected + ".")


@pytest.mark.parametrize("q,expected", LINEAR)
def test_linear_family(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
    steps = _steps(res)
    assert len(steps) >= 4
    assert steps[0].startswith("This is linear in y")
    assert "Integrating factor IF" in steps[1]
    assert steps[-1].endswith(expected + ".")


@pytest.mark.parametrize("q,expected", DIRECT)
def test_direct_family(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
    steps = _steps(res)
    assert len(steps) >= 3
    assert "depends only on x" in steps[0]
    assert steps[-1].endswith(expected + ".")


@pytest.mark.parametrize("q,expected", SUBSTITUTION)
def test_substitution_family(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
    steps = _steps(res)
    assert len(steps) >= 5
    assert steps[0].startswith("Put z = x + y")
    assert steps[-1].endswith(expected + ".")


def test_particular_solution_gets_working_and_constant():
    res = _solve("dy/dx = (1+x^2)(1+y^2), y(0) = 0")
    assert res.get("answer") == "y = tan(x^3/3 + x)"
    steps = _steps(res)
    assert len(steps) >= 4
    assert "Separate the variables" in steps[0]
    assert "C = 0" in steps[-2]
    assert steps[-1] == ("Particular solution: "
                         "y = tan(x^3/3 + x).")


# --- Untouched serves ------------------------------------------------

def test_piecewise_garbage_answer_left_untouched():
    # Wave 209 era: dsolve read "e" as a symbol and
    # served a Piecewise form, and this test pinned
    # that serve standing untouched (the enrich pass
    # refuses Piecewise answers — see the unit gate
    # test_enrich_refuses_piecewise_answer below).
    # Wave 210 fixed the producer (calculus._ode folds
    # e to Euler's number), so the pipeline now serves
    # the verified solution and the enrich pass gives
    # it real steps; the pin follows the fixed serve.
    res = _solve("Solve the differential equation "
                 "dy/dx + y = e^x")
    assert "Piecewise" not in str(res.get("answer"))
    assert res.get("answer") == \
        "y = C1·exp(-x) + exp(x)/2"
    assert any("Integrating factor" in s
               for s in _steps(res))


def test_second_order_left_untouched():
    res = _solve("Solve y'' + y = 0")
    assert res.get("answer") == \
        "y = C1·sin(x) + C2·cos(x)"
    assert any("dsolve" in s for s in _steps(res))


def test_already_real_steps_left_untouched():
    # depth125's homogeneous branch already writes the
    # method out; the implicit serve must not change.
    res = _solve("Solve dy/dx = (y - x)/(y + x)")
    assert res.get("answer") == (
        "-log(x) - log(1 + y^2/x^2)/2 - atan(y/x) = C")
    steps = _steps(res)
    assert steps[0].startswith("Check: f(tx, ty)")


# --- enrich_de_steps unit gates --------------------------------------

_SUMMARY_RESULT = {
    "type": "calculus",
    "op": "differential_equation",
    "answer": "y = tan(C1 + x^3/3 + x)",
    "steps": [
        "Solving the differential equation "
        "dy/dx = (x^2 + 1)·(y^2 + 1) gives the general "
        "solution:",
        "y = tan(C1 + x^3/3 + x) (C is an arbitrary "
        "constant).",
    ],
}


def test_enrich_unit_headline_and_no_mutation():
    import copy
    original = copy.deepcopy(_SUMMARY_RESULT)
    out = enrich_de_steps(HEADLINE, _SUMMARY_RESULT)
    assert out is not None
    assert out["answer"] == original["answer"]
    assert len(out["steps"]) >= 3
    assert out["steps"][0].startswith(
        "Separate the variables")
    # the input dict (possibly a cached result) is
    # never mutated
    assert _SUMMARY_RESULT == original


def test_enrich_unit_hindi_steps():
    out = enrich_de_steps(
        "अवकल समीकरण dy/dx = (1+x^2)(1+y^2) हल कीजिए",
        dict(_SUMMARY_RESULT))
    assert out is not None
    steps = out["steps"]
    assert "चरों को अलग कीजिए" in steps[0]
    assert steps[-1].startswith("अतः व्यापक हल")


def test_enrich_refuses_wrong_answer():
    bad = dict(_SUMMARY_RESULT)
    bad["answer"] = "y = x + C1"
    assert enrich_de_steps(HEADLINE, bad) is None


def test_enrich_refuses_piecewise_answer():
    bad = dict(_SUMMARY_RESULT)
    bad["answer"] = "y = Piecewise((C1, True))"
    assert enrich_de_steps(HEADLINE, bad) is None


def test_enrich_ignores_non_de_and_real_steps():
    assert enrich_de_steps(
        HEADLINE, {"op": "algebra", "answer": "y = x",
                   "steps": ["a", "b"]}) is None
    real = dict(_SUMMARY_RESULT)
    real["steps"] = [
        "Separate the variables: dy/(y^2 + 1) = "
        "(x^2 + 1) dx.",
        "Integrating both sides: atan(y) = x^3/3 + x "
        "+ C.",
        "So the general solution is: "
        "y = tan(C1 + x^3/3 + x).",
    ]
    assert enrich_de_steps(HEADLINE, real) is None
    tex = dict(_SUMMARY_RESULT)
    tex["steps_tex"] = ["a", "b"]
    assert enrich_de_steps(HEADLINE, tex) is None


# --- Regression: answers byte-identical to the old serves ------------

OLD_SERVES = [
    (HEADLINE, "y = tan(C1 + x^3/3 + x)"),
    ("Solve dy/dx = xy", "y = C1·exp(x^2/2)"),
    ("Find the general solution of dy/dx = (x + 1)/(y + 2)",
     "y = -sqrt(C1 + x^2 + 2·x) - 2"),
    ("dy/dx = y/x", "y = C1·x"),
    ("Solve dy/dx + y = y^2", "y = C1/(C1 - exp(x))"),
    ("Solve the differential equation dy/dx = (x+y)/x",
     "y = x·(C1 + log(x))"),
    ("Solve dy/dx = (x^2 + y^2)/(2xy)",
     "y = -sqrt(x·(C1 + x))"),
    ("Solve dy/dx + y tan x = sec x",
     "y = C1·cos(x) + sin(x)"),
    ("Solve x dy/dx + 2y = x^2", "y = (C1 + x^4/4)/x^2"),
    ("Solve dy/dx = x^2 + 3x", "y = C1 + x^3/3 + 3·x^2/2"),
    ("Find the general solution of dy/dx = cos x",
     "y = C1 + sin(x)"),
    ("Solve dy/dx = cos(x + y)", "y = -x + 2·atan(C1 + x)"),
    ("dy/dx = (1+x^2)(1+y^2), y(0) = 0",
     "y = tan(x^3/3 + x)"),
    ("Solve dy/dx = (y - x)/(y + x)",
     "-log(x) - log(1 + y^2/x^2)/2 - atan(y/x) = C"),
    ("Solve y'' + y = 0", "y = C1·sin(x) + C2·cos(x)"),
]


@pytest.mark.parametrize("q,expected", OLD_SERVES)
def test_answers_byte_identical_to_old_serves(q, expected):
    res = _solve(q)
    assert res.get("answer") == expected
