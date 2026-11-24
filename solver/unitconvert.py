"""Wave 222 (DeepSeek Job 3): unit conversion, jad se.

WHY THIS MODULE EXISTS
----------------------
The live checker (ChatGPT Jobs A/B/C, 23 Nov 2026) caught:

    "3 ghante me kitne minute"  ->  "0 hours 3 minutes"   (sahi: 180)

ROOT CAUSE (mechanism, not symptom): the minutes<->hours block
inside solver/wave212.py's _time_calendar fired whenever a
question named BOTH a minute-word and an hour-word and carried
exactly one number — and then UNCONDITIONALLY treated that
number as MINUTES (divmod by 60).  It never asked the two
questions that decide a conversion: which unit is the number
attached to (the SOURCE) and which unit is being asked for
(the TARGET).  "3 ghante..." has its 3 attached to ghante
(hours) and asks for minutes, so the block converted the wrong
way and served "0 hours 3 minutes".  The genuine
hours->minutes branch below it was unreachable for these
shapes (and additionally demanded a convert-word — "convert /
badlo / mein" — missing the Roman "me" students actually
type).  A second defect rode along: the composite serve glued
its parts in the chat rendering ("0 hours3 minutes").

And for every non-time family there was NO Hinglish path at
all: solver/units.py is English-only and the router only tries
it on "convert" / "how many", so "2.5 kg ko gram me badlo",
"3 litre me kitne ml", "45 mm ko cm me badlo" fell through to
the expression parser and errored.

THE FIX (this module, per DeepSeek Job 3's verified spec —
stdlib-only, exact Fraction arithmetic, steps in the
question's language): a conversion is read STRUCTURALLY —

  * a quantity (digits, a decimal, a fraction "1/2", or a
    Hinglish quantity word — ek / do / dedh / dhai / aadha /
    pauna / sawa) sitting immediately before a unit word:
    that unit is the SOURCE;
  * exactly one OTHER unit of the SAME category elsewhere in
    the question: that unit is the TARGET;
  * an ask marker (kitne / how many / badlo / convert / in /
    to / me / ko / = ...) somewhere in the text.

Anything else — two quantity attachments (stories, SDT,
composite times like "2 hours 30 minutes in seconds"), two
possible targets, a % in the text, a clock time, a speed
unit — returns None and the pre-Wave-222 flow decides.  The
solver never guesses a direction again.

Wave 212's broken block now delegates here, and the router
tries this module before the Wave 212 gate, so every path
shares this one source of truth.
"""

import re
from fractions import Fraction

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _fold(text):
    t = str(text or "").translate(_DEV_DIGITS).lower()
    t = t.replace("−", "-").replace("–", "-").replace("—", "-")
    return t


# ----------------------------------------------------------------------
# Unit tables.  factor = how many BASE units one unit is
# (base: second, metre, gram, millilitre).  disp = display
# names per language as (singular, plural); length / mass use
# their symbols in every language, as students write them.
# ----------------------------------------------------------------------

def _u(factor, aliases, en, hi, dev):
    return {"factor": factor, "aliases": aliases,
            "disp": {"en": en, "hi": hi, "dev": dev}}


_CATEGORIES = {
    "time": {
        "hour": _u(Fraction(3600),
                   ("hours", "hour", "hrs", "hr", "ghante",
                    "ghanta", "ghanti", "घंटे", "घण्टे", "घंटा",
                    "घण्टा"),
                   ("hour", "hours"), ("ghanta", "ghante"),
                   ("घंटा", "घंटे")),
        "minute": _u(Fraction(60),
                     ("minutes", "minute", "minuts", "minut",
                      "mins", "min", "मिनट", "मिनिट"),
                     ("minute", "minutes"), ("minute", "minute"),
                     ("मिनट", "मिनट")),
        "second": _u(Fraction(1),
                     ("seconds", "second", "secs", "sec",
                      "सेकंड", "सेकण्ड", "सैकंड"),
                     ("second", "seconds"), ("second", "second"),
                     ("सेकंड", "सेकंड")),
        "day": _u(Fraction(86400),
                  ("days", "day", "din", "दिन"),
                  ("day", "days"), ("din", "din"),
                  ("दिन", "दिन")),
    },
    "length": {
        "km": _u(Fraction(1000),
                 ("kilometres", "kilometre", "kilometers",
                  "kilometer", "km", "किलोमीटर", "किमी"),
                 ("km", "km"), ("km", "km"), ("km", "km")),
        "m": _u(Fraction(1),
                ("metres", "metre", "meters", "meter", "m",
                 "मीटर"),
                ("m", "m"), ("m", "m"), ("m", "m")),
        "cm": _u(Fraction(1, 100),
                 ("centimetres", "centimetre", "centimeters",
                  "centimeter", "cm", "सेंटीमीटर", "सेन्टीमीटर",
                  "सेमी"),
                 ("cm", "cm"), ("cm", "cm"), ("cm", "cm")),
        "mm": _u(Fraction(1, 1000),
                 ("millimetres", "millimetre", "millimeters",
                  "millimeter", "mm", "मिलीमीटर", "मिमी"),
                 ("mm", "mm"), ("mm", "mm"), ("mm", "mm")),
    },
    "mass": {
        "kg": _u(Fraction(1000),
                 ("kilograms", "kilogram", "kg", "किलोग्राम",
                  "किलो"),
                 ("kg", "kg"), ("kg", "kg"), ("kg", "kg")),
        "g": _u(Fraction(1),
                ("grams", "gram", "g", "ग्राम"),
                ("g", "g"), ("g", "g"), ("g", "g")),
        "mg": _u(Fraction(1, 1000),
                 ("milligrams", "milligram", "mg", "मिलीग्राम"),
                 ("mg", "mg"), ("mg", "mg"), ("mg", "mg")),
    },
    "volume": {
        "litre": _u(Fraction(1000),
                    ("litres", "litre", "liters", "liter", "l",
                     "लीटर"),
                    ("litre", "litres"), ("litre", "litre"),
                    ("लीटर", "लीटर")),
        "ml": _u(Fraction(1),
                 ("millilitres", "millilitre", "milliliters",
                  "milliliter", "ml", "मिलीलीटर", "मिली"),
                 ("ml", "ml"), ("ml", "ml"), ("ml", "ml")),
    },
}

# alias -> (category, canonical unit).  Longest aliases are
# matched first so "minutes" claims its span before "min"
# or "m" can nibble at it.
_ALIAS_MAP = {}
for _cat, _units in _CATEGORIES.items():
    for _canon, _info in _units.items():
        for _a in _info["aliases"]:
            _ALIAS_MAP[_a] = (_cat, _canon)
_ALIASES = sorted(_ALIAS_MAP, key=len, reverse=True)


def _unit_mentions(t):
    """All unit mentions as (start, end, category, canon,
    alias-as-written), non-overlapping, longest alias first.
    A mention glued to a following digit or ^ is a squared /
    cubed unit (cm2, m^3) — an area / volume shape, not a
    conversion — and is rejected."""
    found = []
    for alias in _ALIASES:
        if any("\u0900" <= ch <= "\u097f" for ch in alias):
            pat = re.compile(re.escape(alias))
        else:
            pat = re.compile(r"(?<![a-z])" + re.escape(alias)
                             + r"(?![a-z])")
        for m in pat.finditer(t):
            s, e = m.span()
            if e < len(t) and (t[e].isdigit() or t[e] == "^"):
                continue
            if any(s < fe and e > fs
                   for fs, fe, _, _, _ in found):
                continue
            cat, canon = _ALIAS_MAP[alias]
            found.append((s, e, cat, canon, alias))
    found.sort()
    return found


# ----------------------------------------------------------------------
# Quantities: digits / decimals / fractions, plus Hinglish and
# English quantity words (only ever read when glued to the
# unit that follows them, so a stray "do" the verb can never
# become a number).
# ----------------------------------------------------------------------

_QTY_WORDS = {
    "ek": Fraction(1), "do": Fraction(2), "teen": Fraction(3),
    "char": Fraction(4), "chaar": Fraction(4),
    "paanch": Fraction(5), "chhe": Fraction(6),
    "saat": Fraction(7), "aath": Fraction(8),
    "nau": Fraction(9), "das": Fraction(10),
    "gyarah": Fraction(11), "barah": Fraction(12),
    "aadha": Fraction(1, 2), "aadhi": Fraction(1, 2),
    "pauna": Fraction(3, 4), "paune": Fraction(3, 4),
    "sawa": Fraction(5, 4), "dedh": Fraction(3, 2),
    "dhai": Fraction(5, 2),
    "एक": Fraction(1), "दो": Fraction(2), "तीन": Fraction(3),
    "चार": Fraction(4), "पाँच": Fraction(5),
    "आधा": Fraction(1, 2), "आधी": Fraction(1, 2),
    "डेढ़": Fraction(3, 2), "ढाई": Fraction(5, 2),
    "पौना": Fraction(3, 4), "पौने": Fraction(3, 4),
    "सवा": Fraction(5, 4),
    # English number words are deliberately NOT read here:
    # the deep-solve "numbers" rescue owns spelled-out
    # English ("How many minutes are there in two hours?"
    # is its pinned battery row) and serves it correctly.
}

_NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*/\s*\d+|\d+(?:\.\d+)?")
_WORD_QTY_RE = re.compile(
    r"(?<![a-z\u0900-\u097f])("
    + "|".join(re.escape(w) for w in
               sorted(_QTY_WORDS, key=len, reverse=True))
    + r")(?![a-z\u0900-\u097f])")


def _quantities(t):
    """All quantity tokens as (start, end, Fraction)."""
    out = []
    for m in _NUM_RE.finditer(t):
        s, e = m.span()
        txt = m.group(0).replace(" ", "")
        try:
            if "/" in txt:
                a, b = txt.split("/", 1)
                if int(b) == 0:
                    continue
                val = Fraction(int(a), int(b))
            else:
                val = Fraction(txt)
        except (ValueError, ZeroDivisionError):
            continue
        out.append((s, e, val))
    for m in _WORD_QTY_RE.finditer(t):
        out.append((m.start(), m.end(), _QTY_WORDS[m.group(1)]))
    out.sort()
    return out


_ASK_MARKERS = (
    "kitne", "kitna", "kitni", "कितने", "कितना", "कितनी",
    "how many", "how much", "badlo", "badal", "बदलो", "बदल",
    "convert", "kaise", "कैसे", "bolenge", "बोलेंगे",
    "hote", "होते", "hoga", "batao", "बताओ",
)
_ASK_LOOSE_RE = re.compile(r"\b(?:in|into|to|me|mein|ko)\b"
                           r"|में|को|=")


def _has_ask(t):
    if any(mk in t for mk in _ASK_MARKERS):
        return True
    return _ASK_LOOSE_RE.search(t) is not None


def _language(t):
    if any("\u0900" <= ch <= "\u097f" for ch in t):
        return "dev"
    if any(w in t for w in ("ghant", "kitne", "kitna", "badlo",
                            "mein", "batao", "hote", "hoga",
                            "dedh", "dhai", "aadha")):
        return "hi"
    return "en"


def _fmt(fr):
    """Fraction -> clean student string (int, trimmed decimal
    for school-friendly denominators, else a/b)."""
    fr = Fraction(fr).limit_denominator(100000)
    if fr.denominator == 1:
        return str(fr.numerator)
    if fr.denominator in (2, 4, 5, 8, 10, 20, 25, 50, 100,
                          200, 1000):
        s = f"{float(fr):.4f}".rstrip("0").rstrip(".")
        return s
    return f"{fr.numerator}/{fr.denominator}"


# Display family of an alias AS WRITTEN by the student: the
# answer names each unit in the student's own word for it —
# "hours" in the question earns "hours" in the answer, never
# a silent swap to "ghante", and vice versa.  Words shared
# by English and Hinglish ("minute", "second") follow the
# question's language; symbols are the same in every family.
_HI_ROMAN = {"ghante", "ghanta", "ghanti", "din"}
_SHARED = {"minute", "minutes", "minut", "minuts", "min",
           "mins", "second", "seconds", "sec", "secs"}


def _family(alias, qlang):
    if any("\u0900" <= ch <= "\u097f" for ch in alias):
        return "dev"
    if alias in _HI_ROMAN:
        return "hi"
    if alias in _SHARED:
        return "hi" if qlang in ("hi", "dev") else "en"
    return "en"


def _disp(cat, canon, family, value):
    sing, plur = _CATEGORIES[cat][canon]["disp"][family]
    return sing if value == 1 else plur


def solve_unitconvert(question: str):
    """DeepSeek Job 3 unit conversion, or None.  Never
    raises, never guesses a direction."""
    try:
        return _solve(_fold(question))
    except Exception:
        return None


def _solve(t):
    if not t.strip():
        return None
    # Vetoes: percentages, clock times and speed units are
    # other families' shapes, however unit-laden they look.
    if "%" in t or "percent" in t or "प्रतिशत" in t:
        return None
    if re.search(r"\d\s*:\s*\d\d", t):
        return None
    if re.search(r"km\s*/\s*h|kmph|km\s+per\s+hour|"
                 r"\bm\s*/\s*s\b", t):
        return None
    if not _has_ask(t):
        return None

    mentions = _unit_mentions(t)
    if len(mentions) < 2:
        return None
    quantities = _quantities(t)

    # Attach each quantity to the unit mention that follows
    # it with nothing but whitespace between.  A conversion
    # has EXACTLY ONE such attachment — two means a story,
    # an SDT sum, or a composite ("2 hours 30 minutes in
    # seconds", which solver/units.py owns).
    attached = []
    for qs, qe, qv in quantities:
        for ms, me, cat, canon, alias in mentions:
            if ms >= qe and t[qe:ms].strip() == "":
                attached.append((qv, cat, canon, alias))
                break
    if len(attached) != 1:
        return None
    qty, cat, src, src_alias = attached[0]

    # The target: exactly one OTHER unit of the same category.
    targets = {canon for _, _, c, canon, _ in mentions
               if c == cat and canon != src}
    if len(targets) != 1:
        return None
    tgt = targets.pop()
    tgt_alias = next(a for _, _, _, canon, a in mentions
                     if canon == tgt)

    src_f = _CATEGORIES[cat][src]["factor"]
    tgt_f = _CATEGORIES[cat][tgt]["factor"]
    result = qty * src_f / tgt_f
    ratio = src_f / tgt_f  # result = qty * ratio

    lang = _language(t)
    src_fam = _family(src_alias, lang)
    tgt_fam = _family(tgt_alias, lang)
    src_d = _disp(cat, src, src_fam, qty)
    tgt_d = _disp(cat, tgt, tgt_fam, result)
    if ratio.denominator == 1 and ratio >= 1:
        steps = [
            f"1 {_disp(cat, src, src_fam, Fraction(1))} = "
            f"{_fmt(ratio)} {_disp(cat, tgt, tgt_fam, ratio)}",
            f"{_fmt(qty)} {src_d} = {_fmt(qty)} × "
            f"{_fmt(ratio)} = {_fmt(result)} {tgt_d}",
        ]
    elif ratio.numerator == 1 and ratio < 1:
        div = ratio.denominator
        steps = [
            f"1 {_disp(cat, tgt, tgt_fam, Fraction(1))} = "
            f"{div} {_disp(cat, src, src_fam, Fraction(div))}",
            f"{_fmt(qty)} {src_d} = {_fmt(qty)} ÷ {div} = "
            f"{_fmt(result)} {tgt_d}",
        ]
    else:
        steps = [
            f"1 {_disp(cat, src, src_fam, Fraction(1))} = "
            f"{_fmt(ratio)} {_disp(cat, tgt, tgt_fam, ratio)}",
            f"{_fmt(qty)} {src_d} = {_fmt(qty)} × "
            f"{_fmt(ratio)} = {_fmt(result)} {tgt_d}",
        ]
    return {"type": "units", "op": cat,
            "answer": f"{_fmt(result)} {tgt_d}",
            "value": float(result),
            "steps": steps}
