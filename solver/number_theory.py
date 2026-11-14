"""Number theory: primes, prime factorisation, GCD/HCF, LCM, modulo."""
import re

from sympy import factorint, isprime

from .expression_parser import fmt_num, parse_expression


def _factor_str(n: int) -> str:
    f = factorint(n)
    return " × ".join(f"{p}^{e}" if e > 1 else f"{p}" for p, e in f.items())


def _first_int(text: str, default=None):
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else default


def _all_ints(text: str):
    return [int(v) for v in re.findall(r"\d+", text)]


def solve_number_theory(question: str):
    q = question.lower()

    # Modulo: "17 mod 5", "17 modulo 5", "remainder when 17 is divided by 5"
    m = re.search(r"(\d+)\s*(?:mod|modulo)\s*(\d+)", q) or re.search(
        r"remainder\s+when\s+(\d+)\s+is\s+divided\s+by\s+(\d+)", q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        steps = [
            f"Divide {a} by {b}: {a} = {a // b} × {b} + {a % b}",
            f"Remainder = {a % b}",
        ]
        return {"type": "number_theory", "op": "modulo",
                "answer": str(a % b), "value": a % b, "steps": steps}

    # Wave 30: HCF and LCM asked TOGETHER ("Find the HCF and
    # LCM of 12 and 18") — the HCF branch below used to fire
    # alone and the LCM was silently never given.
    _wants_gcd = "gcd" in q or "hcf" in q or "greatest common" in q
    _wants_lcm = "lcm" in q or "least common multiple" in q
    if _wants_gcd and _wants_lcm:
        nums = _all_ints(question)
        if len(nums) >= 2:
            import math
            g, l = nums[0], nums[0]
            for v in nums[1:]:
                g = math.gcd(g, v)
                l = l * v // math.gcd(l, v)
            steps = [f"Prime factorisation: {nums[0]} = "
                     f"{_factor_str(nums[0])}",
                     f"Prime factorisation: {nums[1]} = "
                     f"{_factor_str(nums[1])}",
                     "HCF = product of the lowest powers of the "
                     "common prime factors; LCM = product of the "
                     "highest powers of all prime factors.",
                     f"HCF = {g} and LCM = {l}"]
            return {"type": "number_theory", "op": "hcf_lcm",
                    "answer": f"HCF = {g}, LCM = {l}",
                    "value": [g, l], "steps": steps}

    # GCD / HCF
    if "gcd" in q or "hcf" in q or "greatest common" in q:
        nums = _all_ints(question)
        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            import math
            g = math.gcd(a, b)
            for v in nums[2:]:
                g = math.gcd(g, v)
            steps = [f"Prime factorisation: {a} = {_factor_str(a)}",
                     f"Prime factorisation: {b} = {_factor_str(b)}",
                     "Take the lowest power of each common prime factor.",
                     f"GCD = {g}"]
            return {"type": "number_theory", "op": "gcd",
                    "answer": str(g), "value": g, "steps": steps}

    # LCM
    if "lcm" in q or "least common multiple" in q:
        nums = _all_ints(question)
        if len(nums) >= 2:
            import math
            l = nums[0]
            for v in nums[1:]:
                l = l * v // math.gcd(l, v)
            a, b = nums[0], nums[1]
            steps = [f"Prime factorisation: {a} = {_factor_str(a)}",
                     f"Prime factorisation: {b} = {_factor_str(b)}",
                     "Take the highest power of every prime factor.",
                     f"LCM = {l}"]
            return {"type": "number_theory", "op": "lcm",
                    "answer": str(l), "value": l, "steps": steps}

    # Prime check
    if "prime" in q:
        n = _first_int(question)
        if n is None:
            raise ValueError("Give a number to test for primality.")
        prime = bool(isprime(n))
        steps = [f"Check divisibility of {n} by primes up to "
                 f"sqrt({n}) ≈ {int(n ** 0.5)}."]
        if prime:
            steps.append(f"No divisor found — {n} is prime.")
        else:
            f = factorint(n)
            smallest = min(f)
            steps.append(
                f"{n} = {smallest} × {n // smallest}, so {n} is "
                "composite (not prime).")
        return {"type": "number_theory", "op": "isprime",
                "answer": f"{n} is {'prime' if prime else 'not prime'}",
                "value": prime, "steps": steps}

    # Factorisation of an integer
    if "factor" in q:
        n = _first_int(question)
        if n is not None:
            f = factorint(n)
            steps = [
                f"Break {n} into prime factors: {_factor_str(n)}",
            ]
            return {"type": "number_theory", "op": "factorint",
                    "answer": _factor_str(n),
                    "value": {str(k): v for k, v in f.items()},
                    "steps": steps}

    # Divisibility: "is 144 divisible by 12"
    m = re.search(r"is\s+(\d+)\s+divisible\s+by\s+(\d+)", q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        ok = a % b == 0
        return {"type": "number_theory", "op": "divisibility",
                "answer": f"{a} is {'divisible' if ok else 'not divisible'} "
                          f"by {b} (remainder {a % b})",
                "value": ok,
                "steps": [f"{a} ÷ {b} = {a // b} remainder {a % b}"]}

    # Fallback: evaluate the numeric expression.
    expr = parse_expression(question)
    return {"type": "number_theory", "op": "evaluate",
            "answer": fmt_num(expr), "value": fmt_num(expr),
            "steps": [f"Evaluate: {fmt_num(expr)}"]}
