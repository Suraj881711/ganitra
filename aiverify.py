"""Wave 133: AI-answer verification — "jawab ki jaanch".

Suraj's order (17 Nov 2026): "Bade AI galat ans de dete hai
but Ganitra ko analysis karna hai aur uska ans sahi dena hai —
Ganitra ke andar ye wali power tagdi honi chahiye ans dene
ki." The big AIs sometimes answer wrong with full confidence.
Ganitra's core promise — never serve a guessed or wrong
answer — covered every layer EXCEPT one: the AI fallback
chain (Gemini -> Groq -> OpenRouter, fallback.py). An AI
answer used to be served on first ask with no correctness
check at all; Wave 117 only stopped a REPEAT of an AI answer
from being served unverified (the first serving itself was
unchecked, and the row sat "pending" forever). This module
is the missing gate, sitting between "an AI leg returned a
shaped answer" and "the answer is served":

  1. SANITY GATE (always, cheap, decisive): a claimed final
     value that is IMPOSSIBLE for the question — a probability
     outside [0, 1], a negative length / area / perimeter, a
     non-positive or non-integer HCF — rejects the candidate
     outright, no matter which leg said it.
  2. DETERMINISTIC CHECKS (strongest, free — no AI involved):
     for every question type that supports one, the claimed
     final value is checked against the QUESTION ITSELF with
     SymPy / exact rational arithmetic: plug an equation's
     claimed roots back in, recompute an HCF by divisibility
     and maximality, differentiate a claimed integral and
     sample a claimed derivative numerically, recompute a
     percentage / simple interest / standard probability /
     mensuration value from the question's own numbers. A
     pass is decisive (serve, marked verified); a fail is
     decisive too (the candidate is rejected even if another
     leg later agrees with it — two legs wrong the same way
     cannot outvote arithmetic).
  3. CROSS-LEG CONSENSUS (only when no deterministic check
     applies): a second leg is asked the same question and
     the final values are compared (exact rational / SymPy
     equivalence). Agreement serves the earliest carrier of
     the agreed value, marked consensus. Disagreement asks
     the third leg; a 2-of-3 majority wins. Legs that were
     never configured / are down (they return None) cast no
     vote: if exactly one leg answered and no other leg could
     be consulted, that answer is served marked "single"
     (the pre-Wave-133 behaviour, kept for the degraded case —
     in production all three keys are set, so a second opinion
     is almost always available). If two or more legs answered
     and no two agree, NOTHING is served.

OUTCOMES: a candidate that passes (deterministic or
consensus) is served with an `ai_verification` marker
("deterministic" / "consensus" / "single"). A candidate that
fails is NEVER served: the chain tries the next leg, and if
no leg produces a servable answer the caller falls through
to the existing honest outcome (the Wave 67 one-line
not-found) — Suraj's standing rule: a wrong answer is worse
than not-found. Every rejection is recorded in the
`ai_verify_log` table (question text, the claimed value, the
leg and the check that failed — question text only, no user
data, the Wave 90 log's pattern), and on TOTAL failure the
rejected bundle is handed to the caller's `on_rejected`
hook: fallback.py parks it on the chain's fall-through
result as `_ai_rejected`, which is the documented seam for
Wave 134's deep-solve stage (it consumes the bundle inside
_with_fallback_chain, between the AI block and the Wave 67
collapse; the served not-found dict itself never carries it).

SCOPE — what this layer does NOT verify: an AI answer with
no extractable final VALUE (a history / advice / explanation
answer, e.g. the Wave 111 meta flow for "Euler kaun the?")
carries no claim arithmetic can judge, so it is served
exactly as before (and stays "pending" in the Live Bank
forever — promotion below requires a deterministic pass).
Free-text reasoning inside the steps is never judged; only
the final claimed value is.

LIVE BANK PROMOTION: fallback.py's record hook promotes a
served AI answer's Live Bank row from "pending" to
"verified" via livebank.set_status() — ONLY when this layer
marked it "deterministic". A consensus pass is weaker
evidence (two AIs can share a mistake), so consensus and
single answers stay pending, exactly as Wave 117 designed.

SAFETY: verify_chain() NEVER raises and never blocks a
deterministic layer — it only ever sees AI-leg results
(solver / bank / concept answers never pass through here).
Any internal failure degrades to serving the first leg
answer already in hand (the pre-Wave-133 behaviour) rather
than breaking the chain. Set GANITRA_AIVERIFY=0 to switch
the whole layer off (the chain then behaves byte-identically
to pre-Wave-133: first leg answer wins).
"""
import os
import re
import sqlite3
import time
from fractions import Fraction

import sympy as sp

# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _dev_to_ascii(text):
    return str(text or "").translate(_DEV_DIGITS)


def _enabled():
    return os.environ.get("GANITRA_AIVERIFY", "1").strip() != "0"


def _close(a, b, rel=1e-6, abs_tol=1e-9):
    """Numeric closeness for two Fractions/floats."""
    try:
        fa, fb = float(a), float(b)
    except (TypeError, ValueError):
        return False
    return abs(fa - fb) <= max(abs_tol, rel * max(abs(fa), abs(fb)))


_FRAC_RE = re.compile(r"(-?\d+)\s*/\s*(\d+)")
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")


def extract_values(text):
    """Every numeric value stated in `text`, as Fractions, in
    order of appearance. Fractions (a/b) are read first and
    their spans masked so the digits inside are not counted
    twice; thousands separators are removed; Devanagari
    digits are normalised. A value immediately followed by
    "%" is returned as written (the probability code divides
    by 100 itself, because "%" means /100 only there)."""
    t = _dev_to_ascii(text).replace(",", "")
    out = []
    masked = list(t)
    for m in _FRAC_RE.finditer(t):
        num, den = int(m.group(1)), int(m.group(2))
        if den:
            out.append((m.start(), Fraction(num, den)))
        for i in range(m.start(), m.end()):
            masked[i] = " "
    rest = "".join(masked)
    for m in _NUM_RE.finditer(rest):
        try:
            out.append((m.start(), Fraction(m.group(0))))
        except (ValueError, ZeroDivisionError):
            continue
    out.sort(key=lambda p: p[0])
    return [v for _pos, v in out]


def _try_parse(text):
    """stepcheck's guarded SymPy parse (lazy import: stepcheck
    imports fallback, fallback imports this module lazily —
    top-level imports here stay stdlib + sympy only)."""
    try:
        from stepcheck import _try_parse as parse
        return parse(text)
    except Exception:
        return None


def _trim_to_expr(text, from_left):
    try:
        from stepcheck import _trim_to_expr as trim
        return trim(text, from_left)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Claim extraction — what the AI answer CLAIMS the answer is
# ---------------------------------------------------------------------------

_EXPR_PREFIX = re.compile(
    r"^\s*(?:dy/dx|d/dx|f'\(x\)|y'|x|y|f\(x\)|ans(?:wer)?|उत्तर)"
    r"\s*[:=]\s*", re.I)
_UNIT_TAIL = re.compile(
    r"\s*(?:sq\.?\s*(?:cm|m|km|units?)|cm\^?2|m\^?2|cm|mm|km|metres?|"
    r"meters?|rupees|rs\.?|years?|days?|hours?|units?|students?|"
    r"balls?|marbles?|cards?)\s*$", re.I)


def extract_claim(answer_text, question=None):
    """The machine-checkable claim inside an AI answer's final
    line, or None when the answer carries no value claim (a
    prose answer — history, advice, explanation).

    Returns {"values": [Fraction, ...], "expr": Expr|None,
    "raw": str}. `expr` is set when the answer (after removing
    an "x =" style prefix, a trailing "+ C" and a unit tail)
    parses as one expression in at most one variable — the
    integral / derivative claim shape. For a probability
    question, a value written with "%" is normalised to its
    fraction of 1 here, so "50%", "1/2" and "0.5" are the
    same claim."""
    raw = str(answer_text or "").strip()
    if not raw:
        return None
    values = extract_values(raw)
    prob_q = question is not None and _is_probability_q(question)
    if prob_q and "%" in raw:
        # Re-read: a "%"-suffixed value is a fraction of 1.
        t = _dev_to_ascii(raw).replace(",", "")
        pct = [Fraction(m.group(1)) / 100
               for m in re.finditer(r"(-?\d+(?:\.\d+)?)\s*%", t)]
        plain = [v for v in values
                 if not any(_close(v, p * 100, rel=1e-9)
                            for p in pct)]
        values = plain + pct
    expr = None
    body = _EXPR_PREFIX.sub("", raw)
    body = re.sub(r"\+\s*[Cc]\s*$", "", body.strip())
    body = _UNIT_TAIL.sub("", body.strip()).strip()
    if body and not re.search(r"[.!?]\s", body):
        parsed = _try_parse(body)
        if parsed is not None and len(parsed.free_symbols) <= 1:
            expr = parsed
    if not values and expr is None:
        return None
    if expr is not None and not values and not expr.free_symbols:
        try:
            values = [Fraction(sp.nsimplify(expr, rational=True))]
        except Exception:
            pass
    return {"values": values, "expr": expr, "raw": raw}


def _values_match_single(claim, expected, rel=1e-6):
    """True when the claim's values state `expected` (a
    Fraction): at least one value equals it, and no OTHER
    distinct value contradicts it (a decimal restatement of
    the same value — "1/6 ≈ 0.1667" — is the same claim, not
    a contradiction)."""
    vals = (claim or {}).get("values") or []
    if not vals:
        return False
    if not any(_close(v, expected, rel=rel) for v in vals):
        return False
    distinct = []
    for v in vals:
        if not any(_close(v, d, rel=0.02) for d in distinct):
            distinct.append(v)
    return len(distinct) == 1


def _values_match_set(claim, expected_values, rel=1e-4):
    """True when the claim's values are exactly the expected
    multiset (order-free)."""
    vals = sorted((claim or {}).get("values") or [])
    exp = sorted(expected_values)
    if len(vals) != len(exp):
        return False
    return all(_close(v, e, rel=rel) for v, e in zip(vals, exp))


def claims_agree(question, claim_a, claim_b):
    """Consensus comparison: do two legs' claims state the
    same final value(s)? Exact rational multiset equality,
    symbolic equality for expression claims, numeric sampling
    when symbolic simplification is inconclusive."""
    if claim_a is None or claim_b is None:
        return False
    va, vb = claim_a["values"], claim_b["values"]
    if va and vb:
        if len(va) == len(vb):
            sa = sorted(va)
            sb = sorted(vb)
            if all(_close(x, y, rel=1e-4) for x, y in zip(sa, sb)):
                return True
        # One leg may restate the same single value twice
        # ("1/6 ≈ 0.1667"): compare the distinct-value sets.
        def _distinct(vals):
            out = []
            for v in vals:
                if not any(_close(v, d, rel=0.02) for d in out):
                    out.append(v)
            return out
        da, db = _distinct(va), _distinct(vb)
        return (len(da) == len(db) and len(da) >= 1 and all(
            _close(x, y, rel=1e-4)
            for x, y in zip(sorted(da), sorted(db))))
    ea, eb = claim_a["expr"], claim_b["expr"]
    if ea is not None and eb is not None:
        try:
            if sp.simplify(ea - eb) == 0:
                return True
        except Exception:
            pass
        var = (ea.free_symbols | eb.free_symbols)
        if len(var) == 1:
            var = next(iter(var))
            return _expr_close(ea, eb, var) is True
    return False


def _expr_close(f, g, var, points=(0.3, 1.1, 2.0, -0.7)):
    """Numeric agreement of two expressions at sample points:
    True / False, or None when a point cannot be evaluated
    (singularity, zoo) — the caller treats None as no verdict."""
    for p in points:
        try:
            fv = complex(f.subs(var, p))
            gv = complex(g.subs(var, p))
        except Exception:
            return None
        if abs(fv.imag) > 1e-6 or abs(gv.imag) > 1e-6:
            return None
        if abs(fv.real - gv.real) > 1e-4 * max(1.0, abs(fv.real),
                                              abs(gv.real)):
            return False
    return True


# ---------------------------------------------------------------------------
# The sanity gate — hard impossibilities only
# ---------------------------------------------------------------------------

_PROB_WORDS = re.compile(
    r"probabilit|प्रायिकता|sambhavna|chance of|odds", re.I)
_MEASURE_WORDS = re.compile(
    r"\barea\b|\bperimeter\b|\blength\b|\bbreadth\b|\bwidth\b|"
    r"\bheight\b|\bvolume\b|circumference|\bradius\b|\bdiameter\b|"
    r"क्षेत्रफल|परिधि|लंबाई|चौड़ाई|ऊंचाई|आयतन", re.I)


def _is_probability_q(question):
    return bool(_PROB_WORDS.search(str(question or "")))


def sanity_check(question, result):
    """(ok, check_name). Fails ONLY on hard impossibilities —
    this gate must never accuse a plausible answer."""
    q = str(question or "")
    answer = str((result or {}).get("answer") or "")
    values = extract_values(answer)
    if not values:
        return True, None
    last = values[-1]
    if _is_probability_q(q):
        p = last
        if "%" in answer:
            # A percent-stated probability: "50%" means 1/2.
            m = re.findall(r"(-?\d+(?:\.\d+)?)\s*%", _dev_to_ascii(answer))
            if m:
                p = Fraction(m[-1]) / 100
        if p < 0 or p > Fraction(10001, 10000):
            return False, "sanity_probability_bounds"
    if _MEASURE_WORDS.search(q) and last < 0:
        return False, "sanity_negative_measure"
    if re.search(r"\bhcf\b|\bgcd\b|highest common factor|"
                 r"\blcm\b|lowest common multiple|"
                 r"least common multiple", q, re.I):
        if last <= 0 or last.denominator != 1:
            return False, "sanity_hcf_lcm"
    return True, None


# ---------------------------------------------------------------------------
# Deterministic checks. Each returns ("pass"|"fail"|"none", name):
# "none" = this check does not apply to the question; once a check
# APPLIES, its verdict is decisive — including "fail" when the
# claim is missing or unparseable (a checkable question whose
# answer states no checkable value has not been verified).
# ---------------------------------------------------------------------------

def _claim_or_fail(claim):
    return claim is not None and bool(claim["values"])


def _check_hcf_lcm(question, claim):
    q = str(question or "")
    is_hcf = re.search(r"\bhcf\b|highest common factor|\bgcd\b|"
                       r"greatest common divisor|महत्तम समापवर्तक",
                       q, re.I)
    is_lcm = re.search(r"\blcm\b|lowest common multiple|"
                       r"least common multiple|लघुत्तम समापवर्त्य",
                       q, re.I)
    if not is_hcf and not is_lcm:
        return "none", "hcf_lcm"
    # The operands are the integers named AFTER the keyword
    # (a class number or a year earlier in the sentence is
    # not an operand).
    m = re.search(r"hcf|gcd|lcm|factor|multiple|divisor|"
                  r"समापवर्तक|समापवर्त्य", q, re.I)
    tail = q[m.end():] if m else q
    nums = [int(n) for n in re.findall(r"\d+", _dev_to_ascii(tail))]
    nums = [n for n in nums if n >= 2]
    if len(nums) < 2:
        return "none", "hcf_lcm"
    from math import gcd
    if is_hcf:
        expected = nums[0]
        for n in nums[1:]:
            expected = gcd(expected, n)
        name = "hcf"
    else:
        expected = nums[0]
        for n in nums[1:]:
            expected = expected * n // gcd(expected, n)
        name = "lcm"
    if not _claim_or_fail(claim):
        return "fail", name
    return ("pass" if _values_match_single(
        claim, Fraction(expected)) else "fail"), name


def _check_equation(question, claim):
    q = str(question or "")
    try:
        from fallback import _extract_equation
        eq_text = _extract_equation(q)
    except Exception:
        eq_text = None
    if not eq_text or eq_text.count("=") != 1:
        return "none", "equation"
    lhs_t, rhs_t = eq_text.split("=", 1)
    lhs = _try_parse(lhs_t)
    rhs = _try_parse(rhs_t)
    if lhs is None or rhs is None:
        return "none", "equation"
    diff = sp.expand(lhs - rhs)
    symbols = diff.free_symbols
    if len(symbols) != 1:
        return "none", "equation"
    var = next(iter(symbols))
    # Calculus asks wear equations too ("dy/dx = ..."); the
    # calculus checks own those.
    if re.search(r"dy/dx|d/dx|integrat|differentiat", q, re.I):
        return "none", "equation"
    if claim is None:
        return "fail", "equation"
    # Claimed roots: the numbers in the answer, read as values
    # of the variable ("x = 2, x = 3" / "2 and 3" / "x = 5").
    roots_claimed = claim["values"]
    if not roots_claimed and claim["expr"] is not None \
            and not claim["expr"].free_symbols:
        try:
            roots_claimed = [Fraction(
                sp.nsimplify(claim["expr"], rational=True))]
        except Exception:
            roots_claimed = []
    if not roots_claimed:
        return "fail", "equation"

    def _satisfies(v):
        try:
            val = complex(diff.subs(var, sp.nsimplify(v)))
        except Exception:
            return False
        return abs(val) < 1e-6

    if not all(_satisfies(v) for v in roots_claimed):
        return "fail", "equation"
    # Completeness when SymPy can solve the extracted
    # equation outright: the claimed set must be ALL roots.
    try:
        true_roots = [r for r in sp.solve(diff, var)
                      if r.is_number]
    except Exception:
        true_roots = []
    if true_roots:
        true_vals = []
        for r in true_roots:
            try:
                true_vals.append(
                    Fraction(sp.nsimplify(r, rational=True)))
            except Exception:
                true_vals.append(Fraction(float(r)))
        if not _values_match_set(
                {"values": roots_claimed}, true_vals, rel=1e-4):
            return "fail", "equation"
    return "pass", "equation"


def _check_area_between(question, claim):
    q = str(question or "")
    if not re.search(r"area\s+between|between\s+the\s+curves|"
                     r"के\s+बीच\s+का\s+क्षेत्रफल", q, re.I):
        return "none", "area_between_curves"
    curves = []
    for seg in re.split(r"\band\b|,", q):
        m = re.search(r"y\s*=\s*(.+)$", seg.strip())
        if m:
            e = _trim_to_expr(m.group(1), from_left=False)
            if e is not None and len(e.free_symbols) <= 1:
                curves.append(e)
    if len(curves) != 2:
        return "none", "area_between_curves"
    f, g = curves
    var = (f.free_symbols | g.free_symbols)
    if len(var) != 1:
        return "none", "area_between_curves"
    var = next(iter(var))
    try:
        roots = [r for r in sp.solve(sp.expand(f - g), var)
                 if r.is_real]
    except Exception:
        roots = []
    if len(roots) < 2:
        return "none", "area_between_curves"
    roots = sorted(roots, key=lambda r: float(r))
    a, b = roots[0], roots[1]
    try:
        area = sp.integrate(f - g, (var, a, b))
        area_val = abs(float(area))
    except Exception:
        return "none", "area_between_curves"
    if not _claim_or_fail(claim):
        return "fail", "area_between_curves"
    ok = any(abs(float(v) - area_val) <= 1e-4 * max(1.0, area_val)
             for v in claim["values"])
    return ("pass" if ok else "fail"), "area_between_curves"


def _extract_calculus_target(q, patterns):
    for pat in patterns:
        m = re.search(pat, q, re.I)
        if m:
            e = _trim_to_expr(m.group(1), from_left=True)
            if e is None:
                e = _trim_to_expr(m.group(1), from_left=False)
            if e is not None:
                return e
    return None


def _check_integral(question, claim):
    q = str(question or "")
    if not re.search(r"integrat|integral|∫|समाकलन", q, re.I):
        return "none", "integral"
    if re.search(r"area\s+between", q, re.I):
        return "none", "integral"
    integrand = _extract_calculus_target(q, [
        r"integral\s+of\s+(.+?)(?:\s+with\s+respect\s+to|"
        r"\s+dx\b|[?.!,]|$)",
        r"integrate\s+(.+?)(?:\s+with\s+respect\s+to|"
        r"\s+dx\b|[?.!,]|$)",
        r"∫\s*(.+?)(?:\s*dx\b|[?.!,]|$)",
    ])
    if integrand is None or not integrand.free_symbols:
        return "none", "integral"
    var = next(iter(integrand.free_symbols))
    if claim is None or claim["expr"] is None:
        return "fail", "integral"
    anti = claim["expr"]
    if var not in anti.free_symbols:
        return "fail", "integral"
    try:
        if sp.simplify(sp.diff(anti, var) - integrand) == 0:
            return "pass", "integral"
    except Exception:
        pass
    verdict = _expr_close(sp.diff(anti, var), integrand, var)
    if verdict is None:
        return "none", "integral"
    return ("pass" if verdict else "fail"), "integral"


def _check_derivative(question, claim):
    q = str(question or "")
    if not re.search(r"derivative|differentiat|dy/dx|अवकलज", q, re.I):
        return "none", "derivative"
    if re.search(r"second\s+derivative|दूसरा\s+अवकलज", q, re.I):
        return "none", "derivative"  # v1 checks the first only
    func = _extract_calculus_target(q, [
        r"derivative\s+of\s+(.+?)(?:\s+with\s+respect\s+to|"
        r"\s+at\b|[?.!,]|$)",
        r"differentiate\s+(.+?)(?:\s+with\s+respect\s+to|"
        r"\s+at\b|[?.!,]|$)",
    ])
    if func is None or not func.free_symbols:
        return "none", "derivative"
    var = next(iter(func.free_symbols))
    if claim is None:
        return "fail", "derivative"
    true_deriv = sp.diff(func, var)
    at = re.search(r"\bat\s+(?:x\s*=\s*)?(-?\d+(?:\.\d+)?)", q)
    if at and claim["values"]:
        point = Fraction(at.group(1))
        try:
            expected = float(true_deriv.subs(var, point))
        except Exception:
            return "none", "derivative"
        ok = any(abs(float(v) - expected) <=
                 1e-4 * max(1.0, abs(expected))
                 for v in claim["values"])
        return ("pass" if ok else "fail"), "derivative"
    if claim["expr"] is None:
        return "fail", "derivative"
    try:
        if sp.simplify(claim["expr"] - true_deriv) == 0:
            return "pass", "derivative"
    except Exception:
        pass
    verdict = _expr_close(claim["expr"], true_deriv, var)
    if verdict is None:
        return "none", "derivative"
    return ("pass" if verdict else "fail"), "derivative"


def _probability_expected(q):
    """The exact probability for the standard school forms,
    or None when the question is not one of them. Deterministic
    enumeration / counting — no solver, no AI."""
    ql = " " + _dev_to_ascii(q).lower() + " "
    # --- two dice, sum or doublet (enumerate all 36) ---
    if re.search(r"two\s+dice|2\s+dice|pair\s+of\s+dice|"
                 r"दो\s+पासे", ql):
        m = re.search(r"sum\s+(?:of\s+|is\s+)?(\d+)", ql)
        if m:
            target = int(m.group(1))
            hits = sum(1 for a in range(1, 7) for b in range(1, 7)
                       if a + b == target)
            return Fraction(hits, 36)
        if "doublet" in ql or "same number" in ql:
            return Fraction(6, 36)
        return None
    # --- one die ---
    if re.search(r"\ba\s+(?:die|dice)\b|\bone\s+(?:die|dice)\b|"
                 r"एक\s+पासा", ql):
        outcomes = set(range(1, 7))
        m = re.search(r"(?:getting|get|of|आने)\s+(?:a\s+|an\s+)?"
                      r"(\d)\b", ql)
        if m:
            outcomes = {int(m.group(1))}
        elif "even" in ql or "सम" in ql:
            outcomes = {2, 4, 6}
        elif "odd" in ql or "विषम" in ql:
            outcomes = {1, 3, 5}
        elif "prime" in ql or "अभाज्य" in ql:
            outcomes = {2, 3, 5}
        elif "composite" in ql:
            outcomes = {4, 6}
        else:
            m = re.search(r"multiple\s+of\s+(\d)", ql)
            if m:
                k = int(m.group(1))
                outcomes = {n for n in outcomes if n % k == 0}
            m = re.search(r"(?:greater|more)\s+than\s+(\d)", ql)
            if m:
                outcomes = {n for n in outcomes
                            if n > int(m.group(1))}
            m = re.search(r"less\s+than\s+(\d)", ql)
            if m:
                outcomes = {n for n in outcomes
                            if n < int(m.group(1))}
        if not outcomes:
            return None
        return Fraction(len(outcomes), 6)
    # --- coins ---
    if "coin" in ql or "सिक्का" in ql or "sikka" in ql:
        if re.search(r"two\s+coins|2\s+coins|coin.*twice|"
                     r"दो\s+सिक्के", ql):
            if "at least one head" in ql or "atleast one head" in ql:
                return Fraction(3, 4)
            if "exactly one head" in ql or "one head" in ql:
                return Fraction(1, 2)
            if "two heads" in ql or "both heads" in ql:
                return Fraction(1, 4)
            return None
        if "head" in ql or "tail" in ql or "चित" in ql \
                or "पट" in ql:
            return Fraction(1, 2)
        return None
    # --- a bag of coloured balls / marbles ---
    counts = {}
    for n, colour in re.findall(
            r"(\d+)\s+(red|blue|green|black|white|yellow|pink|"
            r"orange)\b", ql):
        counts[colour] = counts.get(colour, 0) + int(n)
    if len(counts) >= 2:
        total = sum(counts.values())
        m = re.search(r"(?:is|be|being|that\s+it\s+is)\s+(?:a\s+|an\s+)?"
                      r"(red|blue|green|black|white|yellow|pink|"
                      r"orange)\b", ql)
        if m and m.group(1) in counts:
            return Fraction(counts[m.group(1)], total)
        return None
    # --- one card from a 52-card pack ---
    if "52" in ql and "card" in ql:
        if re.search(r"\bking\b|\bqueen\b|\bjack\b|\bace\b", ql):
            return Fraction(4, 52)
        if "face card" in ql:
            return Fraction(12, 52)
        if re.search(r"\bred\b", ql):
            return Fraction(26, 52)
        if re.search(r"\bblack\b", ql):
            return Fraction(26, 52)
        if re.search(r"\bheart", ql) or re.search(r"\bdiamond", ql) \
                or re.search(r"\bspade", ql) \
                or re.search(r"\bclub", ql):
            return Fraction(13, 52)
        return None
    return None


def _check_probability(question, claim):
    q = str(question or "")
    if not _is_probability_q(q):
        return "none", "probability"
    expected = _probability_expected(q)
    if expected is None:
        return "none", "probability"
    if not _claim_or_fail(claim):
        return "fail", "probability"
    # Probability claims arrive as fractions, decimals or
    # percents; extract_claim already normalised "%".
    ok = any(_close(v, expected, rel=1e-3, abs_tol=0.005)
             for v in claim["values"])
    if ok:
        # ...and no contradicting distinct value (a decimal
        # restatement is fine, a second different value is not).
        distinct = []
        for v in claim["values"]:
            if not any(_close(v, d, rel=0.02) for d in distinct):
                distinct.append(v)
        ok = len(distinct) == 1
    return ("pass" if ok else "fail"), "probability"


def _check_percent_of(question, claim):
    q = str(question or "")
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)",
                  _dev_to_ascii(q), re.I)
    if not m:
        return "none", "percent_of"
    expected = Fraction(m.group(1)) / 100 * Fraction(m.group(2))
    if not _claim_or_fail(claim):
        return "fail", "percent_of"
    return ("pass" if _values_match_single(claim, expected)
            else "fail"), "percent_of"


def _check_simple_interest(question, claim):
    q = str(question or "")
    if not re.search(r"simple\s+interest|sadharan\s+byaj|"
                     r"साधारण\s+ब्याज", q, re.I):
        return "none", "simple_interest"
    t = _dev_to_ascii(q)
    principal = None
    m = re.search(r"(?:rs\.?|rupees|₹)\s*(\d+(?:\.\d+)?)", t, re.I)
    if m:
        principal = Fraction(m.group(1))
    rate = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:per\s+annum|salana|"
                  r"वार्षिक|per\s+year)?", t, re.I)
    if m:
        rate = Fraction(m.group(1))
    years = None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:years?|yrs?|saal|साल|वर्ष)",
                  t, re.I)
    if m:
        years = Fraction(m.group(1))
    if principal is None or rate is None or years is None:
        return "none", "simple_interest"
    interest = principal * rate * years / 100
    expected = interest
    if re.search(r"\bamount\b|मिश्रधन|कुल\s+राशि", q, re.I) and \
            not re.search(r"\binterest\b|ब्याज", q, re.I):
        expected = principal + interest
    if not _claim_or_fail(claim):
        return "fail", "simple_interest"
    return ("pass" if _values_match_single(claim, expected)
            else "fail"), "simple_interest"


def _check_two_numbers(question, claim):
    q = str(question or "")
    if not re.search(r"two\s+numbers|दो\s+संख्याएँ|do\s+numbers",
                     q, re.I):
        return "none", "two_numbers"
    m_sum = re.search(r"sum\s+(?:of\s+(?:the\s+)?(?:two\s+)?"
                      r"numbers\s+)?is\s+(\d+(?:\.\d+)?)",
                      _dev_to_ascii(q), re.I)
    m_diff = re.search(r"difference\s+(?:of\s+(?:the\s+)?"
                       r"(?:two\s+)?numbers\s+)?is\s+"
                       r"(\d+(?:\.\d+)?)", _dev_to_ascii(q), re.I)
    if not m_sum or not m_diff:
        return "none", "two_numbers"
    s, d = Fraction(m_sum.group(1)), Fraction(m_diff.group(1))
    if s < d:
        return "none", "two_numbers"
    expected = [(s + d) / 2, (s - d) / 2]
    if not _claim_or_fail(claim):
        return "fail", "two_numbers"
    return ("pass" if _values_match_set(claim, expected)
            else "fail"), "two_numbers"


def _check_train_length(question, claim):
    q = str(question or "")
    if not re.search(r"train|रेलगाड़ी|ट्रेन", q, re.I):
        return "none", "train_length"
    if not re.search(r"pole|post|खंभा|खम्भा", q, re.I):
        return "none", "train_length"
    t = _dev_to_ascii(q)
    m_v = re.search(r"(\d+(?:\.\d+)?)\s*km\s*/\s*(?:hr|h|hour)",
                    t, re.I)
    m_t = re.search(r"(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|सेकंड)",
                    t, re.I)
    if not m_v or not m_t:
        return "none", "train_length"
    expected = Fraction(m_v.group(1)) * Fraction(5, 18) \
        * Fraction(m_t.group(1))
    if not _claim_or_fail(claim):
        return "fail", "train_length"
    return ("pass" if _values_match_single(claim, expected)
            else "fail"), "train_length"


def _check_divide_ratio(question, claim):
    q = str(question or "")
    if not re.search(r"divide|distribute|share|बाँट|बांट", q, re.I):
        return "none", "divide_ratio"
    t = _dev_to_ascii(q)
    m_amt = re.search(r"(?:rs\.?|rupees|₹)\s*(\d+(?:\.\d+)?)",
                      t, re.I)
    m_ratio = re.search(r"ratio[^0-9]*(\d+)\s*:\s*(\d+)"
                        r"(?:\s*:\s*(\d+))?", t, re.I)
    if not m_amt or not m_ratio:
        return "none", "divide_ratio"
    parts = [Fraction(int(g)) for g in m_ratio.groups() if g]
    total = sum(parts)
    amount = Fraction(m_amt.group(1))
    expected = [amount * p / total for p in parts]
    if not _claim_or_fail(claim):
        return "fail", "divide_ratio"
    if len(claim["values"]) != len(expected):
        return "none", "divide_ratio"  # a partial claim: unjudged
    return ("pass" if _values_match_set(claim, expected)
            else "fail"), "divide_ratio"


def _check_mensuration(question, claim):
    q = str(question or "")
    t = _dev_to_ascii(q)
    ql = t.lower()
    name = "mensuration"

    def _num_after(*pats):
        for pat in pats:
            m = re.search(pat, t, re.I)
            if m:
                return Fraction(m.group(1))
        return None

    expected = None
    tol = 0.005  # decimal rounding in a stated answer
    if "rectangle" in ql or "आयत" in ql:
        length = _num_after(r"length\s*(?:is|=)?\s*(\d+(?:\.\d+)?)",
                            r"(\d+(?:\.\d+)?)\s*(?:cm|m)?\s*long")
        breadth = _num_after(
            r"breadth\s*(?:is|=)?\s*(\d+(?:\.\d+)?)",
            r"width\s*(?:is|=)?\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*(?:cm|m)?\s*wide")
        if length is not None and breadth is not None:
            if "perimeter" in ql or "परिधि" in ql:
                expected = 2 * (length + breadth)
            elif "area" in ql or "क्षेत्रफल" in ql:
                expected = length * breadth
    elif "square" in ql or "वर्ग" in ql:
        side = _num_after(r"side\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
        if "perimeter" in ql and "area" in ql and side is None:
            per = _num_after(
                r"perimeter\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
            if per is not None:
                expected = (per / 4) ** 2
        elif side is not None:
            if "perimeter" in ql:
                expected = 4 * side
            elif "area" in ql:
                expected = side * side
    elif "circle" in ql or "वृत्त" in ql:
        radius = _num_after(r"radius\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
        if radius is None:
            dia = _num_after(
                r"diameter\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
            if dia is not None:
                radius = dia / 2
        if radius is not None:
            import math
            if "circumference" in ql or "परिधि" in ql:
                cands = [2 * math.pi * float(radius),
                         float(2 * Fraction(22, 7) * radius)]
            elif "area" in ql or "क्षेत्रफल" in ql:
                cands = [math.pi * float(radius) ** 2,
                         float(Fraction(22, 7) * radius * radius)]
            else:
                cands = []
            if cands:
                if not _claim_or_fail(claim):
                    return "fail", name
                ok = any(
                    abs(float(v) - c) <= 0.015 * max(1.0, c)
                    for v in claim["values"] for c in cands)
                return ("pass" if ok else "fail"), name
    elif "triangle" in ql or "त्रिभुज" in ql:
        base = _num_after(r"base\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
        height = _num_after(r"height\s*(?:is|=)?\s*(\d+(?:\.\d+)?)")
        if base is not None and height is not None \
                and ("area" in ql or "क्षेत्रफल" in ql):
            expected = base * height / 2
    if expected is None:
        return "none", name
    if not _claim_or_fail(claim):
        return "fail", name
    ok = any(abs(float(v) - float(expected))
             <= tol * max(1.0, float(expected))
             for v in claim["values"])
    return ("pass" if ok else "fail"), name


def _check_fraction_addsub(question, claim):
    try:
        from fallback import _fraction_ask_value
        expected = _fraction_ask_value(question)
    except Exception:
        expected = None
    if expected is None:
        return "none", "fraction_addsub"
    if not _claim_or_fail(claim):
        return "fail", "fraction_addsub"
    return ("pass" if _values_match_single(claim, expected)
            else "fail"), "fraction_addsub"


def _check_arithmetic_chain(question, claim):
    q = str(question or "")
    if not re.search(r"value\s+of|calculate|evaluate|compute|"
                     r"kitna\s+hoga|simplify", q, re.I):
        return "none", "arithmetic_chain"
    t = _dev_to_ascii(q).replace("×", "*").replace("÷", "/")
    # A spaced letter x between two numbers is multiplication
    # ("15 + 25 x 4"), the salvage layer's own convention.
    t = re.sub(r"(\d)\s+x\s+(?=\d)", r"\1 * ", t)
    m = re.search(r"(\d+(?:\.\d+)?(?:\s*[-+*/]\s*"
                  r"\d+(?:\.\d+)?)+)", t)
    if not m:
        return "none", "arithmetic_chain"
    expr = _try_parse(m.group(1))
    if expr is None or expr.free_symbols:
        return "none", "arithmetic_chain"
    try:
        expected = Fraction(sp.nsimplify(expr, rational=True))
    except Exception:
        return "none", "arithmetic_chain"
    if not _claim_or_fail(claim):
        return "fail", "arithmetic_chain"
    return ("pass" if _values_match_single(claim, expected)
            else "fail"), "arithmetic_chain"


_CHECKS = (_check_hcf_lcm, _check_equation, _check_area_between,
           _check_integral, _check_derivative, _check_probability,
           _check_percent_of, _check_simple_interest,
           _check_two_numbers, _check_train_length,
           _check_divide_ratio, _check_mensuration,
           _check_fraction_addsub, _check_arithmetic_chain)


def deterministic_check(question, result):
    """("pass"|"fail"|"none", check_name): the first check
    that APPLIES to this question decides. Any check raising
    is treated as that check not applying — a verifier bug
    must never accuse an answer."""
    claim = extract_claim((result or {}).get("answer"), question)
    for check in _CHECKS:
        try:
            verdict, name = check(question, claim)
        except Exception:
            continue
        if verdict != "none":
            return verdict, name
    return "none", None


# ---------------------------------------------------------------------------
# The rejection log — the Wave 90 pattern, for verification failures
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ai_verify_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    question_norm TEXT NOT NULL,
    question_text TEXT NOT NULL,
    leg           TEXT,
    claimed       TEXT,
    check_name    TEXT,
    hits          INTEGER NOT NULL DEFAULT 1,
    first_seen    INTEGER NOT NULL,
    last_seen     INTEGER NOT NULL,
    UNIQUE(question_norm, leg, check_name)
)
"""

_TEXT_CAP = 500
_CLAIM_CAP = 200


def _db_path():
    from accounts import db_path
    return db_path()


def _normalise(text):
    try:
        from bank import normalise_question
        return normalise_question(text)
    except Exception:
        import unicodedata
        t = unicodedata.normalize("NFC", str(text or "")).lower()
        return re.sub(r"\s+", " ", t).strip()


def log_rejection(question, leg, claimed, check_name):
    """Record one rejected AI candidate. Never raises; the
    record is observational only (question text + the AI's
    own claimed value + which check failed — no user data)."""
    try:
        norm = _normalise(question)
        if not norm:
            return False
        now = int(time.time())
        conn = sqlite3.connect(_db_path(), timeout=2.0)
        try:
            conn.execute(_SCHEMA)
            conn.execute(
                "INSERT INTO ai_verify_log (question_norm,"
                " question_text, leg, claimed, check_name,"
                " hits, first_seen, last_seen) VALUES"
                " (?, ?, ?, ?, ?, 1, ?, ?)"
                " ON CONFLICT(question_norm, leg, check_name)"
                " DO UPDATE SET hits = hits + 1,"
                " last_seen = excluded.last_seen,"
                " claimed = excluded.claimed",
                (norm, str(question or "").strip()[:_TEXT_CAP],
                 leg, str(claimed or "")[:_CLAIM_CAP],
                 check_name, now, now))
            conn.commit()
        finally:
            conn.close()
        return True
    except Exception:
        return False


def _read_rows(db_path=None):
    path = db_path or _db_path()
    if not os.path.isfile(path):
        return []
    try:
        conn = sqlite3.connect(path, timeout=2.0)
        try:
            conn.row_factory = sqlite3.Row
            found = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table'"
                " AND name='ai_verify_log'").fetchone()
            if not found:
                return []
            rows = conn.execute(
                "SELECT question_norm, question_text, leg,"
                " claimed, check_name, hits, first_seen,"
                " last_seen FROM ai_verify_log ORDER BY"
                " hits DESC, last_seen DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    except Exception:
        return []


def all_rejections(db_path=None):
    """Every recorded rejection (owner tooling / tests)."""
    return _read_rows(db_path=db_path)


# ---------------------------------------------------------------------------
# The chain gate
# ---------------------------------------------------------------------------

_NUMBER_WORDS = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|thirty|forty|"
    r"fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"twice|thrice|dozen)\b", re.I)


def _expects_value(question):
    """True when the question plainly asks for a computed
    value (it carries numbers — digits or number words, the
    ages word problems spell theirs out — and is not a
    maths-meta ask): an answer to such a question that
    states NO value has not answered it and cannot be
    verified."""
    q = str(question or "")
    if not any(ch.isdigit() for ch in _dev_to_ascii(q)) \
            and not _NUMBER_WORDS.search(q):
        return False
    try:
        from maths_meta import is_meta_shaped
        if is_meta_shaped(q):
            return False
    except Exception:
        pass
    return True


def _mark(result, method, check=None):
    out = dict(result)
    out["ai_verification"] = method
    if check:
        out["ai_verify_check"] = check
    return out


def _consensus_winner(question, valued):
    """The earliest leg result whose claim agrees with a
    later leg's claim, or None. `valued` is a list of
    (leg_name, result, claim) in chain order."""
    for i in range(len(valued)):
        for j in range(i + 1, len(valued)):
            if claims_agree(question, valued[i][2], valued[j][2]):
                return valued[i][1]
    return None


def verify_chain(question, legs, lang=None, student_class=None,
                 on_rejected=None):
    """Run the AI legs (a list of (name, callable) in chain
    order; each callable returns a shaped result dict or
    None) behind the verification gate. Returns the result
    to serve, or None when nothing servable was produced —
    the caller then falls through to its honest outcome.

    On TOTAL failure with at least one rejection, on_rejected
    (when given) is called as on_rejected(question, rejected)
    with rejected = [{"leg", "result", "claim", "check"}...]
    — the Wave 134 deep-solve seam. Never raises."""
    holder = {"first": None}
    try:
        return _verify_chain(question, legs, on_rejected,
                             holder)
    except Exception:
        # Catastrophe insurance: an answer already in hand is
        # served exactly as pre-Wave-133 rather than breaking
        # the chain; with nothing in hand, the honest outcome
        # stands.
        return holder["first"]


def _verify_chain(question, legs, on_rejected, holder):
    if not _enabled():
        for _name, call in legs:
            result = _safe_call(call)
            if result is not None:
                return result
        return None
    rejected = []
    valued = []   # (leg, result, claim): sane, no det verdict
    for name, call in legs:
        result = _safe_call(call)
        if result is None:
            continue
        if holder["first"] is None:
            holder["first"] = result
        ok, sanity_name = sanity_check(question, result)
        if not ok:
            rejected.append({"leg": name, "result": result,
                             "claim": result.get("answer"),
                             "check": sanity_name})
            continue
        verdict, check = deterministic_check(question, result)
        if verdict == "pass":
            _flush_rejections(question, rejected)
            return _mark(result, "deterministic", check)
        if verdict == "fail":
            rejected.append({"leg": name, "result": result,
                             "claim": result.get("answer"),
                             "check": check})
            continue
        if not _expects_value(question):
            # A prose question (history / advice / explanation
            # — the Wave 111 meta flow): its answer carries no
            # value claim for arithmetic to judge, however many
            # incidental numbers (a year, a count) its prose
            # mentions. Served exactly as before; no other leg
            # is consulted (quota discipline).
            _flush_rejections(question, rejected)
            return result
        claim = extract_claim(result.get("answer"), question)
        if claim is None:
            # The question plainly asks for a value and this
            # answer states none — unverifiable, so it cannot
            # be served; the next leg gets its chance.
            rejected.append({"leg": name, "result": result,
                             "claim": result.get("answer"),
                             "check": "no_claim"})
            continue
        valued.append((name, result, claim))
        winner = _consensus_winner(question, valued)
        if winner is not None:
            _flush_rejections(question, rejected)
            return _mark(winner, "consensus", "cross_leg")
    if len(valued) == 1:
        # Exactly one leg produced an unjudged claim (the
        # others are unconfigured, down, or were disproven
        # by a check): the degraded single-opinion path —
        # served as pre-Wave-133, marked honestly, and never
        # promoted in the Live Bank.
        _flush_rejections(question, rejected)
        return _mark(valued[0][1], "single", "single_leg")
    if len(valued) >= 2:
        # Legs answered but no two agreed — no majority, so
        # nothing is verified. The disagreeing candidates
        # join the rejection bundle (check "no_consensus"):
        # Wave 134's deep-solve stage gets their methods too.
        for name, result, _claim in valued:
            rejected.append({"leg": name, "result": result,
                             "claim": result.get("answer"),
                             "check": "no_consensus"})
    _flush_rejections(question, rejected)
    if rejected and on_rejected is not None:
        try:
            on_rejected(question, rejected)
        except Exception:
            pass
    return None


def _safe_call(call):
    try:
        result = call()
    except Exception:
        return None
    return result if isinstance(result, dict) else None


def _flush_rejections(question, rejected):
    for rec in rejected:
        log_rejection(question, rec["leg"], rec["claim"],
                      rec["check"])


__all__ = ["verify_chain", "deterministic_check",
           "sanity_check", "extract_claim", "extract_values",
           "claims_agree", "log_rejection", "all_rejections"]
