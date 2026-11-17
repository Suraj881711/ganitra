# Wave 113 staging fragment — CBSE Class 10 Mathematics (Basic) Term 1,
# 2021-22 (Set 4). Transcribed from the GeeksforGeeks solved-paper page
# (exam 4 Dec 2021): 50 MCQs of 1 mark each (A: Q1-20, B: Q21-40,
# C: Q41-50 in two case studies), 40 marks, attempt-any-40 pattern.
# The source page flattens superscripts and radicals (e.g. "tan245" for
# tan^2 45); they are restored in the standard way.
# Case Study II (Q46-50) depends on a printed quilt-design figure whose
# measurements are not in the text: only Q46 (conceptual) is included;
# Q47-50 are OMITTED and recorded in the entry note.

_CS1_10_T1 = (
    "Case Study-I: Sukriti throws a ball upwards, from a rooftop that is 8 m high from ground "
    "level. The ball reaches some maximum height and then returns and hits the ground. The "
    "height of the ball at time t (in sec) is represented by h (in m), and the equation of its "
    "path is given as h = −t^2 + 2t + 8. Based on the above information, answer the question."
)
_CS2_10_T1 = (
    "Case Study-II: Quilts are available in various colours and designs. The geometric design "
    "includes shapes like squares, triangles, rectangles, hexagons, etc. One such design is "
    "shown in the figure. Two triangles are highlighted, ΔABC and ΔPQR. Based on the above "
    "information, answer the question."
)

_CBSE10_2022_TERM1_BASIC = [
    _q(1, "A", 1, "real-numbers", "HCF of 92 and 152 is (a) 4 (b) 19 (c) 23 (d) 57"),
    _q(2, "A", 1, "triangles", "In ΔABC, DE || BC, AD = 4 cm, DB = 6 cm and AE = 5 cm. The length of EC is (a) 7 cm (b) 6.5 cm (c) 7.5 cm (d) 8 cm"),
    _q(3, "A", 1, "pair-of-linear-equations", "The value of k, for which the pair of linear equations x + y − 4 = 0, 2x + ky − 3 = 0 have no solution, is (a) 0 (b) 2 (c) 6 (d) 8"),
    _q(4, "A", 1, "introduction-to-trigonometry", "The value of (tan^2 45° − cos^2 60°) is (a) 1/2 (b) 1/4 (c) 3/2 (d) 3/4"),
    _q(5, "A", 1, "coordinate-geometry", "A point (x, 1) is equidistant from (0, 0) and (2, 0). The value of x is (a) 1 (b) 0 (c) 2 (d) 1/2"),
    _q(6, "A", 1, "probability", "Two coins are tossed together. The probability of getting exactly one head is (a) 1/4 (b) 1/2 (c) 3/4 (d) 1"),
    _q(7, "A", 1, "areas-related-to-circles", "A circular arc of length 22 cm subtends an angle θ at the centre of the circle of radius 21 cm. The value of θ is (a) 90° (b) 50° (c) 60° (d) 30°"),
    _q(8, "A", 1, "polynomials", "A quadratic polynomial having sum and product of its zeroes as 5 and 0 respectively, is (a) x^2 + 5x (b) 2x(x − 5) (c) 5x^2 − 1 (d) x^2 − 5x + 5"),
    _q(9, "A", 1, "probability", "If P(E) = 0.65, then the value of P(not E) is (a) 1.65 (b) 0.25 (c) 0.65 (d) 0.35"),
    _q(10, "A", 1, "triangles", "It is given that ΔDEF ~ ΔPQR. EF : QR = 3 : 2, then value of ar(DEF) : ar(PQR) is (a) 4 : 9 (b) 4 : 3 (c) 9 : 2 (d) 9 : 4"),
    _q(11, "A", 1, "polynomials", "Zeroes of a quadratic polynomial x^2 − 5x + 6 are (a) −5, 1 (b) 5, 1 (c) 2, 3 (d) −2, −3"),
    _q(12, "A", 1, "real-numbers", "57/300 is a (a) non-terminating and non-repeating decimal expansion (b) terminating decimal expansion after 2 places of decimals (c) terminating decimal expansion after 3 places of decimals (d) non-terminating but repeated decimal expansion"),
    _q(13, "A", 1, "pair-of-linear-equations", "Perimeter of a rectangle whose length (l) is 4 cm more than twice its breadth (b) is 14 cm. The pair of linear equations representing the above information is (a) l + 4 = 2b, 2(l + b) = 14 (b) l − b = 4, 2(l + b) = 14 (c) l = 2b + 4, l + b = 14 (d) l = 2b + 4, 2(l + b) = 14"),
    _q(14, "A", 1, "real-numbers", "5.213213... (5.213 with 213 recurring) can also be written as (a) 5.213213213... (b) 5.2131313... (c) 5.213 (d) 5213/1000"),
    _q(15, "A", 1, "coordinate-geometry", "The ratio in which the point (4, 0) divides the line segment joining the points (4, 6) and (4, −8) is (a) 1 : 2 (b) 3 : 4 (c) 4 : 3 (d) 1 : 1"),
    _q(16, "A", 1, "introduction-to-trigonometry", "Which of the following is not defined? (a) sec 0° (b) cosec 90° (c) tan 90° (d) cot 90°"),
    _q(17, "A", 1, "circles", "In the given figure, a circle is touching a semi-circle at C and its diameter AB at O. If AB = 28 cm, what is the radius of the inner circle? (a) 14 cm (b) 28 cm (c) 7 cm (d) 7/2 cm"),
    _q(18, "A", 1, "coordinate-geometry", "The vertices of a triangle OAB are O(0, 0), A(4, 0) and B(0, 6). The median AD is drawn on OB. The length AD is (a) √52 units (b) 5 units (c) 25 units (d) 10 units"),
    _q(19, "A", 1, "introduction-to-trigonometry", "In a right-angled triangle PQR, ∠Q = 90°. If ∠P = 45°, then value of tan P − cos^2 R is (a) 0 (b) 1 (c) 1/2 (d) 3/2"),
    _q(20, "A", 1, "introduction-to-trigonometry", "If tan θ = 2/3, then the value of sec θ is (a) √13/3 (b) √5/3 (c) √(13/3) (d) 3/√13"),
    _q(21, "B", 1, "areas-related-to-circles", "The perimeter of the sector of a circle of radius 14 cm and central angle of 45° is (a) 11 cm (b) 22 cm (c) 28 cm (d) 39 cm"),
    _q(22, "B", 1, "probability", "A bag contains 16 red balls, 8 green balls and 6 blue balls. One ball is drawn at random. The probability that it is a blue ball is (a) 1/6 (b) 1/5 (c) 1/30 (d) 5/6"),
    _q(23, "B", 1, "introduction-to-trigonometry", "If sin θ − cos θ = 0, then the value of θ is (a) 30° (b) 45° (c) 90° (d) 0°"),
    _q(24, "B", 1, "probability", "The probability of happening of an event is 0.02. The probability of not happening of the event is (a) 0.02 (b) 0.80 (c) 0.98 (d) 49/100"),
    _q(25, "B", 1, "areas-related-to-circles", "Two concentric circles are centred at O. The area of the shaded region (the ring between them) if outer and inner radii are 14 cm and 7 cm respectively, is (a) 462 cm^2 (b) 154 cm^2 (c) 231 cm^2 (d) 308 cm^2"),
    _q(26, "B", 1, "introduction-to-trigonometry", "1/(1 + sin θ) + 1/(1 − sin θ) can be simplified to get (a) 2 cos^2 θ (b) (1/2) sec^2 θ (c) 2/sin^2 θ (d) 2 sec^2 θ"),
    _q(27, "B", 1, "coordinate-geometry", "The origin divides the line segment AB joining the points A(1, −3) and B(−3, 9) in the ratio: (a) 3 : 1 (b) 1 : 3 (c) 2 : 3 (d) 1 : 1"),
    _q(28, "B", 1, "coordinate-geometry", "The perpendicular bisector of a line segment joining A(−8, 0) and B(8, 0) passes through a point (0, k). The value of k is (a) 0 only (b) 0 or 8 only (c) any real number (d) any non-zero real number"),
    _q(29, "B", 1, "triangles", "Which of the following is a correct statement? (a) Two congruent figures are always similar. (b) Two similar figures are always congruent. (c) All rectangles are similar. (d) The polygons having the same number of sides are similar."),
    _q(30, "B", 1, "pair-of-linear-equations", "The solution of the pair of linear equations x = −5 and y = 6 is (a) (−5, 6) (b) (−5, 0) (c) (0, 6) (d) (0, 0)"),
    _q(31, "B", 1, "coordinate-geometry", "A circle of radius 3 units is centred at (0, 0). Which of the following points lie outside the circle? (a) (−1, −1) (b) (0, 3) (c) (1, 2) (d) (3, 1)"),
    _q(32, "B", 1, "pair-of-linear-equations", "The value of k for which the pair of linear equations 3x + 5y = 8 and kx + 15y = 24 has infinitely many solutions, is (a) 3 (b) 9 (c) 5 (d) 15"),
    _q(33, "B", 1, "real-numbers", "HCF of two consecutive even numbers is (a) 0 (b) 1 (c) 2 (d) 4"),
    _q(34, "B", 1, "polynomials", "The zeroes of quadratic polynomial x^2 + 99x + 127 are (a) both negative (b) both positive (c) one positive and one negative (d) reciprocal of each other"),
    _q(35, "B", 1, "coordinate-geometry", "The mid-point of line segment joining the points (−3, 9) and (−6, −4) is (a) (−3/2, −13/2) (b) (9/2, −5/2) (c) (−9/2, 5/2) (d) (9/2, 5/2)"),
    _q(36, "B", 1, "real-numbers", "The decimal expansion of 13/(2 × 5^2 × 7) is (a) terminating after 1 decimal place (b) non-terminating and non-repeating (c) terminating after 2 decimal places (d) non-terminating but repeating"),
    _q(37, "B", 1, "triangles", "In ΔABC, DE || BC, AD = 2 cm, DB = 3 cm, DE : BC is equal to (a) 2 : 3 (b) 2 : 5 (c) 1 : 2 (d) 3 : 5"),
    _q(38, "B", 1, "real-numbers", "The (HCF × LCM) for the numbers 50 and 20 is (a) 1000 (b) 50 (c) 100 (d) 500"),
    _q(39, "B", 1, "real-numbers", "For which natural number n, 6^n ends with digit zero? (a) 6 (b) 5 (c) 0 (d) None"),
    _q(40, "B", 1, "introduction-to-trigonometry", "(1 + tan^2 A)(1 + sin A)(1 − sin A) is equal to (a) cos^2 A/sec^2 A (b) 1 (c) 0 (d) 2"),
    _q(41, "C", 1, "polynomials", _CS1_10_T1 + " The maximum height achieved by the ball is (a) 7 m (b) 8 m (c) 9 m (d) 10 m"),
    _q(42, "C", 1, "polynomials", _CS1_10_T1 + " The polynomial represented by the above graph is (a) linear polynomial (b) quadratic polynomial (c) constant polynomial (d) cubic polynomial"),
    _q(43, "C", 1, "polynomials", _CS1_10_T1 + " Time taken by the ball to reach maximum height is (a) 2 sec. (b) 4 sec. (c) 1 sec. (d) 2 min."),
    _q(44, "C", 1, "polynomials", _CS1_10_T1 + " Number of zeroes of the polynomial whose graph is given, is (a) 1 (b) 2 (c) 0 (d) 3"),
    _q(45, "C", 1, "polynomials", _CS1_10_T1 + " Zeroes of the polynomial are (a) 4 (b) −2, 4 (c) 2, 4 (d) 0, 4"),
    _q(46, "C", 1, "triangles", _CS2_10_T1 + " Which of the following criteria is not suitable for ΔABC to be similar to ΔQRP? (a) SAS (b) AAA (c) SSS (d) RHS"),
]

_CBSE10_2022_TERM1_BASIC_ENTRY = {
    "id": "cbse-10-2022-term1-basic",
    "class_num": 10,
    "board": "CBSE",
    "year": 2022,
    "set_label": "Term 1, Basic, Set 4",
    "source_name": "CBSE Class 10 Mathematics (Basic) Term 1 Question Paper 2021-22, Set 4 (exam 4 Dec 2021), GeeksforGeeks solved-paper reproduction",
    "source_url": "https://www.geeksforgeeks.org/maths/cbse-class-10-term-1-maths-answer-key-2021-basic-paper/",
    "max_marks": 40,
    "full_count": {"C": 10},
    "full_marks": {"C": 10},
    "section_titles": {
        "A": "Section A — Multiple Choice Questions (1 mark each; attempt any 16 of 20)",
        "B": "Section B — Multiple Choice Questions (1 mark each; attempt any 16 of 20)",
        "C": "Section C — Case Study Questions (1 mark each; attempt any 4 of 5 in each case study)",
    },
    "note": "The 2021-22 Term 1 Basic paper: 50 MCQs, 40 marks, 90 minutes; any 40 to be attempted (16+16+4+4). Case Study II (Q46-50) is based on a printed quilt-design figure whose measurements appear only in the figure: Q47-50 are omitted for that reason; Q46 is conceptual and is included. The case-study passages (Q41-45, Q46) are repeated inside each question so every question is self-contained.",
    "questions": _CBSE10_2022_TERM1_BASIC,
}
