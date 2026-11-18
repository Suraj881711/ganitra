"""Wave 164: end-of-test diagnostic card for the chat test.

The Wave-124 chat test used to end with a score, the counts
and the weak topics. Wave 164 (adoption #2 of the Wave-162
all-AI comparison, from Gemini's test summaries) upgrades
that end card into a diagnostic built ONLY from this test's
recorded outcomes:

- a per-topic breakdown (Sahi / Galat / Dekha per topic,
  Skip shown when it happened) when more than one topic
  was attempted;
- the weakest 1–2 topics named plainly, ranked by
  not-right count (wrong + answer-dekha — a topic the
  student kept peeking at counts as weak too);
- one concrete next step naming the weakest topic and
  pointing at the Wave-87 practice entry ("My Weak
  Topics" in the Mistake Notebook — the wrong answers of
  this very test are already recorded there);
- a one-question test stays minimal: no breakdown, no
  practice line.

Pinned here: the breakdown numbers match the attempts
EXACTLY (unit states + full runs through handle_message),
the ranking and its tie-breaks, the answer-dekha cases,
all-correct / all-wrong runs, the language of the card
(en / roman / dev), mid-test behaviour untouched (instant
verdicts, the Wave-160 test_verdict flag), and the Wave-124
pins still holding (run test_wave124.py alongside).
"""
import time

import chat_test


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #

def _state(flavour, topics, outcomes):
    return {"flavour": flavour, "started_at": time.time(),
            "index": len(outcomes),
            "items": [{"topic_label": t} for t in topics],
            "outcomes": [{"given": "", "outcome": o}
                         for o in outcomes]}


def _lines(state, stopped=False):
    return chat_test._result_lines(state, stopped=stopped)


def _expected_rows(topics, outcomes):
    """Independent re-derivation of the per-topic counts
    (written out here, not imported, so the assertions are
    a real cross-check of chat_test._topic_rows)."""
    rows, order = {}, []
    for topic, outcome in zip(topics, outcomes):
        if topic not in rows:
            rows[topic] = {"correct": 0, "wrong": 0,
                           "dekha": 0, "skip": 0}
            order.append(topic)
        if outcome in ("seen", "solved"):
            rows[topic]["dekha"] += 1
        else:
            rows[topic][outcome] += 1
    return [(t, rows[t]) for t in order]


# ------------------------------------------------------------------ #
# Unit: the diagnostic content matches the attempts exactly
# ------------------------------------------------------------------ #

def test_breakdown_matches_attempts_exactly():
    topics = ["Algebra", "Algebra", "Geometry", "Geometry",
              "Arithmetic", "Arithmetic"]
    outcomes = ["correct", "wrong", "wrong", "seen",
                "correct", "skip"]
    lines = _lines(_state("en", topics, outcomes))
    joined = "\n".join(lines)
    assert "Score: 2/6" in joined
    assert "Topic-wise:" in lines
    head = lines.index("Topic-wise:")
    # Breakdown rows sit directly under the header, in
    # first-attempt order, with the exact attempt counts.
    assert lines[head + 1] == \
        "Algebra — Correct 1 • Wrong 1 • Dekha 0"
    assert lines[head + 2] == \
        "Geometry — Correct 0 • Wrong 1 • Dekha 1"
    assert lines[head + 3] == \
        "Arithmetic — Correct 1 • Wrong 0 • Dekha 0 • Skip 1"
    # Weakest first: Geometry (1 wrong + 1 dekha = 2 not
    # right) beats Algebra (1). Arithmetic never went wrong,
    # so it is NOT named weak.
    assert "Weak topics: Geometry, Algebra" in lines
    assert "Geometry: 2 did not go right" in joined
    assert "My Weak Topics" in joined
    assert "Mistake Notebook" in joined


def test_weakest_ranking_tie_breaks():
    # All three topics have bad = 2; wrong count breaks the
    # tie (2 wrong > 1 wrong + 1 dekha > 2 dekha), and only
    # the top 2 are named.
    topics = ["Alpha", "Alpha", "Beta", "Beta",
              "Gamma", "Gamma"]
    outcomes = ["wrong", "seen", "wrong", "wrong",
                "seen", "solved"]
    lines = _lines(_state("en", topics, outcomes))
    assert "Weak topics: Beta, Alpha" in lines
    joined = "\n".join(lines)
    assert "Beta: 2 did not go right" in joined
    assert "Gamma: 2 did not go right" not in joined


def test_dekha_only_topic_counts_as_weak():
    topics = ["Algebra", "Geometry", "Geometry"]
    outcomes = ["correct", "seen", "solved"]
    lines = _lines(_state("en", topics, outcomes))
    joined = "\n".join(lines)
    assert "Answer dekha 2" in joined  # totals line intact
    assert "Geometry — Correct 0 • Wrong 0 • Dekha 2" in lines
    assert "Weak topics: Geometry" in lines
    assert "Geometry: 2 did not go right" in joined


def test_skip_only_topic_is_not_weak():
    topics = ["Algebra", "Geometry"]
    outcomes = ["correct", "skip"]
    lines = _lines(_state("en", topics, outcomes))
    assert "No topic went wrong 🎉" in lines
    assert "Geometry — Correct 0 • Wrong 0 • Dekha 0 • Skip 1" \
        in lines
    assert not any("My Weak Topics" in ln for ln in lines)


def test_all_correct_has_no_practice_line():
    topics = ["Algebra", "Geometry", "Algebra"]
    outcomes = ["correct", "correct", "correct"]
    lines = _lines(_state("en", topics, outcomes))
    assert "Topic-wise:" in lines  # breakdown still shown
    assert "No topic went wrong 🎉" in lines
    assert not any("My Weak Topics" in ln for ln in lines)


def test_single_topic_no_breakdown_but_practice_line():
    topics = ["Algebra", "Algebra", "Algebra"]
    outcomes = ["wrong", "correct", "wrong"]
    lines = _lines(_state("en", topics, outcomes))
    assert "Topic-wise:" not in lines
    assert "Weak topics: Algebra" in lines
    joined = "\n".join(lines)
    assert "Algebra: 2 did not go right" in joined
    assert "My Weak Topics" in joined


def test_single_question_test_stays_minimal():
    lines = _lines(_state("en", ["Algebra"], ["wrong"]))
    joined = "\n".join(lines)
    assert "Score: 0/1" in joined
    assert "Weak topics: Algebra" in lines
    assert "Topic-wise:" not in lines
    assert "My Weak Topics" not in joined
    lines = _lines(_state("en", ["Algebra"], ["correct"]))
    assert "No topic went wrong 🎉" in lines
    assert "Topic-wise:" not in lines


def test_stopped_partial_card_uses_reached_only():
    topics = ["Algebra", "Geometry", "Algebra", "Geometry",
              "Arithmetic"]
    outcomes = ["wrong", "wrong", "correct"]
    state = _state("en", topics, outcomes)
    state["index"] = 3
    lines = _lines(state, stopped=True)
    joined = "\n".join(lines)
    assert "Score: 1/3" in joined  # reached = 3, not 5
    assert "2 questions were left." in lines
    # Breakdown covers only the 3 reached questions.
    assert "Algebra — Correct 1 • Wrong 1 • Dekha 0" in lines
    assert "Geometry — Correct 0 • Wrong 1 • Dekha 0" in lines
    assert not any("Arithmetic" in ln for ln in lines)
    assert "My Weak Topics" in joined


# ------------------------------------------------------------------ #
# Unit: the card speaks the student's language
# ------------------------------------------------------------------ #

def test_roman_card_lines():
    topics = ["Algebra", "Geometry", "Algebra"]
    outcomes = ["wrong", "wrong", "wrong"]
    lines = _lines(_state("roman", topics, outcomes))
    assert "Topic ke hisaab se:" in lines
    assert "Algebra — Sahi 0 • Galat 2 • Dekha 0" in lines
    assert "Geometry — Sahi 0 • Galat 1 • Dekha 0" in lines
    assert "Kamzor topic: Algebra, Geometry" in lines
    joined = "\n".join(lines)
    assert "Algebra me 2 sahi nahi hue" in joined
    assert "iski practice karein?" in joined
    assert "My Weak Topics" in joined


def test_devanagari_card_lines():
    topics = ["Algebra", "Geometry", "Algebra"]
    outcomes = ["wrong", "seen", "correct"]
    lines = _lines(_state("dev", topics, outcomes))
    assert "विषय के हिसाब से:" in lines
    # Algebra: wrong + correct. Geometry: seen (देखा).
    assert "Algebra — सही 1 • गलत 1 • देखा 0" in lines
    assert "Geometry — सही 0 • गलत 0 • देखा 1" in lines
    # Both have bad = 1; the tie breaks on wrong count, so
    # Algebra (1 wrong) outranks Geometry (0 wrong).
    assert "कमज़ोर विषय: Algebra, Geometry" in lines
    joined = "\n".join(lines)
    assert "Algebra में 1 सही नहीं हुए" in joined
    assert "इसका अभ्यास करें?" in joined
    assert "My Weak Topics" in joined


# ------------------------------------------------------------------ #
# End to end: full runs through handle_message
# ------------------------------------------------------------------ #

def _run_plan(session, plan):
    """Drive one chat test in a bare session dict. `plan`
    is a list of per-question actions: "correct", "wrong",
    "seen", "solve", "skip". Returns (items, payloads)."""
    started = chat_test.handle_message(
        session, None, 1, f"{len(plan)} sawal ka test do",
        "en")
    assert started is not None and started["ok"] is True
    state = session[chat_test._session_key(1)]
    items = list(state["items"])
    assert len(items) == len(plan)
    payloads = []
    for i, action in enumerate(plan):
        item = items[i]
        if action == "correct":
            text = str(item["answer"])
        elif action == "wrong":
            text = "987654321"
        elif action == "seen":
            text = "answer batao"
        elif action == "solve":
            text = "solve karke do"
        else:
            text = "skip"
        payloads.append(chat_test.handle_message(
            session, None, 1, text, "en"))
    return items, payloads


def test_full_run_diagnostic_matches_attempts():
    session = {}
    plan = ["correct", "wrong", "seen", "skip", "correct"]
    items, payloads = _run_plan(session, plan)
    topics = [it["topic_label"] for it in items[:len(plan)]]
    outcomes = ["correct", "wrong", "seen", "skip", "correct"]
    final = payloads[-1]["result"]
    lines = [final["answer"]] + list(final["steps"])
    joined = "\n".join(lines)
    assert "Score: 2/5" in joined
    rows = _expected_rows(topics, outcomes)
    if len(rows) > 1:
        assert "Topic-wise:" in lines
        for topic, r in rows:
            want = (f"{topic} — Correct {r['correct']} • "
                    f"Wrong {r['wrong']} • Dekha {r['dekha']}")
            if r["skip"]:
                want += f" • Skip {r['skip']}"
            assert want in lines, want
    else:
        assert "Topic-wise:" not in lines
    # Weakest ranking recomputed independently.
    weak = [(t, r) for t, r in rows
            if r["wrong"] + r["dekha"] > 0]
    weak.sort(key=lambda tr: (-(tr[1]["wrong"]
                                 + tr[1]["dekha"]),
                              -tr[1]["wrong"]))
    assert weak  # the plan guarantees a wrong and a seen
    top = weak[0]
    want_weak = "Weak topics: " + ", ".join(
        t for t, _r in weak[:2])
    assert want_weak in lines
    bad = top[1]["wrong"] + top[1]["dekha"]
    assert f"{top[0]}: {bad} did not go right" in joined
    assert "My Weak Topics" in joined


def test_full_run_all_correct_no_weak_no_practice():
    session = {}
    plan = ["correct", "correct", "correct"]
    _items, payloads = _run_plan(session, plan)
    final = payloads[-1]["result"]
    lines = [final["answer"]] + list(final["steps"])
    joined = "\n".join(lines)
    assert "Score: 3/3" in joined
    assert "No topic went wrong 🎉" in lines
    assert "My Weak Topics" not in joined


def test_mid_test_behaviour_unchanged():
    session = {}
    plan = ["correct", "wrong"]
    _items, payloads = _run_plan(session, plan)
    # Instant verdict on the attempt turn itself, and the
    # Wave-160 laughing-robot flag rides ONLY the correct
    # attempt — never the wrong one, never the start.
    first, second = payloads
    assert first["result"]["answer"].startswith("Correct")
    assert first["result"]["test_verdict"] == "correct"
    assert second["result"]["answer"].startswith("Wrong")
    assert "test_verdict" not in second["result"]
    # Mid-test turns stay plain chat-test turns.
    for payload in payloads:
        assert payload["result"]["plain"] is True
        assert payload["result"]["fallback_kind"] == "chat_test"


def test_full_run_hindi_uses_devanagari_diagnostic():
    session = {}
    started = chat_test.handle_message(
        session, None, 1, "टेस्ट दो", "en")
    assert started is not None and started["ok"] is True
    state = session[chat_test._session_key(1)]
    items = list(state["items"])
    payload = None
    for _item in items:
        payload = chat_test.handle_message(
            session, None, 1, "987654321", "en")
    final = payload["result"]
    lines = [final["answer"]] + list(final["steps"])
    joined = "\n".join(lines)
    assert "स्कोर: 0/" in joined
    assert any(ln.startswith("कमज़ोर विषय:") for ln in lines)
    # Every answer was wrong, so a weakest topic exists and
    # the practice next step is offered, in Devanagari.
    assert "इसका अभ्यास करें?" in joined
    assert "My Weak Topics" in joined
    topics = {it["topic_label"] for it in items}
    if len(topics) > 1:
        assert "विषय के हिसाब से:" in lines
