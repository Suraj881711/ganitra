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
        (the two string-answer kinds: expand_binomials,
        quadratic_roots — those are checked from params instead).
    check_test_answer(item, given) -> bool
    worked_steps(item) -> [str, ...]
        Plain working lines in the house style (no step numbers),
        ending with "Answer: ..." — derived from the item's own
        params, so the working always matches the question asked.
"""
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
    lines.append(f"Answer: {ans}")
    return lines


__all__ = ["generate_test", "check_test_answer", "worked_steps",
           "parse_student_number", "TEST_QUESTION_COUNT",
           "TEST_SECONDS_PER_QUESTION", "TEST_TIME_LIMIT",
           "TOPIC_LABELS"]
