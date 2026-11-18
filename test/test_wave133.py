"""Wave 133: AI-answer verification — "jawab ki jaanch".

Suraj's order (17 Nov 2026): the big AIs sometimes answer
wrong with full confidence; Ganitra must ANALYSE an AI
answer and serve it only when it is right. Until this wave
the AI fallback chain (Gemini -> Groq -> OpenRouter) was the
one layer whose answers were served with no correctness
check at all. Proven here, with every leg STUBBED at the
fallback seam (the Wave 117 pattern — no network, no keys):

- the deterministic checks recompute the claimed final
  value from the QUESTION itself (SymPy / exact rationals):
  correct AI answers pass; the classic AI mistakes fail —
  an arithmetic slip, a common-but-not-greatest "HCF", a
  root that does not satisfy its equation, an incomplete
  root set, an integral with a wrong term;
- the sanity gate rejects hard impossibilities outright
  (a probability of 3/2, a negative area);
- when no deterministic check applies, cross-leg consensus
  decides: two legs agreeing serve the earliest carrier; a
  disagreement is settled by the third leg (2-of-3); no
  majority serves NOTHING (the honest not-found stands);
- a deterministic failure is decisive even when legs agree
  with each other — two legs wrong the same way cannot
  outvote arithmetic (and, honestly pinned: when NO
  deterministic check exists for the type, two legs wrong
  the same way DO pass as consensus — the documented limit);
- cost discipline: a deterministic pass on the first leg
  consults no other leg; consensus stops at the first
  agreeing pair;
- a deterministic-verified AI answer is promoted to
  VERIFIED in the Live Bank (via set_status) and a repeat
  ask is served from the store; a consensus answer stays
  PENDING and is never served from the store;
- total verification failure preserves the rejected bundle
  for Wave 134's deep-solve stage (the _verified_ai_answer
  rejected_sink seam) and logs every rejection in
  ai_verify_log; the served not-found dict never carries
  the bundle;
- solver / bank answers never pass through the gate, the
  science and non-maths guards are untouched, prose answers
  to prose questions (the Wave 111 meta flow) serve exactly
  as before, and GANITRA_AIVERIFY=0 restores the pre-wave
  chain byte-for-byte.
"""
import pytest

import aiverify
import fallback
import livebank
from fallback import fallback_answer, with_fallback

FAILED = {"op": "error",
          "answer": "Could not solve this one: x",
          "steps": []}

AGES_Q = ("Ten years ago, a father was twelve times as old "
          "as his son and ten years hence, he will be twice "
          "as old as his son. Find their present ages.")
AGES_RIGHT = "The present ages are 34 and 12."
AGES_WRONG = "The present ages are 42 and 17."
AGES_WRONG2 = "The present ages are 40 and 15."

AREA_Q = "Find the area between the curves y = x^2 and y = x"
HCF_Q = "Find the HCF of 144 and 180"
COIN_Q = ("What is the probability of getting a head when "
          "a coin is tossed?")
GARDEN_Q = ("A rectangular garden is 25 m long and 15 m wide. "
            "A path of width 2 m is built around it on the "
            "outside. Find the area of the path.")
EULER_Q = "Euler kaun the?"
SCIENCE_Q = ("What is the refractive index of a medium?")
PERCENT_Q = "What is 17% of 380?"


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w133.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_LIVEBANK", raising=False)
    monkeypatch.delenv("GANITRA_AIVERIFY", raising=False)
    return path


def _ai(kind, answer, steps=None):
    return {"type": "Ganitra", "op": kind, "answer": answer,
            "steps": steps or ["working"],
            "fallback": True, "fallback_kind": kind,
            "ai_generated": True}


def _stub_legs(monkeypatch, gemini=None, groq=None,
               openrouter=None):
    """Stub the three leg seams; returns the call-order list.
    Each value is a result dict, None, or a callable."""
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


def _legs(**kw):
    """Direct verify_chain legs from name -> result/None."""
    out = []
    for name in ("gemini", "groq", "openrouter"):
        value = kw.get(name)
        out.append((name, (lambda v: lambda: v)(value)))
    return out


# ---------------------------------------------------------------------------
# 1. The deterministic checks: correct passes, classic AI mistakes fail
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,answer", [
    (HCF_Q, "36"),
    ("Find the LCM of 12 and 18", "36"),
    ("Solve the equation 3x + 7 = 22", "x = 5"),
    ("Solve x^2 - 5x + 6 = 0", "x = 2, x = 3"),
    (PERCENT_Q, "64.6"),
    ("Integrate x^2 + 3x with respect to x",
     "x^3/3 + 3x^2/2 + C"),
    ("Find the derivative of x^3 + 2x", "3x^2 + 2"),
    (AREA_Q, "1/6 square units"),
    (COIN_Q, "1/2"),
    ("What is the probability of getting a 4 when a die "
     "is rolled?", "1/6"),
    ("What is the probability of getting a sum of 7 when "
     "two dice are thrown?", "1/6"),
    ("A bag contains 5 red balls and 3 blue balls. A ball "
     "is drawn at random. What is the probability that it "
     "is a red ball?", "5/8"),
    ("One card is drawn from a pack of 52 cards. What is "
     "the probability of getting a king?", "1/13"),
    ("What is the simple interest on Rs 5000 at 5% per "
     "annum for 3 years?", "Rs 750"),
    ("Find two numbers whose sum is 27 and whose "
     "difference is 5.", "16 and 11"),
    ("A train running at the speed of 60 km/hr crosses a "
     "pole in 9 seconds. What is the length of the train?",
     "150 m"),
    ("Divide Rs 1200 among A, B and C in the ratio "
     "2 : 3 : 5.", "Rs 240, Rs 360 and Rs 600"),
    ("What is the area of a rectangle whose length is "
     "12 cm and breadth is 5 cm?", "60 sq cm"),
    ("What is the circumference of a circle with radius "
     "7 cm?", "44 cm"),
    ("Add 2/3 and 3/4", "17/12"),
    ("Calculate the value of 15 + 25 x 4", "115"),
])
def test_deterministic_checks_pass_correct_answers(
        question, answer):
    verdict, _name = aiverify.deterministic_check(
        question, {"answer": answer})
    assert verdict == "pass"


@pytest.mark.parametrize("question,answer", [
    (HCF_Q, "12"),            # a common factor, not the greatest
    ("Find the LCM of 12 and 18", "72"),
    ("Solve the equation 3x + 7 = 22", "x = 6"),   # root fails plug-back
    ("Solve x^2 - 5x + 6 = 0", "x = 2"),           # incomplete root set
    ("Solve x^2 - 5x + 6 = 0", "x = 2, x = 4"),    # one root is wrong
    (PERCENT_Q, "64.8"),                           # arithmetic slip
    ("Integrate x^2 + 3x with respect to x",
     "x^3/3 + 3x^2 + C"),                          # wrong integral term
    ("Find the derivative of x^3 + 2x", "3x^2 + 1"),
    (AREA_Q, "1/3 square units"),
    (COIN_Q, "1/4"),
    ("What is the simple interest on Rs 5000 at 5% per "
     "annum for 3 years?", "Rs 700"),
    ("Find two numbers whose sum is 27 and whose "
     "difference is 5.", "15 and 12"),
    ("A train running at the speed of 60 km/hr crosses a "
     "pole in 9 seconds. What is the length of the train?",
     "540 m"),                                     # forgot unit conversion
    ("Add 2/3 and 3/4", "5/7"),
    ("Calculate the value of 15 + 25 x 4", "160"),  # BODMAS slip
])
def test_deterministic_checks_catch_classic_ai_mistakes(
        question, answer):
    verdict, _name = aiverify.deterministic_check(
        question, {"answer": answer})
    assert verdict == "fail"


def test_sanity_gate_rejects_impossible_values():
    ok, name = aiverify.sanity_check(
        COIN_Q, {"answer": "3/2"})
    assert not ok and name == "sanity_probability_bounds"
    ok, name = aiverify.sanity_check(
        "What is the area of a rectangle whose length is "
        "12 cm and breadth is 5 cm?", {"answer": "-60 sq cm"})
    assert not ok and name == "sanity_negative_measure"
    ok, _ = aiverify.sanity_check(COIN_Q, {"answer": "1/2"})
    assert ok


# ---------------------------------------------------------------------------
# 2. verify_chain: deterministic outcomes and cost discipline
# ---------------------------------------------------------------------------

def test_det_pass_first_leg_consults_no_other_leg(db):
    calls = []

    def leg(name, value):
        def call():
            calls.append(name)
            return value
        return call
    legs = [("gemini", leg("gemini", _ai("gemini", "36"))),
            ("groq", leg("groq", _ai("groq", "36"))),
            ("openrouter", leg("openrouter",
                               _ai("openrouter", "36")))]
    out = aiverify.verify_chain(HCF_Q, legs)
    assert out["answer"] == "36"
    assert out["ai_verification"] == "deterministic"
    assert out["ai_verify_check"] == "hcf"
    assert calls == ["gemini"]  # free check, zero extra quota


def test_det_fail_moves_to_next_leg_and_logs(db):
    legs = _legs(gemini=_ai("gemini", "12"),
                 groq=_ai("groq", "36"),
                 openrouter=_ai("openrouter", "36"))
    out = aiverify.verify_chain(HCF_Q, legs)
    assert out["fallback_kind"] == "groq"
    assert out["ai_verification"] == "deterministic"
    rows = aiverify.all_rejections()
    assert len(rows) == 1
    assert rows[0]["leg"] == "gemini"
    assert rows[0]["claimed"] == "12"
    assert rows[0]["check_name"] == "hcf"


def test_all_legs_wrong_same_way_deterministic_still_wins(db):
    # The brief's hard case: every leg agrees on the WRONG
    # value — consensus must never outvote arithmetic.
    legs = _legs(gemini=_ai("gemini", "12"),
                 groq=_ai("groq", "12"),
                 openrouter=_ai("openrouter", "12"))
    seen = []
    out = aiverify.verify_chain(
        HCF_Q, legs,
        on_rejected=lambda q, r: seen.append((q, r)))
    assert out is None
    assert len(seen) == 1
    q, rejected = seen[0]
    assert q == HCF_Q
    assert [r["leg"] for r in rejected] == [
        "gemini", "groq", "openrouter"]
    assert all(r["check"] == "hcf" for r in rejected)
    # The rejected bundle carries the full shaped results
    # (steps included) — Wave 134's method-transfer input.
    assert rejected[0]["result"]["steps"] == ["working"]
    assert len(aiverify.all_rejections()) == 3


# ---------------------------------------------------------------------------
# 3. verify_chain: consensus where no deterministic check exists
# ---------------------------------------------------------------------------

def test_consensus_two_agreeing_legs_serve_first(db):
    legs = _legs(gemini=_ai("gemini", AGES_RIGHT),
                 groq=_ai("groq", AGES_RIGHT),
                 openrouter=_ai("openrouter", AGES_WRONG))
    out = aiverify.verify_chain(AGES_Q, legs)
    assert out["fallback_kind"] == "gemini"
    assert out["ai_verification"] == "consensus"


def test_consensus_stops_at_first_agreeing_pair(db):
    calls = []

    def leg(name, value):
        def call():
            calls.append(name)
            return value
        return call
    legs = [("gemini", leg("gemini", _ai("gemini", AGES_RIGHT))),
            ("groq", leg("groq", _ai("groq", AGES_RIGHT))),
            ("openrouter",
             leg("openrouter", _ai("openrouter", AGES_WRONG)))]
    out = aiverify.verify_chain(AGES_Q, legs)
    assert out["ai_verification"] == "consensus"
    assert calls == ["gemini", "groq"]  # third leg never asked


def test_consensus_third_leg_breaks_the_tie(db):
    # First leg wrong, second and third right: the majority
    # value wins and its EARLIEST carrier (leg 2) is served.
    legs = _legs(gemini=_ai("gemini", AGES_WRONG),
                 groq=_ai("groq", AGES_RIGHT),
                 openrouter=_ai("openrouter", AGES_RIGHT))
    out = aiverify.verify_chain(AGES_Q, legs)
    assert out["fallback_kind"] == "groq"
    assert out["answer"] == AGES_RIGHT
    assert out["ai_verification"] == "consensus"


def test_consensus_no_majority_serves_nothing(db):
    legs = _legs(gemini=_ai("gemini", AGES_WRONG),
                 groq=_ai("groq", AGES_RIGHT),
                 openrouter=_ai("openrouter", AGES_WRONG2))
    seen = []
    out = aiverify.verify_chain(
        AGES_Q, legs,
        on_rejected=lambda q, r: seen.append(r))
    assert out is None
    # The disagreeing candidates are preserved for the Wave
    # 134 seam as "no_consensus" records (their methods are
    # deep-solve input even though no value was verified).
    assert len(seen) == 1
    assert [r["check"] for r in seen[0]] == ["no_consensus"] * 3
    rows = aiverify.all_rejections()
    assert len(rows) == 3
    assert all(r["check_name"] == "no_consensus" for r in rows)


def test_consensus_same_wrong_answer_is_the_documented_limit(db):
    # No deterministic check exists for the ages word problem,
    # so two legs wrong THE SAME WAY pass as consensus. This
    # pins the honest limit of cross-leg agreement (the notes
    # carry it as a known limitation, not a surprise).
    legs = _legs(gemini=_ai("gemini", AGES_WRONG),
                 groq=_ai("groq", AGES_WRONG),
                 openrouter=None)
    out = aiverify.verify_chain(AGES_Q, legs)
    assert out is not None
    assert out["ai_verification"] == "consensus"


def test_single_available_leg_is_the_degraded_path(db):
    legs = _legs(gemini=_ai("gemini", AGES_RIGHT),
                 groq=None, openrouter=None)
    out = aiverify.verify_chain(AGES_Q, legs)
    assert out["answer"] == AGES_RIGHT
    assert out["ai_verification"] == "single"


def test_sanity_rejection_then_deterministic_pass(db):
    legs = _legs(gemini=_ai("gemini", "3/2"),
                 groq=_ai("groq", "1/2"),
                 openrouter=None)
    out = aiverify.verify_chain(COIN_Q, legs)
    assert out["fallback_kind"] == "groq"
    assert out["ai_verification"] == "deterministic"
    rows = aiverify.all_rejections()
    assert len(rows) == 1
    assert rows[0]["check_name"] == "sanity_probability_bounds"


def test_no_claim_for_a_value_question_is_rejected(db):
    legs = _legs(
        gemini=_ai("gemini", "The path makes the garden "
                            "look bigger"),
        groq=_ai("groq", "216 sq m"),
        openrouter=None)
    out = aiverify.verify_chain(GARDEN_Q, legs)
    assert out["answer"] == "216 sq m"
    assert out["ai_verification"] == "single"
    rows = aiverify.all_rejections()
    assert len(rows) == 1 and rows[0]["check_name"] == "no_claim"


def test_prose_answer_to_prose_question_serves_as_before(db):
    sentinel = {"type": "AI", "op": "gemini",
                "answer": "AI sentinel", "steps": [],
                "fallback": True, "fallback_kind": "gemini"}
    calls = []

    def leg(name, value):
        def call():
            calls.append(name)
            return value
        return call
    legs = [("gemini", leg("gemini", dict(sentinel))),
            ("groq", leg("groq", _ai("groq", "other"))),
            ("openrouter", leg("openrouter", None))]
    out = aiverify.verify_chain(EULER_Q, legs)
    assert out["answer"] == "AI sentinel"
    assert "ai_verification" not in out
    assert calls == ["gemini"]  # no consensus burn on prose


def test_kill_switch_restores_pre_wave_chain(db, monkeypatch):
    monkeypatch.setenv("GANITRA_AIVERIFY", "0")
    legs = _legs(gemini=_ai("gemini", "12"),  # wrong, but the
                 groq=_ai("groq", "36"),      # old chain served
                 openrouter=None)             # the first answer
    out = aiverify.verify_chain(HCF_Q, legs)
    assert out["answer"] == "12"
    assert "ai_verification" not in out


# ---------------------------------------------------------------------------
# 4. End-to-end through the real chain (fallback.with_fallback)
# ---------------------------------------------------------------------------

def test_e2e_deterministic_verified_and_promoted(db,
                                                 monkeypatch):
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/6 square units"),
               groq=_ai("groq", "1/6 square units"),
               openrouter=None)
    # Deploy-27 merge: Wave 125's solver now answers AREA_Q
    # deterministically — and its fragments too, which the
    # salvage layer re-solves — so this e2e enters the chain
    # at the fallback seam with a failed standing (the same
    # pattern as the consensus e2e below) and salvage stubbed
    # to its pre-Wave-125 outcome for this question. The
    # subject under test is the AI verification stage.
    monkeypatch.setattr(fallback, "_salvage",
                        lambda q, h: None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["ai_verification"] == "deterministic"
    assert res["ai_verify_check"] == "area_between_curves"
    # Promotion: the Live Bank row is VERIFIED, so a repeat
    # ask is served from the store.
    rows = livebank.all_rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "verified"
    served = livebank.lookup_live_result(AREA_Q, "en")
    assert served is not None
    assert served["answer"] == "1/6 square units"


def test_e2e_consensus_stays_pending(db, monkeypatch):
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", AGES_RIGHT),
               groq=_ai("groq", AGES_RIGHT),
               openrouter=None)
    res = with_fallback(AGES_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["ai_verification"] == "consensus"
    rows = livebank.all_rows()
    assert len(rows) == 1
    assert rows[0]["status"] == "pending"
    assert livebank.lookup_live_result(AGES_Q, "en") is None


def test_e2e_all_wrong_falls_through_to_not_found(db,
                                                   monkeypatch):
    # Wave 158 SUPERSESSION (Suraj, 18 Nov 2026 — "jawab
    # milega hi"): this scenario's ending changed by
    # order. Verification still fails every candidate
    # (1/3 and 1/4 are both wrong; the true value is 1/6)
    # and every rejection is still logged — but the chain
    # no longer collapses to not-found while a leg's answer
    # stands: Gemini + Groq agree on 1/3, so the last
    # resort serves that majority value's earliest carrier
    # (Gemini), marked "last_resort". The full Wave 158
    # behaviour is pinned in test_wave158.py.
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/3 square units"),
               groq=_ai("groq", "1/3 square units"),
               openrouter=_ai("openrouter", "1/4 square units"))
    # Deploy-27 merge: entered at the fallback seam — see
    # test_e2e_deterministic_verified_and_promoted.
    monkeypatch.setattr(fallback, "_salvage",
                        lambda q, h: None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["answer"] == "1/3 square units"
    assert res["ai_verification"] == "last_resort"
    assert res["ai_last_resort"] == "majority"
    # The served not-found dict never carries the Wave 134
    # bundle (it lives on the chain's internal fall-through
    # result only, inside _with_fallback_chain).
    assert "_ai_rejected" not in res
    assert len(aiverify.all_rejections()) == 3


def test_wave134_seam_receives_the_rejected_bundle(db,
                                                   monkeypatch):
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", "1/3 square units"),
               groq=None, openrouter=None)
    sink = []
    out = fallback._verified_ai_answer(
        AREA_Q, False, None, sink)
    assert out is None
    assert len(sink) == 1
    bundle = sink[0]
    assert bundle["question"] == AREA_Q
    assert len(bundle["rejected"]) == 1
    rec = bundle["rejected"][0]
    assert rec["leg"] == "gemini"
    assert rec["check"] == "area_between_curves"
    assert rec["result"]["answer"] == "1/3 square units"


def test_solver_answers_never_reach_the_gate(db, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("AI leg consulted for a "
                             "solver answer")
    monkeypatch.setattr(fallback, "_gemini_answer", boom)
    monkeypatch.setattr(fallback, "_groq_answer", boom)
    monkeypatch.setattr(fallback, "_openrouter_answer", boom)
    res = fallback_answer(PERCENT_Q, lang="en")
    assert res["answer"] == "64.6"
    assert "ai_verification" not in res


def test_guards_unchanged_by_the_gate(db, monkeypatch):
    calls = _stub_legs(monkeypatch,
                       gemini=_ai("gemini", "anything"),
                       groq=_ai("groq", "anything"),
                       openrouter=_ai("openrouter", "anything"))
    res = fallback_answer(SCIENCE_Q, lang="en")
    assert res["fallback_kind"] == "science"
    res = fallback_answer("What is the capital of France?",
                          lang="en")
    assert res["fallback_kind"] == "nonmaths"
    assert calls == []  # neither guard ever consults a leg


def test_e2e_prose_meta_flow_unchanged(db, monkeypatch):
    sentinel = {"type": "AI", "op": "gemini",
                "answer": "AI sentinel", "steps": [],
                "fallback": True, "fallback_kind": "gemini"}
    _stub_legs(monkeypatch, gemini=sentinel, groq=None,
               openrouter=None)
    res = fallback_answer(EULER_Q, lang="en")
    assert res.get("answer") == "AI sentinel"
    assert "ai_verification" not in res
