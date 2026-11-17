# Wave 113 staging fragment — CBSE Class 12 Mathematics Term 1, 2021-22
# (Set 65/1/4). Transcribed from the GeeksforGeeks solved-paper page for
# Series SSJ/1, Set 4, Q.P. Code 065/1/4 (exam 6 Dec 2021): 50 MCQs of
# 1 mark each (A: Q1-20, B: Q21-40, C: Q41-50 incl. one case study),
# 40 marks, attempt-any-40 pattern.
# Two questions are OMITTED and recorded in the entry note:
# Q21 (its options (a)/(c) render identically in both web sources read —
# a bracket distinction in print could not be recovered) and Q45
# (graph-based; the feasible-region graph cannot be read as text).
# Q5 is printed with the curve x^2/9 + y^2/25 = 1 (the source page drops
# the '=' sign; the keyed answer (0, +/-5) confirms the ellipse).
# Q49 asks the value of x (side of the square plot, in m) for minimum
# cost; the source page misprints it as 'c'.

_CASE_STUDY_12_T1 = (
    "Case Study: In a residential society comprising of 100 houses, there were 60 children "
    "between the ages of 10-15 years. They were inspired by their teachers to start composting "
    "to ensure that biodegradable waste is recycled. For this purpose, instead of each child "
    "doing it for only his/her house, children convinced the Residents welfare association to "
    "do it as a society initiative. For this, they identified a square area in the local park. "
    "Local authorities charged an amount of ₹50 per square metre for space so that there is no "
    "misuse of the space and the Resident welfare association takes it seriously. The "
    "association hired a labourer for digging out 250 m^3 and he charged ₹400 × (depth)^2. "
    "Association will like to have a minimum cost. Based on this information, answer the question."
)

_CBSE12_2022_TERM1 = [
    _q(1, "A", 1, "continuity-and-differentiability", "Differential of log [log (log x^5)] w.r.t. x is (a) 5/[x log(x^5) log(log x^5)] (b) 5/[x log(log x^5)] (c) 5x^4/[log(x^5) log(log x^5)] (d) 5x^4/[log x^5 log(log x^5)]"),
    _q(2, "A", 1, "matrices", "The number of all possible matrices of order 2 × 3 with each entry 1 or 2 is (a) 16 (b) 6 (c) 64 (d) 24"),
    _q(3, "A", 1, "application-of-derivatives", "A function f : R → R is defined as f(x) = x^3 + 1. Then the function has (a) no minimum value (b) no maximum value (c) both maximum and minimum values (d) neither maximum value nor minimum value"),
    _q(4, "A", 1, "continuity-and-differentiability", "If sin y = x cos (a + y), then dx/dy is (a) cos a/cos^2 (a + y) (b) −cos a/cos^2 (a + y) (c) cos a/sin^2 y (d) −cos a/sin^2 y"),
    _q(5, "A", 1, "application-of-derivatives", "The points on the curve x^2/9 + y^2/25 = 1, where the tangent is parallel to the x-axis are (a) (±5, 0) (b) (0, ±5) (c) (0, ±3) (d) (±3, 0)"),
    _q(6, "A", 1, "determinants", "Three points P(2x, x + 3), Q(0, x) and R(x + 3, x + 6) are collinear, then x is equal to (a) 0 (b) 2 (c) 3 (d) 1"),
    _q(7, "A", 1, "inverse-trigonometric-functions", "The principal value of cos^(−1) (1/2) + sin^(−1) (−1/√2) is (a) π/12 (b) π (c) π/3 (d) π/6"),
    _q(8, "A", 1, "continuity-and-differentiability", "If (x^2 + y^2)^2 = xy, then dy/dx is (a) [y + 4x(x^2 + y^2)]/[4y(x^2 + y^2) − x] (b) [y − 4x(x^2 + y^2)]/[x + 4(x^2 + y^2) − x] (c) [y − 4x(x^2 + y^2)]/[4y(x^2 + y^2) − x] (d) [4y(x^2 + y^2) − x]/[y − 4x(x^2 + y^2)]"),
    _q(9, "A", 1, "matrices", "If a matrix A is both symmetric and skew-symmetric, then A is necessarily (a) Diagonal matrix (b) Zero square matrix (c) Square matrix (d) Identity matrix"),
    _q(10, "A", 1, "relations-and-functions", "Let set X = {1, 2, 3} and a relation R is defined in X as: R = {(1, 3), (2, 2), (3, 2)}, then minimum ordered pairs which should be added in relation R to make it reflexive and symmetric are (a) {(1, 1), (2, 3), (1, 2)} (b) {(3, 3), (3, 1), (1, 2)} (c) {(1, 1), (3, 3), (3, 1), (2, 3)} (d) {(1, 1), (3, 3), (3, 1), (1, 2)}"),
    _q(11, "A", 1, "linear-programming", "A Linear Programming Problem is as follows: Minimise z = 2x + y subject to the constraints x ≥ 3, x ≤ 9, y ≥ 0, x − y ≥ 0, x + y ≤ 14. The feasible region has (a) 5 corner points including (0, 0) and (9, 5) (b) 5 corner points including (7, 7) and (3, 3) (c) 5 corner points including (14, 0) and (9, 0) (d) 5 corner points including (3, 6) and (9, 5)"),
    _q(12, "A", 1, "continuity-and-differentiability", "The function f(x) = (e^(3x) − e^(−5x))/x, if x ≠ 0; f(x) = k, if x = 0, is continuous at x = 0 for the value of k as (a) 3 (b) 5 (c) 2 (d) 8"),
    _q(13, "A", 1, "determinants", "If Cij denotes the cofactor of element pij of the matrix P = [[1, −1, 2], [0, 2, −3], [3, 2, 4]], then the value of C31 · C23 is (a) 3 (b) 5 (c) 2 (d) 8"),
    _q(14, "A", 1, "application-of-derivatives", "The function y = x^2 e^(−x) is decreasing in the interval (a) (0, 2) (b) (2, ∞) (c) (−∞, 0) (d) (−∞, 0) ∪ (2, ∞)"),
    _q(15, "A", 1, "relations-and-functions", "If R = {(x, y) : x, y ∈ Z, x^2 + y^2 ≤ 4} is a relation in set Z, then domain of R is (a) {0, 1, 2} (b) {−2, −1, 0, 1, 2} (c) {0, −1, −2} (d) {−1, 0, 1}"),
    _q(16, "A", 1, "determinants", "The system of linear equations 5x + ky = 5, 3x + 3y = 5 will be consistent if (a) k ≠ −3 (b) k = −5 (c) k = 5 (d) k ≠ 5"),
    _q(17, "A", 1, "application-of-derivatives", "The equation of the tangent to the curve y(1 + x^2) = 2 − x, where it crosses the x-axis is (a) x − 5y = 2 (b) 5x − y = 2 (c) x + 5y = 2 (d) 5x + y = 2"),
    _q(18, "A", 1, "matrices", "If [[3c + 6, a − d], [a + d, 2 − 3d]] = [[12, 2], [−8, −4]] are equal, then value of ab − cd is (a) 4 (b) 16 (c) −4 (d) −16"),
    _q(19, "A", 1, "inverse-trigonometric-functions", "The principal value of tan^(−1) (tan 9π/8) is (a) π/8 (b) 3π/8 (c) −π/8 (d) −3π/8"),
    _q(20, "A", 1, "matrices", "For two matrices P = [[3, 4], [−1, 2], [0, 1]] and Q^T = [[−1, 2, 1], [1, 2, 3]], P − Q is (a) [[2, 3], [−3, 0], [0, −3]] (b) [[4, 3], [−3, 0], [−1, −2]] (c) [[4, 3], [0, −3], [−1, −2]] (d) [[2, 3], [0, −3], [0, −3]]"),
    _q(22, "B", 1, "continuity-and-differentiability", "If x = 2 cos θ − cos 2θ and y = 2 sin θ − sin 2θ, then dy/dx is (a) (cos θ + cos 2θ)/(sin θ − sin 2θ) (b) (cos θ − cos 2θ)/(sin 2θ − sin θ) (c) (cos θ − cos 2θ)/(sin θ − sin 2θ) (d) (cos 2θ − cos θ)/(sin 2θ − sin θ)"),
    _q(23, "B", 1, "inverse-trigonometric-functions", "What is the domain of the function cos^(−1) (2x − 3)? (a) [−1, 1] (b) (1, 2) (c) (−1, 1) (d) [1, 2]"),
    _q(24, "B", 1, "matrices", "A matrix A = [aij] 3×3 is defined by aij = 2i + 3j, if i < j; 5, if i = j; 3i − 2j, if i > j. The number of elements in A which are more than 5, is (a) 3 (b) 4 (c) 5 (d) 6"),
    _q(25, "B", 1, "continuity-and-differentiability", "If a function f defined by f(x) = k cos x/(π − 2x), if x ≠ π/2; f(x) = 3, if x = π/2, is continuous at x = π/2, then the value of k is (a) 2 (b) 3 (c) 6 (d) −6"),
    _q(26, "B", 1, "matrices", "For the matrix X = [[0, 1, 1], [1, 0, 1], [1, 1, 0]], (X^2 − X) is (a) 2I (b) 3I (c) I (d) 5I"),
    _q(27, "B", 1, "relations-and-functions", "Let X = {x^2 : x ∈ N} and the function f : N → X is defined by f(x) = x^2, x ∈ N. Then this function is (a) injective only (b) not bijective (c) surjective only (d) bijective"),
    _q(28, "B", 1, "linear-programming", "The corner points of the feasible region for a Linear Programming problem are P(0, 5), Q(1, 5), R(4, 2) and S(12, 0). The minimum value of the objective function Z = 2x + 5y is at the point (a) P (b) Q (c) R (d) S"),
    _q(29, "B", 1, "application-of-derivatives", "The equation of the normal to the curve ay^2 = x^3 at the point (am^2, am^3) is (a) 2y − 3mx + am^3 = 0 (b) 2x + 3my − 3am^4 − am^2 = 0 (c) 2x + 3my + 3am^4 − 2am^2 = 0 (d) 2x + 3my − 3am^4 − 2am^2 = 0"),
    _q(30, "B", 1, "determinants", "If A is a square matrix of order 3 and |A| = −5, then |adj A| is (a) 125 (b) −25 (c) 25 (d) ±25"),
    _q(31, "B", 1, "inverse-trigonometric-functions", "The simplest form of tan^(−1) [(√(1 + x) − √(1 − x))/(√(1 + x) + √(1 − x))] is (a) π/4 − x/2 (b) π/4 + x/2 (c) π/4 − (1/2) cos^(−1) x (d) π/4 + (1/2) cos^(−1) x"),
    _q(32, "B", 1, "determinants", "If for the matrix A = [[α, −2], [−2, α]], |A^3| = 125, then the value of α is (a) ±3 (b) −3 (c) ±1 (d) 1"),
    _q(33, "B", 1, "continuity-and-differentiability", "If y = sin (m sin^(−1) x), then which one of the following equations is true? (a) (1 − x^2) d^2y/dx^2 + x dy/dx + m^2 y = 0 (b) (1 − x^2) d^2y/dx^2 − x dy/dx + m^2 y = 0 (c) (1 + x^2) d^2y/dx^2 − x dy/dx − m^2 y = 0 (d) (1 − x^2) d^2y/dx^2 + x dy/dx − m^2 x = 0"),
    _q(34, "B", 1, "inverse-trigonometric-functions", "The principal value of [tan^(−1) √3 − cot^(−1) (−√3)] is (a) π (b) −π/2 (c) 0 (d) 2√3"),
    _q(35, "B", 1, "application-of-derivatives", "The maximum value of (1/x)^x is (a) e^(1/e) (b) e (c) (1/e)^(1/e) (d) e^e"),
    _q(36, "B", 1, "determinants", "Let matrix X = [[1, −1, 2], [3, 4, −5], [2, −1, 3]]. Then the matrix Y = [mij] = Minor of xij is (a) [[7, −5, −3], [19, 1, −11], [−11, 1, 3]] (b) [[7, −19, −11], [5, −1, −1], [3, 11, 7]] (c) [[7, 19, −11], [−3, 11, 7], [−5, −1, −1]] (d) [[7, 19, −11], [−1, −1, 1], [−3, −11, 7]]"),
    _q(37, "B", 1, "relations-and-functions", "A function f : R → R defined by f(x) = 2 + x^2 is (a) not one-one (b) one-one (c) not onto (d) neither one-one nor onto"),
    _q(38, "B", 1, "linear-programming", "A Linear Programming Problem is as follows: Maximise/Minimise objective function Z = 2x − y + 5 subject to the constraints 3x + 4y ≤ 60, x + 3y ≤ 30, x ≥ 0, y ≥ 0. If the corner points of the feasible region are A(0, 10), B(12, 6), C(20, 0) and O(0, 0), then which of the following is true? (a) Maximum value of Z is 40 (b) Minimum value of Z is −5 (c) Difference of maximum and minimum values of Z is 35 (d) At two corner points, the values of Z are equal"),
    _q(39, "B", 1, "determinants", "If x = −4 is a root of | x, 2, 3 ; 1, x, 1 ; 3, 2, x | = 0, then the sum of the other two roots is (a) 4 (b) −3 (c) 2 (d) 5"),
    _q(40, "B", 1, "application-of-derivatives", "The absolute maximum value of the function f(x) = 4x − (1/2) x^2 in the interval [−2, 9/2] is (a) 8 (b) 9 (c) 6 (d) 10"),
    _q(41, "C", 1, "application-of-derivatives", "In a sphere of radius r, a right circular cone of height h having maximum curved surface area is inscribed. The expression for the square of the curved surface area of the cone is (a) 2π r^2 rh (2rh + h^2) (b) π^2 hr (2rh + h^2) (c) 2π^2 r (2rh^2 − h^3) (d) 2π^2 r^2 (2rh − h^2)"),
    _q(42, "C", 1, "linear-programming", "The corner points of the feasible region determined by a set of constraints (linear inequalities) are P(0, 5), Q(3, 5), R(5, 0) and S(4, 1) and the objective function is Z = ax + 2by where a, b > 0. The condition on a and b such that the maximum of Z occurs at Q and S is (a) a − 5b = 0 (b) a − 3b = 0 (c) a − 2b = 0 (d) a − 8b = 0"),
    _q(43, "C", 1, "application-of-derivatives", "If curve y^2 = 4x and xy = c cut at right angles, then the value of c is (a) 4√2 (b) 8 (c) 2√2 (d) −4√2"),
    _q(44, "C", 1, "matrices", "The inverse of the matrix X = [[2, 0, 0], [0, 3, 0], [0, 0, 4]] is (a) 24 [[1/2, 0, 0], [0, 1/3, 0], [0, 0, 1/4]] (b) (1/24) [[1, 0, 0], [0, 1, 0], [0, 0, 1]] (c) (1/24) [[2, 0, 0], [0, 3, 0], [0, 0, 4]] (d) [[1/2, 0, 0], [0, 1/3, 0], [0, 0, 1/4]]"),
    _q(46, "C", 1, "application-of-derivatives", _CASE_STUDY_12_T1 + " Let side of square plot is x m and its depth is h metres, then cost c for the pit is (a) 50/h + 400h^2 (b) 12500/h + 400h^2 (c) 250/h + h^2 (d) 250/h + 400h^2"),
    _q(47, "C", 1, "application-of-derivatives", _CASE_STUDY_12_T1 + " Value of h (in m) for which dc/dh = 0 is (a) 1.5 (b) 2 (c) 2.5 (d) 3"),
    _q(48, "C", 1, "application-of-derivatives", _CASE_STUDY_12_T1 + " d^2c/dh^2 is given by (a) 25000/h^3 + 800 (b) 500/h^3 + 800 (c) 100/h^3 + 800 (d) 500/h^3 + 2"),
    _q(49, "C", 1, "application-of-derivatives", _CASE_STUDY_12_T1 + " Value of x (in m) for minimum cost is (a) 5 (b) 10√(5/3) (c) 5√5 (d) 10"),
    _q(50, "C", 1, "application-of-derivatives", _CASE_STUDY_12_T1 + " Total minimum cost of digging the pit (in ₹) is (a) 4,100 (b) 7,500 (c) 7,850 (d) 3,220"),
]

_CBSE12_2022_TERM1_ENTRY = {
    "id": "cbse-12-2022-term1",
    "class_num": 12,
    "board": "CBSE",
    "year": 2022,
    "set_label": "Term 1, Set 65/1/4",
    "source_name": "CBSE Class 12 Mathematics Term 1 Question Paper 2021-22, Series SSJ/1, Set 4, Q.P. Code 065/1/4 (exam 6 Dec 2021), GeeksforGeeks solved-paper reproduction",
    "source_url": "https://www.geeksforgeeks.org/maths/cbse-class-12-maths-term-1-2021-answer-key/",
    "max_marks": 40,
    "full_count": {"B": 20, "C": 10},
    "full_marks": {"B": 20, "C": 10},
    "section_titles": {
        "A": "Section A — Multiple Choice Questions (1 mark each; attempt any 16 of 20)",
        "B": "Section B — Multiple Choice Questions (1 mark each; attempt any 16 of 20)",
        "C": "Section C — Case Study / Application Questions (1 mark each; attempt any 8 of 10)",
    },
    "note": "The 2021-22 Term 1 paper: 50 MCQs, 40 marks, 90 minutes; any 40 to be attempted (16+16+8). Two questions are omitted because they could not be read reliably as text: Q21 (options (a) and (c) render identically in both web sources read — a bracket distinction in the printed paper could not be recovered) and Q45 (based on a printed feasible-region graph). Q5's curve is printed x^2/9 + y^2/25 = 1 (the source page drops the '=' sign). The case-study passage (Q46-50) is repeated inside each of those questions so every question is self-contained.",
    "questions": _CBSE12_2022_TERM1,
}
