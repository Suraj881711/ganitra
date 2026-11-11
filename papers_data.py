"""Previous Papers library + pattern analysis + practice-paper
generator (Wave 16).

Suraj's idea (10 Nov 2026): keep the real previous years' board
papers inside Ganitra, analyse them chapter-wise, and let Ganitra
build its own practice paper from that analysis so students can
practise in the exact board pattern.

HONESTY CONTRACT (read before editing):
- Every entry in PAPERS was fetched in full text from the public
  source named in the entry (source_name + source_url) and its
  questions were transcribed from that text. NOTHING here is
  invented: a question is either a real board-paper question from
  the cited source, or it does not belong in this file.
- Where the source text was illegible or figure-only (a couple of
  questions per paper at most), the question was OMITTED and the
  omission is recorded in the paper's "note" — see each entry.
  Case-study questions whose sub-parts live in a diagram are
  summarised and say so.
- The practice-paper generator (generate_practice_paper) reuses
  real questions from this library where it can and fills the
  remaining slots with fresh template questions. Generated
  questions are ALWAYS flagged (source == "generated") and the
  pages label them "practice question" — they are never presented
  as real board questions.

Chapter tags use the NCERT chapter slugs from board_data.py for
the paper's class, so Board Mode, the analysis and the generator
all speak the same chapter names.
"""
import random

from board_data import get_chapter, get_chapters

# The current CBSE 80-mark structure, shared by Class 10 and
# Class 12 Mathematics: section -> (question count, marks each).
PAPER_STRUCTURE = {
    "A": (20, 1),   # 18 MCQ + 2 assertion-reason
    "B": (5, 2),    # very short answer
    "C": (6, 3),    # short answer
    "D": (4, 5),    # long answer
    "E": (3, 4),    # case-study based
}
TOTAL_MARKS = sum(count * marks for count, marks
                  in PAPER_STRUCTURE.values())  # 80
SECTION_TITLES = {
    "A": "Section A — MCQ / Assertion-Reason (1 mark each)",
    "B": "Section B — Very Short Answer (2 marks each)",
    "C": "Section C — Short Answer (3 marks each)",
    "D": "Section D — Long Answer (5 marks each)",
    "E": "Section E — Case Study (4 marks each)",
}


def _q(number, section, marks, chapter, text):
    return {"number": number, "section": section, "marks": marks,
            "chapter": chapter, "text": text}


# ---------------------------------------------------------------------------
# CBSE Class 12 Mathematics 2024 — Q.P. Code 65/1/1, Series PQ1RS/1, Set 1.
# Full text: AglaSem Docs (see source_url in the entry below).
# All 38 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_CBSE12_2024 = [
    _q(1, "A", 1, "relations-and-functions",
       "A function f : R+ → R (where R+ is the set of all "
       "non-negative real numbers) defined by f(x) = 4x + 3 is: "
       "(A) one-one but not onto (B) onto but not one-one "
       "(C) both one-one and onto (D) neither one-one nor onto"),
    _q(2, "A", 1, "matrices",
       "If a matrix has 36 elements, the number of possible orders "
       "it can have, is: (A) 13 (B) 3 (C) 5 (D) 9"),
    _q(3, "A", 1, "continuity-and-differentiability",
       "Which of the following statements is true for the function "
       "f(x) = {x² + 3, x ≠ 0; 1, x = 0}? (A) f(x) is continuous "
       "and differentiable for all x ∈ R (B) f(x) is continuous "
       "for all x ∈ R (C) f(x) is continuous and differentiable "
       "for all x ∈ R − {0} (D) f(x) is discontinuous at "
       "infinitely many points"),
    _q(4, "A", 1, "application-of-derivatives",
       "Let f(x) be a continuous function on [a, b] and "
       "differentiable on (a, b). Then, this function f(x) is "
       "strictly increasing in (a, b) if (A) f′(x) < 0 for all "
       "x ∈ (a, b) (B) f′(x) > 0 for all x ∈ (a, b) (C) f′(x) = 0 "
       "for all x ∈ (a, b) (D) f(x) > 0 for all x ∈ (a, b)"),
    _q(5, "A", 1, "determinants",
       "If [[x + y, 2], [5, xy]] = [[6, 2], [5, 8]], then the "
       "value of (24/x + 24/y) is: (A) 7 (B) 6 (C) 8 (D) 18"),
    _q(6, "A", 1, "integrals",
       "∫(a to b) f(x) dx is equal to: (A) ∫(a to b) f(a − x) dx "
       "(B) ∫(a to b) f(a + b − x) dx (C) ∫(a to b) f(x − (a + b)) "
       "dx (D) ∫(a to b) f((a − x) + (b − x)) dx"),
    _q(7, "A", 1, "vector-algebra",
       "Let θ be the angle between two unit vectors â and b̂ such "
       "that sin θ = 3/5. Then â · b̂ is equal to: (A) ±3/5 "
       "(B) ±3/4 (C) ±4/5 (D) ±4/3"),
    _q(8, "A", 1, "differential-equations",
       "The integrating factor of the differential equation "
       "(1 − x²) dy/dx + xy = ax, −1 < x < 1, is: (A) 1/(x² − 1) "
       "(B) 1/√(x² − 1) (C) 1/(1 − x²) (D) 1/√(1 − x²)"),
    _q(9, "A", 1, "three-dimensional-geometry",
       "If the direction cosines of a line are k/3, k/3, k/3, "
       "then the value of k is: (A) ±1 (B) ±√3 (C) ±3 (D) ±1/3"),
    _q(10, "A", 1, "linear-programming",
       "A linear programming problem deals with the optimization "
       "of a/an: (A) logarithmic function (B) linear function "
       "(C) quadratic function (D) exponential function"),
    _q(11, "A", 1, "probability",
       "If P(A|B) = P(A′|B), then which of the following "
       "statements is true? (A) P(A) = P(A′) (B) P(A) = 2P(B) "
       "(C) P(A ∩ B) = (1/2) P(B) (D) P(A ∩ B) = 2P(B)"),
    _q(12, "A", 1, "determinants",
       "The determinant | x + 1, x − 1 ; x² + x + 1, x² − x + 1 | "
       "is equal to: (A) 2x³ (B) 2 (C) 0 (D) 2x³ − 2"),
    _q(13, "A", 1, "continuity-and-differentiability",
       "The derivative of sin(x²) w.r.t. x, at x = √π is: "
       "(A) 1 (B) −1 (C) −2√π (D) 2√π"),
    _q(14, "A", 1, "differential-equations",
       "The order and degree of the differential equation "
       "(1 + (dy/dx)²)^(3/2) = d²y/dx² respectively are: "
       "(A) 1, 2 (B) 2, 3 (C) 2, 1 (D) 2, 6"),
    _q(15, "A", 1, "vector-algebra",
       "The vector with terminal point A(2, −3, 5) and initial "
       "point B(3, −4, 7) is: (A) î − ĵ + 2k̂ (B) î + ĵ + 2k̂ "
       "(C) −î − ĵ − 2k̂ (D) −î + ĵ − 2k̂"),
    _q(16, "A", 1, "three-dimensional-geometry",
       "The distance of point P(a, b, c) from y-axis is: "
       "(A) b (B) b² (C) √(a² + c²) (D) a² + c²"),
    _q(17, "A", 1, "linear-programming",
       "The number of corner points of the feasible region "
       "determined by constraints x ≥ 0, y ≥ 0, x + y ≥ 4 is: "
       "(A) 0 (B) 1 (C) 2 (D) 3"),
    _q(18, "A", 1, "matrices",
       "If A and B are two non-zero square matrices of same order "
       "such that (A + B)² = A² + B², then: (A) AB = O (B) AB = "
       "−BA (C) BA = O (D) AB = BA"),
    _q(19, "A", 1, "determinants",
       "Assertion (A): For matrix A = [[1, cos θ, 1], "
       "[−cos θ, 1, cos θ], [−1, −cos θ, 1]], where θ ∈ [0, 2π], "
       "|A| ∈ [2, 4]. Reason (R): cos θ ∈ [−1, 1], for all "
       "θ ∈ [0, 2π]. (Assertion-Reason question)"),
    _q(20, "A", 1, "three-dimensional-geometry",
       "Assertion (A): A line in space cannot be drawn "
       "perpendicular to x, y and z axes simultaneously. "
       "Reason (R): For any line making angles α, β, γ with the "
       "positive directions of x, y and z axes respectively, "
       "cos²α + cos²β + cos²γ = 1. (Assertion-Reason question)"),
    _q(21, "B", 2, "continuity-and-differentiability",
       "(a) Check whether the function f(x) = x²|x| is "
       "differentiable at x = 0 or not. OR (b) If y = √tan x, "
       "prove that dy/dx = (1 + y⁴)/(4y)."),
    _q(22, "B", 2, "application-of-derivatives",
       "Show that the function f(x) = 4x³ − 18x² + 27x − 7 has "
       "neither maxima nor minima."),
    _q(23, "B", 2, "integrals",
       "(a) Find: ∫ x√(1 + 2x) dx. OR (b) Evaluate: ∫(0 to π/2) "
       "⁴√(sin x) / (⁴√(sin x) + ⁴√(cos x)) dx."),
    _q(24, "B", 2, "vector-algebra",
       "If a and b are two non-zero vectors such that (a + b) is "
       "perpendicular to a and (2a + b) is perpendicular to b, "
       "then prove that |b| = 2|a|."),
    _q(25, "B", 2, "vector-algebra",
       "In the given figure, ABCD is a parallelogram. If "
       "AB = 2î − 4ĵ + 5k̂ and DB = 3î − 6ĵ + 2k̂, then find AD "
       "and hence find the area of parallelogram ABCD."),
    _q(26, "C", 3, "relations-and-functions",
       "(a) A relation R on set A = {1, 2, 3, 4, 5} is defined as "
       "R = {(x, y) : |x² − y²| < 8}. Check whether the relation "
       "R is reflexive, symmetric and transitive. OR (b) A "
       "function f is defined from R → R as f(x) = ax + b, such "
       "that f(1) = 1 and f(2) = 3. Find function f(x). Hence, "
       "check whether function f(x) is one-one and onto or not."),
    _q(27, "C", 3, "continuity-and-differentiability",
       "(a) If √(1 − x²) + √(1 − y²) = a(x − y), prove that "
       "dy/dx = √(1 − y²)/√(1 − x²). OR (b) If y = (tan x)^x, "
       "then find dy/dx."),
    _q(28, "C", 3, "integrals",
       "(a) Find: ∫ x²/((x² + 4)(x² + 9)) dx. OR (b) Evaluate: "
       "∫(1 to 3) (|x − 1| + |x − 2| + |x − 3|) dx."),
    _q(29, "C", 3, "differential-equations",
       "Find the particular solution of the differential "
       "equation x² dy/dx − xy = x² cos²(y/(2x)), given that "
       "when x = 1, y = π/2."),
    _q(30, "C", 3, "linear-programming",
       "Solve the following linear programming problem "
       "graphically: Maximise z = 500x + 300y, subject to "
       "constraints x + 2y ≤ 12, 2x + y ≤ 12, 4x + 5y ≥ 20, "
       "x ≥ 0, y ≥ 0."),
    _q(31, "C", 3, "probability",
       "E and F are two independent events such that P(E′) = 0.6 "
       "and P(E ∪ F) = 0.6. Find P(F) and P(E′ ∩ F′)."),
    _q(32, "D", 5, "matrices",
       "(a) If A = [[1, −2, 0], [2, −1, −1], [0, −2, 1]], find "
       "A⁻¹ and use it to solve the following system of "
       "equations: x − 2y = 10, 2x − y − z = 8, −2y + z = 7. "
       "OR (b) If A = [[−1, a, 2], [1, 2, x], [3, 1, 1]] and "
       "A⁻¹ = [[1, −1, 1], [−8, 7, −5], [b, y, 3]], find the "
       "value of (a + x) − (b + y)."),
    _q(33, "D", 5, "integrals",
       "(a) Evaluate: ∫(0 to π) (4 sin x + cos x)/(9 + 16 sin 2x) "
       "dx. OR (b) Evaluate: ∫(0 to π/2) sin 2x · tan⁻¹(sin x) dx."),
    _q(34, "D", 5, "application-of-integrals",
       "Using integration, find the area of the ellipse "
       "x²/16 + y²/4 = 1, included between the lines x = −2 "
       "and x = 2."),
    _q(35, "D", 5, "three-dimensional-geometry",
       "The image of point P(x, y, z) with respect to line "
       "(x/1) = (y − 1)/2 = (z − 2)/3 is P′(1, 0, 7). Find the "
       "coordinates of point P."),
    _q(36, "E", 4, "application-of-derivatives",
       "Case study: The traffic police has installed an Over "
       "Speed Violation Detection (OSVD) system in a city; the "
       "cameras can capture a speeding vehicle from 300 m and "
       "work in the dark. A camera is installed on a pole at the "
       "height of 5 m. It detects a car travelling away from the "
       "pole at the speed of 20 m/s. At any point, x m away from "
       "the base of the pole, the angle of elevation of the "
       "speed camera from the car C is θ. (i) Express θ in terms "
       "of the height of the camera and x. (ii) Find dθ/dx. "
       "(iii)(a) Find the rate of change of the angle of "
       "elevation w.r.t. time when the car is 50 m away from the "
       "pole. OR (iii)(b) If the rate of change of the angle of "
       "elevation w.r.t. time of another car at 50 m from the "
       "pole is 3/101 rad/s, find the speed of the car."),
    _q(37, "E", 4, "probability",
       "Case study: Air turbulence has increased around the "
       "world due to climate change. Assume an airplane observes "
       "severe, moderate or light turbulence with equal "
       "probabilities. The chances of an airplane reaching late "
       "to the destination are 55%, 37% and 17% due to severe, "
       "moderate and light turbulence respectively. (i) Find the "
       "probability that an airplane reached its destination "
       "late. (ii) If the airplane reached its destination late, "
       "find the probability that it was due to moderate "
       "turbulence."),
    _q(38, "E", 4, "inverse-trigonometric-functions",
       "Case study: If a function f : X → Y defined as f(x) = y "
       "is one-one and onto, we can define a unique function "
       "g : Y → X such that g(y) = x; g is called the inverse of "
       "f. The sine function (R → R) is neither one-one nor "
       "onto; let the sine function be defined from set A to "
       "[−1, 1] such that its inverse sin⁻¹x exists, i.e. "
       "sin⁻¹x is defined from [−1, 1] to A. (i) If A is an "
       "interval other than the principal value branch, give an "
       "example of one such interval. (ii) If sin⁻¹(x) is "
       "defined from [−1, 1] to its principal value branch, find "
       "sin⁻¹(−1/2) − sin⁻¹(1). (iii)(a) Draw the graph of "
       "sin⁻¹x from [−1, 1] to its principal value branch. OR "
       "(iii)(b) Find the domain and range of "
       "f(x) = 2 sin⁻¹(1 − x)."),
]


# ---------------------------------------------------------------------------
# CBSE Class 12 Mathematics 2023 — Q.P. Code 65/1/1, Series EF1GH/1, Set 1.
# Full text: AglaSem Docs (see source_url in the entry below).
# Questions 13 and 15 are OMITTED: in the source text their defining
# expressions are illegible (symbols lost), so they are not guessed at.
# ---------------------------------------------------------------------------
_CBSE12_2023 = [
    _q(1, "A", 1, "matrices",
       "If for a square matrix A, A² − 3A + I = O and "
       "A⁻¹ = xA + yI, then the value of x + y is: (a) −2 (b) 2 "
       "(c) −3 (d) 3"),
    _q(2, "A", 1, "determinants",
       "If |A| = 2, where A is a 2 × 2 matrix, then |4A⁻¹| "
       "equals: (a) 4 (b) 2 (c) 8 (d) 1/32"),
    _q(3, "A", 1, "determinants",
       "Let A be a 3 × 3 matrix such that |adj A| = 64. Then |A| "
       "is equal to: (a) 8 only (b) −8 only (c) 64 (d) 8 or −8"),
    _q(4, "A", 1, "matrices",
       "If A = [[3, 4], [5, 2]] and 2A + B is a null matrix, "
       "then B is equal to: (options as printed in the paper)"),
    _q(5, "A", 1, "integrals",
       "If d/dx (f(x)) = log x, then f(x) equals: (a) 1/x + C "
       "(b) x(log x − 1) + C (c) x(log x + x) + C (d) −1/x + C"),
    _q(6, "A", 1, "integrals",
       "∫(0 to π/6) sec²(x − π/6) dx is equal to: (a) −1/√3 "
       "(b) 1/√3 (c) √3 (d) −√3"),
    _q(7, "A", 1, "differential-equations",
       "The sum of the order and the degree of the differential "
       "equation (d²y/dx²)³ + (dy/dx) + sin y = 0 is: "
       "(a) 5 (b) 2 (c) 3 (d) 4"),
    _q(8, "A", 1, "vector-algebra",
       "The value of p for which the vectors 2î + pĵ + k̂ and "
       "4î − 6ĵ + 26k̂ are perpendicular to each other, is: "
       "(a) 3 (b) −3 (c) 17/3 (d) −17/3"),
    _q(9, "A", 1, "vector-algebra",
       "The value of (î − ĵ) · ĵ + (ĵ − î) · k̂ is: (a) 2 (b) 0 "
       "(c) −1 (d) 1"),
    _q(10, "A", 1, "vector-algebra",
       "If a + b = î and a = 2î − 2ĵ + 2k̂, then |b| equals: "
       "(a) √14 (b) 3 (c) √12 (d) √17"),
    _q(11, "A", 1, "three-dimensional-geometry",
       "Direction cosines of the line (x − 1)/2 = (1 − y)/3 = "
       "(2z − 1)/12 are: (a) 2/7, 3/7, 6/7 (b) 2/√157, 3/√157, "
       "12/√157 (c) 2/7, −3/7, 6/7 (d) 2/7, 3/7, 6/7"),
    _q(12, "A", 1, "probability",
       "If P(A/B) = 0.3, P(A) = 0.4 and P(B) = 0.8, then "
       "P(B/A) is equal to: (a) 0.6 (b) 0.3 (c) 0.06 (d) 0.4"),
    _q(14, "A", 1, "matrices",
       "If A = [[0, −1], [1, 0]] and (3I + 4A)(3I − 4A) = x²I, "
       "then the value(s) of x is/are: (a) 7 (b) 0 (c) 5 (d) 25"),
    _q(16, "A", 1, "application-of-derivatives",
       "If f(x) = a(x − cos x) is strictly decreasing in: "
       "(a) {0} (b) (0, π) (c) (−π, 0) (d) (−π, π)"),
    _q(17, "A", 1, "linear-programming",
       "The corner points of the feasible region in the "
       "graphical representation of a linear programming "
       "problem are (2, 72), (15, 20) and (40, 15). If "
       "z = 18x + 9y be the objective function, then: (a) z is "
       "maximum at (2, 72), minimum at (15, 20) (b) z is maximum "
       "at (15, 20), minimum at (40, 15) (c) z is maximum at "
       "(40, 15), minimum at (15, 20) (d) z is maximum at "
       "(40, 15), minimum at (2, 72)"),
    _q(18, "A", 1, "linear-programming",
       "The number of corner points of the feasible region "
       "determined by the constraints x − y ≥ 0, 2y ≤ x + 2, "
       "x ≥ 0, y ≥ 0 is: (a) 2 (b) 3 (c) 4 (d) 5"),
    _q(19, "A", 1, "inverse-trigonometric-functions",
       "Assertion (A): The range of the function "
       "f(x) = 2 sin⁻¹x + 3π/2, where x ∈ [−1/2, 1/2], is "
       "[5π/2, ... ] as printed in the paper. Reason (R): The "
       "range of the principal value branch of sin⁻¹(x) is "
       "[0, π]. (Assertion-Reason question; the printed range "
       "in the assertion is partly illegible in the source "
       "text.)"),
    _q(20, "A", 1, "three-dimensional-geometry",
       "Assertion (A): Equation of a line passing through the "
       "points (1, 2, 3) and (3, −1, 3) is (x − 3)/2 = "
       "(y − 1)/(−3) = (z − 3)/0. Reason (R): Equation of a "
       "line passing through points (x1, y1, z1), (x2, y2, z2) "
       "is given by (x − x1)/(x2 − x1) = (y − y1)/(y2 − y1) = "
       "(z − z1)/(z2 − z1). (Assertion-Reason question)"),
    _q(21, "B", 2, "relations-and-functions",
       "(a) A function f : A → B defined as f(x) = 2x is both "
       "one-one and onto. If A = {1, 2, 3, 4}, then find the "
       "set B. OR (b) Evaluate: sin⁻¹(sin 3π/4) + "
       "cos⁻¹(cos 3π/4) + tan⁻¹(1)."),
    _q(22, "B", 2, "vector-algebra",
       "Find all the vectors of magnitude 3√3 which are "
       "collinear to vector î + ĵ + k̂."),
    _q(23, "B", 2, "vector-algebra",
       "(a) Position vectors of the points A, B and C are "
       "a, b and c respectively. If AC = (5/4) AB, express c in "
       "terms of a and b. OR (b) Check whether the lines given "
       "by equations x = 2λ + 2, y = 7λ + 1, z = 3λ − 3 and "
       "x = −2μ, y = 2μ + 8, z = 4μ + 5 are perpendicular to "
       "each other or not."),
    _q(24, "B", 2, "continuity-and-differentiability",
       "If y = (x + √(x² − 1))², then show that "
       "(x² − 1)(dy/dx)² = 4y²."),
    _q(25, "B", 2, "application-of-derivatives",
       "Show that the function f(x) = (16 sin x)/(4 + cos x) − x "
       "is strictly decreasing in (π/2, π)."),
    _q(26, "C", 3, "integrals",
       "Evaluate: ∫(0 to π/2) [log(sin x) − log(2 cos x)] dx."),
    _q(27, "C", 3, "integrals",
       "Find: ∫ 1/(x(x − 1)(x − 2)) dx."),
    _q(28, "C", 3, "differential-equations",
       "(a) Find the particular solution of the differential "
       "equation dy/dx + sec²x · y = tan x · sec²x, given that "
       "y(0) = 0. OR (b) Solve the differential equation given "
       "by x dy − y dx − √(x² − y²) dx = 0."),
    _q(29, "C", 3, "linear-programming",
       "Solve graphically the following linear programming "
       "problem: Maximise z = 6x + 3y, subject to the "
       "constraints 4x + y ≤ 80, 3x + 2y ≤ 150, x + 5y ≤ 115, "
       "x ≥ 0, y ≥ 0."),
    _q(30, "C", 3, "probability",
       "(a) The probability distribution of a random variable X "
       "is given below: X = 1, 2, 3 with P(X) = k/2, k/3, k/6. "
       "(i) Find the value of k. (ii) Find P(1 < X < 3). "
       "(iii) Find E(X), the mean of X. OR (b) A and B are "
       "independent events such that P(A ∩ B) = 1/4 and "
       "P(A′ ∩ B′) = 1/6. Find P(A) and P(B)."),
    _q(31, "C", 3, "integrals",
       "(a) Evaluate: ∫(0 to π/2) e^x sin x dx. OR (b) Find: "
       "∫ 1/(cos(x − a) cos(x − b)) dx."),
    _q(32, "D", 5, "relations-and-functions",
       "A relation R is defined on a set of real numbers as "
       "R = {(x, y) : x · y is an irrational number}. Check "
       "whether R is reflexive, symmetric and transitive or not."),
    _q(33, "D", 5, "matrices",
       "(a) If A = [[1, 2, 2], [3, 1, 1], [1, 3, 0]] and "
       "B = [[1, 15, 6], [5, 0, 2], [2, 5, 2]] (as printed in "
       "the paper), find (AB)⁻¹. OR (b) Solve the following "
       "system of equations by matrix method: x + 2y + 3z = 6, "
       "2x − y + z = 2, 3x + 2y − 2z = 3."),
    _q(34, "D", 5, "three-dimensional-geometry",
       "(a) Find the vector and the Cartesian equations of a "
       "line passing through the point (1, 2, 4) and parallel "
       "to the line joining the points A(3, 3, 5) and "
       "B(1, 0, 11). Hence, find the distance between the two "
       "lines. OR (b) Find the equations of the line passing "
       "through the points A(1, 2, 3) and B(3, 5, 9). Hence, "
       "find the coordinates of the points on this line which "
       "are at a distance of 14 units from point B."),
    _q(35, "D", 5, "application-of-integrals",
       "Find the area of the region bounded by the curves "
       "x² = y, y = x + 2 and x-axis, using integration."),
    _q(36, "E", 4, "probability",
       "Case study: A Venn diagram represents the probabilities "
       "of three different types of Yoga, A, B and C performed "
       "by the people of a society. It is given that the "
       "probability of a member performing type C Yoga is 0.44. "
       "(i) Find the value of x. (ii) Find the value of y. "
       "(iii)(a) Find P(C/B). OR (iii)(b) Find the probability "
       "that a randomly selected person of the society does "
       "Yoga of type A or B but not C. (The values x and y are "
       "read from the Venn diagram printed in the paper.)"),
    _q(37, "E", 4, "application-of-derivatives",
       "Case study: A tank, formed using a combination of a "
       "cylinder and a cone, offers better drainage as compared "
       "to a flat bottomed tank. A tap is connected to such a "
       "tank whose conical part is full of water. Water is "
       "dripping out from a tap at the bottom at the uniform "
       "rate of 2 cm³/s. The semi-vertical angle of the "
       "conical tank is 45°. (i) Find the volume of water in "
       "the tank in terms of its radius r. (ii) Find the rate "
       "of change of radius at an instant when r = 2√2 cm. "
       "(iii)(a) Find the rate at which the wet surface of the "
       "conical tank is decreasing at an instant when radius "
       "r = 2√2 cm. OR (iii)(b) Find the rate of change of "
       "height when the height is 4 cm."),
    _q(38, "E", 4, "application-of-derivatives",
       "Case study: The equation of the path traced by a "
       "roller-coaster is given by the polynomial "
       "f(x) = a(x + 9)(x + 1)(x − 3). If the roller-coaster "
       "crosses the y-axis at the point (0, 1), answer the "
       "following: (i) Find the value of a. (ii) Find f′(x) "
       "at x = 1."),
]


# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Standard) 2024 — Set 30/1/1 (Delhi).
# Source: Oswaal solved-paper PDF hosted on Oswaal 360 (see source_url).
# Questions 12 and 18 are OMITTED: Q.12's exact wording and Q.18's graph
# could not be verified from the source text, so they are not guessed at.
# For a few MCQs whose option layout was scrambled in the source PDF,
# the question stem is given without options rather than inventing them.
# ---------------------------------------------------------------------------
_CBSE10_2024 = [
    _q(1, "A", 1, "polynomials",
       "If the sum of zeroes of the polynomial kx² − 2√2x + 1 "
       "is 2, then the value of k is:"),
    _q(2, "A", 1, "probability",
       "If the probability of a player winning a game is 0.79, "
       "then the probability of his losing the same game is: "
       "(A) 1.79 (B) 0.31 (C) 0.21% (D) 0.21"),
    _q(3, "A", 1, "quadratic-equations",
       "If the roots of equation ax² + bx + c = 0, a ≠ 0 are "
       "real and equal, then which of the following relation is "
       "true? (A) a = b (B) b² = ac (C) ac = b²/4 (D) c = b²/a"),
    _q(4, "A", 1, "arithmetic-progressions",
       "In an A.P., if the first term a = 7, nth term a_n = 84 "
       "and the sum of first n terms S_n = 2093/2, then n is "
       "equal to:"),
    _q(5, "A", 1, "real-numbers",
       "If two positive integers p and q can be expressed as "
       "p = 18a²b⁴ and q = 20a³b², where a and b are prime "
       "numbers, then LCM(p, q) is: (A) 2a²b² (B) 180a²b² "
       "(C) 12a²b² (D) 180a³b⁴"),
    _q(6, "A", 1, "coordinate-geometry",
       "AD is a median of ΔABC with vertices A(5, −6), B(6, 4) "
       "and C(0, 0). Length AD is equal to: (A) √68 units "
       "(B) 2√15 units (C) √101 units (D) 10 units"),
    _q(7, "A", 1, "introduction-to-trigonometry",
       "If sec θ − tan θ = m, then the value of sec θ + tan θ "
       "is: (A) 1 (B) m² (C) 1/m (D) −m"),
    _q(8, "A", 1, "probability",
       "From the data 1, 4, 7, 9, 16, 21, 25 if all the even "
       "numbers are removed, then the probability of getting a "
       "prime number from the remaining is: (A) 2/5 (B) 1/5 "
       "(C) 1/2 (D) 2/7"),
    _q(9, "A", 1, "statistics",
       "From some data x1, x2, ... xn with respective "
       "frequencies f1, f2, ... fn, the value of Σ fi(xi − x̄) "
       "is equal to: (A) n·x̄ (B) 1 (C) Σfi (D) 0"),
    _q(10, "A", 1, "polynomials",
       "The zeroes of a polynomial x² + px + q are twice the "
       "zeroes of the polynomial 4x² − 5x − 6. The value of p "
       "is: (A) −5/2 (B) 5/2 (C) −5 (D) 10"),
    _q(11, "A", 1, "coordinate-geometry",
       "If the distance between the points (3, −5) and (x, −5) "
       "is 15 units, then the values of x are: (A) 12, −18 "
       "(B) −12, 18 (C) 18, 5 (D) −9, −12"),
    _q(13, "A", 1, "surface-areas-and-volumes",
       "A solid sphere is cut into two hemispheres. The ratio "
       "of the surface areas of sphere to that of two "
       "hemispheres taken together, is: (A) 1 : 1 (B) 1 : 4 "
       "(C) 2 : 3 (D) 3 : 2"),
    _q(14, "A", 1, "statistics",
       "The middle most observation of every data arranged in "
       "order is called: (A) mode (B) median (C) mean "
       "(D) deviation"),
    _q(15, "A", 1, "surface-areas-and-volumes",
       "The volume of the largest right circular cone that can "
       "be carved out from a solid cube of edge 2 cm is: "
       "(A) 4π/3 cm³ (B) 5π/3 cm³ (C) 8π/3 cm³ (D) 2π/3 cm³"),
    _q(16, "A", 1, "probability",
       "Two dice are rolled together. The probability of "
       "getting sum of numbers on the two dice as 2, 3 or 5, "
       "is: (A) 7/36 (B) 11/36 (C) 5/36 (D) 4/9"),
    _q(17, "A", 1, "coordinate-geometry",
       "The centre of a circle is at (2, 0). If one end of a "
       "diameter is at (6, 0), then the other end is at: "
       "(A) (0, 0) (B) (4, 0) (C) (−2, 0) (D) (−6, 0)"),
    _q(19, "A", 1, "circles",
       "Assertion (A): The tangents drawn at the end points of "
       "a diameter of a circle, are parallel. Reason (R): "
       "Diameter of a circle is the longest chord. "
       "(Assertion-Reason question)"),
    _q(20, "A", 1, "polynomials",
       "Assertion (A): If the graph of a polynomial touches "
       "x-axis at only one point, then the polynomial cannot be "
       "a quadratic polynomial. Reason (R): A polynomial of "
       "degree n (n > 1) can have at most n zeroes. "
       "(Assertion-Reason question)"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "Solve the following system of linear equations "
       "7x − 2y = 5 and 8x + 7y = 15 and verify your answer."),
    _q(22, "B", 2, "probability",
       "In a pack of 52 playing cards one card is lost. From "
       "the remaining cards, a card is drawn at random. Find "
       "the probability that the drawn card is queen of heart, "
       "if the lost card is a black card."),
    _q(23, "B", 2, "introduction-to-trigonometry",
       "(b) If A = 60° and B = 30°, verify that: "
       "sin(A + B) = sin A cos B + cos A sin B. (OR choice of "
       "Q.23; the (a) part's expression could not be verified "
       "from the source text.)"),
    _q(24, "B", 2, "triangles",
       "In the given figure, ABCD is a quadrilateral. Diagonal "
       "BD bisects ∠B and ∠D both. Prove that: (i) ΔABD ~ ΔCBD "
       "(ii) AB = BC"),
    _q(25, "B", 2, "real-numbers",
       "(a) Prove that 5 − 2√3 is an irrational number. It is "
       "given that √3 is an irrational number. OR (b) Show that "
       "the number 5 × 11 × 17 + 3 × 11 is a composite number."),
    _q(26, "C", 3, "coordinate-geometry",
       "(b) ABCD is a rectangle formed by the points A(−1, −1), "
       "B(−1, 6), C(3, 6) and D(3, −1). P, Q, R and S are "
       "mid-points of sides AB, BC, CD and DA respectively. "
       "Show that diagonals of the quadrilateral PQRS bisect "
       "each other. (OR choice of Q.26)"),
    _q(27, "C", 3, "real-numbers",
       "In a teachers' workshop, the number of teachers "
       "teaching French, Hindi and English are 48, 80 and 144 "
       "respectively. Find the minimum number of rooms required "
       "if in each room the same number of teachers are seated "
       "and all of them are of the same subject."),
    _q(28, "C", 3, "introduction-to-trigonometry",
       "Prove that: tan θ/(1 − cot θ) + cot θ/(1 − tan θ) = "
       "1 + sec θ · cosec θ. OR (b) In the given figure PA, QB "
       "and RC are each perpendicular to AC. If AP = x, BQ = y "
       "and CR = z, then prove that 1/x + 1/z = 1/y."),
    _q(29, "C", 3, "pair-of-linear-equations",
       "Three years ago, Rashmi was thrice as old as Nazma. Ten "
       "years later, Rashmi will be twice as old as Nazma. How "
       "old are Rashmi and Nazma now?"),
    _q(30, "C", 3, "circles",
       "(a) In the given figure, AB is a diameter of the circle "
       "with centre O. AQ, BP and PQ are tangents to the "
       "circle. Prove that ∠POQ = 90°. OR (b) A circle with "
       "centre O and radius 8 cm is inscribed in a quadrilateral "
       "ABCD in which P, Q, R, S are the points of contact. If "
       "AD is perpendicular to DC, BC = 30 cm and BS = 24 cm, "
       "then find the length DC."),
    _q(31, "C", 3, "surface-areas-and-volumes",
       "The difference between the outer and inner radii of a "
       "hollow right circular cylinder of length 14 cm is 1 cm. "
       "If the volume of the metal used in making the cylinder "
       "is 176 cm³, find the outer and inner radii of the "
       "cylinder."),
    _q(32, "D", 5, "areas-related-to-circles",
       "An arc of a circle of radius 21 cm subtends an angle of "
       "60° at the centre. Find: (i) the length of the arc. "
       "(ii) the area of the minor segment of the circle made "
       "by the corresponding chord."),
    _q(33, "D", 5, "arithmetic-progressions",
       "(a) The sum of first and eight terms of an A.P. is 32 "
       "and their product is 60. Find the first term and common "
       "difference of the A.P. Hence, also find the sum of its "
       "first 20 terms. OR (b) In a A.P. of 40 terms, the sum "
       "of first 9 terms is 153 and the sum of last 6 terms is "
       "687. Determine the first term and common difference of "
       "A.P. Also, find the sum of all the terms of the A.P."),
    _q(34, "D", 5, "triangles",
       "(a) If a line is drawn parallel to one side of a "
       "triangle to intersect the other two sides in distinct "
       "points, then prove that the other two sides are divided "
       "in the same ratio."),
    _q(35, "D", 5, "some-applications-of-trigonometry",
       "A pole 6 m high is fixed on the top of a tower. The "
       "angle of elevation of the top of the pole observed from "
       "a point P on the ground is 60° and the angle of "
       "depression of the point P from the top of the tower is "
       "45°. Find the height of the tower and the distance of "
       "point P from the foot of the tower."),
    _q(36, "E", 4, "quadratic-equations",
       "Case study: A rectangular floor area can be completely "
       "tiled with 200 square tiles. If the side length of each "
       "tile is increased by 1 unit, it would take only 128 "
       "tiles to cover the floor. (i) Assuming the original "
       "length of each side of a tile be x units, make a "
       "quadratic equation from the above information. "
       "(ii) Write the corresponding quadratic equation in "
       "standard form. (iii)(a) Find the value of x, the length "
       "of side of a tile by factorisation. OR (iii)(b) Solve "
       "the quadratic equation for x, using quadratic formula."),
    _q(37, "E", 4, "statistics",
       "Case study: BINGO is a game of chance. The host has 75 "
       "balls numbered 1 through 75. Each player has a BINGO "
       "card with some numbers written on it. The participant "
       "cancels the number on the card when called out a number "
       "written on the ball selected at random. Based on the "
       "information and the grouped data table printed in the "
       "paper, answer: (i) Write the median class. (ii) When "
       "the first ball was picked up, what was the probability "
       "of calling out an even number? (iii)(a) Find the median "
       "of the given data. OR (iii)(b) Find the mode of the "
       "given data."),
    _q(38, "E", 4, "circles",
       "Case study: A backyard is in the shape of a triangle "
       "ABC with right angle at B. AB = 7 m and BC = 15 m. A "
       "circular pit was dug inside it such that it touches the "
       "walls AC, BC and AB at P, Q and R respectively such "
       "that AP = x m. (Sub-questions on the in-circle of the "
       "triangle, as printed in the paper.)"),
]


# ---------------------------------------------------------------------------
# HBSE (Haryana Board) Class 10 Mathematics (Standard) 2024 —
# Code No. 1103, Set A, Series Sec/Annual Exam-2024.
# Full text: AglaSem Docs (see source_url in the entry below).
# All 38 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_HBSE10_2024 = [
    _q(1, "A", 1, "real-numbers",
       "L.C.M. of 6, 72 and 120 is: (A) 120 (B) 6 (C) 360 "
       "(D) 240"),
    _q(2, "A", 1, "real-numbers",
       "Which of the following is a rational number? "
       "(A) 7 + √2 (B) 5 − √3 (C) 2 + √9 (D) 5 − √2"),
    _q(3, "A", 1, "polynomials",
       "The quadratic polynomial, the sum and product of whose "
       "zeroes are 4 and 1, is: (A) x² − 4x − 1 (B) x² − 4x + 1 "
       "(C) x² + 4x − 1 (D) x² + 4x + 1"),
    _q(4, "A", 1, "arithmetic-progressions",
       "Which term of A.P. 10, 7, 4, … is −62? (A) 15th "
       "(B) 25th (C) 27th (D) 30th"),
    _q(5, "A", 1, "quadratic-equations",
       "Value of k for which the quadratic equation "
       "kx² − 2kx + 6 = 0 has equal roots is: (A) 6 (B) −6 "
       "(C) 8 (D) −8"),
    _q(6, "A", 1, "coordinate-geometry",
       "The distance between the points (−5, 7) and (−1, 3) is: "
       "(A) 2√2 (B) 4√2 (C) 5√2 (D) 6√2"),
    _q(7, "A", 1, "triangles",
       "In triangles ABC and DEF, ∠B = ∠E, ∠C = ∠F and "
       "AB = DE, then the two triangles are: (A) Similar as "
       "well as congruent (B) Congruent but not similar "
       "(C) Similar but not congruent (D) Neither congruent "
       "nor similar"),
    _q(8, "A", 1, "circles",
       "If tangents PA and PB from a point P to a circle with "
       "centre O are inclined to each other at angle 80°, then "
       "∠POA is equal to: (A) 50° (B) 60° (C) 70° (D) 80°"),
    _q(9, "A", 1, "circles",
       "A tangent PQ at a point P of a circle of radius 5 cm "
       "meets a line through the centre O at a point Q so that "
       "OQ = 12 cm, length PQ is: (A) 12 cm (B) 13 cm (C) 8 cm "
       "(D) √119 cm"),
    _q(10, "A", 1, "introduction-to-trigonometry",
       "What is the value of sin 60° cos 30° + sin 30° cos 60°? "
       "(A) −1 (B) 1 (C) 0 (D) 2"),
    _q(11, "A", 1, "introduction-to-trigonometry",
       "If sin A = 3/4, then what is the value of tan A? "
       "(A) 3/√7 (B) 4/√7 (C) 3/5 (D) 4/5"),
    _q(12, "A", 1, "introduction-to-trigonometry",
       "9 sec²A − 9 tan²A is equal to: (A) 1 (B) 9 (C) 8 (D) 0"),
    _q(13, "A", 1, "areas-related-to-circles",
       "Area of a sector of angle P (in degrees) of a circle "
       "with radius R is: (A) (P/180) × 2πR (B) (P/180) × πR² "
       "(C) (P/360) × 2πR (D) (P/720) × 2πR²"),
    _q(14, "A", 1, "areas-related-to-circles",
       "The area of a sector of a circle with radius 6 cm, if "
       "angle of the sector is 60°, is: (A) 132/7 cm² "
       "(B) 264/7 cm² (C) 132 cm² (D) 64/7 cm²"),
    _q(15, "A", 1, "surface-areas-and-volumes",
       "Surface area of a metallic sphere having radius 2.1 cm "
       "is: (A) 88.7 cm² (B) 194.5 cm² (C) 55.44 cm² "
       "(D) 39.04 cm²"),
    _q(16, "A", 1, "statistics",
       "If the Median and the Mode of a data are 11 and 17 "
       "respectively, then its Mean is: (A) 7 (B) 8 (C) 9 (D) 10"),
    _q(17, "A", 1, "statistics",
       "For the following distribution, the sum of lower limits "
       "of the median class and modal class is: Class Interval "
       "0-5, 5-10, 10-15, 15-20, 20-25 with Frequency 10, 15, "
       "12, 20, 9. (A) 15 (B) 25 (C) 30 (D) 35"),
    _q(18, "A", 1, "probability",
       "A die is thrown once. The probability of getting an odd "
       "number is: (A) 1/3 (B) 1/2 (C) 1/4 (D) 1/5"),
    _q(19, "A", 1, "real-numbers",
       "Assertion (A): √3 is an example of irrational number. "
       "Reason (R): The square roots of all positive integers "
       "are irrational numbers. (Assertion-Reason question)"),
    _q(20, "A", 1, "coordinate-geometry",
       "Assertion (A): The point (0, 5) lies on y-axis. "
       "Reason (R): The x-coordinate on the point on y-axis is "
       "zero. (Assertion-Reason question)"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "Solve the following pair of linear equations: "
       "2x + 3y = 13 and 5x − 4y = −2."),
    _q(22, "B", 2, "some-applications-of-trigonometry",
       "A tower stands vertically on the ground. From a point "
       "on the ground which is 15 m away from the foot of the "
       "tower, the angle of elevation of the top of the tower "
       "is found to be 60°. Find the height of the tower. OR "
       "In the figure, PS/SQ = PT/TR and ∠PST = ∠PRQ. Prove "
       "that ΔPQR is an isosceles triangle."),
    _q(23, "B", 2, "circles",
       "The length of a tangent from a point A at distance 5 cm "
       "from the centre of circle is 4 cm. Find the radius of "
       "circle."),
    _q(24, "B", 2, "introduction-to-trigonometry",
       "Evaluate the following: 2 tan²45° + cos²30° − sin²60°"),
    _q(25, "B", 2, "areas-related-to-circles",
       "Find the area of the sector of a circle with radius "
       "4 cm and of angle 30°. OR Find the area of a quadrant "
       "of a circle, whose circumference is 22 cm."),
    _q(26, "C", 3, "real-numbers",
       "Prove that √5 is irrational number."),
    _q(27, "C", 3, "polynomials",
       "Find the zeroes of the quadratic polynomial x² + 7x + 10 "
       "and verify the relationship between the zeroes and "
       "coefficients."),
    _q(28, "C", 3, "pair-of-linear-equations",
       "The ratio of incomes of two persons is 9 : 7 and the "
       "ratio of their expenditure is 4 : 3. If each of them "
       "manage to save Rs. 2,000 per month. Find their monthly "
       "income. OR The larger of two supplementary angles "
       "exceeds the smaller by 18 degrees. Find them."),
    _q(29, "C", 3, "circles",
       "Prove that in two concentric circles the chord of the "
       "larger circle, which touches the smaller circle, is "
       "bisected at the point of contact."),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "Prove that: √(1 + sin A)/√(1 − sin A) = sec A + tan A. "
       "OR Prove that: sec A(1 − sin A)(sec A + tan A) = 1."),
    _q(31, "C", 3, "probability",
       "A die is thrown once, find the probability of getting: "
       "(i) a prime number (ii) a number lying between 2 and 6 "
       "(iii) an odd number."),
    _q(32, "D", 5, "quadratic-equations",
       "Find two consecutive positive integer, sum of whose "
       "squares is 365. OR Find the discriminant of the "
       "equation 3x² − 2x + 1/3 = 0 and hence find the nature "
       "of its roots. Find them, if they are real."),
    _q(33, "D", 5, "triangles",
       "A girl of height 90 cm is walking away from the base "
       "of a lamp post at the speed of 1.2 m/s. If the lamp is "
       "3.6 m above the ground. Find the length of her shadow "
       "after 4 second."),
    _q(34, "D", 5, "surface-areas-and-volumes",
       "Shanta runs an industry in a shed which is in the shape "
       "of a cuboid surmounted by a half cylinder. If the base "
       "of the shed is of dimension 7 m × 15 m and the height "
       "of the cuboidal portion is 8 m. Find the volume of air "
       "that shed can hold. Further suppose the machinery in "
       "the shed occupies a total space of 300 m³ and there are "
       "20 workers, each of whom occupy about 0.08 m³ space on "
       "an average. Then how much air is in the shed? "
       "(Take π = 22/7) OR The decorative block shown in fig. "
       "is made of two solids − a cube and a hemisphere. The "
       "base of the block is a cube with edge 5 cm and the "
       "hemisphere fixed on the top has a diameter of 4.2 cm. "
       "Find the total surface area of the block. "
       "(Take π = 22/7)"),
    _q(35, "D", 5, "statistics",
       "The following frequency distribution gives the monthly "
       "consumption of electricity of 68 consumers of a "
       "locality. Find the mode of data: Monthly Consumption "
       "(in Units) 65-85, 85-105, 105-125, 125-145, 145-165, "
       "165-185, 185-205 with No. of Consumers 4, 5, 13, 20, "
       "14, 8, 4."),
    _q(36, "E", 4, "arithmetic-progressions",
       "Case study: A manufacturer of TV sets produced 600 sets "
       "in third year and 700 sets in seventh years. Assuming "
       "that the production increase uniformly by a fixed "
       "number every year, find: (i) the production in the 1st "
       "year (ii) the production in 10th year (iii)(a) the "
       "total production in first 7 years or (b) total "
       "production in 10 years."),
    _q(37, "E", 4, "coordinate-geometry",
       "Case study: Resident Welfare Association (RWA) of a "
       "society put up three electric poles A, B and C in a "
       "society's park. Despite these three poles, some part "
       "of the park are still in dark, so RWA decides to have "
       "one more electric pole D in the park. Based on the "
       "above information, answer the following questions: "
       "(i) Find the position of the pole C. (ii) Find the "
       "distance of the pole B from corner O of the park. "
       "(iii)(a) Find the position of the fourth pole D so "
       "that four points A, B, C and D form a parallelogram. "
       "or (b) Find the distance between poles A and C. "
       "(Positions are read from the park diagram printed in "
       "the paper.)"),
    _q(38, "E", 4, "some-applications-of-trigonometry",
       "Case study: Two hoardings are put on two poles of "
       "equal heights standing on either side of the road. "
       "From a point between them on the road the angle of "
       "elevation of the top of poles are 60° and 30° "
       "respectively. Height of each of pole is 20 m. Based on "
       "above information, answer the following questions: "
       "(i) Find the length of PO. (ii) Find the length of RO. "
       "(iii)(a) Find the width of the road. or (b) If the "
       "angle of elevation made by PQ is 45°, then find the "
       "length of PO."),
]


# ---------------------------------------------------------------------------
# The library registry. Every entry: id, class, board, year, set label,
# source name + URL (the public page the full text was fetched from),
# an honesty note, and the transcribed questions.
# ---------------------------------------------------------------------------
PAPERS = [
    {
        "id": "cbse-12-2024",
        "class_num": 12,
        "board": "CBSE",
        "year": 2024,
        "set_label": "Q.P. Code 65/1/1 · Series PQ1RS/1 · Set 1",
        "source_name": "CBSE Class 12 Mathematics Question Paper "
                       "2024 (full text on AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "5fe0302c-9cfd-11ef-a3b5-0a5e36bc6706",
        "note": "All 38 questions of the paper are included, "
                "transcribed from the source text.",
        "questions": _CBSE12_2024,
    },
    {
        "id": "cbse-12-2023",
        "class_num": 12,
        "board": "CBSE",
        "year": 2023,
        "set_label": "Q.P. Code 65/1/1 · Series EF1GH/1 · Set 1",
        "source_name": "CBSE Class 12 Mathematics Question Paper "
                       "2023 (full text on AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "de97cc22-a587-11ee-8916-0a5e36bc6706",
        "note": "Questions 13 and 15 are NOT included: their "
                "defining expressions are illegible in the "
                "source text, so they were left out instead of "
                "being guessed. Q.19's printed range is partly "
                "illegible and is marked inside the question.",
        "questions": _CBSE12_2023,
    },
    {
        "id": "cbse-10-2024",
        "class_num": 10,
        "board": "CBSE",
        "year": 2024,
        "set_label": "Set 30/1/1 · Delhi Set 1 · Mathematics "
                     "(Standard)",
        "source_name": "CBSE Class 10 Mathematics (Standard) "
                       "Question Paper 2024, solved paper "
                       "(Oswaal 360)",
        "source_url": "https://o360stg.oswaal360.com/pluginfile.php/"
                      "10939/mod_folder/content/0/Latest%20Board%20"
                      "Paper%202024/CBSE%20Class%2010/CBSE%20Maths%20"
                      "Standard%2010th%20Solved%20Paper-1-32.pdf",
        "note": "Questions 12 and 18 are NOT included: Q.12's "
                "exact wording and Q.18's graph could not be "
                "verified from the source text. A few MCQs are "
                "shown without options where the source PDF's "
                "option layout was scrambled.",
        "questions": _CBSE10_2024,
    },
    {
        "id": "hbse-10-2024",
        "class_num": 10,
        "board": "HBSE (Haryana Board)",
        "year": 2024,
        "set_label": "Code No. 1103 · Set A · Mathematics "
                     "(Standard)",
        "source_name": "HBSE Class 10 Mathematics (Standard) "
                       "Question Paper 2024 (full text on "
                       "AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "2479a438-eea5-11ef-bd5f-0a5e36bc6706",
        "note": "All 38 questions of the paper are included, "
                "transcribed from the source text.",
        "questions": _HBSE10_2024,
    },
]

PAPER_BY_ID = {p["id"]: p for p in PAPERS}
CLASSES_WITH_PAPERS = sorted({p["class_num"] for p in PAPERS})


def get_paper(paper_id):
    return PAPER_BY_ID.get(paper_id)


def papers_for_class(class_num):
    return [p for p in PAPERS if p["class_num"] == class_num]


def chapter_title(class_num, slug):
    chapter = get_chapter(class_num, slug)
    return chapter["title"] if chapter else slug


def paper_total_marks(paper):
    return sum(q["marks"] for q in paper["questions"])


# ---------------------------------------------------------------------------
# Pattern analysis — computed from the library above, never hand-written.
# ---------------------------------------------------------------------------
def analysis_for_class(class_num):
    """Chapter-wise marks weightage for one class, computed from
    every collected paper of that class.

    Returns a dict with the honest coverage facts (paper count,
    years, total marks actually collected) and per-chapter rows:
    marks, question count, % share of the collected marks. Rows
    are sorted by marks (desc) — that order IS the "expected
    focus" ranking, and "most repeated" is the same rows re-sorted
    by question count.
    """
    papers = papers_for_class(class_num)
    per_chapter = {}
    total_marks = 0
    total_questions = 0
    for paper in papers:
        for q in paper["questions"]:
            total_marks += q["marks"]
            total_questions += 1
            row = per_chapter.setdefault(
                q["chapter"], {"slug": q["chapter"], "marks": 0,
                               "questions": 0})
            row["marks"] += q["marks"]
            row["questions"] += 1
    rows = []
    for row in per_chapter.values():
        row = dict(row)
        row["title"] = chapter_title(class_num, row["slug"])
        row["share"] = (round(100.0 * row["marks"] / total_marks, 1)
                        if total_marks else 0.0)
        rows.append(row)
    by_marks = sorted(rows, key=lambda r: (-r["marks"], r["title"]))
    by_count = sorted(rows, key=lambda r: (-r["questions"],
                                           -r["marks"], r["title"]))
    return {
        "class_num": class_num,
        "paper_count": len(papers),
        "years": sorted({p["year"] for p in papers}),
        "boards": sorted({p["board"] for p in papers}),
        "total_marks": total_marks,
        "total_questions": total_questions,
        "chapters": by_marks,
        "most_repeated": by_count,
        "focus": by_marks[:5],
    }


# ---------------------------------------------------------------------------
# "Apna Paper Banao" generator.
#
# Fresh practice questions are produced ONLY by the templates below
# (NCERT-style, parameterised). They are always flagged generated.
# Real questions are reused from the library. Slot filling follows
# PAPER_STRUCTURE exactly, with chapters drawn in proportion to
# their collected marks weightage for the class.
# ---------------------------------------------------------------------------
def _t10_real_numbers(rng):
    if rng.random() < 0.5:
        a, b = rng.choice([(12, 18), (24, 36), (18, 48), (26, 91),
                           (36, 60), (45, 75)])
        return f"Find the HCF of {a} and {b}."
    a, b = rng.choice([(4, 6), (12, 16), (9, 12), (15, 20),
                       (8, 14)])
    return f"Find the LCM of {a} and {b}."


def _t10_polynomials(rng):
    r1, r2 = rng.randint(1, 6), rng.randint(1, 6)
    if rng.random() < 0.5:
        return (f"Find the zeroes of the polynomial "
                f"x^2 - {r1 + r2}x + {r1 * r2}.")
    return (f"Find a quadratic polynomial whose zeroes are "
            f"{r1} and {r2}.")


def _t10_pair(rng):
    x, y = rng.randint(2, 9), rng.randint(2, 9)
    return (f"Solve x + y = {x + y} and x - y = {x - y}.")


def _t10_quadratic(rng):
    r1, r2 = rng.randint(1, 9), rng.randint(1, 9)
    return f"Solve x^2 - {r1 + r2}x + {r1 * r2} = 0"


def _t10_ap(rng):
    a, d = rng.randint(1, 15), rng.randint(2, 9)
    if rng.random() < 0.5:
        n = rng.randint(5, 15)
        return (f"Find the {n}th term of the AP {a}, {a + d}, "
                f"{a + 2 * d}, ...")
    n = rng.choice([10, 12, 15, 20])
    return (f"Find the sum of the first {n} terms of the AP "
            f"{a}, {a + d}, {a + 2 * d}, ...")


def _t10_triangles(rng):
    ad, db, ae = rng.choice([(2, 3, 4), (3, 5, 6), (4, 6, 3),
                             (5, 5, 7)])
    return (f"In triangle ABC, DE is parallel to BC, with "
            f"AD = {ad} cm, DB = {db} cm and AE = {ae} cm. "
            f"Find EC.")


def _t10_coordinate(rng):
    x1, y1 = rng.randint(0, 4), rng.randint(0, 4)
    x2, y2 = x1 + rng.choice([3, 6]), y1 + rng.choice([4, 8])
    return f"Find the distance between ({x1}, {y1}) and ({x2}, {y2})"


def _t10_intro_trig(rng):
    fn, ang = rng.choice([("sin", 30), ("cos", 60), ("tan", 45),
                          ("sin", 60), ("cos", 30)])
    return f"What is {fn} {ang}?"


def _t10_applications_trig(rng):
    d = rng.choice([10, 15, 20, 30])
    return (f"A tower stands vertically on the ground. From a "
            f"point on the ground, {d} m away from the foot of "
            f"the tower, the angle of elevation of the top of "
            f"the tower is 60 degrees. Find the height of the "
            f"tower.")


def _t10_circles(rng):
    dist, tang = rng.choice([(5, 4), (13, 12), (10, 8), (25, 24)])
    return (f"The length of a tangent from a point A at distance "
            f"{dist} cm from the centre of a circle is {tang} cm. "
            f"Find the radius of the circle.")


def _t10_areas_circles(rng):
    r = rng.choice([7, 14, 6, 21])
    ang = rng.choice([30, 60, 90])
    return (f"Find the area of a sector of a circle with radius "
            f"{r} cm and angle {ang} degrees (use pi = 22/7).")


def _t10_surface(rng):
    if rng.random() < 0.5:
        s = rng.randint(3, 10)
        return f"Find the volume of a cube of side {s} cm"
    r = rng.choice([7, 14, 21])
    return (f"Find the surface area of a sphere of radius {r} cm "
            f"(use pi = 22/7).")


def _t10_statistics(rng):
    nums = sorted(rng.randint(2, 30) for _ in range(5))
    joined = ", ".join(map(str, nums))
    if rng.random() < 0.5:
        return f"Find the mean of {joined}"
    return f"Find the median of {joined}"


def _t10_probability(rng):
    k = rng.randint(1, 6)
    if rng.random() < 0.5:
        return (f"What is the probability of getting a {k} on "
                f"one roll of a fair die? (answer in decimal)")
    return ("A die is thrown once. Find the probability of "
            "getting a prime number.")


_TEMPLATES_10 = {
    "real-numbers": _t10_real_numbers,
    "polynomials": _t10_polynomials,
    "pair-of-linear-equations": _t10_pair,
    "quadratic-equations": _t10_quadratic,
    "arithmetic-progressions": _t10_ap,
    "triangles": _t10_triangles,
    "coordinate-geometry": _t10_coordinate,
    "introduction-to-trigonometry": _t10_intro_trig,
    "some-applications-of-trigonometry": _t10_applications_trig,
    "circles": _t10_circles,
    "areas-related-to-circles": _t10_areas_circles,
    "surface-areas-and-volumes": _t10_surface,
    "statistics": _t10_statistics,
    "probability": _t10_probability,
}


def _t12_relations(rng):
    a, b, v = rng.choice([(2, 3, 1), (3, -2, 2), (4, 5, 0),
                          (5, -1, 3)])
    return f"If f(x) = {a}x + {b}, find f(f({v}))."


def _t12_inverse_trig(rng):
    fn, val = rng.choice([("arcsin", "0.5"), ("arccos", "0.5"),
                          ("arctan", "1")])
    return f"Find the principal value of {fn}({val}) in degrees."


def _det_question(rng):
    a, b = rng.randint(1, 6), rng.randint(0, 5)
    c, d = rng.randint(0, 5), rng.randint(1, 6)
    return f"Find the determinant of [[{a}, {b}], [{c}, {d}]]"


def _t12_continuity(rng):
    n = rng.choice([2, 3])
    a = rng.randint(2, 3)
    return f"What is the derivative of x^{n} at x = {a}?"


def _t12_aod(rng):
    r = rng.choice([3, 5, 7, 10])
    return (f"Find the rate of change of the area of a circle "
            f"with respect to its radius when r = {r} cm.")


def _t12_integrals(rng):
    if rng.random() < 0.5:
        n = rng.choice([2, 3])
        return f"integrate x^{n}"
    a = rng.randint(1, 3)
    return f"integrate x^2 from 0 to {a}"


def _t12_aoi(rng):
    a = rng.choice([2, 3, 4])
    return (f"Using integration, find the area of the region "
            f"bounded by the line y = x, the x-axis and the "
            f"line x = {a}.")


def _t12_de(rng):
    a = rng.choice([2, 3])
    return f"solve dy/dx = {a}x"


def _t12_vectors(rng):
    a, b, c = rng.choice([(2, 3, 6), (1, 2, 2), (3, 4, 0),
                          (2, 6, 3)])
    return (f"Find the magnitude of the vector {a}i + {b}j + "
            f"{c}k.")


def _t12_3d(rng):
    a, b, c = rng.randint(1, 5), rng.randint(1, 5), rng.randint(1, 5)
    return (f"Find the distance of the point ({a}, {b}, {c}) "
            f"from the y-axis.")


def _t12_lpp(rng):
    a, b, s = rng.choice([(3, 2, 10), (2, 5, 12), (4, 3, 15)])
    return (f"Maximise z = {a}x + {b}y subject to x + y <= {s}, "
            f"x >= 0, y >= 0 (solve graphically).")


def _t12_probability(rng):
    total = rng.choice([7, 9, 11])
    return (f"Two dice are thrown. What is the probability that "
            f"the sum is {total}? (answer in decimal)")


_TEMPLATES_12 = {
    "relations-and-functions": _t12_relations,
    "inverse-trigonometric-functions": _t12_inverse_trig,
    "matrices": _det_question,
    "determinants": _det_question,
    "continuity-and-differentiability": _t12_continuity,
    "application-of-derivatives": _t12_aod,
    "integrals": _t12_integrals,
    "application-of-integrals": _t12_aoi,
    "differential-equations": _t12_de,
    "vector-algebra": _t12_vectors,
    "three-dimensional-geometry": _t12_3d,
    "linear-programming": _t12_lpp,
    "probability": _t12_probability,
}

TEMPLATES = {10: _TEMPLATES_10, 12: _TEMPLATES_12}


def _answer_key_for_generated(text, source_url=None):
    """Answer key for one generated practice question: solver
    steps when Ganitra's solver can solve the question text,
    otherwise a plain pointer to the chapter / marking scheme.
    Never raises."""
    lowered = text.lower()
    if any(word in lowered for word in ("prove", "show that",
                                        "draw", "graphically")):
        return {"kind": "note",
                "text": "Work this out from the NCERT chapter, "
                        "then check your steps with Ganitra's "
                        "chat."}
    try:
        from solver.router import solve_question
        result = solve_question(text)
    except Exception:
        result = None
    if result and result.get("op") != "error" \
            and result.get("answer"):
        return {"kind": "solver",
                "answer": str(result.get("answer")),
                "steps": [str(s) for s in
                          (result.get("steps") or [])][:8]}
    return {"kind": "note",
            "text": "Practise this from your NCERT chapter; "
                    "type the question into Ganitra's chat for a "
                    "step-by-step solution."}


def generate_practice_paper(class_num, seed=None):
    """Build one fresh 80-mark practice paper for Class 10 or 12.

    Follows PAPER_STRUCTURE exactly. Chapters are drawn in
    proportion to their collected marks weightage (analysis);
    each slot first tries an unused real question from the
    library for that chapter + section, else a generated
    template question (flagged "generated", with the
    "practice question" label on the pages).
    """
    rng = random.Random(seed)
    analysis = analysis_for_class(class_num)
    weights = {row["slug"]: row["marks"]
               for row in analysis["chapters"]}
    chapters = [c["slug"] for c in get_chapters(class_num)]
    if not chapters:
        return None
    templates = TEMPLATES.get(class_num, {})

    real_pool = {}
    for paper in papers_for_class(class_num):
        for q in paper["questions"]:
            real_pool.setdefault((q["chapter"], q["section"]),
                                 []).append((paper, q))
    for pool in real_pool.values():
        rng.shuffle(pool)

    def pick_chapter(section_counts):
        weighted = []
        for slug in chapters:
            w = weights.get(slug, 1)
            # keep one section from collapsing onto one chapter
            w = w / (1 + section_counts.get(slug, 0))
            weighted.append((slug, w))
        total = sum(w for _, w in weighted)
        pick = rng.uniform(0, total)
        upto = 0.0
        for slug, w in weighted:
            upto += w
            if pick <= upto:
                return slug
        return weighted[-1][0]

    sections = []
    total = 0
    real_used = 0
    for section, (count, marks) in PAPER_STRUCTURE.items():
        section_counts = {}
        questions = []
        for _ in range(count):
            chapter = pick_chapter(section_counts)
            section_counts[chapter] = \
                section_counts.get(chapter, 0) + 1
            pool = real_pool.get((chapter, section)) or []
            if pool and rng.random() < 0.75:
                paper, q = pool.pop()
                real_used += 1
                questions.append({
                    "text": q["text"], "chapter": chapter,
                    "chapter_title": chapter_title(class_num,
                                                   chapter),
                    "marks": marks, "source": "real",
                    "origin": f"{paper['board']} {paper['year']}",
                    "answer_key": {
                        "kind": "scheme",
                        "text": "See the marking scheme / source "
                                "paper",
                        "url": paper["source_url"]},
                })
            else:
                template = templates.get(chapter)
                if template is None:
                    text = (f"Practice question from "
                            f"{chapter_title(class_num, chapter)} "
                            f"(NCERT Class {class_num}).")
                    key = {"kind": "note",
                           "text": "Practise this from your "
                                   "NCERT chapter."}
                else:
                    text = template(rng)
                    key = _answer_key_for_generated(text)
                questions.append({
                    "text": text, "chapter": chapter,
                    "chapter_title": chapter_title(class_num,
                                                   chapter),
                    "marks": marks, "source": "generated",
                    "origin": "Ganitra practice question",
                    "answer_key": key,
                })
            total += marks
        sections.append({"section": section,
                         "title": SECTION_TITLES[section],
                         "marks_each": marks, "questions": questions})
    return {
        "class_num": class_num,
        "sections": sections,
        "total_marks": total,
        "real_count": real_used,
        "generated_count": sum(len(s["questions"])
                               for s in sections) - real_used,
        "based_on": {"papers": analysis["paper_count"],
                     "years": analysis["years"]},
    }


__all__ = ["PAPERS", "PAPER_BY_ID", "CLASSES_WITH_PAPERS",
           "PAPER_STRUCTURE", "TOTAL_MARKS", "SECTION_TITLES",
           "get_paper", "papers_for_class", "chapter_title",
           "paper_total_marks", "analysis_for_class",
           "generate_practice_paper"]
