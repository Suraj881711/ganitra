"""Calculus: limits, derivatives (incl. partial & implicit), integrals,
and basic differential equations — with step-by-step working.
"""
import re

import sympy as sp
from sympy import S, diff, dsolve, idiff, integrate, limit, symbols

from .expression_parser import fmt, fmt_num, parse_expression

_x = symbols("x")


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


def solve_calculus(question: str):
    q = question.strip()

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
        _dres = _textbook_trig(diff(expr, var))
        return {
            "type": "calculus",
            "op": "derivative",
            "answer": fmt(_dres),
            "steps": _derivative_steps(expr, var),
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
