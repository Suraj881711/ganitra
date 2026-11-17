"""Wave 100: multi-part paper formats — mega-MCQ bundles,
case-study sets, and "Hence, …" chains.

The Wave 93 solver-health audit found three of its seven
regressions were not missing mathematics but missing FORMAT
handling in the live chain (the formats layer designed in
Wave 82 never landed in the main tree):

  * Regression #5 — an ICSE "Choose the correct answers…"
    mega-item: FIFTEEN independent MCQs pasted as one
    message. Treated as one question, the whole-text solver
    carved a fragment out of part (iv)'s line equation and
    served "x = -2/7" as the answer (in Wave 71 that fragment
    counted as SOLVED); on the full 15-part text the stacked
    candidate solves burned past the audit's 20 s budget.
  * Regression #3 — a discus-throw case study: a passage plus
    (a)/(b)/(c) sub-questions. No layer split it, so it fell
    to NOT_FOUND (after the MCQ layer mistook the imperative
    sub-questions for options and burned ~19 s on them —
    mcq.py now refuses imperative "options" itself).
  * Regression #4 — a "Hence, …" chain: "Find the zeroes of
    p(x) = 3x² − 4x − 4. Hence, write a polynomial whose
    zeroes are 2 more than the zeroes of p(x)." The second
    sentence poisoned the first sentence's parse, and no
    layer carried part 1's result into part 2.

`multipart_result(question)` is one honest layer in
fallback.with_fallback, sitting after the MCQ layer and
before salvage; `multipart_preferred(question, result)`
sits in the real-result branch beside mcq_preferred,
because for a bundle the PARTS are the authority — a
whole-text fragment "solve" of one part's numbers is not
an answer to the bundle.

Shapes served, each only on a strict structural match:

  * Mega bundle — a consecutive roman-numeral run
    (i), (ii), (iii), … of >= 3 sub-questions, EVERY one
    carrying its own option list. Each part is answered
    through the MCQ layer (Wave 100 special schemas in a
    fast first pass, the generic machinery in a second
    pass under a soft wall-clock budget).
  * Case study — a passage cue ("based on the above
    information", "answer the following questions", "case
    study") plus >= 2 lettered sub-questions. Each
    sub-question is solved WITH the passage bound in front
    of it (the facts live there), then alone; an "OR"
    alternative inside a part is tried in order. A
    length-ask answered with an area/volume result is
    rejected as irrelevant (the passage's circle area is
    not the length of AP).
  * Hence chain — part 1 finds a polynomial's zeroes;
    part 2 asks for the polynomial whose zeroes are a
    stated transform of them (shifted by k, scaled by k,
    reciprocals, negatives). The new polynomial is built
    from the transformed sum and product, exactly.

HONESTY RULE (same as every layer since Wave 18): a part
that does not solve is marked with the one-line not-found
for that part — never a guessed option, never a similar
question's answer. If NO part solves, the layer returns
None and the existing behaviour runs byte-for-byte
unchanged.
"""

import re
import time
from fractions import Fraction

import sympy as sp

from solver.router import solve_question

# Soft wall-clock budgets for a whole bundle: the parts are
# attempted in order and anything still unsolved when the
# budget runs out is marked, not attempted — one slow part
# must not hang the whole set (the audit's timeout shape).
_MEGA_BUDGET = 30.0
_CASE_BUDGET = 25.0

_ROMAN_VALUES = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6,
    "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11,
    "xii": 12, "xiii": 13, "xiv": 14, "xv": 15,
}
_ROMAN_RE = re.compile(
    r"\((xv|xiii|xiv|xii|xi|x|ix|viii|vii|vi|iv|v|iii|ii|i)\)")
_LETTER_RE = re.compile(r"\(\s*([a-eA-E])\s*\)")
_OPTION_MARK_RE = re.compile(r"\(\s*[a-dA-D]\s*\)")

_CASE_CUE_RE = re.compile(
    r"based\s+on\s+the\s+above\s+information|"
    r"answer\s+the\s+following\s+questions|"
    r"case\s*study|प्रकरण\s+अध्ययन", re.I)


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def _consecutive_run(hits, first_value):
    """hits: [(label, value, start, end)] in text order.
    Return the longest run starting at first_value and
    stepping by 1, or None."""
    best = None
    for i, hit in enumerate(hits):
        if hit[1] != first_value:
            continue
        run = [hit]
        j = i + 1
        while j < len(hits) and hits[j][1] == run[-1][1] + 1:
            run.append(hits[j])
            j += 1
        if best is None or len(run) > len(best):
            best = run
    return best


def split_mega_bundle(question):
    """[(label, part_text), ...] for a roman-numeral bundle
    of >= 3 sub-MCQs, or None. Every part must carry its own
    option list — a run of markers without options is a
    proof's steps or a list, not a bundle of MCQs."""
    q = str(question or "")
    hits = [(m.group(1), _ROMAN_VALUES[m.group(1)],
             m.start(), m.end())
            for m in _ROMAN_RE.finditer(q)]
    run = _consecutive_run(hits, 1)
    if run is None or len(run) < 3:
        return None
    parts = []
    for i, (label, _v, _s, end) in enumerate(run):
        nxt = run[i + 1][2] if i + 1 < len(run) else len(q)
        text = q[end:nxt].strip()
        if len(text) < 8 or len(text) > 1500:
            return None
        if len(_OPTION_MARK_RE.findall(text)) < 2:
            return None
        parts.append((label, text))
    return parts


def split_case_study(question):
    """(passage, [(label, [alternative, ...]), ...]) for a
    passage + lettered sub-questions set, or None."""
    q = str(question or "")
    if not _CASE_CUE_RE.search(q):
        return None
    hits = [(m.group(1).lower(), "abcde".index(
        m.group(1).lower()), m.start(), m.end())
        for m in _LETTER_RE.finditer(q)]
    run = _consecutive_run(hits, 0)
    if run is None or len(run) < 2:
        return None
    passage = q[:run[0][2]].strip()
    if len(passage) < 20:
        return None
    parts = []
    for i, (label, _v, _s, end) in enumerate(run):
        nxt = run[i + 1][2] if i + 1 < len(run) else len(q)
        text = q[end:nxt].strip()
        if len(text) < 5 or len(text) > 900:
            return None
        alts = [a.strip() for a in re.split(
            r"\s+OR\s+|\s+अथवा\s+", text) if a.strip()]
        if not alts:
            return None
        parts.append((label, alts))
    return passage, parts


def split_hence(question):
    """(part1, part2) split at the "Hence," hinge, or None."""
    q = str(question or "").strip()
    m = re.match(r"(.+?)\.\s*Hence,?\s+(.+)$", q)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


# ---------------------------------------------------------------------------
# Solving the parts — the existing machinery, nothing parallel
# ---------------------------------------------------------------------------

def _not_found_line_for(text):
    try:
        from fallback import _looks_hindi, _not_found_line
        return _not_found_line(text, _looks_hindi(text))
    except Exception:
        return "Answer not found."


def _part_is_real(text, result):
    try:
        from mcq import _stem_is_real
        return _stem_is_real(text, result)
    except Exception:
        return False


_AREA_OPS = ("area", "volume", "surface")


def _solve_case_part(passage, alt):
    """One case-study sub-question (one OR alternative):
    passage-bound first (the facts live in the passage),
    then alone. A length-ask answered with an area/volume
    result is rejected — the passage's mensuration facts
    are not the asked length."""
    from mcq import mcq_result
    length_ask = bool(re.search(r"length\s+of", alt, re.I))
    for text in (f"{passage} {alt}", alt):
        result = None
        try:
            if _OPTION_MARK_RE.search(text):
                result = mcq_result(text)
            if result is None:
                raw = solve_question(text)
                if _part_is_real(text, raw):
                    result = raw
        except Exception:
            result = None
        if result is None:
            continue
        if length_ask and any(
                w in str(result.get("op", "")).lower()
                for w in _AREA_OPS):
            continue
        return result
    return None


def _assemble(kind, op, labels, solved, question):
    """The combined result: one answer line naming every
    solved part, steps carrying each part's own working and
    the one-line not-found for each unsolved part."""
    steps = []
    answer_bits = []
    for label in labels:
        result = solved.get(label)
        if result is None:
            steps.append(
                f"({label}) {_not_found_line_for(question)}")
            continue
        answer_bits.append(f"({label}) {result.get('answer')}")
        part_steps = result.get("steps") or []
        if part_steps:
            steps.append(f"({label}) {part_steps[0]}")
            steps.extend(str(s) for s in part_steps[1:])
        else:
            steps.append(f"({label}) {result.get('answer')}")
    return {
        "type": "Multipart",
        "op": op,
        "answer": "; ".join(answer_bits),
        "steps": steps,
        "source": "multipart",
        "multipart": {
            "kind": kind,
            "solved": [lab for lab in labels
                       if solved.get(lab) is not None],
            "total": len(labels),
        },
    }


def _mega_result(parts, question):
    from mcq import mcq_result, mcq_special_result
    deadline = time.monotonic() + _MEGA_BUDGET
    solved = {}
    # Pass 1: the fast special schemas settle most board
    # staples in milliseconds — every part gets its chance
    # before any expensive generic solve starts.
    for label, text in parts:
        try:
            result = mcq_special_result(text)
        except Exception:
            result = None
        if result is not None:
            solved[label] = result
    # Pass 2: the generic MCQ machinery for the rest, under
    # the budget.
    for label, text in parts:
        if label in solved:
            continue
        if time.monotonic() > deadline:
            break
        try:
            result = mcq_result(text)
        except Exception:
            result = None
        if result is not None:
            solved[label] = result
    if not solved:
        return None
    return _assemble("mega_bundle", "multipart_bundle",
                     [lab for lab, _t in parts], solved,
                     question)


def _case_result(passage, parts, question):
    deadline = time.monotonic() + _CASE_BUDGET
    solved = {}
    for label, alts in parts:
        result = None
        for alt in alts:
            if time.monotonic() > deadline:
                break
            result = _solve_case_part(passage, alt)
            if result is not None:
                break
        if result is not None:
            solved[label] = result
    if not solved:
        return None
    return _assemble("case_study", "multipart_case_study",
                     [lab for lab, _a in parts], solved,
                     question)


# ---------------------------------------------------------------------------
# Hence chains: zeroes of p(x) -> a transformed-zeroes polynomial
# ---------------------------------------------------------------------------

def _fr_str(f):
    f = Fraction(f)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def _quad_str_ints(a, b, c):
    from mcq import _quad_str
    return _quad_str(a, b, c)


def _hence_result(question):
    got = split_hence(question)
    if got is None:
        return None
    part1, part2 = got
    if "zero" not in part1.lower() \
            or "zero" not in part2.lower() \
            or "polynomial" not in part2.lower():
        return None
    mp = re.search(r"p\(x\)\s*=\s*(.+?)\s*$", part1) or \
        re.search(r"=\s*(.+?)\s*$", part1)
    if not mp:
        return None
    from mcq import _clean_expr_text
    from solver.expression_parser import parse_expression
    try:
        xs = sp.Symbol("x")
        expr = parse_expression(_clean_expr_text(mp.group(1)))
        poly = sp.Poly(expr, xs)
        if poly is None or poly.degree() not in (2, 3):
            return None
        zeroes = sp.solve(expr, xs)
    except Exception:
        return None
    if not zeroes or any(not z.is_rational for z in zeroes):
        return None
    zeroes = [Fraction(int(z.p), int(z.q)) for z in zeroes]
    # The transform part 2 asks for.
    low = part2.lower()
    new = None
    describe = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*more\s+than", low)
    if m:
        k = Fraction(m.group(1))
        new = [z + k for z in zeroes]
        describe = f"Add {_fr_str(k)} to each zero"
    if new is None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*less\s+than", low)
        if m:
            k = Fraction(m.group(1))
            new = [z - k for z in zeroes]
            describe = f"Subtract {_fr_str(k)} from each zero"
    if new is None and ("twice" in low or "double" in low):
        new = [2 * z for z in zeroes]
        describe = "Double each zero"
    if new is None:
        m = re.search(r"(\d+(?:\.\d+)?)\s*times", low)
        if m:
            k = Fraction(m.group(1))
            new = [k * z for z in zeroes]
            describe = f"Multiply each zero by {_fr_str(k)}"
    if new is None and "reciprocal" in low:
        if any(z == 0 for z in zeroes):
            return None
        new = [1 / z for z in zeroes]
        describe = "Take the reciprocal of each zero"
    if new is None and ("negative" in low
                        or "opposite" in low):
        new = [-z for z in zeroes]
        describe = "Negate each zero"
    if new is None:
        return None
    total = sum(new, Fraction(0))
    product = Fraction(1)
    for z in new:
        product *= z
    if len(new) == 2:
        a2, b2, c2 = Fraction(1), -total, product
    else:
        # Cubic: x^3 - S1 x^2 + S2 x - S3 from the new zeroes.
        s1 = total
        s2 = sum(new[i] * new[j]
                 for i in range(3) for j in range(i + 1, 3))
        a2 = Fraction(1)
        b2, c2 = -s1, s2
        d2 = -product
    from math import gcd as _gcd
    coeffs = [a2, b2, c2] + ([d2] if len(new) == 3 else [])
    den = 1
    for f in coeffs:
        den = den * f.denominator // _gcd(den, f.denominator)
    ints = [int(f * den) for f in coeffs]
    g = 0
    for v in ints:
        g = _gcd(g, abs(v))
    g = g or 1
    ints = [v // g for v in ints]
    if ints[0] < 0:
        ints = [-v for v in ints]
    if len(new) == 2:
        poly_str = _quad_str_ints(ints[0], ints[1], ints[2])
    else:
        poly_str = (f"{'' if ints[0] == 1 else ints[0]}x^3 "
                    f"{'+' if ints[1] >= 0 else '-'} "
                    f"{abs(ints[1])}x^2 "
                    f"{'+' if ints[2] >= 0 else '-'} "
                    f"{abs(ints[2])}x "
                    f"{'+' if ints[3] >= 0 else '-'} "
                    f"{abs(ints[3])}").replace("  ", " ")
    from solver.expression_parser import fmt as _fmt
    try:
        factored = _fmt(sp.factor(expr))
        poly_text = _fmt(expr)
    except Exception:
        factored, poly_text = "", mp.group(1)
    z_old = " and ".join(_fr_str(z) for z in zeroes)
    z_new = " and ".join(_fr_str(z) for z in new)
    steps = [
        f"Factorise: {poly_text} = {factored}" if factored
        else f"Solve {poly_text} = 0.",
        f"Zeroes of the polynomial are {z_old}.",
        f"{describe}: the new zeroes are {z_new}.",
        f"Sum of the new zeroes = {_fr_str(total)}, "
        f"product = {_fr_str(product)}.",
        f"The required polynomial is {poly_str}.",
    ]
    if len(new) == 3:
        steps[3] = (f"Sums of the new zeroes: S1 = "
                    f"{_fr_str(s1)}, S2 = {_fr_str(s2)}, "
                    f"product = {_fr_str(product)}.")
    return {
        "type": "Multipart",
        "op": "hence_chain",
        "answer": f"Zeroes are {z_old}; the required "
                  f"polynomial is {poly_str}",
        "steps": steps,
        "source": "multipart",
        "multipart": {"kind": "hence_chain", "solved": ["1"],
                      "total": 1},
    }


# ---------------------------------------------------------------------------
# Wave 141: general multi-part questions
#
# The Wave 100 shapes above are strict paper formats (MCQ
# bundles, cued case studies, Hence chains). The Wave 135
# NCERT audit found the much larger ordinary family failing:
# book questions that carry 2+ plain sub-parts — (i)/(ii)/
# (iii), (a)/(b)/(c), (क)/(ख)/(ग), (1)/(2), Part 1/Part 2,
# Q1/Q2, numbered 1./2. asks, and unlabelled semicolon- or
# newline-separated asks — under one shared stem ("Find the
# value of the polynomial 5x - 4x^2 + 3 at (i) x = 0
# (ii) x = -1 (iii) x = 2"). Treated as one blob, the whole
# text solves nothing; split, most parts solve at once.
#
# split_general() is deliberately suspicious: every segment
# must look like an ask (its own verb / '=' / '?', a set /
# sequence / expression, or a noun-phrase part under a
# commanding preamble), a bare value is never a part (that
# is an MCQ's option list, the MCQ layer's territory), a
# pure-expression segment counts only under a compute
# preamble (a "which expression describes…" stem must not
# have its options evaluated), Assertion–Reason and OR
# bundles are deferred to formats.py, Hence chains to the
# layer above, and mega/case shapes have already had their
# turn by the time this runs. If NO part solves, the layer
# returns None and the existing behaviour runs byte-for-byte
# unchanged — the same honesty rule as every layer since
# Wave 18. At most 5 parts are answered; further parts are
# named in one plain line, never silently dropped.
# ---------------------------------------------------------------------------

_GENERAL_BUDGET = 25.0
_GENERAL_MAX_PARTS = 5

# Deploy-28 merge (Wave 141 x Wave 146): an explicit
# choose-from-options instruction ("Choose the correct
# answers ... from the given options") marks the labelled
# segments as MCQ OPTIONS, never as sub-parts — splitting
# them "solves" each option as if it were a question and
# serves candidate answers as results (the CISCE audit's
# paint-mixture MCQ: options (a)-(d) are assignments of the
# very a, b, c the stem asks for). The MCQ layer owns such
# questions; this layer must not split them.
_MCQ_INSTRUCTION_RE = re.compile(
    r"\b(?:choose|select|tick|pick)\b[^.]{0,60}?\bcorrect\b"
    r"|\bcorrect\b[^.]{0,40}?\boptions?\b"
    r"|सही\s+विकल्प\s+चुन|सही\s+उत्तर\s+चुन", re.I)

_GEN_LETTER_RE = re.compile(r"\(\s*([a-h])\s*\)")
_GEN_DEV_RE = re.compile(r"\(\s*(क|ख|ग|घ|ङ)\s*\)")
_GEN_DEV_ORDER = "कखगघङ"
_GEN_PARENNUM_RE = re.compile(r"\(\s*(\d{1,2})\s*\)")
_GEN_PART_RE = re.compile(r"(?i)\bpart\s*[-–—]?\s*(\d{1,2})\b")
_GEN_Q_RE = re.compile(r"(?<![A-Za-z])[Qq]\s*(\d{1,2})\s*[.):]")
_GEN_NUM_MARK_RE = re.compile(r"(\d{1,2})[.)]\s+")

_ASK_VERB_RE = re.compile(
    r"\b(find|solve|evaluate|calculate|compute|prove|show|"
    r"determine|simplify|factorise|factorize|rationalise|"
    r"rationalize|expand|express|write|state|check|verify|"
    r"justify|convert|draw|plot|construct|derive|obtain|"
    r"describe|explain|represent|complete|arrange|classify|"
    r"identify|mention|list|give|name|fill|mark|read|match|"
    r"count|measure|predict|examine|batao|bataao|nikalo|"
    r"likho|jodo|ghatayo|gyat)\b"
    r"|ज्ञात|सिद्ध|लिखिए|लिखो|बताइए|बताओ|निकाल|जाँच|परिकलित",
    re.I)
_COMPUTE_VERB_RE = re.compile(
    r"\b(find|calculate|evaluate|compute|simplify|solve)\b"
    r"|ज्ञात|परिकलित", re.I)
_MATHS_HINT_RE = re.compile(r"[\d^√∫=<>%{}]|\\b[xyz]\b")
_EXPR_SEQ_RE = re.compile(
    r"\{[^}]*\}|√|\^|∈|\d+\s*,\s*[-–—+]?\s*\d+\s*,")
_PURE_EXPR_RE = re.compile(r"^[\d\s+\-*/×÷().,^]+$")
_BARE_VALUE_RE = re.compile(
    r"^[-+]?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
    r"(?:\s*(?:cm|mm|km|m|cm²|cm2|m²|m2|mm²|km²|%|₹|"
    r"rs\.?|sq\.?\s*cm))?$", re.I)
_TRAILING_CONJ_RE = re.compile(r"\s+(and|aur|तथा|और)\s*$", re.I)


def _gen_segments(q, run):
    """(preamble, [(label, text), ...]) from a marker run."""
    preamble = q[:run[0][2]].strip()
    parts = []
    for i, (label, _v, _s, end) in enumerate(run):
        nxt = run[i + 1][2] if i + 1 < len(run) else len(q)
        text = q[end:nxt].strip(" \t\n.,;:।")
        text = _TRAILING_CONJ_RE.sub("", text).strip()
        parts.append((label, text))
    return preamble, parts


_GEN_STOPWORDS = {
    "and", "or", "the", "a", "an", "of", "in", "on", "for",
    "to", "aur", "तथा", "और", "का", "की", "के",
}
# The shared-data tail of the "divided by (a) 10, (b) 5,
# (c) 2. 78, 99, 173, …" shape: the last segment is a value
# followed by the data list every part works on. An MCQ's
# option list never carries one, which is what licenses the
# bare-value relaxation in _gen_segment_ok below.
_GEN_DATA_TAIL_RE = re.compile(
    r"^\S{1,12}\s*[.:]\s*(?:\d+\s*,\s*){2,}\d+")


def _gen_segment_ok(seg, preamble, preamble_has_verb,
                    any_digit, allow_bare=False):
    """One segment's ask-plausibility — see the section
    header for the rules each clause enforces."""
    s = (seg or "").strip(" .।,;:")
    if _BARE_VALUE_RE.match(s):
        # A bare value is an MCQ option — never a part —
        # unless the run ends in a shared data list, where
        # the values are the parts' own inputs (divisors).
        # (Checked before the length gate: a divisor part
        # can be a single digit.)
        return allow_bare
    if len(s) < 3 or len(s) > 1500:
        return False
    if _ASK_VERB_RE.search(s) or "=" in s or "?" in s:
        return True
    if _EXPR_SEQ_RE.search(s):
        return True
    s_expr = re.sub(r"(\d)\s*x\s*(?=\d)", r"\1×", s)
    if _PURE_EXPR_RE.match(s_expr) \
            and any(c in s_expr for c in "+-*/×÷^"):
        # A bare expression is a part only when the stem
        # commands a computation ("Calculate: (a) 2 × 50");
        # under a "which expression…" stem it is an option.
        # (The x between two digits is a multiplication
        # sign, not the variable.)
        return bool(preamble and _COMPUTE_VERB_RE.search(preamble))
    if preamble_has_verb and any_digit:
        # A noun-phrase part under a commanding stem —
        # "(i) area and (ii) perimeter of a rectangle with
        # length 5 cm…", "(i) its area (ii) its perimeter".
        # The numbers live in the shared context; the part
        # itself is just the quantity's name, so it needs
        # one real content word, and must either stay short
        # ("its area") or carry data of its own ("perimeter
        # of a rectangle with length 5 cm…" — the part that
        # carries the shared context for its siblings).
        words = re.findall(r"[^\W\d_]+", s.lower())
        if any(len(w) >= 3 and w not in _GEN_STOPWORDS
               for w in words) and (
                len(words) <= 6
                or any(c.isdigit() for c in s)):
            return True
    return False


def _gen_valid_split(preamble, parts, strong=False):
    """Every segment must pass, or there is no split (the
    Wave 100 all-or-nothing gate). `strong` (numbered and
    Q-block families, whose markers also occur inside
    ordinary prose) demands each segment carry its own verb,
    '=' or '?'."""
    if len(parts) < 2 or len(preamble) > 1200:
        return False
    preamble_has_verb = bool(_ASK_VERB_RE.search(preamble))
    any_digit = any(c.isdigit() for c in preamble) or any(
        c.isdigit() for _l, t in parts for c in t)
    allow_bare = bool(_GEN_DATA_TAIL_RE.match(parts[-1][1]))
    for _label, text in parts:
        if strong and not (_ASK_VERB_RE.search(text)
                           or "=" in text or "?" in text):
            return False
        if not _gen_segment_ok(text, preamble,
                               preamble_has_verb, any_digit,
                               allow_bare=allow_bare):
            return False
    return True


def _gen_from_run(q, hits, first_value, strong=False):
    run = _consecutive_run(hits, first_value)
    if run is None or len(run) < 2:
        return None
    preamble, parts = _gen_segments(q, run)
    if not _gen_valid_split(preamble, parts, strong=strong):
        return None
    return preamble, parts


def _split_gen_roman(q):
    hits = [(m.group(1), _ROMAN_VALUES[m.group(1)],
             m.start(), m.end()) for m in _ROMAN_RE.finditer(q)]
    return _gen_from_run(q, hits, 1)


def _split_gen_letter(q):
    hits = [(m.group(1).lower(),
             "abcdefgh".index(m.group(1).lower()),
             m.start(), m.end())
            for m in _GEN_LETTER_RE.finditer(q)]
    return _gen_from_run(q, hits, 0)


def _split_gen_dev(q):
    hits = [(m.group(1), _GEN_DEV_ORDER.index(m.group(1)),
             m.start(), m.end())
            for m in _GEN_DEV_RE.finditer(q)]
    return _gen_from_run(q, hits, 0)


def _split_gen_parennum(q):
    hits = [(m.group(1), int(m.group(1)), m.start(), m.end())
            for m in _GEN_PARENNUM_RE.finditer(q)]
    return _gen_from_run(q, hits, 1)


def _split_gen_part(q):
    hits = [(m.group(1), int(m.group(1)), m.start(), m.end())
            for m in _GEN_PART_RE.finditer(q)]
    return _gen_from_run(q, hits, 1)


def _split_gen_qblock(q):
    hits = [(m.group(1), int(m.group(1)), m.start(), m.end())
            for m in _GEN_Q_RE.finditer(q)]
    return _gen_from_run(q, hits, 1, strong=True)


def _split_gen_numbered(q):
    hits = []
    for m in _GEN_NUM_MARK_RE.finditer(q):
        start = m.start()
        if start >= 2 and q[start - 1] == "." \
                and q[start - 2].isdigit():
            continue  # a decimal's tail, not a marker
        prefix = q[:start].rstrip()
        if prefix and prefix[-1] not in "\n.;:।":
            continue  # mid-sentence number, not a boundary
        hits.append((m.group(1), int(m.group(1)),
                     start, m.end()))
    got = _gen_from_run(q, hits, 1, strong=True)
    if got is None:
        return None
    preamble = got[0]
    if preamble and not preamble.endswith((":", "?")) \
            and not _ASK_VERB_RE.search(preamble):
        return None  # "Fig. 1. … 2. …" prose, not a question set
    return got


def _split_gen_unlabelled(q):
    """Semicolon- / newline-separated distinct asks with no
    labels: every segment must carry its OWN ask verb and
    its OWN digit (a word problem's clauses fail both)."""
    if _ROMAN_RE.search(q) or _GEN_LETTER_RE.search(q) \
            or _GEN_PARENNUM_RE.search(q):
        return None  # a labelled shape owns labels, not this
    segs = [s.strip(" .।,;:") for s in re.split(r"[;\n]+", q)]
    segs = [s for s in segs if s]
    if len(segs) < 2 or len(segs) > 5:
        return None
    for s in segs:
        if len(s) < 12 or len(s) > 1200:
            return None
        if not _ASK_VERB_RE.search(s):
            return None
        if not any(c.isdigit() for c in s):
            return None
    labels = ["i", "ii", "iii", "iv", "v"]
    return "", [(labels[i], s) for i, s in enumerate(segs)]


def split_general(question):
    """(preamble, [(label, part_text), ...]) for an ordinary
    multi-part question, or None. Families run from the most
    explicit markers to the least; the first valid split
    wins. Split-level vetoes defer Assertion–Reason and OR
    bundles to formats.py and Hence chains to the layer
    above, exactly as the chain's order implies."""
    q = str(question or "")
    if len(q) < 12 or len(q) > 4000:
        return None
    if _CASE_CUE_RE.search(q):
        return None  # case-study machinery owns these
    if _MCQ_INSTRUCTION_RE.search(q):
        return None  # options are not parts (see above)
    low = q.lower()
    if "assertion" in low and "reason" in low:
        return None
    if split_hence(q) is not None:
        return None
    try:
        from formats import extract_ar, extract_or
        if extract_ar(q) is not None \
                or extract_or(q) is not None:
            return None
    except Exception:
        pass
    for splitter in (_split_gen_roman, _split_gen_letter,
                     _split_gen_dev, _split_gen_parennum,
                     _split_gen_part, _split_gen_qblock,
                     _split_gen_numbered, _split_gen_unlabelled):
        try:
            got = splitter(q)
        except Exception:
            got = None
        if got is not None:
            return got
    return None


def _gen_tail_clause(parts):
    """The shared context that trails the LAST part of the
    "(i) area and (ii) perimeter of a rectangle with length
    5 cm…" shape: the digit-bearing clause from the last
    segment's first of/for/with/whose, bound into the
    earlier parts that carry no digit of their own."""
    if len(parts) < 2:
        return None
    last = parts[-1][1]
    for m in re.finditer(r"\b(of|for|with|whose)\b", last, re.I):
        clause = last[m.start():].strip()
        if len(clause) >= 10 and any(c.isdigit() for c in clause):
            return clause
    return None


def _gen_data_tail(parts):
    """The shared data list trailing the last part of the
    "divided by (a) 10, (b) 5, (c) 2. 78, 99, …" shape,
    or None."""
    if len(parts) < 2:
        return None
    m = re.match(r"^\S{1,12}\s*[.:]\s*"
                 r"((?:\d+\s*,\s*){2,}\d+.*)$",
                 parts[-1][1], re.S)
    return m.group(1).strip() if m else None


_VERDICT_ASK_RE = re.compile(r"\bwhether\b", re.I)
_VERDICT_ANSWER_RE = re.compile(
    r"\b(yes|no|true|false)\b|हाँ|नहीं|सही है|गलत है", re.I)
_VERDICT_OP_HINTS = ("whether", "check", "verif", "valid",
                     "identity", "is_")


def _verdict_ok(result):
    """For a "check whether…" stem, a part counts only when
    its answer IS a verdict — an equation's solution set is
    not an answer to a yes/no check (the NCERT "Check
    whether the following are quadratic equations" set was
    served cubic roots before this guard)."""
    if _VERDICT_ANSWER_RE.search(str(result.get("answer")
                                     or "")):
        return True
    op = str(result.get("op") or "")
    return any(h in op for h in _VERDICT_OP_HINTS)


def _solve_general_part(preamble, part, tail_clause, deadline,
                        data_tail=None, verdict_ask=False):
    """One general sub-part through the existing machinery:
    preamble-bound first (the facts and the command usually
    live in the stem), then alone, then — for a verb-less
    stem — with the command supplied, then with the shared
    trailing clause bound in; OR alternatives inside the
    part are tried last, in order. Option-carrying parts go
    through the MCQ layer, as in the case-study path."""
    candidates = []

    def add(text):
        text = (text or "").strip()
        if text and text not in candidates:
            candidates.append(text)

    bound = f"{preamble} {part}".strip() if preamble else part
    add(bound)
    add(part)
    if data_tail and _BARE_VALUE_RE.match(
            part.strip(" .।,;:")):
        # A divisor-style bare part gets the shared data
        # list appended: "… divided by 10. 78, 99, 173, …"
        add(f"{bound}. {data_tail}")
        add(f"{part}. {data_tail}")
    if preamble and not _ASK_VERB_RE.search(part) \
            and not _ASK_VERB_RE.search(preamble):
        add(f"{preamble} Find {part}")
    if tail_clause and not any(c.isdigit() for c in part):
        add(f"{part} {tail_clause}")
        if preamble:
            add(f"{preamble} {part} {tail_clause}")
    alts = [a.strip() for a in re.split(
        r"\s+OR\s+|\s+अथवा\s+", part) if a.strip()]
    if len(alts) > 1:
        for alt in alts:
            add(f"{preamble} {alt}".strip() if preamble else alt)
            add(alt)
    for text in candidates:
        if time.monotonic() > deadline:
            return None
        result = None
        try:
            if len(_OPTION_MARK_RE.findall(text)) >= 2:
                from mcq import mcq_result
                result = mcq_result(text)
            if result is None:
                raw = solve_question(text)
                if _part_is_real(text, raw):
                    result = raw
        except Exception:
            result = None
        if result is not None and verdict_ask \
                and not _verdict_ok(result):
            result = None  # a solve is not a verdict
        if result is not None:
            return result
    return None


def _gen_cap_note(question):
    try:
        from fallback import _flavour
        flavour = _flavour(question)
    except Exception:
        flavour = "en"
    if flavour == "dev":
        return ("केवल पहले 5 भागों के उत्तर दिए गए हैं — "
                "बाकी भाग अलग से पूछें।")
    if flavour == "roman":
        return ("Sirf pehle 5 parts ke answer diye gaye "
                "hain — baaki parts alag se puchho.")
    return ("Only the first 5 parts are answered here — "
            "please ask the remaining parts separately.")


def general_multipart_result(question):
    """The general multi-part answer for `question`, or
    None — None unless the question splits AND at least one
    part verifiably solves (the honesty rule: a set with no
    solved part keeps today's behaviour byte-for-byte)."""
    got = split_general(question)
    if got is None:
        return None
    preamble, parts = got
    shown = parts[:_GENERAL_MAX_PARTS]
    tail_clause = _gen_tail_clause(parts)
    data_tail = _gen_data_tail(parts)
    verdict_ask = bool(_VERDICT_ASK_RE.search(preamble))
    deadline = time.monotonic() + _GENERAL_BUDGET
    solved = {}
    for label, text in shown:
        result = _solve_general_part(preamble, text,
                                     tail_clause, deadline,
                                     data_tail=data_tail,
                                     verdict_ask=verdict_ask)
        if result is not None:
            solved[label] = result
    if not solved:
        return None
    out = _assemble("general", "multipart_general",
                    [lab for lab, _t in shown], solved,
                    question)
    if len(parts) > _GENERAL_MAX_PARTS:
        out["steps"] = list(out.get("steps") or []) + [
            _gen_cap_note(question)]
        out["multipart"]["truncated"] = True
        out["multipart"]["parts_total"] = len(parts)
    return out


# ---------------------------------------------------------------------------
# The layer's two entry points (fallback.py calls both lazily)
# ---------------------------------------------------------------------------

def multipart_preferred(question, result=None):
    """The multipart answer when the question IS a bundle —
    for the real-result branch of with_fallback, where a
    whole-text fragment 'solve' must not stand for the set.
    Mega bundles and case studies only (a Hence chain's
    whole-text result is a failure anyway, so the fall-
    through layer below is its home)."""
    parts = split_mega_bundle(question)
    if parts is not None:
        return _mega_result(parts, question)
    cs = split_case_study(question)
    if cs is not None:
        return _case_result(cs[0], cs[1], question)
    # Wave 141: ordinary multi-part questions (plain
    # sub-parts under one stem) — the parts are the
    # authority here too, for the same reason as the
    # Wave 100 shapes.
    return general_multipart_result(question)


def multipart_result(question):
    """The multipart answer for `question`, or None — mega
    bundles and case studies first, then Hence chains."""
    out = multipart_preferred(question)
    if out is not None:
        return out
    return _hence_result(question)


__all__ = ["multipart_result", "multipart_preferred",
           "split_mega_bundle", "split_case_study",
           "split_hence", "split_general",
           "general_multipart_result"]
