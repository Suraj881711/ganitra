"""Arithmetic: expressions, fractions and percentages, with real steps."""
import re

import sympy as sp

from .expression_parser import fmt_num, parse_expression

_WORD_OPS = [
    (r"\bdivided\s+by\b", "/"),
    (r"\bmultiplied\s+by\b", "*"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\btimes\b", "*"),
    (r"\bover\b", "/"),
]


def _word_ops(text: str) -> str:
    t = text
    for pat, rep in _WORD_OPS:
        t = re.sub(pat, f" {rep} ", t, flags=re.I)
    return t


# ---------------------------------------------------------------- step trace
def _tokenize(s):
    tokens, i = [], 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
        elif c in "+-*/()":
            if c == "*" and s[i : i + 2] == "**":
                tokens.append(("op", "**"))
                i += 2
            else:
                tokens.append(("op", c) if c != "(" and c != ")" else (c, c))
                i += 1
        elif c.isdigit() or c == ".":
            m = re.match(r"\d+(?:\.\d+)?|\.\d+", s[i:])
            tokens.append(("num", sp.nsimplify(m.group(0), rational=True)))
            i += len(m.group(0))
        else:
            raise ValueError(f"Unexpected character {c!r}")
    return tokens


def _show(tokens) -> str:
    parts = []
    for kind, val in tokens:
        if kind == "num":
            parts.append(fmt_num(val))
        elif kind == "op":
            parts.append({"**": "^", "*": "×", "/": "÷"}.get(val, val))
        else:
            parts.append(val)
    return " ".join(parts).replace("( ", "(").replace(" )", ")")


def _apply(a, op, b):
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return sp.Rational(a, b) if _is_rat(a) and _is_rat(b) else a / b
    if op == "**":
        return (a**b).evalf() if not _is_rat(b) or b.q != 1 else a**b
    raise ValueError(op)


def _is_rat(v):
    return isinstance(v, sp.Rational)


def _reduce_segment(seg, steps):
    """Reduce a paren-free token segment to one number, recording steps."""
    # Fold unary minus into the following number.
    out = []
    for tok in seg:
        if tok == ("op", "-") and (not out or out[-1][0] == "op"):
            out.append(("num", sp.Integer(0)))
        out.append(tok)
    seg = out
    for ops in (("**",), ("*", "/"), ("+", "-")):
        i = 0
        while i < len(seg):
            kind, val = seg[i]
            if kind == "op" and val in ops and 0 < i < len(seg) - 1:
                a, b = seg[i - 1][1], seg[i + 1][1]
                r = _apply(a, val, b)
                sym = {"**": "^", "*": "×", "/": "÷"}.get(val, val)
                steps.append(
                    f"{fmt_num(a)} {sym} {fmt_num(b)} = {fmt_num(r)}"
                )
                seg = seg[: i - 1] + [("num", r)] + seg[i + 2 :]
                i = max(i - 1, 0)
            else:
                i += 1
    if len(seg) != 1 or seg[0][0] != "num":
        raise ValueError("Could not reduce expression")
    return seg[0][1]


def reduction_steps(expr_text):
    """Genuine BODMAS reduction steps for a numeric expression string."""
    steps = []
    tokens = _tokenize(expr_text)
    if len(tokens) <= 1:
        return steps
    steps.append(f"Write the expression: {_show(tokens)}")
    guard = 0
    while len(tokens) > 1 and guard < 40:
        guard += 1
        # Find innermost parenthesised group.
        start = end = None
        for i, (kind, _) in enumerate(tokens):
            if kind == "(":
                start = i
            if kind == ")" and start is not None:
                end = i
                break
        before = list(steps)
        if start is not None and end is not None:
            val = _reduce_segment(tokens[start + 1 : end], steps)
            tokens = tokens[:start] + [("num", val)] + tokens[end + 1 :]
        else:
            val = _reduce_segment(tokens, steps)
            tokens = [("num", val)]
        if len(tokens) > 1:
            steps.append(f"Now the expression is: {_show(tokens)}")
        elif steps == before:
            break
    return steps


# ---------------------------------------------------------------- percentages
def _percent(question):
    q = question
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:%|percent|per\s?cent)\s*of\s*(\d+(?:\.\d+)?)",
        q,
        re.I,
    )
    if m:
        pct, base = float(m.group(1)), float(m.group(2))
        val = pct / 100.0 * base
        steps = [
            f"{fmt_num(pct)}% means {fmt_num(pct)}/100 = {fmt_num(pct / 100.0)}",
            f"Multiply by {fmt_num(base)}: {fmt_num(pct / 100.0)} × "
            f"{fmt_num(base)} = {fmt_num(val)}",
        ]
        return val, steps
    m = re.search(
        r"what\s+(?:percent|%)\s*of\s*(\d+(?:\.\d+)?)\s*is\s*(\d+(?:\.\d+)?)",
        q,
        re.I,
    ) or re.search(
        r"(\d+(?:\.\d+)?)\s*is\s*what\s+(?:percent|%)\s*of\s*(\d+(?:\.\d+)?)",
        q,
        re.I,
    )
    if m:
        if "is what" in q.lower():
            part, whole = float(m.group(1)), float(m.group(2))
        else:
            whole, part = float(m.group(1)), float(m.group(2))
        val = part / whole * 100.0
        steps = [
            f"Percentage = (part ÷ whole) × 100 = ({fmt_num(part)} ÷ "
            f"{fmt_num(whole)}) × 100",
            f"= {fmt_num(val)}%",
        ]
        return val, steps
    return None


def solve_arithmetic(question):
    pct = _percent(question)
    if pct is not None:
        val, steps = pct
        return {
            "type": "arithmetic",
            "op": "percentage",
            "expression": question.strip(),
            "answer": fmt_num(val),
            "numeric": float(val),
            "steps": steps,
        }

    text = _word_ops(question)
    expr = parse_expression(text)
    # Wave 30 defence-in-depth: parse_expression now rejects tuples
    # itself, but never call .free_symbols on a non-expression.
    if not hasattr(expr, "free_symbols"):
        raise ValueError(f"Could not parse expression: {question!r}")
    if expr.free_symbols:
        # A symbolic expression reached arithmetic: simplify it instead.
        simplified = sp.simplify(expr)
        return {
            "type": "arithmetic",
            "op": "simplify",
            "expression": str(expr),
            "answer": str(simplified),
            "steps": [
                f"Write the expression: {expr}",
                f"Simplify: {simplified}",
            ],
        }

    value = sp.nsimplify(expr, rational=True)
    try:
        steps = reduction_steps(str(expr).replace(" ", ""))
        if not steps:
            steps = [f"Evaluate: {expr} = {fmt_num(value)}"]
    except Exception:
        steps = [
            "Follow BODMAS: brackets, orders (powers), division and "
            "multiplication, then addition and subtraction.",
            f"{expr} = {fmt_num(value)}",
        ]
    result = {
        "type": "arithmetic",
        "op": "evaluate",
        "expression": str(expr),
        "answer": fmt_num(value),
        "numeric": float(value),
        "steps": steps,
    }
    if isinstance(value, sp.Rational) and value.q != 1:
        result["fraction"] = f"{value.p}/{value.q}"
        result["decimal"] = float(value)
    return result
