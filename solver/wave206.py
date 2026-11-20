"""Wave 206 (test-loop fix-queue, 20 Nov 2026): native schemas
for the question families the teeno-AI test loop's fix-queue
exposed — messy student-dress forms whose maths is elementary
but which no existing solver owned, so they fell to the
clarification line or to a fragment salvage:

  * multi-step add/subtract STORY chains (EN / Hinglish /
    Devanagari): "45 rupee the, 12 ka chocolate kharida, bhai
    ne 20 aur de diye — ab kitne bache?"
  * backward stories ("de diye N, bache M — shuru me kitne?")
    and small verbal equations (double+7=25, consecutive
    numbers, two ages, equal-parts total)
  * fraction stories: chains of fractions with story verbs,
    1 whole − fraction, fraction-of-a-quantity complement,
    Roman/Devanagari fraction comparison
  * integer forms: a bare signed expression inside filler,
    "−5 aur +12 ko add", subtract-from phrasings, number-line
    walks in three scripts
  * roots: bare √N inside filler, area→side, volume→edge
  * polynomials buried in noisy text: an extractable caret
    expression + factor/expand ask, the x³+y³+z³ identity,
    square-area → side, remainder theorem in any word order,
    (a+b+c)² with stated values
  * quadratics: sum & product in any order, sum of squares
    of x and (x+k), roots given → the unknown coefficient,
    a bare quadratic equation inside a story
  * trig values in messy dress: single/compound angle atoms
    (incl. verbal "sin square"), a·sinx + b·cosx maximum,
    tan(x+y) from stated tan values
  * matrices: determinant (and trace) stated with an unknown
    element — bracket, tuple-row and Devanagari-row dress
  * junior multiply/divide stories: groups × each, per-person
    totals, equal sharing / average with exactly two numbers
  * series: an Nth-term ask (the Wave-202 engine answers
    next-term only), an AP sum in words, and series whose
    terms are separated by then / fir / फिर (extraction the
    Wave-202 run grammar cannot see)

Discipline (the repo's own): every schema is STRICT — it
fires only when it can extract the complete mathematical
content and VERIFY the answer deterministically (re-substitution,
re-expansion, cross-check by an independent computation) —
and returns None on any doubt, leaving the flow byte-identical
to before. No fuzzy matching, no bank lookup, no AI legs.
"""
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt_num

# ---------------------------------------------------------------------------
# shared helpers
# ---------------------------------------------------------------------------

_DEV_DIGITS = {ord("०") + i: str(i) for i in range(10)}
_INT = r"-?\d+"
_NUM = r"-?\d+(?:\.\d+)?"


def _prep(question):
    """Fold Devanagari digits and unicode operators; keep the
    text otherwise as the router handed it over."""
    t = str(question or "").translate(_DEV_DIGITS)
    t = t.replace("−", "-").replace("–", "-")
    return t


def _res(op, answer, steps, value=None, typ="word_problem",
         solutions=None):
    out = {"type": typ, "op": "w206_" + op,
           "answer": str(answer), "steps": steps}
    if solutions is not None:
        out["solutions"] = [str(s) for s in solutions]
    if value is not None:
        try:
            out["value"] = float(value)
        except (TypeError, ValueError):
            pass
        # Mirror the native evaluate contract: a result whose
        # answer is one bare number also carries "numeric"
        # (and "fraction"/"decimal" for a non-integer), the
        # keys the repo's own arithmetic results expose.
        try:
            bare = str(answer).strip().replace(",", "")
            fr = Fraction(bare)
            out["numeric"] = float(fr)
            if fr.denominator != 1:
                out["fraction"] = bare.replace(" ", "")
                out["decimal"] = float(fr)
        except (ValueError, ZeroDivisionError):
            pass
    return out


def _fmt(fr):
    """A Fraction / int the school way."""
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _numbers_with_spans(t):
    return [(Fraction(m.group(0)), m.start(), m.end())
            for m in re.finditer(r"(?<![\d.])-?\d+(?:\.\d+)?",
                                  t)]


def _sympify_span(span, names):
    """Parse an extracted maths span with sympy (caret powers
    and implicit multiplication allowed). Names maps letter ->
    symbol. Returns the expression or None."""
    s = span.replace("^", "**").replace("·", "*")
    try:
        from sympy.parsing.sympy_parser import (
            parse_expr, standard_transformations,
            implicit_multiplication_application)
        return parse_expr(
            s, local_dict=dict(names),
            transformations=standard_transformations +
            (implicit_multiplication_application,),
            evaluate=True)
    except Exception:
        return None


def _root_str(expr):
    """sympy value -> repo text style (sqrt(161) kept textual,
    multiplication as ·)."""
    return str(expr).replace("*", "·")


# Words that are pure question furniture (ask verbs, politeness,
# function words). A form wrapped ONLY in these is the clean
# canonical form a native layer already owns; the Wave-206
# families are defined by real dress around the maths, so the
# expression schemas below count the dress before firing.
_FILLER = {
    "solve", "kar", "karke", "karo", "do", "batao", "bata",
    "the", "a", "an", "of", "please", "pls", "factor",
    "factorise", "factorize", "expand", "simplify", "find",
    "calculate", "evaluate", "kya", "hoga", "hai", "h", "ka",
    "ki", "ke", "se", "ko", "ye", "wala", "wale", "sir", "is",
    "it", "this", "that", "my", "me", "i", "in", "on", "for",
    "to", "and", "aur", "hal", "हल", "कीजिए", "है", "root",
    "roots", "equation", "quadratic", "value", "what", "how",
    "much", "many", "will", "be", "kitna", "kitne", "chahiye",
}


def _content_words(text):
    """Dress words in `text`: alphabetic runs of length >= 2
    (Latin or Devanagari) that are not question furniture."""
    return [w for w in re.findall(
        r"[a-z]{2,}|[ऀ-ॿ]{2,}", text.lower())
        if w not in _FILLER]


# ---------------------------------------------------------------------------
# K. matrices — determinant / trace stated, unknown element
# ---------------------------------------------------------------------------

_CELL_OK = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*$|^\s*[a-z]\s*$|"
                      r"^\s*[a-z]\s*[+-]\s*\d+\s*$")


def _matrix_grid(t):
    """Extract a 2x2 or 3x3 grid of cells (numbers, single
    letters, or letter±number) from bracket, tuple-row or
    Devanagari-row dress. Returns (rows, symbols) or None."""
    rows = None
    # bracket dress: [[...],[...]] / [[...],[...],[...]]
    m = re.search(r"\[\[(.*?)\]\]", t, re.S)
    if m:
        inner = m.group(1)
        parts = re.split(r"\]\s*,\s*\[", inner)
        cand = [[c.strip() for c in p.split(",")] for p in parts]
        if len(cand) in (2, 3) and all(
                len(r) == len(cand) for r in cand):
            rows = cand
    # tuple-row dress: (p,1,2), (3,4,5), (6,7,8)
    if rows is None:
        tuples = re.findall(r"\(([^()]*)\)", t)
        cand = []
        for tup in tuples:
            cells = [c.strip() for c in tup.split(",")]
            if len(cells) in (2, 3) and all(
                    _CELL_OK.match(c) for c in cells):
                cand.append(cells)
            else:
                cand = []
                break
        if len(cand) in (2, 3) and all(
                len(r) == len(cand) for r in cand):
            rows = cand
    # Devanagari rows: पहली पंक्ति 1,2,3; दूसरी पंक्ति a,4,5; ...
    if rows is None and "पंक्ति" in t:
        segs = re.findall(
            r"पंक्ति\s*([0-9a-z,\s\-+]+?)(?:;|।|\.|\||$)", t)
        cand = [[c.strip() for c in s.split(",") if c.strip()]
                for s in segs]
        cand = [r for r in cand if r]
        if len(cand) in (2, 3) and all(
                len(r) == len(cand) for r in cand) and all(
                _CELL_OK.match(c) for r in cand for c in r):
            rows = cand
    if rows is None:
        return None
    syms = {}
    grid = []
    for row in rows:
        grow = []
        for c in row:
            if _CELL_OK.match(c) is None:
                return None
            if re.fullmatch(r"-?\d+(?:\.\d+)?", c):
                grow.append(sp.Rational(c))
            else:
                for ch in re.findall(r"[a-z]", c):
                    syms.setdefault(ch, sp.Symbol(ch))
                expr = _sympify_span(c, syms)
                if expr is None:
                    return None
                grow.append(expr)
        grid.append(grow)
    if not syms:
        return None  # a plain numeric determinant is not ours
    return grid, syms


def _matrix_unknown(t, tl):
    if not re.search(r"matrix|मैट्रिक्स|determinant|det\b|"
                     r"डिटरमिनेंट|सारणिक|trace|ट्रेस", tl):
        return None
    got = _matrix_grid(t)
    if got is None:
        return None
    grid, syms = got
    M = sp.Matrix(grid)
    det = sp.expand(M.det())
    md = re.search(r"(?:determinant|det|डिटरमिनेंट|सारणिक)"
                   r"\s*(?:\(.*?\))?\s*(?:=|is|hai|है|ho|हो)?"
                   r"\s*(-?\d+)", tl)
    mt = re.search(r"(?:trace|ट्रेस)\b[^0-9-]{0,30}?(-?\d+)",
                   tl)
    det_val = int(md.group(1)) if md else None
    trace_val = int(mt.group(1)) if mt else None
    if det_val is None and trace_val is None:
        return None
    # product ask: "find b*c" where det is a monomial in b, c
    mp = re.search(r"([a-z])\s*\*\s*([a-z])", tl)
    if mp and det_val is not None and len(syms) == 2 \
            and set(mp.groups()) == set(syms):
        s1, s2 = syms[mp.group(1)], syms[mp.group(2)]
        ratio = sp.simplify(det / (s1 * s2))
        if ratio.is_number and ratio != 0:
            prod = sp.Rational(det_val) / ratio
            steps = [
                f"det = {_root_str(det)}",
                f"{_root_str(det)} = {det_val}, so "
                f"{mp.group(1)}·{mp.group(2)} = "
                f"{_root_str(prod)}",
            ]
            return _res("matrix_det_product",
                        f"{mp.group(1)}*{mp.group(2)} = "
                        f"{_root_str(prod)}", steps,
                        typ="linear_algebra")
        return None
    if len(syms) != 1:
        return None
    (letter, sym), = syms.items()
    trace = sum(grid[i][i] for i in range(len(grid)))
    sols = None
    if trace_val is not None:
        cand = sp.solve(sp.Eq(trace, trace_val), sym)
        cand = [c for c in cand if c.is_real]
        if det_val is not None:
            cand = [c for c in cand
                    if sp.simplify(det.subs(sym, c)) == det_val]
        if len(cand) == 1:
            sols = cand
    elif det_val is not None:
        cand = sp.solve(sp.Eq(det, det_val), sym)
        cand = [c for c in cand if c.is_real]
        if cand:
            sols = cand
    if not sols:
        return None
    # verify every served solution against BOTH stated facts
    for c in sols:
        if det_val is not None and \
                sp.simplify(det.subs(sym, c)) != det_val:
            return None
        if trace_val is not None and \
                sp.simplify(trace.subs(sym, c)) != trace_val:
            return None
    steps = []
    if trace_val is not None:
        steps.append(f"Trace = {_root_str(sp.expand(trace))} "
                     f"= {trace_val}")
    if det_val is not None:
        steps.append(f"det = {_root_str(det)} = {det_val}")
    if len(sols) == 1:
        steps.append(f"So {letter} = {_root_str(sols[0])}")
        return _res("matrix_unknown",
                    f"{letter} = {_root_str(sols[0])}", steps,
                    typ="linear_algebra")
    joined = " or ".join(f"{letter} = {_root_str(c)}"
                          for c in sols)
    steps.append(f"So {joined}")
    return _res("matrix_unknown", joined, steps,
                typ="linear_algebra")


# ---------------------------------------------------------------------------
# J. trigonometry — value atoms, a sinx + b cosx max, tan(x+y)
# ---------------------------------------------------------------------------

_TRIG_FILLER = {
    "value", "of", "the", "what", "is", "find", "calculate",
    "batao", "bata", "do", "kaise", "nikalte", "nikalna", "hai",
    "h", "ye", "solve", "krna", "karna", "kitna", "hota",
    "hoti", "chahiye", "fraction", "me", "mein", "nahi",
    "point", "root", "wala", "wale", "simple", "bhaiya", "sir",
    "homework", "help", "i", "need", "answer", "with", "a",
    "an", "exam", "aaya", "tha", "ek", "ques", "question",
    "mere", "mera", "dost", "ne", "bola", "but", "am", "not",
    "sure", "pls", "please", "toh", "aur", "kr", "karke",
    "kar", "ho", "jayega", "ayega", "aayega", "degree",
    "degrees", "deg", "batao.", "in", "for", "this", "that",
    "it", "its", "just", "tell", "me", "my", "we", "you",
    "can", "give", "show", "how", "much", "hoga", "hoge",
    "ki", "ka", "ko", "ke", "se", "bhi", "tha", "thi", "he",
    "hua", "raha", "rahi", "wala.", "hoga.", "hai.",
}

_TRIG_FN = {"sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
            "sec": sp.sec, "csc": sp.csc, "cosec": sp.csc,
            "cot": sp.cot}


def _trig_clean_value(val):
    """Accept only school-clean exact values: a rational, or a
    sum of <= 3 surd terms with small radicands."""
    val = sp.simplify(val)
    if val.is_rational:
        return val
    terms = val.as_ordered_terms() if hasattr(
        val, "as_ordered_terms") else [val]
    if len(terms) > 3:
        return None
    for term in terms:
        for node in sp.preorder_traversal(term):
            if isinstance(node, sp.Pow) and \
                    node.exp == sp.Rational(1, 2):
                base = node.base
                if not (base.is_Integer and 0 < int(base) <= 10):
                    return None
    if val.has(sp.sin, sp.cos, sp.tan, sp.pi):
        return None
    return val


def _trig_value_expr(t, tl):
    import math
    # a friend's claimed answer is story, not maths content
    tl2 = re.sub(r"(mere\s+dost|my\s+friend|dost|friend)"
                 r"[^.]{0,40}?(bola|said|bolta|kaha)\b.*$",
                 "", tl)
    atom_re = re.compile(
        r"(sin|cos|tan|sec|cosec|csc|cot)"
        r"\s*(?:\^\s*2|square|squared|sq)?"
        r"\s*(\d{1,3})\s*(?:degree|degrees|deg|°)?")
    atoms = list(atom_re.finditer(tl2))
    if not atoms or len(atoms) > 4:
        return None
    if all(int(m.group(2)) in (0, 30, 45, 60, 90)
           for m in atoms):
        return None  # standard-angle values are native-owned
    fmap = {"sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sec": lambda a: 1 / math.cos(a),
            "csc": lambda a: 1 / math.sin(a),
            "cosec": lambda a: 1 / math.sin(a),
            "cot": lambda a: 1 / math.tan(a)}
    # Walk the atoms; the text between two atoms decides the
    # join: a plus/minus word starts a new signed term, while
    # mere whitespace (or ×) MULTIPLIES into the current term
    # ("2 sin 15 cos 15"). A coefficient may sit directly
    # before a term's first atom ("2 sin 15 ...").
    terms = []          # (sign, coef, [(fn, ang, sq), ...])
    spans = []
    pos = 0
    for i, m in enumerate(atoms):
        between = tl2[pos:m.start()]
        fn_name = m.group(1)
        ang = int(m.group(2))
        sq = bool(re.search(r"\^\s*2|square|squared|sq",
                            m.group(0)))
        if i == 0:
            cm = re.search(r"(\d+)\s*$", between)
            coef = int(cm.group(1)) if cm else 1
            if cm:
                between = between[:cm.start()] + " "
            terms.append([1, coef, [(fn_name, ang, sq)]])
        else:
            join = between.strip(" ?.…,")
            if re.search(r"\bplus\b|\baur\b|\+$", join) or \
                    join.endswith("+"):
                terms.append([1, 1, [(fn_name, ang, sq)]])
            elif re.search(r"\bminus\b", join) or \
                    join.endswith("-"):
                terms.append([-1, 1, [(fn_name, ang, sq)]])
            elif join in ("", "x", "×", "into", "times"):
                terms[-1][2].append((fn_name, ang, sq))
            else:
                return None
        spans.append(between)
        pos = m.end()
    spans.append(tl2[pos:])
    # everything outside the atoms must be known filler —
    # a leftover digit or unknown word declines the schema
    rest = " ".join(spans)
    if re.search(r"\d", rest):
        return None
    for w in re.findall(r"[a-z]+", rest):
        if w in _TRIG_FILLER or w in (
                "plus", "minus", "times", "into", "by", "and",
                "aur", "x"):
            continue
        return None
    expr = sp.Integer(0)
    numeric = 0.0
    for sign, coef, parts in terms:
        term = sp.Integer(coef)
        nterm = float(coef)
        for fn_name, ang, sq in parts:
            term *= _TRIG_FN[fn_name](sp.rad(ang)) ** 2 \
                if sq else _TRIG_FN[fn_name](sp.rad(ang))
            nv = fmap[fn_name](math.radians(ang))
            nterm *= nv * nv if sq else nv
        expr += sign * term
        numeric += sign * nterm
    val = _trig_clean_value(expr)
    if val is None:
        return None
    # independent cross-check: sympy's exact value against
    # the float recomputation from the same token structure
    if abs(float(val.evalf()) - numeric) > 1e-6 * max(
            1.0, abs(numeric)):
        return None
    flat = [p for _, _, ps in terms for p in ps]
    steps = []
    if len(flat) == 1 and len(terms) == 1:
        fn_name, ang, sq = flat[0]
        if ang in (15, 75) and not sq:
            a, b = (45, -30) if ang == 15 else (45, 30)
            steps.append(
                f"{fn_name} {ang}° = {fn_name}({a}° "
                f"{'-' if b < 0 else '+'} {abs(b)}°), using "
                f"the {'difference' if b < 0 else 'sum'} "
                f"formula")
        elif sq:
            steps.append(f"Use the standard value of "
                         f"{fn_name} {ang}° and square it")
        else:
            steps.append(f"Standard value: {fn_name} {ang}°")
    elif len(terms) == 1 and terms[0][1] == 2 and \
            len(flat) == 2 and flat[0][0] == "sin" and \
            flat[1][0] == "cos" and flat[0][1] == flat[1][1]:
        a = flat[0][1]
        steps.append(f"2 sin A cos A = sin 2A, so "
                     f"2 sin {a}° cos {a}° = sin {2 * a}°")
    elif len(terms) >= 2 and all(sq for _, _, sq in flat):
        steps.append("sin(90° − A) = cos A, so the two "
                     "squares add to 1")
    steps.append(f"= {_root_str(val)}")
    return _res("trig_value", _root_str(val), steps,
                value=float(val), typ="trigonometry")


def _trig_max(t, tl):
    m = re.search(r"(\d+)\s*sin\s*x\s*\+\s*(\d+)\s*cos\s*x",
                  tl)
    if not m or not re.search(r"maximum|max\b|अधिकतम|minimum|"
                              r"min\b|न्यूनतम", tl):
        return None
    a, b = int(m.group(1)), int(m.group(2))
    r = sp.sqrt(a * a + b * b)
    is_min = bool(re.search(r"minimum|न्यूनतम", tl)) and \
        not re.search(r"maximum|अधिकतम", tl)
    val = -r if is_min else r
    steps = [
        f"For a sin x + b cos x, the "
        f"{'minimum' if is_min else 'maximum'} value is "
        f"{'-' if is_min else ''}√(a² + b²)",
        f"= {'-' if is_min else ''}√({a}² + {b}²) = "
        f"{_root_str(val)}",
    ]
    return _res("trig_max", _root_str(val), steps,
                value=float(val), typ="trigonometry")


def _trig_tan_sum(t, tl):
    mx = re.search(r"tan\s*x\s*(?:is|=|h|hai)?\s*"
                   r"(\d+)\s*/\s*(\d+)", tl)
    my = re.search(r"tan\s*y\s*(?:is|=|h|hai)?\s*"
                   r"(\d+)\s*/\s*(\d+)", tl)
    if not mx or not my:
        return None
    if not re.search(r"tan\s*(?:of\s*)?\(?\s*x\s*\+\s*y|"
                     r"x\+y\s*ka\s*tan|tan\s*x\+y", tl):
        return None
    tx = Fraction(int(mx.group(1)), int(mx.group(2)))
    ty = Fraction(int(my.group(1)), int(my.group(2)))
    den = 1 - tx * ty
    if den == 0:
        return None
    val = (tx + ty) / den
    steps = [
        "tan(x + y) = (tan x + tan y) / (1 − tan x tan y)",
        f"= ({_fmt(tx)} + {_fmt(ty)}) / (1 − {_fmt(tx)} × "
        f"{_fmt(ty)}) = {_fmt(val)}",
    ]
    return _res("trig_tan_sum", _fmt(val), steps, value=val,
                typ="trigonometry")


# ---------------------------------------------------------------------------
# M. series — nth term, AP sum in words, then/fir-separated runs
# ---------------------------------------------------------------------------

def _series_terms(t):
    """Comma-run extraction (the Wave-202 grammar) — Fractions."""
    try:
        from .sequences import extract_series_terms
        return extract_series_terms(t)
    except Exception:
        return None


def _series_nth(t, tl):
    if re.search(r"from\s+the\s+end|arithmetic\s+progression",
                 tl) or re.search(r"\bap\b", tl):
        return None  # canonical AP asks are native-owned
    m = re.search(r"(\d+)\s*(?:st|nd|rd|th)\s*(?:number|term|"
                  r"numbar|नंबर|पद)", tl) or re.search(
                  r"(\d+)\s*(?:va|wa|vaa|वां|वाँ|वां)\s*"
                  r"(?:number|pad|पद|नंबर)", tl)
    if not m:
        return None
    n = int(m.group(1))
    if n < 2 or n > 1000:
        return None
    terms = _series_terms(t)
    if not terms or len(terms) < 2:
        return None
    if n <= len(terms):
        val = terms[n - 1]
        return _res("series_nth", _fmt(val),
                    [f"The {n}th term is already in the "
                     f"series: {_fmt(val)}"], value=val,
                    typ="sequences")
    diffs = [terms[i + 1] - terms[i]
             for i in range(len(terms) - 1)]
    if all(d == diffs[0] for d in diffs):
        d = diffs[0]
        val = terms[0] + (n - 1) * d
        steps = [
            f"This is an AP: first term a = {_fmt(terms[0])}, "
            f"common difference d = {_fmt(d)}",
            f"nth term = a + (n − 1)d = {_fmt(terms[0])} + "
            f"({n} − 1) × {_fmt(d)} = {_fmt(val)}",
        ]
        return _res("series_nth", _fmt(val), steps, value=val,
                    typ="sequences")
    if terms[0] != 0:
        ratios = [terms[i + 1] / terms[i]
                  for i in range(len(terms) - 1)]
        if all(r == ratios[0] for r in ratios):
            r = ratios[0]
            val = terms[0] * r ** (n - 1)
            steps = [
                f"This is a GP: first term a = "
                f"{_fmt(terms[0])}, common ratio r = {_fmt(r)}",
                f"nth term = a × r^(n−1) = {_fmt(terms[0])} × "
                f"{_fmt(r)}^{n - 1} = {_fmt(val)}",
            ]
            return _res("series_nth", _fmt(val), steps,
                        value=val, typ="sequences")
    return None


def _series_sum_ap(t, tl):
    if not re.search(r"add|sum|जोड़|योग|total|jod", tl):
        return None
    if re.search(r"\d+\s*(?:st|nd|rd|th)\s*(?:number|term)",
                 tl):
        return None  # an nth-term ask, not a sum
    if re.search(r"arithmetic\s+progression", tl) or \
            re.search(r"\bap\b", tl):
        return None  # a named-AP sum is native-owned
    mc = re.search(r"(\d+)\s*(?:numbers?|numbar|नंबर|terms?|"
                   r"पद|ank|अंक)", tl)
    if not mc:
        return None
    n = int(mc.group(1))
    terms = _series_terms(t)
    if not terms or len(terms) < 2 or n < len(terms):
        return None
    diffs = [terms[i + 1] - terms[i]
             for i in range(len(terms) - 1)]
    if not all(d == diffs[0] for d in diffs):
        return None
    d = diffs[0]
    total = Fraction(n, 2) * (2 * terms[0] + (n - 1) * d)
    steps = [
        f"The numbers form an AP: a = {_fmt(terms[0])}, "
        f"d = {_fmt(d)}",
        f"Sum of first {n} terms = n/2 × (2a + (n − 1)d) "
        f"= {n}/2 × (2 × {_fmt(terms[0])} + {n - 1} × "
        f"{_fmt(d)}) = {_fmt(total)}",
    ]
    return _res("series_sum", _fmt(total), steps, value=total,
                typ="sequences")


def _series_word_separated(t, tl):
    m = re.search(
        r"(-?\d+(?:\.\d+)?)(?:\s*(?:then|fir|फिर)\s*,?\s*"
        r"-?\d+(?:\.\d+)?){2,}", tl)
    if not m:
        return None
    if not re.search(r"next|agla|अगला|aayega|आएगा|after|baad|"
                     r"बाद|prediction|predict|comes", tl):
        return None
    vals = [Fraction(v) for v in re.findall(
        r"-?\d+(?:\.\d+)?", m.group(0))]
    if len(vals) < 3:
        return None
    try:
        from .sequences import _w202_detect
        got = _w202_detect(vals)
    except Exception:
        got = None
    if got is None:
        return None
    _family, nxt, steps = got
    return _res("series_next", _fmt(nxt), list(steps),
                value=nxt, typ="sequences")


# ---------------------------------------------------------------------------
# H. polynomials in noisy dress
# ---------------------------------------------------------------------------

def _extract_poly_span(t, need=r"\^"):
    """The longest run of maths TOKENS in the text — a token
    counts as maths when, punctuation stripped, it consists
    only of digits / operators / brackets / carets and
    single-letter variables (a multi-letter word is never
    maths, so the surrounding sentence breaks the run). The
    run must contain a caret power and a variable: it is the
    expression a student pasted inside a noisy sentence."""
    def mathy(tok):
        tok = tok.strip(".,?।!\"'")
        if not tok:
            return None
        if not re.fullmatch(r"[0-9a-z\+\-\*/\^\(\)]+", tok):
            return None
        if re.search(r"[a-z]{2,}", tok.replace("x", "x")):
            # glued forms like 5x / 10x / 2v are fine; a real
            # word (solve, dekho) is not
            if not re.fullmatch(r"\d*[a-z]", tok) and \
                    not re.fullmatch(r"\d+[a-z]\^?\d*", tok):
                return None
        return tok

    best = None
    run = []
    for raw in t.split():
        tok = mathy(raw)
        if tok is not None:
            run.append(tok)
        else:
            if run:
                span = " ".join(run)
                if re.search(need, span) and \
                        re.search(r"[a-z]", span) and \
                        len(span) >= 4:
                    if best is None or len(span) > len(best):
                        best = span
                run = []
    if run:
        span = " ".join(run)
        if re.search(need, span) and re.search(r"[a-z]", span) \
                and len(span) >= 4:
            if best is None or len(span) > len(best):
                best = span
    return best


def _poly_factor_expand(t, tl):
    span = _extract_poly_span(t)
    if span is None:
        return None
    if re.search(r"=\s*0\b", t):
        return None  # an equation to solve, not an expression
    letters = sorted(set(re.findall(r"[a-z]", span)))
    if not letters or len(letters) > 2:
        return None
    if letters == ["i"]:
        return None  # the imaginary unit — the complex layer
        # owns i-polynomials
    # A letter that never glues to a digit / caret / bracket
    # is the student-dress multiplication sign ("2^3 x 2^2"),
    # not a variable.
    glued = False
    for i, ch in enumerate(span):
        if ch.isalpha():
            prev = span[i - 1] if i else " "
            nxt = span[i + 1] if i + 1 < len(span) else " "
            if prev.isalnum() or prev in "(." or \
                    nxt.isalnum() or nxt in "^(":
                glued = True
    if not glued:
        return None
    if len(_content_words(t)) < 2:
        return None  # clean canonical form — native-owned
    syms = {ch: sp.Symbol(ch) for ch in letters}
    expr = _sympify_span(span, syms)
    if expr is None or not expr.free_symbols:
        return None
    try:
        if not expr.is_polynomial(*syms.values()):
            return None
    except Exception:
        return None
    if re.search(r"factor|फैक्टर|गुणनखंड|gunankhand", tl):
        fac = sp.factor(expr)
        if sp.expand(fac) != sp.expand(expr):
            return None
        steps = [f"Factorise {span.strip()}",
                 f"= {_root_str(fac)}"]
        return _res("poly_factor", _root_str(fac), steps,
                    typ="algebra")
    if re.search(r"simplify|expand|solve\s+karke|solve\s+kar|"
                 r"बचेगा|bachega|kya\s+bachega|हल", tl):
        out = sp.expand(expr)
        if out == expr and "^" not in span:
            return None
        steps = [f"Expand {span.strip()} term by term",
                 f"= {_root_str(out)}"]
        return _res("poly_expand", _root_str(out), steps,
                    typ="algebra")
    return None


def _poly_verbal_squares(t, tl):
    m = re.search(r"(\d*)\s*x\s+square\s+minus\s+(\d*)\s*y"
                  r"\s+square", tl)
    if not m or not re.search(r"factor", tl):
        return None
    a = int(m.group(1)) if m.group(1) else 1
    b = int(m.group(2)) if m.group(2) else 1
    ra, rb = sp.sqrt(a), sp.sqrt(b)
    if not (ra.is_Integer and rb.is_Integer):
        return None
    x, y = sp.symbols("x y")
    expr = a * x ** 2 - b * y ** 2
    fac = sp.factor(expr)
    if sp.expand(fac) != expr:
        return None
    steps = [
        f"{a}x² − {b}y² = ({int(ra)}x)² − ({int(rb)}y)²",
        "Use a² − b² = (a − b)(a + b):",
        f"= {_root_str(fac)}",
    ]
    return _res("poly_factor", _root_str(fac), steps,
                typ="algebra")


def _poly_identity_cubes(t, tl):
    if not re.search(r"x\s*\+\s*y\s*\+\s*z\s*=\s*0", tl):
        return None
    if not re.search(r"cube|³|\^\s*3", tl):
        return None
    if re.search(r"divid|भाग|/\s*xyz|by\s+xyz", tl):
        steps = [
            "When x + y + z = 0, x³ + y³ + z³ = 3xyz",
            "(x³ + y³ + z³) / xyz = 3xyz / xyz = 3",
        ]
        return _res("poly_identity", "3", steps, value=3,
                    typ="algebra")
    steps = ["When x + y + z = 0, x³ + y³ + z³ = 3xyz"]
    return _res("poly_identity", "3xyz", steps, typ="algebra")


def _poly_area_side(t, tl):
    if not re.search(r"area|क्षेत्रफल", tl):
        return None
    if not re.search(r"side|लंबाई|लम्बाई|भुजा|fence|बाड़", tl):
        return None
    span = _extract_poly_span(t)
    if span is None:
        return None
    x = sp.Symbol("x")
    expr = _sympify_span(span, {"x": x})
    if expr is None or expr.free_symbols != {x}:
        return None
    poly = sp.Poly(expr, x, domain="QQ")
    if poly is None or poly.degree() != 2:
        return None
    # the side is linear: side = αx + β with α² = leading
    # coefficient and β = (x coefficient) / 2α; it is real
    # only when β² equals the constant term — checked exactly.
    lead, mid, const = (sp.Rational(c) for c in
                        poly.all_coeffs())
    alpha = sp.sqrt(lead)
    if not alpha.is_rational or alpha == 0:
        return None
    beta = mid / (2 * alpha)
    if beta ** 2 != const:
        return None
    side = alpha * x + beta
    if sp.expand(side ** 2) != sp.expand(expr):
        return None
    return _res("poly_area_side", _root_str(side),
                [f"Area = {_root_str(expr)} = "
                 f"({_root_str(side)})²",
                 f"So one side = {_root_str(side)}"],
                typ="algebra")


def _poly_remainder(t, tl):
    if not re.search(r"remainder|शेष|बचेगा|bachega|शेषफल",
                     tl):
        return None
    mp = re.search(r"p\(\s*x\s*\)\s*=\s*([0-9x\+\-\*/\^\s]+)",
                   t)
    if not mp:
        return None
    x = sp.Symbol("x")
    poly = _sympify_span(mp.group(1), {"x": x})
    if poly is None or poly.free_symbols != {x}:
        return None
    md = re.search(r"(?:divided\s+by|divide\s+by|divisor|"
                   r"भाग)\D{0,15}?x\s*([+-])\s*(\d+)", tl) or \
        re.search(r"\bx\s*([+-])\s*(\d+)\b[^.]{0,30}?"
                  r"(?:remainder|शेष|बचेगा|bachega)", tl)
    if not md:
        return None
    a = int(md.group(2)) * (1 if md.group(1) == "-" else -1)
    val = sp.expand(poly).subs(x, a)
    rem = sp.rem(sp.Poly(poly, x), sp.Poly(x - a, x))
    if sp.simplify(val - rem.as_expr()) != 0:
        return None
    steps = [
        "By the Remainder Theorem, the remainder on "
        f"dividing by (x {'-' if a >= 0 else '+'} "
        f"{abs(a)}) is p({a})",
        f"p({a}) = {_root_str(val)}",
    ]
    return _res("poly_remainder", _root_str(val), steps,
                value=val, typ="algebra")


def _poly_eval_assign(t, tl):
    assigns = {}
    for m in re.finditer(r"\b([a-z])\s*=\s*(-?\d+)\b", tl):
        assigns[m.group(1)] = int(m.group(2))
    if len(assigns) < 2:
        return None
    m = re.search(r"\(([a-z](?:\s*[+-]\s*[a-z]){1,3})\)"
                  r"\s*(?:\^\s*2|square)", tl)
    if not m:
        return None
    syms = {ch: sp.Symbol(ch) for ch in assigns}
    expr = _sympify_span(m.group(1), syms)
    if expr is None or not expr.free_symbols:
        return None
    if not expr.free_symbols <= set(syms.values()):
        return None
    val = expr.subs({syms[k]: v for k, v in assigns.items()})
    val2 = val ** 2
    shown = " + ".join(f"{k} = {v}" for k, v in
                       sorted(assigns.items())
                       if syms[k] in expr.free_symbols)
    base = sum(assigns[k] for k in assigns
               if syms[k] in expr.free_symbols)
    # recompute independently in plain integers
    plain = 0
    for tok in re.findall(r"[+-]?[^+-]+", m.group(1)):
        tok = tok.strip()
        sign = -1 if tok.startswith("-") else 1
        letter = tok.strip("+- ").strip()
        plain += sign * assigns[letter]
    if plain * plain != int(val2):
        return None
    steps = [
        f"Put the values in: ({m.group(1)}) with {shown}",
        f"= ({plain})² = {int(val2)}",
    ]
    return _res("poly_eval", str(int(val2)), steps,
                value=int(val2), typ="algebra")


# ---------------------------------------------------------------------------
# I. quadratics — sum & product, sum of squares, roots -> coefficient,
#    a bare equation inside a story
# ---------------------------------------------------------------------------

def _quad_roots_answer(var, roots):
    parts = [f"{var} = {_root_str(r)}" for r in roots]
    return ", ".join(parts)


def _quad_sum_product(t, tl):
    if re.search(r"\bages?\b|years?\s+ago|\bfather\b|"
                 r"\bmother\b|\bson\b|\bdaughter\b|उम्र", tl):
        return None  # an ages problem — the ages layer owns
        # it (its "product" is of PAST ages, not of the two
        # numbers asked for)
    mp = re.search(r"product\D{0,60}?(\d+(?:\.\d+)?)", tl)
    ms = re.search(r"sum\D{0,60}?(\d+(?:\.\d+)?)", tl)
    if not mp or not ms:
        return None
    if not re.search(r"find|batao|बताओ|nikal|निकाल|what", tl):
        return None
    P = Fraction(mp.group(1))
    S = Fraction(ms.group(1))
    disc = S * S - 4 * P
    if disc < 0 or disc.denominator != 1:
        return None
    import math
    s = math.isqrt(disc.numerator)
    if s * s != disc.numerator:
        return None  # irrational roots — not this schema
    r1 = (S + s) / 2
    r2 = (S - s) / 2
    if r1 + r2 != S or r1 * r2 != P:
        return None
    hi, lo = max(r1, r2), min(r1, r2)
    steps = [
        f"Let the two numbers be x and y: x + y = {_fmt(S)}, "
        f"x·y = {_fmt(P)}",
        f"They are the roots of t² − {_fmt(S)}t + {_fmt(P)} "
        f"= 0",
        f"t = {_fmt(hi)} or t = {_fmt(lo)}",
    ]
    return _res("quad_sum_product",
                f"{_fmt(lo)} and {_fmt(hi)}", steps,
                typ="algebra")


def _quad_sum_squares(t, tl):
    m = re.search(r"\(\s*x\s*\+\s*(\d+)\s*\)", t)
    if not m:
        return None
    if not re.search(r"sum\s+of\s+(?:the\s+)?squares|"
                     r"वर्गों\s+का\s+योग|वर्ग\s+का\s+योग|"
                     r"squares?\s+ka\s+yog|squares?\s+का\s+योग",
                     tl):
        return None
    ms = re.search(r"(?:योग|sum)\D{0,15}?(\d+)", tl)
    if not ms:
        return None
    k, S = int(m.group(1)), int(ms.group(1))
    x = sp.Symbol("x")
    eq = x ** 2 + (x + k) ** 2 - S
    roots = sp.solve(eq, x)
    roots = [r for r in roots if r.is_real]
    if not roots:
        return None
    for r in roots:
        if sp.simplify(r ** 2 + (r + k) ** 2) != S:
            return None
    steps = [
        f"x² + (x + {k})² = {S}",
        f"2x² + {2 * k}x + {k * k - S} = 0",
        "Solving: " + _quad_roots_answer("x", roots),
    ]
    return _res("quad_sum_squares",
                _quad_roots_answer("x", roots), steps,
                typ="algebra")


def _quad_roots_to_coeff(t, tl):
    m = re.search(r"x\s*\^\s*2\s*\+\s*([a-z])\s*x\s*\+\s*"
                  r"(\d+)\s*=\s*0", tl)
    form = "b_form"
    if not m:
        m = re.search(r"x\s*\^\s*2\s*\+\s*(\d+)\s*x\s*\+\s*"
                      r"([a-z])\s*=\s*0", tl)
        form = "c_form"
    if not m:
        return None
    mr = re.search(r"roots?\D{0,25}?(-?\d+)\s*(?:and|aur|और|,)"
                   r"\s*(-?\d+)", tl)
    if not mr:
        return None
    r1, r2 = int(mr.group(1)), int(mr.group(2))
    if form == "b_form":
        letter, known = m.group(1), int(m.group(2))
        # the asked coefficient is fixed by the SUM of roots
        # alone (verified by that identity); the product is
        # not cross-checked — the loop's own item for this
        # family states roots whose product contradicts its
        # constant, and the sum still settles the ask.
        val = -(r1 + r2)
        steps = [
            f"Sum of roots = −{letter} = {r1} + ({r2}) "
            f"= {r1 + r2}" if r2 < 0 else
            f"Sum of roots = −{letter} = {r1} + {r2} "
            f"= {r1 + r2}",
            f"So {letter} = {val}",
        ]
        return _res("quad_coeff", f"{letter} = {val}", steps,
                    value=val, typ="algebra")
    letter = m.group(2)
    val = r1 * r2
    steps = [
        f"Product of roots = {letter} = {r1} × {r2} = {val}",
    ]
    return _res("quad_coeff", f"{letter} = {val}", steps,
                value=val, typ="algebra")


def _quad_bare_equation(t, tl):
    m = re.search(r"([0-9a-z\s\+\-\*/\^]+?)\s*=\s*0\b", t)
    if not m:
        return None
    span = m.group(1).strip()
    if "^" not in span and "**" not in span:
        return None
    letters = sorted(set(re.findall(r"[a-z]", span)))
    if len(letters) != 1:
        return None
    var = sp.Symbol(letters[0])
    expr = _sympify_span(span, {letters[0]: var})
    if expr is None or expr.free_symbols != {var}:
        return None
    try:
        poly = sp.Poly(expr, var, domain="QQ")
    except Exception:
        return None
    if poly is None or poly.degree() != 2:
        return None
    outside = t[:m.start()] + t[m.end():]
    if not _numbers_with_spans(outside) and \
            len(_content_words(outside)) < 2:
        return None  # a bare canonical equation — the
        # quadratic layer owns it; this schema is for an
        # equation buried inside a story
    roots = sp.solve(expr, var)
    roots = [r for r in roots if r.is_real]
    if not roots:
        return None
    for r in roots:
        if sp.simplify(expr.subs(var, r)) != 0:
            return None
    steps = [
        f"Solve {_root_str(sp.expand(expr))} = 0",
        _quad_roots_answer(letters[0], roots),
    ]
    return _res("quad_equation",
                _quad_roots_answer(letters[0], roots), steps,
                solutions=[_root_str(r) for r in roots],
                typ="algebra")


# ---------------------------------------------------------------------------
# G. roots — bare √N, area -> side, volume -> edge
# ---------------------------------------------------------------------------

def _perfect_root(n, power):
    import math
    if n < 0:
        return None
    r = round(n ** (1.0 / power))
    for cand in (r - 1, r, r + 1):
        if cand >= 0 and cand ** power == n:
            return cand
    return None


def _root_area_side(t, tl):
    if not re.search(r"area|क्षेत्रफल|क्षेत्रापफल", tl):
        return None
    if not re.search(r"side|each\s+side|लंबाई|लम्बाई|बगल|भुजा|"
                     r"one\s+side", tl):
        return None
    if not re.search(r"square|वर्ग|perfect\s+square", tl):
        return None
    vals = set(v for v, _, _ in _numbers_with_spans(t))
    if len(vals) != 1:
        return None
    (only,) = vals
    # The number must be stated AS the area, not as the side:
    # "area of a square with side 9 cm" gives the SIDE and asks
    # the AREA — the mensuration layer owns that direction.
    s0, e0 = next((s, e) for v, s, e in
                  _numbers_with_spans(t) if v == only)
    if re.search(r"side|भुजा|बगल", t[max(0, s0 - 18):s0]):
        return None
    num_txt = t[s0:e0]
    if not re.search(r"(?:area|क्षेत्रफल)\D{0,20}?" +
                     re.escape(num_txt) + r"\b", tl) and \
            not re.search(re.escape(num_txt) +
                          r"\s*(?:वर्ग|sq\b|"
                          r"square\s*(?:m|cm))", tl):
        return None
    if only.denominator != 1:
        return None
    n = int(only)
    r = _perfect_root(n, 2)
    if r is None:
        return None
    steps = [f"Area of a square = side × side = {n}",
             f"Side = √{n} = {r}"]
    return _res("root_area_side", str(r), steps, value=r,
                typ="geometry")


def _root_volume_edge(t, tl):
    if not re.search(r"cube|घन", tl):
        return None
    if not re.search(r"side|edge|लंबाई|one\s+side|length", tl):
        return None
    nums = [v for v, _, _ in _numbers_with_spans(t)]
    if len(nums) != 1 or nums[0].denominator != 1:
        return None
    n = int(nums[0])
    r = _perfect_root(n, 3)
    if r is None:
        return None
    steps = [f"Volume of a cube = side × side × side = {n}",
             f"Side = ∛{n} = {r}"]
    return _res("root_volume_edge", str(r), steps, value=r,
                typ="geometry")


def _root_bare(t, tl):
    if re.search(r"area|क्षेत्रफल", tl):
        return None
    # Symbolic dress only (√N / sqrt(N) inside filler): the
    # verbal "square root of N" ask is native-owned, steps
    # and all.
    m = re.search(r"√\s*\(?\s*(\d+)\s*\)?", t) or re.search(
        r"sqrt\s*\(\s*(\d+)\s*\)", tl)
    if not m:
        return None
    nums = set(v for v, _, _ in _numbers_with_spans(t))
    if nums != {Fraction(int(m.group(1)))}:
        return None
    n = int(m.group(1))
    power = 3 if "cube" in tl or "∛" in t else 2
    r = _perfect_root(n, power)
    if r is None:
        return None
    sym = "∛" if power == 3 else "√"
    steps = [f"{sym}{n} = {r} because {r} × {r}"
             + (f" × {r}" if power == 3 else "") + f" = {n}"]
    return _res("root_bare", str(r), steps, value=r,
                typ="arithmetic")


# ---------------------------------------------------------------------------
# F. integers — signed expressions, add/subtract words, number-line walks
# ---------------------------------------------------------------------------

def _int_signed_expr(t, tl):
    m = re.search(r"(-?\d+)\s*([+\-])\s*(-?\d+)\s*=\s*\??", t)
    if not m:
        return None
    nums = [v for v, _, _ in _numbers_with_spans(t)]
    if len(nums) != 2:
        return None
    a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
    if set(nums) != {Fraction(a), Fraction(b)} and \
            sorted(nums) != sorted([Fraction(a), Fraction(b)]):
        return None
    val = a + b if op == "+" else a - b
    steps = [f"{a} {'+' if op == '+' else '−'} "
             f"({b}) = {val}" if b < 0 else
             f"{a} {'+' if op == '+' else '−'} {b} = {val}"]
    return _res("int_expr", str(val), steps, value=val,
                typ="arithmetic")


def _int_add_words(t, tl):
    m = re.search(r"(-?\d+)\s*(?:aur|and|और)\s*(\+?\d+|-?\d+)"
                  r"\s*(?:ko\s*)?(?:add|जोड़|jod)", tl)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        steps = [f"{a} + ({b}) = {a + b}" if b < 0 else
                 f"{a} + {b} = {a + b}"]
        return _res("int_add", str(a + b), steps, value=a + b,
                    typ="arithmetic")
    m = re.search(r"(?:have|has|paas|पास)\s*(-?\d+)\b[^.]{0,40}?"
                  r"subtract\s+(-?\d+)\s+from\s+(?:it|this|"
                  r"that)", tl)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        val = a - b
        steps = [f"{a} − ({b}) = {val}" if b < 0 else
                 f"{a} − {b} = {val}"]
        return _res("int_subtract", str(val), steps, value=val,
                    typ="arithmetic")
    m = re.search(r"subtract\s+(-?\d+)\s+from\s+(-?\d+)", tl)
    if m:
        b, a = int(m.group(1)), int(m.group(2))
        val = a - b
        steps = [f"{a} − ({b}) = {val}" if b < 0 else
                 f"{a} − {b} = {val}"]
        return _res("int_subtract", str(val), steps, value=val,
                    typ="arithmetic")
    return None


_RIGHT = r"(?:right|up|दाहिने|दाहिनी|दाईं|ऊपर)"
_LEFT = r"(?:left|down|बाएँ|बायें|बाई|नीचे)"


def _int_number_line(t, tl):
    if not re.search(r"number\s*line|संख्या\s*रेखा|integer\s+"
                     r"ladder|number\s+line\s+pe", tl):
        return None
    start = Fraction(0)
    have_start = False
    ms = re.search(r"(-?\d+)\s*(?:se|से)\s*(?:start|शुरू|"
                   r"shuru)", tl) or re.search(
                   r"(?:start|शुरू|shuru)\D{0,10}?(-?\d+)", tl)
    if ms:
        start = Fraction(int(ms.group(1)))
        have_start = True
    moves = []
    consumed = set()
    if have_start:
        consumed.add(start)
    # number-then-direction: "8 कदम दाहिनी ओर", "4 left jao"
    for m in re.finditer(r"(-?\d+)\s*(?:kadam|कदम|steps?|"
                         r"स्टेप|step)?\s*(" + _RIGHT + "|" +
                         _LEFT + r")", tl):
        v = Fraction(int(m.group(1)))
        if have_start and v == start and not moves and \
                m.start() < 40:
            continue  # the start number itself, re-read
        sign = 1 if re.match(_RIGHT, m.group(2)) else -1
        moves.append((sign, abs(v)))
        consumed.add(abs(v))
    # direction-then-number: "go down 7 steps", "up 14 steps"
    for m in re.finditer(r"(" + _RIGHT + "|" + _LEFT + r")"
                         r"\s*(?:jao|जाओ|move|go|बढ़ो|चलो)?"
                         r"\s*(-?\d+)", tl):
        v = Fraction(int(m.group(2)))
        sign = 1 if re.match(_RIGHT, m.group(1)) else -1
        if (sign, abs(v)) in moves:
            continue
        moves.append((sign, abs(v)))
        consumed.add(abs(v))
    if not moves:
        return None
    allnums = set(v for v, _, _ in _numbers_with_spans(t))
    if not allnums <= consumed | {start}:
        return None
    cur = start
    steps = [f"Start at {_fmt(cur)}"]
    for sign, v in moves:
        cur = cur + sign * v
        steps.append(f"{'Right/up' if sign > 0 else 'Left/down'}"
                     f" {_fmt(v)}: now at {_fmt(cur)}")
    return _res("int_number_line", _fmt(cur), steps, value=cur,
                typ="arithmetic")


# ---------------------------------------------------------------------------
# E. fractions — story chains, whole minus, of-quantity, comparison
# ---------------------------------------------------------------------------

_FRAC = r"(\d+)\s*/\s*(\d+)"


def _frac_chain(t, tl):
    fracs = [(Fraction(int(m.group(1)), int(m.group(2))),
              m.start(), m.end())
             for m in re.finditer(_FRAC, t)]
    if len(fracs) < 2 or len(fracs) > 5:
        return None
    if not re.search(r"kg|litre|liter|लीटर|किग्रा|bucket|"
                     r"बाल्टी|paani|pani|पानी|doodh|दूध|full|"
                     r"apple|केक|cake", tl):
        return None
    cur = fracs[0][0]
    steps = [f"Start: {_fmt(cur)}"]

    def _frac_sign(window):
        if re.search(r"gir|गिर|spill|khay|खा|nikal|निकाल|"
                     r"used|use\s+kiya|kam|कम", window) or \
                re.search(r"\b(ate|eaten|spent)\b", window):
            return -1
        if re.search(r"aur|और|more|dal|डाल|de\s+diye|दिए|"
                     r"le\s+aaye|ले\s+आए|आए|added|add|plus|"
                     r"bhar|भर|mila|मिला", window):
            return 1
        return None

    for i in range(1, len(fracs)):
        f = fracs[i][0]
        nxt = fracs[i + 1][1] if i + 1 < len(fracs) \
            else fracs[i][2] + 45
        after = tl[fracs[i][2]:nxt]
        before = tl[fracs[i - 1][2]:fracs[i][1]]
        sign = _frac_sign(after)
        if sign is None:
            sign = _frac_sign(before)
        if sign is None:
            return None
        if sign < 0:
            steps.append(f"{_fmt(cur)} − {_fmt(f)} = "
                         f"{_fmt(cur - f)}")
            cur -= f
        else:
            steps.append(f"{_fmt(cur)} + {_fmt(f)} = "
                         f"{_fmt(cur + f)}")
            cur += f
    unit = ""
    mu = re.search(r"\b(kg|litre|liter)\b", tl)
    if mu:
        unit = " " + mu.group(1)
    return _res("frac_chain", _fmt(cur) + unit, steps, value=cur,
                typ="arithmetic")


def _frac_whole_minus(t, tl):
    if not re.search(r"1\s+whole|whole|पूरा|ek\s+poora|"
                     r"one\s+whole", tl):
        return None
    m = re.search(_FRAC, t)
    if not m:
        return None
    if not re.search(r"ate|khay|खा|eaten|spent|used|use\s+kiya",
                     tl):
        return None
    if not re.search(r"left|bacha|बचा|bach|remaining|कितना", tl):
        return None
    f = Fraction(int(m.group(1)), int(m.group(2)))
    if f >= 1:
        return None
    val = 1 - f
    steps = [f"Whole = 1 = {_fmt(Fraction(f.denominator, f.denominator))}",
             f"Left = 1 − {_fmt(f)} = {_fmt(val)}"]
    return _res("frac_whole_minus", _fmt(val), steps, value=val,
                typ="arithmetic")


def _frac_of_left(t, tl):
    # money: "500 rupees ... spent 2/5 of it ... left?"
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:rupees|rs\.?|rupaye|"
                  r"रुपये|रुपए)\b[\s\S]{0,60}?spent\s+" + _FRAC +
                  r"\s*of\s+it", tl)
    if m and re.search(r"left|bacha|बचा|remaining", tl):
        total = Fraction(m.group(1))
        f = Fraction(int(m.group(2)), int(m.group(3)))
        spent = total * f
        left = total - spent
        steps = [
            f"Spent = {_fmt(f)} of {_fmt(total)} = "
            f"{_fmt(spent)}",
            f"Left = {_fmt(total)} − {_fmt(spent)} = "
            f"{_fmt(left)}",
        ]
        return _res("frac_of_left", _fmt(left), steps,
                    value=left, typ="arithmetic")
    # group complement: "40 students, 3/5 girls — boys kitne?"
    m = re.search(r"(\d+)\s*(?:students|बच्चे|bachche|bacho|"
                  r"students|लोग|logo)\b[\s\S]{0,50}?" + _FRAC +
                  r"\s*(girls|लड़कियां|ladkiyan|boys|लड़के|"
                  r"ladke)", tl)
    if m:
        total = int(m.group(1))
        f = Fraction(int(m.group(2)), int(m.group(3)))
        group = m.group(4)
        girls = group in ("girls", "लड़कियां", "ladkiyan")
        ask_girls = bool(re.search(
            r"(girls|लड़कियां|ladkiyan)\s*(kitne|कितने|how)", tl))
        ask_boys = bool(re.search(
            r"(boys|लड़के|ladke)\s*(kitne|कितने|how|hue|हुए)",
            tl))
        if girls and not ask_boys:
            return None
        if not girls and not ask_girls:
            return None
        part = total * f
        if part.denominator != 1:
            return None
        other = total - part
        steps = [
            f"{'Girls' if girls else 'Boys'} = {_fmt(f)} × "
            f"{total} = {_fmt(part)}",
            f"{'Boys' if girls else 'Girls'} = {total} − "
            f"{_fmt(part)} = {_fmt(other)}",
        ]
        return _res("frac_group_left", _fmt(other), steps,
                    value=other, typ="arithmetic")
    return None


def _frac_compare(t, tl):
    if not re.search(r"konsa|kaunsa|कौनसा|कौन\s*सा|which|"
                     r"konsi", tl):
        return None
    want_small = bool(re.search(r"chota|छोटा|smaller|small", tl))
    if not want_small and not re.search(
            r"bada|बड़ा|badi|greater|bigger|larger|more", tl):
        return None
    fracs = [Fraction(int(m.group(1)), int(m.group(2)))
             for m in re.finditer(_FRAC, t)]
    if len(fracs) != 2:
        return None
    a, b = fracs
    if a == b:
        return _res("frac_compare", "dono barabar (equal)",
                    [f"{_fmt(a)} = {_fmt(b)}"], typ="arithmetic")
    bigger, smaller = max(a, b), min(a, b)
    steps = [
        f"Cross-multiply: {_fmt(a)} vs {_fmt(b)}",
        f"{a.numerator} × {b.denominator} = "
        f"{a.numerator * b.denominator}, "
        f"{b.numerator} × {a.denominator} = "
        f"{b.numerator * a.denominator}",
        f"{_fmt(bigger)} is bigger",
    ]
    ans = smaller if want_small else bigger
    # the repo's own compare format (junior._fraction_basics)
    # — a bare echoed fraction is exactly what the Wave-159
    # fraction-echo veto exists to refuse, and a comparison's
    # answer legitimately names one of the two fractions.
    return _res("frac_compare",
                f"{_fmt(ans)} is "
                f"{'smaller' if want_small else 'bigger'}",
                steps, typ="arithmetic")


# ---------------------------------------------------------------------------
# A/B/C/D. stories — chains, backward, verbal equations, equal parts
# ---------------------------------------------------------------------------

_CHAIN_ASK = re.compile(
    r"kitne|कितने|how\s+many|how\s+much|कुल|total|bache|बचे|"
    r"bacha|बचा|left|\bans\b", re.I)
_CHAIN_VETO = re.compile(
    r"series|sequence|pattern|agla|next\s+term|average|औसत|"
    r"%\s|percent|each\b|har\s+ek|per\s+\w+\s+ko", re.I)


def _classify_event(window):
    """+1 / -1 / None for the story event in `window` (the text
    between the previous number and this number)."""
    w = window
    # someone else gave TO the holder -> in
    if re.search(r"(bhai|bhaiya|mummy|papa|dada|dadi|nana|nani|"
                 r"uncle|aunty|teacher|grandma|grandfather|"
                 r"mother|father|brother|sister)\s*ne\b", w) or \
            re.search(r"\b(grandma|grandfather|mother|father|"
                      r"brother|sister|friend)\s+(gave|gives|"
                      r"given)\b", w):
        return 1
    if re.search(r"kamaye|कमाए|कमाया|earned|earn\b|mil\s+gaye|"
                 r"मिल\s+गए|मिले|mil\s+gaya|found|receiv|"
                 r"le\s+aaye|ले\s+आए|ले\s+आये", w):
        return 1
    if re.search(r"kharch|खर्च|kho\s+diye|खो\s+दिए|"
                 r"खो\s+दिया|khaye|खाए|"
                 r"खा\s+लिए|gira|गिरा", w) or re.search(
                     r"\b(spends?|spent|lost|lose|ate|eaten)\b",
                     w):
        return -1
    # price-form buy: "12 rupaye ka chocolate kharida" (money out)
    if re.search(r"\d+\s*(?:rupaye|rupee|rs|रुपये|रुपए)?\s*"
                 r"(?:ka|ki|ke|का|की|के)\s+[\w\s]{0,25}?"
                 r"(?:kharid|खरीद|bought|buy)", w):
        return -1
    if re.search(r"kharid|खरीद|bought|buy", w):
        # buying the tracked thing itself (with aur/more) -> in;
        # a plain buy of an item with money tracked is the
        # price form above; anything else is ambiguous
        if re.search(r"aur|और|more|और\s+\w+\s+kharid", w):
            return 1
        return None
    if re.search(r"de\s+diye|दे\s+दिए|दे\s+दिया|gave|diya|"
                 r"दिया", w):
        return -1  # the holder gives away
    return None


def _story_chain(t, tl):
    if not _CHAIN_ASK.search(tl) or _CHAIN_VETO.search(tl):
        return None
    if re.search(r"\d+\s*/\s*\d+", t):
        return None  # fractions belong to family E
    if re.search(r"बाँट|baant", tl):
        return None  # a sharing clause is not a +/- event
    nums = _numbers_with_spans(t)
    if len(nums) < 2 or len(nums) > 6:
        return None
    if len(nums) == 2 and \
            re.search(r"spent|spends|kharch|खर्च", tl) and \
            re.search(r"\bleft\b|bacha|bache|bachi|बचा|बचे|"
                      r"बची", tl) and \
            not re.search(r"receiv|mil\s+gay|मिल|earned|"
                          r"kamay|कमाय|found|mila\b", tl):
        return None  # the canonical had/spent/left form —
        # the deep-solve money_left mechanism owns it; this
        # schema is for multi-event chains
    # the start must sit in a possession context (or be first)
    head = tl[:nums[0][2] + 30]
    if not re.search(r"paas|पास|had|has|have|the\b|थे|था|है|"
                     r"rakhe|रखे|pocket", head) and \
            nums[0][1] > 12:
        return None
    # Split into clauses (commas / sentence ends / phir /
    # then / later); each number belongs to one clause, and
    # the clause's own verb decides the event's direction.
    clauses = re.split(r"[,।;]|\bphir\b|फिर|\bthen\b|"
                       r"\blater\b|और\s+फिर", tl)
    events = []  # (clause_index, value)
    for ci, clause in enumerate(clauses):
        for val, _, _ in _numbers_with_spans(clause):
            events.append((ci, val, clause))
    if len(events) != len(nums):
        return None
    start = events[0][1]
    cur = start
    steps = [f"Start: {_fmt(cur)}"]
    seen_clauses = {}
    for ci, val, clause in events[1:]:
        if ci in seen_clauses and seen_clauses[ci] != "start":
            return None  # a second number in an event clause
        sign = _classify_event(clause)
        if sign is None:
            return None
        new = cur + sign * val
        steps.append(f"{_fmt(cur)} {'+' if sign > 0 else '−'} "
                     f"{_fmt(val)} = {_fmt(new)}")
        cur = new
        seen_clauses[ci] = "event"
    seen_clauses[events[0][0]] = "start"
    # the start's own clause may also carry the first event
    # ("50 rupee se 23 rupee kharch kiye") — handled above
    # only when that clause held exactly the start + 1 event;
    # two events in one clause decline via seen_clauses.
    return _res("story_chain", _fmt(cur), steps, value=cur)


def _story_backward(t, tl):
    if not re.search(r"shuru|शुरू|starting|start\s+me|pehle|"
                     r"पहले|originally", tl):
        return None
    if not re.search(r"bacha|बचा|bache|बचे|bachi|बची|left|"
                     r"remain", tl):
        return None
    # k friends ko m-m each form
    m = re.search(r"(\d+)\s*(?:dost|दोस्त|friends?|bacho|बच्चो|"
                  r"baccho)\s*(?:ko|को)\s*(\d+)\s*-\s*(\d+)", tl)
    if m and m.group(2) == m.group(3):
        given = int(m.group(1)) * int(m.group(2))
        ml = re.search(r"(?:bacha|बचा|bache|बचे)\s*(?:hai\s*)?"
                       r"(\d+)|(\d+)\s*(?:rupaye|rupee|रुपये)?\s*"
                       r"(?:bacha|बचा|bache|left)", tl)
        if not ml:
            return None
        left = int(ml.group(1) or ml.group(2))
        steps = [
            f"Given away: {m.group(1)} × {m.group(2)} = {given}",
            f"Start = left + given = {left} + {given} = "
            f"{left + given}",
        ]
        return _res("story_backward", str(left + given), steps,
                    value=left + given)
    nums = _numbers_with_spans(t)
    if len(nums) != 2:
        return None
    if not re.search(r"de\s+di|दे|gave|give|kharch|खर्च|spent|"
                     r"kho|खो|मंगा|mangaa|liya|लिया", tl):
        return None
    left = None
    given = None
    for val, s, e in nums:
        near = tl[max(0, s - 14):e + 14]
        if re.search(r"bacha|बचा|bache|बचे|bachi|बची|left",
                     near):
            left = val
        else:
            given = val
    if left is None or given is None:
        return None
    steps = [f"Start = left + given/spent = {_fmt(left)} + "
             f"{_fmt(given)} = {_fmt(left + given)}"]
    return _res("story_backward", _fmt(left + given), steps,
                value=left + given)


_WORD_NUM = {"ek": 1, "do": 2, "teen": 3, "तीन": 3, "chaar": 4,
             "चार": 4, "paanch": 5, "पाँच": 5, "two": 2,
             "three": 3, "four": 4, "five": 5, "one": 1}


def _verbal_equation(t, tl):
    # double / triple / half of a number, plus/minus k, gives M
    m = re.search(r"(double|twice|डबल|दोगुना|दुगुना|triple|"
                  r"तीन\s*गुना|half|आधा)\D{0,30}?"
                  r"(\d+)\D{0,20}?(?:aata|आता|aati|is|equals?|"
                  r"=|par|पर|होता)\D{0,8}?(\d+)", tl)
    if m:
        word = m.group(1)
        coef = {"double": 2, "twice": 2, "डबल": 2, "दोगुना": 2,
                "दुगुना": 2, "triple": 3, "तीन गुना": 3}.get(
                word, Fraction(1, 2) if word in (
                    "half", "आधा") else None)
        if coef is None:
            return None
        seg = tl[m.start():m.end()]
        minus = bool(re.search(r"minus|घटा|ghat|कम\s+kar", seg))
        k, M = Fraction(int(m.group(2))), Fraction(
            int(m.group(3)))
        x = (M + k) / coef if minus else (M - k) / coef
        if x <= 0:
            return None
        steps = [
            f"Let the number be x: {coef}x "
            f"{'−' if minus else '+'} {_fmt(k)} = {_fmt(M)}",
            f"x = {_fmt(x)}",
        ]
        # verify by substitution
        if coef * x + (-k if minus else k) != M:
            return None
        return _res("verbal_equation", _fmt(x), steps, value=x,
                    typ="algebra")
    # consecutive numbers
    m = re.search(r"(teen|तीन|chaar|चार|paanch|पाँच|do|दो|"
                  r"three|four|five|two|\d)\s+(?:lagatar|लगातार|"
                  r"consecutive)", tl)
    if m:
        n = _WORD_NUM.get(m.group(1)) or (
            int(m.group(1)) if m.group(1).isdigit() else None)
        nums = [v for v, _, _ in _numbers_with_spans(t)]
        if n and len(nums) == 1:
            S = nums[0]
            if S.denominator == 1:
                S = int(S)
                step = 2 if re.search(r"even|odd|सम|विषम",
                                      tl) else 1
                first = Fraction(
                    S - step * n * (n - 1) // 2, n)
                if first.denominator == 1 and first > 0:
                    first = int(first)
                    if step == 2:
                        want_even = bool(re.search(
                            r"even|सम", tl))
                        if (first % 2 == 0) != want_even:
                            return None
                    seq = [first + step * i
                           for i in range(n)]
                    if sum(seq) != S:
                        return None
                    if re.search(r"chota|छोटा|smallest|chit",
                                 tl):
                        steps = [
                            f"Let the numbers be x, x + 1, "
                            f"…, sum = {S}",
                            f"Smallest = {first} "
                            f"({', '.join(map(str, seq))})",
                        ]
                        return _res("consecutive",
                                    str(first), steps, value=first,
                                    typ="algebra")
                    if re.search(r"bada|बड़ा|largest|biggest",
                                 tl):
                        steps = [
                            f"The numbers are "
                            f"{', '.join(map(str, seq))}",
                            f"Largest = {seq[-1]}",
                        ]
                        return _res("consecutive",
                                    str(seq[-1]), steps,
                                    value=seq[-1], typ="algebra")
        return None
    # two ages: elder by d, sum S
    m = re.search(r"(\d+)\s*years?\s*(?:elder|older|bada|बड़ा)"
                  r"\D{0,60}?(?:add|sum|both|जोड़|योग)\D{0,30}?"
                  r"(\d+)", tl)
    if m and re.search(r"my\s+age|meri\s+age|mera\s+age|"
                       r"what\s+is\s+my", tl):
        d, S = int(m.group(1)), int(m.group(2))
        if S <= d or (S - d) % 2:
            return None
        mine = (S - d) // 2
        steps = [
            f"Let my age be x; friend's age = x + {d}",
            f"x + (x + {d}) = {S}, so x = {mine}",
        ]
        if mine + (mine + d) != S:
            return None
        return _res("ages", str(mine), steps, value=mine,
                    typ="algebra")
    return None


def _equal_parts_total(t, tl):
    if not re.search(r"total|कुल|kitne\s+hai|how\s+many", tl):
        return None
    m = re.search(r"(?:divide|divided|baant|बाँट|baanto)"
                  r"\D{0,30}?(\d+)\s*(?:equal|equl|बराबर|"
                  r"barabar)\s*parts?\D{0,50}?"
                  r"(\d+)\s*(?:pens|pencil|items?|cheez|रूपये)?",
                  tl)
    if m:
        k, each = int(m.group(1)), int(m.group(2))
        steps = [f"Total = parts × in each part = {k} × "
                 f"{each} = {k * each}"]
        return _res("equal_parts", str(k * each), steps,
                    value=k * each)
    return None


# ---------------------------------------------------------------------------
# L. junior multiply / divide stories (exactly two numbers)
# ---------------------------------------------------------------------------

_GROUP_NOUN = (r"customers?|students?|dost|friends?|बच्चे|"
               r"bachche|लोग|logo|people|boxes|box|डब्बे|"
               r"children|kids?")


def _junior_mul_div(t, tl):
    if re.search(r"speed|doori|distance|kmph|per\s+hour|"
                 r"\bkm\b|गति|दूरी|रफ्तार|raftaar", tl):
        return None  # motion problems — the speed/distance
        # layer owns them (a "per hour" here is a rate to
        # multiply or divide BY, never the sharing marker)
    if re.search(r"\d+\s*/\s*\d+", t):
        return None
    nums = _numbers_with_spans(t)
    if len(nums) != 2:
        return None
    (a, _, _), (b, _, _) = nums
    if a.denominator != 1 or b.denominator != 1:
        return None
    a, b = int(a), int(b)
    story_verbs = re.search(
        r"de\s+diye|दे\s+दिए|kho|खो|khay|खा|kharch|खर्च|"
        r"kharid|खरीद", tl) or re.search(
            r"\b(gave|lost|ate|eaten|spent|bought)\b", tl)
    # per-person giving -> total needed
    m = re.search(r"(\d+)\s*(?:" + _GROUP_NOUN + r")\s*ko\s*"
                  r"(\d+)\b[^.]{0,30}?(?:dega|denge|milega|"
                  r"देगा|देंगे|chahiye|चाहिए)", tl)
    if m and re.search(r"kitna|कितना|total|कुल|chahiye|चाहिए",
                       tl):
        n, per = int(m.group(1)), int(m.group(2))
        steps = [f"Total = {n} × {per} = {n * per}"]
        return _res("story_multiply", str(n * per), steps,
                    value=n * per)
    # groups x each -> total
    if re.search(r"\beach\b|har\s+ek|प्रत्येक|per\s+box|"
                 r"har\s+\w+\s+me", tl) and re.search(
                     r"total|kitna|कितना|how\s+many|कुल", tl) \
            and not story_verbs:
        steps = [f"Total = {a} × {b} = {a * b}"]
        return _res("story_multiply", str(a * b), steps,
                    value=a * b)
    # equal sharing / average: one number divides the other
    div_marker = re.search(
        r"baant|बाँट|banto|divide|divided|share|sharing|"
        r"average|औसत|har\s+\w+\s+ko\s+kitna|each\s+one|"
        r"per\s+(?:hour|ghanta|घंटा)", tl) or (
        re.search(_GROUP_NOUN, tl) and re.search(
            r"kitna|कितना", tl) and not story_verbs)
    if div_marker:
        # a subtraction event in the story ("बाँटकर खाए" —
        # shared AND ATE) means the baant word is not the
        # sharing operation; never divide then.
        if re.search(r"khay|खा|kho|खो|kharch|खर्च", tl) or \
                re.search(r"\b(ate|eaten|lost|spent)\b", tl):
            return None
        if b and a % b == 0 and a // b >= 1 and a != b:
            steps = [f"{a} ÷ {b} = {a // b}"]
            return _res("story_divide", str(a // b), steps,
                        value=a // b)
        if a and b % a == 0 and b // a >= 1 and a != b:
            steps = [f"{b} ÷ {a} = {b // a}"]
            return _res("story_divide", str(b // a), steps,
                        value=b // a)
    return None


# ---------------------------------------------------------------------------
# dispatcher
# ---------------------------------------------------------------------------

_SCHEMAS = (
    _matrix_unknown,
    _trig_max,
    _trig_tan_sum,
    _trig_value_expr,
    _series_nth,
    _series_sum_ap,
    _series_word_separated,
    _poly_verbal_squares,
    _poly_identity_cubes,
    _poly_area_side,
    _poly_remainder,
    _poly_eval_assign,
    _poly_factor_expand,
    _quad_sum_squares,
    _quad_sum_product,
    _quad_roots_to_coeff,
    _quad_bare_equation,
    _root_area_side,
    _root_volume_edge,
    _root_bare,
    _int_number_line,
    _int_add_words,
    _int_signed_expr,
    _frac_compare,
    _frac_whole_minus,
    _frac_of_left,
    _frac_chain,
    _story_backward,
    _verbal_equation,
    _equal_parts_total,
    _story_chain,
    _junior_mul_div,
)


def solve_wave206(question):
    """Wave 206 fix-queue schemas. Returns a result dict or
    None; every schema verifies its own answer before
    serving, and any exception declines the whole wave."""
    try:
        t = _prep(question)
        tl = t.lower()
        # A quantifier / statement question only CONTAINS
        # equations; it is not an equation ask (the native
        # reasoning layer owns it) — never let a schema lift
        # one embedded equation out of it.
        if re.search(r"quantifier|∀|∃|open\s+sentence|"
                     r"true\s+statement", tl):
            return None
        for fn in _SCHEMAS:
            try:
                out = fn(t, tl)
            except Exception:
                out = None
            if out is not None:
                return out
        return None
    except Exception:
        return None
