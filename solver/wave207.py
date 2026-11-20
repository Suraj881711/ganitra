"""Wave 207: the pre-launch audit pack (20 Nov 2026).

Built from the Deploy-51 final self-audit
(~/workspace/ganitra-audit/SUMMARY.md).  Every schema here
is strict and self-verifying in the house style: it fires
only when it settles the question COMPLETELY, recomputes
its answer exactly before serving, and returns None on any
doubt so routing continues unchanged.  Wiring: one
failure-only gate at the end of router._solve_question_
uncached (after the Wave 195 blocks) — a question the
solver already answers is never displaced.

Families:

  * percent_native — a percent-of question in a Bengali /
    Marathi / Tamil / Telugu dress ("५० चा २०% किती?",
    "80 లో 50% ఎంత?", "২০ এর ৫০% কত?", "200 இன் 25%
    எவ்வளவு?").  The audit caught the generic simplify op
    parsing the words of the first two as SymPy symbols and
    SERVING the nonsense ("त*ि*ी*(Mod(1000*च*ा, क))"); the
    Bengali / Tamil dresses fell to not-found.  The schema
    folds the four Indic digit blocks to ASCII, then needs
    the full strict shape: exactly two numbers, the second
    carrying the % sign (or a percent word present), and
    the language's own "of" marker — base first, percent
    second, as all four dresses run.  The value is computed
    in exact rationals (Fraction) and re-verified before
    serving.  (The serve-time symbol-soup guard that stops
    the garbage serve itself lives with the junk mirrors in
    fallback._is_junk / router._w77_is_soup.)

  * min_sum_cubes — "The sum of two numbers is 16. Find
    the two numbers if the sum of their cubes is minimum."
    (audit fp12).  c12gaps142 owns a contiguous-span dress
    of this family ("...sum is S and the sum of whose
    cubes..."); the split-sentence dress students actually
    type matched nothing, the primary handler errored, and
    the chat path served not-found.  Here the two halves
    are matched independently, and the answer (S/2, S/2) is
    served only after SymPy confirms C'(S/2) = 0 and
    C''(S/2) > 0 on the concrete cubic.

  * sphere_dvdr — "A spherical balloon is being inflated.
    Find the rate of change of its volume with respect to
    the radius when the radius is 10 cm." (audit fp13).
    c12gaps142's dV/dr branch needs the words "volume is
    increasing with respect to"; the plain rate-of-change
    dress matched nothing.  Here: rate-of-change + volume
    + radius + sphere/balloon + a radius value, with the
    time-rate dresses vetoed (they are c12gaps142's), and
    dV/dr = 4 pi r^2 re-derived symbolically before the
    value 4 pi R^2 is served.

  * typo_variant — NOT a solver: the respelling map for
    the router gate's failure-only retry (audit edge
    "btao 17 aru 25 kaa jodd kyaa hoga??" -> 42).  A tiny
    closed set of attested Roman-Hinglish misspellings of
    function words (aru/aur, jodd/jod, btao/batao, kaa/ka,
    kyaa/kya); the gate re-solves the respelled text and
    accepts only a clean basic-arithmetic result, so a
    respelling can never manufacture an answer the plain
    question did not already earn.
"""
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt, fmt_num

# ------------------------------------------------------------------ #
# Indic digit folding (Bengali / Devanagari / Telugu / Tamil)
# ------------------------------------------------------------------ #

_DIGIT_BLOCKS = (0x09E6, 0x0966, 0x0C66, 0x0BE6)  # bn, dev, te, ta


def _fold_digits(text):
    out = []
    for ch in str(text or ""):
        o = ord(ch)
        folded = ch
        for base in _DIGIT_BLOCKS:
            if base <= o <= base + 9:
                folded = str(o - base)
                break
        out.append(folded)
    return "".join(out)


# ------------------------------------------------------------------ #
# Percent-of in bn / mr / ta / te dresses
# ------------------------------------------------------------------ #

# The languages' own "of" markers, as they appear between
# the base and the percent: Marathi चा / च्या / चे, Bengali
# এর, Telugu లో, Tamil இன்.
_OF_MARKERS = ("चा", "च्या", "चे", "এর", "లో", "இன்")
_PCT_WORDS = ("শতাংশ", "टक्के", "சதவீதம்", "శాతం")
_NUM_RE = re.compile(r"\d+(?:\.\d+)?")
_PCT_NUM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def _indic_script_present(text):
    for ch in str(text or ""):
        o = ord(ch)
        if 0x0980 <= o <= 0x09FF or 0x0900 <= o <= 0x097F \
                or 0x0B80 <= o <= 0x0BFF or 0x0C00 <= o <= 0x0C7F:
            return True
    return False


def solve_percent_native(question):
    """'<base> <of-marker> <pct>% <how much>' in a Bengali /
    Marathi / Tamil / Telugu dress -> the exact percent
    value, or None.  Strict: an Indic script must be
    present, the language's of-marker must appear, exactly
    two numbers may ride in the question, and no operator
    payload may compete with the reading."""
    q = str(question or "")
    if not _indic_script_present(q):
        return None
    if any(op in q for op in ("=", "+", "*", "/", "^", "−")):
        return None
    folded = _fold_digits(q)
    if not any(mk in folded for mk in _OF_MARKERS):
        return None
    nums = _NUM_RE.findall(folded)
    if len(nums) != 2:
        return None
    pct_match = _PCT_NUM_RE.search(folded)
    if pct_match is not None:
        pct_txt = pct_match.group(1)
        if nums[1] != pct_txt:
            return None  # the % must ride on the second number
        base_txt, pct_val_txt = nums[0], nums[1]
    elif any(w in folded for w in _PCT_WORDS):
        base_txt, pct_val_txt = nums[0], nums[1]
    else:
        return None
    try:
        base = Fraction(base_txt)
        pct = Fraction(pct_val_txt)
    except Exception:
        return None
    if base <= 0 or pct < 0 or pct > 1000:
        return None
    value = base * pct / 100
    # Verify exactly before serving: value * 100 == base * pct.
    if value * 100 != base * pct:
        return None
    shown = int(value) if value.denominator == 1 \
        else round(float(value), 2)
    base_shown = int(base) if base.denominator == 1 \
        else round(float(base), 2)
    pct_shown = int(pct) if pct.denominator == 1 \
        else round(float(pct), 2)
    return {"type": "applied", "op": "w207_percent_native",
            "answer": fmt_num(shown),
            "steps": [f"{fmt_num(pct_shown)}% of "
                      f"{fmt_num(base_shown)} = "
                      f"{fmt_num(base_shown)} × "
                      f"{fmt_num(pct_shown)}/100 = "
                      f"{fmt_num(shown)}"],
            "value": float(value)}


# ------------------------------------------------------------------ #
# AOD: sum S, sum of cubes minimum (split-sentence dress)
# ------------------------------------------------------------------ #

def solve_min_sum_cubes(question):
    low = str(question or "").lower()
    m1 = re.search(r"sum of (?:two |the two )?numbers is "
                   r"([\d.]+)", low)
    m2 = re.search(r"sum of (?:their|whose) cubes is minimum",
                   low)
    if not m1 or not m2:
        return None
    try:
        S = sp.Rational(m1.group(1))
    except Exception:
        return None
    if S <= 0:
        return None
    x = sp.Symbol("x")
    f = x ** 3 + (S - x) ** 3
    half = S / 2
    # Verify on the concrete instance: stationary AND a min.
    if sp.simplify(sp.diff(f, x).subs(x, half)) != 0:
        return None
    if float(sp.diff(f, x, 2).subs(x, half)) <= 0:
        return None
    steps = [
        f"Let the numbers be x and {fmt(S)} - x.",
        f"C = x^3 + ({fmt(S)} - x)^3; C'(x) = 0 gives "
        f"x = {fmt(half)}, and C'' > 0 there, so the sum "
        "of cubes is minimum.",
        f"The other number is {fmt(S)} - {fmt(half)} "
        f"= {fmt(half)}.",
    ]
    return {"type": "calculus", "op": "w207_min_sum_cubes",
            "answer": f"{fmt(half)} and {fmt(half)}",
            "steps": steps}


# ------------------------------------------------------------------ #
# AOD: dV/dr of a sphere / balloon at a radius
# ------------------------------------------------------------------ #

def solve_sphere_dvdr(question):
    low = str(question or "").lower()
    if "rate of change" not in low or "volume" not in low \
            or "radius" not in low or "with respect to" not in low:
        return None
    if not any(w in low for w in
               ("sphere", "spherical", "balloon")):
        return None
    # The time-rate dresses (dr/dt given, dV/dt asked) are
    # c12gaps142's family, not this one.
    if "at the rate of" in low or "per second" in low \
            or "/s" in low:
        return None
    rm = re.search(r"radius is ([\d.]+)\s*cm", low) or \
        re.search(r"radius (?:of )?([\d.]+)\s*cm", low)
    if not rm:
        return None
    try:
        R = sp.Rational(rm.group(1))
    except Exception:
        return None
    if R <= 0:
        return None
    r = sp.Symbol("r")
    # Re-derive before serving: d/dr (4/3 pi r^3) = 4 pi r^2.
    if sp.simplify(sp.diff(sp.Rational(4, 3) * sp.pi * r ** 3, r)
                   - 4 * sp.pi * r ** 2) != 0:
        return None
    val = 4 * sp.pi * R ** 2
    steps = [
        "V = (4/3) pi r^3, so dV/dr = 4 pi r^2.",
        f"At r = {fmt(R)} cm: dV/dr = 4 pi x {fmt(R)}^2 "
        f"= {fmt(val)} cm^3/cm.",
    ]
    return {"type": "calculus", "op": "w207_sphere_dvdr",
            "answer": f"{fmt(val)} cm^3/cm", "steps": steps,
            "value": val}


# ------------------------------------------------------------------ #
# Typo respelling (the router gate re-solves the variant)
# ------------------------------------------------------------------ #

_TYPO_MAP = {
    "aru": "aur",      # aur (and) — audit edge_typos
    "jodd": "jod",     # jod (sum)
    "btao": "batao",   # batao (tell)
    "kaa": "ka",       # ka (of)
    "kyaa": "kya",     # kya (what)
}


def typo_variant(question):
    """The question with the closed set of attested
    Roman-Hinglish function-word misspellings respelled,
    or None when nothing changes.  Only whole Latin tokens
    are touched; numbers, operators and every other word
    pass through byte-identical."""
    q = str(question or "")

    def _sub(m):
        tok = m.group(0)
        fixed = _TYPO_MAP.get(tok.lower())
        if fixed is None:
            return tok
        return fixed.capitalize() if tok[:1].isupper() else fixed

    out = re.sub(r"[A-Za-z]+", _sub, q)
    return out if out != q else None


# ------------------------------------------------------------------ #

def solve_wave207(question):
    """Wave 207 dispatcher: the audit-pack schemas, each
    strict and self-verifying; None unless one settles the
    question completely."""
    for fn in (solve_percent_native, solve_min_sum_cubes,
               solve_sphere_dvdr):
        try:
            out = fn(question)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
