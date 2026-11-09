"""Complex numbers: arithmetic, conjugate, modulus, argument."""
import re

import sympy as sp

from .expression_parser import fmt, parse_expression


def _extract_expr(q: str) -> str:
    """Pull the complex expression out of the question text."""
    t = q.strip()
    t = re.sub(r"\b(complex|number|find|calculate|evaluate|simplify)\b",
               "", t, flags=re.I)
    t = re.sub(r"\b(conjugate|modulus|magnitude|argument|arg|abs)\s+of\b",
               "", t, flags=re.I)
    t = re.sub(r"\b(real|imaginary)\s+part\s+of\b", "", t, flags=re.I)
    return t.strip(" :?")


def _to_sympy(text: str):
    """Convert 'i' notation to SymPy's I and parse."""
    t = re.sub(r"(?<![a-zA-Z])i(?![a-zA-Z])", "I", text)
    t = re.sub(r"(\d)\s*I\b", r"\1*I", t)
    t = re.sub(r"\)\s*I\b", r")*I", t)
    return parse_expression(t)


def solve_complex(question: str):
    q = question.strip()
    ql = q.lower()
    expr = _to_sympy(_extract_expr(q))

    if "conjugate" in ql:
        res = sp.conjugate(expr)
        steps = [f"Conjugate of {fmt(expr)}: change the sign of the "
                 "imaginary part.",
                 f"= {fmt(res)}"]
        return {"type": "complex", "op": "conjugate",
                "answer": fmt(sp.expand(res)), "steps": steps}
    if "modulus" in ql or "magnitude" in ql or "abs" in ql:
        a, b = sp.re(expr), sp.im(expr)
        res = sp.Abs(expr)
        steps = [
            f"Write as a + bi: a = {fmt(a)}, b = {fmt(b)}",
            f"Modulus = sqrt(a^2 + b^2) = sqrt({fmt(a)}^2 + {fmt(b)}^2)"
            f" = {fmt(res)}",
        ]
        return {"type": "complex", "op": "modulus",
                "answer": fmt(res), "value": float(res), "steps": steps}
    if "argument" in ql or re.search(r"\barg\b", ql):
        res = sp.arg(expr)
        steps = [
            f"Argument = atan2(Im, Re) for {fmt(expr)}",
            f"= {fmt(res)} radians ≈ {float(res):.4f} rad "
            f"({float(res) * 180 / 3.141592653589793:.2f}°)",
        ]
        return {"type": "complex", "op": "argument",
                "answer": f"{fmt(res)} rad ≈ {float(res):.4f}",
                "steps": steps}
    if "real part" in ql:
        return {"type": "complex", "op": "real_part",
                "answer": fmt(sp.re(expr)),
                "steps": [f"Real part of {fmt(expr)} is {fmt(sp.re(expr))}"]}
    if "imaginary part" in ql:
        return {"type": "complex", "op": "imaginary_part",
                "answer": fmt(sp.im(expr)),
                "steps": [f"Imaginary part of {fmt(expr)} is "
                          f"{fmt(sp.im(expr))}"]}

    res = sp.expand(expr)
    steps = [
        f"Work with i as the imaginary unit, i^2 = -1: {fmt(expr)}",
        "Expand and collect the real and imaginary parts.",
        f"= {fmt(res)}",
    ]
    return {"type": "complex", "op": "evaluate",
            "answer": fmt(res), "steps": steps}
