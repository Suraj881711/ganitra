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
from .pi_policy import pi_choice, pi_note, pi_note_hi

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
    # Wave 52 (echo case #32): "Divide Rs 900 among A, B and C in
    # the ratio 2:3:4. How much does C get?" missed this branch
    # (the "among ..." segment sits between the amount and "in
    # the ratio") and fell to the simplify-a-ratio fallback,
    # which echoed "2 : 3" back as the answer. The among-segment
    # is now allowed, its names are read, and a "how much does
    # X get" ask answers with X's share alone.
    m = re.search(
        r"\bdivide\s+(?:" + _RS + r"\s*)?(" + _NUM + r")"
        r"\s*(?:" + _RS + r")?\s+"
        r"(?:among\s+([^.]+?)\s+)?in\s+"
        r"(?:the\s+)?ratio\s+(\d+)\s*:\s*(\d+)(?:\s*:\s*(\d+))?", q)
    if m:
        total = _num(m.group(1))
        parts = [int(m.group(3)), int(m.group(4))]
        if m.group(5):
            parts.append(int(m.group(5)))
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
        if m.group(2):
            names = [w.strip() for w in
                     re.split(r",|\band\b", m.group(2)) if w.strip()]
            mq = re.search(r"how\s+much\s+does\s+([a-z]+)\s+get", q)
            if mq and len(names) == len(parts):
                who = mq.group(1).lower()
                for nm, v in zip(names, vals):
                    if nm.lower() == who:
                        disp = nm.upper() if len(nm) == 1 \
                            else nm.capitalize()
                        steps.append(
                            f"So {disp} gets "
                            f"{('Rs ' if money else '')}"
                            f"{fmt_num(v)}.")
                        return {"type": "applied",
                                "op": "ratio_divide",
                                "answer": ("Rs " if money else "")
                                + fmt_num(v),
                                "steps": steps, "value": v}
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
    # Wave 65: AGES in a ratio with a given sum — "the ages
    # of a and b are in ratio 4:7 and sum to 55. age of b?"
    # (the numbers pattern above needs the word "numbers";
    # the simplify catch-all echoed "4 : 7" for this form).
    m = re.search(
        r"\bages?\b[^.]{0,40}?in\s+(?:the\s+)?ratio\s+"
        r"(\d+)\s*:\s*(\d+)\s+and\s+(?:their\s+)?sum\s+"
        r"(?:is|to)\s+(" + _NUM + r")", q)
    if m:
        a, b, total = int(m.group(1)), int(m.group(2)), \
            _num(m.group(3))
        per = total / (a + b)
        first, second = a * per, b * per
        steps = [
            f"The ages are {a} parts and {b} parts: "
            f"{a} + {b} = {a + b} parts = {fmt_num(total)}",
            f"1 part = {fmt_num(total)} ÷ {a + b} = "
            f"{fmt_num(per)}",
            f"First age = {a} × {fmt_num(per)} = "
            f"{fmt_num(first)}",
            f"Second age = {b} × {fmt_num(per)} = "
            f"{fmt_num(second)}",
        ]
        if re.search(r"age\s+of\s+b\b", q):
            return {"type": "applied", "op": "ages_ratio_sum",
                    "answer": fmt_num(second), "steps": steps,
                    "value": second}
        if re.search(r"age\s+of\s+a\b", q):
            return {"type": "applied", "op": "ages_ratio_sum",
                    "answer": fmt_num(first), "steps": steps,
                    "value": first}
        return {"type": "applied", "op": "ages_ratio_sum",
                "answer": f"{fmt_num(first)} and "
                          f"{fmt_num(second)}",
                "steps": steps, "value": [first, second]}
    # Wave 65: SIDES of a triangle in a ratio with a given
    # perimeter — the PERIMETER is split in the ratio (the
    # angles branch below used to steal these via the
    # "triANGLE" substring trap). Longest / shortest side
    # asks answer with that side alone.
    if "triangle" in q and "side" in q and "perimeter" in q:
        mt = re.search(r"ratio\s+(\d+)\s*:\s*(\d+)\s*:\s*(\d+)",
                       q)
        mp = re.search(r"perimeter\s+(?:is\s+|of\s+)?("
                       + _NUM + r")", q)
        if mt and mp:
            parts = [int(mt.group(i)) for i in (1, 2, 3)]
            s = sum(parts)
            per = _num(mp.group(1))
            sides = [per * p / s for p in parts]
            steps = [
                f"The sides are {parts[0]} parts, {parts[1]} "
                f"parts and {parts[2]} parts: "
                f"{' + '.join(str(p) for p in parts)} = {s} "
                f"parts = {fmt_num(per)} (the perimeter).",
                f"Value of 1 part = {fmt_num(per)} ÷ {s} = "
                f"{fmt_num(per / s)}",
            ]
            for p, sd in zip(parts, sides):
                steps.append(f"{p} parts = {p} × "
                             f"{fmt_num(per / s)} = "
                             f"{fmt_num(sd)}")
            if "longest" in q or "largest" in q \
                    or "greatest" in q:
                big = max(sides)
                steps.append(f"The longest side is "
                             f"{fmt_num(big)}.")
                return {"type": "applied",
                        "op": "triangle_sides_ratio",
                        "answer": fmt_num(big), "steps": steps,
                        "value": big}
            if "shortest" in q or "smallest" in q:
                small = min(sides)
                steps.append(f"The shortest side is "
                             f"{fmt_num(small)}.")
                return {"type": "applied",
                        "op": "triangle_sides_ratio",
                        "answer": fmt_num(small), "steps": steps,
                        "value": small}
            return {"type": "applied",
                    "op": "triangle_sides_ratio",
                    "answer": ", ".join(fmt_num(sd)
                                        for sd in sides),
                    "steps": steps, "value": sides}
    # Wave 52 (echo case #349): "The angles of a triangle are
    # in the ratio 2:3:4. Find the largest angle." fell to the
    # simplify fallback below and echoed "2 : 3". The angles
    # are 180° split in the ratio.
    # Wave 65: the guard used to be `"angle" in q` — but
    # "angle" is a substring of "triANGLE" (and "rectANGLE"),
    # so SIDES-in-ratio questions were hijacked into this
    # angles split. Word-boundary match now.
    if "triangle" in q and re.search(r"\bangles?\b", q):
        mt = re.search(r"ratio\s+(\d+)\s*:\s*(\d+)\s*:\s*(\d+)", q)
        if mt:
            parts = [int(mt.group(i)) for i in (1, 2, 3)]
            s = sum(parts)
            angles = [180.0 * p / s for p in parts]
            steps = [
                f"The three angles are {parts[0]} parts, "
                f"{parts[1]} parts and {parts[2]} parts: "
                f"{' + '.join(str(p) for p in parts)} = {s} "
                f"parts = 180° (angles of a triangle).",
                f"Value of 1 part = 180 ÷ {s} = "
                f"{fmt_num(180.0 / s)}°",
            ]
            for p, a in zip(parts, angles):
                steps.append(f"{p} parts = {p} × "
                             f"{fmt_num(180.0 / s)} = "
                             f"{fmt_num(a)}°")
            if "largest" in q or "greatest" in q \
                    or "biggest" in q:
                big = max(angles)
                steps.append(f"The largest angle is "
                             f"{fmt_num(big)}°.")
                return {"type": "applied",
                        "op": "triangle_angles_ratio",
                        "answer": f"{fmt_num(big)}°",
                        "steps": steps, "value": big}
            if "smallest" in q:
                small = min(angles)
                steps.append(f"The smallest angle is "
                             f"{fmt_num(small)}°.")
                return {"type": "applied",
                        "op": "triangle_angles_ratio",
                        "answer": f"{fmt_num(small)}°",
                        "steps": steps, "value": small}
            return {"type": "applied",
                    "op": "triangle_angles_ratio",
                    "answer": ", ".join(f"{fmt_num(a)}°"
                                        for a in angles),
                    "steps": steps, "value": angles}
    # Wave 56: divide an amount AMONG NAMED people in a
    # ratio — "Divide Rs 900 among A, B and C in the ratio
    # 2:3:4. How much does C get?" The first pattern above
    # needs "in the ratio" right after the amount, so the
    # names in between broke it, and the simplify catch-all
    # below echoed "2: 3" (the first two parts) as the
    # answer. Any number of names / parts; the ask may name
    # one share or want them all.
    m = re.search(
        r"\bdivide\s+(?:" + _RS + r"\s*)?(" + _NUM + r")\s+"
        r"among\s+(.+?)\s+in\s+(?:the\s+)?ratio\s+"
        r"(\d+(?:\s*:\s*\d+)+)", q)
    if m:
        total = _num(m.group(1))
        names = [n.strip() for n in re.split(
            r",|\band\b", m.group(2)) if n.strip()]
        parts = [int(p) for p in m.group(3).split(":")]
        if len(names) == len(parts) and len(parts) >= 2:
            s = sum(parts)
            per = total / s
            shares = {n: per * p for n, p in zip(names, parts)}
            asked = None
            ma = re.search(r"how\s+much\s+(?:does\s+)?"
                           r"([a-z]+)\s+(?:get|receive)", q) \
                or re.search(r"([a-z]+)(?:'s)?\s+share", q) \
                or re.search(r"share\s+of\s+([a-z]+)", q)
            if ma and ma.group(1) in shares:
                asked = ma.group(1)
            steps = [
                f"Ratio parts: {' + '.join(str(p) for p in parts)}"
                f" = {s} parts in total.",
                f"Value of 1 part = {fmt_num(total)} ÷ {s} = "
                f"{fmt_num(per)}",
            ]
            if asked:
                p = parts[names.index(asked)]
                steps.append(
                    f"{asked.capitalize()} gets {p} parts = "
                    f"{p} × {fmt_num(per)} = "
                    f"Rs {fmt_num(shares[asked])}")
                return {"type": "applied", "op": "ratio_share_named",
                        "answer": f"Rs {fmt_num(shares[asked])}",
                        "steps": steps,
                        "value": shares[asked]}
            for n_, p in zip(names, parts):
                steps.append(
                    f"{n_.capitalize()} gets {p} × "
                    f"{fmt_num(per)} = Rs {fmt_num(shares[n_])}")
            return {"type": "applied", "op": "ratio_share_named",
                    "answer": " and ".join(
                        f"Rs {fmt_num(shares[n_])}"
                        for n_ in names),
                    "steps": steps,
                    "value": [shares[n_] for n_ in names]}


    # Simplify a ratio: "ratio of 20 to 45"
    m = re.search(r"\bratio\s+of\s+(" + _NUM + r")\s+(?:to|and)\s+("
                  + _NUM + r")", q) or re.search(
                      r"\bsimplify\s+(?:the\s+)?ratio\s+(\d+)\s*:\s*"
                      r"(\d+)", q) or re.search(
                          r"\bratio\s+(\d+)\s*:\s*(\d+)\b", q)
    if m:
        # Wave 56 guard: a THREE-or-more-part ratio, or a
        # divide/share/angle question, is not a 2-number
        # simplify — echoing the first two parts ("2: 3") was
        # a wrong answer. Those belong to the share / angle
        # schemas; abstain instead.
        if re.search(r"\d+\s*:\s*\d+\s*:\s*\d+", q) or \
                any(w in q for w in ("divide", "share", "angle")):
            return None
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
    r"\s*(?:" + _RS + r")?\s+(?:at\s+)?(" + _NUM + r")\s*%\s*"
    r"(?:per\s+(?:annum|year)\s+)?"
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
            r"\s+(?:of\s+)?(?:" + _RS + r"\s*)?(" + _NUM + r")", q) \
            or re.search(
                r"(?:interest\s+for|for)\s+(?:" + _RS + r"\s*)?"
                r"(" + _NUM + r")\s*(?:rupees?|rs\b)", q)
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
        # Wave 59: when the TOTAL AMOUNT is the ask, it is
        # the answer (the SI alone failed those asks).
        if re.search(r"total\s+amount|find\s+the\s+amount|"
                     r"what\s+is\s+the\s+amount|amount\s+after",
                     q):
            return {"type": "word_problem", "op": "simple_amount",
                    "answer": fmt_num(P + si), "value": P + si,
                    "steps": steps, "principal": P, "rate": R,
                    "time_years": T}
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
    if re.search(r"total\s+amount|find\s+the\s+amount|"
                 r"what\s+is\s+the\s+amount|amount\s+after", q):
        return {"type": "word_problem", "op": "simple_amount",
                "answer": fmt_num(P + si), "value": P + si,
                "steps": steps, "principal": P, "rate": R,
                "time_years": T}
    return {"type": "word_problem", "op": "simple_interest",
            "answer": fmt_num(si), "value": si, "steps": steps,
            "principal": P, "rate": R, "time_years": T}


def _profit_loss(q):
    # Wave 59: "cost price is 400, profit is 20%, find the
    # selling price" — SP from CP and a target profit/loss %.
    _msp = re.search(r"cost\s+price\s+(?:is\s+)?(\d+(?:\.\d+)?)"
                     r"[\s\S]{0,60}?profit\s+(?:is\s+)?"
                     r"(\d+(?:\.\d+)?)\s*%[\s\S]{0,40}?"
                     r"selling\s+price", q)
    if _msp:
        _cp = float(_msp.group(1))
        _p = float(_msp.group(2))
        _sp = _cp * (1 + _p / 100)
        _sp = int(_sp) if _sp == int(_sp) else _sp
        return {"type": "applied", "op": "selling_price",
                "answer": f"Rs {_sp}",
                "steps": [
                    f"Selling price = cost price × (1 + "
                    f"profit/100) = {_cp:g} × "
                    f"{1 + _p / 100:g}",
                    f"Selling price = Rs {_sp}"]}
    _msp = re.search(r"cost\s+price\s+(?:is\s+)?(\d+(?:\.\d+)?)"
                     r"[\s\S]{0,60}?loss\s+(?:is\s+)?"
                     r"(\d+(?:\.\d+)?)\s*%[\s\S]{0,40}?"
                     r"selling\s+price", q)
    if _msp:
        _cp = float(_msp.group(1))
        _p = float(_msp.group(2))
        _sp = _cp * (1 - _p / 100)
        _sp = int(_sp) if _sp == int(_sp) else _sp
        return {"type": "applied", "op": "selling_price",
                "answer": f"Rs {_sp}",
                "steps": [
                    f"Selling price = cost price × (1 - "
                    f"loss/100) = {_cp:g} × {1 - _p / 100:g}",
                    f"Selling price = Rs {_sp}"]}
    # Wave 65: bought for a price, sold AT a profit/loss
    # percent — "a shopkeeper buys a cycle for 3600 rs and
    # sells it at 18% profit. selling price?" The buys/sells
    # chain below would read the 18 as the selling price.
    # Wave 78: the same sale stated as "sells it at a loss
    # of 8%" / "at a profit of 10%" — without this the chain
    # below reads the 8 as the selling price and reports a
    # nonsense 99% loss.
    _mbp = re.search(
        r"\bbuys?\b[\s\S]{0,50}?(?:" + _RS + r"\s*)?(" + _NUM
        + r")[\s\S]{0,40}?\bsells?\b[\s\S]{0,30}?at\s+(?:a\s+)?"
        r"(?:(" + _NUM + r")\s*%\s*(profit|loss)|(profit|loss)"
        r"\s+of\s+(" + _NUM + r")\s*%)", q)
    if _mbp:
        _cp = float(_mbp.group(1))
        if _mbp.group(2) is not None:
            _p = float(_mbp.group(2))
            _kind = _mbp.group(3)
        else:
            _kind = _mbp.group(4)
            _p = float(_mbp.group(5))
        _sgn = 1 if _kind == "profit" else -1
        _sp = _cp * (1 + _sgn * _p / 100)
        _sp = int(_sp) if _sp == int(_sp) else _sp
        return {"type": "applied", "op": "selling_price",
                "answer": f"Rs {_sp}",
                "steps": [
                    f"Selling price = cost price × (1 "
                    f"{'+' if _sgn > 0 else '-'} "
                    f"{_kind}/100) = {_cp:g} × "
                    f"{1 + _sgn * _p / 100:g}",
                    f"Selling price = Rs {_sp}"]}
    m = re.search(
        r"\bbought\b[\s\S]{0,40}?(?:" + _RS + r"\s*)?(" + _NUM
        + r")[\s\S]{0,30}?\bsold\b[\s\S]{0,30}?(?:" + _RS
        + r"\s*)?(" + _NUM + r")", q) or re.search(
            r"\bcost\s+price\b[\s\S]{0,30}?(?:" + _RS + r"\s*)?("
            + _NUM + r")[\s\S]{0,30}?\bselling\s+price\b"
            r"[\s\S]{0,20}?(?:" + _RS + r"\s*)?(" + _NUM + r")",
            q) \
        or re.search(
            r"\bcp\s*(?:is|=)?\s*(?:" + _RS + r"\s*)?(" + _NUM
            + r")[\s\S]{0,20}?\bsp\s*(?:is|=)?\s*(?:" + _RS
            + r"\s*)?(" + _NUM + r")", q) \
        or re.search(
            # Wave 38: present-tense NCERT phrasing — "A
            # shopkeeper buys an article for Rs 500 and sells
            # it for Rs 575" (Wave 35 audit #16-20: 0/10 exact;
            # only the bought/sold past tense was recognised).
            r"\bbuys?\b[\s\S]{0,50}?(?:" + _RS + r"\s*)?("
            + _NUM + r")[\s\S]{0,40}?\bsells?\b[\s\S]{0,30}?"
            r"(?:" + _RS + r"\s*)?(" + _NUM + r")", q) \
        or re.search(
            # Wave 38: Hindi — "800 रुपये में खरीदकर 1000 रुपये
            # में बेची गई" (audit #476).
            r"(" + _NUM + r")\s*(?:रुपये|रुपया)\s*में\s*खरीदकर\s*"
            r"(" + _NUM + r")\s*(?:रुपये|रुपया)?\s*में\s*बेच",
            q) \
        or re.search(
            # Wave 38: Roman Hinglish — "250 me khareedi aur
            # 300 me bechi" (audit #422).
            r"(" + _NUM + r")\s*(?:me|mein)\s*(?:khareed\w*|"
            r"kharid\w*)[\s\S]{0,30}?(" + _NUM + r")\s*"
            r"(?:me|mein)\s*bech\w*", q)
    if not m:
        return None
    cp, sp_ = _num(m.group(1)), _num(m.group(2))
    if cp == 0:
        return None
    diff = sp_ - cp
    kind = "Profit" if diff > 0 else "Loss" if diff < 0 else "None"
    wants_pct = bool(re.search(
        r"percent|percentage|%|प्रतिशत|pratishat", q))
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
    # Wave 56: the two-step chain — "A number is multiplied
    # by 6 and 8 is added to the product. The result is 56."
    # kx + b = R (or kx - b = R), any k, b, R.
    m = re.search(r"multiplied\s+by\s+(" + _NUM + r")\s+and\s+("
                  + _NUM + r")\s+is\s+(added|subtracted)"
                  r"[^.]*?\.?\s*(?:the\s+)?result\s+is\s+("
                  + _NUM + r")", q)
    if m:
        k, b, R = _num(m.group(1)), _num(m.group(2)), \
            _num(m.group(4))
        if k == 0:
            return None
        if m.group(3) == "added":
            return _lin(
                f"Let the number be x: {fmt_num(k)}x + "
                f"{fmt_num(b)} = {fmt_num(R)}",
                [f"Subtract {fmt_num(b)} from both sides: "
                 f"{fmt_num(k)}x = {fmt_num(R)} - "
                 f"{fmt_num(b)} = {fmt_num(R - b)}",
                 f"Divide by {fmt_num(k)}: x = "
                 f"{fmt_num(R - b)} ÷ {fmt_num(k)}"],
                (R - b) / k)
        return _lin(
            f"Let the number be x: {fmt_num(k)}x - "
            f"{fmt_num(b)} = {fmt_num(R)}",
            [f"Add {fmt_num(b)} to both sides: "
             f"{fmt_num(k)}x = {fmt_num(R)} + {fmt_num(b)} = "
             f"{fmt_num(R + b)}",
             f"Divide by {fmt_num(k)}: x = "
             f"{fmt_num(R + b)} ÷ {fmt_num(k)}"],
            (R + b) / k)
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

    # Wave 56: NCERT writes the plural as "1 hour(s) less" —
    # the "(s)" sat between the unit and "less" and the time
    # was never read, so the whole family fell through. Allow
    # an optional "(s)" after the unit.
    t_less = _time([r"(" + _NUM + r")\s*(hours?|hrs?|minutes?|"
                    r"mins?)(?:\s*\(s\))?\s+less",
                    r"(" + _NUM + r")\s*(घंटा|घंटे|मिनट)\s+कम"])
    t_more = _time([r"(" + _NUM + r")\s*(hours?|hrs?|minutes?|"
                    r"mins?)(?:\s*\(s\))?\s+more",
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
    # Wave 56: elder is k times as old; after T years the
    # SUM of their ages will be S. (k+1)x + 2T = S. The
    # k-times fact may use the "'s age is k times ...'s
    # age" form instead of "k times as old as".
    _m1b = None
    if not m1:
        _m1b = re.search(
            r"(\w+)'s\s+age\s+is\s+(" + _NUM + r")\s+times\s+"
            r"(?:his\s+|her\s+|their\s+)?(\w+)'s\s+age", qq)
    if m1 or _m1b:
        m5 = re.search(
            r"after\s+(" + _NUM + r")\s+years?[^.]{0,60}?"
            r"sum\s+of\s+their\s+ages\s+(?:will\s+be\s+)?("
            + _NUM + r")", qq)
        if m5:
            if m1:
                elder, younger = _clean_name(m1.group(1)), \
                    _clean_name(m1.group(3))
                k = _num(m1.group(2))
            else:
                elder, younger = _clean_name(_m1b.group(1)), \
                    _clean_name(_m1b.group(3))
                k = _num(_m1b.group(2))
            T, S = _num(m5.group(1)), _num(m5.group(2))
            if k > 0 and S > 2 * T:
                y = (S - 2 * T) / (k + 1)
                e = k * y
                if y > 0:
                    steps = [
                        f"Let the {younger}'s present age be "
                        f"x years. Then the {elder}'s present "
                        f"age is {fmt_num(k)}x years.",
                        f"After {fmt_num(T)} years their ages "
                        f"will be x + {fmt_num(T)} and "
                        f"{fmt_num(k)}x + {fmt_num(T)}, adding "
                        f"to {fmt_num(S)}: ({fmt_num(k)} + 1)x "
                        f"+ {fmt_num(2 * T)} = {fmt_num(S)}",
                        f"x = ({fmt_num(S)} - "
                        f"{fmt_num(2 * T)}) / {fmt_num(k + 1)} "
                        f"= {fmt_num(y)}",
                        f"So the {younger} is {fmt_num(y)} "
                        f"years old and the {elder} is "
                        f"{fmt_num(k)} × {fmt_num(y)} = "
                        f"{fmt_num(e)} years old.",
                    ]
                    return {"type": "applied",
                            "op": "ages_times_sum_after",
                            "answer": f"{elder.capitalize()} "
                                      f"is {fmt_num(e)} years "
                                      f"old and {younger} is "
                                      f"{fmt_num(y)} years old",
                            "steps": steps, "value": [e, y]}
    # Wave 56: sum of the ages now is S; k years ago the
    # PRODUCT of their ages was P. The ages are the roots
    # of t^2 - S t + (P + kS - k^2) = 0.
    m6 = re.search(r"sum\s+of\s+(?:the\s+)?ages[^.]{0,60}?"
                   r"\bis\s+(" + _NUM + r")", qq)
    # "Five years ago" is usually spelled out — accept
    # number words for the years-ago slot.
    _NW56 = (r"(?:\d+(?:\.\d+)?|one|two|three|four|five|six|"
             r"seven|eight|nine|ten)")
    _WN56 = {"one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10}
    m7 = re.search(r"(" + _NW56 + r")\s+years?\s+ago[^.]{0,50}?"
                   r"product\s+of\s+their\s+ages\s+was\s+("
                   + _NUM + r")", qq)
    if m6 and m7:
        S = _num(m6.group(1))
        k = _num(m7.group(1)) if m7.group(1)[0].isdigit() \
            else float(_WN56[m7.group(1)])
        P = _num(m7.group(2))
        ab = P + k * S - k * k
        disc = S * S - 4 * ab
        if disc >= 0:
            r1 = (S + math.sqrt(disc)) / 2
            r2 = (S - math.sqrt(disc)) / 2
            if r2 > k:
                mn = re.search(
                    r"ages\s+of\s+(?:a\s+|the\s+)?(\w+)\s+and\s+"
                    r"(?:his\s+|her\s+|their\s+)?(\w+)", qq)
                elder = _clean_name(mn.group(1)) if mn \
                    else "elder"
                younger = _clean_name(mn.group(2)) if mn \
                    else "younger"
                steps = [
                    f"Let the two ages be a and b: a + b = "
                    f"{fmt_num(S)}",
                    f"{fmt_num(k)} years ago: (a - "
                    f"{fmt_num(k)})(b - {fmt_num(k)}) = "
                    f"{fmt_num(P)}, so ab = {fmt_num(P)} + "
                    f"{fmt_num(k)} × {fmt_num(S)} - "
                    f"{fmt_num(k * k)} = {fmt_num(ab)}",
                    f"a and b are the roots of t^2 - "
                    f"{fmt_num(S)}t + {fmt_num(ab)} = 0, "
                    f"giving t = {fmt_num(r1)} or "
                    f"t = {fmt_num(r2)}",
                    f"So the {elder} is {fmt_num(r1)} years "
                    f"old and the {younger} is {fmt_num(r2)} "
                    f"years old.",
                ]
                return {"type": "applied",
                        "op": "ages_sum_product_ago",
                        "answer": f"{elder.capitalize()} is "
                                  f"{fmt_num(r1)} years old "
                                  f"and {younger} is "
                                  f"{fmt_num(r2)} years old",
                        "steps": steps, "value": [r1, r2]}
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
        + _NUM + r")\s*(?:" + _RS + r")?\s+at\s+(" + _NUM
        + r")\s*%\s*(?:per\s+(?:annum|year)\s+)?(?:for\s+)?("
        + _NUM + r")\s*(?:years?|yrs?)",
        q)
    if not m:
        # Wave 65: amount-first form — "find the amount on
        # 8000 rs at 10% compound interest for 2 years".
        m = re.search(
            r"amount\s+on\s+(?:" + _RS + r"\s*)?(" + _NUM
            + r")\s*(?:" + _RS + r")?\s+at\s+(" + _NUM
            + r")\s*%\s*compound\s+interest\s+(?:for\s+)?("
            + _NUM + r")\s*(?:years?|yrs?)", q)
        if m:
            P, R, T = (sp.Rational(m.group(i)) for i in (1, 2, 3))
            if T != int(T):
                return None
            amount = P * (1 + R / 100) ** int(T)
            steps = [
                "Compound interest: Amount A = P(1 + R/100)^T",
                f"A = {fmt_num(P)} × (1 + {fmt_num(R)}/100)"
                f"^{fmt_num(T)} = {fmt_num(amount)}",
            ]
            return {"type": "applied", "op": "compound_amount",
                    "answer": fmt_num(amount),
                    "value": float(amount), "steps": steps,
                    "amount": float(amount)}
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
    # Wave 59: when the TOTAL AMOUNT is the ask, it is the
    # answer (mirrors the frequency variant's rule below).
    if re.search(r"total\s+amount|find\s+the\s+amount|"
                 r"what\s+is\s+the\s+amount|amount\s+after", q):
        return {"type": "applied", "op": "compound_amount",
                "answer": fmt_num(amount), "value": float(amount),
                "steps": steps, "amount": float(amount)}
    return {"type": "applied", "op": "compound_interest",
            "answer": fmt_num(ci), "value": float(ci),
            "steps": steps, "amount": float(amount)}


def _discount(q):
    if "discount" not in q:
        return None
    md = re.search(r"discount\s+of\s+(" + _NUM + r")\s*%", q) \
        or re.search(r"(" + _NUM + r")\s*%\s+discount", q)
    if not md:
        return None
    d = _num(md.group(1))
    if not (0 <= d < 100):
        return None
    # Wave 56: the reverse and chain forms of the same schema.
    # "Sold at Rs S after a discount of d%" gives the selling
    # price directly; the marked price is S / (1 - d/100), and
    # with a cost price the chain continues to profit %.
    # Wave 78: the price after "sold at/for" must not be a
    # percent — "sold at 15% discount" used to read S = 15.
    ms = re.search(r"(?:sold|sells)\s+(?:at|for)\s+(?:"
                   + _RS + r"\s*)?(" + _NUM + r")(?!\s*%)", q) or \
        re.search(r"selling\s+price\s+(?:is\s+)?(?:"
                  + _RS + r"\s*)?(" + _NUM + r")(?!\s*%)", q)
    if ms:
        S = _num(ms.group(1))
        M = S / (1 - d / 100.0)
        mcp = re.search(r"cost\s+price\s+(?:is\s+)?(?:"
                        + _RS + r"\s*)?(" + _NUM + r")", q)
        if mcp and "profit" in q:
            CP = _num(mcp.group(1))
            if CP <= 0:
                return None
            prof = S - CP
            steps = [
                f"Selling price = Rs {fmt_num(S)} after a "
                f"{fmt_num(d)}% discount, so the marked price "
                f"was {fmt_num(S)} / (1 - {fmt_num(d)}/100) = "
                f"Rs {fmt_num(M)}",
                f"Cost price = Rs {fmt_num(CP)}, so profit = "
                f"{fmt_num(S)} - {fmt_num(CP)} = "
                f"Rs {fmt_num(prof)}",
            ]
            if "percent" in q or "%" in q:
                pp = prof / CP * 100.0
                steps.append(
                    f"Profit percent = {fmt_num(prof)} / "
                    f"{fmt_num(CP)} × 100 = {fmt_num(pp)}%")
                return {"type": "applied",
                        "op": "discount_profit_chain",
                        "answer": f"{fmt_num(pp)}%",
                        "steps": steps, "value": pp}
            return {"type": "applied",
                    "op": "discount_profit_chain",
                    "answer": f"Rs {fmt_num(prof)}",
                    "steps": steps, "value": prof}
        if "marked price" in q:
            steps = [
                f"The article sells for Rs {fmt_num(S)} after "
                f"a discount of {fmt_num(d)}% on the marked "
                f"price.",
                f"So (100 - {fmt_num(d)})% of the marked price "
                f"= Rs {fmt_num(S)}",
                f"Marked price = {fmt_num(S)} × 100 / "
                f"{fmt_num(100 - d)} = Rs {fmt_num(M)}",
            ]
            return {"type": "applied", "op": "discount_reverse",
                    "answer": f"Rs {fmt_num(M)}", "steps": steps,
                    "value": M}
    mm = re.search(
        r"marked\s+price\s+(?:is\s+)?(?:" + _RS + r"\s*)?("
        + _NUM + r")", q) or re.search(
            r"discount\s+of\s+" + _NUM + r"\s*%\s+on\s+"
            r"[\w\s]{0,24}?(?:" + _RS + r"\s*)?(" + _NUM + r")",
            q) or re.search(
                # Wave 56: "the marked price of an article is
                # Rs 1500" — words sit between "marked price"
                # and the amount.
                r"marked\s+price\b[^.]{0,40}?(?:is|=)\s*(?:"
                + _RS + r"\s*)?(" + _NUM + r")", q)
    if not mm:
        return None
    M = _num(mm.group(1))
    if M <= 0:
        return None
    # Wave 56: the chain stated from the marked price —
    # MP + discount % + cost price, profit asked. The
    # selling price is derived, then profit is measured
    # against the cost price.
    _mcp56 = re.search(r"cost\s+price\s+(?:is\s+)?(?:"
                       + _RS + r"\s*)?(" + _NUM + r")", q)
    if _mcp56 and "profit" in q:
        _CP = _num(_mcp56.group(1))
        _SP = M * (1 - d / 100.0)
        if _CP > 0:
            _prof = _SP - _CP
            _steps = [
                f"Marked price = Rs {fmt_num(M)}, discount "
                f"= {fmt_num(d)}%, so the selling price is "
                f"{fmt_num(M)} × (1 - {fmt_num(d)}/100) = "
                f"Rs {fmt_num(_SP)}",
                f"Cost price = Rs {fmt_num(_CP)}, so "
                f"profit = {fmt_num(_SP)} - {fmt_num(_CP)} "
                f"= Rs {fmt_num(_prof)}",
            ]
            if "percent" in q or "%" in q:
                _pp = _prof / _CP * 100.0
                _steps.append(
                    f"Profit percent = {fmt_num(_prof)} / "
                    f"{fmt_num(_CP)} × 100 = "
                    f"{fmt_num(_pp)}%")
                return {"type": "applied",
                        "op": "discount_profit_chain",
                        "answer": f"{fmt_num(_pp)}%",
                        "steps": _steps, "value": _pp}
            return {"type": "applied",
                    "op": "discount_profit_chain",
                    "answer": f"Rs {fmt_num(_prof)}",
                    "steps": _steps, "value": _prof}
    off = M * d / 100.0
    sp_ = M - off
    # Wave 78: when the question asks for the DISCOUNT itself
    # ("how much discount does the customer get?", "what is
    # the discount on ..."), the answer is the amount taken
    # off, not the selling price.
    if re.search(r"how\s+much\s+discount|what\s+is\s+the\s+"
                 r"discount\b|discount\s+amount|amount\s+of\s+"
                 r"discount|discount\s+(?:does|will|did)\b",
                 q) and "percent" not in q \
            and "selling" not in q:
        return {"type": "applied", "op": "discount_amount",
                "answer": f"Rs {fmt_num(off)}",
                "steps": [
                    f"Marked price = Rs {fmt_num(M)}, "
                    f"discount = {fmt_num(d)}%",
                    f"Discount = {fmt_num(d)}% of "
                    f"{fmt_num(M)} = Rs {fmt_num(off)}"],
                "value": off}
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
    # Wave 78: present-tense "sells ... for Rs S at a loss
    # of P%" is the same form (the object may sit between
    # the verb and "for" — "sells a table for Rs 1365"; the
    # gap may not cross a digit or a sentence end), and
    # "gain" is profit.
    m = re.search(
        r"(?:sold|sells)\b[^.\d]{0,25}?(?:at|for)\s+(?:"
        + _RS + r"\s*)?(" + _NUM + r")[\s\S]{0,40}?"
        r"\b(profit|gain|loss)\s+of\s+(" + _NUM + r")\s*%", q)
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
        + _NUM + r")[\s\S]{0,40}?\b(profit|gain|loss)\s+of\s+("
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
    # Wave 38: the same SP ask with the % stated BEFORE the CP
    # — "A man sells an article at a loss of 15%. If the cost
    # price is Rs 2000, find the selling price." (audit #256;
    # the block above needs CP first, % second).
    m = re.search(
        r"\b(profit|gain|loss)\s+of\s+(" + _NUM + r")\s*%"
        r"[\s\S]{0,60}?(?:cost\s+price|cp)\s+(?:is\s+)?"
        r"(?:" + _RS + r"\s*)?(" + _NUM + r")", q)
    if m and "selling" in q:
        kind, p, cp = m.group(1), _num(m.group(2)), \
            _num(m.group(3))
        if kind == "loss":
            if p >= 100:
                return None
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
    # Wave 38: "By selling a watch for Rs 1275, a man loses
    # 15%. Find the cost price." (audit #257) — the verb form
    # "loses/gains P%" after the SP, where the first block
    # needs "sold at/for ... loss of P%".
    m = re.search(
        r"(?:selling|sold)\b[\s\S]{0,40}?(?:" + _RS + r"\s*)?"
        r"(" + _NUM + r")[\s\S]{0,40}?\b(loses|gains)\s+("
        + _NUM + r")\s*%", q)
    if m:
        sp_, verb, p = _num(m.group(1)), m.group(2), \
            _num(m.group(3))
        if verb == "loses":
            if p >= 100:
                return None
            cp = sp_ / (1 - p / 100.0)
            steps = [
                f"With a loss of {fmt_num(p)}%, SP = CP × "
                f"(1 - {fmt_num(p)}/100) = "
                f"{fmt_num(1 - p / 100)} × CP",
                f"CP = {fmt_num(sp_)} ÷ "
                f"{fmt_num(1 - p / 100)} = Rs {fmt_num(cp)}",
            ]
        else:
            cp = sp_ / (1 + p / 100.0)
            steps = [
                f"With a profit of {fmt_num(p)}%, SP = CP × "
                f"(1 + {fmt_num(p)}/100) = "
                f"{fmt_num(1 + p / 100)} × CP",
                f"CP = {fmt_num(sp_)} ÷ "
                f"{fmt_num(1 + p / 100)} = Rs {fmt_num(cp)}",
            ]
        return {"type": "applied", "op": "reverse_profit_loss",
                "answer": f"Rs {fmt_num(cp)}", "steps": steps,
                "value": cp}
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
    # Wave 47: the TRAIN's length is the unknown — platform
    # length, crossing time and speed are all given ("A train
    # crosses a platform 180 m long in 15 seconds travelling
    # at 60 km/h. Find the length of the train."). The loose
    # length match below grabbed the PLATFORM's 180 m as the
    # train's own length and answered a speed, 86.4 km/h
    # (Wave 35 audit #263; correct length 70 m).
    if "length of the train" in q:
        _mpl = re.search(
            r"(?:platform|bridge|tunnel)\s+(?:of\s+length\s+)?("
            + _NUM + r")\s*m", q)
        _mtm = re.search(r"in\s+(" + _NUM + r")\s*seconds?", q)
        _mv = re.search(r"(" + _NUM + r")\s*(km/h|m/s)", q)
        if _mpl and _mtm and _mv:
            _P, _T = _num(_mpl.group(1)), _num(_mtm.group(1))
            _V = _num(_mv.group(1))
            _vms = _V * 5 / 18 if _mv.group(2) == "km/h" \
                else _V
            _dist = _vms * _T
            _L = _dist - _P
            if _L > 0:
                steps = [
                    f"Speed = {fmt_num(_V)} "
                    f"{_mv.group(2)}"
                    + (f" = {fmt_num(_V)} × 5/18 = "
                       f"{fmt_num(_vms)} m/s"
                       if _mv.group(2) == "km/h" else ""),
                    f"While crossing the platform the train "
                    f"covers (its own length + platform length) "
                    f"= speed × time = {fmt_num(_vms)} × "
                    f"{fmt_num(_T)} = {fmt_num(_dist)} m",
                    f"Length of the train = {fmt_num(_dist)} "
                    f"- {fmt_num(_P)} = {fmt_num(_L)} m",
                ]
                return {"type": "applied",
                        "op": "train_length",
                        "answer": f"{fmt_num(_L)} m",
                        "steps": steps, "value": float(_L)}
    mt = re.search(r"train\s+of\s+length\s+(" + _NUM + r")\s*m",
                   q)
    L = None
    if mt:
        L = _num(mt.group(1))
    else:
        _loose = re.search(
            r"train([\s\S]{0,20}?)(" + _NUM + r")\s*m\s+long",
            q)
        # Wave 47: the loose form must not swallow a following
        # platform/bridge length as the train's own (see the
        # audit #263 note above).
        if _loose and not re.search(
                r"platform|bridge|tunnel", _loose.group(1)):
            L = _num(_loose.group(2))
    if L is None:
        return None

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
    # Wave 56 form: (number + reversed number) = 11(a + b),
    # with the digits differing by d — "The sum of a
    # two-digit number and the number obtained by
    # reversing the digits is 66. The digits differ by 2."
    _m56 = re.search(
        r"sum\s+of\s+a\s+two-digit\s+number\s+and\s+the\s+"
        r"number\s+obtained\s+by\s+reversing\s+(?:the\s+)?"
        r"digits\s+is\s+(" + _NUM + r")", q)
    _md56 = re.search(r"digits\s+differ\s+by\s+(" + _NUM +
                      r")", q)
    if _m56 and _md56:
        _tot, _d = int(float(_m56.group(1))), \
            int(float(_md56.group(1)))
        if _tot % 11 == 0:
            _s = _tot // 11
            if (_s + _d) % 2 == 0:
                _hi, _lo = (_s + _d) // 2, (_s - _d) // 2
                if 1 <= _hi <= 9 and 0 <= _lo <= 9:
                    _num = 10 * _hi + _lo
                    return {"type": "applied", "op": "digits",
                            "answer": str(_num),
                            "value": _num,
                            "steps": [
                                "Let the digits be a and b. "
                                "The number plus its reverse "
                                "= 11(a + b).",
                                f"11(a + b) = {_tot}, so "
                                f"a + b = {_s}; also the "
                                f"digits differ by {_d}.",
                                f"Digits: {_hi} and {_lo}, "
                                f"so the number is {_num} "
                                f"(its reverse "
                                f"{10 * _lo + _hi} also "
                                f"satisfies the conditions).",
                            ]}
        return None
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
    # Wave 56: the wording may skip "compound interest"
    # entirely — "Find the amount on Rs 8000 at 5% per annum
    # for 2 years, compounded quarterly" — the frequency word
    # is the real signal. Monthly compounding joins the family.
    if "compound interest" not in q and "compounded" not in q:
        return None
    if "half-yearly" in q or "half yearly" in q:
        n = 2
    elif "quarterly" in q:
        n = 4
    elif "monthly" in q:
        n = 12
    else:
        return None
    m = re.search(
        r"compound\s+interest\s+on\s+(?:" + _RS + r"\s*)?("
        + _NUM + r")\s+at\s+(" + _NUM + r")\s*%\s*(?:per\s+"
        r"annum\s+)?(?:for\s+)?(" + _NUM + r")\s*(?:years?|yrs?)",
        q) or re.search(
            r"(?:amount|sum)\s+(?:on\s+)?(?:" + _RS + r"\s*)?("
            + _NUM + r")\s+at\s+(" + _NUM + r")\s*%\s*(?:per\s+"
            r"annum\s+)?(?:for\s+)?(" + _NUM + r")\s*"
            r"(?:years?|yrs?)", q)
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
    _per = {2: "half-yearly", 4: "quarterly", 12: "monthly"}[n]
    steps = [
        f"Compounded {_per}: "
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
    # Wave 56: when the question asks for the AMOUNT (and
    # never mentions compound interest), the amount is the
    # answer — the CI figure alone failed those asks.
    if "amount" in q and "compound interest" not in q:
        return {"type": "applied", "op": "compound_amount_freq",
                "answer": _money(amount), "value": float(amount),
                "steps": steps, "amount": float(amount)}
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
        # Wave 58: CUBIC Vieta. The quadratic-only path below
        # let "sum of the zeroes of x^3 - 5x^2 + 2x + 8" fall
        # through to the zeroes-LISTING branch, which answered
        # with the roots themselves instead of their sum.
        try:
            _expr = parse_expression(text)
            _syms = sorted(_expr.free_symbols,
                           key=lambda s: s.name)
            if len(_syms) != 1:
                return None
            _poly = sp.Poly(_expr, _syms[0])
            if _poly is None or _poly.degree() != 3:
                return None
            _a, _b, _c, _d = _poly.all_coeffs()
            if (_a.free_symbols | _b.free_symbols
                    | _c.free_symbols | _d.free_symbols):
                return None
            _s1 = sp.simplify(-_b / _a)
            _s2 = sp.simplify(_c / _a)
            _s3 = sp.simplify(-_d / _a)
            steps = [
                f"For a cubic a·x^3 + b·x^2 + c·x + d with "
                f"a = {fmt(_a)}, b = {fmt(_b)}, c = {fmt(_c)}, "
                f"d = {fmt(_d)}:",
                f"Sum of zeroes = -b/a = {fmt(_s1)}",
                f"Sum of products of zeroes taken two at a "
                f"time = c/a = {fmt(_s2)}",
                f"Product of zeroes = -d/a = {fmt(_s3)}",
            ]
            if "two at a time" in q or "pairwise" in q:
                return {"type": "algebra",
                        "op": "sum_product_roots",
                        "answer": f"Sum of products (two at a "
                                  f"time) = {fmt(_s2)}",
                        "steps": steps}
            _parts = []
            if "sum" in q:
                _parts.append(f"Sum = {fmt(_s1)}")
            if "product" in q:
                _parts.append(f"Product = {fmt(_s3)}")
            if not _parts:
                return None
            return {"type": "algebra",
                    "op": "sum_product_roots",
                    "answer": ", ".join(_parts), "steps": steps}
        except Exception:
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
    # Wave 65: "one tap fills a tank in 6 hours. how long
    # will 3 such taps take?" — the count was ignored and
    # the single-tap time (6) came back. With ONE fill time
    # and an explicit tap count, the rate scales by it.
    _cnt = re.search(r"(" + _NUM + r")\s+(?:such\s+)?"
                     r"(?:taps?|pipes?)\b", q)
    if _cnt and len(fills) == 1 and not empties:
        rate = rate * int(float(_cnt.group(1)))
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
    # Wave 47: together-time + ONE worker's solo time given,
    # the OTHER worker's solo time asked ("A and B together
    # can do a work in 8 days. A alone can do it in 12 days.
    # In how many days can B alone do it?"). The two-number
    # path below read 8 and 12 as the two solo times and
    # answered 24/5 (Wave 35 audit #259; correct 24).
    _mt = re.search(r"together[^.]{0,60}?in\s+(" + _NUM
                    + r")\s+days", q)
    _ms = re.search(r"(\w+)\s+alone[^.]{0,60}?in\s+(" + _NUM
                    + r")\s+days", q)
    if _mt and _ms:
        from fractions import Fraction as F
        _T = F(str(_mt.group(1)))
        _A = F(str(_ms.group(2)))
        _solo = _ms.group(1)
        _ask = re.search(r"can\s+(\w+)\s+alone", q) or \
            re.search(r"(\w+)\s+alone\s+(?:do|does|take|"
                      r"finish)", q)
        if _ask and _ask.group(1) == _solo:
            steps = [
                f"{_solo.capitalize()} alone is already given "
                f"to take {_frac_str(_A)} days.",
            ]
            return {"type": "applied", "op": "work_together",
                    "answer": f"{_frac_str(_A)} days",
                    "steps": steps, "value": float(_A)}
        if _A > _T:
            _other = _T * _A / (_A - _T)
            _rate = 1 / _T - 1 / _A
            _who = _ask.group(1).capitalize() if _ask \
                else "The other worker"
            steps = [
                f"Together they finish in {_frac_str(_T)} "
                f"days, so in 1 day they do "
                f"1/{_frac_str(_T)} of the work.",
                f"{_solo.capitalize()} alone does "
                f"1/{_frac_str(_A)} of the work in 1 day.",
                f"{_who}'s rate = 1/{_frac_str(_T)} - "
                f"1/{_frac_str(_A)} = {_frac_str(_rate)} of "
                f"the work per day.",
                f"Days needed alone = {_frac_str(_other)} days"
                + (f" ≈ {float(_other):.2f} days"
                   if _other.denominator != 1 else ""),
            ]
            return {"type": "applied", "op": "work_together",
                    "answer": f"{_frac_str(_other)} days",
                    "steps": steps, "value": float(_other)}
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
                   r"(" + "|".join(_COLOURS) + r")\b", q) or \
        re.search(r"(" + "|".join(_COLOURS) + r")\s+ball\s+is\s+"
                  r"drawn", q)
    if mc:
        colour = mc.group(1)
    if colour is None:
        return None
    target = None
    # Wave 56: the target bag may be named with "came from
    # bag A" or a trailing "from bag A." — not only "drawn
    # from bag A" / "from bag A?".
    mt = re.search(r"drawn from bag\s+(\w+)", q) or \
        re.search(r"came from bag\s+(\w+)", q) or \
        re.search(r"from bag\s+(\w+)\s*\.?\s*\?\s*$", q.strip()) or \
        re.search(r"from bag\s+(\w+)\s*\.\s*$", q.strip())
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


def _lp_inequalities(q):
    """Wave 33: linear programming from RAW inequalities —
    "Maximise Z = 3x + 4y subject to x + y ≤ 4, x ≥ 0,
    y ≥ 0". Wave 32 covered only the corner-points-given
    form; the raw form routed to algebra, whose parser
    turned the sentence into letter-soup. Method (Class 12):
    the optimum of a linear objective over a polygon sits at
    a corner — intersect every pair of boundary lines, keep
    the feasible corners, evaluate Z at each. All arithmetic
    is exact (sympy rationals), so NCERT answers like
    235/19 at (20/19, 45/19) come out as fractions."""
    if not re.search(r"maxim|minim", q):
        return None
    if "corner point" in q:
        return None  # _lp_corners owns that form
    mo = re.search(r"\bz\s*=\s*(.+?)(?=\s+subject\b|,|;|$)", q)
    if not mo:
        return None
    obj_text = mo.group(1).strip()
    rest = q[mo.end():]
    mc = re.search(r"subject\s+to\s+(?:the\s+)?"
                   r"(?:constraints?\s+)?", rest)
    ctext = rest[mc.end():] if mc else rest.lstrip(" ,;")
    x, y = sp.symbols("x y")
    try:
        oexpr = sp.expand(parse_expression(obj_text))
    except Exception:
        return None
    if not oexpr.free_symbols or not \
            oexpr.free_symbols <= {x, y}:
        return None
    oc_a, oc_b = oexpr.coeff(x), oexpr.coeff(y)
    oc_c = oexpr.subs({x: 0, y: 0})
    if oc_a == 0 and oc_b == 0:
        return None
    cons = []  # (a, b, c, sense): a·x + b·y <sense> c
    if re.search(r"\bx\s*,\s*y\s*(>=|≥)", ctext):
        cons += [(sp.Integer(1), sp.Integer(0), sp.Integer(0),
                  ">="), (sp.Integer(0), sp.Integer(1),
                          sp.Integer(0), ">=")]
        ctext = re.sub(r"\bx\s*,\s*y\s*(?:>=|≥)\s*0", " ", ctext)
    pieces = [p.strip(" .")
              for p in re.split(r"[,;]|\band\b", ctext)
              if p.strip(" .")]
    if not pieces:
        return None
    sense_map = {"<=": "<=", "≤": "<=", ">=": ">=", "≥": ">=",
                 "=": "==", "<": "<=", ">": ">="}
    for p in pieces:
        m = re.match(r"^(.*?)(<=|>=|≤|≥|=|<|>)\s*"
                     r"(-?\d+(?:\.\d+)?)\s*$", p)
        if not m:
            return None
        try:
            lhs = sp.expand(parse_expression(m.group(1)))
        except Exception:
            return None
        if not lhs.free_symbols or not \
                lhs.free_symbols <= {x, y}:
            return None
        rhs = sp.Rational(m.group(3))
        cons.append((lhs.coeff(x), lhs.coeff(y),
                     rhs - lhs.subs({x: 0, y: 0}),
                     sense_map[m.group(2)]))
    if len(cons) < 2:
        return None

    def _feasible(px, py):
        for a, b, c, s in cons:
            v = a * px + b * py
            if s == "<=" and v > c:
                return False
            if s == ">=" and v < c:
                return False
            if s == "==" and v != c:
                return False
        return True

    corners = []
    lines = [(a, b, c) for a, b, c, _s in cons]
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            a1, b1, c1 = lines[i]
            a2, b2, c2 = lines[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = (c1 * b2 - c2 * b1) / det
            py = (a1 * c2 - a2 * c1) / det
            if _feasible(px, py) and (px, py) not in corners:
                corners.append((px, py))
    if _feasible(sp.Integer(0), sp.Integer(0)) and \
            (sp.Integer(0), sp.Integer(0)) not in corners:
        corners.append((sp.Integer(0), sp.Integer(0)))
    if not corners:
        return None
    # Unbounded? A boundary-line direction that stays in the
    # recession cone and improves Z means no optimum exists
    # in that direction (an honest Class-12 answer).
    def _improves(dx, dy, want_max):
        for a, b, c, s in cons:
            v = a * dx + b * dy
            if s == "<=" and v > 0:
                return False
            if s == ">=" and v < 0:
                return False
            if s == "==" and v != 0:
                return False
        delta = oc_a * dx + oc_b * dy
        return delta > 0 if want_max else delta < 0

    dirs = set()
    for a, b, c in lines:
        dirs.add((-b, a))
        dirs.add((b, -a))
    want_max = "maxim" in q
    want_min = "minim" in q
    unb_max = want_max and any(
        _improves(dx, dy, True) for dx, dy in dirs)
    unb_min = want_min and any(
        _improves(dx, dy, False) for dx, dy in dirs)
    steps = [
        "The feasible region's corner points come from "
        "intersecting the boundary lines of the constraints "
        "(the optimum of a linear Z is always at a corner):",
    ]
    vals = []
    for (px, py) in corners:
        v = oc_a * px + oc_b * py + oc_c
        vals.append((v, (px, py)))
        steps.append(f"Corner ({fmt(px)}, {fmt(py)}): "
                     f"Z = {fmt(v)}")
    parts = []
    if want_max:
        if unb_max:
            steps.append("The feasible region is unbounded "
                         "in a direction that keeps "
                         "increasing Z, so Z has no maximum "
                         "value.")
            parts.append("No maximum value (feasible region "
                         "is unbounded)")
        else:
            bv, bp = max(vals, key=lambda t: float(t[0]))
            steps.append(f"Maximum value of Z is {fmt(bv)} "
                         f"at ({fmt(bp[0])}, {fmt(bp[1])}).")
            parts.append(f"Maximum Z = {fmt(bv)} at "
                         f"({fmt(bp[0])}, {fmt(bp[1])})")
    if want_min:
        if unb_min:
            steps.append("The feasible region is unbounded "
                         "in a direction that keeps "
                         "decreasing Z, so Z has no minimum "
                         "value.")
            parts.append("No minimum value (feasible region "
                         "is unbounded)")
        else:
            bv, bp = min(vals, key=lambda t: float(t[0]))
            steps.append(f"Minimum value of Z is {fmt(bv)} "
                         f"at ({fmt(bp[0])}, {fmt(bp[1])}).")
            parts.append(f"Minimum Z = {fmt(bv)} at "
                         f"({fmt(bp[0])}, {fmt(bp[1])})")
    if not parts:
        return None
    op = "lp_minimise" if (want_min and not want_max) \
        else "lp_maximise"
    best = None
    if parts and "at (" in parts[0]:
        best = float(max(vals, key=lambda t: float(t[0]))[0]
                     if op == "lp_maximise" else
                     min(vals, key=lambda t: float(t[0]))[0])
    return {"type": "applied", "op": op,
            "answer": "; ".join(parts), "steps": steps,
            "value": best}


def _rectangle_diagonal(q):
    """Wave 33: the NCERT rectangle form "the diagonal is
    60 m more than the shorter side, the longer side is
    30 m more than the shorter side — find the sides".
    With shorter side s: s^2 + (s + A)^2 = (s + B)^2
    (Pythagoras), a quadratic in s."""
    md = re.search(r"diagonal[^.]{0,60}?(" + _NUM + r")\s*"
                   r"(?:m\s+)?more\s+than\s+the\s+shorter\s+"
                   r"side", q)
    ml = re.search(r"longer\s+side\s+is\s+(" + _NUM + r")\s*"
                   r"(?:m\s+)?more\s+than\s+the\s+shorter\s+"
                   r"side", q)
    if not (md and ml):
        return None
    B, A = _num(md.group(1)), _num(ml.group(1))
    # s^2 + (2A - 2B)s + (A^2 - B^2) = 0
    bq, cq = 2 * A - 2 * B, A * A - B * B
    disc = bq * bq - 4 * cq
    if disc < 0:
        return None
    sd = math.sqrt(disc)
    cands = [(-bq + sd) / 2, (-bq - sd) / 2]
    good = [c for c in cands if c > 0]
    if not good:
        return None
    s = good[0]
    steps = [
        f"Let the shorter side be s m. Then the longer "
        f"side is s + {fmt_num(A)} and the diagonal is "
        f"s + {fmt_num(B)}.",
        f"By Pythagoras: s^2 + (s + {fmt_num(A)})^2 = "
        f"(s + {fmt_num(B)})^2.",
        f"Solving the quadratic gives s = {fmt_num(s)} "
        f"(the positive root).",
        f"Longer side = {fmt_num(s)} + {fmt_num(A)} = "
        f"{fmt_num(s + A)} m.",
    ]
    return {"type": "applied", "op": "rectangle_diagonal",
            "answer": f"Shorter side = {fmt_num(s)} m, "
                      f"longer side = {fmt_num(s + A)} m",
            "steps": steps, "value": [s + A, s]}


# ---------------------------------------------------------------------------
# Wave 52 (audit #1): Hindi (Devanagari) word problems. A Hindi
# question outside the pattern set used to reach the expression
# parser, which multiplied the question's own Devanagari letters
# together and returned the product as the "answer" (22 WRONG in
# the Wave 35 battery's Hindi set). These are the top mensuration
# / SI / percentage statement forms, each gated on its shape word
# + quantity word so a partial match can never fire. Steps are in
# Hindi, matching the Wave 33 Hindi probability answers. The
# router tries this family FIRST for Devanagari questions and
# accepts only the hindi_* ops.
# ---------------------------------------------------------------------------
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _hnear(q, word):
    """The number attached to a Hindi quantity word, stated
    after it ("त्रिज्या 7 cm") or before it ("7 cm त्रिज्या")."""
    m = re.search(re.escape(word) + r"\s*(" + _NUM + r")", q) or \
        re.search(r"(" + _NUM + r")\s*(?:cm|सेमी|m|मी)?\s*"
                  + re.escape(word), q)
    return float(m.group(1)) if m else None


def _hpi(coef):
    """(answer, value) for coef·π in the house format."""
    val = sp.Rational(coef) * sp.pi
    return f"{fmt(val)} ≈ {fmt_num(float(val))}", float(val)


def _hindi_word_problems(q):
    q = q.translate(_DEVA_DIGITS)

    def res(op, answer, value, steps):
        return {"type": "applied", "op": op, "answer": answer,
                "value": value, "steps": steps}

    def hpi(coef, r):
        """_hpi + the Wave 99 pi policy for radius r: when the
        radius is 7-friendly the coefficient is multiplied by
        22/7 exactly (Rational), giving the clean textbook
        value; returns (answer, value, used_227)."""
        _pi, _u227, _reason = pi_choice(radius=r)
        if _u227:
            v = sp.Rational(coef) * sp.Rational(22, 7)
            # Display like the float paths: integers clean,
            # anything else a decimal (1437.33, not 4312/3).
            return fmt_num(float(v)), float(v), True
        ans, val = _hpi(coef)
        return ans, val, False

    # Hemisphere volume — BEFORE the sphere (अर्धगोले contains गोले).
    if "अर्धगोल" in q and "आयतन" in q:
        r = _hnear(q, "त्रिज्या")
        if r:
            ans, val, _u = hpi(sp.Rational(2, 3) * sp.Rational(str(r)) ** 3, r)
            return res("hindi_hemisphere_volume", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "अर्धगोले का आयतन = (2/3) × π × त्रिज्या³",
                f"= (2/3) × π × {fmt_num(r)}³ = {ans}",
            ])
    # Cylinder curved surface area (वक्र पृष्ठ क्षेत्रफल = 2πrh).
    if "बेलन" in q and "वक्र पृष्ठ" in q:
        r, h = _hnear(q, "त्रिज्या"), _hnear(q, "ऊंचाई")
        if r and h:
            ans, val, _u = hpi(2 * sp.Rational(str(r)) * sp.Rational(str(h)), r)
            return res("hindi_cylinder_csa", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "बेलन का वक्र पृष्ठ क्षेत्रफल = 2 × π × त्रिज्या "
                "× ऊंचाई",
                f"= 2 × π × {fmt_num(r)} × {fmt_num(h)} = {ans}",
            ])
    # Cylinder volume.
    if "बेलन" in q and "आयतन" in q:
        r, h = _hnear(q, "त्रिज्या"), _hnear(q, "ऊंचाई")
        if r and h:
            ans, val, _u = hpi(sp.Rational(str(r)) ** 2 * sp.Rational(str(h)), r)
            return res("hindi_cylinder_volume", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "बेलन का आयतन = π × त्रिज्या² × ऊंचाई",
                f"= π × {fmt_num(r)}² × {fmt_num(h)} = {ans}",
            ])
    # Cone volume.
    if "शंकु" in q and "आयतन" in q:
        r, h = _hnear(q, "त्रिज्या"), _hnear(q, "ऊंचाई")
        if r and h:
            ans, val, _u = hpi(sp.Rational(1, 3)
                            * sp.Rational(str(r)) ** 2 * sp.Rational(str(h)), r)
            return res("hindi_cone_volume", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "शंकु का आयतन = (1/3) × π × त्रिज्या² × ऊंचाई",
                f"= (1/3) × π × {fmt_num(r)}² × {fmt_num(h)} "
                f"= {ans}",
            ])
    # Sphere volume.
    if "गोल" in q and "आयतन" in q:
        r = _hnear(q, "त्रिज्या")
        if r:
            ans, val, _u = hpi(sp.Rational(4, 3) * sp.Rational(str(r)) ** 3, r)
            return res("hindi_sphere_volume", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "गोले का आयतन = (4/3) × π × त्रिज्या³",
                f"= (4/3) × π × {fmt_num(r)}³ = {ans}",
            ])
    # Cube volume.
    if "घन" in q and "आयतन" in q:
        s = _hnear(q, "भुजा")
        if s:
            v = s ** 3
            return res("hindi_cube_volume", fmt_num(v), v, [
                "घन का आयतन = भुजा³",
                f"= {fmt_num(s)}³ = {fmt_num(v)}",
            ])
    # Circle: area (क्षेत्रफल) or circumference (परिमाप / परिधि).
    if "वृत्त" in q:
        r = _hnear(q, "त्रिज्या")
        if r and "क्षेत्रफल" in q:
            ans, val, _u = hpi(sp.Rational(str(r)) ** 2, r)
            return res("hindi_circle_area", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "वृत्त का क्षेत्रफल = π × त्रिज्या²",
                f"= π × {fmt_num(r)}² = {ans}",
            ])
        if r and ("परिमाप" in q or "परिधि" in q):
            ans, val, _u = hpi(2 * sp.Rational(str(r)), r)
            return res("hindi_circle_circumference", ans, val,
                       ([pi_note_hi()] if _u else []) + [
                "वृत्त का परिमाप (परिधि) = 2 × π × त्रिज्या",
                f"= 2 × π × {fmt_num(r)} = {ans}",
            ])
    # Square: perimeter or area.
    if "वर्ग" in q:
        s = _hnear(q, "भुजा")
        if s and "परिमाप" in q:
            return res("hindi_square_perimeter", fmt_num(4 * s),
                       4 * s, [
                           "वर्ग का परिमाप = 4 × भुजा",
                           f"= 4 × {fmt_num(s)} = {fmt_num(4 * s)}",
                       ])
        if s and "क्षेत्रफल" in q:
            return res("hindi_square_area", fmt_num(s * s), s * s, [
                "वर्ग का क्षेत्रफल = भुजा²",
                f"= {fmt_num(s)}² = {fmt_num(s * s)}",
            ])
    # Rectangle area (लंबाई and चौड़ाई both required — आयत is a
    # substring of आयतन, so the shape word alone is not a gate).
    if "लंबाई" in q and "चौड़ाई" in q and "क्षेत्रफल" in q:
        ln, br = _hnear(q, "लंबाई"), _hnear(q, "चौड़ाई")
        if ln and br:
            return res("hindi_rectangle_area", fmt_num(ln * br),
                       ln * br, [
                           "आयत का क्षेत्रफल = लंबाई × चौड़ाई",
                           f"= {fmt_num(ln)} × {fmt_num(br)} "
                           f"= {fmt_num(ln * br)}",
                       ])
    # Triangle area from base and height.
    if "त्रिभुज" in q and "क्षेत्रफल" in q:
        b, h = _hnear(q, "आधार"), _hnear(q, "ऊंचाई")
        if b and h:
            return res("hindi_triangle_area", fmt_num(b * h / 2),
                       b * h / 2, [
                           "त्रिभुज का क्षेत्रफल = (1/2) × आधार "
                           "× ऊंचाई",
                           f"= (1/2) × {fmt_num(b)} × {fmt_num(h)} "
                           f"= {fmt_num(b * h / 2)}",
                       ])
    # Triangle: third angle from two given angles.
    if "त्रिभुज" in q and "तीसरा कोण" in q:
        angs = re.findall(r"(" + _NUM + r")\s*डिग्री", q)
        if len(angs) >= 2:
            a, b = float(angs[0]), float(angs[1])
            third = 180.0 - a - b
            return res("hindi_triangle_third_angle",
                       f"{fmt_num(third)}°", third, [
                           "त्रिभुज के तीनों कोणों का योग 180° "
                           "होता है।",
                           f"तीसरा कोण = 180 − {fmt_num(a)} − "
                           f"{fmt_num(b)} = {fmt_num(third)}°",
                       ])
    # Simple interest: "P रुपये का T वर्ष के लिए R% वार्षिक दर
    # से साधारण ब्याज".
    if "साधारण ब्याज" in q:
        m = re.search(r"(" + _NUM + r")\s*रुपये\s*का\s*("
                      + _NUM + r")\s*वर्ष[\s\S]{0,30}?("
                      + _NUM + r")\s*%", q)
        if m:
            P, T, R = (float(m.group(i)) for i in (1, 2, 3))
            si = P * R * T / 100.0
            return res("hindi_simple_interest", fmt_num(si), si, [
                "साधारण ब्याज = मूलधन × दर × समय / 100",
                f"= {fmt_num(P)} × {fmt_num(R)} × {fmt_num(T)} "
                f"/ 100 = {fmt_num(si)}",
            ])
    # Percentage of a number: "240 का 25 प्रतिशत".
    m = re.search(r"(" + _NUM + r")\s*का\s*(" + _NUM
                  + r")\s*प्रतिशत", q)
    if m:
        base, pct = float(m.group(1)), float(m.group(2))
        v = base * pct / 100.0
        return res("hindi_percent_of", fmt_num(v), v, [
            f"{fmt_num(pct)} प्रतिशत = {fmt_num(pct)}/100",
            f"{fmt_num(base)} × {fmt_num(pct)}/100 "
            f"= {fmt_num(v)}",
        ])
    # Tower height from the angle of elevation (उन्नयन कोण).
    if "मीनार" in q and "उन्नयन कोण" in q:
        md = re.search(r"(" + _NUM + r")\s*(?:m|मीटर)\s*दूर", q)
        ma = re.search(r"उन्नयन कोण\s*(" + _NUM + r")", q)
        if md and ma:
            d, a = float(md.group(1)), float(ma.group(1))
            h = float(sp.tan(sp.Rational(a) * sp.pi / 180)) * d
            return res("hindi_tower_height", fmt_num(h), h, [
                "tan(उन्नयन कोण) = मीनार की ऊंचाई / दूरी",
                f"ऊंचाई = {fmt_num(d)} × tan({fmt_num(a)}°) "
                f"= {fmt_num(h)}",
            ])
    # "एक संख्या के तीन गुने में 7 जोड़ने पर 40 प्राप्त होता है"
    if "गुने" in q and "संख्या" in q:
        mults = {"दो": 2, "तीन": 3, "चार": 4, "पाँच": 5,
                 "पांच": 5, "छह": 6, "सात": 7, "आठ": 8,
                 "नौ": 9, "दस": 10}
        m = re.search(r"(दो|तीन|चार|पाँच|पांच|छह|सात|आठ|नौ|दस|"
                      + _NUM + r")\s*गुने\s*में\s*(" + _NUM
                      + r")\s*(जोड़ने|घटाने)\s*पर\s*(" + _NUM
                      + r")", q)
        if m:
            mult = mults.get(m.group(1))
            if mult is None:
                mult = float(m.group(1))
            k, tot = float(m.group(2)), float(m.group(4))
            x = (tot - k) / mult if m.group(3) == "जोड़ने" \
                else (tot + k) / mult
            xf = Fraction(x).limit_denominator(1000)
            return res("hindi_linear_equation",
                       fmt_num(float(xf)), float(xf), [
                           f"माना संख्या = x, तो {fmt_num(mult)}x "
                           f"{'+' if m.group(3) == 'जोड़ने' else '−'} "
                           f"{fmt_num(k)} = {fmt_num(tot)}",
                           f"x = {fmt_num(float(xf))}",
                       ])
    # Train: time from speed and distance. The gate is the
    # direct ask form ONLY — "रेलगाड़ी V km/h की चाल से D km
    # की दूरी कितने समय में…" — because the speed-increase
    # quadratic stories (battery #450-452: "…चाल 5 km/h अधिक
    # होती, तो 1 घंटा कम समय… चाल ज्ञात कीजिए") also contain
    # रेलगाड़ी + समय + a km/h figure, and reading that figure
    # as the speed answers 360/5 = 72 for a 40 km/h question.
    if "रेलगाड़ी" in q and "कितने समय" in q:
        mv = re.search(r"(" + _NUM + r")\s*km/h\s*की\s*चाल"
                       r"\s*से", q)
        md = re.search(r"(" + _NUM + r")\s*km\s*की\s*दूरी", q)
        if mv and md and float(mv.group(1)) > 0:
            v, d = float(mv.group(1)), float(md.group(1))
            t = d / v
            return res("hindi_train_time", fmt_num(t), t, [
                "समय = दूरी / चाल",
                f"= {fmt_num(d)} / {fmt_num(v)} = {fmt_num(t)} "
                f"घंटे",
            ])
    return None


# ---------------------------------------------------------- Wave 56
# METHOD-FIRST families (Suraj's strategy: one general
# method per question family, any numbers — the schemas
# below parse the family's variable slots and solve
# symbolically/numerically; each is property-tested on 20+
# fresh random instances in test/test_wave56_fixes.py).

_COUNT56 = {"two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8}


def _consecutive_sum(q):
    """Sum of n consecutive (even/odd) integers is S."""
    m = re.search(
        r"sum\s+of\s+(?:the\s+)?(\d+|two|three|four|five|six|"
        r"seven|eight)\s+consecutive\s+(even\s+|odd\s+)?"
        r"(?:integers|numbers|terms)", q)
    if not m:
        return None
    n = int(m.group(1)) if m.group(1).isdigit() \
        else _COUNT56[m.group(1)]
    step = 2 if m.group(2) else 1
    ms = re.search(r"\bis\s+(-?" + _NUM + r")", q[m.end():]) \
        or re.search(r"\bis\s+(-?" + _NUM + r")", q)
    if not ms or n < 2:
        return None
    S = _num(ms.group(1))
    first = S / n - (n - 1) * step / 2
    if abs(first - round(first)) > 1e-9:
        return None
    first = int(round(first))
    if m.group(2) == "even " and first % 2 != 0:
        return None
    if m.group(2) == "odd " and first % 2 == 0:
        return None
    terms = [first + i * step for i in range(n)]
    kind = (m.group(2) or "").strip()
    steps = [
        f"Let the {n} consecutive {kind + ' ' if kind else ''}"
        f"integers start at x: their sum is {n}x + "
        f"{step * n * (n - 1) // 2} = {fmt_num(S)}",
        f"x = {first}, so the integers are "
        + ", ".join(str(t) for t in terms),
    ]
    if "largest" in q or "greatest" in q or "biggest" in q:
        ans, val = str(terms[-1]), terms[-1]
    elif "smallest" in q or "least" in q:
        ans, val = str(terms[0]), terms[0]
    elif "middle" in q and n % 2 == 1:
        ans, val = str(terms[n // 2]), terms[n // 2]
    else:
        ans = ", ".join(str(t) for t in terms)
        val = terms
    return {"type": "applied", "op": "consecutive_sum",
            "answer": ans, "steps": steps, "value": val}


def _item_cost(q):
    """Two bundle prices for the same two items -> unit cost.
    "cost of 5 pens and 3 pencils is Rs 115; cost of 3 pens
    and 5 pencils is Rs 85; cost of one pen?" A 2x2 linear
    system — any items, any counts, any prices."""
    from fractions import Fraction as _F56
    rows = []
    for m in re.finditer(
            r"cost\s+of\s+(" + _NUM + r")\s+([a-z]+)\s+and\s+("
            + _NUM + r")\s+([a-z]+)\s+is\s+(?:" + _RS
            + r"\s*)?(" + _NUM + r")", q):
        rows.append(m)
    # Wave 56: the same family stated the other way round —
    # "3 pens and 5 pencils cost Rs 100" (verb form, no
    # leading "The cost of").
    for m in re.finditer(
            r"(" + _NUM + r")\s+([a-z]+)\s+and\s+(" + _NUM
            + r")\s+([a-z]+)\s+cost\s+(?:" + _RS + r"\s*)?("
            + _NUM + r")", q):
        rows.append(m)

    def _norm(w):
        return w[:-1] if w.endswith("s") and len(w) > 2 else w

    parsed = []
    for m in rows:
        parsed.append((_F56(m.group(1)), _norm(m.group(2)),
                       _F56(m.group(3)), _norm(m.group(4)),
                       _F56(m.group(5))))
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            a1, x1, b1, y1, t1 = parsed[i]
            a2, x2, b2, y2, t2 = parsed[j]
            if {x1, y1} != {x2, y2} or x1 == y1:
                continue
            if x2 != x1:  # align item order
                a2, b2 = b2, a2
                x2, y2 = y2, x2
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = (t1 * b2 - t2 * b1) / det
            py = (a1 * t2 - a2 * t1) / det
            if px <= 0 or py <= 0:
                continue
            prices = {x1: px, y1: py}
            steps = [
                f"Let one {x1} cost Rs x and one {y1} cost "
                f"Rs y: {fmt_num(a1)}x + {fmt_num(b1)}y = "
                f"{fmt_num(t1)} and {fmt_num(a2)}x + "
                f"{fmt_num(b2)}y = {fmt_num(t2)}",
                f"Solving the two equations: x = "
                f"{fmt_num(px)}, y = {fmt_num(py)}",
            ]
            ma = re.search(r"cost\s+of\s+(?:one|a|1)\s+"
                           r"([a-z]+)", q)
            if ma and _norm(ma.group(1)) in prices:
                it = _norm(ma.group(1))
                return {"type": "applied", "op": "item_cost",
                        "answer": f"Rs {fmt_num(prices[it])}",
                        "steps": steps,
                        "value": float(prices[it])}
            mc = re.search(
                r"cost\s+of\s+(" + _NUM + r")\s+([a-z]+)\s+"
                r"and\s+(" + _NUM + r")\s+([a-z]+)\s*"
                r"(?:\?|\.|$)", q)
            if mc and _norm(mc.group(2)) in prices \
                    and _norm(mc.group(4)) in prices:
                tot = (_F56(mc.group(1))
                       * prices[_norm(mc.group(2))]
                       + _F56(mc.group(3))
                       * prices[_norm(mc.group(4))])
                steps.append(
                    f"Cost of {mc.group(1)} "
                    f"{mc.group(2)} and {mc.group(3)} "
                    f"{mc.group(4)} = Rs {fmt_num(tot)}")
                return {"type": "applied", "op": "item_cost",
                        "answer": f"Rs {fmt_num(tot)}",
                        "steps": steps, "value": float(tot)}
            return {"type": "applied", "op": "item_cost",
                    "answer": f"One {x1} costs Rs "
                              f"{fmt_num(px)} and one {y1} "
                              f"costs Rs {fmt_num(py)}",
                    "steps": steps,
                    "value": [float(px), float(py)]}
    return None


def _fraction_word(q):
    """Fraction from a shift + a numerator/denominator gap:
    "becomes P/Q when K is added to both; the numerator is
    D less than the denominator". Solves the linear
    equation for any P, Q, K, D."""
    mb = re.search(
        r"becomes\s+(" + _NUM + r")\s*/\s*(" + _NUM + r")"
        r"\s+when\s+(" + _NUM + r")\s+is\s+(added\s+to|"
        r"subtracted\s+from)\s+both", q)
    if not mb:
        return None
    P, Q = sp.Rational(mb.group(1)), sp.Rational(mb.group(2))
    K = sp.Rational(mb.group(3))
    shift = K if mb.group(4).startswith("added") else -K
    D = None
    mr = re.search(r"numerator\s+is\s+(" + _NUM + r")\s+"
                   r"(less|more)\s+than\s+the\s+denominator", q)
    if mr:
        D = sp.Rational(mr.group(1)) \
            * (1 if mr.group(2) == "less" else -1)
    else:
        mr2 = re.search(r"denominator\s+is\s+(" + _NUM + r")"
                        r"\s+more\s+than\s+the\s+numerator", q)
        if mr2:
            D = sp.Rational(mr2.group(1))
    if D is None or Q == P:
        return None
    # (x - D + s) / (x + s) = P/Q  ->  x(Q - P) = Q(D - s) + Ps
    x = (Q * (D - shift) + P * shift) / (Q - P)
    n_ = x - D
    if x <= 0 or n_ <= 0 or x.q != 1 or n_.q != 1:
        return None
    frac = sp.Rational(n_, x)
    steps = [
        f"Let the denominator be x; the numerator is "
        f"x - {fmt_num(D)}.",
        f"Adding {fmt_num(shift)} to both: "
        f"(x - {fmt_num(D)} + {fmt_num(shift)}) / "
        f"(x + {fmt_num(shift)}) = {fmt_num(P)}/{fmt_num(Q)}",
        f"Cross-multiplying and solving gives x = "
        f"{fmt_num(x)}, so the numerator is {fmt_num(n_)}.",
    ]
    return {"type": "applied", "op": "fraction_word",
            "answer": f"{frac.p}/{frac.q}" if frac.q != 1
            else str(frac.p),
            "steps": steps, "value": float(frac)}


def _percent_change(q):
    """Percentage increase / decrease from A to B:
    change / original x 100 — "rises from Rs 400 to
    Rs 460", "marks increased from 60 to 75", "falls from
    80 to 60"."""
    if "percent" not in q:
        return None
    m = re.search(r"(?:rises?|rose|increases?|increased|"
                  r"goes\s+up|grew|grows)\s+from\s+(?:"
                  + _RS + r"\s*)?(" + _NUM + r")\s+to\s+(?:"
                  + _RS + r"\s*)?(" + _NUM + r")", q)
    if m:
        A, B = _num(m.group(1)), _num(m.group(2))
        if A > 0 and B >= A:
            v = (B - A) / A * 100.0
            return {"type": "applied", "op": "percent_increase",
                    "answer": f"{fmt_num(round(v, 2))}%",
                    "steps": [
                        f"Increase = {fmt_num(B)} - "
                        f"{fmt_num(A)} = {fmt_num(B - A)}",
                        f"Percentage increase = "
                        f"{fmt_num(B - A)} / {fmt_num(A)} × "
                        f"100 = {fmt_num(round(v, 2))}%"],
                    "value": v}
    m = re.search(r"(?:falls?|fell|decreases?|decreased|"
                  r"drops?|dropped|goes\s+down|reduces?|"
                  r"reduced)\s+from\s+(?:" + _RS + r"\s*)?("
                  + _NUM + r")\s+to\s+(?:" + _RS + r"\s*)?("
                  + _NUM + r")", q)
    if m:
        A, B = _num(m.group(1)), _num(m.group(2))
        if A > 0 and B <= A:
            v = (A - B) / A * 100.0
            return {"type": "applied", "op": "percent_decrease",
                    "answer": f"{fmt_num(round(v, 2))}%",
                    "steps": [
                        f"Decrease = {fmt_num(A)} - "
                        f"{fmt_num(B)} = {fmt_num(A - B)}",
                        f"Percentage decrease = "
                        f"{fmt_num(A - B)} / {fmt_num(A)} × "
                        f"100 = {fmt_num(round(v, 2))}%"],
                    "value": v}
    return None


def _growth_decay(q):
    """Population growth / depreciation — compound-change
    schemas with CI maths but their own wording (no
    "compound interest" anywhere)."""
    mr = re.search(r"(" + _NUM + r")\s*%\s*(?:per\s+(?:annum|"
                   r"year)|annually)", q) or re.search(
                       r"rate\s+of\s+(" + _NUM + r")\s*%", q)
    mt = re.search(r"after\s+(" + _NUM + r")\s+years?", q)
    if "population" in q and mr and mt:
        mp = re.search(r"population\s+(?:of\s+[^.]{0,40}?)?"
                       r"is\s+(" + _NUM + r")", q)
        if mp:
            P, R, T = _num(mp.group(1)), _num(mr.group(1)), \
                _num(mt.group(1))
            sign = -1.0 if ("decreas" in q or "declin" in q) \
                else 1.0
            val = P * (1 + sign * R / 100.0) ** T
            steps = [
                f"Population changes by {fmt_num(R)}% every "
                f"year, so after {fmt_num(T)} years it is "
                f"multiplied by (1 {'+' if sign > 0 else '-'} "
                f"{fmt_num(R)}/100)^{fmt_num(T)}.",
                f"= {fmt_num(P)} × "
                f"{fmt_num((1 + sign * R / 100.0) ** T)} = "
                f"{fmt_num(round(val, 2))}",
            ]
            return {"type": "applied", "op": "population_change",
                    "answer": fmt_num(round(val, 2)),
                    "steps": steps, "value": val}
    if "deprecia" in q and mt:
        mv = re.search(r"(?:value|price|cost)\s+of\s+"
                       r"[^.]{0,40}?\bis\s+(?:" + _RS + r"\s*)?("
                       + _NUM + r")", q) or re.search(
                           r"worth\s+(?:" + _RS + r"\s*)?("
                           + _NUM + r")", q)
        mr2 = mr or re.search(r"deprecia\w*[^.]{0,25}?("
                              + _NUM + r")\s*%", q)
        if mv and mr2:
            P, R, T = _num(mv.group(1)), _num(mr2.group(1)), \
                _num(mt.group(1))
            val = P * (1 - R / 100.0) ** T
            steps = [
                f"The value falls by {fmt_num(R)}% every "
                f"year: after {fmt_num(T)} years it is "
                f"{fmt_num(P)} × (1 - {fmt_num(R)}/100)^"
                f"{fmt_num(T)}.",
                f"= Rs {fmt_num(round(val, 2))}",
            ]
            return {"type": "applied", "op": "depreciation",
                    "answer": f"Rs {fmt_num(round(val, 2))}",
                    "steps": steps, "value": val}
    return None


def _si_doubles(q):
    """At simple interest a sum becomes k times itself:
    SI = (k-1)P, so rate = 100(k-1)/T and time =
    100(k-1)/R."""
    if "simple interest" not in q:
        return None
    mult = None
    if re.search(r"\bdoubles?\b", q) or "two times" in q \
            or "twice" in q:
        mult = 2.0
    elif re.search(r"\btriples?\b", q) or "three times" in q:
        mult = 3.0
    elif "four times" in q or "quadruple" in q:
        mult = 4.0
    elif "five times" in q:
        mult = 5.0
    else:
        mk = re.search(r"becomes\s+(" + _NUM + r")\s+times", q)
        if mk:
            mult = _num(mk.group(1))
    if not mult or mult <= 1:
        return None
    mt = re.search(r"\bin\s+(" + _NUM + r")\s+years?\b", q)
    mr = re.search(r"(?:at|rate\s+of)\s+(" + _NUM + r")\s*%",
                   q)
    if ("how many years" in q or "in what time" in q) and mr:
        R = _num(mr.group(1))
        if R <= 0:
            return None
        T = 100 * (mult - 1) / R
        steps = [
            f"For the sum to become {fmt_num(mult)} times "
            f"itself, the interest must be "
            f"{fmt_num(mult - 1)} × the principal.",
            f"SI = P × R × T / 100 gives T = 100 × "
            f"{fmt_num(mult - 1)} / {fmt_num(R)} = "
            f"{fmt_num(T)} years",
        ]
        return {"type": "applied", "op": "si_doubles_time",
                "answer": f"{fmt_num(T)} years", "steps": steps,
                "value": T}
    if mt and "rate" in q:
        T = _num(mt.group(1))
        if T <= 0:
            return None
        R = 100 * (mult - 1) / T
        steps = [
            f"For the sum to become {fmt_num(mult)} times "
            f"itself in {fmt_num(T)} years, the interest "
            f"earned is {fmt_num(mult - 1)} × the principal.",
            f"SI = P × R × T / 100 gives R = 100 × "
            f"{fmt_num(mult - 1)} / {fmt_num(T)} = "
            f"{fmt_num(R)}%",
        ]
        return {"type": "applied", "op": "si_doubles_rate",
                "answer": f"{fmt_num(R)}%", "steps": steps,
                "value": R}
    return None


def _angle_word(q):
    """Angle word schemas: triangle angles in a ratio,
    complement / supplement (plain, equal, k-times), and
    the exterior-angle theorem."""
    # Wave 65: \bangle — "angle" is a substring of "triangle".
    if "triangle" in q and "ratio" in q \
            and re.search(r"\bangles?\b", q):
        mp = re.search(r"ratio\s+(\d+(?:\s*:\s*\d+)+)", q)
        if mp:
            parts = [int(p) for p in mp.group(1).split(":")]
            if len(parts) == 3:
                s = sum(parts)
                angles = [180.0 * p / s for p in parts]
                steps = [
                    f"The angles are {parts[0]}x, {parts[1]}x "
                    f"and {parts[2]}x, and the angles of a "
                    f"triangle add to 180°: {s}x = 180°, so "
                    f"x = {fmt_num(180.0 / s)}°",
                    "The angles are "
                    + ", ".join(fmt_num(a) + "°"
                                for a in angles),
                ]
                if "largest" in q or "greatest" in q \
                        or "biggest" in q:
                    return {"type": "applied",
                            "op": "triangle_angles_ratio",
                            "answer": f"{fmt_num(max(angles))}°",
                            "steps": steps,
                            "value": max(angles)}
                if "smallest" in q or "least" in q:
                    return {"type": "applied",
                            "op": "triangle_angles_ratio",
                            "answer": f"{fmt_num(min(angles))}°",
                            "steps": steps,
                            "value": min(angles)}
                return {"type": "applied",
                        "op": "triangle_angles_ratio",
                        "answer": ", ".join(
                            fmt_num(a) + "°" for a in angles),
                        "steps": steps, "value": angles}
    # "twice/thrice its complement" is the k-times form
    # with its own words (no "times" follows them).
    _mtw = re.search(r"angle\s+is\s+(twice|thrice)\s+its\s+"
                     r"(complement|supplement)", q)
    if _mtw:
        _k = 2.0 if _mtw.group(1) == "twice" else 3.0
        _base = 90.0 if _mtw.group(2) == "complement" \
            else 180.0
        _x = _base * _k / (_k + 1)
        return {"type": "applied",
                "op": "angle_times_complement",
                "answer": f"{fmt_num(_x)}°",
                "steps": [
                    f"Let the angle be x. Its "
                    f"{_mtw.group(2)} is {fmt_num(_base)} - "
                    f"x, and x = {fmt_num(_k)} × "
                    f"({fmt_num(_base)} - x).",
                    f"Solving: x = {fmt_num(_x)}°"],
                "value": _x}
    m = re.search(r"angle\s+is\s+(" + _NUM + r"|one|two|three|"
                  r"four|five|six|seven|eight|nine|ten)\s+times"
                  r"\s+its\s+(complement|supplement)", q)
    if m:
        _wn = {"one": 1, "two": 2, "three": 3, "four": 4,
               "five": 5, "six": 6, "seven": 7, "eight": 8,
               "nine": 9, "ten": 10}
        k = _num(m.group(1)) if m.group(1)[0].isdigit() \
            else float(_wn[m.group(1)])
        base = 90.0 if m.group(2) == "complement" else 180.0
        x = base * k / (k + 1)
        steps = [
            f"Let the angle be x. Its {m.group(2)} is "
            f"{fmt_num(base)} - x, and x = {fmt_num(k)} × "
            f"({fmt_num(base)} - x).",
            f"Solving: x = {fmt_num(x)}°",
        ]
        return {"type": "applied", "op": "angle_times_complement",
                "answer": f"{fmt_num(x)}°", "steps": steps,
                "value": x}
    if "complementary" in q and "equal" in q:
        return {"type": "applied", "op": "angles_equal_complement",
                "answer": "45°",
                "steps": ["Complementary angles add to 90°. "
                          "Equal angles are each 90° / 2 = 45°."],
                "value": 45.0}
    # The two acute angles of a right triangle are
    # complementary — equal ones are 45° each.
    if "right" in q and "acute" in q and "equal" in q \
            and "triangle" in q:
        return {"type": "applied", "op": "angles_equal_complement",
                "answer": "45°",
                "steps": ["The acute angles of a right "
                          "triangle add to 90° (the third "
                          "angle is 90°). Equal angles are "
                          "each 90° / 2 = 45°."],
                "value": 45.0}
    if "supplementary" in q and "equal" in q:
        return {"type": "applied",
                "op": "angles_equal_supplement",
                "answer": "90°",
                "steps": ["Supplementary angles add to 180°. "
                          "Equal angles are each 180° / 2 = 90°."],
                "value": 90.0}
    m = re.search(r"complement(?:ary)?\s+(?:angle\s+)?of\s+"
                  r"(?:an\s+angle\s+of\s+|the\s+angle\s+of\s+)?"
                  r"(" + _NUM + r")", q)
    if m:
        A = _num(m.group(1))
        if 0 <= A < 90:
            return {"type": "applied", "op": "complement",
                    "answer": f"{fmt_num(90 - A)}°",
                    "steps": [f"Complementary angles add to "
                              f"90°, so the complement of "
                              f"{fmt_num(A)}° is 90° - "
                              f"{fmt_num(A)}° = "
                              f"{fmt_num(90 - A)}°"],
                    "value": 90 - A}
    m = re.search(r"supplement(?:ary)?\s+(?:angle\s+)?of\s+"
                  r"(?:an\s+angle\s+of\s+|the\s+angle\s+of\s+)?"
                  r"(" + _NUM + r")", q)
    if m:
        A = _num(m.group(1))
        if 0 <= A < 180:
            return {"type": "applied", "op": "supplement",
                    "answer": f"{fmt_num(180 - A)}°",
                    "steps": [f"Supplementary angles add to "
                              f"180°, so the supplement of "
                              f"{fmt_num(A)}° is 180° - "
                              f"{fmt_num(A)}° = "
                              f"{fmt_num(180 - A)}°"],
                    "value": 180 - A}
    if "exterior" in q and "interior" in q and "other" in q:
        me = re.search(r"exterior\s+angle[^.]{0,40}?\bis\s+("
                       + _NUM + r")", q)
        mi = re.search(r"interior\s+angles?\s+is\s+(" + _NUM
                       + r")", q)
        if me and mi:
            E, I = _num(me.group(1)), _num(mi.group(1))
            if E > I:
                return {"type": "applied", "op": "exterior_angle",
                        "answer": f"{fmt_num(E - I)}°",
                        "steps": [
                            "An exterior angle equals the sum "
                            "of the two remote interior angles.",
                            f"Other interior angle = "
                            f"{fmt_num(E)}° - {fmt_num(I)}° = "
                            f"{fmt_num(E - I)}°"],
                        "value": E - I}
    return None


def _temperature(q):
    """Start temperature +/- a rise or fall."""
    if "temperature" not in q:
        return None
    mb = re.search(r"temperature[^.]{0,40}?(-?" + _NUM + r")"
                   r"\s*(?:°|degrees?|c\b)", q)
    if not mb:
        return None
    base = _num(mb.group(1))
    mr = re.search(r"(?:rose|rises|increased|went\s+up)\s+by"
                   r"\s+(" + _NUM + r")", q)
    mf = re.search(r"(?:fell|falls|dropped|decreased|went"
                   r"\s+down)\s+by\s+(" + _NUM + r")", q)
    if mr:
        val = base + _num(mr.group(1))
        steps = [f"The temperature rose by "
                 f"{fmt_num(_num(mr.group(1)))}° from "
                 f"{fmt_num(base)}°: {fmt_num(base)} + "
                 f"{fmt_num(_num(mr.group(1)))} = "
                 f"{fmt_num(val)}"]
        return {"type": "applied", "op": "temperature",
                "answer": f"{fmt_num(val)}°C", "steps": steps,
                "value": val}
    if mf:
        val = base - _num(mf.group(1))
        steps = [f"The temperature fell by "
                 f"{fmt_num(_num(mf.group(1)))}° from "
                 f"{fmt_num(base)}°: {fmt_num(base)} - "
                 f"{fmt_num(_num(mf.group(1)))} = "
                 f"{fmt_num(val)}"]
        return {"type": "applied", "op": "temperature",
                "answer": f"{fmt_num(val)}°C", "steps": steps,
                "value": val}
    return None


def _cuboid_capacity(q):
    """Wave 74: cuboid volume / capacity from dimension
    words — "a water tank is 80 cm long, 40 cm wide and
    40 cm deep, how many litres of water can it hold?" No
    earlier family claimed the long/wide/deep phrasing
    (geometry's cuboid branch needs the word "cuboid"),
    so the question fell through to the equation salvage
    and its "(1000 cm^3 = 1 litre)" hint was "solved" as
    an equation (Wave 71 audit, wrong case 2). Reads the
    three dimension slots in either order ("80 cm long" /
    "length is 80 cm"), each with its own unit or the
    unit its neighbours share, and answers the volume —
    in litres when litres / capacity are asked
    (1000 cm^3 = 1 litre)."""
    if not re.search(r"litres?|liters?|capacity|volume|"
                     r"hold", q):
        return None

    def _dim(*words):
        for w in words:
            m = re.search(r"(\d+(?:\.\d+)?)\s*(cm|mm|m)?\s*"
                          + w + r"\b", q)
            if m:
                return float(m.group(1)), m.group(2)
            m = re.search(w + r"\s*(?:is\s*)?(\d+(?:\.\d+)?)"
                          r"\s*(cm|mm|m)?\b", q)
            if m:
                return float(m.group(1)), m.group(2)
        return None

    dims = (_dim("long", "length"), _dim("wide", "breadth",
                                         "width"),
            _dim("deep", "depth", "high", "height"))
    if any(d is None for d in dims):
        return None
    shared = next((u for _, u in dims if u), None)
    if shared is None:
        return None  # no unit anywhere: cannot convert
    _to_cm = {"cm": 1.0, "m": 100.0, "mm": 0.1}
    cms = [v * _to_cm[u or shared] for v, u in dims]
    vol = cms[0] * cms[1] * cms[2]
    steps = [f"Volume of a cuboid = length × breadth × "
             f"height",
             f"= {fmt_num(cms[0])} × {fmt_num(cms[1])} × "
             f"{fmt_num(cms[2])} = {fmt_num(vol)} cm³"]
    if re.search(r"litres?|liters?|capacity|hold", q):
        litres = vol / 1000.0
        steps.append(f"1000 cm³ = 1 litre, so capacity = "
                     f"{fmt_num(vol)} ÷ 1000 = "
                     f"{fmt_num(litres)} litres")
        return {"type": "applied", "op": "cuboid_capacity",
                "answer": f"{fmt_num(litres)} litres",
                "steps": steps, "value": litres}
    return {"type": "applied", "op": "cuboid_volume_dims",
            "answer": f"{fmt_num(vol)} cm³",
            "steps": steps, "value": vol}


def _wrapped_equation(q, op_name):
    """Wave 56: an equation stated inside a Hindi / Hinglish
    wrapper — "समीकरण 3x - 4 = 11 को हल कीजिए",
    "x + 15 = 40 me x ki value kitni hai",
    "x^2 - 5x + 6 = 0 ke roots batao". The wrapper words
    become letter-soup in the algebra parser, so extract
    the equation itself (LHS in x, RHS a plain number) and
    hand it to the algebra solver; the wrapper determines
    nothing else."""
    if not any(w in q for w in ("हल", "ज्ञात", "बताओ",
                                 "मूल", "batao", "btaao",
                                 "bataao", "bataiye", "nikalo",
                                 "nikaalo",
                                 "value", "root", "solve")):
        return None
    m = re.search(
        r"((?:[a-z]|\d)\s*[0-9a-z\s+\-*/^().]*?=\s*-?"
        r"\d+(?:\.\d+)?(?:\s*/\s*\d+)?)", q)
    if not m:
        return None
    eq = m.group(1).strip()
    if eq.count("=") != 1 or not re.search(r"[a-z]", eq):
        return None
    # Wave 74: a unit-conversion statement is not an
    # equation. The "(1000 cm^3 = 1 litre)" hint inside a
    # capacity question used to be extracted here and
    # "solved" for the letter c of "cm", answering
    # "c = 1/(1000·m^3)" (Wave 71 audit, wrong case 2). A
    # real wrapped equation — this schema's own contract —
    # has ONE unknown letter on its LHS; a measurement
    # statement's letters are unit symbols (the c and m of
    # cm, the k and m of km) and it carries a number+unit
    # pair. Refuse both shapes.
    _lhs74 = eq.split("=")[0]
    if len(set(re.findall(r"[a-z]", _lhs74))) != 1:
        return None
    if re.search(r"\d\s*(?:cm|mm|km|ml|kg|litres?|liters?|"
                 r"mins?|secs?|hrs?)\b", eq):
        return None
    try:
        from .algebra import solve_algebra
        out = solve_algebra(eq)
    except Exception:
        return None
    if out is None or out.get("op") in ("error", "unknown",
                                        None):
        return None
    out = dict(out)
    out["type"] = "applied"
    out["op"] = op_name
    return out


_DEV56 = str.maketrans("०१२३४५६७८९", "0123456789")
_HI_MULT56 = {"दो": 2, "तीन": 3, "चार": 4, "पाँच": 5,
              "पांच": 5, "छह": 6}


def _hindi_schemas(q):
    """Wave 56: Devanagari (Hindi-medium) word schemas.
    Before this wave a Hindi mensuration / SI / percentage
    sentence reached NO pattern at all: the expression
    parser treated the Hindi words as letter variables and
    answered letter-soup (the battery's biggest WRONG
    cluster). Each schema reads the family's slots
    (shape word + dimensions + asked quantity) and solves
    for any values. Steps stay in English (house
    convention). Pi is the app's true pi, as everywhere."""
    qt = q.translate(_DEV56)
    pi = math.pi
    # A wrapped equation ("समीकरण ... को हल कीजिए") first —
    # it is the only schema here that carries an "=".
    if "=" in qt:
        _we = _wrapped_equation(qt, "hindi_equation")
        if _we is not None:
            return _we

    def _slot(*pats):
        for pat in pats:
            m = re.search(pat, qt)
            if m:
                return _num(m.group(1))
        return None

    # Slots read both orders: "त्रिज्या 7 cm" and "7 cm
    # त्रिज्या वाले" are both standard Hindi-medium phrasing.
    _rad = lambda: _slot(r"त्रिज्या\s*(?:है\s*)?(" + _NUM + r")",
                         r"त्रिज्या\s*=\s*(" + _NUM + r")",
                         r"(" + _NUM + r")\s*(?:cm|सेमी|m|मीटर)?"
                         r"\s*त्रिज्या")
    _hgt = lambda: _slot(r"ऊ[ँं]चाई\s*(?:है\s*)?(" + _NUM + r")")
    _side = lambda: _slot(r"भुजा\s*(?:है\s*)?(" + _NUM + r")",
                          r"किनारा\s*(?:है\s*)?(" + _NUM + r")",
                          r"(" + _NUM + r")\s*(?:cm|सेमी)?\s*भुजा")
    # --- hemisphere before sphere (अर्धगोला contains गोला)
    if "अर्धगोल" in qt:
        r = _rad()
        if r and "आयतन" in qt:
            _pi, _u227, _reason = pi_choice(radius=r)
            v = 2.0 / 3.0 * _pi * r ** 3
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ([pi_note(_reason)] if _u227 else []) + [
                              "Volume of a hemisphere = "
                              "(2/3)πr³",
                              f"= (2/3) × π × {fmt_num(r)}³ = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    if "गोल" in qt and "गोलाकार" not in qt:
        r = _rad()
        if r and "आयतन" in qt:
            _pi, _u227, _reason = pi_choice(radius=r)
            v = 4.0 / 3.0 * _pi * r ** 3
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ([pi_note(_reason)] if _u227 else []) + [
                              "Volume of a sphere = (4/3)πr³",
                              f"= (4/3) × π × {fmt_num(r)}³ = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
        if r and "पृष्ठ" in qt:
            _pi, _u227, _reason = pi_choice(radius=r)
            v = 4 * _pi * r ** 2
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ([pi_note(_reason)] if _u227 else []) + [
                              "Surface area of a sphere = 4πr²",
                              f"= 4 × π × {fmt_num(r)}² = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- cuboid before cube (घनाभ contains घन)
    if "घनाभ" in qt:
        L = _slot(r"(?:लंबाई|लम्बाई)\s*(?:है\s*)?(" + _NUM + r")")
        B = _slot(r"चौड़ाई\s*(?:है\s*)?(" + _NUM + r")")
        H = _hgt()
        if L and B and H and "आयतन" in qt:
            v = L * B * H
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Volume of a cuboid = length × "
                              "breadth × height",
                              f"= {fmt_num(L)} × {fmt_num(B)} × "
                              f"{fmt_num(H)} = {fmt_num(v)}"],
                    "value": v}
    if "घन" in qt:
        a = _side()
        if a and "आयतन" in qt:
            v = a ** 3
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Volume of a cube = side³",
                              f"= {fmt_num(a)}³ = "
                              f"{fmt_num(v)}"],
                    "value": v}
        if a and "पृष्ठ" in qt:
            v = 6 * a * a
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Surface area of a cube = 6a²",
                              f"= 6 × {fmt_num(a)}² = "
                              f"{fmt_num(v)}"],
                    "value": v}
    # --- cylinder / cone
    if "बेलन" in qt:
        r, h = _rad(), _hgt()
        if r and h:
            _pi, _u227, _reason = pi_choice(radius=r)
            if "आयतन" in qt:
                v = _pi * r * r * h
                return {"type": "applied",
                        "op": "hindi_mensuration",
                        "answer": fmt_num(round(v, 2)),
                        "steps": ([pi_note(_reason)] if _u227 else []) + [
                                  "Volume of a cylinder = πr²h",
                                  f"= π × {fmt_num(r)}² × "
                                  f"{fmt_num(h)} = "
                                  f"{fmt_num(round(v, 2))}"],
                        "value": v}
            if "पृष्ठ" in qt:
                if "कुल" in qt or "संपूर्ण" in qt:
                    v = 2 * _pi * r * (r + h)
                    lab = "Total surface area = 2πr(r + h)"
                else:
                    v = 2 * _pi * r * h
                    lab = "Curved surface area = 2πrh"
                return {"type": "applied",
                        "op": "hindi_mensuration",
                        "answer": fmt_num(round(v, 2)),
                        "steps": ([pi_note(_reason)] if _u227 else []) + [
                                  lab,
                                  f"= {fmt_num(round(v, 2))}"],
                        "value": v}
    if "शंकु" in qt:
        r, h = _rad(), _hgt()
        if r and h and "आयतन" in qt:
            _pi, _u227, _reason = pi_choice(radius=r)
            v = _pi * r * r * h / 3.0
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ([pi_note(_reason)] if _u227 else []) + [
                              "Volume of a cone = (1/3)πr²h",
                              f"= (1/3) × π × {fmt_num(r)}² × "
                              f"{fmt_num(h)} = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- circle
    if "वृत्त" in qt:
        r = _rad()
        d = _slot(r"व्यास\s*(?:है\s*)?(" + _NUM + r")")
        if "परिधि" in qt or "परिमाप" in qt:
            if r:
                _pi, _u227, _reason = pi_choice(radius=r)
                v = 2 * _pi * r
                return {"type": "applied",
                        "op": "hindi_mensuration",
                        "answer": fmt_num(round(v, 2)),
                        "steps": ([pi_note(_reason)] if _u227 else []) + [
                                  "Circumference = 2πr",
                                  f"= 2 × π × {fmt_num(r)} = "
                                  f"{fmt_num(round(v, 2))}"],
                        "value": v}
            if d:
                _pi, _u227, _reason = pi_choice(diameter=d)
                v = _pi * d
                return {"type": "applied",
                        "op": "hindi_mensuration",
                        "answer": fmt_num(round(v, 2)),
                        "steps": ([pi_note(_reason)] if _u227 else []) + [
                                  "Circumference = π × "
                                  "diameter",
                                  f"= π × {fmt_num(d)} = "
                                  f"{fmt_num(round(v, 2))}"],
                        "value": v}
        if "क्षेत्रफल" in qt:
            if r is None and d:
                r = d / 2
            if r:
                _pi, _u227, _reason = pi_choice(radius=r)
                v = _pi * r * r
                return {"type": "applied",
                        "op": "hindi_mensuration",
                        "answer": fmt_num(round(v, 2)),
                        "steps": ([pi_note(_reason)] if _u227 else []) + [
                                  "Area of a circle = πr²",
                                  f"= π × {fmt_num(r)}² = "
                                  f"{fmt_num(round(v, 2))}"],
                        "value": v}
    # --- a number whose square / cube is given ("संख्या
    # का वर्ग 625 है") -> the root
    if "संख्या" in qt and "वर्ग" in qt:
        m = re.search(r"वर्ग\s*(" + _NUM + r")", qt)
        if m:
            v = math.sqrt(_num(m.group(1)))
            return {"type": "applied", "op": "hindi_root",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["The number is the square root "
                              "of the given square.",
                              f"√{fmt_num(_num(m.group(1)))} = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- square
    if "वर्ग" in qt:
        a = _side()
        if a and "परिमाप" in qt:
            v = 4 * a
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Perimeter of a square = 4 × "
                              "side",
                              f"= 4 × {fmt_num(a)} = "
                              f"{fmt_num(v)}"],
                    "value": v}
        if a and "क्षेत्रफल" in qt:
            v = a * a
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Area of a square = side²",
                              f"= {fmt_num(a)}² = "
                              f"{fmt_num(v)}"],
                    "value": v}
        mA = re.search(r"क्षेत्रफल\s*(?:है\s*)?(" + _NUM + r")",
                       qt)
        if mA and "भुजा" in qt and "ज्ञात" in qt:
            v = math.sqrt(_num(mA.group(1)))
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Side = √(area)",
                              f"= √{fmt_num(_num(mA.group(1)))} "
                              f"= {fmt_num(round(v, 2))}"],
                    "value": v}
    # --- triangle: area from base/height; third angle
    if "त्रिभुज" in qt:
        if "तीसरा" in qt and "कोण" in qt:
            angs = [_num(x) for x in re.findall(
                r"(" + _NUM + r")\s*°", qt)]
            if len(angs) != 2:
                cand = [_num(x) for x in re.findall(
                    r"(" + _NUM + r")", qt)
                    if 0 < _num(x) < 180]
                if len(cand) == 2:
                    angs = cand
            if len(angs) == 2:
                v = 180 - angs[0] - angs[1]
                if v > 0:
                    return {"type": "applied",
                            "op": "hindi_triangle_angle",
                            "answer": fmt_num(v),
                            "steps": [
                                "The angles of a triangle add "
                                "to 180°",
                                f"Third angle = 180 - "
                                f"{fmt_num(angs[0])} - "
                                f"{fmt_num(angs[1])} = "
                                f"{fmt_num(v)}"],
                            "value": v}
        b = _slot(r"आधार\s*(?:है\s*)?(" + _NUM + r")")
        h = _hgt()
        if b and h and "क्षेत्रफल" in qt:
            v = b * h / 2
            return {"type": "applied", "op": "hindi_mensuration",
                    "answer": fmt_num(v),
                    "steps": ["Area of a triangle = "
                              "(1/2) × base × height",
                              f"= (1/2) × {fmt_num(b)} × "
                              f"{fmt_num(h)} = {fmt_num(v)}"],
                    "value": v}
    # --- simple interest. Two standard phrasings: slots
    # named ("मूलधन 5000, दर 10%, समय 2 वर्ष") and slots in
    # sentence order ("12000 रुपये का 3 वर्ष के लिए 5%
    # वार्षिक दर से साधारण ब्याज").
    if "ब्याज" in qt:
        P = _slot(r"मूलधन\s*(?:रु\.?|₹)?\s*(" + _NUM + r")",
                  r"(" + _NUM + r")\s*रुपये")
        R = _slot(r"दर\s*(?:से\s*)?(" + _NUM + r")\s*%",
                  r"(" + _NUM + r")\s*%\s*(?:वार्षिक\s*)?दर")
        T = _slot(r"(" + _NUM + r")\s*वर्ष",
                  r"समय\s*(?:है\s*)?(" + _NUM + r")")
        if P and R and T:
            v = P * R * T / 100.0
            return {"type": "applied", "op": "hindi_si",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Simple interest = PRT/100",
                              f"= {fmt_num(P)} × {fmt_num(R)} "
                              f"× {fmt_num(T)} / 100 = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- percentage of a number ("800 का 15%", or प्रतिशत
    # spelled out: "240 का 25 प्रतिशत")
    m = re.search(r"(" + _NUM + r")\s*का\s*(" + _NUM + r")"
                  r"\s*(?:%|प्रतिशत)", qt)
    if m:
        v = _num(m.group(1)) * _num(m.group(2)) / 100.0
        return {"type": "applied", "op": "hindi_percent",
                "answer": fmt_num(round(v, 2)),
                "steps": [f"{fmt_num(_num(m.group(2)))}% of "
                          f"{fmt_num(_num(m.group(1)))} = "
                          f"{fmt_num(_num(m.group(1)))} × "
                          f"{fmt_num(_num(m.group(2)))}/100 = "
                          f"{fmt_num(round(v, 2))}"],
                "value": v}
    # --- HCF / LCM of two numbers
    if "म.स." in qt or "महत्तम समापवर्तक" in qt \
            or "ल.स." in qt or "लघुत्तम" in qt:
        nums = [_num(x) for x in re.findall(r"(" + _NUM + r")",
                                            qt)]
        ints = [int(v) for v in nums if float(v).is_integer()]
        if len(ints) >= 2:
            a, b = ints[0], ints[1]
            if "म.स." in qt or "महत्तम" in qt:
                v = math.gcd(a, b)
                lab = "HCF"
            else:
                v = math.lcm(a, b)
                lab = "LCM"
            return {"type": "applied", "op": "hindi_hcf_lcm",
                    "answer": fmt_num(v),
                    "steps": [f"{lab} of {a} and {b} = {v}"],
                    "value": float(v)}
    # --- distance between two points
    m = re.search(r"\(\s*(-?" + _NUM + r")\s*,\s*(-?" + _NUM
                  + r")\s*\)\s*और\s*\(\s*(-?" + _NUM + r")\s*,"
                  r"\s*(-?" + _NUM + r")\s*\)[^.]{0,25}?दूरी",
                  qt)
    if m:
        x1, y1, x2, y2 = (_num(m.group(i)) for i in range(1, 5))
        v = math.hypot(x2 - x1, y2 - y1)
        return {"type": "applied", "op": "hindi_distance",
                "answer": fmt_num(round(v, 2)),
                "steps": ["Distance = √((x2 - x1)² + "
                          "(y2 - y1)²)",
                          f"= {fmt_num(round(v, 2))}"],
                "value": v}
    # --- height from angle of elevation
    m = re.search(r"उन्नयन\s*कोण\s*(" + _NUM + r")\s*(?:°|"
                  r"डिग्री)", qt)
    if m:
        d = _slot(r"दूरी\s*(?:है\s*)?(" + _NUM + r")",
                  r"(" + _NUM + r")\s*(?:मीटर|मी\.?)\s*दूरी",
                  r"(" + _NUM + r")\s*(?:मीटर|मी\.?|m)\s*दूर",
                  r"पाद\s*से\s*(" + _NUM + r")")
        if d:
            v = d * math.tan(math.radians(_num(m.group(1))))
            return {"type": "applied", "op": "hindi_height",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Height = distance × tan(angle "
                              "of elevation)",
                              f"= {fmt_num(d)} × tan("
                              f"{fmt_num(_num(m.group(1)))}°) = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- linear word forms
    m = re.search(r"संख्या\s*के\s*(\d+|दो|तीन|चार|पाँच|पांच|"
                  r"छह)\s*गुने\s*में\s*(" + _NUM + r")\s*"
                  r"जोड़ने\s*पर\s*(" + _NUM + r")", qt)
    if m:
        k = int(m.group(1)) if m.group(1).isdigit() \
            else _HI_MULT56[m.group(1)]
        b, R = _num(m.group(2)), _num(m.group(3))
        v = (R - b) / k
        return {"type": "applied", "op": "hindi_word_equation",
                "answer": fmt_num(v),
                "steps": [f"Let the number be x: "
                          f"{k}x + {fmt_num(b)} = {fmt_num(R)}",
                          f"x = ({fmt_num(R)} - {fmt_num(b)}) "
                          f"/ {k} = {fmt_num(v)}"],
                "value": v}
    m = re.search(r"संख्या\s*और\s*उसके\s*(दुगुने|दुगना|"
                  r"तिगुने|तिगुना)\s*का\s*योग\s*(" + _NUM
                  + r")", qt)
    if m:
        k = 2 if m.group(1).startswith("दु") else 3
        S = _num(m.group(2))
        v = S / (k + 1)
        return {"type": "applied", "op": "hindi_word_equation",
                "answer": fmt_num(v),
                "steps": [f"Let the number be x: x + {k}x = "
                          f"{fmt_num(S)}",
                          f"x = {fmt_num(S)} / {k + 1} = "
                          f"{fmt_num(v)}"],
                "value": v}
    # --- two numbers with a given sum, one k times the
    # other ("योग 90, एक संख्या दूसरी की दुगुनी, बड़ी
    # संख्या?") -> parts of (k+1)
    m = re.search(r"योग\s*(" + _NUM + r")", qt)
    if m and ("दुगुनी" in qt or "दुगुना" in qt
              or "तिगुनी" in qt or "तिगुना" in qt):
        k = 2 if ("दुगुनी" in qt or "दुगुना" in qt) else 3
        S = _num(m.group(1))
        small = S / (k + 1)
        big = S * k / (k + 1)
        if "छोटी" in qt:
            v, lab = small, "smaller"
        else:
            v, lab = big, "larger"
        return {"type": "applied", "op": "hindi_word_equation",
                "answer": fmt_num(v),
                "steps": [f"Let the smaller number be x; "
                          f"the other is {k}x. x + {k}x = "
                          f"{fmt_num(S)}",
                          f"x = {fmt_num(small)}, so the "
                          f"{lab} number is {fmt_num(v)}"],
                "value": v}
    return None


_PCT56 = r"(?:percent|pratishat|parcent|parsant|feesadi|%)"
_RUP56 = r"(?:rupay|rupaye|rupya|rs\.?|₹)"


def _hinglish_schemas(q):
    """Wave 56: Roman-Hindi (Hinglish) word schemas.
    Spelling is NOT standardised — students write batao /
    btaao, keemat / kimat, chhoot / chhut — so the patterns
    key on flexible stems (kitn*, bata*, keemat|kimat) and
    never on one exact spelling (Wave 57 builds the shared
    normalisation layer; these patterns stay valid on
    normalised text too)."""
    # --- a wrapped equation ("x + 15 = 40 me x ki value
    # kitni hai", "x^2 - 5x + 6 = 0 ke roots batao")
    if "=" in q:
        _we = _wrapped_equation(q, "hinglish_equation")
        if _we is not None:
            return _we
    # --- "144 ka square root batao" / "25 ka cube kitna
    # hota hai" / "16 ka square batao"
    m = re.search(r"(" + _NUM + r")\s+ka\s+(?:square\s*root|"
                  r"vargmool|sqrt)", q)
    if m:
        from .expression_parser import fmt as _fmt56h
        v = sp.sqrt(sp.Rational(m.group(1)))
        return {"type": "applied", "op": "hinglish_root",
                "answer": _fmt56h(v),
                "steps": [f"sqrt({fmt_num(_num(m.group(1)))}) "
                          f"= {_fmt56h(v)}"],
                "value": float(v)}
    m = re.search(r"(" + _NUM + r")\s+ka\s+cube\b", q)
    if m:
        v = _num(m.group(1)) ** 3
        return {"type": "applied", "op": "hinglish_power",
                "answer": fmt_num(v),
                "steps": [f"{fmt_num(_num(m.group(1)))} ka cube "
                          f"= {fmt_num(_num(m.group(1)))} × "
                          f"{fmt_num(_num(m.group(1)))} × "
                          f"{fmt_num(_num(m.group(1)))} = "
                          f"{fmt_num(v)}"],
                "value": v}
    m = re.search(r"(" + _NUM + r")\s+ka\s+(?:square|varg)\b",
                  q)
    if m:
        v = _num(m.group(1)) ** 2
        return {"type": "applied", "op": "hinglish_power",
                "answer": fmt_num(v),
                "steps": [f"{fmt_num(_num(m.group(1)))} ka "
                          f"square = {fmt_num(v)}"],
                "value": v}
    # --- "57 me se 29 ghatao" -> subtraction
    m = re.search(r"(" + _NUM + r")\s+me\s+se\s+(" + _NUM
                  + r")\s+gha+ta+", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        return {"type": "applied", "op": "hinglish_arith",
                "answer": fmt_num(a - b),
                "steps": [f"{fmt_num(a)} me se {fmt_num(b)} "
                          f"ghatane par = {fmt_num(a)} - "
                          f"{fmt_num(b)} = {fmt_num(a - b)}"],
                "value": a - b}
    # --- list sum: "12, 25 aur 38 ko jodne par ..."
    # Bare "jod" counts too when nothing but a solve word
    # follows it ("24, 29, 13, 32 ka jod batao") — but
    # "ko jod ke batao" stays with the normaliser's own
    # translation, which owns that form.
    mj = re.search(r"\bjod", q)
    if mj and ("jodne" in q or "jodo" in q or "jodkar" in q
               or "jodna" in q
               or re.fullmatch(
                   r"jod\w*\s*(?:batao|btaao|bataao|"
                   r"bataiye)?\s*\??\s*", q[mj.start():])):
        # Wave 59: numbers inside "(x, y)" point tuples are
        # coordinates, not addends — "bindu (1, 2) aur (3, 8)
        # ko jodne wali rekha..." (the line JOINING two
        # points) used to be summed into 14.
        _prefix = re.sub(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*"
                         r"-?\d+(?:\.\d+)?\s*\)", " ",
                         q[:mj.start()])
        nums = [_num(x) for x in re.findall(
            r"(" + _NUM + r")", _prefix)]
        if len(nums) >= 2:
            v = sum(nums)
            return {"type": "applied", "op": "hinglish_arith",
                    "answer": fmt_num(v),
                    "steps": [" + ".join(fmt_num(x) for x in nums)
                              + f" = {fmt_num(v)}"],
                    "value": v}
    # --- score percentage: "500 me se 425 ank ... percent",
    # or the part stated apart ("80 me se hai, mujhe 64
    # aaye, percentage kitna") — part/whole x 100 either way.
    if re.search(_PCT56, q):
        m = re.search(r"(" + _NUM + r")\s+me\s+se\s+(" + _NUM
                      + r")\s*(?:ank|marks?|number)?\b", q) \
            or re.search(r"(" + _NUM + r")\s+me\s+se[^.]{0,30}?"
                         r"(" + _NUM + r")\s*(?:aaye|mile|aaya|"
                         r"hua)", q)
        if m:
            whole, part = _num(m.group(1)), _num(m.group(2))
            if whole > 0 and part <= whole:
                v = part / whole * 100.0
                return {"type": "applied",
                        "op": "hinglish_percent",
                        "answer": f"{fmt_num(round(v, 2))}%",
                        "steps": [f"Percentage = "
                                  f"{fmt_num(part)} / "
                                  f"{fmt_num(whole)} × 100 = "
                                  f"{fmt_num(round(v, 2))}%"],
                        "value": v}
    # --- discount selling price. The percent may carry
    # %, percent, pratishat or parcent — or none ("10 off").
    if re.search(r"(?:discount|chhoo?t|chuth|off\b)", q):
        mpct = re.search(r"(" + _NUM + r")\s*(?:%|pratishat|"
                         r"parcent|parsant|percent)?\s*"
                         r"(?:discount|chhoo?t|chuth|off)", q) \
            or re.search(r"(?:discount|chhoo?t|chuth)\s*(?:hai\s*)?"
                         r"(" + _NUM + r")\s*(?:%|pratishat|"
                         r"parcent|percent)", q)
        mprice = re.search(r"(" + _NUM + r")\s+" + _RUP56, q) \
            or re.search(r"(?:keemat|kimat|qeemat)\s*(?:hai\s*)?"
                         r"(" + _NUM + r")", q) \
            or re.search(r"(" + _NUM + r")\s+wali?\s+\w+", q) \
            or re.search(r"(" + _NUM + r")\s+ka\s+hai", q) \
            or re.search(r"(" + _NUM + r")\s+ki\s+hai", q)
        if mpct and mprice:
            P, d = _num(mprice.group(1)), _num(mpct.group(1))
            if P > 0 and 0 <= d < 100:
                off = P * d / 100.0
                sp_ = P - off
                if "discount kitna" in q or "chhoot kitni" in q:
                    return {"type": "applied",
                            "op": "hinglish_discount",
                            "answer": f"Rs {fmt_num(off)}",
                            "steps": [f"Discount = {fmt_num(d)}%"
                                      f" of Rs {fmt_num(P)} = "
                                      f"Rs {fmt_num(off)}"],
                            "value": off}
                return {"type": "applied",
                        "op": "hinglish_discount",
                        "answer": f"Rs {fmt_num(sp_)}",
                        "steps": [
                            f"Keemat = Rs {fmt_num(P)}, "
                            f"discount = {fmt_num(d)}%",
                            f"Discount ke baad keemat = "
                            f"{fmt_num(P)} - {fmt_num(off)} = "
                            f"Rs {fmt_num(sp_)}"],
                        "value": sp_}
    # --- unitary with unit conversion (gram/kg, ml/litre)
    m = re.search(r"(" + _NUM + r")\s*(gram|g|kg|kilo|ml|"
                  r"litre|liter|l)\b[^.]{0,50}?(?:keemat|kimat|"
                  r"qeemat|daam)\s*(?:hai\s*)?(" + _NUM + r")", q)
    if m:
        _conv = {"gram": 1.0, "g": 1.0, "kg": 1000.0,
                 "kilo": 1000.0, "ml": 1.0, "litre": 1000.0,
                 "liter": 1000.0, "l": 1000.0}
        qty = _num(m.group(1)) * _conv[m.group(2)]
        price = _num(m.group(3))
        mt = re.search(r"(" + _NUM + r")\s*(kg|kilo|gram|g|"
                       r"litre|liter|ml|l)\b", q[m.end():])
        if mt and qty > 0:
            tq = _num(mt.group(1)) * _conv[mt.group(2)]
            v = price / qty * tq
            return {"type": "applied", "op": "hinglish_unitary",
                    "answer": f"Rs {fmt_num(round(v, 2))}",
                    "steps": [
                        f"{fmt_num(qty)} unit ki keemat = "
                        f"Rs {fmt_num(price)}, so 1 unit = "
                        f"Rs {fmt_num(round(price / qty, 4))}",
                        f"{fmt_num(tq)} unit ki keemat = "
                        f"Rs {fmt_num(round(v, 2))}"],
                    "value": v}
    # --- dozen pricing (count ask, or the price of ONE)
    if re.search(r"\bdozen\b|\bdarjan\b", q):
        mprice = re.search(r"(" + _NUM + r")\s*" + _RUP56, q)
        mcount = re.search(r"(" + _NUM + r")\s+\w+\s+kitn", q)
        if mprice and (mcount or re.search(
                r"\bek\b\s+\w+\s+ka\s+(?:daam|keemat|kimat)", q)):
            P = _num(mprice.group(1))
            c = _num(mcount.group(1)) if mcount else 1.0
            v = P / 12.0 * c
            return {"type": "applied", "op": "hinglish_unitary",
                    "answer": f"Rs {fmt_num(round(v, 2))}",
                    "steps": [f"1 dozen = 12, so ek ki keemat "
                              f"= {fmt_num(P)} / 12 = "
                              f"Rs {fmt_num(round(P / 12.0, 2))}",
                              f"{fmt_num(c)} ki keemat = "
                              f"Rs {fmt_num(round(v, 2))}"],
                    "value": v}
    # --- speed x time: "ek ghante me 90 km ... 4 ghante me";
    # and the bare speed ask — distance covered in ONE hour
    # IS the speed ("ek ghante me train 90 km jati hai, uski
    # speed batao").
    m = re.search(r"ek\s+ghant\w*\s+me\s+(?:\w+\s+)?(" + _NUM
                  + r")\s*km", q) or re.search(
                      r"(" + _NUM + r")\s*km\s+ek\s+ghant\w*\s+me",
                      q)
    if m:
        mt = re.search(r"(" + _NUM + r")\s+ghant\w*\s+me", q)
        if mt:
            v = _num(m.group(1)) * _num(mt.group(1))
            return {"type": "applied", "op": "hinglish_speed",
                    "answer": f"{fmt_num(v)} km",
                    "steps": [f"Ek ghante me "
                              f"{fmt_num(_num(m.group(1)))} km, "
                              f"to {fmt_num(_num(mt.group(1)))} "
                              f"ghante me = {fmt_num(v)} km"],
                    "value": v}
        if "speed" in q or "raftaar" in q or "chaal" in q:
            v = _num(m.group(1))
            return {"type": "applied", "op": "hinglish_speed",
                    "answer": f"{fmt_num(v)} km/h",
                    "steps": [f"Ek ghante me {fmt_num(v)} km "
                              f"matlab speed = {fmt_num(v)} "
                              f"km/h"],
                    "value": v}
    # --- rectangle area from lambai / chaudai
    mL = re.search(r"lambai\D{0,14}?(" + _NUM + r")", q)
    mB = re.search(r"chaudai\D{0,14}?(" + _NUM + r")", q)
    if mL and mB and ("area" in q or "kshetrafal" in q):
        v = _num(mL.group(1)) * _num(mB.group(1))
        return {"type": "applied", "op": "hinglish_area",
                "answer": fmt_num(v),
                "steps": ["Area = lambai × chaudai",
                          f"= {fmt_num(_num(mL.group(1)))} × "
                          f"{fmt_num(_num(mB.group(1)))} = "
                          f"{fmt_num(v)}"],
                "value": v}
    # --- triangle area from aadhar / unchai
    mA = re.search(r"aadhar\D{0,14}?(" + _NUM + r")", q)
    mU = re.search(r"unchai\D{0,14}?(" + _NUM + r")", q)
    if mA and mU and ("kshetrafal" in q or "area" in q):
        v = _num(mA.group(1)) * _num(mU.group(1)) / 2
        return {"type": "applied", "op": "hinglish_area",
                "answer": fmt_num(v),
                "steps": ["Tribhuj ka kshetrafal = "
                          "(1/2) × aadhar × unchai",
                          f"= (1/2) × "
                          f"{fmt_num(_num(mA.group(1)))} × "
                          f"{fmt_num(_num(mU.group(1)))} = "
                          f"{fmt_num(v)}"],
                "value": v}
    # --- circle from vyas / trijya (paridhi, or the Roman
    # spelling of परिमाप: parimaap)
    _circ56 = "paridhi" in q or "parimaap" in q \
        or "parimap" in q
    if _circ56 or "kshetrafal" in q:
        mD = re.search(r"vyas\D{0,14}?(" + _NUM + r")", q)
        mR = re.search(r"trijya\D{0,14}?(" + _NUM + r")", q)
        if _circ56 and mD:
            # Wave 99: pi policy (diameter rule).
            _pi, _u227, _reason = pi_choice(
                diameter=_num(mD.group(1)))
            _pit = "(22/7)" if _u227 else "π"
            v = _pi * _num(mD.group(1))
            return {"type": "applied", "op": "hinglish_circle",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Paridhi = π × vyas",
                              f"= {_pit} × {fmt_num(_num(mD.group(1)))}"
                              f" = {fmt_num(round(v, 2))}"],
                    "value": v}
        if _circ56 and mR:
            _pi, _u227, _reason = pi_choice(
                radius=_num(mR.group(1)))
            _pit = "(22/7)" if _u227 else "π"
            v = 2 * _pi * _num(mR.group(1))
            return {"type": "applied", "op": "hinglish_circle",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Paridhi = 2πr",
                              f"= 2 × {_pit} × "
                              f"{fmt_num(_num(mR.group(1)))} = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
        if "kshetrafal" in q and mR:
            _pi, _u227, _reason = pi_choice(
                radius=_num(mR.group(1)))
            _pit = "(22/7)" if _u227 else "π"
            v = _pi * _num(mR.group(1)) ** 2
            return {"type": "applied", "op": "hinglish_circle",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Kshetrafal = πr²",
                              f"= {_pit} × "
                              f"{fmt_num(_num(mR.group(1)))}² = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- remainder after a percent is used (tank of water)
    m = re.search(r"(" + _NUM + r")\s*(?:litre|liter|l)\b", q)
    mp = re.search(r"(" + _NUM + r")\s*(?:%|percent|pratishat|"
                   r"parcent)\s*(?:paani\s+)?(?:istemal|"
                   r"istemaal|used|kharch)", q)
    if m and mp:
        total, p = _num(m.group(1)), _num(mp.group(1))
        used = total * p / 100.0
        if "bacha" in q or "bachaa" in q or "baki" in q:
            v = total - used
            return {"type": "applied", "op": "hinglish_percent",
                    "answer": fmt_num(round(v, 2)),
                    "steps": [f"Istemal hua = {fmt_num(p)}% of "
                              f"{fmt_num(total)} = "
                              f"{fmt_num(used)}",
                              f"Bacha = {fmt_num(total)} - "
                              f"{fmt_num(used)} = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
        return {"type": "applied", "op": "hinglish_percent",
                "answer": fmt_num(round(used, 2)),
                "steps": [f"Istemal = {fmt_num(p)}% of "
                          f"{fmt_num(total)} = "
                          f"{fmt_num(round(used, 2))}"],
                "value": used}
    # --- percent of a headcount ("40 bacche, 60% ladkiya")
    m = re.search(r"(" + _NUM + r")\s+(?:bacche|bachche|"
                  r"students?|vidyarthi|log|aadmi)\b", q)
    mp = re.search(r"(" + _NUM + r")\s*(?:%|percent|pratishat|"
                   r"parcent)", q)
    if m and mp and "kitn" in q:
        total, p = _num(m.group(1)), _num(mp.group(1))
        v = total * p / 100.0
        return {"type": "applied", "op": "hinglish_percent",
                "answer": fmt_num(round(v, 2)),
                "steps": [f"{fmt_num(p)}% of {fmt_num(total)} = "
                          f"{fmt_num(total)} × {fmt_num(p)}"
                          f"/100 = {fmt_num(round(v, 2))}"],
                "value": v}
    # --- sum & difference ("yog 48, antar 12, badi sankhya")
    mS = re.search(r"(?:yog|jod)\s*(?:hai\s*)?(" + _NUM + r")",
                   q)
    mD = re.search(r"antar\s*(?:hai\s*)?(" + _NUM + r")", q)
    if mS and mD:
        S, D = _num(mS.group(1)), _num(mD.group(1))
        _big, _small = (S + D) / 2, (S - D) / 2
        if "choti" in q or "chhoti" in q:
            v, lab = _small, "Choti"
        elif "badi" in q or "bada" in q:
            v, lab = _big, "Badi"
        else:
            # Neither is singled out ("Sankhyayen batao" —
            # tell the numbers): give BOTH, as the older
            # normaliser path did.
            return {"type": "applied",
                    "op": "hinglish_sum_diff",
                    "answer": f"{fmt_num(_big)} and "
                              f"{fmt_num(_small)}",
                    "steps": [
                        f"Badi sankhya = (yog + antar) / 2 "
                        f"= ({fmt_num(S)} + {fmt_num(D)}) / 2 "
                        f"= {fmt_num(_big)}",
                        f"Choti sankhya = (yog - antar) / 2 "
                        f"= ({fmt_num(S)} - {fmt_num(D)}) / 2 "
                        f"= {fmt_num(_small)}"],
                    "value": _big}
        return {"type": "applied", "op": "hinglish_sum_diff",
                "answer": fmt_num(v),
                "steps": [f"{lab} sankhya = (yog "
                          f"{'+' if lab == 'Badi' else '-'} "
                          f"antar) / 2 = ({fmt_num(S)} "
                          f"{'+' if lab == 'Badi' else '-'} "
                          f"{fmt_num(D)}) / 2 = {fmt_num(v)}"],
                "value": v}
    # --- sum (or difference) of two stated ages: "bhai 12
    # saal ka hai aur mai 15 saal ka, dono ki umar ka yog
    # batao" -> 12 + 15
    _ages56 = [_num(x) for x in re.findall(
        r"(" + _NUM + r")\s*(?:saal|sal|years?)\b", q)]
    if len(_ages56) == 2 and ("yog" in q or "jod" in q
                              or "antar" in q):
        if "antar" in q:
            v = abs(_ages56[0] - _ages56[1])
            return {"type": "applied", "op": "hinglish_ages",
                    "answer": fmt_num(v),
                    "steps": [f"Umar ka antar = "
                              f"{fmt_num(max(_ages56))} - "
                              f"{fmt_num(min(_ages56))} = "
                              f"{fmt_num(v)}"],
                    "value": v}
        v = _ages56[0] + _ages56[1]
        return {"type": "applied", "op": "hinglish_ages",
                "answer": fmt_num(v),
                "steps": [f"Dono ki umar ka yog = "
                          f"{fmt_num(_ages56[0])} + "
                          f"{fmt_num(_ages56[1])} = "
                          f"{fmt_num(v)}"],
                "value": v}
    # --- "sankhya ka duguna 94 hai"
    m = re.search(r"sankhya\s+ka\s+(dugu?n\w*|do\s+guna|"
                  r"tigu?n\w*|teen\s+guna)\s*(?:hai\s*)?("
                  + _NUM + r")", q)
    if m:
        k = 2 if ("du" in m.group(1) or "do" in m.group(1)) \
            else 3
        v = _num(m.group(2)) / k
        return {"type": "applied", "op": "hinglish_word_eq",
                "answer": fmt_num(v),
                "steps": [f"Sankhya = {fmt_num(_num(m.group(2)))}"
                          f" / {k} = {fmt_num(v)}"],
                "value": v}
    # --- average of a list ("5, 10, 15 ka average")
    if "average" in q or "ausat" in q or "osat" in q:
        seg = re.split(r"average|ausat|osat", q)[0]
        nums = [_num(x) for x in re.findall(r"(" + _NUM + r")",
                                            seg)]
        # Wave 65: this block averaged EVERY number before
        # the word "average" — including journey givens, so
        # "120 km at 60 km/h and 120 km at 40 km/h, average
        # speed?" answered 85 (the mean of 120, 60, 120, 40)
        # and "24 km in 6 hours, back in 3, average speed?"
        # answered 11. A bare list carries no journey/money
        # units; when units are present it is not a list ask.
        if re.search(r"km|hour|ghant|minute|second|speed|"
                     r"rs\b|rupees|meter|metre", seg):
            nums = []
        if len(nums) >= 3:
            v = sum(nums) / len(nums)
            return {"type": "applied", "op": "hinglish_average",
                    "answer": fmt_num(round(v, 2)),
                    "steps": ["Average = (sab ka yog) / "
                              "(kul sankhya)",
                              f"= {fmt_num(sum(nums))} / "
                              f"{len(nums)} = "
                              f"{fmt_num(round(v, 2))}"],
                    "value": v}
    # --- fraction -> decimal ("3/4 ko decimal me batao")
    m = re.search(r"(" + _NUM + r")\s*/\s*(" + _NUM + r")"
                  r"\s+ko\s+decimal", q)
    if m and _num(m.group(2)) != 0:
        v = _num(m.group(1)) / _num(m.group(2))
        return {"type": "applied", "op": "hinglish_convert",
                "answer": fmt_num(round(v, 4)),
                "steps": [f"{fmt_num(_num(m.group(1)))} / "
                          f"{fmt_num(_num(m.group(2)))} = "
                          f"{fmt_num(round(v, 4))}"],
                "value": v}
    # --- decimal -> percent ("0.5 ko percent me badlo")
    m = re.search(r"(" + _NUM + r")\s+ko\s+" + _PCT56, q)
    if m:
        v = _num(m.group(1)) * 100
        return {"type": "applied", "op": "hinglish_convert",
                "answer": f"{fmt_num(round(v, 2))}%",
                "steps": [f"Percent me badalne ke liye 100 se "
                          f"guna: {fmt_num(_num(m.group(1)))} × "
                          f"100 = {fmt_num(round(v, 2))}%"],
                "value": v}
    # --- "800 ka 15% kitna hoga" (Roman twin of the Hindi %)
    m = re.search(r"(" + _NUM + r")\s+ka\s+(" + _NUM + r")"
                  r"\s*%", q)
    if m:
        v = _num(m.group(1)) * _num(m.group(2)) / 100.0
        return {"type": "applied", "op": "hinglish_percent",
                "answer": fmt_num(round(v, 2)),
                "steps": [f"{fmt_num(_num(m.group(2)))}% of "
                          f"{fmt_num(_num(m.group(1)))} = "
                          f"{fmt_num(round(v, 2))}"],
                "value": v}
    # --- days in a year, halved / doubled
    if re.search(r"saal\s+me\s+kitn\w*\s+din", q):
        base = 366.0 if "leap" in q else 365.0
        if "aadha" in q or "adha" in q:
            v = base / 2
            return {"type": "applied", "op": "hinglish_days",
                    "answer": fmt_num(v),
                    "steps": [f"Ek saal me {fmt_num(base)} din "
                              f"hote hai; uska aadha = "
                              f"{fmt_num(v)}"],
                    "value": v}
        return {"type": "applied", "op": "hinglish_days",
                "answer": fmt_num(base),
                "steps": [f"Ek saal me {fmt_num(base)} din "
                          f"hote hai"],
                "value": base}
    return None


def _sdt_hindi(q):
    """Wave 57: Devanagari speed–distance–time. "एक रेलगाड़ी
    360 किलोमीटर की दूरी 4 घंटे में तय करती है, उसकी चाल
    कितनी है?" — the English _speed patterns never match, and
    these asks used to end as letter-soup or a guide."""
    if "चाल" not in q and "रेलगाड़ी" not in q \
            and "ट्रेन" not in q:
        return None
    _UNIT = r"(?:किलोमीटर\s*प्रति\s*घंटा|किमी\s*प्रति\s*घंटा|" \
            r"किमी/घंटा)"
    # Time with the speed in Latin units: "रेलगाड़ी 60 km/h की
    # चाल से 300 km की दूरी कितने समय में तय करेगी?"
    # Merge-3: the distance capture must not be followed by
    # "/" — otherwise the "15 km" inside an increase clause
    # ("गति 15 km/h बढ़ा दी जाए") is misread as a distance and
    # the schema answers time = 15/60 for a question it does
    # not model; abstaining leaves the honest fallback.
    m = re.search(r"(" + _NUM + r")\s*km/h[^0-9]{0,40}?"
                  r"(" + _NUM + r")\s*km(?!\s*/)\b", q)
    if m and "समय" in q:
        s, d = _num(m.group(1)), _num(m.group(2))
        if s == 0:
            return None
        t = d / s
        steps = [
            f"समय = दूरी ÷ चाल = {fmt_num(d)} ÷ {fmt_num(s)} "
            f"= {fmt_num(t)} घंटे",
        ]
        return {"type": "applied", "op": "time_from_speed",
                "answer": f"{fmt_num(t)} hours", "steps": steps,
                "value": t}
    # Distance from speed + time: चाल S किलोमीटर प्रति घंटा,
    # T घंटे, दूरी कितनी? (The speed may also lead: "60
    # किमी/घंटा की चाल से 2 घंटे चलती है, कितनी दूरी?")
    m = re.search(r"चाल\s*(" + _NUM + r")\s*" + _UNIT +
                  r"[^0-9]{0,40}?(" + _NUM + r")\s*घंटे", q) or \
        re.search(r"(" + _NUM + r")\s*" + _UNIT +
                  r"[^0-9]{0,30}?(" + _NUM + r")\s*घंटे", q)
    if m and "दूरी" in q:
        s, t = _num(m.group(1)), _num(m.group(2))
        d = s * t
        steps = [
            f"दूरी = चाल × समय = {fmt_num(s)} × {fmt_num(t)} "
            f"= {fmt_num(d)} किलोमीटर",
        ]
        return {"type": "applied", "op": "distance",
                "answer": f"{fmt_num(d)} km", "steps": steps,
                "value": d}
    # Time from distance + speed: D किलोमीटर जाना है, चाल S.
    m = re.search(r"(" + _NUM + r")\s*(?:किलोमीटर|किमी)"
                  r"[^0-9]{0,50}?चाल\s*(" + _NUM + r")\s*"
                  + _UNIT, q)
    if m and "समय" in q:
        d, s = _num(m.group(1)), _num(m.group(2))
        if s == 0:
            return None
        t = d / s
        steps = [
            f"समय = दूरी ÷ चाल = {fmt_num(d)} ÷ {fmt_num(s)} "
            f"= {fmt_num(t)} घंटे",
        ]
        return {"type": "applied", "op": "time_from_speed",
                "answer": f"{fmt_num(t)} hours", "steps": steps,
                "value": t}
    # Speed from distance + time: D किलोमीटर, T घंटे, चाल/गति?
    m = re.search(r"(" + _NUM + r")\s*(?:किलोमीटर|किमी)"
                  r"[^0-9]{0,30}?(" + _NUM + r")\s*घंटे", q)
    if m and ("चाल" in q or "गति" in q):
        d, t = _num(m.group(1)), _num(m.group(2))
        if t == 0:
            return None
        s = d / t
        steps = [
            f"चाल = दूरी ÷ समय = {fmt_num(d)} ÷ {fmt_num(t)} "
            f"= {fmt_num(s)} किलोमीटर/घंटा",
        ]
        return {"type": "applied", "op": "speed",
                "answer": f"{fmt_num(s)} km/h", "steps": steps,
                "value": s}
    return None


def _simple_interest_hindi(q):
    """Wave 57: Devanagari simple interest — "1000 रुपये पर
    5% वार्षिक ब्याज की दर से 2 वर्ष का साधारण ब्याज कितना
    होगा?" / "2000 रुपये 6% दर से 3 साल के लिए दिए, ब्याज
    कितना मिलेगा?" Same formula as _simple_interest."""
    if "ब्याज" not in q:
        return None
    m = re.search(r"(" + _NUM + r")\s*रुपये[^0-9]{0,30}?"
                  r"(" + _NUM + r")\s*%[^0-9]{0,50}?"
                  r"(" + _NUM + r")\s*(?:वर्ष|साल)", q)
    if not m:
        return None
    P, R, T = (_num(m.group(1)), _num(m.group(2)),
               _num(m.group(3)))
    si = P * R * T / 100.0
    steps = [
        f"मूलधन P = Rs {fmt_num(P)}, दर R = {fmt_num(R)}%, "
        f"समय T = {fmt_num(T)} वर्ष",
        f"साधारण ब्याज = (P × R × T) / 100 = ({fmt_num(P)} × "
        f"{fmt_num(R)} × {fmt_num(T)}) / 100 = Rs {fmt_num(si)}",
    ]
    return {"type": "applied", "op": "simple_interest",
            "answer": fmt_num(si), "steps": steps, "value": si}


def _wave65_schemas(q):
    """Wave 65: general word-problem schemas for the phrasing
    families the trilingual batteries exposed (percent change
    in all directions, SI unknowns other than the interest,
    work together / inverse work, train pole & bridge,
    relative speed, multi-leg average speed, pass marks,
    clock durations, fencing cost, fraction-of-a-number,
    times-a-number, k-times ages). Registered LAST in
    _FAMILIES: every pattern is gated on its full phrasing,
    so it only claims questions no earlier family wanted."""
    # --- Percent change: forward --------------------------------
    m = re.search(r"(" + _NUM + r")\s+(?:is\s+)?(increased|"
                  r"decreased|reduced|raised|lowered)\s+by\s+("
                  + _NUM + r")%", q)
    if m:
        base, pct = _num(m.group(1)), _num(m.group(3))
        up = m.group(2) in ("increased", "raised")
        new = base * (1 + (pct if up else -pct) / 100)
        return {"type": "applied", "op": "percent_change65",
                "answer": fmt_num(new), "value": float(new),
                "steps": [
                    f"Change = {fmt_num(pct)}% of "
                    f"{fmt_num(base)} = "
                    f"{fmt_num(base * pct / 100)}",
                    f"New value = {fmt_num(base)} "
                    f"{'+' if up else '-'} "
                    f"{fmt_num(base * pct / 100)} = "
                    f"{fmt_num(new)}"]}
    # --- Percent change: base stated, then "increases by" ------
    m = re.search(r"(?:is|of|was|are)\s+(" + _NUM + r")"
                  r"[\s\S]{0,40}?(increases?|decreases?|"
                  r"increased|decreased)\s+by\s+(" + _NUM + r")%",
                  q)
    if m:
        base, pct = _num(m.group(1)), _num(m.group(3))
        up = m.group(2).startswith("increas")
        new = base * (1 + (pct if up else -pct) / 100)
        return {"type": "applied", "op": "percent_change65",
                "answer": fmt_num(new), "value": float(new),
                "steps": [
                    f"Change = {fmt_num(pct)}% of "
                    f"{fmt_num(base)} = "
                    f"{fmt_num(base * pct / 100)}",
                    f"New value = {fmt_num(base)} "
                    f"{'+' if up else '-'} "
                    f"{fmt_num(base * pct / 100)} = "
                    f"{fmt_num(new)}"]}
    # --- Percent change: from A to B ----------------------------
    m = re.search(r"(?:increased|decreased|changed|rose|fell|"
                  r"reduced)\s+from\s+(" + _NUM + r")\s*"
                  r"(?:cm|m|km|rs|rupees|kg)?\s*to\s+("
                  + _NUM + r")", q)
    if m and ("percent" in q or "%" in q):
        a, b = _num(m.group(1)), _num(m.group(2))
        if a:
            pct = (b - a) / a * 100
            return {"type": "applied",
                    "op": "percent_change_from_to",
                    "answer": fmt_num(pct) + "%",
                    "value": float(pct),
                    "steps": [
                        f"Change = {fmt_num(b)} - {fmt_num(a)} "
                        f"= {fmt_num(b - a)}",
                        f"Percent change = ({fmt_num(b - a)} / "
                        f"{fmt_num(a)}) × 100 = "
                        f"{fmt_num(pct)}%"]}
    # --- Percent change: reverse --------------------------------
    m = re.search(r"(?:increased|increase|raised)\s+by\s+("
                  + _NUM + r")%\s*(?:,?\s*(?:it|the\s+\w+|a\s+"
                  r"salary|salary)\s+)?(?:becomes|is\s+now|"
                  r"becomes?|now\s+is)\s+(" + _NUM + r")", q) \
        or re.search(r"after\s+(?:a\s+|an\s+)?(" + _NUM
                     + r")%\s+increase[^.]{0,50}?becomes\s+("
                     + _NUM + r")", q)
    if m:
        pct, new = _num(m.group(1)), _num(m.group(2))
        orig = new / (1 + pct / 100)
        return {"type": "applied", "op": "percent_reverse65",
                "answer": fmt_num(orig), "value": float(orig),
                "steps": [
                    f"New value = original × (1 + "
                    f"{fmt_num(pct)}/100)",
                    f"Original = {fmt_num(new)} / "
                    f"{fmt_num(1 + pct / 100)} = "
                    f"{fmt_num(orig)}"]}
    m = re.search(r"(?:decreased|decrease|reduced)\s+by\s+("
                  + _NUM + r")%\s*(?:,?\s*(?:it|the\s+\w+)\s+)?"
                  r"(?:becomes|is\s+now)\s+(" + _NUM + r")", q) \
        or re.search(r"after\s+(?:a\s+|an\s+)?(" + _NUM
                     + r")%\s+(?:decrease|discount|reduction)"
                     r"[^.]{0,50}?becomes\s+(" + _NUM + r")", q)
    if m:
        pct, new = _num(m.group(1)), _num(m.group(2))
        orig = new / (1 - pct / 100)
        return {"type": "applied", "op": "percent_reverse65",
                "answer": fmt_num(orig), "value": float(orig),
                "steps": [
                    f"New value = original × (1 - "
                    f"{fmt_num(pct)}/100)",
                    f"Original = {fmt_num(new)} / "
                    f"{fmt_num(1 - pct / 100)} = "
                    f"{fmt_num(orig)}"]}
    # --- Discount percent from marked & selling prices ----------
    # Wave 78: the sold-for amount usually carries its own
    # "Rs" ("sold for Rs 15300") — without the optional _RS
    # the pattern could never match the textbook phrasing.
    m = re.search(r"(" + _NUM + r")\s*(?:" + _RS + r")?"
                  r"[\s\S]{0,50}?sold\s+for\s+(?:" + _RS
                  + r"\s*)?(" + _NUM + r")"
                  r"[\s\S]{0,50}?discount\s*(?:percent|%)", q)
    if m:
        mp_, sp_ = _num(m.group(1)), _num(m.group(2))
        if mp_:
            pct = (mp_ - sp_) / mp_ * 100
            return {"type": "applied", "op": "discount_percent",
                    "answer": fmt_num(pct) + "%",
                    "value": float(pct),
                    "steps": [
                        f"Discount = {fmt_num(mp_)} - "
                        f"{fmt_num(sp_)} = {fmt_num(mp_ - sp_)}",
                        f"Discount % = ({fmt_num(mp_ - sp_)} / "
                        f"{fmt_num(mp_)}) × 100 = "
                        f"{fmt_num(pct)}%"]}
    # --- Marked above cost, then discounted ----------------------
    m = re.search(r"marks?\b[^.]{0,50}?(" + _NUM + r")%\s+above"
                  r"\s+(?:the\s+)?cost[\s\S]{0,80}?(?:(" + _NUM
                  + r")%\s+discount|discount\s+(?:of\s+)?(" + _NUM
                  + r")%)[\s\S]{0,80}?cost\s+(?:is"
                  r"|price\s+is)\s+(" + _NUM + r")", q)
    if m:
        mk = _num(m.group(1))
        d = _num(m.group(2)) if m.group(2) else _num(m.group(3))
        c = _num(m.group(4))
        sp_ = c * (1 + mk / 100) * (1 - d / 100)
        return {"type": "applied", "op": "marked_discount",
                "answer": fmt_num(sp_), "value": float(sp_),
                "steps": [
                    f"Marked price = {fmt_num(c)} × "
                    f"{fmt_num(1 + mk / 100)} = "
                    f"{fmt_num(c * (1 + mk / 100))}",
                    f"Selling price = marked price × "
                    f"{fmt_num(1 - d / 100)} = "
                    f"{fmt_num(sp_)}"]}
    # --- SI: principal behind a stated amount --------------------
    m = re.search(r"amounts?\s+to\s+(" + _NUM + r")\s*(?:"
                  + _RS + r")?[^.]{0,30}?in\s+(" + _NUM
                  + r")\s+years?\s+at\s+(" + _NUM
                  + r")%\s*(?:per\s+\w+\s+)?(?:simple\s+interest)?",
                  q)
    if m and "simple" in q:
        amt, t, r = (_num(m.group(i)) for i in (1, 2, 3))
        p = amt / (1 + r * t / 100)
        return {"type": "applied", "op": "si_principal_reverse",
                "answer": fmt_num(p), "value": float(p),
                "steps": [
                    f"Amount = P(1 + RT/100), so P = Amount / "
                    f"(1 + {fmt_num(r)} × {fmt_num(t)} / 100)",
                    f"P = {fmt_num(amt)} / "
                    f"{fmt_num(1 + r * t / 100)} = "
                    f"{fmt_num(p)}"]}
    # --- SI: time behind a stated interest -----------------------
    m = re.search(r"in\s+what\s+time\s+will\s+(" + _NUM + r")"
                  r"[^.]{0,40}?earn\s+(" + _NUM + r")\s*(?:"
                  + _RS + r")?\s*(?:of\s+)?interest\s+at\s+("
                  + _NUM + r")%", q)
    if m:
        p, si, r = (_num(m.group(i)) for i in (1, 2, 3))
        if p and r:
            t = si * 100 / (p * r)
            return {"type": "applied", "op": "si_time",
                    "answer": fmt_num(t), "value": float(t),
                    "steps": [
                        f"T = SI × 100 / (P × R) = "
                        f"{fmt_num(si)} × 100 / ({fmt_num(p)} × "
                        f"{fmt_num(r)}) = {fmt_num(t)} years"]}
    # --- SI: rate behind a stated interest -----------------------
    m = re.search(r"simple\s+interest\s+on\s+(" + _NUM + r")"
                  r"[^.]{0,30}?for\s+(" + _NUM + r")\s+years?"
                  r"\s+is\s+(" + _NUM + r")", q)
    if m and "rate" in q:
        p, t, si = (_num(m.group(i)) for i in (1, 2, 3))
        if p and t:
            r = si * 100 / (p * t)
            return {"type": "applied", "op": "si_rate",
                    "answer": fmt_num(r) + "%",
                    "value": float(r),
                    "steps": [
                        f"R = SI × 100 / (P × T) = "
                        f"{fmt_num(si)} × 100 / ({fmt_num(p)} × "
                        f"{fmt_num(t)}) = {fmt_num(r)}%"]}
    # --- Profit/loss reverse: SP and % -> CP ---------------------
    m = re.search(r"sold\s+for\s+(" + _NUM + r")\s*(?:"
                  + _RS + r")?[^.]{0,50}?(profit|loss)\s+of\s+("
                  + _NUM + r")%", q)
    if m:
        sp_, p = _num(m.group(1)), _num(m.group(3))
        sgn = 1 if m.group(2) == "profit" else -1
        cp = sp_ / (1 + sgn * p / 100)
        return {"type": "applied", "op": "cp_from_sp_percent",
                "answer": fmt_num(cp), "value": float(cp),
                "steps": [
                    f"Cost price = selling price / (1 "
                    f"{'+' if sgn > 0 else '-'} "
                    f"{fmt_num(p)}/100) = {fmt_num(sp_)} / "
                    f"{fmt_num(1 + sgn * p / 100)} = "
                    f"{fmt_num(cp)}"]}
    # --- Work together -------------------------------------------
    m = re.search(r"in\s+(" + _NUM + r")\s+days?[\s\S]{0,80}?"
                  r"in\s+(" + _NUM + r")\s+days?[\s\S]{0,60}?"
                  r"together", q)
    if m and ("work" in q or "job" in q or "finish" in q
              or "complete" in q):
        a, b = _num(m.group(1)), _num(m.group(2))
        if a and b:
            t = a * b / (a + b)
            return {"type": "applied", "op": "work_together65",
                    "answer": fmt_num(t), "value": float(t),
                    "steps": [
                        f"In 1 day together they do 1/"
                        f"{fmt_num(a)} + 1/{fmt_num(b)} = "
                        f"{fmt_num(1 / a + 1 / b)} of the work",
                        f"Days together = 1 / "
                        f"{fmt_num(1 / a + 1 / b)} = "
                        f"{fmt_num(t)}"]}
    # --- Inverse work: men-days ----------------------------------
    m = re.search(r"(" + _NUM + r")\s+men\b[^.]{0,60}?in\s+("
                  + _NUM + r")\s+days?[^.]{0,80}?(" + _NUM
                  + r")\s+men\b", q)
    if m:
        m1, d1, m2 = (_num(m.group(i)) for i in (1, 2, 3))
        if m2:
            d2 = m1 * d1 / m2
            return {"type": "applied", "op": "work_inverse65",
                    "answer": fmt_num(d2), "value": float(d2),
                    "steps": [
                        f"Total work = {fmt_num(m1)} men × "
                        f"{fmt_num(d1)} days = "
                        f"{fmt_num(m1 * d1)} man-days",
                        f"Days for {fmt_num(m2)} men = "
                        f"{fmt_num(m1 * d1)} / {fmt_num(m2)} = "
                        f"{fmt_num(d2)}"]}
    # --- Single-rate scaling: one tap / one man ------------------
    m = re.search(r"one\s+(tap|man|worker|pump|machine)\b"
                  r"[^.]{0,60}?in\s+(" + _NUM + r")\s+"
                  r"(hours?|days?)[\s\S]{0,80}?(" + _NUM + r")"
                  r"\s+(?:such\s+)?(taps?|men|workers?|pumps?|"
                  r"machines?)", q)
    if m:
        t1, n = _num(m.group(2)), _num(m.group(4))
        if n:
            t2 = t1 / n
            return {"type": "applied", "op": "single_rate65",
                    "answer": fmt_num(t2), "value": float(t2),
                    "steps": [
                        f"{fmt_num(n)} of them work {fmt_num(n)}"
                        f" times as fast, so the time divides "
                        f"by {fmt_num(n)}",
                        f"Time = {fmt_num(t1)} / {fmt_num(n)} "
                        f"= {fmt_num(t2)} {m.group(3)}"]}
    # --- Train: pole (length from speed x time) ------------------
    m = re.search(r"crosses\s+a\s+pole\s+in\s+(" + _NUM + r")"
                  r"\s+seconds?\s+at\s+(" + _NUM + r")\s*km/h",
                  q)
    if m:
        t, s = _num(m.group(1)), _num(m.group(2))
        length = s * 5 / 18 * t
        return {"type": "applied", "op": "train_pole_length",
                "answer": fmt_num(length), "value": float(length),
                "steps": [
                    f"Speed = {fmt_num(s)} km/h = {fmt_num(s)} "
                    f"× 5/18 = {fmt_num(s * 5 / 18)} m/s",
                    f"Length of the train = speed × time = "
                    f"{fmt_num(s * 5 / 18)} × {fmt_num(t)} = "
                    f"{fmt_num(length)} m"]}
    # --- Train: pole (time from length & speed) ------------------
    m = re.search(r"train\s+(?:is\s+)?(" + _NUM + r")\s*m\s+"
                  r"long[\s\S]{0,60}?(" + _NUM + r")\s*km/h"
                  r"[\s\S]{0,60}?pole", q)
    if m:
        length, s = _num(m.group(1)), _num(m.group(2))
        t = length / (s * 5 / 18)
        return {"type": "applied", "op": "train_pole_time",
                "answer": fmt_num(t), "value": float(t),
                "steps": [
                    f"Speed = {fmt_num(s)} km/h = "
                    f"{fmt_num(s * 5 / 18)} m/s",
                    f"Time to cross a pole = length / speed = "
                    f"{fmt_num(length)} / "
                    f"{fmt_num(s * 5 / 18)} = {fmt_num(t)} "
                    f"seconds"]}
    # --- Train: bridge -------------------------------------------
    m = re.search(r"at\s+(" + _NUM + r")\s*km/h[\s\S]{0,40}?"
                  r"crosses\s+a\s+bridge\s+in\s+(" + _NUM + r")"
                  r"\s+seconds?[\s\S]{0,80}?train\s+is\s+("
                  + _NUM + r")\s*m\s+long", q)
    if m:
        s, t, tl = (_num(m.group(i)) for i in (1, 2, 3))
        total = s * 5 / 18 * t
        bridge = total - tl
        return {"type": "applied", "op": "train_bridge",
                "answer": fmt_num(bridge),
                "value": float(bridge),
                "steps": [
                    f"Speed = {fmt_num(s)} km/h = "
                    f"{fmt_num(s * 5 / 18)} m/s",
                    f"Train + bridge = {fmt_num(s * 5 / 18)} × "
                    f"{fmt_num(t)} = {fmt_num(total)} m",
                    f"Bridge = {fmt_num(total)} - "
                    f"{fmt_num(tl)} = {fmt_num(bridge)} m"]}
    # --- Relative speed ------------------------------------------
    m = re.search(r"(" + _NUM + r")\s*km/h\s+and\s+(" + _NUM
                  + r")\s*km/h[\s\S]{0,60}?relative\s+speed", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        rel = a + b if ("opposite" in q or "towards each "
                        "other" in q or "toward each other"
                        in q) else abs(a - b)
        if "m/s" in q or "metre per second" in q \
                or "meter per second" in q:
            v = rel * 5 / 18
            return {"type": "applied", "op": "relative_speed",
                    "answer": fmt_num(v), "value": float(v),
                    "steps": [
                        f"Relative speed = {fmt_num(a)} + "
                        f"{fmt_num(b)} = {fmt_num(rel)} km/h",
                        f"In m/s: {fmt_num(rel)} × 5/18 = "
                        f"{fmt_num(v)} m/s"]}
        return {"type": "applied", "op": "relative_speed",
                "answer": fmt_num(rel), "value": float(rel),
                "steps": [f"Relative speed = {fmt_num(rel)} "
                          f"km/h"]}
    # --- Average speed: two legs ----------------------------------
    m = re.search(r"first\s+(" + _NUM + r")\s*km\s+at\s+("
                  + _NUM + r")\s*km/h\s+and\s+(?:the\s+)?next\s+("
                  + _NUM + r")\s*km\s+at\s+(" + _NUM
                  + r")\s*km/h", q)
    if m:
        d1, s1, d2, s2 = (_num(m.group(i)) for i in (1, 2, 3, 4))
        if s1 and s2:
            avg = (d1 + d2) / (d1 / s1 + d2 / s2)
            return {"type": "applied", "op": "avg_speed_legs",
                    "answer": fmt_num(avg), "value": float(avg),
                    "steps": [
                        f"Total distance = {fmt_num(d1 + d2)} "
                        f"km; total time = {fmt_num(d1 / s1)} + "
                        f"{fmt_num(d2 / s2)} = "
                        f"{fmt_num(d1 / s1 + d2 / s2)} hours",
                        f"Average speed = {fmt_num(d1 + d2)} / "
                        f"{fmt_num(d1 / s1 + d2 / s2)} = "
                        f"{fmt_num(avg)} km/h"]}
    # --- Average speed: out and back ------------------------------
    m = re.search(r"(" + _NUM + r")\s*km\s+in\s+(" + _NUM + r")"
                  r"\s+hours?[^.]{0,40}?back\s+in\s+(" + _NUM
                  + r")\s+hours?", q)
    if m and "average" in q:
        d, t1, t2 = (_num(m.group(i)) for i in (1, 2, 3))
        avg = 2 * d / (t1 + t2)
        return {"type": "applied", "op": "avg_speed_round",
                "answer": fmt_num(avg), "value": float(avg),
                "steps": [
                    f"Total distance = 2 × {fmt_num(d)} = "
                    f"{fmt_num(2 * d)} km; total time = "
                    f"{fmt_num(t1 + t2)} hours",
                    f"Average speed = {fmt_num(2 * d)} / "
                    f"{fmt_num(t1 + t2)} = {fmt_num(avg)} km/h"]}
    # --- Boat: plain downstream / upstream speed -------------------
    m = re.search(r"goes\s+(" + _NUM + r")\s*km\s+(downstream|"
                  r"upstream)\s+in\s+(" + _NUM + r")\s+hours?",
                  q)
    if m:
        d, t = _num(m.group(1)), _num(m.group(3))
        if t:
            v = d / t
            return {"type": "applied", "op": "boat_plain_speed",
                    "answer": fmt_num(v), "value": float(v),
                    "steps": [
                        f"Speed {m.group(2)} = distance / time "
                        f"= {fmt_num(d)} / {fmt_num(t)} = "
                        f"{fmt_num(v)} km/h"]}
    # --- Boat: still-water speed + stream speed ------------------
    m = re.search(r"still\s+water\s+is\s+(" + _NUM + r")"
                  r"\s*km/h[^.]{0,60}?stream\s+is\s+(" + _NUM +
                  r")\s*km/h", q)
    if m and ("downstream" in q or "upstream" in q):
        bw, st = _num(m.group(1)), _num(m.group(2))
        if "downstream" in q:
            v, sgn = bw + st, "+"
            word = "downstream"
        else:
            v, sgn = bw - st, "-"
            word = "upstream"
        return {"type": "applied", "op": "boat_still_stream",
                "answer": fmt_num(v), "value": float(v),
                "steps": [
                    f"{word.capitalize()} speed = speed in "
                    f"still water {sgn} stream = "
                    f"{fmt_num(bw)} {sgn} {fmt_num(st)}",
                    f"= {fmt_num(v)} km/h"]}
    # --- Fraction of a journey -------------------------------------
    m = re.search(r"covers?\s+(" + _NUM + r")/(" + _NUM + r")"
                  r"\s+of\s+(?:a|the)\s+journey\s+in\s+("
                  + _NUM + r")\s+hours?\s+at\s+(" + _NUM
                  + r")\s*km/h", q)
    if m:
        num_, den = _num(m.group(1)), _num(m.group(2))
        t, s = _num(m.group(3)), _num(m.group(4))
        leg = s * t
        total = leg * den / num_ if num_ else 0
        return {"type": "applied", "op": "journey_fraction",
                "answer": fmt_num(total), "value": float(total),
                "steps": [
                    f"Distance covered = {fmt_num(s)} × "
                    f"{fmt_num(t)} = {fmt_num(leg)} km, and "
                    f"that is {fmt_num(num_)}/{fmt_num(den)} "
                    f"of the journey",
                    f"Total journey = {fmt_num(leg)} × "
                    f"{fmt_num(den)}/{fmt_num(num_)} = "
                    f"{fmt_num(total)} km"]}
    # --- Clock duration --------------------------------------------
    m = re.search(r"(?:leaves?|departs?|starts?)\s+at\s+("
                  + _NUM + r"):(" + _NUM + r")\s*(am|pm)\s+and\s+"
                  r"(?:reaches|arrives|reached)\s+(?:at\s+)?("
                  + _NUM + r"):(" + _NUM + r")\s*(am|pm)", q)
    if m:
        def _mins(h, mi, ap):
            h, mi = int(h), int(mi)
            if ap == "pm" and h != 12:
                h += 12
            if ap == "am" and h == 12:
                h = 0
            return h * 60 + mi
        start = _mins(m.group(1), m.group(2), m.group(3))
        end = _mins(m.group(4), m.group(5), m.group(6))
        if end <= start:
            end += 24 * 60
        dur = end - start
        if "minute" in q:
            return {"type": "applied", "op": "clock_duration",
                    "answer": fmt_num(dur), "value": float(dur),
                    "steps": [f"From {m.group(1)}:{m.group(2)} "
                              f"{m.group(3)} to {m.group(4)}:"
                              f"{m.group(5)} {m.group(6)} is "
                              f"{fmt_num(dur)} minutes"]}
        hrs = dur / 60
        return {"type": "applied", "op": "clock_duration",
                "answer": fmt_num(hrs), "value": float(hrs),
                "steps": [f"Duration = {fmt_num(dur)} minutes "
                          f"= {fmt_num(hrs)} hours"]}
    # --- Fencing cost ----------------------------------------------
    m = re.search(r"(" + _NUM + r")\s*m?\s*(?:long|in\s+length)"
                  r"[^.]{0,40}?(" + _NUM + r")\s*m?\s*(?:wide|"
                  r"in\s+width)[^.]{0,90}?fencing[^.]{0,50}?("
                  + _NUM + r")\s*(?:rs|rupees)", q)
    if m:
        ln, wd, rate = (_num(m.group(i)) for i in (1, 2, 3))
        per = 2 * (ln + wd)
        cost = per * rate
        return {"type": "applied", "op": "fencing_cost",
                "answer": fmt_num(cost), "value": float(cost),
                "steps": [
                    f"Perimeter = 2 × ({fmt_num(ln)} + "
                    f"{fmt_num(wd)}) = {fmt_num(per)} m",
                    f"Fencing cost = {fmt_num(per)} × "
                    f"{fmt_num(rate)} = {fmt_num(cost)}"]}
    # --- Dozen cost -> cost of one ----------------------------------
    m = re.search(r"dozen\s+[a-z]+\s+cost\s+(" + _NUM + r")"
                  r"[\s\S]{0,50}?cost\s+of\s+one", q)
    if m:
        total = _num(m.group(1))
        one = total / 12
        return {"type": "applied", "op": "dozen_cost_one",
                "answer": fmt_num(one), "value": float(one),
                "steps": [
                    f"A dozen is 12, so one costs "
                    f"{fmt_num(total)} / 12 = {fmt_num(one)}"]}
    # --- Fraction of a number ---------------------------------------
    m = re.search(r"(" + _NUM + r")/(" + _NUM + r")\s+of\s+a\s+"
                  r"number\s+is\s+(" + _NUM + r")", q)
    if m:
        num_, den, val = (_num(m.group(i)) for i in (1, 2, 3))
        if num_:
            x = val * den / num_
            return {"type": "applied", "op": "fraction_of_number",
                    "answer": fmt_num(x), "value": float(x),
                    "steps": [
                        f"The number = {fmt_num(val)} × "
                        f"{fmt_num(den)}/{fmt_num(num_)} = "
                        f"{fmt_num(x)}"]}
    # --- Times a number ------------------------------------------------
    m = re.search(r"(twice|thrice|(" + _NUM + r")\s+times)\s+a\s+"
                  r"number\s*(?:(plus|minus|added|less)\s+("
                  + _NUM + r"))?\s*(?:equals?|is)\s+(" + _NUM
                  + r")", q)
    if m:
        k = {"twice": 2, "thrice": 3}.get(m.group(1)) or \
            _num(m.group(2))
        b = _num(m.group(4)) if m.group(4) else 0
        c = _num(m.group(5))
        if m.group(3) in ("plus", "added"):
            x = (c - b) / k
        elif m.group(3) in ("minus", "less"):
            x = (c + b) / k
        else:
            x = c / k
        return {"type": "applied", "op": "times_number",
                "answer": fmt_num(x), "value": float(x),
                "steps": [
                    f"Let the number be x: {fmt_num(k)}x"
                    + (f" {'+' if m.group(3) in ('plus', 'added') else '-'} {fmt_num(b)}" if m.group(4) else "")
                    + f" = {fmt_num(c)}",
                    f"x = {fmt_num(x)}"]}
    # --- Pass marks ------------------------------------------------------
    m = re.search(r"needs?\s+(" + _NUM + r")%\s*(?:marks?\s+)?to"
                  r"\s+pass[\s\S]{0,80}?gets?\s+(" + _NUM + r")"
                  r"\s+marks?[\s\S]{0,40}?fails?\s+by\s+(" + _NUM
                  + r")", q)
    if m:
        pct, got, short = (_num(m.group(i)) for i in (1, 2, 3))
        if pct:
            mx = (got + short) / (pct / 100)
            return {"type": "applied", "op": "pass_marks",
                    "answer": fmt_num(mx), "value": float(mx),
                    "steps": [
                        f"Passing marks = {fmt_num(got)} + "
                        f"{fmt_num(short)} = "
                        f"{fmt_num(got + short)}, and that is "
                        f"{fmt_num(pct)}% of the maximum",
                        f"Maximum marks = {fmt_num(got + short)}"
                        f" / {fmt_num(pct / 100)} = "
                        f"{fmt_num(mx)}"]}
    # --- "costs N rupees, sold at a discount of D%" ----------------
    m = re.search(r"(?:costs|price\s+is|marked\s+at)\s+(" + _NUM +
                  r")\s*(?:rs|rupees)?[^.]{0,50}?discount\s+of"
                  r"\s+(" + _NUM + r")%", q)
    if m and "selling price" in q:
        mp_, d_ = _num(m.group(1)), _num(m.group(2))
        sp_ = mp_ * (1 - d_ / 100)
        return {"type": "applied", "op": "discount_story65",
                "answer": fmt_num(sp_), "value": float(sp_),
                "steps": [
                    f"Discount = {fmt_num(d_)}% of "
                    f"{fmt_num(mp_)} = "
                    f"{fmt_num(mp_ * d_ / 100)}",
                    f"Selling price = {fmt_num(mp_)} - "
                    f"{fmt_num(mp_ * d_ / 100)} = "
                    f"{fmt_num(sp_)}"]}
    # --- Terse train speed: "train 756 km 9 hours speed?" --------
    m = re.search(r"train[^.]{0,20}?(" + _NUM + r")\s*km\s+(" +
                  _NUM + r")\s*hours?\b[^.]{0,20}?speed", q)
    if m:
        d_, t_ = _num(m.group(1)), _num(m.group(2))
        if t_:
            v_ = d_ / t_
            return {"type": "applied", "op": "sdt_terse65",
                    "answer": fmt_num(v_), "value": float(v_),
                    "steps": [
                        f"Speed = distance / time = "
                        f"{fmt_num(d_)} / {fmt_num(t_)}",
                        f"Speed = {fmt_num(v_)} km/h"]}
    # --- Terse / scrambled simple interest -------------------------
    m = re.search(r"(?:on\s+)?(" + _NUM + r")\s*(?:rs|rupees)"
                  r"\s+at\s+(" + _NUM + r")\s*(?:%|percent)"
                  r"\s+for\s+(" + _NUM + r")\s+years?", q)
    if m is None:
        m = re.search(r"(" + _NUM + r")\s+at\s+(" + _NUM +
                      r")%\s+(" + _NUM + r")\s+years?", q)
    if m and "interest" in q and "compound" not in q:
        p_, r_, t_ = (_num(m.group(1)), _num(m.group(2)),
                      _num(m.group(3)))
        si_ = p_ * r_ * t_ / 100
        return {"type": "applied", "op": "si_terse65",
                "answer": fmt_num(si_), "value": float(si_),
                "steps": [
                    f"SI = P × R × T / 100 = {fmt_num(p_)} × "
                    f"{fmt_num(r_)} × {fmt_num(t_)} / 100",
                    f"SI = {fmt_num(si_)}"]}
    # --- Consecutive even / odd pairs --------------------------------
    m = re.search(r"two\s+consecutive\s+(even|odd)\s+numbers"
                  r"[^.]{0,50}?sum\s+(?:is\s+)?(" + _NUM + r")",
                  q)
    if m:
        s = _num(m.group(2))
        smaller = s / 2 - 1
        bigger = s / 2 + 1
        return {"type": "applied", "op": "consecutive_pair65",
                "answer": fmt_num(smaller),
                "value": float(smaller),
                "steps": [
                    f"Let the numbers be x and x + 2: "
                    f"2x + 2 = {fmt_num(s)}",
                    f"x = {fmt_num(smaller)}, so the numbers "
                    f"are {fmt_num(smaller)} and "
                    f"{fmt_num(bigger)}"]}
    # --- k times as old ----------------------------------------------------
    m = re.search(r"(" + _NUM + r")\s+times\s+as\s+old\s+as"
                  r"[\s\S]{0,80}?(?:sum|together)[\s\S]{0,30}?("
                  + _NUM + r")", q)
    if m:
        k, s = _num(m.group(1)), _num(m.group(2))
        younger = s / (k + 1)
        older = s - younger
        if "son" in q or "younger" in q or "daughter" in q:
            return {"type": "applied", "op": "ages_times",
                    "answer": fmt_num(younger),
                    "value": float(younger),
                    "steps": [
                        f"Ages are {fmt_num(k)}x and x, and "
                        f"{fmt_num(k)}x + x = {fmt_num(s)}",
                        f"x = {fmt_num(s)} / {fmt_num(k + 1)} "
                        f"= {fmt_num(younger)}"]}
        return {"type": "applied", "op": "ages_times",
                "answer": fmt_num(older), "value": float(older),
                "steps": [
                    f"Ages are {fmt_num(k)}x and x, and "
                    f"{fmt_num(k)}x + x = {fmt_num(s)}",
                    f"Older age = {fmt_num(k)} × "
                    f"{fmt_num(younger)} = {fmt_num(older)}"]}
    return None


def _english_commercial(q):
    """Wave 78: plain-English commercial-maths phrasings —
    the Class 7-8 textbook shapes the Hinglish-first handlers
    miss ("a shirt costs Rs 800 and is sold at 15% discount",
    "marks it 20% above the cost price", "selling price is
    Rs 616 and the cost price is Rs 560, find the profit
    percent"). Registered LAST in _FAMILIES: every branch is
    gated on a full labelled extraction (marked price / cost
    price / selling price / discount %), so it only claims
    questions no earlier family wanted. The method is the
    standard one throughout: discount is taken on the marked
    price, profit/loss percent on the cost price."""
    if not re.search(r"discount|marked|profit|loss|gain|"
                     r"%\s*off\b", q):
        return None

    def _amt(pat):
        m = re.search(pat, q)
        return _num(m.group(1)) if m else None

    MP = _amt(r"marked\s+price\b[^.]{0,40}?(?:is|=)\s*(?:"
              + _RS + r"\s*)?(" + _NUM + r")") \
        or _amt(r"(?:marked|priced)\s+at\s+(?:" + _RS
                + r"\s*)?(" + _NUM + r")") \
        or _amt(r"\bmarks?\b[^.]{0,30}?\bat\s+(?:" + _RS
                + r"\s*)?(" + _NUM + r")")
    SP = _amt(r"selling\s+price\b[^.]{0,30}?(?:is|=)\s*(?:"
              + _RS + r"\s*)?(" + _NUM + r")(?!\s*%)") \
        or _amt(r"(?:sold|sells)\s+(?:at|for)\s+(?:" + _RS
                + r"\s*)?(" + _NUM + r")(?!\s*%)")
    CP = _amt(r"cost\s+price\b[^.]{0,40}?(?:is|=)\s*(?:"
              + _RS + r"\s*)?(" + _NUM + r")") \
        or _amt(r"\bbuys?\b[^.]{0,50}?(?:for\s+)?(?:" + _RS
                + r"\s*)?(" + _NUM + r")") \
        or _amt(r"\bbought\b[^.]{0,40}?(?:for\s+)?(?:" + _RS
                + r"\s*)?(" + _NUM + r")") \
        or _amt(r"\bpurchased\b[^.]{0,40}?(?:for\s+)?(?:"
                + _RS + r"\s*)?(" + _NUM + r")")
    md = re.search(r"discount\s+(?:of|is|rate\s+is|allowed\s+"
                   r"of)\s+(" + _NUM + r")\s*(?:%|percent)", q) \
        or re.search(r"(" + _NUM + r")\s*(?:%|percent)\s*"
                     r"(?:discount|off)", q) \
        or re.search(r"discount\s+(" + _NUM + r")\s*"
                     r"(?:%|percent)", q)
    d = _num(md.group(1)) if md else None
    if MP is None and d is not None:
        # "A shirt costs Rs 800 and is sold at 15% discount"
        # — here "costs" states the price the discount acts
        # on (the same reading discount_story65 uses).
        MP = _amt(r"(?:costs|price\s+is)\s+(?:" + _RS
                  + r"\s*)?(" + _NUM + r")")

    ask_percent = "percent" in q or "percentage" in q
    ask_discount_amt = bool(re.search(
        r"how\s+much\s+discount|what\s+is\s+the\s+discount\b|"
        r"discount\s+amount|amount\s+of\s+discount|"
        r"discount\s+(?:does|will|did)\b", q))
    ask_mp = bool(re.search(
        r"(?:find|what\s+is|what\s+was)\b[^.]{0,30}?"
        r"marked\s+price", q))

    # --- Mark-up: CP raised by m% to get the marked price,
    # optionally discounted afterwards (the marked_discount
    # schema in _wave65_schemas needs the CP stated last;
    # the textbook order is CP first).
    mm = re.search(r"(" + _NUM + r")\s*%\s+above\s+(?:the\s+)?"
                   r"cost", q)
    if mm and CP:
        mk = _num(mm.group(1))
        MPc = CP * (1 + mk / 100.0)
        if d is not None and 0 <= d < 100 \
                and ("selling" in q or "sold" in q):
            SPc = MPc * (1 - d / 100.0)
            return {"type": "applied", "op": "markup_discount78",
                    "answer": f"Rs {fmt_num(SPc)}",
                    "steps": [
                        f"Marked price = {fmt_num(CP)} × "
                        f"(1 + {fmt_num(mk)}/100) = "
                        f"Rs {fmt_num(MPc)}",
                        f"Selling price = {fmt_num(MPc)} × "
                        f"(1 - {fmt_num(d)}/100) = "
                        f"Rs {fmt_num(SPc)}"],
                    "value": SPc}
        return {"type": "applied", "op": "markup78",
                "answer": f"Rs {fmt_num(MPc)}",
                "steps": [
                    f"Marked price = cost price × (1 + "
                    f"{fmt_num(mk)}/100) = {fmt_num(CP)} × "
                    f"{fmt_num(1 + mk / 100.0)} = "
                    f"Rs {fmt_num(MPc)}"],
                "value": MPc}

    # --- Discount on a known marked price -------------------
    if d is not None and 0 <= d < 100 and MP:
        off = MP * d / 100.0
        SPc = MP - off
        if CP and "profit" in q:
            prof = SPc - CP
            steps = [
                f"Marked price = Rs {fmt_num(MP)}, discount "
                f"= {fmt_num(d)}%, so the selling price is "
                f"{fmt_num(MP)} × (1 - {fmt_num(d)}/100) = "
                f"Rs {fmt_num(SPc)}",
                f"Cost price = Rs {fmt_num(CP)}, so "
                f"{'profit' if prof >= 0 else 'loss'} = "
                f"Rs {fmt_num(abs(prof))}"]
            if ask_percent and CP > 0:
                pp = prof / CP * 100.0
                steps.append(
                    f"Profit percent = {fmt_num(prof)} / "
                    f"{fmt_num(CP)} × 100 = {fmt_num(pp)}%")
                return {"type": "applied",
                        "op": "discount_profit78",
                        "answer": f"{fmt_num(pp)}%",
                        "steps": steps, "value": pp}
            kind = "Profit" if prof >= 0 else "Loss"
            return {"type": "applied",
                    "op": "discount_profit78",
                    "answer": f"{kind} of Rs "
                              f"{fmt_num(abs(prof))}",
                    "steps": steps, "value": abs(prof)}
        if ask_discount_amt and not ask_percent:
            return {"type": "applied",
                    "op": "discount_amount78",
                    "answer": f"Rs {fmt_num(off)}",
                    "steps": [
                        f"Marked price = Rs {fmt_num(MP)}, "
                        f"discount = {fmt_num(d)}%",
                        f"Discount = {fmt_num(d)}% of "
                        f"{fmt_num(MP)} = Rs {fmt_num(off)}"],
                    "value": off}
        return {"type": "applied", "op": "discount78",
                "answer": f"Rs {fmt_num(SPc)}",
                "steps": [
                    f"Marked price = Rs {fmt_num(MP)}, "
                    f"discount = {fmt_num(d)}%",
                    f"Discount amount = {fmt_num(d)}% of "
                    f"{fmt_num(MP)} = Rs {fmt_num(off)}",
                    f"Selling price = {fmt_num(MP)} - "
                    f"{fmt_num(off)} = Rs {fmt_num(SPc)}"],
                "value": SPc}

    # --- Reverse discount: SP and d% given, MP asked --------
    if d is not None and 0 <= d < 100 and SP and MP is None \
            and (ask_mp or "marked" in q):
        MPc = SP / (1 - d / 100.0)
        return {"type": "applied", "op": "discount_reverse78",
                "answer": f"Rs {fmt_num(MPc)}",
                "steps": [
                    f"The article sells for Rs {fmt_num(SP)} "
                    f"after a discount of {fmt_num(d)}% on "
                    f"the marked price.",
                    f"So (100 - {fmt_num(d)})% of the marked "
                    f"price = Rs {fmt_num(SP)}",
                    f"Marked price = {fmt_num(SP)} × 100 / "
                    f"{fmt_num(100 - d)} = Rs {fmt_num(MPc)}"],
                "value": MPc}

    # --- Discount percent from marked & selling prices ------
    if MP and SP and "discount" in q and ask_percent and MP > 0:
        pct = (MP - SP) / MP * 100.0
        return {"type": "applied", "op": "discount_percent78",
                "answer": f"{fmt_num(pct)}%",
                "steps": [
                    f"Discount = {fmt_num(MP)} - "
                    f"{fmt_num(SP)} = Rs {fmt_num(MP - SP)}",
                    f"Discount % = ({fmt_num(MP - SP)} / "
                    f"{fmt_num(MP)}) × 100 = "
                    f"{fmt_num(pct)}%"],
                "value": pct}

    # --- Profit / loss with the SP stated before the CP -----
    if SP and CP and ("profit" in q or "loss" in q
                      or "gain" in q):
        diff = SP - CP
        kind = "Profit" if diff > 0 else "Loss" if diff < 0 \
            else "None"
        if diff == 0:
            return {"type": "applied", "op": "profit_loss78",
                    "answer": "No profit, no loss",
                    "steps": [
                        f"Cost price (CP) = Rs {fmt_num(CP)}, "
                        f"selling price (SP) = "
                        f"Rs {fmt_num(SP)}",
                        "SP = CP, so there is no profit and "
                        "no loss."],
                    "value": 0}
        steps = [
            f"Cost price (CP) = Rs {fmt_num(CP)}, selling "
            f"price (SP) = Rs {fmt_num(SP)}",
            f"{kind} = {'SP - CP' if diff > 0 else 'CP - SP'}"
            f" = Rs {fmt_num(abs(diff))}"]
        if ask_percent:
            pct = abs(diff) / CP * 100.0
            steps.append(
                f"{kind} % = ({kind} ÷ CP) × 100 = "
                f"({fmt_num(abs(diff))} ÷ {fmt_num(CP)}) × "
                f"100 = {fmt_num(pct)}%")
            return {"type": "applied",
                    "op": "profit_loss_percent78",
                    "answer": f"{fmt_num(pct)}%",
                    "steps": steps, "value": pct}
        return {"type": "applied", "op": "profit_loss78",
                "answer": f"{kind} of Rs "
                          f"{fmt_num(abs(diff))}",
                "steps": steps, "value": abs(diff)}

    # --- Profit / loss stated as a rupee amount, % asked ----
    ma = re.search(r"\b(profit|loss|gain)\s+of\s+(?:" + _RS
                   + r"\s*)?(" + _NUM + r")(?!\s*%)", q)
    if ma and CP and ask_percent and CP > 0:
        amt = _num(ma.group(2))
        pct = amt / CP * 100.0
        kind = "Profit" if ma.group(1) != "loss" else "Loss"
        return {"type": "applied",
                "op": "profit_loss_amount_pct78",
                "answer": f"{fmt_num(pct)}%",
                "steps": [
                    f"Cost price = Rs {fmt_num(CP)}, "
                    f"{kind.lower()} = Rs {fmt_num(amt)}",
                    f"{kind} % = ({fmt_num(amt)} ÷ "
                    f"{fmt_num(CP)}) × 100 = "
                    f"{fmt_num(pct)}%"],
                "value": pct}

    # --- CP with a stated profit/loss %, SP asked (the CP
    # statement carries words: "cost price of a bicycle is
    # Rs 3200, it is sold at a profit of 12%").
    mp2 = re.search(r"\b(profit|gain|loss)\s+of\s+(" + _NUM
                    + r")\s*%", q)
    if mp2 and CP and ("selling" in q or "sold" in q
                       or "sells" in q):
        kind, p = mp2.group(1), _num(mp2.group(2))
        if kind == "loss":
            if p >= 100:
                return None
            SPc = CP * (1 - p / 100.0)
            steps = [f"SP = CP × (1 - loss/100) = "
                     f"{fmt_num(CP)} × "
                     f"{fmt_num(1 - p / 100.0)} = "
                     f"Rs {fmt_num(SPc)}"]
        else:
            SPc = CP * (1 + p / 100.0)
            steps = [f"SP = CP × (1 + profit/100) = "
                     f"{fmt_num(CP)} × "
                     f"{fmt_num(1 + p / 100.0)} = "
                     f"Rs {fmt_num(SPc)}"]
        return {"type": "applied", "op": "profit_loss_sp78",
                "answer": f"Rs {fmt_num(SPc)}",
                "steps": steps, "value": SPc}
    return None




_FAMILIES = (_hindi_word_problems,
             _ratio, _unitary_cost, _simple_interest,
             _simple_interest_hindi, _profit_loss,
             _gst, _successive_discount, _two_articles_same_sp,
             _sdt_hindi, _speed, _word_equation, _quadratic_info,
             _find_k_equal_roots, _sum_product_roots,
             _identity_eval, _insert_means,
             _speed_time_quadratic, _sum_difference, _ages,
             _consecutive_product, _rectangle_word,
             _rectangle_diagonal,
             _compound_interest_freq, _compound_interest,
             _discount, _percent_score,
             _profit_loss_forms, _ratio_share_ask,
             _inverse_proportion, _bells_lcm, _train_crossing,
             _digits,
             _lp_corners, _lp_inequalities, _bayes_bags,
             _bayes_medical,
             _bayes_factory, _pipes, _work_together,
             _work_efficiency, _boat_stream, _two_trains,
             # Wave 56 method-first families (appended last:
             # they only fire on phrasings no earlier family
             # claims).
             _consecutive_sum, _item_cost, _fraction_word,
             _percent_change, _growth_decay, _si_doubles,
             _angle_word, _temperature, _cuboid_capacity,
             _hindi_schemas,
             _hinglish_schemas,
             # Wave 65: trilingual word-schema net (gated
             # phrasings only; see _wave65_schemas).
             _wave65_schemas,
             # Wave 78: English commercial-maths net
             # (discount / MP-CP-SP / profit & loss textbook
             # phrasings; gated extractions only, fires only
             # on what no earlier family claimed).
             _english_commercial)


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
