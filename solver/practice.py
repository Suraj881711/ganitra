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


# ------------------------------------------------------------------ quiz
# Timed-quiz generators per topic and difficulty. Every generator returns
# (question_text, numeric_answer) so submissions can be checked
# server-side with a small tolerance for decimals.
def _q_arith_easy(rng):
    return _arith(rng)


def _q_arith_medium(rng):
    q, a = _bodmas(rng)
    return q, a


def _q_arith_hard(rng):
    q, a = _percent(rng)
    return q, a


def _q_algebra_easy(rng):
    xv = rng.randint(2, 12)
    b = rng.randint(1, 15)
    return f"Solve x + {b} = {xv + b}", f"x = {xv}"


def _q_algebra_medium(rng):
    return _linear(rng)


def _q_algebra_hard(rng):
    return _quadratic(rng)


_TRIG_VALUES = {
    ("sin", 0): 0.0, ("sin", 30): 0.5, ("sin", 45): 0.7071,
    ("sin", 60): 0.866, ("sin", 90): 1.0,
    ("cos", 0): 1.0, ("cos", 30): 0.866, ("cos", 45): 0.7071,
    ("cos", 60): 0.5, ("cos", 90): 0.0,
    ("tan", 0): 0.0, ("tan", 30): 0.5774, ("tan", 45): 1.0,
    ("tan", 60): 1.732,
}


def _q_trig_easy(rng):
    fn = rng.choice(["sin", "cos"])
    ang = rng.choice([0, 30, 60, 90])
    return (f"What is {fn} {ang}°? (decimal answer is fine)",
            _TRIG_VALUES[(fn, ang)])


def _q_trig_medium(rng):
    fn = rng.choice(["sin", "cos", "tan"])
    ang = rng.choice([30, 45, 60])
    return (f"What is {fn} {ang}°? (decimal answer is fine)",
            _TRIG_VALUES[(fn, ang)])


def _q_trig_hard(rng):
    a = rng.randint(2, 9)
    ang = rng.choice([30, 60])
    fn = rng.choice(["sin", "cos"])
    return (f"What is {a} × {fn} {ang}°? (decimal answer is fine)",
            a * _TRIG_VALUES[(fn, ang)])


def _q_stats_easy(rng):
    nums = [rng.randint(1, 20) for _ in range(3)]
    return (f"Find the mean of {', '.join(map(str, nums))}",
            sum(nums) / len(nums))


def _q_stats_medium(rng):
    nums = sorted(rng.randint(1, 30) for _ in range(5))
    return (f"Find the median of {', '.join(map(str, nums))}", nums[2])


def _q_stats_hard(rng):
    k = rng.choice([4, 5, 6])
    return (f"What is the probability of getting a {k} on one roll of "
            "a fair die? (decimal, e.g. 0.1667)", 1 / 6)


_QUIZ_GENERATORS = {
    "arithmetic": {"easy": _q_arith_easy, "medium": _q_arith_medium,
                   "hard": _q_arith_hard},
    "algebra": {"easy": _q_algebra_easy, "medium": _q_algebra_medium,
                "hard": _q_algebra_hard},
    "trig": {"easy": _q_trig_easy, "medium": _q_trig_medium,
             "hard": _q_trig_hard},
    "stats": {"easy": _q_stats_easy, "medium": _q_stats_medium,
              "hard": _q_stats_hard},
}

QUIZ_TOPICS = tuple(_QUIZ_GENERATORS)
QUIZ_DIFFICULTIES = ("easy", "medium", "hard")
QUIZ_QUESTION_COUNT = 5
QUIZ_SECONDS_PER_QUESTION = 30


def generate_quiz(topic: str, difficulty: str, seed=None):
    """5 questions for the chosen topic/difficulty. Answers are numeric
    (or 'x = n' strings for algebra) so they can be checked server-side.
    """
    gen = _QUIZ_GENERATORS[topic][difficulty]
    rng = random.Random(seed)
    out = []
    for _ in range(QUIZ_QUESTION_COUNT):
        q, a = gen(rng)
        out.append({"question": q, "answer": a})
    return out


def _parse_user_number(text):
    """Best-effort numeric parse of a submitted answer: accepts '42',
    'x = 42', '1/2', '0.5', '√3/2' (approx), '50%'."""
    if text is None:
        return None
    t = str(text).strip().lower().replace("√", "sqrt")
    if "=" in t:
        t = t.split("=")[-1].strip()
    t = t.rstrip("%").strip()
    try:
        return float(t)
    except ValueError:
        pass
    try:
        from fractions import Fraction
        return float(Fraction(t))
    except Exception:
        pass
    try:
        import sympy as sp
        return float(sp.nsimplify(t, [sp.sqrt(2), sp.sqrt(3)]))
    except Exception:
        return None


def check_quiz_answer(expected, given, tol=0.02):
    exp = _parse_user_number(expected)
    got = _parse_user_number(given)
    if exp is None or got is None:
        return str(expected).strip().lower() == str(given).strip().lower()
    return abs(exp - got) <= tol * max(1.0, abs(exp))


__all__ = ["generate_practice", "generate_quiz", "check_quiz_answer",
           "QUIZ_TOPICS", "QUIZ_DIFFICULTIES", "QUIZ_QUESTION_COUNT",
           "QUIZ_SECONDS_PER_QUESTION"]
