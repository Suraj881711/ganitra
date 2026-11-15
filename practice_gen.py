"""Wave 34: standalone practice-question generator.

Generates fresh practice questions for Classes 6-10 by topic
(arithmetic, algebra, geometry basics, mensuration, probability).
Every question is template-based and the generator computes the
answer itself from the same parameters it puts in the question,
so the answer is correct by construction (the Wave 34 tests
recompute every answer independently and also cross-check a
sample against the Ganitra solver).

This module is deliberately NOT wired into any route or template
(integration is a later wave). It depends on nothing from the app
except, optionally, the solver's public entry point used by the
tests for cross-checking — the generator itself never imports it.

Public API:
    generate_question(class_num, topic, seed=None) -> dict
    generate_set(class_num, topic, count=5, seed=None) -> list

Each question dict carries:
    class_num, topic, kind   -- routing info
    question                 -- text shown to the student
    answer                   -- formatted answer string
    answer_value             -- exact answer as fractions.Fraction
                                (None for non-single-number answers,
                                e.g. polynomial expansion)
    params                   -- every number that went into the
                                question, so tests can recompute
                                the answer independently
    solver_text              -- a plain rendering the Ganitra
                                solver can be asked directly, for
                                the templates where that is
                                meaningful (else None)
"""
import math
import random
from fractions import Fraction

TOPICS = ("arithmetic", "algebra", "geometry", "mensuration",
          "probability")
CLASSES = (6, 7, 8, 9, 10)


def _fmt(value):
    """Format a Fraction/int as a clean answer string."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _signed(value):
    """'+ 3' / '− 3' fragment for a signed int (Wave 54 helpers)."""
    value = int(value)
    return f"+ {value}" if value >= 0 else f"− {abs(value)}"


def _binom(c):
    """'(x + 3)' / '(x − 3)' for a binomial constant."""
    return f"(x + {c})" if c >= 0 else f"(x − {abs(c)})"


def _sup(n):
    """Superscript rendering of a non-negative integer."""
    digits = "⁰¹²³⁴⁵⁶⁷⁸⁹"
    return "".join(digits[int(ch)] for ch in str(n))


def _dec(value):
    """Minimal decimal string for a Fraction whose denominator
    only has factors 2 and 5 (19.75, not 79/4)."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    den = value.denominator
    k = 0
    while (10 ** k) % den:
        k += 1
    scaled = value.numerator * (10 ** k // den)
    s = str(abs(scaled)).rjust(k + 1, "0")
    out = (s[:-k] + "." + s[-k:]).rstrip("0").rstrip(".")
    return ("-" if scaled < 0 else "") + out


def _lin(a, b):
    """'3x + 5' / 'x − 2' / '−x + 4' for a linear expression."""
    if a == 1:
        head = "x"
    elif a == -1:
        head = "−x"
    else:
        head = f"{a}x"
    if b == 0:
        return head
    return f"{head} {_signed(b)}"


def _poly2(c1, c0):
    """Answer string for x² + c1·x + c0 with clean signs."""
    parts = ["x²"]
    if c1:
        coef = "" if abs(c1) == 1 else str(abs(c1))
        parts.append(("+" if c1 > 0 else "−") + f" {coef}x")
    if c0:
        parts.append(("+" if c0 > 0 else "−") + f" {abs(c0)}")
    return " ".join(parts)


def _item(class_num, topic, kind, question, answer_value, params,
          solver_text=None, answer=None):
    return {
        "class_num": class_num,
        "topic": topic,
        "kind": kind,
        "question": question,
        "answer": _fmt(answer_value) if answer is None else answer,
        "answer_value": answer_value,
        "params": params,
        "solver_text": solver_text,
    }


# ---------------------------------------------------------------------------
# Arithmetic
# ---------------------------------------------------------------------------

def _arith_expression(rng, class_num):
    a = rng.randint(3, 60 if class_num >= 8 else 30)
    b = rng.randint(2, 12)
    c = rng.randint(2, 15)
    d = rng.randint(2, 30)
    # a + b * c - d : multiplication first, exact by construction.
    value = Fraction(a) + Fraction(b * c) - Fraction(d)
    expr_solver = f"{a} + {b} * {c} - {d}"
    return _item(
        class_num, "arithmetic", "expression",
        f"Evaluate: {a} + {b} × {c} − {d}",
        value, {"a": a, "b": b, "c": c, "d": d},
        solver_text=expr_solver)


def _arith_fraction_add(rng, class_num):
    b = rng.choice([2, 3, 4, 5, 6, 8])
    d = rng.choice([2, 3, 4, 5, 6, 8])
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    value = Fraction(a, b) + Fraction(c, d)
    return _item(
        class_num, "arithmetic", "fraction_add",
        f"Simplify: {a}/{b} + {c}/{d}",
        value, {"a": a, "b": b, "c": c, "d": d},
        solver_text=f"{a}/{b} + {c}/{d}")


def _arith_percent(rng, class_num):
    p = rng.choice([5, 10, 12, 15, 20, 25, 40, 50, 60, 75])
    n = rng.choice([40, 60, 80, 120, 160, 200, 240, 300, 400])
    value = Fraction(p * n, 100)
    return _item(
        class_num, "arithmetic", "percent",
        f"Find {p}% of {n}.",
        value, {"p": p, "n": n},
        solver_text=f"{p}/100 * {n}")


def _arith_simple_interest(rng, class_num):
    principal = rng.choice([500, 800, 1000, 1200, 2000, 2500, 5000])
    rate = rng.choice([4, 5, 6, 8, 10, 12])
    years = rng.randint(1, 5)
    value = Fraction(principal * rate * years, 100)
    return _item(
        class_num, "arithmetic", "simple_interest",
        f"Find the simple interest on ₹{principal} at {rate}% "
        f"per annum for {years} years.",
        value, {"principal": principal, "rate": rate,
                "years": years},
        solver_text=f"{principal} * {rate} * {years} / 100")


# ---------------------------------------------------------------------------
# Arithmetic — Wave 54 expansion
# ---------------------------------------------------------------------------

def _arith_integer_add_sub(rng, class_num):
    a = rng.randint(-20, 20)
    b = rng.randint(-20, 20)
    op = rng.choice(["add", "sub"])
    if op == "add":
        return _item(
            class_num, "arithmetic", "integer_add_sub",
            f"Simplify: ({a}) + ({b})",
            Fraction(a + b), {"a": a, "b": b, "op": op})
    return _item(
        class_num, "arithmetic", "integer_add_sub",
        f"Simplify: ({a}) − ({b})",
        Fraction(a - b), {"a": a, "b": b, "op": op})


def _arith_fraction_subtract(rng, class_num):
    b = rng.choice([2, 3, 4, 5, 6, 8])
    d = rng.choice([2, 3, 4, 5, 6, 8])
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    f1, f2 = Fraction(a, b), Fraction(c, d)
    if f2 > f1:
        a, b, c, d = c, d, a, b
        f1, f2 = f2, f1
    return _item(
        class_num, "arithmetic", "fraction_subtract",
        f"Simplify: {a}/{b} − {c}/{d}",
        f1 - f2, {"a": a, "b": b, "c": c, "d": d},
        solver_text=f"{a}/{b} - {c}/{d}")


def _arith_fraction_of(rng, class_num):
    d = rng.choice([2, 3, 4, 5, 6, 8, 10])
    n = rng.randint(1, d - 1)
    k = rng.randint(2, 15)
    quantity = d * k
    return _item(
        class_num, "arithmetic", "fraction_of",
        f"Find {n}/{d} of {quantity}.",
        Fraction(n * k), {"n": n, "d": d, "quantity": quantity},
        solver_text=f"{n}/{d} * {quantity}")


def _arith_fraction_multiply(rng, class_num):
    b = rng.choice([2, 3, 4, 5, 6, 7, 8])
    d = rng.choice([2, 3, 4, 5, 6, 7, 8])
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    return _item(
        class_num, "arithmetic", "fraction_multiply",
        f"Simplify: {a}/{b} × {c}/{d}",
        Fraction(a * c, b * d),
        {"a": a, "b": b, "c": c, "d": d},
        solver_text=f"({a}/{b}) * ({c}/{d})")


def _arith_fraction_divide(rng, class_num):
    b = rng.choice([2, 3, 4, 5, 6, 7, 8])
    d = rng.choice([2, 3, 4, 5, 6, 7, 8])
    a = rng.randint(1, b - 1)
    c = rng.randint(1, d - 1)
    return _item(
        class_num, "arithmetic", "fraction_divide",
        f"Simplify: {a}/{b} ÷ {c}/{d}",
        Fraction(a * d, b * c),
        {"a": a, "b": b, "c": c, "d": d},
        solver_text=f"({a}/{b}) / ({c}/{d})")


def _arith_mixed_fraction_add(rng, class_num):
    w1 = rng.randint(1, 5)
    w2 = rng.randint(1, 5)
    d1 = rng.choice([2, 3, 4, 6, 8])
    d2 = rng.choice([2, 3, 4, 6, 8])
    n1 = rng.randint(1, d1 - 1)
    n2 = rng.randint(1, d2 - 1)
    value = (Fraction(w1 * d1 + n1, d1)
             + Fraction(w2 * d2 + n2, d2))
    return _item(
        class_num, "arithmetic", "mixed_fraction_add",
        f"Add: {w1} {n1}/{d1} + {w2} {n2}/{d2}",
        value, {"w1": w1, "n1": n1, "d1": d1,
                "w2": w2, "n2": n2, "d2": d2})


def _arith_decimal_add(rng, class_num):
    a = Fraction(rng.randint(101, 9999), 100)
    b = Fraction(rng.randint(101, 9999), 100)
    value = a + b
    return _item(
        class_num, "arithmetic", "decimal_add",
        f"Add: {_dec(a)} + {_dec(b)}",
        value, {"a": _dec(a), "b": _dec(b)},
        answer=_dec(value))


def _arith_decimal_multiply(rng, class_num):
    a = Fraction(rng.randint(11, 99), 10)
    b = Fraction(rng.randint(11, 99), 10)
    value = a * b
    return _item(
        class_num, "arithmetic", "decimal_multiply",
        f"Multiply: {_dec(a)} × {_dec(b)}",
        value, {"a": _dec(a), "b": _dec(b)},
        answer=_dec(value))


def _arith_percent_increase(rng, class_num):
    price = rng.choice([200, 400, 600, 800, 1000, 1200, 2000])
    p = rng.choice([5, 10, 20, 25, 50])
    value = Fraction(price * (100 + p), 100)
    return _item(
        class_num, "arithmetic", "percent_increase",
        f"The price of an article is ₹{price}. It increases "
        f"by {p}%. Find the new price.",
        value, {"price": price, "p": p})


def _arith_discount_price(rng, class_num):
    price = rng.choice([200, 300, 400, 500, 600, 800, 1000,
                        1500, 2000])
    p = rng.choice([5, 10, 15, 20, 25, 30, 40, 50])
    value = Fraction(price * (100 - p), 100)
    return _item(
        class_num, "arithmetic", "discount_price",
        f"A shirt costs ₹{price}. A discount of {p}% is "
        f"given on it. Find the selling price.",
        value, {"price": price, "p": p})


def _arith_find_whole_from_percent(rng, class_num):
    whole = rng.choice([40, 60, 80, 100, 120, 150, 200, 240,
                        250, 300, 400, 500])
    cands = [p for p in (5, 10, 15, 20, 25, 30, 40, 50, 60,
                         75, 80) if (p * whole) % 100 == 0]
    p = rng.choice(cands)
    part = p * whole // 100
    return _item(
        class_num, "arithmetic", "find_whole_from_percent",
        f"{p}% of a number is {part}. Find the number.",
        Fraction(whole), {"p": p, "part": part})


def _arith_ratio_share(rng, class_num):
    a = rng.randint(1, 9)
    b = rng.randint(1, 9)
    k = rng.randint(2, 20)
    total = (a + b) * k
    ask = rng.choice(["first", "second"])
    share = a if ask == "first" else b
    return _item(
        class_num, "arithmetic", "ratio_share",
        f"Divide ₹{total} in the ratio {a} : {b}. Find the "
        f"{ask} part.",
        Fraction(share * k),
        {"a": a, "b": b, "total": total, "ask": ask})


def _arith_ratio_simplify(rng, class_num):
    while True:
        p = rng.randint(1, 9)
        q = rng.randint(1, 9)
        if math.gcd(p, q) == 1 and (p, q) != (1, 1):
            break
    m = rng.randint(2, 9)
    a, b = p * m, q * m
    return _item(
        class_num, "arithmetic", "ratio_simplify",
        f"Express the ratio {a} : {b} in its simplest form.",
        None, {"a": a, "b": b}, answer=f"{p}:{q}")


def _arith_unitary(rng, class_num):
    n = rng.randint(2, 12)
    unit = rng.randint(3, 40)
    m = rng.randint(2, 15)
    while m == n:
        m = rng.randint(2, 15)
    return _item(
        class_num, "arithmetic", "unitary_method",
        f"{n} pens cost ₹{n * unit}. Find the cost of "
        f"{m} pens.",
        Fraction(m * unit),
        {"n": n, "total": n * unit, "m": m, "unit": unit})


def _arith_average(rng, class_num):
    devs = rng.choice([
        [-4, -2, 0, 2, 4], [-3, -1, 0, 1, 3],
        [-5, 0, 0, 0, 5], [-2, -2, 1, 1, 2],
        [-3, -1, 1, 3], [-4, 0, 0, 4], [-2, -1, 1, 2]])
    base = rng.randint(12, 60)
    nums = [base + d for d in devs]
    listing = ", ".join(str(x) for x in nums)
    return _item(
        class_num, "arithmetic", "average",
        f"Find the average of {listing}.",
        Fraction(base), {"nums": nums})


def _arith_hcf(rng, class_num):
    g = rng.randint(2, 15)
    while True:
        p = rng.randint(2, 9)
        q = rng.randint(2, 9)
        if math.gcd(p, q) == 1 and p != q:
            break
    return _item(
        class_num, "arithmetic", "hcf",
        f"Find the HCF of {g * p} and {g * q}.",
        Fraction(g), {"a": g * p, "b": g * q})


def _arith_lcm(rng, class_num):
    while True:
        a = rng.randint(2, 15)
        b = rng.randint(2, 15)
        value = a * b // math.gcd(a, b)
        if a != b and value <= 120:
            break
    return _item(
        class_num, "arithmetic", "lcm",
        f"Find the LCM of {a} and {b}.",
        Fraction(value), {"a": a, "b": b})


def _arith_compound_interest(rng, class_num):
    years = rng.choice([2, 2, 3])
    rate = rng.choice([5, 10, 20, 25])
    amount = Fraction(0)
    principal = 0
    for _ in range(50):
        principal = rng.choice([1000, 2000, 2500, 4000, 5000,
                                8000, 10000, 16000])
        amount = Fraction(principal * (100 + rate) ** years,
                          100 ** years)
        if amount.denominator == 1:
            break
    return _item(
        class_num, "arithmetic", "compound_interest",
        f"Find the compound interest on ₹{principal} at "
        f"{rate}% per annum for {years} years, compounded "
        f"annually.",
        amount - principal,
        {"principal": principal, "rate": rate, "years": years})


def _arith_square_of(rng, class_num):
    n = rng.randint(3, 40)
    return _item(
        class_num, "arithmetic", "square_of",
        f"Find the value of {n}².",
        Fraction(n * n), {"n": n})


def _arith_sqrt_perfect(rng, class_num):
    root = rng.randint(3, 30)
    return _item(
        class_num, "arithmetic", "sqrt_perfect",
        f"Find the square root of {root * root}.",
        Fraction(root), {"root": root, "number": root * root})


def _arith_cube_of(rng, class_num):
    n = rng.randint(2, 15)
    return _item(
        class_num, "arithmetic", "cube_of",
        f"Find the value of {n}³.",
        Fraction(n ** 3), {"n": n})


def _arith_exponent_value(rng, class_num):
    while True:
        base = rng.randint(2, 10)
        exp = rng.randint(2, 5)
        if base ** exp <= 20000:
            break
    return _item(
        class_num, "arithmetic", "exponent_value",
        f"Find the value of {base}{_sup(exp)}.",
        Fraction(base ** exp), {"base": base, "exp": exp})


def _arith_profit_loss(rng, class_num):
    cp = rng.choice([120, 150, 200, 250, 300, 400, 450, 500,
                     600, 750, 800])
    variant = rng.choice(["profit", "loss"])
    diff = rng.randint(5, max(10, cp // 2))
    sp = cp + diff if variant == "profit" else cp - diff
    return _item(
        class_num, "arithmetic", "profit_loss",
        f"A shopkeeper buys an article for ₹{cp} and sells "
        f"it for ₹{sp}. Find the {variant}.",
        Fraction(diff), {"cp": cp, "sp": sp, "variant": variant})


def _arith_speed_distance_time(rng, class_num):
    speed = rng.randint(5, 80)
    time = rng.randint(2, 9)
    distance = speed * time
    variant = rng.choice(["speed", "distance", "time"])
    params = {"speed": speed, "time": time,
              "distance": distance, "variant": variant}
    if variant == "speed":
        question = (f"A train travels {distance} km in {time} "
                    f"hours. Find its speed.")
        value = Fraction(speed)
    elif variant == "distance":
        question = (f"A car travels at {speed} km/h for "
                    f"{time} hours. Find the distance covered.")
        value = Fraction(distance)
    else:
        question = (f"A bus covers {distance} km at a speed "
                    f"of {speed} km/h. Find the time taken.")
        value = Fraction(time)
    return _item(class_num, "arithmetic", "speed_distance_time",
                 question, value, params)


# ---------------------------------------------------------------------------
# Algebra
# ---------------------------------------------------------------------------

def _algebra_linear(rng, class_num):
    x0 = rng.randint(-9, 15)
    a = rng.randint(2, 9)
    b = rng.randint(-12, 15)
    c = a * x0 + b
    sign = "+" if b >= 0 else "−"
    question = f"Solve for x: {a}x {sign} {abs(b)} = {c}"
    return _item(
        class_num, "algebra", "linear_equation",
        question, Fraction(x0), {"a": a, "b": b, "c": c},
        solver_text=f"{a}x + {b} = {c}")


def _algebra_evaluate(rng, class_num):
    x0 = rng.randint(-6, 9)
    a = rng.randint(2, 8)
    b = rng.randint(-10, 10)
    value = Fraction(a * x0 + b)
    return _item(
        class_num, "algebra", "evaluate_linear",
        f"If x = {x0}, find the value of {a}x + {b}.",
        value, {"a": a, "b": b, "x": x0})


def _algebra_expand(rng, class_num):
    a = rng.randint(-8, 9)
    b = rng.randint(-8, 9)
    s = a + b
    p = a * b
    answer = f"x² + {s}x + {p}"
    return _item(
        class_num, "algebra", "expand_binomials",
        f"Expand: (x + {a})(x + {b})",
        None, {"a": a, "b": b}, answer=answer)


def _algebra_ap_nth(rng, class_num):
    a = rng.randint(2, 30)
    d = rng.randint(2, 12)
    n = rng.randint(5, 20)
    value = Fraction(a + (n - 1) * d)
    return _item(
        class_num, "algebra", "ap_nth_term",
        f"Find the {n}th term of the AP: {a}, {a + d}, "
        f"{a + 2 * d}, ...",
        value, {"a": a, "d": d, "n": n})


def _algebra_quadratic_roots(rng, class_num):
    r1 = rng.randint(-9, 9)
    r2 = rng.randint(-9, 9)
    if r1 == r2:
        r2 += 1
    s = r1 + r2
    p = r1 * r2
    question = (f"Solve: x² − ({s})x + {p} = 0" if s >= 0
                else f"Solve: x² + ({-s})x + {p} = 0")
    return _item(
        class_num, "algebra", "quadratic_roots",
        question, None, {"r1": r1, "r2": r2},
        answer=f"x = {r1} or x = {r2}")


# ---------------------------------------------------------------------------
# Algebra — Wave 54 expansion
# ---------------------------------------------------------------------------

def _algebra_evaluate_quadratic(rng, class_num):
    x0 = rng.randint(-6, 9)
    a = rng.randint(1, 5)
    b = rng.randint(-9, 9)
    c = rng.randint(-12, 12)
    value = Fraction(a * x0 * x0 + b * x0 + c)
    a_str = "" if a == 1 else str(a)
    return _item(
        class_num, "algebra", "evaluate_quadratic",
        f"If x = {x0}, find the value of {a_str}x² "
        f"{_signed(b)}x {_signed(c)}.",
        value, {"a": a, "b": b, "c": c, "x": x0})


def _algebra_evaluate_two_vars(rng, class_num):
    a = rng.randint(2, 9)
    b = rng.randint(2, 9)
    x0 = rng.randint(-5, 8)
    y0 = rng.randint(-5, 8)
    return _item(
        class_num, "algebra", "evaluate_two_vars",
        f"If x = {x0} and y = {y0}, find the value of "
        f"{a}x + {b}y.",
        Fraction(a * x0 + b * y0),
        {"a": a, "b": b, "x": x0, "y": y0})


def _algebra_equation_both_sides(rng, class_num):
    x0 = rng.randint(-8, 12)
    a = rng.randint(3, 9)
    c = rng.randint(1, a - 1)
    b = rng.randint(-12, 12)
    d = (a - c) * x0 + b
    return _item(
        class_num, "algebra", "equation_both_sides",
        f"Solve for x: {a}x {_signed(b)} = {c}x {_signed(d)}",
        Fraction(x0), {"a": a, "b": b, "c": c, "d": d})


def _algebra_simultaneous(rng, class_num):
    y0 = rng.randint(1, 12)
    x0 = y0 + rng.randint(1, 10)
    ask = rng.choice(["x", "y"])
    s = x0 + y0
    d = x0 - y0
    return _item(
        class_num, "algebra", "simultaneous",
        f"Solve the pair of equations: x + y = {s} and "
        f"x − y = {d}. Find the value of {ask}.",
        Fraction(x0 if ask == "x" else y0),
        {"x": x0, "y": y0, "ask": ask})


def _algebra_factorise(rng, class_num):
    while True:
        a = rng.randint(-9, 9)
        b = rng.randint(-9, 9)
        if a != 0 and b != 0 and a + b != 0:
            break
    s, p = a + b, a * b
    return _item(
        class_num, "algebra", "factorise_quadratic",
        f"Factorise: x² {_signed(s)}x {_signed(p)}",
        None, {"a": a, "b": b},
        answer=f"{_binom(a)}{_binom(b)}")


def _algebra_identity_square(rng, class_num):
    while True:
        a = rng.randint(-9, 9)
        if a != 0:
            break
    return _item(
        class_num, "algebra", "identity_square",
        f"Expand: {_binom(a)}²",
        None, {"a": a}, answer=_poly2(2 * a, a * a))


def _algebra_identity_diff_square(rng, class_num):
    a = rng.randint(2, 12)
    return _item(
        class_num, "algebra", "identity_diff_square",
        f"Expand: (x + {a})(x − {a})",
        None, {"a": a}, answer=f"x² − {a * a}")


def _algebra_identity_numeric(rng, class_num):
    variant = rng.choice(["square", "product"])
    if variant == "square":
        n = 100 + rng.choice([-1, 1]) * rng.randint(1, 9)
        return _item(
            class_num, "algebra", "identity_numeric",
            f"Using a suitable identity, find the value "
            f"of {n}².",
            Fraction(n * n), {"variant": variant, "n": n})
    m = rng.choice([50, 100, 100, 200])
    k = rng.randint(1, 5)
    return _item(
        class_num, "algebra", "identity_numeric",
        f"Using a suitable identity, find the value of "
        f"{m - k} × {m + k}.",
        Fraction(m * m - k * k),
        {"variant": variant, "m": m, "k": k})


def _algebra_ap_sum(rng, class_num):
    a = rng.randint(1, 30)
    d = rng.randint(1, 12)
    n = rng.randint(5, 20)
    total = Fraction(n * (2 * a + (n - 1) * d), 2)
    while total.denominator != 1:
        n += 1
        total = Fraction(n * (2 * a + (n - 1) * d), 2)
    return _item(
        class_num, "algebra", "ap_sum",
        f"Find the sum of the first {n} terms of the AP: "
        f"{a}, {a + d}, {a + 2 * d}, ...",
        total, {"a": a, "d": d, "n": n})


def _algebra_gp_nth(rng, class_num):
    a = rng.randint(1, 10)
    r = rng.choice([2, 2, 3])
    n = rng.randint(3, 6 if r == 3 else 8)
    return _item(
        class_num, "algebra", "gp_nth_term",
        f"Find the {n}th term of the GP: {a}, {a * r}, "
        f"{a * r * r}, ...",
        Fraction(a * r ** (n - 1)), {"a": a, "r": r, "n": n})


def _algebra_gp_sum(rng, class_num):
    a = rng.randint(1, 10)
    r = rng.choice([2, 2, 3])
    n = rng.randint(3, 6)
    total = Fraction(a * (r ** n - 1), r - 1)
    return _item(
        class_num, "algebra", "gp_sum",
        f"Find the sum of the first {n} terms of the GP: "
        f"{a}, {a * r}, {a * r * r}, ...",
        total, {"a": a, "r": r, "n": n})


def _algebra_polynomial_add_sub(rng, class_num):
    variant = rng.choice(["add", "subtract"])
    while True:
        a1 = rng.randint(1, 9)
        a2 = rng.randint(1, 9)
        if variant == "add" or a1 != a2:
            break
    b1 = rng.randint(-12, 12)
    b2 = rng.randint(-12, 12)
    sign = "+" if variant == "add" else "−"
    return _item(
        class_num, "algebra", "polynomial_add_sub",
        f"Simplify: ({_lin(a1, b1)}) {sign} ({_lin(a2, b2)})",
        None, {"a1": a1, "b1": b1, "a2": a2, "b2": b2,
               "variant": variant},
        answer=_lin(a1 + a2 if variant == "add" else a1 - a2,
                    b1 + b2 if variant == "add" else b1 - b2))


def _algebra_simplify_like_terms(rng, class_num):
    while True:
        a = rng.randint(2, 12)
        b = rng.randint(2, 12)
        c = rng.randint(1, a + b - 2)
        if a + b - c >= 2:
            break
    return _item(
        class_num, "algebra", "simplify_like_terms",
        f"Simplify: {a}x + {b}x − {c}x",
        None, {"a": a, "b": b, "c": c},
        answer=f"{a + b - c}x")


def _algebra_index_laws(rng, class_num):
    variant = rng.choice(["product", "quotient", "power"])
    base = rng.choice([2, 2, 3, 5])
    if variant == "product":
        m = rng.randint(1, 4)
        n = rng.randint(1, 4)
        value = base ** (m + n)
        question = (f"Simplify: {base}{_sup(m)} × "
                    f"{base}{_sup(n)}")
    elif variant == "quotient":
        n = rng.randint(1, 3)
        m = n + rng.randint(1, 4)
        value = base ** (m - n)
        question = (f"Simplify: {base}{_sup(m)} ÷ "
                    f"{base}{_sup(n)}")
    else:
        m = rng.randint(2, 3)
        n = rng.randint(2, 3)
        value = base ** (m * n)
        question = f"Simplify: ({base}{_sup(m)}){_sup(n)}"
    return _item(
        class_num, "algebra", "index_laws",
        question, Fraction(value),
        {"base": base, "m": m, "n": n, "variant": variant})


# ---------------------------------------------------------------------------
# Geometry basics
# ---------------------------------------------------------------------------

def _geo_supplementary(rng, class_num):
    a = rng.randint(25, 160)
    return _item(
        class_num, "geometry", "supplementary_angle",
        f"Two angles are supplementary. One angle is {a}°. "
        f"Find the other angle.",
        Fraction(180 - a), {"a": a})


def _geo_triangle_third_angle(rng, class_num):
    a = rng.randint(25, 100)
    b = rng.randint(25, min(110, 170 - a))
    return _item(
        class_num, "geometry", "triangle_third_angle",
        f"Two angles of a triangle are {a}° and {b}°. Find "
        f"the third angle.",
        Fraction(180 - a - b), {"a": a, "b": b})


def _geo_rectangle_area(rng, class_num):
    length = rng.randint(4, 30)
    breadth = rng.randint(3, 25)
    return _item(
        class_num, "geometry", "rectangle_area",
        f"Find the area of a rectangle of length {length} cm "
        f"and breadth {breadth} cm.",
        Fraction(length * breadth),
        {"length": length, "breadth": breadth})


def _geo_circle_circumference(rng, class_num):
    k = rng.randint(1, 6)
    r = 7 * k  # π = 22/7 gives an exact integer circumference
    return _item(
        class_num, "geometry", "circle_circumference",
        f"Find the circumference of a circle of radius {r} cm. "
        f"(Use π = 22/7)",
        Fraction(2 * 22 * r, 7), {"r": r})


# ---------------------------------------------------------------------------
# Geometry — Wave 54 expansion
# ---------------------------------------------------------------------------

def _geo_complementary(rng, class_num):
    a = rng.randint(10, 80)
    return _item(
        class_num, "geometry", "complementary_angle",
        f"Two angles are complementary. One angle is {a}°. "
        f"Find the other angle.",
        Fraction(90 - a), {"a": a})


def _geo_triangle_exterior(rng, class_num):
    variant = rng.choice(["exterior", "interior"])
    if variant == "exterior":
        p = rng.randint(25, 100)
        q = rng.randint(25, min(110, 170 - p))
        return _item(
            class_num, "geometry", "triangle_exterior_angle",
            f"The two opposite interior angles of a triangle "
            f"are {p}° and {q}°. Find the exterior angle.",
            Fraction(p + q),
            {"variant": variant, "p": p, "q": q})
    e = rng.randint(60, 170)
    p = rng.randint(25, e - 25)
    return _item(
        class_num, "geometry", "triangle_exterior_angle",
        f"An exterior angle of a triangle is {e}° and one "
        f"of the opposite interior angles is {p}°. Find "
        f"the other opposite interior angle.",
        Fraction(e - p),
        {"variant": variant, "exterior": e, "p": p})


def _geo_isosceles_angle(rng, class_num):
    variant = rng.choice(["base", "vertex"])
    if variant == "base":
        v = 2 * rng.randint(10, 80)
        return _item(
            class_num, "geometry", "isosceles_angle",
            f"The vertex angle of an isosceles triangle is "
            f"{v}°. Find each base angle.",
            Fraction((180 - v) // 2),
            {"variant": variant, "vertex": v})
    b = rng.randint(10, 80)
    return _item(
        class_num, "geometry", "isosceles_angle",
        f"Each base angle of an isosceles triangle is "
        f"{b}°. Find the vertex angle.",
        Fraction(180 - 2 * b),
        {"variant": variant, "base": b})


def _geo_quadrilateral_fourth(rng, class_num):
    while True:
        a = rng.randint(40, 140)
        b = rng.randint(40, 140)
        c = rng.randint(40, 140)
        if a + b + c <= 340:
            break
    return _item(
        class_num, "geometry", "quadrilateral_fourth_angle",
        f"Three angles of a quadrilateral are {a}°, {b}° "
        f"and {c}°. Find the fourth angle.",
        Fraction(360 - a - b - c), {"a": a, "b": b, "c": c})


def _geo_parallelogram_angle(rng, class_num):
    a = rng.randint(25, 155)
    variant = rng.choice(["opposite", "adjacent"])
    if variant == "opposite":
        question = (f"One angle of a parallelogram is {a}°. "
                    f"Find the angle opposite to it.")
        value = Fraction(a)
    else:
        question = (f"One angle of a parallelogram is {a}°. "
                    f"Find the angle adjacent to it.")
        value = Fraction(180 - a)
    return _item(
        class_num, "geometry", "parallelogram_angle",
        question, value, {"a": a, "variant": variant})


def _geo_square_area(rng, class_num):
    side = rng.randint(3, 30)
    return _item(
        class_num, "geometry", "square_area",
        f"Find the area of a square of side {side} cm.",
        Fraction(side * side), {"side": side})


def _geo_square_perimeter(rng, class_num):
    side = rng.randint(3, 40)
    return _item(
        class_num, "geometry", "square_perimeter",
        f"Find the perimeter of a square of side {side} cm.",
        Fraction(4 * side), {"side": side})


def _geo_rectangle_perimeter(rng, class_num):
    length = rng.randint(4, 30)
    breadth = rng.randint(3, 25)
    return _item(
        class_num, "geometry", "rectangle_perimeter",
        f"Find the perimeter of a rectangle of length "
        f"{length} cm and breadth {breadth} cm.",
        Fraction(2 * (length + breadth)),
        {"length": length, "breadth": breadth})


def _geo_triangle_area(rng, class_num):
    base = rng.randint(4, 30)
    height = rng.randint(3, 24)
    if (base * height) % 2:
        height += 1
    return _item(
        class_num, "geometry", "triangle_area",
        f"Find the area of a triangle with base {base} cm "
        f"and height {height} cm.",
        Fraction(base * height, 2),
        {"base": base, "height": height})


def _geo_triangle_perimeter(rng, class_num):
    a = rng.randint(3, 20)
    b = rng.randint(3, 20)
    c = rng.randint(abs(a - b) + 1, a + b - 1)
    return _item(
        class_num, "geometry", "triangle_perimeter",
        f"The sides of a triangle are {a} cm, {b} cm and "
        f"{c} cm. Find its perimeter.",
        Fraction(a + b + c), {"a": a, "b": b, "c": c})


def _geo_rhombus_area(rng, class_num):
    d1 = rng.randint(4, 30)
    d2 = rng.randint(4, 30)
    if (d1 * d2) % 2:
        d2 += 1
    return _item(
        class_num, "geometry", "rhombus_area",
        f"Find the area of a rhombus whose diagonals are "
        f"{d1} cm and {d2} cm.",
        Fraction(d1 * d2, 2), {"d1": d1, "d2": d2})


def _geo_trapezium_area(rng, class_num):
    a = rng.randint(4, 25)
    b = rng.randint(4, 25)
    h = rng.randint(3, 20)
    if ((a + b) * h) % 2:
        h += 1
    return _item(
        class_num, "geometry", "trapezium_area",
        f"Find the area of a trapezium whose parallel "
        f"sides are {a} cm and {b} cm and whose height "
        f"is {h} cm.",
        Fraction((a + b) * h, 2), {"a": a, "b": b, "h": h})


def _geo_circle_area(rng, class_num):
    r = 7 * rng.randint(1, 5)
    return _item(
        class_num, "geometry", "circle_area",
        f"Find the area of a circle of radius {r} cm. "
        f"(Use π = 22/7)",
        Fraction(22 * r * r, 7), {"r": r})


def _geo_circle_radius_from_circumference(rng, class_num):
    r = 7 * rng.randint(1, 6)
    circumference = 44 * r // 7
    return _item(
        class_num, "geometry", "circle_radius_from_circumference",
        f"The circumference of a circle is {circumference} "
        f"cm. Find its radius. (Use π = 22/7)",
        Fraction(r), {"r": r, "circumference": circumference})


def _geo_polygon_interior_sum(rng, class_num):
    n = rng.randint(3, 10)
    return _item(
        class_num, "geometry", "polygon_interior_sum",
        f"Find the sum of the interior angles of a polygon "
        f"with {n} sides.",
        Fraction((n - 2) * 180), {"n": n})


def _geo_regular_polygon_exterior(rng, class_num):
    n = rng.choice([3, 4, 5, 6, 8, 9, 10, 12])
    return _item(
        class_num, "geometry", "regular_polygon_exterior",
        f"Find the exterior angle of a regular polygon "
        f"with {n} sides.",
        Fraction(360, n), {"n": n})


def _geo_parallel_lines_angle(rng, class_num):
    a = rng.randint(25, 155)
    variant = rng.choice(["corresponding", "co_interior"])
    if variant == "corresponding":
        question = (f"Two parallel lines are cut by a "
                    f"transversal. One angle is {a}°. Find "
                    f"the corresponding angle.")
        value = Fraction(a)
    else:
        question = (f"Two parallel lines are cut by a "
                    f"transversal. One interior angle on one "
                    f"side is {a}°. Find the interior angle "
                    f"on the same side of the transversal.")
        value = Fraction(180 - a)
    return _item(
        class_num, "geometry", "parallel_lines_angle",
        question, value, {"a": a, "variant": variant})


_TRIPLES = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17),
            (9, 12, 15), (7, 24, 25), (12, 16, 20),
            (20, 21, 29)]


def _geo_pythagoras(rng, class_num):
    p, q, h = rng.choice(_TRIPLES)
    variant = rng.choice(["hypotenuse", "leg"])
    params = {"p": p, "q": q, "h": h, "variant": variant}
    if variant == "hypotenuse":
        return _item(
            class_num, "geometry", "pythagoras",
            f"A right-angled triangle has legs {p} cm and "
            f"{q} cm. Find the hypotenuse.",
            Fraction(h), params)
    given, other = (p, q) if rng.random() < 0.5 else (q, p)
    params["given_leg"] = given
    return _item(
        class_num, "geometry", "pythagoras",
        f"The hypotenuse of a right-angled triangle is "
        f"{h} cm and one leg is {given} cm. Find the "
        f"other leg.",
        Fraction(other), params)


def _geo_sector_area(rng, class_num):
    r = 7 * rng.randint(1, 3)
    theta = rng.choice([30, 45, 60, 90, 120, 180, 270])
    return _item(
        class_num, "geometry", "sector_area",
        f"Find the area of a sector of angle {theta}° in "
        f"a circle of radius {r} cm. (Use π = 22/7)",
        Fraction(theta * 22 * r * r, 360 * 7),
        {"r": r, "theta": theta})


def _geo_coordinate_distance(rng, class_num):
    variant = rng.choice(["axis", "origin"])
    if variant == "axis":
        x1 = rng.randint(-10, 10)
        x2 = rng.randint(-10, 10)
        while x2 == x1:
            x2 = rng.randint(-10, 10)
        return _item(
            class_num, "geometry", "coordinate_distance",
            f"Find the distance between the points "
            f"({x1}, 0) and ({x2}, 0).",
            Fraction(abs(x2 - x1)),
            {"variant": variant, "x1": x1, "x2": x2})
    p, q, h = rng.choice(_TRIPLES)
    return _item(
        class_num, "geometry", "coordinate_distance",
        f"Find the distance of the point ({p}, {q}) from "
        f"the origin.",
        Fraction(h), {"variant": variant, "x": p, "y": q})


def _geo_coordinate_midpoint(rng, class_num):
    def _pair():
        a = rng.randint(-10, 10)
        b = rng.randint(-10, 10)
        while (a + b) % 2:
            b = rng.randint(-10, 10)
        return a, b
    x1, x2 = _pair()
    y1, y2 = _pair()
    mx, my = (x1 + x2) // 2, (y1 + y2) // 2
    return _item(
        class_num, "geometry", "coordinate_midpoint",
        f"Find the midpoint of the line segment joining "
        f"({x1}, {y1}) and ({x2}, {y2}).",
        None, {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
        answer=f"({mx}, {my})")


# ---------------------------------------------------------------------------
# Mensuration
# ---------------------------------------------------------------------------

def _mens_cuboid_volume(rng, class_num):
    length = rng.randint(3, 20)
    breadth = rng.randint(3, 15)
    height = rng.randint(2, 12)
    return _item(
        class_num, "mensuration", "cuboid_volume",
        f"Find the volume of a cuboid of length {length} cm, "
        f"breadth {breadth} cm and height {height} cm.",
        Fraction(length * breadth * height),
        {"length": length, "breadth": breadth, "height": height})


def _mens_cube_surface_area(rng, class_num):
    side = rng.randint(2, 15)
    return _item(
        class_num, "mensuration", "cube_surface_area",
        f"Find the total surface area of a cube of side "
        f"{side} cm.",
        Fraction(6 * side * side), {"side": side})


def _mens_cylinder_volume(rng, class_num):
    k = rng.randint(1, 4)
    r = 7 * k  # π = 22/7 keeps the volume exact
    h = rng.randint(3, 20)
    return _item(
        class_num, "mensuration", "cylinder_volume",
        f"Find the volume of a cylinder of radius {r} cm and "
        f"height {h} cm. (Use π = 22/7)",
        Fraction(22 * r * r * h, 7), {"r": r, "h": h})


def _mens_cone_volume(rng, class_num):
    k = rng.randint(1, 3)
    r = 7 * k
    h = rng.choice([3, 6, 9, 12, 15, 21])
    return _item(
        class_num, "mensuration", "cone_volume",
        f"Find the volume of a cone of radius {r} cm and "
        f"height {h} cm. (Use π = 22/7)",
        Fraction(22 * r * r * h, 7 * 3), {"r": r, "h": h})


# ---------------------------------------------------------------------------
# Mensuration — Wave 54 expansion
# ---------------------------------------------------------------------------

def _mens_cube_volume(rng, class_num):
    side = rng.randint(2, 20)
    return _item(
        class_num, "mensuration", "cube_volume",
        f"Find the volume of a cube of side {side} cm.",
        Fraction(side ** 3), {"side": side})


def _mens_cuboid_surface_area(rng, class_num):
    length = rng.randint(3, 20)
    breadth = rng.randint(3, 15)
    height = rng.randint(2, 12)
    return _item(
        class_num, "mensuration", "cuboid_surface_area",
        f"Find the total surface area of a cuboid of "
        f"length {length} cm, breadth {breadth} cm and "
        f"height {height} cm.",
        Fraction(2 * (length * breadth + breadth * height
                      + height * length)),
        {"length": length, "breadth": breadth,
         "height": height})


def _mens_cuboid_lsa(rng, class_num):
    length = rng.randint(3, 20)
    breadth = rng.randint(3, 15)
    height = rng.randint(2, 12)
    return _item(
        class_num, "mensuration", "cuboid_lsa",
        f"Find the lateral surface area of a cuboid of "
        f"length {length} cm, breadth {breadth} cm and "
        f"height {height} cm.",
        Fraction(2 * height * (length + breadth)),
        {"length": length, "breadth": breadth,
         "height": height})


def _mens_cylinder_csa(rng, class_num):
    r = 7 * rng.randint(1, 4)
    h = rng.randint(3, 20)
    return _item(
        class_num, "mensuration", "cylinder_csa",
        f"Find the curved surface area of a cylinder of "
        f"radius {r} cm and height {h} cm. (Use π = 22/7)",
        Fraction(44 * r * h, 7), {"r": r, "h": h})


def _mens_cylinder_tsa(rng, class_num):
    r = 7 * rng.randint(1, 4)
    h = rng.randint(3, 20)
    return _item(
        class_num, "mensuration", "cylinder_tsa",
        f"Find the total surface area of a cylinder of "
        f"radius {r} cm and height {h} cm. (Use π = 22/7)",
        Fraction(44 * r * (r + h), 7), {"r": r, "h": h})


def _mens_sphere_volume(rng, class_num):
    r = 7 * rng.randint(1, 3)
    return _item(
        class_num, "mensuration", "sphere_volume",
        f"Find the volume of a sphere of radius {r} cm. "
        f"(Use π = 22/7)",
        Fraction(88 * r ** 3, 21), {"r": r})


def _mens_sphere_surface_area(rng, class_num):
    r = 7 * rng.randint(1, 3)
    return _item(
        class_num, "mensuration", "sphere_surface_area",
        f"Find the surface area of a sphere of radius "
        f"{r} cm. (Use π = 22/7)",
        Fraction(88 * r * r, 7), {"r": r})


def _mens_hemisphere_volume(rng, class_num):
    r = 7 * rng.randint(1, 3)
    return _item(
        class_num, "mensuration", "hemisphere_volume",
        f"Find the volume of a hemisphere of radius {r} "
        f"cm. (Use π = 22/7)",
        Fraction(44 * r ** 3, 21), {"r": r})


def _mens_hemisphere_tsa(rng, class_num):
    r = 7 * rng.randint(1, 3)
    return _item(
        class_num, "mensuration", "hemisphere_tsa",
        f"Find the total surface area of a hemisphere of "
        f"radius {r} cm. (Use π = 22/7)",
        Fraction(66 * r * r, 7), {"r": r})


_CONE_TRIPLES = [(7, 24, 25), (14, 48, 50), (21, 20, 29)]


def _mens_cone_csa(rng, class_num):
    r, h, l = rng.choice(_CONE_TRIPLES)
    return _item(
        class_num, "mensuration", "cone_csa",
        f"Find the curved surface area of a cone of "
        f"radius {r} cm and height {h} cm. (Use π = 22/7)",
        Fraction(22 * r * l, 7), {"r": r, "h": h, "l": l})


def _mens_fencing_cost(rng, class_num):
    length = rng.randint(8, 40)
    breadth = rng.randint(6, 30)
    rate = rng.choice([50, 80, 100, 120, 150, 200])
    return _item(
        class_num, "mensuration", "fencing_cost",
        f"A rectangular garden is {length} m long and "
        f"{breadth} m wide. Find the cost of fencing it "
        f"at ₹{rate} per metre.",
        Fraction(2 * (length + breadth) * rate),
        {"length": length, "breadth": breadth, "rate": rate})


def _mens_tiling_cost(rng, class_num):
    length = rng.randint(4, 15)
    breadth = rng.randint(3, 12)
    rate = rng.choice([100, 150, 200, 250, 300, 400])
    return _item(
        class_num, "mensuration", "tiling_cost",
        f"A room is {length} m long and {breadth} m wide. "
        f"Find the cost of tiling its floor at ₹{rate} "
        f"per m².",
        Fraction(length * breadth * rate),
        {"length": length, "breadth": breadth, "rate": rate})


def _mens_litres_capacity(rng, class_num):
    while True:
        length = rng.choice([40, 50, 60, 80, 100])
        breadth = rng.choice([30, 40, 50])
        height = rng.choice([20, 25, 40, 50])
        volume = length * breadth * height
        if volume % 1000 == 0:
            break
    return _item(
        class_num, "mensuration", "litres_capacity",
        f"A water tank is {length} cm long, {breadth} cm "
        f"wide and {height} cm deep. How many litres of "
        f"water can it hold? (1000 cm³ = 1 litre)",
        Fraction(volume // 1000),
        {"length": length, "breadth": breadth,
         "height": height})


# ---------------------------------------------------------------------------
# Probability
# ---------------------------------------------------------------------------

def _prob_bag(rng, class_num):
    red = rng.randint(1, 12)
    blue = rng.randint(1, 12)
    total = red + blue
    return _item(
        class_num, "probability", "bag_probability",
        f"A bag contains {red} red balls and {blue} blue "
        f"balls. One ball is drawn at random. Find the "
        f"probability that it is red.",
        Fraction(red, total), {"red": red, "blue": blue})


def _prob_die_greater(rng, class_num):
    k = rng.randint(1, 5)
    return _item(
        class_num, "probability", "die_greater",
        f"A die is thrown once. Find the probability of "
        f"getting a number greater than {k}.",
        Fraction(6 - k, 6), {"k": k})


def _prob_coins_at_least_one_head(rng, class_num):
    n = rng.randint(1, 3)
    word = {1: "A coin", 2: "Two coins", 3: "Three coins"}[n]
    verb = "is" if n == 1 else "are"
    return _item(
        class_num, "probability", "coins_at_least_one_head",
        f"{word} {verb} tossed. Find the probability of "
        f"getting at least one head.",
        1 - Fraction(1, 2 ** n), {"n": n})


# ---------------------------------------------------------------------------
# Probability — Wave 54 expansion
# ---------------------------------------------------------------------------

def _prob_bag_three_colours(rng, class_num):
    red = rng.randint(1, 10)
    blue = rng.randint(1, 10)
    green = rng.randint(1, 10)
    total = red + blue + green
    ask = rng.choice(["red", "blue", "green"])
    count = {"red": red, "blue": blue, "green": green}[ask]
    return _item(
        class_num, "probability", "bag_three_colours",
        f"A bag contains {red} red balls, {blue} blue "
        f"balls and {green} green balls. One ball is "
        f"drawn at random. Find the probability that "
        f"it is {ask}.",
        Fraction(count, total),
        {"red": red, "blue": blue, "green": green,
         "ask": ask})


def _prob_die_event(rng, class_num):
    variant = rng.choice(["even", "odd", "prime", "multiple"])
    k = 0
    if variant == "even":
        count, phrase = 3, "an even number"
    elif variant == "odd":
        count, phrase = 3, "an odd number"
    elif variant == "prime":
        count, phrase = 3, "a prime number"
    else:
        k = rng.choice([2, 3, 5])
        count = 6 // k
        phrase = f"a multiple of {k}"
    return _item(
        class_num, "probability", "die_event",
        f"A die is thrown once. Find the probability of "
        f"getting {phrase}.",
        Fraction(count, 6), {"variant": variant, "k": k})


def _prob_coins_exactly(rng, class_num):
    n = rng.choice([2, 3])
    k = rng.randint(0, n)
    if k == 0:
        phrase = "no heads"
    elif k == 1:
        phrase = "exactly 1 head"
    else:
        phrase = f"exactly {k} heads"
    return _item(
        class_num, "probability", "coins_exactly_heads",
        f"{n} coins are tossed together. Find the "
        f"probability of getting {phrase}.",
        Fraction(math.comb(n, k), 2 ** n), {"n": n, "k": k})


_CARD_EVENTS = [
    ("a red card", 26), ("a black card", 26),
    ("a king", 4), ("an ace", 4), ("a queen", 4),
    ("a face card", 12), ("a heart", 13), ("a spade", 13),
]


def _prob_card(rng, class_num):
    phrase, favourable = rng.choice(_CARD_EVENTS)
    return _item(
        class_num, "probability", "card_probability",
        f"One card is drawn from a well-shuffled pack of "
        f"52 cards. Find the probability of getting "
        f"{phrase}.",
        Fraction(favourable, 52),
        {"event": phrase, "favourable": favourable})


def _prob_two_dice_sum(rng, class_num):
    s = rng.randint(2, 12)
    count = 6 - abs(s - 7)
    return _item(
        class_num, "probability", "two_dice_sum",
        f"Two dice are thrown together. Find the "
        f"probability that the sum of the numbers "
        f"obtained is {s}.",
        Fraction(count, 36), {"s": s})


def _prob_two_draw(rng, class_num):
    red = rng.randint(2, 10)
    blue = rng.randint(2, 10)
    total = red + blue
    value = Fraction(red, total) * Fraction(red - 1, total - 1)
    return _item(
        class_num, "probability", "two_draw_probability",
        f"A bag contains {red} red balls and {blue} blue "
        f"balls. Two balls are drawn one after another "
        f"without replacement. Find the probability "
        f"that both are red.",
        value, {"red": red, "blue": blue})


def _prob_complement(rng, class_num):
    b = rng.randint(3, 12)
    a = rng.randint(1, b - 1)
    variant = rng.choice(["rain", "event"])
    if variant == "rain":
        question = (f"The probability that it will rain "
                    f"today is {a}/{b}. Find the probability "
                    f"that it will not rain today.")
    else:
        question = (f"If P(E) = {a}/{b}, find the value "
                    f"of P(not E).")
    return _item(
        class_num, "probability", "complement_probability",
        question, Fraction(b - a, b),
        {"a": a, "b": b, "variant": variant})


_WORDS = ["MATHEMATICS", "GEOMETRY", "ALGEBRA", "SCIENCE",
          "TRIANGLE", "FRACTION", "PROBABILITY"]


def _prob_word_letter(rng, class_num):
    word = rng.choice(_WORDS)
    variant = rng.choice(["vowel", "letter"])
    if variant == "vowel":
        count = sum(1 for ch in word if ch in "AEIOU")
        return _item(
            class_num, "probability", "word_letter_probability",
            f"A letter is chosen at random from the word "
            f"{word}. Find the probability that it is a "
            f"vowel.",
            Fraction(count, len(word)),
            {"word": word, "variant": variant, "letter": ""})
    letter = rng.choice(sorted(set(word)))
    return _item(
        class_num, "probability", "word_letter_probability",
        f"A letter is chosen at random from the word "
        f"{word}. Find the probability that it is the "
        f"letter {letter}.",
        Fraction(word.count(letter), len(word)),
        {"word": word, "variant": variant, "letter": letter})


# ---------------------------------------------------------------------------
# Template pools per topic, gated by the class they suit.
# (min_class, builder)
# ---------------------------------------------------------------------------

_POOLS = {
    "arithmetic": [
        (6, _arith_expression),
        (6, _arith_fraction_add),
        (6, _arith_percent),
        (8, _arith_simple_interest),
        # Wave 54
        (6, _arith_integer_add_sub),
        (6, _arith_fraction_subtract),
        (6, _arith_fraction_of),
        (6, _arith_ratio_share),
        (6, _arith_ratio_simplify),
        (6, _arith_unitary),
        (6, _arith_average),
        (6, _arith_hcf),
        (6, _arith_lcm),
        (6, _arith_decimal_add),
        (6, _arith_speed_distance_time),
        (7, _arith_fraction_multiply),
        (7, _arith_fraction_divide),
        (7, _arith_mixed_fraction_add),
        (7, _arith_decimal_multiply),
        (7, _arith_percent_increase),
        (7, _arith_discount_price),
        (7, _arith_exponent_value),
        (7, _arith_profit_loss),
        (8, _arith_find_whole_from_percent),
        (8, _arith_compound_interest),
        (8, _arith_square_of),
        (8, _arith_sqrt_perfect),
        (8, _arith_cube_of),
    ],
    "algebra": [
        (6, _algebra_evaluate),
        (7, _algebra_linear),
        (8, _algebra_expand),
        (9, _algebra_ap_nth),
        (10, _algebra_quadratic_roots),
        # Wave 54
        (7, _algebra_evaluate_quadratic),
        (7, _algebra_evaluate_two_vars),
        (7, _algebra_polynomial_add_sub),
        (7, _algebra_simplify_like_terms),
        (8, _algebra_equation_both_sides),
        (8, _algebra_simultaneous),
        (8, _algebra_identity_square),
        (8, _algebra_identity_diff_square),
        (8, _algebra_identity_numeric),
        (8, _algebra_index_laws),
        (9, _algebra_factorise),
        (10, _algebra_ap_sum),
        (10, _algebra_gp_nth),
        (10, _algebra_gp_sum),
    ],
    "geometry": [
        (6, _geo_supplementary),
        (6, _geo_rectangle_area),
        (7, _geo_triangle_third_angle),
        (7, _geo_circle_circumference),
        # Wave 54
        (6, _geo_complementary),
        (6, _geo_square_area),
        (6, _geo_square_perimeter),
        (6, _geo_rectangle_perimeter),
        (6, _geo_triangle_perimeter),
        (7, _geo_isosceles_angle),
        (7, _geo_triangle_area),
        (7, _geo_circle_area),
        (7, _geo_circle_radius_from_circumference),
        (7, _geo_pythagoras),
        (8, _geo_quadrilateral_fourth),
        (8, _geo_parallelogram_angle),
        (8, _geo_rhombus_area),
        (8, _geo_trapezium_area),
        (8, _geo_polygon_interior_sum),
        (8, _geo_regular_polygon_exterior),
        (9, _geo_triangle_exterior),
        (9, _geo_parallel_lines_angle),
        (10, _geo_sector_area),
        (10, _geo_coordinate_distance),
        (10, _geo_coordinate_midpoint),
    ],
    "mensuration": [
        (6, _mens_cuboid_volume),
        (6, _mens_cube_surface_area),
        (8, _mens_cylinder_volume),
        (9, _mens_cone_volume),
        # Wave 54
        (6, _mens_cube_volume),
        (6, _mens_fencing_cost),
        (7, _mens_tiling_cost),
        (8, _mens_cuboid_surface_area),
        (8, _mens_cylinder_csa),
        (8, _mens_cylinder_tsa),
        (8, _mens_litres_capacity),
        (9, _mens_cuboid_lsa),
        (9, _mens_sphere_volume),
        (9, _mens_sphere_surface_area),
        (9, _mens_hemisphere_volume),
        (9, _mens_hemisphere_tsa),
        (9, _mens_cone_csa),
    ],
    "probability": [
        (6, _prob_bag),
        (6, _prob_die_greater),
        (7, _prob_coins_at_least_one_head),
        # Wave 54
        (7, _prob_bag_three_colours),
        (7, _prob_die_event),
        (9, _prob_complement),
        (9, _prob_word_letter),
        (10, _prob_coins_exactly),
        (10, _prob_card),
        (10, _prob_two_dice_sum),
        (10, _prob_two_draw),
    ],
}


def generate_question(class_num, topic, seed=None):
    """Generate one practice question for a class (6-10) and topic."""
    if class_num not in CLASSES:
        raise ValueError(f"class_num must be one of {CLASSES}")
    if topic not in TOPICS:
        raise ValueError(f"topic must be one of {TOPICS}")
    rng = random.Random(seed)
    pool = [fn for min_class, fn in _POOLS[topic]
            if class_num >= min_class]
    builder = rng.choice(pool)
    return builder(rng, class_num)


def generate_set(class_num, topic, count=5, seed=None):
    """Generate `count` practice questions (deterministic per seed)."""
    rng = random.Random(seed)
    return [generate_question(class_num, topic,
                               seed=rng.randrange(1 << 30))
            for _ in range(count)]
