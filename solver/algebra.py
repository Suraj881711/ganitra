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
