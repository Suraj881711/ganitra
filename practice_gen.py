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
# Template pools per topic, gated by the class they suit.
# (min_class, builder)
# ---------------------------------------------------------------------------

_POOLS = {
    "arithmetic": [
        (6, _arith_expression),
        (6, _arith_fraction_add),
        (6, _arith_percent),
        (8, _arith_simple_interest),
    ],
    "algebra": [
        (6, _algebra_evaluate),
        (7, _algebra_linear),
        (8, _algebra_expand),
        (9, _algebra_ap_nth),
        (10, _algebra_quadratic_roots),
    ],
    "geometry": [
        (6, _geo_supplementary),
        (6, _geo_rectangle_area),
        (7, _geo_triangle_third_angle),
        (7, _geo_circle_circumference),
    ],
    "mensuration": [
        (6, _mens_cuboid_volume),
        (6, _mens_cube_surface_area),
        (8, _mens_cylinder_volume),
        (9, _mens_cone_volume),
    ],
    "probability": [
        (6, _prob_bag),
        (6, _prob_die_greater),
        (7, _prob_coins_at_least_one_head),
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
