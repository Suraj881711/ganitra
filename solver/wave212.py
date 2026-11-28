"""Wave 212: prediction-by-structure schemas + fix-queue families.

WHY THIS MODULE EXISTS (Suraj's phone test, 21 Nov 2026)
-------------------------------------------------------
The teeno-AI test loop's fix-queue (125 rows) is dominated by
questions whose MATHS is elementary but whose DRESS defeated
the router: the word-problem layers key on specific verb /
unit phrasings, so a rephrased, typo-ridden or language-mixed
ask fell through to not-found (locally) or to the slow AI
chain (live).  Suraj's standing order: prediction must work
by MEANING and NUMBERS, not fixed word patterns.

HOW THE PREDICTION LAYER WORKS HERE
-----------------------------------
``structural_features`` extracts what a question IS made of —
its numbers (decimals, Indian-grouped, Devanagari digits all
folded), ratio pairs, percent tokens, clock times, calendar
names, coordinate points, AP-shaped series, complex literals —
BEFORE any word matching.  Each schema below then keys on a
STRUCTURAL signature (e.g. "a ratio pair + a total + a part
ask", "two clock times", "a complex literal + the word
conjugate") and uses words only to disambiguate INSIDE the
family.  Typos in filler words therefore cannot break a
solve, and a rephrasing that keeps the numbers keeps the
answer.

DISCIPLINE (unchanged, Waves 133/206)
-------------------------------------
Every schema extracts the COMPLETE maths, recomputes the
answer deterministically (sympy / calendar / direct formula,
verified a second way where cheap), and returns None on any
doubt.  A schema never guesses: ambiguous structure falls
through to exactly the pre-Wave-212 flow.  Exact-match-only
bank rule untouched; nothing here serves a "similar"
question's answer.
"""

import calendar
import re
from fractions import Fraction

import sympy as sp

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _fold(text):
    """Lowercase, fold Devanagari digits, drop digit-grouping
    commas (1,00,000 -> 100000 — ONLY inside a real grouping
    pattern: a comma that separates coordinate pairs or list
    items, as in (-4,6) or 2,6,10, is NOT grouping and must
    survive), unify dashes."""
    t = str(text or "").translate(_DEV_DIGITS).lower()
    t = re.sub(r"\d{1,2}(?:,\d{2})*,\d{3}\b|\d{1,3}(?:,\d{3})+\b",
               lambda m: m.group(0).replace(",", ""), t)
    t = t.replace("−", "-").replace("–", "-").replace("—", "-")
    t = t.replace("₹", " rs ").replace("$", " ")
    # "45.75 रुपये" (number BEFORE the currency word) is
    # the same money shape as "rs 45.75".
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(?:रुपये|रुपया)",
               r"rs \1", t)
    return t


_CLOCK_RE = re.compile(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b")


def _mask_clocks(t):
    return _CLOCK_RE.sub(" CLOCK ", t)


def _nums(t):
    """All numbers in order, clock spans masked out."""
    return [float(x) if "." in x else int(x)
            for x in re.findall(r"\d+(?:\.\d+)?", _mask_clocks(t))]


def _clocks(t):
    """Clock times as (hour24, minute, raw_ampm)."""
    out = []
    for h, m, ap in _CLOCK_RE.findall(t):
        h, m = int(h), int(m)
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        out.append((h, m, ap or ""))
    return out


_RATIO_RES = (
    re.compile(r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)"),
    re.compile(r"(\d+(?:\.\d+)?)\s+is\s+to\s+(\d+(?:\.\d+)?)"),
    re.compile(r"(\d+(?:\.\d+)?)\s+to\s+(\d+(?:\.\d+)?)"),
)


def _ratio(t):
    for rx in _RATIO_RES:
        m = rx.search(t)
        if m:
            a, b = float(m.group(1)), float(m.group(2))
            if a > 0 and b > 0:
                return (a, b, m.span())
    return None


_MONTHS = {name: i + 1 for i, name in enumerate(
    ["january", "february", "march", "april", "may", "june",
     "july", "august", "september", "october", "november",
     "december"])}
_MONTHS.update({
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11,
    "dec": 12})
_MONTHS.update({
    "जनवरी": 1, "फ़रवरी": 2, "फरवरी": 2, "मार्च": 3, "अप्रैल": 4,
    "मई": 5, "जून": 6, "जुलाई": 7, "अगस्त": 8, "सितंबर": 9,
    "सितम्बर": 9, "अक्टूबर": 10, "नवंबर": 11, "नवम्बर": 11,
    "दिसंबर": 12, "दिसम्बर": 12})


def _months_in(t):
    """Month numbers present, longest names first, ASCII
    names on word boundaries (so 'mar' cannot hide inside
    another word).  Wave 212 battery: a one-letter-off
    month typo ("Augst") still names the month — a
    close-match fallback (ratio >= 0.84, tokens of 4+
    letters only) runs when the exact pass found fewer
    than two months."""
    found = []
    for name in sorted(_MONTHS, key=len, reverse=True):
        if name.isascii():
            hit = re.search(r"\b" + re.escape(name) + r"\b", t)
        else:
            hit = name in t
        if hit:
            found.append(_MONTHS[name])
    if len(set(found)) < 2:
        import difflib
        full = [n for n in _MONTHS if len(n) > 3
                and n.isascii()]
        exact = {n for n in _MONTHS if n.isascii()}
        for tok in re.findall(r"[a-z]{4,}", t):
            if tok in exact:
                continue
            close = difflib.get_close_matches(
                tok, full, n=1, cutoff=0.84)
            if close and _MONTHS[close[0]] not in found:
                found.append(_MONTHS[close[0]])
    return found
_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday",
             "friday", "saturday", "sunday"]
_WEEKDAYS_HI = {"सोमवार": 0, "मंगलवार": 1, "बुधवार": 2,
                "गुरुवार": 3, "शुक्रवार": 4, "शनिवार": 5,
                "रविवार": 6}


def structural_features(text):
    """The prediction layer's feature extraction: what the
    question is MADE OF, independent of its wording."""
    t = _fold(text)
    feats = {"numbers": _nums(t), "clock_times": _clocks(t),
             "has_percent": ("%" in t or "percent" in t
                             or "प्रतिशत" in t),
             "ratio": None, "points": [], "months": [],
             "weekday": None, "series": None}
    r = _ratio(t)
    if r:
        feats["ratio"] = (r[0], r[1])
    feats["points"] = [
        (int(a), int(b)) for a, b in re.findall(
            r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", t)]
    feats["months"] = _months_in(t)
    for i, name in enumerate(_WEEKDAYS):
        if name in t:
            feats["weekday"] = i
    for name, i in _WEEKDAYS_HI.items():
        if name in t:
            feats["weekday"] = i
    seq = _ap_series(t)
    if seq:
        feats["series"] = seq
    return feats


def _res(op, answer, steps, value=None, full_op=None,
         full_type=None):
    out = {"type": full_type if full_type else "word_problem",
           "op": full_op if full_op else "w212_" + op,
           "answer": str(answer), "steps": steps}
    if value is not None:
        try:
            out["value"] = float(value)
            out["numeric"] = float(value)
        except (TypeError, ValueError):
            pass
    return out


def _fmt(fr):
    """Fraction -> clean student string (int, fraction or
    trimmed decimal)."""
    fr = Fraction(fr).limit_denominator(100000)
    if fr.denominator == 1:
        return str(fr.numerator)
    if fr.denominator in (2, 4, 5, 8, 10, 20, 25, 50, 100,
                          200, 1000):
        s = f"{float(fr):.4f}".rstrip("0").rstrip(".")
        return s
    return f"{fr.numerator}/{fr.denominator}"


def _surd(n):
    """Exact root string for an integer: 52 -> '2√13'."""
    if n < 0:
        return None
    r = sp.sqrt(sp.Integer(n))
    s = str(r).replace("sqrt", "√").replace("*", "")
    return re.sub(r"√\((\d+)\)", r"√\1", s)


def _has(t, *words):
    return any(w in t for w in words)


# ----------------------------------------------------------------------
# Time / calendar / clock (test-loop cycle 21: 6 of 8 failed)
# ----------------------------------------------------------------------

def _clock_str(h, m):
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {ap}"


def _all_clock_times(t):
    """Colon times AND hour-only times ('8 बजे', '8 baje',
    '8 o'clock'), in text order."""
    found = []
    for m in _CLOCK_RE.finditer(t):
        h, mi = int(m.group(1)), int(m.group(2))
        ap = m.group(3) or ""
        if ap == "pm" and h < 12:
            h += 12
        if ap == "am" and h == 12:
            h = 0
        found.append((m.start(), h, mi))
    for m in re.finditer(r"\b(\d{1,2})\s*(?:बजे|baje|"
                         r"o'clock|o’clock)", t):
        found.append((m.start(), int(m.group(1)), 0))
    found.sort()
    return [(h, mi, "") for _, h, mi in found]


def _time_calendar(q, t):
    clocks = _all_clock_times(t)
    nums = _nums(t)

    # Weekday shift: <weekday> + "after N days / N din baad".
    feats_wd = None
    for i, name in enumerate(_WEEKDAYS):
        if name in t:
            feats_wd = i
    for name, i in _WEEKDAYS_HI.items():
        if name in t:
            feats_wd = i
    if feats_wd is not None and len(nums) == 1 and _has(
            t, "after", "baad", "बाद", "later"):
        n = int(nums[0])
        if 1 <= n <= 400:
            day = _WEEKDAYS[(feats_wd + n) % 7]
            return _res(
                "weekday_shift", day.capitalize(),
                [f"{_WEEKDAYS[feats_wd].capitalize()} + {n} days",
                 f"{n} mod 7 = {n % 7}, so count {n % 7} days "
                 f"ahead: {day.capitalize()}."])

    # Month days (single, pair sum, February leap).
    months = _months_in(t)
    years = [int(n) for n in nums
             if 1900 <= int(n) <= 2100]
    if months and _has(t, "din", "days", "day", "dys",
                       "दिन") \
            and not clocks:
        year = years[0] if years else 2023
        if len(set(months)) >= 2 and len(nums) <= 1:
            total = sum(calendar.monthrange(year, m)[1]
                        for m in set(months))
            names = " + ".join(
                calendar.month_name[m] for m in sorted(
                    set(months)))
            return _res(
                "month_days",
                f"{total} days",
                [f"{names} = {total} days in total."],
                value=total)
        if len(months) == 1 and len(nums) <= 1:
            d = calendar.monthrange(year, months[0])[1]
            leap = ""
            if months[0] == 2:
                leap = (f" ({year} is a leap year)"
                        if calendar.isleap(year) else
                        f" ({year} is not a leap year)")
            return _res(
                "month_days", f"{d} days",
                [f"{calendar.month_name[months[0]]} {year} "
                 f"has {d} days{leap}."], value=d)

    # Wave 222: unit conversion is owned by
    # solver/unitconvert.py (DeepSeek Job 3), which reads
    # the DIRECTION from the unit the number is attached
    # to.  The Wave 212 block that used to sit here fired
    # on ANY one-number question naming both a minute-word
    # and an hour-word and unconditionally treated the
    # number as minutes — "3 ghante me kitne minute" was
    # served "0 hours 3 minutes" (sahi: 180).  Delegate to
    # the shared converter; never guess a direction.
    if not clocks:
        try:
            from .unitconvert import solve_unitconvert
            _uc = solve_unitconvert(q)
        except Exception:
            _uc = None
        if _uc is not None:
            return _uc

    if len(clocks) == 2:
        (h1, m1, _), (h2, m2, _) = clocks
        start, end = h1 * 60 + m1, h2 * 60 + m2
        if end <= start:
            end += 12 * 60
        dur = end - start
        if 0 < dur <= 12 * 60 and _has(
                t, "tak", "duration", "how long", "kitne baje",
                "कितने बजे", "कितना समय", "lagta", "लगता",
                "कितने घंटे", "ghante", "घंटे", "रहते",
                "रहते है"):
            h, m = divmod(dur, 60)
            ans = (f"{h} hours {m} minutes" if m else
                   f"{h} hours")
            return _res(
                "duration", ans,
                [f"From {_clock_str(h1, m1)} to "
                 f"{_clock_str(h2 % 24, m2)}.",
                 f"Duration = {ans}."], value=dur / 60.0)

    if len(clocks) == 1:
        h, m, _ap = clocks[0]
        base = h * 60 + m
        rest = [n for n in nums]
        # Late arrival: start time + "N minutes late / der".
        if _has(t, "late", "der se", "देर", "delay") \
                and len(rest) == 1:
            add = int(rest[0])
            end = base + add
            return _res(
                "late_arrival",
                _clock_str(end // 60 % 24, end % 60),
                [f"Start: {_clock_str(h, m)}.",
                 f"{add} minutes late: {_clock_str(h, m)} + "
                 f"{add} min = "
                 f"{_clock_str(end // 60 % 24, end % 60)}."])
        # Start + duration -> end (movie/event finish asks).
        dur_nums = [n for n in rest]
        if len(dur_nums) == 2 and _has(
                t, "hour", "घंट") and _has(
                t, "min", "मिनट") and _has(
                t, "khatam", "end", "finish", "khatm",
                "खत्म", "समाप्त", "over"):
            total = int(dur_nums[0]) * 60 + int(dur_nums[1])
            end = base + total
            return _res(
                "end_time", _clock_str(end // 60 % 24,
                                       end % 60),
                [f"Start: {_clock_str(h, m)}.",
                 f"Length: {int(dur_nums[0])} hours "
                 f"{int(dur_nums[1])} minutes.",
                 f"Ends at "
                 f"{_clock_str(end // 60 % 24, end % 60)}."])
    return None


# ----------------------------------------------------------------------
# Unit conversion (structural: number + source unit + target
# unit + a conversion ask)
# ----------------------------------------------------------------------

_CONVERSIONS = [
    (("centimetre", "centimeter", "cm", "सेमी", "सेंटीमीटर"),
     ("metre", "meter", "मीटर", "m"), Fraction(1, 100), "m"),
    (("metre", "meter", "मीटर"),
     ("centimetre", "centimeter", "cm", "सेमी"), Fraction(100),
     "cm"),
    (("kilometre", "kilometer", "km", "किमी"),
     ("metre", "meter", "मीटर", "m"), Fraction(1000), "m"),
    (("metre", "meter", "मीटर"),
     ("kilometre", "kilometer", "km", "किमी"),
     Fraction(1, 1000), "km"),
    (("kilogram", "kg", "किलो"),
     ("gram", "ग्राम", "g"), Fraction(1000), "g"),
    (("gram", "ग्राम"),
     ("kilogram", "kg", "किलो"), Fraction(1, 1000), "kg"),
    (("litre", "liter", "लीटर", "l"),
     ("millilitre", "milliliter", "ml", "मिली"), Fraction(1000),
     "ml"),
    (("millilitre", "milliliter", "ml", "मिली"),
     ("litre", "liter", "लीटर", "l"), Fraction(1, 1000), "L"),
]


def _unit_in(t, unit):
    """Unit presence with letter boundaries for ASCII
    units (a bare 'm' or 'to' must not hide inside 'total'
    or 'shaped'); Devanagari units match as substrings."""
    if any("\u0900" <= ch <= "\u097f" for ch in unit):
        return unit in t
    return re.search(r"(?<![a-z])" + re.escape(unit)
                     + r"(?![a-z])", t) is not None


def _unit_convert(q, t):
    # Speed units are native's conversion family — a bare
    # km -> m match inside "40 km/h ko m/s me badlo" would
    # convert the length and drop the rate entirely.
    if re.search(r"km\s*/\s*h|kmph|km\s+per\s+hour|"
                 r"m\s*/\s*s\b", t):
        return None
    nums = _nums(t)
    if len(nums) != 1 or _clocks(t):
        return None
    if not _sig(t, "convert", "में", "mein", "in", "to",
                "बदल", "kaise", "कैसे", "bolenge", "बोलेंगे"):
        return None
    n = Fraction(str(nums[0]))
    for srcs, tgts, factor, unit in _CONVERSIONS:
        src = next((s for s in srcs if _unit_in(t, s)), None)
        tgt = next((s for s in tgts if _unit_in(t, s)), None)
        if src and tgt:
            val = n * factor
            return _res(
                "unit_convert", f"{_fmt(val)} {unit}",
                [f"{_fmt(n)} {src} = {_fmt(val)} {unit}."],
                value=float(val))
    return None


# ----------------------------------------------------------------------
# Decimal story arithmetic (Class 5 queue family): the shape
# is two numbers, one of them decimal; the OPERATION comes
# from the structure (per/each/daily -> multiply, equal
# sharing -> divide, note minus two prices -> change).
# ----------------------------------------------------------------------

def _sig(t, *words):
    """Signal-word match that cannot hide inside a longer
    word: Latin words match on word boundaries ('per' must
    not fire inside 'shopkeeper' or 'percent'), Devanagari
    words match as substrings except प्रति, which must not
    fire inside प्रतिशत."""
    for w in words:
        if w == "प्रति":
            if re.search(r"प्रति(?!शत)", t):
                return True
        elif any("\u0900" <= ch <= "\u097f" for ch in w):
            if w in t:
                return True
        elif re.search(r"\b" + re.escape(w) + r"\b", t):
            return True
    return False


# Wave 224: a genuine currency NOTE as a whole word.  The
# bare substring test "note" in t also fires inside
# "notebook(s)", which made every notebook sum a "note"
# sum.  Devanagari नोट has no word-boundary analogue and
# cannot hide inside another word, so it stays a substring.
_NOTE_WORD = re.compile(r"\bnotes?\b|नोट")

# Wave 224: a count x unit-price structure over two of the
# numbers ("4 notebooks at 30 rupees each", "...for Rs 30
# each", "4 notebooks 30 rupees each"): those two numbers
# are a COUNT and its unit price, never two independent
# prices.
_COUNT_PRICE_SHAPES = [
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"(?:at|@|for)\s*(?:rs\.?|₹|rupees?)?\s*"
               r"(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?|₹)?\s*"
               r"(?:each|per\s+\w+)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s+\S+\s+"
               r"(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?|₹)\s*"
               r"(?:each|per\s+\w+)", re.I),
]


def _count_price_clash(t, nums):
    """True when two of `nums` form a count x unit-price
    pair — the money_change schema must decline those (it
    would read the count as a second price: the Deploy-66
    live serve "Total spent = 30 + 4 = ₹34", change ₹166,
    for 4 notebooks at 30 rupees each from a 200 note)."""
    vals = {Fraction(str(x)) for x in nums}
    for pat in _COUNT_PRICE_SHAPES:
        m = pat.search(t)
        if m and Fraction(m.group(1)) in vals \
                and Fraction(m.group(2)) in vals:
            return True
    return False


def _decimal_story(q, t):
    nums = _nums(t)
    money = _has(t, "rs", "rupee", "रुप", "₹", "note", "price",
                 "kharid", "खरीद", "bought", "buy", "shop",
                 "दुकान")
    # Money change: a NOTE minus two prices, in ANY order
    # (the note may be named last: "...give a 100 rupee
    # note, how much balance will I get back?").  The word
    # "note" is REQUIRED — without it, three money numbers
    # are an add/sub chain (Wave 206's family), not a
    # change sum, and this schema must not guess.
    # Wave 224: the note test is now a genuine whole-word
    # test (_NOTE_WORD — "notebooks" no longer counts), and
    # a count x unit-price pair among the three numbers
    # (_count_price_clash) declines the schema outright:
    # those numbers are a count and its price, and reading
    # the count as a second price is exactly the ₹166
    # misfire.  That shape belongs to the multipart money
    # family; a schema that cannot serve a shape correctly
    # must decline it, never guess.
    if len(nums) == 3 and money and _NOTE_WORD.search(t) \
            and not _count_price_clash(t, nums) and _sig(
            t, "change", "bacha", "बचा", "wapas", "वापस",
            "bachenge", "बचेंगे", "left", "bach", "balance",
            "balnce", "get back", "bak", "bache", "बचे",
            "milega", "मिलेंगे", "receive"):
        vals = sorted((Fraction(str(x)) for x in nums),
                      reverse=True)
        note, a, b = vals[0], vals[1], vals[2]
        if note > a + b or (note == a + b and note >= 100):
            change = note - a - b
            if change >= 0:
                return _res(
                    "money_change", f"₹{_fmt(change)}",
                    [f"Total spent = {_fmt(a)} + {_fmt(b)} = "
                     f"₹{_fmt(a + b)}.",
                     f"Change = ₹{_fmt(note)} - "
                     f"₹{_fmt(a + b)} = ₹{_fmt(change)}."],
                    value=float(change))
    # Percent territory belongs to the percent family /
    # native: a % sign or a percent word means this is NOT
    # a plain decimal story, however the numbers look (a
    # cost price and a selling price are not factors).
    if "%" in t or _sig(t, "percent", "percentage",
                        "प्रतिशत", "pratishat"):
        return None
    # A trailing ask-number ("length of 1 piece?") is not
    # an operand.
    if len(nums) == 3 and nums[-1] == 1 and _sig(
            t, "1 piece", "one piece", "ek hissa", "1 hissa",
            "one part", "1 part"):
        nums = nums[:2]
    if len(nums) != 2:
        return None
    a, b = (Fraction(str(x)) for x in nums)
    divide = _sig(t, "equal", "barabar", "बराबर", "pieces",
                  "हिस्स", "hiss", "boxes", "डिब्ब", "भागों",
                  "tukde", "tukd", "टुकड़े", "parts", "baant",
                  "बाँट", "plate", "plates")
    # Multiplication in this family is a DECIMAL story:
    # a count times a decimal unit price, a decimal rate
    # times days.  The per-unit signal must be a tight
    # phrase — the loose tokens "price"/"rate" made every
    # profit-loss dress a "multiply" (616 x 560).  A
    # count x decimal-price money dress ("5 pen, ek pen
    # 12.50 ka hai") is the same shape with no per-word.
    _tight = _sig(
        t, "each", "प्रति", "daily", "roz", "रोज़", "रोज",
        "per day", "har din", "हर दिन", "every", "evry",
        "per litre", "per liter", "per kg", "per piece",
        "per metre", "per meter", "per item", "per hour",
        "per dozen")
    _count_price = money and (
        (a.denominator == 1) != (b.denominator == 1))
    multiply = (
        a.denominator != 1 or b.denominator != 1) and (
        _tight or _count_price) and not _sig(
        t, "cost price", "selling price", "marked price",
        "profit", "loss", "discount", "क्रय मूल्य",
        "विक्रय मूल्य", "अंकित मूल्य", "लाभ", "हानि",
        "छूट")
    if divide and not multiply:
        big, small = max(a, b), min(a, b)
        if small == int(small) and 2 <= int(small) <= 60 \
                and big > 0:
            if big.denominator == 1 \
                    and big % small != 0:
                # Integer grouping must come out exact.
                return None
            val = big / small
            return _res(
                "decimal_divide", _fmt(val),
                [f"{_fmt(big)} ÷ {int(small)} = {_fmt(val)} "
                 f"(each equal part)."], value=float(val))
    if multiply and not divide:
        val = a * b
        return _res(
            "decimal_multiply", _fmt(val),
            [f"{_fmt(a)} × {_fmt(b)} = {_fmt(val)}."],
            value=float(val))
    return None


# ----------------------------------------------------------------------
# Ratio & proportion: ratio pair + (total | known part) +
# a part ask.  The asked side is resolved by entity tokens;
# a total whose ask names neither side serves the first side
# (the queue's generator convention, row 84).
# ----------------------------------------------------------------------

_ASK_WORDS = ("kitne", "kitna", "how many", "how much", "find",
              "nikaal", "बताओ", "batao", "milega", "मिलेगा",
              "gets", "get", "हैं", "hai", "travel", "chahiye",
              "चाहिए", "कितने", "कितना", "कितनी", "होगी",
              "होगा", "निकालो", "कितनी होगी")


def _side_names_detailed(t, span):
    """Entity names for the two ratio sides AND the spans
    of the exact occurrences the naming pattern matched.
    The spans matter: those two occurrences ARE the ratio
    declaration ("ratio of boys to girls") — they state
    the ratio, they never ask for a side — so _ask_side
    sets them aside and listens to the occurrences that
    remain."""
    m = re.search(r"ratio of\s+([a-z\u0900-\u097F]+)\s+to\s+"
                  r"([a-z\u0900-\u097F]+)", t)
    if m:
        return m.group(1), m.group(2), \
            (m.span(1), m.span(2))
    m = re.search(r"([a-z\u0900-\u097F]+)\s+to\s+"
                  r"([a-z\u0900-\u097F]+)\s+ratio", t)
    if m:
        return m.group(1), m.group(2), \
            (m.span(1), m.span(2))
    m = re.search(r"([a-z\u0900-\u097F]+)\s*:\s*"
                  r"([a-z\u0900-\u097F]+)", t)
    if m and not m.group(1).isdigit() \
            and not m.group(2).isdigit():
        return m.group(1), m.group(2), \
            (m.span(1), m.span(2))
    m = re.search(r"([a-z]+)\s+([a-z])\s+is\s+to\s+"
                  r"([a-z]+)\s+([a-z])\b", t)
    if m:
        return m.group(2), m.group(4), \
            (m.span(2), m.span(4))
    m = re.search(r"\b([a-z])\s+is\s+to\s+([a-z])\b", t)
    if m:
        return m.group(1), m.group(2), \
            (m.span(1), m.span(2))
    m = re.search(r"([a-z\u0900-\u097F]+)\s+(?:and|aur|और|&)\s+"
                  r"([a-z\u0900-\u097F]+)", t[:span[0] + 30])
    if m:
        stop = {"the", "a", "an", "of", "ratio", "in", "is"}
        if m.group(1) not in stop and m.group(2) not in stop \
                and any(ch.isalpha() for ch in m.group(1)) \
                and any(ch.isalpha() for ch in m.group(2)):
            return m.group(1), m.group(2), \
                (m.span(1), m.span(2))
    return None, None, ()


def _side_names(t, span):
    """Best-effort entity names for the two ratio sides,
    from the dress patterns students actually use."""
    n1, n2, _spans = _side_names_detailed(t, span)
    return n1, n2


_FEM_ENDINGS = ("ियों", "ियाँ", "यों", "याँ", "ी")
_MASC_ENDINGS = ("ों", "ो", "े", "ा")


def _name_forms(name):
    """Surface forms a side name can take in the ask.
    Latin names get a plural/singular twin (boys/boy).
    A Devanagari name gets the other endings of its OWN
    gender class, because Hindi changes the ending
    between the statement and the ask (लड़कियों का
    अनुपात ... लड़कियाँ कितनी) — but the gender never
    changes, and लड़के/लड़कियाँ share the stem लड़क, so
    a bare stem would cross the two sides."""
    forms = [name]
    if re.fullmatch(r"[a-z]+", name or ""):
        if len(name) > 3 and name.endswith("s"):
            forms.append(name[:-1])
        elif len(name) > 1:
            forms.append(name + "s")
    elif name and any("\u0900" <= ch <= "\u097F"
                      for ch in name):
        for endings in (_FEM_ENDINGS, _MASC_ENDINGS):
            stem = None
            for suf in endings:
                if name.endswith(suf) \
                        and len(name) - len(suf) >= 3:
                    stem = name[:-len(suf)]
                    break
            if stem is not None:
                forms.extend(stem + e for e in endings)
                break
    return list(dict.fromkeys(forms))


def _name_occurrences(t, name):
    """All (start, end) occurrences of a side name in
    any of its surface forms, on letter boundaries (a
    Devanagari matra is not a regex word char, so
    lookarounds, not \\b)."""
    if not name:
        return []
    occ = set()
    for form in _name_forms(name):
        for m in re.finditer(
                r"(?<![a-z\u0900-\u097F])"
                + re.escape(form)
                + r"(?![a-z\u0900-\u097F])", t):
            occ.add((m.start(), m.end()))
    return sorted(occ)


_UNIT_FILLER = {"cup", "cups", "kg", "g", "gram", "grams",
           "litre", "litres", "liter", "liters", "ml",
           "rs", "rupee", "rupees", "metre", "metres",
           "meter", "meters", "cm", "mm", "km", "of",
           "item", "items", "piece", "pieces",
           "कप", "लीटर", "किलो", "ग्राम", "रुपया",
           "रुपये", "का", "की", "के"}


def _tied_to_number(t, num_span, occ):
    """A name occurrence glued to a stated number ("12
    cups of water", "पानी 12 कप है") names the side whose
    count is GIVEN — the known side, not the asked one.
    Only unit/of filler may intervene: if the gap holds
    a sentence break or any real word, the name belongs
    to the next clause's ask, not to this number."""
    if occ[0] >= num_span[1]:
        between = t[num_span[1]:occ[0]]
        limit = 18
    elif occ[1] <= num_span[0]:
        between = t[occ[1]:num_span[0]]
        limit = 10
    else:
        return True
    if len(between) > limit or any(
            ch.isdigit() or ch in ".?!"
            for ch in between):
        return False
    toks = [w for w in re.split(r"[\s,]+", between) if w]
    return all(w in _UNIT_FILLER for w in toks)


_ASK_RE = (r"(kitne|kitna|kitni|kitno|कितने|कितना|कितनी|"
           r"how many|how much|how far|find|nikaal|"
           r"बताओ|batao)")


def _ask_side(t, n1, n2, span=None, third=None):
    """Which ratio side is being ASKED for, resolved by
    meaning: set aside the two occurrences that form the
    ratio DECLARATION and any occurrence glued to the
    GIVEN number (that side is known, not asked); of the
    occurrences that remain, the asked side is the name
    sitting CLOSEST to an ask word (kitne / how many /
    find), on either side of it.  The old serve scanned a
    fixed window and let the LAST name checked win, so a
    declaration inside the window ("...ratio of boys to
    girls 3:2, how many girls?") always answered for the
    FIRST side — boys — even when girls were asked."""
    if not n1 and not n2:
        return None
    decl = ()
    if span is not None:
        _n1, _n2, decl = _side_names_detailed(t, span)
    occ = {1: _name_occurrences(t, n1),
           2: _name_occurrences(t, n2)}
    for side in (1, 2):
        occ[side] = [o for o in occ[side]
                     if not any(o[0] < d[1] and d[0] < o[1]
                                for d in decl)]
    if third is not None:
        for m in re.finditer(r"\d+(?:\.\d+)?", t):
            if span is not None and span[0] <= m.start() \
                    and m.end() <= span[1]:
                continue
            try:
                if Fraction(m.group()) != third:
                    continue
            except Exception:
                continue
            for side in (1, 2):
                occ[side] = [o for o in occ[side]
                             if not _tied_to_number(
                                 t, (m.start(), m.end()), o)]
    best = None
    for m in re.finditer(_ASK_RE, t):
        cand = []
        for side in (1, 2):
            for o in occ[side]:
                if o[1] < m.start() - 25 \
                        or o[0] > m.end() + 35:
                    continue
                d = max(m.start() - o[1], o[0] - m.end(), 0)
                cand.append((d, side))
        if cand:
            cand.sort()
            best = cand[0][1]
    return best



_COLLECTIVES = ("students", "people", "persons", "members",
                "children", "pupils", "residents",
                "passengers", "villagers", "employees",
                "छात्र", "छात्रा", "छात्रों", "विद्यार्थी",
                "लोग", "बच्चे", "बच्चों", "सदस्य", "व्यक्ति")


def _third_is_total(t, span, third, n1, n2):
    """The third number names the WHOLE the two sides add
    up to when it carries a collective noun ("30 students
    in the class") or sits in a there-are frame whose next
    word is not one side's own name ("there are 30
    students" — but not "there are 18 girls", where 18 is
    the girls' own known part)."""
    for m in re.finditer(r"\d+(?:\.\d+)?", t):
        if span[0] <= m.start() and m.end() <= span[1]:
            continue
        try:
            if Fraction(m.group()) != third:
                continue
        except Exception:
            continue
        after = t[m.end():m.end() + 24].strip()
        hit = re.match(r"([a-z\u0900-\u097F]+)", after)
        nxt = hit.group(1) if hit else ""
        if nxt and nxt in (n1, n2):
            continue
        if nxt in _COLLECTIVES:
            return True
        before = t[max(0, m.start() - 14):m.start()]
        if re.search(r"(there are|there is)\s*$", before):
            return True
    return False


def _ratio_part(q, t):
    r = _ratio(t)
    if not r:
        return None
    a, b, span = r
    if not _has(t, "ratio", "anupaat", "अनुपात") \
            and ":" not in t and "is to" not in t:
        return None
    # A ratio with THREE or more parts (8:8:8) is not this
    # two-side schema's question — the named-shares solver
    # owns it; serving its first pair here mis-serves it.
    if re.match(r"\s*:\s*\d", t[span[1]:]):
        return None
    rest = _nums(t[:span[0]] + " " + t[span[1]:])
    fa, fb = Fraction(str(a)), Fraction(str(b))
    others = [n for n in rest
              if Fraction(str(n)) not in (fa, fb)]
    if len(others) != 1:
        return None
    third = Fraction(str(others[0]))
    if not any(w in t for w in _ASK_WORDS):
        return None
    n1, n2 = _side_names(t, span)
    ask_side = _ask_side(t, n1, n2, span=span, third=third)
    total_words = _has(t, "total", "कुल", "kul", "altogether",
                       "mila kar", "मिलाकर") \
        or _third_is_total(t, span, third, n1, n2)
    if total_words:
        part1 = third * fa / (fa + fb)
        part2 = third * fb / (fa + fb)
        if part1.denominator == 1 and part2.denominator == 1:
            if ask_side is None and _has(
                    t, "each", "both", "दोनों", "dono",
                    "प्रत्येक", "har ek"):
                # An EACH ask wants BOTH parts — the older
                # ratio-split serve answers both, with
                # units; serving only the first part here
                # would answer half the question.
                return None
            val = part2 if ask_side == 2 else part1
            side = n2 if ask_side == 2 else n1
            label = f" for {side}" if side else ""
            return _res(
                "ratio_part", _fmt(val),
                [f"Ratio parts: {_fmt(fa)} + {_fmt(fb)} = "
                 f"{_fmt(fa + fb)} parts.",
                 f"Total = {_fmt(third)}, so 1 part = "
                 f"{_fmt(third / (fa + fb))}.",
                 f"Required part{label} = {_fmt(val)}."],
                value=float(val))
    # Known part -> other part (direct proportion).
    if ask_side == 1:
        val = third * fa / fb
        known = fb
    elif ask_side == 2:
        val = third * fb / fa
        known = fa
    else:
        return None
    if val.denominator not in (1, 2, 4, 5, 10, 20, 25):
        return None
    return _res(
        "ratio_proportion", _fmt(val),
        [f"Ratio {_fmt(fa)} : {_fmt(fb)} stays the same.",
         f"Other part = {_fmt(third)} × {_fmt(val / third)}"
         f" = {_fmt(val)} (proportion with the "
         f"{_fmt(known)} side)."], value=float(val))


# ----------------------------------------------------------------------
# Percentage family: CP/SP percent, simple interest (incl.
# terse dress), reverse CP, discount.  Numbers are assigned
# to roles by their neighbouring role words; every answer is
# verified by recomputing the forward relation.
# ----------------------------------------------------------------------

def _near_num(t, words, nums_with_pos):
    for pos, val in nums_with_pos:
        window = t[max(0, pos - 26):pos + 26]
        if any(w in window for w in words):
            return val
    return None


def _nums_pos(t):
    masked = _mask_clocks(t)
    return [(m.start(), float(m.group()))
            for m in re.finditer(r"\d+(?:\.\d+)?", masked)]


def _near_num_closest(t, words, nums_with_pos):
    """The number CLOSEST to any of the role words — a
    window match mis-assigns roles when a far number's
    window happens to contain the word (row 91: '8000 ...
    per year ... in 4 years' made 8000 the 'years')."""
    best = None
    for pos, val in nums_with_pos:
        for w in words:
            start = 0
            while True:
                idx = t.find(w, start)
                if idx < 0:
                    break
                dist = abs(idx - pos)
                if best is None or dist < best[0]:
                    best = (dist, val)
                start = idx + 1
    return best[1] if best else None


def _percent_family(q, t):
    if "%" not in t and "percent" not in t \
            and "प्रतिशत" not in t:
        return None
    # Formal English role dresses ("marked price of Rs 800",
    # "cost price ... selling price", "successive
    # discounts", "find her profit percent") are NATIVE's
    # regression-tested territory — this family exists for
    # the Hinglish/Hindi/terse dresses native missed (the
    # queue rows).  A formal dress with no Hinglish/Hindi
    # marker declines, however well it seems to fit.
    _formal = _has(t, "marked price", "cost price",
                   "selling price", "list price",
                   "discount rate", "successive",
                   "profit percent", "loss percent")
    _hinglish = any("ऀ" <= ch <= "ॿ" for ch in t) or _sig(
        t, "ne", "me", "mein", "ki", "ka", "ke", "hua",
        "hui", "bata", "bhai", "bech", "bechi", "becha",
        "kharid", "kharidi", "jisme", "apni", "apna",
        "diya", "gaya", "wala", "wali", "kitna", "kitne",
        "usne", "iska", "uska", "chhoot", "bhejo")
    if _formal and not _hinglish:
        return None
    npos = _nums_pos(t)
    if len(npos) < 2:
        return None
    # The percent VALUE is a number glued to its % sign —
    # never the number that merely sits near the ask word
    # "प्रतिशत" (row 86's trap: 680 was nearest to it).
    pm = re.search(r"(\d+(?:\.\d+)?)\s*(?:%|percent|प्रतिशत)",
                   t)
    pct = float(pm.group(1)) if pm else None
    # Simple interest: P, R%, T years + an interest signal.
    years = _near_num_closest(
        t, ("year", "years", "sal", "साल", "varsh", "वर्ष",
            "yrs"), npos)
    principal = _near_num(
        t, ("principal", "mooldhan", "मूलधन", "par", "on rs",
            "on ₹", "of rs"), npos)
    if principal is None:
        cands = [v for _, v in npos
                 if v not in (pct, years)]
        principal = max(cands) if cands else None
    if pct is not None and years is not None \
            and principal is not None \
            and len({pct, years, principal}) == 3 \
            and _has(t, "interest", "byaj", "ब्याज", "si",
                     "simple") \
            and not _has(t, "compound", "चक्रवृद्धि") \
            and not (_has(t, "simple interest")
                     and _has(t, "per annum")) \
            and not (_has(t, "साधारण ब्याज")
                     and _has(t, "वर्ष", "ज्ञात")):
        si = Fraction(str(principal)) * Fraction(str(pct)) \
            * Fraction(str(years)) / 100
        check = float(si) * 100 / (
            float(principal) * float(pct) * float(years))
        if abs(check - 1) > 1e-9:
            return None
        return _res(
            "simple_interest", f"Rs {_fmt(si)}",
            [f"SI = P × R × T ÷ 100 = "
             f"{_fmt(Fraction(str(principal)))} × "
             f"{_fmt(Fraction(str(pct)))} × "
             f"{_fmt(Fraction(str(years)))} ÷ 100.",
             f"Simple interest = ₹{_fmt(si)}."],
            value=float(si))
    cp = _near_num(t, ("cost", "cp", "क्रय", "kharid", "खरीद",
                       "bought for", "laagat", "लागत"), npos)
    sp = _near_num(t, ("selling", "sp", "बेचा", "बेच",
                       "becha", "bech", "sold", "बिक्री"), npos)
    # Two money numbers in story order (bought first, sold
    # later), a profit/loss percent ask and a sell word:
    # extra non-price numbers (a "2 years" in row 87) are
    # ignored by taking the two LARGEST values and ordering
    # them by position.
    if (cp is None or sp is None) and pct is None \
            and len(npos) >= 2 \
            and _has(t, "profit", "loss", "लाभ", "हानि",
                     "munafa", "fayda", "फायदा", "nuksan") \
            and _has(t, "sold", "bech", "बेच", "sell"):
        top = sorted(npos, key=lambda pv: -pv[1])[:2]
        top.sort()
        cp, sp = top[0][1], top[1][1]
    if cp is not None and sp is not None and cp != sp \
            and pct is None:
        diff = Fraction(str(sp)) - Fraction(str(cp))
        pctv = abs(diff) * 100 / Fraction(str(cp))
        kind = "Profit" if diff > 0 else "Loss"
        if pctv.denominator not in (1, 2, 4, 5, 10, 20, 25,
                                    50, 100):
            return None
        return _res(
            "profit_loss_percent", f"{_fmt(pctv)}%",
            [f"{kind} = |{_fmt(Fraction(str(sp)))} - "
             f"{_fmt(Fraction(str(cp)))}| = "
             f"₹{_fmt(abs(diff))}.",
             f"{kind}% = {_fmt(abs(diff))} ÷ "
             f"{_fmt(Fraction(str(cp)))} × 100 = "
             f"{_fmt(pctv)}%."], value=float(pctv))
    if pct is not None and sp is not None and cp is None \
            and _has(t, "cp", "cost price", "क्रय मूल्य",
                     "kharid mulya", "original price"):
        p = Fraction(str(pct))
        if _has(t, "profit", "लाभ", "labh", "munafa"):
            cpv = Fraction(str(sp)) * 100 / (100 + p)
            kind = "profit"
        elif _has(t, "loss", "हानि", "nuksan", "नुकसान"):
            if p >= 100:
                return None
            cpv = Fraction(str(sp)) * 100 / (100 - p)
            kind = "loss"
        else:
            return None
        if cpv.denominator not in (1, 2, 4, 5, 10, 20, 25,
                                   50, 100):
            return None
        return _res(
            "reverse_cp", f"Rs {_fmt(cpv)}",
            [f"SP = ₹{_fmt(Fraction(str(sp)))} at "
             f"{_fmt(p)}% {kind}.",
             f"CP = SP × 100 ÷ "
             f"{100 + p if kind == 'profit' else 100 - p} = "
             f"₹{_fmt(cpv)}."], value=float(cpv))
    mp = _near_num(t, ("marked", "list price", "mp",
                       "अंकित", "ankit"), npos)
    # NO largest-number fallback for the marked price:
    # "800 rs wali cheez par 25% chhoot" is native's dress —
    # guessing its price as an MP shadowed it.  Discount
    # fires only on a role-marked price (row 91's dress).
    if pct is not None and mp is not None \
            and _has(t, "discount", "छूट", "chhoot", "chut"):
        d = Fraction(str(pct))
        spv = Fraction(str(mp)) * (100 - d) / 100
        return _res(
            "discount_sp", f"Rs {_fmt(spv)}",
            [f"Discount = {_fmt(d)}% of "
             f"₹{_fmt(Fraction(str(mp)))} = "
             f"₹{_fmt(Fraction(str(mp)) * d / 100)}.",
             f"Selling price = ₹{_fmt(Fraction(str(mp)))} - "
             f"₹{_fmt(Fraction(str(mp)) * d / 100)} = "
             f"₹{_fmt(spv)}."], value=float(spv))
    return None


# ----------------------------------------------------------------------
# Arithmetic progressions: series shapes + story dresses +
# inverse asks.  Every candidate is regenerated and checked
# against the question's own numbers before serving.
# ----------------------------------------------------------------------

def _ap_series(t):
    m = re.search(
        r"(-?\d+(?:\.\d+)?)\s*[, ]\s*(-?\d+(?:\.\d+)?)"
        r"\s*[, ]\s*(-?\d+(?:\.\d+)?)"
        r"(?:\s*[, ]\s*(-?\d+(?:\.\d+)?))?", t)
    if not m:
        return None
    vals = [Fraction(g) for g in m.groups() if g is not None]
    diffs = {vals[i + 1] - vals[i] for i in range(len(vals) - 1)}
    if len(diffs) == 1 and diffs.pop() != 0:
        return vals
    return None


def _ap_family(q, t):
    # A penalty schedule is Wave 195's own AP family
    # (daily penalty with a fixed increment) — its total
    # is computed there, not by the plain story-sum.
    if _has(t, "penalty", "jurmana", "जुर्माना"):
        return None
    series = _ap_series(t)
    nums = _nums(t)
    # Given one term + first term -> sum of first N terms.
    m = re.search(r"(\d+)(?:th|st|nd|rd|वें|वा|वां)\s+term"
                  r"\b[^0-9\-]{0,24}?(-?\d+(?:\.\d+)?)", t)
    msum = re.search(r"sum\s+of\s+(?:its\s+|the\s+)?"
                     r"(?:first\s+)?(\d+)", t) \
        or re.search(r"(\d+)\s*(?:terms|पदों)\s*(?:का\s*)?"
                     r"(?:sum|योग)", t)
    first_m = re.search(
        r"first term\s*(?:is|=|है)?\s*(-?\d+(?:\.\d+)?)", t)
    if m and msum and first_m:
        k = int(m.group(1))
        ak = Fraction(m.group(2))
        a = Fraction(first_m.group(1))
        n = int(msum.group(1))
        if k > 1 and n > 0:
            d = (ak - a) / (k - 1)
            s = Fraction(n, 2) * (2 * a + (n - 1) * d)
            if s.denominator == 1:
                return _res(
                    "ap_given_term_sum", _fmt(s),
                    [f"d = (a{k} - a1) ÷ ({k} - 1) = "
                     f"({_fmt(ak)} - {_fmt(a)}) ÷ {k - 1} = "
                     f"{_fmt(d)}.",
                     f"S{n} = {n}/2 × (2 × {_fmt(a)} + "
                     f"{n - 1} × {_fmt(d)}) = {_fmt(s)}."],
                    value=float(s))
    if series:
        a, d = series[0], series[1] - series[0]
        extra = [Fraction(str(n)) for n in nums
                 if Fraction(str(n)) not in series]
        # Inverse nth term: which term equals the target?
        if _has(t, "which term", "kaun sa pad", "कौन सा पद",
                "कौन सा अंक", "which number") and extra:
            target = extra[-1]
            n = (target - a) / d + 1
            if n.denominator == 1 and int(n) > len(series):
                return _res(
                    "ap_inverse_nth", f"{int(n)}th term",
                    [f"a = {_fmt(a)}, d = {_fmt(d)}.",
                     f"n = ({_fmt(target)} - {_fmt(a)}) ÷ "
                     f"{_fmt(d)} + 1 = {int(n)}.",
                     f"So {_fmt(target)} is the {int(n)}th "
                     f"term."], value=float(n))
        # Inverse sum: how many terms give sum S?  (Checked
        # BEFORE the plain sum: its target number would
        # otherwise be mistaken for a term count.)  The
        # unknown-count signal is structural — "first n
        # terms ... is 200", "find n", "n ज्ञात कीजिए" —
        # not one fixed phrasing (Wave 212 battery).
        _unknown_n = _has(
            t, "how many terms", "kitne pad", "कितने पद",
            "kitne term", "कितने term", "number of terms",
            "find n", "n find", "value of n", "first n",
            "n terms", "पहले n", "n ज्ञात", "ज्ञात कीजिए")
        if _unknown_n and extra:
            target = extra[-1]
            disc = (2 * a - d) ** 2 + 8 * d * target
            root = sp.sqrt(sp.nsimplify(disc))
            if root.is_integer:
                for cand in ((- (2 * a - d) + int(root)),
                             (- (2 * a - d) - int(root))):
                    if cand > 0 and (2 * d) != 0 \
                            and cand % (2 * d) == 0:
                        n = cand // (2 * d)
                        s = Fraction(int(n), 2) * (
                            2 * a + (int(n) - 1) * d)
                        if s == target and int(n) > 0:
                            return _res(
                                "ap_inverse_sum",
                                f"{int(n)} terms",
                                [f"S_n = n/2 (2a + (n-1)d) "
                                 f"with a = {_fmt(a)}, "
                                 f"d = {_fmt(d)}.",
                                 f"Solving S_n = "
                                 f"{_fmt(target)} gives "
                                 f"n = {int(n)}."],
                                value=float(n),
                                full_op="ap_terms_for_sum")
        # Sum of the first N terms (N given, story dress).
        # NEVER when the count itself is the unknown: an
        # unknown-n ask the inverse branch could not
        # settle declines honestly instead of summing to
        # the target (the battery's 80000 wrong serve).
        counts = [int(n) for n in extra
                  if n == int(n) and 2 <= int(n) <= 500]
        if counts and not _unknown_n and _has(
                t, "total", "sum", "कुल", "योग",
                "jama", "जमा", "sabhi", "सभी",
                "weeks", "sundays", "days", "हफ़्ते",
                "सप्ताह"):
            n = counts[-1]
            s = Fraction(n, 2) * (2 * a + (n - 1) * d)
            if s.denominator == 1:
                # Explicit-series AP sum: serve under the
                # sequences contract (type/op) the older
                # solver uses, so the methods layer still
                # offers the Gauss pairing alternate.
                return _res(
                    "ap_sum", _fmt(s),
                    [f"AP: a = {_fmt(a)}, d = {_fmt(d)}, "
                     f"n = {n}.",
                     f"S{n} = {n}/2 × (2 × {_fmt(a)} + "
                     f"{n - 1} × {_fmt(d)}) = {_fmt(s)}."],
                    value=float(s), full_op="ap_sum",
                    full_type="sequences")
    # Story branches.  Two number readings are tried: the
    # raw list (row 100's dress, where "दिन 5" IS the day-1
    # value) and a marker-stripped list (row 101's dress,
    # where "week 1" is an enumeration marker in front of
    # the value 50).  Whichever reading satisfies a schema's
    # gates first, wins.
    t2 = re.sub(r"(week|day|दिन|सप्ताह|हफ़्त\w*)\s*\d+\b",
                " ", t)
    cand_lists = [nums]
    stripped = _nums(t2)
    if stripped != nums:
        cand_lists.append(stripped)
    mo = re.search(r"(\d+)\s*(?:th|st|nd|rd|वें|वा|वां|"
                   r"ve|we)(?![a-z0-9])", t)
    for cand in cand_lists:
        # Story nth term: first-day value, daily increment,
        # and an ordinal day/week ask (15th day / 15वें दिन).
        if mo and len(cand) == 3 and _has(
                t, "day", "दिन", "week", "सप्ताह", "हफ़्त",
                "roz", "रोज़"):
            n_ord = int(mo.group(1))
            vals = [Fraction(str(x)) for x in cand]
            others = [v for v in vals if v != n_ord]
            if len(others) == 2 and 2 <= n_ord <= 366:
                a1, inc = others[0], others[1]
                val = a1 + (n_ord - 1) * inc
                if val > 0:
                    return _res(
                        "ap_story_nth", _fmt(val),
                        [f"Day 1 = {_fmt(a1)}, daily increase "
                         f"= {_fmt(inc)}.",
                         f"Day {n_ord} = {_fmt(a1)} + "
                         f"{n_ord - 1} × {_fmt(inc)} = "
                         f"{_fmt(val)}."], value=float(val))
        # Story sum, series-in-story dress: three leading
        # values in AP + a count (10 Sundays / 12 weeks).
        if len(cand) == 4 and _has(
                t, "total", "कुल", "jama", "जमा", "योग"):
            v = [Fraction(str(x)) for x in cand]
            if v[1] - v[0] == v[2] - v[1] != 0 \
                    and v[3] == int(v[3]) \
                    and 2 <= int(v[3]) <= 366:
                s = v[3] / 2 * (2 * v[0] + (v[3] - 1)
                                * (v[1] - v[0]))
                if s.denominator == 1:
                    return _res(
                        "ap_story_sum", _fmt(s),
                        [f"AP: a = {_fmt(v[0])}, d = "
                         f"{_fmt(v[1] - v[0])}, "
                         f"n = {int(v[3])}.",
                         f"Total = {int(v[3])}/2 × (2 × "
                         f"{_fmt(v[0])} + {int(v[3]) - 1} × "
                         f"{_fmt(v[1] - v[0])}) = "
                         f"{_fmt(s)}."], value=float(s))
        # Story sum: start value, increment, N days/weeks.
        if len(cand) == 3 and _has(
                t, "week", "सप्ताह", "हफ़्त", "day", "दिन") \
                and _has(t, "total", "कुल", "jama", "जमा",
                         "sab", "सब"):
            a1, inc, n = (Fraction(str(x)) for x in cand)
            if n == int(n) and 2 <= int(n) <= 366 \
                    and inc != 0:
                s = n / 2 * (2 * a1 + (n - 1) * inc)
                s_alt = n / 2 * (2 * a1 + (inc - 1) * n)
                if s.denominator == 1 and s != s_alt:
                    return _res(
                        "ap_story_sum", _fmt(s),
                        [f"AP: a = {_fmt(a1)}, d = "
                         f"{_fmt(inc)}, n = {int(n)}.",
                         f"Total = {int(n)}/2 × (2 × "
                         f"{_fmt(a1)} + {int(n) - 1} × "
                         f"{_fmt(inc)}) = {_fmt(s)}."],
                        value=float(s))
    # Story sum, loose dress (row 105): an AP triple as a
    # SUBSEQUENCE of the numbers (an increment mention like
    # "2-2 badhata gaya" sits between the terms and the
    # count) + a count glued to a time word.
    if _has(t, "total", "कुल", "jama", "जमा", "mile",
            "मिले") and len(nums) >= 5:
        fr = [Fraction(str(x)) for x in nums]
        cm = re.search(r"(\d+)\s*(?:sundays|sunday|weeks|"
                       r"week|days|day|रविवार|सप्ताह|दिन)", t)
        if cm:
            count = Fraction(cm.group(1))
            rest = [v for v in fr if v != count]
            for i in range(len(rest) - 2):
                a, b, c = rest[i], rest[i + 1], rest[i + 2]
                if b - a == c - b != 0:
                    s = count / 2 * (2 * a + (count - 1)
                                      * (b - a))
                    if s.denominator == 1 and count >= 2:
                        return _res(
                            "ap_story_sum", _fmt(s),
                            [f"AP: a = {_fmt(a)}, d = "
                             f"{_fmt(b - a)}, "
                             f"n = {int(count)}.",
                             f"Total = {int(count)}/2 × "
                             f"(2 × {_fmt(a)} + "
                             f"{int(count) - 1} × "
                             f"{_fmt(b - a)}) = {_fmt(s)}."],
                            value=float(s))
                    break
    return None


# ----------------------------------------------------------------------
# Complex numbers in verbal dress: i-powers, modulus with
# "i root b", conjugate, real/imaginary part of a sum, the
# argument of a standard value, roots of negative numbers.
# Every value is recomputed with sympy before serving.
# ----------------------------------------------------------------------

_CX_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*([+-])\s*(\d+(?:\.\d+)?)?\s*i"
    r"(?:\s*(?:root|√)\s*(\d+(?:\.\d+)?))?")


def _cx_parse(m):
    re_part = sp.nsimplify(m.group(1))
    sign = 1 if m.group(2) == "+" else -1
    if m.group(4) is not None:
        im = sign * sp.sqrt(sp.nsimplify(m.group(4)))
    elif m.group(3) is not None:
        im = sign * sp.nsimplify(m.group(3))
    else:
        im = sign
    return re_part + im * sp.I


def _cx_str(z):
    # Complex display: the unit is a lowercase i joined by
    # the middle dot ("3 + 2·i", "-i", "9·i"). Wave 231
    # SUPERSESSION: this family used a capital I (matching
    # the old fmt pass-through of SymPy's spelling); the
    # external audit ruled I must reach a student as i, and
    # fmt now renders i everywhere else, so the family
    # dialect is unified on i.
    z = sp.expand(z)
    re_part, im_part = z.as_real_imag()
    if im_part == 0:
        return str(re_part)
    if re_part == 0:
        if im_part == 1:
            return "i"
        if im_part == -1:
            return "-i"
        return f"{im_part}·i".replace("sqrt", "√")
    sign = "+" if im_part > 0 else "-"
    mag = abs(im_part)
    mag_s = "" if mag == 1 else str(mag).replace(
        "sqrt", "√").replace("*", "") + "·"
    return f"{re_part} {sign} {mag_s}i"


_I_POWER_REST = {
    "value", "what", "kitna", "kitni", "kitne", "kya",
    "है", "होगा", "hoga", "होगी", "equals", "equal", "मान",
    "maan", "find", "calculate", "evaluate", "होती", "hoti",
    "होता", "hota", "दीजिए", "dijiye", "power", "घात",
    "ghat", "पावर", "i", "iska", "ans", "answer", "batao",
    "बताओ", "solve", "of", "the", "do", "ko", "ka", "ki",
    "ke", "liye", "karo", "करो", "to", "hai", "hain",
    "please", "question", "find", "out", "kar", "par",
    "aur", "or", "is", "it", "this", "nikalo", "chahiye",
    "चाहिए", "क्या"}


def _i_power_leftover_ok(t, m):
    """Leftover discipline for the caret form (i^N): once
    the token itself is removed, only ask/filler words may
    remain.  The router's clean_text turns a garbled "i2"
    inside long OCR prose into "i^2" — without this gate
    that prose was served an i-power answer."""
    rest = t[:m.start()] + " " + t[m.end():]
    words = re.findall(r"[a-z\u0900-\u097F]+", rest)
    return len(words) <= 10 and all(
        w in _I_POWER_REST for w in words)


def _complex_family(q, t):
    # i ki power N / i^N / i की पावर N.
    m = re.search(r"i\s*(?:ki\s*(?:power|ghat|घात|पावर)|"
                  r"की\s*पावर)\s*(\d+)", t)
    if not m:
        caret = re.search(r"i\s*\^\s*(\d+)", t)
        if caret is not None and _i_power_leftover_ok(
                t, caret):
            m = caret
    if m:
        n = int(m.group(1))
        val = [1, sp.I, -1, -sp.I][n % 4]
        return _res(
            "i_power", _cx_str(val),
            [f"i powers repeat every 4: i, -1, -i, 1.",
             f"{n} mod 4 = {n % 4}, so i^{n} = "
             f"{_cx_str(val)}."], value=None)
    # Roots of negative numbers: root -a + root -b.
    roots = re.findall(
        r"(?:root|√|sqrt)\s*(?:ke andar\s*)?(?:minus|-|−)\s*"
        r"(\d+(?:\.\d+)?)", t)
    if len(roots) == 1 and ("=" in t or not _has(
            t, "find", "value", "evaluate", "simplify",
            "what", "answer", "total", "sum", "कितना",
            "kitna", "कितनी", "मान", "ज्ञात", "होगा",
            "hoga", "क्या", "kya", "बताओ", "batao",
            "जोड़", "jod")):
        # A lone root inside an equation question is the
        # DEFINITION of i ("i = √−1") within a larger ask
        # (a quadratic's complex root) — not a roots-of-
        # negatives question at all.
        roots = []
    if roots and len(roots) <= 3:
        total = sum(sp.sqrt(sp.nsimplify(r)) for r in roots)
        z = total * sp.I
        parts = " + ".join(f"{_surd(int(float(r)))}i"
                            for r in roots)
        return _res(
            "sqrt_negative", _cx_str(z),
            [f"√(-{r}) = {_surd(int(float(r)))}i"
             for r in roots] +
            [f"Sum = {parts} = {_cx_str(z)}."], value=None)
    m = _CX_RE.search(t)
    # Principal argument of a standard value.  An explicit
    # a + bi literal is the native complex solver's dress
    # (its answer format — "pi/4 rad ≈ 0.7854" — is the
    # standing contract), so this branch serves only the
    # bare-i verbal dress native cannot parse.
    if m is None and _has(t, "argument", "कोणांक",
                          "konank"):
        target = None
        if re.search(r"(?<![a-z])i(?![a-z])", t):
            target = sp.I
        if target is not None:
            ang = sp.arg(target)
            if ang is not None:
                return _res(
                    "argument",
                    str(ang).replace("pi", "π"),
                    [f"Principal argument of "
                     f"{_cx_str(target)} = "
                     f"{str(ang).replace('pi', 'π')}."], value=None)
    if not m:
        return None
    z1 = _cx_parse(m)
    if _has(t, "conjugate", "संयुग्मी", "sanyugmi"):
        zc = sp.conjugate(z1)
        return _res(
            "conjugate", _cx_str(zc),
            [f"Conjugate of {_cx_str(z1)} flips the sign "
             f"of the imaginary part.",
             f"Conjugate = {_cx_str(zc)}."], value=None)
    if _has(t, "modulus", "मापांक", "mapank",
            "absolute value") or re.search(
            r"\bmod\w*", t):
        # (The bare "|z|" notation is NOT a trigger: that
        # dress is deliberately the fallback's job — the
        # native router declines it and Wave 187 pins the
        # decline.  This branch owns the modulus-WORD
        # dresses, e.g. "z = 1 + i root 3 ka modulus kya
        # hoga?".)
        mod = sp.Abs(z1)
        # Native's modulus format: an integer when the
        # square is perfect, else "sqrt(n) ≈ x.4dp".
        re_part, im_part = z1.as_real_imag()
        n2 = int(re_part ** 2 + im_part ** 2)
        root = int(sp.sqrt(n2))
        if root * root == n2:
            mod_str = str(root)
        else:
            mod_str = f"sqrt({n2}) ≈ {float(mod):.4f}"
        return _res(
            "modulus", mod_str,
            [f"|z| = √(a² + b²) for z = {_cx_str(z1)}.",
             f"|z| = {str(mod).replace('sqrt', '√')}"],
            value=float(mod))
    # Real / imaginary part of a sum or difference of two.
    m2 = _CX_RE.search(t, m.end())
    if m2 and _has(t, "real part", "वास्तविक भाग",
                   "imaginary part", "काल्पनिक भाग",
                   "kaalpanik"):
        z2 = _cx_parse(m2)
        between = t[m.end():m2.start()]
        if _has(between, "minus", "subtract", "घटा", "-"):
            z = z1 - z2
            op_word = "difference"
        else:
            z = z1 + z2
            op_word = "sum"
        re_part, im_part = sp.expand(z).as_real_imag()
        if _has(t, "real part", "वास्तविक भाग"):
            return _res(
                "complex_real_part", str(re_part),
                [f"{op_word.capitalize()}: {_cx_str(z1)} and "
                 f"{_cx_str(z2)} give {_cx_str(z)}.",
                 f"Real part = {re_part}."], value=None)
        return _res(
            "complex_imag_part", str(im_part),
            [f"{op_word.capitalize()}: {_cx_str(z1)} and "
             f"{_cx_str(z2)} give {_cx_str(z)}.",
             f"Imaginary part = {im_part}."], value=None)
    return None


# ----------------------------------------------------------------------
# Factorisation the caret-free dresses hid: grouping
# (xy + 3x + y + 3), a bare difference of squares, and a
# polynomial divided by a monomial.  The polynomial must be
# a contiguous expression; whatever remains after removing
# it and the ask words must be filler only.  sympy factors
# and the expansion is checked back before serving.
# ----------------------------------------------------------------------

_FILLER = {
    "factorise", "factorize", "factor", "factors",
    "factrise", "factoriz",
    "गुणनखंड", "karke", "dikhana", "dikhao", "iska", "ans",
    "answer", "batao", "बताओ", "solve", "of", "the", "do",
    "ko", "ka", "ki", "me", "hai", "hain", "please",
    "question", "करके", "दिखाना", "इसका", "find", "out",
    "kar", "ke", "liye", "divide", "भाग", "दो", "by",
    "karo", "करो", "to", "par", "aur", "or", "kya", "क्या",
    "nikalo", "chahiye", "चाहिए", "is", "it", "this",
}

_EXPR_RE = re.compile(
    r"[a-z0-9\s\+\-\*/\^\(\)]+")
_TERM_RE = re.compile(
    r"(?:\d*[a-z]+(?:\^\d+)?|\d+)(?:\s*[\+\-]\s*"
    r"(?:\d*[a-z]+(?:\^\d+)?|\d+))+")

_MATHS_LEFTOVER_VETO = {
    "total", "sum", "ratio", "area", "price", "cost",
    "rs", "rupees", "profit", "loss", "distance", "speed",
    "कुल", "योग", "क्षेत्रफल", "दूरी", "कीमत",
}

# Operation-command words: when one of these is the ask, a
# bare polynomial in the text belongs to THAT operation —
# never to factorisation, whatever the ask words say.
_OP_COMMAND_VETO = {
    "derivative", "derivatives", "differentiate",
    "differentiating", "differentiation", "integral",
    "integrals", "integrate", "integrating", "integration",
    "simplify", "simplifying", "simplification", "evaluate",
    "evaluating", "evaluation", "expand", "expanding",
    "expansion", "limit", "limits", "solve", "solving",
    "prove", "proving", "graph", "plot", "draw", "sketch",
    "degree", "coefficient",
    "अवकलन", "समाकलन", "सरल",
}


def _poly_from(t):
    """(sympy expr, span) for a contiguous polynomial with
    at least two terms and a letter, or (None, None).  The
    LONGEST segment wins.  Leftover discipline: with a
    factor ask in the message the segment IS the question,
    however chatty the dress; without one (a bare
    expression), at most 5 innocent leftover words and no
    maths keyword among them."""
    from sympy.parsing.sympy_parser import (
        parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor)
    transforms = standard_transformations + (
        implicit_multiplication_application, convert_xor)
    factor_ask = _has(t, "factor", "गुणनखंड", "gunankhand",
                      "grouping")
    best = (None, None, -1)
    for m in _TERM_RE.finditer(t):
        seg = m.group()
        if not any(ch.isalpha() for ch in seg):
            continue
        try:
            expr = parse_expr(
                seg, transformations=transforms,
                local_dict={"x": sp.Symbol("x"),
                            "y": sp.Symbol("y"),
                            "a": sp.Symbol("a"),
                            "b": sp.Symbol("b")})
        except Exception:
            continue
        if isinstance(expr, sp.Expr) and expr.free_symbols:
            rest = (t[:m.start()] + " " + t[m.end():])
            rest = re.sub(r"[\(\)÷/=]", " ", rest)
            raw_words = [w for w in re.split(r"\s+", rest)
                         if w]
            if any(w in _OP_COMMAND_VETO for w in raw_words) \
                    or any(re.match(r"f\(", w)
                           for w in raw_words):
                continue
            leftover = [w for w in raw_words
                        if w not in _FILLER
                        and not w.isdigit()]
            if factor_ask:
                ok = True
            else:
                ok = len(leftover) <= 5 and not any(
                    w in _MATHS_LEFTOVER_VETO for w in leftover)
            if ok and len(seg) > best[2]:
                best = (expr, m.span(), len(seg))
    return best[0], best[1]


def _pretty(expr_str):
    """Student display for a factored/quotient string, in
    the house style: factors joined by the middle dot
    ("(x + 1)*(y + 3)" -> "(x + 1)·(y + 3)", "2*x" ->
    "2·x") — the same convention native's answers use."""
    return str(expr_str).replace("*", "·")


def _is_square_monomial(term):
    """term is a perfect-square monomial: a perfect-square
    rational coefficient times variables each raised to an
    even power."""
    coeff, factors = term.as_coeff_mul()
    try:
        c = abs(Fraction(str(float(coeff))))
    except Exception:
        return False
    for part in (c.numerator, c.denominator):
        r = int(part ** 0.5)
        if r * r != part:
            return False
    for f in factors:
        if f.is_Pow:
            if not f.exp.is_integer or int(f.exp) % 2 != 0:
                return False
        else:
            return False
    return True


def _is_diff_squares(expr):
    """expr is exactly A² − B²: two square monomials with
    opposite signs."""
    if not expr.is_Add or len(expr.args) != 2:
        return False
    signs = []
    for term in expr.args:
        coeff, _ = term.as_coeff_mul()
        signs.append(coeff.is_negative is True)
        if not _is_square_monomial(term):
            return False
    return signs[0] != signs[1]


def _factor_family(q, t):
    # Two written fractions are a fraction-arithmetic
    # shape, never a polynomial (Wave 212: "7/8 divide
    # by -14/3" was carved into "b*y/8 - 7/4" here).
    if len(_fracs(t)) >= 2:
        return None
    # An equation is not an expression to factorise.  The
    # API path solves "and"-split fragments separately, so
    # half of a two-line question ("6x + 8y = 9") can reach
    # this gate alone — its polynomial half must not be
    # carved out and factored.
    if "=" in t:
        return None
    expr, span = _poly_from(t)
    if expr is None:
        return None
    # Polynomial divided by a monomial/number — the
    # division may be dressed as "÷ 5", "/5", "ko 5 se
    # divide" or "divide by 5".
    dm = None
    for pat in (r"÷\s*(\d+)", r"ko\s*(\d+)\s*se\s*divide",
                r"(\d+)\s*se\s*divide",
                r"divide\s*(?:by\s*)?(\d+)",
                r"divided\s*by\s*(\d+)", r"/\s*(\d+)"):
        dm = re.search(pat, t)
        if dm:
            break
    if dm and _has(t, "factor", "factr", "divide", "भाग",
                   "गुणनखंड"):
        div = sp.Integer(dm.group(1))
        quot = sp.cancel(expr / div)
        if sp.expand(quot * div) == expr:
            return _res(
                "poly_divide", _pretty(quot),
                [f"Divide each term of {expr} by {div}.",
                 f"({expr}) ÷ {div} = {_pretty(quot)}."],
                value=None)
    if not _has(t, "factor", "factr", "गुणनखंड",
                "gunankhand"):
        # A bare difference of squares still factors: the
        # ask may be filler only ("iska ans batao").  The
        # shape must be a TRUE difference of squares — any
        # other bare two-term polynomial (the "2x + 2y"
        # fragment of a matrix-method system) is not a
        # factorisation ask and must not be carved out.
        if not _is_diff_squares(expr):
            return None
    factored = sp.factor(expr)
    if factored == expr or sp.expand(factored) != expr:
        return None
    return _res(
        "factorise",
        _pretty(str(factored).replace("**", "^")),
        [f"Factorise {str(expr).replace('**', '^')}:",
         f"= {_pretty(str(factored).replace('**', '^'))} "
         f"(check: expanding gives back the same "
         f"expression)."], value=None)


# ----------------------------------------------------------------------
# Coordinate geometry: exact distance (the decimal serve
# displaced), distance from the origin (the plot serve
# displaced), and point translation.
# ----------------------------------------------------------------------

def _coord_family(q, t):
    # Equidistant / locus asks are native's coordinate
    # specials — two points in the text are their givens,
    # not a distance ask.  The canonical bare dress is
    # native's own distance op too: by the time the text
    # reaches this layer the router has stripped it to
    # "distance between (x, y) and (x, y)".  This family
    # exists for the story/Hinglish dresses native missed
    # (queue rows).
    if _has(t, "equidistant", "locus", "समदूरस्थ") or \
            re.search(r"distance\s+between", t):
        return None
    pts = [(int(a), int(b)) for a, b in re.findall(
        r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)", t)]
    if len(pts) >= 2 and _has(t, "distance", "dist",
                              "दूरी", "doori",
                              "duuri", "length", "लंबाई",
                              "lambai"):
        (x1, y1), (x2, y2) = pts[0], pts[1]
        d2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
        return _res(
            "distance_exact", _surd(d2),
            [f"Distance = √(({x2} - {x1})² + ({y2} - {y1})²)"
             f" = √({(x2 - x1) ** 2} + {(y2 - y1) ** 2})",
             f"= {_surd(d2)}."], value=float(sp.sqrt(d2)))
    if len(pts) == 1:
        x, y = pts[0]
        if _has(t, "origin", "मूल बिंदु", "mul bindu"):
            d2 = x * x + y * y
            return _res(
                "distance_origin", _surd(d2),
                [f"Distance from origin = √({x}² + {y}²) "
                 f"= {_surd(d2)}."], value=float(sp.sqrt(d2)))
        dirs = {"right": (1, 0), "दाएँ": (1, 0), "दायें": (1, 0),
                "left": (-1, 0), "बाएँ": (-1, 0),
                "up": (0, 1), "ऊपर": (0, 1),
                "down": (0, -1), "नीचे": (0, -1)}
        if _has(t, "shift", "move", "खिसक", "shifted",
                "moved"):
            nums = [n for n in _nums(t) if n not in (x, y)]
            moves = []
            for word, vec in dirs.items():
                for m in re.finditer(
                        r"(\d+)\s*(?:units?\s*)?" + re.escape(
                            word), t):
                    moves.append((vec, int(m.group(1))))
                for m in re.finditer(
                        re.escape(word) + r"\s*(\d+)", t):
                    moves.append((vec, int(m.group(1))))
            if len(moves) == 2:
                nx = x + sum(v[0] * n for v, n in moves)
                ny = y + sum(v[1] * n for v, n in moves)
                return _res(
                    "point_shift", f"({nx}, {ny})",
                    [f"Start: ({x}, {y}).",
                     f"After the shifts: ({nx}, {ny})."],
                    value=None)
    return None


# ----------------------------------------------------------------------
# Area under / between curves for the small whitelist of
# integrands a Class-12 student meets; sympy integrates and
# the sign is sampled before serving.
# ----------------------------------------------------------------------

def _integrand(s):
    s = s.strip().lower().replace(" ", "")
    table = {"sinx": sp.sin(sp.Symbol("x")),
             "cosx": sp.cos(sp.Symbol("x")),
             "e^x": sp.exp(sp.Symbol("x")),
             "e^(2x)": sp.exp(2 * sp.Symbol("x")),
             "e^{2x}": sp.exp(2 * sp.Symbol("x")),
             "e^2x": sp.exp(2 * sp.Symbol("x")),
             "x": sp.Symbol("x"),
             "x^2": sp.Symbol("x") ** 2,
             "x^3": sp.Symbol("x") ** 3}
    return table.get(s)


def _bound(s):
    s = s.strip().lower().replace(" ", "").rstrip(".?,")
    if s.startswith("x="):
        s = s[2:]
    if s in ("pi", "π"):
        return sp.pi
    if s in ("pi/2", "π/2"):
        return sp.pi / 2
    if s in ("pi/4", "π/4"):
        return sp.pi / 4
    try:
        return sp.nsimplify(s)
    except Exception:
        return None


def _area_family(q, t):
    x = sp.Symbol("x")
    # The area word itself, or the battery's typo dress:
    # "ara under the curv y = ..." — the under/curve
    # structure plus the function and bounds below keep
    # the gate strict.
    if not _has(t, "area", "क्षेत्रफल") and not (
            re.search(r"\bunder\b", t) and re.search(
                r"\bara\b|\bcurv\w*\b", t)):
        return None
    bm = re.search(r"from\s+(\S+)\s+to\s+(\S+)", t) \
        or re.search(
        r"(\d+|pi/2|π/2|pi|π)\s*(?:to|se|से)\s*"
        r"(\d+|pi/2|π/2|pi|π)", t)
    if not bm:
        return None
    lo, hi = _bound(bm.group(1)), _bound(bm.group(2))
    if lo is None or hi is None or not bool(hi > lo):
        return None
    fm = re.search(r"f\(x\)\s*=\s*([a-z0-9\^\(\)\{\}]+)", t)
    gm = re.search(r"g\(x\)\s*=\s*([a-z0-9\^\(\)\{\}]+)", t)
    ym = re.search(r"y\s*=\s*([a-z0-9\^\(\)\{\}]+)", t)
    if fm and gm:
        f, g = _integrand(fm.group(1)), _integrand(gm.group(1))
        if f is None or g is None:
            return None
        diff = f - g
        signs = set()
        for frac in (0.1, 0.3, 0.5, 0.7, 0.9):
            xv = float(lo) + frac * (float(hi) - float(lo))
            v = float(diff.subs(x, xv))
            if abs(v) > 1e-9:
                signs.add(1 if v > 0 else -1)
        if len(signs) != 1:
            return None
        integrand = diff if signs.pop() > 0 else -diff
        val = sp.integrate(integrand, (x, lo, hi))
        ans = str(sp.factor(val)).replace("**2", "²") \
            .replace("pi", "π").replace("E", "e") \
            .replace(" ", "")
        return _res(
            "area_between", ans,
            [f"Area = ∫ |f(x) - g(x)| dx from "
             f"{bm.group(1)} to {bm.group(2)}.",
             f"= {ans} square units."], value=None)
    f = None
    if ym:
        f = _integrand(ym.group(1))
    if f is None:
        for name, expr in (("sin x", sp.sin(x)),
                           ("cos x", sp.cos(x)),
                           ("sinx", sp.sin(x)),
                           ("cosx", sp.cos(x))):
            if name in t:
                f = expr
                break
    if f is None:
        return None
    val = sp.integrate(f, (x, lo, hi))
    if val is None or not val.is_real:
        return None
    ans = str(sp.simplify(val)).replace("pi", "π")
    return _res(
        "area_under", ans,
        [f"Area = ∫ f(x) dx from {bm.group(1)} to "
         f"{bm.group(2)}.",
         f"= {ans} square units."], value=None)


# ----------------------------------------------------------------------
# Prime facts: the definition ask in story dress, the
# largest/smallest N-digit prime, and the Archimedes fact
# the pi concept card displaced.
# ----------------------------------------------------------------------

def _prime_family(q, t):
    # Who first approximated pi (Greek mathematician)?
    if _has(t, "pi", "π", "पाई") and _has(
            t, "greek", "ग्रीक", "ग्रीस", "yunan", "यूनान") \
            and _has(t, "pehle", "पहले", "first", "sabse") \
            and _has(t, "naam", "name", "कौन", "kaun", "who"):
        return _res(
            "archimedes_fact", "Archimedes",
            ["π ki value sabse pehle Greek mathematician "
             "Archimedes ne nikaali thi.",
             "Unhone π ko 223/71 aur 22/7 ke beech bandha "
             "tha — isiliye 22/7 ko Archimedes ka "
             "approximation kehte hain."], value=None)
    # Largest / smallest N-digit prime.  The digit count
    # may be a numeral ("2 digit"), a spelled-out word
    # ("two digits", "दो अंकों") — the bound is structural
    # either way (Wave 212 battery).
    m = re.search(r"(\d)\s*[- ]?\s*(?:digit|अंक|ank)", t)
    ndig = int(m.group(1)) if m else None
    if ndig is None:
        mw = re.search(
            r"\b(one|two|three|ek|do|teen)\s+"
            r"(?:digits?|अंकों|अंक)\b", t) or re.search(
            r"(एक|दो|तीन)\s*(?:अंकों|अंक)", t)
        if mw:
            ndig = {"one": 1, "two": 2, "three": 3,
                    "ek": 1, "do": 2, "teen": 3,
                    "एक": 1, "दो": 2, "तीन": 3}[mw.group(1)]
    if ndig is not None and _sig(
            t, "prime", "prme", "prim", "अभाज्य",
            "abhaajya"):
        if 1 <= ndig <= 3:
            if _has(t, "sabse badi", "सबसे बड़ी", "biggest",
                    "largest", "largst", "greatest", "badi",
                    "बड़ी"):
                cand = 10 ** ndig - 1
                while not sp.isprime(cand):
                    cand -= 1
                return _res(
                    "ndigit_prime", str(cand),
                    [f"{ndig}-digit numbers {10 ** ndig - 1} "
                     f"se neeche jaate hain.",
                     f"Sabse badi {ndig}-digit prime number "
                     f"= {cand} (sirf 1 aur khud se divide "
                     f"hoti hai)."], value=cand)
            if _has(t, "sabse chhoti", "सबसे छोटी", "smallest",
                    "chhoti", "छोटी"):
                cand = 10 ** (ndig - 1)
                while not sp.isprime(cand):
                    cand += 1
                return _res(
                    "ndigit_prime", str(cand),
                    [f"Sabse chhoti {ndig}-digit prime number "
                     f"= {cand}."], value=cand)
    # Definition ask: "a number divisible only by 1 and
    # itself is called ...?"
    if _has(t, "sirf", "only", "केवल") and 1 in _nums(t) \
            and _has(t, "khud", "itself", "स्वयं", "khud se",
                     "apne") and _has(
            t, "divide", "divisible", "भाग", "bhaag",
            "div") and _has(
            t, "kya bolte", "kya kehte", "क्या कहते",
            "called", "known as", "कहते हैं", "bolte hain"):
        return _res(
            "prime_definition",
            "Prime number (अभाज्य संख्या)",
            ["Jo sankhya sirf 1 aur khud se hi divide hoti "
             "hai, use prime number (अभाज्य संख्या) kehte "
             "hain.",
             "Example: 2, 3, 5, 7, 11 — inke sirf do "
             "factors hain: 1 aur woh sankhya khud."],
            value=None)
    return None


# ----------------------------------------------------------------------
# Junior share-division with a self-ask (queue row 63):
# "16 sweets shared by 4 — how many did *I* get?"  The core
# story layers read the sharing verb as subtraction; the
# self-ask is what makes this a division.
# ----------------------------------------------------------------------

def _share_division(q, t):
    nums = _nums(t)
    if len(nums) != 2:
        return None
    if not _has(t, "बाँट", "बांट", "baant", "baanta",
                "shared", "sharing", "बाँटकर"):
        return None
    if not _has(t, "मुझे कितने", "mujhe kitne",
                "how many did i get", "mujhe kitna",
                "मुझे कितना", "मुझे कितने मिले"):
        return None
    total, people = Fraction(str(nums[0])), Fraction(
        str(nums[1]))
    if people == int(people) and int(people) >= 2 \
            and total % people == 0:
        each = total / people
        return _res(
            "share_division", _fmt(each),
            [f"Kul {_fmt(total)} cheezen {int(people)} "
             f"hisson me barabar baanti gayi.",
             f"Har hisse me = {_fmt(total)} ÷ "
             f"{int(people)} = {_fmt(each)}."],
            value=float(each))
    return None


# ----------------------------------------------------------------------
# Add/sub chain whose last clause GIVES items away (queue
# row 13): "…then I shared/gave 20 to friends, how many are
# left?"  Fires only when the division reading is provably
# impossible for discrete objects (total % friends != 0),
# which forces the gave-N-items reading.
# ----------------------------------------------------------------------

def _chain_give(q, t):
    if not _has(t, "paas", "पास", "had", "the") or not _has(
            t, "bache", "बचे", "left", "remaining"):
        return None
    m = re.search(r"(?:paas|पास)\s*(\d+)", t)
    if not m:
        return None
    total = int(m.group(1))
    rest = t[m.end():]
    clauses = re.findall(
        r"(\d+)\s*[^,;]{0,24}?(kho|खो|lost|kharid|खरीद|"
        r"bought|aur\s+(?:liye|lie)|baant|बाँट|diye|दिए|"
        r"de\s+diye|gave)", rest)
    if len(clauses) < 3:
        return None
    steps = [f"Start: {total}."]
    for num_s, verb in clauses[:-1]:
        n = int(num_s)
        if verb.startswith(("kho", "खो", "lost")):
            total -= n
            steps.append(f"Lost {n}: {total}.")
        else:
            total += n
            steps.append(f"Got {n} more: {total}.")
    last_n, last_verb = int(clauses[-1][0]), clauses[-1][1]
    if "baant" not in last_verb and "बाँट" not in last_verb \
            and "diye" not in last_verb \
            and "दिए" not in last_verb \
            and "gave" not in last_verb:
        return None
    if last_n <= 0 or total % last_n == 0:
        # A clean division reading exists; not ours to
        # displace.
        return None
    total -= last_n
    if total < 0:
        return None
    steps.append(f"Gave {last_n} away: {total} left.")
    return _res("chain_give", str(total), steps, value=total)


# ----------------------------------------------------------------------
# Fraction arithmetic in story dress (queue rows 130-136,
# later loop cycles): two written fractions + an operation
# signal.  Fraction arithmetic is exact by construction;
# the gates are the discipline (an operation signal is
# mandatory, and no third number may be hiding).
# ----------------------------------------------------------------------

_FRAC_RE = re.compile(r"(-?\d+)\s*/\s*(-?\d+)")


def _fracs(t):
    out = []
    for a, b in _FRAC_RE.findall(t):
        if int(b) != 0:
            out.append(Fraction(int(a), int(b)))
    return out


def _frac_str(fr):
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _fraction_story(q, t):
    # A between-ask ("1/2 aur 3/4 ke beech") names two
    # fractions but asks for neither an operation nor a
    # comparison — it is the rationals-between family.
    if _has(t, "beech", "between", "बीच"):
        return None
    fr = _fracs(t)
    if not fr or len(fr) > 2:
        return None
    if len(fr) == 1:
        f = fr[0]
        if _has(t, "additive inverse", "additive invers",
                "योज्य प्रतिलोम"):
            inv = -f
            return _res(
                "fraction_additive_inverse", _frac_str(inv),
                [f"Additive inverse of {_frac_str(f)} is "
                 f"the number that makes the sum zero: "
                 f"{_frac_str(inv)}."],
                value=float(inv))
        if _has(t, "standard form", "simplest form",
                "lowest form", "सबसे छोटे", "saral roop",
                "सरल रूप"):
            return _res(
                "fraction_standard_form", _frac_str(f),
                [f"{_frac_str(f)} ko numerator aur "
                 f"denominator ke HCF se divide karo.",
                 f"Standard form = {_frac_str(f)}."],
                value=float(f))
        return None
    a, b = fr
    # Numbers beyond the two fractions' own parts mean the
    # story chains MORE operations than the single one this
    # schema performs (the difference of the fractions,
    # times 18, plus 4) — a one-operation serve from the
    # first operation word it spots is a wrong serve.
    _pool = [int(n) if float(n).is_integer() else n
             for n in _nums(t)]
    for _f in fr:
        for _p in (_f.numerator, _f.denominator):
            if _p in _pool:
                _pool.remove(_p)
    extra_nums = _pool
    if _has(t, "bada hai ya", "badi hai ya", "greater",
            "bigger", "compare", "तुलना", "kaun bada",
            "kaun si badi"):
        big = max(a, b)
        return _res(
            "fraction_compare", _frac_str(big),
            [f"{_frac_str(a)} = {float(a):.3f} aur "
             f"{_frac_str(b)} = {float(b):.3f}.",
             f"{_frac_str(big)} bada hai."],
            value=float(big))
    if not extra_nums and (_has(t, "÷", "भाग")
                           or re.search(r"\bdiv\w*", t)):
        if b == 0:
            return None
        val = a / b
        recip = Fraction(b.denominator, b.numerator)
        return _res(
            "fraction_divide", _frac_str(val),
            [f"{_frac_str(a)} ÷ {_frac_str(b)} = "
             f"{_frac_str(a)} × {_frac_str(recip)} = "
             f"{_frac_str(val)}."], value=float(val))
    if not extra_nums and _has(t, "multiply", "guna",
                               "गुणा", "×", "gunna"):
        val = a * b
        return _res(
            "fraction_multiply", _frac_str(val),
            [f"{_frac_str(a)} × {_frac_str(b)} = "
             f"{_frac_str(val)}."], value=float(val))
    if not extra_nums and _has(
            t, "cut", "bacha", "बचा", "बाकी", "remaining",
            "bach", "less", "minus", "घटा", "nikal diya",
            "निकाल"):
        val = a - b
        return _res(
            "fraction_subtract", _frac_str(val),
            [f"{_frac_str(a)} - {_frac_str(b)} = "
             f"{_frac_str(val)}."], value=float(val))
    if not extra_nums and _has(
            t, "total", "jod", "जोड़", "mila", "मिलाकर",
            "sum", "aur", "और", "dono", "दोनों"):
        val = a + b
        return _res(
            "fraction_add", _frac_str(val),
            [f"{_frac_str(a)} + {_frac_str(b)} = "
             f"{_frac_str(val)}."], value=float(val))
    return None


# ----------------------------------------------------------------------
# Small geometry facts the concept cards displaced (queue
# rows 127-129): third angle of a triangle, diameter from
# radius, angle classification by its bounds.
# ----------------------------------------------------------------------

def _triangle_angles(q, t):
    if not _has(t, "triangle", "त्रिभुज", "tribhuj"):
        return None
    if not _has(t, "teesra", "third", "तीसरा", "teesri"):
        return None
    # The angles are the numbers DRESSED as angles
    # ("50 degree"); a bare count ("2 angal") is not an
    # angle.  Fall back to all numbers only when exactly
    # two exist.
    dressed = [float(x) for x in re.findall(
        r"(\d+(?:\.\d+)?)\s*(?:degree|°|डिग्री)", t)]
    angs = dressed if len(dressed) == 2 else [
        n for n in _nums(t) if 0 < n < 180]
    if len(angs) != 2:
        return None
    a, b = angs
    if a + b >= 180:
        return None
    third = 180 - int(a) - int(b)
    return _res(
        "triangle_third_angle", f"{third}°",
        [f"Teeno angles ka sum = 180°.",
         f"Teesra angle = 180 - {int(a)} - {int(b)} = "
         f"{third}°."], value=third)


def _circle_rd(q, t):
    nums = _nums(t)
    if len(nums) != 1:
        return None
    n = nums[0]
    has_radius = bool(re.search(r"\bradi\w*", t)) \
        or _has(t, "त्रिज्या", "trijya")
    has_diameter = bool(re.search(r"\bdiam\w*", t)) \
        or _has(t, "व्यास", "vyaas")
    if has_radius and has_diameter:
        # Both named: the named VALUE is the radius when
        # the diameter is the ask ("radius 4 ... diameter
        # kitna"), and vice versa.  When no ask word
        # survives (typo dress: "what is its diamter?"),
        # the number belongs to the label NEAREST to it —
        # structure, not wording.
        if _has(t, "व्यास कितना", "diameter kitna",
                "diameter kya", "व्यास क्या",
                "diameter hoga", "व्यास होगा",
                "diameter batao"):
            serve_diameter = True
        elif _has(t, "radius kitna", "त्रिज्या कितनी",
                  "radius kya", "radius batao"):
            serve_diameter = False
        else:
            num_pos = re.search(r"\d", t).start()
            r_pos = [m.start() for m in re.finditer(
                r"\bradi\w*|त्रिज्या", t)]
            d_pos = [m.start() for m in re.finditer(
                r"\bdiam\w*|व्यास", t)]
            # The label BEFORE the number owns the value
            # ("radius ... is 4 — what is its diameter?");
            # the other quantity is the ask.
            before_r = [p for p in r_pos if p < num_pos]
            before_d = [p for p in d_pos if p < num_pos]
            if before_r or before_d:
                serve_diameter = (
                    max(before_r) > max(before_d)
                    if before_r and before_d else
                    bool(before_r))
            else:
                r_near = min((abs(p - num_pos)
                              for p in r_pos), default=999)
                d_near = min((abs(p - num_pos)
                              for p in d_pos), default=999)
                serve_diameter = r_near <= d_near
        if serve_diameter:
            return _res(
                "circle_diameter", _fmt(Fraction(str(n)) * 2),
                [f"Diameter = 2 × radius = 2 × "
                 f"{_fmt(Fraction(str(n)))} = "
                 f"{_fmt(Fraction(str(n)) * 2)}."],
                value=float(n) * 2)
        return _res(
            "circle_radius", _fmt(Fraction(str(n)) / 2),
            [f"Radius = diameter ÷ 2 = "
             f"{_fmt(Fraction(str(n)) / 2)}."],
            value=float(n) / 2)
    return None


def _angle_kind(q, t):
    if not _has(t, "angle", "कोण", "kon"):
        return None
    if not _has(t, "called", "kehte", "कहते", "kya hai",
                "what is it", "what is"):
        return None
    nums = set(_nums(t))
    if nums == {0, 90}:
        return _res(
            "angle_acute", "Acute angle (न्यूनकोण)",
            ["0° se bada aur 90° se chhota angle acute "
             "angle (न्यूनकोण) kehlata hai."], value=None)
    if nums == {90, 180}:
        return _res(
            "angle_obtuse", "Obtuse angle (अधिककोण)",
            ["90° se bada aur 180° se chhota angle obtuse "
             "angle (अधिककोण) kehlata hai."], value=None)
    if nums == {90}:
        return _res(
            "angle_right", "Right angle (समकोण)",
            ["Bilkul 90° ka angle right angle (समकोण) "
             "kehlata hai."], value=None)
    return None


# ----------------------------------------------------------------------
# Mensuration the native path mis-served (queue rows
# 137-140): cuboid total surface area and cylinder total /
# lateral surface area.  pi stays the true pi (the house
# rule); the exact multiple of pi leads, the decimal is
# the approximation.
# ----------------------------------------------------------------------

def _labelled_num(t, *labels):
    for lab in labels:
        m = re.search(re.escape(lab) + r"\s*(?:=|is|hai|है)?"
                      r"\s*(-?\d+(?:\.\d+)?)", t)
        if m:
            return float(m.group(1))
    return None


def _mensuration(q, t):
    if not (_has(t, "surface area", "पृष्ठीय",
                 "सतह क्षेत्रफल")
            or re.search(r"surf\w*\s+area", t)):
        return None
    if _has(t, "cuboid", "rectangular box", "box", "बॉक्स",
            "घनाभ"):
        l = _labelled_num(t, "length", "lambaai", "लंबाई")
        w = _labelled_num(t, "width", "breadth", "चौड़ाई")
        h = _labelled_num(t, "height", "ऊँचाई", "unchaai")
        if None in (l, w, h):
            nums = _nums(t)
            if len(nums) == 3:
                l, w, h = (float(x) for x in nums)
            else:
                return None
        tsa = 2 * (l * w + w * h + h * l)
        return _res(
            "cuboid_tsa", _fmt(Fraction(str(tsa))),
            [f"TSA = 2(lw + wh + hl) = 2({_fmt(Fraction(str(l)))}×"
             f"{_fmt(Fraction(str(w)))} + "
             f"{_fmt(Fraction(str(w)))}×{_fmt(Fraction(str(h)))} + "
             f"{_fmt(Fraction(str(h)))}×{_fmt(Fraction(str(l)))}) "
             f"= {_fmt(Fraction(str(tsa)))} square units."],
            value=tsa, full_op="cuboid tsa")
    if _has(t, "cylinder", "बेलन", "सिलेंडर"):
        r = _labelled_num(t, "radius", "त्रिज्या")
        h = _labelled_num(t, "height", "ऊँचाई", "unchaai")
        if r is None or h is None:
            nums = _nums(t)
            if len(nums) == 2:
                r, h = float(nums[0]), float(nums[1])
            else:
                return None
        lateral = _has(t, "lateral", "curved", "only",
                       "no top", "बिना", "पार्श्व")
        if lateral:
            coeff = 2 * r * h
            kind = "lateral surface area"
            formula = f"LSA = 2πrh = {coeff:g}π"
        else:
            coeff = 2 * r * (r + h)
            kind = "total surface area"
            formula = f"TSA = 2πr(r + h) = {coeff:g}π"
        # Pi convention (house rule): true pi by default,
        # 22/7 for the school mensuration shapes designed
        # for it — a radius that is a multiple of 7, where
        # native serves the exact 22/7 value (r=7, h=10
        # TSA is 748, not 747.70).
        if float(r).is_integer() and int(r) % 7 == 0:
            val = float(coeff) * 22.0 / 7.0
            ans = (f"{val:g}" if float(val).is_integer()
                   else f"≈ {val:.2f}")
            return _res(
                "cylinder_lsa" if lateral else "cylinder_tsa",
                ans,
                [f"Cylinder ka {kind}: {formula} "
                 f"(π = 22/7).",
                 f"= {ans} square units."],
                value=val,
                full_op="cylinder csa" if lateral
                else "cylinder tsa")
        val = float(coeff) * 3.141592653589793
        return _res(
            "cylinder_lsa" if lateral else "cylinder_tsa",
            f"≈ {val:.2f}",
            [f"Cylinder ka {kind}: {formula}.",
             f"≈ {val:.2f} square units."],
            value=val,
            full_op="cylinder csa" if lateral
            else "cylinder tsa")
    return None


# ----------------------------------------------------------------------
# Count-ratio (queue row 78): the ratio is carried by two
# COUNTS ("3 red balls aur 5 blue balls") instead of a digit
# pair, then the total changes and one side is asked.
# ----------------------------------------------------------------------

def _count_ratio(q, t):
    pairs = [(int(n), w) for n, w in re.findall(
        r"(\d+)\s+([a-z\u0900-\u097F]{2,})", t)]
    units = {"rs", "rupee", "meter", "metre", "km", "cm",
             "kg", "litre", "liter", "days", "day", "min",
             "mins", "minute", "minutes", "hour", "hours",
             "saal", "year", "years", "din"}
    pairs = [(n, w) for n, w in pairs if w not in units]
    if len(pairs) < 2:
        return None
    (c1, n1), (c2, n2) = pairs[0], pairs[1]
    if n1 == n2:
        return None
    nums = _nums(t)
    totals = [x for x in nums if x not in (c1, c2)]
    if len(totals) != 1:
        return None
    total = Fraction(str(totals[0]))
    if not _has(t, "total", "कुल", "kul") or not _has(
            t, "ratio", "अनुपात", "anupaat", "same"):
        return None
    unit = total / (c1 + c2)
    if unit.denominator != 1:
        return None
    ask_side = _ask_side(t, n1, n2)
    val = unit * (c2 if ask_side == 2 else c1)
    return _res(
        "count_ratio", _fmt(val),
        [f"Ratio {c1} : {c2} — kul {c1 + c2} bhaag.",
         f"Total {_fmt(total)} hai, to 1 bhaag = "
         f"{_fmt(unit)}.",
         f"Required sankhya = {_fmt(val)}."],
        value=float(val))


# ----------------------------------------------------------------------
# HCF / LCM grouping (queue row 126): two counts, the
# biggest equal group with nothing left over (HCF), or the
# smallest common meeting size (LCM).
# ----------------------------------------------------------------------

def _hcf_lcm(q, t):
    nums = [int(n) for n in _nums(t) if n == int(n)]
    if len(nums) != 2 or min(nums) < 2:
        return None
    a, b = nums
    if _has(t, "sabse bada", "सबसे बड़ा", "biggest",
            "largest", "maximum", "bada group", "hcf",
            "एचसीएफ") \
            and _has(t, "group", "समूह", "baant", "बाँट",
                     "baantna", "बाँटना", "divide",
                     "विभाजित", "arrange", "into group"):
        import math
        g = math.gcd(a, b)
        if a % g == 0 and b % g == 0 and g >= 2:
            return _res(
                "hcf_group", str(g),
                [f"Sabse bada group size = HCF({a}, {b}).",
                 f"HCF({a}, {b}) = {g} — {a} ÷ {g} = "
                 f"{a // g} groups aur {b} ÷ {g} = "
                 f"{b // g} groups, kuch nahi bachta."],
                value=g)
    if _has(t, "sabse chhota", "सबसे छोटा", "smallest",
            "lcm", "एलसीएम") and _has(
            t, "dono", "both", "saath", "साथ", "ek saath"):
        import math
        l = a * b // math.gcd(a, b)
        return _res(
            "lcm_meet", str(l),
            [f"LCM({a}, {b}) = {l}.",
             f"{l} dono se pura divide hota hai — yahi "
             f"sabse chhoti common sankhya hai."], value=l)
    return None


# ----------------------------------------------------------------------
# Dispatcher: structure first, words only to disambiguate
# inside a family.  Order is by structural distinctness —
# the most unmistakable signatures run first.
# ----------------------------------------------------------------------

_SCHEMAS = (_complex_family, _area_family, _coord_family,
            _triangle_angles, _circle_rd, _angle_kind,
            _mensuration, _fraction_story, _factor_family,
            _ap_family,
            _ratio_part,
            _count_ratio, _percent_family,
            _unit_convert,
            _time_calendar, _hcf_lcm, _decimal_story,
            _prime_family, _share_division,
            _chain_give)


def w212_upgrade(question, result):
    """Repair hook (the c12gaps142 pattern): the mixed
    plot + distance ask, where the standing serve is
    either a bare plot or a decimal distance; and the
    mensuration shapes the native path mis-serves
    (a cuboid's TSA served as l x w, a cylinder's LSA
    served as its TSA).  Fires only when a strict Wave
    212 schema settles the question completely and the
    standing answer verifiably disagrees — the schema's
    answer then stands."""
    if not isinstance(result, dict):
        return None
    mine = solve_wave212(question)
    if mine is None:
        return None
    if mine.get("op") in ("cuboid tsa",
                          "cylinder tsa",
                          "cylinder csa"):
        mv = mine.get("value")
        if mv is None:
            return None
        try:
            theirs = float(re.findall(
                r"-?\d+(?:\.\d+)?",
                str(result.get("answer") or ""))[0])
        except Exception:
            return mine
        if abs(theirs - float(mv)) <= 0.01 * max(
                1.0, abs(float(mv))):
            return None
        return mine
    if mine.get("op") not in (
            "w212_distance_exact", "w212_distance_origin"):
        return None
    op = str(result.get("op") or "")
    if op == "graph" or str(result.get("type") or "") \
            == "plot":
        return mine
    try:
        theirs = float(str(result.get("answer") or "")
                       .split()[0].rstrip(","))
    except Exception:
        return None
    mv = mine.get("value")
    if mv is None or abs(theirs - float(mv)) > 0.01:
        return None
    if str(result.get("answer")) == mine["answer"]:
        return None
    return mine


def solve_wave212(question):
    """Wave 212's strict schemas, or None.  Never raises."""
    try:
        t = _fold(question)
        if not t.strip():
            return None
        for schema in _SCHEMAS:
            try:
                out = schema(question, t)
            except Exception:
                out = None
            if out is not None:
                return out
        return None
    except Exception:
        return None
