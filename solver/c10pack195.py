"""Wave 195: Class 10 special-form pack — form-audit top-10
item #10 (audit rows 33-35; spot-check probes 27, 28, 29).

Three families whose BASICS already solved but whose NCERT
special dresses did not:

  (a) Coordinate-geometry specials (Ex 7.1-7.2).  geometry.py
      / rekha.py cover distance, midpoint, section and
      collinearity, but probe 27 — "If (1, 2), (4, y), (x, 6)
      and (3, 5) are the vertices of a parallelogram taken
      in order, find x and y" — was a parse error.  Here:
      parallelogram vertices with unknowns (diagonal
      midpoints are equal), the fourth vertex of a
      parallelogram, a point on the x/y-axis equidistant
      from two points, distance-from-a-point = k with an
      unknown coordinate, points of trisection / equal
      parts, quadrilateral-type classification from four
      vertices, and the "AP = (m/n) AB" section dress
      (which fragment-served the bare fraction 3/7).

  (b) Given ONE trigonometric ratio, find the others
      (Ex 8.1).  Probe 28 — "Given sec theta = 13/5,
      calculate all other trigonometric ratios" — was a
      FRAGMENT SERVE: the router echoed "13/5".  The same
      echo hit cos and cot givens; "If sin A = 3/4,
      calculate cos A and tan A" served the nonsense
      equation "A = 3/4"; "If tan A = 4/3, find the other
      trigonometric ratios" served only sin and cos; and
      "Given 15 cot A = 8, find sin A and sec A" served
      sqrt(65) values (the coefficient 15 was dropped) when
      the 8-15-17 triple gives sin A = 15/17, sec A = 17/8.
      Here: any of sin/cos/tan/sec/cosec/cot given as a
      fraction a/b, a ratio a:b, or with a coefficient
      (15 cot A = 8), for all-others asks and named partial
      asks; the right-triangle-with-two-sides dress
      ("right-angled at B, AB = 24, BC = 7, determine
      sin A, cos A"); and ratios expressed in terms of
      cot A / sec A via the standard identities, verified
      numerically before serving.  Acute-angle convention
      (NCERT Class 10 scope) is stated in the steps.

  (c) AP word dresses (Ex 5.2-5.3).  Probe 29 — the NCERT
      penalty question (Rs 200, 250, 300, ..., 30 days) —
      was a parse error at the native layer.  Here:
      penalty / escalating-charge totals, savings with a
      periodic increment reaching a target, prize lists
      from a total, the houses-1-to-N preceding/following
      sums, stacked-logs rows, the reverse form "the sum
      of first n terms is 4n - n^2, find ...",
      missing-terms-in-boxes, the AP table fill (given
      subsets of a, d, n, a_k, S_k that determine the
      rest), and the explicit-series find-d dress.
      Narrative templates are STRUCTURAL (numbers vary);
      an unmatched narrative declines.

Discipline (house rules, Waves 169-194): every schema
fires only when it settles the question COMPLETELY, every
value is recomputed exactly (Fraction / SymPy) and
verified before serving, and anything doubtful returns
None so routing continues unchanged.  Wiring in router.py:
a failure-only gate after the Wave 175 block, plus a
fragment-repair block that displaces ONLY the measured
fragment ops (evaluate / equation / ratio_from_ratio)
under w195_displaces — a verified difference at the seam.
Schemas require the actual ask dress (Wave 192 lesson):
a concept / why / define question declines at entry even
when it mentions the family's objects.
"""
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt, parse_expression

# ------------------------------------------------------------------
# shared helpers
# ------------------------------------------------------------------

_CONCEPT_VETO = (
    "define", "definition", "why ", "explain why",
    "meaning of", "kya hai", "kya hota", "kyun",
    "state whether", "true or false",
    "shown below", "as shown", "in the figure",
)


def _prep(text):
    s = str(text)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("θ", "theta").replace("Θ", "theta")
    s = s.replace("₹", "Rs ")
    return s


def _frac(token):
    """'1.75' / '-4' / '3/4' -> Fraction, or None."""
    t = str(token).strip()
    try:
        if "/" in t:
            p, q = t.split("/", 1)
            return Fraction(int(p.strip()), int(q.strip()))
        return Fraction(t)
    except Exception:
        return None


def _fmtf(fr):
    """Fraction -> '3', '3/4', or a short decimal when the
    fraction is a clean decimal (money: 1.75, not 7/4).
    Letter coordinates pass through unchanged."""
    if isinstance(fr, str):
        return fr
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    den = fr.denominator
    d = den
    for p in (2, 5):
        while d % p == 0:
            d //= p
    if d == 1:
        s = f"{float(fr):.10f}".rstrip("0").rstrip(".")
        return s
    return f"{fr.numerator}/{fr.denominator}"


def _fmt_coord(fr):
    """Coordinate formatting: fractions stay fractions
    (7/2, not 3.5); letters pass through."""
    if isinstance(fr, str):
        return fr
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _fmt_pt(p):
    return f"({_fmt_coord(p[0])}, {_fmt_coord(p[1])})"


_POINT_RE = re.compile(
    r"\(\s*(-?\d+(?:\.\d+)?|-?[a-zA-Z])\s*,"
    r"\s*(-?\d+(?:\.\d+)?|-?[a-zA-Z])\s*\)")


def _points(q):
    """All (x, y) point literals in order; each coordinate a
    Fraction or a single-letter unknown (lowercase str)."""
    out = []
    for m in _POINT_RE.finditer(q):
        pt = []
        for tok in (m.group(1), m.group(2)):
            if re.fullmatch(r"-?[a-zA-Z]", tok):
                pt.append(tok.lower().lstrip("-")
                          if not tok.startswith("-")
                          else "-" + tok[1].lower())
            else:
                v = _frac(tok)
                if v is None:
                    return None
                pt.append(v)
        out.append(tuple(pt))
    return out


def _numeric_points(q):
    pts = _points(q)
    if pts is None:
        return None
    if any(not isinstance(c, Fraction) for p in pts for c in p):
        return None
    return pts


def _result(type_, op, answer, steps):
    return {"type": type_, "op": op, "answer": answer,
            "steps": steps}


# ------------------------------------------------------------------
# (a) coordinate-geometry specials
# ------------------------------------------------------------------

def _parallelogram_unknowns(q, ql):
    if "parallelogram" not in ql or "find" not in ql:
        return None
    pts = _points(q)
    if pts is None or len(pts) != 4:
        return None
    letters = []
    for p in pts:
        for c in p:
            if isinstance(c, str):
                name = c.lstrip("-")
                if name not in letters:
                    letters.append(name)
    if not letters or len(letters) > 2:
        return None
    # The find-ask must name every unknown letter.
    tail = ql[ql.rfind("find"):]
    if any(not re.search(rf"\b{name}\b", tail) for name in letters):
        return None
    syms = {name: sp.Symbol(name) for name in letters}

    def val(c):
        if isinstance(c, Fraction):
            return sp.Rational(c.numerator, c.denominator)
        if c.startswith("-"):
            return -syms[c[1:]]
        return syms[c]

    (a, b, c_, d) = [tuple(val(x) for x in p) for p in pts]
    eqs = [sp.Eq(a[0] + c_[0], b[0] + d[0]),
           sp.Eq(a[1] + c_[1], b[1] + d[1])]
    try:
        sols = sp.solve(eqs, [syms[n] for n in letters],
                        dict=True)
    except Exception:
        return None
    if len(sols) != 1:
        return None
    sol = sols[0]
    if set(sol.keys()) != {syms[n] for n in letters}:
        return None
    for v in sol.values():
        if v.free_symbols or v.is_real is False:
            return None
    # Verify: substituted diagonals really share a midpoint,
    # and the four vertices are distinct.
    sub = [tuple(sp.simplify(x.subs(sol)) for x in p)
           for p in (a, b, c_, d)]
    if len(set(sub)) != 4:
        return None
    if sp.simplify((sub[0][0] + sub[2][0])
                   - (sub[1][0] + sub[3][0])) != 0:
        return None
    if sp.simplify((sub[0][1] + sub[2][1])
                   - (sub[1][1] + sub[3][1])) != 0:
        return None
    final = ", ".join(f"{n} = {fmt(sol[syms[n]])}"
                      for n in letters)
    steps = [
        "In a parallelogram the diagonals bisect each other, "
        "so the diagonals have the same midpoint.",
        f"Midpoint of the diagonal joining {_fmt_pt(pts[0])} "
        f"and {_fmt_pt(pts[2])} = midpoint of the diagonal "
        f"joining {_fmt_pt(pts[1])} and {_fmt_pt(pts[3])}.",
        "Equating the x-coordinates and the y-coordinates "
        "and solving gives:",
        final + ".",
    ]
    return _result("geometry", "w195_parallelogram_unknowns",
                   final, steps)


def _parallelogram_fourth(q, ql):
    if "parallelogram" not in ql or "fourth" not in ql:
        return None
    pts = _numeric_points(q)
    if pts is None or len(pts) != 3:
        return None
    a, b, c = pts
    d = (a[0] + c[0] - b[0], a[1] + c[1] - b[1])
    if d in pts:
        return None
    steps = [
        "The diagonals of a parallelogram bisect each other, "
        "so the fourth vertex D satisfies D = A + C - B "
        "(B is the vertex between A and C).",
        f"D = {_fmt_pt(a)} + {_fmt_pt(c)} - {_fmt_pt(b)} "
        f"= {_fmt_pt(d)}.",
    ]
    return _result("geometry", "w195_parallelogram_fourth",
                   _fmt_pt(d), steps)


def _equidistant_on_axis(q, ql):
    if "equidistant" not in ql:
        return None
    if "y-axis" in ql or "y axis" in ql:
        axis = "y"
    elif "x-axis" in ql or "x axis" in ql:
        axis = "x"
    else:
        return None
    pts = _numeric_points(q)
    if pts is None or len(pts) != 2:
        return None
    (x1, y1), (x2, y2) = pts
    t = sp.Symbol("t")
    if axis == "y":
        p = (sp.Integer(0), t)
        fixed = sp.Integer(0)
    else:
        p = (t, sp.Integer(0))
        fixed = sp.Integer(0)
    d1 = (p[0] - x1) ** 2 + (p[1] - y1) ** 2
    d2 = (p[0] - x2) ** 2 + (p[1] - y2) ** 2
    try:
        sols = sp.solve(sp.Eq(d1, d2), t)
    except Exception:
        return None
    sols = [s for s in sols if s.is_real is not False
            and not s.free_symbols]
    if len(sols) != 1:
        return None
    v = sols[0]
    # Verify numerically-exactly: both squared distances equal.
    if sp.simplify(d1.subs(t, v) - d2.subs(t, v)) != 0:
        return None
    pt = (Fraction(0), Fraction(v)) if axis == "y" \
        else (Fraction(v), Fraction(0))
    var = "y" if axis == "y" else "x"
    generic = f"(0, {var})" if axis == "y" else f"({var}, 0)"
    steps = [
        f"Let the point on the {axis}-axis be {generic}.",
        "Its distances from the two given points are equal, "
        "so the squared distances are equal:",
        f"{fmt(sp.expand(d1))} = {fmt(sp.expand(d2))}",
        f"Solving gives {var} = {fmt(v)}, so the point is "
        f"{_fmt_pt(pt)}.",
    ]
    return _result("geometry", "w195_equidistant_axis",
                   _fmt_pt(pt), steps)


def _distance_equals(q, ql):
    if "distance" not in ql or "find" not in ql:
        return None
    m = re.search(r"distance between[^=]*?is\s+"
                  r"(\d+(?:\.\d+)?)\s*(?:units|unit)?\b", ql)
    if not m:
        return None
    k = _frac(m.group(1))
    if k is None or k <= 0:
        return None
    pts = _points(q)
    if pts is None or len(pts) != 2:
        return None
    letters = [c for p in pts for c in p if isinstance(c, str)]
    if len(letters) != 1:
        return None
    name = letters[0].lstrip("-")
    if not re.search(rf"find (?:the value of )?{name}\b", ql) \
            and not re.search(rf"value of {name}\b", ql):
        return None
    sym = sp.Symbol(name)

    def val(c):
        if isinstance(c, Fraction):
            return sp.Rational(c.numerator, c.denominator)
        return sym if not c.startswith("-") else -sym

    (x1, y1), (x2, y2) = [tuple(val(c) for c in p) for p in pts]
    expr = (x2 - x1) ** 2 + (y2 - y1) ** 2 - k ** 2
    try:
        sols = sp.solve(sp.Eq(expr, 0), sym)
    except Exception:
        return None
    sols = sorted({s for s in sols
                   if s.is_real is not False
                   and not s.free_symbols},
                  key=lambda s: float(s))
    if not sols or len(sols) > 2:
        return None
    for s in sols:
        if sp.simplify(expr.subs(sym, s)) != 0:
            return None
    final = " or ".join(f"{name} = {fmt(s)}" for s in sols)
    steps = [
        f"By the distance formula, the distance between "
        f"{_fmt_pt(pts[0])} and {_fmt_pt(pts[1])} is "
        f"{_fmtf(k)}.",
        f"So ({fmt(x2 - x1)})^2 + ({fmt(y2 - y1)})^2 "
        f"= {_fmtf(k)}^2, which gives "
        f"{fmt(sp.expand(expr + k ** 2))} = {_fmtf(k ** 2)}.",
        f"Solving, {final}.",
    ]
    return _result("geometry", "w195_distance_equals", final,
                   steps)


def _equal_parts(q, ql):
    pts = _numeric_points(q)
    if pts is None or len(pts) != 2:
        return None
    if "trisection" in ql or "trisect" in ql:
        n = 3
    else:
        m = re.search(
            r"into\s+(two|three|four|five|six|2|3|4|5|6)\s+"
            r"equal parts", ql)
        if not m:
            return None
        n = {"two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6}.get(m.group(1))
        if n is None:
            n = int(m.group(1))
    (x1, y1), (x2, y2) = pts
    out = []
    for i in range(1, n):
        px = x1 + Fraction(i, n) * (x2 - x1)
        py = y1 + Fraction(i, n) * (y2 - y1)
        out.append((px, py))
    label = "points of trisection" if n == 3 else \
        f"points dividing the segment into {n} equal parts"
    steps = [
        f"The {label} divide the segment in the ratios "
        + ", ".join(f"{i} : {n - i}" for i in range(1, n))
        + " (section formula).",
    ]
    for i, p in enumerate(out, 1):
        steps.append(f"Point {i}: {_fmt_pt(p)}")
    final = ", ".join(_fmt_pt(p) for p in out)
    return _result("geometry", "w195_equal_parts", final, steps)


def _quadrilateral_type(q, ql):
    if "quadrilateral" not in ql and "vertices of a" not in ql:
        return None
    pts = _numeric_points(q)
    if pts is None or len(pts) != 4:
        return None
    if len(set(pts)) != 4:
        return None
    claim = None
    for name in ("square", "rectangle", "rhombus",
                 "parallelogram", "kite"):
        if re.search(rf"vertices of an?\s+{name}\b", ql) or \
                re.search(rf"is an?\s+{name}\b", ql):
            claim = name
            break
    ask = claim is not None or "type" in ql or "name" in ql \
        or "classify" in ql
    if not ask:
        return None

    def d2(p, r):
        return (p[0] - r[0]) ** 2 + (p[1] - r[1]) ** 2

    a, b, c, d = pts
    sides = [d2(a, b), d2(b, c), d2(c, d), d2(d, a)]
    diags = [d2(a, c), d2(b, d)]
    if any(s == 0 for s in sides) or any(s == 0 for s in diags):
        return None
    s1, s2, s3, s4 = sides
    if s1 == s2 == s3 == s4:
        verdict = "square" if diags[0] == diags[1] else "rhombus"
    elif s1 == s3 and s2 == s4:
        verdict = "rectangle" if diags[0] == diags[1] \
            else "parallelogram"
    elif (s1 == s2 and s3 == s4 and s1 != s3) or \
            (s2 == s3 and s4 == s1 and s2 != s4):
        verdict = "kite"
    else:
        return None  # no special type: decline, do not guess
    if claim is not None and claim != verdict:
        return None  # never contradict / never force a proof
    names = ["AB", "BC", "CD", "DA"]
    steps = ["Side lengths squared: " + ", ".join(
        f"{names[i]}^2 = {_fmtf(sides[i])}" for i in range(4))
        + f"; diagonals squared: AC^2 = {_fmtf(diags[0])}, "
        f"BD^2 = {_fmtf(diags[1])}."]
    reason = {
        "square": "All four sides are equal and the diagonals "
                  "are equal, so it is a square.",
        "rhombus": "All four sides are equal but the diagonals "
                   "are not equal, so it is a rhombus.",
        "rectangle": "Opposite sides are equal and the "
                     "diagonals are equal, so it is a rectangle.",
        "parallelogram": "Opposite sides are equal and the "
                         "diagonals are not equal, so it is a "
                         "parallelogram.",
        "kite": "Two distinct pairs of adjacent sides are "
                "equal, so it is a kite.",
    }[verdict]
    steps.append(reason)
    art = "an" if verdict[0] in "aeiou" else "a"
    final = f"{art.capitalize()} {verdict}" if claim is None \
        else f"Yes, the points are the vertices of {art} {verdict}"
    if claim is not None:
        final = (f"The points are the vertices of {art} "
                 f"{verdict} (verified from the side and "
                 f"diagonal lengths).")
    return _result("geometry", "w195_quadrilateral_type",
                   final, steps)


def _ap_fraction_point(q, ql):
    m = re.search(r"\bAP\s*=\s*(\d+)\s*/\s*(\d+)\s*(?:of\s+)?AB\b",
                  q)
    if not m:
        return None
    num, den = int(m.group(1)), int(m.group(2))
    if den == 0 or num <= 0 or num >= den:
        return None
    pts = _numeric_points(q)
    if pts is None or len(pts) != 2:
        return None
    (x1, y1), (x2, y2) = pts
    f = Fraction(num, den)
    p = (x1 + f * (x2 - x1), y1 + f * (y2 - y1))
    steps = [
        f"AP = {num}/{den} of AB, so P divides AB internally "
        f"in the ratio {num} : {den - num}.",
        f"By the section formula, P = {_fmt_pt(p)}.",
    ]
    return _result("geometry", "w195_ap_fraction_point",
                   _fmt_pt(p), steps)


_COORD_FNS = (_parallelogram_unknowns, _parallelogram_fourth,
              _equidistant_on_axis, _distance_equals,
              _equal_parts, _quadrilateral_type,
              _ap_fraction_point)


# ------------------------------------------------------------------
# (b) given one trig ratio, find the others
# ------------------------------------------------------------------

_TRIG_ORDER = ("sin", "cos", "tan", "sec", "cosec", "cot")
_TRIG_DISP = {"csc": "cosec"}
_GIVEN_RE = re.compile(
    r"(?:(\d+(?:\.\d+)?)\s*)?"
    r"\b(sin|cos|tan|sec|cosec|csc|cot)\s+"
    r"(theta|[A-Za-z])\b\s*=\s*"
    r"(\d+(?:\.\d+)?)\s*(?:/\s*(\d+(?:\.\d+)?)"
    r"|:\s*(\d+(?:\.\d+)?))?",
    re.I)


def _trig_disp(fn):
    return _TRIG_DISP.get(fn, fn)


def _sides_from_given(fn, value):
    """value: Fraction p/q in lowest terms.  Returns
    (opp, adj, hyp) as sympy values, or None."""
    p, q_ = value.numerator, value.denominator
    if p <= 0 or q_ <= 0:
        return None
    if fn == "sin":
        opp, hyp = p, q_
        adj = sp.sqrt(hyp ** 2 - opp ** 2)
    elif fn == "cos":
        adj, hyp = p, q_
        opp = sp.sqrt(hyp ** 2 - adj ** 2)
    elif fn == "tan":
        opp, adj = p, q_
        hyp = sp.sqrt(opp ** 2 + adj ** 2)
    elif fn == "sec":
        hyp, adj = p, q_
        if hyp <= adj:
            return None
        opp = sp.sqrt(hyp ** 2 - adj ** 2)
    elif fn in ("cosec", "csc"):
        hyp, opp = p, q_
        if hyp <= opp:
            return None
        adj = sp.sqrt(hyp ** 2 - opp ** 2)
    elif fn == "cot":
        adj, opp = p, q_
        hyp = sp.sqrt(opp ** 2 + adj ** 2)
    else:
        return None
    if fn in ("sin", "cos") and hyp <= (opp if fn == "sin"
                                       else adj):
        return None
    return sp.sympify(opp), sp.sympify(adj), sp.sympify(hyp)


def _ratio_values(opp, adj, hyp):
    return {
        "sin": sp.simplify(opp / hyp),
        "cos": sp.simplify(adj / hyp),
        "tan": sp.simplify(opp / adj),
        "sec": sp.simplify(hyp / adj),
        "cosec": sp.simplify(hyp / opp),
        "cot": sp.simplify(adj / opp),
    }


def _given_step(fn, ang, value, opp, adj, hyp):
    sides = {"sin": ("opposite", opp, "hypotenuse", hyp),
             "cos": ("adjacent", adj, "hypotenuse", hyp),
             "tan": ("opposite", opp, "adjacent", adj),
             "sec": ("hypotenuse", hyp, "adjacent", adj),
             "cosec": ("hypotenuse", hyp, "opposite", opp),
             "cot": ("adjacent", adj, "opposite", opp)}[fn]
    return (f"{_trig_disp(fn)} {ang} = {sides[0]}/{sides[2]} "
            f"= {_fmtf(value)}, so take {sides[0]} "
            f"= {fmt(sides[1])} and {sides[2]} = {fmt(sides[3])}.")


def _pyth_step(opp, adj, hyp):
    return (f"By Pythagoras, the third side comes from "
            f"opposite^2 + adjacent^2 = hypotenuse^2 with "
            f"opposite = {fmt(opp)}, adjacent = {fmt(adj)}, "
            f"hypotenuse = {fmt(hyp)}.")


def _trig_given_one(q, ql):
    if not any(w in ql for w in ("find", "calculate",
                                 "evaluate", "determine")):
        return None
    m = _GIVEN_RE.search(q)
    if not m:
        return None
    coeff, fn, ang, num, den, den2 = m.groups()
    fn = fn.lower()
    if fn == "csc":
        fn = "cosec"
    ang = "theta" if ang.lower() == "theta" else ang.upper()
    ang_disp = "θ" if ang == "theta" else ang
    top = _frac(num)
    bot = _frac(den or den2) if (den or den2) else Fraction(1)
    if top is None or bot is None or bot == 0:
        return None
    value = top / bot
    if coeff:
        c = _frac(coeff)
        if c is None or c == 0:
            return None
        value = value / c
    if value <= 0:
        return None
    sides = _sides_from_given(fn, value)
    if sides is None:
        return None
    opp, adj, hyp = sides
    vals = _ratio_values(opp, adj, hyp)
    # Verify the given ratio is reproduced exactly.
    if sp.simplify(vals[fn] - sp.Rational(value.numerator,
                                          value.denominator)) != 0:
        return None
    if sp.simplify(opp ** 2 + adj ** 2 - hyp ** 2) != 0:
        return None
    tail = ql[m.end():]
    # An expression ask ("find the value of (sin A + cos A) /
    # (sin A - cos A)", "find cos A + tan A") asks for a
    # combination, not the ratios themselves: decline so the
    # expression schemas keep it.
    if "(" in tail or re.search(
            r"\b(sin|cos|tan|sec|cosec|cot)\s+"
            r"(?:theta|[a-z])\s*[+\-*/]", tail):
        return None
    all_markers = ("all other", "all the other", "other "
                   "trigonometric ratios", "all trigonometric",
                   "all ratios", "all six", "other ratios")
    if any(mk in tail for mk in all_markers) or \
            "all other" in ql or "other trigonometric" in ql:
        asked = [f for f in _TRIG_ORDER if f != fn]
    else:
        asked = []
        ang_low = ang.lower()
        for f in _TRIG_ORDER:
            if f == fn:
                continue
            pat = rf"\b{_trig_disp(f) if f == 'cosec' else f}" \
                  rf"\s+(?:theta|{re.escape(ang_low)})\b"
            if re.search(pat, tail) or \
                    (f == "cosec" and re.search(
                        rf"\bcsc\s+(?:theta|{re.escape(ang_low)})\b",
                        tail)):
                asked.append(f)
        if not asked:
            return None
    steps = [
        _given_step(fn, ang_disp, value, opp, adj, hyp),
        _pyth_step(opp, adj, hyp),
        f"{ang_disp} is acute (Class 10 convention), so all "
        f"the ratios are positive.",
    ]
    for f in asked:
        steps.append(f"{_trig_disp(f)} {ang_disp} = "
                     f"{fmt(vals[f])}")
    final = ", ".join(f"{_trig_disp(f)} {ang_disp} = "
                      f"{fmt(vals[f])}" for f in asked)
    return _result("trigonometry", "w195_trig_ratios", final,
                   steps)


_SIDE_RE = re.compile(r"\b([A-Z])([A-Z])\s*=\s*"
                      r"(\d+(?:\.\d+)?)")


def _trig_triangle_sides(q, ql):
    if "right" not in ql or "angled" not in ql:
        return None
    if not any(w in ql for w in ("find", "determine",
                                 "calculate", "evaluate")):
        return None
    m = re.search(r"right[- ]angled at\s+([A-Z])", q)
    if not m:
        return None
    right = m.group(1)
    tm = re.search(r"triangle\s+([A-Z])([A-Z])([A-Z])", q)
    if not tm:
        return None
    verts = [tm.group(1), tm.group(2), tm.group(3)]
    if right not in verts:
        return None
    sides = {}
    for sm in _SIDE_RE.finditer(q):
        key = "".join(sorted((sm.group(1), sm.group(2))))
        v = _frac(sm.group(3))
        if v is None:
            return None
        sides[key] = v
    if len(sides) != 2:
        return None
    hyp_key = "".join(sorted(v for v in verts if v != right))

    def skey(u, v):
        return "".join(sorted((u, v)))

    all_keys = {skey(verts[0], verts[1]), skey(verts[1], verts[2]),
                skey(verts[0], verts[2])}
    missing = all_keys - set(sides)
    if len(missing) != 1:
        return None
    mk = missing.pop()
    known = list(sides.items())
    if mk == hyp_key:
        a, b = known[0][1], known[1][1]
        third = sp.sqrt(a ** 2 + b ** 2)
        sides[mk] = third
    else:
        if hyp_key not in sides:
            return None
        hyp = sides[hyp_key]
        other = [v for k, v in known if k != hyp_key]
        if len(other) != 1 or hyp <= other[0]:
            return None
        sides[mk] = sp.sqrt(hyp ** 2 - other[0] ** 2)
    # Verify Pythagoras on the completed triangle.
    legs = [v for k, v in sides.items() if k != hyp_key]
    if sp.simplify(legs[0] ** 2 + legs[1] ** 2
                   - sides[hyp_key] ** 2) != 0:
        return None
    asked = []
    for fm in re.finditer(
            r"\b(sin|cos|tan|sec|cosec|csc|cot)\s+([A-Z])\b", q):
        f = fm.group(1).lower()
        if f == "csc":
            f = "cosec"
        angv = fm.group(2)
        if angv == right or angv not in verts:
            continue
        if (f, angv) not in asked:
            asked.append((f, angv))
    if not asked:
        return None
    hyp = sides[hyp_key]
    steps = [f"The triangle is right-angled at {right}, so "
             f"{hyp_key} is the hypotenuse."]
    steps.append("By Pythagoras, the third side is "
                 f"{mk} = {fmt(sides[mk])}, giving "
                 + ", ".join(f"{k} = {fmt(v)}"
                             for k, v in sorted(sides.items()))
                 + ".")
    out = []
    for f, angv in asked:
        opp_key = skey(*[v for v in verts if v != angv])
        adj_key = [k for k in all_keys
                   if k != hyp_key and k != opp_key][0]
        opp, adj = sides[opp_key], sides[adj_key]
        val = _ratio_values(opp, adj, hyp)[f]
        out.append(f"{_trig_disp(f)} {angv} = {fmt(val)}")
        steps.append(f"{_trig_disp(f)} {angv} = {fmt(val)} "
                     f"(opposite = {fmt(opp)}, adjacent = "
                     f"{fmt(adj)}, hypotenuse = {fmt(hyp)})")
    return _result("trigonometry", "w195_trig_triangle",
                   ", ".join(out), steps)


def _trig_in_terms(q, ql):
    m = re.search(r"in terms of\s+(cot|sec)\s+"
                  r"(theta|[A-Za-z])\b", q, re.I)
    if not m:
        return None
    if "trigonometric" not in ql and "ratios" not in ql:
        return None
    base = m.group(1).lower()
    ang = m.group(2)
    ang_disp = "θ" if ang.lower() == "theta" else ang.upper()
    x = sp.Symbol("x")
    if base == "cot":
        exprs = {
            "tan": 1 / x,
            "sin": 1 / sp.sqrt(1 + x ** 2),
            "cos": x / sp.sqrt(1 + x ** 2),
            "sec": sp.sqrt(1 + x ** 2) / x,
            "cosec": sp.sqrt(1 + x ** 2),
        }
        sample = sp.Rational(8, 15)  # 8-15-17 triangle
        sides = _sides_from_given("cot", Fraction(8, 15))
        ident = "1 + cot^2 A = cosec^2 A"
    else:
        exprs = {
            "cos": 1 / x,
            "sin": sp.sqrt(x ** 2 - 1) / x,
            "tan": sp.sqrt(x ** 2 - 1),
            "cot": 1 / sp.sqrt(x ** 2 - 1),
            "cosec": x / sp.sqrt(x ** 2 - 1),
        }
        sample = sp.Rational(13, 5)  # 5-12-13 triangle
        sides = _sides_from_given("sec", Fraction(13, 5))
        ident = "sec^2 A - 1 = tan^2 A"
    if sides is None:
        return None
    vals = _ratio_values(*sides)
    # Numeric verification of every identity expression.
    for f, e in exprs.items():
        got = float(e.subs(x, sample))
        want = float(vals[f])
        if abs(got - want) > 1e-9:
            return None
    steps = [
        f"Use the identity {ident} and the reciprocal "
        f"relations, taking positive roots because the "
        f"angle is acute.",
    ]
    out = []
    for f in _TRIG_ORDER:
        if f == base or f not in exprs:
            continue
        e = fmt(exprs[f]).replace("x", f"{base} {ang_disp}")
        out.append(f"{_trig_disp(f)} {ang_disp} = {e}")
        steps.append(out[-1])
    return _result("trigonometry", "w195_trig_in_terms",
                   ", ".join(out), steps)


_TRIG_FNS = (_trig_given_one, _trig_triangle_sides,
             _trig_in_terms)


# ------------------------------------------------------------------
# (c) AP word dresses
# ------------------------------------------------------------------

_NUMWORDS = {"one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
_ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4,
             "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8,
             "ninth": 9, "tenth": 10}


def _sn(a, d, n):
    return Fraction(n, 2) * (2 * a + (n - 1) * d)


def _ap_penalty(q, ql):
    if "penalty" not in ql and "escalating" not in ql \
            and "charges" not in ql:
        return None
    listed = []
    for m in re.finditer(
            r"rs\.?\s*(\d+(?:\.\d+)?)\s+for the "
            r"(first|second|third|fourth|fifth) day", ql):
        listed.append((_ORDINALS[m.group(2)],
                       _frac(m.group(1))))
    listed = [v for _, v in sorted(listed)]
    inc = None
    mi = re.search(r"rs\.?\s*(\d+(?:\.\d+)?)\s+more than", ql)
    if mi:
        inc = _frac(mi.group(1))
    if len(listed) >= 2:
        a = listed[0]
        d = listed[1] - listed[0]
        if any(listed[i] != a + i * d for i in range(len(listed))):
            return None
        if inc is not None and inc != d:
            return None
    elif len(listed) == 1 and inc is not None:
        a, d = listed[0], inc
    else:
        return None
    days = None
    for m in re.finditer(r"(\d+)\s*days?\b", ql):
        days = int(m.group(1))
    if not days:
        return None
    total = _sn(a, d, days)
    steps = [
        f"The daily penalties form an AP with first term "
        f"a = Rs {_fmtf(a)} and common difference "
        f"d = Rs {_fmtf(d)}.",
        f"Total for {days} days: S{days} = ({days}/2)"
        f"[2 x {_fmtf(a)} + {days - 1} x {_fmtf(d)}] "
        f"= Rs {_fmtf(total)}.",
    ]
    return _result("sequences", "w195_ap_penalty",
                   f"Rs {_fmtf(total)}", steps)


def _ap_savings_target(q, ql):
    if not any(w in ql for w in ("saved", "saves", "saving",
                                 "salary", "income")):
        return None
    m1 = re.search(r"(?:rs\.?\s*)?(\d+(?:\.\d+)?)\s+in the "
                   r"first (week|month|year)", ql)
    m2 = re.search(r"incre\w*\s+(?:\w+\s+){0,4}?(?:by|of)\s+"
                   r"(?:rs\.?\s*)?(\d+(?:\.\d+)?)", ql)
    m3 = re.search(r"(?:become|becomes|reach|reaches|reached)"
                   r"\s+(?:rs\.?\s*)?(\d+(?:\.\d+)?)", ql)
    if not (m1 and m2 and m3):
        return None
    if "find n" not in ql and "nth" not in ql \
            and "which week" not in ql and "which month" not in ql \
            and "which year" not in ql:
        return None
    a, d, target = (_frac(m1.group(1)), _frac(m2.group(1)),
                    _frac(m3.group(1)))
    if a is None or d is None or target is None or d == 0:
        return None
    n = (target - a) / d + 1
    if n.denominator != 1 or n < 1:
        return None
    n = int(n)
    period = m1.group(2)
    steps = [
        f"The amounts form an AP with a = Rs {_fmtf(a)} and "
        f"d = Rs {_fmtf(d)}.",
        f"For the nth {period}: a + (n - 1)d = "
        f"{_fmtf(target)}, so (n - 1) = "
        f"({_fmtf(target)} - {_fmtf(a)}) / {_fmtf(d)} "
        f"= {n - 1}, giving n = {n}.",
    ]
    return _result("sequences", "w195_ap_savings_target",
                   f"n = {n}", steps)


def _ap_prizes(q, ql):
    if "prize" not in ql:
        return None
    ms = re.search(r"sum of\s+rs\.?\s*(\d+(?:\.\d+)?)", ql)
    mn = re.search(r"\b(\d+|seven|five|six|eight|nine|ten|"
                   r"three|four)\s+(?:cash\s+)?prizes", ql)
    md = re.search(r"each prize is\s+rs\.?\s*(\d+(?:\.\d+)?)\s+"
                   r"(less|more) than", ql)
    if not (ms and mn and md):
        return None
    total = _frac(ms.group(1))
    n = int(mn.group(1)) if mn.group(1).isdigit() \
        else _NUMWORDS[mn.group(1)]
    step = _frac(md.group(1))
    if total is None or step is None:
        return None
    d = -step if md.group(2) == "less" else step
    a = total / n - Fraction(n - 1, 2) * d
    terms = [a + i * d for i in range(n)]
    if any(t <= 0 for t in terms):
        return None
    if _sn(a, d, n) != total:
        return None
    steps = [
        f"Let the first (largest) prize be Rs a. The prizes "
        f"form an AP with d = Rs {_fmtf(d)} and n = {n}.",
        f"S{n} = ({n}/2)[2a + {n - 1} x ({_fmtf(d)})] "
        f"= {_fmtf(total)}, so a = {_fmtf(a)}.",
        "The prizes are: " + ", ".join(
            f"Rs {_fmtf(t)}" for t in terms) + ".",
    ]
    final = ", ".join(f"Rs {_fmtf(t)}" for t in terms)
    return _result("sequences", "w195_ap_prizes", final, steps)


def _ap_houses(q, ql):
    m = re.search(r"numbered consecutively from 1 to (\d+)",
                  ql)
    if not m or "preceding" not in ql or "following" not in ql:
        return None
    big_n = int(m.group(1))
    total = big_n * (big_n + 1) // 2
    r = int(sp.sqrt(total))
    if r * r != total or not (1 < r < big_n):
        return None
    x = r
    before = (x - 1) * x // 2
    after = total - x * (x + 1) // 2
    if before != after:
        return None
    steps = [
        "The house numbers 1, 2, ..., "
        f"{big_n} form an AP with a = 1, d = 1.",
        f"Sum before house x = (x - 1)x/2 and sum after it "
        f"= {total} - x(x + 1)/2; equating them gives "
        f"x^2 = {total}.",
        f"So x = {x} (check: sum before = {before}, sum "
        f"after = {after}).",
    ]
    return _result("sequences", "w195_ap_houses", f"x = {x}",
                   steps)


def _ap_logs(q, ql):
    if "stack" not in ql or "bottom row" not in ql:
        return None
    mt = re.search(r"(\d+)\s+logs?\s+(?:are\s+)?stacked", ql)
    mb = re.search(r"(\d+)\s+logs?\s+in the bottom row", ql)
    if not (mt and mb):
        return None
    total, bottom = int(mt.group(1)), int(mb.group(1))
    mn = re.search(r"(\d+)\s+in the next row", ql)
    if mn and int(mn.group(1)) != bottom - 1:
        return None
    if "rows" not in ql:
        return None
    # S_n with a = bottom, d = -1: n^2 - (2*bottom+1)n + 2T = 0
    disc = (2 * bottom + 1) ** 2 - 8 * total
    if disc < 0:
        return None
    r = int(sp.sqrt(disc))
    if r * r != disc:
        return None
    valid = []
    for sgn in (1, -1):
        num = (2 * bottom + 1) + sgn * r
        if num % 2 == 0:
            n = num // 2
            top = bottom - (n - 1)
            if n >= 1 and top >= 1 and \
                    _sn(Fraction(bottom), Fraction(-1), n) \
                    == total:
                valid.append((n, top))
    if len(valid) != 1:
        return None
    n, top = valid[0]
    steps = [
        f"The rows form an AP with a = {bottom}, d = -1 and "
        f"sum = {total}.",
        f"Solving ({n}/2)[2 x {bottom} + {n - 1} x (-1)] "
        f"= {total} gives n = {n} rows.",
        f"Logs in the top row = {bottom} + {n - 1} x (-1) "
        f"= {top}.",
    ]
    return _result("sequences", "w195_ap_logs",
                   f"{n} rows, {top} logs in the top row",
                   steps)


def _ap_reverse_sn(q, ql):
    if "sum of" not in ql or "first n terms" not in ql:
        return None
    if "ap" not in ql and "arithmetic progression" not in ql:
        return None
    m = re.search(r"sum of (?:the )?first n terms of an? "
                  r"(?:ap|arithmetic progression) is\s+"
                  r"([^.,;]+)", ql)
    if not m:
        return None
    expr_text = m.group(1).strip()
    n_sym = sp.Symbol("n")
    try:
        expr = parse_expression(expr_text)
    except Exception:
        return None
    if isinstance(expr, tuple) or expr.free_symbols != {n_sym}:
        return None
    if sp.Poly(expr, n_sym).degree() > 2:
        return None

    def s(k):
        return sp.simplify(expr.subs(n_sym, k))

    parts = []
    steps = [f"S_n = {fmt(expr)}."]
    if "first term" in ql:
        parts.append(f"first term = {fmt(s(1))}")
        steps.append(f"First term = S_1 = {fmt(s(1))}.")
    if "sum of first two terms" in ql:
        parts.append(f"sum of first two terms = {fmt(s(2))}")
        steps.append(f"Sum of first two terms = S_2 "
                     f"= {fmt(s(2))}.")
    a_n_expr = sp.simplify(expr - expr.subs(n_sym, n_sym - 1))
    asked_k = []
    if "term" in ql:
        for km in re.finditer(r"(\d+)(?:st|nd|rd|th)\b", ql):
            k = int(km.group(1))
            if k >= 2 and k not in asked_k:
                asked_k.append(k)
    for k in asked_k:
        ak = sp.simplify(s(k) - s(k - 1))
        suf = {1: "st", 2: "nd", 3: "rd"}.get(k, "th")
        ordl = f"{k}{suf} term"
        parts.append(f"{ordl} = {fmt(ak)}")
        steps.append(f"{ordl} = S_{k} - S_{k - 1} = {fmt(ak)}.")
    if "nth term" in ql:
        parts.append(f"nth term = {fmt(a_n_expr)}")
        steps.append(f"nth term = S_n - S_(n-1) "
                     f"= {fmt(a_n_expr)}.")
    if "common difference" in ql:
        d = sp.simplify((s(2) - s(1)) - s(1))
        parts.append(f"common difference = {fmt(d)}")
        steps.append(f"Common difference = a_2 - a_1 = {fmt(d)}.")
    if not parts:
        return None
    return _result("sequences", "w195_ap_reverse_sn",
                   ", ".join(parts), steps)


def _ap_missing_terms(q, ql):
    if "ap" not in ql and "arithmetic progression" not in ql:
        return None
    if "_" not in q and "□" not in q:
        return None
    if "missing" not in ql and "insert" not in ql \
            and "boxes" not in ql:
        return None
    region = q.rsplit(":", 1)[-1] if ":" in q else q
    tokens = re.findall(r"-?\d+(?:\.\d+)?|_{1,}|□", region)
    if len(tokens) < 3:
        return None
    seq = []
    for t in tokens:
        if t.startswith("_") or t == "□":
            seq.append(None)
        else:
            v = _frac(t)
            if v is None:
                return None
            seq.append(v)
    anchors = [(i, v) for i, v in enumerate(seq) if v is not None]
    if len(anchors) < 2 or len(anchors) == len(seq):
        return None
    (i0, v0), (i1, v1) = anchors[0], anchors[-1]
    d = (v1 - v0) / (i1 - i0)
    a = v0 - i0 * d
    if any(v != a + i * d for i, v in anchors):
        return None
    filled = [a + i * d for i in range(len(seq))]
    steps = [
        f"The terms are in AP; using the first and last "
        f"known terms, d = ({_fmtf(v1)} - {_fmtf(v0)}) / "
        f"{i1 - i0} = {_fmtf(d)}.",
        "The completed AP is: " + ", ".join(
            _fmtf(v) for v in filled) + ".",
    ]
    missing = [f"{_fmtf(filled[i])}"
               for i, v in enumerate(seq) if v is None]
    return _result("sequences", "w195_ap_missing_terms",
                   ", ".join(missing), steps)


def _ap_table(q, ql):
    if "ap" not in ql and "arithmetic progression" not in ql:
        return None
    if "find" not in ql and "determine" not in ql:
        return None
    known = {}
    ma = re.search(r"(?<![a-z0-9])a\s*=\s*(-?\d+(?:\.\d+)?)",
                   ql)
    md = re.search(r"(?<![a-z0-9])d\s*=\s*(-?\d+(?:\.\d+)?)",
                   ql)
    mn = re.search(r"(?<![a-z0-9_])n\s*=\s*(\d+)", ql)
    if ma:
        known["a"] = _frac(ma.group(1))
    if md:
        known["d"] = _frac(md.group(1))
    if mn:
        known["n"] = int(mn.group(1))
    terms_k = {}
    for m in re.finditer(r"a_?\{?(\d+)\}?\s*=\s*"
                         r"(-?\d+(?:\.\d+)?)", ql):
        terms_k[int(m.group(1))] = _frac(m.group(2))
    sums_k = {}
    for m in re.finditer(r"s_?\{?(\d+)\}?\s*=\s*"
                         r"(-?\d+(?:\.\d+)?)", ql):
        sums_k[int(m.group(1))] = _frac(m.group(2))
    n_assign = len(known) + len(terms_k) + len(sums_k)
    if n_assign < 2:
        return None
    # Solve for a and d from the linear equations.
    A, D = sp.symbols("A D")
    eqs = []
    if "a" in known:
        eqs.append(sp.Eq(A, sp.Rational(known["a"].numerator,
                                        known["a"].denominator)))
    if "d" in known:
        eqs.append(sp.Eq(D, sp.Rational(known["d"].numerator,
                                        known["d"].denominator)))
    for k, v in terms_k.items():
        eqs.append(sp.Eq(A + (k - 1) * D,
                         sp.Rational(v.numerator, v.denominator)))
    for k, v in sums_k.items():
        eqs.append(sp.Eq(sp.Rational(k, 2) * (2 * A + (k - 1) * D),
                         sp.Rational(v.numerator, v.denominator)))
    try:
        sols = sp.solve(eqs, (A, D), dict=True)
    except Exception:
        return None
    if len(sols) != 1:
        return None
    sol = sols[0]
    a_val = sol.get(A)
    d_val = sol.get(D)
    if a_val is None or d_val is None or a_val.free_symbols \
            or d_val.free_symbols:
        return None
    a_f = Fraction(a_val) if a_val.is_rational else None
    d_f = Fraction(d_val) if d_val.is_rational else None
    if a_f is None or d_f is None:
        return None
    # Verify every given against the solved a, d.
    for k, v in terms_k.items():
        if a_f + (k - 1) * d_f != v:
            return None
    for k, v in sums_k.items():
        if _sn(a_f, d_f, k) != v:
            return None
    n_known = known.get("n")
    parts = []
    steps = [f"For the AP, a = {_fmtf(a_f)} and "
             f"d = {_fmtf(d_f)}."]
    if re.search(r"find[^.,;]*?\bd\b", ql) \
            or "common difference" in ql:
        if "d" not in known:
            parts.append(f"d = {_fmtf(d_f)}")
    if re.search(r"find[^.,;]*?\ba\b", ql) or \
            "first term" in ql:
        if "a" not in known:
            parts.append(f"a = {_fmtf(a_f)}")
    man = re.search(r"find[^.,;]*?a_?\{?(\d+)\}?", ql)
    if man:
        k = int(man.group(1))
        if k not in terms_k:
            parts.append(f"a{k} = {_fmtf(a_f + (k - 1) * d_f)}")
            steps.append(f"a{k} = a + {k - 1}d "
                         f"= {_fmtf(a_f + (k - 1) * d_f)}.")
    elif ("find an" in ql.replace("_", "") or "find a_n" in ql
          or "find the nth term" in ql) and n_known:
        k = n_known
        parts.append(f"a{k} = {_fmtf(a_f + (k - 1) * d_f)}")
        steps.append(f"a_n with n = {k}: a + (n - 1)d "
                     f"= {_fmtf(a_f + (k - 1) * d_f)}.")
    msn = re.search(r"find[^.,;]*?s_?\{?(\d+)\}?", ql)
    if msn:
        k = int(msn.group(1))
        if k not in sums_k:
            parts.append(f"S{k} = {_fmtf(_sn(a_f, d_f, k))}")
            steps.append(f"S{k} = ({k}/2)[2a + {k - 1}d] "
                         f"= {_fmtf(_sn(a_f, d_f, k))}.")
    elif (re.search(r"find[^.,;]*?\bs_?n\b", ql)
          or "find the sum" in ql) and n_known:
        k = n_known
        if k not in sums_k:
            parts.append(f"S{k} = {_fmtf(_sn(a_f, d_f, k))}")
            steps.append(f"S{k} = ({k}/2)[2a + {k - 1}d] "
                         f"= {_fmtf(_sn(a_f, d_f, k))}.")
    if "find n" in ql and n_known is None:
        # n from a given a_k term value is already encoded;
        # only the a, d, a_n dress reaches here.
        target = None
        mt = re.search(r"a_?n\s*=\s*(-?\d+(?:\.\d+)?)", ql)
        if mt:
            target = _frac(mt.group(1))
        if target is not None and d_f != 0:
            nv = (target - a_f) / d_f + 1
            if nv.denominator == 1 and nv >= 1:
                parts.append(f"n = {int(nv)}")
                steps.append(f"n = (a_n - a)/d + 1 = {int(nv)}.")
    if not parts:
        return None
    return _result("sequences", "w195_ap_table",
                   ", ".join(parts), steps)


def _ap_series_find_d(q, ql):
    if "ap" not in ql and "arithmetic progression" not in ql:
        return None
    if "common difference" not in ql and not re.search(
            r"find (?:the )?(?:value of )?d\b", ql):
        return None
    m = re.search(r"(?:ap|arithmetic progression)\s*:?\s*"
                  r"(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)"
                  r"{2,})", ql)
    if not m:
        return None
    terms = [_frac(t) for t in m.group(1).split(",")]
    if any(t is None for t in terms) or len(terms) < 3:
        return None
    diffs = {terms[i + 1] - terms[i] for i in range(len(terms) - 1)}
    if len(diffs) != 1:
        return None
    d = diffs.pop()
    steps = [
        "Successive differences: " + ", ".join(
            f"{_fmtf(terms[i + 1])} - {_fmtf(terms[i])} "
            f"= {_fmtf(d)}" for i in range(len(terms) - 1))
        + " — constant, so it is an AP.",
    ]
    return _result("sequences", "w195_ap_series_d",
                   f"d = {_fmtf(d)}", steps)


_AP_FNS = (_ap_penalty, _ap_savings_target, _ap_prizes,
           _ap_houses, _ap_logs, _ap_reverse_sn,
           _ap_missing_terms, _ap_table, _ap_series_find_d)


# ------------------------------------------------------------------
# entry point + fragment-displacement predicate
# ------------------------------------------------------------------

_ALL_FNS = _COORD_FNS + _TRIG_FNS + _AP_FNS


def solve_c10pack195(question):
    """Wave 195 Class 10 special-form schemas; None unless a
    strict schema settles the question completely with
    exactly verified values."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip():
        return None
    ql = q.lower()
    if any(v in ql for v in _CONCEPT_VETO):
        return None
    for fn in _ALL_FNS:
        try:
            out = fn(q, ql)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


_RATIO_ASSIGN_RE = re.compile(
    r"(sin|cos|tan|sec|cosec|csc|cot)\s+\S+\s*=\s*([^\s,;]+)")


def _ratio_map(text):
    out = {}
    for m in _RATIO_ASSIGN_RE.finditer(str(text or "")):
        f = m.group(1).lower()
        if f == "csc":
            f = "cosec"
        try:
            out[f] = float(sp.N(parse_expression(m.group(2))))
        except Exception:
            pass
    return out


def w195_displaces(question, result, cand):
    """True when the primary result is a measured Wave 195
    fragment / wrong serve for a question the strict schema
    (cand) settles completely: an echoed given value under
    op 'evaluate', a wrapper equation under op 'equation',
    or a ratio_from_ratio serve that misses a requested
    ratio or disagrees numerically with the verified
    candidate on a shared ratio.  Identical answers never
    displace."""
    if not isinstance(result, dict) or not isinstance(cand, dict):
        return False
    pans = str(result.get("answer", "") or "").strip()
    cans = str(cand.get("answer", "") or "").strip()
    if not pans or not cans or pans == cans:
        return False
    op = result.get("op")
    cop = str(cand.get("op", ""))
    if cop.startswith("w195_trig"):
        if op in ("evaluate", "equation"):
            return True
        if op == "ratio_from_ratio":
            pm = _ratio_map(pans)
            cm = _ratio_map(cans)
            if not cm:
                return False
            if any(f not in pm for f in cm):
                return True
            return any(abs(pm[f] - cm[f]) > 1e-6
                       for f in cm if f in pm)
        return False
    if cop in ("w195_ap_fraction_point", "w195_ap_table"):
        return op in ("evaluate", "equation")
    return False
