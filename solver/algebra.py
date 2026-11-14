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
    return q.strip(" :")


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
