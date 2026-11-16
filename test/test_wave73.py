"""Wave 73: bol-chaal arithmetic + the word-soup guard.

Suraj (16 Nov 2026): students typing basic +, -, x on chat
were failing — "aisa nhi hona chahiye". Probing the live
solve path found the symbol forms all fine, but:
  "5 into 4"      -> answered "20*i*n*o*t"  (letter soup)
  "50 ka aadha"   -> answered "50*a**3*d*h" (letter soup)
  "9 ka varg"     -> answered "9*a*g*r*v"   (letter soup)
  "5 aur 4 guna"  -> answered "20*a*g*n*u"  (letter soup)
  "5 mein se 3 ghatao" / "50 se 20 ghatao" /
  "difference of 9 and 4" / "double of 7"   -> not found
Fix: primary word patterns for those shapes in
solver/arithmetic.py (_wave73_word_arithmetic) + a guard
(_is_word_soup73) that refuses any "simplified" answer
whose symbols are just the letters of one ordinary word.
"""
import re

from api import _solve_friendly

SOLVES = {
    "5 into 4": "20",
    "12 into 3": "36",
    "5 aur 4 guna": "20",
    "50 ka aadha": "25",
    "7 ka dugna": "14",
    "double of 7": "14",
    "9 ka varg": "81",
    "3 ka ghan": "27",
    "5 mein se 3 ghatao": "2",
    "50 se 20 ghatao": "30",
    "10 me se 4 gaya to kitna bacha": "6",
    "difference of 9 and 4": "5",
    "difference of 4 and 9": "5",
}

REGRESSION = {
    "2+2": "4", "5*4": "20", "7×8": "56", "9÷3": "3",
    "1/2+1/3": "5/6", "2^10": "1024", "5 guna 4": "20",
    "subtract 3 from 5": "2", "square of 9": "81",
    "10 percent of 250": "25",
}

_SOUP = re.compile(r"\b[a-z](?:\*[a-z]\b|\*\*)")


def _ans(q):
    return str(_solve_friendly(q).get("answer", ""))


def test_wave73_bolchaal_solves():
    for q, want in SOLVES.items():
        got = _ans(q)
        assert got == want, f"{q!r}: got {got!r}, want {want!r}"


def test_wave73_no_letter_soup_answers():
    for q in ("5 into 4", "50 ka aadha", "9 ka varg",
              "5 aur 4 guna", "5 by 4"):
        got = _ans(q)
        assert not _SOUP.search(got), f"{q!r}: soup answer {got!r}"


def test_wave73_basics_unchanged():
    for q, want in REGRESSION.items():
        got = _ans(q)
        assert got == want, f"{q!r}: got {got!r}, want {want!r}"


def test_word_soup_guard_unit():
    import sympy as sp
    from solver.arithmetic import _is_word_soup73
    i, n, t, o, x, a, b = sp.symbols("i n t o x a b")
    assert _is_word_soup73("5 into 4", 20 * i * n * t * o)
    # Sentence soup: the symbols are spread over several
    # ordinary words ("5 mein se 3 ghata" was served as
    # 15*a**2*e**2*g*h*i*m*n*s*t before this guard).
    e, g, h, m, s = sp.symbols("e g h m s")
    assert _is_word_soup73("5 mein se 3 ghata",
                           15 * a**2 * e**2 * g * h * i * m * n * s * t)
    assert not _is_word_soup73("simplify 2x + 3x", 5 * x)
    assert not _is_word_soup73("expand (a+b) in steps", a + b)
    assert not _is_word_soup73("evaluate 2a + 3b", 2 * a + 3 * b)
