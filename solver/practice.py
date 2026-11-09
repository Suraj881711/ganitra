"""Practice mode: generate random questions with hidden answers."""
import random

from .expression_parser import fmt_num


def _arith(rng):
    a, b = rng.randint(3, 60), rng.randint(3, 40)
    op = rng.choice(["+", "-", "×"])
    if op == "+":
        return f"{a} + {b}", fmt_num(a + b)
    if op == "-":
        if b > a:
            a, b = b, a
        return f"{a} - {b}", fmt_num(a - b)
    return f"{a} × {b}", fmt_num(a * b)


def _bodmas(rng):
    a, b, c = rng.randint(2, 12), rng.randint(2, 12), rng.randint(2, 30)
    return f"{c} + {a} × {b}", fmt_num(c + a * b)


def _linear(rng):
    xv = rng.randint(2, 15)
    a = rng.randint(2, 9)
    b = rng.randint(1, 20)
    return f"Solve {a}x + {b} = {a * xv + b}", f"x = {xv}"


def _quadratic(rng):
    r1, r2 = rng.randint(1, 9), rng.randint(1, 9)
    s, p = r1 + r2, r1 * r2
    q = f"Solve x^2 - {s}x + {p} = 0"
    return q, f"x = {r1} or x = {r2}"


def _percent(rng):
    base = rng.choice([80, 120, 150, 200, 240, 300, 400, 500])
    pct = rng.choice([5, 10, 12, 15, 20, 25, 40, 50])
    return f"What is {pct}% of {base}?", fmt_num(base * pct / 100)


def _ap(rng):
    a = rng.randint(1, 15)
    d = rng.randint(2, 9)
    n = rng.randint(5, 15)
    terms = ", ".join(str(a + i * d) for i in range(3))
    return (f"Find the {n}th term of the AP {terms}, ...",
            fmt_num(a + (n - 1) * d))


def _trig(rng):
    table = {0: "0", 30: "1/2", 45: "1/√2", 60: "√3/2", 90: "1"}
    ang = rng.choice(list(table))
    fn = rng.choice(["sin", "cos"])
    if fn == "cos":
        table = {0: "1", 30: "√3/2", 45: "1/√2", 60: "1/2", 90: "0"}
    return f"What is {fn} {ang}°?", table[ang]


_GENERATORS = [_arith, _bodmas, _linear, _quadratic, _percent, _ap, _trig]


def generate_practice(count: int = 7, seed=None):
    rng = random.Random(seed)
    gens = list(_GENERATORS)
    rng.shuffle(gens)
    out = []
    for i in range(count):
        q, a = gens[i % len(gens)](rng)
        out.append({"question": q, "answer": a})
    return out
