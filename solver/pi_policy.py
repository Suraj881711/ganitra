"""Wave 99: the pi policy — ONE place where the pi rule lives.

Suraj's rule (decided 16 Nov 2026): "Asli pi se aaye toh jyada
achha hai; agar jaha 22/7 ki jarurat hai waha ye use karo" —
TRUE pi is the default everywhere; 22/7 is used ONLY where the
question needs it.

"Needs it" is defined mechanically and conservatively. A
school-style mensuration question (circle area / circumference,
cylinder / cone / sphere / hemisphere volume & surface area,
sectors / arcs, rings, frustums, wheels, wells) qualifies when
its CIRCULAR dimensions are designed for 22/7:

  * the radius is a positive multiple of 7 (7, 14, 21, ...), or
    the diameter it implies (2r) is a positive multiple of 7
    (so r = 3.5 qualifies via d = 7, r = 10.5 via d = 21); or
  * a stated diameter is a positive multiple of 7 (checked via
    its radius, d / 2, by the same rule); or
  * a stated circumference is a positive multiple of 22
    (44, 66, 88, ...), so r = C / (2 * 22/7) = 7C / 44 is exact.

Mixed rule: ONLY the circular dimensions decide. A height,
slant height, sector angle or any other dimension that is not
a multiple of 7 never blocks 22/7 (cylinder r = 7, h = 5 still
uses 22/7: 22/7 * 49 * 5 = 770, exact), and never triggers it.

Two-radius shapes (ring, frustum): EVERY radius must qualify —
with both radii multiples of 7 the pi coefficient (R^2 - r^2,
R + r, R^2 + Rr + r^2) is a multiple of 7, so 22/7 still gives
the clean textbook value; if only one radius qualifies, true
pi stays.

Everywhere else — non-7 radii, decimals like 7.5, trig, calculus,
symbolic answers — true pi is used exactly as before.
"""
import math
from fractions import Fraction

PI_227 = Fraction(22, 7)
PI_227_FLOAT = 22 / 7


def _pos_int(x):
    """x as a positive int if it is exactly integral, else None."""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    if f > 0 and f == int(f):
        return int(f)
    return None


def _fmt_dim(x):
    n = _pos_int(x)
    return str(n) if n is not None else f"{float(x):g}"


def _radius_reason(r):
    """Reason string if radius r qualifies for 22/7, else None."""
    if r is None:
        return None
    try:
        r = float(r)
    except (TypeError, ValueError):
        return None
    if r <= 0:
        return None
    n = _pos_int(r)
    if n is not None and n % 7 == 0:
        return f"radius {_fmt_dim(r)} is a multiple of 7"
    d = _pos_int(2 * r)
    if d is not None and d % 7 == 0:
        return (f"radius {_fmt_dim(r)} gives diameter {d}, "
                f"a multiple of 7")
    return None


def use_227(radius=None, diameter=None, circumference=None,
            radii=None):
    """True when the 22/7 rule fires for these dimensions."""
    return pi_choice(radius=radius, diameter=diameter,
                     circumference=circumference, radii=radii)[1]


def pi_choice(radius=None, diameter=None, circumference=None,
              radii=None):
    """(pi_value, used_227, reason) for a mensuration question.

    Pass exactly what the question gives: `radius`, or
    `diameter`, or a stated `circumference`, or `radii` (a list)
    for two-radius shapes. `reason` is a short English phrase
    for the working line, None when true pi is used.
    """
    if radii is not None:
        rs = [r for r in radii if r is not None]
        if rs and all(_radius_reason(r) is not None for r in rs):
            return PI_227_FLOAT, True, (
                "radii " + " and ".join(_fmt_dim(r) for r in rs)
                + " are multiples of 7")
        return math.pi, False, None
    if radius is not None:
        reason = _radius_reason(radius)
        if reason is not None:
            return PI_227_FLOAT, True, reason
        return math.pi, False, None
    if diameter is not None:
        try:
            d = float(diameter)
        except (TypeError, ValueError):
            return math.pi, False, None
        if _radius_reason(d / 2) is not None:
            return PI_227_FLOAT, True, (
                f"diameter {_fmt_dim(d)} is a multiple of 7")
        return math.pi, False, None
    if circumference is not None:
        n = _pos_int(circumference)
        if n is not None and n % 22 == 0:
            return PI_227_FLOAT, True, (
                f"circumference {n} is a multiple of 22")
        return math.pi, False, None
    return math.pi, False, None


def pi_value(radius=None, diameter=None, circumference=None,
             radii=None):
    """Just the pi value (float) for the given dimensions."""
    return pi_choice(radius=radius, diameter=diameter,
                     circumference=circumference, radii=radii)[0]


def pi_note(reason):
    """The working line shown when 22/7 is used (English steps)."""
    return (f"Take pi = 22/7 here — {reason}, so the answer "
            f"comes out exact.")


def pi_note_hi():
    """The same working line for Devanagari (Hindi) steps."""
    return "यहाँ pi = 22/7 लिया है, इसलिए उत्तर ठीक-ठीक आएगा।"
