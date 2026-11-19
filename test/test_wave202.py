"""Wave 202 (Suraj, 20 Nov 2026: "prediction nhi kar paa
rha hai ganitra achhe se" + "questions ko achhe se samajh
nahi raha hai, aisa kyu ho raha hai") — the native SEQUENCE
ENGINE: next term by the NUMBERS, not by the phrasing.

The parent probed the live site with 10 prediction/series
questions; only one was solved natively. The rest reached
the AI legs (quota luck) — and "predict the next number:
3, 6, 11, 18, 27" ended at "Answer not found." while
"series ka agla number batao 4, 8, 12, 16" was served a
step sentence ("Look at the numbers.") in the answer
field. Both failures are pinned here as regressions:

  * the not-found seam: a series ask's chain standing is
    the "guide" kind, whose ONLY remaining hope was the AI
    legs; total leg silence (every leg maps truncation /
    quota / transport failure to None) collapsed it to the
    not-found line, because no native layer recognised a
    next-term ask outside a few fixed wordings (Wave 42/56:
    "next term" / "agla pad" / "ke baad", AP/GP only). The
    engine (solver/sequences.solve_series_next, hooked into
    solve_sequences and into the router's pre-dispatch)
    settles the ask from the extracted numbers first; the
    AI legs stay the backstop for series no family settles.
  * the malformed serve: a leg's shaped result can carry a
    step sentence in the answer field (gemini_fallback's
    _shape_result takes the model's stated "Answer:" line,
    or the reply's last line, as the answer). Wave 133's
    chain rejected it (no value claim) but Wave 158's
    last-resort picker then served the rejected candidate
    anyway. Wave 202's guard (aiverify.series_answer_
    missing_value, applied in sanity_check AND in the
    last-resort picker): on a series next-term ask, a
    candidate stating no numeric value is never served.

The heart of the wave is the PARAPHRASE BATTERY: the same
series asked many ways (EN formal, EN casual, bare,
Hinglish x2, Devanagari, pattern-ask) must give the SAME
answer, served NATIVELY (fallback_kind None, op
"series_next") — never via an AI kind, never not-found.
"""
import pytest

import fallback
from fallback import fallback_answer
from solver.sequences import solve_series_next


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the real AI legs stay inert (the guard
    tests patch the chain functions directly)."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _patch_ai(monkeypatch, reply):
    """The Wave 111/185 harness: stub the three AI legs at
    fallback's own seams."""
    monkeypatch.setattr(fallback, "_gemini_answer",
                        lambda *a, **k: reply)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)


def _native(question, expected):
    out = fallback_answer(question)
    assert out.get("fallback_kind") is None, (
        f"{question!r} not native: kind="
        f"{out.get('fallback_kind')} answer={out.get('answer')!r}")
    assert out.get("op") == "series_next", (
        f"{question!r} op={out.get('op')}")
    assert str(out.get("answer")) == expected, (
        f"{question!r} -> {out.get('answer')!r}, "
        f"expected {expected!r}")
    return out


# ---------------------------------------------------------------------------
# 1. The two live failures, verbatim
# ---------------------------------------------------------------------------

def test_live_notfound_regression_second_difference():
    # Live: "Answer not found." — correct next term is 38
    # (differences +3, +5, +7, +9, so +11).
    out = _native("predict the next number: 3, 6, 11, 18, 27",
                  "38")
    blob = " ".join(out.get("steps") or [])
    assert "38" in blob


def test_live_malformed_regression_answer_is_the_next_term():
    # Live: answer field was "Look at the numbers."
    out = _native("series ka agla number batao 4, 8, 12, 16",
                  "20")
    assert "numbers" not in str(out.get("answer")).lower()


# ---------------------------------------------------------------------------
# 2. The paraphrase battery — same series, many phrasings,
#    same NATIVE answer
# ---------------------------------------------------------------------------

_SERIES = [
    # (series, expected next, family)
    ("4, 8, 12, 16", "20", "ap"),
    ("3, 9, 27, 81", "243", "gp"),
    ("3, 6, 11, 18, 27", "38", "second_difference"),
    ("1, 4, 9, 16, 25", "36", "squares"),
    ("1, 8, 27, 64", "125", "cubes"),
    ("1, 1, 2, 3, 5, 8", "13", "fibonacci"),
    ("2, 3, 5, 7, 11", "13", "primes"),
    ("1, 10, 2, 20, 3, 30", "4", "interleaved"),
    ("3, 7, 15, 31, 63", "127", "diff_gp / recurrence"),
    ("1, 2, 6, 24, 120", "720", "ratio_ap (factorial)"),
    ("100, 90, 80, 70", "60", "ap decreasing"),
    ("1/2, 1/4, 1/8", "1/16", "gp fractions"),
]

_PHRASINGS = [
    ("en_formal", "What is the next number in the series {s}?"),
    ("en_casual", "predict the next number: {s}"),
    ("bare", "{s}, ?"),
    ("hinglish_series", "series ka agla number batao {s}"),
    ("hinglish_prediction", "agle number ka prediction karo: {s}"),
    ("devanagari", "अगला नंबर क्या होगा: {s}"),
    ("pattern_ask", "pattern batao: {s}, ?"),
]


@pytest.mark.parametrize("series,expected,family", _SERIES,
                         ids=[s[2] for s in _SERIES])
@pytest.mark.parametrize("pname,template", _PHRASINGS,
                         ids=[p[0] for p in _PHRASINGS])
def test_paraphrase_battery(series, expected, family,
                            pname, template):
    _native(template.format(s=series), expected)


def test_battery_devanagari_digits():
    # The AP series written entirely in Devanagari digits.
    _native("अगला नंबर क्या होगा: ४, ८, १२, १६", "20")


@pytest.mark.parametrize("question,expected", [
    # Space-separated series (no commas at all).
    ("series ka agla number batao 4 8 12 16", "20"),
    ("predict next 5 10 20 40", "80"),
    ("अगला नंबर क्या होगा 2 6 12 20", "30"),
    # Trailing "..." instead of "?".
    ("next number: 2, 4, 8, 16, ...", "32"),
    # The remaining live-probe questions, verbatim.
    ("2, 4, 8, 16, ?", "32"),
    ("agle number ka prediction karo: 5, 10, 20, 40", "80"),
    ("1, 1, 2, 3, 5, 8, ?", "13"),
    ("next term kya hoga 100, 90, 80", "70"),
    ("2, 3, 5, 7, 11, ?", "13"),
    ("1, 4, 9, 16, ?", "25"),
    ("अगला नंबर क्या होगा: 2, 6, 12, 20", "30"),
    ("pattern batao: 7, 14, 21, 28, ?", "35"),
])
def test_live_probe_and_shapes(question, expected):
    _native(question, expected)


# ---------------------------------------------------------------------------
# 3. Pattern-family coverage (one canonical case each)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,expected", [
    ("predict the next number: 10, 7, 4, 1", "-2"),      # AP < 0 d
    ("next number 16, 8, 4, 2, ?", "1"),                 # GP r = 1/2
    ("next number: 2, 5, 10, 17, 26", "37"),             # squares + 1
    ("next term: 0, 7, 26, 63", "124"),                  # cubes - 1
    ("series 2, 3, 6, 15, 42 ka agla number", "123"),    # diffs in GP
    ("next number 4, 6, 8, 9, 10, ?", "12"),             # composites
    ("pattern: 2, 3, 4, 9, 6, 27, ?", "8"),              # interleaved AP/GP
    ("next: 2, 6, 14, 30, 62", "126"),                   # x2 + 2 family
    ("series: -5, -1, 3, 7, ?", "11"),                   # negative AP
    ("agla number kya hoga 5, 5, 5, 5", "5"),            # constant
])
def test_pattern_families(question, expected):
    _native(question, expected)


# ---------------------------------------------------------------------------
# 4. Non-hijack — differently-shaped asks keep their owners
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Find the 10th term of the AP 2, 5, 8, ...",
    "sum of the AP 2, 7, 12, ... up to 10 terms",
    "Find the sum of first 10 terms of 3, 6, 11, 18, 27",
    "find the average of 3, 6, 11, 18, 27",
    "find the median of 2, 4, 8, 16, 32",
    "Find the common difference of the series 2, 5, 8, 11",
    "2, 4, 8, 16, ? (A) 18 (B) 24 (C) 32 (D) 64",
    "Ram bought 3 pens, 5 books and 7 notebooks for 100 rupees",
    "solve 2x + 3 = 11",
    "12th class ke kuch questions milenge solve karane ke liye",
])
def test_engine_silent_on_other_shapes(question):
    assert solve_series_next(question) is None


def test_nth_term_ask_still_served_by_its_owner():
    out = fallback_answer("Find the 10th term of the AP 2, 5, 8, ...")
    assert str(out.get("answer")) == "29"
    assert out.get("op") != "series_next"


def test_ap_sum_ask_still_served_by_its_owner():
    out = fallback_answer(
        "sum of the AP 2, 7, 12, ... up to 10 terms")
    assert str(out.get("answer")) == "245"
    assert out.get("op") != "series_next"


def test_broad_gate_hijack_regressions():
    # The first broad-chunk run caught the engine firing
    # on FRAGMENTS the router's Wave-77 core pass carved
    # out of these two questions ("AP: 3, 8, 13, 18, ... d"
    # and "X = 1, 2, 4" slip under a loose bare-shape bar).
    # The bare bar is now ZERO leftover words, and both
    # questions keep their Wave 188/195 owners end-to-end.
    from solver.router import solve_question
    out = solve_question(
        "For the AP: 3, 8, 13, 18, ... find the value of d")
    assert out.get("op") == "w195_ap_series_d"
    assert str(out.get("answer")) == "d = 5"
    out = solve_question(
        "A random variable X has the following probability "
        "distribution: X = 1, 2, 4 with P(X) = 0.2, 0.3, "
        "0.5. Find E(X)")
    assert str(out.get("answer")) == "Mean = 2.8"
    # The carved fragments themselves are not next asks.
    assert solve_series_next("AP: 3, 8, 13, 18, ... d") is None
    assert solve_series_next("X = 1, 2, 4") is None


# ---------------------------------------------------------------------------
# 5. The malformed-answer guard + the AI backstop
# ---------------------------------------------------------------------------

_MALFORMED = {
    "type": "Ganitra", "op": "gemini",
    "answer": "Look at the numbers",
    "steps": ["Look at the numbers.",
              "Each term increases by 4"],
    "fallback": True, "fallback_kind": "gemini",
    "ai_generated": True,
}

# A series no Wave-202 family settles (checked against the
# engine: no AP/GP, no polynomial differences, not
# Fibonacci, not primes, not interleaved, no recurrence) —
# the AI legs are its only route, exactly the standing
# rule's backstop case.
_UNSETTLED = "predict the next number: 5, 3, 8, 4, 2"


def test_unsettled_series_engine_silent():
    assert solve_series_next(_UNSETTLED) is None


def test_ai_backstop_still_serves_unsettled_series(monkeypatch):
    good = {"type": "Ganitra", "op": "gemini", "answer": "9",
            "steps": ["A plausible pattern"], "fallback": True,
            "fallback_kind": "gemini", "ai_generated": True}
    _patch_ai(monkeypatch, good)
    out = fallback_answer(_UNSETTLED)
    assert str(out.get("answer")) == "9"
    assert out.get("fallback_kind") == "gemini"


def test_malformed_candidate_never_served_on_series(monkeypatch):
    _patch_ai(monkeypatch, dict(_MALFORMED))
    out = fallback_answer(_UNSETTLED)
    assert "Look at the numbers" not in str(out.get("answer"))


def test_malformed_candidate_irrelevant_when_native(monkeypatch):
    # A classifiable series never reaches the legs at all.
    _patch_ai(monkeypatch, dict(_MALFORMED))
    _native("series ka agla number batao 4, 8, 12, 16", "20")


def test_guard_is_series_scoped_prose_untouched(monkeypatch):
    # A value-less PROSE answer to a non-series question is
    # the Wave 185 shape and keeps serving exactly as
    # before — the guard must not widen beyond series asks.
    prose = {"type": "Ganitra", "op": "gemini",
             "answer": "Because it has only one factor",
             "steps": ["A prime needs exactly two factors"],
             "fallback": True, "fallback_kind": "gemini",
             "ai_generated": True}
    _patch_ai(monkeypatch, prose)
    # "abacus kya hota hai" is a Wave-177 knowledge ask the
    # curated layers miss — it genuinely reaches the legs.
    out = fallback_answer("abacus kya hota hai")
    assert str(out.get("answer")) == \
        "Because it has only one factor"
