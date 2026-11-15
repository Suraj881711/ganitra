"""Wave 62B verification (15 Nov 2026).

WHAT THIS WAVE CHANGED (Suraj's FINAL scene spec, given
15:57-16:15 IST on 15 Nov 2026, on top of Wave 62):

1. EAGLE ONLY — "abhi saare 3d model chodo bs eagle kaa
   rakho": static/scene3d.js loads ONLY the eagle model.
   The tiger/lion/boy .glb files stay in the tree (parked,
   byte-identical, WalkCycle clips intact) but are never
   requested by the page. On activation the module marks
   tiger/boy/lion broken with the director and sets
   window.__sceneEagleOnly3D, so the performed rotation is
   the eagle's scene alone (the director's pickSceneName
   consults the flag only when the no-repeat rule would
   empty the pool; a pure-2D visit is untouched).
2. NO BOARD — "aise board mai nhi karana, pahale ki tarah
   same karana hai": the wooden plaque/frame is GONE. Like
   the old 2D scene, the LOGO ITSELF is the object: the
   eagle perches directly on the G, grips the G itself for
   the carry, kisses the G itself.
3. G ONLY — "jo ganitra kaa logo hai G bas wahi hona
   chahiye, logo ke naam ke sath kuch nhi karana hai": the
   scene texture is /static/logo-g-t.png — the G glyph
   cropped from Suraj's frozen original artwork
   (~/workspace/your_files/Ganitra_Logo_Frozen_Original.png,
   md5 87bf145e...), crop box (597,166)-(1293,798) around
   the measured glyph bbox (x 627-1262, y 196-785). Its RGB
   pixels are asserted byte-identical to that region of the
   original below; only the paper background was keyed to
   alpha (flood-fill from the borders + a 1.1px alpha
   feather) so the mark stands alone — the same treatment
   the app's own logo-full-t.png carries. No redraw, no
   recolour, no regeneration. The full frozen logo
   everywhere else on the site is untouched.
4. ACTIVITIES (the director's 4.4s eagle slot, rotating):
   PERCH (the classic: swoop in, perch on the G, bob, off),
   CARRY (grip the G with the talons, lift off carrying it,
   fly it across, set it back down gently from the other
   side, re-perch), KISS (lean down, a beak-touch kiss on
   the G with a small heart pop, a soft nuzzle, off).
5. BOY WRITER: the pre-61 2D sprite again — scene3d.js
   never defines window.__ganitraBoyWriter3D, so Teach /
   thinking use scene-boy.webp exactly as before.

No solver file changed; pins unchanged (?v=35 /
ganitra-static-v12; model pin ?v=62 — eagle.glb is the
same file Wave 62 shipped).

MERGE-4 (Waves 62B+63+64+65): the pin checks in §5 assert
the merged pins — stylesheet ?v=38, cache ganitra-static-v15
(Wave 64's Hindi-papers CSS is the newest). Model pin ?v=62
unchanged.

Run:  python3 verify_wave62b.py
"""

import hashlib
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave62b-{RUN_ID}.db"

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

# --- 1. Eagle only ------------------------------------------------
print("== 1. Only the eagle loads ==")
check("scene3d.js loads the eagle (loadEagle kick-off)",
      "loadEagle();" in s3d)
check("no generic multi-model loader remains", "loadActor" not in s3d)
for name in ("tiger", "lion", "boy"):
    check(f"scene3d.js never requests the {name} model",
          f"modelURL('{name}')" not in s3d
          and f"models/{name}.glb" not in s3d)
check("activation reports the eagle as the only actor",
      "actors: ['eagle']" in s3d)
check("activation marks tiger/boy/lion broken, eagle unbroken",
      "__sceneSetBroken('tiger', true)" in s3d
      and "__sceneSetBroken('boy', true)" in s3d
      and "__sceneSetBroken('lion', true)" in s3d
      and "__sceneSetBroken('eagle', false)" in s3d)
check("activation sets the director's eagle-only flag",
      "window.__sceneEagleOnly3D = true" in s3d)
check("director consults the flag in pickSceneName (62B gate)",
      "window.__sceneEagleOnly3D" in index
      and "function pickSceneName" in index)
check("director's 2D rule itself unchanged (excludes prev)",
      "n !== prev" in index)
for name, want in [("tiger.glb", "e125ebd2d1b9cf0c7489da200bc7f3a4"),
                   ("lion.glb", "0d68ef98dfefa1647fd5d7426c9a4950"),
                   ("boy.glb", "0813eaf3b74561813caf397b6aafc66e"),
                   ("eagle.glb", "e183b7f20d421573fd24181d4655503b")]:
    p = ROOT / "static" / "models" / name
    got = hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "MISSING"
    check(f"parked file intact: static/models/{name}", got == want, got)

# --- 2. No board; the G itself -------------------------------------
print("== 2. The G itself is the object (no board) ==")
check("scene texture is the G-only file", "/static/logo-g-t.png" in s3d)
check("the full-logo texture left the 3D scene",
      "/static/logo-full-t.png" not in s3d)
check("no box geometry (the wooden frame + feet are gone)",
      "BoxGeometry" not in s3d)
check("no stick, no other actors' props", "stick" not in s3d.lower())

from PIL import Image
import numpy as np

gtex = Image.open(ROOT / "static" / "logo-g-t.png")
check("logo-g-t.png is RGBA, 696x632 (the crop box)",
      gtex.mode == "RGBA" and gtex.size == (696, 632),
      f"{gtex.mode} {gtex.size}")
ga = np.asarray(gtex)
check("paper keyed away (corners fully transparent)",
      ga[0, 0, 3] == 0 and ga[0, -1, 3] == 0
      and ga[-1, 0, 3] == 0 and ga[-1, -1, 3] == 0)
rows = (ga[:, :, 3] > 128).sum(axis=1)
filled = [i for i, r in enumerate(rows) if r > 0]
check("glyph is a single band — the name text is NOT in the texture",
      filled == list(range(filled[0], filled[-1] + 1))
      and filled[-1] - filled[0] < 600,
      f"band {filled[0]}..{filled[-1]}")

frozen_path = Path.home() / "workspace" / "your_files" / \
    "Ganitra_Logo_Frozen_Original.png"
if frozen_path.exists():
    raw = frozen_path.read_bytes()
    check("frozen original is the known file (md5 87bf145e...)",
          hashlib.md5(raw).hexdigest()
          == "87bf145e4add2c099dd17bd2c2ab47fd")
    frozen = Image.open(frozen_path).convert("RGB")
    region = np.asarray(frozen)[166:798, 597:1293]
    check("texture RGB is byte-identical to the frozen crop region",
          bool((ga[:, :, :3].astype(int) == region.astype(int)).all()))
else:
    check("frozen original found for the provenance check", False,
          str(frozen_path))

# --- 3. The eagle's activities --------------------------------------
print("== 3. Perch / carry / kiss in the old 4.4s slot ==")
for fn in ("playEaglePerch", "playEagleCarry", "playEagleKiss",
           "playEagle"):
    check(f"routine {fn}", f"function {fn}" in s3d)
check("variants rotate (EAGLE_VARIANTS)", "EAGLE_VARIANTS" in s3d)
check("carry pins the G to the talons", "pinLogoToTalons" in s3d)
check("kiss heart pop (canvas heart sprite)",
      "CanvasTexture" in s3d and "heart" in s3d)
check("routines still driven by the director's classes",
      "MutationObserver" in s3d and "sceneFromClass" in s3d)
check("director's eagle duration unchanged (4400ms)",
      "eagle: 4400" in index)

# --- 4. Boy writer: the sprite again ---------------------------------
print("== 4. Boy writer ==")
check("scene3d.js does not define the 3D writer hook",
      "__ganitraBoyWriter3D" not in s3d)
check("sprite writer paths intact in index.html",
      'boyWriter.src = "/static/scene-boy.webp?v=29"' in index
      and 'boy.src = "/static/scene-boy.webp?v=29"' in index)

# --- 5. Pins ----------------------------------------------------------
print("== 5. Pins (merge-4 reconciled) ==")
check("stylesheet pin ?v=38", "v='38'" in base)
check("SW cache ganitra-static-v15",
      'GANITRA_CACHE = "ganitra-static-v15"' in sw)
check("model pin ?v=62 (eagle.glb unchanged)", "MODEL_V = '62'" in s3d)

# --- 6. Served page ----------------------------------------------------
print("== 6. Served chat page ==")
from app import create_app
app = create_app()
app.config["TESTING"] = True
c = app.test_client()
r = c.post("/signup", data={
    "name": "W62B Verify Tester", "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Football",
    "favourite": "Mango", "password": "w62b-verify-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")
page = c.get("/").get_data(as_text=True)
check("served page carries the stage + 3D layer",
      'id="scene-stage"' in page and 'id="scene-3d"' in page)
check("served page carries the eagle-only director gate",
      "__sceneEagleOnly3D" in page)
check("served page pins stylesheet ?v=38", "style.css?v=38" in page)
for url in ("/static/scene3d.js", "/static/logo-g-t.png",
            "/static/models/eagle.glb", "/static/models/tiger.glb",
            "/static/models/lion.glb", "/static/models/boy.glb",
            "/static/scene-boy.webp"):
    rr = c.get(url)
    check(f"GET {url} -> 200", rr.status_code == 200,
          f"status={rr.status_code}")

print(f"\nWave 62B: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
