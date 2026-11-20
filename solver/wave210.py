"""Wave 210: differential-equation ROUTING repairs
(20 Nov 2026).

Wave 209's survey found three DE shapes whose answers
never reach a DE solver, or reach one that misreads
them.  Each was measured through the real pipeline
before this wave:

  1. "e" read as a free SYMBOL instead of Euler's
     number.  calculus._ode parsed e^(x+y) / e^x with
     the letter e as a parameter, so dsolve served
     Piecewise forms conditioned on Eq(e, exp(-1)) /
     Ne(log(e), 0) for the textbook asks
     "dy/dx = e^(x+y)" and "Solve dy/dx + y = e^x";
     depth125._de_solve declined the same dresses at
     its free-symbol gate.  The producer fixes live in
     calculus._ode (_fold_euler at its parse sites) and
     depth125._de_solve (fold before the gate) — the
     diffeq194 _parse precedent, scoped to DE parsers
     only; algebra keeps 'e' as an ordinary letter.
     The BARE dress "dy/dx + y = e^x" never even
     reached _ode: dydx186's early gate ate the dy/dx
     token as dress and served the implicit relation
     y = e^x's derivative, exp(x).  dydx186 now
     declines a dy/dx that is an operand of an
     equation (an operator / "=" adjacent to it).

  2. "Find the general solution of dy/dx + y/x = x^2"
     served op=equation — the primary chain solved
     the dy/dx-stripped fragment "+ y/x = x^2" FOR x
     ("x = y^(1/3), ..."), the fallback salvage then
     served that fragment solve.  diffeq194 settles
     the question directly (y = (C1 + x^4/4)/x), but
     it sits behind the router's failure-only gate
     and _w77_needs_core calls an equation-op result
     a genuine answer, so the gate never fired.  The
     bare dress was ALSO misclaimed by dydx186 (see
     1) and is fixed by the same decline.

  3. Two initial-condition dresses returned not_found
     although depth125 settles them directly:
     "Find the particular solution of
     dy/dx = (1+x^2)(1+y^2) given y(0) = 0" (primary
     result: op=equation, "The equation has no
     variable to solve for." — again invisible to the
     failure gate, and fallback's depth125_upgrade
     sits inside its _is_real branch, which these
     results never enter) and "Solve dy/dx = xy where
     y = 1 when x = 0" (primary: "y = 1" — the IC
     fragment solved as an equation; _de_extract also
     left the rhs reading "xy where", fixed in
     depth125's wrapper-word list).

Fix shape (this module + two router blocks modelled
on the Wave 194 verify-solution repair at the same
seams — one inside the Wave 77 core branch, beside
the w194v / w195c checks, where the fragment solve
would otherwise return first; one at the tail of
_solve_question_uncached, after Wave 207, for results
that never enter the core branch): a REPAIR gate —
it runs whether or not the failure gate fired,
because these results wear "real" ops.  It fires
only when ALL of these hold:

  * the question is strictly DE-shaped: a first-order
    dy/dx that is an operand of an equation (operator
    / "=" adjacent), one "=", and none of the dresses
    owned elsewhere (order / degree asks, integrating-
    factor fact asks, verify / prove / show-that
    dresses, MCQ option sets, second-order forms);
  * the standing result is NOT already a
    differential_equation serve — except a Piecewise /
    nan-shaped one, which is the bug-1 signature and
    may be displaced (producer-fixed in _ode; this is
    the net for any other producer);
  * a candidate settles the question, tried in order:
    diffeq194 (textbook steps), depth125._de_solve
    (verified homogeneous / IC / dsolve machinery),
    and last a strict implicit-dress solve of this
    module (Wave 209's extractor -> bounded dsolve ->
    checkodesol + IC verification, depth125's own
    discipline).  The candidate's answer must differ
    from the standing one.

Every other result stands byte-identical.  The whole
candidate chain runs inside one 6 s bounded worker
thread (the Wave-46 / Wave-209 pattern); any doubt,
timeout or exception returns None.
"""
import re
import threading

import sympy as sp

from .depth125 import _de_solve, _hindi, _mk, _prep
from .diffeq194 import solve_diffeq194
from .expression_parser import fmt
from .wave209 import _extract as _w209_extract
from .wave209 import _verify_answer as _w209_verify

_x = sp.symbols("x")
_y = sp.symbols("y")
_e_sym = sp.symbols("e")

_BUDGET_SECONDS = 6.0

# A dy/dx that is an OPERAND of an equation — the same
# adjacency test dydx186 now declines by.
_DE_SHAPE = re.compile(
    r"[-+*/=^]\s*dy\s*/\s*dx|dy\s*/\s*dx\s*[-+*/=^)]")

# Dresses owned by other layers: never re-route them.
_DECLINE = re.compile(
    r"\border\b|\bdegree\b|integrating\s+factor|"
    r"\bverify\b|\bprove\b|show\s+that|"
    r"check\s+whether|is\s+a\s+solution\s+of",
    re.I)


def _de_shaped(question):
    s = str(question or "")
    if "d2y" in s or "y''" in s or 'y"' in s:
        return False
    if not re.search(r"dy\s*/\s*dx", s):
        return False
    if "=" not in s:
        return False
    if not _DE_SHAPE.search(s):
        return False
    if _DECLINE.search(s):
        return False
    # An MCQ stem belongs to the MCQ authority layers.
    low = s.lower()
    if "(a)" in low and "(b)" in low:
        return False
    return True


def _standing_ok(result):
    """A standing differential_equation serve is never
    displaced — except the bug-1 signature itself: a
    Piecewise / nan answer, which is not a solution a
    student can use."""
    if not isinstance(result, dict):
        return False
    if result.get("op") != "differential_equation":
        return False
    ans = str(result.get("answer") or "")
    if "Piecewise" in ans or "nan" in ans:
        return False
    return True


def _implicit_solve(q):
    """Last-resort candidate for the implicit dress
    ("dy/dx + P y = Q", "A(x) dy/dx + ... = ...",
    with or without an initial condition) that
    diffeq194's and depth125's extractors both decline:
    Wave 209's strict dress extraction -> bounded
    dsolve -> the house verification (checkodesol +
    differentiate-back, plus the IC check) before
    anything is served.  Steps mirror depth125's own
    dsolve-fallback wording, so Wave 209's enrich pass
    recognises them as summary-styled and re-derives
    the real working in fallback."""
    got = _w209_extract(q)
    if got is None:
        return None
    f, ic = got
    if _e_sym in f.free_symbols:
        f = f.subs(_e_sym, sp.E)
    if f.free_symbols - {_x, _y}:
        return None
    hi = _hindi(q)
    yf = sp.Function("y")(_x)
    eq = sp.Eq(yf.diff(_x), f.subs(_y, yf))
    try:
        if ic is not None:
            sol = sp.dsolve(eq, yf,
                            ics={yf.subs(_x, ic[0]): ic[1]})
        else:
            sol = sp.dsolve(eq, yf)
        if isinstance(sol, list):
            sol = sol[0] if sol else None
    except Exception:
        return None
    if sol is None or sol.rhs.has(yf):
        return None
    if not _w209_verify(f, sol.rhs, ic):
        return None
    ans = "y = " + fmt(sol.rhs)
    if ic is not None:
        steps = ([
            f"दिया गया अवकल समीकरण: dy/dx = {fmt(f)}।",
            f"प्रारंभिक शर्त y = {fmt(ic[1])} जब "
            f"x = {fmt(ic[0])} रखकर व्यापक हल से C "
            "ज्ञात करते हैं।",
            f"अतः अभीष्ट विशेष हल: y = {fmt(sol.rhs)}।",
        ] if hi else [
            f"The differential equation is "
            f"dy/dx = {fmt(f)}.",
            f"Solving it and fixing the constant from "
            f"the condition y = {fmt(ic[1])} when "
            f"x = {fmt(ic[0])} gives the particular "
            "solution.",
            f"Particular solution: y = {fmt(sol.rhs)}.",
        ])
    else:
        steps = ([
            f"अवकल समीकरण dy/dx = {fmt(f)} को हल करने पर "
            "व्यापक हल मिलता है:",
            f"y = {fmt(sol.rhs)} (C स्वेच्छ अचर है)।",
        ] if hi else [
            f"Solving the differential equation "
            f"dy/dx = {fmt(f)} gives the general solution:",
            f"y = {fmt(sol.rhs)} (C is an arbitrary "
            "constant).",
        ])
    return _mk("calculus", "differential_equation", ans,
               steps, latex=sp.latex(sp.Eq(_y, sol.rhs)))


def _candidate(q):
    for fn in (solve_diffeq194, _de_solve, _implicit_solve):
        try:
            out = fn(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


def solve_wave210(question, result=None):
    """The verified DE result for a misrouted DE-shaped
    question, or None — see the module docstring for
    the exact gates.  `result` is the standing primary
    result the router is about to serve."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not _de_shaped(q):
        return None
    if _standing_ok(result):
        return None
    box = {}

    def _run():
        try:
            box["out"] = _candidate(q)
        except BaseException:  # never leak into the chain
            box["out"] = None

    worker = threading.Thread(target=_run, daemon=True,
                              name="ganitra-wave210")
    worker.start()
    worker.join(_BUDGET_SECONDS)
    if worker.is_alive():
        return None
    cand = box.get("out")
    if cand is None:
        return None
    if isinstance(result, dict) and \
            str(cand.get("answer", "")).strip() == \
            str(result.get("answer", "")).strip():
        return None
    return cand
