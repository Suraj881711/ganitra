"""Wave 181 (Suraj, 19 Nov 2026): the NEW MASCOT.

Suraj rejected the flat SVG robot — "Muse ki tarah real
nhi hai, real feelings nhi hai" — and approved (with a
heart, on the preview shot) a glossy RENDERED robot:
ivory-cream + deep teal + gold, a glowing mint heart on
its chest, two antenna light-balls. Four pose photographs
live in static/:

  robot-wave.webp   full body, waving (home + header)
  robot-think.webp  portrait, hand on chin
  robot-laugh.webp  portrait, laughing
  robot-kiss.webp   portrait, flying kiss with hearts

What this wave pins:

  * HOME: the mascot stands in a WHITE CIRCLE (soft teal
    ring + soft shadow) at the top of the empty state —
    the approved preview — with the name "Ganitra" below,
    and the four poses slowly crossfade inside the circle
    (wave, think, laugh, kiss, ~6 s each).
  * FULL moments (Suraj: "kabhi kabhi ye pura bhi dikhana
    chahiye"): the KISS pops full on page open (~2.2 s)
    and the LAUGH pops full on a correct chat-test answer
    (~1.9 s), both through the .mascot-pop overlay, both
    dismissible by tap.
  * HEADER: a small circle with the wave portrait rides
    the top bar through an active chat.
  * The typing bubble stays CLEAN (Wave 176) — no figure
    is re-added there; the Teach boy is untouched.
  * The old SVG robot machinery (home SVG, buddy SVG,
    robotSvg() poses, robot-* CSS/keyframes) is removed.
  * Pins: ?v=60 / ganitra-static-v37; the four portraits
    join the service-worker precache shell.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

POSES = ("wave", "think", "laugh", "kiss")


def _rule(selector):
    start = CSS.index(selector + " {")
    return CSS[start:CSS.index("}", start)]


# --- Assets ---------------------------------------------------------

def test_pose_images_exist_and_stay_light():
    total = 0
    for pose in POSES:
        path = ROOT / "static" / ("robot-%s.webp" % pose)
        assert path.exists(), pose
        size = path.stat().st_size
        assert 0 < size < 150_000, (pose, size)
        total += size
    # The free host's disk is tight: the whole mascot set
    # must stay well under 600 KB.
    assert total < 600_000, total


# --- Home circle ------------------------------------------------------

def test_home_circle_markup_and_pose_order():
    home = INDEX.index('<div class="mascot-home"')
    circle = INDEX.index('<div class="mascot-circle">')
    assert home < circle
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the circle holds ONLY the wave pose (the
    # think/laugh/kiss portraits no longer ride inside
    # it) and the name plate under it is gone.
    assert 'class="mascot-pose mascot-pose-wave"' in INDEX
    for p in ("think", "laugh", "kiss"):
        assert 'class="mascot-pose mascot-pose-%s"' % p \
            not in INDEX
    assert INDEX.count('class="mascot-pose ') == 1
    # Inside the Wave 168 top wrapper, gated on a named student.
    top = INDEX.index('<div class="empty-robot-top"')
    assert top < home
    assert "{% if saathi_name %}" in INDEX[
        INDEX.index('<div class="chat-shell">'):home]
    # No name plate anywhere.
    assert "mascot-name" not in INDEX


def test_circle_css_is_the_approved_white_circle():
    rule = _rule(".mascot-circle")
    assert "border-radius: 50%" in rule
    assert "background: #ffffff" in rule
    assert "rgba(10, 122, 100" in rule  # soft teal ring
    assert "box-shadow:" in rule
    assert "overflow: hidden" in rule
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the gentle bob no longer rides the circle;
    # the circle is completely still.
    assert "animation: mascot-bob" not in rule
    assert "animation" not in rule
    assert "@keyframes mascot-bob" not in CSS


def test_crossfade_cycle_css():
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the crossfade cycle is gone: the single
    # remaining pose is plainly visible and still. (The
    # per-pose delay rules below stay in the stylesheet
    # but are inert — no element cycles through them.)
    rule = _rule(".mascot-pose")
    assert "animation: mascot-cycle 24s linear infinite" not in rule
    assert "animation" not in rule
    assert "opacity: 1" in rule
    assert "@keyframes mascot-cycle" not in CSS
    # The wave pose is the resting face of the circle.
    wave = _rule(".mascot-pose-wave")
    assert "opacity: 1" in wave
    # Each later pose is delayed into its own quarter.
    for pose in ("think", "laugh", "kiss"):
        assert "animation-delay:" in _rule(".mascot-pose-%s" % pose)


# --- Full moments -----------------------------------------------------

def test_pop_overlay_markup_and_js():
    assert '<div class="mascot-pop" id="mascot-pop"' in INDEX
    assert 'id="mascot-pop-img"' in INDEX
    assert "function showMascotPop(kind, ms)" in INDEX
    assert "function hideMascotPop()" in INDEX
    # Tapping the moment dismisses it.
    assert 'pop.addEventListener("click", hideMascotPop)' in INDEX
    rule = _rule(".mascot-pop")
    assert "position: fixed" in rule
    assert "visibility: hidden" in rule
    assert ".mascot-pop.show" in CSS


def test_welcome_kiss_on_open():
    # The kiss greets a signed-in student on the home, once,
    # briefly — and only while the home is still showing.
    assert 'showMascotPop("kiss", 2200)' in INDEX
    assert 'document.getElementById("mascot-home")' in INDEX
    assert 'document.getElementById("chat-empty")' in INDEX
    assert "classList.contains(" in INDEX  # the chat-active guard


def test_laugh_on_correct_chat_test_answer():
    assert 'result.test_verdict === "correct"' in INDEX
    assert 'showMascotPop("laugh", 1900)' in INDEX
    assert 'classList.add("mascot-cheer")' in INDEX
    assert "@keyframes mascot-cheer-bounce" in CSS


# --- Header buddy -------------------------------------------------------

def test_header_buddy_is_a_wave_circle():
    buddy = INDEX.index('<div class="mascot-buddy"')
    assert "robot-wave.webp" in INDEX[buddy:buddy + 400]
    rule = _rule(".mascot-buddy")
    assert "border-radius: 50%" in rule
    assert "display: none" in rule
    assert "pointer-events: none" in rule
    assert "body.chat-active .mascot-buddy { display: block; }" in CSS


# --- Removals and untouched neighbours -----------------------------------

def test_old_svg_robot_machinery_removed():
    assert '<svg class="robot"' not in INDEX
    assert '<svg class="robot-buddy-svg"' not in INDEX
    assert "function robotSvg" not in INDEX
    assert "function addTypingRobot" not in INDEX
    assert 'class="robot-card"' not in INDEX
    assert ".robot {" not in CSS
    assert ".robot-card" not in CSS
    assert ".robot-buddy" not in CSS
    assert "@keyframes robot-" not in CSS


def test_typing_bubble_stays_clean_and_boy_untouched():
    # Deploy-44 merge update: Wave 176 (merged alongside)
    # removed the boy's typing post — no figure rides the
    # thinking bubble. His Teach-board post is a different
    # seat and is untouched.
    assert 'id="typing-template"' in INDEX
    assert "addTypingBoy" not in INDEX
    assert "function showBoyWriter" in INDEX
    assert (ROOT / "static" / "scene-boy.webp").exists()


def test_reduced_motion_rests_on_wave():
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the pose is always plainly visible now, so
    # reduced motion no longer hides the poses; it only
    # drops the pop zoom.
    assert ".mascot-pose { opacity: 0; }" not in CSS
    assert ".mascot-pop img { transition: none; transform: none; }" \
        in CSS


# --- Pins and precache -----------------------------------------------------

def test_pins_and_precache():
    assert "v='60'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in SW
    assert '"/static/style.css?v=60"' in SW
    for pose in POSES:
        assert '"/static/robot-%s.webp"' % pose in SW


# --- The page itself renders the mascot -------------------------------------

def test_signed_in_home_renders_mascot(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W181 Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w181-test-pass"})
    page = client.get("/").get_data(as_text=True)
    assert 'class="mascot-circle"' in page
    assert "robot-wave.webp" in page
    assert "robot-kiss.webp" in page
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — no name plate in the rendered page either.
    assert "mascot-name" not in page
    assert 'id="mascot-pop"' in page
    assert '<svg class="robot"' not in page
