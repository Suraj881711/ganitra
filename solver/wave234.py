"""Wave 234 (maths quality — exact forms + coverage gaps):
strict full-shape gates for the families the external audit
proved were mis-served or unserved, each reproduced against
the live tree on 28 Nov 2026 before being fixed:

  * WORDED SQUARE-OF-A-NUMBER — "ek sankhya ka varg 144
    hai", "a number's square is 144", "kisi sankhya ka
    square 144 hai" all fell to the not-found line. The
    answer is x = ±√K with the reason (squaring removes the
    sign); the sibling "side of a square whose area is K"
    dress (which Wave 206's gate misses when a unit rides
    along) serves the POSITIVE root only, because a length
    cannot be negative.

  * WORDED FACTORIAL — "5 factorial" and "What is 5
    factorial?" fell through (statistics._counting owns
    "factorial of N" / "N ka factorial" / "factorial N" —
    those dresses are deliberately NOT claimed here). The
    value with its expansion, exactly as the owned forms
    serve it.

  * ABSOLUTE-VALUE EQUATIONS — "|x - 2| = 3" was
    not-found; the modulus family had no solver at all.
    |A| = k splits into A = k / A = −k; k < 0 has no
    solution because a modulus is never negative.

  * DECIMAL -> FRACTION dresses — junior.decimal_fraction
    owns "0.75 as a fraction" but the router never reaches
    junior for "convert 0.75 to fraction" (an earlier layer
    errors out on the sentence) and junior's patterns miss
    "0.75 to fraction" / "0.75 ko fraction me badlo"
    entirely. This gate owns the full-shape dresses and
    serves junior's own answer format.

  * NEGATIVE SQUARE ROOTS — "sqrt(-4)" was not-found,
    "square root of -4" served a concept card with no
    answer, and "-4 ka square root" served 2 (the minus
    silently dropped by applied's operand grammar — that
    grammar is now guarded in applied.py too). Here:
    √(−N) = √N · i with the school explanation.

  * UNDEFINED-WHY — "1/0 kyun undefined hota hai",
    "0/0 kitna hota hai", "log 0" were not-found (one
    dress was even served a zero-history card by the
    concept layer). Each atom gets the real reason:
    a/0 would need a = 0 × c; 0/0 fits EVERY c, so no
    single answer exists; 10^x never reaches 0.

  * WORDED-OPERATOR ALGEBRA — "x squared minus 4 solve
    karo" was not-found and "Solve x squared minus 4"
    served a letter-product of the words themselves
    (every word read as variables). The words convert to
    symbols (squared -> ^2, minus -> -, plus -> +,
    times -> *, divided by -> /, equals -> =) and the
    clean algebra is then solved for real.

  * DEVANAGARI NUMBER WORDS — "दो जमा तीन" served the
    same letter-product garbage (the parser read the
    Devanagari words as symbols). Number words एक..बीस
    with जमा / घटा / गुना / भाग evaluate with proper
    precedence.

  * CHECK / VERDICT asks — "2 + 2 = 5 sahi hai?" was
    not-found; "verify 2 + 2 = 4" solved for the letter
    e of "verify". A stated identity between two constant
    sides gets a verdict: sahi (with the common value) or
    galat (with the corrected statement).

  * BARE ROOT ATOMS — "sqrt(50)" served the decimal
    7.07107 from the arithmetic evaluate path. A question
    that is ONE root atom serves the exact surd first:
    "5√2 ≈ 7.0711" (the word forms live in
    exponents_logs.nth_root, which now renders the same
    way; general expressions keep the evaluate path's
    established decimal behaviour).

Every gate is a strict full-shape match and returns None
on any doubt, so everything else flows exactly as before.
The router gate sits with the other wave gates (after
Wave 226, before the main dispatch that mis-serves these
shapes); fallback consults it at the same point as the
Wave 226 gate, for the starved-budget path.
"""
import math
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import approx_str, fmt, fmt_exact, \
    fmt_num, parse_expression

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_FILLER_LATIN = {
    "what", "is", "the", "value", "of", "find", "calculate",
    "compute", "evaluate", "solve", "batao", "bataao",
    "bataye", "kitna", "kitne", "kitni", "hota", "hoti",
    "hai", "hain", "ka", "ki", "ke", "answer", "jawab",
    "please", "plz", "tell", "me", "give", "nikaalo",
    "nikalo", "karo", "kar", "do", "iska", "iski", "iske",
    "kya", "hoga", "hogi", "ho", "a", "an", "number",
    "sankhya", "woh", "wo", "whose", "find",
}
_FILLER_DEV = {
    "कितना", "कितने", "कितनी", "होता", "होती", "है", "हैं",
    "बताओ", "बताइए", "का", "की", "के", "क्या", "निकालो",
    "मान", "होगा", "संख्या", "वह",
}


def _hinglish_flavoured(text):
    t = str(text or "")
    if any("ऀ" <= ch <= "ॿ" for ch in t):
        return True
    return bool(re.search(
        r"\b(kitna|kitne|hota|hai|batao|chahiye|nikaal\w*|"
        r"jawab|iska|kya|kyun|kyon|sankhya|varg|karn|karo|"
        r"samjhao)\b",
        t.lower()))


def _residue_is_filler(text):
    """True when every token of `text` is ask-filler."""
    for tok in re.findall(r"[A-Za-z]+", str(text).lower()):
        if tok not in _FILLER_LATIN:
            return False
    for tok in re.findall(r"[ऀ-ॿ]+", str(text)):
        if tok not in _FILLER_DEV:
            return False
    if re.search(r"\d", str(text)):
        return False
    return True


def _result(op, answer, steps, value=None):
    out = {"type": "wave234", "op": op, "answer": answer,
           "steps": steps}
    if value is not None:
        out["value"] = value
    return out


# ---------------------------------------------------------------------------
# Worded square-of-a-number -> ± roots (Item 2)
# ---------------------------------------------------------------------------

_SQ_NUM_RES = [
    r"(?:the\s+)?square\s+of\s+a\s+number\s+is\s+"
    r"(-?\d+(?:\.\d+)?)",
    r"a\s+number[’']?s\s+square\s+is\s+(-?\d+(?:\.\d+)?)",
    r"(?:the\s+)?number\s+whose\s+square\s+is\s+"
    r"(-?\d+(?:\.\d+)?)",
    r"(?:ek\s+|kisi\s+)?sankhya\s+ka\s+(?:varg|square)\s+"
    r"(-?\d+(?:\.\d+)?)\s+hai",
    r"jiska\s+(?:varg|square)\s+(-?\d+(?:\.\d+)?)\s+hai",
    r"(?:किसी\s+|एक\s+)?संख्या\s+का\s+वर्ग\s+"
    r"(-?\d+(?:\.\d+)?)\s+है",
    r"जिसका\s+वर्ग\s+(-?\d+(?:\.\d+)?)\s+है",
]


def _number_square(question):
    q = str(question or "").translate(_DEV_DIGITS)
    hing = _hinglish_flavoured(question)
    for pat in _SQ_NUM_RES:
        m = re.search(pat, q, flags=re.I)
        if not m:
            continue
        residue = q[:m.start()] + " " + q[m.end():]
        if not _residue_is_filler(residue):
            continue
        k = float(m.group(1))
        ks = fmt_num(k)
        if k < 0:
            if hing:
                return _result(
                    "number_square",
                    f"Koi real sankhya nahi hai — kisi bhi "
                    f"sankhya ka varg {ks} nahi ho sakta.",
                    [f"Varg (square) hamesha 0 ya positive "
                     f"hota hai: 3² = 9, (−3)² = 9, 0² = 0.",
                     f"Isliye jis sankhya ka varg {ks} ho, "
                     f"aisi koi real sankhya nahi hai."])
            return _result(
                "number_square",
                f"No real number has square {ks}.",
                ["A square is always 0 or positive: "
                 "3² = 9, (−3)² = 9, 0² = 0.",
                 f"So no real number has square {ks}."])
        root = sp.sqrt(sp.Rational(k).limit_denominator())
        if root.is_Integer:
            r = int(root)
            if hing:
                steps = [
                    f"Sankhya ko x mano: x² = {ks}.",
                    f"x = ±√{ks} = ±{r}.",
                    f"Karan: {r}² = {ks} aur (−{r})² = {ks} "
                    f"bhi hota hai — varg karne par minus "
                    f"gayab ho jata hai, isliye dono jawab "
                    f"aate hain.",
                ]
                return _result("number_square",
                               f"x = ±{r}", steps, float(r))
            steps = [
                f"Let the number be x: x² = {ks}.",
                f"x = ±√{ks} = ±{r}.",
                f"Why both: {r}² = {ks} and (−{r})² = {ks} "
                f"too — squaring removes the sign, so both "
                f"roots count.",
            ]
            return _result("number_square", f"x = ±{r}",
                           steps, float(r))
        exact = fmt_exact(root)
        approx = approx_str(root)
        if hing:
            steps = [
                f"Sankhya ko x mano: x² = {ks}.",
                f"x = ±√{ks} = ±{exact} ≈ ±{approx}.",
                "Varg karne par minus gayab ho jata hai, "
                "isliye + aur − dono jawab aate hain.",
            ]
            return _result("number_square",
                           f"x = ±{exact} ≈ ±{approx}",
                           steps, float(root))
        steps = [
            f"Let the number be x: x² = {ks}.",
            f"x = ±√{ks} = ±{exact} ≈ ±{approx}.",
            "Squaring removes the sign, so both the + and "
            "− roots count.",
        ]
        return _result("number_square",
                       f"x = ±{exact} ≈ ±{approx}",
                       steps, float(root))
    return None


# ---------------------------------------------------------------------------
# Side of a square from its area -> positive root only
# ---------------------------------------------------------------------------

def _square_side_from_area(question):
    q = str(question or "").translate(_DEV_DIGITS)
    hing = _hinglish_flavoured(question)
    m = re.search(
        r"side\s+of\s+a\s+square\s+whose\s+area\s+is\s+"
        r"(\d+(?:\.\d+)?)\s*(cm\^?2|cm2|m\^?2|m2|sq\s*cm|"
        r"sq\s*m|square\s*cm)?", q, flags=re.I) or \
        re.search(
        r"side\s+of\s+a\s+square\s+with\s+area\s+"
        r"(\d+(?:\.\d+)?)\s*(cm\^?2|cm2|m\^?2|m2|sq\s*cm|"
        r"sq\s*m|square\s*cm)", q, flags=re.I)
    if not m:
        return None
    residue = q[:m.start()] + " " + q[m.end():]
    if not _residue_is_filler(residue):
        return None
    area = float(m.group(1))
    unit = (m.group(2) or "").strip().lower().replace(
        "2", "²").replace("^²", "²")
    # the side is a LENGTH: an area unit maps to its length
    unit = {"cm²": "cm", "m²": "m", "sq cm": "cm",
            "sq m": "m", "square cm": "cm"}.get(unit, unit)
    root = sp.sqrt(sp.Rational(area).limit_denominator())
    asq = fmt_num(area)
    if root.is_Integer:
        r = int(root)
        ans = f"{r}" + (f" {unit}" if unit else "")
        if hing:
            steps = [
                f"Square ka area = side × side = {asq}.",
                f"Side = √{asq} = {r}.",
                "Side ek lambai hai — lambai negative nahi "
                "hoti, isliye sirf positive root liya "
                "jata hai.",
            ]
        else:
            steps = [
                f"Area of a square = side × side = {asq}.",
                f"Side = √{asq} = {r}.",
                "A side is a length — a length cannot be "
                "negative, so only the positive root is "
                "taken.",
            ]
        return _result("side_from_area", ans, steps, float(r))
    exact = fmt_exact(root)
    approx = approx_str(root)
    ans = f"{exact} ≈ {approx}" + (f" {unit}" if unit else "")
    steps = [
        f"Area of a square = side × side = {asq}.",
        f"Side = √{asq} = {exact} ≈ {approx}.",
        "A side is a length, so only the positive root "
        "is taken.",
    ]
    return _result("side_from_area", ans, steps, float(root))


# ---------------------------------------------------------------------------
# Worded factorial (Item 3) — only the dresses statistics misses
# ---------------------------------------------------------------------------

def _worded_factorial(question):
    q = str(question or "").translate(_DEV_DIGITS)
    if "factorial" not in q.lower():
        return None
    if re.search(r"factorial\s+of\s+\d", q, flags=re.I):
        return None  # statistics._counting owns this dress
    if re.search(r"\d\s+ka\s+factorial", q, flags=re.I):
        return None  # owned too
    m = re.search(r"(\d+)\s+factorial\b", q, flags=re.I) or \
        re.search(r"\bfactorial\s+(\d+)", q, flags=re.I)
    if not m:
        return None
    residue = q[:m.start()] + " " + q[m.end():]
    if not _residue_is_filler(residue):
        return None
    n = int(m.group(1))
    hing = _hinglish_flavoured(question)
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
        return _result("factorial_too_big", line, [])
    value = math.factorial(n)
    if n <= 1:
        steps = [f"{n}! = 1 (paribhasha se — 0! aur 1! "
                 f"dono 1 hote hain)." if hing else
                 f"{n}! = 1 by definition (both 0! and 1! "
                 f"equal 1)."]
    elif n <= 12:
        expansion = " × ".join(str(k) for k in range(n, 0, -1))
        steps = [f"{n}! = {expansion}", f"= {value}"]
    else:
        steps = [f"{n}! = {n} × {n - 1} × … × 2 × 1",
                 f"= {value}"]
    return _result("factorial", str(value), steps, value)


# ---------------------------------------------------------------------------
# Absolute-value equations (Item 4a)
# ---------------------------------------------------------------------------

def _abs_equation(question):
    q = str(question or "").translate(_DEV_DIGITS)
    hing = _hinglish_flavoured(question)
    inner = rhs = None
    m = re.search(r"\|([^|]+)\|\s*=\s*(-?\d+(?:\.\d+)?)", q)
    if m:
        inner, rhs = m.group(1), float(m.group(2))
        residue = q[:m.start()] + " " + q[m.end():]
        if not _residue_is_filler(residue):
            return None
    else:
        m = re.search(r"(-?\d+(?:\.\d+)?)\s*=\s*\|([^|]+)\|", q)
        if m:
            rhs, inner = float(m.group(1)), m.group(2)
            residue = q[:m.start()] + " " + q[m.end():]
            if not _residue_is_filler(residue):
                return None
        else:
            m = re.search(
                r"modulus\s+(?:of\s+)?(.+?)\s*(?:equals|"
                r"is\s+equal\s+to|=)\s*(-?\d+(?:\.\d+)?)",
                q, flags=re.I)
            if not m:
                return None
            inner = _words_to_symbols(m.group(1))
            rhs = float(m.group(2))
            residue = q[:m.start()] + " " + q[m.end():]
            if not _residue_is_filler(residue):
                return None
    try:
        expr = parse_expression(inner)
    except Exception:
        return None
    if len(expr.free_symbols) != 1:
        return None
    var = list(expr.free_symbols)[0]
    poly = sp.Poly(expr, var)
    if poly is None or poly.degree() != 1:
        return None
    a = poly.nth(1)
    b = poly.nth(0)
    if a == 0:
        return None
    ks = fmt_num(rhs)
    disp = fmt(expr)
    if rhs < 0:
        if hing:
            return _result(
                "abs_equation",
                "Koi hal nahi hai (no solution).",
                [f"|{disp}| ka matlab hai 0 se doori — "
                 f"doori kabhi negative nahi hoti.",
                 f"Isliye |{disp}| = {ks} kabhi ho hi "
                 f"nahi sakta."])
        return _result(
            "abs_equation",
            "No solution.",
            [f"|{disp}| means a distance from 0 — a "
             f"distance is never negative.",
             f"So |{disp}| = {ks} can never happen."])
    s_plus = sp.nsimplify((-b + rhs) / a)
    s_minus = sp.nsimplify((-b - rhs) / a)
    sols = sorted({s_plus, s_minus}, key=lambda s: float(s))
    sol_txt = ", ".join(f"{var} = {fmt(s)}" for s in sols)
    if hing:
        steps = [
            f"|{disp}| = {ks} ka matlab: andar wali cheez "
            f"ya to {ks} hai ya −{ks} hai.",
            f"Pehla case: {disp} = {ks} → {var} = "
            f"{fmt(s_plus)}.",
        ]
        if len(sols) > 1:
            steps.append(
                f"Doosra case: {disp} = −{ks} → {var} = "
                f"{fmt(s_minus)}.")
    else:
        steps = [
            f"|{disp}| = {ks} means the inside is either "
            f"{ks} or −{ks}.",
            f"Case 1: {disp} = {ks} → {var} = "
            f"{fmt(s_plus)}.",
        ]
        if len(sols) > 1:
            steps.append(
                f"Case 2: {disp} = −{ks} → {var} = "
                f"{fmt(s_minus)}.")
    return _result("abs_equation", sol_txt, steps)


# ---------------------------------------------------------------------------
# Decimal -> fraction dresses junior misses (Item 4b)
# ---------------------------------------------------------------------------

_DEC_FRAC_RES = [
    r"(?:convert|write|change|express|turn)\s+"
    r"(\d+\.\d+)\s+(?:to|into|as)\s+(?:an?\s+)?fraction",
    r"(\d+\.\d+)\s+to\s+fraction",
    r"(\d+\.\d+)\s+ko\s+fraction\s+me(?:in)?\s+"
    r"(?:badlo|banao|likho)",
    r"(\d+\.\d+)\s+ka\s+fraction",
]


def _decimal_fraction(question):
    q = str(question or "").translate(_DEV_DIGITS)
    text = None
    for pat in _DEC_FRAC_RES:
        m = re.fullmatch(r"\s*(?:please\s+)?(?:" + pat +
                         r")\s*[.?!]*\s*", q, flags=re.I)
        if m:
            text = m.group(1)
            break
    if text is None:
        return None
    frac = Fraction(text)
    if frac.denominator == 1:
        return _result(
            "decimal_fraction", str(frac.numerator),
            [f"{text} ek poora number hai — iska fraction "
             f"roop {frac.numerator} hi hai."],
            float(frac))
    places = len(text.split(".")[1])
    top = int(text.replace(".", ""))
    g = math.gcd(top, 10 ** places)
    steps = [
        f"Write it over {10 ** places}: {text} = "
        f"{top}/{10 ** places}",
        f"Divide top and bottom by {g} to simplify: "
        f"= {frac.numerator}/{frac.denominator}",
    ]
    return _result("decimal_fraction",
                   f"{frac.numerator}/{frac.denominator}",
                   steps, float(frac))


# ---------------------------------------------------------------------------
# Negative square roots (Item 4g)
# ---------------------------------------------------------------------------

_NEG_ROOT_RES = [
    r"sqrt\s*\(\s*-\s*(\d+(?:\.\d+)?)\s*\)",
    r"√\s*\(?\s*-\s*(\d+(?:\.\d+)?)\s*\)?",
    r"sqrt\s+of\s+-\s*(\d+(?:\.\d+)?)",
    r"square\s+root\s+of\s+(?:minus|negative)\s+"
    r"(\d+(?:\.\d+)?)",
    r"square\s+root\s+of\s+-\s*(\d+(?:\.\d+)?)",
    r"-\s*(\d+(?:\.\d+)?)\s+ka\s+(?:square\s*root|"
    r"vargmool|sqrt)",
    r"-\s*(\d+(?:\.\d+)?)\s+का\s+वर्गमूल",
]


def _negative_root(question):
    q = str(question or "").translate(_DEV_DIGITS)
    hing = _hinglish_flavoured(question)
    for pat in _NEG_ROOT_RES:
        m = re.search(pat, q, flags=re.I)
        if not m:
            continue
        residue = q[:m.start()] + " " + q[m.end():]
        if not _residue_is_filler(residue):
            continue
        n = float(m.group(1))
        ns = fmt_num(n)
        root = sp.sqrt(sp.Rational(n).limit_denominator())
        if root.is_Integer:
            r = int(root)
            ans = f"{r}i"
            work = (f"√(−{ns}) = √({ns} × −1) = √{ns} × "
                    f"√(−1) = {r} × i = {r}i")
        else:
            exact = fmt_exact(root)
            ans = f"{exact}i ≈ {approx_str(root)}i"
            work = (f"√(−{ns}) = √({ns} × −1) = {exact} "
                    f"× i = {exact}i")
        if hing:
            steps = [
                "Koi bhi real sankhya ka varg negative "
                "nahi hota (jaise 2² = 4, (−2)² = 4) — "
                "isliye √(−" + ns + ") real number nahi "
                "hai.",
                "Maths me iske liye i rakha gaya hai: "
                "i = √(−1), matlab i² = −1.",
                work + ".",
            ]
        else:
            steps = [
                "No real number squares to a negative "
                "number (2² = 4 and (−2)² = 4) — so √(−"
                + ns + ") is not a real number.",
                "Maths uses i for this: i = √(−1), "
                "meaning i² = −1.",
                work + ".",
            ]
        return _result("negative_root", ans, steps)
    return None


# ---------------------------------------------------------------------------
# Word operators -> symbols (shared by 4a word form and 4i)
# ---------------------------------------------------------------------------

def _words_to_symbols(text):
    t = " " + str(text).lower().strip() + " "
    t = re.sub(r"(\w+)\s+squared\b", r"\1^2", t)
    t = re.sub(r"(\w+)\s+cubed\b", r"\1^3", t)
    t = t.replace(" multiplied by ", " * ")
    t = re.sub(r"\bdivided\s+by\b", "/", t)
    t = re.sub(r"\bequals\b|\bequal\s+to\b", "=", t)
    t = re.sub(r"\bminus\b", "-", t)
    t = re.sub(r"\bplus\b", "+", t)
    t = re.sub(r"\btimes\b", "*", t)
    return t.strip()


# ---------------------------------------------------------------------------
# Undefined-why explanations (Item 4h)
# ---------------------------------------------------------------------------

_UNDEF_CUES = {
    "why", "kyun", "kyon", "kya", "what", "undefined",
    "hota", "hoti", "hai", "hain", "batao", "kitna",
    "kitne", "matlab", "explain", "samjhao", "defined",
    "nahi", "the", "value", "of", "is", "it", "find",
    "calculate", "please", "answer", "jawab", "hoga",
    "hote", "kyu", "bataiye", "hua", "kabhi",
}


def _undef_residue_ok(text):
    # The residue must be pure ask-words: a digit or an
    # operator means the atom rides inside a bigger
    # expression ("1/0 + 2"), which is not this family.
    if re.search(r"[0-9+\-*/=<>]", str(text)):
        return False
    for tok in re.findall(r"[A-Za-z]+", str(text).lower()):
        if tok not in _UNDEF_CUES:
            return False
    for tok in re.findall(r"[ऀ-ॿ]+", str(text)):
        if tok not in _FILLER_DEV and tok not in (
                "क्यों", "क्यूं", "परिभाषित", "नहीं"):
            return False
    return True


def _undefined_why(question):
    q = str(question or "").translate(_DEV_DIGITS)
    hing = _hinglish_flavoured(question)
    # log 0 / ln 0
    m = re.search(r"\b(?:log|ln)\s*(?:of\s*)?\(?\s*0\s*\)?",
                  q, flags=re.I)
    if m:
        residue = q[:m.start()] + " " + q[m.end():]
        if _undef_residue_ok(residue):
            if hing:
                return _result(
                    "undefined_why",
                    "log 0 undefined hai.",
                    ["log ka sawal hai: 10 ki kis power "
                     "se 0 milega?",
                     "10 ki har power positive hoti hai "
                     "(10^0 = 1, 10^1 = 10, 10^(−1) = "
                     "0.1) — 0 kabhi aata hi nahi.",
                     "Isliye log 0 ka koi jawab nahi — "
                     "ye undefined hai."])
            return _result(
                "undefined_why",
                "log 0 is undefined.",
                ["log asks: 10 raised to what power "
                 "gives 0?",
                 "Every power of 10 is positive "
                 "(10^0 = 1, 10^1 = 10, 10^(−1) = 0.1) "
                 "— it never reaches 0.",
                 "So log 0 has no answer — it is "
                 "undefined."])
        return None
    # a / 0 or a by 0
    m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*0(?!\d)", q) or \
        re.search(r"(\d+(?:\.\d+)?)\s+by\s+0\b", q)
    if not m:
        return None
    residue = q[:m.start()] + " " + q[m.end():]
    if not _undef_residue_ok(residue):
        return None
    a = float(m.group(1))
    a_s = fmt_num(a)
    if a == 0:
        if hing:
            return _result(
                "undefined_why",
                "0/0 undefined hai.",
                ["0/0 ka matlab hota: 0 × c = 0 wali "
                 "sankhya c.",
                 "Lekin 0 × 1 = 0, 0 × 5 = 0, 0 × 100 "
                 "= 0 — HAR sankhya isme sahi baithti "
                 "hai.",
                 "Jab har number 'jawab' ho, to koi EK "
                 "jawab nahi hota — isliye 0/0 "
                 "undefined (indeterminate) hai."])
        return _result(
            "undefined_why",
            "0/0 is undefined.",
            ["0/0 would mean the number c with "
             "0 × c = 0.",
             "But 0 × 1 = 0, 0 × 5 = 0, 0 × 100 = 0 "
             "— EVERY number fits.",
             "When every number is 'the answer', "
             "there is no single answer — so 0/0 is "
             "undefined (indeterminate)."])
    if hing:
        return _result(
            "undefined_why",
            f"{a_s}/0 undefined hai.",
            [f"Division ka matlab: {a_s} ÷ 0 = c "
             f"ho to 0 × c = {a_s} hona chahiye.",
             f"Lekin 0 × koi bhi number = 0 hota hai "
             f"— {a_s} kabhi banta hi nahi.",
             f"Isliye {a_s}/0 ka koi jawab nahi — "
             f"ye undefined hai."])
    return _result(
        "undefined_why",
        f"{a_s}/0 is undefined.",
        [f"Division means: if {a_s} ÷ 0 = c, then "
         f"0 × c must equal {a_s}.",
         f"But 0 × any number = 0 — it can never "
         f"make {a_s}.",
         f"So {a_s}/0 has no answer — it is "
         f"undefined."])


# ---------------------------------------------------------------------------
# Worded-operator algebra (Item 4i)
# ---------------------------------------------------------------------------

_WORD_OPS = ("squared", "cubed", "minus", "plus", "times",
             "multiplied", "divided", "equals", "equal")
_SOLVE_CUES = ("solve", "hal karo", "hal kijiye", "roots",
               "root nikaalo", "find the roots")


def _worded_algebra(question):
    q = str(question or "").translate(_DEV_DIGITS)
    ql = q.lower()
    if not any(w in ql for w in _WORD_OPS):
        return None
    # Scope discipline: the family is worded POWER algebra
    # ("x squared minus 4" — the audit case). A plain linear
    # worded equation ("three x plus five equals twenty")
    # already has an owner — the fallback deep-solve rescue
    # (Wave 134, mechanism-pinned) serves it correctly — so
    # without a squared/cubed word this gate declines and
    # never displaces that path.
    if "squared" not in ql and "cubed" not in ql:
        return None
    if not re.search(r"\bx\b", ql):
        return None
    hing = _hinglish_flavoured(question)
    conv = _words_to_symbols(ql)
    # strip ask filler around the converted algebra
    conv = re.sub(r"^(?:please\s+)?(?:solve|find|calculate"
                  r"|evaluate|hal\s+karo)\s+", "", conv)
    conv = re.sub(r"\s*(?:solve\s+karo|solve|karo|batao|"
                  r"please)\s*$", "", conv)
    conv = conv.strip(" .?!")
    if not re.fullmatch(r"[0-9x\s\.\+\-\*/\^\(\)=]+", conv):
        return None
    if "x" not in conv:
        return None
    disp = conv.replace(" ", "")
    disp = disp.replace("^2", "²").replace("^3", "³")
    x = sp.symbols("x")
    try:
        if "=" in conv:
            left, right = conv.split("=", 1)
            expr = parse_expression(left) - \
                parse_expression(right)
            sols = sp.solve(expr, x)
            if not sols:
                return None
            sols = sorted(sols, key=lambda s: float(
                sp.N(s)))
            sol_txt = ", ".join(f"x = {fmt(s)}"
                                for s in sols)
            if hing:
                steps = [
                    f"Shabdon ko chinhon me badlo: "
                    f"{disp}.",
                    f"Hal karne par: {sol_txt}.",
                ]
            else:
                steps = [
                    f"Write the words in symbols: "
                    f"{disp}.",
                    f"Solving gives: {sol_txt}.",
                ]
            return _result("worded_equation", sol_txt,
                           steps)
        expr = parse_expression(conv)
        if any(c in ql for c in _SOLVE_CUES):
            sols = sp.solve(expr, x)
            if not sols:
                return None
            sols = sorted(sols, key=lambda s: float(
                sp.N(s)))
            sol_txt = ", ".join(f"x = {fmt(s)}"
                                for s in sols)
            if hing:
                steps = [
                    f"Shabdon ko chinhon me badlo: "
                    f"{disp}.",
                    f"Solve ka matlab: isey 0 ke barabar "
                    f"rakh kar roots nikaalo — "
                    f"{disp} = 0.",
                    f"Roots: {sol_txt}.",
                ]
            else:
                steps = [
                    f"Write the words in symbols: "
                    f"{disp}.",
                    f"To solve, set it equal to 0: "
                    f"{disp} = 0.",
                    f"Roots: {sol_txt}.",
                ]
            return _result("worded_equation", sol_txt,
                           steps)
        simp = sp.factor(expr)
        return _result(
            "worded_simplify", fmt(simp),
            [f"Write the words in symbols: {disp}.",
             f"Factorised: {fmt(simp)}."])
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Devanagari number-word arithmetic (Item 4j)
# ---------------------------------------------------------------------------

_DEV_NUMBERS = {
    "शून्य": 0, "एक": 1, "दो": 2, "तीन": 3, "चार": 4,
    "पाँच": 5, "पांच": 5, "छह": 6, "छः": 6, "सात": 7,
    "आठ": 8, "नौ": 9, "दस": 10, "ग्यारह": 11, "बारह": 12,
    "तेरह": 13, "चौदह": 14, "पंद्रह": 15, "पन्द्रह": 15,
    "सोलह": 16, "सत्रह": 17, "अठारह": 18, "उन्नीस": 19,
    "बीस": 20,
}
_DEV_OPS = {
    "जमा": "+", "जोड़": "+", "जोड़ो": "+",
    "घटा": "-", "घटाओ": "-", "घटाना": "-",
    "गुना": "*", "गुणा": "*", "गुणन": "*",
    "भाग": "/", "बाँट": "/", "बांट": "/",
}
_DEV_FILLER = {"कितना", "कितने", "कितनी", "है", "हैं",
               "होता", "होती", "बताओ", "बताइए", "क्या",
               "होगा", "करो", "कीजिए", "का", "की"}
_DEV_OP_TXT = {"+": "जमा", "-": "घटा", "*": "गुना",
               "/": "भाग"}


def _devanagari_arith(question):
    q = str(question or "")
    if not any("ऀ" <= ch <= "ॿ" for ch in q):
        return None
    tokens = re.findall(r"[ऀ-ॿ]+|\d+(?:\.\d+)?",
                        q.translate(_DEV_DIGITS))
    seq = []
    for tok in tokens:
        if tok in _DEV_FILLER:
            continue
        if tok in _DEV_NUMBERS:
            seq.append(Fraction(_DEV_NUMBERS[tok]))
        elif tok in _DEV_OPS:
            seq.append(_DEV_OPS[tok])
        elif re.fullmatch(r"\d+(?:\.\d+)?", tok):
            seq.append(Fraction(tok))
        else:
            return None
    if len(seq) < 3 or len(seq) % 2 == 0:
        return None
    for i, item in enumerate(seq):
        if i % 2 == 0 and not isinstance(item, Fraction):
            return None
        if i % 2 == 1 and item not in "+-*/":
            return None
    # evaluate with precedence: * and / first
    vals = [seq[0]]
    ops = []
    i = 1
    while i < len(seq):
        op, num = seq[i], seq[i + 1]
        if op == "*":
            vals[-1] = vals[-1] * num
        elif op == "/":
            if num == 0:
                return None
            vals[-1] = vals[-1] / num
        else:
            ops.append(op)
            vals.append(num)
        i += 2
    total = vals[0]
    for op, num in zip(ops, vals[1:]):
        total = total + num if op == "+" else total - num
    shown = []
    for item in seq:
        if isinstance(item, Fraction):
            shown.append(fmt_num(item))
        else:
            shown.append({"+": "+", "-": "−", "*": "×",
                          "/": "÷"}[item])
    expr_txt = " ".join(shown)
    return _result(
        "devanagari_arith", fmt_num(total),
        [f"संख्या-शब्दों को अंकों में: {expr_txt} "
         f"= {fmt_num(total)}."],
        float(total))


# ---------------------------------------------------------------------------
# Check / verdict asks (Item 4k)
# ---------------------------------------------------------------------------

_CHECK_CUES = [
    r"sahi\s+hai\s+ya\s+galat", r"sahi\s+hai", r"galat\s+hai",
    r"\bcheck\s+karo\b", r"\bcheck\b", r"\bverify\b",
    r"\bcorrect\b", r"\btrue\b", r"जाँच", r"जांच",
    r"ठीक\s+है",
]
_CHECK_STRIP = [
    r"sahi\s+hai\s+ya\s+galat", r"sahi\s+hai", r"galat\s+hai",
    r"check\s+karo", r"check", r"verify", r"correct", r"true",
    r"जाँच\s*करो?", r"जांच\s*करो?", r"ठीक\s+है",
    r"\bis\b", r"\bkya\b", r"\bhai\s*kya\b",
]


def _check_verdict(question):
    q = str(question or "").translate(_DEV_DIGITS)
    ql = q.lower()
    if not any(re.search(p, ql) for p in _CHECK_CUES):
        return None
    hing = _hinglish_flavoured(question)
    t = ql
    for pat in _CHECK_STRIP:
        t = re.sub(pat, " ", t)
    t = t.strip(" .?!")
    m = re.fullmatch(
        r"([0-9\s\.\+\-\*/\^\(\)x×÷]+)=([0-9\s\.\+\-\*/\^\(\)x×÷]+)",
        t)
    if not m:
        return None
    lhs_txt, rhs_txt = m.group(1).strip(), m.group(2).strip()
    if not lhs_txt or not rhs_txt:
        return None

    def _const(txt):
        s = txt.replace("×", "*").replace("÷", "/")
        s = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", s)
        if re.search(r"[a-z]", s):
            return None
        try:
            v = parse_expression(s)
        except Exception:
            return None
        if v.free_symbols:
            return None
        return sp.nsimplify(v)

    lv = _const(lhs_txt)
    rv = _const(rhs_txt)
    if lv is None or rv is None:
        return None
    lhs_disp = re.sub(r"(?<=\d)x(?=\d)", "×",
                      lhs_txt.replace(" ", ""))
    if sp.simplify(lv - rv) == 0:
        if hing:
            return _result(
                "check_verdict",
                f"Sahi hai ✓ — {lhs_disp} = "
                f"{fmt_num(lv)} sahi hai.",
                [f"Baayein taraf: {lhs_disp} = "
                 f"{fmt_num(lv)}.",
                 f"Daayein taraf: {fmt_num(rv)}.",
                 "Dono barabar hain — statement sahi "
                 "hai."])
        return _result(
            "check_verdict",
            f"Correct ✓ — {lhs_disp} = {fmt_num(lv)}.",
            [f"Left side: {lhs_disp} = {fmt_num(lv)}.",
             f"Right side: {fmt_num(rv)}.",
             "Both sides are equal — the statement "
             "is correct."])
    if hing:
        return _result(
            "check_verdict",
            f"Galat hai — {lhs_disp} = {fmt_num(lv)} "
            f"hota hai, {fmt_num(rv)} nahi.",
            [f"Baayein taraf nikaalo: {lhs_disp} = "
             f"{fmt_num(lv)}.",
             f"Lekin statement me {fmt_num(rv)} likha "
             f"hai — dono barabar nahi hain.",
             f"Sahi statement: {lhs_disp} = "
             f"{fmt_num(lv)}."])
    return _result(
        "check_verdict",
        f"Not correct — {lhs_disp} = {fmt_num(lv)}, "
        f"not {fmt_num(rv)}.",
        [f"Work out the left side: {lhs_disp} = "
         f"{fmt_num(lv)}.",
         f"But the statement says {fmt_num(rv)} — "
         f"the two sides are not equal.",
         f"The correct statement is: {lhs_disp} = "
         f"{fmt_num(lv)}."])


# ---------------------------------------------------------------------------
# Bare root atoms (Item 1) — sqrt(N) / √N as the whole question
# ---------------------------------------------------------------------------

def _bare_root(question):
    q = str(question or "").translate(_DEV_DIGITS)
    t = q.strip().lower().strip(" .?!")
    t = re.sub(r"^(?:what\s+is|find|calculate|evaluate|"
               r"the\s+value\s+of|value\s+of)\s+", "", t)
    m = re.fullmatch(r"sqrt\s*\(\s*(\d+(?:\.\d+)?)\s*\)",
                     t) or \
        re.fullmatch(r"√\s*(\d+(?:\.\d+)?)", t) or \
        re.fullmatch(r"sqrt\s+of\s+(\d+(?:\.\d+)?)", t)
    if not m:
        return None
    n = float(m.group(1))
    if n < 0:
        return None
    root = sp.sqrt(sp.Rational(n).limit_denominator())
    if root.is_Integer or root.is_Rational:
        return None  # the plain paths serve these exactly
    ns = fmt_num(n)
    exact = fmt_exact(root)
    approx = approx_str(root)
    steps = []
    if float(n).is_integer():
        ni = int(n)
        a = math.isqrt(ni)
        while a > 1 and ni % (a * a) != 0:
            a -= 1
        if a > 1:
            b = ni // (a * a)
            steps.append(
                f"{ni} = {a * a} × {b} = {a}² × {b}, "
                f"isliye √{ni} = {a}√{b}.")
    steps.append(f"√{ns} = {exact} ≈ {approx}")
    return _result("root_exact", f"{exact} ≈ {approx}",
                   steps, float(root))


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_GATES234 = (
    _undefined_why,
    _negative_root,
    _number_square,
    _square_side_from_area,
    _worded_factorial,
    _abs_equation,
    _decimal_fraction,
    _check_verdict,
    _worded_algebra,
    _devanagari_arith,
    _bare_root,
)


def solve_wave234(question):
    """Wave 234 gates: the first strict full-shape match
    wins; None on any doubt (the flow is then exactly the
    pre-Wave-234 one)."""
    for gate in _GATES234:
        try:
            out = gate(question)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
