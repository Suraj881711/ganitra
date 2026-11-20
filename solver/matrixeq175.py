"""Wave 175: matrix equality — find the unknowns by equating
corresponding entries of two equal matrices.

Why this module exists (Suraj's live test, 19 Nov 2026,
09:25 IST): he pasted the classic Class 12 question

    [[x-y, 2x+z], [2x-y, 2x+w]] = [[-1, 0], [5, 13]]
    find x, y, z and w            (answer: 6, 7, -12, 1)

and Ganitra never answered — the chat showed the Wave 145
"Server is slow right now" line.  Diagnosis (measured; see
ganitra-wave175-notes.md): route_intent sends the question
to linear_algebra, whose _parse_matrix_block whitelist
accepts DIGITS ONLY, so a symbolic-entry matrix raises
ValueError ("Invalid matrix format"); every failure-only
gate declines (none owned matrices); the app layer then
walks the fallback chain — Live Bank miss, salvage, the
three AI legs (Gemini 2 models x 15 s, Groq 15 s,
OpenRouter 12 s), the Wave 133 verification leg and the
Wave 134 deep-solve — whose combined ceiling is far past
the browser's 45 s abort, so the fetch dies and the client
honestly renders the server-slow line.  The native solver
simply had NO matrix-equality schema: solver/linear_algebra.py
covers numeric add / subtract / multiply, scalar multiples,
determinant, inverse, transpose, trace, rank, eigen and
A.x = b, but nothing equates two matrices entry by entry.

This module is that schema, in the house style of Waves
169/171: it fires only when it settles the question
COMPLETELY, every value is recomputed exactly (SymPy) and
verified by substitution into every entry before serving,
and anything doubtful returns None so routing continues
unchanged.  Wiring: a failure-only gate at the end of
router._solve_question_uncached, after the Wave 171 block —
a question the solver already answers is never displaced.

Accepted shapes (all strict):
  A. Two [[...]] blocks with an equality between them —
     directly ("[[..]] = [[..]]") or named ("A = [[..]],
     B = [[..]], A = B", "... is equal to ...").
  B. Two single-bracket grids with ';' rows and a direct
     '=': "[x-y 2x+z; 2x-y 2x+w] = [-1 0; 5 13]".
  C. The flattened paste (no brackets at all): the token
     stream after the last ':' must segment into EXACTLY
     2n^2 entries (n = 2 or 3), the last n^2 of them plain
     numbers.  A stream that is short an entry (Suraj's
     actual paste has 7 of the 8) is DECLINED: the missing
     entry's position cannot be determined, and different
     positions give different values for the same unknowns
     (x = 6 vs x = 14), so any serve would be a guess.
     Wave 207: the one-short stream is now DETECTED
     (matrixeq_near_miss below) so the fallback layer can
     say so at once — Suraj's rule (20 Nov 2026): a
     question that is itself defective earns a kind "ye
     sawal galat hai" line naming the missing entry, never
     the slow AI chain or the generic clarification.  The
     flat path's literal "matrix"/"find" word gates are
     also loosened: when the stream's shape is unambiguous
     on its own, the words are no longer required.

Entries may be numbers or LINEAR expressions in up to 4
distinct unknowns drawn from {x, y, z, w, a, b} (capitals
folded).  Non-linear entries (x^2, x*y, 1/x, sin x),
ragged / mismatched / non-square shapes, constant-entry
disagreements, underdetermined systems and inconsistent
systems all decline.
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

_ALLOWED = ("x", "y", "z", "w", "a", "b")
_ALLOWED_SET = set(_ALLOWED)
_MAX_UNKNOWNS = 4
_CAP_FOLD = {c: c.lower() for c in "XYZWAB"}


def _prep(text):
    s = str(text)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("×", "*")
    return s


def _cell_expr(text):
    """Parse one matrix entry; fold capital unknowns (Z -> z).
    Raises ValueError on anything unparseable."""
    t = str(text).strip()
    if not t:
        raise ValueError("empty cell")
    expr = parse_expression(t)
    if isinstance(expr, tuple):
        raise ValueError("tuple cell")
    subs = {}
    for sym in expr.free_symbols:
        name = str(sym)
        if name in _CAP_FOLD:
            subs[sym] = sp.Symbol(_CAP_FOLD[name])
    if subs:
        expr = expr.subs(subs)
    return expr


def _check_cell(expr):
    """True when the entry is a number or a LINEAR expression
    in the allowed unknowns only."""
    syms = expr.free_symbols
    if not syms:
        return True
    if any(str(s) not in _ALLOWED_SET for s in syms):
        return False
    try:
        poly = sp.Poly(expr, *sorted(syms, key=str))
    except Exception:
        return False
    if poly is None or poly.total_degree() > 1:
        return False
    return True


def _grid_from_bracket_inner(inner):
    """'x-y, 2x+z],[2x-y, 2x+w' -> rows of cell texts."""
    rows = []
    for row_text in re.split(r"\]\s*,\s*\[", inner):
        cells = [c.strip() for c in row_text.split(",")]
        if any(not c for c in cells):
            return None
        rows.append(cells)
    return rows


def _grid_from_semicolon(content):
    """'x-y 2x+z; 2x-y 2x+w' (or comma cells) -> rows of texts,
    Wave 80 grid rules."""
    rows = []
    for row_text in content.split(";"):
        row_text = row_text.strip()
        if not row_text:
            continue
        if "," in row_text:
            cells = [c.strip() for c in row_text.split(",")]
        else:
            cells = row_text.split()
        if any(not c for c in cells):
            return None
        rows.append(cells)
    return rows or None


def _expr_grid(text_rows):
    """Rows of cell texts -> rows of sympy exprs, or None when
    the grid is ragged, not square 2x2 / 3x3, or any cell is
    not a number / allowed linear expression."""
    if not text_rows:
        return None
    n = len(text_rows)
    if n not in (2, 3):
        return None
    if any(len(r) != n for r in text_rows):
        return None
    grid = []
    for row in text_rows:
        exprs = []
        for cell in row:
            try:
                expr = _cell_expr(cell)
            except Exception:
                return None
            if not _check_cell(expr):
                return None
            exprs.append(expr)
        grid.append(exprs)
    return grid


def _solve_pair(lhs, rhs):
    """Two expr grids of the same square shape -> the result
    dict, or None.  Equate corresponding entries, solve the
    linear system exactly, verify by substitution into
    EVERY entry before serving."""
    n = len(lhs)
    # Unknowns in first-appearance order, row-major:
    ordered = []
    for grid in (lhs, rhs):
        for row in grid:
            for expr in row:
                for name in _ALLOWED:
                    if sp.Symbol(name) in expr.free_symbols \
                            and sp.Symbol(name) not in ordered:
                        ordered.append(sp.Symbol(name))
    unknowns = ordered
    if not unknowns or len(unknowns) > _MAX_UNKNOWNS:
        return None
    equations = []
    display = []
    for i in range(n):
        for j in range(n):
            l, r = lhs[i][j], rhs[i][j]
            if l.free_symbols or r.free_symbols:
                equations.append(sp.Eq(l, r))
                display.append(f"{fmt(l)} = {fmt(r)}")
            elif sp.simplify(l - r) != 0:
                # A constant entry pair already disagrees:
                # the matrices cannot be equal.
                return None
    if not equations:
        return None
    try:
        sols = sp.solve(equations, unknowns, dict=True)
    except Exception:
        return None
    if len(sols) != 1:
        return None
    sol = sols[0]
    if set(sol.keys()) != set(unknowns):
        return None
    for u in unknowns:
        v = sol[u]
        if v.free_symbols or v.is_real is False:
            return None
    # Verify by substitution into every corresponding pair.
    for i in range(n):
        for j in range(n):
            if sp.simplify(lhs[i][j].subs(sol)
                           - rhs[i][j].subs(sol)) != 0:
                return None
    final = ", ".join(f"{u} = {fmt_num(sol[u])}" for u in unknowns)
    steps = ["Equal matrices have equal corresponding "
             "entries — equate each pair:"]
    steps.extend(display)
    steps.append(f"Solving, we get {final}.")
    return {"type": "linear_algebra", "op": "matrix_equality",
            "answer": final, "steps": steps}


def _path_brackets(q):
    blocks = list(re.finditer(r"\[\[(.*?)\]\]", q, re.S))
    if len(blocks) != 2:
        return None
    between = q[blocks[0].end():blocks[1].start()]
    if "=" not in between:
        return None
    ql = q.lower()
    direct = re.fullmatch(r"[\s,;.]*=[\s,;.]*", between) is not None
    named = re.search(r"\ba\s*=\s*b\b", ql) is not None \
        or "equal" in ql
    if not (direct or named):
        return None
    lhs = _expr_grid(_grid_from_bracket_inner(blocks[0].group(1)))
    rhs = _expr_grid(_grid_from_bracket_inner(blocks[1].group(1)))
    if lhs is None or rhs is None or len(lhs) != len(rhs):
        return None
    return _solve_pair(lhs, rhs)


def _path_semicolon(q):
    m = re.search(r"\[([^\[\]]+)\]\s*=\s*\[([^\[\]]+)\]", q)
    if not m or ";" not in m.group(1) or ";" not in m.group(2):
        return None
    lhs = _expr_grid(_grid_from_semicolon(m.group(1)))
    rhs = _expr_grid(_grid_from_semicolon(m.group(2)))
    if lhs is None or rhs is None or len(lhs) != len(rhs):
        return None
    return _solve_pair(lhs, rhs)


_ENTRY_START_NUM = re.compile(r"^[+\-]?\d")
_SIGNED_LETTER = re.compile(r"^[+\-][a-zA-Z]$|^[+\-][a-zA-Z]\d")
_LETTER_START = re.compile(r"^[a-zA-Z]")


def _segment_flat(stream):
    """Segment a flattened entry stream ('x- y 2x +Z 2x- y
    -1 0 5 13') into entry texts, deterministically: a token
    continues the current entry when the entry ends with an
    operator, when the token is a bare operator, or when it
    is a signed letter term ('+Z'); a signed / plain number
    or a fresh letter term starts a new entry.  Returns None
    on any token shape outside these rules."""
    tokens = stream.split()
    if not tokens:
        return None
    entries = []
    cur = ""
    for tok in tokens:
        if not cur:
            cur = tok
            continue
        if cur[-1] in "+-*/^(" or tok in ("+", "-", "*", "/"):
            cur += " " + tok
        elif _SIGNED_LETTER.match(tok):
            cur += " " + tok
        elif _ENTRY_START_NUM.match(tok) or _LETTER_START.match(tok):
            entries.append(cur)
            cur = tok
        else:
            return None
    entries.append(cur)
    return entries


def _path_flat(q):
    if "[" in q or "]" in q:
        return None
    if ":" not in q:
        return None
    stream = q.rsplit(":", 1)[1].strip().rstrip("?.")
    entries = _segment_flat(stream)
    if entries is None:
        return None
    ql = q.lower()
    # Wave 207: the literal word gates ("matrix" AND "find")
    # used to be required before the shape was even looked
    # at, so a perfectly unambiguous flattened paste that
    # happened to name neither word was declined unread.
    # The words now only waive the extra shape proof: when
    # they are absent, the stream itself must prove the
    # shape — exactly 2n^2 entries, the last n^2 plain
    # numbers, and the first n^2 linear cells carrying at
    # least two distinct unknowns — and _solve_pair still
    # verifies the full system before anything is served.
    strict_words = ("matrix" in ql or "matrices" in ql) \
        and "find" in ql
    for n in (2, 3):
        if len(entries) != 2 * n * n:
            continue
        lhs_texts = entries[:n * n]
        rhs_texts = entries[n * n:]
        # The numeric side must be plain numbers, entry by
        # entry — that is what pins the split point.
        rhs_rows = []
        ok = True
        for i in range(n):
            row = []
            for j in range(n):
                try:
                    e = _cell_expr(rhs_texts[i * n + j])
                except Exception:
                    ok = False
                    break
                if e.free_symbols:
                    ok = False
                    break
                row.append(e)
            if not ok:
                break
            rhs_rows.append(row)
        if not ok:
            return None
        lhs_rows = []
        for i in range(n):
            row = []
            for cell in lhs_texts[i * n:(i + 1) * n]:
                try:
                    e = _cell_expr(cell)
                except Exception:
                    return None
                if not _check_cell(e):
                    return None
                row.append(e)
            lhs_rows.append(row)
        if not strict_words:
            unknowns = set()
            for row in lhs_rows:
                for e in row:
                    unknowns |= {str(s) for s in e.free_symbols}
            if len(unknowns) < 2:
                return None
        return _solve_pair(lhs_rows, rhs_rows)
    return None


def matrixeq_near_miss(question):
    """Wave 207: detect the DEFECTIVE flattened paste — a
    bracket-free, colon-led entry stream that segments to
    exactly ONE entry short of a square matrix equality
    (2n^2 - 1 entries for n = 2 or 3), with matrix-equality
    intent in the text.  The missing entry's position
    cannot be determined, so the values cannot be solved
    (shape C's documented ambiguity) — but the question is
    recognisably a real matrix question with a piece
    missing, which is exactly what the fallback layer's
    Wave 207 'ye sawal galat hai' serve reports.  Returns
    {"n": n, "entries": count} or None.  Strict shape: at
    least two entries must be allowed linear expressions
    and at least three plain numbers, over at least two
    distinct unknowns; anything else is not this shape."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q or "[" in q or "]" in q:
        return None
    ql = q.lower()
    if "matrix" not in ql and "matrices" not in ql:
        return None
    if ":" not in q:
        return None
    stream = q.rsplit(":", 1)[1].strip().rstrip("?.")
    entries = _segment_flat(stream)
    if not entries:
        return None
    for n in (2, 3):
        if len(entries) not in (2 * n * n - 1, 2 * n * n - 2):
            continue
        nums = 0
        exprs = 0
        unknowns = set()
        for cell in entries:
            try:
                e = _cell_expr(cell)
            except Exception:
                return None
            if not _check_cell(e):
                return None
            if e.free_symbols:
                exprs += 1
                unknowns |= {str(s) for s in e.free_symbols}
            else:
                nums += 1
        if exprs >= 2 and nums >= 3 and len(unknowns) >= 2:
            return {"n": n, "entries": len(entries)}
        return None
    return None


def solve_matrix_equality(question):
    """Wave 175 matrix-equality schema; None unless one of
    the strict shapes matches completely and the solved
    values verify against every entry."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip():
        return None
    for path in (_path_brackets, _path_semicolon, _path_flat):
        try:
            out = path(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
