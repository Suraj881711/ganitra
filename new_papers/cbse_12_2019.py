# Wave 113 staging fragment — CBSE Class 12 Mathematics 2019 (Set 65/1/1).
# Transcribed from the AglaSem Docs text of the official paper
# (Series BVM/1, Code No. 65/1/1; 29 questions, 100 marks:
# A: Q1-4 x1, B: Q5-12 x2, C: Q13-23 x4, D: Q24-29 x6),
# cross-checked against the Collegedunia PDF of the same set.
# Q3's equation (x^2 * d2y/dx2 = [1 + (dy/dx)^2]^4) verified via Shaalaa's
# per-question page tagged 2018-2019 (March) 65/1/1 (order 2, degree 1).
# Q18's curve is y = sqrt(3x - 2): both OCR layers drop the radical sign,
# and the question is incoherent for the straight line y = 3x - 2.

_CBSE12_2019 = [
    _q(1, "A", 1, "determinants", "If A and B are square matrices of the same order 3, such that |A| = 2 and AB = 2I, write the value of |B|."),
    _q(2, "A", 1, "relations-and-functions", "If f(x) = x + 1, find d/dx [(fof)(x)]."),
    _q(3, "A", 1, "differential-equations", "Find the order and the degree of the differential equation x^2 (d^2y/dx^2) = [1 + (dy/dx)^2]^4."),
    _q(4, "A", 1, "three-dimensional-geometry", "If a line makes angles 90°, 135°, 45° with the x, y and z axes respectively, find its direction cosines. OR Find the vector equation of the line which passes through the point (3, 4, 5) and is parallel to the vector 2i + 2j − 3k."),
    _q(5, "B", 2, "relations-and-functions", "Examine whether the operation * defined on R by a * b = ab + 1 is (i) a binary operation or not. (ii) If it is a binary operation, is it associative or not?"),
    _q(6, "B", 2, "matrices", "Find a matrix A such that 2A − 3B + 5C = O, where B = [[−2, 2, 0], [3, 1, 4]] and C = [[2, 0, −2], [7, 1, 6]]."),
    _q(7, "B", 2, "integrals", "Find: ∫ sec^2 x / (tan^2 x + 4) dx."),
    _q(8, "B", 2, "integrals", "Find: ∫ from π/4 to π/2 of √(1 − sin 2x) dx. OR Find: ∫ sin^(−1) (2x) dx."),
    _q(9, "B", 2, "differential-equations", "Form the differential equation representing the family of curves y = e^(2x) (a + bx), where 'a' and 'b' are arbitrary constants."),
    _q(10, "B", 2, "vector-algebra", "If the sum of two unit vectors is a unit vector, prove that the magnitude of their difference is √3. OR If a = 2i + 3j + k, b = i − 2j + k and c = −3i + j + 2k, find [a b c]."),
    _q(11, "B", 2, "probability", "A die marked 1, 2, 3 in red and 4, 5, 6 in green is tossed. Let A be the event 'number is even' and B be the event 'number is marked red'. Find whether the events A and B are independent or not."),
    _q(12, "B", 2, "probability", "A die is thrown 6 times. If 'getting an odd number' is a 'success', what is the probability of (i) 5 successes? (ii) at most 5 successes? OR The random variable X has a probability distribution P(X) of the following form, where 'k' is some number: P(X = x) = k, if x = 0; 2k, if x = 1; 3k, if x = 2; 0, otherwise. Determine the value of 'k'."),
    _q(13, "C", 4, "relations-and-functions", "Show that the relation R on R defined as R = {(a, b) : a ≤ b}, is reflexive and transitive but not symmetric. OR Prove that the function f : N → N, defined by f(x) = x^2 + x + 1 is one-one but not onto. Find the inverse of f : N → S, where S is the range of f."),
    _q(14, "C", 4, "inverse-trigonometric-functions", "Solve: tan^(−1) 4x + tan^(−1) 6x = π/4."),
    _q(15, "C", 4, "determinants", "Using properties of determinants, prove that | a^2 + 2a, 2a + 1, 1 ; 2a + 1, a + 2, 1 ; 3, 3, 1 | = (a − 1)^3."),
    _q(16, "C", 4, "continuity-and-differentiability", "If log (x^2 + y^2) = 2 tan^(−1) (y/x), show that dy/dx = (x + y)/(x − y). OR If x^y − y^x = a^b, find dy/dx."),
    _q(17, "C", 4, "continuity-and-differentiability", "If y = (sin^(−1) x)^2, prove that (1 − x^2) (d^2y/dx^2) − x (dy/dx) − 2 = 0."),
    _q(18, "C", 4, "application-of-derivatives", "Find the equation of tangent to the curve y = √(3x − 2) which is parallel to the line 4x − 2y + 5 = 0. Also, write the equation of normal to the curve at the point of contact."),
    _q(19, "C", 4, "integrals", "Find: ∫ (3x + 5)/(x^2 + 3x − 18) dx."),
    _q(20, "C", 4, "integrals", "Prove that ∫ from 0 to a of f(x) dx = ∫ from 0 to a of f(a − x) dx, hence evaluate ∫ from 0 to π of x sin x / (1 + cos^2 x) dx."),
    _q(21, "C", 4, "differential-equations", "Solve the differential equation: x dy − y dx = √(x^2 + y^2) dx, given that y = 0 when x = 1. OR Solve the differential equation: (1 + x^2) dy/dx + 2xy − 4x^2 = 0, subject to the initial condition y(0) = 0."),
    _q(22, "C", 4, "vector-algebra", "If i + j + k, 2i + 5j, 3i + 2j − 3k and i − 6j − k respectively are the position vectors of points A, B, C and D, then find the angle between the straight lines AB and CD. Find whether AB and CD are collinear or not."),
    _q(23, "C", 4, "three-dimensional-geometry", "Find the value of λ, so that the lines (1 − x)/3 = (7y − 14)/λ = (z − 3)/2 and (7 − 7x)/(3λ) = (y − 5)/1 = (6 − z)/5 are at right angles. Also, find whether the lines are intersecting or not."),
    _q(24, "D", 6, "matrices", "If A = [[1, 1, 1], [1, 0, 2], [3, 1, 1]], find A^(−1). Hence, solve the system of equations x + y + z = 6, x + 2z = 7, 3x + y + z = 12. OR Find the inverse of the following matrix using elementary operations: A = [[1, 2, −2], [−1, 3, 0], [0, −2, 1]]."),
    _q(25, "D", 6, "application-of-derivatives", "A tank with rectangular base and rectangular sides, open at the top is to be constructed so that its depth is 2 m and volume is 8 m^3. If building of tank costs ₹70 per square metre for the base and ₹45 per square metre for the sides, what is the cost of least expensive tank?"),
    _q(26, "D", 6, "application-of-integrals", "Using integration, find the area of triangle ABC, whose vertices are A(2, 5), B(4, 7) and C(6, 2). OR Find the area of the region lying above x-axis and included between the circle x^2 + y^2 = 8x and inside of the parabola y^2 = 4x."),
    _q(27, "D", 6, "three-dimensional-geometry", "Find the vector and Cartesian equations of the plane passing through the points (2, 2, −1), (3, 4, 2) and (7, 0, 6). Also find the vector equation of a plane passing through (4, 3, 1) and parallel to the plane obtained above. OR Find the vector equation of the plane that contains the line r = (i + j) + λ(i + 2j − k) and the point (−1, 3, −4). Also, find the length of the perpendicular drawn from the point (2, 1, 4) to the plane, thus obtained."),
    _q(28, "D", 6, "probability", "A manufacturer has three machine operators A, B and C. The first operator A produces 1% of defective items, whereas the other two operators B and C produce 5% and 7% defective items respectively. A is on the job for 50% of the time, B on the job for 30% of the time and C on the job for 20% of the time. All the items are put into one stockpile and then one item is chosen at random from this and is found to be defective. What is the probability that it was produced by A?"),
    _q(29, "D", 6, "linear-programming", "A manufacturer has employed 5 skilled men and 10 semi-skilled men and makes two models A and B of an article. The making of one item of model A requires 2 hours work by a skilled man and 2 hours work by a semi-skilled man. One item of model B requires 1 hour by a skilled man and 3 hours by a semi-skilled man. No man is expected to work more than 8 hours per day. The manufacturer's profit on an item of model A is ₹15 and on an item of model B is ₹10. How many items of each model should be made per day in order to maximize daily profit? Formulate the above LPP and solve it graphically and find the maximum profit."),
]

_CBSE12_2019_ENTRY = {
    "id": "cbse-12-2019",
    "class_num": 12,
    "board": "CBSE",
    "year": 2019,
    "set_label": "Set 65/1/1",
    "source_name": "CBSE Class 12 Mathematics Question Paper 2019, Set 65/1/1 (Series BVM/1), AglaSem Docs text, cross-checked with the Collegedunia PDF of the same set; Q3 verified via Shaalaa (65/1/1)",
    "source_url": "https://docs.aglasem.com/view/b5c56222-82fb-11e9-95fc-54e1adc9033a",
    "max_marks": 100,
    "full_count": {"A": 4},
    "full_marks": {"A": 4},
    "section_titles": {
        "A": "Section A — Very Short Answer Questions (1 mark each)",
        "B": "Section B — Short Answer Questions I (2 marks each)",
        "C": "Section C — Short Answer Questions II (4 marks each)",
        "D": "Section D — Long Answer Questions (6 marks each)",
    },
    "note": "The 2019 paper followed the pre-2020 pattern: 29 questions, 100 marks (A: 4×1, B: 8×2, C: 11×4, D: 6×6). Q18's curve is printed y = √(3x − 2); both OCR text layers drop the radical sign.",
    "questions": _CBSE12_2019,
}
