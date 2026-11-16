"""Geometry: area/perimeter/volume of standard shapes and coordinate
geometry (distance, midpoint, slope, line & circle equations)."""
import math
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import (extract_points, find_param, fmt,
                                fmt_num, wants_circumference)
from .pi_policy import PI_227, pi_choice, pi_note, pi_note_hi

PI = math.pi


def _fmt_frac(fr):
    """Wave 99: display an exact Fraction from the 22/7 paths —
    integers clean ("154"), terminating fractions as decimals
    ("38.5", not "77/2"); anything else falls back to fmt_num."""
    if fr.denominator == 1:
        return str(fr.numerator)
    q = fr.denominator
    for _p in (2, 5):
        while q % _p == 0:
            q //= _p
    if q == 1:
        return fmt_num(float(fr))
    return fmt_num(fr)


def _param_flex(q, names):
    """find_param, plus the NCERT sentence form "the radius of a
    cylinder is 7 cm" (Wave 30): the plain finder expects the
    number right after the name ("radius 7", "radius is 7") and
    missed the "radius of a <shape> is N" phrasing entirely, so
    whole mensuration questions fell to the similar-example
    layer even though the formula code existed."""
    v = find_param(q, names)
    if v is not None:
        return v
    for name in names:
        if len(name) < 3:
            continue
        m = re.search(
            rf"\b{name}\s+of\s+(?:a\s+|an\s+|the\s+)?\w+\s+is\s+"
            r"(-?\d+(?:\.\d+)?)", q)
        if m:
            s = m.group(1)
            return float(s) if "." in s else int(s)
    return None


def _solid_height(q, word):
    """The height belonging to one named solid in a combined-
    solid sentence (Wave 47): "cylinder of radius 4 cm and
    height 6 cm" (height stated after the solid's name) or
    "the height of the cone is 4 cm" (height stated before
    it). Returns a float or None."""
    m = re.search(rf"\b{word}\b[\s\S]{{0,90}}?height\s+"
                  r"(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1))
    m = re.search(rf"height\s+of\s+(?:the\s+|a\s+|an\s+)?"
                  rf"{word}\s+is\s+(\d+(?:\.\d+)?)", q)
    if m:
        return float(m.group(1))
    return None


def _three_sides(q):
    """The three side lengths after the word "side(s)", tolerating
    units and filler ("sides of a triangle are 5 cm, 12 cm and
    13 cm") — the old capture regex stopped at the first unit
    ("cm" is not a digit) and Heron never fired (Wave 30)."""
    m = re.search(r"sides?\b[^.]{0,60}", q)
    if not m:
        return None
    nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?",
                                         m.group(0))]
    return nums if len(nums) == 3 else None


def _third_angle(q):
    """Two angles of a triangle given, the third asked (Wave 30).
    "angle A = 50 degrees and angle B = 60 degrees. Find angle
    C" used to reach algebra, which echoed "A = 50" back."""
    if "triangle" not in q or "angle" not in q:
        return None
    pairs = re.findall(
        r"angle\s*([a-z])\s*(?:=|is)\s*(\d+(?:\.\d+)?)\s*"
        r"(?:degrees?|°)?", q)
    given = {lab: float(v) for lab, v in pairs}
    ma = re.search(r"find\s+(?:the\s+)?angle\s*([a-z])\b", q)
    if len(given) == 2 and ma and ma.group(1) not in given:
        asked = ma.group(1)
        rest = " + ".join(fmt_num(v) for v in given.values())
        third = 180 - sum(given.values())
        steps = [
            "The three angles of a triangle add up to 180°.",
            f"Angle {asked.upper()} = 180° - ({rest}) = "
            f"{fmt_num(third)}°",
        ]
        return "third angle", f"{fmt_num(third)}°", steps
    m = re.search(
        r"angles?\s+of\s+a\s+triangle\s+are\s+(\d+(?:\.\d+)?)"
        r"\s*(?:degrees?|°)?\s*and\s+(\d+(?:\.\d+)?)", q)
    if m:
        a1, a2 = float(m.group(1)), float(m.group(2))
        third = 180 - a1 - a2
        steps = [
            "The three angles of a triangle add up to 180°.",
            f"Third angle = 180° - ({fmt_num(a1)}° + "
            f"{fmt_num(a2)}°) = {fmt_num(third)}°",
        ]
        return "third angle", f"{fmt_num(third)}°", steps
    return None


def _angle_deg(q):
    m = re.search(r"angle\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*"
                  r"(?:degrees?|°)", q) or \
        re.search(r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)", q)
    return float(m.group(1)) if m else None


def _mensuration_extra(q):
    """Wave 32 mensuration: several of these were actively
    HIJACKED before this block existed — a hemisphere answered
    as a SPHERE (the word 'hemisphere' contains 'sphere'), a
    cone's CSA/TSA and a cylinder's CSA answered as volume/TSA,
    a sector answered as the whole circle. This block therefore
    runs BEFORE the generic shape branches."""
    # ---- Frustum of a cone -------------------------------------
    if "frustum" in q:
        seg = re.search(r"radii\s+(?:of\s+)?([^.]+)", q)
        nums = [float(v) for v in re.findall(
            r"\d+(?:\.\d+)?", seg.group(1))] if seg else []
        h = _param_flex(q, ["height", "h"])
        if len(nums) < 2 or h is None:
            return None
        R, r = max(nums[0], nums[1]), min(nums[0], nums[1])
        slant = _param_flex(q, ["slant height", "slant"])
        if slant is None:
            slant = math.sqrt(h * h + (R - r) ** 2)
        # Wave 99: pi policy — 22/7 only when BOTH radii are
        # multiples of 7 (see solver/pi_policy.py).
        _pi, _u227, _reason = pi_choice(radii=[R, r])
        _note = [pi_note(_reason)] if _u227 else []
        if "curved surface" in q or " csa" in q:
            val = _pi * (R + r) * slant
            steps = _note + [
                f"For a frustum: R = {fmt_num(R)}, "
                f"r = {fmt_num(r)}, slant height l = "
                f"{slant:.4f}",
                f"Curved surface area = pi(R + r)l = pi × "
                f"({fmt_num(R)} + {fmt_num(r)}) × {slant:.4f} "
                f"= {fmt_num(val)}",
            ]
            return "frustum csa", fmt_num(val), steps
        if "total surface" in q or " tsa" in q:
            val = _pi * (R + r) * slant + _pi * (R * R + r * r)
            steps = _note + [
                f"For a frustum: R = {fmt_num(R)}, "
                f"r = {fmt_num(r)}, slant height l = "
                f"{slant:.4f}",
                f"TSA = pi(R + r)l + pi(R^2 + r^2) = "
                f"{fmt_num(val)}",
            ]
            return "frustum tsa", fmt_num(val), steps
        val = _pi * h / 3 * (R * R + R * r + r * r)
        steps = _note + [
            f"For a frustum: R = {fmt_num(R)}, "
            f"r = {fmt_num(r)}, h = {fmt_num(h)}",
            f"Volume = (1/3)·pi·h·(R^2 + Rr + r^2) = "
            f"(1/3) × pi × {fmt_num(h)} × ({fmt_num(R * R)} + "
            f"{fmt_num(R * r)} + {fmt_num(r * r)}) "
            f"= {fmt_num(val)}",
        ]
        return "frustum volume", fmt_num(val), steps

    # ---- Combined solid: cylinder + cone (same radius) ---------
    if "cylinder" in q and "cone" in q and (
            "mounted" in q or "made of" in q or "placed on" in q
            or "surmounted" in q or "consists of" in q
            or "total volume" in q):
        r = _param_flex(q, ["radius", "r"])
        mh1 = re.search(r"cylinder\s+of\s+height\s+"
                        r"(\d+(?:\.\d+)?)", q)
        mh2 = re.search(r"cone\s+of\s+height\s+"
                        r"(\d+(?:\.\d+)?)", q)
        # Wave 47: the NCERT sentence form states the radius
        # first ("a cylinder of radius 4 cm and height 6 cm
        # with a cone of the same radius and height 3 cm") —
        # the strict "cylinder of height N" regex missed it
        # and the cone was silently dropped (audit #206:
        # 301.59 cylinder-only instead of 351.86). Fall back
        # to each solid's own stated height.
        h1 = float(mh1.group(1)) if mh1 else \
            _solid_height(q, "cylinder")
        h2 = float(mh2.group(1)) if mh2 else \
            _solid_height(q, "cone")
        if r is None or h1 is None or h2 is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        v1 = _pi * r * r * h1
        v2 = _pi * r * r * h2 / 3
        steps = _note + [
            f"Volume of the cylinder part = pi·r^2·h = pi × "
            f"{fmt_num(r)}^2 × {fmt_num(h1)} = {fmt_num(v1)}",
            f"Volume of the cone part = (1/3)·pi·r^2·h = "
            f"(1/3) × pi × {fmt_num(r)}^2 × {fmt_num(h2)} "
            f"= {fmt_num(v2)}",
            f"Total volume = {fmt_num(v1)} + {fmt_num(v2)} "
            f"= {fmt_num(v1 + v2)}",
        ]
        return "combined volume", fmt_num(v1 + v2), steps

    # ---- Combined solids with a hemisphere (Wave 47) --------
    # Audit #10: hemisphere combinations had no pattern at
    # all — a "cylinder with a hemisphere on top" fell to the
    # single-solid branches and only one part was counted.
    # Volume only; the shared radius comes from the sentence.
    if "hemisphere" in q and (
            "mounted" in q or "made of" in q or "placed on" in q
            or "surmounted" in q or "consists of" in q
            or "on top" in q or "total volume" in q) and (
            "surface" not in q):
        r = _param_flex(q, ["radius", "r"])
        if r is None:
            _diam = _param_flex(q, ["diameter"])
            if _diam is not None:
                r = _diam / 2
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        if r is not None and "cylinder" in q:
            h = _solid_height(q, "cylinder")
            if h is not None:
                v1 = _pi * r * r * h
                v2 = 2 * _pi * r ** 3 / 3
                steps = _note + [
                    f"Volume of the cylinder part = pi·r^2·h "
                    f"= pi × {fmt_num(r)}^2 × {fmt_num(h)} "
                    f"= {fmt_num(v1)}",
                    f"Volume of the hemisphere part = "
                    f"(2/3)·pi·r^3 = (2/3) × pi × "
                    f"{fmt_num(r)}^3 = {fmt_num(v2)}",
                    f"Total volume = {fmt_num(v1)} + "
                    f"{fmt_num(v2)} = {fmt_num(v1 + v2)}",
                ]
                return "combined volume", fmt_num(v1 + v2), \
                    steps
        if r is not None and "cone" in q:
            h = _solid_height(q, "cone")
            if h is not None:
                v1 = _pi * r * r * h / 3
                v2 = 2 * _pi * r ** 3 / 3
                steps = _note + [
                    f"Volume of the cone part = "
                    f"(1/3)·pi·r^2·h = (1/3) × pi × "
                    f"{fmt_num(r)}^2 × {fmt_num(h)} "
                    f"= {fmt_num(v1)}",
                    f"Volume of the hemisphere part = "
                    f"(2/3)·pi·r^3 = (2/3) × pi × "
                    f"{fmt_num(r)}^3 = {fmt_num(v2)}",
                    f"Total volume = {fmt_num(v1)} + "
                    f"{fmt_num(v2)} = {fmt_num(v1 + v2)}",
                ]
                return "combined volume", fmt_num(v1 + v2), \
                    steps

    # ---- Hemisphere --------------------------------------------
    if "hemisphere" in q:
        r = _param_flex(q, ["radius", "r"])
        if r is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        if "curved surface" in q or " csa" in q:
            val = 2 * _pi * r * r
            steps = _note + [f"Curved surface area of a hemisphere = "
                     f"2·pi·r^2 = 2 × pi × {fmt_num(r)}^2 "
                     f"= {fmt_num(val)}"]
            return "hemisphere csa", fmt_num(val), steps
        if "total surface" in q or " tsa" in q or \
                "surface" in q:
            val = 3 * _pi * r * r
            steps = _note + [
                f"Total surface area of a hemisphere = curved "
                f"surface + base = 2·pi·r^2 + pi·r^2 "
                f"= 3·pi·r^2",
                f"= 3 × pi × {fmt_num(r)}^2 = {fmt_num(val)}",
            ]
            return "hemisphere tsa", fmt_num(val), steps
        val = 2 * _pi * r ** 3 / 3
        steps = _note + [f"Volume of a hemisphere = (2/3)·pi·r^3 = "
                 f"(2/3) × pi × {fmt_num(r)}^3 "
                 f"= {fmt_num(val)}"]
        return "hemisphere volume", fmt_num(val), steps

    # ---- Cone CSA / TSA ----------------------------------------
    if "cone" in q and ("curved surface" in q or " csa" in q
                        or "total surface" in q or " tsa" in q):
        r = _param_flex(q, ["radius", "r"])
        if r is None:
            return None
        slant = _param_flex(q, ["slant height", "slant", "l"])
        h = _param_flex(q, ["height", "h"])
        if slant is None and h is not None:
            slant = math.sqrt(r * r + h * h)
        if slant is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        if "curved surface" in q or " csa" in q:
            val = _pi * r * slant
            steps = _note + [
                f"Slant height l = {fmt_num(slant)}",
                f"Curved surface area of a cone = pi·r·l = "
                f"pi × {fmt_num(r)} × {fmt_num(slant)} "
                f"= {fmt_num(val)}",
            ]
            return "cone csa", fmt_num(val), steps
        val = _pi * r * (slant + r)
        steps = _note + [
            f"Slant height l = {fmt_num(slant)}",
            f"Total surface area of a cone = pi·r(l + r) = "
            f"pi × {fmt_num(r)} × ({fmt_num(slant)} + "
            f"{fmt_num(r)}) = {fmt_num(val)}",
        ]
        return "cone tsa", fmt_num(val), steps

    # ---- Cylinder CSA ------------------------------------------
    if "cylinder" in q and ("curved surface" in q
                            or " csa" in q):
        r = _param_flex(q, ["radius", "r"])
        h = _param_flex(q, ["height", "h"])
        if r is None or h is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        val = 2 * _pi * r * h
        steps = _note + [f"Curved surface area of a cylinder = "
                 f"2·pi·r·h = 2 × pi × {fmt_num(r)} × "
                 f"{fmt_num(h)} = {fmt_num(val)}"]
        return "cylinder csa", fmt_num(val), steps

    # ---- Sector / segment / arc --------------------------------
    if "segment" in q and "circle" in q:
        r = _param_flex(q, ["radius", "r"])
        th = _angle_deg(q)
        if r is None or th is None:
            return None
        # Wave 99: the policy pi applies to the sector part;
        # the triangle part (a sine) never involves pi.
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        sector = th / 360 * _pi * r * r
        tri = 0.5 * r * r * math.sin(math.radians(th))
        val = sector - tri
        steps = _note + [
            f"Area of the sector = (theta/360)·pi·r^2 = "
            f"({fmt_num(th)}/360) × pi × {fmt_num(r)}^2 "
            f"= {fmt_num(sector)}",
            f"Area of the triangle = (1/2)·r^2·sin(theta) = "
            f"{fmt_num(tri)}",
            f"Area of the segment = {fmt_num(sector)} - "
            f"{fmt_num(tri)} = {fmt_num(val)}",
        ]
        return "segment area", fmt_num(val), steps
    if "sector" in q:
        r = _param_flex(q, ["radius", "r"])
        th = _angle_deg(q)
        if r is None or th is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        val = th / 360 * _pi * r * r
        steps = _note + [f"Area of a sector = (theta/360)·pi·r^2 = "
                 f"({fmt_num(th)}/360) × pi × {fmt_num(r)}^2 "
                 f"= {fmt_num(val)}"]
        return "sector area", fmt_num(val), steps
    if "arc" in q and "length" in q:
        r = _param_flex(q, ["radius", "r"])
        th = _angle_deg(q)
        if r is None or th is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        val = th / 360 * 2 * _pi * r
        steps = _note + [f"Length of an arc = (theta/360)·2·pi·r = "
                 f"({fmt_num(th)}/360) × 2 × pi × "
                 f"{fmt_num(r)} = {fmt_num(val)}"]
        return "arc length", fmt_num(val), steps

    # ---- Cuboid --------------------------------------------------
    if "cuboid" in q:
        L = find_param(q, ["length"])
        B = find_param(q, ["breadth", "width"])
        H = find_param(q, ["height"])
        if L is None or B is None or H is None:
            return None
        if "total surface" in q or " tsa" in q or \
                ("surface" in q and "lateral" not in q):
            val = 2 * (L * B + B * H + H * L)
            steps = [f"Total surface area of a cuboid = "
                     f"2(lb + bh + hl) = 2 × ({fmt_num(L)}×"
                     f"{fmt_num(B)} + {fmt_num(B)}×{fmt_num(H)}"
                     f" + {fmt_num(H)}×{fmt_num(L)}) "
                     f"= {fmt_num(val)}"]
            return "cuboid tsa", fmt_num(val), steps
        if "lateral surface" in q or " lsa" in q:
            val = 2 * H * (L + B)
            steps = [f"Lateral surface area of a cuboid = "
                     f"2h(l + b) = 2 × {fmt_num(H)} × "
                     f"({fmt_num(L)} + {fmt_num(B)}) "
                     f"= {fmt_num(val)}"]
            return "cuboid lsa", fmt_num(val), steps
        val = L * B * H
        steps = [f"Volume of a cuboid = l × b × h = "
                 f"{fmt_num(L)} × {fmt_num(B)} × {fmt_num(H)} "
                 f"= {fmt_num(val)}"]
        return "cuboid volume", fmt_num(val), steps
    return None


def _area_perimeter_volume(q: str):
    extra = _mensuration_extra(q)
    if extra is not None:
        return extra
    # ---- Circle ------------------------------------------------------
    if "circle" in q or wants_circumference(q):
        r = _param_flex(q, ["radius", "r"])
        d = find_param(q, ["diameter"])
        # Wave 59: the radius itself asked from a stated
        # diameter ("diameter is 14 cm, find its radius") —
        # the branch used to compute the area instead.
        if d is not None and "radius" in q \
                and not wants_circumference(q) and "area" not in q:
            return "radius", fmt_num(d / 2), [
                "Radius = diameter / 2",
                f"= {fmt_num(d)} / 2 = {fmt_num(d / 2)}"]
        if r is None and d is not None:
            r = d / 2
        if r is None:
            # Wave 30: area asked with the CIRCUMFERENCE given
            # ("area of a circle whose circumference is 44 cm")
            # — recover r from C = 2·pi·r first.
            C = find_param(q, ["circumference"])
            if C is None:
                # Wave 74: the stated circumference under a
                # misspelt name ("circumferance is 44 cm").
                _mc = re.search(
                    r"circumf\w*\s*(?:is|=|:)?\s*"
                    r"(-?\d+(?:\.\d+)?)", q)
                if _mc:
                    _cs = _mc.group(1)
                    C = float(_cs) if "." in _cs else int(_cs)
            if C is not None and "area" in q:
                # Wave 99: C a multiple of 22 -> r = 7C/44 is
                # exact with pi = 22/7 (Fraction arithmetic, so
                # the textbook value comes out clean).
                _pi, _u227, _reason = pi_choice(circumference=C)
                if _u227:
                    rr = (Fraction(C).limit_denominator(10 ** 6)
                          / (2 * PI_227))
                    val = PI_227 * rr * rr
                    steps = [
                        pi_note(_reason),
                        f"Radius from the circumference: r = C / "
                        f"(2·pi) = {fmt_num(C)} / (2 × 22/7) "
                        f"= {_fmt_frac(rr)}",
                        f"Area = pi·r^2 = (22/7) × "
                        f"{_fmt_frac(rr)}^2 = {_fmt_frac(val)}",
                    ]
                    return "area", _fmt_frac(val), steps
                rr = C / (2 * PI)
                val = PI * rr * rr
                steps = [
                    f"Radius from the circumference: r = C / "
                    f"(2·pi) = {fmt_num(C)} / (2 × pi) "
                    f"≈ {rr:.4f}",
                    f"Area = pi·r^2 = pi × {rr:.4f}^2 "
                    f"≈ {val:.4f}",
                ]
                return "area", f"≈ {val:.4f}", steps
            return None
        # Wave 99: pi policy for the direct radius/diameter
        # forms (22/7 answer is the clean value, no "·pi ≈").
        _pi, _u227, _reason = (pi_choice(diameter=d)
                               if d is not None
                               else pi_choice(radius=r))
        if wants_circumference(q) or "perimeter" in q:
            val = 2 * _pi * r
            if _u227:
                steps = [
                    pi_note(_reason),
                    f"Circumference = 2·pi·r = 2 × (22/7) × "
                    f"{fmt_num(r)}",
                    f"= {fmt_num(val)}",
                ]
                return "circumference", fmt_num(val), steps
            steps = [f"Circumference = 2·pi·r = 2 × pi × {fmt_num(r)}",
                     f"= {fmt_num(val)} (approx) = {fmt_num(2 * r)}·pi "
                     f"exactly"]
            return "circumference", f"{fmt_num(2 * r)}·pi ≈ {val:.4f}", steps
        val = _pi * r * r
        if _u227:
            steps = [
                pi_note(_reason),
                f"Area = pi·r^2 = (22/7) × {fmt_num(r)}^2 "
                f"= (22/7) × {fmt_num(r * r)}",
                f"= {fmt_num(val)}",
            ]
            return "area", fmt_num(val), steps
        steps = [f"Area = pi·r^2 = pi × {fmt_num(r)}^2 = pi × "
                 f"{fmt_num(r * r)}",
                 f"= {fmt_num(r * r)}·pi ≈ {val:.4f}"]
        return "area", f"{fmt_num(r * r)}·pi ≈ {val:.4f}", steps

    # ---- Square ------------------------------------------------------
    if "square" in q:
        s = find_param(q, ["side", "s"])
        if s is None:
            return None
        if "perimeter" in q:
            steps = [f"Perimeter = 4 × side = 4 × {fmt_num(s)} = "
                     f"{fmt_num(4 * s)}"]
            return "perimeter", fmt_num(4 * s), steps
        steps = [f"Area = side^2 = {fmt_num(s)}^2 = {fmt_num(s * s)}"]
        return "area", fmt_num(s * s), steps

    # ---- Parallelogram / Trapezium / Rhombus / Four walls --
    # Wave 56: standard mensuration schemas that had no
    # branch at all and fell to the concept layer.
    if "parallelogram" in q:
        _pb = find_param(q, ["base", "aadhar"])
        _ph = find_param(q, ["height", "h", "unchai"])
        if _pb is not None and _ph is not None:
            val = _pb * _ph
            steps = [f"Area of a parallelogram = base × "
                     f"height = {fmt_num(_pb)} × "
                     f"{fmt_num(_ph)} = {fmt_num(val)}"]
            return "area", fmt_num(val), steps
        return None
    if "trapezium" in q or "trapezoid" in q:
        _tm = re.search(r"parallel\s+sides\s+are\s+"
                        r"(\d+(?:\.\d+)?)\s*(?:cm|m|mm)?\s+and"
                        r"\s+(\d+(?:\.\d+)?)", q)
        _th = find_param(q, ["distance", "height", "h"])
        if _th is None:
            # "the distance between them is 7 cm" — the
            # number is not adjacent to the word "distance".
            _md2 = re.search(r"distance\s+between\s+them\s+"
                             r"is\s+(\d+(?:\.\d+)?)", q)
            if _md2:
                _th = float(_md2.group(1))
        if _tm and _th is not None:
            _a, _b = float(_tm.group(1)), float(_tm.group(2))
            val = 0.5 * (_a + _b) * _th
            steps = [
                "Area of a trapezium = (1/2) × (sum of the "
                "parallel sides) × distance between them",
                f"= (1/2) × ({fmt_num(_a)} + {fmt_num(_b)}) "
                f"× {fmt_num(_th)} = {fmt_num(val)}",
            ]
            return "area", fmt_num(val), steps
        return None
    if "rhombus" in q:
        _dm = re.search(r"diagonals\s+are\s+"
                        r"(\d+(?:\.\d+)?)\s*(?:cm|m|mm)?\s+and"
                        r"\s+(\d+(?:\.\d+)?)", q)
        if _dm:
            _a, _b = float(_dm.group(1)), float(_dm.group(2))
            val = 0.5 * _a * _b
            steps = [
                "Area of a rhombus = (1/2) × product of the "
                "diagonals",
                f"= (1/2) × {fmt_num(_a)} × {fmt_num(_b)} = "
                f"{fmt_num(val)}",
            ]
            return "area", fmt_num(val), steps
        return None
    if "four walls" in q:
        _fl = find_param(q, ["length", "l"])
        _fb = find_param(q, ["breadth", "width", "b", "w"])
        _fh = find_param(q, ["height", "h"])
        if _fl is not None and _fb is not None \
                and _fh is not None:
            val = 2 * _fh * (_fl + _fb)
            steps = [
                "Area of the four walls = 2 × height × "
                "(length + breadth)",
                f"= 2 × {fmt_num(_fh)} × ({fmt_num(_fl)} + "
                f"{fmt_num(_fb)}) = {fmt_num(val)}",
            ]
            return "area of four walls", fmt_num(val), steps
        return None

    # ---- Rectangle ---------------------------------------------------
    if "rectangle" in q:
        l = find_param(q, ["length", "l"])
        b = find_param(q, ["breadth", "width", "b", "w"])
        if (l is None) != (b is None) and "perimeter" in q:
            # Wave 56: perimeter + one side -> the other side
            # ("perimeter is 60, length is 18, find breadth").
            _pm = re.search(r"perimeter\s+(?:is\s+)?"
                            r"(\d+(?:\.\d+)?)", q) or \
                re.search(r"perimeter\s+of\s+(?:a\s+|the\s+)?"
                          r"rectangle\s+is\s+"
                          r"(\d+(?:\.\d+)?)", q)
            if _pm:
                _P = float(_pm.group(1))
                if l is not None:
                    _other = _P / 2 - l
                    if _other > 0:
                        steps = [
                            f"Perimeter = 2(l + b), so l + b "
                            f"= {_P} / 2 = {fmt_num(_P / 2)}",
                            f"Breadth = {fmt_num(_P / 2)} - "
                            f"{fmt_num(l)} = "
                            f"{fmt_num(_other)}",
                        ]
                        return "breadth", fmt_num(_other), steps
                else:
                    _other = _P / 2 - b
                    if _other > 0:
                        steps = [
                            f"Perimeter = 2(l + b), so l + b "
                            f"= {_P} / 2 = {fmt_num(_P / 2)}",
                            f"Length = {fmt_num(_P / 2)} - "
                            f"{fmt_num(b)} = {fmt_num(_other)}",
                        ]
                        return "length", fmt_num(_other), steps
            return None
        if l is None or b is None:
            # Wave 57: "the length of a rectangle is 20 cm and
            # breadth is 10 cm" — length stated BEFORE the word
            # rectangle, so find_param's adjacency never sees it.
            ml2 = re.search(r"length\s+of\s+a\s+rectangle\s+is\s+"
                            r"(\d+(?:\.\d+)?)", q)
            mb2 = re.search(r"(?:breadth|width)\s*(?:is\s+)?"
                            r"(\d+(?:\.\d+)?)", q)
            if ml2 and mb2:
                l, b = float(ml2.group(1)), float(mb2.group(1))
                l = int(l) if l == int(l) else l
                b = int(b) if b == int(b) else b
        if l is None or b is None:
            # Wave 13: "rectangle 8 cm by 5 cm" / "rectangle 8 by 5"
            # — the two bare numbers after the word rectangle.
            m2 = re.search(
                r"rectangle\s+(?:of\s+)?(\d+(?:\.\d+)?)\s*"
                r"(?:cm|m|mm)?\s*(?:by|x|×)\s*(\d+(?:\.\d+)?)", q)
            if m2:
                l, b = float(m2.group(1)), float(m2.group(2))
                l = int(l) if l == int(l) else l
                b = int(b) if b == int(b) else b
        if l is None or b is None:
            return None
        if "perimeter" in q:
            steps = [f"Perimeter = 2(l + b) = 2({fmt_num(l)} + "
                     f"{fmt_num(b)}) = {fmt_num(2 * (l + b))}"]
            return "perimeter", fmt_num(2 * (l + b)), steps
        steps = [f"Area = length × breadth = {fmt_num(l)} × {fmt_num(b)} "
                 f"= {fmt_num(l * b)}"]
        return "area", fmt_num(l * b), steps

    # ---- Triangle ----------------------------------------------------
    if "triangle" in q:
        if "perimeter" in q:
            sides = _three_sides(q)
            if sides:
                steps = ["Perimeter = sum of the three sides = "
                         + " + ".join(fmt_num(s) for s in sides)
                         + f" = {fmt_num(sum(sides))}"]
                return "perimeter", fmt_num(sum(sides)), steps
            return None
        base = find_param(q, ["base"])
        height = find_param(q, ["height", "h"])
        if base is not None and height is not None:
            val = 0.5 * base * height
            steps = [f"Area = (1/2) × base × height = 0.5 × "
                     f"{fmt_num(base)} × {fmt_num(height)} = "
                     f"{fmt_num(val)}"]
            return "area", fmt_num(val), steps
        sides = _three_sides(q)
        if sides:  # Heron's formula
            a, b, c = sides
            s = (a + b + c) / 2
            area = math.sqrt(max(s * (s - a) * (s - b) * (s - c), 0))
            steps = [
                f"Semi-perimeter s = (a + b + c)/2 = {fmt_num(s)}",
                "Heron: Area = sqrt(s(s-a)(s-b)(s-c))",
                f"= sqrt({fmt_num(s)} × {fmt_num(s - a)} × "
                f"{fmt_num(s - b)} × {fmt_num(s - c)}) "
                f"≈ {area:.4f}",
            ]
            return "area (Heron)", f"{area:.4f}", steps
        return None

    # ---- Sphere ------------------------------------------------------
    if "sphere" in q:
        r = _param_flex(q, ["radius", "r"])
        if r is None:
            # Wave 56: diameter given instead of radius
            # ("volume of a sphere of diameter 14 cm").
            _d56 = find_param(q, ["diameter"])
            if _d56 is not None:
                r = _d56 / 2
        if r is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        if "surface" in q:
            val = 4 * _pi * r * r
            if _u227:
                steps = _note + [
                    f"Surface area = 4·pi·r^2 = 4 × (22/7) × "
                    f"{fmt_num(r)}^2",
                    f"= {fmt_num(val)}"]
                return "surface area", fmt_num(val), steps
            steps = [f"Surface area = 4·pi·r^2 = 4 × pi × {fmt_num(r)}^2",
                     f"≈ {val:.4f}"]
            return "surface area", f"≈ {val:.4f}", steps
        val = (4 / 3) * _pi * r ** 3
        if _u227:
            steps = _note + [
                f"Volume = (4/3)·pi·r^3 = (4/3) × (22/7) × "
                f"{fmt_num(r)}^3",
                f"= {fmt_num(4 * r ** 3)} × (22/7) / 3 "
                f"= {fmt_num(val)}"]
            return "volume", fmt_num(val), steps
        steps = [f"Volume = (4/3)·pi·r^3 = (4/3) × pi × {fmt_num(r)}^3",
                 f"= {fmt_num(4 * r ** 3)}·pi/3 ≈ {val:.4f}"]
        return "volume", f"≈ {val:.4f}", steps

    # ---- Cube --------------------------------------------------------
    if "cube" in q:
        s = find_param(q, ["side", "s", "edge"])
        if s is None:
            return None
        if "surface" in q:
            steps = [f"Surface area = 6 × side^2 = 6 × {fmt_num(s)}^2 = "
                     f"{fmt_num(6 * s * s)}"]
            return "surface area", fmt_num(6 * s * s), steps
        steps = [f"Volume = side^3 = {fmt_num(s)}^3 = {fmt_num(s ** 3)}"]
        return "volume", fmt_num(s ** 3), steps

    # ---- Cylinder ----------------------------------------------------
    if "cylinder" in q:
        r = _param_flex(q, ["radius", "r"])
        h = _param_flex(q, ["height", "h"])
        if r is None or h is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        if "surface" in q:
            val = 2 * _pi * r * (r + h)
            if _u227:
                steps = _note + [
                    f"Total surface area = 2·pi·r(r + h) = "
                    f"2 × (22/7) × {fmt_num(r)} × "
                    f"({fmt_num(r)} + {fmt_num(h)})",
                    f"= {fmt_num(val)}"]
                return "surface area", fmt_num(val), steps
            steps = [f"Total surface area = 2·pi·r(r + h) = 2 × pi × "
                     f"{fmt_num(r)} × ({fmt_num(r)} + {fmt_num(h)})",
                     f"≈ {val:.4f}"]
            return "surface area", f"≈ {val:.4f}", steps
        val = _pi * r * r * h
        if _u227:
            steps = _note + [
                f"Volume = pi·r^2·h = (22/7) × {fmt_num(r)}^2 "
                f"× {fmt_num(h)}",
                f"= {fmt_num(val)}"]
            return "volume", fmt_num(val), steps
        steps = [f"Volume = pi·r^2·h = pi × {fmt_num(r)}^2 × "
                 f"{fmt_num(h)}", f"≈ {val:.4f}"]
        return "volume", f"≈ {val:.4f}", steps

    # ---- Cone --------------------------------------------------------
    if "cone" in q:
        r = _param_flex(q, ["radius", "r"])
        h = _param_flex(q, ["height", "h"])
        if r is None or h is None:
            return None
        _pi, _u227, _reason = pi_choice(radius=r)
        _note = [pi_note(_reason)] if _u227 else []
        val = (1 / 3) * _pi * r * r * h
        if _u227:
            steps = _note + [
                f"Volume = (1/3)·pi·r^2·h = (1/3) × (22/7) × "
                f"{fmt_num(r)}^2 × {fmt_num(h)}",
                f"= {fmt_num(val)}"]
            return "volume", fmt_num(val), steps
        steps = [f"Volume = (1/3)·pi·r^2·h = (1/3) × pi × "
                 f"{fmt_num(r)}^2 × {fmt_num(h)}", f"≈ {val:.4f}"]
        return "volume", f"≈ {val:.4f}", steps

    return None


def _coordinate(q: str):
    pts = extract_points(q)

    # Wave 30: section formula — the point dividing the join of
    # two points in a given ratio. This question used to leak to
    # the applied ratio simplifier, which answered "1 : 2" (the
    # ratio echoed back) instead of the point.
    if "divides" in q and len(pts) >= 2:
        mr = re.search(r"ratio\s+(\d+(?:\.\d+)?)\s*:\s*"
                       r"(\d+(?:\.\d+)?)", q)
        if mr:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            m_, n_ = float(mr.group(1)), float(mr.group(2))
            if "externally" in q and m_ != n_:
                px = (m_ * x2 - n_ * x1) / (m_ - n_)
                py = (m_ * y2 - n_ * y1) / (m_ - n_)
                steps = [
                    "Section formula (external division): "
                    "P = ((m·x2 - n·x1)/(m - n), "
                    "(m·y2 - n·y1)/(m - n))",
                    f"= (({fmt_num(m_)}×{fmt_num(x2)} - "
                    f"{fmt_num(n_)}×{fmt_num(x1)}) / "
                    f"{fmt_num(m_ - n_)}, ({fmt_num(m_)}×"
                    f"{fmt_num(y2)} - {fmt_num(n_)}×"
                    f"{fmt_num(y1)}) / {fmt_num(m_ - n_)})",
                    f"= ({fmt_num(px)}, {fmt_num(py)})",
                ]
                return "section formula", \
                    f"({fmt_num(px)}, {fmt_num(py)})", steps
            px = (m_ * x2 + n_ * x1) / (m_ + n_)
            py = (m_ * y2 + n_ * y1) / (m_ + n_)
            steps = [
                "Section formula (internal division): "
                "P = ((m·x2 + n·x1)/(m + n), "
                "(m·y2 + n·y1)/(m + n))",
                f"= (({fmt_num(m_)}×{fmt_num(x2)} + "
                f"{fmt_num(n_)}×{fmt_num(x1)}) / "
                f"{fmt_num(m_ + n_)}, ({fmt_num(m_)}×"
                f"{fmt_num(y2)} + {fmt_num(n_)}×"
                f"{fmt_num(y1)}) / {fmt_num(m_ + n_)})",
                f"= ({fmt_num(px)}, {fmt_num(py)})",
            ]
            return "section formula", \
                f"({fmt_num(px)}, {fmt_num(py)})", steps

    # Wave 30: area of a triangle from its three vertices
    # (shoelace formula).
    if "area" in q and "triangle" in q and len(pts) >= 3:
        (x1, y1), (x2, y2), (x3, y3) = pts[0], pts[1], pts[2]
        val = abs(x1 * (y2 - y3) + x2 * (y3 - y1)
                  + x3 * (y1 - y2)) / 2
        steps = [
            "Area of a triangle with vertices (x1, y1), "
            "(x2, y2), (x3, y3) = (1/2)·|x1(y2 - y3) + "
            "x2(y3 - y1) + x3(y1 - y2)|",
            f"= (1/2)·|{fmt_num(x1)}×({fmt_num(y2)} - "
            f"{fmt_num(y3)}) + {fmt_num(x2)}×({fmt_num(y3)} - "
            f"{fmt_num(y1)}) + {fmt_num(x3)}×({fmt_num(y1)} - "
            f"{fmt_num(y2)})| = {fmt_num(val)} square units",
        ]
        return "area", fmt_num(val), steps

    if "distance" in q and len(pts) >= 2:
        (x1, y1), (x2, y2) = pts[0], pts[1]
        d2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        d = math.sqrt(d2)
        steps = [
            f"Distance = sqrt((x2-x1)^2 + (y2-y1)^2)",
            f"= sqrt(({fmt_num(x2)} - {fmt_num(x1)})^2 + "
            f"({fmt_num(y2)} - {fmt_num(y1)})^2) = sqrt({fmt_num(d2)})",
            f"= {fmt_num(d)}",
        ]
        return "distance", fmt_num(d), steps

    if "midpoint" in q and len(pts) >= 2:
        (x1, y1), (x2, y2) = pts[0], pts[1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        steps = [
            "Midpoint = ((x1+x2)/2, (y1+y2)/2)",
            f"= (({fmt_num(x1)} + {fmt_num(x2)})/2, ({fmt_num(y1)} + "
            f"{fmt_num(y2)})/2) = ({fmt_num(mx)}, {fmt_num(my)})",
        ]
        return "midpoint", f"({fmt_num(mx)}, {fmt_num(my)})", steps

    if "slope" in q and len(pts) >= 2:
        (x1, y1), (x2, y2) = pts[0], pts[1]
        if x2 == x1:
            return "slope", "undefined (vertical line)", [
                "x2 - x1 = 0, so the slope is undefined."]
        m = (y2 - y1) / (x2 - x1)
        steps = [
            "Slope m = (y2 - y1) / (x2 - x1)",
            f"= ({fmt_num(y2)} - {fmt_num(y1)}) / ({fmt_num(x2)} - "
            f"{fmt_num(x1)}) = {fmt_num(m)}",
        ]
        return "slope", fmt_num(m), steps

    if "line" in q and ("equation" in q):
        if len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[0], pts[1]
            if x2 == x1:
                return "line equation", f"x = {fmt_num(x1)}", [
                    "Both points have the same x, so the line is vertical."]
            m = sp.Rational(y2 - y1, x2 - x1) if float(y2 - y1).is_integer() \
                and float(x2 - x1).is_integer() else (y2 - y1) / (x2 - x1)
            c = y1 - m * x1
            steps = [
                f"Slope m = ({fmt_num(y2)} - {fmt_num(y1)}) / "
                f"({fmt_num(x2)} - {fmt_num(x1)}) = {fmt_num(m)}",
                f"Use y - y1 = m(x - x1) through ({fmt_num(x1)}, "
                f"{fmt_num(y1)}).",
                f"y = {fmt_num(m)}·x + {fmt_num(c)}",
            ]
            ans = f"y = {fmt_num(m)}x" + (
                f" + {fmt_num(c)}" if c > 0 else
                f" - {fmt_num(abs(c))}" if c < 0 else "")
            return "line equation", ans, steps
        m = find_param(q, ["slope", "m"])
        if pts and m is not None:
            (x1, y1) = pts[0]
            c = y1 - m * x1
            steps = [
                f"Point-slope form: y - {fmt_num(y1)} = {fmt_num(m)}"
                f"(x - {fmt_num(x1)})",
                f"y = {fmt_num(m)}·x + {fmt_num(c)}",
            ]
            ans = f"y = {fmt_num(m)}x" + (
                f" + {fmt_num(c)}" if c > 0 else
                f" - {fmt_num(abs(c))}" if c < 0 else "")
            return "line equation", ans, steps

    if "circle" in q and "equation" in q:
        r = find_param(q, ["radius"])
        centre = pts[0] if pts else (0, 0)
        if r is not None:
            h, k = centre
            xs, ys = sp.symbols("x y")
            expr = (xs - h) ** 2 + (ys - k) ** 2
            steps = [
                "Standard form: (x - h)^2 + (y - k)^2 = r^2 with centre "
                f"({fmt_num(h)}, {fmt_num(k)}) and radius {fmt_num(r)}",
                f"(x - {fmt_num(h)})^2 + (y - {fmt_num(k)})^2 = "
                f"{fmt_num(r * r)}",
                f"Expanded: {fmt(sp.expand(expr))} = {fmt_num(r * r)}",
            ]
            return ("circle equation",
                    f"(x - {fmt_num(h)})^2 + (y - {fmt_num(k)})^2 = "
                    f"{fmt_num(r * r)}", steps)
    # ---- Wave 32 coordinate topics -----------------------------
    if "centroid" in q and len(pts) == 3:
        (x1, y1), (x2, y2), (x3, y3) = pts
        cx = (x1 + x2 + x3) / 3
        cy = (y1 + y2 + y3) / 3
        steps = [
            "Centroid = ((x1 + x2 + x3)/3, (y1 + y2 + y3)/3)",
            f"= (({x1} + {x2} + {x3})/3, ({y1} + {y2} + "
            f"{y3})/3) = ({cx}, {cy})",
        ]
        return "centroid", f"({cx}, {cy})", steps
    if "quadrilateral" in q and "area" in q and len(pts) == 4:
        s = 0.0
        for i in range(4):
            xa, ya = pts[i]
            xb, yb = pts[(i + 1) % 4]
            s += xa * yb - xb * ya
        val = abs(s) / 2
        steps = [
            "Area by the shoelace formula: half of |sum of "
            "x_i·y_(i+1) - x_(i+1)·y_i| over the vertices in "
            "order.",
            f"= (1/2) × |{s}| = {fmt_num(val)} square units",
        ]
        return "quadrilateral area", fmt_num(val), steps
    # Wave 33: find k for collinearity — one coordinate of
    # the three points is the unknown k, so extract_points
    # (numeric only) dropped that point and the check below
    # never fired. Collinearity ⟺ the determinant (twice
    # the signed area) is zero; that condition is linear
    # in k.
    if "collinear" in q:
        _raw = re.findall(
            r"\(\s*(-?\d+(?:\.\d+)?|k)\s*,\s*"
            r"(-?\d+(?:\.\d+)?|k)\s*\)", q)
        if len(_raw) == 3 and sum(v == "k" for p in _raw
                                  for v in p) == 1:
            _k = sp.Symbol("k")
            _pts = [tuple(_k if v == "k" else
                          sp.Rational(v) for v in p)
                    for p in _raw]
            (x1, y1), (x2, y2), (x3, y3) = _pts
            _det = (x1 * (y2 - y3) + x2 * (y3 - y1)
                    + x3 * (y1 - y2))
            _sol = sp.solve(_det, _k)
            if len(_sol) == 1:
                _disp = [f"({a}, {b})" for a, b in _raw]
                steps = [
                    "Three points are collinear exactly "
                    "when the area of the triangle they "
                    "form is zero.",
                    "Area condition: x1(y2 - y3) + "
                    "x2(y3 - y1) + x3(y1 - y2) = 0 with "
                    f"the points {_disp[0]}, {_disp[1]}, "
                    f"{_disp[2]}.",
                    f"Solving for k: k = {fmt(_sol[0])}",
                ]
                return ("collinearity",
                        f"k = {fmt(_sol[0])}", steps)
    if "collinear" in q and len(pts) == 3:
        (x1, y1), (x2, y2), (x3, y3) = pts
        area2 = abs(x1 * (y2 - y3) + x2 * (y3 - y1)
                    + x3 * (y1 - y2))
        steps = [
            "Three points are collinear exactly when the area "
            "of the triangle they form is zero.",
            f"Twice the area = |{x1}({y2} - {y3}) + {x2}({y3} "
            f"- {y1}) + {x3}({y1} - {y2})| = {fmt_num(area2)}",
        ]
        if area2 == 0:
            steps.append("The area is zero, so the points "
                         "ARE collinear.")
            return ("collinearity",
                    "Yes, the points are collinear", steps)
        steps.append("The area is not zero, so the points "
                     "are NOT collinear.")
        return ("collinearity",
                "No, the points are not collinear", steps)
    if len(pts) == 1 and ("from the origin" in q
                          or "from origin" in q):
        (px, py) = pts[0]
        val = math.sqrt(px * px + py * py)
        steps = [f"Distance from the origin = sqrt(x^2 + y^2) "
                 f"= sqrt({px}^2 + {py}^2) = {fmt_num(val)}"]
        return "distance from origin", fmt_num(val), steps
    if "equidistant" in q and "x-axis" in q and len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        if x1 == x2:
            return None
        xv = (x2 * x2 + y2 * y2 - x1 * x1 - y1 * y1) \
            / (2 * (x2 - x1))
        steps = [
            "Let the point on the x-axis be (x, 0). Equal "
            "distances give:",
            f"(x - {x1})^2 + {y1}^2 = (x - {x2})^2 + {y2}^2",
            f"Solving the linear equation: x = {xv}",
        ]
        return "equidistant point", f"({xv}, 0)", steps
    if "ratio" in q and "divide" in q and len(pts) >= 2:
        if ("x-axis" in q or "y-axis" in q) and len(pts) == 2:
            (x1, y1), (x2, y2) = pts
            if "x-axis" in q:
                if y2 == 0:
                    return None
                k = -y1 / y2
                coord, c1, c2 = "y", y1, y2
            else:
                if x2 == 0:
                    return None
                k = -x1 / x2
                coord, c1, c2 = "x", x1, x2
            steps = [
                f"Let the ratio be k : 1. The {coord}-"
                f"coordinate of the dividing point on the "
                f"axis is zero:",
                f"(k·{c2} + {c1}) / (k + 1) = 0, so "
                f"k = {fmt_num(k)}",
                f"So the axis divides the join in the ratio "
                f"{fmt_num(k)} : 1.",
            ]
            return ("ratio of division",
                    f"{fmt_num(k)} : 1", steps)
        if len(pts) == 3:
            (x1, y1), (x2, y2), (px, py) = pts
            if x2 != px:
                k = (px - x1) / (x2 - px)
            elif y2 != py:
                k = (py - y1) / (y2 - py)
            else:
                return None
            steps = [
                "Let the point divide the join in the ratio "
                "k : 1. By the section formula its coordinate "
                "is (k·x2 + x1)/(k + 1).",
                f"Equating with the point's coordinate gives "
                f"k = {fmt_num(k)}",
                f"So the point divides the join in the ratio "
                f"{fmt_num(k)} : 1.",
            ]
            return ("ratio of division",
                    f"{fmt_num(k)} : 1", steps)
    return None


def _circles_extra(q):
    """Wave 32 circle theorems: tangent length from an external
    point, angle between two tangents, chord distance from the
    centre."""
    # Wave 33: area between two concentric circles (ring /
    # annulus) — the generic circle branch had no form for
    # it and returned the "tell me the shape" shrug.
    if "concentric" in q or "ring" in q or "annulus" in q:
        _mr = re.search(r"radii\s+(?:of\s+)?"
                        r"(\d+(?:\.\d+)?)\s*(?:cm|m|mm)?\s*"
                        r"and\s+(\d+(?:\.\d+)?)", q)
        _rads = [float(_mr.group(1)), float(_mr.group(2))] \
            if _mr else [float(v) for v in re.findall(
                r"radius\s+(?:of\s+)?(?:the\s+)?\w*\s*(?:is\s+)?"
                r"(\d+(?:\.\d+)?)", q)]
        _mo = re.search(r"outer\s+radius\s+(?:is\s+)?"
                        r"(\d+(?:\.\d+)?)", q)
        _mi = re.search(r"inner\s+radius\s+(?:is\s+)?"
                        r"(\d+(?:\.\d+)?)", q)
        if _mo and _mi:
            _rads = [float(_mo.group(1)), float(_mi.group(1))]
        if len(_rads) == 2 and _rads[0] != _rads[1]:
            _R, _r = max(_rads), min(_rads)
            # Wave 56: a CHORD of the larger circle touching
            # the smaller is a different schema — the ring
            # branch used to answer its area (50.27) for the
            # chord question. Chord = 2√(R² − r²).
            if "chord" in q:
                _val = 2 * math.sqrt(_R * _R - _r * _r)
                steps = [
                    "The chord of the larger circle touches "
                    "the smaller circle, so the perpendicular "
                    "from the centre to the chord has length "
                    f"r = {fmt_num(_r)} and bisects the chord.",
                    f"Half the chord = sqrt(R^2 - r^2) = "
                    f"sqrt({fmt_num(_R * _R)} - "
                    f"{fmt_num(_r * _r)}) = "
                    f"{fmt_num(_val / 2)}",
                    f"Chord length = {fmt_num(_val)}",
                ]
                return "concentric chord", fmt_num(_val), steps
            if "area" in q or "ring" in q or "annulus" in q:
                # Wave 99: 22/7 only when BOTH radii qualify.
                _pi, _u227, _reason = pi_choice(radii=[_R, _r])
                _val = _pi * (_R * _R - _r * _r)
                _pit = "(22/7)" if _u227 else "π"
                steps = [
                    "Area between two concentric circles "
                    "= π(R^2 - r^2), with R the larger radius "
                    "and r the smaller.",
                    f"= {_pit}({fmt_num(_R)}^2 - {fmt_num(_r)}^2) "
                    f"= {_pit} × {fmt_num(_R * _R - _r * _r)} "
                    f"= {fmt_num(_val)}",
                ]
                if _u227:
                    steps = [pi_note(_reason)] + steps
                return ("ring area",
                        f"{fmt_num(_val)} square units", steps)
    if "tangent" in q and "length" in q:
        pts = extract_points(q)
        r = find_param(q, ["radius", "r"])
        if r is None:
            m = re.search(r"x\^2\s*\+\s*y\^2\s*=\s*"
                          r"(\d+(?:\.\d+)?)", q)
            if m:
                r = math.sqrt(float(m.group(1)))
        centre = (0.0, 0.0)
        mc = re.search(r"centre\s*(?:is|at)?\s*"
                       r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
                       r"(-?\d+(?:\.\d+)?)\s*\)", q)
        if mc:
            centre = (float(mc.group(1)), float(mc.group(2)))
        ext = None
        for p in pts:
            if p != centre:
                ext = p
        if r is None:
            return None
        if ext is not None:
            d = math.hypot(ext[0] - centre[0],
                           ext[1] - centre[1])
        else:
            # Wave 56: the distance may be stated numerically
            # with no point coordinates at all — "a point at
            # a distance of 13 cm from the centre of a circle
            # of radius 5 cm".
            _md = re.search(r"distance\s+of\s+"
                            r"(\d+(?:\.\d+)?)", q)
            if not _md:
                return None
            d = float(_md.group(1))
        if d <= r:
            return None
        val = math.sqrt(d * d - r * r)
        steps = [
            f"Distance of the point from the centre = "
            f"{fmt_num(d)}; radius = {fmt_num(r)}",
            "The radius to a point of contact is perpendicular "
            "to the tangent, so by Pythagoras:",
            f"Length of tangent = sqrt(d^2 - r^2) = "
            f"sqrt({fmt_num(d * d)} - {fmt_num(r * r)}) "
            f"= {fmt_num(val)}",
        ]
        return "tangent length", fmt_num(val), steps
    if "angle between" in q and "tangent" in q:
        r = find_param(q, ["radius", "r"])
        md = re.search(r"distance\s+of\s+(\d+(?:\.\d+)?)", q)
        if r is None or not md:
            return None
        d = float(md.group(1))
        if d <= r:
            return None
        half = math.degrees(math.asin(r / d))
        ang = 2 * half
        steps = [
            f"The line from the centre to the external point "
            f"bisects the angle between the tangents, and "
            f"sin(angle/2) = r/d = {fmt_num(r)}/{fmt_num(d)}",
            f"angle/2 = {half:.2f} degrees, so the angle "
            f"between the two tangents = {ang:.2f} degrees",
        ]
        return "angle between tangents", f"{ang:.2f} degrees", \
            steps
    if "chord" in q and ("distance" in q and "centre" in q
                         or "from the centre" in q):
        r = find_param(q, ["radius", "r"])
        ml = re.search(r"chord\s+of\s+length\s+"
                       r"(\d+(?:\.\d+)?)", q) or \
            re.search(r"length\s+(\d+(?:\.\d+)?)", q)
        if r is None or not ml:
            return None
        L = float(ml.group(1))
        if L > 2 * r:
            return None
        val = math.sqrt(r * r - (L / 2) ** 2)
        steps = [
            "The perpendicular from the centre bisects the "
            f"chord, so half the chord is {fmt_num(L / 2)}.",
            f"Distance from the centre = sqrt(r^2 - "
            f"(L/2)^2) = sqrt({fmt_num(r * r)} - "
            f"{fmt_num((L / 2) ** 2)}) = {fmt_num(val)}",
        ]
        return "chord distance", fmt_num(val), steps
    return None


_PT3 = r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*," \
       r"\s*(-?\d+(?:\.\d+)?)\s*\)"


def _points3(q):
    return [tuple(float(v) for v in t) for t in
            re.findall(_PT3, q)]


def _threed(q):
    """Wave 32 3D geometry (Class 12): direction ratios and
    cosines, angle between two lines, distance of a point from
    a plane, section formula / midpoint in 3D."""
    pts = _points3(q)
    if "direction ratios" in q or "direction cosines" in q:
        md = re.search(
            r"direction ratios (?:are )?(-?\d+(?:\.\d+)?)\s*,"
            r"\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
            r"\s+and\s+(-?\d+(?:\.\d+)?)\s*,\s*"
            r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", q)
        if "angle between" in q and md:
            a = [float(md.group(i)) for i in (1, 2, 3)]
            b = [float(md.group(i)) for i in (4, 5, 6)]
            dot = sum(x * y for x, y in zip(a, b))
            ma = math.sqrt(sum(x * x for x in a))
            mb = math.sqrt(sum(x * x for x in b))
            if ma == 0 or mb == 0:
                return None
            cos_t = abs(dot) / (ma * mb)
            ang = math.degrees(math.acos(max(-1.0,
                                             min(1.0, cos_t))))
            steps = [
                f"cos(theta) = |a1b1 + a2b2 + a3b3| / "
                f"(|a| |b|) = |{fmt_num(dot)}| / "
                f"({fmt_num(ma)} × {fmt_num(mb)}) "
                f"= {cos_t:.4f}",
                f"theta = {ang:.2f} degrees",
            ]
            return "angle between lines", f"{ang:.2f} " \
                "degrees", steps
        if len(pts) == 2:
            dr = tuple(pts[1][i] - pts[0][i] for i in range(3))
            if "direction cosines" in q:
                mag = math.sqrt(sum(v * v for v in dr))
                if mag == 0:
                    return None
                dc = tuple(v / mag for v in dr)
                steps = [
                    f"Direction ratios = "
                    f"({fmt_num(dr[0])}, {fmt_num(dr[1])}, "
                    f"{fmt_num(dr[2])}); magnitude = "
                    f"{fmt_num(mag)}",
                    "Direction cosines = each direction "
                    "ratio divided by the magnitude:",
                    f"= ({dc[0]:.4f}, {dc[1]:.4f}, "
                    f"{dc[2]:.4f})",
                ]
                return ("direction cosines",
                        f"({dc[0]:.4f}, {dc[1]:.4f}, "
                        f"{dc[2]:.4f})", steps)
            steps = [
                "Direction ratios are the differences of the "
                "coordinates:",
                f"= ({fmt_num(pts[1][0])} - "
                f"{fmt_num(pts[0][0])}, {fmt_num(pts[1][1])} "
                f"- {fmt_num(pts[0][1])}, "
                f"{fmt_num(pts[1][2])} - "
                f"{fmt_num(pts[0][2])})",
            ]
            return ("direction ratios",
                    f"({fmt_num(dr[0])}, {fmt_num(dr[1])}, "
                    f"{fmt_num(dr[2])})", steps)
        return None
    if "plane" in q and "distance" in q and len(pts) == 1:
        mp = re.search(r"plane\s+(.+?)(?:\.|$)", q)
        if not mp:
            return None
        text = mp.group(1).replace(" ", "")
        lhs, _, rhs = text.partition("=")
        rhs_v = float(rhs) if rhs else 0.0

        def _coef(var):
            m = re.search(r"([+-]?\d*(?:\.\d+)?)" + var, lhs)
            if not m:
                return 0.0
            s = m.group(1)
            if s in ("", "+"):
                return 1.0
            if s == "-":
                return -1.0
            return float(s)

        a, b, c = _coef("x"), _coef("y"), _coef("z")
        rest = re.sub(r"[+-]?\d*(?:\.\d+)?[xyz]", "", lhs)
        d0 = 0.0
        if rest not in ("", "+", "-"):
            d0 = float(rest)
        elif rest == "-":
            d0 = 0.0
        denom = math.sqrt(a * a + b * b + c * c)
        if denom == 0:
            return None
        (x0, y0, z0) = pts[0]
        num = abs(a * x0 + b * y0 + c * z0 + d0 - rhs_v)
        val = num / denom
        steps = [
            f"Distance = |a·x0 + b·y0 + c·z0 + d| / "
            f"sqrt(a^2 + b^2 + c^2)",
            f"= |{fmt_num(a)}×{fmt_num(x0)} + "
            f"{fmt_num(b)}×{fmt_num(y0)} + "
            f"{fmt_num(c)}×{fmt_num(z0)} + "
            f"{fmt_num(d0 - rhs_v)}| / {fmt_num(denom)} "
            f"= {fmt_num(val)}",
        ]
        return "point plane distance", fmt_num(val), steps
    if len(pts) == 2 and ("ratio" in q or "midpoint" in q
                          or "mid-point" in q):
        (x1, y1, z1), (x2, y2, z2) = pts
        if "midpoint" in q or "mid-point" in q:
            mid = ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2)
            steps = [f"Midpoint = (({x1} + {x2})/2, ({y1} + "
                     f"{y2})/2, ({z1} + {z2})/2)"]
            return ("midpoint 3d",
                    f"({fmt_num(mid[0])}, {fmt_num(mid[1])}, "
                    f"{fmt_num(mid[2])})", steps)
        mr = re.search(r"ratio\s+(\d+(?:\.\d+)?)\s*:\s*"
                       r"(\d+(?:\.\d+)?)", q)
        if not mr:
            return None
        m_, n_ = float(mr.group(1)), float(mr.group(2))
        px = (m_ * x2 + n_ * x1) / (m_ + n_)
        py = (m_ * y2 + n_ * y1) / (m_ + n_)
        pz = (m_ * z2 + n_ * z1) / (m_ + n_)
        steps = [
            f"Section formula (internal division, ratio "
            f"{fmt_num(m_)} : {fmt_num(n_)}): each coordinate "
            f"is (m·(second) + n·(first)) / (m + n)",
            f"= ({fmt_num(px)}, {fmt_num(py)}, "
            f"{fmt_num(pz)})",
        ]
        return ("section formula 3d",
                f"({fmt_num(px)}, {fmt_num(py)}, "
                f"{fmt_num(pz)})", steps)
    return None


def _sqrt_answer(sq):
    """(answer_text, value) for sqrt(sq): exact integer when sq
    is a perfect square, else the surd with a decimal."""
    r = math.isqrt(int(sq)) if float(sq).is_integer() else None
    if r is not None and r * r == int(sq):
        return str(r), float(r)
    val = math.sqrt(sq)
    return f"√{fmt_num(sq)} ≈ {val:.4f}", val


def _pythagoras(q):
    """Wave 38: Pythagoras theorem — the audit found NO pattern
    at all (0/6 exact, Wave 35 #352-356, #430): hypotenuse from
    two legs, a leg from hypotenuse + other leg, rectangle /
    square diagonals, and the right-angle check (EN + Hindi).
    """
    # Hindi right-angle check: three side lengths + समकोण.
    if "समकोण" in q:
        nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", q)]
        if len(nums) >= 3:
            a, b, c = sorted(nums[:3])
            steps = [
                f"भुजाएँ: {fmt_num(a)}, {fmt_num(b)}, "
                f"{fmt_num(c)} (सबसे बड़ी भुजा = {fmt_num(c)})",
                f"{fmt_num(a)}^2 + {fmt_num(b)}^2 = "
                f"{fmt_num(a * a + b * b)} और "
                f"{fmt_num(c)}^2 = {fmt_num(c * c)}",
            ]
            if a * a + b * b == c * c:
                steps.append("दोनों बराबर हैं, इसलिए पाइथागोरस "
                             "प्रमेय से यह समकोण त्रिभुज है।")
                return ("pythagoras_check",
                        "Yes, it is a right-angled triangle",
                        steps)
            steps.append("दोनों बराबर नहीं हैं, इसलिए यह "
                         "समकोण त्रिभुज नहीं है।")
            return ("pythagoras_check",
                    "No, it is not a right-angled triangle",
                    steps)
        return None

    if "hypotenuse" in q:
        mh = re.search(r"hypotenuse\s*(?:is\s*)?(\d+(?:\.\d+)?)",
                       q)
        ml = re.search(r"(?:one\s+)?leg\s*(?:is\s*)?"
                       r"(\d+(?:\.\d+)?)", q)
        if mh and ml:
            H, L = float(mh.group(1)), float(ml.group(1))
            if H > L:
                ans, _v = _sqrt_answer(H * H - L * L)
                steps = [
                    "Pythagoras theorem: hypotenuse^2 = "
                    "leg1^2 + leg2^2",
                    f"Other leg = sqrt({fmt_num(H)}^2 - "
                    f"{fmt_num(L)}^2) = sqrt({fmt_num(H * H)} - "
                    f"{fmt_num(L * L)})",
                    f"= {ans}",
                ]
                return ("pythagoras_leg", ans, steps)
        nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", q)]
        if "leg" in q and len(nums) >= 2:
            a, b = nums[0], nums[1]
            ans, _v = _sqrt_answer(a * a + b * b)
            steps = [
                "Pythagoras theorem: hypotenuse^2 = "
                "leg1^2 + leg2^2",
                f"= {fmt_num(a)}^2 + {fmt_num(b)}^2 = "
                f"{fmt_num(a * a)} + {fmt_num(b * b)} = "
                f"{fmt_num(a * a + b * b)}",
                f"Hypotenuse = {ans}",
            ]
            return ("pythagoras_hypotenuse", ans, steps)
        # Wave 57: the legs named as base / perpendicular —
        # "find the hypotenuse if base is 3 and perpendicular
        # is 4" (no hypotenuse value given, so mh is None).
        if mh is None and len(nums) >= 2 and (
                "base" in q or "perpendicular" in q):
            a, b = nums[0], nums[1]
            ans, _v = _sqrt_answer(a * a + b * b)
            steps = [
                "Pythagoras theorem: hypotenuse^2 = "
                "base^2 + perpendicular^2",
                f"= {fmt_num(a)}^2 + {fmt_num(b)}^2 = "
                f"{fmt_num(a * a)} + {fmt_num(b * b)} = "
                f"{fmt_num(a * a + b * b)}",
                f"Hypotenuse = {ans}",
            ]
            return ("pythagoras_hypotenuse", ans, steps)

    if "diagonal" in q and "rectangle" in q:
        ml = re.search(r"length\s*(?:is\s*)?(\d+(?:\.\d+)?)", q)
        mb = re.search(r"(?:breadth|width)\s*(?:is\s*)?"
                       r"(\d+(?:\.\d+)?)", q)
        if ml and mb:
            a, b = float(ml.group(1)), float(mb.group(1))
            ans, _v = _sqrt_answer(a * a + b * b)
            steps = [
                "The diagonal splits the rectangle into two "
                "right triangles, so Pythagoras applies: "
                "diagonal^2 = length^2 + breadth^2",
                f"= {fmt_num(a)}^2 + {fmt_num(b)}^2 = "
                f"{fmt_num(a * a + b * b)}",
                f"Diagonal = {ans}",
            ]
            return ("pythagoras_diagonal", ans, steps)
    if "diagonal" in q and "square" in q:
        ms = re.search(r"side\s*(?:is\s*)?(\d+(?:\.\d+)?)", q)
        if ms:
            s = float(ms.group(1))
            ans, _v = _sqrt_answer(2 * s * s)
            steps = [
                "Diagonal of a square = side × √2 (Pythagoras "
                "on the two equal sides)",
                f"= {fmt_num(s)} × √2 = {ans}",
            ]
            return ("pythagoras_diagonal", ans, steps)

    # English right-angle check from three sides.
    if "right" in q and "side" in q and (
            "?" in q or "whether" in q or "check" in q):
        nums = [float(v) for v in re.findall(r"\d+(?:\.\d+)?", q)]
        if len(nums) >= 3:
            a, b, c = sorted(nums[:3])
            steps = [
                f"Sides: {fmt_num(a)}, {fmt_num(b)}, "
                f"{fmt_num(c)}; the largest side "
                f"{fmt_num(c)} would be the hypotenuse.",
                f"{fmt_num(a)}^2 + {fmt_num(b)}^2 = "
                f"{fmt_num(a * a + b * b)} and {fmt_num(c)}^2 "
                f"= {fmt_num(c * c)}",
            ]
            if a * a + b * b == c * c:
                steps.append("They are equal, so by the "
                             "Pythagoras theorem the triangle "
                             "IS right-angled.")
                return ("pythagoras_check",
                        "Yes, it is a right-angled triangle",
                        steps)
            steps.append("They are not equal, so the triangle "
                         "is NOT right-angled.")
            return ("pythagoras_check",
                    "No, it is not a right-angled triangle",
                    steps)
    return None


def _centre_letter(q):
    """The letter naming the circle's centre: stated ("point o
    is the centre") or the conventional o."""
    m = re.search(r"point\s+([a-z])\s+is\s+the\s+cent", q)
    if m:
        return m.group(1)
    return "o"


def _one_angle(q):
    """The single "∠xyz = θ" fact in the text, as
    (arm1, vertex, arm2, degrees), or None when there is not
    exactly one."""
    hits = [(m.group(1), m.group(2), m.group(3),
             float(m.group(4))) for m in re.finditer(
        r"∠\s*([a-z])\s*([a-z])\s*([a-z])\s*=\s*"
        r"(\d+(?:\.\d+)?)\s*°?", q)]
    return hits[0] if len(hits) == 1 else None


def _radii_base_angle(q):
    """Wave 100: the isosceles triangle two radii make with a
    chord — "point O is the centre of the circle and ∠AOB =
    30°, find ∠OBA". OA and OB are radii, so the base angles
    are equal and the angle sum does the rest. The Wave 93
    audit's regression #7: this papers MCQ fell to NOT_FOUND
    because no schema read the figure's facts out of the text
    (the facts ARE all in the text — centre, one angle, the
    asked angle). Both directions: vertex angle given -> base
    angle (180 - θ)/2; base angle given -> vertex 180 - 2β."""
    if "centre of the circle" not in q and \
            "center of the circle" not in q:
        return None
    centre = _centre_letter(q)
    got = _one_angle(q)
    if got is None:
        return None
    g1, gv, g2, given = got
    letters = {g1, gv, g2}
    if len(letters) != 3 or centre not in letters:
        return None
    endpoints = letters - {centre}
    m = re.search(
        r"(?:find|value\s+of|calculate)\s+(?:the\s+)?"
        r"(?:value\s+of\s+)?∠\s*([a-z])\s*([a-z])\s*([a-z])",
        q)
    if not m:
        return None
    a1, av, a2 = m.group(1), m.group(2), m.group(3)
    if {a1, av, a2} != letters:
        return None
    e1, e2 = sorted(endpoints)
    radii_step = (
        f"{centre.upper()}{e1.upper()} and "
        f"{centre.upper()}{e2.upper()} are radii of the same "
        "circle, so they are equal and the triangle is "
        "isosceles — its base angles are equal.")
    if gv == centre and av in endpoints:
        val = (180.0 - given) / 2.0
        steps = [
            radii_step,
            f"∠{a1.upper()}{av.upper()}{a2.upper()} = "
            f"(180° - ∠{g1.upper()}{gv.upper()}{g2.upper()})/2",
            f"= (180° - {fmt_num(given)}°)/2 = "
            f"{fmt_num(val)}°",
        ]
        return "radii base angle", f"{fmt_num(val)}°", steps
    if av == centre and gv in endpoints:
        val = 180.0 - 2.0 * given
        steps = [
            radii_step,
            f"∠{a1.upper()}{av.upper()}{a2.upper()} = 180° - "
            f"2 × ∠{g1.upper()}{gv.upper()}{g2.upper()}",
            f"= 180° - 2 × {fmt_num(given)}° = "
            f"{fmt_num(val)}°",
        ]
        return "radii vertex angle", f"{fmt_num(val)}°", steps
    return None


def _tangent_from_angle(q):
    """Wave 100: a tangent's length from the radius and ONE
    angle of the right triangle (centre, touch point,
    external point) — the Class 10 circles staple behind the
    Wave 93 audit's discus-throw case study (regression #3):
    "AB is a tangent to a circle of radius 75 cm, O is the
    centre and ∠ABO = 30°. Find the length of AB / OB." The
    radius to the touch point is perpendicular to the tangent,
    so tan/sin/cos of the given angle settle every side. The
    asked segment is the LAST "length of XY" in the text (a
    case-study passage carries the facts; the sub-question
    carries the ask). Only this triangle's own segments are
    served — a segment naming any other point (AP, PQ in the
    case study) returns None, honestly unsolved."""
    if "tangent" not in q:
        return None
    mr = re.search(r"radius\s+(?:of\s+)?(?:the\s+|a\s+)?"
                   r"(?:circle\s+)?(?:is\s+)?"
                   r"(\d+(?:\.\d+)?)\s*(cm|mm|m|km)?", q)
    if not mr:
        return None
    radius = float(mr.group(1))
    unit = (" " + mr.group(2)) if mr.group(2) else ""
    centre = _centre_letter(q)
    got = _one_angle(q)
    if got is None:
        return None
    g1, gv, g2, theta = got
    letters = {g1, gv, g2}
    if len(letters) != 3 or centre not in letters:
        return None
    # The tangent segment: named in the text ("AB is one such
    # tangent") or read off the angle's non-centre letters.
    mt = re.search(r"([a-z])([a-z])\s+is\s+(?:one\s+such\s+)?"
                   r"(?:a\s+)?tangent", q)
    if mt:
        tangent_pair = {mt.group(1), mt.group(2)}
    else:
        tangent_pair = letters - {centre}
    if len(tangent_pair) != 2 or centre in tangent_pair:
        return None
    if gv == centre:
        at_centre = True
        external = None  # either tangent letter; set below
        touch = None
    elif centre in (g1, g2):
        at_centre = False
        external = gv
        touch = g2 if g1 == centre else g1
        if {touch, external} != tangent_pair:
            return None
    else:
        return None
    asks = list(re.finditer(
        r"length\s+of\s+([a-z])\s*([a-z])\b", q))
    if not asks:
        return None
    segment = {asks[-1].group(1), asks[-1].group(2)}
    if segment == tangent_pair:
        kind = "tangent"
    elif len(segment) == 2 and centre in segment and \
            (segment - {centre}) <= tangent_pair:
        kind = "centre-line"
        external = (segment - {centre}).pop()
        touch = (tangent_pair - {external}).pop()
    elif external is not None and segment == {centre, touch}:
        kind = "radius"
    else:
        return None
    if kind == "radius":
        steps = [
            "That segment is a radius of the circle, so its "
            f"length is {fmt_num(radius)}{unit}.",
        ]
        return ("tangent radius segment",
                f"{fmt_num(radius)}{unit}", steps)
    tri = (f"{centre.upper()}{touch.upper()}"
           f"{external.upper()}")
    ang = f"∠{g1.upper()}{gv.upper()}{g2.upper()}"
    head = [
        f"{centre.upper()}{touch.upper()} ⊥ "
        f"{touch.upper()}{external.upper()} — the radius to "
        "the point of contact is perpendicular to the tangent, "
        f"so △{tri} is right-angled at {touch.upper()}.",
    ]
    rad = math.radians(theta)
    seg_name = f"{touch.upper()}{external.upper()}"
    if kind == "tangent":
        if at_centre:
            val = radius * math.tan(rad)
            steps = head + [
                f"tan({ang}) = {seg_name}/"
                f"{centre.upper()}{touch.upper()}, so "
                f"{seg_name} = {fmt_num(radius)} × "
                f"tan({fmt_num(theta)}°) = {fmt_num(val)}",
            ]
        else:
            val = radius / math.tan(rad)
            steps = head + [
                f"tan({ang}) = {centre.upper()}{touch.upper()}"
                f"/{seg_name}, so {seg_name} = "
                f"{fmt_num(radius)}/tan({fmt_num(theta)}°)",
            ]
            if theta == 30.0:
                steps.append(
                    f"= {fmt_num(radius)}√3 ≈ {val:.4f}")
                return ("tangent length from angle",
                        f"{fmt_num(radius)}√3{unit} ≈ "
                        f"{val:.4f}{unit}", steps)
            steps.append(f"= {fmt_num(val)}")
        return ("tangent length from angle",
                f"{fmt_num(val)}{unit}", steps)
    # centre-line (the hypotenuse)
    if at_centre:
        val = radius / math.cos(rad)
        steps = head + [
            f"cos({ang}) = {centre.upper()}{touch.upper()}/"
            f"{centre.upper()}{external.upper()}, so "
            f"{centre.upper()}{external.upper()} = "
            f"{fmt_num(radius)}/cos({fmt_num(theta)}°) = "
            f"{fmt_num(val)}",
        ]
    else:
        val = radius / math.sin(rad)
        steps = head + [
            f"sin({ang}) = {centre.upper()}{touch.upper()}/"
            f"{centre.upper()}{external.upper()}, so "
            f"{centre.upper()}{external.upper()} = "
            f"{fmt_num(radius)}/sin({fmt_num(theta)}°) = "
            f"{fmt_num(val)}",
        ]
    return ("tangent centre distance from angle",
            f"{fmt_num(val)}{unit}", steps)


def _vec56_parse(q):
    """One vector from '2i + 3j + 6k' or '(1, 2, 3)' form."""
    m = re.search(_PT3, q)
    if m:
        return tuple(float(v) for v in m.groups())
    comps = {}
    for val, axis in re.findall(
            r"([+-]?\s*\d+(?:\.\d+)?)\s*([ijk])\b", q):
        comps[axis] = float(val.replace(" ", ""))
    if comps and ("i" in comps or "j" in comps):
        return (comps.get("i", 0.0), comps.get("j", 0.0),
                comps.get("k", 0.0))
    return None


def _vectors56(q):
    """Wave 56: vector basics (Class 12) — magnitude, unit
    vector, dot product, 3D distance. No vector code existed
    anywhere; these questions were hijacked by unrelated
    intents (complex numbers read '2i + 3j' as algebra)."""
    if "dot product" in q:
        pts = _points3(q)
        if len(pts) >= 2:
            a, b = pts[0], pts[1]
        elif " and " in q:
            _l, _r = q.split(" and ", 1)
            a, b = _vec56_parse(_l), _vec56_parse(_r)
        else:
            a = b = None
        if a and b:
            val = sum(x * y for x, y in zip(a, b))
            steps = [
                "Dot product = sum of the products of "
                "corresponding components",
                " = " + " + ".join(
                    f"({fmt_num(x)} × {fmt_num(y)})"
                    for x, y in zip(a, b))
                + f" = {fmt_num(val)}",
            ]
            return "dot product", fmt_num(val), steps
        return None
    if "unit vector" in q:
        v = _vec56_parse(q)
        if v:
            mag = math.sqrt(sum(x * x for x in v))
            if mag == 0:
                return None
            s = ""
            for c, ax in zip(v, "ijk"):
                if c == 0:
                    continue
                u = c / mag
                term = f"{fmt_num(round(abs(u), 4))}{ax}"
                if not s:
                    s = ("-" if u < 0 else "") + term
                else:
                    s += (" - " if u < 0 else " + ") + term
            steps = [
                f"|v| = sqrt({' + '.join(fmt_num(x) + '^2' for x in v)}) "
                f"= {fmt_num(mag)}",
                "Unit vector = v / |v|",
            ]
            return "unit vector", s, steps
        return None
    if "magnitude" in q and "vector" in q:
        v = _vec56_parse(q)
        if v:
            val = math.sqrt(sum(x * x for x in v))
            steps = [
                f"|v| = sqrt({' + '.join(fmt_num(x) + '^2' for x in v)})",
                f"= sqrt({fmt_num(sum(x * x for x in v))}) "
                f"= {fmt_num(val)}",
            ]
            return "vector magnitude", fmt_num(val), steps
        return None
    if "distance" in q and "origin" in q:
        pts = _points3(q)
        if pts:
            v = pts[0]
            val = math.sqrt(sum(x * x for x in v))
            steps = [
                "Distance of a point from the origin = "
                "sqrt(x^2 + y^2 + z^2)",
                f"= sqrt({' + '.join(fmt_num(x) + '^2' for x in v)}) "
                f"= {fmt_num(round(val, 4))}",
            ]
            return "distance from origin", \
                fmt_num(round(val, 4)), steps
    return None


_DEV_DIGITS_HI = str.maketrans("०१२३४५६७८९", "0123456789")
_NUM_HI = r"(\d+(?:\.\d+)?)"


def _mensuration_hindi(q: str):
    """Wave 57: Devanagari mensuration — "एक वृत्त की त्रिज्या
    7 सेमी है, उसका क्षेत्रफल निकालो". The English patterns in
    _area_perimeter_volume never match Hindi text, so these asks
    fell to the arithmetic simplifier (letter-soup) or a similar
    example. Same formulas, same answer formats, Hindi steps."""
    q = q.translate(_DEV_DIGITS_HI)

    def _val(m):
        v = float(m.group(1))
        return int(v) if v == int(v) else v

    if "वृत्त" in q:
        m = re.search(r"त्रिज्या\s*" + _NUM_HI, q)
        if m:
            r = _val(m)
            _pi, _u227, _reason = pi_choice(radius=r)
            _note = [pi_note_hi()] if _u227 else []
            if "परिधि" in q:
                val = 2 * _pi * r
                if _u227:
                    steps = _note + [
                        f"परिधि = 2·pi·r = 2 × (22/7) × "
                        f"{fmt_num(r)}",
                        f"= {fmt_num(val)}",
                    ]
                    return "circumference", fmt_num(val), steps
                steps = [
                    f"परिधि = 2·pi·r = 2 × pi × {fmt_num(r)}",
                    f"= {fmt_num(2 * r)}·pi ≈ {val:.4f}",
                ]
                return "circumference", \
                    f"{fmt_num(2 * r)}·pi ≈ {val:.4f}", steps
            if "क्षेत्रफल" in q:
                val = _pi * r * r
                if _u227:
                    steps = _note + [
                        f"क्षेत्रफल = pi·r^2 = (22/7) × "
                        f"{fmt_num(r)}^2 = (22/7) × "
                        f"{fmt_num(r * r)}",
                        f"= {fmt_num(val)}",
                    ]
                    return "area", fmt_num(val), steps
                steps = [
                    f"क्षेत्रफल = pi·r^2 = pi × {fmt_num(r)}^2 "
                    f"= pi × {fmt_num(r * r)}",
                    f"= {fmt_num(r * r)}·pi ≈ {val:.4f}",
                ]
                return "area", f"{fmt_num(r * r)}·pi ≈ {val:.4f}", \
                    steps
    if "आयत" in q and "क्षेत्रफल" in q:
        ml = re.search(r"लंबाई\s*" + _NUM_HI, q)
        mb = re.search(r"चौड़ाई\s*" + _NUM_HI, q)
        if ml and mb:
            l, b = _val(ml), _val(mb)
            steps = [
                f"आयत का क्षेत्रफल = लंबाई × चौड़ाई "
                f"= {fmt_num(l)} × {fmt_num(b)} = {fmt_num(l * b)}",
            ]
            return "area", fmt_num(l * b), steps
    if "वर्ग" in q and "भुजा" in q:
        m = re.search(r"भुजा\s*" + _NUM_HI, q)
        if m:
            s = _val(m)
            if "परिमाप" in q:
                steps = [
                    f"वर्ग का परिमाप = 4 × भुजा = 4 × "
                    f"{fmt_num(s)} = {fmt_num(4 * s)}",
                ]
                return "perimeter", fmt_num(4 * s), steps
            if "क्षेत्रफल" in q:
                steps = [
                    f"वर्ग का क्षेत्रफल = भुजा^2 = {fmt_num(s)}^2 "
                    f"= {fmt_num(s * s)}",
                ]
                return "area", fmt_num(s * s), steps
    if "त्रिभुज" in q and "क्षेत्रफल" in q:
        mb = re.search(r"आधार\s*" + _NUM_HI, q)
        mh = re.search(r"ऊ[ँं]चाई\s*" + _NUM_HI, q)
        if mb and mh:
            b, h = _val(mb), _val(mh)
            val = b * h / 2
            steps = [
                f"त्रिभुज का क्षेत्रफल = (1/2) × आधार × ऊँचाई",
                f"= (1/2) × {fmt_num(b)} × {fmt_num(h)} "
                f"= {fmt_num(val)}",
            ]
            return "area", fmt_num(val), steps
    return None


def _wave65_geometry(q):
    """Wave 65: mensuration / coordinate forms the trilingual
    batteries exposed — each gated on its own ask phrase
    (slant height, one revolution, other side, ...), running
    before the solid-volume paths that used to steal the
    cone slant ask and answer a volume instead."""
    N = r"(-?\d+(?:\.\d+)?)"

    def _res(op, answer, value, steps):
        # solve_geometry's chain carries (op, answer, steps)
        # tuples; the numeric value rides in the answer text.
        return (op, answer, steps)

    # Sentence form: "the length of a rectangle is L and
    # its width/breadth is B, find the perimeter/area".
    m = re.search(r"length\s+of\s+a\s+rectangle\s+is\s+" + N +
                  r"\s*(?:cm|m)?\s+and\s+(?:its\s+)?"
                  r"(?:width|breadth)\s+is\s+" + N, q)
    if m:
        _l, _b = float(m.group(1)), float(m.group(2))
        if "perimeter" in q:
            _p = 2 * (_l + _b)
            return _res("rectangle_perimeter_sentence",
                        fmt_num(_p), _p,
                        [f"Perimeter = 2 × ({fmt_num(_l)} + "
                         f"{fmt_num(_b)}) = {fmt_num(_p)}"])
        if "area" in q:
            _a = _l * _b
            return _res("rectangle_area_sentence",
                        fmt_num(_a), _a,
                        [f"Area = {fmt_num(_l)} × "
                         f"{fmt_num(_b)} = {fmt_num(_a)}"])
    # Radius from a stated diameter.
    m = re.search(r"diameter\s+(?:of\s+(?:a|the)\s+\w+\s+)?"
                  r"is\s+" + N, q)
    if m and "radius" in q and "area" not in q \
            and not wants_circumference(q):
        d = float(m.group(1))
        return _res("radius_from_diameter", fmt_num(d / 2),
                    d / 2,
                    [f"Radius = diameter / 2 = {fmt_num(d)} "
                     f"/ 2 = {fmt_num(d / 2)}"])
    # Cone slant height: l = sqrt(r^2 + h^2). Only when the
    # slant height is the ASK: a surface-area question hands
    # it over as data, and its "slant height N" must not be
    # re-read as the vertical height.
    if "slant height" in q and "cone" in q \
            and "surface area" not in q:
        mr = re.search(r"radius\s+(?:is\s+)?" + N, q)
        mh = re.search(r"(?<!slant )height\s+(?:is\s+)?" + N,
                       q)
        if mr and mh:
            r, h = float(mr.group(1)), float(mh.group(1))
            ln = math.hypot(r, h)
            return _res("cone_slant_height", fmt_num(ln), ln,
                        [f"Slant height l = √(r² + h²) = "
                         f"√({fmt_num(r)}² + {fmt_num(h)}²) = "
                         f"√{fmt_num(r * r + h * h)} = "
                         f"{fmt_num(ln)}"])
    # Ladder against a wall (Pythagoras, either leg asked).
    m = re.search(r"ladder\s+(?:is\s+)?" + N + r"\s*(?:m|cm|"
                  r"metres?|meters?|ft)?\s*long", q)
    if m:
        lad = float(m.group(1))
        mh = re.search(r"(?:reaching|at)\s+(?:a\s+)?height\s+"
                       r"(?:of\s+)?" + N, q) or \
            re.search(N + r"\s*(?:m|cm|metres?|meters?)?\s+"
                      r"high\b", q)
        mf = re.search(r"foot\s+(?:is\s+)?" + N +
                       r"\s*(?:m|cm)?\s*(?:away\s+)?from\s+the"
                       r"\s+wall", q)
        if mh and ("foot" in q or "distance" in q):
            h = float(mh.group(1))
            foot = math.sqrt(max(lad * lad - h * h, 0))
            return _res("ladder_foot", fmt_num(foot), foot,
                        [f"The ladder is the hypotenuse: "
                         f"foot² = {fmt_num(lad)}² - "
                         f"{fmt_num(h)}² = "
                         f"{fmt_num(lad * lad - h * h)}",
                         f"Foot from the wall = {fmt_num(foot)}"])
        if mf and ("height" in q or "reach" in q):
            fd = float(mf.group(1))
            h = math.sqrt(max(lad * lad - fd * fd, 0))
            return _res("ladder_height", fmt_num(h), h,
                        [f"Height² = {fmt_num(lad)}² - "
                         f"{fmt_num(fd)}² = "
                         f"{fmt_num(lad * lad - fd * fd)}",
                         f"Height reached = {fmt_num(h)}"])
    # Rectangle: diagonal and one side -> the other side.
    m = re.search(r"diagonal\s+of\s+a\s+rectangle\s+is\s+" + N,
                  q)
    ms = re.search(r"(?:one\s+side|length|breadth|width)\s+"
                   r"(?:is\s+)?" + N, q)
    if m and ms and ("other side" in q or "other" in q):
        dg, sd = float(m.group(1)), float(ms.group(1))
        other = math.sqrt(max(dg * dg - sd * sd, 0))
        return _res("rectangle_other_side", fmt_num(other),
                    other,
                    [f"Other side = √(diagonal² - side²) = "
                     f"√({fmt_num(dg)}² - {fmt_num(sd)}²) = "
                     f"√{fmt_num(dg * dg - sd * sd)} = "
                     f"{fmt_num(other)}"])
    # Cube side from its volume.
    m = re.search(r"volume\s+of\s+a\s+cube\s+is\s+" + N, q)
    if m and "side" in q:
        v = float(m.group(1))
        k = round(v ** (1 / 3))
        side = float(k) if k ** 3 == v else round(
            v ** (1 / 3), 2)
        return _res("cube_side_from_volume", fmt_num(side),
                    side,
                    [f"Side = ∛(volume) = ∛{fmt_num(v)} = "
                     f"{fmt_num(side)}"])
    # Radius from a stated circumference.
    m = re.search(r"circumference\s+of\s+a\s+circle\s+is\s+"
                  + N, q)
    if m and "radius" in q:
        c = float(m.group(1))
        # Wave 99: C a multiple of 22 -> r = 7C/44 exactly
        # with pi = 22/7 (Fraction arithmetic).
        _pi, _u227, _reason = pi_choice(circumference=c)
        if _u227:
            rf = (Fraction(c).limit_denominator(10 ** 6)
                  / (2 * PI_227))
            return _res("radius_from_circumference",
                        _fmt_frac(rf), float(rf),
                        [pi_note(_reason),
                         f"C = 2πr, so r = C / (2π) = "
                         f"{fmt_num(c)} / (2 × 22/7) = "
                         f"{_fmt_frac(rf)}"])
        r = c / (2 * PI)
        return _res("radius_from_circumference", fmt_num(r), r,
                    [f"C = 2πr, so r = C / (2π) = "
                     f"{fmt_num(c)} / {fmt_num(2 * PI)} = "
                     f"{fmt_num(r)}"])
    # Rectangle: breadth (or length) from area and one side.
    if "rectangle" in q and "area" in q:
        ma = re.search(r"area\s+(?:is\s+|of\s+)?" + N, q)
        ml = re.search(r"length\s+(?:is\s+)?" + N, q)
        mb = re.search(r"breadth\s+(?:is\s+)?" + N, q)
        if ma and ml and "breadth" in q.split("find")[-1] \
                and not mb:
            a, ln = float(ma.group(1)), float(ml.group(1))
            if ln:
                return _res("breadth_from_area",
                            fmt_num(a / ln), a / ln,
                            [f"Breadth = area / length = "
                             f"{fmt_num(a)} / {fmt_num(ln)} = "
                             f"{fmt_num(a / ln)}"])
        if ma and mb and "length" in q.split("find")[-1] \
                and not ml:
            a, bd = float(ma.group(1)), float(mb.group(1))
            if bd:
                return _res("length_from_area",
                            fmt_num(a / bd), a / bd,
                            [f"Length = area / breadth = "
                             f"{fmt_num(a)} / {fmt_num(bd)} = "
                             f"{fmt_num(a / bd)}"])
    # Area scale when the radius is multiplied.
    m = re.search(r"radius\s+of\s+a\s+circle\s+is\s+"
                  r"(doubled|tripled|quadrupled|halved)", q)
    if m and "area" in q and "how many times" in q:
        k = {"doubled": 2, "tripled": 3, "quadrupled": 4,
             "halved": 0.5}[m.group(1)]
        return _res("area_scale", fmt_num(k * k), float(k * k),
                    [f"Area grows with the SQUARE of the "
                     f"radius: {fmt_num(k)}² = "
                     f"{fmt_num(k * k)} times"])
    # A wheel's one revolution = its circumference.
    m = re.search(r"diameter\s+of\s+(?:a|the)\s+wheel\s+is\s+"
                  + N, q) or re.search(
        r"wheel[^.]{0,30}?diameter\s+(?:is\s+)?" + N, q)
    if m and "revolution" in q:
        d = float(m.group(1))
        _pi, _u227, _reason = pi_choice(diameter=d)
        dist = _pi * d
        _pit = "(22/7)" if _u227 else "π"
        return _res("wheel_revolution", fmt_num(dist), dist,
                    [f"In one revolution the wheel covers "
                     f"its circumference = π × d = {_pit} × "
                     f"{fmt_num(d)} = {fmt_num(dist)}"])
    m = re.search(r"radius\s+of\s+(?:a|the)\s+wheel\s+is\s+"
                  + N, q)
    if m and "revolution" in q:
        r = float(m.group(1))
        _pi, _u227, _reason = pi_choice(radius=r)
        dist = 2 * _pi * r
        if _u227:
            return _res("wheel_revolution", fmt_num(dist), dist,
                        [f"In one revolution the wheel covers "
                         f"2πr = 2 × (22/7) × {fmt_num(r)} = "
                         f"{fmt_num(dist)}"])
        return _res("wheel_revolution", fmt_num(dist), dist,
                    [f"In one revolution the wheel covers "
                     f"2πr = 2π × {fmt_num(r)} = "
                     f"{fmt_num(dist)}"])
    # Equilateral triangle perimeter from its side.
    if "equilateral" in q and "perimeter" in q:
        m = re.search(r"side[^0-9]{0,40}?" + N, q) or \
            re.search(N, q)
        if m:
            s = float(m.group(1))
            return _res("equilateral_perimeter",
                        fmt_num(3 * s), 3 * s,
                        [f"All three sides are equal: "
                         f"perimeter = 3 × {fmt_num(s)} = "
                         f"{fmt_num(3 * s)}"])
    # Cuboid given as "A cm by B cm by C cm".
    m = re.search(r"cuboid\s+" + N + r"\s*(?:cm|m)?\s*by\s+"
                  + N + r"\s*(?:cm|m)?\s*by\s+" + N, q)
    if m:
        ln, bd, ht = (float(m.group(i)) for i in (1, 2, 3))
        if "surface area" in q:
            tsa = 2 * (ln * bd + bd * ht + ht * ln)
            return _res("cuboid_tsa_by", fmt_num(tsa), tsa,
                        [f"TSA = 2(lb + bh + hl) = 2("
                         f"{fmt_num(ln * bd)} + "
                         f"{fmt_num(bd * ht)} + "
                         f"{fmt_num(ht * ln)}) = "
                         f"{fmt_num(tsa)}"])
        if "volume" in q:
            v = ln * bd * ht
            return _res("cuboid_volume_by", fmt_num(v), v,
                        [f"Volume = l × b × h = {fmt_num(v)}"])
    # Square: area from its perimeter.
    m = re.search(r"perimeter\s+of\s+a\s+square\s+is\s+" + N,
                  q) or re.search(r"same\s+perimeter\s+(?:is\s+)?"
                                  + N, q)
    if m and "square" in q and "area" in q:
        p = float(m.group(1))
        side = p / 4
        return _res("square_area_from_perimeter",
                    fmt_num(side * side), side * side,
                    [f"Side of the square = {fmt_num(p)} / 4 "
                     f"= {fmt_num(side)}",
                     f"Area = {fmt_num(side)}² = "
                     f"{fmt_num(side * side)}"])
    # Square: area from its diagonal (A = d^2 / 2).
    m = re.search(r"diagonal\s+of\s+a\s+square\s+is\s+" + N, q)
    if m and "area" in q:
        d = float(m.group(1))
        return _res("square_area_from_diagonal",
                    fmt_num(d * d / 2), d * d / 2,
                    [f"Area of a square = diagonal² / 2 = "
                     f"{fmt_num(d)}² / 2 = "
                     f"{fmt_num(d * d / 2)}"])
    # Trapezium from its parallel sides and height.
    if "trapezium" in q or "trapezoid" in q:
        m = re.search(r"parallel\s+sides\s+(?:are\s+)?" + N +
                      r"\s*(?:cm|m)?\s+and\s+" + N, q)
        mh = re.search(r"height\s+(?:is\s+)?" + N, q)
        if m and mh and "area" in q:
            a, b = float(m.group(1)), float(m.group(2))
            h = float(mh.group(1))
            ar = 0.5 * (a + b) * h
            return _res("trapezium_area", fmt_num(ar), ar,
                        [f"Area = ½ × (sum of parallel sides)"
                         f" × height = ½ × ({fmt_num(a)} + "
                         f"{fmt_num(b)}) × {fmt_num(h)} = "
                         f"{fmt_num(ar)}"])
    # A dug well's earth = cylinder volume.
    if "well" in q and "volume" in q or ("well" in q
                                         and "earth" in q):
        md = re.search(N + r"\s*(?:m|metres?|meters?)?\s*deep",
                       q)
        mr = re.search(r"radius\s+(?:is\s+)?" + N, q) or \
            re.search(N + r"\s*(?:m\s+)?in\s+radius", q)
        if md and mr:
            dep, r = float(md.group(1)), float(mr.group(1))
            _pi, _u227, _reason = pi_choice(radius=r)
            v = _pi * r * r * dep
            _pit = "(22/7)" if _u227 else "π"
            return _res("well_volume", fmt_num(v), v,
                        [f"The well is a cylinder: V = πr²h "
                         f"= {_pit} × {fmt_num(r)}² × "
                         f"{fmt_num(dep)} = {fmt_num(v)}"])
    # Right triangle from its legs -> area.
    m = re.search(r"legs?\s+(?:of\s+)?" + N + r"\s*(?:cm|m)?"
                  r"\s+and\s+" + N, q)
    if m and "triangle" in q and "area" in q:
        a, b = float(m.group(1)), float(m.group(2))
        return _res("right_triangle_legs_area",
                    fmt_num(a * b / 2), a * b / 2,
                    [f"The legs are the base and height: "
                     f"area = ½ × {fmt_num(a)} × "
                     f"{fmt_num(b)} = {fmt_num(a * b / 2)}"])
    # Rectangle whose length is k times its breadth.
    m = re.search(r"length\s+of\s+a\s+rectangle\s+is\s+" + N +
                  r"\s+times\s+its\s+breadth", q)
    mb = re.search(r"breadth\s+is\s+" + N, q)
    if m and mb and "area" in q:
        k, bd = float(m.group(1)), float(mb.group(1))
        ln = k * bd
        return _res("rectangle_times_breadth_area",
                    fmt_num(ln * bd), ln * bd,
                    [f"Length = {fmt_num(k)} × breadth = "
                     f"{fmt_num(k)} × {fmt_num(bd)} = "
                     f"{fmt_num(ln)}",
                     f"Area = {fmt_num(ln)} × {fmt_num(bd)} "
                     f"= {fmt_num(ln * bd)}"])
    # A point with one unknown coordinate at a given
    # distance from a fixed point.
    m = re.search(r"\(\s*x\s*,\s*" + N + r"\s*\)\s+is\s+at\s+"
                  r"(?:a\s+)?distance\s+" + N + r"\s+from\s+"
                  r"\(\s*" + N + r"\s*,\s*" + N + r"\s*\)", q)
    if m:
        y0, dist = float(m.group(1)), float(m.group(2))
        cx, cy = float(m.group(3)), float(m.group(4))
        rem = dist * dist - (y0 - cy) ** 2
        if rem >= 0:
            root = math.sqrt(rem)
            r1, r2 = cx + root, cx - root
            steps = [
                f"(x - {fmt_num(cx)})² + ({fmt_num(y0)} - "
                f"{fmt_num(cy)})² = {fmt_num(dist)}², so "
                f"(x - {fmt_num(cx)})² = {fmt_num(rem)}",
                f"x = {fmt_num(r1)} or x = {fmt_num(r2)}"]
            if "positive" in q:
                pos = r1 if r1 > 0 else r2
                return _res("coord_unknown_point",
                            fmt_num(pos), pos, steps)
            return _res("coord_unknown_point",
                        f"{fmt_num(r1)} and {fmt_num(r2)}",
                        [r1, r2], steps)
    # Angle of elevation from a height and its shadow.
    if "angle of elevation" in q and "shadow" in q:
        mh = re.search(N + r"\s*(?:m|cm)?\s*(?:high|tall)", q)
        ms = re.search(r"shadow\s+(?:is\s+)?" + N, q)
        if mh and ms:
            h, s = float(mh.group(1)), float(ms.group(1))
            if s:
                ang = math.degrees(math.atan2(h, s))
                return _res("elevation_from_shadow",
                            fmt_num(round(ang, 2)), ang,
                            [f"tan(angle) = height / shadow = "
                             f"{fmt_num(h)} / {fmt_num(s)} = "
                             f"{fmt_num(h / s)}",
                             f"Angle = {fmt_num(round(ang, 2))}°"])
    # Polygon diagonals from the shape's name / side count.
    if "diagonal" in q:
        names = {"triangle": 3, "quadrilateral": 4,
                 "pentagon": 5, "hexagon": 6, "heptagon": 7,
                 "octagon": 8, "nonagon": 9, "decagon": 10}
        for nm, n in names.items():
            if nm in q and "diagonal" in q:
                dv = n * (n - 3) // 2
                return _res("polygon_diagonals", str(dv),
                            float(dv),
                            [f"A {nm} has {n} sides; diagonals "
                             f"= n(n - 3)/2 = {n} × {n - 3}/2 "
                             f"= {dv}"])
    # Sides of a polygon from its interior-angle sum.
    m = re.search(r"interior\s+angles?\s+sum\s+to\s+" + N, q)
    if m and ("sides" in q or "polygon" in q):
        tot = float(m.group(1))
        n = tot / 180 + 2
        return _res("polygon_sides_from_sum", fmt_num(n), n,
                    [f"Interior-angle sum = (n - 2) × 180°, "
                     f"so n = {fmt_num(tot)} / 180 + 2 = "
                     f"{fmt_num(n)}"])
    return None


def solve_geometry(question: str):
    q = question.lower()
    # Wave 57 (merge-3): Devanagari mensuration first, as in
    # the Wave 57 tree; disjoint from Wave 56's vectors.
    out = _mensuration_hindi(q)
    if out is None:
        out = _wave65_geometry(q)
    if out is None:
        out = _vectors56(q)
    if out is None:
        out = _pythagoras(q)
    if out is None:
        out = _radii_base_angle(q)
    if out is None:
        out = _tangent_from_angle(q)
    if out is None:
        out = _third_angle(q)
    if out is None:
        out = _threed(q)
    if out is None:
        out = _coordinate(q)
    if out is None:
        out = _circles_extra(q)
    if out is None:
        out = _area_perimeter_volume(q)
    if out is None:
        return {
            "type": "geometry",
            "op": "unknown",
            "answer": "Tell me the shape and measurements, e.g. 'area of "
                      "circle with radius 5' or 'distance between (1,2) "
                      "and (4,6)'.",
            "steps": [],
        }
    op, answer, steps = out
    return {"type": "geometry", "op": op, "answer": answer, "steps": steps}
