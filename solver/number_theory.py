"""Number theory: primes, prime factorisation, GCD/HCF, LCM, modulo."""
import re
from math import isqrt

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


# Deploy-70c: the operands of an HCF/LCM ask live in the
# ask's own phrase — the numbers listed right after
# "HCF of", or in the clause that carries the keyword
# ("12 aur 18 ka HCF"). The branches below used to read
# the first integers of the WHOLE text, so any dressing
# ahead of the ask silently became the operands: a pasted
# set's preamble bound into a part-solve ("Please solve
# all of these questions for me 1 by 1: What is the HCF
# of 12 and 18?" — the "1 by 1" is the route normaliser's
# rewrite of the idiom "one by one") gave GCD(1, 1) = 1
# with empty factorisations on the Deploy-70b live paste,
# and a literal "Set 2:" / "Chapter 5:" dressing gives
# GCD(2, 12) / LCM(5, 12, 18) the same way.
_HCF_KW = (r"(?:hcf|gcd|greatest\s+common\s+"
           r"(?:divisor|factor|measure)|महत्तम\s*समापवर्तक)")
_LCM_KW = (r"(?:lcm|least\s+common\s+multiple|"
           r"लघुत्तम\s*समापवर्त्य)")
_OPERAND_RUN_RE = re.compile(
    r"\s*(?:the\s+)?(\d+(?:\s*(?:,|&|\band\b|\baur\b|और)"
    r"\s*\d+)+)")


def _pair_operands(question, q, kind):
    """The integers an HCF/LCM ask is about, anchored to
    the ask itself — never merely the first integers of
    the text:

    1. the operand run listed right after "<keyword> of"
       ("HCF of 12 and 18", "Find the HCF and LCM of 24
       and 36");
    2. else the integers of the one clause carrying the
       keyword, when exactly one such clause has any
       ("12 aur 18 ka HCF batao"; a preamble clause split
       off by ':' or '?' cannot donate its numbers);
    3. else the historical whole-text read, so every
       shape the anchors do not recognise behaves exactly
       as before ("The numbers are 12 and 18. Find their
       HCF." — the operands sit in a keyword-less clause).
    """
    if kind == "gcd":
        kw = _HCF_KW
    elif kind == "lcm":
        kw = _LCM_KW
    else:
        kw = "(?:" + _HCF_KW + "|" + _LCM_KW + ")"
    m = re.search(kw + r"(?:\s*(?:and|&|,)\s*" + kw + r")?"
                  r"\s+of\s+", q)
    if m:
        run = _OPERAND_RUN_RE.match(q, m.end())
        if run:
            return [int(v) for v in
                    re.findall(r"\d+", run.group(1))]
    found = []
    for clause in re.split(r"[.?;:।\n]+", q):
        if re.search(kw, clause):
            ints = [int(v) for v in re.findall(r"\d+", clause)]
            if len(ints) >= 2:
                found.append(ints)
    if len(found) == 1:
        return found[0]
    return _all_ints(question)


def _icbrt140(a: int) -> int:
    """Exact integer cube root (floor) of a non-negative int."""
    if a <= 0:
        return 0
    r = round(a ** (1 / 3))
    while r * r * r > a:
        r -= 1
    while (r + 1) ** 3 <= a:
        r += 1
    return r


def _perfect_power_check140(question, q):
    """Wave 140: "1024 perfect square hai ya nahi?" — a
    haan-nahi ask no solver owned, so it fell to the plain
    parser (error) and then to the slow AI fallback (~30 s
    on the live check). Deterministic yes/no with the root
    shown; non-powers get the two neighbouring powers in one
    line. Fires ONLY on a yes/no-shaped ask, so word problems
    that merely mention a perfect square ("smallest number
    to multiply ... to make a perfect square") never land
    here. Wording follows the question's language: English,
    Hinglish (Roman) or Hindi (Devanagari)."""
    if re.search(r"perfect\s+square|purna\s+varg|पूर्ण\s*वर्ग",
                 q):
        kind = 2
    elif re.search(r"perfect\s+cube|purna\s+ghan|पूर्ण\s*घन",
                   q):
        kind = 3
    else:
        return None
    yn = (re.search(r"hai\s+ya\s+nahi|ya\s+nahi|or\s+not\b", q)
          or re.search(r"\bkya\b|क्या", q)
          or re.search(r"\bis\s+-?\d+\s+an?\s+perfect", q)
          or re.search(r"(?:hai|है)\s*\??\s*$", q)
          or ("?" in q and re.search(r"\bis\b[^?]*\bperfect\b",
                                     q)))
    if not yn:
        return None
    mnum = re.search(r"-?\d+", question)
    if not mnum:
        return None
    n = int(mnum.group(0))
    hindi = bool(re.search(r"[ऀ-ॿ]", question))
    hinglish = (not hindi) and bool(re.search(
        r"\b(hai|nahi|kya|purna|varg|ghan)\b", q))
    op = "perfect_square_check" if kind == 2 \
        else "perfect_cube_check"
    sup = "²" if kind == 2 else "³"
    if kind == 2:
        # lo = floor root of |n|; a negative is never a square.
        lo = isqrt(abs(n))
        yes = n >= 0 and lo * lo == n
        r = lo
    else:
        lo = _icbrt140(abs(n))
        yes = lo ** 3 == abs(n)
        r = -lo if n < 0 else lo
    if yes:
        fac = " × ".join([str(r)] * kind)
        if hindi:
            naam = "पूर्ण वर्ग" if kind == 2 else "पूर्ण घन"
            return {"type": "number_theory", "op": op,
                    "answer": f"हाँ — {n} = {r}{sup}",
                    "steps": [f"{fac} = {n}",
                              f"इसलिए {n} एक {naam} है।"]}
        if hinglish:
            return {"type": "number_theory", "op": op,
                    "answer": f"Haan — {n} = {r}{sup}",
                    "steps": [f"{fac} = {n}",
                              f"Isliye {n} ek perfect "
                              f"{'square' if kind == 2 else 'cube'} "
                              f"hai."]}
        return {"type": "number_theory", "op": op,
                "answer": f"Yes — {n} = {r}{sup}",
                "steps": [f"{fac} = {n}",
                          f"So {n} is a perfect "
                          f"{'square' if kind == 2 else 'cube'}."]}
    # Not a perfect power: one line of nearest-power reasoning
    # on |n| (for a negative cube, |n| between two cubes is
    # exactly why n is not one either).
    shown = abs(n)
    if hindi:
        naam = "पूर्ण वर्ग" if kind == 2 else "पूर्ण घन"
        if kind == 2 and n < 0:
            step = ("ऋणात्मक संख्या किसी भी पूर्ण संख्या का "
                    "वर्ग नहीं होती।")
        else:
            step = (f"{lo}{sup} = {lo ** kind} और "
                    f"{lo + 1}{sup} = {(lo + 1) ** kind} — "
                    f"{shown} इनके बीच है, इसलिए किसी पूर्ण "
                    f"संख्या का "
                    f"{'वर्ग' if kind == 2 else 'घन'} नहीं है।")
        return {"type": "number_theory", "op": op,
                "answer": f"नहीं — {n} {naam} नहीं है",
                "steps": [step]}
    if hinglish:
        naam = "perfect square" if kind == 2 else "perfect cube"
        if kind == 2 and n < 0:
            step = ("Negative sankhya kisi bhi poori sankhya "
                    "ka varg nahi hoti.")
        else:
            step = (f"{lo}{sup} = {lo ** kind} aur "
                    f"{lo + 1}{sup} = {(lo + 1) ** kind} — "
                    f"{shown} inke beech hai, isliye kisi bhi "
                    f"poori sankhya ka "
                    f"{'varg' if kind == 2 else 'ghan'} nahi hai.")
        return {"type": "number_theory", "op": op,
                "answer": f"Nahi — {n} {naam} nahi hai",
                "steps": [step]}
    naam = "perfect square" if kind == 2 else "perfect cube"
    if kind == 2 and n < 0:
        step = ("A negative number is not the square of any "
                "whole number.")
    else:
        step = (f"{lo}{sup} = {lo ** kind} and "
                f"{lo + 1}{sup} = {(lo + 1) ** kind} — {shown} "
                f"lies between them, so it is not the "
                f"{'square' if kind == 2 else 'cube'} of any "
                f"whole number.")
    return {"type": "number_theory", "op": op,
            "answer": f"No — {n} is not a {naam}",
            "steps": [step]}


def solve_number_theory(question: str):
    q = question.lower()

    # Wave 140: perfect square / cube haan-nahi asks.
    _pc140 = _perfect_power_check140(question, q)
    if _pc140 is not None:
        return _pc140

    # Wave 47: "How many factors does 36 have?" — the count
    # of divisors, tau(n) = product of (exponent + 1) over
    # the prime factorisation. This ask never reached this
    # solver at all and the arithmetic simplifier turned the
    # sentence into a letter-product (Wave 35 audit #314-317:
    # 36 -> 9, 48 -> 10, 27 -> 4, 100 -> 9).
    if re.search(r"(how\s+many|number\s+of|total\s+number\s+of)"
                 r"\s+(factors|divisors)\b", q):
        n = _first_int(question)
        if n is not None and n >= 1:
            f = factorint(n)
            count = 1
            for e in f.values():
                count *= e + 1
            steps = [
                f"Prime factorisation: {n} = {_factor_str(n)}",
                "Number of factors = (each exponent + 1), "
                "all multiplied: "
                + " × ".join(f"({e} + 1)" for e in f.values())
                + f" = {count}",
            ]
            return {"type": "number_theory", "op": "factor_count",
                    "answer": str(count), "value": count,
                    "steps": steps}

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

    # HCF × LCM = product of the two numbers (Waves 52 + 56,
    # unified at merge-3 — both waves fixed echo case #437
    # with the same relation; this single block keeps Wave
    # 52's anchored patterns widened with Wave 56's gcd /
    # "=" forms): "The HCF of two numbers is 12 and their
    # LCM is 240. If one number is 60, find the other
    # number." — the together-branch below read the three
    # numbers as the operands and echoed the givens back
    # ("HCF = 12, LCM = 240"). For two numbers,
    # first × second = HCF × LCM.
    _mh = re.search(r"(?:hcf|gcd)\s+(?:of\s+(?:the\s+)?two"
                    r"\s+numbers\s+)?(?:is|=)\s*(\d+)", q)
    _ml = re.search(r"lcm\s+(?:of\s+(?:the\s+)?two\s+numbers"
                    r"\s+)?(?:is|=)\s*(\d+)", q)
    _mo = re.search(r"one\s+(?:of\s+(?:the\s+)?(?:two\s+)?)?"
                    r"numbers?\s+is\s+(\d+)", q)
    if _mh and _ml and _mo and "other" in q:
        _h, _l, _one = (int(_mh.group(1)), int(_ml.group(1)),
                        int(_mo.group(1)))
        if _one and (_h * _l) % _one == 0:
            _other = _h * _l // _one
            steps = [
                "For two numbers: first number × second "
                "number = HCF × LCM",
                f"{_one} × second number = {_h} × {_l} "
                f"= {_h * _l}",
                f"Second number = {_h * _l} ÷ {_one} "
                f"= {_other}",
            ]
            return {"type": "number_theory",
                    "op": "hcf_lcm_other",
                    "answer": str(_other), "value": _other,
                    "steps": steps}

    # Wave 57: Devanagari HCF / LCM — "12 और 18 का महत्तम
    # समापवर्तक बताओ" / "12 और 15 का लघुत्तम समापवर्त्य निकालो".
    # (Digits reach here in ASCII: the router's spelling
    # normalisation converts Devanagari digits first.)
    if "महत्तम समापवर्तक" in q or "लघुत्तम समापवर्त्य" in q:
        nums = _pair_operands(
            question, q, "gcd" if "महत्तम समापवर्तक" in q
            else "lcm")
        if len(nums) >= 2:
            import math
            a, b = nums[0], nums[1]
            if "महत्तम समापवर्तक" in q:
                g = a
                for v in nums[1:]:
                    g = math.gcd(g, v)
                steps = [
                    f"{a} = {_factor_str(a)}",
                    f"{b} = {_factor_str(b)}",
                    "उभयनिष्ठ अभाज्य गुणनखंडों की सबसे छोटी घातें "
                    "लें।",
                    f"महत्तम समापवर्तक (HCF) = {g}",
                ]
                return {"type": "number_theory", "op": "gcd",
                        "answer": str(g), "value": g,
                        "steps": steps}
            l = a
            for v in nums[1:]:
                l = l * v // math.gcd(l, v)
            steps = [
                f"{a} = {_factor_str(a)}",
                f"{b} = {_factor_str(b)}",
                "हर अभाज्य गुणनखंड की सबसे बड़ी घात लें।",
                f"लघुत्तम समापवर्त्य (LCM) = {l}",
            ]
            return {"type": "number_theory", "op": "lcm",
                    "answer": str(l), "value": l, "steps": steps}

    # Wave 59: the PRODUCT of HCF and LCM asked directly
    # ("12 aur 16 ka HCF guna LCM kitna hoga?") — the
    # together-branch below read it as a both-values ask and
    # echoed "HCF = 4, LCM = 48". For two numbers the product
    # is just the numbers' own product.
    if ("hcf" in q or "gcd" in q) and "lcm" in q and re.search(
            r"(?:hcf|gcd)\s*(?:guna|×|x|\*|times)|"
            r"product\s+of\s+(?:the\s+)?(?:hcf|gcd)", q):
        nums = _pair_operands(question, q, "both")
        if len(nums) >= 2:
            a, b = nums[0], nums[1]
            import math
            g = math.gcd(a, b)
            l = a * b // g
            steps = [
                "For two numbers: HCF × LCM = first number "
                "× second number",
                f"HCF = {g}, LCM = {l}",
                f"HCF × LCM = {g} × {l} = {a * b} "
                f"(= {a} × {b})",
            ]
            return {"type": "number_theory",
                    "op": "hcf_lcm_product",
                    "answer": str(a * b), "value": a * b,
                    "steps": steps}

    # Wave 30: HCF and LCM asked TOGETHER ("Find the HCF and
    # LCM of 12 and 18") — the HCF branch below used to fire
    # alone and the LCM was silently never given.
    _wants_gcd = "gcd" in q or "hcf" in q or "greatest common" in q
    _wants_lcm = "lcm" in q or "least common multiple" in q
    if _wants_gcd and _wants_lcm:
        nums = _pair_operands(question, q, "both")
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
        nums = _pair_operands(question, q, "gcd")
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
        nums = _pair_operands(question, q, "lcm")
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

    # Wave 65: prime COUNTING and friends. The prime check
    # below reads the first integer as the number to test,
    # so "how many prime numbers are there between 40 and
    # 60?" answered "40 is not prime". These gated forms
    # run first.
    _mb65 = re.search(r"between\s+(\d+)\s+and\s+(\d+)", q)
    if "prime" in q and _mb65 and ("how many" in q
                                   or "count" in q):
        _a65, _b65 = int(_mb65.group(1)), int(_mb65.group(2))
        _lo65, _hi65 = min(_a65, _b65), max(_a65, _b65)
        _ps65 = [n for n in range(_lo65 + 1, _hi65)
                 if isprime(n)]
        return {"type": "number_theory", "op": "prime_count",
                "answer": str(len(_ps65)), "value": len(_ps65),
                "steps": [
                    f"Prime numbers between {_lo65} and "
                    f"{_hi65}: "
                    + (", ".join(str(p) for p in _ps65)
                       or "none"),
                    f"Count = {len(_ps65)}"]}
    if "smallest factor" in q:
        n = _first_int(question)
        if n is not None and n >= 2:
            _f65 = min(factorint(n)) if not isprime(n) else n
            return {"type": "number_theory",
                    "op": "smallest_factor",
                    "answer": str(_f65), "value": _f65,
                    "steps": [
                        f"{n} = {_f65} × {n // _f65}, and no "
                        f"smaller factor (other than 1) divides"
                        f" it" if not isprime(n) else
                        f"{n} is prime, so its smallest factor "
                        f"other than 1 is {n} itself"]}
    if "smallest prime" in q and "factor" not in q:
        return {"type": "number_theory", "op": "smallest_prime",
                "answer": "2", "value": 2,
                "steps": ["2 is the smallest prime number — "
                          "and the only even one"]}
    # Remainder: "find the remainder when 859 is divided
    # by 11" (and the Roman-Hindi translation canonical).
    _mr65 = re.search(r"remainder[^0-9]{0,40}?(\d+)\s+"
                      r"(?:is\s+)?divided\s+by\s+(\d+)", q) or \
        re.search(r"(\d+)\s+divided\s+by\s+(\d+)[^.]{0,40}?"
                  r"remainder", q)
    if _mr65:
        _a65, _b65 = int(_mr65.group(1)), int(_mr65.group(2))
        if _b65:
            return {"type": "number_theory", "op": "remainder",
                    "answer": str(_a65 % _b65),
                    "value": _a65 % _b65,
                    "steps": [
                        f"{_a65} = {_b65} × {_a65 // _b65} + "
                        f"{_a65 % _b65}",
                        f"Remainder = {_a65 % _b65}"]}
    # Smallest number divisible by both A and B = LCM.
    _ml65 = re.search(r"smallest\s+number\s+divisible\s+by\s+"
                      r"(?:both\s+)?(\d+)\s+and\s+(\d+)", q)
    if _ml65:
        import math
        _a65, _b65 = int(_ml65.group(1)), int(_ml65.group(2))
        _l65 = _a65 * _b65 // math.gcd(_a65, _b65)
        return {"type": "number_theory", "op": "lcm_smallest",
                "answer": str(_l65), "value": _l65,
                "steps": [
                    f"The smallest number divisible by both "
                    f"is their LCM",
                    f"LCM({_a65}, {_b65}) = {_l65}"]}
    # Smallest k-digit number divisible by d.
    _mk65 = re.search(r"smallest\s+(\d+)\s*-\s*digit\s+number"
                      r"\s+divisible\s+by\s+(\d+)", q)
    if _mk65:
        _k65, _d65 = int(_mk65.group(1)), int(_mk65.group(2))
        _base65 = 10 ** (_k65 - 1)
        _v65 = -(-_base65 // _d65) * _d65
        return {"type": "number_theory",
                "op": "smallest_k_digit_divisible",
                "answer": str(_v65), "value": _v65,
                "steps": [
                    f"The smallest {_k65}-digit number is "
                    f"{_base65}; {_base65} / {_d65} leaves "
                    f"remainder {_base65 % _d65}",
                    f"Add {_d65 - _base65 % _d65 if _base65 % _d65 else 0}"
                    f" to reach {_v65}"]}

    # Wave 150: prime-FACTOR asks are not primality asks.
    # "Find prime factors of 1728" used to hit the prime
    # check below and serve "1728 is not prime" — the
    # audits' isprime hijack (UP idx 3841/3847/3848, Bihar
    # likewise). Three shapes, all before the prime check:
    # (a) the factors are GIVEN and the number is asked
    #     ("prime factors of a number are 2, 2 and 3, find
    #     the number") -> their product;
    # (b) two factors are given and the prime factors of
    #     the number are asked -> factorise the product;
    # (c) the plain ask ("prime factors of N", possibly a
    #     list of numbers) -> factorise each number named
    #     after the ask phrase.
    _pf_given = re.search(
        r"prime\s+factors?\s+of\s+a\s+number\s+are\s+"
        r"([\d][\d,\s]*(?:and\s+\d+)?)", q)
    if _pf_given:
        _facs = [int(v) for v in
                 re.findall(r"\d+", _pf_given.group(1))]
        if _facs:
            import math as _m150
            _prod = _m150.prod(_facs)
            return {"type": "number_theory", "op": "factorint",
                    "answer": str(_prod), "value": _prod,
                    "steps": ["The number is the product of "
                              "its prime factors: "
                              + " × ".join(str(v) for v in _facs)
                              + f" = {_prod}"]}
    # (a2) the factorisation is described by COUNT words
    # ("prime factorisation of a number has one 2, two 3s,
    # and one 11. What is the number?") -> prod p^count.
    _pf_has = re.search(
        r"prime\s+factorisation\s+of\s+a\s+number\s+has\s+"
        r"(.+?)(?:\.|\?|$)", q)
    if _pf_has:
        _cnt_words = {"one": 1, "two": 2, "three": 3,
                      "four": 4, "five": 5, "six": 6}
        _pairs = re.findall(
            r"(one|two|three|four|five|six|\d+)\s+"
            r"(\d+)s?\b", _pf_has.group(1))
        if _pairs:
            _prod = 1
            _desc = []
            for _cnt, _p in _pairs:
                _e = _cnt_words.get(_cnt)
                if _e is None:
                    _e = int(_cnt)
                _prod *= int(_p) ** _e
                _desc.append(f"{_p}^{_e}")
            return {"type": "number_theory", "op": "factorint",
                    "answer": str(_prod), "value": _prod,
                    "steps": ["The number is the product of "
                              "its prime factors: "
                              + " × ".join(_desc)
                              + f" = {_prod}"]}
    _f_given = re.search(
        r"factors?\s+of\s+a\s+number\s+are\s+(\d+)\s+and\s+"
        r"(\d+)", q)
    if _f_given and "prime factor" in q:
        _n150 = int(_f_given.group(1)) * int(_f_given.group(2))
        return {"type": "number_theory", "op": "factorint",
                "answer": f"{_n150} = {_factor_str(_n150)}",
                "value": {str(k): v for k, v in
                          factorint(_n150).items()},
                "steps": [f"The number is {_f_given.group(1)} "
                          f"× {_f_given.group(2)} = {_n150}",
                          f"Prime factorisation: {_n150} = "
                          f"{_factor_str(_n150)}"]}
    if "prime factor" in q:
        _tail = q[q.index("prime factor"):]
        _of = _tail.index("of") if "of" in _tail else -1
        _nums = [int(v) for v in re.findall(
            r"\d+", _tail[_of + 2:])] if _of >= 0 else []
        # Unique numbers only, and at most 6: a longer
        # tail is a whole textbook PAGE whose numbers are
        # not a factorisation list (the Ganita Prakash
        # exposition pages) — leave those to the layers
        # below instead of factorising the page.
        _uniq = list(dict.fromkeys(_nums))
        if len(_uniq) > 6:
            _nums = []
        elif _uniq != _nums or 1 in _uniq:
            _nums = [v for v in _uniq if v > 1]
        if _nums and _nums != [1]:
            if len(_nums) == 1:
                _n = _nums[0]
                return {"type": "number_theory",
                        "op": "factorint",
                        "answer": _factor_str(_n),
                        "value": {str(k): v for k, v in
                                  factorint(_n).items()},
                        "steps": [f"Break {_n} into prime "
                                  f"factors: {_factor_str(_n)}"]}
            _parts = [f"{_n} = {_factor_str(_n)}"
                      for _n in _nums]
            return {"type": "number_theory", "op": "factorint",
                    "answer": "; ".join(_parts),
                    "value": None,
                    "steps": [f"Prime factorisation: {_p}"
                              for _p in _parts]}

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
