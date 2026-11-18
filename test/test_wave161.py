"""Wave 161 (Suraj, 18 Nov 2026, after seeing the LIVE
Deploy-34 robot screenshot): three fixes to the Wave 160
robot, all ordered by him the same afternoon.

  1. ~15:28 IST — "Robot achhe se nhi dikh rha, robot ke
     colour ko dark karo": the pale cream robot washed out
     on the cream page, so the palette is DARKENED
     everywhere the robot appears (home SVG, the robotSvg()
     JS minis, the test-correct laugh mini, the new buddy):
     body cream #fdf0dd -> #f0d3a0, teal #0d9b83 ->
     #0a7a64, deep #0b5a4a -> #074335, smile #0b8a72 ->
     #076e59, seam #e8d9c4 -> #dbb87e, pencil #f3e3c2 ->
     #e8cc97, notebook paper #fffaf0 -> #f7ead2. The
     antenna LIGHT balls stay bright mint (#2fe8b8 /
     #46f2c3) so they glow against the darker body, and a
     soft drop shadow separates the robot from the page.
     Same character, same shapes, same animations.
  2. ~15:28 IST — "robot ko Muse ki tarah top or beech
     mai kar do": on the home empty state the robot moved
     from the greeting's left to a CENTRED line ABOVE the
     greeting (.empty-hello is a centred column: robot,
     then "Hello <name>", then the thought below).
  3. ~15:30 IST — "Agar chat bhi kar rahe hai jab bhi
     rahana chahiye Robot", refined ~15:31 IST ("Jaise
     Muse kaam karta hai naa waise"): a small BUDDY copy
     of the robot rides the header band through an active
     chat and mirrors the work state — calm attentive idle
     (blink, bob, wave, soft light pulse); a thinking face
     + head tilt + brighter alternating lights while the
     typing bubble is in the DOM (pure CSS :has on
     .bubble.typing, the exact signal both typing paths
     produce, so it cannot drift out of sync); a brief
     laugh when a chat-test answer is correct (the
     test_verdict hook adds body.robot-buddy-cheer for a
     moment). The buddy shows only under body.chat-active
     (set by hideEmpty() when the empty state goes away),
     so it and the big home robot never show together. It
     is fixed, pointer-events: none and aria-hidden — it
     covers no message, takes no tap, shifts no layout.

Pins moved with the CSS: ?v=52 / ganitra-static-v31.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

HOME = INDEX[INDEX.index('<svg class="robot"'):
             INDEX.index("</svg>", INDEX.index('<svg class="robot"'))]
BUDDY = INDEX[INDEX.index('<div class="robot-buddy"'):
              INDEX.index("</svg>",
                          INDEX.index('<div class="robot-buddy"'))]


def _rule(selector):
    block = CSS[CSS.index(selector + " {"):]
    return block[:block.index("}")]


def _centres(text, cls):
    return {(m.group(1), m.group(2)) for m in re.finditer(
        r'class="%s"\s+cx="([\d.]+)"\s+cy="([\d.]+)"' % cls, text)}


def _luminance(hex_colour):
    h = hex_colour.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    rgb = [c / 12.92 if c <= 0.04045
           else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


# --- 1. The darker palette -------------------------------------------

OLD_TO_NEW = {
    "#fdf0dd": "#f0d3a0",   # body cream -> deeper caramel cream
    "#0d9b83": "#0a7a64",   # teal accent -> deeper teal
    "#0b5a4a": "#074335",   # deep tone -> deeper still
    "#0b8a72": "#076e59",   # smile teal
    "#e8d9c4": "#dbb87e",   # body seam
    "#f3e3c2": "#e8cc97",   # pencil wood tip
    "#fffaf0": "#f7ead2",   # notebook paper
}


def test_old_palette_fully_gone_new_palette_everywhere():
    for old in OLD_TO_NEW:
        assert old not in INDEX, old
    for new in OLD_TO_NEW.values():
        assert new in INDEX, new
    # The home robot, the JS minis and the buddy all carry
    # the darkened body + accent tones.
    assert "#f0d3a0" in HOME and "#0a7a64" in HOME
    assert "#f0d3a0" in BUDDY and "#0a7a64" in BUDDY
    js = INDEX[INDEX.index("function robotSvg(kind)"):]
    assert "#f0d3a0" in js and "#0a7a64" in js


def test_palette_is_measurably_darker():
    for old, new in OLD_TO_NEW.items():
        assert _luminance(new) < _luminance(old), (old, new)
    # The body — the big washed-out area — drops decisively.
    assert _luminance("#fdf0dd") - _luminance("#f0d3a0") > 0.10
    assert _luminance("#0d9b83") - _luminance("#0a7a64") > 0.05
    assert _luminance("#0b5a4a") - _luminance("#074335") > 0.02


def test_lights_stay_bright_mint():
    # The antenna light balls and the eye cores did NOT
    # darken — they are the glow against the darker body.
    assert "#2fe8b8" in INDEX and "#46f2c3" in INDEX
    assert _centres(HOME, "robot-ball") == {("37", "6"), ("63", "6")}
    assert 'fill="#2fe8b8"' in HOME and 'fill="#2fe8b8"' in BUDDY


def test_drop_shadow_separation():
    assert "drop-shadow" in _rule(".robot")
    assert "drop-shadow" in _rule(".robot-buddy-svg")


# --- 2. Centred placement above the greeting --------------------------

def test_home_robot_centred_above_greeting():
    # DOM order inside the empty state: robot, greeting,
    # thought — and the container stacks them centred.
    assert INDEX.index('class="robot"') < \
        INDEX.index("{{ saathi_greeting_short }}")
    assert INDEX.index("{{ saathi_greeting_short }}") < \
        INDEX.index("{{ daily_thought }}")
    rule = _rule(".empty-hello")
    assert "flex-direction: column" in rule
    assert "align-items: center" in rule
    assert "justify-content: center" in rule


# --- 3. The chat buddy --------------------------------------------------

def test_buddy_markup_in_header_with_all_faces():
    assert '<div class="robot-buddy" aria-hidden="true">' in INDEX
    assert 'class="robot-buddy-svg"' in INDEX
    assert 'class="robot-buddy-arm"' in BUDDY  # the wave hand
    for face in ("calm", "busy", "laugh"):
        assert 'robot-buddy-face-%s' % face in BUDDY
    assert 'class="robot-eyes"' in BUDDY  # blink rides along
    # The buddy lives in the header, before the chat thread.
    assert INDEX.index('<div class="robot-buddy"') < \
        INDEX.index('id="chat-empty"')
    # Same geometry contract as the home robot's lights.
    assert _centres(BUDDY, "robot-ball") == {("37", "6"), ("63", "6")}


def test_buddy_visibility_rule_home_vs_chat():
    # Hidden by default (the empty state is showing)…
    assert "display: none" in _rule(".robot-buddy")
    # …revealed only once chatting starts: hideEmpty() puts
    # chat-active on the body as it removes the empty state,
    # so the buddy and the big home robot never co-show.
    assert 'body.chat-active .robot-buddy { display: block; }' in CSS
    assert 'classList.add("chat-active")' in INDEX


def test_buddy_never_blocks_or_covers():
    rule = _rule(".robot-buddy")
    assert "pointer-events: none" in rule
    assert "position: fixed" in rule


def test_buddy_busy_state_synced_to_typing_bubble():
    # Pure CSS on the typing bubble's DOM presence — the
    # signal both typing paths (template clone + fallback
    # bubble) produce and remove together.
    assert "body:has(.bubble.typing) .robot-buddy-face-busy " \
        "{ opacity: 1; }" in CSS
    assert "body:has(.bubble.typing) .robot-buddy-face-calm " \
        "{ opacity: 0; }" in CSS
    # Brighter, alternating lights while solving (the same
    # blink the typing-bubble duo uses).
    assert "body:has(.bubble.typing) .robot-buddy " \
        ".robot-light-halo" in CSS
    assert "robot-blink-alt" in CSS
    # The fallback typing path really does build a .typing
    # bubble, and the template clone carries the class too.
    assert 'addBubble("bot typing"' in INDEX
    assert 'class="bubble bot typing typing-indicator"' in INDEX


def test_buddy_cheer_hook_on_correct_test_answer():
    # The JS hook rides the EXISTING test_verdict block…
    hook = INDEX.index('classList.add("robot-buddy-cheer")')
    assert hook > INDEX.index('result.test_verdict === "correct"')
    assert 'classList.remove(\n                  "robot-buddy-cheer")' \
        in INDEX or "robot-buddy-cheer" in INDEX
    # …and the CSS turns it into a brief laugh.
    assert "body.robot-buddy-cheer .robot-buddy-face-laugh " \
        "{ opacity: 1; }" in CSS
    assert "body.robot-buddy-cheer .robot-buddy-face-calm " \
        "{ opacity: 0; }" in CSS


def test_buddy_reduced_motion_stills():
    blocks = re.findall(
        r"@media \(prefers-reduced-motion: reduce\) \{(.*?)\n\}",
        CSS, re.S)
    buddy = [b for b in blocks if ".robot-buddy-svg" in b]
    assert buddy, "a reduced-motion block stills the buddy"
    assert "animation: none" in buddy[0]
    assert "robot-buddy-face-busy" in buddy[0]


# --- Behaviour preservation (Wave 160, byte-level apart from palette) ---

def test_wave160_behaviours_survive():
    assert HOME.count('class="robot-heart"') == 7
    for kf in ("robot-kiss-face", "robot-heart-rise",
               "robot-grab-show", "robot-grab-hide",
               "robot-monkey-hop", "robot-pose-think",
               "robot-pose-write", "robot-twinkle-once",
               "robot-blink-alt", "robot-glow-soft"):
        assert "@keyframes %s" % kf in CSS
    # The antenna-grab precision contract is untouched.
    assert _centres(INDEX, "robot-grab-hand") == \
        {("63", "6"), ("61", "7")}
    assert _centres(INDEX, "robot-grab-hand") <= \
        _centres(INDEX, "robot-ball")
    for kind in ("think", "write", "laugh"):
        assert 'robotSvg("%s")' % kind in INDEX


def test_pins_moved_to_v51_v28():
    assert "v='54'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v31"' in SW
    assert '"/static/style.css?v=54"' in SW
