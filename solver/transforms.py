"""Transforms & series: Laplace transform, inverse Laplace transform,
Taylor / Maclaurin series expansions, and partial fractions — SymPy does
the symbolic work; we present it with steps.
"""
import re

import sympy as sp

from .expression_parser import fmt, parse_expression

_t = sp.symbols("t", real=True)
_s = sp.symbols("s")
_x = sp.symbols("x")


def _strip_lead(q: str, words: str) -> str:
    return re.sub(rf"^\s*(?:please\s+)?(?:{words})\s*(?:of|for)?\s*", "",
                  q, flags=re.I).strip()


def _laplace(q: str):
    text = _strip_lead(q, r"laplace\s+transform")
    text = re.sub(r"\s+with\s+respect\s+to.*$", "", text, flags=re.I)
    expr = parse_expression(text)
    var = next(iter(expr.free_symbols), _t)
    # Note: t must be declared real, or laplace_transform returns
    # conditions as a tuple; noconds=True collapses it to the transform.
    res = sp.laplace_transform(expr, var, _s, noconds=True)
    F = res[0] if isinstance(res, tuple) else res
    steps = [
        "Definition: L{f(t)} = ∫₀^∞ e^(−st)·f(t) dt",
        f"Apply the Laplace transform to {fmt(expr)} term by term "
        "(standard table: L{t} = 1/s², L{e^(at)} = 1/(s−a), "
        "L{sin(at)} = a/(s²+a²), L{cos(at)} = s/(s²+a²), "
        "L{1} = 1/s).",
        f"L{{ {fmt(expr)} }} = {fmt(F)}",
    ]
    return {
        "type": "transforms", "op": "laplace_transform",
        "answer": fmt(F), "steps": steps, "latex": sp.latex(F),
    }


def _inverse_laplace(q: str):
    text = _strip_lead(q, r"inverse\s+laplace(?:\s+transform)?")
    expr = parse_expression(text)
    var = next(iter(expr.free_symbols), _s)
    f = sp.inverse_laplace_transform(expr, var, _t)
    f_clean = f.replace(
        lambda e: isinstance(e, sp.Heaviside), lambda e: sp.Integer(1))
    steps = [
        "Match F(s) against the standard Laplace table "
        "(and use partial fractions first if needed).",
        f"L⁻¹{{ {fmt(expr)} }} = {fmt(f_clean)}",
    ]
    return {
        "type": "transforms", "op": "inverse_laplace_transform",
        "answer": fmt(f_clean), "steps": steps,
        "latex": sp.latex(f_clean),
    }


def _series(q: str):
    m = re.search(r"(?:up\s+to|to|of)\s+order\s+(\d+)", q, re.I) or \
        re.search(r"(\d+)\s*(?:terms|th\s+order)", q, re.I)
    order = int(m.group(1)) if m else 5
    # "e^x" must be the natural exponential, not symbol e raised to x.
    work = re.sub(r"\be\s*\^", "E^", q)
    text = re.sub(
        r"\b(taylor|maclaurin)\s+series\b|\bseries\s+expansion\b|"
        r"\bexpand\b|\bseries\b", "", work, flags=re.I)
    text = re.sub(r"(?:up\s+to|to)\s+order\s+\d+", "", text, flags=re.I)
    # "of e^x" -> the function follows the LAST "of" in the text; grabbing
    # the tail after it also drops filler like "Taylor series of ...".
    if "of" in text:
        text = text.rsplit("of", 1)[-1]
    text = re.sub(r"\baround\s+(-?\d+(?:\.\d+)?)", r"__AT__\1", text)
    at = 0
    ma = re.search(r"__AT__(-?\d+(?:\.\d+)?)", text)
    if ma:
        at = float(ma.group(1))
        at = int(at) if at == int(at) else at
        text = text.replace(ma.group(0), "")
    text = text.strip(" :")
    expr = parse_expression(text)
    var = next(iter(expr.free_symbols), _x)
    ser = sp.series(expr, var, at, order + 1)
    poly = ser.removeO()
    kind = "Maclaurin" if at == 0 else "Taylor"
    steps = [
        f"{kind} series of f({var}) = {fmt(expr)} about {var} = {at}: "
        f"f({var}) = Σ f⁽ⁿ⁾({at})/n! · ({var} − {at})ⁿ",
    ]
    # A couple of explicit derivative evaluations for low-order terms.
    for n in range(min(order + 1, 3)):
        d = sp.diff(expr, var, n)
        val = d.subs(var, at) if n else expr.subs(var, at)
        steps.append(f"f⁽{n}⁾({at}) = {fmt(val)}, so term {n} is "
                     f"{fmt(val)}/{n}! · ({var} − {at})^{n}"
                     if n else
                     f"f({at}) = {fmt(val)}")
    steps.append(f"Up to order {order}: {fmt(poly)} + O(({var} − {at})"
                 f"^{order + 1})" if at else
                 f"Up to order {order}: {fmt(poly)} + O({var}^{order + 1})")
    return {
        "type": "transforms", "op": "taylor_series",
        "answer": f"{fmt(poly)} + ...",
        "steps": steps, "latex": sp.latex(poly),
    }


def _partial_fractions(q: str):
    text = _strip_lead(q, r"partial\s+fractions?")
    text = re.sub(r"\bof\b", "", text, flags=re.I).strip(" :")
    expr = parse_expression(text)
    var = next(iter(expr.free_symbols), _x)
    out = sp.apart(expr, var)
    steps = [
        f"Write {fmt(expr)} as a sum of simpler fractions with "
        "one factor of the denominator each.",
        "Equate numerators and solve for the constants "
        "(cover-up / comparing coefficients).",
        f"{fmt(expr)} = {fmt(out)}",
    ]
    return {
        "type": "transforms", "op": "partial_fractions",
        "answer": fmt(out), "steps": steps, "latex": sp.latex(out),
    }


def solve_transforms(question: str):
    q = question.strip()
    ql = q.lower()
    try:
        if "inverse" in ql and "laplace" in ql:
            return _inverse_laplace(q)
        if "laplace" in ql:
            return _laplace(q)
        if "partial fraction" in ql:
            return _partial_fractions(q)
        if "series" in ql or "maclaurin" in ql or "taylor" in ql:
            return _series(q)
    except Exception as e:
        return {"type": "transforms", "op": "error",
                "answer": f"Could not solve this one: {e}", "steps": []}
    return {"type": "transforms", "op": "unknown",
            "answer": "Try 'Laplace transform of t', 'inverse Laplace of "
                      "1/(s^2+1)', 'Taylor series of e^x up to order 4' "
                      "or 'partial fractions of 1/(x^2-1)'.",
            "steps": []}


__all__ = ["solve_transforms"]
