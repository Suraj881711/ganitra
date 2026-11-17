"""Wave 136 (Suraj, 17 Nov 2026): DETAIL ON DEMAND — the
LAMBA ANSWER RULE.

Suraj's standing rule: Ganitra's answers stay SHORT by
default; ONLY when the student explicitly asks for a long /
detailed answer does the SAME answer come in a detailed
version (the reason behind the working + one example).
Never long without being asked.

These tests pin, with ALL AI HTTP layers MOCKED (fixtures
only — no network, no real keys):

- the intent detector's exact phrase set: request-shaped
  detail phrases fire (EN + Hindi Devanagari + Hinglish
  Roman); plain asks, "short me batao" / "bas answer do",
  and questions merely CONTAINING the trigger words as
  maths content ("the details are given below", "how long
  is the train", "(x + 3)^2 का विस्तार कीजिए" — विस्तार is
  EXPAND in Hindi maths) do NOT;
- solver answers expand honestly: the topic's formula +
  why block from the concept layer and ONE worked example
  that was actually re-solved with a different answer —
  in the student's flavour, with a Wave-107 explicit
  language request outranking the question's language;
- concept answers gain an on-topic practice set when the
  topic maps confidently, and are served byte-identically
  when it does not;
- AI answers are detailed at the source: the shared
  prompt's DETAIL variant (all three legs), selected only
  when the flag is on; the flag is forwarded through
  fallback.with_fallback in a way that keeps the pre-136
  call shape byte-identical when it is off (the Wave-107
  test-double signature still works);
- with NO detail request, behaviour is byte-identical to
  before the wave across solver, concept and AI-fixture
  paths, and the negative cache never lets a plain ask
  inherit a detailed outcome (or vice versa);
- the one-line outcomes (not-found) stay one line even
  when detail was asked — there is no solved answer to
  detail.
"""
import pytest

import gemini_fallback
import groq_fallback
import openrouter_fallback
import solver.answer_cache as cache
from api import _solve_friendly
from detail import expand_detail
from langdetect_local import detect_detail_request


@pytest.fixture(autouse=True)
def _clean_caches():
    # Same isolation as test_wave108: the negative cache is
    # process-global, and these tests re-ask shared probe
    # questions with and without the detail flag.
    cache.clear_cache()
    yield
    cache.clear_cache()


HCF_Q = "12 aur 18 ka HCF kya hoga"
AGES_Q = ("Ten years ago, a father was twelve times as "
          "old as his son and ten years hence, he will be "
          "twice as old as his son. Find their present ages.")


# ---------------------------------------------------------------------------
# 1. The detector: request shapes fire, content never does
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "12 aur 18 ka HCF detail me samjhao",
    "detail mein batao HCF of 12 and 18",
    "solve 2x+3=7, explain in detail",
    "answer in detail please",
    "detail batao",
    "give a detailed solution for x^2 - 5x + 6 = 0",
    "detailed answer chahiye",
    "full solution batao",
    "explain fully please",
    "vistar se batao",
    "vistaar se samjhao",
    "mujhe lamba answer chahiye",
    "poora samjhao 15% of 240",
    "विस्तार से समझाओ HCF क्या होता है",
    "लंबा उत्तर दो",
    "डिटेल में बताओ",
    "HCF detail me batao hindi me",
])
def test_detail_phrases_fire(question):
    assert detect_detail_request(question) is True, question


@pytest.mark.parametrize("question", [
    "12 aur 18 ka HCF kya hoga?",
    "solve 2x + 3 = 7",
    "What is the area of a circle with radius 7 cm?",
    "bas answer do",
    "short me batao",
    "sirf answer chahiye, detail nahi",
    "lamba mat karna, bas answer do",
    "ye detail galat hai, sahi answer do",
    "The details of the survey are given below. Find the mean.",
    "A train 200 m long crosses a pole in 10 seconds",
    "How long will it take?",
    "full marks ke liye kya karun?",
    "train kitni lambi hai?",
    "Find the detailed balance point",
    "(x + 3)^2 का विस्तार कीजिए",
    # A steps request is Wave 123's gate, not this one.
    "step by step batao",
    "",
    "   ",
])
def test_non_detail_phrases_do_not_fire(question):
    assert detect_detail_request(question) is False, question


# ---------------------------------------------------------------------------
# 2. The AI prompt variant: only when asked, byte-identical else
# ---------------------------------------------------------------------------

def test_prompt_default_is_byte_identical():
    for lang in (None, "en", "hi", "hinglish"):
        plain = gemini_fallback._build_prompt(AGES_Q, lang)
        assert plain == gemini_fallback._build_prompt(
            AGES_Q, lang, detail=False)
        assert "DETAILED answer" not in plain


def test_prompt_detail_variant_inserts_rules_only():
    plain = gemini_fallback._build_prompt(AGES_Q, None)
    detailed = gemini_fallback._build_prompt(
        AGES_Q, None, detail=True)
    # The ONLY difference is the rules block, inserted
    # before the question; removing it restores the plain
    # prompt byte for byte.
    assert gemini_fallback._DETAIL_RULES in detailed
    assert detailed.replace(
        gemini_fallback._DETAIL_RULES, "") == plain
    assert detailed.index(
        gemini_fallback._DETAIL_RULES) < detailed.index(
            "Student's question:")
    # The detail rules keep the house shape: smaller steps,
    # a reason per step, one example, and the single final
    # Answer: line stays the student's OWN question's.
    rules = gemini_fallback._DETAIL_RULES
    assert "smaller steps" in rules
    assert "reason" in rules
    assert "example" in rules
    assert "student's own question" in rules


def test_prompt_detail_variant_keeps_language_line():
    prompt = gemini_fallback._build_prompt(
        AGES_Q, "hi", detail=True)
    assert "answer in Hindi" in prompt
    assert "DETAILED answer" in prompt


# ---------------------------------------------------------------------------
# 3. All three AI legs select the variant (mocked transports)
# ---------------------------------------------------------------------------

_GEMINI_DETAIL_TEXT = (
    "Let the son's age be x years - we take the son's age "
    "as x\n"
    "Father's age = 45 - x - the two ages add up to 45\n"
    "Answer: Son is 9 years old and father is 36 years old")


def _gemini_payload(text):
    return {"candidates": [
        {"content": {"parts": [{"text": text}]}}]}


def _chat_payload(text):
    return {"choices": [{"message": {"content": text}}]}


def test_gemini_leg_detail_prompt_and_shape(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["content"] = payload["contents"][0]["parts"][0][
            "text"]
        return _gemini_payload(_GEMINI_DETAIL_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json",
                        fake_post)
    out = gemini_fallback.try_gemini_answer(
        AGES_Q, detail=True)
    assert out is not None
    assert "DETAILED answer" in seen["content"]
    # The shaped result keeps the exact house field set.
    assert set(out) == {"type", "op", "answer", "steps",
                        "fallback", "fallback_kind",
                        "ai_generated"}
    assert out["fallback_kind"] == "gemini"
    assert out["answer"] == (
        "Son is 9 years old and father is 36 years old")
    # Without the flag the prompt is the plain one.
    out = gemini_fallback.try_gemini_answer(AGES_Q)
    assert out is not None
    assert "DETAILED answer" not in seen["content"]


def test_groq_leg_detail_prompt(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["content"] = payload["messages"][0]["content"]
        return _chat_payload(_GEMINI_DETAIL_TEXT)

    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.setattr(groq_fallback, "_post_json", fake_post)
    out = groq_fallback.try_groq_answer(AGES_Q, detail=True)
    assert out is not None
    assert out["fallback_kind"] == "groq"
    assert "DETAILED answer" in seen["content"]
    out = groq_fallback.try_groq_answer(AGES_Q)
    assert out is not None
    assert "DETAILED answer" not in seen["content"]


def test_openrouter_leg_detail_prompt(monkeypatch):
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["content"] = payload["messages"][0]["content"]
        return _chat_payload(_GEMINI_DETAIL_TEXT)

    monkeypatch.setenv("GANITRA_OPENROUTER_API_KEY",
                       "test-key")
    monkeypatch.setattr(openrouter_fallback, "_post_json",
                        fake_post)
    out = openrouter_fallback.try_openrouter_answer(
        AGES_Q, detail=True)
    assert out is not None
    assert out["fallback_kind"] == "openrouter"
    assert "DETAILED answer" in seen["content"]
    out = openrouter_fallback.try_openrouter_answer(AGES_Q)
    assert out is not None
    assert "DETAILED answer" not in seen["content"]


def test_chain_forwards_detail_and_keeps_old_call_shape(
        monkeypatch):
    """Through fallback.with_fallback: detail=True reaches
    the Gemini seam as a keyword; with detail off, the seam
    is called EXACTLY as before the wave — the Wave-107
    test double (question, hindi, lang_request=None) must
    keep working unchanged."""
    import fallback

    seen = {}

    def fake_gemini(question, hindi, lang_request=None,
                    **kwargs):
        seen.update(question=question, hindi=hindi,
                    lang_request=lang_request, kwargs=kwargs)
        return {"type": "Ganitra", "op": "gemini",
                "answer": "42", "steps": ["working"],
                "fallback": True, "fallback_kind": "gemini",
                "ai_generated": True}

    monkeypatch.setattr(fallback, "_gemini_answer",
                        fake_gemini)
    failed = {"op": "error",
              "answer": "Could not solve this one: x",
              "steps": []}
    res = fallback.with_fallback(AGES_Q, dict(failed),
                                 lang="en", detail=True)
    assert res["fallback_kind"] == "gemini"
    assert seen["kwargs"] == {"detail": True}

    def strict_gemini(question, hindi, lang_request=None):
        # The pre-Wave-136 double: no detail parameter at
        # all. Any extra argument would raise TypeError.
        return {"type": "Ganitra", "op": "gemini",
                "answer": "42", "steps": ["working"],
                "fallback": True, "fallback_kind": "gemini",
                "ai_generated": True}

    monkeypatch.setattr(fallback, "_gemini_answer",
                        strict_gemini)
    res = fallback.with_fallback(AGES_Q, dict(failed),
                                 lang="en")
    assert res["fallback_kind"] == "gemini"


def test_solve_friendly_keeps_old_with_fallback_shape(
        monkeypatch):
    """_solve_friendly must call api.with_fallback exactly
    as before the wave when detail is off — Wave 48's test
    doubles for it predate the detail parameter and would
    raise TypeError on any extra keyword."""
    import api

    def fake_solve(question):
        return {"type": "solver", "op": "error",
                "answer": "Could not solve", "steps": []}

    def fake_fallback(question, result, lang=None,
                      student_class=None, lang_request=None):
        return {"type": "Ganitra", "op": "not_found",
                "answer": "Answer not found.", "steps": [],
                "fallback": True,
                "fallback_kind": "not_found"}

    monkeypatch.setattr(api, "solve_question", fake_solve)
    monkeypatch.setattr(api, "with_fallback", fake_fallback)
    res = _solve_friendly("an unsolvable ask")
    assert res.get("fallback_kind") == "not_found"


def test_ai_path_end_to_end_with_detail(monkeypatch):
    """The real user path (_solve_friendly) with only the
    Gemini transport mocked: a detail ask on an
    AI-territory question is answered by the detail prompt
    variant; the same question plain gets the plain
    prompt."""
    seen = {}

    def fake_post(url, payload, api_key, timeout):
        seen["content"] = payload["contents"][0]["parts"][0][
            "text"]
        return _gemini_payload(_GEMINI_DETAIL_TEXT)

    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_fallback, "_post_json",
                        fake_post)
    res = _solve_friendly(AGES_Q + " in detail", detail=True)
    assert res.get("fallback_kind") == "gemini", res
    assert "DETAILED answer" in seen["content"]
    cache.clear_cache()
    res = _solve_friendly(AGES_Q)
    assert res.get("fallback_kind") == "gemini", res
    assert "DETAILED answer" not in seen["content"]


# ---------------------------------------------------------------------------
# 4. Solver answers: why block + one verified example
# ---------------------------------------------------------------------------

def test_solver_detail_expansion_hcf():
    plain = _solve_friendly(HCF_Q)
    assert plain.get("answer") == "6"
    cache.clear_cache()
    detailed = _solve_friendly(
        HCF_Q + " detail me samjhao", detail=True)
    # The SAME answer, the SAME solving lines first...
    assert detailed.get("answer") == "6"
    assert detailed["steps"][:len(plain["steps"])] == \
        plain["steps"]
    extra = detailed["steps"][len(plain["steps"]):]
    # ...then the topic's why block from the concept layer,
    # in the concept layer's own words...
    assert "Why this works:" in extra
    assert any(s.startswith("Formula:") and "HCF" in s
               for s in extra)
    assert any("prime factors" in s for s in extra)
    # ...and ONE worked example: a different question of
    # the same type, really solved, with a DIFFERENT
    # answer (never the original question re-served).
    assert "One more example:" in extra
    example_q = extra[extra.index("One more example:") + 1]
    assert example_q != HCF_Q + " detail me samjhao"
    assert "Example answer: 1" in extra


def test_solver_detail_flavour_follows_language():
    # Hinglish ask in a Hindi session: Roman headings and
    # the concept entry's Hinglish line.
    detailed = _solve_friendly(
        HCF_Q + " detail me samjhao", lang="hi", detail=True)
    steps = detailed["steps"]
    assert "Ye aise kyon hota hai:" in steps
    assert "Ek aur example:" in steps
    assert any(s.startswith("Hinglish me:") for s in steps)
    # A Wave-107 explicit English request outranks the
    # Hinglish question for the detail additions too.
    cache.clear_cache()
    detailed_en = _solve_friendly(
        HCF_Q + " detail me samjhao", lang="hi",
        lang_request="en", detail=True)
    steps_en = detailed_en["steps"]
    assert "Why this works:" in steps_en
    assert "Ye aise kyon hota hai:" not in steps_en
    assert not any(s.startswith("Hinglish me:")
                   for s in steps_en)


def test_expand_detail_never_mutates_and_skips_kinds():
    # A fabricated solved result with a question that has
    # no concept entry and no number to nudge: nothing
    # honest can be added, so the SAME dict comes back.
    bare = {"type": "Ganitra", "op": "simplify",
            "answer": "2x + 3", "steps": ["2x + 3"]}
    assert expand_detail("simplify the expression",
                         bare) is bare
    # Proofs are their own why; one-liners stay one line;
    # AI results are detailed at the source, never here.
    proof = {"type": "Ganitra", "op": "proof_identity",
             "answer": "proved", "steps": ["LHS = RHS"],
             "fallback": True, "fallback_kind": "proof"}
    assert expand_detail("prove that x = x", proof) is proof
    not_found = {"type": "Ganitra", "op": "not_found",
                 "answer": "Answer not found.", "steps": [],
                 "fallback": True,
                 "fallback_kind": "not_found", "plain": True}
    assert expand_detail("zqx jkv", not_found) is not_found
    ai = {"type": "Ganitra", "op": "gemini", "answer": "42",
          "steps": ["working"], "fallback": True,
          "fallback_kind": "gemini", "ai_generated": True}
    assert expand_detail("anything", ai) is ai
    # A real expansion returns a COPY: the input's steps
    # are untouched.
    cache.clear_cache()
    plain = _solve_friendly(HCF_Q)
    before = list(plain["steps"])
    expanded = expand_detail(HCF_Q, plain, lang="hi")
    assert expanded is not plain
    assert plain["steps"] == before
    assert expanded["steps"][:len(before)] == before
    assert len(expanded["steps"]) > len(before)


# ---------------------------------------------------------------------------
# 5. Concept answers: practice on a confident mapping only
# ---------------------------------------------------------------------------

def test_concept_detail_adds_on_topic_practice():
    plain = _solve_friendly("HCF kya hota hai")
    assert plain.get("fallback_kind") == "concept"
    cache.clear_cache()
    detailed = _solve_friendly(
        "HCF kya hota hai detail me samjhao", detail=True)
    assert detailed.get("fallback_kind") == "concept"
    # The card itself is unchanged; the practice set is
    # appended after it, on the SAME topic, with its key.
    assert detailed["steps"][:len(plain["steps"])] == \
        plain["steps"]
    extra = detailed["steps"][len(plain["steps"]):]
    assert extra[0] == "Practice — try these yourself:"
    assert any("HCF" in s for s in extra)
    assert any(s.startswith("Answers:") for s in extra)


def test_concept_detail_unmapped_topic_served_as_is():
    plain = _solve_friendly("prime numbers kya hote hai")
    assert plain.get("fallback_kind") == "concept"
    cache.clear_cache()
    detailed = _solve_friendly(
        "prime numbers kya hote hai detail me samjhao",
        detail=True)
    assert detailed.get("fallback_kind") == "concept"
    assert detailed["steps"] == plain["steps"]


# ---------------------------------------------------------------------------
# 6. No request: byte-identical; caches never cross the flag
# ---------------------------------------------------------------------------

def test_no_request_byte_identical_paths():
    plain = _solve_friendly(HCF_Q)
    cache.clear_cache()
    explicit = _solve_friendly(HCF_Q, detail=False)
    assert explicit == plain
    cache.clear_cache()
    concept = _solve_friendly("HCF kya hota hai")
    cache.clear_cache()
    concept_explicit = _solve_friendly(
        "HCF kya hota hai", detail=False)
    assert concept_explicit == concept


def test_negative_cache_never_crosses_detail_flag():
    # Concept outcomes are negative-cacheable: ask plain,
    # then detail (same text, flag on) — the detail ask
    # must NOT be served the pinned plain outcome...
    plain = _solve_friendly("HCF kya hota hai")
    detailed = _solve_friendly("HCF kya hota hai",
                               detail=True)
    assert len(detailed["steps"]) > len(plain["steps"])
    # ...and a later plain ask still gets the plain card,
    # never the pinned detailed one.
    again = _solve_friendly("HCF kya hota hai")
    assert again["steps"] == plain["steps"]


def test_not_found_stays_one_line_with_detail():
    res = _solve_friendly("zqx jkv wqpl detail me samjhao",
                          detail=True)
    assert res.get("fallback_kind") == "not_found"
    assert res.get("steps") in (None, [])


# ---------------------------------------------------------------------------
# 7. End to end through the real chat route
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def test_api_solve_detail_end_to_end(client):
    body = client.post("/api/solve", json={
        "question": HCF_Q + " detail me samjhao"}).get_json()
    assert body["ok"] is True
    result = body["result"]
    assert result["answer"] == "6"
    # The session language is Hindi (Hinglish ask), so the
    # detail additions arrive in the Roman flavour.
    assert "Ye aise kyon hota hai:" in result["steps"]
    assert "Ek aur example:" in result["steps"]


def test_api_solve_plain_end_to_end(client):
    body = client.post("/api/solve", json={
        "question": HCF_Q}).get_json()
    assert body["ok"] is True
    result = body["result"]
    assert result["answer"] == "6"
    assert not any("kyon hota hai" in s or "example" in s
                   for s in result["steps"])
