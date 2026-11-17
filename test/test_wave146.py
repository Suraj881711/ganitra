"""Wave 146 (Suraj, 17 Nov 2026): 'MCQ sahi jawab +
galat-jawab rok' — built from the Wave 135 Board-2 (CISCE)
audit (~/workspace/ganitra-syllabus-gapmap.md section 2.5).

189 official CISCE specimen-paper questions were run through
the offline solve path; raw 'SOLVED' was 40.2%, but
hand-checking the solved set against the papers' OFFICIAL
marking schemes found only ~5 verifiably correct and ~50
verifiably WRONG/spurious. Suraj's standing mandate: a wrong
answer is worse than 'Answer not found'. The failing rows
are the fixture battery below (FED: the exact text the audit
fed the solver — instruction + question — keyed by the
row's idx in ganitra-book-questions.jsonl, with its qno).

Root causes fixed, one per pattern:

 1. The combination/permutation schema fed the FIRST TWO
    numbers in the text to C(n, r)/P(n, r) whenever the
    words 'choose'/'combination'/'permutation' appeared —
    and every Section A paper carries the instruction
    'Choose the correct answers...', so an RD question was
    answered C(400, 18) (31 digits), a shares question
    C(50, 40), a correlation question C(53, 28), a
    DEVASTATION word question P(4, 4). Now only explicit
    notation or a structured choose/taken/committee parse
    may proceed, and r > n declines (solver/statistics.py
    _counting).
 2. MCQ AUTHORITY: a whole-text 'solve' of an MCQ that no
    authority layer could certify (no multipart split, no
    verified proof, no exact one-option match, no format
    part) is no longer served raw — the option numbers
    pollute the full-text parse and a garbage value can
    coincide with a distractor (idx 131 was served '(b) 0'
    for a derivative MCQ whose true answer is k = 9). The
    chain falls through to the bank / stem solve / formats
    / honest not-found (fallback.py). Assertion-Reason
    items (incl. the OCR shape formats.extract_ar cannot
    parse) get the same treatment.
 3. Ask/result coherence vetoes (fallback._w146_veto):
    absurd magnitude, proof asks answered with assignments
    or bare matrices, true/false asks with no verdict,
    construction-only asks answered with a number,
    'express in terms of' answered with a bare number,
    'find the value of a + b' answered 'b = 0', a
    single-letter ask answered with a free-variable
    expression, equation asks with no '=', probability /
    correlation / eccentricity domain violations, the
    given-echo ('x = 8500' for a question GIVING
    'sum x = 8500'; 'x = 5' for 'marginal revenue when
    x = 5'), the evaluator's fragment carve (grouped
    tables, derivative/series/mensuration asks), the
    support-set mean (mean of {0,1,2,3} served as E(X)),
    and triangle-medians served as a data median.
 4. Salvage yields to options-bearing questions, to proof
    asks, and to vetoed questions — carving a fragment out
    of the same text reproduces the same incoherence (an
    MCQ was 'salvaged' into the mean of its own options).
 5. Meta-hijack fixes: maths_meta's computation veto now
    covers the Unicode minus signs board-paper extraction
    produces ('x = 100 - 4p' with U+2212 slipped past and a
    marginal-revenue problem got the Zero HISTORY card);
    advice triggers match on word boundaries, so the
    problem verb 'prepared' no longer fires the practice
    card; _is_nonmaths exempts the letters-of-a-word
    arrangement frame ('letters of the word CRICKET',
    'rank of the word CRICKET') while 'who won the cricket
    match' stays non-maths.
 6. Schema fixes: the coin enumeration counts TOSSERS
    ('three friends ... each will toss a coin' -> n = 3)
    and knows the all-same / different-result events (the
    odd-one-out pizza game: 1/4 and 3/4, not 1/2); an
    exact-ROUNDS (geometric) ask declines; the raw
    descriptive block declines Mode A/B/C labels (a frame
    whitelist for the statistic), triangle medians,
    grouped data (>= 3 class intervals), figure-referenced
    data and probability support sets; a line through a
    triangle's CENTROID is anchored at the centroid, not
    at vertex A; a multi-item GST bill declines instead of
    answering item 1; a sums-of-SEVERAL-GPs question
    declines the single-GP path; _coordinate declines when
    the final ask is an eccentricity it cannot compute.

Every guard is narrow and paired with a false-positive
battery: the audit's verifiably-CORRECT rows (idx 7, 24,
40, 109, 159) must keep their exact answers, legit big
factorial answers survive, an HCF that equals one of its
inputs (12 = HCF(12, 24)) is not an 'echo', and the classic
textbook counting forms still compute.
"""
import pytest

from api import _solve_friendly
from fallback import _is_nonmaths, _w146_veto
from maths_meta import meta_result
from solver.statistics import _counting


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    """Fresh DB per test (the live bank must never replay a
    stored answer inside this battery) and no AI keys."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


FED = {2: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) Radha deposited ₹400 per month in a recurring deposit account for 18 months. The qualifying sum of money for the calculation of interest is: (a) ₹ 3,600 (b) ₹ 7,200 (c) ₹ 68,400 (d) ₹ 1,36,800', 'cls': 10, 'qno': 'Q1(ii)'}, 6: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) Given that the sum of the squares of the first seven natural numbers is 140, then their mean is: (a) 20 (b) 70 (c) 280 (d) 980', 'cls': 10, 'qno': 'Q1(vii)'}, 7: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) A bag contains 3 red and 2 blue marbles. A marble is drawn at random. The probability of drawing a black marble is: (a) 0 (b) 1/5 (c) 2/5 (d) 3/5', 'cls': 10, 'qno': 'Q1(viii)'}, 9: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) A mixture of paint is prepared by mixing 2 parts of red pigments with 5 parts of the base. Using the given information in the following table, find the values of a, b & c to get the required mixture of paint. Parts of red pigment 2 4 b 6 Parts of base 5 a 12.5 c (a) a = 10, b = 10, c = 10 (b) a = 5, b = 2, c = 5 (c) a = 10, b = 5, c = 10 & (d) a = 10, b = 5, c = 15', 'cls': 10, 'qno': 'Q1(x)'}, 11: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) The sum of money required to buy 50, ₹ 40 shares at ₹ 38.50 is: (a) ₹ 1,920 (b) ₹ 1,924 (c) ₹ 1,925 (d) ₹ 1,952', 'cls': 10, 'qno': 'Q1(xii)'}, 24: {'q': '-11, -7, -3,.............,49, 53 are the terms of a progression. Answer the following: How many terms are there in all?', 'cls': 10, 'qno': 'Q3(i)(b)'}, 26: {'q': 'In the diagram given below, a tilted right circular cylindrical vessel with base diameter 7 cm contains a liquid. When placed vertically, the height of the liquid in the vessel is the mean of two heights shown in the diagram. Find the area of wet surface, when the cylinder is placed vertically on a horizontal surface. (Use π = 22/7)', 'cls': 10, 'qno': 'Q3(ii)'}, 27: {'q': 'Use a ruler and compass to answer this question. Construct a circle of radius 4.5cm and draw a chord AB of length 6.5 cm.', 'cls': 10, 'qno': 'Q3(iii)(a)'}, 40: {'q': 'Using step-deviation method, find mean for the following frequency distribution: Class 0 - 15 15 - 30 30 - 45 45 - 60 60 - 75 75 - 90 Frequency 3 4 7 6 8 2', 'cls': 10, 'qno': 'Q5(iii)'}, 41: {'q': 'Find the coordinates of the centroid P of the ∆ABC, whose vertices are A(-1, 3), B(3, -1) and C(0, 0). Hence, find the equation of a line passing & through P and parallel to AB.', 'cls': 10, 'qno': 'Q6(i)'}, 44: {'q': 'The following bill shows the GST rate and the marked price of articles: Rajdhani Departmental Store. 1. Dry fruits (1 kg): Marked Price ₹1200, Discount ₹100, Rate of GST 12%. 2. Packed Wheat flour (5 kg): Marked Price ₹286, Discount Nil, Rate of GST 5%. 3. Bakery products: Marked Price ₹500, Discount 10%, Rate of GST 12%. Find the total amount to be paid (including GST) for the above bill.', 'cls': 10, 'qno': 'Q6(iii)'}, 46: {'q': 'The marks of 200 students in a test were recorded as follows: Marks % 0 - 10 10 - 20 20 - 30 30 - 40 40 - 50 50 - 60 60 - 70 70 - 80 80 - 90 90 - 100 No. of 5 7 11 20 40 52 36 15 9 5 students Using a graph sheet draw ogive for the given data and use it to find the: median. ,', 'cls': 10, 'qno': 'Q7(ii)(a)'}, 51: {'q': 'If x, y and z are in continued proportion, prove that: (x^3 + y^3 + z^3)/(x^2 y^2 z^2) = 1/x^3 + 1/y^3 + 1/z^3', 'cls': 10, 'qno': 'Q8(ii)'}, 52: {'q': 'A manufacturing company prepares spherical ball bearings, each of radius 7 mm and mass 4 gm. These ball bearings are packed into boxes. Each box can have a maximum of 2156 cm3 of ball bearings. Find the: maximum number of ball bearings that each box can have. ,', 'cls': 10, 'qno': 'Q8(iii)(a)'}, 60: {'q': 'Given matrix X = [[1, 8], [1, 3]] and I = [[1, 0], [0, 1]], prove that X^2 = 4X + 5I.', 'cls': 10, 'qno': 'Q10(ii)'}, 65: {'q': 'In subparts (i) to (xvii) choose the correct options and in subparts (xviii) to (xx), answer the questions as instructed. The centre of the circle 2x^2 + 2y^2 - 4x - 8y - 45 = 0 is: (a) (2, 4) (b) (-2, -4) (c) (-1, -2) (d) (1, 2)', 'cls': 11, 'qno': 'Q1(ii)'}, 105: {'q': 'The alternative voltage V, in a domestic electrical circuit ′t′ seconds after it is switched on is modelled by the function, V = 115 Sinωt + 115√3cosωt. Express 115 Sinωt + 115√3cosωt in the form RSin(ωt + \uf061), where R and \uf061 are the constants to be found, R> 0 and \uf061 is acute.', 'cls': 11, 'qno': 'Q15(i)'}, 109: {'q': 'A satellite moves in an Elliptical orbit around the earth as shown in the figure below. It moves so that the sum of its distances from the points f2 (-2,0) and f1 (2,0) is 8 units. (Evaluate) Based on the above information, find the following: The length of its semi-major axis of the elliptical orbit.', 'cls': 11, 'qno': 'Q16(ii)(a)'}, 110: {'q': 'A satellite moves in an Elliptical orbit around the earth as shown in the figure below. It moves so that the sum of its distances from the points f2 (-2,0) and f1 (2,0) is 8 units. (Evaluate) Based on the above information, find the following: Eccentricity of the elliptical orbit.', 'cls': 11, 'qno': 'Q16(ii)(b)'}, 111: {'q': 'A satellite moves in an Elliptical orbit around the earth as shown in the figure below. It moves so that the sum of its distances from the points f2 (-2,0) and f1 (2,0) is 8 units. (Evaluate) Based on the above information, find the following: Equation of the elliptical orbit.', 'cls': 11, 'qno': 'Q16(ii)(c)'}, 113: {'q': "For the word 'DEVASTATION', determine the number of 4-letter combinations and 4-letter permutations.", 'cls': 11, 'qno': 'Q17(i)'}, 114: {'q': 'The letters of the word ‘CRICKET’ are written in all possible orders. Find the total number words with or without meaning.', 'cls': 11, 'qno': 'Q17(ii)(a)'}, 115: {'q': 'The letters of the word ‘CRICKET’ are written in all possible orders. If these words are written out as in a dictionary, find the rank of the word ‘CRICKET’.', 'cls': 11, 'qno': 'Q17(ii)(b)'}, 122: {'q': 'Find the mean and standard deviation using the deviation method for the following: Age 20-25 25-30 30-35 35-40 40-45 45-50 50-55 No of employees 170 110 80 45 40 30 25 Find the percentage of the employees in an organisation whose age lies between x̅ − σ and x̅ + σ. (Evaluate)', 'cls': 11, 'qno': 'Q19'}, 123: {'q': 'S1, S2, S3, ..., Sn are the sums of n infinite geometric progressions. The first terms of these progressions are 1, 1/(2^2 - 1), 1/(2^3 - 1), ..., 1/(2^n - 1) and the common ratios are 1/2, 1/2^2, 1/2^3, ..., 1/2^n. Find S1 + S2 + S3 + ... + Sn.', 'cls': 11, 'qno': 'Q20'}, 131: {'q': 'In subparts (i) to (xi) choose the correct options and in subparts (xii) to (xv), answer the questions as instructed. If f(x) = kx 2 + 7x − 4 and f ′ (5) = 97 then what is the value of k? (a) −4 (b) 0 (c) 4 (d) 9', 'cls': 12, 'qno': 'Q1(viii)'}, 133: {'q': 'In subparts (i) to (xi) choose the correct options and in subparts (xii) to (xv), answer the questions as instructed. Assertion: The equality tan(cot −1 x) = cot(tan−1 x), is true for all x ∈ R π Reason: The identity tan−1 x + cot −1 x = 2, is true for all x ∈ R Which of the following is correct? (a) Both Assertion and Reason are true and Reason is the correct explanation for Assertion. (b) Both Assertion and Reason are true but Reason is not the correct explanation for Assertion. (c) Assertion is true and Reason is false. (d) Assertion is false and Reason is true.', 'cls': 12, 'qno': 'Q1(x)'}, 142: {'q': 'Show that the general solution of the differential equation dy/dx = y cot 2x is log y = (1/2) log|sin 2x| + C', 'cls': 12, 'qno': 'Q4'}, 143: {'q': 'If ∫ x 5 cos(x 6) dx = k sin(x 6) + C, find the value of ‘k’. (Evaluate)', 'cls': 12, 'qno': 'Q5(i)'}, 150: {'q': 'Three friends go to a restaurant to have pizza. They decide who will pay for the pizza by tossing a coin. It is decided that each one of them will toss a coin and if one person gets a different result (heads or tails) than the other two, that person would pay. If all three get the same result (all heads or all tails), they will toss again until they get a different result. What is the probability that all three friends will get the same result (all heads or all tails) in one round of tossing?', 'cls': 12, 'qno': 'Q10(i)(a)'}, 151: {'q': 'Three friends go to a restaurant to have pizza. They decide who will pay for the pizza by tossing a coin. It is decided that each one of them will toss a coin and if one person gets a different result (heads or tails) than the other two, that person would pay. If all three get the same result (all heads or all tails), they will toss again until they get a different result. What is the probability that they will get a different result in one round of tossing?', 'cls': 12, 'qno': 'Q10(i)(b)'}, 152: {'q': 'Three friends go to a restaurant to have pizza. They decide who will pay for the pizza by tossing a coin. It is decided that each one of them will toss a coin and if one person gets a different result (heads or tails) than the other two, that person would pay. If all three get the same result (all heads or all tails), they will toss again until they get a different result. What is the probability that they will need exactly four rounds of tossing to determine who would pay?', 'cls': 12, 'qno': 'Q10(i)(c)'}, 153: {'q': 'A school offers students the choice of three modes for attending classes: • Mode A: Offline (in-person) - 40% of students • Mode B: Online (live virtual classes) - 35% of students • Mode C: Recorded lectures - 25% of students After a feedback survey: • 20% of students from Mode A reported the class as “Excellent” • 30% from Mode B rated it as “Excellent” • 50% from Mode C rated it as “Excellent” A student is selected at random from the entire group, and it is found that they rated the class as “Excellent.” Represent the data in terms of probability. Define the events clearly.', 'cls': 12, 'qno': 'Q10(ii)(a)'}, 154: {'q': 'A school offers students the choice of three modes for attending classes: • Mode A: Offline (in-person) - 40% of students • Mode B: Online (live virtual classes) - 35% of students • Mode C: Recorded lectures - 25% of students After a feedback survey: • 20% of students from Mode A reported the class as “Excellent” • 30% from Mode B rated it as “Excellent” • 50% from Mode C rated it as “Excellent” A student is selected at random from the entire group, and it is found that they rated the class as “Excellent.” Using Bayes’ Theorem, find the probability that the student attended the Recorded lectures (Mode C), given that they rated the class as “Excellent.”', 'cls': 12, 'qno': 'Q10(ii)(b)'}, 159: {'q': 'Evaluate: ∫ (x^2 + x + 1)/((x + 2)(x^2 + 1)) dx', 'cls': 12, 'qno': 'Q12(i)'}, 161: {'q': 'A person has manufactured a water tank in the shape of a closed right circular cylinder. The volume of the cylinder is 539/2 cubic units. If the height and radius of the cylinder be h and r. Express h in terms of radius r and given volume.', 'cls': 12, 'qno': 'Q13(i)(a)'}, 164: {'q': 'A person has manufactured a water tank in the shape of a closed right circular cylinder. The volume of the cylinder is 539/2 cubic units. If the height and radius of the cylinder be h and r. Find the height of the tank.', 'cls': 12, 'qno': 'Q13(i)(d)'}, 166: {'q': 'A dolphin jumps and takes a path given by the equation h(t) = (1/2)(-7t^2 + 3t + 2), (t ≥ 0), where h(t) is the height of the dolphin at any point of time. Find the instantaneous rate of change of height at t = 1/14.', 'cls': 12, 'qno': 'Q13(ii)(b)'}, 167: {'q': 'A dolphin jumps and takes a path given by the equation h(t) = (1/2)(-7t^2 + 3t + 2), (t ≥ 0), where h(t) is the height of the dolphin at any point of time. h(t) is increasing in (-∞, 3/14). Is this true or false? Justify.', 'cls': 12, 'qno': 'Q13(ii)(c)'}, 169: {'q': 'In a school, three subject teachers English, Math, and Science sometimes give surprise tests on the same day. Based on past records: The English teacher gives a test 90% of the time • • The Math teacher gives a test 80% of the time • The Science teacher gives a test 70% of the time Each teacher decides independently. If the average number of surprise tests is less than 2.3 then the teachers should coordinate better to increase the performance of the students. Otherwise, no action is needed. Let X be the number of surprise tests a student gets on a given day. So, X ∈ {0,1,2,3}. Find the probability for each possible number of surprise tests.', 'cls': 12, 'qno': 'Q14(i)'}, 170: {'q': 'In a school, three subject teachers English, Math, and Science sometimes give surprise tests on the same day. Based on past records: The English teacher gives a test 90% of the time • • The Math teacher gives a test 80% of the time • The Science teacher gives a test 70% of the time Each teacher decides independently. If the average number of surprise tests is less than 2.3 then the teachers should coordinate better to increase the performance of the students. Otherwise, no action is needed. Let X be the number of surprise tests a student gets on a given day. So, X ∈ {0,1,2,3}. Use the probabilities to build a distribution table.', 'cls': 12, 'qno': 'Q14(ii)'}, 171: {'q': 'In a school, three subject teachers English, Math, and Science sometimes give surprise tests on the same day. Based on past records: The English teacher gives a test 90% of the time • • The Math teacher gives a test 80% of the time • The Science teacher gives a test 70% of the time Each teacher decides independently. If the average number of surprise tests is less than 2.3 then the teachers should coordinate better to increase the performance of the students. Otherwise, no action is needed. Let X be the number of surprise tests a student gets on a given day. So, X ∈ {0,1,2,3}. Calculate the average number of surprise tests per day.', 'cls': 12, 'qno': 'Q14(iii)'}, 178: {'q': 'A building is to be constructed in the form of a triangular pyramid ABCD as shown in the figure. Let the angular points be A (0, 1, 2), B (3, 0, 1), C (4, 3, 6) and D (2, 3, 2) and let G be the point of intersection of the medians of ∆BCD. Using the above information, answer the following What will be the length of vector ⃗⃗⃗⃗⃗⃗ AG?', 'cls': 12, 'qno': 'Q16(i)(a)'}, 186: {'q': 'In subparts (i) and (ii) choose the correct options and in subparts (iii) to (v), answer the questions as instructed. Mean of x = 53, mean of y = 28 regression co-efficient y on x = −1 · 2, regression co-efficient x on y = −0 · 3. Find coefficient of correlation (r).', 'cls': 12, 'qno': 'Q19(iii)'}, 187: {'q': 'In subparts (i) and (ii) choose the correct options and in subparts (iii) to (v), answer the questions as instructed. The total revenue received from the sale of x unit of a product is given by R(x) = 3x 2 + 36x + 5. Find the marginal revenue when x = 5.', 'cls': 12, 'qno': 'Q19(iv)'}, 188: {'q': 'In subparts (i) and (ii) choose the correct options and in subparts (iii) to (v), answer the questions as instructed. A manufacturing company finds that the daily cost of producing x item of product is given by C(x) = 210x + 7000. Find the minimum number that must be produced and sold daily for break even, if each item is sold for ₹280.', 'cls': 12, 'qno': 'Q19(v)'}, 191: {'q': 'A survey of 50 families to study the relationships between expenditure on accommodation in (₹ x) and expenditure on food and entertainment (₹ y) gave the following results: ∑ x = 8500, ∑ y = 9600, σx = 60, σy = 20, r = 0.6 Estimate the expenditure on food and entertainment when expenditure on accommodation is ₹200.', 'cls': 12, 'qno': 'Q21'}}


FED[103] = {'q': 'The curve G has equation y = 1 − x 3 − 6x 2 − 9x and part of the graph of G is shown below: If the tangents drawn to the curve at the points B and C are parallel to x-axis, then find the coordinates of B and C respectively.', 'cls': 11, 'qno': 'Q14(i)(b)'}


def _fed(idx):
    """The audit's exact input text + class for row `idx`."""
    row = FED[idx]
    return row["q"], row["cls"]


def _solve(idx):
    text, cls = _fed(idx)
    return _solve_friendly(text, lang=None, student_class=cls)


# ---------------------------------------------------------------------------
# 1. The verifiably-WRONG rows: no real serve any more.
#    Every one of these must land on an honest fallback
#    (not-found / concept / science / guide) — never on a
#    confident solver answer.
# ---------------------------------------------------------------------------

WRONG_ROWS = [
    2,    # Q1(ii)   RD MCQ -> C(400, 18), 31 digits
    6,    # Q1(vii)  sum-of-squares MCQ -> C(140, 20)
    9,    # Q1(x)    paint mixture -> practice ADVICE card
    11,   # Q1(xii)  shares MCQ -> C(50, 40)
    26,   # Q3(ii)   figure mean -> mean of prose numbers
    27,   # Q3(iii)  construction -> circle area
    44,   # Q6(iii)  3-item GST bill -> item 1 only
    46,   # Q7(ii)a  ogive case -> evaluate carve '-10'
    51,   # Q8(ii)   proof ask -> equation roots
    52,   # Q8(iii)  ball bearings -> practice ADVICE card
    60,   # Q10(ii)  matrix proof -> X + I as 'proof'
    65,   # Q1(ii)   circle centre MCQ -> C(2, 2) = 1
    103,  # Q14(i)b  coordinates of B and C -> '0' carve
    105,  # Q15(i)   express in R sin form -> 'v = 115'
    110,  # Q16(ii)b eccentricity -> foci distance 4
    111,  # Q16(ii)c ellipse equation -> foci distance 4
    113,  # Q17(i)   DEVASTATION -> P(4, 4) = 24
    122,  # Q19      grouped data -> std of bounds+freq mix
    123,  # Q20      sums of n GPs -> 'does not exist'
    133,  # Q1(x)    Assertion-Reason -> 'x = 2' carve
    142,  # Q4       'Show that the general solution' -> y=1/2
    143,  # Q5(i)    find k -> whole antiderivative in x
    152,  # Q10(i)c  exactly four rounds -> 1/2
    153,  # Q10(ii)a Mode A/B/C case -> swept percent list
    154,  # Q10(ii)b Bayes part -> same swept list
    161,  # Q13(i)a  'express h in terms of r' -> 539/2
    164,  # Q13(i)d  'find the height' -> 539 / 2 carve
    166,  # Q13(ii)b rate of change -> echo of t = 1/14
    167,  # Q13(ii)c true/false ask -> bare fraction 3/14
    169,  # Q14(i)   distribution case -> mean of {0,1,2,3}
    170,  # Q14(ii)  distribution table -> 1.5
    171,  # Q14(iii) average tests E(X) -> 1.5
    178,  # Q16(i)a  medians of triangle -> 'Median = 1'
    186,  # Q19(iii) correlation -> C(53, 28), 15 digits
    187,  # Q19(iv)  marginal revenue -> 'x = 5' echo
    188,  # Q19(v)   break-even -> C(210, 7000) = 0
    191,  # Q21      regression estimate -> 'x = 8500' echo
]


@pytest.mark.parametrize("idx", WRONG_ROWS)
def test_wrong_rows_no_longer_served(idx):
    r = _solve(idx)
    assert r.get("fallback"), (
        f"idx {idx} ({FED[idx]['qno']}) still served a real "
        f"answer: {r.get('answer')!r}")


def test_flagship_garbage_values_gone():
    # The exact spurious values from the audit must not
    # appear as answers any more.
    r2 = _solve(2)
    assert "7280215840066377818029733051200" not in \
        str(r2.get("answer"))
    r186 = _solve(186)
    assert "903936161908052" not in str(r186.get("answer"))
    r191 = _solve(191)
    assert str(r191.get("answer")).strip() != "x = 8500"


# ---------------------------------------------------------------------------
# 2. The meta-hijack rows: genuine maths must not route to
#    the non-maths refusal (or a history/advice card).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("idx", [114, 115])
def test_cricket_word_questions_not_nonmaths(idx):
    r = _solve(idx)
    assert r.get("fallback_kind") != "nonmaths", r
    assert r.get("fallback_kind") not in ("history",
                                          "advice"), r


def test_nonmaths_still_refused():
    assert _is_nonmaths("who won the cricket match") is True
    assert _is_nonmaths("cricket ka score kya hai") is True
    assert _is_nonmaths(
        "The letters of the word 'CRICKET' are written in "
        "all possible orders. Find the total number of "
        "words.") is False
    assert _is_nonmaths(
        "If these words are written out as in a dictionary, "
        "find the rank of the word 'CRICKET'.") is False


def test_meta_computation_veto_unicode_minus():
    # idx 190: 'x = 100 - 4p' with U+2212 MINUS — the Zero
    # history card must not fire on a real problem.
    r = meta_result(
        "The demand function of a monopoly is given by "
        "x = 100 \u2212 4p. Find the quantity at which the "
        "Marginal Revenue will be zero.")
    assert r is None


def test_meta_advice_word_boundary():
    # 'prepared' inside a problem statement is not an
    # advice ask; a genuine prepare question still is.
    assert meta_result(
        "A mixture of paint is prepared by mixing 2 parts "
        "of red pigments with 5 parts of the base. Find "
        "the values of a, b and c.") is None
    r = meta_result("How to prepare for maths exam?")
    assert r is not None and r.get("meta_id") == "practice"


# ---------------------------------------------------------------------------
# 3. The verifiably-CORRECT rows: byte-identical answers.
# ---------------------------------------------------------------------------

CORRECT_ROWS = {
    7: "(a) 0",          # black-marble probability MCQ
    24: "17",            # AP term count
    40: "46.5",          # step-deviation grouped mean
    109: "4",            # semi-major axis (foci distance/2
                         # is a coincidence of the schema —
                         # the value is the true one)
    131: "(d) 9",        # f'(5) = 97 -> k = 9, option (d)
    41: "y = -1x + 4/3",  # centroid line, now exact
}


@pytest.mark.parametrize("idx,want", CORRECT_ROWS.items())
def test_correct_rows_unchanged(idx, want):
    r = _solve(idx)
    assert not r.get("fallback"), r
    assert str(r.get("answer")).strip() == want, r


@pytest.mark.parametrize("idx,want", [(150, "1/4"),
                                      (151, "3/4")])
def test_coin_game_parts_correct(idx, want):
    # The odd-one-out pizza game: all-same = 2/8, a
    # different result = 6/8. Both were 1/2 before.
    r = _solve(idx)
    assert not r.get("fallback"), r
    assert str(r.get("answer")).startswith(want), r


def test_correct_integral_unchanged():
    r = _solve(159)      # partial-fractions integral
    assert not r.get("fallback"), r
    assert "log(x + 2)" in str(r.get("answer")), r


# ---------------------------------------------------------------------------
# 4. The MCQ contract: solve the stem, match the option;
#    no match -> honest not-found; an option is never
#    echoed.
# ---------------------------------------------------------------------------

def test_mcq_match_serves_option():
    r = _solve_friendly(
        "Find the HCF of 12 and 18 (A) 3 (B) 6 (C) 9 (D) 36")
    assert not r.get("fallback"), r
    assert str(r.get("answer")).strip() == "(B) 6", r


def test_mcq_matcher_reads_school_notation():
    # Wave 80's integrating-factor item: the matcher must
    # equate the solver's exp(x·log(x) - x) with the
    # school-written option e^(x logx − x) — logx is
    # log(x), and the parser's bare e is not Euler's
    # number until e^(...) is read as exp(...).
    from mcq import _matching_labels, _match_canon
    opts = [("A", "x"), ("B", "e^(x logx − x)"),
            ("C", "e^(x(1 − logx))"), ("D", "None of these")]
    assert _matching_labels("exp(x·log(x) - x)", opts) == ["B"]
    assert _match_canon("the value of e is 2.71") == \
        "the value of e is 2.71"
    r = _solve_friendly(
        "Integrating factor of the differential "
        "Equation dy/dx + y logx = cosx is (A) x "
        "(B) e^(x logx − x) (C) e^(x(1 − logx)) "
        "(D) None of these")
    assert r.get("fallback_kind") is None, r
    assert str(r["answer"]).startswith("(B)")


def test_mcq_no_match_is_not_found():
    r = _solve_friendly("What is 2 + 3? (a) 4 (b) 6 "
                        "(c) 7 (d) 8")
    assert r.get("fallback"), r
    assert str(r.get("answer")).strip() not in (
        "4", "6", "7", "8", "(a) 4", "(b) 6", "(c) 7",
        "(d) 8"), r


def test_probability_event_names_are_not_options():
    # "P(A) = 0.5, P(B) = 0.4" is event NOTATION, not an
    # option list — mcq.extract_mcq 'parses' it as two
    # garbage options, and the MCQ authority must not fire
    # on it (the Wave 58 union pins caught exactly this).
    for q in (
            "Two events A and B are mutually exclusive. "
            "If P(A) = 0.3 and P(B) = 0.4, find P(A or B).",
            "If P(A) = 0.5, P(B) = 0.4 and P(A and B) = "
            "0.2, find P(A or B)."):
        r = _solve_friendly(q)
        assert not r.get("fallback"), r
        assert "0.7" in str(r.get("answer")), r


# ---------------------------------------------------------------------------
# 5. Counting discipline (unit): structured forms compute,
#    bare keywords decline.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,want", [
    ("Choose 3 balls from 10 balls in a bag", "120"),
    ("In how many ways can a committee of 4 be formed "
     "from 10 people?", "210"),
    ("In how many ways can 5 students be chosen from "
     "12 students?", "792"),
    ("Find C(12, 5)", "792"),
    ("Find 10 C 3", "120"),
    ("Find the value of P(8, 3)", "336"),
    ("8 different objects taken 3 at a time, find the "
     "number of permutations", "336"),
])
def test_counting_structured_forms(q, want):
    out = _counting(q)
    assert out is not None and out["answer"] == want, out


@pytest.mark.parametrize("q", [
    "Choose the correct answers to the questions from "
    "the given options. Radha deposited 400 per month "
    "for 18 months.",
    "For the word 'DEVASTATION', determine the number "
    "of 4-letter combinations and 4-letter permutations.",
    "choose 7 from 2",
    "A student is selected at random from the entire "
    "group",
])
def test_counting_bare_keywords_decline(q):
    assert _counting(q) is None


# ---------------------------------------------------------------------------
# 6. Veto false-positive battery: legitimate answers the
#    guards must NOT eat.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,result", [
    # A legit 13-digit factorial answer (15!) — counting
    # frame in the question exempts it from V0.
    ("In how many ways can 15 students be arranged in "
     "a row?",
     {"op": "permutation", "answer": "1307674368000",
      "steps": ["P(15, 15) = 15! = 1307674368000"]}),
    # An explicit C(n, r) the student actually wrote.
    ("What is the value of C(30, 15)?",
     {"op": "combination", "answer": "155117520",
      "steps": ["C(30, 15) = 155117520"]}),
    # HCF(12, 24) = 12 equals an input — a CORRECT echo,
    # not a given-echo (no sum given, no veto shape).
    ("Find the HCF of 12 and 24",
     {"op": "hcf", "answer": "12",
      "steps": ["Factors of 12 and 24"]}),
    # A proof WITH working is not vetoed.
    ("Prove that (sin A + cos A)^2 = 1 + 2 sin A cos A",
     {"op": "identity", "answer": "Identity verified",
      "steps": ["LHS = (sin A + cos A)^2",
                "RHS = 1 + 2 sin A cos A",
                "LHS = RHS, hence proved"]}),
    # A true/false ask WITH a verdict is not vetoed.
    ("State whether 7 is a prime number, true or false?",
     {"op": "prime", "answer": "True — 7 is prime",
      "steps": ["7 has no divisors other than 1 and 7"]}),
    # A probability inside [0, 1] is not vetoed.
    ("What is the probability of getting a head when a "
     "coin is tossed?",
     {"op": "probability", "answer": "1/2",
      "steps": ["Favourable = 1, total = 2"]}),
    # 'Express in terms of' answered with an expression.
    ("Express the area of a circle in terms of its "
     "radius r",
     {"op": "formula", "answer": "pi * r^2",
      "steps": ["Area = pi r^2"]}),
    # 'Find the value of x' answered with the assignment.
    ("Find the value of x if 2x + 3 = 11",
     {"op": "equation", "answer": "x = 4",
      "steps": ["2x = 8", "x = 4"]}),
])
def test_veto_false_positives(q, result):
    assert _w146_veto(q, result) is False


@pytest.mark.parametrize("q,result", [
    # A proof ask answered with an assignment chain.
    ("Prove that x^2 - 5x + 6 = (x - 2)(x - 3)",
     {"op": "equation", "answer": "x = 2, x = 3",
      "steps": ["Solve for x"]}),
    # A true/false ask answered with a bare fraction.
    ("Is the function increasing? Is this true or false? "
     "Justify.",
     {"op": "evaluate", "answer": "3/14",
      "steps": ["Write the expression: 3 / 14"]}),
    # Probability outside [0, 1].
    ("What is the probability of drawing a red ball?",
     {"op": "probability", "answer": "1.5", "steps": []}),
    # The given-echo (sum given, same assignment served).
    ("A survey gave: \u2211 x = 8500, \u2211 y = 9600. "
     "Estimate y when x is 200.",
     {"op": "equation", "answer": "x = 8500",
      "steps": ["x = 8500"]}),
])
def test_veto_true_positives(q, result):
    assert _w146_veto(q, result) is True


# ---------------------------------------------------------------------------
# 7. Solver-level false positives: the descriptive and
#    counting batteries still serve.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q,want", [
    ("Find the mode of the data 3, 5, 3, 7, 3", "3"),
    ("Find the mean of 2, 4, 6", "4"),
    ("Find the median of 5, 1, 9, 3, 7", "5"),
    ("Find the HCF of 12 and 24", "12"),
    ("A coin is tossed. What is the probability of "
     "getting a head?", "1/2"),
    ("Find the sum to infinity of the GP 4, 2, 1, "
     "1/2, ...", "8"),
    ("An article costs Rs 1200 and GST is charged at "
     "12%. Find the total amount to be paid.", "1344"),
    # Notation that extract_mcq misparses as options —
    # the MCQ authority must not fire (Wave 55 pins):
    ("If n(A) = 10, n(B) = 8 and n(A intersection B) "
     "= 3, find n(A union B)", "15"),
    ("Solve the inequality (x - 1) / (x + 2) > 0", "-2"),
    # Legit finite series sums the evaluator owns — the
    # V9 series clause must not fire on them:
    ("Find the sum of the series 2 + 4 + 6 + 8", "20"),
    ("Find the limit of (3x^2 + 1) / (x^2 + 2) as x "
     "tends to infinity", "3"),
    # Coordinates answers are pairs — V12 must not eat
    # them, nor a distance asked over coordinates:
    ("Find the coordinates of the centroid of the "
     "triangle with vertices (0, 0), (3, 0) and (0, 3)",
     "(1.0, 1.0)"),
    ("Find the distance between the coordinates of "
     "A (1, 2) and B (4, 6)", "5"),
])
def test_legit_questions_still_served(q, want):
    r = _solve_friendly(q)
    assert not r.get("fallback"), r
    assert want in str(r.get("answer")), r
