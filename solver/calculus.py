"""Calculus: limits, derivatives (incl. partial & implicit), integrals,
and basic differential equations — with step-by-step working.
"""
import re

import sympy as sp
from sympy import S, diff, dsolve, idiff, integrate, limit, symbols

from .expression_parser import fmt, parse_expression

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
    result = diff(expr, var)
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
    """Basic ODEs of the form dy/dx = f(x, y) or y' = f(x, y)."""
    text = q.replace("y'", "dy/dx")
    text = re.sub(r"\b(dsolve|solve|differential\s+equation)\b", "",
                  text, flags=re.I).strip(" :")
    if "=" not in text:
        return None
    left, right = text.split("=", 1)
    if "dy/dx" not in left.replace(" ", "") and "dy/dx" not in text:
        return None
    yfun = sp.Function("y")
    yx = yfun(_x)
    y_sym = symbols("y")
    rhs = parse_expression(right)
    rhs = rhs.subs(y_sym, yx) if y_sym in rhs.free_symbols else rhs
    if _x not in rhs.free_symbols and yx not in rhs.free_symbols:
        rhs = rhs  # constant RHS is fine
    eq = sp.Eq(sp.Derivative(yx, _x), rhs)
    sol = dsolve(eq, yx)
    steps = [
        f"Differential equation: dy/dx = {fmt(rhs)}",
        "Solve with SymPy's dsolve (separation of variables / "
        "integrating factor as applicable).",
        f"General solution: {fmt(sol.rhs)} (C1 is an arbitrary constant)",
    ]
    return {
        "type": "calculus",
        "op": "differential_equation",
        "answer": f"y = {fmt(sol.rhs)}",
        "steps": steps,
    }


def solve_calculus(question: str):
    q = question.strip()

    # Differential equations first (dy/dx = ... or y' = ...)
    if re.search(r"(dy/dx|y'|dsolve|differential)", q, re.I) and "=" in q \
            and not re.search(r"\bfor\b", q, re.I):
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
        return {
            "type": "calculus",
            "op": "derivative",
            "answer": fmt(diff(expr, var)),
            "steps": _derivative_steps(expr, var),
            "latex": sp.latex(diff(expr, var)),
        }

    # "derivative of ..." / "differentiate ..."
    if re.search(r"derivative|differentiate", q, re.I):
        text = re.sub(
            r"\b(derivative\s+of|differentiate)\b", "", q, flags=re.I
        )
        m2 = re.search(r"(.+?)\s+with\s+respect\s+to\s+([a-zA-Z])", text, re.I)
        if m2:
            expr = parse_expression(m2.group(1))
            var = symbols(m2.group(2))
        else:
            expr = parse_expression(text)
            var = _guess_symbol(expr)
        return {
            "type": "calculus",
            "op": "derivative",
            "answer": fmt(diff(expr, var)),
            "steps": _derivative_steps(expr, var),
            "latex": sp.latex(diff(expr, var)),
        }

    # Integral: "integrate x^2", "integrate x from 0 to 1", "integral of x"
    m = re.search(
        r"\bintegrat\w*\b\s*(?:of\s*)?(.+?)\s*"
        r"(?:from\s+(.+?)\s+to\s+(.+))?$",
        q, re.I,
    )
    if m:
        expr_text = m.group(1)
        expr_text = re.sub(r"\s*d[a-zA-Z]\s*$", "", expr_text).strip()
        expr = parse_expression(expr_text)
        var = _guess_symbol(expr)
        if m.group(2) and m.group(3):
            a, b = parse_expression(m.group(2)), parse_expression(m.group(3))
            val = integrate(expr, (var, a, b))
            return {
                "type": "calculus",
                "op": "definite_integral",
                "answer": fmt(val),
                "value": fmt(val),
                "steps": _integral_steps(expr, var, (a, b)),
                "latex": sp.latex(val),
            }
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
