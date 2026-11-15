"""Wave 53 (15 Nov 2026): MORE SOLUTION METHODS per answer —
Suraj's pick ("Har sawal ke jawab me aur tarike (methods)
dikhao"). The answer card's More (•••) menu gains a genuine
second/third method for ~20 more question families; the
primary answer and steps never change (the 515-question
battery is byte-identical before/after: 335 EXACT / 151
FALLBACK / 29 WRONG / 0 ERROR, 0 per-item diffs).

New alternates (solver/methods.py):
  * pairs of linear equations — substitution / elimination
    (with fraction-clearing) / cross-multiplication,
    whichever the primary did not work;
  * AP sum — Gauss pairing; GP sum — adding the terms;
  * compound interest — year by year;
  * profit/loss percent + reverse profit/loss — unitary;
  * discount — direct percent; successive discounts —
    single equivalent discount;
  * marks percent + "what percent" — unitary / fraction;
  * unitary cost — proportion; ratio division — fraction
    of the whole;
  * LCM — division method (2 and 3 numbers); HCF+LCM —
    Euclid + the a*b = HCF*LCM relation;
  * median — position formula (odd and even n);
  * probability — complement rule (die, one/two coins,
    coloured balls, standard card facts);
  * trig ratio-from-ratio — the identity route;
  * standard trig values — derived from the two standard
    triangles (incl. the "degrees" wording and ^2 forms);
  * circle area / circumference — via the diameter;
  * rectangle / square area — counting unit squares;
  * perimeter — adding the sides; cuboid / cube volume —
    layers; cylinder volume — base area x height; cone
    volume — one-third of the cylinder.

Every test asserts the new method is offered AND that its
final answer equals the primary answer (hard rule (c)).
"""
from solver.methods import alternate_methods
from solver.router import solve_question


def _methods(q):
    return alternate_methods(q, solve_question(q))


def _ids(q):
    return [m["id"] for m in _methods(q)]


def _check(q, want_id):
    primary = solve_question(q)
    ms = alternate_methods(q, primary)
    by_id = {m["id"]: m for m in ms}
    assert want_id in by_id, (q, [m["id"] for m in ms])
    assert by_id[want_id]["answer"] == primary.get("answer"), q
    assert by_id[want_id]["steps"], q
    return by_id[want_id]


# ------------------------------------------------ systems
def test_system_generic_primary_gets_substitution_and_cross():
    q = "Solve for x and y: 2x + 3y = 11, 2x - 4y = -24"
    _check(q, "substitution")
    _check(q, "cross_multiplication")


def test_system_substitution_primary_gets_elimination():
    q = "Solve: x/2 + y/3 = 4, x - y = 2"
    m = _check(q, "elimination")
    assert any("Clear the fractions" in s for s in m["steps"])
    _check(q, "cross_multiplication")


def test_system_plain_pair():
    _check("x + y = 14, x - y = 4", "substitution")
    _check("x + y = 14, x - y = 4", "cross_multiplication")


# ------------------------------------------------ sequences
def test_ap_sum_pairing():
    _check("Find the sum of first 20 terms of the AP: "
           "3, 7, 11, 15, ...", "pairing")


def test_gp_sum_term_addition():
    _check("Find the sum of the first 5 terms of the GP: "
           "3, 6, 12, 24, ...", "term_addition")


# ------------------------------------------------ interest / applied
def test_compound_interest_yearly():
    _check("Find the compound interest on Rs 8000 at 5% "
           "per annum for 2 years", "yearly_breakup")
    _check("Calculate the compound interest on Rs 10000 "
           "at 10% per annum for 3 years", "yearly_breakup")


def test_profit_percent_unitary():
    _check("Find the profit percent if CP is Rs 400 and "
           "SP is Rs 460", "unitary")
    _check("Find the loss percent if CP = Rs 500 and "
           "SP = Rs 425", "unitary")


def test_reverse_profit_loss_unitary():
    _check("A book was sold for Rs 270 with a profit of "
           "8%. Find its cost price", "unitary")


def test_discount_direct_percent():
    # The applied discount solver is reached through the
    # served pipeline (api._solve_friendly), as in production.
    from api import _solve_friendly
    q = ("Find the selling price of an article with marked "
         "price Rs 1500 and a discount of 20%")
    primary = _solve_friendly(q)
    assert primary.get("op") == "discount"
    ms = {m["id"]: m for m in alternate_methods(q, primary)}
    assert "direct_percent" in ms
    assert ms["direct_percent"]["answer"] == \
        primary.get("answer")


def test_successive_discount_equivalent():
    _check("The marked price of an article is Rs 3000. Two "
           "successive discounts of 15% and 10% are offered.",
           "equivalent_discount")


def test_percent_score_unitary():
    _check("Rahul scored 45 marks out of 60. Find his "
           "percentage of marks.", "unitary")


def test_what_percent_fraction_and_unitary():
    q = "What percent of 250 is 50?"
    _check(q, "fraction")
    _check(q, "unitary")


def test_unitary_cost_proportion():
    _check("If the cost of 5 pens is Rs 100, find the cost "
           "of 8 pens.", "proportion")


def test_ratio_divide_fraction_of_whole():
    _check("Divide Rs 1200 in the ratio 2 : 3",
           "fraction_of_whole")


# ------------------------------------------------ number theory
def test_lcm_two_methods():
    q = "Find the LCM of 12 and 18"
    _check(q, "hcf_relation")
    _check(q, "division_method")


def test_lcm_three_numbers_division():
    _check("Find the LCM of 15, 20 and 30", "division_method")


def test_hcf_lcm_relation():
    _check("Find the HCF and LCM of 26 and 91",
           "euclid_relation")


# ------------------------------------------------ statistics
def test_median_odd_position_formula():
    _check("Find the median of 3, 7, 5, 9, 11",
           "position_formula")


def test_median_even_position_formula():
    _check("Find the median of 6, 3, 9, 5, 2, 7",
           "position_formula")


def test_probability_die_complement():
    _check("A die is thrown once. Find the probability of "
           "getting a number greater than 4", "complement")


def test_probability_die_negation_withheld_when_primary_differs():
    # Wave 53's original scenario: the die primary ignored
    # "not" and answered 1/6, so the (correct) 5/6 complement
    # was withheld by rule (c) rather than contradict it.
    # Merge-3 update: Wave 58 FIXED that primary (it was on
    # Wave 53's own flagged list) — the primary now answers
    # 5/6, the complement agrees, and the method legitimately
    # attaches. The withholding rule itself is unchanged.
    q = ("A die is thrown once. Find the probability of "
         "not getting a 6")
    primary = solve_question(q)
    assert "5/6" in str(primary.get("answer"))
    methods = alternate_methods(q, primary)
    assert any(m["id"] == "complement"
               for m in methods)


def test_probability_one_coin_complement():
    _check("A coin is tossed once. What is the probability "
           "of getting a head?", "complement")


def test_probability_two_coins_complement():
    _check("Two coins are tossed. Find the probability of "
           "getting two heads", "complement")
    _check("Two coins are tossed simultaneously. Find the "
           "probability of getting at least one head",
           "complement")


def test_probability_balls_complement():
    _check("A bag contains 5 red balls and 3 blue balls. "
           "Find the probability of getting a blue ball",
           "complement")


def test_probability_balls_not_complement():
    _check("A bag contains 4 red and 6 blue balls. What "
           "is the probability of NOT getting a red ball?",
           "complement")


def test_probability_cards_complement():
    _check("Find the probability of getting a king from a "
           "pack of 52 cards", "complement")
    _check("One card is drawn from a pack of 52 cards. "
           "Find the probability that it is a face card",
           "complement")


# ------------------------------------------------ trigonometry
def test_trig_identity_from_tan():
    _check("If tan A = 4/3, find sin A and cos A", "identity")


def test_trig_identity_from_sin():
    _check("If sin A = 3/5, find cos A and tan A", "identity")


def test_trig_values_standard_triangles():
    _check("Find the value of 2 sin 30 + tan 45",
           "standard_triangles")
    _check("Evaluate cos^2 30 + sin^2 30",
           "standard_triangles")


def test_trig_values_degrees_wording():
    _check("Evaluate sin 30 degrees.", "standard_triangles")
    _check("Evaluate 2 sin^2 30 degrees + 3 cos^2 60 "
           "degrees.", "standard_triangles")


# ------------------------------------------------ mensuration
def test_circle_area_via_diameter():
    _check("Find the area of a circle with radius 7 cm",
           "diameter")


def test_circumference_via_diameter():
    _check("Find the circumference of a circle with "
           "radius 7 cm", "diameter")


def test_rectangle_area_grid_counting():
    _check("Find the area of a rectangle with length "
           "15 cm and breadth 8 cm", "grid_counting")


def test_square_area_grid_counting():
    _check("Find the area of a square with side 9 cm",
           "grid_counting")


def test_perimeter_side_addition():
    _check("Find the perimeter of a rectangle with length "
           "12 cm and breadth 7 cm", "side_addition")
    _check("Find the perimeter of a square with side 9 cm",
           "side_addition")


def test_cuboid_volume_layers():
    _check("Find the volume of a cuboid with length 10 cm, "
           "breadth 8 cm and height 5 cm", "layers")


def test_cube_volume_layers():
    _check("Find the volume of a cube with side 9 cm",
           "layers")


def test_cylinder_volume_base_area():
    _check("Find the volume of a cylinder with radius "
           "7 cm and height 10 cm", "base_area")


def test_cone_volume_third_of_cylinder():
    _check("Find the volume of a cone with radius 7 cm "
           "and height 10 cm", "cone_third")


# ------------------------------------------------ labels / hygiene
def test_wave53_labels_exist_in_all_languages():
    import i18n
    ids = ["elimination", "substitution",
           "cross_multiplication", "pairing", "term_addition",
           "complement", "identity", "standard_triangles",
           "position_formula", "division_method",
           "euclid_relation", "diameter", "layers",
           "base_area", "cone_third", "grid_counting",
           "side_addition", "direct_percent",
           "fraction_of_whole", "equivalent_discount"]
    for lang in ("en", "hi", "bn", "mr", "ta", "te"):
        for mid in ids:
            val = i18n.STRINGS[lang].get(f"mm_label_{mid}")
            assert val and str(val).strip(), (lang, mid)


def test_no_method_when_primary_is_fallback():
    # A fallback/concept primary has no verifiable answer,
    # so no alternate may be attached to it.
    q = ("A bag contains 3 red balls and 5 black balls. A "
         "ball is drawn at random. Find the probability "
         "that it is red")
    primary = solve_question(q)
    if primary.get("type") in ("Concept", "Similar example"):
        assert alternate_methods(q, primary) == []
