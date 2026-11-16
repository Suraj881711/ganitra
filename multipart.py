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
    return None


def multipart_result(question):
    """The multipart answer for `question`, or None — mega
    bundles and case studies first, then Hence chains."""
    out = multipart_preferred(question)
    if out is not None:
        return out
    return _hence_result(question)


__all__ = ["multipart_result", "multipart_preferred",
           "split_mega_bundle", "split_case_study",
           "split_hence"]
