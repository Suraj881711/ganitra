"""Wave 188: probability WORD dress + probability-
distribution mean/variance WRONG-SERVE fix (form-audit
top-10 item #3; audit rows 13, 14, 31; spot-check probes
20, 21, 22, 30).

BEFORE (measured on main, Deploy-46 state):
- Probe 20 "Compute P(A|B), if P(B) = 0.5 and P(A
  intersection B) = 0.32" -> statistics guide (MISS).
- Probe 21 (hosteller / day-scholar Bayes in prose) ->
  statistics guide (MISS).
- Probe 22 "X = 0, 1, 2 with P(X) = 0.2, 0.5, 0.3, find
  the mean of X" -> served **1** (plain mean of the
  values) instead of Σx·P(x) = **1.1** (WRONG SERVE);
  the variance dress served 0.452222 instead of 0.49,
  and the linearised table dress served 0.666667
  instead of 1.3.

Fix: solver/probwords188.py — (a) a wording
normalisation into the probability-relations triangle
(P(A), P(B), P(A∩B)) depth125 computes symbolically,
(b) Bayes schemas for the sentence dresses (residence
groups, factories/machines with % shares, bags with
ball counts), (c) a strict distribution sentence/table
schema (probabilities must sum to exactly 1) wired as a
failure-only gate AND as a verified-difference repair
for the statistics mean/variance/std hijack.  Every
expected value below was verified by hand before
pinning.
"""
from solver.probwords188 import (repair_probwords188,
                                 solve_probwords188)
from solver.router import solve_question

P20 = ("Compute P(A|B), if P(B) = 0.5 and "
       "P(A intersection B) = 0.32")
P21 = ("Of the students in a college, 60% reside in "
       "hostel and 40% are day scholars. 30% of all "
       "students who reside in hostel attain A grade and "
       "20% of day scholars attain A grade. A student is "
       "chosen at random and is found to have attained "
       "A grade. What is the probability that the "
       "student is a hosteller?")
P22 = ("A random variable X has the following "
       "probability distribution: X = 0, 1, 2 with "
       "P(X) = 0.2, 0.5, 0.3. Find the mean of X")
P30 = "If P(B) = 0.5 and P(A∩B) = 0.32, find P(A|B)"


def ans(q):
    out = solve_question(q)
    assert out is not None, q
    return out["answer"]


def mod(q):
    out = solve_probwords188(q)
    assert out is not None, q
    return out


# ------------------------------------------------------------------
# Probe 20 + the word-dress relations family
# ------------------------------------------------------------------

def test_probe20_word_conditional():
    # 0.32 / 0.5 = 0.64
    assert ans(P20) == "16/25 ≈ 0.6400"


def test_word_union_row31():
    # 0.54 + 0.69 - 0.35 = 0.88
    assert ans("P(A) = 0.54, P(B) = 0.69 and "
               "P(A intersection B) = 0.35. "
               "Find P(A union B)") == "22/25 ≈ 0.8800"


def test_word_intersection_via_union():
    # 0.3 + 0.6 - 0.7 = 0.2
    assert ans("Given P(A) = 0.3, P(B) = 0.6 and "
               "P(A union B) = 0.7, find "
               "P(A intersection B)") == "1/5 ≈ 0.2000"


def test_word_conditional_reversed():
    # 0.28 / 0.4 = 0.7
    assert ans("Compute P(B|A), if P(A) = 0.4 and "
               "P(A intersection B) = 0.28") == \
        "7/10 ≈ 0.7000"


def test_word_complement():
    # 1 - 0.54 = 0.46
    assert ans("If P(A) = 0.54, find P(not A)") == \
        "23/50 ≈ 0.4600"


def test_symbol_prime_complement():
    assert ans("If P(A) = 0.54, find P(A')") == \
        "23/50 ≈ 0.4600"


def test_word_not_a_and_not_b():
    # 1 - P(A union B) = 1 - 0.88 = 0.12
    assert ans("P(A) = 0.54, P(B) = 0.69, "
               "P(A ∩ B) = 0.35, find "
               "P(not A and not B)") == "3/25 ≈ 0.1200"


def test_word_a_but_not_b():
    # 0.54 - 0.35 = 0.19 (P(B) never given: only P(A)
    # and the intersection are needed)
    assert ans("P(A) = 0.54, P(A intersection B) = 0.35. "
               "Find P(A but not B)") == "19/100 ≈ 0.1900"
    assert ans("P(A) = 0.54, P(A intersection B) = 0.35. "
               "Find P(A and not B)") == "19/100 ≈ 0.1900"


def test_word_not_a_or_not_b():
    # 1 - P(A ∩ B) = 1 - 0.35 = 0.65
    assert ans("P(A) = 0.54, P(B) = 0.69, "
               "P(A ∩ B) = 0.35, find "
               "P(not A or not B)") == "13/20 ≈ 0.6500"


def test_word_union_with_complement_demorgan():
    # P(A ∪ B') = 1 - P(A' ∩ B) = 1 - (0.69 - 0.35) = 0.66
    assert ans("P(B) = 0.69, P(A ∩ B) = 0.35, find "
               "P(A union not B)") == "33/50 ≈ 0.6600"


def test_relations_hinglish_dress():
    assert ans("Agar P(B) = 0.5 aur "
               "P(A intersection B) = 0.32 hai, to "
               "P(A|B) kitna hoga?") == "16/25 ≈ 0.6400"


# ------------------------------------------------------------------
# Probe 21 + Bayes in sentence dress
# ------------------------------------------------------------------

def test_probe21_bayes_hosteller():
    # (0.6*0.3) / (0.6*0.3 + 0.4*0.2) = 0.18/0.26 = 9/13
    assert ans(P21) == "9/13 ≈ 0.6923"


def test_bayes_day_scholar_target():
    # 0.08 / 0.26 = 4/13
    q = P21.replace("is a hosteller?", "is a day scholar?")
    assert ans(q) == "4/13 ≈ 0.3077"


def test_bayes_three_factories():
    # joints .01 / .009 / .01, total .029 -> 9/29
    assert ans(
        "Factory A produces 50% of the items, factory B "
        "produces 30% of the items and factory C "
        "produces 20% of the items. 2% of items from "
        "factory A are defective, 3% of items from "
        "factory B are defective and 5% of items from "
        "factory C are defective. An item is chosen at "
        "random and is found to be defective. What is "
        "the probability that it came from factory B?") \
        == "9/29 ≈ 0.3103"


def test_bayes_two_machines():
    # joints .018 / .008, total .026 -> 4/13
    assert ans(
        "Machine A produces 60% of the items and "
        "machine B produces 40% of the items. 3% of "
        "items from machine A are defective and 2% "
        "from machine B are defective. An item is found "
        "defective. Find the probability it was "
        "produced by machine B.") == "4/13 ≈ 0.3077"


def test_bayes_bags_module():
    # (1/2 * 3/7) / (1/2 * 3/7 + 1/2 * 4/9) = 27/55
    out = mod("Bag I contains 3 red and 4 black balls, "
              "Bag II contains 4 red and 5 black balls. "
              "A bag is chosen at random and a ball is "
              "drawn from it, which is found to be red. "
              "What is the probability that it came from "
              "Bag I?")
    assert out["answer"] == "27/55 ≈ 0.4909"


def test_bayes_unparseable_declines():
    # priors + target but NO rates: a guess would be
    # needed, so the schema declines
    assert solve_probwords188(
        "Of the students in a college, 60% reside in "
        "hostel and 40% are day scholars. A student is "
        "chosen at random. What is the probability "
        "that the student is a hosteller?") is None


# ------------------------------------------------------------------
# Probe 22: the distribution WRONG SERVE, fixed
# ------------------------------------------------------------------

def test_probe22_mean_wrong_serve_fixed():
    out = solve_question(P22)
    assert out["op"] == "distribution_mean"
    assert out["answer"] == "Mean = 1.1"


def test_probe22_variance_wrong_serve_fixed():
    # E(X^2) = 1.7; Var = 1.7 - 1.1^2 = 0.49
    q = P22.replace("mean", "variance")
    out = solve_question(q)
    assert out["op"] == "distribution_variance"
    assert out["answer"] == "Variance = 0.49"


def test_probe22_sd():
    q = P22.replace("Find the mean of X",
                    "Find the standard deviation of X")
    out = solve_question(q)
    assert out["op"] == "distribution_sd"
    assert out["answer"] == "Standard deviation = 0.7"


def test_distribution_mean_and_variance_combined():
    q = P22.replace("Find the mean of X",
                    "Find the mean and variance of X")
    out = solve_question(q)
    assert out["answer"] == "Mean = 1.1, Variance = 0.49"


def test_distribution_expected_value_dress():
    # 1*0.2 + 2*0.3 + 4*0.5 = 2.8
    assert ans("A random variable X has the following "
               "probability distribution: X = 1, 2, 4 "
               "with P(X) = 0.2, 0.3, 0.5. Find E(X)") \
        == "Mean = 2.8"


def test_distribution_fraction_probs():
    # 0*(1/2) + 1/6 + 2/6 + 3/6 = 1
    assert ans("A random variable X has the following "
               "probability distribution: X = 0, 1, 2, 3 "
               "with P(X) = 1/2, 1/6, 1/6, 1/6. Find "
               "the mean of X") == "Mean = 1"


def test_distribution_table_dress_mean():
    # linearised book dress: 0*0.2 + 1*0.3 + 2*0.5 = 1.3
    assert ans("A random variable X has the following "
               "probability distribution : X 0 1 2 "
               "P (X) 0.2 0.3 0.5 Find the mean of the "
               "distribution.") == "Mean = 1.3"


def test_distribution_table_dress_variance():
    # E(X^2) = 2.3; Var = 2.3 - 1.3^2 = 0.61
    assert ans("A random variable X has the following "
               "probability distribution : X 0 1 2 "
               "P (X) 0.2 0.3 0.5 Find the variance of "
               "the distribution.") == "Variance = 0.61"


def test_distribution_invalid_probs_decline():
    # 0.2 + 0.5 + 0.4 = 1.1 != 1: not a distribution,
    # the schema must decline rather than guess
    assert solve_probwords188(
        "A random variable X has the following "
        "probability distribution: X = 0, 1, 2 with "
        "P(X) = 0.2, 0.5, 0.4. Find the mean of X") \
        is None


def test_distribution_k_table_declines():
    # probabilities in k cannot be settled by this
    # schema (tierA169 owns k-tables for P-asks)
    assert solve_probwords188(
        "A random variable X has the following "
        "probability distribution : X 0 1 2 3 4 5 6 7 "
        "P (X ) 0 k 2k 2k 3k k 2 2k2 7k2 + k Find "
        "the mean.") is None


def test_repair_never_displaces_a_correct_serve():
    # symmetric distribution: plain mean == weighted
    # mean (1.5), so the repair must stand down
    q = ("A random variable X has the following "
         "probability distribution: X = 0, 1, 2, 3 with "
         "P(X) = 1/6, 1/3, 1/3, 1/6. Find the mean of X")
    served = {"type": "statistics", "op": "mean",
              "answer": "1.5", "value": 1.5, "steps": []}
    assert repair_probwords188(q, served) is None
    out = solve_question(q)
    assert out["answer"] == "1.5"


def test_repair_only_for_statistics_stat_ops():
    q = P22
    served = {"type": "arithmetic", "op": "mean",
              "answer": "1", "value": 1, "steps": []}
    assert repair_probwords188(q, served) is None


# ------------------------------------------------------------------
# Controls — must stay exactly as they were
# ------------------------------------------------------------------

def test_control_probe30_symbolic_byte_identical():
    out = solve_question(P30)
    assert out["op"] == "probability"
    assert out["answer"] == "16/25 ≈ 0.6400"


def test_control_row31_symbolic_unchanged():
    assert ans("P(A) = 0.54, P(B) = 0.69, "
               "P(A ∩ B) = 0.35, find P(A ∪ B)") == \
        "P(A or B) = 0.88"


def test_control_plain_mean_unchanged():
    out = solve_question("find the mean of 2, 4, 6")
    assert out["op"] == "mean"
    assert out["answer"] == "4"


def test_control_dice_probability_unchanged():
    assert ans("what is the probability of getting a 6 "
               "on a dice") == "1/6 ≈ 0.1667"


def test_control_tierA169_table_unchanged():
    assert ans("A random variable X has the following "
               "probability distribution : X 0 1 2 3 4 "
               "5 6 7 P (X ) 0 k 2k 2k 3k k 2 2k2 7k2 + "
               "k Determine : (i) k (ii) P (X < 3) "
               "(iii) P ( X > 4)") == \
        "k = 1/10; P(X < 3) = 3/10; P(X > 4) = 1/5"
