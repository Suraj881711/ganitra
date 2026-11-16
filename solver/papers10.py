"""Wave 94: Class 10 board-paper method schemas.

The Wave 71 solver-health audit found the board-papers surface
the weakest in the app, and its Class 10 half (89 sampled
questions, 62 failures) concentrated in a set of perfectly
general NCERT method families the solver simply had no schema
for: midpoint / axis-division / collinearity in coordinate
geometry, AP term-existence and term-count, zeros relations
(α² + β²), degree of a product of polynomials, equal-roots
parameters, "which of the following …" fact MCQs (terminating
decimals, co-prime pairs, unit-digit cycles, complementary-angle
relations, formula MCQs), tangent-length geometry, the
lamp-post shadow, two-angle heights and distances, modal-class
reading of a text table, dice-outcome counting, and a handful of
standard mensuration forms (semicircle perimeter, cylinder/cone
volume ratio, CSA-given-radius, wire-bent-to-arc).

Every schema here is a METHOD, not a per-question patch: it
parses the student's own numbers/letters out of the question and
computes. The fact-MCQ schemas never guess an option — they
VERIFY each option against the mathematics (gcd, decimal
denominator test, unit-digit cycle, symbolic identity check)
and answer only when exactly one option passes.

Hooking: solver/router.py calls solve_papers10 at the very end
of _solve_question_uncached, only when the primary result is a
failure or letter-soup (the Wave 77 gate), so a question the
solver already answers is never displaced — this module only
converts failures. Schemas fire on the full question (options
included, for the verifiers) and equally on an option-stripped
MCQ stem handed over by mcq.py's stem solver.
"""

import math
import re
from fractions import Fraction

from .expression_parser import extract_points, fmt_num

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")


def _prep(q):
    """Surface normalisation shared by every schema: ASCII
    operators and digits, so the parsers below see one shape."""
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("°", "°")
    return s


def _hindi(q):
    return any("ऀ" <= ch <= "ॿ" for ch in str(q or ""))


def _mk(type_, op, answer, steps):
    return {"type": type_, "op": op, "answer": answer,
            "steps": steps}


def _frac(value):
    """Exact Fraction for an int/float/str number."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        return Fraction(value).limit_denominator(10 ** 6)
    return Fraction(value)


def _fmt_frac(fr):
    fr = _frac(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _sqrt_str(n):
    """'√119' style exact form for a non-square positive number,
    with the square factor pulled out ('√72' -> '6√2')."""
    n = int(n)
    if n < 0:
        return f"√({n})"
    root = int(math.isqrt(n))
    if root * root == n:
        return str(root)
    k = root
    while k > 1:
        if n % (k * k) == 0:
            return f"{k}√{n // (k * k)}"
        k -= 1
    return f"√{n}"


def _options(q):
    """(stem, [(label, text), ...]) via the Wave 76 extractor,
    or None. Lazy import: mcq imports the router, the router
    imports this module — a top-level import would cycle."""
    try:
        from mcq import extract_mcq
        return extract_mcq(q)
    except Exception:
        return None


def _sympify(text):
    """Best-effort SymPy parse of an option/expression string
    in board notation (juxtaposition means multiplication:
    '2a', 'n(n + 1)', '5(9x² - 4)'). Returns None when it
    does not parse."""
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor)
    s = str(text)
    s = s.replace("²", "**2").replace("³", "**3")
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/")
    s = s.replace("{", "(").replace("}", ")")
    s = s.replace("π", "pi").replace("√", "sqrt")
    # '2piR' would tokenise as one name — split pi out of
    # digit/letter juxtapositions first.
    s = re.sub(r"(\d)pi", r"\1*pi", s)
    s = re.sub(r"pi(?=[A-Za-z])", "pi*", s)
    s = re.sub(r"(?<=[A-Za-z])pi(?![A-Za-z])", "*pi", s)
    try:
        return parse_expr(
            s, transformations=standard_transformations + (
                implicit_multiplication_application, convert_xor),
            evaluate=True)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Coordinate geometry
# ---------------------------------------------------------------------------

def _midpoint(q):
    if not re.search(r"mid[\s-]?point|मध्य\s?बि[ंन]दु", q, re.I):
        return None
    pts = extract_points(q)
    if len(pts) < 2:
        return None
    (x1, y1), (x2, y2) = pts[0], pts[1]
    mx = _fmt_frac((_frac(x1) + _frac(x2)) / 2)
    my = _fmt_frac((_frac(y1) + _frac(y2)) / 2)
    hi = _hindi(q)
    steps = [
        ("मध्य बिंदु = ((x1 + x2)/2, (y1 + y2)/2)"
         if hi else
         "Midpoint = ((x1 + x2)/2, (y1 + y2)/2)"),
        f"= (({fmt_num(x1)} + {fmt_num(x2)})/2, "
        f"({fmt_num(y1)} + {fmt_num(y2)})/2) = ({mx}, {my})",
    ]
    return _mk("geometry", "w94_midpoint", f"({mx}, {my})", steps)


def _axis_division_ratio(q):
    """In what ratio does the x-axis (or y-axis) divide the
    segment joining two points? The dividing point has
    y = 0 (x-axis) resp. x = 0 (y-axis), so by the section
    formula the ratio is -y1 : y2 resp. -x1 : x2."""
    axis = None
    if re.search(r"x[\s-]?axis|x-अक्ष", q, re.I):
        axis = "x"
    elif re.search(r"y[\s-]?axis|y-अक्ष", q, re.I):
        axis = "y"
    if axis is None:
        return None
    if not re.search(r"ratio|अनुपात|divide|विभाजित|विभाजन", q, re.I):
        return None
    pts = extract_points(q)
    if len(pts) < 2:
        return None
    (x1, y1), (x2, y2) = pts[0], pts[1]
    a, b = (-_frac(y1), _frac(y2)) if axis == "x" \
        else (-_frac(x1), _frac(x2))
    if b == 0:
        return None
    # m : n = a : b as a single fraction; a positive value is
    # an internal division, a negative one external.
    r = a / b
    ai, bi = abs(r.numerator), abs(r.denominator)
    external = r < 0
    hi = _hindi(q)
    coord = "y" if axis == "x" else "x"
    c1, c2 = (y1, y2) if axis == "x" else (x1, x2)
    steps = [
        (f"{axis}-अक्ष पर स्थित बिंदु का {coord}-निर्देशांक 0 होता है।"
         if hi else
         f"On the {axis}-axis the {coord}-coordinate is 0."),
        ("अनुपात m : n में विभाजन पर "
         f"{coord} = (m·{coord}2 + n·{coord}1)/(m + n) = 0, "
         f"इसलिए m : n = -{coord}1 : {coord}2"
         if hi else
         f"Section formula: {coord} = (m·{coord}2 + n·{coord}1)"
         f"/(m + n) = 0, so m : n = -{coord}1 : {coord}2"),
        f"= -({fmt_num(c1)}) : {fmt_num(c2)} = {ai} : {bi}"
        + (" (externally)" if external else ""),
    ]
    ans = f"{ai} : {bi}" + (" (externally)" if external else "")
    return _mk("geometry", "w94_axis_division", ans, steps)


_PT_LETTER = re.compile(
    r"\(\s*(-?\d+(?:\.\d+)?|[a-zA-Z])\s*,\s*"
    r"(-?\d+(?:\.\d+)?|[a-zA-Z])\s*\)")


def _collinear_unknown(q):
    """Three points, one coordinate a letter, points collinear:
    the triangle area is zero — solve for the letter."""
    if not re.search(r"collinear|संरेख|समरेख|एक\s?रेखीय", q, re.I):
        return None
    raw = _PT_LETTER.findall(q)
    if len(raw) < 3:
        return None
    pts = raw[:3]
    letters = [(i, j) for i, p in enumerate(pts)
               for j in (0, 1) if p[j].isalpha()]
    if len(letters) != 1:
        return None
    (pi, pj) = letters[0]
    letter = pts[pi][pj]
    vals = []
    for i, p in enumerate(pts):
        row = []
        for j in (0, 1):
            row.append(None if (i, j) == (pi, pj)
                       else _frac(p[j]))
        vals.append(row)
    (x1, y1), (x2, y2), (x3, y3) = vals
    # area = (1/2)|x1(y2-y3) + x2(y3-y1) + x3(y1-y2)| = 0.
    # The unknown appears linearly: value = coef * t + const.
    def term(coord_i, coord_j, other):
        # placeholder, replaced below by direct algebra
        return None
    # Direct linear solve: substitute t symbolically via two
    # evaluations (the expression is linear in t).
    def area2(t):
        vv = [[(t if (i, j) == (pi, pj) else vals[i][j])
               for j in (0, 1)] for i in range(3)]
        (a1, b1), (a2, b2), (a3, b3) = vv
        return (a1 * (b2 - b3) + a2 * (b3 - b1)
                + a3 * (b1 - b2))
    c0 = area2(Fraction(0))
    c1 = area2(Fraction(1)) - c0
    if c1 == 0:
        return None
    t = -c0 / c1
    hi = _hindi(q)
    steps = [
        ("तीनों बिंदु संरेख हैं, इसलिए उनसे बने त्रिभुज का "
         "क्षेत्रफल 0 है।"
         if hi else
         "The points are collinear, so the area of the triangle "
         "they form is 0."),
        "Area = (1/2)|x1(y2 - y3) + x2(y3 - y1) + x3(y1 - y2)| = 0",
        f"{letter} = {_fmt_frac(t)}",
    ]
    return _mk("geometry", "w94_collinear_unknown",
               f"{letter} = {_fmt_frac(t)}", steps)


def _axis_fact(q):
    """Points on the x-axis have ordinate (y-coordinate) 0;
    points on the y-axis have abscissa (x-coordinate) 0."""
    on_x = re.search(r"x[\s-]?axis|x-अक्ष", q, re.I)
    on_y = re.search(r"y[\s-]?axis|y-अक्ष", q, re.I)
    asks_y = re.search(r"ordinate|कोटि|y[\s-]?coordinate|"
                       r"y[\s-]?निर्देशांक", q, re.I)
    asks_x = re.search(r"abscissa|भुज|x[\s-]?coordinate|"
                       r"x[\s-]?निर्देशांक", q, re.I)
    hi = _hindi(q)
    if on_x and asks_y:
        steps = ["x-अक्ष पर स्थित प्रत्येक बिंदु की ऊँचाई (y-निर्देशांक) 0 होती है।"
                 if hi else
                 "Every point on the x-axis has height "
                 "(y-coordinate) 0."]
        return _mk("geometry", "w94_axis_fact", "0", steps)
    if on_y and asks_x:
        steps = ["y-अक्ष पर स्थित प्रत्येक बिंदु की x-निर्देशांक 0 होती है।"
                 if hi else
                 "Every point on the y-axis has x-coordinate 0."]
        return _mk("geometry", "w94_axis_fact", "0", steps)
    return None


# ---------------------------------------------------------------------------
# Arithmetic progressions
# ---------------------------------------------------------------------------

_SERIES_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?)(?:\s*,\s*(-?\d+(?:\.\d+)?))?")


def _series(q):
    """(a, d, last_or_None) from an explicit numeric series."""
    m = _SERIES_RE.search(q)
    if not m:
        return None
    a = _frac(m.group(1))
    b = _frac(m.group(2))
    c = _frac(m.group(3))
    d = b - a
    if c - b != d:
        return None
    return a, d


def _ap_term_check(q):
    """'Check whether T is a term of a, a+d, a+2d, …' —
    T is a term iff (T - a)/d is a whole number >= 0."""
    if not re.search(r"\bterm\b|पद\b", q):
        return None
    if not re.search(r"check|whether|is\s+(-?\d|the)|क्या|जाँच|"
                     r"बताइए", q, re.I):
        return None
    s = _series(q)
    if s is None:
        return None
    a, d = s
    if d == 0:
        return None
    # the target: the number right before "is a term" / after
    # "whether" / "check whether"
    m = re.search(r"(?:whether|check\s+whether|क्या)\s+"
                  r"(-?\d+(?:\.\d+)?)", q, re.I)
    if m is None:
        m = re.search(r"(-?\d+(?:\.\d+)?)\s+is\s+a\s+term", q,
                      re.I)
    if m is None:
        return None
    t = _frac(m.group(1))
    n_minus_1 = (t - a) / d
    hi = _hindi(q)
    if n_minus_1.denominator == 1 and n_minus_1 >= 0:
        n = int(n_minus_1) + 1
        steps = [
            f"a = {_fmt_frac(a)}, d = {_fmt_frac(d)}",
            f"a_n = a + (n - 1)d: {_fmt_frac(t)} = "
            f"{_fmt_frac(a)} + (n - 1)({_fmt_frac(d)})",
            f"n - 1 = {_fmt_frac(n_minus_1)}, so n = {n}",
        ]
        ans = (f"Yes, {_fmt_frac(t)} is the {n}th term"
               if not hi else
               f"हाँ, {_fmt_frac(t)} इस श्रेढ़ी का {n}वाँ पद है")
        return _mk("sequences", "w94_ap_term_check", ans, steps)
    steps = [
        f"a = {_fmt_frac(a)}, d = {_fmt_frac(d)}",
        f"a_n = a + (n - 1)d: {_fmt_frac(t)} = "
        f"{_fmt_frac(a)} + (n - 1)({_fmt_frac(d)})",
        f"n - 1 = {_fmt_frac(n_minus_1)} — not a whole number",
    ]
    ans = (f"No, {_fmt_frac(t)} is not a term of this AP"
           if not hi else
           f"नहीं, {_fmt_frac(t)} इस श्रेढ़ी का पद नहीं है")
    return _mk("sequences", "w94_ap_term_check", ans, steps)


def _ap_term_count(q):
    """'How many terms in a, …, l?' / 'पदों की संख्या' —
    n = (l - a)/d + 1."""
    if not re.search(r"how many terms|number of terms|"
                     r"पदों की संख्या|कितने पद", q, re.I):
        return None
    s = _series(q)
    if s is None:
        return None
    a, d = s
    if d == 0:
        return None
    # last term: the number right before the end/ellipsis tail
    tail = re.findall(r"(-?\d+(?:\.\d+)?)", q)
    if len(tail) < 4:
        return None
    last = _frac(tail[-1])
    if last == a:
        return None
    n_minus_1 = (last - a) / d
    if n_minus_1.denominator != 1 or n_minus_1 < 0:
        return None
    n = int(n_minus_1) + 1
    hi = _hindi(q)
    steps = [
        f"a = {_fmt_frac(a)}, d = {_fmt_frac(d)}, "
        f"last term l = {_fmt_frac(last)}",
        "l = a + (n - 1)d",
        f"{_fmt_frac(last)} = {_fmt_frac(a)} + (n - 1)"
        f"({_fmt_frac(d)}), so n - 1 = {_fmt_frac(n_minus_1)}",
        f"n = {n}",
    ]
    return _mk("sequences", "w94_ap_term_count", str(n), steps)


def _ap_sum_fact(q):
    """Formula facts: sum of the first n odd / even / natural
    numbers, and the AP sum formula in a and d. These arrive as
    MCQs whose options are the formulas themselves; the computed
    formula is the answer (mcq matching names the option)."""
    low = q.lower()
    if re.search(r"sum of (the )?first n odd|प्रथम n विषम|"
                 r"पहली n विषम", low):
        return _mk("sequences", "w94_ap_sum_fact", "n^2", [
            "The first n odd numbers are 1, 3, 5, …, (2n - 1) "
            "— an AP with a = 1, d = 2.",
            "Sum = (n/2)(2a + (n - 1)d) = (n/2)(2 + 2n - 2) = n^2",
        ])
    if re.search(r"sum of (the )?first n even|प्रथम n सम\b|"
                 r"पहली n सम\b", low):
        return _mk("sequences", "w94_ap_sum_fact", "n(n + 1)", [
            "The first n even numbers are 2, 4, 6, …, 2n "
            "— an AP with a = 2, d = 2.",
            "Sum = (n/2)(2a + (n - 1)d) = (n/2)(2n + 2) "
            "= n(n + 1)",
        ])
    got = _options(q)
    if got is not None:
        _stem, options = got
        texts = " ".join(t for _l, t in options)
        if "a" in texts and "d" in texts and re.search(
                r"sum|योगफल|योग", q, re.I) and re.search(
                r"first term|पहला पद|प्रथम पद|common difference|"
                r"सार्व\s?अंतर|सार्वअंतर", q, re.I):
            import sympy as sp
            n, a, d = sp.symbols("n a d")
            target = (n / 2) * (2 * a + (n - 1) * d)
            hits = []
            for label, text in options:
                expr = _sympify(text)
                if expr is None:
                    continue
                try:
                    if sp.simplify(expr - target) == 0:
                        hits.append((label, text))
                except Exception:
                    continue
            if len(hits) == 1:
                label, text = hits[0]
                steps = [
                    "S_n = (n/2)(2a + (n - 1)d) — the sum of "
                    "the first n terms of an AP.",
                    f"Only option ({label}) equals this: {text}",
                ]
                return _mk("sequences", "w94_ap_sum_fact",
                           f"({label}) {text}", steps)
    return None


# ---------------------------------------------------------------------------
# Polynomials: zeros relations, degree, polynomial from zeros
# ---------------------------------------------------------------------------

def _quad_coeffs(q):
    """(a, b, c) Fractions of a quadratic written in the text:
    '5x² - 7x + 1', '5x^2 - 7x + 1', 'kx(x - 2) + 6' excluded."""
    s = q.replace("²", "^2").replace("−", "-")
    m = re.search(
        r"(-?\d+(?:\.\d+)?(?:/\d+)?)?\s*x\^2\s*"
        r"(?:([+-])\s*(\d+(?:\.\d+)?(?:/\d+)?)\s*x)?\s*"
        r"(?:([+-])\s*(\d+(?:\.\d+)?(?:/\d+)?))?", s)
    if not m:
        return None
    def coef(txt, sign=None):
        if txt is None or txt == "":
            v = Fraction(1)
        elif "/" in txt:
            num, den = txt.split("/", 1)
            v = Fraction(int(num), int(den))
        elif "." in txt:
            v = Fraction(txt)
        else:
            v = Fraction(int(txt))
        if sign == "-":
            v = -v
        return v
    a = coef(m.group(1))
    if m.group(1) and m.group(1).startswith("-"):
        a = -abs(a) if m.group(1) != "-" else Fraction(-1)
    if m.group(1) == "-":
        a = Fraction(-1)
    b = coef(m.group(3), m.group(2)) if m.group(2) else Fraction(0)
    c = coef(m.group(5), m.group(4)) if m.group(4) else Fraction(0)
    if a == 0:
        return None
    return a, b, c


def _zeros_relations(q):
    """α + β = -b/a, αβ = c/a; answer α² + β², 1/α + 1/β,
    α³ + β³, (α - β)² style asks about a stated quadratic."""
    if not re.search(r"zeros|zeroes|शून्यक", q, re.I):
        return None
    coeffs = _quad_coeffs(q)
    if coeffs is None:
        return None
    a, b, c = coeffs
    s = -b / a          # α + β
    p = c / a           # αβ
    asks = [
        (r"α²\s*\+\s*β²|α\^2\s*\+\s*β\^2|a\^2\s*\+\s*b\^2",
         "α² + β²", s * s - 2 * p,
         f"(α + β)² - 2αβ = ({_fmt_frac(s)})² - 2"
         f"({_fmt_frac(p)})"),
        (r"1/α\s*\+\s*1/β|1/a\s*\+\s*1/b",
         "1/α + 1/β", (s / p) if p != 0 else None,
         f"(α + β)/αβ = ({_fmt_frac(s)})/({_fmt_frac(p)})"),
        (r"α³\s*\+\s*β³|α\^3\s*\+\s*β\^3",
         "α³ + β³", s ** 3 - 3 * p * s,
         f"(α + β)³ - 3αβ(α + β) = ({_fmt_frac(s)})³ - 3"
         f"({_fmt_frac(p)})({_fmt_frac(s)})"),
        (r"\(α\s*-\s*β\)²|\(a\s*-\s*b\)\^2",
         "(α - β)²", s * s - 4 * p,
         f"(α + β)² - 4αβ = ({_fmt_frac(s)})² - 4"
         f"({_fmt_frac(p)})"),
    ]
    for pat, name, val, work in asks:
        if val is None:
            continue
        if re.search(pat, q):
            steps = [
                f"α + β = -b/a = {_fmt_frac(s)}, "
                f"αβ = c/a = {_fmt_frac(p)}",
                f"{name} = {work} = {_fmt_frac(val)}",
            ]
            return _mk("algebra", "w94_zeros_relation",
                       _fmt_frac(val), steps)
    return None


def _poly_degree(q):
    """Degree of a polynomial expression, incl. products:
    '(x + 3)²(x³ - 8) का घात' -> 2 + 3 = 5."""
    if not re.search(r"\bdegree\b|का घात|की घात|"
                     r"घात\s*(है|ज्ञात|क्या|बताइ)", q, re.I):
        return None
    import sympy as sp
    x = sp.symbols("x")
    # candidate expression: the longest maths-looking chunk
    s = q.replace("−", "-")
    m = re.search(r"\(?[a-z0-9x\s\+\-\*/\^²³()]+\)?", s)
    cands = re.findall(r"[\(]?[x\d][x\d\s\+\-\*/\^²³()]*", s)
    cands = [c.strip() for c in cands if "x" in c and len(c) >= 3]
    if not cands:
        return None
    expr_text = max(cands, key=len)
    expr = _sympify(expr_text)
    if expr is None:
        return None
    try:
        deg = sp.Poly(expr, x).degree()
    except Exception:
        return None
    if deg is None:
        return None
    steps = [
        f"Expand: {expr_text} = {sp.expand(expr)}",
        f"The highest power of x is {deg}.",
    ]
    return _mk("algebra", "w94_poly_degree", str(deg), steps)


def _poly_from_zeros_mcq(q):
    """'Which polynomial has zeroes u and v?' — verify each
    option by substitution; exactly one may vanish at both."""
    if not re.search(r"zeroes|zeros|शून्यक", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    m = re.search(r"zeroes?\s+(?:are\s+)?(-?\d+(?:\.\d+)?"
                  r"(?:/\d+)?)\s+and\s+(-?\d+(?:\.\d+)?"
                  r"(?:/\d+)?)", q, re.I)
    if m is None:
        # zeroes written '−2/3 and 2/3' right before the options
        m = re.search(r"(-?\d+(?:\.\d+)?(?:/\d+)?)\s+and\s+"
                      r"(-?\d+(?:\.\d+)?(?:/\d+)?)\s*\?", q)
    if m is None:
        return None
    def parse(txt):
        txt = txt.strip()
        if "/" in txt:
            num, den = txt.split("/", 1)
            return Fraction(int(num), int(den))
        return Fraction(txt)
    z1, z2 = parse(m.group(1)), parse(m.group(2))
    import sympy as sp
    x = sp.symbols("x")
    hits = []
    for label, text in options:
        expr = _sympify(text)
        if expr is None or x not in expr.free_symbols:
            continue
        try:
            if sp.expand(expr.subs(x, sp.Rational(z1))) == 0 \
                    and sp.expand(
                        expr.subs(x, sp.Rational(z2))) == 0:
                hits.append((label, text))
        except Exception:
            continue
    if len(hits) != 1:
        return None
    label, text = hits[0]
    steps = [
        f"A polynomial with zeroes {_fmt_frac(z1)} and "
        f"{_fmt_frac(z2)} must vanish at both.",
        f"Checking the options: only ({label}) {text} gives 0 "
        f"at x = {_fmt_frac(z1)} and at x = {_fmt_frac(z2)}.",
    ]
    return _mk("algebra", "w94_poly_from_zeros",
               f"({label}) {text}", steps)


# ---------------------------------------------------------------------------
# "Which of the following …" fact verifiers
# ---------------------------------------------------------------------------

def _terminating_decimal(q):
    """A fraction has a terminating decimal iff its reduced
    denominator has no prime factors other than 2 and 5."""
    if not re.search(r"terminating decimal|सांत\s?दशमलव", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    def terminates(fr):
        den = fr.denominator
        for prime in (2, 5):
            while den % prime == 0:
                den //= prime
        return den == 1
    hits = []
    for label, text in options:
        m = re.fullmatch(r"\s*(-?\d+)\s*/\s*(\d+)\s*", text)
        if not m:
            continue
        fr = Fraction(int(m.group(1)), int(m.group(2)))
        if terminates(fr):
            hits.append((label, text, fr))
    if len(hits) != 1:
        return None
    label, text, fr = hits[0]
    steps = [
        "A fraction in lowest terms terminates exactly when "
        "its denominator has no prime factor other than 2 "
        "and 5.",
        f"{text} reduces to {_fmt_frac(fr)}; its denominator "
        f"{fr.denominator} has no prime factor other than "
        "2 and 5.",
        "Every other option keeps another prime factor in "
        "the denominator, so it recurs.",
    ]
    return _mk("number_theory", "w94_terminating_decimal",
               f"({label}) {text}", steps)


def _coprime_pair(q):
    """Co-prime pair: gcd of the two numbers is 1."""
    if not re.search(r"co[\s-]?prime|सह[\s-]?अभाज्य", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    hits = []
    for label, text in options:
        nums = re.findall(r"-?\d+", text)
        if len(nums) != 2:
            continue
        u, v = int(nums[0]), int(nums[1])
        if math.gcd(u, v) == 1:
            hits.append((label, text, u, v))
    if len(hits) != 1:
        return None
    label, text, u, v = hits[0]
    steps = [
        "Two numbers are co-prime when their HCF is 1.",
        f"HCF({u}, {v}) = 1; every other pair shares a "
        "common factor.",
    ]
    return _mk("number_theory", "w94_coprime_pair",
               f"({label}) {text}", steps)


def _unit_digit_cannot(q):
    """'Which cannot be the unit digit of b^n?' — the unit
    digits of b^1, b^2, … cycle; the option outside the cycle
    is the answer."""
    if not re.search(r"unit digit|इकाई\s?का\s?अंक|इकाई\s?अंक",
                     q, re.I):
        return None
    if not re.search(r"cannot|can\s?not|नहीं\s?हो\s?सकत", q, re.I):
        return None
    m = re.search(r"(\d)\s*\^\s*n|(\d)\s*ⁿ|(\d+) की घात", q)
    if m is None:
        m = re.search(r"(\d)\^", q)
    if m is None:
        return None
    base = int(next(g for g in m.groups() if g is not None))
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    cycle = []
    v = 1
    for _ in range(12):
        v = (v * base) % 10
        if v in cycle:
            break
        cycle.append(v)
    hits = []
    for label, text in options:
        t = text.strip()
        if re.fullmatch(r"\d", t) and int(t) not in cycle:
            hits.append((label, t))
    if len(hits) != 1:
        return None
    label, t = hits[0]
    steps = [
        f"The unit digits of {base}^n cycle through "
        f"{', '.join(str(c) for c in cycle)}.",
        f"{t} never appears in the cycle.",
    ]
    return _mk("number_theory", "w94_unit_digit",
               f"({label}) {t}", steps)


def _prob_pq_relation(q):
    """p = P(event), q = P(not event): the relation is
    p + q = 1. Verify the options symbolically."""
    if not re.search(r"probability|प्रायिकता", q, re.I):
        return None
    if not re.search(r"non[\s-]?happening|not\s+happen|"
                     r"न\s?होने", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    import sympy as sp
    p, qq = sp.symbols("p q")
    hits = []
    for label, text in options:
        if "=" not in text:
            continue
        lhs, rhs = text.split("=", 1)
        le, ri = _sympify(lhs), _sympify(rhs)
        if le is None or ri is None:
            continue
        try:
            if sp.simplify((le - ri) - (p + qq - 1)) == 0:
                hits.append((label, text))
        except Exception:
            continue
    if len(hits) != 1:
        return None
    label, text = hits[0]
    steps = [
        "An event either happens or does not, so "
        "p + q = 1 always.",
        f"Only option ({label}) says this: {text}",
    ]
    return _mk("probability", "w94_prob_pq",
               f"({label}) {text}", steps)


# ---------------------------------------------------------------------------
# More option verifiers: sector-area formula, complementary relations
# ---------------------------------------------------------------------------

def _sector_formula(q):
    """Area of a sector of angle P in a circle of radius R is
    (P/360)·πR². Verify the options symbolically (one printed
    option, (P/720)·2πR², is the same value in disguise — the
    symbolic check, not the surface shape, decides)."""
    if not re.search(r"sector|त्रिज्यखंड|त्रिज्यखण्ड", q, re.I):
        return None
    if not re.search(r"area|क्षेत्रफल", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    import sympy as sp
    P, R = sp.symbols("P R")
    target = (P / 360) * sp.pi * R ** 2
    hits = []
    for label, text in options:
        expr = _sympify(text)
        if expr is None:
            continue
        try:
            if sp.simplify(expr - target) == 0:
                hits.append((label, text))
        except Exception:
            continue
    if len(hits) != 1:
        return None
    label, text = hits[0]
    steps = [
        "Area of a sector = (P/360) × πR², where P is the "
        "angle of the sector and R the radius.",
        f"Only option ({label}) equals this: {text}",
    ]
    return _mk("geometry", "w94_sector_formula",
               f"({label}) {text}", steps)


def _complementary_relation(q):
    """A and B complementary (A + B = 90°): sin A = cos B,
    sec A = cosec B, tan A = cot B, … Verify each option by
    substituting B = 90° - A. An option whose two sides are
    textually identical asserts nothing and is skipped."""
    if not re.search(r"complementary|पूरक\s?कोण", q, re.I):
        return None
    got = _options(q)
    if got is None:
        return None
    _stem, options = got
    import sympy as sp
    A = sp.symbols("A", positive=True)
    funcs = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
             "cot": sp.cot, "sec": sp.sec, "cosec": sp.csc,
             "csc": sp.csc}

    def parse_side(text):
        m = re.fullmatch(
            r"\s*(sin|cos|tan|cot|sec|cosec|csc)\s*\(?\s*"
            r"([AB])\s*\)?\s*", text)
        if not m:
            return None
        fn = funcs[m.group(1).lower()]
        ang = A if m.group(2) == "A" else sp.pi / 2 - A
        return fn(ang)

    hits = []
    for label, text in options:
        if "=" not in text:
            continue
        lhs_t, rhs_t = text.split("=", 1)
        if lhs_t.strip() == rhs_t.strip():
            continue  # a tautology asserts no relation
        lhs, rhs = parse_side(lhs_t), parse_side(rhs_t)
        if lhs is None or rhs is None:
            continue
        try:
            if sp.simplify(sp.trigsimp(lhs - rhs)) == 0:
                hits.append((label, text))
        except Exception:
            continue
    if len(hits) != 1:
        return None
    label, text = hits[0]
    hi = _hindi(q)
    steps = [
        ("A और B पूरक कोण हैं, इसलिए B = 90° - A और "
         "sin A = cos B, sec A = cosec B, tan A = cot B।"
         if hi else
         "A and B are complementary, so B = 90° - A and "
         "sin A = cos B, sec A = cosec B, tan A = cot B."),
        f"Only option ({label}) is true: {text}",
    ]
    return _mk("trigonometry", "w94_complementary_relation",
               f"({label}) {text}", steps)


# ---------------------------------------------------------------------------
# Trigonometry: exact evaluation, tan-ratio expressions
# ---------------------------------------------------------------------------

_TRIG_TOKEN = re.compile(
    r"(sin|cos|tan|cot|sec|cosec|csc)\s*\(?\s*"
    r"(\d+(?:\.\d+)?)\s*°")


def _trig_evaluate(q):
    """An expression built only from trig ratios of degree
    angles and + - × ÷ ( ) — evaluate it exactly with SymPy
    (complementary pairs collapse via the angle-sum rules)."""
    if len(_TRIG_TOKEN.findall(q)) < 2:
        return None
    if not re.search(r"value|मान|evaluate|find\b", q, re.I) \
            and "=" not in q:
        return None
    got = _options(q)
    text = got[0] if got is not None else q
    # the expression: from the first trig token to the end of
    # its arithmetic run
    m = _TRIG_TOKEN.search(text)
    if m is None:
        return None
    expr_text = text[m.start():]
    expr_text = re.split(r"\?|\.\s|होगा|है\b", expr_text)[0]
    expr_text = expr_text.strip().rstrip(".").rstrip("=")
    expr_text = expr_text.strip()
    if not expr_text or len(expr_text) > 120:
        return None
    import sympy as sp

    def repl(mm):
        fn = {"sin": "sin", "cos": "cos", "tan": "tan",
              "cot": "cot", "sec": "sec", "cosec": "csc",
              "csc": "csc"}[mm.group(1).lower()]
        return f"{fn}({mm.group(2)}*pi/180)"
    s = _TRIG_TOKEN.sub(repl, expr_text)
    s = s.replace("²", "**2").replace("³", "**3")
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/")
    s = re.sub(r"\)\s*\(", ")*(", s)
    s = re.sub(r"(\d)\s*\(", r"\1*(", s)
    s = re.sub(r"\)\s*(?=[a-zA-Z])", ")*", s)
    s = re.sub(r"(\d)\s*(?=[a-zA-Z])", r"\1*", s)
    if re.search(r"[a-zA-Z]", re.sub(
            r"sin|cos|tan|cot|sec|csc|pi", "", s)):
        return None
    try:
        val = sp.simplify(sp.trigsimp(sp.sympify(s)))
        val = sp.nsimplify(val, [sp.sqrt(2), sp.sqrt(3)])
    except Exception:
        return None
    if val.free_symbols:
        return None
    ans = fmt_num(val) if not isinstance(val, sp.Expr) \
        else str(val).replace("sqrt", "√")
    if isinstance(val, sp.Expr):
        ans = str(val).replace("**", "^").replace("sqrt", "√")
        ans = ans.replace("*", "·")
    steps = [
        "Use sin(A + B) = sin A cos B + cos A sin B and the "
        "complementary-angle values (cos 55° = sin 35°, …) "
        "where the angles pair to 90°.",
        f"{expr_text} = {ans}",
    ]
    return _mk("trigonometry", "w94_trig_evaluate", ans, steps)


def _tan_ratio_expression(q):
    """Given tan θ = p/q (numbers or letters), evaluate a
    rational expression in sin θ and cos θ by dividing
    through by cos θ."""
    m = re.search(r"tan\s*[θA]\s*=\s*"
                  r"([a-zA-Z]|\d+(?:\.\d+)?)\s*/\s*"
                  r"([a-zA-Z]|\d+(?:\.\d+)?)", q)
    if m is None:
        return None
    got = _options(q)
    text = got[0] if got is not None else q
    vm = re.search(r"value of\s+(.+)$", text, re.I)
    if vm is None:
        vm = re.search(r"मान\s+(.+)$", text)
    if vm is None:
        return None
    expr_text = vm.group(1).strip().rstrip(".")
    expr_text = re.sub(r"\s*(will be|is|होगा|है)\s*:?\s*$", "",
                       expr_text).strip().rstrip(":").strip()
    if "sin" not in expr_text or "cos" not in expr_text:
        return None
    import sympy as sp
    p_txt, q_txt = m.group(1), m.group(2)

    def sym(t):
        return sp.symbols(t) if t.isalpha() else sp.Rational(t)
    p, qq = sym(p_txt), sym(q_txt)
    t = p / qq
    s = expr_text.replace("−", "-")
    s = re.sub(r"sin\s*[θA]", "S", s)
    s = re.sub(r"cos\s*[θA]", "C", s)
    s = s.replace("²", "**2").replace("³", "**3")
    s = re.sub(r"(\d)\s*([SC])", r"\1*\2", s)
    s = re.sub(r"([a-z])\s*([SC])", r"\1*\2", s)
    s = re.sub(r"\)\s*([SC])", r")*\1", s)
    S, C = sp.symbols("S C")
    try:
        expr = sp.sympify(s, locals={"S": S, "C": C})
        val = sp.cancel(expr.subs(S, t * C))
        val = sp.simplify(val)
    except Exception:
        return None
    if C in val.free_symbols or S in val.free_symbols:
        return None
    ans = str(val).replace("**", "^").replace("*", "·")
    steps = [
        f"tan θ = {p_txt}/{q_txt}. Divide the numerator and "
        "denominator by cos θ to turn sin θ/cos θ into tan θ.",
        f"The expression becomes a value in tan θ alone: "
        f"with tan θ = {p_txt}/{q_txt} it is {ans}.",
    ]
    return _mk("trigonometry", "w94_tan_ratio_expr", ans, steps)


# ---------------------------------------------------------------------------
# Pair of linear equations: parameter for no / infinite solutions
# ---------------------------------------------------------------------------

def _linear_coeffs(eq_text, param):
    """(a, b, c) of a·x + b·y + c = 0 from 'a1x + b1y = c1'
    style text; coefficients may involve the parameter."""
    import sympy as sp
    x, y = sp.symbols("x y")
    psym = sp.symbols(param) if param else None
    s = eq_text.replace("−", "-").replace("²", "**2")
    if "=" not in s:
        return None
    lhs, rhs = s.split("=", 1)
    def parse(side):
        side = side.strip()
        side = re.sub(r"(\d)\s*([xy])", r"\1*\2", side)
        side = re.sub(rf"(\d)\s*({param})", r"\1*\2", side) \
            if param else side
        side = re.sub(rf"({param})\s*([xy])", r"\1*\2", side) \
            if param else side
        side = re.sub(r"([xy])\s*([xy])", r"\1*\2", side)
        try:
            return sp.sympify(side, locals={
                "x": x, "y": y, **({param: psym} if param else {})})
        except Exception:
            return None
    le, ri = parse(lhs), parse(rhs)
    if le is None or ri is None:
        return None
    expr = sp.expand(le - ri)
    try:
        poly = sp.Poly(expr, x, y)
    except Exception:
        return None
    a = poly.coeff_monomial(x)
    b = poly.coeff_monomial(y)
    c = poly.coeff_monomial(1)
    return a, b, c


def _pair_parameter(q):
    """'The value of k for which the system … has no solution'
    (or infinitely many): a1/a2 = b1/b2 (≠ c1/c2) decides."""
    mode = None
    if re.search(r"no solution|no\s+unique|inconsistent|"
                 r"कोई हल नहीं|असंगत", q, re.I):
        mode = "none"
    elif re.search(r"infinitely many|infinite solutions|"
                   r"अनंत हल|अपरिमित हल", q, re.I):
        mode = "infinite"
    if mode is None:
        return None
    parts = re.split(r",|;|।|\band\b|और", q)
    eqs = []
    for p in parts:
        if "=" not in p or "x" not in p or "y" not in p:
            continue
        # trim any sentence furniture before the first x/y
        # term ('The value of k … equations x + y - 4 = 0')
        m = re.search(r"(?:^|\s)(-?\d*\.?\d*\s*[xy])(?=[\s+\-=])",
                      p)
        if m is not None:
            p = p[m.start(1):]
        eqs.append(p.strip())
    if len(eqs) < 2:
        return None
    e1, e2 = eqs[0], eqs[1]
    # the parameter: a letter that is not x or y appearing in
    # a coefficient position
    pm = re.search(r"([kmp])\s*(?:x|y|\s*=|\s*\+|\s*-|\s*,)", q)
    if pm is None:
        pm = re.search(r"(?:x|y)\s*([kmp])\b", q)
    if pm is None:
        return None
    param = pm.group(1)
    c1 = _linear_coeffs(e1, param)
    c2 = _linear_coeffs(e2, param)
    if c1 is None or c2 is None:
        return None
    import sympy as sp
    psym = sp.symbols(param)
    (a1, b1, k1), (a2, b2, k2) = c1, c2
    # a1/a2 = b1/b2  ->  a1*b2 - a2*b1 = 0 (linear in param)
    cond = sp.expand(a1 * b2 - a2 * b1)
    try:
        sols = sp.solve(cond, psym)
    except Exception:
        return None
    sols = [s for s in sols if s.is_real]
    if len(sols) != 1:
        return None
    val = sols[0]
    # check the constant ratio really differs (no solution)
    # or agrees (infinite) at this value
    subs = {psym: val}
    try:
        lhs = (a1.subs(subs) * k2.subs(subs)
               - a2.subs(subs) * k1.subs(subs))
    except Exception:
        lhs = None
    if mode == "none" and lhs == 0:
        return None  # would be infinite, not none
    if mode == "infinite" and lhs != 0:
        return None
    ans = fmt_num(val)
    steps = [
        "For a1x + b1y + c1 = 0 and a2x + b2y + c2 = 0, "
        + ("no solution needs a1/a2 = b1/b2 ≠ c1/c2."
           if mode == "none" else
           "infinitely many solutions need "
           "a1/a2 = b1/b2 = c1/c2."),
        f"a1/a2 = b1/b2 gives {param} = {ans}.",
    ]
    return _mk("algebra", "w94_pair_parameter",
               f"{param} = {ans}", steps)


# ---------------------------------------------------------------------------
# Quadratics: equal-roots parameter, rectangle word problem
# ---------------------------------------------------------------------------

def _equal_roots_param(q):
    """'Find k for which ax² + bx + c = 0 (coefficients in k)
    has two real and equal roots' — discriminant = 0."""
    if not re.search(r"equal roots|समान मूल|बराबर मूल", q, re.I):
        return None
    m = re.search(r"(.+?)=\s*0", q)
    if m is None:
        return None
    lhs = m.group(1)
    lhs = lhs[lhs.rfind(".") + 1:] if ". " in lhs else lhs
    pm = re.search(r"\b([kmp])\b", lhs)
    if pm is None:
        return None
    param = pm.group(1)
    import sympy as sp
    x, psym = sp.symbols("x"), sp.symbols(param)
    s = lhs.replace("−", "-").replace("²", "**2")
    s = re.sub(r"(\d)\s*\(", r"\1*(", s)
    s = re.sub(r"\)\s*(\d)", r")*\1", s)
    s = re.sub(r"\)\s*x", ")*x", s)
    s = re.sub(r"(\d)\s*x", r"\1*x", s)
    s = re.sub(rf"({param})\s*\(", r"\1*(", s)
    s = re.sub(rf"({param})\s*x", r"\1*x", s)
    s = re.sub(r"\(\s*x\s*-", "(x -", s)
    try:
        expr = sp.sympify(s, locals={"x": x, param: psym})
        poly = sp.Poly(expr, x)
    except Exception:
        return None
    if poly.degree() != 2:
        return None
    a, b, c = poly.all_coeffs()
    disc = sp.expand(b ** 2 - 4 * a * c)
    try:
        sols = sp.solve(disc, psym)
    except Exception:
        return None
    valid = []
    for s_ in sols:
        if not s_.is_real:
            continue
        if sp.simplify(a.subs(psym, s_)) != 0:
            valid.append(s_)
    if len(valid) != 1:
        return None
    val = valid[0]
    ans = fmt_num(val)
    steps = [
        "Equal roots need the discriminant to be 0: "
        "b² - 4ac = 0.",
        f"Here that gives {param} = {ans} (the other root of "
        "the discriminant equation would make a = 0, so the "
        "equation would stop being quadratic).",
    ]
    return _mk("algebra", "w94_equal_roots_param",
               f"{param} = {ans}", steps)


def _rectangle_field(q):
    """'The diagonal of a rectangular field is A metres more
    than the shorter side; the longer side is B metres more
    than the shorter side. Find the sides.' Pythagoras on
    x, x + B, x + A."""
    if not re.search(r"diagonal", q, re.I) \
            or not re.search(r"rectang", q, re.I):
        return None
    m1 = re.search(r"diagonal[^.]*?(\d+(?:\.\d+)?)\s*(?:m|metre|meter)?"
                   r"s?\s+more than the shorter", q, re.I)
    m2 = re.search(r"longer side[^.]*?(\d+(?:\.\d+)?)\s*(?:m|metre|meter)?"
                   r"s?\s+more than the shorter", q, re.I)
    if m1 is None or m2 is None:
        return None
    A = _frac(m1.group(1))
    B = _frac(m2.group(1))
    # x² + (x + B)² = (x + A)²  ->  x² + 2(B - A)x + (B² - A²) = 0
    import sympy as sp
    xs = sp.symbols("x")
    quad = xs ** 2 + 2 * (B - A) * xs + (B ** 2 - A ** 2)
    sols = [s for s in sp.solve(quad, xs)
            if s.is_real and s > 0]
    if len(sols) != 1:
        return None
    xv = sols[0]
    if not xv.is_rational:
        return None
    x = Fraction(xv.p, xv.q)
    longer = x + B
    steps = [
        "Let the shorter side be x metres. Then the longer "
        f"side is x + {_fmt_frac(B)} and the diagonal is "
        f"x + {_fmt_frac(A)}.",
        "By Pythagoras: x² + (x + "
        f"{_fmt_frac(B)})² = (x + {_fmt_frac(A)})²",
        f"x = {_fmt_frac(x)} (the negative root is not a "
        "length).",
        f"Longer side = {_fmt_frac(x)} + {_fmt_frac(B)} = "
        f"{_fmt_frac(longer)} metres.",
    ]
    ans = (f"{_fmt_frac(x)} metres and {_fmt_frac(longer)} "
           "metres")
    return _mk("word_problem", "w94_rectangle_field", ans,
               steps)


# ---------------------------------------------------------------------------
# Triangles & heights: right angle, tangent length, shadow,
# two-angle heights, BPT parallels, similar-triangle areas,
# circumscribing figures
# ---------------------------------------------------------------------------

def _right_angle_from_sides(q):
    """'In ΔPQR, PR² = PQ² + QR², then ∠Q = ?' — the side on
    the left is the hypotenuse; the right angle is opposite
    it, at the vertex it does not touch."""
    m = re.search(
        r"([A-Z])([A-Z])²\s*=\s*([A-Z])([A-Z])²\s*\+\s*"
        r"([A-Z])([A-Z])²", q)
    if m is None:
        return None
    hyp = {m.group(1), m.group(2)}
    tm = re.search(r"Δ\s?([A-Z])([A-Z])([A-Z])", q)
    if tm is None:
        return None
    verts = [tm.group(1), tm.group(2), tm.group(3)]
    rest = [v for v in verts if v not in hyp]
    if len(rest) != 1:
        return None
    v = rest[0]
    side = f"{m.group(1)}{m.group(2)}"
    steps = [
        f"By the converse of Pythagoras' theorem, when "
        f"{side}² equals the sum of the squares of the other "
        f"two sides, {side} is the hypotenuse.",
        f"The hypotenuse is opposite ∠{v}, so ∠{v} = 90°.",
    ]
    return _mk("geometry", "w94_right_angle", "90°", steps)


def _tangent_length(q):
    """Tangent from an external point: PQ² = OQ² - r² where
    OQ is the centre-to-point distance and r the radius."""
    if not re.search(r"tangent|स्पर्श\s?रेखा", q, re.I):
        return None
    rm = re.search(r"(?:radius|त्रिज्या)[^0-9]{0,24}"
                   r"(\d+(?:\.\d+)?)", q, re.I)
    if rm is None:
        rm = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|सेमी)?[०0]?\s*"
                       r"त्रिज्या", q)
    dm = re.search(r"\bOQ\s*=\s*(\d+(?:\.\d+)?)", q)
    if dm is None:
        dm = re.search(r"distance from (?:the )?centre[^0-9]{0,24}"
                       r"(\d+(?:\.\d+)?)", q, re.I)
    if rm is None or dm is None:
        return None
    r = _frac(rm.group(1))
    d = _frac(dm.group(1))
    if d <= r:
        return None
    val = d * d - r * r
    if val.denominator != 1:
        return None
    ans = _sqrt_str(int(val))
    hi = _hindi(q)
    steps = [
        ("त्रिज्या स्पर्श बिंदु पर स्पर्श रेखा पर लंब होती है, "
         "इसलिए त्रिभुज समकोण है।"
         if hi else
         "The radius to the point of contact is perpendicular "
         "to the tangent, so the triangle is right-angled."),
        f"PQ² = OQ² - r² = {_fmt_frac(d)}² - {_fmt_frac(r)}² "
        f"= {_fmt_frac(val)}",
        f"PQ = {ans}",
    ]
    return _mk("geometry", "w94_tangent_length", ans, steps)


def _concentric_chord(q):
    """Chord of the larger of two concentric circles that
    touches the smaller: length 2√(R² - r²)."""
    if not re.search(r"concentric|संकेन्द्र|संकेंद्री|समकेन्द्री",
                     q, re.I):
        return None
    if not re.search(r"chord|जीवा", q, re.I):
        return None
    nums = [n for n in re.findall(r"\d+(?:\.\d+)?", q)]
    if len(nums) < 2:
        return None
    vals = sorted((_frac(n) for n in nums[:2]), reverse=True)
    R, r = vals
    val = R * R - r * r
    if val.denominator != 1 or val <= 0:
        return None
    root = int(math.isqrt(int(val)))
    if root * root != int(val):
        return None
    ans = str(2 * root)
    steps = [
        "The chord touches the smaller circle, so the "
        "perpendicular from the centre bisects it and has "
        "length r.",
        f"Half the chord = √(R² - r²) = √({_fmt_frac(R)}² - "
        f"{_fmt_frac(r)}²) = {root}",
        f"Chord = 2 × {root} = {ans}",
    ]
    return _mk("geometry", "w94_concentric_chord", ans, steps)


def _lamp_shadow(q):
    """Walking away from a lamp post: shadow s satisfies
    s/(s + vt) = h/H, so s = h·vt/(H - h)."""
    if not re.search(r"lamp", q, re.I) \
            or not re.search(r"shadow", q, re.I):
        return None
    hm = re.search(r"height\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*cm",
                   q, re.I)
    if hm is None:
        hm = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|सेमी)\s*(?:tall|ऊँच)",
                       q, re.I)
    Hm = re.search(r"lamp[^.]*?(\d+(?:\.\d+)?)\s*m\s+above",
                   q, re.I)
    vm = re.search(r"speed of\s+(\d+(?:\.\d+)?)\s*m/s", q, re.I)
    tm = re.search(r"after\s+(\d+(?:\.\d+)?)\s*(?:second|sec)",
                   q, re.I)
    if None in (hm, Hm, vm, tm):
        return None
    h = _frac(hm.group(1)) / 100  # cm -> m
    H = _frac(Hm.group(1))
    v = _frac(vm.group(1))
    t = _frac(tm.group(1))
    if H <= h:
        return None
    dist = v * t
    s = h * dist / (H - h)
    steps = [
        f"In {fmt_num(float(t))} seconds she walks "
        f"{fmt_num(float(v))} × {fmt_num(float(t))} = "
        f"{_fmt_frac(dist)} m from the post.",
        "Similar triangles: shadow/(shadow + distance) = "
        "her height / lamp height.",
        f"s/(s + {_fmt_frac(dist)}) = {_fmt_frac(h)}/"
        f"{_fmt_frac(H)}, so s = {_fmt_frac(s)} m.",
    ]
    return _mk("geometry", "w94_lamp_shadow",
               f"{_fmt_frac(s)} m", steps)


def _two_angle_heights(q):
    """Elevation θ1 from the bank, retreat d metres, elevation
    θ2: height h = d/(cot θ2 - cot θ1); the near distance
    (river width) is h·cot θ1. Standard angles only, exact
    surd answers via SymPy."""
    angs = [a for a in re.findall(r"(\d+(?:\.\d+)?)\s*°", q)]
    if len(angs) < 2:
        return None
    if not re.search(r"elevation|उन्नयन", q, re.I):
        return None
    dm = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|मीटर|metre|meter)s?"
                   r"\s*(?:पीछे|back|away|retreat)", q, re.I)
    if dm is None:
        dm = re.search(r"(?:moves?|walks?|goes?)\s+"
                       r"(\d+(?:\.\d+)?)\s*(?:m|metre|meter)", q,
                       re.I)
    if dm is None:
        return None
    th1, th2 = _frac(angs[0]), _frac(angs[1])
    if th1 == th2:
        return None
    near, far = (th1, th2) if th1 > th2 else (th2, th1)
    d = _frac(dm.group(1))
    import sympy as sp
    cot = lambda deg: sp.cot(sp.pi * sp.Rational(deg) / 180)
    h = sp.simplify(sp.Rational(d) / (cot(far) - cot(near)))
    width = sp.simplify(h * cot(near))
    if not (h.is_real and width.is_real):
        return None
    def nice(v):
        s = str(v).replace("*", "·")
        s = re.sub(r"sqrt\((\d+)\)", r"√\1", s)
        return s.replace("sqrt", "√")
    dec = f"{float(h):.4g}"
    steps = [
        "Let the height be h and the near distance (river "
        "width) be w.",
        f"tan {float(near):g}° = h/w and tan {float(far):g}° "
        f"= h/(w + {_fmt_frac(d)})",
        f"Solving: h = {_fmt_frac(d)}/(cot {float(far):g}° - "
        f"cot {float(near):g}°) = {nice(h)} m (about {dec} m), "
        f"w = {nice(width)} m.",
    ]
    hi = _hindi(q)
    ans = (f"ऊँचाई = {nice(h)} मीटर, चौड़ाई = {nice(width)} मीटर"
           if hi else
           f"Height = {nice(h)} m, width = {nice(width)} m")
    return _mk("trigonometry", "w94_two_angle_heights", ans,
               steps)


def _bpt_parallels(q):
    """Three lines parallel, cut by two transversals: the
    segments are proportional. Given three segments on one
    transversal and one on the other, find an asked segment
    or sum of segments on the second."""
    lm = re.search(r"([A-Z])([A-Z])\s*(?:∥|\|\||parallel)[^.]{0,40}?"
                   r"([A-Z])([A-Z])\s*(?:∥|\|\|)[^.]{0,20}?"
                   r"([A-Z])([A-Z])", q, re.I)
    if lm is None:
        return None
    lines = [(lm.group(1), lm.group(2)),
             (lm.group(3), lm.group(4)),
             (lm.group(5), lm.group(6))]
    assign = {}
    for g1, g2, val in re.findall(
            r"\b([A-Z])([A-Z])\s*=\s*(\d+(?:\.\d+)?)", q):
        assign[g1 + g2] = _frac(val)
    if len(assign) < 4:
        return None
    t1 = [p[0] for p in lines]      # transversal-1 points by line
    t2 = [p[1] for p in lines]      # transversal-2 points by line
    # vertex: a letter in assignments touching t1[0]/t2[0] line
    # points but not itself a line point
    all_line_pts = set(t1 + t2)
    vertex = None
    for name in assign:
        for ch in name:
            if ch not in all_line_pts:
                vertex = ch
    if vertex is None:
        return None
    order1 = [vertex] + t1
    order2 = [vertex] + t2

    def seg_value(order, i, j):
        name = order[i] + order[j]
        if name in assign:
            return assign[name]
        name = order[j] + order[i]
        return assign.get(name)

    # find the known transversal-2 segment to fix the ratio
    ratio = None
    for i in range(3):
        v2 = seg_value(order2, i, i + 1)
        v1 = seg_value(order1, i, i + 1)
        if v2 is not None and v1:
            ratio = v2 / v1
            break
    if ratio is None:
        return None

    def value_on_2(i, j):
        v1 = seg_value(order1, i, j)
        if v1 is None:
            # span of consecutive unit segments
            tot = Fraction(0)
            for k in range(i, j):
                part = seg_value(order1, k, k + 1)
                if part is None:
                    return None
                tot += part
            v1 = tot
        return v1 * ratio

    asked = re.search(r"(?:find|then|ज्ञात)[^.]*?"
                      r"([A-Z][A-Z](?:\s*\+\s*[A-Z][A-Z])*)",
                      q, re.I)
    if asked is None:
        return None
    total = Fraction(0)
    parts = []
    for name in re.findall(r"[A-Z][A-Z]", asked.group(1)):
        a, b = name[0], name[1]
        if a in order2 and b in order2:
            i, j = sorted((order2.index(a), order2.index(b)))
            v = value_on_2(i, j)
        elif a in order1 and b in order1:
            i, j = sorted((order1.index(a), order1.index(b)))
            v = seg_value(order1, i, j)
        else:
            return None
        if v is None:
            return None
        total += v
        parts.append(f"{name} = {_fmt_frac(v)}")
    steps = [
        "Lines cut by two transversals make proportional "
        "segments: each segment on the second transversal is "
        f"the corresponding one × {_fmt_frac(ratio)}.",
        ", ".join(parts),
    ]
    unit = " cm" if "cm" in q else ""
    return _mk("geometry", "w94_bpt_parallels",
               f"{_fmt_frac(total)}{unit}", steps)


def _similar_area_ratio(q):
    """Areas of two similar triangles are in the squared
    ratio of corresponding sides / heights / medians."""
    if not re.search(r"similar|समरूप", q, re.I):
        return None
    if not re.search(r"area|क्षेत्रफल", q, re.I):
        return None
    m = re.search(
        r"(?:heights?|altitudes?|sides?|medians?|ऊँचाइयाँ|भुजाएँ|"
        r"माध्यिकाएँ)[^.0-9]{0,30}?(\d+(?:\.\d+)?)\s*(?:cm|सेमी|m)?"
        r"[०0]?\s*(?:and|तथा|और|,)\s*(\d+(?:\.\d+)?)", q, re.I)
    if m is None:
        return None
    u, v = _frac(m.group(1)), _frac(m.group(2))
    if u.denominator != 1 or v.denominator != 1:
        return None
    u2, v2 = int(u) ** 2, int(v) ** 2
    g = math.gcd(u2, v2)
    steps = [
        "For similar triangles, areas are in the square of "
        "the ratio of corresponding sides/heights.",
        f"Ratio = {int(u)}² : {int(v)}² = {u2 // g} : {v2 // g}",
    ]
    return _mk("geometry", "w94_similar_area_ratio",
               f"{u2 // g} : {v2 // g}", steps)


def _circumscribed_triangle(q):
    """Triangle circumscribing a circle: the two tangents
    from each vertex are equal. With tangent lengths x, y, z
    at A, B, C the sides are AB = x + y, BC = y + z,
    CA = z + x — solve from any three givens."""
    if not re.search(r"circumscrib", q, re.I):
        return None
    if re.search(r"quadrilateral", q, re.I):
        return None
    assign = {}
    for g1, g2, val in re.findall(
            r"\b([A-Z])([A-Z])\s*=\s*(\d+(?:\.\d+)?)", q):
        assign[g1 + g2] = _frac(val)
    contacts = {"AR", "AQ", "BP", "BR", "CQ", "CP"}
    sides = {"AB", "BC", "CA"}
    known = {k: v for k, v in assign.items()
             if k in contacts or k in sides
             or (k[0] in "ABC" and k[1] in "ABC")}
    # equations in x (from A), y (from B), z (from C)
    import sympy as sp
    x, y, z = sp.symbols("x y z")
    exprs = {
        "AR": x, "AQ": x, "BP": y, "BR": y, "CQ": z, "CP": z,
        "AB": x + y, "BA": x + y, "BC": y + z, "CB": y + z,
        "CA": z + x, "AC": z + x,
    }
    eqs = []
    for name, val in known.items():
        if name in exprs:
            eqs.append(sp.Eq(exprs[name], sp.Rational(val)))
    if len(eqs) < 3:
        return None
    try:
        sol = sp.solve(eqs[:4], (x, y, z), dict=True)
    except Exception:
        return None
    if not sol:
        return None
    sol = sol[0]
    asked = re.search(r"length of\s+([A-Z])([A-Z])", q, re.I)
    if asked is None:
        return None
    name = asked.group(1) + asked.group(2)
    if name not in exprs:
        return None
    val = sp.simplify(exprs[name].subs(sol))
    if not val.is_rational or val <= 0:
        return None
    fv = Fraction(int(val.p), int(val.q))
    steps = [
        "Tangents from one external point to a circle are "
        "equal: let the tangent lengths from A, B, C be "
        "x, y, z.",
        "Then AB = x + y, BC = y + z, CA = z + x; solving "
        "with the given lengths gives "
        f"x = {_fmt_frac(Fraction(int(sol[x].p), int(sol[x].q)))}, "
        f"y = {_fmt_frac(Fraction(int(sol[y].p), int(sol[y].q)))}, "
        f"z = {_fmt_frac(Fraction(int(sol[z].p), int(sol[z].q)))}.",
        f"{name} = {_fmt_frac(fv)} cm",
    ]
    return _mk("geometry", "w94_circumscribed_triangle",
               f"{_fmt_frac(fv)} cm", steps)


def _circumscribed_quad(q):
    """Quadrilateral circumscribing a circle:
    AB + CD = BC + AD (Pitot)."""
    if not re.search(r"quadrilateral", q, re.I) \
            or not re.search(r"circumscrib", q, re.I):
        return None
    assign = {}
    for g1, g2, val in re.findall(
            r"\b([A-Z])([A-Z])\s*=\s*(\d+(?:\.\d+)?)", q):
        assign[g1 + g2] = _frac(val)
    sides = {"AB", "BC", "CD", "DA"}
    have = {k: v for k, v in assign.items() if k in sides}
    if len(have) != 3:
        return None
    missing = (sides - set(have)).pop()
    total = sum(have.values(), Fraction(0))
    # AB + CD = BC + AD -> missing = (sum of the two sides
    # not adjacent in the equality) ... solve directly:
    vals = dict(have)
    def side(n):
        return vals.get(n)
    if side("AB") is not None and side("CD") is not None \
            and side("BC") is not None:
        ans = side("AB") + side("CD") - side("BC")
        name = "AD"
    elif side("BC") is not None and side("DA") is not None \
            and side("CD") is not None:
        ans = side("BC") + side("DA") - side("CD")
        name = "AB"
    elif side("AB") is not None and side("BC") is not None \
            and side("DA") is not None:
        ans = side("BC") + side("DA") - side("AB")
        name = "CD"
    elif side("AB") is not None and side("CD") is not None \
            and side("DA") is not None:
        ans = side("AB") + side("CD") - side("DA")
        name = "BC"
    else:
        return None
    steps = [
        "For a quadrilateral circumscribing a circle, the "
        "sums of opposite sides are equal: AB + CD = BC + AD.",
        f"{name} = {_fmt_frac(ans)}",
    ]
    return _mk("geometry", "w94_circumscribed_quad",
               _fmt_frac(ans), steps)


def _bpt_side_ratio(q):
    """A line parallel to the base of a triangle divides the
    other two sides proportionally: if PQ : BC = u : v (the
    parallel segment to the base), then the parts of a side
    are in the ratio AP : PB = u : (v - u)."""
    if not re.search(r"∥|\|\||parallel|समान्तर|समानांतर", q):
        return None
    m = re.search(r"([A-Z])([A-Z])\s*:\s*([A-Z])([A-Z])\s*=\s*"
                  r"(\d+)\s*:\s*(\d+)", q)
    if m is None:
        m = re.search(r"([A-Z])([A-Z])\s*:\s*([A-Z])([A-Z])\s*"
                      r"हो", q)
    if m is None:
        return None
    seg, base = m.group(1) + m.group(2), m.group(3) + m.group(4)
    if len(m.groups()) >= 6 and m.group(5):
        u, v = int(m.group(5)), int(m.group(6))
    else:
        rm = re.search(r"=\s*(\d+)\s*:\s*(\d+)", q)
        if rm is None:
            return None
        u, v = int(rm.group(1)), int(rm.group(2))
    if v <= u or u <= 0:
        return None
    am = re.search(r"([A-Z])([A-Z])\s*(?:और|and|तथा)\s*"
                   r"([A-Z])([A-Z])\s*(?:का\s+)?अनुपात", q)
    if am is None:
        am = re.search(r"ratio of\s+([A-Z])([A-Z])\s+(?:and|to)\s+"
                       r"([A-Z])([A-Z])", q, re.I)
    if am is None:
        return None
    first = am.group(1) + am.group(2)
    second = am.group(3) + am.group(4)
    # the first asked segment starts at the vertex (its first
    # letter is not on the base), the second ends at the base
    g = math.gcd(u, v - u)
    steps = [
        "The line parallel to the base divides the sides "
        "proportionally (Basic Proportionality Theorem): "
        f"{first}/{second}-side ratio follows {seg} : {base} "
        f"= {u} : {v}.",
        f"{first} : {second} = {u} : {v - u} = "
        f"{u // g} : {(v - u) // g}",
    ]
    return _mk("geometry", "w94_bpt_side_ratio",
               f"{u // g} : {(v - u) // g}", steps)


# ---------------------------------------------------------------------------
# Mensuration forms
# ---------------------------------------------------------------------------

def _semicircle_perimeter(q):
    if not re.search(r"semicircle|अर्धवृत्त|अर्द्धवृत्त", q, re.I):
        return None
    if not re.search(r"perimeter|परिमिति|परिधि", q, re.I):
        return None
    rm = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|mm|m|सेमी|मी)"
                   r"[०0]?\s*(?:त्रिज्या|radius)", q, re.I)
    if rm is None:
        rm = re.search(r"(?:radius|त्रिज्या)\s*(?:of|=|:)?\s*"
                       r"(\d+(?:\.\d+)?)", q, re.I)
    if rm is None:
        return None
    r = _frac(rm.group(1))
    ans = f"{_fmt_frac(r)}π + {_fmt_frac(2 * r)}"
    hi = _hindi(q)
    steps = [
        ("अर्धवृत्त की कुल परिमिति = अर्ध-परिधि + व्यास "
         "= πr + 2r"
         if hi else
         "Perimeter of a semicircle = half the circumference "
         "+ the diameter = πr + 2r"),
        f"= π × {_fmt_frac(r)} + 2 × {_fmt_frac(r)} = {ans}",
    ]
    return _mk("geometry", "w94_semicircle_perimeter", ans,
               steps)


def _cylinder_cone_ratio(q):
    if not re.search(r"cylinder|बेलन", q, re.I) \
            or not re.search(r"cone|शंकु", q, re.I):
        return None
    if not re.search(r"equal|बराबर|समान", q, re.I):
        return None
    if not re.search(r"ratio of (their )?volumes|"
                     r"आयतनों का अनुपात|आयतन.*अनुपात", q, re.I):
        return None
    cyl_first = q.lower().find("cylinder") \
        if "cylinder" in q.lower() else q.find("बेलन")
    cone_first = q.lower().find("cone") \
        if "cone" in q.lower() else q.find("शंकु")
    if cyl_first < 0:
        cyl_first = q.find("बेलन")
    if cone_first < 0:
        cone_first = q.find("शंकु")
    ans = "3 : 1" if cyl_first <= cone_first else "1 : 3"
    steps = [
        "With the same radius r and height h: cylinder "
        "volume = πr²h, cone volume = (1/3)πr²h.",
        f"Ratio = πr²h : (1/3)πr²h = {ans}"
        if ans == "3 : 1" else
        f"Ratio = (1/3)πr²h : πr²h = {ans}",
    ]
    return _mk("geometry", "w94_cylinder_cone_ratio", ans,
               steps)


def _cylinder_csa_radius(q):
    """CSA of a cylinder given, height = k × radius:
    CSA = 2πrh = 2πk·r². Solved exactly when r comes out a
    clean rational under π = 22/7 (the school convention for
    numbers built on it), else not claimed."""
    if not re.search(r"cylinder|बेलन", q, re.I):
        return None
    if not re.search(r"curved surface area|वक्र\s?पृष्ठ", q,
                     re.I):
        return None
    cm = re.search(r"(?:curved surface area|वक्र\s?पृष्ठ[^0-9]{0,20})"
                   r"[^0-9]{0,30}?(\d+(?:\.\d+)?)", q, re.I)
    if cm is None:
        cm = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm²|सेमी²|वर्ग\s?सेमी)",
                   q)
    if cm is None:
        return None
    csa = _frac(cm.group(1))
    k = None
    km = re.search(r"(?:height|ऊँचाई)[^.]{0,50}?"
                   r"(दुगुनी|दोगुनी|तिगुनी|आधी|twice|double|thrice|"
                   r"half)", q, re.I)
    if km:
        k = {"दुगुनी": 2, "दोगुनी": 2, "तिगुनी": 3, "आधी":
             Fraction(1, 2), "twice": 2, "double": 2,
             "thrice": 3, "half": Fraction(1, 2)}[km.group(1).lower()]
    if k is None:
        km = re.search(r"(\d+(?:\.\d+)?)\s*(?:times|गुनी)", q,
                       re.I)
        if km:
            k = _frac(km.group(1))
    if k is None:
        return None
    # r² = CSA / (2πk); try π = 22/7 first
    r2 = csa / (2 * Fraction(22, 7) * _frac(k))
    rn, rd = r2.numerator, r2.denominator
    sn, sd = int(math.isqrt(rn)), int(math.isqrt(rd))
    if sn * sn == rn and sd * sd == rd:
        r = Fraction(sn, sd)
        steps = [
            f"Height h = {_fmt_frac(_frac(k))} × radius r, and "
            "CSA = 2πrh.",
            f"{_fmt_frac(csa)} = 2 × (22/7) × r × "
            f"{_fmt_frac(_frac(k))}r, so r² = {_fmt_frac(r2)}",
            f"r = {_fmt_frac(r)} cm",
        ]
        return _mk("geometry", "w94_cylinder_csa_radius",
                   f"{_fmt_frac(r)} cm", steps)
    return None


def _wire_arc(q):
    """A wire of length L bent into an arc subtending θ°:
    L = (θ/360)·2πr. π = 22/7 when the question says so or
    the numbers are built on it."""
    if not re.search(r"wire|तार", q, re.I):
        return None
    if not re.search(r"arc|चाप", q, re.I):
        return None
    lm = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|सेमी)?\s*"
                   r"(?:long|लंबा|लम्बा)", q, re.I)
    am = re.search(r"(\d+(?:\.\d+)?)\s*°", q)
    if lm is None or am is None:
        return None
    L = _frac(lm.group(1))
    th = _frac(am.group(1))
    if th == 0:
        return None
    r = L * 360 / (2 * Fraction(22, 7) * th)
    if r.denominator == 1:
        ans = _fmt_frac(r)
        steps = [
            "Arc length = (θ/360) × 2πr — the wire's length "
            "is the arc's length.",
            f"{_fmt_frac(L)} = ({_fmt_frac(th)}/360) × 2 × "
            f"(22/7) × r, so r = {ans}",
        ]
        unit = " cm" if "cm" in q or "सेमी" in q else ""
        return _mk("geometry", "w94_wire_arc", ans + unit,
                   steps)
    return None


# ---------------------------------------------------------------------------
# Statistics & probability forms
# ---------------------------------------------------------------------------

def _mean_first_n(q):
    """Mean of the first n natural numbers is (n + 1)/2."""
    if not re.search(r"mean of (the )?first n natural|"
                     r"प्रथम n प्राकृत[^.]{0,20}माध्य", q, re.I):
        return None
    m = re.search(r"(?:is|=|है)\s*(\d+(?:\.\d+)?)", q)
    if m is None:
        return None
    mean = _frac(m.group(1))
    n = 2 * mean - 1
    if n.denominator != 1 or n <= 0:
        return None
    steps = [
        "The first n natural numbers are 1, 2, …, n; their "
        "mean is (n + 1)/2.",
        f"(n + 1)/2 = {_fmt_frac(mean)}, so n = {int(n)}",
    ]
    return _mk("statistics", "w94_mean_first_n", str(int(n)),
               steps)


def _modal_class(q):
    """Read a text distribution (class intervals + frequency
    list) and give the modal class limit asked for."""
    if not re.search(r"modal class|बहुलक वर्ग", q, re.I):
        return None
    intervals = re.findall(r"(\d+)\s*[-–]\s*(\d+)", q)
    if len(intervals) < 3:
        return None
    # frequencies: integers after the intervals region
    last_end = 0
    for m in re.finditer(r"\d+\s*[-–]\s*\d+", q):
        last_end = m.end()
    tail = q[last_end:]
    freqs = [int(n) for n in re.findall(r"\d+", tail)]
    # the tail may carry the option numbers too; the frequency
    # list is the run whose length matches the intervals
    if len(freqs) < len(intervals):
        return None
    freqs = freqs[:len(intervals)]
    top = max(range(len(freqs)), key=lambda i: freqs[i])
    lo, hi_ = intervals[top]
    if re.search(r"upper limit|उच्च\s?सीमा|ऊपरी\s?सीमा", q,
                 re.I):
        ans, which = hi_, "upper"
    else:
        ans, which = lo, "lower"
    steps = [
        "The modal class is the class with the highest "
        f"frequency: {lo}-{hi_} (frequency {freqs[top]}).",
        f"Its {which} limit is {ans}.",
    ]
    return _mk("statistics", "w94_modal_class", str(ans),
               steps)


_DICE_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4,
               "five": 5, "six": 6, "एक": 1, "दो": 2, "तीन": 3,
               "चार": 4, "पाँच": 5, "पांच": 5, "छह": 6}


def _dice_coin_outcomes(q):
    """Total outcomes when n dice (6^n) or n coins (2^n) are
    tossed together."""
    if not re.search(r"outcomes?|परिणाम", q, re.I):
        return None
    _NUMWORD = (r"(one|two|three|four|five|six|"
                r"एक|दो|तीन|चार|पाँच|पांच|छह|\d+)")
    m = re.search(_NUMWORD + r"\s+(?:dice|die|पासों|पासे|पासा)",
                  q, re.I)
    base = 6
    if m is None:
        m = re.search(_NUMWORD + r"\s+(?:coins?|सिक्कों|सिक्के|"
                      r"सिक्का)", q, re.I)
        base = 2
    if m is None:
        return None
    word = m.group(1).lower()
    n = _DICE_WORDS.get(word)
    if n is None and word.isdigit():
        n = int(word)
    if n is None or n < 1 or n > 6:
        return None
    total = base ** n
    steps = [
        f"Each {'die' if base == 6 else 'coin'} has {base} "
        f"outcomes; {n} of them together give "
        f"{base}^{n} outcomes.",
        f"{base}^{n} = {total}",
    ]
    return _mk("probability", "w94_outcome_count", str(total),
               steps)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_SCHEMAS = [
    _axis_fact, _midpoint, _axis_division_ratio,
    _collinear_unknown, _terminating_decimal, _coprime_pair,
    _unit_digit_cannot, _prob_pq_relation, _sector_formula,
    _complementary_relation, _poly_from_zeros_mcq,
    _zeros_relations, _poly_degree, _ap_sum_fact,
    _ap_term_check, _ap_term_count, _pair_parameter,
    _equal_roots_param, _rectangle_field, _trig_evaluate,
    _tan_ratio_expression, _right_angle_from_sides,
    _tangent_length, _concentric_chord, _lamp_shadow,
    _two_angle_heights, _bpt_parallels, _bpt_side_ratio,
    _similar_area_ratio,
    _circumscribed_triangle, _circumscribed_quad,
    _semicircle_perimeter, _cylinder_cone_ratio,
    _cylinder_csa_radius, _wire_arc, _mean_first_n,
    _modal_class, _dice_coin_outcomes,
]


def solve_papers10(question):
    """Wave 94 entry point: the Class 10 board-paper method
    schemas. Returns a solver result dict or None. Called by
    the router only when the primary solve failed, so a None
    here leaves behaviour byte-identical."""
    q = _prep(question)
    if not q.strip():
        return None
    for schema in _SCHEMAS:
        try:
            out = schema(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
