"""Exponents & logarithms: evaluate logs, solve exponential/log equations."""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

x = sp.symbols("x")


def _ordinal140(n: int) -> str:
    """Wave 140: proper English ordinal ("4th", "21st",
    "23rd") for the nth-root working line."""
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def solve_exponents_logs(question: str):
    q = question.strip()
    qlow = q.lower()

    # Log SOLVE / inverse (Waves 56 + 58, unified at
    # merge-3): "If log x = 2.5 (base 10), find x",
    # "log_2 x = 5", "log2 x = 5", "ln x = 3" — the unknown
    # inside the log means var = base^value. Wave 56's block
    # handled the plain and "(base N)" forms (answer: the
    # bare number); Wave 58's added subscript bases, ln and
    # any variable letter (answer: "x = 32"). This single
    # block covers both sets; Wave 56's trailing-base lookup
    # is kept for "(base 2)" stated after the equation.
    _mlog = re.search(
        r"\blog\s*(?:_\s*(\d+(?:\.\d+)?)|\(\s*(\d+(?:\.\d+)?)"
        r"\s*\)|base\s+(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?))?\s*"
        r"\(?\s*([a-z])\s*\)?\s*=\s*(-?\d+(?:\.\d+)?)",
        qlow) or re.search(
        r"\bln\s*\(?\s*([a-z])\s*\)?\s*=\s*(-?\d+(?:\.\d+)?)",
        qlow)
    if _mlog:
        if _mlog.re.pattern.startswith(r"\bln"):
            _var, _rhs = _mlog.group(1), float(_mlog.group(2))
            _base = sp.E
            _bname = "e"
        else:
            _base = next((g for g in _mlog.groups()[:4]
                          if g is not None), None)
            _var, _rhs = _mlog.group(5), float(_mlog.group(6))
            if _base is None:
                _mb = re.search(r"base\s+(\d+(?:\.\d+)?)", qlow)
                _base = _mb.group(1) if _mb else None
            _base = float(_base) if _base is not None else 10.0
            _bname = fmt(_base)
        _val = float(_base) ** _rhs
        _exact = sp.nsimplify(_val, rational=True)
        _ans = fmt(_exact) if _exact.is_Integer \
            else fmt_num(_val)
        steps = [
            f"log base {_bname} of {_var} = {fmt(_rhs)} means "
            f"{_var} = {_bname}^{fmt(_rhs)} "
            f"(the definition of a logarithm).",
            f"{_var} = {_ans}",
        ]
        return {"type": "exponents_logs", "op": "log_solve",
                "answer": f"{_var} = {_ans}", "value": _val,
                "steps": steps}

    # log with explicit base: "log base 2 of 32", "log2(32)", "log_2(32)"
    m = re.search(
        r"log\s*(?:base\s*)?(\d+(?:\.\d+)?)\s*(?:of\s*|\(\s*|\s+)"
        r"(\d+(?:\.\d+)?)\s*\)?",
        qlow,
    ) or re.search(r"log_(\d+(?:\.\d+)?)\s*\(\s*(\d+(?:\.\d+)?)\s*\)", qlow) \
        or re.search(r"log_(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\b", qlow) \
        or re.search(r"(?:value\s+of|evaluate|find)\s+(?:the\s+)?"
                     r"log\s+(\d+(?:\.\d+)?)\b", qlow)
    if m:
        # Wave 58 (merge-3): the last pattern is the base-10
        # school convention — "find the value of log 100"
        # (no base written).
        if m.re.pattern.startswith("(?:value"):
            base, val = 10.0, float(m.group(1))
        else:
            base, val = float(m.group(1)), float(m.group(2))
        res = sp.log(val, base)
        steps = [
            f"log base {fmt(base)} of {fmt(val)} asks: {fmt(base)} raised "
            f"to what power gives {fmt(val)}?",
        ]
        exact = sp.nsimplify(res, rational=True)
        if exact.is_Integer or exact.is_Rational:
            steps.append(
                f"{fmt(base)}^{fmt(exact)} = {fmt(val)}, so the answer is "
                f"{fmt(exact)}"
            )
        else:
            steps.append(
                f"= ln({fmt(val)}) / ln({fmt(base)}) ≈ {fmt(float(res))}"
            )
        return {
            "type": "exponents_logs",
            "op": "log_value",
            "answer": fmt(sp.nsimplify(res, rational=True))
            if (sp.nsimplify(res, rational=True)).is_rational
            else fmt(float(res)),
            "value": float(res),
            "steps": steps,
        }

    # Wave 59: nth root stated in words — "find the 5th root
    # of 32", "the cube root of 27" (the symbol forms were
    # covered; the word form fell through entirely).
    _mroot = re.search(
        r"(\d+)(?:st|nd|rd|th)\s+root\s+of\s+(\d+(?:\.\d+)?)",
        qlow) or re.search(
            r"cube\s+root\s+of\s+(\d+(?:\.\d+)?)", qlow) or \
        re.search(r"square\s+root\s+of\s+(\d+(?:\.\d+)?)", qlow)
    if _mroot:
        if _mroot.re.pattern.startswith(r"(\d+)(?:st"):
            _nroot, _vroot = int(_mroot.group(1)), \
                float(_mroot.group(2))
        elif "cube" in _mroot.group(0):
            _nroot, _vroot = 3, float(_mroot.group(1))
        else:
            _nroot, _vroot = 2, float(_mroot.group(1))
        _res = sp.nsimplify(sp.real_root(
            sp.Rational(_vroot).limit_denominator(), _nroot))
        _exact = _res.is_Integer or _res.is_Rational
        # Wave 140: the working line read "The 2th root of
        # 729.0 is the number whose 2th power is 729.0" —
        # square/cube roots have proper names, other roots
        # take a proper ordinal, and a whole-number radicand
        # is shown without the ".0".
        _vtxt = str(int(_vroot)) if float(_vroot).is_integer() \
            else fmt(_vroot)
        if _nroot == 2:
            _w140 = (f"The square root of {_vtxt} is the "
                     f"number whose square is {_vtxt}.")
        elif _nroot == 3:
            _w140 = (f"The cube root of {_vtxt} is the "
                     f"number whose cube is {_vtxt}.")
        else:
            _o140 = _ordinal140(_nroot)
            _w140 = (f"The {_o140} root of {_vtxt} is the "
                     f"number whose {_o140} power is {_vtxt}.")
        return {
            "type": "exponents_logs",
            "op": "nth_root",
            "answer": fmt(_res) if _exact else
                      fmt(float(_res)),
            "value": float(_res),
            "steps": [
                _w140,
                f"Answer = {fmt(_res) if _exact else fmt(float(_res))}",
            ],
        }

    # Log / exponential equation: anything containing log/ln and '='
    if "=" in q and ("log" in qlow or "ln" in qlow or "^" in q or "**" in q):
        text = re.sub(r"^\s*solve\b", "", q, flags=re.I).strip()
        left, right = text.split("=", 1)
        expr = parse_expression(left) - parse_expression(right)
        var = sorted(expr.free_symbols, key=lambda s: s.name)
        var = var[0] if var else x
        sols = sp.solve(expr, var)
        steps = [
            f"Write as one equation: {fmt(expr)} = 0",
            "Use log/exp rules (log a + log b = log(ab); a^x = a^y means "
            "x = y) and solve.",
        ]
        sol_strs = [fmt(s) for s in sols]
        answer = ", ".join(f"{var} = {s}" for s in sol_strs) or "No solution"
        steps.append(f"Solution: {answer}")
        return {
            "type": "exponents_logs",
            "op": "equation",
            "answer": answer,
            "solutions": sol_strs,
            "steps": steps,
        }

    # Plain exponential/log expression to evaluate/simplify.
    expr = parse_expression(q)
    val = sp.simplify(expr)
    steps = [f"Evaluate {fmt(expr)} using exponent/log rules."]
    out = {
        "type": "exponents_logs",
        "op": "evaluate",
        "answer": fmt(val),
        "steps": steps + [f"= {fmt(val)}"],
    }
    if not val.free_symbols:
        out["value"] = float(val)
    return out
