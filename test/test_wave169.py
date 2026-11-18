"""Wave 169: Tier-A solver depth — general method schemas
for the book-question families that still did not solve
(measured 18 Nov 2026 on the Deploy-38 solver over the
NOT_SOLVED pool of ~/workspace/ganitra-book-questions.jsonl):

  line equations 2/30 -> 17/30, sector 7/30 -> 15/30,
  mensuration cost 8/30 -> 13/30, annular 1/8 -> 4/8,
  probability-distribution tables 6/29 -> 10/29,
  rational/irrational between 0/30 -> 9/30,
  commercial sentence forms 0/30 -> 9/30
  (same samples before/after; every new serve hand-checked).

solver/tierA169.py holds the schemas; a failure-only gate at
the end of router._solve_question_uncached (after the Wave
142 gate) calls it, so a question the solver already answers
is never displaced.  Every schema verifies its answer
exactly (Fractions / SymPy) before serving and returns None
on any doubt.
"""
import re
from fractions import Fraction

import pytest

from solver.router import solve_question
from solver.tierA169 import solve_tierA169


def ans(q):
    out = solve_tierA169(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_tierA169(q) is None, q


# ---------------------------------------------------------------------------
# Family 1: sectors
# ---------------------------------------------------------------------------

def test_sector_area_from_radius_and_arc():
    assert ans("Radius of a sector of a circle is 3.5 cm and length "
               "of its arc is 2.2 cm. Find the area of the sector.") \
        == "77/20"                     # (1/2) x 2.2 x 3.5 = 3.85


def test_sector_area_from_arc_and_radius_reversed_order():
    assert ans("Find the area of a sector whose length of the arc "
               "is 50 mm and radius is 14 mm") == "350"


def test_sector_area_from_perimeter_and_arc():
    assert ans("Find the area of a sector whose perimeter is 64 cm "
               "and length of the arc is 44 cm") == "220"


def test_sector_perimeter_from_radius_and_area():
    assert ans("A sector of radius 4.2 cm has an area 9.24 cm2. "
               "Find its perimeter") == "64/5"


def test_sector_from_circle_area_and_angle():
    a = ans("The area of a circle is 25 π sq.cm. Find the length of "
            "its arc subtending an angle of 144 o at the centre. "
            "Also find the area of the corresponding sector.")
    assert "arc length = 4pi" in a and "sector area = 10pi" in a


def test_sector_area_from_circle_area_and_sector_perimeter():
    assert ans("The perimeter of a sector of the circle of area "
               "25 π sq.cm is 20 cm. Find the area of the sector.") \
        == "25"


def test_sector_circle_area_non_square_declines():
    declines("The area of a circle is 30 π sq.cm. Find the length "
             "of its arc subtending an angle of 120 degrees at "
             "the centre.")


def test_sector_figure_question_declines():
    declines("Write the radius of the sector shaded in the "
             "adjacent figure.")


# ---------------------------------------------------------------------------
# Family 1b: annulus + cost-at-rate + Heron
# ---------------------------------------------------------------------------

def test_annular_from_diameter_and_width():
    assert ans("Diameter of the circular garden is 42 m. There is "
               "a 3.5 m wide road around the garden. Find the area "
               "of the road.") == "1001/2"      # 22/7 x 159.25


def test_annular_from_radius_and_width():
    assert ans("The radius of a circular flower garden is 21 m. "
               "A circular path of 14 m wide is laid around the "
               "garden. Find the area of the circular path") == "2464"


def test_annular_from_outer_inner_radii():
    a = ans("Find the area of a circular pathway whose outer "
            "radius is 32 cm and inner radius is 18 cm")
    assert a.startswith("700pi")                # true pi: 32 not 7-fit


def test_cone_whitewash_cost_per_100():
    assert ans("The slant height and base diameter of a conical "
               "tomb are 25 m and 14 m respectively. Find the cost "
               "of white-washing its curved surface at the rate of "
               "` 210 per 100 m2.") == "Rs 1155"


def test_hemisphere_tinplate_cost_per_100():
    a = ans("A hemispherical bowl made of brass has inner "
            "diameter 10.5 cm. Find the cost of tin-plating it on "
            "the inside at the rate of ` 16 per 100 cm2.")
    assert a.startswith("Rs 27.71")   # true pi per pi_policy


def test_heron_area_and_fencing_cost_with_gate():
    a = ans("A triangular park ABC has sides 120m, 80m and 50m. "
            "A gardener Dhania has to put a fence all around it "
            "and also plant grass inside. How much area does she "
            "need to plant? Find the cost of fencing it with "
            "barbed wire at the rate of `20 per metre leaving a "
            "space 3m wide for a gate on one side.")
    assert "375" in a and "4940" in a           # (250 - 3) x 20


def test_heron_impossible_triangle_declines():
    declines("A triangular plot has sides 10m, 20m and 35m. "
             "Find the area to plant grass inside.")


# ---------------------------------------------------------------------------
# Family 2: straight lines
# ---------------------------------------------------------------------------

def test_line_perpendicular_to_line_through_two_points():
    assert ans("Find the equation of the line passing through "
               "(–3, 5) and perpendicular to the line through the "
               "points (2, 5) and (–3, 6).") == "5x - y + 20 = 0"


def test_line_equal_intercepts_through_point():
    assert ans("Find the equation of a line that cuts off equal "
               "intercepts on the coordinate axes and passes "
               "through the point (2, 3).") == "x + y - 5 = 0"


def test_line_equal_intercepts_mcq():
    assert ans("The equation of the line through (1,2), which "
               "makes equal intercepts on the axes, is (A) x+y=1 "
               "(B) x+y=2 (C) x+y=4 (D) x+y=3") == "x + y - 3 = 0"


def test_line_intercepts_sum_two_lines():
    a = ans("Find equation of the line passing through the point "
            "(2, 2) and cutting off intercepts on the axes whose "
            "sum is 9.")
    assert "2x + y - 6 = 0" in a and "x + 2y - 6 = 0" in a


def test_line_perpendicular_from_origin():
    assert ans("The perpendicular from the origin to a line "
               "meets it at the point (–2, 9), find the equation "
               "of the line.") == "2x - 9y + 85 = 0"


def test_line_perpendicular_given_line_x_intercept():
    assert ans("Find equation of the line perpendicular to the "
               "line x – 7y + 5 = 0 and having x intercept 3.") \
        == "7x + y - 21 = 0"


def test_line_equal_intercepts_through_intersection():
    assert ans("Find the equation of the line passing through "
               "the point of intersection of the lines "
               "4x + 7y – 3 = 0 and 2x – 3y + 1 = 0 that has "
               "equal intercepts on the axes.") \
        == "13x + 13y - 6 = 0"


def test_line_parallel_y_axis_left():
    assert ans("Write the equation of the line parallel to the "
               "Y-axis at a distance of 7 units from it to its "
               "left.") == "x + 7 = 0"


def test_line_parallel_x_axis_below():
    assert ans("Write the equation of the line parallel to the "
               "X-axis at a distance of 5 units from it and "
               "below the X-axis.") == "y + 5 = 0"


def test_line_axis_parallel_multipart_declines():
    declines("Write the equation of the line : a) parallel to "
             "the X −axis and at a distance of 5 unit form it "
             "and above it. b) parallel to the Y− axis and at a "
             "distance of 5 unit form it and to the left of it.")


def test_line_inclination_x_intercept():
    assert ans("Find the equation of the line having "
               "inclination 135° and making X-intercept 7.") \
        == "x + y - 7 = 0"


def test_line_3d_point_and_parallel_vector():
    a = ans("Find the equation of the line which passes through "
            "the point (1, 2, 3) and is parallel to the vector "
            "3 iˆ + 2 ˆj − 2 kˆ .")
    assert "λ(3i + 2j - 2k)" in a and "(x - 1)/3" in a


def test_line_3d_position_vector_and_direction():
    a = ans("Find the equation of the line in vector and in "
            "cartesian form that passes through the point with "
            "position vector 2 iˆ − j + 4 kˆ and is in the "
            "direction iˆ + 2 ˆj − kˆ .")
    assert "r = 2i - j + 4k + λ(i + 2j - k)" in a


def test_line_3d_no_direction_declines():
    declines("Find the equation of the line which passes "
             "through the point (1, 2, 3).")


# ---------------------------------------------------------------------------
# Family 3: probability distribution tables
# ---------------------------------------------------------------------------

def test_prob_dist_ncert_k_table_all_parts():
    a = ans("A random variable X has the following probability "
            "distribution : X 0 1 2 3 4 5 6 7 P (X ) 0 k 2k 2k "
            "3k k 2 2k2 7k2 + k Determine : (i) k (ii) P (X < 3) "
            "(iii) P ( X > 4)")
    assert a == "k = 1/10; P(X < 3) = 3/10; P(X > 4) = 1/5"


def test_prob_dist_linear_k_table():
    a = ans("The probability distribution of a discrete r. v. X "
            "is as follows. x 1 2 3 4 5 6 P(X = x) k 2k 3k 4k "
            "5k 6k (i) Determine the value of k. (ii) Find "
            "P(X ≤ 4), P(2 < X < 4), P(X ≥ 3).")
    assert "k = 1/21" in a and "P(X <= 4) = 10/21" in a
    assert "P(2 < X < 4) = 1/7" in a and "P(X >= 3) = 6/7" in a


def test_prob_dist_numeric_table_word_asks():
    a = ans("The following probability distribution of r.v. X "
            "X = x –3 –2 –1 0 1 2 3 P (X = x) 0·05 0·1 0·15 "
            "0·20 0·25 0·15 0.1 Find the probability that "
            "(i) X is positive. (ii) X is non negative.")
    assert a == "P(X > 0) = 1/2; P(X >= 0) = 7/10"


def test_prob_dist_mcq_single_value():
    assert ans("If the a d.r .v. X has the following probability "
               "distribution : X −2 −1 0 1 2 3 P (X = x) 0·1 k "
               "0·2 2k 0·3 k then P (X = −1) = (A) 1 10 "
               "(B) 2 10 (C) 3 10 (D) 4 10") == "P(X = -1) = 1/10"


def test_prob_dist_constructive_declines():
    declines("Find the probability distribution of the number "
             "of successes in two tosses of a die, where a "
             "success is defined as number greater than 4 "
             "appears on at least one die.")


def test_prob_dist_mean_ask_declines():
    declines("A random variable X has the following probability "
             "distribution : X 0 1 2 P (X) 0.2 0.3 0.5 Find the "
             "mean of the distribution.")


def test_prob_dist_bad_table_declines():
    # sum = 1 forces k = -1/2, making probabilities negative
    declines("A random variable X has the following probability "
             "distribution : X 0 1 2 P (X) 0 k 1.5 Determine k.")


# ---------------------------------------------------------------------------
# Family 4: numbers between
# ---------------------------------------------------------------------------

def _between_vals(a_str):
    return [Fraction(t) for t in a_str.split(", ")]


def test_rationals_between_integers():
    vals = _between_vals(ans("Find six rational numbers between "
                             "3 and 4."))
    assert len(vals) == 6 and all(3 < v < 4 for v in vals)


def test_rationals_between_negative_range():
    vals = _between_vals(ans("Find 12 rational numbers between "
                             "-1 and 2."))
    assert len(vals) == 12 and all(-1 < v < 2 for v in vals)


def test_rationals_between_word_count():
    vals = _between_vals(ans("Write any five rational numbers "
                             "between −3 and 0."))
    assert len(vals) == 5 and all(-3 < v < 0 for v in vals)


def test_rationals_between_fractions():
    vals = _between_vals(ans("Find five rational numbers between "
                             "1/2 and 3/4."))
    assert len(vals) == 5
    assert all(Fraction(1, 2) < v < Fraction(3, 4) for v in vals)


def test_irrationals_between_decimals():
    a = ans("Find any 3 irrational numbers between 0.12 and 0.13")
    vals = [float(t) for t in a.split(", ")]
    assert len(vals) == 3 and all(0.12 < v < 0.13 for v in vals)


def test_irrationals_between_two_decimals():
    a = ans("Find two irrational numbers between 0.7 and 0.77")
    vals = [float(t) for t in a.split(", ")]
    assert len(vals) == 2 and all(0.7 < v < 0.77 for v in vals)


def test_between_glyph_lost_endpoints_decline():
    declines("Find five rational numbers between and . 5 5")


def test_between_multipart_declines():
    declines("Write any three rational numbers between the two "
             "numbers given below. (i) 0.3 and -0.5 (ii) - 2.3 "
             "and -2.33 (iii) 5.2 and 5.3")


def test_between_equal_endpoints_declines():
    declines("Find four rational numbers between 5 and 5.")


# ---------------------------------------------------------------------------
# Family 5: commercial sentence forms
# ---------------------------------------------------------------------------

def test_pl_per_unit_profit():
    assert ans("Dwarakanath purchases notebooks at a wholesale "
               "price of ₹23.6 per piece and sells each notebook "
               "at ₹30/-. How much profit does he make if he "
               "sells 50 books in a week?") == "Rs 320"


def test_pl_bulk_counted_profit():
    assert ans("Shyamala bought 3 kg bananas at ₹30/- per kg. "
               "She counted 35 bananas in all. She sells each "
               "banana for ₹5/-. How much profit does she make "
               "selling all the bananas?") == "Rs 85"


def test_pl_sp_plus_loss_amount_gives_cp():
    assert ans("Geeta sold a sari in %750, she suffered a loss "
               "of $125. Find the cost price of the sari.") \
        == "Rs 875"


def test_pl_overhead_profit():
    assert ans("David purchased a house in 48000. He spent 2000 "
               "in its painting and decoration. He sold that "
               "house for ¥55000. Tell how much profit has he "
               "get ?") == "Profit of Rs 5000"


def test_pl_target_percent_sp():
    assert ans("Gopal bought a radio in 300. In how much rupees "
               "should be sold to get 20% profit ?") == "Rs 360"


def test_pl_percent_and_amount_gives_sp():
    assert ans("Rita sold a cow on the profit of 25%. If Rita "
               "get total profit of $350 then find out the "
               "selling price of the cow ?") == "Rs 1750"


def test_pl_sp_plus_loss_percent_gives_cp():
    assert ans("A bicycle when sold in 1800, there is a loss "
               "of 10%. What will be the cost price of the "
               "bicycle ?") == "Rs 2000"


def test_pl_pair_profit_percent():
    assert ans("A shopkeeper purchased a book in €10 and sold "
               "it in £11. What will be the profit percentage ?") \
        == "10%"


def test_pl_margin_declines():
    declines("I am a carpenter and I make chairs. The cost of "
             "materials for a chair is ₹475 and I want to have "
             "a profit margin of 50%. At what price should I "
             "sell a chair?")


def test_simple_interest_rate_on_principal():
    assert ans("Find the simple interest at the rate of 12% "
               "annually on %500 for 3 years.") == "Rs 180"


def test_simple_interest_borrowed():
    assert ans("400 is borrowed at the rate of 6% annual "
               "interest for 3 years. Find out the interest.") \
        == "Rs 72"


def test_simple_interest_nth_year_declines():
    declines("A man deposited Rs 10000 in a bank at the rate of "
             "5% simple interest annually. Find the amount in "
             "15th year since he deposited the amount.")


# ---------------------------------------------------------------------------
# Router gate: integration + non-displacement
# ---------------------------------------------------------------------------

def test_gate_serves_through_router():
    out = solve_question("Find six rational numbers between "
                         "3 and 4.")
    assert out["op"] == "w169_rationals_between"


def test_gate_serves_sector_through_router():
    out = solve_question("Find the area of a sector whose "
                         "perimeter is 64 cm and length of the "
                         "arc is 44 cm")
    assert out["op"] == "w169_sector_perimeter_arc"
    assert out["answer"] == "220"


def test_gate_never_displaces_a_real_answer():
    out = solve_question("What is 15% of 240?")
    assert out["op"] != "w169_simple_interest"
    assert "36" in str(out["answer"])


def test_gate_keeps_existing_line_answer():
    out = solve_question("Find the slope of the line through "
                         "(2, 3) and (5, 9)")
    assert not str(out.get("op", "")).startswith("w169")
