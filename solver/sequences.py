"""Sequences & series: AP/GP nth term and sums, sums of natural
numbers / squares / cubes."""
import re

import sympy as sp

from .expression_parser import fmt_num


def _parse_series(text: str):
    """Numbers of an explicit series like '2, 5, 8' (stops at '...' etc.)."""
    m = re.search(r"(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+)", text)
    if not m:
        return []
    return [float(v) if "." in v else int(v)
            for v in re.findall(r"-?\d+(?:\.\d+)?", m.group(1))]


def _classify(terms):
    if len(terms) >= 3:
        diffs = [terms[i + 1] - terms[i] for i in range(len(terms) - 1)]
        if all(d == diffs[0] for d in diffs):
            return "AP", diffs[0]
        if terms[0] != 0:
            ratios = [terms[i + 1] / terms[i]
                      for i in range(len(terms) - 1)]
            if all(abs(r - ratios[0]) < 1e-12 for r in ratios):
                return "GP", ratios[0]
    if len(terms) == 2:
        return "AP", terms[1] - terms[0]
    return None, None


def _get_params(q):
    """a=.., d=../r=.., n=.. style parameters."""
    out = {}
    for name in ("a", "d", "r", "n"):
        m = re.search(rf"\b{name}\s*=\s*(-?\d+(?:\.\d+)?)", q)
        if m:
            v = m.group(1)
            out[name] = float(v) if "." in v else int(v)
    return out


def _ordinal(n):
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def solve_sequences(question: str):
    q = question.lower()
    params = _get_params(q)

    # --- Wave 32: nth term of an AP from the END -----------------
    _m_end = re.search(
        r"(\d+)(?:st|nd|rd|th)\s+term\s+from\s+the\s+end", q)
    if _m_end:
        _terms = _parse_series(q)
        _kind, _d = _classify(_terms) if _terms else (None, None)
        _m_last = re.search(r"(?:\.\.\.|…)\s*,?\s*"
                            r"(-?\d+(?:\.\d+)?)", q)
        if _kind == "AP" and _m_last and _d:
            _a = _terms[0]
            _l = float(_m_last.group(1))
            _k = int(_m_end.group(1))
            _span = (_l - _a) / _d
            if abs(_span - round(_span)) < 1e-9:
                _N = int(round(_span)) + 1
                if 1 <= _k <= _N:
                    _pos = _N - _k + 1
                    _val = _a + (_pos - 1) * _d
                    steps = [
                        f"The AP has a = {_a}, d = {_d} and "
                        f"last term l = {_l:g}.",
                        f"Number of terms N = (l - a)/d + 1 "
                        f"= {_N}.",
                        f"The {_k}th term from the end is "
                        f"term number N - {_k} + 1 = {_pos} "
                        f"from the start.",
                        f"a_{_pos} = a + ({_pos} - 1)d = "
                        f"{_val:g}",
                    ]
                    return {"type": "sequences",
                            "op": "ap_nth_from_end",
                            "answer": fmt_num(_val),
                            "value": _val, "steps": steps}

    # --- Wave 32: how many AP terms give a stated sum ------------
    if "how many terms" in q and "sum" in q:
        _terms = _parse_series(q)
        _kind, _d = _classify(_terms) if _terms else (None, None)
        _m_sum = re.search(r"sum[^.]{0,40}?(?:is|=)\s*"
                           r"(-?\d+(?:\.\d+)?)", q)
        if _kind == "AP" and _m_sum:
            from fractions import Fraction as _F
            _a = _F(str(_terms[0]))
            _df = _F(str(_d))
            _S = _F(str(_m_sum.group(1)))
            # (n/2)(2a + (n-1)d) = S ->
            # d n^2 + (2a - d) n - 2S = 0
            _A, _B, _C = _df, 2 * _a - _df, -2 * _S
            if _A != 0:
                _disc = _B * _B - 4 * _A * _C
                if _disc >= 0:
                    _sq = sp.sqrt(sp.Rational(_disc.numerator,
                                              _disc.denominator))
                    if _sq.is_number and _sq ** 2 == _disc:
                        for _cand in (
                                (-_B + _sq) / (2 * _A),
                                (-_B - _sq) / (2 * _A)):
                            if _cand > 0 and \
                                    float(_cand).is_integer():
                                _n = int(_cand)
                                steps = [
                                    f"Sum of n terms: S_n = "
                                    f"(n/2)(2a + (n - 1)d) "
                                    f"with a = {_a}, "
                                    f"d = {_df}.",
                                    f"Setting S_n = {_S} "
                                    f"gives {_A}·n^2 + "
                                    f"{_B}·n "
                                    f"{'+' if _C >= 0 else ''}"
                                    f"{_C} = 0.",
                                    f"Solving: n = {_n} "
                                    f"(the positive root).",
                                ]
                                return {
                                    "type": "sequences",
                                    "op": "ap_terms_for_sum",
                                    "answer": str(_n),
                                    "value": _n, "steps": steps}

    # Sum of first n natural numbers / squares / cubes
    m = re.search(
        r"sum\s+of\s+(?:the\s+)?first\s+(\d+)\s+(natural\s+numbers|"
        r"squares|cubes)", q)
    if m:
        n = int(m.group(1))
        kind = m.group(2)
        if kind.startswith("natural"):
            val = n * (n + 1) // 2
            steps = ["Sum of first n natural numbers = n(n + 1)/2",
                     f"= {n} × {n + 1} / 2 = {val}"]
        elif kind == "squares":
            val = n * (n + 1) * (2 * n + 1) // 6
            steps = ["Sum of squares = n(n + 1)(2n + 1)/6",
                     f"= {n} × {n + 1} × {2 * n + 1} / 6 = {val}"]
        else:
            val = (n * (n + 1) // 2) ** 2
            steps = ["Sum of cubes = [n(n + 1)/2]^2",
                     f"= [{n} × {n + 1} / 2]^2 = {val}"]
        return {"type": "sequences", "op": "series_sum",
                "answer": fmt_num(val), "value": val, "steps": steps}

    terms = _parse_series(q)
    kind, ratio_diff = (None, None)
    if terms:
        kind, ratio_diff = _classify(terms)
    if kind is None:
        if "gp" in q or "geometric" in q:
            kind = "GP"
        elif "ap" in q or "arithmetic" in q:
            kind = "AP"
    if kind is None:
        return {"type": "sequences", "op": "unknown",
                "answer": "Give me the series, e.g. '10th term of AP "
                          "2, 5, 8' or 'sum of first 10 terms of GP "
                          "3, 6, 12'.",
                "steps": []}

    a = terms[0] if terms else params.get("a")
    if kind == "AP":
        d = ratio_diff if terms else params.get("d")
        if a is None or d is None:
            return {"type": "sequences", "op": "unknown",
                    "answer": "I need the first term and common "
                              "difference.",
                    "steps": []}
        # Wave 30: "Which term of the AP ... is V?" — invert
        # a_n = a + (n-1)d instead of asking for a term number.
        if "which term" in q:
            mv = re.search(r"\bis\s+(-?\d+(?:\.\d+)?)\s*\?*\s*$",
                           q.strip())
            if mv and d != 0:
                V = float(mv.group(1))
                V = int(V) if V == int(V) else V
                num = V - a
                if num % d == 0 and num // d >= 0:
                    n = int(num // d) + 1
                    steps = [
                        f"AP with a = {fmt_num(a)}, "
                        f"d = {fmt_num(d)}",
                        "Set the nth term equal to the given "
                        "value: a + (n - 1)d = "
                        f"{fmt_num(V)}",
                        f"(n - 1) = ({fmt_num(V)} - "
                        f"{fmt_num(a)}) ÷ {fmt_num(d)} = "
                        f"{fmt_num(num // d)}, so "
                        f"n = {n}",
                    ]
                    return {"type": "sequences",
                            "op": "ap_which_term",
                            "answer": f"The {_ordinal(n)} term",
                            "value": n, "steps": steps}
                # A value WAS named and it is genuinely not
                # reachable — that is the honest exact answer.
                return {"type": "sequences", "op": "ap_which_term",
                        "answer": f"{fmt_num(V)} is not a term "
                                  f"of this AP.",
                        "steps": [
                            f"a + (n - 1)d = {fmt_num(V)} gives "
                            f"n - 1 = {fmt_num(num)} ÷ "
                            f"{fmt_num(d)}, which is not a "
                            f"whole number, so no term equals "
                            f"{fmt_num(V)}.",
                        ]}
        m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
        wants_sum = "sum" in q
        n = None
        m2 = re.search(r"first\s+(\d+)\s+terms", q)
        if m2:
            n = int(m2.group(1))
            wants_sum = True
        elif "n" in params:
            n = params["n"]
        if wants_sum and n:
            val = n * (2 * a + (n - 1) * d) / 2
            steps = [
                f"AP with a = {fmt_num(a)}, d = {fmt_num(d)}",
                "Sum of first n terms: S_n = n/2 · (2a + (n - 1)d)",
                f"S_{n} = {n}/2 × (2×{fmt_num(a)} + {n - 1}×"
                f"{fmt_num(d)}) = {fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "ap_sum",
                    "answer": fmt_num(val), "value": val, "steps": steps}
        if m:
            n = int(m.group(1))
            val = a + (n - 1) * d
            steps = [
                f"AP with a = {fmt_num(a)}, d = {fmt_num(d)}",
                "nth term: a_n = a + (n - 1)d",
                f"a_{n} = {fmt_num(a)} + ({n} - 1) × {fmt_num(d)} = "
                f"{fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "ap_nth_term",
                    "answer": fmt_num(val), "value": val, "steps": steps}

    if kind == "GP":
        r = ratio_diff if terms else params.get("r")
        if a is None or r is None:
            return {"type": "sequences", "op": "unknown",
                    "answer": "I need the first term and common ratio.",
                    "steps": []}
        # Wave 30: "Which term of the GP ... is V?"
        if "which term" in q:
            mv = re.search(r"\bis\s+(-?\d+(?:\.\d+)?)\s*\?*\s*$",
                           q.strip())
            if mv and r not in (0, 1):
                V = float(mv.group(1))
                V = int(V) if V == int(V) else V
                cur, n = a, 1
                while n <= 500 and cur != V:
                    cur = cur * r
                    n += 1
                if cur == V:
                    steps = [
                        f"GP with a = {fmt_num(a)}, "
                        f"r = {fmt_num(r)}",
                        "Keep multiplying by the common ratio "
                        "until the given value appears: it is "
                        f"reached at term {n}.",
                        f"Check: a·r^{n - 1} = {fmt_num(a)} × "
                        f"{fmt_num(r)}^{n - 1} = {fmt_num(V)}",
                    ]
                    return {"type": "sequences",
                            "op": "gp_which_term",
                            "answer": f"The {_ordinal(n)} term",
                            "value": n, "steps": steps}
                return {"type": "sequences", "op": "gp_which_term",
                        "answer": f"{fmt_num(V)} is not a term "
                                  f"of this GP.",
                        "steps": [
                            "Multiplying the first term by the "
                            "common ratio again and again never "
                            f"reaches {fmt_num(V)}.",
                        ]}
        m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
        wants_sum = "sum" in q
        n = None
        m2 = re.search(r"first\s+(\d+)\s+terms", q)
        if m2:
            n = int(m2.group(1))
            wants_sum = True
        elif "n" in params:
            n = params["n"]
        if wants_sum and n:
            if r == 1:
                val = a * n
            else:
                val = a * (r ** n - 1) / (r - 1)
            steps = [
                f"GP with a = {fmt_num(a)}, r = {fmt_num(r)}",
                "Sum of first n terms: S_n = a(r^n - 1)/(r - 1)",
                f"S_{n} = {fmt_num(a)} × ({fmt_num(r)}^{n} - 1) / "
                f"({fmt_num(r)} - 1) = {fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "gp_sum",
                    "answer": fmt_num(val), "value": val, "steps": steps}
        if m:
            n = int(m.group(1))
            val = a * r ** (n - 1)
            steps = [
                f"GP with a = {fmt_num(a)}, r = {fmt_num(r)}",
                "nth term: a_n = a·r^(n-1)",
                f"a_{n} = {fmt_num(a)} × {fmt_num(r)}^{n - 1} = "
                f"{fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "gp_nth_term",
                    "answer": fmt_num(val), "value": val, "steps": steps}

    return {"type": "sequences", "op": "unknown",
            "answer": "Tell me which term or sum you want, e.g. '10th "
                      "term of AP 2, 5, 8'.",
            "steps": []}
