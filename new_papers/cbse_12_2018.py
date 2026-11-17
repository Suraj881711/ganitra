# Wave 113 staging fragment — CBSE Class 12 Mathematics 2018 (Set 65/1).
# Transcribed from the Collegedunia solutions PDF of the official paper
# (Series SGN, Code No. 65/1; 29 questions, 100 marks:
# A: Q1-4 x1, B: Q5-12 x2, C: Q13-23 x4, D: Q24-29 x6).
# Q16 (OR) function reconstructed from the solution's derivative:
# f'(x) = (x + 3)(x - 2)(x - 4) = x^3 - 3x^2 - 10x + 24, so
# f(x) = x^4/4 - x^3 - 5x^2 + 24x + 12 (both OCR passes agree on the
# -5x^2, 24x and 12 terms).

_CBSE12_2018 = [
    _q(1, "A", 1, "inverse-trigonometric-functions", "Find the value of tan^(−1) √3 − cot^(−1) (−√3)."),
    _q(2, "A", 1, "matrices", "If the matrix A = [[0, a, −3], [2, 0, −1], [b, 1, 0]] is skew symmetric, find the values of a and b."),
    _q(3, "A", 1, "vector-algebra", "Find the magnitude of each of the two vectors a and b, having the same magnitude such that the angle between them is 60° and their scalar product is 9/2."),
    _q(4, "A", 1, "relations-and-functions", "If a * b denotes the larger of a and b and if a ◦ b = (a * b) + 3, then write the value of (5) ◦ (10), where * and ◦ are binary operations."),
    _q(5, "B", 2, "inverse-trigonometric-functions", "Prove that: 3 sin^(−1) x = sin^(−1) (3x − 4x^3), x ∈ [−1/2, 1/2]."),
    _q(6, "B", 2, "matrices", "Given A = [[2, −3], [−4, 7]], compute A^(−1) and show that 2A^(−1) = 9I − A."),
    _q(7, "B", 2, "continuity-and-differentiability", "Differentiate tan^(−1) [(1 + cos x)/sin x] with respect to x."),
    _q(8, "B", 2, "application-of-derivatives", "The total cost C(x) associated with the production of x units of an item is given by C(x) = 0.005x^3 − 0.02x^2 + 30x + 5000. Find the marginal cost when 3 units are produced, where by marginal cost we mean the instantaneous rate of change of total cost at any level of output."),
    _q(9, "B", 2, "integrals", "Evaluate: ∫ (cos 2x + 2 sin^2 x)/cos^2 x dx."),
    _q(10, "B", 2, "differential-equations", "Find the differential equation representing the family of curves y = a e^(bx + 5), where a and b are arbitrary constants."),
    _q(11, "B", 2, "vector-algebra", "If θ is the angle between two vectors i − 2j + 3k and 3i − 2j + k, find sin θ."),
    _q(12, "B", 2, "probability", "A black and a red die are rolled together. Find the conditional probability of obtaining the sum 8, given that the red die resulted in a number less than 4."),
    _q(13, "C", 4, "determinants", "Using properties of determinants, prove that | 1, 1, 1 + 3x ; 1 + 3y, 1, 1 ; 1, 1 + 3z, 1 | = 9(3xyz + xy + yz + zx)."),
    _q(14, "C", 4, "continuity-and-differentiability", "If (x^2 + y^2)^2 = xy, find dy/dx. OR If x = a(2θ − sin 2θ) and y = a(1 − cos 2θ), find dy/dx when θ = π/3."),
    _q(15, "C", 4, "continuity-and-differentiability", "If y = sin(sin x), prove that d^2y/dx^2 + tan x (dy/dx) + y cos^2 x = 0."),
    _q(16, "C", 4, "application-of-derivatives", "Find the equations of the tangent and the normal to the curve 16x^2 + 9y^2 = 145 at the point (x1, y1), where x1 = 2 and y1 > 0. OR Find the intervals in which the function f(x) = x^4/4 − x^3 − 5x^2 + 24x + 12 is (a) strictly increasing, (b) strictly decreasing."),
    _q(17, "C", 4, "application-of-derivatives", "An open tank with a square base and vertical sides is to be constructed from a metal sheet so as to hold a given quantity of water. Show that the cost of material will be least when depth of the tank is half of its width. If the cost is to be borne by nearby settled lower income families, for whom water will be provided, what kind of value is hidden in this question?"),
    _q(18, "C", 4, "integrals", "Find: ∫ 2 cos x / [(1 − sin x)(1 + sin^2 x)] dx."),
    _q(19, "C", 4, "differential-equations", "Find the particular solution of the differential equation e^x tan y dx + (2 − e^x) sec^2 y dy = 0, given that y = π/4 when x = 0. OR Find the particular solution of the differential equation dy/dx + 2y tan x = sin x, given that y = 0 when x = π/3."),
    _q(20, "C", 4, "vector-algebra", "Let a = 4i + 5j − k, b = i − 4j + 5k and c = 3i + j − k. Find a vector d which is perpendicular to both c and b and d · a = 21."),
    _q(21, "C", 4, "three-dimensional-geometry", "Find the shortest distance between the lines r = (4i − j) + λ(i + 2j − 3k) and r = (i − j + 2k) + μ(2i + 4j − 5k)."),
    _q(22, "C", 4, "probability", "Suppose a girl throws a die. If she gets 1 or 2, she tosses a coin three times and notes the number of tails. If she gets 3, 4, 5 or 6, she tosses a coin once and notes whether a 'head' or 'tail' is obtained. If she obtained exactly one 'tail', what is the probability that she threw 3, 4, 5 or 6 with the die?"),
    _q(23, "C", 4, "probability", "Two numbers are selected at random (without replacement) from the first five positive integers. Let X denote the larger of the two numbers obtained. Find the mean and variance of X."),
    _q(24, "D", 6, "relations-and-functions", "Let A = {x ∈ Z : 0 ≤ x ≤ 12}. Show that R = {(a, b) : a, b ∈ A, |a − b| is divisible by 4} is an equivalence relation. Find the set of all elements related to 1. Also write the equivalence class [2]. OR Show that the function f : R → R defined by f(x) = x/(x^2 + 1), for all x ∈ R, is neither one-one nor onto. Also, if g : R → R is defined as g(x) = 2x − 1, find fog(x)."),
    _q(25, "D", 6, "matrices", "If A = [[2, −3, 5], [3, 2, −4], [1, 1, −2]], find A^(−1). Use it to solve the system of equations 2x − 3y + 5z = 11, 3x + 2y − 4z = −5, x + y − 2z = −3. OR Using elementary row transformations, find the inverse of the matrix A = [[1, 2, 3], [2, 5, 7], [−2, −4, −5]]."),
    _q(26, "D", 6, "application-of-integrals", "Using integration, find the area of the region in the first quadrant enclosed by the x-axis, the line y = x and the circle x^2 + y^2 = 32."),
    _q(27, "D", 6, "integrals", "Evaluate: ∫ from 0 to π/4 of (sin x + cos x)/(16 + 9 sin 2x) dx. OR Evaluate ∫ from 1 to 3 of (x^2 + 3x + e^x) dx as the limit of the sum."),
    _q(28, "D", 6, "three-dimensional-geometry", "Find the distance of the point (−1, −5, −10) from the point of intersection of the line r = 2i − j + 2k + λ(3i + 4j + 2k) and the plane r · (i − j + k) = 5."),
    _q(29, "D", 6, "linear-programming", "A factory manufactures two types of screws A and B, each type requiring the use of two machines, an automatic and a hand-operated. It takes 4 minutes on the automatic and 6 minutes on the hand-operated machines to manufacture a packet of screws 'A' while it takes 6 minutes on the automatic and 3 minutes on the hand-operated machine to manufacture a packet of screws 'B'. Each machine is available for at most 4 hours on any day. The manufacturer can sell a packet of screws 'A' at a profit of 70 paise and screws 'B' at a profit of ₹1. Assuming that he can sell all the screws he manufactures, how many packets of each type should the factory owner produce in a day in order to maximize his profit? Formulate the above LPP and solve it graphically and find the maximum profit."),
]

_CBSE12_2018_ENTRY = {
    "id": "cbse-12-2018",
    "class_num": 12,
    "board": "CBSE",
    "year": 2018,
    "set_label": "Set 65/1",
    "source_name": "CBSE Class 12 Mathematics Question Paper 2018, Set 65/1 (Series SGN), Collegedunia question paper with solutions PDF",
    "source_url": "https://image-static.collegedunia.com/public/questions/cbse/2018/1791803600_cbse-class-12-mathematics-question-paper-2018-with-solution-pdf-set-65-1-solutions.pdf",
    "max_marks": 100,
    "full_count": {"A": 4},
    "full_marks": {"A": 4},
    "section_titles": {
        "A": "Section A — Very Short Answer Questions (1 mark each)",
        "B": "Section B — Short Answer Questions I (2 marks each)",
        "C": "Section C — Short Answer Questions II (4 marks each)",
        "D": "Section D — Long Answer Questions (6 marks each)",
    },
    "note": "The 2018 paper followed the pre-2020 pattern: 29 questions, 100 marks (A: 4×1, B: 8×2, C: 11×4, D: 6×6).",
    "questions": _CBSE12_2018,
}
