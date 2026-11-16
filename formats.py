"""Wave 82: paper formats — OR bundles, Assertion–Reason,
case-study sets.

The Wave 71 solver-health audit found ~19 papers-sample
failures that are not missing mathematics but missing FORMAT
handling: board papers paste three shapes into one chat
message that the solver, the bank and the MCQ layer (Wave 76,
which deliberately left these out of scope) cannot use:

  * OR bundles — "Solve A OR Solve B" (Hindi: "… अथवा …"):
    two alternative questions; the student must answer ONE.
  * Assertion–Reason — a claim A, a claim R, and the standard
    four options about their truth and whether R explains A.
  * Case-study sets — a passage plus labelled sub-questions
    (i)/(ii)/(iii) that are meaningless without the passage.

`formats_result(question)` is one more honest layer in
fallback.with_fallback, sitting after the MCQ layer and
before salvage. Its companion `formats_preferred(question,
result)` sits in the real-result branch beside
mcq_preferred: for these two formats the parts are the
authority over a whole-text fragment "solve":

  * OR: split the alternatives, solve each through the
    existing machinery (solver.router.solve_question — no
    parallel solver). Exactly one solves -> serve it,
    labelled as the solved alternative. Both solve -> serve
    the FIRST with a note that the other also has a solution.
    Neither solves -> None, existing behaviour unchanged.
  * Assertion–Reason: only the COMPUTABLE subset. Each
    statement's truth must be settled by a decider in this
    module (a linear-pair consistency claim, the standard
    ratio conditions, square-root irrationality, linear
    functions on Z, the direction-cosine facts, or a plain
    value claim the solver itself settles). The "R explains
    A" judgement is made only when a structural link exists
    (R states the very condition A's verification used, or
    the direction-cosine pair) or the two statements are
    clearly independent facts; anything else falls through.
    An A–R option is NEVER guessed.
  * Case study: split passage from sub-questions, solve each
    sub-question independently (with a conservative passage
    binder for the "function defined in the passage + a point
    it passes through" pattern, which is what makes the
    sub-questions solvable at all). Solved parts are served
    in order; an unsolved part is marked with the one-line
    not-found for that part. If NO part solves -> None.

HONESTY RULE (same as every layer since Wave 18): any doubt
returns None and the pre-Wave-82 behaviour runs byte-for-byte
unchanged.
"""

import re
from fractions import Fraction

import sympy

import mcq
from solver.expression_parser import parse_expression
from solver.router import solve_question

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_HINGLISH_MARKERS = {
    "kya", "hai", "ka", "ki", "ke", "ko", "se", "mein", "aur",
    "batao", "nikalo", "kitna", "kitne", "hoga", "chahiye",
}


def _flavour(text):
    """The question's script flavour — "dev" (Devanagari),
    "roman" (Hinglish) or "en" — mirroring fallback._flavour,
    which this module cannot import at top level (fallback
    imports this module, lazily, from inside with_fallback)."""
    q = str(text or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return "dev"
    words = set(re.findall(r"[a-z]+", q.lower()))
    return "roman" if words & _HINGLISH_MARKERS else "en"


def _not_found_line(text):
    from fallback import _NOT_FOUND_LINES
    return _NOT_FOUND_LINES[_flavour(text)]


def _ascii_fold(s):
    return (str(s or "")
            .replace("−", "-").replace("–", "-")
            .replace("—", "-").replace("×", "*")
            .replace("÷", "/").replace("′", "'"))


# ---------------------------------------------------------------------------
# Solving one part through the existing machinery
# ---------------------------------------------------------------------------

def _part_candidates(part):
    """Forms of a part to feed solve_question, most faithful
    first: the part as written, its ASCII-folded form, mcq's
    lightly cleaned stem, the tail after a prose colon
    ("हल कीजिए : <system>"), and a "find the value" retry."""
    cands = []

    def add(c):
        c = (c or "").strip()
        if c and c not in cands:
            cands.append(c)

    add(part)
    add(_ascii_fold(part))
    add(mcq._clean_stem(part))
    m = re.search(r"[:：]", part)
    if m:
        head, tail = part[:m.start()], part[m.end():]
        if not any(ch.isdigit() for ch in head) and "=" not in head:
            add(tail)
            add(_ascii_fold(tail))
    add(part + " find the value")
    # Deliberately NOT salvage's embedded-expression
    # candidates: those extract a fragment of the part and
    # "solve" that (a case-study part asking for
    # sin^-1(-1/2) - sin^-1(1) came back as just sin^-1(1)).
    # A part counts as solved only when a faithful form of
    # the WHOLE part solves.
    return cands


_EQ_SPLIT = re.compile(r",|;|\n| और | and ")
_MATHS_TAIL = re.compile(r"[0-9a-zA-Z\s+\-*/^().]+$")


def _maths_tail(side):
    """The maths expression at the end of an equation side,
    with any prose head cut away ("हल कीजिए : x + 2y + 3z"
    -> "x + 2y + 3z"). Devanagari prose and the colon are
    outside the maths character class, so the trailing run
    of maths characters is exactly the expression; a side
    that is already pure maths is returned whole."""
    m = _MATHS_TAIL.search(side or "")
    return m.group(0).strip() if m else side


def _equations_in(text):
    """The (lhs, rhs) pairs of the plain equations written in
    a text — used to recognise system-shaped parts."""
    eqs = []
    for chunk in _EQ_SPLIT.split(_ascii_fold(text)):
        chunk = chunk.strip(" .।")
        if chunk.count("=") == 1:
            lhs, rhs = (p.strip() for p in chunk.split("="))
            lhs, rhs = _maths_tail(lhs), _maths_tail(rhs)
            if re.search(r"[a-z]", lhs + rhs) and \
                    any(ch.isdigit() for ch in lhs + rhs):
                eqs.append((lhs, rhs))
    return eqs


def _assignments(result):
    """The {variable: Fraction} assignments an answer string
    claims ("x = 19/5, y = 6/5"), or None."""
    out = {}
    for var, val in re.findall(
            r"([a-zA-Z])\s*=\s*(-?\d+(?:\.\d+)?"
            r"(?:\s*/\s*\d+)?)",
            str((result or {}).get("answer", ""))):
        num = mcq._as_number(mcq._clean(val))
        if num is None:
            return None
        out[var.lower()] = num
    return out or None


def _verify_system(part, result):
    """Substitution check for system-shaped parts: a result
    that claims values for the variables must satisfy EVERY
    equation written in the part. This is what rejects the
    router's occasional partial subsystem answer (the Hindi-
    prefixed 3-equation system that "solves" to y = 0, z = 2).
    Non-system parts return True (nothing to verify)."""
    eqs = _equations_in(part)
    if len(eqs) < 2:
        return True
    variables = set()
    for lhs, rhs in eqs:
        variables |= set(re.findall(r"[a-z]", lhs + rhs))
    if len(variables) < 2:
        return True
    assigns = _assignments(result)
    if not assigns:
        return False
    try:
        subs = {sympy.Symbol(v): sympy.Rational(
                    n.numerator, n.denominator)
                for v, n in assigns.items()}
        for lhs, rhs in eqs:
            expr = parse_expression(lhs) - parse_expression(rhs)
            if not set(expr.free_symbols) <= set(subs):
                return False
            if sympy.simplify(expr.subs(subs)) != 0:
                return False
    except Exception:
        return False
    return True


def _part_sanity(part, result):
    """Reject vacuous "solves" of a part: a bare single letter
    as the whole answer ("Find the value of a" -> "a"), and a
    derivative ask answered by something that is not a
    derivative result ("Find f'(x) at x = 1" -> "x = 1")."""
    ans = str((result or {}).get("answer", "") or "").strip()
    if re.fullmatch(r"[a-zA-Z]", ans):
        return False
    # An unevaluated SymPy echo is not a solve: "the integral
    # of x^x" comes back as "Integral(x^x, x) + C" — the
    # question restated, not answered (x^x has no elementary
    # antiderivative). Same for an unevaluated Derivative().
    if re.search(r"\b(?:Integral|Derivative)\s*\(", ans):
        return False
    if re.search(r"[′']|derivative|differentiate|अवकलज", part) \
            and "deriv" not in str((result or {}).get("op", "")):
        return False
    # An entrywise add/subtract of the two matrices named in
    # the text can never answer an inverse or determinant ask
    # — the router's matrix fallback grabs any two matrices it
    # sees (the audit's (AB)^-1 OR alternative "solved" to
    # A + B^-1). Reject that fragment shape outright.
    op = str((result or {}).get("op", ""))
    if op in ("add", "subtract"):
        if "⁻¹" in part or "^-1" in part or "inverse" in part \
                or "व्युत्क्रम" in part:
            return False
        if "determinant" in part or "सारणिक" in part:
            return False
    return True


def _solve_part(part):
    """Solve one self-contained part (an OR alternative, a
    case-study sub-question) through solve_question, with the
    same realness bar mcq applies to stems, the system
    substitution check, and the vacuity sanity guard."""
    part = (part or "").strip()
    if len(part) < 4:
        return None
    for cand in _part_candidates(part):
        try:
            result = solve_question(cand)
        except Exception:
            continue
        if not mcq._stem_is_real(cand, result):
            continue
        if not _part_sanity(part, result):
            continue
        if not _verify_system(part, result):
            continue
        return result
    return None


# ---------------------------------------------------------------------------
# Labelled sub-parts: (a)/(b), (i)/(ii)/(iii), (क)/(ख)/(ग)
# ---------------------------------------------------------------------------

_LABEL_MARK = re.compile(
    r"(?<![A-Za-z])\(\s*(i{1,3}|iv|v|[a-z]|क|ख|ग|घ)\s*\)")
_LABEL_SEQS = (["i", "ii", "iii", "iv", "v"],
               ["a", "b", "c", "d", "e"],
               ["क", "ख", "ग", "घ", "ङ"])


def _split_labelled(text):
    """Split a text into (head, [(label, segment), ...]) on a
    plausible label sequence — Roman numerals, letters or
    Devanagari part labels, in order. Stray markers (the (a)
    inside an (iii) part, P(E)-style parentheses) are ignored
    because only one family's sequence is followed. Returns
    None when no sequence of 2+ parts exists."""
    hits = [(m.group(1), m.start(), m.end())
            for m in _LABEL_MARK.finditer(text)]
    if len(hits) < 2:
        return None
    for seq in _LABEL_SEQS:
        chosen, want = [], 0
        for hit in hits:
            if hit[0] == seq[want]:
                chosen.append(hit)
                want += 1
                if want == len(seq):
                    break
        if len(chosen) < 2:
            continue
        parts = []
        for i, (label, _start, end) in enumerate(chosen):
            stop = chosen[i + 1][1] if i + 1 < len(chosen) \
                else len(text)
            seg = text[end:stop].strip(" .।,;:")
            if seg:
                parts.append((label, seg))
        if len(parts) >= 2:
            return text[:chosen[0][1]].strip(), parts
    return None


def _combine_parts(solved):
    """Combine the per-part solver results of a multi-part
    text into one result dict, following the ordinary answer
    card shape: the first part's shape, steps concatenated
    with their labels, one answer line naming each part."""
    base = dict(solved[0][1])
    steps, answers = [], []
    for label, result in solved:
        psteps = [str(s) for s in (result.get("steps") or [])]
        if psteps:
            psteps[0] = f"({label}) " + psteps[0]
        else:
            psteps = [f"({label})"]
        steps.extend(psteps)
        answers.append(f"({label}) {result.get('answer', '')}")
    base["steps"] = steps
    base["answer"] = " · ".join(answers)
    return base


def _solve_multipart(text):
    """Solve a text that may itself carry labelled sub-parts:
    whole first; if that fails and the text splits into
    labelled parts, it counts as solved only when EVERY part
    solves (half an alternative is not an answer to it)."""
    result = _solve_part(text)
    if result is not None:
        return result
    split = _split_labelled(text)
    if split is None:
        return None
    _head, parts = split
    solved = []
    for label, seg in parts:
        result = _solve_part(seg)
        if result is None:
            return None
        solved.append((label, result))
    return _combine_parts(solved)


# ---------------------------------------------------------------------------
# Format 1: OR bundles
# ---------------------------------------------------------------------------

_OR_SPLIT = re.compile(r"\s+OR\s+|(?<![\w])अथवा(?![\w])")
_ALT_LABEL = re.compile(
    r"^\(\s*(i{1,3}|iv|v|[a-z]|क|ख|ग|घ)\s*\)\s*")
# An alternative carries maths content: a digit, or a maths
# symbol / standalone variable ("Evaluate the integral of
# x^x dx" has no digit but is unmistakably a question).
_MATHS_HINT = re.compile(r"[\d^√∫=<>%]|\b[xyz]\b")


def extract_or(question):
    """The alternatives of an OR bundle —
    [(label_or_None, text), ...] — or None. An alternative
    must be substantial (a real question, not a phrase), and
    a question that carries a value-like MCQ option list is
    not an OR bundle."""
    q = str(question or "").strip()
    if not q:
        return None
    extracted = mcq._extract_marked(q) or mcq._extract_cued(q)
    if extracted is not None:
        _stem, options = extracted
        if all("=" not in text and len(text) <= 40
               for _l, text in options):
            return None  # a plain MCQ, mcq.py's territory
    parts = _OR_SPLIT.split(q)
    if len(parts) < 2:
        return None
    alts = []
    for raw in parts:
        raw = raw.strip()
        m = _ALT_LABEL.match(raw)
        label = m.group(1) if m else None
        text = raw[m.end():] if m else raw
        text = text.strip(" .।,;:")
        if len(text) < 12 or not _MATHS_HINT.search(text):
            return None
        alts.append((label, text))
    return alts


_OR_NOTES = {
    "one": {
        "en": "OR question — alternative ({d}) is solved below:",
        "roman": "OR wala sawal — alternative ({d}) ka hal "
                 "neeche hai:",
        "dev": "अथवा-प्रश्न — विकल्प ({d}) का हल नीचे दिया "
               "गया है:",
    },
    "both": {
        "en": "OR question — both alternatives can be solved; "
              "here is alternative ({d}):",
        "roman": "OR wala sawal — dono alternatives solve ho "
                 "sakte hain; yaha alternative ({d}) ka hal hai:",
        "dev": "अथवा-प्रश्न — दोनों विकल्प हल किए जा सकते हैं; "
               "यहाँ विकल्प ({d}) का हल है:",
    },
}


def or_result(question):
    """The OR answer for `question`, or None.

    Exactly one alternative solving serves that alternative's
    own solver result (labelled by a note step); both solving
    serves the FIRST with a note that the other also has a
    solution. Neither solving returns None."""
    if extract_ar(question) is not None:
        return None  # Assertion–Reason is its own format
    alts = extract_or(question)
    if not alts:
        return None
    solved = []
    for idx, (label, text) in enumerate(alts):
        solved.append((idx, label, _solve_multipart(text)))
    wins = [s for s in solved if s[2] is not None]
    if not wins:
        return None
    idx, label, result = wins[0]
    disp = label if label else "abcd"[idx]
    both = len(wins) == len(alts) and len(alts) > 1
    out = dict(result)
    note = _OR_NOTES["both" if both else "one"][
        _flavour(question)].format(d=disp)
    out["steps"] = [note] + list(out.get("steps") or [])
    out["source"] = "or"
    out["or"] = {
        "solved_label": disp,
        "alternatives": len(alts),
        "both_solved": both,
    }
    return out


# ---------------------------------------------------------------------------
# Format 2: Assertion–Reason
# ---------------------------------------------------------------------------

_A_MARK = re.compile(
    r"(?i)assertion\s*\(\s*a\s*\)\s*[:：]?"
    r"|अभिकथन\s*\(\s*a\s*\)\s*[:：]?")
_R_MARK = re.compile(
    r"(?i)reason\s*\(\s*r\s*\)\s*[:：]?"
    r"|कारण\s*\(\s*r\s*\)\s*[:：]?"
    r"|तर्क\s*\(\s*r\s*\)\s*[:：]?")
_AR_TAIL = re.compile(
    r"\(\s*(?:assertion[- ]reason|अभिकथन[- ]तर्क)[^)]*\)\s*\.?\s*$",
    re.I)


def _ar_options(text):
    """The four standard A–R options inside `text`, as
    ([(label, text), ...], offset_of_first_marker) or None.
    The run finder tolerates stray (A)/(R) markers inside the
    option texts themselves (the options quote "Assertion
    (A)"), which is why mcq's run finder cannot be reused
    here."""
    hits = [(m.group(1), m.start(), m.end())
            for m in re.finditer(r"\(\s*([a-dA-D])\s*\)", text)]
    run = None
    for i, hit in enumerate(hits):
        if hit[0].lower() != "a":
            continue
        cand, want = [hit], 1
        for j in range(i + 1, len(hits)):
            if "abcd".index(hits[j][0].lower()) == want:
                cand.append(hits[j])
                want += 1
                if want == 4:
                    break
        if len(cand) == 4:
            run = cand
            break
    if run is None:
        return None
    options = []
    for i, (label, _start, end) in enumerate(run):
        stop = run[i + 1][1] if i + 1 < len(run) else len(text)
        options.append((label, text[end:stop].strip(" .।")))
    return options, run[0][1]


def extract_ar(question):
    """(assertion_text, reason_text, options_or_None) for an
    Assertion–Reason question, or None."""
    q = str(question or "").strip()
    ma = _A_MARK.search(q)
    if not ma:
        return None
    mr = _R_MARK.search(q, ma.end())
    if not mr:
        return None
    a_text = q[ma.end():mr.start()].strip(" .।")
    rest = q[mr.end():]
    got = _ar_options(rest)
    if got is not None:
        options, offset = got
        r_text = rest[:offset].strip(" .।")
    else:
        options = None
        r_text = _AR_TAIL.sub("", rest).strip(" .।")
    if len(a_text) < 5 or len(r_text) < 5:
        return None
    return a_text, r_text, options


# --- Truth deciders. Each returns (truth, tag, detail) or None
# --- when the statement is outside the computable subset.
# --- `detail` is a one-line justification in the statement's
# --- own language, used in the answer's steps.

def _frac_str(fr):
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


_CLAIM_RE = re.compile(
    r"(?i)value of\s+([a-z])\s+for which\s+(.+?)\s+is\s+"
    r"(-?\d+(?:\.\d+)?)\s*\.?$")
_MATHY_CHARS = set("0123456789+-*/^(). ")


def _linear_pair(stmt, param):
    """The two linear equations (as (a, b, c) coefficient
    triples in `param`, for a*x + b*y + c = 0) written in a
    statement, or None. Equations are found by expanding
    around each "=" over maths characters only — the letter
    whitelist {x, y, param} is what stops the expansion at
    the surrounding prose."""
    letters = _MATHY_CHARS | {"x", "y", param}
    spans = []
    for m in re.finditer(r"=", stmt):
        lo = m.start()
        while lo > 0 and stmt[lo - 1] in letters:
            lo -= 1
        hi = m.end()
        while hi < len(stmt) and stmt[hi] in letters:
            hi += 1
        spans.append(stmt[lo:hi].strip())
    eqs = []
    seen = set()
    for span in spans:
        if span in seen or span.count("=") != 1:
            continue
        seen.add(span)
        lhs, rhs = (p.strip() for p in span.split("="))
        if not lhs or not rhs:
            continue
        try:
            expr = parse_expression(_ascii_fold(lhs)) \
                - parse_expression(_ascii_fold(rhs))
            x, y = sympy.Symbol("x"), sympy.Symbol("y")
            poly = sympy.Poly(expr, x, y)
        except Exception:
            continue
        if poly is None or poly.total_degree() > 1:
            continue
        if not set(expr.free_symbols) <= {x, y,
                                          sympy.Symbol(param)}:
            continue
        a = poly.nth(1, 0)
        b = poly.nth(0, 1)
        c = poly.nth(0, 0)
        if a == 0 and b == 0:
            continue
        eqs.append((a, b, c))
    return eqs if len(eqs) == 2 else None


def _classify_pair(a1, b1, c1, a2, b2, c2):
    """The solution type of a 2x2 linear system whose
    coefficients are Fractions: "unique", "infinite" (the
    same line twice) or "none" (parallel lines)."""
    if a1 * b2 != a2 * b1:
        return "unique"
    if a1 * c2 == a2 * c1 and b1 * c2 == b2 * c1:
        return "infinite"
    return "none"


_PAIR_DESC = {
    "unique": "intersecting lines (a unique solution)",
    "infinite": "the same line twice (infinitely many "
                "solutions)",
    "none": "parallel lines (no solution)",
}


def _decide_linear_pair(stmt):
    """'The value of p for which <system> is <property> is K'
    — decided exactly by classifying the system at p = K.
    For the plain word "consistent" the claim is only
    decidable at the boundary value (where the determinant
    vanishes): a unique solution holds for a whole range of
    p, so "THE value is K" cannot be settled there."""
    m = _CLAIM_RE.search(stmt)
    if not m:
        return None
    param, middle, k_text = m.group(1), m.group(2), m.group(3)
    mid = middle.lower()
    if "infinitely many" in mid:
        prop = "infinite"
    elif "no solution" in mid or "inconsistent" in mid:
        prop = "none"
    elif "consistent" in mid:
        prop = "consistent"
    else:
        return None
    eqs = _linear_pair(stmt, param)
    if eqs is None:
        return None
    psym = sympy.Symbol(param)
    try:
        kval = sympy.Rational(k_text)
        coeffs = []
        for triple in eqs:
            row = []
            for coef in triple:
                val = sympy.expand(coef).subs(psym, kval)
                if val.free_symbols:
                    return None
                row.append(Fraction(val.p, val.q))
            coeffs.append(row)
    except Exception:
        return None
    (a1, b1, c1), (a2, b2, c2) = coeffs
    cls = _classify_pair(a1, b1, c1, a2, b2, c2)
    if prop == "infinite":
        truth = cls == "infinite"
    elif prop == "none":
        truth = cls == "none"
    else:  # consistent
        if cls == "none":
            truth = False
        elif cls == "infinite":
            truth = True
        else:
            return None
    detail = (f"Putting {param} = {k_text}, the system "
              f"becomes {_frac_str(a1)}x + {_frac_str(b1)}y "
              f"+ {_frac_str(c1)} = 0 and {_frac_str(a2)}x + "
              f"{_frac_str(b2)}y + {_frac_str(c2)} = 0 — "
              f"{_PAIR_DESC[cls]}.")
    return truth, "linear_pair", detail


_RATIO_RE = re.compile(r"([abc])1\s*/\s*([abc])2")


def _decide_ratio_condition(stmt):
    """A statement of the standard ratio conditions for a
    pair of lines ('…infinitely many solutions, if
    a1/a2 = b1/b2 = c1/c2') — an NCERT fact, decided by
    comparing the stated relations with the correct table."""
    s = stmt.lower()
    hits = list(_RATIO_RE.finditer(s))
    if len(hits) < 2:
        return None
    pairs = [(h.group(1), h.group(2)) for h in hits]
    if pairs[0] != ("a", "a") or pairs[1] != ("b", "b"):
        return None
    rels = []
    for i in range(len(hits) - 1):
        between = s[hits[i].end():hits[i + 1].start()]
        if "≠" in between or "!=" in between:
            rels.append("≠")
        elif "=" in between:
            rels.append("=")
        else:
            return None
    if "infinitely many" in s:
        expect, name = ["=", "="], "infinitely many solutions"
    elif "no solution" in s:
        expect, name = ["=", "≠"], "no solution"
    elif "unique" in s:
        expect, name = ["≠"], "a unique solution"
    else:
        return None
    if len(rels) < len(expect):
        return None
    truth = rels[:len(expect)] == expect
    stated = " = ".join(f"{c}1/{c}2" for c in "abc"[:len(rels) + 1])
    detail = (f"The condition for {name} is "
              f"a1/a2 {'≠' if expect == ['≠'] else '='} "
              f"b1/b2" + (" = c1/c2" if len(expect) > 1 else "")
              + f"; the statement gives {stated} "
              f"with relations {' and '.join(rels)}.")
    return truth, "linear_pair_ratios", detail


def _decide_sqrt(stmt):
    """Square-root irrationality claims: '√n is irrational'
    (true iff n is not a perfect square) and the universal
    'square roots of ALL positive integers are irrational'
    — false, with √4 = 2 as the counterexample."""
    s = stmt
    low = s.lower()
    dev = any("ऀ" <= ch <= "ॿ" for ch in s)
    mentions_irr = "अपरिमेय" in s or "irrational" in low
    mentions_rat = ("परिमेय" in s and "अपरिमेय" not in s) or \
        ("rational" in low and "irrational" not in low)
    universal = ("सभी" in s and "वर्गमूल" in s) or \
        "square roots of all" in low or \
        re.search(r"all\s+(positive\s+)?integers", low) or \
        re.search(r"every\s+.*square\s+root", low)
    if universal and (mentions_irr or mentions_rat):
        if mentions_irr:
            detail = ("Not all of them: √4 = 2 is a rational "
                      "number." if not dev else
                      "सभी नहीं होते: √4 = 2 एक परिमेय संख्या "
                      "है।")
        else:
            detail = ("Not all of them: √2 is an irrational "
                      "number." if not dev else
                      "सभी नहीं होते: √2 एक अपरिमेय संख्या है।")
        return False, "sqrt", detail
    m = re.search(r"√\s*(\d+)|sqrt\s*\(?\s*(\d+)", low)
    if not m:
        return None
    n = int(m.group(1) or m.group(2))
    root = int(n ** 0.5)
    is_square = root * root == n
    if mentions_irr:
        truth = n > 0 and not is_square
        if dev:
            detail = (f"√{n} अपरिमेय है क्योंकि {n} पूर्ण वर्ग "
                      f"नहीं है।" if truth else
                      f"√{n} = {root} एक परिमेय संख्या है।")
        else:
            detail = (f"√{n} is irrational because {n} is not "
                      f"a perfect square." if truth else
                      f"√{n} = {root} is a rational number.")
        return truth, "sqrt", detail
    if mentions_rat:
        truth = is_square
        if dev:
            detail = (f"√{n} = {root} एक परिमेय संख्या है।"
                      if truth else
                      f"√{n} अपरिमेय है क्योंकि {n} पूर्ण वर्ग "
                      f"नहीं है।")
        else:
            detail = (f"√{n} = {root} is a rational number."
                      if truth else
                      f"√{n} is irrational because {n} is not "
                      f"a perfect square.")
        return truth, "sqrt", detail
    return None


def _decide_bijective(stmt):
    """Bijectivity claims: the definition template itself,
    and a linear f(x) = ax + b on Z -> Z, which is bijective
    iff |a| = 1, injective iff a != 0, surjective iff
    |a| = 1."""
    s = _ascii_fold(stmt)
    low = s.lower()
    if "bijective" in low and "injective" in low \
            and "surjective" in low \
            and ("both" in low or "if" in low):
        return True, "bijective_def", (
            "By definition, a function is bijective exactly "
            "when it is both injective (one-one) and "
            "surjective (onto).")
    m = re.search(r"f\s*\(\s*x\s*\)\s*=\s*([^,.;]+)", s)
    if not m:
        return None
    if not re.search(r"(?i)\bZ\s*(?:→|->)\s*Z\b|integers|पूर्णांक",
                     stmt):
        return None
    try:
        expr = parse_expression(m.group(1))
        x = sympy.Symbol("x")
        if expr.free_symbols != {x}:
            return None
        poly = sympy.Poly(expr, x)
        if poly is None or poly.degree() != 1:
            return None
        a, b = poly.nth(1), poly.nth(0)
        if not (a.is_integer and b.is_integer):
            return None
        a, b = int(a), int(b)
    except Exception:
        return None
    if a == 0:
        return None
    if "bijective" in low or (
            ("injective" in low or "one-one" in low)
            and ("surjective" in low or "onto" in low)):
        truth = abs(a) == 1
        if truth:
            detail = (f"f(x) = {a}x + {b} on Z is bijective: "
                      f"its slope is {a}, so every integer is "
                      f"hit exactly once.")
        else:
            witness = next(
                y for y in range(-10, 30) if (y - b) % a != 0)
            detail = (f"f is injective but not surjective on "
                      f"Z: no integer x gives f(x) = {witness}, "
                      f"since x = ({witness} - ({b}))/{a} is "
                      f"not an integer.")
        return truth, "bijective", detail
    if "injective" in low or "one-one" in low:
        return True, "bijective", (
            f"f(x) = {a}x + {b} is injective on Z: distinct "
            f"integers give distinct values (slope {a} != 0).")
    if "surjective" in low or "onto" in low:
        truth = abs(a) == 1
        detail = (f"f(x) = {a}x + {b} reaches every integer "
                  f"because its slope is {a}." if truth else
                  f"f is not surjective on Z: values between "
                  f"consecutive multiples of {a} are missed.")
        return truth, "bijective", detail
    return None


_DIRCOS_ID = re.compile(
    r"cos\s*\^?\s*2\s*α\s*\+\s*cos\s*\^?\s*2\s*β\s*\+\s*"
    r"cos\s*\^?\s*2\s*γ\s*=\s*1")


def _decide_dircos(stmt):
    """The direction-cosine facts: the identity
    cos²α + cos²β + cos²γ = 1, and its direct consequence
    that no line can be perpendicular to all three axes at
    once (its direction cosines would all be 0)."""
    s = stmt
    dev = any("ऀ" <= ch <= "ॿ" for ch in s)
    folded = s.replace("²", "^2").replace("−", "-")
    if _DIRCOS_ID.search(folded):
        detail = ("For any line, the direction cosines "
                  "satisfy cos²α + cos²β + cos²γ = 1."
                  if not dev else
                  "किसी भी रेखा के दिक्-कोसाइन cos²α + cos²β "
                  "+ cos²γ = 1 को संतुष्ट करते हैं।")
        return True, "dircos", detail
    low = s.lower()
    en = "perpendicular" in low and "axes" in low and (
        "cannot" in low or "simultaneously" in low
        or "never" in low)
    hi = "लंबवत" in s and "अक्ष" in s and (
        "नहीं" in s or "कभी" in s)
    if en or hi:
        detail = ("A line perpendicular to all three axes "
                  "would need direction cosines 0, 0, 0 — but "
                  "0² + 0² + 0² = 0 ≠ 1, so such a line "
                  "cannot exist." if not dev else
                  "तीनों अक्षों के लंबवत रेखा के दिक्-कोसाइन "
                  "0, 0, 0 होने चाहिए, परंतु 0² + 0² + 0² = 0 "
                  "≠ 1, इसलिए ऐसी रेखा संभव नहीं है।")
        return True, "dircos", detail
    return None


_OP_WORDS = ("hcf", "lcm", "gcd", "area", "perimeter",
             "volume", "sum", "product", "mean", "square",
             "cube", "root")


def _decide_value_claim(stmt):
    """A plain value claim — '<computable phrase> is <value>'
    — decided by solving the phrase with the existing
    machinery (mcq._solve_stem) and comparing. False is only
    returned when the phrase solves to a definite DIFFERENT
    number."""
    s = stmt.strip().rstrip(".")
    if re.search(r"(?i)\bif\b|for which", s):
        return None
    m = re.match(r"(?is)^(.+?)\s+is\s+(.+)$", s) or \
        re.match(r"(?is)^(.+?)\s*=\s*(.+)$", s)
    if not m:
        return None
    lhs, rhs = m.group(1).strip(), m.group(2).strip()
    if not any(ch.isdigit() for ch in lhs) or len(rhs) > 30:
        return None
    result = mcq._solve_stem(lhs)
    if result is None:
        return None
    ans = str(result.get("answer", "") or "")
    tag = "value"
    for word in _OP_WORDS:
        if word in lhs.lower():
            tag = f"value:{word}"
            break
    if mcq._matching_labels(ans, [("x", rhs)]):
        return True, tag, f"{lhs} = {ans}."
    if mcq._as_number(mcq._clean(rhs)) is not None and \
            mcq._computed_variants(ans) and \
            mcq._as_number(mcq._clean(
                mcq._computed_variants(ans)[0])) is not None:
        return False, tag, f"{lhs} = {ans}, not {rhs}."
    return None


_DECIDERS = (_decide_linear_pair, _decide_ratio_condition,
             _decide_sqrt, _decide_bijective, _decide_dircos)


def _decide(stmt):
    for fn in _DECIDERS:
        got = fn(stmt)
        if got is not None:
            return got
    return _decide_value_claim(stmt)


def _decide_explanation(a_tag, r_tag):
    """Whether R explains A, when both are true — True only
    on a structural link, False only for clearly independent
    facts, else None (fall through rather than guess).

    Links: R states the ratio conditions and A was a
    linear-pair claim decided by exactly those ratios; the
    direction-cosine pair (A is the axes consequence of the
    very identity R states). A definition offered as R is
    deliberately NOT decided either way."""
    if r_tag == "bijective_def":
        return None
    if (a_tag, r_tag) in (("linear_pair", "linear_pair_ratios"),
                          ("dircos", "dircos")):
        return True
    if a_tag and r_tag and a_tag != r_tag:
        return False
    return None


def _classify_option(text):
    """The truth-combination a standard A–R option states:
    "TT_exp", "TT_noexp", "TF" or "FT" (or None). The
    negation is checked before the positive explanation
    wording, since option (b) quotes it to deny it."""
    t = text.lower()
    both_true = "both a and r are true" in t or "दोनों सही" in text
    if both_true:
        if "not the correct explanation" in t \
                or "व्याख्या नहीं" in text:
            return "TT_noexp"
        if "correct explanation" in t or "सही व्याख्या" in text:
            return "TT_exp"
        return None
    a_true = "a is true" in t or "अभिकथन (a) सही" in t
    a_false = "a is false" in t or "अभिकथन (a) गलत" in t
    r_true = "r is true" in t or "कारण (r) सही" in t
    r_false = "r is false" in t or "कारण (r) गलत" in t
    if a_true and r_false:
        return "TF"
    if a_false and r_true:
        return "FT"
    return None


_STANDARD_COMBO = {
    "TT_exp": {
        "en": "(a) Both A and R are true and R is the "
              "correct explanation of A",
        "dev": "(a) अभिकथन (A) और कारण (R) दोनों सही हैं और "
               "कारण (R), अभिकथन (A) की सही व्याख्या करता है।",
        "roman": "(a) A aur R dono sahi hain aur R, A ki "
                 "sahi vyakhya karta hai",
    },
    "TT_noexp": {
        "en": "(b) Both A and R are true, but R is not the "
              "correct explanation of A",
        "dev": "(b) अभिकथन (A) और कारण (R) दोनों सही हैं, "
               "लेकिन कारण (R), अभिकथन (A) की सही व्याख्या "
               "नहीं है।",
        "roman": "(b) A aur R dono sahi hain, lekin R, A ki "
                 "sahi vyakhya nahi karta",
    },
    "TF": {
        "en": "(c) A is true, but R is false",
        "dev": "(c) अभिकथन (A) सही है, लेकिन कारण (R) गलत है।",
        "roman": "(c) A sahi hai, lekin R galat hai",
    },
    "FT": {
        "en": "(d) A is false, but R is true",
        "dev": "(d) अभिकथन (A) गलत है, लेकिन कारण (R) सही है।",
        "roman": "(d) A galat hai, lekin R sahi hai",
    },
}

_AR_STEP_WORDS = {
    "en": ("Assertion (A)", "Reason (R)", "true", "false",
           "so A is", "so R is"),
    "dev": ("अभिकथन (A)", "कारण (R)", "सही", "गलत",
            "अतः A", "अतः R"),
    "roman": ("Assertion (A)", "Reason (R)", "sahi", "galat",
              "isliye A", "isliye R"),
}


def assertion_reason_result(question):
    """The Assertion–Reason answer for `question`, or None.

    Both statements must be decided by the computable
    deciders; the combination is then mapped to the matching
    printed option when options are present, else to the
    standard wording in the question's own flavour. Both
    statements false, an undecided statement, or an
    undecidable explanation question all return None."""
    got = extract_ar(question)
    if got is None:
        return None
    a_text, r_text, options = got
    da = _decide(a_text)
    dr = _decide(r_text)
    if da is None or dr is None:
        return None
    a_true, a_tag, a_detail = da
    r_true, r_tag, r_detail = dr
    if a_true and r_true:
        explains = _decide_explanation(a_tag, r_tag)
        if explains is None:
            return None
        combo = "TT_exp" if explains else "TT_noexp"
    elif a_true:
        combo = "TF"
    elif r_true:
        combo = "FT"
    else:
        return None  # no standard option covers both false
    flavour = _flavour(question)
    words = _AR_STEP_WORDS[flavour]
    steps = [
        f"{words[0]}: {a_detail} — {words[4]} "
        f"{words[2] if a_true else words[3]}.",
        f"{words[1]}: {r_detail} — {words[5]} "
        f"{words[2] if r_true else words[3]}.",
    ]
    if combo == "TT_exp":
        steps.append({
            "en": "R states exactly the fact that makes A "
                  "true, so R is the correct explanation "
                  "of A.",
            "roman": "R wahi tathya batata hai jis se A sahi "
                     "hota hai, isliye R, A ki sahi vyakhya "
                     "hai.",
            "dev": "R वही तथ्य बताता है जिससे A सही होता "
                   "है, इसलिए R, A की सही व्याख्या है।",
        }[flavour])
    elif combo == "TT_noexp":
        steps.append({
            "en": "A and R are both true, but they are "
                  "independent facts — R does not explain A.",
            "roman": "A aur R dono sahi hain, lekin dono "
                     "alag-alag tathya hain — R, A ki vyakhya "
                     "nahi karta.",
            "dev": "A और R दोनों सही हैं, लेकिन दोनों "
                   "स्वतंत्र तथ्य हैं — R, A की व्याख्या नहीं "
                   "करता।",
        }[flavour])
    if options:
        label = text = None
        for lab, opt_text in options:
            if _classify_option(opt_text) == combo:
                label, text = lab, opt_text
                break
        if label is None:
            return None
        answer = f"({label}) {text}"
    else:
        answer = _STANDARD_COMBO[combo][flavour]
    return {
        "type": "Assertion–Reason",
        "op": "assertion_reason",
        "answer": answer,
        "steps": steps,
        "source": "assertion_reason",
        "assertion_reason": {
            "a_true": a_true,
            "r_true": r_true,
            "combo": combo,
            "assertion": a_text,
            "reason": r_text,
        },
    }


# ---------------------------------------------------------------------------
# Format 3: case-study sets
# ---------------------------------------------------------------------------

_CASE_CUE = re.compile(
    r"(?i)case\s*study|प्रकरण\s*अध्ययन|प्रकरण"
    r"|based on the above information,?\s*answer the following")

_DEF_RE = re.compile(r"([a-z])\s*\(\s*x\s*\)\s*=\s*([^.;]+)")
_POINT_RE = re.compile(
    r"(?:point|बिंदु)\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
    r"(-?\d+(?:\.\d+)?)\s*\)")


def extract_case_study(question):
    """(passage, [(label, sub_question), ...]) for a
    case-study set, or None. The passage is everything
    before the first sub-question marker."""
    q = str(question or "").strip()
    if not _CASE_CUE.search(q):
        return None
    split = _split_labelled(q)
    if split is None:
        return None
    passage, parts = split
    if len(parts) < 2:
        return None
    return passage, parts


def _passage_facts(passage):
    """The passage's function definitions ({name: expr}) and
    the points the graph is stated to pass through
    ([(x0, y0), ...] as strings)."""
    folded = _ascii_fold(passage)
    defs = {}
    for m in _DEF_RE.finditer(folded):
        defs[m.group(1)] = m.group(2).strip()
    points = [(m.group(1), m.group(2))
              for m in _POINT_RE.finditer(passage)]
    return defs, points


def _frac_of(fr):
    return _frac_str(fr)


def _bind_param(defs, points, subq):
    """The 'find the value of <param>' sub-question of a
    passage-defined function: the passage states one point
    the graph passes through, so substituting that point
    into the definition gives one equation in the parameter
    — assembled here and solved by solve_question itself.
    Returns (param, Fraction value, result) or None."""
    m = re.search(r"(?i)find\s+(?:the\s+value\s+of\s+)?([a-z])\b",
                  subq) or re.search(r"([a-z])\s*का\s*मान", subq)
    if not m or not defs or len(points) != 1:
        return None
    param = m.group(1)
    x0, y0 = points[0]
    for _fname, expr in defs.items():
        try:
            full = parse_expression(expr)
        except Exception:
            continue
        if sympy.Symbol(param) not in full.free_symbols:
            continue
        try:
            at = parse_expression(
                re.sub(r"\bx\b", f"({x0})", expr))
        except Exception:
            continue
        eq = f"{at} = {y0}"
        try:
            result = solve_question(eq)
        except Exception:
            return None
        if not mcq._stem_is_real(eq, result):
            return None
        assigns = _assignments(result)
        if not assigns or param not in assigns:
            return None
        result = dict(result)
        result["steps"] = [
            f"From the passage, the graph passes through "
            f"({x0}, {y0}), so substituting x = {x0} in the "
            f"definition gives {eq}."
        ] + list(result.get("steps") or [])
        return param, assigns[param], result
    return None


def _sub_params(expr, known):
    for param, value in known.items():
        expr = re.sub(rf"\b{param}\b", f"({_frac_of(value)})",
                      expr)
    return expr


def _bind_derivative(defs, known, subq):
    """A 'find f'(x) at x = c' sub-question: with the
    passage's parameters known (from an earlier sub-part),
    the derivative question is assembled in plain solver
    language and solved by solve_question. The answer must
    come back a plain number."""
    m = re.search(
        r"(?i)([a-z])\s*'\s*\(\s*x\s*\)\s*at\s*x\s*=\s*"
        r"(-?\d+(?:\.\d+)?)", _ascii_fold(subq))
    if m:
        fname, c = m.group(1), m.group(2)
    else:
        m = re.search(
            r"(?i)derivative[^.]*?at\s*x\s*=\s*"
            r"(-?\d+(?:\.\d+)?)", subq)
        if not m:
            return None
        fname, c = None, m.group(1)
    if fname not in defs:
        fname = next(iter(defs)) if len(defs) == 1 else None
    if fname is None:
        return None
    expr = _sub_params(defs[fname], known)
    try:
        if parse_expression(expr).free_symbols \
                - {sympy.Symbol("x")}:
            return None
    except Exception:
        return None
    q = f"Find the derivative of {expr} at x = {c}"
    try:
        result = solve_question(q)
    except Exception:
        return None
    if not mcq._stem_is_real(q, result):
        return None
    if mcq._as_number(mcq._clean(
            str(result.get("answer", "")))) is None:
        return None
    return result


def _bind_eval(defs, known, subq):
    """A 'find f(k)' sub-question: substitute the known
    parameters and x = k into the passage's definition and
    let solve_question evaluate it. The answer must come
    back a plain number."""
    m = re.search(r"(?i)\b([a-z])\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
                  subq)
    if not m:
        return None
    if "find" not in subq.lower() \
            and "value" not in subq.lower():
        return None
    fname, k = m.group(1), m.group(2)
    if fname not in defs:
        return None
    expr = _sub_params(defs[fname], known)
    expr = re.sub(r"\bx\b", f"({k})", expr)
    try:
        if parse_expression(expr).free_symbols:
            return None
        result = solve_question(expr)
    except Exception:
        return None
    if not mcq._stem_is_real(expr, result):
        return None
    if mcq._as_number(mcq._clean(
            str(result.get("answer", "")))) is None:
        return None
    return result


def case_study_result(question):
    """The case-study answer for `question`, or None.

    Each sub-question is solved independently — standalone
    first, then through the passage binder. Solved parts
    keep their own steps and answers, in order; an unsolved
    part is marked with the one-line not-found. If NO part
    solves, the whole set falls through unchanged."""
    got = extract_case_study(question)
    if got is None:
        return None
    passage, parts = got
    defs, points = _passage_facts(passage)
    known = {}
    part_results = []
    for label, subq in parts:
        result = _solve_multipart(subq)
        if result is None and defs:
            bound = _bind_param(defs, points, subq)
            if bound is not None:
                param, value, result = bound
                known[param] = value
        if result is None and defs:
            result = _bind_derivative(defs, known, subq)
        if result is None and defs:
            result = _bind_eval(defs, known, subq)
        part_results.append((label, result))
    if all(r is None for _l, r in part_results):
        return None
    nf = _not_found_line(question)
    steps, answers = [], []
    for label, result in part_results:
        if result is None:
            steps.append(f"({label}) {nf}")
            answers.append(f"({label}) {nf}")
            continue
        psteps = [str(s) for s in (result.get("steps") or [])]
        if psteps:
            psteps[0] = f"({label}) " + psteps[0]
        else:
            psteps = [f"({label})"]
        steps.extend(psteps)
        answers.append(f"({label}) {result.get('answer', '')}")
    return {
        "type": "Case study",
        "op": "case_study",
        "answer": " · ".join(answers),
        "steps": steps,
        "source": "case_study",
        "case_study": {
            "parts": [{"label": label,
                       "solved": result is not None,
                       "answer": (result.get("answer", "")
                                  if result is not None
                                  else None)}
                      for label, result in part_results],
        },
    }


# ---------------------------------------------------------------------------
# The real-branch preference (mirrors mcq.mcq_preferred)
# ---------------------------------------------------------------------------

def _answer_matches(a, b):
    """Whether two answer strings state the same value —
    cleaned-text equality, else mcq's value matching."""
    ca, cb = mcq._clean(a), mcq._clean(b)
    if ca and ca == cb:
        return True
    return bool(mcq._matching_labels(a, [("x", b)]))


def formats_preferred(question, full_result):
    """The format answer to prefer over an already-"solved"
    whole-text result, or None.

    A whole OR bundle or case-study set fed to the solver as
    one text can come back with a fragment dressed as an
    answer — the matrix/system OR bundle "solves" to
    2*x - y + 6 (a shred of one equation), the roller-coaster
    case study to x = 1. Exactly mcq_preferred's situation:
    for these formats the PARTS are the authority. So when
    an alternative / sub-question verifiably solves and the
    whole-text answer matches NONE of the solved parts'
    answers, the format result is served instead. When the
    whole-text answer does match a solved part, the result
    is a genuine solve of that part and is left untouched —
    byte-for-byte the pre-Wave-82 behaviour. One exception:
    an OR bundle where BOTH alternatives solve always
    serves the format result, because only it notes that
    the other alternative also has a solution."""
    q = str(question or "").strip()
    if not q or not isinstance(full_result, dict):
        return None
    full_ans = str(full_result.get("answer", "") or "")
    if extract_ar(q) is None and extract_or(q):
        result = or_result(q)
        if result is not None:
            # When BOTH alternatives solve, the format result
            # always wins: a whole-text solve can only ever
            # have worked on one fragment of the bundle, and
            # only the format answer carries the note that
            # the other alternative also has a solution.
            if (result.get("or") or {}).get("both_solved"):
                return result
            if not _answer_matches(
                    full_ans, result.get("answer", "")):
                return result
    if extract_case_study(q) is not None:
        result = case_study_result(q)
        if result is not None:
            part_answers = [
                p["answer"] for p in
                result["case_study"]["parts"] if p["solved"]]
            if part_answers and not any(
                    _answer_matches(full_ans, pa)
                    for pa in part_answers):
                return result
    return None


# ---------------------------------------------------------------------------
# The layer
# ---------------------------------------------------------------------------

def formats_result(question):
    """The paper-format answer for `question` — an OR bundle,
    an Assertion–Reason item or a case-study set — or None,
    in which case the existing fallback behaviour runs
    exactly as before."""
    q = str(question or "").strip()
    if not q:
        return None
    result = assertion_reason_result(q)
    if result is not None:
        return result
    result = or_result(q)
    if result is not None:
        return result
    return case_study_result(q)


__all__ = ["formats_result", "formats_preferred",
           "extract_or", "extract_ar", "extract_case_study",
           "or_result", "assertion_reason_result",
           "case_study_result"]
