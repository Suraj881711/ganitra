"""Calculus: limits, derivatives (incl. partial & implicit), integrals,
and basic differential equations — with step-by-step working.
"""
import math
import re

import sympy as sp
from sympy import S, diff, dsolve, idiff, integrate, limit, symbols

from .expression_parser import fmt, fmt_num, parse_expression

_x = symbols("x")

# ---------------------------------------------------------------------------
# Wave 100: order & degree of a differential equation, by inspection.
#
# The Wave 93 audit's regression #2 was a Hindi MCQ that asks only
# for the DEGREE (घात) of an ODE — "अवकल समीकरण x·(d²y/dx²) +
# xy(dy/dx)² − xy(dy/dx) = 0 का घात है (a) 1 (b) 2 …". The question
# never needed the equation SOLVED, but solve_calculus routed it
# into _ode -> dsolve, whose classify_ode factorisation explodes
# combinatorially on the y·(y')² shape (sympy polys dmp_inflate
# recursion) and burned the whole 10 s solve budget twice over
# (original + the app layer's retry) before the MCQ layer could
# even look at it: an audit ERROR_TIMEOUT. Order and degree are
# facts OF the equation's text — the highest derivative present
# and the power it is raised to — so they are read off with a
# pure text scan (no SymPy work at all) and answered directly.
# ---------------------------------------------------------------------------

_SUPERSCRIPT_DIGITS = {
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
}


def _ode_scan_text(text):
    """Normalise the derivative spellings of an ODE text for the
    order/degree scan: Unicode superscripts become ^n, and the
    compact ASCII forms (d2y/dx2) gain their carets."""
    t = str(text or "")
    for sup, caret in _SUPERSCRIPT_DIGITS.items():
        t = t.replace(sup, caret)
    t = re.sub(r"d(\d+)y/dx(\d+)", r"d^\1y/dx^\2", t)
    t = re.sub(r"dy/dx", "dy/dx", t)
    return t


def ode_order_degree(text):
    """(order, degree) of the differential equation in `text`,
    read off its derivative tokens, or None when the text holds
    no derivative at all. degree is None when the highest
    derivative is not raised to a plain positive-integer power
    in a polynomial way (inside sin/log/exp/sqrt, or under a
    fractional power) — the degree is then NOT DEFINED and the
    caller must not invent one.

    Derivative tokens recognised: d^ny/dx^n (any spelling),
    dy/dx, and the prime forms y', y'', y'''. The power of a
    token is the ^n attached to the token itself or to its
    closing parenthesis — "(dy/dx)^2" — never a power applied
    to a larger bracket around it ("[1 + (dy/dx)^2]^3" leaves
    the dy/dx power at 2)."""
    t = _ode_scan_text(text)
    found = []  # (order, power, start, end)

    def _power_after(end):
        rest = t[end:end + 8]
        m = re.match(r"\s*\)\s*\^\s*(\d+)", rest)
        if m:
            return int(m.group(1))
        m = re.match(r"\s*\^\s*(\d+)", rest)
        if m:
            return int(m.group(1))
        return 1

    for m in re.finditer(r"d\^(\d+)y/dx\^(\d+)", t):
        found.append((int(m.group(1)), _power_after(m.end()),
                      m.start(), m.end()))
    for m in re.finditer(r"(?<![a-z])dy/dx", t):
        found.append((1, _power_after(m.end()), m.start(),
                      m.end()))
    for m in re.finditer(r"y('{2,})", t):
        found.append((len(m.group(1)), _power_after(m.end()),
                      m.start(), m.end()))
    for m in re.finditer(r"(?<![a-z'])y'(?![a-z'])", t):
        found.append((1, _power_after(m.end()), m.start(),
                      m.end()))
    if not found:
        return None
    order = max(o for o, _p, _s, _e in found)
    # Degree is undefined when the highest-order derivative sits
    # inside a transcendental call — sin(dy/dx), log(d2y/dx2)…
    for o, _p, s, _e in found:
        if o != order:
            continue
        head = t[max(0, s - 12):s]
        if re.search(r"(sin|cos|tan|sec|csc|cot|log|ln|exp|"
                     r"sqrt)\s*\($", head):
            return (order, None)
    powers = [p for o, p, _s, _e in found if o == order]
    degree = powers[0] if len(set(powers)) == 1 else max(powers)
    return (order, degree)


_ODE_FACT_ASK = re.compile(
    r"अवकल|differential\s+equation", re.I)
_ODE_DEGREE_ASK = re.compile(r"घात|\bdegree\b", re.I)
_ODE_ORDER_ASK = re.compile(r"कोटि|\border\b", re.I)
_ODE_SOLVE_ASK = re.compile(
    r"\bsolve\b|हल\s+कर|dsolve", re.I)


def _ode_order_degree_result(q):
    """The direct answer for a question that asks ONLY for the
    order and/or degree of a differential equation (Wave 100).
    Fires solely when the text names a differential equation
    (अवकल / "differential equation"), asks for घात/degree and/or
    कोटि/order, and does not ask for the equation to be solved;
    anything else returns None and the dsolve path runs exactly
    as before. A both-fact ask on an options-bearing text is
    left to the MCQ layer (a single computed value is what its
    matcher can name); a plain both-fact ask is answered in
    words."""
    if "=" not in q:
        return None
    if not _ODE_FACT_ASK.search(q):
        return None
    want_degree = bool(_ODE_DEGREE_ASK.search(q))
    want_order = bool(_ODE_ORDER_ASK.search(q))
    if not (want_degree or want_order):
        return None
    if _ODE_SOLVE_ASK.search(q):
        return None
    got = ode_order_degree(q)
    if got is None:
        return None
    order, degree = got
    options_bearing = len(re.findall(r"\(\s*[a-dA-D]\s*\)", q)) >= 2
    if want_degree and want_order:
        if options_bearing:
            return None
        if degree is None:
            return None
        return {
            "type": "calculus", "op": "ode_order_degree",
            "answer": f"Order = {order}, Degree = {degree}",
            "steps": [
                "The order is the highest derivative present "
                f"in the equation: order = {order}.",
                "The degree is the power of that highest "
                f"derivative: degree = {degree}.",
            ],
        }
    if want_degree:
        if degree is None:
            return None
        return {
            "type": "calculus", "op": "ode_degree",
            "answer": str(degree),
            "steps": [
                "The degree of a differential equation is the "
                "power of its highest-order derivative.",
                f"Here the highest derivative appears with "
                f"power {degree}, so the degree is {degree}.",
            ],
        }
    return {
        "type": "calculus", "op": "ode_order",
        "answer": str(order),
        "steps": [
            "The order of a differential equation is the "
            "highest derivative present in it.",
            f"Here that is a derivative of order {order}, "
            f"so the order is {order}.",
        ],
    }


def _guess_symbol(expr):
    return next(iter(expr.free_symbols), _x)


def _poly_terms(expr, var):
    """[(coeff, power), ...] if expr is a polynomial in var, else None."""
    try:
        poly = sp.Poly(sp.expand(expr), var)
    except Exception:
        return None
    return [(poly.nth(p), p) for p in range(poly.degree(), -1, -1)
            if poly.nth(p) != 0]


def _derivative_steps(expr, var):
    terms = _poly_terms(expr, var)
    result = _textbook_trig(diff(expr, var))
    if terms is not None:
        steps = [f"Take the derivative of {fmt(expr)} term by term "
                 f"with respect to {var}, using the power rule "
                 "d/dx[c·x^n] = c·n·x^(n-1):"]
        for c, n in terms:
            if n == 0:
                steps.append(f"d/d{var} ({fmt(c)}) = 0 (constant)")
            elif n == 1:
                steps.append(f"d/d{var} ({fmt(c)}·{var}) = {fmt(c)}")
            else:
                steps.append(
                    f"d/d{var} ({fmt(c)}·{var}^{n}) = {fmt(c)}·{n}·"
                    f"{var}^{n - 1} = {fmt(c * n)}·{var}^{n - 1}"
                )
        steps.append(f"Add the results: {fmt(result)}")
        return steps
    steps = [
        f"Differentiate {fmt(expr)} with respect to {var} using the "
        "standard rules (chain/product/quotient as needed).",
        f"Result: {fmt(result)}",
    ]
    return steps


def _integral_steps(expr, var, bounds=None):
    result = integrate(expr, (var, *bounds)) if bounds else integrate(expr, var)
    terms = _poly_terms(expr, var)
    if bounds:
        a, b = bounds
        F = integrate(expr, var)
        steps = [
            f"First find the antiderivative: ∫ {fmt(expr)} d{var} = "
            f"{fmt(F)}",
            f"Apply the limits: F({fmt(b)}) - F({fmt(a)})",
            f"= {fmt(F.subs(var, b))} - {fmt(F.subs(var, a))} = "
            f"{fmt(result)}",
        ]
        return steps
    if terms is not None:
        steps = [f"Integrate {fmt(expr)} term by term using the power "
                 f"rule ∫ c·x^n dx = c·x^(n+1)/(n+1):"]
        for c, n in terms:
            steps.append(
                f"∫ {fmt(c)}·{var}^{n} d{var} = {fmt(c / (n + 1))}·"
                f"{var}^{n + 1}"
            )
        steps.append(f"Combine and add the constant: {fmt(result)} + C")
        return steps
    return [
        f"Integrate {fmt(expr)} with respect to {var} using standard "
        "integral rules.",
        f"Result: {fmt(result)} + C",
    ]


def _ode(q: str):
    """ODEs via dsolve: separable, linear, second-order, with simple
    initial conditions. Accepts dy/dx = ..., y' = ..., y'' + y = 0,
    'differential equation ...', and first-order IVPs like
    'dy/dx = 2x, y(0) = 1'."""
    text = q.strip()
    # y'' must be replaced before y' (y' is a prefix of y'').
    text = text.replace("y''", "d2y/dx2").replace("y'", "dy/dx")
    text = re.sub(r"\b(dsolve|solve|differential\s+equation)\b", "",
                  text, flags=re.I).strip(" :")
    # Wave 58: "Solve THE differential equation dy/dx = ..."
    # leaves a leading "the" behind once the phrase above is
    # removed, and the left side then reads "the dy/dx", which
    # matches no ODE form — the question fell to the salvage
    # even though the stripped equation is trivial.
    text = re.sub(r"^the\s+", "", text, flags=re.I).strip(" :")
    # Pull out initial conditions: y(0) = 1, dy/dx(0) = 2
    ics = {}
    yfun = sp.Function("y")
    yx = yfun(_x)

    def _set_ic(kind, at_raw, val_raw):
        at = parse_expression(at_raw)
        val = parse_expression(val_raw)
        if kind == "deriv":
            ics[yx.diff(_x).subs(_x, at)] = val
        else:
            ics[yx.subs(_x, at)] = val
        return " "

    text = re.sub(
        r"dy/dx\s*\(\s*(-?[\d.]+)\s*\)\s*=\s*(-?[\d.]+)",
        lambda m: _set_ic("deriv", m.group(1), m.group(2)), text)
    text = re.sub(
        r"y\s*\(\s*(-?[\d.]+)\s*\)\s*=\s*(-?[\d.]+)",
        lambda m: _set_ic("func", m.group(1), m.group(2)), text)
    text = text.strip(" ,;")
    text = re.sub(r"\band\s*$", "", text).strip(" ,;")
    text = re.sub(r"\bwith\b.*$", "", text, flags=re.I).strip(" ,;")

    # Wave 80: prose guard. The implicit-form branch below
    # letter-splits every multi-letter word it cannot name
    # (xy -> x*y), so a FACT question about an equation —
    # "Integrating factor of the differential Equation
    # dy/dx + y logx = cosx is" — tokenised into dozens of
    # one-letter symbols and dsolve churned on the soup for
    # ~39 s (Wave 71 audit timeout family). A real ODE's text
    # contains no alphabetic word of 3+ letters except
    # function names (or glued forms like cosx/logx, which
    # START with a function name). Anything else is prose:
    # refuse fast and let the fact schemas answer.
    _FUNC_WORDS = ("sin", "cos", "tan", "exp", "log", "sqrt",
                   "cot", "sec", "csc", "asin", "acos", "atan",
                   "sinh", "cosh", "tanh", "abs")
    for _w in re.findall(r"[A-Za-z]{3,}", text):
        _wl = _w.lower()
        if _wl in _FUNC_WORDS:
            continue
        if any(_wl.startswith(_f) for _f in _FUNC_WORDS):
            continue
        return None

    if "=" not in text:
        return None
    left, right = text.split("=", 1)
    left_c = left.replace(" ", "")
    y_sym = symbols("y")

    def as_yx(expr):
        return expr.subs(y_sym, yx) if y_sym in expr.free_symbols else expr

    if left_c == "d2y/dx2":
        rhs = as_yx(parse_expression(right))
        sol_eq = sp.Eq(yx.diff(_x, 2), rhs)
        ode_text = f"y'' = {fmt(rhs)}"
    elif left_c == "dy/dx":
        rhs = as_yx(parse_expression(right))
        sol_eq = sp.Eq(yx.diff(_x), rhs)
        ode_text = f"dy/dx = {fmt(rhs)}"
    elif "d2y/dx2" in text.replace(" ", "") or "dy/dx" in text:
        # Implicit form, e.g. "d2y/dx2 + y = 0", "dy/dx + y = x". Hide
        # the derivative tokens behind placeholders BEFORE parse_expr
        # runs — its tokenizer mangles "dy/dx" into d*y/d*x, splits
        # "D2" into a derivative application, and even splits a long
        # camel-case symbol like "ZoZ" into Z*o*Z. So: tokenise the
        # text manually, swap the derivative tokens for single letters
        # (w = y', v = y''), parse, then substitute back.
        whole = text.replace("d2y/dx2", "\x01").replace("dy/dx", "\x02")
        tokens = re.findall(r"\x01|\x02|[A-Za-z]+|\d+(?:\.\d+)?|\S", whole)

        def rebuild(toks):
            out = []
            for tk in toks:
                if tk == "\x01":
                    out.append(" v ")
                elif tk == "\x02":
                    out.append(" w ")
                elif tk.isalpha() and len(tk) > 1 and tk not in (
                        "sin", "cos", "tan", "exp", "log", "sqrt",
                        "cot", "sec", "csc"):
                    # implicit multiplication of single letters: xy -> x*y
                    out.append("*".join(tk))
                else:
                    out.append(tk)
            return " ".join(out)

        joined = rebuild(tokens)
        l2, r2 = joined.split("=", 1)
        w_sym, v_sym = symbols("w v")
        lexpr = parse_expression(l2)
        rexpr = parse_expression(r2)
        subs_map = {v_sym: yx.diff(_x, 2), w_sym: yx.diff(_x),
                    y_sym: yx}
        sol_eq = sp.Eq(lexpr.subs(subs_map), rexpr.subs(subs_map))
        ode_text = text.replace("d2y/dx2", "y''")
    else:
        return None

    # Wave 80: symbol guard — an equation carrying more than
    # a couple of stray symbols is letter-soup, not an ODE;
    # never hand it to dsolve.
    _extra = sol_eq.free_symbols - {_x, yx}
    if len(_extra) > 3:
        return None

    try:
        sol = dsolve(sol_eq, yx, ics=ics) if ics else dsolve(sol_eq, yx)
    except Exception:
        return None
    if isinstance(sol, list):
        sol = sol[0]
    rhs_sol = sol.rhs
    kind = ("initial condition(s) applied: "
            + ", ".join(f"{fmt(k)} = {fmt(v)}" for k, v in ics.items())) \
        if ics else "general solution (C1, C2 are arbitrary constants)"
    steps = [
        f"Differential equation: {ode_text}",
        "Solve with SymPy's dsolve — it classifies the equation "
        "(separable, linear, constant-coefficient, ...) and applies "
        "the matching method.",
        f"Solution: y = {fmt(rhs_sol)} — {kind}",
    ]
    return {
        "type": "calculus",
        "op": "differential_equation",
        "answer": f"y = {fmt(rhs_sol)}",
        "steps": steps,
    }


def _textbook_trig(deriv):
    """Wave 47: present Pythagorean derivative results the
    textbook way — tan^2(u) + 1 as sec^2(u) and cot^2(u) + 1
    as csc^2(u). d/dx tan x otherwise displays as
    tan(x)^2 + 1, which students (and answer checks) read
    as unfinished (audit #379)."""
    try:
        _w = sp.Wild("w")
        return deriv.replace(
            sp.tan(_w) ** 2 + 1, sp.sec(_w) ** 2).replace(
            -sp.tan(_w) ** 2 - 1, -sp.sec(_w) ** 2).replace(
            sp.cot(_w) ** 2 + 1, sp.csc(_w) ** 2).replace(
            -sp.cot(_w) ** 2 - 1, -sp.csc(_w) ** 2)
    except Exception:
        return deriv


def _conic_line(A, B, C):
    """Render A·x + B·y = C in simplest integer form."""
    from fractions import Fraction
    import math as _m

    def _fr(v):
        if hasattr(v, "p") and hasattr(v, "q"):
            return Fraction(int(v.p), int(v.q))
        return Fraction(v)

    A, B, C = _fr(A), _fr(B), _fr(C)
    den = 1
    for v in (A, B, C):
        den = den * v.denominator // _m.gcd(den, v.denominator)
    A, B, C = int(A * den), int(B * den), int(C * den)
    g = _m.gcd(_m.gcd(abs(A), abs(B)), abs(C)) or 1
    A, B, C = A // g, B // g, C // g
    if A < 0 or (A == 0 and B < 0):
        A, B, C = -A, -B, -C
    terms = []
    for coef, var in ((A, "x"), (B, "y")):
        if coef == 0:
            continue
        mag = var if abs(coef) == 1 else f"{abs(coef)}{var}"
        terms.append((coef > 0, mag))
    if not terms:
        return None
    lhs = terms[0][1] if terms[0][0] else "-" + terms[0][1]
    for pos, mag in terms[1:]:
        lhs += (" + " if pos else " - ") + mag
    return f"{lhs} = {C}"


def _conic_tangent_normal(q, qlow):
    """Wave 58: equation of the tangent / normal to a CONIC at
    a point on it — circle (standard or general form),
    parabola, ellipse, hyperbola. These had no pattern at
    all and were answered with a similar-example fragment
    ("x = 3, x = 4"). One general method covers every conic:
    the tangent is T = 0, the normal runs along the gradient.
    The point is VERIFIED to lie on the conic first — an
    off-conic point returns None rather than a formula
    answer.
    """
    if "tangent" not in qlow and "normal" not in qlow:
        return None
    _mp = re.search(r"\(\s*(-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?)"
                    r"\s*,\s*(-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?)"
                    r"\s*\)", q)
    if not _mp:
        return None
    _mi = re.search(r"[xy]\s*\^\s*2", qlow)
    if not _mi:
        return None
    _seg = q[_mi.start():]
    _seg = re.split(r"\s+at\s+|\s+which\s+|\s+to\s+the\s+"
                    r"(?:circle|parabola|ellipse|hyperbola)",
                    _seg)[0].strip().rstrip(".?").strip()
    if "=" not in _seg:
        return None
    try:
        _xs, _ys = symbols("x y")
        _lt, _rt = _seg.split("=", 1)
        _E = sp.expand(parse_expression(_lt)
                       - parse_expression(_rt))
        _poly = sp.Poly(_E, _xs, _ys)
        if _poly is None or _poly.total_degree() != 2:
            return None
        _x1 = sp.Rational(_mp.group(1).replace(" ", ""))
        _y1 = sp.Rational(_mp.group(2).replace(" ", ""))
        if sp.simplify(_E.subs({_xs: _x1, _ys: _y1})) != 0:
            return None  # point not on the conic
        _A2 = _poly.coeff_monomial(_xs ** 2)
        _B2 = _poly.coeff_monomial(_ys ** 2)
        _H = _poly.coeff_monomial(_xs * _ys)
        _G = _poly.coeff_monomial(_xs)
        _F = _poly.coeff_monomial(_ys)
        _C0 = _poly.coeff_monomial(1)
        if _A2 == 0 and _B2 == 0:
            return None
        # Tangent (T = 0), coefficients doubled to stay exact.
        _tA = 2 * _A2 * _x1 + _H * _y1 + _G
        _tB = 2 * _B2 * _y1 + _H * _x1 + _F
        _tC = -(_G * _x1 + _F * _y1 + 2 * _C0)
        # Normal: along the gradient (E_x, E_y) at the point.
        _Ex = 2 * _A2 * _x1 + _H * _y1 + _G
        _Ey = 2 * _B2 * _y1 + _H * _x1 + _F
        _nA, _nB = _Ey, -_Ex
        _nC = _Ey * _x1 - _Ex * _y1
        _tan = _conic_line(_tA, _tB, _tC)
        _nor = _conic_line(_nA, _nB, _nC)
        if _tan is None or _nor is None:
            return None
        _pt = f"({_mp.group(1)}, {_mp.group(2)})"
        _base_steps = [
            f"The point {_pt} lies on the conic (it satisfies "
            f"the equation).",
        ]
        _want_t = "tangent" in qlow
        _want_n = "normal" in qlow
        if _want_t and _want_n:
            steps = _base_steps + [
                "Tangent by the T = 0 rule (replace x^2 by "
                "x·x1, y^2 by y·y1, 2x by (x + x1), 2y by "
                f"(y + y1)): {_tan}",
                "The normal is perpendicular to the tangent "
                f"at {_pt} (along the gradient): {_nor}",
            ]
            return {"type": "calculus", "op": "conic_tangent",
                    "answer": f"Tangent: {_tan}; Normal: {_nor}",
                    "steps": steps}
        if _want_t:
            steps = _base_steps + [
                "Tangent by the T = 0 rule (replace x^2 by "
                "x·x1, y^2 by y·y1, 2x by (x + x1), 2y by "
                f"(y + y1)): {_tan}",
            ]
            return {"type": "calculus", "op": "conic_tangent",
                    "answer": _tan, "steps": steps}
        steps = _base_steps + [
            "The normal at a point runs along the gradient "
            "of the conic there — perpendicular to the "
            f"tangent: {_nor}",
        ]
        return {"type": "calculus", "op": "conic_normal",
                "answer": _nor, "steps": steps}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wave 80: Class 12 calculus pack — the ∫ glyph (with Unicode
# sub/superscript limits), glued function forms (sinx, logx,
# cosec x, tan⁻¹x), brace-form continuity (incl. Hindi संतत
# stems), implicit dy/dx, integrating factor, order & degree,
# Hindi अवकलज derivatives, (d/dx)(...) form, and chain-rate
# area schemas. Every general-path integral is verified by
# differentiating the antiderivative back before it is shown.
# ---------------------------------------------------------------------------

_SUP_MAP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
            "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
_SUB_MAP = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
            "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9"}


def _w80_glue(text):
    """Normalise board/student function spellings into forms
    parse_expression reads: sinx -> sin(x), logx -> log(x),
    cosec -> csc, sin⁻¹(x) -> asin(x), x² -> x^2, √ -> sqrt,
    π -> pi."""
    t = str(text).replace("−", "-").replace("π", "pi")
    # parse_expression reads a bare 'e' as a free symbol, not
    # Euler's number — e^x must become exp(x) or nothing
    # downstream (division, verification) can cancel it.
    t = re.sub(r"\be\s*\^\s*\(\s*([^()]*)\s*\)", r"exp(\1)", t)
    t = re.sub(r"\be\s*\^\s*([A-Za-z0-9]+)", r"exp(\1)", t)
    t = t.replace("⁻¹", "^-1").replace("⁻", "-")
    for ch, d in _SUP_MAP.items():
        t = t.replace(ch, "^" + d)
    t = re.sub(r"(sin|cos|tan|sec|csc|cot)\s*\^\s*-\s*1\s*"
               r"(?:\(([^()]*)\)|([A-Za-z0-9]+))",
               lambda m: f"a{m.group(1)}({m.group(2) or m.group(3)})",
               t)
    t = re.sub(r"\bcosec\b", "csc", t)
    t = re.sub(r"√\s*\(([^()]*)\)", r"sqrt(\1)", t)
    t = re.sub(r"√\s*([A-Za-z0-9]+)", r"sqrt(\1)", t)
    t = re.sub(r"\b(sin|cos|tan|sec|csc|cot|log|exp|sqrt)\s*"
               r"([A-Za-z])(?![A-Za-z(])", r"\1(\2)", t)
    return t


def _w80_cut_options(text):
    m = re.search(r"\(\s*[aA]\s*\)\s", text)
    return text[:m.start()].strip() if m else text


def _w80_integral(q):
    """Solve a question carrying the ∫ glyph. Returns a result
    dict or None (fall through unchanged)."""
    s = q[q.index("∫"):]
    lo = hi = None
    rest = s[1:]
    # Limit spellings: "(0 to 1)", "_{0}^{1}", "_0^1", and the
    # Unicode runs ∫₂⁸ — including the router-folded mixed
    # form ∫₂^8, since the router's superscript cleaning has
    # already rewritten superscript digits to ^N by the time
    # the question reaches this solver.
    mp = re.match(r"\s*\(\s*(.+?)\s+to\s+(.+?)\s*\)", rest)
    if mp:
        lo, hi, rest = mp.group(1), mp.group(2), rest[mp.end():]
    else:
        ms = re.match(r"\s*(?:_\{([^}]*)\}|_(\d+)|"
                      r"([₀₁₂₃₄₅₆₇₈₉]+))", rest)
        if ms:
            lo = ms.group(1) or ms.group(2) or "".join(
                _SUB_MAP.get(c, c) for c in ms.group(3))
            rest = rest[ms.end():]
            mu = re.match(r"\s*(?:\^\{([^}]*)\}|\^(\d+)|"
                          r"([⁰¹²³⁴⁵⁶⁷⁸⁹]+))", rest)
            if mu:
                hi = mu.group(1) or mu.group(2) or "".join(
                    _SUP_MAP.get(c, c) for c in mu.group(3))
                rest = rest[mu.end():]
    rest = rest.strip()
    # Integrand and differential variable.
    var = "x"
    integrand = None
    md = re.match(r"d([a-z])\s*/\s*(.+)$", rest)
    if md:  # ∫ dx/(1 + x^2): the differential leads.
        var = md.group(1)
        integrand = "1/" + md.group(2).strip()
    else:
        md = re.search(r"(.+?)\s*d([a-z])\b", rest)
        if md:
            integrand, var = md.group(1).strip(), md.group(2)
        elif rest:
            integrand = rest
    if not integrand:
        return None
    integrand = integrand.strip().rstrip(".").rstrip("=").strip()
    integrand = re.sub(r"\|([^|]+)\|", r"Abs(\1)", integrand)
    integrand = _w80_glue(integrand)
    vsym = symbols(var)

    def _num(text):
        return parse_expression(_w80_glue(str(text).strip()))

    lo_v = _num(lo) if lo is not None else None
    hi_v = _num(hi) if hi is not None else None
    definite = lo_v is not None and hi_v is not None

    # Schema: ∫(0 to 1) x(1 - x)^n dx = 1/((n + 1)(n + 2))
    # (Beta function B(2, n + 1)); SymPy returns a Piecewise
    # for the symbolic n, so the closed form is given directly.
    if definite and lo_v == 0 and hi_v == 1 and re.fullmatch(
            r"x\s*\(\s*1\s*-\s*x\s*\)\s*\^\s*\(?\s*n\s*\)?",
            integrand):
        n = symbols("n")
        val = 1 / ((n + 1) * (n + 2))
        steps = [
            "Put u = 1 - x, so the integral becomes "
            "∫(0 to 1) (1 - u) u^n du.",
            "= [u^(n+1)/(n+1) - u^(n+2)/(n+2)] from 0 to 1",
            f"= 1/((n + 1)(n + 2))",
        ]
        return {"type": "calculus", "op": "definite_integral",
                "answer": fmt(val), "steps": steps}

    try:
        expr = parse_expression(integrand)
    except Exception:
        return None
    if expr.has(sp.Integral):
        return None

    # Schema: ∫ csc x dx and friends have textbook log forms
    # that SymPy's -log(csc x + cot x) style answers obscure.
    if not definite:
        _std = {sp.csc(vsym): "log|tan(x/2)| + C",
                sp.sec(vsym): "log|sec x + tan x| + C",
                sp.tan(vsym): "log|sec x| + C",
                sp.cot(vsym): "log|sin x| + C"}
        if expr in _std and var == "x":
            return {"type": "calculus", "op": "integral",
                    "answer": _std[expr],
                    "steps": [f"∫ {integrand} dx is a standard "
                              f"form: {_std[expr]}"]}

    # Schema: ∫ sec^2(linear) / csc^2(linear) — the general
    # integrator leaves these unevaluated.
    _sec2 = None
    if isinstance(expr, sp.Pow) and expr.exp == 2 and \
            isinstance(expr.base, (sp.sec, sp.csc)):
        _u = expr.base.args[0]
        _du = sp.diff(_u, vsym)
        if _du != 0 and sp.simplify(sp.diff(_u, vsym, 2)) == 0:
            _anti_fn = sp.tan if isinstance(expr.base, sp.sec) \
                else lambda z: -sp.cot(z)
            _sec2 = _anti_fn(_u) / _du

    if definite:
        val = None
        if _sec2 is not None:
            val = sp.simplify(_sec2.subs(vsym, hi_v)
                              - _sec2.subs(vsym, lo_v))
        else:
            try:
                got = sp.integrate(expr, (vsym, lo_v, hi_v))
            except Exception:
                got = None
            if got is not None and not got.has(
                    sp.Integral, sp.zoo, sp.nan, sp.Piecewise):
                val = sp.simplify(got)
            if val is None:
                val = _w80_abs_linear_definite(
                    expr, vsym, lo_v, hi_v)
        if val is None or not val.is_number:
            return None
        steps = [f"Integrate {integrand} with respect to {var}.",
                 f"Substitute the limits {fmt(lo_v)} to "
                 f"{fmt(hi_v)}.",
                 f"Value = {fmt(val)}"]
        return {"type": "calculus", "op": "definite_integral",
                "answer": fmt(val), "steps": steps}

    # Indefinite. First two textbook schemas whose answers the
    # general integrator either misses or presents in an
    # expanded form the MCQ options do not use:
    # (a) ∫ e^x (f + f') dx = e^x f — try each subexpression
    #     of the bracket as f and check f + f' exactly.
    # (b) ∫ h(u)·u' dx by substitution — try each inner
    #     subexpression u (power base, function argument);
    #     the quotient expr/u' must be a function of u alone.
    # Both are exact checks, and the result is still verified
    # by differentiation below.
    F = _sec2
    if F is None and expr.has(sp.exp):
        try:
            _bracket = expr / sp.exp(vsym)
            if not _bracket.has(sp.exp):
                # f must be one of the bracket's sum terms
                # (asin x in 1/sqrt(1 - x^2) + asin x); the
                # check is a syntactic expand — fast, exact.
                _cands = list(_bracket.args) if isinstance(
                    _bracket, sp.Add) else [_bracket]
                for _g in _cands:
                    if not _g.has(vsym):
                        continue
                    if sp.expand(_bracket - _g - sp.diff(
                            _g, vsym)) == 0:
                        F = sp.exp(vsym) * _g
                        break
        except Exception:
            F = None
    if F is None:
        try:
            _cands = set()
            for _node in sp.preorder_traversal(expr):
                if isinstance(_node, sp.Pow) and \
                        _node.base.has(vsym):
                    _cands.add(_node.base)
                if getattr(_node, "is_Function", False) and \
                        _node.args and _node.args[0].has(vsym):
                    _cands.add(_node.args[0])
            _U = symbols("U")
            # Deepest inner expression first; u = x itself is
            # the trivial non-substitution and is excluded.
            for _u in sorted(_cands, key=lambda z: -len(str(z))):
                if _u == vsym:
                    continue
                _du = sp.diff(_u, vsym)
                if _du == 0:
                    continue
                # Plain division: Mul canonicalisation
                # already cancels u' (cancel() would EXPAND
                # the quotient and destroy the inner u).
                _quot = expr / _du
                _h = _quot.subs(_u, _U)
                if _h.has(vsym) or _h.has(sp.Integral):
                    continue
                _H = sp.integrate(_h, _U)
                if _H.has(sp.Integral, sp.zoo, sp.nan):
                    continue
                F = _H.subs(_U, _u)
                break
        except Exception:
            F = None
    if F is None:
        try:
            F = sp.integrate(expr, vsym)
        except Exception:
            return None
    if F is None or F.has(sp.Integral, sp.zoo, sp.nan):
        return None
    try:
        if sp.simplify(sp.diff(F, vsym) - expr) != 0:
            return None
    except Exception:
        return None
    steps = [f"Integrate {integrand} with respect to {var} "
             f"(standard forms / substitution).",
             f"∫ {integrand} d{var} = {fmt(F)} + C"]
    return {"type": "calculus", "op": "integral",
            "answer": f"{fmt(F)} + C", "steps": steps}


def _w80_abs_linear_definite(expr, vsym, lo_v, hi_v):
    """∫|linear| over [lo, hi]: split at the root."""
    abs_args = [a.args[0] for a in expr.atoms(sp.Abs)]
    if len(abs_args) != 1:
        return None
    arg = abs_args[0]
    if sp.diff(arg, vsym, 2) != 0:
        return None
    root = sp.solve(sp.Eq(arg, 0), vsym)
    if not root:
        return None
    r = root[0]
    if not (bool(lo_v < r) and bool(r < hi_v)):
        signed = expr.subs(sp.Abs(arg),
                           arg if sp.sign(arg.subs(
                               vsym, (lo_v + hi_v) / 2)) > 0 else -arg)
        try:
            return sp.simplify(sp.integrate(signed,
                                            (vsym, lo_v, hi_v)))
        except Exception:
            return None
    neg = expr.subs(sp.Abs(arg), -arg)
    pos = expr.subs(sp.Abs(arg), arg)
    try:
        return sp.simplify(
            sp.integrate(neg, (vsym, lo_v, r))
            + sp.integrate(pos, (vsym, r, hi_v)))
    except Exception:
        return None


def _w80_brace_continuity(q):
    """f(x) = {3x + 5, x ≥ 2; kx^2, x < 2} is continuous:
    equate the two branches at the joining point and solve
    for the parameter."""
    mb = re.search(r"\{([^}]*)\}", q)
    if not mb:
        return None
    parts = mb.group(1).split(";")
    if len(parts) != 2:
        return None
    branches = []
    for part in parts:
        mp = re.match(r"\s*(.+?)\s*,\s*x\s*(>=|<=|≥|≤|>|<)\s*"
                      r"(-?\d+(?:\.\d+)?)\s*$", part)
        if not mp:
            return None
        branches.append((mp.group(1), mp.group(2),
                         sp.Rational(mp.group(3))))
    (e1, c1, a1), (e2, c2, a2) = branches
    if a1 != a2:
        return None
    a = a1
    x = symbols("x")
    try:
        b1 = parse_expression(_w80_glue(e1))
        b2 = parse_expression(_w80_glue(e2))
    except Exception:
        return None
    params = (b1.free_symbols | b2.free_symbols) - {x}
    if len(params) != 1:
        return None
    param = next(iter(params))
    v_at = b1 if c1 in (">=", "<=", "≥", "≤") else b2
    v_other = b2 if v_at is b1 else b1
    sol = sp.solve(sp.Eq(v_at.subs(x, a), v_other.subs(x, a)),
                   param)
    if not sol:
        return None
    steps = [
        f"For continuity at x = {fmt(a)}, the two pieces must "
        f"meet: value from one side = limit from the other.",
        f"{e1.strip()} at x = {fmt(a)} gives "
        f"{fmt(v_at.subs(x, a))}; {e2.strip()} at x = {fmt(a)} "
        f"gives {fmt(v_other.subs(x, a))}.",
        f"Equating them: {param} = {fmt(sol[0])}",
    ]
    return {"type": "calculus", "op": "continuity_find_k",
            "answer": f"{param} = {fmt(sol[0])}", "steps": steps}


def solve_calculus(question: str):
    q = question.strip()

    # --- Wave 80: the ∫ glyph (board papers write integrals
    # with ∫ and Unicode limits; no earlier pattern reads the
    # glyph, so these fell through every block) ----
    if "∫" in q:
        try:
            _ri = _w80_integral(_w80_cut_options(q))
        except Exception:
            _ri = None
        if _ri is not None:
            return _ri

    # --- Wave 32: continuity / differentiability at a point ----
    _qlow = q.lower()
    if "continu" in _qlow or "differentiab" in _qlow:
        try:
            _xa, _xs = symbols("x k")
            _ma = re.search(r"at\s+x\s*=\s*(-?\d+(?:\.\d+)?)",
                            _qlow)
            _m_le = re.search(r"x\s*<=\s*(-?\d+(?:\.\d+)?)",
                              _qlow)
            _a = None
            if _ma:
                _a = sp.Rational(_ma.group(1))
            elif _m_le:
                _a = sp.Rational(_m_le.group(1))

            def _branch(region):
                region = re.sub(r"\b(if|for)\s*$", "",
                                region.strip())
                region = re.sub(r"^.*?f\(x\)\s*=", "",
                                region.strip())
                return region.strip(" ,;")

            if _m_le and _a is not None:
                _m_gt = re.search(r"x\s*>\s*-?\d+(?:\.\d+)?",
                                  _qlow)
                _fstart = _qlow.find("f(x)")
                _left = _branch(q[_fstart:_m_le.start()])
                _right = None
                if _m_gt:
                    _seg = q[_m_le.end():_m_gt.start()] \
                        if _m_gt.start() > _m_le.end() else ""
                    _seg2 = q[_m_gt.end():]
                    _cand = _branch(_seg) or _branch(
                        re.split(r"\b(is|at)\b", _seg2)[0])
                    _right = _cand
                if _left and _right:
                    _L = parse_expression(_left)
                    _R = parse_expression(_right)
                    _Lv = _L.subs(_xa, _a)
                    _Rv = _R.subs(_xa, _a)
                    if "k" in [s.name for s in
                               (_L.free_symbols
                                | _R.free_symbols)]:
                        _sol = sp.solve(sp.Eq(_Lv, _Rv), _xs)
                        if _sol:
                            _steps = [
                                f"For continuity at x = "
                                f"{_a}, LHL must equal RHL.",
                                f"LHL = {_left} at x = {_a} "
                                f"= {fmt(_Lv)}",
                                f"RHL = {_right} at x = "
                                f"{_a} = {fmt(_Rv)}",
                                f"Setting them equal: "
                                f"{fmt(_Lv)} = {fmt(_Rv)} "
                                f"gives k = {fmt(_sol[0])}",
                            ]
                            return {
                                "type": "calculus",
                                "op": "continuity_find_k",
                                "answer": f"k = "
                                          f"{fmt(_sol[0])}",
                                "steps": _steps}
                    else:
                        _cont = _Lv == _Rv
                        _steps = [
                            f"LHL = {_left} at x = {_a} = "
                            f"{fmt(_Lv)}",
                            f"RHL = {_right} at x = {_a} = "
                            f"{fmt(_Rv)}",
                            f"f({_a}) (from the x <= {_a} "
                            f"branch) = {fmt(_Lv)}",
                        ]
                        if _cont:
                            _steps.append(
                                "LHL = RHL = f(a), so f is "
                                "CONTINUOUS at the point.")
                            _ans = f"Continuous at x = {_a}"
                        else:
                            _steps.append(
                                "LHL and RHL are not equal, "
                                "so f is NOT continuous at "
                                "the point.")
                            _ans = (f"Not continuous at "
                                    f"x = {_a}")
                        return {"type": "calculus",
                                "op": "continuity_check",
                                "answer": _ans, "steps": _steps}
            if "f(x)" in _qlow and _a is not None:
                _mfx = re.search(r"f\(x\)\s*=\s*(.+?)\s+at\s+"
                                 r"x\s*=", q, re.I)
                if _mfx:
                    _text = re.sub(
                        r"\s+is\s+(?:not\s+)?(?:differentiable"
                        r"|continuous)\b.*$", "",
                        _mfx.group(1))
                    _text = re.sub(r"\|([^|]+)\|",
                                   r"abs(\1)", _text)
                    _E = parse_expression(_text)
                    _xv = _xa
                    if "abs(" in _text:
                        # diff(Abs(x)) only behaves with a
                        # REAL symbol; with a plain (complex)
                        # symbol sympy returns re/im terms
                        # whose limits raise.
                        _xv = sp.Symbol("x", real=True)
                        _E = _E.subs(_xa, _xv)
                    if "differentiab" in _qlow:
                        _cont = sp.limit(_E, _xv, _a, "-") \
                            == sp.limit(_E, _xv, _a, "+") \
                            == _E.subs(_xv, _a)
                        _lhd = sp.limit(sp.diff(_E, _xv),
                                        _xv, _a, "-")
                        _rhd = sp.limit(sp.diff(_E, _xv),
                                        _xv, _a, "+")
                        _steps = [
                            f"Left-hand derivative at "
                            f"x = {_a}: {fmt(_lhd)}",
                            f"Right-hand derivative at "
                            f"x = {_a}: {fmt(_rhd)}",
                        ]
                        if _cont and _lhd == _rhd and \
                                _lhd.is_number:
                            _steps.append(
                                "LHD = RHD and f is "
                                "continuous there, so f IS "
                                "differentiable at the "
                                "point.")
                            _ans = (f"Differentiable at "
                                    f"x = {_a}")
                        else:
                            _steps.append(
                                "The two one-sided "
                                "derivatives do not agree "
                                "(or f is not continuous "
                                "there), so f is NOT "
                                "differentiable at the "
                                "point.")
                            _ans = (f"Not differentiable "
                                    f"at x = {_a}")
                        return {"type": "calculus",
                                "op": "differentiability_check",
                                "answer": _ans,
                                "steps": _steps}
                    _lim = sp.limit(_E, _xv, _a)
                    try:
                        _val = _E.subs(_xv, _a)
                        _defined = bool(_val.is_number) and \
                            _val not in (sp.zoo, sp.nan,
                                         sp.oo, -sp.oo)
                    except Exception:
                        _defined = False
                    _steps = [
                        f"Limit of f as x -> {_a}: "
                        f"{fmt(_lim)}",
                    ]
                    if _defined and _val == _lim:
                        _steps.append(
                            f"f({_a}) = {fmt(_val)} equals "
                            f"the limit, so f is CONTINUOUS "
                            f"at x = {_a}.")
                        _ans = f"Continuous at x = {_a}"
                    elif not _defined:
                        _steps.append(
                            f"f({_a}) is NOT defined "
                            f"(denominator zero), so f is "
                            f"not continuous at x = {_a} — "
                            f"a removable discontinuity, "
                            f"since the limit exists.")
                        _ans = (f"Not continuous at "
                                f"x = {_a} (removable "
                                f"discontinuity; limit = "
                                f"{fmt(_lim)})")
                    else:
                        _steps.append(
                            f"f({_a}) = {fmt(_val)} does "
                            f"not equal the limit, so f is "
                            f"NOT continuous at x = {_a}.")
                        _ans = f"Not continuous at x = {_a}"
                    return {"type": "calculus",
                            "op": "continuity_limit",
                            "answer": _ans, "steps": _steps}
        except Exception:
            pass

    # Wave 47: "Find dy/dx if y = (3x + 2)^5" is plain
    # differentiation. It must be handled BEFORE the ODE
    # block below: _ode tries to read the right side as a
    # differential equation and raises on it, and the
    # implicit block's left side ("Find dy/dx if y") does
    # not parse either — the question errored out with no
    # answer at all (audit #272).
    _mdy = re.search(r"dy/dx\s+if\s+y\s*=\s*(.+)$", q, re.I)
    if _mdy:
        try:
            _dexpr = parse_expression(
                _mdy.group(1).strip().rstrip("."))
            _dvar = _guess_symbol(_dexpr) or symbols("x")
            _dd = _textbook_trig(diff(_dexpr, _dvar))
            return {
                "type": "calculus", "op": "derivative",
                "answer": fmt(_dd), "value": fmt(_dd),
                "steps": [f"y = {fmt(_dexpr)}",
                          f"Differentiate both sides with "
                          f"respect to {_dvar} (chain rule "
                          f"where needed).",
                          f"dy/dx = {fmt(_dd)}"],
                "latex": sp.latex(_dd)}
        except Exception:
            pass

    # Wave 100: an ask for the ORDER / DEGREE of a differential
    # equation is a fact about the equation's text, not a request
    # to solve it — answer it by inspection and never let it
    # reach dsolve (whose classifier factorisation explodes on
    # shapes like y·(y')² and burned the whole solve budget on
    # the Wave 93 audit's Hindi degree MCQ).
    _od = _ode_order_degree_result(q)
    if _od is not None:
        return _od

    # --- Wave 80: brace-form continuity (Hindi संतत stems
    # never reach the Wave 32 block, whose guard needs the
    # English word 'continu...') ----
    if "{" in q and ";" in q and ("संतत" in q or "continu" in _qlow):
        try:
            _bc = _w80_brace_continuity(q)
        except Exception:
            _bc = None
        if _bc is not None:
            return _bc

    # --- Wave 80: (d/dx)(...) derivative form ----
    _mddx = re.search(r"\(\s*d\s*/\s*d([a-z])\s*\)\s*\(", q)
    if _mddx:
        try:
            _start = _mddx.end() - 1
            _depth, _end = 0, None
            for _i in range(_start, len(q)):
                if q[_i] == "(":
                    _depth += 1
                elif q[_i] == ")":
                    _depth -= 1
                    if _depth == 0:
                        _end = _i
                        break
            if _end is not None:
                _dexpr = parse_expression(
                    _w80_glue(q[_start + 1:_end]))
                _dvar = symbols(_mddx.group(1))
                _dd = _textbook_trig(diff(_dexpr, _dvar))
                return {
                    "type": "calculus", "op": "derivative",
                    "answer": fmt(_dd), "value": fmt(_dd),
                    "steps": [f"y = {fmt(_dexpr)}",
                              f"Differentiate with respect to "
                              f"{_dvar}.",
                              f"(d/dx)({fmt(_dexpr)}) = "
                              f"{fmt(_dd)}"],
                    "latex": sp.latex(_dd)}
        except Exception:
            pass

    # --- Wave 80: Hindi derivative — 'x के सापेक्ष <expr> का
    # अवकलज' ----
    if "अवकलज" in q and "समीकरण" not in q:
        _mh = re.search(r"(.+?)\s*का\s+अवकलज", q)
        if _mh:
            try:
                _hexpr = re.sub(r"^\s*[a-zA-Z]\s*के\s+सापेक्ष\s*",
                                "", _mh.group(1)).strip()
                _dexpr = parse_expression(_w80_glue(_hexpr))
                _dvar = _guess_symbol(_dexpr) or symbols("x")
                _dd = _textbook_trig(diff(_dexpr, _dvar))
                return {
                    "type": "calculus", "op": "derivative",
                    "answer": fmt(_dd), "value": fmt(_dd),
                    "steps": [f"y = {fmt(_dexpr)}",
                              f"Differentiate with respect to "
                              f"{_dvar} (chain rule).",
                              f"dy/dx = {fmt(_dd)}"],
                    "latex": sp.latex(_dd)}
            except Exception:
                pass

    # --- Wave 80: integrating factor of dy/dx + P(x)·y = Q(x)
    # (a FACT question — it must never reach dsolve, which
    # used to churn on the prose for ~39 s) ----
    if "integrating factor" in _qlow or "समाकलन गुणक" in q:
        try:
            _stem = _w80_cut_options(q)
            _mif = re.search(r"dy/dx\s*\+\s*y\s*(.+?)\s*=", _stem)
            if _mif:
                _P = parse_expression(_w80_glue(
                    _mif.group(1).strip()))
                _xv = _guess_symbol(_P) or symbols("x")
                _intP = sp.integrate(_P, _xv)
                if not _intP.has(sp.Integral, sp.zoo, sp.nan):
                    _IF = sp.exp(_intP)
                    return {
                        "type": "calculus",
                        "op": "integrating_factor",
                        "answer": fmt(_IF),
                        "steps": [
                            "Write the equation as dy/dx + "
                            "P(x)·y = Q(x).",
                            f"Here P(x) = {fmt(_P)}.",
                            "Integrating factor = "
                            "e^(∫P(x) dx).",
                            f"∫ {fmt(_P)} dx = {fmt(_intP)}, so "
                            f"IF = {fmt(_IF)}"]}
        except Exception:
            pass

    # --- Wave 80: order and degree of a differential
    # equation. Degree = the power of the HIGHEST-order
    # derivative only; powers of lower derivatives (and
    # brackets around them) are distractors. ----
    if ("order" in _qlow and "degree" in _qlow) or \
            ("कोटि" in q and "घात" in q):
        try:
            _stem = _w80_cut_options(q)
            # Normalise every derivative spelling first: the
            # router's superscript cleaning rewrites d²y/dx²
            # as d^2y/dx^2 before the question reaches this
            # solver, and the raw Unicode form arrives on
            # direct calls — both must read identically.
            _norm = _stem.replace("d²y/dx²", "d2y/dx2") \
                .replace("d^2y/dx^2", "d2y/dx2") \
                .replace("²", "^2").replace("³", "^3")
            _flat2 = _norm.replace(" ", "")
            _orders = []
            if "d2y/dx2" in _flat2 or "y''" in _norm:
                _orders.append(2)
            if "dy/dx" in _flat2 or "y'" in _norm:
                _orders.append(1)
            if _orders:
                _ord = max(_orders)
                _deg = 1
                _tok = "d2y/dx2" if _ord == 2 else "dy/dx"
                for _mm in re.finditer(re.escape(_tok), _flat2):
                    _tail = _flat2[_mm.end():_mm.end() + 5]
                    _mp = re.match(r"(?:\))?\^(\d)", _tail)
                    if _mp:
                        _deg = int(_mp.group(1))
                        break
                return {
                    "type": "calculus", "op": "order_degree",
                    "answer": f"{_ord}, {_deg}",
                    "steps": [
                        f"The highest derivative present is of "
                        f"order {_ord}, so the order is {_ord}.",
                        f"The degree is the power of that "
                        f"highest-order derivative: {_deg}."]}
        except Exception:
            pass

    # --- Wave 80: implicit dy/dx — 'If <equation> then find
    # dy/dx' (the block below only reads the 'for ...' form)
    # ----
    if "dy/dx" in q.replace(" ", "") and "=" in q and not _mdy:
        _meq = re.search(r"(?i)^\s*if\s+", q)
        if _meq:
            try:
                _eq = q[_meq.end():]
                _eq = re.sub(r"(?i),?\s*(then\s+)?find\s+dy/dx"
                             r".*$", "", _eq).strip().rstrip(",")
                if "=" in _eq:
                    _l, _r = _eq.split("=", 1)
                    if _l.strip().lower() not in ("y", "f(x)"):
                        _xs, _ys = symbols("x y")
                        _expr = parse_expression(
                            _w80_glue(_l)) - parse_expression(
                            _w80_glue(_r))
                        if _ys in _expr.free_symbols:
                            _dydx = idiff(_expr, _ys, _xs)
                            return {
                                "type": "calculus",
                                "op": "implicit_derivative",
                                "answer": fmt(_dydx),
                                "steps": [
                                    f"Differentiate both sides "
                                    f"of {_l.strip()} = "
                                    f"{_r.strip()} with "
                                    f"respect to x, treating "
                                    f"y as a function of x.",
                                    "Collect the dy/dx terms "
                                    "and divide.",
                                    f"dy/dx = {fmt(_dydx)}"]}
            except Exception:
                pass

    # --- Wave 80: chain-rate area schemas — equilateral
    # triangle / square / circle with a numeric rate and a
    # numeric current size ----
    if "rate" in _qlow and ("increasing" in _qlow
                            or "decreasing" in _qlow):
        try:
            _mrate = re.search(r"rate\s+of\s+(\d+(?:\.\d+)?)",
                               _qlow)
            _mwhen = re.search(
                r"(?:side|radius)(?:\s+of\s+the\s+\w+)?\s+is\s+"
                r"(\d+(?:\.\d+)?)", _qlow)
            if _mrate and _mwhen:
                _rate = sp.Rational(_mrate.group(1))
                _now = sp.Rational(_mwhen.group(1))
                _sgn = -1 if "decreasing" in _qlow else 1
                if "equilateral triangle" in _qlow:
                    _val = sp.sqrt(3) / 2 * _now * _rate * _sgn
                    _steps = [
                        "For an equilateral triangle, "
                        "A = (sqrt(3)/4)·s^2, so dA/dt = "
                        "(sqrt(3)/2)·s·(ds/dt).",
                        f"dA/dt = (sqrt(3)/2) x {_now} x "
                        f"{_rate} = {fmt(_val)} cm^2/s"]
                    return {"type": "calculus",
                            "op": "rate_of_change",
                            "answer": fmt(_val), "steps": _steps}
                if "square" in _qlow:
                    _val = 2 * _now * _rate * _sgn
                    _steps = [
                        "For a square, A = s^2, so dA/dt = "
                        "2s·(ds/dt).",
                        f"dA/dt = 2 x {_now} x {_rate} = "
                        f"{fmt(_val)} cm^2/s"]
                    return {"type": "calculus",
                            "op": "rate_of_change",
                            "answer": fmt(_val), "steps": _steps}
                if "circle" in _qlow and "area" in _qlow:
                    _val = 2 * sp.pi * _now * _rate * _sgn
                    _steps = [
                        "For a circle, A = pi·r^2, so dA/dt = "
                        "2·pi·r·(dr/dt).",
                        f"dA/dt = 2 x pi x {_now} x {_rate} = "
                        f"{fmt(_val)} cm^2/s"]
                    return {"type": "calculus",
                            "op": "rate_of_change",
                            "answer": fmt(_val), "steps": _steps}
        except Exception:
            pass

    # Differential equations first: dy/dx / y' / y'' forms, or an ODE
    # written in implicit form ("y'' + y = 0"). The "for" exclusion keeps
    # implicit differentiation ("find dy/dx for x^2 + y^2 = 25") out, but
    # "solve ... for y" is an ODE request.
    ode_hint = re.search(r"(dy/dx|d2y|dsolve|differential|y'')", q, re.I) \
        or re.search(r"y'\s*=", q) or re.search(r"y'\s*[+\-*/=]", q)
    implicit_diff = bool(re.search(r"\bfor\b", q, re.I)) and not \
        re.search(r"\bsolve\b.*\bfor\b", q, re.I)
    if "=" in q and ode_hint and not implicit_diff:
        out = _ode(q)
        if out:
            return out

    # Implicit differentiation: "dy/dx for x^2 + y^2 = 25"
    if "dy/dx" in q.replace(" ", "") or re.search(r"implicit", q, re.I):
        m = re.search(r"for\s+(.+)$", q, re.I)
        eq_text = m.group(1) if m else q
        if "=" in eq_text:
            l, r = eq_text.split("=", 1)
            xs, ys = symbols("x y")
            expr = parse_expression(l) - parse_expression(r)
            dydx = idiff(expr, ys, xs)
            steps = [
                f"Differentiate both sides of {l.strip()} = {r.strip()} "
                "with respect to x, treating y as a function of x.",
                "Collect the dy/dx terms and divide.",
                f"dy/dx = {fmt(dydx)}",
            ]
            return {
                "type": "calculus",
                "op": "implicit_derivative",
                "answer": fmt(dydx),
                "steps": steps,
            }

    # Wave 47: limits in words — "Evaluate the limit of
    # (x^2 - 9)/(x - 3) as x tends to 3" (the notation
    # block below only reads lim x->3 forms; the prose
    # forms errored on the whole question — audit
    # #273-#276).
    _mlim = re.search(
        r"limit\s+of\s+(.+?)\s+as\s+([a-zA-Z])\s+"
        r"(?:tends?\s+to|approaches|→|->)\s*"
        r"(infinity|inf|-?\d+(?:\.\d+)?)\s*\.?$", _qlow)
    if _mlim:
        try:
            _lvar = symbols(_mlim.group(2))
            _lexpr = parse_expression(_mlim.group(1))
            _lto = S.Infinity if _mlim.group(3) in (
                "infinity", "inf") else sp.Rational(
                _mlim.group(3))
            _lval = sp.limit(_lexpr, _lvar, _lto)
            if _lval.is_number and not _lval.has(
                    S.NaN, S.Infinity, -S.Infinity, sp.zoo):
                _lsteps = [
                    f"Find the limit of {fmt(_lexpr)} as "
                    f"{_mlim.group(2)} -> {fmt(_lto)}.",
                ]
                try:
                    _lsub = _lexpr.subs(_lvar, _lto)
                    if _lsub.is_number and not _lsub.has(
                            S.NaN, S.Infinity, -S.Infinity):
                        _lsteps.append(
                            f"Direct substitution gives "
                            f"{fmt(_lsub)}, which is the "
                            f"limit.")
                    else:
                        _lsteps.append(
                            "Direct substitution gives an "
                            "indeterminate form, so simplify "
                            "first (factor/cancel or use a "
                            "standard limit).")
                except Exception:
                    pass
                _lsteps.append(f"Limit = {fmt(_lval)}")
                return {"type": "calculus", "op": "limit",
                        "answer": fmt(_lval),
                        "value": float(_lval),
                        "steps": _lsteps,
                        "latex": sp.latex(_lval)}
        except Exception:
            pass

    # Limit: "limit x->0 of sin(x)/x", "lim x->0 sin(x)/x"
    m = re.search(
        r"lim(?:it)?[^a-zA-Z0-9]*([a-zA-Z])\s*(?:->|→|➜)\s*([^\s,]+)", q, re.I
    )
    if m:
        var = symbols(m.group(1))
        to_raw = m.group(2)
        to_val = S.Infinity if to_raw.lower() in ("inf", "infinity", "oo") \
            else parse_expression(to_raw)
        expr_text = re.split(r"\bof\b|:", q, maxsplit=1, flags=re.I)[-1]
        expr_text = re.split(r"\bof\b|:", expr_text, maxsplit=1, flags=re.I)[-1] if False else expr_text
        expr_text = re.sub(r"lim(?:it)?\s*[a-zA-Z]\s*(?:->|→|➜)\s*[^\s,]+", "", expr_text, flags=re.I)
        # Wave 47: "Evaluate lim x->2 (x^3 - 8)/(x - 2)"
        # kept its "Evaluate" lead-in in the expression
        # text and failed to parse (audit #274).
        expr_text = re.sub(
            r"^\s*(?:evaluate|find|calculate|compute|"
            r"determine)\s+(?:the\s+)?", "", expr_text,
            flags=re.I).strip().rstrip(".")
        expr = parse_expression(expr_text)
        val = limit(expr, var, to_val)
        steps = [f"Find lim {var}->{fmt(to_val)} of {fmt(expr)}"]
        try:
            sub = expr.subs(var, to_val)
            if sub.is_number and not sub.has(S.NaN, S.Infinity, -S.Infinity):
                steps.append(
                    f"Direct substitution gives {fmt(sub)}, which is "
                    "the limit."
                )
            else:
                steps.append(
                    "Direct substitution gives an indeterminate form, "
                    "so simplify first (factor/cancel or use a standard "
                    "limit)."
                )
        except Exception:
            pass
        steps.append(f"Limit = {fmt(val)}")
        return {
            "type": "calculus",
            "op": "limit",
            "answer": fmt(val),
            "value": fmt(val),
            "steps": steps,
            "latex": sp.latex(val),
        }

    # Wave 47: applications of derivatives — rate of change
    # ("Find the rate of change of the area of a circle with
    # respect to its radius when r = 5 cm" was hijacked by
    # the plain area pattern and answered with the area
    # itself, 25·pi; correct dA/dr = 2·pi·r = 31.4159 —
    # audit #383) and tangent/normal basics ("slope of the
    # tangent to y = x^2 at x = 3" had no pattern — #286).
    if "rate of change" in _qlow:
        _mpoint = re.search(
            r"(?:when|at)\s+([a-z])\s*=\s*(-?\d+(?:\.\d+)?)",
            _qlow)
        _named47 = [
            (r"area of (?:a |the )?circle", "r", "pi*r^2",
             "Area of a circle: A = pi·r^2"),
            (r"circumference of (?:a |the )?circle", "r",
             "2*pi*r", "Circumference: C = 2·pi·r"),
            (r"volume of (?:a |the )?sphere", "r",
             "(4/3)*pi*r^3",
             "Volume of a sphere: V = (4/3)·pi·r^3"),
            (r"surface area of (?:a |the )?sphere", "r",
             "4*pi*r^2", "Surface area: S = 4·pi·r^2"),
            (r"volume of (?:a |the )?cube", "s", "s^3",
             "Volume of a cube: V = s^3"),
            (r"area of (?:a |the )?square", "s", "s^2",
             "Area of a square: A = s^2"),
        ]
        _etxt = _var = _label = None
        for _pat, _vn, _et, _lab in _named47:
            if re.search(_pat, _qlow):
                _etxt, _var, _label = _et, _vn, _lab
                break
        if _etxt is None:
            _mg = re.search(
                r"rate of change of\s+(.+?)\s+with\s+respect"
                r"\s+to\s+(?:its\s+)?([a-z])\b", _qlow)
            if _mg:
                _etxt, _var = _mg.group(1), _mg.group(2)
                _label = f"Quantity: {_etxt}"
        if _etxt is not None and _var:
            try:
                _vs = symbols(_var)
                _expr = parse_expression(_etxt)
                _deriv = diff(_expr, _vs)
                steps = [
                    _label + ".",
                    f"Differentiate with respect to {_var}: "
                    f"{fmt(_deriv)}",
                ]
                if _mpoint and _mpoint.group(1) == _var:
                    _pv = sp.Rational(_mpoint.group(2))
                    _val = _deriv.subs(_vs, _pv)
                    steps.append(
                        f"At {_var} = {fmt(_pv)}: "
                        f"{fmt(_val)} ≈ "
                        f"{fmt_num(float(_val))}")
                    _ans = (f"{fmt(_val)} ≈ "
                            f"{fmt_num(float(_val))}"
                            if _val.has(sp.pi)
                            else fmt(_val))
                    return {"type": "calculus",
                            "op": "rate_of_change",
                            "answer": _ans,
                            "value": float(_val),
                            "steps": steps}
                return {"type": "calculus",
                        "op": "rate_of_change",
                        "answer": fmt(_deriv),
                        "value": fmt(_deriv), "steps": steps}
            except Exception:
                pass

    # Wave 52: conic tangents — "equation of the tangent to
    # the circle x^2 + y^2 = 25 at (3, 4)" / "…to the parabola
    # y^2 = 4x at (1, 2)" errored before this wave (the block
    # below covers y = f(x) curves only). T = 0 forms: for the
    # circle x·x1 + y·y1 = r^2; for y^2 = kx, y·y1 = (k/2)(x +
    # x1). The point is verified ON the conic first — a point
    # that is not on it falls through rather than earning a
    # confident wrong line. Normal-to-a-conic asks stay open.
    if "tangent" in _qlow and "normal" not in _qlow \
            and ("circle" in _qlow or "parabola" in _qlow):
        _mpt = re.search(
            r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
            r"(-?\d+(?:\.\d+)?)\s*\)", q)
        if _mpt:
            _x1 = sp.Rational(_mpt.group(1))
            _y1 = sp.Rational(_mpt.group(2))
            _xs52, _ys52 = symbols("x y")
            _mc52 = re.search(
                r"x\s*\^\s*2\s*\+\s*y\s*\^\s*2\s*=\s*"
                r"(\d+(?:\.\d+)?)", _qlow)
            if _mc52 and "circle" in _qlow:
                _r2 = sp.Rational(_mc52.group(1))
                if _x1 ** 2 + _y1 ** 2 == _r2:
                    _lhs = _x1 * _xs52 + _y1 * _ys52
                    _g = 0
                    if all(v == int(v) for v in
                           (_x1, _y1, _r2)):
                        _g = math.gcd(math.gcd(abs(int(_x1)),
                                               abs(int(_y1))),
                                      abs(int(_r2)))
                    if _g > 1:
                        _lhs = _lhs / _g
                        _r2 = _r2 / _g
                    steps = [
                        "For the circle x^2 + y^2 = r^2, the "
                        "tangent at (x1, y1) is T = 0: "
                        "x·x1 + y·y1 = r^2.",
                        f"Here (x1, y1) = ({fmt(_x1)}, "
                        f"{fmt(_y1)}) and r^2 = "
                        f"{fmt(sp.Rational(_mc52.group(1)))}, "
                        f"so the tangent is "
                        f"{fmt(_lhs)} = {fmt(_r2)}.",
                    ]
                    return {"type": "calculus",
                            "op": "conic_tangent_circle",
                            "answer": f"{fmt(_lhs)} = "
                                      f"{fmt(_r2)}",
                            "steps": steps}
            _mp52 = re.search(
                r"y\s*\^\s*2\s*=\s*(\d+(?:\.\d+)?)\s*x\b",
                _qlow)
            if _mp52 and "parabola" in _qlow:
                _k = sp.Rational(_mp52.group(1))
                if _y1 ** 2 == _k * _x1:
                    _a = _k / 4
                    if _y1 == 0:
                        return {"type": "calculus",
                                "op": "conic_tangent_parabola",
                                "answer": f"x = {fmt(_x1)}",
                                "steps": [
                                    "The tangent at the vertex "
                                    "(0, 0) of y^2 = "
                                    f"{fmt(_k)}x is the y-axis "
                                    "itself, x = 0."]}
                    _mm = _k / (2 * _y1)
                    _cc = _k * _x1 / (2 * _y1)
                    _line = _mm * _xs52 + _cc
                    steps = [
                        "For the parabola y^2 = 4ax, the "
                        "tangent at (x1, y1) is T = 0: "
                        "y·y1 = 2a(x + x1).",
                        f"Here 4a = {fmt(_k)} (a = {fmt(_a)}) "
                        f"and (x1, y1) = ({fmt(_x1)}, "
                        f"{fmt(_y1)}), so "
                        f"{fmt(_y1)}·y = {fmt(_k / 2)}(x + "
                        f"{fmt(_x1)}), i.e. y = {fmt(_line)}.",
                    ]
                    return {"type": "calculus",
                            "op": "conic_tangent_parabola",
                            "answer": f"y = {fmt(_line)}",
                            "steps": steps}

    # Wave 58: tangent / normal to a CONIC at a point on it
    # (circle, parabola, ellipse, hyperbola) — see
    # _conic_tangent_normal. Runs before the y = f(x) curve
    # block below, whose "y =" hunt cannot read an implicit
    # conic equation.
    _conic = _conic_tangent_normal(q, _qlow)
    if _conic is not None:
        return _conic

    if ("tangent" in _qlow or "normal" in _qlow) \
            and "curve" in _qlow:
        _meq = re.search(r"y\s*=\s*(.+)", q)
        _mx = re.search(
            r"(?:at|when)\s+(?:the\s+point\s+)?\(?\s*"
            r"(?:x\s*=\s*)?(-?\d+(?:\.\d+)?)", _qlow)
        if _meq and _mx:
            _etext = re.split(
                r"\s+(?:at|when)\s+", _meq.group(1))[0] \
                .strip().rstrip(".")
            try:
                _xs = symbols("x")
                _f = parse_expression(_etext)
                _x0 = sp.Rational(_mx.group(1))
                _y0 = _f.subs(_xs, _x0)
                _dfull = diff(_f, _xs)
                _m = _dfull.subs(_xs, _x0)
                _want_normal = "normal" in _qlow
                if "slope" in _qlow or "equation" not in _qlow:
                    if _want_normal:
                        if _m == 0:
                            return {
                                "type": "calculus",
                                "op": "normal_slope",
                                "answer": "undefined (the "
                                          "tangent is "
                                          "horizontal, so the "
                                          "normal is vertical)",
                                "steps": [
                                    f"y = {fmt(_f)}, so "
                                    f"dy/dx = {fmt(_dfull)}",
                                    f"At x = {fmt(_x0)} the "
                                    f"tangent's slope is 0, "
                                    f"so the normal is "
                                    f"vertical and its slope "
                                    f"is undefined."]}
                        _mn = -1 / _m
                        steps = [
                            f"y = {fmt(_f)}, so dy/dx = "
                            f"{fmt(_dfull)}",
                            f"Slope of the tangent at x = "
                            f"{fmt(_x0)}: m = {fmt(_m)}",
                            f"Slope of the normal = -1/m = "
                            f"{fmt(_mn)}",
                        ]
                        return {"type": "calculus",
                                "op": "normal_slope",
                                "answer": fmt(_mn),
                                "value": float(_mn),
                                "steps": steps}
                    steps = [
                        f"y = {fmt(_f)}, so dy/dx = "
                        f"{fmt(_dfull)}",
                        f"Slope of the tangent at x = "
                        f"{fmt(_x0)} is dy/dx there = "
                        f"{fmt(_m)}",
                    ]
                    return {"type": "calculus",
                            "op": "tangent_slope",
                            "answer": fmt(_m),
                            "value": float(_m), "steps": steps}
                _mm = _m
                _kind = "tangent"
                if _want_normal:
                    _kind = "normal"
                    if _m == 0:
                        _line = None
                    else:
                        _mm = -1 / _m
                if _want_normal and _m == 0:
                    return {
                        "type": "calculus", "op": "normal_eq",
                        "answer": f"x = {fmt(_x0)}",
                        "steps": [
                            f"The tangent at x = "
                            f"{fmt(_x0)} is horizontal, so "
                            f"the normal is the vertical "
                            f"line x = {fmt(_x0)}."]}
                _line = sp.expand(_y0 + _mm * (_xs - _x0))
                steps = [
                    f"y = {fmt(_f)}, so dy/dx = "
                    f"{fmt(_dfull)}",
                    f"At x = {fmt(_x0)}: y = {fmt(_y0)} and "
                    f"the {_kind}'s slope is {fmt(_mm)}",
                    f"Equation: y - {fmt(_y0)} = "
                    f"{fmt(_mm)}(x - {fmt(_x0)}), i.e. "
                    f"y = {fmt(_line)}",
                ]
                return {"type": "calculus",
                        "op": f"{_kind}_eq",
                        "answer": f"y = {fmt(_line)}",
                        "steps": steps}
            except Exception:
                pass

    # Wave 47: maximum / minimum value of f(x) — "Find the
    # maximum value of the function f(x) = 2x^3 - 15x^2 +
    # 36x + 1" had no pattern and fell back (audit #285).
    # Solve f'(x) = 0, apply the second-derivative test,
    # and report the extreme value.
    if ("maximum value" in _qlow or "minimum value" in _qlow) \
            and "f(x)" in _qlow.replace(" ", ""):
        _want_max = "maximum value" in _qlow
        _mfx = re.search(r"f\(\s*x\s*\)\s*=\s*(.+)$", q, re.I)
        if _mfx:
            try:
                _xs = symbols("x")
                _f = parse_expression(
                    _mfx.group(1).strip().rstrip("."))
                if _f.free_symbols <= {_xs}:
                    _d1 = diff(_f, _xs)
                    _d2 = diff(_d1, _xs)
                    _crit = [r for r in sp.solve(_d1, _xs)
                             if r.is_real]
                    _hits = []
                    for _r in _crit:
                        _s = _d2.subs(_xs, _r)
                        if (_want_max and _s < 0) or \
                                (not _want_max and _s > 0):
                            _hits.append(
                                (_r, _f.subs(_xs, _r), _s))
                    if _hits:
                        _kind = "maximum" if _want_max \
                            else "minimum"
                        _best = (max if _want_max else min)(
                            _hits, key=lambda h: h[1])
                        steps = [
                            f"f(x) = {fmt(_f)}",
                            f"f'(x) = {fmt(_d1)}; setting "
                            f"f'(x) = 0 gives x = "
                            + ", ".join(fmt(h[0])
                                        for h in _hits)
                            + " (second-derivative test).",
                            f"f''({fmt(_best[0])}) = "
                            f"{fmt(_best[2])} confirms a local "
                            f"{_kind} at x = {fmt(_best[0])}.",
                            f"f({fmt(_best[0])}) = "
                            f"{fmt(_best[1])}",
                        ]
                        return {"type": "calculus",
                                "op": f"{_kind}_value",
                                "answer": fmt(_best[1]),
                                "value": float(_best[1]),
                                "steps": steps}
            except Exception:
                pass

    # Partial derivative
    m = re.search(
        r"partial\s+derivative\s+of\s+(.+?)\s+(?:with\s+respect\s+to|w\.?r\.?t\.?)\s*([a-zA-Z])",
        q, re.I,
    ) or re.search(r"∂\s*/\s*∂([a-zA-Z])\s*(?:of\s*)?(.+)$", q)
    if m:
        if m.re.pattern.startswith("partial"):
            expr_text, varname = m.group(1), m.group(2)
        else:
            varname, expr_text = m.group(1), m.group(2)
        expr = parse_expression(expr_text)
        var = symbols(varname)
        result = diff(expr, var)
        steps = [
            f"Differentiate {fmt(expr)} with respect to {varname}, "
            "treating every other variable as a constant.",
            f"Result: {fmt(result)}",
        ]
        return {
            "type": "calculus",
            "op": "partial_derivative",
            "answer": fmt(result),
            "steps": steps,
            "latex": sp.latex(result),
        }

    # d/dx style derivative
    m = re.search(r"d\s*/\s*d([a-zA-Z])\s+(?:of\s+)?(.+)$", q)
    if m:
        var = symbols(m.group(1))
        expr = parse_expression(m.group(2))
        _dres = _textbook_trig(diff(expr, var))
        return {
            "type": "calculus",
            "op": "derivative",
            "answer": fmt(_dres),
            "steps": _derivative_steps(expr, var),
            "latex": sp.latex(_dres),
        }

    # "derivative of ..." / "differentiate ..."
    if re.search(r"derivative|differentiate", q, re.I):
        text = re.sub(
            r"\b(derivative\s+of|differentiate)\b", "", q, flags=re.I
        )
        # Wave 47: "Find the derivative of sin x" kept its
        # "Find the" lead-in after the phrase removal, and
        # the parser choked on the leftover words ('Find
        # the  sin x.') — the derivative of sin x, e^(3x)
        # and log x all errored (Wave 35 audit #268 and its
        # neighbours). Strip the command lead-in and the
        # sentence's trailing full stop.
        text = re.sub(
            r"^\s*(?:find|evaluate|calculate|compute|"
            r"determine)\s+(?:the\s+)?", "", text,
            flags=re.I)
        text = re.sub(r"^\s*the\s+", "", text, flags=re.I)
        text = text.strip().rstrip(".")
        # Wave 59: "... at x = 2" asks for the derivative's
        # VALUE at the point, not the derivative expression —
        # the point clause used to poison the expression parse
        # and the ask fell to salvage ("x = 2"). Capture and
        # strip it; the value is substituted at the end.
        _at59 = None
        _mat59 = re.search(r"\bat\s+(?:the\s+point\s+)?x\s*=\s*"
                           r"(-?\d+(?:\.\d+)?)\s*\??\s*\.?\s*$",
                           text, flags=re.I)
        if _mat59:
            _at59 = sp.Rational(_mat59.group(1))
            text = text[:_mat59.start()].strip().rstrip(".")
        # Wave 56: "second derivative of x^4" — the order
        # word survived into the expression text, which the
        # parser read as s·e·c·o·n·d × x^4. Detect the
        # order from the question, strip the word, and
        # differentiate that many times.
        _ord56 = 1
        if re.search(r"\b(second|2nd)\s+derivative\b", q, re.I):
            _ord56 = 2
        elif re.search(r"\b(third|3rd)\s+derivative\b", q,
                       re.I):
            _ord56 = 3
        if _ord56 > 1:
            text = re.sub(r"\b(?:second|third|2nd|3rd)\s+",
                          "", text, flags=re.I)
        # Wave 47: the parser reads a bare "e" as a symbol,
        # so "e^(3x)" differentiated to 3·e^(3x)·log(e)
        # (shown with a stray /e). When the student writes
        # e^... it means Euler's number — swap the symbol
        # for E before differentiating (audit #269).
        def _euler(expr, src):
            if re.search(r"\be\s*\^", src):
                _es = [s for s in expr.free_symbols
                       if str(s) == "e"]
                if _es:
                    return expr.subs(_es[0], sp.E)
            return expr

        m2 = re.search(r"(.+?)\s+with\s+respect\s+to\s+([a-zA-Z])", text, re.I)
        if m2:
            expr = _euler(parse_expression(m2.group(1)), text)
            var = symbols(m2.group(2))
        else:
            expr = _euler(parse_expression(text), text)
            var = _guess_symbol(expr)
        _dres = _textbook_trig(diff(expr, var, _ord56))
        _steps56 = _derivative_steps(expr, var)
        if _ord56 > 1:
            _steps56 = _steps56 + [
                f"Differentiate {_ord56 - 1} more time(s): "
                f"the result is {fmt(_dres)}"]
        if _at59 is not None:
            _val59 = _dres.subs(var, _at59)
            _steps56 = _steps56 + [
                f"Now put x = {fmt(_at59)} in the derivative: "
                f"{fmt(_dres)}",
                f"Value at x = {fmt(_at59)} = {fmt(_val59)}"]
            return {
                "type": "calculus",
                "op": "derivative_at_point",
                "answer": fmt(_val59),
                "steps": _steps56,
                "latex": sp.latex(_val59),
            }
        return {
            "type": "calculus",
            "op": "derivative" if _ord56 == 1 else
                  "higher_derivative",
            "answer": fmt(_dres),
            "steps": _steps56,
            "latex": sp.latex(_dres),
        }

    # Integral: "integrate x^2", "integrate x from 0 to 1", "integral of x"
    # Wave 38: the pattern used to require "integrat..." — the
    # word "integral" does not contain "integrat", so EVERY
    # "integral of ..." ask missed it and fell to the
    # derivative_and_integral fallback, which parsed the whole
    # sentence into letter-soup (Wave 35 audit: integration
    # 0/6). "with respect to x" also stayed glued to the
    # integrand and broke the parse; it now names the variable.
    m = re.search(
        r"\bintegr\w*\b\s*(?:of\s*)?(.+?)\s*"
        r"(?:from\s+(.+?)\s+to\s+(.+))?$",
        q, re.I,
    )
    if m:
        expr_text = m.group(1)
        wrt_var = None
        _mwrt = re.search(
            r"\s+(?:with\s+respect\s+to|w\.?r\.?t\.?)\s*"
            r"([a-zA-Z])\s*\.?\s*$", expr_text, re.I)
        if _mwrt:
            wrt_var = _mwrt.group(1)
            expr_text = expr_text[:_mwrt.start()]
        expr_text = re.sub(r"\s*d[a-zA-Z]\s*$", "", expr_text)
        expr_text = expr_text.strip().strip(".").strip()
        wants_graph = bool(re.search(
            r"\b(graph|plot|sketch|shade|diagram)\b", q, re.I))
        bound_b = m.group(3)
        if wants_graph and bound_b:
            # "integrate x^2 from 0 to 1 and show the graph" — the lazy
            # regex swallows the graph request into the upper bound.
            mb = re.match(r"\s*(-?\d+(?:\.\d+)?|[a-zA-Z])\b", bound_b)
            if mb:
                bound_b = mb.group(1)
        if bound_b:
            bound_b = bound_b.strip().rstrip(".")
        expr = parse_expression(expr_text)
        # Wave 52: the Wave 47 Euler swap, mirrored for
        # integrals — it was applied to the derivative paths
        # only, so "Integrate e^(2x)" integrated a SYMBOL e
        # and returned a Piecewise in log(e) (and "…e^(2x) dx"
        # mangled worse). A bare e in e^... is Euler's
        # number: swap it for E before the variable is
        # guessed, so the integrand's only symbol is x.
        if re.search(r"\be\s*\^", expr_text):
            _es52 = [s for s in expr.free_symbols
                     if str(s) == "e"]
            if _es52:
                expr = expr.subs(_es52[0], sp.E)
        var = symbols(wrt_var) if wrt_var else _guess_symbol(expr)
        if m.group(2) and bound_b:
            a, b = parse_expression(m.group(2)), parse_expression(bound_b)
            val = integrate(expr, (var, a, b))
            out = {
                "type": "calculus",
                "op": "definite_integral",
                "answer": fmt(val),
                "value": fmt(val),
                "steps": _integral_steps(expr, var, (a, b)),
                "latex": sp.latex(val),
            }
            if wants_graph:
                try:
                    from .plotting import solve_plot_area
                    out["image"] = solve_plot_area(expr, var, a, b)
                    out["steps"] = out["steps"] + [
                        "The shaded region in the graph is exactly "
                        "this area under the curve."
                    ]
                except Exception:
                    pass
            return out
        val = integrate(expr, var)
        return {
            "type": "calculus",
            "op": "integral",
            "answer": f"{fmt(val)} + C",
            "value": fmt(val),
            "steps": _integral_steps(expr, var),
            "latex": sp.latex(val),
        }

    # Fallback: report both derivative and integral of the expression.
    expr = parse_expression(q)
    var = _guess_symbol(expr)
    return {
        "type": "calculus",
        "op": "derivative_and_integral",
        "answer": f"derivative: {fmt(diff(expr, var))}; "
                  f"integral: {fmt(integrate(expr, var))} + C",
        "derivative": fmt(diff(expr, var)),
        "integral": fmt(integrate(expr, var)),
        "steps": _derivative_steps(expr, var),
    }
