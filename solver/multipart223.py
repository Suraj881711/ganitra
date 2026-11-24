"""Wave 223: multipart splitter (J9).

Live gap (Deploy-65 check): a question that asks TWO things
about ONE shape was served as ONE of them only -- the
geometry solver answers the first ask word it sees, so
"Find the area and perimeter of a rectangle with length
8 cm and breadth 5 cm" came back with the area (40) and
no perimeter (26), and "Find the circumference and area
of a circle with radius 7 cm" came back with one of 44 /
154 only.  A student who asks for both measures needs
both answers, with the working for each.

THE FIX (this module): a multipart question is recognised
STRUCTURALLY -- exactly two ask words (area / perimeter /
circumference / volume / surface area, in English or
Hinglish) about exactly one shape, with every dimension
the two parts need stated in the question -- and is
split into its two single-ask parts ("area of a rectangle
with length 8 cm and breadth 5 cm", "perimeter of a
rectangle with length 8 cm and breadth 5 cm").  Each part
is then computed here, directly and exactly (Fraction
arithmetic, pi = 22/7 for circles, as the geometry solver
does), and the two answers are returned together, in the
order the question asked them, with a working line for
each.  The router tries this module BEFORE the Wave 222
unit-conversion gate, so a multipart ask is never handed
to a single-measure solver first.

Anything that is not that shape returns None and the
pre-Wave-223 flow decides: a single ask, three asks, an
unsupported pair (area + volume of a rectangle), a
sector / segment / ring, a comparison ("which is
bigger"), two different shapes in one question, or a
question whose dimensions are missing.  The module never
guesses a dimension and never calls back into the router,
so it cannot recurse.
"""

import re
from decimal import Decimal
from fractions import Fraction

_PI = Fraction(22, 7)
_NUM = r"(\d+(?:\.\d+)?)"
_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_HINGLISH_ASK = {
    "kshetrafal": "area",
    "parimap": "perimeter",
    "paridhi": "circumference",
    "aayatan": "volume",
}

_SHAPES = (
    ("rectangle", ("rectangle", "aayat")),
    ("circle", ("circle", "vritt")),
    ("square", ("square", "varg")),
    ("cuboid", ("cuboid", "ghanaab")),
    ("cube", ("cube",)),
    ("triangle", ("triangle", "tribhuj")),
)

_SUPPORTED = {
    "rectangle": {"area", "perimeter"},
    "square": {"area", "perimeter"},
    "circle": {"area", "circumference"},
    "cuboid": {"volume", "surface area"},
    "cube": {"volume", "surface area"},
    "triangle": {"area", "perimeter"},
}

_LABEL = {
    "area": "Area",
    "perimeter": "Perimeter",
    "circumference": "Circumference",
    "volume": "Volume",
    "surface area": "Surface area",
}


def _fold(text):
    t = str(text or "").translate(_DEV_DIGITS).lower()
    t = t.replace("−", "-").replace("–", "-")
    t = re.sub(r"\bprishtiya\s+kshetrafal\b", " surface area ", t)
    for word, canon in _HINGLISH_ASK.items():
        t = re.sub(r"\b" + word + r"\b", " " + canon + " ", t)
    return t


def _fmt(value):
    fr = Fraction(value)
    if fr.denominator == 1:
        return str(fr.numerator)
    den = fr.denominator
    while den % 2 == 0:
        den //= 2
    while den % 5 == 0:
        den //= 5
    if den == 1:
        dec = Decimal(fr.numerator) / Decimal(fr.denominator)
        return format(dec.normalize(), "f")
    return format(float(fr), ".2f").rstrip("0").rstrip(".")


def _dim(text, words):
    alt = "|".join(words)
    m = re.search(r"(?:" + alt + r")\s*(?:is\s+)?" + _NUM +
                  r"(?:\s*(?:cm|mm|km|m)\b)?", text)
    if m:
        return Fraction(m.group(1))
    m = re.search(_NUM + r"\s*(?:cm|mm|km|m)?\s*(?:" + alt + r")\b",
                  text)
    if m:
        return Fraction(m.group(1))
    return None


def _unit(text):
    m = re.search(r"\d+(?:\.\d+)?\s*(cm|mm|km|m)\b", text)
    return m.group(1) if m else ""


def _shape(text):
    found = []
    for name, words in _SHAPES:
        if any(re.search(r"\b" + w + r"\b", text) for w in words):
            found.append(name)
    if len(found) != 1:
        return None
    return found[0]


def _asks(text):
    surface = [(m.start(), m.end()) for m in
               re.finditer(r"\bsurface area\b", text)]
    hits = []
    for phrase in ("surface area", "area", "perimeter",
                   "circumference", "volume"):
        for m in re.finditer(r"\b" + phrase + r"\b", text):
            if phrase == "area" and any(
                    start <= m.start() < end
                    for start, end in surface):
                continue
            hits.append((m.start(), phrase))
    hits.sort()
    out = []
    for _, phrase in hits:
        if phrase not in out:
            out.append(phrase)
    return out


def _dims(shape, text):
    if shape == "rectangle":
        length = _dim(text, ("length", "lambai"))
        breadth = _dim(text, ("breadth", "chaudai", "width"))
        if length is None or breadth is None:
            return None
        return {"length": length, "breadth": breadth}
    if shape == "circle":
        radius = _dim(text, ("radius", "trijya"))
        if radius is None:
            diameter = _dim(text, ("diameter", "vyas"))
            if diameter is None:
                return None
            radius = diameter / 2
        return {"radius": radius}
    if shape in ("square", "cube"):
        side = _dim(text, ("side", "bhuja"))
        if side is None:
            return None
        return {"side": side}
    if shape == "cuboid":
        length = _dim(text, ("length", "lambai"))
        breadth = _dim(text, ("breadth", "chaudai", "width"))
        height = _dim(text, ("height", "unchai"))
        if length is None or breadth is None or height is None:
            return None
        return {"length": length, "breadth": breadth,
                "height": height}
    if shape == "triangle":
        base = _dim(text, ("base", "aadhar"))
        height = _dim(text, ("height", "unchai"))
        m = re.search(r"sides?\s+" + _NUM + r"\s*(?:cm|m)?\s*,\s*" +
                      _NUM + r"\s*(?:cm|m)?\s+and\s+" + _NUM, text)
        if base is None or height is None or m is None:
            return None
        return {"base": base, "height": height,
                "sides": [Fraction(m.group(1)),
                          Fraction(m.group(2)),
                          Fraction(m.group(3))]}
    return None


def _setup(shape, dims, unit):
    u = (" " + unit) if unit else ""
    if shape == "rectangle":
        return ("a rectangle with length " + _fmt(dims["length"]) +
                u + " and breadth " + _fmt(dims["breadth"]) + u)
    if shape == "circle":
        return "a circle with radius " + _fmt(dims["radius"]) + u
    if shape == "square":
        return "a square with side " + _fmt(dims["side"]) + u
    if shape == "cuboid":
        return ("a cuboid with length " + _fmt(dims["length"]) + u +
                ", breadth " + _fmt(dims["breadth"]) + u +
                " and height " + _fmt(dims["height"]) + u)
    if shape == "cube":
        return "a cube with side " + _fmt(dims["side"]) + u
    if shape == "triangle":
        sides = ", ".join(_fmt(s) + u for s in dims["sides"])
        return ("a triangle with base " + _fmt(dims["base"]) + u +
                ", height " + _fmt(dims["height"]) + u +
                " and sides " + sides)
    return ""


def _parts(shape, asks, dims, unit):
    u = (" " + unit) if unit else ""
    out = []
    for ask in asks:
        if shape == "rectangle" and ask == "area":
            value = dims["length"] * dims["breadth"]
            step = ("Area = length \u00d7 breadth = " +
                    _fmt(dims["length"]) + " \u00d7 " +
                    _fmt(dims["breadth"]) + " = " + _fmt(value) +
                    u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "rectangle" and ask == "perimeter":
            value = 2 * (dims["length"] + dims["breadth"])
            step = ("Perimeter = 2 \u00d7 (length + breadth) = "
                    "2 \u00d7 (" + _fmt(dims["length"]) + " + " +
                    _fmt(dims["breadth"]) + ") = " + _fmt(value) + u)
            out.append((ask, value, u, step))
        elif shape == "circle" and ask == "circumference":
            value = 2 * _PI * dims["radius"]
            step = ("Circumference = 2 \u00d7 \u03c0 \u00d7 radius = "
                    "2 \u00d7 22/7 \u00d7 " + _fmt(dims["radius"]) +
                    " = " + _fmt(value) + u)
            out.append((ask, value, u, step))
        elif shape == "circle" and ask == "area":
            value = _PI * dims["radius"] * dims["radius"]
            step = ("Area = \u03c0 \u00d7 radius\u00b2 = 22/7 \u00d7 " +
                    _fmt(dims["radius"]) + " \u00d7 " +
                    _fmt(dims["radius"]) + " = " + _fmt(value) +
                    u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "square" and ask == "area":
            value = dims["side"] * dims["side"]
            step = ("Area = side \u00d7 side = " + _fmt(dims["side"]) +
                    " \u00d7 " + _fmt(dims["side"]) + " = " +
                    _fmt(value) + u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "square" and ask == "perimeter":
            value = 4 * dims["side"]
            step = ("Perimeter = 4 \u00d7 side = 4 \u00d7 " +
                    _fmt(dims["side"]) + " = " + _fmt(value) + u)
            out.append((ask, value, u, step))
        elif shape == "cuboid" and ask == "volume":
            value = (dims["length"] * dims["breadth"] *
                     dims["height"])
            step = ("Volume = length \u00d7 breadth \u00d7 height = " +
                    _fmt(dims["length"]) + " \u00d7 " +
                    _fmt(dims["breadth"]) + " \u00d7 " +
                    _fmt(dims["height"]) + " = " + _fmt(value) +
                    u + "\u00b3")
            out.append((ask, value, u + "\u00b3", step))
        elif shape == "cuboid" and ask == "surface area":
            value = 2 * (dims["length"] * dims["breadth"] +
                         dims["breadth"] * dims["height"] +
                         dims["height"] * dims["length"])
            step = ("Surface area = 2 \u00d7 (length \u00d7 breadth + "
                    "breadth \u00d7 height + height \u00d7 length) = " +
                    _fmt(value) + u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "cube" and ask == "volume":
            value = dims["side"] ** 3
            step = ("Volume = side\u00b3 = " + _fmt(dims["side"]) +
                    "\u00b3 = " + _fmt(value) + u + "\u00b3")
            out.append((ask, value, u + "\u00b3", step))
        elif shape == "cube" and ask == "surface area":
            value = 6 * dims["side"] * dims["side"]
            step = ("Surface area = 6 \u00d7 side\u00b2 = 6 \u00d7 " +
                    _fmt(dims["side"]) + "\u00b2 = " + _fmt(value) +
                    u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "triangle" and ask == "area":
            value = dims["base"] * dims["height"] / 2
            step = ("Area = 1/2 \u00d7 base \u00d7 height = 1/2 \u00d7 " +
                    _fmt(dims["base"]) + " \u00d7 " +
                    _fmt(dims["height"]) + " = " + _fmt(value) +
                    u + "\u00b2")
            out.append((ask, value, u + "\u00b2", step))
        elif shape == "triangle" and ask == "perimeter":
            value = sum(dims["sides"])
            step = ("Perimeter = " +
                    " + ".join(_fmt(s) for s in dims["sides"]) +
                    " = " + _fmt(value) + u)
            out.append((ask, value, u, step))
        else:
            return None
    return out


def split_multipart223(question):
    """The two single-ask parts of a multipart question, in
    the order the question asks them, or [] when the
    question is not a supported multipart ask."""
    q = _fold(question)
    if re.search(r"\b(sector|segment|ring|which|bigger|greater|"
                 r"smaller)\b", q):
        return []
    shape = _shape(q)
    if shape is None:
        return []
    asks = _asks(q)
    if len(asks) != 2 or set(asks) != _SUPPORTED[shape]:
        return []
    dims = _dims(shape, q)
    if dims is None:
        return []
    setup = _setup(shape, dims, _unit(q))
    return [ask + " of " + setup for ask in asks]


def solve_multipart223(question):
    """Solve a two-part mensuration question, or None.

    Returns the solver's standard dict (type, op, answer,
    steps) with BOTH answers in the answer text, each with
    its working line in the steps."""
    parts = split_multipart223(question)
    if not parts:
        return None
    q = _fold(question)
    shape = _shape(q)
    dims = _dims(shape, q)
    if dims is None:
        return None
    unit = _unit(q)
    computed = _parts(shape, _asks(q), dims, unit)
    if computed is None or len(computed) != 2:
        return None
    answer = "\n".join(_LABEL[ask] + " = " + _fmt(value) + suffix
                       for ask, value, suffix, _ in computed)
    steps = [step for _, _, _, step in computed]
    return {"type": "geometry", "op": "multipart223",
            "answer": answer, "steps": steps}
