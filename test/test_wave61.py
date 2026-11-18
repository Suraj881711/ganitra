"""Wave 61: the 3D Logo Jungle goes live (Suraj: "Ha bro,
live kar do").

Pins: the four models in static/models/ with their size caps
and prototype-identical hashes; the optimised eagle's shape
(KHR_mesh_quantization, every vertex/triangle kept, PBR fix
intact, textures <= 2048px, orphan texture dropped); the logo
files' hashes (artwork never edited); the stage wiring (3D
layer div + import map + lazy bootstrap in the served chat
page, 2D fallback intact); scene3d.js's non-blocking markers;
the CSS swap rules; and the bumped delivery pins
(?v=43 / cache ganitra-static-v30 — merge-4 reconciled,
models bypass the SW).
"""
import hashlib
import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MODELS = ROOT / "static" / "models"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W61 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w61-test-pass"})
    return c


def _glb_json(path):
    data = path.read_bytes()
    assert data[:4] == b"glTF"
    jlen = struct.unpack("<I", data[12:16])[0]
    return data, json.loads(data[20:20 + jlen])


# --- models ------------------------------------------------------

@pytest.mark.parametrize("name,cap", [
    ("lion.glb", 10 * 10**6), ("boy.glb", 10 * 10**6),
    ("tiger.glb", 10 * 10**6), ("eagle.glb", 20 * 10**6),
])
def test_models_present_within_caps(name, cap):
    p = MODELS / name
    assert p.exists()
    assert p.stat().st_size <= cap
    _glb_json(p)   # parses as a GLB with a JSON chunk


def test_total_model_payload_within_35mb():
    total = sum((MODELS / n).stat().st_size
                for n in ("lion.glb", "boy.glb", "tiger.glb", "eagle.glb"))
    assert total <= 35 * 10**6


@pytest.mark.parametrize("name,want", [
    # Wave 62: lion/tiger gained the authored WalkCycle clip,
    # appended at GLB level — the model and the original clip
    # inside are byte-preserved; only the file hash moved.
    ("lion.glb", "0d68ef98dfefa1647fd5d7426c9a4950"),
    ("boy.glb", "0813eaf3b74561813caf397b6aafc66e"),
    ("tiger.glb", "e125ebd2d1b9cf0c7489da200bc7f3a4"),
])
def test_models_byte_identical_to_prototype(name, want):
    got = hashlib.md5((MODELS / name).read_bytes()).hexdigest()
    assert got == want


# --- the optimised eagle ------------------------------------------

def test_eagle_quantised_not_decimated():
    _, eg = _glb_json(MODELS / "eagle.glb")
    assert "KHR_mesh_quantization" in eg["extensionsRequired"]
    prim = eg["meshes"][0]["primitives"][0]
    attrs = prim["attributes"]
    assert eg["accessors"][attrs["POSITION"]]["count"] == 433911
    assert eg["accessors"][prim["indices"]]["count"] == 449559
    assert "TANGENT" not in attrs
    assert len(eg["images"]) == 3   # orphan spec-gloss texture dropped
    mat = eg["materials"][0]
    assert mat["pbrMetallicRoughness"]["metallicFactor"] == 0.0
    assert mat["pbrMetallicRoughness"]["roughnessFactor"] == 0.9


def test_eagle_textures_within_2048():
    import io
    from PIL import Image
    data, eg = _glb_json(MODELS / "eagle.glb")
    bin_off = 20 + struct.unpack("<I", data[12:16])[0] + 8
    for img in eg["images"]:
        bv = eg["bufferViews"][img["bufferView"]]
        off = bin_off + bv.get("byteOffset", 0)
        im = Image.open(io.BytesIO(data[off:off + bv["byteLength"]]))
        assert max(im.size) <= 2048


# --- logo integrity -------------------------------------------------

@pytest.mark.parametrize("name,want", [
    ("logo-full-t.png", "15def831bc209625d6a9ce99a7e68587"),
    ("logo-full.png", "8ffea6f4e42d3d3b1bd8552e26579c4c"),
])
def test_logo_files_untouched(name, want):
    got = hashlib.md5((ROOT / "static" / name).read_bytes()).hexdigest()
    assert got == want


# --- wiring ----------------------------------------------------------

def test_stage_wiring_in_template():
    index = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    assert 'id="scene-3d"' in index
    assert 'type="importmap"' in index
    assert "vendor/three.module.js" in index
    assert 'import("/static/scene3d.js")' in index
    assert "requestIdleCallback" in index
    # the 2D fallback is still fully present
    for n in ("eagle", "tiger", "boy"):
        assert f'id="scene-{n}"' in index


def test_scene3d_module_markers():
    s3d = (ROOT / "static" / "scene3d.js").read_text(encoding="utf-8")
    # Wave 62B: markers track the current module — "logo-full-t.png"
    # (plaque texture) -> "logo-g-t.png" (the G itself, no board);
    # playTiger/playChase/playLion and the 3D writer hook are gone
    # (eagle only; the writer is the sprite again).
    for marker in ("scene-3d-on", "/static/models/", "logo-g-t.png",
                   "LOAD_WATCHDOG_MS",
                   "Math.min(window.devicePixelRatio, 2)",
                   "visibilitychange", "IntersectionObserver",
                   "0.82919",
                   # the director's eagle scene, in three performances
                   "playEagle", "playEaglePerch", "playEagleCarry",
                   "playEagleKiss", "MutationObserver",
                   "__sceneEagleOnly3D", "__friendsReady"):
        assert marker in s3d, marker


def test_css_swap_rules():
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    assert ".scene-3d {" in css
    assert ".scene-stage.scene-3d-on" in css
    # Wave 62: no orbit — the layer never takes pointer events,
    # so the old pan-y touch rule is gone with it.
    assert "touch-action: pan-y" not in css
    assert ".boy-writer-3d" in css


def test_delivery_pins_wave61():
    base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
    sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
    assert "v='53'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v30"' in sw
    assert '"/static/models/"' in sw   # models bypass the worker cache


def test_vendored_three_present():
    for vend in ("vendor/three.module.js",
                 "vendor/addons/loaders/GLTFLoader.js",
                 "vendor/addons/utils/BufferGeometryUtils.js"):
        assert (ROOT / "static" / vend).exists()


# --- served page ------------------------------------------------------

def test_served_chat_page_carries_3d_layer(client):
    page = client.get("/").get_data(as_text=True)
    # Wave 70 (Suraj, 16 Nov 2026): the scene is PARKED — the
    # 3D layer and stage id are NOT served. The inert import
    # map stays in the head (nothing is fetched from it).
    assert 'id="scene-3d"' not in page
    assert 'id="scene-stage"' not in page
    assert "vendor/three.module.js" in page
    assert "style.css?v=53" in page


@pytest.mark.parametrize("url", [
    "/static/scene3d.js",
    "/static/vendor/three.module.js",
    "/static/models/lion.glb",
    "/static/models/boy.glb",
    "/static/models/tiger.glb",
    "/static/models/eagle.glb",
])
def test_statics_served(client, url):
    assert client.get(url).status_code == 200
