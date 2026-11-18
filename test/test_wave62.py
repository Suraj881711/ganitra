"""Wave 62: the OLD scene system, performed by the real 3D cast.

Suraj rejected Wave 61's free-orbit clearing ("sab pahale kaa
hi but dosto ko change karana hai but activity pahali ki tarah
karani hai") and demanded motion that reads as real ("pairo se
chal nhi rahe, khisak rahe hai"). This suite pins: the Wave 23
director restored as the only scheduler (rotation now incl.
the lion, gated on 3D activation); scene3d.js performing the
director's scenes (no orbit / no idle wander / no tap buttons);
the 3D boy writer with the sprite fallback; the 2D fallback
intact; and the bumped pins (?v=35 / ganitra-static-v12;
merge-4 reconciled them to ?v=43 / ganitra-static-v30).

Wave 62B update (Suraj's final spec, same day): the 3D scene
performs ONLY the eagle — perch / carry / kiss on the G
itself, no board — the cats' and boy's models are parked
(files kept, WalkCycle clips intact, never loaded), and the
boy writer is the 2D sprite again. The tests below that
pinned the four-friends 3D layer were updated to match;
the director, fallback and pins tests are unchanged.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
S3D = (ROOT / "static" / "scene3d.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W62 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w62-test-pass"})
    return c


# --- the director ------------------------------------------------

def test_director_rotation_includes_lion():
    assert 'SCENE_ORDER = ["eagle", "tiger", "chase", "lion"]' in INDEX
    assert "lion: 6900" in INDEX
    # the old three keep their exact durations
    assert "eagle: 4400" in INDEX and "tiger: 6900" in INDEX
    assert "chase: 9000" in INDEX


def test_director_triggers_unchanged():
    for marker in ("function firstSceneDelayMs", "function sceneDelayMs",
                   "function pickSceneName", "schedule(true)",
                   'stage.addEventListener("click"',
                   'addEventListener("input", stopScenes)',
                   "firstPending", "if (reduced) return;"):
        assert marker in INDEX, marker


def test_lion_gated_on_3d_activation():
    # no 2D lion sprite exists: he starts out of the rotation
    assert "broken.lion = true;" in INDEX
    assert "window.__sceneSetBroken" in INDEX
    assert 'lion: ["lion", "boy"]' in INDEX


# --- scene3d.js performs the director's scenes --------------------

def test_scene3d_routines_match_the_old_scenes():
    # Wave 62B: the eagle's scene is the only 3D performance,
    # in its three rotating variants; the other routines are
    # gone with their (parked) models.
    for fn in ("playEagle", "playEaglePerch", "playEagleCarry",
               "playEagleKiss"):
        assert f"function {fn}" in S3D, fn
    for fn in ("playTiger", "playChase", "playLion"):
        assert f"function {fn}" not in S3D, fn
    assert "MutationObserver" in S3D
    assert "sceneFromClass" in S3D
    assert "group.visible = false" in S3D   # nobody stands around
    assert "mode: 'oldscene'" in S3D


def test_wave61_presentation_removed():
    for gone in ("OrbitControls", "autoOrbit", "azGoal", "playRandom",
                 "idleScheduler", "tapReact", "setStatus", "logoWobble",
                 "eagleSwoop", "boyCarry", "LOGO_SPOTS", "makeTree",
                 "MOTES", "btn-lion"):
        assert gone not in S3D, gone
    assert "touch-action: pan-y" not in CSS
    on_block = CSS.split(".scene-stage.scene-3d-on .scene-3d {", 1)[1]
    on_block = on_block.split("}", 1)[0]
    assert "pointer-events" not in on_block


# --- the boy writer ------------------------------------------------

def test_boy_writer_prefers_3d_canvas():
    # Wave 62B: the 3D writer is retired — scene3d.js must not
    # define the hook, so the preference code in index.html
    # always lands on the 2D sprite (the pre-61 behaviour).
    assert INDEX.count("__ganitraBoyWriter3D") >= 2
    assert "boy-writer at-board boy-writer-3d" in INDEX
    assert "boy-writer in-typing on boy-writer-3d" in INDEX
    assert "__ganitraBoyWriter3D" not in S3D
    assert "writerPivot" not in S3D


def test_boy_writer_sprite_fallback_intact():
    assert 'boyWriter.src = "/static/scene-boy.webp?v=29"' in INDEX
    assert 'boy.src = "/static/scene-boy.webp?v=29"' in INDEX
    assert ".boy-writer-3d { animation: none !important; }" in CSS
    assert "@keyframes boy-write" in CSS


# --- locomotion: the authored WalkCycle clips ----------------------

def _glb_animations(name):
    import json as _json
    import struct as _struct
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


def test_cats_carry_authored_walkcycle():
    # the original clips survive untouched alongside the walk
    tiger = _glb_animations("tiger.glb")
    assert tiger.get("Animation") == 39.04
    assert tiger.get("WalkCycle") == 1.0
    lion = _glb_animations("lion.glb")
    assert lion.get("GltfAnimation 0") == 2.97
    assert lion.get("WalkCycle") == 1.0


def test_scene3d_wires_locomotion():
    # Wave 62B: the cats are parked — the WalkCycle clips stay
    # in their files (asserted above) but scene3d.js neither
    # loads the models nor wires any locomotion.
    for marker in ("WalkCycle", "walkStride", "walkTarget",
                   "walkSpeed", "nativeScale"):
        assert marker not in S3D, marker
    assert "loadActor('tiger')" not in S3D
    assert "loadActor('lion')" not in S3D
    assert "loadActor('boy')" not in S3D


# --- fallback + pins, served ---------------------------------------

def test_served_page_wave62(client):
    page = client.get("/").get_data(as_text=True)
    assert 'SCENE_ORDER = ["eagle", "tiger", "chase", "lion"]' in page
    # Wave 70 (Suraj, 16 Nov 2026): the scene is PARKED — the
    # stage, 3D layer and 2D actors are NOT served (the
    # director script above stays in the page, inert without
    # its stage element).
    assert 'id="scene-3d"' not in page and 'id="scene-stage"' not in page
    assert "__ganitraBoyWriter3D" in page
    # Merge-4: pins reconciled to ?v=43 / ganitra-static-v30.
    assert "style.css?v=53" in page
    for n in ("eagle", "tiger", "boy"):
        assert f'id="scene-{n}"' not in page
