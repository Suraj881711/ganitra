"""Wave 74: root-cause fixes for the three CONFIRMED wrong
answers in the Wave 71 solver-health audit.

1. Misspelt "circumferance" computed the AREA (306.25pi)
   instead of the circumference (35pi): the mensuration
   intent test was an exact substring match on
   "circumference". Fixed with a stem-tolerant matcher
   (solver/expression_parser.wants_circumference) used by
   geometry's circle branch and the router's mensuration
   rewrites.
2. A cuboid capacity question was hijacked by its own
   "(1000 cm^3 = 1 litre)" hint: the api retry's appended
   "find the value" opened applied._wrapped_equation,
   which extracted the unit-conversion statement and
   "solved" it for the letter c of "cm". Fixed by (a)
   refusing measurement statements in _wrapped_equation
   and (b) a cuboid-capacity schema that reads
   long/wide/deep dimensions and answers in litres.
3. "1/7 ÷ 2/7" evaluated as ((1/7)/2)/7 = 1/98: clean_text
   flattened ÷ to / and the fraction divisor lost its
   grouping. Fixed in clean_text: a fraction literal after
   a division sign (÷, or a spaced /) is parenthesised.
"""
import re

from api import _solve_friendly


def _ans(q):
    return str(_solve_friendly(q).get("answer", ""))


def _num(ans):
    m = re.search(r"≈\s*(-?\d+(?:\.\d+)?)", ans)
    if m:
        return float(m.group(1))
    m = re.search(r"-?\d+(?:\.\d+)?", ans)
    return float(m.group(0)) if m else None


# --- Case 1: circumference vs area ---------------------------------

def test_circumferance_misspelt_is_circumference():
    a = _ans("the circumferance of a circle with radius "
             "17.5 cm is?")
    assert abs(_num(a) - 109.9557) < 0.01, a


def test_circumference_correct_spelling_still_works():
    a = _ans("the circumference of a circle with radius "
             "17.5 cm is?")
    assert abs(_num(a) - 109.9557) < 0.01, a


def test_circumfrence_with_diameter():
    a = _ans("circumfrence of a circle with diameter 28 cm")
    assert abs(_num(a) - 87.9646) < 0.01, a


def test_area_ask_still_area():
    a = _ans("area of a circle with radius 17.5 cm")
    assert abs(_num(a) - 962.1128) < 0.01, a


def test_area_from_circumference_both_spellings():
    for q in ("area of a circle whose circumference is "
              "44 cm",
              "area of a circle whose circumferance is "
              "44 cm"):
        a = _ans(q)
        assert abs(_num(a) - 154.062) < 0.01, (q, a)


# --- Case 2: capacity question vs its conversion hint ---------------

TANK = ("A water tank is 80 cm long, 40 cm wide and "
        "40 cm deep. How many litres of water can it "
        "hold? (1000 cm³ = 1 litre)")


def test_tank_capacity_with_hint():
    assert _ans(TANK) == "128 litres"


def test_tank_capacity_without_hint():
    q = TANK.split(" (")[0]
    assert _ans(q) == "128 litres"


def test_tank_capacity_in_metres():
    a = _ans("a tank is 2 m long, 1 m wide and 1 m deep. "
             "how many litres of water can it hold?")
    assert a == "2000 litres", a


def test_wrapped_equation_rejects_unit_statement():
    from solver.applied import _wrapped_equation
    out = _wrapped_equation(
        " a water tank is 80 cm long (1000 cm^3 = 1 litre) "
        "find the value ", "hindi_equation")
    assert out is None


def test_genuine_wrapped_equations_still_solve():
    assert _ans("समीकरण 3x - 4 = 11 को हल कीजिए") == "x = 5"
    assert _ans("x + 15 = 40 me x ki value kitni hai") \
        == "x = 25"


def test_genuine_equations_still_solve():
    assert _ans("solve x + 3 = 7") == "x = 4"
    assert _ans("2x + 5 = 11") == "x = 3"


# --- Case 3: fraction division ---------------------------------------

def test_fraction_division_cases():
    cases = {
        "Simplify: 1/7 ÷ 2/7": "1/2",
        "2/3 ÷ 4/5": "5/6",
        "3/4 ÷ 2": "3/8",
        "divide 1/7 by 2/7": "1/2",
        "1/2 ÷ 1/2": "1",
        "1/7 / 2/7": "1/2",
    }
    for q, want in cases.items():
        got = _ans(q)
        assert got == want, f"{q!r}: got {got!r}, want {want!r}"


def test_unspaced_slash_chain_keeps_left_to_right():
    # "1/2/3" is conventionally ((1/2)/3); only a fraction
    # after a real division sign gets grouped.
    assert _ans("1/2/3") == "1/6"
