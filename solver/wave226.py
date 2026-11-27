"""Wave 226 (AI-first conversion): three strict solver gates
for shapes the external audit + Suraj's screenshots proved
were mis-served or unserved, each verified against the main
tree on 27 Nov 2026:

  * BARE FACTORIAL asks — "7! kitna hota hai" was served the
    bare operand 7 by the arithmetic single-number path and
    "(-3)!" was served -3: the only factorial handler
    (statistics._counting) matches whole-string / "factorial
    of N" forms, so a factorial inside a sentence fell
    through. This gate fires ONLY when the question is
    essentially one factorial and nothing else (one "!"
    token; the residue is pure ask-filler) — expressions
    like "5! + 3!" keep their existing (correct) parse.
    A negative base gets the defined-nahi reply; N > 100
    gets the bahut-bada reply instead of a thousand-digit
    dump (audit: "1000000!" was served the operand itself).

  * INTEREST FORMULA shape — "simple interest P=1000 R=5
    T=2" was grabbed by the equation solver and served
    "P = 1000": the prose handler (applied._simple_interest)
    owns "on Rs X at Y% for Z years" but not the P=/R=/T=
    assignment dress students copy from their notebooks.
    This gate reads the three assignments (letters or the
    words principal/rate/time) when the question says
    "interest", and computes SI (or CI for "compound")
    with the formula shown.

  * BARE LOG VALUES — "ln(e)" and "log 1000" were served
    unevaluated ("log(e)", "log(1000)") by the generic
    evaluate path: parse_expression reads "e" as a free
    symbol and SymPy leaves log(1000) symbolic, while the
    dedicated log_value handler owns only explicit-base
    and "value of" forms. This gate owns the whole-question
    bare forms: ln = base e, bare log = base 10 (the school
    convention the Wave 58 block already uses).

Every gate is a strict full-shape match and returns None on
any doubt, so the flow below is then exactly the pre-Wave-226
one. The router gate sits with the other wave gates, before
the main dispatch that mis-served these shapes.
"""
import math
import re

import sympy as sp

from .expression_parser import fmt_num

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")

# ---------------------------------------------------------------------------
# Bare factorial
# ---------------------------------------------------------------------------

_FILLER_LATIN = {
    "what", "is", "the", "value", "of", "find", "calculate",
    "compute", "evaluate", "solve", "batao", "bataao",
    "bataye", "kitna", "kitne", "kitni", "hota", "hoti",
    "hai", "hain", "ka", "ki", "ke", "answer", "jawab",
    "please", "plz", "tell", "me", "give", "nikaalo",
    "nikalo", "karo", "kar", "do", "iska", "iski", "iske",
    "kya", "hoga", "hogi", "ho", "please",
}
_FILLER_DEV = {
    "कितना", "कितने", "कितनी", "होता", "होती", "है", "हैं",
    "बताओ", "बताइए", "का", "की", "के", "क्या", "निकालो",
    "मान", "होगा",
}

_BANG_RE = re.compile(
    r"\(\s*(-?\d+)\s*\)\s*!|(?<![\d.])(\d+)\s*!|-\s*(\d+)\s*!")


def _hinglish_flavoured(text):
    t = str(text or "")
    if any("ऀ" <= ch <= "ॿ" for ch in t):
        return True
    return bool(re.search(
        r"\b(kitna|kitne|hota|hai|batao|chahiye|nikaal\w*|"
        r"jawab|iska|kya)\b", t.lower()))


def _factorial(question):
    q = str(question or "").translate(_DEV)
    if q.count("!") != 1:
        return None
    m = _BANG_RE.search(q)
    if not m:
        return None
    if m.group(1) is not None:
        n = int(m.group(1))
    elif m.group(2) is not None:
        n = int(m.group(2))
    else:
        n = -int(m.group(3))
    residue = (q[:m.start()] + " " + q[m.end():]).strip()
    if "factorial" in residue.lower():
        # Word forms belong to statistics._counting.
        return None
    if re.search(r"\d", residue):
        return None
    for tok in re.findall(r"[A-Za-z]+", residue.lower()):
        if tok not in _FILLER_LATIN:
            return None
    for tok in re.findall(r"[ऀ-ॿ]+", residue):
        if tok not in _FILLER_DEV:
            return None
    hing = _hinglish_flavoured(question)
    if n < 0:
        if hing:
            line = (f"({n})! defined nahi hota — factorial "
                    f"sirf 0 aur positive whole numbers ka "
                    f"hota hai (0! = 1, 1! = 1, 2! = 2, "
                    f"3! = 6, ...). Negative number ka "
                    f"factorial school maths me defined "
                    f"nahi hai.")
        else:
            line = (f"({n})! is not defined — factorial is "
                    f"only for 0 and positive whole numbers "
                    f"(0! = 1, 1! = 1, 2! = 2, 3! = 6, ...). "
                    f"A negative number has no factorial in "
                    f"school maths.")
        return {"type": "wave226", "op": "factorial_undefined",
                "answer": line,
                "steps": ["n! = n × (n − 1) × … × 2 × 1, "
                          "sirf n ≥ 0 ke liye." if hing else
                          "n! = n × (n − 1) × … × 2 × 1, "
                          "defined only for n ≥ 0."]}
    if n > 100:
        if hing:
            line = (f"{n}! bahut bada hai — itna bada "
                    f"factorial likha nahi jata (100! me hi "
                    f"158 digits hote hain). Chhota number "
                    f"bhejo, main turant nikal dunga.")
        else:
            line = (f"{n}! is far too big to write out — "
                    f"factorials grow extremely fast (100! "
                    f"itself has 158 digits). Send a smaller "
                    f"number and I'll work it out at once.")
        return {"type": "wave226", "op": "factorial_too_big",
                "answer": line, "steps": []}
    value = math.factorial(n)
    if n <= 1:
        steps = [f"{n}! = 1 (paribhasha se — 0! aur 1! dono "
                 f"1 hote hain)." if hing else
                 f"{n}! = 1 by definition (both 0! and 1! "
                 f"equal 1)."]
    elif n <= 12:
        expansion = " × ".join(str(k) for k in range(n, 0, -1))
        steps = [
            f"{n}! ka matlab hai {n} se 1 tak ki saari "
            f"sankhyao ka gunakar." if hing else
            f"{n}! means the product of all whole numbers "
            f"from {n} down to 1.",
            f"{n}! = {expansion} = {value}",
        ]
    else:
        steps = [f"{n}! = {n} × {n - 1} × … × 2 × 1",
                 f"= {value}"]
    return {"type": "wave226", "op": "factorial",
            "answer": str(value), "value": value,
            "steps": steps}


# ---------------------------------------------------------------------------
# Interest, formula dress (P= / R= / T= assignments)
# ---------------------------------------------------------------------------

_NUM = r"(\d+(?:\.\d+)?)"
_RS = r"(?:rs\.?|₹|inr)?\s*"


def _assign(text, letter_pat, word_pat):
    m = re.search(letter_pat, text) or re.search(word_pat, text)
    return float(m.group(1)) if m else None


def _interest(question):
    q = str(question or "").translate(_DEV)
    t = q.lower()
    if "interest" not in t and "ब्याज" not in q \
            and "byaj" not in t:
        return None
    P = _assign(t, r"\bp\s*=\s*" + _RS + _NUM,
                r"\bprincipal\s*(?:=|is)\s*" + _RS + _NUM)
    R = _assign(t, r"\br\s*=\s*" + _NUM,
                r"\brate\s*(?:=|is)\s*" + _NUM)
    T = _assign(t, r"\bt\s*=\s*" + _NUM,
                r"\btime\s*(?:=|is)\s*" + _NUM)
    if P is None or R is None or T is None:
        return None
    if P <= 0 or R < 0 or T <= 0:
        return None
    ps, rs, ts = fmt_num(P), fmt_num(R), fmt_num(T)
    if "compound" in t or "चक्रवृद्धि" in q:
        amount = P * (1 + R / 100.0) ** T
        ci = amount - P
        steps = [
            f"Amount = P × (1 + R/100)^T",
            f"= {ps} × (1 + {rs}/100)^{ts} = "
            f"Rs {fmt_num(amount)}",
            f"Compound Interest = Amount − Principal = "
            f"{fmt_num(amount)} − {ps} = Rs {fmt_num(ci)}",
        ]
        return {"type": "wave226", "op": "compound_interest",
                "answer": f"Rs {fmt_num(ci)}", "value": ci,
                "steps": steps}
    si = P * R * T / 100.0
    steps = [
        "Simple Interest = (P × R × T) / 100",
        f"= ({ps} × {rs} × {ts}) / 100",
        f"= Rs {fmt_num(si)}",
    ]
    return {"type": "wave226", "op": "simple_interest",
            "answer": f"Rs {fmt_num(si)}", "value": si,
            "steps": steps}


# ---------------------------------------------------------------------------
# Bare log / ln values
# ---------------------------------------------------------------------------

_LEAD_FILLER = re.compile(
    r"^\s*(?:what\s+is|find|calculate|compute|evaluate|"
    r"the\s+value\s+of|value\s+of|solve|get)\s+", re.I)

_ARG = r"(e\s*\^\s*\d+|e|\d+(?:\.\d+)?)"


def _log_arg_value(raw):
    raw = raw.replace(" ", "")
    if raw == "e":
        return sp.E, "e"
    m = re.fullmatch(r"e\^(\d+)", raw)
    if m:
        return sp.E ** int(m.group(1)), raw
    return sp.Rational(raw).limit_denominator(), raw


def _logs(question):
    q = str(question or "").translate(_DEV).strip()
    t = q
    for _ in range(2):
        t2 = _LEAD_FILLER.sub("", t)
        if t2 == t:
            break
        t = t2.strip()
    t = t.rstrip("?.!").strip().lower()
    m = re.fullmatch(r"ln\s*\(\s*" + _ARG + r"\s*\)", t) \
        or re.fullmatch(r"ln\s+" + _ARG, t)
    base = None
    if m:
        base = sp.E
        bname = "e"
    else:
        m = re.fullmatch(r"log\s*\(\s*" + _ARG + r"\s*\)", t) \
            or re.fullmatch(r"log\s+" + _ARG, t)
        if m:
            base = 10
            bname = "10"
    if not m:
        return None
    val, vname = _log_arg_value(m.group(1))
    res = sp.log(val, base)
    exact = sp.nsimplify(res, rational=True)
    if exact.is_Integer or exact.is_Rational:
        ans = str(exact)
        steps = [
            f"log base {bname} of {vname} asks: {bname} "
            f"raised to what power gives {vname}?",
            f"{bname}^{ans} = {vname}, so the answer is "
            f"{ans}.",
        ]
        if base == sp.E:
            steps.insert(0, "ln means log with base e "
                            "(the natural log).")
        return {"type": "wave226", "op": "log_value",
                "answer": ans, "value": float(res),
                "steps": steps}
    approx = round(float(res), 6)
    ans = fmt_num(approx)
    steps = [
        f"log base {bname} of {vname} has no exact whole "
        f"value.",
        f"= ln({vname}) / ln({bname}) ≈ {ans}",
    ]
    if base == sp.E:
        steps.insert(0, "ln means log with base e "
                        "(the natural log).")
    return {"type": "wave226", "op": "log_value",
            "answer": ans, "value": float(res), "steps": steps}


# ---------------------------------------------------------------------------

def solve_wave226(question):
    """Wave 226 gates, in order. None on any doubt."""
    for gate in (_factorial, _interest, _logs):
        try:
            out = gate(question)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


__all__ = ["solve_wave226"]
