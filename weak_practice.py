"""Wave 87: "My Weak Topics" — personal practice built from the
student's own Mistake Notebook.

The Mistake Notebook (Wave 5) stores the wrong rows of every quiz /
chapter test / board test in the session as
    {"question", "expected", "given", "topic", "source"}
newest first.  Until now the only follow-up was /mistakes/practice,
which re-shows those SAME questions.  This module builds a fresh
practice set instead:

  1. aggregate the notebook by its `topic` field and rank the
     topics by mistake count (ties: the topic whose most recent
     mistake is newest ranks first — the notebook is newest-first,
     so first occurrence wins);
  2. allocate the set's slots across the ranked topics in
     proportion to their counts (largest remainder, at least one
     slot per topic while slots last);
  3. generate fresh questions for each topic and keep ONLY the
     ones the app's own solve path (solver.router.solve_question —
     the solver the chat route runs) answers with the generator's
     answer — a question that cannot be verified is never served.

Generation backends, by topic:
  * practice_gen topics (arithmetic, algebra, geometry,
    mensuration, probability) — Classes 6-10, exact-fraction
    checking via test_mode.check_test_answer;
  * quiz-only topics (trig, stats) — solver.practice.generate_quiz
    at medium difficulty, tolerance checking via check_quiz_answer;
  * anything else (sequences, linear_algebra, calculus, ...) has
    no generator yet: it still shows in the ranking, it just
    contributes no questions.  If NO saved topic has a generator,
    the set falls back to a general mix over the practice_gen
    topics so the student still gets a set.

Everything is derived from the calling session's own notebook —
no other student's data is ever read.

Public API:
    aggregate_weak_topics(mistakes) -> [{"topic", "count"}, ...]
    topic_backend(topic) -> "gen" | "quiz" | None
    build_weak_set(mistakes, class_num, count=10, seed=None)
        -> {"items": [...], "plan": [...], "general": bool}
    check_weak_answer(item, given) -> bool
    summarise_results(items, correct_flags)
        -> {"score", "total", "topics": [...], "kinds": [...]}
"""
import random
import re
from fractions import Fraction

import practice_gen
import test_mode
from solver.practice import check_quiz_answer, generate_quiz

SET_QUESTION_COUNT = 10
_MAX_TOPICS = 5          # topics that share one set at most
_MAX_ATTEMPTS = 90       # generation attempts per set build
_MAX_TOPIC_ATTEMPTS = 30  # ... and per topic (the solve path costs
                         # ~1s per candidate, so budgets stay tight)

_GEN_TOPICS = frozenset(practice_gen.TOPICS)
_QUIZ_ONLY_TOPICS = frozenset(("trig", "stats"))


def topic_backend(topic):
    """Which generator can serve this notebook topic, if any."""
    if topic in _GEN_TOPICS:
        return "gen"
    if topic in _QUIZ_ONLY_TOPICS:
        return "quiz"
    return None


def aggregate_weak_topics(mistakes):
    """Rank notebook topics by mistake count, weakest first.

    `mistakes` is the session notebook (newest first).  Entries
    without a usable topic string are ignored.  Ties are broken by
    first occurrence, i.e. the topic of the newest mistake wins.
    """
    counts = {}
    order = []
    for entry in mistakes or []:
        if not isinstance(entry, dict):
            continue
        topic = (entry.get("topic") or "").strip()
        if not topic:
            continue
        if topic not in counts:
            counts[topic] = 0
            order.append(topic)
        counts[topic] += 1
    ranked = [{"topic": t, "count": counts[t]} for t in order]
    ranked.sort(key=lambda r: -r["count"])  # stable: ties keep order
    return ranked


def _allocate(ranked_counts, count):
    """Split `count` slots over topics proportionally to their
    mistake counts (largest remainder; >= 1 slot per topic while
    slots last).  Returns a list parallel to `ranked_counts`."""
    n = len(ranked_counts)
    if n == 0 or count <= 0:
        return []
    if n >= count:
        return [1] * count + [0] * (n - count)
    total = sum(ranked_counts)
    raw = [c * count / total for c in ranked_counts]
    slots = [max(1, int(r)) for r in raw]
    # Trim or top up to exactly `count`, touching the topics whose
    # raw share is furthest from their current slots first.
    while sum(slots) > count:
        i = max(range(n), key=lambda j: (slots[j] - raw[j], slots[j]))
        if slots[i] <= 1:
            break
        slots[i] -= 1
    while sum(slots) < count:
        i = max(range(n), key=lambda j: raw[j] - slots[j])
        slots[i] += 1
    return slots


# ------------------------------------------------------------------
# Solve-path verification
# ------------------------------------------------------------------

_NUM_TOKEN = re.compile(r"[+-]?\d+(?:\.\d+)?(?:\s*/\s*\d+)?")


def _first_number(text):
    """First numeric token of a solver answer as a Fraction
    (the Wave 34 cross-check recipe)."""
    if not text:
        return None
    m = _NUM_TOKEN.search(str(text).replace(",", ""))
    if not m:
        return None
    token = m.group(0).replace(" ", "")
    try:
        if "/" in token and "." not in token:
            num, den = token.split("/")
            return Fraction(int(num), int(den))
        return Fraction(token).limit_denominator(10 ** 6)
    except (ValueError, ZeroDivisionError):
        return None


def _all_numbers(text):
    """Every numeric token of a text as Fractions, in order."""
    out = []
    for m in _NUM_TOKEN.finditer(str(text).replace(",", "")):
        tok = m.group(0).replace(" ", "")
        try:
            if "/" in tok and "." not in tok:
                num, den = tok.split("/")
                out.append(Fraction(int(num), int(den)))
            else:
                out.append(Fraction(tok).limit_denominator(10 ** 6))
        except (ValueError, ZeroDivisionError):
            return []
    return out


_SUPERSCRIPTS = {"⁰": "**0", "¹": "**1", "²": "**2", "³": "**3",
                 "⁴": "**4", "⁵": "**5", "⁶": "**6", "⁷": "**7",
                 "⁸": "**8", "⁹": "**9"}


def _sympy_equiv(got_text, answer_text, kind):
    """Mathematical-equivalence check for the string-answer kinds
    (expansions, factorisations, root lists, midpoints, ratios):
    the solver's answer text must denote the same value(s) as the
    generator's answer.  Anything unparsable is NOT verified."""
    got_nums = _all_numbers(got_text)
    want_nums = _all_numbers(answer_text)
    if want_nums and len(got_nums) == len(want_nums):
        if kind == "quadratic_roots":
            return sorted(got_nums) == sorted(want_nums)
        if got_nums == want_nums:
            return True
    if kind == "ratio_simplify" and len(want_nums) == 2 \
            and len(got_nums) == 1:
        return got_nums[0] * want_nums[1] == want_nums[0]
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            convert_xor, implicit_multiplication_application,
            parse_expr, standard_transformations)
        transformations = (standard_transformations + (convert_xor,)
                           + (implicit_multiplication_application,))

        def _parse(text):
            t = str(text).lower().replace("−", "-").replace("·", "*")
            t = t.replace("×", "*").replace("÷", "/")
            for sup, rep in _SUPERSCRIPTS.items():
                t = t.replace(sup, rep)
            t = t.split("=")[-1].strip().rstrip(".")
            return parse_expr(t, transformations=transformations,
                              evaluate=True)

        return bool(sp.simplify(_parse(got_text)
                                - _parse(answer_text)) == 0)
    except Exception:
        return False


def _solver_agrees(text, answer_value, answer_text, kind=None):
    """True when the app's own solve path answers `text` with the
    generator's answer.

    The solve path is solver.router.solve_question — the exact
    solver the chat route runs (api._solve_friendly is a wrapper
    around it that adds a hint-retry and the fallback layers;
    verifying against the raw solver is the stricter test, and it
    keeps a failed candidate from costing two solver runs plus
    the fallback machinery).  A failed or letter-soup result
    never counts: i18n.solve_failed is the same predicate the
    chat path uses to decide a solve did not land."""
    from i18n import solve_failed
    from solver.router import solve_question
    result = solve_question(text)
    if not isinstance(result, dict) or solve_failed(text, result):
        return False
    got_text = result.get("answer", "")
    if answer_value is not None:
        got = _first_number(got_text)
        return got is not None and got == answer_value
    return _sympy_equiv(got_text, answer_text, kind)


def _verified_gen_item(class_num, topic, rng, numeric_only=False):
    """One practice_gen question that the solver agrees with,
    projected to its JSON-safe session shape; None on failure.
    With numeric_only, string-answer kinds are left for pass 2 —
    numeric agreement is the cheapest reliable check."""
    item = practice_gen.generate_question(
        class_num, topic, seed=rng.randrange(1 << 30))
    if numeric_only and item["answer_value"] is None:
        return None
    text = item["solver_text"] or item["question"]
    if not _solver_agrees(text, item["answer_value"], item["answer"],
                          kind=item["kind"]):
        return None
    projected = test_mode._project(item)
    projected["checker"] = "exact"
    return projected


def _verified_quiz_items(topic, rng, want):
    """Up to `want` solver.practice quiz questions (trig/stats)
    that the solver agrees with, harvested from ONE generated
    batch.  If none of the batch verifies, the topic is given up
    for this build (the solver, e.g., declines 'What is sin 60°?'
    outright, and re-asking costs ~1s per question)."""
    batch = generate_quiz(topic, "medium", seed=rng.randrange(1 << 30))
    rng.shuffle(batch)
    out = []
    for q in batch:
        if len(out) >= want:
            break
        expected = q["answer"]
        try:
            value = Fraction(str(expected)).limit_denominator(10 ** 6)
        except (ValueError, ZeroDivisionError):
            value = None
        if _solver_agrees(q["question"], value, str(expected)):
            out.append({
                "class_num": None,
                "topic": topic,
                "kind": topic,
                "question": q["question"],
                "answer": (str(expected) if not isinstance(expected, str)
                           else expected),
                "answer_value": None,
                "params": {},
                "checker": "quiz",
            })
    return out


# ------------------------------------------------------------------
# Set building
# ------------------------------------------------------------------

def build_weak_set(mistakes, class_num, count=SET_QUESTION_COUNT,
                   seed=None):
    """Build a verified practice set weighted to the notebook's
    weakest topics.  `class_num` is clamped to the practice_gen
    range (6-10).  Returns {"items", "plan", "general"} — plan has
    one row per ranked topic: {"topic", "count" (mistakes),
    "allocated", "served"}."""
    if class_num not in practice_gen.CLASSES:
        class_num = min(10, max(6, int(class_num or 8)))
    rng = random.Random(seed)
    ranked = aggregate_weak_topics(mistakes)
    mappable = [r for r in ranked
                if topic_backend(r["topic"]) is not None]
    general = not mappable
    if general:
        # No generator for any saved topic (or an empty notebook):
        # a general mix over the practice_gen topics.
        mappable = [{"topic": t, "count": 1}
                    for t in practice_gen.TOPICS]
    mappable = mappable[:_MAX_TOPICS]
    slots = _allocate([r["count"] for r in mappable], count)
    plan = {r["topic"]: {"topic": r["topic"], "count": r["count"],
                         "allocated": s, "served": 0}
            for r, s in zip(mappable, slots)}

    items, seen = [], set()
    attempts = 0
    # Fill each topic's allocation; shortfalls roll over to the
    # next topics so the set still reaches `count` whenever the
    # generators can verify enough questions.
    fill_order = [r["topic"] for r in mappable]
    deficit = 0
    for topic in fill_order:
        want = plan[topic]["allocated"] + deficit
        deficit = 0
        got = 0
        topic_attempts = 0
        while (got < want and attempts < _MAX_ATTEMPTS
               and topic_attempts < _MAX_TOPIC_ATTEMPTS):
            attempts += 1
            topic_attempts += 1
            if topic_backend(topic) == "gen":
                batch = [_verified_gen_item(
                    class_num, topic, rng,
                    numeric_only=topic_attempts
                    <= _MAX_TOPIC_ATTEMPTS // 2)]
            else:
                batch = _verified_quiz_items(topic, rng, want - got)
                if not batch:
                    break  # one empty probe batch ends this topic
            for item in batch:
                if item is None or item["question"] in seen:
                    continue
                seen.add(item["question"])
                items.append(item)
                got += 1
        plan[topic]["served"] = got
        deficit = want - got
    rng.shuffle(items)
    return {
        "items": items,
        "plan": [plan[t] for t in fill_order],
        "general": general,
    }


def check_weak_answer(item, given):
    """Score one answer with the checker of the item's backend."""
    if item.get("checker") == "quiz":
        return check_quiz_answer(item["answer"], given)
    return test_mode.check_test_answer(item, given)


def summarise_results(items, correct_flags):
    """Per-topic / per-kind outcome of a finished set.

    A topic counts as "improved" when the student now gets at
    least 80% of its questions right; below that it stays "weak".
    """
    topics, kinds = {}, {}
    for item, ok in zip(items, correct_flags):
        for bucket, key in ((topics, item["topic"]),
                            (kinds, item["kind"])):
            row = bucket.setdefault(
                key, {"topic" if bucket is topics else "kind": key,
                      "total": 0, "correct": 0})
            row["total"] += 1
            row["correct"] += 1 if ok else 0
    topic_rows = []
    for row in topics.values():
        row = dict(row)
        row["status"] = ("improved" if row["total"] and
                         row["correct"] / row["total"] >= 0.8
                         else "weak")
        topic_rows.append(row)
    topic_rows.sort(key=lambda r: (-r["total"], r["topic"]))
    kind_rows = sorted(kinds.values(),
                       key=lambda r: (-r["total"], r["kind"]))
    return {
        "score": sum(1 for ok in correct_flags if ok),
        "total": len(items),
        "topics": topic_rows,
        "kinds": kind_rows,
    }
