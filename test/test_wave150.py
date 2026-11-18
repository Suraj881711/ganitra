"""Wave 150 (Suraj, 18 Nov 2026): 'galat-jawab rok'
for BOOK-STYLE questions — built from the Wave 135
books programme's hand-checked calibrations
(~/workspace/ganitra-syllabus-gapmap.md sections
2.5/2.6/2.7): of the solver's raw "SOLVED" serves on
book text, CISCE hand-checking found ~50 of 76
verifiably WRONG, UP 25 of 40, Bihar 41 of 60.
A wrong serve is worse than "Answer not found".

The battery below is the adjudicated regression
corpus: every row was re-run through the offline
solve path and hand-verified (question -> served
wrong answer -> correct answer / must-decline).
FED text is the exact text the audits fed the
solver (instruction + question), keyed by the
row's idx in ganitra-book-questions.jsonl.

Fixes, by family:
 * Serve-time vetoes (fallback._w150_veto, wired
   into _is_real, mcq._stem_is_real and both
   multipart return seams): dimension clashes
   (diameter asked, cm² served; price asked, %
   served), sum asked / list served, primality
   verdicts for non-primality asks, symbol soup
   (em-dash factors, degree-sign operands, I/<x>
   factors, d = assignments for DE asks), the
   solver's own "no variable to solve for" refusal
   served as an answer, multi-part asks answered
   with one bare value or a partial label set,
   HCF+LCM both asked / one served, given echoes
   (ratio restated, HCF/LCM givens restated, LCM
   slot filled with the product, solution
   restated, how-many-times echo, sum-range
   carve), factorise asks answered with bare
   numbers, proof/show/verify asks answered
   without proof working, draw/construct/plot
   asks answered with numbers, derivative asks
   answered by solving for the variable, sector
   asks worked as full circles, arrange asks
   answered with a range, comparison asks
   answered with one side's percent, naming asks
   answered with numbers, stated angle-sum facts
   contradicted, ratio asks answered with areas,
   nC-notation read as algebra (C = ...), cost-
   at-a-rate asks answered without money, speed
   asks answered with distances, HCF/LCM verified
   against the result's OWN factorisation steps,
   and "find the value of <expr> and <expr>"
   answered with the intermediate variable.
 * Solver seams: geometry answers a stated-radius
   DIAMETER ask with 2r instead of the area;
   number_theory routes prime-FACTOR asks to
   factorisation (given-factors product, product
   reconstruction, single and list factorisation)
   instead of the primality verdict.

Every WRONG row must now either decline to an
honest fallback or serve the correct answer;
every CORRECT row (the control set) must keep
serving its verified answer.
"""

import pytest

from api import _solve_friendly
from fallback import _w150_veto


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    """Fresh DB per test (the live bank must never
    replay a stored answer inside this battery) and
    no AI keys."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


FED = {3370: {'q': 'A plot of land is in the shape of a sector of a circle of radius 55m. The length of fencing that is erected along the edge of the plot to enclose the land is 176m. Calculate the area of the plot of land. (Evaluate)', 'cls': 11, 'board': 'ICSE/ISC (CISCE)'}, 3721: {'q': '(x-y)-(x + y) (ii) 3x — 2y', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3841: {'q': 'Write prime factors of 9.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3912: {'q': 'Solve the equation x — 9=11.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3585: {'q': 'Evaluate 18 — [4 + {16 — (18 — 5)}]', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3586: {'q': 'Simplify 14 — [12 — {9 -(7- 6- 2)}]', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4628: {'q': 'AABCH ZB=72°, ZC =64, ZAM ज्ञात कीजिए।', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4114: {'q': 'In AABC, ZB = 72°, ZC = 64°, find out ZA.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3718: {'q': 'Ifa=2,b=1 andc =3, find the value of (2a + 4b — c)?.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4098: {'q': 'Draw a triangle ABC, where AB=6 cm, BC=8 cm, AC=4 cm.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3847: {'q': 'Find prime factors of 1728 by division method.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3853: {'q': 'Find the HCF of 306 and 630 by division method. 306) 630(2', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3674: {'q': '(i) 6+ 4= 10, (ii) 3 x 9 = 27, (iii) 6- 2 = 4, (iv) 10+2=5;', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3973: {'q': 'Distribute ¥80 between Suhani and Palak in the ratio of 3 : 2.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3877: {'q': 'If HCF of two numbers is 16 and their product is 6400. Find their LCM.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4711: {'q': 'Find seven rational numbers in between the number 1 and 2. . . . 1+2 3', 'cls': 7, 'board': 'UP Board (UPMSP)'}, 3842: {'q': '‘If the prime factors of a number are 2, 2 and 3, then find the number.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3843: {'q': 'If the factors of a number are 8 and 3. Find the prime factors of that.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3717: {'q': 'Simplify : (i) 3abe — 2ab? - Sabc + 3ab? (ii) 5x2 — 2xy + 3x? + Sxy — 9x2,', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3880: {'q': '| How many times the HCF present in the LCM of the numbers 95, 285 and 399 ?', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3848: {'q': '_ Find prime factors of the following numbers : 112, 120, 135, 140, 150, 1228.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4023: {'q': 'Convert the following into the percentage : (i) 1/5 (ii) 3/8 (iii) 3/25 (iv) 17/,', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4149: {'q': 'The radius of a circle is 4.5 cm. Find the measure of the diameter of the circle.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3699: {'q': 'Ifx=7,y=3, find the value of following : @xty (i) 2x -y (iii) 3xy (iv) 2x2 (v) 5x3y.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4474: {'q': '95, 285 और 399 के लघुत्तम समापवर्त्य में इनका महत्तम समापवर्तक कितनी बार सम्मिलित है?', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4256: {'q': 'निम्नांकित तथ्यों को संख्या रेखा पर दिखाइए (४) 5 + 45८ 9 (i)0+5=5 : (iii) 2 + 3 + 45८ 9', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3698: {'q': 'Ifa=-2, find value of following expressions : (@) 5a? + 4a - 2 and (ii) a3 + 4a? + 3a —7.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4008: {'q': 'How much will it be ? @ 30% of 250 (ii) 40% of 300 (ii) 45% of 120 kg (iv) 75% of 678 litre', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3878: {'q': 'Can the HCF of two numbers is 14 and their LCM is 204 ? Give reasons in the favour of answer.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4366: {'q': '- निम्नांकित व्यंजकों के मान ४-3 के लिए ज्ञात कीजिए। (i)x-5 (ii) 7x-5 (iii) 7 — x? (iv) 35—2x°', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3697: {'q': 'Find the values of the following expressions for x = 3 : @)x-5 (i)7x-5 (iii) 17-x? (iv) 35 - 2x3', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4021: {'q': 'How much will it be: (@) 12% of & 150 (ii) 40% of 60 kg (ii) 15% of 2.5 metre (iv) 75% of 1250 litre', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4047: {'q': 'A farmer bought a cow in %13000 and sold it in a loss of 2500. In what price the farmer sold the cow ?', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3660: {'q': 'Ifa=5 and b=9, then find the values of following : (i) a+ 10 (ii) b - 3 (iii) a+ b- 14 (iv)axb (v) 30+a', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4512: {'q': 'एक आयताकार खेत की लम्बाई 29 मी और चौड़ाई 25 मी है । खेत की लम्बाई और चौड़ाई को अनुपात के रूप में लिखिए ।', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4064: {'q': 'Mohit bought a Almirah in $2500 and sold it with a loss of 6%. Find out the selling price of the Almirah.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4107: {'q': 'ADisa bisector of ZA in the figure and ADLBC A (i) Is AABD = AADC ? (ii) Is it correct to say BD=DC? B aD Cc', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3663: {'q': 'Write variables and constant in following statements : (i) Sx2y2z3 (ii) 7x2 yy? (iii) mn? (iv) a2? In this unit we Learnt', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4009: {'q': 'What percentage will it be ? @ 48 out of 144 (i) 55 kg out of 220 kg (ii) 25 paise of %5 (iv) 450 gram of 18 kilogram', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4031: {'q': 'Rahim gets 33 marks out of 50 marks in mathematics and 36 out of 60 marks in Hindi. In which subject Rahim gets good marks ?', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 5734: {'q': '— Factorize the following : (i) a +2at+l (ii) 36+ 12x + 4x7 (iii) 4c7 + 4c +1 (iv) 36x? + 60x + 25 (vy) Ox? + 6x + | - 4 | |', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 6107: {'q': 'Inwhich quadrant the following point are situated : (i) (-3, -7) (ii) (-5, 1) (iii) (2, -10) (iv) (5, 9) (v) (-6, 5) (vi) (-7, -5)', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 3593: {'q': 'The number of members in 10 families in any locality is found as follows : b 53,2 4,5)9, 7, 3,6 arrange the data in ascendingorder.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4187: {'q': 'Find the volume of the cube whose side is as follows: (i) Side = 12 cm (11) Side = 6.4 cm (iii) Side = 7.2 cm. (iv) Side = 1.3 cm. :', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4671: {'q': 'नीचे दी गई भुजा की माप वाले घनों के आयतन ज्ञात कीजिए। 6) भुजा ८ 2 सेमी (ii) भुजा = 6.4 सेमी (ii) भुजा = 7.2 सेमी (iv) भुजा > .3 सेमी', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4802: {'q': 'Express the following in general form : (i) 2.5 x 104 (ii) 1.75 x 10° (ii) 1.21 x 10-8 (iv) 4.5 x 10° (v) 2.3 x 1077 (vi) 2.5 x 10-4', 'cls': 7, 'board': 'UP Board (UPMSP)'}, 3938: {'q': 'Solve the following equations by alteration method : (a)P + 19=21 (b)n-7=8 (c) x — 11 = 20 (d)7=6+8 (e)x +5=0 We Learnt in this Unit :', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 6114: {'q': 'Length is twice of breadth of a rectangle. Plot a graph of relation of its area and breadth. (hint-Area of rectangle A : 2x x x = 2x”)', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 6168: {'q': 'Acircular park has diameter 48 metre 3.5 metre wide road encircles it. Find the cost of repairing it at the rate of 720 per sq. metre.', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 5059: {'q': 'Acarcovers the distance in 10 hours with speed of 48 km per hour. What will be speed of car to cover the same distance only in 8 hours?', 'cls': 7, 'board': 'UP Board (UPMSP)'}, 5900: {'q': 'Write down the names of sides, vertices, angles and diagonals in the following quadrilaterals : : a : | D | a E U : Q R (i) (ii) : (iii)', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 490: {'q': '3–2–5=–4', 'cls': 7, 'board': 'CBSE/NCERT'}, 491: {'q': '5 + 2 + 3 = 10', 'cls': 7, 'board': 'CBSE/NCERT'}, 3049: {'q': 'y log y dx – x dy = 0', 'cls': 12, 'board': 'CBSE/NCERT'}, 2202: {'q': 'If nC8 = nC2, find nC2.', 'cls': 11, 'board': 'CBSE/NCERT'}, 3047: {'q': '(ex + e–x) dy – (ex – e–x) dx = 0', 'cls': 12, 'board': 'CBSE/NCERT'}, 2484: {'q': 'Find the derivative of 99x at x = l00.', 'cls': 11, 'board': 'CBSE/NCERT'}, 943: {'q': 'Write 5 equations whose solution is x = – 2.', 'cls': 7, 'board': 'CBSE/NCERT'}, 822: {'q': 'Find two numbers whose HCF is 1 and LCM is 66.', 'cls': 7, 'board': 'CBSE/NCERT'}, 2779: {'q': 'dy Find in the following: dx x2 + xy + y2 = 100', 'cls': 12, 'board': 'CBSE/NCERT'}, 1695: {'q': 'Find the sum of the odd numbers between 0 and 50.', 'cls': 10, 'board': 'CBSE/NCERT'}, 2107: {'q': 'Prove that: π π π 1 π 7π π 3 cot + cosec + 3tan 2 = 6', 'cls': 11, 'board': 'CBSE/NCERT'}, 177: {'q': 'Which of the following numbers are prime: 23, 51, 37, 26?', 'cls': 6, 'board': 'CBSE/NCERT'}, 958: {'q': 'Given 28p – 36 = 98, find the value of 14p – 19 and 28p – 38.', 'cls': 7, 'board': 'CBSE/NCERT'}, 1491: {'q': 'In Fig. 9.25, ∠ ABC = 69°, ∠ ACB = 31°, find ∠ BDC. Fig. 9.25', 'cls': 9, 'board': 'CBSE/NCERT'}, 2203: {'q': 'Determine n if (i) 2nC3 : nC3 = 12 : 1 (ii) 2nC3 : nC3 = 11 : 1', 'cls': 11, 'board': 'CBSE/NCERT'}, 6291: {'q': 'गुणनखंडन कीजिए: 27ग 3 ़ ल3 ़ ्र3 – 9गल्र', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6873: {'q': 'रू दर्शाइए कि 5 – 3 एक अपरिमेय संख्या है।', 'cls': 10, 'board': 'Bihar (BSEB)'}, 6265: {'q': 'रू ग3 – 23ग2 ़ 142ग – 120 का गुणनखंडन कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6280: {'q': 'रू 8ग3 ़ ल3 ़ 27्र 3 – 18गल्र का गुणनखंडन कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6248: {'q': 'रू सत्यापित कीजिए कि 2 और 0 बहुपद ग2 – 2ग के शून्यक है।ं', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6276: {'q': 'रू 4ग2 ़ ल2 ़ ्र2 – 4गल – 2ल्र ़ 4ग्र का गुणनखंडन कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6264: {'q': 'रू गुणनखंड प्रमेय की सहायता से ल2 – 5ल ़ 6 का गुणनखंडन कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6293: {'q': 'यदि ग ़ ल ़ ्र त्र 0 होए तो दिखाइए कि ग 3 ़ ल3 ़ ्र3 त्र 3गल्र है।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 7559: {'q': 'दो संख्याओं का म.स. 46 और उनका गुणनफल 6400 है। उसका ल.स. ज्ञात करें।', 'cls': 6, 'board': 'Bihar (BSEB)'}, 6615: {'q': 'चक्रीय चतुर्भुज के सम्मुख कोणों के प्रत्येक युग्म का योग 1800 होता है।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6864: {'q': 'रू संख्या 6ए 72 और 120 का अभाज्य गुणनखंडन विधि् द्वारा HCF और स्ब्ड ज्ञात कीजिए।', 'cls': 10, 'board': 'Bihar (BSEB)'}, 6648: {'q': 'एक त्रिभुज की रचना करना, जिसमें आधर, एक आधर कोण तथा अन्य दो भुजाओं का योग दिया हो।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6852: {'q': 'रू 4052 और 12576 का HCF यूक्लिड विभाजन एल्गोरिथ्म का प्रयोग करके ज्ञात कीजिए। 6 गणित', 'cls': 10, 'board': 'Bihar (BSEB)'}, 7142: {'q': 'ABC एक समद्विबाहु त्रिभुज है जिसका कोण ब् समकोण है। सिद्ध कीजिए कि ।ठ2 त्र 2।ब्2 है।', 'cls': 10, 'board': 'Bihar (BSEB)'}, 7071: {'q': '0 और 50 के बीच की विषम संख्याओं का योग ज्ञात कीजिए।', 'cls': 10, 'board': 'Bihar (BSEB)'}, 3430: {'q': 'Evaluate: ∫ (x^2 + x + 1)/((x + 2)(x^2 + 1)) dx', 'cls': 12, 'board': 'ICSE/ISC (CISCE)'}, 3295: {'q': '-11, -7, -3,.............,49, 53 are the terms of a progression. Answer the following: How many terms are there in all?', 'cls': 10, 'board': 'ICSE/ISC (CISCE)'}, 3311: {'q': 'Using step-deviation method, find mean for the following frequency distribution: Class 0 - 15 15 - 30 30 - 45 45 - 60 60 - 75 75 - 90 Frequency 3 4 7 6 8 2', 'cls': 10, 'board': 'ICSE/ISC (CISCE)'}, 3312: {'q': 'Find the coordinates of the centroid P of the ∆ABC, whose vertices are A(-1, 3), B(3, -1) and C(0, 0). Hence, find the equation of a line passing & through P and parallel to AB.', 'cls': 10, 'board': 'ICSE/ISC (CISCE)'}, 3402: {'q': 'In subparts (i) to (xi) choose the correct options and in subparts (xii) to (xv), answer the questions as instructed. If f(x) = kx 2 + 7x − 4 and f ′ (5) = 97 then what is the value of k? (a) −4 (b) 0 (c) 4 (d) 9', 'cls': 12, 'board': 'ICSE/ISC (CISCE)'}, 3278: {'q': 'Choose the correct answers to the questions from the given options. (Do not copy the question, write the correct answers only.) A bag contains 3 red and 2 blue marbles. A marble is drawn at random. The probability of drawing a black marble is: (a) 0 (b) 1/5 (c) 2/5 (d) 3/5', 'cls': 10, 'board': 'ICSE/ISC (CISCE)'}, 3380: {'q': 'A satellite moves in an Elliptical orbit around the earth as shown in the figure below. It moves so that the sum of its distances from the points f2 (-2,0) and f1 (2,0) is 8 units. (Evaluate) Based on the above information, find the following: The length of its semi-major axis of the elliptical orbit.', 'cls': 11, 'board': 'ICSE/ISC (CISCE)'}, 3422: {'q': 'Three friends go to a restaurant to have pizza. They decide who will pay for the pizza by tossing a coin. It is decided that each one of them will toss a coin and if one person gets a different result (heads or tails) than the other two, that person would pay. If all three get the same result (all heads or all tails), they will toss again until they get a different result. What is the probability that they will get a different result in one round of tossing?', 'cls': 12, 'board': 'ICSE/ISC (CISCE)'}, 3421: {'q': 'Three friends go to a restaurant to have pizza. They decide who will pay for the pizza by tossing a coin. It is decided that each one of them will toss a coin and if one person gets a different result (heads or tails) than the other two, that person would pay. If all three get the same result (all heads or all tails), they will toss again until they get a different result. What is the probability that all three friends will get the same result (all heads or all tails) in one round of tossing?', 'cls': 12, 'board': 'ICSE/ISC (CISCE)'}, 4496: {'q': 'हल कीजिए P+ 8=37', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3864: {'q': 'Find LCM of 8 and 15', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3874: {'q': 'Find LCM of 117 and 221.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3895: {'q': 'Find HCF of 5904 and 4848.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3911: {'q': 'Solve the equation x + 7= 15', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3913: {'q': 'Solve the equation 3” + 4 = 25.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3916: {'q': 'Solve the equation 3a + 5 = 17,', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3918: {'q': 'Solve the equation 7 + 5x = 15 + 3x.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3852: {'q': 'Find HCF of 180 and 192 by factor method.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3854: {'q': 'Find HCF of 2052, 3996 and 7380 by division method.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3554: {'q': 'Find the value of (+6) + (+3)', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4142: {'q': 'The sum ofall three interior angles of a triangle is 180°.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4184: {'q': 'Find the volume of 8 m long, 3.5 m high and 20 cm wide wall.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4084: {'q': 'Find the product of 28.4 and 99.5 by the method of practical mathematics.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4214: {'q': 'Multiply 15 and 6. LHS. R.HS. 15 Ee) ees 1] / 0 -20 2 £ Epa ae 6) Ans. - 90', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4211: {'q': 'Multiply 95 and 99, L.H.S. R.HS. 95 -5 99 N -] 94 / 00 1S D4. 05 Ans, - 9405', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3937: {'q': 'Solve the following equations by error and try method : (a)x +6 = 10 (b)x+9=5', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4213: {'q': 'Multiply 12 and 9. L.H.S. R.H.S. 12 +2 jee 11 [220 -2 10 / 10 -2 10 fo Ans. - 108', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4672: {'q': 'एक कमरे की लम्बाई 5 मी, चौड़ाई 4 मी और ऊँचाई 3.5 मी है। कमरे का आयतन ज्ञात कीजिए।', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4033: {'q': 'Akram scored 12 marks out of 20 in a subject. What percentage of marks did he get?', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3879: {'q': 'Find HCF of 2211 and 5025 by division method. Find LCM of these numbers on this basis.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4182: {'q': 'Find the volume of the cuboid, whose length is 5.5 cm, breadth is 3.5 cm, height is 4.0 cm.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3849: {'q': 'Prime numbers between 80 and 90 are : ‘ (1) 81 and 83 (2) 81 and 89 (3) 83 and 87 : (4) 83 and 89', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3516: {'q': 'Find the product at the following using suitable properties : (i) 4 x 2834 x 25 (ii) 5 x 658 x 80 (iii) 25 x 4837 x 40', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 3868: {'q': 'Find out LCM of the following numbers, (a) 5, 10, 15 (b) 16, 44, 64 (c) 10, 65, 91 (d) 22, 121, 418 (e) 14, 28, 35, 56.', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4052: {'q': 'A trader buys wheat at a rate of 500 per quintal and sells it at the rate Rs 450 per quintal Tell the percentage of loss/', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 6042: {'q': 'The height in cm of 8 girls of any class is 140, 142, 135, 133, 137, 150, 148 and 138 respectively. Find the median of data.', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 6074: {'q': 'The median of first five prime numbers is (a) 6.2 (b) 5.6 (c) 5.0 (d) 3.0 yee gz SN 342 Explore Mathematics-8 | We have learnt', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 3869: {'q': 'Find out the smallest number which is completely divisible by 20, 25 and 40. (Hint : Required number is the lcm of given numbers)', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4489: {'q': 'समीकरण 5 p = 5 को हल कीजिए। स्\u200d हलः 5 p =.5 या, 22 = दि- ..... (दोनों पक्षों में 5 से भाग देने पर) अत: p=3 उत्तर की स्वयं जांच कीजिए।', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 4210: {'q': 'Multiply 6 and 7, LHS RHS 6 ><. 4 7 3 ————ctcsctssueenstesnasecss Be 12 tee eens 331: 7 9 neeeaneenticiaetseeenape estes 7.2 Ans, - 42', 'cls': 6, 'board': 'UP Board (UPMSP)'}, 6095: {'q': 'To dices are thrown simultaneously write the set of the event where sum of the numbers appeared on the dice is odd. Probability aS 7 os', 'cls': 8, 'board': 'UP Board (UPMSP)'}, 503: {'q': '5 + (3 × 7)', 'cls': 7, 'board': 'CBSE/NCERT'}, 2158: {'q': '4x + 3 < 5x + 7', 'cls': 11, 'board': 'CBSE/NCERT'}, 2159: {'q': '3x – 7 > 5x – 1', 'cls': 11, 'board': 'CBSE/NCERT'}, 2168: {'q': '3x – 2 < 2x + 1', 'cls': 11, 'board': 'CBSE/NCERT'}, 562: {'q': '2y + (3y – 6) –y+6', 'cls': 7, 'board': 'CBSE/NCERT'}, 2160: {'q': '3(x – 1) ≤ 2 (x – 3)', 'cls': 11, 'board': 'CBSE/NCERT'}, 2170: {'q': '3 (1 – x) < 2 (x + 4)', 'cls': 11, 'board': 'CBSE/NCERT'}, 2177: {'q': 'Solve 4x + 3 < 6x +7.', 'cls': 11, 'board': 'CBSE/NCERT'}, 2165: {'q': '2 (2x + 3) – 10 < 6 (x – 2)', 'cls': 11, 'board': 'CBSE/NCERT'}, 2483: {'q': 'Find the derivative of x at x = 1.', 'cls': 11, 'board': 'CBSE/NCERT'}, 2129: {'q': 'Convert 6 radians into degree measure.', 'cls': 11, 'board': 'CBSE/NCERT'}, 2482: {'q': 'Find the derivative of x2 – 2 at x = 10.', 'cls': 11, 'board': 'CBSE/NCERT'}, 1663: {'q': 'Which term of the AP : 3, 8, 13, 18, . . . ,is 78?', 'cls': 10, 'board': 'CBSE/NCERT'}, 1590: {'q': 'Given that HCF (306, 657) = 9, find LCM (306, 657).', 'cls': 10, 'board': 'CBSE/NCERT'}, 1640: {'q': 'Find two numbers whose sum is 27 and product is 182.', 'cls': 10, 'board': 'CBSE/NCERT'}, 1176: {'q': 'A number increased by 20% becomes 90. What is the number?', 'cls': 8, 'board': 'CBSE/NCERT'}, 2348: {'q': 'Find angles between the lines 3 x + y = 1and x + 3 y = 1.', 'cls': 11, 'board': 'CBSE/NCERT'}, 1665: {'q': 'Check whether – 150 is a term of the AP : 11, 8, 5, 2 . . .', 'cls': 10, 'board': 'CBSE/NCERT'}, 1344: {'q': 'Find the area of a rhombus whose diagonals are 20 cm and 15 cm.', 'cls': 8, 'board': 'CBSE/NCERT'}, 6503: {'q': 'किसी चतुर्भुज के कोणों का योग 360° होता है।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 6419: {'q': 'एक त्रिभुज के तीनों कोणों का योग 1800 होता है।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 7548: {'q': '20, 380, 460 का म.स. भाग विधि द्वारा निकालें -', 'cls': 6, 'board': 'Bihar (BSEB)'}, 6272: {'q': 'रू सीधे गुणा न करके 105 × 106 का मान ज्ञात कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}, 7546: {'q': '42 और 32 का म.स. भाग विधि द्वारा इस प्रकार करते हैं- 2 Y 2 8] 2] 4', 'cls': 6, 'board': 'Bihar (BSEB)'}, 6822: {'q': 'आंकड़ों 14ए 25ए 14ए 28ए 18ए 17ए 18ए 14ए 23ए 22ए 14ए 18 का बहुलक ज्ञात कीजिए।', 'cls': 9, 'board': 'Bihar (BSEB)'}}


# idx -> (family, mode, tokens, absent)
# mode "decline": no confident serve any more.
# mode "tokens": declined, or served with every
# token present and no absent string.
# mode "notwrong": declined, or served with an
# answer different from the recorded wrong one.
WRONG = {3370: ('F8 wrong-schema (sector)', 'tokens', ['1815'], []), 3721: ('F3 soup', 'decline', [], []), 3841: ('F2 isprime hijack', 'tokens', ['3^2'], []), 3912: ('F3 dash-soup', 'tokens', ['20'], ['—']), 3585: ('F3 dash-soup', 'tokens', ['11'], ['—']), 3586: ('F3 dash-soup', 'tokens', ['12'], ['—']), 4628: ('F3 soup', 'decline', [], []), 4114: ('F5 given-echo', 'decline', [], []), 3718: ('F3 soup', 'tokens', ['5'], ['I/f']), 4098: ('F10 draw ask', 'decline', [], []), 3847: ('F2 isprime hijack', 'tokens', ['2^6'], []), 3853: ('F7 gcd text-pollution', 'tokens', ['18'], []), 3674: ('F4 non-answer message', 'decline', [], []), 3973: ('F5 ratio echo', 'tokens', ['48'], []), 3877: ('F5 LCM=product echo', 'tokens', ['400'], []), 4711: ('F6 count-ask mismatch', 'decline', [], []), 3842: ('F2 isprime hijack', 'tokens', ['12'], []), 3843: ('F2 isprime hijack', 'tokens', ['2^3'], []), 3717: ('F6 partial multipart', 'decline', [], []), 3880: ('F6 partial (quotient not given)', 'tokens', ['105'], []), 3848: ('F2 isprime hijack', 'tokens', ['112 ='], []), 4023: ('F5 fraction echo', 'tokens', ['20%'], []), 4149: ('F1 diameter->area', 'tokens', ['9'], ['cm²']), 3699: ('F3 soup', 'tokens', ['11'], ['I/']), 4474: ('F5 given echo (Hindi)', 'tokens', ['105'], []), 4256: ('F4 non-answer message', 'decline', [], []), 3698: ('F3 soup', 'tokens', ['10'], ['I/f']), 4008: ('F6 partial multipart', 'tokens', ['75', '120', '54', '508.5'], []), 3878: ('F9 reason ask', 'decline', [], []), 4366: ('F6 partial multipart', 'tokens', ['-8', '-26', '89'], []), 3697: ('F6 partial multipart', 'tokens', ['-2', '16', '8', '-19'], []), 4021: ('F6 partial multipart', 'tokens', ['18', '24', '937.5'], []), 4047: ('F1 price->percent', 'tokens', ['10500'], []), 3660: ('F3 soup', 'tokens', ['15', '45'], ['I/f']), 4512: ('F8 ratio->area', 'tokens', ['29', '25'], ['725']), 4064: ('F1 price->percent', 'tokens', ['2350'], []), 4107: ('F3 soup', 'decline', [], []), 3663: ('F7 non-computational carve', 'decline', [], []), 4009: ('F6 partial multipart', 'tokens', ['33.33', '5%', '2.5%'], []), 4031: ('F8 comparison ask', 'notwrong', [], []), 5734: ('F7 factorise carve', 'decline', [], []), 6107: ('F6 partial multipart', 'tokens', ['Second', 'Fourth'], []), 3593: ('F8 arrange->range', 'decline', [], []), 4187: ('F6 partial multipart', 'tokens', ['1728', '262.144', '373.248', '2.197'], []), 4671: ('F6 partial multipart', 'tokens', ['512', '262.144', '373.248'], []), 4802: ('F7 carve', 'tokens', ['25000'], []), 3938: ('F3 dash-soup part', 'notwrong', [], ['—']), 6114: ('F10 plot ask', 'decline', [], []), 6168: ('F8 road-area schema', 'tokens', ['11325'], ['576']), 5059: ('F8 inverse proportion', 'tokens', ['60'], []), 5900: ('F7 naming ask', 'decline', [], []), 490: ('F4 non-answer message', 'decline', [], []), 491: ('F4 non-answer message', 'decline', [], []), 3049: ('F3 soup (DE)', 'decline', [], []), 2202: ('F12 counting misparse', 'tokens', ['45'], []), 3047: ('F3 soup (DE)', 'decline', [], []), 2484: ('F3 soup', 'tokens', ['99'], []), 943: ('F5 solution echo', 'decline', [], []), 822: ('F5 givens echo', 'notwrong', [], []), 2779: ('F1 dy/dx->solve', 'tokens', ['dy/dx'], []), 1695: ('F1 sum->list', 'tokens', ['625'], []), 2107: ('F4 non-answer message', 'decline', [], []), 177: ('F6 partial list', 'tokens', ['37'], []), 958: ('F6 partial (intermediate served)', 'tokens', ['48', '96'], []), 1491: ('F3 soup', 'tokens', ['80'], []), 2203: ('F12 counting misparse', 'tokens', ['5', '6'], ['C =']), 6291: ('F7 factorise carve', 'decline', [], []), 6873: ('F9 show-ask', 'decline', [], []), 6265: ('F7 factorise carve', 'decline', [], []), 6280: ('F7 factorise carve', 'decline', [], []), 6248: ('F9 verify-ask', 'decline', [], []), 6276: ('F7 factorise carve', 'decline', [], []), 6264: ('F7 factorise carve', 'decline', [], []), 6293: ('F9 show-ask', 'decline', [], []), 7559: ('F8 wrong-op (HCF for LCM ask)', 'decline', [], []), 6615: ('F11 statement contradiction', 'tokens', ['180'], ['360']), 6864: ('F6 partial (LCM missing)', 'decline', [], []), 6648: ('F10 construction heading', 'decline', [], []), 6852: ('F7 gcd text-pollution', 'tokens', ['4'], []), 7142: ('F9 prove-ask verdict', 'decline', [], []), 7071: ('F7 sum carve (Hindi)', 'tokens', ['625'], [])}


# idx -> token that must remain in the served answer
CORRECT = {3430: 'atan', 3295: '17', 3311: '46.5', 3312: '4/3', 3402: '9', 3278: '0', 3380: '4', 3422: '3/4', 3421: '1/4', 4496: '29', 3864: '120', 3874: '1989', 3895: '48', 3911: 'x = 8', 3913: '7', 3916: 'a = 4', 3918: 'x = 4', 3852: '12', 3854: '36', 3554: '9', 4142: '180', 4184: '5600000', 4084: '2825.8', 4214: '90', 4211: '9405', 3937: '-4', 4213: '108', 4672: '70', 4033: '60%', 3879: '55275', 4182: '77', 3849: '89', 3516: '4837000', 3868: '4598', 4052: '10%', 6042: '139', 6074: '5.0', 3869: '200', 4489: 'p = 1', 4210: '42', 6095: '1/2', 503: '26', 2158: '-4', 2159: '-3', 2168: '3', 562: '4*y', 2160: '-3', 2170: '-1', 2177: '-2', 2165: '4', 2483: '1', 2129: '343.8', 2482: '20', 1663: '16th', 1590: '22338', 1640: '13', 1176: '75', 2348: '53.13', 1665: 'not a term', 1344: '150', 6503: '360', 6419: '180', 7548: '20', 6272: '11130', 7546: '2', 6822: '14'}


def _served(result):
    return (isinstance(result, dict)
            and result.get("fallback_kind") is None
            and not result.get("fallback")
            and bool((result.get("answer") or "").strip()))


def _solve(idx):
    row = FED[idx]
    return _solve_friendly(row["q"], lang=None,
                           student_class=row["cls"])


@pytest.mark.parametrize("idx", sorted(WRONG))
def test_wave150_wrong_rows_no_longer_served_wrong(idx):
    fam, mode, tokens, absent = WRONG[idx]
    r = _solve(idx)
    if not _served(r):
        return  # declined to an honest fallback
    ans = r.get("answer") or ""
    if mode == "decline":
        pytest.fail(f"idx {idx} ({fam}) still served: {ans[:120]}")
    if mode == "tokens":
        assert all(t in ans for t in tokens), (
            f"idx {idx} ({fam}) served without the correct")
        assert not any(a in ans for a in absent)
    if mode == "notwrong":
        assert not any(a in ans for a in absent)


@pytest.mark.parametrize("idx", sorted(CORRECT))
def test_wave150_control_rows_still_served(idx):
    r = _solve(idx)
    assert _served(r), f"control idx {idx} regressed to a decline"
    ans = r.get("answer") or ""
    assert CORRECT[idx] in ans, (
        f"control idx {idx} answer changed: {ans[:120]}")


# ---------------------------------------------------------------------------
# Synthetic near-miss battery: fresh wrong serves of
# the same families (must decline) and correct serves
# one step away from a veto pattern (must NOT decline).
# ---------------------------------------------------------------------------

SYNTH_WRONG = [
    # ratio echo (W9a): pristine served "3 : 2"
    "Distribute \u20b9100 between A and B in the ratio 3 : 2.",
    # price ask, percent serve (W2): pristine served "98.75%"
    "A shopkeeper bought a fan for \u20b9800 and sold it at a profit of 10%. Find the selling price.",
]

SYNTH_OK = [
    ("Find the diameter of a circle whose radius is 7 cm.", 6, "14"),
    ("Find the radius of a circle whose diameter is 14 cm.", 6, "7"),
    ("Find the area of a circle of radius 7 cm.", 6, "154"),
    ("Find the circumference of a circle with radius 7 cm.", 6, "44"),
    ("Is 97 prime?", 6, "prime"),
    ("Check whether 51 is prime or composite.", 6, "not prime"),
    ("Find the prime factors of 36.", 6, "2^2"),
    ("Find HCF of 12 and 18.", 6, "6"),
    ("Find the LCM of 12 and 18.", 6, "36"),
    ("Find the HCF and LCM of 12 and 18.", 6, "36"),
    ("Find the profit percent if CP is \u20b9800 and SP is \u20b9880.", 8, "10%"),
    ("CP = \u20b9500, SP = \u20b9600. Find the profit.", 8, "100"),
    ("Solve: (i) 2x = 10 (ii) 3x = 12 (iii) x + 1 = 4", 6, "x = 3"),
    ("Find the sum of the first 10 natural numbers.", 6, "55"),
    ("Find dy/dx if y = x^3.", 11, "x^2"),
    ("12 \u0914\u0930 18 \u0915\u093e \u092e\u0939\u0924\u094d\u0924\u092e \u0938\u092e\u093e\u092a\u0935\u0930\u094d\u0924\u0915 \u092c\u0924\u093e\u0913\u0964", 6, "6"),
    ("Construct a circle of radius 4.5 cm and find its area.", 6, "63"),
]


@pytest.mark.parametrize("q", SYNTH_WRONG)
def test_wave150_synthetic_wrong_declines(q):
    r = _solve_friendly(q, lang=None, student_class=8)
    assert not _served(r), (r.get("answer") or "")[:120]


@pytest.mark.parametrize("q,cls,token", SYNTH_OK)
def test_wave150_synthetic_correct_survives(q, cls, token):
    r = _solve_friendly(q, lang=None, student_class=cls)
    assert _served(r), f"near-miss control declined: {q[:60]}"
    assert token in (r.get("answer") or "")


def test_wave150_proof_serve_survives():
    r = _solve_friendly("Prove that 1 + tan\u00b2A = sec\u00b2A.",
                        lang=None, student_class=10)
    assert "proved" in (r.get("answer") or "")


# ---------------------------------------------------------------------------
# Direct veto pins (no solving): the verification and
# form rules on fabricated results.
# ---------------------------------------------------------------------------

def test_wave150_w24_gcd_verified_against_own_steps():
    bad = {"op": "gcd", "answer": "2", "steps": [
        "Prime factorisation: 4052 = 2^2 \u00d7 1013",
        "Prime factorisation: 12576 = 2^5 \u00d7 3 \u00d7 131",
        "Take the lowest power of each common prime factor.",
        "GCD = 2"]}
    q = "\u0930\u0942 4052 \u0914\u0930 12576 \u0915\u093e HCF \u092f\u0942\u0915\u094d\u0932\u093f\u0921 \u0935\u093f\u092d\u093e\u091c\u0928 \u090f\u0932\u094d\u0917\u094b\u0930\u093f\u0925\u094d\u092e \u0915\u093e \u092a\u094d\u0930\u092f\u094b\u0917 \u0915\u0930\u0915\u0947 \u091c\u094d\u091e\u093e\u0924 \u0915\u0940\u091c\u093f\u090f\u0964 6 \u0917\u0923\u093f\u0924"
    assert _w150_veto(q, bad)
    good = dict(bad, answer="4", steps=[
        bad["steps"][0], bad["steps"][1], bad["steps"][2], "GCD = 4"])
    assert not _w150_veto(q, good)
    # a genuine 3-number ask: the pair gcd legitimately
    # differs from the folded answer — no veto
    three = {"op": "gcd", "answer": "36", "steps": [
        "Prime factorisation: 2052 = 2^2 \u00d7 3^3 \u00d7 19",
        "Prime factorisation: 3996 = 2^2 \u00d7 3^3 \u00d7 37",
        "GCD = 36"]}
    assert not _w150_veto(
        "Find HCF of 2052, 3996 and 7380 by division method.", three)


def test_wave150_w6_refusal_message_is_not_an_answer():
    r = {"op": "equation",
         "answer": "The equation has no variable to solve for.",
         "steps": []}
    assert _w150_veto("5 + 2 + 3 = 10", r)
    ok = {"op": "equation", "answer": "x = 5", "steps": []}
    assert not _w150_veto("Solve x + 2 = 7", ok)


def test_wave150_designed_serves_survive_the_vetoes():
    # Wave 115's normal form: "sin 225° = √2" — the
    # degree sign before "=" is an angle measure, not
    # the bare-symbol soup ("° = 0") W5 targets.
    r = _solve_friendly(
        "Reduce the equation x + y + 2 = 0 to the normal "
        "form and find the distance of the line from the "
        "origin.", lang=None, student_class=11)
    assert _served(r)
    assert "cos 225" in (r.get("answer") or "")
    # Wave 115's collinearity guard: a show-that answered
    # with an affirmative verdict + area working is the
    # designed serve (a "No" verdict gets no exemption —
    # pinned idx 7142 denies its own given right angle).
    r = _solve_friendly(
        "Show that the points (1, 2), (3, 6) and (5, 10) "
        "are collinear.", lang=None, student_class=11)
    assert _served(r)
    assert "collinear" in (r.get("answer") or "")
    # Wave 103's occurrence counts legitimately coincide
    # with a number in the question (W9e exemption).
    r = _solve_friendly(
        "How many times does the digit 3 occur in the "
        "number 1333?", lang=None, student_class=6)
    assert _served(r)
    assert (r.get("answer") or "").strip() == "3"
    r = _solve_friendly(
        "How many times does 3 occur in the data "
        "3, 5, 3, 7, 3, 9?", lang=None, student_class=6)
    assert _served(r)
    assert (r.get("answer") or "").strip() == "3"


def test_wave150_designed_serves_survive_continuation():
    # Continuation pins: three veto over-fires on
    # designed serves (Wave 55's topics battery) were
    # narrowed — the adjudicated rows they came from
    # stay vetoed (pinned by the corpus above).
    # W4: "Is 29 a prime number?" IS a primality ask;
    # its verdict is the designed serve.
    r = _solve_friendly("Is 29 a prime number?",
                        lang=None, student_class=6)
    assert _served(r)
    assert "29 is prime" in (r.get("answer") or "")
    # W11: a genuine computation schema whose steps
    # DERIVE the claimed number answers a concrete-
    # instance prove-ask by computing it (PMI topic).
    r = _solve_friendly(
        "Prove by mathematical induction that the sum "
        "of the first 8 odd numbers is 64",
        lang=None, student_class=11)
    assert _served(r)
    assert (r.get("answer") or "").strip() == "64"
    # ...but the evaluator carve stays vetoed.
    assert _w150_veto(
        "Verify that 2 and 0 are zeros of x^2 - 2x.",
        {"op": "evaluate", "answer": "0",
         "steps": ["Evaluate: 0 = 0"]})
    # W25: the served variable IS the direct ask
    # ("find the value of k for which ... collinear").
    r = _solve_friendly(
        "Find the value of k for which the points "
        "(1, 2), (3, 4) and (5, k) are collinear",
        lang=None, student_class=12)
    assert _served(r)
    assert "k = 6" in (r.get("answer") or "")
    # ...while the intermediate-variable serve (the
    # idx-958 shape) stays vetoed.
    assert _w150_veto(
        "Given 28p - 36 = 98, find the value of "
        "14p - 19 and 28p - 38.",
        {"op": "evaluate", "answer": "p = 67/14",
         "steps": []})
    # W25, colon form: "find the value of p: <data>"
    # names p itself as the target (Wave 33's mean
    # serve) — the asked unknown, not an intermediate.
    r = _solve_friendly(
        "If the mean of the following data is 30, "
        "find the value of p: x: 10, 20, 30, 40, 50 "
        "and f: 3, 5, 4, p, 3.",
        lang=None, student_class=10)
    assert _served(r)
    assert "p = 5" in (r.get("answer") or "")
    # W11: the purpose-built verify_zeroes layer's
    # negative verdict is computed from its own
    # working (Wave 32) — not a bare verdict.
    r = _solve_friendly(
        "Verify that 1, 2 and 4 are zeroes of the "
        "cubic polynomial x^3 - 6x^2 + 11x - 6.",
        lang=None, student_class=10)
    assert r.get("op") == "verify_zeroes"
    assert "Not all" in (r.get("answer") or "")
    # W11: "prove that N is prime" IS a primality ask
    # and the isprime layer's verdict carries its
    # divisibility working (Wave 95's pin).
    r = _solve_friendly("Prove that 7 is a prime "
                        "number", lang=None,
                        student_class=6)
    assert _served(r)
    assert "7 is prime" in (r.get("answer") or "")
    # W6: for a genuine equation in a variable, the
    # solver's no-solution string is the designed
    # serve (Wave 77's byte-for-byte pin) — while
    # the variable-free statement rows stay vetoed
    # (pinned in test_wave150_w6 above).
    r = _solve_friendly("bhai 2x + 3 = 2x + 5 solve "
                        "karo", lang=None,
                        student_class=7)
    assert (r.get("answer") or "") == (
        "The equation has no variable to solve for.")
    # W10: a factorise-AND-root ask — the bare number
    # is the asked root (Wave 65's repeated-root
    # serve), not a carved factorise answer.
    r = _solve_friendly(
        "factorise x^2 - 12x + 36 and give the "
        "repeated root", lang=None, student_class=6)
    assert _served(r)
    assert "6" in (r.get("answer") or "")


def test_wave150_w7b_partial_card_scope():
    # A genuine multipart card covering 2 of 3 parts is
    # the Waves 100/141 design (serve what you can) —
    # no veto. A ONE-part labelled serve for a 3-part
    # ask is the idx-3717 partial serve — veto.
    card = {"op": "multipart_bundle",
            "answer": "(i) 4; (ii) 9", "steps": []}
    q = "Find: (i) 2 + 2 (ii) 3 + 6 (iii) 5 + 5"
    assert not _w150_veto(q, card)
    one = {"op": "multipart_bundle",
           "answer": "(ii) 9", "steps": []}
    assert _w150_veto(q, one)
    plain = {"op": "evaluate", "answer": "(ii) 9",
             "steps": []}
    assert _w150_veto(q, plain)


def test_wave150_w18_stated_fact_not_contradicted():
    q = "\u091a\u0915\u094d\u0930\u0940\u092f \u091a\u0924\u0941\u0930\u094d\u092d\u0941\u091c \u0915\u0947 \u0938\u092e\u094d\u092e\u0941\u0916 \u0915\u094b\u0923\u094b\u0902 \u0915\u0947 \u092a\u094d\u0930\u0924\u094d\u092f\u0947\u0915 \u092f\u0941\u0917\u094d\u092e \u0915\u093e \u092f\u094b\u0917 1800 \u0939\u094b\u0924\u093e \u0939\u0948\u0964"
    assert _w150_veto(q, {"op": "w103_angle_sum", "answer": "360\u00b0", "steps": []})
    assert not _w150_veto(q, {"op": "w103_angle_sum", "answer": "180\u00b0", "steps": []})

