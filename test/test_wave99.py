"""Wave 99: the pi policy.

Suraj's rule (16 Nov 2026): true pi is the DEFAULT; 22/7 is
used ONLY where the question needs it — school mensuration
whose circular dimensions are designed for 22/7:

  * radius a positive multiple of 7, or the diameter it
    implies (2r) a multiple of 7 (r = 3.5 -> d = 7);
  * a stated diameter a multiple of 7;
  * a stated circumference a multiple of 22;
  * two-radius shapes (ring, frustum): EVERY radius must
    qualify;
  * mixed rule: heights / slant heights / angles never block
    and never trigger 22/7 — only circular dimensions decide.

In the 22/7 cases the answer is the clean textbook value
(154, not "49·pi ≈ 153.9380") and a working line shows
"pi = 22/7". Everywhere else the old true-pi output is
byte-identical. The rule lives in solver/pi_policy.py; every
mensuration computation in geometry.py / applied.py /
methods.py routes through it.
"""
import math

import pytest

from api import _solve_friendly
from solver.pi_policy import pi_choice, pi_value, use_227


def _ans(q):
    res = _solve_friendly(q) or {}
    return str(res.get("answer", "")), res.get("steps") or []


# --- the policy definition itself ------------------------------

@pytest.mark.parametrize("kw", [
    {"radius": 7}, {"radius": 14}, {"radius": 21}, {"radius": 70},
    {"radius": 3.5},          # derived diameter 7
    {"radius": 10.5},         # derived diameter 21
    {"diameter": 7}, {"diameter": 14}, {"diameter": 28},
    {"circumference": 22}, {"circumference": 44},
    {"circumference": 88},
    {"radii": [14, 7]}, {"radii": [21, 14]},
])
def test_policy_triggers(kw):
    assert use_227(**kw)
    val, used, reason = pi_choice(**kw)
    assert used and val == 22 / 7 and reason


@pytest.mark.parametrize("kw", [
    {"radius": 5}, {"radius": 10}, {"radius": 7.5},
    {"radius": 3}, {"radius": 0}, {"radius": -7},
    {"radius": 1.75},         # derived diameter 3.5 — not /7
    {"diameter": 10}, {"diameter": 15},
    {"circumference": 43}, {"circumference": 45},
    {"circumference": 31.4},
    {"radii": [14, 10]},      # only one radius qualifies
    {"radii": [10, 5]},
    {},
])
def test_policy_stays_true_pi(kw):
    assert not use_227(**kw)
    val, used, reason = pi_choice(**kw)
    assert not used and val == math.pi and reason is None


def test_pi_value_matches_choice():
    assert pi_value(radius=7) == 22 / 7
    assert pi_value(radius=10) == math.pi
    assert pi_value(circumference=44) == 22 / 7
    assert pi_value(circumference=40) == math.pi


# --- chat path: 22/7 cases give the clean textbook value -------

@pytest.mark.parametrize("question,want", [
    ("find the area of a circle with radius 7 cm", "154"),
    ("find the circumference of a circle with radius 7 cm", "44"),
    ("find the area of a circle with diameter 14 cm", "154"),
    ("find the area of a circle whose circumference is 44 cm", "154"),
    ("the circumference of a circle is 44 cm, find its radius", "7"),
    # C = 22: exact-Fraction paths (r = 3.5, area = 38.5 —
    # terminating decimals, never "7/2" / "77/2")
    ("find the area of a circle whose circumference is 22 cm", "38.5"),
    ("the circumference of a circle is 22 cm, find its radius", "3.5"),
    ("volume of a cylinder with radius 7 cm and height 10 cm", "1540"),
    # mixed: non-7 height does NOT block 22/7
    ("volume of a cylinder with radius 7 cm and height 5 cm", "770"),
    ("volume of a sphere with radius 21 cm", "38808"),
    ("surface area of a sphere with radius 7 cm", "616"),
    ("volume of a cone with radius 14 cm and height 6 cm", "1232"),
    ("volume of a hemisphere with radius 21 cm", "19404"),
    ("curved surface area of a cone with radius 7 cm and "
     "slant height 25 cm", "550"),
    ("circumference of a circle with diameter 28 cm", "88"),
    ("find the area of a circle with radius 3.5 cm", "38.5"),
    ("total surface area of a cylinder with radius 7 cm and "
     "height 10 cm", "748"),
    ("area of a sector of a circle with radius 7 cm and "
     "angle 90 degrees", "38.5"),
    ("area between two concentric circles with radii 14 cm "
     "and 7 cm", "462"),
    ("एक वृत्त की त्रिज्या 7 सेमी है, उसका क्षेत्रफल निकालो", "154"),
    ("circle ki trijya 7 cm hai, kshetrafal batao", "154"),
    ("circle ka vyas 14 cm hai, paridhi batao", "44"),
])
def test_227_answers_are_clean(question, want):
    ans, steps = _ans(question)
    assert ans.replace(" square units", "") == want or want in ans
    # the working shows pi = 22/7 somewhere
    assert any("22/7" in str(s) for s in steps), (question, steps)
    # and the symbolic true-pi form is gone
    assert "153.938" not in ans and "·pi ≈" not in ans


# --- chat path: true-pi cases are byte-identical ---------------

@pytest.mark.parametrize("question,want", [
    ("find the area of a circle with radius 10 cm",
     "100·pi ≈ 314.1593"),
    ("find the circumference of a circle with radius 5 cm",
     "10·pi ≈ 31.4159"),
    ("find the area of a circle with radius 7.5 cm",
     "56.25·pi ≈ 176.7146"),
])
def test_true_pi_answers_unchanged(question, want):
    ans, steps = _ans(question)
    assert ans == want
    assert not any("22/7" in str(s) for s in steps)


def test_ring_with_one_plain_radius_stays_true_pi():
    ans, _steps = _ans(
        "area between two concentric circles with radii 14 cm "
        "and 10 cm")
    assert ans == "301.593 square units"


# --- alternate methods survive the clean 22/7 answers ----------

@pytest.mark.parametrize("question,want_id", [
    ("Find the area of a circle with radius 7 cm", "diameter"),
    ("Find the circumference of a circle with radius 7 cm",
     "diameter"),
    ("Find the volume of a cylinder with radius 7 cm and "
     "height 10 cm", "base_area"),
    ("Find the volume of a cone with radius 7 cm and "
     "height 10 cm", "cone_third"),
])
def test_alternate_methods_offered_for_227_answers(question,
                                                    want_id):
    # The primary answer is exact now (no "≈"), but the Wave-12
    # alternate methods must still be offered, must agree with
    # the primary, and must show the 22/7 working.
    from solver.methods import alternate_methods
    from solver.router import solve_question
    primary = solve_question(question)
    by_id = {m["id"]: m
             for m in alternate_methods(question, primary)}
    assert want_id in by_id, (question, list(by_id))
    assert by_id[want_id]["answer"] == primary.get("answer")
    assert any("22/7" in s for s in by_id[want_id]["steps"])
