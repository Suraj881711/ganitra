"""Shared expression parsing helpers.

`parse_expression` is the heart of the solver: it turns free-form maths text
("2x + 3", "sin(x)/x", "x^2 - 5x + 6") into a SymPy expression, accepting
``^`` for powers and implicit multiplication ("2x" -> ``2*x``).
"""
import re

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    factorial_notation,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
    factorial_notation,
)

# Leading filler phrases that carry no maths meaning.
_FILLER_LEAD = (
    r"(?:what\s+is|calculate|compute|evaluate|find|work\s+out|solve\s+for|"
    r"simplify|the\s+value\s+of|value\s+of)\s+"
)


# Wave 74: circumference intent, tolerant of the common
# misspellings ("circumferance", "circumfrence", ...): every
# variant shares the stem "circumf". Exact-substring tests on
# "circumference" used to send a misspelt circumference ask
# down the AREA branch of the mensuration solver and compute
# pi*r^2 instead of 2*pi*r (Wave 71 audit, wrong case 1).
CIRCUMFERENCE_RE = re.compile(r"circumf\w*")


def wants_circumference(text) -> bool:
    """True when the text asks for a circumference, however
    the word is spelt."""
    return bool(CIRCUMFERENCE_RE.search(str(text).lower()))


def clean_text(text: str) -> str:
    """Normalise unicode operators and strip filler wording."""
    t = str(text).strip()
    # Wave 74: a fraction literal used as the DIVISOR must
    # stay grouped. "1/7 ÷ 2/7" used to flatten (÷ -> /) into
    # 1/7/2/7, which evaluates left-to-right as ((1/7)/2)/7 =
    # 1/98 instead of (1/7)/(2/7) = 1/2 (Wave 71 audit, wrong
    # case 3). "÷" is never part of a fraction, so a fraction
    # right after it is the divisor as a whole; the same
    # holds for a spaced "/" used as the division sign.
    # Unspaced slash chains ("1/2/3") keep their conventional
    # left-to-right reading.
    t = re.sub(r"÷\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)",
               r"÷(\1/\2)", t)
    t = re.sub(r"\s/\s+(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)",
               r" / (\1/\2)", t)
    # Wave 140: "√" must become a FUNCTION CALL, not the bare
    # word "sqrt" — the old chain replace turned "√144" into
    # "sqrt144", which SymPy tokenised letter by letter and
    # SERVED as "144*q*r*s*t". Wrap the radicand instead: a
    # bracketed group, a number (decimals included) or a
    # letter token. Two passes so a nested "√√16" resolves
    # inside-out (the sqrt(...) produced by the first pass is
    # a valid radicand for the second). Mirrors the correct
    # handling solver/calculus.py already had.
    for _ in range(2):
        t = re.sub(r"√\s*(sqrt\([^()]*\))", r"sqrt(\1)", t)
        t = re.sub(r"√\s*\(([^()]*)\)", r"sqrt(\1)", t)
        t = re.sub(r"√\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", t)
        t = re.sub(r"√\s*((?!sqrt\b)[A-Za-z]+)", r"sqrt(\1)", t)
    t = (
        t.replace("×", "*")
        .replace("÷", "/")
        .replace("−", "-")
        .replace("–", "-")
        .replace("√", "sqrt")
        .replace("π", "pi")
        .replace("≤", "<=")
        .replace("≥", ">=")
    )
    # Wave 56: a trailing full stop is sentence punctuation, not
    # maths — "Evaluate 12.5 + 7.25." failed to parse at all
    # because the final "." poisoned the last number token
    # (the same class of bug Wave 47 fixed locally for trig
    # identities). Strip it here, once, for every caller.
    t = re.sub(r"[?।.]+\s*$", "", t).strip()
    # Strip one or two leading filler phrases ("what is the value of ...").
    for _ in range(2):
        t2 = re.sub(r"^\s*" + _FILLER_LEAD, "", t, flags=re.I)
        if t2 == t:
            break
        t = t2.strip()
    # Wave 58: a standalone "x" between two numbers is a TIMES
    # sign in school typing — "2^3 x 2^2" was parsed as
    # 2^3 · x · 2^2 and "simplified" to 32·x, and "3 x 4"
    # became 12·x (Wave 55 trap). The rewrite fires only when
    # the text carries NO other letters (pi, from the π
    # replacement above, is allowed): with any other letter
    # present, x may be a genuine unknown and is left alone.
    _no_x = re.sub(r"\bpi\b", "", t).replace("x", "") \
        .replace("X", "")
    if not re.search(r"[a-zA-Z]", _no_x):
        t = re.sub(r"(?<=[\d\)])\s+[xX]\s+(?=[\d\(])",
                   " * ", t)
    return t


def parse_expression(text: str):
    """Parse maths text into a SymPy expression.

    Accepts ``^`` as power, implicit multiplication (``2x``, ``3(x+1)``),
    factorials (``5!``) and the usual SymPy function names.
    Raises ValueError with a readable message when parsing fails.
    """
    t = clean_text(text)
    if not t:
        raise ValueError("Empty expression.")
    # Rewrite sin^2(x) -> (sin(x))^2 and sin^2 x -> (sin(x))^2
    def _tp(m):
        inner = m.group(3)
        return f"({m.group(1)}({inner}))^{m.group(2)}"
    t = re.sub(r"\b(sin|cos|tan|cot|sec|csc)\s*\^\s*(\d+)\s*"
               r"\(\s*([^()]+)\s*\)", _tp, t)
    t = re.sub(r"\b(sin|cos|tan|cot|sec|csc)\s*\^\s*(\d+)\s+"
               r"([a-zA-Z])\b", _tp, t)
    try:
        result = parse_expr(t, transformations=_TRANSFORMS,
                            evaluate=True)
    except Exception as e:
        raise ValueError(f"Could not parse expression: {text!r}") from e
    # Wave 30: SymPy parses comma-separated text ("..., ...") into a
    # TUPLE of expressions. A natural-language sentence containing
    # commas (e.g. Suraj's Hindi train question) therefore used to
    # hand a tuple to callers, which then crashed on
    # `expr.free_symbols` ("'tuple' object has no attribute
    # 'free_symbols'") and the fallback layer masked the crash with
    # a similar example. A tuple is never a valid single expression
    # here — reject it with the same readable ValueError as any
    # other unparseable input, so this input class can never
    # hard-error a solver again.
    if isinstance(result, tuple):
        raise ValueError(f"Could not parse expression: {text!r}")
    return result


def is_equation(text: str) -> bool:
    """
    Detects if the given text is an equation.
    Returns True if it contains '=' but is not a calculus expression.
    """
    return "=" in text and not re.search(
        r"\b(?:limit|deriv|integr)\b", text, re.I
    )


def fmt(value) -> str:
    """Human-friendly formatting for SymPy objects: x^2, 3·x, sqrt(2)."""
    s = str(value)
    s = s.replace("**", "^").replace("*", "·")
    return s


def fmt_num(value) -> str:
    """Format a number: integers clean, fractions as a/b, else decimal."""
    if isinstance(value, float):
        # Genuine decimal input: keep decimal formatting (98.6, not 493/5).
        return str(int(value)) if value == int(value) else f"{value:.6g}"
    try:
        v = sp.nsimplify(value, rational=True)
    except Exception:
        v = value
    if isinstance(v, sp.Rational):
        if v.q == 1:
            return str(v.p)
        if v.q > 1000:  # decimal-derived, not a true fraction
            return f"{float(v):.6g}"
        return f"{v.p}/{v.q}"
    try:
        f = float(v)
    except Exception:
        return fmt(value)
    if f == int(f):
        return str(int(f))
    return f"{f:.6g}"


def extract_numbers(text: str):
    """All numbers appearing in the text, as ints/floats."""
    out = []
    for m in re.finditer(r"-?\d+(?:\.\d+)?", text):
        s = m.group(0)
        out.append(float(s) if "." in s else int(s))
    return out


def extract_points(text: str):
    """All (x, y) points in the text, e.g. '(1, 2) and (4, 6)'."""
    pts = []
    for m in re.finditer(
        r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)", text
    ):
        a, b = m.group(1), m.group(2)
        pts.append(
            (float(a) if "." in a else int(a), float(b) if "." in b else int(b))
        )
    return pts


def find_param(text: str, names, default=None):
    """Find 'radius 5', 'radius = 5', 'r=5' style parameters."""
    for name in names:
        m = re.search(
            rf"\b{name}\s*(?:=|is|of|:)?\s*(-?\d+(?:\.\d+)?)", text, re.I
        )
        if m:
            s = m.group(1)
            return float(s) if "." in s else int(s)
    return default
