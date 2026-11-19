"""Wave 185 (Suraj, 19 Nov 2026: "Prediction ko majboot
karo", then "Prediction ke liye deep mai jaao") — the
PREDICTION BATTERY: 110 messy, natural, spoken-style
questions, the way real students actually ask (voice-
typed, extra clauses, fillers, greetings attached,
misspellings, board/exam dress, childish phrasing,
follow-up fragments), driven through fallback_answer()
with no API keys.

A battery question PASSES when it gets a real answer:
a curated card (history / fact), a concept card, a
native solve, or — for questions whose correct home is
the AI chain — a served AI answer with the legs stubbed
(the Wave 111/183 harness). It FAILS when a genuine
maths question ends at not-found with the legs never
consulted, is classified gibberish, or is served a
WRONG card / wrong value.

Before this wave the battery stood at 84/110. The 26
failures, each fixed at the FAMILY level (never a
one-question special case):
  * voice-spelled names/words missed every curated
    keyword ("aryabhat", "jero", "brahmgupt", "sifr",
    "ramanuja", "aljebra", "praakritik") — gibberish.
  * contribution shapes in spoken dress missed
    ("ne kya kia", "ne kya khoja", "ke baare me" in its
    other orders).
  * origin asks in spoken dress missed ("shuruaat
    kahan se hui", "avishkar kahan hua").
  * "ganit ka pita / ka janak" — the father-of titles
    existed only in their "ke" spellings.
  * the follow-up fragment "iska example do" was
    gibberish while its sibling fragments reached the
    AI legs (new maths_meta.is_followup_shaped net).
  * a percent-spent word problem was deep-solved as a
    bare subtraction (240 - 35 = 205 for "35% kharch";
    the money-left core now refuses any percent text).
  * a labelled-speed distance ask was read as
    distance-over-time ("60 km ki speed se 2 ghante,
    kitni door" answered 30 km/h; the router now
    rewrites it to the distance form, 120 km).
  * the deep stage manufactured "Evaluate: 0 = 0" out
    of the WORD zero for knowledge asks (new
    fallback._w185_veto, the mirror of Wave 177's).
  * an exam-dress REPORT of a content ask was hijacked
    by exam advice ("exam me pucha gaya tha ki pi ka
    maan..." served exam strategy; advice now yields
    to an embedded content ask).
  * specific subtopic asks collapsed to the generic
    topic ("matrix ka ulta" served matrix OPERATIONS;
    "vyas" matched nothing) — alias family completed.

AI-CHAIN DEPTH (probed with stubbed legs, section 9):
  (b) all legs silent on a knowledge miss: the question
      still classifies as knowledge — never gibberish.
  (a) FINDING, pinned as-is for a parent decision: for
      a PROSE knowledge question, Wave 133's chain
      serves the FIRST leg's sane answer immediately
      and never consults the other legs (the prose
      branch: no value claim exists for arithmetic to
      judge). So one wrong GK answer from leg 1 IS
      served unverified — see
      test_ai_chain_prose_first_leg_served_unverified.
      No small deterministic fix exists: prose carries
      no machine-checkable claim to compare across
      legs. Options belong to the parent (accept the
      quota discipline / spend a second leg + judge /
      restrict AI GK to checkable claims).
"""
import pytest

import fallback
from deep_solve import _core_money_left, deep_solve
from fallback import _is_gibberish, _w185_veto, \
    fallback_answer
from maths_meta import is_followup_shaped, \
    is_knowledge_shaped, is_meta_shaped, meta_result
from solver.router import solve_question


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the real AI legs stay inert (the routing
    tests patch the chain functions directly)."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _blob(out):
    return (str(out.get("answer") or "") + " "
            + " ".join(out.get("steps") or []))


def _patch_ai(monkeypatch, reply):
    """The Wave 111 harness: stub the three AI legs at
    fallback's own seams and record Gemini's calls."""
    calls = []

    def fake_gemini(question, hindi, lang_request=None):
        calls.append(question)
        return reply

    monkeypatch.setattr(fallback, "_gemini_answer",
                        fake_gemini)
    monkeypatch.setattr(fallback, "_groq_answer",
                        lambda *a, **k: None)
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        lambda *a, **k: None)
    return calls


_SENTINEL = {
    "type": "AI", "op": "gemini", "answer": "AI sentinel",
    "steps": [], "fallback": True, "fallback_kind": "gemini",
}


# ---------------------------------------------------------------------------
# 1. Curated cards — GK people & things, every dress
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,op", [
    # F1: people — contribution + identity, varied forms
    ("Ramanujan ne kya kiya tha", "history_ramanujan"),
    ("Pythagoras kaun tha aur usne kya diya",
     "history_pythagoras"),
    ("Euclid ke baare me kuch batao", "history_euclid"),
    ("Bhaskara ne kya khoja tha", "history_bhaskara"),
    ("गणित के पिता कौन है", "history_archimedes"),
    ("Shakuntala Devi kaun thi", "history_shakuntala_devi"),
    ("Shakuntala Devi ne kya kiya tha",
     "history_shakuntala_devi"),
    ("Srinivasa Ramanujan kaun the", "history_ramanujan"),
    ("Ramanujan ka yogdaan kya tha", "history_ramanujan"),
    ("ganit ka pita kaun hai", "history_archimedes"),
    ("trigonometry ke janak kaun hai",
     "history_trigonometry"),
    ("Aryabhata kaun the aur unhone kya kiya",
     "history_aryabhata"),
    ("बताओ भास्कराचार्य कौन थे", "history_bhaskara"),
    # F2: things / origins / number facts
    ("zero kisne banaya tha aur kyu", "history_zero"),
    ("शून्य का आविष्कार कहाँ हुआ था", "history_zero"),
    ("pi ki khoj kisne ki", "history_pi"),
    ("algebra kahan se aaya", "fact_algebra_origin"),
    ("sabse chhoti sankhya konsi hai",
     "fact_smallest_number"),
    ("sabse badi prime number konsi hai",
     "fact_largest_prime_none"),
    ("geometry ki shuruaat kahan se hui",
     "fact_geometry_origin"),
    ("pi ka value kisne nikala tha", "history_pi"),
    ("sabse chhoti prime sankhya konsi hai",
     "fact_prime_two"),
    ("1 crore me kitne zero hote hai", "fact_crore_zeros"),
    ("decimal system kahan se aaya", "fact_decimal_system"),
    ("sabse bada number konsa hota hai",
     "fact_largest_number"),
    # F7: misspellings / voice-typing errors
    ("aryabhat ne kya kia tha", "history_aryabhata"),
    ("jero kisne banaya", "history_zero"),
    ("brahmgupt kaun tha", "history_brahmagupta"),
    ("aljebra kahan se aaya", "fact_algebra_origin"),
    ("aryabhata ne kya kiya ta", "history_aryabhata"),
    ("sifr kisne banaya", "history_zero"),
    ("ramanuja kaun tha", "history_ramanujan"),
    # F8: greetings / fillers attached
    ("namaste sir ek sawal tha zero kisne khoja tha",
     "history_zero"),
    ("bhai suno, sabse chhoti abhaajya sankhya konsi hai",
     "fact_prime_two"),
    # F9: class spread (youngest dress)
    ("sabse chhoti sankhya konsi hoti hai",
     "fact_smallest_number"),
    # F10: more GK people / topics
    ("ganit ka janak kise kehte hai", "history_archimedes"),
    ("geometry ke pita kaun hai", "history_euclid"),
    ("pi day kab manaya jata hai", "fact_pi_day"),
    ("barabar ka chinh kisne banaya", "fact_equals_sign"),
    ("infinity ka chinh kisne banaya", "fact_infinity"),
    # F11: multi-intent (the named intent is answered)
    ("zero kisne banaya aur uska ulta kya hota hai",
     "history_zero"),
    ("wohi wala sawal phir se puch raha hu, zero kisne "
     "banaya tha", "history_zero"),
    ("aur detail me batao zero ke baare me", "history_zero"),
    # F12: board / exam dress
    ("MP board me aane wala sawal hai, zero ka avishkar "
     "kisne kiya", "history_zero"),
    ("CBSE ka sawal hai, sabse chhoti praakritik sankhya "
     "konsi hai", "fact_smallest_natural"),
])
def test_battery_cards(question, op):
    r = fallback_answer(question)
    assert r["op"] == op, question
    assert r["fallback_kind"] == op.split("_")[0], question


# ---------------------------------------------------------------------------
# 2. Concept cards in spoken dress
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,word", [
    ("ye HCF LCM hota kya hai yaar", "HCF"),
    ("bhai ye percentage wala samjha do", "Percentage"),
    ("मुझे त्रिकोणमिति समझ नहीं आती बताओ", "Trigonometric"),
    ("what is this trigonometry thing", "Trigonometric"),
    ("average ka matlab kya hota hai", "Mean"),
    ("ye BODMAS kya hota hai", "BODMAS"),
    ("ratio matlab kya hai samjhao", "Ratio"),
    ("hello ganitra mujhe ye batao HCF kya hota hai",
     "HCF"),
    ("arre yaar ye wala samjha do, vyaj kaise nikalte "
     "hai", "Simple Interest"),
    ("sir please batao pi ka matlab kya hai", "Pi"),
    ("namaskar, mujhe ye jaanna hai ki vritt ka "
     "kshetrafal kaise nikalta hai", "Circle"),
    ("integration kya hota hai batao", "Integration"),
    ("probability matlab kya hota hai batao",
     "Probability"),
    ("HCF kya hota hai aur ek example bhi do", "HCF"),
    ("board exam me aayega, HCF aur LCM me fark batao",
     "HCF"),
    # The exam-dress hijack: a pi-value ask, NOT advice.
    ("exam me pucha gaya tha ki pi ka maan kitna hota "
     "hai", "Pi"),
    ("pythagorus theorm kya hai", "Pythagoras"),
    ("parsentage kaise nikale", "Percentage"),
    ("trignometry kya hai", "Trigonometric"),
])
def test_battery_concepts(question, word):
    r = fallback_answer(question)
    assert r["fallback_kind"] == "concept", question
    assert word in _blob(r), question


def test_battery_concept_specific_subtopics():
    # A specific subtopic ask must not collapse to the
    # generic topic card (or to nothing).
    r = fallback_answer("matrix ka ulta kaise nikale")
    assert r["fallback_kind"] == "concept"
    assert r["topic_slug"] == "inverse-of-a-3-by-3-matrix"
    r = fallback_answer(
        "2 number ka sawal hai batao vyas kya hota hai")
    assert r["fallback_kind"] == "concept"
    assert r["topic_slug"] == "radius-and-diameter"


# ---------------------------------------------------------------------------
# 3. Native solves in spoken dress
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,answer", [
    ("ek train 60 km ki speed se 2 ghante chalti hai "
     "kitni door gayi", "120"),
    ("ek aayat ki lambai 8 hai chaudai 5 hai area batao",
     "40"),
    ("good morning, mera sawal hai ki 15 ka 20 percent "
     "kitna hota hai", "3"),
    ("pehle ye batao 12 ka 50 percent kitna hai aur phir "
     "percentage samjhao", "6"),
    ("ye wala sawal kal ke test me aayega, 25 ka square "
     "kya hota hai", "625"),
    ("Aryabhata ke sawal: 12 + 8 kitna hota hai", "20"),
    ("Ram ne 15 + 27 kiya to jawab kya aaya", "42"),
    ("5 guna 6 kitna hota hai", "30"),
])
def test_battery_solves(question, answer):
    r = fallback_answer(question)
    assert str(r.get("answer")) == answer, question


def test_battery_table_with_greeting():
    r = fallback_answer(
        "dhanyavaad, ab ye batao 7 ka table sunao")
    assert str(r.get("answer")).startswith("7, 14")


# ---------------------------------------------------------------------------
# 4. AI-eligible: the chain is consulted and serves
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    # GK with no curated entry
    "sabse bada mathematician kaun tha",
    "calculator kisne banaya",
    "kisne banaya calculator",
    "abacus kya hota hai",
    "abacus ka avishkar kahan hua tha",
    "number system kisne banaya",
    "sabse purana ganit ka granth konsa hai",
    "vedic maths kya hota hai",
    # Concept asks the topics library does not own
    "क्षेत्रफल कैसे निकालते हैं",
    "ghaat kya hoti hai maths me",
    "bhinn kya hota hai batao",
    "5 ke pahade sunao",
    "aadha matlab kitna hota hai",
    "log ka matlab kya hota hai",
    "differentiation kya hota hai",
    "2 ke baad konsi sankhya aati hai",
    # The manufactured-echo trap: NOT a deep "0 = 0".
    "1 me kitne zero hote hai",
    # Spoken word problems the native solver misses —
    # the AI chain is their correct home today.
    "suno ek sawal hai, ek aadmi ke paas 240 rupees hai "
    "usne 35% kharch kar diye kitne bache",
    "meri copy me 48 pages the 12 use ho gaye fraction "
    "me batao kitne bache",
    "mummy ne 500 rupaye diye 175 kharch ho gaye kitne "
    "bache",
    "ek class me 40 bache hai unme se 15 ladkiyan hai "
    "ladko ka percentage batao",
    "ram ke paas 3 dozen kele hai usne 9 kha liye kitne "
    "bache",
    "kal maine 250 me se 80 rupaye ki copy kharidi bache "
    "kitne",
    # Follow-up fragments (context lives in the chat)
    "aur iska ulta kya hoga",
    "ye wala phir se samjhao",
    "iska answer step me chahiye",
    "usi ka ulta batao",
    "iska example do",
    "aur detail me samjhao isko",
    "iska answer batao aur step bhi dikhao",
])
def test_battery_ai_eligible(monkeypatch, question):
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert calls, f"AI chain never consulted: {question}"
    assert r.get("answer") == "AI sentinel", question
    assert r.get("fallback_kind") != "not_found", question


# ---------------------------------------------------------------------------
# 5. The two wrong native serves, pinned at their seams
# ---------------------------------------------------------------------------

def test_percent_spent_is_not_a_bare_subtraction():
    # The money-left core: a percent changes the shape.
    assert _core_money_left(
        "ram has 240 rupees, he spent 35% of it, how "
        "much is left") is None
    # ...while the plain money shape keeps its core.
    assert _core_money_left(
        "ram has 240 rupees, he spent 35 rupees, how "
        "much is left") == "240 - 35"
    q = ("suno ek sawal hai, ek aadmi ke paas 240 rupees "
         "hai usne 35% kharch kar diye kitne bache")
    assert deep_solve(q) is None
    r = fallback_answer(q)
    assert r.get("fallback_kind") != "deep_solve"
    assert str(r.get("answer")) != "205"


def test_labelled_speed_distance_not_speed():
    # The router rewrite: labelled speed + time + a
    # distance ask is a DISTANCE question...
    r = solve_question(
        "ek train 60 km ki speed se 2 ghante chalti hai "
        "kitni door gayi")
    assert r.get("op") == "distance"
    assert str(r.get("answer")) == "120"
    # ...and the true speed shape is untouched.
    r = solve_question(
        "ek train 60 km door 2 ghante me gayi speed kya "
        "hai")
    assert r.get("op") == "speed"
    assert str(r.get("answer")) == "30 km/h"


def test_deep_bare_echo_veto():
    echo = {"op": "evaluate", "expression": "0",
            "answer": "0", "numeric": 0.0,
            "steps": ["Evaluate: 0 = 0"]}
    # Manufactured from the WORD zero: vetoed.
    assert _w185_veto("1 me kitne zero hote hai", echo) \
        is True
    # A number the question actually wrote: not this
    # veto's business (Wave 177's covers its own shape).
    assert _w185_veto("0 evaluate karo", echo) is False
    # A real computation's result: never a bare echo of
    # an unwritten number in this sense.
    real = {"op": "evaluate", "expression": "205",
            "answer": "205", "numeric": 205.0}
    assert _w185_veto("240 - 35 kitna hota hai", real) \
        is False
    # A spelled-out computation's answer is a NEW number
    # the question never states — never vetoed (the
    # Wave 134 rescue battery owns this case end-to-end).
    spelled = {"op": "evaluate", "expression": "90",
               "answer": "90", "numeric": 90.0}
    assert _w185_veto("What is fifteen multiplied by "
                      "six?", spelled) is False


# ---------------------------------------------------------------------------
# 6. Classification pins: intent is never "gibberish"
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "aryabhat ne kya kia tha",
    "jero kisne banaya",
    "brahmgupt kaun tha",
    "sifr kisne banaya",
    "ramanuja kaun tha",
    "Bhaskara ne kya khoja tha",
    "geometry ki shuruaat kahan se hui",
    "abacus ka avishkar kahan hua tha",
    "iska example do",
])
def test_battery_intent_is_not_gibberish(question):
    assert _is_gibberish(question) is False, question


def test_followup_net():
    assert is_followup_shaped("iska example do") is True
    assert is_followup_shaped("aur detail me samjhao "
                              "isko") is True
    assert is_followup_shaped("asdf qwer zxcv") is False
    # A real problem is never a fragment.
    assert is_followup_shaped(
        "ek train 60 km ki speed se 2 ghante chalti hai "
        "kitni door gayi, example do") is False


# ---------------------------------------------------------------------------
# 7. Advice: yields to a content ask, serves otherwise
# ---------------------------------------------------------------------------

def test_advice_yields_to_embedded_content_ask():
    assert meta_result(
        "exam me pucha gaya tha ki pi ka maan kitna "
        "hota hai") is None


@pytest.mark.parametrize("question", [
    "exam me bahut darr lagta hai",
    "maths ke exam me time manage kaise karu",
])
def test_advice_still_serves_genuine_advice(question):
    m = meta_result(question)
    assert m is not None
    assert m["op"] == "advice_exam_solve"


# ---------------------------------------------------------------------------
# 8. Controls: guards do not move
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "asdf qwer zxcv",
    "zxcv ne kya kiya tha qwer",
    "Shakespeare ne kya kiya tha",
])
def test_controls_gibberish_never_reach_ai(monkeypatch,
                                           question):
    assert _is_gibberish(question) is True
    assert not (is_meta_shaped(question)
                or is_knowledge_shaped(question)
                or is_followup_shaped(question))
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert not calls, "AI chain must not see this"
    assert r.get("fallback_kind") == "not_found"


@pytest.mark.parametrize("question", [
    "cricket ka score kya hai",
    "What is the capital of France?",
])
def test_controls_nonmaths(monkeypatch, question):
    calls = _patch_ai(monkeypatch, dict(_SENTINEL))
    r = fallback_answer(question)
    assert not calls
    assert r.get("fallback_kind") == "nonmaths"


def test_controls_anti_hijack():
    # A name inside a problem is not knowledge (Wave 183
    # pins, re-asserted because the markers moved).
    assert meta_result(
        "Aryabhata school me 40 bache hai, 5 group "
        "banao") is None
    # "me kya kiya jata hai" is a concept ask, not a
    # contribution ask — the "ne" frame is absent.
    assert meta_result(
        "trigonometry me kya kiya jata hai") is None
    r = fallback_answer("trigonometry me kya kiya jata "
                        "hai")
    assert r.get("fallback_kind") == "concept"


# ---------------------------------------------------------------------------
# 9. AI-chain depth (stubbed legs)
# ---------------------------------------------------------------------------

def test_ai_chain_all_legs_silent_knowledge_stays_knowledge(
        monkeypatch):
    # (b) Every leg silent: the serve collapses locally,
    # but the CLASSIFICATION — what fallback.py consults
    # before the chain — must mark the question a genuine
    # knowledge ask, never gibberish (classification pin
    # only, per the wave brief; the with-calls routing
    # evidence for knowledge misses lives in Wave 183's
    # suite and in section 4 above). Hilbert has no
    # curated entry, so this is a pure routing pin.
    q = "Hilbert ne kya kiya tha"
    _patch_ai(monkeypatch, None)
    fallback_answer(q)
    assert _is_gibberish(q) is False
    assert is_knowledge_shaped(q) is True


def test_ai_chain_prose_first_leg_served_unverified(
        monkeypatch):
    """(a) THE WAVE 185 FINDING, pinned as the machinery
    behaves today (parent decision item — see the module
    docstring): for a PROSE knowledge question the chain
    serves leg 1's sane answer immediately; legs 2 and
    3 are never consulted, so a WRONG GK answer from
    leg 1 is served even when leg 2 holds the right
    one. Wave 133's consensus machinery cannot engage:
    a prose answer carries no value claim to compare.
    If this test starts failing because the chain grew
    a prose cross-check, update the pin deliberately —
    that is the fix landing."""
    wrong = {
        "type": "AI", "op": "gemini",
        "answer": "Euler ne telephone ka avishkar kiya "
                  "tha",
        "steps": ["Euler ek aavishkarak the jinhone "
                  "telephone banaya."],
        "fallback": True, "fallback_kind": "gemini",
    }
    right = {
        "type": "AI", "op": "groq",
        "answer": "Euler ne graph theory ki shuruaat "
                  "ki thi",
        "steps": ["Euler ne Königsberg pul samasya se "
                  "graph theory ki neev rakhi."],
        "fallback": True, "fallback_kind": "groq",
    }
    groq_calls = []
    monkeypatch.setattr(
        fallback, "_gemini_answer",
        lambda *a, **k: dict(wrong))
    monkeypatch.setattr(
        fallback, "_groq_answer",
        lambda *a, **k: (groq_calls.append(1),
                         dict(right))[1])
    monkeypatch.setattr(
        fallback, "_openrouter_answer",
        lambda *a, **k: None)
    r = fallback_answer("Euler ne kya kiya tha")
    assert r.get("answer") == wrong["answer"]
    assert not groq_calls, "leg 2 was consulted — the " \
        "prose cross-check fix has landed; update this pin"
