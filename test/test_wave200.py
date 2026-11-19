"""Wave 200: repeat-ask variation for EVERY knowledge
card (Suraj, 20 Nov 2026 ~00:43 IST).

"Jo 1 baar de diya ans toh wapas kyu deta hai, har baar
Naya ans chahiye" — a repeated question in the same chat
must never serve the identical fixed card again.

Wave 178 built the mechanism (repeat.py counting per
chat + maths_meta.meta_variation) and authored per-entry
variations for 20 of the 61 knowledge entries; every
other FACTS / HISTORY / ADVICE card rode on its kind's
generic pool — the same generic extra lines for every
card of the kind. Wave 200 authors a per-entry "again"
(2nd ask: a fresh example / extra fact) and "third"
(3rd+ ask: a deeper fact / a practice step) for ALL
remaining entries, in en / roman / dev, and deepens
meta_variation so that from the 4th ask on, a rotated
generic "third" line joins the authored lines — the
extra lines themselves keep changing, not only
repeat.py's opener.

Semantics (Wave 178, confirmed by Suraj): variation is
per-chat only — a NEW chat serves the first variant
again; the base card and its answer line are never
mutated; solver / computed answers are untouched.
"""
import pytest

import repeat
import maths_meta
from guidance import guidance_result
from maths_meta import meta_result


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the AI legs must stay inert in this
    battery."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _solve(client, question):
    return client.post(
        "/api/solve", json={"question": question}).get_json()


def _drive(session, question, result, flavour="roman",
           chat="chat1"):
    return repeat.session_variation(
        session, chat, question, result, flavour)


def _progression(question, flavour="roman", asks=4):
    """Ask the same knowledge question `asks` times in
    one chat; return (base, [served results])."""
    base = meta_result(question)
    assert base is not None, question
    session = {}
    served = []
    for _ in range(asks):
        varied = _drive(session, question, base, flavour)
        served.append(base if varied is None else varied)
    return base, served


def _assert_progression(question, flavour="roman",
                        must_carry=()):
    base, served = _progression(question, flavour)
    # 1st ask: the base card, unvaried and unmarked
    assert "w178_repeat" not in served[0]
    assert served[0]["steps"] == base["steps"]
    # every repeat: marked, different steps, same answer,
    # base lines carried untouched in the middle
    for i, r in enumerate(served[1:], start=2):
        assert r["w178_repeat"] == i
        assert r["answer"] == base["answer"]
        for line in base["steps"]:
            assert line in r["steps"]
        for token in must_carry:
            assert token in " ".join(r["steps"]) \
                or token in r["answer"]
    # no two consecutive servings are the same card
    for a, b in zip(served, served[1:]):
        assert a["steps"] != b["steps"]
    # 2nd and 3rd differ from each other too (not just
    # from their neighbours by the opener alone: the
    # authored extra lines differ)
    assert served[1]["steps"][-1] != served[2]["steps"][-1] \
        or served[1]["steps"] != served[2]["steps"]
    # the base result object was never mutated
    assert "w178_repeat" not in base
    return base, served


# ---------------------------------------------------------------------------
# 1. Representative cards: the same question 3+ times in
#    one chat — every serving differs, the core answer
#    stays correct (pre-existing Wave 178 cards AND the
#    cards Wave 200 newly authored)
# ---------------------------------------------------------------------------

def test_zero_progression_roman():
    _assert_progression("0 ki khoj kisne ki hai", "roman",
                        must_carry=("Aryabhata", "Brahmagupta"))


def test_pi_progression_en():
    _assert_progression("Who discovered pi?", "en",
                        must_carry=("3.1416", "Archimedes"))


def test_largest_2digit_prime_progression_new():
    _assert_progression(
        "sabse bada two digit prime number kaun sa hai",
        "roman", must_carry=("97",))


def test_crore_zeros_progression_new():
    _assert_progression("1 crore me kitne zero hote hai",
                        "roman", must_carry=("7",))


def test_dozen_progression_new():
    _assert_progression("1 dozen me kitne hote hai",
                        "roman", must_carry=("12",))


def test_pascal_triangle_progression_new():
    _assert_progression("pascal triangle kisne banaya",
                        "roman", must_carry=("Pascal",))


def test_polygons_progression_new():
    _assert_progression("pentagon me kitni bhujaen hoti hai",
                        "roman", must_carry=("Pentagon",))


def test_advice_practice_progression_new():
    _assert_progression("maths kaise practice karu",
                        "roman")


def test_devanagari_progression_new_card():
    base, served = _progression(
        "१ करोड़ में कितने शून्य होते हैं", "dev")
    assert served[0]["answer"].startswith("1 करोड़")
    # the varied serves speak Devanagari, like the card
    def _has_dev(text):
        return any("ऀ" <= ch <= "ॿ" for ch in str(text))
    assert _has_dev(served[1]["steps"][0])
    assert _has_dev(served[1]["steps"][-1])


# ---------------------------------------------------------------------------
# 2. Coverage: EVERY knowledge entry now carries authored
#    variations in all three flavours — and the table
#    size proves the Wave 200 .update() overwrote nothing
# ---------------------------------------------------------------------------

def test_every_knowledge_entry_has_authored_variations():
    total = 0
    for kind, table in (("history", maths_meta.HISTORY),
                        ("fact", maths_meta.FACTS),
                        ("advice", maths_meta.ADVICE)):
        for entry in table:
            total += 1
            var = maths_meta.META_VARIATIONS.get(
                (kind, entry["id"]))
            assert var is not None, (kind, entry["id"])
            for flavour in ("en", "roman", "dev"):
                assert var[flavour]["again"], \
                    (kind, entry["id"], flavour, "again")
                assert var[flavour]["third"], \
                    (kind, entry["id"], flavour, "third")
                # authored lines are the card's OWN — never
                # a copy of one of its base lines
                base_lines = set(entry[flavour]["steps"]) \
                    | {entry[flavour]["answer"]}
                for level in ("again", "third"):
                    for line in var[flavour][level]:
                        assert line not in base_lines
    # 61 entries, 61 variation blocks: the .update()
    # added only new keys (20 Wave 178 + 41 Wave 200)
    assert len(maths_meta.META_VARIATIONS) == total == 61


def test_meta_variation_never_empty_and_keeps_changing():
    for kind, table in (("history", maths_meta.HISTORY),
                        ("fact", maths_meta.FACTS),
                        ("advice", maths_meta.ADVICE)):
        for entry in table:
            for flavour in ("en", "roman", "dev"):
                prev = None
                for count in (2, 3, 4, 5, 6):
                    lines = maths_meta.meta_variation(
                        kind, entry["id"], flavour, count)
                    assert lines, (kind, entry["id"],
                                   flavour, count)
                    assert lines != prev, \
                        (kind, entry["id"], flavour, count)
                    prev = lines


# ---------------------------------------------------------------------------
# 3. Per-chat semantics: a fresh chat serves the first
#    variant again; a first ask anywhere is the base card
# ---------------------------------------------------------------------------

def test_fresh_chat_serves_first_variant_again():
    q = "1 dozen me kitne hote hai"
    base = meta_result(q)
    session = {}
    assert _drive(session, q, base, chat="chatA") is None
    v = _drive(session, q, base, chat="chatA")
    assert v["w178_repeat"] == 2
    # a different chat in the same session: first ask
    assert _drive(session, q, base, chat="chatB") is None
    # a brand-new session: first ask
    assert _drive({}, q, base, chat="chatA") is None


def test_first_ask_is_the_base_card_unchanged():
    q = "pascal triangle kisne banaya"
    r = meta_result(q)
    entry = next(e for e in maths_meta.HISTORY
                 if e["id"] == "pascal_triangle")
    assert "w178_repeat" not in r
    assert r["answer"] == entry["roman"]["answer"]
    assert r["steps"] == entry["roman"]["steps"]


# ---------------------------------------------------------------------------
# 4. Wave 178 guidance behaviour still intact
# ---------------------------------------------------------------------------

def test_guidance_repeat_still_varies():
    q = "maths me kya scope hai"
    base = guidance_result(q)
    session = {}
    assert _drive(session, q, base) is None
    v2 = _drive(session, q, base)
    assert v2["w178_repeat"] == 2
    assert v2["steps"] != base["steps"]
    v3 = _drive(session, q, base)
    assert v3["w178_repeat"] == 3
    assert v3["steps"] != v2["steps"]


# ---------------------------------------------------------------------------
# 5. End to end through /api/solve
# ---------------------------------------------------------------------------

def test_client_new_fact_card_progression_x3(client):
    q = "1 crore me kitne zero hote hai"
    r1 = _solve(client, q)["result"]
    assert r1["fallback_kind"] == "fact"
    assert r1["meta_id"] == "crore_zeros"
    assert "w178_repeat" not in r1
    r2 = _solve(client, q)["result"]
    assert r2["w178_repeat"] == 2
    assert r2["steps"] != r1["steps"]
    assert r2["answer"] == r1["answer"]
    r3 = _solve(client, q)["result"]
    assert r3["w178_repeat"] == 3
    assert r3["steps"] != r2["steps"]
    assert r3["answer"] == r1["answer"]


def test_client_new_history_card_progression_x3(client):
    q = "pascal triangle kisne banaya"
    r1 = _solve(client, q)["result"]
    assert r1["fallback_kind"] == "history"
    assert r1["meta_id"] == "pascal_triangle"
    assert "w178_repeat" not in r1
    r2 = _solve(client, q)["result"]
    assert r2["w178_repeat"] == 2
    assert r2["steps"] != r1["steps"]
    r3 = _solve(client, q)["result"]
    assert r3["w178_repeat"] == 3
    assert r3["steps"] != r2["steps"]
    for r in (r1, r2, r3):
        assert "Pascal" in " ".join(r["steps"])
