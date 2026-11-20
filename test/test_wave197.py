"""Wave 197 (Suraj, 20 Nov 2026): the home mascot circle
is COMPLETELY STILL and the name plate is GONE.

Suraj's order, verbatim sense: "Robot wala circle hil
kyu rha hai or ye uske neeche ganitra kyu likha aa rha
hai maine toh nhi bola waha par ganitra ko likho apni
marji se add kar diya" — the circle MOVED (the gentle
bob + the four-pose crossfade) and the word "Ganitra"
under the circle was an unasked addition. His standing
rule: no unasked UI additions. So:

  * the "Ganitra" name plate under the circle is
    REMOVED — no .mascot-name markup, no .mascot-name
    CSS rule, nothing in the rendered home page;
  * the circle is STILL: the mascot-bob animation and
    the mascot-cycle crossfade are gone, the think /
    laugh / kiss poses no longer ride inside the
    circle — only the wave portrait remains, plainly
    visible (opacity 1, no animation);
  * UNTOUCHED, because Suraj explicitly ordered them
    earlier: the .mascot-pop full-size moments (the
    kiss on page open, the laugh on a correct chat-test
    answer — "kabhi kabhi ye pura bhi dikhana chahiye")
    and the header .mascot-buddy.
  * Pins: ?v=60 / ganitra-static-v37.
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


# --- (a) The name plate is gone -------------------------------------

def test_no_mascot_name_anywhere():
    assert "mascot-name" not in INDEX
    assert '<div class="mascot-name">Ganitra</div>' not in INDEX
    assert ".mascot-name" not in CSS


# --- (b) Exactly one pose in the circle: the wave -------------------

def test_circle_holds_only_the_wave_pose():
    circle = INDEX.index('<div class="mascot-circle">')
    block = INDEX[circle:INDEX.index("</div>", circle)]
    assert block.count('class="mascot-pose ') == 1
    assert 'class="mascot-pose mascot-pose-wave"' in block
    assert "robot-wave.webp" in block
    # No other pose rides the page as a circle portrait.
    for pose in ("think", "laugh", "kiss"):
        assert 'class="mascot-pose mascot-pose-%s"' % pose \
            not in INDEX


# --- (c) The circle is completely still ------------------------------

def test_circle_css_has_no_bob_and_no_cycle():
    assert "mascot-bob" not in CSS
    assert "mascot-cycle" not in CSS
    assert "animation" not in _rule(".mascot-circle")
    pose = _rule(".mascot-pose")
    assert "animation" not in pose
    assert "opacity: 1" in pose
    # Reduced motion no longer needs to hide the poses.
    assert ".mascot-pose { opacity: 0; }" not in CSS
    assert ".mascot-pop img { transition: none; transform: none; }" \
        in CSS


# --- (d) The full-size special moments stay ---------------------------

def test_pop_overlay_still_present():
    assert '<div class="mascot-pop" id="mascot-pop"' in INDEX
    assert 'id="mascot-pop-img"' in INDEX
    assert "function showMascotPop(kind, ms)" in INDEX
    assert "function hideMascotPop()" in INDEX
    assert 'showMascotPop("kiss", 2200)' in INDEX
    assert 'showMascotPop("laugh", 1900)' in INDEX
    assert ".mascot-pop.show" in CSS


# --- (e) The header buddy stays ---------------------------------------

def test_header_buddy_still_present():
    buddy = INDEX.index('<div class="mascot-buddy"')
    assert "robot-wave.webp" in INDEX[buddy:buddy + 400]
    assert "body.chat-active .mascot-buddy { display: block; }" in CSS


# --- Pins --------------------------------------------------------------

def test_pins_current():
    assert "v='61'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v38"' in SW
    assert '"/static/style.css?v=61"' in SW


# --- The rendered home page ---------------------------------------------

def test_signed_in_home_renders_still_nameless_mascot(
        tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W197 Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w197-test-pass"})
    page = client.get("/").get_data(as_text=True)
    assert 'class="mascot-circle"' in page
    assert "robot-wave.webp" in page
    assert "mascot-name" not in page
    assert 'class="mascot-pose mascot-pose-think"' not in page
    assert 'class="mascot-pose mascot-pose-laugh"' not in page
    assert 'class="mascot-pose mascot-pose-kiss"' not in page
    assert 'id="mascot-pop"' in page
    assert 'class="mascot-buddy"' in page
