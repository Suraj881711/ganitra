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


def section_title_for(section, questions):
    """Display title for one section of a STORED paper.

    SECTION_TITLES describes the current 80-mark pattern above.
    Wave 44 added real papers whose sections carry different
    marks (CBSE 2022 Term-2: A=2/B=3/C=4; CBSE 2020: D=4), so
    when a section's actual marks differ from PAPER_STRUCTURE,
    build the title from the stored data instead of misstating
    the marks. Sections that match the current pattern keep
    their SECTION_TITLES text verbatim.
    """
    standard = PAPER_STRUCTURE[section][1]
    marks = {q["marks"] for q in questions}
    if marks == {standard}:
        return SECTION_TITLES[section]
    if len(marks) == 1:
        return f"Section {section} ({marks.pop()} marks each)"
    return f"Section {section}"


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
# CBSE Class 10 Mathematics (Standard) 2025 — solved paper, LearnCBSE.
# Q.11 is NOT included (see the note in the registry entry below).
# ---------------------------------------------------------------------------
_CBSE10_2025 = [
    _q(1, "A", 1, "real-numbers",
       "√0.4 is a/an: (A) natural number (B) integer "
       "(C) rational number (D) irrational number"),
    _q(2, "A", 1, "real-numbers",
       "Which of the following cannot be the unit digit of 8^n, "
       "where n is a natural number? (A) 4 (B) 2 (C) 0 (D) 6"),
    _q(3, "A", 1, "quadratic-equations",
       "Which of the following quadratic equations has real and "
       "equal roots? (A) (x + 1)² = 2x + 1 (B) x² + x = 0 "
       "(C) x² − 4 = 0 (D) x² + x + 1 = 0"),
    _q(4, "A", 1, "polynomials",
       "If the zeroes of the polynomial ax² + bx + 2a/b are "
       "reciprocal of each other, then the value of b is: "
       "(A) 2 (B) 1/2 (C) −2 (D) −1/2"),
    _q(5, "A", 1, "coordinate-geometry",
       "The distance of the point A(−3, −4) from the X-axis is: "
       "(A) 3 (B) 4 (C) 5 (D) 7"),
    _q(6, "A", 1, "triangles",
       "In the given figure, PQ ∥ XY ∥ BC, AP = 2 cm, PX = 1.5 cm "
       "and BX = 4 cm. If QY = 0.75 cm, then AQ + CY is equal to: "
       "(A) 6 cm (B) 4.5 cm (C) 3 cm (D) 5.25 cm"),
    _q(7, "A", 1, "triangles",
       "Given ΔABC ∼ ΔPQR, ∠A = 30° and ∠Q = 90°. The value of "
       "(∠R + ∠B) is: (A) 90° (B) 120° (C) 150° (D) 180°"),
    _q(8, "A", 1, "probability",
       "Two coins are tossed simultaneously. The probability of "
       "getting at least one head is: (A) 1/4 (B) 1/2 (C) 3/4 "
       "(D) 1"),
    _q(9, "A", 1, "circles",
       "In the given figure, PA and PB are tangents to a circle "
       "with centre O such that ∠P = 90°. If AB = 3√2 cm, then "
       "the diameter of the circle is: (A) 3√2 cm (B) 6√2 cm "
       "(C) 3 cm (D) 6 cm"),
    _q(10, "A", 1, "circles",
       "For a circle with centre O and radius 5 cm, which of the "
       "following statements is true? P: Distance between every "
       "pair of parallel tangents is 5 cm. Q: Distance between "
       "every pair of parallel tangents is 10 cm. R: Distance "
       "between every pair of parallel tangents must be between "
       "5 cm and 10 cm. S: There does not exist a point outside "
       "the circle from where length of tangent is 5 cm. "
       "(A) P (B) Q (C) R (D) S"),
    _q(12, "A", 1, "introduction-to-trigonometry",
       "If x × (2 tan 30°/(1 + tan²30°)) = y × (2 tan 30°/"
       "(1 − tan²30°)), then x : y is equal to: (A) 1 : 1 "
       "(B) 1 : 2 (C) 2 : 1 (D) 4 : 1"),
    _q(13, "A", 1, "some-applications-of-trigonometry",
       "A peacock sitting on the top of a tree of height 10 m "
       "observes a snake moving on the ground. If the snake is "
       "10√3 m away from the base of the tree, then the angle of "
       "depression of the snake from the eye of the peacock is: "
       "(A) 30° (B) 45° (C) 60° (D) 90°"),
    _q(14, "A", 1, "surface-areas-and-volumes",
       "If a cone of greatest possible volume is hollowed out "
       "from a solid wooden cylinder, then the ratio of the "
       "volume of remaining wood to the volume of cone hollowed "
       "out is: (A) 1 : 1 (B) 1 : 3 (C) 2 : 1 (D) 3 : 1"),
    _q(15, "A", 1, "statistics",
       "If the mode of some observations is 10 and the sum of "
       "mean and median is 25, then the mean and median, "
       "respectively, are: (A) 12 and 13 (B) 13 and 12 "
       "(C) 10 and 15 (D) 15 and 10"),
    _q(16, "A", 1, "statistics",
       "If the maximum number of students has obtained 52 marks "
       "out of 80, then: (A) 52 is the mean of the data (B) 52 is "
       "the median of the data (C) 52 is the mode of the data "
       "(D) 52 is the range of the data"),
    _q(17, "A", 1, "pair-of-linear-equations",
       "The system of equations 2x + 1 = 0 and 3y − 5 = 0 has: "
       "(A) unique solution (B) two solutions (C) no solution "
       "(D) infinite number of solutions"),
    _q(18, "A", 1, "introduction-to-trigonometry",
       "In a right ΔABC, right-angled at A, if sin B = 1/4, then "
       "the value of sec B is: (A) 4 (B) √15/4 (C) √15 "
       "(D) 4/√15"),
    _q(19, "A", 1, "real-numbers",
       "Assertion (A): For any two prime numbers p and q, their "
       "HCF is 1 and LCM is p + q. Reason (R): For any two "
       "natural numbers, HCF × LCM = Product of numbers. "
       "(Assertion-Reason question)"),
    _q(20, "A", 1, "probability",
       "Assertion (A): In an experiment of throwing a die, "
       "Event E1: getting a number less than 3 and Event E2: "
       "getting a number greater than 3 are complementary "
       "events. Reason (R): If two events E and F are "
       "complementary events, then P(E) + P(F) = 1. "
       "(Assertion-Reason question)"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "(a) Solve the following pair of equations algebraically: "
       "101x + 102y = 304; 102x + 101y = 305. OR (b) In a pair "
       "of supplementary angles, the greater angle exceeds the "
       "smaller by 50°. Express the given situation as a system "
       "of linear equations in two variables and hence obtain "
       "the measure of each angle."),
    _q(22, "B", 2, "introduction-to-trigonometry",
       "(a) If a sec θ + b tan θ = m and b sec θ + a tan θ = n, "
       "then prove that a² + n² = b² + m². OR (b) Use the "
       "identity sin²A + cos²A = 1 to prove that "
       "tan²A + 1 = sec²A. Hence, find the value of tan A, where "
       "sec A = 5/3 and A is an acute angle."),
    _q(23, "B", 2, "coordinate-geometry",
       "Prove that the abscissa of a point P which is equidistant "
       "from points with coordinates A(7, 1) and B(3, 5) is 2 "
       "more than its ordinate."),
    _q(24, "B", 2, "triangles",
       "P is a point on the side BC of ΔABC such that "
       "∠APC = ∠BAC. Prove that AC² = BC × CP."),
    _q(25, "B", 2, "probability",
       "The number of red balls in a bag is three more than the "
       "number of black balls. If the probability of drawing a "
       "red ball at random from the given bag is 12/23, find "
       "the total number of balls in the given bag."),
    _q(26, "C", 3, "real-numbers",
       "(a) Prove that √5 is an irrational number. OR (b) Let "
       "p, q and r be three distinct prime numbers. Check "
       "whether p·q·r + q is a composite number or not. Further, "
       "give an example for 3 distinct primes p, q and r such "
       "that (i) p·q·r + 1 is a composite number (ii) p·q·r + 1 "
       "is a prime number."),
    _q(27, "C", 3, "polynomials",
       "Find the zeroes of the polynomial p(x) = 3x² − 4x − 4. "
       "Hence, write a polynomial whose each of the zeroes is 2 "
       "more than the zeroes of p(x)."),
    _q(28, "C", 3, "pair-of-linear-equations",
       "Check whether the following pair of equations is "
       "consistent or not. If consistent, solve graphically: "
       "x + 3y = 6; 3y − 2x = −12."),
    _q(29, "C", 3, "coordinate-geometry",
       "If the points A(6, 1), B(p, 2), C(9, 4) and D(7, q) are "
       "the vertices of a parallelogram ABCD, then find the "
       "values of p and q. Hence, check whether ABCD is a "
       "rectangle or not."),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "(a) Prove that (cos θ − 2 cos³θ)/(sin θ − 2 sin³θ) + "
       "cot θ = 0. OR (b) Given that sin θ + cos θ = x, prove "
       "that sin⁴θ + cos⁴θ = [2 − (x² − 1)²]/2."),
    _q(31, "C", 3, "circles",
       "In the given figure, TP and TQ are tangents drawn to a "
       "circle with centre O. If ∠OPQ = 15° and ∠PTQ = θ, then "
       "find the value of sin 2θ."),
    _q(32, "D", 5, "quadratic-equations",
       "(a) There is a circular park of diameter 65 m, where AB "
       "is a diameter. An entry gate is to be constructed at a "
       "point P on the boundary of the park such that the "
       "distance of P from A is 35 m more than the distance of "
       "P from B. Find the distance of point P from A and B, "
       "respectively. OR (b) Find the smallest value of p for "
       "which the quadratic equation x² − 2(p + 1)x + p² = 0 has "
       "real roots. Hence, find the roots of the equation so "
       "obtained."),
    _q(33, "D", 5, "triangles",
       "(a) State and prove the converse of the Basic "
       "Proportionality Theorem: if a line divides any two "
       "sides of a triangle in the same ratio, then the line is "
       "parallel to the third side. OR (b) In the given figure, "
       "ΔCAB is a right triangle, right angled at A, and "
       "AD ⊥ BC. Prove that ΔADB ∼ ΔCDA. Further, if BC = 10 cm "
       "and CD = 2 cm, find the length of AD."),
    _q(34, "D", 5, "surface-areas-and-volumes",
       "From one face of a solid cube of side 14 cm, the largest "
       "possible cone is carved out. Find the volume and surface "
       "area of the remaining solid. (Use π = 22/7)"),
    _q(35, "D", 5, "statistics",
       "The following distribution shows the marks of 230 "
       "students in a particular subject — Marks: 10–20, 20–30, "
       "30–40, 40–50, 50–60, 60–70, 70–80; Number of students: "
       "12, 30, x, 65, y, 25, 18. If the median marks are 46, "
       "then find the values of x and y."),
    _q(36, "E", 4, "areas-related-to-circles",
       "Anurag purchased a farmhouse which is in the form of a "
       "semi-circle of diameter 70 m. He divides it into three "
       "parts by taking a point P on the semi-circle in such a "
       "way that ∠PAB = 30°, where O is the centre of the "
       "semi-circle and AB is the diameter. In part I, he "
       "planted saplings of mango tree, in part II, he grew "
       "tomatoes and in part III, he grew oranges. Based on the "
       "given information, answer the following questions: "
       "(i) What is the measure of ∠POA? (ii) Find the length of "
       "wire needed to fence the entire piece of land. "
       "(iii) (a) Find the area of region in which saplings of "
       "mango tree are planted. OR (b) Find the length of wire "
       "needed to fence region III."),
    _q(37, "E", 4, "arithmetic-progressions",
       "In order to organise the Annual Sports Day, a school "
       "prepared an eight-lane running track with an integrated "
       "football field inside the track area. The length of the "
       "innermost lane of the track is 400 m and each subsequent "
       "lane is 7.6 m longer than the preceding lane. Based on "
       "the given information, answer the following questions, "
       "using the concept of Arithmetic Progression: (i) What "
       "is the length of the 6th lane? (ii) How much longer is "
       "the 8th lane than the 4th lane? (iii) (a) While "
       "practising for a race, a student took one round each in "
       "the first six lanes. Find the total distance covered by "
       "the student. OR (b) A student took one round each in "
       "lanes 4 to 8. Find the total distance covered by the "
       "student."),
    _q(38, "E", 4, "some-applications-of-trigonometry",
       "The Statue of Unity, situated in Gujarat, is the "
       "world's largest statue, which stands over a 58 m high "
       "base. As part of the project, a student constructed an "
       "inclinometer and wishes to find the height of the Statue "
       "of Unity using it. He noted the following observations "
       "from two places: Situation I: The angle of elevation of "
       "the top of the statue from Place A, which is 80√3 m "
       "away from the base of the statue, is found to be 60°. "
       "Situation II: The angle of elevation of the top of the "
       "statue from Place B, which is 40 m above the ground, is "
       "found to be 30°, and the entire height of the statue "
       "including the base is found to be 240 m. Based on the "
       "given information, answer the following questions: "
       "(i) Represent Situation I with the help of a diagram. "
       "(ii) Represent Situation II with the help of a diagram. "
       "(iii) (a) Calculate the height of the statue excluding "
       "the base and also find the height including the base "
       "with the help of Situation I. OR (b) Find the horizontal "
       "distance of Point B (Situation II) from the statue and "
       "the value of tan α, where α is the angle of elevation "
       "of the top of the base of the statue from Point B."),
]


# ---------------------------------------------------------------------------
# CBSE Class 12 Mathematics 2025 — Q.P. Code 65/1/1, Set 1.
# Full text: Collegedunia solved paper, cross-checked question by
# question against PYQ Vault (see source note in the registry entry).
# Q.18 is NOT included; Q.10 and Q.12 are shown without options.
# ---------------------------------------------------------------------------
_CBSE12_2025 = [
    _q(1, "A", 1, "matrices",
       "If A = [[−1, 0, 0], [0, 1, 0], [0, 0, 1]], then A⁻¹ is: "
       "(A) [[−1, 0, 0], [0, −1, 0], [0, 0, −1]] "
       "(B) [[1, 0, 0], [0, −1, 0], [0, 0, −1]] "
       "(C) [[−1, 0, 0], [0, −1, 0], [0, 0, 1]] "
       "(D) [[−1, 0, 0], [0, 1, 0], [0, 0, 1]]"),
    _q(2, "A", 1, "vector-algebra",
       "If vector a = 3î + 2ĵ − k̂ and vector b = î − ĵ + k̂, "
       "then which of the following is correct? (A) a ∥ b "
       "(B) a ⊥ b (C) |a| > |b| (D) |a| = |b|"),
    _q(3, "A", 1, "integrals",
       "∫(−1 to 1) |x|/x dx, x ≠ 0, is equal to: (A) −1 (B) 0 "
       "(C) 1 (D) 2"),
    _q(4, "A", 1, "differential-equations",
       "Which of the following is not a homogeneous function of "
       "x and y? (A) y² − xy (B) x − 3y (C) sin²(y/x) + y/x "
       "(D) tan x − sec y"),
    _q(5, "A", 1, "continuity-and-differentiability",
       "If f(x) = |x| + |x − 1|, then which of the following is "
       "correct? (A) f(x) is both continuous and differentiable "
       "at x = 0 and x = 1 (B) f(x) is differentiable but not "
       "continuous at x = 0 and x = 1 (C) f(x) is continuous "
       "but not differentiable at x = 0 and x = 1 (D) f(x) is "
       "neither continuous nor differentiable at x = 0 and "
       "x = 1"),
    _q(6, "A", 1, "determinants",
       "If A is a square matrix of order 2 such that det(A) = 4, "
       "then det(4 adj A) is equal to: (A) 16 (B) 64 (C) 256 "
       "(D) 512"),
    _q(7, "A", 1, "probability",
       "If E and F are two independent events such that "
       "P(E) = 2/3 and P(F) = 3/7, then P(E | F′) is equal to: "
       "(A) 1/6 (B) 1/2 (C) 2/3 (D) 7/9"),
    _q(8, "A", 1, "application-of-derivatives",
       "The absolute maximum value of the function "
       "f(x) = x³ − 3x + 2 in [0, 2] is: (A) 0 (B) 2 (C) 4 "
       "(D) 5"),
    _q(9, "A", 1, "matrices",
       "Let A = [[1, −2, −1], [0, 4, −1], [−3, 2, 1]], "
       "B = [[−2], [−5], [−7]] and C = [9, 8, 7]. Which of the "
       "following is defined? (A) Only AB (B) Only AC "
       "(C) Only BA (D) All AB, AC and BA"),
    _q(10, "A", 1, "integrals",
       "If ∫ (2^(1/x)/x²) dx = k · 2^(1/x) + C, then k is "
       "equal to:"),
    _q(11, "A", 1, "vector-algebra",
       "If vectors a, b and c satisfy a + b + c = 0, "
       "|a| = √37, |b| = 3 and |c| = 4, then the angle between "
       "b and c is: (A) π/6 (B) π/4 (C) π/3 (D) π/2"),
    _q(12, "A", 1, "differential-equations",
       "The integrating factor of the differential equation "
       "(x + 2y³) dy/dx = 2y is:"),
    _q(13, "A", 1, "matrices",
       "If A = [[7, 0, x], [0, 7, 0], [0, 0, y]] is a scalar "
       "matrix, then y^x is equal to: (A) 0 (B) 1 (C) 7 (D) ±7"),
    _q(14, "A", 1, "linear-programming",
       "The corner points of the feasible region in the "
       "graphical representation of a L.P.P. are (2, 72), "
       "(15, 20) and (40, 15). If Z = 18x + 9y is the objective "
       "function, then: (A) Z is maximum at (2, 72) and minimum "
       "at (15, 20) (B) Z is maximum at (15, 20) and minimum at "
       "(40, 15) (C) Z is maximum at (40, 15) and minimum at "
       "(15, 20) (D) Z is maximum at (40, 15) and minimum at "
       "(2, 72)"),
    _q(15, "A", 1, "matrices",
       "If A and B are invertible matrices, then which of the "
       "following is not correct? (A) (A + B)⁻¹ = B⁻¹ + A⁻¹ "
       "(B) (AB)⁻¹ = B⁻¹A⁻¹ (C) adj(A) = |A| A⁻¹ "
       "(D) |A|⁻¹ = |A⁻¹|"),
    _q(16, "A", 1, "linear-programming",
       "If the feasible region of a linear programming problem "
       "with objective function Z = ax + by is bounded, then "
       "which of the following is correct? (A) It will only "
       "have a maximum value (B) It will only have a minimum "
       "value (C) It will have both maximum and minimum values "
       "(D) It will have neither maximum nor minimum value"),
    _q(17, "A", 1, "application-of-integrals",
       "The area of the shaded region bounded by the curves "
       "y² = x, x = 4 and the x-axis is given by: "
       "(A) ∫(0 to 4) x dx (B) 2∫(0 to 4) √x dx "
       "(C) 4∫(0 to 4) √x dx (D) 4∫(0 to 4) (1/√x) dx"),
    _q(19, "A", 1, "relations-and-functions",
       "Assertion (A): Let Z be the set of integers. A function "
       "f : Z → Z defined as f(x) = 3x − 5, for all x ∈ Z, is "
       "bijective. Reason (R): A function is bijective if it is "
       "both surjective and injective. (Assertion-Reason "
       "question)"),
    _q(20, "A", 1, "continuity-and-differentiability",
       "Assertion (A): f(x) = {3x − 8, x ≤ 5; 2k, x > 5} is "
       "continuous at x = 5 for k = 5/2. Reason (R): For a "
       "function f to be continuous at x = a, "
       "lim (x→a⁻) f(x) = lim (x→a⁺) f(x) = f(a). "
       "(Assertion-Reason question)"),
    _q(21, "B", 2, "continuity-and-differentiability",
       "(a) Differentiate 2^(cos²x) w.r.t. cos²x. OR (b) If "
       "tan⁻¹(x² + y²) = a², then find dy/dx."),
    _q(22, "B", 2, "inverse-trigonometric-functions",
       "Evaluate: tan⁻¹[2 sin(2 cos⁻¹(√3/2))]."),
    _q(23, "B", 2, "vector-algebra",
       "The diagonals of a parallelogram are given by "
       "a = 2î − ĵ + k̂ and b = î + 3ĵ − k̂. Find the area of "
       "the parallelogram."),
    _q(24, "B", 2, "application-of-derivatives",
       "Find the intervals in which the function "
       "f(x) = 5x^(3/2) − 3x^(5/2) is (i) increasing "
       "(ii) decreasing."),
    _q(25, "B", 2, "vector-algebra",
       "(a) Two friends, while flying kites from different "
       "locations, find the strings of their kites crossing "
       "each other. The strings can be represented by vectors "
       "a = 3î + ĵ + 2k̂ and b = 2î − 2ĵ + 4k̂. Determine the "
       "angle formed between the kite strings. Assume there is "
       "no slack in the strings. OR (b) Find a vector of "
       "magnitude 21 units in the direction opposite to that of "
       "vector AB, where A and B are the points A(2, 1, 3) and "
       "B(8, −1, 0) respectively."),
    _q(26, "C", 3, "application-of-derivatives",
       "The side of an equilateral triangle is increasing at "
       "the rate of 3 cm/s. At what rate is its area increasing "
       "when the side of the triangle is 15 cm?"),
    _q(27, "C", 3, "linear-programming",
       "Solve the following linear programming problem "
       "graphically: Maximise Z = x + 2y subject to the "
       "constraints x − y ≥ 0, x − 2y ≥ −2, x ≥ 0, y ≥ 0."),
    _q(28, "C", 3, "integrals",
       "(a) Find: ∫ ((x + sin x)/(1 + cos x)) dx. OR "
       "(b) Evaluate: ∫(0 to π/4) dx/(cos³x √(2 sin 2x))."),
    _q(29, "C", 3, "three-dimensional-geometry",
       "(a) Verify that the lines given by "
       "r = (1 − λ)î + (λ − 2)ĵ + (3 − 2λ)k̂ and "
       "r = (μ + 1)î + (2μ − 1)ĵ − (2μ + 1)k̂ are skew lines. "
       "Hence, find the shortest distance between the lines. "
       "OR (b) During a cricket match, the positions of the "
       "bowler, the wicket keeper and the leg slip fielder are "
       "in a line, given by B = 2î + 8ĵ, W = 6î + 12ĵ and "
       "F = 12î + 18ĵ respectively. Calculate the ratio in "
       "which the wicket keeper divides the line segment "
       "joining the bowler and the leg slip fielder."),
    _q(30, "C", 3, "probability",
       "(a) The probability distribution for the number of "
       "students being absent in a class on a Saturday is as "
       "follows — X: 0, 2, 4, 5; P(X): p, 2p, 3p, p — where X "
       "is the number of students absent. (i) Calculate p. "
       "(ii) Calculate the mean of the number of absent "
       "students on Saturday. OR (b) For a vacancy advertised "
       "in the newspaper, 3000 candidates submitted their "
       "applications. From the data, it was revealed that "
       "two-thirds of the total applicants were females and "
       "the others were males. The selection for the job was "
       "done through a written test. The performance of the "
       "applicants indicates that the probability of a male "
       "getting a distinction in the written test is 0.4 and "
       "that of a female getting a distinction is 0.35. Find "
       "the probability that a candidate chosen at random will "
       "have a distinction in the written test."),
    _q(31, "C", 3, "application-of-integrals",
       "Sketch the graph of y = |x + 3| and find the area of "
       "the region enclosed by the curve and the x-axis, "
       "between x = −6 and x = 0, using integration."),
    _q(32, "D", 5, "continuity-and-differentiability",
       "(a) If √(1 − x²) + √(1 − y²) = a(x − y), then prove "
       "that dy/dx = √((1 − y²)/(1 − x²)). OR (b) If "
       "x = a(cos θ + log tan(θ/2)) and y = sin θ, then find "
       "d²y/dx² at θ = π/4."),
    _q(33, "D", 5, "application-of-derivatives",
       "Find the absolute maximum and absolute minimum of the "
       "function f(x) = 2x³ − 15x² + 36x + 1 on [1, 5]."),
    _q(34, "D", 5, "three-dimensional-geometry",
       "(a) Find the image A′ of the point A(1, 6, 3) in the "
       "line x/1 = (y − 1)/2 = (z − 2)/3. Also, find the "
       "equation of the line joining A and A′. OR (b) Find a "
       "point P on the line (x + 5)/1 = (y + 3)/4 = "
       "(z − 6)/(−9) such that its distance from point "
       "Q(2, 4, −1) is 7 units. Also, find the equation of the "
       "line joining P and Q."),
    _q(35, "D", 5, "matrices",
       "A school wants to allocate students into three clubs — "
       "Sports, Music and Drama — under the following "
       "conditions: the number of students in the Sports club "
       "should be equal to the sum of the number of students "
       "in the Music and Drama clubs; the number of students "
       "in the Music club should be 20 more than half the "
       "number of students in the Sports club; the total "
       "number of students to be allocated in all three clubs "
       "is 180. Find the number of students allocated to "
       "different clubs, using the matrix method."),
    _q(36, "E", 4, "application-of-derivatives",
       "A technical company is designing a rectangular solar "
       "panel installation on a roof using 300 metres of "
       "boundary material. The design includes a partition "
       "running parallel to one of the sides dividing the area "
       "(roof) into two sections. Let the length of the side "
       "perpendicular to the partition be x metres and the "
       "side parallel to the partition be y metres. Based on "
       "this information, answer the following questions: "
       "(i) Write the equation for the total boundary material "
       "used in the boundary and the parallel partition, in "
       "terms of x and y. (ii) Write the area of the solar "
       "panel as a function of x. (iii) (a) Find the critical "
       "points of the area function. Use the second derivative "
       "test to determine the critical point at which the area "
       "is maximum. Also, find the maximum area. OR (b) Using "
       "the first derivative test, calculate the maximum area "
       "the company can enclose with the 300 metres of "
       "boundary material, considering the parallel partition."),
    _q(37, "E", 4, "relations-and-functions",
       "A classroom teacher is keen to assess the learning of "
       "her students on the concept of 'relations' taught to "
       "them. She writes the following five relations, each "
       "defined on the set A = {1, 2, 3}: R1 = {(2, 3), (3, 2)}, "
       "R2 = {(1, 2), (1, 3), (3, 2)}, R3 = {(1, 2), (2, 1), "
       "(1, 1)}, R4 = {(1, 1), (1, 2), (3, 3), (2, 2)}, "
       "R5 = {(1, 1), (1, 2), (3, 3), (2, 2), (2, 1), (2, 3), "
       "(3, 2)}. The students are asked to answer the following "
       "questions about the above relations: (i) Identify the "
       "relation which is reflexive, transitive but not "
       "symmetric. (ii) Identify the relation which is "
       "reflexive and symmetric but not transitive. (iii) (a) "
       "Identify the relations which are symmetric but neither "
       "reflexive nor transitive. OR (b) What pairs should be "
       "added to the relation R2 to make it an equivalence "
       "relation?"),
    _q(38, "E", 4, "probability",
       "A bank offers loans to its customers on different types "
       "of interest rates, namely fixed rate, floating rate and "
       "variable rate. From the past data with the bank, it is "
       "known that a customer avails a loan on fixed rate, "
       "floating rate or variable rate with probabilities 10%, "
       "20% and 70% respectively. A customer, after availing a "
       "loan, can pay the loan or default on loan repayment. "
       "The bank data suggests that the probability that a "
       "person defaults on a loan after availing it at fixed "
       "rate, floating rate and variable rate is 5%, 3% and 1% "
       "respectively. Based on the above information, answer "
       "the following: (i) What is the probability that a "
       "customer, after availing the loan, will default on the "
       "loan repayment? (ii) A customer, after availing the "
       "loan, defaults on loan repayment. What is the "
       "probability that he availed the loan at a variable "
       "rate of interest?"),
]


# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Basic) 2024 — Q.P. Code 430/2/1, Set 1.
# Full text: Vedantu solved paper (see source_url in the registry
# entry). Q.3 and Q.38 are NOT included; Q.5, Q.10 and Q.13 are
# shown without options (see the note in the registry entry).
# ---------------------------------------------------------------------------
_CBSE10_2024_BASIC = [
    _q(1, "A", 1, "real-numbers",
       "The HCF of the smallest 2-digit number and the smallest "
       "composite number is: (A) 2 (B) 20 (C) 40 (D) 4"),
    _q(2, "A", 1, "pair-of-linear-equations",
       "The value of k for which the pair of equations "
       "x + y − 4 = 0 and 2x + ky − 8 = 0 has infinitely many "
       "solutions is: (A) k ≠ 2 (B) k ≠ −2 (C) k = 2 (D) k = −2"),
    _q(4, "A", 1, "arithmetic-progressions",
       "In an AP, if d = −4 and a7 = 4, then the first term a "
       "is: (A) 6 (B) 7 (C) 20 (D) 28"),
    _q(5, "A", 1, "coordinate-geometry",
       "The distance of the point (5, 4) from the origin is:"),
    _q(6, "A", 1, "introduction-to-trigonometry",
       "If sin A = 3/5, then the value of cot A is: (A) 3/4 "
       "(B) 4/3 (C) 4/5 (D) 5/4"),
    _q(7, "A", 1, "introduction-to-trigonometry",
       "The value of (1 + tan²A)/(1 + cot²A) is: (A) sec²A "
       "(B) −1 (C) cot²A (D) tan²A"),
    _q(8, "A", 1, "introduction-to-trigonometry",
       "The value of (2 tan 30°)/(1 − tan²30°) is equal to: "
       "(A) cos 60° (B) sin 60° (C) tan 60° (D) sin 30°"),
    _q(9, "A", 1, "polynomials",
       "The quadratic polynomial, the sum of whose zeroes is "
       "−5 and product of zeroes is 6, is: (A) x² + 5x + 6 "
       "(B) x² − 5x + 6 (C) x² − 5x − 6 (D) −x² + 5x + 6"),
    _q(10, "A", 1, "polynomials",
       "The zeroes of the polynomial 3x² + 11x − 4 are:"),
    _q(11, "A", 1, "statistics",
       "The following distribution shows the daily rainfall "
       "(in mm) in a city — Rainfall: 0–10, 10–20, 20–30, "
       "30–40, 40–50, 50–60; Number of days: 22, 10, 8, 15, 5, "
       "6. The difference of the upper limits of the modal "
       "class and the median class is: (A) 10 (B) 15 (C) 20 "
       "(D) 30"),
    _q(12, "A", 1, "probability",
       "If P(A) denotes the probability of an event A, then: "
       "(A) P(A) < 0 (B) P(A) > 1 (C) 0 ≤ P(A) ≤ 1 "
       "(D) −1 ≤ P(A) ≤ 1"),
    _q(13, "A", 1, "surface-areas-and-volumes",
       "The total surface area of a solid hemisphere of radius "
       "7 cm is:"),
    _q(14, "A", 1, "areas-related-to-circles",
       "The difference of the areas of a minor sector of angle "
       "120° and its corresponding major sector of a circle of "
       "radius 21 cm is: (A) 231 cm² (B) 462 cm² (C) 346.5 cm² "
       "(D) 693 cm²"),
    _q(15, "A", 1, "pair-of-linear-equations",
       "The graph of a pair of linear equations "
       "a1x + b1y + c1 = 0 and a2x + b2y + c2 = 0 represents "
       "parallel lines if: (A) a1/a2 = b1/b2 "
       "(B) a1/a2 = b1/b2 = c1/c2 (C) a1/a2 ≠ b1/b2 "
       "(D) a1/a2 = b1/b2 ≠ c1/c2"),
    _q(16, "A", 1, "circles",
       "In the given figure, tangents PA and PB drawn from a "
       "point P to a circle with centre O are inclined to each "
       "other at an angle of 80°. Then ∠ABO is equal to: "
       "(A) 40° (B) 80° (C) 100° (D) 50°"),
    _q(17, "A", 1, "circles",
       "A line intersecting a circle in two distinct points is "
       "called a: (A) secant (B) chord (C) diameter (D) tangent"),
    _q(18, "A", 1, "some-applications-of-trigonometry",
       "A pole 6 m high casts a shadow 2√3 m long on the "
       "ground. The Sun's angle of elevation is: (A) 30° "
       "(B) 45° (C) 60° (D) 90°"),
    _q(19, "A", 1, "triangles",
       "Assertion (A): A line drawn parallel to one side of a "
       "triangle divides the other two sides in the same ratio. "
       "Reason (R): Parallel lines cannot be drawn to any side "
       "of a triangle. (Assertion-Reason question)"),
    _q(20, "A", 1, "coordinate-geometry",
       "Assertion (A): The point (0, 4) lies on the y-axis. "
       "Reason (R): The x-coordinate of a point lying on the "
       "y-axis is zero. (Assertion-Reason question)"),
    _q(21, "B", 2, "real-numbers",
       "Find the HCF of 84 and 144 by prime factorisation "
       "method."),
    _q(22, "B", 2, "pair-of-linear-equations",
       "(a) The sum of two natural numbers is 70 and their "
       "difference is 10. Find the numbers. OR (b) Solve for "
       "x and y: 2x − 3y = 7; 3x − 3y = 5."),
    _q(23, "B", 2, "probability",
       "15 defective pens are accidentally mixed with 145 good "
       "ones. It is not possible to just look at a pen and tell "
       "whether it is defective or not. One pen is taken out at "
       "random from the lot. Determine the probability that the "
       "pen taken out is a good one."),
    _q(24, "B", 2, "triangles",
       "(a) In the given figure, OA · OB = OC · OD. Prove that "
       "ΔAOD ∼ ΔCOB. OR (b) In the given figure, AD/DB = AE/EC "
       "and ∠ADE = ∠AED. Prove that ΔABC is an isosceles "
       "triangle."),
    _q(25, "B", 2, "circles",
       "Prove that the tangents drawn at the ends of a diameter "
       "of a circle are parallel to each other."),
    _q(26, "C", 3, "probability",
       "Two dice are tossed simultaneously. Find the "
       "probability of getting (a) an even number on both dice "
       "(b) the sum of the numbers on the dice more than 9."),
    _q(27, "C", 3, "circles",
       "(a) Two concentric circles are of radii 5 cm and x cm. "
       "Find the value of x if a chord of the larger circle, "
       "which is of length 24 cm, touches the smaller circle. "
       "OR (b) Prove that the angle between the two tangents "
       "drawn from an external point to a circle is "
       "supplementary to the angle subtended by the line "
       "segment joining the points of contact at the centre."),
    _q(28, "C", 3, "real-numbers",
       "Prove that 7 − 3√5 is an irrational number, given that "
       "√5 is irrational."),
    _q(29, "C", 3, "polynomials",
       "(a) If α and β are the zeroes of the polynomial "
       "x² − 3x + 2, construct a quadratic polynomial whose "
       "zeroes are 2α + 1 and 2β + 1. OR (b) Find the zeroes "
       "of the polynomial 4x² − 4x + 1 and verify the "
       "relationship between the zeroes and the coefficients."),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "Prove that: tan θ/(1 − cot θ) + cot θ/(1 − tan θ) = "
       "1 + sec θ cosec θ."),
    _q(31, "C", 3, "areas-related-to-circles",
       "A car has two wipers which do not overlap. Each wiper "
       "has a blade of length 21 cm sweeping through an angle "
       "of 120°. Find the total area cleaned at each sweep of "
       "the blades."),
    _q(32, "D", 5, "quadratic-equations",
       "A cottage industry produces a certain number of toys "
       "in a day. The cost of production of each toy (in ₹) "
       "was found to be 55 minus the number of toys produced "
       "in a day. On a particular day, the total cost of "
       "production was ₹750. Find the total number of toys "
       "produced on that day."),
    _q(33, "D", 5, "some-applications-of-trigonometry",
       "A TV tower stands vertically on a bank of a canal. "
       "From a point on the other bank exactly opposite the "
       "tower, the angle of elevation of the top of the tower "
       "is 60°. From another point 20 m away from this point "
       "on the line joining this point to the foot of the "
       "tower, the angle of elevation of the top of the tower "
       "is 30°. Find the height of the tower and the width of "
       "the canal. (Use √3 = 1.732)"),
    _q(34, "D", 5, "triangles",
       "(a) In the given figure, altitudes CE and AD of ΔABC "
       "intersect each other at the point P. Show that "
       "(i) ΔAEP ∼ ΔCDP (ii) ΔABD ∼ ΔCBE (iii) ΔAEP ∼ ΔADB. "
       "OR (b) AD and PM are medians of triangles ABC and PQR, "
       "respectively, where ΔABC ∼ ΔPQR. Prove that "
       "AB/PQ = AD/PM."),
    _q(35, "D", 5, "surface-areas-and-volumes",
       "(a) A textile industry runs in a shed. The shed is in "
       "the shape of a cuboid surmounted by a half cylinder. "
       "If the base of the shed is of dimensions 14 m × 20 m "
       "and the height of the cuboidal portion is 7 m, find "
       "the volume of air that the shed can hold. Further, "
       "suppose the machinery in the industry occupies a total "
       "space of 400 m³. Then, how much space is left in the "
       "industry? OR (b) From a solid cylinder of height 8 cm "
       "and radius 6 cm, a conical cavity of the same height "
       "and same radius is carved out. Find the total surface "
       "area of the remaining solid. (Take π = 3.14)"),
    _q(36, "E", 4, "arithmetic-progressions",
       "Saving money is a good habit and it should be "
       "inculcated in children right from the beginning. "
       "Rehan's mother brought a piggy bank for Rehan and puts "
       "one ₹5 coin of her savings in the piggy bank on the "
       "first day. She increases his savings by one ₹5 coin "
       "daily. Based on the above information, answer the "
       "following questions: (i) How many coins were added to "
       "the piggy bank on the 8th day? (ii) How much money "
       "will be there in the piggy bank after 8 days? "
       "(iii) (a) If the piggy bank can hold 120 ₹5 coins in "
       "all, find the number of days she can contribute to put "
       "₹5 coins into it. OR (b) Find the total money saved, "
       "when the piggy bank is full."),
    _q(37, "E", 4, "statistics",
       "The heart rate is one of the 'vital signs' of health "
       "in the human body. It measures the number of times per "
       "minute that the heart contracts or beats. Thirty women "
       "were examined by doctors of AIIMS and the number of "
       "heart beats per minute were recorded and summarised as "
       "follows — Number of heart beats per minute: 65–68, "
       "68–71, 71–74, 74–77, 77–80, 80–83, 83–86; Number of "
       "women: 2, 4, 3, 8, 7, 4, 2. Based on the above "
       "information, answer the following questions: (i) How "
       "many women are having heart beat in the range 68–77? "
       "(ii) What is the median class of heart beats per "
       "minute for these women? (iii) (a) Find the modal value "
       "of heart beats per minute for these women. OR (b) Find "
       "the median value of heart beats per minute for these "
       "women."),
]


# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Standard) 2023 — Q.P. Code 30/1/1, Set 1.
# Full text: Vedantu solved paper, cross-checked against the
# official CBSE marking scheme for paper code 30/1/1 (AglaSem Docs).
# Q.1 is NOT included (see the note in the registry entry).
# ---------------------------------------------------------------------------
_CBSE10_2023 = [
    _q(2, "A", 1, "pair-of-linear-equations",
       "The value of k for which the pair of equations "
       "kx = y + 2 and 6x = 2y + 3 has infinitely many "
       "solutions: (A) is k = 3 (B) does not exist (C) is "
       "k = −3 (D) is k = 4"),
    _q(3, "A", 1, "arithmetic-progressions",
       "If p − 1, p + 1 and 2p + 3 are in A.P., then the value "
       "of p is: (A) −2 (B) 4 (C) 0 (D) 2"),
    _q(4, "A", 1, "coordinate-geometry",
       "In what ratio does the x-axis divide the line segment "
       "joining the points A(3, 6) and B(−12, −3)? (A) 1 : 2 "
       "(B) 1 : 4 (C) 4 : 1 (D) 2 : 1"),
    _q(5, "A", 1, "circles",
       "In the given figure, PQ is tangent to the circle "
       "centred at O. If ∠AOB = 95°, then the measure of "
       "∠ABQ will be: (A) 47.5° (B) 42.5° (C) 85° (D) 95°"),
    _q(6, "A", 1, "introduction-to-trigonometry",
       "If 2 tan A = 3, then the value of (4 sin A + 3 cos A)/"
       "(4 sin A − 3 cos A) is: (A) 7/√13 (B) 1/√13 (C) 3 "
       "(D) does not exist"),
    _q(7, "A", 1, "polynomials",
       "If α and β are the zeroes of a polynomial "
       "p(x) = x² + x − 1, then 1/α + 1/β equals: (A) 1 (B) 2 "
       "(C) −1 (D) −1/2"),
    _q(8, "A", 1, "quadratic-equations",
       "The least positive value of k for which the quadratic "
       "equation 2x² + kx − 4 = 0 has rational roots is: "
       "(A) ±2√2 (B) 2 (C) ±2 (D) √2"),
    _q(9, "A", 1, "introduction-to-trigonometry",
       "(3/4) tan²30° − sec²45° + sin²60° is equal to: "
       "(A) −1 (B) 5/6 (C) −3/2 (D) 1/6"),
    _q(10, "A", 1, "surface-areas-and-volumes",
       "Curved surface area of a cylinder of height 5 cm is "
       "94.2 cm². Radius of the cylinder is (Take π = 3.14): "
       "(A) 2 cm (B) 3 cm (C) 2.9 cm (D) 6 cm"),
    _q(11, "A", 1, "statistics",
       "The distribution below gives the marks obtained by 80 "
       "students on a test — Marks: Less than 10, Less than "
       "20, Less than 30, Less than 40, Less than 50, Less "
       "than 60; Number of students: 3, 12, 27, 57, 75, 80. "
       "The modal class of this distribution is: (A) 10–20 "
       "(B) 20–30 (C) 30–40 (D) 50–60"),
    _q(12, "A", 1, "surface-areas-and-volumes",
       "The curved surface area of a cone having height 24 cm "
       "and radius 7 cm is: (A) 528 cm² (B) 1056 cm² "
       "(C) 550 cm² (D) 500 cm²"),
    _q(13, "A", 1, "coordinate-geometry",
       "The distance between the points (0, 2√5) and "
       "(−2√5, 0) is: (A) 2√10 units (B) 4√10 units "
       "(C) 2√20 units (D) 0 units"),
    _q(14, "A", 1, "polynomials",
       "Which of the following is a quadratic polynomial "
       "having zeroes −2/3 and 2/3? (A) 4x² − 9 (B) 9x² + 4 "
       "(C) x² + 9/4 (D) 5(9x² − 4)"),
    _q(15, "A", 1, "statistics",
       "If the value of each observation of a statistical data "
       "is increased by 3, then the mean of the data: "
       "(A) remains unchanged (B) increases by 3 (C) increases "
       "by 6 (D) increases by 3n"),
    _q(16, "A", 1, "probability",
       "Probability of happening of an event is denoted by p "
       "and probability of non-happening of the event is "
       "denoted by q. Relation between p and q is: "
       "(A) p + q = 1 (B) p = 1, q = 1 (C) p = q − 1 "
       "(D) p + q + 1 = 0"),
    _q(17, "A", 1, "probability",
       "A girl calculates that the probability of her winning "
       "the first prize in a lottery is 0.08. If 6000 tickets "
       "are sold, how many tickets has she bought? (A) 40 "
       "(B) 240 (C) 480 (D) 750"),
    _q(18, "A", 1, "probability",
       "In a group of 20 people, 5 can't swim. If one person "
       "is selected at random, then the probability that "
       "he/she can swim is: (A) 3/4 (B) 1/3 (C) 1 (D) 1/4"),
    _q(19, "A", 1, "coordinate-geometry",
       "Assertion (A): Point P(0, 2) is the point of "
       "intersection of the y-axis with the line 3x + 2y = 4. "
       "Reason (R): The distance of point P(0, 2) from the "
       "x-axis is 2 units. (Assertion-Reason question)"),
    _q(20, "A", 1, "real-numbers",
       "Assertion (A): The perimeter of ΔABC is a rational "
       "number. (In the given figure, ΔABC is right-angled at "
       "B with AB = 2 cm and BC = 3 cm.) Reason (R): The sum "
       "of the squares of two rational numbers is always "
       "rational. (Assertion-Reason question)"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "(a) Solve the pair of equations x = 3 and y = −4 "
       "graphically. OR (b) Using the graphical method, find "
       "whether the following system of linear equations is "
       "consistent or not: x = 0 and y = −7."),
    _q(22, "B", 2, "triangles",
       "In the given figure, XZ is parallel to BC. AZ = 3 cm, "
       "ZC = 2 cm, BM = 3 cm and MC = 5 cm. Find the length of "
       "XY."),
    _q(23, "B", 2, "introduction-to-trigonometry",
       "(a) If sin θ + cos θ = √3, then find the value of "
       "sin θ · cos θ. OR (b) If sin α = 1/√2 and cot β = √3, "
       "then find the value of cosec α + cosec β."),
    _q(24, "B", 2, "real-numbers",
       "Find the greatest number which divides 85 and 72 "
       "leaving remainders 1 and 2 respectively."),
    _q(25, "B", 2, "probability",
       "A bag contains 4 red, 3 blue and 2 yellow balls. One "
       "ball is drawn at random from the bag. Find the "
       "probability that the drawn ball is (i) red "
       "(ii) yellow."),
    _q(26, "C", 3, "pair-of-linear-equations",
       "Half of the difference between two numbers is 2. The "
       "sum of the greater number and twice the smaller number "
       "is 13. Find the numbers."),
    _q(27, "C", 3, "real-numbers",
       "Prove that √5 is an irrational number."),
    _q(28, "C", 3, "coordinate-geometry",
       "If (−5, 3) and (5, 3) are two vertices of an "
       "equilateral triangle, then find the coordinates of "
       "the third vertex, given that the origin lies inside "
       "the triangle. (Take √3 = 1.7)"),
    _q(29, "C", 3, "circles",
       "(a) Two tangents TP and TQ are drawn to a circle with "
       "centre O from an external point T. Prove that "
       "∠PTQ = 2∠OPQ. OR (b) In the given figure, a circle is "
       "inscribed in a quadrilateral ABCD in which ∠B = 90°. "
       "If AD = 17 cm, AB = 20 cm and DS = 3 cm, find the "
       "radius of the circle."),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "Prove that: (tan θ + sec θ − 1)/(tan θ − sec θ + 1) = "
       "(1 + sin θ)/cos θ."),
    _q(31, "C", 3, "surface-areas-and-volumes",
       "(a) A room is in the form of a cylinder surmounted by "
       "a hemispherical dome. The base radius of the "
       "hemisphere is one-half the height of the cylindrical "
       "part. Find the total height of the room if it contains "
       "1408/21 m³ of air. (Take π = 22/7) OR (b) An empty "
       "cone is of radius 3 cm and height 12 cm. Ice cream is "
       "filled in it so that the lower part of the cone, which "
       "is 1/6 of the volume of the cone, is unfilled, but a "
       "hemisphere is formed on the top. Find the volume of "
       "the ice cream. (Take π = 3.14)"),
    _q(32, "D", 5, "triangles",
       "If a line is drawn parallel to one side of a triangle "
       "to intersect the other two sides at distinct points, "
       "prove that the other two sides are divided in the same "
       "ratio."),
    _q(33, "D", 5, "some-applications-of-trigonometry",
       "(a) The angle of elevation of the top of a tower 24 m "
       "high from the foot of another tower in the same plane "
       "is 60°. The angle of elevation of the top of the "
       "second tower from the foot of the first tower is 30°. "
       "Find the distance between the two towers and the "
       "height of the other tower. Also, find the length of "
       "the wire attached to the tops of both the towers. OR "
       "(b) A spherical balloon of radius r subtends an angle "
       "of 60° at the eye of an observer. If the angle of "
       "elevation of its centre is 45° from the same point, "
       "prove that the height of the centre of the balloon is "
       "√2 times its radius."),
    _q(34, "D", 5, "areas-related-to-circles",
       "A chord of a circle of radius 14 cm subtends an angle "
       "of 60° at the centre. Find the area of the "
       "corresponding minor segment of the circle. Also, find "
       "the area of the major segment of the circle."),
    _q(35, "D", 5, "arithmetic-progressions",
       "(a) The ratio of the 11th term to the 17th term of an "
       "A.P. is 3 : 4. Find the ratio of the 5th term to the "
       "21st term of the same A.P. Also, find the ratio of the "
       "sum of first 5 terms to that of first 21 terms. OR "
       "(b) 250 logs are stacked in the following manner: 22 "
       "logs in the bottom row, 21 in the next row, 20 in the "
       "row next to it, and so on. In how many rows are the "
       "250 logs placed and how many logs are there in the top "
       "row?"),
    _q(36, "E", 4, "quadratic-equations",
       "While designing the school year book, a teacher asked "
       "the student that the length and width of a particular "
       "photo is increased by x units each to double the area "
       "of the photo. The original photo is 18 cm long and 12 "
       "cm wide. Based on the above information, answer the "
       "following questions: (i) Write an algebraic equation "
       "depicting the above information. (ii) Write the "
       "corresponding quadratic equation in standard form. "
       "(iii) What should be the new dimensions of the "
       "enlarged photo? OR Can any rational value of x make "
       "the new area equal to 220 cm²?"),
    _q(37, "E", 4, "statistics",
       "The India Meteorological Department observes seasonal "
       "and annual rainfall every year in different "
       "sub-divisions of our country. It helps them to compare "
       "and analyse the results. The table given below shows "
       "sub-division-wise seasonal (monsoon) rainfall (mm) in "
       "2018 — Rainfall (mm): 200–400, 400–600, 600–800, "
       "800–1000, 1000–1200, 1200–1400, 1400–1600, 1600–1800; "
       "Number of sub-divisions: 2, 4, 7, 4, 2, 3, 1, 1. "
       "Based on the above information, answer the following "
       "questions: (i) Write the modal class. (ii) Find the "
       "median of the given data. (iii) Find the mean "
       "rainfall in this season. OR (iii) If a sub-division "
       "having at least 1000 mm rainfall during the monsoon "
       "season is considered a good rainfall sub-division, "
       "then how many sub-divisions had good rainfall?"),
    _q(38, "E", 4, "circles",
       "The discus throw is an event in which an athlete "
       "attempts to throw a discus. The athlete spins "
       "anti-clockwise around one and a half times through a "
       "circle, then releases the throw. When released, the "
       "discus travels along the tangent to the circular spin "
       "orbit. In the given figure, AB is one such tangent to "
       "a circle of radius 75 cm. Point O is the centre of "
       "the circle and ∠ABO = 30°. PQ is parallel to OA. "
       "Based on the above information, answer the following "
       "questions: (a) Find the length of AB. (b) Find the "
       "length of OB. (c) Find the length of AP. OR Find the "
       "length of PQ."),
]

# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Basic) 2025 — Q.P. Code 430/1/1,
# Series GE1FH, Set 1.
# Full text: CogniCraft solved paper (see source_url in the entry
# below), cross-checked against the Swavid paper for the same code.
# All 38 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_CBSE10_2025_BASIC = [
    _q(1, "A", 1, "real-numbers",
       "If the HCF of two positive integers a and b is 1, then their LCM "
       "is: (A) a + b (B) a (C) b (D) ab"),
    _q(2, "A", 1, "real-numbers",
       "The number 3 + √2 is: (A) a rational number (B) an irrational "
       "number (C) an integer (D) a natural number"),
    _q(3, "A", 1, "quadratic-equations",
       "The discriminant of the quadratic equation x2 - 3x - 2 = 0 is: (A) "
       "1 (B) 17 (C) √17 (D) -√17"),
    _q(4, "A", 1, "quadratic-equations",
       "The equation x + 1/x = 3 (x ≠ 0) is expressed as a quadratic "
       "equation in the form ax2 + bx + c = 0. The value of a - b + c is: "
       "(A) 5 (B) 2 (C) 1 (D) -1"),
    _q(5, "A", 1, "coordinate-geometry",
       "For a point (3, -5), the value of (abscissa - ordinate) is: (A) -8 "
       "(B) -2 (C) 2 (D) 8"),
    _q(6, "A", 1, "coordinate-geometry",
       "The mid-point of a line segment divides the line segment in the "
       "ratio: (A) 1 : 2 (B) 2 : 1 (C) 1 : 1 (D) 1/2 : 2"),
    _q(7, "A", 1, "triangles",
       "Which of the following is not the criterion for similarity of "
       "triangles? (A) AAA (B) SSS (C) SAS (D) RHS"),
    _q(8, "A", 1, "triangles",
       "In the given figure, triangle ABC has AB = 3.8 cm, BC = 6 cm, AC = "
       "3√3 cm, angle A = 80° and angle B = 60°, and triangle PQR has PQ = "
       "12 cm, QR = 7.6 cm and PR = 6√3 cm. Which of the following is true "
       "about the measure of angle P? (A) angle P = 60° (B) angle P = 80° "
       "(C) angle P = 40° (D) The measure of angle P cannot be determined"),
    _q(9, "A", 1, "circles",
       "In the given figure, PA is a tangent to a circle with centre O, OP "
       "= 10 cm and angle OPA = 30°. Then the length of AP is: (A) 10√3 cm "
       "(B) 20 cm (C) 5 cm (D) 5√3 cm"),
    _q(10, "A", 1, "introduction-to-trigonometry",
       "Which of the following statements is false? (A) tan 45° = cot 45° "
       "(B) sin 90° = tan 45° (C) sin 30° = cos 30° (D) sin 45° = cos 45°"),
    _q(11, "A", 1, "introduction-to-trigonometry",
       "The value of (tan2 A - 1/cos2 A) is: (A) more than 1 (B) 1 (C) 0 "
       "(D) -1"),
    _q(12, "A", 1, "some-applications-of-trigonometry",
       "In the given figure, an observer at the top of a vertical line "
       "looks down at an object on the ground; a dashed horizontal line "
       "runs from the observer; angle z is between the horizontal line and "
       "the line of sight, angle y is between the vertical and the line of "
       "sight, angle x is at the object, and angle a is the right angle at "
       "the base. Which of the following angles represents the angle of "
       "depression? (A) x (B) y (C) z (D) a"),
    _q(13, "A", 1, "areas-related-to-circles",
       "In the given figure, a circle has centre O; two radii of length r "
       "meet a chord of length a, and the shaded region is the triangle "
       "formed by the two radii and the chord together with the segment "
       "below the chord (i.e. a sector of the circle), the arc having "
       "length l. The perimeter of the shaded region is: (A) l (B) l + a "
       "(C) l + 2r (D) l + 2r + a"),
    _q(14, "A", 1, "areas-related-to-circles",
       "The ratio of the area of a quadrant of a circle to the area of the "
       "same circle is: (A) 1 : 2 (B) 2 : 1 (C) 1 : 4 (D) 4 : 1"),
    _q(15, "A", 1, "surface-areas-and-volumes",
       "For which of the following solids is the lateral/curved surface "
       "area and total surface area the same? (A) Cube (B) Cuboid (C) "
       "Hemisphere (D) Sphere"),
    _q(16, "A", 1, "statistics",
       "The class mark of the median class of the following data is: Class "
       "interval: 10-25, 25-40, 40-55, 55-70, 70-85, 85-100; Frequency: 2, "
       "3, 7, 6, 6, 6. (A) 40 (B) 55 (C) 47.5 (D) 62.5"),
    _q(17, "A", 1, "statistics",
       "The following distribution shows the number of runs scored by some "
       "batsmen in test matches: Runs scored: 3000-4000, 4000-5000, "
       "5000-6000, 6000-7000; Number of batsmen: 5, 10, 9, 8. The lower "
       "limit of the modal class is: (A) 3000 (B) 4000 (C) 5000 (D) 6000"),
    _q(18, "A", 1, "probability",
       "In a random experiment of throwing a die, which of the following "
       "is a sure event? (A) Getting a number between 1 and 6 (B) Getting "
       "an odd number < 7 (C) Getting an even number < 7 (D) Getting a "
       "natural number < 7"),
    _q(19, "A", 1, "real-numbers",
       "Assertion (A): For any two natural numbers a and b, the HCF of a "
       "and b is a factor of the LCM. Reason (R): HCF of any two natural "
       "numbers divides both the numbers. (A) Both A and R are true and R "
       "is the correct explanation of A (B) Both A and R are true, but R "
       "is not the correct explanation of A (C) A is true, but R is false "
       "(D) A is false, but R is true"),
    _q(20, "A", 1, "pair-of-linear-equations",
       "Assertion (A): The value of p for which the system of equations 4x "
       "+ py + 8 = 0 and 2x + 2y + 2 = 0 is consistent is 4. Reason (R): "
       "The system of equations a1x + b1y = c1 and a2x + b2y = c2 is "
       "consistent with infinitely many solutions, if a1/a2 = b1/b2 = "
       "c1/c2. (A) Both A and R are true and R is the correct explanation "
       "of A (B) Both A and R are true, but R is not the correct "
       "explanation of A (C) A is true, but R is false (D) A is false, but "
       "R is true"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "Solve the following system of equations for x and y: x/2 + 2y/3 = "
       "-1 and x - y/3 = 3."),
    _q(22, "B", 2, "triangles",
       "(a) In the given figure, lines PS and QR cross at O with PQ "
       "parallel to RS; if PQ || RS, then prove that triangle POQ ~ "
       "triangle SOR. OR (b) In the given figure, triangle OSR ~ triangle "
       "OQP, angle ROQ = 125° and angle ORS = 70°. Find the measures of "
       "angle OSR and angle OQP."),
    _q(23, "B", 2, "circles",
       "Two concentric circles are of radii 6 cm and 10 cm. Find the "
       "length of the chord of the larger circle which touches the smaller "
       "circle."),
    _q(24, "B", 2, "introduction-to-trigonometry",
       "(a) Find the values of A and B (0° ≤ A < 90°, 0° ≤ B < 90°), if "
       "tan(A + B) = 1 and tan(A - B) = 1/√3. OR (b) Prove that tan 45° = "
       "1 geometrically."),
    _q(25, "B", 2, "areas-related-to-circles",
       "A chord of a circle of diameter 20 cm subtends an angle of 60° at "
       "the centre of the circle. Find the area of the corresponding minor "
       "segment of the circle. (Use π = 3.14 and √3 = 1.73)"),
    _q(26, "C", 3, "real-numbers",
       "(a) Prove that √3 is an irrational number. OR (b) The factor tree "
       "of a number x is as follows: x splits into 2 and y; y splits into "
       "2 and 210; 210 splits into a and 70; 70 splits into 2 and 35; 35 "
       "splits into 5 and b. Find the values of x, y, a and b. Hence, "
       "write the product of the prime factors of the number x so "
       "obtained."),
    _q(27, "C", 3, "polynomials",
       "Find a quadratic polynomial whose sum and product of zeroes are 0 "
       "and -9, respectively. Also, find the zeroes of the polynomial so "
       "obtained."),
    _q(28, "C", 3, "pair-of-linear-equations",
       "(a) Solve the following system of equations graphically: x + 3y = "
       "6; 2x - 3y = 12. OR (b) x and y are complementary angles such that "
       "x : y = 1 : 2. Express the given information as a system of linear "
       "equations in two variables and hence solve it."),
    _q(29, "C", 3, "circles",
       "Prove that a rectangle circumscribing a circle is a square."),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "Prove that: (1 + cot2 A)/(1 + tan2 A) = ((1 - cot A)/(1 - tan A))2"),
    _q(31, "C", 3, "probability",
       "A lot consists of 200 pens of which 180 are good and the rest are "
       "defective. A customer will buy a pen if it is not defective. The "
       "shopkeeper draws a pen at random and gives it to the customer. "
       "What is the probability that the customer will not buy it? Another "
       "lot of 100 pens containing 80 good pens is mixed with the previous "
       "lot of 200 pens. The shopkeeper now draws one pen at random from "
       "the entire lot and gives it to the customer. What is the "
       "probability that the customer will buy the pen?"),
    _q(32, "D", 5, "quadratic-equations",
       "(a) The difference of the squares of two positive numbers is 180. "
       "The square of the smaller number is 8 times the greater number. "
       "Find the two numbers. OR (b) Find the value(s) of k for which the "
       "equation 2x2 + kx + 3 = 0 has real and equal roots. Hence, find "
       "the roots of the equations so obtained."),
    _q(33, "D", 5, "triangles",
       "State 'Basic Proportionality Theorem' and use it to prove the "
       "following: In a quadrilateral ABCD, diagonals AC and BD intersect "
       "each other at O such that AO/BO = CO/DO, as shown in the given "
       "figure. Prove that ABCD is a trapezium."),
    _q(34, "D", 5, "surface-areas-and-volumes",
       "(a) A toy is in the form of a cone surmounted on a hemisphere. The "
       "cone and hemisphere have the same radii. The height of the conical "
       "part of the toy is equal to the diameter of its base. If the "
       "radius of the conical part is 5 cm, find the volume of the toy. OR "
       "(b) A cubical block is surmounted by a hemisphere of radius 3.5 "
       "cm. What is the smallest possible length of the edge of the cube "
       "so that the hemisphere can totally lie on the cube? Find the total "
       "surface area of the solid so formed."),
    _q(35, "D", 5, "statistics",
       "The following data gives the information on the observed lifetime "
       "(in hours) of 200 electrical components: Lifetime (in hours): "
       "0-20, 20-40, 40-60, 60-80, 80-100, 100-120; Number of electrical "
       "components: 10, 35, 50, 60, 30, 15. Find the mean lifetime (in "
       "hours) of the electrical components."),
    _q(36, "E", 4, "some-applications-of-trigonometry",
       "Case study: An injured bird was found on the roof of a building. "
       "The building is 15 m high. A fireman was called to rescue the "
       "bird. The fireman used an adjustable ladder to reach the roof. He "
       "placed the ladder in such a way that the ladder makes an angle of "
       "60° with the ground in order to reach the roof. (i) Find the "
       "length of the ladder used by the fireman to reach the roof. (ii) "
       "Find the distance of the point on the ground at which the ladder "
       "was fixed from the bottom of the building. (iii) In order to avoid "
       "skidding, the fireman placed the ladder in such a way that the "
       "bottom of the ladder touches the base of the wall which is "
       "opposite to the building, making an angle of 30° with the ground. "
       "(a) Draw a neat diagram to represent the above situation and hence "
       "find the width of the road between the building and the wall. OR "
       "(b) Find the length of the ladder used by the fireman in this "
       "case."),
    _q(37, "E", 4, "arithmetic-progressions",
       "Case study: In a garden, saplings of rose flowers were planted at "
       "equal intervals to form a spiral pattern. The spiral is made up of "
       "successive semicircles, with centres alternately at A and B, "
       "starting with centre at A, of radii 50 cm, 100 cm, 150 cm, ....... "
       "Spiral 1 has 10 flowers, Spiral 2 has 20 flowers, Spiral 3 has 30 "
       "flowers and so on. (i) What is the radius of the 13th spiral? (ii) "
       "If the radius of the nth spiral is 500 cm, find the value of n. "
       "(iii) (a) Find the total number of saplings till the 11th spiral. "
       "OR (b) Till which spiral, will there be a total of 450 saplings?"),
    _q(38, "E", 4, "coordinate-geometry",
       "Case study: In a society, there is a circular park having two "
       "gates. The gates are placed at points A(10, 20) and B(50, 50), as "
       "shown in the figure below (AB is a diameter of the circle). Two "
       "fountains are installed at points P and Q on AB such that AP = PQ "
       "= QB. (i) Find the coordinates of the centre C. (ii) Find the "
       "radius of the circular park. (iii) (a) Find the coordinates of the "
       "point P. OR (b) Find the distance of the fountain at Q from gate "
       "A."),
]

# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Standard) 2020 — Q.P. Code 30/1/1,
# Series JBB/1, Set 1.
# Full text: LearnCBSE (see source_url in the entry below); the
# questions LearnCBSE redacts as out-of-syllabus were recovered
# from the Oswaal Solved Paper 2020 for the same code and
# cross-checked against NotesBazar's paper for the same code.
# All 40 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_CBSE10_2020 = [
    _q(1, "A", 1, "polynomials",
       "If one of the zeroes of the quadratic polynomial x2 + 3x + k is 2, "
       "then the value of k is (A) 10 (B) -10 (C) -7 (D) -2"),
    _q(2, "A", 1, "real-numbers",
       "The total number of factors of a prime number is (A) 1 (B) 0 (C) 2 "
       "(D) 3"),
    _q(3, "A", 1, "polynomials",
       "The quadratic polynomial, the sum of whose zeroes is -5 and their "
       "product is 6, is (A) x2 + 5x + 6 (B) x2 - 5x + 6 (C) x2 - 5x - 6 "
       "(D) -x2 + 5x + 6"),
    _q(4, "A", 1, "pair-of-linear-equations",
       "The value of k for which the system of equations x + y - 4 = 0 and "
       "2x + ky = 3, has no solution, is (A) -2 (B) ≠ 2 (C) 3 (D) 2"),
    _q(5, "A", 1, "real-numbers",
       "The HCF and LCM of 12, 21, 15 respectively are (A) 3, 140 (B) 12, "
       "420 (C) 3, 420 (D) 420, 3"),
    _q(6, "A", 1, "arithmetic-progressions",
       "The value of x for which 2x, (x + 10) and (3x + 2) are the three "
       "consecutive terms of an AP, is (A) 6 (B) -6 (C) 18 (D) -18"),
    _q(7, "A", 1, "arithmetic-progressions",
       "The first term of an AP is p and the common difference is q, then "
       "its 10th term is (A) q + 9p (B) p - 9q (C) p + 9q (D) 2p + 9q"),
    _q(8, "A", 1, "coordinate-geometry",
       "The distance between the points (a cos θ + b sin θ, 0) and (0, a "
       "sin θ - b cos θ) is (A) a2 + b2 (B) a2 - b2 (C) √(a2 + b2) (D) "
       "√(a2 - b2)"),
    _q(9, "A", 1, "coordinate-geometry",
       "If the point P(k, 0) divides the line segment joining the points "
       "A(2, -2) and B(-7, 4) in the ratio 1 : 2, then the value of k is "
       "(A) 1 (B) 2 (C) -2 (D) -1"),
    _q(10, "A", 1, "coordinate-geometry",
       "The value of p, for which the points A(3, 1), B(5, p) and C(7, -5) "
       "are collinear, is (A) -2 (B) 2 (C) -1 (D) 1"),
    _q(11, "A", 1, "circles",
       "In Fig. 1, triangle ABC is circumscribing a circle, with AR = 4 "
       "cm, AC = 11 cm and BP = 3 cm (P, Q, R being the points of contact "
       "on BC, CA, AB respectively as shown in the figure). The length of "
       "BC is ______ cm."),
    _q(12, "A", 1, "triangles",
       "Given triangle ABC ~ triangle PQR, if AB/PQ = 1/3, then "
       "ar(triangle ABC)/ar(triangle PQR) = ______."),
    _q(13, "A", 1, "triangles",
       "Triangle ABC is an equilateral triangle of side 2a, then length of "
       "one of its altitude is ______."),
    _q(14, "A", 1, "introduction-to-trigonometry",
       "cos 80°/sin 10° + cos 59° cosec 31° = ______."),
    _q(15, "A", 1, "introduction-to-trigonometry",
       "The value of (sin2 θ + 1/(1 + tan2 θ)) = ______. OR The value of "
       "(1 + tan2 θ)(1 - sin θ)(1 + sin θ) = ______."),
    _q(16, "A", 1, "some-applications-of-trigonometry",
       "The ratio of the length of a vertical rod and the length of its "
       "shadow is 1 : √3. Find the angle of elevation of the sun at that "
       "moment?"),
    _q(17, "A", 1, "surface-areas-and-volumes",
       "Two cones have their heights in the ratio 1 : 3 and radii in the "
       "ratio 3 : 1. What is the ratio of their volumes?"),
    _q(18, "A", 1, "probability",
       "A letter of English alphabet is chosen at random. What is the "
       "probability that the chosen letter is a consonant?"),
    _q(19, "A", 1, "probability",
       "A die is thrown once. What is the probability of getting a number "
       "less than 3? OR If the probability of winning a game is 0.07, what "
       "is the probability of losing it?"),
    _q(20, "A", 1, "statistics",
       "If the mean of the first n natural numbers is 15, then find n."),
    _q(21, "B", 2, "arithmetic-progressions",
       "Show that (a - b)2, (a2 + b2) and (a + b)2 are in AP."),
    _q(22, "B", 2, "triangles",
       "In Fig., DE || AC and DC || AP. Prove that BE/EC = BC/CP. OR In "
       "Fig., two tangents TP and TQ are drawn to a circle with centre O "
       "from an external point T. Prove that angle PTQ = 2 angle OPQ."),
    _q(23, "B", 2, "introduction-to-trigonometry",
       "The rod AC of a TV disc antenna is fixed at right angle to the "
       "wall AB and a rod CD is supporting the disc as shown in Fig. If AC "
       "= 1.5 m long and CD = 3 m, find (i) tan θ (ii) sec θ + cosec θ."),
    _q(24, "B", 2, "areas-related-to-circles",
       "A piece of wire 22 cm long is bent into the form of an arc of a "
       "circle subtending an angle of 60° at its centre. Find the radius "
       "of the circle. [Use π = 22/7]"),
    _q(25, "B", 2, "probability",
       "If a number x is chosen at random from the numbers -3, -2, -1, 0, "
       "1, 2, 3, what is the probability that x2 ≤ 4?"),
    _q(26, "B", 2, "statistics",
       "Find the mean of the following distribution: Class: 3-5, 5-7, 7-9, "
       "9-11, 11-13; Frequency: 5, 10, 10, 7, 8. OR Find the mode of the "
       "following data: Class: 0-20, 20-40, 40-60, 60-80, 80-100, 100-120, "
       "120-140; Frequency: 6, 8, 10, 12, 6, 5, 3."),
    _q(27, "C", 3, "polynomials",
       "(a) Find a quadratic polynomial whose zeroes are reciprocals of "
       "the zeroes of the polynomial f(x) = ax2 + bx + c, a ≠ 0, c ≠ 0. OR "
       "(b) Divide the polynomial f(x) = 3x2 - x3 - 3x + 5 by the "
       "polynomial g(x) = x - 1 - x2 and verify the division algorithm."),
    _q(28, "C", 3, "pair-of-linear-equations",
       "(a) Determine graphically the coordinates of the vertices of a "
       "triangle, the equations of whose sides are given by 2y - x = 8, 5y "
       "- x = 14 and y - 2x = 1. OR (b) If 4 is a zero of the cubic "
       "polynomial x3 - 3x2 - 10x + 24, find its other two zeroes."),
    _q(29, "C", 3, "quadratic-equations",
       "In a flight of 600 km, an aircraft was slowed due to bad weather. "
       "Its average speed for the trip was reduced by 200 km/hr and time "
       "of flight increased by 30 minutes. Find the original duration of "
       "flight."),
    _q(30, "C", 3, "coordinate-geometry",
       "(a) Find the area of triangle PQR formed by the points P(-5, 7), "
       "Q(-4, -5) and R(4, 5). OR (b) If the point C(-1, 2) divides "
       "internally the line segment joining A(2, 5) and B(x, y) in the "
       "ratio 3 : 4, find the coordinates of B."),
    _q(31, "C", 3, "triangles",
       "In Fig., angle D = angle E and AD/DB = AE/EC, prove that BAC is an "
       "isosceles triangle."),
    _q(32, "C", 3, "triangles",
       "In a triangle, if square of one side is equal to the sum of the "
       "squares of the other two sides, then prove that the angle opposite "
       "to the first side is a right angle."),
    _q(33, "C", 3, "introduction-to-trigonometry",
       "If sin θ + cos θ = √3, then prove that tan θ + cot θ = 1."),
    _q(34, "C", 3, "surface-areas-and-volumes",
       "A cone of base radius 4 cm is divided into two parts by drawing a "
       "plane through the mid-point of its height and parallel to its "
       "base. Compare the volume of the two parts."),
    _q(35, "D", 4, "real-numbers",
       "Show that the square of any positive integer cannot be of the form "
       "(5q + 2) or (5q + 3) for any integer q. OR Prove that one of every "
       "three consecutive positive integers is divisible by 3."),
    _q(36, "D", 4, "arithmetic-progressions",
       "The sum of four consecutive numbers in AP is 32 and the ratio of "
       "the product of the first and last terms to the product of two "
       "middle terms is 7 : 15. Find the numbers. OR Solve: 1 + 4 + 7 + 10 "
       "+ … + x = 287."),
    _q(37, "D", 4, "circles",
       "Draw a line segment AB of length 7 cm. Taking A as centre, draw a "
       "circle of radius 3 cm and taking B as centre, draw another circle "
       "of radius 2 cm. Construct tangents to each circle from the centre "
       "of the other circle."),
    _q(38, "D", 4, "some-applications-of-trigonometry",
       "A vertical tower stands on a horizontal plane and is surmounted by "
       "a vertical flag-staff of height 6 m. At a point on the plane, the "
       "angle of elevation of the bottom and top of the flag-staff are 30° "
       "and 45° respectively. Find the height of the tower. (Take √3 = "
       "1.73)"),
    _q(39, "D", 4, "surface-areas-and-volumes",
       "A bucket in the form of a frustum of a cone of height 30 cm with "
       "radii of its lower and upper ends as 10 cm and 20 cm, "
       "respectively. Find the capacity of the bucket. Also find the cost "
       "of milk which can completely fill the bucket at the rate of Rs. 40 "
       "per litre. (Use π = 22/7)"),
    _q(40, "D", 4, "statistics",
       "(a) The following table gives production yield per hectare (in "
       "quintals) of wheat of 100 farms of a village: Production "
       "yield/hect.: 40-45, 45-50, 50-55, 55-60, 60-65, 65-70; No. of "
       "farms: 4, 6, 16, 20, 30, 24. Change the distribution to 'a more "
       "than' type distribution and draw its ogive. OR (b) The median of "
       "the following data is 525. Find the values of x and y, if total "
       "frequency is 100: Class: 0-100, 100-200, 200-300, 300-400, "
       "400-500, 500-600, 600-700, 700-800, 800-900, 900-1000; Frequency: "
       "2, 5, x, 12, 17, 20, y, 9, 7, 4."),
]

# ---------------------------------------------------------------------------
# CBSE Class 10 Mathematics (Standard) 2022, Term 2 — Q.P. Code
# 30/1/1, Series PPQQA/1, Set 1.
# Full text: AglaSem Docs (see source_url in the entry below),
# cross-checked against NetExplanations and CareerPower solutions
# for the same series/code.
# All 14 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_CBSE10_2022_TERM2 = [
    _q(1, "A", 2, "arithmetic-progressions",
       "(a) Find the sum of first 30 terms of AP : -30, -24, -18, ..... . "
       "OR (b) In an AP if Sn = n (4n + 1), then find the AP."),
    _q(2, "A", 2, "surface-areas-and-volumes",
       "A solid metallic sphere of radius 10.5 cm is melted and recast "
       "into a number of smaller cones, each of radius 3.5 cm and height 3 "
       "cm. Find the number of cones so formed."),
    _q(3, "A", 2, "quadratic-equations",
       "(a) Find the value of m for which the quadratic equation (m - 1) "
       "x² + 2 (m - 1) x + 1 = 0 has two real and equal roots. OR (b) "
       "Solve the following quadratic equation for x : √3 x² + 10x + 7√3 = "
       "0."),
    _q(4, "A", 2, "statistics",
       "Find the mode of the following frequency distribution : Class 10 - "
       "20, 20 - 30, 30 - 40, 40 - 50, 50 - 60; Frequency 15, 10, 12, 17, "
       "4."),
    _q(5, "A", 2, "quadratic-equations",
       "The product of Rehan's age (in years) 5 years ago and his age 7 "
       "years from now, is one more than twice his present age. Find his "
       "present age."),
    _q(6, "A", 2, "circles",
       "Two concentric circles are of radii 4 cm and 3 cm. Find the length "
       "of the chord of the larger circle which touches the smaller "
       "circle."),
    _q(7, "B", 3, "statistics",
       "For what value of x, is the median of the following frequency "
       "distribution 34.5 ? Class 0 - 10, 10 - 20, 20 - 30, 30 - 40, 40 - "
       "50, 50 - 60, 60 - 70; Frequency 3, 5, 11, 10, x, 3, 2."),
    _q(8, "B", 3, "circles",
       "Draw a circle of radius 3 cm. Take two points P and Q on one of "
       "its extended diameter each at a distance of 7 cm from its centre. "
       "Construct tangents to the circle from these two points P and Q."),
    _q(9, "B", 3, "some-applications-of-trigonometry",
       "(a) The angle of elevation of the top of a building from the foot "
       "of the tower is 30° and the angle of elevation of the top of the "
       "tower from the foot of the building is 60°. If the tower is 50 m "
       "high, then find the height of the building. OR (b) From a point on "
       "a bridge across a river, the angles of depression of the banks on "
       "opposite sides of the river are 30° and 45° respectively. If the "
       "bridge is at a height of 3 m from the banks, then find the width "
       "of the river."),
    _q(10, "B", 3, "statistics",
       "Following is the daily expenditure on lunch by 30 employees of a "
       "company : Daily Expenditure (in Rupees) 100 - 120, 120 - 140, 140 "
       "- 160, 160 - 180, 180 - 200; Number of Employees 8, 3, 8, 6, 5. "
       "Find the mean daily expenditure of the employees."),
    _q(11, "C", 4, "surface-areas-and-volumes",
       "(a) From a solid cylinder of height 30 cm and radius 7 cm, a "
       "conical cavity of height 24 cm and same radius is hollowed out. "
       "Find the total surface area of the remaining solid. OR (b) Water "
       "in a canal, 8 m wide and 6 m deep, is flowing with a speed of 12 "
       "km/hour. How much area will it irrigate in one hour, if 0.05 m of "
       "standing water is required ?"),
    _q(12, "C", 4, "circles",
       "In Figure 1, a triangle ABC with ∠B = 90° is shown. Taking AB as "
       "diameter, a circle has been drawn intersecting AC at point P. "
       "Prove that the tangent drawn at point P bisects BC."),
    _q(13, "C", 4, "arithmetic-progressions",
       "Case study: In Mathematics, relations can be expressed in various "
       "ways. The matchstick patterns are based on linear relations. "
       "Different strategies can be used to calculate the number of "
       "matchsticks used in different figures. One such pattern is shown "
       "in the paper (figures of matchstick triangles). Observe the "
       "pattern and answer the following questions using Arithmetic "
       "Progression : (a) Write the AP for the number of triangles used in "
       "the figures. Also, write the nth term of this AP. (b) Which figure "
       "has 61 matchsticks ?"),
    _q(14, "C", 4, "some-applications-of-trigonometry",
       "Case study: Gadisar Lake is located in the Jaisalmer district of "
       "Rajasthan. It was built by the King of Jaisalmer and rebuilt by "
       "Gadsi Singh in 14th century. The lake has many Chhatris. One of "
       "them is shown in the paper. Observe the picture. From a point A h "
       "m above from water level, the angle of elevation of top of Chhatri "
       "(point B) is 45° and angle of depression of its reflection in "
       "water (point C) is 60°. If the height of Chhatri above water level "
       "is (approximately) 10 m, then (a) draw a well-labelled figure "
       "based on the above information; (b) find the height (h) of the "
       "point A above water level. (Use √3 = 1.73)"),
]

# ---------------------------------------------------------------------------
# CBSE Class 12 Mathematics 2022, Term 2 — Q.P. Code 65/2/1,
# Series ABCD1/2, Set 1.
# Full text: AglaSem Docs (see source_url in the entry below),
# cross-checked against the Collegedunia solved paper for the
# same set 65/2/1.
# All 14 questions transcribed from the English text of the paper.
# ---------------------------------------------------------------------------
_CBSE12_2022_TERM2 = [
    _q(1, "A", 2, "differential-equations",
       "Find the product of the order and the degree of the differential "
       "equation (dy/dx) (d/dx)(x y²) + y = 0."),
    _q(2, "A", 2, "integrals",
       "(a) Find : ∫ (sin 3x)/(sin x) dx. OR (b) Evaluate : ∫(0 to (1/2) "
       "log 3) e^x/(e^(2x) + 1) dx."),
    _q(3, "A", 2, "vector-algebra",
       "a and b are two unit vectors such that |2a + 3b| = |3a - 2b|. Find "
       "the angle between a and b."),
    _q(4, "A", 2, "probability",
       "A pair of dice is thrown. It is given that the sum of numbers "
       "appearing on both dice is an even number. Find the probability "
       "that the number appearing on at least one die is 3."),
    _q(5, "A", 2, "probability",
       "Probabilities of A and B solving a specific problem are 2/3 and "
       "3/5 respectively. If both of them try independently to solve the "
       "problem, then find the probability that the problem is solved."),
    _q(6, "A", 2, "three-dimensional-geometry",
       "Write the cartesian equation of the line PQ passing through points "
       "P(2, 2, 1) and Q(5, 1, -2). Hence, find the y-coordinate of the "
       "point on the line PQ whose z-coordinate is -2."),
    _q(7, "B", 3, "vector-algebra",
       "ABCD is a parallelogram such that AC = î + ĵ and BD = 2î + ĵ + k̂. "
       "Find AB and AD. Also, find the area of the parallelogram ABCD."),
    _q(8, "B", 3, "integrals",
       "(a) Evaluate : ∫(0 to 1) tan^(-1) x dx. OR (b) Find : ∫ 2x/(x² + "
       "3x + 2) dx."),
    _q(9, "B", 3, "differential-equations",
       "Find the particular solution of the differential equation (y + "
       "3x²) (dx/dy) = x, given that y = 1, when x = 1."),
    _q(10, "B", 3, "three-dimensional-geometry",
       "(a) Find the equation of the plane passing through points (2, 1, "
       "0), (3, -2, -2) and (1, 1, -7). Also, obtain its distance from the "
       "origin. OR (b) Find the distance between the lines x/1 = (y - 1)/2 "
       "= (z - 2)/3 and (x + 1)/1 = (y + 2)/2 = (z - 1)/3."),
    _q(11, "C", 4, "three-dimensional-geometry",
       "Find the distance of the point (-1, -5, -10) from the point of "
       "intersection of the line (x - 2)/3 = (y + 1)/4 = (z - 2)/12 and "
       "the plane x - y + z = 5."),
    _q(12, "C", 4, "integrals",
       "Evaluate : ∫(0 to 1) x (1 - x)^n dx."),
    _q(13, "C", 4, "application-of-integrals",
       "(a) Using integration, find the area of the smaller region "
       "enclosed by the curve 4x² + 4y² = 9 and the line 2x + 2y = 3. OR "
       "(b) If the area of the region bounded by the curve y² = 4ax and "
       "the line x = 4a is 256/3 sq. units, then using integration, find "
       "the value of a, where a > 0."),
    _q(14, "C", 4, "probability",
       "Case study: At the start of a cricket match, a coin is tossed and "
       "the team winning the toss has the opportunity to choose to bat or "
       "bowl. Such a coin is unbiased with equal probabilities of getting "
       "head and tail. Based on the above information, answer the "
       "following questions : (a) If such a coin is tossed 2 times, then "
       "find the probability distribution of number of tails. (b) Find the "
       "probability of getting at least one head in three tosses of such a "
       "coin."),
]

# ---------------------------------------------------------------------------
# HBSE (Board of School Education Haryana) Class 12 Mathematics,
# Annual Examination 2024 — Code No. 1232, Series SS/Annual
# Exam.-2024, SET: A.
# Full text: AglaSem Docs (see source_url in the entry below),
# cross-checked against the Indian Express copy of the same
# document; the board's own March-2024 index (bseh.org.in)
# lists this paper's Sets A–D.
# All 38 questions transcribed from the English text of the
# bilingual paper.
# ---------------------------------------------------------------------------
_HBSE12_2024 = [
    _q(1, "A", 1, "relations-and-functions",
       "Let N be the set of natural numbers and the function f : N → N be "
       "defined by f(n) = 2n + 3 for all n ∈ N, then f is: (A) Surjective "
       "(B) Injective (C) Bijective (D) None of these"),
    _q(2, "A", 1, "inverse-trigonometric-functions",
       "The domain of sin⁻¹ 2x is: (A) [0, 1] (B) [-1, 1] (C) [-1/2, 1/2] "
       "(D) [-2, 2]"),
    _q(3, "A", 1, "matrices",
       "Total numbers of possible matrices of order 3 × 3 with each entry "
       "2 or 0, are: (A) 9 (B) 27 (C) 81 (D) 512"),
    _q(4, "A", 1, "determinants",
       "If |x, 2; 18, x| = |6, 2; 18, 6|, then x is equal to: (A) 6 (B) ±6 "
       "(C) -6 (D) 0"),
    _q(5, "A", 1, "determinants",
       "Let A be a non-singular square matrix of order 3 × 3. Then |adj A| "
       "is equal to ............ ."),
    _q(6, "A", 1, "continuity-and-differentiability",
       "The derivative of sin(log x) w. r. t. x is: (A) cos(log x)/x² (B) "
       "cos(log x) (C) cos(log x)/x (D) None of these"),
    _q(7, "A", 1, "continuity-and-differentiability",
       "The derivative of sin x w. r. t. cos x is ............ ."),
    _q(8, "A", 1, "integrals",
       "∫ e^x sec x (1 + tan x) dx is equal to: (A) e^x cos x + c (B) e^x "
       "sec x + c (C) e^x sin x + c (D) e^x tan x + c"),
    _q(9, "A", 1, "integrals",
       "The value of ∫ sin⁵ x dx, from -π/2 to π/2, is equal to "
       "............ ."),
    _q(10, "A", 1, "application-of-integrals",
       "The area enclosed by circle x² + y² = 2 is equal to: (A) 4π sq. "
       "units (B) 2√2 π sq. units (C) 4π² sq. units (D) 2π sq. units"),
    _q(11, "A", 1, "differential-equations",
       "The order and degree of the differential equation [1 + (dy/dx)²] = "
       "d²y/dx² respectively are: (A) 1, 2 (B) 2, 2 (C) 2, 1 (D) 4, 2"),
    _q(12, "A", 1, "differential-equations",
       "Integrating factor of the differential equation x dy/dx - y = sin "
       "x is ............ ."),
    _q(13, "A", 1, "vector-algebra",
       "Let the vectors a and b be such that |a| = 3 and |b| = √2/3, then "
       "a × b is a unit vector, if the angle between a and b is: (A) π/6 "
       "(B) π/4 (C) π/3 (D) π/2"),
    _q(14, "A", 1, "vector-algebra",
       "If the vectors a = 2i + λj + k and b = i + 2j + 3k are orthogonal, "
       "then the value of λ is ............ ."),
    _q(15, "A", 1, "three-dimensional-geometry",
       "The equations of x-axis in space are: (A) x = 0, y = 0 (B) x = 0, "
       "z = 0 (C) x = 0 (D) y = 0, z = 0"),
    _q(16, "A", 1, "probability",
       "The probability of obtaining an even prime number on each die, "
       "when a pair of dice is rolled is ............ ."),
    _q(17, "A", 1, "probability",
       "A bag contains 5 red and 3 blue balls. If 3 balls are drawn at "
       "random without replacement, the probability of getting exactly one "
       "red ball is ............ ."),
    _q(18, "A", 1, "probability",
       "Two cards are drawn from well shuffled deck of 52 playing cards "
       "with replacement. The probability, that both cards are queens is "
       "............ ."),
    _q(19, "A", 1, "relations-and-functions",
       "Assertion (A): A relation R = {(a, b); |a - b| < 2} defined on the "
       "set A = {1, 2, 3, 4, 5} is reflexive. Reason (R): A relation R on "
       "the set A is said to be reflexive if for (a, b) ∈ R and (b, c) ∈ "
       "R, we have (a, c) ∈ R. (A) Both Assertion (A) and Reason (R) are "
       "true and Reason (R) is the correct explanation of Assertion (A). "
       "(B) Both Assertion (A) and Reason (R) are true and Reason (R) is "
       "not the correct explanation of Assertion (A). (C) Assertion (A) is "
       "true, but Reason (R) is false. (D) Assertion (A) is false, but "
       "Reason (R) is true."),
    _q(20, "A", 1, "three-dimensional-geometry",
       "Assertion (A): The angle between the straight lines (x + 1)/2 = (y "
       "- 2)/5 = (z + 3)/4 and (x - 1)/1 = (y + 2)/2 = (z - 3)/(-3) is "
       "90°. Reason (R): Skew lines are lines in different planes which "
       "are parallel and intersecting. (A) Both Assertion (A) and Reason "
       "(R) are true and Reason (R) is the correct explanation of "
       "Assertion (A). (B) Both Assertion (A) and Reason (R) are true and "
       "Reason (R) is not the correct explanation of Assertion (A). (C) "
       "Assertion (A) is true, but Reason (R) is false. (D) Assertion (A) "
       "is false, but Reason (R) is true."),
    _q(21, "B", 2, "relations-and-functions",
       "Let f : R → R be defined by f(x) = sin x and g : R → R be defined "
       "by g(x) = x², then find fog and gof. Show that: fog ≠ gof OR Find "
       "the value of: cos⁻¹ (1/2) + 2 sin⁻¹ (1/2)"),
    _q(22, "B", 2, "matrices",
       "If A = [[cos θ, sin θ], [-sin θ, cos θ]], then verify that: A'A = "
       "I"),
    _q(23, "B", 2, "continuity-and-differentiability",
       "Differentiate w. r. t. x: tan⁻¹ ((1 - cos x)/(1 + cos x)), -π/4 < "
       "x < π/4"),
    _q(24, "B", 2, "differential-equations",
       "Verify that the function xy = log y + c is a solution of the "
       "differential equation dy/dx = y²/(1 - xy), (xy ≠ 1). OR Find the "
       "general solution of differential equation dy/dx = (1 + x²)(1 + "
       "y²)."),
    _q(25, "B", 2, "probability",
       "Evaluate P(A ∪ B), if 2P(A) = P(B) = 5/13 and P(A/B) = 2/5."),
    _q(26, "C", 3, "relations-and-functions",
       "Show that the relation R defined in the set A of all triangles as "
       "R = {(T1, T2); T1 is similar to T2}, is equivalence relation. OR "
       "Write the following function in simplest form: tan⁻¹ ((3a²x - "
       "x³)/(a³ - 3ax²)), a > 0; -a/√3 < x < a/√3"),
    _q(27, "C", 3, "matrices",
       "If A = [[3, -2], [4, -2]] and I = [[1, 0], [0, 1]], find K, so "
       "that A² = KA - 2I."),
    _q(28, "C", 3, "continuity-and-differentiability",
       "Find the value of K, so that the function f(x) = K cos x/(π - 2x), "
       "if x ≠ π/2; f(x) = 3, if x = π/2, is continuous at x = π/2."),
    _q(29, "C", 3, "application-of-derivatives",
       "A balloon, which always remains spherical, has a variable diameter "
       "(3/2)(2x + 1). Find the rate of change of its volume with respect "
       "to x."),
    _q(30, "C", 3, "integrals",
       "Integrate: ∫ tan x/(sin x . cos x) dx OR Integrate: ∫ 1/[x(x⁴ - "
       "1)] dx"),
    _q(31, "C", 3, "vector-algebra",
       "Find λ and μ, if (2i + 6j + 27k) × (i + λj + μk) = 0."),
    _q(32, "D", 5, "matrices",
       "Solve the following system of linear equations, using matrix "
       "method: 2x + y + z = 1; x - 2y - z = 3/2; 3y - 5z = 9"),
    _q(33, "D", 5, "integrals",
       "Evaluate the following definite integral: ∫ log(1 + tan x) dx, "
       "from 0 to π/4 OR Find the area of the region bounded by the "
       "ellipse 9x² + 4y² = 36."),
    _q(34, "D", 5, "three-dimensional-geometry",
       "Find the shortest distance between the lines whose vector "
       "equations are: r = i + 2j + 3k + λ(i - 3j + 2k) and r = 4i + 5j + "
       "6k + μ(2i + 3j + k) OR Find the shortest distance between the "
       "lines whose vector equations are: r = (1 - t)i + (t - 2)j + (3 - "
       "2t)k and r = (s + 1)i + (2s - 1)j - (2s + 1)k"),
    _q(35, "D", 5, "linear-programming",
       "Minimize and maximize z = 5x + 10y subject to constraints: x + 2y "
       "≤ 120, x + y ≥ 60, x - 2y ≥ 0, x ≥ 0, y ≥ 0"),
    _q(36, "E", 4, "application-of-derivatives",
       "Case study: Let a cone is inscribed in a sphere of radius R. The "
       "height and radius of cone are h and r respectively. On the basis "
       "of above information, answer the following questions: (i) Write "
       "the relation between r and R in terms of x. (ii) Write the volume "
       "V of the cone in terms of R and x. (iii) Show that volume V of the "
       "cone is maximum, when x = R/3. OR If volume V of the cone is "
       "maximum at x = R/3, then find the maximum value of V and find the "
       "ratio of volume of cone and volume of sphere, when volume of cone "
       "is maximum."),
    _q(37, "E", 4, "differential-equations",
       "Case study: Polio drops are delivered to 50 K children in a "
       "district. The rate at which polio drops are given is directly "
       "proportional to the number of children who have not been "
       "administered the drops. By the end of 2nd week, half the children "
       "have been given the polio drops. How many will have been given the "
       "drops by the end of 3rd week can be estimated using the solution "
       "to the differential equation dy/dx = λ(50 - y), where x denotes "
       "the number of weeks and y the number of children who have been "
       "given the drops. Based on the above information, answer the "
       "following questions: (i) State the order of the above differential "
       "equation. (ii) Which method of solving a differential equation can "
       "be used to solve dy/dx = λ(50 - y)? (iii) Solve the differential "
       "equation: dy/dx = λ(50 - y) OR If λ = 0.049 and y(0) = 0, then "
       "find the particular solution of differential equation."),
    _q(38, "E", 4, "probability",
       "Case study: In a school, teacher asks a question to three students "
       "Ravi, Mohit and Sonia. The probability of solving the question by "
       "Ravi, Mohit and Sonia are 30%, 25% and 45% respectively. The "
       "probability of making error by Ravi, Mohit and Sonia are 1%, 1.2% "
       "and 2% respectively. Based on the above information, answer the "
       "following questions: (i) Find the total probability of committing "
       "an error in solving the question. (ii) If the solution of question "
       "is checked by teacher and has some error, then find the "
       "probability that the question is not solved by Ravi."),
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
    {
        "id": "cbse-10-2025",
        "class_num": 10,
        "board": "CBSE",
        "year": 2025,
        "set_label": "Mathematics (Standard) · Board Paper "
                     "2025 (solved paper, LearnCBSE)",
        "source_name": "CBSE Class 10 Mathematics (Standard) "
                       "Question Paper 2025 with Solutions "
                       "(LearnCBSE)",
        "source_url": "https://www.learncbse.in/cbse-class-10-"
                      "maths-standard-question-paper-2025/",
        "note": "Question 11 is NOT included: the angle values "
                "it asks for are given only in the printed "
                "figure, which the source page does not "
                "reproduce in text. All other 37 questions are "
                "included, transcribed from the source text.",
        "questions": _CBSE10_2025,
    },
    {
        "id": "cbse-12-2025",
        "class_num": 12,
        "board": "CBSE",
        "year": 2025,
        "set_label": "Q.P. Code 65/1/1 · Set 1",
        "source_name": "CBSE Class 12 Mathematics Question "
                       "Paper 2025, Set 1 (65/1/1), solved "
                       "paper (Collegedunia), cross-checked "
                       "against PYQ Vault",
        "source_url": "https://collegedunia.com/articles/"
                      "e-704-cbse-class-12-2025-mathematics-"
                      "set-1-65-1-1-question-paper",
        "note": "Question 18 is NOT included: it is a "
                "graph-only question (graph of a trigonometric "
                "function and its inverse) with no text content. "
                "Questions 10 and 12 are shown without options: "
                "in the Collegedunia text Q.10's integrand is "
                "misprinted and Q.12's option list repeats one "
                "option twice, so their options could not be "
                "verified; both stems were verified against PYQ "
                "Vault. All other 35 questions are included "
                "with options.",
        "questions": _CBSE12_2025,
    },
    {
        "id": "cbse-10-2024-basic",
        "class_num": 10,
        "board": "CBSE",
        "year": 2024,
        "set_label": "Q.P. Code 430/2/1 · Set 1 · Mathematics "
                     "(Basic)",
        "source_name": "CBSE Class 10 Mathematics (Basic) "
                       "Question Paper 2024, Set 1 (430/2/1), "
                       "solved paper (Vedantu)",
        "source_url": "https://www.vedantu.com/content-files-"
                      "downloadable/previous-year-question-"
                      "paper/cbse-class-10-maths-question-paper-"
                      "set-1-430-2-1-2024.pdf",
        "note": "Questions 3 and 38 are NOT included: Q.3's "
                "options are illegible in the source PDF's "
                "scrambled table layout, and Q.38's points are "
                "given only in the printed figure. Questions 5, "
                "10 and 13 are shown without options for the "
                "same reason (scrambled option layout in the "
                "source). All other 33 questions are included "
                "with options.",
        "questions": _CBSE10_2024_BASIC,
    },
    {
        "id": "cbse-10-2023",
        "class_num": 10,
        "board": "CBSE",
        "year": 2023,
        "set_label": "Q.P. Code 30/1/1 · Set 1 · Mathematics "
                     "(Standard)",
        "source_name": "CBSE Class 10 Mathematics (Standard) "
                       "Question Paper 2023, Set 1 (30/1/1), "
                       "solved paper (Vedantu), cross-checked "
                       "against the official CBSE marking scheme "
                       "(AglaSem Docs)",
        "source_url": "https://www.vedantu.com/content-files-"
                      "downloadable/previous-year-question-"
                      "paper/cbse-class-10-maths-question-paper-"
                      "set-1-30-1-1-2023.pdf",
        "note": "Question 1 is NOT included: it asks for the "
                "number of zeroes of a polynomial from its "
                "printed graph, which cannot be reproduced in "
                "text. Question 20's assertion refers to a "
                "figure; the figure's data (right triangle with "
                "AB = 2 cm and BC = 3 cm) is stated inside the "
                "question text. All other 37 questions are "
                "included, transcribed from the source text and "
                "cross-checked against the official CBSE "
                "marking scheme for paper code 30/1/1.",
        "questions": _CBSE10_2023,
    },
    {
        "id": "cbse-10-2025-basic",
        "class_num": 10,
        "board": "CBSE",
        "year": 2025,
        "set_label": "Mathematics (Basic) 2025, Q.P. Code 430/1/1, Series "
                     "GE1FH, Set 1",
        "source_name": "CogniGuru (Cognicraft Edu) — CBSE Class 10 Maths "
                       "Basic 2025 Question Paper (Set 430/1/1) with "
                       "Solutions, checked against CBSE's answer key; "
                       "cross-checked against Swavid's 430/1/1 paper",
        "source_url": "https://cognicraftedu.com/cbse- "
                      "class-10-papers/maths-basic/2025/430-1-1",
        "note": "All 38 questions are included; none omitted. Figure "
                "questions Q8, Q9, Q12, Q13, Q22, Q26(b), Q33 and the case "
                "studies Q36-Q38 are included with the figure's data "
                "spelled out in words in the text, exactly as described in "
                "the primary source (the printed figures themselves are not "
                "reproduced). Q7 is transcribed with its printed options; "
                "CBSE's own marking scheme for this paper states that none "
                "of the given options is correct. No question is shown "
                "without options.",
        "questions": _CBSE10_2025_BASIC,
    },
    {
        "id": "cbse-10-2020",
        "class_num": 10,
        "board": "CBSE",
        "year": 2020,
        "set_label": "Mathematics (Standard) 2020, Q.P. Code 30/1/1, "
                     "Series JBB/1, Set 1 (Delhi Set-I)",
        "source_name": "LearnCBSE — CBSE Class 10 Maths Question Paper "
                       "2020 (Series: JBB/1) with Solutions; questions "
                       "redacted there as 'Not in Current Syllabus' "
                       "recovered from Oswaal CBSE Solved Paper 2020 "
                       "(Delhi Set-I, Code No. 30/1/1) and NotesBazar "
                       "30/1/1",
        "source_url": "https://www.learncbse.in/cbse-class-10-maths- "
                      "question-paper-2020-series-jbb-1/",
        "note": "All 40 questions are included; none omitted. LearnCBSE "
                "redacts Q10, Q12, Q13, Q14, Q28, Q32, Q34, Q35, Q37 and "
                "Q39 as 'Not in Current Syllabus' without printing their "
                "text; their text was recovered verbatim from the Oswaal "
                "Solved Paper 2020 for the same code 30/1/1 (Delhi Set-I) "
                "and agrees with NotesBazar's 30/1/1 paper. LearnCBSE also "
                "prints only one side of the internal choices in Q27, Q28, "
                "Q30 and Q40 and only the main part of Q35 and Q40; both "
                "choices are given here from Oswaal/NotesBazar. Q11 is "
                "figure-based; the figure's values (AR = 4 cm, AC = 11 cm, "
                "BP = 3 cm) are spelled out in the text from the Oswaal "
                "figure. Q22, Q23 and Q31 refer to printed figures whose "
                "defining conditions are fully stated in the text. No "
                "question is shown without options. The CBSE Portal page "
                "titled 'Maths Standard 2020' is a DIFFERENT set (its Q1 is "
                "on prime factorisation of 196) and was not used for "
                "transcription.",
        "questions": _CBSE10_2020,
    },
    {
        "id": "cbse-10-2022-term2",
        "class_num": 10,
        "board": "CBSE",
        "year": 2022,
        "set_label": "Q.P. Code 30/1/1 · Series PPQQA/1 · Set 1 · "
                     "Mathematics (Standard) · Term 2 (40 marks)",
        "source_name": "CBSE Class 10 Mathematics (Standard) Question "
                       "Paper 2022, Term 2, Set 1 (30/1/1), full text on "
                       "AglaSem Docs, cross-checked against "
                       "NetExplanations and CareerPower solutions for the "
                       "same series/code",
        "source_url": "https://docs.aglasem.com/view/7ee698c4-5d00-11ed-8e08-0a5e36bc6706",
        "note": "All 14 questions of the Term 2 paper are included (the "
                "2022 board exam was held in two terms; this is the "
                "complete Term 2 paper, 40 marks). Question 12 refers to "
                "the paper's Figure 1 and Question 13 to the printed "
                "matchstick-pattern figures; both question texts are "
                "complete as printed, but the figures themselves are not "
                "reproduced here. The AglaSem OCR drops most minus signs; "
                "every sign was restored only where the cross-check sources "
                "agree (e.g. Q.1's AP is -30, -24, -18, ...).",
        "questions": _CBSE10_2022_TERM2,
    },
    {
        "id": "cbse-12-2022-term2",
        "class_num": 12,
        "board": "CBSE",
        "year": 2022,
        "set_label": "Q.P. Code 65/2/1 · Series ABCD1/2 · Set 1 · Term 2 "
                     "(40 marks)",
        "source_name": "CBSE Class 12 Mathematics Question Paper 2022, "
                       "Term 2, Set 1 (65/2/1), full text on AglaSem Docs, "
                       "cross-checked against the Collegedunia solved "
                       "paper for the same set 65/2/1",
        "source_url": "https://docs.aglasem.com/view/eb06c30a-5da3-11ed-83f1-0a5e36bc6706",
        "note": "All 14 questions of the Term 2 paper are included (the "
                "2022 board exam was held in two terms; this is the "
                "complete Term 2 paper, 40 marks). The AglaSem OCR drops "
                "most minus signs and mangles formula layout; every formula "
                "and sign below was restored only where the Collegedunia "
                "solved paper for the same code 65/2/1 agrees (e.g. Q.6's "
                "point Q is (5, 1, -2), Q.10(a)'s points are (3, -2, -2) "
                "and (1, 1, -7), Q.11's point is (-1, -5, -10)).",
        "questions": _CBSE12_2022_TERM2,
    },
    {
        "id": "hbse-12-2024",
        "class_num": 12,
        "board": "HBSE (Haryana Board)",
        "year": 2024,
        "set_label": "Code No. 1232, Series: SS/Annual Exam.-2024, SET: A",
        "source_name": "AglaSem Docs — HBSE Class 12 Question Paper 2024 "
                       "Mathematics (full text version, 26 pages)",
        "source_url": "https://docs.aglasem.com/view/5169be2e-eea5-11ef- "
                      "bf8b-0a5e36bc6706",
        "note": "All 38 questions included (80/80 marks); English text "
                "transcribed from the bilingual paper. No omissions and no "
                "stem-only questions. Flags: Q10 options (B)/(C) "
                "radical/exponent placement (2√2 π, 4π²) read from the OCR "
                "layout; Q11 — the text versions show an extra superscript "
                "'2' floating at the bracket of the equation whose "
                "attachment could not be resolved, equation transcribed in "
                "its linear visible form [1 + (dy/dx)²] = d²y/dx², treat as "
                "provisional; Q13 |b| = √2/3 — the radical over the 2 is "
                "dropped in both OCR text versions (fraction shows as 2 "
                "over 3), read as the standard printed form; Q23 — lower "
                "bound read as -π/4 (minus sign dropped in the AglaSem OCR, "
                "present in the second source's rendering) and no radical "
                "is legible over the fraction (1 - cos x)/(1 + cos x) in "
                "either text version, transcribed as printed there; Q26 OR "
                "— denominator read as a³ - 3ax² and bounds as -a/√3 < x < "
                "a/√3 (exponents/radicals garbled in OCR); Q30 — no radical "
                "is legible over tan x in either text version, transcribed "
                "as printed there; Q36 — the variable x is defined only in "
                "the printed figure (labels D, R, O, R, x, A, B, C), not in "
                "the text. Q19 Reason and Q20 Reason are transcribed "
                "exactly as printed, even though both statements are "
                "mathematically odd as printed.",
        "questions": _HBSE12_2024,
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
           "section_title_for",
           "get_paper", "papers_for_class", "chapter_title",
           "paper_total_marks", "analysis_for_class",
           "generate_practice_paper"]
