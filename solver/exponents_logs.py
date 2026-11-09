"""Exponents & logarithms: evaluate logs, solve exponential/log equations."""
import re

import sympy as sp

from .expression_parser import fmt, parse_expression

x = sp.symbols("x")


def solve_exponents_logs(question: str):
    q = question.strip()
    qlow = q.lower()

    # log with explicit base: "log base 2 of 32", "log2(32)", "log_2(32)"
    m = re.search(
        r"log\s*(?:base\s*)?(\d+(?:\.\d+)?)\s*(?:of\s*|\(\s*|\s+)"
        r"(\d+(?:\.\d+)?)\s*\)?",
        qlow,
    ) or re.search(r"log_(\d+(?:\.\d+)?)\s*\(\s*(\d+(?:\.\d+)?)\s*\)", qlow)
    if m:
        base, val = float(m.group(1)), float(m.group(2))
        res = sp.log(val, base)
        steps = [
            f"log base {fmt(base)} of {fmt(val)} asks: {fmt(base)} raised "
            f"to what power gives {fmt(val)}?",
        ]
        exact = sp.nsimplify(res, rational=True)
        if exact.is_Integer or exact.is_Rational:
            steps.append(
                f"{fmt(base)}^{fmt(exact)} = {fmt(val)}, so the answer is "
                f"{fmt(exact)}"
            )
        else:
            steps.append(
                f"= ln({fmt(val)}) / ln({fmt(base)}) ≈ {fmt(float(res))}"
            )
        return {
            "type": "exponents_logs",
            "op": "log_value",
            "answer": fmt(sp.nsimplify(res, rational=True))
            if (sp.nsimplify(res, rational=True)).is_rational
            else fmt(float(res)),
            "value": float(res),
            "steps": steps,
        }

    # Log / exponential equation: anything containing log/ln and '='
    if "=" in q and ("log" in qlow or "ln" in qlow or "^" in q or "**" in q):
        text = re.sub(r"^\s*solve\b", "", q, flags=re.I).strip()
        left, right = text.split("=", 1)
        expr = parse_expression(left) - parse_expression(right)
        var = sorted(expr.free_symbols, key=lambda s: s.name)
        var = var[0] if var else x
        sols = sp.solve(expr, var)
        steps = [
            f"Write as one equation: {fmt(expr)} = 0",
            "Use log/exp rules (log a + log b = log(ab); a^x = a^y means "
            "x = y) and solve.",
        ]
        sol_strs = [fmt(s) for s in sols]
        answer = ", ".join(f"{var} = {s}" for s in sol_strs) or "No solution"
        steps.append(f"Solution: {answer}")
        return {
            "type": "exponents_logs",
            "op": "equation",
            "answer": answer,
            "solutions": sol_strs,
            "steps": steps,
        }

    # Plain exponential/log expression to evaluate/simplify.
    expr = parse_expression(q)
    val = sp.simplify(expr)
    steps = [f"Evaluate {fmt(expr)} using exponent/log rules."]
    out = {
        "type": "exponents_logs",
        "op": "evaluate",
        "answer": fmt(val),
        "steps": steps + [f"= {fmt(val)}"],
    }
    if not val.free_symbols:
        out["value"] = float(val)
    return out
