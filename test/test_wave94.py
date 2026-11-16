"""Wave 94: Class 10 papers pack.

Part 1 — the two located-but-not-transcribed Class 10 papers
from the Wave 66 notes are now typed into papers_data: GSEB
2025 (54 questions) and UBSE 2025 in English and Hindi (the
bilingual booklet stored as two entries, 34 stored questions
each for the 27 printed questions).

Part 2 — the Wave 71 audit's Class 10 papers-source failures
that are method gaps (not OR / Assertion-Reason / case-study
formats — Wave 82 — and not proofs) are closed by strict
schemas in solver/papers10.py, wired into the router's
failure-only tail next to the Wave 77 core pass. Every case
below is a verbatim audit question with its hand-verified
answer.
"""
import pytest

import papers_data
from solver.papers10 import solve_papers10
from solver.router import solve_question


CASES = [
    (0, '10 सेमी० त्रिज्या वाले अर्धवृत्त की कुल परिमिति होगी– (a) (π + 2)10 सेमी० (b) (π + 1)10 सेमी० (c) 10π सेमी० (d) (π + 5)10 सेमी०', '10π + 20'),
    (1, 'Check Whether 301 is a term of the list of numbers 5, 11, 17, 23, … ?', 'not a term'),
    (2, 'The sum of first n odd natural numbers is (A) n² − 1 (B) n + 1 (C) 2n − 1 (D) n²', 'n^2'),
    (3, "यदि समांतर श्रेढ़ी का पहला पद 'a' और सार्वअंतर 'd' है, तो प्रथम n पदों का योगफल होगा– (a) n{2a + (n − 1) × d} (b) n(n + 1)/2 (c) (n/2){2a + (n − 1) × d} (d) (1/2){a + (n − 1)d}", '(n/2){2a + (n - 1) × d}'),
    (4, 'The Co-ordinates of the mid-point of the line segment joining the points P(4, −5) and Q(8, 7) are (A) (2, 6) (B) (6, −1) (C) (6, 1) (D) (−2, −6)', '(6, 1)'),
    (5, 'x-अक्ष पर स्थित सभी बिन्दुओं की कोटि होती है– (a) 0 (b) 1 (c) 2 (d) −1', '0'),
    (6, 'बिन्दुओं (5, −6) और (−1, −4) को जोड़ने वाले रेखाखंड को x-अक्ष किस अनुपात में विभाजित करती है?', '3 : 2 (externally)'),
    (7, 'Find the value sin35°·cos55° + cos35°sin55°.', '1'),
    (9, 'यदि A तथा B पूरक कोण हैं, तो (a) sinB = sinB (b) secA = cosecB (c) cotA = cotB (d) tanA = tanB', 'secA = cosecB'),
    (11, 'If α and β are zeros of the polynomial f(x) = 5x² − 7x + 1. Find the value of α² + β².', '39/25'),
    (12, 'बहुपद (x + 3)²(x³ − 8) का घात है– (a) 2 (b) 5 (c) 6 (d) 4', '5'),
    (13, 'तीन पासों की उछाल में संभव परिणामों की संख्या होगी – (a) 216 (b) 136 (c) 128 (d) 18', '216'),
    (14, 'The diagonal of a rectangular field is 60 metres more than the shorter side. If the longer side is 30 metres more than the shorter side, find the sides of the field.', '90 metres and 120 metres'),
    (16, 'Which of the following has terminating decimal expansion? (A) 11/91 (B) 15/23 (C) 17/80 (D) 7/45', '17/80'),
    (17, 'निम्नलिखित में से कौन-सा युग्म सह-अभाज्य है? (a) (15, 45) (b) (9, 16) (c) (21, 105) (d) (14, 84)', '(9, 16)'),
    (18, 'एक व्यक्ति, जो नदी के एक किनारे पर खड़ा है नदी के दूसरे किनारे पर स्थित एक पेड़ के शिखर का उन्नयन कोण 60° पाता है। जब वह व्यक्ति किनारे से 36 मीटर पीछे हट जाता है, तो वह उन्नयन कोण 30° का हो जाता है। पेड़ की ऊँचाई तथा नदी की चौड़ाई ज्ञात करें।', '18·√3'),
    (19, 'If the radius and height of a cylinder and a cone be equal then the ratio of their volumes will be– (A) 1 : 3 (B) 3 : 1 (C) 3 : 4 (D) 2 : 3', '3 : 1'),
    (20, 'यदि किसी लंबवृत्तीय बेलन की ऊँचाई उसके आधार की त्रिज्या की दुगुनी है एवं उसके वक्र पृष्ठ का क्षेत्रफल 616 सेमी²० है, तो उसके आधार की त्रिज्या निकालें।', '7 cm'),
    (21, 'In ΔPQR if PR² = PQ² + QR² then ∠Q = (A) 45° (B) 60° (C) 75° (D) 90°', '90°'),
    (22, 'दो समरूप त्रिभुजों की संगत ऊँचाइयाँ 7 सेमी० तथा 10 सेमी० हैं, तो उनके क्षेत्रफलों का अनुपात होगा– (a) 49 : 100 (b) 100 : 49 (c) √10 : √7 (d) √7 : √10', '49 : 100'),
    (23, 'A piece of wire 22 cm long is bent into the form of an arc of a circle subtending an angle of 60° at its centre. Find the radius of the circle. [Use π = 22/7]', '21 cm'),
    (25, 'In Fig. 1, triangle ABC is circumscribing a circle, with AR = 4 cm, AC = 11 cm and BP = 3 cm (P, Q, R being the points of contact on BC, CA, AB respectively as shown in the figure). The length of BC is ______ cm.', '10 cm'),
    (26, 'The value of p, for which the points A(3, 1), B(5, p) and C(7, -5) are collinear, is (A) -2 (B) 2 (C) -1 (D) 1', 'p = -2'),
    (27, 'The value of k for which the system of equations x + y - 4 = 0 and 2x + ky = 3, has no solution, is (A) -2 (B) ≠ 2 (C) 3 (D) 2', 'k = 2'),
    (28, 'Which of the following is a quadratic polynomial having zeroes −2/3 and 2/3? (A) 4x² − 9 (B) 9x² + 4 (C) x² + 9/4 (D) 5(9x² − 4)', '5(9x² - 4)'),
    (30, 'Probability of happening of an event is denoted by p and probability of non-happening of the event is denoted by q. Relation between p and q is: (A) p + q = 1 (B) p = 1, q = 1 (C) p = q − 1 (D) p + q + 1 = 0', 'p + q = 1'),
    (32, 'Which of the following cannot be the unit digit of 8^n, where n is a natural number? (A) 4 (B) 2 (C) 0 (D) 6', '(C) 0'),
    (34, 'If the mean of the first n natural numbers is 15, then find n.', '29'),
    (35, 'The following distribution shows the number of runs scored by some batsmen in test matches: Runs scored: 3000-4000, 4000-5000, 5000-6000, 6000-7000; Number of batsmen: 5, 10, 9, 8. The lower limit of the modal class is: (A) 3000 (B) 4000 (C) 5000 (D) 6000', '4000'),
    (36, 'In the given figure, PQ ∥ XY ∥ BC, AP = 2 cm, PX = 1.5 cm and BX = 4 cm. If QY = 0.75 cm, then AQ + CY is equal to: (A) 6 cm (B) 4.5 cm (C) 3 cm (D) 5.25 cm', '3 cm'),
    (37, 'Area of a sector of angle P (in degrees) of a circle with radius R is: (A) (P/180) × 2πR (B) (P/180) × πR² (C) (P/360) × 2πR (D) (P/720) × 2πR²', '(P/720)'),
    (38, '5 सेमी त्रिज्या वाले एक वृत्त के बिन्दु P पर स्पर्श रेखा PQ केन्द्र O से जाने वाली एक रेखा से बिन्दु Q पर इस प्रकार मिलती है कि OQ = 12 सेमी, PQ की लंबाई है: (a) 12 सेमी (b) 13 सेमी (c) 8 सेमी (d) √119 सेमी', '√119'),
    (41, 'A girl of height 90 cm is walking away from the base of a lamp post at the speed of 1.2 m/s. If the lamp is 3.6 m above the ground. Find the length of her shadow after 4 second.', '8/5 m'),
    (45, 'समान्तर श्रेढ़ी 7, 13, 19, . . . . , 205 में पदों की संख्या ज्ञात कीजिए।', '34'),
    (46, 'बिन्दुओं (5, 3) और (−3, −2) को मिलाने वाला रेखाखण्ड x-अक्ष द्वारा किस अनुपात में विभाजित होता है?', '3 : 2'),
    (47, 'If tan θ = a/b, then the value of (b sin θ − a cos θ)/(b sin θ + a cos θ) will be: (A) 1 (B) 0 (C) (a² − b²)/(a² + b²) (D) (b² − a²)/(b² + a²)', '0'),
    (48, 'दिये गये चित्र में, ΔABC के आधार BC के समान्तर रेखाखण्ड PQ खींचा गया है। यदि PQ : BC = 1 : 3 हो, तो AP और BP का अनुपात होगा (a) 1:2 (b) 2:3 (c) 1:4 (d) 1:3', '1 : 2'),
]


@pytest.mark.parametrize("idx,question,want", CASES,
                         ids=[f"audit-{i}" for i, _, _ in CASES])
def test_papers10_schema_answers(idx, question, want):
    out = solve_papers10(question)
    assert out is not None, idx
    assert want in str(out["answer"]), (idx, out["answer"])


def test_papers10_wired_into_router():
    # the hook fires through the real solve path, not only
    # when the module is called directly
    for idx, question, want in (CASES[1], CASES[10], CASES[30]):
        out = solve_question(question)
        assert out is not None and want in str(out["answer"]), idx


def test_papers10_does_not_hijack_solved_questions():
    # the quadratic-formula question is solved by the main
    # solver; the degree schema must not fire on the word
    # 'द्विघात' alone
    q = ("द्विघात सूत्र का उपयोग कर समीकरण x² + 7x − 60 = 0 "
         "का मूल निकालें।")
    assert solve_papers10(q) is None


def test_former_wave76_examples_now_solved_by_derivation():
    # Wave 76 used these two questions as 'cannot be solved /
    # pure recall' examples. Wave 94 solves both for real —
    # the AP-sum identity is derived, and the axis ordinate
    # is a stated coordinate fact (BSEB 2025 audit item) —
    # so the mcq layer may now name the matching option.
    out = solve_papers10(
        "The sum of first n odd natural numbers is "
        "(A) n² − 1 (B) n + 1 (C) 2n − 1 (D) n²")
    assert out is not None and out["answer"] == "n^2"
    out = solve_papers10(
        "x-अक्ष पर स्थित सभी बिन्दुओं की कोटि होती है– "
        "(a) 0 (b) 1 (c) 2 (d) −1")
    assert out is not None and out["answer"] == "0"


def test_papers10_ignores_non_paper_questions():
    assert solve_papers10("What is 2 + 2?") is None
    assert solve_papers10(
        "Find the derivative of x^3 + 2x.") is None
    assert solve_papers10(
        "A train travels 360 km in 4 hours. Find its speed."
    ) is None


# ---------------------------------------------------------------------------
# Part 1: the two new papers
# ---------------------------------------------------------------------------

def test_gseb_paper_stored_completely():
    p = papers_data.get_paper("gseb-10-2025")
    assert p["class_num"] == 10 and p["year"] == 2025
    assert len(p["questions"]) == 54
    assert [q["number"] for q in p["questions"]] == \
        list(range(1, 55))
    from collections import Counter
    secs = Counter(q["section"] for q in p["questions"])
    assert secs == {"A": 24, "B": 13, "C": 9, "D": 8}
    # sections B–D are attempt-any subsets, so the printed
    # maximum (80) is an override, not the stored sum (109)
    assert p["max_marks"] == 80
    assert sum(q["marks"] for q in p["questions"]) == 109


def test_ubse_paper_stored_completely_both_mediums():
    for pid in ("ubse-10-2025", "ubse-10-2025-hindi"):
        p = papers_data.get_paper(pid)
        assert p["class_num"] == 10 and p["year"] == 2025
        # 27 printed questions; Q1's eight MCQ parts are
        # stored separately, all numbered 1
        assert len(p["questions"]) == 34
        assert [q["number"] for q in p["questions"]] == \
            [1] * 8 + list(range(2, 28))
        assert sum(q["marks"] for q in p["questions"]) == 80
        assert p["max_questions"] == 27
        assert p["full_count"] == {"A": 16, "B": 7, "C": 5,
                                   "D": 6}
        assert p["full_marks"] == {"A": 16, "B": 14, "C": 20,
                                   "D": 30}


def test_ubse_hindi_entry_metadata():
    p = papers_data.get_paper("ubse-10-2025-hindi")
    assert p["medium"] == "hindi"
    assert p["subject_label"] == "गणित"
    assert p["hindi_section_letters"] == {
        "A": "अ", "B": "ब", "C": "स", "D": "द"}


def test_new_papers_figure_census():
    counts = {pid: sum(q["text"].count("[Figure]")
                       for q in papers_data.get_paper(pid)
                       ["questions"])
              for pid in ("gseb-10-2025", "ubse-10-2025",
                          "ubse-10-2025-hindi")}
    assert counts == {"gseb-10-2025": 1, "ubse-10-2025": 3,
                      "ubse-10-2025-hindi": 3}
