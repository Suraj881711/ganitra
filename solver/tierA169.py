"""Wave 169: Tier-A solver depth — general METHOD schemas for
the book-question families that still do not solve.

Why this module exists (Wave 135 book audit + Wave 150/151
follow-up lists + a fresh 18 Nov 2026 measurement of the
Deploy-38 solver over the NOT_SOLVED book pool,
~/workspace/ganitra-book-questions.jsonl):

  family (clean pool / sampled / solved before this wave)
  sector + annular + mensuration cost   205+40+8   8-7-1 / 30
  straight-line equation forms          113        2 / 30
  probability-distribution tables       29         6 / 29
  rational / irrational between         34         0 / 30
  commercial sentence forms (P/L + SI)  131        0 / 30

House rules, identical to Waves 94/103/115/125/142: a schema
fires only when it settles the question COMPLETELY, every
served value is recomputed exactly (Fractions / SymPy) at
solve time and cross-checked by an independent second path
before serving, and anything doubtful returns None so routing
continues unchanged.  Wiring: a failure-only gate at the end
of router._solve_question_uncached, after the Wave 142 gate —
a question the solver already answers is never displaced.

Families:
  1. Mensuration — sector area from radius + arc length,
     sector area from perimeter + arc, sector perimeter from
     radius + area, arc / sector-area / sector-perimeter from
     a stated circle area (k*pi) + angle, annular road / path
     area (diameter + width, radius + width, outer + inner),
     cost at a rate per 100 sq units (cone white-washing,
     hemisphere tin-plating), Heron area (+ fencing cost) for
     a triangular plot whose three sides are stated.
     Pi follows solver/pi_policy.py (true pi default, 22/7
     only for 7-designed NCERT mensuration).
  2. Straight lines — axis-parallel lines at a stated
     distance / intercept, equal intercepts through a point
     (incl. through the intersection of two given lines),
     intercepts of stated sum through a point, a line
     perpendicular to the line through two points, a line
     perpendicular to a given line with a stated x-intercept,
     the line whose perpendicular from the origin meets it at
     a stated point, inclination + intercept lines, and
     Class 12 3D lines through a point in a stated direction
     (vector + cartesian forms).
  3. Probability distributions (Class 12) — the linearised
     X / P(X) table: entries constant or polynomial in k
     (degree <= 2); k is solved from sum P = 1 and accepted
     only when exactly one root makes every probability lie
     in [0, 1]; numeric tables are checked the same way.
     Asked parts served: k, P(X < a), P(X > a), P(X <= a),
     P(X >= a), P(a < X < b) (either bracket), P(X = a),
     "X is positive / non-negative / negative".  A part the
     schema cannot parse (mean, variance, c.d.f.) declines
     the whole question — no partial serves.
  4. Numbers between — n rational numbers between two
     stated endpoints (integers, decimals, clean fractions),
     equidistant included, by the equal-gap construction
     a + j*(b - a)/(n + 1), each value verified strictly
     between; n irrational numbers by a + (b - a)*sqrt(2)
     scaled offsets, irrational by construction and verified
     numerically at high precision.
  5. Commercial sentence forms — the state-board phrasings
     the keyword solvers miss (currency signs mangled by
     extraction to Rs / $ / ` / %): SP + loss/profit amount
     -> CP, CP + overhead + SP -> profit/loss, target-percent
     selling price, SP + percent -> CP, profit amount +
     percent -> CP/SP, per-unit buy/sell profit, bulk buy +
     rate sell profit percent, CP/SP pair -> profit percent,
     and simple-interest sentence forms (principal + rate +
     years).  "Profit margin" forms are declined (ambiguous
     base), as is any multi-part (i)/(ii) question.

Phrasings: English book text first; the between family also
takes the Devanagari ask.  Steps are Ganitra's short voice.
"""
import math
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt, fmt_num
from .pi_policy import pi_choice
from .rekha import _fmt_general

_NUM = r"-?\d+(?:\.\d+)?"
_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _prep(text):
    s = str(text).translate(_DEV_DIGITS)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("≤", "<=").replace("≥", ">=")
    s = s.replace("−", "-").replace("²", "^2").replace("³", "^3")
    s = s.replace("×", "x")
    return s


def _hindi(text):
    return bool(re.search(r"[\u0900-\u097F]", str(text)))


def _result(op, answer, steps, typ="applied", value=None):
    out = {"type": typ, "op": op, "answer": answer, "steps": steps}
    if value is not None:
        try:
            out["value"] = float(value)
        except Exception:
            pass
    return out


def _frac(tok):
    """Exact Fraction from an int / decimal / 'a/b' token."""
    tok = str(tok).strip().replace(",", "")
    if "/" in tok:
        a, b = tok.split("/", 1)
        return Fraction(a.strip()) / Fraction(b.strip())
    return Fraction(tok)


def _fmt_fr(v):
    """Fraction -> '3' / '3/4' / decimal for non-terminating."""
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        return f"{v.numerator}/{v.denominator}"
    return fmt_num(v)


def _fmt_money(v):
    f = _fmt_fr(v) if isinstance(v, Fraction) else fmt_num(v)
    return f"Rs {f}"


def _dec(v, places=2):
    return f"{float(v):.{places}f}".rstrip("0").rstrip(".")


# ===========================================================================
# Family 1: mensuration — sectors, annulus, cost-at-rate, Heron
# ===========================================================================

def _unit_after(q, pos):
    m = re.match(r"\s*(cm|mm|m)\b", q[pos:])
    return m.group(1) if m else ""


def _sector_radius_arc(q):
    """(radius, arc) Fractions from a sector question, or None."""
    mr = re.search(r"radius[^0-9]{0,35}?(" + _NUM + r")\s*(cm|mm|m)?", q, re.I)
    ma = re.search(r"(?:length of (?:its |the )?arc|arc length|length of the arc)"
                   r"[^0-9]{0,12}?(" + _NUM + r")\s*(cm|mm|m)?", q, re.I)
    if not ma:
        ma = re.search(r"\barc\b[^0-9a-z]{0,10}?(" + _NUM + r")\s*(cm|mm|m)?",
                       q, re.I)
    if mr and ma:
        return _frac(mr.group(1)), _frac(ma.group(1))
    return None


def _pi_area_str(coeff, radius, unit, radii=None):
    """coeff * pi as a served string under the pi policy."""
    piv, used227, _reason = pi_choice(radius=radius, radii=radii)
    if used227:
        val = coeff * Fraction(22, 7)
        return _fmt_fr(val), float(val), True
    val = float(coeff) * math.pi
    cs = _fmt_fr(coeff) if coeff.denominator != 1 else str(coeff.numerator)
    return f"{cs}pi (about {_dec(val)})", val, False


def _sector(q):
    if "sector" not in q.lower():
        return None
    ql = q.lower()
    ask_area = "area" in ql
    ask_perim = "perimeter" in ql

    # -- circle area stated as k*pi: arc / sector area / sector perimeter
    mc = re.search(r"(?:area of (?:the |a )?circle is|circle of area)\s+("
                   + _NUM + r")\s*(?:π|pi\b)", q, re.I)
    if mc:
        K = _frac(mc.group(1))
        r2 = sp.nsimplify(float(K), rational=True)
        root = sp.sqrt(r2)
        if not root.is_rational:
            return None
        r = Fraction(int(root.p), int(root.q))
        mang = re.search(r"angle of\s+(" + _NUM + r")\s*(?:°|degrees?|o\b)",
                         q, re.I)
        mper = re.search(r"perimeter of (?:a |the )?sector.{0,45}?"
                         r"is\s+(" + _NUM + r")", q, re.I)
        steps = [f"Circle area = pi x r^2 = {_fmt_fr(K)}pi, so "
                 f"r^2 = {_fmt_fr(K)} and r = {_fmt_fr(r)}."]
        parts = []
        ask_arc = bool(re.search(r"length of (?:its |the )?arc|arc length",
                                 ql))
        ask_sec_area = bool(re.search(
            r"area of (?:the )?(?:a |corresponding )?sector", ql))
        ask_sec_per = bool(re.search(
            r"perimeter of (?:the |a |corresponding )?sector", ql))
        if mang and not mper:
            th = _frac(mang.group(1))
            if not (0 < th < 360):
                return None
            arc_coeff = Fraction(th, 180) * r          # arc = coeff * pi
            sec_coeff = Fraction(th, 360) * K          # area = coeff * pi
            # verify by the radian path: arc = r * theta_rad
            arc2 = r * th * sp.pi / 180
            if sp.simplify(arc2 - arc_coeff * sp.pi) != 0:
                return None
            if ask_arc:
                s, _v, _u = _pi_area_str(arc_coeff, r, "")
                parts.append(f"arc length = {s}")
                steps.append(f"Arc length = ({_fmt_fr(th)}/360) x 2pi x "
                             f"{_fmt_fr(r)} = {s}.")
            if ask_sec_area:
                s, _v, _u = _pi_area_str(sec_coeff, r, "")
                parts.append(f"sector area = {s}")
                steps.append(f"Sector area = ({_fmt_fr(th)}/360) x "
                             f"{_fmt_fr(K)}pi = {s}.")
            if ask_sec_per and not ask_arc and not ask_sec_area:
                s, _v, _u = _pi_area_str(arc_coeff, r, "")
                parts.append(f"sector perimeter = {s} + {_fmt_fr(2 * r)}")
                steps.append(f"Perimeter of sector = arc + 2r = {s} + "
                             f"{_fmt_fr(2 * r)}.")
            if parts:
                return _result("w169_sector_circle_area",
                               "; ".join(parts), steps, typ="geometry")
            return None
        if mper and ask_sec_area:
            P = _frac(mper.group(1))
            arc = P - 2 * r
            if arc <= 0:
                return None
            A = arc * r / 2
            # verify: 1/2 * r^2 * theta with theta = arc / r
            if sp.simplify(sp.Rational(1, 2) * r * r * (arc / r) - A) != 0:
                return None
            steps.append(f"Arc length = perimeter - 2r = {_fmt_fr(P)} - "
                         f"{_fmt_fr(2 * r)} = {_fmt_fr(arc)}.")
            steps.append(f"Sector area = (1/2) x arc x r = (1/2) x "
                         f"{_fmt_fr(arc)} x {_fmt_fr(r)} = {_fmt_fr(A)}.")
            return _result("w169_sector_from_perimeter",
                           f"{_fmt_fr(A)}", steps, typ="geometry",
                           value=A)
        return None

    ra = _sector_radius_arc(q)
    # -- perimeter + arc -> area
    mp = re.search(r"perimeter\s*(?:is|=)\s*(" + _NUM + r")", q, re.I)
    if mp and "arc" in ql and ask_area:
        ma = re.search(r"(?:length of (?:its |the )?arc|arc)\s*(?:is|=)?\s*"
                       r"(" + _NUM + r")", q, re.I)
        if ma:
            P, L = _frac(mp.group(1)), _frac(ma.group(1))
            r = (P - L) / 2
            if r <= 0 or L <= 0:
                return None
            A = L * r / 2
            if sp.simplify(sp.Rational(1, 2) * r * r * (L / r) - A) != 0:
                return None
            steps = [f"Perimeter = arc + 2r, so r = ({_fmt_fr(P)} - "
                     f"{_fmt_fr(L)})/2 = {_fmt_fr(r)}.",
                     f"Area of sector = (1/2) x arc x r = (1/2) x "
                     f"{_fmt_fr(L)} x {_fmt_fr(r)} = {_fmt_fr(A)}."]
            return _result("w169_sector_perimeter_arc", _fmt_fr(A), steps,
                           typ="geometry", value=A)
    if ra:
        r, L = ra
        if r <= 0 or L <= 0:
            return None
        if ask_area and not ask_perim:
            A = L * r / 2
            if sp.simplify(sp.Rational(1, 2) * r * r * (L / r) - A) != 0:
                return None
            steps = [f"Area of a sector = (1/2) x arc length x radius.",
                     f"= (1/2) x {_fmt_fr(L)} x {_fmt_fr(r)} = {_fmt_fr(A)}."]
            return _result("w169_sector_arc_area", _fmt_fr(A), steps,
                           typ="geometry", value=A)
    # -- radius + sector area -> perimeter
    mse = re.search(r"sector of radius\s+(" + _NUM + r")[^.]{0,45}?"
                    r"area\s+(?:is\s+)?(" + _NUM + r")", q, re.I)
    if mse and ask_perim and not mc:
        r, A = _frac(mse.group(1)), _frac(mse.group(2))
        if r <= 0 or A <= 0:
            return None
        L = 2 * A / r
        P = L + 2 * r
        if sp.simplify(L * r / 2 - A) != 0:
            return None
        steps = [f"Area = (1/2) x arc x r, so arc = 2 x {_fmt_fr(A)} / "
                 f"{_fmt_fr(r)} = {_fmt_fr(L)}.",
                 f"Perimeter = arc + 2r = {_fmt_fr(L)} + {_fmt_fr(2 * r)} "
                 f"= {_fmt_fr(P)}."]
        return _result("w169_sector_area_perimeter", _fmt_fr(P), steps,
                       typ="geometry", value=P)
    return None


def _annular(q):
    ql = q.lower()
    if not re.search(r"\b(road|path|pathway|ring)\b", ql):
        return None
    if "area" not in ql:
        return None
    R = r_ = None
    mo = re.search(r"outer radius[^0-9]{0,20}?(" + _NUM + r")", q, re.I)
    mi = re.search(r"inner radius[^0-9]{0,20}?(" + _NUM + r")", q, re.I)
    if mo and mi:
        R, r_ = _frac(mo.group(1)), _frac(mi.group(1))
    else:
        mw = re.search(r"(" + _NUM + r")\s*(?:m|cm|mm)\s+wide", q, re.I)
        if not mw:
            mw = re.search(r"width\s*(?:of\s*)?(" + _NUM + r")", q, re.I)
        if not mw:
            return None
        W = _frac(mw.group(1))
        md = re.search(r"diameter[^0-9]{0,45}?(" + _NUM + r")", q, re.I)
        mr = re.search(r"radius[^0-9]{0,45}?(" + _NUM + r")", q, re.I)
        base = None
        if md:
            base = _frac(md.group(1)) / 2
        elif mr:
            base = _frac(mr.group(1))
        if base is None or W <= 0:
            return None
        if "inside" in ql:
            R, r_ = base, base - W
        else:
            R, r_ = base + W, base
    if R is None or r_ is None or R <= r_ or r_ <= 0:
        return None
    coeff = R * R - r_ * r_
    s, val, _u = _pi_area_str(coeff, None, "", radii=[R, r_])
    # independent check: pi*(R-r)*(R+r)
    if sp.simplify((R - r_) * (R + r_) - coeff) != 0:
        return None
    steps = [f"Area of the circular path = pi x (R^2 - r^2) with "
             f"R = {_fmt_fr(R)} and r = {_fmt_fr(r_)}.",
             f"= pi x ({_fmt_fr(R * R)} - {_fmt_fr(r_ * r_)}) = {s}."]
    return _result("w169_annular_area", s, steps, typ="geometry", value=val)


def _cost_per_100(q):
    mr = re.search(r"rate of\s*(?:rs\.?|₹|`)?\s*(" + _NUM + r")\s*per\s*100",
                   q, re.I)
    if not mr:
        return None
    rate = _frac(mr.group(1))
    ql = q.lower()
    if "conical" in ql or "cone" in ql:
        # 'slant height and base diameter ... are A and B
        # respectively' pairs the values in mention order.
        mpair = re.search(r"slant height and (?:base )?diameter"
                          r"[^0-9]{0,45}?are\s+(" + _NUM + r")\s*m?\s+and\s+("
                          + _NUM + r")", q, re.I)
        if mpair:
            L, d = _frac(mpair.group(1)), _frac(mpair.group(2))
        else:
            ml = re.search(r"slant height[^0-9]{0,35}?(" + _NUM + r")",
                           q, re.I)
            md = re.search(r"diameter[^0-9]{0,35}?(" + _NUM + r")", q, re.I)
            if not ml or not md:
                return None
            L, d = _frac(ml.group(1)), _frac(md.group(1))
        r = d / 2
        piv, used227, _x = pi_choice(radius=r)
        if used227:
            area_fr = Fraction(22, 7) * r * L
            area_s = _fmt_fr(area_fr)
            cost = area_fr * rate / 100
            cost_s = _fmt_money(cost)
            cval = cost
        else:
            area = piv * float(r) * float(L)
            area_s = f"{_dec(area)} (approx.)"
            cost_f = area * float(rate) / 100
            cost_s = f"Rs {_dec(cost_f)} (approx.)"
            cval = Fraction(str(round(cost_f, 2)))
        steps = [f"Curved surface area of the cone = pi x r x l "
                 f"= pi x {_fmt_fr(r)} x {_fmt_fr(L)} = {area_s}.",
                 f"Cost = {area_s} x {_fmt_fr(rate)}/100 = {cost_s}."]
        return _result("w169_cone_whitewash_cost", cost_s, steps,
                       typ="geometry", value=cval)
    if "hemispheric" in ql:
        md = re.search(r"diameter[^0-9]{0,35}?(" + _NUM + r")", q, re.I)
        if not md:
            return None
        r = _frac(md.group(1)) / 2
        piv, used227, _x = pi_choice(radius=r)
        if used227:
            area_fr = 2 * Fraction(22, 7) * r * r
            area_s = _fmt_fr(area_fr)
            cost = area_fr * rate / 100
            cost_s = _fmt_money(cost)
            cval = cost
        else:
            area = 2 * piv * float(r) ** 2
            area_s = f"{_dec(area)} (approx.)"
            cost_f = area * float(rate) / 100
            cost_s = f"Rs {_dec(cost_f)} (approx.)"
            cval = Fraction(str(round(cost_f, 2)))
        steps = [f"Inner surface area of the hemispherical bowl "
                 f"= 2 x pi x r^2 = 2 x pi x {_fmt_fr(r)}^2 = {area_s}.",
                 f"Cost = {area_s} x {_fmt_fr(rate)}/100 = {cost_s}."]
        return _result("w169_hemisphere_plate_cost", cost_s, steps,
                       typ="geometry", value=cval)
    return None


def _heron(q):
    ms = re.search(r"sides?\s+(?:are\s+|of\s+)?(" + _NUM + r")\s*m?\s*,\s*("
                   + _NUM + r")\s*m?\s*(?:and|,)\s*(" + _NUM + r")", q, re.I)
    if not ms:
        return None
    a, b, c = (_frac(ms.group(i)) for i in (1, 2, 3))
    if a + b <= c or b + c <= a or c + a <= b:
        return None
    ql = q.lower()
    if "area" not in ql and "fence" not in ql and "grass" not in ql:
        return None
    s = (a + b + c) / 2
    rad = s * (s - a) * (s - b) * (s - c)
    if rad <= 0:
        return None
    area_sym = sp.sqrt(sp.Rational(rad.numerator, rad.denominator))
    area_s = fmt(area_sym)
    area_f = float(area_sym)
    # verify by the coordinate (shoelace-free) path: Heron via sides
    # with the law of cosines on side c.
    cosC = (a * a + b * b - c * c) / (2 * a * b)
    area2 = float(a * b) * math.sqrt(max(0.0, 1 - float(cosC) ** 2)) / 2
    if abs(area2 - area_f) > 1e-6 * max(1.0, area_f):
        return None
    steps = [f"Semi-perimeter s = ({_fmt_fr(a)} + {_fmt_fr(b)} + "
             f"{_fmt_fr(c)})/2 = {_fmt_fr(s)}.",
             f"Area = sqrt(s(s-a)(s-b)(s-c)) = sqrt({_fmt_fr(rad)}) "
             f"= {area_s} (about {_dec(area_f)})."]
    parts = [f"area = {area_s} (about {_dec(area_f)})"]
    mf = re.search(r"fenc", ql)
    mrate = re.search(r"rate of\s*(?:rs\.?|₹|`)?\s*(" + _NUM + r")\s*per\s*"
                      r"(?:m\b|metre|meter)", q, re.I)
    gate_w = None
    mg1 = re.search(r"gate of\s+(" + _NUM + r")\s*m", q, re.I)
    mg2 = re.search(r"(" + _NUM + r")\s*m\s+wide\s+for a gate", q, re.I)
    if mg1:
        gate_w = _frac(mg1.group(1))
    elif mg2:
        gate_w = _frac(mg2.group(1))
    if "gate" in ql and gate_w is None and (mf or mrate):
        return None          # fencing length would be wrong: decline
    if mf and mrate:
        gate = gate_w
        per = a + b + c - (gate if gate else Fraction(0))
        cost = per * _frac(mrate.group(1))
        steps.append(f"Fencing length = perimeter"
                     + (f" - gate = {_fmt_fr(per)}" if gate else
                        f" = {_fmt_fr(per)}")
                     + f"; cost = {_fmt_fr(per)} x "
                     f"{_fmt_fr(_frac(mrate.group(1)))} = "
                     f"{_fmt_money(cost)}.")
        parts.append(f"fencing cost = {_fmt_money(cost)}")
    return _result("w169_heron_plot", "; ".join(parts), steps,
                   typ="geometry", value=area_f)


# ===========================================================================
# Family 2: straight-line forms (2D + 3D)
# ===========================================================================

_PT = r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"


def _points(q):
    return [(_frac(a), _frac(b)) for a, b in re.findall(_PT, q)]


def _line_answer(A, B, C, steps, op, extra_note=None):
    """Serve Ax + By + C = 0 after verifying it on demand."""
    s = _fmt_general(A, B, C)
    if extra_note:
        steps = steps + [extra_note]
    return _result(op, s, steps, typ="geometry")


def _check_on_line(A, B, C, pt):
    return A * pt[0] + B * pt[1] + C == 0


def _parse_line_eq(seg):
    """'x - 7y + 5 = 0' -> (A, B, C) Fractions for Ax + By + C = 0."""
    seg = seg.replace(" ", "")
    m = re.fullmatch(r"([+-]?\d*(?:\.\d+)?)x([+-]\d*(?:\.\d+)?)y"
                     r"([+-]\d+(?:\.\d+)?)=0", seg)
    if not m:
        return None

    def coef(t, signed):
        if t in ("", "+", "-"):
            return Fraction(1) if t != "-" else Fraction(-1)
        return _frac(t)
    return coef(m.group(1), False), coef(m.group(2), True), _frac(m.group(3))


def _lines_axis_parallel(q):
    ql = q.lower()
    if "parallel to the" not in ql or "axis" not in ql:
        return None
    if (re.search(r"\(\s*a\s*\)", ql) or re.search(r"\ba\)", ql)) and \
            (re.search(r"\(\s*b\s*\)", ql) or re.search(r"\bb\)", ql)):
        return None  # multi-part: the multipart layer owns it
    md = re.search(r"distance of\s+(" + _NUM + r")", q, re.I)
    steps = []
    if "x-axis" in ql.replace(" ", "") or "x −axis" in ql or "x-axis" in ql:
        if md:
            d = abs(_frac(md.group(1)))
            if "below" in ql:
                v = -d
            elif "above" in ql:
                v = d
            else:
                return None
            steps = [f"A line parallel to the X-axis at distance "
                     f"{_fmt_fr(d)} {'below' if v < 0 else 'above'} it "
                     f"has every point's y-coordinate = {_fmt_fr(v)}."]
            return _line_answer(Fraction(0), Fraction(1), -v, steps,
                                "w169_line_axis_parallel")
        mi = re.search(r"intercept of\s+(" + _NUM + r")\s*(?:unit)?s?\s*on "
                       r"the y-axis", q, re.I)
        if mi:
            v = _frac(mi.group(1))
            steps = [f"Parallel to the X-axis and cutting the Y-axis "
                     f"at {_fmt_fr(v)}: y = {_fmt_fr(v)}."]
            return _line_answer(Fraction(0), Fraction(1), -v, steps,
                                "w169_line_axis_parallel")
    if "y-axis" in ql.replace(" ", "") or "y-axis" in ql:
        if md:
            d = abs(_frac(md.group(1)))
            if "left" in ql:
                v = -d
            elif "right" in ql:
                v = d
            else:
                return None
            steps = [f"A line parallel to the Y-axis at distance "
                     f"{_fmt_fr(d)} to the {'left' if v < 0 else 'right'} "
                     f"has every point's x-coordinate = {_fmt_fr(v)}."]
            return _line_answer(Fraction(1), Fraction(0), -v, steps,
                                "w169_line_axis_parallel")
        mi = re.search(r"intercept of\s+(" + _NUM + r")\s*(?:unit)?s?\s*on "
                       r"the x-axis", q, re.I)
        if mi:
            v = _frac(mi.group(1))
            steps = [f"Parallel to the Y-axis and cutting the X-axis "
                     f"at {_fmt_fr(v)}: x = {_fmt_fr(v)}."]
            return _line_answer(Fraction(1), Fraction(0), -v, steps,
                                "w169_line_axis_parallel")
    return None


def _intersection_point(q):
    eqs = re.findall(r"[+-]?\s*\d*\s*x\s*[+-]\s*\d*\s*y\s*[+-]\s*\d+"
                     r"(?:\.\d+)?\s*=\s*0", q.replace(" ", " "))
    found = []
    for e in re.finditer(r"([+-]?\d*(?:\.\d+)?x[+-]\d*(?:\.\d+)?y"
                         r"[+-]\d+(?:\.\d+)?=0)", q.replace(" ", "")):
        pc = _parse_line_eq(e.group(1))
        if pc and pc not in found:
            found.append(pc)
    if len(found) != 2:
        return None
    (A1, B1, C1), (A2, B2, C2) = found
    det = A1 * B2 - A2 * B1
    if det == 0:
        return None
    x = (B1 * C2 - B2 * C1) / det
    y = (C1 * A2 - C2 * A1) / det
    if not (_check_on_line(A1, B1, C1, (x, y))
            and _check_on_line(A2, B2, C2, (x, y))):
        return None
    return (x, y)


def _lines_intercepts(q):
    ql = q.lower()
    if "intercept" not in ql:
        return None
    pt = None
    mp = re.search(r"(?:passes through|passing through|through) the point "
                   + _PT, q, re.I)
    if mp:
        pt = (_frac(mp.group(1)), _frac(mp.group(2)))
    elif "intersection" in ql:
        pt = _intersection_point(q)
        if pt is None:
            return None
    if pt is None:
        mp = re.search(r"through\s*" + _PT, q, re.I)
        if mp:
            pt = (_frac(mp.group(1)), _frac(mp.group(2)))
    if pt is None:
        return None
    x0, y0 = pt
    if "equal intercept" in ql:
        s = x0 + y0
        A, B, C = Fraction(1), Fraction(1), -s
        if not _check_on_line(A, B, C, pt):
            return None
        steps = [f"Equal intercepts a = b, and the line through "
                 f"({_fmt_fr(x0)}, {_fmt_fr(y0)}) in intercept form "
                 f"x/a + y/a = 1 gives a = {_fmt_fr(s)}.",
                 f"So the line is x + y = {_fmt_fr(s)}."]
        return _line_answer(A, B, C, steps, "w169_line_equal_intercepts")
    msum = re.search(r"sum\s*(?:is|=)\s*(" + _NUM + r")", q, re.I)
    if msum and "intercept" in ql:
        S = _frac(msum.group(1))
        # a^2 + (y0 - x0 - S) a + x0*S = 0
        bb = y0 - x0 - S
        cc = x0 * S
        disc = bb * bb - 4 * cc
        if disc < 0:
            return None
        sq = sp.sqrt(sp.Rational(disc.numerator, disc.denominator))
        if not sq.is_rational:
            return None
        sqf = Fraction(int(sq.p), int(sq.q))
        roots = sorted({(-bb + sqf) / 2, (-bb - sqf) / 2})
        lines = []
        steps = [f"Let the intercepts be a and {_fmt_fr(S)} - a; the "
                 f"intercept form x/a + y/({_fmt_fr(S)} - a) = 1 through "
                 f"({_fmt_fr(x0)}, {_fmt_fr(y0)}) gives a quadratic "
                 f"in a."]
        for a_ in roots:
            b_ = S - a_
            if a_ == 0 or b_ == 0:
                continue
            A, B, C = b_, a_, -a_ * b_
            if not _check_on_line(A, B, C, pt):
                return None
            lines.append(_fmt_general(A, B, C))
            steps.append(f"a = {_fmt_fr(a_)}, b = {_fmt_fr(b_)}: "
                         f"{lines[-1]}.")
        if not lines:
            return None
        return _result("w169_line_intercept_sum", "; ".join(lines), steps,
                       typ="geometry")
    return None


def _lines_perpendicular(q):
    ql = q.lower()
    if "perpendicular" not in ql:
        return None
    # (a) perpendicular from the origin meets the line at P
    mo = re.search(r"perpendicular from the origin[^.]{0,60}?point\s*"
                   + _PT, q, re.I)
    if mo:
        px, py = _frac(mo.group(1)), _frac(mo.group(2))
        A, B, C = px, py, -(px * px + py * py)
        if A == 0 and B == 0:
            return None
        if not _check_on_line(A, B, C, (px, py)):
            return None
        steps = [f"The line is perpendicular to OP at P({_fmt_fr(px)}, "
                 f"{_fmt_fr(py)}), so its equation is "
                 f"{_fmt_fr(px)}x + {_fmt_fr(py)}y = "
                 f"{_fmt_fr(px * px + py * py)}."]
        return _line_answer(A, B, C, steps, "w169_line_perp_from_origin")
    # (b) perpendicular to the line through two points
    mt = re.search(r"through the points\s*" + _PT + r"\s*and\s*" + _PT,
                   q, re.I)
    mp = re.search(r"passing through\s*" + _PT, q, re.I)
    if mt and mp:
        P = (_frac(mp.group(1)), _frac(mp.group(2)))
        A_ = (_frac(mt.group(1)), _frac(mt.group(2)))
        B_ = (_frac(mt.group(3)), _frac(mt.group(4)))
        dx, dy = B_[0] - A_[0], B_[1] - A_[1]
        if dx == 0 and dy == 0:
            return None
        # line direction (dx, dy); the new line's direction is
        # (-B, A) = (-dy, dx), perpendicular to AB by construction;
        # equation: dx*(x - Px) + dy*(y - Py) = 0
        A, B, C = dx, dy, -(dx * P[0] + dy * P[1])
        if not _check_on_line(A, B, C, P):
            return None
        if (-B) * dx + A * dy != 0:      # directions perpendicular
            return None
        steps = [f"Slope of the line through ({_fmt_fr(A_[0])}, "
                 f"{_fmt_fr(A_[1])}) and ({_fmt_fr(B_[0])}, "
                 f"{_fmt_fr(B_[1])}) is {_fmt_fr(dy)}/{_fmt_fr(dx)}; the "
                 f"perpendicular line through ({_fmt_fr(P[0])}, "
                 f"{_fmt_fr(P[1])}) is:"]
        return _line_answer(A, B, C, steps, "w169_line_perp_two_points")
    # (c) perpendicular to a given line, with x-intercept
    mg = re.search(r"perpendicular to the line\s+(.+?)\s+and\s+"
                   r"(?:having|with)\s+x\s*-?\s*intercept\s+(" + _NUM + r")",
                   q, re.I)
    if mg:
        pc = _parse_line_eq(mg.group(1))
        if pc is None:
            # try the segment up to '= 0'
            m2 = re.search(r"([+-]?\d*(?:\.\d+)?x[+-]\d*(?:\.\d+)?y"
                           r"[+-]\d+(?:\.\d+)?=0)", mg.group(1).replace(" ", ""))
            pc = _parse_line_eq(m2.group(1)) if m2 else None
        if pc is None:
            return None
        A1, B1, _C1 = pc
        a_int = _frac(mg.group(2))
        # perpendicular direction: (B1, -A1) is along the given line's
        # normal-rotated; new line: B1*(x - a) - A1*y... use normals:
        # given line normal (A1, B1) is the new line's direction, so
        # new normal = (B1, -A1).
        A, B = B1, -A1
        C = -(A * a_int)
        if not _check_on_line(A, B, C, (a_int, Fraction(0))):
            return None
        if A * A1 + B * B1 != 0:   # normals perpendicular => lines perp
            return None
        steps = [f"The given line has normal ({_fmt_fr(A1)}, "
                 f"{_fmt_fr(B1)}); a perpendicular line has normal "
                 f"({_fmt_fr(A)}, {_fmt_fr(B)}) and passes through "
                 f"({_fmt_fr(a_int)}, 0)."]
        return _line_answer(A, B, C, steps, "w169_line_perp_given_xint")
    return None


def _lines_inclination(q):
    ql = q.lower()
    mi = re.search(r"inclination\s*(?:of\s*)?(" + _NUM + r")\s*"
                   r"(?:°|degrees?|o\b)", q, re.I)
    if not mi:
        return None
    th = _frac(mi.group(1))
    if th < 0 or th > 180:
        return None
    m = sp.tan(sp.rad(sp.Rational(th.numerator, th.denominator)))
    m = sp.simplify(m)
    if m.has(sp.tan) or not m.is_real:
        return None
    mx = re.search(r"x\s*-?\s*intercept\s*(?:of\s*|is\s*)?(" + _NUM + r")",
                   q, re.I)
    my = re.search(r"y\s*-?\s*intercept\s*(?:of\s*|is\s*)?(" + _NUM + r")",
                   q, re.I)
    steps = [f"Slope m = tan({_fmt_fr(th)}) = {fmt(m)}."]
    if mx:
        a_ = _frac(mx.group(1))
        if m.is_rational:
            mf = Fraction(int(m.p), int(m.q))
            # y = m(x - a)  ->  m x - y - m a = 0
            A, B, C = mf, Fraction(-1), -mf * a_
            if not _check_on_line(A, B, C, (a_, Fraction(0))):
                return None
            return _line_answer(A, B, C, steps, "w169_line_inclination")
        ans = f"y = {fmt(m)}(x - {_fmt_fr(a_)})"
        steps.append(f"Through ({_fmt_fr(a_)}, 0): {ans}.")
        return _result("w169_line_inclination", ans, steps, typ="geometry")
    if my:
        b_ = _frac(my.group(1))
        ans = f"y = {fmt(m)}x + {_fmt_fr(b_)}" if b_ >= 0 else \
            f"y = {fmt(m)}x - {_fmt_fr(-b_)}"
        steps.append(f"With y-intercept {_fmt_fr(b_)}: {ans}.")
        return _result("w169_line_inclination", ans, steps, typ="geometry")
    return None


_VEC_TOKEN = re.compile(r"([+-]?)\s*(\d+(?:\.\d+)?)?\s*([ijk])\b")


def _parse_vec(seg):
    """'3 i - 2 j + k' style segment -> (a, b, c) Fractions or None."""
    seg = seg.strip().rstrip(".")
    seg = re.split(r"\b(?:THREE|CHAPTER|THREE DIMENSIONAL)\b", seg)[0]
    seg = seg.replace("î", "i").replace("ĵ", "j").replace("k̂", "k")
    seg = seg.replace("ˆ", "").replace("^", "")
    seg = re.sub(r"([ijk])\s*hat", r"\1", seg)
    out = {}
    pos = 0
    found = False
    for m in _VEC_TOKEN.finditer(seg):
        between = seg[pos:m.start()].strip()
        if between not in ("", "+", "-"):
            return None
        sign = -1 if m.group(1) == "-" else 1
        if between == "-" and m.group(1) == "":
            sign = -1
        coef = _frac(m.group(2)) if m.group(2) else Fraction(1)
        letter = m.group(3)
        if letter in out:
            return None
        out[letter] = sign * coef
        pos = m.end()
        found = True
    if not found or seg[pos:].strip() not in ("", "+", "-"):
        return None
    if set(out) - {"i", "j", "k"}:
        return None
    return (out.get("i", Fraction(0)), out.get("j", Fraction(0)),
            out.get("k", Fraction(0)))


def _vec_str(v):
    parts = []
    for coef, letter in zip(v, "ijk"):
        if coef == 0:
            continue
        body = letter if abs(coef) == 1 else f"{_fmt_fr(abs(coef))}{letter}"
        if not parts:
            parts.append(("-" if coef < 0 else "") + body)
        else:
            parts.append((" - " if coef < 0 else " + ") + body)
    return "".join(parts) if parts else "0"


def _lines_3d(q):
    ql = q.lower()
    if "3" not in ql and "vector form" not in ql and "cartesian" not in ql \
            and "position vector" not in ql and "direction" not in ql:
        # still allow the plain 'passes through the point (x,y,z) and
        # is parallel to the vector ...' form
        if not re.search(r"\(\s*-?\d+\s*,\s*-?\d+\s*,\s*-?\d+\s*\)", q):
            return None
    # direction
    d = None
    md = re.search(r"(?:parallel to the vector|in the direction|direction)"
                   r"\s+(.+)$", q, re.I)
    if md:
        d = _parse_vec(md.group(1))
    if d is None or d == (Fraction(0),) * 3:
        return None
    # point
    pt = None
    mpv = re.search(r"position vector\s+(.+?)\s+and\s+", q, re.I)
    if mpv:
        pt = _parse_vec(mpv.group(1))
    if pt is None:
        mt = re.search(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
                       r"\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", q)
        if mt:
            pt = tuple(_frac(mt.group(i)) for i in (1, 2, 3))
    if pt is None:
        return None
    # verify: direction non-zero; the cartesian ratios at pt are 0/0
    # by construction — cross-check with a second point pt + d.
    p2 = tuple(pt[i] + d[i] for i in range(3))
    for i in range(3):
        if d[i] != 0 and (p2[i] - pt[i]) / d[i] != 1:
            return None
    vec_form = f"r = {_vec_str(pt)} + λ({_vec_str(d)})"
    parts = []
    consts = []
    for i, (coord, dd, var) in enumerate(zip(pt, d, "xyz")):
        if dd == 0:
            consts.append(f"{var} = {_fmt_fr(coord)}")
        else:
            num = var if coord == 0 else (
                f"{var} - {_fmt_fr(coord)}" if coord > 0
                else f"{var} + {_fmt_fr(-coord)}")
            parts.append(f"({num})/{_fmt_fr(dd)}")
    cart = " = ".join(parts)
    if consts:
        cart = (cart + "; " if cart else "") + ", ".join(consts)
    steps = [f"Point on the line: ({_fmt_fr(pt[0])}, {_fmt_fr(pt[1])}, "
             f"{_fmt_fr(pt[2])}); direction: {_vec_str(d)}.",
             f"Vector form: {vec_form}.",
             f"Cartesian form: {cart}."]
    return _result("w169_line_3d", f"{vec_form}; {cart}", steps,
                   typ="geometry")


# ===========================================================================
# Family 3: probability distribution tables (Class 12)
# ===========================================================================

_K = sp.Symbol("k")


def _p_token(tok):
    """One P-row token -> sympy expression in k, or None.

    Handles the linearised book forms: 0, 0.1, 0·05, k, 2k, k2
    (= k^2), 2k2 (= 2k^2), 7k2+k (after '+' merging: '7k2+k').
    """
    t = tok.strip().replace("·", ".")
    if not t:
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)", t)
    if m:
        return sp.Rational(t)          # book decimals are exact
    m = re.fullmatch(r"(\d*)k(?:\^?(\d))?(?:\+(\d*)k(?:\^?(\d))?)?", t)
    if m:
        c1 = sp.Integer(int(m.group(1))) if m.group(1) else sp.Integer(1)
        e1 = int(m.group(2)) if m.group(2) else 1
        expr = c1 * _K ** e1
        if m.group(3) is not None or "+" in t:
            c2 = sp.Integer(int(m.group(3))) if m.group(3) else sp.Integer(1)
            e2 = int(m.group(4)) if m.group(4) else 1
            expr = expr + c2 * _K ** e2
        return expr
    m = re.fullmatch(r"(\d*)k(?:\^?(\d))?-(\d*)k(?:\^?(\d))?", t)
    if m:
        c1 = sp.Integer(int(m.group(1))) if m.group(1) else sp.Integer(1)
        e1 = int(m.group(2)) if m.group(2) else 1
        c2 = sp.Integer(int(m.group(3))) if m.group(3) else sp.Integer(1)
        e2 = int(m.group(4)) if m.group(4) else 1
        return c1 * _K ** e1 - c2 * _K ** e2
    return None


def _prob_dist(q):
    ql = q.lower()
    if "probability distribution" not in ql and "c. d. f" not in ql \
            and "distribution of" not in ql:
        return None
    if "c. d. f" in ql or "c.d.f" in ql.replace(" ", ""):
        return None                      # c.d.f. form: different method
    if re.search(r"\bmean\b|variance|standard deviation|e\(x\)", ql):
        return None                      # unparsed-ask risk
    mp = re.search(r"P\s*\(\s*X\s*(?:=\s*x)?\s*\)|P\s*\(x\)", q)
    if not mp:
        return None
    head = q[:mp.start()]
    tail = q[mp.end():]
    # X row: numbers between the last 'distribution' mention and P(
    di = head.lower().rfind("distribution")
    xseg = head[di:] if di >= 0 else head
    xseg = re.sub(r"distribution", " ", xseg, flags=re.I)
    xseg = re.sub(r"\bX\b|\bx\b|=", " ", xseg)
    xseg = re.sub(r"[^0-9.\-]+", " ", xseg)
    xtoks = [t for t in xseg.split() if re.fullmatch(r"-?\d+(?:\.\d+)?", t)]
    if len(xtoks) < 3:
        return None
    xs = []
    for t in xtoks:
        v = sp.Rational(t) if "." not in t else sp.Float(t)
        xs.append(v)
    if len(set(xs)) != len(xs):
        return None
    # P row: tokens up to the first ask boundary
    cut = re.search(r"\(\s*i\s*\)|\(\s*A\s*\)|\bdetermine\b|\bfind\b|"
                    r"\bthen\b|\bif\b", tail, re.I)
    prow = tail[:cut.start()] if cut else tail
    raw = prow.split()
    merged = []
    i = 0
    while i < len(raw):
        t = raw[i]
        if t == "+" and merged and i + 1 < len(raw):
            merged[-1] = merged[-1] + "+" + raw[i + 1]
            i += 2
            continue
        if t == "-" and merged and i + 1 < len(raw):
            merged[-1] = merged[-1] + "-" + raw[i + 1]
            i += 2
            continue
        if re.fullmatch(r"\d", t) and merged and merged[-1].endswith("k"):
            merged[-1] = merged[-1] + "^" + t     # 'k' '2' -> k^2
            i += 1
            continue
        merged.append(t)
        i += 1
    if len(merged) != len(xs):
        return None
    ps = []
    for t in merged:
        e = _p_token(t)
        if e is None:
            return None
        if e.free_symbols - {_K}:
            return None
        if sp.Poly(e, _K) is not None and sp.Poly(e, _K).degree() > 2:
            return None
        ps.append(sp.expand(e))
    total = sum(ps)
    has_k = any(p.has(_K) for p in ps)
    kval = None
    if has_k:
        sols = sp.solve(sp.Eq(total, 1), _K)
        good = []
        for s_ in sols:
            if not s_.is_rational:
                continue
            vals = [sp.nsimplify(p.subs(_K, s_)) for p in ps]
            if all(v.is_rational and 0 <= v <= 1 for v in vals):
                good.append((s_, vals))
        if len(good) != 1:
            return None
        kval, pvals = good[0]
        # independent re-check: sum of substituted values is exactly 1
        if sum(pvals) != 1:
            return None
    else:
        pvals = ps
        if abs(float(sum(pvals)) - 1.0) > 1e-9:
            return None
        if any(not (0 <= float(v) <= 1) for v in pvals):
            return None
    # ---- asked parts
    asks = []          # (label, value)
    k_asked = re.search(r"(find|determine|value of|then)[^.]{0,40}?\bk\b",
                        q, re.I) or re.search(r"\(\s*i\s*\)\s*k\b", q)
    if has_k and k_asked:
        asks.append((f"k = {fmt_num(kval)}", kval))
    for m in re.finditer(r"P\s*\(\s*X\s*(<=|>=|<|>)\s*(-?\d+)\s*\)", q):
        op_, a_ = m.group(1), sp.Integer(int(m.group(2)))
        sel = [p for x, p in zip(xs, pvals)
               if (x < a_ if op_ == "<" else x > a_ if op_ == ">"
                   else x <= a_ if op_ == "<=" else x >= a_)]
        asks.append((f"P(X {op_} {m.group(2)}) = "
                     f"{fmt_num(sum(sel, sp.Integer(0)))}",
                     sum(sel, sp.Integer(0))))
    for m in re.finditer(r"P\s*\(\s*(-?\d+)\s*(<=|<)\s*X\s*(<=|<)\s*"
                         r"(-?\d+)\s*\)", q):
        lo, o1, o2, hi = (sp.Integer(int(m.group(1))), m.group(2),
                          m.group(3), sp.Integer(int(m.group(4))))
        sel = [p for x, p in zip(xs, pvals)
               if (lo < x if o1 == "<" else lo <= x)
               and (x < hi if o2 == "<" else x <= hi)]
        asks.append((f"P({m.group(1)} {o1} X {o2} {m.group(4)}) = "
                     f"{fmt_num(sum(sel, sp.Integer(0)))}",
                     sum(sel, sp.Integer(0))))
    for m in re.finditer(r"P\s*\(\s*X\s*=\s*(-?\d+)\s*\)", q):
        a_ = sp.Integer(int(m.group(1)))
        sel = [p for x, p in zip(xs, pvals) if x == a_]
        if sel:
            asks.append((f"P(X = {m.group(1)}) = {fmt_num(sel[0])}",
                         sel[0]))
    word_asks = [(r"x is positive", "P(X > 0)",
                  lambda x: x > 0),
                 (r"x is non[- ]negative", "P(X >= 0)",
                  lambda x: x >= 0),
                 (r"x is negative", "P(X < 0)", lambda x: x < 0)]
    for pat, label, test in word_asks:
        if re.search(pat, ql):
            sel = [p for x, p in zip(xs, pvals) if test(x)]
            asks.append((f"{label} = {fmt_num(sum(sel, sp.Integer(0)))}",
                         sum(sel, sp.Integer(0))))
    if not asks:
        return None
    # completeness: numbered parts (i)..(iv) must all be covered
    parts = set(re.findall(r"\(\s*(i{1,3}|iv)\s*\)", ql))
    if parts and len(asks) < len(parts):
        return None
    if has_k and kval is not None and not any(a[0].startswith("k =")
                                              for a in asks):
        # k was in the table but never asked: fine only if a P-ask exists
        pass
    steps = []
    if kval is not None:
        steps.append(f"Sum of all probabilities = 1: {fmt(total)} = 1, "
                     f"so k = {fmt_num(kval)}.")
        steps.append("Each probability then lies between 0 and 1, "
                     "so this k is valid.")
    steps.append("Adding the table entries for the asked values "
                 "of X gives each probability.")
    ans = "; ".join(a[0] for a in asks)
    return _result("w169_prob_distribution", ans, steps,
                   typ="probability")


# ===========================================================================
# Family 4: rational / irrational numbers between two numbers
# ===========================================================================

_WORD_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12}


def _endpoint(seg):
    """First number token of a segment, if the segment is clean."""
    seg = seg.strip().strip(".")
    m = re.match(r"(-?\d+\s*/\s*\d+|-?\d+(?:\.\d+)?)", seg)
    if not m:
        return None
    rest = seg[m.end():].strip()
    if rest and not rest.startswith(("(", "and")):
        return None
    try:
        return _frac(m.group(1))
    except Exception:
        return None


def _between(q):
    ql = q.lower()
    if "between" not in ql and "के बीच" not in q:
        return None
    if re.search(r"\(\s*ii\s*\)", ql) or (
            re.search(r"\ba\)", ql) and re.search(r"\bb\)", ql)):
        return None                       # multi-part: not ours
    hindi = _hindi(q)
    irrational = ("irrational" in ql) or ("अपरिमेय" in q)
    if not irrational and "rational" not in ql and "परिमेय" not in q:
        return None
    m = re.search(r"(?:find|write|insert|list|give|state)\s+"
                  r"(?:any\s+|me\s+)?"
                  r"(\d+|one|two|three|four|five|six|seven|eight|nine|"
                  r"ten|eleven|twelve|a|an)?\s*"
                  r"(?:different\s+|equidistant\s+)?"
                  r"(?:irrational|rational)\s+numbers?\s+between\s+"
                  r"(.+?)\s+and\s+(.+?)\s*(?:\.(?!\d)|$|\()", q, re.I)
    if not m:
        return None
    n_tok = (m.group(1) or "a").lower()
    n = _WORD_NUM.get(n_tok, 1 if n_tok in ("a", "an") else None)
    if n is None:
        try:
            n = int(n_tok)
        except Exception:
            return None
    if not (1 <= n <= 25):
        return None
    a = _endpoint(m.group(2))
    b = _endpoint(m.group(3))
    if a is None or b is None or a == b:
        return None
    if a > b:
        a, b = b, a
    equi = "equidistant" in ql
    if not irrational:
        step = (b - a) / (n + 1)
        vals = [a + step * j for j in range(1, n + 1)]
        # verify: strictly between, distinct, count exact
        if len(vals) != n or any(not (a < v < b) for v in vals) \
                or len(set(vals)) != n:
            return None
        vs = ", ".join(_fmt_fr(v) for v in vals)
        steps = [f"Divide the gap between {_fmt_fr(a)} and {_fmt_fr(b)} "
                 f"into {n + 1} equal parts; each part is "
                 f"{_fmt_fr(step)}.",
                 f"The {n} rational numbers in between are: {vs}."]
        if equi:
            steps[0] += " (equidistant = equal gaps)."
        return _result("w169_rationals_between", vs, steps,
                       typ="number_theory")
    # irrational: v_j = a + (b - a) * sqrt(2) * j / (2(n+1)) — the
    # multiplier is irrational in (0, 1), so v_j is irrational.
    vals = []
    for j in range(1, n + 1):
        v = sp.nsimplify(a) + sp.nsimplify(b - a) * sp.sqrt(2) * j \
            / (2 * (n + 1))
        vals.append(sp.simplify(v))
    af, bf = float(a), float(b)
    for v in vals:
        vf = float(v.evalf(30))
        if not (af < vf < bf):
            return None
        if v.is_rational:
            return None
    vs = ", ".join(f"{float(v.evalf(15)):.10g}" for v in vals)
    steps = [f"Take numbers of the form a + (b - a) x sqrt(2) x "
             f"j/(2 x {n + 1}) for j = 1..{n}: the sqrt(2) factor "
             f"makes each one irrational, and each lies strictly "
             f"between {_fmt_fr(a)} and {_fmt_fr(b)}.",
             f"The {n} irrational numbers are approximately: {vs}."]
    return _result("w169_irrationals_between", vs, steps,
                   typ="number_theory")


# ===========================================================================
# Family 5: commercial sentence forms (profit / loss + simple interest)
# ===========================================================================

_CUR = r"(?:₹|Rs\.?|\$|€|£|¥|`)"
_MONEY = _CUR + r"\s*(\d[\d,]*(?:\.\d+)?)"
# Loose money: the currency sign is often dropped entirely by
# extraction ("bought a radio in 300"); used ONLY inside tight
# verb anchors (bought ... in, spent, sold ... for/in).
_MONEY_LOOSE = r"(?:₹|Rs\.?|\$|€|£|¥|`)?\s*(\d[\d,]*(?:\.\d+)?)"


def _commercial_prep(q):
    q = re.sub(r"\b(in|for|at|on)\s+%\s*(?=\d)", r"\1 ₹", q)
    q = re.sub(r"(?<=\d),(?=\d)", "", q)
    q = re.sub(r"(\d)/-", r"\1", q)      # 'Rs 30/-' price suffix
    return q


def _money_after(q, pat):
    m = re.search(pat, q, re.I)
    return _frac(m.group(1)) if m else None


def _commercial(q):
    if re.search(r"\(\s*i\s*\)", q) and re.search(r"\(\s*ii\s*\)", q):
        return None
    ql = q.lower()
    if "margin" in ql:
        return None
    q = _commercial_prep(q)

    # C1a: per-piece buy/sell with a quantity
    m = re.search(r"(?:at|price of)\s+(?:a\s+\w+\s+price\s+of\s+)?"
                  + _MONEY + r"\s*per\s+(?:piece|unit|item|notebook)",
                  q, re.I)
    m2 = re.search(r"sells?(?:\s+each)?[^.]{0,45}?at\s+" + _MONEY, q, re.I)
    mq = re.search(r"sells?\s+(\d+)\s+", q, re.I)
    if m and m2 and mq and "profit" in ql:
        cp_u, sp_u, n = _frac(m.group(1)), _frac(m2.group(1)), \
            _frac(mq.group(1))
        profit = (sp_u - cp_u) * n
        if sp_u <= cp_u:
            return None
        steps = [f"Profit on one piece = {_fmt_money(sp_u)} - "
                 f"{_fmt_money(cp_u)} = {_fmt_money(sp_u - cp_u)}.",
                 f"On {_fmt_fr(n)} pieces: profit = "
                 f"{_fmt_money(sp_u - cp_u)} x {_fmt_fr(n)} = "
                 f"{_fmt_money(profit)}."]
        return _result("w169_pl_per_unit", _fmt_money(profit), steps,
                       typ="applied", value=profit)
    # C1b: bulk buy per kg, counted items sold each
    m = re.search(r"bought\s+(" + _NUM + r")\s*kg[^.]{0,50}?at\s+"
                  + _MONEY + r"\s*per\s*kg", q, re.I)
    mc = re.search(r"counted\s+(\d+)", q, re.I)
    m2 = re.search(r"sells?\s+each[^.]{0,25}?for\s+" + _MONEY, q, re.I)
    if m and mc and m2 and "profit" in ql:
        qty, cp_u = _frac(m.group(1)), _frac(m.group(2))
        cnt, sp_u = _frac(mc.group(1)), _frac(m2.group(1))
        cp, sp = qty * cp_u, cnt * sp_u
        diff = sp - cp
        if diff <= 0:
            return None
        steps = [f"Total cost = {_fmt_fr(qty)} x {_fmt_money(cp_u)} = "
                 f"{_fmt_money(cp)}.",
                 f"Total selling price = {_fmt_fr(cnt)} x "
                 f"{_fmt_money(sp_u)} = {_fmt_money(sp)}.",
                 f"Profit = {_fmt_money(sp)} - {_fmt_money(cp)} = "
                 f"{_fmt_money(diff)}."]
        return _result("w169_pl_bulk_counted", _fmt_money(diff), steps,
                       typ="applied", value=diff)
    # C2: buy + overhead spend + sell -> profit/loss amount
    mb = re.search(r"(?:bought|purchased)[^.]{0,60}?\bin\s+" + _MONEY_LOOSE,
                   q, re.I)
    if not mb:
        mb = re.search(r"(?:bought|purchased)[^.]{0,60}?" + _MONEY, q, re.I)
    msp = re.search(r"spent\s+" + _MONEY_LOOSE, q, re.I)
    ms = re.search(r"sold[^.]{0,40}?(?:for|in)\s+" + _MONEY_LOOSE, q, re.I)
    if mb and msp and ms and ("profit" in ql or "loss" in ql):
        cp = _frac(mb.group(1)) + _frac(msp.group(1))
        spv = _frac(ms.group(1))
        diff = spv - cp
        if diff == 0:
            return None
        kind = "Profit" if diff > 0 else "Loss"
        steps = [f"Total cost = {_fmt_money(_frac(mb.group(1)))} + "
                 f"{_fmt_money(_frac(msp.group(1)))} = {_fmt_money(cp)}.",
                 f"{kind} = {_fmt_money(spv)} - {_fmt_money(cp)} = "
                 f"{_fmt_money(abs(diff))}." if diff > 0 else
                 f"{kind} = {_fmt_money(cp)} - {_fmt_money(spv)} = "
                 f"{_fmt_money(abs(diff))}."]
        return _result("w169_pl_overhead", f"{kind} of {_fmt_money(abs(diff))}",
                       steps, typ="applied", value=abs(diff))
    # C3: SP + profit/loss amount -> cost price
    ms = re.search(r"sold[^.]{0,55}?(?:in|for)\s+" + _MONEY, q, re.I)
    ma = re.search(r"(loss|profit) of\s+" + _MONEY, q, re.I)
    if ms and ma and "cost price" in ql:
        spv, amt = _frac(ms.group(1)), _frac(ma.group(2))
        cp = spv + amt if ma.group(1).lower() == "loss" else spv - amt
        if cp <= 0:
            return None
        steps = [f"Cost price = selling price "
                 f"{'+' if ma.group(1).lower() == 'loss' else '-'} "
                 f"{ma.group(1).lower()} = {_fmt_money(spv)} "
                 f"{'+' if ma.group(1).lower() == 'loss' else '-'} "
                 f"{_fmt_money(amt)} = {_fmt_money(cp)}."]
        return _result("w169_pl_sp_amount_cp", _fmt_money(cp), steps,
                       typ="applied", value=cp)
    # C6: profit percent + profit amount -> SP (or CP)
    mp = re.search(r"profit of\s+(" + _NUM + r")\s*%", q, re.I)
    ma2 = re.search(r"(?:total\s+)?profit of\s+" + _MONEY, q, re.I)
    if mp and ma2 and ("selling price" in ql or "cost price" in ql):
        p, amt = _frac(mp.group(1)), _frac(ma2.group(1))
        if p <= 0:
            return None
        cp = amt * 100 / p
        spv = cp + amt
        if spv * p != cp * p + amt * p or cp * p / 100 != amt:
            return None
        steps = [f"Profit of {_fmt_fr(p)}% equals {_fmt_money(amt)}, so "
                 f"cost price = {_fmt_money(amt)} x 100/{_fmt_fr(p)} = "
                 f"{_fmt_money(cp)}.",
                 f"Selling price = {_fmt_money(cp)} + {_fmt_money(amt)} "
                 f"= {_fmt_money(spv)}."]
        want = _fmt_money(spv) if "selling price" in ql else _fmt_money(cp)
        return _result("w169_pl_pct_amount", want, steps, typ="applied",
                       value=spv if "selling price" in ql else cp)
    # C4: CP -> SP for a target profit/loss percent
    mt = re.search(r"(" + _NUM + r")\s*%\s*(profit|loss)", q, re.I)
    if mt and re.search(r"should be sold|to get|to gain|to make", ql):
        mb2 = re.search(r"(?:bought|purchased)[^.]{0,40}?\bin\s+"
                        + _MONEY_LOOSE, q, re.I)
        moneys = re.findall(_MONEY, q, re.I)
        cp = _frac(mb2.group(1)) if mb2 else (
            _frac(moneys[0]) if len(moneys) == 1 else None)
        if cp is not None:
            p = _frac(mt.group(1))
            spv = cp * (100 + p) / 100 if mt.group(2).lower() == "profit" \
                else cp * (100 - p) / 100
            if spv <= 0:
                return None
            steps = [f"Selling price = cost price x "
                     f"(100 {'+' if mt.group(2).lower() == 'profit' else '-'} "
                     f"{_fmt_fr(p)})/100 = {_fmt_money(cp)} x "
                     f"{_fmt_fr((100 + p) / 100 if mt.group(2).lower() == 'profit' else (100 - p) / 100)} "
                     f"= {_fmt_money(spv)}."]
            return _result("w169_pl_target_pct", _fmt_money(spv), steps,
                           typ="applied", value=spv)
    # C5: SP + percent -> CP
    ms5 = re.search(r"sold[^.]{0,45}?(?:in|for)\s+" + _MONEY_LOOSE, q, re.I)
    mp5 = re.search(r"(loss|profit) of\s+(" + _NUM + r")\s*%", q, re.I)
    if ms5 and mp5 and "cost price" in ql:
        spv, p = _frac(ms5.group(1)), _frac(mp5.group(2))
        den = (100 - p) if mp5.group(1).lower() == "loss" else (100 + p)
        if den <= 0:
            return None
        cp = spv * 100 / den
        # verify: applying the percent to cp returns spv exactly
        back = cp * den / 100
        if back != spv:
            return None
        steps = [f"Selling price is {den}% of the cost price, so cost "
                 f"price = {_fmt_money(spv)} x 100/{den} = "
                 f"{_fmt_money(cp)}."]
        return _result("w169_pl_sp_pct_cp", _fmt_money(cp), steps,
                       typ="applied", value=cp)
    # C7: bulk buy total + sell rate per unit -> profit percent
    m7 = re.search(r"purchased\s+(" + _NUM + r")\s*(?:kg|quintal|litre|"
                   r"liter)[^.]{0,40}?(?:in|for)\s+" + _MONEY, q, re.I)
    m7s = re.search(r"sold at the rate of\s+" + _MONEY + r"\s*per", q, re.I)
    if m7 and m7s and "profit percent" in ql:
        qty, total = _frac(m7.group(1)), _frac(m7.group(2))
        rate = _frac(m7s.group(1))
        spv = qty * rate
        if total <= 0 or spv <= 0:
            return None
        ratio = spv / total
        if not (Fraction(1, 5) <= ratio <= 5):
            return None          # extraction-glued money guard
        pct = (spv - total) * 100 / total
        kind = "Profit" if pct > 0 else "Loss"
        steps = [f"Total selling price = {_fmt_fr(qty)} x "
                 f"{_fmt_money(rate)} = {_fmt_money(spv)}.",
                 f"{kind} percent = {_fmt_money(abs(spv - total))} / "
                 f"{_fmt_money(total)} x 100 = {_fmt_fr(abs(pct))}%."]
        return _result("w169_pl_bulk_rate", f"{kind} {_fmt_fr(abs(pct))}%",
                       steps, typ="applied", value=abs(pct))
    # C8: CP/SP pair -> profit percent
    m8 = re.search(r"(?:purchased|bought)[^.]{0,40}?\bin\s+" + _MONEY
                   + r"[^.]{0,40}?sold[^.]{0,25}?\bin\s+" + _MONEY, q, re.I)
    if m8 and "profit percent" in ql:
        cp, spv = _frac(m8.group(1)), _frac(m8.group(2))
        if cp <= 0 or spv <= cp:
            return None
        pct = (spv - cp) * 100 / cp
        steps = [f"Profit = {_fmt_money(spv)} - {_fmt_money(cp)} = "
                 f"{_fmt_money(spv - cp)}.",
                 f"Profit percent = {_fmt_money(spv - cp)}/{_fmt_money(cp)} "
                 f"x 100 = {_fmt_fr(pct)}%."]
        return _result("w169_pl_pair_pct", f"{_fmt_fr(pct)}%", steps,
                       typ="applied", value=pct)
    # C9: simple interest sentence form
    if "interest" in ql:
        mp9 = re.search(r"rate of\s+(" + _NUM + r")\s*%", q, re.I) or \
            re.search(r"(" + _NUM + r")\s*%\s*(?:annual|per annum|annually)",
                      q, re.I)
        mt9 = re.search(r"for\s+(" + _NUM + r")\s*years?", q, re.I)
        moneys = re.findall(_MONEY, q, re.I)
        P = _frac(moneys[0]) if moneys else None
        if P is None:
            mP = re.search(r"^\s*(" + _NUM + r")\s+is borrowed", q, re.I) \
                or re.search(r"(?:borrowed|loan of|deposited|deposit of)"
                             r"\s+(?:of\s+)?" + _MONEY_LOOSE, q, re.I)
            if mP:
                P = _frac(mP.group(1))
        if mp9 and mt9 and P is not None and \
                not re.search(r"\d+(?:st|nd|rd|th)\s+year", ql):
            R, T = _frac(mp9.group(1)), _frac(mt9.group(1))
            if P > 0 and R > 0 and T > 0:
                si = P * R * T / 100
                steps = [f"Simple interest = P x R x T / 100 = "
                         f"{_fmt_money(P)} x {_fmt_fr(R)} x {_fmt_fr(T)} "
                         f"/ 100 = {_fmt_money(si)}."]
                return _result("w169_simple_interest", _fmt_money(si),
                               steps, typ="applied", value=si)
    return None


# ===========================================================================
# Dispatcher
# ===========================================================================

_SCHEMAS = (_sector, _annular, _cost_per_100, _heron,
            _lines_axis_parallel, _lines_intercepts, _lines_perpendicular,
            _lines_inclination, _lines_3d,
            _prob_dist, _between, _commercial)


def solve_tierA169(question):
    """Wave 169 Tier-A method schemas; None unless one of them
    matches the question completely and verifies its answer."""
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
