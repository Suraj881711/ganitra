"""Wave 160 (Suraj, 18 Nov 2026): the robot mascot with
activity states — the teddy of Wave 155 was rejected and
replaced by Suraj's LOCKED robot character ("Yahi done
karo"), refined by his follow-up orders the same day.

Pins:
  * the teddy is FULLY gone (markup + CSS), the robot is in
    the signed-in empty state with BOTH hands showing;
  * the character: small chubby cream robot, teal-green ear
    caps / hands / feet / chest button / belly patch,
    glowing teal eyes, TWO antenna light balls — no letter
    G anywhere in the mascot;
  * opening sequence (one-shot on page load): flying kiss
    (kiss face + hand at the mouth), then hearts float up
    like bubbles, then the idle cycle takes over;
  * idle cycle: bob, blink, wave-then-rest, soft pulsing
    light glow, and occasional beats — a laugh (arc eyes,
    wide mouth, bounce, light twinkle), an antenna grab
    (arm FULLY up, the grab hand centred EXACTLY on the
    right light ball, look-up face), monkey play (hop,
    kicking legs, head-scratch hand, cheeky grin, light
    twinkle);
  * loading bubble: a mini robot duo — HUMAN thinking pose
    (hand on head, hand on waist, eyes up) alternating with
    the WRITING pose (notebook, green pencil, squiggles),
    lights blinking alternately and brighter; the writing
    robot also grabs its light ball occasionally; the
    Wave 23 boy and the Wave 145 dots are untouched;
  * chat test: a CORRECT answer's payload carries
    test_verdict "correct" and the JS puts the laughing
    mini robot in that bubble only; wrong answers get none;
  * light system per state: idle soft pulse (robot-glow-
    soft), loading alternate blink (robot-blink-alt), happy
    twinkle (robot-twinkle / robot-twinkle-once /
    robot-twinkle-monkey);
  * prefers-reduced-motion stills everything (static smile
    pose at home, writing pose only in the bubble, static
    soft glow);
  * pins moved with the CSS/JS: ?v=52 / ganitra-static-v30
    (Wave 161 moved them on from ?v=50 / v27 — palette +
    placement only; every behaviour pin below is unchanged);
  * SCENE_ENABLED stays False; greeting + thought wiring is
    Wave 155's and untouched.
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

HOME = INDEX[INDEX.index('<svg class="robot"'):
             INDEX.index("</svg>", INDEX.index('<svg class="robot"'))]


def _centres(text, cls):
    return {(m.group(1), m.group(2)) for m in re.finditer(
        r'class="%s"\s+cx="([\d.]+)"\s+cy="([\d.]+)"' % cls, text)}


# --- The teddy is gone; the robot is here ---------------------------

def test_teddy_fully_removed():
    assert 'class="mascot' not in INDEX
    assert "mascot-paw" not in INDEX and "mascot-eyes" not in INDEX
    assert ".mascot" not in CSS
    assert "@keyframes mascot-" not in CSS
    assert "mascot-bob" not in CSS and "mascot-wave" not in CSS


def test_robot_in_empty_state_with_both_hands():
    assert '<svg class="robot" viewBox="0 0 100 100"' in INDEX
    assert 'class="robot-eyes"' in HOME
    assert 'class="robot-arm"' in HOME        # the waving hand
    assert 'class="robot-arm-rest"' in HOME   # the resting hand
    assert 'class="robot-face-smile"' in HOME
    # Empty state only — before the sign-in card styles.
    assert INDEX.index('class="robot"') < \
        INDEX.index('id="signin-card-style"')
    # Inline and original: no external file, no logo machinery.
    assert "http" not in HOME and "url_for" not in HOME


def test_two_antenna_lights_on_the_home_robot():
    assert _centres(HOME, "robot-ball") == {("37", "6"), ("63", "6")}
    assert HOME.count('class="robot-light-halo"') == 2
    assert HOME.count('class="robot-light-flare"') == 2
    assert HOME.count('class="robot-light-flare2"') == 2


# --- Opening sequence -------------------------------------------------

def test_opening_kiss_and_heart_bubbles():
    assert 'class="robot-face-kiss"' in HOME
    assert 'class="robot-kiss-hand"' in HOME
    assert 'class="robot-hearts"' in HOME
    assert HOME.count('class="robot-heart"') == 7
    assert "@keyframes robot-kiss-face" in CSS
    assert "@keyframes robot-kiss-hand" in CSS
    assert "@keyframes robot-heart-rise" in CSS
    # One-shot: the kiss and the hearts run once, not in a loop.
    assert "animation: robot-kiss-face 2.2s linear 1 both" in CSS
    assert "animation: robot-heart-rise 1.6s ease-out 1 both" in CSS


# --- Idle beats ---------------------------------------------------------

def test_idle_laugh_beat():
    assert 'class="robot-face-laugh"' in HOME
    assert 'class="robot-inner"' in HOME
    assert "@keyframes robot-face-laugh-cycle" in CSS
    assert "@keyframes robot-laugh-bounce" in CSS
    assert "@keyframes robot-face-smile-cycle" in CSS


def test_antenna_grab_beat_and_hand_precision():
    assert 'class="robot-grab-arm"' in HOME
    assert 'class="robot-face-lookup"' in HOME
    assert "@keyframes robot-grab-show" in CSS
    assert "@keyframes robot-grab-hide" in CSS
    # Suraj's precision point: every grab hand is centred
    # EXACTLY on one of the robot's own light balls (the
    # home robot's right ball, the writing mini's right
    # ball) — the ball stays on its antenna.
    balls = _centres(INDEX, "robot-ball")
    grabs = _centres(INDEX, "robot-grab-hand")
    assert grabs == {("63", "6"), ("61", "7")}
    assert grabs <= balls


def test_monkey_play_beat():
    assert 'class="robot-monkey-face"' in HOME
    assert 'class="robot-monkey-scratch"' in HOME
    assert 'class="robot-hop"' in HOME
    assert 'class="robot-foot-l"' in HOME
    assert 'class="robot-foot-r"' in HOME
    assert "@keyframes robot-monkey-hop" in CSS
    assert "@keyframes robot-monkey-show" in CSS
    assert "@keyframes robot-scratch-wiggle" in CSS
    assert "@keyframes robot-kick-l" in CSS
    assert "@keyframes robot-kick-r" in CSS
    assert "@keyframes robot-twinkle-monkey" in CSS


# --- The light system per state -----------------------------------------

def test_light_system_keyframes_per_state():
    # Idle / home: soft gentle pulse.
    assert "@keyframes robot-glow-soft" in CSS
    assert "animation: robot-glow-soft" in CSS
    # Loading: brighter, alternating left-right blink.
    assert "@keyframes robot-blink-alt" in CSS
    assert ".robot-duo .robot-light-halo" in CSS
    assert ".robot-duo .robot-light-halo-r" in CSS
    assert "robot-light-halo-r" in INDEX  # the minis' right light
    # Happy moments: twinkle bursts (laugh + test-correct).
    assert "@keyframes robot-twinkle" in CSS
    assert "@keyframes robot-twinkle-once" in CSS
    assert ".robot-laugh-mini .robot-light-flare" in CSS


# --- The loading bubble duo ----------------------------------------------

def test_loading_duo_think_and_write_poses():
    assert "function robotSvg(kind)" in INDEX
    assert "function addTypingRobot(node)" in INDEX
    assert "addTypingRobot(node)" in INDEX
    assert "addTypingRobot(fb)" in INDEX
    assert 'robotSvg("think")' in INDEX
    assert 'robotSvg("write")' in INDEX
    assert 'class="robot-pose-think"' in INDEX
    assert 'class="robot-pose-write"' in INDEX
    assert 'className = "robot-duo"' in INDEX
    assert "@keyframes robot-pose-think" in CSS
    assert "@keyframes robot-pose-write" in CSS
    # Writing pose machinery: pencil + appearing squiggles.
    assert 'class="robot-pencil"' in INDEX
    assert 'class="robot-squiggle sq1"' in INDEX
    assert "@keyframes robot-write" in CSS
    assert "@keyframes robot-squiggle" in CSS
    # The mini writing robot grabs its light ball too, and
    # looks up while doing it.
    assert 'class="robot-mini-grab"' in INDEX
    assert 'class="robot-mini-lookup"' in INDEX
    # The typing bubble itself (Wave 145) is untouched.
    assert 'id="typing-template"' in INDEX
    assert "chat_thinking" in INDEX
    # The Wave 23 boy still rides the bubble as before.
    assert "addTypingBoy(node)" in INDEX
    assert "addTypingBoy(fb)" in INDEX


# --- Laugh on a correct chat-test answer ----------------------------------

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
    # A wrong answer carries NO verdict (no laughing robot).
    session2 = {}
    chat_test.handle_message(session2, None, 1, "test do", "en")
    wrong = chat_test.handle_message(
        session2, None, 1, "zzz-not-the-answer", "en")
    assert "test_verdict" not in wrong["result"]


def test_laugh_robot_js_hook():
    assert 'result.test_verdict === "correct"' in INDEX
    assert 'className = "robot-laugh-mini"' in INDEX
    assert 'robotSvg("laugh")' in INDEX
    assert 'class="robot-pose-laugh"' in INDEX
    assert ".robot-laugh-mini" in CSS
    # The server only ever sets the flag from the verdict.
    assert 'verdict="correct" if correct else None' in CHAT_TEST


# --- The feelings pass -----------------------------------------------------

def test_feelings_expression_groups_and_noticing_tilt():
    # Every home state carries its OWN facial expression
    # group — feelings, not pose swaps.
    for cls in ("robot-face-smile", "robot-face-laugh",
                "robot-face-kiss", "robot-face-lookup",
                "robot-monkey-face"):
        assert 'class="%s"' % cls in HOME
    # The "noticing you" lean-in: a tilt wrapper + keyframes
    # with a long stillness and a soft settle.
    assert 'class="robot-tilt"' in HOME
    assert "@keyframes robot-notice-tilt" in CSS
    assert ".robot-tilt {" in CSS
    # The laugh lands after an anticipation dip, not cold.
    bounce = CSS[CSS.index("@keyframes robot-laugh-bounce"):]
    assert "translateY(0.9px)" in bounce[:400]
    # The thinking mini leans its head (lost in thought);
    # the writing mini's gaze is DOWN on the notebook.
    assert ".robot-pose-think {" in CSS
    think_rule = CSS[CSS.index(".robot-pose-think {"):]
    assert "rotate(-2deg)" in think_rule[:200]
    assert 'cy="31.5"' in INDEX  # writing eyes lowered


# --- Reduced motion, pins, parked scene -----------------------------------

def test_reduced_motion_stills_everything():
    blocks = re.findall(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}",
        CSS, re.S)
    w160 = [b for b in blocks if "robot-grab-arm" in b]
    assert w160, "the Wave 160 reduced-motion block exists"
    block = w160[0]
    assert "animation: none" in block
    assert ".robot-pose-think { opacity: 0; }" in CSS
    assert ".robot-pose-write { opacity: 1; }" in CSS
    assert ".robot-light-halo { opacity: 0.35; }" in CSS
    assert ".robot-squiggle { stroke-dashoffset: 0; }" in CSS


def test_pins_and_scene_flag():
    assert "v='53'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v30"' in SW
    assert '"/static/style.css?v=53"' in SW
    assert "SCENE_ENABLED = False" in APP


def test_greeting_and_thought_wiring_untouched():
    assert '<h2 class="empty-greeting">{{ saathi_greeting_short }}</h2>' \
        in INDEX
    assert '<p class="empty-sub empty-thought">{{ daily_thought }}</p>' \
        in INDEX
    assert "import thoughts" in APP
