"""Wave 23 (Suraj, 12 Nov 2026, ~23:21-23:25 IST): the LOGO
JUNGLE + the boy writer.

Part 1 — on the empty chat screen, wordless jungle scenes play
around the hero logo ("kabhi eagle aake logo par baith jaaye,
kabhi sher chalke side se aaye, logo ko dhakka deke bahar le
jaaye, toh Mowgli jaisa ladka logo ko wapas leke aaye"): the
eagle perches on the logo; the tiger cub rolls it off-stage
and the jungle boy brings it back; and in Scene C the tiger
drags the logo away, the boy (stick in hand) chases it down,
hugs the logo and carries it home. The schedule is deliberately
unpredictable: first scene at a random ~5-15s, gaps of a random
~25-75s, scene order shuffled with no back-to-back repeat.
Tapping the stage plays a scene instantly; scenes stop when
the student starts typing, pause while the tab is hidden, and
never run under prefers-reduced-motion. The frozen logo files
are never edited — only CSS transforms move their <img>.

Part 2 — when the student starts working, the boy "writes":
beside the thinking indicator while an answer is generated,
and at the steps board (in a reserved right rail) while Teach
playback runs; he leaves ~1s after Teach ends.

These tests pin what Python can see: the served stage markup,
the sprites, the director's pure logic run under node
(extracted between the SCENE-LOGIC markers, the Wave-18/23
harness pattern), the Teach/loading hook wiring, and the
frozen-logo digests.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

LOGO_MD5 = {
    "logo-full-t.png": "15def831bc209625d6a9ce99a7e68587",
    "logo-mark-t.png": "a91866e864db7f10994ab39ec2ea9ea2",
    "logo-full.png": "8ffea6f4e42d3d3b1bd8552e26579c4c",
    "logo-mark.png": "5a190086234946460217a93148632125",
}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_stage_markup_served_on_empty_chat(client):
    # The chat page renders for a signed-in student.
    r = client.post("/signup", data={
        "name": "W23 Scenes Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w23-scenes-pass"})
    assert r.status_code in (200, 302)
    r = client.get("/")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert 'id="scene-stage"' in body
    assert 'id="scene-logo"' in body
    # The logo still renders above the greeting (Wave-8 order).
    assert body.index("logo-full-t.png") < body.index("empty-greeting")
    for actor in ("eagle", "tiger", "boy"):
        assert f'id="scene-{actor}"' in body
        assert f"scene-{actor}.webp" in body
    # Scene C's stick prop rides in the stage too.
    assert 'id="scene-stick"' in body


def test_scene_sprites_exist_and_are_served(client):
    for actor in ("eagle", "tiger", "boy"):
        f = ROOT / "static" / f"scene-{actor}.webp"
        assert f.exists() and f.stat().st_size > 50_000
        r = client.get(f"/static/scene-{actor}.webp")
        assert r.status_code == 200
        assert r.content_type.startswith("image/")


def test_frozen_logos_byte_unchanged():
    for name, want in LOGO_MD5.items():
        digest = hashlib.md5((ROOT / "static" / name).read_bytes())
        assert digest.hexdigest() == want, name


def test_director_wiring_and_restraint():
    assert "/* SCENE-LOGIC-BEGIN */" in INDEX
    assert "/* SCENE-LOGIC-END */" in INDEX
    for fn in ("pickSceneName", "sceneDelayMs", "firstSceneDelayMs",
               "playNext", "stopScenes", "schedule"):
        assert f"function {fn}" in INDEX
    # First scene is scheduled; the picker gets the last scene
    # so it can avoid repeating it.
    assert "schedule(true)" in INDEX
    assert "pickSceneName(lastScene)" in INDEX
    # Tap-to-play on the stage itself.
    assert 'stage.addEventListener("click"' in INDEX
    # Pause/stop conditions: typing, hidden tab, reduced motion.
    assert 'addEventListener("input", stopScenes)' in INDEX
    assert "visibilitychange" in INDEX
    assert "(prefers-reduced-motion: reduce)" in INDEX
    assert "if (reduced) return;" in INDEX
    # A dead sprite disables the scenes silently.
    assert 'addEventListener("error", stopScenes)' in INDEX
    assert "naturalWidth === 0" in INDEX


def test_scene_css_tracks_and_reduced_motion():
    for needle in (".scene-stage", ".scene-actor",
                   "@keyframes eagle-visit", "@keyframes tiger-visit",
                   "@keyframes logo-rolled", "@keyframes boy-rescue"):
        assert needle in CSS
    w23 = CSS[CSS.index("Wave 23: Logo Jungle"):]
    assert "@media (prefers-reduced-motion: reduce)" in w23
    assert ".scene-actor { display: none" in w23
    # Scene durations in the CSS match the director's SCENE_MS.
    assert "eagle-visit 5.4s" in CSS
    assert "tiger-visit 8.6s" in CSS
    assert "logo-rolled 8.6s" in CSS
    assert "boy-rescue 8.6s" in CSS


def test_scene_c_chase_and_rescue():
    # The stick prop is in the stage markup.
    assert 'id="scene-stick"' in INDEX
    assert 'class="scene-stick"' in INDEX
    # All four Scene C tracks exist at the shared 11.2s duration.
    for needle in ("@keyframes chase-tiger", "@keyframes chase-logo",
                   "@keyframes chase-boy", "@keyframes stick-arc",
                   ".scene-stick", "--chase-x", ".playing-chase"):
        assert needle in CSS
    assert "chase-tiger 11.2s" in CSS
    assert "chase-logo 11.2s" in CSS
    assert "chase-boy 11.2s" in CSS
    assert "stick-arc 11.2s" in CSS
    # The hug: the logo's chase track carries the squeeze pulse.
    chase_logo = CSS[CSS.index("@keyframes chase-logo"):]
    chase_logo = chase_logo[:chase_logo.index("\n}")]
    assert "scale(1.06)" in chase_logo


def test_scene_logic_under_node():
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    start = INDEX.index("/* SCENE-LOGIC-BEGIN")
    end = INDEX.index("/* SCENE-LOGIC-END */") + \
        len("/* SCENE-LOGIC-END */")
    driver = INDEX[start:end] + r"""
var out = {};
out.order = SCENE_ORDER.slice();
out.ms = [SCENE_MS.eagle, SCENE_MS.tiger, SCENE_MS.chase];
function draws(prev, n) {
  var seen = {}, bad = 0;
  for (var i = 0; i < n; i++) {
    var s = pickSceneName(prev);
    if (s === prev || SCENE_ORDER.indexOf(s) < 0) bad++;
    seen[s] = 1;
  }
  return { seen: Object.keys(seen).sort(), bad: bad };
}
out.from_null = draws(null, 600);
out.from_eagle = draws("eagle", 600);
out.from_tiger = draws("tiger", 600);
out.from_chase = draws("chase", 600);
var prev = null, rep = 0;
for (var k = 0; k < 3000; k++) {
  var nx = pickSceneName(prev);
  if (nx === prev) rep++;
  prev = nx;
}
out.repeats = rep;
out.delay_min = sceneDelayMs(0);
out.delay_max = sceneDelayMs(0.999999);
var ok = true;
for (var i = 0; i < 2000; i++) {
  var d = sceneDelayMs();
  if (d < 25000 || d >= 75000) ok = false;
}
out.delay_range_ok = ok;
out.first_min = firstSceneDelayMs(0);
out.first_max = firstSceneDelayMs(0.999999);
var ok2 = true;
for (var j = 0; j < 2000; j++) {
  var f = firstSceneDelayMs();
  if (f < 5000 || f >= 15000) ok2 = false;
}
out.first_range_ok = ok2;
console.log(JSON.stringify(out));
"""
    p = Path("/tmp/test-w23-scenes.js")
    p.write_text(driver, encoding="utf-8")
    r = subprocess.run([node, str(p)], capture_output=True, text=True)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["order"] == ["eagle", "tiger", "chase"]
    assert out["ms"] == [5400, 8600, 11200]
    # No back-to-back repeat, ever, and every other scene is
    # reachable from any previous scene (a real shuffle).
    assert out["repeats"] == 0
    for key in ("from_null", "from_eagle", "from_tiger", "from_chase"):
        assert out[key]["bad"] == 0
    assert out["from_null"]["seen"] == ["chase", "eagle", "tiger"]
    assert out["from_eagle"]["seen"] == ["chase", "tiger"]
    assert out["from_tiger"]["seen"] == ["chase", "eagle"]
    assert out["from_chase"]["seen"] == ["eagle", "tiger"]
    # Randomised gaps 25-75s; randomised first scene 5-15s.
    assert out["delay_min"] == 25000
    assert out["delay_max"] == 74999
    assert out["delay_range_ok"] is True
    assert out["first_min"] == 5000
    assert out["first_max"] == 14999
    assert out["first_range_ok"] is True


def test_boy_writer_hooks():
    for fn in ("showBoyWriter", "hideBoyWriter",
               "scheduleBoyWriterHide", "addTypingBoy"):
        assert f"function {fn}" in INDEX
    # No steps board -> no boy.
    assert "if (boyBroken || !stepsDet) return;" in INDEX
    # Teach start/stop wiring.
    t0 = INDEX.index("function startTeachPlayback")
    t1 = INDEX.index("if ((result.steps", t0)
    assert "showBoyWriter();" in INDEX[t0:t1]
    stop = INDEX[INDEX.index("function stopTeachPlayback"):t0]
    assert "scheduleBoyWriterHide();" in stop
    # Loading wiring: both addTyping paths carry the boy.
    a0 = INDEX.index("function addTyping()")
    window = INDEX[a0:a0 + 1200]
    assert "addTypingBoy(node)" in window
    assert "addTypingBoy(fb)" in window


def test_boy_writer_css():
    assert ".boy-writer" in CSS
    assert "@keyframes boy-write" in CSS
    assert ".boy-writer.at-board" in CSS
    assert ".boy-writer.in-typing" in CSS
    # The board rail keeps step text clear of the boy.
    assert ".boy-host > ol.steps" in CSS
    assert ".bubble.typing.boy-host" in CSS
    w23 = CSS[CSS.index("Wave 23: Logo Jungle"):]
    assert ".boy-writer { animation: none" in w23  # reduced motion
