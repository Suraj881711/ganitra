"""Wave 55 tests — the per-class topic directory on /topics.

Suraj's asks: "Topics bada do 100+ or add karo", then "100 se
jyada topic or add karo" (target raised to 200+), then "Topic
solve karne kaa tarika daalo" (every topic must carry HOW TO
SOLVE it). This suite is the quality gate:

- the honest count: 267 class topics (per-class counts locked;
  226 from Wave 55 + 4 restored at merge-3 — the topics Wave 55
  dropped because their starters did not solve then: mutually
  exclusive events, union of events, geometric mean, function
  composition — all four solve EXACTLY after Waves 56/58 —
  + 37 added by Wave 81: the definition topics the Wave 75
  concept layer needed — theorem, derivative/limit
  definitions, ratio/proportion, sample space, ogive, pi,
  logarithms, ...),
  on top of the 17 legacy subject cards;
- every topic has a method section (idea + >=2 plain steps) and
  a worked example with a stored verified answer;
- EVERY example solves EXACTLY through the app's own solve path
  (api._solve_friendly): non-empty answer, fallback falsy,
  fallback_kind None — bank/concept/similar/guide/AI answers do
  NOT count, exactly the gate the wave was built under;
- every topic's parent chapter exists in board_data for that
  class (the card link target is real);
- slugs and names are unique per class;
- /topics renders the directory: topic names from every class,
  method steps, worked examples and chapter links all present,
  and the 17 legacy cards still carry their method + example.
"""
import re

import pytest

import board_data
import topics_data
from api import _solve_friendly

# Deploy-25 merge: Band B adds 9:+131, 10:+151 and Band C
# adds 11:+144, 12:+115 to the original per-class counts.
EXPECTED_PER_CLASS = {6: 22, 7: 32, 8: 33, 9: 162, 10: 205, 11: 213, 12: 165}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_topic_count_is_200_plus_and_honest():
    assert topics_data.TOPIC_COUNT >= 200
    per_class = {c: len(topics_data.topics_for_class(c))
                 for c in topics_data.CLASS_NUMBERS}
    assert per_class == EXPECTED_PER_CLASS
    assert topics_data.TOPIC_COUNT == sum(EXPECTED_PER_CLASS.values())


def test_every_topic_is_complete():
    for class_num, topic in topics_data.all_topics():
        assert topic["name"].strip()
        assert topic["idea"].strip()
        assert len(topic["steps"]) >= 2
        assert all(s.strip() for s in topic["steps"])
        assert topic["starter"].strip()
        assert topic["answer"].strip()


def test_slugs_and_names_unique_per_class():
    for class_num in topics_data.CLASS_NUMBERS:
        topics = topics_data.topics_for_class(class_num)
        assert len({t["slug"] for t in topics}) == len(topics)
        assert len({t["name"] for t in topics}) == len(topics)


def test_every_parent_chapter_exists():
    valid = {(c, ch["slug"]) for c in board_data.CHAPTERS
             for ch in board_data.CHAPTERS[c]}
    for class_num, topic in topics_data.all_topics():
        assert (class_num, topic["chapter"]) in valid, topic["name"]


@pytest.mark.parametrize("class_num,name,starter", [
    (c, t["name"], t["starter"]) for c, t in topics_data.all_topics()
])
def test_every_example_solves_exactly(class_num, name, starter):
    """THE quality gate: the worked example must be a pure solver
    answer — not bank, not fallback, not AI."""
    result = _solve_friendly(starter)
    answer = (result.get("answer") or "").strip()
    assert answer, (class_num, name, starter)
    assert not result.get("fallback"), (class_num, name, starter)
    assert not result.get("fallback_kind"), (
        class_num, name, starter, result.get("fallback_kind"))


def test_topics_page_renders_the_directory(client):
    resp = client.get("/topics")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    # one topic name from every class
    for name in ("Perimeter of a Square", "Simple Interest",
                 "Compound Interest", "Heron&#39;s Formula",
                 "Discriminant and Nature of Roots",
                 "Binomial Expansion", "Linear Programming"):
        assert name in html
    # method steps and a worked example are rendered
    assert "Divide the larger number by the smaller" in html
    assert "Find the HCF of 135 and 225" in html
    # chapter links are real directory links
    assert 'href="/board/10/real-numbers"' in html
    assert 'href="/board/6/number-play"' in html
    # the count of rendered topic cards matches the data
    cards = re.findall(r'href="/board/\d+/[a-z0-9-]+"', html)
    assert len(cards) == topics_data.TOPIC_COUNT


def test_legacy_subject_cards_kept_their_methods(client):
    html = client.get("/topics").get_data(as_text=True)
    # legacy cards now carry a method line and an example each
    assert "Method: Work step by step" in html
    assert "Example: Find the Taylor series of e^x" in html
    assert "Example: Convert 5 km into metres" in html
