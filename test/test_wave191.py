"""Wave 191: Relations & Functions proof / classification
engine (form-audit top-10 item #6; audit rows 10-12).

The audit's probes 05 and 06 missed natively:

  05: "Show that the relation R in the set {1, 2, 3} given
      by R = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 3)} is
      reflexive but neither symmetric nor transitive"
      -> parse error.  Hand-check: reflexive YES (all
      (a, a) present); symmetric NO, witness (1, 2) in R,
      (2, 1) not in R; transitive NO, witness (1, 2),
      (2, 3) in R but (1, 3) not in R.
  06: "Let f : R -> R be defined as f(x) = x^4. Is f
      one-one or onto? (A)...(D) neither one-one nor onto"
      -> fell to a statistics guide.  Hand-check: (D) —
      f(-1) = f(1) = 1 (not one-one); -1 has no preimage
      (not onto).

Fix: solver/relations191.py behind a failure-only gate in
router.py after the Wave 175 block.  Every verdict is the
output of a mechanical check (exhaustive roster checks
with witnesses; per-form parity / monotonicity / range
arguments with verified witnesses; exact counting
formulas).  Unrecognised forms decline — a wrong verdict
is worse than a native miss.
"""
from solver.relations191 import solve_relations191
from solver.router import solve_question

PROBE05 = ("Show that the relation R in the set {1, 2, 3} "
           "given by R = {(1, 1), (2, 2), (3, 3), (1, 2), "
           "(2, 3)} is reflexive but neither symmetric nor "
           "transitive")
PROBE06 = ("Let f : R -> R be defined as f(x) = x^4. "
           "Is f one-one or onto? Choose: (A) one-one onto "
           "(B) many-one onto (C) one-one but not onto "
           "(D) neither one-one nor onto")


def ans(q):
    out = solve_relations191(q)
    assert out is not None, q
    return out


def declines(q):
    assert solve_relations191(q) is None, q


# ------------------------------------------------------------------
# Probe 05 — relation properties, roster dress
# ------------------------------------------------------------------

def test_probe05_schema():
    out = ans(PROBE05)
    assert out["op"] == "relation_properties"
    assert out["answer"] == ("R is reflexive but neither "
                             "symmetric nor transitive.")
    joined = " ".join(out["steps"])
    assert "(1, 2) is in R but (2, 1) is not in R" in joined
    assert "(1, 3) is not in R" in joined


def test_probe05_router():
    out = solve_question(PROBE05)
    assert out["op"] == "relation_properties"
    assert "neither symmetric nor transitive" in out["answer"]


def test_reflexive_false_with_witness():
    out = ans("Is the relation R = {(1,1),(2,2)} on the "
              "set {1,2,3} reflexive?")
    assert out["answer"] == "R is not reflexive."
    assert "(3, 3) is not in R" in " ".join(out["steps"])


def test_symmetric_true_transitive_false():
    out = ans("Show that R = {(1,1),(2,2),(3,3),(1,2),"
              "(2,1),(2,3),(3,2)} on A = {1,2,3} is "
              "symmetric but not transitive")
    assert "symmetric but not transitive" in out["answer"]
    assert "(1, 3) is not in R" in " ".join(out["steps"])


def test_equivalence_true_roster():
    out = ans("Check whether the relation R = {(1,1),(2,2),"
              "(3,3),(1,2),(2,1)} on the set {1,2,3} is an "
              "equivalence relation")
    assert "is an equivalence relation" in out["answer"]
    assert "not an equivalence" not in out["answer"]


def test_equivalence_false_roster():
    out = ans("Check whether R = {(1,1),(2,2),(3,3),(1,2)} "
              "on {1,2,3} is an equivalence relation")
    assert "not an equivalence relation" in out["answer"]


def test_transitive_only_asked():
    out = ans("Check whether R = {(1,1),(2,2),(3,3),(1,2)} "
              "on {1,2,3} is transitive")
    assert out["answer"] == "R is transitive."


def test_letter_set_equivalence():
    out = ans("Check whether R = {(a,a),(b,b),(c,c),(a,b),"
              "(b,a)} on the set {a, b, c} is an "
              "equivalence relation")
    assert "is an equivalence relation" in out["answer"]


# ------------------------------------------------------------------
# Relation properties, set-builder dress
# ------------------------------------------------------------------

def test_builder_less_than():
    out = ans("Check whether the relation R = {(x, y) : "
              "x < y} on the set {1, 2, 3, 4} is reflexive, "
              "symmetric or transitive")
    assert out["answer"] == ("R is transitive but neither "
                             "reflexive nor symmetric.")


def test_builder_divisible_equivalence():
    out = ans("Show that the relation R = {(x, y) : x - y "
              "is divisible by 3} on the set {1, 2, 3, 4, 5, "
              "6} is an equivalence relation")
    assert "is an equivalence relation" in out["answer"]
    # The enumerated roster is shown in the steps.
    assert "(1, 4)" in " ".join(out["steps"])


def test_builder_sum_equals():
    # x + y = 4 on {1,2,3}: R = {(1,3),(2,2),(3,1)} —
    # symmetric YES, reflexive NO (witness 1), transitive
    # NO ((1,3),(3,1) in R, (1,1) not in R).
    out = ans("Check whether R = {(x, y) : x + y = 4} on "
              "the set {1, 2, 3} is reflexive, symmetric "
              "or transitive")
    assert out["answer"] == ("R is symmetric but neither "
                             "reflexive nor transitive.")
    joined = " ".join(out["steps"])
    assert "Symmetric: YES" in joined
    assert "Transitive: NO" in joined


def test_builder_divides():
    # x divides y on {1,2,3,6}: reflexive YES, symmetric
    # NO ((1,2) in R, (2,1) not), transitive YES.
    out = ans("Check whether the relation R = {(x, y) : "
              "x divides y} on the set {1, 2, 3, 6} is "
              "reflexive, symmetric or transitive")
    assert out["answer"] == ("R is reflexive and transitive "
                             "but not symmetric.")


# ------------------------------------------------------------------
# Probe 06 — one-one / onto classification + MCQ
# ------------------------------------------------------------------

def test_probe06_schema():
    out = ans(PROBE06)
    assert out["op"] == "function_classification"
    assert out["answer"].startswith("(D)")
    joined = " ".join(out["steps"])
    assert "f(-1) = f(1) = 1" in joined
    assert "-1 is in the codomain but has no preimage" in \
        joined


def test_probe06_router():
    out = solve_question(PROBE06)
    assert out["op"] == "function_classification"
    assert out["answer"].startswith("(D)")


def test_x3_bijective():
    out = ans("Is the function f: R -> R, f(x) = x^3 "
              "one-one and onto?")
    assert "bijective" in out["answer"]


def test_x2_reals_neither():
    out = ans("Check whether f: R -> R, f(x) = x^2 is "
              "one-one and onto")
    assert "neither one-one nor onto" in out["answer"]


def test_x2_naturals_one_one_not_onto():
    out = ans("f: N -> N, f(x) = x^2. Is f one-one? "
              "Is f onto?")
    assert "one-one but not onto" in out["answer"]
    assert "2 has no preimage" in " ".join(out["steps"])


def test_x2_restricted_domain_flips_verdict():
    out = ans("f : [0, inf) -> [0, inf), f(x) = x^2. "
              "Is f one-one and onto?")
    assert "bijective" in out["answer"]


def test_modulus_neither():
    out = ans("Show that f: R -> R, f(x) = |x| is neither "
              "one-one nor onto")
    assert "neither one-one nor onto" in out["answer"]


def test_greatest_integer_neither():
    out = ans("Let f: R -> R be the greatest integer "
              "function f(x) = [x]. Is f one-one or onto?")
    assert "neither one-one nor onto" in out["answer"]
    assert "f(1/2) = f(3/4) = 0" in " ".join(out["steps"])


def test_signum_neither():
    out = ans("f: R -> R is the signum function. Check "
              "whether f is one-one and onto")
    assert "neither one-one nor onto" in out["answer"]


def test_reciprocal_bijective_on_nonzero():
    out = ans("Show that f: R - {0} -> R - {0}, f(x) = 1/x "
              "is one-one and onto")
    assert "bijective" in out["answer"]


def test_reciprocal_to_reals_not_onto():
    out = ans("f: R - {0} -> R, f(x) = 1/x. Is f onto?")
    assert "one-one but not onto" in out["answer"]


def test_linear_bijective():
    out = ans("f: R -> R, f(x) = 2x + 3. Is f bijective?")
    assert "bijective" in out["answer"]


def test_linear_naturals_not_onto():
    out = ans("f: N -> N, f(x) = 2x. Is f onto?")
    assert "one-one but not onto" in out["answer"]
    assert "1 has no preimage" in " ".join(out["steps"])


def test_linear_integers_bijective_and_not():
    out = ans("f: Z -> Z, f(x) = x + 1. Is f one-one "
              "and onto?")
    assert "bijective" in out["answer"]
    out = ans("f: Z -> Z, f(x) = 2x. Check if f is onto")
    assert "one-one but not onto" in out["answer"]


def test_mobius_one_one_not_onto():
    out = ans("Let f: R - {2} -> R be defined by "
              "f(x) = (x+2)/(x-2). Is f one-one? Is f onto?")
    assert "one-one but not onto" in out["answer"]
    assert "1 is in the codomain but has no preimage" in \
        " ".join(out["steps"])


def test_odd_monomial_rationals_not_onto():
    out = ans("f: Q -> Q, f(x) = x^3. Is f onto?")
    assert "one-one but not onto" in out["answer"]
    assert "2 has no preimage" in " ".join(out["steps"])


def test_constant_neither():
    out = ans("f: R -> R, f(x) = 5. Is f one-one or onto?")
    assert "neither one-one nor onto" in out["answer"]


def test_x5_bijective():
    out = ans("f: R -> R, f(x) = x^5. Is f bijective?")
    assert "bijective" in out["answer"]


# ------------------------------------------------------------------
# Counting forms
# ------------------------------------------------------------------

def test_count_relations():
    assert ans("Find the number of relations on a set "
               "with 3 elements")["answer"] == "512"
    assert ans("Find the number of relations on the set "
               "{1, 2, 3, 4}")["answer"] == "65536"


def test_count_reflexive_relations():
    # 2^(9-3) = 64 for n = 3; 2^(4-2) = 4 for n = 2.
    assert ans("Find the number of reflexive relations "
               "on a set with 3 elements")["answer"] == "64"
    assert ans("How many reflexive relations are there "
               "on a set with 2 elements?")["answer"] == "4"


def test_count_symmetric_relations():
    # 2^(3*4/2) = 64 for n = 3; 2^(2*3/2) = 8 for n = 2.
    assert ans("How many symmetric relations are there "
               "on a set with 2 elements?")["answer"] == "8"


def test_count_equivalence_relations():
    # Bell(3) = 5, Bell(4) = 15.
    assert ans("Find the number of equivalence relations "
               "on a set with 3 elements")["answer"] == "5"
    assert ans("Find the number of equivalence relations "
               "on a set with 4 elements")["answer"] == "15"


def test_count_equivalence_containing_pair():
    # (1, 2) forced: blocks {1,2}, {3} -> Bell(2) = 2.
    assert ans("Find the number of equivalence relations "
               "on the set {1, 2, 3} containing (1, 2)")[
                   "answer"] == "2"


def test_count_functions_total():
    assert ans("Find the number of functions from a set "
               "with 3 elements to a set with 2 elements")[
                   "answer"] == "8"


def test_count_oneone_functions():
    # P(4, 2) = 12; P(2, 3) = 0.
    assert ans("How many one-one functions are there "
               "from a 2-element set to a 4-element set?")[
                   "answer"] == "12"
    assert ans("How many one-one functions are there "
               "from a 3-element set to a 2-element set?")[
                   "answer"] == "0"


def test_count_onto_functions():
    # 2^4 - 2 = 14; 3! = 6; n < m -> 0.
    assert ans("How many onto functions are there from "
               "a set with 4 elements to a set with 2 "
               "elements?")["answer"] == "14"
    assert ans("How many onto functions are there from "
               "a set with 3 elements to a set with 3 "
               "elements?")["answer"] == "6"
    assert ans("How many onto functions are there from "
               "a set with 2 elements to a set with 3 "
               "elements?")["answer"] == "0"


def test_counting_router():
    out = solve_question("Find the number of relations on "
                         "a set with 3 elements")
    assert out["answer"] == "512"
    out = solve_question("How many onto functions are "
                         "there from a set with 4 elements "
                         "to a set with 2 elements?")
    assert out["answer"] == "14"


# ------------------------------------------------------------------
# Declines — unrecognised / undecidable inputs return None
# ------------------------------------------------------------------

def test_declines_unrecognised_function():
    declines("f: R -> R, f(x) = x^2 + 1. Is f one-one "
             "or onto?")
    declines("f: R -> R, f(x) = sin x. Is f one-one "
             "or onto?")
    declines("f: R -> R, f(x) = e^x. Is f onto?")


def test_declines_mobius_with_pole_in_domain():
    # (x+2)/(x-2) is not defined at 2, so f : R -> R is
    # not a valid function statement — decline, never
    # guess.
    declines("Let f: R -> R, f(x) = (x+2)/(x-2). Is f "
             "one-one or onto?")


def test_declines_reciprocal_with_zero_in_domain():
    declines("f: R -> R, f(x) = 1/x. Is f one-one?")


def test_declines_relation_on_infinite_set():
    declines("Show that R = {(x, y) : x < y} is "
             "transitive on N")


def test_declines_relation_without_property_ask():
    declines("Find the domain of the relation "
             "R = {(1,2),(2,3)}")


def test_declines_reflexive_and_symmetric_count():
    # The combined reflexive-and-symmetric count is not
    # in the pinned catalogue.
    declines("Find the number of reflexive and symmetric "
             "relations on a set with 3 elements")


# ------------------------------------------------------------------
# Controls — pre-existing serves stay byte-identical
# ------------------------------------------------------------------

def test_control_function_evaluation():
    out = solve_question("if f(x) = x^2 + 1, find f(2)")
    assert out["answer"] == "f(2) = 5"
    assert solve_relations191("if f(x) = x^2 + 1, find "
                              "f(2)") is None


def test_control_sets_basics():
    out = solve_question("{1,2,3} union {3,4,5}")
    assert out["type"] == "sets"
    assert out["answer"] == "{1, 2, 3, 4, 5}"


def test_control_irrationality_proof():
    out = solve_question("Prove that sqrt(2) is "
                         "irrational")
    assert out.get("fallback_kind") == "proof" or \
        "irrational" in str(out.get("answer", "")).lower()
    assert solve_relations191("Prove that sqrt(2) is "
                              "irrational") is None
