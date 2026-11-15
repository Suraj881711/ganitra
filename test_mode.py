"""Wave 43: Chapter Test Mode — timed topic tests with scores.

The Board Mode chapter test (Wave 5, /board/test/*) is tied to
NCERT chapters and the board_quiz generators. This module is the
complementary piece the Wave 34 generator was built for: a timed
test over the practice_gen topics (arithmetic, algebra, geometry,
mensuration, probability) for Classes 6-10, scored with EXACT
fraction arithmetic instead of the quiz engine's float tolerance,
so "3/4", "0.75" and "6/8" are all the same answer and no correct
answer is ever lost to rounding.

Public API:
    generate_test(class_num, topic, seed=None) -> [item, ...]
        TEST_QUESTION_COUNT unique questions. Each item is a
        JSON-safe projection of a practice_gen item (the raw item
        holds a Fraction, which the session cookie cannot store):
        {class_num, topic, kind, question, answer, answer_value,
        params} where answer_value is a "num/den" string or None
        (the string-answer kinds: expand_binomials,
        quadratic_roots, and the Wave 54 text kinds
        ratio_simplify, factorise_quadratic, identity_square,
        identity_diff_square, polynomial_add_sub,
        simplify_like_terms, coordinate_midpoint — those are
        checked from params instead).
    check_test_answer(item, given) -> bool
    worked_steps(item) -> [str, ...]
        Plain working lines in the house style (no step numbers),
        ending with "Answer: ..." — derived from the item's own
        params, so the working always matches the question asked.
"""
import math
import random
import re
from fractions import Fraction

import practice_gen

TEST_QUESTION_COUNT = 10
TEST_SECONDS_PER_QUESTION = 90  # 10 questions -> 15 minutes
TEST_TIME_LIMIT = TEST_QUESTION_COUNT * TEST_SECONDS_PER_QUESTION

TOPIC_LABELS = {
    "arithmetic": "Arithmetic",
    "algebra": "Algebra",
    "geometry": "Geometry",
    "mensuration": "Mensuration",
    "probability": "Probability",
}


# ------------------------------------------------------------------
# Generation
# ------------------------------------------------------------------

def _project(item):
    value = item["answer_value"]
    return {
        "class_num": item["class_num"],
        "topic": item["topic"],
        "kind": item["kind"],
        "question": item["question"],
        "answer": item["answer"],
        "answer_value": (None if value is None else
                         f"{value.numerator}/{value.denominator}"),
        "params": item["params"],
    }


def generate_test(class_num, topic, seed=None):
    """10 unique practice_gen questions for one class + topic."""
    if class_num not in practice_gen.CLASSES:
        raise ValueError(
            f"class_num must be one of {practice_gen.CLASSES}")
    if topic not in practice_gen.TOPICS:
        raise ValueError(f"topic must be one of {practice_gen.TOPICS}")
    rng = random.Random(seed)
    items, seen = [], set()
    attempts = 0
    while len(items) < TEST_QUESTION_COUNT and attempts < 500:
        attempts += 1
        item = practice_gen.generate_question(
            class_num, topic, seed=rng.randrange(1 << 30))
        if item["question"] in seen:
            continue
        seen.add(item["question"])
        items.append(_project(item))
    if len(items) < TEST_QUESTION_COUNT:
        raise ValueError("could not generate enough unique questions")
    return items


# ------------------------------------------------------------------
# Answer checking (exact, Fraction-based)
# ------------------------------------------------------------------

_MIXED_RE = re.compile(r"^([+-]?\d+)\s+(\d+)\s*/\s*(\d+)$")
_NUM_RE = re.compile(r"[+-]?\d+(?:\.\d+)?(?:\s*/\s*\d+)?")


def parse_student_number(text):
    """Parse a student's typed answer into an exact Fraction.

    Accepts "42", "-3", "3/4", "6/8", "0.75", "1 1/2", "x = 42"
    (anything after the last "=" is the answer) and a trailing
    "%". Returns None when nothing numeric can be read."""
    if text is None:
        return None
    t = str(text).strip().lower()
    if "=" in t:
        t = t.split("=")[-1].strip()
    t = t.rstrip("%").strip().replace(",", "").replace("₹", "")
    t = t.replace("−", "-")
    if not t:
        return None
    m = _MIXED_RE.match(t)
    if m:
        whole, num, den = (int(m.group(1)), int(m.group(2)),
                           int(m.group(3)))
        if den == 0:
            return None
        sign = -1 if whole < 0 else 1
        return Fraction(whole) + sign * Fraction(num, den)
    try:
        return Fraction(t)
    except (ValueError, ZeroDivisionError):
        pass
    try:
        from decimal import Decimal
        return Fraction(Decimal(t))
    except Exception:
        return None


def _expected_fraction(item):
    raw = item.get("answer_value")
    if raw is None:
        return None
    return Fraction(raw)


def _check_quadratic(item, given):
    """'x = 3 or x = -2' style: the set of numbers typed must be
    exactly the two roots stored in params."""
    p = item["params"]
    roots = {Fraction(p["r1"]), Fraction(p["r2"])}
    found = set()
    for token in _NUM_RE.findall(str(given).replace("−", "-")):
        try:
            found.add(Fraction(token.replace(" ", "")))
        except (ValueError, ZeroDivisionError):
            continue
    return found == roots


def _poly_coeffs(text):
    """Parse an expanded quadratic in x into (x^2, x, constant)
    coefficients, or None. Tolerates ^2/², missing coefficients
    ("x", "-x") and any term order."""
    t = str(text).strip().lower().replace(" ", "")
    t = t.replace("²", "^2").replace("**", "^").replace("−", "-")
    if "=" in t:
        t = t.split("=")[-1]
    if "x" not in t:
        return None
    coeffs = [Fraction(0), Fraction(0), Fraction(0)]  # x^2, x, const
    for term in re.findall(r"[+-]?[^+-]+", t):
        if not term:
            continue
        sign = 1
        if term[0] == "+":
            term = term[1:]
        elif term[0] == "-":
            sign = -1
            term = term[1:]
        if not term:
            return None
        try:
            if term.endswith("x^2"):
                num = term[:-3]
                coeffs[0] += sign * (Fraction(num) if num
                                     else Fraction(1))
            elif term.endswith("x"):
                num = term[:-1]
                coeffs[1] += sign * (Fraction(num) if num
                                     else Fraction(1))
            else:
                coeffs[2] += sign * Fraction(term)
        except (ValueError, ZeroDivisionError):
            return None
    return tuple(coeffs)


def _check_expand(item, given):
    p = item["params"]
    expected = (Fraction(1), Fraction(p["a"] + p["b"]),
                Fraction(p["a"] * p["b"]))
    return _poly_coeffs(given) == expected


# --- Wave 54 text-answer kinds ------------------------------------

def _check_ratio(item, given):
    """'3:4' (or '3/4', spaces forgiven) must be the reduced
    form of the params ratio — an unreduced pair is wrong."""
    p = item["params"]
    g = math.gcd(p["a"], p["b"])
    m = re.search(r"(\d+)\s*[:/]\s*(\d+)", str(given))
    if not m:
        return False
    return (int(m.group(1)), int(m.group(2))) == (
        p["a"] // g, p["b"] // g)


def _check_factorise(item, given):
    """'(x + 3)(x − 2)' in either order: the two binomial
    constants read off the text must be the params pair."""
    p = item["params"]
    t = str(given).replace("−", "-")
    found = [int(num) if sign == "+" else -int(num)
             for sign, num in
             re.findall(r"x\s*([+-])\s*(\d+)", t)]
    return len(found) == 2 and sorted(found) == sorted(
        [p["a"], p["b"]])


def _check_poly_answer(item, given):
    """identity_square / identity_diff_square /
    polynomial_add_sub: compare x²/x/constant coefficients."""
    p = item["params"]
    kind = item["kind"]
    if kind == "identity_square":
        a = p["a"]
        expected = (Fraction(1), Fraction(2 * a),
                    Fraction(a * a))
    elif kind == "identity_diff_square":
        a = p["a"]
        expected = (Fraction(1), Fraction(0),
                    Fraction(-a * a))
    else:
        s = 1 if p["variant"] == "add" else -1
        expected = (Fraction(0),
                    Fraction(p["a1"] + s * p["a2"]),
                    Fraction(p["b1"] + s * p["b2"]))
    return _poly_coeffs(given) == expected


def _check_like_terms(item, given):
    p = item["params"]
    total = p["a"] + p["b"] - p["c"]
    t = str(given).strip().replace("−", "-").replace(" ", "")
    m = re.fullmatch(r"([+-]?\d+)x", t)
    if m:
        return int(m.group(1)) == total
    if t in ("x", "+x"):
        return total == 1
    if t == "-x":
        return total == -1
    return False


def _check_midpoint(item, given):
    p = item["params"]
    expected = [Fraction(p["x1"] + p["x2"], 2),
                Fraction(p["y1"] + p["y2"], 2)]
    found = []
    for token in _NUM_RE.findall(str(given).replace("−", "-")):
        try:
            found.append(Fraction(token.replace(" ", "")))
        except (ValueError, ZeroDivisionError):
            continue
    return found == expected


def check_test_answer(item, given):
    """Exact check of one typed answer against a test item."""
    if given is None or not str(given).strip():
        return False
    expected = _expected_fraction(item)
    if expected is not None:
        got = parse_student_number(given)
        if got is None:
            return False
        if got == expected:
            return True
        # "75%" for a probability-style answer below 1 means 0.75.
        t = str(given).strip()
        if t.endswith("%") and expected < 1:
            return got / 100 == expected
        return False
    if item["kind"] == "quadratic_roots":
        return _check_quadratic(item, given)
    if item["kind"] == "expand_binomials":
        return _check_expand(item, given)
    if item["kind"] == "ratio_simplify":
        return _check_ratio(item, given)
    if item["kind"] == "factorise_quadratic":
        return _check_factorise(item, given)
    if item["kind"] in ("identity_square",
                        "identity_diff_square",
                        "polynomial_add_sub"):
        return _check_poly_answer(item, given)
    if item["kind"] == "simplify_like_terms":
        return _check_like_terms(item, given)
    if item["kind"] == "coordinate_midpoint":
        return _check_midpoint(item, given)
    return str(given).strip().lower() == item["answer"].strip().lower()


# ------------------------------------------------------------------
# Worked answers (house style: plain lines, final Answer line)
# ------------------------------------------------------------------

def _f(value):
    """Format a Fraction/int the way practice_gen answers look."""
    return practice_gen._fmt(Fraction(value))


def _signed(value):
    """'+ 3' / '- 3' fragment for a signed int."""
    value = int(value)
    return f"+ {value}" if value >= 0 else f"− {abs(value)}"


def worked_steps(item):
    p = item["params"]
    kind = item["kind"]
    ans = item["answer"]
    lines = []
    if kind == "expression":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        lines = [f"Multiplication first: {b} × {c} = {b * c}",
                 f"{a} + {b * c} − {d} = {_f(a + b * c - d)}"]
    elif kind == "fraction_add":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        den = b * d
        num = a * d + c * b
        lines = [f"Common denominator: {b} × {d} = {den}",
                 f"{a}/{b} = {a * d}/{den} and {c}/{d} = {c * b}/{den}",
                 f"Add: {a * d}/{den} + {c * b}/{den} = {num}/{den}"]
        reduced = Fraction(num, den)
        if reduced.denominator != den:
            lines.append(f"Simplify: {num}/{den} = {_f(reduced)}")
    elif kind == "percent":
        lines = [f"{p['p']}% of {p['n']} = {p['p']}/100 × {p['n']}",
                 f"= {_f(Fraction(p['p'] * p['n'], 100))}"]
    elif kind == "simple_interest":
        lines = ["Simple Interest = P × R × T / 100",
                 f"= {p['principal']} × {p['rate']} × {p['years']} / 100",
                 f"= {_f(Fraction(p['principal'] * p['rate'] * p['years'], 100))}"]
    elif kind == "linear_equation":
        a, b, c = p["a"], p["b"], p["c"]
        lines = [f"{a}x {_signed(b)} = {c}",
                 f"{a}x = {c} {_signed(-b)} = {c - b}",
                 f"x = {c - b} / {a} = {_f(Fraction(c - b, a))}"]
    elif kind == "evaluate_linear":
        lines = [f"Put x = {p['x']}: {p['a']} × {p['x']} "
                 f"{_signed(p['b'])}",
                 f"= {p['a'] * p['x'] + p['b']}"]
    elif kind == "expand_binomials":
        a, b = p["a"], p["b"]
        s, prod = a + b, a * b
        lines = [f"(x {_signed(a)})(x {_signed(b)}) "
                 f"= x² {_signed(a)}x {_signed(b)}x {_signed(prod)}",
                 f"= x² {_signed(s)}x {_signed(prod)}"]
    elif kind == "ap_nth_term":
        a, d, n = p["a"], p["d"], p["n"]
        lines = [f"First term a = {a}, common difference d = {d}",
                 f"a{n} = a + (n − 1) × d = {a} + {n - 1} × {d}",
                 f"= {a + (n - 1) * d}"]
    elif kind == "quadratic_roots":
        r1, r2 = p["r1"], p["r2"]
        lines = [f"Factors: (x {_signed(-r1)})(x {_signed(-r2)}) = 0",
                 f"So x = {r1} or x = {r2}"]
    elif kind == "supplementary_angle":
        lines = ["Supplementary angles add up to 180°",
                 f"Other angle = 180° − {p['a']}° = {180 - p['a']}°"]
    elif kind == "triangle_third_angle":
        lines = ["The angles of a triangle add up to 180°",
                 f"Third angle = 180° − {p['a']}° − {p['b']}° "
                 f"= {180 - p['a'] - p['b']}°"]
    elif kind == "rectangle_area":
        lines = ["Area of a rectangle = length × breadth",
                 f"= {p['length']} × {p['breadth']} "
                 f"= {p['length'] * p['breadth']}"]
    elif kind == "circle_circumference":
        lines = ["Circumference = 2 × π × r",
                 f"= 2 × 22/7 × {p['r']} = {_f(Fraction(44 * p['r'], 7))}"]
    elif kind == "cuboid_volume":
        lines = ["Volume of a cuboid = length × breadth × height",
                 f"= {p['length']} × {p['breadth']} × {p['height']} "
                 f"= {p['length'] * p['breadth'] * p['height']}"]
    elif kind == "cube_surface_area":
        lines = ["Total surface area of a cube = 6 × side²",
                 f"= 6 × {p['side']}² = {6 * p['side'] * p['side']}"]
    elif kind == "cylinder_volume":
        lines = ["Volume of a cylinder = π × r² × h",
                 f"= 22/7 × {p['r']}² × {p['h']} "
                 f"= {_f(Fraction(22 * p['r'] * p['r'] * p['h'], 7))}"]
    elif kind == "cone_volume":
        lines = ["Volume of a cone = (1/3) × π × r² × h",
                 f"= 1/3 × 22/7 × {p['r']}² × {p['h']} "
                 f"= {_f(Fraction(22 * p['r'] * p['r'] * p['h'], 21))}"]
    elif kind == "bag_probability":
        total = p["red"] + p["blue"]
        lines = [f"Total balls = {p['red']} + {p['blue']} = {total}",
                 f"P(red) = {p['red']}/{total} = {_f(Fraction(p['red'], total))}"]
    elif kind == "die_greater":
        lines = [f"Numbers greater than {p['k']} on a die: "
                 f"{6 - p['k']} out of 6",
                 f"Probability = {6 - p['k']}/6 "
                 f"= {_f(Fraction(6 - p['k'], 6))}"]
    elif kind == "coins_at_least_one_head":
        n = p["n"]
        lines = [f"P(at least one head) = 1 − P(no heads)",
                 f"= 1 − (1/2)^{n} = 1 − {_f(Fraction(1, 2 ** n))} "
                 f"= {_f(1 - Fraction(1, 2 ** n))}"]
    # ---------------- Wave 54 kinds ----------------
    elif kind == "integer_add_sub":
        a, b = p["a"], p["b"]
        if p["op"] == "add":
            lines = [f"({a}) + ({b}) = {a + b}"]
        else:
            lines = [f"({a}) − ({b}) = {a - b}"]
    elif kind == "fraction_subtract":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        den = b * d
        num = a * d - c * b
        lines = [f"Common denominator: {b} × {d} = {den}",
                 f"{a}/{b} = {a * d}/{den} and {c}/{d} = {c * b}/{den}",
                 f"Subtract: {a * d}/{den} − {c * b}/{den} = {num}/{den}"]
        reduced = Fraction(num, den)
        if reduced.denominator != den:
            lines.append(f"Simplify: {num}/{den} = {_f(reduced)}")
    elif kind == "fraction_of":
        n, d, q = p["n"], p["d"], p["quantity"]
        lines = [f"{n}/{d} of {q} = {n} × {q} ÷ {d}",
                 f"= {n} × {q // d} = {n * (q // d)}"]
    elif kind == "fraction_multiply":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        lines = [f"Multiply the numerators: {a} × {c} = {a * c}",
                 f"Multiply the denominators: {b} × {d} = {b * d}",
                 f"= {a * c}/{b * d}"]
        reduced = Fraction(a * c, b * d)
        if reduced.denominator != b * d:
            lines.append(f"Simplify: {a * c}/{b * d} = {_f(reduced)}")
    elif kind == "fraction_divide":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        lines = [f"Flip the second fraction and multiply: "
                 f"{a}/{b} × {d}/{c}",
                 f"= {a * d}/{b * c}"]
        reduced = Fraction(a * d, b * c)
        if reduced.denominator != b * c:
            lines.append(f"Simplify: {a * d}/{b * c} = {_f(reduced)}")
    elif kind == "mixed_fraction_add":
        top1 = p["w1"] * p["d1"] + p["n1"]
        top2 = p["w2"] * p["d2"] + p["n2"]
        den = p["d1"] * p["d2"]
        num = top1 * p["d2"] + top2 * p["d1"]
        lines = [f"{p['w1']} {p['n1']}/{p['d1']} = {top1}/{p['d1']} "
                 f"and {p['w2']} {p['n2']}/{p['d2']} = {top2}/{p['d2']}",
                 f"Add: {top1}/{p['d1']} + {top2}/{p['d2']} "
                 f"= {num}/{den}"]
        reduced = Fraction(num, den)
        if reduced.denominator != den:
            lines.append(f"Simplify: {num}/{den} = {_f(reduced)}")
    elif kind == "decimal_add":
        lines = ["Line up the decimal points and add",
                 f"{p['a']} + {p['b']} = {ans}"]
    elif kind == "decimal_multiply":
        ia = int(p["a"].replace(".", ""))
        ib = int(p["b"].replace(".", ""))
        lines = [f"Ignore the decimal points: {ia} × {ib} "
                 f"= {ia * ib}",
                 f"Each number has 1 decimal place, so the "
                 f"product has 2: {ans}"]
    elif kind == "percent_increase":
        inc = Fraction(p["price"] * p["p"], 100)
        lines = [f"Increase = {p['p']}% of {p['price']} "
                 f"= {_f(inc)}",
                 f"New price = {p['price']} + {_f(inc)} "
                 f"= {ans}"]
    elif kind == "discount_price":
        off = Fraction(p["price"] * p["p"], 100)
        lines = [f"Discount = {p['p']}% of ₹{p['price']} "
                 f"= ₹{_f(off)}",
                 f"Selling price = {p['price']} − {_f(off)} "
                 f"= {ans}"]
    elif kind == "find_whole_from_percent":
        one = Fraction(p["part"], p["p"])
        lines = [f"{p['p']}% of the number = {p['part']}",
                 f"1% of the number = {p['part']} ÷ {p['p']} "
                 f"= {_f(one)}",
                 f"The number = {_f(one)} × 100 = {ans}"]
    elif kind == "ratio_share":
        parts = p["a"] + p["b"]
        each = p["total"] // parts
        share = p["a"] if p["ask"] == "first" else p["b"]
        lines = [f"Total parts = {p['a']} + {p['b']} = {parts}",
                 f"Each part = ₹{p['total']} ÷ {parts} = ₹{each}",
                 f"{p['ask']} part = {share} × {each} "
                 f"= {ans}"]
    elif kind == "ratio_simplify":
        g = math.gcd(p["a"], p["b"])
        lines = [f"HCF of {p['a']} and {p['b']} is {g}",
                 f"Divide both by {g}: {p['a']} ÷ {g} "
                 f"= {p['a'] // g} and {p['b']} ÷ {g} "
                 f"= {p['b'] // g}"]
    elif kind == "unitary_method":
        lines = [f"Cost of 1 pen = ₹{p['total']} ÷ {p['n']} "
                 f"= ₹{p['unit']}",
                 f"Cost of {p['m']} pens = {p['unit']} × "
                 f"{p['m']} = {ans}"]
    elif kind == "average":
        nums = p["nums"]
        lines = [f"Sum = {' + '.join(str(x) for x in nums)} "
                 f"= {sum(nums)}",
                 f"Average = {sum(nums)} ÷ {len(nums)} = {ans}"]
    elif kind == "hcf":
        x, y = max(p["a"], p["b"]), min(p["a"], p["b"])
        lines = []
        while y:
            lines.append(f"{x} = {x // y} × {y} + {x % y}")
            x, y = y, x % y
        lines.append(f"The last non-zero remainder is the HCF")
    elif kind == "lcm":
        g = math.gcd(p["a"], p["b"])
        lines = [f"LCM = {p['a']} × {p['b']} ÷ HCF({p['a']}, "
                 f"{p['b']})",
                 f"= {p['a'] * p['b']} ÷ {g} = {ans}"]
    elif kind == "compound_interest":
        lines = ["Amount = P × (1 + R/100)^T"]
        amt = Fraction(p["principal"])
        for yr in range(1, p["years"] + 1):
            interest_y = Fraction(amt * p["rate"], 100)
            amt += interest_y
            lines.append(f"Year {yr}: interest = "
                         f"{_f(interest_y)}, amount = {_f(amt)}")
        lines.append(f"Compound interest = {_f(amt)} − "
                     f"{p['principal']} = {ans}")
    elif kind == "square_of":
        lines = [f"{p['n']}² = {p['n']} × {p['n']} "
                 f"= {p['n'] * p['n']}"]
    elif kind == "sqrt_perfect":
        lines = [f"{p['root']} × {p['root']} = {p['number']}",
                 f"So the square root of {p['number']} is "
                 f"{p['root']}"]
    elif kind == "cube_of":
        lines = [f"{p['n']}³ = {p['n']} × {p['n']} × {p['n']} "
                 f"= {p['n'] ** 3}"]
    elif kind == "exponent_value":
        chain = " × ".join([str(p["base"])] * p["exp"])
        lines = [f"{p['base']}^{p['exp']} = {chain} = {ans}"]
    elif kind == "profit_loss":
        if p["variant"] == "profit":
            lines = [f"Profit = SP − CP = {p['sp']} − "
                     f"{p['cp']} = {ans}"]
        else:
            lines = [f"Loss = CP − SP = {p['cp']} − "
                     f"{p['sp']} = {ans}"]
    elif kind == "speed_distance_time":
        if p["variant"] == "speed":
            lines = [f"Speed = distance ÷ time "
                     f"= {p['distance']} ÷ {p['time']} "
                     f"= {ans} km/h"]
        elif p["variant"] == "distance":
            lines = [f"Distance = speed × time "
                     f"= {p['speed']} × {p['time']} "
                     f"= {ans} km"]
        else:
            lines = [f"Time = distance ÷ speed "
                     f"= {p['distance']} ÷ {p['speed']} "
                     f"= {ans} hours"]
    elif kind == "evaluate_quadratic":
        a, b, c, x = p["a"], p["b"], p["c"], p["x"]
        lines = [f"Put x = {x}: {a} × ({x})² {_signed(b)} "
                 f"× ({x}) {_signed(c)}",
                 f"= {a * x * x} {_signed(b * x)} "
                 f"{_signed(c)} = {ans}"]
    elif kind == "evaluate_two_vars":
        lines = [f"Put x = {p['x']} and y = {p['y']}: "
                 f"{p['a']} × {p['x']} + {p['b']} × {p['y']}",
                 f"= {p['a'] * p['x']} {_signed(p['b'] * p['y'])} "
                 f"= {ans}"]
    elif kind == "equation_both_sides":
        a, b, c, d = p["a"], p["b"], p["c"], p["d"]
        lines = [f"{a}x {_signed(b)} = {c}x {_signed(d)}",
                 f"{a}x − {c}x = {d} {_signed(-b)} = {d - b}",
                 f"{a - c}x = {d - b}",
                 f"x = {d - b} ÷ {a - c} = {ans}"]
    elif kind == "simultaneous":
        s = p["x"] + p["y"]
        d = p["x"] - p["y"]
        lines = [f"x + y = {s} and x − y = {d}",
                 f"Adding the equations: 2x = {s} + {d} "
                 f"= {2 * p['x']}",
                 f"x = {p['x']}"]
        if p["ask"] == "y":
            lines.append(f"y = {s} − {p['x']} = {p['y']}")
    elif kind == "factorise_quadratic":
        a, b = p["a"], p["b"]
        lines = [f"Find two numbers with sum {a + b} and "
                 f"product {a * b}: they are {a} and {b}",
                 f"x² {_signed(a + b)}x {_signed(a * b)} "
                 f"= {practice_gen._binom(a)}"
                 f"{practice_gen._binom(b)}"]
    elif kind == "identity_square":
        a = p["a"]
        lines = [f"Using (x + b)² = x² + 2bx + b² with "
                 f"b = {a}",
                 f"= x² {_signed(2 * a)}x {_signed(a * a)}"]
    elif kind == "identity_diff_square":
        lines = ["Using (x + a)(x − a) = x² − a²",
                 f"= x² − {p['a']}² = x² − {p['a'] * p['a']}"]
    elif kind == "identity_numeric":
        if p["variant"] == "square":
            n = p["n"]
            k = n - 100
            if k > 0:
                lines = [f"{n}² = (100 + {k})² "
                         f"= 100² + 2 × 100 × {k} + {k}²",
                         f"= 10000 + {200 * k} + {k * k} "
                         f"= {ans}"]
            else:
                k = -k
                lines = [f"{n}² = (100 − {k})² "
                         f"= 100² − 2 × 100 × {k} + {k}²",
                         f"= 10000 − {200 * k} + {k * k} "
                         f"= {ans}"]
        else:
            m, k = p["m"], p["k"]
            lines = [f"{m - k} × {m + k} = {m}² − {k}²",
                     f"= {m * m} − {k * k} = {ans}"]
    elif kind == "ap_sum":
        a, d, n = p["a"], p["d"], p["n"]
        lines = [f"S{n} = n/2 × (2a + (n − 1) × d)",
                 f"= {n}/2 × (2 × {a} + {n - 1} × {d}) "
                 f"= {ans}"]
    elif kind == "gp_nth_term":
        a, r, n = p["a"], p["r"], p["n"]
        lines = [f"nth term = a × r^(n − 1)",
                 f"= {a} × {r}^{n - 1} = {a} × {r ** (n - 1)} "
                 f"= {ans}"]
    elif kind == "gp_sum":
        a, r, n = p["a"], p["r"], p["n"]
        lines = [f"S{n} = a × (r^n − 1) ÷ (r − 1)",
                 f"= {a} × ({r ** n} − 1) ÷ {r - 1} = {ans}"]
    elif kind == "polynomial_add_sub":
        if p["variant"] == "add":
            lines = [f"Add the x terms: {p['a1']}x + "
                     f"{p['a2']}x = {p['a1'] + p['a2']}x",
                     f"Add the constants: {p['b1']} "
                     f"{_signed(p['b2'])} = {p['b1'] + p['b2']}"]
        else:
            lines = [f"Subtract the x terms: {p['a1']}x − "
                     f"{p['a2']}x = {p['a1'] - p['a2']}x",
                     f"Subtract the constants: {p['b1']} "
                     f"{_signed(-p['b2'])} = {p['b1'] - p['b2']}"]
    elif kind == "simplify_like_terms":
        total = p["a"] + p["b"] - p["c"]
        lines = [f"{p['a']}x + {p['b']}x − {p['c']}x "
                 f"= ({p['a']} + {p['b']} − {p['c']})x",
                 f"= {total}x"]
    elif kind == "index_laws":
        base, m, n = p["base"], p["m"], p["n"]
        if p["variant"] == "product":
            lines = [f"{base}^{m} × {base}^{n} "
                     f"= {base}^({m} + {n}) = {base}^{m + n}",
                     f"= {ans}"]
        elif p["variant"] == "quotient":
            lines = [f"{base}^{m} ÷ {base}^{n} "
                     f"= {base}^({m} − {n}) = {base}^{m - n}",
                     f"= {ans}"]
        else:
            lines = [f"({base}^{m})^{n} = {base}^({m} × {n}) "
                     f"= {base}^{m * n}",
                     f"= {ans}"]
    elif kind == "complementary_angle":
        lines = ["Complementary angles add up to 90°",
                 f"Other angle = 90° − {p['a']}° "
                 f"= {90 - p['a']}°"]
    elif kind == "triangle_exterior_angle":
        if p["variant"] == "exterior":
            lines = ["Exterior angle = sum of the two "
                     "opposite interior angles",
                     f"= {p['p']}° + {p['q']}° "
                     f"= {p['p'] + p['q']}°"]
        else:
            lines = ["Exterior angle = sum of the two "
                     "opposite interior angles",
                     f"Other angle = {p['exterior']}° − "
                     f"{p['p']}° = {p['exterior'] - p['p']}°"]
    elif kind == "isosceles_angle":
        if p["variant"] == "base":
            lines = ["The two base angles are equal",
                     f"Each base angle = (180° − "
                     f"{p['vertex']}°) ÷ 2 "
                     f"= {(180 - p['vertex']) // 2}°"]
        else:
            lines = [f"Two base angles = 2 × {p['base']}° "
                     f"= {2 * p['base']}°",
                     f"Vertex angle = 180° − "
                     f"{2 * p['base']}° = {180 - 2 * p['base']}°"]
    elif kind == "quadrilateral_fourth_angle":
        rest = p["a"] + p["b"] + p["c"]
        lines = ["The angles of a quadrilateral add up "
                 "to 360°",
                 f"Fourth angle = 360° − {rest}° "
                 f"= {360 - rest}°"]
    elif kind == "parallelogram_angle":
        if p["variant"] == "opposite":
            lines = ["Opposite angles of a parallelogram "
                     "are equal",
                     f"Opposite angle = {p['a']}°"]
        else:
            lines = ["Adjacent angles of a parallelogram "
                     "add up to 180°",
                     f"Adjacent angle = 180° − {p['a']}° "
                     f"= {180 - p['a']}°"]
    elif kind == "square_area":
        lines = ["Area of a square = side × side",
                 f"= {p['side']} × {p['side']} "
                 f"= {p['side'] * p['side']}"]
    elif kind == "square_perimeter":
        lines = ["Perimeter of a square = 4 × side",
                 f"= 4 × {p['side']} = {4 * p['side']}"]
    elif kind == "rectangle_perimeter":
        lines = ["Perimeter of a rectangle "
                 "= 2 × (length + breadth)",
                 f"= 2 × ({p['length']} + {p['breadth']}) "
                 f"= {2 * (p['length'] + p['breadth'])}"]
    elif kind == "triangle_area":
        lines = ["Area of a triangle = 1/2 × base × height",
                 f"= 1/2 × {p['base']} × {p['height']} "
                 f"= {_f(Fraction(p['base'] * p['height'], 2))}"]
    elif kind == "triangle_perimeter":
        lines = ["Perimeter = sum of the three sides",
                 f"= {p['a']} + {p['b']} + {p['c']} "
                 f"= {p['a'] + p['b'] + p['c']}"]
    elif kind == "rhombus_area":
        lines = ["Area of a rhombus = 1/2 × d1 × d2",
                 f"= 1/2 × {p['d1']} × {p['d2']} "
                 f"= {_f(Fraction(p['d1'] * p['d2'], 2))}"]
    elif kind == "trapezium_area":
        lines = ["Area of a trapezium = 1/2 × (sum of "
                 "parallel sides) × height",
                 f"= 1/2 × ({p['a']} + {p['b']}) × {p['h']} "
                 f"= {_f(Fraction((p['a'] + p['b']) * p['h'], 2))}"]
    elif kind == "circle_area":
        lines = ["Area of a circle = π × r²",
                 f"= 22/7 × {p['r']}² "
                 f"= {_f(Fraction(22 * p['r'] * p['r'], 7))}"]
    elif kind == "circle_radius_from_circumference":
        lines = ["Circumference = 2 × π × r",
                 f"{p['circumference']} = 2 × 22/7 × r",
                 f"r = {p['circumference']} × 7 ÷ 44 "
                 f"= {p['r']}"]
    elif kind == "polygon_interior_sum":
        lines = ["Sum of interior angles = (n − 2) × 180°",
                 f"= ({p['n']} − 2) × 180° "
                 f"= {(p['n'] - 2) * 180}°"]
    elif kind == "regular_polygon_exterior":
        lines = ["The exterior angles of a polygon add "
                 "up to 360°",
                 f"Each exterior angle = 360° ÷ {p['n']} "
                 f"= {_f(Fraction(360, p['n']))}°"]
    elif kind == "parallel_lines_angle":
        if p["variant"] == "corresponding":
            lines = ["Corresponding angles are equal",
                     f"Corresponding angle = {p['a']}°"]
        else:
            lines = ["Co-interior angles add up to 180°",
                     f"Angle = 180° − {p['a']}° "
                     f"= {180 - p['a']}°"]
    elif kind == "pythagoras":
        if p["variant"] == "hypotenuse":
            lines = [f"By Pythagoras' theorem: h² "
                     f"= {p['p']}² + {p['q']}² "
                     f"= {p['p'] ** 2} + {p['q'] ** 2} "
                     f"= {p['h'] ** 2}",
                     f"h = √{p['h'] ** 2} = {p['h']}"]
        else:
            given = p["given_leg"]
            other = p["q"] if given == p["p"] else p["p"]
            lines = [f"By Pythagoras' theorem: other leg² "
                     f"= {p['h']}² − {given}² "
                     f"= {p['h'] ** 2} − {given ** 2} "
                     f"= {other ** 2}",
                     f"Other leg = √{other ** 2} = {other}"]
    elif kind == "sector_area":
        lines = ["Area of a sector = (θ/360) × π × r²",
                 f"= {p['theta']}/360 × 22/7 × {p['r']}² "
                 f"= {_f(Fraction(p['theta'] * 22 * p['r'] * p['r'], 2520))}"]
    elif kind == "coordinate_distance":
        if p["variant"] == "axis":
            lines = ["Both points lie on the x-axis",
                     f"Distance = |{p['x2']} − ({p['x1']})| "
                     f"= {abs(p['x2'] - p['x1'])}"]
        else:
            lines = [f"Distance from the origin "
                     f"= √({p['x']}² + {p['y']}²) "
                     f"= √{p['x'] ** 2 + p['y'] ** 2}",
                     f"= {ans}"]
    elif kind == "coordinate_midpoint":
        mx = (p["x1"] + p["x2"]) // 2
        my = (p["y1"] + p["y2"]) // 2
        lines = [f"Midpoint = (({p['x1']} + {p['x2']})/2, "
                 f"({p['y1']} + {p['y2']})/2)",
                 f"= ({mx}, {my})"]
    elif kind == "cube_volume":
        lines = ["Volume of a cube = side³",
                 f"= {p['side']}³ = {p['side'] ** 3}"]
    elif kind == "cuboid_surface_area":
        l, b, h = p["length"], p["breadth"], p["height"]
        lines = ["Total surface area of a cuboid "
                 "= 2(lb + bh + hl)",
                 f"= 2 × ({l * b} + {b * h} + {h * l}) "
                 f"= {2 * (l * b + b * h + h * l)}"]
    elif kind == "cuboid_lsa":
        l, b, h = p["length"], p["breadth"], p["height"]
        lines = ["Lateral surface area of a cuboid "
                 "= 2h(l + b)",
                 f"= 2 × {h} × ({l} + {b}) "
                 f"= {2 * h * (l + b)}"]
    elif kind == "cylinder_csa":
        lines = ["Curved surface area of a cylinder "
                 "= 2πrh",
                 f"= 2 × 22/7 × {p['r']} × {p['h']} "
                 f"= {_f(Fraction(44 * p['r'] * p['h'], 7))}"]
    elif kind == "cylinder_tsa":
        lines = ["Total surface area of a cylinder "
                 "= 2πr(r + h)",
                 f"= 2 × 22/7 × {p['r']} × ({p['r']} "
                 f"+ {p['h']}) "
                 f"= {_f(Fraction(44 * p['r'] * (p['r'] + p['h']), 7))}"]
    elif kind == "sphere_volume":
        lines = ["Volume of a sphere = (4/3) × π × r³",
                 f"= 4/3 × 22/7 × {p['r']}³ "
                 f"= {_f(Fraction(88 * p['r'] ** 3, 21))}"]
    elif kind == "sphere_surface_area":
        lines = ["Surface area of a sphere = 4 × π × r²",
                 f"= 4 × 22/7 × {p['r']}² "
                 f"= {_f(Fraction(88 * p['r'] * p['r'], 7))}"]
    elif kind == "hemisphere_volume":
        lines = ["Volume of a hemisphere = (2/3) × π × r³",
                 f"= 2/3 × 22/7 × {p['r']}³ "
                 f"= {_f(Fraction(44 * p['r'] ** 3, 21))}"]
    elif kind == "hemisphere_tsa":
        lines = ["Total surface area of a hemisphere "
                 "= 3 × π × r²",
                 f"= 3 × 22/7 × {p['r']}² "
                 f"= {_f(Fraction(66 * p['r'] * p['r'], 7))}"]
    elif kind == "cone_csa":
        lines = [f"Slant height l = √({p['r']}² + "
                 f"{p['h']}²) = √{p['r'] ** 2 + p['h'] ** 2} "
                 f"= {p['l']}",
                 "Curved surface area of a cone = π × r × l",
                 f"= 22/7 × {p['r']} × {p['l']} "
                 f"= {_f(Fraction(22 * p['r'] * p['l'], 7))}"]
    elif kind == "fencing_cost":
        perim = 2 * (p["length"] + p["breadth"])
        lines = [f"Perimeter = 2 × ({p['length']} "
                 f"+ {p['breadth']}) = {perim} m",
                 f"Cost = {perim} × ₹{p['rate']} = {ans}"]
    elif kind == "tiling_cost":
        area = p["length"] * p["breadth"]
        lines = [f"Area of the floor = {p['length']} × "
                 f"{p['breadth']} = {area} m²",
                 f"Cost = {area} × ₹{p['rate']} = {ans}"]
    elif kind == "litres_capacity":
        vol = p["length"] * p["breadth"] * p["height"]
        lines = [f"Volume = {p['length']} × {p['breadth']} "
                 f"× {p['height']} = {vol} cm³",
                 f"Capacity = {vol} ÷ 1000 = {ans} litres"]
    elif kind == "bag_three_colours":
        total = p["red"] + p["blue"] + p["green"]
        count = p[p["ask"]]
        lines = [f"Total balls = {p['red']} + {p['blue']} "
                 f"+ {p['green']} = {total}",
                 f"P({p['ask']}) = {count}/{total} "
                 f"= {_f(Fraction(count, total))}"]
    elif kind == "die_event":
        if p["variant"] == "even":
            listing, count = "2, 4, 6", 3
        elif p["variant"] == "odd":
            listing, count = "1, 3, 5", 3
        elif p["variant"] == "prime":
            listing, count = "2, 3, 5", 3
        else:
            nums = [x for x in range(1, 7) if x % p["k"] == 0]
            listing = ", ".join(str(x) for x in nums)
            count = len(nums)
        lines = [f"Favourable outcomes: {listing} — "
                 f"{count} out of 6",
                 f"Probability = {count}/6 "
                 f"= {_f(Fraction(count, 6))}"]
    elif kind == "coins_exactly_heads":
        n, k = p["n"], p["k"]
        ways = math.comb(n, k)
        lines = [f"Total outcomes = 2^{n} = {2 ** n}",
                 f"Outcomes with exactly {k} head(s): {ways}",
                 f"Probability = {ways}/{2 ** n} "
                 f"= {_f(Fraction(ways, 2 ** n))}"]
    elif kind == "card_probability":
        lines = [f"Favourable cards = {p['favourable']} "
                 f"out of 52",
                 f"Probability = {p['favourable']}/52 "
                 f"= {_f(Fraction(p['favourable'], 52))}"]
    elif kind == "two_dice_sum":
        s = p["s"]
        pairs = [(i, s - i) for i in range(1, 7)
                 if 1 <= s - i <= 6]
        listing = ", ".join(f"({i}, {j})" for i, j in pairs)
        lines = [f"Outcomes with sum {s}: {listing} — "
                 f"{len(pairs)} out of 36",
                 f"Probability = {len(pairs)}/36 "
                 f"= {_f(Fraction(len(pairs), 36))}"]
    elif kind == "two_draw_probability":
        total = p["red"] + p["blue"]
        value = Fraction(p["red"], total) * Fraction(
            p["red"] - 1, total - 1)
        lines = [f"P(first ball red) = {p['red']}/{total}",
                 f"P(second ball red) = {p['red'] - 1}/"
                 f"{total - 1}",
                 f"P(both red) = {p['red']}/{total} × "
                 f"{p['red'] - 1}/{total - 1} = {_f(value)}"]
    elif kind == "complement_probability":
        lines = [f"P(not E) = 1 − P(E)",
                 f"= 1 − {p['a']}/{p['b']} "
                 f"= {_f(Fraction(p['b'] - p['a'], p['b']))}"]
    elif kind == "word_letter_probability":
        word = p["word"]
        if p["variant"] == "vowel":
            count = sum(1 for ch in word if ch in "AEIOU")
            lines = [f"{word} has {len(word)} letters, of "
                     f"which {count} are vowels",
                     f"Probability = {count}/{len(word)} "
                     f"= {_f(Fraction(count, len(word)))}"]
        else:
            count = word.count(p["letter"])
            lines = [f"The letter {p['letter']} appears "
                     f"{count} time(s) in {word}, which "
                     f"has {len(word)} letters",
                     f"Probability = {count}/{len(word)} "
                     f"= {_f(Fraction(count, len(word)))}"]
    lines.append(f"Answer: {ans}")
    return lines


__all__ = ["generate_test", "check_test_answer", "worked_steps",
           "parse_student_number", "TEST_QUESTION_COUNT",
           "TEST_SECONDS_PER_QUESTION", "TEST_TIME_LIMIT",
           "TOPIC_LABELS"]
