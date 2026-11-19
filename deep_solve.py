"""Wave 134: the deep-solve stage — Ganitra tries HARDER to
solve the question ITSELF before giving up.

Suraj's order (17 Nov 2026): "Ganitra ka khud ka solver hona
chahiye, khud solve kare agar koi AI ans sahi nahi de raha
ho. Ganitra ki khud ki solve karne ki power honi chahiye."
The solver already runs FIRST (the AI legs are only a
fallback); this wave deepens that power at the one seam
where the app used to give up: the moment the honest layers
(solver, bank, MCQ, salvage, concepts) have all missed and
the chain is about to ask an AI brain — or accept one's
answer — or collapse to "Answer not found".

Two mechanisms, both strictly Ganitra's own work:

1. REFORMULATION RETRIES. The question is re-expressed in
   forms the existing solver owns — spelled-out numbers
   (English / Roman Hindi / Devanagari) turned into digits,
   a spelled equation assembled into symbols, Hindi phrasing
   swaps (guna / ghata / bhaag), the narrative wrapper
   stripped to its maths-bearing sentences, a two-ask
   question split and solved part-wise, and a few loose
   word-problem shapes (unitary cost, money-left, equal
   sharing) regenerated into the canonical shape the solver
   owns. Every variant is run through the REAL solver and
   the fallback layer's own real-answer gate, so a variant
   can only ever serve the answer the solver itself gives
   for that variant. Two question shapes are known to make
   the solver answer PARTIALLY (first leg / first part
   only) — the difference of two percent-ofs and the
   multi-leg total distance — so those are guarded by
   direct schemas that compute the true value themselves
   and run BEFORE any variant is tried.

2. METHOD TRANSFER. When an AI leg DID answer, its steps
   may carry a valid method wrapped around a wrong number
   (the classic AI arithmetic slip). The transfer reads the
   METHOD out of the AI's steps (percent-of, discount,
   simple interest, area, HCF/LCM, an equation written in
   the steps, an average, a bare arithmetic line), checks
   the method is a recognised valid schema for THIS
   question's ask, and RE-COMPUTES the whole thing from the
   question's own numbers with Ganitra's own machinery
   (SymPy / exact fractions). If the recomputation agrees
   with the AI's value, the AI answer stands untouched
   (this function returns None). If it disagrees, GANITRA'S
   OWN answer is served — own steps, own final line; the
   AI contributed only the idea, never the numbers. A
   wrong method (perimeter working for an area ask) is
   never rescued, and vague steps yield nothing.

BUDGETS (PythonAnywhere free): at most MAX_SOLVES solver
calls and MAX_SECONDS wall-clock per deep-solve invocation,
checked between attempts. The stage runs only on questions
the whole stock path already missed, so a normal solve
never pays for it; a normal not-found pays at most this
bounded stage instead of (or before) the AI chain.

TELEMETRY: every rescue is logged (question text + the
mechanism that rescued it, nothing else — the Wave 90
not-found log's pattern and privacy rule) into the
deep_solve_log table of the accounts DB, so future solver
waves can see which mechanisms earn their keep.

KILL SWITCH: GANITRA_DEEP_SOLVE=0 makes deep_solve()
return None immediately — the chain then behaves exactly
as it did before this wave.
"""
import math
import os
import re
import sqlite3
import time
from fractions import Fraction

MAX_SECONDS = 5.0
MAX_SOLVES = 8
MAX_VARIANTS = 6

# ---------------------------------------------------------------------------
# Small helpers: values, formatting, number extraction
# ---------------------------------------------------------------------------

_NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*/\s*\d+)?")


def _frac(text):
    """One number token ('12', '12.5', '3/4') as a Fraction,
    or None."""
    try:
        t = str(text).replace(" ", "").replace(",", "")
        if "/" in t:
            a, b = t.split("/", 1)
            return Fraction(int(a), int(b))
        return Fraction(t)
    except Exception:
        return None


def _numbers_in(text):
    """Every number in a text, as Fractions (order kept,
    duplicates kept — callers decide what they need)."""
    out = []
    for m in _NUM_RE.finditer(str(text or "")):
        v = _frac(m.group(0))
        if v is not None:
            out.append(v)
    return out


def _fmt(value):
    """A Fraction as Ganitra writes it: whole numbers bare,
    small fractions as a/b, anything else a trimmed
    decimal."""
    v = Fraction(value)
    if v.denominator == 1:
        return str(v.numerator)
    if v.denominator <= 100:
        return f"{v.numerator}/{v.denominator}"
    s = f"{float(v):.4f}".rstrip("0").rstrip(".")
    return s or "0"


def _parse_value(text):
    """The numeric value an answer string claims, or None:
    currency words/symbols stripped, the value after the
    last '=' preferred ('x = 5' -> 5), else the LAST number
    in the string (a final line carries its value last)."""
    t = str(text or "")
    if not t.strip():
        return None
    t = t.replace("₹", " ").replace(",", "")
    t = re.sub(r"\b(?:rs\.?|rupees|inr)\b", " ", t, flags=re.I)
    if "=" in t:
        t = t.rsplit("=", 1)[1]
    found = _numbers_in(t)
    return found[-1] if found else None


def _close(a, b):
    return a is not None and b is not None and abs(a - b) <= \
        Fraction(1, 10 ** 9)


# ---------------------------------------------------------------------------
# Number words -> digits (English / Roman Hindi / Devanagari)
# ---------------------------------------------------------------------------

_EN_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
_EN_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
_EN_SCALES = {
    "hundred": 100, "thousand": 1000, "lakh": 100000,
    "million": 1000000, "crore": 10000000,
}
_EN_WORDS = dict(_EN_ONES)
_EN_WORDS.update(_EN_TENS)
_EN_WORDS.update(_EN_SCALES)

# Sentence-level cues: a spelled number is only rewritten
# when its sentence is plainly a maths sentence. This is
# what keeps "one of the two numbers is 12" (no cue for
# "one", and an explicit idiom guard below) and ordinary
# prose untouched.
_MATH_CUES = {
    "%", "percent", "pratishat", "rupees", "rs", "km", "cm",
    "mm", "metre", "meter", "meters", "kg", "gram", "grams",
    "litre", "liter", "litres", "ml", "hour", "hours",
    "minute", "minutes", "second", "seconds", "day", "days",
    "week", "month", "months", "year", "years", "marks",
    "cost", "price", "sum", "total", "plus", "minus",
    "multiplied", "divided", "equal", "equals", "area",
    "perimeter", "interest", "profit", "loss", "discount",
    "half", "quarter", "double", "twice", "average", "mean",
    "speed", "distance", "side", "length", "breadth",
    "height", "radius", "sold", "bought", "spent", "left",
    "kitna", "kitne", "kitni", "hoga", "hoge", "batao",
    "yog", "guna", "bhaag", "daam", "keemat", "rupaye",
    "pratishat", "kharch", "bache", "each", "per",
}


def _seq_value(words, ones, tens, scales):
    """The value of one maximal number-word sequence, using
    the school composition rules (two hundred forty =
    2*100 + 40; four thousand six hundred = 4600)."""
    total = 0
    current = 0
    for w in words:
        if w in ones:
            current += ones[w]
        elif w in tens:
            current += tens[w]
        elif w in scales:
            scale = scales[w]
            if scale == 100:
                current = (current or 1) * 100
            else:
                total += (current or 1) * scale
                current = 0
        else:  # "and" inside a sequence
            continue
    return total + current


def _digitise_en(sentence):
    tokens = re.findall(r"[A-Za-z]+|[^A-Za-z]+", sentence)
    words = [t for t in tokens if t.isalpha()]
    lowered = [w.lower() for w in words]
    if not any(w in _EN_WORDS for w in lowered):
        return sentence
    if not any(w in _MATH_CUES or any(ch.isdigit() for ch in w)
               for w in lowered) and "%" not in sentence:
        return sentence
    out = []
    i = 0
    changed = False
    n = len(tokens)
    # Work on the word stream, then rebuild by replacing the
    # exact spans in the original token list.
    word_pos = [k for k, t in enumerate(tokens) if t.isalpha()]
    lw = [tokens[k].lower() for k in word_pos]
    spans = []  # (start_word_idx, end_word_idx, value)
    j = 0
    while j < len(lw):
        if lw[j] in _EN_WORDS:
            k = j
            seq = []
            while k < len(lw) and (lw[k] in _EN_WORDS or
                                   (lw[k] == "and" and seq and
                                    any(w in _EN_SCALES
                                        for w in seq) and
                                    k + 1 < len(lw) and
                                    lw[k + 1] in _EN_WORDS)):
                # "and" joins a number phrase ONLY after a
                # scale word ("two hundred and forty") —
                # elsewhere it separates two numbers ("the
                # sum of forty five and thirty six" is 45
                # and 36, never 81).
                seq.append(lw[k])
                k += 1
            core = [w for w in seq if w != "and"]
            # Idiom guards: a lone "one" in "one of / one
            # another / each one" is not a quantity.
            if core == ["one"]:
                nxt = lw[k] if k < len(lw) else ""
                prv = lw[j - 1] if j > 0 else ""
                if nxt in ("of", "another") or \
                        prv in ("each", "any", "every"):
                    j = k
                    continue
            spans.append((j, k, _seq_value(core, _EN_ONES,
                                           _EN_TENS, _EN_SCALES)))
            changed = True
            j = k
        else:
            j += 1
    if not changed:
        return sentence
    replaced = {}
    skip = set()
    for (a, b, v) in spans:
        replaced[a] = str(v)
        for x in range(a + 1, b):
            skip.add(x)
    wi = -1
    for k, t in enumerate(tokens):
        if t.isalpha():
            wi += 1
            if wi in skip:
                continue
            out.append(replaced.get(wi, t))
        else:
            # Drop a separator that sat INSIDE a replaced
            # sequence (between two of its words).
            prev_w = wi
            next_w = wi + 1
            if any(a <= prev_w and next_w < b
                   for (a, b, v) in spans):
                continue
            out.append(t)
    return "".join(out)


_HI_ONES = {
    "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5,
    "chhah": 6, "chhe": 6, "chhey": 6, "saat": 7, "aath": 8,
    "nau": 9, "das": 10, "gyarah": 11, "barah": 12,
    "terah": 13, "chaudah": 14, "pandrah": 15, "solah": 16,
    "satrah": 17, "atharah": 18, "unnis": 19, "bis": 20,
    "ikkis": 21, "bais": 22, "teis": 23, "chaubis": 24,
    "pachis": 25, "pachchis": 25, "chhabbis": 26,
    "sattais": 27, "athais": 28, "untis": 29, "tees": 30,
    "iktis": 31, "battis": 32, "taitis": 33, "chautis": 34,
    "paintis": 35, "chhattis": 36, "saintis": 37,
    "adtis": 38, "untalis": 39, "chalis": 40, "iktalis": 41,
    "bayalis": 42, "taintalis": 43, "chavalis": 44,
    "paintalis": 45, "chhiyalis": 46, "saintalis": 47,
    "adtalis": 48, "unchas": 49, "pachas": 50,
    "ikyavan": 51, "bavan": 52, "tirpan": 53, "chauvan": 54,
    "pachpan": 55, "chhappan": 56, "sattavan": 57,
    "athavan": 58, "unsath": 59, "saath": 60, "iksath": 61,
    "basath": 62, "tirsath": 63, "chausath": 64,
    "painsath": 65, "chhiyasath": 66, "sadsath": 67,
    "adsath": 68, "unhattar": 69, "sattar": 70,
    "ikhattar": 71, "bahattar": 72, "tihattar": 73,
    "chauhattar": 74, "pachhattar": 75, "chhihattar": 76,
    "sathattar": 77, "athhattar": 78, "unnasi": 79,
    "assi": 80, "ikyasi": 81, "bayasi": 82, "tirasi": 83,
    "chaurasi": 84, "pachasi": 85, "chhiyasi": 86,
    "sattasi": 87, "athasi": 88, "navasi": 89, "nabbe": 90,
    "ikyanve": 91, "banve": 92, "tiranve": 93,
    "chauranve": 94, "pachanve": 95, "chhiyanve": 96,
    "sattanve": 97, "athanve": 98, "ninyanve": 99,
    # Common alternate Roman spellings of the same words.
    "bees": 20, "gyara": 11, "bara": 12, "tera": 13,
    "chauda": 14, "pandra": 15, "sola": 16, "satra": 17,
    "athara": 18, "unees": 19, "ninyanwe": 99,
    "pachhees": 25,
}
_HI_SCALES = {
    "sau": 100, "hazaar": 1000, "hazar": 1000,
    "lakh": 100000, "crore": 10000000, "arab": 1000000000,
}
_HI_WORDS = dict(_HI_ONES)
_HI_WORDS.update(_HI_SCALES)
# A Roman-Hindi number word is rewritten ONLY inside a
# chain (next to a scale / another number word) or directly
# before a money/percent cue — a bare "do" is the verb
# "give" ("answer do"), a bare "ek" is the article "a".
_HI_CUES_AFTER = {"pratishat", "percent", "%", "rupaye",
                  "rs", "rupay", "rupya"}


def _digitise_hi(sentence):
    tokens = re.findall(r"[A-Za-z]+|[^A-Za-z]+", sentence)
    word_pos = [k for k, t in enumerate(tokens) if t.isalpha()]
    lw = [tokens[k].lower() for k in word_pos]
    if not any(w in _HI_WORDS for w in lw):
        return sentence
    spans = []
    j = 0
    while j < len(lw):
        if lw[j] in _HI_WORDS:
            k = j
            while k < len(lw) and lw[k] in _HI_WORDS:
                k += 1
            seq = lw[j:k]
            nxt = lw[k] if k < len(lw) else ""
            chained = len(seq) >= 2 or \
                any(w in _HI_SCALES for w in seq)
            cued = nxt in _HI_CUES_AFTER
            if chained or cued:
                spans.append((j, k, _seq_value(
                    seq, _HI_ONES, {}, _HI_SCALES)))
            j = k
        else:
            j += 1
    if not spans:
        return sentence
    replaced = {}
    skip = set()
    for (a, b, v) in spans:
        replaced[a] = str(v)
        for x in range(a + 1, b):
            skip.add(x)
    out = []
    wi = -1
    for k, t in enumerate(tokens):
        if t.isalpha():
            wi += 1
            if wi in skip:
                continue
            out.append(replaced.get(wi, t))
        else:
            if any(a <= wi and wi + 1 < b for (a, b, v) in spans):
                continue
            out.append(t)
    return "".join(out)


_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_DEV_ONES = {
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पाँच": 5,
    "पांच": 5, "छह": 6, "सात": 7, "आठ": 8, "नौ": 9,
    "दस": 10, "ग्यारह": 11, "बारह": 12, "तेरह": 13,
    "चौदह": 14, "पंद्रह": 15, "सोलह": 16, "सत्रह": 17,
    "अठारह": 18, "उन्नीस": 19, "बीस": 20, "पच्चीस": 25,
    "तीस": 30, "चालीस": 40, "पचास": 50, "साठ": 60,
    "सत्तर": 70, "अस्सी": 80, "नब्बे": 90,
}
_DEV_SCALES = {
    "सौ": 100, "हज़ार": 1000, "हजार": 1000,
    "लाख": 100000, "करोड़": 10000000,
}
_DEV_WORDS = dict(_DEV_ONES)
_DEV_WORDS.update(_DEV_SCALES)
_DEV_CUES_AFTER = {"प्रतिशत", "रुपये", "रुपए", "%"}


def _digitise_dev(sentence):
    sentence = sentence.translate(_DEV_DIGITS)
    tokens = re.findall(r"[^\s]+", sentence)
    lw = [t.strip(".,?!;:\"'।") for t in tokens]
    if not any(w in _DEV_WORDS for w in lw):
        return sentence
    spans = []
    j = 0
    while j < len(lw):
        if lw[j] in _DEV_WORDS:
            k = j
            while k < len(lw) and lw[k] in _DEV_WORDS:
                k += 1
            seq = lw[j:k]
            nxt = lw[k] if k < len(lw) else ""
            chained = len(seq) >= 2 or \
                any(w in _DEV_SCALES for w in seq)
            if chained or nxt in _DEV_CUES_AFTER:
                spans.append((j, k, _seq_value(
                    seq, _DEV_ONES, {}, _DEV_SCALES)))
            j = k
        else:
            j += 1
    if not spans:
        return sentence
    for (a, b, v) in reversed(spans):
        tokens[a:b] = [str(v)]
    return " ".join(tokens)


def digitise(text):
    """All three number-word passes over a whole text,
    sentence by sentence (the English pass gates on the
    sentence's own maths cues)."""
    parts = re.split(r"(?<=[.!?।])\s+", str(text or ""))
    out = []
    for part in parts:
        part = _digitise_en(part)
        part = _digitise_hi(part)
        part = _digitise_dev(part)
        out.append(part)
    return " ".join(out).strip()


# ---------------------------------------------------------------------------
# Symbol + phrasing variants
# ---------------------------------------------------------------------------

_SUPERSCRIPTS = str.maketrans({
    "⁰": "^0", "¹": "^1", "²": "^2", "³": "^3", "⁴": "^4",
    "⁵": "^5", "⁶": "^6", "⁷": "^7", "⁸": "^8", "⁹": "^9",
})


def _symbol_norm(text):
    t = str(text or "").translate(_SUPERSCRIPTS)
    t = t.replace("−", "-").replace("×", "*").replace("÷", "/")
    return t


def _spelled_equation(text):
    """'2 x plus 3 is equal to 11' -> '2x + 3 = 11'. Only
    when the text names an equality and carries a variable
    but has no '=' yet."""
    t = str(text or "")
    if "=" in t:
        return None
    low = t.lower()
    if "equal" not in low and "बराबर" not in t:
        return None
    if not re.search(r"\b[x-z]\b", low):
        return None
    t = re.sub(r"\bis equal to\b|\bequals\b|\bequal to\b",
               " = ", t, flags=re.I)
    t = re.sub(r"\bplus\b", " + ", t, flags=re.I)
    t = re.sub(r"\bminus\b", " - ", t, flags=re.I)
    t = re.sub(r"\bmultiplied by\b", " * ", t, flags=re.I)
    t = re.sub(r"\bdivided by\b", " / ", t, flags=re.I)
    t = re.sub(r"(\d)\s+([a-zA-Z])\b", r"\1\2", t)
    t = re.sub(r"\s+", " ", t).strip(" .,?!;:")
    if "=" not in t or not any(ch.isdigit() for ch in t):
        return None
    return t


def _hindi_phrase_swaps(text):
    """Deterministic Hindi operator phrases -> bare
    expressions: '15 ka 6 se guna karo' -> '15 * 6',
    '500 me se 200 ghatao' -> '500 - 200', '450 ko 9 se
    bhaag do' -> '450 / 9'."""
    t = str(text or "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ka|ke)\s*"
                  r"(\d+(?:\.\d+)?)\s*se\s*guna", t, re.I)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*me\s*se\s*"
                  r"(\d+(?:\.\d+)?)\s*ghata", t, re.I)
    if m:
        return f"{m.group(1)} - {m.group(2)}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*ko\s*"
                  r"(\d+(?:\.\d+)?)\s*se\s*bhaag", t, re.I)
    if m:
        return f"{m.group(1)} / {m.group(2)}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*aur\s*"
                  r"(\d+(?:\.\d+)?)\s*ka\s*guna", t, re.I)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    return None


def _reorder_if(text):
    """'What is the cost of 8 pens if 5 pens cost rupees
    75?' -> 'If 5 pens cost rupees 75, what is the cost of
    8 pens?' — the solver owns the statement-first shape."""
    m = re.match(r"^\s*what is (.+?)\s+if\s+(.+?)\s*\?\s*$",
                 str(text or ""), re.I)
    if not m:
        return None
    return f"If {m.group(2)}, what is {m.group(1)}?"


# ---------------------------------------------------------------------------
# Narrative stripping
# ---------------------------------------------------------------------------

# A sentence may be dropped ONLY when it carries no number,
# no percent and none of these condition/comparison words —
# dropping a condition would change the question.
_KEEP_MARKERS = (
    "more", "less", "than", "faster", "slower", "older",
    "younger", "twice", "thrice", "double", "triple",
    "half", "quarter", "total", "remaining", "left",
    "if", "when", "then", "before", "after", "each",
    "every", "per", "equal", "barabar", "zyada", "kam",
    "guna", "bhaag", "pratishat", "percent",
)


def _narrative_strip(text):
    """Drop the story sentences that carry no maths, keep
    every number-bearing or asking sentence."""
    parts = [p.strip() for p in
             re.split(r"(?<=[.!?।])\s+", str(text or ""))
             if p.strip()]
    if len(parts) < 3:
        return None
    kept = []
    dropped = 0
    for part in parts:
        low = part.lower()
        has_math = any(ch.isdigit() for ch in part) or \
            "%" in part
        asks = part.rstrip().endswith("?") or \
            low.startswith(("what", "find", "tell", "calculate",
                            "how", "kitna", "kitne", "batao"))
        risky = any(w in low for w in _KEEP_MARKERS)
        if has_math or asks or risky:
            kept.append(part)
        else:
            dropped += 1
    if not dropped or len(kept) < 2:
        return None
    if not any(ch.isdigit() for ch in " ".join(kept)):
        return None
    return " ".join(kept)


# ---------------------------------------------------------------------------
# Canonical cores: loose word-problem shapes the solver
# owns in exactly one phrasing. Extraction is role-pinned —
# every number's job is fixed by an explicit keyword, and a
# text with extra unexplained numbers is refused.
# ---------------------------------------------------------------------------

def _core_unitary(text):
    """Cost of M items = C, cost of N items = ? — EN and
    Roman-Hindi loose forms -> the canonical EN shape."""
    t = str(text or "")
    item = None
    m = re.search(r"cost of (\d+) ([a-z]+) is (?:rupees|rs\.?|₹)"
                  r"\s*(\d+)", t, re.I)
    if m:
        count1, item, cost = int(m.group(1)), m.group(2), m.group(3)
    else:
        m = re.search(r"(\d+|ek) ([a-z]+) k[ae] (?:daam|keemat|"
                      r"kimat)\s*(?:rupees|rs\.?|₹)?\s*(\d+)",
                      t, re.I)
        if m:
            count1 = 1 if m.group(1).lower() == "ek" else \
                int(m.group(1))
            item, cost = m.group(2), m.group(3)
        else:
            m = re.search(r"(\d+) ([a-z]+) cost (?:rupees|rs\.?|₹)"
                          r"\s*(\d+)", t, re.I)
            if m:
                count1, item, cost = int(m.group(1)), m.group(2), \
                    m.group(3)
    if not m:
        return None
    ask = re.search(r"cost of (\d+)|(\d+) " +
                    re.escape(item or "") +
                    r" ka kitna|(\d+) " + re.escape(item or "") +
                    r" k[ae] kitn", t, re.I)
    n = None
    if ask:
        n = next((g for g in ask.groups() if g), None)
    if n is None:
        # Roman-Hindi ask: "paanch notebook ka kitna hoga" —
        # the count is a Hindi number word the digitise pass
        # deliberately leaves alone outside a chain.
        ask_hi = re.search(r"([a-z]+) " +
                           re.escape(item or "") +
                           r" ka kitna", t, re.I)
        if ask_hi:
            n = _HI_ONES.get(ask_hi.group(1).lower())
    if n is None:
        return None
    n = int(n)
    if n == count1:
        return None
    canon = (f"If the cost of {count1} {item} is rupees {cost}, "
             f"what is the cost of {n} {item}?")
    return canon


def _core_money_left(text):
    """'had A rupees ... spent B ... how much left' ->
    the bare core 'A - B'. Refused when the text carries
    any third number (an earning/loss leg would change
    the meaning)."""
    t = str(text or "")
    nums = _numbers_in(t)
    if len(nums) != 2:
        return None
    low = t.lower()
    # Wave 185: a PERCENT anywhere in the text changes the
    # shape — "240 rupees hai, 35% kharch kar diye, kitne
    # bache" spends 35% OF the 240 (84), but the spent
    # regex below happily captures the bare 35 (the "%"
    # is just a non-digit to it) and the core served
    # 240 - 35 = 205. With exactly two numbers present, a
    # percent sign can only belong to one of them, so the
    # bare-subtraction core never applies.
    if "%" in t or "percent" in low or "pratishat" in low \
            or "प्रतिशत" in t:
        return None
    have = re.search(r"(?:has|had|have|ke paas|paas)\D{0,20}?"
                     r"(\d+(?:\.\d+)?)", low)
    spent = re.search(r"(?:spent|spend|gave|lost|paid|kharch)"
                      r"\D{0,20}?(\d+(?:\.\d+)?)", low)
    if not spent:
        # Hindi order: the amount comes BEFORE the verb —
        # "200 rupaye kharch kar diye".
        spent = re.search(r"(\d+(?:\.\d+)?)\D{0,15}?kharch",
                          low)
    left = any(w in low for w in ("left", "bacha", "bache",
                                  "bach", "remaining", "rest"))
    if not (have and spent and left):
        return None
    a, b = _frac(have.group(1)), _frac(spent.group(1))
    if a is None or b is None or a == b:
        return None
    return f"{_fmt(a)} - {_fmt(b)}"


def _core_equal_share(text):
    """'450 cm ribbon cut into 9 equal pieces' -> '450 / 9'.
    The word 'equal' (or 'barabar') is required, and the
    text must carry exactly two numbers."""
    t = str(text or "")
    nums = _numbers_in(t)
    if len(nums) != 2:
        return None
    low = t.lower()
    m = re.search(r"(?:cut|divided|divide|shared|share|split)"
                  r"\b[^.!?]{0,20}?\b(?:into|among)\s+(\d+)",
                  low)
    if not m and "barabar" in low:
        m = re.search(r"(\d+)\s*barabar", low)
    if not m:
        return None
    if "equal" not in low and "barabar" not in low:
        return None
    n = _frac(m.group(1))
    total = nums[0] if nums[1] == n else nums[1] \
        if nums[0] == n else None
    if total is None or n in (None, 0):
        return None
    return f"{_fmt(total)} / {_fmt(n)}"


_CORES = (("core:unitary", _core_unitary),
          ("core:money_left", _core_money_left),
          ("core:equal_share", _core_equal_share))


# ---------------------------------------------------------------------------
# Guard schemas: shapes where the stock solver answers
# PARTIALLY. These compute the true value themselves and
# run before any variant, so a partial solver answer can
# never be laundered into a rescue.
# ---------------------------------------------------------------------------

_PCT_OF_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:%|percent|pratishat)\s*of\s*"
    r"(\d+(?:\.\d+)?)", re.I)


def _schema_percent_pair(text):
    """Sum / difference of exactly two percent-ofs, with no
    other numbers in the question."""
    t = str(text or "")
    found = _PCT_OF_RE.findall(t)
    if len(found) != 2:
        return None
    used = set()
    for p, n in found:
        used.add(_frac(p))
        used.add(_frac(n))
    if any(v not in used for v in _numbers_in(t)):
        return None
    low = t.lower()
    (p1, n1), (p2, n2) = [(_frac(a), _frac(b)) for a, b in found]
    v1 = p1 * n1 / 100
    v2 = p2 * n2 / 100
    steps = [f"{_fmt(p1)}% of {_fmt(n1)} = {_fmt(v1)}",
             f"{_fmt(p2)}% of {_fmt(n2)} = {_fmt(v2)}"]
    if "difference" in low or "antar" in low:
        d = abs(v1 - v2)
        steps.append(f"Difference = {_fmt(max(v1, v2))} - "
                     f"{_fmt(min(v1, v2))} = {_fmt(d)}")
        return ("schema:percent_difference", _fmt(d), steps)
    if "sum" in low or "yog" in low or "total" in low:
        s = v1 + v2
        steps.append(f"Sum = {_fmt(v1)} + {_fmt(v2)} = {_fmt(s)}")
        return ("schema:percent_sum", _fmt(s), steps)
    return None


_LEG_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:km/h|km per hour|km/hr|kmph)"
    r"\s*for\s*(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|ghante)", re.I)


def _schema_multileg(text):
    """Total distance over 2+ speed-for-time legs, with no
    other numbers in the question (a '25% faster' leg
    carries an extra number and is refused, honestly)."""
    t = str(text or "")
    legs = _LEG_RE.findall(t)
    if len(legs) < 2:
        return None
    used = set()
    for s, h in legs:
        used.add(_frac(s))
        used.add(_frac(h))
    if any(v not in used for v in _numbers_in(t)):
        return None
    low = t.lower()
    if "distance" not in low and "doori" not in low:
        return None
    if "total" not in low and "kul" not in low:
        return None
    steps = []
    total = Fraction(0)
    for s, h in legs:
        d = _frac(s) * _frac(h)
        total += d
        steps.append(f"Distance = {_fmt(_frac(s))} × "
                     f"{_fmt(_frac(h))} = {_fmt(d)} km")
    steps.append(f"Total distance = {_fmt(total)} km")
    return ("schema:multileg_distance", _fmt(total), steps)


_SCHEMAS = (_schema_percent_pair, _schema_multileg)


# ---------------------------------------------------------------------------
# Multi-part splitting
# ---------------------------------------------------------------------------

_ASK_NOUNS = (
    "area", "perimeter", "circumference", "volume", "hcf",
    "lcm", "sum", "difference", "product", "mean", "average",
    "breadth", "length", "height", "diagonal", "surface area",
)


def _split_parts(text):
    """Split a two-ask question into standalone part
    questions, or None. Two shapes: (S1) two clauses joined
    by an explicit second-ask marker; (S2) 'Find the X and
    Y of <shared context>' with X, Y known ask nouns."""
    t = str(text or "").strip()
    parts = None
    m = re.split(r"\s*(?:\.\s*|\s+and\s+|\s*;\s*)also\s+"
                 r"(?:find|calculate)\s*", t, flags=re.I)
    if len(m) == 2 and all(any(ch.isdigit() for ch in p)
                           for p in m):
        head, tail = m
        verb = "Find " if re.search(r"\bfind\b", head, re.I) \
            else ""
        parts = [head.strip(" .,;"),
                 (verb + tail).strip(" .,;")]
    if parts is None:
        m = re.match(
            r"^\s*find\s+(?:the\s+)?([a-z ]+?)\s+and\s+"
            r"(?:the\s+)?([a-z ]+?)\s+of\s+(.+?)\s*\??\s*$",
            t, re.I)
        if m:
            x = m.group(1).strip().lower()
            y = m.group(2).strip().lower()
            ctx = m.group(3).strip()
            if x in _ASK_NOUNS and y in _ASK_NOUNS and \
                    any(ch.isdigit() for ch in ctx):
                parts = [f"Find the {x} of {ctx}",
                         f"Find the {y} of {ctx}"]
    if not parts or len(parts) != 2:
        return None
    if any(p.lower() == t.lower() for p in parts):
        return None
    return parts


# ---------------------------------------------------------------------------
# Method transfer: the AI's method, Ganitra's own numbers
# ---------------------------------------------------------------------------

def _factorisation_lines(a, b, pick):
    """Prime-factorisation step lines in the solver's own
    style, for the HCF/LCM transfer."""
    import sympy
    lines = []
    for n in (a, b):
        fac = sympy.factorint(int(n))
        bits = [f"{p}^{e}" if e > 1 else f"{p}"
                for p, e in sorted(fac.items())]
        lines.append(f"Prime factorisation: {n} = "
                     f"{' × '.join(bits) if bits else n}")
    return lines


def _t_percent_of(question, steps_text, ai_val):
    low_q = question.lower()
    if "discount" in low_q or "selling price" in low_q or \
            "deduct" in low_q:
        # The percent-of here is a SUB-PART of a price
        # question — the discount schema owns those; serving
        # the bare percent value would answer a different
        # question than the student asked.
        return None
    m = _PCT_OF_RE.search(question)
    if m:
        p, n = _frac(m.group(1)), _frac(m.group(2))
    else:
        # Hindi order: "240 ka 25 pratishat" — the base
        # first, the percent second, no "of".
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ka|ke|ki)\s*"
                      r"(\d+(?:\.\d+)?)\s*(?:pratishat|"
                      r"percent|%)", question, re.I)
        if not m:
            return None
        n, p = _frac(m.group(1)), _frac(m.group(2))
    if "%" not in steps_text and "percent" not in steps_text \
            and "pratishat" not in steps_text \
            and "/100" not in steps_text:
        return None
    v = p * n / 100
    steps = [f"{_fmt(p)}% of {_fmt(n)} = {_fmt(n)} × "
             f"{_fmt(p)}/100 = {_fmt(v)}"]
    return ("percent_of", v, steps, _fmt(v))


def _t_discount(question, steps, steps_text, ai_val):
    if "discount" not in steps_text or \
            "discount" not in question.lower():
        return None
    m = None
    for line in steps:
        m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*"
                      r"(\d+(?:\.\d+)?)", line)
        if m:
            break
    if not m:
        return None
    p, price = _frac(m.group(1)), _frac(m.group(2))
    if price not in _numbers_in(question):
        return None
    disc = p * price / 100
    final = price - disc
    low_q = question.lower()
    asks_amount = "how much discount" in low_q or \
        "discount amount" in low_q or \
        "discount kitna" in low_q or "chhoot kitni" in low_q
    asks_price = "selling price" in low_q or \
        "final price" in low_q or "price to pay" in low_q or \
        "kitne me" in low_q or "becha" in low_q
    # The steps demonstrate the selling price as their
    # final method when their last line is a computed
    # subtraction (price - discount = ...).
    steps_show_price = bool(steps) and "-" in steps[-1] and \
        "=" in steps[-1] and \
        _parse_value(steps[-1]) is not None
    if asks_amount and not asks_price:
        own = [f"Discount = {_fmt(p)}% of {_fmt(price)} = "
               f"{_fmt(disc)}"]
        return ("discount", disc, own, _fmt(disc))
    if asks_price or steps_show_price:
        own = [f"Discount = {_fmt(p)}% of {_fmt(price)} = "
               f"{_fmt(disc)}",
               f"Selling price = {_fmt(price)} - "
               f"{_fmt(disc)} = {_fmt(final)}"]
        return ("discount", final, own, _fmt(final))
    return None


def _t_simple_interest(question, steps_text, ai_val):
    letters_only = re.sub(r"[^a-z]", "", steps_text)
    if "interest" not in steps_text and \
            "prt" not in letters_only and \
            "si" not in steps_text.split():
        return None
    low = question.lower()
    pm = re.search(r"(?:on|of|principal(?:\s+of)?|sum of)\s+"
                   r"(?:rupees|rs\.?|₹)?\s*(\d+(?:\.\d+)?)", low)
    rm = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per cent)"
                   r"\s*(?:per annum|p\.a\.)?", low)
    tm = re.search(r"for\s+(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
                   low)
    if not (pm and rm and tm):
        return None
    p, r, t = (_frac(pm.group(1)), _frac(rm.group(1)),
               _frac(tm.group(1)))
    v = p * r * t / 100
    own = [f"SI = (P × R × T) / 100 = ({_fmt(p)} × "
           f"{_fmt(r)} × {_fmt(t)}) / 100 = {_fmt(v)}"]
    if "amount" in low and "interest" not in low:
        # The ask is the total amount, not the interest —
        # serving the bare SI would answer a different
        # question.
        total = p + v
        own.append(f"Amount = {_fmt(p)} + {_fmt(v)} = "
                   f"{_fmt(total)}")
        return ("simple_interest", total, own, _fmt(total))
    if "amount" in low and "interest" in low:
        # Both are asked; the transfer may only speak when
        # the AI's claim is attributable to one of them.
        total = p + v
        if ai_val is not None and _close(ai_val, total):
            own.append(f"Amount = {_fmt(p)} + {_fmt(v)} = "
                       f"{_fmt(total)}")
            return ("simple_interest", total, own,
                    _fmt(total))
        if ai_val is not None and _close(ai_val, v):
            return ("simple_interest", v, own, _fmt(v))
        return None
    return ("simple_interest", v, own, _fmt(v))


def _t_area(question, steps_text, ai_val):
    low = question.lower()
    if "area" not in low:
        return None
    # Wrong method shown (perimeter working for an area
    # ask) is never rescued.
    if "perimeter" in steps_text and "area" not in steps_text:
        return None
    if "rectangle" in low:
        lm = re.search(r"length\D{0,12}?(\d+(?:\.\d+)?)", low)
        bm = re.search(r"breadth\D{0,12}?(\d+(?:\.\d+)?)", low)
        if not (lm and bm):
            return None
        l, b = _frac(lm.group(1)), _frac(bm.group(1))
        if "×" not in steps_text and "*" not in steps_text \
                and "length" not in steps_text:
            return None
        v = l * b
        own = [f"Area = length × breadth = {_fmt(l)} × "
               f"{_fmt(b)} = {_fmt(v)}"]
        return ("area_rectangle", v, own, _fmt(v))
    if "square" in low:
        sm = re.search(r"side\D{0,12}?(\d+(?:\.\d+)?)", low)
        if not sm:
            return None
        s = _frac(sm.group(1))
        v = s * s
        own = [f"Area = side × side = {_fmt(s)} × {_fmt(s)} "
               f"= {_fmt(v)}"]
        return ("area_square", v, own, _fmt(v))
    if "triangle" in low:
        bm = re.search(r"base\D{0,12}?(\d+(?:\.\d+)?)", low)
        hm = re.search(r"height\D{0,12}?(\d+(?:\.\d+)?)", low)
        if not (bm and hm):
            return None
        b, h = _frac(bm.group(1)), _frac(hm.group(1))
        v = b * h / 2
        own = [f"Area = 1/2 × base × height = 1/2 × "
               f"{_fmt(b)} × {_fmt(h)} = {_fmt(v)}"]
        return ("area_triangle", v, own, _fmt(v))
    return None


def _t_hcf_lcm(question, steps_text, ai_val):
    low = question.lower()
    m = re.search(r"(\d+)\s+and\s+(\d+)", low)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    asks_hcf = "hcf" in low or "gcd" in low or \
        "महत्तम" in question
    asks_lcm = "lcm" in low or "लघुत्तम" in question
    if asks_hcf and not asks_lcm:
        if "hcf" not in steps_text and "gcd" not in steps_text:
            return None  # the steps did a different method
        v = math.gcd(a, b)
        own = _factorisation_lines(a, b, "hcf")
        own.append(f"HCF = {v}")
        return ("hcf", Fraction(v), own, str(v))
    if asks_lcm and not asks_hcf:
        if "lcm" not in steps_text:
            return None
        v = a * b // math.gcd(a, b)
        own = _factorisation_lines(a, b, "lcm")
        own.append(f"LCM = {v}")
        return ("lcm", Fraction(v), own, str(v))
    return None


_EQ_CAND_RE = re.compile(
    r"([0-9x][0-9x\s\+\-\*/\^\(\)\.]*=[0-9x\s\+\-\*/\^\(\)\.]+)")


def _t_equation(question, steps, ai_result):
    """The equation schema fires ONLY when the equation is
    the question's own ask and the AI's final claim is
    itself an x-answer. An equation that appears as an
    INTERMEDIATE step of another problem (the intersection
    equation inside an area-between-curves working) is not
    the AI's method for the asked quantity, and replacing
    that answer with the roots would be a wrong rescue —
    the Wave 119 probe is the pinned case. Agreement is
    decided here by root-SET comparison and reported
    pre-checked."""
    low = question.lower()
    if "=" not in question and "solve" not in low and \
            "equation" not in low and "समीकरण" not in question:
        return None
    ai_answer = str(ai_result.get("answer") or "")
    ai_roots = set()
    for m in re.finditer(r"x\s*=\s*(-?\d+(?:\.\d+)?"
                         r"(?:\s*/\s*\d+)?)", ai_answer):
        v = _frac(m.group(1))
        if v is not None:
            ai_roots.add(v)
    if not ai_roots:
        # Deploy-27 merge fix: a BARE numeric answer to an
        # equation-solve ask ("Solve: 3x + 5 = 20" -> "6") is
        # the AI's claimed root in context — the wave's own
        # fixture pins the rescue. The Wave-119 guard is
        # untouched: a bare claim only counts when the
        # QUESTION itself is the equation ask.
        bare = _frac(ai_answer.strip().rstrip("."))
        if bare is not None and "=" in question and (
                "solve" in low or "equation" in low
                or "हल" in question):
            ai_roots.add(bare)
    if not ai_roots:
        return None  # the AI did not finally claim roots
    qnums = set(_numbers_in(digitise(question)))
    for line in steps:
        m = _EQ_CAND_RE.search(str(line).replace("×", "*")
                                .replace("÷", "/"))
        if not m:
            continue
        eq = re.sub(r"\s+", "", m.group(1)).strip(".,;:")
        if "x" not in eq or eq.count("=") != 1:
            continue
        eq_nums = set(_numbers_in(eq))
        if not eq_nums or not eq_nums <= qnums:
            continue  # the AI invented a different problem
        try:
            import sympy
            from sympy.parsing.sympy_parser import (
                implicit_multiplication_application,
                standard_transformations)
            # Deploy-27 merge fix: stock parse_expr does NOT
            # apply implicit multiplication, so a step written
            # "5x" never parsed and this schema silently
            # declined every ordinary equation (the wave's own
            # tests pin the rescue). Same expressions, now
            # with the multiplication transform the schema
            # always assumed.
            _transforms = standard_transformations + (
                implicit_multiplication_application,)
            x = sympy.Symbol("x")
            lhs, rhs = eq.split("=")
            expr = sympy.parse_expr(
                lhs.replace("^", "**"),
                local_dict={"x": x},
                transformations=_transforms) - sympy.parse_expr(
                    rhs.replace("^", "**"),
                    local_dict={"x": x},
                    transformations=_transforms)
            sols = sympy.solve(expr, x)
        except Exception:
            continue
        if not sols:
            continue
        vals = []
        for s in sols:
            if s.is_real is False:
                continue
            try:
                vals.append(Fraction(s).limit_denominator(
                    10 ** 6) if not s.is_integer else
                    Fraction(int(s)))
            except Exception:
                vals.append(None)
        if not vals or any(v is None for v in vals):
            continue
        vals = sorted(set(vals))
        if set(vals) == ai_roots:
            return None  # agreement: the AI answer stands
        answer = "x = " + ", x = ".join(_fmt(v) for v in vals)
        own = [f"Equation: {eq}", answer]
        return ("equation", vals[0], own, answer, True)
    return None


def _t_average(question, steps_text, ai_val):
    low = question.lower()
    if "average" not in low and "mean" not in low:
        return None
    if "average" not in steps_text and "mean" not in steps_text:
        return None
    m = re.search(r"(?:of|numbers are|numbers:)\s*"
                  r"([\d\s,\.and]+?)(?:\?|$)", low)
    if not m:
        return None
    nums = _numbers_in(m.group(1))
    if len(nums) < 2:
        return None
    total = sum(nums, Fraction(0))
    v = total / len(nums)
    own = [f"Add all values: "
           f"{' + '.join(_fmt(n) for n in nums)} = "
           f"{_fmt(total)}",
           f"Divide by the count ({len(nums)}): "
           f"{_fmt(total)} ÷ {len(nums)} = {_fmt(v)}"]
    return ("average", v, own, _fmt(v))


_ARITH_SEG_RE = re.compile(
    r"([0-9][0-9\s\+\-\*/×÷\(\)\.\^]*=\s*-?[\d\./]+)")


def _t_arith_steps(question, steps, ai_val):
    """A bare arithmetic line rescues ONLY when it is the
    line that PRODUCED the AI's claimed value (its stated
    result equals the claim) — an intermediate computation
    whose value merely differs from the final answer is
    not the AI's final method and must never hijack it."""
    if ai_val is None:
        return None
    qnums = set(_numbers_in(digitise(question)))
    for line in reversed(steps):
        m = _ARITH_SEG_RE.search(str(line))
        if not m:
            continue
        seg = m.group(1)
        expr, _, stated = seg.partition("=")
        expr = expr.strip()
        if not any(op in expr for op in "+-*/×÷"):
            continue
        if not _close(_frac(stated.strip()), ai_val):
            continue  # not the producing line
        nums = _numbers_in(expr)
        if len(nums) < 2 or not set(nums) <= qnums:
            continue
        try:
            import sympy
            value = sympy.Rational(
                sympy.parse_expr(
                    expr.replace("×", "*").replace("÷", "/")
                    .replace("^", "**")))
            v = Fraction(int(value.p), int(value.q))
        except Exception:
            continue
        own = [f"{expr.strip()} = {_fmt(v)}"]
        return ("arith_steps", v, own, _fmt(v))
    return None


def _method_transfer(question, ai_result):
    """Recompute the AI's demonstrated method from the
    question's own numbers. Returns Ganitra's own result
    when the method is recognised AND its recomputed value
    DISAGREES with the AI's claimed value (or the claim is
    unparseable); None when the method is unrecognised,
    invalid for this ask, or the recomputation AGREES (the
    AI answer then stands exactly as it was)."""
    if not isinstance(ai_result, dict):
        return None
    steps = [str(s) for s in (ai_result.get("steps") or [])]
    if not steps:
        return None
    steps_text = " ".join(steps).lower()
    ai_val = _parse_value(ai_result.get("answer"))
    q = digitise(question)
    attempts = (
        lambda: _t_percent_of(q, steps_text, ai_val),
        lambda: _t_discount(q, steps, steps_text, ai_val),
        lambda: _t_simple_interest(q, steps_text, ai_val),
        lambda: _t_area(q, steps_text, ai_val),
        lambda: _t_hcf_lcm(q, steps_text, ai_val),
        lambda: _t_equation(question, steps, ai_result),
        lambda: _t_average(q, steps_text, ai_val),
        lambda: _t_arith_steps(question, steps, ai_val),
    )
    for attempt in attempts:
        try:
            got = attempt()
        except Exception:
            got = None
        if got is None:
            continue
        name, value, own_steps, answer = got[:4]
        pre_checked = len(got) > 4 and got[4]
        if not pre_checked:
            # The transfer may only replace the AI answer
            # when disagreement with the AI's OWN claimed
            # quantity is established. A schema with no
            # recomputed value never serves; a solid
            # recompute facing an UNPARSEABLE AI claim
            # serves (there is no claim to agree with).
            if value is None or ai_val is None:
                if not (value is not None and ai_val is None):
                    continue
            elif _close(value, ai_val):
                return None  # agreement: the AI stands
        return {
            "type": "Ganitra",
            "op": "deep_transfer",
            "answer": answer,
            "steps": own_steps,
            "fallback": True,
            "fallback_kind": "deep_solve",
            "deep_mechanism": f"transfer:{name}",
        }
    return None


# ---------------------------------------------------------------------------
# Telemetry (Wave 90's pattern: question text + tag only,
# never raises, killable)
# ---------------------------------------------------------------------------

_LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS deep_solve_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_norm TEXT NOT NULL UNIQUE,
    question_text TEXT NOT NULL,
    mechanism     TEXT,
    hits          INTEGER NOT NULL DEFAULT 1,
    first_seen    INTEGER NOT NULL,
    last_seen     INTEGER NOT NULL
)
"""


def _log_rescue(question, mechanism):
    if os.environ.get("GANITRA_DEEP_SOLVE_LOG", "1") \
            .strip() == "0":
        return False
    try:
        from accounts import db_path
        from bank import normalise_question
        norm = normalise_question(question)
        if not norm:
            return False
        now = int(time.time())
        conn = sqlite3.connect(db_path(), timeout=2.0)
        try:
            conn.execute(_LOG_SCHEMA)
            conn.execute(
                "INSERT INTO deep_solve_log (question_norm,"
                " question_text, mechanism, hits, first_seen,"
                " last_seen) VALUES (?, ?, ?, 1, ?, ?)"
                " ON CONFLICT(question_norm) DO UPDATE SET"
                " hits = hits + 1, last_seen = excluded"
                ".last_seen, mechanism = excluded.mechanism",
                (norm, str(question).strip()[:500], mechanism,
                 now, now))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def rescue_rows(db_path=None, limit=None):
    """Logged rescues as dicts, most-hit first — the
    owner/reporting reader (mirrors notfound_log)."""
    try:
        from accounts import db_path as _dp
        path = db_path or _dp()
    except Exception:
        return []
    if not os.path.isfile(path):
        return []
    try:
        conn = sqlite3.connect(path, timeout=2.0)
        try:
            conn.row_factory = sqlite3.Row
            found = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type="
                "'table' AND name='deep_solve_log'").fetchone()
            if not found:
                return []
            sql = ("SELECT question_norm, question_text,"
                   " mechanism, hits, first_seen, last_seen"
                   " FROM deep_solve_log ORDER BY hits DESC,"
                   " last_seen DESC")
            if limit is not None:
                rows = conn.execute(
                    sql + " LIMIT ?", (int(limit),)).fetchall()
            else:
                rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


# ---------------------------------------------------------------------------
# The stage
# ---------------------------------------------------------------------------

def _real(question, result):
    """The fallback layer's own real-answer gate (lazy
    import — fallback.py imports this module lazily too,
    so neither side can create a cycle)."""
    try:
        from fallback import _is_real
        return _is_real(question, result)
    except Exception:
        pass
    try:
        from i18n import solve_failed
        return isinstance(result, dict) and \
            not solve_failed(question, result) and \
            bool(str(result.get("answer") or "").strip())
    except Exception:
        return False


def _solve(text, counter):
    """One budgeted solver call, or None when the budget
    is spent."""
    if counter["solves"] >= MAX_SOLVES:
        return None
    if time.monotonic() > counter["deadline"]:
        return None
    counter["solves"] += 1
    try:
        from solver.router import solve_question
        return solve_question(text)
    except Exception:
        return None


def _tag(result, mechanism, variant=None):
    out = dict(result)
    out["fallback"] = True
    out["fallback_kind"] = "deep_solve"
    out["deep_mechanism"] = mechanism
    if variant is not None:
        out["deep_variant"] = variant
    return out


def _variants(question):
    """(mechanism, text) reformulations of the question,
    most faithful first, deduped, the original itself
    never included."""
    q = str(question or "").strip()
    out = []

    def add(mech, text):
        text = (text or "").strip()
        if not text or text.lower() == q.lower():
            return
        if any(text.lower() == t.lower() for _, t in out):
            return
        out.append((mech, text))

    digits = digitise(q)
    add("numbers", digits)
    syms = _symbol_norm(digits)
    add("symbols", syms)
    eq = _spelled_equation(syms)
    if eq:
        add("equation", eq)
    phrase = _hindi_phrase_swaps(syms)
    if phrase:
        add("phrase", phrase)
    add("reorder", _reorder_if(syms))
    add("strip", _narrative_strip(q))
    add("strip", _narrative_strip(syms))
    for mech, fn in _CORES:
        try:
            core = fn(syms)
        except Exception:
            core = None
        if core and core.lower() != syms.lower():
            add(mech, core)
    return out[:MAX_VARIANTS + 3]


def deep_solve(question, hindi=False, lang=None,
               lang_request=None, ai_result=None,
               student_class=None):
    """The deep-solve stage. Two call shapes:

    deep_solve(question) — reformulation retries + guard
    schemas + part-splitting. Returns Ganitra's own solved
    result, or None when nothing honestly solves.

    deep_solve(question, ai_result=<an AI leg's shaped
    result>) — METHOD TRANSFER only: recompute the AI's
    demonstrated method from the question's own numbers.
    Returns Ganitra's own result when the recomputation
    disagrees with the AI's claimed value; None when the
    method is unrecognised/invalid or the values agree
    (the caller then serves the AI answer untouched).

    Never raises. GANITRA_DEEP_SOLVE=0 disables the stage.
    """
    if os.environ.get("GANITRA_DEEP_SOLVE", "1").strip() \
            == "0":
        return None
    try:
        return _deep_solve(question, hindi=hindi, lang=lang,
                           lang_request=lang_request,
                           ai_result=ai_result,
                           student_class=student_class)
    except Exception:
        return None


def _deep_solve(question, hindi=False, lang=None,
                lang_request=None, ai_result=None,
                student_class=None):
    q = str(question or "").strip()
    if not q:
        return None

    # Method transfer: the AI answered; check its method,
    # not its numbers.
    if ai_result is not None:
        own = _method_transfer(q, ai_result)
        if own is not None:
            _log_rescue(q, own["deep_mechanism"])
        return own

    counter = {"solves": 0,
               "deadline": time.monotonic() + MAX_SECONDS}
    digits = digitise(q)

    # 1. Guard schemas on the (digitised) original — these
    # shapes make variant answers untrustworthy, so the
    # schema's own computation is the only rescue allowed.
    for schema in _SCHEMAS:
        try:
            got = schema(digits)
        except Exception:
            got = None
        if got is not None:
            mech, answer, steps = got
            result = {"type": "Ganitra", "op": "deep_schema",
                      "answer": answer, "steps": steps}
            out = _tag(result, mech)
            _log_rescue(q, mech)
            return out

    # 2. Multi-part splitting: every part must really
    # solve, through the real solver + the real gate.
    parts = _split_parts(digits)
    if parts and len(parts) >= 2:
        solved = []
        ok = True
        for part in parts:
            res = _solve(part, counter)
            if res is None or not _real(part, res):
                ok = False
                break
            solved.append((part, res))
        if ok:
            steps = []
            bits = []
            for i, (part, res) in enumerate(solved, 1):
                bits.append(f"({i}) {res.get('answer')}")
                psteps = res.get("steps") or []
                if psteps:
                    steps.append(f"({i}) {psteps[0]}")
                    steps.extend(str(s) for s in psteps[1:])
                else:
                    steps.append(f"({i}) {res.get('answer')}")
            result = {"type": "Ganitra", "op": "deep_split",
                      "answer": "; ".join(bits),
                      "steps": steps}
            out = _tag(result, "split")
            _log_rescue(q, "split")
            return out

    # 3. Reformulation variants through the real solver.
    for mech, variant in _variants(q):
        if counter["solves"] >= MAX_SOLVES or \
                time.monotonic() > counter["deadline"]:
            break
        res = _solve(variant, counter)
        if res is not None and _real(variant, res):
            out = _tag(res, mech, variant)
            _log_rescue(q, mech)
            return out
    return None


__all__ = ["deep_solve", "rescue_rows", "digitise",
           "MAX_SECONDS", "MAX_SOLVES", "MAX_VARIANTS"]
