"""Wave 58 (15 Nov 2026): ZERO-MISTAKE hunt — every known
wrong answer fixed at its root cause.

Families: trailing full stop; any-script junk detection;
Hindi word problems; ratio / HCF-LCM echoes; probability
(at least / not / or / streak / addition rule); worded
fractions + salvage echo guard; square/cube word forms;
"x" as a times sign; geometric mean; substitution /
find-k / composition; cubic Vieta; log forms; rationalise
display; concentric chord; theta identities; sqrt ratios;
ODE prose; conic tangents / normals.
"""
from api import _solve_friendly


def _r(q):
    return _solve_friendly(q)


def _ans(q):
    return str(_r(q).get("answer", ""))


def _exact(q):
    return "fallback" not in _r(q)


# --- trailing full stop --------------------------------------
def test_expand_trailing_dot():
    assert _exact("Expand (2x + 3y)^2.")
    assert "4·x^2" in _ans("Expand (2x + 3y)^2.")


def test_factorise_trailing_dot():
    assert _ans("Factorise x^2 - 9.") == "(x - 3)·(x + 3)"


def test_decimal_not_eaten():
    assert _ans("What is 2.5 + 1.5?") == "4"


# --- Hindi patterns + junk ------------------------------------
def test_hindi_rectangle_area():
    assert _ans("एक आयत की लंबाई 15 cm और चौड़ाई 10 cm है। "
                "इसका क्षेत्रफल ज्ञात कीजिए।") == "150"


def test_hindi_simple_interest():
    assert _ans("12000 रुपये का 3 वर्ष के लिए 5% वार्षिक दर "
                "से साधारण ब्याज ज्ञात कीजिए।") == "1800"


def test_hindi_train_time():
    assert _ans("एक रेलगाड़ी 60 km/h की चाल से 300 km की "
                "दूरी कितने समय में तय करेगी?") == "5"


def test_hindi_fresh_cone():
    # Merge-3: in the merged tree Wave 52's hindi_cone_volume
    # pattern answers in the app's established format
    # "98·pi ≈ 307.876" — the same value; assert containment,
    # as Wave 52's own Hindi tests do.
    assert "307.876" in _ans(
        "एक शंकु की त्रिज्या 7 cm और ऊंचाई 6 cm है। "
        "शंकु का आयतन ज्ञात कीजिए।")


# --- ratio / HCF-LCM echoes -----------------------------------
def test_named_share():
    assert _ans("Divide Rs 900 among A, B and C in the "
                "ratio 2:3:4. How much does C get?") \
        == "Rs 400"


def test_triangle_angles_ratio():
    assert _ans("The angles of a triangle are in the ratio "
                "2:3:4. Find the largest angle.") == "80°"


def test_hcf_lcm_other_number():
    assert _ans("The HCF of two numbers is 12 and their "
                "LCM is 240. If one number is 60, find the "
                "other number.") == "48"


# --- probability ----------------------------------------------
def test_die_at_least():
    assert "1/3" in _ans(
        "What is the probability of getting at least 5 "
        "when a die is rolled?")


def test_die_at_most_fresh():
    assert "1/3" in _ans(
        "What is the probability of getting at most 2 "
        "when a die is rolled?")


def test_die_not_getting():
    assert "5/6" in _ans(
        "A die is thrown once. What is the probability "
        "of not getting a 6?")


def test_die_not_even_fresh():
    assert "1/2" in _ans(
        "A die is thrown once. What is the probability "
        "of not getting an even number?")


def test_card_or_union():
    assert "2/13" in _ans(
        "A card is drawn from a well-shuffled deck of 52 "
        "cards. What is the probability of getting a king "
        "or a queen?")


def test_streak_not_confident():
    assert not _exact(
        "A coin is tossed 100 times in a row and it lands "
        "heads every time. What is the probability it "
        "lands heads on the next toss?")


def test_union_mutually_exclusive():
    assert "0.7" in _ans(
        "Two events A and B are mutually exclusive. If "
        "P(A) = 0.3 and P(B) = 0.4, find P(A or B).")


def test_union_general():
    assert "0.7" in _ans(
        "If P(A) = 0.5, P(B) = 0.4 and P(A and B) = 0.2, "
        "find P(A or B).")


def test_two_coins_not_a_head():
    assert "1/4" in _ans(
        "Two coins are tossed simultaneously. What is "
        "the probability of not getting a head?")


# --- fractions --------------------------------------------------
def test_add_fractions_words():
    assert _ans("Add 2/3 and 3/4.") == "17/12"


def test_subtract_from_words():
    assert _ans("Subtract 1/4 from 5/6.") == "7/12"


def test_difference_between_words():
    assert _ans("Find the difference between 5/6 and "
                "1/4.") == "7/12"


def test_hinglish_expression_exact():
    assert _ans("2/3 + 3/4 kitna hota hai?") == "17/12"


def test_salvage_never_echoes_operand():
    assert _ans("Add 2/3 & 3/4 please") != "2/3"


# --- square / cube / x-times ------------------------------------
def test_square_of():
    assert _ans("Find the square of 15.") == "225"


def test_squared_word():
    assert _ans("What is 15 squared?") == "225"


def test_ka_cube():
    assert _ans("25 ka cube kitna hota hai?") == "15625"


def test_ka_square_root_not_squared():
    assert _ans("144 ka square root batao") != "20736"


def test_numeric_x_is_times():
    assert _ans("Simplify 2^3 x 2^2.") == "32"


def test_plain_x_times():
    assert _ans("Evaluate 3 x 4.") == "12"


def test_variable_x_untouched():
    a = _ans("Simplify 3x + 2x.")
    assert "5" in a and "x" in a


# --- means ------------------------------------------------------
def test_geometric_mean():
    assert _ans("Find the geometric mean of 4 and 9.") \
        == "6"


def test_geometric_mean_three():
    assert _ans("Find the geometric mean of 2, 4 and 8.") \
        == "4"


def test_arithmetic_mean_control():
    assert _ans("What is the mean of 4 and 9?") == "6.5"


# --- algebra: substitution / find-k / composition / Vieta -------
def test_substitution_two_vars():
    assert _ans("If a = 2 and b = -3, find the value of "
                "a^2 + b^2 - ab.") == "19"


def test_substitution_radical():
    assert _ans("If x = 2 + sqrt(3), find 1/x.") \
        == "2 - sqrt(3)"


def test_find_k_given_root():
    assert "17/4" in _ans(
        "If x = 2 is a solution of 3x^2 - 2kx + 5 = 0, "
        "find the value of k.")


def test_composition():
    assert "4·x^2 + 12·x + 10" in _ans(
        "If f(x) = x^2 + 1 and g(x) = 2x + 3, "
        "find f(g(x)).")


def test_composition_numeric():
    assert "50" in _ans(
        "If f(x) = x^2 + 1 and g(x) = 2x + 3, "
        "find f(g(2)).")


def test_cubic_vieta_sum():
    assert _ans("Find the sum of the zeroes of the "
                "polynomial x^3 - 5x^2 + 2x + 8.") \
        == "Sum = 5"


def test_quadratic_vieta_control():
    assert _ans("Find the sum and product of the zeroes "
                "of x^2 - 5x + 6.") == "Sum = 5, Product = 6"


# --- logs --------------------------------------------------------
def test_log_solve_base10():
    assert "316.228" in _ans(
        "If log x = 2.5 and log means base 10, find x.")


def test_log_solve_subscript():
    assert _ans("If log_2 x = 5, find x.") == "x = 32"


def test_log_value_subscript_space():
    assert _ans("Find the value of log_2 32.") == "5"


def test_log_value_base10_word():
    assert _ans("Find the value of log 100.") == "2"


# --- rationalise / geometry --------------------------------------
def test_rationalise_single_fraction():
    assert _ans("Rationalise the denominator of "
                "1/(3 + sqrt(2)).") == "(3 - sqrt(2))/7"


def test_rationalise_monomial_control():
    assert _ans("Rationalise the denominator of "
                "5/sqrt(7).") == "5·sqrt(7)/7"


def test_concentric_chord():
    assert _ans("Two concentric circles have radii 5 cm "
                "and 3 cm. Find the length of the chord of "
                "the larger circle which touches the "
                "smaller circle.") == "8"


def test_ring_area_control():
    assert "125.664" in _ans(
        "Find the area between two concentric circles "
        "of radii 7 cm and 3 cm.")


# --- trig ----------------------------------------------------------
def test_theta_identity_true():
    assert _ans("Prove that sin^2 theta + cos^2 theta "
                "= 1.") == "Identity verified ✔"


def test_theta_identity_false():
    assert _ans("Prove that sin^2 theta + cos^2 theta "
                "= 2.") == "Not an identity"


def test_sqrt_ratio_angle():
    assert _ans("If cos theta = sqrt(3)/2, find theta.") \
        == "θ = 30°"


def test_sqrt_ratio_other_ratios():
    a = _ans("If cos theta = sqrt(3)/2, find sin theta "
             "and tan theta.")
    assert "1/2" in a and "sqrt(3)/3" in a


def test_ratio_control():
    assert _ans("If sin A = 3/5, find cos A.") \
        == "cos A = 4/5"


# --- calculus ------------------------------------------------------
def test_ode_prose():
    assert _ans("Solve the differential equation "
                "dy/dx = 2x.") == "y = C1 + x^2"


def test_conic_tangent_circle():
    # Merge-3: Wave 52's conic block (kept for the standard
    # forms) presents the tangent in the app's house format
    # "3·x + 4·y = 25" — asserted exactly by Wave 52's tests;
    # Wave 58's general block covers the other conics.
    assert _ans("Find the equation of the tangent to "
                "the circle x^2 + y^2 = 25 at the point "
                "(3, 4).") == "3·x + 4·y = 25"


def test_conic_normal_parabola():
    assert _ans("Find the equation of the normal to "
                "the parabola y^2 = 4x at the point "
                "(1, 2).") == "x + y = 3"


def test_conic_tangent_ellipse():
    assert _ans("Find the equation of the tangent to "
                "the ellipse x^2/25 + y^2/9 = 1 at the "
                "point (3, 12/5).") == "9x + 20y = 75"


def test_conic_off_point_refused():
    assert not _exact(
        "Find the equation of the tangent to the circle "
        "x^2 + y^2 + 4x - 2y - 8 = 0 at the point (2, 2).")


def test_conic_both_lines():
    a = _ans("Find the equations of the tangent and "
             "normal to the circle x^2 + y^2 = 25 at the "
             "point (3, 4).")
    assert "3x + 4y = 25" in a and "4x - 3y = 0" in a
