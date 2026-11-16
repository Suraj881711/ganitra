"""Wave 81: concept-library content gaps closed.

Wave 75's notes recorded 42 real concept asks (from the
Wave 71 audit's CONCEPT rows) that fell through the
concept layer because topics_data.py had NO matching
topic — theorem/derivative/limit definitions, ratio vs
proportion, sample space, radius, pi, logarithm, ogive,
and more. This wave adds the 37 missing topics (230 -> 267)
in the exact Wave 55 format — method idea + steps + one
worked example verified through the app's own solve path
(test_wave55_topics.py re-verifies every starter,
including the new ones).

The matcher itself is unchanged in logic: the only
concept_topics.py edits are DATA rows (phrase/token
aliases, difference pairs, two Roman-Hindi phrase
translations) for asks whose content is a single word the
scorer can never reach (it needs >= 2 content hits) —
documented row by row in ganitra-wave81-notes.md.

41 of the 42 asks now answer from topics. The one that
stays is honest: "chaturbhuj ke chaaro kono ka yog kitna
hota hai?" asks for a FACT (a quadrilateral's angle sum)
and no topic can be authored for it — the Wave 55 format
requires a solver-verified worked example and the solver
has no quadrilateral-angle path at all (11 phrasings
tried). It keeps today's concepts.py card.
"""
import pytest

from api import _solve_friendly
from concept_topics import topic_concept_result

# --- The Wave 75 fall-through asks, now answered ---------
# (question, expected topic_slug)

CONCEPT_ASKS_81 = [
    # theorem — Class 9 Euclid topic
    ("what is a theorem", "theorem"),
    ("pramey kya hota hai?", "theorem"),
    ("प्रमेय किसे कहते हैं?", "theorem"),
    # derivative / limit definitions — Class 11
    ("derivative kya hota hai yr?", "derivative-of-a-function"),
    ("bhai ye derivative hota kya hai, dimag kharab ho gaya?",
     "derivative-of-a-function"),
    ("limit kya hoti hai maths me?", "limit-of-a-function"),
    # degree of a polynomial — Class 10
    ("polynomial ki degree kya hoti hai?",
     "degree-of-a-polynomial"),
    # coordinate geometry — Class 9
    ("coordinate geometry kya hai, simple me samjhao?",
     "coordinate-geometry"),
    ("quadrant kya hote hain coordinate plane me?",
     "quadrants-in-the-coordinate-plane"),
    # sets — Class 11
    ("subset (upasamuchchay) kya hota hai?", "subsets"),
    ("cardinal number of set matlab kya?",
     "cardinal-number-of-a-set"),
    ("empty set aur universal set kya hote hain?",
     "empty-set-and-universal-set"),
    # probability — Class 10
    ("impossible event aur certain event kya hote hain?",
     "impossible-and-certain-events"),
    ("sikka uchale to sample space kya banega samjhao?",
     "sample-space"),
    # mensuration words — Class 8
    ("aayatan (volume) kya hota hai?", "volume"),
    # pi / ratio / discount — Class 7
    ("ek batao — pi (π) kya hai aur value kitni hoti hai?", "pi"),
    ("anupaat kise kehte hain?", "ratio"),
    ("discount kese kaam karta hai dukaan par?", "discount"),
    # logarithm — Class 12
    ("log (logarithm) kya hota hai simple bhasha me?",
     "logarithms"),
    # statistics words — Class 9/10
    ("data kya hota hai statistics me?", "data-in-statistics"),
    ("class interval kya hota hai?", "class-intervals"),
    ("frequency (barambarta) kya hoti hai?", "frequency"),
    ("ogive kya hota hai?", "ogive"),
    # functions — Class 11
    ("function kya hota hai maths me?", "function"),
    ("domain aur range kya hote hain function ke?",
     "domain-and-range-of-a-function"),
    # degrees and radians / iota — Class 11
    ("ek degree kitne radian hota hai?", "degrees-and-radians"),
    ("iota (i) kya hai aur kyun banaya gaya?",
     "iota-the-imaginary-unit"),
    # rational numbers — Class 7 (exact-name topic wins over
    # the three operations/properties topics that used to tie)
    ("परिमेय संख्या क्या होती है?", "rational-numbers"),
    ("parimey sankhya matlab kya hota hai yr?",
     "rational-numbers"),
    ("define a rational number", "rational-numbers"),
    # radius — Class 9
    ("वृत्त की त्रिज्या किसे कहते हैं?", "radius-of-a-circle"),
    ("vritt ki trijya kya hoti hai?", "radius-of-a-circle"),
    # equilateral triangle — Class 7
    ("समबाहु त्रिभुज किसे कहते हैं?", "equilateral-triangle"),
    ("what is an equilateral triangle?", "equilateral-triangle"),
]


@pytest.mark.parametrize("question,slug", CONCEPT_ASKS_81)
def test_wave81_concept_asks_answered_from_topics(question, slug):
    res = _solve_friendly(question)
    assert res.get("source") == "topics", res.get("answer")
    assert res.get("topic_slug") == slug, res.get("topic_slug")
    assert res.get("fallback_kind") == "concept"
    from topics_data import TOPICS_BY_CLASS
    topic = next(t for ts in TOPICS_BY_CLASS.values()
                 for t in ts if t["slug"] == slug)
    assert topic["name"] in str(res.get("answer", ""))
    steps = res.get("steps") or []
    assert any(s.startswith("Example") for s in steps), steps
    assert any(topic["answer"] in s for s in steps), steps


# --- Difference asks composed from the new topics --------

DIFFERENCE_ASKS_81 = [
    ("ratio aur proportion me kya fark hai?",
     "ratio", "proportion"),
    ("congruent aur similar triangles me kya fark hai?",
     "congruent-triangles", "similar-triangles"),
    ("surface area aur volume me kya antar hai?",
     "surface-area", "volume"),
    ("sequence aur series me kya antar hai?",
     "sequence", "series"),
    ("rekha aur rekha khand me kya antar hai?",
     "line", "line-segment"),
    ("वर्ग और आयत में क्या अंतर है?", "square", "rectangle"),
    ("what is the difference between a square and a rectangle?",
     "square", "rectangle"),
]


@pytest.mark.parametrize("question,slug_a,slug_b",
                         DIFFERENCE_ASKS_81)
def test_wave81_difference_answers(question, slug_a, slug_b):
    res = _solve_friendly(question)
    assert res.get("source") == "topics", res.get("answer")
    assert res.get("topic_slug") == slug_a, res.get("topic_slug")
    assert res.get("topic_slug_b") == slug_b, \
        res.get("topic_slug_b")


# --- The one honest leftover -------------------------------

def test_quadrilateral_angle_sum_stays_off_topics():
    # No solver-verifiable worked example exists for a
    # quadrilateral angle-sum topic (the solver has no such
    # path), so the layer must keep returning None and the
    # ask keeps its concepts.py card — not a topics answer.
    assert topic_concept_result(
        "chaturbhuj ke chaaro kono ka yog kitna hota hai?"
    ) is None
    res = _solve_friendly(
        "chaturbhuj ke chaaro kono ka yog kitna hota hai?")
    assert res.get("source") != "topics"


# --- Route guards: older topics keep their asks -----------
# The new aliases/pairs must not steal asks that already had
# a home (the bare "theorem" alias is the risky one — the
# protective "remainder theorem" / "logarithmic functions"
# rows exist precisely for these).

ROUTE_GUARDS_81 = [
    ("remainder theorem kya hai", "remainder-theorem"),
    ("pythagoras theorem kya hai", "pythagoras-theorem"),
    ("derivative of trigonometric functions kya hota hai",
     "derivative-of-trigonometric-functions"),
    ("derivatives of logarithmic functions kya hai",
     "derivatives-of-logarithmic-functions"),
    ("direct proportion kya hota hai", "direct-proportion"),
    ("operations on rational numbers kya hai",
     "operations-on-rational-numbers"),
]


@pytest.mark.parametrize("question,slug", ROUTE_GUARDS_81)
def test_wave81_existing_routes_preserved(question, slug):
    res = topic_concept_result(question)
    assert res is not None, question
    assert res.get("topic_slug") == slug, res.get("topic_slug")


def test_wave81_direction_ratios_not_hijacked():
    # Pre-existing tie between "Direction Ratios of a Line"
    # and "Direction Cosines and Direction Ratios" makes the
    # layer abstain; the new ratio topic must not grab it.
    res = topic_concept_result("direction ratios kya hai")
    assert res is None or res.get("topic_slug") != "ratio"


# --- Hijack guards: concrete problems ----------------------

LAYER_NONE_81 = [
    "find the volume of a cube with side 5 cm",
    "find the volume of a cuboid with length 9 cm, "
    "breadth 6 cm and height 5 cm",
    "find the derivative of x^3",
    "what is the ratio of 20 to 30",
    "The value of log base 2 of 32 is (A) 3 (B) 4 (C) 5 (D) 6",
    "draw an ogive for the following data",
]


@pytest.mark.parametrize("question", LAYER_NONE_81)
def test_wave81_layer_never_captures_concrete_problems(question):
    assert topic_concept_result(question) is None


NUMERIC_SOLVES_81 = {
    "find the derivative of x^3": "3·x^2",
    "what is the ratio of 20 to 30": "2 : 3",
    "what is the value of log base 2 of 32?": "5",
    "find the number of subsets of a set having 4 elements": "16",
    "find the volume of a cube with side 5 cm": "125",
}


@pytest.mark.parametrize("question,want",
                         NUMERIC_SOLVES_81.items())
def test_wave81_concrete_problems_still_solve(question, want):
    res = _solve_friendly(question)
    assert res.get("source") != "topics"
    assert res.get("fallback_kind") in (None, "salvage"), \
        res.get("fallback_kind")
    assert want in str(res.get("answer", "")), res.get("answer")
