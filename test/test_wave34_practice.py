"""Wave 34 tests for the standalone practice generator
(practice_gen.py at the app root).

Three things are proved here:
1. Generated questions PARSE — every solver-rendered text parses
   with sympy's parser (the same parser family the solver uses),
   and every question text is a clean non-empty string.
2. The generator's answers match an INDEPENDENT recomputation
   done here from the item's params, from first principles.
3. A sample CROSS-CHECK against the Ganitra solver itself
   (api._solve_friendly): for the templates that have a
   solver_text, the solver's answer must agree numerically.

practice_gen is standalone (not wired into routes/templates);
these tests only import it directly.
"""
import math
import re
from fractions import Fraction

import pytest
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application, parse_expr,
    standard_transformations)

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,)

import practice_gen


def _all_items(seeds=range(30)):
    items = []
    for class_num in practice_gen.CLASSES:
        for topic in practice_gen.TOPICS:
            for seed in seeds:
                items.append(practice_gen.generate_question(
                    class_num, topic, seed=seed))
    return items


# ---------------------------------------------------------------------------
# 1. Generation + parsing
# ---------------------------------------------------------------------------

def test_generates_for_every_class_and_topic():
    items = _all_items(seeds=range(5))
    assert len(items) == 5 * 5 * 5
    for it in items:
        assert isinstance(it["question"], str)
        assert len(it["question"]) > 10
        assert "{" not in it["question"]  # no unformatted template
        assert isinstance(it["answer"], str) and it["answer"]


def test_solver_texts_parse_with_sympy():
    checked = 0
    # Wave 54: the pool grew from 20 to 100 kinds, so the
    # solver_text kinds are a smaller share of random draws;
    # the seed range is widened to keep the sample > 100.
    for it in _all_items(seeds=range(90)):
        text = it["solver_text"]
        if text is None:
            continue
        checked += 1
        if "=" in text:  # an equation: both sides must parse
            lhs, rhs = text.split("=", 1)
            parse_expr(lhs, transformations=_TRANSFORMS)
            parse_expr(rhs, transformations=_TRANSFORMS)
        else:
            parse_expr(text, transformations=_TRANSFORMS)
    assert checked > 100  # a real sample, not a token few


def test_invalid_class_or_topic_rejected():
    with pytest.raises(ValueError):
        practice_gen.generate_question(5, "arithmetic")
    with pytest.raises(ValueError):
        practice_gen.generate_question(11, "arithmetic")
    with pytest.raises(ValueError):
        practice_gen.generate_question(8, "trigonometry")


def test_generate_set_is_deterministic():
    a = practice_gen.generate_set(9, "algebra", count=6, seed=42)
    b = practice_gen.generate_set(9, "algebra", count=6, seed=42)
    assert [x["question"] for x in a] == [x["question"] for x in b]
    assert len(a) == 6


# ---------------------------------------------------------------------------
# 2. Independent recomputation of every answer
# ---------------------------------------------------------------------------

def _recompute(it):
    """Recompute the expected answer from params, independently."""
    p = it["params"]
    kind = it["kind"]
    if kind == "expression":
        return Fraction(eval(it["solver_text"], {"__builtins__": {}},
                             {}))
    if kind == "fraction_add":
        return Fraction(p["a"], p["b"]) + Fraction(p["c"], p["d"])
    if kind == "percent":
        return Fraction(p["p"], 100) * p["n"]
    if kind == "simple_interest":
        return Fraction(p["principal"] * p["rate"] * p["years"], 100)
    if kind == "linear_equation":
        return Fraction(p["c"] - p["b"], p["a"])
    if kind == "evaluate_linear":
        return Fraction(p["a"] * p["x"] + p["b"])
    if kind == "ap_nth_term":
        return Fraction(p["a"] + (p["n"] - 1) * p["d"])
    if kind == "supplementary_angle":
        return Fraction(180 - p["a"])
    if kind == "triangle_third_angle":
        return Fraction(180 - p["a"] - p["b"])
    if kind == "rectangle_area":
        return Fraction(p["length"] * p["breadth"])
    if kind == "circle_circumference":
        return Fraction(2 * 22 * p["r"], 7)
    if kind == "cuboid_volume":
        return Fraction(p["length"] * p["breadth"] * p["height"])
    if kind == "cube_surface_area":
        return Fraction(6 * p["side"] ** 2)
    if kind == "cylinder_volume":
        return Fraction(22, 7) * p["r"] ** 2 * p["h"]
    if kind == "cone_volume":
        return Fraction(22, 7) * p["r"] ** 2 * p["h"] / 3
    if kind == "bag_probability":
        return Fraction(p["red"], p["red"] + p["blue"])
    if kind == "die_greater":
        return Fraction(6 - p["k"], 6)
    if kind == "coins_at_least_one_head":
        return 1 - Fraction(1, 2) ** p["n"]
    # ---- Wave 54 kinds (independent recomputation) ----
    if kind == "integer_add_sub":
        return Fraction(p["a"] + p["b"] if p["op"] == "add"
                        else p["a"] - p["b"])
    if kind == "fraction_subtract":
        return Fraction(p["a"], p["b"]) - Fraction(p["c"],
                                                   p["d"])
    if kind == "fraction_of":
        return Fraction(p["n"], p["d"]) * p["quantity"]
    if kind == "fraction_multiply":
        return Fraction(p["a"] * p["c"], p["b"] * p["d"])
    if kind == "fraction_divide":
        return Fraction(p["a"] * p["d"], p["b"] * p["c"])
    if kind == "mixed_fraction_add":
        return (Fraction(p["w1"] * p["d1"] + p["n1"], p["d1"])
                + Fraction(p["w2"] * p["d2"] + p["n2"],
                           p["d2"]))
    if kind == "decimal_add":
        return Fraction(p["a"]) + Fraction(p["b"])
    if kind == "decimal_multiply":
        return Fraction(p["a"]) * Fraction(p["b"])
    if kind == "percent_increase":
        return Fraction(p["price"] * (100 + p["p"]), 100)
    if kind == "discount_price":
        return Fraction(p["price"] * (100 - p["p"]), 100)
    if kind == "find_whole_from_percent":
        return Fraction(p["part"] * 100, p["p"])
    if kind == "ratio_share":
        share = p["a"] if p["ask"] == "first" else p["b"]
        return Fraction(p["total"] * share, p["a"] + p["b"])
    if kind == "unitary_method":
        return Fraction(p["total"], p["n"]) * p["m"]
    if kind == "average":
        return Fraction(sum(p["nums"]), len(p["nums"]))
    if kind == "hcf":
        return Fraction(math.gcd(p["a"], p["b"]))
    if kind == "lcm":
        return Fraction(p["a"] * p["b"]
                        // math.gcd(p["a"], p["b"]))
    if kind == "compound_interest":
        amount = Fraction(p["principal"]) * Fraction(
            100 + p["rate"], 100) ** p["years"]
        return amount - p["principal"]
    if kind == "square_of":
        return Fraction(p["n"] ** 2)
    if kind == "sqrt_perfect":
        return Fraction(math.isqrt(p["number"]))
    if kind == "cube_of":
        return Fraction(p["n"] ** 3)
    if kind == "exponent_value":
        return Fraction(p["base"] ** p["exp"])
    if kind == "profit_loss":
        return Fraction(abs(p["sp"] - p["cp"]))
    if kind == "speed_distance_time":
        if p["variant"] == "speed":
            return Fraction(p["distance"], p["time"])
        if p["variant"] == "distance":
            return Fraction(p["speed"] * p["time"])
        return Fraction(p["distance"], p["speed"])
    if kind == "evaluate_quadratic":
        return Fraction(p["a"] * p["x"] ** 2
                        + p["b"] * p["x"] + p["c"])
    if kind == "evaluate_two_vars":
        return Fraction(p["a"] * p["x"] + p["b"] * p["y"])
    if kind == "equation_both_sides":
        return Fraction(p["d"] - p["b"], p["a"] - p["c"])
    if kind == "simultaneous":
        return Fraction(p["x"] if p["ask"] == "x" else p["y"])
    if kind == "identity_numeric":
        if p["variant"] == "square":
            return Fraction(p["n"] ** 2)
        return Fraction(p["m"] ** 2 - p["k"] ** 2)
    if kind == "ap_sum":
        return Fraction(p["n"] * (2 * p["a"]
                        + (p["n"] - 1) * p["d"]), 2)
    if kind == "gp_nth_term":
        return Fraction(p["a"] * p["r"] ** (p["n"] - 1))
    if kind == "gp_sum":
        return Fraction(p["a"] * (p["r"] ** p["n"] - 1),
                        p["r"] - 1)
    if kind == "index_laws":
        if p["variant"] == "product":
            return Fraction(p["base"] ** (p["m"] + p["n"]))
        if p["variant"] == "quotient":
            return Fraction(p["base"] ** (p["m"] - p["n"]))
        return Fraction(p["base"] ** (p["m"] * p["n"]))
    if kind == "complementary_angle":
        return Fraction(90 - p["a"])
    if kind == "triangle_exterior_angle":
        if p["variant"] == "exterior":
            return Fraction(p["p"] + p["q"])
        return Fraction(p["exterior"] - p["p"])
    if kind == "isosceles_angle":
        if p["variant"] == "base":
            return Fraction(180 - p["vertex"], 2)
        return Fraction(180 - 2 * p["base"])
    if kind == "quadrilateral_fourth_angle":
        return Fraction(360 - p["a"] - p["b"] - p["c"])
    if kind == "parallelogram_angle":
        return Fraction(p["a"] if p["variant"] == "opposite"
                        else 180 - p["a"])
    if kind == "square_area":
        return Fraction(p["side"] ** 2)
    if kind == "square_perimeter":
        return Fraction(4 * p["side"])
    if kind == "rectangle_perimeter":
        return Fraction(2 * (p["length"] + p["breadth"]))
    if kind == "triangle_area":
        return Fraction(p["base"] * p["height"], 2)
    if kind == "triangle_perimeter":
        return Fraction(p["a"] + p["b"] + p["c"])
    if kind == "rhombus_area":
        return Fraction(p["d1"] * p["d2"], 2)
    if kind == "trapezium_area":
        return Fraction((p["a"] + p["b"]) * p["h"], 2)
    if kind == "circle_area":
        return Fraction(22, 7) * p["r"] ** 2
    if kind == "circle_radius_from_circumference":
        return Fraction(p["circumference"] * 7, 44)
    if kind == "polygon_interior_sum":
        return Fraction((p["n"] - 2) * 180)
    if kind == "regular_polygon_exterior":
        return Fraction(360, p["n"])
    if kind == "parallel_lines_angle":
        return Fraction(
            p["a"] if p["variant"] == "corresponding"
            else 180 - p["a"])
    if kind == "pythagoras":
        if p["variant"] == "hypotenuse":
            return Fraction(math.isqrt(p["p"] ** 2
                                       + p["q"] ** 2))
        return Fraction(math.isqrt(p["h"] ** 2
                                   - p["given_leg"] ** 2))
    if kind == "sector_area":
        return (Fraction(p["theta"], 360) * Fraction(22, 7)
                * p["r"] ** 2)
    if kind == "coordinate_distance":
        if p["variant"] == "axis":
            return Fraction(abs(p["x2"] - p["x1"]))
        return Fraction(math.isqrt(p["x"] ** 2 + p["y"] ** 2))
    if kind == "cube_volume":
        return Fraction(p["side"] ** 3)
    if kind == "cuboid_surface_area":
        return Fraction(2 * (p["length"] * p["breadth"]
                             + p["breadth"] * p["height"]
                             + p["height"] * p["length"]))
    if kind == "cuboid_lsa":
        return Fraction(2 * p["height"]
                        * (p["length"] + p["breadth"]))
    if kind == "cylinder_csa":
        return Fraction(2) * Fraction(22, 7) * p["r"] * p["h"]
    if kind == "cylinder_tsa":
        return (Fraction(2) * Fraction(22, 7) * p["r"]
                * (p["r"] + p["h"]))
    if kind == "sphere_volume":
        return Fraction(4, 3) * Fraction(22, 7) * p["r"] ** 3
    if kind == "sphere_surface_area":
        return Fraction(4) * Fraction(22, 7) * p["r"] ** 2
    if kind == "hemisphere_volume":
        return Fraction(2, 3) * Fraction(22, 7) * p["r"] ** 3
    if kind == "hemisphere_tsa":
        return Fraction(3) * Fraction(22, 7) * p["r"] ** 2
    if kind == "cone_csa":
        slant = math.isqrt(p["r"] ** 2 + p["h"] ** 2)
        return Fraction(22, 7) * p["r"] * slant
    if kind == "fencing_cost":
        return Fraction(2 * (p["length"] + p["breadth"])
                        * p["rate"])
    if kind == "tiling_cost":
        return Fraction(p["length"] * p["breadth"]
                        * p["rate"])
    if kind == "litres_capacity":
        return Fraction(p["length"] * p["breadth"]
                        * p["height"], 1000)
    if kind == "bag_three_colours":
        return Fraction(p[p["ask"]],
                        p["red"] + p["blue"] + p["green"])
    if kind == "die_event":
        faces = range(1, 7)
        if p["variant"] == "even":
            count = sum(1 for x in faces if x % 2 == 0)
        elif p["variant"] == "odd":
            count = sum(1 for x in faces if x % 2 == 1)
        elif p["variant"] == "prime":
            count = sum(1 for x in faces if x in (2, 3, 5))
        else:
            count = sum(1 for x in faces if x % p["k"] == 0)
        return Fraction(count, 6)
    if kind == "coins_exactly_heads":
        return Fraction(math.comb(p["n"], p["k"]),
                        2 ** p["n"])
    if kind == "card_probability":
        return Fraction(p["favourable"], 52)
    if kind == "two_dice_sum":
        count = sum(1 for i in range(1, 7)
                    for j in range(1, 7) if i + j == p["s"])
        return Fraction(count, 36)
    if kind == "two_draw_probability":
        total = p["red"] + p["blue"]
        return Fraction(p["red"], total) * Fraction(
            p["red"] - 1, total - 1)
    if kind == "complement_probability":
        return 1 - Fraction(p["a"], p["b"])
    if kind == "word_letter_probability":
        word = p["word"]
        if p["variant"] == "vowel":
            count = sum(1 for ch in word if ch in "AEIOU")
        else:
            count = word.count(p["letter"])
        return Fraction(count, len(word))
    raise AssertionError(f"no recompute branch for kind {kind}")


def test_answers_match_independent_recomputation():
    checked = 0
    for it in _all_items():
        if it["answer_value"] is None:
            continue
        checked += 1
        expected = _recompute(it)
        assert it["answer_value"] == expected, (
            it["kind"], it["question"], it["answer_value"], expected)
        # The printed answer must carry the same value — in
        # fraction form ("79/4") or, for the Wave 54 decimal
        # kinds, decimal form ("19.75"); Fraction() parses both.
        assert Fraction(it["answer"]) == expected, (
            it["kind"], it["question"], it["answer"], expected)
    assert checked > 400


def test_expand_and_quadratic_answers():
    for class_num in (8, 9, 10):
        for seed in range(60):
            it = practice_gen.generate_question(
                class_num, "algebra", seed=seed)
            p = it["params"]
            if it["kind"] == "expand_binomials":
                # (x + a)(x + b) = x² + (a+b)x + ab, recomputed
                assert it["answer"] == (
                    f"x² + {p['a'] + p['b']}x + {p['a'] * p['b']}")
            elif it["kind"] == "quadratic_roots":
                r1, r2 = p["r1"], p["r2"]
                # the roots really satisfy the printed equation:
                for r in (r1, r2):
                    assert r * r - (r1 + r2) * r + r1 * r2 == 0
                assert it["answer"] == f"x = {r1} or x = {r2}"


# ---------------------------------------------------------------------------
# 3. Cross-check a sample against the Ganitra solver
# ---------------------------------------------------------------------------

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?(?:/\d+)?")


def _first_number(text):
    m = _NUMBER_RE.search(str(text))
    if not m:
        return None
    token = m.group(0)
    if "/" in token and "." not in token:
        num, den = token.split("/")
        return Fraction(int(num), int(den))
    return Fraction(token).limit_denominator(10 ** 6)


def test_solver_crosscheck_sample():
    from api import _solve_friendly

    sample = []
    for class_num in (7, 8, 9, 10):
        for topic in ("arithmetic", "algebra"):
            # Wave 54: wider seed range — with 100 kinds in
            # the pools, 10 seeds no longer yield 20+
            # solver_text items (assertions unchanged).
            for seed in range(60):
                it = practice_gen.generate_question(
                    class_num, topic, seed=seed)
                if it["solver_text"] and it["answer_value"] is not None:
                    sample.append(it)
    assert len(sample) >= 20

    agreed = 0
    for it in sample:
        result = _solve_friendly(it["solver_text"])
        if "fallback" in result:
            continue  # solver declined; not a disagreement
        got = _first_number(result.get("answer", ""))
        assert got is not None, (it["solver_text"], result)
        assert got == it["answer_value"], (
            it["solver_text"], result.get("answer"),
            it["answer_value"])
        agreed += 1
    # the large majority of the sample must actually be answered
    # by the solver (not silently skipped as fallbacks)
    assert agreed >= 15, f"only {agreed} solver agreements"
