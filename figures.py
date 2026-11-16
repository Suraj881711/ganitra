"""Wave 86: answer diagrams for mensuration solves.

When a REAL solver answer is about a rectangle, square, circle
or triangle whose dimensions are stated unambiguously in the
question, the answer card also carries a small labelled figure
(server-generated inline SVG) drawn with the question's OWN
numbers.

The trigger is deliberately conservative — a wrong figure is
worse than no figure:

1. The result must be a plain mensuration solve (op area /
   perimeter / circumference, or the applied Hindi mensuration
   ops of the same quantities). No fallback, concept, bank or
   salvage result ever reaches here — the only caller is
   fallback.with_fallback's real-answer branch.
2. Exactly ONE of the four shapes may be named in the
   question (English or Devanagari).
3. The dimensions are re-extracted from the question text
   with the same finders the solver itself uses.
4. The figure's numbers must REPRODUCE the solved answer:
   the quantity is recomputed from the extracted dimensions
   and compared with the result's value / answer text. Any
   mismatch — or an answer whose number cannot be parsed
   unambiguously — means no figure.

Everything interpolated into the SVG is a formatted number, a
unit from a fixed whitelist, or a fixed English word — never
raw question text — so the markup is safe to inline.
"""

import math
import re

from solver.expression_parser import find_param, fmt_num

_INK = "#25324e"      # --text
_ACCENT = "#2f7d6e"   # --accent
_MUTED = "#66738d"    # --muted
_FILL = "rgba(47, 125, 110, 0.08)"

_NUM = r"(-?\d+(?:\.\d+)?)"

_QUANTITY_OPS = {
    "area": "area",
    "perimeter": "perimeter",
    "circumference": "circumference",
    "hindi_circle_area": "area",
    "hindi_circle_circumference": "circumference",
    "hindi_rectangle_area": "area",
    "hindi_triangle_area": "area",
    "hindi_square_area": "area",
    "hindi_square_perimeter": "perimeter",
}

_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _num(s):
    f = float(s)
    return int(f) if f == int(f) else f


def _flex(q, names):
    """find_param + the NCERT sentence form ("the radius of a
    circle is 7 cm") — the same pairing solver/geometry.py's
    _param_flex uses, so the figure reads the question exactly
    as the solver did."""
    v = find_param(q, names)
    if v is not None:
        return v
    for name in names:
        if len(name) < 3:
            continue
        m = re.search(
            rf"\b{name}\s+of\s+(?:a\s+|an\s+|the\s+)?\w+\s+is\s+"
            + _NUM, q)
        if m:
            return _num(m.group(1))
    return None


def _hnear(q, word):
    """Mirror of applied.py's Hindi finder: the number attached
    to a Devanagari quantity word, after it or before it."""
    m = re.search(re.escape(word) + r"\s*(\d+(?:\.\d+)?)", q) or \
        re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|सेमी|m|मी)?\s*"
                  + re.escape(word), q)
    return _num(m.group(1)) if m else None


def _unit(q, q_raw):
    units = re.findall(r"\d+(?:\.\d+)?\s*(cm|mm|km|m)\b", q)
    if units:
        return max(set(units), key=units.count)
    if "सेमी" in q_raw:
        return "cm"
    return ""


def _answer_value(result):
    """The solved quantity as a float, or None when the answer
    text does not carry exactly one unambiguous number."""
    value = result.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    ans = str(result.get("answer", "") or "").replace(",", "")
    m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*",
                     ans)
    if m:
        den = float(m.group(2))
        return float(m.group(1)) / den if den else None
    if "≈" in ans:
        tail = ans.rsplit("≈", 1)[1]
        nums = re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", tail)
        return float(nums[0]) if len(nums) == 1 else None
    nums = re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", ans)
    return float(nums[0]) if len(nums) == 1 else None


def _matches(expected, actual):
    if actual is None:
        return False
    return abs(expected - actual) <= max(0.02, abs(expected) * 0.002)


def _label(value, unit):
    return f"{fmt_num(value)} {unit}".strip()


def _svg_open(width, height, caption):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" '
        f'role="img" aria-label="{caption}" '
        f'style="max-width:100%;height:auto">'
        f"<title>{caption}</title>")


def _rect_svg(l, b, unit, shape_word):
    scale = min(200.0 / l, 118.0 / b)
    w = max(l * scale, 24.0)
    h = max(b * scale, 24.0)
    width = int(w + 66)
    height = int(h + 42)
    x0, y0 = 8.0, 8.0
    parts = [
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" '
        f'height="{h:.1f}" fill="{_FILL}" stroke="{_ACCENT}" '
        f'stroke-width="2"/>',
        f'<line x1="{x0:.1f}" y1="{y0 + h + 7:.1f}" x2="{x0 + w:.1f}" '
        f'y2="{y0 + h + 7:.1f}" stroke="{_MUTED}" stroke-width="1"/>',
        f'<line x1="{x0 + w + 7:.1f}" y1="{y0:.1f}" '
        f'x2="{x0 + w + 7:.1f}" y2="{y0 + h:.1f}" stroke="{_MUTED}" '
        f'stroke-width="1"/>',
        f'<text x="{x0 + w / 2:.1f}" y="{height - 4}" '
        f'text-anchor="middle" font-size="12" fill="{_INK}">'
        f'{_label(l, unit)}</text>',
        f'<text x="{x0 + w + 12:.1f}" y="{y0 + h / 2:.1f}" '
        f'dominant-baseline="middle" font-size="12" '
        f'fill="{_INK}">{_label(b, unit)}</text>',
    ]
    if shape_word == "Square":
        caption = f"Square: side {_label(l, unit)}"
    else:
        caption = (f"Rectangle: length {_label(l, unit)}, "
                   f"breadth {_label(b, unit)}")
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


def _circle_svg(r, d, unit):
    radius = r if r is not None else d / 2
    rad = 62.0
    cx = cy = 78.0
    width, height = 156, 184
    parts = [
        f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{_FILL}" '
        f'stroke="{_ACCENT}" stroke-width="2"/>',
    ]
    if r is not None:
        x2 = cx + rad * math.cos(math.radians(-40))
        y2 = cy + rad * math.sin(math.radians(-40))
        parts.append(
            f'<line x1="{cx}" y1="{cy}" x2="{x2:.1f}" '
            f'y2="{y2:.1f}" stroke="{_INK}" stroke-width="1.5"/>')
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="{_INK}"/>')
        label = f"r = {_label(r, unit)}"
        caption = f"Circle: radius {_label(r, unit)}"
    else:
        parts.append(
            f'<line x1="{cx - rad}" y1="{cy}" x2="{cx + rad}" '
            f'y2="{cy}" stroke="{_INK}" stroke-width="1.5"/>')
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="2.4" fill="{_INK}"/>')
        label = f"d = {_label(d, unit)}"
        caption = f"Circle: diameter {_label(d, unit)}"
    parts.append(
        f'<text x="{cx}" y="{height - 6}" text-anchor="middle" '
        f'font-size="12" fill="{_INK}">{label}</text>')
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


def _triangle_svg(base, height_v, unit):
    scale = min(208.0 / base, 128.0 / height_v)
    bw = max(base * scale, 30.0)
    hh = min(max(height_v * scale, 30.0), 132.0)
    x0 = 10.0
    y_base = hh + 12.0
    apex_x = x0 + 0.38 * bw
    width = int(bw + 88)
    height = int(y_base + 30)
    parts = [
        f'<polygon points="{x0:.1f},{y_base:.1f} '
        f'{x0 + bw:.1f},{y_base:.1f} {apex_x:.1f},12" '
        f'fill="{_FILL}" stroke="{_ACCENT}" stroke-width="2"/>',
        f'<line x1="{apex_x:.1f}" y1="12" x2="{apex_x:.1f}" '
        f'y2="{y_base:.1f}" stroke="{_MUTED}" stroke-width="1.2" '
        f'stroke-dasharray="4 3"/>',
        f'<text x="{apex_x + 6:.1f}" y="{12 + hh / 2:.1f}" '
        f'dominant-baseline="middle" font-size="12" '
        f'fill="{_INK}">{_label(height_v, unit)}</text>',
        f'<text x="{x0 + bw / 2:.1f}" y="{height - 5}" '
        f'text-anchor="middle" font-size="12" fill="{_INK}">'
        f'{_label(base, unit)}</text>',
    ]
    caption = (f"Triangle: base {_label(base, unit)}, "
               f"height {_label(height_v, unit)}")
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


def _shapes_in(q, q_raw):
    shapes = []
    if "circle" in q or "वृत्त" in q_raw:
        shapes.append("circle")
    if "rectangle" in q or ("लंबाई" in q_raw and "चौड़ाई" in q_raw):
        shapes.append("rectangle")
    if "square" in q or "वर्ग" in q_raw:
        shapes.append("square")
    if "triangle" in q or "त्रिभुज" in q_raw:
        shapes.append("triangle")
    return shapes


def _dims(shape, q, q_raw):
    """(dims dict) re-extracted from the question, or None."""
    if shape == "rectangle":
        if "लंबाई" in q_raw:
            ln, br = _hnear(q_raw, "लंबाई"), _hnear(q_raw, "चौड़ाई")
            if ln and br:
                return {"l": ln, "b": br}
        l = find_param(q, ["length", "l"])
        b = find_param(q, ["breadth", "width", "b", "w"])
        if l is None or b is None:
            m = re.search(r"length\s+of\s+a\s+rectangle\s+is\s+"
                          + _NUM, q)
            m2 = re.search(r"(?:breadth|width)\s*(?:is\s+)?"
                           + _NUM, q)
            if m and m2:
                l, b = _num(m.group(1)), _num(m2.group(1))
        if l is None or b is None:
            m = re.search(r"rectangle\s+(?:of\s+)?" + _NUM +
                          r"\s*(?:cm|m|mm)?\s*(?:by|x|×)\s*" + _NUM, q)
            if m:
                l, b = _num(m.group(1)), _num(m.group(2))
        if l is None or b is None:
            return None
        return {"l": l, "b": b}
    if shape == "square":
        if "वर्ग" in q_raw:
            s = _hnear(q_raw, "भुजा")
            if s:
                return {"s": s}
        s = find_param(q, ["side", "s"])
        if s is None:
            m = re.search(r"square\s+" + _NUM +
                          r"\s*(?:cm|m|mm)?\s*$", q.strip())
            if m:
                s = _num(m.group(1))
        return {"s": s} if s is not None else None
    if shape == "circle":
        if "वृत्त" in q_raw:
            r = _hnear(q_raw, "त्रिज्या")
            if r:
                return {"r": r}
        r = _flex(q, ["radius", "r"])
        d = find_param(q, ["diameter"])
        if r is not None:
            return {"r": r}
        if d is not None:
            return {"d": d}
        return None
    if shape == "triangle":
        if "त्रिभुज" in q_raw:
            b = _hnear(q_raw, "आधार")
            h = _hnear(q_raw, "ऊंचाई")
            if b and h:
                return {"base": b, "height": h}
        base = find_param(q, ["base"])
        height = find_param(q, ["height", "h"])
        if base is None or height is None:
            return None
        return {"base": base, "height": height}
    return None


def _expected(shape, quantity, dims):
    if shape == "rectangle":
        return (dims["l"] * dims["b"] if quantity == "area"
                else 2 * (dims["l"] + dims["b"]))
    if shape == "square":
        return (dims["s"] * dims["s"] if quantity == "area"
                else 4 * dims["s"])
    if shape == "circle":
        r = dims["r"] if "r" in dims else dims["d"] / 2
        return (math.pi * r * r if quantity == "area"
                else 2 * math.pi * r)
    if shape == "triangle":
        return 0.5 * dims["base"] * dims["height"]
    return None


def figure_for(question, result):
    """The labelled figure for a solved mensuration answer, as
    {"svg": ..., "caption": ...}, or None. Never raises."""
    try:
        return _figure_for(question, result)
    except Exception:
        return None


def _figure_for(question, result):
    if not isinstance(result, dict):
        return None
    if result.get("fallback") or result.get("fallback_kind"):
        return None
    quantity = _QUANTITY_OPS.get(str(result.get("op", "")))
    if quantity is None:
        return None
    if not result.get("steps"):
        return None
    q_raw = str(question or "")
    q = q_raw.lower().translate(_DEVA_DIGITS)
    shapes = _shapes_in(q, q_raw)
    if len(shapes) != 1:
        return None
    shape = shapes[0]
    if shape == "triangle" and quantity != "area":
        return None
    dims = _dims(shape, q, q_raw.translate(_DEVA_DIGITS))
    if dims is None:
        return None
    if any(not isinstance(v, (int, float)) or v <= 0
           for v in dims.values()):
        return None
    expected = _expected(shape, quantity, dims)
    if expected is None or not _matches(expected,
                                         _answer_value(result)):
        return None
    unit = _unit(q, q_raw)
    if shape == "rectangle":
        return _rect_svg(dims["l"], dims["b"], unit, "Rectangle")
    if shape == "square":
        return _rect_svg(dims["s"], dims["s"], unit, "Square")
    if shape == "circle":
        return _circle_svg(dims.get("r"), dims.get("d"), unit)
    return _triangle_svg(dims["base"], dims["height"], unit)
