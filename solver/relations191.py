"""Wave 191: Relations & Functions proof / classification
engine (form-audit top-10 item #6; audit rows 10-12).

Why this module exists: the form audit (19 Nov 2026) probed
two Class 12 Relations & Functions staples and both missed
natively —

  05: "Show that the relation R in the set {1, 2, 3} given
      by R = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 3)} is
      reflexive but neither symmetric nor transitive"
      -> parse error (no relation-property engine existed;
      proofs.py verifies equations and serves textbook
      irrationality proofs only).
  06: "Let f : R -> R be defined as f(x) = x^4. Is f
      one-one or onto? (A)...(D) neither one-one nor onto"
      -> fell to a statistics guide.

This module is that engine, in the house style of Waves
169/175: it fires only when it settles the question
COMPLETELY by a mechanical decision procedure, and anything
unparsable or unrecognised returns None so routing
continues unchanged.  A wrong verdict is worse than a
native miss, so every verdict below is COMPUTED, never
copied from the question's own claim:

(a) Relation properties on FINITE sets.  The roster is
    parsed (or enumerated from a decidable set-builder
    condition on a finite stated set), then reflexive /
    symmetric / transitive are checked EXHAUSTIVELY over
    the roster.  Every negative verdict carries the
    concrete counterexample pair / triple the check found;
    equivalence = all three, stated as such.

(b) One-one / onto classification for a fixed catalogue of
    function forms (monomials x^n, |x|, greatest integer
    [x], signum, 1/x, constants, linear ax + b, and
    linear-over-linear rationals) over the standard
    NCERT domains / codomains (R, N, Z, Q, R - {0},
    R - {k}, (0, inf), [0, inf)).  Each form's verdict is
    decided by the encoded parity / monotonicity / range
    argument for that form; a one-one failure is served
    only with a witness pair whose two f-values are
    re-evaluated and confirmed equal before serving, and
    an onto failure only with a concrete codomain value
    mechanically confirmed to have no preimage.
    UNRECOGNISED functions decline — no guessed verdicts.

(c) Counting forms: relations on an n-set (2^(n^2)),
    reflexive relations (2^(n^2-n)), symmetric relations
    (2^(n(n+1)/2)), equivalence relations (Bell number,
    exact Stirling-number sum; with forced pairs the pairs
    are contracted first), functions m^n, one-one
    functions P(m, n), onto functions by
    inclusion-exclusion.

Wiring: a failure-only gate at the end of
router._solve_question_uncached, after the Wave 175 block —
a question the solver already answers is never displaced
(plain f(x) evaluation, sets_basics operations and the
proofs.py serves are pinned as controls).
"""
import re
from fractions import Fraction
from math import comb, factorial

import sympy as sp

from .expression_parser import parse_expression

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _prep(text):
    s = str(text).translate(_DEV_DIGITS)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("→", "->").replace("⟶", "->")
    s = s.replace("≤", "<=").replace("≥", ">=")
    s = s.replace("≠", "!=").replace("∞", "inf")
    s = s.replace("²", "^2").replace("³", "^3").replace("⁴", "^4")
    return s


def _hindi(text):
    return bool(re.search(r"[\u0900-\u097F]", str(text)))


def _result(op, answer, steps, typ="relations"):
    return {"type": typ, "op": op, "answer": answer,
            "steps": steps}


def _fmt_frac(v):
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    return f"{v.numerator}/{v.denominator}"


# ===========================================================================
# (a) Relation properties on finite sets
# ===========================================================================

_PROP_WORDS = ("reflexive", "symmetric", "transitive",
               "equivalence")


def _parse_elements(text):
    """'1, 2, 3' / 'a, b, c' -> ordered element list, or None.
    Elements are ints or single letters, never mixed."""
    items = [t.strip() for t in text.split(",") if t.strip()]
    if not items or len(items) > 12:
        return None
    out = []
    kind = None
    for t in items:
        if re.fullmatch(r"-?\d+", t):
            k, v = "int", int(t)
        elif re.fullmatch(r"[a-zA-Z]", t):
            k, v = "str", t
        else:
            return None
        if kind is None:
            kind = k
        elif k != kind:
            return None
        out.append(v)
    if len(set(out)) != len(out):
        return None
    return out


def _elem_key(v):
    return (0, v) if isinstance(v, int) else (1, str(v))


def _show_set(elems):
    return "{" + ", ".join(str(v) for v in
                            sorted(elems, key=_elem_key)) + "}"


def _show_pair(p):
    return f"({p[0]}, {p[1]})"


def _show_roster(rel):
    return "{" + ", ".join(_show_pair(p) for p in
                            sorted(rel, key=lambda p:
                                   (_elem_key(p[0]),
                                    _elem_key(p[1])))) + "}"


def _condition_fn(cond):
    """A decidable set-builder condition on (x, y) -> a
    predicate, or None when the condition is outside the
    recognised catalogue.  Int elements only (the caller
    checks); x = y / x != y also work for letters."""
    c = " " + re.sub(r"\s+", " ", cond.strip().lower()) + " "
    m = re.search(r"\|\s*x\s*-\s*y\s*\|\s*is\s+divisible\s+by\s+"
                  r"(\d+)", c)
    if m:
        k = int(m.group(1))
        return lambda x, y: (x - y) % k == 0
    m = re.search(r"x\s*-\s*y\s+is\s+divisible\s+by\s+(\d+)", c)
    if m:
        k = int(m.group(1))
        return lambda x, y: (x - y) % k == 0
    m = re.search(r"x\s*\+\s*y\s+is\s+divisible\s+by\s+(\d+)", c)
    if m:
        k = int(m.group(1))
        return lambda x, y: (x + y) % k == 0
    m = re.search(r"(x\s*-\s*y|x\s*\+\s*y)\s+is\s+(even|odd)", c)
    if m:
        plus = "+" in m.group(1)
        want = 0 if m.group(2) == "even" else 1
        if plus:
            return lambda x, y: (x + y) % 2 == want
        return lambda x, y: (x - y) % 2 == want
    m = re.search(r"x\s*\+\s*y\s*=\s*(-?\d+)", c)
    if m:
        k = int(m.group(1))
        return lambda x, y: x + y == k
    m = re.search(r"x\s*-\s*y\s*=\s*(-?\d+)", c)
    if m:
        k = int(m.group(1))
        return lambda x, y: x - y == k
    if re.search(r"\bx\s+divides\s+y\b", c) or \
            re.search(r"y\s+is\s+divisible\s+by\s+x", c) or \
            re.search(r"y\s+is\s+a\s+multiple\s+of\s+x", c):
        return lambda x, y: x != 0 and y % x == 0
    if re.search(r"\by\s+divides\s+x\b", c) or \
            re.search(r"x\s+is\s+divisible\s+by\s+y", c) or \
            re.search(r"x\s+is\s+a\s+multiple\s+of\s+y", c):
        return lambda x, y: y != 0 and x % y == 0
    m = re.search(r"x\s*(<=|>=|!=|<|>|=)\s*y", c)
    if m:
        op = m.group(1)
        if op == "<":
            return lambda x, y: x < y
        if op == "<=":
            return lambda x, y: x <= y
        if op == ">":
            return lambda x, y: x > y
        if op == ">=":
            return lambda x, y: x >= y
        if op == "=":
            return lambda x, y: x == y
        return lambda x, y: x != y
    return None


def _extract_relation(q):
    """-> (elements, relation set, builder_text or None), or
    None.  Recognises a roster {(a, b), ...} and a
    set-builder {(x, y) : cond} / {(a, b) : cond} on a
    finite stated set."""
    # Set-builder first (its braces contain a ':' condition).
    mb = re.search(r"\{\s*\(\s*[xyab]\s*,\s*[xyab]\s*\)\s*:\s*"
                   r"([^}]*)\}", q)
    builder = None
    rel = None
    if mb:
        builder = mb.group(1).strip()
        rest = q[:mb.start()] + " " + q[mb.end():]
    else:
        rest = q
    # Roster of pairs.
    mr = re.search(r"\{((?:\s*\(\s*[^()]*\s*\)\s*,?)+)\}", rest)
    if mr and builder is None:
        pair_texts = re.findall(r"\(\s*([^()]*)\s*\)",
                                mr.group(1))
        pairs = []
        ok = True
        for pt in pair_texts:
            parts = [t.strip() for t in pt.split(",")]
            if len(parts) != 2:
                ok = False
                break
            vals = []
            for t in parts:
                if re.fullmatch(r"-?\d+", t):
                    vals.append(int(t))
                elif re.fullmatch(r"[a-zA-Z]", t):
                    vals.append(t)
                else:
                    ok = False
                    break
            if not ok:
                break
            pairs.append((vals[0], vals[1]))
        if not ok or not pairs:
            return None
        rel = set(pairs)
        rest = rest[:mr.start()] + " " + rest[mr.end():]
    # The underlying set: a plain {..} group left over.
    elems = None
    for sm in re.finditer(r"\{([^{}]*)\}", rest):
        cand = _parse_elements(sm.group(1))
        if cand is not None:
            elems = cand
            break
    if builder is not None:
        fn = _condition_fn(builder)
        if fn is None or elems is None:
            return None
        if any(not isinstance(v, int) for v in elems):
            # Arithmetic conditions need int elements; only
            # x = y / x != y make sense for letters, and the
            # predicate still runs on them harmlessly — but
            # a divisibility lambda would crash, so re-check:
            if not re.search(r"x\s*(=|!=)\s*y", builder):
                return None
        rel = {(x, y) for x in elems for y in elems
               if fn(x, y)}
        return elems, rel, builder
    if rel is None:
        return None
    if elems is None:
        elems = sorted({v for p in rel for v in p},
                       key=_elem_key)
    if any(v not in elems for p in rel for v in p):
        return None
    return elems, rel, None


def _check_properties(elems, rel):
    """Exhaustive mechanical check.  Returns a dict:
    prop -> (verdict bool, witness or None)."""
    out = {}
    missing = [a for a in elems if (a, a) not in rel]
    out["reflexive"] = (not missing, missing[0] if missing
                        else None)
    bad_sym = None
    for p in sorted(rel, key=lambda p: (_elem_key(p[0]),
                                        _elem_key(p[1]))):
        if (p[1], p[0]) not in rel:
            bad_sym = p
            break
    out["symmetric"] = (bad_sym is None, bad_sym)
    bad_tr = None
    rel_sorted = sorted(rel, key=lambda p: (_elem_key(p[0]),
                                            _elem_key(p[1])))
    for (a, b) in rel_sorted:
        for (b2, c) in rel_sorted:
            if b2 == b and (a, c) not in rel:
                bad_tr = (a, b, c)
                break
        if bad_tr is not None:
            break
    out["transitive"] = (bad_tr is None, bad_tr)
    return out


def _relation_result(q, hi):
    ql = q.lower()
    if "relation" not in ql and not re.search(r"\bR\s*=", q):
        return None
    asked = [p for p in _PROP_WORDS if p in ql]
    if not asked:
        return None
    ext = _extract_relation(q)
    if ext is None:
        return None
    elems, rel, builder = ext
    checks = _check_properties(elems, rel)
    is_eq = all(checks[p][0] for p in
                ("reflexive", "symmetric", "transitive"))
    steps = []
    if builder is not None:
        steps.append(
            f"On A = {_show_set(elems)}, the condition "
            f"\"{builder}\" gives R = {_show_roster(rel)}.")
    else:
        steps.append(f"A = {_show_set(elems)}, "
                     f"R = {_show_roster(rel)}.")
    show = [p for p in ("reflexive", "symmetric",
                        "transitive") if p in asked]
    if "equivalence" in asked or not show:
        show = ["reflexive", "symmetric", "transitive"]
    for p in show:
        ok, wit = checks[p]
        if p == "reflexive":
            if ok:
                steps.append(
                    "Reflexive: YES — every (a, a) is in R: "
                    + ", ".join(_show_pair((a, a))
                                for a in elems) + ".")
            else:
                steps.append(
                    f"Reflexive: NO — ({wit}, {wit}) is not "
                    f"in R, though {wit} is in A.")
        elif p == "symmetric":
            if ok:
                steps.append(
                    "Symmetric: YES — whenever (a, b) is in "
                    "R, (b, a) is also in R.")
            else:
                steps.append(
                    f"Symmetric: NO — {_show_pair(wit)} is "
                    f"in R but {_show_pair((wit[1], wit[0]))} "
                    f"is not in R.")
        else:
            if ok:
                steps.append(
                    "Transitive: YES — whenever (a, b) and "
                    "(b, c) are in R, (a, c) is also in R.")
            else:
                a, b, c = wit
                steps.append(
                    f"Transitive: NO — {_show_pair((a, b))} "
                    f"and {_show_pair((b, c))} are in R but "
                    f"{_show_pair((a, c))} is not in R.")
    if "equivalence" in asked:
        if is_eq:
            steps.append(
                "R is reflexive, symmetric and transitive, "
                "so R IS an equivalence relation.")
        else:
            lacks = [p for p in ("reflexive", "symmetric",
                                 "transitive")
                     if not checks[p][0]]
            steps.append(
                "R is not " + " and not ".join(lacks) +
                ", so R is NOT an equivalence relation.")
    # Summary answer, computed from the verdicts.
    words = []
    for p in ("reflexive", "symmetric", "transitive"):
        if p in show or "equivalence" in asked:
            words.append((p, checks[p][0]))
    if "equivalence" in asked:
        detail = ", ".join(
            p if ok else f"not {p}" for p, ok in words)
        answer = (f"R is an equivalence relation. ({detail})"
                  if is_eq else
                  f"R is not an equivalence relation. "
                  f"({detail})")
    else:
        pos = [p for p, ok in words if ok]
        neg = [p for p, ok in words if not ok]
        if pos and not neg:
            answer = "R is " + " and ".join(pos) + "."
        elif neg and not pos:
            answer = ("R is not " + neg[0] + ".") \
                if len(neg) == 1 else \
                ("R is neither " + " nor ".join(neg) + ".")
        elif len(neg) == 1:
            answer = ("R is " + " and ".join(pos) +
                      " but not " + neg[0] + ".")
        else:
            answer = ("R is " + " and ".join(pos) +
                      " but neither " + " nor ".join(neg) + ".")
    return _result("relation_properties", answer, steps)


# ===========================================================================
# (b) One-one / onto classification
# ===========================================================================

# Domain / codomain descriptors:
#   ("R",) all reals          ("Q",) rationals
#   ("Z",) integers           ("N",) naturals {1, 2, ...}
#   ("NZR",) R - {0}          ("POS",) (0, inf)
#   ("NONNEG",) [0, inf)      ("MINUS", k) R - {k}

def _parse_set_token(tok):
    t = re.sub(r"\s+", "", tok).lower()
    t = t.replace("−", "-")
    if t in ("r", "ℝ".lower(), "real", "reals"):
        return ("R",)
    if t == "n":
        return ("N",)
    if t == "z":
        return ("Z",)
    if t == "q":
        return ("Q",)
    if t in ("r-{0}", "r\\{0}", "r*", "r-{0}"):
        return ("NZR",)
    m = re.fullmatch(r"r-\{(-?\d+(?:/\d+)?)\}", t)
    if m:
        k = Fraction(m.group(1))
        return ("NZR",) if k == 0 else ("MINUS", k)
    if t in ("[0,inf)", "[0,inf]", "[0,∞)"):
        return ("NONNEG",)
    if t in ("(0,inf)", "(0,inf]", "(0,∞)"):
        return ("POS",)
    return None


def _set_name(desc):
    return {("R",): "R", ("Q",): "Q", ("Z",): "Z",
            ("N",): "N", ("NZR",): "R - {0}",
            ("POS",): "(0, inf)", ("NONNEG",): "[0, inf)"}.get(
                desc, f"R - {{{_fmt_frac(desc[1])}}}"
                if desc[0] == "MINUS" else str(desc))


def _in_set(v, desc):
    """Is the Fraction v an element of the described set?"""
    k = desc[0]
    if k == "R" or k == "Q":
        return True
    if k == "Z":
        return v.denominator == 1
    if k == "N":
        return v.denominator == 1 and v >= 1
    if k == "NZR":
        return v != 0
    if k == "POS":
        return v > 0
    if k == "NONNEG":
        return v >= 0
    if k == "MINUS":
        return v != desc[1]
    return False


# Range descriptors:
#   ("all",) ("minus", y0) ("ray_up", lo, closed)
#   ("ray_down", hi, closed) ("q",) exactly Q
#   ("qsub",) proper subset of Q ("q_nonneg",) nonneg rationals
#   ("zall",) all integers ("zfrom", lo) integers >= lo
#   ("nset",) exactly N ("nonneg_ints",) {0, 1, 2, ...}
#   ("sparse",) / ("finite", frozenset) — cover no codomain

def _covers(rd, cod):
    """True when range descriptor rd contains codomain cod
    entirely (so the function is onto cod)."""
    rk = rd[0]
    ck = cod[0]
    if rk == "all":
        return True
    if rk == "minus":
        y0 = rd[1]
        if ck == "R":
            return False
        if ck == "NZR":
            return y0 == 0
        if ck == "MINUS":
            return y0 == cod[1]
        if ck == "POS":
            return y0 <= 0
        if ck == "NONNEG":
            return y0 < 0
        if ck == "Q":
            return False  # y0 is rational, hence missed
        if ck == "Z":
            return y0.denominator != 1
        if ck == "N":
            return not (y0.denominator == 1 and y0 >= 1)
        return False
    if rk == "ray_up":
        lo, closed = rd[1], rd[2]
        if ck == "POS":
            return lo < 0 or lo == 0
        if ck == "NONNEG":
            return lo < 0 or (lo == 0 and closed)
        if ck == "N":
            return lo < 1 or (lo == 1 and closed)
        return False
    if rk == "ray_down":
        return False
    if rk == "q":
        return ck in ("Q", "Z", "N")
    if rk == "q_nonneg":
        return ck == "N"
    if rk == "zall":
        return ck in ("Z", "N")
    if rk == "zfrom":
        return ck == "N" and rd[1] <= 1
    if rk == "nset":
        return ck == "N"
    if rk == "nonneg_ints":
        return ck == "N"
    return False  # qsub / sparse / finite


def _in_range(v, rd):
    rk = rd[0]
    if rk == "all":
        return True
    if rk == "minus":
        return v != rd[1]
    if rk == "ray_up":
        return v > rd[1] or (rd[2] and v == rd[1])
    if rk == "ray_down":
        return v < rd[1] or (rd[2] and v == rd[1])
    if rk == "q":
        return True
    if rk == "zall":
        return v.denominator == 1
    if rk == "zfrom":
        return v.denominator == 1 and v >= rd[1]
    if rk == "nset":
        return v.denominator == 1 and v >= 1
    if rk == "nonneg_ints":
        return v.denominator == 1 and v >= 0
    if rk == "q_nonneg":
        return v >= 0
    return False


_MISS_CANDIDATES = [Fraction(0), Fraction(1), Fraction(-1),
                    Fraction(2), Fraction(-2), Fraction(1, 2),
                    Fraction(-1, 2), Fraction(3), Fraction(-3),
                    Fraction(3, 2), Fraction(-3, 2), Fraction(4),
                    Fraction(-4), Fraction(5), Fraction(-5)]


def _find_missed(rd, cod):
    """A concrete Fraction in cod but not in range rd, or
    None.  Only called when _covers(rd, cod) is False and rd
    is membership-decidable."""
    cands = list(_MISS_CANDIDATES)
    if rd[0] in ("ray_up", "ray_down"):
        lo = rd[1]
        cands += [lo - 1, lo + 1, lo - 2, lo + 2,
                  lo / 2 if lo > 0 else lo - 1]
    if rd[0] == "minus":
        cands.insert(0, rd[1])
    for v in cands:
        if _in_set(v, cod) and not _in_range(v, rd):
            return v
    return None


def _perfect_power(fr, n):
    """The rational n-th root of Fraction fr, or None."""
    if fr < 0:
        return None
    def root_int(a):
        if a < 0:
            return None
        lo, hi = 0, max(1, int(round(a ** (1.0 / n))) + 2)
        while lo <= hi:
            mid = (lo + hi) // 2
            p = mid ** n
            if p == a:
                return mid
            if p < a:
                lo = mid + 1
            else:
                hi = mid - 1
        return None
    rn = root_int(fr.numerator)
    rd_ = root_int(fr.denominator)
    if rn is None or rd_ is None:
        return None
    return Fraction(rn, rd_)


def _monomial_missed(c, n, dom, cod):
    """For a monomial c*x^n on a discrete / rational domain:
    a codomain value with no preimage in dom, verified by
    the exact rational-root test."""
    for cand in (Fraction(2), Fraction(3), Fraction(5),
                 Fraction(6), Fraction(7), Fraction(10),
                 Fraction(-2), Fraction(-3), Fraction(4),
                 Fraction(8), Fraction(9)):
        if not _in_set(cand, cod):
            continue
        t = cand / c
        roots = []
        if t >= 0:
            r = _perfect_power(t, n)
            if r is not None:
                roots.append(r)
                if n % 2 == 0:
                    roots.append(-r)
        elif n % 2 == 1:
            r = _perfect_power(-t, n)
            if r is not None:
                roots.append(-r)
        if not any(_in_set(r, dom) for r in roots):
            return cand
    return None


def _eval_form(form, x):
    """Evaluate the catalogue function at Fraction x
    (sympy-exact); None when undefined there."""
    kind = form[0]
    xs = sp.nsimplify(x, rational=True)
    try:
        if kind == "monomial":
            v = sp.nsimplify(form[1], rational=True) * xs ** form[2]
        elif kind == "linear":
            v = sp.nsimplify(form[1], rational=True) * xs + \
                sp.nsimplify(form[2], rational=True)
        elif kind == "modulus":
            v = sp.Abs(xs)
        elif kind == "gif":
            v = sp.floor(xs)
        elif kind == "signum":
            v = sp.sign(xs)
        elif kind == "recip":
            if xs == 0:
                return None
            v = 1 / xs
        elif kind == "const":
            v = sp.nsimplify(form[1], rational=True)
        elif kind == "mobius":
            a, b, cc, d = (sp.nsimplify(t, rational=True)
                           for t in form[1:])
            if cc * xs + d == 0:
                return None
            v = (a * xs + b) / (cc * xs + d)
        else:
            return None
        v = sp.nsimplify(sp.simplify(v), rational=True)
        return Fraction(v.p, v.q)
    except Exception:
        return None


def _witness_pair(form, dom, w1, w2):
    """Confirm w1 != w2, both in dom, and f(w1) == f(w2).
    Returns the common value or None — a one-one failure is
    served ONLY with a verified witness."""
    if w1 == w2:
        return None
    if not (_in_set(w1, dom) and _in_set(w2, dom)):
        return None
    v1 = _eval_form(form, w1)
    v2 = _eval_form(form, w2)
    if v1 is None or v2 is None or v1 != v2:
        return None
    return v1


_ONE_SIDED = (("POS",), ("NONNEG",), ("N",))


def _classify(form, dom, cod):
    """-> (one_one, onto, one_reason, onto_reason) or None
    when this form / domain / codomain combination is
    outside the mechanically decidable catalogue."""
    if dom[0] == "MINUS" and form[0] != "mobius":
        return None
    # A MINUS codomain (R - {k}) stays decidable for every
    # form: _covers / _find_missed handle it set-wise.
    kind = form[0]
    one = None
    rd = None          # range descriptor
    one_wit = None     # (w1, w2) candidate for a NO verdict
    special_onto = None

    if kind == "monomial":
        _, c, n = form
        if n == 1:
            return _classify(("linear", c, Fraction(0)),
                             dom, cod)
        even = (n % 2 == 0)
        if even:
            one = dom in _ONE_SIDED
            if not one:
                one_wit = (Fraction(-1), Fraction(1))
            if dom in (("R",), ("NONNEG",)):
                rd = ("ray_up", Fraction(0), True) if c > 0 \
                    else ("ray_down", Fraction(0), True)
            elif dom in (("POS",), ("NZR",)):
                rd = ("ray_up", Fraction(0), False) if c > 0 \
                    else ("ray_down", Fraction(0), False)
            elif dom == ("Q",):
                rd = ("qsub",)
            else:  # Z, N
                rd = ("sparse",)
        else:
            one = True
            if dom == ("R",):
                rd = ("all",)
            elif dom == ("POS",):
                rd = ("ray_up", Fraction(0), False) if c > 0 \
                    else ("ray_down", Fraction(0), False)
            elif dom == ("NONNEG",):
                rd = ("ray_up", Fraction(0), True) if c > 0 \
                    else ("ray_down", Fraction(0), True)
            elif dom == ("NZR",):
                rd = ("minus", Fraction(0))
            elif dom == ("Q",):
                rd = ("qsub",)
            else:
                rd = ("sparse",)
    elif kind == "linear":
        _, a, b = form
        one = True
        if dom == ("R",):
            rd = ("all",)
        elif dom == ("Q",):
            rd = ("q",)
        elif dom == ("POS",):
            rd = ("ray_up", b, False) if a > 0 else \
                ("ray_down", b, False)
        elif dom == ("NONNEG",):
            rd = ("ray_up", b, True) if a > 0 else \
                ("ray_down", b, True)
        elif dom == ("NZR",):
            rd = ("minus", b)
        elif dom in (("Z",), ("N",)):
            special_onto = _linear_discrete_onto(a, b, dom, cod)
            if special_onto is None:
                return None
    elif kind == "modulus":
        one = dom in _ONE_SIDED
        if not one:
            one_wit = (Fraction(-1), Fraction(1))
        if dom in (("R",), ("NONNEG",)):
            rd = ("ray_up", Fraction(0), True)
        elif dom in (("POS",), ("NZR",)):
            rd = ("ray_up", Fraction(0), False)
        elif dom == ("Q",):
            rd = ("q_nonneg",)
        elif dom == ("Z",):
            rd = ("nonneg_ints",)
        elif dom == ("N",):
            rd = ("nset",)
    elif kind == "gif":
        one = dom in (("Z",), ("N",))
        if not one:
            one_wit = (Fraction(1, 2), Fraction(3, 4))
        if dom in (("R",), ("Q",), ("NZR",), ("Z",)):
            rd = ("zall",)
        elif dom == ("N",):
            rd = ("nset",)
        elif dom in (("POS",), ("NONNEG",)):
            rd = ("zfrom", 0)
    elif kind == "signum":
        one = False
        one_wit = (Fraction(1), Fraction(2))
        if dom in (("POS",), ("N",)):
            rd = ("finite", frozenset({Fraction(1)}))
        elif dom == ("NONNEG",):
            rd = ("finite", frozenset({Fraction(0),
                                       Fraction(1)}))
        elif dom == ("NZR",):
            rd = ("finite", frozenset({Fraction(-1),
                                       Fraction(1)}))
        else:
            rd = ("finite", frozenset({Fraction(-1),
                                       Fraction(0),
                                       Fraction(1)}))
    elif kind == "recip":
        if dom not in (("NZR",), ("POS",), ("N",)):
            return None  # 0 in the domain: f is not defined
        one = True
        if dom == ("NZR",):
            rd = ("minus", Fraction(0))
        elif dom == ("POS",):
            rd = ("ray_up", Fraction(0), False)
        else:
            rd = ("sparse",)
    elif kind == "const":
        one = False
        one_wit = (Fraction(1), Fraction(2))
        rd = ("finite", frozenset({form[1]}))
    elif kind == "mobius":
        _, a, b, cc, d = form
        if a * d - b * cc == 0:
            return None  # constant where defined; decline
        pole = -d / cc
        if dom == ("NZR",):
            if pole != 0:
                return None
        elif dom[0] == "MINUS":
            if dom[1] != pole:
                return None
        else:
            return None  # pole inside the stated domain
        one = True
        rd = ("minus", a / cc)
    else:
        return None

    # One-one verdict: verify a NO with its witness pair.
    one_reason = ""
    if one is False:
        if one_wit is None:
            return None
        val = _witness_pair(form, dom, *one_wit)
        if val is None:
            return None
        one_reason = (f"f({_fmt_frac(one_wit[0])}) = "
                      f"f({_fmt_frac(one_wit[1])}) = "
                      f"{_fmt_frac(val)}, but "
                      f"{_fmt_frac(one_wit[0])} != "
                      f"{_fmt_frac(one_wit[1])}")
    # Onto verdict.
    if special_onto is not None:
        onto = special_onto
    else:
        onto = _covers(rd, cod)
    onto_reason = ""
    if not onto:
        if special_onto is not None:
            missed = _linear_discrete_missed(form, dom, cod)
            if missed is None:
                return None
            onto_reason = (f"{_fmt_frac(missed)} has no "
                           f"preimage in {_set_name(dom)}")
        elif rd[0] in ("qsub", "sparse") and kind == "monomial":
            missed = _monomial_missed(form[1], form[2], dom,
                                      cod)
            if missed is None:
                return None
            onto_reason = (f"{_fmt_frac(missed)} has no "
                           f"preimage in {_set_name(dom)}")
        elif rd[0] == "q":
            # Range is exactly Q; the codomain (an interval
            # set) contains irrationals, e.g. sqrt(2).
            if cod[0] not in ("R", "POS", "NONNEG", "NZR"):
                return None
            onto_reason = ("sqrt(2) is in the codomain but "
                           "is not rational, so it has no "
                           "preimage")
        elif rd[0] == "q_nonneg":
            # Non-negative rationals: a negative codomain
            # value, or an irrational, is never attained.
            if cod[0] in ("Q", "Z", "R", "NZR"):
                onto_reason = ("-1 is in the codomain but "
                               "|x| is never negative")
            elif cod[0] in ("POS", "NONNEG"):
                onto_reason = ("sqrt(2) is in the codomain "
                               "but has no rational preimage")
            else:
                return None
        elif rd[0] == "finite":
            missed = None
            for v in _MISS_CANDIDATES:
                if _in_set(v, cod) and v not in rd[1]:
                    missed = v
                    break
            if missed is None:
                return None
            if kind == "signum":
                onto_reason = ("the range is only "
                               + ", ".join(_fmt_frac(v) for v in
                                           sorted(rd[1]))
                               + f", so {_fmt_frac(missed)} "
                                 "is never attained")
            else:
                onto_reason = (f"the only value f takes is "
                               f"{_fmt_frac(form[1])}, so "
                               f"{_fmt_frac(missed)} is never "
                               f"attained")
        else:
            missed = _find_missed(rd, cod)
            if missed is None:
                return None
            onto_reason = (f"{_fmt_frac(missed)} is in the "
                           f"codomain but has no preimage")
    return one, onto, one_reason, onto_reason


def _linear_discrete_onto(a, b, dom, cod):
    """Onto verdict for f(x) = a x + b (a != 0, rational) on
    a discrete domain Z or N.  Mechanical: the preimage of
    y is (y - b)/a; onto iff that lands in dom for EVERY y
    in cod, which for these sets reduces to the step /
    offset conditions checked here."""
    if dom == ("Z",):
        if cod[0] in ("Q", "R", "POS", "NONNEG", "NZR",
                      "MINUS"):
            return False  # discrete range, dense/interval cod
        # cod Z or N: onto iff a = +-1/k and k*b is integral
        p, q = a.numerator, a.denominator
        if abs(p) != 1:
            return False
        return (q * b).denominator == 1
    # dom N
    if cod != ("N",):
        return False  # range is discrete and one-sided
    if a <= 0:
        return False
    p, q = a.numerator, a.denominator
    if p != 1:
        return False
    if (q * b).denominator != 1:
        return False
    return q * (1 - b) >= 1


def _linear_discrete_missed(form, dom, cod):
    """A codomain value whose linear preimage is outside
    the discrete domain, found by direct search."""
    _, a, b = form
    cands = list(_MISS_CANDIDATES)
    cands += [b + a / 2, b + 3 * a / 2, b + a, b - a / 2,
              b + 5 * a / 2]
    for v in cands:
        if not _in_set(v, cod):
            continue
        x = (v - b) / a
        if not _in_set(x, dom):
            return v
    for k in range(1, 60):
        for v in (Fraction(k), Fraction(-k)):
            if not _in_set(v, cod):
                continue
            x = (v - b) / a
            if not _in_set(x, dom):
                return v
    return None


def _parse_function_form(expr_text):
    """The recognised catalogue -> a form tuple, or None.
    Anything outside the catalogue declines: no guessed
    verdicts."""
    t = re.sub(r"\s+", "", expr_text).lower()
    t = t.replace("**", "^")
    if not t:
        return None
    if "signum" in t:
        return ("signum",)
    if t in ("[x]", "⌊x⌋", "floor(x)") or \
            "greatestinteger" in t:
        return ("gif",)
    if t in ("|x|", "abs(x)") or "modulus" in t:
        return ("modulus",)
    if t in ("1/x",):
        return ("recip",)
    # Numeric constant.
    try:
        return ("const", Fraction(t))
    except Exception:
        pass
    # SymPy-parseable forms in x with rational coefficients.
    try:
        expr = parse_expression(expr_text.replace("^", "**"))
    except Exception:
        return None
    if isinstance(expr, tuple) or expr is None:
        return None
    x = sp.Symbol("x")
    if not expr.free_symbols <= {x}:
        return None
    try:
        numer, denom = sp.fraction(sp.together(expr))
        if denom != 1:
            pn = sp.Poly(numer, x)
            pd = sp.Poly(denom, x)
            if pn is None or pd is None:
                return None
            if pn.degree() <= 1 and pd.degree() == 1:
                b = pn.nth(0)
                a = pn.nth(1) if pn.degree() == 1 else sp.Integer(0)
                d = pd.nth(0)
                cc = pd.nth(1)
                vals = [Fraction(sp.nsimplify(v, rational=True).p,
                                 sp.nsimplify(v, rational=True).q)
                        for v in (a, b, cc, d)]
                return ("mobius", *vals)
            return None
        poly = sp.Poly(expr, x)
    except Exception:
        return None
    if poly is None:
        return None
    coeffs = {}
    for (deg,), coeff in poly.as_dict().items():
        try:
            fv = sp.nsimplify(coeff, rational=True)
            coeffs[deg] = Fraction(fv.p, fv.q)
        except Exception:
            return None
    deg = poly.degree()
    if deg == 0:
        return ("const", coeffs.get(0, Fraction(0)))
    if len(coeffs) == 1:
        (n, c), = coeffs.items()
        if c == 0:
            return None
        return ("monomial", c, n)
    if deg == 1:
        return ("linear", coeffs.get(1, Fraction(0)),
                coeffs.get(0, Fraction(0)))
    return None


def _lin_term(a):
    if a == 1:
        return "x"
    if a == -1:
        return "-x"
    return f"{_fmt_frac(a)}x"


def _form_display(form):
    kind = form[0]
    if kind == "monomial":
        c, n = form[1], form[2]
        cs = "" if c == 1 else ("-" if c == -1
                                else _fmt_frac(c))
        return f"{cs}x^{n}"
    if kind == "linear":
        a, b = form[1], form[2]
        s = _lin_term(a)
        if b > 0:
            s += f" + {_fmt_frac(b)}"
        elif b < 0:
            s += f" - {_fmt_frac(-b)}"
        return s
    if kind == "modulus":
        return "|x|"
    if kind == "gif":
        return "[x]"
    if kind == "signum":
        return "signum(x)"
    if kind == "recip":
        return "1/x"
    if kind == "const":
        return _fmt_frac(form[1])
    if kind == "mobius":
        a, b, cc, d = form[1:]
        num = _lin_term(a) + (
            f" + {_fmt_frac(b)}" if b > 0 else
            f" - {_fmt_frac(-b)}" if b < 0 else "")
        den = _lin_term(cc) + (
            f" + {_fmt_frac(d)}" if d > 0 else
            f" - {_fmt_frac(-d)}" if d < 0 else "")
        return f"({num})/({den})"
    return "f(x)"


_CLASS_WORDS = ("one-one", "one one", "injective", "onto",
                "surjective", "bijective", "many-one",
                "many one")


_SET_TOKEN_RE = (r"(?:\[0,\s*inf\)|\(0,\s*inf\)|"
                 r"R\s*-\s*\{[^}]*\}|R\*|[RNZQ]\b)")


def _extract_classification(q):
    """-> (form, dom, cod) or None."""
    m = re.search(r"f\s*:\s*(" + _SET_TOKEN_RE +
                  r")\s*->\s*(" + _SET_TOKEN_RE + r")",
                  q, re.I)
    if not m:
        return None
    dom = _parse_set_token(m.group(1))
    cod = _parse_set_token(m.group(2))
    if dom is None or cod is None:
        return None
    mf = re.search(r"f\s*\(\s*x\s*\)\s*=\s*(.+)", q, re.I)
    if not mf:
        # "f is the signum function" / "the greatest integer
        # function" dresses without an f(x) = ... formula.
        ql = q.lower()
        if "signum" in ql:
            return ("signum",), dom, cod
        if "greatest integer" in ql:
            return ("gif",), dom, cod
        if "modulus function" in ql:
            return ("modulus",), dom, cod
        return None
    expr_text = mf.group(1)
    expr_text = re.split(r"\?|\.\s+(?=[A-Z])|;\s*|,\s*(?:is|"
                         r"check|show|choose)\b|\s+is\s+f\b|"
                         r"\s+check\b|\s+choose\b|"
                         r"\s+(?:is|check|show|one-one|"
                         r"one\s+one|onto|injective|"
                         r"surjective|bijective)\b",
                         expr_text)[0].strip().rstrip(".")
    form = _parse_function_form(expr_text)
    if form is None:
        return None
    return form, dom, cod


def _option_class(text):
    t = text.lower()
    if "neither" in t:
        return (False, False)
    if "bijective" in t:
        return (True, True)
    has_one = "one-one" in t or "one one" in t
    has_onto = "onto" in t
    if has_one and "not onto" in t:
        return (True, False)
    if ("many-one" in t or "many one" in t or
            "not one-one" in t or "not one one" in t) and \
            has_onto:
        return (False, True)
    if has_one and has_onto:
        return (True, True)
    if has_one:
        return (True, False)
    if has_onto:
        return (False, True)
    return None


def _classification_result(q, hi):
    ql = q.lower()
    if not any(w in ql for w in _CLASS_WORDS):
        return None
    ext = _extract_classification(q)
    if ext is None:
        return None
    form, dom, cod = ext
    out = _classify(form, dom, cod)
    if out is None:
        return None
    one, onto, one_reason, onto_reason = out
    fshow = _form_display(form)
    steps = [f"f : {_set_name(dom)} -> {_set_name(cod)}, "
             f"f(x) = {fshow}."]
    if one:
        steps.append("One-one: YES — distinct inputs always "
                     "give distinct outputs for this form.")
    else:
        steps.append(f"One-one: NO — {one_reason}, so two "
                     f"different inputs give the same output.")
    if onto:
        steps.append(f"Onto: YES — every value in "
                     f"{_set_name(cod)} is attained.")
    else:
        steps.append(f"Onto: NO — {onto_reason}.")
    verdict = {(True, True): "one-one and onto (bijective)",
               (True, False): "one-one but not onto",
               (False, True): "not one-one but onto "
                              "(many-one onto)",
               (False, False): "neither one-one nor onto"}[
                   (one, onto)]
    answer = f"f is {verdict}."
    # MCQ dress: map the computed verdict to the option.
    opts = re.findall(r"\(([A-D])\)\s*([^()]+?)(?=\s*\([A-D]\)"
                      r"|\s*$)", q)
    if len(opts) >= 3:
        matches = [letter for letter, text in opts
                   if _option_class(text) == (one, onto)]
        if len(matches) != 1:
            return None  # no unique matching option: decline
        letter = matches[0]
        text = dict(opts)[letter].strip()
        steps.append(f"This matches option ({letter}): "
                     f"{text}.")
        answer = f"({letter}) {text} — f is {verdict}."
    return _result("function_classification", answer, steps,
                   typ="functions")


# ===========================================================================
# (c) Counting forms
# ===========================================================================

def _bell(n):
    """Bell number B_n by the exact Stirling-number sum."""
    stir = [[0] * (n + 1) for _ in range(n + 1)]
    stir[0][0] = 1
    for i in range(1, n + 1):
        for k in range(1, i + 1):
            stir[i][k] = stir[i - 1][k - 1] + k * stir[i - 1][k]
    return sum(stir[n][k] for k in range(n + 1))


def _set_size_near(q, keywords):
    """Find a set size stated as 'set with n elements',
    'n-element set', or an explicit {..} set near the
    keywords."""
    m = re.search(r"(\d+)\s*-\s*element", q)
    if m:
        return int(m.group(1))
    m = re.search(r"set\s+(?:of|with|having)\s+(\d+)\s+"
                  r"elements", q)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+elements", q)
    if m:
        return int(m.group(1))
    return None


def _counting_result(q, hi):
    ql = q.lower()
    if "number of" not in ql and "how many" not in ql:
        return None
    # ---- relations on an n-set ----
    if "relation" in ql:
        n = _set_size_near(ql, "relation")
        elems = None
        if n is None:
            for sm in re.finditer(r"\{([^{}]*)\}", q):
                cand = _parse_elements(sm.group(1))
                if cand is not None:
                    elems = cand
                    n = len(cand)
                    break
        if "equivalence" in ql:
            if n is None or n > 12:
                return None
            base_elems = elems if elems is not None else \
                list(range(1, n + 1))
            pairs = re.findall(r"\(\s*(-?\d+|[a-zA-Z])\s*,\s*"
                               r"(-?\d+|[a-zA-Z])\s*\)", q)
            blocks = n
            forced = []
            if pairs:
                parent = {e: e for e in base_elems}

                def find(e):
                    while parent[e] != e:
                        parent[e] = parent[parent[e]]
                        e = parent[e]
                    return e

                for a, b in pairs:
                    ea = int(a) if re.fullmatch(r"-?\d+", a) \
                        else a
                    eb = int(b) if re.fullmatch(r"-?\d+", b) \
                        else b
                    if ea not in parent or eb not in parent:
                        return None
                    ra, rb = find(ea), find(eb)
                    if ra != rb:
                        parent[ra] = rb
                    forced.append((ea, eb))
                blocks = len({find(e) for e in base_elems})
            val = _bell(blocks)
            steps = [
                f"Equivalence relations on a {n}-element set "
                f"are exactly its partitions.",
            ]
            if forced:
                steps.append(
                    "The forced pairs "
                    + ", ".join(_show_pair(p) for p in forced)
                    + f" merge the set into {blocks} block(s); "
                      "equivalence relations containing them "
                      "are the partitions of these blocks.")
            steps.append(
                f"Number = Bell({blocks}) = {val}.")
            return _result("count_equivalence_relations",
                           str(val), steps)
        if n is None or n > 20:
            return None
        if "reflexive" in ql and "symmetric" in ql:
            return None  # not in the pinned catalogue
        if "reflexive" in ql:
            exp = n * (n - 1)
            val = 2 ** exp
            steps = [
                f"A reflexive relation must contain all {n} "
                f"diagonal pairs (a, a); each of the other "
                f"{n * n} - {n} = {exp} pairs is free.",
                f"Number = 2^{exp} = {val}."]
            return _result("count_reflexive_relations",
                           str(val), steps)
        if "symmetric" in ql:
            exp = n * (n + 1) // 2
            val = 2 ** exp
            steps = [
                f"A symmetric relation is decided by the "
                f"{n} diagonal pairs and the {n * (n - 1) // 2} "
                f"pair-choices above the diagonal: "
                f"{exp} free choices.",
                f"Number = 2^{exp} = {val}."]
            return _result("count_symmetric_relations",
                           str(val), steps)
        exp = n * n
        val = 2 ** exp
        steps = [
            f"A relation on a {n}-element set is any subset "
            f"of A x A, which has {n} x {n} = {exp} pairs.",
            f"Number = 2^{exp} = {val}."]
        return _result("count_relations", str(val), steps)
    # ---- functions from an n-set to an m-set ----
    if "function" in ql:
        sizes = None
        m = re.search(r"(\d+)\s*-\s*element.*?(\d+)\s*-\s*"
                      r"element", ql)
        if m:
            sizes = (int(m.group(1)), int(m.group(2)))
        if sizes is None:
            ms = re.findall(r"set\s+(?:of|with|having)\s+"
                            r"(\d+)\s+elements", ql)
            if len(ms) >= 2:
                sizes = (int(ms[0]), int(ms[1]))
        if sizes is None:
            sets = []
            for sm in re.finditer(r"\{([^{}]*)\}", q):
                cand = _parse_elements(sm.group(1))
                if cand is not None:
                    sets.append(cand)
            if len(sets) >= 2:
                sizes = (len(sets[0]), len(sets[1]))
        if sizes is None:
            return None
        n, mm = sizes
        if n > 12 or mm > 12:
            return None
        if "onto" in ql or "surjective" in ql:
            terms = []
            total = 0
            for k in range(mm + 1):
                term = (-1) ** k * comb(mm, k) * (mm - k) ** n
                total += term
                terms.append(str(term))
            shown = terms[0] + "".join(
                f" - {t[1:]}" if t.startswith("-") else
                f" + {t}" for t in terms[1:])
            steps = [
                f"Onto functions from a {n}-element set to a "
                f"{mm}-element set, by inclusion-exclusion: "
                f"sum over k of (-1)^k C({mm},k) "
                f"({mm}-k)^{n}.",
                f"= {shown} = {total}."]
            return _result("count_onto_functions", str(total),
                           steps, typ="functions")
        if "one-one" in ql or "one one" in ql or \
                "injective" in ql:
            if n > mm:
                val = 0
                steps = [f"A one-one function needs {n} "
                         f"distinct images but the codomain "
                         f"has only {mm} elements, so the "
                         f"number is 0."]
            else:
                val = 1
                for i in range(n):
                    val *= (mm - i)
                steps = [
                    f"The first element has {mm} choices of "
                    f"image, the next {mm - 1}, and so on for "
                    f"{n} elements.",
                    f"Number = P({mm}, {n}) = {val}."]
            return _result("count_oneone_functions", str(val),
                           steps, typ="functions")
        val = mm ** n
        steps = [
            f"Each of the {n} elements of the domain has "
            f"{mm} choices of image, independently.",
            f"Number = {mm}^{n} = {val}."]
        return _result("count_functions", str(val), steps,
                       typ="functions")
    return None


# ===========================================================================
# Dispatcher
# ===========================================================================

def solve_relations191(question):
    """Wave 191 entry point: Relations & Functions
    proof / classification / counting schemas.  Returns a
    solver result dict or None.  Called by the router only
    when the primary solve failed, so a None here leaves
    behaviour byte-identical."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip():
        return None
    hi = _hindi(question)
    for schema in (_counting_result, _relation_result,
                   _classification_result):
        try:
            out = schema(q, hi)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
