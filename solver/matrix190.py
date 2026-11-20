"""Wave 190: matrix family completion — the Class 12 forms
the form audit (item B.5 / rows 7-9) proved missing while
the core matrix operations already solved:

  (a) A system of linear equations stated AS EQUATIONS and
      asked BY MATRIX METHOD (or as an examine-the-
      consistency ask): parse the equation list into
      A.x = B, serve X = A^-1 B with matrix-method steps
      (determinant, inverse, product).  A singular A gets
      the correct rank verdict — no solution when
      rank(A) < rank([A|B]), infinitely many when the
      ranks agree below the number of unknowns — never a
      bogus numeric answer.
  (b) A'A = I / AA' = I find-the-unknowns in PLAIN dress
      (letter entries, prime notation, no bar form — the
      dress solver/linear_algebra.py's Wave 80 verifier
      does not reach): set the product equal to I entry by
      entry, solve, and verify every candidate solution
      against the full product before serving.
  (c) Verify / prove dresses with CONCRETE matrices —
      (AB)' = B'A', A + A' symmetric, A - A' skew-
      symmetric, AB - BA skew-symmetric for symmetric
      A, B.  Both sides are always COMPUTED and compared;
      a claim that fails for the given matrices is served
      as the computed verdict (sides shown, not equal),
      never as a template-asserted proof.
  (d) Hence-find-A^-1 chains: A given numerically and
      A^2 + pA + qI = O stated — the premise is checked
      exactly, A^-1 = -(A + pI)/q is derived from the
      equation, and A.A^-1 = I is verified numerically
      before serving; any failure declines.
  (e) Matrix word problems, templated on the NCERT
      narrative STRUCTURE (numbers vary): the trust-fund
      two-bond investment (total split at two rates to a
      target interest, solved as a matrix system) and the
      manufacturer selling products in two markets
      (revenue, and profit when cost prices are given,
      via matrix multiplication).  A narrative that does
      not match a template exactly declines.

House rules (Waves 169/175 style): this module fires only
when a strict schema settles the question COMPLETELY with
every value recomputed exactly (SymPy) and verified; any
doubt returns None so routing continues unchanged.  Wiring:
a failure-only gate at the end of
router._solve_question_uncached (after Wave 175), plus a
narrow hijack-repair block in the Wave 171 style for the
verify / hence dresses whose primary serve is a fragment
of the question (the bare product AB served for a
"(AB)' = B'A'" verify, 5A served for a hence-inverse ask).
"""
import re

import sympy as sp
from sympy import Matrix

from .expression_parser import fmt, fmt_num, parse_expression
from .matrixeq175 import _cell_expr, _check_cell

_VARS = ("x", "y", "z")


def _prep(text):
    s = str(text)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("′", "'").replace("’", "'")
    s = s.replace("²", "^2").replace("³", "^3")
    s = s.replace("⁻¹", "^-1")
    s = s.replace("×", "*").replace("₹", "Rs ")
    return s


def _mstr(M):
    return str(M.tolist()).replace("'", "")


def _grid(block_inner):
    """'1, 2],[3, 4' -> Matrix of exact cells, or None.
    Cells may be symbolic (branch (b)); callers check."""
    rows = []
    for row_text in re.split(r"\]\s*,\s*\[", block_inner):
        cells = []
        for c in row_text.split(","):
            c = c.strip()
            if not c:
                return None
            try:
                e = _cell_expr(c)
            except Exception:
                return None
            if not e.free_symbols:
                e = sp.nsimplify(e, rational=True)
            cells.append(e)
        rows.append(cells)
    if not rows or any(len(r) != len(rows[0]) for r in rows):
        return None
    return Matrix(rows)


def _named_matrix(q, name):
    m = re.search(rf"\b{name}\s*=\s*\[\[(.+?)\]\]", q, re.S)
    if not m:
        return None
    return _grid(m.group(1))


def _first_matrix(q):
    m = re.search(r"\[\[(.+?)\]\]", q, re.S)
    if not m:
        return None
    return _grid(m.group(1))


def _numeric(M):
    return M is not None and not any(
        e.free_symbols for e in M)


# ---------------------------------------------------------------------------
# (a) System of equations by matrix method / consistency
# ---------------------------------------------------------------------------

_EQ_LHS_OK = re.compile(r"^[0-9\.\+\-\*\/\(\)xyz\s]+$")


def _parse_system(q):
    """Extract a 2x2 or 3x3 linear system stated as equations
    from the question text.  Returns (unknowns, A, B) with
    exact rational entries, or None."""
    frags = []
    for chunk in re.split(r"[;\n]", q):
        for piece in chunk.split(","):
            frags.append(piece)
    # 'and'-separated equations survive the comma split as
    # one fragment only when no commas are present; split
    # those too, but only around an '=' boundary.
    widened = []
    for f in frags:
        if f.count("=") > 1:
            parts = re.split(r"\band\b", f)
            if all("=" in p for p in parts):
                widened.extend(parts)
                continue
        widened.append(f)
    eqs = []
    intended = 0
    for f in widened:
        if "=" not in f:
            continue
        f = f.rsplit(":", 1)[-1].strip()
        if "=" not in f:
            continue
        # Wave 207: count every fragment that carries an
        # x/y/z equation, extracted or not.  The audit's
        # consistency item glued its first equation to the
        # preamble ("...linear equations x - y + z = -9"),
        # the fragment failed the strict LHS pattern, and
        # the schema went on to solve the remaining 3x3
        # subsystem and serve values the dropped equation
        # contradicts — verified only against the subset.
        # A strict schema that cannot see the whole system
        # declines; it never solves part of it.
        if re.search(r"[xyz]", f.split("=", 1)[0]):
            intended += 1
        lhs_t, rhs_t = f.split("=", 1)
        lhs_t, rhs_t = lhs_t.strip(), \
            rhs_t.strip().rstrip(".?")
        if not lhs_t or not rhs_t:
            continue
        if not _EQ_LHS_OK.match(lhs_t):
            continue
        if not re.search(r"[xyz]", lhs_t):
            continue
        if not re.fullmatch(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?",
                            rhs_t):
            continue
        try:
            lhs = parse_expression(lhs_t)
            rhs = sp.nsimplify(rhs_t.replace(" ", ""),
                               rational=True)
        except Exception:
            continue
        if isinstance(lhs, tuple) or lhs.free_symbols - {
                sp.Symbol(v) for v in _VARS}:
            continue
        eqs.append((lhs, rhs))
    if intended != len(eqs):
        return None
    if len(eqs) not in (2, 3):
        return None
    present = []
    for lhs, _ in eqs:
        for v in _VARS:
            if sp.Symbol(v) in lhs.free_symbols \
                    and v not in present:
                present.append(v)
    unknowns = [v for v in _VARS if v in present]
    if len(unknowns) != len(eqs):
        return None
    syms = [sp.Symbol(v) for v in unknowns]
    rows, bvals = [], []
    for lhs, rhs in eqs:
        try:
            poly = sp.Poly(sp.expand(lhs), *syms)
        except Exception:
            return None
        if poly is None or poly.total_degree() > 1:
            return None
        row = []
        for s in syms:
            c = poly.coeff_monomial(s)
            if c.free_symbols or not c.is_rational:
                return None
            row.append(sp.nsimplify(c, rational=True))
        if poly.coeff_monomial(1) != 0:
            return None
        rows.append(row)
        bvals.append(rhs)
    return unknowns, Matrix(rows), Matrix(bvals)


def _solve_matrix_method(question, q, ql):
    if "matrix method" not in ql and "by matrix" not in ql \
            and "using matrices" not in ql \
            and "consisten" not in ql:
        return None
    if "system" not in ql and "equations" not in ql \
            and "consisten" not in ql:
        return None
    parsed = _parse_system(q)
    if parsed is None:
        return None
    unknowns, A, B = parsed
    n = len(unknowns)
    xstr = "[" + ", ".join(unknowns) + "]^T"
    steps = [
        "Write the system as A X = B with "
        f"A = {_mstr(A)}, X = {xstr}, B = {_mstr(B.T)}.",
    ]
    det = A.det()
    steps.append(f"|A| = {fmt_num(det)}")
    rank_a = A.rank()
    rank_aug = A.row_join(B).rank()
    if det == 0:
        # Singular: the rank comparison decides the verdict.
        steps.append(
            f"rank(A) = {rank_a}, rank([A|B]) = {rank_aug}.")
        if rank_a != rank_aug:
            steps.append(
                "rank(A) is not equal to rank([A|B]), so the "
                "equations contradict each other.")
            return {"type": "linear_algebra",
                    "op": "w190_consistency",
                    "answer": "The system is inconsistent — "
                              "no solution",
                    "steps": steps}
        # Consistent but underdetermined: describe the
        # solution set with a free parameter, verified by
        # substitution into every equation.
        syms = [sp.Symbol(v) for v in unknowns]
        try:
            solset = sp.linsolve((A, B), *syms)
            sol = list(solset)[0]
        except Exception:
            return None
        for lhs_row, rhs in zip(A.tolist(), B.tolist()):
            val = sum(c * s for c, s in zip(lhs_row, sol))
            if sp.simplify(val - rhs[0]) != 0:
                return None
        free = [u for u, s in zip(unknowns, sol)
                if sp.Symbol(u) in s.free_symbols]
        parts = ", ".join(
            f"{u} = {fmt(s)}" for u, s in zip(unknowns, sol)
            if not (s == sp.Symbol(u)))
        steps.append(
            "rank(A) = rank([A|B]) is less than the number "
            "of unknowns, so there are infinitely many "
            "solutions.")
        if parts:
            steps.append(f"Solutions: {parts}, with "
                         f"{', '.join(free) or 'a parameter'} "
                         "free (any real value).")
        return {"type": "linear_algebra",
                "op": "w190_consistency",
                "answer": "Infinitely many solutions"
                          + (f": {parts}" if parts else ""),
                "steps": steps}
    inv = A.inv()
    steps.append(f"A^-1 = {_mstr(inv)}")
    X = inv * B
    xvals = [X[i] for i in range(X.rows)]
    steps.append(f"X = A^-1 B = {_mstr(X.T)}")
    # Verify against every original equation before serving.
    for lhs_row, rhs in zip(A.tolist(), B.tolist()):
        val = sum(c * v for c, v in zip(lhs_row, xvals))
        if sp.simplify(val - rhs[0]) != 0:
            return None
    final = ", ".join(f"{u} = {fmt_num(v)}" for u, v in
                      zip(unknowns, xvals))
    steps.append(f"Check: the values satisfy every equation. "
                 f"{final}.")
    return {"type": "linear_algebra", "op": "w190_matrix_method",
            "answer": final, "steps": steps}


# ---------------------------------------------------------------------------
# (b) A'A = I / AA' = I — find the unknowns, plain dress
# ---------------------------------------------------------------------------

def _solve_ata_identity(question, q, ql):
    qn = q.replace("A^T", "A'").replace("A^t", "A'")
    squashed = qn.replace(" ", "").lower()
    transpose_first = "a'a=i" in squashed
    first_first = "aa'=i" in squashed
    if not (transpose_first or first_first):
        if re.search(r"a\s+transpose\s+a\s*=\s*i\b", ql):
            transpose_first = True
        elif re.search(r"a\s+a\s+transpose\s*=\s*i\b", ql):
            first_first = True
        else:
            return None
    if "find" not in ql and "determine" not in ql:
        return None
    A = _named_matrix(q, "A")
    if A is None:
        A = _first_matrix(q)
    if A is None or A.rows != A.cols or A.rows not in (2, 3):
        return None
    for e in A:
        if not _check_cell(e):
            return None
    unknowns = []
    for e in A:
        for name in ("x", "y", "z", "w", "a", "b"):
            s = sp.Symbol(name)
            if s in e.free_symbols and s not in unknowns:
                unknowns.append(s)
    if not unknowns or len(unknowns) > 3:
        return None
    P = A.T * A if transpose_first else A * A.T
    label = "A'A" if transpose_first else "AA'"
    I = sp.eye(A.rows)
    eqs = []
    for i in range(A.rows):
        for j in range(A.cols):
            e = sp.expand(P[i, j] - I[i, j])
            if e != 0:
                eqs.append(sp.Eq(P[i, j], I[i, j]))
    if not eqs:
        return None
    try:
        sols = sp.solve(eqs, unknowns, dict=True)
    except Exception:
        return None
    if not sols or len(sols) > 4:
        return None
    verified = []
    for sol in sols:
        if set(sol.keys()) != set(unknowns):
            continue
        if any(v.free_symbols for v in sol.values()):
            continue
        Pv = P.subs(sol).applyfunc(
            lambda e: sp.simplify(sp.expand(e)))
        if Pv == I:
            verified.append(sol)
    if not verified:
        return None
    steps = [
        f"A = {_mstr(A)}",
        f"{label} = {_mstr(P.applyfunc(sp.expand))}",
        f"Set {label} = I and equate corresponding entries.",
    ]
    answers = []
    for sol in verified:
        part = ", ".join(f"{u} = {fmt_num(sol[u])}"
                         for u in unknowns)
        answers.append(part)
        steps.append(f"Solving gives {part} — substituting "
                     f"back, {label} = I is confirmed.")
    return {"type": "linear_algebra", "op": "w190_ata_identity",
            "answer": " or ".join(answers), "steps": steps}


# ---------------------------------------------------------------------------
# (c) Verify / prove dresses — computed verdicts only
# ---------------------------------------------------------------------------

def _verify_dresses(question, q, ql):
    if not any(w in ql for w in ("verify", "show", "prove")):
        return None
    qn = q.replace("A^T", "A'").replace("B^T", "B'") \
          .replace("A^t", "A'").replace("B^t", "B'")
    squashed = qn.replace(" ", "").lower()

    # (c1) (AB)' = B'A' — and the false dress (AB)' = A'B'.
    claim = None
    if "(ab)'=b'a'" in squashed or "b'a'=(ab)'" in squashed:
        claim = "B'A'"
    elif "(ab)'=a'b'" in squashed or "a'b'=(ab)'" in squashed:
        claim = "A'B'"
    if claim is not None:
        A = _named_matrix(q, "A")
        B = _named_matrix(q, "B")
        if not _numeric(A) or not _numeric(B):
            return None
        if A.cols != B.rows:
            return None
        lhs = (A * B).T
        rhs = B.T * A.T if claim == "B'A'" else A.T * B.T
        steps = [
            f"A = {_mstr(A)}, B = {_mstr(B)}",
            f"AB = {_mstr(A * B)}, so (AB)' = {_mstr(lhs)}.",
            f"{claim} = {_mstr(rhs)}.",
        ]
        if lhs == rhs:
            steps.append("Both sides are equal, so "
                         f"(AB)' = {claim} is verified.")
            return {"type": "linear_algebra",
                    "op": "w190_verify_transpose_product",
                    "answer": f"(AB)' = {claim} = "
                              f"{_mstr(lhs)} (verified)",
                    "steps": steps}
        steps.append("The two sides are not equal, so the "
                     "stated identity does not hold for "
                     "these matrices.")
        return {"type": "linear_algebra",
                "op": "w190_verify_transpose_product",
                "answer": f"(AB)' = {_mstr(lhs)} but "
                          f"{claim} = {_mstr(rhs)} — not "
                          "equal, so the identity does not "
                          "hold for these matrices",
                "steps": steps}

    # (c4) AB - BA skew-symmetric for symmetric A, B.
    if "ab-ba" in squashed and "skew" in ql:
        A = _named_matrix(q, "A")
        B = _named_matrix(q, "B")
        if not _numeric(A) or not _numeric(B):
            return None
        if A.rows != A.cols or B.rows != B.cols \
                or A.rows != B.rows:
            return None
        steps = [f"A = {_mstr(A)}, B = {_mstr(B)}"]
        if A != A.T or B != B.T:
            bad = "A" if A != A.T else "B"
            steps.append(
                f"But {bad}' = "
                f"{_mstr(A.T if bad == 'A' else B.T)}, which "
                f"is not equal to {bad} — the given matrix "
                "is not symmetric, so the claim does not "
                "apply as stated.")
            return {"type": "linear_algebra",
                    "op": "w190_verify_ab_ba_skew",
                    "answer": f"{bad} is not symmetric for "
                              "the given matrices, so the "
                              "claim does not apply as stated",
                    "steps": steps}
        steps.append("A' = A and B' = B (both symmetric, "
                     "checked entry by entry).")
        E = A * B - B * A
        steps.append(f"AB - BA = {_mstr(E)}.")
        steps.append(f"(AB - BA)' = {_mstr(E.T)}.")
        if E == -E.T:
            steps.append("(AB - BA)' = -(AB - BA), so "
                         "AB - BA is skew-symmetric — "
                         "verified.")
            return {"type": "linear_algebra",
                    "op": "w190_verify_ab_ba_skew",
                    "answer": f"AB - BA = {_mstr(E)}, which "
                              "is skew-symmetric (verified)",
                    "steps": steps}
        steps.append("(AB - BA)' is not equal to "
                     "-(AB - BA), so AB - BA is not "
                     "skew-symmetric for these matrices.")
        return {"type": "linear_algebra",
                "op": "w190_verify_ab_ba_skew",
                "answer": f"AB - BA = {_mstr(E)} is not "
                          "skew-symmetric for these matrices",
                "steps": steps}

    # (c2)/(c3) A + A' symmetric / A - A' skew-symmetric.
    expr_label = None
    E = None
    A = _named_matrix(q, "A")
    if A is None:
        A = _first_matrix(q)
    if _numeric(A) and A.rows == A.cols:
        if "a+a'" in squashed:
            expr_label, E = "A + A'", A + A.T
        elif "a-a'" in squashed:
            expr_label, E = "A - A'", A - A.T
    if E is not None:
        is_sym = E == E.T
        is_skew = E == -E.T
        claimed = "skew" if "skew" in ql else "symmetric"
        actual = "skew-symmetric" if is_skew else (
            "symmetric" if is_sym else "neither symmetric "
            "nor skew-symmetric")
        steps = [
            f"A = {_mstr(A)}, so A' = {_mstr(A.T)}.",
            f"{expr_label} = {_mstr(E)}.",
            f"({expr_label})' = {_mstr(E.T)}.",
        ]
        holds = (claimed == "skew" and is_skew) or \
            (claimed != "skew" and is_sym)
        if holds:
            steps.append(
                f"({expr_label})' "
                f"{'= -(' + expr_label + ')' if is_skew else '= ' + expr_label}, "
                f"so {expr_label} is {actual} — verified.")
            return {"type": "linear_algebra",
                    "op": "w190_verify_sum_symmetric"
                    if expr_label == "A + A'" else
                    "w190_verify_diff_skew",
                    "answer": f"{expr_label} = {_mstr(E)}, "
                              f"which is {actual} (verified)",
                    "steps": steps}
        steps.append(
            f"So {expr_label} is {actual}, not "
            f"{'skew-symmetric' if claimed == 'skew' else 'symmetric'} "
            "as stated.")
        return {"type": "linear_algebra",
                "op": "w190_verify_sum_symmetric"
                if expr_label == "A + A'" else
                "w190_verify_diff_skew",
                "answer": f"{expr_label} = {_mstr(E)} is "
                          f"{actual}, not "
                          f"{'skew-symmetric' if claimed == 'skew' else 'symmetric'} "
                          "as stated",
                "steps": steps}
    return None


# ---------------------------------------------------------------------------
# (d) Hence-find-A^-1 chains
# ---------------------------------------------------------------------------

_POLY_RE = re.compile(
    r"a\s*\^\s*2\s*([+\-])\s*(\d+(?:\.\d+)?)?\s*\*?\s*a\b"
    r"\s*([+\-])\s*(\d+(?:\.\d+)?)?\s*\*?\s*i\s*=\s*[o0]\b",
    re.I)


def _hence_inverse(question, q, ql):
    if "hence" not in ql:
        return None
    squashed = q.replace(" ", "").lower()
    if "a^-1" not in squashed and "inverse" not in ql:
        return None
    m = _POLY_RE.search(q)
    if not m:
        return None
    p = sp.Rational(m.group(2)) if m.group(2) else sp.Integer(1)
    if m.group(1) == "-":
        p = -p
    qq = sp.Rational(m.group(4)) if m.group(4) else sp.Integer(1)
    if m.group(3) == "-":
        qq = -qq
    if qq == 0:
        return None
    A = _named_matrix(q, "A")
    if A is None:
        A = _first_matrix(q)
    if not _numeric(A) or A.rows != A.cols \
            or A.rows not in (2, 3):
        return None
    n = A.rows
    I = sp.eye(n)
    premise = A * A + p * A + qq * I
    if premise != sp.zeros(n):
        return None
    inv = -(A + p * I) / qq
    inv = inv.applyfunc(lambda e: sp.nsimplify(e, rational=True))
    if A * inv != I or inv * A != I:
        return None
    term_a = f"{fmt_num(abs(p))}A" if abs(p) != 1 else "A"
    term_i = f"{fmt_num(abs(qq))}I" if abs(qq) != 1 else "I"
    eq_str = (f"A^2 {'+' if p >= 0 else '-'} {term_a} "
              f"{'+' if qq >= 0 else '-'} {term_i} = O")
    steps = [
        f"A = {_mstr(A)}",
        f"Given: {eq_str} (checked first: substituting A "
        "makes every entry of the left side 0).",
        "From A(A + pI) = -qI, post-multiplying by A^-1 "
        "gives A + pI = -q A^-1, so "
        f"A^-1 = -(A + ({fmt_num(p)})I)/({fmt_num(qq)}).",
        f"A^-1 = {_mstr(inv)}",
        f"Check: A A^-1 = {_mstr(A * inv)} = I. Verified.",
    ]
    return {"type": "linear_algebra", "op": "w190_hence_inverse",
            "answer": f"A^-1 = {_mstr(inv)}", "steps": steps}


# ---------------------------------------------------------------------------
# (e) Matrix word problems — NCERT narrative templates
# ---------------------------------------------------------------------------

def _amounts_after(text, start=0):
    return [(m.start(), m.group(1).replace(",", ""))
            for m in re.finditer(r"rs\.?\s*([\d,]+(?:\.\d+)?)",
                                 text.lower()[start:])]


def _trust_fund(question, q, ql):
    if "bond" not in ql or "invest" not in ql:
        return None
    if "trust fund" not in ql and "matrix" not in ql:
        return None
    rates = [sp.Rational(m.group(1)) / 100 for m in
             re.finditer(r"(\d+(?:\.\d+)?)\s*%", q)]
    if len(rates) != 2 or rates[0] == rates[1]:
        return None
    amounts = _amounts_after(q)
    if len(amounts) < 2:
        return None
    total = sp.Rational(amounts[0][1])
    interest = sp.Rational(amounts[-1][1])
    if interest == total or interest <= 0 or total <= 0:
        return None
    r1, r2 = rates
    A = Matrix([[1, 1], [r1, r2]])
    B = Matrix([total, interest])
    if A.det() == 0:
        return None
    X = A.inv() * B
    xv, yv = X[0], X[1]
    if xv <= 0 or yv <= 0:
        return None
    if sp.simplify(xv + yv - total) != 0 or \
            sp.simplify(r1 * xv + r2 * yv - interest) != 0:
        return None
    steps = [
        "Let Rs x be invested in the first bond and Rs y "
        "in the second bond.",
        f"x + y = {fmt_num(total)} (the total amount) and "
        f"{fmt_num(r1)}x + {fmt_num(r2)}y = "
        f"{fmt_num(interest)} (the target interest).",
        f"In matrix form: [[1, 1], [{fmt_num(r1)}, "
        f"{fmt_num(r2)}]] [x, y]^T = [{fmt_num(total)}, "
        f"{fmt_num(interest)}]^T.",
        f"Solving by the matrix method: x = {fmt_num(xv)}, "
        f"y = {fmt_num(yv)}.",
        f"Check: {fmt_num(xv)} + {fmt_num(yv)} = "
        f"{fmt_num(total)} and interest = "
        f"{fmt_num(r1 * xv)} + {fmt_num(r2 * yv)} = "
        f"{fmt_num(interest)}. Correct.",
    ]
    return {"type": "linear_algebra", "op": "w190_trust_fund",
            "answer": f"Rs {fmt_num(xv)} in the first bond "
                      f"and Rs {fmt_num(yv)} in the second "
                      "bond",
            "steps": steps}


_MARKET_RE = re.compile(
    r"market\s*(i{1,2}|1|2|one|two)\s*[:\-]?\s*"
    r"((?:[a-z]\s*=\s*[\d,]+\s*,?\s*(?:and\s*)?)+)",
    re.I)


def _clause_amounts(q, keyword):
    idx = q.lower().find(keyword)
    if idx == -1:
        return None
    seg = q[idx:idx + 400].lower()
    seg = seg.split("respectively")[0]
    vals = re.findall(r"rs\.?\s*([\d,]+(?:\.\d+)?)", seg)
    if len(vals) < 2:
        # "Rs 2.50, 1.50 and 1.00" dress: only the first
        # amount carries the Rs marker.
        m = re.search(r"rs\.?\s*([\d,]+(?:\.\d+)?)\s*,"
                      r"(.+)$", seg, re.S)
        if m:
            rest = re.findall(r"[\d,]+(?:\.\d+)?",
                              m.group(2))
            if rest:
                vals = [m.group(1)] + rest
    if not vals:
        return None
    return [sp.nsimplify(v.replace(",", ""), rational=True)
            for v in vals]


def _manufacturer(question, q, ql):
    if "manufacturer" not in ql or "market" not in ql:
        return None
    if "revenue" not in ql and "sale price" not in ql \
            and "selling price" not in ql:
        return None
    markets = []
    for m in _MARKET_RE.finditer(q):
        entries = re.findall(
            r"([a-z])\s*=\s*([\d,]+)", m.group(2), re.I)
        if not entries:
            return None
        markets.append([(k.upper(), sp.Rational(
            v.replace(",", ""))) for k, v in entries])
    if len(markets) != 2:
        return None
    products = [k for k, _ in markets[0]]
    if len(products) not in (2, 3):
        return None
    if [k for k, _ in markets[1]] != products:
        return None
    prices = _clause_amounts(q, "sale price")
    if prices is None:
        prices = _clause_amounts(q, "selling price")
    if prices is None or len(prices) != len(products):
        return None
    S = Matrix([[v for _, v in row] for row in markets])
    P = Matrix(prices)
    revenue = S * P
    steps = [
        f"Sales matrix S = {_mstr(S)} (rows: Market I, "
        "Market II; columns: "
        f"{', '.join(products)}).",
        f"Price column P = {_mstr(P.T)}.",
        f"Revenue = S P = {_mstr(revenue.T)}.",
    ]
    answer = (f"Revenue: Market I = Rs "
              f"{fmt_num(revenue[0])}, Market II = Rs "
              f"{fmt_num(revenue[1])}")
    if "cost" in ql and ("profit" in ql or "cost price" in ql):
        costs = _clause_amounts(q, "cost")
        if costs is not None and len(costs) == len(products):
            margin = Matrix([p - c for p, c in
                             zip(prices, costs)])
            profit = S * margin
            if all(v >= 0 for v in margin):
                steps.append(
                    f"Profit per unit = P - C = "
                    f"{_mstr(margin.T)}; gross profit = "
                    f"S (P - C) = {_mstr(profit.T)}.")
                answer += (f"; Profit: Market I = Rs "
                           f"{fmt_num(profit[0])}, Market II "
                           f"= Rs {fmt_num(profit[1])}")
    return {"type": "linear_algebra",
            "op": "w190_market_revenue",
            "answer": answer, "steps": steps}


_BRANCHES = (_solve_matrix_method, _solve_ata_identity,
             _verify_dresses, _hence_inverse, _trust_fund,
             _manufacturer)


def solve_matrix190(question):
    """Wave 190 matrix-family schemas; None unless one of
    the strict branches settles the question completely
    with a verified answer."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip():
        return None
    ql = q.lower()
    for branch in _BRANCHES:
        try:
            out = branch(question, q, ql)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
