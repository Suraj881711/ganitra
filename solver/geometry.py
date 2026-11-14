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


def _area_perimeter_volume(q: str):
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
    return None


def solve_geometry(question: str):
    q = question.lower()
    out = _third_angle(q)
    if out is None:
        out = _coordinate(q)
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
