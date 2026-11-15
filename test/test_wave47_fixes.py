"""Wave 47 (15 Nov 2026): solver coverage round 3 — the
Wave 38 left-open list (Wave 35 audit #6, #10-#14) plus
battery #123.

1. STATISTICS WORD PROBLEMS (audit #6). The wrongly-
   recorded-mean form ("mean 25, 36 recorded as 63") had
   no pattern and answered with the plain mean (#218);
   the included-person form ("teacher's weight included,
   mean becomes...") likewise (#225); and a colon-
   introduced data list fed the stated count ("of 15
   students") into the median as a data point (#223).
2. COMBINED SOLIDS (audit #10). Cylinder+cone with the
   cone's height stated after the cone's name now reads
   both heights (#206); hemisphere combinations
   (cylinder+hemisphere, cone+hemisphere, diameter-stated
   toy) are new volume patterns.
3. TRAIN / WORK HIJACKS (audit #11). "Train crosses a
   platform, find the train's length" fell into the
   crossing-pattern that needed the train's length as an
   input (#263); "together in T days, A alone in A days,
   B alone?" had no pattern (#259).
4. FACTOR COUNTS (audit #12). "How many factors does N
   have" was unanswered; tau(n) from the prime
   factorisation (#314-#317).
5. TRIGONOMETRY (audit #13/#14). "Find the value of
   theta" / "find A" after a given ratio now returns the
   angle itself (#160, #163) instead of another ratio;
   a sum of two asked ratios (cos A + tan A) is evaluated
   (#443); the identity verifier no longer chokes on the
   filler word "that" or the trailing full stop that
   turned sec^2 into sec^2.0 (#161); chains of three
   arctan terms fold pairwise with the pi correction
   (#180).
6. SEQUENCES (#123). GP sum+product of the first three
   terms: a/r, a, ar gives a^3 = P and r + 1/r = S/a - 1.
7. CALCULUS (audit #14 + #268). "Find the derivative
   of ..." kept its "Find the" lead-in and errored
   (#268, #270); a bare e is Euler's number in e^...
   (#269); trig derivatives display in textbook form
   (sec^2, -csc^2 — #379); "dy/dx if y = ..." is plain
   differentiation and must run before the ODE block
   (#272); limits in words ("limit of ... as x tends
   to ...", #273/#275/#276) and the "Evaluate lim x->2"
   lead-in (#274); rate of change of named quantities
   and of a general expression (#383); slope/equation of
   tangent and normal; maximum/minimum value of f(x)
   (#285/#286).

Measured: built on a Waves 1-38 copy, the 515-question
Wave 35 battery moves EXACT 301 -> 329, FALLBACK
168 -> 156, WRONG 46 -> 30, ERROR 0 -> 0 with ZERO
per-item regressions; rebased onto the merged Waves
39-46 tree (the merge landed mid-task) it moves
308 -> 335 EXACT with ZERO regressions again (#161 was
already fixed there by Wave 42; Wave 47's identity
contribution on the merged base is the trailing-dot
strip the sec^2 form still needed).
"""
from solver.router import solve_question


def _ans(q):
    return str(solve_question(q).get("answer", ""))


def _op(q):
    return solve_question(q).get("op")


# ------------------------------------------------- 1. statistics words
def test_wrongly_recorded_mean():
    assert _op("The mean of 10 observations is 25. If one "
               "observation 36 was wrongly recorded as 63, "
               "find the correct mean.") == \
        "mean_wrongly_recorded"
    assert _ans("The mean of 10 observations is 25. If one "
                "observation 36 was wrongly recorded as 63, "
                "find the correct mean.") == "22.3"


def test_included_person_weight():
    assert _ans("The mean weight of 8 students is 50 kg. "
                "When the teacher's weight is included, "
                "the mean becomes 52 kg. Find the "
                "teacher's weight.") == "68 kg"


def test_median_colon_list_ignores_stated_count():
    assert _ans("The marks of 15 students are: 41, 39, 48, "
                "52, 46, 62, 54, 40, 96, 52, 98, 40, 42, "
                "52, 60. Find the median.") == "52"


def test_statistics_neighbours_unchanged():
    assert _ans("Find the mean of 2, 4, 6, 8, 10.") == "6"
    assert _ans("Find the median of 3, 1, 4, 1, 5, 9, 2.") \
        == "3"


# ---------------------------------------------------- 2. combined solids
def test_cylinder_cone_heights_after_names():
    a = _ans("A solid consists of a cylinder of radius "
             "4 cm and height 6 cm with a cone of the same "
             "radius and height 3 cm on top. Find the "
             "total volume.")
    assert "351.858" in a


def test_cylinder_hemisphere_volume():
    a = _ans("A solid consists of a cylinder of radius "
             "3 cm and height 7 cm with a hemisphere of "
             "the same radius on top. Find the total "
             "volume.")
    assert "254.469" in a


def test_cone_hemisphere_volume():
    a = _ans("A solid consists of a cone of radius 3 cm "
             "and height 4 cm with a hemisphere of the "
             "same radius on top. Find the total volume.")
    assert "94.2478" in a


def test_plain_hemisphere_unchanged():
    a = _ans("Find the volume of a hemisphere of radius "
             "7 cm.")
    assert "718.378" in a


# ------------------------------------------------------ 3. train / work
def test_train_length_from_platform_crossing():
    assert _op("A train crosses a platform 180 m long in "
               "15 seconds travelling at 60 km/h. Find "
               "the length of the train.") == "train_length"
    assert _ans("A train crosses a platform 180 m long "
                "in 15 seconds travelling at 60 km/h. "
                "Find the length of the train.") == "70 m"


def test_work_together_and_solo():
    assert _ans("A and B together can do a work in 8 "
                "days. A alone can do it in 12 days. In "
                "how many days can B alone do it?") == \
        "24 days"


def test_work_neighbours_unchanged():
    assert "20/3" in _ans(
        "A can do a work in 12 days and B can do it in "
        "15 days. How long will they take together?")
    assert _ans("A train 240 m long crosses a pole in "
                "12 seconds. Find the speed of the train "
                "in km/h.") == "72 km/h"


# ------------------------------------------------------ 4. factor counts
def test_factor_counts():
    assert _ans("How many factors does 36 have?") == "9"
    assert _ans("How many factors does 48 have?") == "10"
    assert _ans("How many factors does 27 have?") == "4"
    assert _ans("How many factors does 100 have?") == "9"
    assert _ans("How many factors does 720 have?") == "30"
    assert _op("How many factors does 36 have?") == \
        "factor_count"


def test_number_theory_neighbours_unchanged():
    assert _ans("Find the HCF of 12 and 18.") == "6"
    assert _ans("Is 29 a prime number?") in (
        "Yes, 29 is prime", "29 is prime", "Yes")


# ------------------------------------------------------------ 5. trig
def test_inverse_angle_asks():
    assert _ans("If sin theta = 1/2, find the value of "
                "theta in degrees.") == "θ = 30°"
    assert _ans("If tan A = 1, find the value of A in "
                "degrees.") == "A = 45°"
    assert _op("If sin theta = 1/2, find the value of "
               "theta in degrees.") == "inverse_angle"


def test_ratio_ask_still_ratio_not_angle():
    # Wave 33 contract: "find the value of tan theta"
    # asks for the RATIO, never the angle.
    assert _ans("If sin theta = 3/5, find the value of "
                "tan theta.") == "tan θ = 3/4"
    assert _ans("If sin A = 3/5, find cos A.") == \
        "cos A = 4/5"


def test_ratio_sum():
    assert _ans("If sin A = 1/2 and A is acute, find "
                "cos A + tan A.") == "5·sqrt(3)/6"


def test_identity_verifier():
    assert _ans("Prove that sin^2 A + cos^2 A = 1.") == \
        "Identity verified ✔"
    assert _ans("Prove that tan^2 A + 1 = sec^2 A.") == \
        "Identity verified ✔"
    assert _ans("Prove that sin^2 A = cos^2 A.") == \
        "Not an identity"


def test_arctan_chain_and_pair_contract():
    assert _ans("Evaluate tan^-1(1) + tan^-1(2) + "
                "tan^-1(3).") == "pi"
    # Wave 32 contract stays: the pair form is kept.
    assert "atan(3)" in _ans(
        "Evaluate tan^-1(1) + tan^-1(1/2).")


# ------------------------------------------------------- 6. GP sum+product
def test_gp_sum_product_ratio():
    r = solve_question("The sum of the first three terms "
                       "of a GP is 39 and their product "
                       "is 729. Find the common ratio.")
    assert r.get("op") == "gp_sum_product"
    assert r.get("answer") == "3 or 1/3"


def test_gp_sum_product_terms():
    assert _ans("The sum of the first three terms of a "
                "GP is 39 and their product is 729. Find "
                "the terms.") == "3, 9, 27"


# ------------------------------------------------------------ 7. calculus
def test_derivative_lead_in_hygiene():
    assert _ans("Find the derivative of sin x.") == \
        "cos(x)"
    assert _ans("Find the derivative of log x.") == "1/x"
    assert _ans("Find the derivative of x^5.") == "5·x^4"
    assert _ans("Differentiate sin x with respect to "
                "x.") == "cos(x)"


def test_derivative_euler_and_textbook_trig():
    assert _ans("Find the derivative of e^(3x).") == \
        "3·exp(3·x)"
    assert _ans("Find the derivative of tan x.") == \
        "sec(x)^2"
    assert _ans("Find the derivative of cot x.") == \
        "-csc(x)^2"


def test_dydx_if_is_plain_differentiation():
    assert _ans("Find dy/dx if y = (3x + 2)^5.") == \
        "15·(3·x + 2)^4"
    assert _ans("Find dy/dx if y = sin x.") == "cos(x)"


def test_limits_in_words_and_notation():
    assert _ans("Evaluate the limit of (x^2 - 9)/(x - 3) "
                "as x tends to 3.") == "6"
    assert _ans("Find the limit of sin x / x as x tends "
                "to 0.") == "1"
    assert _ans("Evaluate the limit of (2x^2 + 3x)/"
                "(x^2 - 1) as x tends to infinity.") == "2"
    assert _ans("Evaluate lim x->2 (x^3 - 8)/(x - 2).") \
        == "12"
    assert _ans("Evaluate lim x->0 sin(x)/x.") == "1"


def test_rate_of_change():
    assert _ans("Find the rate of change of the area of "
                "a circle with respect to its radius "
                "when r = 5 cm.") == "10·pi ≈ 31.4159"
    assert _ans("Find the rate of change of the volume "
                "of a sphere with respect to its radius "
                "when r = 3.") == "36·pi ≈ 113.097"
    assert _ans("Find the rate of change of x^3 with "
                "respect to x when x = 2.") == "12"
    assert _ans("Find the rate of change of the area of "
                "a circle with respect to its radius.") \
        == "2·pi·r"


def test_tangent_normal_basics():
    assert _ans("Find the slope of the tangent to the "
                "curve y = x^2 at x = 3.") == "6"
    assert _ans("Find the slope of the normal to the "
                "curve y = x^2 at x = 3.") == "-1/6"
    assert _ans("Find the equation of the tangent to "
                "the curve y = x^2 at x = 3.") == \
        "y = 6·x - 9"
    assert _ans("Find the equation of the normal to the "
                "curve y = x^2 at x = 3.") == \
        "y = 19/2 - x/6"


def test_maximum_minimum_value():
    assert _ans("Find the maximum value of the function "
                "f(x) = 2x^3 - 15x^2 + 36x + 1.") == "29"
    assert _ans("Find the minimum value of the function "
                "f(x) = x^3 - 3x^2 + 2.") == "-2"


def test_calculus_neighbours_unchanged():
    assert _ans("Find dy/dx for x^2 + y^2 = 25.") == "-x/y"
    assert _ans("Integrate sin x with respect to x.") == \
        "-cos(x) + C"
    assert _ans("Find the slope of the line joining "
                "(2, 3) and (5, 7).") == "1.33333"
