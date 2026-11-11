"""Applied maths (Wave 13) — Classes 6-12 gap families.

Ratio & proportion, simple interest in its common "Rs" forms,
profit & loss, speed/distance/time stories, unit-rate
(unitary) cost questions, simple linear word equations, and
the discriminant / nature of roots for quadratics.

Like solver/junior.py this is CONSERVATIVE pattern matching:
solve_applied returns None when no pattern extracts clean
numbers, and the router falls back (word_problems, then the
normal pipeline). Result types reuse existing families where
they belong (simple interest is a "word_problem", word
equations are "algebra" equations) so explanations, advice,
Teach me and the Wave-12/13 methods all keep working.
"""
import math
import re
from fractions import Fraction

import sympy as sp

from .algebra import _poly_coeffs
from .expression_parser import fmt, fmt_num, parse_expression

_NUM = r"\d+(?:\.\d+)?"
_RS = r"(?:rs\.?|₹|rupees)"


def _num(s):
    return float(s) if "." in s else int(s)


def _ratio_parts(s):
    """'20'/'45' (or decimals) -> exact Fractions."""
    return Fraction(s) if "." not in s else Fraction(s).limit_denominator(1000)


# --------------------------------------------------------------------------
# Ratio & proportion
# --------------------------------------------------------------------------
def _ratio(q):
    # Divide an amount in a ratio: "divide Rs 600 in the ratio 2:3"
    m = re.search(
        r"\bdivide\s+(?:" + _RS + r"\s*)?(" + _NUM + r")\s+in\s+"
        r"(?:the\s+)?ratio\s+(\d+)\s*:\s*(\d+)(?:\s*:\s*(\d+))?", q)
    if m:
        total = _num(m.group(1))
        parts = [int(m.group(2)), int(m.group(3))]
        if m.group(4):
            parts.append(int(m.group(4)))
        s = sum(parts)
        money = bool(re.search(_RS, q))
        vals = [total * p / s for p in parts]
        steps = [
            f"Ratio parts: {' + '.join(str(p) for p in parts)} "
            f"= {s} parts in total.",
            f"Value of 1 part = {fmt_num(total)} ÷ {s} = "
            f"{fmt_num(total / s)}",
        ]
        named = []
        for p, v in zip(parts, vals):
            steps.append(f"{p} parts = {p} × {fmt_num(total / s)} "
                         f"= {fmt_num(v)}")
            named.append(("Rs " if money else "") + fmt_num(v))
        return {"type": "applied", "op": "ratio_divide",
                "answer": " and ".join(named), "steps": steps,
                "value": vals}
    # Two numbers in ratio a:b with a given sum
    m = re.search(
        r"\bnumbers?\s+(?:are\s+)?in\s+(?:the\s+)?ratio\s+"
        r"(\d+)\s*:\s*(\d+)\s+and\s+(?:their\s+)?sum\s+is\s+("
        + _NUM + r")", q)
    if m:
        a, b, total = int(m.group(1)), int(m.group(2)), \
            _num(m.group(3))
        per = total / (a + b)
        steps = [
            f"The numbers are {a} parts and {b} parts: "
            f"{a} + {b} = {a + b} parts = {fmt_num(total)}",
            f"1 part = {fmt_num(total)} ÷ {a + b} = "
            f"{fmt_num(per)}",
            f"First number = {a} × {fmt_num(per)} = "
            f"{fmt_num(a * per)}",
            f"Second number = {b} × {fmt_num(per)} = "
            f"{fmt_num(b * per)}",
        ]
        return {"type": "applied", "op": "ratio_sum",
                "answer": f"{fmt_num(a * per)} and "
                          f"{fmt_num(b * per)}",
                "steps": steps, "value": [a * per, b * per]}
    # Simplify a ratio: "ratio of 20 to 45"
    m = re.search(r"\bratio\s+of\s+(" + _NUM + r")\s+(?:to|and)\s+("
                  + _NUM + r")", q) or re.search(
                      r"\bsimplify\s+(?:the\s+)?ratio\s+(\d+)\s*:\s*"
                      r"(\d+)", q) or re.search(
                          r"\bratio\s+(\d+)\s*:\s*(\d+)\b", q)
    if m:
        fa, fb = _ratio_parts(m.group(1)), _ratio_parts(m.group(2))
        if fb == 0:
            return None
        # Scale both to integers, then divide by the gcd.
        den = math.lcm(fa.denominator, fb.denominator)
        ia, ib = int(fa * den), int(fb * den)
        g = math.gcd(abs(ia), abs(ib)) or 1
        steps = [
            f"Write the ratio as a fraction: {fmt_num(fa)}/"
            f"{fmt_num(fb)}",
            f"Divide both numbers by their HCF ({g}): "
            f"{fmt_num(fa)} ÷ {g} = {ia // g} and {fmt_num(fb)} ÷ "
            f"{g} = {ib // g}",
            f"Simplest form: {ia // g} : {ib // g}",
        ]
        return {"type": "applied", "op": "ratio",
                "answer": f"{ia // g} : {ib // g}", "steps": steps}
    return None


def _unitary_cost(q):
    m = re.search(
        r"\b(" + _NUM + r")\s+[\w]+\s+(?:cost|price)\s+(?:is\s+)?"
        r"(?:" + _RS + r"\s*)?(" + _NUM + r")\b[\s\S]{0,40}?"
        r"\b(?:cost|price)\s+of\s+(" + _NUM + r")\b", q) or \
        re.search(
            r"\bcost\s+of\s+(" + _NUM + r")\s+[\w]+\s+(?:is\s+)?"
            r"(?:" + _RS + r"\s*)?(" + _NUM + r")\b[\s\S]{0,40}?"
            r"\bcost\s+of\s+(" + _NUM + r")\b", q)
    if not m:
        return None
    n1, total, n2 = _num(m.group(1)), _num(m.group(2)), \
        _num(m.group(3))
    if n1 == 0:
        return None
    one = total / n1
    steps = [
        f"Cost of {fmt_num(n1)} = Rs {fmt_num(total)}",
        f"Cost of 1 = Rs {fmt_num(total)} ÷ {fmt_num(n1)} = "
        f"Rs {fmt_num(one)}",
        f"Cost of {fmt_num(n2)} = {fmt_num(n2)} × "
        f"Rs {fmt_num(one)} = Rs {fmt_num(one * n2)}",
    ]
    return {"type": "applied", "op": "unitary_cost",
            "answer": f"Rs {fmt_num(one * n2)}", "steps": steps,
            "value": one * n2}


# --------------------------------------------------------------------------
# Simple interest / profit & loss / speed
# --------------------------------------------------------------------------
_SI_RE = re.compile(
    r"simple\s+interest\s+on\s+(?:" + _RS + r"\s*)?(" + _NUM + r")"
    r"\s+(?:at\s+)?(" + _NUM + r")\s*%\s*(?:per\s+annum\s+)?"
    r"(?:for\s+)?(" + _NUM + r")\s*(years?|yrs?|months?)", re.I)


def _simple_interest(q):
    m = _SI_RE.search(q)
    if not m:
        return None
    P, R, T = (float(m.group(i)) for i in (1, 2, 3))
    unit = m.group(4).lower()
    steps = ["Simple Interest = P × R × T / 100"]
    if unit.startswith("month"):
        steps.append(f"Time in years: T = {fmt_num(T)} months ÷ "
                     f"12 = {fmt_num(T / 12)} years")
        T = T / 12.0
    si = P * R * T / 100.0
    steps.append(f"= {fmt_num(P)} × {fmt_num(R)} × {fmt_num(T)} "
                 f"/ 100 = {fmt_num(si)}")
    steps.append(f"Total amount = P + SI = {fmt_num(P + si)}")
    return {"type": "word_problem", "op": "simple_interest",
            "answer": fmt_num(si), "value": si, "steps": steps,
            "principal": P, "rate": R, "time_years": T}


def _profit_loss(q):
    m = re.search(
        r"\bbought\s+(?:for|at)?\s*(?:" + _RS + r"\s*)?(" + _NUM
        + r")[\s\S]{0,30}?\bsold\s+(?:for|at)?\s*(?:" + _RS
        + r"\s*)?(" + _NUM + r")", q) or re.search(
            r"\bcost\s+price\s+(?:is\s+)?(?:" + _RS + r"\s*)?("
            + _NUM + r")[\s\S]{0,30}?\bselling\s+price\s+"
            r"(?:is\s+)?(?:" + _RS + r"\s*)?(" + _NUM + r")", q) \
        or re.search(
            r"\bcp\s*(?:is|=)?\s*(?:" + _RS + r"\s*)?(" + _NUM
            + r")[\s\S]{0,20}?\bsp\s*(?:is|=)?\s*(?:" + _RS
            + r"\s*)?(" + _NUM + r")", q)
    if not m:
        return None
    cp, sp_ = _num(m.group(1)), _num(m.group(2))
    if cp == 0:
        return None
    diff = sp_ - cp
    kind = "Profit" if diff > 0 else "Loss" if diff < 0 else "None"
    wants_pct = bool(re.search(r"percent|percentage|%", q))
    steps = [
        f"Cost price (CP) = Rs {fmt_num(cp)}, selling price "
        f"(SP) = Rs {fmt_num(sp_)}",
    ]
    if diff == 0:
        steps.append("SP = CP, so there is no profit and no loss.")
        return {"type": "applied", "op": "profit_loss",
                "answer": "No profit, no loss", "steps": steps,
                "value": 0}
    steps.append(f"{kind} = {'SP - CP' if diff > 0 else 'CP - SP'}"
                 f" = Rs {fmt_num(abs(diff))}")
    pct = abs(diff) / cp * 100.0
    if wants_pct:
        steps.append(f"{kind} % = ({kind} ÷ CP) × 100 = "
                     f"({fmt_num(abs(diff))} ÷ {fmt_num(cp)}) × "
                     f"100 = {fmt_num(pct)}%")
        return {"type": "applied", "op": "profit_loss_percent",
                "answer": f"{fmt_num(pct)}%", "steps": steps,
                "value": pct}
    return {"type": "applied", "op": "profit_loss",
            "answer": f"{kind} of Rs {fmt_num(abs(diff))}",
            "steps": steps, "value": abs(diff)}


def _speed(q):
    # km/h <-> m/s conversion
    m = re.search(r"(" + _NUM + r")\s*km/h\s*(?:to|in)\s*m/s", q)
    if m:
        v = _num(m.group(1))
        out = v * 5 / 18
        steps = ["To change km/h into m/s, multiply by 5/18.",
                 f"{fmt_num(v)} × 5/18 = {fmt_num(out)} m/s"]
        return {"type": "applied", "op": "speed_convert",
                "answer": f"{fmt_num(out)} m/s", "steps": steps,
                "value": out}
    m = re.search(r"(" + _NUM + r")\s*m/s\s*(?:to|in)\s*km/h", q)
    if m:
        v = _num(m.group(1))
        out = v * 18 / 5
        steps = ["To change m/s into km/h, multiply by 18/5.",
                 f"{fmt_num(v)} × 18/5 = {fmt_num(out)} km/h"]
        return {"type": "applied", "op": "speed_convert",
                "answer": f"{fmt_num(out)} km/h", "steps": steps,
                "value": out}
    # Speed from distance & time: "travels 180 km in 3 hours"
    m = re.search(
        r"\b(?:travels?|covers?|goes|drives?|runs?)\s+(" + _NUM
        + r")\s*km\s+in\s+(" + _NUM + r")\s*(hours?|hrs?|minutes?|"
        r"mins?)", q) or re.search(
            r"\bdistance\s+(?:of\s+)?(" + _NUM + r")\s*km\s+in\s+("
            + _NUM + r")\s*(hours?|hrs?|minutes?|mins?)", q)
    if m:
        dist, t = _num(m.group(1)), _num(m.group(2))
        unit = m.group(3)
        if t == 0:
            return None
        steps = [f"Speed = distance ÷ time = {fmt_num(dist)} km "
                 f"÷ {fmt_num(t)} {unit}"]
        if unit.startswith("min"):
            speed = dist / (t / 60.0)
            steps.append(f"Time = {fmt_num(t)} minutes = "
                         f"{fmt_num(t / 60.0)} hours")
            steps.append(f"Speed = {fmt_num(dist)} ÷ "
                         f"{fmt_num(t / 60.0)} = {fmt_num(speed)} "
                         f"km/h")
        else:
            speed = dist / t
            steps.append(f"= {fmt_num(speed)} km/h")
        return {"type": "applied", "op": "speed",
                "answer": f"{fmt_num(speed)} km/h", "steps": steps,
                "value": speed}
    # Time from distance & speed
    m = re.search(
        r"\bhow\s+long[\s\S]{0,40}?(" + _NUM + r")\s*km\s+at\s+("
        + _NUM + r")\s*km/h", q)
    if m:
        dist, speed = _num(m.group(1)), _num(m.group(2))
        if speed == 0:
            return None
        t = dist / speed
        steps = [f"Time = distance ÷ speed = {fmt_num(dist)} ÷ "
                 f"{fmt_num(speed)} = {fmt_num(t)} hours"]
        return {"type": "applied", "op": "time_from_speed",
                "answer": f"{fmt_num(t)} hours", "steps": steps,
                "value": t}
    return None


# --------------------------------------------------------------------------
# Linear word equations + discriminant
# --------------------------------------------------------------------------
def _word_equation(q):
    def _lin(setup, solve_steps, value):
        steps = [setup] + solve_steps + [f"The number is "
                                         f"{fmt_num(value)}"]
        return {"type": "algebra", "op": "equation",
                "answer": f"x = {fmt_num(value)}",
                "solutions": [fmt_num(value)], "steps": steps}

    m = re.search(r"\ba\s+number\s+increased\s+by\s+(" + _NUM
                  + r")\s+is\s+(" + _NUM + r")", q)
    if m:
        a, s = _num(m.group(1)), _num(m.group(2))
        return _lin(f"Let the number be x: x + {fmt_num(a)} = "
                    f"{fmt_num(s)}",
                    [f"Subtract {fmt_num(a)} from both sides: "
                     f"x = {fmt_num(s)} - {fmt_num(a)}"], s - a)
    m = re.search(r"\ba\s+number\s+decreased\s+by\s+(" + _NUM
                  + r")\s+is\s+(" + _NUM + r")", q)
    if m:
        a, s = _num(m.group(1)), _num(m.group(2))
        return _lin(f"Let the number be x: x - {fmt_num(a)} = "
                    f"{fmt_num(s)}",
                    [f"Add {fmt_num(a)} to both sides: "
                     f"x = {fmt_num(s)} + {fmt_num(a)}"], s + a)
    m = re.search(r"\b(?:twice|double)\s+(?:of\s+)?(?:a\s+)?number"
                  r"\s+is\s+(" + _NUM + r")", q)
    if m:
        s = _num(m.group(1))
        return _lin("Let the number be x: 2x = " + fmt_num(s),
                    [f"Divide both sides by 2: x = {fmt_num(s)} "
                     f"÷ 2"], s / 2)
    m = re.search(r"\b(?:thrice|three\s+times)\s+(?:a\s+)?number"
                  r"\s+is\s+(" + _NUM + r")", q)
    if m:
        s = _num(m.group(1))
        return _lin("Let the number be x: 3x = " + fmt_num(s),
                    [f"Divide both sides by 3: x = {fmt_num(s)} "
                     f"÷ 3"], s / 3)
    m = re.search(r"\b(" + _NUM + r")\s+times\s+a\s+number\s+is\s+("
                  + _NUM + r")", q)
    if m:
        k, s = _num(m.group(1)), _num(m.group(2))
        if k == 0:
            return None
        return _lin(f"Let the number be x: {fmt_num(k)}x = "
                    f"{fmt_num(s)}",
                    [f"Divide both sides by {fmt_num(k)}: "
                     f"x = {fmt_num(s)} ÷ {fmt_num(k)}"], s / k)
    m = re.search(r"\bsum\s+of\s+a\s+number\s+and\s+(" + _NUM
                  + r")\s+is\s+(" + _NUM + r")", q) or re.search(
                      r"\b(" + _NUM + r")\s+more\s+than\s+a\s+number"
                      r"\s+is\s+(" + _NUM + r")", q)
    if m:
        a, s = _num(m.group(1)), _num(m.group(2))
        return _lin(f"Let the number be x: x + {fmt_num(a)} = "
                    f"{fmt_num(s)}",
                    [f"Subtract {fmt_num(a)} from both sides: "
                     f"x = {fmt_num(s)} - {fmt_num(a)}"], s - a)
    m = re.search(r"\bwhen\s+(" + _NUM + r")\s+is\s+added\s+to\s+a"
                  r"\s+number\s*,?\s+(?:the\s+)?(?:result|sum)\s+"
                  r"is\s+(" + _NUM + r")", q)
    if m:
        a, s = _num(m.group(1)), _num(m.group(2))
        return _lin(f"Let the number be x: x + {fmt_num(a)} = "
                    f"{fmt_num(s)}",
                    [f"Subtract {fmt_num(a)} from both sides: "
                     f"x = {fmt_num(s)} - {fmt_num(a)}"], s - a)
    return None


def _quadratic_info(q):
    m = re.search(r"\bdiscriminant\s+of\s+(.+)$", q) or \
        re.search(r"\bnature\s+of\s+(?:the\s+)?roots\s+of\s+(.+)$",
                  q)
    if not m:
        return None
    text = m.group(1).strip().rstrip(".?")
    text = re.sub(r"=\s*0\s*$", "", text)
    if "=" in text:
        left, right = text.split("=", 1)
        expr_text = f"({left}) - ({right})"
    else:
        expr_text = text
    try:
        expr = sp.expand(parse_expression(expr_text))
        symbols = sorted(expr.free_symbols, key=lambda s: s.name)
        if len(symbols) != 1:
            return None
        var = symbols[0]
        degree, coeffs = _poly_coeffs(expr, var)
        if degree != 2:
            return None
    except Exception:
        return None
    a, b, c = (coeffs.get(2, 0), coeffs.get(1, 0), coeffs.get(0, 0))
    D = b ** 2 - 4 * a * c
    steps = [
        f"Standard form: {fmt(a)}·{var}^2 + {fmt(b)}·{var} + "
        f"{fmt(c)} = 0, so a = {fmt(a)}, b = {fmt(b)}, "
        f"c = {fmt(c)}",
        f"Discriminant D = b^2 - 4ac = ({fmt(b)})^2 - "
        f"4·{fmt(a)}·{fmt(c)} = {fmt(D)}",
    ]
    if "discriminant" in q:
        return {"type": "algebra", "op": "discriminant",
                "answer": fmt(D), "steps": steps,
                "value": float(D) if D.is_number else None}
    if D > 0:
        nature, note = "Two distinct real roots", "D > 0"
    elif D == 0:
        nature, note = "Two equal real roots (one repeated root)", \
            "D = 0"
    else:
        nature, note = "No real roots (the roots are complex)", \
            "D < 0"
    steps.append(f"Since {note}: the equation has "
                 f"{nature.lower()}.")
    return {"type": "algebra", "op": "nature_of_roots",
            "answer": nature, "steps": steps}


_FAMILIES = (_ratio, _unitary_cost, _simple_interest, _profit_loss,
             _speed, _word_equation, _quadratic_info)


def solve_applied(question: str):
    """Wave 13 applied solver. Returns a result dict, or None
    when no applied pattern matches. Never raises."""
    try:
        q = " " + str(question).strip().lower() + " "
        q = re.sub(r"\s+", " ", q)
        for fn in _FAMILIES:
            try:
                out = fn(q)
            except Exception:
                out = None
            if out is not None:
                return out
        return None
    except Exception:
        return None
