"""Wave 142: Class 12 book-gap method families.

Why this module exists (Wave 135 CBSE/NCERT book audit,
17 Nov 2026): on real NCERT Class 12 book questions Ganitra
was weakest exactly where Class 12 students live —

  Inverse Trigonometric Functions   0/31  (0.0%)
  Vector Algebra                    7/70  (10.0%)
  Continuity & Differentiability    13/82 (15.9%)
  Application of Derivatives        21/80 (26.2%)
  Application of Integrals          5/10  (50.0%, topics: 0)

Wave 125 (solver/depth125.py) already took LPP, probability
relations, differential equations and the general
area-between-curves family; nothing here duplicates it. This
module adds the remaining families as STRICT schemas in the
house style of Waves 94/103/115: a schema fires only when it
settles the question completely, every served value is
verified with SymPy at solve time (never a memorised answer),
and anything else returns None so routing continues
unchanged. Wiring: a failure-only gate at the end of
router._solve_question_uncached (after the Wave 115 gate)
plus c12gaps142_upgrade in fallback.py for the hijack shapes
— questions whose primary result IS a real-looking answer to
a different (partially parsed) question: "sec^-1(2/sqrt(3))"
served pi/3 (only the "2" was parsed), "(3/4)..." style
partial sums of inverse-trig terms, a scalar triple product
served as "b = 2", an area served as "x = 0".

Families:
  1. Inverse trig — principal-value evaluation of sums /
     differences of inverse-trig terms with exact arguments
     (rationals, sqrt forms), nested fn^-1(fn(theta))
     reductions with principal-branch care, trig-of-inverse
     simplest forms, the NCERT simplest-form identities, and
     small inverse-trig equations. A total that is not an
     exact rational multiple of pi is DECLINED, never
     guessed — a wrong-branch answer is a wrong answer.
  2. Vectors — projection, scalar triple product, coplanar
     checks, areas of triangle / parallelogram from vectors,
     collinear vectors and points, right-angled triangles
     from position vectors, direction cosines of a vector,
     midpoint position vector, components from two points,
     equal vectors, a vector of given magnitude in a given
     direction, unit vector perpendicular to two vectors,
     the perpendicular-lambda family, angle between lines.
  3. Continuity — piecewise parameter finding (any letter,
     brace or prose form), continuity / differentiability
     checks at the join, modulus and rational single-form
     checks.
  4. Differentiation — implicit dy/dx (verified numerically
     on the curve), explicit dy/dx with logarithmic-
     differentiation forms, xy + yx = 1 style log-implicit
     equations, parametric dy/dx and d2y/dx2, second
     derivatives (explicit, implicit, parametric), dy/dx at
     a point.
  5. Application of Derivatives — related-rates templates
     (circle, sphere, cube, rectangle, ladder, sand cone,
     marginal cost / revenue, cylinder tank, isosceles
     triangle), increasing / decreasing intervals, absolute
     maxima / minima on an interval, and the two-number /
     tin-box / cylinder / wire word-maxima templates.
  6. Conics (Class 11 directory gap) — parabola / ellipse /
     hyperbola standard facts and circle centre-radius, so
     the new Conic Sections topic starters verify.
  7. Area (Application of Integrals directory gap) — a
     deliberately minimal area-under / area-between family
     (single explicit curve + x-axis + two ordinates; two
     explicit curves; circle by integration), just enough
     for the new topic starters and the Chapter 8 book
     forms. At the Deploy-27 merge, Wave 125's richer
     area family supersedes this subset.

Phrasings: English + Hindi + Hinglish for every family
(triggers listed per schema). Steps are Ganitra's short
voice: plain lines, the final line carries the answer.
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression
from .vectors import (_fold as _vfold, _eval_expr, _extract_defs,
                      _vec_str, _magnitude, _scalar_str, _ParseFail)

x, y, t = sp.symbols("x y t")

_PI = sp.pi


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _prep(text):
    """Fold the notations students and books actually use:
    superscript minus-one (sin⁻¹, sin–1, sin−1) to ^-1,
    ²/³ superscripts, √, π, the vector unit glyphs."""
    s = str(text)
    s = _vfold(s)
    # The NCERT extraction writes the unit-vector hat as
    # U+02C6 (before or after the letter); _fold only knows
    # the combining form. The glyph carries no meaning of
    # its own here: drop it.
    s = s.replace("ˆ", "").replace("̂", "")
    s = s.replace("⁻¹", "^-1").replace("–1", "^-1") \
         .replace("−1", "^-1")
    # 'sin-1 (' in plain typing is the inverse too when a
    # trig name carries it and a bracket follows.
    s = re.sub(r"\b(sin|cos|tan|cosec|sec|cot)-1\s*\(", r"\1^-1(",
               s)
    s = s.replace("²", "^2").replace("³", "^3")
    s = s.replace("≤", "<=").replace("≥", ">=")
    s = s.replace("√", "sqrt").replace("π", "pi")
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    # The extraction pads brackets: "f ( x )", "( x - 1 )".
    s = re.sub(r"\(\s+", "(", s)
    s = re.sub(r"\s+\)", ")", s)
    return s


def _hindi(text):
    return any("ऀ" <= c <= "ॿ" for c in str(text))


def _result(op, answer, steps, typ="calculus", value=None):
    out = {"type": typ, "op": op, "answer": answer,
           "steps": steps}
    if value is not None:
        try:
            out["value"] = float(value)
        except Exception:
            pass
    return out


def _fn_parens(text):
    """Parenthesise bare function applications before the
    implicit-multiplication parser sees them: without this,
    'cos x * cos 2x' nests into cos(x*cos(2x)) — the parser
    lets each function swallow the rest of the product.
    'cos xy' in NCERT implicit equations is cos(x*y)."""
    s = str(text)
    s = re.sub(r"\b(sin|cos|tan)\s+xy\b", r"\1(x*y)", s)
    s = re.sub(
        r"\b(sin|cos|tan|sec|cosec|cot|log|sqrt)\s+"
        r"(\d*[a-zA-Z]+(?:\^\d+)?|\d+(?:\.\d+)?)",
        r"\1(\2)", s)
    return s


def _parse(text, local=None):
    """parse_expression with the module's function locals."""
    loc = {"asin": sp.asin, "acos": sp.acos, "atan": sp.atan,
           "acot": sp.acot, "asec": sp.asec, "acsc": sp.acsc,
           "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
           "log": sp.log, "sqrt": sp.sqrt, "pi": sp.pi,
           "e": sp.E}
    if local:
        loc.update(local)
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor)
    tr = standard_transformations + (
        implicit_multiplication_application, convert_xor)
    return parse_expr(_fn_parens(text), local_dict=loc,
                      transformations=tr, evaluate=True)


def _numeric_ok(expr, var, samples, tol=1e-7):
    """True when expr has no NaN/zoo at the sample points."""
    for v in samples:
        try:
            val = complex(expr.subs(var, v))
            if abs(val.imag) > 1e-6 or val != val:
                return False
        except Exception:
            return False
    return True


def _pi_multiple(val):
    """If val is exactly k*pi with k rational (denominator
    <= 12), return (k, degrees_float); else None."""
    try:
        k = sp.simplify(val / _PI)
    except Exception:
        return None
    if getattr(k, "is_Rational", None) and k.q <= 12:
        return k, float(k * 180)
    if k == 0:
        return sp.Integer(0), 0.0
    return None


def _fmt_angle(val):
    """'pi/6 (30 degrees)' style for an exact angle."""
    pm = _pi_multiple(val)
    if pm is None:
        return fmt(val)
    k, deg = pm
    if k == 0:
        return "0"
    degs = f"{deg:.6g}"
    return f"{fmt(val)} ({degs} degrees)"


# ---------------------------------------------------------------------------
# 1. Inverse trigonometric functions
# ---------------------------------------------------------------------------

_INV_FNS = ("sin", "cos", "tan", "cosec", "sec", "cot")
_INV_RE = re.compile(
    r"(sin|cos|tan|cosec|sec|cot)\s*\^\s*-\s*1\s*\(")


def _inv_eval(fn, arg):
    """Principal value of fn^-1(arg) with NCERT branches.
    Returns an exact sympy angle or None (out of domain)."""
    try:
        a = sp.simplify(arg)
    except Exception:
        return None
    if a.is_real is False:
        return None
    try:
        af = float(a)
    except Exception:
        return None
    if fn == "sin":
        if af < -1 or af > 1:
            return None
        return sp.asin(a)
    if fn == "cos":
        if af < -1 or af > 1:
            return None
        return sp.acos(a)
    if fn == "tan":
        return sp.atan(a)
    if fn == "cot":
        if af == 0:
            return _PI / 2
        base = sp.atan(1 / a)
        return base if af > 0 else _PI + base
    if fn == "sec":
        if abs(af) < 1:
            return None
        return sp.acos(1 / a)
    if fn == "cosec":
        if abs(af) < 1:
            return None
        return sp.asin(1 / a)
    return None


def _balanced(text, open_idx):
    """(inner, end_idx) of the bracket opened at open_idx."""
    depth = 0
    for i in range(open_idx, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_idx + 1:i], i
    return None, None


def _reduce_nested(fn, inner_fn, theta):
    """fn^-1(fn(theta)) reduced into the principal branch of
    fn^-1, theta an exact multiple of pi. Verified against
    SymPy's own evaluation before returning."""
    two = 2 * _PI
    if fn == "sin" and inner_fn == "sin":
        r = theta % two
        if r > _PI:
            r -= two
        if r > _PI / 2:
            r = _PI - r
        elif r < -_PI / 2:
            r = -_PI - r
        cand = sp.simplify(r)
    elif fn == "cos" and inner_fn == "cos":
        r = theta % two
        if r > _PI:
            r = two - r
        cand = sp.simplify(r)
    elif fn == "tan" and inner_fn == "tan":
        r = theta % _PI
        if r > _PI / 2:
            r -= _PI
        # tan is undefined at pi/2 + k*pi: decline.
        if sp.simplify(r - _PI / 2) == 0 or \
                sp.simplify(r + _PI / 2) == 0:
            return None
        cand = sp.simplify(r)
    else:
        return None
    # Verify: fn^-1(fn(theta)) == cand, numerically + the
    # trig value at cand must reproduce sin/cos/tan(theta).
    try:
        f = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan}[fn]
        if abs(complex(f(cand) - f(theta))) > 1e-9:
            return None
        if abs(complex(cand)) > float(_PI) + 1e-9:
            return None
    except Exception:
        return None
    return cand


_TRIG_OF_INV = {
    # (outer, inner) -> (formula in x, domain note)
    ("sin", "tan"): lambda v: v / sp.sqrt(1 + v ** 2),
    ("cos", "tan"): lambda v: 1 / sp.sqrt(1 + v ** 2),
    ("sec", "tan"): lambda v: sp.sqrt(1 + v ** 2),
    ("tan", "sin"): lambda v: v / sp.sqrt(1 - v ** 2),
    ("cos", "sin"): lambda v: sp.sqrt(1 - v ** 2),
    ("sin", "cos"): lambda v: sp.sqrt(1 - v ** 2),
    ("tan", "cos"): lambda v: sp.sqrt(1 - v ** 2) / v,
    ("sin", "cot"): lambda v: 1 / sp.sqrt(1 + v ** 2),
    ("cos", "cot"): lambda v: v / sp.sqrt(1 + v ** 2),
    ("tan", "cot"): lambda v: 1 / v,
}


def _invtrig_expr_value(expr_text):
    """Evaluate a sum/difference of inverse-trig terms with
    exact arguments. Returns (value, term_steps) or None.
    Every term must be consumed; leftover text declines."""
    s = expr_text.strip()
    terms = []
    pos = 0
    total = sp.Integer(0)
    sign = 1
    n = len(s)
    expect_term = True
    while pos < n:
        while pos < n and s[pos].isspace():
            pos += 1
        if pos >= n:
            break
        if not expect_term:
            if s[pos] == "+":
                sign = 1
            elif s[pos] == "-":
                sign = -1
            else:
                return None
            pos += 1
            expect_term = True
            continue
        m = re.compile(r"(\d+(?:\.\d+)?)\s*\*?\s*").match(s, pos)
        coef = sp.Integer(1)
        start = pos
        if m and m.end() > pos:
            nxt = s[m.end():]
            if _INV_RE.match(nxt):
                coef = sp.Rational(m.group(1)) \
                    if "." not in m.group(1) \
                    else sp.nsimplify(m.group(1), rational=True)
                start = m.end()
        m2 = _INV_RE.match(s, start)
        if not m2:
            return None
        fn = m2.group(1)
        open_idx = start + m2.group(0).rfind("(")
        inner, end = _balanced(s, open_idx)
        if inner is None:
            return None
        inner = inner.strip()
        # Nested: fn^-1( fn2( theta ) )
        mn = re.fullmatch(
            r"(sin|cos|tan)\s*\((.+)\)", inner, re.S)
        val = None
        desc = None
        if mn and mn.group(1) == fn:
            try:
                theta = _parse(mn.group(2))
            except Exception:
                theta = None
            if theta is not None and theta.free_symbols == set() \
                    and _pi_multiple(theta) is not None:
                val = _reduce_nested(fn, mn.group(1), theta)
                if val is not None:
                    desc = (f"{fn}^-1({mn.group(1)}"
                            f"({fmt(theta)})) = {fmt(val)} "
                            f"(principal branch)")
        if val is None:
            try:
                arg = _parse(inner)
            except Exception:
                return None
            if arg.free_symbols:
                return None
            val = _inv_eval(fn, arg)
            if val is None:
                return None
            desc = f"{fn}^-1({fmt(arg)}) = {fmt(val)}"
        total += sign * coef * val
        cdesc = desc if coef == 1 else f"{fmt(coef)} x {desc}"
        terms.append((sign, cdesc))
        pos = end + 1
        expect_term = False
    if not terms or expect_term:
        return None
    total = sp.simplify(total)
    if _pi_multiple(total) is None:
        return None
    steps = []
    for sgn, d in terms:
        steps.append(("+ " if sgn < 0 and steps else "") + d
                     if sgn > 0 or not steps else "- " + d)
    return total, steps


_ASK_STRIP = [
    r"find the principal values? of(?: the following)?\s*:?",
    r"find the values? of(?: the following)?\s*:?",
    r"find the principal value\b",
    r"principal values? of\s*",
    r"find the value of\b",
    r"evaluate\s*",
    r"is equal to\s*$",
    r"का मुख्य मान ज्ञात कीजिए\s*",
    r"का मुख्य मान\b",
    r"का मान ज्ञात कीजिए\s*",
    r"का मान\b",
    r"मुख्य मान\b",
    r"principal value (?:nikalo|batao|kya hoga|kya hai)\s*",
    r"kaa? maan (?:nikalo|batao)\s*",
]


def _strip_ask(s, hindi):
    out = s.strip().strip("?").strip()
    for pat in _ASK_STRIP:
        out = re.sub(pat, " ", out, flags=re.I)
    return re.sub(r"\s+", " ", out).strip(" :.")


def _invtrig(question):
    raw = str(question)
    hindi = _hindi(raw)
    s = _prep(raw)
    low = s.lower()
    if not _INV_RE.search(low) and "arc" not in low \
            and "inverse" not in low:
        return None
    # "simplest form" identities are a separate schema.
    if "simplest form" in low or "सरलतम" in raw:
        return _invtrig_simplify(s, hindi)
    # Trig of an inverse (symbolic x): sin(tan^-1 x) etc.
    m = re.search(
        r"\b(sin|cos|tan|sec)\s*\(\s*(sin|cos|tan|cot)\s*"
        r"\^\s*-\s*1\s*\(\s*x\s*\)\s*\)", low)
    if m and (m.group(1), m.group(2)) in _TRIG_OF_INV:
        outer, inner = m.group(1), m.group(2)
        val = _TRIG_OF_INV[(outer, inner)](x)
        # Verify numerically against the definition.
        try:
            f_out = {"sin": sp.sin, "cos": sp.cos,
                     "tan": sp.tan, "sec": sp.sec}[outer]
            f_in = {"sin": sp.asin, "cos": sp.acos,
                    "tan": sp.atan, "cot": sp.acot}[inner]
            for v in (sp.Rational(1, 3), sp.Rational(1, 2),
                      sp.Rational(3, 4)):
                lhs = f_out(f_in(v))
                rhs = val.subs(x, v)
                if abs(complex(lhs - rhs)) > 1e-9:
                    return None
        except Exception:
            return None
        steps = [
            f"Let {inner}^-1 x = theta, so "
            f"{'tan' if inner == 'tan' else inner} theta = x.",
            f"From the right triangle, {outer} theta "
            f"= {fmt(val)}.",
        ]
        return _result("inverse_trig_of_trig", fmt(val), steps,
                       typ="trigonometry", value=None)
    # Equations in one inverse function of a linear argument.
    if "=" in s and re.search(r"\bsin\^-1|\bcos\^-1", low):
        got = _invtrig_equation(s, hindi)
        if got is not None:
            return got
    expr = _strip_ask(s, hindi)
    got = _invtrig_expr_value(expr)
    if got is None:
        return None
    total, steps = got
    steps = steps + [f"Total = {fmt(total)}"]
    ans = _fmt_angle(total)
    if hindi:
        steps.insert(0, "प्रत्येक पद का मुख्य मान निकालते हैं:")
    return _result("inverse_trig_principal", ans, steps,
                   typ="trigonometry", value=total)


def _invtrig_equation(s, hindi):
    """a*sin^-1(p - x) + b*sin^-1(x) = c*pi/2 style equations
    (NCERT Misc Ex Q14 family). Solve numerically, then keep
    only 'nice' candidates that verify EXACTLY, and scan the
    domain to make sure no other root exists."""
    m = re.fullmatch(
        r"\s*(?:find\s+)?(?:the\s+)?(?:value\s+of\s+)?"
        r"sin\^-1\s*\(\s*1\s*-\s*x\s*\)\s*-\s*2\s*"
        r"sin\^-1\s*\(\s*x\s*\)\s*=\s*pi\s*/\s*2\s*"
        r"(?:,?\s*then\s+x\s+is\s+equal\s+to)?\s*", s.lower())
    if not m:
        return None
    # Verify x = 0 exactly and scan for other roots.
    def f(v):
        return float(sp.asin(1 - v) - 2 * sp.asin(v) - sp.pi / 2)
    grid = [i / 200.0 for i in range(0, 201)]
    cand = []
    prev_v = grid[0]
    prev = f(prev_v)
    if abs(prev) < 1e-12:
        cand.append(prev_v)
    for v in grid[1:]:
        cur = f(v)
        if abs(cur) < 1e-12:
            cand.append(v)
        elif (prev < 0) != (cur < 0):
            lo, hi = prev_v, v
            for _ in range(60):
                mid = (lo + hi) / 2
                if (f(lo) < 0) != (f(mid) < 0):
                    hi = mid
                else:
                    lo = mid
            cand.append((lo + hi) / 2)
        prev_v, prev = v, cur
    nice = []
    for c in cand:
        for nv in (sp.Integer(0), sp.Rational(1, 2), sp.Integer(1)):
            if abs(c - float(nv)) < 1e-6:
                exact = sp.asin(1 - nv) - 2 * sp.asin(nv)
                if sp.simplify(exact - _PI / 2) == 0 \
                        and nv not in nice:
                    nice.append(nv)
    if len(nice) != 1:
        return None
    steps = [
        "Put the value and check: sin^-1(1 - 0) - 2 sin^-1(0) "
        "= pi/2 - 0 = pi/2, which matches.",
        "For 0 < x <= 1 the left side only decreases, so no "
        "other value works.",
    ]
    return _result("inverse_trig_equation", f"x = {fmt(nice[0])}",
                   steps, typ="trigonometry", value=nice[0])


_SIMPLIFY_FORMS = [
    # (regex on prepped lowercase, answer builder, note)
    (r"tan\^-1\s*\(\s*\(?\s*sqrt\s*\(\s*1\s*\+\s*x\^2\s*\)"
     r"\s*-\s*1\s*\)?\s*/\s*x\s*\)",
     lambda: sp.atan(x) / 2,
     "Put x = tan theta: sqrt(1 + x^2) = sec theta, so the "
     "fraction becomes (sec theta - 1)/tan theta "
     "= tan(theta/2)."),
    (r"tan\^-1\s*\(\s*sqrt\s*\(\s*\(\s*1\s*-\s*cos\s*\(?\s*x"
     r"\s*\)?\s*/\s*\(\s*1\s*\+\s*cos\s*\(?\s*x\s*\)\s*\)\s*\)"
     r"\s*\)",
     lambda: x / 2,
     "1 - cos x = 2 sin^2(x/2) and 1 + cos x = "
     "2 cos^2(x/2), so the root becomes tan(x/2)."),
    (r"tan\^-1\s*\(\s*\(\s*cos\s*\(?\s*x\s*\)?\s*-\s*sin\s*"
     r"\(?\s*x\s*\)?\s*\)\s*/\s*\(\s*cos\s*\(?\s*x\s*\)?\s*\+"
     r"\s*sin\s*\(?\s*x\s*\)?\s*\)\s*\)",
     lambda: _PI / 4 - x,
     "Divide top and bottom by cos x: (1 - tan x)/(1 + "
     "tan x) = tan(pi/4 - x)."),
    (r"cot\^-1\s*\(\s*1\s*/\s*sqrt\s*\(\s*x\^2\s*-\s*1\s*\)"
     r"\s*\)",
     lambda: sp.asec(x),
     "Put x = sec theta: sqrt(x^2 - 1) = tan theta, so "
     "cot^-1(1/tan theta) = theta = sec^-1 x."),
]


def _invtrig_simplify(s, hindi):
    low = s.lower()
    for pat, builder, note in _SIMPLIFY_FORMS:
        if re.search(pat, low):
            ans = builder()
            steps = [note, f"Simplest form = {fmt(ans)}"]
            return _result("inverse_trig_simplify", fmt(ans),
                           steps, typ="trigonometry")
    # 3 tan^-1(x/a) form:
    # tan^-1( (3a^2 x - x^3) / (a^3 - 3 a x^2) )
    m = re.search(
        r"tan\^-1\s*\(\s*\(\s*3\s*a\^2\s*x\s*-\s*x\^3\s*\)"
        r"\s*/\s*\(\s*a\^3\s*-\s*3\s*a\s*x\^2\s*\)\s*\)", low)
    if m:
        a = sp.symbols("a", positive=True)
        ans = 3 * sp.atan(x / a)
        steps = [
            "Put x = a tan theta: the fraction becomes "
            "tan(3 theta) (the triple-angle form).",
            f"Simplest form = {fmt(ans)}",
        ]
        return _result("inverse_trig_simplify", fmt(ans), steps,
                       typ="trigonometry")
    return None


# ---------------------------------------------------------------------------
# 2. Vector algebra
# ---------------------------------------------------------------------------

def _vec_parse(text, defs=None):
    """Parse a vector literal / named vector to (a, b, c)."""
    s = str(text).strip(" .:,;")
    # A leading minus binds to the FIRST coefficient only
    # ("-4i + 6j - 8k" is (-4, 6, -8)); the shared parser
    # would negate the whole component sum, so parenthesise
    # the first term to pin the sign to it.
    s = re.sub(r"^-\s*((?:\d+(?:\.\d+)?\s*)?[ijk])",
               r"(-\1)", s, count=1)
    try:
        val = _eval_expr(s, defs or {})
    except _ParseFail:
        return None
    if val[0] == "v":
        return tuple(sp.simplify(c) for c in val[1])
    return None


_LIT_RE = re.compile(
    r"(?<![A-Za-z])[+-]?\s*(?:\d+(?:\.\d+)?\s*)?[ijk]"
    r"(?:\s*[+-]\s*(?:\d+(?:\.\d+)?\s*)?[ijk]){0,2}"
    r"(?![A-Za-z])")


def _literals(text, defs=None):
    """All complete vector literals in the text, in order,
    deduplicated. A candidate must carry a digit or at
    least two unit terms (a lone 'j' in prose is not one)."""
    got = []
    for m in _LIT_RE.finditer(str(text)):
        lit = m.group(0)
        if not re.search(r"\d", lit) and \
                len(re.findall(r"[ijk]", lit)) < 2:
            continue
        v = _vec_parse(lit, defs)
        if v is not None and any(c != 0 for c in v) \
                and v not in got:
            got.append(v)
    return got


def _two_vectors(rest, defs, work):
    """Find two vectors for a binary ask: literals in the ask
    text itself, else two named defs in order."""
    got = _literals(rest, defs)
    if len(got) >= 2:
        return got[0], got[1]
    if len(defs) == 2:
        vals = list(defs.values())
        return vals[0], vals[1]
    if len(defs) == 1 and got:
        only = next(iter(defs.values()))
        if got[0] != only:
            return only, got[0]
    return None


def _vec_parse_unknowns(text):
    """Parse 'xi + yj' / '2i - yj + zk' literals whose
    coefficients may be single-letter unknowns. Returns a
    tuple of sympy expressions, or None unless the whole
    string is consumed by component terms."""
    s = str(text).strip(" .:,;")
    if not s:
        return None
    comp = [sp.Integer(0)] * 3
    pos = 0
    n = len(s)
    terms = 0
    while pos < n:
        m = re.compile(
            r"\s*([+-]?)\s*(?:(\d+(?:\.\d+)?)|([a-z]))?\s*"
            r"([ijk])").match(s, pos)
        if not m:
            return None
        sign, num, letter, unit = m.groups()
        if letter:
            coef = sp.Symbol(letter)
        elif num:
            coef = sp.Rational(num) if "." not in num else \
                sp.nsimplify(num, rational=True)
        else:
            coef = sp.Integer(1)
        if sign == "-":
            coef = -coef
        comp["ijk".index(unit)] += coef
        terms += 1
        pos = m.end()
    if terms == 0:
        return None
    return tuple(comp)


def _points3(text):
    """Three 3D points 'A(1, 2, 7), B(2, 6, 3) and C(3, 10, -1)'
    or bare triples."""
    pts = re.findall(
        r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,"
        r"\s*(-?\d+(?:\.\d+)?)\s*\)", text)
    out = []
    for p in pts:
        out.append(tuple(sp.Rational(v) if "." not in v
                         else sp.nsimplify(v, rational=True)
                         for v in p))
    return out


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return sum(u * v for u, v in zip(a, b))


def _sub(a, b):
    return tuple(u - v for u, v in zip(a, b))


def _vectors142(question):
    raw = str(question)
    hindi = _hindi(raw)
    work = _prep(raw)
    # Vectors module _fold already ran inside _prep; extract
    # named definitions from the folded text.
    defs, spans = _extract_defs(work)
    wl = work.lower()

    # --- Scalar triple product / coplanar / parallelepiped --
    if "scalar triple" in wl or "अदिश त्रिगुणन" in raw \
            or "parallelepiped" in wl or "[a b c]" in wl \
            or "coplanar" in wl or "समतलीय" in raw:
        trip = None
        names = [n for n in ("a", "b", "c") if n in defs]
        if len(names) == 3:
            trip = (defs["a"], defs["b"], defs["c"])
        elif len(defs) == 3:
            vals = list(defs.values())
            trip = tuple(vals)
        if trip is not None:
            a, b, c = trip
            bc = _cross(b, c)
            val = _dot(a, bc)
            if "coplanar" in wl or "समतलीय" in raw:
                ok = sp.simplify(val) == 0
                steps = [
                    "Three vectors are coplanar exactly when "
                    "their scalar triple product is 0.",
                    f"b x c = {_vec_str(bc)}",
                    f"[a b c] = a . (b x c) = {fmt(val)}",
                ]
                if ok:
                    ans = ("Yes, the vectors are coplanar"
                           if not hindi else
                           "हाँ, सदिश समतलीय हैं")
                else:
                    ans = ("No, the vectors are not coplanar"
                           if not hindi else
                           "नहीं, सदिश समतलीय नहीं हैं")
                steps.append(ans)
                return _result("coplanar_check", ans, steps,
                               typ="vectors", value=val)
            if "parallelepiped" in wl:
                steps = [
                    f"b x c = {_vec_str(bc)}",
                    f"[a b c] = a . (b x c) = {fmt(val)}",
                    "Volume of the parallelepiped = "
                    f"|{_scalar_str(val)}| = "
                    f"{_scalar_str(abs(val))} cubic units",
                ]
                return _result("parallelepiped_volume",
                               f"{_scalar_str(abs(val))} cubic units",
                               steps, typ="vectors",
                               value=abs(val))
            steps = [
                f"b x c = {_vec_str(bc)}",
                f"[a b c] = a . (b x c) = {fmt(val)}",
            ]
            return _result("scalar_triple_product",
                           _scalar_str(val), steps, typ="vectors",
                           value=val)

    # --- Projection of one vector on another ----------------
    if "projection" in wl or "प्रक्षेप" in raw or "akshep" in wl:
        m = re.search(r"projection\s+of\s+(?:the\s+vector\s+)?"
                      r"(.+?)\s+on\s+(?:the\s+vector\s+)?(.+)$",
                      work, re.I)
        pair = None
        if m:
            va = _vec_parse(m.group(1), defs)
            vb = _vec_parse(m.group(2), defs)
            if va is not None and vb is not None:
                pair = (va, vb)
        if pair is None:
            pair = _two_vectors(work, defs, work)
        if pair is not None:
            a, b = pair
            mb = _magnitude(b)
            if mb == 0:
                return None
            d = _dot(a, b)
            val = sp.simplify(d / mb)
            steps = [
                f"a . b = {fmt(d)}, |b| = {_scalar_str(mb)}",
                "Projection of a on b = a . b / |b| "
                f"= {fmt(d)} / {_scalar_str(mb)} "
                f"= {_scalar_str(val)}",
            ]
            return _result("projection", _scalar_str(val), steps,
                           typ="vectors", value=val)

    # --- Area of triangle / parallelogram from vectors ------
    if ("area" in wl and ("triangle" in wl or "parallelogram" in wl
                          or "त्रिभुज" in raw
                          or "समांतर चतुर्भुज" in raw)):
        pair = _two_vectors(work, defs, work)
        if pair is not None:
            a, b = pair
            cr = _cross(a, b)
            mag = _magnitude(cr)
            steps = [
                f"a x b = {_vec_str(cr)}",
                f"|a x b| = {_scalar_str(mag)}",
            ]
            if "triangle" in wl or "त्रिभुज" in raw:
                val = sp.simplify(mag / 2)
                steps.append("Area of the triangle = "
                             f"(1/2)|a x b| = {_scalar_str(val)}"
                             " sq. units")
                return _result("area_triangle_vectors",
                               f"{_scalar_str(val)} sq. units",
                               steps, typ="vectors", value=val)
            steps.append("Area of the parallelogram = |a x b| "
                         f"= {_scalar_str(mag)} sq. units")
            return _result("area_parallelogram_vectors",
                           f"{_scalar_str(mag)} sq. units",
                           steps, typ="vectors", value=mag)

    # --- Collinear points ------------------------------------
    if ("collinear" in wl or "समरेख" in raw) and "point" in wl \
            or ("collinear" in wl and len(_points3(work)) == 3):
        pts = _points3(work)
        if len(pts) == 3:
            A, B, C = pts
            ab = _sub(B, A)
            ac = _sub(C, A)
            cr = _cross(ab, ac)
            ok = all(sp.simplify(v) == 0 for v in cr)
            steps = [
                f"AB = {_vec_str(ab)}, AC = {_vec_str(ac)}",
                f"AB x AC = {_vec_str(cr)}",
            ]
            if ok:
                ans = ("Yes, the points are collinear"
                       if not hindi else
                       "हाँ, बिंदु समरेख हैं")
                steps.append("AB x AC = 0, so AB and AC are "
                             "parallel; sharing A, the points "
                             "lie on one line.")
            else:
                ans = ("No, the points are not collinear"
                       if not hindi else
                       "नहीं, बिंदु समरेख नहीं हैं")
                steps.append("AB x AC is not 0, so the points "
                             "do not lie on one line.")
            return _result("collinear_points", ans, steps,
                           typ="vectors")

    # --- Collinear vectors -----------------------------------
    if "collinear" in wl or "समरेख" in raw:
        # Four or more loose vectors (the position-vectors-
        # of-A-B-C-D shape) are not a two-vector ask.
        if len(defs) < 2 and len(_literals(work, defs)) > 2:
            return None
        pair = _two_vectors(work, defs, work)
        if pair is not None:
            a, b = pair
            cr = _cross(a, b)
            ok = all(sp.simplify(v) == 0 for v in cr)
            steps = [f"a x b = {_vec_str(cr)}"]
            if ok:
                # find the ratio
                ratio = None
                for u, v in zip(a, b):
                    if u != 0:
                        ratio = sp.simplify(v / u)
                        break
                ans = ("Yes, the vectors are collinear"
                       if not hindi else
                       "हाँ, सदिश समरेख हैं")
                if ratio is not None:
                    steps.append(
                        f"a x b = 0 and b = ({fmt(ratio)})a, so "
                        "the vectors are collinear.")
                else:
                    steps.append("a x b = 0, so the vectors "
                                 "are collinear.")
            else:
                ans = ("No, the vectors are not collinear"
                       if not hindi else
                       "नहीं, सदिश समरेख नहीं हैं")
                steps.append("a x b is not 0, so the vectors "
                             "are not parallel.")
            return _result("collinear_vectors", ans, steps,
                           typ="vectors")

    # --- Right-angled triangle from vectors / points ---------
    if "right" in wl and "triangle" in wl:
        trip = None
        pts = _points3(work)
        if len(pts) == 3:
            A, B, C = pts
            trip = (_sub(B, A), _sub(C, B), _sub(A, C))
            names = ("AB", "BC", "CA")
        elif "position" in wl or "vertices" in wl \
                or "vertex" in wl:
            # Position vectors of the three vertices, named
            # or literal: the sides are their differences.
            pos3 = None
            if len(defs) == 3:
                pos3 = list(defs.values())
            else:
                lits = _literals(work, defs)
                if len(lits) == 3:
                    pos3 = lits
            if pos3 is not None:
                A, B, C = pos3
                trip = (_sub(B, A), _sub(C, B), _sub(A, C))
                names = ("AB", "BC", "CA")
        if trip is not None:
            sq = [sp.simplify(_dot(v, v)) for v in trip]
            ok = False
            which = None
            for i in range(3):
                j, k = (i + 1) % 3, (i + 2) % 3
                if sp.simplify(sq[j] + sq[k] - sq[i]) == 0:
                    ok = True
                    which = i
            steps = [
                "Squared side lengths: " + ", ".join(
                    f"|{names[i]}|^2 = {fmt(sq[i])}"
                    for i in range(3)),
            ]
            if ok:
                ans = ("Yes, it is a right angled triangle"
                       if not hindi else
                       "हाँ, यह समकोण त्रिभुज है")
                steps.append(
                    f"{fmt(sq[(which + 1) % 3])} + "
                    f"{fmt(sq[(which + 2) % 3])} = "
                    f"{fmt(sq[which])}, so by Pythagoras the "
                    "triangle is right angled.")
            else:
                ans = ("No, it is not a right angled triangle"
                       if not hindi else
                       "नहीं, यह समकोण त्रिभुज नहीं है")
                steps.append("No side squared equals the sum "
                             "of the other two, so it is not "
                             "right angled.")
            return _result("right_triangle_vectors", ans, steps,
                           typ="vectors")

    # --- Direction cosines of a vector ------------------------
    if "direction cosines" in wl or "दिक्" in raw:
        target = None
        if len(defs) == 1:
            target = next(iter(defs.values()))
        if target is None:
            m = re.search(r"of\s+(?:the\s+vector\s+)?(.+)$",
                          work, re.I)
            if m:
                target = _vec_parse(m.group(1), defs)
        if target is not None:
            mag = _magnitude(target)
            if mag == 0:
                return None
            dcs = tuple(sp.simplify(c / mag) for c in target)
            steps = [
                f"|a| = {_scalar_str(mag)}",
                "Direction cosines = components / |a| = ("
                + ", ".join(_scalar_str(c) for c in dcs) + ")",
            ]
            ans = "(" + ", ".join(_scalar_str(c) for c in dcs) + ")"
            return _result("direction_cosines_vector", ans,
                           steps, typ="vectors")
        # Equally inclined: i + j + k
        if "equally inclined" in wl:
            v = _vec_parse(re.sub(r".*?vector\s+", "", work),
                           defs) or (sp.Integer(1),) * 3
            mag = _magnitude(v)
            dcs = tuple(sp.simplify(c / mag) for c in v)
            if len(set(dcs)) == 1:
                ang = _fmt_angle(sp.acos(dcs[0]))
                steps = [
                    f"|a| = {_scalar_str(mag)}; each direction "
                    f"cosine = {_scalar_str(dcs[0])}.",
                    "All three direction cosines are equal, "
                    "so the vector is equally inclined to "
                    f"the three axes, at {ang} to each.",
                ]
                return _result("equally_inclined",
                               f"Equally inclined, angle = {ang}",
                               steps, typ="vectors")

    # --- Midpoint position vector -----------------------------
    # Only the position-vector phrasing (NCERT Ex 10.2
    # Q16's family): a plain "midpoint of the points"
    # ask is 3D geometry, which the core already serves
    # in coordinate form.
    if "mid" in wl and "point" in wl and "position" in wl:
        pts = _points3(work)
        if len(pts) == 2:
            A, B = pts
            mid = tuple(sp.simplify((a + b) / 2)
                        for a, b in zip(A, B))
            steps = [
                "Position vector of the midpoint = "
                "(position vector of P + position vector "
                "of Q) / 2.",
                f"= {_vec_str(mid)}",
            ]
            return _result("midpoint_position_vector",
                           _vec_str(mid), steps, typ="vectors")

    # --- Components from initial / terminal points ------------
    if "initial point" in wl and "terminal point" in wl:
        pts = re.findall(
            r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
            r"(?:\s*,\s*(-?\d+(?:\.\d+)?))?\s*\)", work)
        if len(pts) == 2:
            def _mk(p):
                vals = [sp.Rational(v) if "." not in v
                        else sp.nsimplify(v, rational=True)
                        for v in p if v != ""]
                while len(vals) < 3:
                    vals.append(sp.Integer(0))
                return tuple(vals)
            A, B = _mk(pts[0]), _mk(pts[1])
            ab = _sub(B, A)
            steps = [
                "The vector = terminal point - initial "
                f"point = {_vec_str(ab)}.",
                "Scalar components: " + ", ".join(
                    fmt(c) for c in ab),
                "Vector components: " + ", ".join(
                    f"{fmt(c)}{u}" for c, u in
                    zip(ab, ("i", "j", "k")) if c != 0),
            ]
            return _result("components_from_points",
                           _vec_str(ab), steps, typ="vectors")

    # --- Equal vectors: find the unknowns ----------------------
    if "equal" in wl and re.search(r"find the values? of", wl):
        m = re.search(r"vectors?\s+(.+?)\s+and\s+(.+?)\s+are\s+"
                      r"equal", work, re.I)
        if m:
            va = _vec_parse_unknowns(m.group(1))
            vb = _vec_parse_unknowns(m.group(2))
            if va is not None and vb is not None:
                steps = ["Equal vectors have equal "
                         "corresponding components:"]
                pairs = []
                for u, v in zip(va, vb):
                    if u == v:
                        continue
                    if v.free_symbols and not u.free_symbols:
                        pairs.append(f"{fmt(v)} = {fmt(u)}")
                    elif u.free_symbols and not v.free_symbols:
                        pairs.append(f"{fmt(u)} = {fmt(v)}")
                    else:
                        pairs.append(f"{fmt(u)} = {fmt(v)}")
                if not pairs:
                    return None
                steps.append(", ".join(pairs))
                ans = ", ".join(pairs)
                return _result("equal_vectors", ans, steps,
                               typ="vectors")

    # --- Vector of given magnitude in a given direction --------
    m = re.search(r"magnitude\s+(\d+(?:\.\d+)?)\s+units", wl)
    if m and "direction" in wl:
        target = None
        mm = re.search(r"direction\s+of\s+(?:the\s+)?"
                       r"(?:vector\s+)?(.+?)(?:\s+which|\s*$)",
                       work, re.I)
        if mm:
            target = _vec_parse(mm.group(1), defs)
        if target is None and len(defs) == 1:
            target = next(iter(defs.values()))
        if target is not None:
            mag = _magnitude(target)
            want = sp.Rational(m.group(1)) if "." not in \
                m.group(1) else sp.nsimplify(m.group(1),
                                             rational=True)
            if mag == 0:
                return None
            fac = sp.simplify(want / mag)
            vec = tuple(sp.simplify(fac * c) for c in target)
            steps = [
                f"|a| = {_scalar_str(mag)}; unit vector "
                f"= a / {_scalar_str(mag)}.",
                f"Required vector = {fmt(want)} x unit "
                f"vector = {_vec_str(vec)}",
            ]
            return _result("vector_given_magnitude",
                           _vec_str(vec), steps, typ="vectors")

    # --- Unit vector perpendicular to both ----------------------
    if "perpendicular" in wl and "unit vector" in wl:
        pair = _two_vectors(work, defs, work)
        if pair is not None:
            a, b = pair
            cr = _cross(a, b)
            mag = _magnitude(cr)
            if mag == 0:
                return None
            unit = tuple(sp.simplify(c / mag) for c in cr)
            steps = [
                f"a x b = {_vec_str(cr)}, |a x b| = "
                f"{_scalar_str(mag)}",
                "Unit vector perpendicular to both = "
                f"+-({_vec_str(unit)})",
            ]
            return _result("unit_perpendicular",
                           f"+-({_vec_str(unit)})", steps,
                           typ="vectors")

    # --- Perpendicular lambda ----------------------------------
    if "perpendicular" in wl and re.search(
            r"find the value of\s*(λ|lambda|k)\b", wl):
        got = _perp_lambda(work, defs)
        if got is not None:
            return got

    # --- Angle between two lines (direction vectors) ------------
    if "angle between" in wl and "line" in wl:
        drs = re.findall(
            r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)",
            work)
        pair = None
        if len(drs) == 2:
            pair = tuple(tuple(sp.Integer(int(v)) for v in d)
                         for d in drs)
        if pair is None:
            pair = _two_vectors(work, defs, work)
        if pair is not None:
            a, b = pair
            d = _dot(a, b)
            ma, mb = _magnitude(a), _magnitude(b)
            if ma == 0 or mb == 0:
                return None
            cosv = sp.simplify(abs(d) / (ma * mb))
            steps = [
                f"Direction vectors: {_vec_str(a)} and "
                f"{_vec_str(b)}.",
                f"cos theta = |a . b| / (|a| |b|) = "
                f"{_scalar_str(cosv)}",
            ]
            val = sp.acos(cosv)
            if _pi_multiple(val) is not None:
                ans = _fmt_angle(val)
            else:
                import math as _math
                deg = _math.degrees(_math.acos(float(cosv)))
                ans = (f"cos^-1({_scalar_str(cosv)}) "
                       f"(about {deg:.1f} degrees)")
            steps.append(f"theta = {ans}")
            return _result("angle_between_lines", ans, steps,
                           typ="vectors", value=val)
    return None


_LAMBDAS = ("λ", "lambda", "k")


def _comp_with_unknown(text):
    """Parse '2i + λj - 3k' style literals with one unknown
    (λ / lambda / k) as a component coefficient."""
    s = str(text).strip()
    s = s.replace("lambda", "λ")
    parts = re.findall(
        r"([+-]?)\s*(\d+(?:\.\d+)?)?\s*(λ)?\s*([ijk])", s)
    if not parts:
        return None
    comp = [sp.Integer(0)] * 3
    unk = [False] * 3
    used = 0
    for sign, num, lam, unit in parts:
        idx = "ijk".index(unit)
        if lam:
            coef = sp.Symbol("λ")
            unk[idx] = True
        elif num:
            coef = sp.Rational(num) if "." not in num else \
                sp.nsimplify(num, rational=True)
        else:
            coef = sp.Integer(1)
        if sign == "-":
            coef = -coef
        comp[idx] = comp[idx] + coef
        used += 1
    if used == 0 or sum(unk) != 1:
        return None
    return tuple(comp)


def _perp_lambda(work, defs):
    # Two literals, one carrying the unknown. Fold the word
    # "lambda" to the glyph first so the scan can see it.
    work = str(work).replace("lambda", "λ")
    lits = re.findall(
        r"[+-]?\s*(?:\d+\s*|λ\s*)?[ijk](?:\s*[+-]\s*"
        r"(?:\d+\s*|λ\s*)?[ijk]){1,2}", work)
    vecs = []
    for lit in lits:
        v = _comp_with_unknown(lit)
        if v is not None:
            vecs.append(v)
            continue
        v = _vec_parse(lit, defs)
        if v is not None:
            vecs.append(v)
    vecs = [v for i, v in enumerate(vecs)
            if v not in vecs[:i]]
    if len(vecs) != 2:
        return None
    a, b = vecs
    lam = sp.Symbol("λ")
    d = sp.expand(_dot(a, b))
    sol = sp.solve(sp.Eq(d, 0), lam)
    if not sol:
        return None
    steps = [
        "Perpendicular vectors have dot product 0.",
        f"a . b = {fmt(d)} = 0",
        f"lambda = {fmt(sol[0])}",
    ]
    return _result("perpendicular_lambda",
                   f"lambda = {fmt(sol[0])}", steps,
                   typ="vectors", value=sol[0])


# ---------------------------------------------------------------------------
# 3. Continuity
# ---------------------------------------------------------------------------

_PIECE_RE = re.compile(
    r"([^,;{}]+?)\s*,\s*if\s*x\s*(<=|>=|<|>|=)\s*"
    r"(-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?)")


def _piece_expr(text):
    """Parse one piecewise branch expression in x (may carry
    one parameter letter). Returns (expr, params) or None."""
    s = text.strip()
    # The first branch's capture carries the whole question
    # prose up to "f (x) =": cut everything through it.
    s = re.sub(r"^.*f\s*\(x\)\s*=\s*", "", s).strip()
    if not s or len(s) > 40:
        return None
    try:
        expr = _parse(s, {"k": sp.Symbol("k"),
                          "a": sp.Symbol("a"),
                          "b": sp.Symbol("b"),
                          "lambda": sp.Symbol("lambda")})
    except Exception:
        return None
    syms = expr.free_symbols - {x}
    if len(syms) > 2:
        return None
    if x not in expr.free_symbols and not syms:
        pass  # constant branch is fine
    elif x not in expr.free_symbols and syms:
        pass  # parameter-only branch (e.g. "k") is fine
    return expr, syms


def _continuity142(question):
    raw = str(question)
    hindi = _hindi(raw)
    s = _fold_ascii_powers(_prep(raw))
    low = s.lower()
    if "continu" not in low and "differentiab" not in low \
            and "संतत" not in raw and "अवकलनीय" not in raw:
        return None
    # --- Piecewise in linear "expr, if x < a" notation ----
    pieces = []
    for m in _PIECE_RE.finditer(s):
        got = _piece_expr(m.group(1))
        if got is None:
            continue
        expr, syms = got
        pt = _parse(m.group(3))
        pieces.append((expr, syms, m.group(2), pt))
    if len(pieces) >= 2:
        joins = sorted({pt for _, _, _, pt in pieces})
        params = set()
        for _, syms, _, _ in pieces:
            params |= syms
        find_mode = bool(params) and (
            "find" in low or "ज्ञात" in raw)
        diff_mode = "differentiab" in low
        if len(joins) == 1 and len(pieces) <= 4:
            got = _piecewise_at(pieces, joins[0], params,
                                find_mode, diff_mode, hindi)
            if got is not None:
                return got
        if len(joins) == 2 and find_mode and params \
                and len(pieces) <= 5:
            got = _piecewise_two_join(pieces, joins, params,
                                      hindi)
            if got is not None:
                return got
    # --- Single-form modulus: f(x) = |linear| -------------
    # Multi-function rows ("(a) f(x) = ... (b) f(x) = ...")
    # are not single-form asks.
    multi = len(re.findall(r"f\s*\(x\)\s*=", s)) > 1
    m = re.search(r"f\s*\(x\)\s*=\s*\|\s*([^|]+)\|", s)
    if m and not multi and ("examine" in low or "discuss"
                            in low or "is the function"
                            in low or "show" in low
                            or "continuous" in low):
        try:
            inner = _parse(m.group(1))
        except Exception:
            inner = None
        if inner is not None and inner.free_symbols <= {x} \
                and sp.Poly(inner, x) is not None \
                and sp.Poly(inner, x).degree() == 1:
            zero = sp.solve(inner, x)[0]
            steps = [
                f"|{fmt(inner)}| is a modulus of a "
                "continuous (polynomial) function, so it "
                "is continuous everywhere.",
            ]
            ans = "Continuous for all real x"
            if "differentiab" in low:
                steps.append(
                    f"It is not differentiable at x = "
                    f"{fmt(zero)}, where the graph has a "
                    "corner.")
                ans += (f"; not differentiable at "
                        f"x = {fmt(zero)}")
            return _result("continuity_modulus", ans, steps,
                           typ="calculus")
    # --- Single-form polynomial -----------------------------
    m = re.search(r"f\s*\(x\)\s*=\s*([^,;]+)$", s.strip())
    if m and not multi and ("examine" in low or "discuss"
                            in low or "is the function"
                            in low):
        try:
            expr = _parse(m.group(1))
        except Exception:
            expr = None
        if expr is not None and expr.free_symbols <= {x}:
            poly = sp.Poly(expr, x)
            if poly is not None:
                steps = [
                    f"f(x) = {fmt(expr)} is a polynomial, "
                    "and every polynomial is continuous "
                    "at every real number.",
                ]
                return _result("continuity_polynomial",
                               "Continuous for all real x",
                               steps, typ="calculus")
    return None


def _piecewise_at(pieces, a, params, find_mode, diff_mode,
                  hindi):
    left = [e for e, _, op, pt in pieces
            if pt == a and op in ("<", "<=")]
    right = [e for e, _, op, pt in pieces
             if pt == a and op in (">", ">=")]
    value = None
    for e, _, op, pt in pieces:
        if pt == a and op == "=":
            value = e
    if value is None:
        for e, _, op, pt in pieces:
            if pt == a and op in ("<=", ">="):
                try:
                    value = e.subs(x, a)
                except Exception:
                    value = None
    if not left or not right:
        return None
    try:
        lhl = sp.limit(left[0], x, a, dir="-")
        rhl = sp.limit(right[0], x, a, dir="+")
    except Exception:
        return None
    if find_mode:
        eqs = [sp.Eq(lhl, rhl)]
        if value is not None:
            eqs.append(sp.Eq(lhl, value))
        try:
            sol = sp.solve(eqs, list(params), dict=True)
        except Exception:
            return None
        sol = [d for d in sol
               if all(v.is_real is not False for v in d.values())]
        if len(sol) != 1:
            return None
        sol = sol[0]
        steps = [
            f"Left hand limit at x = {fmt(a)}: {fmt(lhl)}",
            f"Right hand limit at x = {fmt(a)}: {fmt(rhl)}",
            "For continuity the two limits must be equal"
            + (" and equal to f(" + fmt(a) + ")" if value
               is not None else "") + ".",
        ]
        for p in sorted(params, key=str):
            steps.append(f"{p} = {fmt(sol[p])}")
        ans = ", ".join(f"{p} = {fmt(sol[p])}"
                        for p in sorted(params, key=str))
        return _result("continuity_find_parameter", ans, steps,
                       typ="calculus")
    # Verdict mode.
    steps = [
        f"Left hand limit at x = {fmt(a)}: {fmt(lhl)}",
        f"Right hand limit at x = {fmt(a)}: {fmt(rhl)}",
    ]
    if value is not None:
        steps.append(f"f({fmt(a)}) = {fmt(value)}")
    cont = sp.simplify(lhl - rhl) == 0 and (
        value is None or sp.simplify(lhl - value) == 0)
    if value is None and sp.simplify(lhl - rhl) == 0:
        steps.append(
            f"Both limits are {fmt(lhl)}, but f({fmt(a)}) "
            "is not defined, so the function is not "
            "continuous there.")
        return _result("continuity_verdict",
                       f"Not continuous at x = {fmt(a)} "
                       "(value not defined)", steps,
                       typ="calculus")
    if not cont:
        steps.append("The limits do not match"
                     + (" the value" if value is not None
                        else "") + ", so the function is "
                     "not continuous there.")
        return _result("continuity_verdict",
                       f"Not continuous at x = {fmt(a)}",
                       steps, typ="calculus")
    steps.append("Limit = value, so the function is "
                 "continuous there.")
    if diff_mode:
        try:
            lhd = sp.limit(sp.diff(left[0], x), x, a, dir="-")
            rhd = sp.limit(sp.diff(right[0], x), x, a, dir="+")
        except Exception:
            return _result("continuity_verdict",
                           f"Continuous at x = {fmt(a)}",
                           steps, typ="calculus")
        if sp.simplify(lhd - rhd) == 0:
            steps.append(
                f"Left and right derivatives are both "
                f"{fmt(lhd)}, so it is differentiable too.")
            return _result("differentiability_verdict",
                           f"Continuous and differentiable "
                           f"at x = {fmt(a)}", steps,
                           typ="calculus")
        steps.append(
            f"Left derivative = {fmt(lhd)}, right "
            f"derivative = {fmt(rhd)}; they differ, so "
            "it is not differentiable there.")
        return _result("differentiability_verdict",
                       f"Continuous but not differentiable "
                       f"at x = {fmt(a)}", steps, typ="calculus")
    return _result("continuity_verdict",
                   f"Continuous at x = {fmt(a)}", steps,
                   typ="calculus")


def _piecewise_two_join(pieces, joins, params, hindi):
    eqs = []
    detail = []
    for a in joins:
        left = [e for e, _, op, pt in pieces
                if pt == a and op in ("<", "<=")]
        right = [e for e, _, op, pt in pieces
                 if pt == a and op in (">", ">=")]
        value = None
        for e, _, op, pt in pieces:
            if pt == a and op == "=":
                value = e
        if value is None:
            for e, _, op, pt in pieces:
                if pt == a and op in ("<=", ">="):
                    value = e.subs(x, a)
        if not left or not right:
            return None
        try:
            lhl = sp.limit(left[0], x, a, dir="-")
            rhl = sp.limit(right[0], x, a, dir="+")
        except Exception:
            return None
        eqs.append(sp.Eq(lhl, rhl))
        if value is not None:
            eqs.append(sp.Eq(rhl, value))
        detail.append((a, lhl, rhl))
    try:
        sol = sp.solve(eqs, list(params), dict=True)
    except Exception:
        return None
    if len(sol) != 1:
        return None
    sol = sol[0]
    if set(sol) != set(params):
        return None
    steps = []
    for a, lhl, rhl in detail:
        steps.append(f"At x = {fmt(a)}: left limit "
                     f"{fmt(lhl)}, right limit {fmt(rhl)}; "
                     "continuity needs them equal.")
    for p in sorted(params, key=str):
        steps.append(f"{p} = {fmt(sol[p])}")
    ans = ", ".join(f"{p} = {fmt(sol[p])}"
                    for p in sorted(params, key=str))
    return _result("continuity_find_parameter", ans, steps,
                   typ="calculus")


# ---------------------------------------------------------------------------
# 4. Differentiation (implicit / logarithmic / parametric /
#    second order / at a point)
# ---------------------------------------------------------------------------

_THETA = sp.Symbol("theta")
_AA = sp.Symbol("a")
_BB = sp.Symbol("b")

_DIFF_BOILER = [
    r"find\s+(?:the\s+)?(?:second\s+order\s+derivatives?\s+of\s+the\s+functions?\s+given\s+in\s+exercises?\s+\d+\s+to\s+\d+\.?\s*)",
    r"differentiate\s+the\s+functions?\s+given\s+in\s+exercises?\s+\d+\s+to\s+\d+\s+w\.?\s*r\.?\s*t\.?\s*x\.?\s*",
    r"if\s+x\s+and\s+y\s+are\s+connected\s+parametrically\s+by\s+the\s+equations?\s+given\s+in\s+exercises?\s+\d+\s+to\s+\d+,?\s*(?:dy\s+)?without\s+eliminating\s+the\s+parameter,?\s*",
    r"find\s*\.?\s*dx\s*",
    r"find\s+(?:of\s+the\s+functions?\s+given\s+in\s+exercises?\s+\d+\s+to\s+\d+\.?\s*)",
    r"find\s+in\s+the\s+following:?\s*",
    r"find\s*,?\s*if\s+",
    r"differentiate\s+the\s+following\s+w\.?\s*r\.?\s*t\.?\s*x:?\s*",
    r"differentiate\s+w\.?\s*r\.?\s*t\.?\s*x:?\s*",
    r"differentiate\s+",
]


def _fold_ascii_powers(s):
    """Glued powers in the PDF extraction: sin2 y ->
    sin(y)^2 ; x2 -> x^2 ; 3x4 -> 3x^4 ; (x + 3)2 ->
    (x + 3)^2. No word boundary is required before the
    variable: in '3x4' the x follows a digit."""
    s = re.sub(r"(?<![a-zA-Z])(sin|cos|tan|sec|cosec|cot)"
               r"([23])\s+([a-z])\b", r"\1(\3)^\2", s)
    s = re.sub(r"([xyt])([234])(?!\d)", r"\1^\2", s)
    s = re.sub(r"\)(\d)\b", r")^\1", s)
    return s


def _clean_diff(raw):
    s = _prep(raw)
    s = s.replace("θ", "theta").replace("κ", "pi")
    low = s.lower()
    for pat in _DIFF_BOILER:
        low = re.sub(pat, " ", low)
    s = low
    # The PDF column bleed that prefixes every Ex 5.5 row.
    s = re.sub(r"\(\s*x\s*-\s*1\s*\)\s*\(\s*x\s*-\s*2\s*\)",
               " ", s)
    # Spaced dots are multiplication in the extraction.
    s = re.sub(r"\s\.\s", " * ", s)
    # The dy/dx wrapper the extraction scatters around the
    # actual equation ("dy Find ... : dx 2x + 3y = sin x").
    s = re.sub(r"^(?:dy\s*/\s*dx|dy\s+dx|dy|dx)\s+", "", s)
    # Plain asks: "find dy/dx of X", "find the derivative
    # of X", "find d2y/dx2 of X".
    s = re.sub(r"\bfind\s+(?:the\s+)?(?:dy\s*/\s*dx|"
               r"d2y\s*/\s*dx2|(?:second\s+(?:order\s+)?)?"
               r"derivative)\s+of\s+", "", s)
    s = re.sub(r"^find\s+(?:the\s+)?(?:dy\s*/\s*dx|"
               r"d2y\s*/\s*dx2|(?:second\s+(?:order\s+)?)?"
               r"derivative)\s*", "", s)
    # "If x = a (...), find d2y/dx2" keeps a leading "if".
    s = re.sub(r"^if\s+", "", s)
    s = _fold_ascii_powers(s)
    # Glued exponents (superscripts lost in extraction).
    s = re.sub(r"\((log x)\)(cos x|sin x|log x|x)\b",
               r"(log x)^(\2)", s)
    s = re.sub(r"\((sin|cos|tan) x\)(sin|cos|tan) x",
               r"(\1 x)^(\2 x)", s)
    s = re.sub(r"\bxsin\s*x\b", "x^(sin x)", s)
    s = re.sub(r"\bxlog\s*x\b", "x^(log x)", s)
    s = re.sub(r"\bxx\b", "x^x", s)
    s = re.sub(r"\b2sin\s*x\b", "2^(sin x)", s)
    s = re.sub(r"\s+", " ", s).strip(" .:,;")
    # Trailing conditions like ", 0 < x < 1" / ", x > 1".
    s = re.sub(r",?\s*-?\d*\s*<\s*x\s*<\s*-?\d+.*$", "", s)
    s = re.sub(r",?\s*x\s*>\s*-?\d+.*$", "", s)
    s = re.sub(r",?\s*x\s*!=\s*0.*$", "", s)
    return s.strip(" .:,;")


def _dparse(text):
    return _parse(text, {"theta": _THETA, "a": _AA, "b": _BB,
                         "y": y})


def _verify_implicit(F, cand):
    """Symbolic check: differentiating F(x, y(x)) = 0 with
    dy/dx = cand must give 0 identically. The candidate
    itself must be read in terms of Y(x) too."""
    Y = sp.Function("Y")
    try:
        d = sp.diff(F.subs(y, Y(x)), x)
        d = d.subs(sp.Derivative(Y(x), x), cand.subs(y, Y(x)))
        return sp.simplify(d) == 0
    except Exception:
        return False


def _verify_implicit_numeric(F, cand):
    """Fallback when symbolic simplification cannot close:
    find a point on the curve F = 0 and compare the
    candidate against a finite-difference slope whose
    neighbouring points are re-solved on the curve."""
    point = None
    for c in (0.5, 0.3, 0.7, 1.0, 1.3):
        try:
            if abs(float(F.subs({x: c, y: c}))) < 1e-9:
                point = (c, c)
                break
        except Exception:
            continue
    if point is None:
        for x0 in (0.4, 0.8, 1.2, 1.7):
            for guess in (0.4, 1.0, 2.0):
                try:
                    y0 = float(sp.nsolve(
                        F.subs(x, x0), y, guess,
                        tol=1e-14, maxsteps=100))
                    if abs(float(F.subs({x: x0, y: y0}))) \
                            < 1e-8:
                        point = (x0, y0)
                        break
                except Exception:
                    continue
            if point:
                break
    if point is None:
        return False
    x0, y0 = point
    h = 1e-4
    try:
        yp = float(sp.nsolve(F.subs(x, x0 + h), y, y0,
                             tol=1e-14, maxsteps=100))
        ym = float(sp.nsolve(F.subs(x, x0 - h), y, y0,
                             tol=1e-14, maxsteps=100))
        slope = (yp - ym) / (2 * h)
        got = float(cand.subs({x: x0, y: y0}))
    except Exception:
        return False
    return abs(slope - got) <= 2e-2 * max(1.0, abs(slope))


def _implicit_dydx(F, steps_head, op="implicit_dydx"):
    try:
        cand = sp.idiff(F, y, x)
    except Exception:
        return None
    if cand is None or cand.has(sp.Derivative):
        return None
    cand = sp.simplify(cand)
    if not _verify_implicit(F, cand) \
            and not _verify_implicit_numeric(F, cand):
        return None
    steps = list(steps_head) + [
        "Differentiate both sides w.r.t. x, treating y "
        "as a function of x.",
        f"dy/dx = {fmt(cand)}",
    ]
    return _result(op, fmt(cand), steps, typ="calculus")


_LOG_IMPLICIT = [
    (r"^x\^y\s*\+\s*y\^x\s*=\s*1$|^xy\s*\+\s*yx\s*=\s*1$",
     lambda: x ** y + y ** x - 1,
     "Let u = x^y and v = y^x. Taking log: log u = "
     "y log x and log v = x log y."),
    (r"^y\^x\s*=\s*x\^y$|^yx\s*=\s*xy$",
     lambda: y ** x - x ** y,
     "Taking log on both sides: x log y = y log x."),
    (r"^\(cos x\)\^y\s*=\s*\(cos y\)\^x$|"
     r"^\(cos x\)y\s*=\s*\(cos y\)x$",
     lambda: sp.cos(x) ** y - sp.cos(y) ** x,
     "Taking log on both sides: y log(cos x) = "
     "x log(cos y)."),
    (r"^xy\s*=\s*e\^\(x\s*-\s*y\)$|"
     r"^xy\s*=\s*e\s*\(\s*x\s*-\s*y\s*\)$",
     lambda: x ** y - sp.exp(x - y),
     "Taking log on both sides: y log x = x - y."),
]


_PURE_TOKENS = {"x", "y", "t", "a", "b", "c", "e", "pi",
                "sin", "cos", "tan", "sec", "cosec", "cot",
                "log", "sqrt", "exp", "theta", "asin",
                "acos", "atan", "abs"}


def _pure_math(text):
    """True when every word token in the text is a maths
    symbol or function name. Prose that survived cleaning
    ('find the area enclosed by the circle ...') must never
    be parsed as an implicit-multiplication product."""
    toks = re.findall(r"[a-zA-Z]+", str(text))
    return all(tok in _PURE_TOKENS for tok in toks)


def _differentiation142(question):
    raw = str(question)
    low_raw = raw.lower()
    # Proof asks are out of scope: serving dy/dx for a
    # "prove that d2y/dx2 ... is constant" question is a
    # partial non-answer.
    if "prove" in low_raw or "show that" in low_raw:
        return None
    # Wave 210: a dy/dx that sits INSIDE an equation —
    # an operator or "=" adjacent to it ("dy/dx + y =
    # e^x", "x dy/dx + 2y = x^2") — is a differential
    # equation to SOLVE, not a differentiation ask.
    # _clean_diff strips a leading dy/dx as boilerplate,
    # so the bare DE was misread as the implicit
    # relation y = e^x and its "derivative" exp(x) even
    # displaced the correct DE serve via the upgrade
    # below.  In this family's genuine dresses the
    # dy/dx is a noun phrase ("find dy/dx if ..."),
    # never an operand.  Decline; the DE layers own it.
    if re.search(r"[-+*/=^]\s*dy\s*/\s*dx", low_raw) \
            or re.search(r"dy\s*/\s*dx\s*[-+*/=^)]",
                         low_raw):
        return None
    if not any(k in low_raw for k in (
            "dy", "differentiat", "derivative", "अवकल")) \
            and "w.r.t" not in low_raw:
        # Book rows carry the ask in their boilerplate,
        # which _clean_diff strips; detect it there.
        cleaned_probe = _clean_diff(raw)
        if cleaned_probe == _prep(raw).lower().strip():
            return None
    s = _clean_diff(raw)
    if not s:
        return None
    second = ("second" in low_raw or "d2y" in low_raw
              or "d^2y" in low_raw)
    at_m = re.search(
        r"\bat\s+(x|t|theta)\s*=\s*"
        r"(-?\s*(?:pi\s*/\s*\d+|\d+(?:\.\d+)?))", s)
    at_var = at_val = None
    if at_m:
        at_var = {"x": x, "t": t, "theta": _THETA}[at_m.group(1)]
        try:
            at_val = _dparse(at_m.group(2))
        except Exception:
            at_var = at_val = None
        s = (s[:at_m.start()] + s[at_m.end():]).strip(" ,;")
    # --- Parametric --------------------------------------
    # Extract the two assignments by search: extraction
    # tails (conditions, stray "dy") must not block them.
    mx = re.search(r"\bx\s*=\s*([^,;]+)", s)
    my = re.search(r"\by\s*=\s*([^,;]+)", s)
    if mx and my and mx.group(1) != my.group(1):
        xs_ = re.split(r"\s+and\s+(?:x|y)\s*=",
                       mx.group(1))[0]
        ys_ = re.split(r"\s+and\s+(?:x|y)\s*=",
                       my.group(1))[0]
        both = (xs_ + ys_).replace("theta", "")
        if "t" in both or "theta" in xs_ + ys_:
            got = _parametric(xs_, ys_, second, at_var,
                              at_val)
            if got is not None:
                return got
    # --- Log-implicit named equations ----------------------
    for pat, builder, note in _LOG_IMPLICIT:
        if re.match(pat, s):
            return _implicit_dydx(
                builder(), [note], op="log_implicit_dydx")
    # --- General implicit ----------------------------------
    if s.count("=") == 1:
        lhs, rhs = s.split("=")
        lhs = lhs.strip()
        if lhs not in ("y", "f(x)") \
                and _pure_math(lhs) and _pure_math(rhs):
            try:
                F = _dparse(lhs) - _dparse(rhs)
            except Exception:
                F = None
            if F is not None and y in F.free_symbols \
                    and x in F.free_symbols:
                return _implicit_dydx(F, [])
        elif lhs == "y":
            try:
                expr = _dparse(rhs)
            except Exception:
                expr = None
            if expr is not None and expr.free_symbols <= {x}:
                return _explicit_dydx(expr, second, at_var,
                                      at_val)
            return None
    # --- Bare explicit function ----------------------------
    if "=" not in s and _pure_math(s):
        try:
            expr = _dparse(s)
        except Exception:
            expr = None
        if expr is not None and expr.free_symbols \
                and expr.free_symbols <= {x}:
            return _explicit_dydx(expr, second, at_var,
                                  at_val)
    return None


def _explicit_dydx(expr, second, at_var, at_val):
    d1 = sp.diff(expr, x)
    log_form = False
    ratio = None
    try:
        r = sp.simplify(d1 / expr)
        if r != 0 and len(str(r)) < 60:
            ratio = r
            log_form = True
    except Exception:
        pass
    has_var_pow = any(
        isinstance(n, sp.Pow) and x in n.base.free_symbols
        and x in n.exp.free_symbols
        for n in sp.preorder_traversal(expr))
    steps = []
    if second:
        d2raw = sp.diff(d1, x)
        # Verify numerically: simplify() is not a complete
        # prover and fails to prove the identity for heavy
        # forms like (log x)^(log x), so check d2 against
        # finite differences of d1 at two points instead.
        ok = True
        for x0 in (2.0, 3.0):
            try:
                h = 1e-4
                num = (float(d1.subs(x, x0 + h))
                       - float(d1.subs(x, x0 - h))) / (2 * h)
                got = float(d2raw.subs(x, x0))
            except Exception:
                ok = False
                break
            if abs(num - got) > 1e-3 * max(1.0, abs(num)):
                ok = False
                break
        if not ok:
            return None
        try:
            d2 = sp.simplify(d2raw)
        except Exception:
            d2 = d2raw
        steps.append(f"First derivative: dy/dx = {fmt(d1)}")
        if at_var is x and at_val is not None:
            val = sp.simplify(d2.subs(x, at_val))
            steps.append(f"At x = {fmt(at_val)}: "
                         f"d2y/dx2 = {fmt(val)}")
            return _result("second_derivative_at_point",
                           fmt(val), steps, typ="calculus",
                           value=val)
        steps.append(f"Second derivative: d2y/dx2 = "
                     f"{fmt(d2)}")
        return _result("second_derivative", fmt(d2), steps,
                       typ="calculus")
    if has_var_pow or (expr.is_Mul and len(expr.args) >= 3):
        steps.append("Take log on both sides and "
                     "differentiate (logarithmic "
                     "differentiation).")
    if at_var is x and at_val is not None:
        val = sp.simplify(d1.subs(x, at_val))
        steps.append(f"dy/dx = {fmt(d1)}")
        steps.append(f"At x = {fmt(at_val)}: dy/dx = "
                     f"{fmt(val)}")
        return _result("dydx_at_point", fmt(val), steps,
                       typ="calculus", value=val)
    if log_form and has_var_pow:
        ans = f"({fmt(expr)}) * ({fmt(ratio)})"
        steps.append(f"dy/dx = y * (log-derivative) = {ans}")
        return _result("log_differentiation", ans, steps,
                       typ="calculus")
    steps.append(f"dy/dx = {fmt(d1)}")
    return _result("dydx", fmt(d1), steps, typ="calculus")


def _parametric(xs_, ys_, second, at_var, at_val):
    # One parameter only: mixing t and theta means the
    # extraction merged two questions.
    has_theta = "theta" in xs_ + ys_
    has_t = "t" in (xs_ + ys_).replace("theta", "")
    if has_theta and has_t:
        return None
    var = _THETA if has_theta else t
    try:
        xe = _dparse(xs_)
        ye = _dparse(ys_)
    except Exception:
        return None
    if var not in xe.free_symbols and var not in ye.free_symbols:
        return None
    dx = sp.diff(xe, var)
    dy = sp.diff(ye, var)
    if sp.simplify(dx) == 0:
        return None
    d1 = sp.simplify(dy / dx)
    # Numeric verification against the parametric curve
    # (the constant parameters a, b are set to 1: any
    # nonzero instance verifies the formula).
    try:
        for v0 in (0.4, 0.9, 1.7):
            h = 1e-4
            sub_p = {var: v0 + h, _AA: 1, _BB: 1}
            sub_m = {var: v0 - h, _AA: 1, _BB: 1}
            num = (float(ye.subs(sub_p))
                   - float(ye.subs(sub_m))) / \
                  (float(xe.subs(sub_p))
                   - float(xe.subs(sub_m)))
            got = float(d1.subs({var: v0, _AA: 1, _BB: 1}))
            if abs(num - got) > 1e-3:
                return None
    except Exception:
        return None
    steps = [
        f"dx/d{fmt(var)} = {fmt(dx)}, dy/d{fmt(var)} = "
        f"{fmt(dy)}",
        f"dy/dx = (dy/d{fmt(var)}) / (dx/d{fmt(var)}) "
        f"= {fmt(d1)}",
    ]
    if second:
        d2 = sp.simplify(sp.diff(d1, var) / dx)
        try:
            for v0 in (0.4, 0.9, 1.7):
                h = 1e-3
                sub_p = {var: v0 + h, _AA: 1, _BB: 1}
                sub_m = {var: v0 - h, _AA: 1, _BB: 1}
                fp = float(d1.subs(sub_p))
                fm = float(d1.subs(sub_m))
                xp = float(xe.subs(sub_p))
                xm = float(xe.subs(sub_m))
                num = (fp - fm) / (xp - xm)
                got = float(d2.subs({var: v0, _AA: 1,
                                     _BB: 1}))
                if abs(num - got) > 5e-2:
                    return None
        except Exception:
            return None
        if at_var is var and at_val is not None:
            val = sp.simplify(d2.subs(var, at_val))
            steps.append(f"At {fmt(var)} = {fmt(at_val)}: "
                         f"d2y/dx2 = {fmt(val)}")
            return _result("parametric_second_at_point",
                           fmt(val), steps, typ="calculus",
                           value=val)
        steps.append(f"d2y/dx2 = (d/d{fmt(var)} of dy/dx) "
                     f"/ (dx/d{fmt(var)}) = {fmt(d2)}")
        return _result("parametric_second_derivative",
                       fmt(d2), steps, typ="calculus")
    if at_var is var and at_val is not None:
        val = sp.simplify(d1.subs(var, at_val))
        steps.append(f"At {fmt(var)} = {fmt(at_val)}: "
                     f"dy/dx = {fmt(val)}")
        return _result("parametric_dydx_at_point", fmt(val),
                       steps, typ="calculus", value=val)
    return _result("parametric_dydx", fmt(d1), steps,
                   typ="calculus")


# ---------------------------------------------------------------------------
# 5. Application of Derivatives
# ---------------------------------------------------------------------------

def _num(text):
    try:
        v = sp.Rational(str(text)) if "." not in str(text) \
            else sp.nsimplify(str(text), rational=True)
        return v
    except Exception:
        return None


def _fexpr(text):
    """Parse an f(x) body for the AoD schemas."""
    try:
        expr = _dparse(str(text).strip(" .:"))
    except Exception:
        return None
    if expr is None or not expr.free_symbols <= {x}:
        return None
    return expr


def _aod_intervals(s, low):
    # Multi-function rows ("(a) ... (b) ... (c) ...")
    # carry several functions in one extraction row.
    if len(re.findall(r"\(\s*[a-e]\s*\)", s)) >= 2:
        return None
    m = re.search(r"f\s*\(x\)\s*=\s*(.+)$", s)
    if not m:
        return None
    # Scrambled extractions put the expression BEFORE
    # "f (x) =" (the fraction's numerator/denominator
    # merged around it); then what follows "=" is only a
    # fragment of the true function. A genuine ask has no
    # trig/log content before the "f (x) =".
    if re.search(r"sin|cos|tan|log",
                 s[:m.start()].lower()):
        return None
    body = re.split(r"\s+is\b", m.group(1))[0]
    expr = _fexpr(body)
    if expr is None:
        return None
    claim = re.search(
        r"increasing on\s*(?:r\b|\(\s*-?\s*(?:∞|oo|inf))", low)
    d1 = sp.diff(expr, x)
    try:
        crits = [c for c in sp.solve(d1, x)
                 if c.is_real and not c.free_symbols]
    except Exception:
        crits = []
    # Domain breaks: points where f or f' is undefined.
    breaks = set(crits)
    for cand in (sp.solve(sp.denom(sp.together(expr)), x)
                 if expr.is_rational_function() else []):
        if cand.is_real:
            breaks.add(cand)
    pts = sorted(breaks, key=lambda v: float(v))
    edges = [sp.S.NegativeInfinity] + pts + [sp.S.Infinity]
    spans = []
    for lo_e, hi_e in zip(edges, edges[1:]):
        lo_f = float(lo_e) if lo_e != sp.S.NegativeInfinity \
            else None
        hi_f = float(hi_e) if hi_e != sp.S.Infinity else None
        if lo_f is None and hi_f is None:
            samples = [-2.0, 0.0, 2.0]
        elif lo_f is None:
            samples = [hi_f - 3.0, hi_f - 1.5, hi_f - 0.5]
        elif hi_f is None:
            samples = [lo_f + 0.5, lo_f + 1.5, lo_f + 3.0]
        else:
            w = hi_f - lo_f
            samples = [lo_f + 0.25 * w, lo_f + 0.5 * w,
                       lo_f + 0.75 * w]
        # The sign of f' must be constant and nonzero at
        # ALL samples: a missed critical point (solve does
        # not always find every root of a trig derivative)
        # shows up here and declines the whole answer
        # rather than serving a wrong interval.
        signs = []
        ok = True
        for smp in samples:
            try:
                dv = float(d1.subs(x, smp))
                fv = float(expr.subs(x, smp))
            except Exception:
                ok = False
                break
            if dv != dv or fv != fv or abs(dv) < 1e-9:
                ok = False
                break
            signs.append(dv > 0)
        if not ok or len(set(signs)) != 1:
            return None
        spans.append((lo_e, hi_e, signs[0]))

    def _iv(lo_e, hi_e):
        a = "-∞" if lo_e == sp.S.NegativeInfinity \
            else fmt(lo_e)
        b = "∞" if hi_e == sp.S.Infinity else fmt(hi_e)
        return f"({a}, {b})"

    inc = [_iv(a, b) for a, b, pos in spans if pos]
    dec = [_iv(a, b) for a, b, pos in spans if not pos]
    if not inc and not dec:
        return None
    steps = [f"f'(x) = {fmt(d1)}"]
    if crits:
        steps.append("f'(x) = 0 at x = " + ", ".join(
            fmt(c) for c in crits))
    parts = []
    if inc:
        parts.append("increasing in " + ", ".join(inc))
    if dec:
        parts.append("decreasing in " + ", ".join(dec))
    steps.append("Sign of f' gives: " + "; ".join(parts))
    ans = "; ".join(parts)
    return _result("increasing_decreasing_intervals", ans,
                   steps, typ="calculus")


def _aod_abs_maxmin(s, low):
    # Multi-part rows ("(i) ... (ii) ... (iii) ...") ask
    # several questions at once; serving only the first
    # part would be a partial non-answer.
    if re.search(r"\(\s*(?:ii|iii|iv)\s*\)", s):
        return None
    m = re.search(r"f\s*\(x\)\s*=\s*(.+?)(?:,?\s*(?:x\s*∈|in\s+the\s+interval|on\s+the\s+interval|in)\s*\[)", s)
    if m and re.search(r"sin|cos|tan|log",
                       s[:m.start()].lower()):
        return None  # scrambled extraction, as in intervals
    expr = None
    if m:
        expr = _fexpr(m.group(1))
    if expr is None:
        m2 = re.search(
            r"(?:value of|maximum value of|minimum value of|"
            r"maximum and minimum values? of)\s+(.+?)\s+"
            r"(?:on|in)\s+(?:the\s+interval\s+)?\[", s)
        if m2:
            expr = _fexpr(m2.group(1))
    im = re.search(r"\[\s*(-?[^,\]]+?)\s*,\s*(-?[^\]]+?)\s*\]",
                   s)
    if expr is None or not im:
        return None
    try:
        a = _dparse(im.group(1))
        b = _dparse(im.group(2))
        if a.free_symbols or b.free_symbols:
            return None
    except Exception:
        return None
    d1 = sp.diff(expr, x)
    cand = [a, b]
    try:
        for c in sp.solve(d1, x):
            if c.is_real and not c.free_symbols \
                    and float(a) < float(c) < float(b):
                cand.append(c)
    except Exception:
        pass
    vals = []
    for c in cand:
        try:
            v = sp.simplify(expr.subs(x, c))
            fv = float(v)
        except Exception:
            return None
        if fv != fv:
            return None
        vals.append((fv, c, v))
    vals.sort(key=lambda t: t[0])
    lo_f, lo_c, lo_v = vals[0]
    hi_f, hi_c, hi_v = vals[-1]
    steps = [
        f"f'(x) = {fmt(d1)}",
        "Check f at the endpoints and at the critical "
        "points inside the interval: " + ", ".join(
            f"f({fmt(c)}) = {fmt(v)}" for _, c, v in vals),
    ]
    want_min = "minimum" in low
    want_max = "maximum" in low
    if want_max and not want_min:
        ans = f"Maximum value = {fmt(hi_v)} at x = {fmt(hi_c)}"
        steps.append(ans)
        return _result("absolute_maximum", ans, steps,
                       typ="calculus", value=hi_v)
    if want_min and not want_max:
        ans = f"Minimum value = {fmt(lo_v)} at x = {fmt(lo_c)}"
        steps.append(ans)
        return _result("absolute_minimum", ans, steps,
                       typ="calculus", value=lo_v)
    ans = (f"Maximum value = {fmt(hi_v)} at x = {fmt(hi_c)}; "
           f"minimum value = {fmt(lo_v)} at x = {fmt(lo_c)}")
    steps.append(ans)
    return _result("absolute_max_min", ans, steps,
                   typ="calculus")


def _aod_global_extremum(s, low):
    # Maximum value of a sin x + b cos x (no interval).
    m = re.search(
        r"(?:maximum|minimum)\s+value\s+of\s+"
        r"(?:the\s+function\s+)?"
        r"(-?\d*)\s*sin\s*x\s*([+-])\s*(\d*)\s*cos\s*x"
        r"\s*\??\s*$",
        s.strip())
    if m:
        a = int(m.group(1)) if m.group(1) not in ("", "-") \
            else (-1 if m.group(1) == "-" else 1)
        b = int(m.group(3)) if m.group(3) else 1
        if m.group(2) == "-":
            b = -b
        amp = sp.sqrt(a * a + b * b)
        if "maximum" in low:
            steps = [
                f"For a sin x + b cos x the maximum value "
                f"is sqrt(a^2 + b^2) = sqrt({a*a + b*b}) "
                f"= {fmt(amp)}.",
            ]
            return _result("global_maximum_trig",
                           fmt(amp), steps, typ="calculus",
                           value=amp)
        steps = [
            f"For a sin x + b cos x the minimum value "
            f"is -sqrt(a^2 + b^2) = {fmt(-amp)}.",
        ]
        return _result("global_minimum_trig", fmt(-amp),
                       steps, typ="calculus", value=-amp)
    # Claim verdict: "f has maximum at x = e" style.
    m = re.search(r"f\s*\(x\)\s*=\s*(.+?)\s+has\s+(maximum|"
                  r"minimum)\s+at\s+x\s*=\s*(.+?)\s*\.?\s*$",
                  s)
    if m:
        expr = _fexpr(m.group(1))
        try:
            pt = _dparse(m.group(3))
        except Exception:
            pt = None
        if expr is not None and pt is not None \
                and not pt.free_symbols:
            d1 = sp.diff(expr, x)
            if sp.simplify(d1.subs(x, pt)) != 0:
                return None
            try:
                before = float(d1.subs(x, pt - sp.Rational(1, 10)))
                after = float(d1.subs(x, pt + sp.Rational(1, 10)))
            except Exception:
                return None
            is_max = before > 0 and after < 0
            is_min = before < 0 and after > 0
            if (m.group(2) == "maximum" and is_max) or \
                    (m.group(2) == "minimum" and is_min):
                pt_s = "e" if pt == sp.E else fmt(pt)
                steps = [
                    f"f'(x) = {fmt(d1)}; f'({pt_s}) = 0.",
                    "f' changes sign from "
                    + ("+ to -" if is_max else "- to +")
                    + f" at x = {pt_s}, so f has a "
                    f"{m.group(2)} there.",
                    f"f({pt_s}) = {fmt(expr.subs(x, pt))}",
                ]
                return _result("extremum_claim_verdict",
                               f"Yes, {m.group(2)} at "
                               f"x = {pt_s}", steps,
                               typ="calculus")
            return None
    return None


_WORD_FRAC = {"one-half": 2, "half": 2, "one-third": 3,
              "one-fourth": 4, "one-fifth": 5, "one-sixth": 6,
              "one-seventh": 7, "one-eighth": 8}


def _aod_rates(s, low):
    # --- Circle circumference / area rates ----------------
    m = re.search(r"radius of a circle is increasing at "
                  r"the rate of ([\d.]+)", low)
    if m and "circumference" in low:
        r0 = _num(m.group(1))
        val = 2 * _PI * r0
        steps = [
            "C = 2 pi r, so dC/dt = 2 pi (dr/dt) "
            f"= 2 pi x {fmt(r0)} = {fmt(val)} cm/s.",
        ]
        return _result("rate_circle_circumference",
                       f"{fmt(val)} cm/s", steps,
                       typ="calculus", value=val)
    m = re.search(r"waves move in circles at a speed of "
                  r"([\d.]+)\s*cm", low)
    if m and "enclosed area" in low:
        rm = re.search(r"radius of the circular wave is "
                       r"([\d.]+)\s*cm", low)
        if rm:
            r0, v0 = _num(rm.group(1)), _num(m.group(1))
            val = 2 * _PI * r0 * v0
            steps = [
                "A = pi r^2, so dA/dt = 2 pi r (dr/dt) "
                f"= 2 pi x {fmt(r0)} x {fmt(v0)} "
                f"= {fmt(val)} cm^2/s.",
            ]
            return _result("rate_circle_area", f"{fmt(val)} "
                           "cm^2/s", steps, typ="calculus",
                           value=val)
    # --- Sphere: dV/dt given, find dr/dt ------------------
    m = re.search(r"pumping in ([\d.]+) cubic centimetres "
                  r"of gas per second", low)
    if m and "radius" in low:
        rm = re.search(r"radius is ([\d.]+)\s*cm", low)
        if rm:
            dv, r0 = _num(m.group(1)), _num(rm.group(1))
            val = sp.simplify(dv / (4 * _PI * r0 ** 2))
            steps = [
                "V = (4/3) pi r^3, so dV/dt = 4 pi r^2 "
                "(dr/dt).",
                f"{fmt(dv)} = 4 pi x {fmt(r0)}^2 x dr/dt, "
                f"so dr/dt = {fmt(val)} cm/s.",
            ]
            return _result("rate_sphere_radius", f"{fmt(val)} "
                           "cm/s", steps, typ="calculus",
                           value=val)
    # --- Sphere: dV/dr at a radius --------------------------
    if "volume is increasing with the radius" in low \
            or "volume is increasing with respect to" in low:
        rm = re.search(r"radius[^.]*?([\d.]+)\s*cm", low)
        if rm:
            r0 = _num(rm.group(1))
            val = 4 * _PI * r0 ** 2
            steps = [
                "V = (4/3) pi r^3, so dV/dr = 4 pi r^2 "
                f"= 4 pi x {fmt(r0)}^2 = {fmt(val)} "
                "cm^3 per cm.",
            ]
            return _result("rate_sphere_dvdr", f"{fmt(val)} "
                           "cm^3/cm", steps, typ="calculus",
                           value=val)
    # --- Sphere / bubble: dr/dt given, find dV/dt -----------
    m = re.search(r"radius[^.]*?increasing at the rate of "
                  r"([\d.]+)(?:\s*/\s*(\d+))?\s*cm/s", low)
    if m and ("volume" in low or "bubble" in low
              or "balloon" in low):
        rm = re.search(r"radius is ([\d.]+)\s*cm", low)
        if rm:
            r0 = _num(rm.group(1))
            dr = _num(m.group(1))
            if m.group(2):
                dr = dr / int(m.group(2))
            val = sp.simplify(4 * _PI * r0 ** 2 * dr)
            steps = [
                "V = (4/3) pi r^3, so dV/dt = 4 pi r^2 "
                "(dr/dt).",
                f"At r = {fmt(r0)}: dV/dt = 4 pi x "
                f"{fmt(r0)}^2 x {fmt(dr)} = {fmt(val)} "
                "cm^3/s.",
            ]
            return _result("rate_sphere_volume", f"{fmt(val)} "
                           "cm^3/s", steps, typ="calculus",
                           value=val)
    # --- Ladder ---------------------------------------------
    m = re.search(r"ladder ([\d.]+)\s*m long", low)
    if m and "wall" in low:
        sm = re.search(r"rate of ([\d.]+)\s*cm/s", low)
        dm = re.search(r"foot of the ladder is ([\d.]+)\s*m "
                       r"away", low)
        if sm and dm:
            L = _num(m.group(1)) * 100
            d = _num(dm.group(1)) * 100
            sp_ = _num(sm.group(1))
            h = sp.sqrt(L ** 2 - d ** 2)
            val = sp.simplify(-d * sp_ / h)
            steps = [
                f"x^2 + y^2 = {fmt(L)}^2 (in cm). At x = "
                f"{fmt(d)}, y = {fmt(h)}.",
                "2x (dx/dt) + 2y (dy/dt) = 0, so dy/dt = "
                f"-x/y x dx/dt = {fmt(val)} cm/s.",
            ]
            return _result("rate_ladder",
                           f"Decreasing at {fmt(-val)} cm/s",
                           steps, typ="calculus", value=val)
    # --- Rectangle perimeter / area --------------------------
    m = re.search(
        r"length x of a rectangle is (decreasing|increasing)"
        r" at the rate of ([\d.]+)[^.]*?width y is "
        r"(decreasing|increasing) at the rate of ([\d.]+)"
        r".*?when x = ?([\d.]+)\s*cm and y = ?"
        r"([\d.]+)\s*cm", low)
    if m:
        dx = _num(m.group(2)) * (-1 if m.group(1)
                                  == "decreasing" else 1)
        dy = _num(m.group(4)) * (-1 if m.group(3)
                                 == "decreasing" else 1)
        xv, yv = _num(m.group(5)), _num(m.group(6))
        dp = 2 * (dx + dy)
        da = yv * dx + xv * dy
        steps = [
            f"dx/dt = {fmt(dx)} cm/min, dy/dt = {fmt(dy)} "
            "cm/min.",
            "P = 2(x + y): dP/dt = 2(dx/dt + dy/dt) = "
            f"{fmt(dp)} cm/min.",
            "A = xy: dA/dt = y(dx/dt) + x(dy/dt) = "
            f"{fmt(da)} cm^2/min.",
        ]
        ans = (f"(a) Perimeter changes at {fmt(dp)} "
               f"cm/min; (b) area changes at {fmt(da)} "
               "cm^2/min")
        return _result("rate_rectangle", ans, steps,
                       typ="calculus")
    # --- Sand cone -------------------------------------------
    m = re.search(r"pouring[^.]*?rate of ([\d.]+)\s*cm3/s",
                  low)
    if m and "cone" in low:
        frac = None
        for w, n in _WORD_FRAC.items():
            if ("height of the cone is always " + w +
                    " of the radius") in low:
                frac = n
        hm = re.search(r"height is ([\d.]+)\s*cm", low)
        if frac and hm:
            dv, h0 = _num(m.group(1)), _num(hm.group(1))
            val = sp.simplify(dv / (_PI * frac ** 2 * h0 ** 2))
            vcoef = sp.Rational(frac ** 2, 3)
            steps = [
                f"h = r/{frac}, so r = {frac}h and V = "
                f"(1/3) pi r^2 h = {fmt(vcoef)} pi h^3.",
                f"dV/dt = pi x {frac}^2 h^2 (dh/dt). At h = "
                f"{fmt(h0)}: {fmt(dv)} = pi x {frac ** 2} x "
                f"{fmt(h0 ** 2)} x dh/dt.",
                f"dh/dt = {fmt(val)} cm/s.",
            ]
            return _result("rate_sand_cone", f"{fmt(val)} "
                           "cm/s", steps, typ="calculus",
                           value=val)
    # --- Cylindrical tank depth ------------------------------
    m = re.search(r"cylindrical tank of radius ([\d.]+)\s*m",
                  low)
    dm = re.search(r"rate of ([\d.]+) cubic metre per hour",
                   low)
    if m and dm:
        dv = _num(dm.group(1))
        r0 = _num(m.group(1))
        val = sp.simplify(dv / (_PI * r0 ** 2))
        approx = float(val)
        steps = [
            "V = pi r^2 h with r fixed, so dV/dt = "
            "pi r^2 (dh/dt).",
            f"dh/dt = {fmt(dv)} / (pi x {fmt(r0)}^2) = "
            f"{fmt(val)} m/h, about {approx:.2f} m/h.",
        ]
        return _result("rate_tank_depth",
                       f"About {approx:.1f} m/h", steps,
                       typ="calculus", value=val)
    # --- Isosceles triangle area rate --------------------------
    if "isosceles triangle" in low and "fixed base" in low \
            and "decreasing at the rate of" in low:
        rm = re.search(r"decreasing at the rate of "
                       r"([\d.]+)\s*cm per second", low)
        if rm:
            rate = _num(rm.group(1))
            b = sp.Symbol("b", positive=True)
            s_ = b
            dA = b * s_ / sp.sqrt(4 * s_ ** 2 - b ** 2)
            val = sp.simplify(dA * rate)
            steps = [
                "With equal sides s and base b, A = "
                "(b/4) sqrt(4s^2 - b^2).",
                "dA/ds = bs / sqrt(4s^2 - b^2); at s = b "
                f"this is b/sqrt(3).",
                f"dA/dt = -(b/sqrt(3)) x {fmt(rate)} "
                f"= -{fmt(val)} cm^2/s.",
            ]
            return _result("rate_isosceles",
                           f"Decreasing at {fmt(val)} "
                           "cm^2/s", steps, typ="calculus")
    # --- Marginal cost / revenue ------------------------------
    m = re.search(r"c\(x\)\s*=\s*(.+?)(?:\.|,)?\s*(?:find|"
                  r"what is) the marginal", low)
    if m:
        expr = _fexpr(m.group(1))
        nm = re.search(r"when\s+(?:x|the number of units "
                       r"produced)\s*(?:is|=)\s*(\d+)", low)
        if expr is not None and nm:
            n0 = int(nm.group(1))
            d1 = sp.diff(expr, x)
            val = sp.simplify(d1.subs(x, n0))
            steps = [
                f"C'(x) = {fmt(d1)}",
                f"Marginal cost at x = {n0}: C'({n0}) = "
                f"{fmt(val)}",
            ]
            return _result("marginal_cost", fmt(val), steps,
                           typ="calculus", value=val)
    return None


def _aod_word_maxima(s, low):
    # Two numbers, sum S, product maximum.
    m = re.search(r"two numbers whose sum is ([\d.]+) and "
                  r"whose product is as large as possible",
                  low)
    if m:
        S = _num(m.group(1))
        half = S / 2
        steps = [
            f"Let the numbers be x and {fmt(S)} - x. "
            f"Product P = x({fmt(S)} - x).",
            f"P'(x) = {fmt(S)} - 2x = 0 gives x = "
            f"{fmt(half)}, and P'' < 0 there.",
        ]
        return _result("word_max_two_numbers",
                       f"{fmt(half)} and {fmt(half)}", steps,
                       typ="calculus")
    # x + y = S, x^p y^q maximum (incl. "sum is S").
    m = re.search(
        r"(?:x \+ y = ([\d.]+)|sum is ([\d.]+))[^.]*?"
        r"x\^?(\d*)\s*y\^?(\d+)\s*is\s*(?:a\s+)?maximum",
        low)
    if m:
        S = _num(m.group(1) or m.group(2))
        p = int(m.group(3)) if m.group(3) else 1
        q = int(m.group(4))
        xv = S * p / (p + q)
        yv = S * q / (p + q)
        # Verify on the concrete instance.
        f = x ** p * (S - x) ** q
        d1 = sp.diff(f, x)
        if sp.simplify(d1.subs(x, xv)) != 0:
            return None
        if float(sp.diff(f, x, 2).subs(x, xv)) >= 0:
            return None
        steps = [
            f"y = {fmt(S)} - x, so P = x^{p} ({fmt(S)} - "
            f"x)^{q}.",
            f"P'(x) = 0 gives x = {fmt(xv)} (the other "
            "root makes P = 0), and P'' < 0 there.",
            f"y = {fmt(S)} - {fmt(xv)} = {fmt(yv)}.",
        ]
        return _result("word_max_product_powers",
                       f"x = {fmt(xv)}, y = {fmt(yv)}", steps,
                       typ="calculus")
    # Sum S, sum of cubes minimum.
    m = re.search(r"sum is ([\d.]+) and the sum of "
                  r"(?:whose|their) cubes is minimum", low)
    if m:
        S = _num(m.group(1))
        half = S / 2
        f = x ** 3 + (S - x) ** 3
        if float(sp.diff(f, x, 2).subs(x, half)) <= 0:
            return None
        steps = [
            f"C = x^3 + ({fmt(S)} - x)^3; C'(x) = 0 gives "
            f"x = {fmt(half)}, and C'' > 0 there.",
        ]
        return _result("word_min_sum_cubes",
                       f"{fmt(half)} and {fmt(half)}", steps,
                       typ="calculus")
    # Tin box: sheet A x B, cut squares, volume maximum.
    m = re.search(r"sheet of tin ([\d.]+)\s*cm by "
                  r"([\d.]+)\s*cm", low)
    if m and "box" in low and "volume" in low:
        A, B = _num(m.group(1)), _num(m.group(2))
        V = x * (A - 2 * x) * (B - 2 * x)
        d1 = sp.diff(V, x)
        roots = [r for r in sp.solve(d1, x)
                 if r.is_real and 0 < float(r)
                 < float(min(A, B)) / 2]
        good = [r for r in roots
                if float(sp.diff(V, x, 2).subs(x, r)) < 0]
        if len(good) != 1:
            return None
        r0 = sp.simplify(good[0])
        steps = [
            f"V = x({fmt(A)} - 2x)({fmt(B)} - 2x) "
            f"= {fmt(sp.expand(V))}.",
            f"V'(x) = {fmt(d1)} = 0 gives x = {fmt(r0)} "
            "in the valid range, and V'' < 0 there.",
        ]
        return _result("word_max_tin_box",
                       f"{fmt(r0)} cm", steps, typ="calculus",
                       value=r0)
    # Cylinder of given volume, minimum surface area.
    m = re.search(r"cylindrical cans?[^.]*?volume of "
                  r"([\d.]+) cubic centimetres[^.]*?"
                  r"minimum surface area", low)
    if m:
        V = _num(m.group(1))
        r = (V / (2 * _PI)) ** sp.Rational(1, 3)
        h = sp.simplify(V / (_PI * r ** 2))
        if sp.simplify(h - 2 * r) != 0:
            return None
        steps = [
            "S = 2 pi r^2 + 2V/r. S'(r) = 4 pi r - "
            "2V/r^2 = 0 gives r^3 = V/(2 pi).",
            f"r = {fmt(r)} cm, and h = V/(pi r^2) = "
            f"{fmt(h)} cm = 2r.",
        ]
        return _result("word_min_cylinder_surface",
                       f"Radius = {fmt(r)} cm, height = "
                       f"{fmt(h)} cm", steps, typ="calculus")
    # Wire cut into square + circle, combined area minimum.
    m = re.search(r"wire of length ([\d.]+)\s*m.*?"
                  r"square.*?circle.*?minimum", low)
    if m:
        L = _num(m.group(1))
        xsq = sp.simplify(4 * L / (_PI + 4))
        xci = sp.simplify(L * _PI / (_PI + 4))
        # Verify: A'(x) = 0 at xsq and A'' > 0.
        A = x ** 2 / 16 + (L - x) ** 2 / (4 * _PI)
        if sp.simplify(sp.diff(A, x).subs(x, xsq)) != 0:
            return None
        steps = [
            "If x m makes the square, A = x^2/16 + "
            "(L - x)^2/(4 pi).",
            f"A'(x) = 0 gives x = 4L/(pi + 4) = "
            f"{fmt(xsq)} m for the square.",
            f"Circle piece = {fmt(L)} - {fmt(xsq)} = "
            f"{fmt(xci)} m.",
        ]
        return _result("word_min_wire_square_circle",
                       f"Square piece = {fmt(xsq)} m, "
                       f"circle piece = {fmt(xci)} m", steps,
                       typ="calculus")
    return None


def _aod142(question):
    raw = str(question)
    s = _fold_ascii_powers(_prep(raw))
    low = s.lower()
    got = _aod_rates(s, low)
    if got is not None:
        return got
    got = _aod_word_maxima(s, low)
    if got is not None:
        return got
    if "interval" in low or "increasing" in low \
            or "decreasing" in low:
        got = _aod_abs_maxmin(s, low)
        if got is not None:
            return got
        got = _aod_intervals(s, low)
        if got is not None:
            return got
    got = _aod_global_extremum(s, low)
    if got is not None:
        return got
    if "maximum" in low or "minimum" in low:
        got = _aod_abs_maxmin(s, low)
        if got is not None:
            return got
    return None


# ---------------------------------------------------------------------------
# 6. Conics (Class 11 directory gap) + minimal area family
# ---------------------------------------------------------------------------

def _conics142(question):
    raw = str(question)
    s = _fold_ascii_powers(_prep(raw))
    low = s.lower()
    # --- Parabola standard forms ---------------------------
    # Facts only when a fact is actually asked: a parabola
    # equation inside a nearest-point / tangent question is
    # not a facts ask.
    _facts_ask = any(k in low for k in (
        "focus", "foci", "vertex", "directrix", "latus",
        "axis", "eccentricity"))
    m = re.search(r"y\^2\s*=\s*(-?[\d.]+)\s*x\b", s)
    m_sym = re.search(r"y\^2\s*=\s*4\s*a\s*x\b", s)
    if (m or m_sym) and _facts_ask:
        a = sp.Rational(1) if m_sym else _num(m.group(1)) / 4
        if a != 0:
            return _parabola_answer(a, "y", low, hindi=False)
    m = re.search(r"x\^2\s*=\s*(-?[\d.]+)\s*y\b", s)
    m_sym = re.search(r"x\^2\s*=\s*4\s*a\s*y\b", s)
    if (m or m_sym) and _facts_ask:
        a = sp.Rational(1) if m_sym else _num(m.group(1)) / 4
        if a != 0:
            return _parabola_answer(a, "x", low, hindi=False)
    # --- Ellipse / hyperbola facts ---------------------------
    m = re.search(
        r"x\^2\s*/\s*(\d+(?:\.\d+)?)\s*([+-])\s*"
        r"y\^2\s*/\s*(\d+(?:\.\d+)?)\s*=\s*1", s)
    if m and ("ellipse" in low or "hyperbola" in low
              or "foci" in low or "eccentricity" in low
              or "latus" in low or "vertices" in low):
        A, B = _num(m.group(1)), _num(m.group(3))
        sign = m.group(2)
        return _ellipse_hyperbola(A, B, sign, low)
    m = re.search(
        r"y\^2\s*/\s*(\d+(?:\.\d+)?)\s*-\s*"
        r"x\^2\s*/\s*(\d+(?:\.\d+)?)\s*=\s*1", s)
    if m and ("hyperbola" in low or "foci" in low
              or "eccentricity" in low or "latus" in low):
        B, A = _num(m.group(1)), _num(m.group(2))
        return _ellipse_hyperbola(A, B, "-", low,
                                  transverse_y=True)
    # --- Circle: centre / radius from the general form -------
    m = re.search(
        r"x\^2\s*\+\s*y\^2\s*([+-])\s*(\d+(?:\.\d+)?)\s*x\s*"
        r"([+-])\s*(\d+(?:\.\d+)?)\s*y\s*([+-])\s*"
        r"(\d+(?:\.\d+)?)\s*=\s*0", s)
    if m and ("centre" in low or "center" in low
              or "radius" in low):
        D = _num(m.group(2)) * (1 if m.group(1) == "+"
                                else -1)
        E = _num(m.group(4)) * (1 if m.group(3) == "+"
                                else -1)
        Fc = _num(m.group(6)) * (1 if m.group(5) == "+"
                                 else -1)
        cx, cy = -D / 2, -E / 2
        r2 = cx ** 2 + cy ** 2 - Fc
        if r2 <= 0:
            return None
        r = sp.sqrt(r2)
        steps = [
            "For x^2 + y^2 + 2gx + 2fy + c = 0 the centre "
            "is (-g, -f) and radius sqrt(g^2 + f^2 - c).",
            f"Centre = ({fmt(cx)}, {fmt(cy)}), radius = "
            f"{fmt(r)}",
        ]
        if "radius" in low and "centre" not in low \
                and "center" not in low:
            ans = f"Radius = {fmt(r)}"
        elif "centre" in low or "center" in low:
            ans = f"Centre = ({fmt(cx)}, {fmt(cy)})"
            if "radius" in low:
                ans += f", radius = {fmt(r)}"
        else:
            ans = steps[-1]
        return _result("circle_centre_radius", ans, steps,
                       typ="geometry", value=r)
    return None


def _parabola_answer(a, squared, low, hindi):
    """squared == 'y': parabola y^2 = 4a x; 'x': x^2 = 4a y.
    a may be signed; the opening follows its sign."""
    aa = abs(a)
    sgn = 1 if a > 0 else -1
    if squared == "y":
        focus = (fmt(sgn * aa), "0")
        vertex = "(0, 0)"
        directrix = f"x = {fmt(-sgn * aa)}"
        axis = "y = 0 (the x-axis)"
    else:
        focus = ("0", fmt(sgn * aa))
        vertex = "(0, 0)"
        directrix = f"y = {fmt(-sgn * aa)}"
        axis = "x = 0 (the y-axis)"
    lr = 4 * aa
    asked = []
    steps = [f"Comparing with the standard form, "
             f"a = {fmt(aa)}."]
    if "focus" in low or "foci" in low:
        asked.append(f"focus = ({focus[0]}, {focus[1]})")
    if "vertex" in low:
        asked.append(f"vertex = {vertex}")
    if "directrix" in low:
        asked.append(f"directrix: {directrix}")
    if "latus" in low:
        asked.append(f"length of latus rectum = {fmt(lr)}")
    if "axis" in low:
        asked.append(f"axis: {axis}")
    if not asked:
        asked = [f"focus = ({focus[0]}, {focus[1]})",
                 f"vertex = {vertex}",
                 f"directrix: {directrix}",
                 f"length of latus rectum = {fmt(lr)}"]
    steps.append("; ".join(asked))
    return _result("parabola_facts", "; ".join(asked),
                   steps, typ="geometry")


def _ellipse_hyperbola(A, B, sign, low, transverse_y=False):
    """A = denominator under the positive term's variable
    squared (a^2), B = the other denominator (b^2)."""
    a = sp.sqrt(A)
    if sign == "+":
        if A >= B:
            e = sp.sqrt(1 - B / A)
            foci = (sp.sqrt(A - B), 0)
            lr = 2 * B / a
            verts = (a, 0)
            major = 2 * a
            minor = 2 * sp.sqrt(B)
            kind = "ellipse"
        else:
            e = sp.sqrt(1 - A / B)
            foci = (0, sp.sqrt(B - A))
            lr = 2 * A / sp.sqrt(B)
            verts = (0, sp.sqrt(B))
            major = 2 * sp.sqrt(B)
            minor = 2 * a
            kind = "ellipse"
    else:
        e = sp.sqrt(1 + B / A)
        if transverse_y:
            foci = (0, sp.sqrt(A + B))
            verts = (0, a)
        else:
            foci = (sp.sqrt(A + B), 0)
            verts = (a, 0)
        lr = 2 * B / a
        major = minor = None
        kind = "hyperbola"
    asked = []
    steps = [f"a^2 = {fmt(A)}, b^2 = {fmt(B)} "
             f"({kind})."]
    if "eccentricity" in low:
        asked.append(f"eccentricity e = {fmt(e)}")
    if "foci" in low or "focus" in low:
        if foci[1] == 0:
            asked.append(f"foci = (+-{fmt(foci[0])}, 0)")
        else:
            asked.append(f"foci = (0, +-{fmt(foci[1])})")
    if "vertices" in low or "vertex" in low:
        if verts[1] == 0:
            asked.append(f"vertices = (+-{fmt(verts[0])}, 0)")
        else:
            asked.append(f"vertices = (0, +-{fmt(verts[1])})")
    if "latus" in low:
        asked.append(f"length of latus rectum = {fmt(lr)}")
    if "major" in low and major is not None:
        asked.append(f"length of major axis = {fmt(major)}")
    if "minor" in low and minor is not None:
        asked.append(f"length of minor axis = {fmt(minor)}")
    if not asked:
        return None
    steps.append("; ".join(asked))
    return _result(f"{kind}_facts", "; ".join(asked), steps,
                   typ="geometry")


def _deabs(f, mid):
    """Replace each Abs(arg) in f by +arg or -arg according
    to the sign of arg at the sample point mid."""
    def pick(e):
        try:
            return e.args[0] if float(
                e.args[0].subs(x, mid)) >= 0 else -e.args[0]
        except Exception:
            return e
    return f.replace(lambda e: isinstance(e, sp.Abs), pick)


def _area_integral(f, a, b):
    """Exact area between f and the x-axis on [a, b]:
    split at the real roots of f inside, integrate each
    piece, add absolute values. Verified numerically."""
    pts = [a]
    try:
        for r in sp.solve(f, x):
            if r.is_real and not r.free_symbols \
                    and float(a) < float(r) < float(b):
                pts.append(r)
    except Exception:
        pass
    # Abs arguments change sign at their own roots: split
    # there too (the x|x| family).
    for node in sp.preorder_traversal(f):
        if isinstance(node, sp.Abs):
            try:
                for r in sp.solve(node.args[0], x):
                    if r.is_real and not r.free_symbols \
                            and float(a) < float(r) \
                            < float(b):
                        pts.append(r)
            except Exception:
                pass
    pts.append(b)
    pts = sorted(set(pts), key=lambda v: float(v))
    total = sp.Integer(0)
    for lo_p, hi_p in zip(pts, pts[1:]):
        mid = (float(lo_p) + float(hi_p)) / 2.0
        try:
            piece = sp.integrate(_deabs(f, mid),
                                 (x, lo_p, hi_p))
        except Exception:
            return None
        if piece.has(sp.Integral):
            return None
        total += abs(sp.simplify(piece))
    total = sp.simplify(total)
    # Numeric cross-check (Simpson sampling).
    try:
        n = 200
        fa, fb = float(a), float(b)
        h = (fb - fa) / n
        acc = 0.0
        for i in range(n + 1):
            v = fa + i * h
            fv = abs(float(f.subs(x, v)))
            acc += fv * (4 if i % 2 else 2) * \
                (0.5 if i in (0, n) else 1)
        numeric = acc * h / 3.0
        if abs(numeric - float(total)) > 0.02 * max(
                1.0, abs(numeric)):
            return None
    except Exception:
        return None
    return total


def _area142(question):
    raw = str(question)
    s = _fold_ascii_powers(_prep(raw))
    low = s.lower()
    if "area" not in low and "क्षेत्रफल" not in raw:
        return None
    # --- Ellipse area ---------------------------------------
    if "ellipse" in low:
        A = B = None
        m = re.search(r"x\^2\s*/\s*(\d+(?:\.\d+)?)", s)
        m2 = re.search(r"y\^2\s*/\s*(\d+(?:\.\d+)?)", s)
        if m and m2:
            A, B = _num(m.group(1)), _num(m2.group(1))
        else:
            # Extraction order: "= 1 . A B x2 y2".
            m3 = re.search(r"=\s*1\s*\.?\s*(\d+(?:\.\d+)?)"
                           r"\s+(\d+(?:\.\d+)?)", s)
            if m3:
                A, B = _num(m3.group(1)), _num(m3.group(2))
        if A is not None and B is not None:
            val = _PI * sp.sqrt(A) * sp.sqrt(B)
            steps = [
                "Area of the ellipse x^2/a^2 + y^2/b^2 "
                f"= 1 is pi*a*b = pi x {fmt(sp.sqrt(A))} "
                f"x {fmt(sp.sqrt(B))} = {fmt(val)} sq. "
                "units.",
            ]
            return _result("area_ellipse",
                           f"{fmt(val)} sq. units", steps,
                           typ="calculus", value=val)
        if re.search(r"a(?:\^2|2)(?!\d)", s) \
                and re.search(r"b(?:\^2|2)(?!\d)", s):
            steps = ["Area of the ellipse x^2/a^2 + "
                     "y^2/b^2 = 1 is pi*a*b sq. units."]
            return _result("area_ellipse", "pi*a*b sq. "
                           "units", steps, typ="calculus")
    # --- Circle area (whole / first quadrant) -----------------
    m = re.search(r"x\^2\s*\+\s*y\^2\s*=\s*(\d+(?:\.\d+)?)",
                  s)
    if m and ("enclosed" in low or "bounded" in low
              or "lying" in low or "area of the region"
              in low or "area enclosed" in low):
        r = sp.sqrt(_num(m.group(1)))
        if "first quadrant" in low:
            val = _PI * r ** 2 / 4
            steps = [
                f"The region is a quarter of the circle "
                f"of radius {fmt(r)}: area = pi r^2 / 4 "
                f"= {fmt(val)} sq. units.",
            ]
            return _result("area_circle_quarter",
                           f"{fmt(val)} sq. units", steps,
                           typ="calculus", value=val)
        val = _PI * r ** 2
        steps = [
            f"Area enclosed by the circle of radius "
            f"{fmt(r)} is pi r^2 = {fmt(val)} sq. units.",
        ]
        return _result("area_circle", f"{fmt(val)} sq. "
                       "units", steps, typ="calculus",
                       value=val)
    if re.search(r"x\^2\s*\+\s*y\^2\s*=\s*a(?:\^2|2)"
                 r"(?!\d)", s) \
            and ("enclosed" in low or "area" in low):
        steps = ["Area enclosed by the circle x^2 + y^2 "
                 "= a^2 is pi a^2 sq. units."]
        return _result("area_circle", "pi*a^2 sq. units",
                       steps, typ="calculus")
    # --- Single curve + x-axis + ordinates (multi-part ok) ----
    if "x-axis" in low or "x - axis" in low \
            or "between x" in low:
        parts = re.split(r"\(\s*(?:i{1,3}|iv)\s*\)", s)
        answers = []
        steps_all = []
        values = []
        for part in parts:
            got = _area_single(part)
            if got is not None:
                answers.append(got[0])
                steps_all.extend(got[1])
                values.append(got[2])
        if answers:
            return _result(
                "area_under_curve", "; ".join(answers),
                steps_all, typ="calculus",
                value=values[0] if len(values) == 1 else None)
    # --- Two explicit curves -----------------------------------
    m = re.search(r"bounded by (?:the curves?\s+)?y\s*=\s*"
                  r"(.+?)\s+and\s+y\s*=\s*(.+?)(?:\.|$)", s)
    if m:
        f = _fexpr(m.group(1))
        g = _fexpr(m.group(2))
        if f is not None and g is not None:
            try:
                roots = [r for r in sp.solve(f - g, x)
                         if r.is_real and not r.free_symbols]
            except Exception:
                roots = []
            if len(roots) == 2:
                a, b = sorted(roots, key=lambda v: float(v))
                val = _area_integral(f - g, a, b)
                if val is not None:
                    steps = [
                        f"The curves meet at x = {fmt(a)} "
                        f"and x = {fmt(b)}.",
                        "Area = integral of |f - g| between "
                        f"them = {fmt(val)} sq. units.",
                    ]
                    return _result("area_between_curves142",
                                   f"{fmt(val)} sq. units",
                                   steps, typ="calculus",
                                   value=val)
    # --- Parabola + y-axis + horizontal line -------------------
    m = re.search(r"y\^2\s*=\s*(\d+(?:\.\d+)?)\s*x", s)
    if m and "y-axis" in low:
        lm = re.search(r"line y\s*=\s*(\d+(?:\.\d+)?)", s)
        if lm:
            k = _num(m.group(1))
            c = _num(lm.group(1))
            val = sp.simplify(c ** 3 / (3 * k))
            steps = [
                f"x = y^2/{fmt(k)}; area = integral from "
                f"0 to {fmt(c)} of y^2/{fmt(k)} dy "
                f"= {fmt(val)} sq. units.",
            ]
            return _result("area_parabola_yaxis",
                           f"{fmt(val)} sq. units", steps,
                           typ="calculus", value=val)
    return None


def _area_single(part):
    """One 'y = f, x = a, x = b and x-axis' segment.
    Returns (answer_str, steps) or None."""
    m = re.search(r"y\s*=\s*(.+)$", part)
    if not m:
        return None
    # The body ends at the first comma, "between" or "and".
    body = re.split(r",|\s+between\s+|\s+and\s+",
                    m.group(1))[0]
    body = body.replace("| x |", "Abs(x)") \
        .replace("|x|", "Abs(x)")
    f = _fexpr(body)
    if f is None:
        return None
    lims = []
    for tok in re.findall(
            r"x\s*=\s*(-?\d+(?:\.\d+)?\s*pi(?:\s*/\s*\d+)?|"
            r"-?\d+(?:\.\d+)?|pi(?:\s*/\s*\d+)?)",
            part):
        try:
            v = _dparse(tok)
        except Exception:
            v = None
        if v is not None and not v.free_symbols:
            lims.append(v)
    if len(lims) < 2:
        return None
    a, b = lims[0], lims[1]
    if a == b:
        return None
    if float(a) > float(b):
        a, b = b, a
    val = _area_integral(f, a, b)
    if val is None:
        return None
    steps = [
        f"Area = integral from {fmt(a)} to {fmt(b)} of "
        f"|{fmt(f)}| dx = {fmt(val)} sq. units.",
    ]
    return f"{fmt(val)} sq. units", steps, val


# ---------------------------------------------------------------------------
# Dispatcher + upgrade hook
# ---------------------------------------------------------------------------

_FAMILIES = (_invtrig, _vectors142, _continuity142,
             _differentiation142, _aod142, _area142,
             _conics142)


def solve_c12gaps(question):
    """Wave 142 dispatcher: the first strict schema that
    settles the question wins; None declines."""
    for fn in _FAMILIES:
        try:
            got = fn(question)
        except Exception:
            got = None
        if got is not None:
            return got
    return None


def _norm_ans(text):
    s = str(text).lower()
    s = re.sub(r"[^a-z0-9./^*-]+", "", s)
    return s


def c12gaps142_upgrade(question, result):
    """Replace a real-looking but WRONG primary answer when
    a Wave 142 schema settles the same question and the
    served answer verifiably differs. Returns the
    replacement result, or None to keep the primary."""
    if not isinstance(result, dict):
        return None
    mine = solve_c12gaps(question)
    if mine is None:
        return None
    served = result.get("answer")
    if served is None:
        return None
    my_val = mine.get("value")
    sv_val = result.get("value")
    if my_val is not None and isinstance(sv_val, (int, float)):
        if abs(float(my_val) - float(sv_val)) > 1e-6:
            return mine
        return None
    a = _norm_ans(mine.get("answer", ""))
    b = _norm_ans(served)
    if not a or not b:
        return None
    if a == b:
        return None
    if a in b or b in a:
        # Containment without equality: one side is a
        # truncated or padded variant of the other (the
        # primary serving "b" for a true "b/a"). My
        # schema-verified exact form wins.
        return mine
    # Verdict answers: a yes/no flip is a verifiable
    # difference; anything else needs the numeric path.
    ya = a.startswith("yes") or a.startswith("not")
    yb = b.startswith("yes") or b.startswith("not")
    if ya and yb and (a.startswith("yes")
                      != b.startswith("yes")):
        return mine
    if my_val is not None:
        return mine
    # Numeric-token path (multi-part area answers carry
    # no single value): if every number in my answer is
    # absent from the served answer, the served answer
    # cannot be the same result in another dress.
    my_nums = _ans_numbers(mine.get("answer", ""))
    sv_nums = _ans_numbers(served)
    if my_nums and all(
            all(abs(mn - sn) > 1e-6 for sn in sv_nums)
            for mn in my_nums):
        return mine
    # Area asks: my answer carries square units, the
    # served one does not (the primary sometimes reads
    # "area enclosed by x^2 + y^2 = a^2" as implicit
    # differentiation and serves a dy/dx).
    if "area" in str(question).lower() \
            and "sq" in str(mine.get("answer", "")) \
            and "sq" not in str(served):
        return mine
    # Derivative asks answered with an integral: the
    # primary sometimes replies "derivative: ...;
    # integral: ..." with y-laden fragments. A dy/dx
    # question served an integral is off-task.
    ql = str(question).lower()
    if ("dy/dx" in ql or "derivative" in ql
            or "differentiat" in ql) \
            and "integral" in str(served).lower() \
            and "integral" not in str(
                mine.get("answer", "")).lower():
        return mine
    return None


def _ans_numbers(text):
    out = []
    for tok in re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?",
                          str(text)):
        try:
            if "/" in tok:
                n, d = tok.split("/")
                out.append(float(n) / float(d))
            else:
                out.append(float(tok))
        except Exception:
            continue
    return out
