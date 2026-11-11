"""Junior maths (Wave 13) — Classes 0-5 pattern families.

Counting & number names, place value, tables, junior word
problems (add/subtract/multiply/divide stories), fraction
basics, money stories, clock basics, shape facts, parity and
simple sequences, factors/multiples/prime lists.

Everything here is CONSERVATIVE pattern matching: a pattern
fires only when the numbers and the operation can be extracted
unambiguously. When nothing matches, solve_junior returns None
and the router falls back to the normal pipeline (which ends
in the friendly error card, never a guessed answer). All steps
are real workings computed from the extracted numbers.
"""
import re
from fractions import Fraction

from sympy import primerange

from .expression_parser import fmt_num

_NUM = r"\d+(?:\.\d+)?"
_INT = r"\d+"


def _num(s):
    return float(s) if "." in s else int(s)


def _res(op, answer, steps, value=None):
    out = {"type": "junior", "op": op, "answer": answer,
           "steps": steps}
    if value is not None:
        out["value"] = value
    return out


# --------------------------------------------------------------------------
# Number names (international system, NCERT primary style: no "and")
# --------------------------------------------------------------------------
_ONES = ["zero", "one", "two", "three", "four", "five", "six",
         "seven", "eight", "nine", "ten", "eleven", "twelve",
         "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty",
         "seventy", "eighty", "ninety"]


def _words_below_1000(n):
    parts = []
    if n >= 100:
        parts.append(_ONES[n // 100] + " hundred")
        n %= 100
    if n >= 20:
        w = _TENS[n // 10]
        if n % 10:
            w += "-" + _ONES[n % 10]
        parts.append(w)
    elif n > 0:
        parts.append(_ONES[n])
    return " ".join(parts)


def number_words(n):
    """457 -> 'four hundred fifty-seven' (0 <= n <= 999,999,999)."""
    if n == 0:
        return "zero"
    parts = []
    for scale, name in ((1_000_000, "million"), (1_000, "thousand")):
        if n >= scale:
            parts.append(_words_below_1000(n // scale) + " " + name)
            n %= scale
    if n:
        parts.append(_words_below_1000(n))
    return " ".join(parts)


_PLACES = ["ones", "tens", "hundreds", "thousands", "ten thousands",
           "hundred thousands", "millions", "ten millions",
           "hundred millions"]


# --------------------------------------------------------------------------
# Individual families — each returns a result dict or None
# --------------------------------------------------------------------------
def _number_name(q):
    m = re.search(r"(?:number\s+name\s+of|write|spell|express)\s+"
                  r"(\d{1,9})\s+in\s+words", q) or \
        re.search(r"(\d{1,9})\s+in\s+words\b", q) or \
        re.search(r"number\s+name\s+(?:of\s+)?(\d{1,9})\b", q)
    if not m:
        return None
    n = int(m.group(1))
    words = number_words(n)
    steps = [f"Read the number in groups: {fmt_num(n)}",
             f"In words: {words}"]
    return _res("number_name",
                f"{fmt_num(n)} = {words[0].upper() + words[1:]}",
                steps, n)


def _place_value(q):
    m = re.search(r"place\s+value\s+of\s+(\d)\s+in\s+(\d+)", q)
    if m:
        digit, n = int(m.group(1)), m.group(2)
        s = str(int(n))
        idx = s.rfind(str(digit))
        if idx < 0:
            return None
        pos = len(s) - 1 - idx
        value = digit * 10 ** pos
        steps = [
            f"In {s}, the digit {digit} is in the "
            f"{_PLACES[pos]} place.",
            f"Place value = {digit} × {10 ** pos} = {value}",
        ]
        return _res("place_value", str(value), steps, value)
    m = re.search(r"expanded\s+form\s+of\s+(\d+)", q)
    if m:
        s = m.group(1)
        parts = []
        steps = [f"Break {int(s)} into the value of each digit:"]
        for i, ch in enumerate(s):
            d = int(ch)
            if d:
                v = d * 10 ** (len(s) - 1 - i)
                parts.append(str(v))
                steps.append(
                    f"{d} in the {_PLACES[len(s) - 1 - i]} place "
                    f"= {v}")
        steps.append("Expanded form: " + " + ".join(parts))
        return _res("expanded_form", " + ".join(parts), steps,
                    int(s))
    return None


def _table(q):
    m = re.search(r"table\s+of\s+(\d{1,3})\b", q) or \
        re.search(r"(\d{1,3})\s+ka\s+table\b", q) or \
        re.search(r"multiplication\s+table\s+of\s+(\d{1,3})\b", q)
    if not m:
        return None
    n = int(m.group(1))
    steps = [f"{n} × {k} = {n * k}" for k in range(1, 11)]
    answer = ", ".join(str(n * k) for k in range(1, 11))
    return _res("table", answer, steps, n)


def _times_pair(q):
    m = re.fullmatch(
        r"\s*(?:what\s+is\s+)?(\d{1,3})\s*(?:x|×|\*)\s*(\d{1,3})"
        r"\s*\?*\s*", q)
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    steps = []
    if a <= 12 and b <= 12:
        steps.append(f"Use the table of {a}: count {b} steps of "
                     f"{a}.")
        steps.append(" + ".join([str(a)] * b) + f" = {a * b}")
    steps.append(f"{a} × {b} = {a * b}")
    return _res("times_pair", str(a * b), steps, a * b)


def _fraction_basics(q):
    # a/b of N
    m = re.search(r"(\d+)\s*/\s*(\d+)\s+of\s+(" + _NUM + r")", q)
    if m:
        a, b, n = int(m.group(1)), int(m.group(2)), _num(m.group(3))
        if b == 0:
            return None
        val = Fraction(a, b) * Fraction(str(n))
        steps = [
            f"Divide {fmt_num(n)} into {b} equal parts: "
            f"{fmt_num(n)} ÷ {b} = {fmt_num(Fraction(str(n)) / b)}",
            f"Take {a} part(s): {a} × "
            f"{fmt_num(Fraction(str(n)) / b)} = {fmt_num(val)}",
        ]
        return _res("fraction_of", fmt_num(val), steps,
                    float(val))
    # half / quarter of N
    m = re.search(r"\bhalf\s+of\s+(" + _NUM + r")", q) or \
        re.search(r"\bquarter\s+of\s+(" + _NUM + r")", q)
    if m:
        n = _num(m.group(1))
        div = 2 if "half" in m.group(0) else 4
        val = Fraction(str(n)) / div
        steps = [f"{'Half' if div == 2 else 'Quarter'} means "
                 f"divide by {div}: {fmt_num(n)} ÷ {div} = "
                 f"{fmt_num(val)}"]
        return _res("fraction_of", fmt_num(val), steps, float(val))
    # fraction -> decimal
    m = re.search(r"(\d+)\s*/\s*(\d+)\s+(?:as|in|into)\s+"
                  r"(?:a\s+)?decimal", q) or \
        re.search(r"convert\s+(\d+)\s*/\s*(\d+)\s+(?:to|into)\s+"
                  r"(?:a\s+)?decimal", q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == 0:
            return None
        val = a / b
        exact = Fraction(a, b)
        dec = str(int(val)) if val == int(val) else f"{val:.6g}"
        steps = [f"A fraction bar means division: {a} ÷ {b}",
                 f"{a} ÷ {b} = {dec}"]
        if exact.denominator not in (1, 2, 4, 5, 8, 10, 20, 25, 40,
                                     50, 100, 125, 200, 250, 500,
                                     1000):
            steps[-1] += " (rounded)"
        return _res("fraction_decimal", dec, steps, val)
    # decimal -> fraction
    m = re.search(r"(\d+\.\d+)\s+(?:as|in|into)\s+(?:a\s+)?"
                  r"fraction", q) or \
        re.search(r"convert\s+(\d+\.\d+)\s+(?:to|into)\s+"
                  r"(?:a\s+)?fraction", q)
    if m:
        text = m.group(1)
        frac = Fraction(text)
        places = len(text.split(".")[1])
        top = int(text.replace(".", ""))
        import math as _math
        g = _math.gcd(top, 10 ** places)
        steps = [
            f"Write it over {10 ** places}: {text} = "
            f"{top}/{10 ** places}",
            f"Divide top and bottom by {g} to simplify: "
            f"= {frac.numerator}/{frac.denominator}",
        ]
        return _res("decimal_fraction",
                    f"{frac.numerator}/{frac.denominator}", steps,
                    float(frac))
    # compare fractions
    m = re.search(
        r"(?:which|what)\s+is\s+(bigger|greater|larger|smaller)"
        r"\s*:?\s*(\d+)\s*/\s*(\d+)\s*(?:or|,|and)\s*(\d+)\s*/\s*"
        r"(\d+)", q) or re.search(
        r"compare\s+(\d+)\s*/\s*(\d+)\s*(?:and|with)\s*(\d+)\s*/\s*"
        r"(\d+)", q)
    if m:
        if m.re.pattern.startswith("(?:which"):
            want, a1, b1, a2, b2 = (m.group(1), int(m.group(2)),
                                    int(m.group(3)), int(m.group(4)),
                                    int(m.group(5)))
        else:
            want, a1, b1, a2, b2 = ("bigger", int(m.group(1)),
                                    int(m.group(2)), int(m.group(3)),
                                    int(m.group(4)))
        if b1 == 0 or b2 == 0:
            return None
        left, right = a1 * b2, a2 * b1
        steps = [
            "Cross-multiply to compare:",
            f"{a1}/{b1}: {a1} × {b2} = {left}",
            f"{a2}/{b2}: {a2} × {b1} = {right}",
        ]
        if left == right:
            steps.append("Both products are equal, so the "
                         "fractions are equal.")
            return _res("compare_fractions",
                        f"{a1}/{b1} = {a2}/{b2} (equal)", steps)
        bigger = f"{a1}/{b1}" if left > right else f"{a2}/{b2}"
        smaller = f"{a2}/{b2}" if left > right else f"{a1}/{b1}"
        steps.append(f"{bigger} has the bigger cross-product, "
                     f"so {bigger} is bigger.")
        answer = (f"{smaller} is smaller" if want == "smaller"
                  else f"{bigger} is bigger")
        return _res("compare_fractions", answer, steps)
    return None


def _word_add_sub(q):
    m = re.search(r"\badd\s+(" + _NUM + r")\s+and\s+(" + _NUM + r")",
                  q) or re.search(
                      r"\bsum\s+of\s+(" + _NUM + r")\s+and\s+("
                      + _NUM + r")", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        steps = [f"Add: {fmt_num(a)} + {fmt_num(b)}"]
        if float(a).is_integer() and float(b).is_integer() \
                and b >= 10:
            steps = [f"Break {fmt_num(b)} into hundreds, tens "
                     f"and ones and add in parts:"]
            rem, place = int(b), 1
            cur = int(a)
            chunks = []
            while rem:
                chunks.append((rem % 10) * place)
                rem //= 10
                place *= 10
            for c in reversed([c for c in chunks if c]):
                steps.append(f"{cur} + {c} = {cur + c}")
                cur += c
        steps.append(f"= {fmt_num(a + b)}")
        return _res("add", fmt_num(a + b), steps, a + b)
    m = re.search(r"\bsubtract\s+(" + _NUM + r")\s+from\s+("
                  + _NUM + r")", q)
    if m:
        small, big = _num(m.group(1)), _num(m.group(2))
        steps = [f"Subtract: {fmt_num(big)} - {fmt_num(small)} "
                 f"= {fmt_num(big - small)}"]
        return _res("subtract", fmt_num(big - small), steps,
                    big - small)
    m = re.search(r"\bdifference\s+between\s+(" + _NUM + r")\s+and"
                  r"\s+(" + _NUM + r")", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        big, small = max(a, b), min(a, b)
        steps = [f"Difference = bigger - smaller = {fmt_num(big)}"
                 f" - {fmt_num(small)} = {fmt_num(big - small)}"]
        return _res("difference", fmt_num(big - small), steps,
                    big - small)
    m = re.search(r"\bproduct\s+of\s+(" + _NUM + r")\s+and\s+("
                  + _NUM + r")", q) or re.search(
                      r"\bmultiply\s+(" + _NUM + r")\s+(?:by|and)\s+("
                      + _NUM + r")", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        steps = [f"Multiply: {fmt_num(a)} × {fmt_num(b)} = "
                 f"{fmt_num(a * b)}"]
        return _res("multiply", fmt_num(a * b), steps, a * b)
    m = re.search(r"\bdivide\s+(" + _NUM + r")\s+by\s+(" + _NUM
                  + r")", q)
    if m:
        a, b = _num(m.group(1)), _num(m.group(2))
        if b == 0:
            return None
        val = Fraction(str(a)) / Fraction(str(b))
        steps = [f"Divide: {fmt_num(a)} ÷ {fmt_num(b)} = "
                 f"{fmt_num(val)}"]
        return _res("divide", fmt_num(val), steps, float(val))
    return None


def _stories(q):
    # Money spent story (before the generic give/get stories,
    # because "buys" there means spending, not receiving).
    m = re.search(
        r"\bhas\s+(?:rs\.?|₹|rupees)?\s*(" + _INT + r")\b"
        r"[\s\S]{0,80}?\b(?:buys?|bought|spends?|spent)\b"
        r"[\s\S]{0,40}?(?:rs\.?|₹|rupees)?\s*(" + _INT + r")\b", q)
    if m and ("left" in q or "change" in q or "remain" in q):
        a, b = int(m.group(1)), int(m.group(2))
        steps = [f"Money left = money he had - money spent",
                 f"= Rs {a} - Rs {b} = Rs {a - b}"]
        return _res("money_left", f"Rs {a - b}", steps, a - b)
    # Start -> gives/loses -> left
    m = re.search(
        r"\bhas\s+(" + _INT + r")\b[\s\S]{0,80}?\b(?:gives?|gave|"
        r"loses?|lost|eats|ate)\b[\s\S]{0,40}?(" + _INT + r")\b", q)
    if m and ("left" in q or "remain" in q):
        a, b = int(m.group(1)), int(m.group(2))
        steps = [f"He started with {a} and gave away {b}.",
                 f"Left = {a} - {b} = {a - b}"]
        return _res("story_subtract", str(a - b), steps, a - b)
    # Start -> gets/buys more -> now
    m = re.search(
        r"\bhas\s+(" + _INT + r")\b[\s\S]{0,80}?\b(?:gets?|got|"
        r"receives?|received|finds|found|buys?|bought)\b"
        r"[\s\S]{0,40}?(" + _INT + r")\b[\s\S]{0,20}?\bmore\b", q)
    if m and ("now" in q or "in all" in q or "total" in q
              or "altogether" in q):
        a, b = int(m.group(1)), int(m.group(2))
        steps = [f"He had {a} and got {b} more.",
                 f"Now = {a} + {b} = {a + b}"]
        return _res("story_add", str(a + b), steps, a + b)
    # Groups of equal size: "5 boxes have 6 pencils each"
    m = re.search(
        r"\b(" + _INT + r")\s+\w+(?:\s+\w+)?\s+(?:have|has|contain|"
        r"contains)\s+(" + _INT + r")\b[\s\S]{0,40}?\beach\b", q)
    if m and ("in all" in q or "altogether" in q or "total" in q
              or "how many" in q):
        a, b = int(m.group(1)), int(m.group(2))
        steps = [f"There are {a} groups with {b} in each group.",
                 f"Total = {a} × {b} = {a * b}"]
        return _res("story_multiply", str(a * b), steps, a * b)
    # Sharing equally: "24 sweets shared equally among 6 children"
    m = re.search(
        r"\b(" + _INT + r")\b[\s\S]{0,40}?\b(?:shared|divided)\s+"
        r"equally\s+(?:among|between)\s+(" + _INT + r")\b", q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if b == 0:
            return None
        val = Fraction(a, b)
        steps = [f"Sharing equally means dividing: {a} ÷ {b}",
                 f"Each one gets {fmt_num(val)}"]
        return _res("story_divide", fmt_num(val), steps,
                    float(val))
    # Cost of N items at Rs R each
    m = re.search(
        r"\bcost\s+of\s+(" + _INT + r")\b[\s\S]{0,30}?\bat\s+"
        r"(?:rs\.?|₹|rupees)\s*(" + _NUM + r")\s*each\b", q) or \
        re.search(
            r"\b(" + _INT + r")\b[\s\S]{0,30}?\bat\s+(?:rs\.?|₹|"
            r"rupees)\s*(" + _NUM + r")\s*each\b[\s\S]{0,30}?"
            r"\bcost\b", q)
    if m:
        n, rate = int(m.group(1)), _num(m.group(2))
        steps = [f"Cost of {n} items = {n} × Rs {fmt_num(rate)}",
                 f"= Rs {fmt_num(n * rate)}"]
        return _res("money_cost", f"Rs {fmt_num(n * rate)}", steps,
                    n * rate)
    return None


def _clock(q):
    # "45 minutes after 3:30"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s*(minutes?|mins?|hours?|hrs?)\s+after\s+"
        r"(\d{1,2}):(\d{2})\s*(am|pm)?", q)
    if m:
        amt = float(m.group(1))
        is_hours = m.group(2).startswith("h")
        add_min = int(amt * 60) if is_hours else int(amt)
        hh, mm = int(m.group(3)), int(m.group(4))
        suffix = m.group(5)
        base = hh % 12 * 60 + mm
        if suffix == "pm":
            base += 12 * 60
        total = base + add_min
        end_h24, end_m = divmod(total, 60)
        end_h24 %= 24
        if suffix:
            out_suffix = "am" if end_h24 < 12 else "pm"
            h12 = end_h24 % 12 or 12
            ans = f"{h12}:{end_m:02d} {out_suffix.upper()}"
        else:
            ans = f"{end_h24}:{end_m:02d}"
        steps = [
            f"Start time: {hh}:{mm:02d}"
            + (f" {suffix.upper()}" if suffix else ""),
            f"Add {fmt_num(amt)} "
            f"{'hours' if is_hours else 'minutes'}: the clock "
            f"moves forward to {ans}",
        ]
        return _res("clock_after", ans, steps)
    # Elapsed: "from 2 pm to 5 pm how many hours"
    m = re.search(
        r"\bfrom\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s+to\s+"
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", q)
    if m:
        def _to_min(h, mnt, sfx):
            v = (int(h) % 12) * 60 + int(mnt or 0)
            return v + (720 if sfx == "pm" else 0)
        start = _to_min(m.group(1), m.group(2), m.group(3))
        end = _to_min(m.group(4), m.group(5), m.group(6))
        if end <= start:
            end += 24 * 60
        diff = end - start
        hours, mins = divmod(diff, 60)
        steps = [
            f"Count forward from {m.group(1)} "
            f"{m.group(3).upper()} to {m.group(4)} "
            f"{m.group(6).upper()}.",
            f"Time passed = {hours} hours"
            + (f" {mins} minutes" if mins else ""),
        ]
        answer = (f"{hours} hours" if not mins else
                  f"{hours} hours {mins} minutes")
        return _res("elapsed_time", answer, steps, diff / 60)
    # Months in years ("how many months in 3 years")
    m = re.search(r"how\s+many\s+months\s+in\s+(\d+)\s+years?", q)
    if m:
        y = int(m.group(1))
        steps = ["1 year = 12 months",
                 f"{y} years = {y} × 12 = {y * 12} months"]
        return _res("time_convert", f"{y * 12} months", steps,
                    y * 12)
    return None


_SHAPES = {
    "triangle": 3, "quadrilateral": 4, "square": 4, "rectangle": 4,
    "pentagon": 5, "hexagon": 6, "heptagon": 7, "octagon": 8,
    "nonagon": 9, "decagon": 10, "circle": 0,
}
_SHAPE_BY_SIDES = {v: k for k, v in _SHAPES.items() if v >= 3}


def _shapes(q):
    m = re.search(r"how\s+many\s+sides\s+(?:does|has)\s+(?:a\s+|an"
                  r"\s+)?(\w+)\s+have", q) or re.search(
                      r"how\s+many\s+sides\s+(?:in|does)\s+(?:a\s+|"
                      r"an\s+)?(\w+)", q) or re.search(
                          r"(\w+)\s+has\s+how\s+many\s+sides", q)
    if m:
        name = m.group(1)
        if name in _SHAPES:
            n = _SHAPES[name]
            steps = [f"A {name} has {n} sides."
                     if n else "A circle is round — it has no "
                     "straight sides (0 sides)."]
            return _res("shape_sides", str(n), steps, n)
        return None
    m = re.search(r"how\s+many\s+(?:corners|vertices)\s+(?:does\s+)?"
                  r"(?:a\s+|an\s+)?(\w+)", q)
    if m and m.group(1) in _SHAPES:
        name = m.group(1)
        n = _SHAPES[name]
        steps = [f"For a polygon, corners (vertices) = sides, "
                 f"so a {name} has {n} corners."]
        return _res("shape_corners", str(n), steps, n)
    m = re.search(r"(?:shape|polygon)\s+with\s+(\d+)\s+sides", q) \
        or re.search(r"(\d+)\s*-\s*sided\s+(?:shape|polygon)", q) \
        or re.search(r"name\s+the\s+shape\s+with\s+(\d+)\s+sides", q)
    if m:
        n = int(m.group(1))
        name = _SHAPE_BY_SIDES.get(n)
        if name is None:
            return None
        steps = [f"A shape with {n} sides is called a {name}."]
        return _res("shape_name", name.capitalize(), steps, n)
    return None


def _parity_sequences(q):
    # "is 47 odd or even"
    m = re.search(r"\bis\s+(\d+)\s+(?:odd\s+or\s+even|even\s+or\s+"
                  r"odd)\b", q) or re.search(
                      r"\b(\d+)\s+is\s+(odd|even)\b", q)
    if m and "between" not in q:
        n = int(m.group(1))
        parity = "even" if n % 2 == 0 else "odd"
        steps = [
            f"Divide {n} by 2: {n} = 2 × {n // 2} + {n % 2}",
            f"Remainder is {n % 2}, so {n} is {parity}.",
        ]
        if m.re.pattern.startswith(r"\b(\d+)"):
            claimed = m.group(2)
            steps.insert(0, f"You said {claimed} — let us check.")
            if claimed != parity:
                steps.append(f"So the correct answer is: {n} is "
                             f"{parity}, not {claimed}.")
        return _res("parity", f"{n} is {parity}", steps, n)
    # odd/even numbers between a and b
    m = re.search(r"\b(odd|even)\s+numbers?\s+(?:between|from)\s+"
                  r"(\d+)\s+(?:and|to)\s+(\d+)", q)
    if m:
        want_odd = m.group(1) == "odd"
        a, b = int(m.group(2)), int(m.group(3))
        lo, hi = min(a, b), max(a, b)
        nums = [v for v in range(lo + 1, hi)
                if (v % 2 == 1) == want_odd]
        steps = [
            f"{'Odd' if want_odd else 'Even'} numbers lie "
            f"between {lo} and {hi} (not counting the ends):",
            ", ".join(str(v) for v in nums) or "none",
            f"There are {len(nums)} of them.",
        ]
        return _res("parity_list", ", ".join(str(v) for v in nums),
                    steps, len(nums))
    # next number / missing number in a sequence
    m = re.search(r"next\s+number\s*(?:is)?\s*:?\s*(.+)$", q) or \
        re.search(r"what\s+comes\s+next\s*:?\s*(.+)$", q) or \
        re.search(r"comes\s+next\s*:?\s*(.+)$", q) or \
        re.search(r"missing\s+number\s*:?\s*(.+)$", q)
    if m:
        tail = m.group(1)
        # Drop any lead-in words ("in the sequence 2, 4, ..."):
        # the list starts at the first digit or gap marker.
        dm = re.search(r"\d|\?|_", tail)
        if dm:
            tail = tail[dm.start():]
        tokens = [t.strip() for t in tail.split(",") if t.strip()]
        values, missing_idx = [], None
        for i, t in enumerate(tokens):
            if t in ("?", "_", "-", "…", "..."):
                missing_idx = i
                values.append(None)
            else:
                mm = re.fullmatch(r"-?\d+(?:\.\d+)?", t)
                if not mm:
                    return None
                values.append(_num(t))
        known = [(i, v) for i, v in enumerate(values)
                 if v is not None]
        if len(known) < 3 or len(values) < 3:
            return None
        # Arithmetic progression through the known terms?
        (i0, v0), (i1, v1) = known[0], known[-1]
        span = i1 - i0
        if span and (v1 - v0) % span == 0:
            d = (v1 - v0) // span if float(v1 - v0).is_integer() \
                else (v1 - v0) / span
            if all(v0 + (i - i0) * d == v for i, v in known):
                steps = [
                    "Each number grows by the same amount: "
                    f"+ {fmt_num(d)} each time.",
                ]
                if missing_idx is None or \
                        missing_idx == len(values) - 1:
                    target = missing_idx if missing_idx is not None \
                        else len(values)
                    nxt = v0 + (target - i0) * d
                    steps.append(
                        "The next number in the pattern is "
                        f"{fmt_num(nxt)}.")
                    return _res("sequence_next", fmt_num(nxt),
                                steps, nxt)
                fill = v0 + (missing_idx - i0) * d
                steps.append(
                    f"So position {missing_idx + 1} = "
                    f"{fmt_num(fill)}")
                return _res("sequence_missing", fmt_num(fill),
                            steps, fill)
        # Geometric progression (integers only, safe division)
        if all(v is not None for v in values) and values[0] != 0 \
                and missing_idx is None:
            ratios = [values[i + 1] / values[i]
                      for i in range(len(values) - 1)]
            if all(r == ratios[0] for r in ratios) and ratios[0]:
                r = ratios[0]
                nxt = values[-1] * r
                steps = [
                    f"Each number is multiplied by "
                    f"{fmt_num(r)}: "
                    + ", ".join(fmt_num(v) for v in values),
                    f"Next = {fmt_num(values[-1])} × {fmt_num(r)}"
                    f" = {fmt_num(nxt)}",
                ]
                return _res("sequence_next", fmt_num(nxt), steps,
                            nxt)
        return None
    return None


def _factors_multiples_primes(q):
    # factors of N (only for the bare junior question; the
    # number_theory intent claims most "factors of" phrasings
    # first — see router note — this covers multiples/primes)
    m = re.search(r"\bprime\s+numbers?\s+(?:between|from)\s+(\d+)"
                  r"\s+(?:and|to)\s+(\d+)", q)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        lo, hi = min(a, b), max(a, b)
        primes = list(primerange(lo, hi + 1))
        steps = [
            f"A prime number has exactly two factors: 1 and "
            f"itself.",
            f"Checking every number from {lo} to {hi}, the "
            f"primes are:",
            ", ".join(str(p) for p in primes) or "none",
        ]
        return _res("primes_between",
                    ", ".join(str(p) for p in primes), steps,
                    len(primes))
    m = re.search(r"\bmultiples?\s+of\s+(\d+)\s+(?:up\s+to|till|"
                  r"until)\s+(\d+)", q)
    if m:
        n, limit = int(m.group(1)), int(m.group(2))
        if n == 0:
            return None
        vals = list(range(n, limit + 1, n))
        steps = [f"Count in {n}s: "
                 + ", ".join(str(v) for v in vals)]
        return _res("multiples", ", ".join(str(v) for v in vals),
                    steps, len(vals))
    m = re.search(r"\bfirst\s+(\d+)\s+multiples?\s+of\s+(\d+)", q)
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        if k > 50:
            return None
        vals = [n * i for i in range(1, k + 1)]
        steps = [f"{n} × {i} = {n * i}" for i in range(1, k + 1)]
        return _res("multiples", ", ".join(str(v) for v in vals),
                    steps, len(vals))
    m = re.search(r"\bfactors?\s+of\s+(\d+)\b", q)
    if m:
        rest = re.sub(
            r"\bfactors?\b|\bof\b|\bthe\b|\ball\b|\blist\b|\bgive\b"
            r"|\bme\b|\bwhat\b|\bare\b|\bplease\b|\d+", "", q).strip()
        if rest:
            return None
        n = int(m.group(1))
        divs = [d for d in range(1, n + 1) if n % d == 0]
        pairs = [(d, n // d) for d in divs if d <= n // d]
        steps = ["Find pairs that multiply to "
                 f"{n}:"] + [
                     f"{d} × {e} = {n}" for d, e in pairs] + [
                     f"So the factors of {n} are: "
                     + ", ".join(str(d) for d in divs)]
        return _res("factors", ", ".join(str(d) for d in divs),
                    steps, len(divs))
    return None


def _rectangle_by(q):
    m = re.search(
        r"\b(perimeter|area)\s+of\s+(?:a\s+)?rectangle\s+(?:of\s+)?"
        r"(" + _NUM + r")\s*(?:cm|m|mm)?\s*(?:by|x|×)\s*(" + _NUM
        + r")", q)
    if m:
        kind = m.group(1)
        l, b = _num(m.group(2)), _num(m.group(3))
        if kind == "perimeter":
            val = 2 * (l + b)
            steps = [f"Perimeter = 2 × (length + breadth) = 2 × "
                     f"({fmt_num(l)} + {fmt_num(b)}) = "
                     f"{fmt_num(val)}"]
            return _res("perimeter", fmt_num(val), steps, val)
        val = l * b
        steps = [f"Area = length × breadth = {fmt_num(l)} × "
                 f"{fmt_num(b)} = {fmt_num(val)}"]
        return _res("area", fmt_num(val), steps, val)
    m = re.search(
        r"\b(perimeter|area)\s+of\s+(?:a\s+)?square\s+(" + _NUM
        + r")\s*(?:cm|m|mm)?\s*$", q.strip())
    if m:
        kind, s = m.group(1), _num(m.group(2))
        if kind == "perimeter":
            steps = [f"Perimeter = 4 × side = 4 × {fmt_num(s)} = "
                     f"{fmt_num(4 * s)}"]
            return _res("perimeter", fmt_num(4 * s), steps, 4 * s)
        steps = [f"Area = side × side = {fmt_num(s)} × "
                 f"{fmt_num(s)} = {fmt_num(s * s)}"]
        return _res("area", fmt_num(s * s), steps, s * s)
    return None


_FAMILIES = (_number_name, _place_value, _table, _times_pair,
             _fraction_basics, _word_add_sub, _stories, _clock,
             _shapes, _parity_sequences, _factors_multiples_primes,
             _rectangle_by)


def solve_junior(question: str):
    """Wave 13 junior solver. Returns a result dict, or None
    when no junior pattern matches (the router then falls
    back to the normal pipeline). Never raises."""
    try:
        q = " " + str(question).strip().lower() + " "
        q = re.sub(r"\s+", " ", q)
        for fn in _FAMILIES:
            try:
                out = fn(q)
            except Exception:
                out = None
            if out is not None:
                return out
        return None
    except Exception:
        return None
