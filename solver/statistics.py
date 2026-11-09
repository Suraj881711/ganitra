"""Statistics & probability.

Descriptive stats (mean, median, mode, variance, standard deviation,
range), permutations, combinations, factorials, and basic probability
(dice, coins, balls in a bag, a pack of cards, binomial trials).
"""
import re
from fractions import Fraction
from itertools import product as _iproduct

import sympy as sp

from .expression_parser import fmt_num

# ------------------------------------------------------------ descriptive
def _extract_list(question: str):
    m = re.search(r"\[([^\]]+)\]", question)
    text = m.group(1) if m else question
    nums = []
    for tok in re.finditer(r"-?\d+(?:\.\d+)?", text):
        s = tok.group(0)
        nums.append(float(s) if "." in s else int(s))
    return nums


def _mean(nums):
    return sum(nums) / len(nums)


def _median(nums):
    s = sorted(nums)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _mode(nums):
    counts = {}
    for v in nums:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    return sorted(v for v, c in counts.items() if c == top)


def _variance(nums, sample=False):
    mu = _mean(nums)
    n = len(nums) - (1 if sample else 0)
    return sum((v - mu) ** 2 for v in nums) / n


def _stats_result(op, nums):
    if len(nums) < 2:
        return None
    listed = ", ".join(fmt_num(v) for v in nums)
    if op == "mean":
        steps = [
            f"Add all values: {' + '.join(fmt_num(v) for v in nums)} "
            f"= {fmt_num(sum(nums))}",
            f"Divide by the count ({len(nums)}): {fmt_num(sum(nums))} ÷ "
            f"{len(nums)} = {fmt_num(_mean(nums))}",
        ]
        return _mean(nums), steps
    if op == "median":
        s = sorted(nums)
        steps = [
            f"Arrange in order: {', '.join(fmt_num(v) for v in s)}",
            "Take the middle value"
            + (" (average of the two middle values)." if len(s) % 2 == 0
               else "."),
            f"Median = {fmt_num(_median(nums))}",
        ]
        return _median(nums), steps
    if op == "mode":
        modes = _mode(nums)
        steps = [
            f"Count how often each value appears in: {listed}",
            "The most frequent value(s): "
            + ", ".join(fmt_num(v) for v in modes),
        ]
        return (modes[0] if len(modes) == 1 else modes), steps
    if op in ("variance", "std"):
        mu = _mean(nums)
        var = _variance(nums)
        steps = [
            f"Mean x̄ = {fmt_num(mu)}",
            "Squared deviations (x - x̄)^2: "
            + ", ".join(fmt_num((v - mu) ** 2) for v in nums),
            f"Variance = average of squared deviations = {fmt_num(var)}",
        ]
        if op == "std":
            steps.append(f"Standard deviation = sqrt({fmt_num(var)}) "
                         f"= {fmt_num(var ** 0.5)}")
            return var ** 0.5, steps
        return var, steps
    if op == "range":
        steps = [
            f"Largest value = {fmt_num(max(nums))}, smallest = "
            f"{fmt_num(min(nums))}",
            f"Range = {fmt_num(max(nums))} - {fmt_num(min(nums))} "
            f"= {fmt_num(max(nums) - min(nums))}",
        ]
        return max(nums) - min(nums), steps
    return None


# ------------------------------------------------------------ probability
def _prob_answer(frac: Fraction, steps, label="Probability"):
    dec = frac.numerator / frac.denominator
    steps.append(f"{label} = {frac} ≈ {dec:.4f} ({dec * 100:.2f}%)")
    return {
        "type": "statistics",
        "op": "probability",
        "answer": f"{frac} ≈ {dec:.4f}",
        "value": float(dec),
        "steps": steps,
    }


def _probability(q: str):
    ql = q.lower()

    # Binomial: exactly k successes in n trials with p
    m = re.search(
        r"exactly\s+(\d+)\s+success\w*\s+in\s+(\d+)\s+trials.*?p\s*=\s*"
        r"(\d+(?:\.\d+)?)",
        ql,
    ) or re.search(r"binomial.*?n\s*=\s*(\d+).*?k\s*=\s*(\d+).*?p\s*=\s*"
                   r"(\d+(?:\.\d+)?)", ql)
    if m:
        if "binomial" in ql:
            n, k, p = int(m.group(1)), int(m.group(2)), float(m.group(3))
        else:
            k, n, p = int(m.group(1)), int(m.group(2)), float(m.group(3))
        from math import comb
        prob = comb(n, k) * p**k * (1 - p) ** (n - k)
        steps = [
            "Binomial formula: P(X = k) = C(n, k) · p^k · (1-p)^(n-k)",
            f"C({n}, {k}) = {comb(n, k)}",
            f"P = {comb(n, k)} · {p}^{k} · {1 - p}^{n - k} = {prob:.4f}",
        ]
        return _prob_answer(Fraction(prob).limit_denominator(10**9), steps)

    # Coins: exactly k heads in n tosses (or "2 heads in 3 tosses")
    m = re.search(r"(?:exactly\s+)?(\d+)\s+heads?\s+in\s+(\d+)\s+"
                  r"(?:coin\s+)?tosses", ql)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        from math import comb
        fav = comb(n, k)
        steps = [
            f"Total outcomes for {n} coin tosses = 2^{n} = {2**n}",
            f"Favourable outcomes (exactly {k} heads) = C({n}, {k}) "
            f"= {fav}",
        ]
        return _prob_answer(Fraction(fav, 2**n), steps)
    if "coin" in ql and "head" in ql:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "heads is 1 of them."])
    if "coin" in ql and "tail" in ql:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "tails is 1 of them."])

    # Two dice: sum
    m = re.search(r"sum\s+(?:of\s+)?(\d+)\s+(?:with|on|of)?\s*two\s+dice",
                  ql) or re.search(r"two\s+dice.*?sum\s+(?:of\s+)?(\d+)", ql)
    if m:
        target = int(m.group(1))
        fav = sum(1 for a, b in _iproduct(range(1, 7), repeat=2)
                  if a + b == target)
        steps = [
            "Two dice give 6 × 6 = 36 equally likely outcomes.",
            f"Outcomes with sum {target}: {fav}",
        ]
        return _prob_answer(Fraction(fav, 36), steps)

    # Single die
    m = re.search(r"(?:getting|rolling|of)\s+(?:a\s+)?(\d)\s+on\s+a\s+"
                  r"(?:die|dice)", ql) or re.search(
                      r"die|dice", ql) and re.search(r"\b(\d)\b", ql)
    if m and ("die" in ql or "dice" in ql) and "two" not in ql:
        steps = ["A fair die has 6 equally likely faces (1-6); the "
                 "wanted face is 1 of them."]
        return _prob_answer(Fraction(1, 6), steps)

    # Balls in a bag: "5 red and 3 blue balls ... red ball"
    if "ball" in ql:
        counts = {}
        for num, colour in re.findall(
            r"(\d+)\s+(red|blue|green|yellow|black|white|orange|pink|"
            r"purple|brown)\s*(?:balls?)?", ql
        ):
            counts[colour] = counts.get(colour, 0) + int(num)
        m = re.search(r"(red|blue|green|yellow|black|white|orange|pink|"
                      r"purple|brown)\s+ball", ql.split("probab")[-1])
        if counts and m:
            colour = m.group(1)
            total = sum(counts.values())
            steps = [
                "Count the balls: "
                + ", ".join(f"{c} {col}" for col, c in counts.items())
                + f" — total {total}",
                f"Favourable (red... wanted {colour}) = "
                f"{counts.get(colour, 0)}",
            ]
            return _prob_answer(
                Fraction(counts.get(colour, 0), total), steps)

    # Pack of cards
    if "card" in ql and ("deck" in ql or "pack" in ql or "52" in ql):
        fav, label = None, None
        table = [
            (r"\bace\b", 4, "aces"),
            (r"\bking\b", 4, "kings"),
            (r"\bqueen\b", 4, "queens"),
            (r"\bjack\b", 4, "jacks"),
            (r"face\s+card", 12, "face cards"),
            (r"\bred\b", 26, "red cards"),
            (r"\bblack\b", 26, "black cards"),
            (r"\bheart", 13, "hearts"),
            (r"\bdiamond", 13, "diamonds"),
            (r"\bspade", 13, "spades"),
            (r"\bclub", 13, "clubs"),
        ]
        for pat, n, lab in table:
            if re.search(pat, ql):
                fav, label = n, lab
                break
        if fav is not None:
            steps = [
                "A standard pack has 52 cards.",
                f"Number of {label} = {fav}",
            ]
            return _prob_answer(Fraction(fav, 52), steps)
    return None


# ------------------------------------------------------------ counting
def _counting(q: str):
    ql = q.lower()
    m = re.search(r"\bP\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", q) or re.search(
        r"(\d+)\s*P\s*(\d+)", q)
    if m or "permutation" in ql:
        if not m:
            nums = [int(v) for v in re.findall(r"\d+", q)]
            if len(nums) < 2:
                return None
            n, r = nums[0], nums[1]
        else:
            n, r = int(m.group(1)), int(m.group(2))
        val = sp.perm(n, r) if hasattr(sp, "perm") else None
        from math import factorial as _f
        val = _f(n) // _f(n - r)
        steps = [
            "Permutations (order matters): P(n, r) = n! / (n - r)!",
            f"P({n}, {r}) = {n}! / {n - r}! = {val}",
        ]
        return {"type": "statistics", "op": "permutation",
                "answer": fmt_num(val), "value": int(val), "steps": steps}
    m = re.search(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", q) or re.search(
        r"(\d+)\s*C\s*(\d+)", q)
    if m or "combination" in ql or "choose" in ql:
        if not m:
            mm = re.search(r"choose\s+(\d+)\s+from\s+(\d+)", ql) or \
                re.search(r"(\d+)\s+(?:taken|from)\s+(\d+)", ql)
            if mm:
                if "choose" in ql and mm.re.pattern.startswith("choose"):
                    r, n = int(mm.group(1)), int(mm.group(2))
                else:
                    n, r = int(mm.group(1)), int(mm.group(2))
            else:
                nums = [int(v) for v in re.findall(r"\d+", q)]
                if len(nums) < 2:
                    return None
                n, r = nums[0], nums[1]
        else:
            n, r = int(m.group(1)), int(m.group(2))
        from math import comb
        val = comb(n, r)
        steps = [
            "Combinations (order does not matter): "
            "C(n, r) = n! / (r! · (n - r)!)",
            f"C({n}, {r}) = {n}! / ({r}! · {n - r}!) = {val}",
        ]
        return {"type": "statistics", "op": "combination",
                "answer": fmt_num(val), "value": int(val), "steps": steps}
    m = re.search(r"factorial\s*(?:of\s*)?(\d+)", ql) or re.search(
        r"^\s*(\d+)\s*!\s*$", q)
    if m:
        from math import factorial as _f
        n = int(m.group(1))
        steps = [
            f"{n}! = {' × '.join(str(i) for i in range(n, 0, -1))}"
            if n <= 10 else f"{n}! = {n} × {n-1} × ... × 1",
            f"= {_f(n)}",
        ]
        return {"type": "statistics", "op": "factorial",
                "answer": fmt_num(_f(n)), "value": _f(n), "steps": steps}
    return None


def solve_statistics(question: str):
    q = question.strip()
    ql = q.lower()

    if "probab" in ql:
        out = _probability(q)
        if out:
            return out

    counted = _counting(q)
    if counted:
        return counted

    op = None
    if "standard deviation" in ql or re.search(r"\bstd\b", ql):
        op = "std"
    elif "variance" in ql:
        op = "variance"
    elif "median" in ql:
        op = "median"
    elif "mode" in ql:
        op = "mode"
    elif "range" in ql:
        op = "range"
    elif "mean" in ql or "average" in ql:
        op = "mean"
    if op:
        nums = _extract_list(q)
        # For std/variance questions the numbers are the data itself.
        out = _stats_result(op, nums)
        if out:
            val, steps = out
            ans = val if not isinstance(val, list) else \
                ", ".join(fmt_num(v) for v in val)
            return {
                "type": "statistics",
                "op": op,
                "answer": fmt_num(ans) if not isinstance(ans, str) else ans,
                "value": float(val) if not isinstance(val, list) else None,
                "steps": steps,
            }
    return {
        "type": "statistics",
        "op": "unknown",
        "answer": "Tell me the data, e.g. 'mean of 2, 4, 6' or "
                  "'probability of getting a 6 on a dice'.",
        "steps": [],
    }
