"""Wave 158: the last resort — "jawab milega hi".

Suraj's order (18 Nov 2026): "Aisa nhi bolna — nhi aa
rha; ans kahi se bhi de, ans bs chahiye, chahe kisi AI se
leke de" — joined with his quality bar the same morning:
"ans 101% sahi hona chahiye." So for a GENUINE maths
question, when the solver, the bank, Wave 133's
verification AND Wave 134's method transfer have all
failed, the chain no longer collapses to the one-line
not-found if an AI leg did answer: the best rejected AI
answer is served as the last resort, under a strict
preference —

  (a) MAJORITY: a final value two or more legs agree on
      (aiverify's own claim agreement) beats everything,
      even when its earliest carrier is a later leg;
  (b) SINGLE: otherwise the first leg's answer in chain
      order (Gemini -> Groq -> OpenRouter).

...and Ganitra's own counting always outranks both: on a
disagreement with no majority, Wave 134's method transfer
over the rejected candidates (already wired ahead of this
picker) recomputes the value itself and serves THAT.

Proven here, with every leg stubbed at the fallback seam
(the Wave 133 pattern — no network, no keys):

- verification-fail + an AI answer -> the last-resort
  serve, values and steps byte-identical to the leg's own
  shaped result (the legs re-voice via Wave 132's
  normaliser; the serve adds no disclaimer, no apology);
- majority beats first-leg; no majority -> first leg;
- method-transfer value beats every AI value on a
  disagreement;
- the verified path is unchanged: a deterministic pass
  still serves marked "deterministic" and promotes in the
  Live Bank, while a last-resort serve stays PENDING and
  is never served from the store;
- the boundaries stand: non-maths keeps its one-liner
  (legs never consulted), pure gibberish never reaches
  the AI block, and when every leg is silent the honest
  not-found remains.
"""
import pytest

import aiverify
import deep_solve
import fallback
import livebank
from fallback import with_fallback

FAILED = {"op": "error",
          "answer": "Could not solve this one: x",
          "steps": []}

AREA_Q = "Find the area between the curves y = x^2 and y = x"
PERCENT_Q = "What is 24% of 450?"
NONMATHS_Q = "What is the capital of France?"
GIBBERISH_Q = "asdf qwer zxcv plugh"


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w158.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    monkeypatch.delenv("GANITRA_AIVERIFY", raising=False)
    monkeypatch.delenv("GANITRA_DEEP_SOLVE", raising=False)
    return path


@pytest.fixture()
def no_salvage(monkeypatch):
    """Enter the chain at the AI stage (the Wave 133 e2e
    pattern): the salvage layer's outcome for these
    questions is not the subject under test."""
    monkeypatch.setattr(fallback, "_salvage",
                        lambda q, h: None)


def _ai(kind, answer, steps=None):
    return {"type": "Ganitra", "op": kind, "answer": answer,
            "steps": steps or ["working"],
            "fallback": True, "fallback_kind": kind,
            "ai_generated": True}


def _stub_legs(monkeypatch, gemini=None, groq=None,
               openrouter=None):
    """Stub the three leg seams; returns the call-order
    list. Each value is a result dict, None, or a
    callable."""
    calls = []

    def _mk(name, value, with_req):
        def fake(question, hindi, lang_request=None):
            calls.append(name)
            v = value(question) if callable(value) else value
            return dict(v) if isinstance(v, dict) else v

        def fake_or(question, hindi):
            calls.append(name)
            v = value(question) if callable(value) else value
            return dict(v) if isinstance(v, dict) else v

        return fake if with_req else fake_or

    monkeypatch.setattr(fallback, "_gemini_answer",
                        _mk("gemini", gemini, True))
    monkeypatch.setattr(fallback, "_groq_answer",
                        _mk("groq", groq, True))
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        _mk("openrouter", openrouter, False))
    return calls


# ---------------------------------------------------------------------------
# The last-resort serve
# ---------------------------------------------------------------------------

def test_verification_fail_ai_answer_served_last_resort(
        db, no_salvage, monkeypatch):
    # Gemini's value fails the deterministic check
    # (area_between_curves: the true value is 1/6), the
    # other legs are silent. Pre-Wave-158 this collapsed to
    # not-found; now the leg's own answer is served as-is.
    leg = _ai("gemini", "1/3 square units",
              ["The curves meet at x = 0 and x = 1.",
               "Integrate x - x^2 from 0 to 1."])
    _stub_legs(monkeypatch, gemini=leg, groq=None,
               openrouter=None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["ai_verification"] == "last_resort"
    assert res["ai_last_resort"] == "single"
    # Values and steps are the leg's own, byte-identical —
    # the serve never rewrites numbers (Wave 132's
    # invariant), and there is no disclaimer or apology.
    assert res["answer"] == "1/3 square units"
    assert res["steps"] == leg["steps"]
    assert "not found" not in res["answer"].lower()


def test_majority_beats_first_leg(db, no_salvage,
                                  monkeypatch):
    # All three values fail the deterministic check, but
    # Groq + OpenRouter agree on 1/3 while Gemini (the
    # first leg) says 1/4. The majority value wins and its
    # earliest carrier — Groq, not Gemini — is served.
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/4 square units"),
               groq=_ai("groq", "1/3 square units"),
               openrouter=_ai("openrouter",
                              "1/3 square units"))
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "groq"
    assert res["answer"] == "1/3 square units"
    assert res["ai_verification"] == "last_resort"
    assert res["ai_last_resort"] == "majority"


def test_majority_without_first_leg(db, no_salvage,
                                    monkeypatch):
    # Gemini silent; the two answering legs agree — their
    # shared value is the majority serve.
    _stub_legs(monkeypatch, gemini=None,
               groq=_ai("groq", "1/3 square units"),
               openrouter=_ai("openrouter",
                              "1/3 square units"))
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "groq"
    assert res["ai_last_resort"] == "majority"


def test_no_majority_first_leg_wins(db, no_salvage,
                                    monkeypatch):
    # Three legs, three different (all wrong) values, no
    # transferable method in the vague steps: the first
    # leg's answer is the last resort.
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/4 square units"),
               groq=_ai("groq", "1/5 square units"),
               openrouter=_ai("openrouter",
                              "1/8 square units"))
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["answer"] == "1/4 square units"
    assert res["ai_last_resort"] == "single"


def test_method_transfer_value_beats_ai_values_on_disagreement(
        db, no_salvage, monkeypatch):
    # The legs disagree (118 vs 95, no majority) and both
    # fail the percent deterministic check. Gemini's steps
    # carry a RIGHT method with an arithmetic slip: Wave
    # 134's transfer recomputes it from the question's own
    # numbers and Ganitra serves its OWN 108 — never either
    # AI value, never the last-resort picker.
    _stub_legs(
        monkeypatch,
        gemini=_ai("gemini", "118",
                   ["24% of 450 = 450 × 24/100 = 118"]),
        groq=_ai("groq", "95"),
        openrouter=None)
    # Isolate the transfer seam: the question-only deep
    # stage is not the subject here.
    real_deep = deep_solve.deep_solve

    def spy(question, **kw):
        if kw.get("ai_result") is None:
            return None
        return real_deep(question, **kw)

    monkeypatch.setattr(deep_solve, "deep_solve", spy)
    res = with_fallback(PERCENT_Q, dict(FAILED), lang="en")
    assert res["answer"] == "108"
    assert res["fallback_kind"] == "deep_solve"
    assert not res.get("ai_generated")
    assert res.get("ai_verification") != "last_resort"


# ---------------------------------------------------------------------------
# The verified path is unchanged; the last resort never promotes
# ---------------------------------------------------------------------------

def test_verified_path_and_promotion_unchanged(
        db, no_salvage, monkeypatch):
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/6 square units"),
               groq=None, openrouter=None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["ai_verification"] == "deterministic"
    assert "ai_last_resort" not in res
    rows = livebank.all_rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "verified"
    served = livebank.lookup_live_result(AREA_Q, "en")
    assert served is not None
    assert served["answer"] == "1/6 square units"


def test_last_resort_stays_pending_never_store_served(
        db, no_salvage, monkeypatch):
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/3 square units"),
               groq=None, openrouter=None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["ai_verification"] == "last_resort"
    rows = livebank.all_rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "pending"
    # A repeat ask re-runs the chain; the store never
    # serves the last-resort copy.
    assert livebank.lookup_live_result(AREA_Q, "en") is None


# ---------------------------------------------------------------------------
# The boundaries stand
# ---------------------------------------------------------------------------

def test_all_legs_silent_not_found_remains(
        db, no_salvage, monkeypatch):
    # A genuine maths question, but no leg produced any
    # answer: the honest not-found is the only ending left.
    _stub_legs(monkeypatch, gemini=None, groq=None,
               openrouter=None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "not_found"


def test_nonmaths_still_one_liner_legs_never_consulted(
        db, monkeypatch):
    calls = _stub_legs(monkeypatch,
                       gemini=_ai("gemini", "Paris"),
                       groq=_ai("groq", "Paris"),
                       openrouter=_ai("openrouter", "Paris"))
    res = with_fallback(NONMATHS_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "nonmaths"
    assert calls == []


def test_gibberish_never_reaches_ai_block(
        db, monkeypatch):
    # Pure gibberish is classified before the AI block and
    # keeps the one-line not-found, even with willing legs.
    calls = _stub_legs(monkeypatch,
                       gemini=_ai("gemini", "42"),
                       groq=_ai("groq", "42"),
                       openrouter=_ai("openrouter", "42"))
    res = with_fallback(GIBBERISH_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "not_found"
    assert calls == []


# ---------------------------------------------------------------------------
# The picker itself
# ---------------------------------------------------------------------------

def _rec(leg, answer, check="det_fail"):
    return {"leg": leg, "result": _ai(leg, answer),
            "claim": answer, "check": check}


def test_picker_empty_bundle_returns_none(db):
    assert fallback._last_resort_ai_answer(AREA_Q, []) \
        is None
    assert fallback._last_resort_ai_answer(AREA_Q, None) \
        is None
    assert fallback._last_resort_ai_answer(
        AREA_Q, [{"leg": "gemini", "result": None}]) is None
    assert fallback._last_resort_ai_answer(
        AREA_Q, [_rec("gemini", "  ")]) is None


def test_picker_majority_and_order(db):
    bundle = [_rec("gemini", "1/4 square units"),
              _rec("groq", "1/3 square units"),
              _rec("openrouter", "1/3 square units")]
    out = fallback._last_resort_ai_answer(AREA_Q, bundle)
    assert out["fallback_kind"] == "groq"
    assert out["ai_last_resort"] == "majority"
    # Bundle order does not matter; chain order does.
    out = fallback._last_resort_ai_answer(
        AREA_Q, list(reversed(bundle)))
    assert out["fallback_kind"] == "groq"
    out = fallback._last_resort_ai_answer(
        AREA_Q, [_rec("groq", "7"), _rec("gemini", "9")])
    assert out["fallback_kind"] == "gemini"
    assert out["ai_last_resort"] == "single"
    # The picked candidate is a copy — the bundle's own
    # dict is never marked.
    assert "ai_verification" not in bundle[0]["result"]
