"""Wave 62B: the eagle-only final cut of the 3D scene.

Suraj's final spec (15 Nov 2026, 15:57-16:15 IST), applied on
top of Wave 62: "abhi saare 3d model chodo bs eagle kaa
rakho" (the 3D scene keeps ONLY the eagle; tiger/lion/boy
models are parked — files kept, never loaded), "aise board
mai nhi karana, pahale ki tarah same karana hai" (NO wooden
board — the logo itself is the object, as in the old 2D
scene), "jo ganitra kaa logo hai G bas wahi hona chahiye"
(the object is ONLY the G, never the name), plus the carry
(the eagle grips the G with its talons, flies it across,
sets it back from the other side) and the kiss (pyaar: a
beak-touch on the G with a heart pop). The boy writer is
the pre-61 2D sprite again.
"""
import hashlib
import json
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
S3D = (ROOT / "static" / "scene3d.js").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W62B Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w62b-test-pass"})
    return c


# --- only the eagle loads -------------------------------------

def test_scene3d_loads_only_the_eagle():
    assert "loadEagle();" in S3D
    assert "loadActor" not in S3D
    for name in ("tiger", "lion", "boy"):
        assert f"modelURL('{name}')" not in S3D
        assert f"loadEagle('{name}')" not in S3D
    assert "actors: ['eagle']" in S3D


def test_parked_models_stay_in_the_tree():
    # parked, not deleted — with Wave 62's authored WalkCycle
    for name, md5 in (("tiger.glb", "e125ebd2d1b9cf0c7489da200bc7f3a4"),
                      ("lion.glb", "0d68ef98dfefa1647fd5d7426c9a4950"),
                      ("boy.glb", "0813eaf3b74561813caf397b6aafc66e"),
                      ("eagle.glb", "e183b7f20d421573fd24181d4655503b")):
        p = ROOT / "static" / "models" / name
        assert p.exists(), name
        assert hashlib.md5(p.read_bytes()).hexdigest() == md5, name


def test_activation_makes_the_rotation_eagle_only():
    assert "window.__sceneEagleOnly3D = true" in S3D
    assert "__sceneSetBroken('tiger', true)" in S3D
    assert "__sceneSetBroken('boy', true)" in S3D
    assert "__sceneSetBroken('lion', true)" in S3D
    assert "__sceneSetBroken('eagle', false)" in S3D
    # the director consults the flag only when the pool empties
    assert "window.__sceneEagleOnly3D" in INDEX
    assert "n !== prev" in INDEX   # the 2D rule itself unchanged


# --- the G itself, no board ------------------------------------

def test_no_board_no_plaque():
    assert "/static/logo-g-t.png" in S3D
    assert "/static/logo-full-t.png" not in S3D
    # the wooden frame and its feet were the only boxes in the
    # scene; with the board gone there is no BoxGeometry at all
    assert "BoxGeometry" not in S3D


def test_g_texture_is_the_glyph_only():
    from PIL import Image
    import numpy as np
    im = Image.open(ROOT / "static" / "logo-g-t.png")
    assert im.mode == "RGBA"
    assert im.size == (696, 632)         # the frozen crop's box
    a = np.asarray(im)
    alpha = a[:, :, 3]
    # the paper is keyed away: corners fully transparent
    assert alpha[0, 0] == 0 and alpha[0, -1] == 0
    assert alpha[-1, 0] == 0 and alpha[-1, -1] == 0
    # the glyph is one contiguous opaque band — no name text
    rows = (alpha > 128).sum(axis=1)
    filled = [i for i, r in enumerate(rows) if r > 0]
    assert filled == list(range(filled[0], filled[-1] + 1))
    assert filled[-1] - filled[0] < 600  # glyph height, not glyph+name


# --- the eagle's three performances ------------------------------

def test_eagle_variants_perch_carry_kiss():
    for fn in ("playEaglePerch", "playEagleCarry", "playEagleKiss"):
        assert f"function {fn}" in S3D, fn
    assert "EAGLE_VARIANTS" in S3D
    # the carry pins the G to the talons while it flies
    assert "pinLogoToTalons" in S3D
    # the kiss has its heart pop
    assert "CanvasTexture" in S3D and "heart" in S3D


# --- the boy writer is the sprite again --------------------------

def test_boy_writer_is_the_2d_sprite_again():
    assert "__ganitraBoyWriter3D" not in S3D
    assert 'boyWriter.src = "/static/scene-boy.webp?v=29"' in INDEX
    # Wave 176: the typing bubble's sprite (boy.src) is gone
    # with the bubble post; the board writer remains.
    assert 'boy.src = "/static/scene-boy.webp' not in INDEX


# --- served --------------------------------------------------------

def test_served_page_wave62b(client):
    page = client.get("/").get_data(as_text=True)
    # Wave 70 (Suraj, 16 Nov 2026): the scene is PARKED — the
    # stage and 3D layer are NOT served at all.
    assert 'id="scene-3d"' not in page and 'id="scene-stage"' not in page
    # Merge-4: pins reconciled to ?v=43 / ganitra-static-v25
    # (historical note; the live pin asserted below is current).
    assert "style.css?v=59" in page
    r = client.get("/static/logo-g-t.png")
    assert r.status_code == 200
    # the parked files are still served (they exist) — the
    # PAGE simply never asks for them (headless-verified).
    for name in ("tiger", "lion", "boy", "eagle"):
        rr = client.get(f"/static/models/{name}.glb")
        assert rr.status_code == 200, name
