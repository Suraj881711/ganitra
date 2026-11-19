"""Wave 193: Sets & Cartesian-product forms + the De Morgan
WRONG-SERVE fix (form audit item B.8, probes 23-24).

Probe 23 BEFORE: solve_sets read the first two brace groups
of "U = {1..9}, A = {2,4,6,8}, B = {2,3,5,7}, verify that
(A union B)' = A' intersection B'" as its A and B, intersected
them and served the fragment {2,4,6,8}.  Correct: both sides
compute to {1, 9}.  Probe 24 BEFORE: parse error.

Fix: solver/sets193.py — strict family schemas (identity
verify with both sides computed, direct complement
computations, ordered-pair equality, Cartesian products,
domain/range of a pair roster, decidable roster <->
set-builder conversions, whole-battery subset/membership
verdicts) behind a failure-only gate in router.py PLUS a
scoped displacement: a sets-typed primary serve is displaced
only when sets193 settles the same question completely with
a verifiably different answer.  Concept / why asks decline.
"""
from solver.router import solve_question
from solver.sets193 import solve_sets193

UAB = ("U = {1, 2, 3, 4, 5, 6, 7, 8, 9}, A = {2, 4, 6, 8} "
       "and B = {2, 3, 5, 7}")
PROBE23 = (f"If {UAB}, verify that (A union B)' = "
           f"A' intersection B'")
PROBE24 = "If (x + 1, y - 2) = (3, 1), find the values of x and y"


def routed(q):
    return solve_question(q)


def ans(q):
    out = routed(q)
    assert out is not None, q
    return out


def mod(q):
    out = solve_sets193(q)
    assert out is not None, q
    return out


def declines(q):
    assert solve_sets193(q) is None, q


# ---------------------------------------------------------------------------
# Probe 23: the De Morgan wrong serve, fixed
# ---------------------------------------------------------------------------

def test_probe23_demorgan_verify_fixed():
    out = ans(PROBE23)
    assert out["op"] == "w193_verify"
    # A union B = {2,3,4,5,6,7,8}; complement in U = {1, 9};
    # A' cap B' = {1,9}.  The old fragment serve was {2,4,6,8}.
    assert out["answer"] == "{1, 9}"
    joined = " ".join(out["steps"])
    assert "A ∪ B = {2, 3, 4, 5, 6, 7, 8}" in joined
    assert "A' ∩ B' = {1, 9}" in joined
    assert "verified" in joined


def test_probe23_symbol_dress():
    q = (f"If {UAB}, verify that (A ∪ B)' = A' ∩ B'")
    out = ans(q)
    assert out["op"] == "w193_verify"
    assert out["answer"] == "{1, 9}"


def test_demorgan_second_law():
    q = (f"If {UAB}, verify that (A intersection B)' = "
         f"A' union B'")
    out = ans(q)
    assert out["op"] == "w193_verify"
    # A cap B = {2}; complement = U - {2}; A' cup B' agrees.
    assert out["answer"] == "{1, 3, 4, 5, 6, 7, 8, 9}"


def test_verify_false_identity_serves_computed_verdict():
    q = (f"If {UAB}, verify that (A union B)' = A' union B'")
    out = ans(q)
    assert out["op"] == "w193_verify"
    # LHS = {1, 9} but A' union B' = {1,3,4,5,6,7,8,9}:
    # the identity does NOT hold for these sets, and the
    # serve must say so with both sides shown — never assert.
    assert "not equal" in out["answer"]
    assert "{1, 9}" in out["answer"]
    assert "{1, 3, 4, 5, 6, 7, 8, 9}" in out["answer"]


def test_verify_distributive_law():
    q = ("If U = {1, 2, 3, 4, 5, 6}, A = {1, 2, 3}, "
         "B = {2, 3, 4} and C = {3, 4, 5}, verify that "
         "A intersection (B union C) = (A intersection B) "
         "union (A intersection C)")
    out = ans(q)
    assert out["op"] == "w193_verify"
    assert out["answer"] == "{2, 3}"


def test_verify_double_complement():
    q = f"If {UAB}, verify that (A')' = A"
    out = ans(q)
    assert out["op"] == "w193_verify"
    assert out["answer"] == "{2, 4, 6, 8}"


def test_direct_complement_computation():
    out = ans(f"If {UAB}, find (A union B)'")
    assert out["op"] == "w193_set_compute"
    assert out["answer"] == "{1, 9}"


def test_direct_complement_of_intersection():
    out = ans(f"If {UAB}, find (A intersection B)'")
    assert out["answer"] == "{1, 3, 4, 5, 6, 7, 8, 9}"


def test_direct_single_complement():
    q = ("If U = {1, 2, 3, 4, 5, 6, 7, 8, 9}, "
         "A = {2, 4, 6, 8}, find A'")
    out = ans(q)
    assert out["op"] == "w193_set_compute"
    assert out["answer"] == "{1, 3, 5, 7, 9}"


def test_verify_without_universal_declines():
    # Complement with no U given is undecidable here.
    declines("If A = {1, 2} and B = {2, 3}, verify that "
             "(A union B)' = A' intersection B'")


# ---------------------------------------------------------------------------
# Probe 24 + ordered-pair equality family
# ---------------------------------------------------------------------------

def test_probe24_ordered_pair():
    out = ans(PROBE24)
    assert out["op"] == "w193_ordered_pair"
    assert out["answer"] == "x = 2, y = 3"


def test_ordered_pair_system_variant():
    # (x + y, x - y) = (5, 1): adding gives 2x = 6.
    out = ans("If (x + y, x - y) = (5, 1), find x and y")
    assert out["op"] == "w193_ordered_pair"
    assert out["answer"] == "x = 3, y = 2"


def test_ordered_pair_fraction_variant():
    # NCERT Ex 2.1 dress: (x/3 + 1, y - 2/3) = (5/3, 2/3).
    out = ans("If (x/3 + 1, y - 2/3) = (5/3, 2/3), "
              "find the values of x and y")
    assert out["op"] == "w193_ordered_pair"
    assert out["answer"] == "x = 2, y = 4/3"


def test_ordered_pair_inconsistent_declines():
    declines("If (x + 1, 5) = (3, 7), find x")


def test_ordered_pair_nonlinear_declines():
    declines("If (x^2, y) = (4, 1), find x and y")


# ---------------------------------------------------------------------------
# Cartesian products
# ---------------------------------------------------------------------------

def test_cartesian_list():
    out = ans("If A = {1, 2, 3} and B = {3, 4}, find A x B")
    assert out["op"] == "w193_cartesian_list"
    assert out["answer"] == ("{(1, 3), (1, 4), (2, 3), "
                             "(2, 4), (3, 3), (3, 4)}")


def test_cartesian_word_dress():
    out = ans("If A = {1, 2} and B = {3, 4}, find the "
              "cartesian product of A and B")
    assert out["op"] == "w193_cartesian_list"
    assert out["answer"] == "{(1, 3), (1, 4), (2, 3), (2, 4)}"


def test_cartesian_count():
    out = ans("If A = {1, 2} and B = {3, 4, 5}, how many "
              "elements are there in A x B?")
    assert out["op"] == "w193_cartesian_count"
    assert out["answer"] == "6"


def test_cartesian_product_of_intersection():
    # NCERT Ex 2.1: B cap C is empty, so the product is empty.
    out = ans("Let A = {1, 2}, B = {1, 2, 3, 4}, C = {5, 6}. "
              "Find A x (B intersection C)")
    assert out["op"] == "w193_cartesian_list"
    assert out["answer"] == "{}"


def test_cartesian_product_of_union():
    out = ans("Let A = {1, 2}, B = {1, 2, 3, 4}, C = {5, 6}. "
              "Find A x (B union C)")
    assert out["op"] == "w193_cartesian_list"
    assert out["answer"] == (
        "{(1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), "
        "(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6)}")


def test_cartesian_triple_count():
    out = ans("If P = {1, 3}, find the number of elements "
              "in P x P x P")
    assert out["op"] == "w193_cartesian_count"
    assert out["answer"] == "8"


def test_cartesian_triple_list():
    out = mod("If P = {1, 2}, find P x P x P")
    assert out["op"] == "w193_cartesian_list"
    assert out["answer"] == (
        "{(1, 1, 1), (1, 1, 2), (1, 2, 1), (1, 2, 2), "
        "(2, 1, 1), (2, 1, 2), (2, 2, 1), (2, 2, 2)}")


def test_cartesian_count_given_variant():
    out = mod("If A x B has 6 elements and A has 2 elements, "
              "find n(B)")
    assert out["op"] == "w193_cartesian_count"
    assert out["answer"] == "3"


def test_cartesian_count_given_inexact_declines():
    declines("If A x B has 7 elements and A has 2 elements, "
             "find n(B)")


# ---------------------------------------------------------------------------
# Domain & range of a relation roster
# ---------------------------------------------------------------------------

def test_domain_range_roster():
    out = ans("Find the domain and range of the relation "
              "R = {(1, 2), (2, 3), (3, 4)}")
    assert out["op"] == "w193_domain_range"
    assert out["answer"] == ("Domain = {1, 2, 3}, "
                             "Range = {2, 3, 4}")


def test_domain_range_repeated_components():
    out = mod("Find the domain and range of R = "
              "{(1, 2), (1, 3), (2, 3)}")
    assert out["answer"] == ("Domain = {1, 2}, Range = {2, 3}")


def test_domain_only():
    out = mod("Find the domain of the relation "
              "R = {(2, 5), (3, 6)}")
    assert out["answer"] == "Domain = {2, 3}"


def test_codomain_from_to_dress():
    out = mod("R is a relation from A = {1, 2, 3} to "
              "B = {4, 5, 6} where R = {(1, 4), (2, 5)}. "
              "Find the domain, range and codomain of R")
    assert out["op"] == "w193_domain_range"
    assert "Codomain = {4, 5, 6}" in out["answer"]
    assert "Domain = {1, 2}" in out["answer"]
    assert "Range = {4, 5}" in out["answer"]


def test_codomain_without_from_to_declines():
    # A bare roster cannot give a codomain — partial serve
    # is refused.
    declines("Find the domain, range and codomain of "
             "R = {(1, 4), (2, 5)}")


def test_rule_relation_declines():
    declines("Find the domain and range of the relation "
             "R = {(x, y) : y = 2x + 1}")


# ---------------------------------------------------------------------------
# Roster <-> set-builder conversions (decidable only)
# ---------------------------------------------------------------------------

def test_builder_to_roster_natural_less_than():
    out = ans("Write the set {x : x is a natural number "
              "less than 5} in roster form")
    assert out["op"] == "w193_roster_from_builder"
    assert out["answer"] == "{1, 2, 3, 4}"


def test_builder_to_roster_integer_range():
    out = mod("Write the set {x : x is an integer and "
              "-3 <= x < 7} in roster form")
    assert out["answer"] == "{-3, -2, -1, 0, 1, 2, 3, 4, 5, 6}"


def test_builder_to_roster_even():
    out = mod("Write {x : x is an even natural number less "
              "than 10} in roster form")
    assert out["answer"] == "{2, 4, 6, 8}"


def test_builder_to_roster_prime():
    out = mod("Write {x : x is a prime number less than 20} "
              "in roster form")
    assert out["answer"] == "{2, 3, 5, 7, 11, 13, 17, 19}"


def test_builder_to_roster_squares():
    out = mod("Write {x : x is the square of a natural "
              "number and x < 30} in roster form")
    assert out["answer"] == "{1, 4, 9, 16, 25}"


def test_builder_to_roster_multiple():
    out = mod("Write {x : x is a multiple of 3 and x < 20} "
              "in roster form")
    assert out["answer"] == "{3, 6, 9, 12, 15, 18}"


def test_builder_undecidable_declines():
    declines("Write {x : x is a natural number less than 5 "
             "and x is not divisible by 2} in roster form")
    declines("Write {x : x is a real number less than 5} "
             "in roster form")
    declines("Write {x : x is a natural number} in roster "
             "form")


def test_roster_to_builder_naturals():
    out = ans("Write {1, 2, 3, 4, 5} in set-builder form")
    assert out["op"] == "w193_builder_from_roster"
    assert out["answer"] == ("{x : x is a natural number "
                             "less than 6}")


def test_roster_to_builder_evens():
    out = mod("Write the set {2, 4, 6, 8, 10} in "
              "set-builder form")
    assert out["answer"] == ("{x : x is an even natural "
                             "number and 2 ≤ x ≤ 10}")


def test_roster_to_builder_squares():
    out = mod("Write {1, 4, 9, 16, 25} in set-builder form")
    assert out["answer"] == ("{x : x is the square of a "
                             "natural number and x ≤ 25}")


def test_roster_to_builder_unpatterned_declines():
    declines("Write {2, 3, 5, 9} in set-builder form")


def test_interval_to_builder():
    out = mod("Write the interval [-2, 5) in set-builder "
              "form")
    assert out["op"] == "w193_interval"
    assert out["answer"] == "{x : -2 ≤ x < 5}"


def test_builder_to_interval():
    out = mod("Write {x : 2 < x <= 7} in interval form")
    assert out["op"] == "w193_interval"
    assert out["answer"] == "(2, 7]"


def test_vowels_roster():
    out = ans("Write the set of all vowels in the English "
              "alphabet in roster form")
    assert out["answer"] == "{a, e, i, o, u}"


def test_letters_of_word_roster():
    out = mod("Write the set of letters in the word "
              "'BETTER' in roster form")
    assert out["answer"] == "{B, E, R, T}"


def test_described_even_set_roster():
    out = mod("Write the set of all even natural numbers "
              "less than 8 in roster form")
    assert out["answer"] == "{2, 4, 6}"


# ---------------------------------------------------------------------------
# Subset / membership batteries
# ---------------------------------------------------------------------------

BATTERY = ("If A = {1, 2, 3, 4, 5} and B = {2, 4, 6}, state "
           "whether each of the following statements is true "
           "or false: (i) 3 ∈ A (ii) 6 ∈ A (iii) {2, 4} ⊆ B "
           "(iv) B ⊂ A (v) 5 ∉ B")


def test_battery_all_verdicts():
    out = mod(BATTERY)
    assert out["op"] == "w193_battery"
    assert out["answer"] == "True, False, True, False, True"


def test_battery_with_undecidable_tail_declines():
    # A half-answered battery is a fragment serve — the
    # extra undecidable statement sinks the whole question.
    declines(BATTERY + " (vi) A is a finite set")


def test_battery_with_undefined_set_declines():
    declines("If A = {1, 2, 3}, state whether the following "
             "are true or false: (i) 2 ∈ A (ii) {1} ⊆ X")


def test_single_subset_word_dress():
    out = mod("If A = {1, 2, 3, 4}, is {1, 2} a subset of A?")
    assert out["op"] == "w193_battery"
    assert out["answer"] == "True"


def test_single_element_word_dress():
    out = mod("If A = {1, 2, 3}, is 5 an element of A?")
    assert out["answer"] == "False"


# ---------------------------------------------------------------------------
# Controls — pre-existing behaviour must not move
# ---------------------------------------------------------------------------

def test_control_plain_union_unchanged():
    out = routed("Find A union B if A = {1, 2, 3} and "
                 "B = {3, 4, 5}")
    assert out["op"] == "union"
    assert out["answer"] == "{1, 2, 3, 4, 5}"


def test_control_plain_intersection_unchanged():
    out = routed("A = {1, 2, 3}, B = {2, 3, 4}, find A "
                 "intersection B")
    assert out["op"] == "intersection"
    assert out["answer"] == "{2, 3}"


def test_control_subset_count_unchanged():
    out = routed("A set has 5 elements, how many subsets "
                 "does it have?")
    assert out["answer"] == "32"


def test_concept_asks_decline_in_module():
    declines("What is a set?")
    declines("Define subset")
    declines("What is a cartesian product?")
    declines("What is the difference between a set and a "
             "subset?")


def test_why_question_declines_in_module():
    # Wave 192 lesson: a why-question that merely mentions
    # decidable objects must never be settled by a schema.
    declines("Why is {1, 2} a subset of {1, 2, 3}?")
    declines("Why is 3 ∈ A if A = {1, 2, 3}?")


def test_concept_with_explicit_sets_still_declines():
    # Sets are given, but the ask is a concept ask, not a
    # verify / compute / product dress.
    declines("If A = {1, 2} and B = {3, 4}, what is a "
             "cartesian product?")
