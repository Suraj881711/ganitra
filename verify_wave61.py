"""Wave 61 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (Suraj approved the 3D prototype going live:
"Ha bro, live kar do"):

The real-3D Logo Jungle from the verified prototype
(~/workspace/ganitra-3d-demo) now lives in the SAME slot the 2D
scenes have always used — #scene-stage in the chat empty state:

1. MODELS: the four Sketchfab models Suraj downloaded, under
   static/models/. The eagle (a 149.5 MB museum scan) was
   optimised to <= 20 MB WITHOUT decimation: textures 8192 ->
   2048 px, the orphaned spec-gloss texture dropped, geometry
   re-encoded with KHR_mesh_quantization (all 433,911 verts /
   149,853 tris kept; TANGENT dropped — three.js derives the
   tangent frame). Tiger/lion/boy ship byte-identical to the
   prototype's verified copies. Total payload <= 35 MB.
2. WIRING: static/scene3d.js (lazy ES module) + a bootstrap in
   index.html (idle callback + IntersectionObserver + reduced-
   motion refusal) + an import map for the vendored three.js.
   The 2D scene stays until ALL FOUR models load; only then
   does the stage gain .scene-3d-on. Any failure leaves the
   2D scene running, silently. Rendering pauses when hidden /
   off-screen and stops when the empty state is removed.
3. The logo on the 3D plaque is the app's own
   /static/logo-full-t.png, byte-for-byte the file it has
   always been (hashes asserted below).
4. Service worker: cache ganitra-static-v15; /static/models/
   bypasses the worker cache (HTTP cache + the ?v=61 pin in
   scene3d.js govern freshness). Stylesheet pin ?v=38.

No solver file changed; answer behaviour is untouched.

WAVE 62B ADDENDUM (15 Nov 2026, Suraj's final scene spec):
the scene this script verifies has since been re-scoped —
only the eagle performs, on the G itself (no plaque), and
the boy writer is the 2D sprite again. The model files, logo
files, pins and wiring asserted below are unchanged by 62B;
the §4 scene3d.js marker list was updated to the 62B markers
(the four-friends markers it replaces are named in the
comment there). Wave 62B's own assertions live in
verify_wave62b.py.

MERGE-4 (Waves 62B+63+64+65): the pin checks below were
reconciled to the merged pins — stylesheet ?v=38, cache
ganitra-static-v15 (Wave 64's Hindi-papers CSS is the newest).

Run:  python3 verify_wave61.py
"""

import hashlib
import json
import os
import struct
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave61-{RUN_ID}.db"

ROOT = Path(__file__).parent
MODELS = ROOT / "static" / "models"

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


def glb_json(path):
    data = path.read_bytes()
    assert data[:4] == b"glTF", f"{path} is not a GLB"
    jlen = struct.unpack("<I", data[12:16])[0]
    return data, json.loads(data[20:20 + jlen])


# --- 1. Model files: presence, sizes, integrity ----------------
print("== 1. Models in static/models ==")
CAPS = {"lion.glb": 10 * 10**6, "boy.glb": 10 * 10**6,
        "tiger.glb": 10 * 10**6, "eagle.glb": 20 * 10**6}
total = 0
for name, cap in CAPS.items():
    p = MODELS / name
    check(f"{name} present", p.exists())
    if not p.exists():
        continue
    size = p.stat().st_size
    total += size
    check(f"{name} within cap ({size/1e6:.2f} MB <= {cap/1e6:.0f} MB)",
          size <= cap)
    data, _ = glb_json(p)
    check(f"{name} is a valid GLB header", len(data) == size)
check(f"total payload <= 35 MB ({total/1e6:.2f} MB)", total <= 35 * 10**6)

# Prototype-identical copies (md5 recorded at build). Wave 62:
# lion/tiger hashes moved — each gained an authored WalkCycle
# clip appended at GLB level; model + original clip inside are
# byte-preserved (proof in ganitra-wave62-notes.md).
for name, want in [("lion.glb", "0d68ef98dfefa1647fd5d7426c9a4950"),
                   ("boy.glb", "0813eaf3b74561813caf397b6aafc66e"),
                   ("tiger.glb", "e125ebd2d1b9cf0c7489da200bc7f3a4")]:
    got = hashlib.md5((MODELS / name).read_bytes()).hexdigest()
    check(f"{name} byte-identical to the prototype copy", got == want, got)

# --- 2. The optimised eagle ------------------------------------
print("== 2. Optimised eagle ==")
_, eg = glb_json(MODELS / "eagle.glb")
check("eagle uses KHR_mesh_quantization",
      "KHR_mesh_quantization" in eg.get("extensionsRequired", []))
prim = eg["meshes"][0]["primitives"][0]
attrs = prim["attributes"]
check("eagle keeps POSITION/NORMAL/TEXCOORD_0",
      all(k in attrs for k in ("POSITION", "NORMAL", "TEXCOORD_0")))
check("eagle drops TANGENT (derived tangent frame)", "TANGENT" not in attrs)
pos_acc = eg["accessors"][attrs["POSITION"]]
check("eagle keeps every vertex (433911)",
      pos_acc["count"] == 433911, f"count={pos_acc['count']}")
idx_acc = eg["accessors"][prim["indices"]]
check("eagle keeps every triangle (149853)",
      idx_acc["count"] == 449559, f"count={idx_acc['count']}")
check("eagle has exactly 3 textures (orphan spec-gloss dropped)",
      len(eg["images"]) == 3, f"images={len(eg['images'])}")
mat = eg["materials"][0]
check("eagle PBR fix intact (metallic 0, roughness 0.9)",
      mat["pbrMetallicRoughness"]["metallicFactor"] == 0.0
      and mat["pbrMetallicRoughness"]["roughnessFactor"] == 0.9)
try:
    import io
    from PIL import Image
    data = (MODELS / "eagle.glb").read_bytes()
    bin_off = 20 + struct.unpack("<I", data[12:16])[0] + 8
    for ii, img in enumerate(eg["images"]):
        bv = eg["bufferViews"][img["bufferView"]]
        off = bin_off + bv.get("byteOffset", 0)
        im = Image.open(io.BytesIO(data[off:off + bv["byteLength"]]))
        check(f"eagle texture {ii} <= 2048px ({im.size})",
              max(im.size) <= 2048)
except ImportError:
    check("PIL available for texture check", False, "Pillow missing")

# --- 3. Logo files untouched ------------------------------------
print("== 3. Logo artwork untouched ==")
for name, want in [("logo-full-t.png", "15def831bc209625d6a9ce99a7e68587"),
                   ("logo-full.png", "8ffea6f4e42d3d3b1bd8552e26579c4c")]:
    p = ROOT / "static" / name
    got = hashlib.md5(p.read_bytes()).hexdigest()
    check(f"static/{name} hash unchanged", got == want, got)

# --- 4. Wiring in files ------------------------------------------
print("== 4. Scene wiring ==")
index = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
check("stage carries the 3D layer div", 'id="scene-3d"' in index)
check("2D fallback actors still in the stage",
      all(f'id="scene-{n}"' in index for n in ("eagle", "tiger", "boy")))
check("import map for vendored three.js",
      'type="importmap"' in index and "vendor/three.module.js" in index)
check("lazy bootstrap (idle + intersection + reduced motion)",
      "requestIdleCallback" in index and "IntersectionObserver" in index
      and 'import("/static/scene3d.js")' in index
      and "prefers-reduced-motion" in index)

s3d = (ROOT / "static" / "scene3d.js").read_text(encoding="utf-8")
# Wave 62B: the marker list tracks the CURRENT scene3d.js.
# Replaced Wave 61/62 markers: "logo-full-t.png" (the plaque
# texture — now the G-only "logo-g-t.png", and there is no
# plaque), "fitMode: 'skinned'" (the tiger's fit — he is
# parked, never loaded), "playTiger"/"playChase"/"playLion"
# (routines removed — eagle only) and "__ganitraBoyWriter3D"
# (the 3D writer, retired — the sprite writer serves again).
for marker in ["scene-3d-on", "/static/models/", "logo-g-t.png",
               "LOAD_WATCHDOG_MS", "Math.min(window.devicePixelRatio, 2)",
               "visibilitychange", "IntersectionObserver",
               "0.82919",           # eagle manual fit (quantised model)
               # the routines are the director's eagle scene now,
               # in its three rotating performances
               "playEagle", "playEaglePerch", "playEagleCarry",
               "playEagleKiss", "MutationObserver",
               "__sceneEagleOnly3D", "__friendsReady"]:
    check(f"scene3d.js: {marker}", marker in s3d)

css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
check("CSS: .scene-3d layer + .scene-3d-on swap",
      ".scene-3d {" in css and ".scene-stage.scene-3d-on" in css)
check("CSS: canvas is pointer-free (Wave 62 — no orbit; taps hit the stage)",
      "touch-action: pan-y" not in css and ".boy-writer-3d" in css)

sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
check("SW cache v13", 'GANITRA_CACHE = "ganitra-static-v15"' in sw)
check("SW bypasses /static/models/", '"/static/models/"' in sw)
base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
check("stylesheet pin ?v=38", "v='38'" in base)

for vend in ["vendor/three.module.js",
             "vendor/addons/loaders/GLTFLoader.js",
             "vendor/addons/utils/BufferGeometryUtils.js"]:
    check(f"vendored file present: {vend}",
          (ROOT / "static" / vend).exists())

# --- 5. Served pages ----------------------------------------------
print("== 5. Served chat page + statics ==")
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True
client = app.test_client()
r = client.post("/signup", data={
    "name": "W61 Scene " + RUN_ID, "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w61-test-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")
page = client.get("/").get_data(as_text=True)
check("served chat page has the 3D layer", 'id="scene-3d"' in page)
check("served chat page has the import map", "vendor/three.module.js" in page)
check("served chat page keeps the 2D stage", 'id="scene-stage"' in page)
check("served page pins stylesheet ?v=38", "style.css?v=38" in page)
for url in ["/static/scene3d.js", "/static/vendor/three.module.js",
            "/static/models/lion.glb", "/static/models/boy.glb",
            "/static/models/tiger.glb", "/static/models/eagle.glb"]:
    rr = client.get(url)
    check(f"GET {url} -> 200", rr.status_code == 200,
          f"status={rr.status_code}")

print(f"\nWave 61: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
