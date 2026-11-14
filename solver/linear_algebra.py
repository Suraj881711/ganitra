"""Linear algebra: matrix operations, determinant, inverse, transpose,
trace, rank, eigenvalues/eigenvectors and solving A·x = b — with steps.
"""
import re

import sympy as sp
from sympy import Matrix

from .expression_parser import fmt


def _parse_matrix_block(block: str) -> Matrix:
    """Parse '[[1,2],[3,4]]' or '1,2;3,4' into a SymPy Matrix."""
    block = block.strip().replace(";", "],[")
    if not (block.startswith("[[") and block.endswith("]]")):
        block = f"[[{block}]]"
    if not re.fullmatch(r"[\[\],\s0-9+\-\.]+", block):
        raise ValueError("Invalid matrix format")
    return Matrix(eval(block))  # safe: character whitelist checked above


def _find_matrices(text: str):
    return [_parse_matrix_block(m.group(0))
            for m in re.finditer(r"\[\[[^\]]*\](?:\s*,\s*\[[^\]]*\])*\]",
                                 text)]


def _mstr(M: Matrix) -> str:
    return str(M.tolist()).replace("'", "")


def solve_linear_algebra(question: str):
    q = question
    ql = q.lower()

    # A = [[...]], b = [[...]]  -> solve A x = b
    mA = re.search(r"A\s*=\s*(\[\[.+?\]\])", q, re.S)
    mb = re.search(r"b\s*=\s*(\[\[.+?\]\]|\[[^\]]+\])", q, re.S)
    if mA and mb:
        A = _parse_matrix_block(mA.group(1))
        b_raw = mb.group(1)
        b = _parse_matrix_block(b_raw)
        if b.rows == 1:
            b = b.T
        x = A.LUsolve(b)
        steps = [
            f"A = {_mstr(A)}, b = {_mstr(b.T)}",
            "Solve A·x = b by Gaussian elimination (equivalently "
            "x = A^-1 · b).",
            f"x = {_mstr(x)}",
        ]
        return {"type": "linear_algebra", "op": "solve",
                "answer": _mstr(x), "x": _mstr(x), "steps": steps}

    mats = _find_matrices(q)
    if not mats:
        raise ValueError("Provide a matrix like [[1,2],[3,4]].")
    M = mats[0]

    # Wave 42: named two-matrix ops — "find A - B", "find AB".
    # The old block only saw operator characters or keywords
    # between the matrices, so "find A - B" silently returned
    # A + B and "find AB" fell through entirely. "Subtract X
    # from Y" names the subtrahend first: the result is Y - X,
    # NOT text order (the old code returned [[-4, -4], ...]
    # for "Subtract [[5,6],[7,8]] from [[9,10],[11,12]]").
    _named42 = None
    _sub_from42 = False
    if len(mats) >= 2:
        if re.search(r"(?<![A-Za-z])A\s*-\s*B(?![A-Za-z])", q):
            _named42 = ("subtract", mats[0] - mats[1],
                        "A - B: subtract the second matrix "
                        "from the first, entry by entry.")
        elif re.search(r"(?<![A-Za-z])B\s*-\s*A(?![A-Za-z])", q):
            _named42 = ("subtract", mats[1] - mats[0],
                        "B - A: subtract the first matrix "
                        "from the second, entry by entry.")
        elif re.search(r"(?<![A-Za-z])A\s*\+\s*B(?![A-Za-z])", q):
            _named42 = ("add", mats[0] + mats[1],
                        "A + B: add the two matrices entry "
                        "by entry.")
        elif re.search(r"(?<![A-Za-z])AB(?![A-Za-z])", q) or \
                re.search(r"(?<![A-Za-z])A\s*\*\s*B"
                          r"(?![A-Za-z])", q):
            _named42 = ("multiply", mats[0] * mats[1],
                        "AB: multiply the first matrix by "
                        "the second — each entry is a "
                        "row·column dot product.")
        elif re.search(r"(?<![A-Za-z])BA(?![A-Za-z])", q):
            _named42 = ("multiply", mats[1] * mats[0],
                        "BA: multiply the second matrix by "
                        "the first — each entry is a "
                        "row·column dot product.")
        _si42 = ql.find("subtract")
        if _named42 is None and _si42 != -1 \
                and "[[" in ql[_si42:] \
                and re.search(r"\bfrom\b", ql[_si42:]):
            _sub_from42 = True
    if _sub_from42:
        R = mats[1] - mats[0]
        steps = [
            "'Subtract X from Y' means Y - X: subtract the "
            "first-named matrix from the second, entry by "
            "entry.",
            f"Result: {_mstr(R)}",
        ]
        return {"type": "linear_algebra", "op": "subtract",
                "answer": _mstr(R), "steps": steps}
    if _named42 is not None:
        _op42, _R42, _step42 = _named42
        return {"type": "linear_algebra", "op": _op42,
                "answer": _mstr(_R42),
                "steps": [_step42, f"Result: {_mstr(_R42)}"]}

    # Two-matrix arithmetic: [[..]] * [[..]], "multiply", "add", ...
    _between = q.split("]]", 1)[1] if "]]" in q else ""
    if len(mats) >= 2 and (
        "*" in _between or "+" in _between or "-" in _between
        or "multiply" in ql or "product" in ql or "add" in ql
        or "sum" in ql or "subtract" in ql
    ):
        A, B = mats[0], mats[1]
        if "*" in q or "multiply" in ql or "product" in ql:
            R = A * B
            steps = [
                f"Multiply {A.rows}x{A.cols} by {B.rows}x{B.cols}: each "
                "entry is a row·column dot product.",
                f"Result: {_mstr(R)}",
            ]
            return {"type": "linear_algebra", "op": "multiply",
                    "answer": _mstr(R), "steps": steps}
        if "subtract" in ql or re.search(r"\]\]\s*-", q):
            R = A - B
            opname = "subtract"
        else:
            R = A + B
            opname = "add"
        steps = [
            f"{'Subtract' if opname == 'subtract' else 'Add'} the two "
            "matrices entry by entry.",
            f"Result: {_mstr(R)}",
        ]
        return {"type": "linear_algebra", "op": opname,
                "answer": _mstr(R), "steps": steps}

    # Wave 42: scalar multiple — "Find 2A if A = [[...]]",
    # "Find A * 3". One matrix, one number: multiply every
    # entry. Skipped when another matrix task is named.
    if len(mats) == 1 and re.search(r"\bA\s*=", q) and not \
            re.search(r"determinant|inverse|transpose|rank|"
                      r"trace|eigen", ql):
        _ms42 = re.search(r"(?<![\d.])(\d+(?:\.\d+)?)\s*\*?\s*"
                          r"A\b", q) or re.search(
                              r"\bA\s*\*\s*(\d+(?:\.\d+)?)", q)
        if _ms42:
            _k42 = sp.nsimplify(_ms42.group(1), rational=True)
            R = _k42 * M
            steps = [
                f"Scalar multiplication: multiply every entry "
                f"of A by {fmt(_k42)}.",
                f"Result: {_mstr(R)}",
            ]
            return {"type": "linear_algebra",
                    "op": "scalar_multiply",
                    "answer": _mstr(R), "steps": steps}

    # Wave 42: "|A|" is the school notation for det(A).
    if "det" in ql or "determinant" in ql or \
            re.search(r"\|\s*A\s*\|", q):
        d = M.det()
        steps = [f"Matrix: {_mstr(M)}"]
        if M.rows == 2 and M.cols == 2:
            (a, b), (c, dd) = M.tolist()
            steps.append(
                f"For a 2x2 matrix, det = a·d - b·c = {a}·{dd} - {b}·{c}")
            steps.append(f"= {fmt(a * dd)} - {fmt(b * c)} = {fmt(d)}")
        else:
            steps.append("Expand along the first row (cofactor "
                         "expansion).")
            steps.append(f"det = {fmt(d)}")
        return {"type": "linear_algebra", "op": "determinant",
                "answer": fmt(d), "value": fmt(d), "steps": steps}

    if "inverse" in ql or "inv(" in ql:
        d = M.det()
        if d == 0:
            return {"type": "linear_algebra", "op": "inverse",
                    "answer": "No inverse exists (determinant is 0).",
                    "steps": [f"det = 0 for {_mstr(M)}, so the matrix "
                              "is singular."]}
        inv = M.inv()
        steps = [f"Matrix: {_mstr(M)}", f"det = {fmt(d)} (non-zero, so "
                 "an inverse exists)"]
        if M.rows == 2 and M.cols == 2:
            (a, b), (c, dd) = M.tolist()
            steps.append(
                f"A^-1 = (1/det)·[[d, -b], [-c, a]] = (1/{fmt(d)})·"
                f"[[{dd}, {-b}], [{-c}, {a}]]")
        steps.append(f"A^-1 = {_mstr(inv)}")
        return {"type": "linear_algebra", "op": "inverse",
                "answer": _mstr(inv), "value": _mstr(inv), "steps": steps}

    if "eigen" in ql:
        if "eigenvector" in ql:
            ev = M.eigenvects()
            parts = []
            steps = [f"Matrix: {_mstr(M)}",
                     "For each eigenvalue λ, solve (A - λI)·v = 0."]
            for val, mult, vecs in ev:
                for v in vecs:
                    vt = v.T if v.rows > 1 else v
                    parts.append(f"λ = {fmt(val)}: v = {_mstr(vt)}")
                    steps.append(f"λ = {fmt(val)} → v = {_mstr(vt)}")
            return {"type": "linear_algebra", "op": "eigenvectors",
                    "answer": "; ".join(parts), "steps": steps}
        ev = M.eigenvals()
        lam = sp.symbols("lambda")
        cp = M.charpoly(lam)
        parts = ", ".join(f"{fmt(v)} (x{m})" if m > 1 else fmt(v)
                          for v, m in ev.items())
        steps = [
            f"Matrix: {_mstr(M)}",
            f"Characteristic polynomial: {fmt(cp.as_expr())} = 0",
            f"Roots (eigenvalues): {parts}",
        ]
        return {"type": "linear_algebra", "op": "eigenvalues",
                "answer": parts,
                "eigenvalues": {str(k): v for k, v in ev.items()},
                "steps": steps}

    if "rank" in ql:
        r = M.rank()
        steps = [
            f"Matrix: {_mstr(M)}",
            "Row-reduce to echelon form and count the non-zero rows "
            "(pivots).",
            f"Rank = {r}",
        ]
        return {"type": "linear_algebra", "op": "rank",
                "answer": str(r), "value": r, "steps": steps}

    if "transpose" in ql:
        T = M.T
        steps = [f"Matrix: {_mstr(M)}",
                 "Swap rows and columns: row i becomes column i.",
                 f"Transpose: {_mstr(T)}"]
        return {"type": "linear_algebra", "op": "transpose",
                "answer": _mstr(T), "steps": steps}

    if "trace" in ql:
        tr = sum(M[i, i] for i in range(min(M.rows, M.cols)))
        diag = " + ".join(fmt(M[i, i]) for i in range(min(M.rows, M.cols)))
        steps = [f"Trace = sum of diagonal entries = {diag} = {fmt(tr)}"]
        return {"type": "linear_algebra", "op": "trace",
                "answer": fmt(tr), "value": fmt(tr), "steps": steps}

    raise ValueError(
        "Could not determine the linear algebra task. Try 'determinant "
        "of [[1,2],[3,4]]', 'inverse of ...', 'eigenvalues of ...', "
        "'rank of ...' or 'A=[[...]], b=[[...]]'."
    )
