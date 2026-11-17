"""Wave 103: audit-gap solver cleanup.

Wave 81's starter probing flagged eight solver gaps (the
concept layer could not author topics for them — a topic
needs a solver-verified worked example), and left exactly
one concept ask unanswered ("chaturbhuj ke chaaro kono ka
yog"). Wave 103 closes them with method schemas in
solver/gaps103.py, hooked at the router's failure-only tail
(the Wave 77/94 gate), plus ONE upgrade hook in
fallback.py for the polynomial-degree gap: there the
primary "simplify" path eats the words "degree of" into
the expression and returns a mangled expression as a
plausible answer, which the failure gate can never see —
so degree_upgrade (Wave 95 proof-upgrade precedent) fires
only on a strict degree ask whose answer is not already
the true degree.

Every test below goes through the real chat path
(api._solve_friendly) unless it is a layer-level guard on
solve_gaps103 / degree_upgrade themselves.
"""
import pytest

from api import _solve_friendly
from solver.gaps103 import degree_upgrade, solve_gaps103


def _ans(q):
    return str(_solve_friendly(q).get("answer", ""))


def _kind(q):
    return _solve_friendly(q).get("fallback_kind")


# --- Gap 1: quadrilateral / polygon angle sums -----------

def test_quad_sum_english():
    # Was hijacked by the "Sum and Difference of Angles"
    # trig topic card.
    r = _solve_friendly(
        "What is the sum of all the angles of a quadrilateral?")
    assert r.get("source") != "topics"
    assert r.get("answer") == "360°"


def test_quad_sum_hinglish_wave81_leftover():
    r = _solve_friendly(
        "chaturbhuj ke chaaro kono ka yog kitna hota hai?")
    assert r.get("source") != "topics"
    assert r.get("answer") == "360°"


def test_quad_sum_hindi():
    assert _ans("चतुर्भुज के चारों कोणों का योग कितना होता "
                "है?") == "360°"
    assert _ans("चतुर्भुज के कोणों का योग क्या है?") == "360°"


def test_polygon_sums():
    assert _ans("Find the sum of interior angles of a "
                "hexagon") == "720°"
    assert _ans("What is the sum of the exterior angles of "
                "a pentagon?") == "360°"
    assert _ans("What is the sum of the angles of a "
                "triangle?") == "180°"


def test_fourth_angle_english():
    assert _ans("Find the fourth angle of a quadrilateral "
                "if the other three angles are 90, 80 and "
                "100 degrees") == "90°"


def test_fourth_angle_hindi():
    assert _ans("चतुर्भुज के तीन कोण 90°, 80° और 100° हैं। "
                "चौथा कोण ज्ञात कीजिए।") == "90°"


def test_fourth_angle_hinglish():
    assert _ans("ek chaturbhuj ke teen kon 90, 80 aur 100 "
                "degree hai, chautha kon kitna "
                "hoga?") == "90°"


def test_ratio_angles_not_hijacked():
    # Ratio angles need the parts method, which this wave
    # does not claim — the ask must stay honestly unanswered
    # rather than be caught by the fourth-angle schema.
    assert _kind("The angles of a quadrilateral are in the "
                 "ratio 1:2:3:4. Find the largest "
                 "angle") == "not_found"


# --- Gap 2: occurrence counting --------------------------

def test_digit_in_range_english():
    assert _ans("How many times does the digit 3 occur in "
                "the numbers from 1 to 50?") == "15"
    assert _ans("How many times does the number 7 appear "
                "from 1 to 100?") == "20"


def test_digit_in_range_hindi():
    assert _ans("1 se 50 tak ki sankhyaon mein ank 3 kitni "
                "baar aata hai?") == "15"


def test_digit_in_range_bruteforce_crosscheck():
    # Independent brute force, not the schema's own method.
    for digit, lo, hi_n in [(3, 1, 50), (7, 1, 100),
                            (0, 1, 100), (9, 45, 210)]:
        want = sum(str(n).count(str(digit))
                   for n in range(lo, hi_n + 1))
        got = _ans(f"How many times does the digit {digit} "
                   f"occur in the numbers from {lo} to "
                   f"{hi_n}?")
        assert got == str(want)


def test_occurrence_in_data_list():
    assert _ans("How many times does 3 occur in the data "
                "3, 5, 3, 7, 3, 9?") == "3"


def test_occurrence_in_one_number():
    assert _ans("How many times does the digit 3 occur in "
                "the number 1333?") == "3"


def test_mode_not_hijacked():
    assert _ans("Find the mode of the data 3, 5, 3, 7, "
                "3") == "3"
    assert solve_gaps103(
        "Find the mode of the data 3, 5, 3, 7, 3") is None


# --- Gap 3: n(A) / set cardinality -----------------------

def test_n_of_a():
    assert _ans("Find n(A) if A = {1, 2, 3, 4, 5}") == "5"
    assert _ans("If A = {a, e, i, o, u}, find "
                "n(A)") == "5"


def test_how_many_elements():
    assert _ans("How many elements are in the set "
                "{2, 4, 6, 8, 10}?") == "5"


def test_cardinality_hindi_hinglish():
    assert _ans("samuchchay {1, 2, 3} mein kitne avayav "
                "hain?") == "3"
    assert _ans("समुच्चय A = {2, 4, 6} में कितने अवयव "
                "हैं?") == "3"


def test_cardinality_picks_named_set():
    assert _ans("Find n(A) if A = {1, 2} and B = "
                "{1, 2, 3}") == "2"


def test_set_operations_not_hijacked():
    assert _ans("If A = {1, 2, 3} and B = {2, 3, 4}, find "
                "A union B") == "{1, 2, 3, 4}"
    assert _ans("A set has 5 elements. How many subsets "
                "does it have?") == "32"
    assert solve_gaps103(
        "Find n(A union B) if A = {1, 2} and B = {2, 3}"
    ) is None


# --- Gap 4: polynomial degree ----------------------------

def test_degree_what_is_phrasing():
    # The Deploy-era junk: this used to come back as the
    # expression "2*x**2 + 5*x + 10".
    assert _ans("What is the degree of 3x^3 + 2x^2 + 5x + "
                "7?") == "3"
    assert _ans("What is the degree of x^3 + "
                "2x^2?") == "3"


def test_degree_existing_paths_untouched():
    assert _ans("Find the degree of the polynomial "
                "4x^2 + 1") == "2"
    assert _ans("Find the degree of 9x^5") == "5"
    assert _ans("What is the degree of the polynomial "
                "(x + 3)^2 (x^3 - 8)?") == "5"
    assert _ans("bahupad 5x^2 + 3x ki degree kya "
                "hai?") == "2"


def test_degree_differential_equation_not_upgraded():
    q = ("Find the order and degree of the differential "
         "equation (dy/dx)^2 + dy/dx + 1 = 0")
    assert _ans(q) == "Order = 1, Degree = 2"
    assert degree_upgrade(
        q, {"op": "simplify", "answer": "junk"}) is None


def test_degree_upgrade_only_when_wrong():
    # Already-correct answers are left byte-identical.
    assert degree_upgrade(
        "Find the degree of 9x^5",
        {"op": "evaluate", "answer": "5"}) is None
    out = degree_upgrade(
        "What is the degree of 3x^3 + 2x^2 + 5x + 7?",
        {"op": "simplify", "answer": "2*x**2 + 5*x + 10"})
    assert out is not None
    assert out["answer"] == "3"


# --- Gap 5: degree <-> radian ----------------------------

def test_deg_to_rad():
    assert "π/3" in _ans("Convert 60 degrees to radians")
    assert "π/4" in _ans("Convert 45 degrees to radians")
    assert _ans("180 degrees is equal to how many "
                "radians?").startswith("π")
    assert "π/2" in _ans("90 degree ko radian mein badlo")


def test_rad_to_deg():
    assert _ans("Convert pi/3 radians to degrees") == "60°"
    assert _ans("Convert 3pi/2 radians to degrees") == "270°"
    assert _ans("Convert 1 radian to degrees") == "57.3°"


def test_deg_rad_hindi():
    assert "π/3" in _ans("60 डिग्री को रेडियन में बदलिए")
    assert _ans("π/6 रेडियन को डिग्री में बदलिए") == "30°"


def test_arc_length_not_hijacked():
    # No "radian" word — the arc-length path keeps the ask.
    r = _solve_friendly(
        "Find the length of an arc of a circle with radius "
        "7 cm which subtends an angle of 60 degrees at the "
        "centre")
    assert r.get("fallback_kind") is None
    assert solve_gaps103(
        "Find the length of an arc of a circle with radius "
        "7 cm which subtends an angle of 60 degrees at the "
        "centre") is None


# --- Gap 6: quadrant identification ----------------------

def test_quadrant_four():
    assert "First" in _ans(
        "In which quadrant does the point (3, 4) lie?")
    assert "Second" in _ans(
        "In which quadrant does the point (-3, 5) lie?")
    assert "Third" in _ans(
        "bindu (-2, -7) kis chaturthansh mein sthit hai?")
    assert "Fourth" in _ans(
        "Which quadrant does the point (4, -2) lie in?")


def test_quadrant_hindi():
    assert "चतुर्थ" in _ans("बिंदु (5, -3) किस चतुर्थांश "
                            "में है?")


def test_quadrant_on_axis_is_honest():
    assert _ans("In which quadrant does the point (0, 5) "
                "lie?") == "y-axis"
    assert _ans("In which quadrant does the point (-4, 0) "
                "lie?") == "x-axis"


def test_quadrant_angle():
    assert "Third" in _ans(
        "In which quadrant does 200 degrees lie?")


def test_distance_not_hijacked():
    assert _ans("Find the distance of the point (5, 12) "
                "from the origin") == "13"


# --- Gap 7: sample space basics --------------------------

def test_sample_space_counts():
    assert _ans("How many outcomes are there when a die "
                "is thrown once?") == "6"
    assert _ans("ek sikka uchhalne par kitne parinaam "
                "sambhav hain?") == "2"
    assert _ans("एक पासा फेंकने पर कितने परिणाम संभव "
                "हैं?") == "6"
    assert _ans("How many outcomes when a coin is tossed "
                "twice?") == "4"


def test_sample_space_listing():
    assert _ans("What is the sample space when a coin is "
                "tossed once?") == "{H, T}"
    assert _ans("What is the sample space when a die is "
                "thrown once?") == "{1, 2, 3, 4, 5, 6}"


def test_sample_space_existing_paths_untouched():
    assert _ans("How many outcomes when two coins are "
                "tossed?") == "4"
    assert _ans("How many outcomes when two dice are "
                "thrown?") == "36"


def test_probability_not_hijacked():
    assert solve_gaps103(
        "A coin is tossed once. What is the probability "
        "of getting a head?") is None
    r = _solve_friendly(
        "A coin is tossed once. What is the probability "
        "of getting a head?")
    assert r.get("answer", "").startswith("1/2")


# --- Gap 8: f(n) evaluation ------------------------------

def test_function_value_of_phrasing():
    # The exact phrasing Wave 81 found failing.
    assert _ans("If f(x) = 3x + 1, find the value of "
                "f(4)") == "f(4) = 13"


def test_function_hinglish():
    assert _ans("f(x) = 2x - 5 hai to f(10) ka maan kya "
                "hoga?") == "f(10) = 15"


def test_function_more_forms():
    assert _ans("If f(x) = x^2 - 3x + 2, find "
                "f(-1)") == "f(-1) = 6"
    assert _ans("If f(x) = x^2 + 2x, find "
                "f(3)") == "f(3) = 15"
    assert _ans("If f(x) = 3x + 1, find "
                "f(2)") == "f(2) = 7"


# --- Global guards ----------------------------------------

def test_proof_and_why_asks_not_captured():
    # Pinned by test_wave95: a proof ask falls through.
    assert _kind("Prove that the sum of the angles of a "
                 "triangle is 180 degrees") == "not_found"
    assert solve_gaps103(
        "Prove that the sum of the angles of a triangle "
        "is 180 degrees") is None
    # Pinned by test_wave75 / test_wave81: why- and
    # explain-asks keep their concept topics.
    r = _solve_friendly(
        "tribhuj ke teeno kono ka yog 180 hi kyun hota "
        "hai?")
    assert r.get("source") == "topics"
    r = _solve_friendly(
        "sikka uchale to sample space kya banega samjhao?")
    assert r.get("source") == "topics"


def test_gibberish_still_not_found():
    assert _kind("blah blah ulta seedha kuch "
                 "bhi") == "not_found"


def test_nonmaths_still_nonmaths():
    assert _kind("what is the capital of "
                 "india") == "nonmaths"
