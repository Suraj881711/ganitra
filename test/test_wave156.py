"""Wave 156 (Suraj, 18 Nov 2026): fixes for the
wrong-serve + missed-solve families found by the
Wave 153 AI cross-check audit (150 questions solved
by Ganitra first, then checked by an independent AI;
22 serves adjudicated wrong, 36 genuine missed
solves). The FED texts below are the audit's exact
questions (~/workspace/ganitra-wave153-aicheck).

Root fixes, by audit family:
 1. stem-echo / harvested numbers — bracketed-
    expression candidates now outrank bare chains in
    the salvage candidate order (router + fallback);
    _w156_veto V5/V6 backstops (echo fraction,
    class-limits list).
 2. bare-year serves — date-shaped chains excluded
    from the salvage candidates; _w156_veto V2.
 3. evaluate garbage on figure / garbled text —
    _w156_veto V1/V3/V8/V9 (identity-on-prose,
    figure-prompt harvest ops, invented operands,
    figure-page blank harvest).
 4. wrong-quantity misroutes — an explicit HCF/LCM
    ask owns its two measures (the rectangle-area
    translation no longer claims it); ratio_angles
    abstains when sides/perimeter/area are asked and
    a Heron ratio-sides schema serves instead.
 5. computation errors — the mean/median list regex
    spans ", and N" (the dropped last data point);
    the Hindi wrapped-equation extractor normalises
    U+2212 and superscript 2/3 (the dropped x^2);
    the spaced-typeset quadratic pre-pass in
    clean_text; P(specific card) = 1/52 in the Hindi
    probability path; variance+SD and median+mode
    both named when both are asked.
 6. proof/verify bare numbers — _w156_veto V4/V4b;
    degree_upgrade abstains on proof prompts and
    requires a degree ASK.
 7. missed easy schemas — rectangular prose dims
    (long/wide + fencing = perimeter), point-on-line,
    ratio split, age-times-plus, three-plan
    investment, AP sum of multiples, inscribed
    circle, parallelogram + cube-side Hindi
    mensuration, supplementary-angle translation,
    unit-crossing ratio translation, perfect-square
    subtraction, inverse-proportion sweets,
    ratio-to-percent, corrected mean/SD, regression
    estimate, probability relations, tetrahedron-
    centroid distance, MCQ cost-expression builder,
    and the two Mathematical Reasoning schemas
    (negations, quantifier conversions) — plus the
    gates that let them serve: _is_junk exemption,
    the pre-nonmaths reasoning guard, the Wave 140
    gate's subtraction carve-out, and maths_meta's
    data-list computation veto (book-079).

Left declining honestly (documented in
~/workspace/ganitra-wave156-notes.md): book-023
(variable glyphs destroyed), book-045 (figure-led
frame, units garbled), book-063 (fraction
denominators destroyed in extraction).
"""

import pytest

from api import _solve_friendly
from fallback import _is_junk, _w156_veto
from maths_meta import meta_result
from solver.gaps103 import degree_upgrade


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


FED = {
    'bank_089': {'q': 'A train traveled at different speeds of 65, 72, 68, 70, and 75 km/h during a 5-hour journey. Find the mean speed of the train.', 'cls': 7},
    'bank_092': {'q': 'एक आयताकार खेत की लंबाई ९४५ मीटर और चौड़ाई ६३० मीटर है। इन दोनों मापों का HCF निकालें।', 'cls': 10},
    'bank_107': {'q': 'समीकरण x² − 15x + 54 = 0 को हल कीजिए।', 'cls': 11},
    'bank_111': {'q': 'Ananya spends a total of 180 minutes studying Mathematics and Science in the ratio 4:5. How much time does she spend on each subject?', 'cls': 8},
    'bank_116': {'q': 'एक परीक्षा में छात्र ने ५/६ घंटा गणित और १/३ घंटा विज्ञान पढ़ा। इस अंतर को १८ से गुणा करके ४ जोड़ा जाए तो कुल कितना समय हुआ?', 'cls': 6},
    'bank_120': {'q': "अच्छी तरह से फेंटी गई 52 पत्तों की एक ताश की गड्डी में से एक पत्ता निकाला जाता है। इस पत्ते के 'पान का राजा' (King of Hearts) होने की प्रायिकता ज्ञात कीजिए।", 'cls': 10},
    'book_006': {'q': 'Given below are the marks out of 25 of 5 students in a mathematics test. Calculate the variance and standard deviation of these observations. Marks : 10, 13, 17, 20, 23', 'cls': 11},
    'book_020': {'q': 'The mean and standard deviation of 20 observations are found to be 10 and 2, respectively. On rechecking, it was found that an observation 8 was incorrect. Calculate the correct mean and standard deviation in each of the following cases: (i) If wrong item is omitted. (ii) If it is replaced by 12.', 'cls': 11},
    'book_025': {'q': 'रू एक त्रिभुजाकार भूखंड (plot) की भुजाओं का अनुपात 3 : 5 : 7 है और उसका परिमाप 300 उ है। इस भूखंड का क्षेत्रापफल ज्ञात कीजिए।', 'cls': 9},
    'book_030': {'q': 'If the centroid of a tetrahedron OABC is (1, 2, -1) where A = (a, 2, 3), B = (1, b, 2), C = (2, 1, c) respectively, find the distance of P (a, b, c) from the origin.', 'cls': 12},
    'book_036': {'q': '27 x 2 − 10 x + 1 = 0 COMPLEX NUMBERS AND QUADRATIC EQUATIONS 113', 'cls': 11},
    'book_038': {'q': 'For a bivariate data: x = 53, y = 28, bYX = −1.5 and bXY = − 0.2. Estimate Y when X = 50.', 'cls': 12},
    'bank_081': {'q': 'A rectangular shop floor in a market is 4 meters long and 7 meters wide. Find the area of the floor.', 'cls': 6},
    'bank_082': {'q': 'एक किसान ने बीज खरीदने के लिए बैंक से ₹15000 का ऋण 7% वार्षिक साधारण ब्याज की दर पर लिया। 2 वर्ष के अंत में उसे कितना ब्याज चुकाना होगा?', 'cls': 7},
    'bank_084': {'q': '₹10,000 पर 10% वार्षिक दर से 2 वर्ष का चक्रवृद्धि ब्याज ज्ञात कीजिए।', 'cls': 9},
    'bank_087': {'q': 'दो संख्याओं का योग 154 है और उनका अंतर 46 है। दोनों संख्याएँ ज्ञात कीजिए।', 'cls': 12},
    'bank_095': {'q': 'दो बसें एक स्टेशन से एक साथ निकलती हैं। पहली बस हर 12 मिनट में और दूसरी बस हर 15 मिनट में वापस आती है। वे कितने समय बाद फिर से एक साथ स्टेशन पर मिलेंगी?', 'cls': 6},
    'bank_098': {'q': 'एक गाँव में स्थित त्रिकोणीय खेत का आधार १२\u202fसेमी और ऊँचाई ९\u202fसेमी है। इस त्रिकोण का क्षेत्रफल निकालिए।', 'cls': 9},
    'bank_100': {'q': 'बिंदु (x, 4) रेखा 2x + 3y = 18 पर स्थित है। x का मान ज्ञात कीजिए।', 'cls': 11},
    'bank_102': {'q': 'A farmer has a rectangular field that is 120 meters long and 80 meters wide. He wants to fence it with a single wire. What is the total length of the wire needed?', 'cls': 6},
    'bank_108': {'q': 'एक कार 7 घंटे में 420 किमी की दूरी तय करती है। कार की चाल ज्ञात कीजिए।', 'cls': 12},
    'bank_110': {'q': "A grandfather is 3 times his son's age plus 12 years. The grandfather is 33 years old. How old is the son?", 'cls': 7},
    'bank_112': {'q': 'एक खेत के त्रिकोणीय भाग की आधार लंबाई १२ मीटर और ऊँचाई ५ मीटर है। उसका क्षेत्रफल निकालिए।', 'cls': 9},
    'bank_118': {'q': 'Divide Rs 5400 between Asha and Bala in the ratio 5:4. How much does each get?', 'cls': 8},
    'bank_119': {'q': 'एक बगीचे में त्रिकोणीय पथ है जिसकी लंबाई (आधार) ७ फुट और ऊँचाई ५ फुट है। पथ का क्षेत्रफल क्या होगा?', 'cls': 9},
    'book_007': {'q': 'एक कार 2.2 घंटे में 89.1 ाउ की दूरी तय करती है। कार द्वारा 1 घंटे में तय की गई औसत दूरी कितनी है?', 'cls': 7},
    'book_018': {'q': 'Find the mean of the following data and share your observations: Talk (i) The first 50 natural numbers. (ii) The first 50 odd numbers. (iii) The first 50 multiples of 4.', 'cls': 8},
    'book_021': {'q': 'निम्नलिखित संख्याओं में से प्रत्येक में न्यूनतम संख्या क्या घटाई जाए कि एक पूर्ण वर्ग संख्या प्राप्त हो जाए। इस प्रकार प्राप्त पूर्ण वर्ग संख्याओं का वर्गमूल भी ज्ञात कीजिए : (i) 402 (ii) 1989 (iii) 3250 (iv) 825 (v) 4000', 'cls': 8},
    'book_027': {'q': 'If 2 − i√3 where i = √−1 is a root of the equation x 2 + ax + b = 0, then find the value of a + b.', 'cls': 11},
    'book_040': {'q': 'एक कमरे की लम्बाई 8 मीटर और चौड़ाई 500 सेंटीमीटर है । कमरे की लम्बाई और चौड़ाई को अनुपात के रूप में लिखिए । _ : अतः 500 सेंटीमीटर ८ 5 मीटर कमरे की लम्बाई और चौड़ाई में अनुपात = 8: 5', 'cls': 6},
    'book_046': {'q': 'Use quantifiers to convert each of the following open sentences defined on N, into a true statement. i) x2 + 3x − 10 = 0 ii) 3x − 4 < 9 iii) n2 ≥ 1 iv) 2n − 1 = 5 v) Y + 4 > 6 vi) 3y − 2 ≤ 9', 'cls': 12},
    'book_047': {'q': 'एक समांतर चतुर्भुज की एक भुजा और संगत ऊँचाई क्रमशः 4 बउ और 3 बउ है। समांतर चतुर्भुज का क्षेत्रापफल ज्ञात कीजिए (आकृति 9.8)।', 'cls': 7},
    'book_052': {'q': 'A and B are events such that P(A) = 0.42, P(B) = 0.48 and P(A and B) = 0.16. Determine (i) P(not A), (ii) P(not B) and (iii) P(A or B)', 'cls': 11},
    'book_053': {'q': 'एक ऐसे घन की भुजा ज्ञात कीजिए जिसका पृष्ठीय क्षेत्रापफल 600 बउ2 है।', 'cls': 8},
    'book_054': {'q': 'An amount of Rs. 5000 is invested in three plans at rates 6%, 7% and 8% per annuam respectively. The total annual income from these investments is Rs 350. If the total annual income from first two investments is Rs. 70 more than the income from the third, find the amount invested in each plan by using Cramer’s Rule.', 'cls': 11},
    'book_056': {'q': 'In figure 18.34 the square is of sides 28 cm. It Va \\ encloses a circle touching all its sides. Find the circular area. Nw WA, Fig. 18.34', 'cls': 8},
    'book_058': {'q': 'One plate of Jowar roti costs ₹30 and one plate of Pulao costs ₹20. If x plates of Jowar roti and y plates of pulao were ordered in a day, which expression(s) describe the total amount in rupees earned that day? (a) 30x + 20y (b) (30 + 20) × (x + y) (c) 20x + 30y (d) (30 + 20) × x + y (e) 30x – 20y', 'cls': 7},
    'book_059': {'q': 'If z is a complex number such that (z - 1)/(z + 1) is purely imaginary, then what is |z| equal to?', 'cls': 11},
    'book_061': {'q': 'निम्नलिखित अनुपातों को प्रतिशत में परिवर्तित कीजिए : (ं) 3 रू 4 (इ) 2 रू 3', 'cls': 8},
    'book_066': {'q': 'Find the sum of the first 40 positive integers divisible by 6.', 'cls': 10},
    'book_068': {'q': 'Write the negation of the following statements: (i) Chennai is the capital of Tamil Nadu. (ii) 2 is not a complex number (iii) All triangles are not equilateral triangle. (iv) The number 2 is greater than 7. (v) Every natural number is an integer.', 'cls': 11},
    'book_069': {'q': 'यदि किसी डिब्बे की मिठाई को 24 बच्चों में बाँटा जाए, तो प्रत्येक बच्चे को 5 मिठाइयाँ मिलती हैं। यदि बच्चों की संख्या में 4 की कमी हो जाए, तो प्रत्येक बच्चे को कितनी मिठाइयाँ मिलेंगी?', 'cls': 8},
    'book_071': {'q': 'ऐसा कोण ज्ञात कीजिए जो अपने संपूरक के समान हो।', 'cls': 7},
    'book_079': {'q': 'गणित की एक परीक्षा में, 15 विद्यार्थियों द्वारा (25 में से) प्राप्त किए गए अंक निम्नलिखित हैं: 19ए 25ए 23ए 20ए 9ए 20ए 15ए 10ए 5ए 16ए 25ए 20ए 24ए 12ए 20 इन आँकड़ों के बहुलक और माध्यक ज्ञात कीजिए। क्या ये समान हैं? आपके एक मित्रा ने दिए हुए आँकड़ों के माध्यक और बहुलक ज्ञात किए। उस मित्रा द्वारा की गई त्राुटि, यदि कोई हो तो, बताइए और सही कीजिए: 35ए 32ए 35ए 42ए 38ए 32ए 34 माध्यक त्र 42ए बहुलक त्र 32 प्रयास कीजिए 2024.25 आँकड़ों का प्रबंधन 57', 'cls': 7},
    'book_002': {'q': 'Diagonals AC and BD of a trapezium ABCD with AB || DC intersect each other at the point O. Using a similarity criterion for two Fig. 6.35 OA OB triangles, show that \uf03d \uf0d7 OC OD 96 MATHEMATICS QR QT', 'cls': 10},
    'book_008': {'q': '5 पुस्तकों का मूल्य 7 पुस्तकों के मूल्य से 4 कम है। एक पुस्तक का मूल्य बताइये। हलः मान लीजिए कि एक पुस्तक का मूल्य ₹ > है। 5 पुस्तकों का मूल्य = 5 x रुपये 7 पुस्तकों का मूल्य = 7 x रुपये प्रश्नानुसार : 5 ८ 7x -4 या, 5६-7४ =7x -l4-7x या, -2 ४ = -l4 या, 2४ ८ 4 WT x=7 अत: एक पुस्तक का मूल्य ₹ 7 है।', 'cls': 6},
    'book_010': {'q': 'Find the angles marked below. 52° 99° 81° 48° b° c° a° a= b= c= d° e° f° 81° 99° 69° 132° 97° 83° d= e= f= g° 58° i° 122° 75° h° 54° 122° 70° 56° 58° 120° g= h= i= 27° 97° 124° j° j= Fig. 5.30 Chapter-5.indd 123 4/11/2025 7:30:40 PM Ganita Prakash | Grade 7', 'cls': 7},
    'book_017': {'q': 'एक दृत्त की CLD 52.8 सेनी. ऐ तो इत्त पृत्त की त्रिज्या am क्षेत्रफल ज्ञात्त करें| (7-3.I4) sa: qua) aN - 2zr 58.8 सेमी, = 2 x 34 xr 628 BRD wth या. aa सेनी. =r a eels =r या, at =? शा ढ5-या) 8". वृत्त का क्षेत्रफल a 3.]40600)* - 3.44 x t00 - 344 वर्ग रोने, < SP TOL बगल की आकृति में दिए गए दो संलेन्द्रीय ge की त्रिज्याएँ क्रमशः i2 St और 86 रोने हैं गो wisi भा क्षेत्रफल ज्ञात करें।', 'cls': 7},
    'book_022': {'q': 'V erify that the combined equation of lines 2x + 3y = 0 and x – 2y = 0 is a homogeneous equation of degree two.', 'cls': 12},
    'book_028': {'q': 'Refer to Example 9. How many packets of each food should be used to maximise the amount of vitamin A in the diet? What is the maximum amount of vitamin A in the diet? 2019-20 526 MATHEMATICS', 'cls': 12},
    'book_023': {'q': 'निम्नलिखित व्यंजकों में पदों के संख्यात्मक गुणांकों, जो अचर न हों, की पहचान कीजिए। (i) 5 – 3ज2 (ii) 1 ़ ज ़ ज2 ़ ज3 (iii) ग ़ 2गल ़ 3ल (iv) 100उ ़ 1000द (v) – च2ु2 ़ 7चु (vi) 1.2 ं ़ 0.8 इ (vii) 3.14 त2 (viii) 2 (स ़ इ) (पग) 0.1 ल ़ 0.01 ल2', 'cls': 7},
    'book_045': {'q': 'संलग्न पिक्चर प्रेफम के आरेख की बाहरी एवं अंतः विमाएँ व्रफमशः 24 बउ × 28 बउ एवं 16 बउ × 20 बउ हैं। यदि प्रेफम के प्रत्येक खंड की चौड़ाई समान है, तो प्रत्येक खंड का क्षेत्रापफल ज्ञात कीजिए।', 'cls': 8},
    'book_063': {'q': 'ज्ञात कीजिए : (ं) (i) 24 का 2 (ii) 46 का 2 (इ) (i) 18 का 2 3 (ii) 27 का 2 3 (ब) (i) 16 का 3 4 (ii) 36 का 3 4 (क) (i) 20 का 4 5 (ii) 35 का 4 5', 'cls': 7},
    'bank_088': {'q': 'Evaluate: 3/4 + 5/6 × 2 − 1/2.', 'cls': 6},
    'chat_138': {'q': 'सीता की माँ ने बाज़ार से 4 किलो आम 60 रुपये किलो के भाव से और 2 किलो सेब खरीदे। आमों पर कुल कितने रुपये खर्च हुए?', 'cls': 6},
    'chat_150': {'q': '144 ko 12 se bhaag do, kitana aayega?', 'cls': None},
    'bank_104': {'q': 'Find the compound interest on ₹8000 at 10% per annum for 2 years, compounded annually.', 'cls': 8},
    'chat_127': {'q': 'Evaluate: 27 + 2 × 12 − 6', 'cls': 9},
}


def _served(res):
    return (isinstance(res, dict)
            and res.get("fallback_kind") is None
            and not res.get("fallback")
            and bool((res.get("answer") or "").strip()))


def _solve(sid):
    fed = FED[sid.replace("-", "_")]
    return _solve_friendly(fed["q"], lang=None,
                           student_class=fed["cls"])


SOLVE_PINS = [
    ('bank-089', '70'),
    ('bank-092', '315'),
    ('bank-107', 'x = 6, x = 9'),
    ('bank-111', '80 minutes and 100 minutes'),
    ('bank-116', '13'),
    ('bank-120', '1/52'),
    ('book-006', 'Variance = 21.84'),
    ('book-020', '10.1053'),
    ('book-025', '1500'),
    ('book-030', '10.3441'),
    ('book-036', '5/27'),
    ('book-038', '32.5'),
    ('bank-081', '28'),
    ('bank-082', '2100'),
    ('bank-084', '2100'),
    ('bank-087', '100 and 54'),
    ('bank-095', '60'),
    ('bank-098', '54'),
    ('bank-100', 'x = 3'),
    ('bank-102', '400'),
    ('bank-108', '60 km/h'),
    ('bank-110', '7'),
    ('bank-112', '30'),
    ('bank-118', '3000'),
    ('bank-119', '17.5'),
    ('book-007', '40.5'),
    ('book-018', '25.5'),
    ('book-021', 'वर्गमूल = 44'),
    ('book-027', '3'),
    ('book-040', '8 : 5'),
    ('book-046', '∀n ∈ N'),
    ('book-047', '12'),
    ('book-052', '0.74'),
    ('book-053', '10'),
    ('book-054', '1750'),
    ('book-056', '616'),
    ('book-058', '30x + 20y'),
    ('book-059', '1'),
    ('book-061', '75%'),
    ('book-066', '4920'),
    ('book-068', 'is not the capital'),
    ('book-069', '6'),
    ('book-071', '90'),
    ('book-079', 'Median = 20, Mode = 20'),
]


@pytest.mark.parametrize("sid,want", SOLVE_PINS)
def test_wave156_families_now_solve(sid, want):
    res = _solve(sid)
    assert _served(res), (sid, res.get("answer"),
                          res.get("fallback_kind"))
    assert want in res["answer"], (sid, res["answer"])


DECLINE_PINS = [
    'book-002',
    'book-008',
    'book-010',
    'book-017',
    'book-022',
    'book-028',
    'book-023',
    'book-045',
    'book-063',
]


@pytest.mark.parametrize("sid", DECLINE_PINS)
def test_wave156_wrong_serves_now_decline(sid):
    res = _solve(sid)
    assert not _served(res), (sid, res.get("answer"))


CONTROL_PINS = [
    ('bank-088', '23/12'),
    ('chat-138', '240'),
    ('chat-150', '12'),
    ('bank-104', '1680'),
    ('chat-127', '45'),
]


@pytest.mark.parametrize("sid,want", CONTROL_PINS)
def test_wave156_correct_controls_unchanged(sid, want):
    res = _solve(sid)
    assert _served(res), (sid, res.get("answer"))
    assert res["answer"].strip() == want, \
        (sid, res["answer"])


# --- _w156_veto unit pins -------------------------------


def test_v2_bare_year_vetoes():
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "1999", "expression": "2019 - 20",
           "steps": []}
    q = ("During the year 2019-20 the school collected")
    assert _w156_veto(q, res)


def test_v2_expression_question_kept():
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "1999", "expression": "2019 - 20",
           "steps": []}
    assert not _w156_veto("2019 - 20", res)


def test_v4_proof_bare_number_vetoes():
    res = {"type": "algebra", "op": "polygon_diagonals",
           "answer": "0", "steps": []}
    assert _w156_veto(
        "Prove that the number of diagonals of a"
        " polygon is n(n-3)/2.", res)


def test_v4b_verify_system_serve_vetoes():
    fed = FED["book_022"]
    res = {"type": "algebra", "op": "system",
           "answer": "x = 0, y = 0", "steps": []}
    assert _w156_veto(fed["q"], res)


def test_v5_stem_echo_fraction_vetoes():
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "9/10", "expression": "9/10",
           "steps": []}
    q = ("A student got 9/10 marks in a test. Find"
         " (9/10 * 20) + 11.")
    assert _w156_veto(q, res)


def test_v5_genuine_evaluate_kept():
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "29",
           "expression": "(9/10 * 20) + 11", "steps": []}
    assert not _w156_veto("Find (9/10 * 20) + 11.", res)


def test_v6_class_limits_echo_vetoes():
    res = {"type": "statistics", "op": "mode",
           "answer": "1000, 1500, 2000, 2500, 3000",
           "steps": []}
    q = ("The classes are 1000, 1500, 2000, 2500 and"
         " 3000. Find the mode.")
    assert _w156_veto(q, res)


def test_v8_invented_operand_vetoes():
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "0.000179574",
           "expression": "4/22275", "steps": []}
    assert _w156_veto("Find the angles marked below.",
                      res)


def test_v9_figure_blank_harvest_vetoes():
    fed = FED["book_010"]
    res = {"type": "applied", "op": "hindi_equation",
           "answer": "i = 27", "steps": []}
    assert _w156_veto(fed["q"], res)


def test_v1_garbled_identity_vetoes_hinglish_kept():
    fed = FED["book_017"]
    res = {"type": "arithmetic", "op": "evaluate",
           "answer": "4", "expression": "4", "steps": []}
    assert _w156_veto(fed["q"], res)
    fed2 = FED["chat_150"]
    res2 = {"type": "arithmetic", "op": "evaluate",
            "answer": "12", "expression": "12",
            "steps": []}
    assert not _w156_veto(fed2["q"], res2)


def test_degree_upgrade_abstains_on_verify():
    fed = FED["book_022"]
    res = {"type": "algebra", "op": "system",
           "answer": "x = 0, y = 0", "steps": []}
    assert degree_upgrade(fed["q"], res) is None


def test_degree_upgrade_still_upgrades_degree_ask():
    res = {"type": "algebra", "op": "simplify",
           "answer": "2*x**2 + 5*x + 10", "steps": []}
    up = degree_upgrade(
        "Find the degree of the polynomial"
        " 3x^3 + 2x^2 + 5x + 7", res)
    assert up is not None and up["answer"] == "3"


def test_meta_data_list_veto_book079():
    fed = FED["book_079"]
    assert meta_result(fed["q"], "dev") is None


def test_reasoning_answer_is_not_junk():
    fed = FED["book_046"]
    res = {"type": "applied",
           "op": "reasoning_quantifier",
           "answer": "(i) ∃x ∈ N such that"
           " x^2 + 3x - 10 = 0 (x = 2 works)",
           "steps": []}
    assert not _is_junk(fed["q"], res)

