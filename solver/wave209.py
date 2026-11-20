"""Wave 209: real step-by-step working for differential
equations (20 Nov 2026).

The Deploy-52 visual check caught the full solution page
showing ONE summary line for "Find the general solution
of dy/dx = (1+x^2)(1+y^2)":

    "Solving the differential equation
     dy/dx = (x^2 + 1)·(y^2 + 1) gives the general
     solution: y = tan(C1 + x^3/3 + x)"

The ANSWER is right; the working is missing.  Two
producers serve verified DE answers with summary steps:

  * solver/depth125.py's _de_solve fallback (anything
    dsolve solves that is neither homogeneous nor an IC
    ask): two lines — "Solving the differential equation
    ... gives the general solution:" + the answer.
  * solver/calculus.py's _ode (the primary dsolve path):
    three lines, the middle one literally "Solve with
    SymPy's dsolve — it classifies the equation ...".

(solver/diffeq194.py and depth125's homogeneous branch
already write real textbook steps; their serves carry
method lines and are never touched here.)

enrich_de_steps(question, result) is a serve-IMPROVING
post-pass, wired as one hook in fallback.with_fallback
(next to Wave 130's relanguage pass, so both routes —
chat and the classic page — see it, and the Live Bank
records what the student actually saw).  It fires only
when ALL of these hold:

  * the result is a differential_equation serve whose
    steps are summary-style (a summary marker line, or
    at most two steps) and carry no method line yet;
  * the answer is an explicit "y = ..." with exactly
    one arbitrary constant (none for a particular
    solution) and no Piecewise / stray symbols;
  * the question re-parses as a first-order dy/dx = f
    (depth125's extractor, or the strict implicit dress
    "dy/dx + P y = Q" / "A(x) dy/dx + ... = ..." below).

It then re-derives the textbook working for the family
the equation belongs to — direct integration,
homogeneous (y = vx), variable separable, linear
(integrating factor), or the z = x ± y substitution —
as an implicit relation R(x, y) = C, and serves the new
steps ONLY when every check passes, inside one bounded
worker thread (the router's Wave-46 budget pattern):

  1. the served answer satisfies the ODE — SymPy's
     checkodesol (depth125's own verifier), with a
     direct differentiate-and-simplify as back-up;
  2. the derived relation is a true first integral of
     the same equation (-R_x / R_y == f identically,
     depth125's _verify_implicit);
  3. the working lands on the served answer: R(x, y(x))
     is constant along the served solution (symbolic
     derivative; numeric sampling only as corroboration
     where a branch form like atan(tan u) defeats the
     symbolic simplifier);
  4. for an initial condition, the served particular
     solution also satisfies the condition, and the C
     the steps quote is R evaluated at the condition.

The answer and every other field are byte-identical —
only "steps" is replaced, on a copy of the dict.  Any
doubt, any timeout, any exception: None, and the serve
stands exactly as it was.  Second-order serves,
implicit-form answers (already real-stepped), and
answers that fail verification (e.g. the dsolve
Piecewise forms where "e" was read as a symbol) are
all left untouched.
"""
import re
import threading

import sympy as sp

from .depth125 import _de_extract, _hindi, _prep, \
    _verify_implicit
from .expression_parser import fmt, parse_expression

_x = sp.symbols("x")
_y = sp.symbols("y")
_e_sym = sp.symbols("e")


def _fold_e(expr):
    """Wave 210 companion: inside a differential
    equation 'e' is Euler's number (the diffeq194 _parse
    precedent).  Fold it at this module's two parse sites
    so the enrich pass can re-derive working for the
    e^(...) serves Wave 210 repaired — with 'e' left a
    symbol, the free-symbol gates below decline them and
    the summary steps would stand."""
    try:
        if hasattr(expr, "free_symbols") \
                and _e_sym in expr.free_symbols:
            return expr.subs(_e_sym, sp.E)
    except Exception:
        pass
    return expr

# One bounded worker for the whole derive + verify, the
# Wave-46 pattern: a normal school form finishes in
# milliseconds; the budget exists so no SymPy call this
# wave makes can ever hold a request open.
_BUDGET_SECONDS = 6.0
_MAX_OPS = 80  # diffeq194's cap, reused

_SUMMARY_MARKERS = (
    "gives the general solution",
    "Solve with SymPy",
    "dsolve",
    "fixing the constant from",
    "समाकलन करने पर व्यापक हल मिलता है",
)

_METHOD_MARKERS = (
    "Separate the variables",
    "Separating the variables",
    "Integrating factor",
    "Put y = vx",
    "Put z = x",
    "Integrate both sides",
    "Integrating both sides",
    "चरों को अलग",
    "समाकलन गुणक",
    "y = vx रखिए",
    "दोनों पक्षों का समाकलन",
)


# ------------------------------------------------------------------ #
# Gates (cheap, no SymPy)
# ------------------------------------------------------------------ #

def _summary_styled(result):
    steps = result.get("steps")
    if not isinstance(steps, list) or not steps:
        return False
    text = "\n".join(str(s) for s in steps)
    if any(mk in text for mk in _METHOD_MARKERS):
        return False
    if len(steps) <= 2:
        return True
    return any(mk in text for mk in _SUMMARY_MARKERS)


def enrich_de_steps(question, result):
    """The verified real-steps copy of a summary-stepped
    DE serve, or None (serve stands untouched)."""
    if not isinstance(result, dict):
        return None
    if result.get("op") != "differential_equation":
        return None
    if result.get("steps_tex"):
        return None
    answer = result.get("answer")
    if not isinstance(answer, str):
        return None
    answer = answer.strip()
    if not answer.startswith("y ="):
        return None
    if "Piecewise" in answer or "piecewise" in answer:
        return None
    if not _summary_styled(result):
        return None
    q = str(question or "")
    if "d2y" in q or "y''" in q or 'y"' in q:
        return None
    box = {}

    def _run():
        try:
            box["out"] = _build(q, answer, result)
        except BaseException:  # never leak into the chain
            box["out"] = None

    worker = threading.Thread(target=_run, daemon=True,
                              name="ganitra-wave209")
    worker.start()
    worker.join(_BUDGET_SECONDS)
    if worker.is_alive():
        return None
    return box.get("out")


# ------------------------------------------------------------------ #
# Extraction: (f, ic) for the question
# ------------------------------------------------------------------ #

_IC_FUNC_RE = re.compile(
    r"y\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)\s*=\s*"
    r"(-?\d+(?:\.\d+)?)")
_IC_WHEN_RE = re.compile(
    r"y\s*=\s*(-?\d+(?:\.\d+)?)\s+when\s+x\s*=\s*"
    r"(-?\d+(?:\.\d+)?)")

_WRAPPER_RE = re.compile(
    r"\b(find|solve|the|general|particular|solution|of|"
    r"given|that|differential\s+equation)\b", re.I)


def _extract_ic(text):
    """depth125's two IC phrasings; (ic, text_without_ic)."""
    m = _IC_FUNC_RE.search(text)
    if m:
        ic = (sp.Rational(m.group(1)),
              sp.Rational(m.group(2)))
        return ic, text[:m.start()] + " " + text[m.end():]
    m = _IC_WHEN_RE.search(text)
    if m:
        ic = (sp.Rational(m.group(2)),
              sp.Rational(m.group(1)))
        return ic, text[:m.start()] + " " + text[m.end():]
    return None, text


def _extract_dress(question):
    """The implicit dress depth125's extractor cannot
    read — "dy/dx + P(x) y = Q(x)", "A(x) dy/dx + B y =
    Q" — parsed strictly: the cleaned text must be ONE
    equation, linear in the dy/dx placeholder, with an
    x-only coefficient.  Returns (f, ic) or None."""
    text = _prep(question)
    ic, text = _extract_ic(text)
    text = text.replace("अवकल समीकरण", " ")
    text = _WRAPPER_RE.sub(" ", text)
    text = text.strip(" .,;:?")
    if "d2y" in text:
        return None
    if not re.search(r"dy\s*/\s*dx", text) \
            and "y'" not in text:
        return None
    # The placeholder rides as "w1": parse_expression
    # folds a trailing digit off a symbol name, so the
    # token lands as the single symbol w (a bare "y1"
    # would fold onto y itself and vanish).
    text = re.sub(r"dy\s*/\s*dx", " w1 ", text)
    text = text.replace("y'", " w1 ")
    if text.count("=") != 1:
        return None
    left, right = text.split("=", 1)
    try:
        expr = _fold_e(parse_expression(left)
                       - parse_expression(right))
    except Exception:
        return None
    w = None
    for sym in expr.free_symbols:
        if sym.name == "w":
            w = sym
            break
    if w is None:
        return None
    try:
        poly = sp.Poly(expr, w)
    except Exception:
        return None
    if poly is None or poly.degree() != 1:
        return None
    coeff = poly.nth(1)
    rest = poly.nth(0)
    if coeff == 0 or coeff.free_symbols - {_x}:
        return None
    if rest.free_symbols - {_x, _y}:
        return None
    f = -rest / coeff
    if f.free_symbols - {_x, _y}:
        return None
    return f, ic


def _extract(question):
    got = None
    try:
        got = _de_extract(_prep(question))
    except Exception:
        got = None
    if got is not None:
        rhs_text, ic = got
        try:
            f = _fold_e(parse_expression(rhs_text))
        except Exception:
            return None
        if f.free_symbols - {_x, _y}:
            return None
        return f, ic
    return _extract_dress(question)


# ------------------------------------------------------------------ #
# Verification pieces
# ------------------------------------------------------------------ #

def _verify_answer(f, ysol, ic):
    """The served solution satisfies the ODE (and the
    IC): checkodesol first — depth125's verifier — then
    a direct differentiate-and-simplify."""
    yf = sp.Function("y")(_x)
    eq = sp.Eq(yf.diff(_x), f.subs(_y, yf))
    ok = False
    try:
        res = sp.checkodesol(eq, sp.Eq(yf, ysol), order=1,
                             solve_for_func=False)
        ok = bool(isinstance(res, tuple) and res[0])
    except Exception:
        ok = False
    if not ok:
        try:
            ok = sp.simplify(
                sp.diff(ysol, _x)
                - f.subs(_y, ysol)) == 0
        except Exception:
            ok = False
    if not ok:
        return False
    if ic is not None:
        try:
            return sp.simplify(
                ysol.subs(_x, ic[0]) - ic[1]) == 0
        except Exception:
            return False
    return True


def _consistency_ok(rel, ysol, const_sym):
    """rel(x, y) = C really lands on the served solution:
    rel is constant along y = ysol(x).  Symbolic first;
    numeric sampling only as corroboration (branch forms
    like atan(tan u) defeat the symbolic simplifier but
    not three sample points)."""
    along = rel.subs(_y, ysol)
    try:
        d = sp.diff(along, _x)
    except Exception:
        return False
    for cand in (d,):
        try:
            if sp.simplify(cand) == 0:
                return True
        except Exception:
            pass
    try:
        if sp.trigsimp(d) == 0:
            return True
    except Exception:
        pass
    subs_map = {}
    if const_sym is not None:
        subs_map[const_sym] = sp.Rational(37, 100)
    try:
        curve = along.subs(subs_map)
        vals = []
        for xv in (sp.Rational(2, 5), sp.Rational(9, 10),
                   sp.Rational(17, 10)):
            try:
                val = complex(curve.subs(_x, xv).evalf())
            except Exception:
                continue
            if abs(val.imag) < 1e-9:
                vals.append(val.real)
        return len(vals) >= 2 and \
            max(vals) - min(vals) < 1e-6
    except Exception:
        return False


# ------------------------------------------------------------------ #
# Families: each returns (relation R, steps) or None.
# R is the implicit general relation R(x, y) = C in
# house form; the closing line is added by the caller.
# ------------------------------------------------------------------ #

def _fam_direct(f, hi):
    if _y in f.free_symbols:
        return None
    try:
        ix = sp.integrate(f, _x)
    except Exception:
        return None
    if ix.has(sp.Integral):
        return None
    rel = _y - ix
    steps = ([
        "यहाँ dy/dx केवल x पर निर्भर है, इसलिए सीधे "
        "समाकलन कीजिए।",
        f"समाकलन करने पर: y = {fmt(ix)} + C।",
    ] if hi else [
        "Here dy/dx depends only on x, so integrate "
        "directly.",
        f"Integrating: y = {fmt(ix)} + C.",
    ])
    return rel, steps


def _fam_homogeneous(f, hi):
    if _y not in f.free_symbols:
        return None
    t = sp.symbols("t", positive=True)
    try:
        homog = sp.simplify(
            f.subs({_x: t * _x, _y: t * _y}) - f) == 0
    except Exception:
        homog = False
    if not homog:
        return None
    v = sp.symbols("v")
    try:
        g = sp.simplify(f.subs(_y, v * _x))
    except Exception:
        return None
    if g.free_symbols - {v}:
        return None
    if sp.simplify(g - v) == 0:
        return None  # f == y/x in disguise: separable
    try:
        sep = sp.integrate(1 / (g - v), v)
    except Exception:
        return None
    if sep.has(sp.Integral):
        return None
    rel = sep.subs(v, _y / _x) - sp.log(_x)
    steps = ([
        "जाँच: f(tx, ty) = f(x, y), अतः समीकरण "
        "समघातीय है।",
        "y = vx रखिए, तो dy/dx = v + x dv/dx।",
        f"रखने पर: v + x dv/dx = {fmt(g)} अर्थात् "
        f"x dv/dx = {fmt(g)} - v।",
        "चरों को अलग करके समाकलन करने पर: "
        f"{fmt(sep)} = log|x| + C।",
        f"v = y/x वापस रखने पर: {fmt(rel)} = C।",
    ] if hi else [
        "Check: f(tx, ty) = f(x, y), so the equation "
        "is homogeneous.",
        "Put y = vx, so dy/dx = v + x dv/dx.",
        f"Substituting: v + x dv/dx = {fmt(g)}, so "
        f"x dv/dx = {fmt(g)} - v.",
        "Separating the variables and integrating: "
        f"{fmt(sep)} = log|x| + C.",
        f"Putting v = y/x back: {fmt(rel)} = C.",
    ])
    return rel, steps


def _separate_gh(f):
    """f = g(x) * h(y), diffeq194's factor test and
    extraction, verbatim in spirit."""
    x, y = _x, _y
    if x not in f.free_symbols:
        return sp.Integer(1), f
    if y not in f.free_symbols:
        return f, sp.Integer(1)
    try:
        fx = sp.diff(f, x)
        fy = sp.diff(f, y)
        fxy = sp.diff(fx, y)
        if sp.simplify(fx * fy - f * fxy) != 0:
            return None
    except Exception:
        return None
    for y0 in (0, 1, 2, -1, sp.Rational(1, 2)):
        try:
            cand_g = f.subs(y, y0)
            if cand_g == 0 or cand_g.has(sp.zoo, sp.nan):
                continue
            cand_h = sp.simplify(f / cand_g)
        except Exception:
            continue
        if cand_h.free_symbols - {y}:
            continue
        if cand_g.free_symbols - {x}:
            continue
        try:
            if sp.simplify(cand_g * cand_h - f) == 0:
                return cand_g, cand_h
        except Exception:
            continue
    return None


def _fam_separable(f, hi):
    got = _separate_gh(f)
    if got is None:
        return None
    g, h = got
    if h == 1:
        return None  # direct integration's shape
    # Normalise the split: a constant factor riding on
    # h moves onto g (dy/(c·h) = g dx is (c·g) dx against
    # dy/h), so the separated line reads the NCERT way —
    # (y + 2) dy = (x + 1) dx, not dy/(2/(y + 2)).
    try:
        hf = sp.factor(h)
        if hf.is_Mul and hf.args and \
                hf.args[0].is_number and \
                hf.args[0] not in (0, 1):
            g = sp.simplify(g * hf.args[0])
            h = sp.simplify(h / hf.args[0])
    except Exception:
        pass
    try:
        iy = sp.integrate(1 / h, _y)
        ix = sp.integrate(g, _x)
    except Exception:
        return None
    if iy.has(sp.Integral) or ix.has(sp.Integral):
        return None
    rel = iy - ix
    # Display: dy/(h) when h is a plain expression, but
    # (1/h) dy when h itself is a fraction — NCERT writes
    # (y + 2) dy = (x + 1) dx, not dy/(1/(y + 2)).
    try:
        numer = sp.fraction(sp.together(h))[0]
    except Exception:
        numer = None
    rhs = "dx" if g == 1 else f"({fmt(g)}) dx"
    if numer == 1:
        inv = sp.simplify(1 / h)
        sep_line = (
            f"चरों को अलग कीजिए: ({fmt(inv)}) dy = "
            f"{rhs}।" if hi else
            f"Separate the variables: ({fmt(inv)}) dy "
            f"= {rhs}.")
    else:
        sep_line = (
            f"चरों को अलग कीजिए: dy/({fmt(h)}) = "
            f"{rhs}।" if hi else
            f"Separate the variables: dy/({fmt(h)}) "
            f"= {rhs}.")
    steps = ([sep_line,
              "दोनों पक्षों का समाकलन करने पर: "
              f"{fmt(iy)} = {fmt(ix)} + C।"]
             if hi else
             [sep_line,
              "Integrating both sides: "
              f"{fmt(iy)} = {fmt(ix)} + C."])
    return rel, steps


def _fam_linear(f, hi):
    try:
        poly = sp.Poly(f, _y)
    except Exception:
        poly = None
    if poly is None or poly.degree() != 1:
        return None
    a = poly.nth(1)  # f = a(x) y + b(x)
    b = poly.nth(0)
    if a.free_symbols - {_x} or b.free_symbols - {_x}:
        return None
    P = -a
    Q = b
    try:
        int_p = sp.integrate(P, _x)
        if int_p.has(sp.Integral):
            return None
        mu = sp.exp(int_p)
        int_qmu = sp.integrate(Q * mu, _x)
        if int_qmu.has(sp.Integral):
            return None
    except Exception:
        return None
    rel = _y * mu - int_qmu
    steps = ([
        "यह y में रैखिक समीकरण है: "
        f"dy/dx + ({fmt(P)}) y = {fmt(Q)}।",
        f"समाकलन गुणक IF = e^(∫P dx) = {fmt(mu)}।",
        "IF से गुणा करके समाकलन करने पर: "
        f"y × {fmt(mu)} = {fmt(int_qmu)} + C।",
    ] if hi else [
        "This is linear in y: "
        f"dy/dx + ({fmt(P)}) y = {fmt(Q)}.",
        "Integrating factor IF = e^(∫P dx) "
        f"= {fmt(mu)}.",
        "Multiplying by the IF and integrating: "
        f"y × {fmt(mu)} = {fmt(int_qmu)} + C.",
    ])
    return rel, steps


def _fam_substitution(f, hi):
    """f a function of z = x + y or z = x - y alone:
    the substitution makes it separable in z."""
    z = sp.symbols("z")
    for sign, label, dz_form in (
            (1, "x + y", "1 + dy/dx"),
            (-1, "x - y", "1 - dy/dx")):
        try:
            if sign == 1:
                big_f = f.subs(_y, z - _x)
            else:
                big_f = f.subs(_y, _x - z)
        except Exception:
            continue
        if big_f.free_symbols - {z}:
            continue
        denom = 1 + big_f if sign == 1 else 1 - big_f
        try:
            iz = sp.integrate(1 / denom, z)
        except Exception:
            continue
        if iz.has(sp.Integral):
            continue
        rel = iz.subs(z, _x + sign * _y) - _x
        steps = ([
            f"z = {label} रखिए, तो dz/dx = {dz_form}।",
            f"रखने पर: dz/dx = {fmt(denom)}।",
            f"चरों को अलग कीजिए: dz/({fmt(denom)}) "
            "= dx।",
            f"समाकलन करने पर: {fmt(iz)} = x + C।",
            f"z = {label} वापस रखने पर: {fmt(rel)} "
            "= C।",
        ] if hi else [
            f"Put z = {label}, so dz/dx = {dz_form}.",
            f"Substituting: dz/dx = {fmt(denom)}.",
            f"Separate the variables: "
            f"dz/({fmt(denom)}) = dx.",
            f"Integrating: {fmt(iz)} = x + C.",
            f"Putting z = {label} back: {fmt(rel)} "
            "= C.",
        ])
        return rel, steps
    return None


_FAMILIES = (_fam_direct, _fam_homogeneous,
             _fam_separable, _fam_linear,
             _fam_substitution)


# ------------------------------------------------------------------ #
# The builder (runs inside the bounded worker)
# ------------------------------------------------------------------ #

def _build(question, answer, result):
    hi = _hindi(question)
    got = _extract(question)
    if got is None:
        return None
    f, ic = got
    if sp.count_ops(f) > _MAX_OPS:
        return None
    if _x not in f.free_symbols and \
            _y not in f.free_symbols:
        return None
    # The served solution, parsed back.  parse_expression
    # folds the house constant spellings (C1 / C2) onto
    # one symbol; exactly one arbitrary constant may ride
    # in a general solution, none in a particular one.
    rhs_text = answer[len("y ="):].strip()
    rhs_text = rhs_text.replace("·", "*") \
        .replace("−", "-")
    try:
        ysol = parse_expression(rhs_text)
    except Exception:
        return None
    if ysol.has(sp.Piecewise) or _y in \
            ysol.free_symbols:
        return None
    extras = ysol.free_symbols - {_x}
    if ic is None:
        if len(extras) != 1:
            return None
        const_sym = next(iter(extras))
    else:
        if extras:
            return None
        const_sym = None
    if not _verify_answer(f, ysol, ic):
        return None
    built = None
    for fam in _FAMILIES:
        try:
            built = fam(f, hi)
        except Exception:
            built = None
        if built is not None:
            break
    if built is None:
        return None
    rel, steps = built
    if not _verify_implicit(rel, f):
        return None
    if not _consistency_ok(rel, ysol, const_sym):
        return None
    if ic is not None:
        try:
            cval = sp.simplify(rel.subs(
                {_x: ic[0], _y: ic[1]}))
        except Exception:
            return None
        steps = steps + ([
            f"अब शर्त y = {fmt(ic[1])} जब "
            f"x = {fmt(ic[0])} रखने पर C = "
            f"{fmt(cval)} मिलता है।",
            f"अतः विशेष हल: {answer}।",
        ] if hi else [
            f"Now use the condition y = {fmt(ic[1])} "
            f"when x = {fmt(ic[0])}: this gives "
            f"C = {fmt(cval)}.",
            f"Particular solution: {answer}.",
        ])
    else:
        steps = steps + ([
            f"अतः व्यापक हल: {answer}।",
        ] if hi else [
            f"So the general solution is: {answer}.",
        ])
    out = dict(result)
    out["steps"] = steps
    return out
