"""Statistics & probability.

Descriptive stats (mean, median, mode, variance, standard deviation,
range), permutations, combinations, factorials, and basic probability
(dice, coins, balls in a bag, a pack of cards, binomial trials).
"""
import re
from fractions import Fraction
from itertools import product as _iproduct

import sympy as sp

from .expression_parser import fmt_num

# ------------------------------------------------------------ descriptive
def _extract_list(question: str):
    m = re.search(r"\[([^\]]+)\]", question)
    text = m.group(1) if m else question
    nums = []
    for tok in re.finditer(r"-?\d+(?:\.\d+)?", text):
        s = tok.group(0)
        nums.append(float(s) if "." in s else int(s))
    return nums


def _mean(nums):
    return sum(nums) / len(nums)


def _median(nums):
    s = sorted(nums)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _mode(nums):
    counts = {}
    for v in nums:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    return sorted(v for v, c in counts.items() if c == top)


def _variance(nums, sample=False):
    mu = _mean(nums)
    n = len(nums) - (1 if sample else 0)
    return sum((v - mu) ** 2 for v in nums) / n


def _stats_result(op, nums):
    if len(nums) < 2:
        return None
    listed = ", ".join(fmt_num(v) for v in nums)
    if op == "mean":
        steps = [
            f"Add all values: {' + '.join(fmt_num(v) for v in nums)} "
            f"= {fmt_num(sum(nums))}",
            f"Divide by the count ({len(nums)}): {fmt_num(sum(nums))} ÷ "
            f"{len(nums)} = {fmt_num(_mean(nums))}",
        ]
        return _mean(nums), steps
    if op == "median":
        s = sorted(nums)
        steps = [
            f"Arrange in order: {', '.join(fmt_num(v) for v in s)}",
            "Take the middle value"
            + (" (average of the two middle values)." if len(s) % 2 == 0
               else "."),
            f"Median = {fmt_num(_median(nums))}",
        ]
        return _median(nums), steps
    if op == "mode":
        modes = _mode(nums)
        steps = [
            f"Count how often each value appears in: {listed}",
            "The most frequent value(s): "
            + ", ".join(fmt_num(v) for v in modes),
        ]
        return (modes[0] if len(modes) == 1 else modes), steps
    if op in ("variance", "std"):
        mu = _mean(nums)
        var = _variance(nums)
        steps = [
            f"Mean x̄ = {fmt_num(mu)}",
            "Squared deviations (x - x̄)^2: "
            + ", ".join(fmt_num((v - mu) ** 2) for v in nums),
            f"Variance = average of squared deviations = {fmt_num(var)}",
        ]
        if op == "std":
            steps.append(f"Standard deviation = sqrt({fmt_num(var)}) "
                         f"= {fmt_num(var ** 0.5)}")
            return var ** 0.5, steps
        return var, steps
    if op == "range":
        steps = [
            f"Largest value = {fmt_num(max(nums))}, smallest = "
            f"{fmt_num(min(nums))}",
            f"Range = {fmt_num(max(nums))} - {fmt_num(min(nums))} "
            f"= {fmt_num(max(nums) - min(nums))}",
        ]
        return max(nums) - min(nums), steps
    return None


# ------------------------------------------------------------ probability
# Wave 33: Hindi / Hinglish probability. NCERT Hindi-medium
# Class 10 asks ("दो सिक्के उछाले जाते हैं… प्रायिकता") had NO
# patterns anywhere: the router never sent them to statistics
# and this solver only understood the English words, so they
# fell through to the arithmetic simplifier, which returned
# Devanagari letter-soup. The block below parses the standard
# experiment set — coins (चित/पट = head/tail), dice (पासा),
# cards (पत्ते) and balls (गेंदें) — in Devanagari and Roman
# Hinglish, and answers through the SAME enumeration /
# counting as the English paths. Steps stay English, as
# everywhere in the solver.
_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_HI_NUM_WORDS = {"एक": 1, "दो": 2, "तीन": 3, "चार": 4,
                 "पाँच": 5, "पांच": 5, "छह": 6,
                 "ek": 1, "do": 2, "teen": 3, "char": 4,
                 "chaar": 4, "panch": 5, "paanch": 5}
_HI_NUM = (r"(?:एक|दो|तीन|चार|पाँच|पांच|छह|\d+|\bek\b|"
           r"\bdo\b|\bteen\b|\bchaar\b|\bchar\b|\bpaanch\b|"
           r"\bpanch\b)")
_HI_FACE = r"(चित|पट|chit|pat|puchh|heads?|tails?)"


def _hi_num(tok):
    tok = tok.strip()
    if tok.isdigit():
        return int(tok)
    return _HI_NUM_WORDS.get(tok)


def _hi_face_is_heads(tok):
    return tok.startswith(("चि", "ch", "he"))


def _hindi_coin(qn):
    """(n_coins, test(heads, n), label) from a Hindi/Hinglish
    coin question, or None."""
    if not re.search(r"सिक्क|sikk", qn):
        return None
    n = None
    m = re.search(_HI_NUM + r"\s*(?:सिक्के?|सिक्कों|sikke|"
                  r"sikka)", qn)
    if m:
        n = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
    if n is None and re.search(r"दोनों\s+सिक्क", qn):
        n = 2
    if n is None:
        # "ek sikka do baar uchhala" — one coin, tossed n times
        m = re.search(_HI_NUM + r"\s*(?:बार|baar)\b", qn)
        if m:
            n = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
    if n is None:
        n = 1
    if not (1 <= n <= 5):
        return None
    # No head / no tail at all ("कोई चित न आने…")
    if re.search(r"कोई|एक\s+भी|\bkoi\b|\bek\s+bhi\b", qn) and \
            re.search(r"नहीं|नही|(?:^|\s)न(?:\s|$)|\bnahi\b",
                      qn):
        if re.search(r"पट|\bpat\b|\btail", qn):
            return n, (lambda h, nn: h == nn), "no tail"
        return n, (lambda h, nn: h == 0), "no head"
    # Both / all of a face ("दोनों पट", "sabhi chit",
    # "teeno chit" — Wave 57: तीनों/teeno was missing and
    # three-coin all-heads asks fell through entirely)
    if re.search(r"दोनों|\bdono\b|तीनों|तीनो|\bteeno\b|\btino\b|"
                 r"सभी|\bsabhi\b", qn):
        m = re.search(_HI_FACE, qn)
        if m:
            if _hi_face_is_heads(m.group(1)):
                return n, (lambda h, nn: h == nn), "all heads"
            return n, (lambda h, nn: h == 0), "all tails"
    # Quantified events: at least / at most / exactly k of a
    # face. The count may be omitted after "kam se kam" (= 1).
    quants = [
        (r"कम\s+से\s+कम|kam\s+se\s+kam", "at least",
         lambda c, k: c >= k),
        (r"अधिक\s+से\s+अधिक|अधिकतम|adhik\s+se\s+adhik|"
         r"adhiktam", "at most", lambda c, k: c <= k),
        (r"ठीक|theek|केवल|keval", "exactly",
         lambda c, k: c == k),
    ]
    for pat, word, fn in quants:
        m = re.search(r"(?:" + pat + r")\s+(?:(" + _HI_NUM +
                      r")\s+)?" + _HI_FACE, qn)
        if m:
            k = _hi_num(m.group(1)) if m.group(1) else 1
            heads = _hi_face_is_heads(m.group(2))
            face = "head" if heads else "tail"
            test = (lambda c, nn, k=k, fn=fn: fn(c, k)) if heads \
                else (lambda c, nn, k=k, fn=fn: fn(nn - c, k))
            label = (f"{word} {k} {face}" if k != 1
                     else f"{word} one {face}")
            return n, test, label
    # Bare count + face ("दो चित") means exactly that many.
    m = re.search(_HI_NUM + r"\s+" + _HI_FACE, qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        heads = _hi_face_is_heads(m.group(1))
        face = "head" if heads else "tail"
        test = (lambda c, nn, k=k: c == k) if heads else \
            (lambda c, nn, k=k: nn - c == k)
        return n, test, f"exactly {k} {face}" + ("s" if k != 1
                                                 else "")
    # A single coin and a bare face ("चित आने की प्रायिकता").
    if n == 1:
        m = re.search(_HI_FACE, qn)
        if m:
            if _hi_face_is_heads(m.group(1)):
                return n, (lambda c, nn: c == 1), "one head"
            return n, (lambda c, nn: c == 0), "one tail"
    return None


def _hindi_dice_faces(qn):
    """(favourable faces, label) for a single-die Hindi /
    Hinglish event, or None."""
    m = re.search(_HI_NUM + r"\s*(?:से|\bse\b)\s*(?:बड़ी|बड़ा|"
                  r"अधिक|badi|bada|adhik)\s*"
                  r"(?:संख्या|sankhya|number)?", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        return [f for f in range(1, 7) if f > k], \
            f"a number greater than {k}"
    m = re.search(_HI_NUM + r"\s*(?:से|\bse\b)\s*(?:छोटी|छोटा|"
                  r"कम|chhoti|chhota|kam)\s*"
                  r"(?:संख्या|sankhya|number)?", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        return [f for f in range(1, 7) if f < k], \
            f"a number less than {k}"
    if re.search(r"सम\s*(?:संख्या|sankhya)|\bsama?\s+sankhya\b|"
                 r"\beven\b", qn):
        return [2, 4, 6], "an even number"
    if re.search(r"विषम\s*(?:संख्या|sankhya)|visham\s+sankhya|"
                 r"\bodd\b", qn):
        return [1, 3, 5], "an odd number"
    if re.search(r"अभाज्य|abhajya|\bprime\b", qn):
        return [2, 3, 5], "a prime number"
    if re.search(r"संयुक्त|sanyukt|\bcomposite\b", qn):
        return [4, 6], "a composite number"
    if re.search(r"पूर्ण\s*वर्ग|perfect\s+square", qn):
        return [1, 4], "a perfect square"
    m = re.search(_HI_NUM + r"\s*(?:का|की|ke|ka)\s*"
                  r"(?:गुणज|अपवर्त्य|multiple)", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        if k:
            return [f for f in range(1, 7) if f % k == 0], \
                f"a multiple of {k}"
    m = re.search(_HI_NUM + r"\s*(?:अंक\s*)?(?:आने|प्राप्त|"
                  r"aane)", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        if k and 1 <= k <= 6:
            return [k], f"the number {k}"
    nums = {int(t) for t in re.findall(r"\d+", qn)
            if 1 <= int(t) <= 6}
    if len(nums) == 1:
        k = nums.pop()
        return [k], f"the number {k}"
    return None


# Colour stems for Hindi balls/cards. The Devanagari stem
# must not start mid-word: काल (black) occurs inside
# निकाली ("drawn") — the commonest verb in these questions
# — and हर inside शहर. A negative lookbehind for any
# Devanagari character forces a real word start.
_DNB = r"(?<![ऀ-ॿ])"
_HI_COLOURS = [
    (_DNB + r"लाल|\blaal\b", "red"), (_DNB + r"नील|\bneel", "blue"),
    (_DNB + r"हर[ाी]|\bhara\b|\bhari\b", "green"),
    (_DNB + r"पील|\bpeel", "yellow"), (_DNB + r"काल|\bkaal", "black"),
    (_DNB + r"सफेद|\bsafed\b", "white"), (_DNB + r"गुलाबी", "pink"),
    (_DNB + r"नारंगी", "orange"), (_DNB + r"बैंगनी", "purple"),
    (_DNB + r"भूर", "brown"),
]


def _probability_hindi(q, ql):
    qn = ql.translate(_DEV_DIGITS)
    # --- coins ---
    got = _hindi_coin(qn)
    if got is not None:
        n, test, label = got
        outcomes = list(_iproduct("HT", repeat=n))
        fav = sum(1 for o in outcomes if test(o.count("H"), n))
        steps = [
            f"{n} coin(s) tossed together give 2^{n} = "
            f"{2 ** n} equally likely outcomes: "
            + ", ".join("".join(o) for o in outcomes),
            f"Favourable outcomes ({label}) = {fav}",
        ]
        return _prob_answer(Fraction(fav, 2 ** n), steps)
    # --- dice ---
    # Wave 56: the Roman gate was "pasa|paase" — the common
    # spelling "paasa" (double a) matched NEITHER and the
    # whole Hindi dice path was skipped (battery #496).
    # Hinglish spelling variants (doubled vowels, an extra
    # nasal) are folded into the pattern itself: pa + s
    # with any vowel tail covers pasa / paasa / paase /
    # paansa.
    if re.search(r"पास|pa+n?s\w*", qn):
        two = re.search(r"(?:दो|\bdo\b|\b2\b)\s*(?:पासे|पासों|"
                        r"pa+n?s\w*|dice)", qn) or \
            "दोनों पास" in qn
        if two:
            if re.search(r"समान\s*संख्या|बराबर\s*संख्या|"
                         r"doublet|same\s+number", qn):
                steps = [
                    "Two dice give 6 × 6 = 36 equally likely "
                    "outcomes.",
                    "Outcomes with the same number on both "
                    "dice (doublets): 6",
                ]
                return _prob_answer(Fraction(6, 36), steps)
            m = re.search(r"(?:योग|yog|sum)\s*(?:का\s*)?" +
                          _HI_NUM, qn) or re.search(
                              _HI_NUM + r"\s*(?:का\s*)?"
                              r"(?:योग|yog)", qn)
            if m:
                km = re.search(_HI_NUM, m.group(0))
                target = _hi_num(km.group(0))
                if target and 2 <= target <= 12:
                    fav = sum(1 for a, b in
                              _iproduct(range(1, 7), repeat=2)
                              if a + b == target)
                    steps = [
                        "Two dice give 6 × 6 = 36 equally "
                        "likely outcomes.",
                        f"Outcomes with sum {target}: {fav}",
                    ]
                    return _prob_answer(Fraction(fav, 36),
                                        steps)
            return None
        faces = _hindi_dice_faces(qn)
        if faces is not None:
            fav_faces, label = faces
            steps = [
                "A fair die has 6 equally likely faces (1-6).",
                f"Favourable outcomes ({label}): "
                + ", ".join(str(f) for f in fav_faces)
                + f" — {len(fav_faces)} of them",
            ]
            return _prob_answer(Fraction(len(fav_faces), 6),
                                steps)
        return None
    # --- cards ---
    if re.search(r"पत्त|ताश|taash", qn) and \
            ("52" in qn or "गड्डी" in qn or "pack" in qn
             or "deck" in qn):
        # Wave 156 (Wave 153 audit bank-120): a SPECIFIC card
        # — a rank named together with a suit ('पान का राजा',
        # King of Hearts) — is exactly ONE card in the pack.
        # The suit/rank table below matches the suit alone
        # first (पान → 13 hearts → 1/4), which is the wrong
        # quantity for a specific-card ask; the pair check
        # must run before the table.
        _rank = re.search(r"इक्का|बादशाह|राजा|बेगम|रानी|गुलाम|"
                          r"\bikka\b|\bking\b|\bqueen\b|\bjack\b|"
                          r"\bace\b", qn)
        _suit = re.search(r"हुकुम|पान|ईंट|चिड़ी|\bhukum\b|"
                          r"\bhearts?\b|\bdiamonds?\b|"
                          r"\bspades?\b|\bclubs?\b", qn)
        if _rank and _suit:
            steps = [
                "A standard pack has 52 cards.",
                "The named rank-and-suit card is exactly 1 "
                "specific card in the pack.",
            ]
            return _prob_answer(Fraction(1, 52), steps)
        table = [
            (_DNB + r"इक्का|\bikka\b", 4, "aces"),
            (_DNB + r"बादशाह|badshah", 4, "kings"),
            (_DNB + r"बेगम|begum", 4, "queens"),
            (_DNB + r"गुलाम|gulam", 4, "jacks"),
            (_DNB + r"फेस\s*कार्ड|तस्वीर", 12, "face cards"),
            (_DNB + r"हुकुम|hukum", 13, "spades"),
            (_DNB + r"पान", 13, "hearts"),
            (_DNB + r"ईंट", 13, "diamonds"),
            (_DNB + r"चिड़ी", 13, "clubs"),
            (_DNB + r"लाल|\blaal\b", 26, "red cards"),
            (_DNB + r"काल|\bkaal", 26, "black cards"),
        ]
        for pat, cnt, label in table:
            if re.search(pat, qn):
                steps = [
                    "A standard pack has 52 cards.",
                    f"Number of {label} = {cnt}",
                ]
                return _prob_answer(Fraction(cnt, 52), steps)
        return None
    # --- balls in a bag ---
    if "गेंद" in qn or re.search(r"\bgend\b", qn):
        counts = {}
        for pat, colour in _HI_COLOURS:
            c = 0
            for m in re.finditer(r"(\d+)\s*(?:रंग\s+की\s+)?"
                                 r"(?:" + pat + r")", qn):
                c += int(m.group(1))
            for m in re.finditer(r"(?:" + pat + r")\s*"
                                 r"(?:रंग\s+की\s+)?(\d+)\s*"
                                 r"गेंद", qn):
                c += int(m.group(1))
            # Wave 42: colour-first order — "नीली गेंदें 3
            # हैं" (the count AFTER गेंदें). Neither loop
            # above sees it, so a bag stated this way yielded
            # no counts at all and fell to a fallback. The
            # [^0-9\s]* eats the colour word's own tail (the
            # ी of नीली) without crossing a space, and the
            # compulsory गेंदें keeps it from double-counting
            # the "4 लाल गेंदें" (count-first) forms.
            for m in re.finditer(r"(?:" + pat + r")"
                                 r"[^0-9\s]*\s*"
                                 r"(?:रंग\s+की\s+)?गेंदें?\s*"
                                 r"(\d+)", qn):
                c += int(m.group(1))
            if c:
                counts[colour] = c
        # Target = the LAST colour mention in text order
        # that carries no count and exists among the counts.
        _mentions = []
        for pat, colour in _HI_COLOURS:
            for m in re.finditer(pat, qn):
                before = qn[max(0, m.start() - 3):m.start()]
                after = qn[m.end():m.end() + 3]
                if re.search(r"\d\s*$", before) or \
                        re.search(r"^\s*\d", after):
                    continue  # this mention carries the count
                _mentions.append((m.start(), colour))
        target = None
        for _pos, colour in sorted(_mentions, reverse=True):
            if colour in counts:
                target = colour
                break
        if counts and target in counts:
            total = sum(counts.values())
            steps = [
                "Count the balls: "
                + ", ".join(f"{c} {col}" for col, c
                            in counts.items())
                + f" — total {total}",
                f"Favourable ({target}) = {counts[target]}",
            ]
            return _prob_answer(
                Fraction(counts[target], total), steps)
        return None
    return None


def _prob_answer(frac: Fraction, steps, label="Probability"):
    dec = frac.numerator / frac.denominator
    steps.append(f"{label} = {frac} ≈ {dec:.4f} ({dec * 100:.2f}%)")
    return {
        "type": "statistics",
        "op": "probability",
        "answer": f"{frac} ≈ {dec:.4f}",
        "value": float(dec),
        "steps": steps,
    }


def _probability(q: str):
    ql = q.lower()

    # Wave 33: Hindi / Hinglish asks (Devanagari + Roman) —
    # parsed by the dedicated block; returns None when the
    # question is not one of its experiment forms, in which
    # case the English paths below run exactly as before.
    _hindi = _probability_hindi(q, ql)
    if _hindi is not None:
        return _hindi

    # Wave 156 (Wave 153 audit book-052): event-probability
    # relations — "P(A) = 0.42, P(B) = 0.48 and P(A and B) =
    # 0.16. Determine (i) P(not A), (ii) P(not B) and
    # (iii) P(A or B)". No schema parsed the stated event
    # values, so the whole family declined. Compute exactly
    # the quantities the text asks for.
    _pa = re.search(r"p\(\s*a\s*\)\s*=\s*(\d+(?:\.\d+)?)", ql)
    _pb = re.search(r"p\(\s*b\s*\)\s*=\s*(\d+(?:\.\d+)?)", ql)
    _pab = re.search(r"p\(\s*a\s*(?:and|∩|cap)\s*b\s*\)\s*=\s*"
                     r"(\d+(?:\.\d+)?)", ql)
    if _pa and _pb:
        _va, _vb = float(_pa.group(1)), float(_pb.group(1))
        _vab = float(_pab.group(1)) if _pab else None
        _rel = []
        _rel_steps = []
        if re.search(r"p\(\s*not\s+a\s*\)", ql):
            _rel.append(f"P(not A) = {fmt_num(1 - _va)}")
            _rel_steps.append(
                f"P(not A) = 1 - P(A) = 1 - {fmt_num(_va)} "
                f"= {fmt_num(1 - _va)}")
        if re.search(r"p\(\s*not\s+b\s*\)", ql):
            _rel.append(f"P(not B) = {fmt_num(1 - _vb)}")
            _rel_steps.append(
                f"P(not B) = 1 - P(B) = 1 - {fmt_num(_vb)} "
                f"= {fmt_num(1 - _vb)}")
        if re.search(r"p\(\s*a\s*(?:or|∪|cup)\s*b\s*\)", ql) \
                and _vab is not None:
            _rel.append(
                f"P(A or B) = {fmt_num(_va + _vb - _vab)}")
            _rel_steps.append(
                f"P(A or B) = P(A) + P(B) - P(A and B) = "
                f"{fmt_num(_va)} + {fmt_num(_vb)} - "
                f"{fmt_num(_vab)} = "
                f"{fmt_num(_va + _vb - _vab)}")
        if _rel:
            return {"type": "statistics", "op": "probability",
                    "answer": "; ".join(_rel), "value": None,
                    "steps": _rel_steps}

    # Wave 65: card / coin / dice / lottery / bag families in
    # plain phrasings the older patterns missed (they fell
    # to the probability CONCEPT answer). All gated on the
    # experiment's own words. Union ("or") and complement
    # ("not") asks stay with the older general machinery
    # below — this block answers only the single-event forms.
    if ("probability" in ql or "chance" in ql) \
            and not re.search(r"\bnot\b|\bor\b", ql):
        # --- cards from a 52 pack --------------------------
        if re.search(r"\b52\b", ql) and ("card" in ql
                                        or "pack" in ql
                                        or "deck" in ql):
            _specific = re.search(
                r"\b(king|queen|jack|ace)\s+of\s+"
                r"(hearts|diamonds|spades|clubs)\b", ql)
            if _specific:
                return _prob_answer(Fraction(1, 52), [
                    f"There is exactly one {_specific.group(1)}"
                    f" of {_specific.group(2)} in a pack of "
                    f"52 cards"])
            _combo = re.search(
                r"\b(red|black)\s+(king|queen|jack|ace)\b", ql)
            if _combo:
                return _prob_answer(Fraction(2, 52), [
                    f"There are exactly 2 {_combo.group(1)} "
                    f"{_combo.group(2)}s in a pack of 52 "
                    f"cards"])
            if "face card" in ql:
                return _prob_answer(Fraction(12, 52), [
                    "A pack has 12 face cards (4 jacks, 4 "
                    "queens, 4 kings) out of 52"])
            for _face, _nm in (("king", "kings"),
                               ("queen", "queens"),
                               ("jack", "jacks"),
                               ("ace", "aces")):
                if re.search(r"\b" + _face + r"\b", ql):
                    return _prob_answer(Fraction(4, 52), [
                        f"A pack of 52 cards has 4 {_nm}"])
            if "black card" in ql:
                return _prob_answer(Fraction(26, 52), [
                    "26 of the 52 cards are black (spades "
                    "and clubs)"])
            if "red card" in ql:
                return _prob_answer(Fraction(26, 52), [
                    "26 of the 52 cards are red (hearts and "
                    "diamonds)"])
        # --- coins: all heads / no heads -------------------
        _cn = re.search(r"(\d+)\s+(?:coins?|times)", ql)
        if ("coin" in ql or "toss" in ql) and _cn:
            _n = int(_cn.group(1))
            if 1 <= _n <= 10 and ("all head" in ql
                                  or "every time head" in ql
                                  or re.search(
                                      r"all\s+(?:\d+\s+)?heads",
                                      ql)):
                return _prob_answer(Fraction(1, 2 ** _n), [
                    f"Each toss is independent with P(head) "
                    f"= 1/2, so P(all {_n} heads) = "
                    f"(1/2)^{_n}"])
            if 1 <= _n <= 10 and ("no head" in ql
                                  or "not a single head" in ql
                                  or "ek bhi" in ql):
                return _prob_answer(Fraction(1, 2 ** _n), [
                    f"No head means all tails: "
                    f"(1/2)^{_n}"])
        # --- a die rolled twice, both the same face --------
        if ("die" in ql or "dice" in ql) and "twice" in ql:
            _db = re.search(r"both\s+(?:show\s+|are\s+)?"
                            r"(\d)", ql)
            if _db:
                return _prob_answer(Fraction(1, 36), [
                    "Two rolls give 36 equally likely "
                    "outcomes; only one of them is "
                    f"({_db.group(1)}, {_db.group(1)})"])
        # --- lottery ----------------------------------------
        _lot = re.search(r"(\d+)\s+tickets?[^.]{0,50}?"
                         r"(\d+)\s+prizes?", ql)
        if _lot and "lottery" in ql:
            _tk, _pz = int(_lot.group(1)), int(_lot.group(2))
            if _tk >= 1:
                return _prob_answer(Fraction(_pz, _tk), [
                    f"Favourable tickets = {_pz} prizes out "
                    f"of {_tk} tickets"])
        # --- bag of named colours ---------------------------
        _colours = ("red|blue|green|yellow|black|white|"
                    "orange|pink|purple|brown")
        _pairs = re.findall(
            r"(\d+)\s+(" + _colours + r")\s*(?:balls?|"
            r"marbles?|pens?|beads?|counters?)?", ql)
        if len(_pairs) >= 2 and ("bag" in ql or "box" in ql
                                 or "urn" in ql):
            _counts = {}
            for _n, _c in _pairs:
                _counts[_c] = _counts.get(_c, 0) + int(_n)
            _total = sum(_counts.values())
            _ask = re.search(
                r"(?:probability of|getting|drawing|picking|"
                r"drawn|picked)\s+(?:a\s+|an\s+|the\s+)?("
                + _colours + r")", ql)
            if _ask and _ask.group(1) in _counts:
                _c = _ask.group(1)
                return _prob_answer(
                    Fraction(_counts[_c], _total), [
                        f"Total = {_total}; {_c} count = "
                        f"{_counts[_c]}"])
        _sub = re.search(
            r"(\d+)\s+(?:balls?|marbles?|pens?)\b[^.]{0,60}?"
            r"(\d+)\s+(?:of\s+(?:them|which)\s+)?(?:are\s+)?("
            + _colours + r")", ql)
        if _sub and ("bag" in ql or "box" in ql):
            _total, _cnt, _c = (int(_sub.group(1)),
                                int(_sub.group(2)),
                                _sub.group(3))
            if _total >= 1:
                return _prob_answer(Fraction(_cnt, _total), [
                    f"Total = {_total}; {_c} count = {_cnt}"])

    # Wave 59: "a number is chosen from 1 to N, find the
    # probability that it is a multiple of K / divisible by K".
    _mch = re.search(r"from\s+1\s+to\s+(\d+)", ql)
    _mk = re.search(r"multiple\s+of\s+(\d+)", ql) or \
        re.search(r"divisible\s+by\s+(\d+)", ql)
    if _mch and _mk and "probability" in ql:
        _n = int(_mch.group(1))
        _k = int(_mk.group(1))
        if _n >= 1 and _k >= 1:
            _cnt = _n // _k
            return _prob_answer(Fraction(_cnt, _n), [
                f"Total outcomes = {_n} (numbers 1 to {_n})",
                f"Favourable outcomes = {_cnt} (every "
                f"{_k}th number)",
            ])

    # Wave 58: the abstract union formula — "P(A) = 0.3 and
    # P(B) = 0.4, A and B mutually exclusive, find P(A or B)"
    # and the general form with P(A and B) given. Formula-
    # style questions like this parsed as letter equations
    # everywhere else (Wave 55 trap); here they are answered
    # by the addition rule itself, and only when the result
    # is a valid probability.
    if "p(a)" in ql and "p(b)" in ql:
        def _pval(pat):
            _m = re.search(pat, ql)
            return Fraction(_m.group(1)) if _m else None
        _pa = _pval(r"p\(\s*a\s*\)\s*=\s*(\d+(?:\.\d+)?)")
        _pb = _pval(r"p\(\s*b\s*\)\s*=\s*(\d+(?:\.\d+)?)")
        _pab = _pval(r"p\(\s*a\s*(?:and|∩|cap)\s*b\s*\)\s*"
                     r"=\s*(\d+(?:\.\d+)?)")
        _por = _pval(r"p\(\s*a\s*(?:or|union|∪)\s*b\s*\)\s*"
                     r"=\s*(\d+(?:\.\d+)?)")
        _ask_or = re.search(r"find\s+p\(\s*a\s*(?:or|union|∪)"
                            r"\s*b\s*\)", ql)
        _ask_and = re.search(r"find\s+p\(\s*a\s*(?:and|∩|cap)"
                             r"\s*b\s*\)", ql)
        if _pa is not None and _pb is not None:
            if _ask_or:
                if "mutually exclusive" in ql:
                    _pab = Fraction(0)
                if _pab is not None:
                    _res = _pa + _pb - _pab
                    if 0 <= _res <= 1:
                        steps = [
                            "Addition rule: P(A or B) = "
                            "P(A) + P(B) - P(A and B)",
                            f"= {fmt_num(_pa)} + "
                            f"{fmt_num(_pb)} - "
                            f"{fmt_num(_pab)} "
                            f"= {fmt_num(_res)}",
                        ]
                        return _prob_answer(_res, steps)
            if _ask_and and _por is not None:
                _res = _pa + _pb - _por
                if 0 <= _res <= 1:
                    steps = [
                        "Addition rule rearranged: "
                        "P(A and B) = P(A) + P(B) - P(A or B)",
                        f"= {fmt_num(_pa)} + {fmt_num(_pb)} "
                        f"- {fmt_num(_por)} "
                        f"= {fmt_num(_res)}",
                    ]
                    return _prob_answer(_res, steps)

    # Binomial: exactly k successes in n trials with p
    m = re.search(
        r"exactly\s+(\d+)\s+success\w*\s+in\s+(\d+)\s+trials.*?p\s*=\s*"
        r"(\d+(?:\.\d+)?)",
        ql,
    ) or re.search(r"binomial.*?n\s*=\s*(\d+).*?k\s*=\s*(\d+).*?p\s*=\s*"
                   r"(\d+(?:\.\d+)?)", ql)
    if m:
        if "binomial" in ql:
            n, k, p = int(m.group(1)), int(m.group(2)), float(m.group(3))
        else:
            k, n, p = int(m.group(1)), int(m.group(2)), float(m.group(3))
        from math import comb
        prob = comb(n, k) * p**k * (1 - p) ** (n - k)
        steps = [
            "Binomial formula: P(X = k) = C(n, k) · p^k · (1-p)^(n-k)",
            f"C({n}, {k}) = {comb(n, k)}",
            f"P = {comb(n, k)} · {p}^{k} · {1 - p}^{n - k} = {prob:.4f}",
        ]
        return _prob_answer(Fraction(prob).limit_denominator(10**9), steps)

    # Wave 33: empirical probability — "a coin is tossed 1000
    # times, head appears 450 times" / "a die is rolled 100
    # times, 6 appears 20 times". The theoretical blocks below
    # answered these 1/2 and 1/6 (the bare single-coin / die
    # shortcuts), ignoring the observed counts entirely.
    _mt = re.search(r"(?:tossed|thrown|flipped|rolled)\s+"
                    r"(\d+)\s+times", ql)
    if _mt and ("coin" in ql or "die" in ql or "dice" in ql):
        _total = int(_mt.group(1))
        if "coin" in ql:
            _counts = {}
            for _face in ("head", "tail"):
                _mf = re.search(
                    _face + r"s?\s+(?:appears?|occurs?|comes?|"
                    r"is\s+obtained|obtained)\s+(\d+)\s+times",
                    ql) or re.search(
                        r"(?:obtained|got|getting)\s+(\d+)\s+"
                        + _face, ql)
                if _mf:
                    _counts[_face] = int(_mf.group(1))
            _asked = "tail" if re.search(
                r"probab\w*[^.]*tail|getting\s+an?\s+tail|"
                r"of\s+a\s+tail", ql) else "head"
            if _asked in _counts:
                _c = _counts[_asked]
                steps = [
                    f"The coin was tossed {_total} times and "
                    f"{_asked} appeared {_c} times.",
                    f"Empirical probability = {_c}/{_total}",
                ]
                return _prob_answer(Fraction(_c, _total), steps)
        else:
            _mf = re.search(
                r"(?:number\s+)?([1-6])\s+(?:appears?|occurs?|"
                r"comes?\s+up|is\s+obtained|obtained)\s+"
                r"(\d+)\s+times", ql)
            if _mf:
                _face, _c = _mf.group(1), int(_mf.group(2))
                steps = [
                    f"The die was rolled {_total} times and "
                    f"{_face} appeared {_c} times.",
                    f"Empirical probability = {_c}/{_total}",
                ]
                return _prob_answer(Fraction(_c, _total), steps)

    # Coins: exactly k heads in n tosses (or "2 heads in 3 tosses").
    # Wave 31: "at least / at most k heads in n tosses" must NOT be
    # hijacked by this exactly-shortcut (the "exactly" below is
    # optional) — those fall through to the enumeration block,
    # which knows the quantifiers.
    m = re.search(r"(?:exactly\s+)?(\d+)\s+heads?\s+in\s+(\d+)\s+"
                  r"(?:coin\s+)?tosses", ql)
    if m and re.search(r"at\s+(?:least|most)\s+$", ql[:m.start()]):
        m = None
    if m:
        k, n = int(m.group(1)), int(m.group(2))
        from math import comb
        fav = comb(n, k)
        steps = [
            f"Total outcomes for {n} coin tosses = 2^{n} = {2**n}",
            f"Favourable outcomes (exactly {k} heads) = C({n}, {k}) "
            f"= {fav}",
        ]
        return _prob_answer(Fraction(fav, 2**n), steps)
    # Coins tossed together (Wave 30; full event set, Wave 31):
    # enumerate the outcomes and count the matches. The legacy
    # single-coin shortcuts just below answer 1/2 for ANY
    # coin+head / coin+tail question, so every standard event
    # must be recognised here first. Wave 30 covered only
    # "at least / exactly ... heads / both / no head" — "two
    # coins ... at most one head" (correct 3/4) silently fell
    # through to the shortcut and returned 1/2, and "no tail" /
    # "at most ... tail" / "exactly ... tails" were missing too.
    # Wave 146: "exactly four ROUNDS of tossing" is a
    # geometric (repeat-until-success) ask, not a single-round
    # enumeration — the block below (and the bare 1/2 shortcut
    # after it) answered it 1/2. Decline the whole probability
    # path for the exact-rounds shape.
    if re.search(r"\bexactly\s+(?:\d+|one|two|three|four|"
                 r"five|six|seven|eight|nine|ten)\s+rounds?\b",
                 ql):
        return None
    if "coin" in ql and ("toss" in ql or "throw" in ql
                         or "flip" in ql or "both" in ql):
        _words = {"one": 1, "two": 2, "three": 3, "four": 4,
                  "five": 5}
        _num = r"(one|two|three|four|five|\d+)"

        def _cnt(word):
            _w = _words.get(word)
            return _w if _w is not None else int(word)

        # How many coins? "two coins" / "a pair of coins", or one
        # coin tossed repeatedly ("in 3 tosses", "tossed twice");
        # otherwise a single coin.
        _mc = re.search(r"\b" + _num + r"\s+coins?\b", ql)
        # Wave 146: "Three friends ... each one of them will
        # toss a coin" — the coin count is the number of
        # TOSSERS (the odd-one-out pizza game). Without it the
        # count stayed 1 and every part of the case was
        # answered 1/2 (CISCE audit idx 150-152).
        _mtoss = re.search(
            r"\b" + _num + r"\s+(?:friends|persons|people|"
            r"players|students|children)\b[\s\S]{0,160}?\beach\b"
            r"[\s\S]{0,40}?\btoss", ql)
        if _mc:
            _n = _cnt(_mc.group(1))
        elif _mtoss:
            _n = _cnt(_mtoss.group(1))
        elif re.search(r"\bboth\s+coins?\b", ql):
            # Wave 57: "both coins show heads" states the count
            # without a number word.
            _n = 2
        elif re.search(r"\ba\s+pair\s+of\s+coins?\b", ql):
            _n = 2
        elif re.search(r"\btossed\s+twice\b", ql):
            _n = 2
        elif re.search(r"\b(?:tossed|thrown|flipped)\s+"
                       r"thrice\b", ql):
            _n = 3
        else:
            # Wave 38: one coin tossed repeatedly is stated as
            # "tossed 5 times" — without this the count stayed
            # 1 and "exactly 3 heads" in 5 tosses counted the
            # favourable outcomes of a SINGLE toss (0) — the
            # broken binomial of Wave 35 audit #311.
            _mtm = re.search(r"(?:tossed|thrown|flipped)\s+"
                             + _num + r"\s+times", ql)
            _mr = re.search(r"\bin\s+" + _num + r"\s+tosses\b",
                            ql)
            if _mtm:
                _n = _cnt(_mtm.group(1))
            else:
                _n = _cnt(_mr.group(1)) if _mr else 1
        if 1 <= _n <= 5:
            outcomes = list(_iproduct("HT", repeat=_n))
            _ev = None
            # Wave 42: mixed exact events — "one head and
            # two tails" / "two tails and one head". When the
            # two counts add up to the number of coins, the
            # head count alone fixes the event.
            _m_ht = re.search(r"(?:getting\s+|of\s+)?" + _num
                              + r"\s+heads?\s+and\s+" + _num
                              + r"\s+tails?", ql)
            _m_th = re.search(r"(?:getting\s+|of\s+)?" + _num
                              + r"\s+tails?\s+and\s+" + _num
                              + r"\s+heads?", ql)
            _kh = _kt = None
            if _m_ht:
                _kh = _cnt(_m_ht.group(1))
                _kt = _cnt(_m_ht.group(2))
            elif _m_th:
                _kt = _cnt(_m_th.group(1))
                _kh = _cnt(_m_th.group(2))
            if _kh is not None and _kh + _kt == _n:
                _ev = (lambda h, k=_kh: h == k,
                       f"{_kh} head(s) and {_kt} tail(s)")
            # (pattern, test(heads_count, k)) — the label is the
            # matched phrase itself, e.g. "at most one head".
            _specs = [
                (r"at\s+least\s+" + _num + r"\s+heads?",
                 lambda h, k: h >= k),
                (r"at\s+least\s+" + _num + r"\s+tails?",
                 lambda h, k, n=_n: n - h >= k),
                (r"at\s+most\s+" + _num + r"\s+heads?",
                 lambda h, k: h <= k),
                (r"at\s+most\s+" + _num + r"\s+tails?",
                 lambda h, k, n=_n: n - h <= k),
                (r"exactly\s+" + _num + r"\s+heads?",
                 lambda h, k: h == k),
                (r"exactly\s+" + _num + r"\s+tails?",
                 lambda h, k, n=_n: n - h == k),
                # Wave 38: a bare count is an exact count —
                # "getting two heads" (Wave 35 audit #227
                # answered 1/2 via the single-coin shortcut).
                # Wave 42: "get" added to the alternation.
                (r"(?:getting|get|of)\s+" + _num + r"\s+heads?",
                 lambda h, k: h == k),
                (r"(?:getting|get|of)\s+" + _num + r"\s+tails?",
                 lambda h, k, n=_n: n - h == k),
            ]
            if _ev is None:
                for _pat, _fn in _specs:
                    _m = re.search(_pat, ql)
                    if _m:
                        _k = _cnt(_m.group(1))
                        _ev = ((lambda fn, k: lambda h: fn(h, k))
                               (_fn, _k), _m.group(0))
                        break
            if _ev is None:
                # Wave 146: the odd-one-out game events — "all
                # get the SAME result" (all heads or all tails)
                # vs "a DIFFERENT result" (not all the same).
                # The stem states both phrases, so the event is
                # whichever phrase the ASK (the later text)
                # repeats: compare last occurrences.
                _ps = ql.rfind("same result")
                _pd = ql.rfind("different result")
                if _ps >= 0 and _ps > _pd:
                    _ev = (lambda h, n=_n: h == 0 or h == n,
                           "all the same result")
                elif _pd >= 0 and _pd > _ps:
                    _ev = (lambda h, n=_n: 0 < h < n,
                           "a different result")
            if _ev is None:
                if re.search(r"\bboth\s+coins?\b[^.]{0,24}?"
                             r"\bheads?\b", ql):
                    _ev = (lambda h, n=_n: h == n, "all heads")
                elif re.search(r"\bboth\s+coins?\b[^.]{0,24}?"
                               r"\btails?\b", ql):
                    _ev = (lambda h: h == 0, "all tails")
                elif "both heads" in ql or "all heads" in ql:
                    _ev = (lambda h, n=_n: h == n, "all heads")
                elif "both tails" in ql or "all tails" in ql:
                    _ev = (lambda h: h == 0, "all tails")
                elif "no head" in ql:
                    _ev = (lambda h: h == 0, "no head")
                elif "no tail" in ql:
                    _ev = (lambda h, n=_n: h == n, "no tail")
                # Wave 58: "not getting a head" is the no-head
                # event worded with a negation — it used to fall
                # through to the bare coin+head shortcut below
                # and answer 1/2 whatever the coin count.
                elif re.search(
                        r"not\s+(?:getting|get)\s+(?:a\s+|an\s+)?"
                        r"heads?\b", ql):
                    _ev = (lambda h: h == 0,
                           "not getting a head")
                elif re.search(
                        r"not\s+(?:getting|get)\s+(?:a\s+|an\s+)?"
                        r"tails?\b", ql):
                    _ev = (lambda h, n=_n: h == n,
                           "not getting a tail")
                elif _n == 2 and re.search(
                        r"\b(?:a|one)\s+head\s+and\s+"
                        r"(?:a|one)\s+tail\b", ql):
                    _ev = (lambda h: h == 1,
                           "one head and one tail")
            if _ev is not None:
                fav = sum(1 for o in outcomes
                          if _ev[0](o.count("H")))
                steps = [
                    f"{_n} coin(s) tossed together give "
                    f"2^{_n} = {2 ** _n} equally likely "
                    f"outcomes: "
                    + ", ".join("".join(o) for o in outcomes),
                    f"Favourable outcomes ({_ev[1]}) = {fav}",
                ]
                return _prob_answer(Fraction(fav, 2 ** _n),
                                    steps)
    # Wave 58: the two bare shortcuts below carry an unstated
    # premise — a PLAIN single-toss ask. A question that
    # narrates an observed streak ("tossed 100 times in a row
    # and it lands heads every time — the next toss?") is not
    # that ask: the audit (#515) counts the confident 1/2 there
    # as a mistake, so a streak/history framing falls through
    # to the honest fallback instead.
    _streak = re.search(
        r"every\s+time|in\s+a\s+row|\bstreak\b|so\s+far|"
        r"always\s+lands?|has\s+landed", ql)
    if "coin" in ql and "head" in ql and not _streak:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "heads is 1 of them."])
    if "coin" in ql and "tail" in ql and not _streak:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "tails is 1 of them."])

    # Wave 38: one die thrown repeatedly — binomial with
    # p = 1/6 for the named face. "A die is thrown 4 times.
    # What is the probability of getting a six exactly 2
    # times?" was answered 1/6 (the single-throw shortcut of
    # Wave 35 audit #313); the coin analogue is the enumeration
    # above, a die has too many outcomes to enumerate.
    if "die" in ql or "dice" in ql:
        _mdt = re.search(r"(?:thrown|rolled|tossed)\s+(\d+)\s+"
                         r"times", ql)
        _mex = re.search(r"exactly\s+(\d+)\s+times", ql)
        _mface = re.search(
            r"\b(?:a\s+|an\s+)?(one|two|three|four|five|six|"
            r"[1-6])\b", ql[ql.find("getting"):]
            if "getting" in ql else ql)
        if _mdt and _mex and _mface:
            _n2 = int(_mdt.group(1))
            _k2 = int(_mex.group(1))
            if 1 <= _n2 <= 30 and 0 <= _k2 <= _n2:
                from math import comb as _comb
                _face = _mface.group(1)
                _prob = (Fraction(_comb(_n2, _k2))
                         * Fraction(1, 6) ** _k2
                         * Fraction(5, 6) ** (_n2 - _k2))
                steps = [
                    f"Each throw is independent with P({_face}) "
                    f"= 1/6 — a binomial experiment with "
                    f"n = {_n2}, p = 1/6.",
                    f"P(exactly {_k2} times) = C({_n2}, {_k2}) "
                    f"· (1/6)^{_k2} · (5/6)^{_n2 - _k2}",
                    f"C({_n2}, {_k2}) = {_comb(_n2, _k2)}",
                ]
                return _prob_answer(_prob, steps)

    # Two dice: sum
    m = re.search(r"sum\s+(?:of\s+)?(\d+)\s+(?:with|on|of)?\s*two\s+dice",
                  ql) or re.search(r"two\s+dice.*?sum\s+(?:of\s+)?(\d+)", ql)
    if m:
        target = int(m.group(1))
        fav = sum(1 for a, b in _iproduct(range(1, 7), repeat=2)
                  if a + b == target)
        steps = [
            "Two dice give 6 × 6 = 36 equally likely outcomes.",
            f"Outcomes with sum {target}: {fav}",
        ]
        return _prob_answer(Fraction(fav, 36), steps)

    # Wave 56: two-dice / thrown-twice SUM in the separated
    # phrasings — "the sum of the numbers is 8" (the sum and
    # the dice sit in different clauses, so the two patterns
    # above miss it) and "a die is thrown twice ... sum is
    # 12" (no word "two" at all). Same schema, any target.
    if ("two dice" in ql or "pair of dice" in ql
            or "two die" in ql or "thrown twice" in ql
            or "rolled twice" in ql or "tossed twice" in ql):
        _m56 = re.search(
            r"sum[^.]{0,45}?\bis\s+(?:equal\s+to\s+)?(\d+)",
            ql) or re.search(r"\bsum\s+(?:of\s+)?(\d+)\b", ql)
        if _m56:
            _t56 = int(_m56.group(1))
            if 2 <= _t56 <= 12:
                _fav56 = sum(
                    1 for a, b in _iproduct(range(1, 7),
                                            repeat=2)
                    if a + b == _t56)
                steps = [
                    "Two dice give 6 × 6 = 36 equally likely "
                    "outcomes.",
                    f"Outcomes with sum {_t56}: {_fav56}",
                ]
                return _prob_answer(Fraction(_fav56, 36),
                                    steps)

    # Wave 33: two dice — doublet ("same number on both dice").
    if ("die" in ql or "dice" in ql) and (
            "doublet" in ql or "same number" in ql):
        steps = [
            "Two dice give 6 × 6 = 36 equally likely outcomes.",
            "Outcomes with the same number on both dice "
            "(doublets): 6",
        ]
        return _prob_answer(Fraction(6, 36), steps)

    # Wave 33: single-die EVENT asks — even / odd / prime /
    # composite / square / greater than k / less than k /
    # multiple of k. These must run BEFORE the legacy single-
    # die pattern just below, which reads ANY digit in the
    # question as the wanted face ("greater than 4" answered
    # 1/6, the chance of exactly 4).
    if ("die" in ql or "dice" in ql) and "two" not in ql:
        _faces, _label = None, None
        _mg = re.search(r"(?:greater|more)\s+than\s+(\d)", ql)
        _ml = re.search(r"less\s+than\s+(\d)", ql)
        _mm = re.search(r"multiple\s+of\s+(\d)", ql) or \
            re.search(r"divisible\s+by\s+(\d)", ql)
        # Wave 58: "at least k" / "at most k" were missing from
        # this event table entirely, so "at least 5" fell to the
        # legacy pattern below, which reads ANY digit as the
        # wanted face and answered 1/6 (the chance of exactly 5).
        _mal = re.search(r"at\s+least\s+(\d)", ql)
        _mam = re.search(r"at\s+most\s+(\d)", ql)
        if "even" in ql:
            _faces, _label = [2, 4, 6], "an even number"
        elif "odd" in ql:
            _faces, _label = [1, 3, 5], "an odd number"
        elif "prime" in ql:
            _faces, _label = [2, 3, 5], "a prime number"
        elif "composite" in ql:
            _faces, _label = [4, 6], "a composite number"
        elif "perfect square" in ql or "square number" in ql:
            _faces, _label = [1, 4], "a perfect square"
        elif _mg:
            _k = int(_mg.group(1))
            _faces = [f for f in range(1, 7) if f > _k]
            _label = f"a number greater than {_k}"
        elif _ml:
            _k = int(_ml.group(1))
            _faces = [f for f in range(1, 7) if f < _k]
            _label = f"a number less than {_k}"
        elif _mm:
            _k = int(_mm.group(1))
            if _k:
                _faces = [f for f in range(1, 7) if f % _k == 0]
                _label = f"a multiple of {_k}"
        elif _mal:
            _k = int(_mal.group(1))
            _faces = [f for f in range(1, 7) if f >= _k]
            _label = f"a number at least {_k}"
        elif _mam:
            _k = int(_mam.group(1))
            _faces = [f for f in range(1, 7) if f <= _k]
            _label = f"a number at most {_k}"
        # Wave 58: "not getting ..." is the COMPLEMENT of the
        # event. The legacy pattern below ignored the "not"
        # entirely — "not getting a 6" was answered 1/6, the
        # probability of getting a 6 itself.
        _neg = re.search(
            r"\bnot\s+(?:getting|rolling|obtaining|get)\b", ql) \
            or re.search(
                r"\bnot\s+(?:an?\s+)?(?:even|odd|prime|"
                r"composite)\b", ql)
        if _faces is None and _neg:
            _mf1 = re.search(
                r"(?:getting|rolling|of)\s+(?:a\s+|an\s+)?"
                r"(\d)\b", ql)
            if _mf1:
                _faces = [int(_mf1.group(1))]
                _label = f"a {_mf1.group(1)}"
        if _faces is not None and _neg:
            _faces = [f for f in range(1, 7) if f not in _faces]
            _label = "not " + _label
        if _faces is not None:
            steps = [
                "A fair die has 6 equally likely faces (1-6).",
                f"Favourable outcomes ({_label}): "
                + ", ".join(str(f) for f in _faces)
                + f" — {len(_faces)} of them",
            ]
            return _prob_answer(Fraction(len(_faces), 6), steps)

    # Single die
    m = re.search(r"(?:getting|rolling|of)\s+(?:a\s+)?(\d)\s+on\s+a\s+"
                  r"(?:die|dice)", ql) or re.search(
                      r"die|dice", ql) and re.search(r"\b(\d)\b", ql)
    if m and ("die" in ql or "dice" in ql) and "two" not in ql:
        steps = ["A fair die has 6 equally likely faces (1-6); the "
                 "wanted face is 1 of them."]
        return _prob_answer(Fraction(1, 6), steps)

    # Wave 33: defective items — "a lot of 20 bulbs contains
    # 4 defective ones … probability that it is not defective".
    _md = re.search(
        r"(\d+)\s+(?:bulbs?|items?|articles?|pens?|eggs?|"
        r"mangoes|apples|oranges|toys?|balls?)\b[^.]{0,40}?"
        r"(\d+)\s+(?:of\s+them\s+)?(?:are\s+)?defective", ql) or \
        re.search(r"contains?\s+(\d+)\s+defective", ql)
    if _md and "defective" in ql:
        if _md.re.pattern.startswith("contains"):
            _total_m = re.search(r"(?:lot|box|bag|batch|set)"
                                 r"\s+of\s+(\d+)", ql)
            _total = int(_total_m.group(1)) if _total_m else None
            _def = int(_md.group(1))
        else:
            _total, _def = int(_md.group(1)), int(_md.group(2))
        if _total and 0 <= _def <= _total:
            if "not defective" in ql or "non-defective" in ql \
                    or "not be defective" in ql:
                _fav, _lab = _total - _def, "not defective"
            else:
                _fav, _lab = _def, "defective"
            steps = [
                f"Total items = {_total}, defective = {_def}, "
                f"so not defective = {_total - _def}.",
                f"Favourable ({_lab}) = {_fav}",
            ]
            return _prob_answer(Fraction(_fav, _total), steps)

    # Wave 33: 53 weekdays in a year — a leap year has 52
    # weeks + 2 extra days (7 possible consecutive pairs, 2
    # contain any given weekday); a non-leap year has 1 extra
    # day (1 of 7).
    _mw = re.search(
        r"53\s+(sundays?|mondays?|tuesdays?|wednesdays?|"
        r"thursdays?|fridays?|saturdays?)", ql)
    if _mw and "year" in ql:
        if "non-leap" in ql or "non leap" in ql \
                or "ordinary year" in ql:
            steps = [
                "A non-leap year has 365 days = 52 weeks + "
                "1 extra day.",
                "The extra day can be any of the 7 weekdays; "
                f"exactly 1 of them is a {_mw.group(1)[:-1]} "
                "day, giving a 53rd one.",
            ]
            return _prob_answer(Fraction(1, 7), steps)
        if "leap" in ql:
            steps = [
                "A leap year has 366 days = 52 weeks + 2 "
                "extra days.",
                "The 2 extra days form one of 7 consecutive "
                "pairs; 2 of those pairs contain a "
                f"{_mw.group(1)[:-1]} day, giving a 53rd one.",
            ]
            return _prob_answer(Fraction(2, 7), steps)

    # Balls in a bag: "5 red and 3 blue balls ... red ball"
    # Wave 56: marbles in a jar/box are the same schema (the
    # gate required the word "ball", so "4 red marbles, 6
    # green marbles ... it is green" fell through), and the
    # ask may name the colour WITHOUT the object word —
    # "probability that it is red / it is not black" — which
    # the "<colour> ball" search after "probab" missed.
    if "ball" in ql or "marble" in ql:
        counts = {}
        for num, colour in re.findall(
            r"(\d+)\s+(red|blue|green|yellow|black|white|orange|pink|"
            r"purple|brown)\s*(?:balls?|marbles?)?", ql
        ):
            counts[colour] = counts.get(colour, 0) + int(num)
        m = re.search(r"(red|blue|green|yellow|black|white|orange|pink|"
                      r"purple|brown)\s+(?:ball|marble)",
                      ql.split("probab")[-1])
        if m is None:
            m = re.search(
                r"it\s+is\s+(?:not\s+)?"
                r"(red|blue|green|yellow|black|white|orange|"
                r"pink|purple|brown)\b", ql.split("probab")[-1])
        if m is None:
            # "the marble is black" — object word, then the
            # colour (the reverse of the "<colour> ball"
            # order above).
            m = re.search(
                r"(?:ball|marble)\s+is\s+(?:not\s+)?"
                r"(red|blue|green|yellow|black|white|orange|"
                r"pink|purple|brown)\b", ql.split("probab")[-1])
        if counts and m:
            colour = m.group(1)
            total = sum(counts.values())
            # Wave 33: "not a red ball" is the COMPLEMENT —
            # the plain colour match below answered it with
            # the red probability itself (5/8 for "not red").
            _seg = ql.split("probab")[-1]
            if re.search(r"\bnot\b[^.]{0,30}?" + colour, _seg) \
                    or re.search(r"\bnot\s+(?:a\s+)?" + colour
                                 + r"\b", _seg):
                steps = [
                    "Count the balls: "
                    + ", ".join(f"{c} {col}" for col, c
                                in counts.items())
                    + f" — total {total}",
                    f"Not {colour} = {total} - "
                    f"{counts.get(colour, 0)} = "
                    f"{total - counts.get(colour, 0)}",
                ]
                return _prob_answer(
                    Fraction(total - counts.get(colour, 0),
                             total), steps)
            steps = [
                "Count the balls: "
                + ", ".join(f"{c} {col}" for col, c in counts.items())
                + f" — total {total}",
                f"Favourable (red... wanted {colour}) = "
                f"{counts.get(colour, 0)}",
            ]
            return _prob_answer(
                Fraction(counts.get(colour, 0), total), steps)

    # Wave 56: numbered-set schema — discs / tickets / cards /
    # chits numbered 1 to N, or a spinner with numbers 1 to N.
    # One number is drawn; count how many of 1..N carry the
    # asked property (two-digit, multiple of k, prime, ...)
    # arithmetically — any N, any property in the table.
    _mn56 = None
    if "numbered" in ql or "spinner" in ql:
        _mn56 = re.search(r"1\s+to\s+(\d+)", ql)
    if _mn56:
        _N56 = int(_mn56.group(1))
        if 2 <= _N56 <= 100000:
            _fav56 = _label56 = None
            _mg56 = re.search(r"(?:greater|more)\s+than\s+(\d+)",
                              ql)
            _ml56 = re.search(r"less\s+than\s+(\d+)", ql)
            _mm56 = re.search(r"multiple\s+of\s+(\d+)", ql) or \
                re.search(r"divisible\s+by\s+(\d+)", ql)
            if "two-digit" in ql or "two digit" in ql:
                _fav56 = max(0, min(_N56, 99) - 9)
                _label56 = "two-digit numbers"
            elif "single-digit" in ql or "one-digit" in ql:
                _fav56 = min(_N56, 9)
                _label56 = "single-digit numbers"
            elif _mm56 and int(_mm56.group(1)) > 0:
                _k56 = int(_mm56.group(1))
                _fav56 = _N56 // _k56
                _label56 = f"multiples of {_k56}"
            elif "prime" in ql:
                _fav56 = sum(
                    1 for _v in range(2, _N56 + 1)
                    if all(_v % _d for _d in range(
                        2, int(_v ** 0.5) + 1)))
                _label56 = "prime numbers"
            elif "perfect square" in ql or "square number" in ql:
                from math import isqrt as _isqrt56
                _fav56 = _isqrt56(_N56)
                _label56 = "perfect squares"
            elif "even" in ql:
                _fav56 = _N56 // 2
                _label56 = "even numbers"
            elif "odd" in ql:
                _fav56 = (_N56 + 1) // 2
                _label56 = "odd numbers"
            elif _mg56:
                _k56 = int(_mg56.group(1))
                _fav56 = max(0, _N56 - _k56)
                _label56 = f"numbers greater than {_k56}"
            elif _ml56:
                _k56 = int(_ml56.group(1))
                _fav56 = max(0, min(_N56, _k56 - 1))
                _label56 = f"numbers less than {_k56}"
            if _fav56 is not None:
                steps = [
                    f"The numbers are 1 to {_N56} — {_N56} "
                    f"equally likely outcomes.",
                    f"Favourable ({_label56}) = {_fav56}",
                ]
                return _prob_answer(Fraction(_fav56, _N56),
                                    steps)

    # Pack of cards
    if "card" in ql and ("deck" in ql or "pack" in ql or "52" in ql):
        # Wave 33: a SPECIFIC card or colour+rank ask must be
        # answered before the generic rank table — "king of
        # hearts" and "queen of black colour" both used to
        # return the any-king / any-queen 1/13.
        _ms = re.search(r"\b(king|queen|jack|ace)\s+of\s+"
                        r"(hearts?|diamonds?|spades?|clubs?)\b",
                        ql)
        if _ms:
            steps = [
                "A standard pack has 52 cards.",
                f"There is exactly 1 {_ms.group(1)} of "
                f"{_ms.group(2)}.",
            ]
            return _prob_answer(Fraction(1, 52), steps)
        _mc2 = re.search(r"\b(red|black)\s+"
                         r"(king|queen|jack|ace)\b", ql) or \
            re.search(r"\b(king|queen|jack|ace)\s+of\s+"
                      r"(red|black)\b", ql)
        if _mc2:
            _rank = _mc2.group(1) if _mc2.re.pattern.startswith(
                r"\b(king") else _mc2.group(2)
            _colr = _mc2.group(2) if _rank == _mc2.group(1) \
                else _mc2.group(1)
            steps = [
                "A standard pack has 52 cards.",
                f"Number of {_colr} {_rank}s = 2.",
            ]
            return _prob_answer(Fraction(2, 52), steps)
        # Wave 58: "a king or a queen" is a UNION of two
        # mutually exclusive events. The table below takes the
        # FIRST pattern that matches, so it answered 1/13 (the
        # kings alone). The union is summed only inside one
        # disjoint family — two ranks, two suits, or the two
        # colours — where the events cannot overlap.
        _mu = re.search(
            r"\b(ace|king|queen|jack)s?\b\s+or\s+(?:a\s+|an\s+)?"
            r"(ace|king|queen|jack)s?\b", ql)
        if _mu and _mu.group(1) != _mu.group(2):
            steps = [
                "A standard pack has 52 cards.",
                f"There are 4 {_mu.group(1)}s and 4 "
                f"{_mu.group(2)}s, and a card cannot be both.",
                f"Favourable = 4 + 4 = 8",
            ]
            return _prob_answer(Fraction(8, 52), steps)
        _mu = re.search(
            r"\b(hearts?|diamonds?|spades?|clubs?)\b\s+or\s+"
            r"(?:a\s+|an\s+)?(hearts?|diamonds?|spades?|clubs?)\b",
            ql)
        if _mu and _mu.group(1) != _mu.group(2):
            steps = [
                "A standard pack has 52 cards.",
                f"There are 13 {_mu.group(1)} and 13 "
                f"{_mu.group(2)}, and a card has only one suit.",
                "Favourable = 13 + 13 = 26",
            ]
            return _prob_answer(Fraction(26, 52), steps)
        _mu = re.search(
            r"\b(red|black)\b\s+or\s+(?:a\s+|an\s+)?(red|black)\b",
            ql)
        if _mu and _mu.group(1) != _mu.group(2):
            steps = [
                "A standard pack has 52 cards.",
                "Every card is either red or black.",
                "Favourable = 26 + 26 = 52",
            ]
            return _prob_answer(Fraction(52, 52), steps)
        fav, label = None, None
        table = [
            (r"\bace\b", 4, "aces"),
            (r"\bking\b", 4, "kings"),
            (r"\bqueen\b", 4, "queens"),
            (r"\bjack\b", 4, "jacks"),
            (r"face\s+card", 12, "face cards"),
            (r"\bred\b", 26, "red cards"),
            (r"\bblack\b", 26, "black cards"),
            (r"\bheart", 13, "hearts"),
            (r"\bdiamond", 13, "diamonds"),
            (r"\bspade", 13, "spades"),
            (r"\bclub", 13, "clubs"),
        ]
        for pat, n, lab in table:
            if re.search(pat, ql):
                fav, label = n, lab
                break
        if fav is not None:
            steps = [
                "A standard pack has 52 cards.",
                f"Number of {label} = {fav}",
            ]
            return _prob_answer(Fraction(fav, 52), steps)
    return None


# ------------------------------------------------------------ counting
def _counting(q: str):
    ql = q.lower()
    m = re.search(r"\bP\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", q) or re.search(
        r"(\d+)\s*P\s*(\d+)", q)
    if m or "permutation" in ql:
        if not m:
            # Wave 146: a bare "permutation" mention is NOT a
            # licence to feed the first two numbers in the text
            # to P(n, r) — the CISCE audit's DEVASTATION ask
            # ("4-letter combinations and 4-letter
            # permutations") was answered P(4, 4) = 24 from the
            # two 4s. Only a structured "n things taken r at a
            # time" parse may proceed; anything else declines.
            mm = re.search(
                r"(\d+)\s+(?:different\s+)?(?:things|objects|"
                r"items|letters|digits|persons|people|students|"
                r"books|colours|colors)\s+(?:taken|arranged)\s+"
                r"(\d+)\s+at\s+a\s+time", ql)
            if mm:
                n, r = int(mm.group(1)), int(mm.group(2))
            else:
                mm = re.search(
                    r"taken\s+(\d+)\s+at\s+a\s+time\s*(?:from|"
                    r"of)\s+(\d+)", ql)
                if not mm:
                    return None
                r, n = int(mm.group(1)), int(mm.group(2))
        else:
            n, r = int(m.group(1)), int(m.group(2))
        if r > n or r < 0:
            return None
        val = sp.perm(n, r) if hasattr(sp, "perm") else None
        from math import factorial as _f
        val = _f(n) // _f(n - r)
        steps = [
            "Permutations (order matters): P(n, r) = n! / (n - r)!",
            f"P({n}, {r}) = {n}! / {n - r}! = {val}",
        ]
        return {"type": "statistics", "op": "permutation",
                "answer": fmt_num(val), "value": int(val), "steps": steps}
    m = re.search(r"\bC\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", q) or re.search(
        r"(\d+)\s*C\s*(\d+)", q)
    if m or "combination" in ql or "choose" in ql \
            or "chosen" in ql or "selected" in ql \
            or "committee" in ql:
        if not m:
            # Wave 146: the old fallback took the FIRST TWO
            # numbers in the whole text as (n, r) whenever the
            # words "combination"/"choose" appeared anywhere —
            # and every board-paper Section A carries the
            # instruction "Choose the correct answers...", so
            # an RD question was answered C(400, 18) (a 31-digit
            # number), a shares question C(50, 40), a
            # correlation question C(53, 28). Only a structured
            # choose/select/taken parse may proceed now; a bare
            # keyword declines.
            mm = re.search(
                r"(?:choose|select|chosen|selected)\s+(\d+)\s+"
                r"(?:\w+\s+)?(?:from|of|out\s+of)\s+"
                r"(?:a\s+total\s+of\s+)?(\d+)", ql)
            if mm:
                r, n = int(mm.group(1)), int(mm.group(2))
            else:
                mm = re.search(
                    r"(\d+)\s+(?:students|persons|people|"
                    r"members|items|objects|books|things)\s+"
                    r"(?:can\s+be\s+|to\s+be\s+|are\s+|be\s+)?"
                    r"(?:chosen|selected)\s+from\s+(\d+)", ql)
            if mm:
                r, n = int(mm.group(1)), int(mm.group(2))
            else:
                mm = re.search(
                    r"(?:committee|team|group)\s+of\s+(\d+)\b[^.]{0,40}?"
                    r"\bfrom\s+(?:a\s+total\s+of\s+)?(\d+)", ql)
                if mm:
                    r, n = int(mm.group(1)), int(mm.group(2))
                else:
                    mm = re.search(
                        r"(\d+)\s+(?:taken|from)\s+(\d+)", ql)
                    if not mm:
                        return None
                    n, r = int(mm.group(1)), int(mm.group(2))
        else:
            n, r = int(m.group(1)), int(m.group(2))
        if r > n or r < 0:
            return None
        from math import comb
        val = comb(n, r)
        steps = [
            "Combinations (order does not matter): "
            "C(n, r) = n! / (r! · (n - r)!)",
            f"C({n}, {r}) = {n}! / ({r}! · {n - r}!) = {val}",
        ]
        return {"type": "statistics", "op": "combination",
                "answer": fmt_num(val), "value": int(val), "steps": steps}
    m = re.search(r"factorial\s*(?:of\s*)?(\d+)", ql) or re.search(
        r"^\s*(\d+)\s*!\s*$", q)
    if m:
        from math import factorial as _f
        n = int(m.group(1))
        steps = [
            f"{n}! = {' × '.join(str(i) for i in range(n, 0, -1))}"
            if n <= 10 else f"{n}! = {n} × {n-1} × ... × 1",
            f"= {_f(n)}",
        ]
        return {"type": "statistics", "op": "factorial",
                "answer": fmt_num(_f(n)), "value": _f(n), "steps": steps}
    return None


def _parse_grouped_table(ql):
    """(classes, freqs) from a text-given frequency table like
    'class intervals 0-10, 10-20, 20-30 with frequencies
    5, 8, 12' — or None when the shape is not clean."""
    classes = [(float(a), float(b)) for a, b in re.findall(
        r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", ql)]
    mf = re.search(
        r"(?:frequenc\w+|number\s+of\s+(?:students|"
        r"observations|persons|workers|families))"
        r"\s*(?:are|:|is)?\s*([\d][\d,\s]*)", ql)
    if not classes or not mf:
        return None
    freqs = [float(v) for v in re.findall(r"\d+(?:\.\d+)?",
                                          mf.group(1))]
    if len(freqs) > len(classes):
        freqs = freqs[:len(classes)]
    if len(freqs) != len(classes) or len(classes) < 2:
        return None
    if any(b <= a for a, b in classes):
        return None
    if any(classes[i][0] < classes[i - 1][0]
           for i in range(1, len(classes))):
        return None
    return classes, freqs


def _grouped_stats(ql):
    """Wave 32: mean / median / mode of GROUPED data from a
    frequency table given in the question text. The raw-list
    statistics below used to grab the frequency numbers as if
    they were the data itself."""
    got = _parse_grouped_table(ql)
    if not got:
        return None
    classes, freqs = got
    asks = [(ql.find(w), w) for w in ("median", "mode", "mean")
            if w in ql]
    if not asks:
        return None
    ask = min(asks)[1]
    N = sum(freqs)
    if ask == "mean":
        mids = [(a + b) / 2 for a, b in classes]
        sfx = sum(f * x for f, x in zip(freqs, mids))
        val = sfx / N
        steps = [
            "Class marks (midpoints): "
            + ", ".join(fmt_num(m) for m in mids),
            f"Sum of f·x = {fmt_num(sfx)}, sum of f = "
            f"{fmt_num(N)}",
            f"Mean = {fmt_num(sfx)} / {fmt_num(N)} "
            f"= {fmt_num(val)}",
        ]
        return {"type": "statistics", "op": "grouped_mean",
                "answer": fmt_num(val), "value": val,
                "steps": steps}
    contiguous = all(classes[i][1] == classes[i + 1][0]
                     for i in range(len(classes) - 1))
    if not contiguous:
        return None
    if ask == "median":
        half = N / 2
        cf = 0.0
        for i, (a, b) in enumerate(classes):
            prev = cf
            cf += freqs[i]
            if cf >= half:
                l, f, h = a, freqs[i], b - a
                val = l + ((half - prev) / f) * h
                steps = [
                    f"N = {fmt_num(N)}, so N/2 = "
                    f"{fmt_num(half)}.",
                    f"The cumulative frequency first reaches "
                    f"{fmt_num(half)} in the class "
                    f"{fmt_num(a)}-{fmt_num(b)} — the median "
                    f"class (l = {fmt_num(l)}, f = "
                    f"{fmt_num(f)}, cf before it = "
                    f"{fmt_num(prev)}, h = {fmt_num(h)}).",
                    f"Median = l + ((N/2 - cf)/f) × h = "
                    f"{fmt_num(val)}",
                ]
                return {"type": "statistics",
                        "op": "grouped_median",
                        "answer": fmt_num(val), "value": val,
                        "steps": steps}
        return None
    # mode
    widths = {b - a for a, b in classes}
    if len(widths) != 1:
        return None
    i = max(range(len(freqs)), key=lambda j: freqs[j])
    f1 = freqs[i]
    f0 = freqs[i - 1] if i > 0 else 0.0
    f2 = freqs[i + 1] if i < len(freqs) - 1 else 0.0
    denom = 2 * f1 - f0 - f2
    if denom == 0:
        return None
    l, h = classes[i][0], classes[i][1] - classes[i][0]
    val = l + ((f1 - f0) / denom) * h
    steps = [
        f"The modal class is {fmt_num(classes[i][0])}-"
        f"{fmt_num(classes[i][1])} (highest frequency "
        f"{fmt_num(f1)}).",
        f"Mode = l + ((f1 - f0)/(2·f1 - f0 - f2)) × h with "
        f"f0 = {fmt_num(f0)}, f2 = {fmt_num(f2)}, "
        f"h = {fmt_num(h)}",
        f"= {fmt_num(val)}",
    ]
    return {"type": "statistics", "op": "grouped_mode",
            "answer": fmt_num(val), "value": val,
            "steps": steps}


def _ogive_median(ql):
    """Wave 33: median from an OGIVE (cumulative frequency)
    question. NCERT Class 10 gives the data as "less than
    <bound>: <cf>" (or "more than") pairs and asks for the
    median — the value whose cumulative frequency is N/2 on
    the ogive. The pairs carry no class-interval dashes, so
    the grouped-table parser missed them and the raw-list
    median of bounds+frequencies answered instead (22.5 for
    data whose true median is 21.67)."""
    if "ogive" not in ql and "cumulative" not in ql:
        return None
    lt = [(float(a), float(b)) for a, b in re.findall(
        r"less\s+than\s+(\d+(?:\.\d+)?)\s*[:\-–]?\s*"
        r"(\d+(?:\.\d+)?)", ql)]
    mt = [(float(a), float(b)) for a, b in re.findall(
        r"more\s+than\s+(\d+(?:\.\d+)?)\s*[:\-–]?\s*"
        r"(\d+(?:\.\d+)?)", ql)]
    classes = freqs = None
    kind = None
    for pairs, how in ((lt, "less"), (mt, "more")):
        if len(pairs) < 3:
            continue
        pairs = sorted(pairs)
        bounds = [p[0] for p in pairs]
        cfs = [p[1] for p in pairs]
        diffs = [bounds[i + 1] - bounds[i]
                 for i in range(len(bounds) - 1)]
        if not diffs or any(d <= 0 for d in diffs) or \
                len(set(diffs)) != 1:
            continue
        h = diffs[0]
        if how == "less":
            if any(cfs[i] < cfs[i - 1]
                   for i in range(1, len(cfs))):
                continue
            classes = [(bounds[0] - h, bounds[0])] + \
                [(bounds[i - 1], bounds[i])
                 for i in range(1, len(bounds))]
            freqs = [cfs[0]] + [cfs[i] - cfs[i - 1]
                                for i in range(1, len(cfs))]
        else:
            if any(cfs[i] > cfs[i - 1]
                   for i in range(1, len(cfs))):
                continue
            classes = [(bounds[i], bounds[i + 1])
                       for i in range(len(bounds) - 1)] + \
                [(bounds[-1], bounds[-1] + h)]
            freqs = [cfs[i] - cfs[i + 1]
                     for i in range(len(cfs) - 1)] + [cfs[-1]]
        kind = how
        break
    if classes is None or any(f < 0 for f in freqs):
        return None
    N = sum(freqs)
    if N <= 0:
        return None
    half = N / 2
    cf = 0.0
    for i, (a, b) in enumerate(classes):
        prev = cf
        cf += freqs[i]
        if cf >= half:
            l, f, h = a, freqs[i], b - a
            if f == 0:
                return None
            val = l + ((half - prev) / f) * h
            steps = [
                f"From the {kind}-than ogive data: N = "
                f"{fmt_num(N)}, so the median is the value "
                f"with cumulative frequency N/2 = "
                f"{fmt_num(half)}.",
                f"Converting to classes, the cumulative "
                f"frequency first reaches {fmt_num(half)} "
                f"in the class {fmt_num(a)}-{fmt_num(b)} "
                f"— the median class (l = {fmt_num(l)}, "
                f"f = {fmt_num(f)}, cf before it = "
                f"{fmt_num(prev)}, h = {fmt_num(h)}).",
                f"Median = l + ((N/2 - cf)/f) × h = "
                f"{fmt_num(val)}",
            ]
            return {"type": "statistics", "op": "ogive_median",
                    "answer": fmt_num(val), "value": val,
                    "steps": steps}
    return None


def _freq_mean_unknown(ql):
    """Wave 33: "the mean of x: 10, 20, 30, 40, 50 with
    f: 3, 5, 4, p, 3 is 30 — find p". Two colon lists, one
    letter among the frequencies; solve the linear equation
    Σfx = mean × Σf for the unknown frequency. The raw-list
    mean below averaged every number in the sentence
    (19.8-style) for this standard NCERT form."""
    mx = re.search(r"\bx\s*:\s*([\d][\d,\s]*)", ql)
    mf = re.search(r"\bf\s*:\s*([\d][\d,\s]*[a-z][\d,\s]*)", ql)
    mm = re.search(r"mean[^.]{0,60}?\bis\s+(\d+(?:\.\d+)?)", ql)
    if not (mx and mf and mm):
        return None
    xs = [float(v) for v in re.findall(r"\d+(?:\.\d+)?",
                                       mx.group(1))]
    toks = [t for t in re.split(r"[,\s]+", mf.group(1).strip())
            if t]
    if len(xs) < 3 or len(toks) != len(xs):
        return None
    unk = [i for i, t in enumerate(toks) if not t[0].isdigit()]
    if len(unk) != 1:
        return None
    ui = unk[0]
    letter = toks[ui]
    if len(letter) != 1:
        return None
    mean = float(mm.group(1))
    sf = sum(float(t) for i, t in enumerate(toks) if i != ui)
    sfx = sum(x * float(t) for i, (x, t) in enumerate(
        zip(xs, toks)) if i != ui)
    xu = xs[ui]
    if xu == mean:
        return None
    val = (mean * sf - sfx) / (xu - mean)
    if val <= 0 or abs(val - round(val)) > 1e-9:
        return None
    val = int(round(val))
    steps = [
        f"Σfx = {fmt_num(sfx)} + {fmt_num(xu)}·{letter} and "
        f"Σf = {fmt_num(sf)} + {letter}.",
        f"Mean = Σfx / Σf = {fmt_num(mean)} gives "
        f"{fmt_num(xu)}·{letter} - {fmt_num(mean)}·{letter} "
        f"= {fmt_num(mean * sf)} - {fmt_num(sfx)}.",
        f"{letter} = {val}",
    ]
    return {"type": "statistics", "op": "freq_mean_unknown",
            "answer": f"{letter} = {val}", "value": val,
            "steps": steps}


def solve_statistics(question: str):
    q = question.strip()
    ql = q.lower()

    # Wave 38: binomial mean / variance relations (Wave 35
    # audit #312 — "mean 20, variance 16, find n and p" was
    # answered '4', the variance of the two stated numbers).
    # mean = np and variance = npq, so q = variance / mean.
    if "binomial" in ql:
        _bm = re.search(r"mean\s*(?:is|=)\s*(\d+(?:\.\d+)?)",
                        ql) or re.search(
                            r"mean\b[^.]{0,45}?\bis\s+"
                            r"(\d+(?:\.\d+)?)", ql)
        _bv = re.search(r"variance\s*(?:is|=)\s*"
                        r"(\d+(?:\.\d+)?)", ql) or re.search(
                            r"variance\b[^.]{0,45}?\bis\s+"
                            r"(\d+(?:\.\d+)?)", ql)
        if _bm and _bv:
            _M, _V = float(_bm.group(1)), float(_bv.group(1))
            if 0 < _V < _M:
                _qq = _V / _M
                _pp = 1 - _qq
                _nn = _M / _pp
                steps = [
                    f"For a binomial distribution, mean = np "
                    f"= {fmt_num(_M)} and variance = npq = "
                    f"{fmt_num(_V)}.",
                    f"q = variance / mean = {fmt_num(_V)} / "
                    f"{fmt_num(_M)} = {fmt_num(_qq)}",
                    f"p = 1 - q = {fmt_num(_pp)}",
                    f"n = mean / p = {fmt_num(_M)} / "
                    f"{fmt_num(_pp)} = {fmt_num(_nn)}",
                ]
                return {"type": "statistics",
                        "op": "binomial_mean_variance",
                        "answer": f"n = {fmt_num(_nn)}, "
                                  f"p = {fmt_num(_pp)}",
                        "value": float(_nn), "steps": steps}
        _bn = re.search(r"\bn\s*=\s*(\d+)", ql)
        _bp = re.search(r"\bp\s*=\s*(\d+(?:\.\d+)?)", ql)
        if _bn and _bp and ("mean" in ql or "variance" in ql):
            _nn = int(_bn.group(1))
            _pp = float(_bp.group(1))
            if 0 < _pp < 1:
                steps = [
                    f"Binomial with n = {_nn}, p = {fmt_num(_pp)}"
                    f", q = 1 - p = {fmt_num(1 - _pp)}.",
                    f"Mean = np = {_nn} × {fmt_num(_pp)} = "
                    f"{fmt_num(_nn * _pp)}",
                    f"Variance = npq = {fmt_num(_nn * _pp)} × "
                    f"{fmt_num(1 - _pp)} = "
                    f"{fmt_num(_nn * _pp * (1 - _pp))}",
                ]
                return {"type": "statistics",
                        "op": "binomial_mean_variance",
                        "answer": f"Mean = {fmt_num(_nn * _pp)}, "
                                  f"variance = "
                                  f"{fmt_num(_nn * _pp * (1 - _pp))}",
                        "value": float(_nn * _pp), "steps": steps}

    # Wave 156 (Wave 153 audit book-020): corrected mean & SD
    # after a wrong observation — the NCERT form: "The mean
    # and standard deviation of N observations are M and S.
    # ... an observation W was incorrect. (i) If the wrong
    # item is omitted. (ii) If it is replaced by C." The raw
    # path harvested the stated numbers as a data list and
    # answered with their own std. Sigma x = N*M and
    # Sigma x^2 = N*(S^2 + M^2); adjust for the case.
    _cm = re.search(
        r"mean\s+and\s+standard\s+deviation\s+of\s+(\d+)\s+"
        r"observations?\s+are\s+(?:found\s+to\s+be\s+)?"
        r"(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)", ql)
    _cw = re.search(
        r"observation\s+(\d+(?:\.\d+)?)\s+was\s+(?:incorrect|"
        r"wrong)", ql) or re.search(
            r"wrong\s+(?:item|observation)\s+(?:is|was)\s+"
            r"(\d+(?:\.\d+)?)", ql)
    if _cm and _cw:
        _cn = int(_cm.group(1))
        _cmean, _csd = float(_cm.group(2)), float(_cm.group(3))
        _cwrong = float(_cw.group(1))
        _sx = _cn * _cmean
        _sx2 = _cn * (_csd ** 2 + _cmean ** 2)
        _cases = []
        _parts = []
        _rep = re.search(r"replaced\s+by\s+(\d+(?:\.\d+)?)",
                         ql)
        if re.search(r"omit|removed|left\s+out|excluded",
                     ql) and _cn >= 2:
            _n1 = _cn - 1
            _m1 = (_sx - _cwrong) / _n1
            _v1 = (_sx2 - _cwrong ** 2) / _n1 - _m1 ** 2
            if _v1 >= 0:
                _cases.append(
                    f"(i) omitted: new sum = {fmt_num(_sx)} - "
                    f"{fmt_num(_cwrong)} = "
                    f"{fmt_num(_sx - _cwrong)} over {_n1} "
                    f"observations, so correct mean = "
                    f"{fmt_num(_m1)}; correct SD = "
                    f"sqrt({fmt_num(_v1)}) = "
                    f"{fmt_num(_v1 ** 0.5)}")
                _parts.append(
                    f"(i) mean = {fmt_num(_m1)}, SD = "
                    f"{fmt_num(_v1 ** 0.5)}")
        if _rep:
            _crc = float(_rep.group(1))
            _m2 = (_sx - _cwrong + _crc) / _cn
            _v2 = (_sx2 - _cwrong ** 2 + _crc ** 2) / _cn \
                - _m2 ** 2
            if _v2 >= 0:
                _cases.append(
                    f"(ii) replaced by {fmt_num(_crc)}: correct "
                    f"mean = {fmt_num(_m2)}; correct SD = "
                    f"sqrt({fmt_num(_v2)}) = "
                    f"{fmt_num(_v2 ** 0.5)}")
                _parts.append(
                    f"(ii) mean = {fmt_num(_m2)}, SD = "
                    f"{fmt_num(_v2 ** 0.5)}")
        if _parts:
            steps = [
                f"Sum of the {_cn} observations = {_cn} x "
                f"{fmt_num(_cmean)} = {fmt_num(_sx)}; sum of "
                f"squares = {_cn} x ({fmt_num(_csd)}^2 + "
                f"{fmt_num(_cmean)}^2) = {fmt_num(_sx2)}",
            ] + _cases
            return {"type": "statistics",
                    "op": "corrected_mean_sd",
                    "answer": "; ".join(_parts),
                    "value": None, "steps": steps}

    # Wave 156 (Wave 153 audit book-038): regression estimate
    # — "bivariate data: x = 53, y = 28, bYX = -1.5 ...
    # Estimate Y when X = 50" uses the regression line
    # y - ybar = bYX (x - xbar). The algebra path echoed the
    # stem's x value (x = 53) instead.
    if "estimate" in ql and ("byx" in ql or "bxy" in ql):
        _qn = ql.replace("−", "-").replace("–", "-")
        _xb = re.search(r"(?<![a-z])x\s*=\s*(-?\d+(?:\.\d+)?)",
                        _qn)
        _yb = re.search(r"(?<![a-z])y\s*=\s*(-?\d+(?:\.\d+)?)",
                        _qn)
        _byx = re.search(r"byx\s*=\s*(-?\d+(?:\.\d+)?)", _qn)
        _bxy = re.search(r"bxy\s*=\s*(-?\d+(?:\.\d+)?)", _qn)
        _tx = re.search(r"estimate\s+y\s+when\s+x\s*=\s*"
                        r"(-?\d+(?:\.\d+)?)", _qn)
        _ty = re.search(r"estimate\s+x\s+when\s+y\s*=\s*"
                        r"(-?\d+(?:\.\d+)?)", _qn)
        if _xb and _yb and _byx and _tx:
            _est = float(_yb.group(1)) + float(_byx.group(1)) \
                * (float(_tx.group(1)) - float(_xb.group(1)))
            steps = [
                f"Regression line of Y on X: y - "
                f"{fmt_num(float(_yb.group(1)))} = "
                f"{fmt_num(float(_byx.group(1)))} (x - "
                f"{fmt_num(float(_xb.group(1)))})",
                f"At x = {fmt_num(float(_tx.group(1)))}: y = "
                f"{fmt_num(_est)}",
            ]
            return {"type": "statistics",
                    "op": "regression_estimate",
                    "answer": fmt_num(_est),
                    "value": float(_est), "steps": steps}
        if _xb and _yb and _bxy and _ty:
            _est = float(_xb.group(1)) + float(_bxy.group(1)) \
                * (float(_ty.group(1)) - float(_yb.group(1)))
            steps = [
                f"Regression line of X on Y: x - "
                f"{fmt_num(float(_xb.group(1)))} = "
                f"{fmt_num(float(_bxy.group(1)))} (y - "
                f"{fmt_num(float(_yb.group(1)))})",
                f"At y = {fmt_num(float(_ty.group(1)))}: x = "
                f"{fmt_num(_est)}",
            ]
            return {"type": "statistics",
                    "op": "regression_estimate",
                    "answer": fmt_num(_est),
                    "value": float(_est), "steps": steps}

    # Wave 33: ogive (cumulative frequency) median — before
    # the grouped/raw paths, which misread the cf pairs.
    _ogive = _ogive_median(ql)
    if _ogive is not None:
        return _ogive

    # Wave 32: grouped-data mean/median/mode from a text-given
    # frequency table (added last in the wave, once the Wave 31
    # deploy released this file).
    _grouped = _grouped_stats(ql)
    if _grouped is not None:
        return _grouped

    # Wave 56: mean of the first n natural / even / odd
    # numbers — a closed-form family ((n+1)/2, n+1, n). The
    # generic list path read the lone count "10" as the data
    # and could not answer at all.
    _mf56 = re.search(
        r"(?:mean|average)\s+of\s+(?:the\s+)?first\s+(\d+)\s+"
        r"(natural|even|odd)\s+numbers?", ql) or re.search(
            r"(?:mean|average)\s+of\s+(?:the\s+)?first\s+(\d+)\s+"
            r"multiples?\s+of\s+(\d+)", ql) or re.search(
            # Wave 156 (audit book-018): the multipart stem
            # form — "Find the mean of the following data
            # ... (i) The first 50 natural numbers." — puts
            # intervening words between "mean of" and the
            # "first N" phrase (each multipart segment
            # carries the stem plus one part).
            r"(?:mean|average)\s+of\b[^.]{0,60}?first\s+"
            r"(\d+)\s+(natural|even|odd)\s+numbers?", ql) \
        or re.search(
            r"(?:mean|average)\s+of\b[^.]{0,60}?first\s+"
            r"(\d+)\s+multiples?\s+of\s+(\d+)", ql)
    if _mf56:
        _n56 = int(_mf56.group(1))
        _kind56 = _mf56.group(2)
        # Wave 156: "first n multiples of k" — group 2 is the
        # multiplier k, not a kind word.
        if _kind56.isdigit():
            _k56 = int(_kind56)
            _v56 = _k56 * (_n56 + 1) / 2
            steps = [
                f"The first {_n56} multiples of {_k56} are "
                f"{_k56}, {2 * _k56}, ..., {_k56 * _n56}; "
                f"their mean is {_k56} x ({_n56} + 1)/2 "
                f"= {fmt_num(_v56)}"]
            return {"type": "statistics", "op": "mean_first_n",
                    "answer": fmt_num(_v56), "value": float(_v56),
                    "steps": steps}
        if _n56 >= 1:
            if _kind56 == "natural":
                _v56 = (_n56 + 1) / 2
                _f56 = (f"Sum of the first {_n56} natural "
                        f"numbers = {_n56}({_n56} + 1)/2, so "
                        f"mean = ({_n56} + 1)/2")
            elif _kind56 == "even":
                _v56 = float(_n56 + 1)
                _f56 = (f"The first {_n56} even numbers are "
                        f"2, 4, ..., {2 * _n56}; their mean is "
                        f"{_n56} + 1")
            else:
                _v56 = float(_n56)
                _f56 = (f"The first {_n56} odd numbers are "
                        f"1, 3, ..., {2 * _n56 - 1}; their mean "
                        f"is {_n56}")
            steps = [_f56 + f" = {fmt_num(_v56)}"]
            return {"type": "statistics", "op": "mean_first_n",
                    "answer": fmt_num(_v56), "value": float(_v56),
                    "steps": steps}

    # Wave 30: the missing value behind a stated mean ("The
    # mean of 5 numbers is 20. Four of the numbers are 18, 22,
    # 19 and 21. Find the fifth number."). The generic list-mean
    # below averaged every number in the sentence — count and
    # mean included — and answered 17.5 for that question.
    _mm = re.search(
        r"(?:mean|average)\s+of\s+(\d+)\s+(?:numbers|"
        r"observations|items|values|people|students)"
        r"\s+is\s+(\d+(?:\.\d+)?)", ql)
    if _mm:
        _n = int(_mm.group(1))
        _mean_v = float(_mm.group(2))
        _known = _extract_list(ql[_mm.end():])
        if _n >= 2 and len(_known) == _n - 1:
            _total = _n * _mean_v
            _missing = _total - sum(_known)
            steps = [
                f"Sum of all {_n} numbers = mean × count = "
                f"{fmt_num(_mean_v)} × {_n} = {fmt_num(_total)}",
                f"Sum of the known {_n - 1} numbers = "
                + " + ".join(fmt_num(v) for v in _known)
                + f" = {fmt_num(sum(_known))}",
                f"Missing number = {fmt_num(_total)} - "
                f"{fmt_num(sum(_known))} = {fmt_num(_missing)}",
            ]
            return {"type": "statistics", "op": "mean_missing",
                    "answer": fmt_num(_missing),
                    "value": float(_missing), "steps": steps}

    # Wave 33: the excluded number behind two stated means
    # ("The mean of 6 numbers is 15. If one number is
    # excluded, the mean of the remaining numbers is 14.").
    # The Wave 30 block above needs the known numbers listed;
    # this form gives only the two means, and the raw-list
    # mean answered 11.6667 for it.
    _mx2 = re.search(
        r"(?:mean|average)\s+of\s+(\d+)\s+(?:numbers|"
        r"observations|items|values|people|students)"
        r"\s+is\s+(\d+(?:\.\d+)?)", ql)
    if _mx2 and ("exclud" in ql or "remov" in ql):
        _n2 = int(_mx2.group(1))
        _mean2 = float(_mx2.group(2))
        _mr2 = re.search(
            r"remaining[^.]{0,50}?\bis\s+(\d+(?:\.\d+)?)", ql)
        if _n2 >= 2 and _mr2:
            _rem_mean = float(_mr2.group(1))
            _excl = _n2 * _mean2 - (_n2 - 1) * _rem_mean
            steps = [
                f"Sum of all {_n2} numbers = {_n2} × "
                f"{fmt_num(_mean2)} = {fmt_num(_n2 * _mean2)}",
                f"Sum of the remaining {_n2 - 1} numbers = "
                f"{_n2 - 1} × {fmt_num(_rem_mean)} = "
                f"{fmt_num((_n2 - 1) * _rem_mean)}",
                f"Excluded number = {fmt_num(_n2 * _mean2)} "
                f"- {fmt_num((_n2 - 1) * _rem_mean)} = "
                f"{fmt_num(_excl)}",
            ]
            return {"type": "statistics",
                    "op": "mean_excluded",
                    "answer": fmt_num(_excl),
                    "value": float(_excl), "steps": steps}

    # Wave 65: the TOTAL behind a stated mean — "the mean
    # of 6 numbers is 15, find their total" / "the average
    # age of 8 people is 35, find the total of their ages".
    # The generic paths averaged the count and the mean
    # themselves ((6 + 15) / 2 = 10.5). Runs after the
    # missing/excluded blocks above, which own the forms
    # that also state a list or a second mean.
    _mt65 = re.search(
        r"(?:mean|average)(?:\s+age)?\s+of\s+(\d+)\s+(?:"
        r"numbers|observations|items|values|people|students|"
        r"persons)\s+is\s+(\d+(?:\.\d+)?)", ql)
    if _mt65 and ("total" in ql or re.search(r"\bsum\b", ql)) \
            and "exclud" not in ql and "remov" not in ql:
        _n65 = int(_mt65.group(1))
        _mean65 = float(_mt65.group(2))
        _tot65 = _n65 * _mean65
        return {"type": "statistics", "op": "mean_total",
                "answer": fmt_num(_tot65),
                "value": float(_tot65),
                "steps": [
                    f"Total = mean × count = "
                    f"{fmt_num(_mean65)} × {_n65} = "
                    f"{fmt_num(_tot65)}"]}

    # Wave 65: mean / median of the first N prime numbers
    # and of the first N multiples of M — closed families
    # the generic paths could only fail or concept-fallback.
    _wn65 = {"one": 1, "two": 2, "three": 3, "four": 4,
             "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
    _fp65 = re.search(r"first\s+(\d+|one|two|three|four|five|"
                      r"six|seven|eight|nine|ten|eleven|"
                      r"twelve)\s+prime\s+numbers?", ql)
    if _fp65 and ("median" in ql or "mean" in ql
                  or "average" in ql):
        _n65 = int(_fp65.group(1)) if _fp65.group(1).isdigit() \
            else _wn65[_fp65.group(1)]
        _primes65 = []
        _cand65 = 2
        while len(_primes65) < _n65:
            if all(_cand65 % p for p in _primes65
                   if p * p <= _cand65):
                _primes65.append(_cand65)
            _cand65 += 1
        if "median" in ql:
            _s65 = sorted(_primes65)
            _v65 = _s65[_n65 // 2] if _n65 % 2 else \
                (_s65[_n65 // 2 - 1] + _s65[_n65 // 2]) / 2
            _what65 = "Median"
        else:
            _v65 = sum(_primes65) / _n65
            _what65 = "Mean"
        return {"type": "statistics", "op": "first_primes_stat",
                "answer": fmt_num(_v65), "value": float(_v65),
                "steps": [
                    f"The first {_n65} prime numbers are "
                    + ", ".join(str(p) for p in _primes65),
                    f"{_what65} = {fmt_num(_v65)}"]}
    _fm65 = re.search(r"first\s+(\d+|one|two|three|four|five|"
                      r"six|seven|eight|nine|ten|eleven|"
                      r"twelve)\s+multiples?\s+of\s+"
                      r"(\d+(?:\.\d+)?)", ql)
    if _fm65 and ("mean" in ql or "average" in ql
                  or "median" in ql):
        _n65 = int(_fm65.group(1)) if _fm65.group(1).isdigit() \
            else _wn65[_fm65.group(1)]
        _m65 = float(_fm65.group(2))
        _v65 = _m65 * (_n65 + 1) / 2
        return {"type": "statistics",
                "op": "first_multiples_mean",
                "answer": fmt_num(_v65), "value": float(_v65),
                "steps": [
                    f"The first {_n65} multiples of "
                    f"{fmt_num(_m65)} run from {fmt_num(_m65)} "
                    f"to {fmt_num(_m65 * _n65)} in an AP, so "
                    f"the mean is the middle value",
                    f"Mean = {fmt_num(_m65)} × ({_n65} + 1) / "
                    f"2 = {fmt_num(_v65)}"]}

    # Wave 59: combined mean of two groups ("the mean of 10
    # numbers is 12 and the mean of 20 numbers is 18, find
    # the combined mean") — the generic paths averaged the
    # two means (15), which is wrong unless the groups are
    # equal. Weighted by group size.
    _mc59 = re.search(
        r"mean\s+of\s+(\d+)\s+(?:numbers|observations|values)"
        r"\s+is\s+(\d+(?:\.\d+)?)\s+and\s+(?:the\s+)?mean\s+of"
        r"\s+(\d+)\s+(?:numbers|observations|values)\s+is\s+"
        r"(\d+(?:\.\d+)?)", ql)
    if _mc59 and "combined" in ql:
        _n1, _m1 = int(_mc59.group(1)), float(_mc59.group(2))
        _n2, _m2 = int(_mc59.group(3)), float(_mc59.group(4))
        _comb = (_n1 * _m1 + _n2 * _m2) / (_n1 + _n2)
        steps = [
            f"Sum of the first group = {_n1} × "
            f"{fmt_num(_m1)} = {fmt_num(_n1 * _m1)}",
            f"Sum of the second group = {_n2} × "
            f"{fmt_num(_m2)} = {fmt_num(_n2 * _m2)}",
            f"Combined mean = ({fmt_num(_n1 * _m1)} + "
            f"{fmt_num(_n2 * _m2)}) / ({_n1} + {_n2}) = "
            f"{fmt_num(_comb)}",
        ]
        return {"type": "statistics", "op": "combined_mean",
                "answer": fmt_num(_comb), "value": _comb,
                "steps": steps}
    # Wave 59: total from a stated average ("the average of
    # 5 numbers is 12, find their sum") — sum = n × mean.
    _ms59 = re.search(
        r"average\s+of\s+(\d+)\s+(?:numbers|values)\s+is\s+"
        r"(\d+(?:\.\d+)?)", ql)
    if _ms59 and ("sum" in ql or "total" in ql):
        _n59, _m59 = int(_ms59.group(1)), float(_ms59.group(2))
        _tot59 = _n59 * _m59
        return {"type": "statistics", "op": "sum_from_average",
                "answer": fmt_num(_tot59), "value": _tot59,
                "steps": [
                    f"Sum = number of values × average = "
                    f"{_n59} × {fmt_num(_m59)} = "
                    f"{fmt_num(_tot59)}"]}
    # Wave 59: P(not E) from P(E) ("if P(E) = 3/6, find
    # P(not E)") — the complement rule; salvage used to
    # guess at the fraction.
    _mp59 = re.search(r"p\(\s*([a-z])\s*\)\s*=\s*"
                      r"(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)",
                      ql)
    # Wave 156: a MULTI-relation ask (P(not A) AND P(not B)
    # AND P(A or B), audit book-052) belongs to the relations
    # schema inside _probability, which answers every asked
    # quantity; this single-complement shortcut must not
    # swallow it by answering only the first.
    _multi_rel156 = len(re.findall(r"p\(\s*not\s+[a-z]\s*\)",
                                   ql)) >= 2 or re.search(
                                       r"p\(\s*[a-z]\s*or\s*"
                                       r"[a-z]\s*\)", ql)
    if _mp59 and not _multi_rel156 and re.search(
            r"p\(\s*not\s+" + _mp59.group(1) + r"\s*\)", ql):
        from fractions import Fraction as _F59
        _pv = _F59(_mp59.group(2).replace(" ", ""))
        if 0 <= _pv <= 1:
            _nv = 1 - _pv
            return {"type": "statistics",
                    "op": "probability_not",
                    "answer": f"{_nv} ≈ {float(_nv):.4f}",
                    "value": float(_nv),
                    "steps": [
                        "P(not E) = 1 - P(E) (the complement "
                        "rule)",
                        f"= 1 - {_pv} = {_nv}"]}

    # Wave 47: a wrongly-recorded observation ("The mean of
    # 10 observations is 25. If one observation 36 was
    # wrongly recorded as 63, find the correct mean."). The
    # generic list-mean below averaged every number in the
    # sentence (10, 25, 36, 63) and answered 33.5 (Wave 35
    # audit #218; correct 22.3).
    if _mm and ("wrongly" in ql or "incorrectly" in ql
                or "mistakenly" in ql):
        _n47 = int(_mm.group(1))
        _mean47 = float(_mm.group(2))
        _bad = re.search(
            r"(\d+(?:\.\d+)?)\s+was\s+(?:wrongly|incorrectly|"
            r"mistakenly)\s+(?:recorded|written|taken|entered|"
            r"read)\s+as\s+(\d+(?:\.\d+)?)", ql)
        _right = _wrong = None
        if _bad:
            _right, _wrong = float(_bad.group(1)), \
                float(_bad.group(2))
        else:
            _bad2 = re.search(
                r"(?:recorded|written|taken|entered)\s+as\s+"
                r"(\d+(?:\.\d+)?)\s+instead\s+of\s+"
                r"(\d+(?:\.\d+)?)", ql)
            if _bad2:
                _wrong, _right = float(_bad2.group(1)), \
                    float(_bad2.group(2))
        if _right is not None:
            _total47 = _n47 * _mean47
            _corr = (_total47 - _wrong + _right) / _n47
            steps = [
                f"Sum of the {_n47} observations (with the "
                f"wrong entry) = {_n47} × {fmt_num(_mean47)} "
                f"= {fmt_num(_total47)}",
                f"Correct sum = {fmt_num(_total47)} - "
                f"{fmt_num(_wrong)} + {fmt_num(_right)} = "
                f"{fmt_num(_total47 - _wrong + _right)}",
                f"Correct mean = "
                f"{fmt_num(_total47 - _wrong + _right)} ÷ "
                f"{_n47} = {fmt_num(_corr)}",
            ]
            return {"type": "statistics",
                    "op": "mean_wrongly_recorded",
                    "answer": fmt_num(_corr),
                    "value": float(_corr), "steps": steps}

    # Wave 47: one more person joins and the mean moves
    # ("The mean weight of 8 students is 50 kg. When the
    # teacher's weight is included, the mean becomes 52 kg.
    # Find the teacher's weight."). The generic list-mean
    # averaged 8, 50 and 52 and answered 36.6667 (audit
    # #225; correct 68).
    if "includ" in ql:
        _mi = re.search(
            r"mean\s+(?:weight\s+|marks?\s+|height\s+)?of\s+"
            r"(\d+)\s+(?:students|persons|people|boys|girls|"
            r"children|men|women)\s+is\s+(\d+(?:\.\d+)?)", ql)
        _mb = re.search(r"becomes\s+(\d+(?:\.\d+)?)", ql)
        if _mi and _mb:
            _n48 = int(_mi.group(1))
            _old = float(_mi.group(2))
            _new = float(_mb.group(1))
            _person = (_n48 + 1) * _new - _n48 * _old
            _who = "teacher" if "teacher" in ql else "new person"
            steps = [
                f"Total of the {_n48} values = {_n48} × "
                f"{fmt_num(_old)} = {fmt_num(_n48 * _old)}",
                f"Total after including the {_who} = "
                f"{_n48 + 1} × {fmt_num(_new)} = "
                f"{fmt_num((_n48 + 1) * _new)}",
                f"The {_who}'s value = "
                f"{fmt_num((_n48 + 1) * _new)} - "
                f"{fmt_num(_n48 * _old)} = {fmt_num(_person)}",
            ]
            return {"type": "statistics",
                    "op": "mean_included_person",
                    "answer": fmt_num(_person) + (
                        " kg" if "kg" in ql else ""),
                    "value": float(_person), "steps": steps}

    # Wave 33: the probability gate used to be the literal
    # substring "probab" — Hindi/Hinglish asks carry
    # प्रायिकता / संभावना / sambhavna instead, and "chance"
    # asks never reached _probability at all. The experiment
    # tokens route the no-probability-word Hindi forms too;
    # _probability returns None unless it can parse an event,
    # so descriptive questions are unaffected.
    if "probab" in ql or "chance" in ql or re.search(
            r"p\(\s*[a-z]\s*\)", ql) or re.search(
            r"प्रायिकता|संभावना|sambhavna|सिक्क|पास|गेंद|पत्त|"
            r"\bsikka\b|\bsikke\b|\bpasa\b|\bpaase\b", ql):
        out = _probability(q)
        if out:
            return out

    counted = _counting(q)
    if counted:
        return counted

    # Wave 33: frequency-table mean with an unknown frequency
    # ("x: … f: …, p, …", mean given) — before the raw-list
    # mean below, which averaged the sentence's numbers.
    _freq_unk = _freq_mean_unknown(ql)
    if _freq_unk is not None:
        return _freq_unk

    # Wave 58: GEOMETRIC mean. The keyword selection below
    # sees only "mean" and answered with the ARITHMETIC mean
    # — GM of 4 and 9 came out 6.5 instead of 6 (Wave 55
    # trap). GM = (product of the numbers)^(1/n), exact when
    # the product is a perfect nth power.
    if "geometric mean" in ql or "geometric-mean" in ql:
        _gnums = _extract_list(q)
        if _gnums and len(_gnums) >= 2 \
                and all(n > 0 for n in _gnums):
            _prod = 1
            for _n in _gnums:
                _prod *= _n
            _cnt = len(_gnums)
            _root = None
            if all(float(n).is_integer() for n in _gnums):
                _iprod = 1
                for _n in _gnums:
                    _iprod *= int(_n)
                _cand = round(_iprod ** (1.0 / _cnt))
                if _cand ** _cnt == _iprod:
                    _root = float(_cand)
            _val = _root if _root is not None else \
                float(_prod) ** (1.0 / _cnt)
            steps = [
                "Geometric mean = (product of the numbers)"
                f"^(1/n) with n = {_cnt} numbers.",
                f"Product = "
                + " × ".join(fmt_num(n) for n in _gnums)
                + f" = {fmt_num(_prod)}",
                f"GM = {fmt_num(_prod)}^(1/{_cnt}) "
                f"= {fmt_num(_val)}",
            ]
            return {"type": "statistics",
                    "op": "geometric_mean",
                    "answer": fmt_num(_val), "value": _val,
                    "steps": steps}

    op = None
    # Wave 33: Hindi descriptive statistics — माध्यक /
    # माध्यिका (median) is checked before माध्य (mean):
    # the mean word is a prefix of the median word.
    if "माध्यक" in ql or "माध्यिका" in ql:
        op = "median"
    elif "बहुलक" in ql:
        op = "mode"
    elif "माध्य" in ql or "औसत" in ql:
        op = "mean"
    elif "standard deviation" in ql or re.search(r"\bstd\b", ql):
        op = "std"
    elif "variance" in ql:
        op = "variance"
    elif "median" in ql:
        op = "median"
    elif "mode" in ql:
        op = "mode"
    elif "range" in ql:
        op = "range"
    elif "mean" in ql or "average" in ql:
        op = "mean"
    if op:
        # Wave 146 (CISCE audit): the bare-keyword op choice
        # above plus the whole-text number sweep below is a
        # hijack magnet when the "data" is not a raw list at
        # all. Four narrow declines:
        if op == "mode":
            # "Mode A / Mode B / Mode C" are LABELS (attendance
            # modes in a Bayes case study), not the statistic —
            # the case parts were answered with the swept
            # percentage list, because the bare substring
            # "mode" fired on the labels. The statistic is
            # only meant when the question carries a mode-OF /
            # find-the-mode frame; label uses carry none.
            # (The router's stopword-normalised copy drops
            # label letters and prepositions, so a label-strip
            # cannot be made reliable — the frame whitelist
            # can.)
            if not re.search(
                    r"\bmode\s+of\b|\bmode\s+is\b|\bmode\s*[:=]|"
                    r"\bfind\s+(?:the\s+)?mode\b|"
                    r"\bcalculate\s+(?:the\s+)?mode\b|"
                    r"\bdetermine\s+(?:the\s+)?mode\b|"
                    r"\bka\s+mode\b|\bmode\s+(?:kya|batao)\b",
                    ql) and "बहुलक" not in ql:
                op = None
        if op == "median" and re.search(
                r"medians?\s+of\s+(?:the\s+)?"
                r"(?:triangle|∆|Δ)", ql):
            # The medians of a TRIANGLE (geometry — their
            # intersection point G) are not a data median; a
            # vectors question was answered "Median = 1" from
            # the scavenged coordinates (0, 1, 2).
            op = None
        if op in ("mean", "median", "mode", "std", "variance",
                  "range") and "[" not in q and (
                      len(re.findall(
                          r"\d+(?:\.\d+)?\s*[-–—]\s*"
                          r"\d+(?:\.\d+)?", q))
                      + len(re.findall(
                          r"\d+\s+\.\s+\d+", q))) >= 3:
            # Three or more class-interval ranges = GROUPED
            # data. The grouped handlers above own it; a raw
            # sweep would mix class bounds with frequencies
            # (the audit's grouped question was answered with
            # the std of a bounds+frequency mixture).
            op = None
        if op == "mean" and "[" not in q:
            if re.search(r"\{\s*\d", q) and (
                    "probab" in ql or "distribution" in ql
                    or "random variable" in ql):
                # The mean of a random variable's SUPPORT SET
                # ({0,1,2,3} -> 1.5) is not E(X) — every part
                # of the audit's distribution case was answered
                # 1.5 while the true mean was 2.4.
                op = None
            elif "shown in" in ql and (
                    "diagram" in ql or "figure" in ql) and \
                    "are:" not in ql and "is:" not in ql:
                # The data lives in a FIGURE ("mean of two
                # heights shown in the diagram"); the prose
                # numbers (a diameter, pi = 22/7) are not the
                # data — they were averaged into a fake mean.
                op = None
    if op:
        nums = _extract_list(q)
        # Wave 47: a colon-introduced list IS the data — the
        # sentence's own count is not ("The marks of 15
        # students are: 41, 39, ... . Find the median." — the
        # whole-sentence extraction swept the 15 in and the
        # median came out 50 instead of 52; audit #223). The
        # stated-count drop covers the same pollution when
        # there is no colon.
        _from_colon156 = False
        if "[" not in q and ":" in q:
            _after = _extract_list(q.split(":", 1)[1])
            if len(_after) >= 3:
                nums = _after
                _from_colon156 = True
        _mc = re.search(
            r"\bof\s+(\d+)\s+(?:students|observations|numbers|"
            r"items|values|persons|people)\b", ql)
        if _mc and len(nums) == int(_mc.group(1)) + 1 \
                and nums[0] == int(_mc.group(1)):
            nums = nums[1:]
        # Wave 156 (audit book-079): a colon list followed
        # by a SECOND worked data set in the same text (the
        # "your friend found the median as follows: <another
        # list>" tail of the NCERT question) — the sweep
        # merged both lists and served the median of the
        # union. When the question states the data's count
        # (15 विद्यार्थियों / of 15 students), the data is
        # exactly the first that many values of the list.
        _cnt156 = _mc or re.search(r"(\d+)\s+विद्यार्थियों", q)
        if _from_colon156 and _cnt156 \
                and len(nums) > int(_cnt156.group(1)):
            nums = nums[:int(_cnt156.group(1))]
        # For std/variance questions the numbers are the data itself.
        out = _stats_result(op, nums)
        if out:
            val, steps = out
            ans = val if not isinstance(val, list) else \
                ", ".join(fmt_num(v) for v in val)
            # Wave 156 (Wave 153 audit book-006): "calculate
            # the variance AND standard deviation" chose op
            # std and served ONLY the SD — the steps computed
            # the variance (21.84) but the answer line dropped
            # it. When both are asked, the answer names both.
            if op == "std" and re.search(r"\bvariance\b", ql):
                _var156 = _variance(nums)
                ans = (f"Variance = {fmt_num(_var156)}, "
                       f"Standard deviation = {fmt_num(val)}")
            # Wave 156 (audit book-079): median AND mode both
            # asked in Hindi ("बहुलक और माध्यक ज्ञात कीजिए")
            # — name both quantities, like the variance/SD
            # pair above.
            if op in ("median", "mode") and "बहुलक" in q \
                    and "माध्यक" in q:
                _other156 = "mode" if op == "median" \
                    else "median"
                _o156 = _stats_result(_other156, nums)
                if _o156 is not None:
                    _ov156 = _o156[0]
                    _ovs156 = _ov156 if not isinstance(
                        _ov156, list) else ", ".join(
                        fmt_num(v) for v in _ov156)
                    _lbl156 = {"median": "Median",
                               "mode": "Mode"}
                    steps = steps + _o156[1]
                    ans = (f"{_lbl156[op]} = {ans}, "
                           f"{_lbl156[_other156]} = {_ovs156}")
            return {
                "type": "statistics",
                "op": op,
                "answer": fmt_num(ans) if not isinstance(ans, str) else ans,
                "value": float(val) if not isinstance(val, list) else None,
                "steps": steps,
            }
    return {
        "type": "statistics",
        "op": "unknown",
        "answer": "Tell me the data, e.g. 'mean of 2, 4, 6' or "
                  "'probability of getting a 6 on a dice'.",
        "steps": [],
    }
