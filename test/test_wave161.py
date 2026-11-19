"""Wave 161 (Suraj, 18 Nov 2026): the mascot moved to a
centred line above the greeting, and a small copy of him
rode the header through an active chat.

Wave 181 update (Suraj, 19 Nov 2026): the SVG robot both
halves of that wave drew was replaced by the new RENDERED
mascot. The PLACEMENT contract this wave created survives
exactly and is what this file pins now:

  * the mascot stands at the top of the home, above the
    logo and the greeting, inside the Wave 168 top wrapper;
  * a small circle with the wave portrait rides the header
    through an active chat (.mascot-buddy), shown only
    while body.chat-active, never intercepting taps, still
    during page load, tilting while Ganitra solves and
    bouncing on a correct chat-test answer;
  * home mascot and header buddy never show together —
    body.chat-active hides the home one;
  * the palette pins of the old SVG are retired with the
    artwork (a photograph carries its own colours);
  * pins moved with the CSS: ?v=60 / ganitra-static-v37.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


def _rule(selector):
    start = CSS.index(selector + " {")
    return CSS[start:CSS.index("}", start)]


# --- Header buddy -------------------------------------------------

def test_buddy_markup_is_the_wave_portrait_circle():
    buddy = INDEX.index('<div class="mascot-buddy"')
    assert 'src="{{ url_for(\'static\', filename=\'robot-wave.webp\') }}"' \
        in INDEX[buddy:buddy + 400]
    # The buddy lives in the chat header (its Wave 161 seat)
    # and comes before the scrolling thread.
    assert INDEX.index('<header class="chat-header">') < buddy
    assert buddy < INDEX.index('<div class="chat-scroll"')


def test_buddy_shows_only_during_active_chat():
    assert "body.chat-active .mascot-buddy { display: block; }" in CSS
    rule = _rule(".mascot-buddy")
    assert "display: none" in rule
    assert "position: fixed" in rule
    assert "border-radius: 50%" in rule


def test_buddy_never_intercepts_taps():
    assert "pointer-events: none" in _rule(".mascot-buddy")


def test_buddy_thinking_tilt_and_cheer():
    # While Ganitra solves, the buddy tilts a touch; on a
    # correct chat-test answer it bounces (the Wave 181
    # form of the old buddy's thinking/cheer motion).
    assert "body:has(.bubble.typing) .mascot-buddy" in CSS
    assert "rotate(-3deg)" in CSS
    assert "body.mascot-cheer .mascot-buddy" in CSS
    assert "@keyframes mascot-cheer-bounce" in CSS
    # Driven from the answer hook, not on page load.
    assert 'showMascotPop("laugh", 1900)' in INDEX
    assert 'classList.add("mascot-cheer")' in INDEX


# --- Home placement -------------------------------------------------

def test_mascot_before_logo_and_greeting():
    top = INDEX.index('<div class="empty-robot-top"')
    home = INDEX.index('<div class="mascot-home"')
    logo = INDEX.index('class="empty-logo"')
    greeting = INDEX.index("{{ saathi_greeting_short }}")
    assert top < home < logo < greeting
    # The home mascot hides the moment a chat starts.
    assert "body.chat-active .empty-robot-top { display: none; }" in CSS


def test_home_circle_holds_only_the_wave_pose_still():
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the crossfade is gone: the circle holds ONLY
    # the wave pose, plainly visible and completely still.
    # (This test pinned the four-pose crossfade until now.)
    rule = _rule(".mascot-pose")
    assert "animation: mascot-cycle 24s linear infinite" not in rule
    assert "animation" not in rule
    assert "opacity: 1" in rule
    assert "@keyframes mascot-cycle" not in CSS
    assert 'class="mascot-pose mascot-pose-wave"' in INDEX
    for pose in ("think", "laugh", "kiss"):
        assert 'class="mascot-pose mascot-pose-%s"' % pose \
            not in INDEX
    for pose in ("wave", "think", "laugh", "kiss"):
        assert (ROOT / "static" / ("robot-%s.webp" % pose)).exists()


# --- Pins -----------------------------------------------------------

def test_pins_current():
    assert "v='60'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in SW
    assert '"/static/style.css?v=60"' in SW
