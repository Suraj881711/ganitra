"""Wave 80: vector algebra in component form — dot / cross
products, magnitude, unit vectors, angle between vectors,
parallelogram diagonals, direction cosines and the coordinate
plane facts.

Why this module exists (Wave 71 audit, families 31 + 32):
board questions write vectors with Unicode unit glyphs —
î (U+00EE), ĵ (U+0135), k̂ (k + U+0302 combining circumflex)
and a⃗ (letter + U+20D7 combining arrow). No solver understood
the notation at all, so every such question failed; worse, the
MCQ layer then retried the unsolvable stem through ~11
full-pipeline candidates, each paying the router's 10 s
budget, and the item burned >20 s (the audit's ERROR_TIMEOUT
family). This module claims the family directly, in
milliseconds: the stem solves on the first attempt and the
retry multiplier never engages.

The module is strict: it returns a result only when the text
carries real vector content (unit glyphs, named vector
definitions, or an explicit vector ask) AND the maths parses
completely. Anything else returns None and routing continues
unchanged.
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num

_UNITS = ("i", "j", "k")
_UNIT_GLYPH = {"i": "î", "j": "ĵ", "k": "k̂"}


# ---------------------------------------------------------------------------
# Text preparation
# ---------------------------------------------------------------------------

def _fold(text):
    """Fold the Unicode vector glyphs to plain letters:
    î/ĵ (precomposed) and i/j/k + U+0302 become i/j/k;
    X + U+20D7 (a⃗) becomes the plain letter X (a vector
    NAME — the definitions it appears in mark it as one)."""
    t = str(text)
    t = t.replace("î", "i").replace("ĵ", "j")
    t = re.sub(r"([ijk])\u0302", r"\1", t)
    t = re.sub(r"([A-Za-z])\u20d7", r"\1", t)
    t = t.replace("−", "-").replace("–", "-")
    t = t.replace("×", "×")
    return t


def _cut_options(text):
    """Drop a trailing MCQ option block: '(A) ...' onwards."""
    m = re.search(r"\(\s*[aA]\s*\)\s", text)
    if m:
        return text[:m.start()].strip()
    return text


# ---------------------------------------------------------------------------
# A small evaluator over vector expressions.
# Values are ("s", sympy scalar) or ("v", (a, b, c)) with sympy
# components. Operators: + - (binary/unary), · (dot), × (cross),
# * and juxtaposition (scalar multiplication), / (scalar only).
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
    \s*(?:
    (?P<num>\d+(?:\.\d+)?)
    | (?P<unit>[ijk])(?![A-Za-z])
    | (?P<name>[A-Za-z])(?![A-Za-z])
    | (?P<op>[+\-·×*/(),])
    )""", re.X)


class _ParseFail(Exception):
    pass


def _tokenise(text, strict=True):
    toks = []
    i = 0
    while i < len(text):
        if text[i].isspace():
            i += 1
            continue
        m = _TOKEN_RE.match(text, i)
        if not m or m.end() == i:
            if strict:
                raise _ParseFail(f"bad token at {text[i:]!r}")
            break
        i = m.end()
        if m.group("num") is not None:
            toks.append(("num", sp.Rational(m.group("num"))
                         if "." not in m.group("num")
                         else sp.nsimplify(m.group("num"),
                                            rational=True)))
        elif m.group("unit") is not None:
            toks.append(("unit", m.group("unit")))
        elif m.group("name") is not None:
            toks.append(("name", m.group("name")))
        else:
            toks.append(("op", m.group("op")))
    return toks


def _vadd(a, b, sign=1):
    return ("v", tuple(x + sign * y for x, y in zip(a[1], b[1])))


def _combine_add(a, b, sign):
    if a[0] == "s" and b[0] == "s":
        return ("s", a[1] + sign * b[1])
    if a[0] == "v" and b[0] == "v":
        return _vadd(a, b, sign)
    raise _ParseFail("cannot add scalar and vector")


def _combine_mul(a, b, op):
    if op == "·":
        if a[0] == "v" and b[0] == "v":
            return ("s", sum(x * y for x, y in zip(a[1], b[1])))
        if a[0] == "s" and b[0] == "s":
            return ("s", a[1] * b[1])
        raise _ParseFail("dot product needs two vectors")
    if op == "×" and a[0] == "v" and b[0] == "v":
        (a1, a2, a3), (b1, b2, b3) = a[1], b[1]
        return ("v", (a2 * b3 - a3 * b2,
                      a3 * b1 - a1 * b3,
                      a1 * b2 - a2 * b1))
    # × between a scalar and a vector, *, juxtaposition: scaling.
    if a[0] == "s" and b[0] == "v":
        return ("v", tuple(a[1] * x for x in b[1]))
    if a[0] == "v" and b[0] == "s":
        return ("v", tuple(b[1] * x for x in a[1]))
    if a[0] == "s" and b[0] == "s":
        return ("s", a[1] * b[1])
    raise _ParseFail("vector x vector needs × or ·")


class _Parser:
    def __init__(self, toks, defs):
        self.toks = toks
        self.i = 0
        self.defs = defs

    def peek(self, ahead=0):
        j = self.i + ahead
        return self.toks[j] if j < len(self.toks) else (None, None)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def parse(self):
        val = self.expr()
        if self.i != len(self.toks):
            raise _ParseFail("trailing tokens")
        return val

    def expr(self):
        val = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.next()[1]
            rhs = self.term()
            val = _combine_add(val, rhs, 1 if op == "+" else -1)
        return val

    def term(self):
        val = self.factor()
        while True:
            tok = self.peek()
            if tok in (("op", "·"), ("op", "×"), ("op", "*")):
                op = self.next()[1]
                rhs = self.factor()
                val = _combine_mul(val, rhs, op)
            elif tok == ("op", "/"):
                self.next()
                rhs = self.factor()
                if val[0] != "s" or rhs[0] != "s":
                    raise _ParseFail("division is scalar-only")
                val = ("s", val[1] / rhs[1])
            elif tok[0] in ("num", "unit", "name") or \
                    tok == ("op", "("):
                rhs = self.factor()
                val = _combine_mul(val, rhs, "*")
            else:
                return val

    def factor(self):
        tok = self.peek()
        if tok == ("op", "-"):
            self.next()
            val = self.factor()
            if val[0] == "s":
                return ("s", -val[1])
            return ("v", tuple(-x for x in val[1]))
        if tok == ("op", "+"):
            self.next()
            return self.factor()
        if tok == ("op", "("):
            # A parenthesised tuple "(2, -3, 5)" is a vector;
            # anything else is a sub-expression.
            save = self.i
            try:
                return self._tuple()
            except _ParseFail:
                self.i = save
            self.next()
            val = self.expr()
            if self.next() != ("op", ")"):
                raise _ParseFail("missing )")
            return val
        if tok[0] == "num":
            # Scalar, or the first term of a component sum:
            # "2i" / "2 i" starts a vector literal.
            if self.peek(1)[0] == "unit":
                return self._component_sum()
            self.next()
            return ("s", tok[1])
        if tok[0] == "unit":
            return self._component_sum()
        if tok[0] == "name":
            self.next()
            if tok[1] in self.defs:
                return ("v", self.defs[tok[1]])
            raise _ParseFail(f"unknown vector {tok[1]}")
        raise _ParseFail(f"unexpected {tok}")

    def _tuple(self):
        # Consume "(a, b, c)" with scalar entries.
        self.next()  # (
        vals = []
        for k in range(3):
            sign = 1
            if self.peek() == ("op", "-"):
                self.next()
                sign = -1
            elif self.peek() == ("op", "+"):
                self.next()
            tok = self.next()
            if tok[0] != "num":
                raise _ParseFail("tuple entries must be numbers")
            vals.append(sign * tok[1])
            if k < 2:
                if self.next() != ("op", ","):
                    raise _ParseFail("tuple needs commas")
        if self.next() != ("op", ")"):
            raise _ParseFail("tuple needs )")
        return ("v", tuple(vals))

    def _component_sum(self):
        """Parse '2i - j + 2k' style literals. Stops before a
        +/- that is not followed by a [coef] unit term, so the
        outer expression keeps its own operators."""
        comp = [sp.Integer(0)] * 3
        sign = 1
        while True:
            coef = sp.Integer(1)
            tok = self.peek()
            if tok[0] == "num":
                coef = tok[1]
                self.next()
                tok = self.peek()
            if tok[0] != "unit":
                raise _ParseFail("component term needs a unit")
            self.next()
            comp[_UNITS.index(tok[1])] += sign * coef
            # Continue only on +/- followed by [num] unit.
            save = self.i
            tok = self.peek()
            if tok not in (("op", "+"), ("op", "-")):
                break
            nxt = self.peek(1)
            nxt2 = self.peek(2)
            if nxt[0] == "unit" or (nxt[0] == "num"
                                    and nxt2[0] == "unit"):
                sign = 1 if tok[1] == "+" else -1
                self.next()
                continue
            self.i = save
            break
        return ("v", tuple(comp))


def _eval_expr(text, defs):
    """Evaluate a vector expression string fully, or raise."""
    toks = _tokenise(text)
    if not toks:
        raise _ParseFail("empty")
    return _Parser(toks, defs).parse()


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _vec_str(vec):
    """(2, -1, 2) -> '2î - ĵ + 2k̂' (the board notation)."""
    parts = []
    for coef, unit in zip(vec, _UNITS):
        if coef == 0:
            continue
        glyph = _UNIT_GLYPH[unit]
        if coef == 1:
            term = glyph
        elif coef == -1:
            term = "-" + glyph
        else:
            term = f"{fmt(coef)}{glyph}"
        parts.append(term)
    if not parts:
        return "0"
    out = parts[0]
    for part in parts[1:]:
        if part.startswith("-"):
            out += " - " + part[1:]
        else:
            out += " + " + part
    return out


def _scalar_str(val):
    # Exact forms stay exact: fmt_num would decimalise
    # sqrt(605) to 24.5967, but the board answer is sqrt(605).
    if getattr(val, "is_rational", None) or \
            getattr(val, "is_integer", None):
        try:
            return fmt_num(val)
        except Exception:
            return fmt(val)
    return fmt(val)


def _magnitude(vec):
    return sp.sqrt(sum(x ** 2 for x in vec))


# ---------------------------------------------------------------------------
# Definitions: "a = 2i - j + 2k", "AB = ...", "a = (2, 3, -5)"
# ---------------------------------------------------------------------------

_DEF_RE = re.compile(r"(?<![A-Za-z])([A-Za-z]{1,2})\s*=\s*")


def _extract_defs(text):
    """Find 'NAME = <vector literal>' definitions. Returns
    (defs, spans) — spans are blanked out of the working text
    so the ask can be read from what remains."""
    defs = {}
    spans = []
    for m in _DEF_RE.finditer(text):
        name = m.group(1)
        rest = text[m.end():]
        # Tokenise tolerantly: prose after the value (the word
        # 'and', the next definition, ...) simply ends the
        # token stream.
        toks = _tokenise(rest, strict=False)
        if not toks:
            continue
        # Longest token prefix that parses completely as a
        # vector — the value may be followed by tokens that
        # belong to the question, not the definition.
        got = None
        for end in range(len(toks), 0, -1):
            parser = _Parser(toks[:end], defs)
            try:
                val = parser.parse()
            except _ParseFail:
                continue
            if val[0] == "v":
                got = (val[1], end)
                break
        if got is None:
            continue
        consumed = _consumed_chars(rest, got[1])
        if consumed <= 0:
            continue
        defs[name] = got[0]
        spans.append((m.start(), m.end() + consumed))
    return defs, spans


def _consumed_chars(text, ntoks):
    """Raw character length of the first ntoks tokens."""
    i = 0
    n = 0
    while n < ntoks and i < len(text):
        if text[i].isspace():
            i += 1
            continue
        m = _TOKEN_RE.match(text, i)
        if not m or m.end() == i:
            break
        i = m.end()
        n += 1
    return i


def _blank_spans(text, spans):
    chars = list(text)
    for a, b in spans:
        for i in range(a, min(b, len(chars))):
            chars[i] = " "
    return "".join(chars)


# ---------------------------------------------------------------------------
# The solver
# ---------------------------------------------------------------------------

def solve_vectors(question: str):
    """Solve a component-form vector question, or return None."""
    try:
        return _solve_vectors(question)
    except Exception:
        return None


def _solve_vectors(question):
    raw = str(question)
    # Unit-vector names written with a circumflex: â (a+U+0302)
    # asks for the unit vector of a.
    hat_names = [c for c in re.findall(r"([A-Za-z])\u0302", raw)
                 if c not in _UNITS]
    work = _cut_options(_fold(raw))
    defs, spans = _extract_defs(work)
    rest = _blank_spans(work, spans)
    wl = rest.lower()

    # --- Parallelogram: AB and DB (diagonal) given ---------
    if "parallelogram" in wl and "AB" in defs and "DB" in defs:
        ab, db = defs["AB"], defs["DB"]
        ad = tuple(a - d for a, d in zip(ab, db))
        cross = _combine_mul(("v", ab), ("v", ad), "×")[1]
        area = _magnitude(cross)
        steps = [
            "In parallelogram ABCD, AD = AB - DB (the diagonal "
            "DB = AB - AD rearranged).",
            f"AD = {_vec_str(ab)} - ({_vec_str(db)}) "
            f"= {_vec_str(ad)}",
            "Area = |AB x AD|.",
            f"AB x AD = {_vec_str(cross)}, so area = "
            f"{_scalar_str(area)}"
            + (f" ≈ {fmt_num(float(area))}" if not area.is_Integer
               else "") + " sq. units",
        ]
        return {"type": "vectors", "op": "parallelogram",
                "answer": f"AD = {_vec_str(ad)}, "
                          f"Area = {_scalar_str(area)}",
                "steps": steps}
    if "parallelogram" in wl and "AB" in defs and "AD" in defs:
        ab, ad = defs["AB"], defs["AD"]
        cross = _combine_mul(("v", ab), ("v", ad), "×")[1]
        area = _magnitude(cross)
        steps = [
            "Area of a parallelogram = |AB x AD| (cross product "
            "of adjacent sides).",
            f"AB x AD = {_vec_str(cross)}",
            f"Area = {_scalar_str(area)} sq. units",
        ]
        return {"type": "vectors", "op": "parallelogram_area",
                "answer": _scalar_str(area), "steps": steps}

    # --- |pa + qb| = |ra + sb| for UNIT vectors a, b --------
    mm = re.search(r"\|([^|]+)\|\s*=\s*\|([^|]+)\|", rest)
    if mm and ("unit" in wl or "मात्रक" in raw):
        got = _modulus_equation(mm.group(1), mm.group(2))
        if got is not None:
            return got

    # --- Unit vector -----------------------------------------
    if ("unit vector" in wl or "इकाई सदिश" in raw or hat_names):
        target = None
        m = re.search(r"direction\s+of\s+(?:the\s+)?(?:vector\s+)?"
                      r"([A-Za-z])\b", rest)
        if m and m.group(1) in defs:
            target = defs[m.group(1)]
        if target is None and hat_names and hat_names[0] in defs:
            target = defs[hat_names[0]]
        if target is None and len(defs) == 1:
            target = next(iter(defs.values()))
        if target is None:
            # A literal after "of": "unit vector of 2i - j + 2k"
            m = re.search(r"unit\s+vector\s+(?:of|in\s+the\s+"
                          r"direction\s+of)\s+(.+)$", rest)
            if m:
                try:
                    val = _eval_expr(m.group(1).strip(" .:"), defs)
                    if val[0] == "v":
                        target = val[1]
                except _ParseFail:
                    pass
        if target is not None:
            mag = _magnitude(target)
            if mag == 0:
                return None
            unit = tuple(sp.simplify(x / mag) for x in target)
            sq = " + ".join(f"{fmt(x)}^2" for x in target)
            steps = [
                f"|a| = sqrt({sq}) = {_scalar_str(mag)}",
                "Unit vector = a / |a|.",
            ]
            if mag.is_Integer and mag > 1 and all(
                    x.is_Integer for x in target):
                ans = f"(1/{fmt(mag)})({_vec_str(target)})"
                steps.append(f"= (1/{fmt(mag)})({_vec_str(target)})")
            else:
                ans = _vec_str(unit)
                steps.append(f"= {_vec_str(unit)}")
            return {"type": "vectors", "op": "unit_vector",
                    "answer": ans, "steps": steps}

    # --- Magnitude -------------------------------------------
    if "magnitude" in wl or "परिमाण" in raw:
        target = None
        m = re.search(r"magnitude\s+of\s+(.+)$", rest)
        if m:
            cand = m.group(1).strip(" .:")
            cand = re.sub(r"(?i)^(the\s+)?vector\s+", "", cand)
            if cand in defs:
                target = defs[cand]
            else:
                try:
                    val = _eval_expr(cand, defs)
                    if val[0] == "v":
                        target = val[1]
                except _ParseFail:
                    pass
        if target is None and len(defs) == 1:
            target = next(iter(defs.values()))
        if target is not None:
            mag = _magnitude(target)
            sq = " + ".join(f"{fmt(x)}^2" for x in target)
            steps = [
                f"|a| = sqrt({sq}) = sqrt({fmt(sum(x ** 2 for x in target))})",
                f"|a| = {_scalar_str(mag)}",
            ]
            return {"type": "vectors", "op": "magnitude",
                    "answer": _scalar_str(mag), "steps": steps}

    # --- Angle between two vectors ---------------------------
    if "angle between" in wl or ("कोण" in raw and "बीच" in raw):
        pair = _angle_pair(rest, defs)
        if pair is not None:
            a, b = pair
            dot = sum(x * y for x, y in zip(a, b))
            ma, mb = _magnitude(a), _magnitude(b)
            if ma == 0 or mb == 0:
                return None
            cosv = sp.simplify(dot / (ma * mb))
            steps = [
                f"a·b = {fmt(dot)}, |a| = {_scalar_str(ma)}, "
                f"|b| = {_scalar_str(mb)}",
                f"cos θ = a·b / (|a| |b|) = {_scalar_str(cosv)}",
            ]
            deg = _standard_degrees(cosv)
            if deg is not None:
                steps.append(f"θ = {deg}°")
                return {"type": "vectors", "op": "angle_between",
                        "answer": f"θ = {deg}°", "steps": steps}
            return {"type": "vectors", "op": "angle_between",
                    "answer": f"cos θ = {_scalar_str(cosv)}",
                    "steps": steps}

    # --- Direction cosines from the three angles -------------
    if "direction cosines" in wl:
        angs = re.findall(r"(-?\d+(?:\.\d+)?)\s*°", rest)
        if len(angs) >= 3:
            vals = []
            for a in angs[:3]:
                v = sp.cos(sp.rad(sp.Rational(a)))
                vals.append(sp.simplify(v))
            steps = [
                "Direction cosines are cos α, cos β, cos γ for "
                "the angles with the x, y, z axes.",
                "cos " + "°, cos ".join(angs[:3]) + "° = "
                + ", ".join(_scalar_str(v) for v in vals),
            ]
            return {"type": "vectors", "op": "direction_cosines",
                    "answer": "(" + ", ".join(
                        _scalar_str(v) for v in vals) + ")",
                    "steps": steps}

    # --- Equation of a coordinate plane ----------------------
    mp = re.search(r"equation\s+of\s+(?:the\s+)?"
                   r"(xy|yz|zx)[-\s]?plane", wl)
    if mp:
        plane = {"xy": "z = 0", "yz": "x = 0", "zx": "y = 0"}[
            mp.group(1)]
        steps = [
            f"Every point on the {mp.group(1).upper()} plane "
            f"has its third coordinate 0, so its equation is "
            f"{plane}.",
        ]
        return {"type": "vectors", "op": "plane_equation",
                "answer": plane, "steps": steps}

    # --- "dot / cross product of X and Y" --------------------
    # Runs on `work` (definitions intact): the operands are
    # names resolved through defs or literals, and the second
    # operand ends at an if/where boundary or the string end
    # ("... of a and b if a = ..., b = ...").
    mp2 = re.search(r"(dot|cross)\s+product\s+of\s+(.+?)\s+and\s+"
                    r"(.+?)(?:\s+if\b|\s+where\b|\s*$)", work)
    if mp2:
        try:
            va = _eval_expr(mp2.group(2).strip(" .:,"), defs)
            vb = _eval_expr(mp2.group(3).strip(" .:,"), defs)
        except _ParseFail:
            va = vb = None
        if va and vb and va[0] == "v" and vb[0] == "v":
            op = "·" if mp2.group(1) == "dot" else "×"
            val = _combine_mul(va, vb, op)
            if val[0] == "s":
                return {"type": "vectors", "op": "dot_product",
                        "answer": _scalar_str(val[1]),
                        "steps": _eval_steps("", val)}
            return {"type": "vectors", "op": "cross_product",
                    "answer": _vec_str(val[1]),
                    "steps": _eval_steps("", val)}

    # --- Bare vector expression ------------------------------
    text = rest.strip()
    text = re.sub(r"(?i)^\s*(what\s+is|evaluate|compute|"
                  r"calculate|find\s+the\s+value\s+of|find|"
                  r"simplify)\b[:\s]*", "", text)
    text = re.split(r"(?i)\b(?:if|given|where|when)\b", text)[0]
    text = re.sub(r"का\s*मान.*$", "", text)
    text = re.sub(r"(?i)\bis\s+equal\s+to.*$", "", text)
    text = text.strip(" .:।?")
    if text.endswith("="):
        text = text[:-1].strip()
    # |expr| as the whole ask: the magnitude.
    mb = re.fullmatch(r"\|\s*(.+?)\s*\|", text)
    if mb:
        try:
            val = _eval_expr(mb.group(1), defs)
        except _ParseFail:
            val = None
        if val is not None and val[0] == "v":
            mag = _magnitude(val[1])
            sq = " + ".join(f"{fmt(x)}^2" for x in val[1])
            return {"type": "vectors", "op": "magnitude",
                    "answer": _scalar_str(mag),
                    "steps": [f"|a| = sqrt({sq})",
                              f"|a| = {_scalar_str(mag)}"]}
    # The expression must contain a dot/cross or a unit glyph
    # sum — a plain arithmetic string is not ours to claim.
    if not re.search(r"[·×]|[ijk](?![A-Za-z])", text):
        return None
    # Nothing but maths tokens may remain.
    if re.search(r"[A-Za-z]{2,}", re.sub(
            r"(sin|cos|tan|log|sqrt)", "", text)):
        # Two+ letter words mean prose survived the strip.
        if not defs:
            return None
    try:
        val = _eval_expr(text, defs)
    except _ParseFail:
        return None
    if val[0] == "s":
        return {"type": "vectors", "op": "vector_evaluate",
                "answer": _scalar_str(val[1]),
                "steps": _eval_steps(text, val)}
    return {"type": "vectors", "op": "vector_evaluate",
            "answer": _vec_str(val[1]),
            "steps": _eval_steps(text, val)}


def _eval_steps(text, val):
    if val[0] == "s":
        return [f"Evaluate the vector expression: "
                f"{_scalar_str(val[1])}"]
    return [f"Evaluate the vector expression: {_vec_str(val[1])}"]


def _standard_degrees(cosv):
    """Degrees when cos θ is a standard value, else None."""
    try:
        deg = float(sp.deg(sp.acos(cosv)))
    except Exception:
        return None
    for std in (0, 30, 45, 60, 90, 120, 135, 150, 180):
        if abs(deg - std) < 1e-9:
            return std
    return None


def _angle_pair(rest, defs):
    """The two vectors of an angle-between ask: named in the
    text ('between a and b') or the two defined vectors."""
    m = re.search(r"between\s+([A-Za-z])\s+and\s+([A-Za-z])", rest)
    if m and m.group(1) in defs and m.group(2) in defs:
        return defs[m.group(1)], defs[m.group(2)]
    m = re.search(r"([A-Za-z])\s+तथा\s+([A-Za-z])", rest)
    if m and m.group(1) in defs and m.group(2) in defs:
        return defs[m.group(1)], defs[m.group(2)]
    if len(defs) == 2:
        vals = list(defs.values())
        return vals[0], vals[1]
    return None


def _modulus_equation(left, right):
    """|p·a + q·b| = |r·a + s·b| with a, b unit vectors:
    square both sides and solve for cos θ = a·b."""
    def combo(text):
        # Parse '2a + 3b' / '3a - 2b' into {name: coefficient}.
        t = text.replace(" ", "")
        if not re.fullmatch(r"[+-]?(\d+(?:\.\d+)?)?[A-Za-z]"
                            r"([+-](\d+(?:\.\d+)?)?[A-Za-z])?", t):
            return None
        out = {}
        for m in re.finditer(r"([+-]?)(\d+(?:\.\d+)?)?([A-Za-z])", t):
            coef = sp.Rational(m.group(2)) if m.group(2) \
                else sp.Integer(1)
            if m.group(1) == "-":
                coef = -coef
            out[m.group(3)] = out.get(m.group(3), 0) + coef
        return out if len(out) == 2 else None

    lc, rc = combo(left), combo(right)
    if not lc or not rc or set(lc) != set(rc):
        return None
    names = sorted(lc)
    a1, b1 = lc[names[0]], lc[names[1]]
    a2, b2 = rc[names[0]], rc[names[1]]
    # |..|^2 = a^2 + b^2 + 2ab·cosθ  (unit vectors)
    c = sp.symbols("c")
    eq = sp.Eq(a1 ** 2 + b1 ** 2 + 2 * a1 * b1 * c,
               a2 ** 2 + b2 ** 2 + 2 * a2 * b2 * c)
    sol = sp.solve(eq, c)
    if not sol:
        return None
    cosv = sol[0]
    steps = [
        "a and b are unit vectors, so |a| = |b| = 1 and "
        "|p·a + q·b|^2 = p^2 + q^2 + 2pq·cos θ.",
        f"Squaring both sides: {fmt(a1 ** 2 + b1 ** 2)} + "
        f"{fmt(2 * a1 * b1)}·cos θ = "
        f"{fmt(a2 ** 2 + b2 ** 2)} + {fmt(2 * a2 * b2)}·cos θ",
        f"cos θ = {_scalar_str(cosv)}",
    ]
    deg = _standard_degrees(cosv)
    if deg is not None:
        steps.append(f"θ = {deg}°")
        return {"type": "vectors", "op": "unit_modulus_angle",
                "answer": f"θ = {deg}°", "steps": steps}
    return {"type": "vectors", "op": "unit_modulus_angle",
            "answer": f"cos θ = {_scalar_str(cosv)}",
            "steps": steps}
