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
        # Wave 30 story form: "A man borrowed Rs 12000 at 10% per
        # annum simple interest for 2 years. How much interest
        # will he pay?" — the numbers are scattered through the
        # sentence instead of sitting in the fixed formula order.
        if "simple interest" not in q:
            return None
        mp = re.search(
            r"(?:borrowed|deposited|invested|lent|principal|sum)"
            r"\s+(?:of\s+)?(?:" + _RS + r"\s*)?(" + _NUM + r")", q)
        mr = re.search(r"(" + _NUM + r")\s*%\s*(?:per\s+annum)?", q)
        mt = re.search(r"for\s+(" + _NUM + r")\s*(years?|yrs?|"
                       r"months?)", q)
        if not (mp and mr and mt):
            return None
        P, R, T = float(mp.group(1)), float(mr.group(1)), \
            float(mt.group(1))
        unit = mt.group(2).lower()
        steps = [f"Principal P = Rs {fmt_num(P)}, rate R = "
                 f"{fmt_num(R)}% per annum, time T = "
                 f"{fmt_num(T)} {unit}",
                 "Simple Interest = P × R × T / 100"]
        if unit.startswith("month"):
            steps.append(f"Time in years: T = {fmt_num(T)} "
                         f"months ÷ 12 = {fmt_num(T / 12)} years")
            T = T / 12.0
        si = P * R * T / 100.0
        steps.append(f"= {fmt_num(P)} × {fmt_num(R)} × "
                     f"{fmt_num(T)} / 100 = {fmt_num(si)}")
        steps.append(f"Total amount = P + SI = {fmt_num(P + si)}")
        return {"type": "word_problem", "op": "simple_interest",
                "answer": fmt_num(si), "value": si, "steps": steps,
                "principal": P, "rate": R, "time_years": T}
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
    # Wave 32 robustness fix (not a new topic): "nature of roots
    # of THE EQUATION x^2 + ..." kept the words "the equation" in
    # the captured text and the parse failed, so the ask fell
    # through; without those words the same question worked.
    text = re.sub(r"^(?:the\s+)?(?:quadratic\s+)?(?:equation|polynomial)\s+",
                  "", text)
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


# --------------------------------------------------------------------------
# Wave 30 families — the "similar example instead of my question"
# complaint (Suraj, 14 Nov 2026). Every pattern below extracts the
# STUDENT'S OWN numbers and solves that exact question; the
# similar-example layer is now only for genuinely unparseable
# input. All patterns stay strict: clean numbers or None.
# --------------------------------------------------------------------------
def _speed_time_quadratic(q):
    """Fixed distance, speed changed by k, time changes by t:
        faster: D/x - D/(x+k) = t      slower: D/(x-k) - D/x = t
    Suraj's exact question (Class 10, NCERT Ex. 4.3): "एक रेलगाड़ी
    एक समान चाल से 360 km की दूरी तय करती है। यदि यह चाल 5 km/h
    अधिक होती, तो वह उसी यात्रा में 1 घंटा कम समय लेती।" — and its
    English twin. Both languages, one equation."""
    if not ("speed" in q or "train" in q or "चाल" in q
            or "रेलगाड़ी" in q):
        return None
    md = re.search(r"(" + _NUM + r")\s*km\s*की\s*दूरी", q) or \
        re.search(r"distance\s+of\s+(" + _NUM + r")\s*km", q)
    if md:
        dist = sp.Rational(md.group(1))
    else:
        cand = [m.group(1) for m in re.finditer(
            r"(" + _NUM + r")\s*km(?!\s*/)", q)]
        if not cand:
            return None
        dist = sp.Rational(cand[0])
    inc = re.search(r"(" + _NUM + r")\s*km/h\s+more\b", q) or \
        re.search(r"increased\s+by\s+(" + _NUM + r")\s*km/h", q) or \
        re.search(r"(" + _NUM + r")\s*km/h\s+अधिक", q)
    dec = re.search(r"(" + _NUM + r")\s*km/h\s+less\b", q) or \
        re.search(r"decreased\s+by\s+(" + _NUM + r")\s*km/h", q) or \
        re.search(r"(" + _NUM + r")\s*km/h\s+कम", q)

    def _time(pats):
        for pat in pats:
            m = re.search(pat, q)
            if m:
                v = sp.Rational(m.group(1))
                unit = m.group(2)
                if "min" in unit or "मिनट" in unit:
                    v = v / 60
                return v
        return None

    t_less = _time([r"(" + _NUM + r")\s*(hours?|hrs?|minutes?|"
                    r"mins?)\s+less",
                    r"(" + _NUM + r")\s*(घंटा|घंटे|मिनट)\s+कम"])
    t_more = _time([r"(" + _NUM + r")\s*(hours?|hrs?|minutes?|"
                    r"mins?)\s+more",
                    r"(" + _NUM + r")\s*(घंटा|घंटे|मिनट)\s+अधिक"])
    if inc and t_less is not None and not dec:
        k, t, faster = sp.Rational(inc.group(1)), t_less, True
    elif dec and t_more is not None and not inc:
        k, t, faster = sp.Rational(dec.group(1)), t_more, False
    else:
        return None
    if dist <= 0 or k <= 0 or t <= 0:
        return None
    x = sp.symbols("x")
    quad = t * x ** 2 + (t * k if faster else -t * k) * x - dist * k
    try:
        roots = [r for r in sp.solve(quad, x) if r.is_real]
    except Exception:
        return None
    good = [r for r in roots if r > 0 and (faster or r > k)]
    if len(good) != 1 or not roots:
        return None
    root = good[0]
    D_s, k_s, t_s = fmt_num(dist), fmt_num(k), fmt_num(t)
    if faster:
        steps = [
            f"Let the original speed be x km/h. Time taken for "
            f"the {D_s} km journey = {D_s}/x hours.",
            f"If the speed were {k_s} km/h more, the new speed "
            f"would be (x + {k_s}) km/h and the time would be "
            f"{D_s}/(x + {k_s}) hours.",
            f"The faster journey takes {t_s} hour(s) less: "
            f"{D_s}/x - {D_s}/(x + {k_s}) = {t_s}",
            f"Multiply both sides by x(x + {k_s}): "
            f"{fmt_num(dist * k)} = {t_s}·x(x + {k_s}), which "
            f"gives {fmt(sp.expand(quad / t))} = 0",
        ]
    else:
        steps = [
            f"Let the original speed be x km/h. Time taken for "
            f"the {D_s} km journey = {D_s}/x hours.",
            f"If the speed were {k_s} km/h less, the new speed "
            f"would be (x - {k_s}) km/h and the time would be "
            f"{D_s}/(x - {k_s}) hours.",
            f"The slower journey takes {t_s} hour(s) more: "
            f"{D_s}/(x - {k_s}) - {D_s}/x = {t_s}",
            f"Multiply both sides by x(x - {k_s}): "
            f"{fmt_num(dist * k)} = {t_s}·x(x - {k_s}), which "
            f"gives {fmt(sp.expand(quad / t))} = 0",
        ]
    steps.append("Solving the quadratic: " + " or ".join(
        f"x = {fmt(r)}" for r in roots))
    steps.append(f"Speed cannot be negative, so x = {fmt(root)}.")
    steps.append(f"The speed of the train is {fmt_num(root)} km/h.")
    return {"type": "applied", "op": "speed_time_quadratic",
            "answer": f"{fmt_num(root)} km/h",
            "solutions": [fmt(root)], "steps": steps,
            "value": float(root)}


def _sum_difference(q):
    m = re.search(
        r"sum\s+of\s+(?:the\s+)?two\s+numbers\s+is\s+(" + _NUM
        + r")\s+and\s+(?:their\s+)?difference\s+is\s+(" + _NUM
        + r")", q) or re.search(
            r"sum\s+is\s+(" + _NUM + r")\s+and\s+(?:the\s+)?"
            r"difference\s+is\s+(" + _NUM + r")", q)
    if not m:
        return None
    S, D = _num(m.group(1)), _num(m.group(2))
    a, b = (S + D) / 2, (S - D) / 2
    steps = [
        f"Let the numbers be x and y (x > y): x + y = "
        f"{fmt_num(S)} and x - y = {fmt_num(D)}",
        f"Add the two equations: 2x = {fmt_num(S)} + "
        f"{fmt_num(D)} = {fmt_num(S + D)}, so x = {fmt_num(a)}",
        f"Then y = {fmt_num(S)} - {fmt_num(a)} = {fmt_num(b)}",
    ]
    return {"type": "applied", "op": "sum_difference",
            "answer": f"{fmt_num(a)} and {fmt_num(b)}",
            "steps": steps, "value": [a, b]}


def _clean_name(s):
    return re.sub(r"^(a|an|the|his|her|their|my)\s+", "",
                  s.strip())


def _ages(q):
    qq = q.replace("twice", "2 times").replace("thrice", "3 times")
    # Elder is k times as old; after T years, m times as old.
    m1 = re.search(
        r"(?:a\s+|the\s+)?(\w+)\s+is\s+(" + _NUM + r")\s+times\s+"
        r"as\s+old\s+as\s+(?:his\s+|her\s+|their\s+)?(\w+)", qq)
    m2 = re.search(
        r"after\s+(" + _NUM + r")\s+years?[\s\S]{0,60}?(" + _NUM
        + r")\s+times\s+as\s+old", qq)
    if m1 and m2:
        elder, younger = _clean_name(m1.group(1)), \
            _clean_name(m1.group(3))
        k, T, mm = _num(m1.group(2)), _num(m2.group(1)), \
            _num(m2.group(2))
        if k > mm > 1:
            y = T * (mm - 1) / (k - mm)
            e = k * y
            if y > 0:
                steps = [
                    f"Let the {younger}'s present age be x years. "
                    f"Then the {elder}'s present age is "
                    f"{fmt_num(k)}x years.",
                    f"After {fmt_num(T)} years: {elder} will be "
                    f"{fmt_num(k)}x + {fmt_num(T)} and {younger} "
                    f"will be x + {fmt_num(T)}, and the {elder} "
                    f"will be {fmt_num(mm)} times as old: "
                    f"{fmt_num(k)}x + {fmt_num(T)} = "
                    f"{fmt_num(mm)}(x + {fmt_num(T)})",
                    f"Solving: x = {fmt_num(y)}",
                    f"So the {younger} is {fmt_num(y)} years old "
                    f"and the {elder} is {fmt_num(k)} × "
                    f"{fmt_num(y)} = {fmt_num(e)} years old.",
                ]
                return {"type": "applied", "op": "ages_ratio",
                        "answer": f"{elder.capitalize()} is "
                                  f"{fmt_num(e)} years old and "
                                  f"{younger} is {fmt_num(y)} "
                                  f"years old",
                        "steps": steps, "value": [e, y]}
    # Elder is d years older; the ages add up to S.
    m3 = re.search(
        r"(\w+)\s+is\s+(" + _NUM + r")\s+years?\s+older\s+than\s+"
        r"(?:his\s+|her\s+|their\s+)?(\w+)", qq)
    m4 = re.search(r"sum\s+of\s+their\s+ages\s+is\s+(" + _NUM
                   + r")", qq)
    if m3 and m4:
        elder, younger = _clean_name(m3.group(1)), \
            _clean_name(m3.group(3))
        d, S = _num(m3.group(2)), _num(m4.group(1))
        e, y = (S + d) / 2, (S - d) / 2
        if y < 0:
            return None
        steps = [
            f"Let the {younger}'s age be x years. Then the "
            f"{elder}'s age is x + {fmt_num(d)} years.",
            f"Their ages add up to {fmt_num(S)}: x + (x + "
            f"{fmt_num(d)}) = {fmt_num(S)}",
            f"2x = {fmt_num(S)} - {fmt_num(d)} = "
            f"{fmt_num(S - d)}, so x = {fmt_num(y)}",
            f"So the {younger} is {fmt_num(y)} years old and "
            f"the {elder} is {fmt_num(y)} + {fmt_num(d)} = "
            f"{fmt_num(e)} years old.",
        ]
        return {"type": "applied", "op": "ages_sum",
                "answer": f"{elder.capitalize()} is "
                          f"{fmt_num(e)} years old and {younger} "
                          f"is {fmt_num(y)} years old",
                "steps": steps, "value": [e, y]}
    return None


def _consecutive_product(q):
    m = re.search(
        r"product\s+of\s+two\s+consecutive\s+(odd|even)\s+"
        r"(?:integers|numbers)\s+is\s+(" + _NUM + r")", q)
    gap = 2
    if not m:
        m = re.search(
            r"product\s+of\s+two\s+consecutive\s+(?:integers|"
            r"numbers|natural\s+numbers|positive\s+integers)\s+"
            r"is\s+(" + _NUM + r")", q)
        gap = 1
    if not m:
        return None
    P = _num(m.group(2) if gap == 2 else m.group(1))
    disc = gap * gap + 4 * P
    root_disc = math.isqrt(int(disc)) if float(disc).is_integer() \
        else None
    if root_disc is None or root_disc * root_disc != int(disc):
        return None
    xv = (-gap + root_disc) // 2
    if xv <= 0:
        return None
    steps = [
        f"Let the first integer be x. The next consecutive "
        f"{'odd/even ' if gap == 2 else ''}integer is "
        f"x + {gap}.",
        f"Their product: x(x + {gap}) = {fmt_num(P)}, so "
        f"x^2 + {gap}x - {fmt_num(P)} = 0",
        f"Solving: x = {fmt_num(xv)} (the negative root is "
        f"rejected: the integers are positive).",
        f"The integers are {fmt_num(xv)} and "
        f"{fmt_num(xv + gap)}.",
    ]
    return {"type": "applied", "op": "consecutive_product",
            "answer": f"{fmt_num(xv)} and {fmt_num(xv + gap)}",
            "steps": steps, "value": [xv, xv + gap]}


def _rectangle_word(q):
    m1 = re.search(
        r"length\s+(?:is\s+)?(" + _NUM + r")\s*(?:m|cm|mm|"
        r"metres?|meters?)?\s*more\s+than\s+(?:its\s+|the\s+)?"
        r"breadth", q)
    m2 = re.search(
        r"area\s+(?:of\s+(?:the\s+|this\s+)?\w+\s+)?is\s+("
        + _NUM + r")", q)
    if not (m1 and m2):
        return None
    d, A = _num(m1.group(1)), _num(m2.group(1))
    disc = d * d + 4 * A
    sd = math.sqrt(disc)
    b = (-d + sd) / 2
    if b <= 0:
        return None
    l = b + d
    steps = [
        f"Let the breadth be b. Then the length is b + "
        f"{fmt_num(d)}.",
        f"Area = length × breadth: b(b + {fmt_num(d)}) = "
        f"{fmt_num(A)}, so b^2 + {fmt_num(d)}b - {fmt_num(A)} "
        f"= 0",
        f"Solving: b = {fmt_num(b)} (breadth cannot be "
        f"negative).",
        f"Length = {fmt_num(b)} + {fmt_num(d)} = "
        f"{fmt_num(l)}.",
    ]
    return {"type": "applied", "op": "rectangle_word",
            "answer": f"Length = {fmt_num(l)} m, breadth = "
                      f"{fmt_num(b)} m",
            "steps": steps, "value": [l, b]}


def _compound_interest(q):
    m = re.search(
        r"compound\s+interest\s+on\s+(?:" + _RS + r"\s*)?("
        + _NUM + r")\s+at\s+(" + _NUM + r")\s*%\s*(?:per\s+"
        r"annum\s+)?(?:for\s+)?(" + _NUM + r")\s*(?:years?|yrs?)",
        q)
    if not m:
        return None
    P, R, T = (sp.Rational(m.group(i)) for i in (1, 2, 3))
    if T != int(T):
        return None
    amount = P * (1 + R / 100) ** int(T)
    ci = amount - P
    steps = [
        "Compound interest: Amount A = P(1 + R/100)^T",
        f"A = {fmt_num(P)} × (1 + {fmt_num(R)}/100)^{fmt_num(T)} "
        f"= {fmt_num(amount)}",
        f"Compound interest = A - P = {fmt_num(amount)} - "
        f"{fmt_num(P)} = {fmt_num(ci)}",
    ]
    return {"type": "applied", "op": "compound_interest",
            "answer": fmt_num(ci), "value": float(ci),
            "steps": steps, "amount": float(amount)}


def _discount(q):
    if "discount" not in q:
        return None
    md = re.search(r"discount\s+of\s+(" + _NUM + r")\s*%", q) \
        or re.search(r"(" + _NUM + r")\s*%\s+discount", q)
    mm = re.search(
        r"marked\s+price\s+(?:is\s+)?(?:" + _RS + r"\s*)?("
        + _NUM + r")", q) or re.search(
            r"discount\s+of\s+" + _NUM + r"\s*%\s+on\s+"
            r"[\w\s]{0,24}?(?:" + _RS + r"\s*)?(" + _NUM + r")", q)
    if not (md and mm):
        return None
    d, M = _num(md.group(1)), _num(mm.group(1))
    if M <= 0 or not (0 <= d < 100):
        return None
    off = M * d / 100.0
    sp_ = M - off
    steps = [
        f"Marked price = Rs {fmt_num(M)}, discount = "
        f"{fmt_num(d)}%",
        f"Discount amount = {fmt_num(d)}% of {fmt_num(M)} = "
        f"Rs {fmt_num(off)}",
        f"Selling price = {fmt_num(M)} - {fmt_num(off)} = "
        f"Rs {fmt_num(sp_)}",
    ]
    return {"type": "applied", "op": "discount",
            "answer": f"Rs {fmt_num(sp_)}", "steps": steps,
            "value": sp_}


def _percent_score(q):
    if "percent" not in q and "%" not in q:
        return None
    m = re.search(r"(" + _NUM + r")\s+(?:marks\s+)?out\s+of\s+("
                  + _NUM + r")", q)
    if not m:
        return None
    part, whole = _num(m.group(1)), _num(m.group(2))
    if whole == 0:
        return None
    pct = part / whole * 100.0
    steps = [
        f"Percentage = (marks scored ÷ total marks) × 100",
        f"= ({fmt_num(part)} ÷ {fmt_num(whole)}) × 100 = "
        f"{fmt_num(pct)}%",
    ]
    return {"type": "applied", "op": "percent_score",
            "answer": f"{fmt_num(pct)}%", "steps": steps,
            "value": pct}


def _profit_loss_forms(q):
    # Sold at SP with a stated profit/loss % — find the CP.
    m = re.search(
        r"sold\s+(?:at|for)\s+(?:" + _RS + r"\s*)?(" + _NUM
        + r")[\s\S]{0,40}?\b(profit|loss)\s+of\s+(" + _NUM
        + r")\s*%", q)
    if m:
        sp_, kind, p = _num(m.group(1)), m.group(2), \
            _num(m.group(3))
        if kind == "loss":
            if p >= 100:
                return None
            cp = sp_ / (1 - p / 100.0)
            steps = [
                f"With a loss of {fmt_num(p)}%, SP = CP × "
                f"(1 - {fmt_num(p)}/100) = {fmt_num(1 - p / 100)} "
                f"× CP",
                f"CP = {fmt_num(sp_)} ÷ {fmt_num(1 - p / 100)} "
                f"= Rs {fmt_num(cp)}",
            ]
        else:
            cp = sp_ / (1 + p / 100.0)
            steps = [
                f"With a profit of {fmt_num(p)}%, SP = CP × "
                f"(1 + {fmt_num(p)}/100) = {fmt_num(1 + p / 100)} "
                f"× CP",
                f"CP = {fmt_num(sp_)} ÷ {fmt_num(1 + p / 100)} "
                f"= Rs {fmt_num(cp)}",
            ]
        return {"type": "applied", "op": "reverse_profit_loss",
                "answer": f"Rs {fmt_num(cp)}", "steps": steps,
                "value": cp}
    # CP with a stated profit/loss % — find the SP.
    m = re.search(
        r"(?:cost\s+price|cp)\s+(?:is\s+)?(?:" + _RS + r"\s*)?("
        + _NUM + r")[\s\S]{0,40}?\b(profit|loss)\s+of\s+("
        + _NUM + r")\s*%", q)
    if m and "selling" in q:
        cp, kind, p = _num(m.group(1)), m.group(2), \
            _num(m.group(3))
        if kind == "loss":
            sp_ = cp * (1 - p / 100.0)
            steps = [f"SP = CP × (1 - loss/100) = "
                     f"{fmt_num(cp)} × {fmt_num(1 - p / 100)} "
                     f"= Rs {fmt_num(sp_)}"]
        else:
            sp_ = cp * (1 + p / 100.0)
            steps = [f"SP = CP × (1 + profit/100) = "
                     f"{fmt_num(cp)} × {fmt_num(1 + p / 100)} "
                     f"= Rs {fmt_num(sp_)}"]
        return {"type": "applied", "op": "profit_loss_sp",
                "answer": f"Rs {fmt_num(sp_)}", "steps": steps,
                "value": sp_}
    return None


def _ratio_share_ask(q):
    m = re.search(r"ratio\s+of\s+(\w+)\s+to\s+(\w+)\b"
                  r"[\s\S]{0,30}?(\d+)\s*:\s*(\d+)", q)
    if not m:
        return None
    g1, g2 = m.group(1), m.group(2)
    a, b = int(m.group(3)), int(m.group(4))
    mt = re.search(r"there\s+are\s+(" + _NUM + r")", q) or \
        re.search(r"total\s+(?:of\s+)?(" + _NUM + r")", q) or \
        re.search(r"(" + _NUM + r")\s+(?:students|children|"
                  r"people)\b", q)
    mq = re.search(r"how\s+many\s+(\w+)", q)
    if not (mt and mq):
        return None
    total, asked = _num(mt.group(1)), mq.group(1)
    if asked == g1:
        part, other = a, b
    elif asked == g2:
        part, other = b, a
    else:
        return None
    share = total * part / (a + b)
    steps = [
        f"The ratio {a}:{b} has {a} + {b} = {a + b} parts in "
        f"total, and the total is {fmt_num(total)}.",
        f"Value of 1 part = {fmt_num(total)} ÷ {a + b} = "
        f"{fmt_num(total / (a + b))}",
        f"{asked.capitalize()} = {part} parts = {part} × "
        f"{fmt_num(total / (a + b))} = {fmt_num(share)}",
    ]
    return {"type": "applied", "op": "ratio_share",
            "answer": f"{fmt_num(share)} {asked}",
            "steps": steps, "value": share}


def _inverse_proportion(q):
    if "how many days" not in q:
        return None
    m = re.search(
        r"(" + _NUM + r")\s+(workers|men|women|people|"
        r"labourers|machines)\s+can\s+[\w\s]{0,30}?\bin\s+("
        + _NUM + r")\s+days", q)
    if not m:
        return None
    n1, unit, d1 = _num(m.group(1)), m.group(2), \
        _num(m.group(3))
    counts = [_num(v) for v, _u in re.findall(
        r"(" + _NUM + r")\s+(workers|men|women|people|"
        r"labourers|machines)", q)]
    others = [c for c in counts if c != n1]
    if not others:
        return None
    n2 = others[0]
    days = n1 * d1 / n2
    steps = [
        f"The work is fixed, so more {unit} means fewer days "
        f"(inverse proportion).",
        f"Total work = {fmt_num(n1)} {unit} × {fmt_num(d1)} "
        f"days = {fmt_num(n1 * d1)} {unit}-days",
        f"Days for {fmt_num(n2)} {unit} = {fmt_num(n1 * d1)} "
        f"÷ {fmt_num(n2)} = {fmt_num(days)} days",
    ]
    return {"type": "applied", "op": "inverse_proportion",
            "answer": f"{fmt_num(days)} days", "steps": steps,
            "value": days}


def _bells_lcm(q):
    if "interval" not in q or not ("toll" in q or "bell" in q
                                   or "blink" in q):
        return None
    m = re.search(r"intervals?\s+of\s+([^.]+)", q)
    if not m:
        return None
    ivals = [int(v) for v in re.findall(r"\d+", m.group(1))]
    if len(ivals) < 2:
        return None
    L = math.lcm(*ivals)
    steps = [
        f"The bells toll together again after the LCM of "
        f"{' and '.join(str(v) for v in ivals)} minutes.",
        f"LCM({', '.join(str(v) for v in ivals)}) = {L}, so "
        f"they toll together again after {L} minutes.",
    ]
    mt = re.search(r"(\d{1,2}):(\d{2})\s*(am|pm)", q)
    if mt:
        h = int(mt.group(1)) % 12 + (12 if mt.group(2) == "pm"
                                     else 0)
        total_min = h * 60 + int(mt.group(2)) + L
        nh, nm = (total_min // 60) % 24, total_min % 60
        suffix = "am" if nh < 12 else "pm"
        h12 = nh % 12 or 12
        new_time = f"{h12}:{nm:02d} {suffix}"
        steps.append(f"Starting at {mt.group(1)}:{mt.group(2)} "
                     f"{mt.group(3)}, add {L} minutes: "
                     f"{new_time}.")
        return {"type": "applied", "op": "bells_lcm",
                "answer": f"{new_time} (after {L} minutes)",
                "steps": steps, "value": L}
    return {"type": "applied", "op": "bells_lcm",
            "answer": f"After {L} minutes", "steps": steps,
            "value": L}


def _train_crossing(q):
    mt = re.search(r"train\s+of\s+length\s+(" + _NUM + r")\s*m",
                   q) or re.search(
                       r"train[\s\S]{0,20}?(" + _NUM + r")\s*m\s+"
                       r"long", q)
    if not mt:
        return None
    L = _num(mt.group(1))

    def _finish(dist_m, T, label):
        v = dist_m / T
        steps = [f"Speed = distance ÷ time. {label}"]
        steps.append(f"Speed = {fmt_num(dist_m)} ÷ "
                     f"{fmt_num(T)} = {fmt_num(v)} m/s")
        if "km/h" in q:
            kmh = v * 18 / 5
            steps.append(f"Change m/s to km/h (multiply by "
                         f"18/5): {fmt_num(v)} × 18/5 = "
                         f"{fmt_num(kmh)} km/h")
            return {"type": "applied", "op": "train_crossing",
                    "answer": f"{fmt_num(kmh)} km/h",
                    "steps": steps, "value": kmh}
        return {"type": "applied", "op": "train_crossing",
                "answer": f"{fmt_num(v)} m/s", "steps": steps,
                "value": v}

    mp = re.search(
        r"crosses\s+a\s+(?:pole|tree|post|signal)[\s\S]{0,30}?"
        r"in\s+(" + _NUM + r")\s*seconds?", q)
    if mp:
        return _finish(L, _num(mp.group(1)),
                       f"Crossing a pole, the train covers its "
                       f"own length, {fmt_num(L)} m.")
    mpl = re.search(
        r"crosses\s+a\s+(?:platform|bridge|tunnel)\s+(?:of\s+"
        r"length\s+)?(" + _NUM + r")\s*m[\s\S]{0,30}?in\s+("
        + _NUM + r")\s*seconds?", q)
    if mpl:
        P, T = _num(mpl.group(1)), _num(mpl.group(2))
        return _finish(L + P, T,
                       f"Crossing it, the train covers its own "
                       f"length plus the platform: {fmt_num(L)} "
                       f"+ {fmt_num(P)} = {fmt_num(L + P)} m.")
    return None


def _digits(q):
    m1 = re.search(
        r"sum\s+of\s+the\s+digits\s+of\s+a\s+two-digit\s+"
        r"number\s+is\s+(" + _NUM + r")", q)
    m2 = re.search(
        r"reversing\s+the\s+digits\s+is\s+(" + _NUM + r")\s+"
        r"(more|less)\s+than\s+the\s+original", q)
    if not (m1 and m2):
        return None
    S, D = int(float(m1.group(1))), int(float(m2.group(1)))
    if D % 9:
        return None
    diff = D // 9 if m2.group(2) == "more" else -D // 9
    if (S + diff) % 2:
        return None
    b, a = (S + diff) // 2, (S - diff) // 2
    if not (1 <= a <= 9 and 0 <= b <= 9):
        return None
    num = 10 * a + b
    steps = [
        "Let the tens digit be a and the units digit be b. "
        "The number is 10a + b; reversing the digits gives "
        "10b + a.",
        f"Sum of the digits: a + b = {S}.",
        f"The reversed number differs from the original by "
        f"{D}: 9(b - a) = {D} (in size), so b - a = {diff}.",
        f"Solving the two equations: a = {a}, b = {b}.",
        f"The number is 10 × {a} + {b} = {num}.",
    ]
    return {"type": "applied", "op": "digits",
            "answer": str(num), "steps": steps, "value": num}


# --------------------------------------------------------------------------
# Wave 32 families — ~50 new topics (Suraj, 14 Nov 2026: "or bhi
# topics add karo"). Every pattern below was first PROVEN to be a
# gap by a probe battery through the real user path (the question
# returned a fallback, or — worse — a valid-looking op with a wrong
# number). All patterns stay strict: clean numbers or None.
# --------------------------------------------------------------------------

def _money(x):
    """Money display: exact when whole, else 2 decimal places
    (the NCERT convention) instead of a bare fraction."""
    f = float(x)
    if abs(f - round(f)) < 1e-9:
        return fmt_num(int(round(f)))
    return fmt_num(round(f, 2))


def _compound_interest_freq(q):
    """CI compounded half-yearly / quarterly. The annual pattern
    below used to swallow these questions and silently IGNORE the
    frequency, answering the annual figure — a wrong answer with a
    valid op. This family runs first and only fires when a
    compounding frequency is actually named."""
    if "compound interest" not in q:
        return None
    if "half-yearly" in q or "half yearly" in q:
        n = 2
    elif "quarterly" in q:
        n = 4
    else:
        return None
    m = re.search(
        r"compound\s+interest\s+on\s+(?:" + _RS + r"\s*)?("
        + _NUM + r")\s+at\s+(" + _NUM + r")\s*%\s*(?:per\s+"
        r"annum\s+)?(?:for\s+)?(" + _NUM + r")\s*(?:years?|yrs?)",
        q)
    if not m:
        return None
    P, R, T = (sp.Rational(m.group(i)) for i in (1, 2, 3))
    periods = n * T
    if periods != int(periods) or periods <= 0:
        return None
    periods = int(periods)
    rate = R / n
    amount = P * (1 + rate / 100) ** periods
    ci = amount - P
    steps = [
        f"Compounded {'half-yearly' if n == 2 else 'quarterly'}: "
        f"the rate is divided by {n} and the time is multiplied "
        f"by {n}.",
        f"Rate per period = {fmt_num(R)}% / {n} = "
        f"{fmt_num(rate)}%, number of periods = {n} × "
        f"{fmt_num(T)} = {periods}",
        "Amount A = P(1 + r/100)^n",
        f"A = {fmt_num(P)} × (1 + {fmt_num(rate)}/100)^{periods} "
        f"= Rs {_money(amount)}",
        f"Compound interest = A - P = {_money(amount)} - "
        f"{fmt_num(P)} = Rs {_money(ci)}",
    ]
    return {"type": "applied", "op": "compound_interest_freq",
            "answer": _money(ci), "value": float(ci),
            "steps": steps, "amount": float(amount)}


def _gst(q):
    if "gst" not in q:
        return None
    # Reverse: total price INCLUDING gst -> price before gst.
    # Form A: "including 28% GST is Rs 6400" (rate, then total).
    # Form B: "Rs 6400 including 28% GST" (total, then rate).
    rate = total = None
    mA = re.search(r"includ\w*\s+(?:a\s+)?(?:gst\s+of\s+)?("
                   + _NUM + r")\s*%\s*gst[^.]{0,50}?(?:"
                   + _RS + r"\s*)?(" + _NUM + r")", q)
    mB = re.search(r"(?:" + _RS + r"\s*)?(" + _NUM
                   + r")\s*(?:rs)?[^.]{0,30}?includ\w*\s+"
                   r"(?:a\s+)?(?:gst\s+of\s+)?(" + _NUM
                   + r")\s*%", q)
    if mA:
        rate, total = _num(mA.group(1)), _num(mA.group(2))
    elif mB:
        total, rate = _num(mB.group(1)), _num(mB.group(2))
    if rate is not None and total is not None:
        base = total * 100.0 / (100.0 + rate)
        gst_amt = total - base
        steps = [
            f"Total price (including GST) = Rs {fmt_num(total)}, "
            f"GST rate = {fmt_num(rate)}%",
            "Price before GST = total × 100 / (100 + rate)",
            f"= {fmt_num(total)} × 100 / {fmt_num(100.0 + rate)} "
            f"= Rs {fmt_num(base)}",
            f"GST amount = {fmt_num(total)} - {fmt_num(base)} "
            f"= Rs {fmt_num(gst_amt)}",
        ]
        return {"type": "applied", "op": "gst_reverse",
                "answer": f"Rs {fmt_num(base)}",
                "steps": steps, "value": base}
    # Forward: price + gst rate -> gst amount and total.
    mr = re.search(r"(" + _NUM + r")\s*%\s*gst", q) or \
        re.search(r"gst\s*(?:is\s*)?(?:charged\s*at\s*|@\s*)?("
                  + _NUM + r")\s*%", q)
    mp = re.search(r"(?:" + _RS + r")\s*(" + _NUM + r")", q) or \
        re.search(r"(?:costs?|price|worth|amount)\s+(?:is\s+)?"
                  r"(?:rs\.?\s*)?(" + _NUM + r")", q)
    if not (mp and mr):
        return None
    price, rate = _num(mp.group(1)), _num(mr.group(1))
    if price == rate:
        # The "price" found is just the rate restated; look for
        # any other number to serve as the price.
        others = [_num(v) for v in re.findall(_NUM, q)
                  if _num(v) != rate]
        if not others:
            return None
        price = others[0]
    if price <= 0 or not (0 < rate < 100):
        return None
    gst_amt = price * rate / 100.0
    total = price + gst_amt
    steps = [
        f"Price = Rs {fmt_num(price)}, GST rate = "
        f"{fmt_num(rate)}%",
        f"GST amount = {fmt_num(rate)}% of {fmt_num(price)} = "
        f"Rs {fmt_num(gst_amt)}",
        f"Total amount to be paid = {fmt_num(price)} + "
        f"{fmt_num(gst_amt)} = Rs {fmt_num(total)}",
    ]
    return {"type": "applied", "op": "gst",
            "answer": f"GST Rs {fmt_num(gst_amt)}, total "
                      f"Rs {fmt_num(total)}",
            "steps": steps, "value": total}


def _successive_discount(q):
    if "successive" not in q or "discount" not in q:
        return None
    pcts = [float(v) for v in re.findall(
        r"(" + _NUM + r")\s*%\s*(?:discount)?", q)
        if 0 < float(v) < 100]
    ds = re.findall(r"(" + _NUM + r")\s*%", q)
    if len(ds) < 2:
        return None
    d1, d2 = float(ds[0]), float(ds[1])
    if not (0 < d1 < 100 and 0 < d2 < 100):
        return None
    equiv = d1 + d2 - d1 * d2 / 100.0
    if "equivalent" in q or "single discount" in q:
        steps = [
            "A single discount equivalent to two successive "
            "discounts of a% and b% is a + b - ab/100.",
            f"= {fmt_num(d1)} + {fmt_num(d2)} - "
            f"({fmt_num(d1)} × {fmt_num(d2)})/100 "
            f"= {fmt_num(equiv)}%",
        ]
        return {"type": "applied", "op": "successive_discount_equiv",
                "answer": f"{fmt_num(equiv)}%", "steps": steps,
                "value": equiv}
    mm = re.search(r"marked\s+(?:price\s+)?(?:is\s+|at\s+)?(?:"
                   + _RS + r"\s*)?(" + _NUM + r")", q) or \
        re.search(r"(?:" + _RS + r"\s*)?(" + _NUM + r")", q)
    if not mm:
        return None
    M = _num(mm.group(1))
    after1 = M * (1 - d1 / 100.0)
    sp_ = after1 * (1 - d2 / 100.0)
    steps = [
        f"Marked price = Rs {fmt_num(M)}",
        f"After the first discount of {fmt_num(d1)}%: "
        f"{fmt_num(M)} × (1 - {fmt_num(d1)}/100) = "
        f"Rs {fmt_num(after1)}",
        f"After the second discount of {fmt_num(d2)}%: "
        f"{fmt_num(after1)} × (1 - {fmt_num(d2)}/100) = "
        f"Rs {fmt_num(sp_)}",
        f"(The two discounts together equal a single discount "
        f"of {fmt_num(equiv)}%.)",
    ]
    return {"type": "applied", "op": "successive_discount",
            "answer": f"Rs {fmt_num(sp_)}", "steps": steps,
            "value": sp_}


def _two_articles_same_sp(q):
    m = re.search(r"two\s+(?:articles|items|watches|shirts|"
                  r"objects)[^.]{0,40}?(?:" + _RS + r"\s*)?("
                  + _NUM + r")\s+each", q)
    if not m:
        return None
    mg = re.search(r"(?:gain|profit)(?:s|ed)?\s*(?:of\s*)?("
                   + _NUM + r")\s*%", q)
    ml = re.search(r"(?:loss|loses|lost)(?:\s*of)?\s*(" + _NUM
                   + r")\s*%", q)
    if not (mg and ml):
        return None
    sp_each = sp.Rational(m.group(1))
    g, l = sp.Rational(mg.group(1)), sp.Rational(ml.group(1))
    if sp_each <= 0 or g <= 0 or l >= 100:
        return None
    cp1 = sp_each / (1 + g / 100)
    cp2 = sp_each / (1 - l / 100)
    cp_total = cp1 + cp2
    sp_total = 2 * sp_each
    diff = sp_total - cp_total
    pct = diff / cp_total * 100
    steps = [
        f"Selling price of each article = Rs "
        f"{fmt_num(sp_each)}",
        f"CP of the first = SP / (1 + gain%) = "
        f"{fmt_num(sp_each)} / (1 + {fmt_num(g)}/100) = "
        f"Rs {fmt_num(cp1)}",
        f"CP of the second = SP / (1 - loss%) = "
        f"{fmt_num(sp_each)} / (1 - {fmt_num(l)}/100) = "
        f"Rs {fmt_num(cp2)}",
        f"Total CP = Rs {fmt_num(cp_total)}, total SP = "
        f"Rs {fmt_num(sp_total)}",
    ]
    if diff > 0:
        steps.append(f"SP is more than CP, so there is a gain "
                     f"of {fmt_num(pct)}%.")
        ans = f"Gain of {fmt_num(pct)}%"
    elif diff < 0:
        steps.append(f"CP is more than SP, so there is a loss "
                     f"of {fmt_num(-pct)}%.")
        ans = f"Loss of {fmt_num(-pct)}%"
    else:
        steps.append("Total SP equals total CP: no gain, "
                     "no loss.")
        ans = "No gain, no loss (0%)"
    return {"type": "applied", "op": "two_articles_same_sp",
            "answer": ans, "steps": steps, "value": float(pct)}


def _quad_coeffs(text):
    """Parse a quadratic text -> (a, b, c, var) with sympy
    expressions (coefficients may involve one parameter), or
    None. Shared by the Wave 32 quadratic families."""
    text = text.strip().rstrip(".?")
    text = re.sub(r"^(?:the\s+)?(?:quadratic\s+)?(?:equation|polynomial)\s+",
                  "", text)
    text = re.sub(r"=\s*0\s*$", "", text)
    if "=" in text:
        left, right = text.split("=", 1)
        text = f"({left}) - ({right})"
    try:
        expr = sp.expand(parse_expression(text))
        symbols = sorted(expr.free_symbols, key=lambda s: s.name)
        if not (1 <= len(symbols) <= 2):
            return None
        var = None
        for s in symbols:
            if s.name == "x":
                var = s
        if var is None:
            var = symbols[0]
        poly = sp.Poly(expr, var)
        if poly is None or poly.degree() != 2:
            return None
        coeffs = poly.all_coeffs()
        return coeffs[0], coeffs[1], coeffs[2], var
    except Exception:
        return None


def _eq_text_after_of(q):
    """The equation text after '... of (the) (equation) ...'.
    The first 'of' in "sum of roots of the equation 3x^2..." is
    NOT the equation's own 'of', so strip any leading filler
    words (roots / of / the / equation) from the capture."""
    m = re.search(r"\bof\s+(.+)$", q)
    if not m:
        return None
    text = m.group(1)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"^(?:the\s+|roots\s+|of\s+|equation\s+|"
                      r"quadratic\s+|polynomial\s+|zeroes\s+|zeros\s+)", "", text)
    return text


def _find_k_equal_roots(q):
    if "equal roots" not in q:
        return None
    m = re.search(r"(?:equation\s+)?(.+?)\s+has\s+(?:two\s+)?"
                  r"equal\s+roots", q)
    if not m:
        return None
    text = re.sub(r"^(?:for\s+which|which)\s+", "", m.group(1))
    text = re.sub(r"^.*?equation\s+", "", text)
    got = _quad_coeffs(text)
    if not got:
        return None
    a, b, c, var = got
    params = (a.free_symbols | b.free_symbols | c.free_symbols) \
        - {var}
    if len(params) != 1:
        return None
    param = list(params)[0]
    D = sp.expand(b ** 2 - 4 * a * c)
    sols = sp.solve(D, param)
    if not sols:
        return None
    steps = [
        f"For {fmt(sp.expand(a * var ** 2 + b * var + c))} = 0: "
        f"a = {fmt(a)}, b = {fmt(b)}, c = {fmt(c)}",
        f"Discriminant D = b^2 - 4ac = {fmt(D)}",
        "Equal roots need D = 0.",
        f"Solving {fmt(D)} = 0 gives {param} = "
        + ", ".join(fmt(s) for s in sols),
    ]
    return {"type": "algebra", "op": "find_k_equal_roots",
            "answer": ", ".join(f"{param} = {fmt(s)}"
                                for s in sols),
            "steps": steps}


def _sum_product_roots(q):
    if not re.search(r"\b(sum|product)\b[^.]{0,30}?"
                     r"\b(roots|zeroes|zeros)\b", q):
        return None
    text = _eq_text_after_of(q)
    if text is None:
        return None
    got = _quad_coeffs(text)
    if not got:
        return None
    a, b, c, var = got
    if (a.free_symbols | b.free_symbols | c.free_symbols) - {var}:
        return None
    if a == 0:
        return None
    s = sp.simplify(-b / a)
    p = sp.simplify(c / a)
    want_sum = "sum" in q
    want_prod = "product" in q
    steps = [
        f"Standard form: a = {fmt(a)}, b = {fmt(b)}, "
        f"c = {fmt(c)}",
        "For ax^2 + bx + c = 0: sum of roots = -b/a, product "
        "of roots = c/a.",
    ]
    parts = []
    if want_sum:
        steps.append(f"Sum of roots = -({fmt(b)})/{fmt(a)} "
                     f"= {fmt(s)}")
        parts.append(f"Sum = {fmt(s)}")
    if want_prod:
        steps.append(f"Product of roots = {fmt(c)}/{fmt(a)} "
                     f"= {fmt(p)}")
        parts.append(f"Product = {fmt(p)}")
    if not parts:
        return None
    return {"type": "algebra", "op": "sum_product_roots",
            "answer": ", ".join(parts), "steps": steps}


_COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4,
                "five": 5, "a": 1, "an": 1}


def _insert_means(q):
    m = re.search(
        r"insert\s+(?:(\d+|one|two|three|four|five|a|an)\s+)?"
        r"(arithmetic|geometric)\s+means?\s+between\s+"
        r"(-?" + _NUM + r")\s+and\s+(-?" + _NUM + r")", q)
    if not m:
        return None
    n = _COUNT_WORDS.get(m.group(1), None) if m.group(1) else 1
    if m.group(1) and m.group(1).isdigit():
        n = int(m.group(1))
    if n is None or n < 1 or n > 10:
        return None
    kind = m.group(2)
    A, B = sp.Rational(m.group(3)), sp.Rational(m.group(4))
    if kind == "arithmetic":
        d = (B - A) / (n + 1)
        means = [A + i * d for i in range(1, n + 1)]
        steps = [
            f"Inserting {n} arithmetic mean(s) between "
            f"{fmt(A)} and {fmt(B)} makes an AP of {n + 2} "
            f"terms.",
            f"Common difference d = (B - A)/(n + 1) = "
            f"({fmt(B)} - {fmt(A)})/{n + 1} = {fmt(d)}",
            "The means are "
            + ", ".join(fmt(v) for v in means) + ".",
        ]
        return {"type": "sequences", "op": "insert_arithmetic_means",
                "answer": ", ".join(fmt(v) for v in means),
                "steps": steps}
    # Geometric means: r = (B/A)^(1/(n+1)).
    if A == 0 or B == 0 or (A < 0) != (B < 0):
        return None
    ratio = sp.simplify((B / A) ** sp.Rational(1, n + 1))
    if ratio.has(sp.Pow) and not ratio.is_number:
        return None
    try:
        ratio_f = float(ratio)
    except Exception:
        return None
    if abs(ratio_f) == float("inf"):
        return None
    means = [sp.simplify(A * ratio ** i) for i in range(1, n + 1)]
    steps = [
        f"Inserting {n} geometric mean(s) between {fmt(A)} "
        f"and {fmt(B)} makes a GP of {n + 2} terms.",
        f"Common ratio r = (B/A)^(1/(n+1)) = "
        f"({fmt(B)}/{fmt(A)})^(1/{n + 1}) = {fmt(ratio)}",
        "The means are " + ", ".join(fmt(v) for v in means)
        + ".",
    ]
    return {"type": "sequences", "op": "insert_geometric_means",
            "answer": ", ".join(fmt(v) for v in means),
            "steps": steps}


def _identity_eval(q):
    m = re.search(r"a\s*\+\s*b\s*=\s*(" + _NUM + r")\s*(?:,|and)"
                  r"\s*(?:ab|a\s*b)\s*=\s*(" + _NUM + r")", q)
    if not m:
        return None
    S, P = sp.Rational(m.group(1)), sp.Rational(m.group(2))
    if re.search(r"a\s*(?:\^|\*\*)\s*3\s*\+\s*b\s*(?:\^|\*\*)"
                 r"\s*3", q) or "a^3 + b^3" in q or \
            "a³ + b³" in q:
        val = S ** 3 - 3 * P * S
        steps = [
            f"Given a + b = {fmt(S)} and ab = {fmt(P)}.",
            "Identity: a^3 + b^3 = (a + b)^3 - 3ab(a + b)",
            f"= {fmt(S)}^3 - 3 × {fmt(P)} × {fmt(S)} "
            f"= {fmt(val)}",
        ]
        return {"type": "algebra", "op": "identity_a3_b3",
                "answer": fmt(val), "steps": steps,
                "value": float(val)}
    if re.search(r"a\s*(?:\^|\*\*)\s*2\s*\+\s*b\s*(?:\^|\*\*)"
                 r"\s*2", q) or "a^2 + b^2" in q or \
            "a² + b²" in q:
        val = S ** 2 - 2 * P
        steps = [
            f"Given a + b = {fmt(S)} and ab = {fmt(P)}.",
            "Identity: a^2 + b^2 = (a + b)^2 - 2ab",
            f"= {fmt(S)}^2 - 2 × {fmt(P)} = {fmt(val)}",
        ]
        return {"type": "algebra", "op": "identity_a2_b2",
                "answer": fmt(val), "steps": steps,
                "value": float(val)}
    return None


def _frac_str(fr):
    from fractions import Fraction as _F
    fr = _F(fr).limit_denominator(10000)
    return str(fr.numerator) if fr.denominator == 1 else \
        f"{fr.numerator}/{fr.denominator}"


def _pipes(q):
    if "tank" not in q:
        return None
    fills = [float(v) for v in re.findall(
        r"fill(?:s|ing)?\s+(?:a\s+tank|the\s+tank|it|"
        r"the\s+container)\s+in\s+(" + _NUM + r")\s*hours?", q)]
    empties = [float(v) for v in re.findall(
        r"empt(?:y|ies|ying)\s+(?:a\s+tank|the\s+tank|it|"
        r"the\s+container)?\s*in\s+(" + _NUM + r")\s*hours?", q)]
    if not fills and not empties:
        return None
    if empties and not fills:
        return None
    from fractions import Fraction as F
    rate = sum(F(1, 1) / F(str(t)) for t in fills) \
        - sum(F(1, 1) / F(str(t)) for t in empties)
    steps = []
    for t in fills:
        steps.append(f"A pipe that fills the tank in "
                     f"{fmt_num(t)} hours fills 1/{fmt_num(t)} "
                     f"of the tank in 1 hour.")
    for t in empties:
        steps.append(f"A pipe that empties the tank in "
                     f"{fmt_num(t)} hours empties 1/{fmt_num(t)} "
                     f"of the tank in 1 hour.")
    if rate <= 0:
        steps.append("The emptying rate is not less than the "
                     "filling rate, so the tank will never fill.")
        return {"type": "applied", "op": "pipes",
                "answer": "The tank will never fill",
                "steps": steps}
    total = 1 / rate
    steps.append(f"Net rate together = {_frac_str(rate)} of "
                 f"the tank per hour.")
    steps.append(f"Time to fill = 1 / ({_frac_str(rate)}) = "
                 f"{_frac_str(total)} hours"
                 + (f" ≈ {float(total):.2f} hours"
                    if total.denominator != 1 else ""))
    return {"type": "applied", "op": "pipes",
            "answer": f"{_frac_str(total)} hours",
            "steps": steps, "value": float(total)}


def _work_together(q):
    if "work" not in q or "together" not in q:
        return None
    if "efficient" in q:
        return None  # the efficiency family owns that story
    days = [float(v) for v in re.findall(
        r"in\s+(" + _NUM + r")\s+days", q)]
    if len(days) != 2:
        return None
    from fractions import Fraction as F
    t1, t2 = days
    total = F(str(t1)) * F(str(t2)) / (F(str(t1)) + F(str(t2)))
    steps = [
        f"One worker finishes the work in {fmt_num(t1)} days, "
        f"so does 1/{fmt_num(t1)} of it in a day; the other "
        f"does 1/{fmt_num(t2)} in a day.",
        f"Together in 1 day: 1/{fmt_num(t1)} + "
        f"1/{fmt_num(t2)} = {_frac_str(1 / total)} of the "
        f"work.",
        f"Days needed together = {_frac_str(total)} days"
        + (f" ≈ {float(total):.2f} days"
           if total.denominator != 1 else ""),
    ]
    return {"type": "applied", "op": "work_together",
            "answer": f"{_frac_str(total)} days",
            "steps": steps, "value": float(total)}


_EFF_WORDS = {"twice": 2, "thrice": 3, "double": 2}


def _work_efficiency(q):
    if "efficient" not in q or "together" not in q:
        return None
    m = re.search(r"(\w+)\s+is\s+(twice|thrice|double|"
                  r"(" + _NUM + r")\s+times)\s+as\s+efficient"
                  r"\s+as\s+(\w+)", q)
    mt = re.search(r"together[^.]{0,60}?in\s+(" + _NUM
                   + r")\s+days", q)
    if not (m and mt):
        return None
    first, second = m.group(1), m.group(4)
    e = _EFF_WORDS.get(m.group(2))
    if e is None:
        e = float(m.group(3))
    T = float(mt.group(1))
    from fractions import Fraction as F
    eF, TF = F(str(e)), F(str(T))
    t_first = TF * (eF + 1) / eF
    t_second = TF * (eF + 1)
    ask_second = re.search(
        rf"\b{re.escape(second)}\s+alone\b", q) is not None
    pick, who = (t_second, second) if ask_second else \
        (t_first, first)
    steps = [
        f"Efficiency ratio: {first} : {second} = "
        f"{fmt_num(e)} : 1, so in 1 day they do "
        f"{fmt_num(e)} + 1 = {fmt_num(e + 1)} units of work "
        f"(taking {second}'s rate as 1 unit/day).",
        f"Together they take {fmt_num(T)} days, so the whole "
        f"work is {fmt_num(e + 1)} × {fmt_num(T)} = "
        f"{fmt_num((e + 1) * T)} units.",
        f"{who.capitalize()} alone does "
        f"{fmt_num(e) if not ask_second else 1} unit/day, so "
        f"needs {fmt_num((e + 1) * T)} / "
        f"{fmt_num(e) if not ask_second else 1} = "
        f"{_frac_str(pick)} days.",
    ]
    return {"type": "applied", "op": "work_efficiency",
            "answer": f"{_frac_str(pick)} days",
            "steps": steps, "value": float(pick)}


def _boat_stream(q):
    md = re.search(r"(" + _NUM + r")\s*km\s+downstream\s+in\s+"
                   r"(" + _NUM + r")\s*hours?", q)
    mu = re.search(r"(" + _NUM + r")\s*km\s+upstream\s+in\s+"
                   r"(" + _NUM + r")\s*hours?", q)
    if not (md and mu):
        return None
    d1, t1 = float(md.group(1)), float(md.group(2))
    d2, t2 = float(mu.group(1)), float(mu.group(2))
    if t1 == 0 or t2 == 0:
        return None
    down, up = d1 / t1, d2 / t2
    boat = (down + up) / 2
    stream = (down - up) / 2
    if stream < 0:
        return None
    steps = [
        f"Downstream speed = {fmt_num(d1)} / {fmt_num(t1)} "
        f"= {fmt_num(down)} km/h (boat + stream)",
        f"Upstream speed = {fmt_num(d2)} / {fmt_num(t2)} "
        f"= {fmt_num(up)} km/h (boat - stream)",
        f"Speed of the boat in still water = ({fmt_num(down)}"
        f" + {fmt_num(up)}) / 2 = {fmt_num(boat)} km/h",
        f"Speed of the stream = ({fmt_num(down)} - "
        f"{fmt_num(up)}) / 2 = {fmt_num(stream)} km/h",
    ]
    return {"type": "applied", "op": "boat_stream",
            "answer": f"Boat {fmt_num(boat)} km/h, stream "
                      f"{fmt_num(stream)} km/h",
            "steps": steps, "value": boat}


def _two_trains(q):
    if "two trains" not in q and "two train" not in q:
        return None
    ml = re.search(r"lengths?\s+(?:of\s+)?(" + _NUM + r")\s*m"
                   r"(?:etres?)?\s+and\s+(" + _NUM + r")\s*m", q)
    ms = re.search(r"(" + _NUM + r")\s*km/h\s+and\s+(" + _NUM
                   + r")\s*km/h", q)
    if not (ml and ms):
        return None
    L1, L2 = float(ml.group(1)), float(ml.group(2))
    s1, s2 = float(ms.group(1)), float(ms.group(2))
    if "opposite" in q:
        rel = s1 + s2
        rel_note = (f"opposite directions, so the relative "
                    f"speed is {fmt_num(s1)} + {fmt_num(s2)} "
                    f"= {fmt_num(rel)} km/h")
    elif "same direction" in q:
        rel = abs(s1 - s2)
        if rel == 0:
            return None
        rel_note = (f"same direction, so the relative speed "
                    f"is |{fmt_num(s1)} - {fmt_num(s2)}| = "
                    f"{fmt_num(rel)} km/h")
    else:
        return None
    dist = L1 + L2
    secs = dist / (rel * 5 / 18)
    steps = [
        f"To cross each other the trains must cover "
        f"{fmt_num(L1)} + {fmt_num(L2)} = {fmt_num(dist)} m.",
        f"They run in {rel_note}.",
        f"In m/s: {fmt_num(rel)} × 5/18 = "
        f"{fmt_num(rel * 5 / 18)} m/s",
        f"Time = {fmt_num(dist)} / {fmt_num(rel * 5 / 18)} "
        f"= {fmt_num(secs)} seconds",
    ]
    return {"type": "applied", "op": "two_trains_crossing",
            "answer": f"{fmt_num(secs)} seconds",
            "steps": steps, "value": secs}


_COLOURS = ("red", "black", "white", "green", "blue", "yellow")


def _parse_bag(segment):
    counts = {}
    for colour in _COLOURS:
        m = re.search(r"(" + _NUM + r")\s+" + colour, segment)
        if m:
            counts[colour] = float(m.group(1))
    return counts


def _bayes_bags(q):
    from fractions import Fraction as F
    if "bag" not in q:
        return None
    parts = re.split(r"\bbag\s+", q)
    bags = []
    for part in parts[1:]:
        name_m = re.match(r"(\w+)\b", part)
        if not name_m:
            continue
        counts = _parse_bag(part)
        if counts:
            bags.append((name_m.group(1), counts))
    if len(bags) < 2:
        return None
    colour = None
    mc = re.search(r"(?:found to be|drawn is|comes out|is)\s+"
                   r"(" + "|".join(_COLOURS) + r")\b", q)
    if mc:
        colour = mc.group(1)
    if colour is None:
        return None
    target = None
    mt = re.search(r"drawn from bag\s+(\w+)", q) or \
        re.search(r"from bag\s+(\w+)\s*\?\s*$", q.strip())
    if mt:
        target = mt.group(1)
    if target is None:
        target = bags[0][0]
    weights = []
    for name, counts in bags:
        total = sum(counts.values())
        if total == 0 or colour not in counts:
            return None
        weights.append((name, F(str(counts[colour]))
                        / F(str(total))))
    denom = sum(w for _, w in weights)
    if denom == 0:
        return None
    post = dict((name, w / denom) for name, w in weights)
    if target not in post:
        return None
    steps = [
        "By Bayes' theorem, with each bag equally likely to "
        "be chosen:",
    ]
    for name, counts in bags:
        total = sum(counts.values())
        steps.append(
            f"P({colour} | bag {name}) = "
            f"{fmt_num(counts[colour])}/{fmt_num(total)}")
    steps.append(
        f"P(bag {target} | {colour}) = P({colour} | bag "
        f"{target}) / (sum over all bags) = "
        f"{_frac_str(post[target])} ≈ "
        f"{float(post[target]):.4f}")
    return {"type": "statistics", "op": "bayes_bags",
            "answer": f"{_frac_str(post[target])} ≈ "
                      f"{float(post[target]):.4f}",
            "steps": steps, "value": float(post[target])}


def _prob_value(tok):
    tok = tok.strip()
    if tok.endswith("%"):
        return float(tok[:-1]) / 100.0
    return float(tok)


def _bayes_medical(q):
    from fractions import Fraction as F
    if not re.search(r"disease|infection|condition", q):
        return None
    mp = re.search(r"(" + _NUM + r")\s*%\s*of\s+(?:the\s+)?"
                   r"(?:people|population|persons)", q)
    ms = re.search(r"(?:detects?|sensitivity|true positive)"
                   r"[^.]{0,70}?(?:probability\s+)?(0\.\d+|"
                   + _NUM + r"\s*%)", q)
    mf = re.search(r"false positive[^.]{0,70}?(?:probability"
                   r"\s+)?(0\.\d+|" + _NUM + r"\s*%)", q)
    if not (mp and ms and mf):
        return None
    prev = float(mp.group(1)) / 100.0
    sens = _prob_value(ms.group(1))
    fpr = _prob_value(mf.group(1))
    if not (0 < prev < 1 and 0 < sens <= 1 and 0 <= fpr < 1):
        return None
    num = sens * prev
    den = num + fpr * (1 - prev)
    post = F(str(num)) / F(str(den)) if den else None
    if post is None:
        return None
    steps = [
        f"Out of 100 people: {fmt_num(prev * 100)} have the "
        f"disease and the test catches "
        f"{fmt_num(sens * 100)}% of them, so true positives "
        f"= {fmt_num(num * 100)}.",
        f"The other {fmt_num((1 - prev) * 100)} do not have "
        f"it, but {fmt_num(fpr * 100)}% of them still test "
        f"positive: false positives = "
        f"{fmt_num(fpr * (1 - prev) * 100)}.",
        f"P(disease | positive) = {fmt_num(num * 100)} / "
        f"({fmt_num(num * 100)} + "
        f"{fmt_num(fpr * (1 - prev) * 100)}) = "
        f"{_frac_str(post)} ≈ {float(post) * 100:.2f}%",
    ]
    return {"type": "statistics", "op": "bayes_medical",
            "answer": f"{_frac_str(post)} ≈ "
                      f"{float(post) * 100:.2f}%",
            "steps": steps, "value": float(post)}


def _bayes_factory(q):
    from fractions import Fraction as F
    if "machine" not in q or "defective" not in q:
        return None
    pairs = re.findall(
        r"machine\s+(\w+)\s+produces\s+(" + _NUM + r")\s*%"
        r"[^.]{0,50}?(" + _NUM + r")\s*%\s*(?:defective|"
        r"defects|faulty)", q)
    if len(pairs) < 2:
        return None
    target = None
    mt = re.search(r"came from machine\s+(\w+)", q) or \
        re.search(r"from machine\s+(\w+)\s*\?\s*$", q.strip())
    if mt:
        target = mt.group(1)
    weights = []
    for name, share, defect in pairs:
        weights.append((name, F(str(float(share) / 100))
                        * F(str(float(defect) / 100))))
    if target is None:
        target = weights[0][0]
    denom = sum(w for _, w in weights)
    if denom == 0:
        return None
    post = dict((name, w / denom) for name, w in weights)
    if target not in post:
        return None
    steps = ["By Bayes' theorem:"]
    for (name, share, defect), (_, w) in zip(pairs, weights):
        steps.append(
            f"P(defective and machine {name}) = "
            f"{share}% × {defect}% = {float(w) * 100:.2f}% of "
            f"all items")
    steps.append(
        f"P(machine {target} | defective) = "
        f"{_frac_str(post[target])} ≈ "
        f"{float(post[target]):.4f}")
    return {"type": "statistics", "op": "bayes_factory",
            "answer": f"{_frac_str(post[target])} ≈ "
                      f"{float(post[target]):.4f}",
            "steps": steps, "value": float(post[target])}


def _lp_corners(q):
    if "corner point" not in q:
        return None
    mo = re.search(r"\bz\s*=\s*(.+?)(?:\s+subject|\s+at\s+"
                   r"(?:the\s+)?corner|,|\.$|$)", q)
    if not mo:
        return None
    pts = [(float(a), float(b)) for a, b in re.findall(
        r"\(\s*(-?" + _NUM + r")\s*,\s*(-?" + _NUM + r")\s*\)",
        q)]
    if len(pts) < 2:
        return None
    try:
        expr = parse_expression(mo.group(1))
        syms = expr.free_symbols
        if len(syms) > 2:
            return None
        xs = [s for s in syms if s.name == "x"]
        ys = [s for s in syms if s.name == "y"]
        x = xs[0] if xs else sp.Symbol("x")
        y = ys[0] if ys else sp.Symbol("y")
    except Exception:
        return None
    vals = []
    steps = [f"Evaluate Z = {fmt(expr)} at each corner point:"]
    for (px, py) in pts:
        v = sp.nsimplify(expr.subs({x: sp.Rational(str(px)),
                                    y: sp.Rational(str(py))}))
        vals.append((v, (px, py)))
        steps.append(f"At ({fmt_num(px)}, {fmt_num(py)}): "
                     f"Z = {fmt(v)}")
    if "minim" in q:
        best_v, best_p = min(vals, key=lambda t: float(t[0]))
        word, op = "Minimum", "lp_minimise"
    else:
        best_v, best_p = max(vals, key=lambda t: float(t[0]))
        word, op = "Maximum", "lp_maximise"
    steps.append(f"{word} value of Z is {fmt(best_v)} at "
                 f"({fmt_num(best_p[0])}, {fmt_num(best_p[1])}).")
    return {"type": "applied", "op": op,
            "answer": f"{word} Z = {fmt(best_v)} at "
                      f"({fmt_num(best_p[0])}, "
                      f"{fmt_num(best_p[1])})",
            "steps": steps, "value": float(best_v)}


_FAMILIES = (_ratio, _unitary_cost, _simple_interest, _profit_loss,
             _gst, _successive_discount, _two_articles_same_sp,
             _speed, _word_equation, _quadratic_info,
             _find_k_equal_roots, _sum_product_roots,
             _identity_eval, _insert_means,
             _speed_time_quadratic, _sum_difference, _ages,
             _consecutive_product, _rectangle_word,
             _compound_interest_freq, _compound_interest,
             _discount, _percent_score,
             _profit_loss_forms, _ratio_share_ask,
             _inverse_proportion, _bells_lcm, _train_crossing,
             _digits,
             _lp_corners, _bayes_bags, _bayes_medical,
             _bayes_factory, _pipes, _work_together,
             _work_efficiency, _boat_stream, _two_trains)


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
