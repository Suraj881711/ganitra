"""Wave 42 (15 Nov 2026): matrices & determinants basics
(Class 12) — the named-op forms NCERT actually uses.

Already working (controls below): determinant 2x2/3x3,
keyword add/multiply, transpose, inverse. Broken before
this wave (probes):
- "find A - B" returned A + B (the operator hunt missed
  the named form and defaulted to add);
- "find AB" fell to a guide fallback (no operator
  character between the matrices);
- "Subtract [[5,6],[7,8]] from [[9,10],[11,12]]" returned
  [[-4,-4],[-4,-4]] — text order instead of Y - X;
- "Find 2A if A = [[...]]" (scalar multiple) fell back;
- "Find |A|" (school determinant notation) fell back.
"""
from api import _solve_friendly


def _answer(question):
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


def _matrix(question, expected):
    res = _answer(question)
    assert res["answer"] == expected, (
        f"{question!r} -> {res['answer']!r}, "
        f"expected {expected!r}")


A = "A = [[1, 2], [3, 4]]"
B = "B = [[5, 6], [7, 8]]"


# --- Named two-matrix ops ------------------------------------
def test_find_a_minus_b():
    _matrix(f"If {A} and {B}, find A - B.",
            "[[-4, -4], [-4, -4]]")


def test_find_b_minus_a():
    _matrix(f"If {A} and {B}, find B - A.",
            "[[4, 4], [4, 4]]")


def test_find_ab_product():
    _matrix(f"If {A} and {B}, find AB.",
            "[[19, 22], [43, 50]]")


def test_find_ba_product():
    _matrix(f"If {A} and {B}, find BA.",
            "[[23, 34], [31, 46]]")


def test_subtract_from_order():
    _matrix("Subtract [[5, 6], [7, 8]] from "
            "[[9, 10], [11, 12]]", "[[4, 4], [4, 4]]")


# --- Scalar multiple ------------------------------------------
def test_scalar_multiple_2a():
    _matrix("Find 2A if A = [[1, 2], [3, 4]].",
            "[[2, 4], [6, 8]]")


def test_scalar_multiple_3a():
    _matrix("Find 3A if A = [[2, 0], [1, 5]].",
            "[[6, 0], [3, 15]]")


# --- Determinant notation |A| ---------------------------------
def test_determinant_pipe_notation():
    res = _answer("Find |A| if A = [[2, 3], [1, 4]].")
    assert res["answer"] == "5"


# --- Controls: previously exact forms stay exact --------------
def test_control_determinant_2x2():
    res = _answer("Find the determinant of the matrix "
                  "[[2, 3], [1, 4]].")
    assert res["answer"] == "5"


def test_control_determinant_3x3():
    res = _answer("Find the determinant of the matrix "
                  "[[1, 2, 3], [4, 5, 6], [7, 8, 10]].")
    assert res["answer"] == "-3"


def test_control_find_a_plus_b():
    _matrix(f"If {A} and {B}, find A + B.",
            "[[6, 8], [10, 12]]")


def test_control_keyword_multiply():
    _matrix("Multiply the matrices [[1, 2], [3, 4]] and "
            "[[5, 6], [7, 8]].", "[[19, 22], [43, 50]]")


def test_control_transpose():
    _matrix("Find the transpose of the matrix "
            "[[1, 2, 3], [4, 5, 6]].",
            "[[1, 4], [2, 5], [3, 6]]")


def test_control_inverse():
    _matrix("Find the inverse of [[1, 2], [3, 4]].",
            "[[-2, 1], [3/2, -1/2]]")


def test_control_add_matrices_keyword():
    _matrix("Add the matrices [[1, 2], [3, 4]] and "
            "[[5, 6], [7, 8]].", "[[6, 8], [10, 12]]")
