"""Geometry: area/perimeter/volume of standard shapes and coordinate
geometry (distance, midpoint, slope, line & circle equations)."""
import math
import re

import sympy as sp

from .expression_parser import extract_points, find_param, fmt, fmt_num

PI = math.pi


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
        if "curved surface" in q or " csa" in q:
            val = PI * (R + r) * slant
            steps = [
                f"For a frustum: R = {fmt_num(R)}, "
                f"r = {fmt_num(r)}, slant height l = "
                f"{slant:.4f}",
                f"Curved surface area = pi(R + r)l = pi × "
                f"({fmt_num(R)} + {fmt_num(r)}) × {slant:.4f} "
                f"= {fmt_num(val)}",
            ]
            return "frustum csa", fmt_num(val), steps
        if "total surface" in q or " tsa" in q:
            val = PI * (R + r) * slant + PI * (R * R + r * r)
            steps = [
                f"For a frustum: R = {fmt_num(R)}, "
                f"r = {fmt_num(r)}, slant height l = "
                f"{slant:.4f}",
                f"TSA = pi(R + r)l + pi(R^2 + r^2) = "
                f"{fmt_num(val)}",
            ]
            return "frustum tsa", fmt_num(val), steps
        val = PI * h / 3 * (R * R + R * r + r * r)
        steps = [
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
        if r is None or not (mh1 and mh2):
            return None
        h1, h2 = float(mh1.group(1)), float(mh2.group(1))
        v1 = PI * r * r * h1
        v2 = PI * r * r * h2 / 3
        steps = [
            f"Volume of the cylinder part = pi·r^2·h = pi × "
            f"{fmt_num(r)}^2 × {fmt_num(h1)} = {fmt_num(v1)}",
            f"Volume of the cone part = (1/3)·pi·r^2·h = "
            f"(1/3) × pi × {fmt_num(r)}^2 × {fmt_num(h2)} "
            f"= {fmt_num(v2)}",
            f"Total volume = {fmt_num(v1)} + {fmt_num(v2)} "
            f"= {fmt_num(v1 + v2)}",
        ]
        return "combined volume", fmt_num(v1 + v2), steps

    # ---- Hemisphere --------------------------------------------
    if "hemisphere" in q:
        r = _param_flex(q, ["radius", "r"])
        if r is None:
            return None
        if "curved surface" in q or " csa" in q:
            val = 2 * PI * r * r
            steps = [f"Curved surface area of a hemisphere = "
                     f"2·pi·r^2 = 2 × pi × {fmt_num(r)}^2 "
                     f"= {fmt_num(val)}"]
            return "hemisphere csa", fmt_num(val), steps
        if "total surface" in q or " tsa" in q or \
                "surface" in q:
            val = 3 * PI * r * r
            steps = [
                f"Total surface area of a hemisphere = curved "
                f"surface + base = 2·pi·r^2 + pi·r^2 "
                f"= 3·pi·r^2",
                f"= 3 × pi × {fmt_num(r)}^2 = {fmt_num(val)}",
            ]
            return "hemisphere tsa", fmt_num(val), steps
        val = 2 * PI * r ** 3 / 3
        steps = [f"Volume of a hemisphere = (2/3)·pi·r^3 = "
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
        if "curved surface" in q or " csa" in q:
            val = PI * r * slant
            steps = [
                f"Slant height l = {fmt_num(slant)}",
                f"Curved surface area of a cone = pi·r·l = "
                f"pi × {fmt_num(r)} × {fmt_num(slant)} "
                f"= {fmt_num(val)}",
            ]
            return "cone csa", fmt_num(val), steps
        val = PI * r * (slant + r)
        steps = [
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
        val = 2 * PI * r * h
        steps = [f"Curved surface area of a cylinder = "
                 f"2·pi·r·h = 2 × pi × {fmt_num(r)} × "
                 f"{fmt_num(h)} = {fmt_num(val)}"]
        return "cylinder csa", fmt_num(val), steps

    # ---- Sector / segment / arc --------------------------------
    if "segment" in q and "circle" in q:
        r = _param_flex(q, ["radius", "r"])
        th = _angle_deg(q)
        if r is None or th is None:
            return None
        sector = th / 360 * PI * r * r
        tri = 0.5 * r * r * math.sin(math.radians(th))
        val = sector - tri
        steps = [
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
        val = th / 360 * PI * r * r
        steps = [f"Area of a sector = (theta/360)·pi·r^2 = "
                 f"({fmt_num(th)}/360) × pi × {fmt_num(r)}^2 "
                 f"= {fmt_num(val)}"]
        return "sector area", fmt_num(val), steps
    if "arc" in q and "length" in q:
        r = _param_flex(q, ["radius", "r"])
        th = _angle_deg(q)
        if r is None or th is None:
            return None
        val = th / 360 * 2 * PI * r
        steps = [f"Length of an arc = (theta/360)·2·pi·r = "
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
    if "circle" in q or "circumference" in q:
        r = _param_flex(q, ["radius", "r"])
        d = find_param(q, ["diameter"])
        if r is None and d is not None:
            r = d / 2
        if r is None:
            # Wave 30: area asked with the CIRCUMFERENCE given
            # ("area of a circle whose circumference is 44 cm")
            # — recover r from C = 2·pi·r first.
            C = find_param(q, ["circumference"])
            if C is not None and "area" in q:
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
        if "circumference" in q or "perimeter" in q:
            val = 2 * PI * r
            steps = [f"Circumference = 2·pi·r = 2 × pi × {fmt_num(r)}",
                     f"= {fmt_num(val)} (approx) = {fmt_num(2 * r)}·pi "
                     f"exactly"]
            return "circumference", f"{fmt_num(2 * r)}·pi ≈ {val:.4f}", steps
        val = PI * r * r
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

    # ---- Rectangle ---------------------------------------------------
    if "rectangle" in q:
        l = find_param(q, ["length", "l"])
        b = find_param(q, ["breadth", "width", "b", "w"])
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
            return None
        if "surface" in q:
            val = 4 * PI * r * r
            steps = [f"Surface area = 4·pi·r^2 = 4 × pi × {fmt_num(r)}^2",
                     f"≈ {val:.4f}"]
            return "surface area", f"≈ {val:.4f}", steps
        val = (4 / 3) * PI * r ** 3
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
        if "surface" in q:
            val = 2 * PI * r * (r + h)
            steps = [f"Total surface area = 2·pi·r(r + h) = 2 × pi × "
                     f"{fmt_num(r)} × ({fmt_num(r)} + {fmt_num(h)})",
                     f"≈ {val:.4f}"]
            return "surface area", f"≈ {val:.4f}", steps
        val = PI * r * r * h
        steps = [f"Volume = pi·r^2·h = pi × {fmt_num(r)}^2 × "
                 f"{fmt_num(h)}", f"≈ {val:.4f}"]
        return "volume", f"≈ {val:.4f}", steps

    # ---- Cone --------------------------------------------------------
    if "cone" in q:
        r = _param_flex(q, ["radius", "r"])
        h = _param_flex(q, ["height", "h"])
        if r is None or h is None:
            return None
        val = (1 / 3) * PI * r * r * h
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
        if r is None or ext is None:
            return None
        d = math.hypot(ext[0] - centre[0], ext[1] - centre[1])
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


def solve_geometry(question: str):
    q = question.lower()
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
