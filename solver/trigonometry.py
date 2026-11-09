"""Trigonometry: values (degrees by default), identities, equations.

School convention used here: a bare number argument ("sin 30") is in
DEGREES unless the question mentions radians or the argument uses pi.
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

_FUNCS = ("sin", "cos", "tan", "cot", "sec", "csc", "cosec")
_WORD_FUNCS = [
    (r"\bsine\b", "sin"),
    (r"\bcosine\b", "cos"),
    (r"\btangent\b", "tan"),
    (r"\bcotangent\b", "cot"),
    (r"\bsecant\b", "sec"),
    (r"\bcosecant\b", "cosec"),
]


def _normalise(q: str) -> str:
    t = q
    for pat, rep in _WORD_FUNCS:
        t = re.sub(pat, rep, t, flags=re.I)
    t = t.replace("cosec", "csc")
    return t


def _degrees_mode(q: str) -> bool:
    if re.search(r"\brad", q, re.I):
        return False
    if "pi" in q or "π" in q:
        return False
    return True


def _convert_degrees(q: str):
    """Rewrite sin(30)/sin 30 as sin(30*pi/180); returns (text, conversions)."""
    conversions = []

    def repl(m):
        fn, val = m.group(1).lower(), m.group(2)
        conversions.append((fn, val))
        return f"{fn}({val}*pi/180)"

    t = re.sub(
        r"\b(sin|cos|tan|cot|sec|csc)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
        repl, q, flags=re.I,
    )
    t = re.sub(
        r"\b(sin|cos|tan|cot|sec|csc)\s+(-?\d+(?:\.\d+)?)\b",
        repl, t, flags=re.I,
    )
    return t, conversions


def solve_trigonometry(question: str):
    q = _normalise(question.strip())
    qlow = q.lower()
    deg = _degrees_mode(q)

    # --- Identity proof / verification -------------------------------------
    if "=" in q and re.search(r"\b(prove|verify|identity|show)\b", qlow):
        text = re.sub(r"\b(prove|verify|show\s+that)\b", "", q, flags=re.I)
        if deg:
            text, _ = _convert_degrees(text)
        left, right = text.split("=", 1)
        diff_expr = sp.trigsimp(
            parse_expression(left) - parse_expression(right)
        )
        ok = diff_expr == 0
        steps = [
            "Take LHS - RHS and simplify using trig identities "
            "(sin^2 t + cos^2 t = 1, tan t = sin t / cos t, ...).",
            f"LHS - RHS simplifies to {fmt(diff_expr)}",
            "Since LHS - RHS = 0, the identity is "
            + ("TRUE (verified)." if ok else "NOT an identity."),
        ]
        return {
            "type": "trigonometry",
            "op": "identity",
            "answer": "Identity verified ✔" if ok else "Not an identity",
            "verified": bool(ok),
            "steps": steps,
        }

    # --- Trig equation: solve sin(x) = 1/2 --------------------------------
    if "=" in q and re.search(r"(sin|cos|tan)\s*\(", q):
        text = re.sub(r"^\s*solve\b", "", q, flags=re.I).strip()
        left, right = text.split("=", 1)
        var_syms = parse_expression(left).free_symbols
        var = sorted(var_syms, key=lambda s: s.name)[0] if var_syms \
            else sp.symbols("x")
        expr = parse_expression(left) - parse_expression(right)
        sols = sp.solveset(expr, var, domain=sp.Interval(0, 2 * sp.pi))
        deg_sols = sorted(
            float(sp.deg(sp.N(s))) if hasattr(sp, "deg") else
            float(s * 180 / sp.pi)
            for s in sols
        ) if sols else []
        deg_sols = [round(d, 4) for d in deg_sols]
        steps = [
            f"Solve {left.strip()} = {right.strip()} for angles between "
            "0° and 360°.",
            "Use the unit circle: note the sign of the function in each "
            "quadrant to find every solution in the range.",
            "Solutions (degrees): "
            + (", ".join(fmt_num(d) + "°" for d in deg_sols) or "none"),
        ]
        return {
            "type": "trigonometry",
            "op": "equation",
            "answer": ", ".join(f"{fmt_num(d)}°" for d in deg_sols)
            or "No solution in [0°, 360°)",
            "solutions": [f"{fmt_num(d)} degrees" for d in deg_sols],
            "steps": steps,
        }

    # --- Inverse trig: arcsin(0.5), sin^-1(0.5), inverse sin of 0.5 --------
    m = re.search(
        r"(?:arc|a)(sin|cos|tan)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)"
        r"|(sin|cos|tan)\s*\^\s*\(\s*-1\s*\)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)"
        r"|inverse\s+(sin|cos|tan)\s*(?:of\s*)?(-?\d+(?:\.\d+)?)",
        q, re.I,
    )
    if m:
        fn = (m.group(1) or m.group(3) or m.group(5)).lower()
        val = float(m.group(2) or m.group(4) or m.group(6))
        func = {"sin": sp.asin, "cos": sp.acos, "tan": sp.atan}[fn]
        res = func(sp.nsimplify(val, rational=True))
        deg_val = float(res * 180 / sp.pi)
        steps = [
            f"arc{fn}({fmt_num(val)}) asks: which angle has "
            f"{fn} = {fmt_num(val)}?",
            f"Angle = {fmt(res)} radians = {fmt_num(deg_val)}°",
        ]
        return {
            "type": "trigonometry",
            "op": "inverse_value",
            "answer": f"{fmt_num(deg_val)}° ({fmt(res)} rad)",
            "value": deg_val,
            "steps": steps,
        }

    # --- Plain value: sin 30, cos(pi/3), sin 30 + cos 60 ------------------
    text = q
    conversions = []
    if deg:
        text, conversions = _convert_degrees(text)
    expr = parse_expression(text)
    value = sp.simplify(expr)
    steps = []
    for fn, val in conversions:
        steps.append(
            f"{fn} {val}° = {fn}({val}·pi/180) "
            f"[converting degrees to radians]"
        )
    if not expr.free_symbols:
        steps.append(f"Evaluate: {fmt(value)} ≈ {fmt_num(float(value))}")
        return {
            "type": "trigonometry",
            "op": "value",
            "answer": fmt(value),
            "value": float(value),
            "steps": steps,
        }
    simplified = sp.trigsimp(value)
    steps.append(f"Simplify: {fmt(simplified)}")
    return {
        "type": "trigonometry",
        "op": "simplify",
        "answer": fmt(simplified),
        "steps": steps,
    }
