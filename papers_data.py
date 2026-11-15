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
       "The order and degree of the differential equation [1 + (dy/dx)²]² "
       "= d²y/dx² respectively are: (A) 1, 2 (B) 2, 2 (C) 2, 1 (D) 4, 2"),
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
       "Differentiate w. r. t. x: tan⁻¹ (√((1 - cos x)/(1 + cos x))), "
       "π/4 < x < π/4 (bound as printed in the paper)"),
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
       "Integrate: ∫ √tan x/(sin x . cos x) dx OR Integrate: ∫ 1/[x(x⁴ - "
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
# ---------------------------------------------------------------------------
# Wave 64 — HINDI-MEDIUM versions of four CBSE papers above.
# Each was transcribed question-by-question from the Hindi
# half of the same printed bilingual paper (read from the
# source's page images; the sources' Hindi text layers are
# legacy-font encoded and unusable). Nothing is translated
# or invented: these are the genuine Hindi-medium papers
# as issued by CBSE.
# ---------------------------------------------------------------------------
_CBSE12_2024_HI = [
    _q(1, 'A', 1, 'relations-and-functions',
       'एक फलन f : R+ → R (जहाँ R+ सभी ऋणेतर वास्तविक संख्याओं का समुच्चय है) f(x) = 4x + 3 द्वारा परिभाषित है, तो यह फलन : (A) एकैकी है परन्तु आच्छादक नहीं है (B) आच्छादक है परन्तु एकैकी नहीं है (C) एकैकी तथा आच्छादक दोनों हैं (D) न तो एकैकी और न ही आच्छादक है'),
    _q(2, 'A', 1, 'matrices',
       'यदि एक आव्यूह के 36 अवयव हैं, तो इसकी संभव कोटियों की संख्या है : (A) 13 (B) 3 (C) 5 (D) 9'),
    _q(3, 'A', 1, 'continuity-and-differentiability',
       'फलन f(x) = {x² + 3, x ≠ 0; 1, x = 0} के लिए, निम्न कथनों में से कौन-सा सही है ? (A) f(x) संतत और अवकलनीय है, सभी x ∈ R के लिए (B) f(x) संतत है, सभी x ∈ R के लिए (C) f(x) संतत और अवकलनीय है, सभी x ∈ R − {0} के लिए (D) f(x) अनंत बिंदुओं पर असंतत है'),
    _q(4, 'A', 1, 'application-of-derivatives',
       'माना f(x) अन्तराल [a, b] में एक संतत फलन है और अन्तराल (a, b) में अवकलनीय है। तो यह फलन f(x) अन्तराल (a, b) में निरंतर वर्धमान होगा, यदि : (A) f′(x) < 0, सभी x ∈ (a, b) के लिए (B) f′(x) > 0, सभी x ∈ (a, b) के लिए (C) f′(x) = 0, सभी x ∈ (a, b) के लिए (D) f(x) > 0, सभी x ∈ (a, b) के लिए'),
    _q(5, 'A', 1, 'determinants',
       'यदि [[x + y, 2], [5, xy]] = [[6, 2], [5, 8]] है, तो (24/x + 24/y) का मान होगा : (A) 7 (B) 6 (C) 8 (D) 18'),
    _q(6, 'A', 1, 'integrals',
       '∫(a to b) f(x) dx बराबर है : (A) ∫(a to b) f(a − x) dx (B) ∫(a to b) f(a + b − x) dx (C) ∫(a to b) f(x − (a + b)) dx (D) ∫(a to b) f((a − x) + (b − x)) dx'),
    _q(7, 'A', 1, 'vector-algebra',
       'माना दो मात्रक सदिशों a⃗ और b⃗ के बीच का कोण θ इस प्रकार है कि sin θ = 3/5 है। तो a⃗ · b⃗ बराबर है : (A) ±3/5 (B) ±3/4 (C) ±4/5 (D) ±4/3'),
    _q(8, 'A', 1, 'differential-equations',
       'अवकल समीकरण (1 − x²) dy/dx + xy = ax, −1 < x < 1, का समाकलन गुणक है : (A) 1/(x² − 1) (B) 1/√(x² − 1) (C) 1/(1 − x²) (D) 1/√(1 − x²)'),
    _q(9, 'A', 1, 'three-dimensional-geometry',
       'यदि किसी एक रेखा के दिक्-कोसाइन √3 k, √3 k, √3 k हैं, तो k का मान है : (A) ±1 (B) ±√3 (C) ±3 (D) ±1/3'),
    _q(10, 'A', 1, 'linear-programming',
       'एक रैखिक प्रोग्रामन इष्टतमकारी समस्या संबंधित होती है : (A) लघुगणकीय फलन से (B) रैखिक फलन से (C) द्विघातीय फलन से (D) चरघातांकीय फलन से'),
    _q(11, 'A', 1, 'probability',
       'यदि P(A|B) = P(A′|B) है, तो निम्न में से कौन-सा कथन सही है ? (A) P(A) = P(A′) (B) P(A) = 2 P(B) (C) P(A ∩ B) = 1/2 P(B) (D) P(A ∩ B) = 2 P(B)'),
    _q(12, 'A', 1, 'determinants',
       '|x + 1, x − 1; x² + x + 1, x² − x + 1| बराबर है : (A) 2x³ (B) 2 (C) 0 (D) 2x³ − 2'),
    _q(13, 'A', 1, 'continuity-and-differentiability',
       'x के सापेक्ष, sin (x²) का अवकलज, x = √π पर है : (A) 1 (B) −1 (C) −2√π (D) 2√π'),
    _q(14, 'A', 1, 'differential-equations',
       'अवकल समीकरण [1 + (dy/dx)²]³ = d²y/dx² की कोटि और घात क्रमशः हैं : (A) 1, 2 (B) 2, 3 (C) 2, 1 (D) 2, 6'),
    _q(15, 'A', 1, 'vector-algebra',
       'सदिश, जिसका अंतिम बिंदु A (2, −3, 5) तथा प्रारंभिक बिंदु B (3, −4, 7) है, है : (A) î − ĵ + 2k̂ (B) î + ĵ + 2k̂ (C) −î − ĵ − 2k̂ (D) −î + ĵ − 2k̂'),
    _q(16, 'A', 1, 'three-dimensional-geometry',
       'y-अक्ष से बिंदु P(a, b, c) की दूरी है : (A) b (B) b² (C) √(a² + c²) (D) a² + c²'),
    _q(17, 'A', 1, 'linear-programming',
       'व्यवरोधों x ≥ 0, y ≥ 0, x + y ≥ 4 से निर्धारित सुसंगत क्षेत्र के कोनीय बिंदुओं की संख्या है : (A) 0 (B) 1 (C) 2 (D) 3'),
    _q(18, 'A', 1, 'matrices',
       'यदि दो समान कोटि वाले शून्येतर वर्ग आव्यूहों A और B के लिए (A + B)² = A² + B² है, तो : (A) AB = O (B) AB = −BA (C) BA = O (D) AB = BA'),
    _q(19, 'A', 1, 'determinants',
       'अभिकथन (A) : आव्यूह A = [[1, cos θ, 1], [−cos θ, 1, cos θ], [−1, −cos θ, 1]], जहाँ θ ∈ [0, 2π] के लिए, |A| ∈ [2, 4]। तर्क (R) : cos θ ∈ [−1, 1], ∀ θ ∈ [0, 2π]। (अभिकथन-तर्क प्रश्न)'),
    _q(20, 'A', 1, 'three-dimensional-geometry',
       'अभिकथन (A) : अंतरिक्ष में एक रेखा कभी भी एक साथ x, y और z अक्षों के लंबवत नहीं हो सकती है। तर्क (R) : किसी रेखा द्वारा x, y और z अक्षों की धनात्मक दिशाओं के साथ क्रमशः α, β और γ के कोण बनाने पर cos²α + cos²β + cos²γ = 1 है। (अभिकथन-तर्क प्रश्न)'),
    _q(21, 'B', 2, 'continuity-and-differentiability',
       '(क) जाँच कीजिए कि क्या फलन f(x) = x²|x|, बिंदु x = 0 पर अवकलनीय है या नहीं। अथवा (ख) यदि y = √(tan √x) है, तो सिद्ध कीजिए कि √x dy/dx = (1 + y⁴)/(4y)।'),
    _q(22, 'B', 2, 'application-of-derivatives',
       'दर्शाइए कि फलन f(x) = 4x³ − 18x² + 27x − 7 का उच्चतम या निम्नतम मान नहीं है।'),
    _q(23, 'B', 2, 'integrals',
       '(क) ज्ञात कीजिए : ∫ x√(1 + 2x) dx अथवा (ख) मान ज्ञात कीजिए : ∫(0 to π²/4) (sin √x)/(√x) dx'),
    _q(24, 'B', 2, 'vector-algebra',
       'यदि दो शून्येतर सदिश a⃗ और b⃗ इस प्रकार हैं कि (a⃗ + b⃗) ⊥ a⃗ और (2a⃗ + b⃗) ⊥ b⃗, तो सिद्ध कीजिए कि |b⃗| = √2 |a⃗|।'),
    _q(25, 'B', 2, 'vector-algebra',
       'दी गई आकृति में, ABCD एक समांतर चतुर्भुज है। यदि AB = 2î − 4ĵ + 5k̂ तथा DB = 3î − 6ĵ + 2k̂ हैं, तो AD ज्ञात कीजिए और इसके प्रयोग से समांतर चतुर्भुज ABCD का क्षेत्रफल ज्ञात कीजिए।'),
    _q(26, 'C', 3, 'relations-and-functions',
       '(क) समुच्चय A = {1, 2, 3, 4, 5} में एक संबंध R = {(x, y) : |x² − y²| < 8} द्वारा परिभाषित है। जाँच कीजिए कि क्या यह संबंध R स्वतुल्य, सममित और संक्रामक है। अथवा (ख) फलन f : R → R, f(x) = ax + b द्वारा इस प्रकार परिभाषित है कि f(1) = 1 और f(2) = 3. फलन f(x) ज्ञात कीजिए। अतः, जाँच कीजिए कि क्या फलन f(x) एकैकी और आच्छादक है या नहीं।'),
    _q(27, 'C', 3, 'continuity-and-differentiability',
       '(क) यदि √(1 − x²) + √(1 − y²) = a(x − y) है, तो सिद्ध कीजिए कि dy/dx = √((1 − y²)/(1 − x²))। अथवा (ख) यदि y = (tan x)^x है, तो dy/dx ज्ञात कीजिए।'),
    _q(28, 'C', 3, 'integrals',
       '(क) ज्ञात कीजिए : ∫ x²/((x² + 4)(x² + 9)) dx अथवा (ख) मान ज्ञात कीजिए : ∫(1 to 3) (|x − 1| + |x − 2| + |x − 3|) dx'),
    _q(29, 'C', 3, 'differential-equations',
       'अवकल समीकरण x² dy/dx − xy = x² cos²(y/(2x)) का विशिष्ट हल ज्ञात कीजिए, दिया हुआ है कि y = π/2, यदि x = 1.'),
    _q(30, 'C', 3, 'linear-programming',
       'निम्न रैखिक प्रोग्रामन समस्या को आलेखीय विधि द्वारा हल कीजिए : निम्न व्यवरोधों के अंतर्गत x + 2y ≤ 12, 2x + y ≤ 12, 4x + 5y ≥ 20, x ≥ 0, y ≥ 0; z = 500x + 300y का अधिकतमीकरण कीजिए।'),
    _q(31, 'C', 3, 'probability',
       'E और F दो स्वतंत्र घटनाएँ ऐसी हैं जिनके लिए P(Ē) = 0.6 तथा P(E ∪ F) = 0.6 है। P(F) और P(Ē ∪ F̄) ज्ञात कीजिए।'),
    _q(32, 'D', 5, 'matrices',
       '(क) यदि A = [[1, −2, 0], [2, −1, −1], [0, −2, 1]] है, तो A⁻¹ ज्ञात कीजिए और इसके प्रयोग से, निम्न समीकरण निकाय को हल कीजिए : x − 2y = 10, 2x − y − z = 8, −2y + z = 7 अथवा (ख) यदि A = [[−1, a, 2], [1, 2, x], [3, 1, 1]] तथा A⁻¹ = [[1, −1, 1], [−8, 7, −5], [b, y, 3]] है, तो (a + x) − (b + y) का मान ज्ञात कीजिए।'),
    _q(33, 'D', 5, 'integrals',
       '(क) मान ज्ञात कीजिए : ∫(0 to π/4) (sin x + cos x)/(9 + 16 sin 2x) dx अथवा (ख) मान ज्ञात कीजिए : ∫(0 to π/2) sin 2x tan⁻¹(sin x) dx'),
    _q(34, 'D', 5, 'application-of-integrals',
       'समाकलन विधि के प्रयोग से, दीर्घवृत्त x²/16 + y²/4 = 1 के उस क्षेत्र का, जो रेखाओं x = −2 और x = 2 के बीच है, क्षेत्रफल ज्ञात कीजिए।'),
    _q(35, 'D', 5, 'three-dimensional-geometry',
       'यदि रेखा x/1 = (y − 1)/2 = (z − 2)/3 में बिंदु P(x, y, z) का प्रतिबिम्ब P′ (1, 0, 7) है, तो बिंदु P के निर्देशांक ज्ञात कीजिए।'),
    _q(36, 'E', 4, 'application-of-derivatives',
       'प्रकरण अध्ययन : ट्रैफिक पुलिस ने शहर में विभिन्न स्थानों पर ओवर स्पीड उल्लंघन डिटेक्शन (OSVD) प्रणाली स्थापित की है। ये कैमरे 300 मीटर की दूरी से तेज़ गति से चलने वाले वाहन की फोटो ले सकते हैं और अँधेरे में भी काम कर सकते हैं। एक खंभे पर 5 मीटर की ऊँचाई पर एक कैमरा स्थापित किया गया है। यह 20 मीटर/सेकंड की गति से खंभे से दूर जा रही एक कार का पता लगाता है। खंभे के पाद से x मीटर दूरी पर किसी भी बिंदु पर, कार C से स्पीड कैमरे का उन्नयन कोण θ है। उपर्युक्त सूचना के आधार पर, निम्न प्रश्नों के उत्तर दीजिए : (i) खंभे पर स्थापित किए गए कैमरे की ऊँचाई और x के रूप में θ को व्यक्त कीजिए। (ii) dθ/dx ज्ञात कीजिए। (iii) (क) जब कार खंभे से 50 मीटर दूर हो, तो उस क्षण पर समय के सापेक्ष उन्नयन कोण में परिवर्तन की दर ज्ञात कीजिए। अथवा (iii) (ख) यदि खंभे के पाद से 50 मीटर की दूरी पर दूसरी कार के समय के सापेक्ष उन्नयन कोण में परिवर्तन की दर 3/101 रेडियन/सेकंड है, तो कार की गति ज्ञात कीजिए।'),
    _q(37, 'E', 4, 'probability',
       'प्रकरण अध्ययन : हाल के शोध के अनुसार, जलवायु परिवर्तन के कारण दुनिया भर के विभिन्न क्षेत्रों में वायु विक्षोभ बढ़ता है। वायु विक्षोभ उड़ान को मुश्किल बना देता है और अक्सर उड़ान में देरी करता है। मान लीजिए कि एक हवाई जहाज समान प्रायिकता के साथ गंभीर विक्षोभ, मध्यम विक्षोभ या हल्के विक्षोभ का अनुभव करता है। इसके अलावा, गंभीर विक्षोभ, मध्यम विक्षोभ और हल्के विक्षोभ के कारण हवाई जहाज के गंतव्य पर देर से पहुँचने की प्रायिकता क्रमशः 55%, 37% और 17% है। उपर्युक्त सूचना के आधार पर, निम्न प्रश्नों के उत्तर दीजिए : (i) हवाई जहाज के गंतव्य पर देर से पहुँचने की प्रायिकता ज्ञात कीजिए। (ii) यदि हवाई जहाज अपने गंतव्य पर देर से पहुँचता है, तो प्रायिकता ज्ञात कीजिए कि ऐसा मध्यम विक्षोभ के कारण हुआ है।'),
    _q(38, 'E', 4, 'inverse-trigonometric-functions',
       'प्रकरण अध्ययन : यदि फलन f : X → Y इस प्रकार परिभाषित है कि f(x) = y एकैकी तथा आच्छादक हो, तो हम एक अद्वितीय फलन g : Y → X इस प्रकार परिभाषित कर सकते हैं कि g(y) = x, जहाँ x ∈ X तथा y = f(x), y ∈ Y है। फलन g को फलन f का प्रतिलोम कहा जाता है। sine फलन का प्रांत R और फलन sine : R → R न तो एकैकी है और न ही आच्छादक है। निम्न आकृति में sine फलन का आलेख दिखाया गया है। मान लीजिए sine फलन समुच्चय A से [−1, 1] इस प्रकार परिभाषित है कि sine फलन के प्रतिलोम का अस्तित्व है, यानि sin⁻¹ x : [−1, 1] → A पर परिभाषित है। उपर्युक्त सूचना के आधार पर, निम्न प्रश्नों के उत्तर दीजिए : (i) यदि A मुख्य मान शाखा के अलावा अन्य अंतराल है, तो ऐसे एक अंतराल का उदाहरण दीजिए। (ii) यदि sin⁻¹(x) को [−1, 1] से इसकी मुख्य मान शाखा में परिभाषित किया गया हो, तो sin⁻¹(−1/2) − sin⁻¹(1) का मान ज्ञात कीजिए। (iii) (क) [−1, 1] से मुख्य मान शाखा तक के लिए sin⁻¹ x का आलेख बनाइए। अथवा (iii) (ख) f(x) = 2 sin⁻¹(1 − x) का प्रांत और परिसर ज्ञात कीजिए।'),
]

_CBSE12_2023_HI = [
    _q(1, 'A', 1, 'matrices',
       'यदि किसी वर्ग आव्यूह A के लिए A² − 3A + I = O है तथा A⁻¹ = xA + yI है, तो x + y का मान है : (a) −2 (b) 2 (c) 3 (d) −3'),
    _q(2, 'A', 1, 'determinants',
       'यदि एक 2 × 2 आव्यूह A के लिए |A| = 2 है, तो |4A⁻¹| बराबर है : (a) 4 (b) 2 (c) 8 (d) 1/32'),
    _q(3, 'A', 1, 'determinants',
       'माना A एक ऐसा 3 × 3 आव्यूह है कि |adj A| = 64 है। तो |A| बराबर है : (a) केवल 8 (b) केवल −8 (c) 64 (d) 8 अथवा −8'),
    _q(4, 'A', 1, 'matrices',
       'यदि A = [[3, 4], [5, 2]] है तथा 2A + B एक शून्य आव्यूह है, तो B बराबर है : (a) [[6, 8], [10, 4]] (b) [[−6, −8], [−10, −4]] (c) [[5, 8], [10, 3]] (d) [[−5, −8], [−10, −3]]'),
    _q(5, 'A', 1, 'integrals',
       'यदि d/dx (f(x)) = log x है, तो f(x) बराबर है : (a) −1/x + C (b) x(log x − 1) + C (c) x(log x + x) + C (d) 1/x + C'),
    _q(6, 'A', 1, 'integrals',
       '∫(0 to π/6) sec²(x − π/6) dx बराबर है : (a) 1/√3 (b) −1/√3 (c) √3 (d) −√3'),
    _q(7, 'A', 1, 'differential-equations',
       'अवकल समीकरण d²y/dx² + (dy/dx)³ = sin y की कोटि तथा घात का योगफल है : (a) 5 (b) 2 (c) 3 (d) 4'),
    _q(8, 'A', 1, 'vector-algebra',
       'p का वह मान जिसके लिए सदिश 2î + pĵ + k̂ तथा −4î − 6ĵ + 26k̂ परस्पर लंबवत हैं, है : (a) 3 (b) −3 (c) −17/3 (d) 17/3'),
    _q(9, 'A', 1, 'vector-algebra',
       '(î × ĵ) · ĵ + (ĵ × î) · k̂ का मान है : (a) 2 (b) 0 (c) 1 (d) −1'),
    _q(10, 'A', 1, 'vector-algebra',
       'यदि a⃗ + b⃗ = î तथा a⃗ = 2î − 2ĵ + 2k̂ है, तो |b⃗| बराबर है : (a) √14 (b) 3 (c) √12 (d) √17'),
    _q(11, 'A', 1, 'three-dimensional-geometry',
       'रेखा (x − 1)/2 = (1 − y)/3 = (2z − 1)/12 के दिक्-कोसाइन हैं : (a) 2/7, 3/7, 6/7 (b) 2/√157, −3/√157, 12/√157 (c) 2/7, −3/7, −6/7 (d) 2/7, −3/7, 6/7'),
    _q(12, 'A', 1, 'probability',
       'यदि P(A/B) = 0.3, P(A) = 0.4 तथा P(B) = 0.8 है, तो P(B/A) बराबर है : (a) 0.6 (b) 0.3 (c) 0.06 (d) 0.4'),
    _q(13, 'A', 1, 'continuity-and-differentiability',
       'k का वह मान जिसके लिए f(x) = {3x + 5, x ≥ 2; kx², x < 2} एक संतत फलन है, है : (a) −11/4 (b) 4/11 (c) 11 (d) 11/4'),
    _q(14, 'A', 1, 'matrices',
       'यदि A = [[0, 1], [−1, 0]] तथा (3I + 4A)(3I − 4A) = x²I है, तो x का/के मान है/हैं : (a) ±√7 (b) 0 (c) ±5 (d) 25'),
    _q(15, 'A', 1, 'differential-equations',
       'अवकल समीकरण x dy − (1 + x²) dx = dx का व्यापक हल है : (a) y = 2x + x³/3 + C (b) y = 2 log x + x³/3 + C (c) y = x²/2 + C (d) y = 2 log x + x²/2 + C'),
    _q(16, 'A', 1, 'application-of-derivatives',
       "यदि f(x) = a(x − cos x), R में निरंतर ह्रासमान है, तो 'a' निम्न में से किस में स्थित है ? (a) {0} (b) (0, ∞) (c) (−∞, 0) (d) (−∞, ∞)"),
    _q(17, 'A', 1, 'linear-programming',
       'किसी रैखिक प्रोग्रामन समस्या के आलेखीय निरूपण में सुसंगत क्षेत्र के शीर्ष बिन्दु (2, 72), (15, 20) तथा (40, 15) हैं। यदि z = 18x + 9y उद्देश्य फलन है, तो : (a) z, (2, 72) पर अधिकतम तथा (15, 20) पर न्यूनतम है। (b) z, (15, 20) पर अधिकतम तथा (40, 15) पर न्यूनतम है। (c) z, (40, 15) पर अधिकतम तथा (15, 20) पर न्यूनतम है। (d) z, (40, 15) पर अधिकतम तथा (2, 72) पर न्यूनतम है।'),
    _q(18, 'A', 1, 'linear-programming',
       'व्यवरोधों x − y ≥ 0, 2y ≤ x + 2, x ≥ 0, y ≥ 0 द्वारा बने सुसंगत क्षेत्र के शीर्ष बिन्दुओं की संख्या है : (a) 2 (b) 3 (c) 4 (d) 5'),
    _q(19, 'A', 1, 'inverse-trigonometric-functions',
       'अभिकथन (A) : फलन f(x) = 2 sin⁻¹ x + 3π/2, जहाँ x ∈ [−1, 1] का परिसर [π/2, 5π/2] है। तर्क (R) : sin⁻¹(x) की मुख्य मान शाखा का परिसर [0, π] है। (अभिकथन-तर्क प्रश्न)'),
    _q(20, 'A', 1, 'three-dimensional-geometry',
       'अभिकथन (A) : बिन्दुओं (1, 2, 3) तथा (3, −1, 3) से होकर जाने वाली रेखा का समीकरण (x − 3)/2 = (y + 1)/3 = (z − 3)/0 है। तर्क (R) : बिन्दुओं (x₁, y₁, z₁) तथा (x₂, y₂, z₂) से होकर जाने वाली रेखा का समीकरण (x − x₁)/(x₂ − x₁) = (y − y₁)/(y₂ − y₁) = (z − z₁)/(z₂ − z₁) है। (अभिकथन-तर्क प्रश्न)'),
    _q(21, 'B', 2, 'relations-and-functions',
       '(क) f(x) = 2x द्वारा परिभाषित फलन f : A → B, एकैकी और आच्छादक दोनों है। यदि A = {1, 2, 3, 4} है, तो समुच्चय B ज्ञात कीजिए। अथवा (ख) मान ज्ञात कीजिए : sin⁻¹(sin 3π/4) + cos⁻¹(cos 3π/4) + tan⁻¹(1)'),
    _q(22, 'B', 2, 'vector-algebra',
       'परिमाण 3√3 के वह सभी सदिश ज्ञात कीजिए जो सदिश î + ĵ + k̂ के संरेख हों।'),
    _q(23, 'B', 2, 'vector-algebra',
       '(क) नीचे दी गई आकृति में दर्शाए गए बिन्दुओं A, B तथा C के स्थिति सदिश क्रमशः a⃗, b⃗ तथा c⃗ हैं। यदि AC = (5/4) AB है, तो c⃗ को a⃗ तथा b⃗ के पदों में व्यक्त कीजिए। अथवा (ख) ज्ञात कीजिए कि क्या रेखाएँ जिनके समीकरण x = 2λ + 2, y = 7λ + 1, z = −3λ − 3 तथा x = −μ − 2, y = 2μ + 8, z = 4μ + 5 हैं, परस्पर लंबवत हैं या नहीं।'),
    _q(24, 'B', 2, 'continuity-and-differentiability',
       'यदि y = (x + √(x² − 1))² है, तो दर्शाइए कि (x² − 1)(dy/dx)² = 4y².'),
    _q(25, 'B', 2, 'application-of-derivatives',
       'दर्शाइए कि फलन f(x) = (16 sin x)/(4 + cos x) − x, (π/2, π) में निरंतर ह्रासमान है।'),
    _q(26, 'C', 3, 'integrals',
       'मान ज्ञात कीजिए : ∫(0 to π/2) [log(sin x) − log(2 cos x)] dx'),
    _q(27, 'C', 3, 'integrals',
       'ज्ञात कीजिए : ∫ 1/(√x(√x + 1)(√x + 2)) dx'),
    _q(28, 'C', 3, 'differential-equations',
       '(क) अवकल समीकरण dy/dx + sec²x · y = tan x · sec²x का विशिष्ट हल ज्ञात कीजिए, दिया गया है कि y(0) = 0. अथवा (ख) अवकल समीकरण x dy − y dx − √(x² + y²) dx = 0 को हल कीजिए।'),
    _q(29, 'C', 3, 'linear-programming',
       'निम्न रैखिक प्रोग्रामन समस्या को आलेख द्वारा हल कीजिए : z = 6x + 3y का निम्नलिखित व्यवरोधों के अंतर्गत, अधिकतम मान ज्ञात कीजिए : 4x + y ≥ 80, 3x + 2y ≤ 150, x + 5y ≥ 115, x ≥ 0, y ≥ 0.'),
    _q(30, 'C', 3, 'probability',
       '(क) किसी यादृच्छिक चर X का प्रायिकता बंटन नीचे दिया गया है : X : 1, 2, 3; P(X) : k/2, k/3, k/6. (i) k का मान ज्ञात कीजिए। (ii) ज्ञात कीजिए : P(1 ≤ X < 3) (iii) X का माध्य E(X) ज्ञात कीजिए। अथवा (ख) A तथा B ऐसी स्वतंत्र घटनाएँ हैं कि P(A ∩ B̄) = 1/4 तथा P(Ā ∩ B) = 1/6 है। P(A) तथा P(B) ज्ञात कीजिए।'),
    _q(31, 'C', 3, 'integrals',
       '(क) मान ज्ञात कीजिए : ∫(0 to π/2) e^x sin x dx अथवा (ख) ज्ञात कीजिए : ∫ 1/(cos(x − a) cos(x − b)) dx'),
    _q(32, 'D', 5, 'relations-and-functions',
       'एक संबंध R, वास्तविक संख्याओं के समुच्चय R पर इस प्रकार परिभाषित है कि R = {(x, y) : x · y एक अपरिमेय संख्या है}। जाँच कीजिए कि क्या R, स्वतुल्य, सममित या संक्रामक है या नहीं।'),
    _q(33, 'D', 5, 'matrices',
       '(क) यदि A = [[1, 2, −2], [−1, 3, 0], [0, −2, 1]] तथा B⁻¹ = [[3, −1, 1], [−15, 6, −5], [5, −2, 2]] है, तो (AB)⁻¹ ज्ञात कीजिए। अथवा (ख) आव्यूह विधि द्वारा निम्न समीकरण निकाय को हल कीजिए : x + 2y + 3z = 6, 2x − y + z = 2, 3x + 2y − 2z = 3'),
    _q(34, 'D', 5, 'three-dimensional-geometry',
       '(क) उस रेखा के सदिश तथा कार्तीय समीकरण ज्ञात कीजिए, जो बिन्दु (1, 2, −4) से होकर जाती है तथा बिन्दुओं A(3, 3, −5) तथा B(1, 0, −11) को मिलाने वाली रेखा के समांतर है। अतः इन दो रेखाओं के बीच की दूरी ज्ञात कीजिए। अथवा (ख) बिन्दुओं A(1, 2, 3) तथा B(3, 5, 9) से होकर जाने वाली रेखा के समीकरण ज्ञात कीजिए। अतः इस रेखा पर उन बिन्दुओं के निर्देशांक ज्ञात कीजिए, जो बिन्दु B से 14 इकाई की दूरी पर हैं।'),
    _q(35, 'D', 5, 'application-of-integrals',
       'समाकलन के प्रयोग से वक्र x² = y, y = x + 2 तथा x-अक्ष द्वारा घिरे क्षेत्र का क्षेत्रफल ज्ञात कीजिए।'),
    _q(36, 'E', 4, 'probability',
       'प्रकरण अध्ययन : योग के कई प्रकार हैं जिनमें योग के विभिन्न प्रकार के आसन, मनन-प्रार्थना, प्राणायाम इत्यादि हैं जैसा कि चित्र में दर्शाया गया है। नीचे दी गई वेन-आकृति में, एक सोसाइटी के लोगों द्वारा किए गए तीन विभिन्न प्रकार के योग A, B तथा C की प्रायिकताओं को दर्शाया गया है। यह भी दिया गया है कि एक सदस्य द्वारा C प्रकार के योग करने की प्रायिकता 0.44 है। उपर्युक्त सूचनाओं के आधार पर, निम्न प्रश्नों के उत्तर दीजिए : (i) x का मान ज्ञात कीजिए। (ii) y का मान ज्ञात कीजिए। (iii) (क) P(C/B) ज्ञात कीजिए। अथवा (iii) (ख) प्रायिकता ज्ञात कीजिए कि सोसाइटी का एक यादृच्छया चुना गया सदस्य A या B प्रकार का योग करता है परन्तु C प्रकार का नहीं।'),
    _q(37, 'E', 4, 'application-of-derivatives',
       "प्रकरण अध्ययन : निम्न आकृति में दर्शाए गए टैंक, जो बेलन तथा शंकु को जोड़कर बने हैं, एक सीधे आधार वाले टैंक से पानी की अच्छी निकासी देते हैं। एक ऐसा टैंक, जिसका शंक्वाकार भाग पानी से भरा है, में एक नल लगाया गया तथा नल से 2 cm³/s की समान दर से पानी टपक रहा है। शंक्वाकार टैंक का अर्ध-शीर्ष कोण 45° है। उपर्युक्त सूचनाओं के आधार पर निम्न प्रश्नों के उत्तर दीजिए : (i) टैंक में पानी के आयतन को त्रिज्या r के पदों में व्यक्त कीजिए। (ii) उस समय जब r = 2√2 cm है, त्रिज्या के बदलने की दर ज्ञात कीजिए। (iii) (क) उस समय जब r = 2√2 cm है, शंक्वाकार टैंक के गीले तल के घटने की दर ज्ञात कीजिए। अथवा (iii) (ख) जब तिर्यक ऊँचाई 4 cm है, उस समय ऊँचाई 'h' के बदलने की दर ज्ञात कीजिए।"),
    _q(38, 'E', 4, 'application-of-derivatives',
       "प्रकरण अध्ययन : एक रोलर-कोस्टर द्वारा तय किया गया पथ बहुपद f(x) = a(x + 9)(x + 1)(x − 3) द्वारा प्रदत्त है। यदि यह रोलर-कोस्टर y-अक्ष को बिंदु (0, −1) पर मिलता है, तो निम्न के उत्तर दीजिए : (i) 'a' का मान ज्ञात कीजिए। (ii) x = 1 पर f″(x) ज्ञात कीजिए।"),
]

_CBSE10_2024_HI = [
    _q(1, 'A', 1, 'polynomials',
       'यदि बहुपद p(x) = 2x² − k√2 x + 1 के शून्यकों का योगफल √2 है, तो k का मान है : (a) √2 (b) 2 (c) 2√2 (d) 1/2'),
    _q(2, 'A', 1, 'probability',
       'यदि एक खिलाड़ी के एक खेल को जीतने की प्रायिकता 0.79 है, तो उसके, उसी खेल को हारने की प्रायिकता है : (a) 1.79 (b) 0.31 (c) 0.21% (d) 0.21'),
    _q(3, 'A', 1, 'quadratic-equations',
       'यदि समीकरण ax² + bx + c = 0, a ≠ 0 के मूल वास्तविक और समान हैं, तो निम्न में से कौनसा संबंध सही है ? (a) a = b²/c (b) b² = ac (c) ac = b²/4 (d) c = b²/a'),
    _q(4, 'A', 1, 'arithmetic-progressions',
       'एक समांतर श्रेढ़ी में यदि प्रथम पद a = 7, nवां पद a_n = 84 तथा प्रथम n पदों का योग s_n = 2093/2 है, तो n का मान है : (a) 22 (b) 24 (c) 23 (d) 26'),
    _q(5, 'A', 1, 'real-numbers',
       'यदि दो धन पूर्णांकों p तथा q को p = 18 a²b⁴ तथा q = 20 a³b² के रूप में लिखा जा सकता है, जहाँ a तथा b अभाज्य संख्याएँ हैं, तो LCM (p, q) है : (a) 2 a²b² (b) 180 a²b² (c) 12 a²b² (d) 180 a³b⁴'),
    _q(6, 'A', 1, 'coordinate-geometry',
       'त्रिभुज ABC के शीर्ष A(5, −6), B(6, 4) तथा C(0, 0) हैं तथा AD त्रिभुज की एक माध्यिका है। AD की लंबाई है : (a) √68 इकाई (b) 2√15 इकाई (c) √101 इकाई (d) 10 इकाई'),
    _q(7, 'A', 1, 'introduction-to-trigonometry',
       'यदि sec θ − tan θ = m है, तो sec θ + tan θ का मान है : (a) 1 − 1/m (b) m² − 1 (c) 1/m (d) −m'),
    _q(8, 'A', 1, 'probability',
       'आँकड़ों 1, 4, 7, 9, 16, 21, 25 में से यदि सभी सम संख्याएँ निकाल दी गई हों, तो शेष में यादृच्छया एक अभाज्य संख्या आने की प्रायिकता है : (a) 2/5 (b) 1/5 (c) 1/7 (d) 2/7'),
    _q(9, 'A', 1, 'statistics',
       'किन्हीं आँकड़ों x₁, x₂, ...... x_n जहाँ f₁, f₂, ...... f_n क्रमशः उनकी बारंबारताएँ हैं, के लिए Σ f_i (x_i − x̄) का मान है : (a) n x̄ (b) 1 (c) Σ f_i (d) 0'),
    _q(10, 'A', 1, 'polynomials',
       'यदि बहुपद x² + px + q के शून्यक, बहुपद 4x² − 5x − 6 के शून्यकों के दुगने के बराबर हैं, तो p का मान है : (a) −5/2 (b) 5/2 (c) −5 (d) 10'),
    _q(11, 'A', 1, 'coordinate-geometry',
       'यदि बिंदुओं (3, −5) तथा (x, −5) के बीच की दूरी 15 इकाई है, तो x के मान हैं : (a) 12, −18 (b) −12, 18 (c) 18, 5 (d) −9, −12'),
    _q(12, 'A', 1, 'introduction-to-trigonometry',
       'यदि cos(α + β) = 0 है, तो cos((α + β)/2) का मान है : (a) 1/√2 (b) 1/2 (c) 0 (d) √2'),
    _q(13, 'A', 1, 'surface-areas-and-volumes',
       'एक ठोस गोले को दो अर्धगोलों में काटा गया। इस गोले के पृष्ठीय क्षेत्रफल का दोनों अर्धगोलों के संपूर्ण पृष्ठीय क्षेत्रफल से अनुपात है : (a) 1 : 1 (b) 1 : 4 (c) 2 : 3 (d) 3 : 2'),
    _q(14, 'A', 1, 'statistics',
       'प्रत्येक प्रकार के आँकड़ों को क्रम में व्यवस्थित करने पर सबसे बीच का प्रेक्षण होता है : (a) बहुलक (b) माध्यक (c) माध्य (d) विचलन'),
    _q(15, 'A', 1, 'surface-areas-and-volumes',
       'भुजा 2 cm वाले एक ठोस घन से काटकर निकाले जा सकने वाले अधिकतम आयतन के शंकु का आयतन है : (a) 4π/3 cu cm (b) 5π/3 cu cm (c) 8π/3 cu cm (d) 2π/3 cu cm'),
    _q(16, 'A', 1, 'probability',
       'दो पासों को एक साथ उछाला गया। दोनों पासों पर आई संख्याओं का योग 2, 3 या 5 आने की प्रायिकता है : (a) 7/36 (b) 11/36 (c) 5/36 (d) 4/9'),
    _q(17, 'A', 1, 'coordinate-geometry',
       'एक वृत्त का केंद्र बिंदु (2, 0) पर है। यदि वृत्त के एक व्यास का एक सिरा बिंदु (6, 0) पर है, तो इसके दूसरे सिरे के निर्देशांक हैं : (a) (0, 0) (b) (4, 0) (c) (−2, 0) (d) (−6, 0)'),
    _q(18, 'A', 1, 'pair-of-linear-equations',
       'दी गई आकृति में दो रैखिक समीकरणों का ग्राफ दर्शाया गया है। इन रैखिक समीकरणों का युग्म : (a) अद्वितीय हल के साथ संगत है। (b) अपरिमित रूप से अनेक हलों के साथ संगत है। (c) असंगत है। (d) असंगत है परन्तु रेखाओं को बढ़ाने पर संगत बनाया जा सकता है।'),
    _q(19, 'A', 1, 'circles',
       'अभिकथन (A) : वृत्त के किसी व्यास के सिरों पर खींची गई स्पर्श रेखाएँ परस्पर समांतर होती हैं। तर्क (R) : एक वृत्त का व्यास इसकी सबसे लम्बी जीवा होती है। (अभिकथन-तर्क प्रश्न)'),
    _q(20, 'A', 1, 'polynomials',
       'अभिकथन (A) : यदि किसी बहुपद का ग्राफ x-अक्ष को केवल एक बिंदु पर स्पर्श करता है, तो यह द्विघात बहुपद नहीं हो सकता। तर्क (R) : घात n (n > 1) के बहुपद के अधिकतम शून्यक n होते हैं। (अभिकथन-तर्क प्रश्न)'),
    _q(21, 'B', 2, 'pair-of-linear-equations',
       'निम्न रैखिक समीकरण निकाय का हल ज्ञात कीजिए 7x − 2y = 5 तथा 8x + 7y = 15 और अपने उत्तर को सत्यापित कीजिए।'),
    _q(22, 'B', 2, 'probability',
       'एक अच्छी प्रकार से फेंटी गई 52 पत्तों की ताश की गड्डी में से यादृच्छया एक पत्ता निकाला गया। यदि यह एक काले रंग का पत्ता है, तो इसे अलग रखकर शेष पत्तों में से एक पत्ता यादृच्छया निकाला गया। इस पत्ते के पान की बेगम वाला पत्ता आने की प्रायिकता ज्ञात कीजिए।'),
    _q(23, 'B', 2, 'introduction-to-trigonometry',
       '(A) मान ज्ञात कीजिए : 2√2 cos 45° sin 30° + 2√3 cos 30° अथवा (B) यदि A = 60° तथा B = 30° है, तो सत्यापित कीजिए कि : sin (A + B) = sin A cos B + cos A sin B'),
    _q(24, 'B', 2, 'triangles',
       'दी गई आकृति में, ABCD एक चतुर्भुज है जिसका विकर्ण BD, कोण B तथा कोण D को समद्विभाजित करता है। सिद्ध कीजिए : (i) ΔABD ~ ΔCBD (ii) AB = BC'),
    _q(25, 'B', 2, 'real-numbers',
       '(A) सिद्ध कीजिए कि 5 − 2√3 एक अपरिमेय संख्या है जब दिया है कि √3 अपरिमेय संख्या है। अथवा (B) दर्शाइए कि संख्या 5×11×17 + 3×11 एक भाज्य संख्या (समग्र संख्या) है।'),
    _q(26, 'C', 3, 'coordinate-geometry',
       '(A) वह अनुपात ज्ञात कीजिए जिसमें बिंदु (8/5, y) बिंदुओं (1, 2) तथा (2, 3) को मिलाने वाले रेखाखण्ड को विभाजित करता है। y का मान भी ज्ञात कीजिए। अथवा (B) बिंदु A (−1, −1), B (−1, 6), C (3, 6) तथा D (3, −1) एक आयत ABCD बनाते हैं। यदि P, Q, R तथा S क्रमशः भुजाओं AB, BC, CD तथा DA के मध्य बिंदु हैं तो सिद्ध कीजिए कि चतुर्भुज PQRS के विकर्ण एक-दूसरे का समद्विभाजन करते हैं।'),
    _q(27, 'C', 3, 'real-numbers',
       'अध्यापकों की एक कार्यशाला में फ्रेंच, हिन्दी तथा अंग्रेजी के क्रमशः 48, 80 तथा 144 अध्यापक हैं। यदि प्रत्येक कमरे में एक ही विषय के अध्यापकों की समान संख्या रखनी हो, तो कम से कम कितने कमरों की आवश्यकता होगी?'),
    _q(28, 'C', 3, 'introduction-to-trigonometry',
       'सिद्ध कीजिए : tan θ/(1 − cot θ) + cot θ/(1 − tan θ) = 1 + sec θ cosec θ'),
    _q(29, 'C', 3, 'pair-of-linear-equations',
       'तीन वर्ष पहले, रश्मि की आयु नजमा की आयु की तीन गुनी थी। दस वर्ष पश्चात् रश्मि की आयु नजमा की आयु की दुगनी रह जाएगी। उन दोनों की वर्तमान आयु ज्ञात कीजिए।'),
    _q(30, 'C', 3, 'circles',
       '(A) दी गई आकृति में, AB वृत्त का व्यास है तथा O वृत्त का केंद्र है। AQ, BP तथा PQ वृत्त पर खींची गई स्पर्श रेखाएँ हैं। सिद्ध कीजिए कि ∠POQ = 90° है। अथवा (B) एक चतुर्भुज ABCD के अंतर्गत एक 8 सेमी त्रिज्या वाला वृत्त इस प्रकार खींचा गया कि P, Q, R, S स्पर्श बिंदु हैं, जैसा आकृति में दर्शाया गया है। यदि AD ⊥ DC है तथा BC = 30 सेमी और BS = 24 सेमी है तो DC की लंबाई ज्ञात कीजिए।'),
    _q(31, 'C', 3, 'surface-areas-and-volumes',
       '14 सेमी लंबे एक लंबवृत्तीय खोखले बेलन की बाह्य तथा अन्तः त्रिज्याओं का अंतर 1 सेमी है। यदि इस बेलन को बनाने में लगी धातु का आयतन 176 सेमी³ है, तो इसकी बाह्य तथा अन्तः त्रिज्याएँ ज्ञात कीजिए।'),
    _q(32, 'D', 5, 'areas-related-to-circles',
       'त्रिज्या 21 सेमी वाले वृत्त का एक चाप केंद्र पर 60° का कोण अंतरित करता है। ज्ञात कीजिए : (i) चाप की लंबाई। (ii) संगत जीवा द्वारा बनाए गए लघु वृत्तखण्ड का क्षेत्रफल।'),
    _q(33, 'D', 5, 'arithmetic-progressions',
       '(A) एक समांतर श्रेढ़ी (A.P.) के प्रथम तथा आठवें पदों का योगफल 32 है तथा गुणनफल 60 है। इस श्रेढ़ी का प्रथम पद तथा सार्वअंतर ज्ञात कीजिए। इस श्रेढ़ी के प्रथम 20 पदों का योग भी ज्ञात कीजिए। अथवा (B) 40 पदों की एक समांतर श्रेढ़ी के प्रथम 9 पदों का योगफल 153 है तथा इसके आखिरी छः पदों का योग 687 है। इस श्रेढ़ी का प्रथम पद तथा सार्वअन्तर ज्ञात कीजिए। इस श्रेढ़ी के सभी पदों का योगफल भी ज्ञात कीजिए।'),
    _q(34, 'D', 5, 'triangles',
       '(A) यदि किसी त्रिभुज की एक भुजा के समांतर अन्य दो भुजाओं को भिन्न-भिन्न बिंदुओं पर प्रतिच्छेद करने के लिए एक रेखा खींची जाए, तो सिद्ध कीजिए कि यह भुजा अन्य भुजाओं को एक ही अनुपात में विभाजित करती है। अथवा (B) दी गई आकृति में PA, QB तथा RC प्रत्येक AC पर लंब हैं। यदि AP = x, BQ = y तथा CR = z हैं, तो सिद्ध कीजिए कि 1/x + 1/z = 1/y.'),
    _q(35, 'D', 5, 'some-applications-of-trigonometry',
       'एक खम्भा जिसकी ऊँचाई 6 मीटर है, एक मीनार के शिखर पर खड़ा है। भूमि पर एक बिंदु P से खम्भे के शिखर का उन्नयन कोण 60° तथा मीनार के शिखर से बिंदु P का अवनमन कोण 45° है। मीनार की ऊँचाई तथा बिंदु P की मीनार के पाद से दूरी ज्ञात कीजिए। (√3 = 1.73 लीजिए)'),
    _q(36, 'E', 4, 'quadratic-equations',
       'प्रकरण अध्ययन : एक आयताकार क्षेत्र के फर्श को 200 वर्गाकार टाइलों द्वारा पूरा ढका (भरा) जा सकता है। यदि प्रत्येक टाइल की भुजा 1 इकाई बढ़ा दी जाए तो फर्श केवल 128 टाइलों से ही ढक जाता है। (i) यह मानते हुए कि टाइल की प्रत्येक भुजा की मूल लंबाई x इकाई है, उपरोक्त सूचना को द्विघात समीकरण द्वारा निरूपित कीजिए। (ii) संगत द्विघात समीकरण को मानक रूप में लिखिए। (iii) (a) गुणनखण्डन से x का मान ज्ञात कीजिए। अथवा (iii) (b) द्विघात समीकरण को द्विघात सूत्र से हल कीजिए।'),
    _q(37, 'E', 4, 'statistics',
       "प्रकरण अध्ययन : बिंगो एक संयोग का खेल है। मेजबान के पास 1 से 75 तक क्रमांकित 75 गेंदें हैं। प्रत्येक खिलाड़ी के पास एक बिंगो कार्ड है जिस पर कुछ संख्याएँ अंकित हैं। एक गेंद यादृच्छया चुनकर उस पर लिखी संख्या बोले जाने पर प्रतिभागी कार्ड पर वह संख्या रद्द कर देता है। जो भी कार्ड की सारी संख्याएँ रद्द कर पाता है तो वह बिंगो बोल कर खेल जीत जाता/जाती है। नीचे दिए आँकड़े, एक ऐसा खेल दर्शाते हैं जिसमें तारा के 'बिंगो' कहने से पहले 48 गेंद प्रयोग में लाई गईं। बोली गई संख्या : 0-15, 15-30, 30-45, 45-60, 60-75; कितनी बार : 8, 9, 10, 12, 9. उपरोक्त जानकारी के आधार पर निम्न के उत्तर दीजिए : (i) माध्यक वर्ग लिखिए। (ii) जब पहली गेंद निकाली गई थी उस समय एक सम संख्या के बोलने की क्या प्रायिकता थी ? (iii) (a) दिए गए आँकड़ों का माध्यक ज्ञात कीजिए। अथवा (iii) (b) दिए गए आँकड़ों का बहुलक ज्ञात कीजिए।"),
    _q(38, 'E', 4, 'circles',
       'प्रकरण अध्ययन : एक भवन के पीछे का हिस्सा एक त्रिभुज ABC के आकार का है जिसका कोण B समकोण है। AB = 7 मी. तथा BC = 15 मी. है। इसके अंदर एक वृत्ताकार खड्डा इस प्रकार खोदा गया कि यह भुजाओं AC, BC तथा AB को क्रमशः P, Q तथा R पर स्पर्श करता है तथा AP = x मी. है। उपरोक्त जानकारी के आधार पर निम्न प्रश्नों के उत्तर दीजिए : (i) x के पदों में AR की लंबाई ज्ञात कीजिए। (ii) चतुर्भुज BQOR किस प्रकार का चतुर्भुज है? (iii) (a) PC की लंबाई x के पदों में ज्ञात कीजिए और x का मान ज्ञात कीजिए। अथवा (iii) (b) x का मान ज्ञात कीजिए और वृत्त की त्रिज्या r का मान ज्ञात कीजिए।'),
]

_CBSE10_2022_TERM2_HI = [
    _q(1, 'A', 2, 'arithmetic-progressions',
       '(क) समांतर श्रेढ़ी : −30, −24, −18, ..... के प्रथम 30 पदों का योगफल ज्ञात कीजिए। अथवा (ख) एक समांतर श्रेढ़ी में यदि S_n = n (4n + 1) है, तो समांतर श्रेढ़ी ज्ञात कीजिए।'),
    _q(2, 'A', 2, 'surface-areas-and-volumes',
       '10.5 सेमी त्रिज्या वाले धातु के एक ठोस गोले को पिघलाकर, 3.5 सेमी त्रिज्या और 3 सेमी ऊँचाई के कुछ छोटे-छोटे शंकु बनाए जाते हैं। इस प्रकार बनाए गए शंकुओं की संख्या ज्ञात कीजिए।'),
    _q(3, 'A', 2, 'quadratic-equations',
       '(क) m के किस मान के लिए द्विघात समीकरण (m − 1)x² + 2(m − 1)x + 1 = 0 के दो बराबर और वास्तविक मूल होंगे ? अथवा (ख) निम्न द्विघात समीकरण को, x के लिए हल कीजिए : √3 x² + 10x + 7√3 = 0'),
    _q(4, 'A', 2, 'statistics',
       'निम्न बारंबारता बंटन का बहुलक ज्ञात कीजिए : वर्ग : 10 – 20, 20 – 30, 30 – 40, 40 – 50, 50 – 60; बारंबारता : 15, 10, 12, 17, 4.'),
    _q(5, 'A', 2, 'quadratic-equations',
       'रेहान की 5 वर्ष पूर्व आयु (वर्षों में) तथा अब से 7 वर्ष उपरान्त उसकी आयु का गुणनफल उसकी वर्तमान आयु के दो गुने से एक अधिक है। उसकी वर्तमान आयु ज्ञात कीजिए।'),
    _q(6, 'A', 2, 'circles',
       'दो संकेंद्रीय वृत्तों की त्रिज्याएँ 4 सेमी तथा 3 सेमी हैं। बड़े वृत्त की उस जीवा की लम्बाई ज्ञात कीजिए जो छोटे वृत्त को स्पर्श करती हो।'),
    _q(7, 'B', 3, 'statistics',
       'x के किस मान के लिए निम्नलिखित बारंबारता बंटन का माध्यक 34.5 है ? वर्ग : 0 – 10, 10 – 20, 20 – 30, 30 – 40, 40 – 50, 50 – 60, 60 – 70; बारंबारता : 3, 5, 11, 10, x, 3, 2.'),
    _q(8, 'B', 3, 'circles',
       '3 सेमी त्रिज्या का एक वृत्त खींचिए। इसके किसी बढ़ाए गए व्यास पर केंद्र से 7 सेमी की दूरी पर दो बिंदु P और Q लीजिए। इन दोनों बिंदुओं P और Q से वृत्त पर स्पर्श-रेखाओं की रचना कीजिए।'),
    _q(9, 'B', 3, 'some-applications-of-trigonometry',
       '(क) एक मीनार के पाद-बिंदु से एक भवन के शिखर का उन्नयन कोण 30° है और भवन के पाद-बिंदु से मीनार के शिखर का उन्नयन कोण 60° है। यदि मीनार 50 मी. ऊँची है, तो भवन की ऊँचाई ज्ञात कीजिए। अथवा (ख) एक नदी के पुल के एक बिंदु से नदी के सम्मुख किनारों के अवनमन कोण क्रमशः 30° और 45° हैं। यदि पुल किनारों से 3 मी. की ऊँचाई पर हो, तो नदी की चौड़ाई ज्ञात कीजिए।'),
    _q(10, 'B', 3, 'statistics',
       'किसी कम्पनी के 30 कर्मचारियों के खाने के दैनिक खर्च निम्न हैं : दैनिक खर्च (रुपयों में) : 100 – 120, 120 – 140, 140 – 160, 160 – 180, 180 – 200; कर्मचारियों की संख्या : 8, 3, 8, 6, 5. कर्मचारियों का माध्य दैनिक खर्च ज्ञात कीजिए।'),
    _q(11, 'C', 4, 'surface-areas-and-volumes',
       '(क) ऊँचाई 30 सेमी तथा त्रिज्या 7 सेमी वाले एक ठोस बेलन में से 24 सेमी ऊँचाई तथा इसी त्रिज्या वाला एक शंक्वाकार खोल काटकर निकाल लिया जाता है। शेष बचे ठोस का सम्पूर्ण पृष्ठीय क्षेत्रफल ज्ञात कीजिए। अथवा (ख) 8 मी. चौड़ी तथा 6 मी. गहरी एक नहर में पानी 12 किमी/घंटे की चाल से बह रहा है। 1 घंटे में यह नहर कितने क्षेत्रफल की सिंचाई कर पाएगी, यदि सिंचाई के लिए 0.05 मी. अप्रवाही पानी की आवश्यकता होती है ?'),
    _q(12, 'C', 4, 'circles',
       'आकृति 1 में, त्रिभुज ABC दर्शाया गया है जिसमें ∠B = 90° है। AB को व्यास लेते हुए एक वृत्त खींचा गया है, जो AC को बिंदु P पर प्रतिच्छेद करता है। सिद्ध कीजिए कि बिंदु P पर खींची गई स्पर्श रेखा BC को समद्विभाजित करती है।'),
    _q(13, 'C', 4, 'arithmetic-progressions',
       'प्रकरण अध्ययन : गणित में संबंधों को कई प्रकार से व्यक्त किया जा सकता है। माचिस की तीलियों से बनाए गए पैटर्न रेखीय संबंधों पर आधारित हैं। अलग-अलग आकृतियों में प्रयुक्त माचिस की तीलियों की संख्या ज्ञात करने के लिए भिन्न युक्तियाँ प्रयुक्त की जा सकती हैं। एक ऐसा ही पैटर्न नीचे दर्शाया गया है। पैटर्न को ध्यानपूर्वक देखिए तथा समांतर श्रेढ़ी का उपयोग करते हुए निम्न प्रश्नों के उत्तर दीजिए : (क) आकृतियों में प्रयुक्त त्रिभुजों की संख्या को दर्शाने वाली एक समांतर श्रेढ़ी लिखिए। इस समांतर श्रेढ़ी का nवाँ पद भी लिखिए। (ख) किस आकृति में 61 माचिस की तीलियों का उपयोग हुआ है ?'),
    _q(14, 'C', 4, 'some-applications-of-trigonometry',
       'प्रकरण अध्ययन : गड़ीसर झील राजस्थान के जैसलमेर जिले में स्थित है। इसको जैसलमेर के राजा ने बनवाया था तथा 14वीं शताब्दी में गड़सी सिंह ने इसे दुबारा बनवाया। इस झील में बहुत-सी छतरियाँ बनी हुई हैं। उनमें से एक छतरी को नीचे दर्शाया गया है : चित्र को ध्यानपूर्वक देखिए। पानी की सतह से h मी. ऊँचाई पर स्थित बिंदु A से छतरी के शीर्ष (बिंदु B) का उन्नयन कोण 45° है तथा इसी बिंदु से पानी में छतरी के प्रतिबिम्ब (बिंदु C) का अवनमन कोण 60° है। पानी की सतह के ऊपर छतरी की ऊँचाई यदि 10 मी. हो, तो (क) उपर्युक्त सूचना के आधार पर अच्छी प्रकार से अंकित एक आकृति खींचिए। (ख) पानी की सतह से बिंदु A की ऊँचाई (h) ज्ञात कीजिए। (√3 = 1.73 का प्रयोग कीजिए)'),
]


# Wave 66: RBSE Class 10 Mathematics 2025 (S-09-Mathematics),
# bilingual printed paper — English half transcribed from the
# source PDF's text layer, cross-checked against its page images.
_RBSE10_2025 = [
    _q(1, "A", 18, "real-numbers",
       "Choose the correct option to answer the following multiple "
       "choice questions (i to xviii). (i) The sum of powers of prime "
       "factors of 400 is (A) 4 (B) 9 (C) 6 (D) 8 (ii) If 3 is a zero "
       "of the polynomial 2x² + x + k, then the value of k will be "
       "(A) −12 (B) 21 (C) −21 (D) 12 (iii) In a two digit number, the "
       "unit digit is x and the tens digit is y, then that number is "
       "(A) (10x + y) (B) (10y + x) (C) (x + y) (D) 10xy (iv) If "
       "△ABC ~ △DEF and AB = 10 cm, DE = 8 cm, then BC : EF is "
       "(A) 8 : 18 (B) 4 : 5 (C) 9 : 4 (D) 5 : 4 (v) Distance of "
       "point P(−3, 4) from origin O(0, 0) is (A) 5 (B) √7 (C) 7 "
       "(D) 1 (vi) cosec²45° − cot²45° equals (A) √2 (B) 1 (C) 0 "
       "(D) 2√2 (vii) The shadow of a vertical pillar is same as the "
       "height of pillar, then the angle of elevation of sun is "
       "(A) 60° (B) 30° (C) 90° (D) 45° (viii) From a point P, the "
       "length of the tangent to a circle is 24 cm and the distance "
       "of P from the centre is 25 cm. The radius of the circle is "
       "(A) 7 cm (B) 14 cm (C) 3.5 cm (D) 1 cm (ix) The area of a "
       "quadrant of a circle whose radius is 7 cm is (A) 38.5 cm² "
       "(B) 77 cm² (C) 154 cm² (D) 44 cm² (x) If the radius of a cone "
       "is 14 cm and slant height is 10 cm, then the curved surface "
       "area of the cone is (A) 220 cm² (B) 110 cm² (C) 440 cm² "
       "(D) 140 cm² (xi) Which of the following number cannot be the "
       "probability of any event? (A) 2/3 (B) 3/2 (C) 0.7 (D) 0.5 "
       "(xii) If HCF = LCM for two rational numbers, then numbers "
       "always should be (A) Composite (B) Equal (C) Prime "
       "(D) Co-prime (xiii) If the sum and product of the zeros of a "
       "quadratic polynomial are 5 and 6 respectively, then the "
       "quadratic polynomial is (A) x² + 5x + 6 (B) x² + 6x + 5 "
       "(C) x² − 6x + 5 (D) x² − 5x + 6 (xiv) For which value of k, "
       "linear pair x + y − 4 = 0, 2x + ky − 3 = 0 has no solution? "
       "(A) 0 (B) 2 (C) 6 (D) 8 (xv) In the given figure, AB = 2 cm, "
       "∠A = 50°, AC = 4 cm, DE = 3 cm, ∠D = 50° and DF = 6 cm. If "
       "BC = 3 cm, then the measurement of EF is (A) 4.5 cm (B) 6 cm "
       "(C) 8 cm (D) 5 cm (xvi) sin2A = 2 sinA is true, when A equals "
       "(A) 0° (B) 30° (C) 45° (D) 90° (xvii) If cosA = 12/13, then "
       "the value of sinA is (A) 13/12 (B) 5/12 (C) 5/13 (D) 13/5 "
       "(xviii) The angle subtended at the centre by the minute hand "
       "of a clock in 5 minutes is (A) 30° (B) 60° (C) 2½° (D) 10°"),
    _q(2, "A", 6, "arithmetic-progressions",
       "Fill in the blanks in the following questions (i to vi). "
       "(i) If 18, a, 10 are in arithmetic progression, then "
       "a = _________. (ii) The co-ordinates of the mid point of "
       "point P(7, −3) and point Q(3, 9) is ___________. (iii) The "
       "value of sin60° cosec60° + cos30° sec30° is __________. "
       "(iv) If the diameter of a solid hemisphere is 14 cm, then "
       "its total surface area is ___________. (v) The mode of the "
       "distribution 1, 4, 5, 6, 4, 7, 9, 2, 4, 3, 5 is "
       "____________. (vi) The class mark for any class interval is "
       "17. If the upper class limit is 24, then the lower class "
       "limit is ____________."),
    _q(3, "A", 12, "areas-related-to-circles",
       "Very short answer type questions (i to xii). (i) If the "
       "radius of a circle is 14 cm and the length of the arc is "
       "22 cm, then find the angle subtended by the arc at the "
       "centre. (ii) If the total surface area of a cube is 864 "
       "square cm, then find the surface area of one of its faces. "
       "(iii) Find the median of the following frequency "
       "distribution. x : 3, 5, 7, 9; f : 6, 7, 5, 6 (iv) In a "
       "single throw of a die, determine the probability of getting "
       "a number more than 5. (v) A right circular cone and a "
       "cylinder are of equal radius and equal height. If the "
       "volume of the cone is 66 cubic cm, then find the volume of "
       "the cylinder. (vi) Find median of the following data. 19, "
       "17, 25, 27, 18, 20, 29 (vii) Two players Ram and Shyam play "
       "a chess match. It is given that probability of winning the "
       "match by Ram is 4/5. Find the probability of winning the "
       "match by Shyam. (viii) A solid cuboid is formed by joining "
       "the adjacent faces of two cubes, each of side 2 cm. Find "
       "the volume of the resulting cuboid. (ix) Find the "
       "arithmetic mean of the first ten positive odd natural "
       "numbers. (x) A bag contains 6 red and 7 white balls. From "
       "this bag, one ball is drawn randomly. Find the probability "
       "that the ball released is white. (xi) If the curved surface "
       "area of a solid hemisphere is 50π square cm, then find the "
       "radius of that hemisphere. (xii) If the arithmetic mean of "
       "5, 7, 9, 4, 3, (x + 2) is 6, then find the value of x."),
    _q(4, "B", 2, "real-numbers",
       "Find the HCF and LCM of 12, 15 and 21 using the prime "
       "factorisation method."),
    _q(5, "B", 2, "polynomials",
       "If a and b are the zeros of the quadratic polynomial "
       "3x² − 5x + 9, then find (a + b) and ab."),
    _q(6, "B", 2, "pair-of-linear-equations",
       "Use elimination method to find all possible solutions of "
       "the following pair of linear equations : 3x + 5y = 7, "
       "6x + y = −4"),
    _q(7, "B", 2, "arithmetic-progressions",
       "Find the number of terms in arithmetic progression 7, 13, "
       "19, . . . . , 205."),
    _q(8, "B", 2, "triangles",
       "In the given figure, DE || BC, then find the value of x. "
       "(In the figure, AD = (x + 2), DB = 6, AE = 4 and EC = 8.)"),
    _q(9, "B", 2, "coordinate-geometry",
       "In which ratio, x-axis divides the line segment which joins "
       "points (5, 3) and (−3, −2)?"),
    _q(10, "B", 2, "introduction-to-trigonometry",
       "Find the value of 4cot²45° − sec²60° + sin²60°."),
    _q(11, "B", 2, "some-applications-of-trigonometry",
       "A 12 meter long ladder touches the top of a vertical wall. "
       "If this ladder makes an angle of 60° with the wall, then "
       "find height of the wall."),
    _q(12, "B", 2, "circles",
       "A quadrilateral ABCD is drawn to circumscribe a circle. "
       "Prove that AB + CD = AD + BC. (In the given figure, the "
       "circle touches the sides AB, BC, CD and DA at P, Q, R and "
       "S respectively.)"),
    _q(13, "B", 2, "areas-related-to-circles",
       "The angle subtended at the centre by an arc of a circle is "
       "50°. If the length of the arc is 5π cm, then find the "
       "radius of that circle."),
    _q(14, "C", 3, "arithmetic-progressions",
       "Find the sum of first 15 terms of arithmetic progression, "
       "whose nth term is a_n = 3 + 2n. OR There are 60 terms in an "
       "arithmetic progression. If its first and last terms are 7 "
       "and 125 respectively, then find its 32nd term."),
    _q(15, "C", 3, "coordinate-geometry",
       "Find the co-ordinates of points which divide the line "
       "segment joining points (4, 0) and (0, −8) into 4 equal "
       "parts. OR Find the co-ordinates of a point A, where AB is "
       "a diameter of a circle whose centre is (2, −3) and "
       "co-ordinates of B is (1, 4)."),
    _q(16, "C", 3, "circles",
       "Prove that in two concentric circles, the chord of the "
       "larger circle, which touches the smaller circle, is "
       "bisected at the point of contact. OR Prove that the lengths "
       "of tangents drawn from an external point to a circle are "
       "equal."),
    _q(17, "C", 3, "statistics",
       "Find the mean of the following frequency distribution. "
       "x : 5, 6, 7, 8, 9, 10, 11; f : 5, 8, 9, 12, 6, 6, 4 OR If "
       "mean of the following distribution is 7, then find the "
       "value of P. x : 2, 5, P, 9, 10; f : 1, 5, 4, 7, 3"),
    _q(18, "D", 4, "quadratic-equations",
       "The difference of squares of two numbers is 180. The square "
       "of the smaller number is eight times the larger number. "
       "Find both the numbers. OR Find two consecutive positive "
       "integers, whose sum of squares is 365."),
    _q(19, "D", 4, "introduction-to-trigonometry",
       "Prove that 1/(1 + sinθ) + 1/(1 − sinθ) = 2sec²θ. OR Prove "
       "that sin²θcosθ + cos³θ + tanθ sinθ = secθ."),
    _q(20, "D", 4, "statistics",
       "Find the median of the following frequency distribution. "
       "Class : 7 – 17, 17 – 27, 27 – 37, 37 – 47, 47 – 57, "
       "57 – 67; Frequency : 22, 18, 20, 12, 15, 13 OR Find the "
       "mode of the following frequency distribution. Class : "
       "2 – 11, 11 – 20, 20 – 29, 29 – 38, 38 – 47; Frequency : "
       "15, 16, 17, 12, 11"),
]

# Wave 66: the Hindi half of the same printed bilingual paper,
# transcribed question-by-question from the source's page images
# (the Hindi text layer is legacy-font encoded).
_RBSE10_2025_HI = [
    _q(1, "A", 18, "real-numbers",
       "निम्न बहुविकल्पीय प्रश्न (i से xviii) के उत्तर का सही विकल्प "
       "चयन कर उत्तर-पुस्तिका में लिखिए। (i) 400 के अभाज्य "
       "गुणनखण्डों की घातों का योगफल है (a) 4 (b) 9 (c) 6 (d) 8 "
       "(ii) यदि बहुपद 2x² + x + k का एक शून्यक 3 है, तो k का मान "
       "होगा (a) −12 (b) 21 (c) −21 (d) 12 (iii) एक दो अंकों की "
       "संख्या में इकाई का अंक x व दहाई का अंक y है, तो वह संख्या "
       "है (a) (10x + y) (b) (10y + x) (c) (x + y) (d) 10xy (iv) यदि "
       "△ABC ~ △DEF हो एवं AB = 10 सेमी, DE = 8 सेमी हो, तो "
       "BC : EF है (a) 8 : 18 (b) 4 : 5 (c) 9 : 4 (d) 5 : 4 (v) मूल "
       "बिन्दु O(0, 0) से बिन्दु P(−3, 4) की दूरी है (a) 5 (b) √7 "
       "(c) 7 (d) 1 (vi) cosec²45° − cot²45° बराबर है (a) √2 (b) 1 "
       "(c) 0 (d) 2√2 (vii) एक उर्ध्वाधर खम्बे की परछाई, खम्बे की "
       "ऊँचाई के बराबर है, तो सूर्य का उन्नयन कोण है (a) 60° "
       "(b) 30° (c) 90° (d) 45° (viii) एक बिन्दु P से एक वृत्त पर "
       "स्पर्श रेखा की लम्बाई 24 सेमी तथा P की केन्द्र से दूरी 25 "
       "सेमी है। वृत्त की त्रिज्या है (a) 7 सेमी (b) 14 सेमी "
       "(c) 3.5 सेमी (d) 1 सेमी (ix) एक वृत्त की त्रिज्या 7 सेमी "
       "है, उस वृत्त के एक चतुर्थांश का क्षेत्रफल है (a) 38.5 "
       "सेमी² (b) 77 सेमी² (c) 154 सेमी² (d) 44 सेमी² (x) यदि एक "
       "शंकु की त्रिज्या 14 सेमी तथा तिर्यक ऊँचाई 10 सेमी है, तो "
       "शंकु का वक्र पृष्ठीय क्षेत्रफल है (a) 220 सेमी² (b) 110 "
       "सेमी² (c) 440 सेमी² (d) 140 सेमी² (xi) निम्नलिखित में से "
       "कौन-सी संख्या किसी घटना की प्रायिकता नहीं हो सकती? (a) 2/3 "
       "(b) 3/2 (c) 0.7 (d) 0.5 (xii) यदि दो परिमेय संख्याओं के "
       "लिये HCF = LCM, तो संख्याएँ हमेशा होनी चाहिए (a) भाज्य "
       "(b) समान (c) अभाज्य (d) सहअभाज्य (xiii) यदि एक द्विघात "
       "बहुपद के शून्यकों का योग तथा गुणनफल क्रमशः 5 व 6 हैं, तो "
       "द्विघात बहुपद है (a) x² + 5x + 6 (b) x² + 6x + 5 "
       "(c) x² − 6x + 5 (d) x² − 5x + 6 (xiv) k के किस मान के लिए "
       "समीकरण युग्म x + y − 4 = 0, 2x + ky − 3 = 0 का कोई हल नहीं "
       "होगा? (a) 0 (b) 2 (c) 6 (d) 8 (xv) दिए गए चित्र में "
       "AB = 2 सेमी, ∠A = 50°, AC = 4 सेमी, DE = 3 सेमी, ∠D = 50° "
       "और DF = 6 सेमी है। यदि BC = 3 सेमी हो, तो EF का माप है "
       "(a) 4.5 सेमी (b) 6 सेमी (c) 8 सेमी (d) 5 सेमी (xvi) "
       "sin2A = 2 sinA तब सत्य होता है, जबकि A बराबर है (a) 0° "
       "(b) 30° (c) 45° (d) 90° (xvii) यदि cosA = 12/13 है, तो "
       "sinA का मान है (a) 13/12 (b) 5/12 (c) 5/13 (d) 13/5 "
       "(xviii) एक घड़ी की मिनट की सुई द्वारा 5 मिनट में केन्द्र पर "
       "अन्तरित कोण है (a) 30° (b) 60° (c) 2½° (d) 10°"),
    _q(2, "A", 6, "arithmetic-progressions",
       "निम्नलिखित प्रश्नों (i से vi) में रिक्त स्थानों की पूर्ति "
       "करते हुए उत्तर-पुस्तिका में लिखिए। (i) यदि 18, a, 10 "
       "समान्तर श्रेढ़ी में है, तो a = _________। (ii) बिन्दु "
       "P(7, −3) और बिन्दु Q(3, 9) के मध्य बिन्दु के निर्देशांक "
       "_________ है। (iii) sin60° cosec60° + cos30° sec30° का मान "
       "__________ है। (iv) एक ठोस अर्धगोले का व्यास 14 सेमी है, तो "
       "इसका सम्पूर्ण पृष्ठीय क्षेत्रफल _____________ है। (v) बंटन "
       "1, 4, 5, 6, 4, 7, 9, 2, 4, 3, 5 का बहुलक ____________ है। "
       "(vi) किसी वर्ग अन्तराल के लिए वर्ग चिन्ह 17 है। यदि उपरि "
       "वर्ग सीमा 24 है, तो निचली वर्ग सीमा ____________ है।"),
    _q(3, "A", 12, "areas-related-to-circles",
       "अति लघुत्तरात्मक प्रश्न (i से xii)। (i) यदि एक वृत्त की "
       "त्रिज्या 14 सेमी है तथा चाप की लम्बाई 22 सेमी है, तो उस चाप "
       "द्वारा केन्द्र पर अन्तरित कोण ज्ञात कीजिए। (ii) यदि एक घन "
       "का सम्पूर्ण पृष्ठीय क्षेत्रफल 864 वर्ग सेमी है, तो इसके एक "
       "फलक का पृष्ठीय क्षेत्रफल ज्ञात कीजिए। (iii) निम्न "
       "बारम्बारता बंटन का माध्यक ज्ञात कीजिए। x : 3, 5, 7, 9; "
       "f : 6, 7, 5, 6 (iv) एक पासे को एक बार फेंकने पर 5 से बड़ा "
       "अंक आने की प्रायिकता ज्ञात कीजिए। (v) एक लम्बवृत्तीय शंकु "
       "और बेलन समान त्रिज्या और समान ऊँचाई के हैं। यदि शंकु का "
       "आयतन 66 घन सेमी है, तो बेलन का आयतन ज्ञात कीजिए। (vi) निम्न "
       "आँकड़ों का माध्यक ज्ञात कीजिए। 19, 17, 25, 27, 18, 20, 29 "
       "(vii) दो खिलाड़ी राम और श्याम शतरंज का एक मैच खेलते हैं। यह "
       "ज्ञात है कि राम द्वारा मैच जीतने की प्रायिकता 4/5 है। श्याम "
       "के जीतने की प्रायिकता ज्ञात कीजिए। (viii) दो घनों, जिनमें से "
       "प्रत्येक की भुजा 2 सेमी है, के संलग्न फलकों को मिलाकर एक "
       "ठोस घनाभ बनाया जाता है। इससे प्राप्त घनाभ का आयतन ज्ञात "
       "कीजिए। (ix) प्रथम दस धनात्मक विषम प्राकृत संख्याओं का "
       "समान्तर माध्य ज्ञात कीजिए। (x) एक थैले में 6 लाल व 7 सफेद "
       "गेंदें हैं। इस थैले में से एक गेंद यादृच्छया निकाली जाती "
       "है। निकाली गई गेंद की सफेद होने की प्रायिकता ज्ञात कीजिए। "
       "(xi) यदि एक ठोस अर्धगोले का वक्र पृष्ठीय क्षेत्रफल 50π वर्ग "
       "सेमी है, तो उस अर्धगोले की त्रिज्या ज्ञात कीजिए। (xii) यदि "
       "5, 7, 9, 4, 3, (x + 2) का समान्तर माध्य 6 हो, तो x का मान "
       "ज्ञात कीजिए।"),
    _q(4, "B", 2, "real-numbers",
       "संख्या 12, 15 और 21 का अभाज्य गुणनखंडन विधि द्वारा HCF और "
       "LCM ज्ञात कीजिए।"),
    _q(5, "B", 2, "polynomials",
       "यदि द्विघात बहुपद 3x² − 5x + 9 के शून्यक α और β हो, तो "
       "(α + β) तथा αβ ज्ञात कीजिए।"),
    _q(6, "B", 2, "pair-of-linear-equations",
       "विलोपन विधि का प्रयोग करके, निम्न रैखिक समीकरण युग्म के सभी "
       "संभव हल ज्ञात कीजिए : 3x + 5y = 7, 6x + y = −4"),
    _q(7, "B", 2, "arithmetic-progressions",
       "समान्तर श्रेढ़ी 7, 13, 19, . . . . , 205 में पदों की संख्या "
       "ज्ञात कीजिए।"),
    _q(8, "B", 2, "triangles",
       "दी गई आकृति में DE || BC हो, तो x का मान ज्ञात कीजिए। "
       "(आकृति में AD = (x + 2), DB = 6, AE = 4 तथा EC = 8 है।)"),
    _q(9, "B", 2, "coordinate-geometry",
       "बिन्दुओं (5, 3) और (−3, −2) को मिलाने वाला रेखाखण्ड x-अक्ष "
       "द्वारा किस अनुपात में विभाजित होता है?"),
    _q(10, "B", 2, "introduction-to-trigonometry",
       "4cot²45° − sec²60° + sin²60° का मान ज्ञात कीजिए।"),
    _q(11, "B", 2, "some-applications-of-trigonometry",
       "12 मीटर लम्बी एक सीढ़ी, एक उर्ध्वाधर दीवार के शिखर तक "
       "पहुँचती है। यदि यह सीढ़ी दीवार के साथ 60° का कोण बनाती है, "
       "तो दीवार की ऊँचाई ज्ञात कीजिए।"),
    _q(12, "B", 2, "circles",
       "एक वृत्त के परिगत एक चतुर्भुज ABCD खींचा गया है। सिद्ध "
       "कीजिए कि AB + CD = AD + BC। (दी गई आकृति में वृत्त भुजाओं "
       "AB, BC, CD तथा DA को क्रमशः P, Q, R तथा S पर स्पर्श करता "
       "है।)"),
    _q(13, "B", 2, "areas-related-to-circles",
       "वृत्त के चाप द्वारा वृत्त के केन्द्र पर अन्तरित कोण 50° है। "
       "यदि चाप की लम्बाई 5π सेमी हो, तो उस वृत्त की त्रिज्या ज्ञात "
       "कीजिए।"),
    _q(14, "C", 3, "arithmetic-progressions",
       "समान्तर श्रेढ़ी के प्रथम 15 पदों का योगफल ज्ञात कीजिए, जिसका "
       "n वाँ पद a_n = 3 + 2n है। अथवा एक समान्तर श्रेढ़ी में 60 पद "
       "हैं। यदि उसका प्रथम पद तथा अंतिम पद क्रमशः 7 तथा 125 हैं, तो "
       "उसका 32 वाँ पद ज्ञात कीजिए।"),
    _q(15, "C", 3, "coordinate-geometry",
       "बिन्दुओं (4, 0) और (0, −8) को मिलाने वाले रेखाखण्ड को 4 "
       "बराबर भागों में विभाजित करने वाले बिन्दुओं के निर्देशांक "
       "ज्ञात कीजिए। अथवा बिन्दु A के निर्देशांक ज्ञात कीजिए, जहाँ "
       "AB एक वृत्त का व्यास है, जिसका केन्द्र (2, −3) है तथा B के "
       "निर्देशांक (1, 4) है।"),
    _q(16, "C", 3, "circles",
       "सिद्ध कीजिए कि दो संकेंद्रीय वृत्तों में बड़े वृत्त की जीवा "
       "जो छोटे वृत्त को स्पर्श करती है, स्पर्श बिन्दु पर "
       "समद्विभाजित होती है। अथवा सिद्ध कीजिए कि बाह्य बिन्दु से "
       "वृत्त पर खींची गई स्पर्श रेखाओं की लम्बाइयाँ बराबर होती "
       "हैं।"),
    _q(17, "C", 3, "statistics",
       "निम्न बारम्बारता बंटन का माध्य ज्ञात कीजिए। x : 5, 6, 7, 8, "
       "9, 10, 11; f : 5, 8, 9, 12, 6, 6, 4 अथवा यदि निम्न बंटन का "
       "माध्य 7 हो, तो P का मान ज्ञात कीजिए। x : 2, 5, P, 9, 10; "
       "f : 1, 5, 4, 7, 3"),
    _q(18, "D", 4, "quadratic-equations",
       "दो संख्याओं के वर्गों का अन्तर 180 है। छोटी संख्या का वर्ग "
       "बड़ी संख्या का आठ गुना है। दोनों संख्याएँ ज्ञात कीजिए। अथवा "
       "दो क्रमागत धनात्मक पूर्णांक ज्ञात कीजिए, जिनके वर्गों का योग "
       "365 हो।"),
    _q(19, "D", 4, "introduction-to-trigonometry",
       "सिद्ध कीजिए कि 1/(1 + sinθ) + 1/(1 − sinθ) = 2sec²θ अथवा "
       "सिद्ध कीजिए कि sin²θcosθ + cos³θ + tanθ sinθ = secθ"),
    _q(20, "D", 4, "statistics",
       "निम्न बारम्बारता बंटन का माध्यक ज्ञात कीजिए। वर्ग : 7 – 17, "
       "17 – 27, 27 – 37, 37 – 47, 47 – 57, 57 – 67; बारम्बारता : "
       "22, 18, 20, 12, 15, 13 अथवा निम्न बारम्बारता बंटन का बहुलक "
       "ज्ञात कीजिए। वर्ग : 2 – 11, 11 – 20, 20 – 29, 29 – 38, "
       "38 – 47; बारम्बारता : 15, 16, 17, 12, 11"),
]

# Wave 66: RBSE Class 12 Mathematics 2025 (SS-15-Mathematics),
# bilingual printed paper — English half transcribed from the
# source PDF's text layer, every formula cross-checked against
# its page images; Hindi half transcribed from the page images.
_RBSE12_2025 = [
    _q(1, "A", 18, "relations-and-functions",
       "Multiple Choice Questions: (i) Let R be the relation "
       "defined on the set N and given by {(a, b) : a = b − 2, "
       "b < 6}, then range of R will be - (A) {1, 2, 3} "
       "(B) {1, 2, 3, 4, 5} (C) {3, 4, 5} (D) {3, 4, 5, 6} (ii) The "
       "principal value of cos⁻¹(−1/2) is - (A) 2π/3 (B) π/6 "
       "(C) π/3 (D) −π/3 (iii) A = [a_ij]_{m×n} is a column matrix, "
       "if - (A) m > 1 (B) m = 1 (C) n > 1 (D) n = 1 (iv) Value of "
       "|cosθ −sinθ; sinθ cosθ| will be - (A) 0 (B) 1 (C) cos2θ "
       "(D) sin2θ (v) Let A be a nonsingular square matrix of order "
       "3 × 3. Then |adj A| is equal to - (A) |A|² (B) |A|³ (C) |A| "
       "(D) 2|A| (vi) If x² + y² = 2, then dy/dx is equal to - "
       "(A) (1 − 2x)/(2y) (B) 2y/(1 − 2x) (C) −x/y (D) −y/x (vii) "
       "Which of the following function is strictly decreasing "
       "function in interval (0, π/2)? (A) sin x (B) cos x "
       "(C) tan x (D) sin 2x (viii) f(x) = {2x − 5, if x ≤ 3; 2k, "
       "if x > 3}, is continuous at x = 3, then value of k will "
       "be - (A) 1 (B) 1/6 (C) 6 (D) 1/2 (ix) Value of ∫(0 to 1) "
       "(sin⁻¹x + cos⁻¹x) dx will be - (A) π/2 (B) π (C) π²/4 "
       "(D) π² (x) The area bounded by x-axis, y-axis, y = cos x, "
       "0 ≤ x ≤ π/2 will be - (A) 1 (B) 0 (C) −1 (D) 2 (xi) "
       "Particular solution of differential equation dy/dx + x = 0 "
       "at x = 0, y = 1 will be - (A) y + x²/2 + 1 = 0 "
       "(B) y + x²/2 = 1 (C) y + 2x² + 1 = 0 (D) y + 2x² = 1 (xii) "
       "If magnitude of two vectors a and b are 1 and 2 "
       "respectively and a · b = 1, then angle between these "
       "vectors will be - (A) π/2 (B) π/4 (C) π/3 (D) π/6 (xiii) "
       "Value of î · (k̂ × ĵ) − ĵ · (k̂ × î) + k̂ · (î × ĵ) is - "
       "(A) 1 (B) 0 (C) −3 (D) −1 (xiv) Direction cosines of vector "
       "a = î + ĵ − 2k̂ are - (A) 1/4, 1/4, −1/2 (B) 1/√6, 1/√6, "
       "−2/√6 (C) 1/√2, 1/√2, −√2 (D) 1, 1, −2 (xv) The cartesian "
       "equation of the line passing through point (1, 2, 3) and "
       "parallel to the line (x + 3)/3 = (y − 4)/5 = (z + 8)/6 "
       "will be - (A) (x − 1)/3 = (y − 2)/5 = (z − 3)/6 "
       "(B) (x + 1)/3 = (y + 2)/5 = (z + 3)/6 (C) (x + 3)/1 = "
       "(y − 4)/2 = (z + 8)/3 (D) (x + 2)/3 = (y − 6)/5 = "
       "(z + 5)/6 (xvi) A coin is tossed three times, then the "
       "probability to get Head at least two times will be - "
       "(A) 1/8 (B) 3/8 (C) 1/2 (D) 5/8 (xvii) Probabilities of "
       "solving specific problem independently by students A and B "
       "are 1/2 and 1/3 respectively. If both try to solve the "
       "problem independently, then the probability that the "
       "problem will be solved - (A) 1/6 (B) 5/6 (C) 1/3 (D) 2/3 "
       "(xviii) If P(A) = 4/7, P(B) = 3/7 and A and B are "
       "independent events, then value of P(A ∩ B) will be - "
       "(A) 1/7 (B) 12/49 (C) 37/49 (D) 1"),
    _q(2, "A", 6, "inverse-trigonometric-functions",
       "Fill in the blanks: (i to vi). (i) ________ is the "
       "principal value of sin⁻¹(√3/2). (ii) If |2 1; 1 2| − "
       "k|1 0; 0 1| = 0, then k = ________. (iii) The total "
       "revenue in Rupees received from the sale of x units of a "
       "product is given by R(x) = 2x² + 25x. Then marginal "
       "revenue = ________ when x = 10. (iv) ∫√(x² + 3x + 9/4) "
       "dx = __________. (v) The integrating factor of "
       "differential equation dy/dx + y = x is ________. (vi) The "
       "projection of the vector î + 2ĵ on x-axis is ________."),
    _q(3, "A", 12, "matrices",
       "Very short answer type questions: (i) If A = [[−1], [2]] "
       "and B = [−1 1], then find BA. (ii) Find the value of "
       "Δ = |3 2 3; 2 2 3; 3 2 3|. (iii) Draw a graphical "
       "representation of the function f(x) = |x| in your answer "
       "book. (iv) If y = e^(tan⁻¹x), then find dy/dx. (v) "
       "Differentiate 1/√(2x + 3) with respect to x. (vi) Find the "
       "rate of change of the area of a circle with respect to its "
       "radius r when r = 2.5 cm. (vii) Evaluate ∫x sin x dx. "
       "(viii) Find the area lying in the first quadrant and "
       "bounded by the circle x² + y² = 4. (ix) Find the order and "
       "degree of the differential equation xy(d²y/dx²) + "
       "x(dy/dx)² − y = 0. (x) Write Associative property for "
       "addition of any three vectors a, b and c. (xi) Find the "
       "vector equation of the line passing through the points "
       "(3, 2, 0) and (1, 2, 5). (xii) Given that E and F are "
       "events such that P(F) = 0.3 and P(E ∩ F) = 0.2, find "
       "P(E/F)."),
    _q(4, "B", 2, "relations-and-functions",
       "If three functions f, g and h are defined in set N, where "
       "f(x) = 2x, g(y) = 3y + 4 and h(z) = sin z ∀ x, y and "
       "z ∈ N, prove that h∘(g∘f) = (h∘g)∘f."),
    _q(5, "B", 2, "inverse-trigonometric-functions",
       "Prove that tan⁻¹(1/2) + tan⁻¹(1/3) = π/4."),
    _q(6, "B", 2, "matrices",
       "Construct a 2 × 2 matrix [a_ij], whose elements are given "
       "by a_ij = (1/2)|i + 2j|."),
    _q(7, "B", 2, "determinants",
       "Find the area of the triangle, whose vertices are (3, 0), "
       "(4, 2) and (5, 1)."),
    _q(8, "B", 2, "continuity-and-differentiability",
       "Find the derivative of the function given by f(x) = "
       "(1 + x)(1 − x) and hence find f′(1)."),
    _q(9, "B", 2, "continuity-and-differentiability",
       "If y = A sin x + B cos x, then prove that d²y/dx² + y = 0."),
    _q(10, "B", 2, "application-of-derivatives",
       "Find two positive numbers whose sum is 15 and the sum of "
       "whose squares is minimum."),
    _q(11, "B", 2, "integrals",
       "Find ∫√(3 − 2x − x²) dx."),
    _q(12, "B", 2, "application-of-integrals",
       "Find the area of circle x² + y² = 16 using applications of "
       "integrals."),
    _q(13, "B", 2, "vector-algebra",
       "Find the magnitude of two vectors a and b, having the same "
       "magnitude and such that the angle between them is 60° and "
       "value of their scalar product is 1/2."),
    _q(14, "C", 3, "integrals",
       "Find ∫(2x + 9)/(x² + 8x + 25) dx. OR Find ∫ sin x/"
       "sin(x + a) dx."),
    _q(15, "C", 3, "differential-equations",
       "Find the general solution of the differential equation "
       "y dx − x dy − 2y² dy = 0. OR Prove that y = e^(−2x) is a "
       "solution of differential equation: d²y/dx² + 4(dy/dx) + "
       "4y = 0."),
    _q(16, "C", 3, "three-dimensional-geometry",
       "Find the direction cosines of the sides of the triangle "
       "whose vertices are A(3, 5, −4), B(−1, 1, 2) and "
       "C(−5, −5, −2). OR Show that the line through the points "
       "(1, 2, 3), (3, 4, 5) is perpendicular to the line through "
       "the points (−1, 2, 4), (2, −1, 4)."),
    _q(17, "C", 3, "probability",
       "If A and B are two independent events, then prove that the "
       "probability of occurrence of at least one of A and B is "
       "given by = 1 − P(A′)P(B′). OR A card from a pack of 52 "
       "cards is lost. From remaining cards of the pack, two cards "
       "are drawn and they are found to be both diamonds. Find the "
       "probability of the lost card being a diamond."),
    _q(18, "D", 4, "integrals",
       "Find the value of ∫(1 to 3) dx/(x²(x + 1)). OR Solve "
       "∫ 1/√((x − a)(x − b)) dx."),
    _q(19, "D", 4, "three-dimensional-geometry",
       "Find the vector equation of the line passing through the "
       "point (1, 2, −4) and perpendicular to the both lines: "
       "(x − 8)/3 = (y + 19)/(−16) = (z − 10)/7 and (x − 15)/3 = "
       "(y − 29)/8 = (z − 5)/(−5). OR Find shortest distance "
       "between the following pair of lines: x/2 = y/2 = z/1 and "
       "(x − 5)/4 = (y − 2)/1 = (z − 3)/8."),
    _q(20, "D", 4, "linear-programming",
       "Determine graphically the maximum value of the objective "
       "function Z = 3x + 2y subject to the following constraints: "
       "x − y + 2 ≥ 0, x + 2y ≤ 7 and x ≥ 0, y ≥ 0. OR Determine "
       "graphically the minimum value of the objective function "
       "Z = x + 3y subject to the following constraints: x ≥ y, "
       "x + y ≥ 4, x + 2y ≤ 8 and x ≥ 0, y ≥ 0."),
]

# Wave 66: the Hindi half of the same printed bilingual paper,
# transcribed question-by-question from the source's page images.
_RBSE12_2025_HI = [
    _q(1, "A", 18, "relations-and-functions",
       "बहुविकल्पीय प्रश्न: (i) मान लीजिए कि समुच्चय N में परिभाषित "
       "{(a, b) : a = b − 2, b < 6} द्वारा प्रदत्त सम्बन्ध R है, तो "
       "R का परिसर होगा – (a) {1, 2, 3} (b) {1, 2, 3, 4, 5} "
       "(c) {3, 4, 5} (d) {3, 4, 5, 6} (ii) cos⁻¹(−1/2) का मुख्य "
       "मान है – (a) 2π/3 (b) π/6 (c) π/3 (d) −π/3 (iii) "
       "A = [a_ij]_{m×n} एक स्तंभ आव्यूह होगा, यदि – (a) m > 1 "
       "(b) m = 1 (c) n > 1 (d) n = 1 (iv) |cosθ −sinθ; sinθ cosθ| "
       "का मान होगा – (a) 0 (b) 1 (c) cos2θ (d) sin2θ (v) यदि A, "
       "3 × 3 कोटि का एक व्युत्क्रमणीय वर्ग आव्यूह है, तो |adj A| "
       "का मान होगा – (a) |A|² (b) |A|³ (c) |A| (d) 2|A| (vi) यदि "
       "x² + y² = 2 हो, तो dy/dx बराबर होगा – (a) (1 − 2x)/(2y) "
       "(b) 2y/(1 − 2x) (c) −x/y (d) −y/x (vii) निम्नलिखित में से "
       "कौन-सा फलन अन्तराल (0, π/2) में निरन्तर ह्रासमान है? "
       "(a) sin x (b) cos x (c) tan x (d) sin 2x (viii) f(x) = "
       "{2x − 5 ; यदि x ≤ 3; 2k ; यदि x > 3}, x = 3 पर संतत हो, तो "
       "k का मान होगा – (a) 1 (b) 1/6 (c) 6 (d) 1/2 (ix) "
       "∫₀¹(sin⁻¹x + cos⁻¹x) dx का मान होगा – (a) π/2 (b) π "
       "(c) π²/4 (d) π² (x) x – अक्ष, y – अक्ष, y = cos x, "
       "0 ≤ x ≤ π/2 से घिरे क्षेत्र का क्षेत्रफल होगा – (a) 1 "
       "(b) 0 (c) −1 (d) 2 (xi) अवकल समीकरण dy/dx + x = 0 का "
       "x = 0, y = 1 पर विशिष्ट हल होगा – (a) y + x²/2 + 1 = 0 "
       "(b) y + x²/2 = 1 (c) y + 2x² + 1 = 0 (d) y + 2x² = 1 (xii) "
       "दो सदिशों a⃗ और b⃗ के परिमाण क्रमशः 1 और 2 है तथा a⃗ · b⃗ = 1 "
       "हो, तो इन सदिशों के बीच का कोण होगा – (a) π/2 (b) π/4 "
       "(c) π/3 (d) π/6 (xiii) î · (k̂ × ĵ) − ĵ · (k̂ × î) + "
       "k̂ · (î × ĵ) का मान है – (a) 1 (b) 0 (c) −3 (d) −1 (xiv) "
       "सदिश a⃗ = î + ĵ − 2k̂ के दिक्-कोसाइन है – (a) 1/4, 1/4, "
       "−1/2 (b) 1/√6, 1/√6, −2/√6 (c) 1/√2, 1/√2, −√2 (d) 1, 1, "
       "−2 (xv) बिन्दु (1, 2, 3) से जाने वाली तथा रेखा "
       "(x + 3)/3 = (y − 4)/5 = (z + 8)/6 के समान्तर रेखा का "
       "कार्तीय समीकरण होगा – (a) (x − 1)/3 = (y − 2)/5 = "
       "(z − 3)/6 (b) (x + 1)/3 = (y + 2)/5 = (z + 3)/6 "
       "(c) (x + 3)/1 = (y − 4)/2 = (z + 8)/3 (d) (x + 2)/3 = "
       "(y − 6)/5 = (z + 5)/6 (xvi) एक सिक्के को तीन बार उछाला "
       "जाएँ, तो न्यूनतम दो बार चित आने की प्रायिकता होगी – "
       "(a) 1/8 (b) 3/8 (c) 1/2 (d) 5/8 (xvii) एक विशेष समस्या को "
       "छात्रों A और B द्वारा स्वतंत्र रूप से हल करने की "
       "प्रायिकताएँ क्रमशः 1/2 और 1/3 है। यदि दोनों, स्वतंत्र रूप "
       "से समस्या हल करें, तो समस्या के हल होने की प्रायिकता होगी "
       "– (a) 1/6 (b) 5/6 (c) 1/3 (d) 2/3 (xviii) यदि P(A) = 4/7, "
       "P(B) = 3/7 और A तथा B स्वतंत्र घटनाएँ है, तो P(A ∩ B) का "
       "मान होगा – (a) 1/7 (b) 12/49 (c) 37/49 (d) 1"),
    _q(2, "A", 6, "inverse-trigonometric-functions",
       "रिक्त स्थानों की पूर्ति कीजिए: (i से vi) (i) sin⁻¹(√3/2) का "
       "मुख्य मान ............. है। (ii) यदि |2 1; 1 2| − k|1 0; "
       "0 1| = 0 हो, तो k = ............... (iii) एक उत्पाद की x "
       "इकाइयों के विक्रय से प्राप्त कुल आय रूपयों में "
       "R(x) = 2x² + 25x से प्रदत्त है। जब x = 10 है तो सीमान्त आय "
       "= ............... (iv) ∫√(x² + 3x + 9/4) dx = "
       ".................... (v) अवकल समीकरण dy/dx + y = x का "
       "समाकलन गुणांक ............... है। (vi) सदिश î + 2ĵ का "
       "x – अक्ष पर प्रक्षेप ............... है।"),
    _q(3, "A", 12, "matrices",
       "अति लघुत्तरात्मक प्रश्न: (i) यदि A = [[−1], [2]] तथा "
       "B = [−1 1] हो, तो BA ज्ञात कीजिए। (ii) Δ = |3 2 3; 2 2 3; "
       "3 2 3| का मान ज्ञात कीजिए। (iii) अपनी उत्तर पुस्तिका में "
       "फलन f(x) = |x| का आलेखीय निरूपण कीजिए। (iv) यदि "
       "y = e^(tan⁻¹x) हो, तो dy/dx ज्ञात कीजिए। (v) 1/√(2x + 3) "
       "का x के सापेक्ष अवकलन कीजिए। (vi) वृत्त के क्षेत्रफल "
       "परिवर्तन की दर इसकी त्रिज्या r के सापेक्ष ज्ञात कीजिए जबकि "
       "r = 2.5 सेमी है। (vii) हल कीजिए ∫x sin x dx। (viii) प्रथम "
       "चतुर्थांश में वृत्त x² + y² = 4 से घिरे क्षेत्र का क्षेत्रफल "
       "ज्ञात कीजिए। (ix) अवकल समीकरण xy(d²y/dx²) + x(dy/dx)² − "
       "y = 0 की कोटि एवं घात ज्ञात कीजिए। (x) तीन सदिशों a⃗, b⃗ "
       "और c⃗ के योगफल के लिए साहचर्य गुणधर्म लिखिए। (xi) बिन्दुओं "
       "(3, 2, 0) और (1, 2, 5) से होकर जाने वाली रेखा का सदिश "
       "समीकरण ज्ञात कीजिए। (xii) यदि E और F इस प्रकार की घटनाएँ "
       "है कि P(F) = 0.3 और P(E ∩ F) = 0.2, तो P(E/F) ज्ञात "
       "कीजिए।"),
    _q(4, "B", 2, "relations-and-functions",
       "यदि तीन फलन f, g तथा h समुच्चय N में परिभाषित है, जहाँ "
       "f(x) = 2x, g(y) = 3y + 4 तथा h(z) = sin z ∀ x, y तथा "
       "z ∈ N, सिद्ध कीजिए h∘(g∘f) = (h∘g)∘f।"),
    _q(5, "B", 2, "inverse-trigonometric-functions",
       "सिद्ध कीजिए tan⁻¹(1/2) + tan⁻¹(1/3) = π/4।"),
    _q(6, "B", 2, "matrices",
       "एक ऐसे 2 × 2 आव्यूह [a_ij] की रचना कीजिए, जिसके अवयव "
       "a_ij = (1/2)|i + 2j| द्वारा प्रदत्त हो।"),
    _q(7, "B", 2, "determinants",
       "एक त्रिभुज का क्षेत्रफल ज्ञात कीजिए, जिसके शीर्ष (3, 0), "
       "(4, 2) और (5, 1) है।"),
    _q(8, "B", 2, "continuity-and-differentiability",
       "f(x) = (1 + x)(1 − x) द्वारा प्रदत्त फलन का अवकलन ज्ञात "
       "कीजिए और इस प्रकार f′(1) ज्ञात कीजिए।"),
    _q(9, "B", 2, "continuity-and-differentiability",
       "यदि y = A sin x + B cos x हो, तो सिद्ध कीजिए कि "
       "d²y/dx² + y = 0।"),
    _q(10, "B", 2, "application-of-derivatives",
       "ऐसी दो धन संख्याएँ ज्ञात कीजिए जिनका योग 15 है और जिनके "
       "वर्गों का योग न्यूनतम हो।"),
    _q(11, "B", 2, "integrals",
       "∫√(3 − 2x − x²) dx ज्ञात कीजिए।"),
    _q(12, "B", 2, "application-of-integrals",
       "समाकलन के अनुप्रयोग द्वारा वृत्त x² + y² = 16 का क्षेत्रफल "
       "ज्ञात कीजिए।"),
    _q(13, "B", 2, "vector-algebra",
       "दो सदिशों a⃗ और b⃗ के परिमाण ज्ञात कीजिए, यदि इनके परिमाण "
       "समान है और इनके बीच का कोण 60° व इनके अदिश गुणनफल का मान "
       "1/2 है।"),
    _q(14, "C", 3, "integrals",
       "ज्ञात कीजिए ∫(2x + 9)/(x² + 8x + 25) dx। अथवा ज्ञात कीजिए "
       "∫ sin x/sin(x + a) dx।"),
    _q(15, "C", 3, "differential-equations",
       "अवकल समीकरण y dx − x dy − 2y² dy = 0 का व्यापक हल ज्ञात "
       "कीजिए। अथवा सिद्ध कीजिए y = e^(−2x) अवकल समीकरण "
       "d²y/dx² + 4(dy/dx) + 4y = 0 का एक हल है।"),
    _q(16, "C", 3, "three-dimensional-geometry",
       "एक त्रिभुज की भुजाओं के दिक्-कोसाइन ज्ञात कीजिए यदि त्रिभुज "
       "के शीर्ष बिन्दु A(3, 5, −4), B(−1, 1, 2) और C(−5, −5, −2) "
       "हैं। अथवा दर्शाइए कि बिन्दुओं (1, 2, 3), (3, 4, 5) से होकर "
       "जाने वाली रेखा, बिन्दुओं (−1, 2, 4), (2, −1, 4) से जाने "
       "वाली रेखा पर लम्ब है।"),
    _q(17, "C", 3, "probability",
       "यदि A और B स्वतंत्र घटनाएँ है तो सिद्ध कीजिए कि A और B में "
       "से कम से कम एक के होने की प्रायिकता = 1 − P(A′)P(B′) "
       "होगी। अथवा 52 ताशों की गड्डी से एक पत्ता खो जाता है। शेष "
       "पत्तों से दो पत्ते निकाले जाते है जो ईंट के है। खो गये "
       "पत्ते के ईंट का होने की प्रायिकता ज्ञात कीजिए।"),
    _q(18, "D", 4, "integrals",
       "∫₁³ dx/(x²(x + 1)) का मान ज्ञात कीजिए। अथवा "
       "∫ 1/√((x − a)(x − b)) dx का हल कीजिए।"),
    _q(19, "D", 4, "three-dimensional-geometry",
       "बिन्दु (1, 2, −4) से जाने वाली और दोनों रेखाओं (x − 8)/3 = "
       "(y + 19)/(−16) = (z − 10)/7 और (x − 15)/3 = (y − 29)/8 = "
       "(z − 5)/(−5) के लम्ब रेखा का सदिश समीकरण ज्ञात कीजिए। अथवा "
       "निम्नलिखित रेखा युग्म के बीच की न्यूनतम दूरी ज्ञात कीजिए : "
       "x/2 = y/2 = z/1 और (x − 5)/4 = (y − 2)/1 = (z − 3)/8।"),
    _q(20, "D", 4, "linear-programming",
       "आलेखीय विधि द्वारा उद्देश्य फलन Z = 3x + 2y का अधिकतम मान "
       "निम्नलिखित व्यवरोधों के अंतर्गत ज्ञात कीजिए : x − y + 2 ≥ 0, "
       "x + 2y ≤ 7 तथा x ≥ 0, y ≥ 0 अथवा आलेखीय विधि द्वारा "
       "उद्देश्य फलन Z = x + 3y का न्यूनतम मान निम्नलिखित व्यवरोधों "
       "के अंतर्गत ज्ञात कीजिए : x ≥ y, x + y ≥ 4, x + 2y ≤ 8 तथा "
       "x ≥ 0, y ≥ 0"),
]

# Wave 66: CBSE Class 12 Mathematics 2022 Term 2 — Hindi-medium
# version of cbse-12-2022-term2 (the same printed bilingual
# paper, Q.P. Code 65/2/1). All 14 questions transcribed from
# the Hindi half of the paper, read from the source's page
# images and cross-checked against its English half.
_CBSE12_2022_TERM2_HI = [
    _q(1, "A", 2, "differential-equations",
       "अवकल समीकरण [d/dx (xy²)] · (dy/dx) + y = 0 की कोटि और घात "
       "का गुणनफल ज्ञात कीजिए।"),
    _q(2, "A", 2, "integrals",
       "(क) ज्ञात कीजिए : ∫ (sin 3x)/(sin x) dx अथवा (ख) मान ज्ञात "
       "कीजिए : ∫(0 to (1/2) log 3) e^x/(e^(2x) + 1) dx"),
    _q(3, "A", 2, "vector-algebra",
       "दो मात्रक सदिशों a⃗ और b⃗ के लिए |2a⃗ + 3b⃗| = |3a⃗ − 2b⃗| है। "
       "a⃗ तथा b⃗ के बीच का कोण ज्ञात कीजिए।"),
    _q(4, "A", 2, "probability",
       "पासों के एक युग्म को उछाला गया। दोनों पासों पर आई संख्याओं "
       "का योगफल एक सम संख्या है। कम-से-कम एक पासे पर संख्या 3 आने "
       "की प्रायिकता ज्ञात कीजिए।"),
    _q(5, "A", 2, "probability",
       "एक विशेष प्रश्न को A और B द्वारा स्वतंत्र रूप से हल करने "
       "की प्रायिकताएँ क्रमशः 2/3 और 3/5 हैं। यदि दोनों स्वतंत्र "
       "रूप से प्रश्न को हल करने की कोशिश करते हैं, तो प्रश्न के "
       "हल हो जाने की प्रायिकता ज्ञात कीजिए।"),
    _q(6, "A", 2, "three-dimensional-geometry",
       "रेखा PQ जो बिन्दुओं P(2, 2, 1) तथा Q(5, 1, −2) से गुज़रती "
       "है, का कार्तीय समीकरण लिखिए। अतः रेखा PQ पर उस बिन्दु का "
       "y-निर्देशांक ज्ञात कीजिए जिसका z-निर्देशांक −2 है।"),
    _q(7, "B", 3, "vector-algebra",
       "ABCD एक समांतर चतुर्भुज है जिसमें AC⃗ = î + ĵ और "
       "BD⃗ = 2î + ĵ + k̂ हैं। AB⃗ और AD⃗ ज्ञात कीजिए। समांतर "
       "चतुर्भुज ABCD का क्षेत्रफल भी ज्ञात कीजिए।"),
    _q(8, "B", 3, "integrals",
       "(क) मान ज्ञात कीजिए : ∫(0 to 1) tan⁻¹x dx अथवा (ख) ज्ञात "
       "कीजिए : ∫ 2x/(x² + 3x + 2) dx"),
    _q(9, "B", 3, "differential-equations",
       "अवकल समीकरण (y + 3x²)(dx/dy) = x का विशिष्ट हल ज्ञात "
       "कीजिए, दिया गया है y = 1 जब x = 1।"),
    _q(10, "B", 3, "three-dimensional-geometry",
       "(क) बिन्दुओं (2, 1, 0), (3, −2, −2) और (1, 1, −7) से "
       "गुज़रने वाले समतल का समीकरण ज्ञात कीजिए। इस समतल की "
       "मूल-बिन्दु से दूरी भी ज्ञात कीजिए। अथवा (ख) रेखाओं "
       "x = (y − 1)/2 = (z − 2)/3 तथा x + 1 = (y + 2)/2 = "
       "(z − 1)/3 के बीच की दूरी ज्ञात कीजिए।"),
    _q(11, "C", 4, "three-dimensional-geometry",
       "रेखा (x − 2)/3 = (y + 1)/4 = (z − 2)/12 और समतल "
       "x − y + z = 5 के प्रतिच्छेदन बिन्दु की बिन्दु (−1, −5, "
       "−10) से दूरी ज्ञात कीजिए।"),
    _q(12, "C", 4, "integrals",
       "मान ज्ञात कीजिए : ∫(0 to 1) x(1 − x)^n dx"),
    _q(13, "C", 4, "application-of-integrals",
       "(क) समाकलन के प्रयोग से, वक्र 4x² + 4y² = 9 और रेखा "
       "2x + 2y = 3 के बीच घिरे लघु क्षेत्र का क्षेत्रफल ज्ञात "
       "कीजिए। अथवा (ख) यदि वक्र y² = 4ax और रेखा x = 4a से घिरे "
       "क्षेत्र का क्षेत्रफल 256/3 वर्ग इकाई है, तो समाकलन के "
       "प्रयोग से a, जहाँ a > 0, का मान ज्ञात कीजिए।"),
    _q(14, "C", 4, "probability",
       "प्रकरण-अध्ययन आधारित प्रश्न : किसी भी क्रिकेट के मैच के "
       "आरम्भ में, एक सिक्का उछाला जाता है और जो टीम टॉस जीतती है "
       "उसे बल्लेबाजी या गेंदबाजी चुनने का मौका मिलता है। ऐसा "
       "सिक्का अनभिनत होता है जिसमें चित और पट के आने की "
       "प्रायिकताएँ समान होती हैं। उपरोक्त सूचना के आधार पर, "
       "निम्नलिखित प्रश्नों के उत्तर दीजिए : (क) यदि ऐसा सिक्का 2 "
       "बार उछाला जाए, तो पटों की संख्या के लिए प्रायिकता बंटन "
       "ज्ञात कीजिए। (ख) ऐसे सिक्के को 3 बार उछालने पर कम-से-कम "
       "एक चित आने की प्रायिकता ज्ञात कीजिए।"),
]

# Wave 66: ISC (CISCE) Class 12 Mathematics 2025 — English only
# (CISCE publishes ISC papers in English only). Transcribed
# question-by-question from the source PDF's page images (its
# text layer scrambles fractions, matrices and integrals).
# Sections B and C are alternatives in the real paper (attempt
# either); both are typed in full here.
_ISC12_2025 = [
    _q(1, "A", 15, "matrices",
       "In subparts (i) to (xi) choose the correct options and in "
       "subparts (xii) to (xv), answer the questions as instructed. "
       "(i) If A = [[0, a], [0, 0]], then A¹⁶ is: (a) Unit matrix "
       "(b) Null matrix (c) Diagonal matrix (d) Skew matrix (ii) "
       "Which of the following is a homogenous differential "
       "equation? (a) (4x² + 6y + 5) dy − (3y² + 2x + 4) dx = 0 "
       "(b) (xy) dx − (x³ + y³) dy = 0 (c) (x³ + 2y²) dx + 2xy dy = 0 "
       "(d) y² dx + (x² − xy − y²) dy = 0 (iii) Consider the graph "
       "of the function f(x) shown below: (The graph is a diagram "
       "printed in the paper: f stays constant at 1 up to x = 0, "
       "decreases to 0 at x = 1/2, increases back to 1 at x = 1 and "
       "stays constant afterwards.) Statement 1: The function f(x) "
       "is increasing in (1/2, 2). Statement 2: The function f(x) "
       "is strictly increasing in (1/2, 1). Which of the following "
       "is correct with respect to the above statements? (a) "
       "Statement 1 is true and Statement 2 is false. (b) Statement "
       "2 is true and Statement 1 is false. (c) Both the statements "
       "are true. (d) Both the statements are false. (iv) "
       "∫(0 to 1) (x⁴ − 1)/(x² + 1) dx is equal to: (a) 2/3 (b) 1/3 "
       "(c) −2/3 (d) 0 (v) Assertion: Consider the two events A and "
       "B such that n(A) = n(B) and P(A/B) = P(B/A). Reason: The "
       "events A and B are mutually exclusive. (a) Both Assertion "
       "and Reason are true and Reason is the correct explanation "
       "for Assertion. (b) Both Assertion and Reason are true but "
       "Reason is not the correct explanation for Assertion. (c) "
       "Assertion is true and Reason is false. (d) Assertion is "
       "false and Reason is true. (vi) The existence of unique "
       "solution of the system of equations x + y = λ and "
       "5x + ky = 2 depends on: (a) λ only (b) λ/k = 1 (c) both k "
       "and λ (d) k only (vii) A cylindrical popcorn tub of radius "
       "10 cm is being filled with popcorns at the rate of 314 cm³ "
       "per minute. The level of the popcorns in the tub is "
       "increasing at the rate of: (a) 1 cm/minute (b) 0.1 "
       "cm/minute (c) 1.1 cm/minute (d) 0.5 cm/minute (viii) If "
       "f(x) = {x + 2, x < 0; −x² − 2, 0 ≤ x < 1; x, x ≥ 1} then "
       "the number of point(s) of discontinuity of f(x), is / are: "
       "(a) 1 (b) 3 (c) 2 (d) 0 (ix) Assertion: If Set A has m "
       "elements, Set B has n elements and n < m, then the number "
       "of one-one function(s) from A → B is zero. Reason: A "
       "function f: A → B is defined only if all elements in Set A "
       "have an image in Set B. (a) Both Assertion and Reason are "
       "true and Reason is the correct explanation for Assertion. "
       "(b) Both Assertion and Reason are true but Reason is not "
       "the correct explanation for Assertion. (c) Assertion is "
       "true and Reason is false. (d) Assertion is false and "
       "Reason is true. (x) Let X be a discrete random variable. "
       "The probability distribution of X is given below: X : 30, "
       "10, −10; P(X) : 1/5, 3/10, 1/2. Then E(X) will be: (a) 1 "
       "(b) 4 (c) 2 (d) 30 (xi) Statement 1: If 'A' is an "
       "invertible matrix, then (A²)⁻¹ = (A⁻¹)² Statement 2: If "
       "'A' is an invertible matrix, then |A⁻¹| = |A|⁻¹ (a) "
       "Statement 1 is true and Statement 2 is false. (b) Statement "
       "2 is true and Statement 1 is false. (c) Both the statements "
       "are true. (d) Both the statements are false. (xii) Write "
       "the smallest equivalence relation from the set A to A, "
       "where A = {1, 2, 3}. (xiii) For what value of x, is "
       "A = [[0, 1, −2], [−1, 0, 3], [x, −3, 0]] a skew symmetric "
       "matrix? (xiv) Three critics review a book. Odds in favour "
       "of the book are 5:2, 4:3 and 3:4 respectively for the three "
       "critics. Find the probability that all critics are in "
       "favour of the book. (xv) Evaluate: ∫ 5/√(2x + 7) dx"),
    _q(2, "A", 2, "application-of-derivatives",
       "Find the point on the curve y = 2x² − 6x − 4 at which the "
       "tangent is parallel to the x-axis."),
    _q(3, "A", 2, "inverse-trigonometric-functions",
       "Find the value of tan⁻¹x − cot⁻¹x, if (tan⁻¹x)² − "
       "(cot⁻¹x)² = 5π/8."),
    _q(4, "A", 2, "continuity-and-differentiability",
       "(i) If x^y = e^(x − y), prove that dy/dx = logx/"
       "(1 + logx)². OR (ii) If f(x) = log(1 + x) + 1/(1 + x), "
       "show that f(x) attains its minimum value at x = 0."),
    _q(5, "A", 2, "matrices",
       "Three shopkeepers Gaurav, Rizwan and Jacob use carry bags "
       "made of polythene, handmade paper and newspaper. The "
       "number of polythene bags, handmade bags and newspaper bags "
       "used by Gaurav, Rizwan and Jacob are (20, 30, 40), (30, 40, "
       "20) and (40, 20, 30) respectively. One polythene bag costs "
       "₹ 1, one handmade bag is for ₹ 5 and one newspaper bag "
       "costs ₹ 2. Gaurav, Rizwan and Jacob spend ₹ A, ₹ B and ₹ C "
       "respectively on these carry bags. Using the concepts of "
       "matrices and determinants, answer the following questions: "
       "(i) Represent the above information in Matrix form. (ii) "
       "Find the values of ₹ A, ₹ B and ₹ C."),
    _q(6, "A", 2, "continuity-and-differentiability",
       "(i) Differentiate sin⁻¹((2^(x + 1) · 3^x)/(1 + (36)^x)) "
       "with respect to x. OR (ii) Show that tan⁻¹x + tan⁻¹y = C "
       "is the general solution of the differential equation "
       "(1 + x²) dy + (1 + y²) dx = 0."),
    _q(7, "A", 4, "determinants",
       "If x + y + z = 0 then show that |1 1 1; x y z; x³ y³ z³| = "
       "0, using properties of determinant."),
    _q(8, "A", 4, "integrals",
       "(i) Evaluate: ∫ cosx/(3cosx − 5) dx OR (ii) Evaluate: "
       "∫(log x)² dx"),
    _q(9, "A", 4, "application-of-derivatives",
       "(i) If x = tan((1/a) log y) then show that (1 + x²)"
       "(d²y/dx²) + (2x − a)(dy/dx) = 0 OR (ii) The graph of "
       "f(x) = −x³ + 27x − 2 is given below: (The graph is a "
       "diagram printed in the paper: the curve falls to its "
       "turning point A (a, b), rises to its turning point "
       "B (c, d), then falls again.) (a) Find the slope of the "
       "above graph. (b) Find the co-ordinates of turning points, "
       "A and B. (c) Evaluate f″(−2), f(0) and f′(3) and arrange "
       "them in ascending order."),
    _q(10, "A", 4, "probability",
       "Pia, Sia and Dia displayed their paintings in an art "
       "exhibition. The three artists displayed 15, 5 and 10 of "
       "their paintings respectively. A person bought three "
       "paintings from the exhibition. (i) Find the probability "
       "that he bought one painting from each of them. (ii) Find "
       "the probability that he bought all the three paintings "
       "from the same person."),
    _q(11, "A", 6, "integrals",
       "(i) Prove: ∫(π/4 to 3π/4) x/(1 + sinx) dx = (√2 − 1)π OR "
       "(ii) Evaluate: ∫ x²/((x − 1)²(x² + 1)) dx"),
    _q(12, "A", 6, "differential-equations",
       "(i) Solve the differential equation: (x + 5y²)(dy/dx) = y "
       "when x = 2 and y = 1 OR (ii) Find the particular solution "
       "of the differential equation: (x² − 2y²)dx + 2xy dy = 0, "
       "when x = 1 and y = 1"),
    _q(13, "A", 6, "inverse-trigonometric-functions",
       "Observe the two graphs, Graph 1 and Graph 2 given below "
       "and answer the questions that follow. (Both graphs are "
       "diagrams printed in the paper — increasing curves through "
       "the origin, drawn over different domains.) (i) Which one "
       "of the graphs represents y = sin⁻¹x? (ii) Write the domain "
       "and range of y = sin⁻¹x. (iii) Prove that sin⁻¹(1/√5) + "
       "sin⁻¹(2/√5) = π/2 (iv) Find the value of tan⁻¹[2 sin(2 "
       "cos⁻¹(√3/2))]"),
    _q(14, "A", 6, "probability",
       "An international conference takes place in a metropolitan "
       "city. International leaders, scientists and industrialists "
       "participate in it. The organisers of the conference "
       "appoint three agencies namely X, Y and Z for the security "
       "of the participants. The track record of the success of "
       "X, Y and Z in providing security services is 99%, 98.5% "
       "and 98% respectively. The organisers assign the "
       "responsibility of ensuring the security of 1000 people to "
       "agency X, 2000 people to agency Y and 3000 people to "
       "agency Z. At the end of the conference, one participant "
       "goes missing from the conference room. What is the "
       "probability that the missing participant was placed under "
       "the responsibility of the security agency X?"),
    _q(15, "B", 5, "vector-algebra",
       "In subparts (i) and (ii) choose the correct options and "
       "in subparts (iii) and (iv), answer the questions as "
       "instructed. (i) Assertion: (a⃗ + b⃗)² + (b⃗ − a⃗)² = "
       "2(a² + b²) Reason: Dot product of any two vectors is "
       "commutative. (a) Both Assertion and Reason are true and "
       "Reason is the correct explanation for Assertion. (b) Both "
       "Assertion and Reason are true but Reason is not the "
       "correct explanation for Assertion. (c) Assertion is true "
       "and Reason is false. (d) Assertion is false and Reason is "
       "true. (ii) The angle between the two planes x + y + 2z = 9 "
       "and 2x − y + z = 15 is: (a) π/2 (b) π/3 (c) π (d) 3π/4 "
       "(iii) Show that points P(−2, 3, 5), Q(1, 2, 3) and "
       "R(7, 0, −1) are collinear. (iv) Two honeybees are flying "
       "parallel to each other in the garden to collect the "
       "nectar. The path traced by the bees is given in the form "
       "of a straight line. The equation of the path traced by one "
       "honeybee is r⃗ = (î + 2ĵ + 3k̂) + λ(2î + 3ĵ + 4k̂). (a) "
       "Write the above-mentioned equation in cartesian form. (b) "
       "Find the equation of the path traced by the other honeybee "
       "passing through the point (2, 4, 5)."),
    _q(16, "B", 2, "three-dimensional-geometry",
       "(i) Find the equation of the plane passing through the "
       "points (2, 2, −1), (3, 4, 2) and (7, 0, 6). OR (ii) Find "
       "the equation of the plane passing through the points "
       "(2, 3, 1), (4, −5, 3) and parallel to x-axis."),
    _q(17, "B", 4, "vector-algebra",
       "Consider the position vectors of A, B and C as OA⃗ = "
       "2î − 2ĵ + k̂, OB⃗ = î + 2ĵ − 2k̂ and OC⃗ = 2î − ĵ + 4k̂. "
       "(i) Calculate AB⃗ and BC⃗. (ii) Find the projection of "
       "AB⃗ on BC⃗. (iii) Find the area of the triangle ABC whose "
       "sides are AB⃗ and BC⃗."),
    _q(18, "B", 4, "application-of-integrals",
       "(i) The equation y = 4 − x² represents a parabola. (a) "
       "Make a rough sketch of the graph of the given function. "
       "(b) Determine the area enclosed between the curve, the "
       "x-axis, the lines x = 0 and x = 2. (c) Hence, find the "
       "area bounded by the parabola and the x-axis. OR (ii) A "
       "farmer has a field bounded by three lines x + 2y = 2, "
       "y − x = 1, 2x + y = 7. Using integration, find the area of "
       "the region bounded by these lines."),
    _q(19, "C", 5, "statistics",
       "In subparts (i) and (ii) choose the correct options and "
       "in subpart (iii), answer the questions as instructed. (i) "
       "The total revenue received from the sale of 'x' units of a "
       "product is R(x) = 36x + 3x² + 5. Then, the actual revenue "
       "for selling the 10th item will be: (a) 27 (b) 90 (c) 93 "
       "(d) 33 (ii) Read the following statements and choose the "
       "correct option. (I) The correlation coefficient and the "
       "regression coefficients are of the same sign. (II) The "
       "correlation coefficient is the arithmetic mean between the "
       "regression coefficients. (III) The product of two "
       "regression coefficients is always equal to 1. (IV) Both "
       "the regression coefficients cannot be numerically greater "
       "than unity. (a) Only (IV) is correct. (b) Only (I) and "
       "(II) are correct. (c) Only (I) and (IV) are correct. (d) "
       "Only (III) and (IV) are correct. (iii) Consider the "
       "following data: x : 1, 2, 3, 6; y : 6, 5, 4, 1 (with rows "
       "for x − x̄ and y − ȳ to be completed). (a) Calculate x̄ and "
       "ȳ (b) Complete the table. (c) Calculate b_xy"),
    _q(20, "C", 2, "statistics",
       "(i) Find the regression line of best fit from the "
       "following data. Σx = 24, Σy = 44, Σxy = 306, Σx² = 164, "
       "Σy² = 576, n = 4 OR (ii) Two lines of regression are given "
       "as 4x + 3y + 7 = 0 and 3x + 4y + 8 = 0. Identify the line "
       "of regression of x on y."),
    _q(21, "C", 4, "application-of-derivatives",
       "(i) A utensil manufacturer produces 'x' dinner sets per "
       "week and sells each set at ₹ p, where x = (600 − p)/8. The "
       "cost of production of 'x' sets is ₹ x² + 78x + 2000. (a) "
       "Write the revenue function. (b) Write the profit function. "
       "(c) Calculate the number of dinner sets to be produced and "
       "sold per week to ensure maximum profit. OR (ii) The "
       "Average Cost of producing 'x' units of commodity is given "
       "by: AC = x²/200 − x/50 − 30 + 5000/x. (a) Find the Cost "
       "function. (b) Find the Marginal Cost function. (c) Find "
       "the Marginal Average Cost function. (d) Verify that "
       "d/dx(AC) = (MC − AC)/x."),
    _q(22, "C", 4, "linear-programming",
       "Two different types of books have to be stacked in the "
       "shelf of a library. The first type of book weighs 1 kg and "
       "has a thickness of 6 cm. The second type of book weighs "
       "1.5 kg and has a thickness of 4 cm. The shelf is 96 cm "
       "long and can support a maximum weight of 21 kg. How should "
       "both the types of books be placed in the shelf to include "
       "the maximum number of books? Formulate a Linear "
       "Programming Problem and solve it graphically."),
]

# Wave 66: ICSE (CISCE) Class 10 Mathematics 2025 — English only
# (CISCE publishes ICSE papers in English only). Transcribed from
# the source PDF; its text layer doubles bold characters, and the
# figure questions (Q1(vi), Q1(xi)) and Q4 were verified against
# the page images. Section A is compulsory; Section B: attempt
# any four of seven questions.
_ICSE10_2025 = [
    _q(1, "A", 15, "quadratic-equations",
       "Choose the correct answers to the questions from the given "
       "options. (Do not copy the questions, write the correct "
       "answers only.) (i) The given quadratic equation 3x² + √7x "
       "+ 2 = 0 has: (a) two equal real roots. (b) two distinct "
       "real roots. (c) more than two real roots. (d) no real "
       "roots. (ii) Mr. Anuj deposits ₹500 per month for 18 months "
       "in a recurring deposit account at a certain rate. If he "
       "earns ₹570 as interest at the time of maturity, then his "
       "matured amount is: (a) ₹(500 × 18 + 570) (b) ₹(500 × 19 + "
       "570) (c) ₹(500 × 18 × 19 + 570) (d) ₹(500 × 9 × 19 + 570) "
       "(iii) Which of the following cannot be the probability of "
       "any event? (a) 5/4 (b) 0.25 (c) 1/33 (d) 67% (iv) The "
       "equation of the line passing through origin and parallel "
       "to the line 3x + 4y + 7 = 0 is: (a) 3x + 4y + 5 = 0 (b) "
       "4x − 3y − 5 = 0 (c) 4x − 3y = 0 (d) 3x + 4y = 0 (v) If "
       "A = [[0, 1], [1, 0]], then A² is equal to: (a) [[1, 1], "
       "[0, 0]] (b) [[0, 0], [1, 1]] (c) [[1, 0], [0, 1]] (d) "
       "[[0, 1], [1, 0]] (vi) In the given diagram, chords AC and "
       "BC are equal. If ∠ACD = 120°, then ∠AEC is: (a) 30° (b) "
       "60° (c) 90° (d) 120° (vii) The factor common to the two "
       "polynomials x² − 4 and x³ − x² − 4x + 4 is: (a) (x + 1) "
       "(b) (x − 1) (c) (x − 2) (d) (x − 4) (viii) A man invested "
       "in a company paying 12% dividend on its share. If the "
       "percentage return on his investment is 10%, then the "
       "shares are: (a) at par (b) below par (c) above par (d) "
       "cannot be determined (ix) Statement 1: The point which is "
       "equidistant from three non-collinear points D, E and F is "
       "the circumcentre of the ΔDEF. Statement 2: The incentre "
       "of a triangle is the point where the bisector of the "
       "angles intersects. (a) Both the statements are true. (b) "
       "Both the statements are false. (c) Statement 1 is true, "
       "and Statement 2 is false. (d) Statement 1 is false, and "
       "Statement 2 is true. (x) Assertion (A): If sin²A + sinA = "
       "1 then cos⁴A + cos²A = 1 Reason (R): 1 − sin²A = cos²A "
       "(a) (A) is true, (R) is false. (b) (A) is false, (R) is "
       "true. (c) Both (A) and (R) are true, and (R) is the "
       "correct reason for (A). (d) Both (A) and (R) are true, "
       "and (R) is the incorrect reason for (A). (xi) In the "
       "given diagram ΔABC ~ ΔEFG. If ∠ABC = ∠EFG = 60°, then the "
       "length of the side FG is: (In the diagram, AB = 15 cm, "
       "BC = 3 cm and FE = 75 cm.) (a) 15 cm (b) 20 cm (c) 25 cm "
       "(d) 30 cm (xii) If the volume of two spheres is in the "
       "ratio 27 : 64, then the ratio of their radii is: (a) 3 : 4 "
       "(b) 4 : 3 (c) 9 : 16 (d) 16 : 9 (xiii) The marked price "
       "of an article is ₹1375. If the CGST is charged at a rate "
       "of 4%, then the price of the article including GST is: "
       "(a) ₹55 (b) ₹110 (c) ₹1430 (d) ₹1485 (xiv) The solution "
       "set for 0 < −x/3 < 2, x ∈ Z is: (a) {−5, −4, −3, −2, −1} "
       "(b) {−6, −5, −4, −3, −2, −1} (c) {−5, −4, −3, −2, −1, 0} "
       "(d) {−6, −5, −4, −3, −2, −1, 0} (xv) Assertion (A): The "
       "mean of first 9 natural numbers is 4.5. Reason (R): Mean "
       "= (Sum of all the observations)/(Total number of "
       "observations) (a) (A) is true, (R) is false. (b) (A) is "
       "false, (R) is true. (c) Both (A) and (R) are true, and "
       "(R) is the correct reason for (A). (d) Both (A) and (R) "
       "are true, and (R) is the incorrect reason for (A)."),
    _q(2, "A", 12, "quadratic-equations",
       "(i) Solve the following quadratic equation 2x² − 5x − 4 = "
       "0. Give your answer correct to three significant figures. "
       "(Use mathematical tables for this question) (ii) Mrs. Rao "
       "deposited ₹250 per month in a recurring deposit account "
       "for a period of 3 years. She received ₹10,110 at the time "
       "of maturity. Find: (a) the rate of interest. (b) how much "
       "more interest Mrs. Rao will receive if she had deposited "
       "₹50 more per month at the same rate of interest and for "
       "the same time. (iii) In ΔABC, ∠ABC = 90°, AB = 20 cm, "
       "AC = 25 cm, DE is perpendicular to AC such that ∠DEA = "
       "90° and DE = 3 cm as shown in the given figure. (a) Prove "
       "that ΔABC ~ ΔAED. (b) Find the lengths of BC, AD and AE. "
       "(c) If BCED represents a plot of land on a map whose "
       "actual area on ground is 576 m², then find the scale "
       "factor of the map."),
    _q(3, "A", 13, "circles",
       "(i) Use ruler and compass for the following construction. "
       "Construct a ΔABC, where AB = 6 cm, AC = 4.5 cm and "
       "∠BAC = 120°. Construct a circle circumscribing the ΔABC. "
       "Measure and write down the length of the radius of the "
       "circle. (ii) If A = [[1, 2], [3, 4]], B = [[2, 1], [4, "
       "2]] and C = [[−5, 1], [7, −4]] Find: (a) A + C (b) B(A + "
       "C) (c) 5B (d) B(A + C) – 5B (iii) In the given graph ABCD "
       "is a parallelogram. Scale: x-axis, 2 cm = 1 unit; y-axis, "
       "2 cm = 1 unit. Using the graph, answer the following: (a) "
       "write down the coordinates of A, B, C and D. (b) calculate "
       "the coordinates of 'P', the point of intersection of the "
       "diagonals AC and BD. (c) find the slope of sides CB and DA "
       "and verify that they represent parallel lines. (d) find "
       "the equation of the diagonal AC."),
    _q(4, "B", 10, "introduction-to-trigonometry",
       "(i) Solve the following inequation, write the solution "
       "set and represent it on the real number line. 2x − 5/3 < "
       "3x/5 + 10 ≤ 4x/5 + 11; x ∈ R (ii) The first term of an "
       "Arithmetic Progression (A.P.) is 5, the last term is 50 "
       "and their sum is 440. Find: (a) the number of terms (b) "
       "common difference (iii) Prove that: ((cotA + tanA − "
       "1)(sinA + cosA))/(sin³A + cos³A) = secA · cosecA"),
    _q(5, "B", 10, "surface-areas-and-volumes",
       "(i) Using properties of proportion, find the value of "
       "'x': (6x² + 3x − 5)/(3x − 5) = (9x² + 2x + 5)/(2x + 5); "
       "x ≠ 0 (ii) It is given that (x − 2) is a factor of "
       "polynomial 2x³ − 7x² + kx − 2. Find: (a) the value of 'k'. "
       "(b) hence, factorise the resulting polynomial completely. "
       "(iii) A solid wooden capsule is shown in Figure 1. The "
       "capsule is formed of a cylindrical block and two "
       "hemispheres. Find the sum of total surface area of the "
       "three parts as shown in Figure 2. Given, the radius of "
       "the capsule is 3.5 cm and the length of the cylindrical "
       "block is 14 cm. (Use π = 22/7)"),
    _q(6, "B", 10, "coordinate-geometry",
       "(i) Use a graph paper for this question taking 2 cm = 1 "
       "unit along both axes. (a) Plot A(1, 3), B(1, 2) and C(3, "
       "0). (b) Reflect A and B on the x-axis and name their "
       "images as E and D respectively. Write down their "
       "coordinates. (c) Reflect A and B through the origin and "
       "name their images as F and G respectively. (d) Reflect A, "
       "B and C on the y-axis and name their images as J, I and H "
       "respectively. (e) Join all the points A, B, C, D, E, F, G, "
       "H, I and J in order and name the closed figure so formed. "
       "(ii) In the given diagram, AB is a vertical tower 100 m "
       "away from the foot of a 30 storied building CD. The angles "
       "of depression from the point C and E, (E being the "
       "mid-point of CD), are 35° and 14° respectively. (Use "
       "mathematical table for the required values rounded off "
       "correct to two places of decimals only) Find the height "
       "of the: (a) tower AB (b) building CD"),
    _q(7, "B", 10, "statistics",
       "(i) Use a graph paper for this question. (Take 2 cm = 10 "
       "Marks along one axis and 2 cm = 10 students along another "
       "axis). Draw a Histogram for the following distribution "
       "which gives the marks obtained by 164 students in a "
       "particular class and hence find the Mode. Marks : 30 – 40, "
       "40 – 50, 50 – 60, 60 – 70, 70 – 80; Number of Students : "
       "10, 26, 40, 54, 34 (ii) In the given graph, P and Q are "
       "points such that PQ cuts off intercepts of 5 units and 3 "
       "units along the x-axis and y-axis respectively. Line RS "
       "is perpendicular to PQ and passes through the origin. Find "
       "the: (a) coordinates of P and Q (b) equation of line RS "
       "(iii) Refer to the given bill. A customer paid ₹2000 "
       "(rounded off to the nearest ₹10) to clear the bill. Note: "
       "5% discount is applicable on an article if 10 or more such "
       "articles are purchased. BILL — Article A: M.P. ₹190, "
       "Quantity 06, G.S.T. 12%; Article B: M.P. ₹50, Quantity 12, "
       "G.S.T. 18%. Check whether the total amount paid by the "
       "customer is correct or not. Justify your answer with "
       "necessary working."),
    _q(8, "B", 10, "quadratic-equations",
       "(i) A man bought ₹200 shares of a company at 25% premium. "
       "If he received a return of 5% on his investment. Find "
       "the: (a) market value (b) dividend percent declared (c) "
       "number of shares purchased, if annual dividend is ₹1000. "
       "(ii) For the given frequency distribution, find the: (a) "
       "mean, to the nearest whole number (b) median. x : 10, 11, "
       "12, 13, 14, 15, 16; f : 3, 2, 2, 6, 3, 5, 3 (iii) Mr. and "
       "Mrs. Das were travelling by car from Delhi to Kasauli for "
       "a holiday. Distance between Delhi and Kasauli is "
       "approximately 350 km (via NH 152D). Due to heavy rain they "
       "had to slow down. The average speed of the car was reduced "
       "by 20 km/hr and time of the journey increased by 2 hours. "
       "Find: (a) the original speed of the car. (b) with the "
       "reduced speed, the number of hours they took to reach "
       "their destination."),
    _q(9, "B", 10, "circles",
       "(i) A hollow sphere of external diameter 10 cm and "
       "internal diameter 6 cm is melted and made into a solid "
       "right circular cone of height 8 cm. Find the radius of the "
       "cone so formed. [Use π = 22/7] (ii) Ms. Sushmita went to "
       "a fair and participated in a game. The game consisted of "
       "a box having number cards with numbers from 01 to 30. The "
       "three prizes were as per the given table: Wall Clock — "
       "Number on the card drawn at random is a perfect square; "
       "Water Bottle — even number which is also a multiple of 3; "
       "Purse — prime number. Find the probability of winning a: "
       "(a) Wall Clock (b) Water Bottle (c) Purse (iii) X, Y, Z "
       "and C are the points on the circumference of a circle with "
       "centre 'O'. AB is a tangent to the circle at 'X' and "
       "ZY = XY. Given ∠OBX = 32° and ∠AXZ = 66°. Find: (a) ∠BOX "
       "(b) ∠CYX (c) ∠ZYX (d) ∠OXY"),
    _q(10, "B", 10, "statistics",
       "(i) If 1701 is the nth term of the Geometric Progression "
       "(G.P.) 7, 21, 63 ……., find: (a) the value of 'n' (b) hence "
       "find the sum of the 'n' terms of the G.P. (ii) In the "
       "given diagram 'O' is the centre of the circle. Chord SR "
       "produced meets the tangent XTP at P. (a) Prove that ΔPTR "
       "~ ΔPST (b) Prove that PT² = PR × PS (c) If PR = 4 cm and "
       "PS = 16 cm, find the length of the tangent PT. (iii) The "
       "given graph represents the monthly salaries (in ₹) of "
       "workers of a factory. Scale: along x-axis, 2 cm = ₹2000; "
       "along y-axis, 2 cm = 10 workers; Monthly salary (in ₹) "
       "(× 10³). Using graph answer the following: (a) the total "
       "number of workers. (b) the median class. (c) the "
       "lower-quartile class. (d) number of workers having monthly "
       "salary more than or equal to ₹6,000 but less than "
       "₹10,000."),
]

# Wave 66: UP Board (UPMSP) Class 10 Mathematics 2025, set
# 822 (CA) — English and Hindi prints. The Hindi print was read
# question-by-question from the AglaSem scan of the real booklet
# (image-only PDF); the English print from the Collegedunia
# solved-paper PDF, cross-checked on Zollege. The two mediums'
# booklets genuinely differ in four places (Section A Q7 option
# D, Q11 option D, Q15 option B, and the sign of a point in
# Section B Q1(e)) — each list below follows its own medium's
# print, verified on high-resolution crops of the Hindi scan.
# Section A: 20 MCQs x 1 (OMR). Section B (50 marks): Q1 all six
# parts x 2 = 12, Q2 any five of six parts x 4 = 20, Q3-Q5 x 6
# with internal choice. Section B numbering restarts at 1, as
# printed.
_UP10_2025_EN_A = [
    _q(1, "A", 1, "real-numbers",
       "Given the HCF (99, 153) = 9, then LCM (99, 153) will be: "
       "(A) 1683 (B) 99 (C) 153 (D) 99 × 153"),
    _q(2, "A", 1, "probability",
       "A bag contains 3 red and 2 blue balls. If a ball is drawn "
       "randomly from the bag, then the probability of it being "
       "blue will be: (A) 1/3 (B) 2/5 (C) 1/2 (D) 3/5"),
    _q(3, "A", 1, "statistics",
       "The median class of the following table will be: Class "
       "interval : 0-4, 4-8, 8-12, 12-16, 16-20; Frequency : 1, "
       "5, 8, 6, 3 (A) 0-4 (B) 4-8 (C) 8-12 (D) 16-20"),
    _q(4, "A", 1, "statistics",
       "The modal class of the following frequency distribution "
       "will be: Class interval : 0-10, 10-20, 20-30, 30-40, "
       "40-50; Frequency : 11, 21, 23, 5, 14 (A) 40-50 (B) 10-20 "
       "(C) 20-30 (D) 30-40"),
    _q(5, "A", 1, "probability",
       "The probability of getting a head when a coin is tossed "
       "once, will be: (A) 1 (B) -1 (C) 1/3 (D) 1/2"),
    _q(6, "A", 1, "real-numbers",
       "The prime factorization of the number 144 will be: (A) "
       "2⁴ × 3² (B) 4² × 3² (C) 2⁴ × 3³ (D) 2³ × 3²"),
    _q(7, "A", 1, "real-numbers",
       "The HCF of the numbers 54 and 336 will be: (A) 9 (B) 6 "
       "(C) 3 (D) 18"),
    _q(8, "A", 1, "coordinate-geometry",
       "Distance of the point (3, 4) from x-axis will be: (A) 1 "
       "unit (B) 2 units (C) 3 units (D) 4 units"),
    _q(9, "A", 1, "quadratic-equations",
       "Roots of the quadratic equation 3x² + 5x + 3 = 0 is: (A) "
       "Real (B) Real and equal (C) Not real (D) Real and "
       "different"),
    _q(10, "A", 1, "pair-of-linear-equations",
       "The solution of the equations x − y = 2 and x + y = 2 "
       "will be: (A) x = 0, y = 2 (B) x = 4, y = 2 (C) x = −2, "
       "y = 0 (D) x = 2, y = 0"),
    _q(11, "A", 1, "pair-of-linear-equations",
       "The sum and difference of two numbers are 8 and 2 "
       "respectively. The numbers will be: (A) 6, 2 (B) 5, 3 (C) "
       "7, 1 (D) 12, -2"),
    _q(12, "A", 1, "arithmetic-progressions",
       "20th term of the A.P. 10, 7, 4, . . . will be: (A) -57 "
       "(B) 57 (C) -47 (D) 47"),
    _q(13, "A", 1, "circles",
       "Length of a tangent drawn on a circle of radius 5 cm "
       "from a point 13 cm distant from its centre will be: (A) "
       "5 cm (B) 8 cm (C) 16 cm (D) 12 cm"),
    _q(14, "A", 1, "surface-areas-and-volumes",
       "Two cubes each of side 7 cm are joined end to end. The "
       "total surface area of the resulting solid will be: (A) "
       "490 cm² (B) 539 cm² (C) 588 cm² (D) 590 cm²"),
    _q(15, "A", 1, "areas-related-to-circles",
       "In a circle of radius 21 cm, an arc subtends an angle of "
       "30° at the centre. The length of the arc will be: (A) 22 "
       "cm (B) 16.5 cm (C) 11 cm (D) 5.5 cm"),
    _q(16, "A", 1, "introduction-to-trigonometry",
       "If tan θ = a/b, then the value of (b sin θ − a cos θ)/"
       "(b sin θ + a cos θ) will be: (A) 1 (B) 0 (C) (a² − b²)/"
       "(a² + b²) (D) (b² − a²)/(b² + a²)"),
    _q(17, "A", 1, "introduction-to-trigonometry",
       "If 3 cot A = 4, then the value of sec A will be: (A) 3/2 "
       "(B) 2/3 (C) 3/4 (D) 5/4"),
    _q(18, "A", 1, "introduction-to-trigonometry",
       "If sin 2A = √3/2, then the value of A will be: (A) 60° "
       "(B) 45° (C) 30° (D) 0°"),
    _q(19, "A", 1, "introduction-to-trigonometry",
       "If 2 cos 3θ = 1, then the value of θ will be: (A) 25° "
       "(B) 20° (C) 15° (D) 10°"),
    _q(20, "A", 1, "triangles",
       "In the given figure, line segment PQ is drawn parallel "
       "to the base BC of △ABC. If PQ : BC = 1 : 3, then the "
       "ratio of AP and BP will be: (A) 1:2 (B) 2:3 (C) 1:4 (D) "
       "1:3"),
]
_UP10_2025_EN_B = [
    _q(1, "B", 12, "real-numbers",
       "Do all the parts: (a) Prove that (4 + √2) is an "
       "irrational number. (b) If cosec θ = 13/5, find cot θ. "
       "(c) Find the area of the sector of a circle of radius 14 "
       "cm, whose angle is 30°. (d) Find the median from the "
       "following table: Class Interval : 0-10, 10-20, 20-30, "
       "30-40, 40-50, 50-60; Frequency : 5, 8, 20, 15, 7, 5 (e) "
       "Find the distance between the points (-5, 7) and (-1, 3). "
       "(f) The distance between the points (2, y) and (10, 3) is "
       "10 units. Find y."),
    _q(2, "B", 20, "polynomials",
       "Do any five parts: (a) If a zero of the quadratic "
       "polynomial (p - 1)x² + px + 1 is -3, then find the value "
       "of p. (b) For which values of p, following pair of "
       "equations have unique solution? 4x + py + 8 = 0, 2x + 2y "
       "+ 2 = 0 (c) Prove that a line segment joining an external "
       "point of a circle to its centre makes equal angle with "
       "the two tangents drawn from that point. (d) Prove that "
       "the line passing through the mid-point of one side of a "
       "triangle and parallel to the second side bisects the "
       "third side. (e) Find the mean from the following table: "
       "Class Interval : 120-130, 130-140, 140-150, 150-160, "
       "160-170; Frequency : 2, 8, 12, 20, 8 (f) A bag contains 3 "
       "red and 5 black balls. One ball is drawn at random. Find "
       "probability that ball will be (i) Red (ii) Black."),
    _q(3, "B", 6, "arithmetic-progressions",
       "First term of an A.P. is 5, last term is 64 and sum of "
       "all terms is 400. Find the number of terms and common "
       "difference. OR Solve the following equations: (a) x + y = "
       "5 and 2x - 3y = 4 (b) 3x + 4y = 10 and 2x - 2y = 2"),
    _q(4, "B", 6, "surface-areas-and-volumes",
       "A solid is of conical shape which is surmounted on a "
       "hemisphere having radius r and equal base. If the curved "
       "surface of the hemisphere and the curved surface of the "
       "cone are equal, then find the ratio of the radius and "
       "height of the cone. OR From a solid cylinder whose height "
       "is 2.4 cm and diameter is 1.4 cm, a conical cavity of the "
       "same height and same diameter is hollowed out. Find the "
       "total surface area of the remaining solid to the nearest "
       "square cm."),
    _q(5, "B", 6, "some-applications-of-trigonometry",
       "The angle of elevation of the top Q of a vertical tower "
       "PQ from a point X on the ground is 60°. The angle of "
       "elevation of Q from a point Y situated 40 m above the "
       "point X is 45°. Find the height of the tower PQ and the "
       "distance PX. OR From the top of a lighthouse above sea "
       "level, the angles of depression of two ships are 30° and "
       "45°. If one ship is exactly 50 m behind the other on the "
       "same side of the lighthouse, find the height of the "
       "lighthouse."),
]
_UP10_2025_HI_A = [
    _q(1, "A", 1, "real-numbers",
       "दिया है HCF (99, 153) = 9, तो LCM (99, 153) होगा (a) "
       "1683 (b) 99 (c) 153 (d) 99 × 153"),
    _q(2, "A", 1, "probability",
       "एक थैले में 3 लाल और 2 नीली गेंदें हैं। थैले से यादृच्छया "
       "एक गेंद निकाली गयी। उस गेंद के नीली होने की प्रायिकता "
       "होगी (a) 1/3 (b) 2/5 (c) 1/2 (d) 3/5"),
    _q(3, "A", 1, "statistics",
       "निम्नलिखित सारणी का माध्यक वर्ग होगा वर्ग अंतराल : 0-4, "
       "4-8, 8-12, 12-16, 16-20; बारंबारता : 1, 5, 8, 6, 3 (a) "
       "0-4 (b) 4-8 (c) 8-12 (d) 16-20"),
    _q(4, "A", 1, "statistics",
       "निम्नांकित बारम्बारता बंटन से बहुलक वर्ग होगा वर्ग "
       "अंतराल : 0-10, 10-20, 20-30, 30-40, 40-50; बारम्बारता : "
       "11, 21, 23, 5, 14 (a) 40-50 (b) 10-20 (c) 20-30 (d) 30-40"),
    _q(5, "A", 1, "probability",
       "किसी सिक्के को एक बार उछालने पर शीर्ष (हेड) आने की "
       "प्रायिकता होगी (a) 1 (b) -1 (c) 1/3 (d) 1/2"),
    _q(6, "A", 1, "real-numbers",
       "संख्या 144 के अभाज्य गुणनखण्डन होंगे (a) 2⁴ × 3² (b) 4² "
       "× 3² (c) 2⁴ × 3³ (d) 2³ × 3²"),
    _q(7, "A", 1, "real-numbers",
       "संख्याओं 54 और 336 का HCF होगा (a) 9 (b) 6 (c) 3 (d) 8"),
    _q(8, "A", 1, "coordinate-geometry",
       "बिन्दु (3, 4) की X-अक्ष से दूरी होगी (a) 1 इकाई (b) 2 "
       "इकाई (c) 3 इकाई (d) 4 इकाई"),
    _q(9, "A", 1, "quadratic-equations",
       "द्विघात समीकरण 3x² + 5x + 3 = 0 के मूल हैं (a) वास्तविक "
       "(b) वास्तविक तथा बराबर (c) वास्तविक नहीं (d) वास्तविक "
       "तथा भिन्न"),
    _q(10, "A", 1, "pair-of-linear-equations",
       "समीकरणों x - y = 2 एवं x + y = 2 का हल होगा (a) x = 0, "
       "y = 2 (b) x = 4, y = 2 (c) x = -2, y = 0 (d) x = 2, y = 0"),
    _q(11, "A", 1, "pair-of-linear-equations",
       "दो संख्याओं का योगफल तथा अन्तर क्रमशः 8 और 2 हैं, तो "
       "संख्याएँ होंगी (a) 6, 2 (b) 5, 3 (c) 7, 1 (d) 1, 2"),
    _q(12, "A", 1, "arithmetic-progressions",
       "समान्तर श्रेढ़ी 10, 7, 4, ....... का 20 वाँ पद होगा (a) "
       "-57 (b) 57 (c) -47 (d) 47"),
    _q(13, "A", 1, "circles",
       "5 सेमी त्रिज्या के वृत्त पर उसके केन्द्र से 13 सेमी दूर "
       "स्थित एक बिन्दु से खींची गयी स्पर्श रेखा की लम्बाई होगी "
       "(a) 5 सेमी (b) 8 सेमी (c) 16 सेमी (d) 12 सेमी"),
    _q(14, "A", 1, "surface-areas-and-volumes",
       "7 सेमी भुजा वाले दो घनों के सिरों को मिलाकर रखा गया है। "
       "प्राप्त ठोस का सम्पूर्ण पृष्ठीय क्षेत्रफल होगा (a) 490 "
       "सेमी² (b) 539 सेमी² (c) 588 सेमी² (d) 590 सेमी²"),
    _q(15, "A", 1, "areas-related-to-circles",
       "त्रिज्या 21 सेमी वाले वृत्त का एक चाप केन्द्र पर 30° का "
       "कोण अन्तरित करता है। चाप की लम्बाई होगी (a) 22 सेमी (b) "
       "6.5 सेमी (c) 11 सेमी (d) 5.5 सेमी"),
    _q(16, "A", 1, "introduction-to-trigonometry",
       "यदि tanθ = a/b है, तो (b sinθ − a cosθ)/(b sinθ + a cosθ) "
       "का मान होगा (a) 1 (b) 0 (c) (a² − b²)/(a² + b²) (d) (b² "
       "− a²)/(b² + a²)"),
    _q(17, "A", 1, "introduction-to-trigonometry",
       "यदि 3cot A = 4 है तो sec A का मान होगा (a) 3/2 (b) 2/3 "
       "(c) 3/4 (d) 5/4"),
    _q(18, "A", 1, "introduction-to-trigonometry",
       "यदि sin2A = √3/2 है तो A का मान होगा (a) 60° (b) 45° (c) "
       "30° (d) 0°"),
    _q(19, "A", 1, "introduction-to-trigonometry",
       "यदि 2cos3θ = 1 है तो θ का मान होगा (a) 25° (b) 20° (c) "
       "15° (d) 10°"),
    _q(20, "A", 1, "triangles",
       "दिये गये चित्र में, ΔABC के आधार BC के समान्तर रेखाखण्ड "
       "PQ खींचा गया है। यदि PQ : BC = 1 : 3 हो, तो AP और BP का "
       "अनुपात होगा (a) 1:2 (b) 2:3 (c) 1:4 (d) 1:3"),
]
_UP10_2025_HI_B = [
    _q(1, "B", 12, "real-numbers",
       "सभी खण्ड कीजिए: (a) सिद्ध कीजिए कि (4 + √2) अपरिमेय "
       "संख्या है। (b) यदि cosec θ = 13/5, तो cot θ का मान ज्ञात "
       "कीजिए। (c) 14 सेमी त्रिज्या वाले एक वृत्त के त्रिज्यखण्ड "
       "का क्षेत्रफल ज्ञात कीजिए जिसका कोण 30° है। (d) "
       "निम्नलिखित सारणी की माध्यिका ज्ञात कीजिए: वर्ग अंतराल : "
       "0-10, 10-20, 20-30, 30-40, 40-50, 50-60; बारंबारता : 5, "
       "8, 20, 15, 7, 5 (e) बिन्दुओं (5, 7) और (-1, 3) के मध्य "
       "की दूरी ज्ञात कीजिए। (f) बिन्दुओं (2, y) और (10, 3) के "
       "बीच की दूरी 10 मात्रक है। y का मान ज्ञात कीजिए।"),
    _q(2, "B", 20, "polynomials",
       "किन्हीं पाँच खण्डों को हल कीजिए: (a) यदि द्विघात बहुपद "
       "(P - 1)x² + Px + 1 का एक शून्यक -3 है तो P का मान ज्ञात "
       "कीजिए। (b) p के किन मानों के लिए, निम्न समीकरण युग्म का "
       "एक अद्वितीय हल है? 4x + py + 8 = 0, 2x + 2y + 2 = 0 (c) "
       "सिद्ध कीजिए कि किसी वृत्त के बाह्य बिन्दु को वृत्त के "
       "केन्द्र पर मिलाने वाला रेखाखण्ड, उसी बाह्य बिन्दु से "
       "खींची गयी वृत्त की दो स्पर्श रेखाओं के साथ बराबर कोण "
       "बनाती है। (d) सिद्ध कीजिए कि एक त्रिभुज की एक भुजा के "
       "मध्य बिन्दु से होकर दूसरी भुजा के समान्तर खींची गयी "
       "रेखा, तीसरी भुजा को समद्विभाजित करती है। (e) निम्नलिखित "
       "सारणी से माध्य ज्ञात कीजिए: वर्ग अंतराल : 120-130, "
       "130-140, 140-150, 150-160, 160-170; बारंबारता : 2, 8, "
       "12, 20, 8 (f) एक थैले में 3 लाल और 5 काली गेंदें हैं। "
       "इस थैले में से एक गेंद यादृच्छया निकाली जाती है। इसकी "
       "क्या प्रायिकता होगी कि वह गेंद (i) लाल हो (ii) काली हो?"),
    _q(3, "B", 6, "arithmetic-progressions",
       "किसी समान्तर श्रेणी का प्रथम पद 5, अन्तिम पद 64 और सभी "
       "पदों का योगफल 400 है। पदों की संख्या एवं सार्व अंतर "
       "ज्ञात कीजिए। अथवा निम्नलिखित समीकरणों को हल कीजिए: (a) "
       "x + y = 5 और 2x - 3y = 4 (b) 3x + 4y = 10 और 2x - 2y = 2"),
    _q(4, "B", 6, "surface-areas-and-volumes",
       "एक ठोस शंकु के आकार का है जो एक समान आधार वाली त्रिज्या "
       "के अर्द्धगोले पर अध्यारोपित है। यदि अर्द्धगोले का "
       "वक्रपृष्ठ तथा शंकु का वक्रपृष्ठ समान हों तो शंकु की "
       "त्रिज्या और ऊँचाई का अनुपात ज्ञात कीजिए। अथवा 2.4 सेमी "
       "ऊँचाई और 1.4 सेमी व्यास वाले एक ठोस बेलन से इसी ऊँचाई "
       "और इसी व्यास वाला एक शंक्वाकार खोल काट लिया जाता है। "
       "शेष बचे ठोस का निकटतम वर्ग सेमी तक कुल पृष्ठीय "
       "क्षेत्रफल ज्ञात कीजिए।"),
    _q(5, "B", 6, "some-applications-of-trigonometry",
       "भूमि पर स्थित बिन्दु X से उर्ध्वाधर टावर PQ के शीर्ष Q "
       "का उन्नयन कोण 60° है। बिन्दु X से 40 मीटर ऊँचाई पर "
       "स्थित बिन्दु Y से Q का उन्नयन कोण 45° है। टावर PQ की "
       "ऊँचाई तथा दूरी PX ज्ञात कीजिए। अथवा एक प्रकाश स्तम्भ के "
       "शिखर से देखने पर समुद्र तल में दो जहाजों के अवनमन कोण "
       "क्रमशः 30° और 45° हैं। यदि प्रकाश स्तम्भ के एक ही ओर एक "
       "जहाज दूसरे जहाज के ठीक पीछे 50 मीटर की दूरी पर है, तो "
       "समुद्र तल से प्रकाश स्तम्भ की ऊँचाई ज्ञात कीजिए।"),
]

# Wave 66: UP Board (UPMSP) Class 12 Mathematics 2025, set
# 324 (IX) — English and Hindi prints. Maximum Marks 100, nine
# questions, no sections in the real paper (stored under one
# section heading). Marks per the board's pattern, as printed
# against the questions: Q1 five MCQ parts x 1 = 5, Q2 five
# parts x 1 = 5, Q3-Q4 four parts x 2 = 8 each, Q5-Q6 five
# parts x 5 = 25 each, Q7-Q9 do-any-one-of-two = 8 each. The
# Hindi print was read from the AglaSem scan of the booklet
# (image-only); the English print from the Collegedunia
# solved-paper PDF of the same set, cross-checked question by
# question against the Hindi. Q1(d)'s exponent is 1/3, verified
# on a high-resolution crop of the printed page (the
# solved-paper sites' worked answer does not match the print).
_UP12_2025_EN = [
    _q(1, "A", 5, "relations-and-functions",
       "Do all parts. Select the correct option of each part and "
       "write it on your answer-book. (a) The modulus function "
       "f: R → R+ given by f(x) = |x| is (A) one-one and onto (B) "
       "many-one and onto (C) one-one but not onto (D) neither "
       "one-one nor onto (b) A relation R = {(a, b) : a = b - 1, "
       "b ≥ 3} is defined on set N, then (A) (2, 4) ∈ R (B) (4, "
       "5) ∈ R (C) (4, 6) ∈ R (D) (1, 3) ∈ R (c) The value of "
       "∫(0 to π/2) dx/(1 + √tanx) is: (A) 0 (B) π/2 (C) π/4 (D) "
       "π/8 (d) The degree of differential equation 9(d²y/dx²) = "
       "{1 + (dy/dx)²}^(1/3) is: (A) 1 (B) 6 (C) 3 (D) 2 (e) The "
       "value of expression î·î − ĵ·ĵ + k̂ × k̂ is (A) 0 (B) 1 (C) "
       "2 (D) 3"),
    _q(2, "A", 5, "inverse-trigonometric-functions",
       "Do all parts. (a) Write cot⁻¹{1/√(x² − 1)}; x > 1 in the "
       "simplest form. (b) Prove that the function f(x) = |x| is "
       "continuous at x = 0. (c) Find the degree of the "
       "differential equation xy(d²y/dx²) + x(dy/dx)² − y(dy/dx) "
       "= 2. (d) If P(A) = 0.12, P(B) = 0.15 and P(B/A) = 0.18, "
       "then find the value of P(A ∩ B). (e) Find the angle "
       "between the vectors −2î + ĵ + 3k̂ and 3î − 2ĵ + k̂."),
    _q(3, "A", 8, "relations-and-functions",
       "Do all parts. (a) If f: R → R and g: R → R be functions "
       "defined by f(x) = cos x and g(x) = 3x² respectively, then "
       "prove that gof ≠ fog. (b) Find the general solution of "
       "the differential equation y dx + (x − y²) dy = 0. (c) "
       "Prove that (4, 4, 2), (3, 5, 2) and (-1, -1, 2) are "
       "vertices of a right angle triangle. (d) If [[x + y, 2], "
       "[5 + z, xy]] = [[6, 2], [5, 8]], then find the values of "
       "x, y, z."),
    _q(4, "A", 8, "application-of-derivatives",
       "Do all parts. (a) Show that the function f(x) = 7x² − 3 "
       "is an increasing function when x > 0. (b) Find a unit "
       "vector perpendicular to each of the vectors (a⃗ + b⃗) and "
       "(a⃗ − b⃗), where a⃗ = î + ĵ + k̂, b⃗ = î + 2ĵ + 3k̂. (c) If "
       "the Cartesian equation of a line is (x − 5)/3 = (y + 4)/7 "
       "= (z − 6)/2, then find its equation in vector form. (d) A "
       "bag contains 4 white and 2 black balls and another bag "
       "contains 3 white and 5 black balls. If one ball is drawn "
       "from each bag, then find the probability that both balls "
       "are black."),
    _q(5, "A", 25, "relations-and-functions",
       "Do all parts. (a) If R₁ and R₂ be two equivalence "
       "relations on a set A, then prove that R₁ ∩ R₂ is also an "
       "equivalence relation. (b) If A = [[0, −tan(α/2)], "
       "[tan(α/2), 0]], then prove that (I + A) = (I − A)[[cos α, "
       "−sin α], [sin α, cos α]]. (c) Differentiate tan⁻¹(sinx/"
       "(1 + cosx)) with respect to x. (d) Find the shortest "
       "distance between the lines r⃗ = î + ĵ + λ(2î − ĵ + k̂) and "
       "r⃗ = (2î + ĵ − k̂) + μ(3î + ĵ + 2k̂). (e) If y = e^(tan⁻¹x), "
       "prove that (1 + x²)(d²y/dx²) + (2x − 1)(dy/dx) = 0."),
    _q(6, "A", 25, "continuity-and-differentiability",
       "Do all parts. (a) If f(x) = {−2, if x ≤ −1; 2x, if −1 < x "
       "≤ 1; 2, if x > 1}, then test the continuity of the "
       "function at x = −1 and at x = 1. (b) Three vectors a⃗, b⃗ "
       "and c⃗ satisfy the condition a⃗ + b⃗ + c⃗ = 0. If |a⃗| = 3, "
       "|b⃗| = 4 and |c⃗| = 2, then find the value of a⃗·b⃗ + "
       "b⃗·c⃗ + c⃗·a⃗. (c) The radius of an air bubble is "
       "increasing at the rate of 1/2 cm/s. At what rate is the "
       "volume of the bubble increasing while the radius is 1 "
       "cm? (d) Minimize Z = 3x + 2y by graphical method under "
       "the following constraints: x + y ≥ 8, 3x + 5y ≤ 15, x ≥ "
       "0, y ≥ 0. (e) The probabilities of solving a problem by "
       "three students A, B, C are 3/10, 1/5 and 1/10 "
       "respectively. Find the probability that the problem is "
       "solved."),
    _q(7, "A", 8, "matrices",
       "Do any one part. (a) Find the inverse of the matrix A = "
       "[[2, 0, −1], [5, 1, 0], [0, 1, 3]]. OR (b) Solve the "
       "system of equations by matrix method: 3x − 2y + 3z = 8, "
       "2x + y − z = 1, 4x − 3y + 2z = 4."),
    _q(8, "A", 8, "application-of-derivatives",
       "Do any one part. (a) Prove that the semi-vertical angle "
       "of a cone with given slant height and maximum volume is "
       "tan⁻¹(√2). OR (b) Find a particular solution of the "
       "differential equation (x − y)(dx + dy) = dx − dy, when y "
       "= −1 and x = 0."),
    _q(9, "A", 8, "integrals",
       "Do any one part. (a) Integrate: ∫((2 + sin 2x)/(1 + cos "
       "2x)) e^x dx OR (b) Solve: ∫(3x + 5)/(x³ − x² − x + 1) dx"),
]
_UP12_2025_HI = [
    _q(1, "A", 5, "relations-and-functions",
       "सभी खण्ड कीजिए। प्रत्येक खण्ड का सही विकल्प चुनकर अपनी "
       "उत्तर-पुस्तिका में लिखिए। (क) f(x) = |x| द्वारा प्रदत्त "
       "मापांक फलन f: R → R+ है (a) एकैकी और आच्छादक (b) "
       "बहु-एकैकी और आच्छादक (c) एकैकी, किन्तु आच्छादक नहीं (d) "
       "न तो एकैकी और न ही आच्छादक (ख) एक सम्बन्ध R = {(a, b) : "
       "a = b − 1, b ≥ 3} समुच्चय N पर परिभाषित है तो: (a) (2, "
       "4) ∈ R (b) (4, 5) ∈ R (c) (4, 6) ∈ R (d) (1, 3) ∈ R (ग) "
       "∫(0 to π/2) dx/(1 + √tanx) का मान होगा: (a) 0 (b) π/2 "
       "(c) π/4 (d) π/8 (घ) अवकल समीकरण 9(d²y/dx²) = {1 + "
       "(dy/dx)²}^(1/3) की घात है: (a) 1 (b) 6 (c) 3 (d) 2 (ङ) "
       "व्यंजक î·î − ĵ·ĵ + k̂ × k̂ का मान है: (a) 0 (b) 1 (c) 2 "
       "(d) 3"),
    _q(2, "A", 5, "inverse-trigonometric-functions",
       "सभी खण्ड कीजिए: (क) cot⁻¹{1/√(x² − 1)}; x > 1 को सरलतम "
       "रूप में लिखिए। (ख) सिद्ध कीजिए कि फलन f(x) = |x|, x = 0 "
       "पर संतत है। (ग) अवकल समीकरण xy(d²y/dx²) + x(dy/dx)² − "
       "y(dy/dx) = 2 की घात ज्ञात कीजिए। (घ) यदि P(A) = 0.12, "
       "P(B) = 0.15 और P(B/A) = 0.18 तो P(A∩B) का मान ज्ञात "
       "कीजिए। (ङ) सदिशों −2î + ĵ + 3k̂ और 3î − 2ĵ + k̂ के बीच "
       "का कोण ज्ञात कीजिए।"),
    _q(3, "A", 8, "relations-and-functions",
       "सभी खण्ड कीजिए: (क) यदि f: R → R तथा g: R → R फलन क्रमशः "
       "f(x) = cosx तथा g(x) = 3x² द्वारा परिभाषित है तो सिद्ध "
       "कीजिए gof ≠ fog. (ख) अवकल समीकरण ydx + (x − y²)dy = 0 का "
       "व्यापक हल ज्ञात कीजिए। (ग) सिद्ध कीजिए कि (4, 4, 2), (3, "
       "5, 2) तथा (-1, -1, 2) एक समकोण त्रिभुज के शीर्ष हैं। "
       "(घ) यदि [[x + y, 2], [5 + z, xy]] = [[6, 2], [5, 8]], तो "
       "x, y, z के मान ज्ञात कीजिए।"),
    _q(4, "A", 8, "application-of-derivatives",
       "सभी खण्ड कीजिए: (क) दर्शाइए कि फलन f(x) = 7x² − 3 एक "
       "वर्धमान फलन है जबकि x > 0 है। (ख) सदिश (a⃗ + b⃗) और (a⃗ "
       "− b⃗) में से प्रत्येक पर लंबवत् मात्रक सदिश ज्ञात कीजिए, "
       "जहाँ a⃗ = î + ĵ + k̂, b⃗ = î + 2ĵ + 3k̂. (ग) यदि एक रेखा "
       "का कार्तीय समीकरण (x − 5)/3 = (y + 4)/7 = (z − 6)/2 है, "
       "तो इसका सदिश रूप में समीकरण ज्ञात कीजिए। (घ) एक थैले में "
       "4 सफेद और 2 काली गेंद हैं तथा दूसरे थैले में 3 सफेद और 5 "
       "काली गेंद हैं। यदि प्रत्येक थैले से एक गेंद निकाली जाये "
       "तो दोनों गेंद काली होने की प्रायिकता ज्ञात कीजिए।"),
    _q(5, "A", 25, "relations-and-functions",
       "सभी खण्ड कीजिए: (क) यदि R₁ तथा R₂ समुच्चय A में दो "
       "तुल्यता संबंध हैं, तो सिद्ध कीजिए कि R₁ ∩ R₂ भी एक "
       "तुल्यता संबंध है। (ख) यदि A = [[0, −tan(α/2)], "
       "[tan(α/2), 0]] तो सिद्ध कीजिए कि (I + A) = (I − A)"
       "[[cosα, −sinα], [sinα, cosα]] (ग) tan⁻¹(sinx/(1 + cosx)) "
       "का x के सापेक्ष अवकलन कीजिए। (घ) रेखाओं r⃗ = î + ĵ + "
       "λ(2î − ĵ + k̂) तथा r⃗ = (2î + ĵ − k̂) + μ(3î + ĵ + 2k̂) के "
       "मध्य न्यूनतम दूरी ज्ञात कीजिए। (ङ) यदि y = e^(tan⁻¹x), "
       "सिद्ध कीजिए कि (1 + x²)(d²y/dx²) + (2x − 1)(dy/dx) = 0."),
    _q(6, "A", 25, "continuity-and-differentiability",
       "सभी खण्ड कीजिए: (क) यदि f(x) = {−2 यदि x ≤ −1; 2x यदि "
       "−1 < x ≤ 1; 2 यदि x > 1} तब x = −1 तथा x = 1 पर फलन के "
       "संतत की जाँच कीजिए। (ख) तीन सदिश a⃗, b⃗ और c⃗ प्रतिबंध "
       "a⃗ + b⃗ + c⃗ = 0 को संतुष्ट करते हैं। यदि |a⃗| = 3, |b⃗| "
       "= 4 और |c⃗| = 2, तो a⃗·b⃗ + b⃗·c⃗ + c⃗·a⃗ का मान ज्ञात "
       "कीजिए। (ग) हवा के एक बुलबुले की त्रिज्या 1/2 cm/s की दर "
       "से बढ़ रही है। बुलबुले का आयतन किस दर से बढ़ रहा है "
       "जबकि त्रिज्या 1 cm है? (घ) निम्नलिखित अवरोधों के "
       "अन्तर्गत Z = 3x + 2y का आलेखीय विधि से न्यूनतमिकरण "
       "कीजिए जबकि: x + y ≥ 8, 3x + 5y ≤ 15, x ≥ 0, y ≥ 0 (ङ) "
       "किसी प्रश्न को तीन छात्रों A, B, C के द्वारा हल करने की "
       "प्रायिकता क्रमशः 3/10, 1/5 तथा 1/10 है, तो प्रश्न के हल "
       "हो जाने की प्रायिकता ज्ञात कीजिए।"),
    _q(7, "A", 8, "matrices",
       "कोई एक खण्ड कीजिए: (क) A = [[2, 0, −1], [5, 1, 0], [0, "
       "1, 3]] का व्युत्क्रम ज्ञात कीजिए। अथवा (ख) समीकरण निकाय "
       "3x − 2y + 3z = 8, 2x + y − z = 1, 4x − 3y + 2z = 4 को "
       "आव्यूह विधि से हल कीजिए।"),
    _q(8, "A", 8, "application-of-derivatives",
       "कोई एक खण्ड कीजिए: (क) सिद्ध कीजिए कि दी गई तिर्यक "
       "ऊँचाई और महत्तम आयतन वाले शंकु का अर्ध-शीर्ष कोण "
       "tan⁻¹(√2) होता है। अथवा (ख) अवकल समीकरण (x − y)(dx + dy) "
       "= dx − dy का एक विशिष्ट हल ज्ञात कीजिए, जबकि y = −1 यदि "
       "x = 0."),
    _q(9, "A", 8, "integrals",
       "कोई एक खण्ड कीजिए: (क) समाकलन कीजिए: ∫((2 + sin2x)/"
       "(1 + cos2x))e^x dx अथवा (ख) हल कीजिए: ∫(3x + 5)dx/"
       "(x³ − x² − x + 1)"),
]

# Wave 66: HBSE (Haryana Board) Class 10 Mathematics
# (Standard) 2024, Code No. 1103, Set A — Hindi-medium text.
# The booklet is bilingual (Hindi and English Medium printed
# on the cover); the Hindi text below was read question by
# question from the page images of the same AglaSem scan used
# for the English entry hbse-10-2024 (the PDF's Hindi text
# layer is a legacy-font encoding, so the images are the
# reliable source). Sections, marks and chapter tags mirror
# the English entry exactly. MCQ options are labelled (a)-(d)
# in the app's Hindi convention; the printed paper labels them
# (A)-(D).
_HBSE10_2024_HI = [
    _q(1, "A", 1, "real-numbers",
       "6, 72 तथा 120 का L.C.M. है: (a) 120 (b) 6 (c) 360 (d) "
       "240"),
    _q(2, "A", 1, "real-numbers",
       "निम्नलिखित में से कौन-सी संख्या परिमेय है? (a) 7 + √2 "
       "(b) 5 − √3 (c) 2 + √9 (d) 5 − √2"),
    _q(3, "A", 1, "polynomials",
       "एक द्विघात बहुपद जिसके शून्यकों के योग तथा गुणनफल "
       "क्रमशः 4 और 1 हैं, है: (a) x² − 4x − 1 (b) x² − 4x + 1 "
       "(c) x² + 4x − 1 (d) x² + 4x + 1"),
    _q(4, "A", 1, "arithmetic-progressions",
       "10, 7, 4, ....... का कौन-सा पद −62 है? (a) 15वाँ (b) "
       "25वाँ (c) 27वाँ (d) 30वाँ"),
    _q(5, "A", 1, "quadratic-equations",
       "k का मान जिसके लिए द्विघात समीकरण kx² − 2kx + 6 = 0 के "
       "मूल बराबर हैं: (a) 6 (b) −6 (c) 8 (d) −8"),
    _q(6, "A", 1, "coordinate-geometry",
       "बिन्दुओं (−5, 7) और (−1, 3) के बीच की दूरी है: (a) 2√2 "
       "(b) 4√2 (c) 5√2 (d) 6√2"),
    _q(7, "A", 1, "triangles",
       "त्रिभुज ABC और DEF में, ∠B = ∠E, ∠C = ∠F और AB = DE है, "
       "तब दो त्रिभुज हैं: (a) समरूप और सर्वांगसम (b) सर्वांगसम "
       "लेकिन समरूप नहीं (c) समरूप लेकिन सर्वांगसम नहीं (d) न "
       "सर्वांगसम और न समरूप"),
    _q(8, "A", 1, "circles",
       "यदि एक बिन्दु P से O केन्द्र वाले किसी वृत्त पर PA, PB "
       "स्पर्श रेखाएँ परस्पर 80° के कोण पर झुकी हों, तो ∠POA "
       "बराबर है: (a) 50° (b) 60° (c) 70° (d) 80°"),
    _q(9, "A", 1, "circles",
       "5 सेमी त्रिज्या वाले एक वृत्त के बिन्दु P पर स्पर्श "
       "रेखा PQ केन्द्र O से जाने वाली एक रेखा से बिन्दु Q पर "
       "इस प्रकार मिलती है कि OQ = 12 सेमी, PQ की लंबाई है: (a) "
       "12 सेमी (b) 13 सेमी (c) 8 सेमी (d) √119 सेमी"),
    _q(10, "A", 1, "introduction-to-trigonometry",
       "sin 60° cos 30° + sin 30° cos 60° का मान क्या है? (a) "
       "−1 (b) 1 (c) 0 (d) 2"),
    _q(11, "A", 1, "introduction-to-trigonometry",
       "यदि sin A = 3/4, तो tan A का मान क्या है? (a) 3/√7 (b) "
       "4/√7 (c) 3/5 (d) 4/5"),
    _q(12, "A", 1, "introduction-to-trigonometry",
       "9 sec²A − 9 tan²A बराबर है: (a) 1 (b) 9 (c) 8 (d) 0"),
    _q(13, "A", 1, "areas-related-to-circles",
       "त्रिज्या R वाले वृत्त के उस त्रिज्यखण्ड का क्षेत्रफल "
       "जिसका कोण P° है: (a) (P/180) × 2πR (b) (P/180) × πR² "
       "(c) (P/360) × 2πR (d) (P/720) × 2πR²"),
    _q(14, "A", 1, "areas-related-to-circles",
       "6 सेमी त्रिज्या वाले एक वृत्त के त्रिज्यखण्ड का "
       "क्षेत्रफल, जिसका कोण 60° है: (a) 132/7 सेमी² (b) 264/7 "
       "सेमी² (c) 132 सेमी² (d) 64/7 सेमी²"),
    _q(15, "A", 1, "surface-areas-and-volumes",
       "त्रिज्या 2.1 सेमी वाले धातु के गोले का पृष्ठीय "
       "क्षेत्रफल है: (a) 88.7 सेमी² (b) 194.5 सेमी² (c) 55.44 "
       "सेमी² (d) 39.04 सेमी²"),
    _q(16, "A", 1, "statistics",
       "यदि किन्हीं आँकड़ों का माध्यक और बहुलक क्रमशः 11 और 17 "
       "हैं, तो उनका माध्य है: (a) 7 (b) 8 (c) 9 (d) 10"),
    _q(17, "A", 1, "statistics",
       "निम्नलिखित वितरण के लिए माध्यक वर्ग और बहुलक वर्ग की "
       "निचली सीमाओं का योग है: वर्ग अन्तराल: 0-5, 5-10, "
       "10-15, 15-20, 20-25; बारंबारता: 10, 15, 12, 20, 9 (a) "
       "15 (b) 25 (c) 30 (d) 35"),
    _q(18, "A", 1, "probability",
       "एक पासे को एक बार फेंका जाता है। विषम संख्या प्राप्त "
       "करने की प्रायिकता है: (a) 1/3 (b) 1/2 (c) 1/4 (d) 1/5"),
    _q(19, "A", 1, "real-numbers",
       "अभिकथन (A): √3 एक अपरिमेय संख्या का उदाहरण है। कारण "
       "(R): सभी धनात्मक पूर्णांकों के वर्गमूल अपरिमेय संख्या "
       "होती हैं। (a) अभिकथन (A) और कारण (R) दोनों सही हैं और "
       "कारण (R), अभिकथन (A) की सही व्याख्या करता है। (b) "
       "अभिकथन (A) और कारण (R) दोनों सही हैं, लेकिन कारण (R), "
       "अभिकथन (A) की सही व्याख्या नहीं है। (c) अभिकथन (A) सही "
       "है, लेकिन कारण (R) गलत है। (d) अभिकथन (A) गलत है, "
       "लेकिन कारण (R) सही है।"),
    _q(20, "A", 1, "coordinate-geometry",
       "अभिकथन (A): बिन्दु (0, 5) y-अक्ष पर स्थित है। कारण (R): "
       "y-अक्ष पर किसी भी बिंदु का x-निर्देशांक शून्य होता है। "
       "(a) अभिकथन (A) और कारण (R) दोनों सही हैं और कारण (R), "
       "अभिकथन (A) की सही व्याख्या करता है। (b) अभिकथन (A) और "
       "कारण (R) दोनों सही हैं, लेकिन कारण (R), अभिकथन (A) की "
       "सही व्याख्या नहीं है। (c) अभिकथन (A) सही है, लेकिन "
       "कारण (R) गलत है। (d) अभिकथन (A) गलत है, लेकिन कारण (R) "
       "सही है।"),
    _q(21, "B", 2, "pair-of-linear-equations",
       "निम्नलिखित रैखिक समीकरणों के युग्म को हल करें: 2x + 3y "
       "= 13 और 5x − 4y = −2"),
    _q(22, "B", 2, "some-applications-of-trigonometry",
       "धरती पर एक मीनार ऊर्ध्वाधर खड़ी है। धरती के एक बिंदु "
       "से, जो मीनार के पाद बिंदु से 15 m दूर है, मीनार के शिखर "
       "का उन्नयन कोण 60° है। मीनार की ऊँचाई ज्ञात कीजिए। अथवा "
       "आकृति में PS/SQ = PT/TR है तथा ∠PST = ∠PRQ है। सिद्ध "
       "कीजिए कि ΔPQR एक समद्विबाहु त्रिभुज है।"),
    _q(23, "B", 2, "circles",
       "एक बिंदु A से जो वृत्त के केन्द्र से 5 cm की दूरी पर "
       "है, वृत्त पर स्पर्शरेखा की लम्बाई 4 cm है। वृत्त की "
       "त्रिज्या ज्ञात कीजिए।"),
    _q(24, "B", 2, "introduction-to-trigonometry",
       "निम्नलिखित का मान ज्ञात कीजिए: 2 tan²45° + cos²30° − "
       "sin²60°"),
    _q(25, "B", 2, "areas-related-to-circles",
       "त्रिज्या 4 cm वाले एक वृत्त के त्रिज्यखण्ड का "
       "क्षेत्रफल ज्ञात कीजिए, जिसका कोण 30° है। अथवा एक वृत्त "
       "के चतुर्थांश का क्षेत्रफल ज्ञात कीजिए, जिसकी परिधि 22 "
       "सेमी है।"),
    _q(26, "C", 3, "real-numbers",
       "सिद्ध कीजिए √5 एक अपरिमेय संख्या है।"),
    _q(27, "C", 3, "polynomials",
       "द्विघात बहुपद x² + 7x + 10 के शून्यक ज्ञात कीजिए और "
       "शून्यकों तथा गुणांकों के बीच के संबंध की सत्यता की "
       "जाँच कीजिए।"),
    _q(28, "C", 3, "pair-of-linear-equations",
       "दो व्यक्तियों की आय का अनुपात 9 : 7 है और उनके खर्चों "
       "का अनुपात 4 : 3 है। यदि प्रत्येक व्यक्ति प्रति महीने "
       "2,000 रुपया बचा लेता है, तो उनकी मासिक आय ज्ञात कीजिए। "
       "अथवा दो संपूरक कोणों में बड़ा कोण छोटे कोण से 18° अधिक "
       "है। उन्हें ज्ञात कीजिए।"),
    _q(29, "C", 3, "circles",
       "सिद्ध कीजिए कि दो संकेन्द्रीय वृत्तों में बड़े वृत्त "
       "की जीवा जो छोटे वृत्त को स्पर्श करती है, स्पर्श बिंदु "
       "पर समद्विभाजित होती है।"),
    _q(30, "C", 3, "introduction-to-trigonometry",
       "सिद्ध कीजिए: √((1 + sin A)/(1 − sin A)) = sec A + tan "
       "A अथवा सिद्ध कीजिए: sec A(1 − sin A)(sec A + tan A) = 1"),
    _q(31, "C", 3, "probability",
       "एक पासे को एक बार फेंका जाता है। निम्नलिखित को प्राप्त "
       "करने की प्रायिकता ज्ञात कीजिए: (i) एक अभाज्य संख्या "
       "(ii) 2 और 6 के बीच स्थित कोई संख्या (iii) एक विषम "
       "संख्या"),
    _q(32, "D", 5, "quadratic-equations",
       "दो क्रमागत धनात्मक पूर्णांक ज्ञात कीजिए, जिनके वर्गों "
       "का योग 365 है। अथवा समीकरण 3x² − 2x + 1/3 = 0 का "
       "विविक्तकर ज्ञात कीजिए और फिर मूलों की प्रकृति ज्ञात "
       "कीजिए। यदि वे वास्तविक हैं, तो उन्हें ज्ञात कीजिए।"),
    _q(33, "D", 5, "triangles",
       "90 cm की लंबाई वाली एक लड़की बल्ब लगे एक खंभे के आधार "
       "से परे 1.2 m/s की चाल से चल रही है। यदि बल्ब भूमि से "
       "3.6 m की ऊँचाई पर है, तो 4 सेकण्ड बाद उस लड़की की छाया "
       "की लंबाई ज्ञात कीजिए।"),
    _q(34, "D", 5, "surface-areas-and-volumes",
       "शांता किसी शेड (shed) में एक उद्योग चलाती है। यह शेड "
       "एक घनाभ के आकार का है जिस पर एक अर्ध-बेलन आरोपित है। "
       "यदि इस शेड के आधार की विमाएँ 7 m × 15 m हैं, तो "
       "घनाभाकार भाग की ऊँचाई 8 m है, तो शेड में समावेशित हो "
       "सकने वाली हवा का आयतन ज्ञात कीजिए। पुनः यदि मान लें कि "
       "शेड में रखी मशीनरी 300 m³ स्थान घेरती है और शेड के "
       "अन्दर 20 श्रमिक हैं जिनमें से प्रत्येक 0.08 m³ के औसत "
       "से स्थान घेरता है, तब शेड में कितनी हवा होगी? (π = "
       "22/7 लीजिए) अथवा आकृति में दर्शाया गया सजावट के लिए "
       "प्रयोग होने वाले ब्लॉक दो ठोसों से मिलकर बना है। इसमें "
       "से एक घन है दूसरा अर्धगोला है। इस ब्लॉक का आधार 5 cm "
       "कोर या किनारे वाला एक घन है और ऊपरी लगे हुए अर्धगोले "
       "का व्यास 4.2 cm है। इस ब्लॉक का संपूर्ण पृष्ठीय "
       "क्षेत्रफल ज्ञात कीजिए। (π = 22/7 लीजिए)"),
    _q(35, "D", 5, "statistics",
       "निम्नलिखित बारंबारता बंटन किसी मोहल्ले के 68 "
       "उपभोक्ताओं की बिजली की मासिक खपत दर्शाता है। इन आँकड़ों "
       "के लिए बहुलक ज्ञात कीजिए: मासिक खपत (इकाईयों में): "
       "65-85 — 4 उपभोक्ता, 85-105 — 5, 105-125 — 13, 125-145 "
       "— 20, 145-165 — 14, 165-185 — 8, 185-205 — 4"),
    _q(36, "E", 4, "arithmetic-progressions",
       "प्रकरण अध्ययन: टी०वी० सेटों का निर्माता तीसरे वर्ष "
       "में 600 टी०वी० तथा 7वें वर्ष में 700 टी०वी० सेटों का "
       "उत्पादन करता है। यह मानते हुए कि प्रत्येक वर्ष उत्पादन "
       "में एक समान रूप से निश्चित संख्या में वृद्धि होती है, "
       "ज्ञात कीजिए: (i) प्रथम वर्ष में उत्पादन (ii) 10वें "
       "वर्ष में उत्पादन (iii) (a) प्रथम 7 वर्षों में कुल "
       "उत्पादन अथवा (b) 10 वर्षों में कुल उत्पादन"),
    _q(37, "E", 4, "coordinate-geometry",
       "प्रकरण अध्ययन: एक सोसाइटी के रेजिडेंट वेलफेयर "
       "एसोसिएशन (RWA) ने एक सोसाइटी के पार्क में तीन बिजली के "
       "खंभे A, B और C लगाए। इन तीन खंभों के बावजूद, पार्क के "
       "कुछ हिस्सों में अभी भी अंधेरा है इसलिए RWA एक और बिजली "
       "का खंभा D लगाने का फैसला किया। उपरोक्त जानकारी के आधार "
       "पर निम्नलिखित प्रश्नों के उत्तर दें: (i) खंभे C की "
       "स्थिति ज्ञात कीजिए। (ii) पार्क के कोने O से खंभे B की "
       "दूरी ज्ञात कीजिए। (iii) (a) चौथे खंभे D की स्थिति "
       "ज्ञात कीजिए, ताकि चार बिंदु A, B, C और D एक समांतर "
       "चतुर्भुज बना लें। अथवा (b) खंभों A और C के बीच की दूरी "
       "ज्ञात कीजिए। (खंभों की स्थितियाँ दी गई आकृति में बने "
       "पार्क के ग्रिड से पढ़नी हैं।)"),
    _q(38, "E", 4, "some-applications-of-trigonometry",
       "प्रकरण अध्ययन: सड़क के दोनों ओर खड़े समान ऊँचाई के दो "
       "खंभों पर दो होर्डिंग लगाए जाते हैं। सड़क पर उनके बीच "
       "एक बिंदु से खंभों के शीर्ष का उन्नयन कोण क्रमशः 60° और "
       "30° है। प्रत्येक खंभे की ऊँचाई 20 मीटर है। उपरोक्त "
       "जानकारी के आधार पर निम्नलिखित प्रश्नों के उत्तर दीजिए: "
       "(i) PO की लंबाई ज्ञात कीजिए। (ii) RO की लंबाई ज्ञात "
       "कीजिए। (iii) (a) सड़क की चौड़ाई ज्ञात कीजिए। अथवा (b) "
       "यदि खंभे PQ द्वारा बनाया गया उन्नयन कोण 45° है, तो PO "
       "की लंबाई ज्ञात कीजिए।"),
]

# Wave 66: HBSE (Haryana Board) Class 12 Mathematics 2024,
# Code No. 1232, Set A — Hindi-medium text. The booklet is
# bilingual (Hindi and English Medium printed on the cover);
# the Hindi text was read question by question from the page
# images of the same AglaSem scan used for the English entry
# hbse-12-2024 (the PDF's Hindi text layer is a legacy-font
# encoding). Sections, marks and chapter tags mirror the
# English entry. The printed Hindi instructions name the
# sections 'अ', 'ब', 'स', 'द', 'ध'. MCQ options are labelled
# (a)-(d) in the app's Hindi convention; the paper labels them
# (A)-(D). Reading the printed pages also settled three
# readings the English entry had flagged as provisional —
# Q11's bracket carries an outer square, Q23's fraction
# carries a square root and its lower bound is printed
# without a minus sign, and Q30's integrand is sqrt(tan x) —
# and the English entry has been corrected to match.
_HBSE12_2024_HI = [
    _q(1, "A", 1, "relations-and-functions",
       "मान लीजिए कि N प्राकृत संख्याओं का समुच्चय है तथा f: N "
       "→ N, f(n) = 2n + 3 ∀ n ∈ N द्वारा परिभाषित एक फलन है, "
       "तो f है: (a) आच्छादी (b) एकैक (c) एकैकी आच्छादी (d) "
       "इनमें से कोई नहीं"),
    _q(2, "A", 1, "inverse-trigonometric-functions",
       "sin⁻¹2x का प्रांत है: (a) [0, 1] (b) [−1, 1] (c) "
       "[−1/2, 1/2] (d) [−2, 2]"),
    _q(3, "A", 1, "matrices",
       "कोटि 3 × 3 के सभी सम्भव आव्यूहों की संख्या, जिनकी "
       "प्रत्येक प्रविष्टि 2 या 0 हो, होगी: (a) 9 (b) 27 (c) "
       "81 (d) 512"),
    _q(4, "A", 1, "determinants",
       "यदि |x, 2; 18, x| = |6, 2; 18, 6| हो, तो x बराबर है: "
       "(a) 6 (b) ±6 (c) −6 (d) 0"),
    _q(5, "A", 1, "determinants",
       "यदि A, 3 × 3 कोटि का व्युत्क्रमणीय वर्ग आव्यूह है, तो "
       "|adj. A| का मान है ............।"),
    _q(6, "A", 1, "continuity-and-differentiability",
       "x के सापेक्ष sin(log x) का अवकलज है: (a) cos(log x)/x² "
       "(b) cos(log x) (c) cos(log x)/x (d) इनमें से कोई नहीं"),
    _q(7, "A", 1, "continuity-and-differentiability",
       "cos x के सापेक्ष sin x का अवकलज ............ है।"),
    _q(8, "A", 1, "integrals",
       "∫e^x sec x(1 + tan x)dx बराबर है: (a) e^x cos x + c (b) "
       "e^x sec x + c (c) e^x sin x + c (d) e^x tan x + c"),
    _q(9, "A", 1, "integrals",
       "∫(−π/2 to π/2) sin⁵x dx का मान बराबर है ............।"),
    _q(10, "A", 1, "application-of-integrals",
       "वृत्त x² + y² = 2 द्वारा परिबद्ध क्षेत्र का क्षेत्रफल "
       "बराबर है: (a) 4π वर्ग इकाई (b) 2√2π वर्ग इकाई (c) 4π² "
       "वर्ग इकाई (d) 2π वर्ग इकाई"),
    _q(11, "A", 1, "differential-equations",
       "अवकल समीकरण [1 + (dy/dx)²]² = d²y/dx² के क्रमशः कोटि "
       "और घात हैं: (a) 1, 2 (b) 2, 2 (c) 2, 1 (d) 4, 2"),
    _q(12, "A", 1, "differential-equations",
       "अवकल समीकरण x(dy/dx) − y = sin x का समाकलन गुणक (I.F.) "
       "............ है।"),
    _q(13, "A", 1, "vector-algebra",
       "मान लीजिए सदिश a⃗ और b⃗ इस प्रकार हैं कि |a⃗| = 3 और "
       "|b⃗| = √2/3, तब a⃗ × b⃗ एक मात्रक सदिश है, यदि a⃗ और b⃗ "
       "के बीच का कोण है: (a) π/6 (b) π/4 (c) π/3 (d) π/2"),
    _q(14, "A", 1, "vector-algebra",
       "यदि सदिश a⃗ = 2î + λĵ + k̂ तथा b⃗ = î + 2ĵ + 3k̂ लांबिक "
       "(orthogonal) हो, तो λ का मान है ............।"),
    _q(15, "A", 1, "three-dimensional-geometry",
       "आकाश (स्पेस) में x-अक्ष का समीकरण है: (a) x = 0, y = 0 "
       "(b) x = 0, z = 0 (c) x = 0 (d) y = 0, z = 0"),
    _q(16, "A", 1, "probability",
       "यदि पासों का एक जोड़ा उछाला जाता है, तो प्रत्येक पासे "
       "पर सम अभाज्य संख्या प्राप्त करने की प्रायिकता "
       "............ है।"),
    _q(17, "A", 1, "probability",
       "एक थैले में 5 लाल तथा 3 नीली गेंदें हैं। यदि 3 गेंदें "
       "यादृच्छया बिना प्रतिस्थापन के निकाली जाती हैं, तो "
       "तथ्यतः एक लाल रंग की गेंद के निकलने की प्रायिकता "
       "............ है।"),
    _q(18, "A", 1, "probability",
       "ताश के 52 पत्तों की भली-भाँति फेंटी हुई किसी गड्डी से "
       "दो पत्ते प्रतिस्थापन सहित निकाले जाते हैं। दोनों पत्तों "
       "के 'रानी' होने की प्रायिकता है ............।"),
    _q(19, "A", 1, "relations-and-functions",
       "अभिकथन (A): समुच्चय A = {1, 2, 3, 4, 5} पर परिभाषित "
       "संबंध R = {(a, b); |a − b| < 2} स्वतुल्य (reflexive) "
       "है। कारण (R): किसी समुच्चय A पर परिभाषित संबंध R "
       "स्वतुल्य (reflexive) कहलाता है, यदि (a, b) ∈ R तथा "
       "(b, c) ∈ R से (a, c) ∈ R प्राप्त हो। (a) अभिकथन (A) "
       "एवं कारण (R) दोनों सही हैं तथा कारण (R), अभिकथन (A) "
       "की सही व्याख्या है। (b) अभिकथन (A) एवं कारण (R) दोनों "
       "सही हैं तथा कारण (R), अभिकथन (A) की सही व्याख्या नहीं "
       "है। (c) अभिकथन (A) सही है, किन्तु कारण (R) गलत है। "
       "(d) अभिकथन (A) गलत है, किन्तु कारण (R) सही है।"),
    _q(20, "A", 1, "three-dimensional-geometry",
       "अभिकथन (A): सरल रेखाओं (x + 1)/2 = (y − 2)/5 = (z + "
       "3)/4 तथा (x − 1)/1 = (y + 2)/2 = (z − 3)/(−3) के बीच "
       "का कोण 90° है। कारण (R): विषमतलीय रेखाएँ विभिन्न तलों "
       "में स्थित रेखाएँ होती हैं जो समान्तर और प्रतिच्छेदी "
       "होती हैं। (a) अभिकथन (A) एवं कारण (R) दोनों सही हैं "
       "तथा कारण (R), अभिकथन (A) की सही व्याख्या है। (b) "
       "अभिकथन (A) एवं कारण (R) दोनों सही हैं तथा कारण (R), "
       "अभिकथन (A) की सही व्याख्या नहीं है। (c) अभिकथन (A) "
       "सही है, किन्तु कारण (R) गलत है। (d) अभिकथन (A) गलत "
       "है, किन्तु कारण (R) सही है।"),
    _q(21, "B", 2, "relations-and-functions",
       "मान लीजिए कि f: R → R, f(x) = sin x तथा g: R → R, g(x) "
       "= x² द्वारा परिभाषित है, तो fog तथा gof ज्ञात कीजिए। "
       "दिखाइए कि: fog ≠ gof अथवा मान ज्ञात कीजिए: cos⁻¹(1/2) + "
       "2 sin⁻¹(1/2)"),
    _q(22, "B", 2, "matrices",
       "यदि A = [[cos θ, sin θ], [−sin θ, cos θ]] हो, तो "
       "सत्यापित कीजिए कि: A'A = I"),
    _q(23, "B", 2, "continuity-and-differentiability",
       "x के सापेक्ष अवकलन कीजिए: tan⁻¹(√((1 − cos x)/(1 + cos "
       "x))), π/4 < x < π/4 (प्रश्न-पत्र में सीमा इसी प्रकार "
       "छपी है)"),
    _q(24, "B", 2, "differential-equations",
       "सत्यापित कीजिए कि फलन xy = log y + c अवकल समीकरण dy/dx "
       "= y²/(1 − xy), (xy ≠ 1) का हल है। अथवा अवकल समीकरण "
       "dy/dx = (1 + x²)(1 + y²) का व्यापक हल ज्ञात कीजिए।"),
    _q(25, "B", 2, "probability",
       "P(A ∪ B) ज्ञात कीजिए, यदि 2P(A) = P(B) = 5/13 और P(A/B) "
       "= 2/5।"),
    _q(26, "C", 3, "relations-and-functions",
       "सिद्ध कीजिए कि समस्त त्रिभुजों के समुच्चय A में, R = "
       "{(T₁, T₂); T₁ समरूप है T₂ के} द्वारा परिभाषित संबंध R "
       "एक तुल्यता संबंध है। अथवा निम्नलिखित फलन को सरलतम रूप "
       "में लिखिए: tan⁻¹((3a²x − x³)/(a³ − 3ax²)), a > 0; "
       "−a/√3 < x < a/√3"),
    _q(27, "C", 3, "matrices",
       "यदि A = [[3, −2], [4, −2]] और I = [[1, 0], [0, 1]], "
       "जोकि A² = KA − 2I है, तो K का मान ज्ञात कीजिए।"),
    _q(28, "C", 3, "continuity-and-differentiability",
       "K का मान ज्ञात कीजिए, ताकि प्रदत्त फलन f(x) = {K cos "
       "x/(π − 2x), यदि x ≠ π/2; 3, यदि x = π/2} बिन्दु x = π/2 "
       "पर संतत है।"),
    _q(29, "C", 3, "application-of-derivatives",
       "एक गुब्बारा, जो सदैव गोलाकार रहता है, का परिवर्तनशील "
       "व्यास (3/2)(2x + 1) है। x के सापेक्ष आयतन के परिवर्तन "
       "की दर ज्ञात कीजिए।"),
    _q(30, "C", 3, "integrals",
       "समाकलन कीजिए: ∫(√tan x/(sin x · cos x))dx अथवा समाकलन "
       "कीजिए: ∫1/(x(x⁴ − 1))dx"),
    _q(31, "C", 3, "vector-algebra",
       "λ और μ ज्ञात कीजिए, यदि (2î + 6ĵ + 27k̂) × (î + λĵ + "
       "μk̂) = 0⃗।"),
    _q(32, "D", 5, "matrices",
       "निम्नलिखित रैखिक समीकरण निकाय को आव्यूह विधि से हल "
       "कीजिए: 2x + y + z = 1; x − 2y − z = 3/2; 3y − 5z = 9"),
    _q(33, "D", 5, "integrals",
       "निम्नलिखित निश्चित समाकलन का मान ज्ञात कीजिए: ∫(0 to "
       "π/4) log(1 + tan x) dx अथवा दीर्घवृत्त 9x² + 4y² = 36 "
       "से घिरे क्षेत्र का क्षेत्रफल ज्ञात कीजिए।"),
    _q(34, "D", 5, "three-dimensional-geometry",
       "रेखाएँ, जिनके सदिश समीकरण निम्नलिखित हैं, के बीच की "
       "न्यूनतम दूरी ज्ञात कीजिए: r⃗ = î + 2ĵ + 3k̂ + λ(î − 3ĵ "
       "+ 2k̂) और r⃗ = 4î + 5ĵ + 6k̂ + μ(2î + 3ĵ + k̂) अथवा "
       "रेखाएँ, जिनके सदिश समीकरण निम्नलिखित हैं, के बीच की "
       "न्यूनतम दूरी ज्ञात कीजिए: r⃗ = (1 − t)î + (t − 2)ĵ + "
       "(3 − 2t)k̂ और r⃗ = (s + 1)î + (2s − 1)ĵ − (2s + 1)k̂"),
    _q(35, "D", 5, "linear-programming",
       "निम्न अवरोधों के अन्तर्गत z = 5x + 10y का न्यूनतमीकरण "
       "तथा अधिकतमीकरण कीजिए: x + 2y ≤ 120, x + y ≥ 60, x − 2y "
       "≥ 0, x ≥ 0, y ≥ 0"),
    _q(36, "E", 4, "application-of-derivatives",
       "प्रकरण अध्ययन: माना त्रिज्या R वाले एक गोले के "
       "अन्तर्गत एक शंकु है। शंकु की ऊँचाई तथा त्रिज्या क्रमशः "
       "h तथा r हैं। उपरोक्त जानकारी के आधार पर निम्नलिखित "
       "प्रश्नों के उत्तर दीजिए: (i) r और R के बीच संबंध x के "
       "पदों में लिखें। (ii) शंकु का आयतन V को R और x के पदों "
       "में लिखें। (iii) दिखाइए कि x = R/3 पर शंकु का आयतन "
       "अधिकतम है। अथवा यदि x = R/3 पर शंकु का आयतन V अधिकतम "
       "है, तो V का अधिकतम मान ज्ञात कीजिए। जब शंकु का आयतन "
       "अधिकतम है, तब शंकु के आयतन तथा गोले के आयतन का अनुपात "
       "ज्ञात कीजिए। (x दी गई आकृति में अंकित है — गोले के "
       "केन्द्र से शंकु के आधार-तल की दूरी।)"),
    _q(37, "E", 4, "differential-equations",
       "प्रकरण अध्ययन: एक जिले में 50 K बच्चों को पोलियो "
       "ड्रॉप्स पिलाई जाती है। पोलियो ड्रॉप्स देने की दर उन "
       "बच्चों की संख्या के समानुपाती है जिन्हें ड्रॉप्स नहीं "
       "पिलाई गई है। दूसरे सप्ताह के अंत तक आधे बच्चों को "
       "पोलियो की खुराक दी जा चुकी है। तीसरे सप्ताह के अंत तक "
       "कितनों को ड्रॉप्स दी गई होगी, इसका अनुमान अवकल समीकरण "
       "dy/dx = λ(50 − y) के हल से लगाया जा सकता है, जहाँ x "
       "सप्ताहों की संख्या को दर्शाता है और y उन बच्चों की "
       "संख्या को दर्शाता है जिन्हें ड्रॉप्स दी गई है। उपरोक्त "
       "जानकारी के आधार पर निम्नलिखित प्रश्नों के उत्तर दीजिए: "
       "(i) उपरोक्त अवकल समीकरण की कोटि ज्ञात कीजिए। (ii) अवकल "
       "समीकरण dy/dx = λ(50 − y) को हल करने के लिए किस विधि का "
       "उपयोग किया जा सकता है? (iii) अवकल समीकरण dy/dx = λ(50 "
       "− y) को हल कीजिए। अथवा यदि λ = 0.049 तथा y(0) = 0, तो "
       "अवकल समीकरण का विशिष्ट हल ज्ञात कीजिए।"),
    _q(38, "E", 4, "probability",
       "प्रकरण अध्ययन: एक स्कूल में शिक्षक 3 छात्रों रवि, "
       "मोहित और सोनिया से एक प्रश्न पूछते हैं। रवि, मोहित और "
       "सोनिया के प्रश्न हल करने की प्रायिकता क्रमशः 30%, 25% "
       "और 45% है। रवि, मोहित और सोनिया द्वारा त्रुटि करने की "
       "प्रायिकता क्रमशः 1%, 1.2% और 2% है। उपरोक्त जानकारी के "
       "आधार पर निम्नलिखित प्रश्नों के उत्तर दीजिए: (i) प्रश्न "
       "को हल करने में त्रुटि होने की कुल प्रायिकता ज्ञात "
       "कीजिए। (ii) यदि प्रश्न का हल शिक्षक द्वारा जाँचा गया "
       "है और उसमें कुछ त्रुटि है, तो प्रायिकता ज्ञात कीजिए "
       "कि प्रश्न रवि द्वारा हल नहीं किया गया है।"),
]

# Wave 66: MP Board (MPBSE) Class 10 Mathematics 2025, High
# School Examination (Main), paper code 102513, Set A. One
# bilingual booklet (Hindi & English Versions); both texts
# were read from the page images of the AglaSem scan (the PDF
# has no text layer) and cross-checked against each other.
# Maximum Marks 75, Time 3 Hours, 23 questions, all
# compulsory, no sections in the real paper (stored under one
# section heading). Q1-Q5 are objective bundles of six
# 1-mark parts each (6 marks each); Q6-Q17 carry 2 marks,
# Q18-Q20 carry 3 marks and Q21-Q23 carry 4 marks, each with
# an internal choice — 75 marks in all, as printed.
_MP10_2025_EN = [
    _q(1, "A", 6, "real-numbers",
       "Choose the correct option and write it: (i) H.C.F. of "
       "numbers 6 and 20 is - (a) 2 (b) 6 (c) 20 (d) 1 (ii) "
       "When a₁/a₂ = b₁/b₂ = c₁/c₂ then the system of equation "
       "a₁x + b₁y + c₁ = 0 and a₂x + b₂y + c₂ = 0 has: (a) "
       "Unique solution (b) Both solutions (c) No solution (d) "
       "Infinitely many solutions (iii) The quadratic equation "
       "ax² + bx + c = 0 has real and equal roots if: (a) b² − "
       "4ac > 0 (b) b² − 4ac = 0 (c) b² − 4ac < 0 (d) b² − 4ac² "
       "= 0 (iv) 10th term of an A. P.: 2, 4, 6, .... is: (a) 2 "
       "(b) 18 (c) 20 (d) 22 (v) The distance between points "
       "(2, 3) and (4, 1) is: (a) √8 (b) 3√3 (c) 3√2 (d) 2√3 "
       "(vi) How many tangents can a circle have? (a) 0 (b) 1 "
       "(c) 2 (d) Infinite"),
    _q(2, "A", 6, "real-numbers",
       "Fill in the blanks: (i) √2 is a __________ number. "
       "(ii) A polynomial of degree 3 is called a __________ "
       "polynomial. (iii) In the A. P.: 3/2, 1/2, −1/2, −3/2, "
       "..... the common difference d is __________. (iv) All "
       "congruent triangles are __________. (v) A line "
       "intersecting a circle in two points is called a "
       "__________. (vi) For any event E, P(E) + P(Ē) = "
       "__________"),
    _q(3, "A", 6, "triangles",
       "Write True / False in the following: (i) Area of "
       "similar triangle are always equal. (ii) 1, 2, 1, 3, "
       ".... is not an A.P. (iii) The distance of a point from "
       "the y-axis is called its y-coordinate. (iv) The volume "
       "of cone is πr². (v) The probability of an event E is a "
       "number P(E) such that 0 ≤ P(E) ≤ 1. (vi) The area of "
       "minor segment is less than the area of corresponding "
       "sector."),
    _q(4, "A", 6, "introduction-to-trigonometry",
       "Match the correct column: Column - \"A\": (i) 9sec²A − "
       "9tan²A (ii) cos0° (iii) sin0° (iv) Area of sector of "
       "angle θ (v) Curved surface area of hemisphere (vi) "
       "Total surface area of hemisphere; Column - \"B\": (a) 0 "
       "(b) (θ/360) × πr² (c) 2πr² (d) 3πr² (e) 1 (f) 9"),
    _q(5, "A", 6, "quadratic-equations",
       "Write the answer in one word / sentence of each: (i) "
       "Write the standard form of a quadratic equation. (ii) "
       "Write any one condition of similarity of two "
       "triangles. (iii) Write the distance between origin (0, "
       "0) and point (x₁, y₁). (iv) If shadow and height of the "
       "pole are equal, then what will be the angle of the "
       "elevation of the Sun? (v) Write the formula of the "
       "length of an arc of a sector of angle θ and radius r. "
       "(vi) Write the class mark (middle point) of 20 - 40."),
    _q(6, "A", 2, "real-numbers",
       "Find the H.C.F. of 96 and 404 by prime factorisation "
       "method. OR Express the number 148 as a product of its "
       "prime factors."),
    _q(7, "A", 2, "real-numbers",
       "Write the statement of fundamental theorem of "
       "Arithmetic. OR Explain, why 7 × 11 × 13 + 13 and 7 × 6 "
       "× 5 × 4 × 3 × 2 × 1 + 5 are composite numbers."),
    _q(8, "A", 2, "polynomials",
       "The graph y = P(x) is given below for some polynomial "
       "P(x). Find the number of zeroes of P(x) in this case. "
       "OR Find the zeroes of the Quadratic Polynomial x² − 3x "
       "− 10."),
    _q(9, "A", 2, "polynomials",
       "Find the zeroes of 4u² + 8u. OR Find a quadratic "
       "polynomial, if the sum and product of whose zeroes are "
       "−1/4 and 1/4 respectively."),
    _q(10, "A", 2, "pair-of-linear-equations",
       "Solve the following pair of linear equations: x + 2y = "
       "8, x − y = 8 OR On comparing ratios a₁/a₂, b₁/b₂, "
       "c₁/c₂, find out whether the pair of linear equations "
       "2x − 3y = 8 and 4x − 6y = 9 are consistent or "
       "inconsistent."),
    _q(11, "A", 2, "arithmetic-progressions",
       "Find the 10th term of the A.P.: 2, 7, 12, ..... OR "
       "Which term of the A.P.: 21, 18, 15, ..... is −81?"),
    _q(12, "A", 2, "triangles",
       "Write the statement of Basic Proportionality Theorem. "
       "OR In fig. if OA·OB = OC·OD, show that ∠A = ∠C and ∠B = "
       "∠D."),
    _q(13, "A", 2, "coordinate-geometry",
       "Find a point on the y-axis which is equidistant from "
       "the points A(6, 5) and B(−4, 3). OR Find the distance "
       "between the points (a, b) and (−a, −b)."),
    _q(14, "A", 2, "introduction-to-trigonometry",
       "If cos A = 3/5, find the value of sin A and tan A. OR "
       "Find the value of: 2 tan 30°/(1 − tan²30°)"),
    _q(15, "A", 2, "areas-related-to-circles",
       "In a circle of radius 14 cm, an arc subtends an angle "
       "of 45° at the centre. Find the area of the sector "
       "formed by the arc. (π = 22/7 or 3.14) OR Find the "
       "length of the arc of a circle with radius 7 cm and of "
       "angle is 60°. (π = 22/7)"),
    _q(16, "A", 2, "probability",
       "Two players A and B play a tennis match. It is known "
       "that the probability of A winning the match is 0.63. "
       "What is the probability of B winning the match? OR A "
       "die thrown once. Find the probability of getting a "
       "prime number."),
    _q(17, "A", 2, "probability",
       "A bag contains 3 red and 5 black balls. A ball is "
       "drawn at random from the bag. What is the probability "
       "that the ball drawn is (i) red? (ii) not red? OR One "
       "card is drawn from a well-shuffled deck of 52 cards. "
       "Find the probability of getting a red face card."),
    _q(18, "A", 3, "quadratic-equations",
       "Find the roots of the equation 2x² − 5x + 3 = 0 by "
       "factorisation. OR Find two consecutive positive "
       "integers, sum of whose squares is 365."),
    _q(19, "A", 3, "circles",
       "Prove that the lengths of tangents drawn from an "
       "external point to a circle are equal. OR Two "
       "concentric circles are of radii 5 cm and 3 cm. Find "
       "the length of the chord of the larger circle which "
       "touches the smaller circle."),
    _q(20, "A", 3, "surface-areas-and-volumes",
       "2 cubes each of volume 64 cm³ are joined end to end. "
       "Find the surface area of the resulting cuboid. OR A "
       "juice seller was serving his customers using glasses "
       "as shown in fig. The inner diameter of the cylindrical "
       "glass was 5 cm, but the bottom of the glass had a "
       "hemispherical raised portion which reduced the "
       "capacity of the glass. If the height of a glass was 10 "
       "cm, find the apparent capacity of the glass and its "
       "actual capacity. (Use π = 3.14)"),
    _q(21, "A", 4, "pair-of-linear-equations",
       "A fraction becomes 9/11, if 2 added to both the "
       "numerator and the denominator. If 3 is added to both "
       "the numerator and the denominator it becomes 5/6. Find "
       "the fraction. OR Solve the following pair of linear "
       "equations by elimination method: x + y = 5, 2x − 3y = "
       "4"),
    _q(22, "A", 4, "some-applications-of-trigonometry",
       "A statue, 2 m tall, stands on the top of a pedestal. "
       "From a point on the ground, the angle of elevation of "
       "the top of the statue is 60° and from the same point "
       "the angle of elevation of the top of the pedestal is "
       "45°. Find the height of the pedestal. (Use √3 = 1.732) "
       "OR The angle of elevation of the top of a building "
       "from the foot of the tower is 30° and the angle of "
       "elevation of the top of the tower from the foot of the "
       "building is 60°. If the tower is 45 m high, find the "
       "height of the building."),
    _q(23, "A", 4, "statistics",
       "A survey conducted on 21 households in a locality by a "
       "group of students resulted in the following frequency "
       "table for the number of family members in a household: "
       "Family size: 1 - 3, 3 - 5, 5 - 7, 7 - 9, 9 - 11; "
       "Number of families: 7, 8, 3, 2, 1. Find the mode of "
       "this data. OR The following table gives the literacy "
       "rate (in percentage) of 34 cities. Find the mean "
       "literacy rate by assumed mean method. Literacy rate "
       "(in %): 45 - 55, 55 - 65, 65 - 75, 75 - 85, 85 - 95; "
       "Number of cities: 3, 10, 11, 8, 2"),
]
_MP10_2025_HI = [
    _q(1, "A", 6, "real-numbers",
       "सही विकल्प चुनकर लिखिए: (i) संख्याओं 6 व 20 का H.C.F. "
       "होगा - (a) 2 (b) 6 (c) 20 (d) 1 (ii) यदि a₁/a₂ = b₁/b₂ "
       "= c₁/c₂ हो, तो समीकरण निकाय a₁x + b₁y + c₁ = 0 तथा a₂x "
       "+ b₂y + c₂ = 0 का - (a) एक अद्वितीय हल होगा (b) दोनों "
       "हल होंगे (c) कोई भी हल नहीं होगा (d) अनंततः अनेक हल "
       "होंगे (iii) द्विघात समीकरण ax² + bx + c = 0 के मूल "
       "वास्तविक और बराबर होंगे यदि - (a) b² − 4ac > 0 (b) b² "
       "− 4ac = 0 (c) b² − 4ac < 0 (d) b² − 4ac² = 0 (iv) A. "
       "P.: 2, 4, 6, .... का 10वाँ पद है: (a) 2 (b) 18 (c) 20 "
       "(d) 22 (v) बिंदु (2, 3) तथा (4, 1) के बीच दूरी है: (a) "
       "√8 (b) 3√3 (c) 3√2 (d) 2√3 (vi) एक वृत्त की कितनी "
       "स्पर्श रेखा हो सकती है? (a) 0 (b) 1 (c) 2 (d) अनन्त"),
    _q(2, "A", 6, "real-numbers",
       "रिक्त स्थानों की पूर्ति कीजिए: (i) √2 एक __________ "
       "संख्या है। (ii) एक बहुपद जिसकी घात 3 है, वह __________ "
       "बहुपद कहलाता है। (iii) A. P.: 3/2, 1/2, −1/2, −3/2, "
       "..... का सार्व अंतर d = __________ है। (iv) सभी "
       "सर्वांगसम त्रिभुज __________ होते हैं। (v) वृत्त को दो "
       "बिंदुओं पर प्रतिच्छेद करने वाली रेखा को __________ "
       "कहते हैं। (vi) किसी घटना E के लिए P(E) + P(Ē) = "
       "__________"),
    _q(3, "A", 6, "triangles",
       "निम्नलिखित में सत्य / असत्य लिखिए: (i) समरूप त्रिभुजों "
       "के क्षेत्रफल सदैव बराबर होते हैं। (ii) 1, 2, 1, 3, "
       ".... एक समान्तर श्रेढ़ी (A.P.) नहीं है। (iii) किसी "
       "बिंदु की y-अक्ष से दूरी उस बिंदु का y-निर्देशांक होती "
       "है। (iv) शंकु का आयतन πr² है। (v) घटना E की प्रायिकता "
       "एक ऐसी संख्या P(E) है कि 0 ≤ P(E) ≤ 1 (vi) दीर्घवृत्त "
       "खण्ड का क्षेत्रफल संगत त्रिज्यखंड के क्षेत्रफल से कम "
       "होता है।"),
    _q(4, "A", 6, "introduction-to-trigonometry",
       "सही जोड़ी मिलाइए: स्तम्भ - \"A\": (i) 9sec²A − 9tan²A "
       "(ii) cos0° (iii) sin0° (iv) कोण θ वाले त्रिज्यखंड का "
       "क्षेत्रफल (v) अर्धगोले का वक्र पृष्ठीय क्षेत्रफल (vi) "
       "अर्धगोले का सम्पूर्ण पृष्ठीय क्षेत्रफल; स्तम्भ - "
       "\"B\": (a) 0 (b) (θ/360) × πr² (c) 2πr² (d) 3πr² (e) 1 "
       "(f) 9"),
    _q(5, "A", 6, "quadratic-equations",
       "प्रत्येक का एक शब्द / वाक्य में उत्तर लिखिए: (i) "
       "द्विघात समीकरण का मानक रूप लिखिए। (ii) दो त्रिभुजों के "
       "समरूप होने की कोई एक शर्त लिखिए। (iii) मूलबिंदु (0, 0) "
       "से बिंदु (x₁, y₁) की दूरी लिखिए। (iv) किसी खंभे की "
       "छाया तथा ऊँचाई समान होने पर सूर्य का उन्नयन कोण कितना "
       "होगा? (v) कोण θ एवं त्रिज्या r वाले त्रिज्यखण्ड के "
       "संगत चाप की लंबाई का सूत्र लिखिए। (vi) वर्ग 20 - 40 का "
       "वर्ग चिह्न (मध्य बिंदु) लिखिए।"),
    _q(6, "A", 2, "real-numbers",
       "अभाज्य गुणनखण्ड विधि द्वारा 96 और 404 का H.C.F. ज्ञात "
       "कीजिए। अथवा संख्या 148 को अभाज्य गुणनखंडों के गुणनफल "
       "के रूप में व्यक्त कीजिए।"),
    _q(7, "A", 2, "real-numbers",
       "अंकगणित का आधारभूत प्रमेय का कथन लिखिए। अथवा व्याख्या "
       "कीजिए कि 7 × 11 × 13 + 13 और 7 × 6 × 5 × 4 × 3 × 2 × 1 "
       "+ 5 भाज्य संख्याएँ क्यों हैं।"),
    _q(8, "A", 2, "polynomials",
       "किसी बहुपद P(x) के लिए, y = P(x) का ग्राफ नीचे दिया "
       "है। इस स्थिति में P(x) के शून्यकों की संख्या ज्ञात "
       "कीजिए। अथवा द्विघात बहुपद x² − 3x − 10 के शून्यक ज्ञात "
       "कीजिए।"),
    _q(9, "A", 2, "polynomials",
       "4u² + 8u के शून्यक ज्ञात कीजिए। अथवा एक द्विघात बहुपद "
       "ज्ञात कीजिए, जिसके शून्यकों का योग तथा गुणनफल क्रमशः "
       "−1/4 और 1/4 है।"),
    _q(10, "A", 2, "pair-of-linear-equations",
       "निम्न रैखिक समीकरण युग्म को हल कीजिए: x + 2y = 8, x − "
       "y = 8 अथवा अनुपातों a₁/a₂, b₁/b₂, c₁/c₂ की तुलना कर "
       "ज्ञात कीजिए की रेखीय समीकरण युग्म 2x − 3y = 8 व 4x − "
       "6y = 9 संगत हैं या असंगत हैं।"),
    _q(11, "A", 2, "arithmetic-progressions",
       "A. P.: 2, 7, 12, ..... का 10वाँ पद ज्ञात कीजिए। अथवा "
       "A. P.: 21, 18, 15, ..... का कौन-सा पद −81 है?"),
    _q(12, "A", 2, "triangles",
       "आधारभूत समानुपातिकता प्रमेय का कथन लिखिए। अथवा आकृति "
       "में यदि OA·OB = OC·OD है, दर्शाइए कि ∠A = ∠C और ∠B = "
       "∠D है।"),
    _q(13, "A", 2, "coordinate-geometry",
       "y-अक्ष पर एक ऐसा बिंदु ज्ञात कीजिए, जो बिंदुओं A(6, 5) "
       "और B(−4, 3) से समदूरस्थ हो। अथवा बिंदुओं (a, b) और "
       "(−a, −b) के बीच की दूरी ज्ञात कीजिए।"),
    _q(14, "A", 2, "introduction-to-trigonometry",
       "यदि cos A = 3/5 हो, तो sin A और tan A का मान ज्ञात "
       "कीजिए। अथवा मान ज्ञात कीजिए: 2 tan 30°/(1 − tan²30°)"),
    _q(15, "A", 2, "areas-related-to-circles",
       "त्रिज्या 14 cm वाले वृत्त का एक चाप केन्द्र पर 45° का "
       "कोण अंतरित करता है। संगत चाप द्वारा बनाए गए त्रिज्यखंड "
       "का क्षेत्रफल ज्ञात कीजिए। (π = 22/7 या 3.14) अथवा 7 cm "
       "त्रिज्या वाले एक वृत्त के चाप की लंबाई ज्ञात कीजिए, "
       "जिसका कोण 60° है। (π = 22/7)"),
    _q(16, "A", 2, "probability",
       "दो खिलाड़ी A और B टेनिस का एक मैच खेलते हैं। यह ज्ञात "
       "है कि A द्वारा मैच जीतने की प्रायिकता 0.63 है। B के "
       "मैच जीतने की प्रायिकता क्या है? अथवा एक पासे को एक बार "
       "फेंकने पर अभाज्य संख्या आने की प्रायिकता ज्ञात कीजिए।"),
    _q(17, "A", 2, "probability",
       "एक थैले में 3 लाल और 5 काली गेंदें हैं। इस थैले में से "
       "एक गेंद यादृच्छया निकाली जाती है। इसकी प्रायिकता क्या "
       "है कि गेंद (i) लाल हो? (ii) लाल नहीं हो? अथवा 52 "
       "पत्तों की अच्छी प्रकार से फेंटी गई एक गड्डी में से एक "
       "पत्ता निकाला जाता है। लाल रंग का तस्वीर वाला पत्ता "
       "प्राप्त करने की प्रायिकता ज्ञात कीजिए।"),
    _q(18, "A", 3, "quadratic-equations",
       "गुणनखंड द्वारा समीकरण 2x² − 5x + 3 = 0 के मूल ज्ञात "
       "कीजिए। अथवा दो क्रमागत धनात्मक पूर्णांक ज्ञात कीजिए "
       "जिनके वर्गों का योग 365 हो।"),
    _q(19, "A", 3, "circles",
       "सिद्ध करो कि बाह्य बिंदु से वृत्त पर खींची गई स्पर्श "
       "रेखाओं की लंबाइयाँ बराबर होती हैं। अथवा दो संकेन्द्रीय "
       "वृत्तों की त्रिज्याएँ 5 cm तथा 3 cm हैं। बड़े वृत्त की "
       "उस जीवा की लंबाई ज्ञात कीजिए जो छोटे वृत्त को स्पर्श "
       "करती हो।"),
    _q(20, "A", 3, "surface-areas-and-volumes",
       "दो घनों, जिनमें से प्रत्येक का आयतन 64 cm³ है, के "
       "संलग्न फलकों को मिलाकर एक ठोस बनाया जाता है। इससे "
       "प्राप्त घनाभ का पृष्ठीय क्षेत्रफल ज्ञात कीजिए। अथवा "
       "एक जूस (juice) बेचने वाला अपने ग्राहकों को आकृति में "
       "दर्शाए गिलासों से जूस देता था। बेलनाकार गिलास का "
       "आंतरिक व्यास 5 cm था, परंतु गिलास के निचले आधार (तली) "
       "में एक उभरा हुआ अर्धगोला था, जिससे गिलास की धारिता कम "
       "हो जाती थी। यदि एक गिलास की ऊँचाई 10 cm थी, तो गिलास "
       "की आभासी (apparent) धारिता तथा उसकी वास्तविक धारिता "
       "ज्ञात कीजिए। (π = 3.14 लीजिए)"),
    _q(21, "A", 4, "pair-of-linear-equations",
       "यदि किसी भिन्न के अंश और हर दोनों में 2 जोड़ दिया "
       "जाए, तो वह 9/11 हो जाती है। यदि अंश और हर दोनों में 3 "
       "जोड़ दिया जाए, तो वह 5/6 हो जाती है। वह भिन्न ज्ञात "
       "कीजिए। अथवा निम्नलिखित रैखिक समीकरण युग्म को विलोपन "
       "विधि से हल कीजिए: x + y = 5, 2x − 3y = 4"),
    _q(22, "A", 4, "some-applications-of-trigonometry",
       "एक पेडस्टल के शिखर पर एक 2 m ऊँची मूर्ति लगी है। भूमि "
       "पर एक बिंदु से मूर्ति के शिखर का उन्नयन कोण 60° है और "
       "उसी बिंदु से पेडस्टल के शिखर का उन्नयन कोण 45° है। "
       "पेडस्टल की ऊँचाई ज्ञात कीजिए। (√3 = 1.732 लीजिए) अथवा "
       "एक मीनार के पाद बिंदु से एक भवन के शिखर का उन्नयन कोण "
       "30° है और भवन के पाद-बिंदु से मीनार के शिखर का उन्नयन "
       "कोण 60° है। यदि मीनार 45 m ऊँची हो, तो भवन की ऊँचाई "
       "ज्ञात कीजिए।"),
    _q(23, "A", 4, "statistics",
       "विद्यार्थियों के एक समूह द्वारा एक मोहल्ले के 21 "
       "परिवारों पर किए गए सर्वेक्षण के परिणामस्वरूप विभिन्न "
       "परिवारों के सदस्यों की संख्या से संबंधित निम्नलिखित "
       "आँकड़े प्राप्त हुए: परिवार माप: 1 - 3, 3 - 5, 5 - 7, "
       "7 - 9, 9 - 11; परिवारों की संख्या: 7, 8, 3, 2, 1. इन "
       "आँकड़ों का बहुलक ज्ञात कीजिए। अथवा निम्नलिखित सारणी 34 "
       "नगरों की साक्षरता दर (प्रतिशत में) दर्शाती है। माध्य "
       "साक्षरता दर कल्पित माध्य विधि (assumed mean method) "
       "से ज्ञात कीजिए। साक्षरता दर (% में): 45 - 55, 55 - "
       "65, 65 - 75, 75 - 85, 85 - 95; नगरों की संख्या: 3, 10, "
       "11, 8, 2"),
]

# Wave 66: Bihar Board (BSEB) Class 10 Mathematics 2025,
# Secondary School Examination (Annual), Subject Code 110.
# One bilingual booklet; both texts were read from the page
# images of the AglaSem scan and cross-checked (the PDF's
# Hindi text layer is a legacy-font encoding and its English
# layer drops exponents, so the images are the authority).
# Full Marks 100, Time 3 Hours 15 Minutes, 138 questions:
# Section-A 100 objective questions of 1 mark (answer any
# 50); Section-B Short Answer Q1-30 of 2 marks (answer any
# 15) and Long Answer Q31-38 of 5 marks (answer any 4). The
# entry therefore carries max_marks 100: the stored texts sum
# to 200 because every printed question is typed in full.
_BSEB10_2025_EN_A = [
    _q(1, "A", 1, "real-numbers", "Which of the following is a rational number? (A) √7 + √7 (B) √25 + √3 (C) 1/√4 (D) √9 × √3"),
    _q(2, "A", 1, "real-numbers", "If m is an integer then the form of every odd integer is – (A) m + 1 (B) m (C) 2m (D) 2m + 1"),
    _q(3, "A", 1, "real-numbers", "Which of the following has terminating decimal expansion? (A) 11/91 (B) 15/23 (C) 17/80 (D) 7/45"),
    _q(4, "A", 1, "real-numbers", "0.87̄ = (A) 87/90 (B) 87/99 (C) 79/90 (D) 79/99"),
    _q(5, "A", 1, "real-numbers", "If 540 = 2^x × 3^y × 5^z then x + y − z = (A) 4 (B) 5 (C) 3 (D) 6"),
    _q(6, "A", 1, "real-numbers", "Which of the following is an irrational number? (A) 2.3̄ (B) √13 × √13 (C) √441 (D) √(10/100)"),
    _q(7, "A", 1, "real-numbers", "If m and n are two prime numbers then their highest common factor will be – (A) 0 (B) 1 (C) 2 (D) 3"),
    _q(8, "A", 1, "real-numbers", "The product of two numbers is 2366 and their Lowest Common Multiple is 182 then Highest Common Factor will be (A) 13 (B) 23 (C) 3 (D) 16"),
    _q(9, "A", 1, "real-numbers", "Which of the following has non-terminating decimal expansion? (A) 11/40 (B) 17/160 (C) 33/200 (D) 13/441"),
    _q(10, "A", 1, "real-numbers", "If p = ab³ and q = a⁴b, where p, q positive integer and a, b are prime numbers then the Lowest Common Multiple of (p, q) is (A) ab (B) a³b³ (C) a⁴b³ (D) a⁴b⁴"),
    _q(11, "A", 1, "real-numbers", "Which of the following pair is Co-prime? (A) (15, 45) (B) (9, 16) (C) (21, 105) (D) (14, 84)"),
    _q(12, "A", 1, "real-numbers", "0.3125 can be written in the form of p/q as- (A) 5/8 (B) 5/16 (C) 1/8 (D) 5/4"),
    _q(13, "A", 1, "polynomials", "Which of the following is a polynomial? (A) x² + √2x + 1 (B) x + 6/x (C) (1/4)x³ − 3x² + √121 (D) 2x² + √4x"),
    _q(14, "A", 1, "polynomials", "The degree of the polynomial (x + 3)²(x³ − 8) is (A) 2 (B) 5 (C) 6 (D) 4"),
    _q(15, "A", 1, "polynomials", "The zeroes of the polynomial 2x² − 6 are (A) (√3, −√3) (B) (√3, √3) (C) (−√3, −√3) (D) (3, −3)"),
    _q(16, "A", 1, "polynomials", "The polynomial p(x) = 2x² − 8x − 12, then the value of p(2) is – (A) 20 (B) −20 (C) 36 (D) −28"),
    _q(17, "A", 1, "polynomials", "If zeroes of the polynomial 3y² + 7y − K are reciprocal to each other, then the value of K will be– (A) 1/3 (B) −1/3 (C) 3 (D) −3"),
    _q(18, "A", 1, "polynomials", "The number of polynomial with zeroes −2, −5 will be– (A) 2 (B) 3 (C) 5 (D) Infinite"),
    _q(19, "A", 1, "polynomials", "If α and β are zeroes of the polynomial p(x) = 5x² + 7x − 12, then the value of 5(α + β) is – (A) −7 (B) 7 (C) 35 (D) 60"),
    _q(20, "A", 1, "polynomials", "If α, β, γ are zeroes of the Cubic polynomial ax³ + bx² + cx + d, then the value of α·β·γ is (A) c/a (B) −c/a (C) b/a (D) −d/a"),
    _q(21, "A", 1, "pair-of-linear-equations", "If the lines 5x + py = 6 and 15x + 9y = 12 are parallel, then the value of p will be (A) 3 (B) 1/3 (C) 2 (D) 9"),
    _q(22, "A", 1, "pair-of-linear-equations", "If the graph of two linear equations in two variables is intersecting lines, then the number of solutions will be (A) no solution (B) only one (C) infinite solution (D) none of these"),
    _q(23, "A", 1, "pair-of-linear-equations", "If 5x − 8y = 0 and 10x − 18y = 0 then the values of x and y are– (A) x = 5, y = 0 (B) x = 0, y = 8 (C) x = 0, y = 0 (D) x = 1, y = 1"),
    _q(24, "A", 1, "quadratic-equations", "If the equation ax² + bx + c = 0, a ≠ 0, has equal roots, then c = (A) −b²/(4a) (B) b²/(4a) (C) b/(2a) (D) −b/(2a)"),
    _q(25, "A", 1, "quadratic-equations", "Which of the following is not a quadratic equation? (A) (x + 2)² = 3(x² − 4) (B) 4x − x² = x² + 7 (C) (√2x − 3)² = 2x² + 4 (D) (x − 1)² = 3x² − 2x + 4"),
    _q(26, "A", 1, "quadratic-equations", "If one root of the quadratic equation x² − 7x + 12 = 0 is 3 then its other root will be – (A) −3 (B) 4 (C) −4 (D) 2"),
    _q(27, "A", 1, "quadratic-equations", "If p and q are roots of the quadratic equation x² + px + q = 0, then p + q = (A) 1 (B) −1 (C) 2 (D) −2"),
    _q(28, "A", 1, "quadratic-equations", "The discriminant of the quadratic equation 3x² − 13x + 10 = 0 is – (A) 49 (B) −49 (C) 13 (D) 169"),
    _q(29, "A", 1, "quadratic-equations", "The product of the roots of the quadratic equation x(2x + 5) = 0 is (A) 5/2 (B) 0 (C) −5/2 (D) 2/5"),
    _q(30, "A", 1, "arithmetic-progressions", "Which of the following is an arithmetic progression? (A) 0.2, 0.22, 0.222, 0.2222, … (B) √7, √28, √63, √112, … (C) 2, 4, 8, 16, … (D) 1, 1/2, 3/2, 2, …"),
    _q(31, "A", 1, "arithmetic-progressions", "Which term of the arithmetic progression 12, 10, 8, … is 0? (A) 7th (B) 8th (C) 9th (D) 10th"),
    _q(32, "A", 1, "arithmetic-progressions", "The Common difference of the arithmetic progression −5, −1, 3, 7, … is – (A) 4 (B) −4 (C) 3 (D) −6"),
    _q(33, "A", 1, "arithmetic-progressions", "If the first term of an arithmetic progression is 'a' and Common difference is 'd' then the sum of first n terms of the arithmetic progression will be (A) n{2a + (n − 1) × d} (B) n(n + 1)/2 (C) (n/2){2a + (n − 1) × d} (D) (1/2){a + (n − 1)d}"),
    _q(34, "A", 1, "arithmetic-progressions", "If the nth term of an arithmetic progression, t_n = 3 − 4n then t_5 = (A) −17 (B) 17 (C) 20 (D) −20"),
    _q(35, "A", 1, "arithmetic-progressions", "If the general term of an arithmetic progression is (17 − 5n) then its Common difference will be– (A) 5 (B) −5 (C) 12 (D) 0"),
    _q(36, "A", 1, "arithmetic-progressions", "The sum of first n odd natural numbers is (A) n² − 1 (B) n + 1 (C) 2n − 1 (D) n²"),
    _q(37, "A", 1, "arithmetic-progressions", "If 18, x, y, −3 are in arithmetic progression then x + y = (A) 7 (B) 13 (C) 21 (D) 15"),
    _q(38, "A", 1, "introduction-to-trigonometry", "If A and B are complementary angles, then (A) sinB = sinB (B) secA = cosecB (C) cotA = cotB (D) tanA = tanB"),
    _q(39, "A", 1, "introduction-to-trigonometry", "cos(90° − ϕ) = (A) sinϕ (B) cosϕ (C) −sinϕ (D) −cosϕ"),
    _q(40, "A", 1, "introduction-to-trigonometry", "cos²27° − sin²63° = (A) −1 (B) 0 (C) 1 (D) 1/2"),
    _q(41, "A", 1, "introduction-to-trigonometry", "sin2θ = 2sinθ is true when θ = (A) 60° (B) 45° (C) 30° (D) 0°"),
    _q(42, "A", 1, "introduction-to-trigonometry", "If sinθ = 4/5 then tan θ = (A) 5/4 (B) 3/4 (C) 4/3 (D) 4/5"),
    _q(43, "A", 1, "introduction-to-trigonometry", "If tanθ = 1/√7 then sec²θ − tan²θ = (A) 2√2/7 (B) 2√2 (C) √7 (D) 1"),
    _q(44, "A", 1, "introduction-to-trigonometry", "(1 − tan²45°)/(1 + tan²45°) = (A) 0 (B) 1 (C) 2 (D) 1/2"),
    _q(45, "A", 1, "introduction-to-trigonometry", "3cot²60° = (A) 1/3 (B) 1 (C) 3 (D) √3"),
    _q(46, "A", 1, "introduction-to-trigonometry", "cos1°·cos2°·cos3° … cos180° = (A) 1 (B) −1 (C) 0 (D) −1/2"),
    _q(47, "A", 1, "introduction-to-trigonometry", "2 − 2cosec²A = (A) −cot²A (B) cot²A (C) 2cot²A (D) −2cot²A"),
    _q(48, "A", 1, "introduction-to-trigonometry", "If asinx = 1 and bcosx = 1 then cotx = (A) 1 (B) a/b (C) b/a (D) 1/(ab)"),
    _q(49, "A", 1, "introduction-to-trigonometry", "sin²45° + cos²45° − 1 = (A) 0 (B) 1/2 (C) 1 (D) −1"),
    _q(50, "A", 1, "introduction-to-trigonometry", "−tan²A + 1/(1 − sin²A) = (A) 0 (B) 1 (C) −1 (D) 2tan²A"),
]
_BSEB10_2025_EN_B = [
    _q(51, "A", 1, "introduction-to-trigonometry", "(cos75°/sin15°)² − (sin15°/cos75°)² = (A) 1 (B) 2 (C) 0 (D) 4"),
    _q(52, "A", 1, "introduction-to-trigonometry", "(cos60°/sin60°) × tan60° = (A) 0 (B) 1 (C) √3 (D) 2"),
    _q(53, "A", 1, "introduction-to-trigonometry", "If cosecϕ − cotϕ = y then cotϕ = (A) (1 − y²)/(2y) (B) (y² − 1)/(2y) (C) (1 − y²)/2 (D) (1 − y²)/y"),
    _q(54, "A", 1, "introduction-to-trigonometry", "cosec30° = (A) sin30° (B) sec60° (C) cosec60° (D) sec30°"),
    _q(55, "A", 1, "introduction-to-trigonometry", "If 2cos3θ = 1 then θ = (A) 10° (B) 20° (C) 30° (D) 60°"),
    _q(56, "A", 1, "introduction-to-trigonometry", "If sinB = a/b then cosB = (A) √(b² − a²)/b (B) b/√(b² − a²) (C) b/a (D) a/√(b² − a²)"),
    _q(57, "A", 1, "introduction-to-trigonometry", "If tanA + cotA = 2 then tan²A + cot²A = (A) 0 (B) 1 (C) 2 (D) 4"),
    _q(58, "A", 1, "coordinate-geometry", "In which quadrant are both abscissa and ordinate negative? (A) First (B) Second (C) Third (D) Fourth"),
    _q(59, "A", 1, "coordinate-geometry", "The distance between the point A(8, 0) and B(−6, 2) is (A) 2√10 units (B) 10√2 units (C) 10 units (D) 16 units"),
    _q(60, "A", 1, "coordinate-geometry", "The point of intersection of x-axis and y-axis is said to be (A) Centroid (B) Origin (C) Orthocentre (D) Circumcentre"),
    _q(61, "A", 1, "coordinate-geometry", "The Co-ordinates of the mid-point of the line segment joining the points P(4, −5) and Q(8, 7) are (A) (2, 6) (B) (6, −1) (C) (6, 1) (D) (−2, −6)"),
    _q(62, "A", 1, "coordinate-geometry", "The distance of the point R(−x, y) from the origin is (A) √(x² − y²) units (B) √(x² + y²) units (C) (x² + y²) units (D) (x + y) units"),
    _q(63, "A", 1, "coordinate-geometry", "If points (1, 2), (−5, 6) and (a, −2) are collinear, then a = (A) 7 (B) −7 (C) 6 (D) 2"),
    _q(64, "A", 1, "coordinate-geometry", "The graph of the line y = 7 passes through which of the following point? (A) (7, 3) (B) (7, −6) (C) (5, 7) (D) (7, 1)"),
    _q(65, "A", 1, "coordinate-geometry", "The distance of the point P(4, 6) from y-axis is (A) 6 units (B) 4 units (C) 2 units (D) 10 units"),
    _q(66, "A", 1, "coordinate-geometry", "The y-Co-ordinates of a point which divide the line segment AB joining the points A(a, b) and B(c, d) in the ratio λ : 1 internally is – (A) (λd + b)/(λ + 1) (B) (λc + a)/(λ + 1) (C) (λb + d)/(λ + 1) (D) (λa + c)/(λ + 1)"),
    _q(67, "A", 1, "coordinate-geometry", "The Co-ordinates of the ends of diameter of a circle are P(8, −6) and Q(−8, 6), then Co-ordinate of its centre is– (A) (4, −3) (B) (−4, 3) (C) (1, 1) (D) (0, 0)"),
    _q(68, "A", 1, "coordinate-geometry", "The Centroid of a triangle is (4, 0) and its two vertices are (3, 4) and (5, −6), then the third vertex is (A) (2, 4) (B) (4, 2) (C) (0, 2) (D) (2, 0)"),
    _q(69, "A", 1, "coordinate-geometry", "In which quadrant does the point (−5/2, 4) lie? (A) First (B) Second (C) Third (D) Fourth"),
    _q(70, "A", 1, "coordinate-geometry", "Ordinate of all the points on x-axis is – (A) 0 (B) 1 (C) 2 (D) −1"),
    _q(71, "A", 1, "triangles", "If ΔABC and ΔPQR are similar and ∠A = 42°, ∠Q = 84° then ∠C = (A) 48° (B) 54° (C) 96° (D) 42°"),
    _q(72, "A", 1, "triangles", "In ΔPQR if PR² = PQ² + QR² then ∠Q = (A) 45° (B) 60° (C) 75° (D) 90°"),
    _q(73, "A", 1, "triangles", "If ΔABC is an equilateral triangle such that AD ⊥ BC, then AD² = (A) 2DC² (B) (3/2)DC² (C) 4DC² (D) 3CD²"),
    _q(74, "A", 1, "triangles", "In ΔABC, D and E are points on the sides AB and AC respectively such that DE ∥ BC. If AD/DB = 4/5 and AC = 18 cm. then AE = (A) 8 cm. (B) 9 cm. (C) 12 cm. (D) 4 cm."),
    _q(75, "A", 1, "triangles", "In isosceles right triangle the measure of each acute angle will be (A) 60° (B) 90° (C) 45° (D) 30°"),
    _q(76, "A", 1, "triangles", "The Corresponding heights of two similar triangles are 7 cm. and 10 cm., then the ratio of their areas will be (A) 49 : 100 (B) 100 : 49 (C) √10 : √7 (D) √7 : √10"),
    _q(77, "A", 1, "circles", "The distance between two parallel tangents drawn on a circle of radius 4.5 cm is– (A) 4.5 cm. (B) 1.5 cm. (C) 9 cm. (D) 6 cm."),
    _q(78, "A", 1, "circles", "How many tangents can be drawn to a circle from an external point? (A) Two (B) One (C) Three (D) Infinitely many"),
    _q(79, "A", 1, "circles", "If PA and PB are two tangents to a circle with centre O such that ∠APB = 50° then ∠AOB = (A) 50° (B) 25° (C) 90° (D) 130°"),
    _q(80, "A", 1, "circles", "In the given figure point O is the centre of the circle and ∠AOB = 30° then the value of ∠OBA is (A) 30° (B) 60° (C) 75° (D) 90°"),
    _q(81, "A", 1, "circles", "The length of the tangent drawn from a point 17 cm away from the centre of a circle of radius 8 cm. is – (A) 15 cm. (B) 8 cm. (C) √353 cm. (D) 25 cm."),
    _q(82, "A", 1, "surface-areas-and-volumes", "The length of the diagonal of a cube is 5√3 cm., then its total surface area will be (A) 125 cm² (B) 150 cm² (C) 75 cm² (D) 250 cm²"),
    _q(83, "A", 1, "surface-areas-and-volumes", "If the radius and height of a cylinder and a cone be equal then the ratio of their volumes will be– (A) 1 : 3 (B) 3 : 1 (C) 3 : 4 (D) 2 : 3"),
    _q(84, "A", 1, "surface-areas-and-volumes", "A surahi is the combination of (A) a sphere and a cylinder (B) a cylinder and a cone (C) two hemispheres (D) a hemisphere and a cylinder"),
    _q(85, "A", 1, "areas-related-to-circles", "Angle described by minute hand of a watch in 45 minutes is (A) 180° (B) 270° (C) 90° (D) 135°"),
    _q(86, "A", 1, "areas-related-to-circles", "Total perimeter of a semi-circle of radius 10 cm is – (A) (π + 2)10 cm. (B) (π + 1)10 cm. (C) 10π cm. (D) (π + 5)10 cm."),
    _q(87, "A", 1, "surface-areas-and-volumes", "The volume of air displaced by a sphere of diameter 6 cm. is (A) 36 cubic cm. (B) 108π cubic cm. (C) 36π cubic cm. (D) 144π cubic cm."),
    _q(88, "A", 1, "areas-related-to-circles", "The arc of a sector of an angle θ⁰ in the circle with radius p is (A) (πp²θ)/360 square unit (B) (πp²θ)/180 square unit (C) (πpθ)/360⁰ square unit (D) (p²θ)/360⁰ square unit"),
    _q(89, "A", 1, "surface-areas-and-volumes", "If the total surface area of a hemisphere is 462 cm² then its radius will be– (A) 14 cm. (B) 7 cm. (C) 6 cm. (D) 3.5 cm."),
    _q(90, "A", 1, "triangles", "The area of an equilateral triangle is 81√3 cm², then its side is (A) 9√3 cm. (B) 9 cm. (C) 3√3 cm. (D) 18 cm."),
    _q(91, "A", 1, "probability", "In tossing of three dice the number of possible outcomes is – (A) 216 (B) 136 (C) 128 (D) 18"),
    _q(92, "A", 1, "probability", "If an event cannot occur then its probability is – (A) 0 (B) 1/2 (C) 1 (D) 1/3"),
    _q(93, "A", 1, "probability", "A dice is thrown once. The probability of getting a prime number will be (A) 1/6 (B) 1/2 (C) 2/3 (D) 1/3"),
    _q(94, "A", 1, "probability", "One card is drawn at random from a well-shuffled deck of playing cards then its probability of getting a black queen is (A) 2/13 (B) 1/26 (C) 1/13 (D) 3/26"),
    _q(95, "A", 1, "probability", "The probability of getting no head in tossing two coins will be – (A) 3/4 (B) 1/3 (C) 1/2 (D) 1/4"),
    _q(96, "A", 1, "statistics", "Mode of 23, 20, 22, 37, 24, 23, 19, 22, 17, 23 is (A) 23 (B) 22 (C) 19 (D) 37"),
    _q(97, "A", 1, "statistics", "If the mean of the five data x, x + 1, x + 2, x + 3 and x + 4 is 14 then x = (A) 10 (B) 14 (C) 12 (D) 11"),
    _q(98, "A", 1, "statistics", "Which of the following is not a measure of central tendency? (A) Range (B) Mode (C) Mean (D) Median"),
    _q(99, "A", 1, "statistics", "The median of first 8 prime numbers is (A) 13 (B) 11 (C) 9 (D) 7"),
    _q(100, "A", 1, "statistics", "For the following distribution: Class-interval: 0-10, 10-20, 20-30, 30-40, 40-50; Frequency: 8, 12, 20, 6, 4. The upper limit of the modal class is- (A) 20 (B) 30 (C) 25 (D) 50"),
    _q(1, "B", 2, "real-numbers", "Prove that 2√3 is an irrational number."),
    _q(2, "B", 2, "real-numbers", "Find the Lowest Common Multiple of the numbers 12, 144 and 240 by prime factorization."),
    _q(3, "B", 2, "real-numbers", "Using Euclid's division algorithm, find the Highest Common Factor of 135 and 225."),
    _q(4, "B", 2, "polynomials", "Find the zeroes of the quadratic polynomial 6y² − 3 − 7y."),
    _q(5, "B", 2, "polynomials", "If p(x) = x² − 18x + 81 and q(x) = (x − 9) then find the degree of p(x)/q(x)."),
    _q(6, "B", 2, "polynomials", "If α and β are zeros of the polynomial f(x) = 5x² − 7x + 1. Find the value of α² + β²."),
    _q(7, "B", 2, "pair-of-linear-equations", "Solve the pair of equation x − 2y = 0 and 3x + 4y − 20 = 0."),
    _q(8, "B", 2, "quadratic-equations", "Find the discriminant of the quadratic equation 3y² − 2√6y + 2 = 0 and hence find the nature of the roots."),
    _q(9, "B", 2, "quadratic-equations", "Using quadratic formula find the roots of the equation x² + 7x − 60 = 0."),
    _q(10, "B", 2, "arithmetic-progressions", "Check Whether 301 is a term of the list of numbers 5, 11, 17, 23, … ?"),
    _q(11, "B", 2, "arithmetic-progressions", "The 17th term of an arithmetic progression exceeds its 10th term by 14. Find the Common difference."),
    _q(12, "B", 2, "arithmetic-progressions", "Find the sum: 7 + 10(1/2) + 14 + ⋯ + 84."),
    _q(13, "B", 2, "arithmetic-progressions", "Find the sum of the odd numbers between 0 and 50."),
    _q(14, "B", 2, "introduction-to-trigonometry", "If 5cotA = 3 then find the value of (5sinA − 3cosA)/(4sinA + 3cosA)."),
    _q(15, "B", 2, "introduction-to-trigonometry", "Prove that (sin⁴θ − cos⁴θ + 1)cosec²θ = 2."),
    _q(16, "B", 2, "introduction-to-trigonometry", "Find the value of (6cos²60° + 4sin²30° − cot²45°)/(sin²60° + cos²60°)."),
    _q(17, "B", 2, "introduction-to-trigonometry", "Find the value sin35°·cos55° + cos35°sin55°."),
    _q(18, "B", 2, "coordinate-geometry", "Find the area of the triangle whose vertices are (4, −3), (−9, 7) and (8, 8)."),
    _q(19, "B", 2, "coordinate-geometry", "Find the ratio in which the x-axis divides the line segment joining the points (5, −6) and (−1, −4)?"),
    _q(20, "B", 2, "coordinate-geometry", "Find the value of x for which the distance between the points P(x, 2) and Q(3, 4) is 8 units."),
    _q(21, "B", 2, "coordinate-geometry", "Find the distance of the midpoint of the line segment joining the points (8, 10) and (4, 6) from the point (2, 4)."),
    _q(22, "B", 2, "triangles", "If in ΔABC, ∠B = ∠C and points D and E are on the sides AB and AC respectively such that BD = CE then prove that DE ∥ BC."),
    _q(23, "B", 2, "triangles", "In the given figure ST ∥ QR. If ST = 3 cm., QR = 6 cm. and ar.(ΔPST) = 15 cm² then find the area of ΔPQR."),
    _q(24, "B", 2, "circles", "The length of a tangent drawn from a point P which is at a distance 13 cm. from the centre of a circle, is 12 cm. Find the radius of the circle."),
    _q(25, "B", 2, "pair-of-linear-equations", "If 2 is added to the numerator and denominator of a fraction it becomes to 5 and if 1 is subtracted from its numerator and denominator it becomes 7. Write the equations for these statements."),
    _q(26, "B", 2, "statistics", "Find the mean of the following distribution: Class-interval: 0-10, 10-20, 20-30, 30-40, 40-50; Frequency: 8, 15, 12, 16, 9"),
    _q(27, "B", 2, "areas-related-to-circles", "If the arc of a circle of radius 14 cm. subtends 120⁰ at the centre then find the length of the arc."),
    _q(28, "B", 2, "surface-areas-and-volumes", "If the height of a right circular cylinder is twice the radius of its base and its curved surface area is 616 cm², find the radius of its base."),
    _q(29, "B", 2, "probability", "If three coins are tossed simultaneously then find the probability of getting the same outcome in all three coins."),
    _q(30, "B", 2, "probability", "If two dice are thrown simultaneously, find the probability that the difference between the numbers on both the dice is 3."),
    _q(31, "B", 5, "pair-of-linear-equations", "Using graphical method, solve the pair of linear equations x − y + 1 = 0 and 2x + 3y − 12 = 0."),
    _q(32, "B", 5, "quadratic-equations", "The diagonal of a rectangular field is 60 metres more than the shorter side. If the longer side is 30 metres more than the shorter side, find the sides of the field."),
    _q(33, "B", 5, "triangles", "Prove that in a right triangle, the square of the hypotenuse is equal to the sum of the squares of the other two sides."),
    _q(34, "B", 5, "triangles", "Draw a triangle PQR in which QR = 8 cm. ∠Q = 45°, ∠P = 105°. Then construct a triangle similar to ΔPQR. Whose sides are 4/3 times the corresponding sides of ΔPQR."),
    _q(35, "B", 5, "some-applications-of-trigonometry", "A person standing on the bank of a river observes that the angle of elevation of the top of a tree standing on the opposite bank is 60°. When he moves 36 metres away from the bank, he finds the angle of elevation to be 30°. Find the height of the tree and the width of the river."),
    _q(36, "B", 5, "introduction-to-trigonometry", "Prove that cosecA/(cosecA − 1) + cosecA/(cosecA + 1) = 2sec²A."),
    _q(37, "B", 5, "statistics", "Find the median of the following data: Marks obtained: More than 70% — 7, More than 60% — 18, More than 50% — 40, More than 40% — 42, More than 30% — 53, More than 20% — 60 (No. of Students)"),
    _q(38, "B", 5, "surface-areas-and-volumes", "The base radius and height of a right circular cone are 5 meter and 12 meters respectively. Find its volume and total surface area."),
]
_BSEB10_2025_EN = _BSEB10_2025_EN_A + _BSEB10_2025_EN_B
_BSEB10_2025_HI_A = [
    _q(1, "A", 1, "real-numbers", "निम्नलिखित में कौन परिमेय संख्या है? (a) √7 + √7 (b) √25 + √3 (c) 1/√4 (d) √9 × √3"),
    _q(2, "A", 1, "real-numbers", "यदि m एक पूर्णांक है तो प्रत्येक विषम पूर्णांक का रूप होता है– (a) m + 1 (b) m (c) 2m (d) 2m + 1"),
    _q(3, "A", 1, "real-numbers", "निम्नलिखित में किसका दशमलव प्रसार सांत है? (a) 11/91 (b) 15/23 (c) 17/80 (d) 7/45"),
    _q(4, "A", 1, "real-numbers", "0.87̄ = (a) 87/90 (b) 87/99 (c) 79/90 (d) 79/99"),
    _q(5, "A", 1, "real-numbers", "यदि 540 = 2^x × 3^y × 5^z हो तो x + y − z = (a) 4 (b) 5 (c) 3 (d) 6"),
    _q(6, "A", 1, "real-numbers", "निम्नलिखित में कौन अपरिमेय संख्या है? (a) 2.3̄ (b) √13 × √13 (c) √441 (d) √(10/100)"),
    _q(7, "A", 1, "real-numbers", "यदि m और n दो अभाज्य संख्याएँ हैं तो उनका महत्तम समापवर्तक होगा– (a) 0 (b) 1 (c) 2 (d) 3"),
    _q(8, "A", 1, "real-numbers", "दो संख्याओं का गुणनफल 2366 है और उनका लघुतम समापवर्त्य 182 है, तो महत्तम समापवर्तक होगा– (a) 13 (b) 23 (c) 3 (d) 16"),
    _q(9, "A", 1, "real-numbers", "निम्नलिखित में किसका दशमलव प्रसार असांत है? (a) 11/40 (b) 17/160 (c) 33/200 (d) 13/441"),
    _q(10, "A", 1, "real-numbers", "यदि p = ab³ तथा q = a⁴b, जहाँ p, q धनात्मक पूर्णांक तथा a, b अभाज्य संख्याएँ हैं, तो (p, q) का लघुतम समापवर्त्य है– (a) ab (b) a³b³ (c) a⁴b³ (d) a⁴b⁴"),
    _q(11, "A", 1, "real-numbers", "निम्नलिखित में से कौन-सा युग्म सह-अभाज्य है? (a) (15, 45) (b) (9, 16) (c) (21, 105) (d) (14, 84)"),
    _q(12, "A", 1, "real-numbers", "0.3125 को p/q के रूप में लिखा जा सकता है– (a) 5/8 (b) 5/16 (c) 1/8 (d) 5/4"),
    _q(13, "A", 1, "polynomials", "निम्नलिखित में से कौन-सा बहुपद है? (a) x² + √2x + 1 (b) x + 6/x (c) (1/4)x³ − 3x² + √121 (d) 2x² + √4x"),
    _q(14, "A", 1, "polynomials", "बहुपद (x + 3)²(x³ − 8) का घात है– (a) 2 (b) 5 (c) 6 (d) 4"),
    _q(15, "A", 1, "polynomials", "बहुपद 2x² − 6 के शून्यक हैं– (a) (√3, −√3) (b) (√3, √3) (c) (−√3, −√3) (d) (3, −3)"),
    _q(16, "A", 1, "polynomials", "बहुपद p(x) = 2x² − 8x − 12, तो p(2) का मान है– (a) 20 (b) −20 (c) 36 (d) −28"),
    _q(17, "A", 1, "polynomials", "यदि बहुपद 3y² + 7y − K के शून्यक एक दूसरे के व्युत्क्रम हों, तो K का मान होगा– (a) 1/3 (b) −1/3 (c) 3 (d) −3"),
    _q(18, "A", 1, "polynomials", "शून्यक −2, −5 वाले बहुपदों की संख्या होगी– (a) 2 (b) 3 (c) 5 (d) अनगिनत"),
    _q(19, "A", 1, "polynomials", "यदि बहुपद p(x) = 5x² + 7x − 12, के शून्यक α और β हों, तो 5(α + β) का मान है– (a) −7 (b) 7 (c) 35 (d) 60"),
    _q(20, "A", 1, "polynomials", "यदि α, β, γ त्रिघात बहुपद ax³ + bx² + cx + d के शून्यक हों, तो α·β·γ का मान होगा (a) c/a (b) −c/a (c) b/a (d) −d/a"),
    _q(21, "A", 1, "pair-of-linear-equations", "यदि रेखाएँ 5x + py = 6 और 15x + 9y = 12 समान्तर हैं, तो p का मान होगा (a) 3 (b) 1/3 (c) 2 (d) 9"),
    _q(22, "A", 1, "pair-of-linear-equations", "यदि दो चरों में दो रैखिक समीकरणों के आलेख प्रतिच्छेदी रेखाएँ हों, तो हलों की संख्या होगी– (a) कोई हल नहीं (b) सिर्फ एक (c) अनन्त हल (d) इनमें से कोई नहीं"),
    _q(23, "A", 1, "pair-of-linear-equations", "यदि 5x − 8y = 0 तथा 10x − 18y = 0 तो x तथा y के मान हैं– (a) x = 5, y = 0 (b) x = 0, y = 8 (c) x = 0, y = 0 (d) x = 1, y = 1"),
    _q(24, "A", 1, "quadratic-equations", "यदि समीकरण ax² + bx + c = 0, a ≠ 0, का मूल समान हो, तो c = (a) −b²/(4a) (b) b²/(4a) (c) b/(2a) (d) −b/(2a)"),
    _q(25, "A", 1, "quadratic-equations", "निम्नलिखित में से कौन सा द्विघात समीकरण नहीं है? (a) (x + 2)² = 3(x² − 4) (b) 4x − x² = x² + 7 (c) (√2x − 3)² = 2x² + 4 (d) (x − 1)² = 3x² − 2x + 4"),
    _q(26, "A", 1, "quadratic-equations", "यदि द्विघात समीकरण x² − 7x + 12 = 0 का एक मूल 3 हो, तो इसका दूसरा मूल होगा– (a) −3 (b) 4 (c) −4 (d) 2"),
    _q(27, "A", 1, "quadratic-equations", "यदि द्विघात समीकरण x² + px + q = 0 के मूल p तथा q हों, तो p + q = (a) 1 (b) −1 (c) 2 (d) −2"),
    _q(28, "A", 1, "quadratic-equations", "द्विघात समीकरण 3x² − 13x + 10 = 0 का विविक्तकर है– (a) 49 (b) −49 (c) 13 (d) 169"),
    _q(29, "A", 1, "quadratic-equations", "द्विघात समीकरण x(2x + 5) = 0 के मूलों का गुणनफल है– (a) 5/2 (b) 0 (c) −5/2 (d) 2/5"),
    _q(30, "A", 1, "arithmetic-progressions", "निम्नलिखित में कौन-सा समांतर श्रेढ़ी में है? (a) 0.2, 0.22, 0.222, 0.2222, … (b) √7, √28, √63, √112, … (c) 2, 4, 8, 16, … (d) 1, 1/2, 3/2, 2, …"),
    _q(31, "A", 1, "arithmetic-progressions", "समांतर श्रेढ़ी 12, 10, 8, … का कौन-सा पद 0 है? (a) 7वाँ (b) 8वाँ (c) 9वाँ (d) 10वाँ"),
    _q(32, "A", 1, "arithmetic-progressions", "समांतर श्रेढ़ी −5, −1, 3, 7, … का सार्वअंतर है– (a) 4 (b) −4 (c) 3 (d) −6"),
    _q(33, "A", 1, "arithmetic-progressions", "यदि समांतर श्रेढ़ी का पहला पद 'a' और सार्वअंतर 'd' है, तो प्रथम n पदों का योगफल होगा– (a) n{2a + (n − 1) × d} (b) n(n + 1)/2 (c) (n/2){2a + (n − 1) × d} (d) (1/2){a + (n − 1)d}"),
    _q(34, "A", 1, "arithmetic-progressions", "यदि समांतर श्रेढ़ी का n वाँ पद t_n = 3 − 4n तो t_5 = (a) −17 (b) 17 (c) 20 (d) −20"),
    _q(35, "A", 1, "arithmetic-progressions", "यदि समांतर श्रेढ़ी का सामान्य पद (17 − 5n) है, तो इसका सार्वअंतर होगा– (a) 5 (b) −5 (c) 12 (d) 0"),
    _q(36, "A", 1, "arithmetic-progressions", "प्रथम n विषम प्राकृत संख्याओं का योगफल है– (a) n² − 1 (b) n + 1 (c) 2n − 1 (d) n²"),
    _q(37, "A", 1, "arithmetic-progressions", "यदि 18, x, y, −3 समांतर श्रेढ़ी में हैं तो x + y = (a) 7 (b) 13 (c) 21 (d) 15"),
    _q(38, "A", 1, "introduction-to-trigonometry", "यदि A तथा B पूरक कोण हैं, तो (a) sinB = sinB (b) secA = cosecB (c) cotA = cotB (d) tanA = tanB"),
    _q(39, "A", 1, "introduction-to-trigonometry", "cos(90° − ϕ) = (a) sinϕ (b) cosϕ (c) −sinϕ (d) −cosϕ"),
    _q(40, "A", 1, "introduction-to-trigonometry", "cos²27° − sin²63° = (a) −1 (b) 0 (c) 1 (d) 1/2"),
    _q(41, "A", 1, "introduction-to-trigonometry", "sin2θ = 2sinθ सत्य है जब θ = (a) 60° (b) 45° (c) 30° (d) 0°"),
    _q(42, "A", 1, "introduction-to-trigonometry", "यदि sinθ = 4/5 तो tan θ = (a) 5/4 (b) 3/4 (c) 4/3 (d) 4/5"),
    _q(43, "A", 1, "introduction-to-trigonometry", "यदि tanθ = 1/√7 तो sec²θ − tan²θ = (a) 2√2/7 (b) 2√2 (c) √7 (d) 1"),
    _q(44, "A", 1, "introduction-to-trigonometry", "(1 − tan²45°)/(1 + tan²45°) = (a) 0 (b) 1 (c) 2 (d) 1/2"),
    _q(45, "A", 1, "introduction-to-trigonometry", "3cot²60° = (a) 1/3 (b) 1 (c) 3 (d) √3"),
    _q(46, "A", 1, "introduction-to-trigonometry", "cos1°·cos2°·cos3° … cos180° = (a) 1 (b) −1 (c) 0 (d) −1/2"),
    _q(47, "A", 1, "introduction-to-trigonometry", "2 − 2cosec²A = (a) −cot²A (b) cot²A (c) 2cot²A (d) −2cot²A"),
    _q(48, "A", 1, "introduction-to-trigonometry", "यदि asinx = 1 और bcosx = 1 तो cotx = (a) 1 (b) a/b (c) b/a (d) 1/(ab)"),
    _q(49, "A", 1, "introduction-to-trigonometry", "sin²45° + cos²45° − 1 = (a) 0 (b) 1/2 (c) 1 (d) −1"),
    _q(50, "A", 1, "introduction-to-trigonometry", "−tan²A + 1/(1 − sin²A) = (a) 0 (b) 1 (c) −1 (d) 2tan²A"),
]
_BSEB10_2025_HI_B = [
    _q(51, "A", 1, "introduction-to-trigonometry", "(cos75°/sin15°)² − (sin15°/cos75°)² = (a) 1 (b) 2 (c) 0 (d) 4"),
    _q(52, "A", 1, "introduction-to-trigonometry", "(cos60°/sin60°) × tan60° = (a) 0 (b) 1 (c) √3 (d) 2"),
    _q(53, "A", 1, "introduction-to-trigonometry", "यदि cosecϕ − cotϕ = y तो cotϕ = (a) (1 − y²)/(2y) (b) (y² − 1)/(2y) (c) (1 − y²)/2 (d) (1 − y²)/y"),
    _q(54, "A", 1, "introduction-to-trigonometry", "cosec30° = (a) sin30° (b) sec60° (c) cosec60° (d) sec30°"),
    _q(55, "A", 1, "introduction-to-trigonometry", "यदि 2cos3θ = 1 तो θ = (a) 10° (b) 20° (c) 30° (d) 60°"),
    _q(56, "A", 1, "introduction-to-trigonometry", "यदि sinB = a/b तो cosB = (a) √(b² − a²)/b (b) b/√(b² − a²) (c) b/a (d) a/√(b² − a²)"),
    _q(57, "A", 1, "introduction-to-trigonometry", "यदि tanA + cotA = 2 तो tan²A + cot²A = (a) 0 (b) 1 (c) 2 (d) 4"),
    _q(58, "A", 1, "coordinate-geometry", "किस चतुर्थांश में भुज और कोटि दोनों ऋणात्मक होते हैं? (a) प्रथम (b) द्वितीय (c) तृतीय (d) चतुर्थ"),
    _q(59, "A", 1, "coordinate-geometry", "बिन्दु A(8, 0) तथा B(−6, 2) के बीच की दूरी है– (a) 2√10 इकाई (b) 10√2 इकाई (c) 10 इकाई (d) 16 इकाई"),
    _q(60, "A", 1, "coordinate-geometry", "x-अक्ष और y-अक्ष का प्रतिच्छेदन बिन्दु कहलाता है– (a) केन्द्रक (b) बिन्दु (c) लम्बकेन्द्र (d) परिकेन्द्र"),
    _q(61, "A", 1, "coordinate-geometry", "बिन्दुओं P(4, −5) तथा Q(8, 7) को जोड़ने वाले रेखाखंड के मध्य-बिन्दु के निर्देशांक हैं– (a) (2, 6) (b) (6, −1) (c) (6, 1) (d) (−2, −6)"),
    _q(62, "A", 1, "coordinate-geometry", "बिन्दु R(−x, y) की मूलबिन्दु से दूरी है– (a) √(x² − y²) इकाई (b) √(x² + y²) इकाई (c) (x² + y²) इकाई (d) (x + y) इकाई"),
    _q(63, "A", 1, "coordinate-geometry", "यदि बिन्दु (1, 2), (−5, 6) तथा (a, −2) संरेख हों, तो a = (a) 7 (b) −7 (c) 6 (d) 2"),
    _q(64, "A", 1, "coordinate-geometry", "रेखा y = 7 का आलेख निम्नलिखित में से किस बिन्दु से गुजरता है? (a) (7, 3) (b) (7, −6) (c) (5, 7) (d) (7, 1)"),
    _q(65, "A", 1, "coordinate-geometry", "बिन्दु P(4, 6) की y-अक्ष से दूरी है– (a) 6 इकाई (b) 4 इकाई (c) 2 इकाई (d) 10 इकाई"),
    _q(66, "A", 1, "coordinate-geometry", "बिन्दुओं A(a, b) तथा B(c, d) को जोड़ने वाले रेखाखंड AB को λ : 1 के अनुपात में आंतरिक रूप से विभाजित करने वाले बिन्दु का y-निर्देशांक है– (a) (λd + b)/(λ + 1) (b) (λc + a)/(λ + 1) (c) (λb + d)/(λ + 1) (d) (λa + c)/(λ + 1)"),
    _q(67, "A", 1, "coordinate-geometry", "किसी वृत्त के व्यास के सिरों के निर्देशांक P(8, −6) तथा Q(−8, 6) हैं, तो उसके केन्द्र के निर्देशांक हैं– (a) (4, −3) (b) (−4, 3) (c) (1, 1) (d) (0, 0)"),
    _q(68, "A", 1, "coordinate-geometry", "किसी त्रिभुज का केन्द्रक (4, 0) है तथा उसके दो शीर्ष (3, 4) तथा (5, −6) हैं, तो तीसरा शीर्ष है– (a) (2, 4) (b) (4, 2) (c) (0, 2) (d) (2, 0)"),
    _q(69, "A", 1, "coordinate-geometry", "बिन्दु (−5/2, 4) किस चतुर्थांश में स्थित है? (a) प्रथम (b) द्वितीय (c) तृतीय (d) चतुर्थ"),
    _q(70, "A", 1, "coordinate-geometry", "x-अक्ष पर स्थित सभी बिन्दुओं की कोटि होती है– (a) 0 (b) 1 (c) 2 (d) −1"),
    _q(71, "A", 1, "triangles", "यदि ΔABC तथा ΔPQR समरूप हों तथा ∠A = 42°, ∠Q = 84° हो, तो ∠C = (a) 48° (b) 54° (c) 96° (d) 42°"),
    _q(72, "A", 1, "triangles", "ΔPQR में यदि PR² = PQ² + QR² तो ∠Q = (a) 45° (b) 60° (c) 75° (d) 90°"),
    _q(73, "A", 1, "triangles", "यदि ΔABC एक समबाहु त्रिभुज है तथा AD ⊥ BC, तो AD² = (a) 2DC² (b) (3/2)DC² (c) 4DC² (d) 3CD²"),
    _q(74, "A", 1, "triangles", "ΔABC में, D और E क्रमशः भुजाओं AB और AC पर स्थित बिन्दु हैं इस प्रकार कि DE ∥ BC। यदि AD/DB = 4/5 और AC = 18 सेमी० है, तो AE = (a) 8 सेमी० (b) 9 सेमी० (c) 12 सेमी० (d) 4 सेमी०"),
    _q(75, "A", 1, "triangles", "समद्विबाहु समकोण त्रिभुज में प्रत्येक न्यूनकोण की माप होगी– (a) 60° (b) 90° (c) 45° (d) 30°"),
    _q(76, "A", 1, "triangles", "दो समरूप त्रिभुजों की संगत ऊँचाइयाँ 7 सेमी० तथा 10 सेमी० हैं, तो उनके क्षेत्रफलों का अनुपात होगा– (a) 49 : 100 (b) 100 : 49 (c) √10 : √7 (d) √7 : √10"),
    _q(77, "A", 1, "circles", "4.5 सेमी० त्रिज्या वाले वृत्त पर खींची गई दो समान्तर स्पर्श रेखाओं के बीच की दूरी है– (a) 4.5 सेमी० (b) 1.5 सेमी० (c) 9 सेमी० (d) 6 सेमी०"),
    _q(78, "A", 1, "circles", "किसी बाह्य बिन्दु से वृत्त पर कितनी स्पर्श रेखाएँ खींची जा सकती हैं? (a) दो (b) एक (c) तीन (d) अनगिनत"),
    _q(79, "A", 1, "circles", "यदि PA और PB केन्द्र O वाले वृत्त की दो स्पर्श रेखाएँ हैं तथा ∠APB = 50° है तो ∠AOB = (a) 50° (b) 25° (c) 90° (d) 130°"),
    _q(80, "A", 1, "circles", "दी गई आकृति में बिन्दु O वृत्त का केन्द्र है और ∠AOB = 30° है तो ∠OBA का मान है– (a) 30° (b) 60° (c) 75° (d) 90°"),
    _q(81, "A", 1, "circles", "8 सेमी० त्रिज्या वाले वृत्त के केन्द्र से 17 सेमी० दूर स्थित बिन्दु से खींची गई स्पर्श रेखा की लम्बाई है– (a) 15 सेमी० (b) 8 सेमी० (c) √353 सेमी० (d) 25 सेमी०"),
    _q(82, "A", 1, "surface-areas-and-volumes", "किसी घन के विकर्ण की लम्बाई 5√3 सेमी० है, तो उसका सम्पूर्ण पृष्ठ क्षेत्रफल होगा– (a) 125 सेमी² (b) 150 सेमी² (c) 75 सेमी² (d) 250 सेमी²"),
    _q(83, "A", 1, "surface-areas-and-volumes", "यदि एक बेलन और शंकु के त्रिज्या और ऊँचाई समान हों, तो उनके आयतनों का अनुपात होगा– (a) 1 : 3 (b) 3 : 1 (c) 3 : 4 (d) 2 : 3"),
    _q(84, "A", 1, "surface-areas-and-volumes", "सुराही का संयोजन है– (a) गोला तथा बेलन (b) बेलन तथा शंकु (c) दो अर्धगोलें (d) अर्धगोला तथा बेलन"),
    _q(85, "A", 1, "areas-related-to-circles", "एक घड़ी के मिनट वाली सूई द्वारा 45 मिनट में बनाया गया कोण है– (a) 180° (b) 270° (c) 90° (d) 135°"),
    _q(86, "A", 1, "areas-related-to-circles", "10 सेमी० त्रिज्या वाले अर्धवृत्त की कुल परिमिति होगी– (a) (π + 2)10 सेमी० (b) (π + 1)10 सेमी० (c) 10π सेमी० (d) (π + 5)10 सेमी०"),
    _q(87, "A", 1, "surface-areas-and-volumes", "6 सेमी० व्यास के एक गोले द्वारा विस्थापित हवा का आयतन है– (a) 36 घन सेमी० (b) 108π घन सेमी० (c) 36π घन सेमी० (d) 144π घन सेमी०"),
    _q(88, "A", 1, "areas-related-to-circles", "p त्रिज्या वाले वृत्त में कोण θ⁰ के त्रिज्यखंड का क्षेत्रफल है– (a) (πp²θ)/360 वर्ग इकाई (b) (πp²θ)/180 वर्ग इकाई (c) (πpθ)/360 वर्ग इकाई (d) (p²θ)/360 वर्ग इकाई"),
    _q(89, "A", 1, "surface-areas-and-volumes", "यदि किसी अर्धगोले के सम्पूर्ण पृष्ठ का क्षेत्रफल 462 सेमी²० हो, तो उसकी त्रिज्या होगी– (a) 14 सेमी० (b) 7 सेमी० (c) 6 सेमी० (d) 3.5 सेमी०"),
    _q(90, "A", 1, "triangles", "एक समबाहु त्रिभुज का क्षेत्रफल 81√3 सेमी²० है, तो इसकी भुजा है– (a) 9√3 सेमी० (b) 9 सेमी० (c) 3√3 सेमी० (d) 18 सेमी०"),
    _q(91, "A", 1, "probability", "तीन पासों की उछाल में संभव परिणामों की संख्या होगी – (a) 216 (b) 136 (c) 128 (d) 18"),
    _q(92, "A", 1, "probability", "यदि कोई घटना घटित नहीं हो सकती है तो उसकी प्रायिकता होगी– (a) 0 (b) 1/2 (c) 1 (d) 1/3"),
    _q(93, "A", 1, "probability", "एक पासा एक बार फेंका जाता है। अभाज्य संख्या आने की प्रायिकता होगी– (a) 1/6 (b) 1/2 (c) 2/3 (d) 1/3"),
    _q(94, "A", 1, "probability", "अच्छी प्रकार से फेंटी गई एक ताश की गड्डी में से एक पत्ता यादृच्छया निकाला जाता है, तो इसके काला रंग का रानी होने की प्रायिकता है– (a) 2/13 (b) 1/26 (c) 1/13 (d) 3/26"),
    _q(95, "A", 1, "probability", "दो सिक्कों की उछाल में एक भी शीर्ष नहीं आने की प्रायिकता होगी– (a) 3/4 (b) 1/3 (c) 1/2 (d) 1/4"),
    _q(96, "A", 1, "statistics", "23, 20, 22, 37, 24, 23, 19, 22, 17, 23 का बहुलक है– (a) 23 (b) 22 (c) 19 (d) 37"),
    _q(97, "A", 1, "statistics", "यदि पाँच आँकड़ों x, x + 1, x + 2, x + 3 तथा x + 4 का माध्य 14 हो तो x = (a) 10 (b) 14 (c) 12 (d) 11"),
    _q(98, "A", 1, "statistics", "निम्नलिखित में से कौन केन्द्रीय प्रवृत्ति की माप नहीं है? (a) परिसर (b) बहुलक (c) माध्य (d) माध्यिका"),
    _q(99, "A", 1, "statistics", "प्रथम 8 अभाज्य संख्याओं का माध्यिका है– (a) 13 (b) 11 (c) 9 (d) 7"),
    _q(100, "A", 1, "statistics", "निम्नलिखित वितरण के लिए: वर्ग-अंतराल: 0-10, 10-20, 20-30, 30-40, 40-50; बारंबारता: 8, 12, 20, 6, 4। बहुलक वर्ग का उच्च-सीमा है– (a) 20 (b) 30 (c) 25 (d) 50"),
    _q(1, "B", 2, "real-numbers", "सिद्ध करें कि 2√3 एक अपरिमेय संख्या है।"),
    _q(2, "B", 2, "real-numbers", "संख्या 12, 144 और 240 का लघुतम समापवर्त्य अभाज्य गुणनखंड विधि से ज्ञात करें।"),
    _q(3, "B", 2, "real-numbers", "यूक्लिड के विभाजन एल्गोरिथ्म का उपयोग कर, 135 और 225 का महत्तम समापवर्तक ज्ञात करें।"),
    _q(4, "B", 2, "polynomials", "द्विघात बहुपद 6y² − 3 − 7y के शून्यकों को ज्ञात करें।"),
    _q(5, "B", 2, "polynomials", "यदि p(x) = x² − 18x + 81 तथा q(x) = (x − 9) तो p(x)/q(x) का घात ज्ञात करें।"),
    _q(6, "B", 2, "polynomials", "यदि बहुपद f(x) = 5x² − 7x + 1 के शून्यांक α तथा β हैं। α² + β² का मान ज्ञात करें।"),
    _q(7, "B", 2, "pair-of-linear-equations", "समीकरण युग्म x − 2y = 0 तथा 3x + 4y − 20 = 0 को हल करें।"),
    _q(8, "B", 2, "quadratic-equations", "द्विघात समीकरण 3y² − 2√6y + 2 = 0 का विविक्तकर ज्ञात करें एवं फिर की प्रकृति ज्ञात बताएँ।"),
    _q(9, "B", 2, "quadratic-equations", "द्विघात सूत्र का उपयोग कर समीकरण x² + 7x − 60 = 0 का मूल निकालें।"),
    _q(10, "B", 2, "arithmetic-progressions", "क्या संख्याओं की सूची 5, 11, 17, 23, …. का कोई पद 301 है?"),
    _q(11, "B", 2, "arithmetic-progressions", "किसी समांतर श्रेढ़ी का 17 वाँ पद उसके 10 वें पद से 14 अधिक है। इसका सार्वअंतर ज्ञात करें।"),
    _q(12, "B", 2, "arithmetic-progressions", "योगफल निकालें: 7 + 10(1/2) + 14 + ⋯ + 84."),
    _q(13, "B", 2, "arithmetic-progressions", "0 और 50 के बीच की विषम संख्याओं का योग ज्ञात करें।"),
    _q(14, "B", 2, "introduction-to-trigonometry", "यदि 5cotA = 3 तो (5sinA − 3cosA)/(4sinA + 3cosA) का मान निकालें।"),
    _q(15, "B", 2, "introduction-to-trigonometry", "सिद्ध करें कि (sin⁴θ − cos⁴θ + 1)cosec²θ = 2."),
    _q(16, "B", 2, "introduction-to-trigonometry", "(6cos²60° + 4sin²30° − cot²45°)/(sin²60° + cos²60°) का मान निकालें।"),
    _q(17, "B", 2, "introduction-to-trigonometry", "sin35°·cos55° + cos35°sin55° का मान निकालें।"),
    _q(18, "B", 2, "coordinate-geometry", "उस त्रिभुज का क्षेत्रफल ज्ञात करें जिसके शीर्ष (4, −3), (−9, 7) और (8, 8) हैं।"),
    _q(19, "B", 2, "coordinate-geometry", "बिन्दुओं (5, −6) और (−1, −4) को जोड़ने वाले रेखाखंड को x-अक्ष किस अनुपात में विभाजित करती है?"),
    _q(20, "B", 2, "coordinate-geometry", "x का मान ज्ञात करें, जिसके लिए बिन्दु P(x, 2) और Q(3, 4) के बीच की दूरी 8 इकाई है।"),
    _q(21, "B", 2, "coordinate-geometry", "बिन्दुओं (8, 10) और (4, 6) को मिलाने वाले रेखाखंड के मध्य बिन्दु की दूरी बिन्दु (2, 4) से ज्ञात करें।"),
    _q(22, "B", 2, "triangles", "यदि ΔABC, ∠B = ∠C और बिन्दु D तथा E क्रमशः भुजाओं AB तथा AC पर इस प्रकार हैं कि BD = CE तो सिद्ध करें कि DE ∥ BC."),
    _q(23, "B", 2, "triangles", "दी गई आकृति में ST ∥ QR, यदि ST = 3 सेमी०, QR = 6 सेमी० तथा क्षे०(ΔPST) = 15 सेमी²०, तो ΔPQR का क्षेत्रफल ज्ञात करें।"),
    _q(24, "B", 2, "circles", "किसी वृत्त के केन्द्र से 13 सेमी० की दूरी पर किसी बिन्दु P से खींची गई स्पर्श रेखा की लम्बाई 12 सेमी० है। वृत्त की त्रिज्या ज्ञात करें।"),
    _q(25, "B", 2, "pair-of-linear-equations", "किसी भिन्न के अंश और हर में 2 जोड़ देने पर वह 5 के बराबर हो जाता है और यदि उसके अंश और हर में से 1 घटा दें तो वह 7 के बराबर हो जाता है इन कथनों के लिए समीकरण लिखें"),
    _q(26, "B", 2, "statistics", "निम्नलिखित बंटन का माध्य ज्ञात करें: वर्ग-अंतराल: 0-10, 10-20, 20-30, 30-40, 40-50; बारंबारता: 8, 15, 12, 16, 9"),
    _q(27, "B", 2, "areas-related-to-circles", "यदि 14 सेमी० त्रिज्या वाले वृत्त का एक चाप केन्द्र पर 120⁰ का कोण अंतरित करता है, तो चाप की लम्बाई ज्ञात करें।"),
    _q(28, "B", 2, "surface-areas-and-volumes", "यदि किसी लंबवृत्तीय बेलन की ऊँचाई उसके आधार की त्रिज्या की दुगुनी है एवं उसके वक्र पृष्ठ का क्षेत्रफल 616 सेमी²० है, तो उसके आधार की त्रिज्या निकालें।"),
    _q(29, "B", 2, "probability", "यदि तीन सिक्कों को एक साथ उछाला जाता है तो तीनों पर एक ही परिणाम आने की प्रायिकता ज्ञात करें।"),
    _q(30, "B", 2, "probability", "यदि दो पासों को एक साथ फेंकने पर दोनों पर आने वाले अंको का अंतर 3 आने की प्रायिकता निकालें।"),
    _q(31, "B", 5, "pair-of-linear-equations", "ग्राफीय विधि से रैखिक समीकरण युग्म x − y + 1 = 0 तथा 2x + 3y − 12 = 0 को हल करें।"),
    _q(32, "B", 5, "quadratic-equations", "एक आयताकार खेत का विकर्ण उसकी छोटी भुजा से 60 मीटर अधिक लंबा है। यदि बड़ी भुजा छोटी भुजा से 30 मीटर अधिक हो, तो खेत की भुजाएँ ज्ञात करें।"),
    _q(33, "B", 5, "triangles", "सिद्ध करें कि एक समकोण त्रिभुज में कर्ण का वर्ग अन्य दो भुजाओं के वर्गों के योगफल के बराबर होता है।"),
    _q(34, "B", 5, "triangles", "एक त्रिभुज PQR बनाएँ जिसमें QR = 8 सेमी०। ∠Q = 45°, ∠P = 105° है, फिर ΔPQR के समरूप एक त्रिभुज का रचना करें जिसकी भुजाएँ ΔPQR की संगत भुजाओं की 4/3 गुनी हों।"),
    _q(35, "B", 5, "some-applications-of-trigonometry", "एक व्यक्ति, जो नदी के एक किनारे पर खड़ा है नदी के दूसरे किनारे पर स्थित एक पेड़ के शिखर का उन्नयन कोण 60° पाता है। जब वह व्यक्ति किनारे से 36 मीटर पीछे हट जाता है, तो वह उन्नयन कोण 30° का हो जाता है। पेड़ की ऊँचाई तथा नदी की चौड़ाई ज्ञात करें।"),
    _q(36, "B", 5, "introduction-to-trigonometry", "सिद्ध करें कि cosecA/(cosecA − 1) + cosecA/(cosecA + 1) = 2sec²A."),
    _q(37, "B", 5, "statistics", "निम्नलिखित आँकड़े का माध्यिका ज्ञात करें: प्राप्तांक: 70% से अधिक — 7, 60% से अधिक — 18, 50% से अधिक — 40, 40% से अधिक — 42, 30% से अधिक — 53, 20% से अधिक — 60 (छात्र संख्या)"),
    _q(38, "B", 5, "surface-areas-and-volumes", "एक लंब वृत्तीय शंकु के आधार की त्रिज्या और ऊँचाई क्रमशः 5 मीटर तथा 12 मीटर है। उस शंकु का आयतन एवं कुल पृष्ठीय क्षेत्रफल ज्ञात करें।"),
]
_BSEB10_2025_HI = _BSEB10_2025_HI_A + _BSEB10_2025_HI_B

# Wave 66: MP Board (MPBSE) Class 12 Higher Mathematics 2025,
# Higher Secondary Examination (Main), code 202504, Set B.
# One bilingual booklet "(Hindi & English Versions)" — the
# booklet itself states the Hindi version is final in case of
# discrepancy. 23 questions, Maximum Marks 80, Time 3 Hours,
# no printed sections: Q1-5 are objective bundles (Q1 true/
# false 6, Q2 match-the-columns 7, Q3 one-word 7, Q4 MCQ 6,
# Q5 fill-in-the-blanks 6), Q6-15 carry 2 marks, Q16-19
# carry 3 marks and Q20-23 carry 4 marks; Q6 onwards every
# question has an internal choice (OR). Both texts were read
# from the page images of the AglaSem scan.
_MP12_2025_EN = [
    _q(1, "A", 6, "relations-and-functions", "Write True or False: (i) If a function f is invertible, then f must be one-one and onto. (ii) If A' = −A, then A is a symmetric matrix. (iii) Inverse of a square matrix, if it exists, is unique. (iv) The differential coefficient of sec²x with respect to x is tan x. (v) If A is an invertible matrix of order 2, then det (A⁻¹) = det (A). (vi) If A is a singular matrix, then |A| = 0."),
    _q(2, "A", 7, "integrals", "Match the correct pair: Column 'A': (i) ∫ dx/√(x² + a²) (ii) ∫√(x² + a²) dx (iii) ∫tan x dx (iv) ∫cot x dx (v) ∫√(x² − 9) dx (vi) ∫ (1/√(x² − 9)) dx (vii) simplest form of tan(1/√(x² − 1)), x > 1. Column 'B': (a) log|sin x| + c (b) (x/2)√(x² − 9) − (9/2)log|x + √(x² − 9)| + c (c) cosec⁻¹x (d) log|x + √(x² − 9)| + c (e) (x/2)√(x² + a²) + (a²/2)log|x + √(x² + a²)| + c (f) log|x + √(x² + a²)| + c (g) log|sec x| + c"),
    _q(3, "A", 7, "relations-and-functions", "Give answer in one word / sentence each: (i) Write the minimum value of the function f given by f(x) = |x|, x ∈ R. (ii) If P(B) = 0.5 and P(A ∩ B) = 0.32, then write the value of P(A/B). (iii) Write definition of scalar matrix. (iv) Write the value of (î × ĵ)·k̂ + (ĵ × k̂)·î. (v) If A = [1 2; 3 4], then write the value of |adj(A)|. (vi) Write the range of principal value of tan⁻¹x. (vii) Find the intervals in which the function f given by f(x) = x² − 2x is increasing."),
    _q(4, "A", 6, "relations-and-functions", "Choose and write the correct option: (i) If f : R → R be defined as f(x) = 3x, then (a) f is one-one onto. (b) f is many one onto. (c) f is one-one but not onto. (d) f is neither one-one nor onto. (ii) The principal value of cos⁻¹(−1/√2) is: (a) π/3 (b) 3π/4 (c) 2π/3 (d) −π/3 (iii) If A = [cosα −sinα; sinα cosα] and A + A' = I, then the value of α is: (a) π/6 (b) π (c) 3π/2 (d) π/3 (iv) If |1 x; x 1| = |0 2; 1 2|, then the value of x is: (a) 0 (b) ±1 (c) ±√3 (d) ±√2 (v) If a⃗ and b⃗ are two non-zero vectors and a⃗·b⃗ = 0, then angle between these two vectors will be: (a) θ = π/2 (b) θ = 0 (c) θ = π (d) θ = π/4 (vi) The probability of obtaining an odd prime number on each die, when a pair of dice is rolled, is: (a) 0 (b) 1/3 (c) 1/18 (d) 1/36"),
    _q(5, "A", 6, "continuity-and-differentiability", "Fill in the blanks: (i) If y = log(log x), x > 1, then dy/dx = ______ (ii) The rate of change of the area of a circle with respect to its radius at r = 6 cm is ______. (iii) If −1 ≤ x ≤ 1, then sin(sin⁻¹x) = ______. (iv) If l, m, n are the direction cosine of a line, then l² + m² + n² = ______. (v) If A = {1, 2, 3}, then number of equivalence relation containing (1, 2) is ______. (vi) The vector sum of the three sides of a triangle taken in order is ______."),
    _q(6, "A", 2, "differential-equations", "Verify that the function y = e^(−3x) is a solution of the differential equation d²y/dx² + dy/dx − 6y = 0. OR Find the general solution of the differential equation dy/dx = −4xy²."),
    _q(7, "A", 2, "vector-algebra", "Find the unit vector in the direction of vector PQ, where P and Q are the points (1, 2, 3) and (4, 5, 6) respectively. OR Find the projection of the vector a⃗ = 2î + 3ĵ + 2k̂ on the vector b⃗ = î + 2ĵ + k̂."),
    _q(8, "A", 2, "vector-algebra", "Find the angle between the vectors a⃗ = î + ĵ − k̂ and b⃗ = î − ĵ + k̂. OR Find |x⃗|, if for a unit vector a⃗, (x⃗ − a⃗)·(x⃗ + a⃗) = 12."),
    _q(9, "A", 2, "three-dimensional-geometry", "Find the vector equation of the line passing through the point (5, 2, −4) and which is parallel to the vector 3î + 2ĵ − 8k̂. OR Show that the lines (x − 5)/7 = (y + 2)/(−5) = z/1 and x/1 = y/2 = z/3 are perpendicular to each other."),
    _q(10, "A", 2, "relations-and-functions", "Show that the relation R in the set {1, 2, 3} given by R = {(1, 2), (2, 1)} is symmetric but neither reflexive nor transitive. OR Let A = {1, 2, 3}, B = {4, 5, 6, 7} and let f = {(1, 4), (2, 5), (3, 6)} be a function from A to B. Show that f is one-one."),
    _q(11, "A", 2, "inverse-trigonometric-functions", "Prove that 3cos⁻¹x = cos⁻¹(4x³ − 3x), x ∈ [1/2, 1]. OR Find the value of tan⁻¹(√3) − sec⁻¹(−2)."),
    _q(12, "A", 2, "matrices", "If x[2; 3] + y[−1; 1] = [10; 5], find the value of x and y. OR Show that the matrix A = [0 1 −1; −1 0 1; 1 −1 0] is a skew symmetric matrix."),
    _q(13, "A", 2, "matrices", "Find adjoint of the matrix A = [2 3; 1 4]. OR Find the area of the triangle whose vertices are (1, 0), (6, 0) and (4, 3) using determinants."),
    _q(14, "A", 2, "continuity-and-differentiability", "If 2x + 3y = sin y, then find dy/dx. OR If x = acosθ, y = bsinθ, then find dy/dx."),
    _q(15, "A", 2, "integrals", "Find the value of ∫cos²x dx. OR Evaluate ∫₀^(π/2) (sin⁴x)/(sin⁴x + cos⁴x) dx."),
    _q(16, "A", 3, "linear-programming", "Maximise Z = 3x + 4y subject to the constraints: x + y ≤ 4, x ≥ 0, y ≥ 0. OR Minimise Z = −4x + 3y subject to the constraints: x + 2y ≤ 8, 3x + 2y ≤ 12, x ≥ 0, y ≥ 0."),
    _q(17, "A", 3, "probability", "A bag contains 3 red and 3 black balls and another bag contains 4 red and 5 black balls. One of the two bags is selected at random and a ball is drawn from the bag which is found to be red. Find the probability that the ball is drawn from the first bag. OR A die is thrown once. If E is the event 'the number appearing is a multiple of 3' and F be the event 'the number appearing is even', then find whether E and F are independent?"),
    _q(18, "A", 3, "application-of-derivatives", "A stone is dropped into a quiet lake and waves move in circles at a speed of 4 cm/s. At the instant, when the radius of the circular waves is 10 cm, how fast is the enclosed area increasing? OR Find the intervals in which the function f given by f(x) = 4x³ − 6x² − 72x + 30 is (a) increasing (b) decreasing."),
    _q(19, "A", 3, "application-of-integrals", "Using integration find the area enclosed by the circle x² + y² = 16. OR Using integration find the area enclosed by the ellipse x²/4 + y²/9 = 1."),
    _q(20, "A", 4, "differential-equations", "Find the general solution of the differential equation x(dy/dx) + 2y = x² (x ≠ 0). OR Find the general solution of the differential equation (x² − y²)dx + 2xy dy = 0."),
    _q(21, "A", 4, "three-dimensional-geometry", "Find the shortest distance between the lines (x + 1)/7 = (y + 1)/(−6) = (z + 1)/1 and (x − 3)/1 = (y − 5)/(−2) = (z − 7)/1. OR Find the shortest distance between the lines r⃗ = î + 2ĵ + k̂ + λ(î − ĵ + k̂) and r⃗ = 2î − ĵ − k̂ + μ(2î + ĵ + 2k̂)."),
    _q(22, "A", 4, "continuity-and-differentiability", "If y = sin⁻¹x, then show that (1 − x²)(d²y/dx²) − x(dy/dx) = 0. OR Find the values of K so that the function defined by f(x) = {Kcosx/(π − 2x), if x ≠ π/2; 3, if x = π/2} is continuous at x = π/2."),
    _q(23, "A", 4, "integrals", "Evaluate: ∫₀^π (x sinx)/(1 + cos²x) dx. OR Evaluate: ∫ (xe^x)/(1 + x)² dx."),
]
_MP12_2025_HI = [
    _q(1, "A", 6, "relations-and-functions", "सत्य या असत्य लिखिए: (i) यदि एक फलन f व्युत्क्रमणीय है, तो f अनिवार्यतः एकैकी तथा आच्छादक होता है। (ii) यदि A' = −A है, तो A एक सममित आव्यूह है। (iii) किसी वर्ग आव्यूह का व्युत्क्रम आव्यूह, यदि उसका अस्तित्व है तो अद्वितीय होता है। (iv) x के सापेक्ष sec²x का अवकल गुणांक tan x होता है। (v) यदि A कोटि 2 का व्युत्क्रमणीय आव्यूह है, तो det (A⁻¹) = det (A) (vi) यदि A एक अव्युत्क्रमणीय आव्यूह है तब |A| = 0 होता है।"),
    _q(2, "A", 7, "integrals", "सही जोड़ी बनाइये: स्तम्भ 'अ': (i) ∫ dx/√(x² + a²) (ii) ∫√(x² + a²) dx (iii) ∫tan x dx (iv) ∫cot x dx (v) ∫√(x² − 9) dx (vi) ∫ (1/√(x² − 9)) dx (vii) tan(1/√(x² − 1)), x > 1 का सरलतम रूप। स्तम्भ 'ब': (a) log|sin x| + c (b) (x/2)√(x² − 9) − (9/2)log|x + √(x² − 9)| + c (c) cosec⁻¹x (d) log|x + √(x² − 9)| + c (e) (x/2)√(x² + a²) + (a²/2)log|x + √(x² + a²)| + c (f) log|x + √(x² + a²)| + c (g) log|sec x| + c"),
    _q(3, "A", 7, "relations-and-functions", "प्रत्येक का एक शब्द / वाक्य में उत्तर दीजिए: (i) f(x) = |x|, x ∈ R द्वारा प्रदत्त फलन f का निम्नतम मान लिखिए। (ii) यदि P(B) = 0.5 और P(A ∩ B) = 0.32, तो P(A/B) का मान लिखिए। (iii) अदिश आव्यूह की परिभाषा लिखिए। (iv) (î × ĵ)·k̂ + (ĵ × k̂)·î का मान लिखिए। (v) यदि A = [1 2; 3 4], तो |adj(A)| का मान लिखिए। (vi) tan⁻¹x की मुख्य मान शाखा का परिसर लिखिए। (vii) अंतराल ज्ञात कीजिए जिनमें f(x) = x² − 2x से प्रदत्त फलन f वर्धमान है।"),
    _q(4, "A", 6, "relations-and-functions", "सही विकल्प चुनकर लिखिए: (i) यदि फलन f : R → R, f(x) = 3x द्वारा परिभाषित है, तो (a) f एकैकी आच्छादक है। (b) f बहुएक आच्छादक है। (c) f एकैकी है किन्तु आच्छादक नहीं है। (d) f न तो एकैकी है और न ही आच्छादक है। (ii) cos⁻¹(−1/√2) का मुख्य मान है: (a) π/3 (b) 3π/4 (c) 2π/3 (d) −π/3 (iii) यदि A = [cosα −sinα; sinα cosα] तथा A + A' = I, तो α का मान है: (a) π/6 (b) π (c) 3π/2 (d) π/3 (iv) यदि |1 x; x 1| = |0 2; 1 2|, तो x का मान है: (a) 0 (b) ±1 (c) ±√3 (d) ±√2 (v) यदि a⃗ तथा b⃗ दो शून्येतर सदिश हैं तथा a⃗·b⃗ = 0, तब इन दोनों सदिशों के बीच का कोण होगा: (a) θ = π/2 (b) θ = 0 (c) θ = π (d) θ = π/4 (vi) यदि पासों का एक जोड़ा उछाला जाता है तो प्रत्येक पासे पर विषम अभाज्य संख्या प्राप्त करने की प्रायिकता होगी: (a) 0 (b) 1/3 (c) 1/18 (d) 1/36"),
    _q(5, "A", 6, "continuity-and-differentiability", "रिक्त स्थानों की पूर्ति कीजिए: (i) यदि y = log(log x), x > 1, तो dy/dx = ______ (ii) एक वृत्त की त्रिज्या r = 6 cm पर r के सापेक्ष क्षेत्रफल में परिवर्तन की दर ______ है। (iii) यदि −1 ≤ x ≤ 1, तो sin(sin⁻¹x) = ______ (iv) यदि एक रेखा की दिक्-कोसाइन l, m, n हैं, तो l² + m² + n² = ______ (v) यदि A = {1, 2, 3} हो, तो अवयव (1, 2) वाले तुल्यता संबंधों की संख्या ______ है। (vi) त्रिभुज की तीनों भुजाओं को क्रम में लेने पर उनका सदिश योग ______ होता है।"),
    _q(6, "A", 2, "differential-equations", "सत्यापित कीजिए कि फलन y = e^(−3x) अवकल समीकरण d²y/dx² + dy/dx − 6y = 0 का एक हल है। अथवा अवकल समीकरण dy/dx = −4xy² का व्यापक हल ज्ञात कीजिए।"),
    _q(7, "A", 2, "vector-algebra", "सदिश PQ के अनुदिश मात्रक सदिश ज्ञात कीजिए जहाँ बिंदु P और Q क्रमशः (1, 2, 3) और (4, 5, 6) हैं। अथवा सदिश a⃗ = 2î + 3ĵ + 2k̂ का, सदिश b⃗ = î + 2ĵ + k̂ पर प्रक्षेप ज्ञात कीजिए।"),
    _q(8, "A", 2, "vector-algebra", "सदिश a⃗ = î + ĵ − k̂ तथा b⃗ = î − ĵ + k̂ के बीच का कोण ज्ञात कीजिए। अथवा यदि एक मात्रक सदिश a⃗ के लिए (x⃗ − a⃗)·(x⃗ + a⃗) = 12 हो, तो |x⃗| ज्ञात कीजिए।"),
    _q(9, "A", 2, "three-dimensional-geometry", "बिंदु (5, 2, −4) से जाने वाली तथा सदिश 3î + 2ĵ − 8k̂ के समान्तर रेखा का सदिश समीकरण ज्ञात कीजिए। अथवा दिखाएँ कि रेखाएँ (x − 5)/7 = (y + 2)/(−5) = z/1 और x/1 = y/2 = z/3 परस्पर लंब हैं।"),
    _q(10, "A", 2, "relations-and-functions", "सिद्ध कीजिए कि समुच्चय {1, 2, 3} में R = {(1, 2), (2, 1)} द्वारा प्रदत्त संबंध R सममित है किन्तु न तो स्वतुल्य है और न ही संक्रामक है। अथवा मान लीजिए कि A = {1, 2, 3}, B = {4, 5, 6, 7} तथा माना f = {(1, 4), (2, 5), (3, 6)} A से B तक एक फलन है। सिद्ध कीजिए कि f एकैकी है।"),
    _q(11, "A", 2, "inverse-trigonometric-functions", "सिद्ध कीजिए 3cos⁻¹x = cos⁻¹(4x³ − 3x), x ∈ [1/2, 1]। अथवा tan⁻¹(√3) − sec⁻¹(−2) का मान ज्ञात कीजिए।"),
    _q(12, "A", 2, "matrices", "यदि x[2; 3] + y[−1; 1] = [10; 5] है, तो x तथा y के मान ज्ञात कीजिए। अथवा सिद्ध कीजिए कि आव्यूह A = [0 1 −1; −1 0 1; 1 −1 0] एक विषम सममित आव्यूह है।"),
    _q(13, "A", 2, "matrices", "आव्यूह A = [2 3; 1 4] का सहखंडज ज्ञात कीजिए। अथवा सारणिक का प्रयोग करके एक त्रिभुज का क्षेत्रफल ज्ञात कीजिए जिसके शीर्ष (1, 0), (6, 0) और (4, 3) हैं।"),
    _q(14, "A", 2, "continuity-and-differentiability", "यदि 2x + 3y = sin y है, तो dy/dx ज्ञात कीजिए। अथवा यदि x = acosθ, y = bsinθ, तो dy/dx ज्ञात कीजिए।"),
    _q(15, "A", 2, "integrals", "∫cos²x dx का मान ज्ञात कीजिए। अथवा ∫₀^(π/2) (sin⁴x)/(sin⁴x + cos⁴x) dx का मान ज्ञात कीजिए।"),
    _q(16, "A", 3, "linear-programming", "निम्न व्यवरोधों के अंतर्गत Z = 3x + 4y का अधिकतमीकरण कीजिए: x + y ≤ 4, x ≥ 0, y ≥ 0। अथवा निम्न व्यवरोधों के अंतर्गत Z = −4x + 3y का न्यूनतमीकरण कीजिए: x + 2y ≤ 8, 3x + 2y ≤ 12, x ≥ 0, y ≥ 0।"),
    _q(17, "A", 3, "probability", "एक थैले में 3 लाल और 3 काली गेंदें हैं और एक अन्य थैले में 4 लाल और 5 काली गेंदें हैं। दोनों थैलों में से एक को यादृच्छया चुना जाता है और उसमें से एक गेंद निकाली जाती है जो कि लाल है। इस बात की क्या प्रायिकता है कि गेंद पहले थैले से निकाली गई है? अथवा एक पासे को एक बार उछाला जाता है। घटना 'पासे पर प्राप्त संख्या 3 का अपवर्त्य है' को E से और 'पासे पर प्राप्त संख्या सम है' को F से निरूपित किया जाए, तो बताइए क्या घटनाएँ E और F स्वतंत्र हैं?"),
    _q(18, "A", 3, "application-of-derivatives", "एक स्थिर झील में एक पत्थर डाला जाता है और तरंगें वृत्तों में 4 cm/s की गति से चलती हैं। जब वृत्ताकार तरंग की त्रिज्या 10 cm है, तो उस क्षण घिरा हुआ क्षेत्रफल कितनी तेजी से बढ़ रहा है? अथवा वे अंतराल ज्ञात कीजिए जिनमें f(x) = 4x³ − 6x² − 72x + 30 द्वारा प्रदत्त फलन f, (a) वर्धमान (b) ह्रासमान है।"),
    _q(19, "A", 3, "application-of-integrals", "समाकलन के उपयोग से वृत्त x² + y² = 16 से घिरे क्षेत्र का क्षेत्रफल ज्ञात कीजिए। अथवा समाकलन के उपयोग से दीर्घवृत्त x²/4 + y²/9 = 1 से घिरे क्षेत्र का क्षेत्रफल ज्ञात कीजिए।"),
    _q(20, "A", 4, "differential-equations", "अवकल समीकरण x(dy/dx) + 2y = x² (x ≠ 0) का व्यापक हल ज्ञात कीजिए। अथवा अवकल समीकरण (x² − y²)dx + 2xy dy = 0 का व्यापक हल ज्ञात कीजिए।"),
    _q(21, "A", 4, "three-dimensional-geometry", "रेखाओं (x + 1)/7 = (y + 1)/(−6) = (z + 1)/1 और (x − 3)/1 = (y − 5)/(−2) = (z − 7)/1 के बीच की न्यूनतम दूरी ज्ञात कीजिए। अथवा रेखाओं r⃗ = î + 2ĵ + k̂ + λ(î − ĵ + k̂) और r⃗ = 2î − ĵ − k̂ + μ(2î + ĵ + 2k̂) के बीच की न्यूनतम दूरी ज्ञात कीजिए।"),
    _q(22, "A", 4, "continuity-and-differentiability", "यदि y = sin⁻¹x है, तो दर्शाइए कि (1 − x²)(d²y/dx²) − x(dy/dx) = 0। अथवा K के उन मानों को ज्ञात कीजिए जिनके लिए f(x) = {Kcosx/(π − 2x), यदि x ≠ π/2; 3, यदि x = π/2} द्वारा परिभाषित फलन x = π/2 पर संतत है।"),
    _q(23, "A", 4, "integrals", "मान ज्ञात कीजिए: ∫₀^π (x sinx)/(1 + cos²x) dx। अथवा मान ज्ञात कीजिए: ∫ (xe^x)/(1 + x)² dx।"),
]

# Wave 66: Bihar Board (BSEB) Class 12 Mathematics
# (Elective) 2025, Intermediate Examination (Annual),
# Subject Code 121/327, I.Sc. & I.A. One bilingual booklet;
# both texts were read from the page images of the AglaSem
# scan (the PDF's Hindi text layer is a legacy-font encoding
# and its English layer drops exponents, so the images are
# the authority). Full Marks 100, Time 3 Hours 15 Minutes,
# 138 questions: Section-A 100 objective questions of 1 mark
# (answer any 50); Section-B Short Answer Q1-30 of 2 marks
# (answer any 15) and Long Answer Q31-38 of 5 marks (answer
# any 4). The entry therefore carries max_marks 100: the
# stored texts sum to 200 because every printed question is
# typed in full. Pure-expression questions are printed only
# once in the booklet, serving both mediums; verbal
# questions print the Hindi above the English.
_BSEB12_2025_EN_A = [
    _q(1, "A", 1, "integrals", "∫ dx/(sin²x cos²x) = (A) tanx + cotx + C (B) tan2x − cotx + C (C) −cotx + tanx + C (D) tanx·cotx + C"),
    _q(2, "A", 1, "integrals", "∫ dx/√(a² − x²) = (A) log|x + √(x² − a²)| + C (B) sin⁻¹(x/a) + C (C) (1/2a)log|(x − a)/(x + a)| + C (D) cot⁻¹(x/a) + C"),
    _q(3, "A", 1, "integrals", "∫ x²(1/x² + 1) dx = (A) 2x + c (B) (x³/3)(−1/x + x) + C (C) x(x²/3 − x) + C (D) (1/3)x³ + x + C"),
    _q(4, "A", 1, "integrals", "∫ (5 − 3sinx)/cos²x dx = (A) 5tanx − 3secx + C (B) 3tanx − 5secx + C (C) 5tanx + 3secx + C (D) 3tanx + 5secx + C"),
    _q(5, "A", 1, "integrals", "∫ cosec x dx = (A) log|cosec x + cot x| + c (B) log|tan(x/2)| + C (C) log|sin x| + C (D) log|cot(x/2)| + C"),
    _q(6, "A", 1, "integrals", "∫ (7 + logx)²/x dx (A) (7/3)(7 + logx)³ + C (B) (1/3)(logx)³ + C (C) (1/3)(7 + logx)³ + C (D) (2/3)(7 + logx) + C"),
    _q(7, "A", 1, "integrals", "∫ 2(sin⁻¹(cos x)) dx = (A) (π/2)x − x²/2 + C (B) x² + C (C) πx + x² + C (D) πx − x² + C"),
    _q(8, "A", 1, "integrals", "∫ e^x(1/√(1 − x²) + sin⁻¹x) dx = (A) e^x sin⁻¹x + C (B) e^x/√(1 − x²) + C (C) −e^x sin⁻¹x + C (D) (−2e^x)/√(1 − x²) + C"),
    _q(9, "A", 1, "integrals", "∫ 4x logx dx = (A) 4x logx − 4x + C (B) (x²/4)(2logx − 1) + C (C) x²(2logx − 1) + C (D) (x²/2)(2logx − 1) + C"),
    _q(10, "A", 1, "integrals", "∫ (cos√x)/√x dx = (A) 2sin√x + C (B) (1/2)sin√x + C (C) sin2√x + C (D) sinx + C"),
    _q(11, "A", 1, "differential-equations", "Degree of the differential Equation x·(d²y/dx²) + xy(dy/dx)² − xy(dy/dx) = 0 is (A) 1 (B) 2 (C) 0 (D) None of these"),
    _q(12, "A", 1, "differential-equations", "Integrating factor of the differential Equation dy/dx + y logx = cosx is (A) x (B) e^(x logx − x) (C) e^(x(1 − logx)) (D) None of these"),
    _q(13, "A", 1, "differential-equations", "Solution of Differential equation y logy dx − x dy = 0 is (A) xy = e^(cx) (B) ye^x = C (C) x = e^(cy) (D) y = e^(cx)"),
    _q(14, "A", 1, "differential-equations", "Solution of differential equation dy/dx = (1 + y²)/(1 + x²) is (A) (y + y³/3) = (x + x³/3) + k (B) (tan⁻¹x)/(tan⁻¹y) = k (C) tan⁻¹x − tan⁻¹y = k (D) (tan⁻¹x)(tan⁻¹y) = k"),
    _q(15, "A", 1, "differential-equations", "Integrating factor of differential equation dx/dy + 3x = e^(2y) is (A) e^(3y) (B) e^(3x) (C) 3y (D) 3x"),
    _q(16, "A", 1, "vector-algebra", "î·î − ĵ·ĵ = (A) 1 (B) −1 (C) 0 (D) 2"),
    _q(17, "A", 1, "vector-algebra", "|−î − ĵ − k̂| = (A) 3 (B) √3 (C) −√3 (D) 0"),
    _q(18, "A", 1, "vector-algebra", "(2î + 5ĵ − k̂)·(−î + 7ĵ + 2k̂) = (A) 28 (B) 29 (C) 30 (D) 31"),
    _q(19, "A", 1, "vector-algebra", "î × k̂ = (A) 0⃗ (B) ĵ (C) −ĵ (D) k̂ × î"),
    _q(20, "A", 1, "vector-algebra", "(ĵ + 2k̂) × (î + 2ĵ) = (A) 4î − 2ĵ + k̂ (B) −4î + 2ĵ − k̂ (C) 4î + 2ĵ + k̂ (D) −4î − 2ĵ − k̂"),
    _q(21, "A", 1, "application-of-derivatives", "The rate of change of the area of a Circle with respect to its radius r at r = 10 cm. is (A) 20π cm²/cm. (B) 22π cm²/cm. (C) 18π cm²/cm. (D) 10π cm²/cm."),
    _q(22, "A", 1, "application-of-derivatives", "The slope of the normal to the Curve y = 3x³ + 7sinx at x = 0 is (A) −7 (B) −1/7 (C) 1/7 (D) 7"),
    _q(23, "A", 1, "probability", "Let E be an event of a sample space S of an experiement, then P(S/E) = (A) 1/4 (B) 1/2 (C) 0 (D) 1"),
    _q(24, "A", 1, "probability", "If P(A) = 5/11, P(B) = 7/11 and P(A ∩ B) = 3/11 and P(A/B) = (A) 1 (B) 0 (C) 3/7 (D) 5/7"),
    _q(25, "A", 1, "probability", "A family has two children the probability that both the Children are boys given that at least one of them is a boy is (A) 2/3 (B) 3/4 (C) 1/3 (D) 1/4"),
    _q(26, "A", 1, "probability", "If P(A) = 6/11, P(B) = 5/11 and P(A ∪ B) = 7/11 then P(A/B) = (A) 4/5 (B) 5/6 (C) 6/7 (D) 5/7"),
    _q(27, "A", 1, "probability", "If E and F are independent events then P(E' ∩ F') = (A) P(E)·P(F') (B) P(E')·P(F') (C) P(E)·P(F) (D) All of these"),
    _q(28, "A", 1, "three-dimensional-geometry", "The equation of ZX-plane is (A) x = 0 (B) y = 0 (C) z = 0 (D) None of these"),
    _q(29, "A", 1, "three-dimensional-geometry", "The direction Cosines of y-axis are (A) (1, 0, 1) (B) (1, 0, 0) (C) (0, 1, 0) (D) (0, 0, 1)"),
    _q(30, "A", 1, "three-dimensional-geometry", "The distance between the points (−2, 6, 7) and (1, 2, 7) is (A) 5 (B) 7 (C) 9 (D) 4"),
    _q(31, "A", 1, "integrals", "∫ (3x²)/(x⁶ + 1) dx = (A) 3tan⁻¹x² + C (B) log(x⁶ + 1) + C (C) tan⁻¹x³ + C (D) sin⁻¹x³ + C"),
    _q(32, "A", 1, "integrals", "∫ (4x + 1)/√(2x² + x − 3) dx = (A) (1/2)√(2x² + x − 3) + C (B) 2√(2x² + x − 3) + C (C) log|2x² + x − 3| + C (D) (2/3)(2x² + x − 3)^(3/2) + C"),
    _q(33, "A", 1, "integrals", "∫ e^x[2cos2x + sin2x] dx = (A) (1/2)e^x cos2x + C (B) 2e^x cos2x + C (C) 2e^x sin2x + C (D) e^x sin2x + C"),
    _q(34, "A", 1, "integrals", "∫ dx/√(x² + a²) = (A) log|x + √(x² + a²)| + C (B) (1/a)tan⁻¹(x/a) + C (C) (1/2a)log|(x − a)/(x + a)| + C (D) log|x + √(x² − a²)| + C"),
    _q(35, "A", 1, "integrals", "∫₋₁¹ sin⁷x cos⁶x dx = (A) −1 (B) 0 (C) 1 (D) 2"),
    _q(36, "A", 1, "integrals", "∫₀^(π/2) (√cosx)/(√sinx + √cosx) dx = (A) π (B) π/8 (C) π/4 (D) π/2"),
    _q(37, "A", 1, "integrals", "∫₀¹ e^x dx = (A) e² − 1 (B) 1/(e − 1) (C) 1 − e (D) e − 1"),
    _q(38, "A", 1, "integrals", "∫₀^(π/4) tanx dx = (A) log2 (B) log4 (C) 2log2 (D) (1/2)log2"),
    _q(39, "A", 1, "integrals", "∫₀¹ dx/(1 + x²) = (A) π/4 (B) π/2 (C) 0 (D) π"),
    _q(40, "A", 1, "integrals", "∫₀¹ xe^x dx = (A) 1 (B) 2 (C) 3 (D) 4"),
    _q(41, "A", 1, "inverse-trigonometric-functions", "cos⁻¹(−1/√2) = (A) π/4 (B) 3π/4 (C) 5π/4 (D) −π/4"),
    _q(42, "A", 1, "inverse-trigonometric-functions", "tan⁻¹(−√3) = (A) 2π/3 (B) 4π/3 (C) π/3 (D) −π/3"),
    _q(43, "A", 1, "inverse-trigonometric-functions", "tan⁻¹(tan(3π/4)) = (A) π/4 (B) 5π/4 (C) −π/4 (D) 3π/4"),
    _q(44, "A", 1, "inverse-trigonometric-functions", "sin[π/3 − sin⁻¹(−1/2)] = (A) 1/√2 (B) 1 (C) 1/2 (D) √3/2"),
    _q(45, "A", 1, "inverse-trigonometric-functions", "sin(tan⁻¹x) = ___, |x| < 1 (A) x/√(1 − x²) (B) 1/√(1 − x²) (C) 1/√(1 + x²) (D) x/√(1 + x²)"),
    _q(46, "A", 1, "inverse-trigonometric-functions", "tan⁻¹√3 − cot⁻¹(−√3) = (A) π (B) −π/2 (C) 0 (D) 2√3"),
    _q(47, "A", 1, "inverse-trigonometric-functions", "sin⁻¹sin(3π/5) = (A) 2π/5 (B) 3π/5 (C) 8π/5 (D) π/5"),
    _q(48, "A", 1, "inverse-trigonometric-functions", "Domain of cosec⁻¹x is (A) R (B) (−1, 1) (C) R − (−1, 1) (D) [−1, 1]"),
    _q(49, "A", 1, "inverse-trigonometric-functions", "sin⁻¹(−1/2) + cos⁻¹(√3/2) = (A) 0 (B) π/3 (C) 2π/3 (D) π/6"),
    _q(50, "A", 1, "relations-and-functions", "Function f : N → N, f(x) = 2x is (A) one-one and onto (B) one-one but not onto (C) onto but not one-one (D) None of these"),
]
_BSEB12_2025_EN_B = [
    _q(51, "A", 1, "vector-algebra", "If a⃗ = 2î − ĵ + 2k̂ then unit vector in the direction of vector a⃗ is (A) (1/3)(−2î + ĵ − 2k̂) (B) (1/9)(2î − ĵ + 2k̂) (C) (1/9)(−2î + ĵ − 2k̂) (D) (1/3)(2î − ĵ + 2k̂)"),
    _q(52, "A", 1, "vector-algebra", "If a⃗ = 2î + 3ĵ + 4k̂, b⃗ = −ĵ − 2k̂ then |a⃗ × b⃗| = (A) 2√6 (B) 6√2 (C) √12 (D) √36"),
    _q(53, "A", 1, "vector-algebra", "If (3î − 2ĵ + k̂) and (2î − 3ĵ − λk̂) are perpendicular to each other then λ = (A) 0 (B) −12 (C) 12 (D) 6"),
    _q(54, "A", 1, "vector-algebra", "ĵ·(î × k̂) = (A) −ĵ (B) 0 (C) −1 (D) 1"),
    _q(55, "A", 1, "vector-algebra", "The projection of the vector î − ĵ on the vector î + ĵ is (A) 2 (B) 0 (C) 1 (D) 1/2"),
    _q(56, "A", 1, "vector-algebra", "If |a⃗| = 3, |b⃗| = √2/3 and a⃗ × b⃗ is a unit vector then angle between a⃗ and b⃗ is (A) π/6 (B) π/4 (C) π/3 (D) π/2"),
    _q(57, "A", 1, "vector-algebra", "î·(ĵ × k̂) + ĵ·(î × k̂) + k̂·(î × ĵ) = (A) 0 (B) −1 (C) 1 (D) 3"),
    _q(58, "A", 1, "vector-algebra", "(2î + 3ĵ − 5k̂)·(7î − ĵ + 3k̂) = (A) 32 (B) 2 (C) 4 (D) −4"),
    _q(59, "A", 1, "linear-programming", "The maximum value of z = 3x + 4y is, where constraints x + y ≤ 4, x ≥ 0, y ≥ 0 (A) 16 (B) 0 (C) 12 (D) 28"),
    _q(60, "A", 1, "linear-programming", "The minimum value of z = 4x + y is, where constraints x + y ≤ 50, x + y ≤ 90, x ≥ 0, y ≥ 0 (A) 0 (B) 50 (C) 110 (D) 120"),
    _q(61, "A", 1, "determinants", "If |2 x; x 8| = |10 7; 30 21|, then x = (A) ±16 (B) ±4 (C) 0 (D) ±3"),
    _q(62, "A", 1, "determinants", "|11 7 9; 2 −1 5; 22 14 18| = (A) 72 (B) −61 (C) 0 (D) 65"),
    _q(63, "A", 1, "determinants", "|−1 3 0; 1 2 4; 4 1 0| = (A) −52 (B) 0 (C) 52 (D) 62"),
    _q(64, "A", 1, "matrices", "The number of all possible matrices of order 2 × 2 with each entry 3 or 7 is (A) 42 (B) 32 (C) 64 (D) 16"),
    _q(65, "A", 1, "matrices", "6[−2 1; 3 5] = (A) [12 6; −18 30] (B) [−12 6; 18 30] (C) [12 6; 18 30] (D) [6 −12; 18 30]"),
    _q(66, "A", 1, "matrices", "A = [0 1; 1 0] ⇒ A⁴ = (A) [0 1; 1 0] (B) [1 0; 0 1] (C) [0 1; 0 1] (D) [1 1; 0 0]"),
    _q(67, "A", 1, "matrices", "[1 −2 0][3; −2; 11] = (A) [7] (B) [3 −6 0; −2 4 0; 11 −22 0] (C) [18] (D) [3 6 0; 2 −4 0; 11 −22 0]"),
    _q(68, "A", 1, "matrices", "If A and B are invertible matrices of same order then (AB)⁻¹ = (A) A − B (B) A⁻¹B⁻¹ (C) B − A (D) B⁻¹A⁻¹"),
    _q(69, "A", 1, "relations-and-functions", "A function f : X → Y is one-one if x₁, x₂ ∈ X, f(x₁) = f(x₂) ⇒ (A) x₁x₂ = 1 (B) x₁x₂ = −1 (C) x₁ = x₂ (D) None of these"),
    _q(70, "A", 1, "relations-and-functions", "A function f : X → Y invertible if and only if f is (A) one-one (B) onto (C) one-one and onto (D) None of these"),
    _q(71, "A", 1, "continuity-and-differentiability", "d(sinx)/dx = (A) −cosx (B) 1/secx (C) (cosx)⁻¹ (D) sin(π − x)"),
    _q(72, "A", 1, "continuity-and-differentiability", "(d/dx) log sin(sec⁻¹x + cosec⁻¹x) = (A) 0 (B) 1 (C) cos(sec⁻¹x + cosec⁻¹x) (D) cot(sec⁻¹x + cosec⁻¹x)"),
    _q(73, "A", 1, "continuity-and-differentiability", "If y = t²¹ then d²y/dt² = (A) 210t¹⁹ (B) 420t¹⁹ (C) 420t²⁰ (D) 210t²⁰"),
    _q(74, "A", 1, "continuity-and-differentiability", "If x = 4t, y = 4/t then dy/dx = (A) 1/t² (B) 4/t² (C) t/4 (D) −1/t²"),
    _q(75, "A", 1, "continuity-and-differentiability", "(d/dx)cos⁻¹(sinx) = (A) −1 (B) 1/√(1 − x²) (C) 1 (D) 0"),
    _q(76, "A", 1, "continuity-and-differentiability", "(d/dx)sin(√x) = (A) 2cos√x/√x (B) cos√x/√x (C) cos√x/(2√x) (D) cos√x/(2x)"),
    _q(77, "A", 1, "continuity-and-differentiability", "(d/dx)(2 + cos2x) = (A) 1 − sin2x (B) 2sin2x (C) −2sin2x (D) 2sin²x"),
    _q(78, "A", 1, "integrals", "∫₂³ (1/x) dx = (A) log6 (B) log(3/2) (C) log(2/3) (D) 0"),
    _q(79, "A", 1, "integrals", "∫ (sin⁻¹x)/√(1 − x²) dx (A) (1/2)(sin⁻¹x)² + C (B) (−1/2)(sin⁻¹x)² + C (C) 2(sin⁻¹x)² + C (D) −2(sin⁻¹x)² + C"),
    _q(80, "A", 1, "integrals", "∫ from −π/2 to π/2 of (x⁵ + xcosx + sin⁷x + 1) dx = (A) π (B) 0 (C) 2 (D) 1"),
    _q(81, "A", 1, "three-dimensional-geometry", "If a line makes angle 30°, 60° and 90° with the positive direction of x, y and z-axis respectively, then its direction cosines are (A) 0, 1, 0 (B) 1/√14, 2/√14, 3/√14 (C) 3/5, 4/5, 0 (D) √3/2, 1/2, 0"),
    _q(82, "A", 1, "three-dimensional-geometry", "Direction ratios of two lines are a₁, b₁, c₁ and a₂, b₂, c₂ respectively. Both lines are parallel, if (A) a₁a₂ + b₁b₂ + c₁c₂ = 0 (B) a₁/a₂ + b₁/b₂ + c₁/c₂ = 0 (C) a₁a₂ + b₁b₂ + c₁c₂ = 1 (D) a₁/a₂ ≠ b₁/b₂ = c₁/c₂"),
    _q(83, "A", 1, "three-dimensional-geometry", "The direction cosines of the unit vector perpendicular to the plane r⃗·(2î + 3ĵ − 6k̂) + 1 = 0 and passing through the origin are (A) 1/√3, 1/√3, −1/√3 (B) −2/√7, −3/√7, 6/√7 (C) −2/7, −3/7, 6/7 (D) 1, 0, 0"),
    _q(84, "A", 1, "three-dimensional-geometry", "If direction ratios of a straight line are 2, −3, 5 then its direction cosines are (A) 2/4, −3/4, 5/4 (B) 2/√38, −3/√38, 5/√38 (C) 2/√19, −3/√19, 5/√19 (D) 2/√38, 3/√38, 5/√38"),
    _q(85, "A", 1, "three-dimensional-geometry", "The plane parallel to the Plane 2x − 3y + 7z = 9 is (A) 2x − 3y + 7z = 23 (B) 2x + 3y + 7z = 9 (C) 3x + 2y − 7z = 10 (D) None of these"),
    _q(86, "A", 1, "three-dimensional-geometry", "If two planes x − 3y + 2z = 10 and 7x + y − λz = 5 are perpendicular to each other, then λ = (A) −3 (B) −2 (C) 2 (D) None of these"),
    _q(87, "A", 1, "three-dimensional-geometry", "If the lines (x + 1)/a = (y − 2)/b = (z − 3)/c and (x − 2)/3 = (y − 5)/1 = (z − 6)/2 are parallel then (A) 3a + b + 2c = 0 (B) 3/a = 1/b = 2/c (C) 3a = b = 2c (D) None of these"),
    _q(88, "A", 1, "three-dimensional-geometry", "The angle between the planes 4x + 8y + z − 3 = 0 and y + z − 7 = 0 is (A) π/2 (B) 0 (C) π/3 (D) π/4"),
    _q(89, "A", 1, "three-dimensional-geometry", "The distance of the plane 2x − y + z = 7 from the point (0, 0, 1) is (A) 6√6 (B) √6 (C) 7/√6 (D) 3"),
    _q(90, "A", 1, "matrices", "2[3 7; 1 −2] + 5[1 3; 0 4] = (A) [11 29; 2 16] (B) [29 11; 2 16] (C) [11 29; 2 −16] (D) [29 11; −2 −16]"),
    _q(91, "A", 1, "matrices", "If A = [2 −1 0; 7 3 5] then A' = (A) [2 3; −1 7; 0 5] (B) [2 0; −1 7; 3 5] (C) [2 7; −1 3; 0 5] (D) [2 7; −1 3; 0 4]"),
    _q(92, "A", 1, "determinants", "If |x + 1 3; 5 x − 1| = 0 then x = (A) ±16 (B) ±4 (C) 16 (D) 0"),
    _q(93, "A", 1, "continuity-and-differentiability", "(d/dx)(cosec⁻¹x) = (A) 1/√(x² − 1) (B) 1/(x√(x² − 1)) (C) −1/(x√(x² − 1)) (D) −1/(x√(1 − x²))"),
    _q(94, "A", 1, "continuity-and-differentiability", "(d/dx) log(secx) = (A) −tanx (B) cotx (C) −cotx (D) tanx"),
    _q(95, "A", 1, "matrices", "If A = [1 0; 0 1] then A⁻¹ = (A) [0 0; 1 1] (B) [0 1; 1 0] (C) [0 1; 0 1] (D) [1 0; 0 1]"),
    _q(96, "A", 1, "integrals", "∫((x³ − x² + x − 1)/(x² + 1))dx = (A) x²/2 − x + C (B) x − x²/2 + C (C) 1 − x + C (D) x²/2 + x + C"),
    _q(97, "A", 1, "integrals", "∫e^(−7x)dx = (A) −7e^(−7x) + C (B) (−1/7)e^(−7x) + C (C) (1/7)e^(−7x) + C (D) (−1/7)e^(7x) + C"),
    _q(98, "A", 1, "continuity-and-differentiability", "(d/dx)(3x² − cosx + 2) = (A) 2x + sinx (B) 6x − sinx (C) 6x + sinx (D) sinx − 6x"),
    _q(99, "A", 1, "integrals", "∫(5x⁴ + 2x + sinx)dx = (A) x⁵ + x² + cosx + C (B) x⁵ + 2 − cosx + C (C) x⁵ + x² − cosx + C (D) x⁴ + x² − cosx + C"),
    _q(100, "A", 1, "continuity-and-differentiability", "(d/dx)(e^(logx²)) = (A) 1/logx² (B) 2x (C) 2x/logx² (D) 2/x"),
    _q(1, "B", 2, "three-dimensional-geometry", "Find the distance of the point (a, b, c) from X-axis."),
    _q(2, "B", 2, "three-dimensional-geometry", "Find the equation of a plane passing through the points (3, 0, 0), (0, −1, 0) and (0, 0, 2)."),
    _q(3, "B", 2, "three-dimensional-geometry", "The foot of perpendicular drawn from the origin to a plane is (2, −1, 3). Find the equation of the plane."),
    _q(4, "B", 2, "probability", "If A and B are two events such that P(A) = 1/2, P(B) = 1/3 and P(A ∩ B) = 1/4 then find the following (i) P(A'/B) (ii) P(A'/B')"),
    _q(5, "B", 2, "probability", "The probability distribution of a random variable x is following. X: 0.5, 1, 1.5, 2; P(X): K, K², 2K², K. (i) Find the value of K. (ii) Determine the mean of the distribution."),
    _q(6, "B", 2, "inverse-trigonometric-functions", "If cos⁻¹α + cos⁻¹β + cos⁻¹γ = 3π, then find the value of α(β + γ) + β(γ + α) + γ(α + β)."),
    _q(7, "B", 2, "inverse-trigonometric-functions", "Find the value of tan⁻¹(−1/√3) + cot⁻¹(1/√3) + tan⁻¹[sin(−π/2)]."),
    _q(8, "B", 2, "inverse-trigonometric-functions", "Solve the Equation cos(tan⁻¹x) = sin(cot⁻¹(3/4))."),
    _q(9, "B", 2, "integrals", "Integrate: ∫(x² + 2)/(x + 1) dx"),
    _q(10, "B", 2, "integrals", "Integrate: ∫ dx/(1 + cosx)"),
    _q(11, "B", 2, "integrals", "If ∫₀^a (1/(1 + 4x²)) dx = π/8 then find the value of a."),
    _q(12, "B", 2, "integrals", "Integrate: ∫ sinx/(3 + 4cos²x) dx"),
    _q(13, "B", 2, "integrals", "Integrate: ∫ (sin⁶x + cos⁶x)/(sin²x cos²x) dx"),
    _q(14, "B", 2, "integrals", "Integrate: ∫₂⁸ |x − 5| dx"),
    _q(15, "B", 2, "integrals", "Integrate: ∫ from −π/4 to π/4 of sin²x dx"),
    _q(16, "B", 2, "vector-algebra", "If a⃗ = î + ĵ + 2k̂ and b⃗ = 2î + ĵ + 2k̂ then find the unit vector in the direction of vector (2a⃗ − b⃗)."),
    _q(17, "B", 2, "vector-algebra", "Find vector v⃗ which is perpendicular to (2î − ĵ + 2k̂) and (4î − ĵ + 3k̂) and |v⃗| = 6"),
    _q(18, "B", 2, "vector-algebra", "If a⃗, b⃗, c⃗ are unit vectors and a⃗ + b⃗ + c⃗ = 0⃗ then find the value of a⃗·b⃗ + b⃗·c⃗ + c⃗·a⃗."),
    _q(19, "B", 2, "continuity-and-differentiability", "If x = 3cosθ − 2cos³θ, y = 3sinθ − 2sin³θ then find dy/dx."),
    _q(20, "B", 2, "continuity-and-differentiability", "If tan⁻¹(x² + y²) = K then find dy/dx."),
    _q(21, "B", 2, "continuity-and-differentiability", "If y = log|(1 − x²)/(1 + x²)|, then find dy/dx."),
    _q(22, "B", 2, "continuity-and-differentiability", "If √x + √y = 1 then find the value of dy/dx at point (1/4, 1/4)."),
    _q(23, "B", 2, "application-of-derivatives", "If the curves ay + x² = 7 and x³ = y cut each other orthogonally at (1, 1), find the value of a."),
    _q(24, "B", 2, "application-of-derivatives", "Find the interval in which the function f(x) = 2x³ + 9x² + 12x − 1 is decreasing."),
    _q(25, "B", 2, "differential-equations", "Find the integrating factor of the differential equation (1 − x²)(dy/dx) − xy = 1."),
    _q(26, "B", 2, "differential-equations", "Solve: dy/dx + y = e^(−x)"),
    _q(27, "B", 2, "matrices", "If A = [2 −1 0; 3 4 5] and B = [7 −1; 2 3; 5 0], then find (AB)'."),
    _q(28, "B", 2, "matrices", "Find the inverse matrix of the matrix A = [3 2; 5 −1]."),
    _q(29, "B", 2, "determinants", "Solve: |x² − x + 1, x − 1; x + 1, x + 1| = 2"),
    _q(30, "B", 2, "relations-and-functions", "If f(x) = 4 − (x − 7)³ then find f⁻¹(x)."),
    _q(31, "B", 5, "inverse-trigonometric-functions", "Prove that sin⁻¹(5/13) + cos⁻¹(3/5) = tan⁻¹(63/16)."),
    _q(32, "B", 5, "integrals", "Integrate: ∫₀¹ x log(1 + 2x) dx"),
    _q(33, "B", 5, "differential-equations", "Solve: (1 + tany)(dx − dy) + 2x dy = 0"),
    _q(34, "B", 5, "application-of-derivatives", "Find the equation of the normal lines to the curve 3x² − y² = 8 which are parallel to the line x + 3y = 4."),
    _q(35, "B", 5, "vector-algebra", "If a⃗ = î − ĵ + k̂ and b⃗ = ĵ − k̂ then find c⃗ such that a⃗ × c⃗ = b⃗ and a⃗·c⃗ = 3."),
    _q(36, "B", 5, "linear-programming", "Minimize z = 13x − 15y subject to x + y ≤ 7, 2x − 3y + 6 ≥ 0, x ≥ 0 and y ≥ 0."),
    _q(37, "B", 5, "probability", "Find the probability distribution of number of doublets in three throws of a pair of dice."),
    _q(38, "B", 5, "matrices", "Solve the following linear equations by matrix method. 2x + 3y + 3z = 5, x − 2y + z = −4, 3x − y − 2z = 3."),
]
_BSEB12_2025_EN = _BSEB12_2025_EN_A + _BSEB12_2025_EN_B
_BSEB12_2025_HI_A = [
    _q(1, "A", 1, "integrals", "∫ dx/(sin²x cos²x) = (a) tanx + cotx + C (b) tan2x − cotx + C (c) −cotx + tanx + C (d) tanx·cotx + C"),
    _q(2, "A", 1, "integrals", "∫ dx/√(a² − x²) = (a) log|x + √(x² − a²)| + C (b) sin⁻¹(x/a) + C (c) (1/2a)log|(x − a)/(x + a)| + C (d) cot⁻¹(x/a) + C"),
    _q(3, "A", 1, "integrals", "∫ x²(1/x² + 1) dx = (a) 2x + c (b) (x³/3)(−1/x + x) + C (c) x(x²/3 − x) + C (d) (1/3)x³ + x + C"),
    _q(4, "A", 1, "integrals", "∫ (5 − 3sinx)/cos²x dx = (a) 5tanx − 3secx + C (b) 3tanx − 5secx + C (c) 5tanx + 3secx + C (d) 3tanx + 5secx + C"),
    _q(5, "A", 1, "integrals", "∫ cosec x dx = (a) log|cosec x + cot x| + c (b) log|tan(x/2)| + C (c) log|sin x| + C (d) log|cot(x/2)| + C"),
    _q(6, "A", 1, "integrals", "∫ (7 + logx)²/x dx (a) (7/3)(7 + logx)³ + C (b) (1/3)(logx)³ + C (c) (1/3)(7 + logx)³ + C (d) (2/3)(7 + logx) + C"),
    _q(7, "A", 1, "integrals", "∫ 2(sin⁻¹(cos x)) dx = (a) (π/2)x − x²/2 + C (b) x² + C (c) πx + x² + C (d) πx − x² + C"),
    _q(8, "A", 1, "integrals", "∫ e^x(1/√(1 − x²) + sin⁻¹x) dx = (a) e^x sin⁻¹x + C (b) e^x/√(1 − x²) + C (c) −e^x sin⁻¹x + C (d) (−2e^x)/√(1 − x²) + C"),
    _q(9, "A", 1, "integrals", "∫ 4x logx dx = (a) 4x logx − 4x + C (b) (x²/4)(2logx − 1) + C (c) x²(2logx − 1) + C (d) (x²/2)(2logx − 1) + C"),
    _q(10, "A", 1, "integrals", "∫ (cos√x)/√x dx = (a) 2sin√x + C (b) (1/2)sin√x + C (c) sin2√x + C (d) sinx + C"),
    _q(11, "A", 1, "differential-equations", "अवकल समीकरण x·(d²y/dx²) + xy(dy/dx)² − xy(dy/dx) = 0 का घात है (a) 1 (b) 2 (c) 0 (d) इनमें से कोई नहीं"),
    _q(12, "A", 1, "differential-equations", "अवकल समीकरण dy/dx + y logx = cosx का समाकलन गुणक है (a) x (b) e^(x logx − x) (c) e^(x(1 − logx)) (d) इनमें से कोई नहीं"),
    _q(13, "A", 1, "differential-equations", "अवकल समीकरण y logy dx − x dy = 0 का हल है (a) xy = e^(cx) (b) ye^x = C (c) x = e^(cy) (d) y = e^(cx)"),
    _q(14, "A", 1, "differential-equations", "अवकल समीकरण dx/dy = (1 + y²)/(1 + x²) का हल है (a) (y + y³/3) = (x + x³/3) + k (b) (tan⁻¹x)/(tan⁻¹y) = k (c) tan⁻¹x − tan⁻¹y = k (d) (tan⁻¹x)(tan⁻¹y) = k"),
    _q(15, "A", 1, "differential-equations", "अवकल समीकरण dx/dy + 3x = e^(2y) का समाकलन है (a) e^(3y) (b) e^(3x) (c) 3y (d) 3x"),
    _q(16, "A", 1, "vector-algebra", "î·î − ĵ·ĵ = (a) 1 (b) −1 (c) 0 (d) 2"),
    _q(17, "A", 1, "vector-algebra", "|−î − ĵ − k̂| = (a) 3 (b) √3 (c) −√3 (d) 0"),
    _q(18, "A", 1, "vector-algebra", "(2î + 5ĵ − k̂)·(−î + 7ĵ + 2k̂) = (a) 28 (b) 29 (c) 30 (d) 31"),
    _q(19, "A", 1, "vector-algebra", "î × k̂ = (a) 0⃗ (b) ĵ (c) −ĵ (d) k̂ × î"),
    _q(20, "A", 1, "vector-algebra", "(ĵ + 2k̂) × (î + 2ĵ) = (a) 4î − 2ĵ + k̂ (b) −4î + 2ĵ − k̂ (c) 4î + 2ĵ + k̂ (d) −4î − 2ĵ − k̂"),
    _q(21, "A", 1, "application-of-derivatives", "एक वृत्त की त्रिज्या r = 10 cm. पर r के सापेक्ष क्षेत्रफल में परिवर्तन की दर है (a) 20π cm²/cm. (b) 22π cm²/cm. (c) 18π cm²/cm. (d) 10π cm²/cm."),
    _q(22, "A", 1, "application-of-derivatives", "वक्र y = 3x³ + 7sinx के x = 0 पर लम्ब रेखा की प्रवणता है (a) −7 (b) −1/7 (c) 1/7 (d) 7"),
    _q(23, "A", 1, "probability", "मान लें कि E किसी प्रतिदर्श समष्टि S की घटना है तो P(S/E) = (a) 1/4 (b) 1/2 (c) 0 (d) 1"),
    _q(24, "A", 1, "probability", "यदि P(A) = 5/11, P(B) = 7/11 तथा P(A ∩ B) = 3/11 तो P(A/B) = (a) 1 (b) 0 (c) 3/7 (d) 5/7"),
    _q(25, "A", 1, "probability", "एक परिवार में दो बच्चे हैं। यदि यह ज्ञात हो कि बच्चों में से कम से कम एक बच्चा लड़का है तो दोनों बच्चों के लड़का होने की प्रायिकता है (a) 2/3 (b) 3/4 (c) 1/3 (d) 1/4"),
    _q(26, "A", 1, "probability", "यदि P(A) = 6/11, P(B) = 5/11 और P(A ∪ B) = 7/11 तो P(A/B) = (a) 4/5 (b) 5/6 (c) 6/7 (d) 5/7"),
    _q(27, "A", 1, "probability", "यदि E और F स्वतंत्र घटनाएँ हैं। तो P(E' ∩ F') = (a) P(E)·P(F') (b) P(E')·P(F') (c) P(E)·P(F) (d) इनमें से सभी"),
    _q(28, "A", 1, "three-dimensional-geometry", "ZX-तल का समीकरण है (a) x = 0 (b) y = 0 (c) z = 0 (d) इनमें से कोई नहीं"),
    _q(29, "A", 1, "three-dimensional-geometry", "y-अक्ष की दिक्-कोज्याएँ हैं (a) (1, 0, 1) (b) (1, 0, 0) (c) (0, 1, 0) (d) (0, 0, 1)"),
    _q(30, "A", 1, "three-dimensional-geometry", "बिन्दुओं (−2, 6, 7) और (1, 2, 7) के बीच की दूरी है: (a) 5 (b) 7 (c) 9 (d) 4"),
    _q(31, "A", 1, "integrals", "∫ (3x²)/(x⁶ + 1) dx = (a) 3tan⁻¹x² + C (b) log(x⁶ + 1) + C (c) tan⁻¹x³ + C (d) sin⁻¹x³ + C"),
    _q(32, "A", 1, "integrals", "∫ (4x + 1)/√(2x² + x − 3) dx = (a) (1/2)√(2x² + x − 3) + C (b) 2√(2x² + x − 3) + C (c) log|2x² + x − 3| + C (d) (2/3)(2x² + x − 3)^(3/2) + C"),
    _q(33, "A", 1, "integrals", "∫ e^x[2cos2x + sin2x] dx = (a) (1/2)e^x cos2x + C (b) 2e^x cos2x + C (c) 2e^x sin2x + C (d) e^x sin2x + C"),
    _q(34, "A", 1, "integrals", "∫ dx/√(x² + a²) = (a) log|x + √(x² + a²)| + C (b) (1/a)tan⁻¹(x/a) + C (c) (1/2a)log|(x − a)/(x + a)| + C (d) log|x + √(x² − a²)| + C"),
    _q(35, "A", 1, "integrals", "∫₋₁¹ sin⁷x cos⁶x dx = (a) −1 (b) 0 (c) 1 (d) 2"),
    _q(36, "A", 1, "integrals", "∫₀^(π/2) (√cosx)/(√sinx + √cosx) dx = (a) π (b) π/8 (c) π/4 (d) π/2"),
    _q(37, "A", 1, "integrals", "∫₀¹ e^x dx = (a) e² − 1 (b) 1/(e − 1) (c) 1 − e (d) e − 1"),
    _q(38, "A", 1, "integrals", "∫₀^(π/4) tanx dx = (a) log2 (b) log4 (c) 2log2 (d) (1/2)log2"),
    _q(39, "A", 1, "integrals", "∫₀¹ dx/(1 + x²) = (a) π/4 (b) π/2 (c) 0 (d) π"),
    _q(40, "A", 1, "integrals", "∫₀¹ xe^x dx = (a) 1 (b) 2 (c) 3 (d) 4"),
    _q(41, "A", 1, "inverse-trigonometric-functions", "cos⁻¹(−1/√2) = (a) π/4 (b) 3π/4 (c) 5π/4 (d) −π/4"),
    _q(42, "A", 1, "inverse-trigonometric-functions", "tan⁻¹(−√3) = (a) 2π/3 (b) 4π/3 (c) π/3 (d) −π/3"),
    _q(43, "A", 1, "inverse-trigonometric-functions", "tan⁻¹(tan(3π/4)) = (a) π/4 (b) 5π/4 (c) −π/4 (d) 3π/4"),
    _q(44, "A", 1, "inverse-trigonometric-functions", "sin[π/3 − sin⁻¹(−1/2)] = (a) 1/√2 (b) 1 (c) 1/2 (d) √3/2"),
    _q(45, "A", 1, "inverse-trigonometric-functions", "sin(tan⁻¹x) = ___, |x| < 1 (a) x/√(1 − x²) (b) 1/√(1 − x²) (c) 1/√(1 + x²) (d) x/√(1 + x²)"),
    _q(46, "A", 1, "inverse-trigonometric-functions", "tan⁻¹√3 − cot⁻¹(−√3) = (a) π (b) −π/2 (c) 0 (d) 2√3"),
    _q(47, "A", 1, "inverse-trigonometric-functions", "sin⁻¹sin(3π/5) = (a) 2π/5 (b) 3π/5 (c) 8π/5 (d) π/5"),
    _q(48, "A", 1, "inverse-trigonometric-functions", "cosec⁻¹x का प्रांत है (a) R (b) (−1, 1) (c) R − (−1, 1) (d) [−1, 1]"),
    _q(49, "A", 1, "inverse-trigonometric-functions", "sin⁻¹(−1/2) + cos⁻¹(√3/2) = (a) 0 (b) π/3 (c) 2π/3 (d) π/6"),
    _q(50, "A", 1, "relations-and-functions", "फलन f : N → N, f(x) = 2x है: (a) एकैकी तथा आच्छादक (b) एकैकी लेकिन आच्छादक नहीं (c) आच्छादक लेकिन एकैकी नहीं (d) इनमें से कोई नहीं"),
]
_BSEB12_2025_HI_B = [
    _q(51, "A", 1, "vector-algebra", "यदि a⃗ = 2î − ĵ + 2k̂ तो a⃗ की दिशा में संगत इकाई सदिश â है: (a) (1/3)(−2î + ĵ − 2k̂) (b) (1/9)(2î − ĵ + 2k̂) (c) (1/9)(−2î + ĵ − 2k̂) (d) (1/3)(2î − ĵ + 2k̂)"),
    _q(52, "A", 1, "vector-algebra", "यदि a⃗ = 2î + 3ĵ + 4k̂, b⃗ = −ĵ − 2k̂ तो |a⃗ × b⃗| = (a) 2√6 (b) 6√2 (c) √12 (d) √36"),
    _q(53, "A", 1, "vector-algebra", "यदि (3î − 2ĵ + k̂) तथा (2î − 3ĵ − λk̂) परस्पर लम्ब हों तो λ = (a) 0 (b) −12 (c) 12 (d) 6"),
    _q(54, "A", 1, "vector-algebra", "ĵ·(î × k̂) = (a) −ĵ (b) 0 (c) −1 (d) 1"),
    _q(55, "A", 1, "vector-algebra", "सदिश î − ĵ का सदिश î + ĵ पर प्रक्षेप है (a) 2 (b) 0 (c) 1 (d) 1/2"),
    _q(56, "A", 1, "vector-algebra", "यदि |a⃗| = 3, |b⃗| = √2/3 तथा a⃗ × b⃗ एक इकाई सदिश है। तो a⃗ और b⃗ के बीच का कोण है (a) π/6 (b) π/4 (c) π/3 (d) π/2"),
    _q(57, "A", 1, "vector-algebra", "î·(ĵ × k̂) + ĵ·(î × k̂) + k̂·(î × ĵ) = (a) 0 (b) −1 (c) 1 (d) 3"),
    _q(58, "A", 1, "vector-algebra", "(2î + 3ĵ − 5k̂)·(7î − ĵ + 3k̂) = (a) 32 (b) 2 (c) 4 (d) −4"),
    _q(59, "A", 1, "linear-programming", "z = 3x + 4y का अधिकतम मान है, जहाँ कि व्यवरोध x + y ≤ 4, x ≥ 0, y ≥ 0 (a) 16 (b) 0 (c) 12 (d) 28"),
    _q(60, "A", 1, "linear-programming", "z = 4x + y का न्यूनतम मान है, जहाँ कि व्यवरोध x + y ≤ 50, x + y ≤ 90, x ≥ 0, y ≥ 0 (a) 0 (b) 50 (c) 110 (d) 120"),
    _q(61, "A", 1, "determinants", "यदि |2 x; x 8| = |10 7; 30 21| तो x = (a) ±16 (b) ±4 (c) 0 (d) ±3"),
    _q(62, "A", 1, "determinants", "|11 7 9; 2 −1 5; 22 14 18| = (a) 72 (b) −61 (c) 0 (d) 65"),
    _q(63, "A", 1, "determinants", "|−1 3 0; 1 2 4; 4 1 0| = (a) −52 (b) 0 (c) 52 (d) 62"),
    _q(64, "A", 1, "matrices", "2 × 2 कोटि के ऐसे आव्यूहो की कुल कितनी संख्या होगी जिनकी प्रत्येक प्रविष्टि 3 या 7 है (a) 42 (b) 32 (c) 64 (d) 16"),
    _q(65, "A", 1, "matrices", "6[−2 1; 3 5] = (a) [12 6; −18 30] (b) [−12 6; 18 30] (c) [12 6; 18 30] (d) [6 −12; 18 30]"),
    _q(66, "A", 1, "matrices", "A = [0 1; 1 0] ⇒ A⁴ = (a) [0 1; 1 0] (b) [1 0; 0 1] (c) [0 1; 0 1] (d) [1 1; 0 0]"),
    _q(67, "A", 1, "matrices", "[1 −2 0][3; −2; 11] = (a) [7] (b) [3 −6 0; −2 4 0; 11 −22 0] (c) [18] (d) [3 6 0; 2 −4 0; 11 −22 0]"),
    _q(68, "A", 1, "matrices", "यदि A तथा B समान कोटि के व्युत्क्रमीय आव्यूह हों तो (AB)⁻¹ = (a) A − B (b) A⁻¹B⁻¹ (c) B − A (d) B⁻¹A⁻¹"),
    _q(69, "A", 1, "relations-and-functions", "एक फलन f : X → Y एकैकी फलन है, यदि x₁, x₂ ∈ X, f(x₁) = f(x₂) ⇒ (a) x₁x₂ = 1 (b) x₁x₂ = −1 (c) x₁ = x₂ (d) इनमें से कोई नहीं"),
    _q(70, "A", 1, "relations-and-functions", "एक फलन f : X → Y व्युत्क्रमणीय है, यदि और केवल यदि f हो (a) एकैकी (b) आच्छादक (c) एकैकी तथा आच्छादक (d) इनमें से कोई नहीं"),
    _q(71, "A", 1, "continuity-and-differentiability", "d(sinx)/dx = (a) −cosx (b) 1/secx (c) (cosx)⁻¹ (d) sin(π − x)"),
    _q(72, "A", 1, "continuity-and-differentiability", "(d/dx) log sin(sec⁻¹x + cosec⁻¹x) = (a) 0 (b) 1 (c) cos(sec⁻¹x + cosec⁻¹x) (d) cot(sec⁻¹x + cosec⁻¹x)"),
    _q(73, "A", 1, "continuity-and-differentiability", "यदि y = t²¹ तो d²y/dt² = (a) 210t¹⁹ (b) 420t¹⁹ (c) 420t²⁰ (d) 210t²⁰"),
    _q(74, "A", 1, "continuity-and-differentiability", "यदि x = 4t, y = 4/t तो dy/dx = (a) 1/t² (b) 4/t² (c) t/4 (d) −1/t²"),
    _q(75, "A", 1, "continuity-and-differentiability", "(d/dx)cos⁻¹(sinx) = (a) −1 (b) 1/√(1 − x²) (c) 1 (d) 0"),
    _q(76, "A", 1, "continuity-and-differentiability", "(d/dx)sin(√x) = (a) 2cos√x/√x (b) cos√x/√x (c) cos√x/(2√x) (d) cos√x/(2x)"),
    _q(77, "A", 1, "continuity-and-differentiability", "(d/dx)(2 + cos2x) = (a) 1 − sin2x (b) 2sin2x (c) −2sin2x (d) 2sin²x"),
    _q(78, "A", 1, "integrals", "∫₂³ (1/x) dx = (a) log6 (b) log(3/2) (c) log(2/3) (d) 0"),
    _q(79, "A", 1, "integrals", "∫ (sin⁻¹x)/√(1 − x²) dx (a) (1/2)(sin⁻¹x)² + C (b) (−1/2)(sin⁻¹x)² + C (c) 2(sin⁻¹x)² + C (d) −2(sin⁻¹x)² + C"),
    _q(80, "A", 1, "integrals", "∫ from −π/2 to π/2 of (x⁵ + xcosx + sin⁷x + 1) dx = (a) π (b) 0 (c) 2 (d) 1"),
    _q(81, "A", 1, "three-dimensional-geometry", "यदि एक रेखा x, y तथा z-अक्षों की धनात्मक दिशा के साथ क्रमशः 30°, 60° तथा 90° का कोण बनाती है। तो दिक्-कोसाइन हैं (a) 0, 1, 0 (b) 1/√14, 2/√14, 3/√14 (c) 3/5, 4/5, 0 (d) √3/2, 1/2, 0"),
    _q(82, "A", 1, "three-dimensional-geometry", "दो रेखाओं का दिक्-अनुपात क्रमशः a₁, b₁, c₁ तथा a₂, b₂, c₂ है। दोनों रेखाएँ समांतर होंगी, यदि (a) a₁a₂ + b₁b₂ + c₁c₂ = 0 (b) a₁/a₂ + b₁/b₂ + c₁/c₂ = 0 (c) a₁a₂ + b₁b₂ + c₁c₂ = 1 (d) a₁/a₂ ≠ b₁/b₂ = c₁/c₂"),
    _q(83, "A", 1, "three-dimensional-geometry", "समतल r⃗·(2î + 3ĵ − 6k̂) + 1 = 0 पर मूल बिन्दु से डाले गए लम्ब इकाई सदिश की दिक्-कोसाइन हैं (a) 1/√3, 1/√3, −1/√3 (b) −2/√7, −3/√7, 6/√7 (c) −2/7, −3/7, 6/7 (d) 1, 0, 0"),
    _q(84, "A", 1, "three-dimensional-geometry", "किसी सरल रेखा के दिक्-अनुपात 2, −3, 5 है। तो इसके दिक्-कोज्याएँ है (a) 2/4, −3/4, 5/4 (b) 2/√38, −3/√38, 5/√38 (c) 2/√19, −3/√19, 5/√19 (d) 2/√38, 3/√38, 5/√38"),
    _q(85, "A", 1, "three-dimensional-geometry", "तल 2x − 3y + 7z = 9 के समांतर तल का समीकरण है (a) 2x − 3y + 7z = 23 (b) 2x + 3y + 7z = 9 (c) 3x + 2y − 7z = 10 (d) इनमें से कोई नहीं"),
    _q(86, "A", 1, "three-dimensional-geometry", "यदि दो तल x − 3y + 2z = 10 तथा 7x + y − λz = 5 परस्पर लम्ब हों तो λ = (a) −3 (b) −2 (c) 2 (d) इनमें से कोई नहीं"),
    _q(87, "A", 1, "three-dimensional-geometry", "यदि रेखाएँ (x + 1)/a = (y − 2)/b = (z − 3)/c तथा (x − 2)/3 = (y − 5)/1 = (z − 6)/2 समांतर हो तो (a) 3a + b + 2c = 0 (b) 3/a = 1/b = 2/c (c) 3a = b = 2c (d) इनमें से कोई नहीं"),
    _q(88, "A", 1, "three-dimensional-geometry", "तलों 4x + 8y + z − 3 = 0 तथा y + z − 7 = 0 के बीच का कोण है (a) π/2 (b) 0 (c) π/3 (d) π/4"),
    _q(89, "A", 1, "three-dimensional-geometry", "बिन्दु (0, 0, 1) से तल 2x − y + z = 7 की दूरी है (a) 6√6 (b) √6 (c) 7/√6 (d) 3"),
    _q(90, "A", 1, "matrices", "2[3 7; 1 −2] + 5[1 3; 0 4] = (a) [11 29; 2 16] (b) [29 11; 2 16] (c) [11 29; 2 −16] (d) [29 11; −2 −16]"),
    _q(91, "A", 1, "matrices", "यदि [2 −1 0; 7 3 5] तो A' = (a) [2 3; −1 7; 0 5] (b) [2 0; −1 7; 3 5] (c) [2 7; −1 3; 0 5] (d) [2 7; −1 3; 0 4]"),
    _q(92, "A", 1, "determinants", "यदि |x + 1 3; 5 x − 1| = 0 तो x = (a) ±16 (b) ±4 (c) 16 (d) 0"),
    _q(93, "A", 1, "continuity-and-differentiability", "(d/dx)(cosec⁻¹x) = (a) 1/√(x² − 1) (b) 1/(x√(x² − 1)) (c) −1/(x√(x² − 1)) (d) −1/(x√(1 − x²))"),
    _q(94, "A", 1, "continuity-and-differentiability", "(d/dx) log(secx) = (a) −tanx (b) cotx (c) −cotx (d) tanx"),
    _q(95, "A", 1, "matrices", "यदि A = [1 0; 0 1] तो A⁻¹ = (a) [0 0; 1 1] (b) [0 1; 1 0] (c) [0 1; 0 1] (d) [1 0; 0 1]"),
    _q(96, "A", 1, "integrals", "∫((x³ − x² + x − 1)/(x² + 1))dx = (a) x²/2 − x + C (b) x − x²/2 + C (c) 1 − x + C (d) x²/2 + x + C"),
    _q(97, "A", 1, "integrals", "∫e^(−7x)dx = (a) −7e^(−7x) + C (b) (−1/7)e^(−7x) + C (c) (1/7)e^(−7x) + C (d) (−1/7)e^(7x) + C"),
    _q(98, "A", 1, "continuity-and-differentiability", "(d/dx)(3x² − cosx + 2) = (a) 2x + sinx (b) 6x − sinx (c) 6x + sinx (d) sinx − 6x"),
    _q(99, "A", 1, "integrals", "∫(5x⁴ + 2x + sinx)dx = (a) x⁵ + x² + cosx + C (b) x⁵ + 2 − cosx + C (c) x⁵ + x² − cosx + C (d) x⁴ + x² − cosx + C"),
    _q(100, "A", 1, "continuity-and-differentiability", "(d/dx)(e^(logx²)) = (a) 1/logx² (b) 2x (c) 2x/logx² (d) 2/x"),
    _q(1, "B", 2, "three-dimensional-geometry", "X-अक्ष से बिन्दु (a, b, c) की दूरी ज्ञात कीजिए।"),
    _q(2, "B", 2, "three-dimensional-geometry", "बिन्दु (3, 0, 0), (0, −1, 0) तथा (0, 0, 2) से गुजरने वाले तल का समीकरण ज्ञात कीजिए।"),
    _q(3, "B", 2, "three-dimensional-geometry", "मूलबिन्दु से एक तल पर डाले गए लम्ब की पाद का निर्देशांक (2, −1, 3) है। उस तल का समीकरण ज्ञात कीजिए।"),
    _q(4, "B", 2, "probability", "यदि A तथा B दो घटनाएँ इस प्रकार है कि P(A) = 1/2, P(B) = 1/3 तथा P(A ∩ B) = 1/4 तो निम्नलिखित को ज्ञात कीजिए। (i) P(A'/B) (ii) P(A'/B')"),
    _q(5, "B", 2, "probability", "एक यादृच्छिक चर x का प्रायिकता बंटन निम्नलिखित है। X: 0.5, 1, 1.5, 2; P(X): K, K², 2K², K. (i) K का मान ज्ञात करें। (ii) बंटन का माध्य ज्ञात करें।"),
    _q(6, "B", 2, "inverse-trigonometric-functions", "यदि cos⁻¹α + cos⁻¹β + cos⁻¹γ = 3π तो α(β + γ) + β(γ + α) + γ(α + β) का मान ज्ञात करें।"),
    _q(7, "B", 2, "inverse-trigonometric-functions", "tan⁻¹(−1/√3) + cot⁻¹(1/√3) + tan⁻¹[sin(−π/2)] का मान ज्ञात कीजिए।"),
    _q(8, "B", 2, "inverse-trigonometric-functions", "समीकरण cos(tan⁻¹x) = sin(cot⁻¹(3/4)) को हल कीजिए।"),
    _q(9, "B", 2, "integrals", "समाकलन करें: ∫(x² + 2)/(x + 1) dx"),
    _q(10, "B", 2, "integrals", "समाकलन करें: ∫ dx/(1 + cosx)"),
    _q(11, "B", 2, "integrals", "यदि ∫₀^a (1/(1 + 4x²)) dx = π/8 तो a का मान ज्ञात करें।"),
    _q(12, "B", 2, "integrals", "समाकलन करें: ∫ sinx/(3 + 4cos²x) dx"),
    _q(13, "B", 2, "integrals", "समाकलन करें: ∫ (sin⁶x + cos⁶x)/(sin²x cos²x) dx"),
    _q(14, "B", 2, "integrals", "समाकलन करें: ∫₂⁸ |x − 5| dx"),
    _q(15, "B", 2, "integrals", "समाकलन करें: ∫ from −π/4 to π/4 of sin²x dx"),
    _q(16, "B", 2, "vector-algebra", "यदि a⃗ = î + ĵ + 2k̂ तथा b⃗ = 2î + ĵ + 2k̂ तो सदिश (2a⃗ − b⃗) की दिशा में इकाई सदिश ज्ञात कीजिए।"),
    _q(17, "B", 2, "vector-algebra", "सदिश v⃗ ज्ञात कीजिए। जो कि (2î − ĵ + 2k̂) तथा (4î − ĵ + 3k̂) पर लम्ब है। तथा |v⃗| = 6"),
    _q(18, "B", 2, "vector-algebra", "यदि a⃗, b⃗, c⃗ इकाई सदिश है। तथा a⃗ + b⃗ + c⃗ = 0⃗ तो a⃗·b⃗ + b⃗·c⃗ + c⃗·a⃗ का मान ज्ञात कीजिए।"),
    _q(19, "B", 2, "continuity-and-differentiability", "यदि x = 3cosθ − 2cos³θ, y = 3sinθ − 2sin³θ तो dy/dx ज्ञात कीजिए।"),
    _q(20, "B", 2, "continuity-and-differentiability", "यदि tan⁻¹(x² + y²) = K तो dy/dx ज्ञात करें।"),
    _q(21, "B", 2, "continuity-and-differentiability", "यदि y = log|(1 − x²)/(1 + x²)| तो dy/dx ज्ञात कीजिए।"),
    _q(22, "B", 2, "continuity-and-differentiability", "यदि √x + √y = 1 तो बिन्दु (1/4, 1/4) पर dy/dx ज्ञात करें।"),
    _q(23, "B", 2, "application-of-derivatives", "यदि वक्र ay + x² = 7 तथा x³ = y एक दूसरे का बिन्दु (1, 1) पर लम्बवत काटते हैं तो a का मान ज्ञात करें।"),
    _q(24, "B", 2, "application-of-derivatives", "अंतराल ज्ञात करें जिसमें फलन f(x) = 2x³ + 9x² + 12x − 1 ह्रासमान है।"),
    _q(25, "B", 2, "differential-equations", "अवकल समीकरण (1 − x²)(dy/dx) − xy = 1 का समाकलन गुणक ज्ञात करें।"),
    _q(26, "B", 2, "differential-equations", "हल करें: dy/dx + y = e^(−x)"),
    _q(27, "B", 2, "matrices", "यदि A = [2 −1 0; 3 4 5] तथा B = [7 −1; 2 3; 5 0] तो (AB)' ज्ञात कीजिए।"),
    _q(28, "B", 2, "matrices", "आव्यूह A = [3 2; 5 −1] का व्युत्क्रम आव्यूह ज्ञात करें।"),
    _q(29, "B", 2, "determinants", "हल करें: |x² − x + 1, x − 1; x + 1, x + 1| = 2"),
    _q(30, "B", 2, "relations-and-functions", "यदि f(x) = 4 − (x − 7)³ तो f⁻¹(x) ज्ञात कीजिए।"),
    _q(31, "B", 5, "inverse-trigonometric-functions", "सिद्ध करें कि sin⁻¹(5/13) + cos⁻¹(3/5) = tan⁻¹(63/16)"),
    _q(32, "B", 5, "integrals", "हल करें: ∫₀¹ x log(1 + 2x) dx"),
    _q(33, "B", 5, "differential-equations", "हल करें: (1 + tany)(dx − dy) + 2x dy = 0"),
    _q(34, "B", 5, "application-of-derivatives", "वक्र 3x² − y² = 8 पर अभिलम्ब रेखाओं का समीकरण ज्ञात करें जो कि रेखा x + 3y = 4 के समांतर है।"),
    _q(35, "B", 5, "vector-algebra", "यदि a⃗ = î − ĵ + k̂ तथा b⃗ = ĵ − k̂ तो c⃗ ज्ञात करें ताकि a⃗ × c⃗ = b⃗ तथा a⃗·c⃗ = 3"),
    _q(36, "B", 5, "linear-programming", "z = 13x − 15y का न्यूनतमीकरण करें जबकि x + y ≤ 7, 2x − 3y + 6 ≥ 0, x ≥ 0 तथा y ≥ 0."),
    _q(37, "B", 5, "probability", "पासों के एक जोड़े को तीन बार उछालने पर द्विकों की संख्या का प्रायिकता बंटन ज्ञात कीजिए।"),
    _q(38, "B", 5, "matrices", "आव्यूह विधि से निम्नाकित रैखिक समीकरणों का हल करें। 2x + 3y + 3z = 5, x − 2y + z = −4, 3x − y − 2z = 3."),
]
_BSEB12_2025_HI = _BSEB12_2025_HI_A + _BSEB12_2025_HI_B

# Wave 66: Maharashtra Board (MSBSHSE) SSC Class 10
# Mathematics (71) Algebra — Part I, March 2025, code
# N 819, English medium version (E). The AglaSem document
# binds the English paper (N 819) and the Marathi paper
# (N 820) in one PDF; the English text is a clean digital
# text layer, spot-verified against the page images (Q1(A)
# options and the Q5 pie-diagram values O 45%, A 20%,
# B 30%, AB 5%). Max. Marks 40, Time 2 Hours, all questions
# compulsory. Each numbered question is stored as one
# question with its (A)/(B) parts in the text; sections A-E
# below are the paper's Questions 1-5. Maharashtra's
# Algebra syllabus includes determinants and financial
# planning (GST/shares), which are not CBSE Class 10
# chapters; those questions carry the descriptive slugs
# "determinants" and "financial-planning" (the practice
# generator only draws CBSE slugs, as with the ISC paper).
_MH10ALG_2025_EN = [
    _q(1, "A", 8, "determinants", "(A) Choose the correct alternative from given: (i) |1 2; 3 4|. Write the degree of the given determinant. (A) 1 (B) 2 (C) 3 (D) 4 (ii) From the following equations which one is the quadratic equation? (A) 5/x − 3 = x² (B) x(x + 5) = 2 (C) n − 1 = 2n (D) (1/x²)(x + 2) = x (iii) Find the common difference of the following A.P.: 4, 4, 4, ... (A) 1 (B) 8 (C) 4 (D) 0 (iv) Which number cannot represent a probability? (A) 2/3 (B) 15/10 (C) 15% (D) 0.7 (B) Solve the following subquestions: (i) If 2x + y = 7 and x + 2y = 11, then find the value of x + y. (ii) Find the first term of the given sequence: t_n = 3n – 4. (iii) How many alpha numerals are there in the format of GSTIN? (iv) Two coins are tossed simultaneously. Write the sample space S."),
    _q(2, "B", 12, "pair-of-linear-equations", "(A) Complete and write any two activities from the following: (i) Complete the following table to draw the graph of x + 2y = 4. Activity: x = –2, …; y = …, 1; (x, y) = … (ii) Complete the following activity to form a quadratic equation. Activity: I am a quadratic equation. My standard form is ______. My roots are 5 and 12. Sum of my roots ______. Product of my roots ______. My quadratic equation is ______. (iii) Pushpmala has invested ₹ 24,000 and purchased share of FV ₹ 20 at a premium of ₹ 4. Complete the following activity to find the number of shares she purchased. Activity: FV = ₹ 20, Premium = ₹ 4, MV = FV + ______ = 20 + ______ = ₹ 24, Number of shares = Total investment / MV = 24,000 / ______ = ______ shares. (B) Solve any four subquestions from the following: (i) Solve the following simultaneous equations: x + y = 3; 3x – 2y = 4 (ii) Solve the following quadratic equation by factorisation method: m² + 14m + 13 = 0 (iii) Find the 19th term of the following A.P.: 7, 13, 19, 25, ... (iv) A share is sold for the market value of ₹ 2,000. Brokerage is paid at the rate of 0.5%. What is the amount received after the sale? (v) The following table shows the number of students and the time they utilized daily for their studies. Find the mean time spent by the students for their studies. Class (Time in hours): 0–2, 2–4, 4–6, 6–8, 8–10; Class Marks (x_i): 1, 3, 5, 7, 9; No. of Students (f_i): 8, 14, 18, 10, 10; f_i x_i: 08, 42, 90, 70, 90"),
    _q(3, "C", 9, "financial-planning", "(A) Complete and write any one activity from the following: (i) Shri Maniklal has purchased 300 shares of F.V. ₹ 100, for M.V. ₹ 120. Company has paid dividend at 7%. Complete the following activity to find the rate of return on his investment. Activity: F.V. = ₹ 100, Number of shares = 300, Market value = ₹ 120 (a) Sum invested = M.V. × No. of shares = ______ × ______ = ₹ 36,000 (b) Dividend per share = F.V. × rate of dividend = ______ × (7/100) = ₹ 7, Total dividend received = 300 × 7 = ₹ ______ (c) Rate of return = (Dividend income / Sum invested) × 100 = (2,100 / 36,000) × 100 = ______%. (ii) A two digit number is to be formed from the digits 2, 3, 5 without repetition of the digits. Complete the following activity to find the probability that the number so formed is an odd number. Activity: Let S be the sample space. S = {23, 25, 32, ______, 52, 53}, n(S) = ______. Event A: The number so formed is an odd number. A = {23, 25, ______, 53}, n(A) = 4, P(A) = ______ / n(S) (Formula), P(A) = ______ / 6, P(A) = ______ / 3. (B) Solve any two subquestions from the following: (i) Solve the following simultaneous equations by Cramer's rule: 4x + 3y = 18; 3x – 2y = 5 (ii) Solve the following quadratic equation by using formula method: x² – 2x – 3 = 0 (iii) A committee of two members is to be formed from three boys and two girls. Find the probability of the following events: Event A: At least one girl must be a member of the committee. Event B: Committee must be of one boy and one girl. (iv) In a general store the prices of different articles and its demand is shown in the following frequency distribution table. Find the Median of the prices. Price in Rupees: Less than 20, 20—40, 40—60, 60—80, 80—100; No. of Articles: 140, 100, 80, 60, 20"),
    _q(4, "D", 8, "quadratic-equations", "Solve any two subquestions from the following: (i) Find the value of 'm' if the quadratic equation (m – 12)x² + 2(m – 12)x + 2 = 0 has real and equal roots. (ii) A farmer borrows ₹ 1,000 and agrees to repay with a total interest of ₹ 140, in 12 instalments. Each instalment being less than the preceding instalment by ₹ 10. What should be the amount of his first and last instalment? (iii) The following table shows the marks of 180 students in Mathematics. Marks: 0—10, 10—20, 20—30, 30—40, 40—50; No. of Students: 25, x, 30, 2x, 65. Find the value of 'x' and draw histogram."),
    _q(5, "E", 3, "pair-of-linear-equations", "Solve any one of the following subquestions: (i) Draw the graphs representing the equation 2x = y + 2 and 4x + 3y = 24 on the same graph paper. Find the area of the triangle formed by these lines and the X-axis. (ii) The following pie-diagram shows percentage of persons according to blood group in a blood group checking camp (O 45%, A 20%, B 30%, AB 5% in the printed pie-diagram). Answer the following questions: (a) Find the measure of central angle for each blood group. (b) Find the total number of persons, if there are 600 persons of blood group B."),
]

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
                "layout; Q13 |b| = √2/3 — the radical over the 2 is "
                "dropped in both OCR text versions (fraction shows as 2 "
                "over 3), read as the standard printed form; Q26 OR "
                "— denominator read as a³ - 3ax² and bounds as -a/√3 < x < "
                "a/√3 (exponents/radicals garbled in OCR). Wave 66 "
                "verified three readings against the printed page "
                "images and corrected them: Q11's bracket carries an "
                "outer square, [1 + (dy/dx)²]² = d²y/dx²; Q23's "
                "fraction carries a square root and its lower bound "
                "is printed without a minus sign (π/4 < x < π/4, an "
                "evident misprint kept as printed); Q30's integrand "
                "is √tan x. Q36 — the variable x is defined only in "
                "the printed figure (labels D, R, O, R, x, A, B, C), not in "
                "the text. Q19 Reason and Q20 Reason are transcribed "
                "exactly as printed, even though both statements are "
                "mathematically odd as printed.",
        "questions": _HBSE12_2024,
    },
    {
        "id": 'cbse-12-2024-hindi',
        "class_num": 12,
        "board": "CBSE",
        "year": 2024,
        "set_label": 'Q.P. Code 65/1/1 · Series PQ1RS/1 · Set 1',
        "subject_label": 'गणित',
        "medium": "hindi",
        "source_name": 'CBSE Class 12 Mathematics Question Paper 2024 — Hindi medium (AglaSem Docs)',
        "source_url": 'https://docs.aglasem.com/view/5fe0302c-9cfd-11ef-a3b5-0a5e36bc6706',
        "note": "Hindi-medium version of cbse-12-2024 (the same printed bilingual paper). All 38 questions transcribed from the Hindi half of the paper, read from the source's page images (its Hindi text layer is legacy-font encoded). Time allowed: 3 hours, as printed on the paper.",
        "questions": _CBSE12_2024_HI,
    },
    {
        "id": 'cbse-12-2023-hindi',
        "class_num": 12,
        "board": "CBSE",
        "year": 2023,
        "set_label": 'Q.P. Code 65/1/1 · Series EF1GH/1 · Set 1',
        "subject_label": 'गणित',
        "medium": "hindi",
        "source_name": 'CBSE Class 12 Mathematics Question Paper 2023 — Hindi medium (AglaSem Docs)',
        "source_url": 'https://docs.aglasem.com/view/de97cc22-a587-11ee-8916-0a5e36bc6706',
        "note": "Hindi-medium version of cbse-12-2023. All 38 questions transcribed from the Hindi half of the printed paper, read from the source's page images — including Q.13 and Q.15, which the English entry omits because its text source was illegible there, and Q.19 with its printed range read in full. Time allowed: 3 hours, as printed on the paper.",
        "questions": _CBSE12_2023_HI,
    },
    {
        "id": 'cbse-10-2024-hindi',
        "class_num": 10,
        "board": "CBSE",
        "year": 2024,
        "set_label": 'Q.P. Code 30/1/1 · Series C3ABD/1 · Set 1',
        "subject_label": 'गणित (मानक)',
        "medium": "hindi",
        "source_name": 'CBSE Class 10 Mathematics (Standard) Question Paper 2024 — Hindi medium (AglaSem Docs)',
        "source_url": 'https://docs.aglasem.com/view/485376b2-9cfd-11ef-9ef6-0a5e36bc6706',
        "note": "Hindi-medium version of the printed 30/1/1 paper (Series C3ABD/1). All 38 questions transcribed from the Hindi half of the paper itself, read from the source's page images — including Q.12 and Q.18, which the English entry (taken from a solved-paper source) omits. Time allowed: 3 hours, as printed on the paper.",
        "questions": _CBSE10_2024_HI,
    },
    {
        "id": 'cbse-10-2022-term2-hindi',
        "class_num": 10,
        "board": "CBSE",
        "year": 2022,
        "set_label": 'Q.P. Code 30/1/1 · Series PPQQA/1 · Set 1 · Term 2 (40 marks)',
        "subject_label": 'गणित (मानक)',
        "medium": "hindi",
        "source_name": 'CBSE Class 10 Mathematics (Standard) Question Paper 2022 Term-2 — Hindi medium (AglaSem Docs)',
        "source_url": 'https://docs.aglasem.com/view/7ee698c4-5d00-11ed-8e08-0a5e36bc6706',
        "note": "Hindi-medium version of cbse-10-2022-term2. All 14 questions transcribed from the Hindi half of the printed paper, read from the source's page images. Time allowed: 2 hours, as printed on the paper.",
        "questions": _CBSE10_2022_TERM2_HI,
    },
    {
        "id": "rbse-10-2025",
        "full_count": {"C": 4}, "full_marks": {"C": 12},
        "class_num": 10,
        "board": "RBSE (Rajasthan Board)",
        "year": 2025,
        "set_label": "S-09-Mathematics · Secondary Examination, 2025",
        "source_name": "RBSE Class 10 Mathematics Question Paper 2025 "
                       "(S-09-Mathematics), bilingual paper (full text "
                       "on AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "f9cd2e36-ea29-11f0-8aa5-0a5e36bc6706",
        "note": "All 20 questions of the paper are included (Section A "
                "holds Q.1's 18 MCQs, Q.2's 6 fill-in-the-blanks and "
                "Q.3's 12 very short answers as one stored question "
                "each, exactly as printed). The RBSE paper is "
                "bilingual — every question is printed in Hindi "
                "followed by English; this entry transcribes the "
                "English half, cross-checked against the paper's page "
                "images. Time allowed: 3 hours 15 minutes, Maximum "
                "Marks 80, as printed on the paper.",
        "section_titles": {
            "A": "Section A — Multiple Choice Questions and Very "
                 "Short Answer Type Questions",
            "B": "Section B — Short Answer Type Questions",
            "C": "Section C — Long Answer Type Questions",
            "D": "Section D — Essay Type Questions",
        },
        "questions": _RBSE10_2025,
    },
    {
        "id": "rbse-10-2025-hindi",
        "full_count": {"C": 4}, "full_marks": {"C": 12},
        "class_num": 10,
        "board": "RBSE (Rajasthan Board)",
        "year": 2025,
        "set_label": "S-09-Mathematics · Secondary Examination, 2025",
        "subject_label": "गणित",
        "medium": "hindi",
        "source_name": "RBSE Class 10 Mathematics Question Paper 2025 "
                       "(S-09-Mathematics) — Hindi medium (AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "f9cd2e36-ea29-11f0-8aa5-0a5e36bc6706",
        "note": "Hindi-medium version of rbse-10-2025 (the same "
                "printed bilingual paper). All 20 questions "
                "transcribed from the Hindi half of the paper, read "
                "from the source's page images (its Hindi text layer "
                "is legacy-font encoded). MCQ options are labelled "
                "(a)–(d) in the app's convention; the printed Hindi "
                "paper labels them (अ)–(द). Time allowed: 3 hours 15 "
                "minutes, Maximum Marks 80, as printed on the paper.",
        "section_titles_hindi": {
            "A": "बहुविकल्पीय प्रश्न एवं अति लघुत्तरात्मक प्रश्न",
            "B": "लघुत्तरात्मक प्रश्न (प्रत्येक 2 अंक)",
            "C": "दीर्घ-उत्तरीय प्रश्न (प्रत्येक 3 अंक)",
            "D": "निबंधात्मक प्रश्न (प्रत्येक 4 अंक)",
        },
        "hindi_section_letters": {"A": "अ", "B": "ब", "C": "स",
                                  "D": "द"},
        "questions": _RBSE10_2025_HI,
    },
    {
        "id": "rbse-12-2025",
        "full_count": {"C": 4}, "full_marks": {"C": 12},
        "class_num": 12,
        "board": "RBSE (Rajasthan Board)",
        "year": 2025,
        "set_label": "SS-15-Mathematics · Senior Secondary "
                     "Examination, 2025",
        "source_name": "RBSE Class 12 Mathematics Question Paper 2025 "
                       "(SS-15-Mathematics), bilingual paper (full "
                       "text on AglaSem Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "15fdd600-ea2a-11f0-8946-0a5e36bc6706",
        "note": "All 20 questions of the paper are included (Section A "
                "holds Q.1's 18 MCQs, Q.2's 6 fill-in-the-blanks and "
                "Q.3's 12 very short answers as one stored question "
                "each, exactly as printed). The RBSE paper is "
                "bilingual — every question is printed in Hindi "
                "followed by English; this entry transcribes the "
                "English half, with every formula cross-checked "
                "against the paper's page images (the text layer "
                "drops some radicals and fraction bars; Q.18's OR is "
                "∫ dx/√((x − a)(x − b)) as printed, not the text "
                "layer's unrooted form). Time allowed: 3 hours 15 "
                "minutes, Maximum Marks 80, as printed on the paper.",
        "section_titles": {
            "A": "Section A — Multiple Choice Questions and Very "
                 "Short Answer Type Questions",
            "B": "Section B — Short Answer Type Questions",
            "C": "Section C — Long Answer Type Questions",
            "D": "Section D — Essay Type Questions",
        },
        "questions": _RBSE12_2025,
    },
    {
        "id": "rbse-12-2025-hindi",
        "full_count": {"C": 4}, "full_marks": {"C": 12},
        "class_num": 12,
        "board": "RBSE (Rajasthan Board)",
        "year": 2025,
        "set_label": "SS-15-Mathematics · Senior Secondary "
                     "Examination, 2025",
        "subject_label": "गणित",
        "medium": "hindi",
        "source_name": "RBSE Class 12 Mathematics Question Paper 2025 "
                       "(SS-15-Mathematics) — Hindi medium (AglaSem "
                       "Docs)",
        "source_url": "https://docs.aglasem.com/view/"
                      "15fdd600-ea2a-11f0-8946-0a5e36bc6706",
        "note": "Hindi-medium version of rbse-12-2025 (the same "
                "printed bilingual paper). All 20 questions "
                "transcribed from the Hindi half of the paper, read "
                "from the source's page images (its Hindi text layer "
                "is legacy-font encoded). MCQ options are labelled "
                "(a)–(d) in the app's convention; the printed Hindi "
                "paper labels them (अ)–(द). Time allowed: 3 hours 15 "
                "minutes, Maximum Marks 80, as printed on the paper.",
        "section_titles_hindi": {
            "A": "बहुविकल्पीय प्रश्न, रिक्त स्थान पूर्ति एवं अति "
                 "लघुत्तरात्मक प्रश्न",
            "B": "लघुत्तरात्मक प्रश्न (प्रत्येक 2 अंक)",
            "C": "दीर्घ उत्तरात्मक प्रश्न (प्रत्येक 3 अंक)",
            "D": "निबंधात्मक प्रश्न (प्रत्येक 4 अंक)",
        },
        "hindi_section_letters": {"A": "अ", "B": "ब", "C": "स",
                                  "D": "द"},
        "questions": _RBSE12_2025_HI,
    },
    {
        "id": 'cbse-12-2022-term2-hindi',
        "class_num": 12,
        "board": "CBSE",
        "year": 2022,
        "set_label": 'Q.P. Code 65/2/1 · Series ABCD1/2 · Set 1 · '
                     'Term 2 (40 marks)',
        "subject_label": 'गणित',
        "medium": "hindi",
        "source_name": 'CBSE Class 12 Mathematics Question Paper 2022 '
                       'Term-2 — Hindi medium (AglaSem Docs)',
        "source_url": 'https://docs.aglasem.com/view/'
                      'eb06c30a-5da3-11ed-83f1-0a5e36bc6706',
        "note": "Hindi-medium version of cbse-12-2022-term2 (the same "
                "printed bilingual paper). All 14 questions "
                "transcribed from the Hindi half of the paper, read "
                "from the source's page images and cross-checked "
                "against its English half. Time allowed: 2 hours, as "
                "printed on the paper.",
        "questions": _CBSE12_2022_TERM2_HI,
    },
    {
        "id": "isc-12-2025",
        "class_num": 12,
        "board": "ISC (CISCE)",
        "year": 2025,
        "set_label": "1225-860 · T5017028 · Mathematics",
        "max_marks": 80,
        "max_questions": 22,
        "section_titles": {
            "A": "Section A — Compulsory (65 marks)",
            "B": "Section B — 15 marks (attempt either Section B "
                 "or Section C)",
            "C": "Section C — 15 marks (attempt either Section B "
                 "or Section C)",
        },
        "source_name": "ISC Class 12 Mathematics Question Paper "
                       "2025 (CISCE), full text on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "bc54a472-f4b9-11f0-9437-0a5e36bc6706",
        "note": "The real ISC Mathematics 2025 paper (paper code "
                "1225-860, T5017028), typed in full from the source "
                "PDF's page images — its text layer scrambles "
                "fractions, matrices and integrals, so every "
                "question was read off the printed pages. Printed "
                "header: Maximum Marks 80, Time Allotted Three "
                "Hours, with an additional fifteen minutes of "
                "reading time. Section A (65 marks) is compulsory; "
                "candidates attempt ALL of Section B OR all of "
                "Section C (15 marks each) — both sections are "
                "typed here in full, and the header totals use the "
                "printed 80 marks / 22 questions rather than adding "
                "the two alternative sections together. CISCE "
                "publishes ISC papers in English only, so there is "
                "no Hindi-medium ISC paper. Q19 and Q20 are the "
                "paper's Statistics (regression) questions; they "
                "are tagged 'statistics', the ISC unit they belong "
                "to.",
        "questions": _ISC12_2025,
    },
    {
        "id": "icse-10-2025",
        "class_num": 10,
        "board": "ICSE (CISCE)",
        "year": 2025,
        "set_label": "T25 511 · Mathematics",
        "max_marks": 80,
        "section_titles": {
            "A": "Section A — 40 Marks (Attempt all questions "
                 "from this Section.)",
            "B": "Section B — 40 Marks (Attempt any four "
                 "questions from this Section.)",
        },
        "source_name": "ICSE Class 10 Mathematics Question Paper "
                       "2025 (CISCE), full text on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "9ba6f8d8-f4b9-11f0-9d04-0a5e36bc6706",
        "note": "The real ICSE Mathematics 2025 paper (code T25 "
                "511), typed in full from the source PDF; the "
                "figure questions Q1(vi) and Q1(xi) and Q4 were "
                "checked against the printed page images. Printed "
                "header: Maximum Marks 80, Time allowed: Three "
                "hours (with the first 15 minutes for reading "
                "only). Section A (40 marks) is compulsory; from "
                "Section B any four of the seven questions are to "
                "be attempted (40 marks) — all seven are typed "
                "here, and the header total uses the printed 80 "
                "marks rather than adding both sections' stored "
                "marks together. CISCE publishes ICSE papers in "
                "English only, so there is no Hindi-medium ICSE "
                "paper. ICSE questions often mix chapters; each "
                "question is tagged with the chapter of its "
                "largest part.",
        "questions": _ICSE10_2025,
    },
    {
        "id": "up-10-2025",
        "class_num": 10,
        "board": "UP Board (UPMSP)",
        "year": 2025,
        "set_label": "822 (CA) · Mathematics",
        "section_titles": {
            "A": "Section A — Multiple Choice Questions (1 mark "
                 "each, answered on OMR sheet)",
            "B": "Section B — Descriptive Questions",
        },
        "source_name": "UP Board Class 10 Mathematics Question "
                       "Paper 2025, Code 822 (CA) — English-medium "
                       "print with solutions on Collegedunia "
                       "(cross-checked on Zollege)",
        "source_url": "https://image-static.collegedunia.com/"
                      "public/image/UP_Board_Class_10_Mathematics_"
                      "822_CA_2025_5748d52b289540dcac444a474e9863"
                      "ba.pdf",
        "note": "The real UP Board (UPMSP) High School "
                "Mathematics 2025 paper, subject code 822, set "
                "(CA), English-medium print. Maximum Marks 70, "
                "Time Allowed 3 Hours, as printed. Section A has "
                "20 objective questions of 1 mark each (answered "
                "on the OMR sheet). Section B (50 marks) restarts "
                "its numbering at 1, as printed: Q1 — do all six "
                "parts, 2 marks each (12); Q2 — do any five of six "
                "parts, 4 marks each (20); Q3–Q5 — 6 marks each "
                "with internal choice. The Hindi-medium print of "
                "this same set is stored separately (up-10-2025-"
                "hindi); the two booklets genuinely differ in four "
                "places — Section A Q7 option (D), Q11 option (D) "
                "and Q15 option (B), and the sign of a point in "
                "Section B Q1(e) — and each entry follows its own "
                "medium's print (the Hindi readings were verified "
                "on high-resolution crops of the scanned booklet). "
                "Section B Q3's A.P. data (first term 5, last term "
                "64, sum 400) is the board's own printed data.",
        "questions": _UP10_2025_EN_A + _UP10_2025_EN_B,
    },
    {
        "id": "up-10-2025-hindi",
        "class_num": 10,
        "board": "UP Board (UPMSP)",
        "year": 2025,
        "set_label": "822 (CA) · Mathematics",
        "subject_label": "गणित",
        "medium": "hindi",
        "hindi_section_letters": {"A": "अ", "B": "ब"},
        "section_titles": {
            "A": "Section A — Multiple Choice Questions (1 mark "
                 "each, answered on OMR sheet)",
            "B": "Section B — Descriptive Questions",
        },
        "section_titles_hindi": {
            "A": "बहुविकल्पीय प्रश्न (प्रत्येक 1 अंक)",
            "B": "वर्णनात्मक प्रश्न",
        },
        "source_name": "UP Board Class 10 Mathematics Question "
                       "Paper 2025, Code 822 (CA) — Hindi-medium "
                       "print on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "4465e584-1ecb-11f1-8702-0a5e36bc6706",
        "note": "Hindi-medium version of up-10-2025 (UP Board "
                "High School Mathematics 2025, code 822, set CA). "
                "The source PDF is a scan of the printed booklet "
                "with no text layer, so every question was read "
                "from the page images. Maximum Marks 70. खण्ड-अ "
                "has 20 objective questions of 1 mark each; खण्ड-ब "
                "(50 marks) restarts its numbering at 1, as "
                "printed: Q1 — सभी खण्ड (6 parts × 2 = 12), Q2 — "
                "किन्हीं पाँच खण्ड (5 of 6 parts × 4 = 20), Q3–Q5 "
                "— 6 marks each with अथवा. MCQ options are "
                "labelled (a)–(d) in the app's convention; the "
                "printed paper labels them (A)–(D). The Hindi and "
                "English booklets of this set genuinely differ in "
                "four places — Section A Q7 option (D) (8 here, 18 "
                "in the English print), Q11 option (D) (1, 2 here, "
                "12, -2 in English), Q15 option (B) (6.5 cm here, "
                "16.5 cm in English) and Section B Q1(e), where "
                "the Hindi print gives the point (5, 7) and the "
                "English print (-5, 7); the Hindi readings were "
                "verified on high-resolution crops of the scanned "
                "booklet, and each entry follows its own medium's "
                "print.",
        "questions": _UP10_2025_HI_A + _UP10_2025_HI_B,
    },
    {
        "id": "up-12-2025",
        "class_num": 12,
        "board": "UP Board (UPMSP)",
        "year": 2025,
        "set_label": "324 (IX) · Mathematics",
        "section_titles": {
            "A": "Section A — Complete Paper (9 questions, no "
                 "sections in the original)",
        },
        "source_name": "UP Board Class 12 Mathematics Question "
                       "Paper 2025, Code 324 (IX) — English-medium "
                       "print with solutions on Collegedunia",
        "source_url": "https://image-static.collegedunia.com/"
                      "public/image/UP_Board_Class_12_Mathematics_"
                      "324_IX_2025_1efe58f52b4c47122b33021a3d4890f"
                      "9.pdf",
        "note": "The real UP Board (UPMSP) Intermediate "
                "Mathematics 2025 paper, subject code 324, set "
                "(IX), English-medium print. Maximum Marks 100, "
                "Time Allowed 3 Hours (plus 15 minutes reading "
                "time), nine questions, all compulsory, with no "
                "section divisions — the questions are stored "
                "under a single section heading for that reason. "
                "Marks follow the board's printed pattern: Q1 — "
                "five objective parts of 1 mark each (5); Q2 — "
                "five parts of 1 mark each (5); Q3 and Q4 — four "
                "parts of 2 marks each (8 each); Q5 and Q6 — five "
                "parts of 5 marks each (25 each); Q7, Q8 and Q9 — "
                "8 marks each, attempt any one of the two parts. "
                "Every question was cross-checked against the "
                "Hindi-medium print of the same set (stored "
                "separately as up-12-2025-hindi). In Q1(d) the "
                "exponent is 1/3, verified on the printed Hindi "
                "booklet; the solved-paper sites' worked answer "
                "for that part does not match the printed paper.",
        "questions": _UP12_2025_EN,
    },
    {
        "id": "up-12-2025-hindi",
        "class_num": 12,
        "board": "UP Board (UPMSP)",
        "year": 2025,
        "set_label": "324 (IX) · Mathematics",
        "subject_label": "गणित",
        "medium": "hindi",
        "hindi_section_letters": {"A": "अ"},
        "section_titles": {
            "A": "Section A — Complete Paper (9 questions, no "
                 "sections in the original)",
        },
        "section_titles_hindi": {
            "A": "सम्पूर्ण प्रश्न-पत्र (9 प्रश्न, मूल पत्र में "
                 "खण्ड नहीं हैं)",
        },
        "source_name": "UP Board Class 12 Mathematics Question "
                       "Paper 2025, Code 324 (IX) — Hindi-medium "
                       "print on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "5951f5f0-1ecb-11f1-8f81-0a5e36bc6706",
        "note": "Hindi-medium version of up-12-2025 (UP Board "
                "Intermediate Mathematics 2025, code 324, set IX). "
                "The source PDF is a scan of the printed booklet "
                "with no text layer, so every question was read "
                "from the page images and cross-checked against "
                "the English-medium print of the same set. Maximum "
                "Marks 100; the paper has nine questions and no "
                "section divisions, so the questions are stored "
                "under a single section heading. Marks: Q1 — पाँच "
                "वस्तुनिष्ठ खण्ड × 1 = 5; Q2 — पाँच खण्ड × 1 = 5; "
                "Q3, Q4 — चार खण्ड × 2 = 8 each; Q5, Q6 — पाँच खण्ड "
                "× 5 = 25 each; Q7, Q8, Q9 — कोई एक खण्ड, 8 marks "
                "each. MCQ options are labelled (a)–(d) in the "
                "app's convention; the printed paper labels them "
                "(A)–(D). In Q1(घ) the exponent is 1/3, verified "
                "on a high-resolution crop of the printed page.",
        "questions": _UP12_2025_HI,
    },
    {
        "id": "hbse-10-2024-hindi",
        "class_num": 10,
        "board": "HBSE (Haryana Board)",
        "year": 2024,
        "set_label": "Code No. 1103 · Set A · Mathematics "
                     "(Standard)",
        "subject_label": "गणित (मानक)",
        "medium": "hindi",
        "hindi_section_letters": {"A": "क", "B": "ख", "C": "ग",
                                  "D": "घ", "E": "ङ"},
        "section_titles": {
            "A": "Section A — Questions 1–20 (1 mark each)",
            "B": "Section B — Very Short Answer Questions (2 "
                 "marks each)",
            "C": "Section C — Short Answer Questions (3 marks "
                 "each)",
            "D": "Section D — Long Answer Questions (5 marks "
                 "each)",
            "E": "Section E — Case Study Based Questions (4 "
                 "marks each)",
        },
        "section_titles_hindi": {
            "A": "प्रश्न 1–20 (प्रत्येक 1 अंक; प्रश्न 1–18 "
                 "बहुविकल्पीय/वस्तुनिष्ठ, प्रश्न 19–20 "
                 "अभिकथन-कारण आधारित)",
            "B": "अति लघु उत्तरीय प्रश्न (प्रत्येक 2 अंक)",
            "C": "लघु उत्तरीय प्रश्न (प्रत्येक 3 अंक)",
            "D": "दीर्घ उत्तरीय प्रश्न (प्रत्येक 5 अंक)",
            "E": "प्रकरण अध्ययन आधारित प्रश्न (प्रत्येक 4 अंक)",
        },
        "source_name": "HBSE Class 10 Mathematics (Standard) "
                       "Question Paper 2024, Code No. 1103, Set "
                       "A — Hindi text of the bilingual booklet "
                       "on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "2479a438-eea5-11ef-bd5f-0a5e36bc6706",
        "note": "Hindi-medium text of hbse-10-2024. The HBSE "
                "booklet is a single bilingual paper (Hindi and "
                "English Medium, printed on the cover); the "
                "English text is stored separately as "
                "hbse-10-2024. The source PDF's Hindi text layer "
                "is a legacy-font encoding, so the Hindi "
                "questions were read from the page images of the "
                "scan and checked question by question against "
                "the English text printed beside them. Maximum "
                "Marks 80, Time Allowed 3 hours, 38 questions — "
                "all present. MCQ options are labelled (a)–(d) "
                "in the app's convention; the printed paper "
                "labels them (A)–(D). In Q22 and Q34 the printed "
                "Hindi refers to a figure (आकृति में) in words "
                "the sheet's Hindi figure-marker does not match, "
                "so those two questions show no [Figure] marker "
                "here although the English entry marks them; Q37 "
                "depends on the printed park grid, whose "
                "positions are noted inside the question.",
        "questions": _HBSE10_2024_HI,
    },
    {
        "id": "hbse-12-2024-hindi",
        "class_num": 12,
        "board": "HBSE (Haryana Board)",
        "year": 2024,
        "set_label": "Code No. 1232 · Set A · Mathematics",
        "subject_label": "गणित",
        "medium": "hindi",
        "hindi_section_letters": {"A": "अ", "B": "ब", "C": "स",
                                  "D": "द", "E": "ध"},
        "section_titles": {
            "A": "Section A — Questions 1–20 (1 mark each)",
            "B": "Section B — Questions 21–25 (2 marks each)",
            "C": "Section C — Questions 26–31 (3 marks each)",
            "D": "Section D — Questions 32–35 (5 marks each)",
            "E": "Section E — Questions 36–38 (4 marks each)",
        },
        "section_titles_hindi": {
            "A": "प्रश्न 1–20 (प्रत्येक 1 अंक)",
            "B": "प्रश्न 21–25 (प्रत्येक 2 अंक)",
            "C": "प्रश्न 26–31 (प्रत्येक 3 अंक)",
            "D": "प्रश्न 32–35 (प्रत्येक 5 अंक)",
            "E": "प्रश्न 36–38 (प्रत्येक 4 अंक)",
        },
        "source_name": "HBSE Class 12 Mathematics Question "
                       "Paper 2024, Code No. 1232, Set A — Hindi "
                       "text of the bilingual booklet on "
                       "AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "5169be2e-eea5-11ef-bf8b-0a5e36bc6706",
        "note": "Hindi-medium text of hbse-12-2024. The HBSE "
                "booklet is a single bilingual paper (Hindi and "
                "English Medium, printed on the cover); the "
                "English text is stored separately as "
                "hbse-12-2024. The source PDF's Hindi text layer "
                "is a legacy-font encoding, so the Hindi "
                "questions were read from the page images of the "
                "scan and checked question by question against "
                "the English text printed beside them. Maximum "
                "Marks 80, Time Allowed 3 hours, 38 questions — "
                "all present. MCQ options are labelled (a)–(d) "
                "in the app's convention; the printed paper "
                "labels them (A)–(D). Reading the printed pages "
                "settled three readings the English entry had "
                "flagged as provisional, and the English entry "
                "has been corrected to match: Q11's bracket "
                "carries an outer square ([1 + (dy/dx)²]² = "
                "d²y/dx²); Q23's fraction carries a square root "
                "and its lower bound is printed without a minus "
                "sign (π/4 < x < π/4, an evident misprint kept "
                "as printed); Q30's integrand is √tan x, not "
                "tan x. Q19's Reason is transcribed exactly as "
                "printed even though it states the transitive "
                "property under the name 'reflexive', and Q36's "
                "variable x is defined only in the printed "
                "figure, as noted inside the question.",
        "questions": _HBSE12_2024_HI,
    },
    {
        "id": "mpbse-10-2025",
        "class_num": 10,
        "board": "MP Board (MPBSE)",
        "year": 2025,
        "set_label": "102513 · Set A · High School Examination "
                     "(Main)",
        "section_titles": {
            "A": "Section A — Complete Paper (23 questions, no "
                 "sections in the original)",
        },
        "source_name": "MP Board Class 10 Mathematics Question "
                       "Paper 2025, Code 102513, Set A — "
                       "English version of the bilingual booklet "
                       "on AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "b34ee1ac-dfca-11f0-9a87-0a5e36bc6706",
        "note": "The real MP Board (MPBSE) High School "
                "Examination (Main) 2025 Mathematics paper, code "
                "102513, Set A. Maximum Marks 75, Time 3 Hours, "
                "23 questions, all compulsory, with no section "
                "divisions — the questions are stored under a "
                "single section heading for that reason. Q1–Q5 "
                "are objective bundles of six 1-mark parts each "
                "(6 marks each); Q6–Q17 carry 2 marks, Q18–Q20 "
                "carry 3 marks and Q21–Q23 carry 4 marks, every "
                "one of Q6–Q23 with an internal choice — 75 marks "
                "in all, as printed on the paper. The booklet "
                "prints the Hindi and English versions together; "
                "both were read from the page images of the scan "
                "(the PDF has no text layer) and cross-checked "
                "against each other. The Hindi text is stored "
                "separately as mpbse-10-2025-hindi; the booklet "
                "itself states that in case of any discrepancy "
                "the Hindi version is to be treated as final.",
        "questions": _MP10_2025_EN,
    },
    {
        "id": "mpbse-10-2025-hindi",
        "class_num": 10,
        "board": "MP Board (MPBSE)",
        "year": 2025,
        "set_label": "102513 · Set A · High School Examination "
                     "(Main)",
        "subject_label": "गणित",
        "medium": "hindi",
        "hindi_section_letters": {"A": "अ"},
        "section_titles": {
            "A": "Section A — Complete Paper (23 questions, no "
                 "sections in the original)",
        },
        "section_titles_hindi": {
            "A": "सम्पूर्ण प्रश्न-पत्र (23 प्रश्न, मूल पत्र में "
                 "खण्ड नहीं हैं)",
        },
        "source_name": "MP Board Class 10 Mathematics Question "
                       "Paper 2025, Code 102513, Set A — Hindi "
                       "version of the bilingual booklet on "
                       "AglaSem Docs",
        "source_url": "https://docs.aglasem.com/view/"
                      "b34ee1ac-dfca-11f0-9a87-0a5e36bc6706",
        "note": "Hindi version of mpbse-10-2025 (MP Board High "
                "School Examination (Main) 2025, code 102513, "
                "Set A). The booklet prints both versions "
                "together and states that the Hindi version is "
                "final in case of discrepancy. Both texts were "
                "read from the page images of the scan and "
                "cross-checked. Maximum Marks 75; 23 questions "
                "with no section divisions, stored under a "
                "single section heading. Marks: Q1–Q5 — छह-छह "
                "1-अंक के भाग, 6 each; Q6–Q17 — 2 each; Q18–Q20 "
                "— 3 each; Q21–Q23 — 4 each; Q6–Q23 सभी में "
                "आंतरिक विकल्प। In Q3(vi) the Hindi print reads "
                "'दीर्घवृत्त खण्ड' where the English version "
                "says 'minor segment' — transcribed exactly as "
                "printed in each version.",
        "questions": _MP10_2025_HI,
    },    {
        "id": "bseb-10-2025",
        "class_num": 10,
        "board": "BSEB (Bihar Board)",
        "year": 2025,
        "set_label": "Subject Code 110",
        "source_name": "Bihar School Examination Board (BSEB) Secondary School Examination (Annual) 2025, Mathematics (Compulsory), Subject Code 110 — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/ffb7428c-c841-11f0-a3e6-0a5e36bc6706",
        "note": "Real printed paper: Full Marks 100, Time Allowed 3 Hours 15 Minutes (as printed on the paper), 138 questions in all. Section A has 100 objective questions of 1 mark each, of which any 50 are to be answered on the OMR sheet; Section B has Short Answer Questions 1–30 of 2 marks (answer any 15) and Long Answer Questions 31–38 of 5 marks (answer any 4), so the typed texts sum to 200 marks while the paper itself is of 100 marks. Every question is typed in full from the bilingual booklet (Hindi printed above the English for every question). Print quirks kept as printed: Q38's option (A) reads 'sinB = sinB' in both mediums; Q79's printed English option labels are garbled (the last option is labelled (E)) so the four values are stored in the clean order of the Hindi print; Q25's fraction 'becomes to 5 … becomes 7' exactly as printed. Section B Q23 and Section A Q80 carry printed figures.",
        "max_marks": 100,
        "section_titles": {
            "A": "Section A — Objective Type Questions (100 questions, answer any 50, 1 mark each)",
            "B": "Section B — Short Answer Questions 1–30 (answer any 15, 2 marks each) and Long Answer Questions 31–38 (answer any 4, 5 marks each)",
        },
        "questions": _BSEB10_2025_EN,
    },
    {
        "id": "bseb-10-2025-hindi",
        "class_num": 10,
        "board": "BSEB (Bihar Board)",
        "year": 2025,
        "set_label": "Subject Code 110",
        "medium": "hindi",
        "subject_label": "गणित (अनिवार्य)",
        "source_name": "Bihar School Examination Board (BSEB) Secondary School Examination (Annual) 2025, Mathematics (Compulsory), Subject Code 110 — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/ffb7428c-c841-11f0-a3e6-0a5e36bc6706",
        "note": "उसी द्विभाषी प्रश्न-पत्रिका का हिंदी पाठ, प्रश्न-दर-प्रश्न जैसा छपा है वैसा ही टाइप किया गया है (पूर्णांक 100, समय 3 घंटे 15 मिनट — पत्र पर छपा अनुसार)। खण्ड-अ में 100 वस्तुनिष्ठ प्रश्न (प्रत्येक 1 अंक, किन्हीं 50 के उत्तर देने हैं); खण्ड-ब में लघु उत्तरीय प्रश्न 1–30 (प्रत्येक 2 अंक, किन्हीं 15 के उत्तर) तथा दीर्घ उत्तरीय प्रश्न 31–38 (प्रत्येक 5 अंक, किन्हीं 4 के उत्तर) हैं, इसलिए टाइप किए गए प्रश्नों के अंकों का योग 200 बनता है जबकि पत्र 100 अंकों का है। विकल्प (a)–(d) में रखे गए हैं। छपाई की विचित्रताएँ यथावत रखी गई हैं: प्रश्न 38 का विकल्प (a) दोनों माध्यमों में 'sinB = sinB' ही छपा है; प्रश्न 60 के हिंदी विकल्प (b) में 'Origin' के स्थान पर 'बिन्दु' छपा है। खण्ड-ब प्रश्न 23 तथा खण्ड-अ प्रश्न 80 में छपी आकृतियाँ हैं।",
        "max_marks": 100,
        "hindi_section_letters": {"A": "अ", "B": "ब"},
        "section_titles": {
            "A": "Section A — Objective Type Questions (100 questions, answer any 50, 1 mark each)",
            "B": "Section B — Short Answer Questions 1–30 (answer any 15, 2 marks each) and Long Answer Questions 31–38 (answer any 4, 5 marks each)",
        },
        "section_titles_hindi": {
            "A": "वस्तुनिष्ठ प्रश्न (100 प्रश्न, किन्हीं 50 के उत्तर दें, प्रत्येक 1 अंक)",
            "B": "लघु उत्तरीय प्रश्न 1–30 (किन्हीं 15 के उत्तर दें, प्रत्येक 2 अंक) तथा दीर्घ उत्तरीय प्रश्न 31–38 (किन्हीं 4 के उत्तर दें, प्रत्येक 5 अंक)",
        },
        "questions": _BSEB10_2025_HI,
    },
    {
        "id": "mpbse-12-2025",
        "class_num": 12,
        "board": "MP Board (MPBSE)",
        "year": 2025,
        "set_label": "Set B · Code 202504",
        "source_name": "Board of Secondary Education, Madhya Pradesh (MPBSE) Higher Secondary Examination (Main) 2025, Higher Mathematics, Code 202504, Set B — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/d20930f2-dfca-11f0-9314-0a5e36bc6706",
        "note": "Real printed paper: Higher Secondary Examination (Main) 2025, Higher Mathematics (उच्च गणित), Maximum Marks 80, Time Allowed 3 Hours (both as printed on the paper), 23 questions, all compulsory, no printed sections. Questions 1–5 are objective bundles whose sub-questions carry 1 mark each (Q1 true/false ×6, Q2 match-the-columns ×7, Q3 one-word answers ×7, Q4 MCQs ×6, Q5 fill-in-the-blanks ×6); Questions 6–15 carry 2 marks, 16–19 carry 3 marks and 20–23 carry 4 marks, and every question from Q6 onwards has an internal choice (OR). The booklet is bilingual and itself states that the Hindi version is final in case of discrepancy; Q2(i) follows the Hindi print ∫ dx/√(x² + a²), matching column-B entry (f). Each bundle question is stored as one question with its sub-parts in the text; the chapter tag follows its lead sub-part.",
        "section_titles": {
            "A": "Complete Paper (23 questions, no sections in the original)",
        },
        "questions": _MP12_2025_EN,
    },
    {
        "id": "mpbse-12-2025-hindi",
        "class_num": 12,
        "board": "MP Board (MPBSE)",
        "year": 2025,
        "set_label": "Set B · Code 202504",
        "medium": "hindi",
        "subject_label": "उच्च गणित",
        "source_name": "Board of Secondary Education, Madhya Pradesh (MPBSE) Higher Secondary Examination (Main) 2025, Higher Mathematics, Code 202504, Set B — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/d20930f2-dfca-11f0-9314-0a5e36bc6706",
        "note": "उसी द्विभाषी प्रश्न-पत्रिका (हायर सेकण्डरी मुख्य परीक्षा वर्ष-2025, उच्च गणित, कोड 202504, सेट B) का हिंदी पाठ, प्रश्न-दर-प्रश्न जैसा छपा है वैसा ही टाइप किया गया है। पूर्णांक 80, समय 3 घंटे (पत्र पर छपा अनुसार), कुल 23 प्रश्न, सभी अनिवार्य, मूल पत्र में खण्ड नहीं हैं। प्रश्न 1–5 वस्तुनिष्ठ समूह हैं जिनके प्रत्येक उपप्रश्न पर 1 अंक है (प्र.1 सत्य/असत्य ×6, प्र.2 सही जोड़ी ×7, प्र.3 एक शब्द/वाक्य ×7, प्र.4 बहुविकल्पीय ×6, प्र.5 रिक्त स्थान ×6); प्रश्न 6–15 प्रत्येक 2 अंक, 16–19 प्रत्येक 3 अंक तथा 20–23 प्रत्येक 4 अंक के हैं, और प्रश्न 6 से आगे प्रत्येक प्रश्न में आंतरिक विकल्प (अथवा) है। पत्रिका स्वयं कहती है कि विसंगति की स्थिति में हिंदी संस्करण अंतिम माना जाएगा।",
        "hindi_section_letters": {"A": "अ"},
        "section_titles": {
            "A": "Complete Paper (23 questions, no sections in the original)",
        },
        "section_titles_hindi": {
            "A": "सम्पूर्ण प्रश्न-पत्र (23 प्रश्न, मूल पत्र में खण्ड नहीं हैं)",
        },
        "questions": _MP12_2025_HI,
    },
    {
        "id": "bseb-12-2025",
        "class_num": 12,
        "board": "BSEB (Bihar Board)",
        "year": 2025,
        "set_label": "Subject Code 121/327",
        "source_name": "Bihar School Examination Board (BSEB) Intermediate Examination (Annual) 2025, Mathematics (Elective), Subject Code 121/327, I.Sc. & I.A. — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/2ad5d64a-c842-11f0-bd1e-0a5e36bc6706",
        "note": "Real printed paper: Full Marks 100, Time Allowed 3 Hours 15 Minutes (as printed on the paper), 138 questions in all. Section A has 100 objective questions of 1 mark each, of which any 50 are to be answered on the OMR sheet; Section B has Short Answer Questions 1–30 of 2 marks (answer any 15) and Long Answer Questions 31–38 of 5 marks (answer any 4), so the typed texts sum to 200 marks while the paper itself is of 100 marks. Pure-expression questions are printed only once in the booklet and serve both mediums; verbal questions print the Hindi above the English. Print quirks kept or noted: Q14's Hindi stem prints dx/dy where the English prints dy/dx (each entry follows its own print); Q12's printed English options truncate the exponents of options (B) and (C), which are stored complete as in the Hindi print; Section B Q23's English print omits the final ask, completed from the Hindi print.",
        "max_marks": 100,
        "section_titles": {
            "A": "Section A — Objective Type Questions (100 questions, answer any 50, 1 mark each)",
            "B": "Section B — Short Answer Questions 1–30 (answer any 15, 2 marks each) and Long Answer Questions 31–38 (answer any 4, 5 marks each)",
        },
        "questions": _BSEB12_2025_EN,
    },
    {
        "id": "bseb-12-2025-hindi",
        "class_num": 12,
        "board": "BSEB (Bihar Board)",
        "year": 2025,
        "set_label": "Subject Code 121/327",
        "medium": "hindi",
        "subject_label": "गणित (ऐच्छिक)",
        "source_name": "Bihar School Examination Board (BSEB) Intermediate Examination (Annual) 2025, Mathematics (Elective), Subject Code 121/327, I.Sc. & I.A. — bilingual booklet as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/2ad5d64a-c842-11f0-bd1e-0a5e36bc6706",
        "note": "उसी द्विभाषी प्रश्न-पत्रिका का हिंदी पाठ, प्रश्न-दर-प्रश्न जैसा छपा है वैसा ही टाइप किया गया है (पूर्णांक 100, समय 3 घंटे 15 मिनट — पत्र पर छपा अनुसार)। खण्ड-अ में 100 वस्तुनिष्ठ प्रश्न (प्रत्येक 1 अंक, किन्हीं 50 के उत्तर देने हैं); खण्ड-ब में लघु उत्तरीय प्रश्न 1–30 (प्रत्येक 2 अंक, किन्हीं 15 के उत्तर) तथा दीर्घ उत्तरीय प्रश्न 31–38 (प्रत्येक 5 अंक, किन्हीं 4 के उत्तर) हैं, इसलिए टाइप किए गए प्रश्नों के अंकों का योग 200 बनता है जबकि पत्र 100 अंकों का है। शुद्ध व्यंजक-प्रश्न पत्रिका में केवल एक बार छपे हैं और दोनों माध्यमों के लिए वही पाठ है; विकल्प (a)–(d) में रखे गए हैं। प्रश्न 14 के हिंदी पाठ में dx/dy छपा है जबकि अंग्रेज़ी में dy/dx — प्रत्येक प्रविष्टि अपने छपे पाठ के अनुसार है; प्रश्न 91 के हिंदी पाठ में 'A =' छूटा हुआ छपा है, यथावत रखा गया है।",
        "max_marks": 100,
        "hindi_section_letters": {"A": "अ", "B": "ब"},
        "section_titles": {
            "A": "Section A — Objective Type Questions (100 questions, answer any 50, 1 mark each)",
            "B": "Section B — Short Answer Questions 1–30 (answer any 15, 2 marks each) and Long Answer Questions 31–38 (answer any 4, 5 marks each)",
        },
        "section_titles_hindi": {
            "A": "वस्तुनिष्ठ प्रश्न (100 प्रश्न, किन्हीं 50 के उत्तर दें, प्रत्येक 1 अंक)",
            "B": "लघु उत्तरीय प्रश्न 1–30 (किन्हीं 15 के उत्तर दें, प्रत्येक 2 अंक) तथा दीर्घ उत्तरीय प्रश्न 31–38 (किन्हीं 4 के उत्तर दें, प्रत्येक 5 अंक)",
        },
        "questions": _BSEB12_2025_HI,
    },
    {
        "id": "msbshse-10-2025-algebra",
        "class_num": 10,
        "board": "Maharashtra Board (MSBSHSE)",
        "year": 2025,
        "set_label": "Code N 819 · Algebra Part I (E)",
        "source_name": "Maharashtra State Board of Secondary and Higher Secondary Education (MSBSHSE) SSC Examination March 2025, Mathematics (71) Algebra — Part I, Code N 819, English version — as mirrored by AglaSem (docs.aglasem.com)",
        "source_url": "https://docs.aglasem.com/view/346c6b98-c9d1-11f0-a5c9-0a5e36bc6706",
        "note": "Real printed paper: Mathematics (71) Algebra — Part I (Revised Course), Max. Marks 40, Time 2 Hours (both as printed on the paper), all questions compulsory; Maharashtra splits Class 10 Maths into Algebra (Part I) and Geometry (Part II) papers — this is the Algebra paper only. The same AglaSem document also binds the Marathi-medium version of this paper (Code N 820); Maharashtra publishes in English and Marathi, not Hindi, so no Hindi-medium entry exists for this board. Each numbered question is stored as one question with its (A)/(B) parts in the text, under sections named for Questions 1–5. Q5(ii)'s pie-diagram percentages (O 45%, A 20%, B 30%, AB 5%) are given in the text so the question can be answered. Determinant and financial-planning (GST/shares) questions follow Maharashtra's own syllabus and carry descriptive chapter slugs.",
        "section_titles": {
            "A": "Question 1 — Choose the correct alternative (4 marks) and Solve the subquestions (4 marks)",
            "B": "Question 2 — Complete any two activities (4 marks) and Solve any four subquestions (8 marks)",
            "C": "Question 3 — Complete any one activity (3 marks) and Solve any two subquestions (6 marks)",
            "D": "Question 4 — Solve any two subquestions (8 marks)",
            "E": "Question 5 — Solve any one subquestion (3 marks)",
        },
        "questions": _MH10ALG_2025_EN,
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
