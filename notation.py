"""Wave 138 — proper maths notation (typeset rendering).

Suraj's order (17 Nov 2026, with a screenshot of a big-AI
answer as the target): Ganitra's answers must show maths
PROPERLY TYPESET — fractions stacked (numerator above a line,
denominator below), powers raised small (x²), the root sign
covering its whole expression (sqrt(b^2 - 4ac)), the quadratic
formula / distance formula / slope / probability shown as real
maths notation — not inline text like "1/6", "x^2", "sqrt(x)".

WHAT THIS MODULE IS
-------------------
A deterministic, conservative plain-text -> TeX converter.
The solver (and every other answer source) keeps producing
exactly the plain lines it produces today — same words, same
values, same order (Wave 132's voice rules are untouched).
This layer only finds the MATHS SPANS inside a line and wraps
each one as ``\\(...\\)`` TeX, so the MathJax 3 that base.html
already loads (and the chat already calls typesetPromise with)
renders them typeset.  Everything outside a span is copied
byte-for-byte.  Plain fields (steps / answer) are never
mutated: the typeset variants ride in NEW parallel fields
(steps_tex / answer_tex) used for DISPLAY only — copy,
narration and stored plain text keep the original strings.

HARD RULES (Wave 132's invariant, extended)
-------------------------------------------
* Values are never changed.  Every converted span passes a
  self-check: the multiset of value tokens (numbers,
  identifier letters, units, %, !) extracted from the source
  span must equal the multiset extracted from the produced
  TeX.  Any mismatch -> the span is served plain.
* Ambiguous spans stay plain.  A span must parse under the
  small grammar below AND carry a strong maths feature
  (a fraction, a root, a power, a relation, a multiplication
  or an algebraic juxtaposition).  Bare atoms ("12", "(5)"),
  word-operand lines ("Speed = distance ÷ time"), unit rates
  ("60 km/h"), ordinals ("2th"), dates (a second bare "/"
  declines the span) and prose parentheticals ("(LCM of 4
  and 6)") all stay exactly as they are.
* A line that already carries TeX delimiters or a "$" is
  returned untouched (never double-wrap, never pair a stray
  "$" into a fake span).

RENDERING / FALLBACK
--------------------
Display-side only: the chat inserts the *_tex strings with
textContent (exactly like the plain strings — no HTML
injection surface) and uses them ONLY when MathJax's
typesetPromise is actually available at render time; if the
CDN is blocked/offline the plain string is shown instead, so
an answer can never arrive blank or covered in raw
delimiters.  Server-rendered pages (answer / print) get the
same fields in their result dict; MathJax auto-typesets them
on load, as it already does for result.latex today.
"""

import re
from collections import Counter

__all__ = ["texify_line", "annotate_result", "annotate_method",
           "values_preserved"]


# ------------------------------------------------------------------
# Tokenizer
# ------------------------------------------------------------------

_SUPER_MAP = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-", "ⁿ": "n", "ˣ": "x",
}

_FUNCS = {"sqrt", "sin", "cos", "tan", "cot", "sec", "cosec",
          "log", "ln", "lim"}
_FUNC_TEX = {"cosec": r"\csc", "sec": r"\sec", "cot": r"\cot",
             "sin": r"\sin", "cos": r"\cos", "tan": r"\tan",
             "log": r"\log", "ln": r"\ln", "lim": r"\lim"}
_GREEKS = {"pi": r"\pi", "theta": r"\theta", "alpha": r"\alpha",
           "beta": r"\beta", "gamma": r"\gamma", "delta": r"\Delta",
           "lambda": r"\lambda", "mu": r"\mu", "sigma": r"\sigma",
           "phi": r"\phi", "omega": r"\omega"}
_ABBREVS = {"SI", "CP", "SP", "MP", "HCF", "LCM", "GCD", "LHS", "RHS"}
_UNITS = {"cm", "mm", "km", "kg", "ml", "hr", "min", "mins",
          "secs", "hours", "hour", "days", "day", "weeks",
          "week", "months", "month", "years", "year", "metres",
          "metre", "grams", "gram", "litres", "litre"}
_UNITC = {"km/h", "km/hr", "m/s", "cm/s", "m/min"}
_DIFFS = {"dx", "dy", "dt"}
# Two-letter prose runs that must never be split into variable
# pairs ("at" in "at 5%", "of", "is", "Rs" the currency label…).
# ("at" costs the kinematics "v = u + at" its tail — documented;
# prose safety wins.)
_BREAK_RUNS = {
    "of", "an", "in", "on", "at", "by", "to", "do", "if", "it",
    "he", "we", "me", "my", "no", "so", "up", "am", "as", "be",
    "or", "is", "rs", "mr", "dr", "vs",
}
_ORDINAL_SUFFIXES = {"th", "st", "nd", "rd"}

_NUM_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?|\.\d+")
_RUN_RE = re.compile(r"[A-Za-z]+")
_SUPER_RE = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻ⁿˣ]+")

_OP_TEX = {
    "+": "+", "-": "-", "=": "=", "<": "<", ">": ">",
    "≤": r"\le", "≥": r"\ge", "≈": r"\approx", "≠": r"\ne",
    "±": r"\pm", "*": r"\cdot", "·": r"\cdot", "×": r"\times",
    "÷": r"\div",
}
_REL_OPS = {"=", "<", ">", "≤", "≥", "≈", "≠"}
_MUL_OPS = {"*", "·", "×"}


class _Tok(object):
    __slots__ = ("kind", "text", "start", "end", "letter", "digits")

    def __init__(self, kind, text, start, end, letter=None,
                 digits=None):
        self.kind = kind
        self.text = text
        self.start = start
        self.end = end
        self.letter = letter
        self.digits = digits


def _classify_run(run, start, end):
    """One maximal [A-Za-z]+ run -> token(s)."""
    low = run.lower()
    if run in _ABBREVS:
        return [_Tok("ABBREV", run, start, end)]
    if low in _FUNCS:
        return [_Tok("FUNC", low, start, end)]
    if low in _GREEKS:
        return [_Tok("GREEK", low, start, end)]
    if low in _DIFFS:
        return [_Tok("DIFF", low, start, end)]
    if low in _UNITS:
        return [_Tok("UNIT", low, start, end)]
    if low in _BREAK_RUNS or len(run) > 2:
        return [_Tok("BREAK", run, start, end)]
    if len(run) == 1:
        return [_Tok("IDENT", run, start, end)]
    if len(run) == 2:
        # A two-letter run that is no known word: an algebraic
        # juxtaposition (ac, xy, AB, pq) — two single idents.
        return [_Tok("IDENT", run[0], start, start + 1),
                _Tok("IDENT", run[1], start + 1, end)]
    return [_Tok("BREAK", run, start, end)]


def _tokenize(line):
    """Significant tokens of the line, with source positions.
    Anything unrecognised becomes a BREAK token (a hard wall
    no maths span may cross)."""
    toks = []
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if ch in " \t":
            i += 1
            continue
        # Compound units first (km/h must not become k·m/h).
        matched = False
        for unit in _UNITC:
            if line.startswith(unit, i):
                j = i + len(unit)
                before_ok = i == 0 or not (
                    line[i - 1].isalnum() or line[i - 1] == "_")
                after_ok = j >= n or not (
                    line[j].isalnum() or line[j] == "_")
                if before_ok and after_ok:
                    toks.append(_Tok("UNITC", unit, i, j))
                    i = j
                    matched = True
                    break
        if matched:
            continue
        if (ch.isascii() and ch.isdigit()) or (
                ch == "." and i + 1 < n
                and line[i + 1].isascii()
                and line[i + 1].isdigit()):
            m = _NUM_RE.match(line, i)
            text = m.group(0)
            j = m.end()
            # Ordinal poison: 2th / 1st / 3rd are prose, and
            # the number+letters must not start a span.
            m2 = _RUN_RE.match(line, j)
            if m2 and m2.group(0).lower() in _ORDINAL_SUFFIXES:
                toks.append(_Tok("BREAK", line[i:m2.end()], i,
                                 m2.end()))
                i = m2.end()
                continue
            toks.append(_Tok("NUM", text, i, j))
            i = j
            continue
        m = _RUN_RE.match(line, i)
        if m:
            run = m.group(0)
            j = m.end()
            # letter+digits: a subscripted variable (x2, y1).
            if len(run) == 1 and j < n and line[j].isdigit():
                k = j
                while k < n and line[k].isdigit():
                    k += 1
                toks.append(_Tok("IDENTD", line[i:k], i, k,
                                 letter=run,
                                 digits=line[j:k]))
                i = k
                continue
            toks.extend(_classify_run(run, i, j))
            i = j
            continue
        m = _SUPER_RE.match(line, i)
        if m:
            digits = "".join(_SUPER_MAP[c] for c in m.group(0))
            toks.append(_Tok("SUPER", digits, i, m.end()))
            i = m.end()
            continue
        if ch in "+-=<>*·×÷±":
            toks.append(_Tok("OP", ch, i, i + 1))
            i += 1
            continue
        if ch == "/":
            toks.append(_Tok("OP", "/", i, i + 1))
            i += 1
            continue
        if ch in "≤≥≈≠":
            toks.append(_Tok("OP", ch, i, i + 1))
            i += 1
            continue
        if ch == "−":  # U+2212 minus
            toks.append(_Tok("OP", "-", i, i + 1))
            i += 1
            continue
        if ch == "(":
            toks.append(_Tok("LP", ch, i, i + 1))
            i += 1
            continue
        if ch == ")":
            toks.append(_Tok("RP", ch, i, i + 1))
            i += 1
            continue
        if ch == "[":
            toks.append(_Tok("LB", ch, i, i + 1))
            i += 1
            continue
        if ch == "]":
            toks.append(_Tok("RB", ch, i, i + 1))
            i += 1
            continue
        if ch == "^":
            toks.append(_Tok("POW", ch, i, i + 1))
            i += 1
            continue
        if ch == "!":
            toks.append(_Tok("BANG", ch, i, i + 1))
            i += 1
            continue
        if ch == "%":
            toks.append(_Tok("PCT", ch, i, i + 1))
            i += 1
            continue
        if ch == "°":
            toks.append(_Tok("DEG", ch, i, i + 1))
            i += 1
            continue
        if ch == ",":
            toks.append(_Tok("COMMA", ch, i, i + 1))
            i += 1
            continue
        if ch == "√":
            toks.append(_Tok("SQRT", ch, i, i + 1))
            i += 1
            continue
        if ch == "∫":
            toks.append(_Tok("INTG", ch, i, i + 1))
            i += 1
            continue
        if ch == "π":
            toks.append(_Tok("GREEK", "pi", i, i + 1))
            i += 1
            continue
        if ch == "θ":
            toks.append(_Tok("GREEK", "theta", i, i + 1))
            i += 1
            continue
        if ch == "∞":
            toks.append(_Tok("INFTY", ch, i, i + 1))
            i += 1
            continue
        toks.append(_Tok("BREAK", ch, i, i + 1))
        i += 1
    return toks


# ------------------------------------------------------------------
# Parser: tokens -> TeX.  Every parse function returns
# (tex, next_index, features) or raises _Fail / _Decline.
# A factor also reports its unwrapped inner TeX when it is
# exactly one parenthesised group (a fraction operand drops
# its redundant parens: (y2-y1)/(x2-x1) -> \frac{y_2-y_1}{x_2-x_1}).
# ------------------------------------------------------------------

_STRONG = {"frac", "sqrt", "pow", "rel", "op", "jux", "fact",
           "int"}


class _Fail(Exception):
    pass


class _Decline(Exception):
    """The span looked like maths but must be served plain
    (e.g. a second bare '/' — the date shape)."""
    pass


def _starts_factor(tok):
    return tok.kind in ("NUM", "IDENT", "IDENTD", "FUNC",
                        "GREEK", "ABBREV", "DIFF", "LP", "LB",
                        "SQRT", "INTG", "INFTY")


def _parse_atom(toks, i):
    if i >= len(toks):
        raise _Fail()
    t = toks[i]
    if t.kind == "NUM":
        return t.text, i + 1, set(), None
    if t.kind == "IDENT":
        return t.text, i + 1, set(), None
    if t.kind == "IDENTD":
        if len(t.digits) == 1:
            sub = "_" + t.digits
        else:
            sub = "_{" + t.digits + "}"
        return t.letter + sub, i + 1, set(), None
    if t.kind == "GREEK":
        return _GREEKS[t.text], i + 1, set(), None
    if t.kind == "ABBREV":
        return r"\mathrm{" + t.text + "}", i + 1, set(), None
    if t.kind == "DIFF":
        return t.text, i + 1, set(), None
    if t.kind == "INFTY":
        return r"\infty", i + 1, set(), None
    if t.kind in ("LP", "LB"):
        close = "RP" if t.kind == "LP" else "RB"
        inner, j, feats = _parse_expr(toks, i + 1)
        if j >= len(toks) or toks[j].kind != close:
            raise _Fail()
        if t.kind == "LP":
            if "\\frac" in inner or "\\sqrt" in inner:
                tex = r"\left(" + inner + r"\right)"
            else:
                tex = "(" + inner + ")"
        else:
            tex = "[" + inner + "]"
        return tex, j + 1, feats, inner
    raise _Fail()


def _parse_power(toks, i):
    """The exponent after ^ : one simple atom or a group."""
    if i >= len(toks):
        raise _Fail()
    t = toks[i]
    if t.kind in ("NUM", "IDENT", "GREEK"):
        tex, j, _f, _in = _parse_atom(toks, i)
        if len(tex) == 1:
            return "^" + tex, j
        return "^{" + tex + "}", j
    if t.kind == "IDENTD":
        tex, j, _f, _in = _parse_atom(toks, i)
        return "^{" + tex + "}", j
    if t.kind in ("LP", "LB"):
        inner, j, _f = _parse_expr(toks, i + 1)
        close = "RP" if t.kind == "LP" else "RB"
        if j >= len(toks) or toks[j].kind != close:
            raise _Fail()
        return "^{" + inner + "}", j + 1
    raise _Fail()


def _parse_unary(toks, i):
    if i >= len(toks):
        raise _Fail()
    t = toks[i]
    if t.kind == "FUNC":
        if t.text == "sqrt":
            if i + 1 >= len(toks) or toks[i + 1].kind != "LP":
                raise _Fail()
            inner, j, _f = _parse_expr(toks, i + 2)
            if j >= len(toks) or toks[j].kind != "RP":
                raise _Fail()
            return r"\sqrt{" + inner + "}", j + 1, {"sqrt"}, None
        tex = _FUNC_TEX[t.text]
        j = i + 1
        feats = set()
        if j < len(toks) and toks[j].kind == "POW":
            ptex, j = _parse_power(toks, j + 1)
            tex += ptex
            feats.add("pow")
        elif j < len(toks) and toks[j].kind == "SUPER":
            tex += "^{" + toks[j].text + "}"
            j += 1
            feats.add("pow")
        # One factor as the function's argument (sin t, log 100).
        if j < len(toks) and _starts_factor(toks[j]) \
                and toks[j].kind != "FUNC":
            atex, j, afeats, _in = _parse_factor(toks, j)
            tex += " " + atex
            feats |= afeats
            feats.add("jux")
        return tex, j, feats, None
    if t.kind == "SQRT":
        atex, j, _f, _in = _parse_atom(toks, i + 1)
        return r"\sqrt{" + atex + "}", j, {"sqrt"}, None
    if t.kind == "INTG":
        itex, j, ifeats = _parse_additive(toks, i + 1)
        return r"\int " + itex, j, ifeats | {"int"}, None
    return _parse_atom(toks, i)


def _parse_factor(toks, i):
    feats = set()
    sign = ""
    if i < len(toks) and toks[i].kind == "OP" \
            and toks[i].text in ("+", "-"):
        if i + 1 < len(toks) and _starts_factor(toks[i + 1]):
            sign = toks[i].text if toks[i].text == "-" else ""
            i += 1
        else:
            raise _Fail()
    tex, i, ufeats, inner = _parse_unary(toks, i)
    feats |= ufeats
    tex = sign + tex
    while i < len(toks):
        t = toks[i]
        if t.kind == "POW":
            ptex, i = _parse_power(toks, i + 1)
            tex += ptex
            feats.add("pow")
            inner = None
        elif t.kind == "SUPER":
            tex += "^{" + t.text + "}"
            i += 1
            feats.add("pow")
            inner = None
        elif t.kind == "BANG":
            tex += "!"
            i += 1
            feats.add("fact")
            inner = None
        elif t.kind == "PCT":
            tex += r"\%"
            i += 1
            inner = None
        elif t.kind == "DEG":
            tex += r"^{\circ}"
            i += 1
            inner = None
        elif t.kind in ("UNIT", "UNITC"):
            tex += r"\ \mathrm{" + t.text + "}"
            i += 1
            inner = None
        else:
            break
    return tex, i, feats, inner


def _group_has_pct(toks, i):
    """True when the group opening at token i contains a %
    before its matching close (a percent remark, not maths)."""
    depth = 0
    for j in range(i, len(toks)):
        t = toks[j]
        if t.kind in ("LP", "LB"):
            depth += 1
        elif t.kind in ("RP", "RB"):
            depth -= 1
            if depth == 0:
                return False
        elif t.kind == "PCT" and depth >= 1:
            return True
    return False


def _parse_term(toks, i):
    tex, i, feats, inner = _parse_factor(toks, i)
    chain = tex            # accumulated numerator chain
    chain_inner = inner    # set while the chain is ONE group
    bare_frac_seen = False
    while i < len(toks):
        t = toks[i]
        if t.kind == "OP" and t.text in _MUL_OPS:
            save = i
            try:
                ftex, i, ffeats, _in = _parse_factor(toks, i + 1)
            except _Fail:
                i = save
                break
            chain += " " + _OP_TEX[t.text] + " " + ftex
            chain_inner = None
            feats |= ffeats | {"op"}
        elif t.kind == "OP" and t.text == "÷":
            save = i
            try:
                ftex, i, ffeats, finner = _parse_factor(toks,
                                                        i + 1)
                # A division's operand may itself be one
                # fraction (5/6 ÷ 2/3) — a local frac that does
                # not touch the term's bare-frac guard.
                if i < len(toks) and toks[i].kind == "OP" \
                        and toks[i].text == "/":
                    dtex, i, dfeats, dinner = _parse_factor(
                        toks, i + 1)
                    num = finner if finner is not None else ftex
                    den = dinner if dinner is not None else dtex
                    ftex = r"\frac{" + num + "}{" + den + "}"
                    ffeats |= dfeats | {"frac"}
            except _Fail:
                i = save
                break
            chain += r" \div " + ftex
            chain_inner = None
            feats |= ffeats | {"op"}
        elif t.kind == "OP" and t.text == "/":
            if bare_frac_seen:
                # A second bare division in one term is the
                # date shape (12/11/2026) — end the span here
                # and serve the rest plain.
                break
            save = i
            try:
                ftex, i, ffeats, finner = _parse_factor(toks,
                                                        i + 1)
            except _Fail:
                i = save
                break
            num = chain_inner if chain_inner is not None else chain
            den = finner if finner is not None else ftex
            chain = r"\frac{" + num + "}{" + den + "}"
            chain_inner = None
            bare_frac_seen = True
            feats |= ffeats | {"frac"}
        elif _starts_factor(t):
            # A parenthesised percent remark ("(62.50%)") is a
            # prose aside, not an algebraic factor — never let
            # it be swallowed as a juxtaposed product.
            if t.kind in ("LP", "LB") and _group_has_pct(toks, i):
                break
            save = i
            try:
                ftex, i, ffeats, _in = _parse_factor(toks, i)
            except _Fail:
                i = save
                break
            # Juxtaposition renders as plain adjacency (4ac,
            # 2(x+1)) — except where TeX would misread the
            # join: after a \command (\pi r^2, never \pir^2)
            # or after a bare one-char exponent (x^n dx,
            # never x^ndx).
            if ftex[:1].isalpha() and (
                    re.search(r"\\[A-Za-z]+$", chain)
                    or re.search(r"\^[A-Za-z0-9]$", chain)):
                chain += " " + ftex
            else:
                chain += ftex
            chain_inner = None
            feats |= ffeats | {"jux"}
        else:
            break
    return chain, i, feats


def _parse_additive(toks, i):
    tex, i, feats = _parse_term(toks, i)
    while i < len(toks):
        t = toks[i]
        if t.kind == "OP" and t.text in ("+", "-", "±"):
            save = i
            try:
                rtex, i, rfeats = _parse_term(toks, i + 1)
            except _Fail:
                i = save
                break
            tex += " " + _OP_TEX[t.text] + " " + rtex
            feats |= rfeats | {"op"}
        else:
            break
    return tex, i, feats


def _parse_expr(toks, i):
    tex, i, feats = _parse_additive(toks, i)
    while i < len(toks):
        t = toks[i]
        if t.kind == "OP" and t.text in _REL_OPS:
            save = i
            try:
                rtex, i, rfeats = _parse_additive(toks, i + 1)
            except _Fail:
                i = save
                break
            tex += " " + _OP_TEX[t.text] + " " + rtex
            feats |= rfeats | {"rel"}
        elif t.kind == "COMMA":
            save = i
            try:
                rtex, i, rfeats = _parse_additive(toks, i + 1)
            except _Fail:
                i = save
                break
            tex += ", " + rtex
            feats |= rfeats
        else:
            break
    return tex, i, feats


# ------------------------------------------------------------------
# Value-preservation self-check (Wave 132's invariant).
# Operators are structure, not values, and are excluded; numbers,
# identifier letters, function/Greek names, units and the %/!
# marks must match as multisets between source span and TeX.
# ------------------------------------------------------------------

_CMD_WORDS = {
    "frac": None, "sqrt": "sqrt", "left": None, "right": None,
    "pi": "pi", "theta": "theta", "alpha": "alpha",
    "beta": "beta", "gamma": "gamma", "Delta": "delta",
    "lambda": "lambda", "mu": "mu", "sigma": "sigma",
    "phi": "phi", "omega": "omega", "sin": "sin", "cos": "cos",
    "tan": "tan", "csc": "cosec", "sec": "sec", "cot": "cot",
    "log": "log", "ln": "ln", "lim": "lim", "infty": "infty",
    "mathrm": None, "cdot": None, "times": None, "div": None,
    "pm": None, "approx": None, "le": None, "ge": None,
    "ne": None, "int": None, "circ": "deg",
}


def _canon(text):
    """Canonical value-token multiset of a source span OR of a
    produced TeX span (delimiters/commands normalised away)."""
    s = text
    s = s.replace("\\(", " ").replace("\\)", " ")
    s = s.replace("≈", " approx ").replace("×", " ").replace(
        "·", " ").replace("*", " ").replace("÷", " ")
    s = s.replace("≤", " ").replace("≥", " ").replace(
        "≠", " ").replace("±", " ")
    s = re.sub(r"\\([A-Za-z]+)", lambda m: (
        " " + _CMD_WORDS[m.group(1)] + " ")
        if _CMD_WORDS.get(m.group(1)) else " ", s)
    s = s.replace("{", " ").replace("}", " ").replace(
        "^", " ").replace("_", " ").replace("\\", " ")
    counts = Counter()
    for tok in _tokenize(s):
        if tok.kind == "NUM":
            counts[("n", tok.text.replace(",", ""))] += 1
        elif tok.kind == "IDENT":
            counts[("v", tok.text)] += 1
        elif tok.kind == "IDENTD":
            counts[("v", tok.letter)] += 1
            counts[("n", tok.digits)] += 1
        elif tok.kind in ("FUNC", "GREEK", "ABBREV", "UNIT",
                          "UNITC", "DIFF"):
            counts[("w", tok.text)] += 1
        elif tok.kind == "SUPER":
            for part in re.findall(r"\d+|[a-z]", tok.text):
                counts[("n" if part.isdigit() else "v", part)] += 1
        elif tok.kind == "SQRT":
            counts[("w", "sqrt")] += 1
        elif tok.kind == "PCT":
            counts[("m", "%")] += 1
        elif tok.kind == "BANG":
            counts[("m", "!")] += 1
        elif tok.kind == "DEG":
            counts[("m", "deg")] += 1
        elif tok.kind == "INFTY":
            counts[("w", "infty")] += 1
        elif tok.kind == "BREAK" and tok.text == "infty":
            # The word a stripped \infty leaves behind in TeX.
            counts[("w", "infty")] += 1
        elif tok.kind == "BREAK" and tok.text == "deg":
            # The word a stripped \circ leaves behind in TeX.
            counts[("m", "deg")] += 1
    return counts


def values_preserved(source_span, tex_span):
    """True iff converting source_span to tex_span kept every
    value token (Wave 132's hard rule)."""
    return _canon(source_span) == _canon(tex_span)


# ------------------------------------------------------------------
# Line conversion
# ------------------------------------------------------------------

def texify_line(line):
    """Return `line` with its maths spans wrapped as \\(...\\)
    TeX.  Anything uncertain stays byte-identical plain text."""
    if not isinstance(line, str) or not line:
        return line
    if len(line) > 2000 or "\\(" in line or "$" in line:
        return line
    toks = _tokenize(line)
    if not toks:
        return line
    out = []
    last = 0
    i = 0
    changed = False
    while i < len(toks):
        t = toks[i]
        span = None
        # A token sitting right after a bare "/" is a
        # denominator fragment (the tail of a span that ended
        # at the second-slash guard) — never start a span
        # there, or "…/2 = 5/4" would fake a "2 = 5/4" span.
        if line[:t.start].rstrip().endswith("/"):
            i += 1
            continue
        # Leading-relation span ("= sqrt(25)").
        if t.kind == "OP" and t.text in ("=", "≈") \
                and i + 1 < len(toks):
            try:
                tex, j, feats = _parse_expr(toks, i + 1)
                if j > i + 1 and (feats & _STRONG):
                    src = line[t.start:toks[j - 1].end]
                    full = _OP_TEX[t.text] + " " + tex
                    if values_preserved(src, full):
                        span = (t.start, toks[j - 1].end, full, j)
            except (_Fail, _Decline):
                span = None
        if span is None and _starts_factor(t):
            try:
                tex, j, feats = _parse_expr(toks, i)
                if j > i and (feats & _STRONG):
                    src = line[t.start:toks[j - 1].end]
                    if values_preserved(src, tex):
                        span = (t.start, toks[j - 1].end, tex, j)
            except (_Fail, _Decline):
                span = None
        if span is not None:
            out.append(line[last:span[0]])
            out.append("\\(" + span[2] + "\\)")
            last = span[1]
            i = span[3]
            changed = True
        else:
            i += 1
    if not changed:
        return line
    out.append(line[last:])
    return "".join(out)


# ------------------------------------------------------------------
# Result annotation: parallel display-only fields.
# ------------------------------------------------------------------

def _is_plain_result(result):
    """One-line / plain-reply results render as raw text in the
    chat (no typeset pass) — never annotate them, or the raw
    delimiters would show."""
    if not isinstance(result, dict):
        return True
    if result.get("plain") or result.get("plain_reply"):
        return True
    if result.get("fallback_kind") == "not_found":
        return True
    return False


def annotate_result(result):
    """Add steps_tex / answer_tex (display-only) to a solve
    result, in place, when conversion changes anything.  The
    plain fields are never touched.  Callers pass a shallow
    copy at the response/template boundary, so the solver's
    own dict — the negative cache's, the session's — is never
    the object annotated (Wave 48's pass-through pin)."""
    if _is_plain_result(result):
        return result
    steps = result.get("steps")
    if isinstance(steps, list) and steps:
        tex_steps = [texify_line(s) if isinstance(s, str) else s
                     for s in steps]
        if tex_steps != steps:
            result["steps_tex"] = tex_steps
    answer = result.get("answer")
    if isinstance(answer, str) and answer:
        tex_answer = texify_line(answer)
        if tex_answer != answer:
            result["answer_tex"] = tex_answer
    return result


def annotate_method(method):
    """Same display-only annotation for one alternate method."""
    if not isinstance(method, dict):
        return method
    steps = method.get("steps")
    if isinstance(steps, list) and steps:
        tex_steps = [texify_line(s) if isinstance(s, str) else s
                     for s in steps]
        if tex_steps != steps:
            method["steps_tex"] = tex_steps
    return method
