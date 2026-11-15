"""Wave 62 verification (15 Nov 2026).

WHAT THIS WAVE CHANGED (Suraj's verdict on Wave 61: "3d kaa
aisa nhi chahiye sab pahale kaa hi but dosto ko change karana
hai but activity pahali ki tarah karani hai" — the old scene
system and its activities back, the cast swapped to the real
3D models; and "pairo se chal nhi rahe, khisak rahe hai" —
motion must read as real):

1. PRESENTATION REVERTED: Wave 61's free-orbit clearing is
   gone — no orbit controls, no auto-rotate, no always-on
   standing scene, no tap buttons, no status lines. The Wave
   23-28 scene director in templates/index.html is again the
   ONLY scene system: same slot, same schedule (first scene
   ~2-4s after every load, gaps ~25-75s, shuffled, no
   back-to-back repeat, tap-to-play, stop on typing, hidden-
   tab pause, reduced-motion off).
2. THE CAST IS 3D: static/scene3d.js watches the director's
   .playing-* classes and performs the same scenes with the
   four real models at the old durations (eagle 4.4s, tiger
   6.9s, chase 9.0s) — fixed camera, transparent stage, the
   frozen-logo plaque at centre, actors visible only during
   their scene. The lion joins the rotation with a new scene
   in the old grammar (6.9s); the director keeps him "broken"
   until the 3D layer activates (__sceneSetBroken).
3. THE BOY WRITER IS 3D TOO: window.__ganitraBoyWriter3D
   hands Teach / thinking a canvas painted from an offscreen
   render of the boy doing the same writing rock; the 2D
   sprite writer remains the fallback.
4. FALLBACK INTACT: until all four models load — and forever
   on any failure — the 2D jungle runs exactly as before.
   Canvas is pointer-events:none; composer and cards are
   untouched. Pins: stylesheet ?v=35, cache ganitra-static-v12.
   (Merge-4: the pin checks below assert the merged pins —
   stylesheet ?v=37, cache ganitra-static-v14, Wave 64's CSS
   being the newest.)

CLIP AUDIT + WALK AUTHORING (measured, see
ganitra-wave62-notes.md): neither shipped cat clip contains a
walk cycle — the tiger's 39.04s clip is an in-place standing
performance (max foot lift ~1.9 units), the lion's 2.97s clip
a breathing idle (feet static). Per Suraj's decision ("Safed
tiger par hi asli walk bana do"), a real trot was authored on
each cat's own rig in Blender and appended to its .glb as a
"WalkCycle" clip (GLB-level append: model + original clip
byte-preserved — the original clips' durations are asserted
below). scene3d.js crossfades travelling cats into WalkCycle
at ground-speed-matched playback. The eagle is a static scan
and the boy has no rig: their moves stay short, as before.

No solver file changed; answer behaviour is untouched.

WAVE 62B ADDENDUM (15 Nov 2026, Suraj's FINAL scene spec —
"abhi saare 3d model chodo bs eagle kaa rakho", "aise board
mai nhi karana", "logo hai G bas wahi hona chahiye"): the 3D
scene now performs ONLY the eagle, on the G itself (no
plaque/board), in three rotating performances (perch /
carry / kiss); the tiger/lion/boy models are parked (files
kept, never loaded); the boy writer is the 2D sprite again.
Sections 2, 4 and 4b below were updated to that spec — each
change is commented where it happens. The director (§1),
the fallback, the pins and the parked model files (§4b/§5)
are asserted exactly as before. Wave 62B's own assertions
live in verify_wave62b.py.

Run:  python3 verify_wave62.py
"""

import hashlib
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave62-{RUN_ID}.db"

ROOT = Path(__file__).parent

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


index = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
s3d = (ROOT / "static" / "scene3d.js").read_text(encoding="utf-8")
css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")

# --- 1. The old director: triggers, schedule, rotation --------
print("== 1. The Wave 23 director, restored as the only system ==")
check("director logic block present",
      "/* SCENE-LOGIC-BEGIN */" in index and "/* SCENE-LOGIC-END */" in index)
check("rotation is eagle/tiger/chase/lion",
      'SCENE_ORDER = ["eagle", "tiger", "chase", "lion"]' in index)
check("durations: eagle 4400, tiger 6900, chase 9000, lion 6900",
      "eagle: 4400" in index and "tiger: 6900" in index
      and "chase: 9000" in index and "lion: 6900" in index)
check("first scene ~2-4s (firstSceneDelayMs 2000 + <2000)",
      "function firstSceneDelayMs" in index and "2000 + Math.floor" in index)
check("later gaps ~25-75s (sceneDelayMs 25000 + <50000)",
      "function sceneDelayMs" in index and "25000 + Math.floor" in index)
check("no back-to-back repeat (pickSceneName excludes prev)",
      "function pickSceneName" in index and "n !== prev" in index)
check("tap-to-play on the stage",
      'stage.addEventListener("click"' in index)
check("scenes stop when the student types",
      'addEventListener("input", stopScenes)' in index)
check("hidden tab pauses (visibilitychange + resetStage)",
      "visibilitychange" in index and "resetStage()" in index)
check("reduced motion: director refuses",
      "(prefers-reduced-motion: reduce)" in index and "if (reduced) return;" in index)
check("first scene owed until played (firstPending)",
      "firstPending" in index and "schedule(firstPending)" in index)
check("lion starts broken (3D-only scene)",
      "broken.lion = true;" in index)
check("director exposes __sceneSetBroken for the 3D layer",
      "window.__sceneSetBroken" in index)
check("2D sprites + stick still in the stage (the fallback)",
      all(f'id="scene-{n}"' in index for n in ("eagle", "tiger", "boy"))
      and 'id="scene-stick"' in index)
check("2D scene CSS tracks intact (eagle-visit / tiger-visit / chase)",
      all(k in css for k in ("eagle-visit", "tiger-visit", "boy-rescue",
                             "chase-tiger", "chase-logo", "chase-boy",
                             "stick-arc")))

# --- 2. The 3D layer performs the director's scenes -----------
print("== 2. scene3d.js: the old scenes, performed in 3D ==")
# Wave 62B: the performed rotation is the eagle's scene alone,
# in three rotating performances. The tiger/chase/lion
# routines were removed (their models are parked, §4b).
for fn in ("playEagle", "playEaglePerch", "playEagleCarry",
           "playEagleKiss"):
    check(f"routine {fn}", f"function {fn}" in s3d)
for fn in ("playTiger", "playChase", "playLion"):
    check(f"routine removed in 62B: {fn}", f"function {fn}" not in s3d)
check("routines driven by the stage classes (MutationObserver)",
      "MutationObserver" in s3d and "playing-" in s3d
      and "sceneFromClass" in s3d)
check("activation marks the others broken, eagle unbroken (62B)",
      "__sceneSetBroken" in s3d and "__sceneSetBroken('lion', true)" in s3d
      and "__sceneSetBroken('tiger', true)" in s3d
      and "__sceneSetBroken('boy', true)" in s3d
      and "__sceneSetBroken('eagle', false)" in s3d
      and "__sceneEagleOnly3D" in s3d)
check("activation swaps the stage (.scene-3d-on) + hooks",
      "scene-3d-on" in s3d and "__friendsReady" in s3d
      and "mode: 'oldscene'" in s3d)
check("actors hidden until their scene (group.visible = false at load)",
      "group.visible = false" in s3d)
# Wave 62B: no plaque/board — the object is the G itself.
check("the G itself is the scene object (logo-g-t.png, no board)",
      "/static/logo-g-t.png" in s3d and "/static/logo-full-t.png" not in s3d
      and "BoxGeometry" not in s3d)
check("lazy + watchdog + DPR cap (non-blocking contract)",
      "LOAD_WATCHDOG_MS" in s3d
      and "Math.min(window.devicePixelRatio, 2)" in s3d)
check("rendering pauses hidden / off-screen",
      "visibilitychange" in s3d and "IntersectionObserver" in s3d)

# --- 3. Wave 61 presentation is GONE ---------------------------
print("== 3. Removed Wave 61 behaviours ==")
for gone in ("OrbitControls", "autoOrbit", "azGoal", "polGoal",
             "playRandom", "idleScheduler", "tapReact", "setStatus",
             "btn-lion", "btn-boy", "btn-eagle", "btn-tiger",
             "logoWobble", "eagleSwoop", "boyCarry", "LOGO_SPOTS",
             "makeTree", "MOTES"):
    check(f"absent from scene3d.js: {gone}", gone not in s3d)
check("CSS: no pan-y orbit touch rule", "touch-action: pan-y" not in css)
on_block = css.split(".scene-stage.scene-3d-on .scene-3d {", 1)[1].split("}", 1)[0]
check("CSS: the on-state does not take pointer events",
      "pointer-events" not in on_block and "opacity: 1" in on_block)
check("CSS: layer is pointer-events:none",
      ".scene-3d {" in css and "pointer-events: none" in css)

# --- 4. The boy writer -----------------------------------------
print("== 4. Boy writer: the 2D sprite again (Wave 62B) ==")
# Wave 62B: the boy is out of the 3D scene, so the 3D writer
# is retired — scene3d.js must NOT define the hook, and the
# Teach / thinking code falls back to the sprite exactly as
# it did pre-61. (The preference code in index.html stays;
# with no hook defined it always takes the sprite path.)
check("scene3d.js does NOT define the 3D writer hook (62B)",
      "__ganitraBoyWriter3D" not in s3d and "initWriter" not in s3d)
check("Teach writer preference code still falls back to the sprite",
      index.count("__ganitraBoyWriter3D") >= 2
      and "boy-writer at-board boy-writer-3d" in index)
check("thinking writer preference code still in place",
      "boy-writer in-typing on boy-writer-3d" in index)
check("sprite writer fallback intact",
      'boyWriter.src = "/static/scene-boy.webp?v=29"' in index
      and 'boy.src = "/static/scene-boy.webp?v=29"' in index)
check("CSS: .boy-writer-3d kills the element-level rock only",
      ".boy-writer-3d { animation: none !important; }" in css
      and "@keyframes boy-write" in css)

# --- 4b. Locomotion: authored WalkCycle clips -------------------
print("== 4b. Locomotion: the cats' authored WalkCycle ==")
import json as _json
import struct as _struct


def _anims(name):
    data = (ROOT / "static" / "models" / name).read_bytes()
    jlen = _struct.unpack("<I", data[12:16])[0]
    g = _json.loads(data[20:20 + jlen])
    out = {}
    for a in g.get("animations", []):
        mx = 0.0
        for ch in a["channels"]:
            acc = g["accessors"][a["samplers"][ch["sampler"]]["input"]]
            mx = max(mx, acc["max"][0])
        out[a.get("name")] = round(mx, 2)
    return out


_t = _anims("tiger.glb")
check("tiger.glb: original clip intact (Animation, 39.04s)",
      _t.get("Animation") == 39.04)
check("tiger.glb: WalkCycle appended (1.0s)", _t.get("WalkCycle") == 1.0)
_l = _anims("lion.glb")
check("lion.glb: original clip intact (GltfAnimation 0, 2.97s)",
      _l.get("GltfAnimation 0") == 2.97)
check("lion.glb: WalkCycle appended (1.0s)", _l.get("WalkCycle") == 1.0)
# Wave 62B: the cats are parked — their files (with the
# authored WalkCycle, asserted just above) stay in the tree,
# but scene3d.js no longer loads or wires them.
check("parked in 62B: scene3d.js does not load the cats/boy",
      all(m not in s3d for m in ("loadActor('tiger')", "loadActor('lion')",
                                 "loadActor('boy')", "walkStride",
                                 "WalkCycle")))

# --- 5. Pins + logo integrity ----------------------------------
print("== 5. Pins and the frozen logo ==")
check("stylesheet pin ?v=37", "v='37'" in base)
check("SW cache ganitra-static-v14",
      'GANITRA_CACHE = "ganitra-static-v14"' in sw)
check("SW still bypasses /static/models/", '"/static/models/"' in sw)
for name, want in [("logo-full-t.png", "15def831bc209625d6a9ce99a7e68587"),
                   ("logo-full.png", "8ffea6f4e42d3d3b1bd8552e26579c4c")]:
    got = hashlib.md5((ROOT / "static" / name).read_bytes()).hexdigest()
    check(f"static/{name} hash unchanged", got == want, got)
check("static/logo-g-t.png exists (the G-only scene texture, 62B)",
      (ROOT / "static" / "logo-g-t.png").exists())

# --- 6. Served page ---------------------------------------------
print("== 6. Served chat page ==")
from app import create_app
app = create_app()
app.config["TESTING"] = True
c = app.test_client()
r = c.post("/signup", data={
    "name": "W62 Verify Tester", "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Football",
    "favourite": "Mango", "password": "w62-verify-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")
page = c.get("/").get_data(as_text=True)
check("served page carries the director (lion in rotation)",
      'SCENE_ORDER = ["eagle", "tiger", "chase", "lion"]' in page)
check("served page carries the 3D layer + stage",
      'id="scene-3d"' in page and 'id="scene-stage"' in page)
check("served page carries the writer hook",
      "__ganitraBoyWriter3D" in page)
check("served page pins stylesheet ?v=37", "style.css?v=37" in page)
for url in ("/static/scene3d.js", "/static/models/lion.glb",
            "/static/models/boy.glb", "/static/models/tiger.glb",
            "/static/models/eagle.glb", "/static/scene-boy.webp"):
    rr = c.get(url)
    check(f"GET {url} -> 200", rr.status_code == 200,
          f"status={rr.status_code}")

print(f"\nWave 62: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
