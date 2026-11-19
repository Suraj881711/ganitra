"""Wave 195: Class 10 special-form pack — form-audit top-10
item #10 (audit rows 33-35; spot-check probes 27, 28, 29).

Before this wave (measured on the pristine tree):
  * Probe 27 (parallelogram vertices, find x and y) was a
    parse error; probe 29 (NCERT penalty AP) was a parse
    error; probe 28 (sec theta = 13/5, all other ratios)
    FRAGMENT-served the bare echo "13/5" — as did the cos
    and cot givens; "If sin A = 3/4, calculate cos A and
    tan A" served the wrapper equation "A = 3/4"; "If
    tan A = 4/3, find the other trigonometric ratios"
    served only sin and cos; "Given 15 cot A = 8, find
    sin A and sec A" served sqrt(65) values (the
    coefficient dropped) instead of the 8-15-17 values
    sin A = 15/17, sec A = 17/8; the AP = 3/7 AB dress
    echoed "3/7"; the AP table dress served "a = 5".

Fix: solver/c10pack195.py — strict family schemas
(coordinate specials, given-one-ratio-find-others, AP
word dresses), every value recomputed exactly and
verified before serving, wired in router.py as a
failure-only gate after Wave 175, a fragment check at
the Wave 77 core seam, and a fragment block for real
primary answers — displacement only under
w195_displaces (verified difference at the seam).

Every expected answer below was hand-verified before
pinning (diagonal midpoints for x = 6, y = 3; the
5-12-13 ratios; S_30 = 15 x 1850 = Rs 27,750; the
8-15-17 triple for 15 cot A = 8; houses x = 35 since
34 x 35/2 = 595 = 1225 - 630; logs 16 rows / top 5).
"""
import sympy as sp

from solver.c10pack195 import solve_c10pack195, w195_displaces
from solver.router import solve_question

P27 = ("If (1, 2), (4, y), (x, 6) and (3, 5) are the "
       "vertices of a parallelogram taken in order, find "
       "x and y")
P28 = ("Given sec theta = 13/5, calculate all other "
       "trigonometric ratios")
P29 = ("A contract on construction job specifies a penalty "
       "for delay of completion beyond a certain date as "
       "follows: Rs 200 for the first day, Rs 250 for the "
       "second day, Rs 300 for the third day, etc., the "
       "penalty for each succeeding day being Rs 50 more "
       "than for the preceding day. Find the total penalty "
       "if the work is delayed by 30 days")


def ans(q):
    out = solve_c10pack195(q)
    assert out is not None, q
    return out["answer"]


def declines(q):
    assert solve_c10pack195(q) is None, q


def routed(q):
    out = solve_question(q)
    assert isinstance(out, dict), q
    return out


# ------------------------------------------------------------------
# The three audit probes, verbatim — schema and router
# ------------------------------------------------------------------

def test_probe27_parallelogram_schema():
    out = solve_c10pack195(P27)
    assert out["op"] == "w195_parallelogram_unknowns"
    assert "x = 6" in out["answer"]
    assert "y = 3" in out["answer"]


def test_probe27_parallelogram_router():
    out = routed(P27)
    assert out["op"] == "w195_parallelogram_unknowns"
    assert "x = 6" in out["answer"] and "y = 3" in out["answer"]


def test_probe28_sec_all_others_schema():
    out = solve_c10pack195(P28)
    assert out["op"] == "w195_trig_ratios"
    assert out["answer"] == (
        "sin θ = 12/13, cos θ = 5/13, tan θ = 12/5, "
        "cosec θ = 13/12, cot θ = 5/12")


def test_probe28_sec_all_others_router_no_echo():
    out = routed(P28)
    assert out["op"] == "w195_trig_ratios"
    assert out["answer"] != "13/5"
    for frag in ("sin θ = 12/13", "cos θ = 5/13",
                 "tan θ = 12/5", "cosec θ = 13/12",
                 "cot θ = 5/12"):
        assert frag in out["answer"]


def test_probe29_penalty_schema():
    out = solve_c10pack195(P29)
    assert out["op"] == "w195_ap_penalty"
    assert out["answer"] == "Rs 27750"


def test_probe29_penalty_router():
    out = routed(P29)
    assert out["op"] == "w195_ap_penalty"
    assert out["answer"] == "Rs 27750"


# ------------------------------------------------------------------
# (a) coordinate specials — variants per branch
# ------------------------------------------------------------------

def test_parallelogram_one_unknown():
    # Diagonals (0,0)-(6,4) and (3,y)-(3,1): midpoints
    # (3,2) and (3,(y+1)/2) -> y = 3.
    q = ("If (0, 0), (3, y), (6, 4) and (3, 1) are the "
         "vertices of a parallelogram taken in order, "
         "find y")
    assert ans(q) == "y = 3"


def test_parallelogram_fourth_vertex():
    # D = A + C - B = (-2+4-1, -1+3-0) = (1, 2).
    q = ("If A(-2, -1), B(1, 0) and C(4, 3) are three "
         "vertices of a parallelogram ABCD, find the "
         "fourth vertex D")
    assert ans(q) == "(1, 2)"


def test_equidistant_y_axis():
    q = ("Find the point on the y-axis which is equidistant "
         "from the points (6, 5) and (-4, 3)")
    assert ans(q) == "(0, 9)"
    assert routed(q)["answer"] == "(0, 9)"


def test_equidistant_x_axis_schema():
    q = ("Find the point on the x-axis which is equidistant "
         "from the points (2, -5) and (-2, 9)")
    assert ans(q) == "(-7, 0)"


def test_distance_equals_two_roots():
    q = ("Find the value of y for which the distance "
         "between the points P(2, -3) and Q(10, y) is "
         "10 units")
    a = ans(q)
    assert "y = 3" in a and "y = -9" in a
    assert routed(q)["op"] == "w195_distance_equals"


def test_distance_equals_variant():
    # dx = 3, dy = x - 2, distance 5 -> (x-2)^2 = 16.
    q = ("Find the value of x for which the distance "
         "between the points (1, 2) and (4, x) is 5 units")
    a = ans(q)
    assert "x = 6" in a and "x = -2" in a


def test_trisection():
    q = ("Find the points of trisection of the line segment "
         "joining the points (4, -1) and (-2, -3)")
    assert ans(q) == "(2, -5/3), (0, -7/3)"


def test_four_equal_parts():
    q = ("Find the points which divide the line segment "
         "joining A(-2, 2) and B(2, 8) into four equal parts")
    assert ans(q) == "(-1, 7/2), (0, 5), (1, 13/2)"


def test_three_equal_parts_variant():
    q = ("Find the points which divide the line segment "
         "joining (1, 2) and (4, 5) into three equal parts")
    assert ans(q) == "(2, 3), (3, 4)"


def test_quadrilateral_square_show():
    q = ("Show that the points (1, 7), (4, 2), (-1, -1) "
         "and (-4, 4) are the vertices of a square")
    assert "square" in ans(q)


def test_quadrilateral_square_name_type():
    q = ("Name the type of quadrilateral formed by the "
         "points (-1, -2), (1, 0), (-1, 2) and (-3, 0)")
    assert ans(q) == "A square"


def test_quadrilateral_rectangle():
    q = ("Name the type of quadrilateral formed by the "
         "points (0, 0), (4, 0), (4, 3) and (0, 3)")
    assert ans(q) == "A rectangle"


def test_quadrilateral_rhombus():
    q = ("Name the type of quadrilateral formed by the "
         "points (0, 0), (2, 1), (4, 0) and (2, -1)")
    assert ans(q) == "A rhombus"


def test_quadrilateral_kite():
    q = ("Name the type of quadrilateral formed by the "
         "points (0, 3), (2, 0), (0, -4) and (-2, 0)")
    assert ans(q) == "A kite"


def test_quadrilateral_parallelogram():
    q = ("Name the type of quadrilateral formed by the "
         "points (0, 0), (3, 0), (4, 2) and (1, 2)")
    assert ans(q) == "A parallelogram"


def test_quadrilateral_general_declines():
    declines("Name the type of quadrilateral formed by "
             "the points (0, 0), (5, 0), (4, 3) and (1, 2)")


def test_ap_fraction_point():
    q = ("Find the point P which divides the line segment "
         "joining A(-2, 2) and B(2, -8) such that "
         "AP = 3/7 AB")
    assert ans(q) == "(-2/7, -16/7)"
    out = routed(q)
    assert out["op"] == "w195_ap_fraction_point"
    assert out["answer"] == "(-2/7, -16/7)"


def test_ap_fraction_point_variant():
    q = ("Find the point P which divides the line segment "
         "joining A(0, 0) and B(5, 10) such that "
         "AP = 2/5 AB")
    assert ans(q) == "(2, 4)"


# ------------------------------------------------------------------
# (b) given one trig ratio, find the others
# ------------------------------------------------------------------

def test_trig_tan_given_all_others():
    q = "If tan A = 4/3, find the other trigonometric ratios of angle A"
    assert ans(q) == ("sin A = 4/5, cos A = 3/5, "
                      "sec A = 5/3, cosec A = 5/4, cot A = 3/4")
    out = routed(q)
    assert out["op"] == "w195_trig_ratios"
    assert "cosec A = 5/4" in out["answer"]


def test_trig_cos_given_all_others_router():
    q = ("Given cos theta = 5/13, calculate all other "
         "trigonometric ratios")
    out = routed(q)
    assert out["op"] == "w195_trig_ratios"
    assert "sin θ = 12/13" in out["answer"]
    assert "sec θ = 13/5" in out["answer"]


def test_trig_sin_given_partial():
    q = "If sin A = 3/4, calculate cos A and tan A"
    out = solve_c10pack195(q)
    assert out["op"] == "w195_trig_ratios"
    vals = {}
    for part in out["answer"].split(", "):
        name, v = part.split(" = ")
        vals[name] = sp.nsimplify(v.replace("·", "*"))
    assert sp.simplify(vals["cos A"] - sp.sqrt(7) / 4) == 0
    assert sp.simplify(vals["tan A"] - 3 / sp.sqrt(7)) == 0
    r = routed(q)
    assert r["op"] == "w195_trig_ratios"


def test_trig_cot_given_all_others_router():
    q = "If cot theta = 7/8, evaluate all other trigonometric ratios"
    out = routed(q)
    assert out["op"] == "w195_trig_ratios"
    assert "tan θ = 8/7" in out["answer"]
    assert "sec θ = sqrt(113)/7" in out["answer"]


def test_trig_cosec_given_all_others():
    q = ("Given cosec theta = 13/12, calculate all other "
         "trigonometric ratios")
    assert ans(q) == ("sin θ = 12/13, cos θ = 5/13, "
                      "tan θ = 12/5, sec θ = 13/5, "
                      "cot θ = 5/12")


def test_trig_coefficient_dress():
    # 15 cot A = 8 -> cot A = 8/15, the 8-15-17 triple.
    q = "Given 15 cot A = 8, find sin A and sec A"
    assert ans(q) == "sin A = 15/17, sec A = 17/8"
    out = routed(q)
    assert out["op"] == "w195_trig_ratios"
    assert out["answer"] == "sin A = 15/17, sec A = 17/8"


def test_trig_colon_dress():
    q = "If tan A = 4:3, find the other trigonometric ratios of angle A"
    assert "sin A = 4/5" in ans(q)


def test_trig_triangle_two_sides():
    q = ("In triangle ABC, right-angled at B, AB = 24 cm, "
         "BC = 7 cm. Determine sin A, cos A")
    assert ans(q) == "sin A = 7/25, cos A = 24/25"
    assert routed(q)["op"] == "w195_trig_triangle"


def test_trig_triangle_hypotenuse_given():
    q = ("In triangle ABC, right-angled at B, AB = 5 cm, "
         "AC = 13 cm. Determine sin A, cos A, sin C, cos C")
    a = ans(q)
    assert "sin A = 12/13" in a and "cos A = 5/13" in a
    assert "sin C = 5/13" in a and "cos C = 12/13" in a


def test_trig_in_terms_of_cot():
    q = "Express all trigonometric ratios in terms of cot A"
    a = ans(q)
    assert "tan A = 1/cot A" in a
    assert "cosec A = sqrt(cot A^2 + 1)" in a


def test_trig_in_terms_of_sec():
    q = "Express all trigonometric ratios in terms of sec A"
    a = ans(q)
    assert "cos A = 1/sec A" in a
    assert "tan A = sqrt(sec A^2 - 1)" in a


def test_trig_no_ask_declines():
    declines("sin A = 3/4")
    declines("If sin A = 3/4, find the angle A")


def test_trig_expression_ask_declines():
    declines("If tan A = 4/3, find the value of "
             "(sin A + cos A)/(sin A - cos A)")


# ------------------------------------------------------------------
# (c) AP word dresses
# ------------------------------------------------------------------

def test_ap_penalty_variant():
    # a = 100, d = 25, n = 20 -> S = 10 x 675 = 6750.
    q = ("A penalty for delay is specified as follows: "
         "Rs 100 for the first day, Rs 125 for the second "
         "day, Rs 150 for the third day, etc., the penalty "
         "for each succeeding day being Rs 25 more than "
         "for the preceding day. Find the total penalty if "
         "the work is delayed by 20 days")
    assert ans(q) == "Rs 6750"


def test_ap_savings_ramkali():
    q = ("Ramkali saved Rs 5 in the first week of a year "
         "and then increased her weekly savings by "
         "Rs 1.75. If in the nth week, her weekly savings "
         "become Rs 20.75, find n")
    assert ans(q) == "n = 10"
    assert routed(q)["op"] == "w195_ap_savings_target"


def test_ap_savings_salary_variant():
    # (14500 - 10000)/500 + 1 = 10.
    q = ("A man's salary is Rs 10000 in the first year "
         "and he gets an increment of Rs 500 every year. "
         "In which year will his salary reach Rs 14500?")
    assert ans(q) == "n = 10"


def test_ap_prizes():
    q = ("A sum of Rs 700 is to be used to give seven cash "
         "prizes to students of a school for their overall "
         "academic performance. If each prize is Rs 20 "
         "less than its preceding prize, find the value "
         "of the prizes")
    assert ans(q) == ("Rs 160, Rs 140, Rs 120, Rs 100, "
                      "Rs 80, Rs 60, Rs 40")


def test_ap_prizes_variant():
    # a = 1000/5 - 2 x (-20) = 240; sum 240+...+160 = 1000.
    q = ("A sum of Rs 1000 is to be used to give five cash "
         "prizes to students. If each prize is Rs 20 less "
         "than its preceding prize, find the value of "
         "the prizes")
    assert ans(q) == "Rs 240, Rs 220, Rs 200, Rs 180, Rs 160"


def test_ap_houses():
    q = ("The houses of a row are numbered consecutively "
         "from 1 to 49. Show that there is a value of x "
         "such that the sum of the numbers of the houses "
         "preceding the house numbered x is equal to the "
         "sum of the numbers of the houses following it. "
         "Find this value of x")
    assert ans(q) == "x = 35"


def test_ap_houses_variant():
    # 8 x 9/2 = 36 = 6^2; before 6: 15, after: 36 - 21 = 15.
    q = ("The houses of a row are numbered consecutively "
         "from 1 to 8. Find a value of x such that the sum "
         "of the numbers of the houses preceding the house "
         "numbered x is equal to the sum of the numbers "
         "of the houses following it")
    assert ans(q) == "x = 6"


def test_ap_logs():
    q = ("200 logs are stacked in the following manner: "
         "20 logs in the bottom row, 19 in the next row, "
         "18 in the row next to it and so on. In how many "
         "rows are the 200 logs placed and how many logs "
         "are in the top row?")
    assert ans(q) == "16 rows, 5 logs in the top row"


def test_ap_logs_variant():
    # 10 + 9 + ... + 1 = 55 -> 10 rows, top row 1.
    q = ("55 logs are stacked in the following manner: "
         "10 logs in the bottom row, 9 in the next row "
         "and so on. In how many rows are the 55 logs "
         "placed and how many logs are in the top row?")
    assert ans(q) == "10 rows, 1 logs in the top row"


def test_ap_reverse_sn_full():
    q = ("If the sum of first n terms of an AP is "
         "4n - n^2, what is the first term? What is the "
         "sum of first two terms? What is the 2nd term? "
         "Similarly find the 3rd, the 10th and the nth "
         "terms")
    a = ans(q)
    for frag in ("first term = 3", "sum of first two "
                 "terms = 4", "2nd term = 1", "3rd term = -1",
                 "10th term = -15", "nth term = 5 - 2·n"):
        assert frag in a, frag
    assert routed(q)["op"] == "w195_ap_reverse_sn"


def test_ap_reverse_sn_variant():
    # S_n = 2n^2 + 3n: a1 = 5, a2 = 9, d = 4, a5 = 21.
    q = ("If the sum of first n terms of an AP is "
         "2n^2 + 3n, find the first term, the common "
         "difference and the 5th term")
    a = ans(q)
    assert "first term = 5" in a
    assert "common difference = 4" in a
    assert "5th term = 21" in a


def test_ap_missing_terms_one():
    q = "Find the missing terms in the AP: 2, __, 26"
    assert ans(q) == "14"
    assert routed(q)["op"] == "w195_ap_missing_terms"


def test_ap_missing_terms_boxes():
    q = ("In the following APs, find the missing terms "
         "in the boxes: -4, □, □, □, □, 6")
    assert ans(q) == "-2, 0, 2, 4"


def test_ap_missing_terms_two():
    q = "Find the missing terms in the AP: 2, __, __, 26"
    assert ans(q) == "10, 18"


def test_ap_table_an():
    q = "In an AP, a = 5, d = 3, n = 8, find a_n"
    assert ans(q) == "a8 = 26"
    out = routed(q)
    assert out["op"] == "w195_ap_table"
    assert out["answer"] == "a8 = 26"


def test_ap_table_from_term():
    # d = (35 - 7)/12 = 7/3; S13 = 13/2 x 42 = 273.
    q = "In an AP, a = 7, a13 = 35, find d and S13"
    assert ans(q) == "d = 7/3, S13 = 273"


def test_ap_table_two_terms():
    # d = (27 - 15)/4 = 3; a = 15 - 2 x 3 = 9.
    q = "In an AP, a3 = 15, a7 = 27, find a and d"
    a = ans(q)
    assert "a = 9" in a and "d = 3" in a


def test_ap_table_sum_and_term():
    # a10 = 2 + 9 x 5 = 47; S10 = 5 x (2 + 47) = 245.
    q = "In an AP, a = 2, d = 5, n = 10, find a_n and S_n"
    a = ans(q)
    assert "a10 = 47" in a and "S10 = 245" in a


def test_ap_series_find_d():
    q = "For the AP: 3, 8, 13, 18, ... find the value of d"
    assert ans(q) == "d = 5"
    assert routed(q)["op"] == "w195_ap_series_d"


def test_ap_unmatched_narrative_declines():
    declines("Ravi earns Rs 5000 per month and spends "
             "Rs 3000 on rent")
    declines("A train travels 60 km in the first hour "
             "and 80 km in the second hour, find its speed")


# ------------------------------------------------------------------
# Controls — prior outcomes unchanged
# ------------------------------------------------------------------

def test_control_distance():
    out = routed("Find the distance between the points "
                 "(2, 3) and (4, 1)")
    assert out["op"] == "distance"


def test_control_midpoint():
    out = routed("Find the midpoint of the line segment "
                 "joining (2, 3) and (4, 1)")
    assert out["answer"] == "(3, 2)"


def test_control_section_ratio():
    out = routed("Find the coordinates of the point which "
                 "divides the line segment joining (4, -3) "
                 "and (8, 5) in the ratio 3:1 internally")
    assert out["answer"] == "(7, 3)"


def test_control_x_axis_equidistant_existing():
    out = routed("Find the point on the x-axis which is "
                 "equidistant from the points (2, -5) "
                 "and (-2, 9)")
    assert out["op"] == "equidistant point"


def test_control_ap_nth_term():
    out = routed("Find the 10th term of the AP 2, 7, 12, ...")
    assert out["op"] == "ap_nth_term"
    assert out["answer"] == "47"


def test_control_sin60():
    out = routed("Evaluate sin 60 degrees")
    assert out["answer"] == "sqrt(3)/2"
    out = routed("Find sin 60°")
    assert out["answer"] == "sqrt(3)/2"


def test_control_ladder_heights():
    out = routed("A ladder 15 m long just reaches the top "
                 "of a vertical wall. If the ladder makes "
                 "an angle of 60 degrees with the wall, "
                 "find the height of the wall")
    assert out["op"] == "heights_distances"


def test_control_expression_ask_not_displaced():
    # The expression ask is NOT the given-one-ratio dress:
    # Wave 195 declines it and the pre-existing primary
    # outcome stands byte-identical (verified against
    # pristine main in the wave notes).
    out = routed("If tan A = 4/3, find the value of "
                 "(sin A + cos A)/(sin A - cos A)")
    assert not str(out["op"]).startswith("w195")
    assert out["op"] == "ratio_from_ratio"
    assert out["answer"] == "sin A = 4/5, cos A = 3/5"


def test_control_concept_asks_decline():
    declines("What is a parallelogram")
    declines("Define an arithmetic progression")
    declines("What is the distance formula")


def test_displaces_predicate_guards():
    cand = {"op": "w195_trig_ratios",
            "answer": "sin A = 4/5, cos A = 3/5"}
    # Identical answers never displace.
    assert not w195_displaces(
        "q", {"op": "evaluate", "answer": "sin A = 4/5, cos A = 3/5"},
        cand)
    # A non-fragment op never displaces.
    assert not w195_displaces(
        "q", {"op": "value", "answer": "sqrt(3)/2"}, cand)
    # The echo does.
    assert w195_displaces(
        "q", {"op": "evaluate", "answer": "4/3"}, cand)
