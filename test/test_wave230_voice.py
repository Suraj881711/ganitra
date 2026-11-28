"""Wave 230 — VOICE CALL (personal chat first).

Suraj's spec (23 Nov 2026): the student talks to Ganitra
the way he talks to Muse — speaks the question, Ganitra
answers BY VOICE in its soft voice, and the mascot moves
while it speaks. Free Web Speech API only
(SpeechRecognition + speechSynthesis); no service, no key,
no cloning. Group voice call is a later wave — not here.

What already existed and is NOT touched: the Wave-84
one-shot mic (dictate → box → check → send, interimResults
off) and the Listen buttons' full teacher narration
(narrateSolution + speakable + tuneUtterance at rate 0.95 /
pitch 1.0). Wave 230 adds, in templates/index.html only:

1. A phone button in the composer + a call status bar:
   the hands-free loop. The call recogniser shows the LIVE
   interim transcript in the box and submits the final one
   through the composer's own submit path (form.requestSubmit
   → the same handler a typed send uses → the same
   /api/solve flow, same chat_id). handleSolveData hands
   every finished turn to voiceCallAfterTurn.
2. The SHORT spoken form: buildCallSpeech speaks at most a
   one-line summary + the final answer in the teacher's
   closing line — never the whole step list. Its text is
   built by speakClean (the ear-cleaner: LaTeX, markdown,
   fractions as "3 by 4", ₹/%/° verbalised, "Answer:"
   prefixes, ticks and emoji stripped) on top of the house
   speakable().
3. Mascot states: body.voice-speaking (a gentle talking
   bob — the portraits are stills, no mouth layer) and
   body.voice-listening (a soft ring), in style.css with
   reduced-motion rest. Stylesheet bumped v='65' → v='66',
   service-worker cache v41 → v42 (the standing rule).

Browser speech APIs cannot run in this harness, so the
cleaner is exercised under node (the repo's established
pattern: extract the marked JS, run the real functions),
the wiring is pinned on the template/CSS/i18n text, and
the typed flow is proven unchanged against the test
client. The full call can only be judged on a real phone.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
API = (ROOT / "api.py").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _signup(client):
    r = client.post("/signup", data={
        "name": "W230 Voice Tester", "class": "10",
        "board": "CBSE", "goal": "Doctor", "hobby": "Cricket",
        "favourite": "Pizza", "password": "w230-voice-pass"})
    assert r.status_code in (200, 302)


# ---------------------------------------------------------------------------
# The node harness: extract the REAL cleaner functions from
# the template (WORDS + speakable, TEACHER + pickLine, and
# the marked Wave-230 block) and run the cases through them.
# ---------------------------------------------------------------------------

def _extract_js():
    words = INDEX[INDEX.index("var WORDS = {"):
                  INDEX.index("/* ---------- Teacher voice")]
    teacher = INDEX[INDEX.index("var TEACHER = {"):
                    INDEX.index("/* ---------- Wave 230")]
    b = INDEX.index("WAVE230-SPEECH-CLEAN-BEGIN")
    b = INDEX.index("*/", b) + 2
    block = INDEX[b:INDEX.index("WAVE230-SPEECH-CLEAN-END")]
    block = block[:block.rindex("/*")]
    return words, teacher, block


_CLEAN_CASES = [
    # (text, code, exact-or-None, must-contain, must-not-contain)
    ("x² + 3x = 0", "en", "x squared plus 3x equals 0", (), ()),
    (r"\frac{3}{4}", "en", "3 by 4", (), ()),
    ("3/4 of 100", "en", "3 by 4 of 100", (), ()),
    ("√144 = 12", "en", "square root of 144 equals 12", (), ()),
    ("Speed = distance ÷ time", "en",
     "Speed equals distance divided by time", (), ()),
    ("Area = π × r²", "en",
     "Area equals pi multiplied by r squared", (), ()),
    ("50% of ₹500", "en", "50 percent of 500 rupees", (), ()),
    ("sin 30° = 1/2", "en", "sin 30 degrees equals 1 by 2", (), ()),
    (r"**Answer:** $x = \frac{1}{2}$ ✓", "en",
     "x equals 1 by 2", (), ()),
    ("a ≤ b and c ≥ d", "en",
     "a less than or equal to b and c greater than or equal to d",
     (), ()),
    ("Answer is 5 🎉😊", "en", None, ("5",), ("🎉", "😊")),
    ("x^2 - 5x + 6 = 0", "en", None,
     ("x squared", "minus", "plus", "equals"), ("^",)),
    ("## Solution\n- Step one: 2 × 3 = 6", "en", None,
     ("2 multiplied by 3 equals 6",), ("#", "×")),
    ("उत्तर: x² = 4", "hi", "x का वर्ग बराबर 4", (), ()),
    ("3/4 भाग", "hi", "3 बटा 4 भाग", (), ()),
    ("Answer: 50% छूट", "hi", "50 प्रतिशत छूट", (), ()),
    ("x² ka value 9 hai", "hi", None, ("का वर्ग",), ()),
]

_BUILD_CASES = [
    # (payload, code, speech_lang)
    ({"ok": True,
      "result": {"steps": ["Subtract 3 from both sides: 2x = 8",
                           "Divide both sides by 2: x = 4"],
                 "answer": "x = 4"}}, "en", "en-IN"),
    ({"ok": True,
      "result": {"plain_reply": True,
                 "answer": "That's not a maths question — "
                           "Ganitra only solves Maths.",
                 "steps": []}}, "en", "en-IN"),
    ({"ok": False}, "en", "en-IN"),
    ({"ok": True,
      "result": {"steps": [],
                 "answer": "x = 4"}}, "hi", "hi-IN"),
    ({"ok": True,
      "intro": "A train travels 120 km in 2 hours.",
      "result": {"steps": ["Speed = 120 ÷ 2 = 60"],
                 "answer": "60"}}, "en", "en-IN"),
]

_DRIVER = """
"use strict";
var UI_CODE = "en";
var SPEECH_LANG = "en-IN";
__WORDS__
__TEACHER__
__BLOCK__
var cases = JSON.parse(require("fs").readFileSync(
  process.argv[2], "utf8"));
var out = { clean: [], build: [] };
cases.clean.forEach(function (c) {
  UI_CODE = c.code;
  out.clean.push(speakClean(c.text, c.code));
});
cases.build.forEach(function (c) {
  UI_CODE = c.code;
  SPEECH_LANG = c.lang;
  out.build.push(buildCallSpeech(c.data));
});
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def spoken():
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    words, teacher, block = _extract_js()
    driver = (_DRIVER.replace("__WORDS__", words)
              .replace("__TEACHER__", teacher)
              .replace("__BLOCK__", block))
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "driver.js").write_text(driver, encoding="utf-8")
        cases = {
            "clean": [{"text": t, "code": c}
                      for (t, c, _e, _has, _not) in _CLEAN_CASES],
            "build": [{"data": data, "code": code, "lang": lang}
                      for (data, code, lang) in _BUILD_CASES],
        }
        (d / "cases.json").write_text(
            json.dumps(cases), encoding="utf-8")
        p = subprocess.run(
            [node, str(d / "driver.js"), str(d / "cases.json")],
            capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout.strip().splitlines()[-1])


# ---------------------------------------------------------------------------
# 1. speakClean — the ear-cleaner (parametrised, en + hi)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "idx", range(len(_CLEAN_CASES)),
    ids=[f"clean{i}" for i in range(len(_CLEAN_CASES))])
def test_speak_clean(spoken, idx):
    text, code, exact, must, must_not = _CLEAN_CASES[idx]
    got = spoken["clean"][idx]
    if exact is not None:
        assert got == exact, (text, got)
    for frag in must:
        assert frag in got, (text, got, frag)
    for frag in must_not:
        assert frag not in got, (text, got, frag)
    # Nothing raw ever reaches the ear.
    for raw in ("=", "²", "³", "√", "π", "≤", "≥", "%", "₹", "°",
                "\\frac", "**", "`"):
        assert raw not in got, (text, got, raw)


# ---------------------------------------------------------------------------
# 2. buildCallSpeech — the SHORT spoken form
# ---------------------------------------------------------------------------

def test_build_solved_speaks_summary_then_answer(spoken):
    parts = spoken["build"][0]
    assert len(parts) == 2
    # The summary is the first step, cleaned, spoken as the
    # board language (the house rule for step bodies).
    assert parts[0]["lang"] == "en-IN"
    assert "2x equals 8" in parts[0]["text"]
    # The close carries the final answer, cleaned.
    assert parts[1]["lang"] == "en-IN"
    assert "x equals 4" in parts[1]["text"]
    for p in parts:
        assert "=" not in p["text"] and "²" not in p["text"]


def test_build_plain_reply_speaks_its_one_line(spoken):
    parts = spoken["build"][1]
    assert len(parts) == 1
    assert parts[0]["text"] == (
        "That's not a maths question — Ganitra only solves Maths.")


def test_build_failed_turn_speaks_nothing(spoken):
    assert spoken["build"][2] == []


def test_build_hindi_close_and_no_summary_without_steps(spoken):
    parts = spoken["build"][3]
    assert len(parts) == 1
    assert parts[0]["lang"] == "hi-IN"
    assert "x बराबर 4" in parts[0]["text"]


def test_build_intro_is_the_summary(spoken):
    parts = spoken["build"][4]
    assert len(parts) == 2
    assert parts[0]["text"] == "A train travels 120 km in 2 hours."
    assert "60" in parts[1]["text"]


def test_build_never_dumps_the_step_list(spoken):
    """Even a long solve speaks at most two short parts."""
    for parts in spoken["build"]:
        assert len(parts) <= 2
        for p in parts:
            assert len(p["text"]) <= 320


# ---------------------------------------------------------------------------
# 3. Template wiring — controls, guards, hooks
# ---------------------------------------------------------------------------

def test_call_controls_present():
    assert 'id="call-btn"' in INDEX
    assert 'id="voice-call-bar"' in INDEX
    assert 'id="voice-call-status"' in INDEX
    assert 'id="voice-call-end"' in INDEX
    assert "{{ t.voice_call_btn }}" in INDEX
    assert "{{ t.voice_call_end }}" in INDEX
    # The phone sits inside the composer tools, next to the
    # mic and the camera — the composer's own furniture.
    bar = INDEX[INDEX.index('class="chat-bar-tools"'):
                INDEX.index('id="attach-menu"')]
    assert bar.index('id="mic-btn"') < bar.index('id="call-btn"') \
        < bar.index('id="attach-btn"')


def test_call_functions_and_bridge_present():
    for needle in ("function speakClean", "function buildCallSpeech",
                   "WAVE230-SPEECH-CLEAN-BEGIN",
                   "WAVE230-SPEECH-CLEAN-END",
                   "var VoiceCall", "function voiceCallAfterTurn",
                   "function voiceCallSpeakParts",
                   "function endVoiceCall",
                   "function startCallRecognition",
                   "function beginVoiceCall"):
        assert needle in INDEX, needle
    # The bridge registrations the IIFE-level player needs.
    assert "VoiceCall.startListening = function" in INDEX
    assert "VoiceCall.stopListening = function" in INDEX


def test_finished_turns_reach_the_call():
    # handleSolveData (classic + stream), the offline
    # evaluator's answer, and the failed-turn path.
    assert "voiceCallAfterTurn(data);" in INDEX
    assert "voiceCallAfterTurn(odata);" in INDEX
    assert "voiceCallAfterTurn(null);" in INDEX


def test_call_recogniser_uses_the_same_send_path():
    start = INDEX.index("function startCallRecognition")
    block = INDEX[start:INDEX.index("VoiceCall.startListening", start)]
    # Live interim transcript in the box, final submitted via
    # the composer's own submit — no second endpoint anywhere.
    assert "mine.interimResults = true" in block
    assert "form.requestSubmit()" in block
    assert "normalizeSpokenMaths(finalText)" in block
    assert "/api/solve" not in block


def test_call_feature_guards():
    mic_block = INDEX[INDEX.index('var micBtn = document.getElementById("mic-btn")'):]
    # No SpeechRecognition → the phone hides with the mic.
    assert 'if (callBtn) callBtn.style.display = "none";' in mic_block
    # No speechSynthesis → no call (it could not answer).
    assert '!("speechSynthesis" in window) && callBtn' in mic_block
    # Permission denial ends the call with the kind line.
    assert 'ev.error === "not-allowed"' in mic_block
    assert "endVoiceCall();" in mic_block
    assert "say(L.js_voice_denied)" in mic_block
    # A mic tap during a call hangs up, never double-listens.
    assert "if (VoiceCall.active) { endVoiceCall(); return; }" \
        in mic_block


def test_one_shot_mic_and_listen_untouched():
    # Wave 84 dictate-check-send: interim still OFF there,
    # the transcript still lands in the box first.
    assert "mine.interimResults = false" in INDEX
    assert "WAVE84-SPEECH-NORMALISE-END" in INDEX
    assert INDEX.count("normalizeSpokenMaths(") >= 3
    # Listen's teacher pace is unchanged; the call's softer
    # pitch is set only on the call's own utterances.
    assert "u.rate = 0.95" in INDEX
    assert "u.pitch = 1.0" in INDEX
    assert "u.pitch = 1.05" in INDEX


def test_call_speech_watchdog_and_soft_voice():
    block = INDEX[INDEX.index("function voiceCallSpeakParts"):
                  INDEX.index("function voiceCallAfterTurn")]
    # The queue advances even if an utterance's onend never
    # fires — the call can never stall mid-answer.
    assert "watchdog" in block
    assert "u.onend = u.onerror" in block


# ---------------------------------------------------------------------------
# 4. Mascot states + call bar CSS, version bump
# ---------------------------------------------------------------------------

def test_mascot_voice_states_in_css():
    assert "body.voice-speaking .mascot-buddy img" in CSS
    assert "body.voice-speaking .mascot-pose-wave" in CSS
    assert "body.voice-listening .mascot-buddy" in CSS
    assert "body.voice-listening .mascot-circle" in CSS
    assert "@keyframes voice-talk" in CSS
    assert "@keyframes voice-ring" in CSS
    # Reduced motion rests the voice states too.
    voice_css = CSS[CSS.index("/* Wave 230: the voice-call states"):]
    assert "prefers-reduced-motion" in voice_css


def test_call_bar_and_button_css():
    assert ".voice-call-bar" in CSS
    assert ".voice-call-bar[hidden]" in CSS
    assert ".voice-call-end" in CSS
    assert ".voice-call-dot" in CSS
    assert ".composer-btn.call-live" in CSS


def test_stylesheet_version_bumped():
    assert "v='66'" in BASE
    assert "ganitra-static-v42" in SW
    assert "style.css?v=66" in SW


# ---------------------------------------------------------------------------
# 5. i18n — every language carries the call strings
# ---------------------------------------------------------------------------

def test_i18n_call_strings_all_languages():
    import i18n
    for lang in i18n.SUPPORTED_LANGS:
        s = i18n.get_strings(lang)
        for key in ("voice_call_btn", "voice_call_end",
                    "js_voice_call_listening",
                    "js_voice_call_speaking",
                    "js_voice_call_thinking"):
            assert s.get(key), (lang, key)
        # The js_ strings ride js_t to the page automatically.
        js_t = {k: v for k, v in s.items() if k.startswith("js_")}
        assert js_t["js_voice_call_listening"]
    # A mid-call language switch re-labels the controls:
    # the solve response's ui payload carries the two t-keys.
    assert '"voice_call_btn"' in API and '"voice_call_end"' in API


# ---------------------------------------------------------------------------
# 6. The typed flow is untouched — the page renders with the
#    new furniture and the brain answers as before.
# ---------------------------------------------------------------------------

def test_chat_page_renders_and_typed_solve_unchanged(client):
    _signup(client)
    page = client.get("/").get_data(as_text=True)
    assert 'id="call-btn"' in page
    assert 'id="voice-call-bar"' in page
    assert 'id="mic-btn"' in page
    r = client.post("/api/solve", json={"question": "347 + 258"})
    data = r.get_json()
    assert data["ok"] is True
    assert data["result"]["answer"] == "605"
