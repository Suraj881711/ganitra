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


def solve_units(question: str):
    q = question.strip()
    # Wave 13: "5 kg = how many grams" — value first, question
    # form second (the two patterns below cannot see this shape).
    m0 = re.search(
        r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z]+)\s*=\s*how\s+many\s+"
        r"([a-zA-Z]+)", q, re.I)
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
