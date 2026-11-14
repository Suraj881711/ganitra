"""Algebra: equations, systems, inequalities, factor/expand/simplify.

Every solver returns a dict with at least:
  type, op, answer (string), steps (list of strings)
Equations also return `solutions` (list of strings).
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, is_equation, parse_expression

x, y = sp.symbols("x y")


def _strip_solve_prefix(q: str) -> str:
    q = re.sub(r"^\s*(solve|find|work\s+out)\b", "", q, flags=re.I).strip()
    # Wave 33: lead-ins and method suffixes used to be parsed
    # as VARIABLES — "Solve the quadratic equation 2x^2 - 7x
    # + 3 = 0" answered a letter-soup "a = 2^(2/3)·(7/(c·d…"
    # and "Find the roots of 1/(x+4) - … = 11/30" failed to
    # parse at all. Strip them so the bare equation remains.
    # (The no-"=" "roots of" polynomial form is handled
    # earlier by the zeroes block; this only affects the
    # equation path.)
    q = re.sub(
        r"^(the\s+)?(roots?|zeroes|zeros|solutions?|values?)"
        r"\s+of\s+(the\s+)?(quadratic\s+)?"
        r"(equation|polynomial)?\s*", "", q, flags=re.I).strip()
    q = re.sub(r"^(the\s+)?(following\s+)?(quadratic\s+)?"
               r"equation\s+", "", q, flags=re.I).strip()
    q = re.sub(
        r"\s+by\s+(completing\s+the\s+square|factorisation|"
        r"factorization|factoring|splitting\s+the\s+middle\s+"
        r"term|the\s+quadratic\s+formula|quadratic\s+formula)"
        r"\b.*$", "", q, flags=re.I).strip()
    q = re.sub(
        r"\s+using\s+(the\s+)?(quadratic\s+formula|"
        r"completing\s+the\s+square)\b.*$", "", q,
        flags=re.I).strip()
    # Wave 33: a trailing domain restriction ("..., x not
    # equal to -4 and 7") is not part of the equation.
    q = re.sub(
        r",?\s*\bx\s*(?:not\s+equal\s+to|≠|!=)\s*"
        r"-?\d+(?:\s*(?:,|and|or)\s*-?\d+)*\s*\.?\s*$",
        "", q, flags=re.I).strip()
    return q.strip(" :.")


def _poly_coeffs(expr, var):
    """Return (degree, {power: coeff}) if expr is a polynomial in var."""
    try:
        poly = sp.Poly(sp.expand(expr), var)
    except Exception:
        return None, {}
    return poly.degree(), {p: poly.nth(p) for p in range(poly.degree() + 1)}


def _linear_steps(a, b, var):
    """Steps for a*var + b = 0 (a != 0)."""
    steps = [f"Bring all terms to one side: {fmt(a)}·{var} + {fmt(b)} = 0"]
    if b != 0:
        verb = "Subtract" if b > 0 else "Add"
        steps.append(
            f"{verb} {fmt(abs(b))} from both sides: "
            f"{fmt(a)}·{var} = {fmt(-b)}"
        )
    if a != 1:
        steps.append(
            f"Divide both sides by {fmt(a)}: {var} = {fmt(sp.nsimplify(-b / a, rational=True))}"
        )
    return steps


def _quadratic_steps(a, b, c, var):
    D = b**2 - 4 * a * c
    steps = [
        f"Write in standard form: {fmt(a)}·{var}^2 + {fmt(b)}·{var} + "
        f"{fmt(c)} = 0, so a = {fmt(a)}, b = {fmt(b)}, c = {fmt(c)}",
        f"Discriminant D = b^2 - 4ac = ({fmt(b)})^2 - 4·{fmt(a)}·{fmt(c)} "
        f"= {fmt(D)}",
    ]
    if D > 0:
        steps.append("D > 0, so there are two distinct real roots.")
    elif D == 0:
        steps.append("D = 0, so there is one repeated real root.")
    else:
        steps.append("D < 0, so the roots are complex (non-real).")
    steps.append(
        f"Quadratic formula: {var} = (-b ± sqrt(D)) / (2a) = "
        f"({fmt(-b)} ± sqrt({fmt(D)})) / {fmt(2 * a)}"
    )
    return steps


def _solve_single_equation(eq_text: str):
    left, right = eq_text.split("=", 1)
    expr = parse_expression(left) - parse_expression(right)
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    if not symbols:
        return {
            "type": "algebra",
            "op": "equation",
            "answer": "The equation has no variable to solve for.",
            "solutions": [],
            "steps": [f"Simplify both sides: {fmt(expr)} = 0"],
        }
    var = symbols[0]
    degree, coeffs = _poly_coeffs(expr, var)
    steps = []
    if degree == 1:
        steps = _linear_steps(coeffs.get(1, 0), coeffs.get(0, 0), var)
    elif degree == 2:
        steps = _quadratic_steps(
            coeffs.get(2, 0), coeffs.get(1, 0), coeffs.get(0, 0), var
        )
    else:
        steps = [
            f"Move everything to one side: {fmt(expr)} = 0",
            "Solve for " + str(var) + " using symbolic methods (SymPy).",
        ]
    sols = sp.solve(expr, var)
    sol_strs = [fmt(s) for s in sols]
    answer = ", ".join(f"{var} = {s}" for s in sol_strs) or "No solution"
    steps.append(f"Solution: {answer}")
    result = {
        "type": "algebra",
        "op": "equation",
        "answer": answer,
        "solutions": sol_strs,
        "steps": steps,
    }
    try:
        result["latex"] = sp.latex(sp.Eq(parse_expression(left), parse_expression(right)))
    except Exception:
        pass
    return result


# ---------------------------------------------------------------
# Wave 38: the Class 9/10 system phrasing "If a + b = 10 and
# a - b = 4, find a and b" reached _solve_system, whose split
# on "and" fed the tail ", find a" into the expression parser
# — the letters of "find" became symbols and the answer was
# complex garbage in f and I (Wave 35 audit #62-65, and the
# Hindi form #471 never parsed at all). The two helpers below
# recognise the pattern directly from the raw question text:
# exactly two linear equations in the same two single-letter
# unknowns, wherever they sit in the sentence (English or
# Hindi), plus the a±b / ab identity-value asks (#100).
# ---------------------------------------------------------------
_EQ2_RE = re.compile(
    r"(?<![a-zA-Z])(\d+(?:\.\d+)?)?\s*([a-z])\s*([+\-])\s*"
    r"(\d+(?:\.\d+)?)?\s*([a-z])\s*=\s*"
    r"(-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?)")


def _rat(s):
    return sp.Rational(str(s).replace(" ", ""))


def _term_str(coef, var):
    if coef == 1:
        return var
    if coef == -1:
        return f"-{var}"
    return f"{fmt(coef)}·{var}"


def _eq_str(a, u, b, v):
    left = _term_str(a, u)
    if b >= 0:
        left += " + " + _term_str(b, v).lstrip("-")
    else:
        left += " - " + _term_str(-b, v)
    return left


def _solve_two_linear(q: str):
    ql = q.lower()
    ms = list(_EQ2_RE.finditer(ql))
    if len(ms) != 2:
        return None
    for m in ms:
        # A leading '-' before the first term ("-a + b = 3") is
        # not captured by the pattern — decline rather than
        # solve the wrong system.
        j = m.start() - 1
        while j >= 0 and ql[j] == " ":
            j -= 1
        if j >= 0 and ql[j] == "-":
            return None
    (c1, u1, s1, c2, v1, r1), (c3, u2, s2, c4, v2, r2) = (
        m.groups() for m in ms)
    if u1 == v1 or u2 == v2 or {u1, v1} != {u2, v2}:
        return None
    u, v = u1, v1
    a1 = _rat(c1) if c1 else sp.Integer(1)
    b1 = (_rat(c2) if c2 else sp.Integer(1)) * (1 if s1 == "+" else -1)
    a2 = sp.Integer(0)
    b2 = sp.Integer(0)
    for coef_s, letter, sign in ((c3, u2, "+"), (c4, v2, s2)):
        coef = (_rat(coef_s) if coef_s else sp.Integer(1)) * (
            1 if sign == "+" else -1)
        if letter == u:
            a2 = coef
        else:
            b2 = coef
    r1, r2 = _rat(r1), _rat(r2)
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    xv = (r1 * b2 - r2 * b1) / det
    yv = (a1 * r2 - a2 * r1) / det
    eq1 = f"{_eq_str(a1, u, b1, v)} = {fmt(r1)}"
    eq2 = f"{_eq_str(a2, u, b2, v)} = {fmt(r2)}"
    steps = [f"Equations: {eq1} and {eq2}"]
    if abs(a1) == 1 and abs(a2) == 1 and a1 == a2:
        # Classic sum/difference shape: one clean elimination.
        if b1 == -b2:
            tot = r1 + r2
            steps.append(
                f"Add the two equations — the {v} terms cancel: "
                f"2·{u} = {fmt(tot)}, so {u} = {fmt(xv)}")
            steps.append(
                f"Put {u} = {fmt(xv)} in equation (1): "
                f"{v} = {fmt(yv)}")
        elif b1 == b2:
            dif = r1 - r2
            steps.append(
                f"Subtract equation (2) from equation (1) — "
                f"the {u} terms cancel: 2·{v} = {fmt(dif)}, "
                f"so {v} = {fmt(yv)}")
            steps.append(
                f"Put {v} = {fmt(yv)} in equation (1): "
                f"{u} = {fmt(xv)}")
    if len(steps) == 1:
        steps.append(
            f"Solving the two equations together (elimination) "
            f"gives {u} = {fmt(xv)} and {v} = {fmt(yv)}")
        steps.append(
            f"Check: {_eq_str(a1, u, b1, v)} with these values "
            f"= {fmt(a1 * xv + b1 * yv)} ✓")
    answer = f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"
    steps.append(f"Solution: {answer}")
    return {
        "type": "algebra",
        "op": "system",
        "answer": answer,
        "solutions": [fmt(xv), fmt(yv)],
        "steps": steps,
    }


def _identity_value(q: str):
    """'If a - b = 4 and ab = 21, find a^2 + b^2' (audit #100)
    and its (a+b)^2 / (a-b)^2 siblings."""
    ql = q.lower().replace("²", "^2")
    m_prod = re.search(r"\b([a-z])\s*\*?\s*([a-z])\s*=\s*"
                       r"(-?\d+(?:\.\d+)?)", ql)
    m_pm = re.search(r"\b([a-z])\s*([+\-])\s*([a-z])\s*=\s*"
                     r"(-?\d+(?:\.\d+)?)", ql)
    if not m_prod or not m_pm:
        return None
    u, v = m_pm.group(1), m_pm.group(3)
    if {m_prod.group(1), m_prod.group(2)} != {u, v} or u == v:
        return None
    P = _rat(m_prod.group(3))
    D = _rat(m_pm.group(4))
    sign = m_pm.group(2)
    given = f"{u} {'+' if sign == '+' else '-'} {v} = {fmt(D)}"
    steps = [f"Given: {given} and {u}{v} = {fmt(P)}"]
    if re.search(rf"\b{u}\s*\^\s*2\s*\+\s*{v}\s*\^\s*2\b", ql):
        if sign == "-":
            val = D ** 2 + 2 * P
            steps.append(
                f"({u} - {v})^2 = {u}^2 + {v}^2 - 2{u}{v}, so "
                f"{u}^2 + {v}^2 = ({fmt(D)})^2 + 2·{fmt(P)} "
                f"= {fmt(val)}")
        else:
            val = D ** 2 - 2 * P
            steps.append(
                f"({u} + {v})^2 = {u}^2 + {v}^2 + 2{u}{v}, so "
                f"{u}^2 + {v}^2 = ({fmt(D)})^2 - 2·{fmt(P)} "
                f"= {fmt(val)}")
        return {"type": "algebra", "op": "identity_value",
                "answer": fmt(val), "value": float(val),
                "steps": steps}
    m_t = re.search(r"\(\s*([a-z])\s*([+\-])\s*([a-z])\s*\)"
                    r"\s*\^\s*2", ql)
    if m_t and m_t.group(1) == u and m_t.group(3) == v:
        tsign = m_t.group(2)
        if tsign == sign:
            val = D ** 2
            steps.append(f"That is just ({given.split(' = ')[0]})^2 "
                         f"= ({fmt(D)})^2 = {fmt(val)}")
        elif sign == "-":
            val = D ** 2 + 4 * P
            steps.append(
                f"({u} + {v})^2 = ({u} - {v})^2 + 4{u}{v} "
                f"= ({fmt(D)})^2 + 4·{fmt(P)} = {fmt(val)}")
        else:
            val = D ** 2 - 4 * P
            steps.append(
                f"({u} - {v})^2 = ({u} + {v})^2 - 4{u}{v} "
                f"= ({fmt(D)})^2 - 4·{fmt(P)} = {fmt(val)}")
        return {"type": "algebra", "op": "identity_value",
                "answer": fmt(val), "value": float(val),
                "steps": steps}
    return None


def _solve_system(eq_text: str):
    parts = [p for p in re.split(r";|\band\b|,", eq_text) if "=" in p]
    eqs, syms = [], set()
    for p in parts:
        l, r = p.split("=", 1)
        e = parse_expression(l) - parse_expression(r)
        eqs.append(e)
        syms |= e.free_symbols
    syms = sorted(syms, key=lambda s: s.name)
    steps = [f"Equations: " + "; ".join(f"{fmt(e)} = 0" for e in eqs)]
    sol = sp.solve(eqs, list(syms), dict=True)
    if not sol:
        return {
            "type": "algebra",
            "op": "system",
            "answer": "No solution (the system is inconsistent).",
            "solutions": [],
            "steps": steps + ["The equations have no common solution."],
        }
    s0 = sol[0]
    if len(syms) == 2 and len(eqs) == 2:
        v0, v1 = syms
        try:
            expr0 = sp.solve(eqs[0], v0)
            if expr0:
                steps.append(f"From equation (1): {v0} = {fmt(expr0[0])}")
                sub = sp.expand(eqs[1].subs(v0, expr0[0]))
                steps.append(
                    f"Substitute into equation (2): {fmt(sub)} = 0"
                )
                s1 = sp.solve(sub, v1)
                if s1:
                    steps.append(f"Solve for {v1}: {v1} = {fmt(s1[0])}")
                    back = expr0[0].subs(v1, s1[0])
                    steps.append(
                        f"Back-substitute: {v0} = {fmt(sp.simplify(back))}"
                    )
        except Exception:
            pass
    answer = ", ".join(f"{k} = {fmt(v)}" for k, v in s0.items())
    steps.append(f"Solution: {answer}")
    return {
        "type": "algebra",
        "op": "system",
        "answer": answer,
        "solutions": [fmt(v) for v in s0.values()],
        "steps": steps,
    }


def _solve_inequality(q: str):
    m = re.search(r"(<=|>=|<|>)", q)
    op = m.group(1)
    left, right = q[: m.start()], q[m.end() :]
    left = _strip_solve_prefix(left)
    expr_l, expr_r = parse_expression(left), parse_expression(right)
    expr = expr_l - expr_r
    symbols = sorted(expr.free_symbols, key=lambda s: s.name)
    var = symbols[0] if symbols else x
    steps = [f"Move all terms to one side: {fmt(expr)} {op} 0"]
    degree, coeffs = _poly_coeffs(expr, var)
    if degree == 1:
        a, b = coeffs.get(1, 0), coeffs.get(0, 0)
        steps.append(f"Isolate {var}: {fmt(a)}·{var} {op} {fmt(-b)}")
        if a != 0 and a < 0:
            flip = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}[op]
            steps.append(
                f"Divide by {fmt(a)} (negative), so flip the inequality "
                f"sign: {var} {flip} {fmt(sp.nsimplify(-b / a, rational=True))}"
            )
        elif a != 0:
            steps.append(
                f"Divide by {fmt(a)}: {var} {op} "
                f"{fmt(sp.nsimplify(-b / a, rational=True))}"
            )
    rel = {"<": sp.Lt, "<=": sp.Le, ">": sp.Gt, ">=": sp.Ge}[op]
    sol = sp.solveset(rel(expr_l, expr_r, evaluate=False), var, domain=sp.S.Reals)
    answer = fmt(sol).replace("Interval", "")
    steps.append(f"Solution set: {fmt(sol)}")
    return {
        "type": "algebra",
        "op": "inequality",
        "answer": str(sol),
        "solutions": [str(sol)],
        "steps": steps,
    }


def solve_algebra(question: str):
    q = question.strip()

    # Wave 30: polynomial division ("Divide x^3 + 3x^2 + 3x + 1
    # by x + 1") and zeroes of a polynomial ("Find the zeroes of
    # the polynomial x^2 - 3x - 10"). Both used to fall through
    # to the bare-expression simplifier, which returned a stray
    # fragment (the fallback then salvaged junk like "-1").
    _md = re.match(
        r"\s*(?:divide|division\s+of)\s+(.+?)\s+by\s+(.+?)\s*"
        r"\.?\s*$", q, re.I)
    if _md and re.search(r"[a-z]\s*\^|[a-z]\s*\*\*",
                         _md.group(1)):
        try:
            _dividend = parse_expression(_md.group(1))
            _divisor = parse_expression(_md.group(2))
            _syms = sorted((_dividend + _divisor).free_symbols,
                           key=lambda s: s.name)
            if len(_syms) == 1:
                _var = _syms[0]
                _quot, _rem = sp.div(sp.Poly(_dividend, _var),
                                     sp.Poly(_divisor, _var))
                _steps = [
                    f"Divide {fmt(_dividend)} by "
                    f"{fmt(_divisor)} (polynomial long "
                    f"division, highest degree first).",
                    f"Quotient = {fmt(_quot.as_expr())}",
                ]
                if _rem.is_zero:
                    _steps.append(
                        "Remainder = 0, so the divisor is a "
                        "factor of the dividend.")
                    _ans = fmt(_quot.as_expr())
                else:
                    _steps.append(
                        f"Remainder = {fmt(_rem.as_expr())}")
                    _ans = (f"{fmt(_quot.as_expr())} "
                            f"(remainder {fmt(_rem.as_expr())})")
                return {"type": "algebra",
                        "op": "polynomial_division",
                        "answer": _ans, "steps": _steps}
        except Exception:
            pass
    # --- Wave 32: remainder / factor theorem, cubic zeroes ----
    # --- relations, verify-zeroes, rationalisation -------------
    _qlow = q.lower()
    try:
        if "remainder" in _qlow and "divided by" in _qlow:
            _mr = re.search(
                r"when\s+(.+?)\s+is\s+divided\s+by\s+"
                r"(.+?)\s*\.?\s*$", q, re.I) or re.search(
                    r"^(.+?)\s+is\s+divided\s+by\s+"
                    r"(.+?)\s*\.?\s*$", q, re.I)
            if _mr:
                _P = parse_expression(_mr.group(1))
                _D = parse_expression(_mr.group(2))
                _syms = sorted(_P.free_symbols,
                               key=lambda s: s.name)
                if len(_syms) == 1:
                    _var = _syms[0]
                    _rem = sp.rem(sp.Poly(_P, _var),
                                  sp.Poly(_D, _var), _var)
                    _root = sp.solve(_D, _var)
                    _steps = [
                        f"Remainder theorem: the remainder on "
                        f"dividing by {fmt(_D)} equals "
                        f"P({_root[0] if _root else ''}) — the "
                        f"value of the polynomial where the "
                        f"divisor is zero.",
                        f"Remainder = {fmt(_rem.as_expr())}",
                    ]
                    return {"type": "algebra",
                            "op": "remainder_theorem",
                            "answer": fmt(_rem.as_expr()),
                            "steps": _steps}
        if "is a factor of" in _qlow and (
                "find" in _qlow and re.search(r"\bk\b", _qlow)):
            _mf = re.search(r"(.+?)\s+is\s+a\s+factor\s+of\s+"
                            r"(.+?)\s*\.?\s*$", q, re.I)
            if _mf:
                _left, _poly_text = _mf.group(1), _mf.group(2)
                _pm = re.search(r"\(([^()]*)\)\s*$",
                                _left.strip())
                _div_text = _pm.group(1) if _pm else \
                    _left.strip().split()[-3:]
                if not isinstance(_div_text, str):
                    _div_text = " ".join(_div_text)
                _D = parse_expression(_div_text)
                _P = parse_expression(_poly_text)
                _syms = sorted(_P.free_symbols,
                               key=lambda s: s.name)
                if len(_syms) == 2:
                    _var = [s for s in _syms
                            if s.name == "x"][0]
                    _par = [s for s in _syms if s is not _var][0]
                    _root = sp.solve(_D, _var)[0]
                    _eq = _P.subs(_var, _root)
                    _sol = sp.solve(_eq, _par)
                    if _sol:
                        _steps = [
                            f"If {fmt(_D)} is a factor, then "
                            f"P({_root}) must be 0 "
                            f"(factor theorem).",
                            f"P({_root}) = {fmt(_eq)} = 0 "
                            f"gives {_par} = {fmt(_sol[0])}",
                        ]
                        return {"type": "algebra",
                                "op": "factor_theorem_k",
                                "answer": f"{_par} = "
                                          f"{fmt(_sol[0])}",
                                "steps": _steps}
        if re.search(r"\ba\s+factor\s+of\b", _qlow) and not (
                "is a factor of" in _qlow and "find" in _qlow):
            _mf = re.search(r"is\s+(.+?)\s+a\s+factor\s+of\s+"
                            r"(.+?)\s*\??\s*$", q, re.I)
            if _mf:
                _D = parse_expression(_mf.group(1))
                _P = parse_expression(_mf.group(2))
                _syms = sorted(_P.free_symbols,
                               key=lambda s: s.name)
                if len(_syms) == 1:
                    _var = _syms[0]
                    _rem = sp.rem(sp.Poly(_P, _var),
                                  sp.Poly(_D, _var), _var)
                    _root = sp.solve(_D, _var)
                    _steps = [
                        f"Divide: the remainder on dividing "
                        f"{fmt(_P)} by {fmt(_D)} is "
                        f"{fmt(_rem.as_expr())} (equivalently "
                        f"P({_root[0] if _root else ''})).",
                    ]
                    if _rem.is_zero:
                        _steps.append("Remainder is 0, so YES, "
                                      "it is a factor.")
                        _ans = "Yes, it is a factor"
                    else:
                        _steps.append("Remainder is not 0, so "
                                      "it is NOT a factor.")
                        _ans = (f"No, not a factor (remainder "
                                f"{fmt(_rem.as_expr())})")
                    return {"type": "algebra",
                            "op": "factor_theorem_check",
                            "answer": _ans, "steps": _steps}
        if "verify" in _qlow and ("zeroes" in _qlow
                                  or "zeros" in _qlow):
            _mv = re.search(r"that\s+(.+?)\s+are\s+"
                            r"(?:the\s+)?(?:zeroes|zeros)", q,
                            re.I)
            _mp = re.search(r"polynomial\s+(.+?)\s*\.?\s*$",
                            q, re.I)
            if _mv and _mp:
                _vals = [float(v) if "." in v else int(v)
                         for v in re.findall(
                             r"-?\d+(?:\.\d+)?", _mv.group(1))]
                _P = parse_expression(_mp.group(1))
                _syms = sorted(_P.free_symbols,
                               key=lambda s: s.name)
                if len(_syms) == 1 and _vals:
                    _var = _syms[0]
                    _checks = [(v, sp.expand(
                        _P.subs(_var, v))) for v in _vals]
                    _steps = [
                        f"P({v}) = {fmt(val)}" +
                        (" ✔" if val == 0 else " ✘")
                        for v, val in _checks]
                    if all(val == 0 for _, val in _checks):
                        _ans = ("Verified: all are zeroes of "
                                "the polynomial")
                    else:
                        _bad = [str(v) for v, val in _checks
                                if val != 0]
                        _ans = ("Not all are zeroes: " +
                                ", ".join(_bad) +
                                " is/are not")
                    return {"type": "algebra",
                            "op": "verify_zeroes",
                            "answer": _ans, "steps": _steps}
        if ("α" in q or "alpha" in _qlow) and \
                "polynomial" in _qlow:
            _mp = re.search(r"polynomial\s+(.+?)(?:,|\s+find"
                            r"\b|\s*$)", q, re.I)
            if _mp:
                _P = parse_expression(_mp.group(1))
                _syms = sorted(_P.free_symbols,
                               key=lambda s: s.name)
                if len(_syms) == 1:
                    _var = _syms[0]
                    _poly = sp.Poly(_P, _var)
                    if _poly is not None and \
                            _poly.degree() == 3:
                        _cf = _poly.all_coeffs()
                        _a, _b, _c, _d = _cf
                        _s1 = sp.simplify(-_b / _a)
                        _s2 = sp.simplify(_c / _a)
                        _s3 = sp.simplify(-_d / _a)
                        _steps = [
                            f"For a cubic a·x^3 + b·x^2 + "
                            f"c·x + d with a = {fmt(_a)}, "
                            f"b = {fmt(_b)}, c = {fmt(_c)}, "
                            f"d = {fmt(_d)}:",
                            f"α + β + γ = -b/a = {fmt(_s1)}",
                            f"αβ + βγ + γα = c/a = {fmt(_s2)}",
                            f"αβγ = -d/a = {fmt(_s3)}",
                        ]
                        return {"type": "algebra",
                                "op": "cubic_zeroe_relations",
                                "answer": f"α + β + γ = "
                                          f"{fmt(_s1)}, "
                                          f"αβ + βγ + γα = "
                                          f"{fmt(_s2)}, "
                                          f"αβγ = {fmt(_s3)}",
                                "steps": _steps}
        if "rationalise" in _qlow or "rationalize" in _qlow:
            _mrat = re.search(
                r"rationali[sz]e\s+(?:the\s+denominator\s+of"
                r"\s+)?(.+?)\s*\.?\s*$", q, re.I)
            if _mrat:
                _E = parse_expression(_mrat.group(1))

                def _has_sqrt(_e):
                    return any(
                        isinstance(_a, sp.Pow)
                        and _a.exp == sp.Rational(1, 2)
                        for _a in _e.atoms(sp.Pow))
                # Prefer the RAW numerator/denominator:
                # sp.together() silently rationalises simple
                # monomial denominators itself (5/sqrt(7) ->
                # 5*sqrt(7)/7), which would hide the sqrt this
                # branch exists to remove.
                _num, _den = sp.fraction(_E)
                if not _has_sqrt(_den):
                    _num, _den = sp.fraction(sp.together(_E))
                if _has_sqrt(_den):
                    if isinstance(_den, sp.Add):
                        _terms = list(_den.args)
                        _conj = sum(_terms[:-1]) - _terms[-1]
                    else:
                        _conj = -_den
                    _prod = sp.expand(_den * _conj)
                    if not _has_sqrt(_prod):
                        _res = sp.simplify(
                            _num * _conj / _prod)
                        _steps = [
                            f"Multiply top and bottom by "
                            f"the conjugate {fmt(_conj)}:",
                            f"= {fmt(_res)}",
                        ]
                        return {"type": "algebra",
                                "op": "rationalise",
                                "answer": fmt(_res),
                                "steps": _steps}
                elif "sqrt" in _mrat.group(1) and \
                        not _E.free_symbols:
                    # Sympy already rationalised a simple
                    # monomial denominator while parsing
                    # (5/sqrt(7) is stored as 5*sqrt(7)/7);
                    # that stored value IS the rationalised
                    # form.
                    _res = sp.simplify(_E)
                    _steps = [
                        "Multiply the numerator and "
                        "denominator by the root in the "
                        "denominator so it becomes a whole "
                        "number:",
                        f"= {fmt(_res)}",
                    ]
                    return {"type": "algebra",
                            "op": "rationalise",
                            "answer": fmt(_res),
                            "steps": _steps}
    except Exception:
        pass
    _mz = re.search(
        r"(?:zeroes|zeros|roots)\s+of\s+(?:the\s+)?"
        r"(?:polynomial|equation)?\s*(.+)$", q, re.I)
    if _mz and "=" not in q:
        _expr_text = _mz.group(1).strip().rstrip(".")
        _expr_text = re.split(
            r"\s+and\s+(?:verify|check|show)\b", _expr_text)[0]\
            .strip()
        if _expr_text:
            try:
                _res = _solve_single_equation(_expr_text + " = 0")
                _res["steps"] = [
                    "The zeroes of a polynomial are the values "
                    "of the variable that make it 0 — solve "
                    f"{_expr_text} = 0."] + _res["steps"]
                _res["op"] = "zeroes"
                return _res
            except Exception:
                pass

    # factor / expand / simplify commands
    m = re.match(r"\s*(factorise|factorize|factor)\b[:\s]*(.+)$", q, re.I)
    if m:
        expr = parse_expression(m.group(2))
        factored = sp.factor(expr)
        steps = [f"Factorise {fmt(expr)}"]
        var = sorted(expr.free_symbols, key=lambda s: s.name)
        if var:
            roots = sp.solve(expr, var[0])
            real_roots = [r for r in roots if r.is_real]
            if real_roots:
                steps.append(
                    "Find the roots: "
                    + ", ".join(f"{var[0]} = {fmt(r)}" for r in real_roots)
                    + " — each root r gives a factor "
                    f"({var[0]} - r)"
                )
        steps.append(f"= {fmt(factored)}")
        return {
            "type": "algebra",
            "op": "factor",
            "answer": fmt(factored),
            "steps": steps,
            "latex": sp.latex(factored),
        }
    m = re.match(r"\s*expand\b[:\s]*(.+)$", q, re.I)
    if m:
        expr = parse_expression(m.group(1))
        expanded = sp.expand(expr)
        steps = [
            f"Multiply out the brackets in {fmt(expr)} term by term "
            "(FOIL for two brackets).",
            f"= {fmt(expanded)}",
        ]
        return {
            "type": "algebra",
            "op": "expand",
            "answer": fmt(expanded),
            "steps": steps,
            "latex": sp.latex(expanded),
        }
    m = re.match(r"\s*simplify\b[:\s]*(.+)$", q, re.I)
    if m:
        expr = parse_expression(m.group(1))
        simplified = sp.trigsimp(sp.simplify(expr))
        steps = [
            f"Simplify {fmt(expr)}: cancel common factors and combine "
            "like terms.",
            f"= {fmt(simplified)}",
        ]
        return {
            "type": "algebra",
            "op": "simplify",
            "answer": fmt(simplified),
            "steps": steps,
            "latex": sp.latex(simplified),
        }

    if re.search(r"(<=|>=|<|>)", q):
        return _solve_inequality(q)

    # Wave 38: exact two-linear-equation and identity-value
    # patterns read the RAW question (the generic system path
    # below mangles any sentence wrapped around the equations).
    _idv = _identity_value(q)
    if _idv is not None:
        return _idv
    _two = _solve_two_linear(q)
    if _two is not None:
        return _two

    eq_text = _strip_solve_prefix(q)
    n_eq = eq_text.count("=")
    if n_eq >= 2:
        return _solve_system(eq_text)
    if is_equation(eq_text) or n_eq == 1:
        return _solve_single_equation(eq_text)

    # Bare symbolic expression: simplify it.
    expr = parse_expression(q)
    simplified = sp.simplify(expr)
    return {
        "type": "algebra",
        "op": "simplify",
        "answer": fmt(simplified),
        "steps": [f"Simplify {fmt(expr)}", f"= {fmt(simplified)}"],
        "latex": sp.latex(simplified),
    }
