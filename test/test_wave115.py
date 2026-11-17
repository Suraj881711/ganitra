"""Wave 115: Rekha Ganit — straight-line / coordinate-geometry
SOLVING depth.

Suraj's order: "rekha gadit ke question solve hone chahiye" —
line questions must SOLVE with steps, not return a concept
card or "Answer not found". The pre-wave audit (49 probes)
found the family in three states: already solving (slope
from two points, two-point / point-slope equations, section
formula on the "divides" phrasing, collinearity, areas,
midpoint — left byte-identical, guarded below), honestly
missing (slope from an equation, inclination, intercept
forms, parallel/perpendicular constructions and checks,
line distances, angle between lines, foot/image, section
point on other phrasings, intersection family, bisector /
locus, normal form, and the Hindi/Hinglish phrasings), and
HIJACKED (check / angle / intersection asks "solved" as a
2x2 system, the dividing-point ask echoing its ratio, the
bisector ask serving the segment's own line, a slope ask
echoing the line).

Wave 115 adds solver/rekha.py: strict method schemas behind
the router's failure-only gate (the Wave 77/94/103 pattern)
plus rekha_upgrade in fallback.py (the Wave 103
degree_upgrade pattern) for the hijack shapes. Every battery
answer below was hand-verified. Tests go through the real
chat path (api._solve_friendly) unless they are layer-level
guards on solve_rekha / rekha_upgrade themselves.
"""
import pytest

from api import _solve_friendly
from solver.rekha import rekha_upgrade, solve_rekha


def _ans(q):
    return str(_solve_friendly(q).get("answer", ""))


def _op(q):
    return str(_solve_friendly(q).get("op", ""))


# --- Slope from an equation / inclination ------------------

def test_slope_from_general_equation():
    assert _ans("Find the slope of the line 3x + 4y = 12.") \
        == "-3/4"


def test_slope_from_slope_intercept_form():
    assert _ans("Find the slope of the line y = 5x - 7.") == "5"


def test_slope_of_vertical_line_is_undefined():
    # Was hijacked: the equation itself was echoed back.
    assert "undefined" in _ans("Find the slope of the line x = 4.")


def test_inclination_from_slope():
    assert _ans("A line has slope 1. Find its angle of "
                "inclination.") == "45°"


def test_inclination_from_slope_hinglish():
    assert _ans("ek line ki slope √3 hai, uska inclination "
                "kitna hoga?") == "60°"


def test_slope_from_inclination():
    assert _ans("Find the slope of a line whose inclination "
                "is 135 degrees.") == "-1"


def test_slope_hindi_two_points():
    assert _ans("बिंदुओं (2, 3) और (5, 11) को मिलाने वाली "
                "रेखा की प्रवणता ज्ञात कीजिए।") == "8/3"


def test_slope_hinglish_equation():
    assert _ans("line 2x + 5y = 10 ki slope kya hai?") == "-2/5"


# --- Equation constructions --------------------------------

def test_eq_from_slope_and_y_intercept():
    assert _ans("Find the equation of a line with slope -2 "
                "and y-intercept 5.") == "y = -2x + 5"


def test_eq_from_two_intercepts():
    assert _ans("Find the equation of the line which makes "
                "intercepts 3 and -4 on the x-axis and "
                "y-axis respectively.") == "x/3 - y/4 = 1"


def test_intercept_form_of_given_line():
    assert _ans("Reduce the equation 2x + 3y = 6 into "
                "intercept form and find its intercepts.") \
        == "x/3 + y/2 = 1"


def test_convert_to_slope_intercept_form():
    assert _ans("Convert the equation 3x - 4y + 10 = 0 into "
                "slope-intercept form.") == "y = (3/4)x + 5/2"


def test_eq_parallel_through_point():
    assert _ans("Find the equation of the line parallel to "
                "2x - 3y + 5 = 0 and passing through the "
                "point (1, 4).") == "2x - 3y + 10 = 0"


def test_eq_perpendicular_through_point():
    assert _ans("Find the equation of the line perpendicular "
                "to x + 2y = 3 and passing through the "
                "point (2, 1).") == "2x - y - 3 = 0"


def test_eq_parallel_hindi():
    assert _ans("बिंदु (3, 2) से होकर जाने वाली और रेखा "
                "x - 2y = 3 के समांतर रेखा का समीकरण ज्ञात "
                "कीजिए।") == "x - 2y + 1 = 0"


def test_eq_two_points_hindi():
    assert _ans("बिंदुओं (1, 1) और (2, 3) से होकर जाने "
                "वाली रेखा का समीकरण ज्ञात कीजिए।") \
        == "y = 2x - 1"


# --- Parallel / perpendicular checks (hijack repairs) ------

def test_parallel_check_yes():
    assert _ans("Check whether the lines 2x + 3y = 5 and "
                "4x + 6y = 7 are parallel or not.") \
        == "Yes, the lines are parallel"


def test_perpendicular_check_yes_system_hijack():
    # The primary "solves" the pair as a system and serves
    # the intersection point; the upgrade must replace it.
    assert _ans("Are the lines 3x - y = 2 and x + 3y = 5 "
                "perpendicular to each other?") \
        == "Yes, the lines are perpendicular"


def test_parallel_check_no():
    assert _ans("Are the lines 2x + y = 3 and 3x - y = 1 "
                "parallel?") == "No, the lines are not parallel"


# --- Distances ----------------------------------------------

def test_point_line_distance():
    assert _ans("Find the distance of the point (3, 4) "
                "from the line 3x - 4y + 5 = 0.") == "2/5"


def test_point_line_distance_surd():
    assert _ans("Find the distance of the point (1, 2) "
                "from the line x + y + 1 = 0.") == "2√2"


def test_point_line_distance_hindi():
    assert _ans("बिंदु (2, -1) की रेखा 4x - 3y + 2 = 0 से "
                "दूरी ज्ञात कीजिए।") == "13/5"


def test_point_line_distance_hinglish():
    assert _ans("point (5, 5) ki line x + y = 2 se doori "
                "kitni hai?") == "4√2"


def test_origin_line_distance():
    assert _ans("Find the distance of the origin from "
                "the line 3x + 4y = 10.") == "2"


def test_parallel_lines_distance():
    assert _ans("Find the distance between the parallel "
                "lines 3x + 4y - 10 = 0 and "
                "3x + 4y - 30 = 0.") == "4"


def test_parallel_lines_distance_scaled():
    # the second line must be scaled to the first's (A, B)
    assert _ans("Find the distance between the lines "
                "6x + 8y = 9 and 3x + 4y = 1.") == "7/10"


def test_parallel_lines_distance_hindi():
    assert _ans("समांतर रेखाओं 5x + 12y = 7 और "
                "5x + 12y = 20 के बीच की दूरी ज्ञात "
                "कीजिए।") == "1"


# --- Angle between two lines --------------------------------

def test_angle_between_slopes():
    assert "8.13°" in _ans("Find the angle between the "
                           "lines having slopes 2 and 3.")


def test_angle_between_slopes_standard():
    assert _ans("Find the angle between the lines with "
                "slopes 1 and √3.") == "15°"


def test_angle_between_equations_system_hijack():
    assert _ans("Find the angle between the lines "
                "x + y = 3 and x - y = 1.") == "90°"


def test_angle_between_hindi_hijack():
    # The primary served op=hindi_equation "y = 2".
    assert "8.13°" in _ans("रेखाओं y = 2x + 1 और "
                           "y = 3x + 2 के बीच का कोण ज्ञात "
                           "कीजिए।")


# --- Foot / image --------------------------------------------

def test_foot_of_perpendicular():
    assert _ans("Find the foot of the perpendicular from "
                "the point (1, 4) to the line x + y = 3.") \
        == "(0, 3)"


def test_foot_of_perpendicular_hindi():
    assert _ans("बिंदु (1, 3) से रेखा 2x + y = 4 पर डाले "
                "गए लंब के पाद के निर्देशांक ज्ञात "
                "कीजिए।") == "(3/5, 14/5)"


def test_image_of_point():
    assert _ans("Find the image of the point (1, 2) in "
                "the line x + y = 0.") == "(-2, -1)"


def test_image_of_point_hindi():
    assert _ans("बिंदु (3, 1) का रेखा x - y = 0 में "
                "प्रतिबिंब ज्ञात कीजिए।") == "(1, 3)"


# --- Section point / intersection family / locus -------------

def test_division_point_ratio_echo_hijack():
    # The primary echoed the ratio "2 : 1" as the answer.
    assert _ans("Find the coordinates of the point "
                "dividing the line joining (1, 1) and "
                "(4, 7) in the ratio 2 : 1 internally.") \
        == "(3, 5)"


def test_section_point_hindi_internal():
    assert _ans("बिंदुओं (2, 4) और (6, 8) को मिलाने वाले "
                "रेखाखंड को 1 : 3 के अनुपात में आंतरिक रूप "
                "से विभाजित करने वाले बिंदु के निर्देशांक "
                "ज्ञात कीजिए।") == "(3, 5)"


def test_section_point_hindi_external():
    assert _ans("बिंदुओं (3, 2) और (9, 8) को मिलाने वाले "
                "रेखाखंड को 2 : 1 के अनुपात में बाह्य रूप "
                "से विभाजित करने वाले बिंदु के निर्देशांक "
                "ज्ञात कीजिए।") == "(15, 14)"


def test_line_through_intersection_and_point():
    # The primary served the intersection point (2, 1).
    assert _ans("Find the equation of the line passing "
                "through the point of intersection of the "
                "lines 2x + 3y = 7 and x - y = 1 and "
                "through the point (1, 1).") == "y - 1 = 0"


def test_line_through_intersection_parallel():
    assert _ans("Find the equation of the line through "
                "the intersection of the lines x + y = 2 "
                "and 2x - y = 4 and parallel to the line "
                "3x + y = 5.") == "3x + y - 6 = 0"


def test_locus_equidistant():
    assert _ans("Find the locus of a point which is "
                "always equidistant from the points "
                "(1, 2) and (3, 4).") == "x + y - 5 = 0"


def test_perpendicular_bisector_segment_line_hijack():
    # The primary served the segment's own line y = x + 1.
    assert _ans("Find the equation of the perpendicular "
                "bisector of the line segment joining "
                "(2, 3) and (6, 7).") == "x + y - 9 = 0"


def test_normal_form():
    assert _ans("Reduce the equation x + y + 2 = 0 to "
                "the normal form and find the distance "
                "of the line from the origin.") \
        == "x cos 225° + y sin 225° = √2"


# --- Guards: pre-existing behaviour is byte-identical --------

def test_guard_prime_concept_card():
    assert _solve_friendly("What is a prime number?") \
        .get("fallback_kind") == "concept"


def test_guard_algebra_unchanged():
    assert _ans("Solve 2x + 3 = 11.") == "x = 4"


def test_guard_circle_area_unchanged():
    assert _ans("Find the area of a circle with "
                "radius 7.") == "154"


def test_guard_percentage_unchanged():
    assert _ans("What is 15% of 240?") == "36"


def test_guard_nonmaths_unchanged():
    assert _solve_friendly("What is the capital of "
                           "France?").get("fallback_kind") \
        == "nonmaths"


def test_guard_slope_two_points_unchanged():
    # geometry.py's own slope (decimal display) — the
    # failure gate must never displace it.
    r = _solve_friendly("Find the slope of the line "
                        "joining the points (2, 3) and "
                        "(5, 11).")
    assert r.get("op") == "slope"
    assert r.get("answer") == "2.66667"


def test_guard_two_point_equation_unchanged():
    assert _ans("Find the equation of the line passing "
                "through (1, 2) and (3, 8).") == "y = 3x - 1"


def test_guard_collinearity_unchanged():
    assert _ans("Show that the points (1, 2), (3, 6) and "
                "(5, 10) are collinear.") \
        == "Yes, the points are collinear"


def test_guard_external_division_unchanged():
    assert _ans("Find the coordinates of the point which "
                "divides the line joining (2, 3) and "
                "(8, 9) externally in the ratio 2 : 1.") \
        == "(14, 15)"


def test_guard_midpoint_unchanged():
    assert _ans("Find the midpoint of the line segment "
                "joining (-2, 5) and (4, -1).") == "(1, 2)"


# --- Layer-level guards ---------------------------------------

def test_layer_ignores_non_line_questions():
    assert solve_rekha("What is the capital of France?") \
        is None
    assert solve_rekha("Solve 2x + 3 = 11.") is None
    assert solve_rekha("Find the area of a circle with "
                       "radius 7.") is None
    assert solve_rekha("What is a prime number?") is None


def test_layer_falls_through_when_it_cannot_settle():
    # non-parallel lines have no parallel distance
    assert solve_rekha("Find the distance between the "
                       "lines 2x + y = 3 and 3x - y = 1.") \
        is None
    # a ratio ask (the ratio is the unknown) is not a
    # dividing-point ask
    assert solve_rekha("In what ratio does the point "
                       "(2, 3) divide the line joining "
                       "(1, 1) and (4, 7)?") is None


def test_upgrade_ignores_ordinary_results():
    # a genuine system solve is not a hijack
    res = {"op": "system", "answer": "x = 2, y = 1",
           "steps": []}
    assert rekha_upgrade("Solve the equations x + y = 3 "
                         "and x - y = 1.", res) is None
    # a genuine bisector answer is not displaced
    res2 = {"op": "line equation", "answer": "y = -x + 9",
            "steps": []}
    assert rekha_upgrade(
        "Find the equation of the perpendicular bisector "
        "of the line segment joining (2, 3) and (6, 7).",
        res2) is None
