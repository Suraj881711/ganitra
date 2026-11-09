"""Chapter-test / chapter-practice question generators (Wave 5).

solver/practice.py already has timed-quiz generators for arithmetic,
algebra, trig and stats. Board Mode also needs sequences, probability,
calculus, linear_algebra and geometry, so those generators live here
in the same style: every generator returns (question_text, answer)
where the answer is numeric (or an "x = n" style string) so the
existing check_quiz_answer() can score it server-side.

generate_chapter_questions() is the single entry point the board
routes use: it delegates to generate_quiz(topic, "medium") for the
original four topics and to the local generators for the new ones.
"""
import random

from solver.expression_parser import fmt_num
from solver.practice import QUIZ_QUESTION_COUNT, generate_quiz

CLASSIC_QUESTION_COUNT = 7


# ------------------------------------------------------------------ new
def _q_sequences(rng):
    kind = rng.choice(["ap_term", "ap_sum", "gp_term"])
    if kind == "ap_term":
        a, d = rng.randint(1, 15), rng.randint(2, 9)
        n = rng.randint(5, 15)
        return (f"Find the {n}th term of the AP {a}, {a + d}, "
                f"{a + 2 * d}, ...", a + (n - 1) * d)
    if kind == "ap_sum":
        a, d = rng.randint(1, 10), rng.randint(1, 6)
        n = rng.choice([10, 12, 15, 20])
        return (f"Find the sum of the first {n} terms of the AP "
                f"{a}, {a + d}, {a + 2 * d}, ...",
                n * (2 * a + (n - 1) * d) // 2)
    a = rng.choice([2, 3, 5])
    r = rng.choice([2, 3])
    n = rng.randint(4, 6)
    return (f"Find the {n}th term of the GP {a}, {a * r}, "
            f"{a * r * r}, ...", a * r ** (n - 1))


def _q_probability(rng):
    kind = rng.choice(["die", "coin", "two_dice", "card", "bag"])
    if kind == "die":
        k = rng.randint(1, 6)
        return (f"What is the probability of getting a {k} on one "
                "roll of a fair die? (decimal, e.g. 0.1667)", 1 / 6)
    if kind == "coin":
        return (f"What is the probability of getting heads on one "
                "toss of a fair coin? (decimal)", 0.5)
    if kind == "two_dice":
        total = rng.choice([2, 7, 12])
        ways = {2: 1, 7: 6, 12: 1}[total]
        return (f"Two dice are thrown. What is the probability that "
                f"the sum is {total}? (decimal)", ways / 36)
    if kind == "card":
        return ("A card is drawn from a pack of 52. What is the "
                "probability that it is a king? (decimal)", 4 / 52)
    red, total = rng.choice([(3, 8), (4, 10), (5, 12)])
    return (f"A bag has {total} balls, {red} of them red. One ball is "
            "drawn at random. What is the probability that it is "
            "red? (decimal)", red / total)


def _q_calculus(rng):
    kind = rng.choice(["deriv_power", "deriv_at_point", "integral"])
    if kind == "deriv_power":
        n = rng.randint(2, 5)
        return (f"What is the derivative of x^{n} at x = 1?", n)
    if kind == "deriv_at_point":
        n = rng.choice([2, 3])
        a = rng.randint(2, 3)
        return (f"What is the derivative of x^{n} at x = {a}?",
                n * a ** (n - 1))
    a = rng.randint(1, 3)
    power = rng.choice([1, 2])
    # integral of x^p from 0 to a = a^(p+1)/(p+1)
    return (f"Evaluate the integral of x^{power} from 0 to {a}",
            a ** (power + 1) / (power + 1))


def _q_linear_algebra(rng):
    kind = rng.choice(["det", "trace", "mat_add"])
    if kind == "det":
        a, b = rng.randint(1, 6), rng.randint(0, 5)
        c, d = rng.randint(0, 5), rng.randint(1, 6)
        return (f"Find the determinant of the matrix "
                f"[[{a}, {b}], [{c}, {d}]]", a * d - b * c)
    if kind == "trace":
        a, d = rng.randint(1, 12), rng.randint(1, 12)
        b, c = rng.randint(0, 9), rng.randint(0, 9)
        return (f"Find the trace of the matrix "
                f"[[{a}, {b}], [{c}, {d}]]", a + d)
    a, b = rng.randint(1, 9), rng.randint(1, 9)
    c, d = rng.randint(1, 9), rng.randint(1, 9)
    return (f"If A = [[{a}, {b}]] and B = [[{c}, {d}]], what is the "
            "first entry of A + B?", a + c)


def _q_geometry(rng):
    kind = rng.choice(["circle_area", "triangle_area", "cube_volume",
                       "circumference", "rectangle_area"])
    if kind == "circle_area":
        r = rng.choice([7, 14])
        return (f"Find the area of a circle of radius {r} cm "
                "(use pi = 22/7)", 22 / 7 * r * r)
    if kind == "triangle_area":
        base, height = rng.randint(4, 20), rng.randint(3, 16)
        return (f"Find the area of a triangle with base {base} cm "
                f"and height {height} cm", base * height / 2)
    if kind == "cube_volume":
        side = rng.randint(3, 10)
        return (f"Find the volume of a cube of side {side} cm",
                side ** 3)
    if kind == "circumference":
        r = rng.choice([7, 14, 21])
        return (f"Find the circumference of a circle of radius "
                f"{r} cm (use pi = 22/7)", 2 * 22 / 7 * r)
    length, width = rng.randint(5, 20), rng.randint(3, 12)
    return (f"Find the area of a rectangle of length {length} cm "
            f"and width {width} cm", length * width)


_NEW_GENERATORS = {
    "sequences": _q_sequences,
    "probability": _q_probability,
    "calculus": _q_calculus,
    "linear_algebra": _q_linear_algebra,
    "geometry": _q_geometry,
}

NEW_TOPICS = tuple(_NEW_GENERATORS)


def generate_chapter_questions(topic, count=QUIZ_QUESTION_COUNT,
                               seed=None):
    """`count` questions for a board-chapter topic.

    Returns [{"question": str, "answer": raw}] where raw answers stay
    in checker form (numeric or "x = n") for server-side scoring.
    For the classic practice view, use display_answer() to format.
    """
    if topic in _NEW_GENERATORS:
        gen = _NEW_GENERATORS[topic]
        rng = random.Random(seed)
        return [{"question": q, "answer": a}
                for q, a in (gen(rng) for _ in range(count))]
    # Original quiz topics: reuse the existing timed-quiz engine.
    if count == QUIZ_QUESTION_COUNT:
        return generate_quiz(topic, "medium", seed=seed)
    rng = random.Random(seed)
    base = generate_quiz(topic, "medium", seed=seed)
    out = list(base)
    extra_seed = rng.randint(0, 10 ** 9)
    while len(out) < count:
        out.extend(generate_quiz(topic, "medium", seed=extra_seed))
        extra_seed += 1
    return out[:count]


def display_answer(answer):
    """Human-friendly answer string for reveal-style practice."""
    if isinstance(answer, (int, float)):
        return fmt_num(answer)
    return str(answer)


__all__ = ["generate_chapter_questions", "display_answer", "NEW_TOPICS",
           "CLASSIC_QUESTION_COUNT"]
