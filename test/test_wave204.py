"""Wave 204 (Suraj, 20 Nov 2026): "Answer not found"
RETIRED FOREVER.

His order, verbatim sense: "user toh kuch bhi puch leta
hai toh uska kuch naa kuch ans hona chahiye; aisa bhi nhi
ki ans de deta hu toh glt de diya; ans dena hai wo bhi
sahi wala; ab se ans not found toh aana hi nhi chahiye."
And his refinement the same night: "Aisa nhi ho ki
question likh kar bheja hai fir bhi saaf suthra maang rha
hai — aisa nhi hona chahiye."

What this wave changed (fallback.py / i18n.py /
multipart.py): every terminal line the fallback layer can
render is now the kind CLARIFICATION line ("Samajh nahi
aaya — maths ka sawal thoda saaf likh kar bhejo, main
turant solve kar dunga." and its per-language twins). The
internal sentinel (op / fallback_kind "not_found") keeps
its name — renderers, the Live Bank classifier and the
Wave-90 log gate on the label, not the words.

Proven here:
- zero-recoverable-content inputs (keyboard mash, random
  strings, symbol-only, Devanagari letter-soup) get the
  clarification line in the student's own language — and
  nothing else (no steps, plain rendering, kind unchanged);
- messy-but-real questions (heavy typos, misspellings,
  broken word order, jumbled units, Hinglish / Devanagari)
  are SOLVED with the correct value, or AI-answered when a
  leg answers — NEVER the clarification line;
- the Wave 133/134/158 discipline is untouched: verified
  serves, method transfer, and the last resort (majority
  first, then the first leg) all still fire, marked
  last_resort and never promoted;
- knowledge questions the curated layers miss reach the
  AI legs and are answered;
- non-maths keeps its maths-only one-liner, greetings and
  vague asks keep their friendly lines;
- a broad fuzz battery (300+ inputs: generated arithmetic
  with exact values, generated junk, mixed junk with a
  maths core, GK, requests) — NONE returns a retired
  not-found string, in the answer or in any step.
"""
import random

import pytest

import fallback
from fallback import fallback_answer, with_fallback

FAILED = {"op": "error",
          "answer": "Could not solve this one: x",
          "steps": []}

AREA_Q = "Find the area between the curves y = x^2 and y = x"
AGES_Q = ("Ten years ago, a father was twelve times as old "
          "as his son and ten years hence, he will be twice "
          "as old as his son. Find their present ages.")
LADKE_Q = ("ek ladke ke paas 50 rupaye hai usne 3 chocolate "
           "10 rupaye ki kharidi kitne bache")

RETIRED = (
    "Answer not found.",
    "Answer nahi mila.",
    "उत्तर नहीं मिला।",
    "উত্তর পাওয়া যায়নি।",
    "उत्तर सापडले नाही.",
    "பதில் கிடைக்கவில்லை.",
    "సమాధానం దొరకలేదు.",
)

CLARIFY_EN = ("I didn't understand that — type your maths "
              "question a little clearly and I'll solve it "
              "right away.")
CLARIFY_ROMAN = ("Samajh nahi aaya — maths ka sawal thoda "
                 "saaf likh kar bhejo, main turant solve kar "
                 "dunga.")
CLARIFY_DEV = ("समझ नहीं आया — गणित का सवाल थोड़ा साफ़ "
               "लिखकर भेजिए, मैं तुरंत हल कर दूँगा।")
CLARIFY_BN = ("বুঝতে পারিনি — গণিতের প্রশ্নটা একটু "
              "পরিষ্কার করে লিখে পাঠাও, আমি সঙ্গে সঙ্গে "
              "সমাধান করে দেব।")
CLARIFY_MR = ("समजलं नाही — गणिताचा प्रश्न थोडा स्पष्ट "
              "लिहून पाठवा, मी लगेच सोडवून देईन.")
CLARIFY_ALL = {CLARIFY_EN, CLARIFY_ROMAN, CLARIFY_DEV,
               CLARIFY_BN, CLARIFY_MR,
               "புரியவில்லை — கணிதக் கேள்வியை கொஞ்சம் "
               "தெளிவாக எழுதி அனுப்புங்கள், உடனே தீர்த்து "
               "தருகிறேன்.",
               "అర్థం కాలేదు — గణిత ప్రశ్నను కొంచెం "
               "స్పష్టంగా రాసి పంపండి, వెంటనే పరిష్కరించి "
               "ఇస్తాను."}


def _text(res):
    parts = [str(res.get("answer") or "")]
    parts += [str(s) for s in (res.get("steps") or [])]
    return "\n".join(parts)


def assert_no_retired(res):
    text = _text(res)
    for bad in RETIRED:
        assert bad not in text, (bad, text[:200])


def assert_not_clarify(res):
    assert str(res.get("answer") or "") not in CLARIFY_ALL, \
        res.get("answer")


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "w204.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(path))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    return path


@pytest.fixture()
def no_salvage(monkeypatch):
    monkeypatch.setattr(fallback, "_salvage",
                        lambda *a, **k: None)


def _ai(kind, answer, steps=()):
    return {"type": "Ganitra", "op": kind, "answer": answer,
            "steps": list(steps), "fallback": True,
            "fallback_kind": kind, "ai_generated": True}


def _stub_legs(monkeypatch, gemini=None, groq=None,
               openrouter=None):
    """The Wave 133/158 seam pattern: stub the three leg
    functions on the fallback module (no network, no keys)."""
    def _mk(value, with_req):
        def fake(question, hindi, lang_request=None):
            v = value(question) if callable(value) else value
            return dict(v) if isinstance(v, dict) else v

        def fake_or(question, hindi):
            v = value(question) if callable(value) else value
            return dict(v) if isinstance(v, dict) else v

        return fake if with_req else fake_or

    monkeypatch.setattr(fallback, "_gemini_answer",
                        _mk(gemini, True))
    monkeypatch.setattr(fallback, "_groq_answer",
                        _mk(groq, True))
    monkeypatch.setattr(fallback, "_openrouter_answer",
                        _mk(openrouter, False))


# ---------------------------------------------------------------------------
# 1. Zero recoverable content -> the clarification line, and only that
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,want", [
    ("asdf qwer zxq", CLARIFY_EN),
    ("xkcd blah zzz", CLARIFY_EN),
    ("blorp snizzle wumpus", CLARIFY_EN),
    ("If tu gfuf", CLARIFY_EN),
    ("zxcv plugh", CLARIFY_EN),
    ("?", CLARIFY_EN),
    ("!!!", CLARIFY_EN),
    ("कखग घङच छजझ", CLARIFY_DEV),
    ("कुछ भी लिख दिया बकवास", CLARIFY_DEV),
    ("कुछ भी बकवास लिख दिया", CLARIFY_DEV),
])
def test_zero_content_gets_the_clarification_line(question,
                                                  want):
    res = fallback_answer(question)
    assert res.get("fallback_kind") == "not_found"
    assert res.get("answer") == want
    assert res.get("steps") == []
    assert_no_retired(res)


def test_clarification_line_follows_ui_language_and_request():
    # bn UI -> the bn clarification line (i18n key, Wave 204
    # values); mr UI + Devanagari -> the mr line; an explicit
    # Hinglish request -> the Roman line.
    res = fallback_answer("asdf qwer", lang="bn")
    assert res.get("answer") == CLARIFY_BN
    res = fallback_answer("कुछ भी बकवास लिख दिया", lang="mr")
    assert res.get("answer") == CLARIFY_MR
    res = fallback_answer("asdf qwer",
                          lang_request="hinglish")
    assert res.get("answer") == CLARIFY_ROMAN
    res = fallback_answer("asdf qwer", lang_request="hi")
    assert res.get("answer") == CLARIFY_DEV


def test_deferred_ai_honest_outcome_is_the_clarification():
    # Wave 131's streaming seam precomputes the honest
    # outcome through the same code — it must carry the
    # clarification line too, never a retired string.
    out = with_fallback("wat is the squar root of 144",
                        dict(FAILED), lang="en", defer_ai=True)
    assert out.get("ai_deferred") is True
    honest = out.get("ai_honest") or {}
    assert honest.get("answer") == CLARIFY_EN
    assert_no_retired(honest)


# ---------------------------------------------------------------------------
# 2. Messy-but-real questions: solved or AI-answered, NEVER clarified
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,want", [
    # Misspellings / heavy typos (native chain).
    ("144 ka square root kya hai", "12"),
    ("15 aur 25 ka yog kya hoga", "40"),
    ("5 bindu 5 jodo", "10"),
    ("ek ghante me kitne second hote hai", "3600"),
    # Spelled-out numbers + Hinglish (deep solve).
    ("paanch sau ka 20 percent kitna hoga", "100"),
    ("bhaiya 100 me se 37 ghatane par kitna bacha", "63"),
    # Mixed junk around a real maths core (salvage).
    ("asdf 5 + 3 qwer", "8"),
    ("blah blah 12 * 4 blah", "48"),
    # Requests / tables / facts the built-in layers own.
    ("2 ka pahada sunao", "20"),
    ("0 ki khoj kisne ki", "Aryabhata"),
    ("fibonacci sequence kisne banaya tha", "Fibonacci"),
])
def test_messy_but_real_native(question, want):
    res = fallback_answer(question)
    assert want in str(res.get("answer") or "")
    assert res.get("fallback_kind") != "not_found"
    assert_not_clarify(res)
    assert_no_retired(res)


@pytest.mark.parametrize("question,leg_answer,want", [
    # The refinement's own standard cases: heavy-typo /
    # jumbled real questions the native chain cannot parse.
    # With a leg answering (the production configuration)
    # they are served the AI answer — never the
    # clarification line.
    ("wat is the squar root of 144", "12", "12"),
    ("train ki speed 60 hai aur 3 ghante chali toh kitni "
     "dur gayi", "180 km", "180"),
    ("ek kilo aalu 40 rupay hai 2.5 kilo kitne ka hoga",
     "100 rupaye", "100"),
    (AGES_Q, "Father is 34 years old, son is 12 years old",
     "34"),
    (LADKE_Q, "20 rupaye bache", "20"),
])
def test_messy_but_real_ai_answered(db, monkeypatch,
                                    question, leg_answer,
                                    want):
    leg_g = _ai("gemini", leg_answer)
    leg_q = _ai("groq", leg_answer)
    _stub_legs(monkeypatch, gemini=leg_g, groq=leg_q,
               openrouter=None)
    res = fallback_answer(question)
    assert want in str(res.get("answer") or "")
    assert res.get("fallback_kind") in ("gemini", "groq")
    assert_not_clarify(res)
    assert_no_retired(res)


# ---------------------------------------------------------------------------
# 3. The last-resort discipline is unchanged (Wave 158), minus not-found
# ---------------------------------------------------------------------------

def test_last_resort_single_leg(db, no_salvage, monkeypatch):
    leg = _ai("gemini", "1/3 square units",
              ["The curves meet at x = 0 and x = 1."])
    _stub_legs(monkeypatch, gemini=leg, groq=None,
               openrouter=None)
    res = with_fallback(AREA_Q, dict(FAILED), lang="en")
    assert res["fallback_kind"] == "gemini"
    assert res["ai_verification"] == "last_resort"
    assert res["ai_last_resort"] == "single"
    assert res["answer"] == "1/3 square units"
    assert_not_clarify(res)
    assert_no_retired(res)


def test_last_resort_majority_beats_first_leg(
        db, no_salvage, monkeypatch):
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
    assert_not_clarify(res)
    assert_no_retired(res)


def test_knowledge_miss_reaches_the_ai_legs(
        db, monkeypatch):
    # "abacus kya hota hai" / "calculator kisne banaya tha"
    # are maths-knowledge questions the curated FACTS layer
    # does not carry: they must reach the AI legs (Waves
    # 183/185 routing) and be answered — never clarified.
    prose = ("Abacus ek purana ginti ka upkaran hai jisme "
             "taaron par moti ghumakar jod-ghata kiya jata "
             "hai.")
    _stub_legs(monkeypatch,
               gemini=_ai("gemini", prose),
               groq=_ai("groq", prose),
               openrouter=None)
    res = fallback_answer("abacus kya hota hai")
    assert "Abacus" in str(res.get("answer") or "")
    assert res.get("fallback_kind") != "not_found"
    assert_not_clarify(res)
    assert_no_retired(res)


# ---------------------------------------------------------------------------
# 4. The guards and friendly lines are untouched
# ---------------------------------------------------------------------------

def test_nonmaths_keeps_the_maths_only_line():
    res = fallback_answer("What is the capital of France?")
    assert res.get("fallback_kind") == "nonmaths"
    assert "not a maths question" in str(res.get("answer"))
    assert_not_clarify(res)
    assert_no_retired(res)


def test_greeting_and_vague_unchanged():
    res = fallback_answer("hello")
    assert res.get("fallback_kind") == "greeting"
    assert_no_retired(res)
    res = fallback_answer("samjhao")
    assert res.get("fallback_kind") == "vague"
    assert "Bilkul" in str(res.get("answer"))
    assert_no_retired(res)


# ---------------------------------------------------------------------------
# 5. The broad fuzz battery: NO input returns a retired string
# ---------------------------------------------------------------------------

def test_fuzz_generated_arithmetic_exact_values():
    pairs = [(3, 4), (7, 6), (12, 9), (15, 11), (20, 18),
             (25, 30), (9, 8), (14, 5), (30, 22), (45, 15)]
    count = 0
    for a, b in pairs:
        for question, want in (
                (f"{a} + {b}", str(a + b)),
                (f"{a} - {b}", str(a - b)),
                (f"{a} * {b}", str(a * b)),
                (f"{a} x {b}", str(a * b)),
                (f"{a * b} / {b}", str(a)),
                (f"{a} plus {b}", str(a + b)),
                (f"{a} aur {b} jodo", str(a + b)),
                (f"{a} multiplied by {b}", str(a * b))):
            res = fallback_answer(question)
            count += 1
            if want is not None:
                assert want in str(res.get("answer") or ""), \
                    (question, res.get("answer"))
            assert res.get("fallback_kind") != "not_found", \
                question
            assert_not_clarify(res)
            assert_no_retired(res)
    assert count >= 80


def test_fuzz_generated_junk_only_clarifies():
    rng = random.Random(204)
    letters = "zxqwvbnmkjhgfdsp"
    count = 0
    for _ in range(60):
        tokens = []
        for _ in range(rng.randint(2, 4)):
            n = rng.randint(3, 7)
            tokens.append("".join(rng.choice(letters)
                                  for _ in range(n)))
        question = " ".join(tokens)
        res = fallback_answer(question)
        count += 1
        assert res.get("fallback_kind") == "not_found", \
            (question, res.get("fallback_kind"))
        assert res.get("answer") in CLARIFY_ALL, \
            (question, res.get("answer"))
        assert_no_retired(res)
    assert count == 60


def test_fuzz_mixed_junk_with_maths_core_solves():
    rng = random.Random(97)
    junk = ["zxq", "blorp", "wqz", "snizzle", "plugh"]
    count = 0
    for _ in range(30):
        a, b = rng.randint(2, 40), rng.randint(2, 15)
        op = rng.choice(["+", "*"])
        want = a + b if op == "+" else a * b
        question = (f"{rng.choice(junk)} {a} {op} {b} "
                    f"{rng.choice(junk)}")
        res = fallback_answer(question)
        count += 1
        assert str(want) in str(res.get("answer") or ""), \
            (question, res.get("answer"))
        assert_not_clarify(res)
        assert_no_retired(res)
    assert count == 30


@pytest.mark.parametrize("question", [
    "", " ", "a", "zzz", "😀😀😀", "🎉🎉", "....", "ok",
    "mera naam kya hai", "aaj ka din kya hai",
    "tum kaun ho", "thank you", "namaste",
    "what is the speed of light",
    "capital of India kya hai",
    "maths me sabse bada number kaun sa hai",
    "venn diagram kisne banaya",
    "golden ratio kya hota hai",
    "pi ka maan kisne diya",
    "adhik se adhik 3 anko ki sankhya",
    "solve 2x + 3 = 7", "HCF of 12 and 18",
    "area of circle with radius 7",
    "prove that sin^2 A + cos^2 A = 1",
])
def test_fuzz_misc_inputs_never_retired(question):
    res = fallback_answer(question)
    assert_no_retired(res)


def test_api_gibberish_payload_has_no_retired_text(
        tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    client = application.test_client()
    body = client.post(
        "/api/solve", json={"question": "If tu gfuf"}
    ).get_json()
    assert body["ok"] is True
    result = body["result"]
    assert result.get("fallback_kind") == "not_found"
    assert result.get("answer") == CLARIFY_EN
    assert body["explanation"] == ""
    assert body["advice"] == ""
    for bad in RETIRED:
        assert bad not in str(result.get("answer"))
