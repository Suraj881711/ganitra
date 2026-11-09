"""Geometry: area/perimeter/volume of standard shapes and coordinate
geometry (distance, midpoint, slope, line & circle equations)."""
import math
import re

import sympy as sp

from .expression_parser import extract_points, find_param, fmt, fmt_num

PI = math.pi


def _area_perimeter_volume(q: str):
    # ---- Circle ------------------------------------------------------
    if "circle" in q or "circumference" in q:
        r = find_param(q, ["radius", "r"])
        d = find_param(q, ["diameter"])
        if r is None and d is not None:
            r = d / 2
        if r is None:
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
            m = re.search(r"sides?\s*(?:are|:)?\s*([\d\s,\.and]+)", q)
            if m:
                sides = [float(v) for v in
                         re.findall(r"\d+(?:\.\d+)?", m.group(1))]
                if len(sides) == 3:
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
        m = re.search(r"sides?\s*(?:are|:)?\s*([\d\s,\.and]+)", q)
        if m:  # Heron's formula
            sides = [float(v) for v in
                     re.findall(r"\d+(?:\.\d+)?", m.group(1))]
            if len(sides) == 3:
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
        r = find_param(q, ["radius", "r"])
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
        r = find_param(q, ["radius", "r"])
        h = find_param(q, ["height", "h"])
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
        r = find_param(q, ["radius", "r"])
        h = find_param(q, ["height", "h"])
        if r is None or h is None:
            return None
        val = (1 / 3) * PI * r * r * h
        steps = [f"Volume = (1/3)·pi·r^2·h = (1/3) × pi × "
                 f"{fmt_num(r)}^2 × {fmt_num(h)}", f"≈ {val:.4f}"]
        return "volume", f"≈ {val:.4f}", steps

    return None


def _coordinate(q: str):
    pts = extract_points(q)

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
