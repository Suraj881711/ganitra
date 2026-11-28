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
    # Wave 156 (Wave 153 audit book-036): NCERT's spaced
    # typesetting prints the quadratic head as "27 x 2"
    # (27x^2) — the Wave 58 rule below read it as 27 x 2 =
    # 54 and served x = 11/2 for 27x^2 - 10x + 1 = 0. The
    # spaced power is recognisable when the SAME text also
    # uses x as a genuine variable (an x NOT flanked by
    # digits — "10 x + 1") and the digit-x-2/3 group sits at
    # a term head followed by an operator or the end. Pure
    # arithmetic ("3 x 4", "2^3 x 2^2") has no variable x
    # and is untouched.
    _head156 = re.search(
        r"(?:^|[=+\-])\s*(\d+(?:\.\d+)?)\s+[xX]\s+([23])"
        r"(?=\s*(?:[-+=]|$))", t)
    if _head156 and re.search(r"[xX](?!\s*\d)", t) and \
            re.search(r"(?<![\d.])[xX]\s*(?:[-+=]|$)", t):
        t = (t[:_head156.start()] +
             re.sub(r"(\d+(?:\.\d+)?)\s+[xX]\s+([23])",
                    r"\1*x^\2",
                    t[_head156.start():_head156.end()]) +
             t[_head156.end():])
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


def _fmt_exp(s):
    """Wave 231: SymPy's function spelling "exp(x)" is raw
    library output, not student text — the house style writes
    e^x. A single-token argument rides bare ("exp(-x)" ->
    "e^-x", "exp(x)" -> "e^x"); anything wider takes
    parentheses ("exp(x + 1)" -> "e^(x + 1)"). Balanced-paren
    scan, so nested calls convert inside-out and a malformed
    string is returned untouched rather than mangled."""
    out = []
    i = 0
    while True:
        k = s.find("exp(", i)
        if k < 0:
            out.append(s[i:])
            break
        if k > 0 and (s[k - 1].isalpha() or s[k - 1] == "_"):
            out.append(s[i:k + 4])
            i = k + 4
            continue
        depth = 0
        j = k + 3
        while j < len(s):
            if s[j] == "(":
                depth += 1
            elif s[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if j >= len(s):
            out.append(s[i:])
            break
        arg = _fmt_exp(s[k + 4:j])
        out.append(s[i:k])
        if re.fullmatch(r"-?[A-Za-z0-9]+", arg):
            out.append("e^" + arg)
        else:
            out.append("e^(" + arg + ")")
        i = j + 1
    return "".join(out)


_OO_RE = re.compile(r"(?<![A-Za-z])oo(?![A-Za-z])")
_IMAG_RE = re.compile(r"(?<![A-Za-z])I(?![A-Za-z])")


def fmt(value) -> str:
    """Human-friendly formatting for SymPy objects: x^2, 3·x, sqrt(2).

    Wave 231 (external-audit row): raw SymPy spellings must
    never reach a student. On top of the ** / * folds, three
    token-exact normalisations — none of them can change a
    value's meaning, they only change its spelling:
    "exp(x)" -> "e^x" (see _fmt_exp), a standalone "oo" ->
    "∞" (the letter-guarded pattern cannot touch "good",
    "floor", "zoo"…), and a standalone "I" -> "i" (the
    imaginary unit; guarded the same way, so "Interval" and
    prose words are safe)."""
    s = str(value)
    s = s.replace("**", "^").replace("*", "·")
    s = _fmt_exp(s)
    s = _OO_RE.sub("∞", s)
    s = _IMAG_RE.sub("i", s)
    return s


def fmt_set(sol, var) -> str:
    """Wave 231: a SymPy SET (a solveset result) as student
    text — "x < 1 or x > 2", never the raw
    "Union(Interval.open(-oo, 1), Interval.open(2, oo))".
    The conversion reads the set OBJECT, so it is exact by
    construction: interval ends and their open/closed flags
    become the matching inequality signs, infinite ends drop
    their side, a Union joins with "or", a FiniteSet lists
    its points as "x = a or x = b". Anything that is not a
    plain interval union / finite set (ConditionSet and
    friends) falls back to fmt() unchanged — an honest
    spelling, never an invented inequality."""
    v = str(var)
    try:
        if sol is sp.S.EmptySet:
            return "no solution"
        if sol == sp.S.Reals:
            return "all real numbers"
        if isinstance(sol, sp.FiniteSet):
            pts = sorted(sol.args, key=lambda e: float(sp.N(e)))
            return " or ".join(f"{v} = {fmt(p)}" for p in pts)
        if isinstance(sol, sp.Interval):
            return _fmt_interval(sol, v)
        if isinstance(sol, sp.Union):
            parts = []
            for arg in sol.args:
                if isinstance(arg, sp.Interval):
                    parts.append(_fmt_interval(arg, v))
                elif isinstance(arg, sp.FiniteSet):
                    parts.append(fmt_set(arg, var))
                else:
                    return fmt(sol)
            return " or ".join(parts)
    except Exception:
        pass
    return fmt(sol)


def _fmt_interval(iv, v):
    a, b = iv.start, iv.end
    if a == -sp.oo and b == sp.oo:
        return "all real numbers"
    if a == -sp.oo:
        sign = "<" if iv.right_open else "≤"
        return f"{v} {sign} {fmt(b)}"
    if b == sp.oo:
        sign = ">" if iv.left_open else "≥"
        return f"{v} {sign} {fmt(a)}"
    ls = "<" if iv.left_open else "≤"
    rs = "<" if iv.right_open else "≤"
    return f"{fmt(a)} {ls} {v} {rs} {fmt(b)}"


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
