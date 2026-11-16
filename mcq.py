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
    for candidate in candidates:
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


def _sympy_match(a_text, b_text):
    """Symbolic equivalence through the app's own expression
    parser: (π + 2)10 vs 10π + 20, n² vs n*n, √2 vs sqrt(2)."""
    try:
        from solver.expression_parser import parse_expression
        ea = parse_expression(a_text)
        eb = parse_expression(b_text)
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
    stem_result = _solve_stem(stem)
    if stem_result is not None:
        matched = _matching_labels(
            stem_result.get("answer", ""), options)
        if len(matched) == 1:
            return _shape(stem_result, stem, options, matched[0])
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
    result = _solve_stem(stem)
    if result is None:
        return None
    matched = _matching_labels(result.get("answer", ""), options)
    if len(matched) != 1:
        return None
    return _shape(result, stem, options, matched[0])


__all__ = ["extract_mcq", "mcq_result", "mcq_wrap", "mcq_preferred"]
