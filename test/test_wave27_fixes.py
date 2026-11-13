"""Wave 27 (Suraj, 13 Nov 2026): the phone-test fixes.

Plain composer (no pre-written example question), real
characters (transparent 384px sprites, no photo-card CSS),
a scene on EVERY load (first scene 2-4s, node-tested),
speed (sprites 537 KB -> ~69 KB, preloaded, ~20% quicker
scenes), smaller/tighter/plain composer icons in a roomier
comfort bar, and the chat font scale one notch down.
(The any-file endpoint itself is pinned in
test_file_upload.py.)
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


@pytest.fixture()
def page(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W27 Fixes Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w27-fixes-pass"})
    return client.get("/").get_data(as_text=True)


# --- 1. Plain composer ------------------------------------------

def test_composer_has_no_pre_written_question(page):
    assert 'placeholder="{{ t.question_placeholder }}"' not in INDEX
    assert "box.placeholder =" not in INDEX
    tag = re.search(r'<textarea id="q"[^>]*>', page)
    assert tag is not None and "placeholder" not in tag.group(0)
    assert "Solve 2x+3=7, integrate" not in page


# --- 2. Real characters, not photo cards -------------------------

def test_sprites_transparent_small_with_clear_corners():
    from PIL import Image
    total = 0
    for name in ("eagle", "tiger", "boy"):
        path = ROOT / "static" / f"scene-{name}.webp"
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        assert w <= 384 and h <= 384
        corners = [im.getpixel((0, 0))[3], im.getpixel((w - 1, 0))[3],
                   im.getpixel((0, h - 1))[3],
                   im.getpixel((w - 1, h - 1))[3]]
        assert corners == [0, 0, 0, 0]
        total += path.stat().st_size
    assert total < 120_000  # was 537,226 bytes at 1600px


def test_scene_css_has_no_card_styling():
    for selector in (".scene-actor {", ".boy-writer {"):
        rule = CSS[CSS.index(selector):]
        rule = rule[:rule.index("}")]
        assert "border-radius:" not in rule
        assert "box-shadow:" not in rule
    actor = CSS[CSS.index(".scene-actor {"):]
    assert "object-fit: contain" in actor[:actor.index("}")]


# --- 3+4. Scene on every load, fast -------------------------------

def test_sprites_preloaded(page):
    assert page.count('rel="preload"') >= 3
    for name in ("eagle", "tiger", "boy"):
        assert f"scene-{name}.webp" in page


def test_css_durations_match_trimmed_scenes():
    for decl in ("animation: eagle-visit 4.4s",
                 "animation: tiger-visit 6.9s",
                 "animation: logo-rolled 6.9s",
                 "animation: boy-rescue 6.9s",
                 "animation: chase-tiger 9.0s",
                 "animation: chase-logo 9.0s",
                 "animation: chase-boy 9.0s",
                 "animation: stick-arc 9.0s"):
        assert decl in CSS


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="node not installed")
def test_first_scene_within_2_to_4s_on_every_load():
    s = INDEX.index("/* SCENE-LOGIC-BEGIN")
    e = INDEX.index("/* SCENE-LOGIC-END */") + \
        len("/* SCENE-LOGIC-END */")
    driver = INDEX[s:e] + r"""
var out = {};
out.ms = [SCENE_MS.eagle, SCENE_MS.tiger, SCENE_MS.chase];
out.first_min = firstSceneDelayMs(0);
var ok = true;
for (var i = 0; i < 3000; i++) {
  var f = firstSceneDelayMs();
  if (f < 2000 || f >= 4000) ok = false;
}
out.first_range_ok = ok;
var prev = null, rep = 0;
for (var k = 0; k < 3000; k++) {
  var nx = pickSceneName(prev);
  if (nx === prev) rep++;
  prev = nx;
}
out.repeats = rep;
console.log(JSON.stringify(out));
"""
    path = "/tmp/w27-pytest-scenes.js"
    Path(path).write_text(driver, encoding="utf-8")
    r = subprocess.run([shutil.which("node"), path],
                       capture_output=True, text=True)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out["first_min"] == 2000
    assert out["first_range_ok"] is True
    assert out["ms"] == [4400, 6900, 9000]
    assert out["repeats"] == 0
    # The guarantee is structural: the director runs on every
    # load and its first pass uses the first-scene delay.
    assert "schedule(true);" in INDEX
    assert "first ? firstSceneDelayMs() : sceneDelayMs()" in INDEX


# --- 5+6. Composer icons + comfort ---------------------------------

def test_send_icon_not_highlighted():
    send = CSS[CSS.index(".send-btn {"):]
    send = send[:send.index("}")]
    assert "background: transparent" in send
    assert "var(--accent)" not in send
    assert "box-shadow: none" in send
    assert "body.chat-page .send-btn.icon-btn" \
        " { color: var(--accent); }" in CSS
    assert "body.chat-page .send-btn.icon-btn { color: #fff; }" \
        not in CSS


def test_composer_icons_smaller_and_tighter():
    assert "body.chat-page .chat-bar .composer-btn svg {\n" \
        "  width: 17px; height: 17px;" in CSS
    assert "body.chat-page .chat-bar .send-btn svg {\n" \
        "  width: 17px; height: 17px;" in CSS
    bar = CSS[CSS.index("body.chat-page .chat-bar {"):]
    bar = bar[:bar.index("}")]
    assert "gap: 2px" in bar
    assert "gap: 2px; align-items: center;" in CSS  # tools row


def test_composer_comfort_properties():
    bar = CSS[CSS.index("body.chat-page .chat-bar {"):]
    bar = bar[:bar.index("}")]
    assert "border-radius: 28px" in bar
    assert "padding: 12px 14px" in bar
    assert "align-items: flex-end" in bar  # icons bottom-aligned
    # ~40px tap target: 36px button + invisible halo.
    assert "width: 36px; height: 36px; min-height: 36px;" in CSS
    assert ".chat-bar .composer-btn::after" in CSS
    assert "inset: -2px;" in CSS
    # Textarea auto-grow handler (JS) with a sane cap.
    assert "Math.min(box.scrollHeight, 160)" in INDEX


# --- 8. Font scale ---------------------------------------------------

def test_chat_font_scale_wave27():
    assert "body.chat-page .bubble { font-size: 13px;" \
        " line-height: 1.65; }" in CSS
    assert "font-size: 14px; line-height: 1.8;" in CSS
    assert "font-size: 13.5px; line-height: 1.55;" in CSS
    assert "font-size: 14.5px; line-height: 1.5;" in CSS
    assert "font-size: 12px; letter-spacing: .04em;" in CSS


# --- Delivery hygiene --------------------------------------------------

def test_delivery_versions_bumped():
    assert "v='28'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v5"' in SW
