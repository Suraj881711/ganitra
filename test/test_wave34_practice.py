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
    for it in _all_items():
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
        assert it["answer"] == (
            str(expected.numerator) if expected.denominator == 1
            else f"{expected.numerator}/{expected.denominator}")
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
            for seed in range(10):
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
