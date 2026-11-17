"""Band B topics expansion (Classes 9-10) — pinning tests.

The expansion adds 282 topics (Class 9: +131, Class 10: +151)
from the standalone topics_bandb module, wired into
topics_data.TOPICS_BY_CLASS and concept_topics._ALIASES.

Pins:
- the tree's total topic count is 267 + 282 = 549, with the
  per-class Band B deltas exact;
- no Band B slug collides with a pre-existing slug in the
  same class (and Band B slugs are unique across the band);
- every new topic is complete in the topics_data schema
  (slug, name, chapter, starter, answer, idea, >= 2 steps).
  Note: the schema has no separate Hindi field — topic cards
  are English by the library's standing design, while chat
  routing accepts EN / Hindi / Hinglish asks;
- a routing battery subset: natural student questions reach
  the right new topic card through topic_concept_result;
- every new topic's starter solves through the app's own
  solve path with the stored answer verbatim (the full set
  is also re-verified by test_wave55_topics.py).
"""
import topics_bandb
import topics_data
from api import _solve_friendly
from concept_topics import topic_concept_result

BANDB_TOTAL = 282
EXPECTED_CLASS_TOTALS = {9: 162, 10: 205}
EXPECTED_BANDB_PER_CLASS = {9: 131, 10: 151}


def _bandb_topics():
    out = []
    for cls in sorted(topics_bandb.TOPICS_BY_CLASS_BANDB):
        for topic in topics_bandb.TOPICS_BY_CLASS_BANDB[cls]:
            out.append((cls, topic))
    return out


def test_bandb_counts():
    assert len(_bandb_topics()) == BANDB_TOTAL
    for cls, n in EXPECTED_BANDB_PER_CLASS.items():
        assert len(topics_bandb.TOPICS_BY_CLASS_BANDB[cls]) == n
    # Deploy-25 merge: Band C is wired into topics_data too,
    # so the combined count is 267 + 282 + 259 = 808.
    # Wave 142: +24 Band C topics -> 832.
    assert topics_data.TOPIC_COUNT == 832
    for cls, total in EXPECTED_CLASS_TOTALS.items():
        assert len(topics_data.TOPICS_BY_CLASS[cls]) == total


def test_no_slug_collisions_with_existing():
    bandb_slugs = {t["slug"] for _c, t in _bandb_topics()}
    assert len(bandb_slugs) == BANDB_TOTAL  # unique across the band
    for cls, topic in _bandb_topics():
        in_class = [t["slug"] for t in topics_data.TOPICS_BY_CLASS[cls]]
        assert in_class.count(topic["slug"]) == 1
    # Global disjointness: a Band B slug must not reuse ANY
    # pre-existing slug in ANY class — concept_topics._BY_SLUG
    # keeps the lowest class, so a reused slug would shadow
    # (or be shadowed by) the older topic in chat routing.
    bandb_ids = {id(t) for _c, t in _bandb_topics()}
    other_slugs = {
        t["slug"]
        for topics in topics_data.TOPICS_BY_CLASS.values()
        for t in topics
        if id(t) not in bandb_ids
    }
    assert not (bandb_slugs & other_slugs)


def test_every_bandb_topic_is_complete():
    for _cls, topic in _bandb_topics():
        assert topic["slug"] and topic["name"] and topic["chapter"]
        assert topic["starter"] and topic["answer"]
        assert topic["idea"]
        assert len(topic["steps"]) >= 2


def test_bandb_starters_solve_exactly():
    for _cls, topic in _bandb_topics():
        result = _solve_friendly(topic["starter"])
        assert result and result.get("answer"), topic["slug"]
        assert not result.get("fallback"), topic["slug"]
        assert result.get("fallback_kind") is None, topic["slug"]
        assert str(result["answer"]).strip() == topic["answer"], topic["slug"]


ROUTING_BATTERY = [
    ("What is a terminating decimal expansion?", "terminating-decimal-expansions"),
    ("Factor theorem kya hota hai?", "factor-theorem-finding-k"),
    ("Difference of cubes ka formula kya hai?", "difference-of-cubes"),
    # Deploy-25 merge: Band A's Class-8 topic owns the plain
    # slug and wins this generic ask in the combined library
    # (lowest-class-wins); the Band B card keeps the
    # -practice slug and its own routes.
    ("Area of a trapezium ka formula batao", "area-of-a-trapezium"),
    ("Volume of a hemisphere kaise nikale?", "hemisphere-volume-problems"),
    ("Missing value kaise nikale mean me?", "mean-with-a-missing-value"),
    ("Euclid's division algorithm kya hai?", "euclid-algorithm-for-large-numbers"),
    ("Cross multiplication method kya hota hai?", "cross-multiplication-method"),
    ("Nature of roots kaise check kare?", "nature-of-roots"),
    ("AP ka nth term from the end kaise nikale?", "nth-term-from-the-end"),
    ("Converse of Pythagoras theorem kya hai?", "converse-of-pythagoras-theorem"),
    ("Centroid kya hota hai triangle me?", "centroid-of-a-triangle"),
    ("Angle of depression kya hota hai?", "angle-of-depression-of-a-car"),
    ("Frustum kya hota hai?", "frustum-volume-variant"),
    ("Step deviation method kya hai?", "step-deviation-method"),
    ("Grouped median kaise nikale?", "grouped-median-variant-10"),
    ("Doublet kya hota hai probability me?", "probability-of-a-doublet"),
    ("Face card ki probability kaise nikale?", "probability-of-a-face-card"),
    ("Leap year me 53 Sundays ki probability kya hoti hai?", "leap-year-probability"),
    ("Exactly one head ki probability kya hoti hai?", "probability-of-exactly-one-head"),
]


def test_routing_battery_subset():
    for question, slug in ROUTING_BATTERY:
        result = topic_concept_result(question)
        assert result is not None, question
        assert result.get("topic_slug") == slug, question
