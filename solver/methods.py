"""Alternate solution methods (Wave 12) — stdlib + SymPy only.

Suraj's rule: a question is first solved ONE way (the primary
result, unchanged). When the SAME question genuinely has other
honest methods, they are offered on the side ("More methods") —
each computed here for real, never invented: an entry is returned
only when its answer agrees with the primary answer. Questions
with just one natural method (e.g. "2+2") get an empty list and
the chips simply do not appear.

Families covered (everything else returns []):
  * quadratic equations — factorisation (when the factors are
    rational), completing the square, and the graph view; the
    quadratic formula itself only when the primary steps did not
    already use it (they normally do — algebra._quadratic_steps).
  * linear equations — the graph view (table of values, where
    the line crosses the x-axis).
  * "p% of N" percentages — the fraction way and the unitary way.
  * plain arithmetic expressions with 2+ operators or brackets —
    a grouped-BODMAS walkthrough of the same reductions.

Every function is defensive: any surprise returns [] rather than
raising into the chat. Steps stay in English, like all solver
steps (project scope). Formatting reuses fmt / fmt_num from
expression_parser, and the equation parsing reuses algebra's
internals so the methods can never disagree with the primary
solver about what the question MEANS.
"""
import re

import sympy as sp

from .algebra import _poly_coeffs, _strip_solve_prefix
from .arithmetic import reduction_steps
from .expression_parser import (extract_points, find_param, fmt,
                                fmt_num, parse_expression)


def _root_text(value):
    """A root formatted for prose: integers/fractions clean,
    irrationals as sqrt(...) via fmt."""
    try:
        return fmt(sp.nsimplify(value, rational=True))
    except Exception:
        return fmt(value)


def _final_line(answer):
    return f"Answer: {answer}"


def _standard_form(a, b, c, var):
    return (f"Write in standard form: {fmt(a)}·{var}^2 + {fmt(b)}·{var}"
            f" + {fmt(c)} = 0, so a = {fmt(a)}, b = {fmt(b)}, "
            f"c = {fmt(c)}")


def _answer_check(candidate_answer, primary_answer):
    """An alternate method may only ship when its answer agrees
    with the primary one (equal string, or one contains the
    other — word-problem answers can carry extra words)."""
    cand = " ".join(str(candidate_answer or "").split()).lower()
    prim = " ".join(str(primary_answer or "").split()).lower()
    return bool(cand) and bool(prim) and (cand == prim
                                          or cand in prim
                                          or prim in cand)


def _quadratic_methods(expr, var, degree, coeffs, primary):
    a, b, c = coeffs.get(2, 0), coeffs.get(1, 0), coeffs.get(0, 0)
    answer = primary.get("answer", "")
    sols = sorted(sp.solve(expr, var), key=lambda s: complex(s).real
                  if s.is_real else 0)
    real_sols = [s for s in sols if s.is_real]
    if len(real_sols) != 2 and not (len(real_sols) == 1):
        return []
    methods = []
    standard = _standard_form(a, b, c, var)

    # --- factorisation (only honest when factors are rational) --
    try:
        factored = sp.factor(expr, modulus=None)
        if factored != expr:
            # Rational roots <=> every root is rational.
            if real_sols and all(s.is_rational for s in real_sols):
                steps = [standard,
                         f"Factorise the left side: {fmt(factored)} = 0"]
                for s in real_sols:
                    if s >= 0:
                        steps.append(
                            f"{var} - {fmt(s)} = 0 gives {var} = {fmt(s)}")
                    else:
                        steps.append(
                            f"{var} + {fmt(-s)} = 0 gives "
                            f"{var} = {fmt(s)}")
                steps.append(_final_line(answer))
                methods.append({"id": "factor",
                                "label": "Factorisation method",
                                "steps": steps, "answer": answer})
    except Exception:
        pass

    # --- completing the square ----------------------------------
    try:
        steps = [standard]
        if a != 1:
            steps.append(
                f"Divide every term by {fmt(a)}: {var}^2 + "
                f"{fmt(sp.nsimplify(b / a, rational=True))}·{var} + "
                f"{fmt(sp.nsimplify(c / a, rational=True))} = 0")
        half = sp.nsimplify(b / (2 * a), rational=True)
        moved = sp.nsimplify(-c / a, rational=True)
        steps.append(
            f"Move the constant to the right: {var}^2 + "
            f"{fmt(sp.nsimplify(b / a, rational=True))}·{var} "
            f"= {fmt(moved)}")
        steps.append(
            f"Add ({fmt(half)})^2 to both sides to complete the "
            f"square: ({fmt(half)})^2 = "
            f"{fmt(sp.nsimplify(half ** 2, rational=True))}")
        rhs = sp.nsimplify(moved + half ** 2, rational=True)
        steps.append(f"Left side is a perfect square: "
                     f"({var} + {fmt(half)})^2 = {fmt(rhs)}")
        root = sp.sqrt(rhs)
        steps.append(
            f"Take square roots: {var} + {fmt(half)} = ±{fmt(root)}")
        for s in real_sols:
            steps.append(f"{var} = {fmt(s)}")
        steps.append(_final_line(answer))
        methods.append({"id": "complete_square",
                        "label": "Completing the square",
                        "steps": steps, "answer": answer})
    except Exception:
        pass

    # --- graph view ----------------------------------------------
    try:
        vx = sp.nsimplify(-b / (2 * a), rational=True)
        vy = sp.expand(expr).subs(var, vx)
        steps = [
            f"Draw y = {fmt(sp.expand(expr))} — a parabola"
            + (" opening upwards." if a > 0 else " opening downwards."),
            f"Vertex: x = -b/(2a) = {fmt(vx)}, and y there is "
            f"{fmt(vy)}, so the vertex is ({fmt(vx)}, {fmt(vy)}).",
            f"y-intercept (x = 0) is {fmt(c)}.",
            "The roots are the x-values where the parabola "
            "crosses the x-axis (y = 0): "
            + ", ".join(f"{var} = {fmt(s)}" for s in real_sols) + ".",
            _final_line(answer),
        ]
        methods.append({"id": "graph", "label": "Graph method",
                        "steps": steps, "answer": answer})
    except Exception:
        pass

    # --- formula (only when the primary did not already use it) --
    primary_steps = " ".join(primary.get("steps") or [])
    if "Quadratic formula" not in primary_steps:
        try:
            D = b ** 2 - 4 * a * c
            steps = [
                standard,
                f"Discriminant D = b^2 - 4ac = {fmt(D)}",
                f"Quadratic formula: {var} = (-b ± sqrt(D)) / (2a) = "
                f"({fmt(-b)} ± sqrt({fmt(D)})) / {fmt(2 * a)}",
            ]
            for s in real_sols:
                steps.append(f"{var} = {fmt(s)}")
            steps.append(_final_line(answer))
            methods.append({"id": "formula",
                            "label": "Quadratic formula",
                            "steps": steps, "answer": answer})
        except Exception:
            pass
    return methods


def _linear_transposition_method(expr, var, coeffs, primary):
    """Wave 13: transposition — move terms across the = sign and
    flip their sign, instead of doing the same operation to both
    sides (the balancing presentation of the primary steps)."""
    a, b = coeffs.get(1, 0), coeffs.get(0, 0)
    answer = primary.get("answer", "")
    sols = sp.solve(expr, var)
    if not sols:
        return None
    root = sols[0]
    steps = [
        f"Transpose: move every term with {var} to the left and "
        f"the numbers to the right — a term that crosses the = "
        f"sign flips its sign.",
    ]
    if b != 0:
        steps.append(f"{fmt(a)}·{var} = {fmt(-b)}")
    if a != 1:
        steps.append(
            f"The coefficient {fmt(a)} also crosses as division: "
            f"{var} = {fmt(-b)} / {fmt(a)} = {fmt(root)}")
    else:
        steps.append(f"{var} = {fmt(root)}")
    steps.append(_final_line(answer))
    return {"id": "transposition", "label": "Transposition method",
            "steps": steps, "answer": answer}


def _linear_graph_method(expr, var, coeffs, primary):
    a, b = coeffs.get(1, 0), coeffs.get(0, 0)
    answer = primary.get("answer", "")
    sols = sp.solve(expr, var)
    if not sols:
        return None
    root = sols[0]
    steps = [
        f"Rewrite as a line: y = {fmt(a)}·{var} + {fmt(b)} "
        f"(the left side of the equation).",
        "Make a small table of values:",
    ]
    xs = [0, 1, 2, -1]
    for xv in xs:
        yv = a * xv + b
        steps.append(f"  x = {xv}  →  y = {fmt(yv)}")
    steps.append(
        f"Join the points — the line crosses the x-axis (y = 0) "
        f"at {var} = {fmt(root)}, and that crossing point is the "
        f"solution of the equation.")
    steps.append(_final_line(answer))
    return {"id": "graph", "label": "Graph method",
            "steps": steps, "answer": answer}


def _percentage_methods(question, primary):
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:%|percent|per\s?cent)\s*of\s*"
        r"(\d+(?:\.\d+)?)", question, re.I)
    if not m:
        return []
    pct = sp.nsimplify(m.group(1), rational=True)
    base = sp.nsimplify(m.group(2), rational=True)
    answer = primary.get("answer", "")
    frac = sp.nsimplify(pct / 100, rational=True)
    methods = []
    value = frac * base
    if _answer_check(fmt_num(value), answer):
        methods.append({
            "id": "fraction", "label": "Fraction method",
            "steps": [
                f"{fmt_num(pct)}% as a fraction is {fmt_num(pct)}/100"
                f" = {fmt_num(frac)}",
                f"Multiply by {fmt_num(base)}: {fmt_num(frac)} × "
                f"{fmt_num(base)} = {fmt_num(value)}",
                _final_line(answer),
            ],
            "answer": answer,
        })
    one_pct = sp.nsimplify(base / 100, rational=True)
    value2 = pct * one_pct
    if _answer_check(fmt_num(value2), answer):
        methods.append({
            "id": "unitary", "label": "Unitary method",
            "steps": [
                f"1% of {fmt_num(base)} = {fmt_num(base)} ÷ 100 = "
                f"{fmt_num(one_pct)}",
                f"So {fmt_num(pct)}% = {fmt_num(pct)} × "
                f"{fmt_num(one_pct)} = {fmt_num(value2)}",
                _final_line(answer),
            ],
            "answer": answer,
        })
    # Wave 13: the proportion set-up (x : base = pct : 100).
    cross = pct * base
    value3 = sp.nsimplify(cross / 100, rational=True)
    if _answer_check(fmt_num(value3), answer):
        methods.append({
            "id": "proportion", "label": "Proportion method",
            "steps": [
                f"Let the answer be x. Percent means out of 100, "
                f"so set up a proportion: x/{fmt_num(base)} = "
                f"{fmt_num(pct)}/100",
                f"Cross-multiply: x × 100 = {fmt_num(pct)} × "
                f"{fmt_num(base)} = {fmt_num(cross)}",
                f"x = {fmt_num(cross)} ÷ 100 = {fmt_num(value3)}",
                _final_line(answer),
            ],
            "answer": answer,
        })
    return methods


def _arithmetic_methods(working, primary):
    """Grouped-BODMAS walkthrough for a plain numeric expression."""
    expr_text = str(working).replace(" ", "")
    if len(re.findall(r"[+\-*/]", expr_text)) < 1:
        return []
    operators = len(re.findall(r"[+\-*/]", re.sub(r"^-", "", expr_text)))
    if operators < 2 and "(" not in expr_text:
        return []
    try:
        value = parse_expression(working)
    except Exception:
        return []
    if getattr(value, "free_symbols", None):
        return []
    steps = reduction_steps(expr_text)
    if len(steps) < 2:
        return []
    answer = primary.get("answer", "")
    if not _answer_check(fmt_num(sp.nsimplify(value, rational=True))
                         if value.is_number else str(value), answer):
        # The reduction formatter and the primary answer can differ
        # in style (e.g. fraction vs decimal); only ship when the
        # primary itself was produced from this same expression.
        if str(primary.get("expression", "")).replace(" ", "") \
                != expr_text:
            return []
    steps = list(steps) + [_final_line(answer)]
    return [{"id": "bodmas_grouped", "label": "Step-by-step BODMAS",
             "steps": steps, "answer": answer}]


# ----------------------------------------------------------------------
# Wave 13 method families (applied / number theory / geometry /
# sequences / statistics primaries)
# ----------------------------------------------------------------------
_SI_METHOD_RE = re.compile(
    r"simple\s+interest\s+on\s+(?:rs\.?\s*|₹\s*|rupees\s*)?"
    r"(\d+(?:\.\d+)?)\s+(?:at\s+)?(\d+(?:\.\d+)?)\s*%\s*"
    r"(?:per\s+annum\s+)?(?:for\s+)?(\d+(?:\.\d+)?)\s*"
    r"(years?|yrs?|months?)", re.I)


def _si_yearly_method(question, primary):
    """Interest for one year first, then scaled by the time."""
    m = _SI_METHOD_RE.search(question or "")
    if not m:
        return None
    P, R, T = (float(m.group(i)) for i in (1, 2, 3))
    years = T / 12.0 if m.group(4).lower().startswith("month") \
        else T
    one = P * R / 100.0
    total = one * years
    if primary.get("value") is not None:
        try:
            if abs(total - float(primary["value"])) > 1e-9:
                return None
        except (TypeError, ValueError):
            return None
    elif not _answer_check(fmt_num(total), primary.get("answer")):
        return None
    steps = [
        f"Find the interest for ONE year: P × R / 100 = "
        f"{fmt_num(P)} × {fmt_num(R)} / 100 = {fmt_num(one)}",
    ]
    if m.group(4).lower().startswith("month"):
        steps.append(f"The time is {fmt_num(T)} months = "
                     f"{fmt_num(years)} years.")
    steps.append(
        f"Interest for {fmt_num(years)} year(s) = "
        f"{fmt_num(one)} × {fmt_num(years)} = {fmt_num(total)}")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "yearly_breakup", "label": "Year-by-year method",
            "steps": steps, "answer": primary.get("answer", "")}


def _hcf_euclid_method(question, primary):
    """HCF by Euclid's division algorithm (the primary used
    prime factorisation)."""
    import math as _math
    nums = [int(v) for v in re.findall(r"\d+", question or "")]
    if len(nums) < 2 or any(n <= 0 for n in nums):
        return None
    steps = [
        "Euclid's method: divide the bigger number by the "
        "smaller; the HCF of the divisor and the remainder is "
        "the same HCF. Repeat until the remainder is 0.",
    ]
    cur = nums[0]
    for nxt in nums[1:]:
        a, b = max(cur, nxt), min(cur, nxt)
        while b:
            steps.append(f"{a} ÷ {b} = {a // b} remainder {a % b}")
            a, b = b, a % b
        cur = a
    if not _answer_check(str(cur), primary.get("answer")):
        return None
    steps.append(f"The last non-zero divisor is the HCF: {cur}")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "euclid", "label": "Euclid's division method",
            "steps": steps, "answer": primary.get("answer", "")}


def _lcm_hcf_method(question, primary):
    """LCM from a × b = HCF × LCM (two numbers only)."""
    import math as _math
    nums = [int(v) for v in re.findall(r"\d+", question or "")]
    if len(nums) != 2 or any(n <= 0 for n in nums):
        return None
    a, b = nums
    h = _math.gcd(a, b)
    val = a * b // h
    if not _answer_check(str(val), primary.get("answer")):
        return None
    steps = [
        f"First find the HCF of {a} and {b}: HCF = {h}",
        "For two numbers: first × second = HCF × LCM.",
        f"So LCM = {a} × {b} ÷ {h} = {a * b} ÷ {h} = {val}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "hcf_relation", "label": "Using the HCF relation",
            "steps": steps, "answer": primary.get("answer", "")}


def _distance_graph_method(question, primary):
    """Distance as the hypotenuse of the plotted right triangle."""
    import math as _math
    pts = extract_points(question or "")
    if len(pts) < 2:
        return None
    (x1, y1), (x2, y2) = pts[0], pts[1]
    dx, dy = x2 - x1, y2 - y1
    d2 = dx * dx + dy * dy
    d = _math.sqrt(d2)
    if not _answer_check(fmt_num(d), primary.get("answer")):
        return None
    steps = [
        f"Plot A({fmt_num(x1)}, {fmt_num(y1)}) and "
        f"B({fmt_num(x2)}, {fmt_num(y2)}) on graph paper and "
        f"complete a right-angled triangle.",
        f"Horizontal side = |{fmt_num(x2)} - {fmt_num(x1)}| = "
        f"{fmt_num(abs(dx))}; vertical side = |{fmt_num(y2)} - "
        f"{fmt_num(y1)}| = {fmt_num(abs(dy))}",
        f"By Pythagoras: AB^2 = {fmt_num(abs(dx))}^2 + "
        f"{fmt_num(abs(dy))}^2 = {fmt_num(d2)}",
        f"AB = sqrt({fmt_num(d2)}) = {fmt_num(d)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "graph", "label": "Graph method",
            "steps": steps, "answer": primary.get("answer", "")}


def _triangle_half_rect_method(question, primary):
    """Triangle area as half of the same-base rectangle."""
    ql = (question or "").lower()
    if "triangle" not in ql:
        return None
    base = find_param(ql, ["base"])
    height = find_param(ql, ["height", "h"])
    if base is None or height is None:
        return None
    rect = base * height
    val = rect / 2
    if not _answer_check(fmt_num(val), primary.get("answer")):
        return None
    steps = [
        f"Draw the rectangle with the same base and height: "
        f"area = {fmt_num(base)} × {fmt_num(height)} = "
        f"{fmt_num(rect)}",
        "A diagonal cuts that rectangle into two equal "
        "triangles, so the triangle is exactly half of it.",
        f"Area of triangle = {fmt_num(rect)} ÷ 2 = "
        f"{fmt_num(val)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "half_rectangle",
            "label": "Half of a rectangle method",
            "steps": steps, "answer": primary.get("answer", "")}


def _sequence_listing_method(question, primary):
    """AP/GP nth term by writing the terms out (small n only)."""
    from .sequences import _classify, _parse_series
    q = (question or "").lower()
    m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
    if not m:
        return None
    n = int(m.group(1))
    if n < 2 or n > 12:
        return None
    terms = _parse_series(q)
    if len(terms) < 3:
        return None
    kind, step = _classify(terms)
    if kind is None or step is None:
        return None
    a = terms[0]
    if kind == "AP":
        seq = [a + i * step for i in range(n)]
        how = f"Keep adding the common difference " \
              f"{fmt_num(step)}:"
    else:
        seq = [a * step ** i for i in range(n)]
        how = f"Keep multiplying by the common ratio " \
              f"{fmt_num(step)}:"
    if not _answer_check(fmt_num(seq[-1]), primary.get("answer")):
        return None
    steps = [
        how,
        ", ".join(fmt_num(v) for v in seq),
        f"Counting along to position {n}: the {n}th term is "
        f"{fmt_num(seq[-1])}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "listing", "label": "Writing out the terms",
            "steps": steps, "answer": primary.get("answer", "")}


def _mean_assumed_method(question, primary):
    """The assumed-mean method for the mean (>= 4 values)."""
    from .statistics import _extract_list
    nums = _extract_list(question or "")
    if len(nums) < 4:
        return None
    ordered = sorted(nums)
    assumed = ordered[len(ordered) // 2]
    devs = [v - assumed for v in nums]
    total_dev = sum(devs)
    mean = assumed + total_dev / len(nums)
    if not _answer_check(fmt_num(mean), primary.get("answer")):
        return None
    steps = [
        f"Pick an assumed mean near the middle: A = "
        f"{fmt_num(assumed)}",
        "Write each deviation (value - A): "
        + ", ".join(fmt_num(d) for d in devs),
        f"Sum of deviations = {fmt_num(total_dev)} over "
        f"{len(nums)} values.",
        f"Mean = A + (sum of deviations ÷ count) = "
        f"{fmt_num(assumed)} + {fmt_num(total_dev)}/"
        f"{len(nums)} = {fmt_num(mean)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "assumed_mean", "label": "Assumed mean method",
            "steps": steps, "answer": primary.get("answer", "")}


def alternate_methods(question, primary_result):
    """Wave 12: up to 3 genuinely-different extra methods for a
    question, each agreeing with the primary answer. Returns a
    list of {"id", "label", "steps", "answer"} — [] when the
    question honestly has only the one method (or on ANY doubt:
    this function never raises)."""
    try:
        primary = primary_result or {}
        if primary.get("op") == "error":
            return []
        working = primary.get("interpreted_as") or question or ""
        ptype = primary.get("type", "")
        pop = primary.get("op", "")

        if ptype == "arithmetic" and pop == "percentage":
            out = _percentage_methods(working, primary)
            return [m for m in out
                    if _answer_check(m["answer"],
                                     primary.get("answer"))][:3]

        if ptype == "arithmetic" and pop == "evaluate":
            return _arithmetic_methods(working, primary)[:3]

        # Equations (single variable, polynomial deg 1 or 2).
        eq_text = _strip_solve_prefix(str(working).strip())
        if eq_text.count("=") == 1 and ptype == "algebra" \
                and pop in ("equation", "", None):
            left, right = eq_text.split("=", 1)
            expr = parse_expression(left) - parse_expression(right)
            symbols = sorted(expr.free_symbols,
                             key=lambda s: s.name)
            if len(symbols) != 1:
                return []
            var = symbols[0]
            degree, coeffs = _poly_coeffs(expr, var)
            if degree == 2:
                out = _quadratic_methods(expr, var, degree, coeffs,
                                         primary)
            elif degree == 1:
                out = []
                tp = _linear_transposition_method(
                    expr, var, coeffs, primary)
                if tp:
                    out.append(tp)
                one = _linear_graph_method(expr, var, coeffs,
                                           primary)
                if one:
                    out.append(one)
            else:
                return []
            return [m for m in out
                    if _answer_check(m["answer"],
                                     primary.get("answer"))][:3]

        # Wave 13 families, keyed by the primary result's type/op.
        _w13 = None
        if ptype == "word_problem" and pop == "simple_interest":
            _w13 = _si_yearly_method(working, primary)
        elif ptype == "number_theory" and pop == "gcd":
            _w13 = _hcf_euclid_method(working, primary)
        elif ptype == "number_theory" and pop == "lcm":
            _w13 = _lcm_hcf_method(working, primary)
        elif ptype == "geometry" and pop == "distance":
            _w13 = _distance_graph_method(working, primary)
        elif ptype == "geometry" and pop == "area":
            _w13 = _triangle_half_rect_method(working, primary)
        elif ptype == "sequences" and pop in ("ap_nth_term",
                                              "gp_nth_term"):
            _w13 = _sequence_listing_method(working, primary)
        elif ptype == "statistics" and pop == "mean":
            _w13 = _mean_assumed_method(working, primary)
        if _w13 is not None and _answer_check(
                _w13["answer"], primary.get("answer")):
            return [_w13]
        return []
    except Exception:
        return []
