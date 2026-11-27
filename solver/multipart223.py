"""Wave 223 (DeepSeek Job 9): multi-part questions, jad se.

WHY THIS MODULE EXISTS
----------------------
The live checker (ChatGPT Jobs A/B/C, 23 Nov 2026) caught:

    "ek aayat ka kshetrafal aur parimap batao, lambai
     8 cm, chaudai 5 cm"   ->  sirf area 40; parimap 26 gayab

and the English dress of the same question lost a part too:

    "Find the area and perimeter of a rectangle whose
     length is 8 cm and breadth is 5 cm"  ->  sirf ek jawab

ROOT CAUSE (mechanism, not symptom): EVERY layer that can
serve these questions is built to return exactly ONE result
for the FIRST ask it recognises, and no layer ever looks for
a second ask:

  * solver/geometry.py's rectangle branch is literally
    `if "perimeter" in q: return perimeter; return area` —
    one op, chosen by keyword presence, the other ask never
    examined.  The circle branch and the arithmetic router
    (sum/difference/product) have the same single-op shape.
  * The Hinglish whole-question translator
    (router.normalize_hinglish) is first-match-wins: an
    early UNCONDITIONAL rectangle-area rule (aayat + lambai
    + chaudai -> "area of a rectangle ...") shadows the
    ask-sensitive rules below it, so a two-ask Hinglish
    question collapses to a single-ask English one before
    any solver runs — "parimap batao" ALONE is served as
    area by the same shadowing.

THE FIX (this module, per DeepSeek Job 9's verified spec):
split BEFORE those single-ask paths, but only when two
genuine asks provably exist, solve each part through the
ordinary pipeline, verify each part's op is the ask it
claims to answer, and assemble one result in the Wave 100
multipart format ("(a) ... (b) ...", the answer line naming
every part).  Any doubt at any step -> None, and the
pre-Wave-223 flow decides exactly as before.

split_parts(text) follows the Job 9 contract: it returns
{"parts": [part1, part2, ...]} only when two separate asks
exist.  Split candidates are tried in the spec's order —
sentence, semicolon, "aur"/"and" — the before-part must be
a complete clause and the after-part must carry its own ask
signal.  The spec's trap stays a non-split:

    "lambai aur chaudai 12 aur 8 hai, area batao" -> None
    (the "aur"s join DATA words; there is only one ask)

Families owned here (each strict, each verified):

  * Mensuration ask-lists — two (or three) of area /
    perimeter / circumference / diameter joined by and/aur
    over ONE shape with extractable dimensions (rectangle,
    square, circle; English + Roman Hinglish + Devanagari).
    Parts are rebuilt in the canonical English forms the
    translator itself emits, because the Hinglish path is
    single-ask by construction (see above).
  * Sum / difference / product ask-lists over exactly two
    numbers ("sum and difference of 25 and 13" -> 38, 12).
  * Money: cost of N items + the change from a note.  This
    family is computed HERE, not delegated, because the
    pipeline provably cannot: the pay dress ("How much
    does he pay?") errors in the expression parser, and
    Wave 212's money_change schema misfires on this shape
    (its "note" substring test fires inside "notebooks"
    and it reads the item COUNT as a second price —
    "Total spent = 30 + 4 = ₹34", change ₹166, both wrong;
    sahi: total ₹120, change ₹80).
  * Generic two-clause questions (the Job 9 core): two
    independent ask clauses sharing at most a data
    preamble.  Every part must solve on its own and the
    two parts must not collapse to the same (op, answer),
    or the gate declines.

Follow-up safety: "samjhao" / "galat hai, phir se karo"
carry no ask pair, so they return None here and the
Wave 214/216/220 anchoring flow is untouched; a re-solve
of an anchored two-ask question now serves BOTH parts,
which is the point of the fix.
"""

import re
import threading
from fractions import Fraction

_ACTIVE = threading.local()

_N = r"(\d+(?:\.\d+)?)"
_LABELS = "abcd"

# ---------------------------------------------------------------------------
# Ask vocabularies.  Each ask maps to the solver ops that are
# allowed to answer it — a part whose op is not in its set is
# NOT an answer to that ask, and the whole gate declines.
# ---------------------------------------------------------------------------

_ASK_OPS = {
    "area": {"area"},
    "perimeter": {"perimeter"},
    "circumference": {"circumference"},
    "diameter": {"diameter", "w212_circle_diameter"},
    "sum": {"add"},
    "difference": {"subtract"},
    "product": {"multiply"},
}

_MENS_ASK_WORDS = [
    ("area", r"\barea\b|kshetrafal|क्षेत्रफल"),
    ("perimeter", r"\bperimeter\b|parimap|परिमाप"),
    ("circumference", r"\bcircumference\b|paridhi|परिधि"),
    ("diameter", r"\bdiameter\b"),
]

_SUM_ASK_WORDS = [
    ("sum", r"\bsum\b|yog|योग"),
    ("difference", r"\bdifference\b|antar|अंतर"),
    ("product", r"\bproduct\b|gunanfal|गुणनफल"),
]

# "vyas / व्यास" is diameter in both directions: followed by
# a number it is DATA (the diameter is given); bare, in an
# ask list, it is the ASK.  Handled in _mensuration_parts.

_CONJ_GAP = re.compile(
    r"^[\s,;]*(?:and|aur|or|तथा|एवं|और|व|,|&|\+)[\s,;]*$")

_ASK_SIGNALS = re.compile(
    r"find|calculate|determine|solve|what\s+is|what\s+are|"
    r"how\s+much|how\s+many|how\s+long|how\s+far|"
    r"batao|nikalo|kitna|kitne|kitni|hal\s+karo|gyat|"
    r"बताओ|निकालो|कितना|कितने|ज्ञात|"
    r"\barea\b|\bperimeter\b|\bcircumference\b|\bdiameter\b|"
    r"kshetrafal|parimap|paridhi|क्षेत्रफल|परिमाप|परिधि",
    re.I)

_STRONG_SIGNALS = re.compile(
    r"find|calculate|determine|solve|what\s+is|what\s+are|"
    r"how\s+much|how\s+many|how\s+long|how\s+far|"
    r"batao|nikalo|kitna|kitne|kitni|hal\s+karo|gyat|"
    r"बताओ|निकालो|कितना|कितने|ज्ञात", re.I)


def _seg_has_ask(seg):
    """A segment carries an ask when it has a strong ask
    signal (find / how much / batao ...), or an ask noun
    that is not just naming GIVEN data.  'The area of a
    circle is 154 cm2.' names data — its only ask noun has
    its value stated in the same clause — so the segment is
    a preamble, not an ask (Job 9's complete-clause rule
    must not promote data statements into questions)."""
    if _STRONG_SIGNALS.search(seg):
        return True
    if not _ASK_SIGNALS.search(seg):
        return False
    hits = _ask_hits(seg.lower(),
                     _MENS_ASK_WORDS + _SUM_ASK_WORDS)
    for _ask, _s, e in hits:
        if not re.search(r"(?:is|=|hai)\s*\d", seg[e:]):
            return True
    return False

_LABELLED = re.compile(
    r"\(\s*(?:i{1,3}|iv|v|[a-e])\s*\)|\bcase\s+study\b|"
    r"based\s+on\s+the\s+above|\bhence\b", re.I)


def _fmt(fr):
    """Fraction -> the plain school format (120, not 120.0)."""
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return str(float(fr))


def _is_solved(result):
    """A part counts as solved only on a real solver result —
    never an error shell, never a 'Could not ...' answer."""
    if not result:
        return False
    if result.get("op") in ("error", "unknown", None):
        return False
    ans = str(result.get("answer") or "")
    if not ans or ans.startswith("Could not"):
        return False
    return True


def _ask_hits(text, word_table):
    """Ask-noun occurrences in text order:
    [(ask, start, end), ...].  An occurrence immediately
    followed by a NUMBER ('diameter 14 cm', 'area is 154')
    is GIVEN data, not an ask, and is skipped — the ask
    dress is 'diameter of ...' / 'diameter kitna', never
    'diameter 14'."""
    hits = []
    for ask, pat in word_table:
        for m in re.finditer(pat, text, re.I):
            tail = text[m.end():m.end() + 10]
            if re.match(r"\s*(?:is|=|hai)?\s*\d", tail):
                continue
            hits.append((ask, m.start(), m.end()))
    hits.sort(key=lambda h: h[1])
    return hits


def _asks_joined(text, hits):
    """The asks form ONE ask-list: every consecutive pair is
    separated by nothing but a conjunction / comma (no data,
    no number in between)."""
    if len(hits) < 2:
        return False
    for (_, _s1, e1), (_, s2, _e2) in zip(hits, hits[1:]):
        if not _CONJ_GAP.match(text[e1:s2]):
            return False
    return True


def _assemble(op, solved_parts, part_texts):
    """Wave 100 multipart format: steps grouped under
    (a)/(b) labels, the answer line naming every part."""
    steps = []
    answer_bits = []
    for i, result in enumerate(solved_parts):
        label = _LABELS[i]
        answer_bits.append(f"({label}) {result.get('answer')}")
        part_steps = [str(s) for s in result.get("steps") or []]
        if part_steps:
            steps.append(f"({label}) {part_steps[0]}")
            steps.extend(part_steps[1:])
        else:
            steps.append(f"({label}) {result.get('answer')}")
    return {
        "type": "Multipart",
        "op": op,
        "answer": "; ".join(answer_bits),
        "steps": steps,
        "source": "wave223",
        "parts": list(part_texts),
        "multipart": {"kind": "two_ask", "solved": [
            _LABELS[i] for i in range(len(solved_parts))],
            "total": len(solved_parts)},
    }


# ---------------------------------------------------------------------------
# Family 1 — mensuration ask-lists (rectangle / square / circle)
# ---------------------------------------------------------------------------

def _unit_near(text, fallback=""):
    m = re.search(r"\b(cm|mm|km|m)\b", text)
    return f" {m.group(1)}" if m else fallback


def _mensuration_parts(q):
    """-> (part_texts, expected_ops) or None."""
    ql = q.lower()
    if len(re.findall(r"rectangle|aayat|आयत|circle|vritt|वृत्त|"
                      r"square|varg|वर्ग", ql)) != 1:
        return None  # zero shapes, or a two-clause question
    hits = _ask_hits(ql, _MENS_ASK_WORDS)
    # vyas / व्यास as an ASK (bare — not followed by a number)
    for m in re.finditer(r"vyas|व्यास", ql):
        tail = ql[m.end():m.end() + 8]
        if not re.match(r"\s*\d", tail):
            hits.append(("diameter", m.start(), m.end()))
    hits.sort(key=lambda h: h[1])
    asks = [h[0] for h in hits]
    if len(set(asks)) < 2 or len(asks) > 3:
        return None
    if not _asks_joined(ql, hits):
        return None

    unit = _unit_near(ql)

    def num(pat):
        m = re.search(pat, ql)
        return m.group(1) if m else None

    if re.search(r"rectangle|aayat|आयत", ql):
        if not set(asks) <= {"area", "perimeter"}:
            return None
        length = num(r"(?:length|lambai|लम्बाई|लंबाई)\s*"
                     r"(?:is\s+|hai\s+)?" + _N) or \
            num(r"rectangle\s+(?:of\s+)?" + _N)
        breadth = num(r"(?:breadth|width|chaudai|चौड़ाई)\s*"
                      r"(?:is\s+|hai\s+)?" + _N)
        if length is None or breadth is None:
            m2 = re.search(r"rectangle\s+(?:of\s+)?" + _N +
                           r"\s*(?:cm|mm|km|m)?\s*(?:by|x|×)\s*"
                           + _N, ql)
            if m2:
                length, breadth = m2.group(1), m2.group(2)
        if length is None or breadth is None:
            return None
        tail = (f"of a rectangle with length {length}{unit} "
                f"and breadth {breadth}{unit}")
    elif re.search(r"\bsquare\b|\bvarg\b|वर्ग", ql):
        if "vargmul" in ql or "वर्गमूल" in ql or "perfect" in ql:
            return None
        if not set(asks) <= {"area", "perimeter"}:
            return None
        side = num(r"(?:side|bhuja|भुजा)\s*(?:is\s+|hai\s+)?"
                   + _N)
        if side is None:
            return None
        tail = f"of a square with side {side}{unit}"
    elif re.search(r"circle|vritt|वृत्त", ql):
        if not set(asks) <= {"area", "circumference", "diameter"}:
            return None
        radius = num(r"(?:radius|trijya|त्रिज्या)\s*"
                     r"(?:is\s+|hai\s+)?" + _N) or \
            num(_N + r"\s*(?:cm|mm|km|m)?\s*"
                r"(?:radius|trijya|त्रिज्या)\b")
        diam = num(r"(?:diameter|vyas|व्यास)\s*"
                   r"(?:is\s+|hai\s+)?" + _N)
        if radius is not None and "diameter" not in asks \
                and diam is not None:
            return None  # both given — not this family's shape
        if radius is not None:
            tail = f"of a circle with radius {radius}{unit}"
        elif diam is not None:
            tail = f"of a circle with diameter {diam}{unit}"
        else:
            return None
    else:
        return None
    parts = [f"{ask} {tail}" for ask in asks]
    return parts, [_ASK_OPS[a] for a in asks]


# ---------------------------------------------------------------------------
# Family 2 — sum / difference / product ask-lists over two numbers
# ---------------------------------------------------------------------------

def _sum_parts(q):
    """-> (part_texts, expected_ops) or None."""
    ql = q.lower()
    if "%" in ql or "ratio" in ql or "average" in ql \
            or "mean" in ql:
        return None
    hits = _ask_hits(ql, _SUM_ASK_WORDS)
    asks = [h[0] for h in hits]
    if len(set(asks)) < 2 or len(asks) > 3:
        return None
    if not _asks_joined(ql, hits):
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", ql)
    if len(nums) != 2:
        return None
    a, b = nums
    parts = [f"{ask} of {a} and {b}" for ask in asks]
    return parts, [_ASK_OPS[x] for x in asks]


# ---------------------------------------------------------------------------
# Family 3 — money: cost of N items + change from a note (computed here)
# ---------------------------------------------------------------------------

_PAY_ASK = re.compile(
    r"how\s+much[^?]{0,30}\b(?:pay|spend|spent)\b|"
    r"total\s+cost|total\s+price|"
    r"how\s+much[^?]{0,20}\bcost\b|kitna\s+paisa\s+lagega|"
    r"kitne\s+rupaye\s+lagenge|how\s+much\s+money[^?]{0,20}"
    r"spend|kitn[ae]\s+(?:rupaye\s+)?kharch|"
    r"kharch\s+(?:kiye|kiya|karenge|hoga)", re.I)
_CHANGE_ASK = re.compile(
    r"\bchange\b|money\s+is\s+left|how\s+much[^?]{0,20}left|"
    r"bacha|bache|बचा|बचे|bachenge|wapas\s+milega", re.I)
_COUNT_PRICE = [
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"(?:at|@)\s*(?:rs\.?|₹|rupees?)\s*"
               r"(\d+(?:\.\d+)?)\s*(?:each|per\s+\w+)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"(?:costing|priced\s+at)\s*(?:rs\.?|₹|rupees?)\s*"
               r"(\d+(?:\.\d+)?)\s*each", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s+\S+\s+(?:rs\.?|₹|rupaye)?\s*"
               r"(\d+(?:\.\d+)?)\s*(?:rupaye\s+)?(?:prati|प्रति)",
               re.I),
    # Wave 224: the price BEFORE its currency word — "at 30
    # rupees each" (the Deploy-66 live wording).  The three
    # patterns above all demand the currency first ("at
    # Rs 30 each"), so this whole dress declined.
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"(?:at|@|for)\s*(\d+(?:\.\d+)?)\s*"
               r"(?:rupees?|rs\.?|₹)?\s*(?:each|per\s+\w+)",
               re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"for\s*(?:rs\.?|₹|rupees?)\s*"
               r"(\d+(?:\.\d+)?)\s*(?:each|per\s+\w+)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s+(?:[a-zA-Z]{2,}\s+){0,3}?"
               r"(?:costing|priced\s+at)\s*(\d+(?:\.\d+)?)\s*"
               r"(?:rupees?|rs\.?|₹)?\s*each", re.I),
]
_NOTE = [
    re.compile(r"(?:from|gave|gives|give|paid|has|have|with|"
               r"diye|diya)\s+(?:a\s+)?(?:rs\.?|₹|rupees?)\s*"
               r"(\d+(?:\.\d+)?)", re.I),
    re.compile(r"(?:rs\.?|₹|rupees?)\s*(\d+(?:\.\d+)?)\s*"
               r"(?:ka\s+)?note", re.I),
    # Wave 224: plural "rupees" — "a 200 rupees note" (the
    # Deploy-66 live wording) missed the singular-only
    # "rupee" alternation below.
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:rupees?|rs\.?|rupaye)\s+"
               r"(?:ka\s+)?note", re.I),
    re.compile(r"note\s+of\s+(?:rs\.?|₹|rupees?)?\s*"
               r"(\d+(?:\.\d+)?)", re.I),
    re.compile(r"(\d+(?:\.\d+)?)\s*rupaye\s+diye", re.I),
]


def _money_result(q):
    """The finished two-part result, or None.  Computed with
    exact Fractions; both asks must be present, the
    count x unit-price structure must be explicit ('each' /
    'per' / 'prati'), and the note must exceed the total.
    Wave 224 widened the surface forms after the Deploy-66
    live failure: 'spend'/'spent' asks without the word
    'money', Hinglish 'kharch' asks and 'bache' change asks,
    the price BEFORE its currency word ('at 30 rupees
    each'), and the plural note ('a 200 rupees note')."""
    ql = q.lower()
    if "%" in ql or "discount" in ql or "profit" in ql \
            or "loss" in ql or "interest" in ql:
        return None
    pay_m = _PAY_ASK.search(ql)
    change_m = _CHANGE_ASK.search(ql)
    if not pay_m or not change_m:
        return None
    cp = None
    for pat in _COUNT_PRICE:
        cp = pat.search(ql)
        if cp:
            break
    if not cp:
        return None
    count, price = Fraction(cp.group(1)), Fraction(cp.group(2))
    if count <= 0 or price <= 0 or count.denominator != 1:
        return None
    note = None
    for pat in _NOTE:
        nm = pat.search(ql)
        if nm:
            cand = Fraction(nm.group(1))
            if cand != count and cand != price:
                note = cand
                break
    if note is None:
        return None
    total = count * price
    change = note - total
    if total <= 0 or change < 0:
        return None
    pay_part = {
        "answer": f"₹{_fmt(total)}",
        "steps": [f"Total cost = {_fmt(count)} × "
                  f"₹{_fmt(price)} = ₹{_fmt(total)}"],
    }
    change_part = {
        "answer": f"₹{_fmt(change)}",
        "steps": [f"Total cost = {_fmt(count)} × "
                  f"₹{_fmt(price)} = ₹{_fmt(total)}",
                  f"Change = ₹{_fmt(note)} − ₹{_fmt(total)} "
                  f"= ₹{_fmt(change)}"],
    }
    ordered = [pay_part, change_part] \
        if pay_m.start() < change_m.start() \
        else [change_part, pay_part]
    texts = ["total cost", "change"] \
        if ordered[0] is pay_part else ["change", "total cost"]
    return _assemble("multipart_money", ordered, texts)


# ---------------------------------------------------------------------------
# Family 4 — the Job 9 generic split (two independent ask clauses)
# ---------------------------------------------------------------------------

def _generic_parts(q):
    """-> [part1, part2] (student's own words, preamble bound
    into both) or None."""
    if len(q) > 320 or _LABELLED.search(q):
        return None
    # Sentence segments; a leading data preamble (no ask
    # signal) binds into every part, J9-style.
    segments = [s.strip() for s in
                re.split(r"(?<=[.?!।])\s+", q) if s.strip()]
    if not segments:
        return None
    preamble = []
    ask_segs = []
    for seg in segments:
        if _seg_has_ask(seg):
            ask_segs.append(seg)
        elif not ask_segs:
            preamble.append(seg)
        else:
            return None  # data after an ask — not this shape
    pre = (" ".join(preamble) + " ") if preamble else ""

    def bound(seg):
        # A discourse opener ("Also find ...", "Phir ...")
        # is not maths: left in, the expression parser reads
        # "Also" as a*l*s*o letter-soup (the Wave 77 family).
        seg = re.sub(r"^(?:also|then|now|phir|uske\s+baad|"
                     r"aur\s+phir)[\s,]+", "", seg.strip(),
                     flags=re.I)
        text = (pre + seg).strip()
        return text if text.endswith((".", "?", "।")) \
            else text + "?"

    if len(ask_segs) == 2 and len(segments) <= 3:
        return [bound(ask_segs[0]), bound(ask_segs[1])]
    if len(ask_segs) != 1:
        return None
    seg = ask_segs[0]
    # Semicolon candidates, then aur/and candidates (J9 order).
    for sep in (";",):
        if sep in seg:
            left, _, right = seg.partition(sep)
            if _seg_has_ask(left) \
                    and _seg_has_ask(right):
                return [bound(left.strip()),
                        bound(right.strip())]
    for m in re.finditer(r"\s+(?:and|aur|तथा|एवं|और)\s+",
                         seg, re.I):
        left, right = seg[:m.start()], seg[m.end():]
        if len(left) < 8 or len(right) < 4:
            continue
        if _seg_has_ask(left) \
                and _seg_has_ask(right):
            return [bound(left.strip()), bound(right.strip())]
    return None


# ---------------------------------------------------------------------------
# Family 5 (Wave 227) — OCR-doubled multi-part calculus
# questions (Suraj's screenshot case 5, 27 Nov 2026):
#
#     "Check the continuity of a function at x = 0 x=0.
#      Differentiate y = x 2 sin x y=x2 sinx."
#         -> the canned "I didn't understand"
#
# Three stacked mechanisms, each fixed at its own root:
#
#  1. OCR DOUBLING.  The photo/OCR layer often emits a
#     fragment twice — once spaced ("x = 0", "y = x 2 sin
#     x"), once glued ("x=0", "y=x2 sinx").  No solver can
#     read the doubled text.  _dedup_ocr_restatements drops
#     a tail fragment whose glued form restates the glued
#     tail of what precedes it.
#  2. OCR POWER SPELLING.  The surviving spaced rendering
#     writes x^2 as "x 2" (and the glued one as "x2"); the
#     expression parser reads "x 2 sin x" as 2x·sin x and
#     answers a DIFFERENT question.  In a differentiate /
#     integrate part, a variable followed by a bare digit
#     directly before a trig/log function is the power
#     spelling, and is repaired to x^2 before solving.
#  3. A GENUINELY INCOMPLETE PART.  "Check the continuity
#     of a function at x = 0" names no function — there is
#     nothing to check, and the honest answer for THAT part
#     is a plain note saying exactly what is missing (the
#     standing rule for wrong/incomplete questions), while
#     the complete part is still solved.  The old flow
#     demanded every part solve, so one incomplete part
#     sank the whole question into the canned line.
#
# The gate stays strict: at least two parts, EVERY part a
# calculus ask (continuity / differentiate / integrate /
# limit / dy/dx), every part either solved for real or the
# incomplete-continuity shape, and at least one part really
# solved.  Any doubt -> None, and the older families and
# flows decide exactly as before.
# ---------------------------------------------------------------------------

_CALC_ASK = re.compile(
    r"continuit|differentiat|derivative|integrat|"
    r"dy\s*/\s*dx|\blimit\b", re.I)

_OCR_POWER_SPACED = re.compile(
    r"\b([a-zA-Z])\s+(\d+)\s+"
    r"(?=(?:sin|cos|tan|sec|csc|cot|log|ln)\b)")
_OCR_POWER_GLUED = re.compile(
    r"\b([a-zA-Z])(\d+)\s+"
    r"(?=(?:sin|cos|tan|sec|csc|cot|log|ln)\b)")

_FUNCTION_GIVEN = re.compile(
    r"f\s*\(\s*x\s*\)\s*=|function\s+is\b|=\s*\{|"
    r"continuit\w*\s+of\s+(?:the\s+)?"
    r"(?:sin|cos|tan|sec|csc|cot|log|ln|e\^|x\^|\d|"
    r"f\s*\()", re.I)


def _glued(text):
    return re.sub(r"\s+", "", str(text)).lower()


def _dedup_ocr_restatements(text):
    """Drop OCR's doubled rendering of a fragment: a tail
    whose space-stripped form restates the space-stripped
    tail of what precedes it ("... at x = 0 x=0" -> "... at
    x = 0"; "... y = x 2 sin x y=x2 sinx" -> "... y = x 2
    sin x").  Only a fragment carrying '=' or a digit can
    be dropped, and only inside one sentence segment."""
    segments = re.split(r"(?<=[.?!।])\s+", str(text))
    out = []
    for seg in segments:
        tokens = seg.split(" ")
        for i in range(len(tokens) - 1, 0, -1):
            right = " ".join(tokens[i:])
            # The sentence's final punctuation rides on the
            # dropped fragment; it is punctuation, not part
            # of the restatement, and the kept text needs it
            # back (the parts are re-split on it downstream).
            punct = re.search(r"[.?!।]+$", right)
            glued_right = _glued(
                right[:punct.start()] if punct else right)
            if len(glued_right) < 3:
                continue
            if "=" not in right and not any(
                    ch.isdigit() for ch in right):
                continue
            left = " ".join(tokens[:i])
            if _glued(left).endswith(glued_right):
                seg = left + (punct.group(0) if punct
                              else "")
                break
        out.append(seg)
    return " ".join(out)


def _repair_ocr_powers(part):
    """The OCR power spelling in a calculus part: 'x 2 sin
    x' / 'x2 sin x' -> 'x^2 sin x' (see the family note)."""
    part = _OCR_POWER_SPACED.sub(r"\1^\2 ", part)
    part = _OCR_POWER_GLUED.sub(r"\1^\2 ", part)
    return part


def _continuity_missing_function(part):
    """A continuity ask that names no function is genuinely
    incomplete — there is nothing whose continuity could be
    checked.  Returns the point string (or "" when no point
    is named either), or None when this is not that shape
    (no continuity ask, or a function IS given)."""
    if not re.search(r"continuit", part, re.I):
        return None
    if _FUNCTION_GIVEN.search(part):
        return None
    m = re.search(r"at\s+x\s*=\s*(-?\d+(?:\.\d+)?)", part)
    return m.group(1) if m else ""


def _incomplete_continuity_result(point):
    """The plain, specific note for the incomplete part:
    what is missing, why it is needed, and what to send —
    never the canned line."""
    where = f" at x = {point}" if point else ""
    note = (
        "The function itself is not given in this part — "
        f"only the point{where}. Continuity can only be "
        "checked when the function is known (for example "
        "f(x) = x^2 + 1), so this part cannot be checked "
        "yet. Send the function and I will check it right "
        "away.")
    return {"answer": "Function not given — continuity "
                      "cannot be checked",
            "steps": [note]}


def _ocr_calculus_result(q):
    """The finished Wave 227 result, or None (see the
    family note above for the strict gate)."""
    if len(q) > 600:
        return None
    deduped = _dedup_ocr_restatements(q)
    segments = [s.strip() for s in
                re.split(r"(?<=[.?!।])\s+", deduped)
                if s.strip()]
    if len(segments) < 2:
        return None
    if not all(_CALC_ASK.search(s) for s in segments):
        return None
    from .router import solve_question
    results = []
    solved_any = False
    for seg in segments:
        point = _continuity_missing_function(seg)
        if point is not None:
            results.append(
                _incomplete_continuity_result(point))
            continue
        try:
            result = solve_question(_repair_ocr_powers(seg))
        except Exception:
            return None
        if not _is_solved(result):
            return None
        solved_any = True
        results.append(result)
    if not solved_any:
        return None
    return _assemble("multipart227", results, segments)


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------

def split_parts(text):
    """DeepSeek Job 9 contract: {"parts": [...]} when two
    separate asks exist, else None."""
    if not text:
        return None
    q = str(text).strip()
    fam = _mensuration_parts(q) or _sum_parts(q)
    if fam is not None:
        return {"parts": fam[0]}
    if _money_result(q) is not None:
        return {"parts": ["total cost", "change"]}
    parts = _generic_parts(q)
    if parts:
        return {"parts": parts}
    return None


def _dependent_parts(parts):
    """A later part that leans on an earlier part's RESULT
    (a 'Hence' chain in disguise) is not an independent ask:
    'Find the value of x in 2x + 3 = 7. Also find the value
    of 3x + 1.' — part 2 needs part 1's x, and solved alone
    it echoes '3*x + 1'.  Those chains belong to Wave 100;
    the generic split declines them."""
    if len(parts) < 2:
        return False
    solved_for = set()
    for part in parts[:-1]:
        for m in re.finditer(
                r"\bvalue\s+of\s+([a-z])\b|\bfind\s+([a-z])\s*"
                r"(?:=|in\b|when\b)", part, re.I):
            solved_for.add((m.group(1) or m.group(2)).lower())
    for part in parts[1:]:
        pl = part.lower()
        if re.search(r"\bits\s+value\b|\bthis\s+value\b|"
                     r"\bthese\s+values\b|\bthe\s+obtained\b|"
                     r"\bso\s+obtained\b", pl):
            return True
        for var in solved_for:
            if re.search(r"(?:\d\s*" + var + r"\b|\b" + var +
                         r"\s*(?:[+\-*/=]|\*\*|\^))", pl):
                return True
    return False


def _solve_parts(parts, expected_ops_list=None):
    """Solve every part through the ordinary pipeline; ALL
    must solve, and (where the family knows the ask) each
    part's op must be that ask's op."""
    from .router import solve_question
    solved = []
    for i, part in enumerate(parts):
        try:
            result = solve_question(part)
        except Exception:
            return None
        if not _is_solved(result):
            return None
        if expected_ops_list is not None \
                and result.get("op") not in expected_ops_list[i]:
            return None
        solved.append(result)
    return solved


def solve_multipart223(question):
    """The router gate: a verified two-ask result, or None
    (the pre-Wave-223 flow then decides, byte-identical)."""
    if getattr(_ACTIVE, "on", False):
        return None
    if not question:
        return None
    q = str(question).strip()
    _ACTIVE.on = True
    try:
        money = _money_result(q)
        if money is not None:
            return money
        fam = _mensuration_parts(q) or _sum_parts(q)
        if fam is not None:
            parts, expected = fam
            solved = _solve_parts(parts, expected)
            if solved is not None:
                return _assemble("multipart223", solved, parts)
            return None
        # Wave 227: the OCR-doubled calculus family — it
        # must run before the generic family, whose ask
        # signals never knew "check"/"differentiate" and
        # which demands every part solve (an incomplete
        # part sank the whole question, screenshot case 5).
        ocr_calc = _ocr_calculus_result(q)
        if ocr_calc is not None:
            return ocr_calc
        parts = _generic_parts(q)
        if parts and not _dependent_parts(parts):
            solved = _solve_parts(parts)
            if solved is not None:
                # The generic family has no op pin, so it
                # needs the letter-soup veto itself: a part
                # "answered" as unresolved letter products
                # (3*A*l*s*o*x + 1 — the Wave 77/207 junk
                # shape) is not an answer, and a dependent
                # part ("also find 3x + 1" after x was solved)
                # declines with it, exactly as pre-Wave-223.
                soup = any(
                    re.search(r"[A-Za-z]\s*\*\s*[A-Za-z]",
                              str(r.get("answer") or ""))
                    or "Mod(" in str(r.get("answer") or "")
                    for r in solved)
                keys = [(r.get("op"), str(r.get("answer")))
                        for r in solved]
                if not soup and len(set(keys)) == len(keys):
                    return _assemble("multipart223", solved,
                                     parts)
        return None
    finally:
        _ACTIVE.on = False
