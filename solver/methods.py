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
  * Wave 53 — pairs of linear equations (substitution /
    elimination / cross-multiplication, whichever the primary
    did not work), AP sums (Gauss pairing), GP sums (adding
    the terms), compound interest (year by year), profit/loss
    percent and reverse profit/loss (unitary), discount
    (direct percent), marks percent (unitary), unitary-cost
    (proportion), ratio division (fraction of the whole),
    LCM (division method), HCF+LCM (Euclid + product
    relation), median (position formula), probability
    (complement rule for die / coins / balls / cards), trig
    ratio-from-ratio (identities), standard trig values
    (derived from the two standard triangles), circle area
    and circumference (via the diameter), rectangle / square
    area (counting unit squares), perimeter (adding the
    sides), cuboid / cube volume (layers), cylinder volume
    (base area × height) and cone volume (one-third of the
    cylinder).

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
from .pi_policy import pi_choice


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
    # Wave 53: "A is what percent of B" — the primary divides
    # and multiplies by 100; the alternates simplify the
    # fraction first, and use the unitary route.
    mw = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:is\s+)?what\s+percent\s+of\s*"
        r"(\d+(?:\.\d+)?)", question, re.I)
    _wp = None  # (part, whole) for either word order
    if mw:
        _wp = (mw.group(1), mw.group(2))
    else:
        # The other word order: "What percent of B is A?"
        mo = re.search(
            r"what\s+percent\s+of\s+(\d+(?:\.\d+)?)\s+is\s+"
            r"(\d+(?:\.\d+)?)", question, re.I)
        if mo:
            _wp = (mo.group(2), mo.group(1))
    if _wp:
        part = sp.nsimplify(_wp[0], rational=True)
        whole = sp.nsimplify(_wp[1], rational=True)
        if whole == 0:
            return []
        answer = primary.get("answer", "")
        pct = part * 100 / whole
        frac = sp.nsimplify(part / whole, rational=True)
        methods = []
        if _answer_check(fmt_num(pct), answer):
            methods.append({
                "id": "fraction", "label": "Fraction method",
                "steps": [
                    f"Write it as a fraction: {fmt_num(part)} "
                    f"out of {fmt_num(whole)} is "
                    f"{fmt_num(part)}/{fmt_num(whole)} = "
                    f"{fmt_num(frac)}",
                    f"Convert the fraction to a percent by "
                    f"multiplying by 100: {fmt_num(frac)} × "
                    f"100 = {fmt_num(pct)}%",
                    _final_line(answer),
                ],
                "answer": answer,
            })
            one = sp.nsimplify(whole / 100, rational=True)
            methods.append({
                "id": "unitary", "label": "Unitary method",
                "steps": [
                    f"1% of {fmt_num(whole)} = "
                    f"{fmt_num(whole)} ÷ 100 = {fmt_num(one)}",
                    f"How many such 1% units make "
                    f"{fmt_num(part)}? {fmt_num(part)} ÷ "
                    f"{fmt_num(one)} = {fmt_num(pct)}",
                    f"So the answer is {fmt_num(pct)}%.",
                    _final_line(answer),
                ],
                "answer": answer,
            })
        return methods
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
    # Wave 53: tolerate a lead-in verb ("Evaluate ...",
    # "Calculate ...", "Find the value of ...") and a trailing
    # full stop — the router's arithmetic primary accepts
    # those, so the alternate should reach them too.
    expr_src = re.sub(
        r"(?i)^\s*(evaluate|calculate|find the value of|"
        r"simplify|find|solve)\b[:\s]*", "", str(working)).strip()
    expr_src = re.sub(r"[.?]\s*$", "", expr_src)
    expr_text = expr_src.replace(" ", "")
    if len(re.findall(r"[+\-*/]", expr_text)) < 1:
        return []
    operators = len(re.findall(r"[+\-*/]", re.sub(r"^-", "", expr_text)))
    if operators < 2 and "(" not in expr_text:
        return []
    try:
        value = parse_expression(expr_src)
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


def _median_position_method(question, primary):
    """Wave 53: the median by the position formula — the
    ((n + 1)/2)th value for odd n, the average of the (n/2)th
    and ((n/2) + 1)th values for even n — instead of the
    primary's arrange-and-pick-the-middle presentation."""
    from .sequences import _ordinal
    from .statistics import _extract_list
    nums = _extract_list(question or "")
    if len(nums) < 3:
        return None
    ordered = sorted(nums)
    n = len(ordered)
    if n % 2 == 1:
        pos = (n + 1) // 2
        val = ordered[pos - 1]
        steps = [
            "Arrange the values in ascending order: "
            + ", ".join(fmt_num(v) for v in ordered),
            f"There are n = {n} values (odd), so by the "
            f"position formula the median is the ((n + 1)/2)th "
            f"value, i.e. the {_ordinal(pos)} value.",
            f"The {_ordinal(pos)} value is {fmt_num(val)}.",
        ]
    else:
        p1, p2 = n // 2, n // 2 + 1
        v1, v2 = ordered[p1 - 1], ordered[p2 - 1]
        val = (v1 + v2) / 2
        steps = [
            "Arrange the values in ascending order: "
            + ", ".join(fmt_num(v) for v in ordered),
            f"There are n = {n} values (even), so by the "
            f"position formula the median is the average of "
            f"the (n/2)th and ((n/2) + 1)th values, i.e. "
            f"the {_ordinal(p1)} and {_ordinal(p2)} values.",
            f"Those values are {fmt_num(v1)} and "
            f"{fmt_num(v2)}, whose average is "
            f"({fmt_num(v1)} + {fmt_num(v2)}) / 2 = "
            f"{fmt_num(val)}.",
        ]
    if primary.get("value") is not None:
        try:
            if abs(float(val) - float(primary["value"])) > 1e-9:
                return None
        except (TypeError, ValueError):
            return None
    elif not _answer_check(fmt_num(val), primary.get("answer")):
        return None
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "position_formula",
            "label": "Position formula method",
            "steps": steps, "answer": primary.get("answer", "")}


# ----------------------------------------------------------------------
# Wave 53 method families — more genuine methods per answer
# (Suraj's pick: "Har sawal ke jawab me aur tarike (methods)
# dikhao", ~100+ patterns). Same honesty rule as Waves 12/13:
# every alternate is computed independently here and ships
# only when its result agrees with the primary answer.
# ----------------------------------------------------------------------
from fractions import Fraction  # noqa: E402

from .algebra import _eq_str, _term_str  # noqa: E402
from .sequences import _DEV_DIGITS_42  # noqa: E402


def _value_close(primary, target, tol=1e-9):
    """True when the primary carries a scalar value close to
    target (or no value at all — caller then checks strings)."""
    v = primary.get("value")
    if v is None:
        return True
    try:
        return abs(float(v) - float(target)) <= tol
    except (TypeError, ValueError):
        return False


def _frac_str(fr):
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


# --- pairs of linear equations ------------------------------------
def _parse_system(working):
    """Extract two linear equations in two unknowns from the
    question text. Returns ((u, v), [(a1, b1, c1), (a2, b2, c2)],
    (xv, yv)) with a*u + b*v = c rows, or None."""
    text = _strip_solve_prefix(str(working).strip())
    _eqpos = text.find("=")
    if _eqpos >= 0:
        _tail = re.split(r"\bfind\b", text[_eqpos:])
        text = text[:_eqpos] + _tail[0]
    parts = [p for p in re.split(r";|,|\band\b", text)
             if "=" in p]
    eqs, syms = [], set()
    for p in parts:
        if ":" in p:
            p = p.rsplit(":", 1)[1]
        p = p.strip().strip(".")
        p = re.sub(r"^(?:if|solve|equations|the|pair|linear"
                   r"|system)\s+", "", p, flags=re.I)
        if "=" not in p:
            continue
        left, right = p.split("=", 1)
        try:
            expr = parse_expression(left) - parse_expression(right)
        except Exception:
            continue
        if not expr.free_symbols or len(expr.free_symbols) > 2:
            continue
        eqs.append(expr)
        syms |= expr.free_symbols
    if len(eqs) != 2 or len(syms) != 2:
        return None
    u, v = sorted(syms, key=lambda s: s.name)
    rows = []
    for e in eqs:
        try:
            poly = sp.Poly(e, u, v)
        except Exception:
            return None
        if poly is None or poly.total_degree() != 1:
            return None
        a = sp.nsimplify(poly.coeff_monomial(u), rational=True)
        b = sp.nsimplify(poly.coeff_monomial(v), rational=True)
        k = sp.nsimplify(poly.coeff_monomial(1), rational=True)
        rows.append((a, b, -k))
    (a1, b1, c1), (a2, b2, c2) = rows
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None
    xv = (c1 * b2 - c2 * b1) / det
    yv = (a1 * c2 - a2 * c1) / det
    return (u, v), rows, (xv, yv)


def _elimination_method(rows, u, v, sol):
    """Worked elimination (the primary either asserted it or
    worked substitution instead). Small fractions are cleared
    first, as in the NCERT examples, so the multiply-to-match
    presentation stays clean."""
    import math as _math
    (a1, b1, c1), (a2, b2, c2) = rows
    xv, yv = sol
    steps = []
    if any(not sp.nsimplify(x, rational=True).is_integer
           for x in (a1, b1, c1, a2, b2, c2)):
        steps.append(
            f"Equations: (1) "
            f"{_eq_str(a1, str(u), b1, str(v))} = {fmt(c1)} and "
            f"(2) {_eq_str(a2, str(u), b2, str(v))} = {fmt(c2)}")
        scaled = []
        notes = []
        for i, row in enumerate(rows):
            L = 1
            for c in row:
                L = sp.ilcm(L, int(sp.denom(
                    sp.nsimplify(c, rational=True))))
            if L > 24:
                return None
            scaled.append(tuple(
                sp.nsimplify(c, rational=True) * L for c in row))
            if L != 1:
                notes.append(f"equation ({i + 1}) by {L}")
        if any(not sp.nsimplify(x, rational=True).is_integer
               for row in scaled for x in row):
            return None
        (a1, b1, c1), (a2, b2, c2) = scaled
        steps.append(
            "Clear the fractions first — multiply "
            + " and ".join(notes) + ":")
    a1, b1, c1, a2, b2, c2 = (int(x) for x in
                              (a1, b1, c1, a2, b2, c2))
    eq1 = f"{_eq_str(a1, str(u), b1, str(v))} = {c1}"
    eq2 = f"{_eq_str(a2, str(u), b2, str(v))} = {c2}"
    steps.append(f"Equations: (1) {eq1} and (2) {eq2}")
    # Eliminate v when both v-coefficients are present, else u.
    if b1 != 0 and b2 != 0:
        tname, oname = v, u
        t1, t2, o1, o2, r1, r2 = b1, b2, a1, a2, c1, c2
    elif a1 != 0 and a2 != 0:
        tname, oname = u, v
        t1, t2, o1, o2, r1, r2 = a1, a2, b1, b2, c1, c2
    else:
        return None
    g = _math.gcd(abs(t1), abs(t2))
    m1, m2 = abs(t2) // g, abs(t1) // g
    T1, T2 = t1 * m1, t2 * m2
    O1, O2, R1, R2 = o1 * m1, o2 * m2, r1 * m1, r2 * m2
    if m1 == 1 and m2 == 1:
        lab1, lab2 = "(1)", "(2)"
        steps.append(
            f"The {tname} coefficients are already equal in "
            f"size ({abs(t1)}), so no multiplication is needed.")
    else:
        lab1, lab2 = "(1')", "(2')"
        _mult = []
        if m1 != 1:
            _mult.append(f"multiply equation (1) by {m1}")
        if m2 != 1:
            _mult.append(f"multiply equation (2) by {m2}")
        steps.append(
            "Make the " + str(tname) + " coefficients equal: "
            + " and ".join(_mult) + ":")
        steps.append(
            f"  {_eq_str(O1, str(oname), T1, str(tname))} = "
            f"{R1} ... (1')")
        steps.append(
            f"  {_eq_str(O2, str(oname), T2, str(tname))} = "
            f"{R2} ... (2')")
    if (T1 > 0) == (T2 > 0):
        O, R = O1 - O2, R1 - R2
        steps.append(
            f"Subtract {lab2} from {lab1} — the {tname} terms "
            f"cancel: {_term_str(O, str(oname))} = {R}")
    else:
        O, R = O1 + O2, R1 + R2
        steps.append(
            f"Add {lab1} and {lab2} — the {tname} terms "
            f"cancel: {_term_str(O, str(oname))} = {R}")
    if O == 0:
        return None
    oval = sp.Rational(R, O)
    steps.append(f"So {oname} = {R} / {O} = {fmt(oval)}")
    # Back-substitute into equation (1).
    if oname == u:
        known, target, kc, tc, rc = xv, v, a1, b1, c1
    else:
        known, target, kc, tc, rc = yv, u, b1, a1, c1
    if tc == 0:
        if oname == u:
            known, target, kc, tc, rc = xv, v, a2, b2, c2
        else:
            known, target, kc, tc, rc = yv, u, b2, a2, c2
    prod = kc * int(known) if float(known) == int(known) \
        else kc * known
    prod = sp.nsimplify(prod, rational=True)
    rest = sp.nsimplify(rc - prod, rational=True)
    steps.append(
        f"Put {oname} = {fmt(known)} in equation (1): "
        f"{fmt(prod)} + {_term_str(tc, str(target))} = {rc}, "
        f"so {_term_str(tc, str(target))} = {fmt(rest)} and "
        f"{target} = {fmt(sp.nsimplify(rest / tc, rational=True))}")
    steps.append(_final_line(
        f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"))
    return {"id": "elimination", "label": "Elimination method",
            "steps": steps,
            "answer": f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"}


def _substitution_method(rows, u, v, sol):
    """Worked substitution: isolate one variable (a unit
    coefficient when there is one), substitute, solve, put
    back."""
    (a1, b1, c1), (a2, b2, c2) = rows
    xv, yv = sol
    # (eq index, var, its coeff, other var, other coeff, rhs)
    cands = [(0, v, b1, u, a1, c1), (0, u, a1, v, b1, c1),
             (1, v, b2, u, a2, c2), (1, u, a2, v, b2, c2)]
    pick = None
    for cand in cands:
        if abs(cand[2]) == 1:
            pick = cand
            break
    if pick is None:
        pick = cands[0]
    ei, var, vc, ovar, oc, rhs = pick
    if vc == 0:
        return None
    expr = (rhs - oc * ovar) / vc
    oj = 1 - ei
    oa, ob, oc2 = rows[oj]
    ocoef = oa if ovar == u else ob
    vcoef = oa if var == u else ob
    steps = [
        f"From equation ({ei + 1}): {var} = {fmt(expr)}",
        f"Put this value of {var} in equation ({oj + 1}): "
        f"{fmt(ocoef * ovar + vcoef * expr)} = {fmt(oc2)}",
    ]
    expanded = sp.expand(ocoef * ovar + vcoef * expr)
    if expanded != ocoef * ovar + vcoef * expr:
        steps.append(f"Simplify: {fmt(expanded)} = {fmt(oc2)}")
    oval = xv if ovar == u else yv
    steps.append(f"Solve for {ovar}: {ovar} = {fmt(oval)}")
    varval = xv if var == u else yv
    steps.append(
        f"Put {ovar} = {fmt(oval)} back in {var} = "
        f"{fmt(expr)}: {var} = {fmt(sp.simplify(expr.subs(ovar, oval)))}")
    if fmt(sp.simplify(expr.subs(ovar, oval))) != fmt(varval):
        return None
    steps.append(_final_line(
        f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"))
    return {"id": "substitution", "label": "Substitution method",
            "steps": steps,
            "answer": f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"}


def _cross_mult_method(rows, u, v, sol):
    """Cross-multiplication formula for a pair of equations."""
    (a1, b1, c1), (a2, b2, c2) = rows
    xv, yv = sol
    k1, k2 = -c1, -c2  # a*x + b*y + k = 0 form

    def lhs0(a, b, k):
        s = _eq_str(a, str(u), b, str(v))
        if k > 0:
            s += f" + {fmt(k)}"
        elif k < 0:
            s += f" - {fmt(-k)}"
        return s + " = 0"

    det = a1 * b2 - a2 * b1
    dx = b1 * k2 - b2 * k1
    dy = k1 * a2 - k2 * a1
    if det == 0 or dx / det != xv or dy / det != yv:
        return None
    steps = [
        "Write both equations in the form a·x + b·y + c = 0:",
        f"  {lhs0(a1, b1, k1)}",
        f"  {lhs0(a2, b2, k2)}",
        f"Cross-multiplication: {u} / (b1·c2 - b2·c1) = "
        f"{v} / (c1·a2 - c2·a1) = 1 / (a1·b2 - a2·b1)",
        f"Here: {u} / {fmt(dx)} = {v} / {fmt(dy)} = "
        f"1 / {fmt(det)}",
        f"So {u} = {fmt(dx)} / {fmt(det)} = {fmt(xv)} and "
        f"{v} = {fmt(dy)} / {fmt(det)} = {fmt(yv)}",
        _final_line(f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"),
    ]
    return {"id": "cross_multiplication",
            "label": "Cross-multiplication method",
            "steps": steps,
            "answer": f"{u} = {fmt(xv)}, {v} = {fmt(yv)}"}


def _system_methods(working, primary):
    parsed = _parse_system(working)
    if parsed is None:
        return []
    (u, v), rows, sol = parsed
    xv, yv = sol
    stated = dict(re.findall(r"([a-z])\s*=\s*(-?[\d.]+(?:/\d+)?)",
                             primary.get("answer", "")))
    if stated.get(str(u)) != fmt(xv) or \
            stated.get(str(v)) != fmt(yv):
        return []
    steps_text = " ".join(primary.get("steps") or [])
    out = []
    if "Substitute into equation" in steps_text:
        em = _elimination_method(rows, u, v, sol)
        if em:
            out.append(em)
    else:
        sm = _substitution_method(rows, u, v, sol)
        if sm:
            out.append(sm)
    cm = _cross_mult_method(rows, u, v, sol)
    if cm:
        out.append(cm)
    # The method dicts carry the system's own answer string;
    # swap in the primary's exact answer for the final line
    # consistency the dispatcher checks.
    for m in out:
        m["answer"] = primary.get("answer", "")
        m["steps"] = [s if not s.startswith("Answer:") else
                      _final_line(primary.get("answer", ""))
                      for s in m["steps"]]
    return out


# --- sequences: AP sum pairing / GP sum by adding ------------------
def _seq_n(working):
    m = re.search(r"first\s+(\d+)\s+terms", working) \
        or re.search(r"(\d+)\s+terms", working) \
        or re.search(r"पहले\s*(\d+)\s*पद", working) \
        or re.search(r"(\d+)\s*पदों\s*का\s*योग", working)
    return int(m.group(1)) if m else None


def _ap_sum_pairing_method(working, primary):
    """Gauss pairing for the sum of an AP: pair the first and
    last terms; every pair has the same total."""
    from .sequences import _classify, _get_params, _parse_series
    text = str(working).translate(_DEV_DIGITS_42)
    terms = _parse_series(text)
    kind, d = _classify(terms) if terms else (None, None)
    n = _seq_n(text)
    a = None
    if kind == "AP" and terms:
        a = terms[0]
    if a is None or d is None or n is None:
        params = _get_params(text.lower())
        if "a" in params and "d" in params and "n" in params:
            a, d, n = params["a"], params["d"], int(params["n"])
        else:
            # Verbal form: "first term is 5 and common
            # difference is 3" (with n from _seq_n above).
            ma = re.search(r"first\s+term\s*(?:is|=)\s*"
                           r"(-?\d+(?:\.\d+)?)", text, re.I)
            md = re.search(r"common\s+difference\s*(?:is|=)\s*"
                           r"(-?\d+(?:\.\d+)?)", text, re.I)
            if ma and md and n is not None:
                a, d = float(ma.group(1)), float(md.group(1))
            else:
                return None
    if n < 2 or n > 10000:
        return None
    a_f, d_f = Fraction(str(a)), Fraction(str(d))
    last = a_f + (n - 1) * d_f
    total = Fraction(n) * (a_f + last) / 2
    if not _value_close(primary, float(total), tol=1e-6):
        return None
    if primary.get("value") is None and not _answer_check(
            fmt_num(total), primary.get("answer")):
        return None
    steps = [
        f"First find the last term: l = a + (n - 1)d = "
        f"{fmt_num(a_f)} + {n - 1} × {fmt_num(d_f)} = "
        f"{fmt_num(last)}",
        "Pairing method (Gauss): write the sum forwards and "
        "backwards — the first + last, second + second-last, "
        "and every such pair adds to the same total "
        f"a + l = {fmt_num(a_f + last)}.",
        f"There are {n} terms, so 2S = {n} × "
        f"{fmt_num(a_f + last)} = {fmt_num(n * (a_f + last))}",
        f"S = {fmt_num(n * (a_f + last))} / 2 = "
        f"{fmt_num(total)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "pairing", "label": "Pairing method",
            "steps": steps, "answer": primary.get("answer", "")}


def _gp_sum_addition_method(working, primary):
    """GP sum by writing out every term and adding (small n)."""
    from .sequences import _classify, _get_params, _parse_series
    text = str(working).translate(_DEV_DIGITS_42)
    terms = _parse_series(text)
    kind, r = _classify(terms) if terms else (None, None)
    n = _seq_n(text)
    a = None
    if kind == "GP" and terms:
        a = terms[0]
    if a is None or r is None or n is None:
        params = _get_params(text.lower())
        if "a" in params and "r" in params and "n" in params:
            a, r, n = params["a"], params["r"], int(params["n"])
        else:
            return None
    if n < 2 or n > 10:
        return None
    a_f, r_f = Fraction(str(a)), Fraction(str(r))
    seq = [a_f * r_f ** i for i in range(n)]
    if any(abs(t) > 10 ** 9 for t in seq):
        return None
    total = sum(seq)
    if not _value_close(primary, float(total), tol=1e-6):
        return None
    if primary.get("value") is None and not _answer_check(
            fmt_num(total), primary.get("answer")):
        return None
    steps = [
        "Write out all the terms of the GP:",
        ", ".join(fmt_num(t) for t in seq),
        "Add them one by one: "
        + " + ".join(fmt_num(t) for t in seq)
        + f" = {fmt_num(total)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "term_addition", "label": "Adding the terms",
            "steps": steps, "answer": primary.get("answer", "")}


# --- applied: CI year-by-year ---------------------------------------
_CI_RE_53 = re.compile(
    r"compound\s+interest\s+on\s+(?:rs\.?\s*|₹\s*|rupees\s*)?"
    r"(\d+(?:\.\d+)?)\s+at\s+(\d+(?:\.\d+)?)\s*%\s*(?:per\s+"
    r"annum\s+)?(?:for\s+)?(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
    re.I)


def _ci_yearly_method(working, primary):
    """Compound interest year by year: each year's interest
    is simple interest on the amount at its start."""
    m = _CI_RE_53.search(working or "")
    if not m:
        return None
    P = sp.Rational(m.group(1))
    R = sp.Rational(m.group(2))
    T = sp.Rational(m.group(3))
    if T != int(T) or not (2 <= int(T) <= 5):
        return None
    steps = [
        "Work year by year: in compound interest, each "
        "year's interest is calculated on the amount at the "
        "start of that year (not just on the original "
        "principal).",
    ]
    bal = P
    for year in range(1, int(T) + 1):
        interest = bal * R / 100
        new = bal + interest
        steps.append(
            f"Year {year}: interest = {fmt_num(bal)} × "
            f"{fmt_num(R)} / 100 = {fmt_num(interest)}; "
            f"amount = {fmt_num(bal)} + {fmt_num(interest)} "
            f"= {fmt_num(new)}")
        bal = new
    ci = bal - P
    if not _value_close(primary, float(ci), tol=1e-6):
        return None
    if not _answer_check(fmt_num(ci), primary.get("answer")):
        return None
    steps.append(
        f"Compound interest = final amount - principal = "
        f"{fmt_num(bal)} - {fmt_num(P)} = {fmt_num(ci)}")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "yearly_breakup", "label": "Year-by-year method",
            "steps": steps, "answer": primary.get("answer", "")}


def _pl_percent_unitary_method(working, primary):
    """Profit/loss percent by the unitary route: find the
    profit or loss on a cost price of Rs 100."""
    cp = sp_ = None
    for s in primary.get("steps") or []:
        m = re.search(r"Cost price \(CP\) = Rs ([\d.]+), "
                      r"selling price \(SP\) = Rs ([\d.]+)", s)
        if m:
            cp, sp_ = float(m.group(1)), float(m.group(2))
            break
    if cp is None:
        m = re.search(r"\bcp\s*(?:is|=)?\s*(?:rs\.?\s*)?(\d+(?:\.\d+)?)"
                      r"[\s\S]{0,20}?\bsp\s*(?:is|=)?\s*"
                      r"(?:rs\.?\s*)?(\d+(?:\.\d+)?)",
                      working or "", re.I)
        if m:
            cp, sp_ = float(m.group(1)), float(m.group(2))
    if not cp:
        return None
    diff = sp_ - cp
    if diff == 0:
        return None
    kind = "Profit" if diff > 0 else "Loss"
    per100 = abs(diff) * 100.0 / cp
    if not _value_close(primary, per100, tol=1e-6):
        return None
    steps = [
        f"{kind} = Rs {fmt_num(abs(diff))} on a cost price "
        f"of Rs {fmt_num(cp)}.",
        f"Unitary method: scale the cost price to Rs 100 — "
        f"the {kind.lower()} on Rs 100 is "
        f"{fmt_num(abs(diff))} × 100 / {fmt_num(cp)} = "
        f"{fmt_num(per100)}.",
        f"But 'percent' means 'per hundred', so this is "
        f"already the {kind.lower()} percent: "
        f"{fmt_num(per100)}%",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "unitary", "label": "Unitary method",
            "steps": steps, "answer": primary.get("answer", "")}


def _reverse_pl_unitary_method(working, primary):
    """Cost price from SP + profit/loss % by the unitary
    route: an article with CP Rs 100 sells for Rs (100 ± p)."""
    kind = p = sp_ = None
    for s in primary.get("steps") or []:
        m = re.search(r"With a (profit|loss) of ([\d.]+)%", s)
        if m:
            kind, p = m.group(1), float(m.group(2))
        m2 = re.search(r"CP = ([\d.]+) ÷", s)
        if m2:
            sp_ = float(m2.group(1))
    if kind is None or sp_ is None:
        m = re.search(r"\b(profit|loss)\s+of\s+([\d.]+)\s*%",
                      working or "", re.I)
        m2 = re.search(r"sold\s+(?:at|for)\s+(?:rs\.?\s*)?"
                       r"([\d.]+)", working or "", re.I)
        if m and m2:
            kind, p, sp_ = m.group(1), float(m.group(2)), \
                float(m2.group(1))
    if kind is None or not sp_:
        return None
    eff = 100.0 + p if kind == "profit" else 100.0 - p
    if eff <= 0:
        return None
    cp = sp_ * 100.0 / eff
    if not _value_close(primary, cp, tol=0.01):
        return None
    steps = [
        f"Unitary method: take the cost price as Rs 100. "
        f"With a {kind} of {fmt_num(p)}%, such an article "
        f"sells for Rs 100 {'+' if kind == 'profit' else '-'} "
        f"{fmt_num(p)} = Rs {fmt_num(eff)}.",
        f"So a selling price of Rs {fmt_num(eff)} means a "
        f"cost price of Rs 100.",
        f"For the actual selling price Rs {fmt_num(sp_)}: "
        f"CP = {fmt_num(sp_)} × 100 / {fmt_num(eff)} = "
        f"Rs {fmt_num(cp)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "unitary", "label": "Unitary method",
            "steps": steps, "answer": primary.get("answer", "")}


def _discount_direct_method(working, primary):
    """Discount: pay (100 - d)% of the marked price directly,
    instead of subtracting the discount amount."""
    q = working or ""
    md = re.search(r"discount\s+of\s+(\d+(?:\.\d+)?)\s*%", q, re.I) \
        or re.search(r"(\d+(?:\.\d+)?)\s*%\s+discount", q, re.I)
    mm = re.search(r"marked\s+price\s+(?:is\s+)?(?:rs\.?\s*)?"
                   r"(\d+(?:\.\d+)?)", q, re.I) or re.search(
        r"discount\s+of\s+\d+(?:\.\d+)?\s*%\s+on\s+"
        r"[\w\s]{0,24}?(?:rs\.?\s*)?(\d+(?:\.\d+)?)", q, re.I)
    if not (md and mm):
        return None
    d, M = float(md.group(1)), float(mm.group(1))
    if M <= 0 or not (0 <= d < 100):
        return None
    pay = 100.0 - d
    sp_ = M * pay / 100.0
    if not _value_close(primary, sp_, tol=1e-6):
        return None
    steps = [
        f"A discount of {fmt_num(d)}% means you pay "
        f"100 - {fmt_num(d)} = {fmt_num(pay)}% of the marked "
        f"price.",
        f"Selling price = {fmt_num(pay)}% of Rs {fmt_num(M)} "
        f"= {fmt_num(pay)} / 100 × {fmt_num(M)} = "
        f"Rs {fmt_num(sp_)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "direct_percent",
            "label": "Direct percentage method",
            "steps": steps, "answer": primary.get("answer", "")}


def _successive_discount_equiv_method(working, primary):
    """Successive discounts via the single equivalent discount
    D = d1 + d2 - d1*d2/100 (the primary applied the two
    discounts one after the other)."""
    q = working or ""
    pcts = [float(x) for x in re.findall(
        r"(\d+(?:\.\d+)?)\s*%", q)]
    mm = re.search(r"marked\s+price\s+(?:is\s+)?(?:rs\.?\s*)?"
                   r"(\d+(?:\.\d+)?)", q, re.I) or re.search(
        r"marked\s+price[\s\S]{0,40}?(?:rs\.?\s*)"
        r"(\d+(?:\.\d+)?)", q, re.I)
    if not mm:
        for s in (primary.get("steps") or []):
            ms = re.search(r"[Mm]arked\s+price\s*=\s*"
                           r"(?:rs\.?\s*)?(\d+(?:\.\d+)?)",
                           str(s), re.I)
            if ms:
                mm = ms
                break
    if len(pcts) != 2 or not mm:
        return None
    d1, d2 = pcts
    M = float(mm.group(1))
    if M <= 0 or not (0 <= d1 < 100 and 0 <= d2 < 100):
        return None
    D = d1 + d2 - d1 * d2 / 100.0
    sp_ = M * (100.0 - D) / 100.0
    if not _value_close(primary, sp_, tol=0.01):
        return None
    steps = [
        f"Equivalent discount method: two successive discounts "
        f"of {fmt_num(d1)}% and {fmt_num(d2)}% equal one "
        f"single discount of D = d1 + d2 - (d1 × d2) / 100.",
        f"D = {fmt_num(d1)} + {fmt_num(d2)} - "
        f"({fmt_num(d1)} × {fmt_num(d2)}) / 100 = "
        f"{fmt_num(D)}%",
        f"Selling price = Rs {fmt_num(M)} × (1 - "
        f"{fmt_num(D)} / 100) = Rs {fmt_num(M)} × "
        f"{fmt_num((100.0 - D) / 100.0)} = Rs {fmt_num(sp_)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "equivalent_discount",
            "label": "Single equivalent discount",
            "steps": steps, "answer": primary.get("answer", "")}


def _percent_score_unitary_method(working, primary):
    """Marks percentage by the unitary route: one mark is
    worth 100/total percent."""
    m = re.search(r"(\d+(?:\.\d+)?)\s+(?:marks\s+)?out\s+of\s+"
                  r"(\d+(?:\.\d+)?)", working or "")
    if not m:
        return None
    part, whole = float(m.group(1)), float(m.group(2))
    if whole == 0:
        return None
    pct = part * 100.0 / whole
    if not _value_close(primary, pct, tol=1e-6):
        return None
    steps = [
        f"Unitary method: the full {fmt_num(whole)} marks "
        f"stand for 100%, so 1 mark stands for "
        f"100 / {fmt_num(whole)} percent.",
        f"{fmt_num(part)} marks = {fmt_num(part)} × 100 / "
        f"{fmt_num(whole)} = {fmt_num(pct)}%",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "unitary", "label": "Unitary method",
            "steps": steps, "answer": primary.get("answer", "")}


def _unitary_cost_proportion_method(working, primary):
    """Cost-of-many by proportion (the primary used the
    unitary route): total cost scales in direct proportion."""
    q = working or ""
    m = re.search(
        r"\b(\d+(?:\.\d+)?)\s+[\w]+\s+(?:cost|price)\s+"
        r"(?:is\s+)?(?:rs\.?\s*)?(\d+(?:\.\d+)?)\b"
        r"[\s\S]{0,40}?\b(?:cost|price)\s+of\s+"
        r"(\d+(?:\.\d+)?)\b", q, re.I) or re.search(
        r"\bcost\s+of\s+(\d+(?:\.\d+)?)\s+[\w]+\s+(?:is\s+)?"
        r"(?:rs\.?\s*)?(\d+(?:\.\d+)?)\b[\s\S]{0,40}?"
        r"\bcost\s+of\s+(\d+(?:\.\d+)?)\b", q, re.I)
    if not m:
        return None
    n1, total, n2 = (float(m.group(i)) for i in (1, 2, 3))
    if n1 == 0:
        return None
    ans = total * n2 / n1
    if not _value_close(primary, ans, tol=1e-6):
        return None
    steps = [
        "Proportion method: the cost grows in direct "
        "proportion to the number of items.",
        f"{fmt_num(n1)} items : Rs {fmt_num(total)} = "
        f"{fmt_num(n2)} items : Rs x",
        f"Cross-multiply: x = {fmt_num(total)} × "
        f"{fmt_num(n2)} / {fmt_num(n1)} = Rs {fmt_num(ans)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "proportion", "label": "Proportion method",
            "steps": steps, "answer": primary.get("answer", "")}


def _ratio_fraction_method(working, primary):
    """Dividing an amount in a ratio by taking fractions of
    the whole (the primary used value-of-one-part)."""
    q = working or ""
    mt = re.search(r"(?:rs\.?\s*|₹\s*)(\d+(?:\.\d+)?)", q, re.I)
    mr = re.search(r"(\d+)\s*:\s*(\d+)", q)
    if not (mt and mr):
        return None
    total = float(mt.group(1))
    a, b = int(mr.group(1)), int(mr.group(2))
    if a <= 0 or b <= 0 or total <= 0:
        return None
    s1 = total * a / (a + b)
    s2 = total * b / (a + b)
    vals = primary.get("value")
    if isinstance(vals, (list, tuple)) and len(vals) == 2:
        if abs(float(vals[0]) - s1) > 1e-6 or \
                abs(float(vals[1]) - s2) > 1e-6:
            return None
    elif not (_answer_check(fmt_num(s1), primary.get("answer"))
              and _answer_check(fmt_num(s2),
                                primary.get("answer"))):
        return None
    steps = [
        f"The ratio {a} : {b} has {a} + {b} = {a + b} parts, "
        f"so the first share is {a}/{a + b} of the whole "
        f"amount and the second is {b}/{a + b}.",
        f"First share = {a}/{a + b} × {fmt_num(total)} = "
        f"Rs {fmt_num(s1)}",
        f"Second share = {b}/{a + b} × {fmt_num(total)} = "
        f"Rs {fmt_num(s2)}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "fraction_of_whole",
            "label": "Fraction of the whole method",
            "steps": steps, "answer": primary.get("answer", "")}


# --- number theory: LCM division / HCF+LCM relation -----------------
def _lcm_division_method(working, primary):
    """LCM by the common-division method (the primary used
    prime factorisation): divide the row by a prime that
    divides at least two of the numbers, repeat, multiply."""
    import math as _math
    nums = [int(v) for v in re.findall(r"\d+", working or "")]
    if not (2 <= len(nums) <= 4) or any(n <= 1 for n in nums):
        return None
    if any(n > 100000 for n in nums):
        return None
    cur = list(nums)
    divisors, rows = [], [list(cur)]

    def smallest_common_prime(vals):
        p = 2
        while p * p <= max(vals) or p <= max(vals):
            if sum(1 for x in vals if x % p == 0) >= 2:
                return p
            p += 1 if p == 2 else 2
            if p > max(vals):
                return None
        return None

    while len(divisors) < 40:
        p = smallest_common_prime(cur)
        if p is None:
            break
        divisors.append(p)
        cur = [x // p if x % p == 0 else x for x in cur]
        rows.append(list(cur))
    if not divisors:
        return None
    val = 1
    for d in divisors:
        val *= d
    for x in cur:
        val *= x
    if _math.lcm(*nums) != val:
        return None
    if not _value_close(primary, val):
        return None
    if primary.get("value") is None and not _answer_check(
            str(val), primary.get("answer")):
        return None
    steps = [
        "Division method: divide the whole row by a prime "
        "that divides at least two of the numbers; a number "
        "that does not divide comes down unchanged.",
    ]
    for i, p in enumerate(divisors):
        steps.append(
            f"  ÷ {p}: "
            + ", ".join(str(x) for x in rows[i])
            + "  →  "
            + ", ".join(str(x) for x in rows[i + 1]))
    tail = [x for x in cur if x != 1]
    factors = [str(d) for d in divisors] + [str(x) for x in tail]
    steps.append(
        "Multiply all the divisors and the numbers left in "
        "the last row: " + " × ".join(factors) + f" = {val}")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "division_method", "label": "Division method",
            "steps": steps, "answer": primary.get("answer", "")}


def _hcf_lcm_relation_method(working, primary):
    """HCF by Euclid, then LCM from a × b = HCF × LCM (the
    primary used prime factorisation for both)."""
    import math as _math
    nums = [int(v) for v in re.findall(r"\d+", working or "")]
    if len(nums) != 2 or any(n <= 0 for n in nums):
        return None
    a, b = nums
    steps = [
        "First find the HCF by Euclid's division method:",
    ]
    x, y = max(a, b), min(a, b)
    while y:
        steps.append(f"  {x} ÷ {y} = {x // y} remainder {x % y}")
        x, y = y, x % y
    h = x
    lcm = a * b // h
    vals = primary.get("value")
    if isinstance(vals, (list, tuple)) and len(vals) == 2:
        if int(vals[0]) != h or int(vals[1]) != lcm:
            return None
    elif not (_answer_check(str(h), primary.get("answer"))
              and _answer_check(str(lcm), primary.get("answer"))):
        return None
    steps.append(f"So HCF = {h}.")
    steps.append(
        f"For two numbers: first × second = HCF × LCM, so "
        f"LCM = {a} × {b} / {h} = {a * b} / {h} = {lcm}")
    steps.append(
        f"Check: {a} × {b} = {a * b} and {h} × {lcm} = "
        f"{h * lcm} — equal ✓")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "euclid_relation",
            "label": "Using Euclid and the product relation",
            "steps": steps, "answer": primary.get("answer", "")}


# --- probability: the complement rule --------------------------------
def _prob_agrees(frac, primary):
    v = primary.get("value")
    if v is None:
        return False
    try:
        return abs(float(frac) - float(v)) < 1e-9
    except (TypeError, ValueError):
        return False


def _complement_steps(event_name, opp_desc, opp_frac, frac,
                      answer):
    return [
        "Complement rule: P(event) = 1 - P(opposite event).",
        f"The opposite of {event_name} is {opp_desc}: its "
        f"probability is {_frac_str(opp_frac)}.",
        f"So P({event_name}) = 1 - {_frac_str(opp_frac)} = "
        f"{_frac_str(frac)}.",
        _final_line(answer),
    ]


def _die_complement(ql, primary):
    if "die" not in ql and "dice" not in ql:
        return None
    if re.search(r"two\s+(dice|dies)|2\s+(dice|dies)|pair of dice",
                 ql):
        return None
    seg = ql[ql.rfind("probability"):] if "probability" in ql \
        else ql
    neg = bool(re.search(r"\bnot\b", seg))
    base = None
    m = re.search(r"greater than\s+(\d)|more than\s+(\d)", seg)
    if m:
        k = int(m.group(1) or m.group(2))
        base = set(range(k + 1, 7))
    if base is None:
        m = re.search(r"less than\s+(\d)|fewer than\s+(\d)", seg)
        if m:
            k = int(m.group(1) or m.group(2))
            base = set(range(1, k))
    if base is None:
        m = re.search(r"at least\s+(\d)", seg)
        if m:
            base = set(range(int(m.group(1)), 7))
    if base is None:
        m = re.search(r"at most\s+(\d)", seg)
        if m:
            base = set(range(1, int(m.group(1)) + 1))
    if base is None and "even" in seg:
        base = {2, 4, 6}
    if base is None and "odd" in seg:
        base = {1, 3, 5}
    if base is None and "prime" in seg:
        base = {2, 3, 5}
    if base is None and "composite" in seg:
        base = {4, 6}
    if base is None:
        m = re.search(r"(?:getting|get|of)\s+(?:a\s+|an\s+)?"
                      r"(\d)\b", seg) or re.search(
            r"\bnumber\s+(\d)\b", seg)
        if m:
            base = {int(m.group(1))}
    if not base or not all(1 <= x <= 6 for x in base):
        return None
    event = set(range(1, 7)) - base if neg else base
    if not event or len(event) == 6:
        return None
    frac = Fraction(len(event), 6)
    if not _prob_agrees(frac, primary):
        return None
    opp = sorted(set(range(1, 7)) - event)
    opp_frac = Fraction(len(opp), 6)
    steps = _complement_steps(
        "the event",
        "getting one of " + ", ".join(str(x) for x in opp)
        + f" ({len(opp)} of the 6 faces)",
        opp_frac, frac, primary.get("answer", ""))
    steps.insert(1, "A die has 6 equally likely faces: "
                    "1, 2, 3, 4, 5, 6.")
    return {"id": "complement", "label": "Complement method",
            "steps": steps, "answer": primary.get("answer", "")}


def _coin_complement(ql, primary):
    if "coin" not in ql:
        return None
    seg = ql[ql.rfind("probability"):] if "probability" in ql \
        else ql
    neg = bool(re.search(r"\bnot\b", seg))
    if re.search(r"two coins|2 coins|pair of coins", ql):
        outcomes = ["HH", "HT", "TH", "TT"]
        base = None
        if re.search(r"two heads|both heads|2 heads", seg):
            base = {"HH"}
        elif re.search(r"two tails|both tails|2 tails", seg):
            base = {"TT"}
        elif re.search(r"at least one head", seg):
            base = {"HH", "HT", "TH"}
        elif re.search(r"at least one tail", seg):
            base = {"HT", "TH", "TT"}
        elif re.search(r"exactly one head|one head and one "
                       r"tail|one head one tail", seg):
            base = {"HT", "TH"}
        elif re.search(r"exactly one tail", seg):
            base = {"HT", "TH"}
        elif re.search(r"no head", seg):
            base = {"TT"}
        elif re.search(r"no tail", seg):
            base = {"HH"}
        if not base:
            return None
        event = set(outcomes) - base if neg else base
        if not event or len(event) == 4:
            return None
        frac = Fraction(len(event), 4)
        if not _prob_agrees(frac, primary):
            return None
        opp = [o for o in outcomes if o not in event]
        steps = [
            "Two coins give 4 equally likely outcomes: "
            "HH, HT, TH, TT.",
        ] + _complement_steps(
            "the event",
            "getting " + ", ".join(opp)
            + f" ({len(opp)} of the 4 outcomes)",
            Fraction(len(opp), 4), frac,
            primary.get("answer", ""))
        return {"id": "complement", "label": "Complement method",
                "steps": steps,
                "answer": primary.get("answer", "")}
    if re.search(r"three coins|3 coins", ql):
        return None
    base = None
    if re.search(r"\bhead", seg):
        base = {"H"}
    elif re.search(r"\btail", seg):
        base = {"T"}
    if not base:
        return None
    event = {"H", "T"} - base if neg else base
    frac = Fraction(len(event), 2)
    if not _prob_agrees(frac, primary):
        return None
    opp = sorted({"H", "T"} - event)
    name = {"H": "a head", "T": "a tail"}
    steps = _complement_steps(
        "the event",
        f"getting {name[opp[0]]} (1 of the 2 outcomes, "
        f"probability 1/2)",
        Fraction(1, 2), frac, primary.get("answer", ""))
    steps.insert(1, "One coin has 2 equally likely outcomes: "
                    "head and tail.")
    return {"id": "complement", "label": "Complement method",
            "steps": steps, "answer": primary.get("answer", "")}


_BALL_RE_53 = re.compile(
    r"(\d+)\s+(red|blue|green|yellow|black|white|orange|pink"
    r"|purple|brown|grey|gray)\b")


def _balls_complement(ql, primary):
    counts = {}
    for n, colour in _BALL_RE_53.findall(ql):
        counts[colour] = counts.get(colour, 0) + int(n)
    if len(counts) < 2:
        return None
    total = sum(counts.values())
    if total < 2:
        return None
    seg = ql[ql.rfind("probability"):] if "probability" in ql \
        else ql
    neg = bool(re.search(r"\bnot\b", seg))
    m = re.search(
        r"(?:a\s+|an\s+)?"
        r"(red|blue|green|yellow|black|white|orange|pink"
        r"|purple|brown|grey|gray)\b", seg)
    if not m:
        return None
    colour = m.group(1)
    if colour not in counts:
        return None
    fav = total - counts[colour] if neg else counts[colour]
    frac = Fraction(fav, total)
    if not _prob_agrees(frac, primary):
        return None
    answer = primary.get("answer", "")
    if neg:
        steps = [
            f"The bag has {total} balls in all, of which "
            f"{counts[colour]} are {colour}.",
            f"First find P({colour}) = {counts[colour]}/"
            f"{total} = {_frac_str(Fraction(counts[colour], total))}.",
            f"The asked event is the complement: P(not "
            f"{colour}) = 1 - "
            f"{_frac_str(Fraction(counts[colour], total))} = "
            f"{_frac_str(frac)}.",
            _final_line(answer),
        ]
    else:
        others = [(c, n) for c, n in counts.items()
                  if c != colour]
        opp = total - counts[colour]
        steps = [
            f"The bag has {total} balls in all. The balls "
            f"that are NOT {colour} are "
            + ", ".join(f"{n} {c}" for c, n in others)
            + f" — {opp} in total.",
            f"P(not {colour}) = {opp}/{total} = "
            f"{_frac_str(Fraction(opp, total))}.",
            f"Complement rule: P({colour}) = 1 - "
            f"{_frac_str(Fraction(opp, total))} = "
            f"{_frac_str(frac)}.",
            _final_line(answer),
        ]
    return {"id": "complement", "label": "Complement method",
            "steps": steps, "answer": answer}


_CARD_TABLE_53 = [
    ("face card", 12), ("red", 26), ("black", 26),
    ("heart", 13), ("diamond", 13), ("club", 13),
    ("spade", 13), ("king", 4), ("queen", 4), ("jack", 4),
    ("ace", 4),
]


def _cards_complement(ql, primary):
    if "card" not in ql or "52" not in ql:
        return None
    seg = ql[ql.rfind("probability"):] if "probability" in ql \
        else ql
    hit = None
    for name, n in _CARD_TABLE_53:
        if name in seg:
            hit = (name, n)
            break
    if hit is None:
        return None
    name, n = hit
    neg = bool(re.search(r"\bnot\b", seg))
    fav = 52 - n if neg else n
    frac = Fraction(fav, 52)
    if not _prob_agrees(frac, primary):
        return None
    answer = primary.get("answer", "")
    if neg:
        steps = [
            f"A pack has 52 cards, of which {n} are "
            f"'{name}'.",
            f"P({name}) = {n}/52 = "
            f"{_frac_str(Fraction(n, 52))}.",
            f"The asked event is the complement: "
            f"P(not {name}) = 1 - "
            f"{_frac_str(Fraction(n, 52))} = "
            f"{_frac_str(frac)}.",
            _final_line(answer),
        ]
    else:
        steps = [
            f"A pack has 52 cards. The cards that are NOT "
            f"'{name}' number 52 - {n} = {52 - n}.",
            f"P(not {name}) = {52 - n}/52 = "
            f"{_frac_str(Fraction(52 - n, 52))}.",
            f"Complement rule: P({name}) = 1 - "
            f"{_frac_str(Fraction(52 - n, 52))} = "
            f"{_frac_str(frac)}.",
            _final_line(answer),
        ]
    return {"id": "complement", "label": "Complement method",
            "steps": steps, "answer": answer}


def _probability_complement_method(working, primary):
    """The complement rule P(E) = 1 - P(not E) for the
    standard die / coin / balls / cards questions (the
    primary counts the favourable outcomes directly)."""
    ql = (working or "").lower()
    if primary.get("value") is None:
        return None
    for fn in (_die_complement, _coin_complement,
               _balls_complement, _cards_complement):
        try:
            out = fn(ql, primary)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


# --- trigonometry: identity route / standard triangles ---------------
def _trig_identity_method(working, primary):
    """Given one ratio, find the others from the identities
    sin^2 + cos^2 = 1 and sec^2 = 1 + tan^2 (the primary
    builds a right triangle and uses Pythagoras)."""
    m = re.search(r"\b(sin|cos|tan)\s+([A-Za-z])\s*=\s*"
                  r"(\d+)\s*/\s*(\d+)", working or "")
    if not m:
        return None
    fn, ang = m.group(1), m.group(2)
    val = sp.Rational(int(m.group(3)), int(m.group(4)))
    if val <= 0 or (fn in ("sin", "cos") and val > 1):
        return None
    asked = re.findall(r"(sin|cos|tan)\s+" + re.escape(ang)
                       + r"\s*=\s*([^,]+)",
                       primary.get("answer", ""))
    asked = [(f, s.strip()) for f, s in asked if f != fn]
    if not asked:
        return None
    if fn == "sin":
        s = val
        c = sp.sqrt(1 - s ** 2)
        t = s / c
        steps = [
            "Use the identity sin^2 " + ang + " + cos^2 "
            + ang + " = 1, which holds for every angle.",
            f"cos^2 {ang} = 1 - sin^2 {ang} = 1 - "
            f"({fmt(val)})^2 = 1 - {fmt(val ** 2)} = "
            f"{fmt(c ** 2)}",
            f"cos {ang} = sqrt({fmt(c ** 2)}) = {fmt(c)} "
            f"(positive, as {ang} is acute).",
        ]
        if any(f == "tan" for f, _ in asked):
            steps.append(
                f"tan {ang} = sin {ang} / cos {ang} = "
                f"{fmt(s)} / {fmt(c)} = {fmt(t)}")
    elif fn == "cos":
        c = val
        s = sp.sqrt(1 - c ** 2)
        t = s / c
        steps = [
            "Use the identity sin^2 " + ang + " + cos^2 "
            + ang + " = 1, which holds for every angle.",
            f"sin^2 {ang} = 1 - cos^2 {ang} = 1 - "
            f"({fmt(val)})^2 = 1 - {fmt(val ** 2)} = "
            f"{fmt(s ** 2)}",
            f"sin {ang} = sqrt({fmt(s ** 2)}) = {fmt(s)} "
            f"(positive, as {ang} is acute).",
        ]
        if any(f == "tan" for f, _ in asked):
            steps.append(
                f"tan {ang} = sin {ang} / cos {ang} = "
                f"{fmt(s)} / {fmt(c)} = {fmt(t)}")
    else:
        t = val
        c = 1 / sp.sqrt(1 + t ** 2)
        s = t * c
        steps = [
            "Use the identity sec^2 " + ang + " = 1 + tan^2 "
            + ang + ".",
            f"sec^2 {ang} = 1 + ({fmt(t)})^2 = "
            f"{fmt(1 + t ** 2)}, so sec {ang} = "
            f"{fmt(1 / c)} and cos {ang} = 1 / sec {ang} = "
            f"{fmt(c)}.",
            f"sin {ang} = tan {ang} × cos {ang} = "
            f"{fmt(t)} × {fmt(c)} = {fmt(s)}.",
        ]
    vals = {"sin": s, "cos": c, "tan": t}
    for f, stated in asked:
        if fmt(sp.simplify(vals[f])) != stated:
            return None
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "identity", "label": "Identity method",
            "steps": steps, "answer": primary.get("answer", "")}


_TRIG_TOKEN_53 = re.compile(
    r"(sin|cos|tan|cosec|sec|cot)\s*(?:\^\s*(\d+)\s*)?"
    r"(0|30|45|60|90)\b(?:\s*°)?")


def _std_trig(fn, ang):
    x = sp.pi * ang / 180
    base = {"sin": sp.sin(x), "cos": sp.cos(x), "tan": sp.tan(x)}
    if fn in base:
        return base[fn]
    if fn == "cosec":
        return 1 / sp.sin(x)
    if fn == "sec":
        return 1 / sp.cos(x)
    return 1 / sp.tan(x)


def _trig_triangle_method(working, primary):
    """Standard-angle values derived from the two standard
    triangles (the primary quotes the table): the 30-60-90
    half-equilateral triangle and the 45-45-90 isosceles
    right triangle."""
    if primary.get("value") is None:
        return None
    text = str(working or "")
    body = re.sub(r"(?i)find the value of|evaluate|find|"
                  r"value of|calculate", "", text)
    body = re.sub(r"(?i)\bdegrees?\b", "", body)
    body = re.sub(r"\.\s*$", "", body)
    matches = list(_TRIG_TOKEN_53.finditer(body))
    if not matches:
        return None
    pieces, gaps, last = [], [], 0
    for m in matches:
        fn, power, ang = m.group(1), m.group(2), int(m.group(3))
        val = _std_trig(fn, ang)
        piece = f"({fmt(val)})"
        if power:
            piece = f"({fmt(val)})^{power}"
        gaps.append(body[last:m.start()])
        pieces.append(body[last:m.start()])
        pieces.append(piece)
        last = m.end()
    gaps.append(body[last:])
    pieces.append(body[last:])
    # Only the parts BETWEEN the trig tokens are checked: they
    # must be plain arithmetic. The substituted values may
    # legitimately contain "sqrt(...)".
    gap_text = "".join(gaps).replace("×", "*").replace("÷", "/")
    gap_text = gap_text.replace("?", " ")
    if not re.fullmatch(r"[\d\s+\-*/().^]*", gap_text):
        return None
    cleaned = "".join(pieces).replace("×", "*").replace("÷", "/")
    cleaned = cleaned.replace("?", " ").strip()
    try:
        value = parse_expression(cleaned.replace("·", "*"))
    except Exception:
        return None
    if getattr(value, "free_symbols", None) and \
            value.free_symbols:
        return None
    try:
        if abs(float(value.evalf())
               - float(primary["value"])) > 1e-9:
            return None
    except Exception:
        return None
    angles = {int(m.group(3)) for m in matches}
    fns = {m.group(1) for m in matches}
    steps = []
    if 30 in angles:
        steps.append(
            "Derive the 30° values: halve an equilateral "
            "triangle of side 2 — the perpendicular splits "
            "the base into 1 and 1, and the height is "
            "sqrt(2^2 - 1^2) = sqrt(3). So sin 30° = 1/2, "
            "cos 30° = sqrt(3)/2, tan 30° = 1/sqrt(3).")
    if 60 in angles:
        steps.append(
            "The same half-equilateral triangle (side 2, "
            "height sqrt(3)) gives the 60° values: "
            "sin 60° = sqrt(3)/2, cos 60° = 1/2, "
            "tan 60° = sqrt(3).")
    if 45 in angles:
        steps.append(
            "Derive the 45° values: an isosceles right "
            "triangle with legs 1 and 1 has hypotenuse "
            "sqrt(1^2 + 1^2) = sqrt(2). So sin 45° = "
            "cos 45° = 1/sqrt(2) and tan 45° = 1.")
    if angles & {0, 90}:
        steps.append(
            "The end values come from the unit circle: "
            "sin 0° = 0, cos 0° = 1, tan 0° = 0, "
            "sin 90° = 1, cos 90° = 0.")
    if fns & {"cosec", "sec", "cot"}:
        steps.append(
            "Also: cosec = 1/sin, sec = 1/cos, cot = 1/tan.")
    display = cleaned.replace("*", "·")
    steps.append(
        f"Now substitute these values in the expression: "
        f"{display} = {fmt(value)}")
    steps.append(_final_line(primary.get("answer", "")))
    return {"id": "standard_triangles",
            "label": "From the standard triangles",
            "steps": steps, "answer": primary.get("answer", "")}


# --- geometry: diameter / grid / sides / layers -----------------------
def _answer_approx(primary):
    m = re.search(r"≈\s*(-?[\d.]+)", primary.get("answer", ""))
    return float(m.group(1)) if m else None


def _answer_first_num(primary):
    m = re.search(r"-?\d+(?:\.\d+)?", primary.get("answer", ""))
    return float(m.group(0)) if m else None


def _circle_diameter_area_method(working, primary):
    """Circle area through the diameter: A = pi d^2 / 4."""
    ql = (working or "").lower()
    if "circle" not in ql:
        return None
    r = find_param(ql, ["radius"])
    if r is None:
        return None
    approx = _answer_approx(primary)
    if approx is None:
        # Wave 99: a 22/7 primary answer is exact — it carries
        # no "≈" — so verify against its plain value instead.
        approx = _answer_first_num(primary)
    # Wave 99: verify against the policy pi for this radius
    # (22/7 for 7-friendly radii), like the primary does.
    _pi, _u227, _reason = pi_choice(radius=r)
    if approx is None or abs(_pi * r * r - approx) > 0.01:
        return None
    d = 2 * r
    if _u227:
        steps = [
            f"Use the diameter instead: d = 2 × r = 2 × "
            f"{fmt_num(r)} = {fmt_num(d)}.",
            f"Area = pi × d^2 / 4 = (22/7) × "
            f"{fmt_num(d)}^2 / 4 = (22/7) × "
            f"{fmt_num(r * r)} = {fmt_num(_pi * r * r)}",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "diameter", "label": "Using the diameter",
                "steps": steps,
                "answer": primary.get("answer", "")}
    steps = [
        f"Use the diameter instead: d = 2 × r = 2 × "
        f"{fmt_num(r)} = {fmt_num(d)}.",
        f"Area = pi × d^2 / 4 = pi × {fmt_num(d)}^2 / 4 = "
        f"pi × {fmt_num(d * d)} / 4 = {fmt_num(r * r)}·pi "
        f"≈ {_pi * r * r:.4f}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "diameter", "label": "Using the diameter",
            "steps": steps, "answer": primary.get("answer", "")}


def _circle_diameter_circ_method(working, primary):
    """Circumference as pi × diameter (the primary used
    2 pi r)."""
    ql = (working or "").lower()
    if "circle" not in ql:
        return None
    r = find_param(ql, ["radius"])
    if r is None:
        return None
    approx = _answer_approx(primary)
    if approx is None:
        approx = _answer_first_num(primary)
    _pi, _u227, _reason = pi_choice(radius=r)
    if approx is None or abs(2 * _pi * r - approx) > 0.01:
        return None
    d = 2 * r
    if _u227:
        steps = [
            f"The circumference is pi times the diameter: "
            f"C = pi × d.",
            f"d = 2 × r = 2 × {fmt_num(r)} = {fmt_num(d)}, so "
            f"C = pi × {fmt_num(d)} = (22/7) × "
            f"{fmt_num(d)} = {fmt_num(2 * _pi * r)}",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "diameter", "label": "Using the diameter",
                "steps": steps,
                "answer": primary.get("answer", "")}
    steps = [
        f"The circumference is pi times the diameter: "
        f"C = pi × d.",
        f"d = 2 × r = 2 × {fmt_num(r)} = {fmt_num(d)}, so "
        f"C = pi × {fmt_num(d)} = {fmt_num(d)}·pi ≈ "
        f"{2 * _pi * r:.4f}",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "diameter", "label": "Using the diameter",
            "steps": steps, "answer": primary.get("answer", "")}


def _rect_grid_area_method(working, primary):
    """Rectangle / square area by counting unit squares in a
    grid (the primary multiplied length × breadth directly)."""
    ql = (working or "").lower()
    first = _answer_first_num(primary)
    if first is None:
        return None
    if "rectangle" in ql:
        l = find_param(ql, ["length"])
        b = find_param(ql, ["breadth", "width"])
        if l is None or b is None or l * b != first:
            return None
        steps = [
            "Counting-squares method: cover the rectangle "
            "with unit squares (1 × 1). Each row along the "
            f"length holds {fmt_num(l)} squares, and there "
            f"are {fmt_num(b)} rows.",
            f"Total unit squares = {fmt_num(l)} × "
            f"{fmt_num(b)} = {fmt_num(l * b)}, and each has "
            f"area 1, so the area is {fmt_num(l * b)}.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "grid_counting",
                "label": "Counting unit squares",
                "steps": steps,
                "answer": primary.get("answer", "")}
    if "square" in ql:
        s = find_param(ql, ["side"])
        if s is None or s * s != first:
            return None
        steps = [
            "Counting-squares method: cover the square with "
            f"unit squares (1 × 1) — {fmt_num(s)} rows of "
            f"{fmt_num(s)} squares each.",
            f"Total unit squares = {fmt_num(s)} × "
            f"{fmt_num(s)} = {fmt_num(s * s)}, so the area "
            f"is {fmt_num(s * s)}.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "grid_counting",
                "label": "Counting unit squares",
                "steps": steps,
                "answer": primary.get("answer", "")}
    return None


def _perimeter_sides_method(working, primary):
    """Perimeter by adding every side (the primary used the
    2(l + b) / 4s shortcut)."""
    ql = (working or "").lower()
    first = _answer_first_num(primary)
    if first is None:
        return None
    if "rectangle" in ql:
        l = find_param(ql, ["length"])
        b = find_param(ql, ["breadth", "width"])
        if l is None or b is None or 2 * (l + b) != first:
            return None
        steps = [
            "Perimeter is the total boundary — add all "
            "four sides one by one (opposite sides of a "
            "rectangle are equal):",
            f"{fmt_num(l)} + {fmt_num(b)} + {fmt_num(l)} + "
            f"{fmt_num(b)} = {fmt_num(2 * (l + b))}",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "side_addition",
                "label": "Adding all the sides",
                "steps": steps,
                "answer": primary.get("answer", "")}
    if "square" in ql:
        s = find_param(ql, ["side"])
        if s is None or 4 * s != first:
            return None
        steps = [
            "Perimeter is the total boundary — add all "
            "four equal sides one by one:",
            f"{fmt_num(s)} + {fmt_num(s)} + {fmt_num(s)} + "
            f"{fmt_num(s)} = {fmt_num(4 * s)}",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "side_addition",
                "label": "Adding all the sides",
                "steps": steps,
                "answer": primary.get("answer", "")}
    return None


def _volume_layers_method(working, primary):
    """Cuboid / cube volume by layers of unit cubes (the
    primary multiplied l × b × h directly)."""
    ql = (working or "").lower()
    first = _answer_first_num(primary)
    if first is None:
        return None
    if "cuboid" in ql or "rectangular" in ql:
        l = find_param(ql, ["length"])
        b = find_param(ql, ["breadth", "width"])
        h = find_param(ql, ["height"])
        if None in (l, b, h) or l * b * h != first:
            return None
        steps = [
            "Layer method: fill the cuboid with unit cubes, "
            "one layer at a time.",
            f"One layer on the base holds {fmt_num(l)} × "
            f"{fmt_num(b)} = {fmt_num(l * b)} cubes.",
            f"There are {fmt_num(h)} layers, so the total "
            f"is {fmt_num(l * b)} × {fmt_num(h)} = "
            f"{fmt_num(l * b * h)} cubes — and that count "
            f"is the volume.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "layers", "label": "Layer method",
                "steps": steps,
                "answer": primary.get("answer", "")}
    if "cube" in ql:
        s = find_param(ql, ["side", "edge"])
        if s is None or s ** 3 != first:
            return None
        steps = [
            "Layer method: fill the cube with unit cubes, "
            "one layer at a time.",
            f"One layer holds {fmt_num(s)} × {fmt_num(s)} = "
            f"{fmt_num(s * s)} cubes, and there are "
            f"{fmt_num(s)} layers.",
            f"Total = {fmt_num(s * s)} × {fmt_num(s)} = "
            f"{fmt_num(s ** 3)} cubes — and that count is "
            f"the volume.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "layers", "label": "Layer method",
                "steps": steps,
                "answer": primary.get("answer", "")}
    return None


def _cylinder_base_area_method(working, primary):
    """Cylinder volume as (area of the circular base) ×
    height — a stack of identical circles."""
    ql = (working or "").lower()
    if "cylinder" not in ql:
        return None
    r = find_param(ql, ["radius"])
    h = find_param(ql, ["height"])
    if r is None or h is None:
        return None
    approx = _answer_approx(primary)
    if approx is None:
        approx = _answer_first_num(primary)
    _pi, _u227, _reason = pi_choice(radius=r)
    base = _pi * r * r
    vol = base * h
    if approx is None or abs(vol - approx) > 0.01:
        return None
    if _u227:
        steps = [
            "Think of the cylinder as a stack of identical "
            "thin circles, one on top of another.",
            f"Area of one circular base = pi × r^2 = "
            f"(22/7) × {fmt_num(r)}^2 = {fmt_num(base)}.",
            f"The stack is {fmt_num(h)} high, so the volume "
            f"= {fmt_num(base)} × {fmt_num(h)} "
            f"= {fmt_num(vol)}.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "base_area",
                "label": "Base area × height method",
                "steps": steps,
                "answer": primary.get("answer", "")}
    steps = [
        "Think of the cylinder as a stack of identical "
        "thin circles, one on top of another.",
        f"Area of one circular base = pi × r^2 = pi × "
        f"{fmt_num(r)}^2 = {fmt_num(r * r)}·pi ≈ "
        f"{base:.4f}.",
        f"The stack is {fmt_num(h)} high, so the volume = "
        f"{base:.4f} × {fmt_num(h)} ≈ {vol:.4f}.",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "base_area", "label": "Base area × height method",
            "steps": steps, "answer": primary.get("answer", "")}


def _cone_third_method(working, primary):
    """Cone volume as one-third of the matching cylinder."""
    ql = (working or "").lower()
    if "cone" not in ql or "cylinder" in ql:
        return None
    r = find_param(ql, ["radius"])
    h = find_param(ql, ["height"])
    if r is None or h is None:
        return None
    approx = _answer_approx(primary)
    if approx is None:
        approx = _answer_first_num(primary)
    _pi, _u227, _reason = pi_choice(radius=r)
    cyl = _pi * r * r * h
    vol = cyl / 3.0
    if approx is None or abs(vol - approx) > 0.01:
        return None
    if _u227:
        steps = [
            "A cone holds exactly one-third of a cylinder "
            "with the same base and height.",
            f"Cylinder volume = pi × r^2 × h = (22/7) × "
            f"{fmt_num(r)}^2 × {fmt_num(h)} "
            f"= {fmt_num(cyl)}.",
            f"Cone volume = {fmt_num(cyl)} / 3 "
            f"= {fmt_num(vol)}.",
            _final_line(primary.get("answer", "")),
        ]
        return {"id": "cone_third",
                "label": "One-third of the cylinder",
                "steps": steps,
                "answer": primary.get("answer", "")}
    steps = [
        "A cone holds exactly one-third of a cylinder with "
        "the same base and height.",
        f"Cylinder volume = pi × r^2 × h = pi × "
        f"{fmt_num(r)}^2 × {fmt_num(h)} ≈ {cyl:.4f}.",
        f"Cone volume = {cyl:.4f} / 3 ≈ {vol:.4f}.",
        _final_line(primary.get("answer", "")),
    ]
    return {"id": "cone_third",
            "label": "One-third of the cylinder",
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

        # Wave 53: pairs of linear equations (two unknowns).
        if ptype == "algebra" and pop == "system":
            out = _system_methods(working, primary)
            return [m for m in out
                    if _answer_check(m["answer"],
                                     primary.get("answer"))][:3]

        # Wave 13 families, keyed by the primary result's type/op.
        # Wave 53: collected as candidates so a family can offer
        # more than one genuine method; every helper verifies
        # its own result against the primary before returning.
        _cands = []

        def _add(m):
            if m is not None:
                _cands.append(m)

        if ptype == "word_problem" and pop == "simple_interest":
            _add(_si_yearly_method(working, primary))
        elif ptype == "number_theory" and pop == "gcd":
            _add(_hcf_euclid_method(working, primary))
        elif ptype == "number_theory" and pop == "lcm":
            _add(_lcm_hcf_method(working, primary))
            _add(_lcm_division_method(working, primary))
        elif ptype == "number_theory" and pop == "hcf_lcm":
            _add(_hcf_lcm_relation_method(working, primary))
        elif ptype == "geometry" and pop == "distance":
            _add(_distance_graph_method(working, primary))
        elif ptype == "geometry" and pop == "area":
            _add(_triangle_half_rect_method(working, primary))
            _add(_circle_diameter_area_method(working, primary))
            _add(_rect_grid_area_method(working, primary))
        elif ptype == "geometry" and pop == "circumference":
            _add(_circle_diameter_circ_method(working, primary))
        elif ptype == "geometry" and pop == "perimeter":
            _add(_perimeter_sides_method(working, primary))
        elif ptype == "geometry" and pop in ("volume",
                                              "cuboid volume"):
            _add(_volume_layers_method(working, primary))
            _add(_cylinder_base_area_method(working, primary))
            _add(_cone_third_method(working, primary))
        elif ptype == "sequences" and pop in ("ap_nth_term",
                                              "gp_nth_term"):
            _add(_sequence_listing_method(working, primary))
        elif ptype == "sequences" and pop == "ap_sum":
            _add(_ap_sum_pairing_method(working, primary))
        elif ptype == "sequences" and pop == "gp_sum":
            _add(_gp_sum_addition_method(working, primary))
        elif ptype == "statistics" and pop == "mean":
            _add(_mean_assumed_method(working, primary))
        elif ptype == "statistics" and pop == "median":
            _add(_median_position_method(working, primary))
        elif ptype == "statistics" and pop == "probability":
            _add(_probability_complement_method(working,
                                                primary))
        elif ptype == "trigonometry" and \
                pop == "ratio_from_ratio":
            _add(_trig_identity_method(working, primary))
        elif ptype == "trigonometry" and pop == "value":
            _add(_trig_triangle_method(working, primary))
        elif ptype == "applied" and pop == "compound_interest":
            _add(_ci_yearly_method(working, primary))
        elif ptype == "applied" and \
                pop == "profit_loss_percent":
            _add(_pl_percent_unitary_method(working, primary))
        elif ptype == "applied" and \
                pop == "reverse_profit_loss":
            _add(_reverse_pl_unitary_method(working, primary))
        elif ptype == "applied" and pop == "discount":
            _add(_discount_direct_method(working, primary))
        elif ptype == "applied" and \
                pop == "successive_discount":
            _add(_successive_discount_equiv_method(working,
                                                   primary))
        elif ptype == "applied" and pop == "percent_score":
            _add(_percent_score_unitary_method(working, primary))
        elif ptype == "applied" and pop == "unitary_cost":
            _add(_unitary_cost_proportion_method(working,
                                                 primary))
        elif ptype == "applied" and pop == "ratio_divide":
            _add(_ratio_fraction_method(working, primary))
        return [m for m in _cands
                if _answer_check(m["answer"],
                                 primary.get("answer"))][:3]
    except Exception:
        return []
