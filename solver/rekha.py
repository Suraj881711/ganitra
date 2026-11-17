"""Wave 115: Rekha Ganit — straight-line / coordinate-geometry
SOLVING depth.

Suraj's order (17 Nov 2026): "rekha gadit ke question solve
hone chahiye" — line questions must actually SOLVE with steps,
not return a concept card or "Answer not found". The pre-wave
audit (49 probes through /api/solve) found the family in three
states:

- already solving (left untouched): slope from two points,
  two-point and point-slope equations, section formula on the
  "divides" phrasing, collinearity checks, triangle/quadrilateral
  area, midpoint, centroid (all in solver/geometry.py), plus the
  Wave 94 coordinate schemas in solver/papers10.py;
- honestly missing (NOT_FOUND): slope from an equation,
  inclination <-> slope, slope-intercept construction, intercept
  form, form conversion, parallel/perpendicular line equations
  through a point, point-to-line distance, parallel-line
  distance, angle between lines, foot of perpendicular, image
  of a point, locus / perpendicular bisector, normal form,
  origin-to-line distance, and nearly every Hindi/Hinglish
  phrasing of the above;
- HIJACKED (a plausible answer to a DIFFERENT question):
  parallel/perpendicular CHECKS and angle-between-lines asks
  were "solved" as a 2x2 system (the intersection point),
  the internal-division point ask echoed the ratio back,
  the line-through-intersection ask served the intersection
  point, and the perpendicular-bisector ask served the
  segment's own line.

This module closes the missing families with METHOD schemas —
each parses the student's own numbers out of the question and
computes — and repairs the hijacks through rekha_upgrade, the
Wave 103 degree_upgrade pattern: the primary result for those
asks is "real" by the fallback layer's judgement, so the
router's failure gate can never see it; the upgrade fires
only on a strict ask shape whose served answer is verifiably
not an answer to that ask (a system solution served for a
yes/no check, a ratio echoed for a point ask, the segment's
own line served for its bisector).

Hooking: solver/router.py calls solve_rekha at the very end
of _solve_question_uncached, behind the same failure-only
gate as Waves 77/94/103, so a question the solver already
answers is never displaced — the schemas only convert
failures. fallback.py consults rekha_upgrade next to
degree_upgrade for the hijack shapes.
"""

import math
import re
from fractions import Fraction

from .expression_parser import extract_points, fmt_num

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")


def _prep(q):
    """Surface normalisation shared by every schema: ASCII
    operators and digits, one shape for the parsers."""
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"sqrt\s*\(\s*(\d+)\s*\)", r"√\1", s)
    s = s.replace("√(", "√")
    return s


def _hindi(q):
    return any("ऀ" <= ch <= "ॿ" for ch in str(q or ""))


def _mk(type_, op, answer, steps):
    return {"type": type_, "op": op, "answer": answer,
            "steps": steps}


# ---------------------------------------------------------------------------
# Numbers: rational values stay Fractions; surds (√n) ride as floats
# ---------------------------------------------------------------------------

_NUM = (r"(?:\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
        r"|\d+\s*/\s*√\s*\d+|√\s*\d+)")


def _val(token):
    """Parse a number token: '3', '2.5', '2/3', '√3', '1/√3'
    -> Fraction when rational, else a float."""
    t = str(token).replace(" ", "")
    if "√" in t:
        if "/" in t:
            a, b = t.split("/", 1)
            return float(a) / math.sqrt(float(b.replace("√", "")))
        return math.sqrt(float(t.replace("√", "")))
    if "/" in t:
        a, b = t.split("/", 1)
        return Fraction(a) / Fraction(b)
    return Fraction(t)


def _signed(sign, token, default=None):
    """Coefficient from an optional sign + optional token.
    A missing token means the coefficient is 1 (bare 'x')."""
    if token is None:
        v = default if default is not None else Fraction(1)
    else:
        v = _val(token)
    if str(sign).strip() == "-":
        v = -v
    return v


def _fmt_frac(fr):
    fr = Fraction(fr) if not isinstance(fr, float) else fr
    if isinstance(fr, float):
        return fmt_num(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _fmt_val(v):
    """Display a coefficient/value: Fractions as a/b, a float
    that is exactly √n as √n, anything else via fmt_num."""
    if isinstance(v, Fraction):
        return _fmt_frac(v)
    if isinstance(v, float):
        n = v * v
        if abs(n - round(n)) < 1e-9 and round(n) > 0:
            return f"√{int(round(n))}"
        return fmt_num(v)
    return str(v)


def _is_zero(v):
    return abs(float(v)) < 1e-12


# ---------------------------------------------------------------------------
# Line-equation parsing: every match becomes (A, B, C) with
# A·x + B·y + C = 0, plus the match span (for de-duplication)
# ---------------------------------------------------------------------------

def _find_lines(q):
    found = []  # (start, end, (A, B, C))

    def add(m, triple):
        s, e = m.span()
        for (s2, e2, _t) in found:
            if s < e2 and s2 < e:
                return  # overlaps an accepted match
        found.append((s, e, triple))

    # y = m·x + c  ->  m·x - y + c = 0
    for m in re.finditer(
            r"y\s*=\s*([+-]?)\s*(" + _NUM + r")?\s*x"
            r"(?:\s*([+-])\s*(" + _NUM + r"))?", q):
        mv = _signed(m.group(1), m.group(2))
        cv = _signed(m.group(3), m.group(4), Fraction(0)) \
            if m.group(3) else Fraction(0)
        add(m, (mv, Fraction(-1), cv))
    # A·x + B·y + D = R  (either term may be absent)
    for m in re.finditer(
            r"([+-]?)\s*(" + _NUM + r")?\s*x"
            r"(?:\s*([+-])\s*(" + _NUM + r")?\s*y)?"
            r"(?:\s*([+-])\s*(" + _NUM + r"))?"
            r"\s*=\s*([+-]?)\s*(" + _NUM + r")", q):
        a = _signed(m.group(1), m.group(2))
        b = _signed(m.group(3), m.group(4)) if m.group(3) \
            else Fraction(0)
        d = _signed(m.group(5), m.group(6)) if m.group(5) \
            else Fraction(0)
        r = _signed(m.group(7), m.group(8))
        add(m, (a, b, d - r))
    # B·y + A·x + D = R  (y-term first)
    for m in re.finditer(
            r"([+-]?)\s*(" + _NUM + r")?\s*y"
            r"\s*([+-])\s*(" + _NUM + r")?\s*x"
            r"(?:\s*([+-])\s*(" + _NUM + r"))?"
            r"\s*=\s*([+-]?)\s*(" + _NUM + r")", q):
        b = _signed(m.group(1), m.group(2))
        a = _signed(m.group(3), m.group(4))
        d = _signed(m.group(5), m.group(6)) if m.group(5) \
            else Fraction(0)
        r = _signed(m.group(7), m.group(8))
        add(m, (a, b, d - r))
    # B·y + D = R  (no x-term; 'y = c' included)
    for m in re.finditer(
            r"([+-]?)\s*(" + _NUM + r")?\s*y"
            r"(?:\s*([+-])\s*(" + _NUM + r"))?"
            r"\s*=\s*([+-]?)\s*(" + _NUM + r")(?!\s*x)", q):
        b = _signed(m.group(1), m.group(2))
        d = _signed(m.group(3), m.group(4)) if m.group(3) \
            else Fraction(0)
        r = _signed(m.group(5), m.group(6))
        add(m, (Fraction(0), b, d - r))
    found.sort(key=lambda t: t[0])
    return [t for (_s, _e, t) in found]


def _fmt_general(a, b, c):
    """'2x - 3y + 10 = 0' from (A, B, C); rational triples are
    scaled to coprime integers with the first non-zero of
    (A, B) positive."""
    if all(isinstance(v, Fraction) for v in (a, b, c)):
        den = 1
        for v in (a, b, c):
            den = den * v.denominator // math.gcd(den, v.denominator)
        ia, ib, ic = int(a * den), int(b * den), int(c * den)
        g = math.gcd(math.gcd(abs(ia), abs(ib)), abs(ic)) or 1
        ia, ib, ic = ia // g, ib // g, ic // g
        if ia < 0 or (ia == 0 and ib < 0):
            ia, ib, ic = -ia, -ib, -ic
        a, b, c = Fraction(ia), Fraction(ib), Fraction(ic)
    parts = []
    for coef, var in ((a, "x"), (b, "y")):
        if _is_zero(coef):
            continue
        mag = -coef if float(coef) < 0 else coef
        body = var if mag == 1 else f"{_fmt_val(mag)}{var}"
        if not parts:
            parts.append(("-" if float(coef) < 0 else "") + body)
        else:
            parts.append((" - " if float(coef) < 0 else " + ") + body)
    if not _is_zero(c):
        mag = -c if float(c) < 0 else c
        if not parts:
            parts.append(("-" if float(c) < 0 else "") + _fmt_val(mag))
        else:
            parts.append((" - " if float(c) < 0 else " + ")
                         + _fmt_val(mag))
    return "".join(parts) + " = 0"


def _fmt_slope_form(m, c):
    """'y = 3x - 1' / 'y = -x + 4' / 'y = (3/4)x + 5/2'."""
    if _is_zero(m):
        return f"y = {_fmt_val(c)}"
    if isinstance(m, Fraction) and m.denominator != 1:
        mterm = f"({_fmt_frac(m)})x"
    elif m == 1:
        mterm = "x"
    elif m == -1:
        mterm = "-x"
    else:
        mterm = f"{_fmt_val(m)}x"
    if _is_zero(c):
        return f"y = {mterm}"
    if float(c) > 0:
        return f"y = {mterm} + {_fmt_val(c)}"
    return f"y = {mterm} - {_fmt_val(-c)}"


def _fmt_point(x, y):
    return f"({_fmt_val(x)}, {_fmt_val(y)})"


def _fmt_dist(num, s):
    """Exact display of num/√s (num >= 0): the radical is
    simplified and the denominator rationalised, NCERT style
    ('4/√2' -> '2√2', '2/√5' -> '2√5/5')."""
    num = float(num)
    s = float(s)
    if s <= 0:
        return "0"
    if abs(num) < 1e-12:
        return "0"
    si = int(round(s))
    if abs(s - si) < 1e-9 and float(num).is_integer():
        n = int(round(num))
        k = int(math.isqrt(si))
        while k > 1 and si % (k * k):
            k -= 1
        r = si // (k * k)
        if r == 1:
            return _fmt_frac(Fraction(n, k))
        g = math.gcd(n, k * r)
        p, qq = n // g, (k * r) // g
        head = f"√{r}" if p == 1 else f"{p}√{r}"
        return head if qq == 1 else f"{head}/{qq}"
    return fmt_num(num / math.sqrt(s))


def _slope_of(line):
    """Slope of (A, B, C); None for a vertical line."""
    a, b, _c = line
    if _is_zero(b):
        return None
    return -a / b


# ---------------------------------------------------------------------------
# Shared trigger patterns
# ---------------------------------------------------------------------------

_SLOPE_WORD = r"slope|प्रवणता|ढाल|pravanta|\bdhal\b"
_INCL_WORD = r"inclination|झुकाव|आनति|jhukav|jhukaav"
_EQ_WORD = r"equation|समीकरण|samikaran"
_PAR_WORD = r"parallel|समांतर|समानांतर|samantar"
_PERP_WORD = (r"perpendicular|लंबवत|लम्बवत|lambvat|lambwat|"
             r"lambat")
_DIST_WORD = r"distance|दूरी|doori|\bduri\b"
_ANGLE_WORD = r"angle|कोण"
_FOOT_WORD = r"foot|पाद|paad"
_IMAGE_WORD = r"image|reflection|प्रतिबिंब|परावर्तन|pratibimb"
_INTERSECT_WORD = r"intersection|प्रतिच्छेद|प्रतिच्छेदन"
_BISECT_WORD = (r"bisector|समद्विभाजक|"
                r"perpendicular\s+bisector")
_LOCUS_WORD = r"locus|बिंदुपथ|bindupath|बिन्दुपथ"
_INTERCEPT_WORD = r"intercept|अंतःखंड|antahkhand"


def _slope_value(q):
    """A slope value stated in the question ('slope is 3',
    'ढाल √3 है', 'slope -2'), else None."""
    m = re.search(
        r"(?:" + _SLOPE_WORD + r")\s*(?:is|of|=|:|का|की)?\s*"
        r"([+-]?)\s*(" + _NUM + r")", q, re.I)
    if not m:
        return None
    return _signed(m.group(1), m.group(2))


def _incl_value(q):
    """An inclination in degrees stated in the question."""
    m = re.search(
        r"(?:" + _INCL_WORD + r")\s*(?:is|of|=|:|का|की)?\s*"
        r"(\d+(?:\.\d+)?)\s*(?:°|degrees?|डिग्री)?", q, re.I)
    if m:
        return float(m.group(1))
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:°|degrees|डिग्री)\s*(?:के|का)?\s*"
        r"(?:" + _INCL_WORD + r")", q, re.I)
    if m:
        return float(m.group(1))
    return None


_STD_TAN = [(0.0, 0, "0"), (2 - math.sqrt(3), 15, "2 - √3"),
            (1 / math.sqrt(3), 30, "1/√3"), (1.0, 45, "1"),
            (math.sqrt(3), 60, "√3"), (2 + math.sqrt(3), 75, "2 + √3")]


def _std_from_tan(t):
    """(degrees, tan display) when tan(theta) is a standard
    value, else None."""
    for val, deg, disp in _STD_TAN:
        if abs(t - val) < 1e-9:
            return deg, disp
    return None


_STD_SLOPE_DEG = [(0.0, 0), (1 / math.sqrt(3), 30), (1.0, 45),
                  (math.sqrt(3), 60), (-math.sqrt(3), 120),
                  (-1.0, 135), (-1 / math.sqrt(3), 150)]


def _deg_from_slope(m):
    """Inclination in degrees for slope m (float), snapped to
    a standard angle when it is one."""
    f = float(m)
    for val, deg in _STD_SLOPE_DEG:
        if abs(f - val) < 1e-9:
            return float(deg)
    d = math.degrees(math.atan(f))
    if d < 0:
        d += 180.0
    return d


def _fmt_deg(d):
    if abs(d - round(d)) < 1e-9:
        return f"{int(round(d))}°"
    return f"{d:.2f}°"


# ---------------------------------------------------------------------------
# 1. Slope — from an equation, or from two points (Hindi/Hinglish
#    phrasings the English-keyword path in geometry.py misses)
# ---------------------------------------------------------------------------

def _slope(q):
    if not re.search(_SLOPE_WORD, q, re.I):
        return None
    if re.search(_INCL_WORD, q, re.I):
        return None  # the inclination schema owns mixed asks
    hi = _hindi(q)
    lines = _find_lines(q)
    pts = extract_points(q)
    if lines and len(pts) < 2:
        a, b, c = lines[0]
        if _is_zero(b):
            steps = [
                ("रेखा ऊर्ध्वाधर है (x = स्थिरांक), इसलिए इसकी "
                 "प्रवणता अपरिभाषित है।"
                 if hi else
                 "The line is vertical (x = constant), so its "
                 "slope is undefined.")]
            return _mk("geometry", "w115_slope_eq",
                       "अपरिभाषित (undefined)" if hi
                       else "undefined (vertical line)", steps)
        m = -a / b
        steps = [
            (f"रेखा Ax + By + C = 0 की प्रवणता m = -A/B होती है। "
             f"यहाँ A = {_fmt_val(a)}, B = {_fmt_val(b)}।"
             if hi else
             f"The slope of Ax + By + C = 0 is m = -A/B. "
             f"Here A = {_fmt_val(a)}, B = {_fmt_val(b)}."),
            f"m = -({_fmt_val(a)})/({_fmt_val(b)}) = {_fmt_val(m)}",
        ]
        return _mk("geometry", "w115_slope_eq", _fmt_val(m), steps)
    if len(pts) >= 2:
        (x1, y1), (x2, y2) = pts[0], pts[1]
        if x2 == x1:
            steps = [
                ("दोनों बिंदुओं का x-निर्देशांक बराबर है, इसलिए "
                 "रेखा ऊर्ध्वाधर है और प्रवणता अपरिभाषित है।"
                 if hi else
                 "Both points have the same x-coordinate, so "
                 "the line is vertical and the slope is "
                 "undefined.")]
            return _mk("geometry", "w115_slope_points",
                       "अपरिभाषित (undefined)" if hi
                       else "undefined (vertical line)", steps)
        m = Fraction(y2 - y1) / Fraction(x2 - x1) \
            if all(isinstance(v, int) for v in (x1, y1, x2, y2)) \
            else (y2 - y1) / (x2 - x1)
        steps = [
            ("प्रवणता m = (y2 - y1)/(x2 - x1)"
             if hi else "Slope m = (y2 - y1)/(x2 - x1)"),
            f"= ({fmt_num(y2)} - {fmt_num(y1)})/({fmt_num(x2)} - "
            f"{fmt_num(x1)}) = {_fmt_val(m)}",
        ]
        return _mk("geometry", "w115_slope_points",
                   _fmt_val(m), steps)
    return None


# ---------------------------------------------------------------------------
# 2. Inclination <-> slope
# ---------------------------------------------------------------------------

def _inclination(q):
    if not re.search(_INCL_WORD, q, re.I):
        return None
    hi = _hindi(q)
    sv = _slope_value(q)
    iv = _incl_value(q)
    if sv is not None and iv is None:
        # slope given, inclination asked
        d = _deg_from_slope(sv)
        steps = [
            ("झुकाव θ के लिए tan θ = प्रवणता होती है।"
             if hi else
             "For the inclination θ, tan θ = slope."),
            f"tan θ = {_fmt_val(sv)}, इसलिए θ = {_fmt_deg(d)}",
        ]
        return _mk("geometry", "w115_inclination",
                   _fmt_deg(d), steps)
    if iv is not None and sv is None:
        # inclination given, slope asked — needs a slope ask too
        if not re.search(_SLOPE_WORD, q, re.I):
            return None
        if abs(iv - 90) < 1e-9:
            steps = [
                ("झुकाव 90° है, अर्थात रेखा ऊर्ध्वाधर है — "
                 "इसकी प्रवणता अपरिभाषित है।"
                 if hi else
                 "The inclination is 90°, so the line is "
                 "vertical — its slope is undefined.")]
            return _mk("geometry", "w115_slope_from_incl",
                       "अपरिभाषित (undefined)" if hi
                       else "undefined (vertical line)", steps)
        t = math.tan(math.radians(iv))
        std = _std_from_tan(abs(t))
        if std is not None and abs(iv - round(iv)) < 1e-9 \
                and int(round(iv)) in (0, 15, 30, 45, 60, 75):
            disp = std[1] if t >= 0 else f"-{std[1]}"
            val = t
        else:
            disp = None
            val = t
        steps = [
            ("प्रवणता m = tan θ होती है।"
             if hi else "The slope is m = tan θ."),
            (f"m = tan {_fmt_deg(iv)} = {disp}"
             if disp else
             f"m = tan {_fmt_deg(iv)} = {fmt_num(round(val, 4))}"),
        ]
        ans = disp if disp else fmt_num(round(val, 4))
        return _mk("geometry", "w115_slope_from_incl", ans, steps)
    return None


# ---------------------------------------------------------------------------
# 3. Equation from slope + intercept; equation from two intercepts
# ---------------------------------------------------------------------------

def _intercept_value(q, axis):
    """The stated intercept on one axis ('y-intercept is 5',
    'x-अक्ष पर अंतःखंड 3', 'cuts the y-axis at -4')."""
    pats = [
        rf"{axis}[-\s]?(?:intercept|अंतःखंड)\s*(?:is|of|=|:|का|की)?"
        rf"\s*([+-]?)\s*(" + _NUM + r")",
        rf"(?:intercept|अंतःखंड)\s*(?:on|पर)\s*(?:the\s+)?{axis}"
        rf"[-\s]?(?:axis|अक्ष)\s*(?:is|=|:)?\s*([+-]?)\s*(" + _NUM + r")",
        rf"cuts?\s*(?:off\s*)?(?:the\s+)?{axis}[-\s]?(?:axis|अक्ष)"
        rf"\s*(?:at|पर)?\s*([+-]?)\s*(" + _NUM + r")",
        rf"{axis}[-\s]?(?:axis|अक्ष)\s*(?:को|पर)?\s*([+-]?)\s*(" + _NUM + r")"
        rf"\s*(?:पर|at)?\s*(?:काटती|काटता|cuts?)",
    ]
    for p in pats:
        m = re.search(p, q, re.I)
        if m:
            return _signed(m.group(1), m.group(2))
    return None


def _eq_slope_intercept(q):
    if not re.search(_EQ_WORD, q, re.I):
        return None
    if not re.search(_INTERCEPT_WORD + r"|काटती|काटता|cuts?\b",
                     q, re.I):
        return None
    m = _slope_value(q)
    if m is None:
        return None
    hi = _hindi(q)
    c = _intercept_value(q, "y")
    if c is not None:
        steps = [
            ("ढाल-अंतःखंड रूप: y = mx + c"
             if hi else "Slope-intercept form: y = mx + c"),
            f"m = {_fmt_val(m)}, c = {_fmt_val(c)} रखने पर: "
            f"{_fmt_slope_form(m, c)}",
        ]
        return _mk("geometry", "w115_eq_slope_intercept",
                   _fmt_slope_form(m, c), steps)
    a = _intercept_value(q, "x")
    if a is not None:
        # the line passes through (a, 0) with slope m
        c = -m * a
        steps = [
            (f"रेखा बिंदु ({_fmt_val(a)}, 0) से होकर जाती है और "
             f"इसकी ढाल {_fmt_val(m)} है।"
             if hi else
             f"The line passes through ({_fmt_val(a)}, 0) with "
             f"slope {_fmt_val(m)}."),
            ("बिंदु-ढाल रूप: y - y1 = m(x - x1)"
             if hi else "Point-slope form: y - y1 = m(x - x1)"),
            f"y = {_fmt_slope_form(m, c)[4:]}",
        ]
        return _mk("geometry", "w115_eq_slope_intercept",
                   _fmt_slope_form(m, c), steps)
    return None


def _intercept_term(v, var):
    """'x/3' style term for the intercept form, sign folded."""
    fv = _fmt_val(-v if float(v) < 0 else v)
    term = f"{var}/{fv}" if fv != "1" else var
    return (" - " if float(v) < 0 else " + "), term


def _intercept_form_str(a, b):
    s = ""
    for i, (v, var) in enumerate(((a, "x"), (b, "y"))):
        sign, term = _intercept_term(v, var)
        if i == 0:
            s += ("-" if float(v) < 0 else "") + term
        else:
            s += sign + term
    return s + " = 1"


def _eq_from_intercepts(q):
    if not re.search(_EQ_WORD, q, re.I):
        return None
    if not re.search(_INTERCEPT_WORD, q, re.I):
        return None
    if _slope_value(q) is not None:
        return None  # slope + intercept belongs to schema 3
    a = _intercept_value(q, "x")
    b = _intercept_value(q, "y")
    if a is None or b is None:
        m = re.search(r"intercepts?\s*(?:are|of|:)?\s*([+-]?)\s*("
                      + _NUM + r")\s*(?:and|aur|और|,)\s*([+-]?)\s*("
                      + _NUM + r")", q, re.I)
        if m:
            a = _signed(m.group(1), m.group(2))
            b = _signed(m.group(3), m.group(4))
    if a is None or b is None or _is_zero(a) or _is_zero(b):
        return None
    hi = _hindi(q)
    form = _intercept_form_str(a, b)
    steps = [
        ("अंतःखंड रूप: x/a + y/b = 1, जहाँ a और b क्रमशः "
         "x-अक्ष और y-अक्ष पर अंतःखंड हैं।"
         if hi else
         "Intercept form: x/a + y/b = 1, where a and b are "
         "the intercepts on the x-axis and the y-axis."),
        f"a = {_fmt_val(a)}, b = {_fmt_val(b)} रखने पर: {form}",
    ]
    return _mk("geometry", "w115_eq_intercepts", form, steps)


# ---------------------------------------------------------------------------
# 4. Intercept form of a given line; intercepts of a given line
# ---------------------------------------------------------------------------

def _intercept_form(q):
    lines = _find_lines(q)
    if len(lines) != 1:
        return None
    form_ask = re.search(r"(?<!slope[-\s])intercept[-\s]?form|"
                         r"अंतःखंड\s*रूप", q, re.I)
    find_ask = re.search(
        r"(?:find|ज्ञात|निकाल|बताइए|बताओ)[^.]{0,30}intercepts?\b",
        q, re.I) and not re.search(r"slope[-\s]?intercept", q, re.I)
    if not form_ask and not find_ask:
        return None
    a, b, c = lines[0]
    if _is_zero(a) or _is_zero(b) or _is_zero(c):
        return None
    ia, ib = -c / a, -c / b
    hi = _hindi(q)
    form = _intercept_form_str(ia, ib)
    steps = [
        (f"रेखा को Ax + By = -C के रूप में लिखने पर: "
         f"{_fmt_val(a)}x + {_fmt_val(b)}y = {_fmt_val(-c)}"
         if hi else
         f"Write the line as Ax + By = -C: "
         f"{_fmt_val(a)}x + {_fmt_val(b)}y = {_fmt_val(-c)}"),
        ("दोनों पक्षों को -C से भाग देने पर अंतःखंड रूप मिलता है:"
         if hi else
         "Divide both sides by -C to get the intercept form:"),
        f"{form} — x-अंतःखंड = {_fmt_val(ia)}, "
        f"y-अंतःखंड = {_fmt_val(ib)}"
        if hi else
        f"{form} — x-intercept = {_fmt_val(ia)}, "
        f"y-intercept = {_fmt_val(ib)}",
    ]
    if find_ask and not form_ask:
        ans = (f"x-अंतःखंड = {_fmt_val(ia)}, "
               f"y-अंतःखंड = {_fmt_val(ib)}" if hi else
               f"x-intercept = {_fmt_val(ia)}, "
               f"y-intercept = {_fmt_val(ib)}")
        return _mk("geometry", "w115_intercept_form", ans, steps)
    return _mk("geometry", "w115_intercept_form", form, steps)


# ---------------------------------------------------------------------------
# 5. Form conversion (to slope-intercept form / to general form)
# ---------------------------------------------------------------------------

def _convert_form(q):
    if not re.search(r"convert|reduce|बदल|परिवर्तित|रूप\s*में\s*लिख",
                     q, re.I):
        return None
    lines = _find_lines(q)
    if len(lines) != 1:
        return None
    a, b, c = lines[0]
    hi = _hindi(q)
    if re.search(r"slope[-\s]?intercept|ढाल[-\s]?अंतःखंड", q, re.I):
        if _is_zero(b):
            return None  # vertical line: no slope-intercept form
        m, ci = -a / b, -c / b
        steps = [
            (f"y को एक ओर ले जाने पर: {_fmt_val(b)}y = "
             f"{_fmt_val(-a)}x + {_fmt_val(-c)}"
             if hi else
             f"Bring y to one side: {_fmt_val(b)}y = "
             f"{_fmt_val(-a)}x + {_fmt_val(-c)}"),
            f"y = {_fmt_slope_form(m, ci)[4:]}",
        ]
        return _mk("geometry", "w115_convert_form",
                   _fmt_slope_form(m, ci), steps)
    if re.search(r"general\s*form|सामान्य\s*रूप", q, re.I):
        gen = _fmt_general(a, b, c)
        steps = [
            ("सभी पदों को एक ओर लाने पर सामान्य रूप मिलता है:"
             if hi else
             "Bring every term to one side for the general "
             "form Ax + By + C = 0:"),
            gen,
        ]
        return _mk("geometry", "w115_convert_form", gen, steps)
    return None


# ---------------------------------------------------------------------------
# 6. Parallel / perpendicular CHECK on two given lines
# ---------------------------------------------------------------------------

def _check_verdict(q):
    """'parallel' / 'perpendicular' / None — what the check
    ask is about (the first relation word wins)."""
    mp = re.search(_PAR_WORD, q, re.I)
    mq = re.search(_PERP_WORD, q, re.I)
    if mp and mq:
        return "both"
    if mp:
        return "parallel"
    if mq:
        return "perpendicular"
    return None


def _parallel_perp_check(q):
    want = _check_verdict(q)
    if want is None:
        return None
    if re.search(_EQ_WORD, q, re.I) and re.search(
            r"find|ज्ञात|निकाल", q, re.I):
        return None  # an equation CONSTRUCTION ask, not a check
    lines = _find_lines(q)
    if len(lines) != 2:
        return None
    if extract_points(q):
        return None  # a construction ask carries a point
    (a1, b1, c1), (a2, b2, c2) = lines
    hi = _hindi(q)
    parallel = _is_zero(a1 * b2 - a2 * b1)
    coincident = parallel and _is_zero(a1 * c2 - a2 * c1) \
        and _is_zero(b1 * c2 - b2 * c1)
    perp = _is_zero(a1 * a2 + b1 * b2)
    m1, m2 = _slope_of(lines[0]), _slope_of(lines[1])
    if m1 is not None and m2 is not None:
        crit = (f"प्रवणताएँ: m1 = {_fmt_val(m1)}, "
                f"m2 = {_fmt_val(m2)}"
                if hi else
                f"Slopes: m1 = {_fmt_val(m1)}, "
                f"m2 = {_fmt_val(m2)}")
    else:
        crit = (f"दिशा अनुपात की जाँच: A1·B2 - A2·B1 = "
                f"{_fmt_val(a1 * b2 - a2 * b1)}, "
                f"A1·A2 + B1·B2 = {_fmt_val(a1 * a2 + b1 * b2)}"
                if hi else
                f"Direction test: A1·B2 - A2·B1 = "
                f"{_fmt_val(a1 * b2 - a2 * b1)}, "
                f"A1·A2 + B1·B2 = {_fmt_val(a1 * a2 + b1 * b2)}")
    if want == "parallel":
        if coincident:
            ans = ("रेखाएँ संपाती हैं (एक ही रेखा है)" if hi
                   else "The lines are coincident "
                        "(they are the same line)")
            why = ("दोनों समीकरण एक ही रेखा के हैं (गुणांक समान "
                   "अनुपात में हैं)।" if hi else
                   "Both equations describe the same line "
                   "(all coefficients are in the same ratio).")
        elif parallel:
            ans = ("हाँ, रेखाएँ समांतर हैं" if hi
                   else "Yes, the lines are parallel")
            why = ("प्रवणताएँ बराबर हैं (m1 = m2), इसलिए रेखाएँ "
                   "समांतर हैं।" if hi else
                   "The slopes are equal (m1 = m2), so the "
                   "lines are parallel.")
        else:
            ans = ("नहीं, रेखाएँ समांतर नहीं हैं" if hi
                   else "No, the lines are not parallel")
            why = ("प्रवणताएँ बराबर नहीं हैं, इसलिए रेखाएँ "
                   "समांतर नहीं हैं।" if hi else
                   "The slopes are not equal, so the lines "
                   "are not parallel.")
        return _mk("geometry", "w115_par_perp_check", ans,
                   [crit, why])
    if want == "perpendicular":
        if perp:
            ans = ("हाँ, रेखाएँ लंबवत हैं" if hi
                   else "Yes, the lines are perpendicular")
            why = ("A1·A2 + B1·B2 = 0 है (प्रवणताओं का गुणनफल "
                   "-1), इसलिए रेखाएँ लंबवत हैं।" if hi else
                   "A1·A2 + B1·B2 = 0 (the product of the "
                   "slopes is -1), so the lines are "
                   "perpendicular.")
        else:
            ans = ("नहीं, रेखाएँ लंबवत नहीं हैं" if hi
                   else "No, the lines are not perpendicular")
            why = ("A1·A2 + B1·B2 = 0 नहीं है, इसलिए रेखाएँ "
                   "लंबवत नहीं हैं।" if hi else
                   "A1·A2 + B1·B2 is not 0, so the lines are "
                   "not perpendicular.")
        return _mk("geometry", "w115_par_perp_check", ans,
                   [crit, why])
    # both relations asked: report the true one
    if coincident:
        ans = ("रेखाएँ संपाती हैं (एक ही रेखा है)" if hi
               else "The lines are coincident "
                    "(they are the same line)")
    elif parallel:
        ans = ("रेखाएँ समांतर हैं" if hi
               else "The lines are parallel")
    elif perp:
        ans = ("रेखाएँ लंबवत हैं" if hi
               else "The lines are perpendicular")
    else:
        ans = ("रेखाएँ न समांतर हैं, न लंबवत" if hi
               else "The lines are neither parallel nor "
                    "perpendicular")
    why = ("ऊपर की जाँच से संबंध स्पष्ट है।" if hi
           else "The test above settles the relation.")
    return _mk("geometry", "w115_par_perp_check", ans,
               [crit, why])


# ---------------------------------------------------------------------------
# 7. Equation of a line parallel / perpendicular to a given line
#    through a given point (axis-parallel cases included)
# ---------------------------------------------------------------------------

def _eq_parallel_perp(q):
    if not re.search(_EQ_WORD, q, re.I):
        return None
    want = _check_verdict(q)
    if want not in ("parallel", "perpendicular"):
        return None
    pts = extract_points(q)
    hi = _hindi(q)
    # parallel / perpendicular to an AXIS through a point
    if re.search(r"x[-\s]?axis|x-अक्ष", q, re.I) and len(pts) == 1:
        x1, y1 = pts[0]
        horiz = (want == "parallel")
        if horiz:
            ans = f"y = {fmt_num(y1)}"
            steps = [
                ("x-अक्ष के समांतर रेखा क्षैतिज होती है: y = स्थिरांक"
                 if hi else
                 "A line parallel to the x-axis is horizontal: "
                 "y = constant"),
                f"y = {fmt_num(y1)}",
            ]
        else:
            ans = f"x = {fmt_num(x1)}"
            steps = [
                ("x-अक्ष के लंबवत रेखा ऊर्ध्वाधर होती है: x = स्थिरांक"
                 if hi else
                 "A line perpendicular to the x-axis is "
                 "vertical: x = constant"),
                f"x = {fmt_num(x1)}",
            ]
        return _mk("geometry", "w115_eq_parallel_perp", ans, steps)
    if re.search(r"y[-\s]?axis|y-अक्ष", q, re.I) and len(pts) == 1:
        x1, y1 = pts[0]
        if want == "parallel":
            ans = f"x = {fmt_num(x1)}"
            steps = [
                ("y-अक्ष के समांतर रेखा ऊर्ध्वाधर होती है: x = स्थिरांक"
                 if hi else
                 "A line parallel to the y-axis is vertical: "
                 "x = constant"),
                f"x = {fmt_num(x1)}",
            ]
        else:
            ans = f"y = {fmt_num(y1)}"
            steps = [
                ("y-अक्ष के लंबवत रेखा क्षैतिज होती है: y = स्थिरांक"
                 if hi else
                 "A line perpendicular to the y-axis is "
                 "horizontal: y = constant"),
                f"y = {fmt_num(y1)}",
            ]
        return _mk("geometry", "w115_eq_parallel_perp", ans, steps)
    lines = _find_lines(q)
    if len(lines) != 1 or len(pts) != 1:
        return None
    a, b, c = lines[0]
    x1, y1 = _frac_pt(pts[0])
    if want == "parallel":
        nc = -(a * x1 + b * y1)
        gen = _fmt_general(a, b, nc)
        steps = [
            (f"{_fmt_general(a, b, c)} के समांतर रेखा का रूप "
             f"{_fmt_val(a)}x + {_fmt_val(b)}y + C = 0 होता है।"
             if hi else
             f"A line parallel to {_fmt_general(a, b, c)} has "
             f"the form {_fmt_val(a)}x + {_fmt_val(b)}y + C = 0."),
            (f"यह बिंदु {_fmt_point(x1, y1)} से होकर जाती है, "
             f"इसलिए C = {_fmt_val(nc)}।"
             if hi else
             f"It passes through {_fmt_point(x1, y1)}, "
             f"so C = {_fmt_val(nc)}."),
            gen,
        ]
        return _mk("geometry", "w115_eq_parallel_perp", gen, steps)
    na, nb = b, -a
    nc = -(na * x1 + nb * y1)
    gen = _fmt_general(na, nb, nc)
    steps = [
        (f"{_fmt_general(a, b, c)} के लंबवत रेखा का रूप "
         f"{_fmt_val(b)}x - {_fmt_val(a)}y + C = 0 होता है।"
         if hi else
         f"A line perpendicular to {_fmt_general(a, b, c)} "
         f"has the form {_fmt_val(b)}x - {_fmt_val(a)}y + C = 0."),
        (f"यह बिंदु {_fmt_point(x1, y1)} से होकर जाती है, "
         f"इसलिए C = {_fmt_val(nc)}।"
         if hi else
         f"It passes through {_fmt_point(x1, y1)}, "
         f"so C = {_fmt_val(nc)}."),
        gen,
    ]
    return _mk("geometry", "w115_eq_parallel_perp", gen, steps)


def _frac_pt(p):
    x, y = p
    fx = Fraction(x) if isinstance(x, int) else Fraction(str(x))
    fy = Fraction(y) if isinstance(y, int) else Fraction(str(y))
    return fx, fy


# ---------------------------------------------------------------------------
# 8. Distances: point <-> line, two parallel lines, point <-> point
# ---------------------------------------------------------------------------

def _parallel_distance(q):
    if not re.search(_DIST_WORD, q, re.I):
        return None
    lines = _find_lines(q)
    if len(lines) != 2:
        return None
    (a1, b1, c1), (a2, b2, c2) = lines
    if not _is_zero(a1 * b2 - a2 * b1):
        return None  # not parallel — fall through honestly
    hi = _hindi(q)
    # scale line 2 so its (A, B) equals line 1's
    if not _is_zero(a1):
        if _is_zero(a2):
            return None
        k = a1 / a2
    else:
        if _is_zero(b2):
            return None
        k = b1 / b2
    c2s = c2 * k
    num = abs(c1 - c2s)
    s = a1 * a1 + b1 * b1
    d = _fmt_dist(num, s)
    steps = [
        ("दोनों रेखाओं की दिशा एक ही है (A और B समान अनुपात "
         "में), इसलिए वे समांतर हैं।"
         if hi else
         "Both lines have the same direction (A and B in "
         "the same ratio), so they are parallel."),
        ("समांतर रेखाओं के बीच की दूरी = |C1 - C2|/√(A² + B²)"
         if hi else
         "Distance between parallel lines = "
         "|C1 - C2|/√(A² + B²)"),
        (f"= |{_fmt_val(c1)} - ({_fmt_val(c2s)})|/"
         f"√({_fmt_val(a1)}² + {_fmt_val(b1)}²) = {d}"
         if hi else
         f"= |{_fmt_val(c1)} - ({_fmt_val(c2s)})|/"
         f"√({_fmt_val(a1)}² + {_fmt_val(b1)}²) = {d}"),
    ]
    return _mk("geometry", "w115_parallel_distance", d, steps)


def _point_line_distance(q):
    if not re.search(_DIST_WORD, q, re.I):
        return None
    lines = _find_lines(q)
    if len(lines) != 1:
        return None
    pts = extract_points(q)
    hi = _hindi(q)
    if len(pts) == 1:
        x1, y1 = _frac_pt(pts[0])
        who = _fmt_point(x1, y1)
    elif not pts and re.search(r"origin|मूल\s?बिंदु|मूलबिंदु|"
                               r"mool\s?bindu", q, re.I):
        x1, y1 = Fraction(0), Fraction(0)
        who = "(0, 0)"
    else:
        return None
    a, b, c = lines[0]
    num = abs(a * x1 + b * y1 + c)
    s = a * a + b * b
    d = _fmt_dist(num, s)
    steps = [
        (f"बिंदु {who} की रेखा Ax + By + C = 0 से दूरी "
         f"= |Ax1 + By1 + C|/√(A² + B²)"
         if hi else
         f"Distance of the point {who} from the line "
         f"Ax + By + C = 0 is |Ax1 + By1 + C|/√(A² + B²)"),
        (f"= |{_fmt_val(a)}×{_fmt_val(x1)} + {_fmt_val(b)}×"
         f"{_fmt_val(y1)} + {_fmt_val(c)}|/"
         f"√({_fmt_val(a)}² + {_fmt_val(b)}²) = {d}"
         if hi else
         f"= |{_fmt_val(a)}×{_fmt_val(x1)} + {_fmt_val(b)}×"
         f"{_fmt_val(y1)} + {_fmt_val(c)}|/"
         f"√({_fmt_val(a)}² + {_fmt_val(b)}²) = {d}"),
    ]
    return _mk("geometry", "w115_point_line_distance", d, steps)


def _point_point_distance(q):
    if not re.search(_DIST_WORD, q, re.I):
        return None
    if _find_lines(q):
        return None
    pts = extract_points(q)
    if len(pts) != 2:
        return None
    (x1, y1), (x2, y2) = pts
    hi = _hindi(q)
    s = (x2 - x1) ** 2 + (y2 - y1) ** 2
    # the distance is √s, i.e. num/√s with num = s
    num = Fraction(s) if isinstance(s, int) else Fraction(str(s))
    d = _fmt_dist(num, s)
    steps = [
        ("दो बिंदुओं के बीच की दूरी = √((x2 - x1)² + (y2 - y1)²)"
         if hi else
         "Distance between two points = "
         "√((x2 - x1)² + (y2 - y1)²)"),
        f"= √(({fmt_num(x2)} - {fmt_num(x1)})² + "
        f"({fmt_num(y2)} - {fmt_num(y1)})²) = √{fmt_num(s)} = {d}",
    ]
    return _mk("geometry", "w115_point_point_distance", d, steps)


# ---------------------------------------------------------------------------
# 9. Angle between two lines
# ---------------------------------------------------------------------------

def _angle_between(q):
    if not re.search(_ANGLE_WORD, q, re.I):
        return None
    if not re.search(r"between|बीच|ke\s+beech", q, re.I):
        return None
    hi = _hindi(q)
    m = re.search(r"(?:slopes?|प्रवणताएँ|प्रवणता)\s*"
                  r"(?:are|is|:|हैं)?\s*([+-]?)\s*(" + _NUM
                  + r")\s*(?:and|aur|और|,)\s*([+-]?)\s*(" + _NUM
                  + r")", q, re.I)
    lines = _find_lines(q)
    m1 = m2 = None
    src = None
    if m:
        m1 = _signed(m.group(1), m.group(2))
        m2 = _signed(m.group(3), m.group(4))
        src = (f"प्रवणताएँ m1 = {_fmt_val(m1)}, "
               f"m2 = {_fmt_val(m2)} दी गई हैं।"
               if hi else
               f"The slopes are given: m1 = {_fmt_val(m1)}, "
               f"m2 = {_fmt_val(m2)}.")
    elif len(lines) == 2:
        m1, m2 = _slope_of(lines[0]), _slope_of(lines[1])
        src = (f"रेखाओं की प्रवणताएँ: m1 = "
               f"{_fmt_val(m1) if m1 is not None else 'अपरिभाषित (ऊर्ध्वाधर)'}, "
               f"m2 = {_fmt_val(m2) if m2 is not None else 'अपरिभाषित (ऊर्ध्वाधर)'}"
               if hi else
               f"Slopes of the lines: m1 = "
               f"{_fmt_val(m1) if m1 is not None else 'undefined (vertical)'}, "
               f"m2 = {_fmt_val(m2) if m2 is not None else 'undefined (vertical)'}")
    if src is None:
        return None
    if m1 is None or m2 is None:
        # one line vertical: work with inclinations
        def incl(mm):
            if mm is None:
                return 90.0
            return _deg_from_slope(mm)
        d = abs(incl(m1) - incl(m2))
        if d > 90:
            d = 180 - d
        steps = [
            src,
            ("झुकावों का अंतर ही न्यून कोण है: "
             f"θ = {_fmt_deg(d)}"
             if hi else
             "The acute angle is the difference of the "
             f"inclinations: θ = {_fmt_deg(d)}"),
        ]
        return _mk("geometry", "w115_angle_between",
                   _fmt_deg(d), steps)
    den = 1 + m1 * m2
    if _is_zero(den):
        steps = [
            src,
            ("m1·m2 = -1 है, इसलिए रेखाएँ लंबवत हैं और उनके "
             "बीच का कोण 90° है।"
             if hi else
             "m1·m2 = -1, so the lines are perpendicular "
             "and the angle between them is 90°."),
        ]
        return _mk("geometry", "w115_angle_between", "90°", steps)
    t = abs(float((m2 - m1) / den))
    std = _std_from_tan(t)
    if std is not None:
        deg, disp = std
        steps = [
            src,
            ("tan θ = |(m2 - m1)/(1 + m1·m2)|"
             if hi else
             "tan θ = |(m2 - m1)/(1 + m1·m2)|"),
            f"tan θ = {disp}, इसलिए θ = {deg}°",
        ]
        return _mk("geometry", "w115_angle_between",
                   f"{deg}°", steps)
    deg = math.degrees(math.atan(t))
    raw = (m2 - m1) / den
    tans = _fmt_val(abs(raw) if isinstance(raw, Fraction)
                    else Fraction(t).limit_denominator(1000))
    steps = [
        src,
        ("tan θ = |(m2 - m1)/(1 + m1·m2)|"
         if hi else "tan θ = |(m2 - m1)/(1 + m1·m2)|"),
        f"tan θ = {tans}, इसलिए θ = tan⁻¹({tans}) ≈ {deg:.2f}°",
    ]
    return _mk("geometry", "w115_angle_between",
               f"tan⁻¹({tans}) ≈ {deg:.2f}°", steps)


# ---------------------------------------------------------------------------
# 10. Foot of the perpendicular; image (reflection) of a point
# ---------------------------------------------------------------------------

def _foot_image(q, image=False):
    trig = _IMAGE_WORD if image else _FOOT_WORD
    if not re.search(trig, q, re.I):
        return None
    lines = _find_lines(q)
    pts = extract_points(q)
    if len(lines) != 1 or len(pts) != 1:
        return None
    a, b, c = lines[0]
    x1, y1 = _frac_pt(pts[0])
    hi = _hindi(q)
    den = a * a + b * b
    if _is_zero(den):
        return None
    t = (a * x1 + b * y1 + c) / den
    k = 2 if image else 1
    fx, fy = x1 - k * a * t, y1 - k * b * t
    ans = _fmt_point(fx, fy)
    if image:
        steps = [
            (f"बिंदु {_fmt_point(x1, y1)} के प्रतिबिंब के लिए "
             f"(x - x1)/A = (y - y1)/B = "
             f"-2(Ax1 + By1 + C)/(A² + B²)"
             if hi else
             f"For the image of {_fmt_point(x1, y1)}: "
             f"(x - x1)/A = (y - y1)/B = "
             f"-2(Ax1 + By1 + C)/(A² + B²)"),
            (f"यहाँ अनुपात = {_fmt_val(-2 * t)}, इसलिए "
             f"प्रतिबिंब = {ans}"
             if hi else
             f"Here the ratio is {_fmt_val(-2 * t)}, "
             f"so the image is {ans}"),
        ]
        return _mk("geometry", "w115_image", ans, steps)
    steps = [
        (f"लंब के पाद के लिए (x - x1)/A = (y - y1)/B = "
         f"-(Ax1 + By1 + C)/(A² + B²)"
         if hi else
         f"For the foot of the perpendicular: "
         f"(x - x1)/A = (y - y1)/B = "
         f"-(Ax1 + By1 + C)/(A² + B²)"),
        (f"यहाँ अनुपात = {_fmt_val(-t)}, इसलिए पाद = {ans}"
         if hi else
         f"Here the ratio is {_fmt_val(-t)}, "
         f"so the foot is {ans}"),
    ]
    return _mk("geometry", "w115_foot", ans, steps)


# ---------------------------------------------------------------------------
# 11. Section formula — the dividing POINT (internal / external),
#     for the phrasings geometry.py's "divides" branch misses
# ---------------------------------------------------------------------------

def _division_point(q):
    if re.search(r"in\s+what\s+ratio|what\s+ratio|किस\s+अनुपात|"
                 r"axis|अक्ष", q, re.I):
        return None  # the ratio itself is the unknown there
    if not re.search(r"divid|विभाजित|विभाजन|बाँट|बांट", q, re.I):
        return None
    mr = re.search(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)", q)
    if not mr:
        return None
    pts = extract_points(q)
    if len(pts) != 2:
        return None
    if not re.search(r"coordinates|निर्देशांक|point|बिंदु|बिन्दु",
                     q, re.I):
        return None
    m_, n_ = Fraction(mr.group(1)), Fraction(mr.group(2))
    (x1, y1), (x2, y2) = _frac_pt(pts[0]), _frac_pt(pts[1])
    external = bool(re.search(r"external|बाह्य|बाहरी|बाहर\s*से",
                              q, re.I))
    hi = _hindi(q)
    if external:
        if m_ == n_:
            return None  # division at infinity — no such point
        px = (m_ * x2 - n_ * x1) / (m_ - n_)
        py = (m_ * y2 - n_ * y1) / (m_ - n_)
        steps = [
            ("बाह्य विभाजन का अनुभाग सूत्र: "
             "P = ((m·x2 - n·x1)/(m - n), (m·y2 - n·y1)/(m - n))"
             if hi else
             "Section formula (external division): "
             "P = ((m·x2 - n·x1)/(m - n), "
             "(m·y2 - n·y1)/(m - n))"),
            f"P = {_fmt_point(px, py)}",
        ]
    else:
        px = (m_ * x2 + n_ * x1) / (m_ + n_)
        py = (m_ * y2 + n_ * y1) / (m_ + n_)
        steps = [
            ("आंतरिक विभाजन का अनुभाग सूत्र: "
             "P = ((m·x2 + n·x1)/(m + n), (m·y2 + n·y1)/(m + n))"
             if hi else
             "Section formula (internal division): "
             "P = ((m·x2 + n·x1)/(m + n), "
             "(m·y2 + n·y1)/(m + n))"),
            (f"= (({_fmt_val(m_)}×{_fmt_val(x2)} + "
             f"{_fmt_val(n_)}×{_fmt_val(x1)})/{_fmt_val(m_ + n_)}, "
             f"({_fmt_val(m_)}×{_fmt_val(y2)} + "
             f"{_fmt_val(n_)}×{_fmt_val(y1)})/{_fmt_val(m_ + n_)})"
             if hi else
             f"= (({_fmt_val(m_)}×{_fmt_val(x2)} + "
             f"{_fmt_val(n_)}×{_fmt_val(x1)})/{_fmt_val(m_ + n_)}, "
             f"({_fmt_val(m_)}×{_fmt_val(y2)} + "
             f"{_fmt_val(n_)}×{_fmt_val(y1)})/{_fmt_val(m_ + n_)})"),
            f"P = {_fmt_point(px, py)}",
        ]
    return _mk("geometry", "w115_division_point",
               _fmt_point(px, py), steps)


# ---------------------------------------------------------------------------
# 12. Line through the intersection of two lines (family form)
# ---------------------------------------------------------------------------

def _line_through_intersection(q):
    if not re.search(_INTERSECT_WORD, q, re.I):
        return None
    if not re.search(_EQ_WORD, q, re.I):
        return None
    lines = _find_lines(q)
    if len(lines) < 2:
        return None
    (a1, b1, c1), (a2, b2, c2) = lines[0], lines[1]
    hi = _hindi(q)
    pts = extract_points(q)
    lam = None
    cond_step = None
    if len(lines) >= 3 and re.search(_PAR_WORD, q, re.I):
        a3, b3, _c3 = lines[2]
        # (A1 + λA2)·B3 = A3·(B1 + λB2)
        num = a3 * b1 - a1 * b3
        den = a2 * b3 - a3 * b2
        if _is_zero(den):
            return None
        lam = num / den
        cond_step = ("परिवार की रेखा तीसरी रेखा के समांतर हो, "
                     "इस शर्त से λ का मान मिलता है।"
                     if hi else
                     "The family line must be parallel to "
                     "the third line; that condition gives λ.")
    elif len(lines) >= 3 and re.search(_PERP_WORD, q, re.I):
        a3, b3, _c3 = lines[2]
        num = -(a1 * a3 + b1 * b3)
        den = a2 * a3 + b2 * b3
        if _is_zero(den):
            return None
        lam = num / den
        cond_step = ("परिवार की रेखा तीसरी रेखा के लंबवत हो, "
                     "इस शर्त से λ का मान मिलता है।"
                     if hi else
                     "The family line must be perpendicular "
                     "to the third line; that condition "
                     "gives λ.")
    elif len(pts) == 1:
        x0, y0 = _frac_pt(pts[0])
        num = -(a1 * x0 + b1 * y0 + c1)
        den = a2 * x0 + b2 * y0 + c2
        if _is_zero(den):
            if _is_zero(num):
                return None  # the point IS the intersection
            # the required line is L2 itself
            gen = _fmt_general(a2, b2, c2)
            steps = [
                ("दोनों रेखाओं के प्रतिच्छेद से जाने वाली रेखाओं "
                 "का परिवार: L1 + λL2 = 0"
                 if hi else
                 "Family of lines through the intersection: "
                 "L1 + λL2 = 0"),
                ("दिया गया बिंदु दूसरी रेखा पर स्थित है, इसलिए "
                 "अभीष्ट रेखा दूसरी रेखा ही है।"
                 if hi else
                 "The given point lies on the second line, "
                 "so the required line is the second line "
                 "itself."),
                gen,
            ]
            return _mk("geometry", "w115_intersection_line",
                       gen, steps)
        lam = num / den
        cond_step = (f"परिवार की रेखा बिंदु "
                     f"{_fmt_point(x0, y0)} से होकर जाती है, "
                     f"इस शर्त से λ का मान मिलता है।"
                     if hi else
                     f"The family line passes through "
                     f"{_fmt_point(x0, y0)}; that condition "
                     f"gives λ.")
    elif re.search(r"origin|मूल\s?बिंदु|मूलबिंदु", q, re.I):
        if _is_zero(c2):
            if _is_zero(c1):
                return None  # intersection IS the origin
            gen = _fmt_general(a2, b2, c2)
            steps = [
                ("दूसरी रेखा स्वयं मूल बिंदु से होकर जाती है, "
                 "इसलिए अभीष्ट रेखा वही है।"
                 if hi else
                 "The second line itself passes through "
                 "the origin, so it is the required line."),
                gen,
            ]
            return _mk("geometry", "w115_intersection_line",
                       gen, steps)
        lam = -c1 / c2
        cond_step = ("परिवार की रेखा मूल बिंदु से होकर जाती "
                     "है, इसलिए स्थिर पद 0 होगा — इससे λ मिलता है।"
                     if hi else
                     "The family line passes through the "
                     "origin, so its constant term is 0 — "
                     "that gives λ.")
    if lam is None:
        return None
    na, nb, nc = a1 + lam * a2, b1 + lam * b2, c1 + lam * c2
    if _is_zero(na) and _is_zero(nb):
        return None
    gen = _fmt_general(na, nb, nc)
    steps = [
        (f"परिवार: ({_fmt_general(a1, b1, c1)}) + "
         f"λ({_fmt_general(a2, b2, c2)}) = 0"
         if hi else
         f"Family: ({_fmt_general(a1, b1, c1)}) + "
         f"λ({_fmt_general(a2, b2, c2)}) = 0"),
        cond_step,
        f"λ = {_fmt_val(lam)} रखने पर: {gen}",
    ]
    return _mk("geometry", "w115_intersection_line", gen, steps)


# ---------------------------------------------------------------------------
# 13. Perpendicular bisector / locus of an equidistant point
# ---------------------------------------------------------------------------

def _bisector_locus(q):
    bisect_ask = re.search(_BISECT_WORD, q, re.I)
    locus_ask = re.search(_LOCUS_WORD, q, re.I) and re.search(
        r"equidistant|समदूरस्थ|समान\s*दूरी|बराबर\s*दूरी", q, re.I)
    if not bisect_ask and not locus_ask:
        return None
    pts = extract_points(q)
    if len(pts) != 2:
        return None
    (x1, y1), (x2, y2) = _frac_pt(pts[0]), _frac_pt(pts[1])
    hi = _hindi(q)
    a = 2 * (x2 - x1)
    b = 2 * (y2 - y1)
    c = (x1 * x1 + y1 * y1) - (x2 * x2 + y2 * y2)
    if _is_zero(a) and _is_zero(b):
        return None
    gen = _fmt_general(a, b, c)
    if locus_ask:
        steps = [
            ("माना बिंदुपथ पर कोई बिंदु P(x, y) है। P दोनों "
             "बिंदुओं से समदूरस्थ है, इसलिए PA = PB, अर्थात "
             "PA² = PB²।"
             if hi else
             "Let P(x, y) be a point on the locus. P is "
             "equidistant from both points, so PA = PB, "
             "i.e. PA² = PB²."),
            (f"(x - {_fmt_val(x1)})² + (y - {_fmt_val(y1)})² = "
             f"(x - {_fmt_val(x2)})² + (y - {_fmt_val(y2)})² "
             f"को सरल करने पर:"
             if hi else
             f"Simplifying (x - {_fmt_val(x1)})² + "
             f"(y - {_fmt_val(y1)})² = (x - {_fmt_val(x2)})² + "
             f"(y - {_fmt_val(y2)})² gives:"),
            gen,
        ]
        return _mk("geometry", "w115_locus", gen, steps)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    steps = [
        (f"मध्य बिंदु = {_fmt_point(mx, my)}"
         if hi else f"Midpoint = {_fmt_point(mx, my)}"),
        ("लंब समद्विभाजक इस मध्य बिंदु से होकर जाती है और "
         "रेखाखंड के लंबवत होती है।"
         if hi else
         "The perpendicular bisector passes through this "
         "midpoint and is perpendicular to the segment."),
        gen,
    ]
    return _mk("geometry", "w115_bisector", gen, steps)


# ---------------------------------------------------------------------------
# 14. Normal form of a line
# ---------------------------------------------------------------------------

def _normal_form(q):
    if not re.search(r"normal\s*form|अभिलंब\s*रूप|normal\s*roop",
                     q, re.I):
        return None
    lines = _find_lines(q)
    if len(lines) != 1:
        return None
    a, b, c = lines[0]
    hi = _hindi(q)
    s2 = a * a + b * b
    if _is_zero(s2):
        return None
    # orient so that p = -C/√(A²+B²) is positive
    if float(c) > 0:
        a, b, c = -a, -b, -c
    s = math.sqrt(float(s2))
    cos_a, sin_a = float(a) / s, float(b) / s
    alpha = math.degrees(math.atan2(sin_a, cos_a))
    if alpha < 0:
        alpha += 360.0
    p = _fmt_dist(abs(c), s2)
    astr = _fmt_deg(alpha)
    form = f"x cos {astr} + y sin {astr} = {p}"
    steps = [
        (f"√(A² + B²) = √{_fmt_val(s2)} से भाग देने और चिह्न "
         f"ऐसे रखने पर कि p > 0 हो:"
         if hi else
         f"Divide by √(A² + B²) = √{_fmt_val(s2)}, choosing "
         f"signs so that p > 0:"),
        form,
        (f"यहाँ p = {p} मूल बिंदु से रेखा की दूरी है और "
         f"α = {astr}।"
         if hi else
         f"Here p = {p} is the distance of the line from "
         f"the origin and α = {astr}."),
    ]
    return _mk("geometry", "w115_normal_form", form, steps)


# ---------------------------------------------------------------------------
# 15. Equation through two points (non-English phrasings —
#     geometry.py's branch needs the English words)
# ---------------------------------------------------------------------------

def _eq_two_points(q):
    if not re.search(_EQ_WORD, q, re.I):
        return None
    if _find_lines(q):
        return None
    pts = extract_points(q)
    if len(pts) != 2:
        return None
    if not re.search(r"through|passing|से\s*होकर|होकर\s*जाने|"
                     r"joining|मिलाने", q, re.I):
        return None
    (x1, y1), (x2, y2) = _frac_pt(pts[0]), _frac_pt(pts[1])
    hi = _hindi(q)
    if x2 == x1:
        ans = f"x = {_fmt_val(x1)}"
        steps = [
            ("दोनों बिंदुओं का x-निर्देशांक बराबर है, इसलिए "
             "रेखा ऊर्ध्वाधर है।"
             if hi else
             "Both points have the same x-coordinate, so "
             "the line is vertical."),
            ans,
        ]
        return _mk("geometry", "w115_eq_two_points", ans, steps)
    m = (y2 - y1) / (x2 - x1)
    c = y1 - m * x1
    steps = [
        (f"प्रवणता m = ({_fmt_val(y2)} - {_fmt_val(y1)})/"
         f"({_fmt_val(x2)} - {_fmt_val(x1)}) = {_fmt_val(m)}"
         if hi else
         f"Slope m = ({_fmt_val(y2)} - {_fmt_val(y1)})/"
         f"({_fmt_val(x2)} - {_fmt_val(x1)}) = {_fmt_val(m)}"),
        (f"बिंदु {_fmt_point(x1, y1)} से बिंदु-ढाल रूप लगाने पर:"
         if hi else
         f"Point-slope form through {_fmt_point(x1, y1)}:"),
        _fmt_slope_form(m, c),
    ]
    return _mk("geometry", "w115_eq_two_points",
               _fmt_slope_form(m, c), steps)


# ---------------------------------------------------------------------------
# Dispatcher (failure-gate entry, like solve_papers10 / solve_gaps103)
# ---------------------------------------------------------------------------

_SCHEMAS = [
    _normal_form, _line_through_intersection,
    lambda q: _foot_image(q, image=False),
    lambda q: _foot_image(q, image=True),
    _bisector_locus, _parallel_distance, _point_line_distance,
    _point_point_distance, _angle_between,
    _parallel_perp_check, _eq_parallel_perp, _division_point,
    _intercept_form, _eq_from_intercepts, _eq_slope_intercept,
    _convert_form, _eq_two_points, _slope, _inclination,
]


def solve_rekha(question):
    """Wave 115 straight-line schemas; None unless one of
    them matches the question completely."""
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


# ---------------------------------------------------------------------------
# Upgrade hook (fallback.py, next to degree_upgrade): the
# hijacked asks whose primary result is "real" — a system
# solution served for a yes/no check, an angle ask or a
# through-intersection ask; the ratio echoed for a dividing-
# point ask; the segment's own line served for its bisector.
# Fires only when the strict rekha schema settles the ask
# AND the served answer is verifiably not that answer.
# ---------------------------------------------------------------------------

def rekha_upgrade(question, result):
    if not isinstance(result, dict):
        return None
    op = result.get("op")
    q = _prep(question)
    try:
        if op == "system":
            for schema in (_parallel_perp_check, _angle_between,
                           _line_through_intersection):
                out = schema(q)
                if out is not None:
                    return out
            return None
        if op == "hindi_equation":
            return _angle_between(q)
        if op == "ratio":
            return _division_point(q)
        if op == "equation":
            # a slope ask answered with the line itself
            # echoed back ("Find the slope of the line
            # x = 4" -> "x = 4"): upgrade only when the
            # served answer parses to the very line in the
            # question and the slope schema settles it.
            if not re.search(_SLOPE_WORD, q, re.I):
                return None
            lines = _find_lines(q)
            if len(lines) != 1:
                return None
            ans_lines = _find_lines(str(result.get("answer", "")))
            if len(ans_lines) != 1:
                return None
            (a1, b1, c1), (a2, b2, c2) = lines[0], ans_lines[0]
            if _is_zero(a1 * b2 - a2 * b1) and \
                    _is_zero(a1 * c2 - a2 * c1) and \
                    _is_zero(b1 * c2 - b2 * c1):
                return _slope(q)
            return None
        if op == "line equation":
            out = _bisector_locus(q)
            if out is None:
                return None
            # upgrade only when the served line is the
            # segment's OWN line (it passes through both
            # given points) — never displace a real bisector
            ans_lines = _find_lines(str(result.get("answer", "")))
            pts = extract_points(q)
            if len(ans_lines) != 1 or len(pts) != 2:
                return None
            a, b, c = ans_lines[0]
            (x1, y1), (x2, y2) = pts
            if _is_zero(a * x1 + b * y1 + c) and \
                    _is_zero(a * x2 + b * y2 + c):
                return out
            return None
    except Exception:
        return None
    return None
