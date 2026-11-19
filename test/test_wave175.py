"""Wave 175: matrix equality — native solve + the slow-path fix.

Suraj's live test (19 Nov 2026, 09:25 IST): the classic
Class 12 matrix-equality question got NO answer — the chat
showed the Wave 145 "Server is slow right now" line.  Root
cause (measured): route_intent sends the question to
linear_algebra, whose matrix parser accepts digits only,
so a symbolic-entry matrix raises ValueError; no
failure-only gate owned matrices; the app layer then
walked the whole fallback chain (Live Bank -> salvage ->
Gemini 2x15 s -> Groq 15 s -> OpenRouter 12 s -> verify
leg -> deep-solve), whose combined ceiling is far past
the browser's 45 s abort.

Fix: solver/matrixeq175.py — a strict matrix-equality
schema (equate corresponding entries, solve the linear
system exactly with SymPy, verify by substitution into
every entry) behind a failure-only gate in router.py,
after the Wave 171 block.  Shapes: bracketed [[..]] =
[[..]] (direct or named A = B), the semicolon grid form,
and a COMPLETE flattened paste (exactly 2n^2 entries).

Suraj's actual paste is short one entry (7 of 8) and is
DECLINED, deliberately: the missing entry's position is
unknowable, and different positions give different values
for the same unknowns (missing (2,2) -> x = 6; missing
(1,2) -> x = 14) — a serve would be a guess.  The decline
goes to the normal fallback chain, never a wrong serve.
"""
from solver.matrixeq175 import solve_matrix_equality
from solver.router import solve_question

CLASSIC = ("If [[x-y, 2x+z],[2x-y, 2x+w]] = [[-1, 0],[5, 13]], "
           "find x, y, z and w")
PASTED = ("Question 1: Finding Unknown Values (Matrix Equality) "
          "Find the values of x, y, z, and w from the following "
          "equation: x- y 2x +Z 2x- y -1 0 5 13")
FLAT_FULL = ("Matrix Equality. Find the values of x, y, z, and w "
             "from the following equation: "
             "x- y 2x +Z 2x- y 2x +w -1 0 5 13")


def ans(q):
    out = solve_matrix_equality(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_matrix_equality(q) is None, q


# ------------------------------------------------------------------
# The classic, every accepted shape
# ------------------------------------------------------------------

def test_bracketed_classic_schema():
    out = solve_matrix_equality(CLASSIC)
    assert out["op"] == "matrix_equality"
    assert out["answer"] == "x = 6, y = 7, z = -12, w = 1"
    assert any("corresponding entries" in s for s in out["steps"])


def test_bracketed_classic_via_router():
    out = solve_question(CLASSIC)
    assert out["op"] == "matrix_equality"
    assert out["answer"] == "x = 6, y = 7, z = -12, w = 1"


def test_semicolon_grid_form():
    assert ans("[x-y 2x+z; 2x-y 2x+w] = [-1 0; 5 13], "
               "find x, y, z, w") == "x = 6, y = 7, z = -12, w = 1"


def test_named_a_equals_b_form():
    assert ans("A = [[x+1, 3],[2, y-2]] and B = [[5, 3],[2, 7]]. "
               "If A = B, find x and y") == "x = 4, y = 9"


def test_flattened_complete_form():
    assert ans(FLAT_FULL) == "x = 6, y = 7, z = -12, w = 1"
    out = solve_question(FLAT_FULL)
    assert out["op"] == "matrix_equality"


# ------------------------------------------------------------------
# Variants
# ------------------------------------------------------------------

def test_variant_different_numbers():
    # 2x = 8, y + 3 = 9, z - 1 = 5, 4 = 4
    assert ans("If [[2x, y+3],[z-1, 4]] = [[8, 9],[5, 4]], "
               "find x, y and z") == "x = 4, y = 6, z = 6"


def test_variant_unknown_names_a_b():
    # a + b = 7, a - b = 1
    assert ans("If [[a+b, 2],[3, a-b]] = [[7, 2],[3, 1]], "
               "find a and b") == "a = 4, b = 3"


def test_variant_unknowns_on_both_sides():
    # x + 2 = 7 and y = x - 1
    assert ans("If [[x+2, 1],[3, y]] = [[7, 1],[3, x-1]], "
               "find x and y") == "x = 5, y = 4"


def test_variant_3x3():
    assert ans("If [[x, 2, 3],[4, y+1, 6],[7, 8, z-3]] = "
               "[[1, 2, 3],[4, 9, 6],[7, 8, 5]], "
               "find x, y and z") == "x = 1, y = 8, z = 8"


def test_variant_fractional_values():
    # 2x = 5 -> x = 5/2; y - 1 = 3 -> y = 4
    assert ans("If [[2x, 1],[y-1, 6]] = [[5, 1],[3, 6]], "
               "find x and y") == "x = 5/2, y = 4"


# ------------------------------------------------------------------
# Declines — never a guessed or wrong serve
# ------------------------------------------------------------------

def test_pasted_short_form_declines():
    # Suraj's exact paste: 7 of the 8 entries — the missing
    # entry's position is ambiguous (x = 6 vs x = 14), so
    # the schema declines and the router must NOT serve the
    # classic answer as a guess.
    declines(PASTED)
    out = solve_question(PASTED)
    assert out["op"] != "matrix_equality"
    assert "x = 6" not in str(out.get("answer", ""))


def test_nonlinear_entry_declines():
    declines("If [[x^2, 1],[2, y]] = [[9, 1],[2, 5]], find x and y")
    declines("If [[x*y, 1],[2, 3]] = [[6, 1],[2, 3]], find x and y")


def test_mismatched_sizes_decline():
    declines("If [[x, 1],[2, 3]] = [[1, 2, 3],[4, 5, 6],[7, 8, 9]], "
             "find x")


def test_inconsistent_declines():
    # A constant entry already disagrees (3 vs 4).
    declines("If [[x, 1],[2, 3]] = [[5, 1],[2, 4]], find x")
    # The unknown equations contradict each other (x = 3, x = 4).
    declines("If [[x, x+1],[1, 2]] = [[3, 5],[1, 2]], find x")


def test_underdetermined_declines():
    # One equation, two unknowns — no unique answer exists.
    declines("If [[x+y, 1],[2, 3]] = [[5, 1],[2, 3]], find x and y")


def test_numeric_equality_is_not_ours():
    declines("Is [[1, 2],[3, 4]] = [[1, 2],[3, 4]]?")


def test_matrix_ops_are_not_equality():
    declines("Find A + B where A = [[1, 2],[3, 4]] and "
             "B = [[5, 6],[7, 8]]")
    declines("Find the determinant of [[1, 2],[3, 4]]")
    declines("Multiply [[1,2],[3,4]] by [[5,6],[7,8]]")


# ------------------------------------------------------------------
# Regression pins — existing serves unchanged
# ------------------------------------------------------------------

def test_regression_matrix_ops_unchanged():
    out = solve_question("Find the determinant of [[1,2],[3,4]]")
    assert (out["op"], out["answer"]) == ("determinant", "-2")
    out = solve_question("Add [[1, 2], [3, 4]] and [[5, 6], [7, 8]]")
    assert (out["op"], out["answer"]) == ("add", "[[6, 8], [10, 12]]")
    out = solve_question("Find A - B where A = [[9,10],[11,12]], "
                         "B = [[1,2],[3,4]]")
    assert (out["op"], out["answer"]) == ("subtract", "[[8, 8], [8, 8]]")


def test_regression_algebra_unchanged():
    out = solve_question("Solve 2x + 3 = 7")
    assert (out["op"], out["answer"]) == ("equation", "x = 2")
    out = solve_question("What is 15% of 200?")
    assert out["answer"] == "30"
