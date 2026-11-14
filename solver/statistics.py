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
_HI_FACE = r"(चित|पट|chit|pat|heads?|tails?)"


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
    # Both / all of a face ("दोनों पट", "sabhi chit")
    if re.search(r"दोनों|\bdono\b|सभी|\bsabhi\b", qn):
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
    m = re.search(_HI_NUM + r"\s*से\s*(?:बड़ी|बड़ा|अधिक)\s*"
                  r"(?:संख्या|sankhya|number)?", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        return [f for f in range(1, 7) if f > k], \
            f"a number greater than {k}"
    m = re.search(_HI_NUM + r"\s*से\s*(?:छोटी|छोटा|कम)\s*"
                  r"(?:संख्या|sankhya|number)?", qn)
    if m:
        k = _hi_num(re.search(_HI_NUM, m.group(0)).group(0))
        return [f for f in range(1, 7) if f < k], \
            f"a number less than {k}"
    if re.search(r"सम\s*(?:संख्या|sankhya)|\bsam\s+sankhya\b|"
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
    if re.search(r"पास|pasa|paase", qn):
        two = re.search(r"(?:दो|\bdo\b|\b2\b)\s*(?:पासे|पासों|"
                        r"pasa|paase|dice)", qn) or \
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
    if "coin" in ql and ("toss" in ql or "throw" in ql
                         or "flip" in ql):
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
        if _mc:
            _n = _cnt(_mc.group(1))
        elif re.search(r"\ba\s+pair\s+of\s+coins?\b", ql):
            _n = 2
        elif re.search(r"\btossed\s+twice\b", ql):
            _n = 2
        else:
            _mr = re.search(r"\bin\s+" + _num + r"\s+tosses\b",
                            ql)
            _n = _cnt(_mr.group(1)) if _mr else 1
        if 1 <= _n <= 5:
            outcomes = list(_iproduct("HT", repeat=_n))
            _ev = None
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
            ]
            for _pat, _fn in _specs:
                _m = re.search(_pat, ql)
                if _m:
                    _k = _cnt(_m.group(1))
                    _ev = ((lambda fn, k: lambda h: fn(h, k))
                           (_fn, _k), _m.group(0))
                    break
            if _ev is None:
                if "both heads" in ql or "all heads" in ql:
                    _ev = (lambda h, n=_n: h == n, "all heads")
                elif "both tails" in ql or "all tails" in ql:
                    _ev = (lambda h: h == 0, "all tails")
                elif "no head" in ql:
                    _ev = (lambda h: h == 0, "no head")
                elif "no tail" in ql:
                    _ev = (lambda h, n=_n: h == n, "no tail")
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
    if "coin" in ql and "head" in ql:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "heads is 1 of them."])
    if "coin" in ql and "tail" in ql:
        return _prob_answer(Fraction(1, 2),
                            ["A fair coin has 2 equally likely outcomes; "
                             "tails is 1 of them."])

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
    if "ball" in ql:
        counts = {}
        for num, colour in re.findall(
            r"(\d+)\s+(red|blue|green|yellow|black|white|orange|pink|"
            r"purple|brown)\s*(?:balls?)?", ql
        ):
            counts[colour] = counts.get(colour, 0) + int(num)
        m = re.search(r"(red|blue|green|yellow|black|white|orange|pink|"
                      r"purple|brown)\s+ball", ql.split("probab")[-1])
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
            nums = [int(v) for v in re.findall(r"\d+", q)]
            if len(nums) < 2:
                return None
            n, r = nums[0], nums[1]
        else:
            n, r = int(m.group(1)), int(m.group(2))
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
    if m or "combination" in ql or "choose" in ql:
        if not m:
            mm = re.search(r"choose\s+(\d+)\s+from\s+(\d+)", ql) or \
                re.search(r"(\d+)\s+(?:taken|from)\s+(\d+)", ql)
            if mm:
                if "choose" in ql and mm.re.pattern.startswith("choose"):
                    r, n = int(mm.group(1)), int(mm.group(2))
                else:
                    n, r = int(mm.group(1)), int(mm.group(2))
            else:
                nums = [int(v) for v in re.findall(r"\d+", q)]
                if len(nums) < 2:
                    return None
                n, r = nums[0], nums[1]
        else:
            n, r = int(m.group(1)), int(m.group(2))
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

    # Wave 30: the missing value behind a stated mean ("The
    # mean of 5 numbers is 20. Four of the numbers are 18, 22,
    # 19 and 21. Find the fifth number."). The generic list-mean
    # below averaged every number in the sentence — count and
    # mean included — and answered 17.5 for that question.
    _mm = re.search(
        r"mean\s+of\s+(\d+)\s+(?:numbers|observations|items|"
        r"values)\s+is\s+(\d+(?:\.\d+)?)", ql)
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
        r"mean\s+of\s+(\d+)\s+(?:numbers|observations|items|"
        r"values)\s+is\s+(\d+(?:\.\d+)?)", ql)
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

    # Wave 33: the probability gate used to be the literal
    # substring "probab" — Hindi/Hinglish asks carry
    # प्रायिकता / संभावना / sambhavna instead, and "chance"
    # asks never reached _probability at all. The experiment
    # tokens route the no-probability-word Hindi forms too;
    # _probability returns None unless it can parse an event,
    # so descriptive questions are unaffected.
    if "probab" in ql or "chance" in ql or re.search(
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
        nums = _extract_list(q)
        # For std/variance questions the numbers are the data itself.
        out = _stats_result(op, nums)
        if out:
            val, steps = out
            ans = val if not isinstance(val, list) else \
                ", ".join(fmt_num(v) for v in val)
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
