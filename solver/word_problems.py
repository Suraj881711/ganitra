"""Word problems: percentage change, distance = speed × time,
two numbers from sum & product, and simple interest."""
import re

from sympy import Eq, solve, symbols

from .expression_parser import fmt_num


def solve_word_problem(question: str):
    q = question.lower()

    # Simple interest: "simple interest on 1000 at 5% for 2 years"
    m = re.search(
        r"simple\s+interest\s+on\s+(\d+(?:\.\d+)?)\s+at\s+"
        r"(\d+(?:\.\d+)?)\s*%\s*(?:per\s+annum\s+)?for\s+"
        r"(\d+(?:\.\d+)?)\s*years?",
        q,
    )
    if m:
        P, R, T = (float(m.group(i)) for i in (1, 2, 3))
        si = P * R * T / 100.0
        steps = [
            "Simple Interest = P × R × T / 100",
            f"= {fmt_num(P)} × {fmt_num(R)} × {fmt_num(T)} / 100 "
            f"= {fmt_num(si)}",
            f"Total amount = P + SI = {fmt_num(P + si)}",
        ]
        return {"type": "word_problem", "op": "simple_interest",
                "answer": fmt_num(si), "value": si, "steps": steps}

    # Percent increase/decrease: "increase by 15% of 240"
    m = re.search(
        r"(increase|decrease)\s+by\s+(\d+(?:\.\d+)?)%\s+of\s+"
        r"(\d+(?:\.\d+)?)", q)
    if m:
        op, pct, base = m.groups()
        pct_f, base_f = float(pct), float(base)
        change = base_f * pct_f / 100.0
        value = base_f + change if op == "increase" else base_f - change
        steps = [
            f"{pct}% of {fmt_num(base_f)} = {fmt_num(base_f)} × "
            f"{fmt_num(pct_f)}/100 = {fmt_num(change)}",
            f"{'Add to' if op == 'increase' else 'Subtract from'} the "
            f"original: {fmt_num(base_f)} "
            f"{'+' if op == 'increase' else '-'} {fmt_num(change)} "
            f"= {fmt_num(value)}",
        ]
        return {"type": "word_problem", "op": "percent_change",
                "answer": fmt_num(value), "value": value, "steps": steps}

    # Distance = speed × time: "60 km/h for 2 hours"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:km/h|mph|m/s)\s*for\s+(\d+(?:\.\d+)?)\s*"
        r"(?:hours?|hrs?|h|seconds?|sec|s)\b", q)
    if m:
        v, t = float(m.group(1)), float(m.group(2))
        steps = [
            "Distance = speed × time",
            f"= {fmt_num(v)} × {fmt_num(t)} = {fmt_num(v * t)}",
        ]
        return {"type": "word_problem", "op": "distance",
                "answer": fmt_num(v * t), "value": v * t, "distance": v * t,
                "steps": steps}

    # Two numbers: "sum is 10 and product is 21"
    m = re.search(
        r"sum\s+is\s+(\d+(?:\.\d+)?)\s+and\s+product\s+is\s+"
        r"(\d+(?:\.\d+)?)", q)
    if m:
        S, P = float(m.group(1)), float(m.group(2))
        xv, yv = symbols("x y")
        sol = solve((Eq(xv + yv, S), Eq(xv * yv, P)), (xv, yv))
        pairs = [tuple(fmt_num(float(v)) for v in s) for s in sol]
        steps = [
            f"Let the numbers be x and y: x + y = {fmt_num(S)} and "
            f"x·y = {fmt_num(P)}",
            "Substitute y = S - x into the product equation and solve "
            "the quadratic.",
            "Pairs (x, y): " + ", ".join(f"({a}, {b})" for a, b in pairs),
        ]
        return {"type": "word_problem", "op": "sum_product",
                "answer": ", ".join(f"({a}, {b})" for a, b in pairs),
                "solutions": [list(p) for p in pairs], "steps": steps}

    return {"type": "word_problem", "op": "unknown",
            "answer": "No word-problem pattern matched. Try a form like "
                      "'increase by 15% of 240', '60 km/h for 2 hours' "
                      "or 'sum is 10 and product is 21'.",
            "steps": []}
