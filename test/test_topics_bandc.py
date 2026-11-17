"""Topics Scale-Up — Band C (Classes 11-12 + applied maths).

Adds 259 topics from topics_bandc.py (267 -> 526 total):
Classes 11-12 depth (sets/relations/trig/complex numbers/
inequalities/P&C/binomial/sequences/conics/3D intro/limits/
derivatives/statistics/probability for Class 11; relations/
inverse trig/matrices/determinants/continuity/differential-
calculus/integrals/DEs/vectors/LPP/Bayes for Class 12) plus
applied/everyday maths placed in Class 11 (money/growth under
sequences-and-series, commercial/rates under statistics).

Every Band C starter was verified through the app's own solve
path while authoring (test_wave55_topics.py re-verifies every
one of them exactly, like all pre-existing topics). Three
authored topics were dropped before shipping because their
starters only passed through a non-deterministic salvage:
principal values of sec^-1(2), tan^-1(sqrt 3) and
sin^-1(-1/2) — the solver has no native path for them.

This file pins: the total count, no slug collisions with the
pre-existing library, EN + HI completeness of every new
topic, and the routing battery (natural student questions in
English / Hindi / Hinglish -> the right topic card through
the app's solve path).
"""
import pytest

from api import _solve_friendly
from topics_bandc import TOPICS_BANDC
from topics_data import TOPICS_BY_CLASS


@pytest.fixture(autouse=True)
def _w125_isolated_livebank(tmp_path, monkeypatch):
    """Wave 125 (test-only): this battery used to run against
    the tree's real ganitra_users.db, so a Wave 117 live-bank
    row recorded by an earlier test in the same suite run
    could be re-served here and flip an item — half of the
    second-derivative routing flake (the other half, the
    solver's nondeterministic prose parse, is fixed at the
    root in solver/calculus.py). Point the live bank at a
    throwaway DB and clear the answer caches — the same
    seam test_wave117 uses — so the battery measures
    routing, not suite history."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "bandc.db"))
    from solver.answer_cache import (clear_cache,
                                     clear_negative_cache)
    clear_cache()
    clear_negative_cache()
    yield

BANDC_COUNT = 283
BASE_COUNT = 267


def _bandc_topics():
    return [(cls, t) for cls, ts in TOPICS_BANDC.items()
            for t in ts]


def test_bandc_topic_count():
    assert sum(len(ts) for ts in TOPICS_BANDC.values()) \
        == BANDC_COUNT
    total = sum(len(ts) for ts in TOPICS_BY_CLASS.values())
    # Deploy-25 merge: Band B is wired into topics_data too,
    # so the combined total is 267 + 282 + 259 = 808.
    # Wave 142: Band C grows by 24 (14 Conic Sections fill +
    # 10 Application of Integrals) -> 283 and 832.
    assert total == 832


def test_no_slug_collisions_with_existing():
    bandc_slugs = {t["slug"] for _, t in _bandc_topics()}
    assert len(bandc_slugs) == BANDC_COUNT
    # The aggregation holds every slug exactly as often as the
    # pre-existing library did: Band C slugs appear once per
    # class list they were added to and nowhere else.
    all_slugs = [t["slug"] for ts in TOPICS_BY_CLASS.values()
                 for t in ts]
    for slug in bandc_slugs:
        assert all_slugs.count(slug) == 1, slug


def test_every_bandc_topic_is_complete_en_hi():
    for cls, t in _bandc_topics():
        assert t["name"] and t["idea"], t["slug"]
        # Hindi explanation present and actually Devanagari.
        assert t["idea_hi"], t["slug"]
        assert any("ऀ" <= ch <= "ॿ"
                   for ch in t["idea_hi"]), t["slug"]
        assert t["starter"] and t["answer"], t["slug"]
        assert len(t["steps"]) >= 2, t["slug"]


# --- Routing battery: natural asks -> Band C topic cards ---
# (question, expected topic_slug). The last four pin the
# translation wiring: Band C's Devanagari phrases must land
# those asks on the EXISTING topics, not steal them.

ROUTING_BATTERY = [
    ("what is the dot product of two vectors",
     "dot-product-of-two-vectors"),
    ("cross product kya hota hai vectors me",
     "cross-product-of-two-vectors"),
    ("what is a unit vector",
     "unit-vector-in-the-direction-of-a-vector"),
    ("angle between two vectors kaise nikale",
     "angle-between-two-vectors"),
    ("bayes theorem kya hota hai", "bayes-theorem-with-two-bags"),
    ("cramer's rule kya hai", "solving-a-system-by-cramers-rule"),
    ("what are eigenvalues of a matrix", "eigenvalues-of-a-matrix"),
    ("eigenvalues kaise nikale matrix ke",
     "eigenvalues-of-a-matrix"),
    ("rank of a matrix kaise nikale", "rank-of-a-matrix"),
    ("what is the trace of a matrix", "trace-of-a-matrix"),
    ("product rule kya hota hai differentiation me",
     "product-rule"),
    ("quotient rule samjhao", "quotient-rule"),
    ("integration by parts kaise karte hain",
     "integration-by-parts-x-sin-x"),
    ("integration by substitution kya hoti hai",
     "integration-by-substitution-x-e-x2"),
    ("second derivative kaise nikalte hai kisi function ka",
     "second-derivative-of-x4"),
    ("mean value theorem kya hai", "lagrange-mean-value-theorem"),
    ("depreciation kya hota hai", "depreciation-of-an-asset"),
    ("population growth kaise calculate karte hain",
     "population-growth-by-compound-interest"),
    ("discount percent kaise nikale", "discount-percent"),
    # Deploy-25 merge: in the combined library this
    # definitional ask is served by Band A's Class-8
    # "Marked Price and Discount" card (it owns the phrase);
    # the Band C computation topic keeps its own routes.
    ("marked price kya hota hai",
     "marked-price-and-discount"),
    ("pipes and cisterns ke sawal kaise kare", "pipes-and-cisterns"),
    ("time and work ke questions kaise solve kare",
     "time-and-work-together"),
    ("mathematical induction kya hota hai",
     "principle-of-mathematical-induction"),
    ("symmetric difference kya hota hai sets me",
     "symmetric-difference-of-sets"),
    ("power set kya hota hai", "power-set-and-its-elements"),
    ("difference of sets kya hota hai", "difference-of-sets"),
    ("sum of squares of natural numbers ka formula",
     "sum-of-squares-of-natural-numbers"),
    ("sum of cubes ka formula batao",
     "sum-of-cubes-of-natural-numbers"),
    # Deploy-25 merge: these three generic probability asks
    # are served by Band B's Class-10 cards in the combined
    # library (Band C's bare-word aliases were removed so
    # they cannot hijack the canonical Class-10 routes);
    # the Band C cards remain in the library.
    ("अधिवर्ष में 53 रविवार होने की प्रायिकता कैसे निकालते हैं",
     "leap-year-probability"),
    ("doublet kya hota hai probability me",
     "probability-of-a-doublet"),
    ("face card ki probability kaise nikale",
     "probability-of-a-face-card"),
    ("at most one head ka matlab probability me",
     "probability-of-at-most-one-head"),
    ("homogeneous differential equation kya hoti hai",
     "homogeneous-differential-equation"),
    ("order of a differential equation kaise nikale",
     "order-of-a-differential-equation"),
    ("degree of a differential equation kya hoti hai",
     "degree-of-a-differential-equation"),
    ("rate of change of volume kaise nikale sphere ka",
     "rate-of-change-of-volume-of-a-sphere"),
    ("successive discounts ka single discount kaise nikale",
     "single-equivalent-discount"),
    ("speed of the stream kaise nikale", "speed-of-the-stream"),
    ("price before gst kaise nikale",
     "price-before-gst-from-an-inclusive-price"),
    ("converting degrees to radians kaise kare",
     "converting-degrees-to-radians"),
    ("principal value kya hota hai inverse trig me",
     "principal-value-of-cos-inverse"),
    ("what is rational inequality", "rational-inequalities"),
    ("what is the magnitude of a vector", "magnitude-of-a-vector"),
    ("how to find the determinant of a diagonal matrix",
     "determinant-of-a-diagonal-matrix"),
    ("what is collinearity of three points",
     "collinearity-of-three-points"),
    ("integration of log x kaise kare", "integral-of-log-x"),
    ("coordinate planes ke equations kya hote hain",
     "equations-of-the-coordinate-planes"),
    ("even number of observations ka median kaise nikale",
     "median-of-an-even-number-of-observations"),
    # Deploy-25 merge: Band A's Class-7 card owns the plain
    # slug and serves this generic ask in the combined
    # library; the Band C card keeps the -advanced slug.
    ("range of data kaise nikale", "range-of-data"),
    ("chain rule kaise lagaye jab andar quadratic ho",
     "chain-rule-with-a-quadratic-inside"),
    ("limit of sin 3x / x kaise nikale", "limit-of-sin-3x-over-x"),
    ("derivative of tan x kya hota hai", "derivative-of-tan-x"),
    ("argument in the third quadrant kaise nikale complex "
     "number ka", "argument-in-the-third-quadrant"),
    # translation wiring — existing topics must keep these
    ("गुणोत्तर श्रेणी क्या होती है", "geometric-progressions"),
    ("आव्यूह क्या होता है", "matrix-operations"),
    ("समाकलन क्या होता है", "indefinite-integrals"),
    ("मापांक क्या होता है सम्मिश्र संख्या का",
     "modulus-and-conjugate"),
]


@pytest.mark.parametrize("question,slug", ROUTING_BATTERY)
def test_bandc_routing_battery(question, slug):
    res = _solve_friendly(question)
    assert res.get("source") == "topics", res.get("answer")
    assert res.get("topic_slug") == slug, res.get("topic_slug")
    assert res.get("fallback_kind") == "concept"
