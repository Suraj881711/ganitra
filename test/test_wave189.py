"""Wave 189: Three Dimensional Geometry — shortest distance
between lines, angle between lines, line equations, plane
basics (form audit item B.4 / rows 4-5, probes 17-18).

Probe 17 verbatim —
    Find the shortest distance between the lines
    r = (i + 2j + k) + lambda(i - j + k) and
    r = (2i - j - k) + mu(2i + j + 2k)
— fell to the generic geometry guide before this wave.
Independently verified: b1 x b2 = (-3, 0, 3),
(a2 - a1) . (b1 x b2) = -9, so SD = 9 / (3 sqrt(2))
= 3 sqrt(2)/2 units.

Probe 18 (control) —
    Find the direction cosines of the line passing through
    the points (-2, 4, -5) and (1, 2, 3)
— already solved ((0.3419, -0.2279, 0.9117)) and must stay
solved with the same outcome.

Fix: solver/threed189.py — strict family schemas (every
value recomputed exactly with Fractions/SymPy and checked
by an independent second computation) behind a failure-only
gate in router.py after the Wave 175 block, plus two narrow
repairs at the return sites of the gates that produce the
measured wrong serves: c12gaps142's angle_between_lines on
the r = dress (it pairs the first line's POINT vector with
its direction) and rekha's w115_eq_intercepts on a 3D plane
intercepts question (it drops the z term).

The ASCII i/j/k parser is scoped to line/plane dresses
only: complex-number questions keep their behaviour.
"""
from solver.router import solve_question
from solver.threed189 import solve_threed189

P17 = ("Find the shortest distance between the lines "
       "r = (i + 2j + k) + lambda(i - j + k) and "
       "r = (2i - j - k) + mu(2i + j + 2k)")
P18 = ("Find the direction cosines of the line passing "
       "through the points (-2, 4, -5) and (1, 2, 3)")


def ans(q):
    out = solve_threed189(q)
    assert out is not None, q
    return out


def declines(q):
    assert solve_threed189(q) is None, q


def rans(q):
    return solve_question(q)


# ------------------------------------------------------------------
# (a) Shortest distance between two lines
# ------------------------------------------------------------------

def test_probe17_schema():
    out = ans(P17)
    assert out["op"] == "w189_sd_skew"
    assert out["answer"] == "3·sqrt(2)/2 units (about 2.12 units)"


def test_probe17_router():
    out = rans(P17)
    assert out["op"] == "w189_sd_skew"
    assert "2.12" in out["answer"]


def test_sd_lambda_mu_symbols():
    out = ans("Find the shortest distance between the lines "
              "r = (i + 2j + k) + λ(i - j + k) and "
              "r = (2i - j - k) + μ(2i + j + 2k)")
    assert out["answer"] == "3·sqrt(2)/2 units (about 2.12 units)"


def test_sd_bare_vectors_no_parens():
    out = ans("Find the shortest distance between the lines "
              "r = i + 2j + k + lambda(i - j + k) and "
              "r = 2i - j - k + mu(2i + j + 2k)")
    assert out["op"] == "w189_sd_skew"
    assert "2.12" in out["answer"]


def test_sd_cartesian():
    # a1=(1,2,3) b1=(2,3,4); a2=(2,3,5) b2=(3,4,5);
    # b1 x b2 = (-1, 2, -1), triple = -1, SD = 1/sqrt(6).
    out = ans("Find the shortest distance between the lines "
              "(x-1)/2 = (y-2)/3 = (z-3)/4 and "
              "(x-2)/3 = (y-3)/4 = (z-5)/5")
    assert out["op"] == "w189_sd_skew"
    assert out["answer"] == "sqrt(6)/6 units (about 0.41 units)"


def test_sd_skew_second_example():
    # b1 x b2 = (-4, -3, 5), triple = -9, SD = 9/sqrt(50).
    out = ans("Find the shortest distance between the lines "
              "r = (i + j) + lambda(2i - j + k) and "
              "r = (2i + j - k) + mu(i + 2j + 2k)")
    assert out["answer"] == "9·sqrt(2)/10 units (about 1.27 units)"


def test_sd_parallel_vector():
    # |b x (a2 - a1)| / |b| = sqrt(32)/3 = 4 sqrt(2)/3.
    out = ans("Find the shortest distance between the parallel "
              "lines r = (i + 2j - k) + lambda(2i - j + 2k) and "
              "r = (3i - j + k) + mu(2i - j + 2k)")
    assert out["op"] == "w189_sd_parallel"
    assert out["answer"] == "4·sqrt(2)/3 units (about 1.89 units)"


def test_sd_parallel_cartesian():
    # (a2 - a1) x b = (-8, -8, 4), |.| = 12, |b| = 3 -> 4.
    out = ans("Find the shortest distance between the parallel "
              "lines (x-1)/2 = (y-2)/-1 = (z-3)/2 and "
              "(x-3)/2 = (y+1)/-1 = (z-1)/2")
    assert out["op"] == "w189_sd_parallel"
    assert out["answer"] == "4 units"


def test_sd_parallel_not_labelled_parallel():
    # Directions equal but the word 'parallel' absent: the
    # maths (cross product zero) routes to the parallel form.
    out = ans("Find the shortest distance between the lines "
              "r = (i + 2j - k) + lambda(2i - j + 2k) and "
              "r = (3i - j + k) + mu(4i - 2j + 4k)")
    assert out["op"] == "w189_sd_parallel"
    assert "1.89" in out["answer"]


def test_sd_intersecting_lines():
    # (a2 - a1) . (b1 x b2) = 0 with non-parallel directions:
    # the lines meet at (1, 1, 0), so SD = 0, said plainly.
    out = ans("Find the shortest distance between the lines "
              "r = lambda(i + j) and r = i + mu(j)")
    assert out["op"] == "w189_sd_intersecting"
    assert out["answer"] == "0 units"
    assert any("intersect" in s for s in out["steps"])


def test_sd_coincident_lines():
    out = ans("Find the shortest distance between the lines "
              "r = (i + j) + lambda(i + j) and "
              "r = (2i + 2j) + mu(i + j)")
    assert out["op"] == "w189_sd_coincident"
    assert out["answer"] == "0 units"


def test_sd_single_line_declines():
    declines("Find the shortest distance between the lines "
             "r = (i + 2j + k) + lambda(i - j + k)")


# ------------------------------------------------------------------
# (b) Angle between two lines
# ------------------------------------------------------------------

def test_angle_lines_cartesian():
    # b1=(2,3,-2), b2=(1,2,2): dot 4, cos = 4/(3 sqrt(17)).
    out = ans("Find the angle between the lines "
              "(x-1)/2 = (y+1)/3 = (z-2)/-2 and "
              "(x+2)/1 = (y-1)/2 = (z)/2")
    assert out["op"] == "w189_angle_lines"
    assert out["answer"] == \
        "cos^-1(4·sqrt(17)/51) (about 71.1 degrees)"


def test_angle_lines_vector_dress_schema():
    # True directions (2,1,-1) and (1,2,1): cos = 3/6 = 1/2.
    out = ans("Find the angle between the lines "
              "r = (i + 2j - k) + lambda(2i + j - k) and "
              "r = (2i - j + k) + mu(i + 2j + k)")
    assert out["answer"] == "60 degrees"


def test_angle_lines_vector_dress_router_repair():
    # BEFORE: c12gaps142 served cos^-1(5/6) (33.6 degrees),
    # pairing line 1's point vector with its direction.
    out = rans("Find the angle between the lines "
               "r = (i + 2j - k) + lambda(2i + j - k) and "
               "r = (2i - j + k) + mu(i + 2j + k)")
    assert out["op"] == "w189_angle_lines"
    assert out["answer"] == "60 degrees"


def test_angle_lines_direction_vectors_ijk():
    out = ans("Find the angle between the lines with direction "
              "vectors 2i + 3j - 2k and i + 2j + 2k")
    assert out["answer"] == \
        "cos^-1(4·sqrt(17)/51) (about 71.1 degrees)"


def test_angle_lines_perpendicular():
    out = ans("Find the angle between the lines "
              "r = lambda(i + j) and r = i + mu(i - j + k)")
    # directions (1,1,0) and (1,-1,1): dot = 0.
    assert out["answer"] == "90 degrees"


# ------------------------------------------------------------------
# (c) Line equations
# ------------------------------------------------------------------

def test_line_through_two_points():
    out = ans("Find the equation of the line passing through "
              "the points (1, 2, 3) and (4, 5, 6)")
    assert out["op"] == "w189_line_two_points"
    assert out["answer"] == (
        "r = i + 2j + 3k + lambda(3i + 3j + 3k); "
        "(x - 1)/3 = (y - 2)/3 = (z - 3)/3")


def test_line_through_two_points_router():
    out = rans("Find the equation of the line passing through "
               "the points (1, 2, 3) and (4, 5, 6)")
    assert out["op"] == "w189_line_two_points"


def test_line_two_points_zero_direction_component():
    out = ans("Find the equation of the line passing through "
              "the points (1, 2, 3) and (1, 5, 3)")
    assert "(y - 2)/3" in out["answer"]
    assert "x = 1" in out["answer"] and "z = 3" in out["answer"]


def test_line_point_direction_ratios():
    out = ans("Find the equation of the line passing through "
              "the point (1, 2, 3) and having direction "
              "ratios 2, 3, -2")
    assert out["op"] == "w189_line_point_dir"
    assert out["answer"] == (
        "r = i + 2j + 3k + lambda(2i + 3j - 2k); "
        "(x - 1)/2 = (y - 2)/3 = (z - 3)/-2")


def test_line_point_position_vector_direction():
    out = ans("Find the equation of the line through the point "
              "with position vector 2i - j + 3k and parallel "
              "to the vector i + 4j - 2k")
    assert out["answer"] == (
        "r = 2i - j + 3k + lambda(i + 4j - 2k); "
        "(x - 2)/1 = (y + 1)/4 = (z - 3)/-2")


def test_line_parallel_to_cartesian_line():
    out = ans("Find the equation of the line passing through "
              "the point (5, 2, -4) and parallel to the line "
              "(x-1)/3 = (y-2)/2 = (z+4)/-8")
    assert out["op"] == "w189_line_point_dir"
    assert "(x - 5)/3 = (y - 2)/2 = (z + 4)/-8" in out["answer"]


def test_line_same_point_twice_declines():
    declines("Find the equation of the line passing through "
             "the points (1, 2, 3) and (1, 2, 3)")


# ------------------------------------------------------------------
# (d) Plane basics
# ------------------------------------------------------------------

def test_plane_point_normal():
    # n . a = 2 - 2 + 9 = 9.
    out = ans("Find the equation of the plane passing through "
              "the point (1, 2, 3) with normal vector 2i - j + 3k")
    assert out["op"] == "w189_plane_point_normal"
    assert out["answer"] == "r.(2i - j + 3k) = 9; 2x - y + 3z = 9"


def test_plane_point_normal_second():
    out = ans("Find the equation of the plane through the "
              "point (2, 3, 4) whose normal vector is 3i + 2j - k")
    assert out["answer"] == "r.(3i + 2j - k) = 8; 3x + 2y - z = 8"


def test_plane_point_normal_direction_ratios():
    out = ans("Find the equation of the plane passing through "
              "the point (1, 0, -2) with normal having "
              "direction ratios 1, -2, 3")
    assert out["answer"] == \
        "r.(i - 2j + 3k) = -5; x - 2y + 3z = -5"


def test_plane_three_points():
    # AB = (0,1,1), AC = (-3,1,-1), AB x AC = (-2,-3,3),
    # reduced plane 2x + 3y - 3z = 5 (all 3 points satisfy).
    out = ans("Find the equation of the plane passing through "
              "the points (1, 1, 0), (1, 2, 1) and (-2, 2, -1)")
    assert out["op"] == "w189_plane_three_points"
    assert out["answer"] == \
        "r.(2i + 3j - 3k) = 5; 2x + 3y - 3z = 5"


def test_plane_three_collinear_points_declines():
    declines("Find the equation of the plane passing through "
             "the points (1, 1, 0), (2, 2, 0) and (3, 3, 0)")


def test_plane_zero_normal_declines():
    declines("Find the equation of the plane passing through "
             "the point (1, 2, 3) with normal vector "
             "0i + 0j + 0k")


def test_plane_intercepts():
    out = ans("Find the equation of the plane with intercepts "
              "2, 3 and 4 on the x, y and z axes respectively")
    assert out["op"] == "w189_plane_intercepts"
    assert out["answer"] == \
        "x/2 + y/3 + z/4 = 1; 6x + 4y + 3z = 12"


def test_plane_intercepts_per_axis():
    out = ans("Find the equation of the plane with x-intercept "
              "2, y-intercept 3 and z-intercept 4")
    assert out["answer"] == \
        "x/2 + y/3 + z/4 = 1; 6x + 4y + 3z = 12"


def test_plane_intercepts_router_repair():
    # BEFORE: rekha's 2D schema served "x/2 + y/3 = 1".
    out = rans("Find the equation of the plane with intercepts "
               "2, 3 and 4 on the x, y and z axes respectively")
    assert out["op"] == "w189_plane_intercepts"
    assert "z/4" in out["answer"]


def test_distance_point_plane_vector_dress():
    # |1 + 2 - 2 - 5| / 3 = 4/3.
    out = ans("Find the distance of the point (1, 1, 1) from "
              "the plane r.(i + 2j - 2k) = 5")
    assert out["op"] == "w189_point_plane_distance"
    assert out["answer"] == "4/3 units"


def test_distance_point_plane_vector_dress_second():
    # |2 + 3 - 6 - 7| / 7 = 8/7.
    out = rans("Find the distance of the point (1, 1, 1) from "
               "the plane r.(2i + 3j - 6k) = 7")
    assert out["op"] == "w189_point_plane_distance"
    assert out["answer"] == "8/7 units"


def test_angle_between_planes_cartesian():
    # normals (2,-1,1), (1,2,2): dot 2, cos = 2/(3 sqrt(6)).
    out = ans("Find the angle between the planes "
              "2x - y + z = 5 and x + 2y + 2z = 3")
    assert out["op"] == "w189_angle_planes"
    assert out["answer"] == \
        "cos^-1(sqrt(6)/9) (about 74.2 degrees)"


def test_angle_between_planes_vector_dress():
    # normals (1,1,-1), (2,-1,1): dot = 0.
    out = ans("Find the angle between the planes "
              "r.(i + j - k) = 3 and r.(2i - j + k) = 5")
    assert out["answer"] == "90 degrees"


def test_angle_between_parallel_planes():
    out = ans("Find the angle between the planes "
              "3x + 4y + 5z = 10 and 6x + 8y + 10z = 20")
    assert out["answer"] == "0 degrees"


def test_angle_planes_router():
    out = rans("Find the angle between the planes "
               "2x - y + z = 5 and x + 2y + 2z = 3")
    assert out["op"] == "w189_angle_planes"
    assert "74.2" in out["answer"]


# ------------------------------------------------------------------
# Controls — already-solving forms and other families untouched
# ------------------------------------------------------------------

def test_probe18_direction_cosines_control():
    out = rans(P18)
    assert out["op"] == "direction cosines"
    assert out["answer"] == "(0.3419, -0.2279, 0.9117)"


def test_tierA_line_point_dir_control():
    out = rans("Find the equation of the line passing through "
               "the point (1, 2, -4) and parallel to the vector "
               "3i + 2j - 8k")
    assert out["op"] == "w169_line_3d"
    assert "(x - 1)/3 = (y - 2)/2 = (z + 4)/-8" in out["answer"]


def test_angle_tuples_control_not_displaced():
    # c12gaps142 serves this dress CORRECTLY (no r = lines):
    # the repair must not touch it.
    out = rans("Find the angle between the lines with direction "
               "vectors (2, 3, -2) and (1, 2, 2)")
    assert out["op"] == "angle_between_lines"
    assert "71.1" in out["answer"]


def test_angle_direction_ratios_control():
    out = rans("Find the angle between the lines whose direction "
               "ratios are 2, 3, -2 and 1, 2, 2")
    assert out["answer"] == "71.13 degrees"


def test_distance_point_plane_cartesian_control():
    out = rans("Find the distance of the point (2, 3, -5) from "
               "the plane x + 2y - 2z = 9")
    assert out["op"] == "point plane distance"
    assert out["answer"] == "3"


def test_2d_intercepts_control_not_displaced():
    # A 2D line intercepts question (no plane, no z) stays
    # with rekha's 2D answer.
    out = rans("Find the equation of the line with intercepts "
               "2 and 3 on the x and y axes")
    assert out["op"] == "w115_eq_intercepts"
    assert out["answer"] == "x/2 + y/3 = 1"


def test_complex_numbers_control():
    declines("Evaluate (2 + 3i)(1 - i)")
    out = rans("Evaluate (2 + 3i)(1 - i)")
    assert out["answer"] == "5 + I"


def test_2d_geometry_controls():
    declines("Find the distance between the points (1, 2) "
             "and (4, 6)")
    declines("Find the equation of the line passing through "
             "the points (1, 2) and (3, 4)")
    out = rans("Find the distance between the points (1, 2) "
               "and (4, 6)")
    assert out["answer"] == "5"


def test_vector_algebra_question_declines():
    # A plain vector-algebra ask is not a line/plane dress.
    declines("Find the angle between the vectors "
             "2i + 3j - k and i - j + 2k")
