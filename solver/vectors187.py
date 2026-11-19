"""Wave 187: vector algebra in plain phone-typed (ASCII)
notation — the form-audit top-10 item #2 (probe 16).

Why this module exists (form audit, 19 Nov 2026): NCERT
Ex 10.2/10.3 questions typed on a phone write vectors as
`2i + 3j - k` — no Unicode î ĵ k̂ glyphs.  Wave 80's
solver/vectors.py does the maths and its component parser
accepts ASCII, but the router's Wave 80 gate only fires on
glyphs / a few ask words, so the plain dress fell through:
bare `i` was read as the complex unit I and the question
died with a parse error —

    "Find the angle between the vectors a = 2i + 3j - k
     and b = i - j + 2k"  ->  op=error (complex parse)

— or, worse, the geometry intent served FRAGMENTS: the
magnitude of 2i + 3j - k came back 3.60555 (sqrt(13), one
component dropped), its unit vector came back as a 2D
decimal pair, and the dot product of -i + 2j and 3i - j
came back 0 (correct: -5).

Design (decided after reading vectors.py + c12gaps142.py):
the maths is re-implemented locally on a strict literal
parser instead of dispatching into solve_vectors, because
the shared component parser mishandles a LEADING minus —
it negates the whole sum, so `-i + 2j` parses as (-1, -2)
instead of (-1, 2) (measured: solve_vectors gives
a.b = -1 for a = -i + 2j, b = 3i - j; correct is -5).
Signs here bind per term, exactly as written.  Rendering
(vec_str / scalar_str / answer shapes) is reused from
vectors.py so the ASCII dress answers in the same form
the Unicode dress already produces ("cos θ = -sqrt(21)/14",
"(1/3)(2î - ĵ + 2k̂)").

Strictness / the complex guard: bare `i` is also the
complex unit, so this module requires REAL vector evidence
before anything else — a literal or definition carrying a
j or k component, or an explicit vector word (vector /
sadish / सदिश) together with an [ijk] literal.  A lone
`Ni` term is never enough: "(2 + 3i)(1 - i)", "modulus of
3 + 4i", "express in a + ib form" carry no j/k and no
vector word, so they decline here and keep their current
behaviour byte-for-byte.  Every schema settles the
question COMPLETELY with SymPy-exact values, verified
before serving (lambda values are substituted back);
anything doubtful returns None.

Wiring (router.py): the house failure-only late gate after
the Wave 175 block (solve_vectors187), plus a narrow
fragment-repair entry (repair_vectors187) in the Wave 171
style for the measured geometry fragment ops — "vector
magnitude", "unit vector", "dot product" (type geometry)
— the scalar-only "projection" serve when the student
explicitly asked for the VECTOR projection, and the
cosines-only serve when BOTH direction ratios and
cosines were asked.  Repair displaces only when this
module settles the same ask completely AND the served
answer verifiably differs; a correct primary always
stands.

Family: angle between two vectors; magnitude |a|; unit
vector; projection of a on b (scalar + vector forms);
collinearity / parallel checks (two vectors, three
points); perpendicular check; find lambda / x so two
vectors are perpendicular / parallel; direction ratios
and direction cosines from components; dot / cross /
scalar / vector product; a + b / a - b / a.b / a x b with
named definitions.  Dresses: English + the Hinglish-Roman
and Devanagari triggers vectors.py itself uses (kon /
beech, pariman, ikai sadish; कोण / बीच, परिमाण,
इकाई सदिश).  Steps stay in Ganitra's plain English voice,
as in vectors.py.
"""
import math
import re

import sympy as sp

from .expression_parser import fmt, fmt_num
from .vectors import _fold, _magnitude, _scalar_str, _vec_str

_UNITS = "ijk"

# ---------------------------------------------------------------------------
# Strict ASCII literal parsing (per-term signs)
# ---------------------------------------------------------------------------

_NUM_COEF = r"\d+(?:\.\d+)?"
_TERM_NUM = rf"(?:{_NUM_COEF}\s*)?[ijk]"
_LIT_FULL = re.compile(
    rf"\s*[+-]?\s*{_TERM_NUM}(?:\s*[+-]\s*{_TERM_NUM})*\s*")
_LIT_FIND = re.compile(
    rf"(?<![A-Za-z0-9.])[+-]?\s*{_TERM_NUM}"
    rf"(?:\s*[+-]\s*{_TERM_NUM})*(?![A-Za-z])")
_TERM_FIND = re.compile(rf"([+-]?)\s*({_NUM_COEF})?\s*([ijk])")

_UNK_COEF = rf"(?:{_NUM_COEF}|lambda|λ|[a-z])"
_TERM_UNK = rf"(?:{_UNK_COEF}\s*)?[ijk]"
_ULIT_FULL = re.compile(
    rf"\s*[+-]?\s*{_TERM_UNK}(?:\s*[+-]\s*{_TERM_UNK})*\s*")
_ULIT_FIND = re.compile(
    rf"(?<![A-Za-z0-9.])[+-]?\s*{_TERM_UNK}"
    rf"(?:\s*[+-]\s*{_TERM_UNK})*(?![A-Za-z])")
_UTERM_FIND = re.compile(
    rf"([+-]?)\s*({_NUM_COEF}|lambda|λ|[a-z])?\s*([ijk])")


def _num(text):
    return sp.Rational(text) if "." not in text else \
        sp.nsimplify(text, rational=True)


def _parse_literal(text):
    """'2i + 3j - k' / '-i + 2j' -> (2, 3, -1) / (-1, 2, 0)
    with each sign bound to its own term, or None unless
    the whole string is one component sum."""
    s = str(text)
    if not _LIT_FULL.fullmatch(s):
        return None
    comp = [sp.Integer(0)] * 3
    terms = 0
    for sign, coef, unit in _TERM_FIND.findall(s):
        val = _num(coef) if coef else sp.Integer(1)
        if sign == "-":
            val = -val
        comp[_UNITS.index(unit)] += val
        terms += 1
    if terms == 0:
        return None
    return tuple(comp)


def _parse_unknown_literal(text):
    """Like _parse_literal but a coefficient may be one
    unknown ('lambda', 'λ' or a single letter: 'lambda j',
    'xi').  Returns (comp, symbol) or None; symbol is None
    for a fully numeric literal."""
    s = str(text)
    if not _ULIT_FULL.fullmatch(s):
        return None
    comp = [sp.Integer(0)] * 3
    sym = None
    terms = 0
    for sign, coef, unit in _UTERM_FIND.findall(s):
        if coef in ("lambda", "λ"):
            val = sp.Symbol("lambda")
        elif coef and not coef[0].isdigit():
            val = sp.Symbol(coef)
        elif coef:
            val = _num(coef)
        else:
            val = sp.Integer(1)
        if isinstance(val, sp.Symbol):
            if sym is not None and sym != val:
                return None
            sym = val
        if sign == "-":
            val = -val
        comp[_UNITS.index(unit)] += val
        terms += 1
    if terms == 0:
        return None
    return tuple(comp), sym


def _has_jk(vec_or_text):
    if isinstance(vec_or_text, (tuple, list)):
        return vec_or_text[1] != 0 or vec_or_text[2] != 0
    return re.search(r"[jk](?![A-Za-z])", str(vec_or_text)) \
        is not None


# ---------------------------------------------------------------------------
# Definitions and literals in the question text
# ---------------------------------------------------------------------------

_DEF_RE = re.compile(r"(?<![A-Za-z])([A-Za-z]{1,2})\s*=\s*")


def _extract(text):
    """Collect named definitions ('a = 2i + 3j - k') and
    bare literals, each with its text position.  Returns
    (defs, unknowns, cands):
      defs     name -> numeric (a, b, c)
      unknowns name -> (comp-with-symbol, symbol)
      cands    [(pos, numeric vec)] over defs + literals,
               in text order (def literals blanked first so
               they are not double-counted)."""
    defs, unknowns, spans = {}, {}, []
    for m in _DEF_RE.finditer(text):
        name = m.group(1)
        if name in _UNITS:
            continue
        rest = text[m.end():]
        got = None
        um = _ULIT_FIND.match(rest)
        if um:
            parsed = _parse_unknown_literal(um.group(0))
            if parsed is not None and parsed[1] is not None \
                    and _has_jk(parsed[0]):
                got = ("u", parsed)
        if got is None:
            lm = _LIT_FIND.match(rest)
            if lm:
                vec = _parse_literal(lm.group(0))
                if vec is not None:
                    got = ("n", vec)
        if got is None:
            continue
        if got[0] == "u":
            unknowns[name] = got[1]
            spans.append((m.start(), m.end() + len(
                um.group(0))))
        else:
            defs[name] = got[1]
            spans.append((m.start(), m.end() + len(
                lm.group(0))))
    chars = list(text)
    for a, b in spans:
        for i in range(a, min(b, len(chars))):
            chars[i] = " "
    blanked = "".join(chars)
    # Unknown-carrying literals are blanked too: otherwise
    # the numeric scan would pick up phantom fragments of
    # them ('i', 'j', '2k' out of 'i + lambda j + 2k').
    bare_unk = []
    for m in _ULIT_FIND.finditer(blanked):
        parsed = _parse_unknown_literal(m.group(0))
        # A real unknown literal carries a j or k component;
        # without one, letter+unit accidents of prose (the
        # Hinglish word 'ki' = k.i) would phantom-match.
        if parsed is not None and parsed[1] is not None \
                and _has_jk(parsed[0]):
            bare_unk.append((m.start(), parsed[0], parsed[1]))
            for i in range(m.start(), m.end()):
                chars[i] = " "
    blanked = "".join(chars)
    cands = []
    for m in _DEF_RE.finditer(text):
        name = m.group(1)
        if name in defs:
            cands.append((m.start(), defs[name]))
    for m in _LIT_FIND.finditer(blanked):
        vec = _parse_literal(m.group(0))
        if vec is not None:
            cands.append((m.start(), vec))
    cands.sort(key=lambda pv: pv[0])
    return defs, unknowns, cands, blanked, bare_unk


def _bare_unknown_literals(blanked):
    """Unknown-carrying literals in a text (used on the
    def-blanked text only for the evidence check)."""
    out = []
    for m in _ULIT_FIND.finditer(blanked):
        parsed = _parse_unknown_literal(m.group(0))
        if parsed is not None and parsed[1] is not None \
                and _has_jk(parsed[0]):
            out.append((m.start(), parsed[0], parsed[1]))
    return out


# ---------------------------------------------------------------------------
# Small maths helpers (exact; rendered via vectors.py)
# ---------------------------------------------------------------------------

def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _standard_degrees(cosv):
    try:
        deg = float(sp.deg(sp.acos(cosv)))
    except Exception:
        return None
    for std in (0, 30, 45, 60, 90, 120, 135, 150, 180):
        if abs(deg - std) < 1e-9:
            return std
    return None


def _result(op, answer, steps, value=None):
    out = {"type": "vectors", "op": op, "answer": answer,
           "steps": steps}
    if value is not None:
        out["value"] = value
    return out


def _angle_result(a, b):
    dot = _dot(a, b)
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
        return _result("angle_between", f"θ = {deg}°", steps)
    try:
        approx = math.degrees(math.acos(float(cosv)))
        steps.append(f"θ = cos^-1({_scalar_str(cosv)}) "
                     f"≈ {approx:.1f}°")
    except Exception:
        pass
    return _result("angle_between",
                   f"cos θ = {_scalar_str(cosv)}", steps)


def _magnitude_result(vec):
    mag = _magnitude(vec)
    sq = " + ".join(f"{fmt(x)}^2" for x in vec)
    total = fmt(sum(x ** 2 for x in vec))
    steps = [f"|a| = sqrt({sq}) = sqrt({total})",
             f"|a| = {_scalar_str(mag)}"]
    return _result("magnitude", _scalar_str(mag), steps,
                   value=float(mag))


def _unit_result(vec):
    mag = _magnitude(vec)
    if mag == 0:
        return None
    sq = " + ".join(f"{fmt(x)}^2" for x in vec)
    steps = [f"|a| = sqrt({sq}) = {_scalar_str(mag)}",
             "Unit vector = a / |a|."]
    unit = tuple(sp.simplify(x / mag) for x in vec)
    if mag.is_Integer and mag > 1 and all(
            x.is_Integer for x in vec):
        ans = f"(1/{fmt(mag)})({_vec_str(vec)})"
        steps.append(f"= (1/{fmt(mag)})({_vec_str(vec)})")
    else:
        ans = _vec_str(unit)
        steps.append(f"= {_vec_str(unit)}")
    return _result("unit_vector", ans, steps,
                   value=tuple(float(x) for x in unit))


def _pair(cands):
    """The two operand vectors of a binary ask: the first
    two candidate OCCURRENCES in text order (so the angle
    between a vector and itself still settles, θ = 0).
    More than two DISTINCT vectors in the text makes the
    pairing ambiguous — decline (mirrors Wave 142's guard
    on loose-vector asks)."""
    occ = [vec for _, vec in cands]
    distinct = []
    for vec in occ:
        if vec not in distinct:
            distinct.append(vec)
    if len(distinct) > 2 or len(occ) < 2:
        return None
    return occ[0], occ[1]


def _target(cands, wl, keyword_pos):
    """One vector for a single-vector ask: the candidate
    right after the ask keyword, else the only candidate."""
    after = [v for p, v in cands if p >= keyword_pos]
    uniq_after = []
    for v in after:
        if v not in uniq_after:
            uniq_after.append(v)
    if len(uniq_after) == 1:
        return uniq_after[0]
    uniq = []
    for _, v in cands:
        if v not in uniq:
            uniq.append(v)
    if len(uniq) == 1:
        return uniq[0]
    return None


# ---------------------------------------------------------------------------
# Lambda / unknown schemas (perpendicular / parallel)
# ---------------------------------------------------------------------------

def _lambda_schema(kind, vecs, sym):
    """kind is 'perpendicular' or 'parallel'.  vecs are two
    component tuples of sympy expressions in the single
    symbol sym.  Every served value is verified by
    substitution before returning."""
    a, b = vecs
    if kind == "perpendicular":
        d = sp.expand(_dot(a, b))
        if d.free_symbols - {sym}:
            return None
        poly = sp.Poly(d, sym) if d.has(sym) else None
        if poly is not None and poly.degree() > 1:
            return None
        name = str(sym)
        if poly is None or poly.degree() == 0:
            if sp.simplify(d) == 0:
                return _result(
                    "perpendicular_lambda",
                    f"Perpendicular for every value of {name}",
                    ["a·b = 0 for every value of "
                     f"{name}, so the vectors are "
                     "perpendicular for all "
                     f"{name}."])
            return _result(
                "perpendicular_lambda",
                f"No value of {name} makes the vectors "
                "perpendicular",
                [f"a·b = {fmt(d)}, which is never 0, so no "
                 f"value of {name} makes the vectors "
                 "perpendicular."])
        sol = sp.solve(sp.Eq(d, 0), sym)
        if len(sol) != 1 or sol[0].free_symbols:
            return None
        val = sol[0]
        if sp.simplify(_dot(tuple(
                sp.expand(c.subs(sym, val)) for c in a),
                tuple(sp.expand(c.subs(sym, val))
                      for c in b))) != 0:
            return None
        steps = [
            "Perpendicular vectors have dot product 0.",
            f"a·b = {fmt(d)} = 0",
            f"{name} = {fmt_num(val)}",
        ]
        return _result("perpendicular_lambda",
                       f"{name} = {fmt_num(val)}", steps)
    # parallel: cross product must vanish component-wise.
    cr = [sp.expand(c) for c in _cross(a, b)]
    name = str(sym)
    cands = []
    for comp in cr:
        if comp.free_symbols - {sym}:
            return None
        if not comp.has(sym):
            if sp.simplify(comp) != 0:
                return _result(
                    "parallel_lambda",
                    f"No value of {name} makes the vectors "
                    "parallel",
                    [f"a x b = {_vec_str(tuple(cr))} — one "
                     "component is a non-zero constant, so "
                     "the cross product can never be 0."])
            continue
        poly = sp.Poly(comp, sym)
        if poly.degree() > 1:
            return None
        sol = sp.solve(sp.Eq(comp, 0), sym)
        if len(sol) != 1 or sol[0].free_symbols:
            return None
        cands.append(sol[0])
    if not cands:
        return _result(
            "parallel_lambda",
            f"Parallel for every value of {name}",
            ["a x b = 0 for every value of "
             f"{name}, so the vectors are parallel for "
             f"all {name}."])
    val = cands[0]
    if any(sp.simplify(c - val) != 0 for c in cands):
        return None
    av = tuple(sp.expand(c.subs(sym, val)) for c in a)
    bv = tuple(sp.expand(c.subs(sym, val)) for c in b)
    if any(sp.simplify(c) != 0 for c in _cross(av, bv)):
        return None
    steps = [
        "Parallel vectors have cross product 0 "
        "(components in the same ratio).",
        f"a x b = {_vec_str(tuple(cr))} = 0",
        f"{name} = {fmt_num(val)}",
    ]
    return _result("parallel_lambda",
                   f"{name} = {fmt_num(val)}", steps)


# ---------------------------------------------------------------------------
# The solver
# ---------------------------------------------------------------------------

def solve_vectors187(question: str):
    """Wave 187 ASCII vector schema; None unless strict
    ASCII vector evidence holds and one schema settles the
    question completely."""
    try:
        return _solve(question)
    except Exception:
        return None


def _solve(question):
    raw = str(question)
    work = _fold(raw)
    wl = work.lower()
    defs, unknowns, cands, blanked, bare_unk = _extract(work)

    # --- Evidence gate (the complex guard) ----------------
    jk = any(_has_jk(v) for _, v in cands) or \
        any(_has_jk(comp) for comp, _ in unknowns.values()) or \
        any(_has_jk(comp) for _, comp, _ in bare_unk)
    vector_word = ("vector" in wl or "sadish" in wl
                   or "सदिश" in raw)
    # Three 3D points + a collinearity ask is vector
    # evidence of its own (no ijk literal is present).
    pts_evidence = len(re.findall(
        r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*,"
        r"\s*-?\d+(?:\.\d+)?\s*\)", work)) == 3 and \
        ("collinear" in wl or "समरेख" in raw)
    if not jk and not (vector_word and cands) \
            and not pts_evidence:
        return None
    # Complex-family markers with no j/k literal: never ours.
    if not jk and any(m in wl for m in (
            "ib form", "conjugate", "argument", "complex",
            "modulus of", "real part", "imaginary part")):
        return None

    hindi = any("ऀ" <= c <= "ॿ" for c in raw)

    # --- Unknown (lambda / x) schemas ----------------------
    if unknowns or bare_unk:
        vecs = []
        syms = set()
        for comp, sym in unknowns.values():
            vecs.append(comp)
            syms.add(sym)
        for _, vec in cands:
            vecs.append(tuple(vec))
        for _, comp, sym in bare_unk:
            vecs.append(comp)
            syms.add(sym)
        # Keep text order irrelevant: exactly two vectors
        # and one symbol, one of them numeric.
        unk_vecs = [v for v in vecs
                    if any(isinstance(c, sp.Symbol)
                           or getattr(c, "free_symbols", None)
                           for c in v)]
        num_vecs = [v for v in vecs if v not in unk_vecs]
        if len(syms) == 1 and len(unk_vecs) >= 1 and \
                len(unk_vecs) + len(num_vecs) == 2:
            sym = next(iter(syms))
            pair = (unk_vecs + num_vecs)[:2] \
                if num_vecs else unk_vecs[:2]
            if "perpendicular" in wl or "लंबवत" in raw \
                    or "lambvat" in wl:
                return _lambda_schema("perpendicular",
                                      pair, sym)
            if "parallel" in wl or "collinear" in wl \
                    or "समांतर" in raw or "samantar" in wl:
                return _lambda_schema("parallel", pair, sym)
        return None

    # --- Angle between two vectors --------------------------
    angle_ask = ("angle between" in wl
                 or ("kon" in wl and "beech" in wl)
                 or ("कोण" in raw and "बीच" in raw))
    if angle_ask:
        # A second, different ask in the same question is a
        # multi-part question — not ours to half-serve.
        if any(p in wl for p in ("dot product",
                                 "cross product",
                                 "scalar product",
                                 "vector product")):
            return None
        pair = _pair(cands)
        if pair is None:
            return None
        return _angle_result(pair[0], pair[1])

    # --- Projection of a on b --------------------------------
    if "projection" in wl or "प्रक्षेप" in raw:
        pair = _pair(cands)
        if pair is None:
            return None
        a, b = pair
        # 'projection of X on Y': X precedes ' on ', Y after
        # it — candidate order in the text already gives
        # (a, b) for the standard dress.
        dot = _dot(a, b)
        mb = _magnitude(b)
        if mb == 0:
            return None
        # The ask FORM must be explicit: "vector
        # projection of ..." / "projection vector of ...".
        # The bare adjacent words are not enough — the
        # router's wrapper-core pass compresses "projection
        # of the vector X on ..." into "projection vector
        # X on ...", which is a SCALAR-projection ask in
        # compressed dress and must keep the scalar serve.
        if "vector projection of" in wl or \
                "projection vector of" in wl:
            coef = sp.simplify(dot / (mb ** 2))
            proj = tuple(sp.simplify(coef * x) for x in b)
            steps = [
                f"a·b = {fmt(dot)}, |b|^2 = {fmt(mb ** 2)}",
                "Vector projection of a on b = "
                "((a·b / |b|^2)) b",
                f"= ({fmt(coef)})({_vec_str(b)}) "
                f"= {_vec_str(proj)}",
            ]
            return _result("vector_projection",
                           _vec_str(proj), steps)
        val = sp.simplify(dot / mb)
        steps = [
            f"a·b = {fmt(dot)}, |b| = {_scalar_str(mb)}",
            "Scalar projection of a on b = a·b / |b| "
            f"= {_scalar_str(val)}",
        ]
        return _result("projection", _scalar_str(val), steps)

    # --- Unit vector ------------------------------------------
    if "unit vector" in wl or "ikai sadish" in wl \
            or "ekai sadish" in wl or "इकाई सदिश" in raw \
            or "मात्रक सदिश" in raw:
        if "perpendicular" in wl:
            return None  # unit-perpendicular is Wave 142's
        pos = min([p for p in (wl.find("unit vector"),
                               wl.find("ikai sadish")) if p >= 0]
                  or [0])
        vec = _target(cands, wl, pos)
        if vec is None:
            return None
        return _unit_result(vec)

    # --- Direction ratios / cosines ---------------------------
    if "direction ratios" in wl or "direction cosines" in wl \
            or "दिक्" in raw:
        pos = min([p for p in (wl.find("direction ratios"),
                               wl.find("direction cosines"))
                   if p >= 0] or [0])
        vec = _target(cands, wl, pos)
        if vec is None:
            return None
        mag = _magnitude(vec)
        if mag == 0:
            return None
        cosines = tuple(sp.simplify(x / mag) for x in vec)
        cos_str = "(" + ", ".join(
            _scalar_str(c) for c in cosines) + ")"
        ratio_str = "(" + ", ".join(fmt(x) for x in vec) + ")"
        if "direction ratios" in wl and \
                "direction cosines" in wl:
            steps = [
                "Direction ratios are the components of "
                f"the vector: {ratio_str}.",
                f"|a| = {_scalar_str(mag)}, so the direction "
                f"cosines are {cos_str}.",
            ]
            return _result(
                "direction_ratios_cosines",
                f"Direction ratios: {ratio_str}, "
                f"Direction cosines: {cos_str}", steps)
        if "direction ratios" in wl:
            steps = [
                "Direction ratios are the components of "
                "the vector.",
                f"Direction ratios = {ratio_str}",
            ]
            return _result("direction_ratios", ratio_str,
                           steps)
        steps = [
            f"|a| = {_scalar_str(mag)}",
            "Direction cosines = components / |a| "
            f"= {cos_str}",
        ]
        return _result("direction_cosines_vector", cos_str,
                       steps)

    # --- Magnitude ---------------------------------------------
    mag_pos = -1
    for kw in ("magnitude", "modulus", "pariman"):
        p = wl.find(kw)
        if p >= 0:
            mag_pos = p
            break
    if mag_pos < 0 and "परिमाण" in raw:
        mag_pos = 0
    mbar = re.search(r"\|\s*([^|]+?)\s*\|", work)
    # "A vector of magnitude 5 in the direction of ..." —
    # there the magnitude is GIVEN, not asked (Wave 142's
    # family); serving |literal| would be a wrong answer.
    if re.search(r"\bmagnitude\s+(?:of\s+)?\d+"
                 r"(?!\s*[ijk](?![A-Za-z]))", wl) or \
            re.search(r"\bof\s+magnitude\s+\d+"
                      r"(?!\s*[ijk](?![A-Za-z]))", wl):
        mag_pos = -1
        mbar = None
    if mag_pos >= 0 or mbar:
        vec = None
        if mbar:
            inner = mbar.group(1).strip()
            if inner in defs:
                vec = defs[inner]
            else:
                vec = _parse_literal(inner)
        if vec is None:
            vec = _target(cands, wl, max(mag_pos, 0))
        if vec is None:
            return None
        return _magnitude_result(vec)

    # --- Perpendicular check (no unknown) -----------------------
    if "perpendicular" in wl or "लंबवत" in raw:
        pair = _pair(cands)
        if pair is None:
            return None
        a, b = pair
        dot = _dot(a, b)
        steps = [f"a·b = {fmt(dot)}"]
        if dot == 0:
            steps.append("a·b = 0, so the vectors are "
                         "perpendicular.")
            return _result("perpendicular_check",
                           "Yes, the vectors are "
                           "perpendicular", steps)
        steps.append("a·b is not 0, so the vectors are "
                     "not perpendicular.")
        return _result("perpendicular_check",
                       "No, the vectors are not "
                       "perpendicular", steps)

    # --- Collinear / parallel check ------------------------------
    if "collinear" in wl or "parallel" in wl \
            or "समरेख" in raw or "समांतर" in raw \
            or "samrekh" in wl or "samantar" in wl:
        word = "parallel" if ("parallel" in wl
                              or "समांतर" in raw
                              or "samantar" in wl) \
            else "collinear"
        pts = re.findall(
            r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
            r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)"
            r"\s*\)", work)
        if ("point" in wl or len(pts) == 3) and len(pts) == 3:
            A, B, C = [tuple(_num(v) for v in p) for p in pts]
            ab = tuple(y - x for x, y in zip(A, B))
            ac = tuple(y - x for x, y in zip(A, C))
            cr = _cross(ab, ac)
            steps = [f"AB = {_vec_str(ab)}, "
                     f"AC = {_vec_str(ac)}",
                     f"AB x AC = {_vec_str(cr)}"]
            if all(v == 0 for v in cr):
                steps.append("AB x AC = 0, so the points "
                             "lie on one line.")
                return _result("collinear_points",
                               "Yes, the points are "
                               "collinear", steps)
            steps.append("AB x AC is not 0, so the points "
                         "do not lie on one line.")
            return _result("collinear_points",
                           "No, the points are not "
                           "collinear", steps)
        pair = _pair(cands)
        if pair is None:
            return None
        a, b = pair
        cr = _cross(a, b)
        steps = [f"a x b = {_vec_str(cr)}"]
        if all(v == 0 for v in cr):
            ratio = None
            for u, v in zip(a, b):
                if u != 0:
                    ratio = sp.simplify(v / u)
                    break
            if ratio is not None:
                steps.append(
                    f"a x b = 0 and b = ({fmt(ratio)})a, "
                    f"so the vectors are {word}.")
            else:
                steps.append(f"a x b = 0, so the vectors "
                             f"are {word}.")
            return _result(f"{word}_vectors_check"
                           if word == "parallel" else
                           "collinear_vectors",
                           f"Yes, the vectors are {word}",
                           steps)
        steps.append(f"a x b is not 0, so the vectors are "
                     f"not {word}.")
        return _result(f"{word}_vectors_check"
                       if word == "parallel" else
                       "collinear_vectors",
                       f"No, the vectors are not {word}",
                       steps)

    # --- Dot / cross product asks ---------------------------------
    prod = None
    if "dot product" in wl or "scalar product" in wl:
        prod = "dot"
    elif "cross product" in wl or "vector product" in wl:
        prod = "cross"
    if prod:
        pair = _pair(cands)
        if pair is None:
            return None
        a, b = pair
        if prod == "dot":
            terms = " + ".join(
                f"({fmt(x)})({fmt(y)})"
                for x, y in zip(a, b))
            val = _dot(a, b)
            steps = [f"a·b = {terms} = {fmt(val)}"]
            return _result("dot_product",
                           _scalar_str(val), steps,
                           value=float(val))
        val = _cross(a, b)
        steps = [f"a x b = {_vec_str(val)}"]
        return _result("cross_product", _vec_str(val),
                       steps)

    # --- Named expression: a + b / a - b / a.b / a x b -------------
    if len(defs) >= 2:
        m = re.search(
            r"\b([A-Za-z]{1,2})\s*([+\-])\s*([A-Za-z]{1,2})\b",
            blanked)
        op = None
        if m and m.group(1) in defs and m.group(3) in defs:
            op = ("add" if m.group(2) == "+" else "sub",
                  m.group(1), m.group(3))
        if op is None:
            m = re.search(
                r"\b([A-Za-z]{1,2})\s*([.·×])\s*"
                r"([A-Za-z]{1,2})\b", blanked)
            if m and m.group(1) in defs \
                    and m.group(3) in defs:
                op = ("dot" if m.group(2) in (".", "·")
                      else "cross", m.group(1), m.group(3))
        if op is None:
            m = re.search(
                r"\b([A-Za-z]{1,2})\s+x\s+([A-Za-z]{1,2})\b",
                blanked)
            if m and m.group(1) in defs \
                    and m.group(2) in defs:
                op = ("cross", m.group(1), m.group(2))
        if op is not None:
            kind, na, nb = op
            a, b = defs[na], defs[nb]
            if kind in ("add", "sub"):
                s = 1 if kind == "add" else -1
                val = tuple(x + s * y for x, y in zip(a, b))
                sym = "+" if kind == "add" else "-"
                steps = [f"{na} {sym} {nb} = "
                         f"({_vec_str(a)}) {sym} "
                         f"({_vec_str(b)}) "
                         f"= {_vec_str(val)}"]
                return _result("vector_evaluate",
                               _vec_str(val), steps)
            if kind == "dot":
                val = _dot(a, b)
                steps = [f"{na}·{nb} = {fmt(val)}"]
                return _result("dot_product",
                               _scalar_str(val), steps,
                               value=float(val))
            val = _cross(a, b)
            steps = [f"{na} x {nb} = {_vec_str(val)}"]
            return _result("cross_product", _vec_str(val),
                           steps)
    return None


# ---------------------------------------------------------------------------
# Fragment repair (Wave 171 style)
# ---------------------------------------------------------------------------

def _float_of(text):
    try:
        return float(sp.N(sp.sympify(str(text))))
    except Exception:
        try:
            return float(text)
        except Exception:
            return None


def _answer_components(text):
    """'0.5547i + 0.8321j' -> {'i': 0.5547, 'j': 0.8321,
    'k': 0.0}; None when no unit terms are present."""
    out = {}
    for coef, unit in re.findall(
            r"(-?\d+(?:\.\d+)?)\s*\*?\s*([ijkîĵ])", str(text)):
        unit = {"î": "i", "ĵ": "j"}.get(unit, unit)
        out[unit] = float(coef)
    if not out:
        return None
    for u in "ijk":
        out.setdefault(u, 0.0)
    return out


def repair_vectors187(question, result):
    """Displace a measured fragment serve with the strict
    Wave 187 result for the same ask, only when the served
    answer verifiably differs.  Returns the replacement
    result dict or None (primary stands)."""
    if not isinstance(result, dict):
        return None
    op = result.get("op")
    typ = result.get("type")
    wl = _fold(str(question)).lower()
    try:
        mine = solve_vectors187(question)
    except Exception:
        mine = None
    if mine is None:
        return None
    if typ == "geometry" and op == "vector magnitude" \
            and mine.get("op") == "magnitude":
        served = _float_of(result.get("answer"))
        exact = mine.get("value")
        if served is not None and exact is not None \
                and abs(served - exact) > 1e-4:
            return mine
        return None
    if typ == "geometry" and op == "unit vector" \
            and mine.get("op") == "unit_vector":
        served = _answer_components(result.get("answer"))
        exact = mine.get("value")
        if served is None or exact is None:
            return None
        if any(abs(served[u] - exact[i]) > 2e-3
               for i, u in enumerate("ijk")):
            return mine
        return None
    if typ == "geometry" and op == "dot product" \
            and mine.get("op") == "dot_product":
        served = _float_of(result.get("answer"))
        exact = mine.get("value")
        if served is not None and exact is not None \
                and abs(served - exact) > 1e-9:
            return mine
        return None
    if op == "projection" \
            and mine.get("op") == "vector_projection" \
            and ("vector projection of" in wl
                 or "projection vector of" in wl):
        return mine
    if op == "direction_cosines_vector" \
            and mine.get("op") == "direction_ratios_cosines":
        return mine
    return None
