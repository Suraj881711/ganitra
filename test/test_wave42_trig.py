"""Wave 42 (15 Nov 2026): trigonometric evaluations.

Broken before this wave (probes):
- "Evaluate sin 30° + cos 60°" returned the junk answer
  "°" and "sin 60° cos 30° + ..." returned "°^2": the
  plain-value path fed the raw question (° signs, command
  words) to the expression parser, which read ° as a
  symbol. "Find the value of sin 45°" -> "sqrt(2)·°/2".
- "^2" forms ("sin^2 30° + cos^2 30°", "sec^2 45° -
  tan^2 45°") fell to concept/similar fallbacks.
- "Simplify (1 - cos^2 A) / sin A" fell back; "Simplify
  sin A * cosec A" returned letter-soup
  "f·i^2·l·m·p·y·sin(A·csc(A))".
- "Prove that sin^2 A + cos^2 A = 1" answered "Not an
  identity": the proof stripper removed bare "prove" but
  left "that", which the parser read as t·h·a·t symbols
  (audit #161).
- Hindi "sin 30 डिग्री का मान" returned a Devanagari
  letter-product (audit #482, still live); Roman "cos 60
  degree ka maan kya hai?" fell back ("degree" singular
  missed the Wave-32 written-out block).

The new block reduces the question to a pure trig
expression (fillers stripped, fn^2 x -> (fn x)^2, fn A ->
fn(A), degrees converted) and parses ONLY when every
remaining word is a trig function or a single-letter
angle, so word problems can never be hijacked.
"""
import pytest

from api import _solve_friendly


def _res(question):
    res = _solve_friendly(question)
    assert "fallback" not in res, (
        f"{question!r} fell to a fallback layer: "
        f"{res.get('fallback_kind')} / {res.get('answer')}")
    return res


def _value(question, expected):
    res = _res(question)
    assert res.get("value") == pytest.approx(expected), (
        f"{question!r} -> {res.get('answer')!r}, "
        f"expected {expected}")


# --- Standard-angle evaluations (degrees, mixed forms) --------
def test_eval_sin30_plus_cos60():
    _value("Evaluate sin 30° + cos 60°", 1)


def test_eval_product_sum_identity_form():
    _value("Evaluate sin 60° cos 30° + sin 30° cos 60°", 1)


def test_eval_lone_value_with_filler_words():
    _value("Find the value of sin 45°", 2 ** 0.5 / 2)


def test_eval_mixed_powers():
    _value("Find the value of 2 tan^2 45° + cos^2 30° "
           "- sin^2 60°", 2)


# --- Identity-based evaluations -------------------------------
def test_eval_sin2_plus_cos2_degrees():
    _value("Evaluate sin^2 30° + cos^2 30°", 1)


def test_eval_sec2_minus_tan2():
    _value("Evaluate sec^2 45° - tan^2 45°", 1)


def test_eval_cos2_plus_sin2_45():
    _value("Evaluate cos^2 45° + sin^2 45°", 1)


# --- Symbolic identity simplifications -------------------------
def test_simplify_one_minus_cos2_over_sin():
    res = _res("Simplify (1 - cos^2 A) / sin A")
    assert "sin" in res["answer"] and "cos" not in \
        res["answer"]


def test_simplify_sin_times_cosec():
    # symbolic-simplify results carry no numeric "value"
    # (the established simplify-result shape) — check text.
    res = _res("Simplify sin A * cosec A")
    assert res["answer"] == "1"


def test_simplify_tan_times_cot():
    res = _res("Simplify tan A * cot A")
    assert res["answer"] == "1"


def test_simplify_sin2_plus_cos2_theta():
    res = _res("Simplify sin^2 theta + cos^2 theta")
    assert res["answer"] == "1"


# --- The flagship identity proof (audit #161) ------------------
def test_prove_sin2_plus_cos2_is_identity():
    res = _res("Prove that sin^2 A + cos^2 A = 1.")
    assert res["answer"].startswith("Identity verified")


def test_prove_non_identity_stays_rejected():
    res = _res("Prove that sin A + cos A = 1.")
    assert res["answer"] == "Not an identity"


# --- Hindi / Roman-Hindi value asks -----------------------------
def test_hindi_sin30_degree_maan():
    _value("sin 30 डिग्री का मान ज्ञात कीजिए।", 0.5)


def test_hindi_cos45_degree_maan():
    _value("cos 45 डिग्री का मान ज्ञात कीजिए।",
           2 ** 0.5 / 2)


def test_roman_hindi_cos60_degree_ka_maan():
    _value("cos 60 degree ka maan kya hai?", 0.5)


# --- Controls: previously exact forms stay exact ----------------
def test_control_plain_sin30():
    _value("sin 30", 0.5)


def test_control_degrees_written_out():
    _value("Evaluate tan 45 degrees + sin 90 degrees", 2)


def test_control_degrees_written_out_powers():
    _value("Evaluate sin^2 30 degrees + cos^2 30 degrees",
           1)


def test_control_ratio_from_ratio():
    res = _res("If sin A = 3/5, find cos A")
    assert "4/5" in res["answer"]


def test_control_heights_not_hijacked():
    res = _res("Find the height of a tower if the angle "
               "of elevation is 60 degrees from a point "
               "10 m away")
    assert "17.32" in res["answer"]
