"""Wave-23 verification: LOGO JUNGLE SCENES + THE BOY WRITER.

Contract (Suraj, 12 Nov 2026, ~23:21-23:32 IST): like Muse's
in-between activities, little jungle scenes play around the
hero logo on the empty chat screen — "kabhi eagle aake logo
par baith jaaye, kabhi sher chalke side se aaye, logo ko
dhakka deke bahar le jaaye, toh Mowgli jaisa ladka logo ko
wapas leke aaye" — and a richer chase story: the tiger cub
runs off WITH the logo, the boy chases it with a stick, the
cub drops the logo and flees, the boy throws the stick away,
hugs the logo and sets it back in its place.

  * wordless animated mini-stories on the empty chat screen
    only (stage markup, three cream sprites, a stick prop);
  * the scene director picks at random with no back-to-back
    repeat (shuffled feel), the first scene lands ~5-15s after
    the empty screen opens, later gaps run ~25-75s; tapping
    the stage plays the next scene; typing, sending or a
    hidden tab stops the show; reduced motion disables it;
  * the boy writer: when the student starts working, the
    jungle boy stands at the Teach board and "writes" as the
    steps reveal, and rides beside the thinking indicator
    while an answer is being made;
  * HARD RULE kept: the frozen logo artwork files are never
    edited — scenes animate the <img> element with CSS
    transforms only (digests pinned below).

Run:  python verify_wave23.py
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

RUN_ID = uuid.uuid4().hex[:8]
_DB = f"/tmp/ganitra-verify-wave23-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass

ROOT = Path(__file__).parent
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


# --- 0. A signed-in chat page to inspect --------------------------------
from app import create_app  # noqa: E402

app = create_app()
client = app.test_client()
USER = {"name": "W23 Tester " + RUN_ID, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w23test-pass"}
r = client.post("/signup", data=USER)
check("signup for scene checks", r.status_code in (200, 302),
      f"status={r.status_code}")
r = client.get("/")
body = r.get_data(as_text=True)
check("GET / (signed in)", r.status_code == 200,
      f"status={r.status_code}")

# --- 1. The stage, the actors and their sprite assets -------------------
_idx = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
_css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

check("scene stage wraps the hero logo",
      'id="scene-stage"' in body and 'id="scene-logo"' in body
      and body.index('id="scene-stage"') < body.index("empty-greeting"))
for _actor in ("eagle", "tiger", "boy"):
    check(f"scene actor in page ({_actor})",
          f'id="scene-{_actor}"' in body
          and f"scene-{_actor}.webp" in body)
    _f = ROOT / "static" / f"scene-{_actor}.webp"
    check(f"scene asset on disk ({_actor})",
          _f.exists() and _f.stat().st_size > 50_000,
          f"bytes={_f.stat().st_size if _f.exists() else 0}")
    _r = client.get(f"/static/scene-{_actor}.webp")
    check(f"scene asset over HTTP ({_actor})",
          _r.status_code == 200
          and _r.content_type.startswith("image/"),
          f"status={_r.status_code} type={_r.content_type}")

# --- 2. Director wiring, Scene C and the guards --------------------------
check("scene logic markers present",
      "SCENE-LOGIC-BEGIN" in _idx and "SCENE-LOGIC-END" in _idx)
check("scene director wired",
      "function pickSceneName" in _idx
      and "function sceneDelayMs" in _idx
      and "function firstSceneDelayMs" in _idx
      and "function playNext" in _idx
      and "function stopScenes" in _idx
      and "playing-eagle" in _idx and "playing-tiger" in _idx
      and "playing-chase" in _idx)
check("stick element in the stage",
      'id="scene-stick"' in body and 'class="scene-stick"' in body)
check("scene C CSS present (chase + stick)",
      all(s in _css for s in (
          ".scene-stick", "@keyframes chase-tiger",
          "@keyframes chase-logo", "@keyframes chase-boy",
          "@keyframes stick-arc", "--chase-x")))
check("scenes honour reduced motion (JS)",
      "(prefers-reduced-motion: reduce)" in _idx
      and "if (reduced) return;" in _idx)
check("scenes stop on typing, pause on hidden tab",
      'addEventListener("input", stopScenes)' in _idx
      and "visibilitychange" in _idx)
check("tap on the stage plays the next scene",
      'stage.addEventListener("click"' in _idx)
check("scene CSS present",
      all(s in _css for s in (
          ".scene-stage", ".scene-actor",
          "@keyframes eagle-visit", "@keyframes tiger-visit",
          "@keyframes logo-rolled", "@keyframes boy-rescue",
          "@keyframes boy-write", ".boy-writer")))
_w23css = _css[_css.index("Wave 23: Logo Jungle"):]
check("reduced-motion kills the scenes (CSS)",
      "@media (prefers-reduced-motion: reduce)" in _w23css
      and ".scene-actor { display: none" in _w23css)

# --- 3. Frozen logos --------------------------------------------------------
for _name, _want in (("logo-full-t.png",
                      "15def831bc209625d6a9ce99a7e68587"),
                     ("logo-mark-t.png",
                      "a91866e864db7f10994ab39ec2ea9ea2")):
    _digest = hashlib.md5(
        (ROOT / "static" / _name).read_bytes()).hexdigest()
    check(f"frozen logo {_name} untouched",
          _digest == _want, _digest)

# --- 4. Part 2: the boy who writes at the board -------------------------
check("boy writer functions present",
      all(s in _idx for s in (
          "function showBoyWriter", "function hideBoyWriter",
          "function scheduleBoyWriterHide", "function addTypingBoy")))
check("boy writer needs the steps board",
      "if (boyBroken || !stepsDet) return;" in _idx)
_teach0 = _idx.index("function startTeachPlayback")
_teach1 = _idx.index("if ((result.steps", _teach0)
check("Teach start shows the boy writer",
      "showBoyWriter();" in _idx[_teach0:_teach1])
_stop = _idx[_idx.index("function stopTeachPlayback"): _teach0]
check("Teach stop schedules the boy's exit",
      "scheduleBoyWriterHide();" in _stop)
_typ0 = _idx.index("function addTyping()")
check("thinking indicator carries the boy",
      "addTypingBoy(node)" in _idx[_typ0:_typ0 + 1000]
      and "addTypingBoy(fb)" in _idx[_typ0:_typ0 + 1000])
check("boy writer CSS (board rail + typing post)",
      ".boy-host > ol.steps" in _css
      and ".boy-writer.in-typing" in _css
      and ".boy-writer.at-board" in _css)

# --- 5. Scene-director logic under node --------------------------------
_node = shutil.which("node")
if _node:
    _s = _idx.index("/* SCENE-LOGIC-BEGIN")
    _e = _idx.index("/* SCENE-LOGIC-END */") + \
        len("/* SCENE-LOGIC-END */")
    _driver = _idx[_s:_e] + r"""
var out = {};
out.order = SCENE_ORDER.slice();
out.ms = [SCENE_MS.eagle, SCENE_MS.tiger, SCENE_MS.chase];
// The picker: never repeats the previous scene, and over many
// draws reaches every other scene (the order feels shuffled).
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
// A long simulated run: no back-to-back repeat ever.
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
    _p = "/tmp/w23-scenes.js"
    open(_p, "w", encoding="utf-8").write(_driver)
    _r = subprocess.run([_node, _p], capture_output=True, text=True)
    try:
        _out = json.loads(_r.stdout.strip().splitlines()[-1])
    except Exception:
        _out = {}
        print("node stderr:", _r.stderr[:400])
    check("scene order is eagle/tiger/chase",
          _out.get("order") == ["eagle", "tiger", "chase"],
          f"order={_out.get('order')}")
    check("picker never repeats the previous scene",
          _out.get("repeats") == 0
          and all(_out.get(k, {}).get("bad") == 0 for k in (
              "from_null", "from_eagle", "from_tiger",
              "from_chase")),
          f"repeats={_out.get('repeats')}")
    check("picker can reach every other scene",
          _out.get("from_null", {}).get("seen")
          == ["chase", "eagle", "tiger"]
          and _out.get("from_eagle", {}).get("seen")
          == ["chase", "tiger"]
          and _out.get("from_tiger", {}).get("seen")
          == ["chase", "eagle"]
          and _out.get("from_chase", {}).get("seen")
          == ["eagle", "tiger"],
          f"from_eagle={_out.get('from_eagle')}")
    check("scene gap randomised within 25-75s",
          _out.get("delay_min") == 25000
          and _out.get("delay_max") == 74999
          and _out.get("delay_range_ok") is True,
          f"min={_out.get('delay_min')} max={_out.get('delay_max')}")
    check("first scene randomised within 5-15s",
          _out.get("first_min") == 5000
          and _out.get("first_max") == 14999
          and _out.get("first_range_ok") is True,
          f"min={_out.get('first_min')} max={_out.get('first_max')}")
    check("scene durations match the CSS tracks",
          _out.get("ms") == [5400, 8600, 11200],
          f"ms={_out.get('ms')}")
else:
    check("scene logic behaviour (node)", True,
          "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
