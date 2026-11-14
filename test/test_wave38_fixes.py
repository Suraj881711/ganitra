"""Wave 38 (15 Nov 2026): solver fixes from the Wave 35
audit top-15 backlog.

1. SUM/DIFFERENCE SYSTEMS. "If a + b = 10 and a - b = 4,
   find a and b" returned complex garbage in f and I — the
   generic system solver split the sentence on "and" and fed
   ", find a" to the expression parser (audit #62-65; the
   Hindi form #471 never parsed). algebra._solve_two_linear
   now reads exactly two linear equations in the same two
   single-letter unknowns straight from the raw question
   (EN + Hindi), and algebra._identity_value covers the
   a±b / ab identity asks (#100).
2. GP HIJACKED BY AP. _classify reads any two-term series
   as an AP, so "8th term of the GP 3, 6, ..." answered 24
   instead of 384 (#117-119). The student's explicit GP/AP
   label now wins; word-stated parameters ("first term is 4,
   common ratio is 3") parse; GP sum-to-infinity added.
3. BINOMIAL. "Exactly 3 heads in 5 coin tosses" counted the
   favourable outcomes of ONE toss (answer 0, #311) because
   "tossed 5 times" never set the coin count; a repeated die
   ("a six exactly 2 times in 4 throws") got the single-throw
   1/6 (#313); binomial mean/variance ("mean 20, variance
   16, find n and p") answered 4 (#312). All three fixed,
   plus the bare-count event "getting two heads" (#227).
4. MISSING CHAPTERS. Pythagoras (0/6: hypotenuse, leg,
   rectangle/square diagonal, right-angle check EN + Hindi),
   integration (0/6: the word "integral" does not contain
   "integrat", so every "integral of ..." ask missed the
   integral block), profit/loss percent (0/10: buys/sells
   present tense, %-first SP form, "loses/gains" CP form,
   Hindi खरीदकर/बेची), complex numbers (0/5: "the" and the
   trailing full stop in the extracted expression broke the
   parse; "Multiply A by B"; "a + ib" routing).
5. HINDI SUMMARY IN MARATHI. langdetect treated the shared
   tatsama words गणित/प्रश्न/उत्तर/अभ्यास and the Hindi
   passive auxiliary जाते as distinctly Marathi, flipping
   plain Hindi questions ("सिक्के उछाले जाते हैं…") to
   Marathi. They no longer trigger the switch alone.
"""
from langdetect_local import detect_language_confident
from solver.router import solve_question


def _ans(q):
    return str(solve_question(q).get("answer", ""))


def _op(q):
    return solve_question(q).get("op")


# ---------------------------------------------------------- 1. systems
def test_sum_difference_system_all_audit_cases():
    assert _ans("If a + b = 10 and a - b = 4, find a and b.") \
        == "a = 7, b = 3"
    assert _ans("If a + b = 15 and a - b = 5, find a and b.") \
        == "a = 10, b = 5"
    assert _ans("If a + b = 20 and a - b = 6, find a and b.") \
        == "a = 13, b = 7"
    assert _ans("If a + b = 7 and a - b = 3, find a and b.") \
        == "a = 5, b = 2"


def test_sum_difference_system_hindi():
    assert _ans("यदि a + b = 8 और a - b = 2 हो तो a और b "
                "ज्ञात कीजिए।") == "a = 5, b = 3"


def test_system_with_coefficients():
    r = solve_question("Solve the pair of equations: "
                       "2x + 3y = 13 and x - y = 1.")
    assert r["solutions"] == ["16/5", "11/5"]
    assert _ans("Solve 3x + 2y = 12 and x + y = 5.") \
        == "x = 2, y = 3"


def test_system_other_letters_and_order():
    assert _ans("If p + q = 12 and p - q = 4, find p and q.") \
        == "p = 8, q = 4"
    assert _ans("If x - y = 3 and x + y = 11, find x and y.") \
        == "x = 7, y = 4"


def test_identity_value():
    assert _ans("If a - b = 4 and ab = 21, find a^2 + b^2.") \
        == "58"
    assert _ans("If a + b = 9 and ab = 20, find a^2 + b^2.") \
        == "41"
    assert _ans("If a - b = 4 and ab = 21, find (a + b)^2.") \
        == "100"


def test_single_equation_not_hijacked():
    assert _op("Solve x^2 - 5x + 6 = 0.") == "equation"
    assert _ans("Solve 2x + 3 = 11.") == "x = 4"


# ---------------------------------------------------------- 2. GP / AP
def test_gp_two_term_series_uses_ratio():
    assert _ans("Find the 8th term of the GP 3, 6, ...") == "384"
    assert _ans("Find the 6th term of the GP 5, 15, ...") == "1215"
    assert _ans("Find the 5th term of the GP 81, 27, ...") == "1"
    assert _ans("Find the 7th term of the GP 5, 10, 20, ...") \
        == "320"


def test_gp_word_parameters():
    assert _ans("In a GP, the first term is 4 and the common "
                "ratio is 3. Find the 5th term.") == "324"
    assert _ans("In an AP, the first term is 7 and the common "
                "difference is 3. Find the 12th term.") == "40"


def test_gp_sum_to_infinity():
    assert _ans("Find the sum to infinity of the GP "
                "8, 4, 2, 1, ...") == "16"
    assert _ans("Find the sum of the first 6 terms of the GP "
                "2, 6, 18, ...") == "728"


def test_ap_unchanged():
    assert _ans("Find the 10th term of the AP 2, 5, 8, ...") \
        == "29"
    assert _ans("Find the sum of the first 10 terms of the AP "
                "2, 5, 8, ...") == "155"


# ---------------------------------------------------------- 3. binomial
def test_coin_tossed_n_times_exactly_k_heads():
    assert _ans("A coin is tossed 5 times. What is the "
                "probability of getting exactly 3 heads?") \
        .startswith("5/16")
    assert _ans("A coin is tossed 3 times. What is the "
                "probability of getting exactly 2 heads?") \
        .startswith("3/8")


def test_two_coins_two_heads():
    assert _ans("Two coins are tossed simultaneously. What is "
                "the probability of getting two heads?") \
        .startswith("1/4")
    assert _ans("Two coins are tossed simultaneously. What is "
                "the probability of getting at most one head?") \
        .startswith("3/4")


def test_die_thrown_n_times_binomial():
    assert _ans("A die is thrown 4 times. What is the "
                "probability of getting a six exactly 2 "
                "times?").startswith("25/216")


def test_binomial_mean_variance():
    assert _ans("The mean of a binomial distribution is 20 "
                "and the variance is 16. Find n and p.") \
        == "n = 100, p = 0.2"
    assert _ans("A binomial distribution has n = 10 and "
                "p = 0.5. Find its mean and variance.") \
        == "Mean = 5, variance = 2.5"
    assert _op("Binomial n=10 p=0.5, P(X=5)") \
        == "binomial_probability"


def test_empirical_probability_unchanged():
    assert _ans("A coin is tossed 1000 times and head appears "
                "450 times. Find the probability of getting "
                "a head.").startswith("9/20")


# ---------------------------------------------------------- 4a. pythagoras
def test_pythagoras_hypotenuse_and_leg():
    assert _ans("Find the hypotenuse of a right triangle "
                "with legs 9 cm and 12 cm.") == "15"
    assert _ans("Find the hypotenuse of a right triangle "
                "with legs 5 cm and 12 cm.") == "13"
    assert _ans("A right triangle has hypotenuse 25 cm and "
                "one leg 7 cm. Find the other leg.") == "24"
    assert _ans("A right triangle has hypotenuse 10 cm and "
                "one leg 6 cm. Find the other leg.") == "8"


def test_pythagoras_diagonals():
    assert _ans("Find the diagonal of a rectangle with "
                "length 12 cm and breadth 5 cm.") == "13"
    assert _ans("Find the diagonal of a square with side "
                "5 cm.").startswith("√50")


def test_pythagoras_checks():
    assert _ans("Is a triangle with sides 6 cm, 8 cm and "
                "10 cm a right triangle?").startswith("Yes")
    assert _ans("किसी त्रिभुज की भुजाएँ 6 cm, 8 cm और 10 cm "
                "हैं। क्या यह समकोण त्रिभुज है?") \
        .startswith("Yes")


# ---------------------------------------------------------- 4b. integration
def test_integrate_with_respect_to():
    assert _ans("Integrate x^3 with respect to x.") \
        == "x^4/4 + C"
    assert _ans("Integrate sin x with respect to x.") \
        == "-cos(x) + C"
    assert _ans("Integrate 1/x with respect to x.") \
        == "log(x) + C"


def test_integral_of_phrasing():
    assert _ans("Find the integral of 2x + 3.") \
        == "x^2 + 3·x + C"


def test_definite_integrals():
    assert _ans("Evaluate the definite integral of x from "
                "0 to 2.") == "2"
    assert _ans("Evaluate the definite integral of x^2 from "
                "1 to 3.") == "26/3"
    assert _ans("Integrate x^2 from 0 to 1 and show the "
                "graph.") == "1/3"


# ---------------------------------------------------------- 4c. profit/loss
def test_profit_loss_percent_present_tense():
    assert _ans("A shopkeeper buys an article for Rs 500 and "
                "sells it for Rs 575. Find his profit "
                "percent.") == "15%"
    assert _ans("A shopkeeper buys an article for Rs 800 and "
                "sells it for Rs 720. Find his loss "
                "percent.") == "10%"
    assert _ans("A shopkeeper buys an article for Rs 1200 "
                "and sells it for Rs 1500. Find his profit "
                "percent.") == "25%"
    assert _ans("A shopkeeper buys an article for Rs 250 and "
                "sells it for Rs 200. Find his loss "
                "percent.") == "20%"


def test_profit_loss_percent_forms():
    assert _ans("A man sells an article at a loss of 15%. "
                "If the cost price is Rs 2000, find the "
                "selling price.") == "Rs 1700"
    assert _ans("By selling a watch for Rs 1275, a man loses "
                "15%. Find the cost price of the watch.") \
        == "Rs 1500"
    assert _ans("By selling a table for Rs 900, a man gains "
                "20%. Find the cost price.") == "Rs 750"


def test_profit_loss_hindi():
    assert _ans("एक वस्तु 800 रुपये में खरीदकर 1000 रुपये में "
                "बेची गई। लाभ प्रतिशत ज्ञात कीजिए।") == "25%"
    assert _ans("एक वस्तु 500 रुपये में खरीदकर 450 रुपये में "
                "बेची गई। हानि प्रतिशत ज्ञात कीजिए।") == "10%"
    assert _ans("ek vastu 250 me khareedi aur 300 me bechi, "
                "kitne pratishat ka laabh hua") == "20%"


def test_profit_loss_older_forms_unchanged():
    assert _ans("Ravi bought a cycle for Rs 1200 and sold it "
                "for Rs 1500. Find his profit.") \
        == "Profit of Rs 300"
    assert _ans("The cost price of an article is Rs 400 and "
                "the selling price is Rs 460. Find the "
                "profit percent.") == "15%"


# ---------------------------------------------------------- 4d. complex
def test_complex_basics():
    assert _ans("Find the modulus of 3 + 4i.") == "5"
    assert _ans("Find the modulus of 1 + i.") \
        == "sqrt(2) ≈ 1.4142"
    assert _ans("Multiply (1 + i) by (1 - i).") == "2"
    assert _ans("Express 1/i in the form a + ib.") == "-I"
    assert _op("Simplify (2 + 3i) + (4 - 5i).") == "evaluate"
    assert _ans("Simplify (2 + 3i) + (4 - 5i).") == "6 - 2·I"
    assert _ans("Find the conjugate of 3 - 2i.") == "3 + 2·I"


# ---------------------------------------------------------- 5. langdetect
def test_hindi_not_detected_as_marathi():
    assert detect_language_confident(
        "दो सिक्के उछाले जाते हैं। कम से कम एक चित आने की "
        "प्रायिकता क्या है?")[0] == "hi"
    assert detect_language_confident(
        "इस प्रश्न का उत्तर बताओ")[0] == "hi"
    assert detect_language_confident(
        "गणित का अभ्यास करो")[0] == "hi"


def test_marathi_still_detected():
    assert detect_language_confident(
        "मला हा प्रश्न समजत नाहीये, सांगा ना कसा "
        "करायचा")[0] == "mr"
    assert detect_language_confident(
        "हा प्रश्न सोडवा")[0] == "mr"
