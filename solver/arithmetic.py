"""Arithmetic: expressions, fractions and percentages, with real steps."""
import math
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


# ---------------------------------------------------------------- Wave 56
# METHOD-FIRST schemas (Suraj's direction: one general method
# per question FAMILY, any numbers — never per-question hacks).
# The plain expression parser cannot read command sentences
# ("Add 2/3 and 3/4", "Find the cube root of 729", "Express
# 0.636363... as a fraction") — it treated the words as letter
# variables and answered letter-soup. Each schema below parses
# the family's variable slots and solves for ANY values.

_FRAC56 = (r"(?:\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+"
           r"|\d+(?:\.\d+)?)")


def _frac56_val(s):
    """'1 1/2' / '3/4' / '5' -> sp.Rational."""
    s = s.strip()
    m = re.fullmatch(r"(\d+)\s+(\d+)\s*/\s*(\d+)", s)
    if m:
        return sp.Rational(int(m.group(1)) * int(m.group(3))
                           + int(m.group(2)), int(m.group(3)))
    m = re.fullmatch(r"(\d+)\s*/\s*(\d+)", s)
    if m:
        return sp.Rational(int(m.group(1)), int(m.group(2)))
    return sp.Rational(s)


def _frac56_str(r):
    r = sp.Rational(r)
    return str(r.p) if r.q == 1 else f"{r.p}/{r.q}"


def _wave56_fraction_command(q):
    """Add / Subtract-from / Multiply / Divide two fractions
    (or mixed numbers / whole numbers), any values."""
    ql = q.strip().lower().rstrip(".?")
    m = re.fullmatch(
        rf"add\s+({_FRAC56})\s+and\s+({_FRAC56})", ql)
    if m:
        a, b = _frac56_val(m.group(1)), _frac56_val(m.group(2))
        val = a + b
        steps = [
            f"Add {_frac56_str(a)} and {_frac56_str(b)}: make "
            f"the denominators equal (LCM of {a.q} and {b.q}).",
            f"{_frac56_str(a)} + {_frac56_str(b)} = "
            f"{_frac56_str(val)}",
        ]
        return {"type": "arithmetic", "op": "fraction_add",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    m = re.fullmatch(
        rf"subtract\s+({_FRAC56})\s+from\s+({_FRAC56})", ql)
    if m:
        a, b = _frac56_val(m.group(1)), _frac56_val(m.group(2))
        val = b - a
        steps = [
            f"Subtract {_frac56_str(a)} from {_frac56_str(b)}: "
            f"make the denominators equal (LCM of {a.q} and "
            f"{b.q}).",
            f"{_frac56_str(b)} - {_frac56_str(a)} = "
            f"{_frac56_str(val)}",
        ]
        return {"type": "arithmetic", "op": "fraction_subtract",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    m = re.fullmatch(
        rf"multiply\s+({_FRAC56})\s+(?:and|by)\s+({_FRAC56})", ql)
    if m:
        a, b = _frac56_val(m.group(1)), _frac56_val(m.group(2))
        val = a * b
        steps = [
            "Multiply the numerators and the denominators, "
            "then simplify.",
            f"{_frac56_str(a)} × {_frac56_str(b)} = "
            f"{_frac56_str(val)}",
        ]
        return {"type": "arithmetic", "op": "fraction_multiply",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    m = re.fullmatch(
        rf"divide\s+({_FRAC56})\s+by\s+({_FRAC56})", ql)
    if m:
        a, b = _frac56_val(m.group(1)), _frac56_val(m.group(2))
        if b == 0:
            return None
        val = a / b
        steps = [
            "Dividing by a fraction = multiply by its "
            "reciprocal.",
            f"{_frac56_str(a)} ÷ {_frac56_str(b)} = "
            f"{_frac56_str(a)} × {_frac56_str(1 / b)} = "
            f"{_frac56_str(val)}",
        ]
        return {"type": "arithmetic", "op": "fraction_divide",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    return None


def _wave56_power_root(q):
    """'square / cube of N' and 'square / cube root of N' as
    whole-question commands, any N (integer, decimal or
    fraction)."""
    ql = q.strip().lower().rstrip(".?")
    m = re.fullmatch(
        r"(?:find\s+the\s+|find\s+|what\s+is\s+the\s+|"
        r"what\s+is\s+|calculate\s+the\s+|calculate\s+|"
        r"evaluate\s+the\s+|evaluate\s+)?"
        r"(square\s+root|cube\s+root|square|cube)\s+of\s+"
        rf"({_FRAC56})", ql)
    if not m:
        return None
    kind = m.group(1)
    n = _frac56_val(m.group(2))
    from .expression_parser import fmt as _fmt56
    if kind == "square":
        val = n * n
        steps = [f"Square of {_frac56_str(n)} = "
                 f"{_frac56_str(n)} × {_frac56_str(n)} = "
                 f"{_frac56_str(val)}"]
        return {"type": "arithmetic", "op": "square_of",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    if kind == "cube":
        val = n * n * n
        steps = [f"Cube of {_frac56_str(n)} = "
                 f"{_frac56_str(n)} × {_frac56_str(n)} × "
                 f"{_frac56_str(n)} = {_frac56_str(val)}"]
        return {"type": "arithmetic", "op": "cube_of",
                "answer": _frac56_str(val), "value": float(val),
                "steps": steps}
    if kind == "square root":
        val = sp.sqrt(n)
        steps = [
            f"Find a number which multiplied by itself gives "
            f"{_frac56_str(n)}.",
            f"sqrt({_frac56_str(n)}) = {_fmt56(val)}",
        ]
        return {"type": "arithmetic", "op": "square_root_of",
                "answer": _fmt56(val), "value": float(val),
                "steps": steps}
    val = sp.nsimplify(n ** sp.Rational(1, 3), rational=True)
    if not (val.is_rational or val.is_Integer):
        val = n ** sp.Rational(1, 3)
    steps = [
        f"Find a number whose cube is {_frac56_str(n)}.",
        f"Cube root of {_frac56_str(n)} = {_fmt56(val)}",
    ]
    return {"type": "arithmetic", "op": "cube_root_of",
            "answer": _fmt56(val), "value": float(val),
            "steps": steps}


def _wave56_recurring_decimal(q):
    """'Express 0.636363... as a fraction' — a pure or mixed
    recurring decimal -> exact fraction. The repeating block
    is detected from the shown digits (shortest period that
    regenerates them); anything that does not visibly repeat
    is left alone."""
    m = re.search(r"(\d*)\.(\d{2,}?)\s*(?:\.\.\.|…|\. ?\. ?\.)",
                  q)
    if not m:
        return None
    whole = int(m.group(1)) if m.group(1) else 0
    s = m.group(2)
    best = None
    for i in range(0, len(s)):
        tail = s[i:]
        for p in range(1, len(tail) // 2 + 1):
            block = tail[:p]
            regen = (block * (len(tail) // p + 1))[:len(tail)]
            if regen == tail:
                if best is None or (i + p) < best[0] + best[1]:
                    best = (i, p)
                break
    if best is None:
        return None
    i, p = best
    block = s[i:i + p]
    nonrep = sp.Rational(int(s[:i]) if i else 0, 10 ** i)
    rep = sp.Rational(int(block),
                      (10 ** i) * (10 ** p - 1)) if p else \
        sp.Rational(0)
    val = whole + nonrep + rep
    shown = (f"{whole}." + s + "...") if whole else \
        ("0." + s + "...")
    steps = [
        f"Let x = {shown}. The block '{block}' repeats "
        f"forever.",
        f"Multiply by {10 ** p} and subtract to remove the "
        f"repeating part: x = {_frac56_str(val)}",
    ]
    return {"type": "arithmetic", "op": "recurring_decimal",
            "answer": _frac56_str(val), "value": float(val),
            "steps": steps}


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
_UNIT56 = {"hour": 3600.0, "hours": 3600.0, "minute": 60.0,
           "minutes": 60.0, "second": 1.0, "seconds": 1.0,
           "kg": 1000.0, "g": 1.0, "gram": 1.0, "grams": 1.0,
           "km": 1000.0, "m": 1.0, "cm": 0.01, "litre": 1000.0,
           "litres": 1000.0, "liter": 1000.0, "ml": 1.0,
           "rupee": 100.0, "rupees": 100.0, "paise": 1.0}


def _percent(question):
    q = question
    # Wave 56: percent across UNITS — "What percent of 2
    # hours is 36 minutes?" Both quantities are converted
    # to a common base unit before dividing.
    m = re.search(
        r"what\s+(?:percent|%)\s*of\s*(\d+(?:\.\d+)?)\s*"
        r"([a-z]+)\s+is\s+(\d+(?:\.\d+)?)\s*([a-z]+)", q, re.I)
    if m and m.group(2).lower() in _UNIT56 \
            and m.group(4).lower() in _UNIT56:
        whole = float(m.group(1)) * _UNIT56[m.group(2).lower()]
        part = float(m.group(3)) * _UNIT56[m.group(4).lower()]
        if whole > 0:
            val = part / whole * 100.0
            steps = [
                f"Convert to the same unit: {m.group(1)} "
                f"{m.group(2)} = {fmt_num(whole)} and "
                f"{m.group(3)} {m.group(4)} = {fmt_num(part)}",
                f"Percentage = ({fmt_num(part)} ÷ "
                f"{fmt_num(whole)}) × 100 = {fmt_num(val)}%",
            ]
            return val, steps
    # Wave 56: "Out of 45 students, 27 are girls. What
    # percent ...?" — part and whole stated in prose order.
    m = re.search(r"out\s+of\s+(\d+(?:\.\d+)?)\b[^.]{0,40}?"
                  r",\s*(\d+(?:\.\d+)?)\s+are\b", q, re.I)
    if m and "percent" in q.lower():
        whole, part = float(m.group(1)), float(m.group(2))
        if whole > 0:
            val = part / whole * 100.0
            steps = [
                f"Percentage = (part ÷ whole) × 100 = "
                f"({fmt_num(part)} ÷ {fmt_num(whole)}) × 100",
                f"= {fmt_num(val)}%",
            ]
            return val, steps
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


_FRAC_OPERAND = r"\d+(?:\s*/\s*\d+)?"


def _fraction_steps(a, b, sign):
    """Textbook LCM working for a + b or a - b (Rationals)."""
    den = a.q * b.q // math.gcd(a.q, b.q)
    na, nb = a.p * (den // a.q), b.p * (den // b.q)
    tot = na + nb if sign > 0 else na - nb
    res = sp.Rational(tot, den)
    steps = [
        f"Denominators are {a.q} and {b.q}; their LCM is {den}.",
        f"Convert: {fmt_num(a)} = {na}/{den} and "
        f"{fmt_num(b)} = {nb}/{den}.",
        f"{'Add' if sign > 0 else 'Subtract'} the numerators: "
        f"{na} {'+' if sign > 0 else '-'} {nb} = {tot}, "
        f"so the result is {tot}/{den}.",
    ]
    if res.q != den or res.p != tot:
        steps.append(f"Simplify: {tot}/{den} = {fmt_num(res)}.")
    return res, steps


def _fraction_ask(question):
    """Wave 52 (audit #15): 'Add 2/3 and 3/4' / 'Subtract 1/4
    from 5/6' as a PRIMARY pattern. These used to reach only
    the salvage layer, which solved one operand and echoed
    it ('Add 2/3 and 3/4' -> '2/3'); 31 of 52 salvage
    answers in the Wave 35 audit carried a wrong value."""
    q = str(question or "")
    m = re.search(rf"\badd\s+(?:the\s+)?(?:fractions?\s+)?"
                  rf"({_FRAC_OPERAND})\s+and\s+"
                  rf"({_FRAC_OPERAND})", q, re.I) or re.search(
                      rf"\bsum\s+of\s+({_FRAC_OPERAND})\s+and\s+"
                      rf"({_FRAC_OPERAND})", q, re.I)
    if m:
        a = sp.Rational(m.group(1).replace(" ", ""))
        b = sp.Rational(m.group(2).replace(" ", ""))
        res, steps = _fraction_steps(a, b, +1)
        return {"type": "arithmetic", "op": "fraction_add",
                "expression": f"{fmt_num(a)} + {fmt_num(b)}",
                "answer": fmt_num(res), "numeric": float(res),
                "fraction": (f"{res.p}/{res.q}" if res.q != 1
                             else str(res.p)),
                "steps": steps}
    m = re.search(rf"\bsubtract\s+(?:the\s+)?(?:fractions?\s+)?"
                  rf"({_FRAC_OPERAND})\s+from\s+"
                  rf"({_FRAC_OPERAND})", q, re.I)
    if m:
        sub = sp.Rational(m.group(1).replace(" ", ""))
        base = sp.Rational(m.group(2).replace(" ", ""))
        res, steps = _fraction_steps(base, sub, -1)
        return {"type": "arithmetic", "op": "fraction_subtract",
                "expression": f"{fmt_num(base)} - {fmt_num(sub)}",
                "answer": fmt_num(res), "numeric": float(res),
                "fraction": (f"{res.p}/{res.q}" if res.q != 1
                             else str(res.p)),
                "steps": steps}
    return None


def _power_word(question):
    """Wave 52 (audit #15): 'Find the square of 15' / 'cube
    of 8' as a primary pattern — the salvage layer turned
    'square' into a letter-product (s-q-u-a-r-e multiplied
    out) and served it as the answer. The digit must follow
    'of' directly, so 'area of a square of side 15' (where
    'side' intervenes) can never fire this."""
    m = re.search(r"\b(square|cube)\s+of\s+(\d+(?:\.\d+)?)\b",
                  str(question or ""), re.I)
    if not m:
        return None
    n = sp.Rational(m.group(2))
    power = 2 if m.group(1).lower() == "square" else 3
    val = n ** power
    steps = [
        f"{'Square' if power == 2 else 'Cube'} of "
        f"{fmt_num(n)} = {fmt_num(n)}"
        + (f" × {fmt_num(n)}" if power == 2
           else f" × {fmt_num(n)} × {fmt_num(n)}")
        + f" = {fmt_num(val)}.",
    ]
    return {"type": "arithmetic",
            "op": "square_of" if power == 2 else "cube_of",
            "expression": f"{fmt_num(n)}^{power}",
            "answer": fmt_num(val), "numeric": float(val),
            "steps": steps}


_FRAC_LIT = r"(\d+)\s*/\s*(\d+)"


def _fraction_word_problem(question):
    """Wave 58: worded fraction addition / subtraction —
    "Add 2/3 and 3/4", "Subtract 1/4 from 5/6", "Find the
    sum of ...", "difference between ...". None of these had
    a pattern: the generic parser choked on the words and the
    fallback salvage echoed the FIRST OPERAND as the answer
    (audit #7-#14). Solved here with exact Fractions and LCM
    steps; anything that is not exactly this shape returns
    None.
    """
    from fractions import Fraction
    import math as _math
    q = question.lower()

    def _mk(op, a, b, result, order_note=None):
        L = _math.lcm(a.denominator, b.denominator)
        steps = []
        if order_note:
            steps.append(order_note)
        steps.append(
            f"Take the LCM of the denominators "
            f"{a.denominator} and {b.denominator}: LCM = {L}")
        steps.append(
            f"{a} = {a.numerator * (L // a.denominator)}/{L} "
            f"and {b} = {b.numerator * (L // b.denominator)}/{L}")
        sym = "+" if op == "fraction_add" else "−"
        steps.append(
            f"{a.numerator * (L // a.denominator)}/{L} {sym} "
            f"{b.numerator * (L // b.denominator)}/{L} "
            f"= {result}")
        out = {"type": "arithmetic", "op": op,
               "answer": fmt_num(result),
               "numeric": float(result), "steps": steps}
        if result.denominator != 1:
            out["fraction"] = f"{result.numerator}/" \
                              f"{result.denominator}"
        return out

    def _fr(m, i):
        return Fraction(int(m.group(i)), int(m.group(i + 1)))

    m = re.search(r"add\s+(?:the\s+fractions\s+)?" + _FRAC_LIT
                  + r"\s+(?:and|to)\s+" + _FRAC_LIT, q) or \
        re.search(r"(?:find\s+)?(?:the\s+)?sum\s+of\s+"
                  + _FRAC_LIT + r"\s+and\s+" + _FRAC_LIT, q)
    if m:
        a, b = _fr(m, 1), _fr(m, 3)
        return _mk("fraction_add", a, b, a + b)
    m = re.search(r"subtract\s+" + _FRAC_LIT + r"\s+from\s+"
                  + _FRAC_LIT, q)
    if m:
        sub, whole = _fr(m, 1), _fr(m, 3)
        return _mk("fraction_subtract", whole, sub, whole - sub,
                   order_note=f"Subtract {sub} from {whole}: "
                              f"that is {whole} − {sub}.")
    m = re.search(r"(?:find\s+)?(?:the\s+)?difference\s+"
                  r"between\s+" + _FRAC_LIT + r"\s+and\s+"
                  + _FRAC_LIT, q)
    if m:
        a, b = _fr(m, 1), _fr(m, 3)
        big, small = max(a, b), min(a, b)
        return _mk("fraction_subtract", big, small, big - small)
    return None


_HINGLISH_FILLER = re.compile(
    r"\b(kitna\s+hota\s+hai|kitna\s+hai|kitna\s+hoga|"
    r"kitne\s+ka\s+hai|batao|bata\s+do|nikalo|nikaal\s+do|"
    r"solve\s+karo|solve\s+kar\s+do)\b", re.I)


def _strip_hinglish_filler(question):
    """Wave 58: a pure arithmetic expression wearing Hinglish
    filler — "2/3 + 3/4 kitna hota hai?" The filler words
    became junk variables for the parser, so the question
    fell to the fallback even though the expression itself
    is trivially solvable. Returns the cleaned question ONLY
    when a filler phrase was present AND the remainder is a
    symbol-free arithmetic expression; otherwise None.
    """
    if not _HINGLISH_FILLER.search(question):
        return None
    cleaned = _HINGLISH_FILLER.sub("", question)
    cleaned = cleaned.strip().rstrip("?.!").strip()
    if not cleaned or not any(c.isdigit() for c in cleaned):
        return None
    try:
        expr = parse_expression(_word_ops(cleaned))
    except Exception:
        return None
    if not hasattr(expr, "free_symbols") or expr.free_symbols:
        return None
    return cleaned


def _square_cube_word(question):
    """Wave 58: "Find the square of 15", "What is 9 cubed?",
    "25 ka cube kitna hota hai?" — none had a pattern, so
    they fell to the guide / salvage soup (audit #33-#35,
    #502; Wave 55's "squared" trap). The digit must follow
    "of" directly, which is exactly what keeps "square ROOT
    of 144" and "area of a square of side 15" out of this
    branch.
    """
    from fractions import Fraction
    q = question.lower()
    N = r"(-?\d+(?:\.\d+)?)"
    power, m = None, None
    for pat, p in (
            (r"square\s+of\s+" + N, 2),
            (r"cube\s+of\s+" + N, 3),
            (N + r"\s+squared\b", 2),
            (N + r"\s+cubed\b", 3),
            (N + r"\s+ka\s+square\b(?!\s*root)", 2),
            (N + r"\s+ka\s+cube\b(?!\s*root)", 3)):
        m = re.search(pat, q)
        if m:
            power = p
            break
    if m is None:
        return None
    try:
        n = Fraction(m.group(1))
    except Exception:
        return None
    v = n ** power
    word = "Square" if power == 2 else "Cube"
    factors = " × ".join(fmt_num(n) for _ in range(power))
    steps = [f"{word} of {fmt_num(n)} = {factors} "
             f"= {fmt_num(v)}"]
    out = {"type": "arithmetic",
           "op": "square_of" if power == 2 else "cube_of",
           "answer": fmt_num(v), "numeric": float(v),
           "steps": steps}
    if v.denominator != 1:
        out["fraction"] = f"{v.numerator}/{v.denominator}"
    return out


def solve_arithmetic(question):
    # Wave 56 command schemas first: they are whole-question
    # anchored, so they can never shadow a plain expression.
    # (Merge-3: ahead of Wave 52's fraction/power patterns —
    # the two layers cover the same families; Wave 56's
    # operand grammar is the more general one, Wave 52's
    # patterns remain as the next layer for its phrasings.)
    for _fn56 in (_wave56_fraction_command, _wave56_power_root,
                  _wave56_recurring_decimal):
        _r56 = _fn56(question)
        if _r56 is not None:
            return _r56
    frac = _fraction_ask(question)
    if frac is not None:
        return frac
    power = _power_word(question)
    if power is not None:
        return power
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

    # Wave 58: worded fraction add / subtract (see
    # _fraction_word_problem) and Hinglish-filler expressions.
    _fw = _fraction_word_problem(question)
    if _fw is not None:
        return _fw
    _sc = _square_cube_word(question)
    if _sc is not None:
        return _sc
    _cleaned = _strip_hinglish_filler(question)
    if _cleaned is not None:
        question = _cleaned

    text = _word_ops(question)
    # Wave 56: school questions write multiplication as a
    # spaced "x" between two numbers ("Evaluate 8.75 x 2.5");
    # the parser read that x as a variable. Only the
    # digit-x-digit form is rewritten — algebraic "3x" and
    # "x + 2" are untouched.
    text = re.sub(r"(?<=\d)\s+x\s+(?=\d)", " * ", text)
    try:
        expr = parse_expression(text)
    except Exception:
        # Wave 56: a conversational command lead-in ("can
        # you solve 17 * 24", "please calculate ...") is
        # not in the parser's filler list, so the whole
        # sentence failed to parse. Strip the lead-in and
        # retry ONCE; if that also fails, the original
        # error propagates exactly as before.
        _bare = re.sub(
            r"^\s*(?:can\s+you\s+)?(?:please\s+)?"
            r"(?:solve|calculate|evaluate|compute|find)\s+",
            "", text, flags=re.I)
        if _bare == text:
            raise
        expr = parse_expression(_bare)
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
