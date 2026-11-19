"""Wave 178: repeat-ask variation (Suraj's standing
rule, 19 Nov 2026 ~09:52 IST).

"agar student ek hi sawal baar-baar puche (khaas kar
guidance ke liye), to har baar kuch ALAG ya SPECIAL
mile — same jawab copy-paste kabhi nahi. Pehli baar
normal short jawab, dusri baar naya example ya extra
tip, teesri baar aur depth / related fact / practice
sawal — asli teacher ki tarah."

Mechanism (repeat.py + route seams in api.py / app.py):
every finished answer gets a repeat KEY — the guidance /
baat / knowledge TOPIC id for the conversational layers
(so a reworded or other-language re-ask of the same
topic is the same ask), the normalised question text
for a solved maths answer. The routes count asks per
chat in the session and, from the 2nd ask on, display a
VARIED COPY: a warm opener + the base card + fresh
authored extra lines (2nd: example / tip; 3rd: depth /
fact / practice) for guidance and knowledge cards; an
alternate authored line for small talk; a framing line
+ an offer line around the UNTOUCHED working for a
solved card. The base result — session state, caches,
history — is never mutated, and a first ask of anything
is byte-identical to before this wave.
"""
import pytest

import repeat
from guidance import baat_result, guidance_result
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


def _has_dev(text):
    return any("ऀ" <= ch <= "ॿ" for ch in str(text or ""))


# ---------------------------------------------------------------------------
# 1. Question normalisation (solved-maths keys)
# ---------------------------------------------------------------------------

def test_normalise_spacing_case_and_glue():
    n = repeat.normalise_question
    assert n("5+3") == n("5 + 3") == n("5+3 batao") == "5+3"
    assert n("WHAT IS 5 + 3?") == "5+3"
    assert n("२ + ३") == "2+3"          # Devanagari digits
    assert n("5 + 3 kya hota hai") == "5+3"


def test_normalise_operator_spellings_fold():
    n = repeat.normalise_question
    assert n("12 x 4") == n("12 × 4") == n("12*4") == "12x4"
    assert n("10 ÷ 2") == n("10/2")


def test_normalise_different_questions_stay_different():
    n = repeat.normalise_question
    assert n("5+3") != n("5-3")
    assert n("5+3") != n("6+3")
    assert n("area of circle radius 5") != \
        n("area of circle radius 6")


# ---------------------------------------------------------------------------
# 2. Repeat keys: topics for conversation, text for solves,
#    nothing for non-answers
# ---------------------------------------------------------------------------

def test_result_key_topics():
    g = guidance_result("maths me kya scope hai")
    assert repeat.result_key("maths me kya scope hai", g) \
        == "g:scope_career"
    # The same topic asked in another language / wording
    # is the SAME key — the topic id, not the text.
    g_en = guidance_result("what can I do after 12th with maths")
    assert repeat.result_key("anything", g_en) \
        == "g:after_12th"
    b = baat_result("kya haal hai")
    assert repeat.result_key("kya haal hai", b) == "b:haal"
    z = meta_result("0 ki khoj kisne ki hai")
    assert repeat.result_key("0 ki khoj kisne ki hai", z) \
        == "m:history:zero"
    z_en = meta_result("Who discovered 0?")
    assert repeat.result_key("Who discovered 0?", z_en) \
        == "m:history:zero"


def test_result_key_solved_and_non_answers():
    solved = {"type": "arithmetic", "op": "evaluate",
              "answer": "8", "steps": ["Evaluate: 8 = 8"]}
    assert repeat.result_key("5+3", solved) == "q:5+3"
    assert repeat.result_key("5 + 3 batao", solved) == "q:5+3"
    for kind in ("not_found", "nonmaths", "gibberish",
                 "science", "vague", "greeting"):
        r = {"type": "x", "op": "y", "answer": "line",
             "steps": [], "fallback_kind": kind,
             "plain_reply": True}
        assert repeat.result_key("whatever", r) is None
    assert repeat.result_key("hi", None) is None
    assert repeat.result_key("hi", {}) is None


# ---------------------------------------------------------------------------
# 3. The variation mechanism itself (unit, fake session)
# ---------------------------------------------------------------------------

def _drive(session, question, result, flavour="roman"):
    return repeat.session_variation(
        session, "chat1", question, result, flavour)


def test_guidance_progression_unit():
    q = "maths me kya scope hai"
    base = guidance_result(q)
    session = {}
    assert _drive(session, q, base) is None          # 1st
    v2 = _drive(session, q, base)
    assert v2 is not None and v2["w178_repeat"] == 2
    assert v2["steps"] != base["steps"]
    # base card lines ride along untouched, extras added
    for line in base["steps"]:
        assert line in v2["steps"]
    assert len(v2["steps"]) > len(base["steps"])
    v3 = _drive(session, q, base)
    assert v3["w178_repeat"] == 3
    assert v3["steps"] != v2["steps"]                # 3rd != 2nd
    v4 = _drive(session, q, base)
    assert v4["w178_repeat"] == 4
    assert v4["steps"] != v3["steps"]                # keeps varying
    # the base result object was never mutated
    assert "w178_repeat" not in base


def test_baat_repeat_swaps_the_line_unit():
    q = "kya haal hai"
    base = baat_result(q)
    session = {}
    assert _drive(session, q, base) is None
    v2 = _drive(session, q, base)
    assert v2["answer"] != base["answer"]
    assert v2["w178_repeat"] == 2
    v3 = _drive(session, q, base)
    assert v3["answer"] != v2["answer"]


def test_knowledge_progression_unit():
    q = "0 ki khoj kisne ki hai"
    base = meta_result(q)
    session = {}
    assert _drive(session, q, base) is None
    v2 = _drive(session, q, base)
    assert v2["w178_repeat"] == 2
    for line in base["steps"]:
        assert line in v2["steps"]
    # both discoverers stay named on every serve
    joined = " ".join(v2["steps"])
    assert "Aryabhata" in joined and "Brahmagupta" in joined
    v3 = _drive(session, q, base)
    assert v3["steps"] != v2["steps"]


def test_solved_repeat_frames_but_never_touches_maths_unit():
    solved = {"type": "arithmetic", "op": "evaluate",
              "answer": "8", "steps": ["Evaluate: 8 = 8"]}
    session = {}
    assert _drive(session, "5+3", solved, "en") is None
    v2 = _drive(session, "5 + 3", solved, "en")
    assert v2["answer"] == "8"
    assert v2["steps"][1:-1] == solved["steps"]      # working intact
    assert len(v2["steps"]) == len(solved["steps"]) + 2
    v3 = _drive(session, "5+3 batao", solved, "en")
    assert v3["w178_repeat"] == 3
    assert v3["steps"] != v2["steps"]


def test_different_question_is_never_a_repeat_unit():
    session = {}
    g1 = guidance_result("maths me kya scope hai")
    g2 = guidance_result("maths kaise improve karu")
    assert _drive(session, "maths me kya scope hai", g1) is None
    # a DIFFERENT topic in the same chat: first ask, unvaried
    assert _drive(session, "maths kaise improve karu", g2) is None
    s1 = {"type": "arithmetic", "op": "evaluate", "answer": "8",
          "steps": ["Evaluate: 8 = 8"]}
    s2 = {"type": "arithmetic", "op": "evaluate", "answer": "9",
          "steps": ["Evaluate: 9 = 9"]}
    assert _drive(session, "5+3", s1, "en") is None
    assert _drive(session, "7+2", s2, "en") is None


def test_counts_are_per_chat_unit():
    q = "maths me kya scope hai"
    base = guidance_result(q)
    session = {}
    assert repeat.session_variation(
        session, "chatA", q, base, "roman") is None
    assert repeat.session_variation(
        session, "chatB", q, base, "roman") is None   # other chat: 1st
    v = repeat.session_variation(
        session, "chatA", q, base, "roman")
    assert v["w178_repeat"] == 2


# ---------------------------------------------------------------------------
# 4. End to end through /api/solve
# ---------------------------------------------------------------------------

def test_client_guidance_progression_x3(client):
    q = "maths me kya scope hai"
    r1 = _solve(client, q)["result"]
    assert r1["fallback_kind"] == "guidance"
    assert "w178_repeat" not in r1
    r2 = _solve(client, q)["result"]
    assert r2["w178_repeat"] == 2
    assert r2["steps"] != r1["steps"]
    for line in r1["steps"]:
        assert line in r2["steps"]
    # a reworded re-ask of the same topic counts on
    r3 = _solve(client, "Maths me scope kya hai?")["result"]
    assert r3["w178_repeat"] == 3
    assert r3["steps"] != r2["steps"]
    # guidance standing rules hold on the varied serves too
    import re as _re
    for r in (r2, r3):
        for line in r["steps"]:
            assert not _re.search(r"₹|salary|LPA", line, _re.I)


def test_client_guidance_devanagari_progression(client):
    q = "गणित में करियर कैसे बनाएं"
    r1 = _solve(client, q)["result"]
    if r1.get("fallback_kind") != "guidance":
        pytest.skip("phrasing does not route to guidance here")
    r2 = _solve(client, q)["result"]
    assert r2["w178_repeat"] == 2
    assert _has_dev(r2["steps"][0])     # opener in Devanagari


def test_client_knowledge_progression_cross_language(client):
    r1 = _solve(client, "0 ki khoj kisne ki hai")["result"]
    assert r1["fallback_kind"] == "history"
    assert "w178_repeat" not in r1
    r2 = _solve(client, "0 ki khoj kisne ki hai")["result"]
    assert r2["w178_repeat"] == 2
    assert not _has_dev(r2["steps"][0])  # Roman opener, Roman card
    r3 = _solve(client, "Who discovered 0?")["result"]
    assert r3["w178_repeat"] == 3       # same topic, other language
    assert not _has_dev(r3["steps"][0])
    for r in (r1, r2, r3):
        joined = " ".join(r["steps"])
        assert "Aryabhata" in joined and "Brahmagupta" in joined


def test_client_solved_progression_x3(client):
    a1 = _solve(client, "12 x 4")["result"]
    assert "w178_repeat" not in a1
    a2 = _solve(client, "12 × 4")["result"]
    assert a2["w178_repeat"] == 2
    a3 = _solve(client, "12*4")["result"]
    assert a3["w178_repeat"] == 3
    assert a1["answer"] == a2["answer"] == a3["answer"] == "48"
    for line in a1["steps"]:
        assert line in a2["steps"] and line in a3["steps"]
    assert a2["steps"] != a3["steps"]


def test_client_baat_repeat(client):
    r1 = _solve(client, "kya haal hai")["result"]
    assert r1["fallback_kind"] == "baat"
    r2 = _solve(client, "kya haal hai")["result"]
    assert r2["w178_repeat"] == 2
    assert r2["answer"] != r1["answer"]


def test_client_controls_no_false_repeats(client):
    _solve(client, "maths me kya scope hai")
    _solve(client, "maths me kya scope hai")
    # a different topic right after: first ask, unvaried
    other = _solve(client, "maths kaise improve karu")["result"]
    assert other["fallback_kind"] == "guidance"
    assert "w178_repeat" not in other
    # a different sum: first ask, unvaried
    s = _solve(client, "7+2")["result"]
    assert "w178_repeat" not in s
    # a non-maths guard line repeated: the exact one-liner
    # both times (standing rule), never varied
    n1 = _solve(client, "who is the prime minister of india")
    n2 = _solve(client, "who is the prime minister of india")
    assert n1["result"].get("answer") == n2["result"].get("answer")
    assert "w178_repeat" not in n2["result"]


def test_client_first_ask_is_the_base_answer(client):
    """A first ask through the client is byte-identical
    to the base chain's own result for the same question
    (the wave changes nothing until a repeat happens)."""
    from fallback import with_fallback
    from solver.router import solve_question
    q = "maths me kya scope hai"
    base = with_fallback(q, solve_question(q))
    got = _solve(client, q)["result"]
    assert got["answer"] == base["answer"]
    assert got["steps"] == base["steps"]


def test_client_language_request_is_not_a_repeat(client):
    """The same question re-asked with an explicit
    language request (Wave 107/130) is a presentation
    channel, not a repeat: served exactly (the solver's
    own steps in the requested language), never counted,
    never varied — and the plain re-ask after it is the
    2nd ask, not the 3rd."""
    quad = "Solve x^2 - 5x + 6 = 0"
    plain = _solve(client, quad)["result"]
    assert "w178_repeat" not in plain
    req = _solve(client, quad + ". Answer in Hindi")["result"]
    assert "w178_repeat" not in req
    assert req["steps"][0].startswith("मानक रूप में लिखिए:")
    again = _solve(client, quad)["result"]
    assert again["w178_repeat"] == 2


def test_client_detail_ask_is_not_a_repeat(client):
    """An explicit detail ask is the student's own
    follow-up channel (Wave 136): it neither counts as a
    repeat nor gets varied — and the plain re-ask after
    it is the 2nd ask, not the 3rd."""
    _solve(client, "maths me kya scope hai")
    d = _solve(client, "maths me scope detail me batao")["result"]
    assert d["fallback_kind"] == "guidance"
    assert "w178_repeat" not in d
    r = _solve(client, "maths me kya scope hai")["result"]
    assert r["w178_repeat"] == 2
