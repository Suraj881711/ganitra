"""Unit conversion: length, mass, time, volume, area and temperature."""
import re

from .expression_parser import fmt_num

# unit -> (base-unit factor, base name). Base units: m, kg, s, L, m^2
_UNITS = {
    "length": {
        "mm": 0.001, "millimetre": 0.001, "millimeter": 0.001,
        "millimetres": 0.001, "millimeters": 0.001,
        "cm": 0.01, "centimetre": 0.01, "centimeter": 0.01,
        "centimetres": 0.01, "centimeters": 0.01,
        "m": 1.0, "metre": 1.0, "meter": 1.0,
        "metres": 1.0, "meters": 1.0,
        "km": 1000.0, "kilometre": 1000.0, "kilometer": 1000.0,
        "kilometres": 1000.0, "kilometers": 1000.0,
        "inch": 0.0254, "inches": 0.0254, "in": 0.0254,
        "foot": 0.3048, "feet": 0.3048, "ft": 0.3048,
        "yard": 0.9144, "yards": 0.9144, "yd": 0.9144,
        "mile": 1609.344, "miles": 1609.344, "mi": 1609.344,
    },
    "mass": {
        "mg": 0.000001, "milligram": 0.000001,
        "g": 0.001, "gram": 0.001, "grams": 0.001,
        "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
        "tonne": 1000.0, "tonnes": 1000.0, "ton": 1000.0,
        "pound": 0.45359237, "pounds": 0.45359237, "lb": 0.45359237,
        "ounce": 0.0283495231, "ounces": 0.0283495231, "oz": 0.0283495231,
    },
    "time": {
        "s": 1.0, "second": 1.0, "seconds": 1.0, "sec": 1.0,
        "min": 60.0, "minute": 60.0, "minutes": 60.0,
        "h": 3600.0, "hour": 3600.0, "hours": 3600.0, "hr": 3600.0,
        "day": 86400.0, "days": 86400.0,
        "week": 604800.0, "weeks": 604800.0,
        "year": 31557600.0, "years": 31557600.0,
    },
    "volume": {
        "ml": 0.001, "millilitre": 0.001, "milliliter": 0.001,
        "l": 1.0, "litre": 1.0, "liter": 1.0, "litres": 1.0,
        "gallon": 3.785411784, "gallons": 3.785411784,
    },
    "area": {
        "cm2": 0.0001, "cm^2": 0.0001, "sq cm": 0.0001,
        "m2": 1.0, "m^2": 1.0, "sq m": 1.0, "square metre": 1.0,
        "km2": 1_000_000.0, "km^2": 1_000_000.0,
        "hectare": 10000.0, "hectares": 10000.0,
        "acre": 4046.8564224, "acres": 4046.8564224,
        "sq ft": 0.09290304, "square foot": 0.09290304,
    },
}

_TEMP_UNITS = {"celsius", "fahrenheit", "kelvin", "c", "f", "k"}
_CONVERT_WORD_RE = re.compile(r"\bconvert\b", re.I)
_CONVERT_UNIT_RE = re.compile(
    r"\d\s*(km|cm|mm|miles?|kg|grams?|litres?|liters?|hours?|minutes?|"
    r"seconds?|inches|feet|yards?|pounds?|ounces?|hectares?|acres?)\b"
    r".{0,12}?\b(to|in)\b",
    re.I,
)


def _find_category(u1, u2):
    for cat, table in _UNITS.items():
        if u1 in table and u2 in table:
            return cat, table
    return None, None


def _norm_unit(u: str) -> str:
    return u.strip().lower().replace("²", "2").replace("³", "3")


def _to_celsius(v, u):
    if u in ("f", "fahrenheit"):
        return (v - 32) * 5 / 9
    if u in ("k", "kelvin"):
        return v - 273.15
    return v


def _from_celsius(v, u):
    if u in ("f", "fahrenheit"):
        return v * 9 / 5 + 32
    if u in ("k", "kelvin"):
        return v + 273.15
    return v


def _wave65_units(q):
    """Wave 65: unit asks in the shapes the trilingual
    batteries used — "how many grams are there in 4.25 kg"
    (the are-there form), composite times ("2 hours 30
    minutes in seconds"), bare unit facts ("how many
    minutes in an hour"), dozens, and a time stated as a
    fraction of a day."""
    import re as _re
    from fractions import Fraction as _F
    N = r"(\d+(?:\.\d+)?)"
    # Composite time -> seconds.
    m = _re.search(N + r"\s*hours?\s+(?:and\s+)?" + N +
                   r"\s*minutes?\s+(?:in|to|into)\s+seconds",
                   q, _re.I)
    if m:
        total = float(m.group(1)) * 3600 + float(m.group(2)) * 60
        total = int(total) if total == int(total) else total
        return {"type": "units", "op": "time_composite",
                "answer": f"{fmt_num(total)} seconds",
                "value": float(total),
                "steps": [
                    f"{m.group(1)} hours = "
                    f"{fmt_num(float(m.group(1)) * 3600)} "
                    f"seconds and {m.group(2)} minutes = "
                    f"{fmt_num(float(m.group(2)) * 60)} seconds",
                    f"Total = {fmt_num(total)} seconds"]}
    # "how many X are there in N Y" (are-there form).
    m = _re.search(r"how\s+many\s+([a-z]+)\s+(?:are\s+there\s+"
                   r")?in\s+" + N + r"\s*([a-z]+)", q, _re.I)
    if m:
        to_u, val, from_u = _norm_unit(m.group(1)), \
            float(m.group(2)), _norm_unit(m.group(3))
        cat, table = _find_category(from_u, to_u)
        if cat is not None:
            out = val * table[from_u] / table[to_u]
            return {"type": "units", "op": cat,
                    "answer": f"{fmt_num(out)} {to_u}",
                    "value": out,
                    "steps": [
                        f"{fmt_num(val)} {from_u} = "
                        f"{fmt_num(out)} {to_u}"]}
    # Bare unit facts: "how many minutes in an hour".
    m = _re.search(r"how\s+many\s+([a-z]+)\s+(?:are\s+there\s+"
                   r")?in\s+(?:an?|one)\s+([a-z]+)", q, _re.I)
    if m:
        facts = {("minutes", "hour"): 60, ("seconds", "hour"):
                 3600, ("hours", "day"): 24,
                 ("minutes", "day"): 1440,
                 ("seconds", "day"): 86400,
                 ("seconds", "minute"): 60,
                 ("hours", "week"): 168, ("days", "week"): 7,
                 ("minutes", "week"): 10080}
        key = (_norm_unit(m.group(1)), _norm_unit(m.group(2)))
        if key in facts:
            v = facts[key]
            return {"type": "units", "op": "unit_fact",
                    "answer": f"{v} {key[0]}", "value": float(v),
                    "steps": [
                        f"1 {key[1]} = {v} {key[0]}"]}
    # Dozens: "how many bananas in 5 dozen" / "5 dozen eggs,
    # how many eggs".
    m = _re.search(r"how\s+many\s+([a-z]+)\s+(?:are\s+there\s+"
                   r")?in\s+" + N + r"\s*dozen", q, _re.I)
    n = float(m.group(2)) if m else None
    if m is None:
        m = _re.search(N + r"\s*dozen\s+([a-z]+)", q, _re.I)
        if m:
            n = float(m.group(1))
    if m and n is not None and ("how many" in q.lower()
                                or "total" in q.lower()
                                or "kitne" in q.lower()):
        cnt = n * 12
        cnt = int(cnt) if cnt == int(cnt) else cnt
        return {"type": "units", "op": "dozen_count",
                "answer": str(cnt), "value": float(cnt),
                "steps": [
                    f"1 dozen = 12, so {fmt_num(n)} dozen = "
                    f"{fmt_num(n)} × 12 = {cnt}"]}
    # Minutes as a fraction of a day.
    m = _re.search(N + r"\s*minutes?\s+as\s+a\s+fraction\s+of"
                   r"\s+a\s+day", q, _re.I)
    if m:
        fr = _F(int(float(m.group(1))), 1440)
        return {"type": "units", "op": "fraction_of_day",
                "answer": f"{fr} ≈ {float(fr):.4f}",
                "value": float(fr),
                "steps": [
                    f"A day has 1440 minutes, so the fraction "
                    f"is {m.group(1)}/1440 = {fr}"]}
    return None


def solve_units(question: str):
    q = question.strip()
    _w65 = _wave65_units(q)
    if _w65 is not None:
        return _w65
    # Wave 13: "5 kg = how many grams" — value first, question
    # form second (the two patterns below cannot see this shape).
    # Wave 57: anaphoric form — "a rope is 3 metres long, how
    # many centimetres is that?" (same group order: value, from,
    # to; non-unit words fall out at _find_category below). The
    # two units must DIFFER — "12 days ... in how many days"
    # is a work-rate question, not a conversion.
    m0 = re.search(
        r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*=\s*how\s+many\s+"
        r"([a-zA-Z]+)", q, re.I)
    if not m0:
        _ma = re.search(
            r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\b[^0-9]{0,60}?"
            r"how\s+many\s+([a-zA-Z]+)", q, re.I)
        if _ma and _norm_unit(_ma.group(2)) != \
                _norm_unit(_ma.group(3)):
            m0 = _ma
    m = None if m0 else re.search(
        r"(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*([a-zA-Z°\^²2 ]+?)\s+"
        r"(?:to|into|in|=)\s+([a-zA-Z°\^²2 ]+?)\s*$",
        q, re.I,
    ) or re.search(
        r"how\s+many\s+([a-zA-Z°\^2 ]+?)\s+in\s+(-?\d+(?:\.\d+)?)\s*"
        r"([a-zA-Z°\^2 ]+)",
        q, re.I,
    )
    if m0:
        val, from_u, to_u = float(m0.group(1)), m0.group(2), \
            m0.group(3)
    elif not m:
        return None
    elif m.re.pattern.startswith("how"):
        to_u, val, from_u = m.group(1), float(m.group(2)), m.group(3)
    else:
        val, from_u, to_u = float(m.group(1)), m.group(2), m.group(3)
    from_u, to_u = _norm_unit(from_u), _norm_unit(to_u)

    # Temperature
    if from_u in _TEMP_UNITS and to_u in _TEMP_UNITS:
        c = _to_celsius(val, from_u)
        out = _from_celsius(c, to_u)
        steps = [
            "Use the temperature formulas: F = C × 9/5 + 32 and "
            "K = C + 273.15.",
            f"{fmt_num(val)} {from_u} = {fmt_num(c)} °C",
            f"= {fmt_num(out)} {to_u}",
        ]
        return {"type": "units", "op": "temperature",
                "answer": f"{fmt_num(out)} {to_u}", "value": out,
                "steps": steps}

    cat, table = _find_category(from_u, to_u)
    if cat is None:
        return None
    base_val = val * table[from_u]
    out = base_val / table[to_u]
    steps = [
        f"Convert to the base unit: {fmt_num(val)} {from_u} = "
        f"{fmt_num(base_val)} (base)",
        f"Convert to {to_u}: {fmt_num(base_val)} ÷ "
        f"{fmt_num(table[to_u])} = {fmt_num(out)}",
    ]
    return {"type": "units", "op": cat,
            "answer": f"{fmt_num(out)} {to_u}", "value": out,
            "steps": steps}
