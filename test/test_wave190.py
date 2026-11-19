"""Wave 190: matrix family completion — form-audit item
B.5 (rows 7-9): system of equations by matrix method,
A'A = I / AA' = I find-the-unknowns in plain dress, the
verify/prove dresses with concrete matrices, the
hence-find-A^-1 chain, and the NCERT matrix word
templates (trust-fund bonds, manufacturer markets).

Audit probe 04, verbatim: "Solve the system of equations
using the matrix method: x + y + z = 6, x - y + z = 2,
2x + y - z = 1" — BEFORE: the primary linear_algebra
solver demanded a raw matrix (op "error": "Provide a
matrix like [[1,2],[3,4]]").  Correct (verified by
elimination and by SymPy independently of this module):
x = 1, y = 2, z = 3.

Every expected answer below was verified independently
(SymPy / hand) before pinning.  Verify dresses are
COMPUTED verdicts: the false-claim cases pin the computed
"not equal / not as stated" serve, never a proof of a
false statement.  The hence chain verifies the premise
and A.A^-1 = I before serving; a false premise declines
at module level.

Controls (must keep current outcomes): Wave 175 matrix
equality, the AB product, the 3x3 determinant, and plain
algebra system solving without the words "matrix method".
"""
from solver.matrix190 import solve_matrix190
from solver.router import solve_question

PROBE04 = ("Solve the system of equations using the "
           "matrix method: x + y + z = 6, x - y + z = 2, "
           "2x + y - z = 1")
TRUST_NCERT = (
    "A trust fund has Rs 30000 that must be invested in "
    "two types of bonds. The first bond pays 5% interest "
    "per year and the second bond pays 7% interest per "
    "year. Using matrix multiplication, determine how to "
    "divide Rs 30000 among the two types of bonds if the "
    "trust fund must obtain an annual total interest of "
    "Rs 1800.")
MANUF_NCERT = (
    "A manufacturer produces three types of products X, "
    "Y and Z which he sells in two markets. Annual sales "
    "are indicated below: Market I: X = 10000, Y = 2000, "
    "Z = 18000 and Market II: X = 6000, Y = 20000, "
    "Z = 8000. If unit sale prices of X, Y and Z are "
    "Rs 2.50, Rs 1.50 and Rs 1.00 respectively, find the "
    "total revenue in each market with the help of "
    "matrix algebra.")


def ans(q):
    out = solve_matrix190(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_matrix190(q) is None, q


# ------------------------------------------------------------------
# (a) System by matrix method — probe 04 + variants
# ------------------------------------------------------------------

def test_probe04_schema():
    out = solve_matrix190(PROBE04)
    assert out["op"] == "w190_matrix_method"
    assert out["answer"] == "x = 1, y = 2, z = 3"
    assert any("|A|" in s for s in out["steps"])
    assert any("A^-1" in s for s in out["steps"])


def test_probe04_via_router():
    out = solve_question(PROBE04)
    assert out["op"] == "w190_matrix_method"
    assert out["answer"] == "x = 1, y = 2, z = 3"


def test_matrix_method_2x2():
    q = ("Solve the system of equations using the matrix "
         "method: 2x + 3y = 7, x - y = 1")
    assert ans(q) == "x = 2, y = 1"
    out = solve_question(q)
    assert out["answer"] == "x = 2, y = 1"


def test_matrix_method_3x3_fractional():
    # Verified independently: det = 14, X = A^-1 B.
    q = ("Solve the system of equations using the matrix "
         "method: x + 2y + z = 8, 2x - y + z = 5, "
         "x + y - 2z = -1")
    assert ans(q) == "x = 15/7, y = 12/7, z = 17/7"
    out = solve_question(q)
    assert out["op"] == "w190_matrix_method"
    assert out["answer"] == "x = 15/7, y = 12/7, z = 17/7"


def test_matrix_method_inconsistent():
    # rank(A) = 1, rank([A|B]) = 2: no solution.
    q = ("Examine the consistency of the system of "
         "equations using the matrix method: "
         "x + y + z = 1, x + y + z = 2, 2x + 2y + 2z = 3")
    out = solve_matrix190(q)
    assert out["op"] == "w190_consistency"
    assert "inconsistent" in out["answer"]
    assert "no solution" in out["answer"].lower()
    out = solve_question(q)
    assert out["op"] == "w190_consistency"


def test_consistency_dress_without_matrix_method_words():
    q = ("Examine the consistency of the system of "
         "equations: x + y + z = 1, x + y + z = 2, "
         "2x + 2y + 2z = 3")
    out = solve_matrix190(q)
    assert out["op"] == "w190_consistency"
    assert "inconsistent" in out["answer"]


def test_matrix_method_infinitely_many():
    q = ("Solve the system of equations using the matrix "
         "method: x + y = 2, 2x + 2y = 4")
    out = solve_matrix190(q)
    assert out["op"] == "w190_consistency"
    assert out["answer"] == \
        "Infinitely many solutions: x = 2 - y"
    out = solve_question(q)
    assert out["op"] == "w190_consistency"
    assert "Infinitely many" in out["answer"]


def test_matrix_method_dependent_consistent_3x3():
    # rank 2 = rank([A|B]) < 3: one free parameter.
    q = ("Solve the system of equations using the matrix "
         "method: x + y + z = 3, 2x + 2y + 2z = 6, "
         "x - y = 0")
    out = solve_matrix190(q)
    assert out["op"] == "w190_consistency"
    assert "Infinitely many" in out["answer"]
    assert "3/2 - z/2" in out["answer"]
    out = solve_question(q)
    assert out["op"] == "w190_consistency"


def test_system_without_matrix_method_declines():
    # Plain algebra territory — the module must not claim
    # a system that was not asked by matrix method /
    # consistency.
    declines("Solve the system of equations: "
             "x + y + z = 6, x - y + z = 2, 2x + y - z = 1")
    declines("Solve the system of equations using the "
             "matrix method: x + y = 3, x - y = 1, "
             "2x + y = 4, x + 2y = 5")


# ------------------------------------------------------------------
# (b) A'A = I / AA' = I find-the-unknowns, plain dress
# ------------------------------------------------------------------

def test_ata_equals_i_find_unknown():
    # A'A = [[x^2 + 9/25, 3x/5 + 12/25], [..., 1]]:
    # off-diagonal 0 and (1,1) entry 1 both give x = -4/5.
    q = ("If A = [[3/5, 4/5], [x, 3/5]], find x such "
         "that A'A = I")
    assert ans(q) == "x = -4/5"
    out = solve_question(q)
    assert out["op"] == "w190_ata_identity"
    assert out["answer"] == "x = -4/5"


def test_aat_equals_i_find_unknown():
    q = ("If A = [[3/5, x], [4/5, 3/5]], find x such "
         "that AA' = I")
    assert ans(q) == "x = -4/5"
    out = solve_question(q)
    assert out["answer"] == "x = -4/5"


def test_ata_two_solutions_both_served():
    # A'A = x^2 I, so x = 1 and x = -1 both verify.
    q = "If A = [[x, 0], [0, x]], find x such that A'A = I"
    assert ans(q) == "x = -1 or x = 1"


def test_ata_no_solution_declines():
    # A'A has (1,1) entry 1 + 4 = 5, never 1: no x works.
    declines("If A = [[1, -2], [2, x]], find x such "
             "that A'A = I")
    out = solve_question("If A = [[1, -2], [2, x]], "
                         "find x such that A'A = I")
    assert out["op"] != "w190_ata_identity"


def test_ata_verify_dress_is_not_find():
    # A pure verify (no unknowns, no "find") stays with
    # the existing handlers — this branch declines.
    declines("Verify that A'A = I for "
             "A = [[3/5, 4/5], [-4/5, 3/5]]")


# ------------------------------------------------------------------
# (c) Verify / prove dresses — computed verdicts
# ------------------------------------------------------------------

def test_verify_transpose_of_product():
    q = ("Verify that (AB)' = B'A' for "
         "A = [[1, 2], [3, 4]] and B = [[2, 0], [1, 3]]")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_transpose_product"
    assert out["answer"] == \
        "(AB)' = B'A' = [[4, 10], [6, 12]] (verified)"
    out = solve_question(q)
    assert out["op"] == "w190_verify_transpose_product"
    assert "[[4, 10], [6, 12]]" in out["answer"]


def test_verify_transpose_false_claim_verdict():
    # (AB)' = [[4, 10], [6, 12]] but A'B' = [[2, 10],
    # [4, 14]]: the computed verdict, not a false proof.
    q = ("Verify that (AB)' = A'B' for "
         "A = [[1, 2], [3, 4]] and B = [[2, 0], [1, 3]]")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_transpose_product"
    assert "not equal" in out["answer"]
    assert "[[2, 10], [4, 14]]" in out["answer"]
    out = solve_question(q)
    assert out["op"] == "w190_verify_transpose_product"
    assert "not equal" in out["answer"]


def test_show_a_plus_at_symmetric():
    q = ("If A = [[1, 2], [3, 4]], show that A + A' is "
         "a symmetric matrix")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_sum_symmetric"
    assert out["answer"] == \
        "A + A' = [[2, 5], [5, 8]], which is symmetric " \
        "(verified)"
    out = solve_question(q)
    assert out["op"] == "w190_verify_sum_symmetric"


def test_show_a_minus_at_skew():
    q = ("If A = [[1, 2], [3, 4]], show that A - A' is "
         "a skew-symmetric matrix")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_diff_skew"
    assert out["answer"] == \
        "A - A' = [[0, -1], [1, 0]], which is " \
        "skew-symmetric (verified)"
    out = solve_question(q)
    assert out["op"] == "w190_verify_diff_skew"


def test_show_a_plus_at_false_claim_verdict():
    # A + A' is symmetric, NOT skew-symmetric: computed
    # verdict, never a false proof.
    q = ("If A = [[1, 2], [3, 4]], show that A + A' is "
         "a skew-symmetric matrix")
    out = solve_matrix190(q)
    assert "is symmetric, not skew-symmetric" in \
        out["answer"]


def test_show_ab_minus_ba_skew_for_symmetric():
    # A, B symmetric (checked); AB - BA = [[0, -4],
    # [4, 0]] by direct computation.
    q = ("If A = [[1, 2], [2, 3]] and B = [[3, 0], "
         "[0, 1]] are symmetric matrices, show that "
         "AB - BA is a skew-symmetric matrix")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_ab_ba_skew"
    assert out["answer"] == \
        "AB - BA = [[0, -4], [4, 0]], which is " \
        "skew-symmetric (verified)"
    out = solve_question(q)
    assert out["op"] == "w190_verify_ab_ba_skew"


def test_ab_minus_ba_false_premise_verdict():
    # A = [[1, 2], [3, 4]] is NOT symmetric: the premise
    # fails on computation, and that is the serve.
    q = ("If A = [[1, 2], [3, 4]] and B = [[3, 0], "
         "[0, 1]] are symmetric matrices, show that "
         "AB - BA is a skew-symmetric matrix")
    out = solve_matrix190(q)
    assert out["op"] == "w190_verify_ab_ba_skew"
    assert "not symmetric" in out["answer"]


# ------------------------------------------------------------------
# (d) Hence-find-A^-1 chains
# ------------------------------------------------------------------

def test_hence_inverse_ncert():
    # NCERT: A = [[3, 1], [-1, 2]] satisfies
    # A^2 - 5A + 7I = O; A^-1 = (5I - A)/7.
    q = ("If A = [[3, 1], [-1, 2]] satisfies "
         "A^2 - 5A + 7I = O, hence find A^-1")
    out = solve_matrix190(q)
    assert out["op"] == "w190_hence_inverse"
    assert out["answer"] == \
        "A^-1 = [[2/7, -1/7], [1/7, 3/7]]"
    out = solve_question(q)
    assert out["op"] == "w190_hence_inverse"
    assert out["answer"] == \
        "A^-1 = [[2/7, -1/7], [1/7, 3/7]]"


def test_hence_inverse_unit_coefficient():
    # A^2 - 4A + I = O (I carries coefficient 1);
    # A^-1 = 4I - A = [[2, -3], [-1, 2]].
    q = ("If A = [[2, 3], [1, 2]] and A^2 - 4A + I = O, "
         "hence find A^-1")
    assert ans(q) == "A^-1 = [[2, -3], [-1, 2]]"
    out = solve_question(q)
    assert out["answer"] == "A^-1 = [[2, -3], [-1, 2]]"


def test_hence_inverse_false_premise_declines():
    # [[1, 2], [3, 4]] gives A^2 - 5A + 7I = 9I, not O:
    # the premise fails, so no inverse is derived from it.
    declines("If A = [[1, 2], [3, 4]] satisfies "
             "A^2 - 5A + 7I = O, hence find A^-1")
    declines("Find A^-1 for A = [[2, 3], [1, 2]]")


# ------------------------------------------------------------------
# (e) Matrix word problems — NCERT templates, numbers vary
# ------------------------------------------------------------------

def test_trust_fund_ncert():
    # x + y = 30000, 0.05x + 0.07y = 1800 -> 15000 each.
    out = solve_matrix190(TRUST_NCERT)
    assert out["op"] == "w190_trust_fund"
    assert out["answer"] == \
        "Rs 15000 in the first bond and Rs 15000 in " \
        "the second bond"
    out = solve_question(TRUST_NCERT)
    assert out["op"] == "w190_trust_fund"


def test_trust_fund_changed_numbers():
    # x + y = 50000, 0.06x + 0.08y = 3400
    # -> x = 30000, y = 20000 (verified independently).
    q = ("A trust fund has Rs 50000 to invest in two "
         "types of bonds. The first bond pays 6% "
         "interest per year and the second bond pays 8% "
         "interest per year. Using matrix "
         "multiplication, determine how to divide "
         "Rs 50000 among the two types of bonds if the "
         "trust fund must obtain an annual total "
         "interest of Rs 3400.")
    assert ans(q) == \
        "Rs 30000 in the first bond and Rs 20000 in " \
        "the second bond"


def test_trust_fund_impossible_target_declines():
    # Target interest 2500 exceeds the 7% maximum (2100):
    # the formal solution invests a negative amount.
    declines(TRUST_NCERT.replace("Rs 1800", "Rs 2500"))


def test_manufacturer_revenue_ncert():
    # [10000 2000 18000; 6000 20000 8000] x [2.5 1.5 1]^T
    # = [46000, 53000] (verified independently).
    out = solve_matrix190(MANUF_NCERT)
    assert out["op"] == "w190_market_revenue"
    assert out["answer"] == \
        "Revenue: Market I = Rs 46000, Market II = " \
        "Rs 53000"
    out = solve_question(MANUF_NCERT)
    assert out["op"] == "w190_market_revenue"


def test_manufacturer_revenue_and_profit_ncert():
    q = MANUF_NCERT + (
        " If the unit cost prices of X, Y and Z are "
        "Rs 2.00, Rs 1.00 and Rs 0.50 respectively, "
        "find the gross profit in each market.")
    out = solve_matrix190(q)
    assert "Revenue: Market I = Rs 46000" in \
        out["answer"]
    assert "Profit: Market I = Rs 15000, Market II = " \
        "Rs 17000" in out["answer"]


def test_manufacturer_changed_numbers():
    # Revenue [110000, 100000]; profit [25000, 24000]
    # (verified independently).
    q = ("A manufacturer produces two types of "
         "products X and Y which he sells in two "
         "markets. Annual sales are indicated below: "
         "Market I: X = 5000, Y = 3000 and Market II: "
         "X = 2000, Y = 4000. If unit sale prices of X "
         "and Y are Rs 10 and Rs 20 respectively, find "
         "the total revenue in each market with the "
         "help of matrix algebra. If the unit cost "
         "prices of X and Y are Rs 8 and Rs 15 "
         "respectively, find the gross profit in each "
         "market.")
    out = solve_matrix190(q)
    assert out["answer"] == \
        "Revenue: Market I = Rs 110000, Market II = " \
        "Rs 100000; Profit: Market I = Rs 25000, " \
        "Market II = Rs 24000"


def test_manufacturer_incomplete_narrative_declines():
    # Only one market's sales: the template does not
    # match, so the module declines rather than guess.
    declines("A manufacturer produces products X and Y "
             "which he sells in two markets. Annual "
             "sales: Market I: X = 5000, Y = 3000. If "
             "unit sale prices of X and Y are Rs 10 and "
             "Rs 20 respectively, find the total revenue "
             "in each market with the help of matrix "
             "algebra.")


# ------------------------------------------------------------------
# Controls — existing serves unchanged
# ------------------------------------------------------------------

def test_control_matrix_equality_wave175():
    out = solve_question(
        "If [[x-y, 2x+z],[2x-y, 2x+w]] = "
        "[[-1, 0],[5, 13]], find x, y, z and w")
    assert out["op"] == "matrix_equality"
    assert out["answer"] == "x = 6, y = 7, z = -12, w = 1"


def test_control_matrix_product():
    out = solve_question(
        "If A = [[1, 2], [3, 4]] and B = [[2, 0], "
        "[1, 3]], find AB")
    assert out["op"] == "multiply"
    assert out["answer"] == "[[4, 6], [10, 12]]"


def test_control_determinant_3x3():
    out = solve_question(
        "Find the determinant of "
        "[[1,2,3],[4,5,6],[7,8,10]]")
    assert out["op"] == "determinant"
    assert out["answer"] == "-3"


def test_control_plain_algebra_system():
    out = solve_question("Solve x + y = 5, x - y = 1")
    assert out["op"] == "system"
    assert out["answer"] == "x = 3, y = 2"


def test_control_plain_matrix_asks_not_claimed():
    declines("Find the transpose of [[1, 2], [3, 4]]")
    declines("Find the determinant of [[1, 2], [3, 4]]")
    declines("Multiply [[1,2],[3,4]] by [[5,6],[7,8]]")
