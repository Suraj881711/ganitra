# Wave 113 staging fragment — CBSE Class 12 Mathematics 2017, Set 65-2.
# Transcribed from the Collegedunia solutions PDF of Set 65-2 (full
# question text printed with solutions). Structure: A: Q1-4 x1,
# B: Q5-12 x2, C: Q13-23 x4, D: Q24-29 x6 = 100 marks.
# Q13(b)'s limits (1 to 4) are dropped from the question line in the
# source PDF but are stated explicitly in its solution's first step.

_CBSE12_2017 = [
    _q(1, "A", 1, "integrals", "Find: ∫ (sin^2 x − cos^2 x)/(sin x cos x) dx."),
    _q(2, "A", 1, "three-dimensional-geometry", "Find the distance between the planes 2x − y + 2z = 5 and 5x − 2.5y + 5z = 20."),
    _q(3, "A", 1, "determinants", "If for any 2 × 2 square matrix A, A(adj A) = [[8, 0], [0, 8]], then write the value of |A|."),
    _q(4, "A", 1, "continuity-and-differentiability", "Determine the value of k for which the following function is continuous at x = 3: f(x) = ((x + 3)^2 − 36)/(x − 3), x ≠ 3; f(x) = k, x = 3."),
    _q(5, "B", 2, "probability", "A die, whose faces are marked 1, 2, 3 in red and 4, 5, 6 in green, is tossed. Let A be the event 'number obtained is even' and B be the event 'number obtained is red'. Find if A and B are independent events."),
    _q(6, "B", 2, "linear-programming", "Two tailors, A and B, earn ₹300 and ₹400 per day respectively. A can stitch 6 shirts and 4 pairs of trousers while B can stitch 10 shirts and 4 pairs of trousers per day. To find how many days should each of them work and if it is desired to produce at least 60 shirts and 32 pairs of trousers at a minimum labour cost, formulate this as an LPP."),
    _q(7, "B", 2, "three-dimensional-geometry", "The x-coordinate of a point on the line joining the points P(2, 2, 1) and Q(5, 1, −2) is 4. Find its z-coordinate."),
    _q(8, "B", 2, "integrals", "Find: ∫ dx/(5 − 8x − x^2)."),
    _q(9, "B", 2, "determinants", "If A is a skew-symmetric matrix of order 3, then prove that det A = 0."),
    _q(10, "B", 2, "application-of-derivatives", "Find the value of c in Rolle's theorem for the function f(x) = x^3 − 3x in [−√3, 0]."),
    _q(11, "B", 2, "application-of-derivatives", "Show that the function f(x) = x^3 − 3x^2 + 6x − 100 is increasing on R."),
    _q(12, "B", 2, "application-of-derivatives", "The length x, of a rectangle is decreasing at the rate of 5 cm/minute and the width y, is increasing at the rate of 4 cm/minute. When x = 8 cm and y = 6 cm, find the rate of change of the area of the rectangle."),
    _q(13, "C", 4, "integrals", "(a) Evaluate: ∫ from 0 to π of x tan x/(sec x + tan x) dx. OR (b) Evaluate: ∫ from 1 to 4 of {|x − 1| + |x − 2| + |x − 4|} dx."),
    _q(14, "C", 4, "vector-algebra", "Show that the points A, B, C with position vectors 2i − j + k, i − 3j − 5k and 3i − 4j − 4k respectively, are the vertices of a right-angled triangle. Hence find the area of the triangle."),
    _q(15, "C", 4, "probability", "There are 4 cards numbered 1, 3, 5 and 7, one number on one card. Two cards are drawn at random without replacement. Let X denote the sum of the numbers on the two drawn cards. Find the mean and variance of X."),
    _q(16, "C", 4, "probability", "Of the students in a school, it is known that 30% have 100% attendance and 70% students are irregular. Previous year results report that 70% of all students who have 100% attendance attain A grade and 10% irregular students attain A grade in their annual examination. At the end of the year, one student is chosen at random from the school and he was found to have an A grade. What is the probability that the student has 100% attendance? Is regularity required only in school? Justify your answer."),
    _q(17, "C", 4, "inverse-trigonometric-functions", "If tan^(−1) ((x − 3)/(x − 4)) + tan^(−1) ((x + 3)/(x + 4)) = π/4, then find the value of x."),
    _q(18, "C", 4, "determinants", "(a) Using properties of determinants, prove that | a^2 + 2a, 2a + 1, 1; 2a + 1, a + 2, 1; 3, 3, 1 | = (a − 1)^3. OR (b) Find matrix A such that [[2, −1], [1, 0], [−3, 4]] A = [[−1, −8], [1, −2], [9, 22]]."),
    _q(19, "C", 4, "continuity-and-differentiability", "(a) If x^y + y^x = a^b, then find dy/dx. OR (b) If e^y (x + 1) = 1, then show that d^2y/dx^2 = (dy/dx)^2."),
    _q(20, "C", 4, "integrals", "Find: ∫ sin θ dθ / ((4 + cos^2 θ)(2 − sin^2 θ))."),
    _q(21, "C", 4, "linear-programming", "Solve the following linear programming problem graphically: Maximise Z = 34x + 45y under the following constraints x + y ≤ 300, 2x + 3y ≤ 70, x ≥ 0, y ≥ 0."),
    _q(22, "C", 4, "three-dimensional-geometry", "Find the value of x such that the points A(3, 2, 1), B(4, x, 5), C(4, 2, −2) and D(6, 5, −1) are coplanar."),
    _q(23, "C", 4, "differential-equations", "Find the general solution of the differential equation y dx − (x + 2y^2) dy = 0."),
    _q(24, "D", 6, "three-dimensional-geometry", "(a) Find the coordinates of the point where the line through the points (3, −4, −5) and (2, −3, 1), crosses the plane determined by the points (1, 2, 3), (4, 2, −3) and (0, 4, 3). OR (b) A variable plane which remains at a constant distance 3p from the origin cuts the coordinate axes at A, B, C. Show that the locus of the centroid of triangle ABC is 1/x^2 + 1/y^2 + 1/z^2 = 1/p^2."),
    _q(25, "D", 6, "differential-equations", "Find the particular solution of the differential equation (x − y) dy/dx = (x + 2y), given that y = 0 when x = 1."),
    _q(26, "D", 6, "application-of-integrals", "(a) Using the method of integration, find the area of the triangle ABC, coordinates of whose vertices are A(4, 1), B(6, 6) and C(8, 4). OR (b) Find the area enclosed between the parabola 4y = 3x^2 and the straight line 3x − 2y + 12 = 0."),
    _q(27, "D", 6, "relations-and-functions", "(a) Consider f : R − {−4/3} → R − {4/3} given by f(x) = (4x + 3)/(3x + 4). Show that f is bijective. Find the inverse of f and hence find f^(−1)(0) and x such that f^(−1)(x) = 2. OR (b) Let A = Q × Q and let * be a binary operation on A defined by (a, b) * (c, d) = (ac, b + ad) for (a, b), (c, d) ∈ A. Determine, whether * is commutative and associative. Then, with respect to * on A: (i) Find the identity element in A. (ii) Find the invertible elements of A."),
    _q(28, "D", 6, "application-of-derivatives", "AB is the diameter of a circle and C is any point on the circle. Show that the area of triangle ABC is maximum, when it is an isosceles triangle."),
    _q(29, "D", 6, "matrices", "If A = [[2, −3, 5], [3, 2, −4], [1, 1, −2]], find A^(−1). Hence using A^(−1) solve the system of equations 2x − 3y + 5z = 11, 3x + 2y − 4z = −5, x + y − 2z = −3."),
]

_CBSE12_2017_ENTRY = {
    "id": "cbse-12-2017",
    "class_num": 12,
    "board": "CBSE",
    "year": 2017,
    "set_label": "Set 65-2",
    "source_name": "CBSE Class 12 Mathematics Question Paper 2017, Set 65-2 (Collegedunia solutions PDF)",
    "source_url": "https://image-static.collegedunia.com/public/questions/cbse/2017/1791803585_cbse-class-12-mathematics-question-paper-2017-with-solution-pdf-set-65-2-solutions.pdf",
    "max_marks": 100,
    "full_count": {"A": 4},
    "full_marks": {"A": 4},
    "section_titles": {
        "A": "Section A (1 mark each)",
        "B": "Section B (2 marks each)",
        "C": "Section C (4 marks each)",
        "D": "Section D (6 marks each)",
    },
    "note": "The 2017 paper in the pre-2019 pattern: 29 questions, 100 marks. Q13(b)'s integral limits (1 to 4) are dropped from the question line in the source PDF and are taken from its solution, which works throughout on the interval [1, 4].",
    "questions": _CBSE12_2017,
}
