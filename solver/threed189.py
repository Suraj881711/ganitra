"""Wave 189: Three Dimensional Geometry — shortest distance
between two lines, angle between lines, line equations, and
plane basics (Class 12, NCERT Ex 11.1-11.2 + TN Line and
Plane).

Why this module exists (form audit, 19 Nov 2026, item B.4 /
table rows 4-5; probes 17-18): direction cosines through two
points already solved (geometry.py Wave 32), and tierA169
(Waves 169/171) serves a 3D line through a point parallel to
an i/j/k vector — but the rest of the chapter had no native
schema at all.  Probe 17 verbatim —

    Find the shortest distance between the lines
    r = (i + 2j + k) + lambda(i - j + k) and
    r = (2i - j - k) + mu(2i + j + 2k)

— fell to the generic geometry guide (op "unknown").  The
cartesian shortest-distance dress, parallel-line distance,
line through two points, every plane form (point + normal,
three points, intercepts), point-to-plane distance in the
r.n = d dress, and angle between planes likewise missed
(measured 19 Nov; see ganitra-wave189-notes.md).

Two measured WRONG serves are repaired in router.py at the
return sites of the gates that produce them (displacement
only for the measured op + a strict complete match in this
module + a different answer — see
threed189_should_displace):
  * "angle between the lines r = ... and r = ..." — the
    c12gaps142 angle schema reads the first line's POINT
    vector and direction as the pair, serving cos^-1(5/6)
    (33.6 degrees) where the true direction vectors give
    cos = 1/2 (60 degrees).
  * "equation of the plane with intercepts 2, 3 and 4 on
    the x, y and z axes" — the 2D rekha intercept schema
    serves "x/2 + y/3 = 1", dropping the z term entirely.

House rules, identical to Waves 169/175: a schema fires
only when it settles the question COMPLETELY, every served
value is recomputed exactly (Fractions / SymPy) and checked
by an independent second computation before serving, and
anything doubtful returns None so routing continues
unchanged.  Wiring: a failure-only gate at the end of
router._solve_question_uncached, after the Wave 175 block —
a question the solver already answers is never displaced,
except via the two strict repairs above.

The ASCII i/j/k parser here is SCOPED: it is only ever
called on segments this module has already claimed as line
or plane dresses (after "r =", after "normal", inside a
cartesian fraction triple).  It never sees a general
question, so complex-number text such as "(2 + 3i)(1 - i)"
keeps its current behaviour untouched.
"""
import re
from fractions import Fraction
from math import gcd

import sympy as sp

from .expression_parser import fmt, fmt_num

_F0 = Fraction(0)
_F1 = Fraction(1)


# ---------------------------------------------------------------------------
# Text preparation (scoped to this module)
# ---------------------------------------------------------------------------

def _prep(text):
    s = str(text)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("î", "i").replace("ĵ", "j")
    s = re.sub(r"([ijk])\u0302", r"\1", s)
    s = s.replace("·", ".").replace("•", ".")
    s = s.replace("λ", "lambda").replace("μ", "mu")
    return s.lower()


def _num(tok):
    """Exact Fraction from '3', '-2.5' or '3/2' (spaces ok)."""
    return Fraction(str(tok).replace(" ", ""))


def _fr_str(fr):
    return fmt_num(sp.Rational(fr.numerator, fr.denominator))


def _is_zero(v):
    return all(c == 0 for c in v)


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _sym_vec(v):
    return sp.Matrix([sp.Rational(c.numerator, c.denominator)
                      for c in v])


def _exact_norm(v):
    """|v| as an exact sympy value (verified against Matrix)."""
    m = _sym_vec(v)
    return sp.simplify(sp.sqrt(m.dot(m)))


def _result(op, answer, steps):
    return {"type": "geometry", "op": op,
            "answer": answer, "steps": steps}


# ---------------------------------------------------------------------------
# Scoped vector / point parsing
# ---------------------------------------------------------------------------

def _wraps(s):
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0 or (depth == 0 and i != len(s) - 1):
                return False
    return depth == 0


_TERM_RE = re.compile(
    r"([+-]?)(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)?)?([ijk])")


def _vec(seg):
    """Parse a COMPLETE vector literal -> (Fraction, Fraction,
    Fraction) or None.  Accepts '(i + 2j - k)', '2i - j + 2k',
    '(2, -1, 3)' and '2, -1, 3'.  Strict: the whole segment
    must be consumed, each unit at most once."""
    if seg is None:
        return None
    s = str(seg).strip().strip(".")
    while len(s) >= 2 and s[0] == "(" and s[-1] == ")" \
            and _wraps(s):
        s = s[1:-1].strip()
    if not s:
        return None
    if "," in s:
        parts = [p.strip() for p in s.split(",")]
        if len(parts) != 3:
            return None
        try:
            return tuple(_num(p) for p in parts)
        except Exception:
            return None
    t = re.sub(r"\s+", "", s)
    if not t:
        return None
    comp = {}
    pos = 0
    first = True
    while pos < len(t):
        m = _TERM_RE.match(t, pos)
        if not m:
            return None
        sign, coef, unit = m.group(1), m.group(2), m.group(3)
        if not first and sign == "":
            return None
        if unit in comp:
            return None
        try:
            c = _num(coef) if coef else _F1
        except Exception:
            return None
        if sign == "-":
            c = -c
        comp[unit] = c
        pos = m.end()
        first = False
    if not comp:
        return None
    return (comp.get("i", _F0), comp.get("j", _F0),
            comp.get("k", _F0))


_PT3_RE = re.compile(
    r"\(\s*(-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)\s*,"
    r"\s*(-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)\s*,"
    r"\s*(-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)\s*\)")


def _points3(q):
    out = []
    for m in _PT3_RE.finditer(q):
        try:
            out.append(tuple(_num(g) for g in m.groups()))
        except Exception:
            continue
    return out


def _vec_str(v):
    """(1, 2, -4) -> 'i + 2j - 4k' (tierA169 house style)."""
    parts = []
    for coef, letter in zip(v, "ijk"):
        if coef == 0:
            continue
        body = letter if abs(coef) == 1 \
            else f"{_fr_str(abs(coef))}{letter}"
        if not parts:
            parts.append(("-" if coef < 0 else "") + body)
        else:
            parts.append((" - " if coef < 0 else " + ") + body)
    return "".join(parts) if parts else "0"


def _pt_str(p):
    return "(" + ", ".join(_fr_str(c) for c in p) + ")"


# ---------------------------------------------------------------------------
# Line parsing — vector dress and cartesian dress
# ---------------------------------------------------------------------------

def _matching_close(s):
    depth = 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return None


def _junk_only(rest):
    return re.fullmatch(
        r"[\s\.,;:\?!]*(and)?[\s\.,;:\?!]*", rest or "") is not None


def _parse_line_seg(seg):
    """One 'r = ...' segment -> (point, direction) or None."""
    seg = seg.strip()
    seg = re.split(r"\b(?:find|show|determine|hence)\b", seg)[0]
    pm = re.search(r"\b(lambda|mu)\b", seg)
    if pm is None:
        pm = re.search(r"(?<![a-z])([ts])\s*\(", seg)
    if pm is None:
        pm = re.search(r"(?<![a-z])([ts])\s+", seg)
    if pm is None:
        return None
    head = seg[:pm.start()].strip()
    if head.endswith("+"):
        head = head[:-1].strip()
    tail = seg[pm.end():].strip()
    if tail.startswith("("):
        close = _matching_close(tail)
        if close is None:
            return None
        if not _junk_only(tail[close + 1:]):
            return None
        d = _vec(tail[:close + 1])
    else:
        d = _vec(tail)
        if d is None and " and " in tail:
            d = _vec(tail.split(" and ")[0])
    if d is None or _is_zero(d):
        return None
    if head == "":
        a = (_F0, _F0, _F0)
    else:
        a = _vec(head)
        if a is None:
            return None
    return (a, d)


def _lines_vector(q):
    """All 'r = a + param b' lines in the question.  Strict:
    if any r = segment fails to parse, no lines are claimed."""
    starts = list(re.finditer(r"\br\s*=", q))
    if not starts:
        return []
    lines = []
    for idx, m in enumerate(starts):
        end = starts[idx + 1].start() if idx + 1 < len(starts) \
            else len(q)
        line = _parse_line_seg(q[m.end():end])
        if line is None:
            return []
        lines.append(line)
    return lines


_FRAC_RE = re.compile(
    r"\(\s*([xyz])\s*(?:([+-])\s*(\d+(?:\.\d+)?))?\s*\)"
    r"\s*/\s*\(?\s*(-?\d+(?:\.\d+)?)\s*\)?")


def _lines_cartesian(q):
    """All '(x-x1)/a = (y-y1)/b = (z-z1)/c' lines, as
    (point, direction) pairs.  A triple counts only when the
    three fractions are x, y, z in order, joined by '='."""
    ms = list(_FRAC_RE.finditer(q))
    lines = []
    i = 0
    while i + 2 < len(ms):
        trio = ms[i:i + 3]
        if [t.group(1) for t in trio] != ["x", "y", "z"]:
            i += 1
            continue
        if any(q[a.end():b.start()].strip() != "="
               for a, b in zip(trio, trio[1:])):
            i += 1
            continue
        pt, dr, good = [], [], True
        for t in trio:
            try:
                den = _num(t.group(4))
                if t.group(3) is None:
                    coord = _F0
                elif t.group(2) == "-":
                    coord = _num(t.group(3))
                else:
                    coord = -_num(t.group(3))
            except Exception:
                good = False
                break
            if den == 0:
                good = False
                break
            pt.append(coord)
            dr.append(den)
        if not good:
            i += 1
            continue
        lines.append((tuple(pt), tuple(dr)))
        i += 3
    return lines


def _two_lines(q):
    lines = _lines_vector(q)
    if len(lines) == 2:
        return lines
    lines = _lines_cartesian(q)
    if len(lines) == 2:
        return lines
    return None


# ---------------------------------------------------------------------------
# Plane parsing — cartesian dress and r.n = d dress
# ---------------------------------------------------------------------------

def _parse_plane_lhs(chunk):
    """'2x - y + z - 5' -> ((a, b, c), const) or None.  The
    chunk must consist ONLY of x/y/z terms and one constant."""
    s = (chunk or "").strip()
    if not s or not re.fullmatch(r"[0-9xyz\s\.\+\-]+", s):
        return None
    if not any(v in s for v in "xyz"):
        return None
    t = re.sub(r"\s+", "", s)
    terms = re.findall(r"[+-]?[^+-]+", t)
    if "".join(terms) != t:
        return None
    coef = {"x": None, "y": None, "z": None}
    const = _F0
    seen_const = False
    for term in terms:
        sign = _F1
        body = term
        if body[:1] in ("+", "-"):
            sign = Fraction(-1) if body[0] == "-" else _F1
            body = body[1:]
        m = re.fullmatch(r"(\d+(?:\.\d+)?)?([xyz])", body)
        if m:
            var = m.group(2)
            if coef[var] is not None:
                return None
            try:
                c = _num(m.group(1)) if m.group(1) else _F1
            except Exception:
                return None
            coef[var] = sign * c
            continue
        if re.fullmatch(r"\d+(?:\.\d+)?", body):
            if seen_const:
                return None
            seen_const = True
            try:
                const = sign * _num(body)
            except Exception:
                return None
            continue
        return None
    n = tuple(coef[v] if coef[v] is not None else _F0
              for v in "xyz")
    if _is_zero(n):
        return None
    return (n, const)


def _find_planes_cartesian(q):
    """Every 'ax + by + cz (+ d) = N' plane in the question,
    as (normal, D) with the plane written n . r = D."""
    planes = []
    for m in re.finditer(r"=\s*(-?\d+(?:\.\d+)?)", q):
        try:
            rhs = _num(m.group(1))
        except Exception:
            continue
        bpos = 0
        for tok in ("plane", "planes", " and ", ":", ",", " is ",
                    ";"):
            idx = q.rfind(tok, 0, m.start())
            if idx >= 0:
                bpos = max(bpos, idx + len(tok))
        parsed = _parse_plane_lhs(q[bpos:m.start()])
        if parsed is None:
            continue
        n, const = parsed
        planes.append((n, rhs - const))
    return planes


def _find_planes_vector(q):
    """Every 'r.(...) = d' plane, as (normal, D)."""
    planes = []
    for m in re.finditer(r"\br\s*\.\s*", q):
        eq = re.match(r"(.+?)\s*=\s*(-?\d+(?:\.\d+)?)",
                      q[m.end():])
        if not eq:
            continue
        n = _vec(eq.group(1))
        if n is None or _is_zero(n):
            continue
        try:
            planes.append((n, _num(eq.group(2))))
        except Exception:
            continue
    return planes


def _reduce_plane_frac(n, D):
    """Scale a rational normal to smallest integers with a
    positive first non-zero component (D follows, and is
    divided only when the division is exact)."""
    dens = [c.denominator for c in n] + [D.denominator]
    L = 1
    for d in dens:
        L = L * d // gcd(L, d)
    ni = [int(c * L) for c in n]
    Di = int(D * L)
    g = 0
    for v in ni:
        g = gcd(g, abs(v))
    if g > 1 and Di % g == 0:
        ni = [v // g for v in ni]
        Di //= g
    for v in ni:
        if v != 0:
            if v < 0:
                ni = [-x for x in ni]
                Di = -Di
            break
    return (tuple(Fraction(v) for v in ni), Fraction(Di))


def _join_signed(terms):
    """[(neg, body), ...] -> '2x - y + 3z' style string."""
    out = ""
    for i, (neg, body) in enumerate(terms):
        if i == 0:
            out += ("-" if neg else "") + body
        else:
            out += (" - " if neg else " + ") + body
    return out


def _plane_cart_str(n, D):
    terms = []
    for coef, var in zip(n, "xyz"):
        if coef == 0:
            continue
        body = var if abs(coef) == 1 \
            else f"{_fr_str(abs(coef))}{var}"
        terms.append((coef < 0, body))
    if not terms:
        return None
    return f"{_join_signed(terms)} = {_fr_str(D)}"


def _cart_line_str(pt, d):
    parts, consts = [], []
    for coord, dd, var in zip(pt, d, "xyz"):
        if dd == 0:
            consts.append(f"{var} = {_fr_str(coord)}")
        else:
            if coord == 0:
                num = var
            elif coord > 0:
                num = f"{var} - {_fr_str(coord)}"
            else:
                num = f"{var} + {_fr_str(-coord)}"
            parts.append(f"({num})/{_fr_str(dd)}")
    cart = " = ".join(parts)
    if consts:
        cart = (cart + "; " if cart else "") + ", ".join(consts)
    return cart


def _serve_line(pt, d, op, lead_steps):
    if _is_zero(d):
        return None
    # Independent check: pt + d must sit on the cartesian
    # form with every ratio exactly 1.
    for i in range(3):
        if d[i] != 0 and (pt[i] + d[i] - pt[i]) / d[i] != 1:
            return None
    if _is_zero(pt):
        vec_form = f"r = lambda({_vec_str(d)})"
    else:
        vec_form = f"r = {_vec_str(pt)} + lambda({_vec_str(d)})"
    cart = _cart_line_str(pt, d)
    steps = lead_steps + [
        f"Vector form: {vec_form}.",
        f"Cartesian form: {cart}.",
    ]
    return _result(op, f"{vec_form}; {cart}", steps)


def _serve_plane(n, D, op, lead_steps):
    cart = _plane_cart_str(n, D)
    if cart is None:
        return None
    vec_form = f"r.({_vec_str(n)}) = {_fr_str(D)}"
    steps = lead_steps + [
        f"Vector form: {vec_form}.",
        f"Cartesian form: {cart}.",
    ]
    return _result(op, f"{vec_form}; {cart}", steps)


# ---------------------------------------------------------------------------
# Shared exact computations
# ---------------------------------------------------------------------------

def _dist_str(val):
    """Exact sympy distance -> served string."""
    if val == 0:
        return "0 units"
    if val.is_rational:
        return f"{fmt_num(val)} units"
    return f"{fmt(val)} units (about {float(val):.2f} units)"


def _angle_from_dirs(b1, b2):
    """(cos sympy, answer string) for the ACUTE angle between
    two direction vectors, or None on a zero vector."""
    if _is_zero(b1) or _is_zero(b2):
        return None
    m1, m2 = _sym_vec(b1), _sym_vec(b2)
    dot = m1.dot(m2)
    if m1.dot(m1) == 0 or m2.dot(m2) == 0:
        return None
    cosv = sp.simplify(abs(dot) / (sp.sqrt(m1.dot(m1))
                                   * sp.sqrt(m2.dot(m2))))
    # Independent float path for the degree value.
    import math as _math
    fcos = abs(_dot(b1, b2)) / (_math.sqrt(float(_dot(b1, b1)))
                                * _math.sqrt(float(_dot(b2, b2))))
    if abs(float(cosv) - fcos) > 1e-9:
        return None
    deg = _math.degrees(_math.acos(max(-1.0, min(1.0, fcos))))
    for std in (0, 30, 45, 60, 90):
        if abs(deg - std) < 1e-6:
            return cosv, f"{std} degrees"
    return cosv, (f"cos^-1({fmt(cosv)}) "
                  f"(about {deg:.1f} degrees)")


# ---------------------------------------------------------------------------
# (a) Shortest distance between two lines
# ---------------------------------------------------------------------------

def _sd(q):
    if "shortest distance" not in q:
        return None
    lines = _two_lines(q)
    if lines is None:
        return None
    (a1, b1), (a2, b2) = lines
    w = _sub(a2, a1)
    cross = _cross(b1, b2)
    if _is_zero(cross):
        # Parallel (or coincident) lines: point-to-line form.
        if _is_zero(_cross(w, b1)):
            steps = [
                f"Line 1 passes through {_pt_str(a1)} with "
                f"direction {_vec_str(b1)}.",
                f"Line 2 passes through {_pt_str(a2)} with "
                "the same direction, and a2 - a1 is parallel "
                "to that direction too.",
                "So the two lines are the same line "
                "(coincident), and the shortest distance "
                "between them is 0.",
            ]
            return _result("w189_sd_coincident", "0 units", steps)
        cw = _cross(w, b1)
        sd = sp.simplify(_exact_norm(cw) / _exact_norm(b1))
        # Independent check: |w|^2 - (component along b1)^2.
        alt = sp.simplify(sp.sqrt(
            _sym_vec(w).dot(_sym_vec(w))
            - (_sym_vec(w).dot(_sym_vec(b1)) ** 2)
            / _sym_vec(b1).dot(_sym_vec(b1))))
        if sp.simplify(sd - alt) != 0:
            return None
        steps = [
            "The lines are parallel (same direction "
            f"{_vec_str(b1)}), so the shortest distance is "
            "the distance from a point of one line to the "
            "other line: d = |b x (a2 - a1)| / |b|.",
            f"b x (a2 - a1) = {_vec_str(cw)}, |b x (a2 - a1)| "
            f"= {fmt(_exact_norm(cw))}, |b| = "
            f"{fmt(_exact_norm(b1))}.",
            f"d = {_dist_str(sd)}.",
        ]
        return _result("w189_sd_parallel", _dist_str(sd), steps)
    triple = _dot(w, cross)
    if triple == 0:
        steps = [
            f"b1 x b2 = {_vec_str(cross)}.",
            "(a2 - a1) . (b1 x b2) = 0, so the lines are "
            "coplanar; with non-parallel directions they "
            "meet at one point.",
            "So the lines intersect and the shortest "
            "distance between them is 0.",
        ]
        return _result("w189_sd_intersecting", "0 units", steps)
    sd = sp.simplify(abs(sp.Integer(triple.numerator)
                         if triple.denominator == 1 else
                         sp.Rational(triple.numerator,
                                     triple.denominator))
                     / _exact_norm(cross))
    # Independent recomputation through sympy Matrix.
    mcross = _sym_vec(b1).cross(_sym_vec(b2))
    mtriple = _sym_vec(w).dot(mcross)
    sd2 = sp.simplify(abs(mtriple) / sp.sqrt(mcross.dot(mcross)))
    if sp.simplify(sd - sd2) != 0:
        return None
    steps = [
        "For skew lines, d = |(a2 - a1) . (b1 x b2)| / "
        "|b1 x b2|.",
        f"b1 x b2 = {_vec_str(cross)}, |b1 x b2| = "
        f"{fmt(_exact_norm(cross))}.",
        f"(a2 - a1) . (b1 x b2) = {_fr_str(triple)}.",
        f"d = {_dist_str(sd)}.",
    ]
    return _result("w189_sd_skew", _dist_str(sd), steps)


# ---------------------------------------------------------------------------
# (b) Angles
# ---------------------------------------------------------------------------

def _angle_lines(q):
    if "angle between" not in q or "line" not in q:
        return None
    if "plane" in q:
        return None
    dirs = None
    lines = _two_lines(q)
    if lines is not None:
        dirs = (lines[0][1], lines[1][1])
    if dirs is None:
        m = re.search(
            r"direction ratios[^0-9\-]*(-?\d+(?:\.\d+)?)\s*,"
            r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
            r"\s+and\s+(-?\d+(?:\.\d+)?)\s*,\s*"
            r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", q)
        if m:
            try:
                dirs = (tuple(_num(m.group(i)) for i in (1, 2, 3)),
                        tuple(_num(m.group(i)) for i in (4, 5, 6)))
            except Exception:
                dirs = None
    if dirs is None and "direction vectors" in q:
        seg = q.split("direction vectors", 1)[1]
        parts = re.split(r"\s+and\s+", seg, maxsplit=1)
        if len(parts) == 2:
            va = _vec(parts[0].strip(" :"))
            vb = _vec(parts[1].strip(" ."))
            if va is not None and vb is not None:
                dirs = (va, vb)
    if dirs is None:
        return None
    got = _angle_from_dirs(dirs[0], dirs[1])
    if got is None:
        return None
    cosv, ans = got
    steps = [
        f"Direction vectors: {_vec_str(dirs[0])} and "
        f"{_vec_str(dirs[1])}.",
        f"cos theta = |b1 . b2| / (|b1| |b2|) = {fmt(cosv)}.",
        f"theta = {ans}.",
    ]
    return _result("w189_angle_lines", ans, steps)


def _angle_planes(q):
    if "angle between" not in q or "plane" not in q:
        return None
    planes = _find_planes_vector(q)
    if len(planes) != 2:
        planes = _find_planes_cartesian(q)
    if len(planes) != 2:
        return None
    (n1, _d1), (n2, _d2) = planes
    got = _angle_from_dirs(n1, n2)
    if got is None:
        return None
    cosv, ans = got
    steps = [
        "The angle between two planes is the angle between "
        "their normals.",
        f"Normals: {_vec_str(n1)} and {_vec_str(n2)}.",
        f"cos theta = |n1 . n2| / (|n1| |n2|) = {fmt(cosv)}.",
        f"theta = {ans}.",
    ]
    return _result("w189_angle_planes", ans, steps)


# ---------------------------------------------------------------------------
# (c) Line equations
# ---------------------------------------------------------------------------

def _line_eq(q):
    if "line" not in q or "equation" not in q:
        return None
    pts = _points3(q)
    dir_cue = any(w in q for w in
                  ("parallel", "direction", "perpendicular"))
    if len(pts) == 2 and pts[0] != pts[1] and not dir_cue:
        A, B = pts
        d = _sub(B, A)
        return _serve_line(A, d, "w189_line_two_points", [
            f"Direction of the line = B - A = {_vec_str(d)} "
            f"(from A{_pt_str(A)} to B{_pt_str(B)}).",
        ])
    if len(pts) > 2:
        return None
    # Point: explicit 3D point, or a stated position vector.
    pt = None
    mpv = re.search(r"position vector\s+(?:is\s+)?(.+?)"
                    r"(?:\s+and\b|\s+through\b|$)", q)
    if mpv:
        pt = _vec(mpv.group(1))
    if pt is None and len(pts) == 1:
        pt = pts[0]
    if pt is None:
        return None
    # Direction: direction ratios, a parallel/direction
    # vector, or a parallel cartesian line.
    d = None
    mdr = re.search(
        r"direction ratios\s*(?:are\s*|is\s*)?"
        r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,"
        r"\s*(-?\d+(?:\.\d+)?)", q)
    if mdr:
        try:
            d = tuple(_num(mdr.group(i)) for i in (1, 2, 3))
        except Exception:
            d = None
    if d is None:
        for pat in (r"parallel to(?:\s+the)?(?:\s+vector)?\s+(.+)$",
                    r"in the direction of\s+(.+)$",
                    r"direction vector\s+(?:is\s+)?(.+)$"):
            m = re.search(pat, q)
            if not m:
                continue
            seg = m.group(1)
            seg = re.split(r"\s+and\s+(?:passing|through)\b",
                           seg)[0]
            seg = re.split(r"\(\s*-?\d", seg)[0]
            cand = _vec(seg.strip().rstrip("."))
            if cand is not None:
                d = cand
                break
    if d is None and "parallel" in q:
        cl = _lines_cartesian(q)
        if len(cl) == 1:
            d = cl[0][1]
    if d is None or _is_zero(d):
        return None
    return _serve_line(pt, d, "w189_line_point_dir", [
        f"Point on the line: {_pt_str(pt)}; direction: "
        f"{_vec_str(d)}.",
    ])


# ---------------------------------------------------------------------------
# (d) Plane basics
# ---------------------------------------------------------------------------

def _plane_intercepts(q):
    if "plane" not in q or "intercept" not in q:
        return None
    vals = []
    for axis in "xyz":
        m = re.search(axis + r"\s*-?\s*intercept\s*(?:is\s*)?"
                      r"(-?\d+(?:\.\d+)?)", q)
        vals.append(_num(m.group(1)) if m else None)
    if any(v is None for v in vals):
        m = re.search(
            r"intercepts?\s*(?:are\s*|is\s*)?"
            r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
            r"\s*(?:,|\band\b)\s*(-?\d+(?:\.\d+)?)", q)
        if not m:
            return None
        try:
            vals = [_num(m.group(i)) for i in (1, 2, 3)]
        except Exception:
            return None
    a, b, c = vals
    if a == 0 or b == 0 or c == 0:
        return None
    terms = []
    for var, val in zip("xyz", vals):
        body = var if abs(val) == 1 else \
            f"{var}/{_fr_str(abs(val))}"
        terms.append((val < 0, body))
    intercept_str = _join_signed(terms) + " = 1"
    n, D = _reduce_plane_frac((b * c, a * c, a * b), a * b * c)
    # Verify: the three intercept points lie on the plane.
    for P in ((a, _F0, _F0), (_F0, b, _F0), (_F0, _F0, c)):
        if _dot(n, P) != D:
            return None
    cart = _plane_cart_str(n, D)
    steps = [
        "Intercept form of a plane: x/a + y/b + z/c = 1, "
        f"with a = {_fr_str(a)}, b = {_fr_str(b)}, "
        f"c = {_fr_str(c)}.",
        f"So the plane is {intercept_str}, i.e. {cart}.",
    ]
    return _result("w189_plane_intercepts",
                   f"{intercept_str}; {cart}", steps)


def _plane_three_points(q):
    if "plane" not in q or "equation" not in q:
        return None
    if "intercept" in q or "normal" in q:
        return None
    pts = _points3(q)
    if len(pts) != 3 or len(set(pts)) != 3:
        return None
    A, B, C = pts
    AB, AC = _sub(B, A), _sub(C, A)
    n0 = _cross(AB, AC)
    if _is_zero(n0):
        return None          # collinear points: no unique plane
    n, D = _reduce_plane_frac(n0, _dot(n0, A))
    for P in pts:
        if _dot(n, P) != D:
            return None
    return _serve_plane(n, D, "w189_plane_three_points", [
        f"AB = {_vec_str(AB)}, AC = {_vec_str(AC)}.",
        f"Normal = AB x AC = {_vec_str(n)} (reduced).",
        f"The plane through A{_pt_str(A)} with this normal:",
    ])


def _plane_point_normal(q):
    if "plane" not in q or "normal" not in q:
        return None
    if "equation" not in q:
        return None
    pts = _points3(q)
    pt = pts[0] if len(pts) == 1 else None
    if pt is None:
        mpv = re.search(r"position vector\s+(?:is\s+)?(.+?)"
                        r"(?:\s+and\b|$)", q)
        if mpv:
            pt = _vec(mpv.group(1))
    if pt is None:
        return None
    n = None
    mdr = re.search(
        r"direction ratios\s*(?:are\s*|is\s*)?"
        r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,"
        r"\s*(-?\d+(?:\.\d+)?)", q)
    if mdr and "normal" in q[:mdr.start() + 20]:
        try:
            n = tuple(_num(mdr.group(i)) for i in (1, 2, 3))
        except Exception:
            n = None
    if n is None:
        idx = q.find("normal")
        seg = q[idx + len("normal"):]
        seg = re.split(r"\b(?:passing|through)\b", seg)[0]
        # A point tuple inside the segment is not the normal.
        seg = _PT3_RE.sub(" ", seg)
        seg = seg.replace("vector", " ")
        seg = re.sub(r"^\s*(is|of|to|the|a|an)\b", " ", seg)
        seg = re.sub(r"\s*(is|of|to|the|a|an)\s*$", " ", seg)
        n = _vec(seg.strip(" :,."))
        if n is None:
            # The normal may sit before the word 'normal'
            # ("... whose normal vector is 3i + 2j - k" is
            # covered above; "2i - j + 3k is the normal" is
            # not common) — decline rather than guess.
            return None
    if n is None or _is_zero(n):
        return None
    D = _dot(n, pt)
    if _dot(n, pt) != D:
        return None
    return _serve_plane(n, D, "w189_plane_point_normal", [
        f"For a plane through {_pt_str(pt)} with normal "
        f"{_vec_str(n)}: n . (r - a) = 0, i.e. n . r = "
        f"n . a = {_fr_str(D)}.",
    ])


def _dist_point_plane(q):
    if "plane" not in q or "distance" not in q:
        return None
    if "shortest distance" in q:
        return None
    if re.search(r"\br\s*=", q):
        return None          # a line's point is not the point
    pts = _points3(q)
    if len(pts) != 1:
        return None
    planes = _find_planes_vector(q)
    if len(planes) != 1:
        planes = _find_planes_cartesian(q)
    if len(planes) != 1:
        return None
    n, D = planes[0]
    pt = pts[0]
    num = _dot(n, pt) - D
    dist = sp.simplify(abs(sp.Rational(num.numerator,
                                       num.denominator))
                       / _exact_norm(n))
    # Independent check with sympy Matrix arithmetic.
    alt = sp.simplify(abs(_sym_vec(n).dot(_sym_vec(pt))
                          - sp.Rational(D.numerator,
                                        D.denominator))
                      / sp.sqrt(_sym_vec(n).dot(_sym_vec(n))))
    if sp.simplify(dist - alt) != 0:
        return None
    steps = [
        "Distance from a point to a plane = "
        "|n . p - d| / |n|.",
        f"n = {_vec_str(n)}, d = {_fr_str(D)}, "
        f"p = {_pt_str(pt)}: |{_fr_str(num)}| / "
        f"{fmt(_exact_norm(n))}.",
        f"Distance = {_dist_str(dist)}.",
    ]
    return _result("w189_point_plane_distance",
                   _dist_str(dist), steps)


# ---------------------------------------------------------------------------
# Dispatcher + repair predicate
# ---------------------------------------------------------------------------

_SCHEMAS = (_sd, _angle_planes, _angle_lines, _dist_point_plane,
            _plane_intercepts, _plane_three_points,
            _plane_point_normal, _line_eq)


def solve_threed189(question):
    """Wave 189 3D-geometry schemas; None unless one of them
    matches the question completely and verifies its answer."""
    try:
        q = _prep(question)
    except Exception:
        return None
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


def threed189_should_displace(question, result, cand):
    """Wave 189 repair predicate (the Wave 171 pattern):
    True only for the two measured wrong serves, when this
    module's strict schema settles the same question with a
    different answer —
      * op 'angle_between_lines' (c12gaps142) on a question
        carrying two explicit 'r = ...' line equations: the
        schema paired the first line's point vector with
        its direction, so its angle is not the lines' angle.
      * op 'w115_eq_intercepts' (rekha, 2D) on a PLANE
        intercepts question: the z term was dropped.
    Every other primary answer stands untouched."""
    if not isinstance(result, dict) or not isinstance(cand, dict):
        return False
    pans = str(result.get("answer", "") or "").strip()
    cans = str(cand.get("answer", "") or "").strip()
    if not pans or not cans or pans == cans:
        return False
    try:
        q = _prep(question)
    except Exception:
        return False
    if result.get("op") == "angle_between_lines" \
            and cand.get("op") == "w189_angle_lines" \
            and len(_lines_vector(q)) == 2:
        return True
    if result.get("op") == "w115_eq_intercepts" \
            and cand.get("op") == "w189_plane_intercepts" \
            and "plane" in q and "intercept" in q:
        return True
    return False
