"""Wave 160 (Suraj, 18 Nov 2026): the robot mascot with
activity states — the teddy of Wave 155 was rejected and
replaced by Suraj's LOCKED robot character ("Yahi done
karo"), refined by his follow-up orders the same day.

Wave 181 update (Suraj, 19 Nov 2026): the hand-drawn SVG
robot this wave built was itself rejected — "Muse ki
tarah real nhi hai, real feelings nhi hai" — and replaced
by the new RENDERED mascot (glossy 3D robot, four pose
photographs in static/robot-*.webp) sitting in a white
circle at the top of the home, with full-size pop moments
(the kiss on page open, the laugh on a correct chat-test
answer). The SVG-specific pins below were retired with
the artwork; what this file still pins is the BEHAVIOUR
contract that survives the swap:

  * the teddy is still fully gone;
  * the chat-test verdict flag behaviour is unchanged —
    test_verdict "correct" rides ONLY a correct answer,
    and the JS turns it into the mascot's laugh moment;
  * the typing bubble carries NO robot figure (the Wave
    160 duo is gone; the Wave 145 dots are untouched —
    and since Wave 176, merged alongside in Deploy-44,
    the Wave 23 boy no longer rides the bubble either);
  * SCENE_ENABLED stays False; greeting + thought wiring
    is Wave 155's and untouched;
  * pins moved with the CSS: ?v=59 / ganitra-static-v36.
"""
import re
from pathlib import Path

import chat_test

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CHAT_TEST = (ROOT / "chat_test.py").read_text(encoding="utf-8")


# --- The teddy is gone; the SVG robot is gone too -------------

def test_teddy_fully_removed():
    # The teddy's own markup and selectors stay gone (Wave
    # 181's mascot-* classes are a different character).
    assert 'class="mascot"' not in INDEX
    assert "mascot-paw" not in INDEX and "mascot-eyes" not in INDEX
    assert ".mascot {" not in CSS
    assert ".mascot-paw" not in CSS and ".mascot-eyes" not in CSS
    assert "@keyframes mascot-wave" not in CSS


def test_svg_robot_fully_removed():
    # Wave 181: no SVG robot anywhere — not at home, not in
    # the header, not as JS pose strings.
    assert '<svg class="robot"' not in INDEX
    assert '<svg class="robot-buddy-svg"' not in INDEX
    assert "function robotSvg" not in INDEX
    assert 'robotSvg("' not in INDEX
    assert 'class="robot-pose-laugh"' not in INDEX
    assert 'class="robot-pose-think"' not in INDEX
    assert 'class="robot-pose-write"' not in INDEX
    assert ".robot {" not in CSS
    assert "@keyframes robot-" not in CSS


# --- The typing bubble carries no robot -------------------------

def test_typing_bubble_has_no_robot_duo():
    # The Wave 160 think/write duo rode the bubble; Wave 181
    # removes it outright (the bubble stays clean).
    assert "function addTypingRobot" not in INDEX
    assert "addTypingRobot(node)" not in INDEX
    assert "addTypingRobot(fb)" not in INDEX
    assert "robot-duo" not in INDEX
    assert ".robot-duo" not in CSS
    # The typing bubble itself (Wave 145) is untouched.
    assert 'id="typing-template"' in INDEX
    assert "chat_thinking" in INDEX
    # Wave 176 (merged alongside in Deploy-44): the Wave 23
    # boy no longer rides the bubble either — his Teach-
    # board post (showBoyWriter) is untouched, only the
    # typing post is gone, so the bubble is text + dots.
    assert "addTypingBoy" not in INDEX


# --- Laugh on a correct chat-test answer -------------------------

def test_chat_test_verdict_flag_behaviour():
    # user_id=None keeps the state in the session dict (the
    # DB-backed path is for signed-in users).
    session = {}
    started = chat_test.handle_message(session, None, 1, "test do", "en")
    assert started is not None and started["ok"] is True
    assert "test_verdict" not in started["result"]
    state = session[chat_test._session_key(1)]
    item = state["items"][state["index"]]
    payload = chat_test.handle_message(
        session, None, 1, str(item["answer"]), "en")
    assert payload["result"]["test_verdict"] == "correct"
    # A wrong answer carries NO verdict (no laughing mascot).
    session2 = {}
    chat_test.handle_message(session2, None, 1, "test do", "en")
    wrong = chat_test.handle_message(
        session2, None, 1, "zzz-not-the-answer", "en")
    assert "test_verdict" not in wrong["result"]


def test_laugh_mascot_js_hook():
    # Wave 181: the verdict now pops the rendered LAUGH
    # portrait full-size (showMascotPop) and bounces the
    # header buddy — no mini robot inside the bubble.
    assert 'result.test_verdict === "correct"' in INDEX
    assert 'showMascotPop("laugh", 1900)' in INDEX
    assert 'classList.add("mascot-cheer")' in INDEX
    assert "robot-laugh-mini" not in INDEX
    assert ".robot-laugh-mini" not in CSS
    # The server only ever sets the flag from the verdict.
    assert 'verdict="correct" if correct else None' in CHAT_TEST


# --- Reduced motion, pins, parked scene ---------------------------

def test_reduced_motion_stills_mascot():
    blocks = re.findall(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}",
        CSS, re.S)
    w181 = [b for b in blocks if ".mascot-circle" in b]
    assert w181, "the Wave 181 reduced-motion block exists"
    block = w181[0]
    assert "animation: none" in block
    assert ".mascot-pose { opacity: 0; }" in CSS
    assert ".mascot-pose-wave { opacity: 1; }" in CSS


def test_pins_and_scene_flag():
    assert "v='59'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v36"' in SW
    assert '"/static/style.css?v=59"' in SW
    assert "SCENE_ENABLED = False" in APP


def test_greeting_and_thought_wiring_untouched():
    assert '<h2 class="empty-greeting">{{ saathi_greeting_short }}</h2>' \
        in INDEX
    assert '<p class="empty-sub empty-thought">{{ daily_thought }}</p>' \
        in INDEX
    assert "import thoughts" in APP
