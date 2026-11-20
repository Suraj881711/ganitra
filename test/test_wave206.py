"""Wave 206 (test-loop fix-queue, 20 Nov 2026): native
schemas for the messy student-dress families the teeno-AI
test loop queued — story add/sub chains and backward
stories, fraction stories, integer walks, verbal equations,
roots from area/volume, polynomials buried in noisy text,
dressed quadratics, trig value atoms, determinant-with-
unknown matrices, junior multiply/divide stories, and the
series shapes the Wave-202 engine cannot see (nth term,
AP sum in words, then/fir-separated terms).

Every queue row is pinned verbatim below. Two queue rows
are NOT pinned as solves, on purpose (see the last section):
their expected answers do not follow from their own text,
so the wave declines them rather than guess.
"""
import pytest

import fallback
from solver.wave206 import solve_wave206


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the real AI legs stay inert."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _native(question, expected):
    out = fallback.fallback_answer(question)
    assert out.get("fallback_kind") is None, (
        f"{question!r} not native: kind="
        f"{out.get('fallback_kind')} answer="
        f"{out.get('answer')!r}")
    assert str(out.get("op", "")).startswith("w206_"), (
        f"{question!r} op={out.get('op')}")
    assert str(out.get("answer")) == expected, (
        f"{question!r} -> {out.get('answer')!r}, "
        f"expected {expected!r}")
    return out


def _module(question, expected):
    out = solve_wave206(question)
    assert out is not None, f"{question!r} declined"
    assert str(out.get("answer")) == expected, (
        f"{question!r} -> {out.get('answer')!r}, "
        f"expected {expected!r}")
    return out


# ---------------------------------------------------------------------------
# 1. Story chains (Class 4) — queue verbatim + paraphrases
# ---------------------------------------------------------------------------

def test_chain_rupee_hinglish():
    _native("Mere paas 45 rupee the, maine 12 rupee ka "
            "chocolate kharida, phir mere bhai ne 20 rupee "
            "aur de diye. Ab mere paas kitne rupee bache?",
            "53")


def test_chain_mangoes_devanagari():
    _native("राहुल के पास 30 आम थे। उसने अपने दोस्त को 8 आम "
            "दे दिए और फिर बाजार से 15 और आम खरीदे। अब उसके "
            "पास कुल कितने आम हैं?", "37")


def test_chain_marbles_english():
    _native("I had 100 marbles, I gave 27 to my sister and "
            "then found 13 more under the couch. How many "
            "marbles now?", "86")


def test_chain_short_form():
    _native("50 rupee se 23 rupee kharch kiye, phir 10 "
            "rupee mil gaye. ans?", "37")


def test_chain_four_events():
    _native("Maya bought 12 mangoes, ate 4, then her "
            "grandma gave her 9 more. Later she gave 5 to "
            "neighbor. How many mangoes left?", "12")


def test_chain_spends_and_change():
    _native("If a boy has 68 rupees and spends 25 rupees "
            "on a book, then receives 10 rupees as change, "
            "how much does he have now?", "53")


def test_chain_negative_start():
    _native("Rohan ne apne pocket me -10 rupees rakhe the, "
            "phir usne market se 25 rupees kamaye. Ab uske "
            "paas kitne rupees hain?", "15")


def test_chain_paraphrase_english_two_events():
    _module("Sara had 80 stickers, she gave 15 to her "
            "friend and then bought 20 more. How many "
            "stickers now?", "85")


def test_chain_paraphrase_hinglish_lost_found():
    _module("mere paas 60 rupaye the, 18 kharch ho gaye, "
            "phir 25 mil gaye. ab kitne bache?", "67")


# ---------------------------------------------------------------------------
# 2. Backward stories + verbal equations
# ---------------------------------------------------------------------------

def test_backward_gave_left_hinglish():
    _native("sir mere pas kch chocolates thi... 5 maine "
            "chote bhai ko de di ab mere pas 12 bachi h. "
            "toh starting me kitni thi mere pas??", "17")


def test_backward_spent_left_devanagari():
    _native("मेरे पास कुछ पैसे थे, 15 रुपये की मम्मी ने "
            "सब्जी मंगा ली अब 45 बचे हैं. पहले कितने थे?",
            "60")


def test_backward_per_friend_form():
    _native("आज स्कूल में हम सबको 5 रुपये का कैंडी दिया "
            "गया। मैं 3 दोस्त को 2-2 रुपये दे दिया, फिर "
            "मेरे पास बचा 7 रुपये। तो शुरू में मेरे पास "
            "कितने रुपये थे?", "13")


def test_verbal_double_plus():
    _native("एक नंबर के डबल में 7 जोड़ने पर 25 आता है. "
            "बताओ वो नंबर कौन सा है?", "9")


def test_verbal_double_plus_english():
    _module("double of a number plus 5 is 21. what is "
            "the number?", "8")


def test_consecutive_smallest():
    _native("teen lagatar numbers ko plus kiya toh 18 "
            "aaya... sabse chota wala number kaunsa hai??",
            "5")


def test_consecutive_largest_english():
    _module("three consecutive numbers add up to 27. "
            "largest number?", "10")


def test_ages_sum():
    _native("my friend aman is 5 years elder than me... "
            "if we add both our ages it is 25. what is my "
            "age??", "10")


def test_equal_parts_total():
    _native("i have some pens i divide them into 4 equl "
            "parts... evry part has 8 pens... total pens "
            "kitne hai mere pas??", "32")


# ---------------------------------------------------------------------------
# 3. Fractions
# ---------------------------------------------------------------------------

def test_frac_chain_kg():
    _native("bhai mere paas 1/4 kg apple the aur mummy ne "
            "2/4 kg aur de diye... ab total kitne hue mere "
            "pas batao jaldi", "3/4 kg")


def test_frac_chain_milk_devanagari():
    _module("मेरे पास 1/2 लीटर दूध था, पापा 1/4 लीटर और ले "
            "आए। अब कुल कितना दूध है?", "3/4")


def test_frac_chain_bucket():
    _module("ek bucket 3/10 full thi. maine 4/10 aur pani "
            "dala. fir 1/10 gir gaya. ab kitna bacha "
            "bucket me?", "3/5")


def test_frac_whole_minus():
    _native("sir i have 1 whole cake i ate 3/8 of it. "
            "how much is left?? plss help i am confused",
            "5/8")


def test_frac_of_money_left():
    _native("i have 500 rupees. i spent 2/5 of it on a "
            "toy. how much money is left with me now??",
            "300")


def test_frac_group_complement():
    _native("mere class me 40 students hai. usme se 3/5 "
            "girls hain. toh boys kitne hue? calculation "
            "nahi ho raha mere se.", "16")


def test_frac_compare_hinglish():
    _native("konsa bada hai 5/6 ya 7/9?? jaldi batao exam "
            "me aaya hai", "5/6 is bigger")


def test_frac_compare_smaller_english():
    _module("which is smaller: 3/7 or 4/9?",
            "3/7 is smaller")


# ---------------------------------------------------------------------------
# 4. Integers
# ---------------------------------------------------------------------------

def test_int_bare_expression_in_filler():
    _native("iska ans batao: -15 + 9 = ?", "-6")


def test_int_add_words():
    _native("Bhai, agar -5 aur +12 ko add karte hain to "
            "result kya aayega? batao.", "7")


def test_int_subtract_negative_from_it():
    _native("I have -20, then I subtract -7 from it, what "
            "is left?", "-13")


def test_int_number_line_devanagari():
    _native("एक संख्या रेखा पर -3 से शुरू करो, फिर 8 कदम "
            "दाहिनी ओर बढ़ो, अंत में कौन सी संख्या मिलेगी?",
            "5")


def test_int_number_line_roman():
    _native("Number line pe -2 se start karke 4 left jao, "
            "phir 6 right, phir 3 left. Final position?",
            "-3")


def test_int_ladder_from_zero():
    _native("If I go down 7 steps (negative) and then up "
            "14 steps on the integer ladder, where do I "
            "land?", "7")


# ---------------------------------------------------------------------------
# 5. Roots
# ---------------------------------------------------------------------------

def test_root_bare_in_filler():
    _native("iska ans batao: √(81) = ?", "9")


def test_root_area_square_devanagari():
    _native("अगर एक खेत का क्षेत्रफल 225 वर्ग मीटर है, तो "
            "उस खेत की एक बगल की लंबाई (जो बराबर है) क्या "
            "होगी? (अर्थात् √225)", "15")


def test_root_area_square_english():
    _native("Riya bought a chocolate bar shaped like a "
            "perfect square. The total area is 196 cm². "
            "How long is each side of the bar?", "14")


def test_root_volume_cube():
    _native("I have a box that can hold 64 cubes. If each "
            "side of the cube is same length, what's the "
            "length of one side?", "4")


# ---------------------------------------------------------------------------
# 6. Polynomials
# ---------------------------------------------------------------------------

def test_poly_expand_noisy():
    _native("sir ye wala dekho... (x+3)^2 - (x-3)^2 solve "
            "karke kya bachega? shortcut se batao pls",
            "12·x")


def test_poly_factor_noisy_hindi():
    _native("सर x^2 + 5x + 6 का factor kya hoga?? jaldi "
            "batao exam hai kal", "(x + 2)·(x + 3)")


def test_poly_factor_verbal_squares():
    _native("bhai 4x square minus 9y square ko factorise "
            "kaise karte hai? exams aa rahe hai darr lag "
            "raha", "(2·x - 3·y)·(2·x + 3·y)")


def test_poly_identity_cubes_ratio():
    _native("if x+y+z=0 then what is x cube + y cube + "
            "z cube divided by xyz? my teacher gave this "
            "today and i am stuck", "3")


def test_poly_area_side():
    _native("I have a square park with area x^2 + 10x + "
            "25. What is the length of one side of the "
            "park? My dad is asking for the garden fence.",
            "x + 5")


def test_poly_remainder_hinglish():
    _native("if p(x) = x^3 - 2x^2 + x - 1 is divided by "
            "x-2 then remainder kitna bachega? help kardo "
            "frnds", "1")


def test_poly_eval_assignments():
    _native("wo formula hai na (a+b+c) square wala... "
            "agar a=1, b=2 aur c=-3 hai toh (a+b+c)^2 ka "
            "value kya hoga?", "0")


# ---------------------------------------------------------------------------
# 7. Quadratics
# ---------------------------------------------------------------------------

def test_quad_sum_product_costs():
    _native("If the product of the costs of two types of "
            "pens is Rs. 120 and their sum is Rs. 23, find "
            "the individual costs.", "8 and 15")


def test_quad_sum_squares_devanagari():
    out = solve_wave206(
        "एक बॉलिस्टर में दो गेंदें हैं, उनका वजन x और "
        "(x+3) किग्रा है, और उनका वर्गों का योग 85 है। तो "
        "x के लिये quadratic equation बनाओ और हल करो।")
    assert out is not None
    assert "sqrt(161)" in out["answer"]


def test_quad_bare_equation_in_story():
    _native("एक कार की गति v km/h है। अगर वह 2 घंटे में "
            "तय किया गया दूरी 2v^2 - 10v = 0 km के बराबर "
            "है, तो v क्या होगा?", "v = 0, v = 5")


def test_quad_roots_to_coefficient():
    _native("my friend says if x^2 + bx + 12 = 0 has "
            "roots 3 and -4, what is b?", "b = 1")


# ---------------------------------------------------------------------------
# 8. Trigonometry
# ---------------------------------------------------------------------------

def test_trig_sin75_hinglish():
    _native("Bhaiya ye sin 75 kaise nikalte hai? value "
            "bata do point me nahi fraction me chahiye "
            "root wala.", "sqrt(2)/4 + sqrt(6)/4")


def test_trig_tan15_degree_word():
    _native("Sir homework help. What is the value of "
            "tan 15 degree? I need the simple answer with "
            "root.", "2 - sqrt(3)")


def test_trig_double_angle_product():
    _native("ye solve krna h... 2 sin 15 cos 15 kitna "
            "hota h??", "1/2")


def test_trig_complementary_squares():
    _native("Exam me ek ques aaya tha ki sin square 1 "
            "degree plus sin square 89 degree kitna hota "
            "hai? Mere dost ne bola 1 hai but i am not "
            "sure.", "1")


def test_trig_max_asinx_bcosx():
    _native("Yaar ye 3 sin x + 4 cos x ki maximum value "
            "kya hogi? logic bhul gaya.", "5")


def test_trig_tan_sum_from_values():
    _native("agar tan x 1/2 h aur tan y 1/3 h toh tan of "
            "x+y kitna ayega? simple wala batao.", "1")


# ---------------------------------------------------------------------------
# 9. Matrices
# ---------------------------------------------------------------------------

def test_matrix_det_unknown_2x2():
    _native("Bhai, ek 2x2 matrix A = [[3, -1],[k, 5]] "
            "hai. Iska determinant 14 hai. k ka value kya "
            "hai?", "k = -1")


def test_matrix_det_unknown_devanagari_rows():
    _native("एक 3×3 मैट्रिक्स B है जिसके तत्व हैं: पहली "
            "पंक्ति 1,2,3; दूसरी पंक्ति a,4,5; तीसरी "
            "पंक्ति 6,7,8. अगर det(B)=0 हो तो a का मान "
            "निकालो।", "a = 3")


def test_matrix_trace_and_det():
    _native("Mere ko ek 2x2 matrix C diya gaya hai: "
            "C = [[x,5],[3,x+2]]. Iska trace (sum of "
            "diagonal) 12 hai aur determinant 20 hai. x "
            "ka value nikal.", "x = 5")


def test_matrix_det_zero_devanagari():
    _native("2×2 मैट्रिक्स D = [[-2, a],[4, 6]] का "
            "डिटरमिनेंट 0 है, a निकालो।", "a = -3")


def test_matrix_triangular_product():
    _native("If A = [[1,2,3],[0,b,5],[0,0,c]] then "
            "det(A)= 60. Find b*c.", "b*c = 60")


def test_matrix_tuple_rows():
    _native("Yaar, ek 3x3 matrix E le, uske rows hain: "
            "(p,1,2), (3,4,5), (6,7,8). Agar is matrix ka "
            "determinant -10 ho, to p ka value kya hoga?",
            "p = 10/3")


# ---------------------------------------------------------------------------
# 10. Junior multiply / divide stories
# ---------------------------------------------------------------------------

def test_junior_groups_total_broken_english():
    _native("there is 6 box and in each box 7 pencil how "
            "much total pencil?", "42")


def test_junior_groups_total_each():
    _native("There are 8 boxes with 6 apples each. How "
            "many apples are there?", "48")


def test_junior_per_person_total():
    _native("meri maa ne 24 students ko 5 laddoo dega, "
            "kitna laddoo chahiye?", "120")


def test_junior_share_baanto():
    _native("bhai 234 chocolate ke 3 kutty me baanto "
            "kitna kutty banega?", "78")


def test_junior_share_per_customer():
    _native("ek kirana store me 8 customers aaye, 56 "
            "biscuits bikaye, har customer ko kitna?", "7")


def test_junior_share_two_numbers():
    _native("12 chocolate, 4 dost, kitna mota? iska ans "
            "batao", "3")


def test_junior_average_rate():
    _native("ek tanki 40 litre bhari thi, usne 8 ghante "
            "chal diye, average kitna?", "5")


# ---------------------------------------------------------------------------
# 11. Series shapes Wave 202 cannot see
# ---------------------------------------------------------------------------

def test_series_nth_term_ap():
    _native("bhai ek help chahiye maths homework mein... "
            "series hai 5, 12, 19 and so on... iska 10th "
            "number kya hoga?? jaldi batao pls", "68")


def test_series_nth_term_gp_paraphrase():
    _module("series 3, 6, 12, 24 ka 7th term kya hoga?",
            "192")


def test_series_sum_ap_words():
    _native("agar hum 2, 4, 6 aise karke 10 numbers ko "
            "add kare toh total kitna hoga?? help me",
            "110")


def test_series_then_separated_gp():
    _native("my teacher gave one sequence 2 then 6 then "
            "18... i dont know what comes after 18. pls "
            "help fast exam tomorrow", "54")


def test_series_fir_separated_squares():
    _native("ek game khel rahe the usme numbers aise "
            "chal rahe hain 2 fir 5 fir 10 fir 17... agla "
            "prediction kya hai? logic kya hai?", "26")


# ---------------------------------------------------------------------------
# 12. Decline discipline — shapes the wave must NOT claim
# ---------------------------------------------------------------------------

def test_decline_ambiguous_sharing_story():
    # Queue row [13]: "20 dost ko barabar baant diya" —
    # 20 is the FRIEND count, not marbles given away; the
    # generator's expected 155 assumes the other reading.
    # The text does not settle it, so the wave declines.
    assert solve_wave206(
        "मेरे पास 200 marbles थे, मैंने 55 खो दिए और फिर "
        "30 और खरीदे, फिर मैं 20 दोस्त को बराबर बाँट "
        "दिया। अब मेरे पास कितने बचे?") is None


def test_decline_broken_question_row():
    # Queue row [63]: 16 mile, 4 baantkar khaye, "kitne
    # mile?" — the expected 4 follows from no reading of
    # the text (16 − 4 = 12 bache would be the story
    # answer); the wave must not divide 16 by 4 to match.
    assert solve_wave206(
        "मुझे १६ लौवाँ मिले, मैंने ४ लौवाँ बाँटकर खाए, "
        "मुझे कितने लौवाँ मिले?") is None


def test_decline_plain_det_no_unknown():
    assert solve_wave206(
        "find the determinant of [[1,2],[3,4]]") is None


def test_decline_unrelated_text():
    assert solve_wave206(
        "what is the capital of india?") is None
    assert solve_wave206(
        "essay on my school in 200 words") is None


def test_decline_story_with_unclassified_event():
    # "bech diye" (sold) is not a modelled event verb —
    # the chain must decline rather than guess a sign.
    assert solve_wave206(
        "ram ke paas 50 aam the, usne 20 bech diye, phir "
        "10 aur kharide. ab kitne bache?") is None
