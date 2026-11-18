"""Wave 76: MCQ mode — solve the stem, match the option.

The Wave 71 solver-health audit found the board-papers surface
the weakest in the app (35/150 sample questions solved), and 75
of its 115 failures were MCQs: the question ARRIVES with its
options — "(a) 12 (b) 18 (c) 24 (d) 36" — and the app had no
way to use them. The full text (stem + options) usually defeats
the solver, and the honest layers could only salvage a fragment
or serve a concept card for what is really a concrete problem.

`mcq_result(question)` is one more honest layer in
fallback.with_fallback, sitting after the Verified Data Bank
and before salvage:

  1. extract the stem and the option list (2–6 options) from
     the question text — parenthesised markers "(a) … (d)",
     bare markers "A. … D." / "1) … 4)", newline-separated
     marker lists, and an explicit "options are …" tail split
     by commas;
  2. solve the STEM through the existing machinery
     (solver.router.solve_question, with the same
     "find the value" retry _solve_friendly uses) — no parallel
     solver is written here;
  3. match the computed answer against the options (exact
     string, numeric/Fraction equality with a rounding rule,
     SymPy equivalence via the app's own expression parser,
     coordinate tuples, unit-stripped retry). If EXACTLY ONE
     option matches, the stem's own result is returned with
     its answer line naming that option — "(b) 42" — in the
     question's own option text, so the language rule holds
     automatically.

HONESTY RULE (same as every layer since Wave 18): when the
stem cannot be solved, or no option — or more than one option
— matches, this layer returns None and the existing behaviour
runs byte-for-byte unchanged. An option is NEVER guessed.

Out of scope for this wave (follow-ups): OR-type internal
choice questions and Assertion–Reason items. Both are detected
and left to the existing layers untouched.
"""

import re
import time
from fractions import Fraction

from i18n import solve_failed
from solver.router import solve_question

# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

_LETTERS = "abcdef"

# Marker families, tried in order. Each pattern captures the
# label in group 1; the match END is where the option text
# starts and the match START (adjusted for a leading separator
# in the bare families) is where the previous chunk ends.
_PAREN_LETTER = re.compile(r"\(\s*([a-fA-F])\s*\)")
_PAREN_DIGIT = re.compile(r"\(\s*([1-6])\s*\)")
_BARE_LETTER = re.compile(r"(?:^|(?<=[\s,;]))([a-fA-F])\s*[.)]\s+")
_BARE_DIGIT = re.compile(r"(?:^|(?<=[\s,;]))([1-6])\s*[.)]\s+")

_OPTIONS_CUE = re.compile(
    r"(?i)\b(?:options?|choices?|विकल्प)\s*(?:are|is|:|—|–|-)?\s*")

_ASSERTION_RE = re.compile(
    r"(?i)assertion|अभिकथन|कथन\s*\(?\s*[aA]\s*\)?\s*और\s*कारण")


def _best_run(hits, kind):
    """The option run inside the marker hits: a consecutive
    a,b,c… (or 1,2,3…) sequence of length 2–6, preferring the
    longest, then the last. Stems carry their own
    parenthesised letters — P(E), P(F), P(A/B) — so the whole
    hit list rarely validates; the options are the consecutive
    run that starts at a/1."""
    def key(label):
        if kind == "letter":
            return _LETTERS.find(label.lower())
        return int(label) - 1

    best = None
    for i, hit in enumerate(hits):
        if key(hit[0]) != 0:
            continue
        run = [hit]
        j = i + 1
        while j < len(hits) and len(run) < 6 \
                and key(hits[j][0]) == len(run):
            run.append(hits[j])
            j += 1
        if len(run) >= 2 and (best is None
                              or len(run) >= len(best)):
            best = run
    return best


def _validate_hits(question, hits, kind):
    """hits: [(label, marker_start, text_start)] in order of
    appearance. Return (stem, [(label, text), ...]) or None."""
    run = _best_run(hits, kind)
    if run is None:
        return None
    stem = question[:run[0][1]].strip()
    if len(stem) < 3:
        return None
    options = []
    for i, (label, _start, text_start) in enumerate(run):
        end = run[i + 1][1] if i + 1 < len(run) else len(question)
        text = question[text_start:end].strip()
        text = text.strip(" ,;·").strip()
        if text.endswith("।"):
            text = text[:-1].strip()
        if not text or len(text) > 90:
            return None
        options.append((label, text))
    # A "?" buried inside a non-final option means these are
    # almost certainly sub-questions, not answer options.
    for _label, text in options[:-1]:
        if "?" in text or "？" in text:
            return None
    # Wave 100: imperative "options" are sub-questions, not
    # answers — a case-study set pasted whole ("(a) Find the
    # length of AB. (b) Find the length of OB. (c) Find the
    # length of AP.") used to validate as an MCQ whose "stem"
    # was the whole passage, and _solve_stem then burned its
    # ~13 candidate solves on it (19 s in the Wave 93 audit,
    # regression #3) before returning None anyway. Genuine
    # options are values, expressions or statements — never
    # commands to compute something.
    imperatives = sum(
        1 for _label, text in options
        if re.match(r"(?i)\s*(?:find|solve|calculate|evaluate|"
                    r"prove|state|determine|write|show|"
                    r"construct|draw)\b", text))
    if imperatives >= 2:
        return None
    return stem, options


def _extract_marked(question):
    for pattern, kind in ((_PAREN_LETTER, "letter"),
                          (_PAREN_DIGIT, "digit"),
                          (_BARE_LETTER, "letter"),
                          (_BARE_DIGIT, "digit")):
        hits = [(m.group(1), m.start(), m.end())
                for m in pattern.finditer(question)]
        got = _validate_hits(question, hits, kind)
        if got is not None:
            return got
    return None


def _extract_cued(question):
    """An explicit "options are 12, 18, 24, 36" tail: split the
    tail by commas or newlines and label the parts a, b, c…"""
    m = _OPTIONS_CUE.search(question)
    if not m:
        return None
    stem = question[:m.start()].strip()
    tail = question[m.end():].strip()
    if len(stem) < 3 or not tail:
        return None
    parts = [p.strip(" .।,;") for p in re.split(r"[,\n]", tail)]
    parts = [p for p in parts if p]
    # A trailing "or 36" / "and 36" belongs to the last item.
    if len(parts) >= 2:
        parts[-1] = re.sub(r"(?i)^(or|and|या|और)\s+", "", parts[-1])
    if not (2 <= len(parts) <= 6):
        return None
    if any(len(p) > 90 or "?" in p for p in parts):
        return None
    options = [(letter, p) for letter, p in zip(_LETTERS, parts)]
    return stem, options


def extract_mcq(question):
    """(stem, [(label, option_text), ...]) or None when the
    question does not carry a usable option list."""
    q = str(question or "").strip()
    if not q:
        return None
    # Out of scope this wave: Assertion–Reason items.
    if _ASSERTION_RE.search(q):
        return None
    got = _extract_marked(q) or _extract_cued(q)
    if got is None:
        return None
    stem, options = got
    # Out of scope this wave: OR-type internal choice ("… OR …"
    # offers a second QUESTION, not answer options).
    if re.search(r"\bOR\b", stem):
        return None
    # Assertion–Reason options ("Both A and R are true…") can
    # arrive without the word "assertion" in the stem.
    joined = " ".join(text for _l, text in options).lower()
    if "both a and r" in joined or "a और r" in joined:
        return None
    return stem, options


# ---------------------------------------------------------------------------
# Solving the stem — the existing machinery, nothing parallel
# ---------------------------------------------------------------------------

_SOFT_PREFIXES = (
    "tell me", "i need", "no word-problem pattern matched",
    "give a number", "give me", "please tell", "please give",
    "could not", "enter a", "try a form",
)


def _looks_junk(answer):
    """Letter-soup check (mirrors fallback._is_junk's core
    rules): sympy multiplying the question's own words into a
    product of single letters is not an answer. Two shapes get
    no benefit of the doubt at all: an unevaluated integral
    sign left standing in the "answer", and the vector-unicode
    glyphs (combining diacritics like the hat in k̂, the
    precomposed î/ĵ, the combining vector arrow) — the Wave 71
    audit's known-broken surface, where the solver shreds the
    notation into letter products that can spuriously
    "match" an option written in the same notation."""
    ans = str(answer or "")
    if "∫" in ans or "⃗" in ans:
        return True
    if any(0x300 <= ord(ch) <= 0x36F for ch in ans):
        return True
    if "î" in ans or "ĵ" in ans:
        return True
    if "*" not in ans and "·" not in ans:
        return False
    if any(mark in ans for mark in ("**", "·", "^")):
        letters = set(re.findall(r"(?<![A-Za-z])[a-z](?![A-Za-z])",
                                 ans))
        if len(ans) >= 8 and len(letters) >= 4:
            return True
    factors = set()
    for fac in re.split(r"[*·]", ans):
        f = fac.strip().strip("()")
        f = re.sub(r"(?:\*\*|\^)\s*\d+(?:\.\d+)?$", "", f).strip()
        if len(f) == 1 and f.isalpha():
            factors.add(f)
    return len(factors) >= 4


def _stem_is_real(stem, result):
    """The same realness bar fallback.with_fallback applies:
    not a solver failure, not a soft prompt, not letter soup,
    and a non-empty answer."""
    if not isinstance(result, dict):
        return False
    try:
        if solve_failed(stem, result):
            return False
    except Exception:
        return False
    ans = str(result.get("answer", "") or "").strip()
    if not ans:
        return False
    if ans.lower().startswith(_SOFT_PREFIXES):
        return False
    if _looks_junk(ans):
        return False
    # Wave 150: the book-style wrong-serve vetoes also gate
    # part-level solves (multipart parts and MCQ stems are
    # solved through this bar): a part whose form provably
    # disagrees with its ask is not real either.
    try:
        from fallback import _w150_veto
        if _w150_veto(stem, result):
            return False
    except Exception:
        pass
    return True


def _clean_stem(stem):
    """Light surface cleanup of a stem before it is fed to the
    solver — the same service salvage's filler-stripper does
    for embedded expressions. Board stems carry sentence
    furniture the expression paths reject: a trailing "=",
    "The value of …", a leading "If …", and a ", then x = ?"
    tail that asks for the very value being solved."""
    s = str(stem).strip()
    m = re.search(r"[,;]?\s*then\s+(.{0,30})$", s, flags=re.I)
    if m and ("=" in m.group(1) or "find" in m.group(1).lower()
              or s.rstrip().endswith("?")):
        s = s[:m.start()].strip()
    s = s.rstrip("?").strip()
    if s.endswith("="):
        s = s[:-1].strip()
    s = re.sub(r"(?i)^if\s+", "", s)
    s = re.sub(r"(?i)^the\s+value\s+of\s+", "", s)
    s = re.sub(r"(?i)^value\s+of\s+", "", s)
    return s.strip()


def _solve_stem(stem):
    """solve_question on the stem until one form really
    solves. The forms, in order: the stem as written (with
    _solve_friendly's own "find the value" retry), the lightly
    cleaned stem, a superscript-spaced form ("cos²27" reaches
    the router's parser as "cos^227" otherwise), a degree-free
    variant of it, and finally the maths cores salvage's own
    candidate extractor finds inside the stem ("The value of
    5 + 3 is" -> "5 + 3") — the app's existing machinery
    throughout, never a parallel solver. Returns a real
    result dict or None."""
    cleaned = _clean_stem(stem)
    spaced = cleaned.replace("²", "^2 ").replace("³", "^3 ")
    # Some router paths never fold the Unicode operators
    # (the trig path rejects "−" U+2212 outright), so an
    # ASCII-operator form is tried too.
    ascii_ops = spaced.replace("−", "-").replace("–", "-") \
        .replace("×", "*").replace("÷", "/")
    deg_free = ascii_ops.replace("°", "")
    candidates = []

    def add(cand):
        cand = (cand or "").strip()
        if cand and cand not in candidates:
            candidates.append(cand)

    for base in (stem, cleaned, spaced, ascii_ops, deg_free):
        add(base)
        add(f"{base} find the value")
    try:
        from fallback import _candidates as _salvage_candidates
        for cand in _salvage_candidates(stem):
            add(cand)
    except Exception:
        pass
    # Wave 80: wall-clock discipline. Each candidate pays the
    # router's own solve budget, so an unsolvable stem used to
    # multiply ~11 candidates into a >20 s hang (the audit's
    # ERROR_TIMEOUT family). The first candidate always runs;
    # once ~5 s have elapsed no NEW candidate is started, so
    # the worst case is one budget plus what already ran.
    _t0 = time.monotonic()
    for candidate in candidates:
        if candidate is not candidates[0] and \
                time.monotonic() - _t0 > 5.0:
            break
        try:
            result = solve_question(candidate)
        except Exception:
            continue
        if _stem_is_real(stem, result):
            return result
    return None


# ---------------------------------------------------------------------------
# Matching the computed answer against the options
# ---------------------------------------------------------------------------

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_UNITS = {
    "cm", "mm", "km", "m", "cm2", "m2", "km2", "cm3", "m3",
    "litre", "litres", "liter", "liters", "ml", "l",
    "kg", "g", "mg", "km/h", "kmph", "mph",
    "sec", "secs", "second", "seconds", "min", "mins",
    "minute", "minutes", "hour", "hours", "hr", "hrs",
    "unit", "units", "day", "days",
    "सेमी", "मीटर", "किमी", "लीटर", "ग्राम", "किग्रा",
    "सेकंड", "मिनट", "घंटा", "घंटे", "इकाई",
}


def _clean(text, strip_units=False):
    """Normalise a value string for comparison: scripts,
    operators, superscripts, currency, percent — and, on the
    second pass only, trailing/standalone unit words."""
    s = str(text or "").translate(_DEV_DIGITS)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("×", "*").replace("✕", "*").replace("·", "*")
    s = s.replace("÷", "/")
    s = s.replace("²", "^2").replace("³", "^3").replace("⁴", "^4")
    s = s.replace("½", "(1/2)").replace("¼", "(1/4)").replace("¾", "(3/4)")
    s = s.replace("₹", " ")
    s = re.sub(r"(?i)\b(?:rs\.?|rupees?)\b", " ", s)
    s = s.replace("%", " ")
    s = s.strip().strip(".,;।").strip()
    if strip_units:
        # digit-attached units first: "128litres", "10cm"
        s = re.sub(r"(?<=\d)\s*(?:cm|mm|km|kg|ml|m|g|l)\b", "", s,
                   flags=re.I)
        tokens = [t for t in re.split(r"\s+", s)
                  if t.strip(".,;()").lower() not in _UNITS]
        s = " ".join(tokens)
    return s.strip()


def _as_number(s):
    """Parse a cleaned string as ONE exact number (integer,
    decimal, fraction or mixed number) -> Fraction, or None."""
    t = s.replace(",", "").strip()
    m = re.fullmatch(r"(-?\d+)\s*/\s*(\d+)", t)
    if m:
        den = int(m.group(2))
        return Fraction(int(m.group(1)), den) if den else None
    m = re.fullmatch(r"(-?)(\d+)\s+(\d+)\s*/\s*(\d+)", t)
    if m:  # mixed number "1 1/2"
        den = int(m.group(4))
        if not den:
            return None
        val = Fraction(int(m.group(2))) + Fraction(int(m.group(3)), den)
        return -val if m.group(1) else val
    if re.fullmatch(r"-?\d+(?:\.\d+)?", t):
        try:
            return Fraction(t)
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _decimal_places(s):
    m = re.search(r"\.(\d+)", s)
    return len(m.group(1)) if m else 0


def _numbers_match(a_text, b_text):
    """Exact numeric equality, with the board-paper rounding
    rule: a decimal written with d places also matches a value
    that rounds to it at d places (5/6 vs 0.83)."""
    a = _as_number(a_text)
    b = _as_number(b_text)
    if a is None or b is None:
        return False
    if a == b:
        return True
    for dec_text, other in ((a_text, b), (b_text, a)):
        d = _decimal_places(dec_text)
        if d:
            try:
                if round(float(other), d) == float(_as_number(dec_text)):
                    return True
            except (ValueError, OverflowError):
                pass
    return False


def _match_canon(text):
    """Wave 146: canonical surface for the symbolic matcher,
    applied to BOTH sides identically. School texts write
    "logx" for log(x) — the expression parser otherwise
    reads it as l*o*g*x and a correct integrating-factor
    answer (exp(x log x - x)) can never match its option
    (the Wave 80 timeout-item pin). Also folds the middle
    dot some solver answers carry, and rewrites a
    parenthesised e^(...) power as exp(...) — the parser's
    bare "e" is a plain symbol, not Euler's number."""
    t = str(text or "").replace("·", "*")
    t = re.sub(r"\b(log|ln)\s*([a-zA-Z])\b", r"\1(\2)", t)
    _epow = re.compile(r"(?<![A-Za-z0-9_])e\s*(?:\*\*|\^)\s*\(")
    out, i = [], 0
    m = _epow.search(t, i)
    while m:
        out.append(t[i:m.start()])
        j = m.end()  # just past the "("
        depth, k = 1, j
        while k < len(t) and depth:
            if t[k] == "(":
                depth += 1
            elif t[k] == ")":
                depth -= 1
            k += 1
        if depth:  # unbalanced — leave the rest untouched
            out.append(t[m.start():])
            i = len(t)
            break
        out.append("exp(" + t[j:k - 1] + ")")
        i = k
        m = _epow.search(t, i)
    out.append(t[i:])
    return "".join(out)


def _sympy_match(a_text, b_text):
    """Symbolic equivalence through the app's own expression
    parser: (π + 2)10 vs 10π + 20, n² vs n*n, √2 vs sqrt(2)."""
    try:
        from solver.expression_parser import parse_expression
        ea = parse_expression(_match_canon(a_text))
        eb = parse_expression(_match_canon(b_text))
    except Exception:
        return False
    try:
        if ea == eb:
            return True
        from sympy import simplify
        if simplify(ea - eb) == 0:
            return True
        if ea.is_number and eb.is_number:
            fa, fb = float(ea), float(eb)
            scale = max(1.0, abs(fa), abs(fb))
            if abs(fa - fb) <= 1e-9 * scale:
                return True
            for dec_text, other in ((a_text, fb), (b_text, fa)):
                d = _decimal_places(dec_text)
                if d and round(other, d) == float(
                        _as_number(dec_text) or other):
                    return True
    except Exception:
        return False
    return False


def _split_top(text):
    """Split on top-level commas (parentheses protect the
    commas inside a coordinate pair)."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts]


def _one_value_match(computed, option):
    """One computed value vs one option text (both already
    cleaned with the same pass settings)."""
    if not computed or not option:
        return False
    if computed.replace(" ", "") == option.replace(" ", ""):
        return True
    # Coordinate / tuple form: "(6, 1)" vs "(6,1)".
    if computed.startswith("(") and option.startswith("(") \
            and computed.endswith(")") and option.endswith(")"):
        ca = _split_top(computed[1:-1])
        cb = _split_top(option[1:-1])
        if len(ca) == len(cb) and len(ca) >= 2:
            return all(_one_value_match(x, y) for x, y in zip(ca, cb))
    if _numbers_match(computed, option):
        return True
    return _sympy_match(computed, option)


def _computed_variants(answer_text):
    """The comparable forms of the solver's answer string: the
    whole text, the RHS of a short "x = …" equation, and each
    "… or …" alternative."""
    ans = str(answer_text or "").strip()
    if "≈" in ans:
        ans = ans.split("≈")[0].strip()
    variants = []
    for piece in re.split(r"\s+or\s+", ans):
        piece = piece.strip().rstrip(".")
        m = re.match(r"^([A-Za-z][A-Za-z0-9 ]{0,14})\s*=\s*(.+)$",
                     piece)
        if m and not re.search(r"[+\-*/^()]", m.group(1)):
            piece = m.group(2).strip()
        if piece and piece not in variants:
            variants.append(piece)
    return variants


def _matching_labels(answer_text, options):
    """Labels of the options that match the computed answer.
    Matching runs per cleaning pass so a unit-stripped match
    can never silently override a light-pass match: pass 1
    decides whenever it matches anything at all."""
    computed = _computed_variants(answer_text)
    for strip_units in (False, True):
        matched = []
        for label, text in options:
            opt = _clean(text, strip_units=strip_units)
            if any(_one_value_match(
                    _clean(v, strip_units=strip_units), opt)
                    for v in computed):
                matched.append(label)
        if matched:
            return matched
    return []


# ---------------------------------------------------------------------------
# Wave 100: special stem schemas.
#
# The Wave 93 audit's regressions were stems the generic
# machinery cannot read at all — it either fails them after
# burning its ~13 candidate solves, or (worse) a concept card
# captures them. These schemas are the finite, NCERT/ICSE-
# recurring shapes behind those regressions. Each is a pure
# pattern + exact computation: it returns a result only when
# its full pattern matches AND the computed value (or the
# classified claim) settles EXACTLY ONE option; anything less
# returns None and the generic machinery runs as before. An
# option is still never guessed.
#
# Two families:
#   * value schemas (_special_value_result): compute the
#     stem's value; the caller matches it against the options
#     with the ordinary _matching_labels.
#   * claim schemas (_special_claim_result): the options are
#     STATEMENTS (one-one/onto, nature of roots, par value);
#     the schema classifies the stem, classifies each option's
#     claim, and shapes the one option whose claim agrees.
# ---------------------------------------------------------------------------

import sympy as _sp
from fractions import Fraction as _Fraction

from solver.expression_parser import parse_expression as _parse_expr


def _clean_expr_text(s):
    """Surface cleanup for the expression parser: Unicode
    operators and superscripts, and √n -> sqrt(n)."""
    t = str(s or "")
    t = t.replace("−", "-").replace("–", "-").replace("×", "*")
    t = t.replace("²", "^2").replace("³", "^3").replace("⁴", "^4")
    t = re.sub(r"√\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", t)
    t = re.sub(r"√\s*\(", "sqrt(", t)
    return t.strip()


def _quad_str(a, b, c):
    """'x^2 - 3x + 1' from integer coefficients a, b, c."""
    def term(coef, var):
        if coef == 0:
            return None
        mag = var if abs(coef) == 1 and var else \
            f"{abs(coef)}{var}"
        return ("-" if coef < 0 else "+", mag)
    parts = []
    for coef, var in ((a, "x^2"), (b, "x"), (c, "")):
        t = term(coef, var)
        if t is None:
            continue
        sign, mag = t
        if not parts:
            parts.append(("-" if sign == "-" else "") + mag)
        else:
            parts.append(f" {sign} {mag}")
    return "".join(parts) if parts else "0"


# --- value schema: "x + 1/x = 3 … expressed as a quadratic ----
# --- equation in the form ax^2 + bx + c = 0; value of a-b+c" --

_FORM_RE = re.compile(
    r"in\s+the\s+form\s+ax\s*\^?\s*2\s*\+\s*bx\s*\+\s*c\s*=\s*0",
    re.I)


def _coeff_form_value(stem):
    """Wave 93 regression #1. The equation is cleared of its
    fraction and collected into ax^2 + bx + c = 0 (primitive
    integer coefficients, a > 0 — the school convention for
    "the form"), then the asked combination of a, b, c is
    evaluated exactly."""
    m = re.search(
        r"(.+?)\s+is\s+expressed\s+as\s+a\s+quadratic\s+"
        r"equation\s+in\s+the\s+form", stem, re.I)
    if not m or not _FORM_RE.search(stem):
        return None
    mq = re.search(r"value\s+of\s+(.+?)\s+is\s*:?\s*$", stem,
                   re.I)
    if not mq:
        return None
    combo = mq.group(1).strip()
    eq = re.sub(r"^.*?equation\s+", "", m.group(1),
                flags=re.I)
    eq = re.sub(r"\(\s*x\s*(?:≠|!=)\s*0\s*\)", " ", eq)
    eq = eq.strip().rstrip(".")
    if "=" not in eq:
        return None
    lhs, rhs = eq.split("=", 1)
    try:
        expr = _parse_expr(_clean_expr_text(lhs)) \
            - _parse_expr(_clean_expr_text(rhs))
        num, _den = _sp.together(expr).as_numer_denom()
        poly = _sp.Poly(num, _sp.Symbol("x"))
        if poly is None or poly.degree() != 2:
            return None
        coeffs = []
        for v in poly.all_coeffs():
            coeffs.append(_Fraction(int(v.p), int(v.q))
                          if hasattr(v, "p") else _Fraction(v))
    except Exception:
        return None
    from math import gcd as _gcd
    den = 1
    for f in coeffs:
        den = den * f.denominator // _gcd(den, f.denominator)
    ints = [int(f * den) for f in coeffs]
    g = _gcd(_gcd(abs(ints[0]), abs(ints[1])), abs(ints[2])) or 1
    a, b, c = (v // g for v in ints)
    if a < 0:
        a, b, c = -a, -b, -c
    try:
        cexpr = _parse_expr(_clean_expr_text(combo))
        sa, sb, sc = _sp.symbols("a b c")
        value = cexpr.subs({sa: a, sb: b, sc: c})
        if not value.is_number:
            return None
        value = _sp.nsimplify(value)
    except Exception:
        return None
    steps = [
        "Clear the fraction and collect the equation into "
        "the form ax^2 + bx + c = 0:",
        f"{_quad_str(a, b, c)} = 0, so a = {a}, b = {b}, "
        f"c = {c}.",
        f"{combo} = {value}",
    ]
    return {"type": "algebra", "op": "quadratic_coefficients",
            "answer": str(value), "steps": steps}


# --- value schema: order / degree of a differential equation --

def _ode_fact_value(stem):
    """The MCQ form of the calculus order/degree fact (Wave
    93 regression #2): the same inspection helper
    solver.calculus uses, applied to the stem so the MCQ
    layer can settle it even when the whole-text solve never
    reaches calculus."""
    if not re.search(r"घात|कोटि|\bdegree\b|\border\b", stem):
        return None
    if not re.search(r"dy/dx|d\s*\^?\s*\d*\s*y\s*/\s*dx|अवकल|"
                     r"differential", stem):
        return None
    try:
        from solver.calculus import ode_order_degree
        got = ode_order_degree(stem)
    except Exception:
        return None
    if got is None:
        return None
    order, degree = got
    want_degree = bool(re.search(r"घात|\bdegree\b", stem))
    want_order = bool(re.search(r"कोटि|\border\b", stem))
    if want_degree and want_order:
        return None
    if want_degree:
        if degree is None:
            return None
        return {"type": "calculus", "op": "ode_degree",
                "answer": str(degree),
                "steps": [
                    "The degree is the power of the highest-"
                    "order derivative in the equation.",
                    f"That power is {degree}, so the degree "
                    f"is {degree}."]}
    return {"type": "calculus", "op": "ode_order",
            "answer": str(order),
            "steps": [
                "The order is the highest derivative present "
                "in the equation.",
                f"That is a derivative of order {order}, so "
                f"the order is {order}."]}


# --- value schema: recurring-deposit maturity (ICSE) ----------

def _rd_maturity_value(stem):
    if not re.search(r"recurring\s+deposit", stem, re.I):
        return None
    if "matur" not in stem.lower():
        return None
    md = re.search(r"deposits?\s*₹?\s*(\d+(?:\.\d+)?)\s*per\s+"
                   r"month\s+for\s*(\d+)\s*months", stem, re.I)
    mi = re.search(r"earns?\s*₹?\s*(\d+(?:\.\d+)?)\s*as\s+"
                   r"interest", stem, re.I) or re.search(
        r"interest\s+of\s*₹?\s*(\d+(?:\.\d+)?)", stem, re.I)
    if not md or not mi:
        return None
    monthly, months = float(md.group(1)), int(md.group(2))
    interest = float(mi.group(1))
    total = monthly * months
    value = total + interest
    steps = [
        f"Total deposited = {monthly:g} × {months} = "
        f"{total:g}",
        "Maturity amount = total deposited + interest "
        f"= {total:g} + {interest:g} = {value:g}",
    ]
    return {"type": "applied", "op": "rd_maturity",
            "answer": f"{value:g}", "steps": steps}


# --- value schema: GST-inclusive price (CGST means +SGST) -----

def _gst_value(stem):
    low = stem.lower()
    if "gst" not in low or "includ" not in low:
        return None
    mp = re.search(r"(?:marked|list)\s+price[^₹\d]{0,40}₹?\s*"
                   r"(\d+(?:\.\d+)?)", stem, re.I)
    if not mp:
        return None
    price = _Fraction(mp.group(1))
    mc = re.search(r"cgst[^%\d]{0,40}(\d+(?:\.\d+)?)\s*%",
                   stem, re.I)
    if mc:
        rate = 2 * _Fraction(mc.group(1))
        note = (f"CGST is {_Fraction(mc.group(1))}% and SGST "
                f"is the same again, so GST = {rate}% in all.")
    else:
        mg = re.search(r"\bgst\b[^%\d]{0,25}"
                       r"(\d+(?:\.\d+)?)\s*%", stem, re.I)
        if not mg:
            return None
        rate = _Fraction(mg.group(1))
        note = f"GST is charged at {rate}%."
    value = price * (100 + rate) / 100
    val_str = str(int(value)) if value.denominator == 1 \
        else f"{float(value):.2f}"
    steps = [
        note,
        f"Price including GST = {price} × (1 + {rate}/100) "
        f"= {val_str}",
    ]
    return {"type": "applied", "op": "gst_price",
            "answer": val_str, "steps": steps}


# --- value schema: a matrix power (A = [[..]], find A^2) -------

def _matrix_power_value(stem):
    mm = re.search(r"\b([A-Z])\s*=\s*(\[\[.*?\]\])", stem)
    if not mm:
        return None
    name, literal = mm.group(1), mm.group(2)
    rows = []
    for row_text in literal[2:-2].split("], ["):
        vals = re.findall(r"-?\d+(?:\.\d+)?", row_text)
        if not vals:
            return None
        rows.append([_Fraction(v) for v in vals])
    n = len(rows)
    if n not in (2, 3) or any(len(r) != n for r in rows):
        return None
    mp = re.search(rf"\b{name}\s*(?:\^|\*\*)\s*(\d)\b", stem) \
        or re.search(rf"\b{name}(²|³)", stem)
    if not mp:
        return None
    power = {"²": 2, "³": 3}.get(mp.group(1))
    if power is None:
        power = int(mp.group(1))
    if power not in (2, 3):
        return None
    try:
        mat = _sp.Matrix([[int(v) if v.denominator == 1
                           else float(v) for v in row]
                          for row in rows]) ** power
    except Exception:
        return None
    text = "[[" + "], [".join(
        ", ".join(str(v) for v in row)
        for row in mat.tolist()) + "]]"
    steps = [
        f"{name}^{power} = {name} × {name}"
        + (" × " + name if power == 3 else "")
        + " (row × column multiplication).",
        f"{name}^{power} = {text}",
    ]
    return {"type": "algebra", "op": "matrix_power",
            "answer": text, "steps": steps}


# --- value schema: spheres — volume/surface ratio <-> radii ---

def _ratio_pair(text):
    m = re.search(r"(\d+)\s*:\s*(\d+)", text)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _perfect_root(n, k):
    r = round(n ** (1.0 / k))
    for cand in (r - 1, r, r + 1):
        if cand >= 0 and cand ** k == n:
            return cand
    return None


def _sphere_ratio_value(stem):
    low = stem.lower()
    if "sphere" not in low or "ratio" not in low:
        return None
    pair = _ratio_pair(stem)
    if pair is None:
        return None
    a, b = pair
    if "volume" in low and "radii" in low:
        # Which ratio is ASKED? Both phrases can appear (the
        # given ratio names itself too) — the ask is the one
        # that occurs LAST, in the question's tail.
        ask_radii = low.rfind("ratio of their radii")
        if ask_radii < 0:
            ask_radii = low.rfind("ratio of radii")
        ask_vol = low.rfind("ratio of their volume")
        if ask_vol < 0:
            ask_vol = low.rfind("ratio of volume")
        if ask_radii > ask_vol:
            ra, rb = _perfect_root(a, 3), _perfect_root(b, 3)
            if ra is None or rb is None:
                return None
            steps = [
                "For spheres, volume ∝ (radius)^3, so the "
                "radii are in the cube-root ratio of the "
                "volumes.",
                f"∛{a} : ∛{b} = {ra} : {rb}",
            ]
            return {"type": "geometry", "op": "sphere_ratio",
                    "answer": f"{ra} : {rb}", "steps": steps}
        if ask_vol > ask_radii:
            steps = [
                "For spheres, volume ∝ (radius)^3.",
                f"Volume ratio = {a}^3 : {b}^3 = {a ** 3} : "
                f"{b ** 3}",
            ]
            return {"type": "geometry", "op": "sphere_ratio",
                    "answer": f"{a ** 3} : {b ** 3}",
                    "steps": steps}
    if "surface area" in low and "radii" in low and \
            re.search(r"ratio\s+of\s+(?:their\s+)?radii", low):
        ra, rb = _perfect_root(a, 2), _perfect_root(b, 2)
        if ra is None or rb is None:
            return None
        steps = [
            "For spheres, surface area ∝ (radius)^2, so the "
            "radii are in the square-root ratio of the areas.",
            f"√{a} : √{b} = {ra} : {rb}",
        ]
        return {"type": "geometry", "op": "sphere_ratio",
                "answer": f"{ra} : {rb}", "steps": steps}
    return None


# --- value schema: line through the origin, parallel / --------
# --- perpendicular to a given line ------------------------------

def _line_str(a, b):
    """'3x + 4y = 0' from integer coefficients."""
    parts = []
    for coef, var in ((a, "x"), (b, "y")):
        if coef == 0:
            continue
        mag = var if abs(coef) == 1 else f"{abs(coef)}{var}"
        if not parts:
            parts.append(("-" if coef < 0 else "") + mag)
        else:
            parts.append((" - " if coef < 0 else " + ") + mag)
    return "".join(parts) + " = 0" if parts else "0 = 0"


def _line_origin_value(stem):
    m = re.search(r"passing\s+through\s+(?:the\s+)?origin\s+"
                  r"and\s+(parallel|perpendicular)\s+to\s+"
                  r"the\s+line\s+(.+?)\s*$", stem, re.I)
    if not m:
        return None
    kind, line = m.group(1).lower(), m.group(2)
    line = re.sub(r"(?i)\s+is\s*:?\s*$", "", line.strip())
    if "=" not in line:
        return None
    lhs, rhs = line.split("=", 1)
    try:
        expr = _parse_expr(_clean_expr_text(lhs)) \
            - _parse_expr(_clean_expr_text(rhs))
        xs, ys = _sp.symbols("x y")
        a = int(expr.coeff(xs))
        b = int(expr.coeff(ys))
    except Exception:
        return None
    if kind == "parallel":
        na, nb = a, b
        steps = [
            f"A line parallel to {line.strip()} has the form "
            f"{_line_str(a, b)[:-4]} + c = 0.",
            "It passes through the origin (0, 0), so c = 0.",
            f"The equation is {_line_str(na, nb)}.",
        ]
    else:
        na, nb = b, -a
        steps = [
            f"A line perpendicular to {line.strip()} has "
            f"the form {_line_str(b, -a)[:-4]} + c = 0.",
            "It passes through the origin (0, 0), so c = 0.",
            f"The equation is {_line_str(na, nb)}.",
        ]
    return {"type": "geometry", "op": "line_through_origin",
            "answer": _line_str(na, nb), "steps": steps}


# --- claim schema: the common factor of two polynomials -------
# (A claim schema because the gcd itself need not be an option:
# for x^2 - 4 and x^3 - x^2 - 4x + 4 the gcd is x^2 - 4, while
# the option the board wants is its linear factor (x - 2) —
# the option that DIVIDES both polynomials.)

def _common_factor_claim(stem, options):
    m = re.search(r"factor\s+common\s+to\s+the\s+two\s+"
                  r"polynomials\s+(.+?)\s+and\s+(.+?)\s+is"
                  r"\s*:?\s*$", stem, re.I)
    if not m:
        return None
    try:
        xs = _sp.Symbol("x")
        p = _sp.Poly(_parse_expr(_clean_expr_text(m.group(1))),
                     xs)
        q = _sp.Poly(_parse_expr(_clean_expr_text(m.group(2))),
                     xs)
        common = []
        for label, text in options:
            try:
                cand = _sp.Poly(
                    _parse_expr(_clean_expr_text(text)), xs)
            except Exception:
                continue
            if cand.degree() < 1:
                continue
            if _sp.rem(p, cand, xs).as_expr() == 0 \
                    and _sp.rem(q, cand, xs).as_expr() == 0:
                common.append(label)
        if len(common) != 1:
            return None
        from solver.expression_parser import fmt as _fmt
        steps = [
            f"{_fmt(p.as_expr())} = "
            f"{_fmt(_sp.factor(p.as_expr()))}",
            f"{_fmt(q.as_expr())} = "
            f"{_fmt(_sp.factor(q.as_expr()))}",
            "The factor appearing in both factorisations is "
            f"{dict(options)[common[0]]}.",
        ]
    except Exception:
        return None
    base = {"type": "algebra", "op": "common_factor",
            "answer": dict(options)[common[0]],
            "steps": steps}
    return _shape(base, stem, options, common[0])


# --- value schema: integer solution set of a < expr < b -------

def _inequality_set_value(stem):
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*<\s*(.+?)\s*<\s*"
                  r"(-?\d+(?:\.\d+)?)\s*,?\s*x\s*(?:∈|in)\s*"
                  r"(?:z|integers?)\b", stem, re.I)
    if not m:
        return None
    lo, hi = _Fraction(m.group(1)), _Fraction(m.group(3))
    try:
        xs = _sp.Symbol("x")
        expr = _parse_expr(_clean_expr_text(m.group(2)))
        a = _Fraction(int(expr.coeff(xs).p),
                      int(expr.coeff(xs).q)) \
            if hasattr(expr.coeff(xs), "p") else None
        if a is None or a == 0:
            return None
        b = _Fraction(int(expr.subs(xs, 0).p),
                      int(expr.subs(xs, 0).q)) \
            if hasattr(expr.subs(xs, 0), "p") else None
        if b is None:
            return None
    except Exception:
        return None
    t1 = (lo - b) / a
    t2 = (hi - b) / a
    low, high = min(t1, t2), max(t1, t2)
    import math as _math
    ints = list(range(_math.floor(low) + 1, _math.ceil(high)))
    if not ints or len(ints) > 60:
        return None
    text = "{" + ", ".join(str(i) for i in ints) + "}"
    steps = [
        f"Solve {m.group(1)} < {m.group(2).strip()} < "
        f"{m.group(3)} for x: {low} < x < {high}.",
        f"The integers strictly between {low} and {high} "
        f"are {text}.",
    ]
    return {"type": "algebra", "op": "inequality_set",
            "answer": text, "steps": steps}


# --- value schema: similar triangles, one side asked ---------

def _similar_triangles_value(stem):
    """'ΔABC ~ ΔEFG … AB = 15 cm, BC = 3 cm and FE = 75 cm.
    Find the length of side FG' — correspondence by letter
    position, one complete corresponding pair sets the
    scale, the asked side follows. Side givens must carry a
    unit (an angle fact like '∠EFG = 60°' must never be read
    as a side)."""
    mt = re.search(r"Δ\s*([A-Z])([A-Z])([A-Z])\s*(?:~|∼)\s*"
                   r"Δ?\s*([A-Z])([A-Z])([A-Z])", stem)
    if not mt:
        return None
    tri1 = mt.group(1) + mt.group(2) + mt.group(3)
    tri2 = mt.group(4) + mt.group(5) + mt.group(6)
    ma = re.search(r"length\s+of\s+(?:the\s+)?side\s+"
                   r"([A-Z])([A-Z])", stem)
    if not ma:
        return None
    target = ma.group(1) + ma.group(2)
    givens = {}
    unit = ""
    for g in re.finditer(r"\b([A-Z])([A-Z])\s*=\s*"
                         r"(\d+(?:\.\d+)?)\s*(cm|mm|m)\b",
                         stem):
        givens[frozenset((g.group(1), g.group(2)))] = \
            float(g.group(3))
        unit = g.group(4)

    def corr(side, src, dst):
        return "".join(dst[src.index(ch)] for ch in side)

    def side_key(s):
        return frozenset(s)

    if target[0] in tri2 and target[1] in tri2:
        target_in, other = tri2, tri1
    elif target[0] in tri1 and target[1] in tri1:
        target_in, other = tri1, tri2
    else:
        return None
    counterpart = corr(target, target_in, other)
    if side_key(counterpart) not in givens:
        return None
    base_val = givens[side_key(counterpart)]
    scale = None
    scale_pair = None
    for i in range(3):
        for j in range(i + 1, 3):
            s_other = other[i] + other[j]
            s_target = corr(s_other, other, target_in)
            if side_key(s_other) in givens and \
                    side_key(s_target) in givens:
                scale = givens[side_key(s_target)] / \
                    givens[side_key(s_other)]
                scale_pair = (s_other, s_target)
                break
        if scale is not None:
            break
    if scale is None:
        return None
    value = base_val * scale
    val_str = f"{value:g}"
    steps = [
        f"△{tri1} ~ △{tri2}, so corresponding sides are in "
        "the same ratio.",
        f"{scale_pair[0]}/{scale_pair[1]} gives the scale: "
        f"{givens[side_key(scale_pair[0])]:g} -> "
        f"{givens[side_key(scale_pair[1])]:g} "
        f"(× {scale:g}).",
        f"{target} = {counterpart} × {scale:g} = {val_str} "
        f"{unit}".strip(),
    ]
    return {"type": "geometry", "op": "similar_triangles",
            "answer": f"{val_str} {unit}".strip(),
            "steps": steps}


_VALUE_SCHEMAS = (_coeff_form_value, _ode_fact_value,
                  _rd_maturity_value, _gst_value,
                  _matrix_power_value, _sphere_ratio_value,
                  _line_origin_value, _inequality_set_value,
                  _similar_triangles_value)


def _special_value_result(stem):
    """The first Wave 100 value schema that settles the stem,
    or None. Each schema is fully gated on its own pattern, so
    trying them in order is safe."""
    for schema in _VALUE_SCHEMAS:
        try:
            out = schema(stem)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


# --- claim schema: f : D -> D, f(x) = … is one-one / onto -----

def _fn_claim(text):
    """The (one-one, onto) claim an option text makes, the
    string 'none' for a None-of-these option, or None."""
    t = " " + str(text or "").lower().replace("-", " ") + " "
    if "none of" in t:
        return "none"
    if "neither" in t:
        return (False, False)
    one = "one one" in t or "injective" in t
    onto = "onto" in t or "surjective" in t
    neg_one = "not one one" in t or "not injective" in t
    neg_onto = "not onto" in t or "not surjective" in t
    if one and onto:
        if neg_onto:
            return (True, False)
        if neg_one:
            return (False, True)
        return (True, True)
    if one:
        return (True, False)
    if onto:
        return (False, True)
    return None


def _function_type_claim(stem, options):
    """Wave 93 regression #6: 'Function f : N → N, f(x) = 2x
    is (A) one-one and onto (B) one-one but not onto …'. The
    classification of a linear or monomial f is decidable
    exactly; anything richer falls through unanswered."""
    m = re.search(r"f\s*:\s*([NZQR])\s*(?:→|->)\s*([NZQR])\s*"
                  r",?\s*f\s*\(\s*x\s*\)\s*=\s*(.+?)\s*"
                  r"(?:is)?\s*$", stem)
    if not m:
        return None
    dom, cod, expr_text = m.group(1), m.group(2), m.group(3)
    try:
        xs = _sp.Symbol("x")
        expr = _parse_expr(_clean_expr_text(expr_text))
        if expr.free_symbols - {xs}:
            return None
        poly = _sp.Poly(expr, xs)
    except Exception:
        return None
    inj = surj = None
    if poly is not None and poly.degree() == 1:
        a = poly.nth(1)
        b = poly.nth(0)
        if a == 0:
            return None
        inj = True
        if cod in ("R", "Q"):
            surj = True
        elif cod == "Z":
            surj = abs(a) == 1
        else:  # N: onto only for the identity map x -> x
            surj = (a == 1 and b == 0)
        why_inj = ("f(x1) = f(x2) forces x1 = x2, so f is "
                   "one-one.")
        why_surj = {
            True: "Every value of the codomain is reached, "
                  "so f is onto.",
            False: "Some values of the codomain are never "
                   "reached, so f is not onto.",
        }[bool(surj)]
    elif poly is not None and poly.degree() == 0:
        inj, surj = False, False
        why_inj = "Every input gives the same output, so f " \
                  "is not one-one."
        why_surj = "Only one value is ever reached, so f is " \
                   "not onto."
    elif poly is not None and len(poly.terms()) == 1:
        n = poly.degree()
        lead = poly.nth(n)
        if lead != 1 or n < 2:
            return None
        odd = (n % 2 == 1)
        if dom == "N":
            inj, surj = True, False
        elif dom == "Z":
            inj, surj = odd, False
        else:  # R / Q
            inj = surj = odd
        why_inj = ("Different inputs give different outputs, "
                   "so f is one-one." if inj else
                   "Two different inputs (x and -x) give the "
                   "same output, so f is not one-one.")
        why_surj = ("Every value of the codomain is reached, "
                    "so f is onto." if surj else
                    "Some values of the codomain are never "
                    "reached, so f is not onto.")
    else:
        return None
    computed = (bool(inj), bool(surj))
    matched = []
    none_label = None
    for label, text in options:
        claim = _fn_claim(text)
        if claim == "none":
            none_label = label
        elif claim == computed:
            matched.append(label)
    if len(matched) == 1:
        label = matched[0]
    elif not matched and none_label is not None:
        label = none_label
    else:
        return None
    base = {"type": "algebra", "op": "function_type",
            "answer": dict(options)[label],
            "steps": [why_inj, why_surj]}
    return _shape(base, stem, options, label)


# --- claim schema: nature of the roots of a quadratic ---------

def _roots_claim(text):
    t = str(text or "").lower()
    if "more than two" in t:
        return "impossible"
    if "no real" in t or "not real" in t or "imaginary" in t \
            or "non-real" in t or "no solution" in t:
        return "neg"
    if "equal" in t:
        return "zero"
    if "distinct" in t or "different real" in t \
            or "two real" in t:
        return "pos"
    return None


def _nature_roots_claim(stem, options):
    """'The given quadratic equation 3x^2 + √7x + 2 = 0 has:
    (a) two equal real roots … (d) no real roots' — the
    discriminant's SIGN is the whole question."""
    m = re.search(r"([^.;]*?x\s*(?:\^2|²)[^.;]*?=\s*0)", stem)
    if not m:
        return None
    if "root" not in stem.lower() and not any(
            "root" in str(t).lower() for _l, t in options):
        return None
    eq = re.split(r"(?i)equation\s+", m.group(1))[-1]
    eq = re.sub(r"(?i)^\s*(is|:)\s*", "", eq).strip()
    if "=" not in eq:
        return None
    lhs, rhs = eq.split("=", 1)
    try:
        xs = _sp.Symbol("x")
        expr = _parse_expr(_clean_expr_text(lhs)) \
            - _parse_expr(_clean_expr_text(rhs))
        poly = _sp.Poly(expr, xs)
        if poly is None or poly.degree() != 2:
            return None
        a, b, c = poly.all_coeffs()
        disc = b * b - 4 * a * c
        dval = float(disc)
    except Exception:
        return None
    computed = "pos" if dval > 0 else "zero" if dval == 0 \
        else "neg"
    matched = [label for label, text in options
               if _roots_claim(text) == computed]
    if len(matched) != 1:
        return None
    from solver.expression_parser import fmt as _fmt
    verdict = {
        "pos": "D > 0, so the roots are real and distinct.",
        "zero": "D = 0, so the roots are real and equal.",
        "neg": "D < 0, so the equation has no real roots.",
    }[computed]
    base = {"type": "algebra", "op": "nature_of_roots",
            "answer": dict(options)[matched[0]],
            "steps": [
                f"Here a = {_fmt(a)}, b = {_fmt(b)}, "
                f"c = {_fmt(c)}.",
                f"Discriminant D = b^2 - 4ac = {_fmt(disc)}.",
                verdict,
            ]}
    return _shape(base, stem, options, matched[0])


# --- claim schema: which option CANNOT be a probability -------

def _probability_cannot_claim(stem, options):
    if not re.search(r"cannot\s+be\s+the\s+probability|"
                     r"can\s*not\s+be\s+the\s+probability",
                     stem, re.I):
        return None
    invalid = []
    for label, text in options:
        val = _as_number(_clean(text))
        if val is None:
            try:
                val = _Fraction(
                    str(float(_parse_expr(
                        _clean_expr_text(text)))))
            except Exception:
                return None
        if "%" in str(text):
            val = val / 100
        if val < 0 or val > 1:
            invalid.append((label, text, val))
    if len(invalid) != 1:
        return None
    label, text, val = invalid[0]
    shown = str(text).strip()
    if shown != str(val):
        shown = f"{shown} = {val}"
    base = {"type": "statistics", "op": "probability_range",
            "answer": text,
            "steps": [
                "A probability always lies between 0 and 1.",
                f"{shown} is outside that range, so it "
                "cannot be the probability of an event.",
            ]}
    return _shape(base, stem, options, label)


# --- claim schema: shares at / above / below par --------------

def _dividend_claim(stem, options):
    low = stem.lower()
    if "dividend" not in low or "return" not in low:
        return None
    md = re.search(r"(\d+(?:\.\d+)?)\s*%\s*dividend", stem)
    mr = re.search(r"return\s+on\s+(?:his\s+|the\s+|an\s+)?"
                   r"investment\s+is\s+(\d+(?:\.\d+)?)\s*%",
                   stem)
    if not md or not mr:
        return None
    div, ret = float(md.group(1)), float(mr.group(1))
    if ret < div:
        phrase, why = "above par", (
            f"The shares pay {div:g}% on their face value "
            f"but return only {ret:g}% on the money invested, "
            "so the investor paid MORE than the face value.")
    elif ret > div:
        phrase, why = "below par", (
            f"The shares pay {div:g}% on their face value "
            f"and return {ret:g}% on the money invested, so "
            "the investor paid LESS than the face value.")
    else:
        phrase, why = "at par", (
            f"The dividend rate ({div:g}%) equals the return "
            f"on investment ({ret:g}%), so the market price "
            "equals the face value.")
    matched = [label for label, text in options
               if phrase in str(text).lower()]
    if len(matched) != 1:
        return None
    base = {"type": "applied", "op": "shares_par",
            "answer": dict(options)[matched[0]],
            "steps": [why, f"The shares are {phrase}."]}
    return _shape(base, stem, options, matched[0])


_CLAIM_SCHEMAS = (_function_type_claim, _nature_roots_claim,
                  _probability_cannot_claim, _dividend_claim,
                  _common_factor_claim)


def _special_claim_result(stem, options):
    """The first Wave 100 claim schema that settles the stem,
    or None."""
    for schema in _CLAIM_SCHEMAS:
        try:
            out = schema(stem, options)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


def _stem_result(stem, options):
    """The MCQ answer for an extracted stem: Wave 100 special
    schemas first (fast, exact, authoritative for their
    shapes), then the generic stem machinery — shaped with
    the matched option named, or None."""
    claim = _special_claim_result(stem, options)
    if claim is not None:
        return claim
    special = _special_value_result(stem)
    if special is not None:
        matched = _matching_labels(
            special.get("answer", ""), options)
        if len(matched) == 1:
            return _shape(special, stem, options, matched[0])
    result = _solve_stem(stem)
    if result is None:
        return None
    matched = _matching_labels(result.get("answer", ""),
                               options)
    if len(matched) != 1:
        return None
    return _shape(result, stem, options, matched[0])


def mcq_special_result(question):
    """Only the Wave 100 special schemas over the question's
    stem (no generic stem solve) — multipart.py's fast first
    pass over a bundle's parts; the generic machinery gets
    its own second pass there."""
    extracted = extract_mcq(question)
    if extracted is None:
        return None
    stem, options = extracted
    claim = _special_claim_result(stem, options)
    if claim is not None:
        return claim
    special = _special_value_result(stem)
    if special is not None:
        matched = _matching_labels(
            special.get("answer", ""), options)
        if len(matched) == 1:
            return _shape(special, stem, options, matched[0])
    return None


# ---------------------------------------------------------------------------
# The layer
# ---------------------------------------------------------------------------

def _shape(result, stem, options, label):
    """The result dict for a confident MCQ match: the solver
    result's own steps and shape, with the answer line naming
    the matched option — "(b) 42", the option quoted verbatim
    from the question, so the answer stays in the question's
    own language — plus source="mcq" and an "mcq" block."""
    option_text = dict(options)[label]
    out = dict(result)
    out["answer"] = f"({label}) {option_text}"
    out["source"] = "mcq"
    out["mcq"] = {
        "label": label,
        "option": option_text,
        "stem": stem,
        "options": [text for _l, text in options],
    }
    return out


def mcq_wrap(question, result):
    """Name the option for an ALREADY-SOLVED MCQ: when the
    whole question text solved as-is (some stems survive their
    options), the computed answer is matched against the
    options and, on exactly one match, the same result is
    returned with the option named. No match — or not an MCQ
    at all — returns None and the caller serves the result
    untouched."""
    if not isinstance(result, dict):
        return None
    extracted = extract_mcq(question)
    if extracted is None:
        return None
    stem, options = extracted
    matched = _matching_labels(result.get("answer", ""), options)
    if len(matched) != 1:
        return None
    return _shape(result, stem, options, matched[0])


def mcq_preferred(question, full_result):
    """The MCQ answer when the WHOLE question text already
    solved: for an MCQ the stem is the authority, because the
    option numbers pollute the full-text solve (the HCF of
    "12 and 18 (A) 3 (B) 6 (C) 9 (D) 36" comes out as the HCF
    of all six numbers — 3, the wrong option). So the stem is
    solved first and, on exactly one option match, its result
    is served; only when the stem cannot settle it does the
    full-text result get its chance through mcq_wrap."""
    extracted = extract_mcq(question)
    if extracted is None:
        return None
    stem, options = extracted
    shaped = _stem_result(stem, options)
    if shaped is not None:
        return shaped
    return mcq_wrap(question, full_result)


def mcq_result(question):
    """The MCQ answer for `question`, or None.

    On a confident match the STEM solver's own result dict is
    returned with its answer line naming the matched option —
    "(b) 42", the option quoted verbatim from the question —
    plus source="mcq" and an "mcq" detail block. Anything less
    than exactly one matching option returns None and the
    existing fallback behaviour runs unchanged."""
    extracted = extract_mcq(question)
    if extracted is None:
        return None
    stem, options = extracted
    return _stem_result(stem, options)


__all__ = ["extract_mcq", "mcq_result", "mcq_wrap", "mcq_preferred",
           "mcq_special_result"]
