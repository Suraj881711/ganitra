"""Wave 192: P&C counting WORD forms (form audit B.7).

statistics.py computes nPr / nCr only from the explicit
"nPr" dress, so the NCERT Ex 6.1-6.4 word forms had no
parser and the audit's probes 25-26 parse-errored:

  25  team of 3 boys + 3 girls from 5 boys + 4 girls -> 40
  26  committee of 7 from 9 boys + 4 girls, exactly
      3 girls -> 504

Fix: solver/pnc192.py — strict word-form schemas (selections
with conditions, letter arrangements, digit numbers,
C(n, 2) / C(n, 3) geometric dresses) behind a failure-only
gate in router.py after the Wave 175 block.  Every expected
value below was verified independently (hand computation in
the comments, several also by brute-force enumeration while
building); uncertain parses decline to None — a wrong count
is worse than a native miss.
"""
from solver.pnc192 import solve_pnc_word
from solver.router import solve_question

PROBE25 = ("In how many ways can a team of 3 boys and 3 girls "
           "be selected from 5 boys and 4 girls?")
PROBE26 = ("A committee of 7 has to be formed from 9 boys and "
           "4 girls. In how many ways can this be done when "
           "the committee consists of exactly 3 girls?")
COMMITTEE = ("A committee of 7 has to be formed from 9 boys "
             "and 4 girls. In how many ways can this be done "
             "when the committee consists of ")


def ans(q):
    out = solve_pnc_word(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_pnc_word(q) is None, q


# ------------------------------------------------------------------
# Audit probes, verbatim
# ------------------------------------------------------------------

def test_probe25_verbatim_schema():
    # C(5, 3) = 10, C(4, 3) = 4, product 10 x 4 = 40.
    out = solve_pnc_word(PROBE25)
    assert out["op"] == "pnc_word"
    assert out["answer"] == "40"


def test_probe25_via_router():
    out = solve_question(PROBE25)
    assert out["op"] == "pnc_word"
    assert out["answer"] == "40"


def test_probe26_verbatim_schema():
    # Exactly 3 girls -> 4 boys: C(4, 3) x C(9, 4).
    # C(9, 4) = 9*8*7*6 / 24 = 3024 / 24 = 126; 4 x 126 = 504.
    out = solve_pnc_word(PROBE26)
    assert out["op"] == "pnc_word"
    assert out["answer"] == "504"


def test_probe26_via_router():
    out = solve_question(PROBE26)
    assert out["op"] == "pnc_word"
    assert out["answer"] == "504"


# ------------------------------------------------------------------
# A. Selections with conditions
# ------------------------------------------------------------------

def test_at_least_girls():
    # j=3: 504; j=4: C(4,4) x C(9,3) = 1 x 84 = 84; total 588.
    assert ans(COMMITTEE + "at least 3 girls?") == "588"


def test_at_most_girls():
    # j=0: 36; j=1: 4 x 84 = 336; j=2: 6 x 126 = 756;
    # j=3: 504; total 36+336+756+504 = 1632.
    assert ans(COMMITTEE + "at most 3 girls?") == "1632"


def test_condition_on_boys():
    # Exactly 4 boys -> 3 girls: C(9, 4) x C(4, 3) = 504.
    assert ans(COMMITTEE + "exactly 4 boys?") == "504"


def test_pool_order_reversed():
    q = ("A committee of 7 has to be formed from 4 girls and "
         "9 boys. In how many ways can this be done when the "
         "committee consists of exactly 3 girls?")
    assert ans(q) == "504"


def test_at_least_one_girl_boundary():
    # C(10, 5) - C(6, 5) = 252 - 6 = 246.
    q = ("A committee of 5 has to be formed from 6 boys and "
         "4 girls. In how many ways can this be done when "
         "the committee consists of at least 1 girl?")
    assert ans(q) == "246"


def test_at_most_full_range_boundary():
    # At most 4 girls covers every feasible committee:
    # C(13, 7) = 1716.
    assert ans(COMMITTEE + "at most 4 girls?") == "1716"


def test_at_least_zero_full_range_boundary():
    assert ans(COMMITTEE + "at least 0 girls?") == "1716"


def test_exactly_impossible_is_zero():
    # Only 4 girls exist; exactly 5 girls can never happen.
    assert ans(COMMITTEE + "exactly 5 girls?") == "0"


def test_at_least_impossible_is_zero():
    assert ans(COMMITTEE + "at least 5 girls?") == "0"


def test_mixed_split_men_women():
    # C(6, 2) x C(5, 3) = 15 x 10 = 150.
    q = ("In how many ways can a team of 2 men and 3 women "
         "be selected from 6 men and 5 women?")
    assert ans(q) == "150"


def test_bare_total_two_group_pool():
    # No condition: C(9 + 4, 7) = C(13, 7) = 1716.
    q = ("In how many ways can a committee of 7 be formed "
         "from 9 boys and 4 girls?")
    assert ans(q) == "1716"


def test_plain_single_group_committee():
    # C(10, 5) = 252.
    q = "In how many ways can a committee of 5 be formed from 10 people?"
    assert ans(q) == "252"
    out = solve_question(q)
    assert out["op"] == "pnc_word" and out["answer"] == "252"


def test_plain_single_group_selected():
    # C(12, 4) = 495.
    q = "In how many ways can 4 students be selected from 12 students?"
    assert ans(q) == "495"


def test_plain_single_group_same_noun():
    # C(8, 3) = 56.
    q = "In how many ways can 3 girls be selected from 8 girls?"
    assert ans(q) == "56"


def test_word_numbers():
    q = "In how many ways can a committee of five be formed from ten people?"
    assert ans(q) == "252"


def test_hinglish_split():
    q = ("5 boys and 4 girls me se 3 boys and 3 girls kitne "
         "tarike se select kar sakte hain?")
    assert ans(q) == "40"


def test_hinglish_plain():
    # C(5, 3) = 10.
    q = "kitne tarike se 5 ladko me se 3 chune ja sakte hain?"
    assert ans(q) == "10"


def test_three_groups_decline():
    # Three counted groups: a pair schema would silently
    # drop the teachers and serve a wrong count.
    declines("In how many ways can a team of 3 boys, 3 girls "
             "and 2 teachers be selected from 5 boys, 4 girls "
             "and 6 teachers?")


# ------------------------------------------------------------------
# B. Letter arrangements
# ------------------------------------------------------------------

def test_monday_plain():
    # 6 distinct letters: 6! = 720.
    q = "In how many ways can the letters of the word MONDAY be arranged?"
    assert ans(q) == "720"
    out = solve_question(q)
    assert out["op"] == "pnc_word" and out["answer"] == "720"


def test_mississippi_repeats():
    # 11 letters, I x4, S x4, P x2: 11! / (4! 4! 2!)
    # = 39916800 / 1152 = 34650.
    q = ("In how many ways can the letters of the word "
         "MISSISSIPPI be arranged?")
    assert ans(q) == "34650"


def test_banana_repeats():
    # 6! / (3! 2!) = 720 / 12 = 60.
    q = "In how many ways can the letters of the word BANANA be arranged?"
    assert ans(q) == "60"


def test_daughter_plain():
    q = ("In how many ways can the letters of the word "
         "DAUGHTER be arranged?")
    assert ans(q) == "40320"


def test_daughter_vowels_together():
    # Block AUE: (5 consonants + 1 block)! x 3! = 720 x 6.
    q = ("In how many ways can the letters of the word "
         "DAUGHTER be arranged so that vowels are always "
         "together?")
    assert ans(q) == "4320"


def test_daughter_consonants_together():
    # Block DGHTR: (3 vowels + 1 block)! x 5! = 24 x 120.
    q = ("In how many ways can the letters of the word "
         "DAUGHTER be arranged so that consonants are "
         "always together?")
    assert ans(q) == "2880"


def test_banana_vowels_together_repeats():
    # Brute-force verified: 12.  Units {B, N, N, block}:
    # 4! / 2! = 12; block AAA internal: 3! / 3! = 1.
    q = ("In how many ways can the letters of the word "
         "BANANA be arranged so that vowels are always "
         "together?")
    assert ans(q) == "12"


def test_banana_consonants_together_repeats():
    # Brute-force verified: 12.  Units {A, A, A, block}:
    # 4! / 3! = 4; block BNN internal: 3! / 2! = 3; 4 x 3.
    q = ("In how many ways can the letters of the word "
         "BANANA be arranged so that consonants are always "
         "together?")
    assert ans(q) == "12"


def test_vowels_even_places_matching_counts():
    # ORANGE: 3 vowels, 3 even places.  Vowels in even
    # places: 3! = 6; consonants in odd places: 3! = 6;
    # brute-force verified total 36.
    q = ("In how many ways can the letters of the word "
         "ORANGE be arranged so that the vowels occupy "
         "even places?")
    assert ans(q) == "36"


def test_vowels_even_places_assassination():
    # 13 letters, vowels A3 I2 O (6) = 6 even places:
    # 6!/(3!2!) = 60; consonants S4 N2 T (7) in odd places:
    # 7!/(4!2!) = 105; 60 x 105 = 6300.
    q = ("In how many ways can the letters of the word "
         "ASSASSINATION be arranged so that the vowels "
         "occupy even places?")
    assert ans(q) == "6300"


def test_vowels_even_places_ambiguous_declines():
    # DAUGHTER: 3 vowels but 4 even places — "occupy even
    # places" has two readings with different answers.
    declines("In how many ways can the letters of the word "
             "DAUGHTER be arranged so that the vowels occupy "
             "even places?")


def test_vowels_never_together_declines():
    declines("In how many ways can the letters of the word "
             "DAUGHTER be arranged so that vowels are never "
             "together?")


# ------------------------------------------------------------------
# C. Digit numbers
# ------------------------------------------------------------------

def test_digits_plain_no_repetition():
    # P(5, 3) = 60.
    q = ("How many 3-digit numbers can be formed from the "
         "digits 1, 2, 3, 4, 5 without repetition?")
    assert ans(q) == "60"
    out = solve_question(q)
    assert out["op"] == "pnc_word" and out["answer"] == "60"


def test_digits_repetition_allowed():
    q = ("How many 3-digit numbers can be formed from the "
         "digits 1, 2, 3, 4, 5 with repetition allowed?")
    assert ans(q) == "125"


def test_digits_leading_zero_trap():
    # First digit 4 ways (not 0), then 4, then 3: 48.
    q = ("How many 3-digit numbers can be formed from the "
         "digits 0, 1, 2, 3, 4 without repetition?")
    assert ans(q) == "48"


def test_digits_even_no_zero_in_set():
    # Units {2, 4}: 2 ways; remaining P(4, 3) = 24; 48.
    q = ("How many 4-digit even numbers can be formed from "
         "the digits 1, 2, 3, 4, 5 without repetition?")
    assert ans(q) == "48"


def test_digits_even_with_zero_bruteforce():
    # Brute-force verified: 30 (units 0: 4x3 = 12; units
    # 2 or 4: 3 x 3 x 2 = 18).  The units/leading-zero
    # interaction is exactly what the subset DP counts.
    q = ("How many 3-digit even numbers can be formed from "
         "the digits 0, 1, 2, 3, 4 without repetition?")
    assert ans(q) == "30"


def test_digits_odd():
    # Units {1, 3, 5}: 3 x 4 x 3 = 36.
    q = ("How many 3-digit odd numbers can be formed from "
         "the digits 1, 2, 3, 4, 5 without repetition?")
    assert ans(q) == "36"


def test_digits_divisible_by_5():
    # Brute-force verified: 36 (units 0: 5x4 = 20; units
    # 5: 4x4 = 16).
    q = ("How many 3-digit numbers divisible by 5 can be "
         "formed from the digits 0, 1, 2, 3, 4, 5 without "
         "repetition?")
    assert ans(q) == "36"


def test_digits_divisible_by_10():
    # Units 0; hundreds 5 ways, tens 4 ways: 20.
    q = ("How many 3-digit numbers divisible by 10 can be "
         "formed from the digits 0, 1, 2, 3, 4, 5 without "
         "repetition?")
    assert ans(q) == "20"


def test_digits_starts_with_67():
    # Brute-force verified: remaining 3 places from 5
    # digits: P(5, 3) = 60.
    q = ("How many 5-digit numbers can be formed from the "
         "digits 1, 2, 3, 4, 5, 6, 7 without repetition if "
         "the numbers start with 67?")
    assert ans(q) == "60"


def test_digits_starts_with_repetition():
    # First digit fixed 3; other 3 places 5 ways each: 125.
    q = ("How many 4-digit numbers can be formed from the "
         "digits 1, 2, 3, 4, 5 with repetition allowed if "
         "the numbers start with 3?")
    assert ans(q) == "125"


def test_digits_range_dress():
    # Digits 0 to 9: 9 x 9 x 8 x 7 = 4536.
    q = ("How many 4-digit numbers can be formed using the "
         "digits 0 to 9 without repetition?")
    assert ans(q) == "4536"


def test_digits_even_repetition_with_zero():
    # Hundreds 4 ways (not 0), tens 5, units {0,2,4}: 60.
    q = ("How many 3-digit even numbers can be formed from "
         "the digits 0, 1, 2, 3, 4 with repetition allowed?")
    assert ans(q) == "60"


def test_digits_word_length():
    q = ("How many three-digit numbers can be formed from "
         "the digits 1, 2, 3, 4, 5 without repetition?")
    assert ans(q) == "60"


def test_digits_unstated_repetition_declines():
    declines("How many 3-digit numbers can be formed from "
             "the digits 1, 2, 3, 4, 5?")


def test_digits_divisible_by_3_declines():
    declines("How many 3-digit numbers divisible by 3 can "
             "be formed from the digits 1, 2, 3, 4, 5 "
             "without repetition?")


# ------------------------------------------------------------------
# D. Geometric counting + row arrangements
# ------------------------------------------------------------------

def test_chords_21_points():
    # NCERT Ex 6.4: C(21, 2) = 210.
    q = "How many chords can be drawn through 21 points on a circle?"
    assert ans(q) == "210"
    out = solve_question(q)
    assert out["op"] == "pnc_word" and out["answer"] == "210"


def test_handshakes():
    # C(10, 2) = 45.
    assert ans("How many handshakes among 10 people?") == "45"


def test_diagonals_10_sided():
    # C(10, 2) - 10 = 45 - 10 = 35.
    q = "How many diagonals does a polygon with 10 sides have?"
    assert ans(q) == "35"


def test_diagonals_named_polygon_via_router_unchanged():
    # Named polygons already solved before this wave; the
    # primary answer must stand (failure-only gate).
    out = solve_question("How many diagonals does a hexagon have?")
    assert out["answer"] == "9"


def test_triangles_plain():
    # C(10, 3) = 120.
    q = ("How many triangles can be formed from 10 points, "
         "no three of which are collinear?")
    assert ans(q) == "120"


def test_triangles_collinear_subtraction():
    # C(10, 3) - C(4, 3) = 120 - 4 = 116.
    q = ("How many triangles can be formed from 10 points, "
         "4 of which are collinear?")
    assert ans(q) == "116"


def test_lines_collinear():
    # C(10, 2) - C(4, 2) + 1 = 45 - 6 + 1 = 40.
    q = ("How many straight lines can be formed from 10 "
         "points, 4 of which are collinear?")
    assert ans(q) == "40"


def test_lines_plain():
    # C(12, 2) = 66.
    q = "How many straight lines can be drawn through 12 points?"
    assert ans(q) == "66"


def test_row_arrangement_people():
    q = "In how many ways can 5 people be arranged in a row?"
    assert ans(q) == "120"
    out = solve_question(q)
    assert out["op"] == "pnc_word" and out["answer"] == "120"


def test_row_arrangement_books():
    # 6! = 720.
    q = "How many ways can 6 books be arranged on a shelf in a row?"
    assert ans(q) == "720"


# ------------------------------------------------------------------
# Controls — existing serves unchanged
# ------------------------------------------------------------------

def test_control_explicit_ncr():
    out = solve_question("Find 5C3")
    assert (out["op"], out["answer"]) == ("combination", "10")


def test_control_explicit_npr():
    out = solve_question("Evaluate 5P3")
    assert (out["op"], out["answer"]) == ("permutation", "60")


def test_control_factorial():
    out = solve_question("What is factorial of 5?")
    assert (out["op"], out["answer"]) == ("factorial", "120")


def test_control_probability_coin():
    out = solve_question(
        "Probability of getting a head when a coin is tossed")
    assert out["op"] == "probability"
    assert out["answer"].startswith("1/2")


def test_control_probability_question_declines_in_schema():
    declines("What is the probability that a committee of "
             "3 boys and 3 girls is selected from 5 boys "
             "and 4 girls?")


def test_control_probability_bag_unchanged():
    out = solve_question(
        "A bag contains 3 red and 5 blue balls. What is the "
        "probability of drawing a red ball?")
    assert out["op"] == "probability"


def test_control_algebra_unchanged():
    out = solve_question("Solve 2x + 3 = 7")
    assert (out["op"], out["answer"]) == ("equation", "x = 2")
