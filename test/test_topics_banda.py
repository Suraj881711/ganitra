"""Topics Expansion — Band A (Classes 0-8).

Suraj's order: take the concept topics from 267 towards
1000+. Band A adds 268 foundational / middle-school topics
(Classes 0-8) from topics_banda.py, wired into the concept
index in concept_topics.py only — topics_data's per-class
counts stay locked (test_wave55_topics.py) because the
/topics directory and its starter-verification gate live
there, while chat concept routing reads the concept index.

This suite pins:
- the honest counts: 268 band topics, concept index at
  267 + 268 = 535 entries;
- no band slug collides with an existing topics_data slug
  (or with another band slug), and band classes stay in
  0..8;
- every band topic is complete in the topics_data schema
  (slug, name, chapter, starter, answer, idea, >=2 steps)
  plus a non-empty Hindi idea (idea_hi);
- a routing battery: natural student asks (English, Hindi,
  Hinglish) reach the right band topic through the concept
  layer;
- the old routes are untouched: prime/HCF/Pythagoras asks
  still land on their original topics, the pinned Wave-75
  fall-through (quadrilateral angle-sum fact) still returns
  None at the layer, and concrete problems are never
  captured.
"""
import pytest

import concept_topics
import topics_banda
import topics_data
from concept_topics import topic_concept_result

BAND = [(c, t) for c in sorted(topics_banda.TOPICS_BANDA)
        for t in topics_banda.TOPICS_BANDA[c]]
EXPECTED_PER_CLASS = {0: 28, 1: 30, 2: 32, 3: 34, 4: 34,
                      5: 34, 6: 26, 7: 26, 8: 24}


def test_band_counts():
    assert len(BAND) == 268
    per_class = {c: len(topics_banda.TOPICS_BANDA[c])
                 for c in topics_banda.TOPICS_BANDA}
    assert per_class == EXPECTED_PER_CLASS
    # the concept index grew by exactly the band
    # (Deploy-25 merge: Bands B and C are also wired in, so
    # the combined index is 267 + 268 + 282 + 259 = 1076 and
    # topics_data holds 267 + 282 + 259 = 808)
    # Wave 142: +24 Band C topics -> 1100 and 832.
    assert len(concept_topics._ORDERED) == 1100
    assert topics_data.TOPIC_COUNT == 832


def test_no_slug_or_name_collisions():
    existing = {t["slug"] for _, t in topics_data.all_topics()}
    band_slugs = [t["slug"] for _, t in BAND]
    assert not (set(band_slugs) & existing)
    assert len(set(band_slugs)) == len(band_slugs)
    band_names = [t["name"] for _, t in BAND]
    assert len(set(band_names)) == len(band_names)


def test_band_classes_stay_in_band():
    assert all(0 <= c <= 8 for c, _ in BAND)


def test_every_band_topic_is_complete():
    for class_num, topic in BAND:
        assert topic["name"].strip()
        assert topic["idea"].strip()
        assert topic["idea_hi"].strip()
        assert len(topic["steps"]) >= 2
        assert all(s.strip() for s in topic["steps"])
        assert topic["starter"].strip()
        assert topic["answer"].strip()


def test_every_band_topic_is_in_the_index():
    for class_num, topic in BAND:
        hit = concept_topics._topic(topic["slug"])
        assert hit is not None, topic["slug"]
        # the index's copy is this band's own entry (band
        # slugs are new, so setdefault kept ours)
        assert hit[1] is topic


# --- Routing battery (layer level) -------------------------
# (question, expected topic_slug) — English, Hinglish and
# Devanagari asks a student would actually type.

BATTERY = [
    ("what is counting backwards", "counting-backwards"),
    ("tens and ones kya hota hai", "tens-and-ones"),
    ("what is skip counting", "skip-counting"),
    ("even and odd numbers kya hote hain",
     "even-and-odd-numbers-intro"),
    ("what is a pictograph", "pictographs-with-scale"),
    ("what is division as sharing", "division-as-sharing"),
    ("rounding to the nearest 10 kaise karte hain",
     "rounding-to-nearest-10"),
    ("tally marks kya hote hain", "data-tally-intro"),
    ("what is the numerator and denominator",
     "numerator-and-denominator"),
    ("long division kaise karte hain", "long-division-intro"),
    ("what are roman numerals", "roman-numerals-intro"),
    ("what is face value and place value",
     "face-value-and-place-value"),
    ("bar graphs kya hote hain", "bar-graphs-intro"),
    ("what are divisibility rules", "divisibility-rules"),
    ("what are equivalent fractions", "equivalent-fractions"),
    ("like and unlike fractions me antar batao",
     "like-and-unlike-fractions"),
    ("what is comparing decimals", "comparing-decimals"),
    ("decimals me tenths kya hota hai", "decimals-tenths"),
    ("what is elapsed time", "elapsed-time"),
    ("what is the unitary method", "unitary-method-intro"),
    ("types of angles batao", "types-of-angles"),
    ("complementary and supplementary angles kya hote hain",
     "pairs-of-angles-intro"),
    ("parallel and perpendicular lines kya hoti hain",
     "parallel-and-perpendicular-lines"),
    ("quadrilateral kya hota hai",
     "types-of-quadrilaterals-intro"),
    ("what is speed in maths", "speed-intro"),
    ("whole numbers kya hote hain", "whole-numbers-intro"),
    ("what is the distributive property",
     "distributive-property"),
    ("successor and predecessor kya hote hain",
     "successor-and-predecessor"),
    ("chaturbhuj kya hota hai", "types-of-quadrilaterals-intro"),
    ("what are intersecting lines", "intersecting-lines-intro"),
    ("integers in daily life samjhao", "integers-in-daily-life"),
    ("what is ratio in the simplest form",
     "ratio-in-simplest-form"),
    ("what is reciprocal of a fraction", "reciprocal-intro"),
    ("vyutkram kise kehte hain", "reciprocal-intro"),
    ("what is a transversal", "angles-of-a-transversal"),
    ("vertically opposite angles kya hote hain",
     "vertically-opposite-angles"),
    ("what is percentage increase",
     "percentage-increase-decrease"),
    ("what is cost price and selling price",
     "cost-price-and-selling-price"),
    ("area of a parallelogram ka formula kya hai",
     "area-of-a-parallelogram"),
    ("what is rotational symmetry", "rotational-symmetry"),
    ("square root by division method kaise nikale",
     "square-root-by-division-method"),
    ("what is cube root", "cube-roots-intro"),
    ("ghanmool kya hota hai", "cube-roots-intro"),
    ("what is marked price", "marked-price-and-discount"),
    ("factorisation by grouping samjhao",
     "factorisation-by-grouping"),
    ("area of a trapezium ka formula batao",
     "area-of-a-trapezium"),
    ("what is a pie chart", "pie-charts"),
    ("histogram kya hota hai", "histograms-intro"),
    ("what is general form of a number",
     "general-form-of-a-number"),
    ("वर्गमूल कैसे निकालते हैं division method से",
     "square-root-by-division-method"),
    ("चतुर्भुज किसे कहते हैं", "types-of-quadrilaterals-intro"),
    ("face value aur place value me kya antar hai",
     "face-value-and-place-value"),
    ("parallel lines aur perpendicular lines me antar batao",
     "parallel-and-perpendicular-lines"),
    ("what is the difference between successor and predecessor",
     "successor-and-predecessor"),
    ("how to find the lcm by division method",
     "lcm-by-division-method"),
    ("HCF by division method kaise nikale",
     "hcf-by-division-method"),
]


@pytest.mark.parametrize("question,slug", BATTERY)
def test_band_routing_battery(question, slug):
    res = topic_concept_result(question)
    assert res is not None, question
    assert res.get("source") == "topics"
    assert res.get("topic_slug") == slug, res.get("topic_slug")
    assert res.get("fallback_kind") == "concept"


# --- Old routes untouched -----------------------------------

@pytest.mark.parametrize("question,slug", [
    ("what is a prime number", "prime-and-composite-numbers"),
    ("HCF kaise nikale?", "hcf-and-lcm"),
    ("पाइथागोरस प्रमेय क्या है?", "pythagoras-theorem"),
    ("what is the formula of simple interest", "simple-interest"),
    ("what is the formula of speed distance and time",
     "speed-distance-and-time"),
])
def test_existing_routes_unchanged(question, slug):
    res = topic_concept_result(question)
    assert res is not None
    assert res.get("topic_slug") == slug


def test_pinned_fall_through_still_falls_through():
    # Wave 75 pins this fact ask (quadrilateral angle sum) to
    # fall through to the concepts.py card — Band A's
    # quadrilateral topic must not capture it.
    assert topic_concept_result(
        "chaturbhuj ke chaaro kono ka yog kitna hota hai?") is None


@pytest.mark.parametrize("question", [
    "Find the mean of 3, 6, 9, 12.",
    "what is the HCF of 12 and 18",
    "using the quadratic formula solve x^2 - 3x + 2 = 0",
    "Sphere ka radius 7 cm hai to uska surface area find karo?",
])
def test_concrete_problems_never_captured(question):
    assert topic_concept_result(question) is None
