"""Wave 32 (Suraj, 14 Nov 2026: "or bhi topics add karo,
karib 50 topics add karo"): ~50 NEW exact-solve topics.

Every topic below was first PROVEN to be a gap by a probe
battery through the real user path (api._solve_friendly): the
question either fell back (similar example / guide) or — the
worse class — a valid-looking op answered a DIFFERENT
question with a wrong number (hemisphere answered as sphere,
annual CI answering a half-yearly ask, cylinder TSA answering
a CSA ask, single-coin mean answering an insert-geometric-
mean ask, ...). Each test here asserts the solver now
computes the answer from the STUDENT'S OWN numbers through
the friendly path, with the wave's op tag.

76 topics: calculus continuity/differentiability (4),
trigonometry (8), geometry mensuration + coordinate + circles
+ 3D (29), applied money/Bayes/LP/work stories (24),
sequences (2), algebra theorems (6), grouped statistics (3).

Solver-side only: no template/CSS/JS changed, so the ?v=29 /
ganitra-static-v6 delivery pins deliberately do NOT move.
Deliberately NOT taken (stated in the audit doc): LP from
raw inequalities, single geometric mean of two numbers
(frozen statistics shortcut answers it as the arithmetic
mean; the NCERT insert-means ask IS covered), proof/verify
identity asks, cumulative-frequency ogive forms.
"""
import pytest

from api import _solve_friendly


def _r(q):
    return _solve_friendly(q)


def _assert(q, op, *needles):
    r = _r(q)
    assert r.get("op") == op, (q, r.get("op"), r.get("answer"))
    ans = str(r.get("answer", ""))
    for n in needles:
        assert n in ans, (q, n, ans)
    return r


# -----------------------------------------------------------------
# Calculus: continuity & differentiability (Class 12)
# -----------------------------------------------------------------

def test_continuity_piecewise_continuous():
    _assert("Examine the continuity of the function "
            "f(x) = 2x + 3 for x <= 2, x + 5 for x > 2 "
            "at x = 2.",
            "continuity_check", "Continuous at x = 2")


def test_continuity_piecewise_not_continuous():
    _assert("Examine the continuity of the function "
            "f(x) = 2x + 3 for x <= 2, x + 9 for x > 2 "
            "at x = 2.",
            "continuity_check", "Not continuous")


def test_continuity_find_k():
    _assert("Find the value of k for which the function "
            "f(x) = kx + 1, if x <= 3; 5x - 7, if x > 3 is "
            "continuous at x = 3.",
            "continuity_find_k", "k = 7/3")


def test_differentiability_abs_not_differentiable():
    _assert("Check whether f(x) = |x| is differentiable "
            "at x = 0.",
            "differentiability_check", "Not differentiable")


def test_differentiability_polynomial():
    _assert("Check the differentiability of f(x) = x^2 "
            "at x = 1.",
            "differentiability_check", "Differentiable at x = 1")


def test_continuity_removable_discontinuity():
    _assert("Discuss the continuity of "
            "f(x) = (x^2 - 4)/(x - 2) at x = 2.",
            "continuity_limit", "Not continuous", "limit = 4")


# -----------------------------------------------------------------
# Trigonometry (Classes 10-12)
# -----------------------------------------------------------------

def test_angle_of_depression_distance():
    _assert("From the top of a 60 m high tower, the angle of "
            "depression of an object on the ground is "
            "30 degrees. Find the distance of the object from "
            "the foot of the tower.",
            "angle_of_depression", "103.92")


def test_two_observation_height():
    _assert("The angle of elevation of the top of a tower "
            "from a point on the ground changes from "
            "30 degrees to 60 degrees when the observer moves "
            "20 m closer to the tower. The two points are "
            "20 m apart. Find the height of the tower.",
            "two_observation_height", "17.32")


@pytest.mark.parametrize("q,needle", [
    ("Find the principal value of sec^-1(2).", "pi/3"),
    ("Find the principal value of cosec^-1(2).", "pi/6"),
    ("Find the principal value of cot^-1(sqrt(3)).", "pi/6"),
    ("Find the principal value of sin^-1(1).", "pi/2"),
])
def test_inverse_trig_principal_values(q, needle):
    _assert(q, "inverse_trig_value", needle)


def test_inverse_trig_complementary_sum():
    _assert("Evaluate sin^-1(1/2) + cos^-1(1/2).",
            "inverse_trig_sum", "pi/2")


def test_inverse_trig_reduction():
    _assert("Evaluate sin^-1(sin 210 degrees).",
            "inverse_trig_reduction", "-30")


def test_inverse_trig_tan_formula():
    _assert("Evaluate tan^-1(1) + tan^-1(1/2).",
            "inverse_trig_formula", "atan(3)")


def test_standard_values_written_out_degrees():
    _assert("Evaluate sin 60 degrees cos 30 degrees + "
            "sin 30 degrees cos 60 degrees.",
            "value", "1")


def test_standard_values_squared_forms():
    _assert("Evaluate 2 sin^2 30 degrees + "
            "3 cos^2 60 degrees.",
            "value", "5/4")


def test_complementary_angle_ratio():
    _assert("Evaluate tan 65 degrees / cot 25 degrees.",
            "complementary_ratio", "1")


# -----------------------------------------------------------------
# Geometry: mensuration (Class 10) — several were hijacked
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Find the volume of a frustum of a cone with radii "
     "10 cm and 6 cm and height 7 cm.",
     "frustum volume", "1436.76"),
    ("Find the curved surface area of a frustum of a cone "
     "with radii 8 cm and 4 cm and height 6 cm.",
     "frustum csa", "271.85"),
    ("Find the total surface area of a frustum of a cone "
     "with radii 8 cm and 4 cm and height 6 cm.",
     "frustum tsa", "523.18"),
    ("Find the volume of a hemisphere of radius 7 cm.",
     "hemisphere volume", "718.378"),
    ("Find the total surface area of a hemisphere of "
     "radius 7 cm.",
     "hemisphere tsa", "461.814"),
    ("Find the curved surface area of a hemisphere of "
     "radius 14 cm.",
     "hemisphere csa", "1231.5"),
    ("Find the curved surface area of a cone with "
     "radius 7 cm and slant height 10 cm.",
     "cone csa", "219.911"),
    ("Find the total surface area of a cone with "
     "radius 7 cm and slant height 10 cm.",
     "cone tsa", "373.85"),
    ("Find the curved surface area of a cylinder with "
     "radius 7 cm and height 10 cm.",
     "cylinder csa", "439.823"),
    ("Find the volume of a cuboid with length 10 cm, "
     "breadth 8 cm and height 6 cm.",
     "cuboid volume", "480"),
    ("Find the total surface area of a cuboid with "
     "length 10 cm, breadth 8 cm and height 6 cm.",
     "cuboid tsa", "376"),
    ("Find the total volume of a solid made of a cylinder "
     "of height 5 cm and a cone of height 4 cm mounted on "
     "it, both of radius 3 cm.",
     "combined volume", "179.071"),
    ("Find the area of a sector of a circle with "
     "radius 14 cm and angle 90 degrees.",
     "sector area", "153.938"),
    ("Find the area of a segment of a circle with "
     "radius 14 cm and angle 90 degrees.",
     "segment area", "55.938"),
    ("Find the length of an arc of a circle with "
     "radius 10 cm and angle 60 degrees.",
     "arc length", "10.472"),
])
def test_mensuration_topics(q, op, needle):
    _assert(q, op, needle)


def test_existing_cylinder_tsa_not_hijacked_back():
    # The generic cylinder branch owns TSA — the new CSA
    # branch must not steal it.
    r = _r("Find the total surface area of a cylinder with "
           "radius 7 cm and height 10 cm.")
    assert "747.6991" in str(r.get("answer", "")), r


def test_existing_sphere_volume_intact():
    r = _r("Find the volume of a sphere of radius 7 cm.")
    assert r.get("op") == "volume"
    assert "1436.755" in str(r.get("answer", "")), r


# -----------------------------------------------------------------
# Geometry: circles (Class 10)
# -----------------------------------------------------------------

def test_tangent_length_from_external_point():
    _assert("Find the length of the tangent drawn from the "
            "point (5, 0) to the circle x^2 + y^2 = 16.",
            "tangent length", "3")


def test_angle_between_two_tangents():
    _assert("Tangents are drawn from a point at a distance "
            "of 10 cm from the centre of a circle of "
            "radius 6 cm. Find the angle between the two "
            "tangents.",
            "angle between tangents", "73.74")


def test_chord_distance_from_centre():
    _assert("A chord of length 16 cm is drawn in a circle "
            "of radius 10 cm. Find the distance of the chord "
            "from the centre.",
            "chord distance", "6")


# -----------------------------------------------------------------
# Geometry: coordinate (Class 10) + 3D (Class 12)
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Find the centroid of a triangle with vertices "
     "(2, 3), (4, 5) and (6, 7).",
     "centroid", "(4.0, 5.0)"),
    ("Find the area of a quadrilateral with vertices "
     "(0, 0), (4, 0), (6, 3) and (2, 5).",
     "quadrilateral area", "18"),
    ("Check whether the points (1, 2), (2, 3) and (3, 4) "
     "are collinear.",
     "collinearity", "collinear"),
    ("Find the distance of the point (3, 4) from the "
     "origin.",
     "distance from origin", "5"),
    ("In what ratio does the x-axis divide the line "
     "segment joining (3, 4) and (2, -5)?",
     "ratio of division", "0.8 : 1"),
    ("Find the point on the x-axis which is equidistant "
     "from the points (2, 3) and (4, 5).",
     "equidistant point", "(7.0, 0)"),
    ("Find the direction ratios of the line joining the "
     "points (1, 2, 3) and (4, 6, 8).",
     "direction ratios", "(3, 4, 5)"),
    ("Find the direction cosines of the line joining the "
     "points (1, 2, 3) and (4, 6, 8).",
     "direction cosines", "0.4243"),
    ("Find the angle between two lines whose direction "
     "ratios are 1, 2, 2 and 2, 1, 2.",
     "angle between lines", "27.27"),
    ("Find the distance of the point (1, 2, 3) from the "
     "plane 2x + 3y + 4z = 10.",
     "point plane distance", "1.8569"),
    ("Find the point which divides the join of (1, 2, 3) "
     "and (3, 4, 5) internally in the ratio 2:1.",
     "section formula 3d", "2.333"),
    ("Find the midpoint of the points (1, 2, 3) and "
     "(3, 4, 5).",
     "midpoint 3d", "(2, 3, 4)"),
])
def test_coordinate_and_3d_topics(q, op, needle):
    _assert(q, op, needle)


def test_existing_distance_between_points_intact():
    r = _r("Find the distance between (1, 2) and (4, 6).")
    assert r.get("op") == "distance"
    assert str(r.get("answer", "")).startswith("5"), r


# -----------------------------------------------------------------
# Applied: money (Classes 8-10)
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Find the compound interest on Rs 10000 at 10% per "
     "annum for 2 years, compounded half-yearly.",
     "compound_interest_freq", "2155.06"),
    ("Find the compound interest on Rs 8000 at 12% per "
     "annum for 1 year, compounded quarterly.",
     "compound_interest_freq", "1004.07"),
    ("An article costs Rs 5000. GST is charged at 18% on "
     "it. Find the GST amount and the total amount to be "
     "paid.",
     "gst", "5900"),
    ("The total price of an item including 28% GST is "
     "Rs 6400. Find the price before GST.",
     "gst_reverse", "5000"),
    ("The marked price of an article is Rs 2000. Two "
     "successive discounts of 10% and 5% are offered. "
     "Find the selling price.",
     "successive_discount", "1710"),
    ("Find a single discount equivalent to two successive "
     "discounts of 20% and 10%.",
     "successive_discount_equiv", "28%"),
    ("A shopkeeper sells two articles at Rs 999 each. On "
     "one he gains 10% and on the other he loses 10%. "
     "Find his overall gain or loss percent.",
     "two_articles_same_sp", "Loss of 1%"),
])
def test_money_topics(q, op, needle):
    _assert(q, op, needle)


# -----------------------------------------------------------------
# Applied: quadratic asks (Class 10)
# -----------------------------------------------------------------

def test_find_k_for_equal_roots_irrational():
    _assert("Find the value of k for which the equation "
            "2x^2 + kx + 3 = 0 has two equal roots.",
            "find_k_equal_roots", "k = -2·sqrt(6)",
            "k = 2·sqrt(6)")


def test_find_k_for_equal_roots_integer():
    _assert("Find the value of k for which the equation "
            "x^2 - 4x + k = 0 has equal roots.",
            "find_k_equal_roots", "k = 4")


def test_sum_and_product_of_roots():
    _assert("Find the sum and product of roots of the "
            "equation 3x^2 - 5x + 2 = 0.",
            "sum_product_roots", "Sum = 5/3", "Product = 2/3")


def test_nature_of_roots_with_the_equation_wording():
    # Robustness fix riding along: "of THE EQUATION x^2..."
    # used to keep the words in the parse text and fail.
    _assert("Find the nature of roots of the equation "
            "x^2 + 5x + 6 = 0",
            "nature_of_roots", "Two distinct real roots")


# -----------------------------------------------------------------
# Applied: means insertion + identity evaluation (Classes 9-11)
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Insert two arithmetic means between 8 and 26.",
     "insert_arithmetic_means", "14, 20"),
    ("Insert one geometric mean between 4 and 16.",
     "insert_geometric_means", "8"),
    ("Insert two geometric means between 4 and 32.",
     "insert_geometric_means", "8, 16"),
    ("If a + b = 10 and ab = 21, find a^2 + b^2.",
     "identity_a2_b2", "58"),
    ("If a + b = 5 and ab = 6, find a^3 + b^3.",
     "identity_a3_b3", "35"),
])
def test_means_and_identity_topics(q, op, needle):
    _assert(q, op, needle)


# -----------------------------------------------------------------
# Applied: pipes, work, boats, trains (Classes 8-10)
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Pipe A can fill a tank in 6 hours and pipe B can "
     "fill it in 8 hours. How long will they take to fill "
     "the tank together?",
     "pipes", "24/7"),
    ("A pipe can fill a tank in 4 hours and another pipe "
     "can empty it in 6 hours. If both are opened "
     "together, in how many hours will the tank be filled?",
     "pipes", "12"),
    ("A can do a piece of work in 10 days and B can do "
     "it in 15 days. In how many days can they do it "
     "together?",
     "work_together", "6"),
    ("A is twice as efficient as B. Together they finish "
     "a work in 12 days. In how many days can A alone do "
     "the work?",
     "work_efficiency", "18"),
    ("A boat goes 36 km downstream in 3 hours and 24 km "
     "upstream in 4 hours. Find the speed of the boat in "
     "still water and the speed of the stream.",
     "boat_stream", "Boat 9 km/h, stream 3 km/h"),
    ("Two trains of lengths 120 m and 180 m run at "
     "60 km/h and 40 km/h in opposite directions. In how "
     "much time will they cross each other?",
     "two_trains_crossing", "10.8"),
    ("Two trains of lengths 150 m and 100 m run at "
     "50 km/h and 30 km/h in the same direction. In how "
     "much time will they cross each other?",
     "two_trains_crossing", "45"),
])
def test_work_story_topics(q, op, needle):
    _assert(q, op, needle)


def test_pipes_that_can_never_fill_stays_honest():
    r = _r("A pipe can fill a tank in 6 hours and another "
           "pipe can empty it in 4 hours. If both are "
           "opened together, will the tank fill?")
    assert r.get("op") == "pipes"
    assert "never fill" in str(r.get("answer", "")), r


# -----------------------------------------------------------------
# Applied: Bayes theorem + LP corner evaluation (Class 12)
# -----------------------------------------------------------------

def test_bayes_two_bags():
    _assert("Bag A contains 3 red balls and 2 black balls. "
            "Bag B contains 2 red balls and 3 black balls. "
            "A bag is chosen at random and a ball is drawn "
            "from it, which is found to be red. Find the "
            "probability that the ball was drawn from bag A.",
            "bayes_bags", "3/5")


def test_bayes_medical_test():
    _assert("A test detects a disease with probability "
            "0.99 when a person has it, and gives a false "
            "positive with probability 0.05 when a person "
            "does not have it. 1% of people have the "
            "disease. If a person tests positive, what is "
            "the probability that the person actually has "
            "the disease?",
            "bayes_medical", "1/6")


def test_bayes_factory_machines():
    _assert("Machine A produces 60% of items with 2% "
            "defective, machine B produces 40% with 3% "
            "defective. An item is found defective. Find "
            "the probability it came from machine A.",
            "bayes_factory", "1/2")


def test_lp_maximise_at_corners():
    _assert("Maximise Z = 3x + 4y at the corner points "
            "(0, 0), (6, 0), (3, 4) and (0, 5).",
            "lp_maximise", "Maximum Z = 25 at (3, 4)")


def test_lp_minimise_at_corners():
    _assert("Minimise Z = x + 2y subject to constraints "
            "with corner points (2, 0), (2, 2), (0, 3) and "
            "(0, 0). Evaluate Z at the corner points.",
            "lp_minimise", "Minimum Z = 0 at (0, 0)")


# -----------------------------------------------------------------
# Sequences (Class 11 / AP Class 10)
# -----------------------------------------------------------------

def test_ap_nth_term_from_the_end():
    _assert("Find the 10th term from the end of the AP "
            "7, 10, 13, ..., 184.",
            "ap_nth_from_end", "157")


def test_ap_how_many_terms_for_sum():
    _assert("How many terms of the AP 9, 17, 25, ... must "
            "be taken so that their sum is 636?",
            "ap_terms_for_sum", "12")


def test_existing_ap_nth_term_intact():
    r = _r("Find the 10th term of the AP 7, 10, 13, ...")
    assert str(r.get("answer", "")).startswith("34"), r


# -----------------------------------------------------------------
# Algebra: polynomial theorems + rationalisation (Class 9-10)
# -----------------------------------------------------------------

@pytest.mark.parametrize("q,op,needle", [
    ("Find the remainder when x^3 + 3x^2 + 3x + 1 is "
     "divided by x + 1.",
     "remainder_theorem", "0"),
    ("Is x + 1 a factor of x^3 + 3x^2 + 3x + 1?",
     "factor_theorem_check", "Yes"),
    ("Is x + 2 a factor of x^2 - 5x + 6?",
     "factor_theorem_check", "No"),
    ("Find the value of k for which (x - 1) is a factor "
     "of x^3 - 6x^2 + 11x + k.",
     "factor_theorem_k", "k = -6"),
    ("For the cubic polynomial x^3 - 6x^2 + 11x - 6, "
     "find α + β + γ, αβ + βγ + γα and αβγ.",
     "cubic_zeroe_relations", "α + β + γ = 6",
     ),
    ("Verify that 1, 2 and 3 are zeroes of the cubic "
     "polynomial x^3 - 6x^2 + 11x - 6.",
     "verify_zeroes", "Verified"),
    ("Rationalise the denominator of 1/(2 + sqrt(3)).",
     "rationalise", "2 - sqrt(3)"),
    ("Rationalise the denominator of 5/sqrt(7).",
     "rationalise", "5·sqrt(7)/7"),
])
def test_algebra_theorem_topics(q, op, needle):
    _assert(q, op, needle)


def test_cubic_relations_all_three_values():
    r = _r("For the cubic polynomial "
           "x^3 - 6x^2 + 11x - 6, find α + β + γ, "
           "αβ + βγ + γα and αβγ.")
    ans = str(r.get("answer", ""))
    assert "αβ + βγ + γα = 11" in ans and "αβγ = 6" in ans, ans


def test_verify_zeroes_rejects_a_wrong_zero():
    r = _r("Verify that 1, 2 and 4 are zeroes of the cubic "
           "polynomial x^3 - 6x^2 + 11x - 6.")
    assert r.get("op") == "verify_zeroes"
    assert "Not all" in str(r.get("answer", "")), r


# -----------------------------------------------------------------
# Grouped statistics (Class 10)
# -----------------------------------------------------------------

_TABLE_Q = ("of the data with class intervals 0-10, "
            "10-20, 20-30, 30-40 and frequencies "
            "5, 8, 12, 5.")


def test_grouped_mean():
    _assert("Find the mean " + _TABLE_Q,
            "grouped_mean", "20.6667")


def test_grouped_median():
    _assert("Find the median " + _TABLE_Q,
            "grouped_median", "21.6667")


def test_grouped_mode():
    _assert("Find the mode " + _TABLE_Q,
            "grouped_mode", "23.6364")


def test_wave31_coins_still_exact_after_statistics_edit():
    r = _r("Two coins are tossed simultaneously. What is "
           "the probability of getting at most one head?")
    assert str(r.get("answer", "")).startswith("3/4"), r


def test_raw_list_mean_and_median_intact():
    r1 = _r("Find the mean of 4, 6, 8, 10.")
    assert str(r1.get("answer", "")).startswith("7"), r1
    r2 = _r("Find the median of the following data: "
            "3, 5, 7, 9, 11.")
    assert str(r2.get("answer", "")).startswith("7"), r2


# -----------------------------------------------------------------
# Guards: the router pre-checks must not steal old questions
# -----------------------------------------------------------------

def test_guard_plain_system_still_solves_as_system():
    # The applied-first pre-check must FALL THROUGH for a
    # two-equation system (it is not an identity-evaluation
    # ask): algebra's system solver answers it, exactly as
    # before Wave 32 (its answer for this wording is a known
    # pre-existing quirk, identical on the pristine tree).
    r = _r("If a + b = 10 and a - b = 4, find a and b.")
    assert r.get("op") == "system", r


def test_guard_trig_ratio_question_untouched():
    r = _r("If sin A = 3/5, find cos A.")
    assert str(r.get("answer", "")).startswith("cos A = 4/5"), r


def test_guard_train_question_wave30_intact():
    r = _r("A train travels 360 km at a uniform speed. If "
           "the speed had been 5 km/h more, it would have "
           "taken 1 hour less. Find the speed of the train.")
    assert "40" in str(r.get("answer", "")), r
