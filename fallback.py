"""Wave 18: the no-dead-end answer layer.

Suraj's direction (10 Nov 2026): "Muse or ChatGPT ki tarah
comfortable hona chahiye, har ek question ka answer milna
chahiye." The rule-based solver is exact but narrow: concept
asks ("pythagoras theorem kya hai"), greetings, messy word
problems and off-topic questions used to end at the friendly
error card — or worse, at a letter-multiplied nonsense "answer"
(sympy happily turns unknown words into a product of letters).

`with_fallback(question, result)` sits between the solver and
the routes (api.py's _solve_friendly and app.py's classic
/solve + /photo-solve). A REAL solver answer is returned
untouched. Anything else is routed through the layers:

  0. greetings / small talk (checked before everything — the
     solver turns "hi" into "h*i", which must never be shown)
  0b. known non-maths topics (capital of India, cricket score,
     photosynthesis...) — a friendly maths-only reply, never a
     fake answer
  1. salvage: strip conversational filler (batao, samjhao,
     please, "my homework says..."), extract an embedded
     expression/equation and solve THAT; the reply says plainly
     that it solved the maths part of the question
  2. concepts: the curated concepts.py library (formula + one
     worked example) for "what is X / X kya hai / X ka formula"
  3. topic guess: a similar SOLVED example with different
     numbers, honestly labelled "similar example", plus one
     short line asking for the exact missing detail
  4. vague / gibberish / guide: a friendly reply that shows how
     to ask, with a tiny solved example — never a bare error

Wave 39 adds one layer to this chain, between the science
guard and salvage: the Verified Data Bank (bank.py). When the
solver could not really answer and the question is an EXACT
normalised match with a banked item, the item's own steps +
final answer are served instead of a salvaged fragment, a
similar example or the general guide — every banked answer was
independently SymPy-verified before banking. A real solver
answer is still served untouched above it, a science question
never reaches it, and a miss changes nothing: the rest of the
flow is byte-for-byte the pre-Wave-39 behaviour.

HONESTY RULE: a fallback result is flagged (fallback=True,
fallback_kind=...) and never presents a guessed or similar
answer as the exact answer to the student's question.

Result dicts keep the solver's shape ({type, op, answer,
steps, ...) so every existing renderer (chat bubble, answer
page, print, download, history) works unchanged: the gibberish
guard in i18n only fires for type arithmetic/algebra with
op == "simplify", which no fallback result ever uses.

Wave 67 (Suraj, 15 Nov 2026, with phone screenshots): the
no-dead-end layers above were honest but LOUD — gibberish like
"If tu gfuf" earned the full guide card (mixed-language guide
text, the "Questions I solve for sure" notebook panel, a long
final-answer paragraph and Teacher's Advice). His order:
"jab kuch bhi likh diya to itna bada answer dene ki jarurat
nahi hai — bas 'answer not found' bol do, itna hi." So now
anything that is NOT actually solved — greetings/small talk,
vague asks, gibberish, a similar example, the general guide —
collapses to ONE short line in the question's own language
(fallback_kind == "not_found", see _not_found_result), after
the AI chain has had its chance (solver -> bank -> AI ->
one-line not-found). Real answers are untouched: solver,
salvage, bank, concept cards and AI answers render exactly as
before. The maths-only guards keep their own one-line wording
and gain plain=True so the chat shows just that line: the
science payload keeps its formula-guidance steps for the
full-solution page, the non-maths line is trimmed to the
guard sentence itself.
Wave 90: every outcome that collapses to the one-line
not-found is recorded in the not-found learning log
(notfound_log.py) — question text, detected language, the
student's class when known, and how the chain gave up — so
future waves target real student failures instead of
hand-built audits. The log is purely observational: the hook
below is guarded end to end, a logging failure is a silent
no-op, and no answer changes in any way (proven byte-for-byte
in test_wave90, logging on and off).
"""
import re
from fractions import Fraction

from concepts import find_concept
from concept_topics import topic_concept_result
from i18n import get_strings, solve_failed
from solver.router import has_science_signal, normalize_spelling, \
    solve_question

# ---------------------------------------------------------------------------
# Detectors for "the solver did not really answer"
# ---------------------------------------------------------------------------

# Soft non-answers: the solver asking for more input instead of
# answering ("Tell me the data...", "I need the first term...",
# the word-problem catch-all). These are not answers, so the
# fallback may improve on them — but ONLY via its honest layers.
_SOFT_PREFIXES = (
    "tell me", "i need", "no word-problem pattern matched",
    "give a number", "give me", "please tell", "please give",
    "could not", "enter a", "try a form",
)


def _answer_text(result):
    return str((result or {}).get("answer", "") or "")


def _is_soft(result):
    ans = _answer_text(result).strip().lower()
    return bool(ans) and ans.startswith(_SOFT_PREFIXES)


_SYMBOLIC_COMMANDS = ("simplify", "expand", "factor", "factorise",
                      "factorize", "collect")


def _single_letter_factors(text):
    """Distinct single-letter factors of the *-products in a
    text, in ANY script: split on * and ·, strip the exponent
    off each factor (\"ए**2\" -> \"ए\") and keep the factors
    that are exactly one letter (\"c\", \"m\", \"क\", \"ा\").
    Latin-only counting missed the Devanagari letter-soup —
    the Wave 35 audit's 22 Hindi WRONGs are products of the
    question's own Devanagari letters (Wave 52)."""
    out = set()
    for fac in re.split(r"[*·]", str(text or "")):
        f = fac.strip().strip("()")
        f = re.sub(r"(?:\*\*|\^)\s*\d+(?:\.\d+)?$", "", f).strip()
        if len(f) == 1 and f.isalpha():
            out.add(f)
    return out


def _single_letter_factors(ans):
    """Distinct single-character letter/mark factors of a product
    answer, in ANY script. Wave 58: the old detector counted only
    Latin [a-z] singles, so Devanagari soup ("12*c*m*इ*ए**2*क**4…")
    — two Latin letters and a dozen Devanagari ones, vowel signs
    included — sailed through as a genuine answer."""
    import unicodedata
    t = str(ans).replace("·", "*").replace(" ", "")
    t = re.sub(r"\*\*\d+", "", t)
    out = set()
    for fac in t.split("*"):
        fac = fac.strip("()")
        if len(fac) == 1 and unicodedata.category(fac)[0] in ("L", "M"):
            out.add(fac)
    return out


def _is_junk(question, result):
    """Letter-soup detection: sympy turned the question's words
    into a product of single letters ("what is pythagoras
    theorem" -> a**2*e**2*g*h**2*...). A genuine symbolic answer
    almost never mentions 4+ DISTINCT single letters, and real
    simplify/expand/factor asks are excluded up front.

    Wave 52: the letter count now covers every script (the
    Hindi questions' soup is Devanagari: "12*c*m*इ*ए**2*क**4*…"
    carries only 2 Latin letters but a dozen Devanagari ones),
    and a bare *-chain of 5+ distinct single letters is soup
    even without an exponent mark ("Find the square of 15"
    salvaged to "15*a*e*q*r*s*u" — the word "square" itself,
    letter-multiplied)."""
    q = str(question or "").lower()
    if any(cmd in q for cmd in _SYMBOLIC_COMMANDS):
        return False
    ans = _answer_text(result)
    letters = set(re.findall(r"(?<![A-Za-z])[a-z](?![A-Za-z])", ans))
    factors = _single_letter_factors(ans)
    if any(mark in ans for mark in ("**", "·", "^")):
        if len(ans) >= 8 and len(letters | factors) >= 4:
            return True
        # Wave 57 (merge-3 hand-merge into Wave 52's branch):
        # a SHORT whole-answer product of single letters is
        # soup too — it slipped under the length threshold
        # ("what is HCF" -> "C·F·H", three distinct letters).
        compact0 = ans.replace(" ", "").replace("·", "*")
        if re.fullmatch(r"[A-Za-z](\*\*\d+)?"
                        r"(\*[A-Za-z](\*\*\d+)?)+", compact0):
            if len(set(re.findall(r"[A-Za-z]",
                                  compact0))) >= 3:
                return True
        # Wave 57: Devanagari letter-soup fragments — a
        # product with 4+ short non-Latin fragments is sympy
        # multiplying Hindi words letter-wise (catches the
        # shapes whose factor count stays under the rules
        # above, e.g. two-codepoint fragments).
        parts = re.split(r"[*·]", ans)
        frags = 0
        for part in parts:
            core = re.sub(r"\*\*\d+$", "", part.strip()) \
                .strip("()")
            if 1 <= len(core) <= 2 and \
                    any(ord(c) > 127 for c in core):
                frags += 1
        if len(parts) >= 4 and frags >= 4:
            return True
    if ("*" in ans or "·" in ans) and len(factors) >= 5:
        return True
    # Plain-product form: "a*b*d*m*o*s" — the whole answer is
    # single letters multiplied together, 5+ distinct letters.
    compact = ans.replace(" ", "").replace("·", "*")
    if re.fullmatch(r"[a-z](\*\*\d+)?(\*[a-z](\*\*\d+)?)+",
                    compact):
        return len(letters) >= 5
    # Wave 68: Devanagari letter-soup — a bare Hindi word
    # ("बताओ") letter-multiplied by sympy ("ओ*त*ब*ा") slipped
    # under the Latin thresholds (4 factors, no exponents,
    # and the plain-product regex is Latin-only). A product
    # of 4+ distinct single NON-Latin letters/marks with no
    # digit anywhere in the answer is soup, never a genuine
    # solution (real symbolic answers use Latin symbols).
    if not any(ch.isdigit() for ch in ans) \
            and ("*" in ans or "·" in ans):
        nonlatin = {f for f in factors if ord(f) > 127}
        if len(nonlatin) >= 4:
            return True
    return False


def _is_real(question, result):
    """True when the solver's result may be shown as-is."""
    if not isinstance(result, dict):
        return False
    if solve_failed(question, result):
        return False
    if _is_soft(result) or _is_junk(question, result):
        return False
    if not _answer_text(result).strip():
        return False
    if _w146_veto(question, result):
        return False
    if _w150_veto(question, result):
        return False
    return True


# ---------------------------------------------------------------------------
# Wave 146: ask/result coherence vetoes (from the Wave 135
# CISCE audit, which hand-checked 189 specimen questions
# against the official marking schemes and found ~50 served
# "answers" that were spurious). Each veto is narrow and
# shape-based: it fires only when the question's ASK and the
# result's FORM provably disagree — the signature of a schema
# that solved a different question, or carved a fragment out
# of this one. A vetoed result is not discarded as "wrong
# looking"; the fallback chain below gets its honest chances
# (bank, MCQ stem solve, formats, not-found). A guard that
# eats a legitimate answer is a regression, so every pattern
# here is pinned by test_wave146.py, including a
# false-positive battery.
# ---------------------------------------------------------------------------

_W146_PROOF_MARKERS = ("lhs", "rhs", "hence proved", "proved",
                       "verified", "∴", "hence,")


def _w146_bare_number(ans):
    """The float value when `ans` is JUST a number (optional
    sign, commas, decimal, simple fraction, one trailing unit
    word), else None."""
    s = str(ans or "").strip()
    s = s.split("≈")[0].strip()
    s = re.sub(r"(?i)^(?:rs\.?|₹)\s*", "", s)
    s = re.sub(r"(?i)\s*(?:rs\.?|₹|square\s+units?|sq\.?\s*"
               r"units?|units?|cm\^?2|m\^?2|cm|m|km|hours?|hrs?|"
               r"minutes?|mins?|seconds?|secs?|days?|years?|"
               r"months?|students?|marks?|rupees?|paise|"
               r"litres?|kg|g|%)\s*$", "", s)
    s = s.replace(",", "").replace("−", "-") \
        .replace("–", "-").strip()
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)",
                     s)
    if m:
        den = float(m.group(2))
        return float(m.group(1)) / den if den else None
    if re.fullmatch(r"-?\d+(?:\.\d+)?", s):
        return float(s)
    return None


def _w146_has_plausible_options(question):
    """True when the question carries a PLAUSIBLE MCQ option
    list: at least 3 parsed options, or exactly 2 whose texts
    are both short value-like strings (a True/False pair).
    mcq.extract_mcq also "parses" probability event notation
    — "P(A) = 0.5, P(B) = 0.4" yields two "options" whose
    texts are "= 0.5, P" and a whole sentence; those are
    event NAMES, not options, and a union-probability
    question must keep its real solver answer (the Wave 58
    pins). The Wave 146 authority / salvage-yield checks use
    this test, never the raw extract."""
    try:
        from mcq import extract_mcq
        got = extract_mcq(question)
    except Exception:
        got = None
    if got is None:
        return False
    _stem, options = got
    # Option labels are letters (a-d / A-D). A parse whose
    # "labels" are digits — "(x - 1) / (x + 2)" read as
    # options '1' and '2' — is an expression, not an MCQ
    # (the Wave 55 rational-inequality pin).
    if not all(str(label).strip().isalpha()
               for label, _text in options):
        return False
    # An option text that starts with "=" is notation
    # continuing an equation ("P(A) = 0.5"), never an option.
    if any(str(text).strip().startswith("=")
           for _label, text in options):
        return False
    if len(options) >= 3:
        return True
    if len(options) == 2:
        return all(
            len(str(text).strip()) <= 12
            for _label, text in options)
    return False


def _w146_ar_shaped(question):
    """True for an Assertion–Reason shaped text, including
    the OCR-degraded shape (plain "Assertion:" / "Reason:"
    words plus (a)…(d) options) that formats.extract_ar
    cannot parse."""
    ql = str(question or "").lower()
    return "assertion" in ql and "reason" in ql \
        and "(a)" in ql and "(d)" in ql


def _w146_veto(question, result):
    q = str(question or "")
    ql = q.lower()
    ans = _answer_text(result)
    blob = (ans + " " + " ".join(
        str(s) for s in (result.get("steps") or []))).lower()
    num = _w146_bare_number(ans)

    # V0 — absurd magnitude: a bare integer answer of 13+
    # digits, when every number in the question is small and
    # the student never wrote a factorial / counting notation
    # or a counting frame. (The audit's RD question was
    # answered with a 31-digit "qualifying sum".)
    if num is not None and float(num).is_integer() \
            and len(str(abs(int(num)))) >= 13:
        qnums = [float(v) for v in re.findall(
            r"\d+(?:\.\d+)?", q.replace(",", ""))]
        if (not qnums or max(qnums) < 1e6) and not re.search(
                r"[CP]\s*\(\s*\d+\s*,|\d+\s*[CP]\s*\d+|"
                r"factorial|\d+\s*!|how\s+many\s+ways|"
                r"number\s+of\s+ways|arrang|permutation|"
                r"combination|how\s+many\s+\d+\s*-?\s*digit",
                ql):
            return True

    # V1 — proof asks ("prove that / show that") answered
    # with an assignment chain, a bare matrix or an evaluator
    # number, with no proof working anywhere in the result.
    # (A matrix identity "proof" was served X + I; a
    # continued-proportion proof was served four equation
    # roots.) Genuine proof results carry LHS/RHS working or
    # a verified verdict and pass.
    if re.search(r"\b(?:prove|show)\s+that\b|सिद्ध\s+करो", ql):
        if not any(mk in blob for mk in _W146_PROOF_MARKERS):
            a = ans.strip()
            if re.match(r"^[a-z]\s*=", a) \
                    or a.startswith("[[") \
                    or (num is not None
                        and result.get("op") == "evaluate"):
                return True

    # V2 — a true/false ask needs a verdict word somewhere in
    # the result; a bare carved fraction is not a verdict.
    if re.search(r"\btrue\s+or\s+false\b|\bstate\s+whether\b|"
                 r"\bis\s+it\s+true\b|सही\s+या\s+गलत", ql):
        if not any(w in blob for w in (
                "true", "false", "correct", "incorrect",
                "सही", "गलत")):
            return True

    # V3 — a construction-only ask (construct / ruler and
    # compass, with no computation verb) cannot be answered
    # by a numeric value. (A "construct a circle of radius
    # 4.5 cm" ask was served the circle's area, "20.25·pi" —
    # a numeric-LEADING answer, not a bare number, so the
    # test is on the answer's first character.)
    if re.search(r"\bconstruct\b|ruler\s+and\s+compass", ql) \
            and not re.search(
                r"\bfind\b|\bcalculate\b|\bdetermine\b|"
                r"\bmeasure\b|\bwhat\s+is\b|\bvalue\s+of\b",
                ql) \
            and re.match(r"^\s*-?\d", ans):
        return True

    # V4 — "express ... in terms of <var>" wants an
    # expression, not a bare number (a cylinder case's
    # "express h in terms of r" was served 539/2, the volume
    # fraction carved out of the stem); "express ... in the
    # form R sin(...)" (or cos / tan) wants that function in
    # the answer.
    if re.search(r"\bexpress\b[^.]{0,80}\bin\s+terms?\s+of\b",
                 ql) and num is not None:
        return True
    m = re.search(r"\bexpress\b[^.]{0,100}\bin\s+the\s+form\b"
                  r"[^.]{0,40}?(sin|cos|tan)\b", ql)
    if m and m.group(1) not in ans.lower():
        return True

    # V5 — "find the value of <a + b>" cannot be answered by
    # a single-letter assignment ("b = 0"); "find the value
    # of <k>" cannot be answered by an expression still
    # carrying other free variables (an integral ask for k
    # was served the whole antiderivative in x).
    m = re.search(r"find\s+the\s+value\s+of\s+"
                  r"['‘’]?\s*([a-z])\s*['‘’]?\s*(?:\+|plus)\s*"
                  r"['‘’]?\s*([a-z])\b", ql)
    if m and re.match(r"^\s*[a-z]\s*=", ans):
        return True
    m = re.search(r"(?:find\s+the\s+value\s+of|find)\s+"
                  r"['‘’]?\s*([a-z])\s*['‘’]?\s*"
                  r"(?=[\?\.\,\)]|$|\bwhen\b|\bif\b|\bfor\b)",
                  ql)
    if m:
        var = m.group(1)
        if not re.search(r"\b" + var + r"\s*=", ans):
            others = set(re.findall(r"[a-z]", ans.lower())) \
                - {var}
            if num is None and others:
                return True

    # V6 — an equation ask ("find the equation of ...") needs
    # an equation: the answer must contain "=". The second
    # shape is the case-study part whose final segment IS the
    # equation ask ("... find the following: Equation of the
    # elliptical orbit.") — the audit's ellipse case answered
    # it with the foci distance.
    if "=" not in ans:
        if re.search(r"(?:find|determine|what\s+is)\s+"
                     r"(?:the\s+)?equation\s+of", ql):
            return True
        _seg = re.split(r"[.?]\s+", ql)[-1].strip()
        _tail = _seg.rsplit(":", 1)[-1].strip()
        if re.match(r"(?:find\s+|determine\s+|what\s+is\s+)?"
                    r"(?:the\s+)?equation\s+of\b", _seg) \
                or re.match(
                    r"(?:find\s+|determine\s+|what\s+is\s+)?"
                    r"(?:the\s+)?equation\s+of\b", _tail):
            return True

    # V7 — domain sanity for bare numeric answers: a
    # probability lives in [0, 1], a correlation coefficient
    # in [-1, 1], an ellipse eccentricity in [0, 1).
    if num is not None:
        if ("probability" in ql or "प्रायिकता" in ql) \
                and not re.search(
                    r"\bmean\b|\bexpected\b|\bexpectation\b|"
                    r"\bvariance\b|standard\s+deviation", ql) \
                and not (0 <= num <= 1):
            return True
        if "correlation" in ql and abs(num) > 1:
            return True
        if "eccentricity" in ql and "ellip" in ql \
                and num >= 1:
            return True

    # V8 — the given-echo: "x = 8500" served for a question
    # that GIVES "∑ x = 8500" as data (a regression-estimate
    # ask). The answer merely restates a given sum.
    m = re.match(r"^\s*([a-zA-Z])\s*=\s*(-?[\d,]+(?:\.\d+)?)"
                 r"\s*$", ans)
    if m:
        var = m.group(1)
        val = m.group(2).replace(",", "")
        if re.search(r"(?:∑|Σ|\bsum\b)[^=]{0,14}?"
                     + re.escape(var) + r"\s*=\s*"
                     + re.escape(val) + r"\b", q):
            return True

    # V9 — the arithmetic evaluator's fragment carve: an
    # "evaluate" op result for a question whose data is a
    # grouped table (3+ class intervals — an ogive case was
    # answered "-10" from the interval "0 − 10") or whose ask
    # is a derivative / rate of change (answered with an echo
    # of the given t value).
    if str(result.get("op") or "") == "evaluate":
        if len(re.findall(
                r"\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?",
                q)) >= 3 \
                or re.search(r"\bdy\s*/\s*dx\b|\bderivative\b|"
                             r"\brate\s+of\s+change\b|"
                             r"\bdifferentiat", ql) \
                or re.search(r"geometric\s+progression|"
                             r"arithmetic\s+progression", ql) \
                or re.search(
                    r"\bfind\s+(?:the\s+)?(?:height|radius|"
                    r"diameter|area|volume|length|width|"
                    r"breadth|perimeter|circumference|side|"
                    r"distance|speed|time|cost|price)\b", ql):
            # A series ask ("Find S1 + S2 + ... + Sn" for n
            # geometric progressions) answered by evaluating
            # ONE fraction out of the text is a carve, not a
            # sum. The same holds for a mensuration find-ask
            # ("Find the height of the tank" answered with the
            # stem's volume fraction 539 ÷ 2): the evaluator
            # has no formula, so its number is a fragment.
            return True

    # V10 — the support-set mean: for a probability /
    # distribution question whose random variable takes the
    # values in a brace set {0, 1, 2, 3}, the plain mean of
    # the SET (1.5) is not E(X) — E(X) needs the
    # probabilities. (The router's candidate extraction
    # synthesised "mean of 0,1,2,3" out of the case and
    # served it for every part; the true mean was 2.4.)
    if num is not None:
        _sup = re.search(r"\{\s*(\d+(?:\s*,\s*\d+)+)\s*\}", q)
        if _sup and ("probab" in ql or "distribution" in ql
                     or "random variable" in ql
                     or "∈" in q
                     or re.search(r"let\s+x\s+be", ql)):
            _vals = [float(v) for v in
                     _sup.group(1).split(",")]
            if _vals and abs(
                    num - sum(_vals) / len(_vals)) < 1e-9:
                return True

    # V11 — triangle medians are not a data median: when the
    # question is about the medians of a triangle (their
    # intersection point G), a statistics "median" result is
    # a hijack of the word (the audit's vectors case was
    # answered "Median = 1" from the point (0, 1, 2)). The
    # router's candidate text may lose the triangle context,
    # so the check sits here, on the original question.
    if str(result.get("op") or "") == "median" and re.search(
            r"medians?\s+of\s+(?:the\s+)?(?:triangle|∆|Δ)|"
            r"intersection\s+of\s+the\s+medians", ql):
        return True

    # V12 — coordinates are a PAIR, never a bare number:
    # "find the coordinates of B and C" (turning points of
    # a cubic) was answered "0" — a derivative value carved
    # out of the working. Judged on the FINAL ask segment
    # only, and exempt for single-axis asks ("y-coordinate
    # of B" — that answer IS a bare number) and for
    # distance/length asks that merely mention coordinates.
    _seg = re.split(r"[.?]\s+", ql)[-1]
    if num is not None and re.search(
            r"coordinates?\s+of", _seg) and not re.search(
            r"\b[xy]\s*-?\s*coordinates?\s+of|"
            r"distance|length|area|perimeter", _seg):
        return True

    # V8b — the given-value echo for derived-quantity asks:
    # "Find the marginal revenue when x = 5" answered with
    # "x = 5" — the answer restates the GIVEN evaluation
    # point instead of computing the derived quantity.
    m = re.match(r"^\s*([a-z])\s*=\s*(-?[\d]+(?:\.\d+)?)\s*$",
                 ans)
    if m and re.search(
            r"\b(?:when|at)\s+" + re.escape(m.group(1))
            + r"\s*=\s*" + re.escape(m.group(2)) + r"\b", ql) \
            and re.search(
                r"marginal|derivative|dy\s*/\s*dx|"
                r"rate\s+of|differentiat|gradient", ql):
        return True
    return False


# ---------------------------------------------------------------------------
# Wave 150: book-style wrong-serve vetoes (from the Wave 135
# books programme's hand-checked calibrations: CISCE ~50 of
# 76 raw "SOLVED" serves verifiably wrong, UP 25 of 40, Bihar
# 41 of 60 — wrong-schema serves, asked-quantity mismatches,
# given echoes and evaluator carves on raw book text). Like
# Wave 146's veto, each rule fires only when the question's
# ASK and the result's FORM provably disagree; a vetoed
# result falls through to the honest chain (bank, MCQ stem
# solve, formats, verified AI, not-found) — a replacement
# answer is never invented here. Every rule is pinned by
# test_wave150.py, including its false-positive battery.
# ---------------------------------------------------------------------------

def _w150_bare_number(ans):
    """_w146_bare_number plus the square/cube unit suffixes
    mensuration answers carry (cm², cm³, m², m³)."""
    s = str(ans or "").strip()
    s = re.sub(r"(?:cm|m|mm|km)(?:²|³|\^2|\^3)\s*$", "", s)
    s = re.sub(r"(?:²|³)\s*$", "", s)
    return _w146_bare_number(s)


_W150_PART_LABEL = r"\((i|ii|iii|iv|v|vi|a|b|c|d|e)\)"


def _w150_part_labels(text):
    return set(re.findall(_W150_PART_LABEL,
                          str(text or "").lower()))


def _w150_factorised_numbers(steps):
    """Reconstruct the integers a steps block factorises:
    lines like "Prime factorisation: 4052 = 2^2 × 1013" or
    "4052 = 2^2 × 1013" whose stated factors multiply back
    to the stated number. Returns the list of validated
    integers (parse failures are skipped, never guessed)."""
    out = []
    for line in (steps or []):
        m = re.search(r"(\d+)\s*=\s*"
                      r"((?:\d+(?:\^\d+)?\s*(?:×|\*|x)\s*)*"
                      r"\d+(?:\^\d+)?)\s*$", str(line).strip())
        if not m:
            continue
        n = int(m.group(1))
        try:
            val = 1
            for tok in re.split(r"\s*(?:×|\*|x)\s*",
                                m.group(2)):
                if "^" in tok:
                    p, e = tok.split("^")
                    val *= int(p) ** int(e)
                else:
                    val *= int(tok)
        except Exception:
            continue
        if val == n and n not in out:
            out.append(n)
    return out


def _w150_veto(question, result):
    try:
        return _w150_veto_inner(question, result)
    except Exception:
        return False


def _w150_veto_inner(question, result):
    if not isinstance(result, dict):
        return False
    q = str(question or "")
    ql = q.lower()
    ans = _answer_text(result)
    al = ans.lower()
    blob = (ans + " " + " ".join(
        str(s) for s in (result.get("steps") or []))).lower()
    op = str(result.get("op") or "")
    num = _w150_bare_number(ans)
    qints = [int(v) for v in re.findall(r"\d+", q.replace(",", ""))]

    # W1 — dimension clash: a LENGTH quantity is the find
    # target (diameter / radius / circumference / perimeter,
    # incl. Hindi) but the answer carries AREA units; or a
    # VOLUME target answered in area units / an AREA target
    # answered in volume units. (UP idx 4149: diameter asked,
    # "20.25·pi ≈ 63.6173 cm²" served.)
    _len_target = re.search(
        r"(?:find|calculate|determine|measure\s+of|what\s+is)"
        r"[^.]{0,40}?\b(diameter|radius|circumference|"
        r"perimeter)\b", ql) or re.search(
            r"(व्यास|त्रिज्या|परिधि|परिमाप)\s*(?:ज्ञात|निकाल|बताओ)", q)
    _area_target = re.search(
        r"(?:find|calculate|determine|what\s+is)[^.]{0,40}?"
        r"\barea\b", ql) or "क्षेत्रफल" in q
    _vol_target = re.search(
        r"(?:find|calculate|determine|what\s+is)[^.]{0,40}?"
        r"\bvolume\b", ql) or "आयतन" in q
    if re.search(r"(?:cm|m|mm|km)²|sq\.?\s*(?:cm|m|units?)|"
                 r"square\s+units?", ans):
        if _len_target and not _area_target:
            return True
        if _vol_target and not _area_target:
            return True
    if re.search(r"(?:cm|m|mm|km)³", ans) and _area_target \
            and not _vol_target:
        return True

    # W2 — a PRICE is the find target but the answer is a
    # bare percentage. (UP idx 4047/4064: "selling price"
    # answered "80.7692%" / "99.76%".) A percent ask in the
    # question disarms the rule.
    if re.search(r"(?:selling|sale)\s+price|cost\s+price|"
                 r"what\s+price|at\s+what\s+price|"
                 r"विक्रय\s*मूल्य|क्रय\s*मूल्य", ql + q) \
            and not re.search(r"percent|प्रतिशत", ql + q):
        if re.fullmatch(r"-?\d+(?:\.\d+)?\s*%", ans.strip()):
            return True

    # W3 — a SUM is asked but the answer is the unsummed
    # list of addends. (CBSE idx 1695: sum of odd numbers
    # 0–50 served as the 25-number list.)
    if re.search(r"\bsum\s+of\b", ql) or "योग ज्ञात" in q \
            or "योग निकाल" in q:
        if re.fullmatch(
                r"-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?){4,}",
                ans.strip()):
            return True

    # W4 — primality-verdict serves: a bare "N is (not)
    # prime" verdict is only an answer to a primality ask.
    # Factorisation asks (fixed at the solver seam too) and
    # "which of the following are prime" list asks (where a
    # one-number verdict is at best partial) decline.
    if re.fullmatch(r"\s*\d+\s+is\s+(?:not\s+)?prime\s*\.?\s*",
                    al):
        if re.search(r"which\s+of\s+the\s+following[^.]*"
                     r"\bare\s+prime\b", ql):
            return True
        if not re.search(r"\bis\s+\d+\s+prime\b|"
                         r"\bis\s+\d+\s+a\s+prime\b|"
                         r"\b\d+\s+is\s+(?:a\s+)?prime\b|"
                         r"\bare\s+prime\b|"
                         r"prime\s+or\s+composite|"
                         r"अभाज्य\s+है", ql + q):
            return True

    # W5 — symbol soup in the ANSWER: an em/en dash used as
    # an algebraic factor (OCR minus signs parsed as
    # symbols: "x = 11/(9·—)"), the degree sign used as a
    # multiplied/divided operand ("B = 72·°/Z"), the
    # "I/<letter>" factor (the word "If" parsed as I·f),
    # and differential-equation asks answered by assigning
    # the letter d or by a LambertW expression.
    if re.search(r"[·*×]\s*[—–]|[—–]\s*[·*×]|[—–]\s*/|"
                 r"/\s*[—–]|\(\s*[—–]|[—–]\s*\)", ans):
        return True
    if re.search(r"·\s*°|°\s*/|/\s*°|(?<!\d)°\s*=|=\s*°",
                 ans):
        return True
    if re.search(r"\bI\s*/\s*[a-z]\b", ans):
        return True
    # Guillemets as algebraic factors ("64800*»**2") are
    # OCR quote debris parsed as symbols — never a result.
    if re.search(r"[»«]", ans) and ("*" in ans or "·" in ans):
        return True
    if (re.search(r"\bdy\b", ql) and re.search(r"\bdx\b", ql)) \
            or "dy/dx" in ql:
        if re.match(r"\s*d\s*=", ans) \
                or "lambertw" in al:
            return True

    # W6 — the solver's own refusal served as an answer:
    # "The equation has no variable to solve for." (alone,
    # or repeated per part in a multipart card) is a
    # non-answer, never a result. EXEMPTION: when the
    # question genuinely poses an equation in a variable
    # (a digit-glued term like "2x", or a standalone
    # variable next to an operator), the same string is
    # the solver's designed no-solution serve — Wave 77
    # pins it byte-for-byte ("bhai 2x + 3 = 2x + 5 solve
    # karo"). The adjudicated rows are variable-free
    # statements ("5 + 2 + 3 = 10", "3 x 9 = 27" — the
    # x there is a multiplication sign between digits).
    _w6 = re.sub(_W150_PART_LABEL, " ", al)
    _w6 = _w6.replace(
        "the equation has no variable to solve for", " ")
    if not re.sub(r"[\s.;:,()]+", "", _w6):
        if not re.search(r"\d[a-z](?![a-z])|"
                         r"(?<![a-z\d])[a-z](?![a-z])"
                         r"\s*(?:[+\-*/=]|$)", ql):
            return True

    # W6b — fill-in-the-blanks pages carry several blanks;
    # one bare number cannot answer them (a stray carved
    # statistic was served for a Hindi fill-in page).
    if ("रिक्त स्थान" in q or "fill in the blank" in ql) \
            and _w150_bare_number(ans):
        return True

    # W7 — a multi-part ask (3+ part markers) answered with
    # ONE bare value and no part labels: at most one part
    # was answered. (UP percent multipart rows 4008/4021/
    # 4009, cube volumes 4187, Bihar products 4802.)
    _part_hits = len(re.findall(
        r"\((?:i|ii|iii|iv|v|vi)\)", ql))
    if _part_hits >= 3 and num is not None \
            and not _w150_part_labels(ans):
        return True
    # W7b — a labelled serve covering only SOME of the
    # question's parts (the multipart card for UP idx 3717
    # served "(ii) 10" with part (i) unanswered inside a
    # "solved" card). Scope: genuine multipart cards
    # (Waves 100/141) serve the parts they can solve BY
    # DESIGN — partial coverage alone is not a wrong
    # serve there; the veto fires for non-card serves
    # covering a subset, and for any serve (card or not)
    # covering exactly ONE part of a multi-part ask.
    _qlabels = _w150_part_labels(q)
    _alabels = _w150_part_labels(ans)
    _is_card = str(op).startswith("multipart") \
        or isinstance(result.get("multipart"), dict)
    if len(_qlabels) >= 2 and _alabels \
            and _alabels < _qlabels \
            and (not _is_card or len(_alabels) == 1):
        return True
    # W7c — a many-part ask (4+ markers) answered with one
    # short unlabelled phrase (UP idx 6107: six quadrant
    # parts answered with only the first quadrant).
    if _part_hits >= 4 and not _alabels \
            and len(ans.strip()) <= 60 \
            and num is None:
        return True

    # W8 — HCF *and* LCM are both asked (EN / Hindi /
    # abbreviations) but the answer is a single bare
    # number: one of the two is missing. (Bihar idx 6864
    # served only the HCF; idx 7559 served a bare 2 for an
    # LCM-given-HCF-and-product ask.)
    if re.search(r"\bhcf\b[^.।]{0,30}?\blcm\b|"
                 r"\blcm\b[^.।]{0,30}?\bhcf\b|"
                 r"म\.स\.[^.।]{0,40}?ल\.स\.|"
                 r"ल\.स\.[^.।]{0,40}?म\.स\.|"
                 r"महत्तम\s+समापवर्तक[^.।]{0,40}?"
                 r"लघुत्तम", ql + q) and num is not None:
        return True

    # W9 — given echoes: the answer restates a given
    # instead of computing the asked quantity.
    # (a) distribute/divide/share in a ratio, answered with
    # the ratio itself (UP idx 3973: "3 : 2").
    _ratio = re.search(r"(\d+)\s*:\s*(\d+)", q)
    if _ratio and re.search(r"\bdistribute\b|\bdivide\b|"
                            r"\bshare\b", ql) \
            and "ratio" in ql:
        if ans.replace(" ", "") == \
                f"{_ratio.group(1)}:{_ratio.group(2)}":
            return True
    # (b) "find two numbers whose HCF is H and LCM is L"
    # answered by restating "HCF = H, LCM = L" (CBSE 822).
    _fn = re.search(r"find\s+(?:two|the)\s+numbers?\s+whose"
                    r"\s+hcf\s+is\s+(\d+)\s+and\s+(?:their\s+)?"
                    r"lcm\s+is\s+(\d+)", ql)
    if _fn:
        _fa = re.fullmatch(r"\s*HCF\s*=\s*(\d+)\s*,\s*LCM"
                           r"\s*=\s*(\d+)\s*", ans)
        if _fa and _fa.groups() == _fn.groups():
            return True
    # (c) the LCM slot filled with the given PRODUCT
    # (UP idx 3877: HCF 16, product 6400 -> "LCM = 6400";
    # the true LCM is 6400 / 16 = 400).
    _ph = re.search(r"\bhcf\s+is\s+(\d+)", ql)
    _pp = re.search(r"\bproduct\s+is\s+(\d+)", ql)
    if _ph and _pp and int(_ph.group(1)) > 1:
        _la = re.search(r"LCM\s*=\s*(\d+)", ans)
        if _la and int(_la.group(1)) == int(_pp.group(1)):
            return True
    # (d) "write N equations whose solution is x = v"
    # answered by restating "x = v" (CBSE idx 943).
    if re.search(r"write\s+\d+\s+equations?\s+whose\s+"
                 r"solution\s+is", ql):
        _sa = re.fullmatch(r"\s*([a-z])\s*=\s*(-?[\d.]+)"
                           r"\s*", ans)
        if _sa and re.search(
                r"solution\s+is\s+" + _sa.group(1) +
                r"\s*=\s*[–—-]?\s*" +
                re.escape(_sa.group(2).lstrip("-")), ql):
            return True
    # (e) "how many times" asks: a bare answer equal to
    # the question's FIRST given number is the echo of
    # that given (Hindi twin idx 4474 served 95), and the
    # ingredients form "HCF = a, LCM = b" is not the
    # quotient asked for (UP idx 3880).
    if "how many times" in ql or "कितनी बार" in q:
        # Occurrence-count asks — "how many times does
        # the digit 3 occur in 1333?" / "does 3 occur in
        # the data ..." — are Wave 103's counting layer;
        # their small counts legitimately coincide with
        # a number in the question, so the first-given
        # echo test does not apply to them.
        if not re.search(r"does\b[^?]*\boccur", ql):
            if num is not None and qints \
                    and abs(num - qints[0]) < 1e-9:
                return True
        if "HCF =" in ans and "LCM =" in ans:
            return True
    # (f) a sum ask whose bare answer is the question's
    # first number — the evaluator carved the range start
    # (Bihar idx 7071: sum of odds 0–50 served "0").
    if (re.search(r"\bsum\s+of\b", ql) or "योग" in q) \
            and num is not None and len(qints) >= 2 \
            and abs(num - qints[0]) < 1e-9:
        return True

    # W10 — a factorisation ask answered with a bare
    # number (Bihar factorise rows served -6, -20, -15,
    # -2, -3; UP factorise idx 5734 served 11). A
    # factorise-AND-root ask is exempt: the bare number
    # is the asked root, served by the purpose-built
    # repeated-root layer (Wave 65: "factorise x^2 -
    # 12x + 36 and give the repeated root" -> 6).
    if re.search(r"\bfactoriz?e\b|\bfactorise\b|"
                 r"गुणनखंड", ql + q) and num is not None \
            and not re.search(r"\broots?\b", ql):
        return True

    # W11 — proof / show / verify / give-reasons asks
    # (incl. Hindi दर्शाइए / दिखाइए / सिद्ध / सत्यापित)
    # answered without any proof working: a bare number,
    # an evaluator result, or a short verdict. Genuine
    # proof results carry LHS/RHS working or a proved
    # verdict and pass (Wave 146 V1's marker list).
    _proof_ask = re.search(
        r"\bprove\b|\bshow\s+that\b|दर्शाइए|दिखाइए|सिद्ध|"
        r"सत्यापित|\bverify\s+(?:that|whether)\b", ql + q)
    # The purpose-built verdict layers — verify_zeroes
    # (Wave 32) and isprime — CHECK each candidate and
    # their verdicts, including negative ones ("Not
    # all ..."), are computed from their own working;
    # they are not carves or bare verdicts, so W11
    # does not gate them. (The adjudicated verify row,
    # Bihar idx 6248, was served by the evaluator
    # carve, op "evaluate"; the isprime hijack rows
    # were factor asks, fixed at the solver seam and
    # by W4 — "prove that N is prime" IS a primality
    # ask, Wave 95's pin.)
    if _proof_ask and op not in ("verify_zeroes",
                                 "isprime") and not any(
            mk in blob for mk in _W146_PROOF_MARKERS):
        # An affirmative verdict WITH working ("Yes, the
        # points are collinear" + the area computation) is
        # the designed serve of the show-that layers
        # (Wave 115's collinearity guard) — not a
        # non-answer. A "No" verdict gets no exemption: a
        # textbook show-that proposition is true, so a
        # denial means the layer misread the question
        # (Bihar idx 7142 denied the question's own given
        # right angle).
        # A genuine computation schema (NOT the evaluator
        # carve) whose steps DERIVE the claimed number
        # answers a concrete-instance claim by computing
        # it — Wave 55's PMI topic serve ("prove ... the
        # sum of the first 8 odd numbers is 64" -> the
        # n^2 computation whose last step ends "= 64").
        # The carve (op "evaluate", "Evaluate: 0 = 0")
        # and verdict serves (num is None) stay vetoed.
        _derived150 = False
        if num is not None and op != "evaluate":
            for _s150 in (result.get("steps") or []):
                if str(_s150).rsplit("=", 1)[-1].strip() \
                        == ans.strip():
                    _derived150 = True
                    break
        if not _derived150:
            if num is not None or op == "evaluate" \
                    or len(ans.strip()) < 80:
                if not re.match(r"\s*yes\b", al):
                    return True
    if re.search(r"give\s+reasons?\b|कारण\s+(?:दीजिए|बताइए)",
                 ql + q) and num is None:
        if not any(w in blob for w in (
                "because", "since", "divides", "cannot",
                "not possible", "कारण")):
            if re.search(r"HCF\s*=|LCM\s*=", ans):
                return True

    # W12 — draw / construct / plot asks (incl. Hindi
    # रचना) with no computation verb, answered with a
    # number or a bare assignment. Extends Wave 146 V3's
    # "construct" to "draw" / "plot a graph" (UP idx 4098
    # "Draw a triangle" -> "A = 6/B"; idx 6114 plot ->
    # "8"; Bihar idx 6648 construction heading -> "180°").
    if re.search(r"\bdraw\b|\bconstruct\b|"
                 r"\bplot\s+a\s+graph\b|रचना", ql + q) \
            and not re.search(
                r"\bfind\b|\bcalculate\b|\bdetermine\b|"
                r"\bmeasure\b|\bwhat\s+is\b|\bvalue\s+of\b",
                ql):
        if re.match(r"\s*-?\d", ans) \
                or re.fullmatch(r"\s*[A-Za-z]\s*=\s*"
                                r"[^\n]{1,30}", ans):
            return True

    # W13 — derivative asks answered by solving for the
    # variable instead: an assignment to x, or a y = ...
    # solution with no dy/dx anywhere. (CBSE idx 2484:
    # derivative of 99x -> "x = 0"; idx 2779: dy/dx ask
    # -> "y = -10, y = 10".)
    if re.search(r"dy\s*/\s*dx", ql) \
            or (re.search(r"\bdy\b", ql)
                and re.search(r"\bdx\b", ql)) \
            or re.search(r"\bderivative\b|\bdifferentiat",
                         ql):
        if re.match(r"\s*x\s*=", ans):
            return True
        if re.match(r"\s*y\s*=", ans) \
                and "dy/dx" not in blob:
            return True

    # W14 — a SECTOR area ask whose working is the full
    # circle formula pi·r^2 with the stated radius: the
    # sector's fencing/arc datum was ignored. (ICSE idx
    # 3370, flagged already by Wave 146 as a schema gap;
    # the gate declines it until the schema exists.)
    if "sector" in ql and re.search(
            r"area\s*=\s*pi\s*[·*×]\s*r\^2\s*=\s*pi", blob):
        return True

    # W15 — an arrange-in-order ask answered by a
    # statistics RANGE result (UP idx 3593).
    if re.search(r"\barrange\b|ascending|descending|"
                 r"आरोही|अवरोही", ql + q) and op == "range":
        return True

    # W16 — a comparison ask ("which subject ... good
    # marks") answered with one side's bare percentage
    # and no verdict (UP idx 4031).
    if re.search(r"\bwhich\b", ql) and re.search(
            r"\bbetter\b|\bgood\s+marks\b|\bmore\b|"
            r"\bgreater\b|\bhigher\b", ql):
        if re.fullmatch(r"-?[\d.,]+\s*%?", ans.strip()):
            return True

    # W17 — a naming ask ("write down the names of ...")
    # answered with a bare number (UP idx 5900).
    if re.search(r"write\s+down\s+the\s+names|"
                 r"name\s+the\s+following|नाम\s+लिखिए",
                 ql + q) and num is not None:
        return True

    # W18 — a stated angle-sum fact contradicted by the
    # serve: the question STATES "योग <N> होता है" and the
    # answer is a different bare degree value. (Bihar idx
    # 6615: cyclic-quadrilateral statement says 180, the
    # generic quadrilateral schema served 360°. The OCR
    # degree glyph often lands as a trailing 0 — 1800 for
    # 180° — so both readings of the stated value pass.)
    _st = re.search(r"योग\s+(\d+)\s*°?\s*होता\s+है", q)
    if _st:
        _sv = int(_st.group(1))
        _readings = {_sv}
        if _sv >= 1000 and _sv % 10 == 0:
            _readings.add(_sv // 10)
        _da = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*°\s*",
                           ans)
        if _da and float(_da.group(1)) not in _readings:
            return True

    # W20 — the ratio itself is the ask (अनुपात के रूप में
    # / "as a ratio") but an AREA result was served
    # (UP idx 4512: ratio of length to breadth -> 725).
    if ("अनुपात के रूप में" in q
            or re.search(r"\bas\s+a\s+ratio\b", ql)) \
            and op == "area":
        return True

    # W21 — combinatorial notation read as algebra: the
    # question uses nC<n> notation and the answer assigns
    # a value to the letter C. (CBSE idx 2202: "If
    # nC8 = nC2, find nC2" -> "C = 0"; idx 2203 likewise.)
    if re.search(r"\bn\s*C\s*\d+|\bnC\d+", q) \
            and re.search(r"\bC\s*=", ans):
        return True

    # W22 — a cost-at-a-rate ask answered with a bare
    # area value and no money anywhere (ICSE/UP road
    # case, UP idx 6168: cost of repairing the road
    # served as the park's own area).
    if "cost" in ql and re.search(r"per\s+sq|rate\s+of",
                                  ql):
        if "₹" not in ans and "rs" not in al:
            return True

    # W23 — a speed ask answered by a DISTANCE result
    # (UP idx 5059: speed for the same distance in 8 h
    # served 384, the 48 × 8 product).
    if re.search(r"what\s+will\s+be\s+(?:the\s+)?speed|"
                 r"find\s+(?:the\s+)?speed", ql) \
            and op == "distance":
        return True

    # W24 — HCF/LCM verification against the result's OWN
    # factorisation steps: when the steps factorise two
    # numbers a and b, the served GCD/LCM must equal
    # gcd/lcm(a, b). The audits' poisoned serves folded
    # stray integers from the book text (page numbers,
    # the printed division working) into the fold — Bihar
    # idx 6852 served GCD 2 for (4052, 12576) whose own
    # steps factorise to gcd 4; UP idx 3853 served 2 for
    # (306, 630), gcd 18. Skipped when the question lists
    # 3+ numbers comma-wise (a genuine multi-number ask
    # whose fold legitimately differs from the pair gcd).
    if op in ("gcd", "lcm", "hcf_lcm"):
        _fac = _w150_factorised_numbers(
            result.get("steps") or [])
        # The pair is the FULL operand set only when the
        # ask segment itself (the sentence carrying the
        # HCF/LCM phrase) names exactly those two numbers:
        # a genuine 3-number ask ("HCF of 2052, 3996 and
        # 7380") names three in its segment and its fold
        # legitimately differs from the pair gcd.
        _seg = None
        for _s in re.split(r"[।.?\n]", q):
            if re.search(r"hcf|lcm|gcd|म\.स\.|ल\.स\.|"
                         r"महत्तम|लघुत्तम", _s.lower()):
                _seg = _s
                break
        _seg_ints = set()
        if _seg is not None:
            _seg_ints = {int(v) for v in re.findall(
                r"\d+", _seg.replace(",", ""))}
        if len(_fac) >= 2 and len(_seg_ints) == 2 \
                and set(_fac[:2]) == _seg_ints:
            import math as _m
            _a, _b = _fac[0], _fac[1]
            _g = _m.gcd(_a, _b)
            _l = _a * _b // _g
            if op == "gcd" and num is not None \
                    and abs(num - _g) > 1e-9:
                return True
            if op == "lcm" and num is not None \
                    and abs(num - _l) > 1e-9:
                return True
            if op == "hcf_lcm":
                _pair = re.search(
                    r"HCF\s*=\s*(\d+)\s*,\s*LCM\s*=\s*(\d+)",
                    ans)
                if _pair and (int(_pair.group(1)) != _g
                              or int(_pair.group(2)) != _l):
                    return True

    # W8b — the asked one of HCF/LCM is not the computed
    # one: the question asks for the LCM (ल.स. not followed
    # by its given value / "find the lcm") with no HCF ask,
    # but the result's own steps label the computation
    # "HCF of ..." — the Hindi handler folded the GIVEN
    # pair (Bihar idx 7559: LCM asked from HCF 46 and
    # product 6400, served "HCF of 46 and 6400 = 2").
    # Mirror image for an HCF ask with "LCM of ..." steps.
    _steps_txt = " ".join(
        str(s) for s in (result.get("steps") or []))
    _lcm_ask150 = re.search(r"ल\.स\.(?!\s*\d)", q) \
        or re.search(r"\bfind\s+(?:the\s+)?lcm\b", ql)
    _hcf_ask150 = re.search(r"म\.स\.(?!\s*\d)", q) \
        or re.search(r"\bfind\s+(?:the\s+)?(?:hcf|gcd)\b",
                     ql)
    if _lcm_ask150 and not _hcf_ask150 \
            and re.search(r"\bHCF\s+of\b", _steps_txt):
        return True
    if _hcf_ask150 and not _lcm_ask150 \
            and re.search(r"\bLCM\s+of\b", _steps_txt):
        return True

    # W10b — a SIMPLIFY ask over variable expressions
    # (letters mixed into digit-bearing tokens, 3+
    # distinct) answered with a bare number: the number
    # was carved out of one part (UP idx 3717).
    if "simplify" in ql and num is not None:
        _mixed = [t for t in re.findall(r"[a-z0-9]+", ql)
                  if any(c.isalpha() for c in t)
                  and any(c.isdigit() for c in t)]
        _letters = {c for t in _mixed for c in t
                    if c.isalpha()}
        if len(_letters) >= 3:
            return True

    # W19 — "rational numbers between A and B" answered
    # with a single number OUTSIDE (A, B): it cannot be
    # one of the asked numbers (UP idx 4711 served 3 for
    # "between 1 and 2").
    _rb = re.search(
        r"rational\s+numbers?\s+(?:in\s+)?between\s+"
        r"(?:the\s+(?:numbers?\s+)?)?(-?\d+(?:\.\d+)?)"
        r"\s+and\s+(-?\d+(?:\.\d+)?)", ql)
    if _rb and num is not None:
        _lo, _hi = float(_rb.group(1)), float(_rb.group(2))
        if not (_lo < num < _hi):
            return True

    # W25 — "find the value of <expr> and <expr>" answered
    # with the intermediate variable alone (CBSE idx 958:
    # values of 14p − 19 and 28p − 38 answered "p = 67/14").
    if re.search(r"find\s+the\s+value\s+of\s+[^.]{1,60}?"
                 r"\band\b", ql) \
            and not re.search(
                r"find\s+the\s+value\s+of\s+[a-z]\s*(?:and|,|$)",
                ql):
        _m25 = re.fullmatch(r"\s*([a-z])\s*=\s*-?[\d./]+"
                            r"\s*", ans)
        if _m25:
            # The served variable IS the direct ask
            # ("find the value of k for which the points
            # ... are collinear" -> "k = 6", Wave 55's
            # collinearity serve; "find the value of p:
            # x: 10, 20, ..." -> "p = 5", Wave 33's mean
            # serve) — the asked unknown, not an
            # intermediate. The variable must stand
            # alone right after "value of" (a colon,
            # comma, end, or a for/when/if/such/that
            # clause): a compound target ("value of
            # 14p - 19 and ...") does not exempt.
            if not re.search(
                    r"find\s+the\s+value\s+of\s+"
                    + _m25.group(1)
                    + r"(?:\s*[:,]|\s+(?:for|when|if|such|"
                    r"that)\b|\s*$)",
                    ql):
                return True
    return False


def _with_figure(question, result):
    """Wave 86: attach the labelled diagram (figures.py) to a
    real mensuration solve — only when the shape and its
    dimensions are unambiguous in the question AND the
    figure's numbers reproduce the solved answer. Anything
    else returns the result untouched (byte-identical). The
    result is copied before the key is added: the router's
    positive answer cache hands out shared dicts, and they
    must never gain keys.

    Wave 128: when figures.py has no diagram, graphs.py
    gets the same chance for the picture the student
    actually asked for — a matplotlib plot result rebuilt
    as a verified SVG, a number line for an inequality
    solve, a points plot for a coordinate solve — under
    the same cross-check discipline (graphs.py's module
    docstring). When the SVG replaces a plot result, the
    matplotlib "image" key is dropped from the copy: the
    card shows ONE graph, not two."""
    try:
        from figures import figure_for
        fig = figure_for(question, result)
    except Exception:
        fig = None
    if fig is None:
        try:
            from graphs import graph_figure_for
            fig = graph_figure_for(question, result)
        except Exception:
            fig = None
    if fig is None:
        return result
    out = dict(result)
    out["figure"] = fig
    if out.get("op") == "graph":
        out.pop("image", None)
    return out


# ---------------------------------------------------------------------------
# Layer 0: greetings & small talk; Layer 0b: known non-maths topics
# ---------------------------------------------------------------------------

_GREETING_EXACT = {
    "hi", "hii", "hiii", "hello", "helo", "hey", "namaste",
    "namaskar", "kaise ho", "how are you", "kese ho",
    "thank you", "thanks", "dhanyavaad", "dhanyavad", "shukriya",
    "tum kaun ho", "who are you", "your name", "tumhara naam",
    "tumhara naam kya hai", "good morning", "good evening",
    "good afternoon", "good night", "bye", "ok", "okay",
    "haan", "yes", "no", "nahi",
    # Wave 68: Devanagari small talk — "नमस्ते" alone used to
    # fall through to the long guide card because the exact
    # set only knew the Roman spellings.
    "नमस्ते", "नमस्कार", "हेलो", "हाय", "धन्यवाद", "शुक्रिया",
    "कैसे हो", "कैसे हो आप", "तुम कौन हो", "तुम्हारा नाम",
    "तुम्हारा नाम क्या है", "अलविदा", "शुभ प्रभात",
    "शुभ रात्रि", "हाँ", "नहीं", "ठीक है",
}

_GREETING_STARTS = ("hello", "hi ", "hey ", "namaste", "good morning",
                    "good evening", "good afternoon", "thank you",
                    "thanks", "kaise ho", "how are you",
                    "नमस्ते", "नमस्कार", "धन्यवाद", "शुक्रिया",
                    "कैसे हो", "शुभ प्रभात")

_HINDI_MARKERS = ("kya", "hai", "ho", "kaise", "tum", "mera",
                  "ka", "ki", "batao", "samjhao", "dhanyavaad",
                  "shukriya", "nahi", "haan", "namaste", "ganit")


def _looks_hindi(question):
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return True
    words = set(re.findall(r"[a-z]+", q.lower()))
    return bool(words & set(_HINDI_MARKERS))


# Extra Roman-Hindi markers used ONLY for flavour choice:
# _HINDI_MARKERS misses everyday Hinglish words like "kuch",
# "bata", "sawal", "kitna" — "kuch bhi bata do" read as
# English and got the English reply line.
_FLAVOUR_MARKERS = set(_HINDI_MARKERS) | {
    "kuch", "bata", "chahiye", "sawal", "jawab", "kitna",
    "kitne", "kitni", "wala", "wali", "mujhe", "hain",
    "dunga", "hoga", "hogi", "raha", "rahi", "mera", "mere",
}


def _flavour(question):
    """Wave 68: the script flavour of a question — "dev"
    (Devanagari Hindi), "roman" (Hinglish in Latin letters)
    or "en". The friendly one-line replies (greeting,
    maths-only guard, not-found) are written per flavour, so
    a Devanagari question no longer gets a Roman-Hindi reply
    (the mixed-language mess Suraj flagged on 15 Nov 2026)
    and a Hinglish question gets Hinglish back."""
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return "dev"
    if _looks_hindi(q):
        return "roman"
    words = set(re.findall(r"[a-z]+", q.lower()))
    return "roman" if words & _FLAVOUR_MARKERS else "en"


def _greeting_kind(question):
    """Return a greeting key when the WHOLE message (short, no
    digits, no operators) is small talk, else None. A greeting
    glued to a real question ("hello, solve 2+2") is NOT small
    talk — the salvage layer handles those."""
    q = str(question or "").strip().lower()
    q = re.sub(r"[!?.,;:\"।]+", "", q).strip()
    if not q or any(ch.isdigit() for ch in q):
        return None
    if any(ch in q for ch in "+-*/^=<>%"):
        return None
    if len(q.split()) > 5:
        return None
    if q in _GREETING_EXACT:
        return q
    for start in _GREETING_STARTS:
        if q.startswith(start):
            return start.strip()
    return None


_NONMATHS_KEYWORDS = (
    "capital of", "capital kya", "rajdhaani", "prime minister",
    "pradhan mantri", "president of", "cricket", "football",
    "movie", "film", "song", "gaana", "weather", "mausam",
    "photosynthesis", "prakash sanshleshan", "sky blue",
    "aasmaan neela", "news", "khabar", "meaning of love",
    "girlfriend", "boyfriend", "joke", "chutkula",
    "who won", "match ka score", "score kya",
    # Wave 68: the same topics in Devanagari — "भारत की
    # राजधानी क्या है?" used to miss every Roman keyword and
    # land on the long guide card.
    "राजधानी", "प्रधानमंत्री", "प्रधान मंत्री", "राष्ट्रपति",
    "मौसम", "फ़िल्म", "फिल्म", "गाना", "चुटकुला",
    "मैच का स्कोर",
)


def _is_nonmaths(question):
    q = str(question or "").lower()
    if any(ch.isdigit() for ch in q) and any(
            ch in q for ch in "+-*/^=%"):
        return False  # an actual calculation rides along; not ours
    # Wave 56: set-counting word problems legitimately talk
    # about games — "30 play cricket and 25 play football.
    # If 12 play both, how many play neither?" is a Class
    # 10 sets question with real numbers, not a sports
    # question. The counting shape (digits + play
    # both/neither, or the power-set ask) is maths.
    if any(ch.isdigit() for ch in q) and (
            "play both" in q or "play neither" in q
            or "power set" in q):
        return False
    # Wave 59: Hinglish story dressing — sets/ages/geometry
    # word problems mention cricket or football as scene
    # colour ("30 ladke cricket khelte hain... dono khelte
    # hain, kitne ladke?", a brother who "cricket khelta
    # hai" in an ages story, a sphere described as a
    # football). Digits + a quantitative ask + a maths
    # context word is a maths question, not sports chat.
    if any(ch.isdigit() for ch in q) and (
            "kitna" in q or "kitne" in q or "kitni" in q
            or "how many" in q or "how much" in q
            or "कितना" in q or "कितने" in q or "कितनी" in q) and any(
            w in q for w in (
                "dono", "khelte", "khelta", "umar", "yog",
                "antar", "trijya", "volume", "kshetrafal",
                "paridhi", "doori", "unchai", "anupat",
                "anupaat", "sambhavna", "probability",
                "ausat", "byaj", "speed", "train",
                # Wave 68: the same maths-context words in
                # Devanagari, so a Hindi sets/ages/geometry
                # story that merely mentions a game stays a
                # maths question.
                "दोनों", "खेलते", "खेलता", "उम्र", "योग",
                "अंतर", "त्रिज्या", "आयतन", "क्षेत्रफल",
                "परिधि", "दूरी", "ऊँचाई", "अनुपात",
                "संभावना", "औसत", "ब्याज", "चाल")):
        return False
    # Wave 146: arranging the LETTERS OF A WORD is maths even
    # when the word itself is a non-maths keyword — "The
    # letters of the word 'CRICKET' are written in all
    # possible orders" and "the rank of the word CRICKET in a
    # dictionary" are permutation questions, and both were
    # refused as non-maths in the CISCE audit. The exemption
    # needs the arrangement frame, so "who won the cricket
    # match" stays non-maths.
    if "letters of the word" in q or "letters in the word" in q \
            or "शब्द के अक्षर" in q \
            or re.search(r"(?:rank|dictionary)\s+of\s+the\s+word",
                         q) \
            or re.search(r"\bword\b[^.]{0,30}\b(?:arrang\w*|"
                         r"permut\w*|dictionary|rank)\b", q):
        return False
    return any(kw in q for kw in _NONMATHS_KEYWORDS)


def _friendly_result(kind, answer, steps, hindi):
    return {
        "type": "Ganitra",
        "op": kind,
        "answer": answer,
        "steps": steps,
        "fallback": True,
        "fallback_kind": kind,
    }


def _plain_result(kind, answer, hindi, steps=None):
    """Wave 68: a PLAIN reply — the chat renders it as one
    simple bubble line (plus any guidance lines in `steps` as
    quiet sub-lines), never as an answer card with a badge,
    steps panel, advice or icon row. Suraj's rule (15 Nov
    2026): greetings, the maths-only guard, gibberish and
    unsolved questions get ONE short line, nothing more.
    `plain_reply` is the sentinel the chat renderer keys on;
    the classic pages render the same text plainly too.
    Merge-5: the result ALSO carries Wave 67's `plain` flag,
    so both waves' renderers and i18n gates (result_is_plain)
    treat it as the same one-line reply."""
    result = _friendly_result(kind, answer, steps or [], hindi)
    result["plain_reply"] = True
    result["plain"] = True
    return result


# ---------------------------------------------------------------------------
# Wave 67: the one-line not-found answer
# ---------------------------------------------------------------------------

_HINGLISH_NOT_FOUND = "Answer nahi mila."


def _not_found_line(question, hindi, lang=None, lang_request=None):
    """The not-found line in the question's own language:
    Devanagari question -> Hindi (Marathi UI keeps its own
    line), Roman Hinglish -> "Answer nahi mila.", a bn/mr/ta/te
    UI language -> its i18n line, otherwise English. The
    Devanagari/Hinglish wording is Suraj's spec verbatim; the
    rest ride the i18n "answer_not_found" key.

    Wave 107: an explicit language request in the message
    (lang_request: "hi" / "en" / "hinglish") outranks the
    question's own language here exactly as it does for the
    answer itself."""
    if lang_request == "hi":
        return get_strings("hi")["answer_not_found"]
    if lang_request == "hinglish":
        return _HINGLISH_NOT_FOUND
    if lang_request == "en":
        return get_strings("en")["answer_not_found"]
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        if lang == "mr":
            return get_strings("mr")["answer_not_found"]
        return get_strings("hi")["answer_not_found"]
    if hindi:
        return _HINGLISH_NOT_FOUND
    if lang in ("bn", "mr", "ta", "te"):
        return get_strings(lang)["answer_not_found"]
    if lang == "hi":
        return _HINGLISH_NOT_FOUND
    return get_strings("en")["answer_not_found"]


def _not_found_result(question, hindi, lang=None, lang_request=None):
    """The ONLY answer to anything that was not solved: one
    short line, no steps, nothing else. fallback_kind ==
    "not_found" is the sentinel every renderer gates on (the
    chat shows a plain minimal bubble; i18n gives it no
    explanation / advice / teach lines)."""
    return {
        "type": "Ganitra",
        "op": "not_found",
        "answer": _not_found_line(question, hindi, lang,
                                  lang_request),
        "steps": [],
        "fallback": True,
        "fallback_kind": "not_found",
        # Merge-5: Wave 68's chat renderer keys on plain_reply,
        # Wave 67's on plain / the not_found kind — carry both
        # flags so the one line renders plainly everywhere.
        "plain": True,
        "plain_reply": True,
    }


_GREETING_LINES = {
    "default": {
        "en": "Hello! 😊 I'm doing great. Send me a maths "
              "question and I'll solve it step by step.",
        "roman": "Namaste! 😊 Main bilkul theek hoon. Apna "
                 "maths ka sawal bhejo — main step-by-step "
                 "hal dunga.",
        "dev": "नमस्ते! 😊 मैं बिल्कुल ठीक हूँ। अपना गणित का "
               "सवाल भेजिए — मैं चरण-दर-चरण हल दूँगा।",
    },
    "thanks": {
        "en": "You're welcome! 😊 Send me another maths "
              "question any time.",
        "roman": "Koi baat nahi! 😊 Kuch aur maths ka sawal "
                 "ho to bhejo.",
        "dev": "कोई बात नहीं! 😊 और कोई गणित का सवाल हो तो "
               "भेजिए।",
    },
    "who": {
        "en": "I'm Ganitra — your maths friend. Type or "
              "photograph any maths question and I'll solve "
              "it step by step.",
        "roman": "Main Ganitra hoon — tumhara maths dost. "
                 "Koi bhi ganit ka sawal likho ya photo bhejo, "
                 "main step-by-step hal dunga.",
        "dev": "मैं Ganitra हूँ — आपका गणित दोस्त। कोई भी "
               "गणित का सवाल लिखिए या फ़ोटो भेजिए, मैं "
               "चरण-दर-चरण हल दूँगा।",
    },
    "bye": {
        "en": "Bye! 👋 Whenever maths gets stuck, I'm right "
              "here.",
        "roman": "Bye! 👋 Jab bhi maths me atak jao, main "
                 "yahi hoon.",
        "dev": "अलविदा! 👋 जब भी गणित में अटकें, मैं यहीं हूँ।",
    },
}


def _greeting_result(question, hindi, flavour=None):
    # Merge-5 (decided rule 1): a greeting gets Wave 68's
    # friendly per-flavour ONE line with plain rendering —
    # NOT Wave 67's "Answer not found." (a friendly hello
    # deserves a friendly line).
    g = _greeting_kind(question)
    if g is None:
        return None
    if flavour is None:
        flavour = _flavour(question)
    if g in ("thank you", "thanks", "dhanyavaad", "dhanyavad",
             "shukriya", "धन्यवाद", "शुक्रिया"):
        group = "thanks"
    elif g in ("tum kaun ho", "who are you", "your name",
               "tumhara naam", "tumhara naam kya hai",
               "तुम कौन हो", "तुम्हारा नाम",
               "तुम्हारा नाम क्या है"):
        group = "who"
    elif g in ("bye", "अलविदा"):
        group = "bye"
    else:
        group = "default"
    return _plain_result(
        "greeting", _GREETING_LINES[group][flavour], hindi)


_NONMATHS_LINES = {
    # Merge-5 (decided rule 3): ONE guard line in the
    # question's own flavour, plain rendering (Wave 68
    # behaviour, Wave 67's plain flag preserved via
    # _plain_result). The en/roman texts are Wave 67's
    # trimmed guard sentences verbatim (pinned by
    # test_wave67); the Devanagari line is Wave 68's, so a
    # Hindi question gets a Hindi guard line.
    "en": "That's not a maths question — Ganitra only "
          "solves Maths.",
    "roman": "Ye sawal maths ka nahi hai — Ganitra sirf Maths "
             "ke sawal hal karta hai।",
    "dev": "यह सवाल गणित का नहीं है — मैं सिर्फ़ गणित के "
           "सवाल हल करता हूँ। 😊 कोई गणित का सवाल भेजिए, "
           "चरण-दर-चरण हल दूँगा।",
}


def _nonmaths_result(question, hindi, flavour=None):
    if flavour is None:
        flavour = _flavour(question)
    return _plain_result(
        "nonmaths", _NONMATHS_LINES[flavour], hindi)


# ---------------------------------------------------------------------------
# Layer 0c (Wave 20, Suraj 12 Nov 2026): SCIENCE questions. A
# Physics/Chemistry/Biology question must get an honest
# "Ganitra is for Maths" reply plus the concept's formula as
# GUIDANCE — never a force-solved fake answer. (The reported
# case: a refractive-index question was salvaged into the
# fragment "2 x 10" from "2 x 10^8" and answered by the junior
# times-pair solver.) This layer runs only when the solver did
# NOT really answer, so genuine maths that merely mentions a
# science word (a calculus velocity problem the solver solves
# properly) is never disturbed.
# ---------------------------------------------------------------------------

def _science_result(question, hindi, flavour=None):
    # Merge-5: Wave 68's per-flavour version, kept as-is;
    # _plain_result now also sets Wave 67's `plain` flag,
    # so the guard renders plainly under both waves.
    # Wave 68: the topic line now comes in the question's own
    # script (a Devanagari Physics question used to get the
    # Roman-Hindi line), and the result is a PLAIN reply: the
    # guard line plus the formula guidance as quiet sub-lines
    # — no answer card, no extra invitation step (the guard
    # line already says what Ganitra does). The guidance
    # content itself is Wave 20's, unchanged.
    q = str(question or "").lower()
    if flavour is None:
        flavour = _flavour(question)
    if "refractive" in q or "speed of light" in q \
            or "ray of light" in q or "light ray" in q:
        steps = [
            "Formula (guidance): refractive index of B with "
            "respect to A, n = (speed of light in A) ÷ "
            "(speed of light in B).",
            "So speed in B = (speed in A) ÷ n — put your values "
            "into this formula and the Physics answer follows.",
        ]
        topic_line = {
            "en": "This is a Physics (Light / Optics) "
                  "question — Ganitra only solves Maths, "
                  "so I won't fake an answer for it. 😊",
            "roman": "Ye Physics (Prakash / Optics) ka sawal "
                     "hai — Ganitra sirf Maths ke sawal hal "
                     "karta hai, isliye main iska nakli hal "
                     "nahi dunga. 😊",
            "dev": "यह Physics (प्रकाश / Optics) का सवाल है — "
                   "Ganitra सिर्फ़ Maths के सवाल हल करता है, "
                   "इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    elif any(w in q for w in ("velocity", "acceleration", "force",
                              "newton", "momentum", "friction",
                              "gravity", "kinetic energy",
                              "potential energy")):
        steps = [
            "Useful formulas (guidance): speed v = distance ÷ "
            "time; acceleration a = (v − u) ÷ t; force F = "
            "mass × acceleration.",
        ]
        topic_line = {
            "en": "This is a Physics (Motion / Force) "
                  "question — Ganitra only solves Maths, "
                  "so I won't fake an answer for it. 😊",
            "roman": "Ye Physics (Gati / Bal) ka sawal hai "
                     "— Ganitra sirf Maths ke sawal hal "
                     "karta hai, isliye main iska nakli hal "
                     "nahi dunga. 😊",
            "dev": "यह Physics (गति / बल) का सवाल है — "
                   "Ganitra सिर्फ़ Maths के सवाल हल करता है, "
                   "इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    elif any(w in q for w in ("voltage", "ampere", "resistance",
                              "ohm", "electric current", "circuit",
                              "capacitor")):
        steps = [
            "Useful formula (guidance): Ohm's law — V = I × R "
            "(voltage = current × resistance).",
        ]
        topic_line = {
            "en": "This is a Physics (Electricity) question "
                  "— Ganitra only solves Maths, so I won't "
                  "fake an answer for it. 😊",
            "roman": "Ye Physics (Bijli / Electricity) ka "
                     "sawal hai — Ganitra sirf Maths ke sawal "
                     "hal karta hai, isliye main iska nakli "
                     "hal nahi dunga. 😊",
            "dev": "यह Physics (बिजली / Electricity) का सवाल "
                   "है — Ganitra सिर्फ़ Maths के सवाल हल करता "
                   "है, इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    else:
        steps = []
        topic_line = {
            "en": "This is a Science question — Ganitra "
                  "only solves Maths, so I won't fake an "
                  "answer for it. 😊",
            "roman": "Ye Science ka sawal hai — Ganitra "
                     "sirf Maths ke sawal hal karta hai, "
                     "isliye main iska nakli hal nahi "
                     "dunga. 😊",
            "dev": "यह Science का सवाल है — Ganitra सिर्फ़ "
                   "Maths के सवाल हल करता है, इसलिए मैं इसका "
                   "नकली हल नहीं दूँगा। 😊",
        }[flavour]
    return _plain_result("science", topic_line, hindi, steps)


# ---------------------------------------------------------------------------
# Layer 1: salvage — strip the chatter, solve the maths inside
# ---------------------------------------------------------------------------

_FILLER_WORDS = {
    "please", "plz", "batao", "bata", "samjhao", "samjha", "do",
    "karo", "kar", "nikalo", "help", "me", "my", "homework",
    "says", "say", "question", "sawal", "wala", "wali", "hai",
    "kitna", "kitne", "hoga", "hoge", "chahiye", "mujhe", "mera",
    "mere", "find", "the", "value", "what", "is", "when", "tell",
    "usko", "isko", "yeh", "ye", "aur", "ka", "ki", "ke", "ko",
    "se", "me", "mein", "par", "bhi", "toh", "to", "a", "an",
    "of", "for", "solve", "this", "that", "it", "just", "can",
    "you", "could", "would", "dear", "teacher", "sir", "madam",
    "bhai", "bro", "yar", "yaar", "abhi", "jaldi", "zara",
    "thoda", "answer", "ans", "solution", "hal",
}


def _strip_filler(question):
    tokens = re.findall(r"[^\s]+", str(question or ""))
    kept = [t for t in tokens
            if t.strip(".,?!;:\"'").lower() not in _FILLER_WORDS]
    return " ".join(kept).strip(" .,?!;:")


_MATHY_TOKEN = re.compile(r"^[0-9a-zA-Z\.\+\-\*/\^\(\)%]+$")


def _mathy(token):
    """A token that can belong to an equation: only maths
    characters, and either it carries a digit, is an operator,
    or is a short symbol (x, x^2, 3x). Plain English/Hindi words
    ("when", "please", "batao") are never mathy — they bound the
    extraction."""
    t = token.strip(".,?!;:\"'")
    if not t or not _MATHY_TOKEN.match(t):
        return False
    if any(ch.isdigit() for ch in t):
        return True
    if t in ("+", "-", "*", "/", "=", "^", "(", ")", "x", "×"):
        return True
    return len(t) <= 3 and not t.isalpha() or (
        len(t) <= 3 and t.lower() in ("x", "y", "z", "a", "b"))


def _extract_equation(question):
    """Find "3x + 7 = 22" inside "my homework says find x when
    3x + 7 = 22 please batao": locate the '=' and expand token
    by token while the neighbours are mathy."""
    tokens = str(question or "").split()
    for i, tok in enumerate(tokens):
        if "=" not in tok:
            continue
        lo = i
        while lo > 0 and _mathy(tokens[lo - 1]):
            lo -= 1
        hi = i
        while hi < len(tokens) - 1 and _mathy(tokens[hi + 1]):
            hi += 1
        cand = " ".join(tokens[lo:hi + 1]).strip(" .,?!;:")
        if any(ch.isdigit() for ch in cand) and \
                any(ch.isalpha() for ch in cand.split("=")[0]):
            return cand
    return None


def _candidates(question):
    """Possible maths cores inside a messy question, most
    specific first: an equation, a percentage, an arithmetic
    chain (only when there is no equation — a chain inside an
    equation is a fragment, not the question), then the
    filler-stripped whole."""
    q = str(question or "")
    out = []

    def add(cand):
        cand = (cand or "").strip(" .,?!;:")
        if cand and cand not in out and any(ch.isdigit()
                                            for ch in cand):
            out.append(cand)

    equation = _extract_equation(q)
    if equation:
        add(equation)
    m = re.search(r"(\d+(?:\.\d+)?\s*%\s*of\s*\d+(?:\.\d+)?)", q,
                  re.I)
    if m:
        add(m.group(1))
    if not equation:
        for m in re.finditer(
                r"(\d+(?:\.\d+)?(?:\s*[-+\*/x×]\s*"
                r"\d+(?:\.\d+)?)+)", q):
            # Wave 20: a chain that runs straight into a "^" is
            # scientific notation, not a multiplication sum —
            # "2 x 10^8" must never be salvaged as "2 x 10".
            if q[m.end():].lstrip().startswith("^"):
                continue
            add(m.group(1))
    add(_strip_filler(q))
    return out


_FRAC52 = r"\d+\s*/\s*\d+"


def _fraction_ask_value(question):
    """Wave 52 (audit #15): the exact value a two-fraction
    Add/Subtract question asks for, or None. Salvage used to
    "solve" these by solving ONE operand — 'Add 2/3 and 3/4'
    came back as '2/3', the first fraction echoed (31 of 52
    salvage answers in the Wave 35 audit carried a wrong
    value, and the fraction echo was the flagship case). The
    primary solver owns these asks now (solver/arithmetic.py);
    this is the salvage-side guard for any phrasing variant
    that still slips past it: a salvaged result for such a
    question is only believable if its value IS the sum /
    difference."""
    from fractions import Fraction
    q = str(question or "").lower()
    fracs = re.findall(_FRAC52, q)
    if len(fracs) < 2:
        return None
    first = Fraction(fracs[0].replace(" ", ""))
    second = Fraction(fracs[1].replace(" ", ""))
    if re.search(r"\bsubtract\b", q):
        # "Subtract A from B": the first fraction named is
        # the one taken away.
        return second - first
    if re.search(r"\badd\b|\bsum\b", q):
        return first + second
    return None


def _result_value(result):
    """Best-effort numeric value of a result's answer: the
    structured value/numeric fields first, then a fraction
    or decimal read out of the answer text."""
    for key in ("value", "numeric"):
        v = (result or {}).get(key)
        if isinstance(v, (int, float)):
            return float(v)
    ans = _answer_text(result)
    m = re.search(r"(-?\d+)\s*/\s*(\d+)", ans)
    if m and int(m.group(2)):
        return int(m.group(1)) / int(m.group(2))
    m = re.search(r"-?\d+(?:\.\d+)?", ans)
    return float(m.group(0)) if m else None


def _fraction_echo(question, result):
    """Wave 58 guard: for a two-fraction add/subtract ASK, a
    salvaged answer that merely repeats one of the OPERANDS
    (and is not the asked sum/difference) is an echo, never a
    solution — reject the candidate. With the primary word
    patterns in arithmetic.py this is defence in depth for
    rewordings they do not cover."""
    ql = str(question).lower()
    if not re.search(r"\b(add|subtract|sum|difference|plus|"
                     r"minus)\b", ql):
        return False
    fr = []
    for a, b in re.findall(r"(\d+)\s*/\s*(\d+)", str(question)):
        if int(b) != 0:
            fr.append(Fraction(int(a), int(b)))
    if len(fr) != 2:
        return False
    val = result.get("numeric", result.get("value"))
    if isinstance(val, (list, tuple)):
        return False
    if val is None:
        m = re.match(r"\s*(-?\d+)\s*/\s*(\d+)\s*$",
                     str(result.get("answer", "")))
        if m:
            val = Fraction(int(m.group(1)), int(m.group(2)))
        else:
            try:
                val = Fraction(
                    str(result.get("answer", "")).strip())
            except Exception:
                return False
    try:
        fv = Fraction(val).limit_denominator(10 ** 6)
    except Exception:
        return False
    if fv in (fr[0] + fr[1], fr[0] - fr[1], fr[1] - fr[0]):
        return False
    return fv in fr


def _salvage(question, hindi):
    # Wave 20: never salvage a science question — its numbers
    # are not a maths sum hiding in the text (see Layer 0c).
    if has_science_signal(question):
        return None
    _want52 = _fraction_ask_value(question)
    for cand in _candidates(question):
        if cand.strip().lower() == str(question).strip().lower():
            continue  # identical to the original: already failed
        try:
            result = solve_question(cand)
        except Exception:
            continue
        if _is_real(cand, result):
            if _want52 is not None:
                _got52 = _result_value(result)
                if _got52 is None or abs(
                        _got52 - float(_want52)) > 0.01:
                    continue  # an echoed operand, not the answer
            note = (f"Solved the maths part of your question: "
                    f"{cand}")
            result = dict(result)
            result["steps"] = [note] + list(
                result.get("steps") or [])
            result["fallback"] = True
            result["fallback_kind"] = "salvage"
            result["salvaged_from"] = cand
            return result
    return None


# ---------------------------------------------------------------------------
# Layer 2: concepts
# ---------------------------------------------------------------------------

def _concept_result(question, hindi):
    entry = find_concept(question)
    if entry is None:
        # Wave 57: retry on the spelling-folded text — students
        # ask "byaj kaise nikalte hai?" / "ausat kaise nikale?"
        # with spellings the keyword lists are not written in.
        folded = normalize_spelling(question)
        if folded != question:
            entry = find_concept(folded)
    if entry is None:
        return None
    ex = entry["example"]
    steps = [entry["explain"],
             f"Hinglish me: {entry['hinglish']}",
             f"Example: {ex['q']}"]
    steps.extend(ex["steps"])
    steps.append(f"Example answer: {ex['answer']}")
    return {
        "type": "Concept",
        "op": entry["id"],
        "answer": f"{entry['title']} — {entry['formula']}",
        "steps": steps,
        "fallback": True,
        "fallback_kind": "concept",
        "concept_id": entry["id"],
    }


# ---------------------------------------------------------------------------
# Layer 3: topic guess + a similar SOLVED example (honestly labelled)
# ---------------------------------------------------------------------------

_TOPIC_EXAMPLES = (
    (("train", "speed", "chaal", "distance", "doori", "yatra",
      "km/h", "kmh"),
     "Speed–Distance",
     "A train travels at 60 km/h for 2 hours. How far does it go?",
     "60 km/h for 2 hours"),
    (("interest", "byaj", "ब्याज", "bank"),
     "Simple Interest",
     "Find the simple interest on ₹1,000 at 5% for 2 years.",
     "simple interest on 1000 at 5% for 2 years"),
    (("percent", "%", "pratishat", "प्रतिशत", "discount"),
     "Percentage",
     "Find 15% of 240.",
     "15% of 240"),
    (("quadratic", "x^2", "x²"),
     "Quadratic Equations",
     "Solve x² - 7x + 12 = 0.",
     "x^2 - 7x + 12 = 0"),
    (("equation", "find x", "solve x", "samikaran"),
     "Equations",
     "Solve 2x + 3 = 11.",
     "2x + 3 = 11"),
    (("area", "kshetrafal", "क्षेत्रफल", "perimeter", "parimap"),
     "Area",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
    (("sin", "cos", "tan", "trig"),
     "Trigonometry",
     "Find the value of sin 30.",
     "sin 30"),
    (("mean", "average", "ausat", "median"),
     "Statistics",
     "Find the mean of 3, 6, 9, 12.",
     "mean of 3, 6, 9, 12"),
    (("rupee", "rupaye", "रुपये", "money", "paisa", "paise",
      "cost", "price", "keemat"),
     "Money Maths",
     "Find 15% of ₹200.",
     "15% of 200"),
    (("triangle", "tribhuj", "त्रिभुज"),
     "Triangles",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
)


def _similar_result(question, hindi):
    # Wave 57: match topic keywords against the original text AND
    # its spelling-folded form ("tren wala sawal" -> train topic).
    q = (str(question or "") + " "
         + normalize_spelling(question)).lower()
    for keywords, label, example_q, example_solve in _TOPIC_EXAMPLES:
        if any(kw in q for kw in keywords):
            try:
                solved = solve_question(example_solve)
            except Exception:
                solved = None
            if solved is not None and _is_real(example_solve,
                                               solved):
                if hindi:
                    head = ("Tumhare sawal ka exact hal abhi nahi "
                            "mila, lekin usi topic ka ek solved "
                            "example ye raha:")
                    ask = ("Apne sawal ki exact sankhyayen (numbers) "
                           "ek baar saaf-saaf likh kar bhejo, main "
                           "usi ka hal dunga.")
                else:
                    head = ("I couldn't solve your exact question "
                            "yet, but here is a solved example from "
                            "the same topic:")
                    ask = ("Now type your question once more with "
                           "its exact numbers, and I'll solve yours.")
                steps = [head, f"Similar example: {example_q}"]
                steps.extend(
                    str(s) for s in (solved.get("steps") or []))
                steps.append(ask)
                return {
                    "type": "Similar example",
                    "op": label,
                    "answer": (f"Similar example ({label}): "
                               f"{solved.get('answer', '')}"),
                    "steps": steps,
                    "fallback": True,
                    "fallback_kind": "similar",
                }
    return None


# ---------------------------------------------------------------------------
# Layer 4: vague asks, gibberish, and the general guide
# ---------------------------------------------------------------------------

_VAGUE_WORDS = {
    "samjhao", "samjha", "batao", "bata", "solve", "help",
    "explain", "ye", "yeh", "wala", "wali", "this", "that",
    "isko", "usko", "karo", "kar", "do", "please", "plz",
    "maths", "math", "ganit", "question", "sawal", "abhi",
    "kuch", "bhi", "ek", "the", "a", "an", "it", "me", "my",
}


_VAGUE_WORDS_DEV = {
    "समझाओ", "समझा", "बताओ", "बता", "बताइए", "हल", "करो",
    "कर", "दो", "कुछ", "भी", "एक", "गणित", "सवाल", "यह",
    "ये", "वाला", "वाली", "इसको", "उसको", "अभी", "कृपया",
    "मदद",
}


def _is_vague(question):
    words = re.findall(r"[a-z]+", str(question or "").lower())
    if words:
        if len(words) > 6:
            return False
        if any(ch.isdigit() for ch in str(question or "")):
            return False
        return all(w in _VAGUE_WORDS for w in words)
    # Wave 68: the same test for Devanagari asks — "समझाओ"
    # alone used to fall to the not-found line instead of
    # the friendly send-your-question reply.
    dev_words = re.findall(r"[ऀ-ॿ]+", str(question or ""))
    if not dev_words or len(dev_words) > 6:
        return False
    if any(ch.isdigit() for ch in str(question or "")):
        return False
    return all(w in _VAGUE_WORDS_DEV for w in dev_words)


_KNOWN_WORDS = _VAGUE_WORDS | _FILLER_WORDS | {
    "what", "is", "of", "the", "a", "an", "in", "on", "for",
    "and", "or", "to", "how", "why", "when", "which", "find",
    "value", "area", "volume", "radius", "circle", "square",
    "triangle", "rectangle", "angle", "degree", "degrees",
    "percent", "percentage", "probability", "derivative",
    "integral", "integrate", "limit", "equation", "root",
    "roots", "power", "cube", "prime", "factor", "factors",
    "expand", "simplify", "graph", "plot", "sin", "cos", "tan",
    "log", "mean", "mode", "median", "hcf", "lcm", "gcd",
    "theorem", "formula", "interest", "speed", "distance",
    "time", "number", "numbers", "sum", "product", "difference",
}


def _is_gibberish(question):
    q = str(question or "")
    if any(ch.isdigit() for ch in q):
        return False
    if any(ch in q for ch in "+-*/^=<>%"):
        return False
    words = [w for w in re.findall(r"[a-z]+", q.lower())
             if len(w) >= 3]
    if len(words) < 2:
        return False
    unknown = [w for w in words if w not in _KNOWN_WORDS]
    return len(unknown) >= 2 and len(unknown) == len(words)


# Wave 68 (Suraj, 15 Nov 2026 — the rule Wave 67 also
# implements): when nothing solved, the reply is ONE short
# line in the question's own language/script. No guide card,
# no "questions I solve for sure" panel, no tips, no advice.
_NOT_FOUND_LINES = {
    "en": "Answer not found.",
    "roman": "Answer nahi mila.",
    "dev": "उत्तर नहीं मिला।",
}

_VAGUE_LINES = {
    "en": "Of course! 😊 Just send me your full maths "
          "question — like 'solve 2x + 3 = 7' — and I'll "
          "solve it step by step.",
    "roman": "Bilkul! 😊 Apna maths ka sawal poora likh kar "
             "bhejo — jaise 'solve 2x + 3 = 7' — main "
             "step-by-step hal dunga.",
    "dev": "बिल्कुल! 😊 अपना गणित का सवाल पूरा लिखकर भेजिए "
           "— जैसे '2x + 3 = 7 हल कीजिए' — मैं चरण-दर-चरण "
           "हल दूँगा।",
}


def _guide_result(question, hindi, kind, flavour=None):
    if flavour is None:
        flavour = _flavour(question)
    if kind == "vague":
        return _plain_result(
            "vague", _VAGUE_LINES[flavour], hindi)
    # "gibberish" (letter-soup / jumbled words) and "guide"
    # (a real question nothing could solve — the AI brains
    # above get their chance first, since kind "guide" is in
    # _GEMINI_KINDS and this result is only settled when they
    # return None): both are the same honest one-liner. The
    # fallback_kind is preserved for analytics/tests; the
    # content is the Wave 67/68 not-found line.
    return _plain_result(
        kind, _NOT_FOUND_LINES[flavour], hindi)


# ---------------------------------------------------------------------------
# Wave 37: the Gemini free-tier second brain (gemini_fallback.py)
# Wave 41: Groq (groq_fallback.py) joins as the second brain —
# consulted only when Gemini returned None.
# Wave 108: OpenRouter (openrouter_fallback.py) joins as the
# third brain — consulted only when Gemini AND Groq both
# returned None.
# ---------------------------------------------------------------------------

# The fallback kinds that mean "the student's OWN question is
# still unanswered": a similar example, a concept card, or the
# general guide. Only these may be upgraded by an AI brain.
# Real solver answers, salvage solves, greetings, non-maths
# and science replies never reach the check at all (they
# return earlier), and vague/gibberish asks have no real
# question to send.
_GEMINI_KINDS = ("similar", "concept", "guide")


def _ai_lang(hindi, lang_request):
    """The language instruction handed to the AI brains: a
    Wave-107 explicit request verbatim ("en" / "hi" /
    "hinglish"), else the pre-Wave-107 rule — "hi" for a
    Hindi-looking question, None (the prompt's own
    same-language rule) otherwise."""
    if lang_request in ("en", "hi", "hinglish"):
        return lang_request
    return "hi" if hindi else None


def _gemini_answer(question, hindi, lang_request=None,
                   detail=False):
    """Ask Gemini for the student's own question. Lazy import
    so the module (and its env key) stays fully optional; ANY
    failure returns None and the honest Wave-18 fallback is
    served exactly as before. `detail` (Wave 136) selects the
    prompt's DETAIL variant for an explicit long-answer
    request."""
    try:
        from gemini_fallback import try_gemini_answer
        return try_gemini_answer(question,
                                 _ai_lang(hindi, lang_request),
                                 detail=detail)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wave 39: the Verified Data Bank (bank.py) — exact matches only
# ---------------------------------------------------------------------------

def _bank_answer(question):
    """The banked, SymPy-verified answer for this EXACT question
    (bank.lookup_result), or None. Lazy import + blanket guard,
    same pattern as the Gemini layer: the bank snapshot is an
    optional file and any failure must leave the Wave-18 flow
    exactly as it was."""
    try:
        from bank import lookup_result
        return lookup_result(question)
    except Exception:
        return None


def _groq_answer(question, hindi, lang_request=None,
                 detail=False):
    """Wave 41: ask Groq for the student's own question —
    only ever called when Gemini returned None. Same contract
    as _gemini_answer: lazy import, ANY failure returns None
    and the honest Wave-18 fallback is served unchanged.
    `detail` (Wave 136) selects the prompt's DETAIL
    variant."""
    try:
        from groq_fallback import try_groq_answer
        return try_groq_answer(question,
                               _ai_lang(hindi, lang_request),
                               detail=detail)
    except Exception:
        return None


def _openrouter_answer(question, hindi, detail=False):
    """Wave 108: ask OpenRouter for the student's own
    question — only ever called when Gemini AND Groq both
    returned None. Same contract as _gemini_answer: lazy
    import, ANY failure returns None and the honest Wave-18
    fallback is served unchanged. `detail` (Wave 136)
    selects the prompt's DETAIL variant."""
    try:
        from openrouter_fallback import try_openrouter_answer
        return try_openrouter_answer(question,
                                     "hi" if hindi else None,
                                     detail=detail)
    except Exception:
        return None


def _verified_ai_answer(question, hindi, lang_request,
                        rejected_sink=None, detail=False):
    """Wave 133: the AI chain behind aiverify's verification
    gate ("jawab ki jaanch"). The three legs keep their
    Wave 37/41/108 order and contracts; what changed is that
    a leg's answer is no longer served on sight — aiverify
    first runs the sanity gate, then a deterministic check
    of the claimed final value against the question itself,
    then (only when no deterministic check applies) a
    cross-leg consensus. A candidate that fails is rejected
    and the next leg gets its chance; when nothing servable
    remains, this returns None and the chain falls through
    to the honest Wave 67 not-found, exactly as when every
    leg returned None before this wave.

    `rejected_sink` (a list, when the caller passes one)
    receives one {"question", "rejected"} bundle on total
    verification failure — the Wave 134 deep-solve seam (see
    the AI block in _with_fallback_chain). aiverify never
    raises by contract; if the module itself cannot be
    imported, the pre-Wave-133 chain runs unchanged (first
    leg answer wins) rather than losing the AI fallback to
    an import problem."""
    # Wave 136 (Deploy-27 merge): `detail` rides to the legs
    # ONLY as a keyword when it is on — with it off, the three
    # calls are byte-for-byte the pre-Wave-136 ones (older test
    # doubles for these seams take no detail argument).
    extra = {"detail": True} if detail else {}
    legs = [
        ("gemini", lambda: _gemini_answer(question, hindi,
                                          lang_request, **extra)),
        ("groq", lambda: _groq_answer(question, hindi,
                                      lang_request, **extra)),
        ("openrouter", lambda: _openrouter_answer(question,
                                                  hindi,
                                                  **extra)),
    ]

    def _seam(q, rejected):
        if rejected_sink is not None:
            rejected_sink.append({"question": q,
                                  "rejected": rejected})

    try:
        from aiverify import verify_chain
        return verify_chain(question, legs, on_rejected=_seam)
    except Exception:
        for _name, call in legs:
            try:
                result = call()
            except Exception:
                result = None
            if result is not None:
                return result
        return None


# ---------------------------------------------------------------------------
# The entry point
# Wave 90: the not-found learning log hook (notfound_log.py)
# ---------------------------------------------------------------------------

def _log_not_found(question, lang, student_class, terminal_kind):
    """Record a collapsed not-found outcome. Double-guarded:
    notfound_log.log_not_found never raises by contract, and
    this wrapper swallows even an import failure — logging is
    observational and must never slow, break or alter the
    answer. The recorded language is the explicit `lang` when
    the caller supplied one, else the question's own flavour
    mapped to a language label (dev -> hi, roman -> hinglish,
    en -> en)."""
    try:
        from notfound_log import log_not_found
        language = lang
        if not language:
            language = {"dev": "hi", "roman": "hinglish",
                        "en": "en"}[_flavour(question)]
        log_not_found(question, lang=language,
                      student_class=student_class,
                      terminal_kind=terminal_kind)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

def _honest_after_ai_miss(question, result_out, hindi, lang,
                          lang_request, student_class=None,
                          log=True):
    """The chain's ending when the AI legs could not answer
    (factored out in Wave 131 so the deferred-AI path can
    compute the identical outcome without serving it yet):
    a similar example, gibberish or the general guide means
    the student's OWN question was not solved, so the answer
    collapses to the one not-found line (Wave 67); anything
    else still standing — a concept card above all — is
    served as-is. `log` fires the Wave-90 not-found learning
    log; the deferred path passes log=False at defer time
    and logs later, only if this outcome is actually served
    (see log_deferred_not_found)."""
    if result_out.get("fallback_kind") in (
            "similar", "gibberish", "guide"):
        # Wave 90: this collapse is THE "Answer not found"
        # outcome — solver, bank, MCQ, salvage, concepts and
        # the AI chain all missed. Record it in the learning
        # log (observational only; the answer below is built
        # exactly as before, whether logging works or not).
        # Wave 107: a Hinglish request is logged as "hinglish"
        # (the session lang only knows it as "hi").
        if log:
            _log_not_found(
                question,
                "hinglish" if lang_request == "hinglish" else lang,
                student_class, result_out.get("fallback_kind"))
        return _not_found_result(question, hindi, lang,
                                 lang_request)
    return result_out


def log_deferred_not_found(question, deferred, lang=None,
                           student_class=None, lang_request=None):
    """Wave 131: a deferred-AI solve (see _with_fallback_chain's
    defer_ai) ended up serving the honest collapse — fire the
    Wave-90 log the classic chain would have fired at exactly
    this point, with the pre-collapse kind the marker kept.
    A deferred solve whose AI leg answered never reaches
    here, so an AI-answered question is never logged as
    not-found."""
    kind = (deferred or {}).get("ai_pre_collapse_kind")
    if kind in ("similar", "gibberish", "guide"):
        _log_not_found(
            question,
            "hinglish" if lang_request == "hinglish" else lang,
            student_class, kind)


def _with_fallback_chain(question, result, lang=None,
                         student_class=None, lang_request=None,
                         defer_ai=False, detail=False):
    """Return `result` unchanged when it is a real solver
    answer; otherwise return an honest fallback result (never
    None, never an error dict). `lang` is the app's UI /
    detected language (Wave 67: it picks the not-found line
    for the bn/mr/ta/te UIs; the line otherwise follows the
    question's own script/words). `student_class` (Wave 90)
    is the signed-in student's class when the caller knows
    it — used only by the not-found learning log.
    `lang_request` (Wave 107) is an explicit answer-language
    request detected in the message ("hi" / "en" /
    "hinglish", from langdetect_local.detect_language_request)
    — when present it outranks the question's own language for
    every language choice made in this layer: the Hindi flag,
    the one-line replies' flavour, the AI brains' prompt
    language and the not-found line. When it is None every
    choice below is exactly the pre-Wave-107 one. `detail`
    (Wave 136) is an explicit long-answer request detected
    in the message (langdetect_local.detect_detail_request):
    it is forwarded ONLY to the AI brains' prompt builder
    (their DETAIL variant) — no deterministic layer's output
    changes here; api.py expands those itself via
    detail.expand_detail. When it is False the AI calls
    below are made exactly as before this wave."""
    if lang_request in ("hi", "hinglish"):
        hindi = True
    elif lang_request == "en":
        hindi = False
    else:
        hindi = _looks_hindi(question)
    req_flavour = {"en": "en", "hi": "dev",
                   "hinglish": "roman"}.get(lang_request)

    # Layer 0 / 0b run before the solver result is even looked
    # at: the solver's letter-products for "hi" / "what is the
    # capital of india" are not answers at all.
    # Merge-5 (decided rule 1): a greeting is NOT "not found" —
    # Wave 68's friendly per-flavour one line is served (kind
    # "greeting", plain rendering). Wave 67's collapse of
    # greetings to the not-found line is superseded here.
    greeting = _greeting_result(question, hindi, req_flavour)
    if greeting is not None:
        return greeting
    if _is_nonmaths(question):
        return _nonmaths_result(question, hindi, req_flavour)

    # Wave 111: the maths-META layer (maths_meta.py) — maths
    # history/creator facts and study/practice/exam advice.
    # It sits here, after the greeting and non-maths guards
    # (so the guards stay authoritative) and before every
    # solving/concept layer, because its whole point is the
    # questions those layers mishandle: a WHO-shaped ask
    # ("Pythagoras theorem kisne banaya tha?") used to be
    # served the WHAT card by the concept layers below, and
    # person/advice asks fell through to the not-found line.
    # The layer's own double gate (who shape + curated
    # topic/person keyword; advice trigger + maths gate) plus
    # its computation veto keep every real problem and every
    # concept ask out — it returns None for all of them, and
    # the flow below is then exactly the pre-Wave-111 one.
    try:
        from maths_meta import meta_result
        meta = meta_result(question,
                           req_flavour or _flavour(question))
    except Exception:
        meta = None
    if meta is not None:
        return meta

    if _is_real(question, result):
        # Wave 100: a multi-part bundle (mega-MCQ set, case
        # study) is not one question — a whole-text "solve" of
        # it is a fragment carved out of one part (the Wave 93
        # audit's regression #5 served "x = -2/7" from part
        # (iv)'s line equation as the answer to a 15-part ICSE
        # set). The parts are the authority: when the bundle
        # splits and at least one part verifiably solves, the
        # multipart answer stands instead of the fragment.
        try:
            from multipart import multipart_preferred
            mp_preferred = multipart_preferred(question, result)
        except Exception:
            mp_preferred = None
        if mp_preferred is not None \
                and not _w150_veto(question, mp_preferred):
            return _with_figure(question, mp_preferred)
        # Wave 95: for a proof ask, a SymPy-verified identity
        # derivation (proofs.py) upgrades the solver's bare
        # verdict ("Identity verified ✔" with no working, or a
        # parse-flawed "Not an identity" for true identities
        # like (sin A + cos A)^2 = 1 + 2 sin A cos A). The
        # layer returns None for anything it cannot verify,
        # so a genuinely false identity keeps the solver's
        # "Not an identity" and every non-proof real answer
        # is untouched.
        try:
            from proofs import proof_result
            proof = proof_result(question, hindi,
                                 lang_request=lang_request)
        except Exception:
            proof = None
        if proof is not None:
            return proof
        # Wave 76: a question that arrived WITH options gets
        # its answer named by option even when the whole text
        # solved as-is — and for MCQs the STEM solve is the
        # authority, because the option numbers pollute the
        # full-text solve (the HCF of "12 and 18 (A) 3 (B) 6
        # (C) 9 (D) 36" comes out as the HCF of all six numbers
        # — the wrong option). mcq_preferred only fires on an
        # exact one-option match and returns None otherwise,
        # leaving the real result untouched.
        try:
            from mcq import mcq_preferred
            wrapped = mcq_preferred(question, result)
        except Exception:
            wrapped = None
        if wrapped is not None:
            return _with_figure(question, wrapped)
        # Wave 82: the same authority question for OR bundles
        # and case-study sets — a whole bundle fed to the
        # solver as one text can come back as a fragment
        # dressed as an answer (the matrix/system OR bundle
        # "solves" to 2*x - y + 6, a shred of one equation).
        # formats_preferred serves the format result only
        # when a part verifiably solves AND the whole-text
        # answer matches none of the solved parts' answers;
        # a genuine whole-text solve of a part is left
        # untouched.
        try:
            from formats import formats_preferred
            preferred = formats_preferred(question, result)
        except Exception:
            preferred = None
        if preferred is not None:
            return _with_figure(question, preferred)
        # Wave 103: a polynomial-degree ask whose primary
        # result is the simplify path's mangled expression
        # ("degree of 3x^3 + 2x^2 + 5x + 7" came back as
        # "2*x**2 + 5*x + 10" — the words are eaten into the
        # expression, so the router's failure gate can never
        # see it) is upgraded to the verified degree.
        # degree_upgrade fires only on a strict degree ask
        # whose answer is not already the true degree, so
        # every other real answer is untouched.
        try:
            from solver.gaps103 import degree_upgrade
            upgraded = degree_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        # Wave 115: the hijacked Rekha Ganit asks — a 2x2
        # system solution served for a parallel/perpendicular
        # CHECK, an angle-between-lines ask or a line-through-
        # intersection ask; the ratio echoed back for a
        # dividing-POINT ask; the segment's own line served
        # for its perpendicular bisector. Those results are
        # "real" answers to different questions, so the
        # router's failure gate can never see them.
        # rekha_upgrade fires only on the strict ask shape
        # whose rekha schema settles the question completely,
        # leaving every other real answer untouched.
        try:
            from solver.rekha import rekha_upgrade
            upgraded = rekha_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        # Wave 142: the hijacked Class 12 book-gap asks —
        # a partially parsed inverse-trig sum served as
        # one term's value ("sec^-1(2/sqrt(3))" came back
        # pi/3, the "2" alone), a scalar triple product
        # served as "b = 2", a triangle area served as a
        # decimal approximation of the wrong vectors.
        # Those results are "real" answers to different
        # (partially parsed) questions, so the router's
        # failure gate can never see them.
        # c12gaps142_upgrade fires only when a strict
        # Wave 142 schema settles the question completely
        # AND the served answer verifiably differs (numeric
        # value mismatch, or a yes/no verdict flip),
        # leaving every other real answer untouched.
        try:
            from solver.c12gaps142 import c12gaps142_upgrade
            upgraded = c12gaps142_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        # Wave 143: an explicit graph-METHOD ask ("by
        # graphical method", "graph se hal karo") whose
        # pair the solver answered algebraically, or a
        # zeros ask it answered without the graph. The
        # student asked for the graph way, so when the
        # graphical answer AGREES with the standing one —
        # the plotted intersection, computed independently
        # from the drawn lines' own points, equals the
        # standing (x, y); the standing answer names
        # exactly the graph's zeros — the graphical answer
        # stands instead: both lines drawn, the solution
        # read off the crossing point. On any disagreement
        # graphsolve_upgrade returns None and the standing
        # algebraic answer is served untouched, WITHOUT
        # the graph claim.
        try:
            from graphsolve import graphsolve_upgrade
            upgraded = graphsolve_upgrade(question, result,
                                          hindi)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return upgraded
        # Wave 125: the hijacked solver-depth asks — the
        # Hindi-equation path's "z = 3" for an LPP ask, the
        # unconditional dice/card probability served for a
        # "given that …" conditional ask, the equation
        # solver's "y = 1" for a DE-with-initial-condition
        # ask, "x = 0" for a sin/cos area ask. Those results
        # are "real" answers to different questions, so the
        # router's failure gate can never see them.
        # depth125_upgrade fires only when a strict schema
        # settles the question completely AND the served
        # answer is not already the schema's value.
        try:
            from solver.depth125 import depth125_upgrade
            upgraded = depth125_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        # Wave 128: a PURE graph request the router solved
        # as something else — "y = 2x + 3 ka graph banao"
        # came back as a hindi_equation solve ("y = 2"),
        # "draw the graph of y = x^3" as a solve-for-x.
        # The graph IS the answer asked for, so on the
        # strict pure-ask shape (explicit picture trigger,
        # no surviving solve verb, a supported target) the
        # graph answer stands instead. graph_upgrade
        # returns None for every genuine solve, leaving
        # the real result untouched.
        try:
            from graphs import graph_upgrade
            upgraded = graph_upgrade(question, result, hindi)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return upgraded
        # Wave 146: MCQ / Assertion–Reason AUTHORITY. When
        # the question carries options (or is an
        # assertion–reason item) and NONE of the authority
        # layers above could certify the whole-text result —
        # no multipart split, no verified proof, no exact
        # one-option match (mcq_preferred), no format part —
        # the raw whole-text result is NOT served: for an MCQ
        # the option numbers pollute the full-text parse, and
        # mcq_wrap can even certify a garbage value that
        # happens to coincide with a distractor (the CISCE
        # audit served "(b) 0" for a derivative MCQ whose
        # whole-text "solve" was C(2, 7) = 0 from the stem's
        # own numbers). Fall through to the lower chain: the
        # bank, the MCQ STEM solve (mcq_result), the formats
        # layer, or the honest not-found. An option is never
        # echoed and never guessed.
        _w146_options_bearing = _w146_has_plausible_options(
            question)
        if not _w146_options_bearing:
            try:
                from formats import extract_ar
                _w146_options_bearing = \
                    extract_ar(question) is not None
            except Exception:
                _w146_options_bearing = False
        if not _w146_options_bearing \
                and _w146_ar_shaped(question):
            # Wave 146: OCR'd papers often lose the "(A)"
            # markers formats.extract_ar expects — the words
            # "Assertion:" / "Reason:" arrive plain, with
            # (a)-(d) options. The shape alone is enough to
            # withhold the raw whole-text result (the audit's
            # A–R item was served "x = 2", carved out of the
            # Reason's identity).
            _w146_options_bearing = True
        if not _w146_options_bearing:
            return _with_figure(question, result)
        # else: fall out of the _is_real branch — the layers
        # below decide.

    # Wave 20, Layer 0c: a SCIENCE question the solver could not
    # really answer gets the honest maths-only reply + formula
    # guidance — BEFORE salvage, which would otherwise carve a
    # fake "maths part" out of it (the refractive-index case).
    if has_science_signal(question):
        return _science_result(question, hindi, req_flavour)

    # Wave 125: a primary solve that ran past its time
    # budget returns the router's op "error" refusal from
    # OUTSIDE _solve_question_uncached, so the Wave 125
    # failure gate inside the router never ran for it (the
    # dy/dx = (x + y)/(x - y) homogeneous DE is the known
    # case — the primary dsolve grinds for ~10 s and the
    # answer flip-flops between its implicit form and a
    # timeout). Consult the strict Wave 125 schemas once
    # here, before the bank: they return None unless one
    # settles the question completely, so every other
    # fall-through runs exactly as before.
    if isinstance(result, dict) and \
            result.get("op") == "error" and \
            result.get("answer") == \
            "That one is too big to work out here.":
        try:
            from solver.depth125 import solve_depth125
            w125 = solve_depth125(question)
        except Exception:
            w125 = None
        if w125 is not None:
            return _with_figure(question, w125)

    # Wave 39: the Verified Data Bank exact-match layer. It sits
    # AFTER the science guard (a science question is never
    # served from the bank) and after a real solver answer has
    # been served untouched above — what it upgrades is the
    # fall-through: a question the solver could not really
    # answer, whose EXACT normalised text matches a banked item,
    # gets that item's SymPy-verified steps + final answer
    # instead of a salvaged fragment, a similar example or the
    # general guide. Exact-only, so it can never shadow the
    # solver for a non-identical question; on a miss the layers
    # below run exactly as before.
    banked = _bank_answer(question)
    if banked is not None:
        return banked

    # Wave 117: the Live Bank (livebank.py) — questions
    # students actually asked, answered before by a
    # deterministic layer and stored VERIFIED at ask time.
    # It sits exactly where the master bank sits (after the
    # science guard, after a real solver answer, before the
    # fall-through layers it can only ever reproduce), and
    # serves only a language-key match: a repeat ask gets
    # its stored answer instantly instead of re-paying the
    # salvage / concept / AI layers. Pending (AI) rows are
    # never served — they wait for offline verification.
    live = _livebank_answer(question, lang, lang_request)
    if live is not None:
        return live

    # Wave 76: the MCQ layer (mcq.py). A question that arrives
    # WITH its options ("(a) 12 (b) 18 (c) 24 (d) 36") usually
    # defeats the solver as a whole — the Wave 71 audit counted
    # 75 such failures in a 150-question papers sample — but
    # the STEM alone often solves through the ordinary
    # machinery. This layer extracts stem + options, solves the
    # stem, and serves the stem's own steps with a final answer
    # naming the one option the computed value matches. It
    # sits here — after the science guard and the bank, before
    # salvage (which would otherwise carve a fragment out of
    # the option text) — and returns None unless the stem
    # really solved AND exactly one option matched, so on any
    # doubt the layers below run byte-for-byte as before. An
    # option is never guessed.
    try:
        from mcq import mcq_result
        mcq = mcq_result(question)
    except Exception:
        mcq = None
    if mcq is not None:
        return mcq

    # Wave 100: the multi-part layer (multipart.py) — mega-MCQ
    # bundles, case-study sets and "Hence, …" chains, the
    # paper formats the Wave 93 audit's regressions #3–#5
    # exposed as missing from the live chain. It splits the
    # format, solves the parts through the existing machinery
    # and serves only what settles exactly; unsolved parts
    # carry the one-line not-found. It sits here — after the
    # MCQ layer, before salvage (which would otherwise carve
    # a fragment out of the bundle) — and returns None on any
    # doubt, so the layers below run byte-for-byte as before.
    try:
        from multipart import multipart_result
        multi = multipart_result(question)
    except Exception:
        multi = None
    if multi is not None and not _w150_veto(question, multi):
        return multi

    # Wave 95: the proof layer (proofs.py). "Prove that ..."
    # asks the solver could not answer — algebraic identities
    # (which ended at the not-found line) and the irrationality
    # proofs (which the concepts card answered for the WRONG
    # root: a sqrt(5) ask was served the sqrt(2) card) — are
    # answered here, but only when honestly possible: a
    # SymPy-verified identity derivation, or the standard
    # textbook proof from proofs_data.py. Anything else
    # returns None and the layers below run as before.
    try:
        from proofs import proof_result
        proof = proof_result(question, hindi,
                             lang_request=lang_request)
    except Exception:
        proof = None
    if proof is not None:
        return proof

    # Wave 82: the paper-format layer (formats.py). Board
    # papers paste three shapes the solver and the MCQ layer
    # cannot use: OR bundles ("Solve A OR Solve B" / "…
    # अथवा …"), Assertion–Reason items, and case-study sets
    # (a passage plus labelled sub-questions). This layer
    # splits the format, solves the parts through the existing
    # machinery, and serves only what it can settle exactly —
    # an OR alternative that really solves, an Assertion–
    # Reason combination both of whose statements a decider
    # in formats.py could decide, a case-study set with at
    # least one solved part. It sits here — after the science
    # guard, the bank and the MCQ layer, before salvage
    # (which would otherwise carve a fragment out of the
    # bundle) — and returns None on any doubt, so the layers
    # below run byte-for-byte as before. An A–R option is
    # never guessed.
    try:
        from formats import formats_result
        formatted = formats_result(question)
    except Exception:
        formatted = None
    if formatted is not None:
        return formatted

    # Wave 143: the graph-METHOD layer (graphsolve.py).
    # Suraj's standing rule — a graph-type question is
    # solved USING the graph, not merely pictured. Three
    # shapes the layers above miss: a linear pair solved
    # by its graph (the parallel / coincident phrasings
    # and "draw the graph and find the solution" end at
    # not-found today; the unique-solution phrasings are
    # repaired in the real branch above), the zeros of a
    # polynomial read off its graph's x-intercepts ("kitne
    # zero hai graph se" ends at a salvage fragment
    # today), and chart-reading asks whose data is stated
    # in the question — the chart drawn AND the
    # sub-question (sabse zyada / antar / kul) answered
    # from it, where Wave 128 deliberately only drew or
    # refused. It sits here — before the Wave 128 graph
    # layer, whose pure-ask gate vetoes these solve-verb
    # shapes — under its own strict gates: an explicit
    # graph-method / zeros / chart-reading trigger, a
    # full parse, and an exact cross-check of every
    # read-off (plotted intersection vs algebraic
    # solution; sp.solve vs sp.real_roots; chart values
    # from the validated parse). It returns None on any
    # doubt, so the layers below run byte-for-byte as
    # before.
    try:
        from graphsolve import graphsolve_result
        gsolved = graphsolve_result(question, hindi)
    except Exception:
        gsolved = None
    if gsolved is not None:
        return gsolved

    # Wave 128: the graph layer (graphs.py). A graph /
    # plot / number-line / chart request the solver could
    # not answer at all ("draw the graph of y = x^2" ended
    # at the not-found line; "plot the points (2, 3) and
    # (4, 5)" likewise) is answered here with a hand-built
    # verified SVG — but only on the strict pure-ask shape:
    # an explicit picture trigger, no surviving solve
    # verb, and a supported target (validated function
    # form, stated points, a re-solvable linear
    # inequality, stated chart data). It sits here —
    # after the science guard, the bank and the format
    # layers, before salvage (which would otherwise carve
    # a fragment out of the request) — and returns None
    # on any doubt, so the layers below run byte-for-byte
    # as before.
    try:
        from graphs import graph_result
        graphed = graph_result(question, hindi)
    except Exception:
        graphed = None
    if graphed is not None:
        return graphed

    # The solver did not really answer. Work the layers.
    # Wave 146: salvage YIELDS to options-bearing questions,
    # for the same reason the concept layers yield below
    # (Wave 100): salvage carves a solvable fragment out of
    # the text, and in an MCQ the most carve-able fragments
    # are the OPTIONS themselves — the CISCE audit's
    # sum-of-squares MCQ was "salvaged" into the mean of its
    # own option values (298). An MCQ no solving layer could
    # settle ends at the honest not-found, never at a carved
    # fragment of its options.
    _w146_is_mcq_text = _w146_has_plausible_options(question)
    if not _w146_is_mcq_text and _w146_ar_shaped(question):
        _w146_is_mcq_text = True
    # Wave 146: salvage also yields to PROOF asks — "solving
    # the maths part" of a proof means solving the identity
    # as an equation and serving its roots, which is the
    # audit's spurious pattern verbatim (a continued-
    # proportion proof was salvaged into four equation
    # roots). The proofs layer below gets the ask instead.
    _w146_is_proof_ask = bool(re.search(
        r"\b(?:prove|show)\s+that\b|सिद्ध\s+करो",
        str(question or "").lower()))
    # Wave 146: salvage also yields when the Wave 146 veto
    # layer rejected the solver's whole-text result for this
    # question — carving a fragment out of the same text
    # reproduces the same incoherence (the "find the value
    # of a + b" ask was salvaged into solving "+ b = 0").
    _w146_vetoed = False
    try:
        _w146_vetoed = _w146_veto(question, result)
    except Exception:
        _w146_vetoed = False
    salvaged = None
    if not _w146_is_mcq_text and not _w146_is_proof_ask \
            and not _w146_vetoed:
        salvaged = _salvage(question, hindi)
    if salvaged is not None:
        return salvaged

    # Wave 75: the topics-library concept layer
    # (concept_topics.py). A genuine concept ask — definition,
    # formula, how-to, difference, why — is answered from the
    # app's own topics library (the topic's method + its
    # verified worked example) instead of the small concepts.py
    # card. It sits here, after the solver, the bank and
    # salvage, so a concrete problem has already had every
    # real chance to solve; its own gate + vetoes keep it from
    # ever capturing one. On no confident topic match the
    # Wave-18 concepts.py card runs exactly as before.
    # Wave 100: the concept layers YIELD to options-bearing
    # (MCQ-shaped) questions. A question that carries options
    # is a problem to solve, not a concept to teach — when
    # every solving layer above has failed it, serving a
    # concept card for its keywords is a hijack (the Wave 93
    # audit's regression #1: "x + 1/x = 3 … value of a - b + c
    # is: (A) 5 (B) 2 (C) 1 (D) -1" was served the Quadratic
    # Formula card). The topics layer already vetoes option
    # markers internally; the concepts.py card did not, so
    # the yield is enforced here for both layers at once.
    # Genuine concept asks carry no option list, so their
    # behaviour is untouched.
    options_bearing = False
    try:
        from mcq import extract_mcq
        options_bearing = extract_mcq(question) is not None
    except Exception:
        options_bearing = False
    if not options_bearing and _w146_ar_shaped(question):
        # Wave 146: an Assertion–Reason item is a problem to
        # decide, not a concept to teach, either.
        options_bearing = True
    concept = None
    if not options_bearing:
        try:
            concept = topic_concept_result(question)
        except Exception:
            concept = None
        if concept is None:
            concept = _concept_result(question, hindi)
    if concept is not None:
        result_out = concept
    else:
        similar = _similar_result(question, hindi)
        if similar is not None:
            result_out = similar
        elif _is_vague(question):
            result_out = _guide_result(question, hindi, "vague",
                                       req_flavour)
        elif _is_gibberish(question):
            # Wave 111: a WHO/ADVICE-shaped MATHS question the
            # curated meta layer missed ("Euler kaun the?")
            # is not gibberish — it is a real question this
            # app cannot answer itself. Classify it as
            # "guide" instead: the content served locally is
            # the identical one-line not-found (via the
            # collapse below), but "guide" is in _GEMINI_KINDS,
            # so in production the AI chain gets its chance
            # at the student's actual question first. Genuine
            # gibberish (no meta shape) is untouched.
            try:
                from maths_meta import is_meta_shaped
                meta_shaped = is_meta_shaped(question)
            except Exception:
                meta_shaped = False
            result_out = _guide_result(
                question, hindi,
                "guide" if meta_shaped else "gibberish",
                req_flavour)
        else:
            result_out = _guide_result(question, hindi, "guide",
                                       req_flavour)

    # Wave 37: when the honest layers still could not answer
    # the student's own question (similar example, concept card
    # or the general guide), ask Gemini (free tier) before
    # settling — solver first, AI only as the fallback. Any
    # Gemini failure leaves the Wave-18 answer untouched.
    # Wave 41: when Gemini returns None, Groq (also free tier)
    # gets the same question before we settle. Exact solves,
    # salvage, greetings, non-maths and science replies have
    # all returned earlier, so neither brain can reach them.
    # Wave 108: when Groq also returns None, OpenRouter (also
    # free tier) gets the same question as the last resort.
    # Wave 133: "gets the same question" now happens behind
    # a verification gate — a leg's answer must pass
    # aiverify's sanity + deterministic / consensus checks
    # before it can be served (see _verified_ai_answer); a
    # rejected answer moves the chain to the next leg, and
    # total rejection falls through to the honest collapse
    # below, with the rejected bundle parked for Wave 134.
    # Wave 75: a topics-library concept answer (source
    # "topics") is verified in-app content (Wave 55) — like
    # the bank, it is exempt from the AI upgrade below, which
    # could otherwise rewrite it and burn free quota.
    # Wave 134: the deep-solve stage (deep_solve.py) — before
    # any AI brain is asked, Ganitra tries HARDER itself:
    # reformulated variants of the question through the real
    # solver, guard schemas for the two known partial-answer
    # shapes, and part-wise splitting. It runs for every
    # standing the AI chain would have served (the topics
    # exemption below is about AI rewriting verified content
    # and burning quota — the deep stage is Ganitra's own
    # solver, so it runs for topics standings too: a concrete
    # problem wearing spelled-out numbers deserves its real
    # answer, not just the concept card). Any failure of the
    # stage itself leaves the chain exactly as it was.
    # (A "gibberish"-classified standing is covered too: a
    # spelled-out equation ("three x plus five equals
    # twenty") carries no digits for the gibberish gate to
    # see, yet its reformulation solves exactly. True
    # gibberish produces no viable variant and falls
    # through untouched, at the cost of a few regex passes.)
    if result_out.get("fallback_kind") in _GEMINI_KINDS + (
            "gibberish",):
        try:
            from deep_solve import deep_solve
            deep = deep_solve(question, hindi=hindi, lang=lang,
                              lang_request=lang_request,
                              student_class=student_class)
        except Exception:
            deep = None
        if deep is not None:
            return _with_figure(question, deep)

    if result_out.get("fallback_kind") in _GEMINI_KINDS \
            and result_out.get("source") != "topics":
        # Wave 133: the legs now run behind aiverify's
        # verification gate — an AI answer is served only
        # when its claimed final value survives the sanity
        # gate plus a deterministic check or a cross-leg
        # consensus (see _verified_ai_answer). On total
        # verification failure the rejected candidates are
        # parked on result_out["_ai_rejected"] — the Wave
        # 134 deep-solve seam: that stage hooks in HERE,
        # between this block and the Wave 67 collapse below,
        # and consumes the bundle from result_out before the
        # collapse builds the (fresh) not-found dict, which
        # never carries the key.
        # Wave 131: a caller streaming the answer (the
        # /api/solve/stream endpoint, flag-gated) needs the
        # chain to STOP here: the AI legs are the slow part
        # and only they can be streamed. The marker carries
        # everything the streaming layer needs to finish the
        # job with identical outcomes — the Hindi flag this
        # chain computed, the pre-collapse kind (for the
        # Wave-90 log, fired later only if the honest outcome
        # is really served) and that honest outcome itself,
        # computed by the same code the classic ending runs.
        # The marker is internal: it is never served, never
        # recorded and never cached.
        if defer_ai:
            deferred = dict(result_out)
            deferred["ai_deferred"] = True
            deferred["ai_hindi"] = hindi
            deferred["ai_pre_collapse_kind"] = \
                result_out.get("fallback_kind")
            deferred["ai_honest"] = _honest_after_ai_miss(
                question, result_out, hindi, lang, lang_request,
                student_class=student_class, log=False)
            return deferred
        rejected_sink = []
        ai_result = _verified_ai_answer(
            question, hindi, lang_request, rejected_sink,
            detail=detail)
        if ai_result is not None:
            # Wave 134: method transfer at the accept seam —
            # when the AI's demonstrated METHOD recomputes
            # (from the question's own numbers) to a
            # DIFFERENT value than the AI claimed, Ganitra
            # serves its OWN recomputed answer instead. An
            # agreeing recomputation (or an unrecognised
            # method) leaves the AI answer byte-identical.
            # Deploy-27 merge decision: a result Wave 133's
            # gate marked "deterministic" was recomputed from
            # the question itself and matched — verification
            # is decisive there, so transfer never overrides
            # it (Wave 134's own merge recommendation:
            # "Verified → serve it"). Transfer guards the
            # weaker marks — consensus, single-leg and the
            # unmarked pre-133 path (kill switch) — exactly
            # the answers nobody has recomputed yet.
            if ai_result.get("ai_verification") != \
                    "deterministic":
                try:
                    from deep_solve import deep_solve
                    own = deep_solve(
                        question, hindi=hindi, lang=lang,
                        lang_request=lang_request,
                        ai_result=ai_result,
                        student_class=student_class)
                except Exception:
                    own = None
                if own is not None:
                    return _with_figure(question, own)
            return ai_result
        if rejected_sink:
            result_out["_ai_rejected"] = rejected_sink[0]
            # Wave 134 (Deploy-27 merge, per its notes'
            # recommended order): verification failed for
            # every candidate — before collapsing, give
            # method transfer the rejected results: a wrong
            # VALUE carried by a right METHOD is exactly its
            # case, and a recomputation from the question's
            # own numbers can still give the student
            # Ganitra's own correct answer. No extractable
            # method (or agreement) → the honest collapse
            # below stands.
            for _rec in rejected_sink[0].get("rejected") or []:
                _rej = _rec.get("result")
                if not isinstance(_rej, dict):
                    continue
                try:
                    from deep_solve import deep_solve
                    own = deep_solve(
                        question, hindi=hindi, lang=lang,
                        lang_request=lang_request,
                        ai_result=_rej,
                        student_class=student_class)
                except Exception:
                    own = None
                if own is not None:
                    return _with_figure(question, own)

    # Wave 67: whatever honest layer is still standing here —
    # a similar example, gibberish, the general guide — means
    # the student's OWN question was not solved, so the whole
    # answer collapses to the one not-found line.
    # A concept card is a real answer (formula + worked
    # example for the exact concept asked) and is served as-is.
    # Merge-5 (decided rule 1): a VAGUE ask no longer collapses
    # — _guide_result already settled it as Wave 68's friendly
    # per-flavour line (kind "vague", plain rendering).
    # (Wave 131: the collapse itself lives in
    # _honest_after_ai_miss now — one source for both endings.)
    return _honest_after_ai_miss(
        question, result_out, hindi, lang, lang_request,
        student_class=student_class)


# ---------------------------------------------------------------------------
# Wave 117: the Live Bank hooks (livebank.py)
# ---------------------------------------------------------------------------

def _livebank_lang_key(question, lang, lang_request):
    """The live bank's language key for one ask — Wave 107's
    rules, owned here because this layer owns the language
    choices: an explicit in-message request wins verbatim
    ("en" / "hi" / "hinglish"); a bn/mr/ta/te session
    language keys under itself (conservative — its answers
    are stored and served only within that language); else
    the question's own flavour decides, with the same
    mapping the Wave 90 log uses (dev -> "hi", roman ->
    "hinglish", en -> "en"). Record and lookup compute the
    key through this one function, so the two sides always
    agree."""
    if lang_request in ("en", "hi", "hinglish"):
        return lang_request
    if lang and lang not in ("en", "hi"):
        return lang
    return {"dev": "hi", "roman": "hinglish",
            "en": "en"}[_flavour(question)]


def _livebank_answer(question, lang, lang_request):
    """The Live Bank's stored VERIFIED answer for this exact
    question + language key (livebank.lookup_live_result),
    or None. Lazy import + blanket guard, same pattern as
    the bank layer above: the store is an accelerator, and
    any failure must leave the chain exactly as it was."""
    try:
        from livebank import lookup_live_result
        return lookup_live_result(
            question,
            _livebank_lang_key(question, lang, lang_request))
    except Exception:
        return None


def _record_livebank(question, result, lang, lang_request):
    """Record one finished outcome in the Live Bank.
    Double-guarded like the Wave 90 hook:
    livebank.record_answer never raises by contract, and
    this wrapper swallows even an import failure — storing
    is observational and must never slow, break or alter
    the answer. Note what is NOT passed: no student class,
    no session, no identity of any kind — the store's
    privacy rule is question text only. A result the Live
    Bank itself just served is not re-recorded (its hit was
    already counted by the serve, and re-storing the served
    copy would bake the live_bank marker into the stored
    payload)."""
    if isinstance(result, dict) and result.get("live_bank"):
        return
    try:
        from livebank import record_answer
        record_answer(
            question, result,
            _livebank_lang_key(question, lang, lang_request))
    except Exception:
        pass
    # Wave 133: an AI answer this wave's verification gate
    # marked "deterministic" has EARNED verified status — its
    # claimed value was recomputed from the question itself
    # and matched. Promote its Live Bank row through the
    # store's own set_status machinery (the same hook the
    # offline databank pipeline uses). Consensus and single
    # marks are weaker evidence and stay "pending", exactly
    # as Wave 117 designed. Guarded like everything here:
    # promotion is bookkeeping and can never alter the
    # answer the student already has.
    if isinstance(result, dict) and \
            result.get("ai_verification") == "deterministic":
        try:
            from bank import normalise_question
            from livebank import VERIFIED, set_status
            set_status(
                normalise_question(question),
                _livebank_lang_key(question, lang, lang_request),
                VERIFIED)
        except Exception:
            pass


def with_fallback(question, result, lang=None, student_class=None,
                  lang_request=None, defer_ai=False,
                  detail=False):
    """The chain above (_with_fallback_chain), plus Wave
    117's record hook: every finished outcome — solver,
    bank, deterministic layer or AI — is offered to the
    Live Bank, which stores the storeable ones (verified
    for deterministic answers, pending for AI answers) so a
    repeat ask can be served instantly. Recording happens
    after the answer is final and can never change it; the
    not-found / non-maths / greeting outcomes are refused
    by the store's own classifier (Wave 90's log owns the
    not-found ones).

    Wave 130 (steps language): Wave 107 made an explicit
    request switch the chrome, the explanation and the AI
    prompt, but the solver's own STEP sentences kept the
    question's language — an English question with "answer
    in Hindi" got English working lines under a Hindi card.
    When a request is in force, solver-family results now
    pass through steplang.relanguage_result, which renders
    the solver's recurring boilerplate step templates in the
    requested language (EN / Hindi Devanagari / Hinglish
    Roman) without ever touching formulas, numbers or answer
    values; untranslatable free-form lines pass through
    unchanged. The relanguaging happens BEFORE the Live Bank
    record below, so what is stored under the request's
    language key is the answer the student actually saw.
    Concept cards, proofs (bilingual data switched by the
    chain's own flag) and the AI legs are language-aware
    already and are never touched by the transform. With no
    request this hook is skipped entirely and behaviour is
    byte-identical to before this wave."""
    out = _with_fallback_chain(question, result, lang=lang,
                               student_class=student_class,
                               lang_request=lang_request,
                               defer_ai=defer_ai, detail=detail)
    if lang_request in ("hi", "en", "hinglish"):
        try:
            from steplang import relanguage_result
            out = relanguage_result(out, lang_request)
        except Exception:
            pass
    # Wave 131: a deferred marker is not a finished outcome —
    # the streaming layer records the FINAL result itself
    # (record_outcome below) once the AI legs have answered
    # or missed, so the store never sees the marker.
    if not (isinstance(out, dict) and out.get("ai_deferred")):
        _record_livebank(question, out, lang, lang_request)
    return out


def record_outcome(question, result, lang=None, lang_request=None):
    """Wave 131: the public face of the Wave-117 record hook
    for a caller that finishes an answer asynchronously —
    the streaming endpoint records the result it actually
    served (an AI answer, or the honest outcome when every
    leg missed), exactly as with_fallback would have."""
    _record_livebank(question, result, lang, lang_request)


def fallback_answer(question, result=None, lang=None,
                    student_class=None, lang_request=None,
                    detail=False):
    """Convenience wrapper: solve (if no result was given) and
    guarantee a presentable answer dict."""
    if result is None:
        try:
            result = solve_question(question)
        except Exception as e:  # solver must never leak a crash
            result = {"type": "solver", "op": "error",
                      "answer": f"Could not solve this one: {e}",
                      "steps": []}
    return with_fallback(question, result, lang=lang,
                         student_class=student_class,
                         lang_request=lang_request,
                         detail=detail)


__all__ = ["with_fallback", "fallback_answer", "record_outcome",
           "log_deferred_not_found"]
