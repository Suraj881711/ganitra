"""Broader coverage tests: one (or more) per topic area.

These mirror the samples verified against the live solver; expected
values are standard textbook results.
"""
import pytest

from solver.router import solve_question


def ans(q):
    return solve_question(q)


def test_fraction():
    r = ans("3/4 + 1/2")
    assert r["type"] == "arithmetic"
    assert r["numeric"] == pytest.approx(1.25)


def test_percentage():
    r = ans("15% of 240")
    assert r["numeric"] == pytest.approx(36.0)


def test_quadratic():
    r = ans("x^2 - 5x + 6 = 0")
    assert r["type"] == "algebra"
    assert sorted(r["solutions"]) == ["2", "3"]


def test_system():
    r = ans("x + y = 10 and x - y = 4")
    assert r["type"] == "algebra"
    assert "x = 7" in r["answer"] and "y = 3" in r["answer"]


def test_inequality():
    r = ans("2x + 3 > 7")
    assert r["type"] == "algebra"
    assert "2" in r["answer"]


def test_factor_expand_simplify():
    assert "(x - 2)" in ans("factor x^2 - 5x + 6")["answer"].replace(
        "·", "*") or "x - 2" in ans("factor x^2 - 5x + 6")["answer"]
    assert ans("expand (x+2)(x+3)")["answer"].replace(" ", "") in (
        "x^2+5·x+6", "x^2+5x+6")
    assert ans("simplify (x^2-1)/(x-1)")["answer"] == "x + 1"


def test_log():
    r = ans("log base 2 of 32")
    assert r["value"] == pytest.approx(5.0)


def test_trig_values():
    assert ans("sin 30")["value"] == pytest.approx(0.5)
    r = ans("cos(pi/3)")
    assert r["value"] == pytest.approx(0.5)


def test_trig_identity():
    r = ans("prove sin^2(x) + cos^2(x) = 1")
    assert r["verified"] is True


def test_trig_equation():
    r = ans("solve sin(x) = 1/2")
    assert "30" in r["answer"] and "150" in r["answer"]


def test_calculus():
    assert ans("derivative of x^3 + 2x")["answer"] == "3·x^2 + 2"
    assert ans("integrate x^2 from 0 to 1")["answer"] == "1/3"
    assert ans("limit x->0 of sin(x)/x")["answer"] == "1"
    assert ans("partial derivative of x^2*y with respect to y")[
        "answer"] == "x^2"
    assert "C1" in ans("solve dy/dx = 2x")["answer"]


def test_linear_algebra():
    assert ans("determinant of [[1,2],[3,4]]")["answer"] == "-2"
    assert ans("rank of [[1,2],[2,4]]")["answer"] == "1"
    assert "2" in ans("eigenvalues of [[2,0],[0,3]]")["answer"]


def test_geometry():
    assert "78.5" in ans("area of circle with radius 5")["answer"]
    assert ans("distance between (1,2) and (4,6)")["answer"] == "5"


def test_statistics():
    assert ans("mean of 2, 4, 6, 8")["value"] == pytest.approx(5.0)
    assert ans("standard deviation of 2,4,4,4,5,5,7,9")[
        "value"] == pytest.approx(2.0)
    assert ans("C(5,2)")["value"] == 10
    assert ans("probability of getting a 6 on a dice")[
        "value"] == pytest.approx(1 / 6)
    assert ans("probability of sum 7 with two dice")[
        "value"] == pytest.approx(1 / 6)


def test_number_theory():
    assert ans("is 97 prime?")["value"] is True
    assert ans("gcd of 12 and 18")["value"] == 6
    assert ans("lcm of 4 and 6")["value"] == 12
    assert ans("17 mod 5")["value"] == 2


def test_sequences():
    assert ans("10th term of AP 2, 5, 8")["value"] == 29
    assert ans("sum of first 10 terms of AP 2, 5, 8")[
        "value"] == pytest.approx(155)
    assert ans("sum of first 10 natural numbers")["value"] == 55


def test_complex_numbers():
    assert ans("(2+3i)*(1-i)")["answer"] == "5 + I".replace("I", "i") or \
        "5" in ans("(2+3i)*(1-i)")["answer"]
    assert ans("modulus of 3+4i")["value"] == pytest.approx(5.0)


def test_sets():
    r = ans("{1,2,3} union {3,4,5}")
    assert r["elements"] == [1, 2, 3, 4, 5]


def test_units():
    r = ans("convert 5 km to miles")
    assert r["value"] == pytest.approx(3.10686, abs=1e-3)
    r = ans("convert 37 celsius to fahrenheit")
    assert r["value"] == pytest.approx(98.6)


def test_word_problem():
    assert ans("increase by 15% of 240")["value"] == pytest.approx(276.0)
    assert ans("simple interest on 1000 at 5% for 2 years")[
        "value"] == pytest.approx(100.0)


def test_hinglish():
    assert ans("5 aur 3 ko jodo")["numeric"] == pytest.approx(8.0)
    assert ans("20 ko 4 se bhaag do")["numeric"] == pytest.approx(5.0)
    assert ans("240 ka 15 pratishat")["numeric"] == pytest.approx(36.0)
    assert ans("sin 30 ka maan")["value"] == pytest.approx(0.5)


def test_hinglish_ka_jod_family():
    # Regression (live bug, 12 Nov 2026): "15 aur 27 ka jod kitna
    # hoga?" had NO normalisation pattern, fell through to SymPy and
    # was answered as 405*d*j*o ("jod" read as variables j*o*d).
    # The whole natural noun/imperative addition family must work.
    add_cases = [
        "15 aur 27 ka jod kitna hoga?",
        "15 aur 27 ka jod",
        "15 aur 27 ka jod kitna hai",
        "15 aur 27 ko jodkar batao",
        "15 aur 27 ko jod ke batao",
        "15 aur 27 jodkar batao",
        "15 aur 27 jodo",
    ]
    for q in add_cases:
        r = ans(q)
        assert r["numeric"] == pytest.approx(42.0), q
        assert r["steps"], q
    # Same one-pattern gap in the sibling operations' noun forms:
    # "ka ghata/ghatav" (subtract) and "ka bhaag" (divide) were
    # missing too; "ka guna" (multiply) already worked.
    assert ans("27 aur 15 ka ghata kitna hoga?")["numeric"] == \
        pytest.approx(12.0)
    assert ans("27 aur 15 ka ghatav")["numeric"] == pytest.approx(12.0)
    assert ans("20 aur 4 ka bhaag kitna hoga?")["numeric"] == \
        pytest.approx(5.0)
    assert ans("15 aur 27 ka guna kitna hoga?")["numeric"] == \
        pytest.approx(405.0)
