#!/usr/bin/env python3
"""Wave 27 (Suraj, 13 Nov 2026): the phone-test fixes.

Suraj tested Waves 23-26 on his phone and reported:
1. "Chat box mai pahale se wo question likha hai, usse
   hatana hai, bilkul plane rakhana hai" — the composer
   carried a pre-written example question (the
   question_placeholder: "e.g., Solve 2x+3=7, ..."). The
   placeholder attribute AND its language-switch re-apply
   are gone; the box is completely plain.
2. "Jo eagle aa rha hai photo mai aa rha hai, photo nhi
   aana, real wala chahiye" — the scene sprites were
   1600x1600 images with the cream background baked in,
   shown with a rounded card + shadow. Now: transparent
   384px WebPs (cream keyed out by border-connected
   component labelling; the tiger's white muzzle/belly
   survive because those near-white regions never touch
   the border) and NO card styling on the actors.
3. "Jab bhi wo reload kare, jab bhi aa jaaye" — the first
   scene now lands ~2-4s after EVERY load (the director
   runs fresh per load and schedule(true) uses
   firstSceneDelayMs), still rotating, never back-to-back.
4. "Slow kaam ho hai, speed se karana chahiye kaam" —
   sprites 537 KB -> ~69 KB total and preloaded; scene
   durations trimmed ~20% (5.4/8.6/11.2s -> 4.4/6.9/9.0s).
Plus his follow-ups the same morning:
5. Composer icons smaller (36px buttons, 17px glyphs),
   closer (2px cluster), and the SEND icon NOT highlighted
   (the accent disc is gone — plain like the others).
6. The composer gets the Claude/ChatGPT comfort treatment:
   28px radius, 12px 14px padding, auto-growing textarea
   (already present), bottom-aligned icons, ~40px tap
   targets via an invisible halo.
7. "Koi si bhi file ho" — the attach picker has NO accept
   restriction; /file-extract reads PDF/.docx/.txt server
   side (see test/test_file_upload.py) and answers honestly
   for anything else, in the student's language.
8. "Font size ko chota karo" (third time) — chat fonts one
   notch down: body/steps 13px, handwriting steps 14px,
   composer 13.5px, final answer 14.5px, headings 12px,
   line-height still 1.65.
Delivery hygiene: stylesheet ?v=27, worker cache v4.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

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


with open("templates/index.html", encoding="utf-8") as fh:
    INDEX = fh.read()
with open("templates/base.html", encoding="utf-8") as fh:
    BASE = fh.read()
with open("static/style.css", encoding="utf-8") as fh:
    CSS = fh.read()
with open("static/sw.js", encoding="utf-8") as fh:
    SW = fh.read()

os.environ["GANITRA_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(), "w27.db")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
from app import create_app  # noqa: E402

_app = create_app()
_app.config.update(TESTING=True)
_c = _app.test_client()
_c.post("/signup", data={
    "name": "W27 Verify", "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w27-verify-pass"})
PAGE = _c.get("/").get_data(as_text=True)

# --- 1. The composer is PLAIN -----------------------------------
check("placeholder attribute gone from the source",
      'placeholder="{{ t.question_placeholder }}"' not in INDEX
      and "box.placeholder =" not in INDEX)
_q = re.search(r'<textarea id="q"[^>]*>', PAGE)
check("served textarea has NO placeholder at all",
      _q is not None and "placeholder" not in _q.group(0),
      _q.group(0) if _q else "no textarea")
check("no example question text anywhere in the composer",
      "Solve 2x+3=7, integrate" not in PAGE)

# --- 2. Sprites: transparent, small, de-carded -------------------
from PIL import Image  # noqa: E402

_total = 0
for _name in ("eagle", "tiger", "boy"):
    _p = os.path.join("static", f"scene-{_name}.webp")
    _im = Image.open(_p)
    _px = _im.convert("RGBA")
    _w, _h = _px.size
    _corners = [_px.getpixel((0, 0))[3], _px.getpixel((_w - 1, 0))[3],
                _px.getpixel((0, _h - 1))[3],
                _px.getpixel((_w - 1, _h - 1))[3]]
    _size = os.path.getsize(_p)
    _total += _size
    check(f"sprite {_name}: RGBA, <=384px, clear corners, small",
          _im.mode == "RGBA" and _w <= 384 and _h <= 384
          and _corners == [0, 0, 0, 0] and _size < 40000,
          f"mode={_im.mode} size={_px.size} corners={_corners} "
          f"bytes={_size}")
check("all sprites together under 120 KB (was 537 KB)",
      _total < 120000, f"total={_total}")
_actor = CSS[CSS.index(".scene-actor {"):]
_actor = _actor[:_actor.index("}")]
_boy = CSS[CSS.index(".boy-writer {"):]
_boy = _boy[:_boy.index("}")]
check("scene actors carry NO photo-card styling",
      "border-radius:" not in _actor and "box-shadow:" not in _actor
      and "object-fit: contain" in _actor
      and "border-radius:" not in _boy and "box-shadow:" not in _boy,
      _actor.replace("\n", " ")[:120])

# --- 3. A scene on EVERY load, quickly ---------------------------
check("director still schedules the first scene per load",
      "schedule(true);" in INDEX
      and "first ? firstSceneDelayMs() : sceneDelayMs()" in INDEX)
_node = shutil.which("node")
if _node:
    _s = INDEX.index("/* SCENE-LOGIC-BEGIN")
    _e = INDEX.index("/* SCENE-LOGIC-END */") + \
        len("/* SCENE-LOGIC-END */")
    _driver = INDEX[_s:_e] + r"""
var out = {};
out.ms = [SCENE_MS.eagle, SCENE_MS.tiger, SCENE_MS.chase];
out.first_min = firstSceneDelayMs(0);
out.first_max = firstSceneDelayMs(0.999999);
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
    _p = "/tmp/w27-scenes.js"
    open(_p, "w", encoding="utf-8").write(_driver)
    _r = subprocess.run([_node, _p], capture_output=True, text=True)
    try:
        _out = json.loads(_r.stdout.strip().splitlines()[-1])
    except Exception:
        _out = {}
        print("node stderr:", _r.stderr[:300])
    check("first scene guaranteed within 2-4s of every load",
          _out.get("first_min") == 2000
          and _out.get("first_range_ok") is True,
          f"out={_out}")
    check("scene durations trimmed ~20% (4.4/6.9/9.0s)",
          _out.get("ms") == [4400, 6900, 9000], f"out={_out}")
    check("rotation never repeats back-to-back",
          _out.get("repeats") == 0, f"out={_out}")
else:
    print("  --  node not found: scheduler unit checks skipped")
check("CSS keyframes carry the same trimmed durations",
      all(s in CSS for s in (
          "animation: eagle-visit 4.4s", "animation: tiger-visit 6.9s",
          "animation: logo-rolled 6.9s", "animation: boy-rescue 6.9s",
          "animation: chase-tiger 9.0s", "animation: chase-logo 9.0s",
          "animation: chase-boy 9.0s", "animation: stick-arc 9.0s")))

# --- 4. Speed: preloads ------------------------------------------
check("sprites preloaded from the chat page head",
      PAGE.count('rel="preload"') >= 3
      and "scene-eagle.webp" in PAGE and "scene-tiger.webp" in PAGE
      and "scene-boy.webp" in PAGE)

# --- 5+6. Composer icons + comfort --------------------------------
_send = CSS[CSS.index(".send-btn {"):]
_send = _send[:_send.index("}")]
check("send icon is PLAIN (no accent fill, no shadow)",
      "background: transparent" in _send
      and "var(--accent)" not in _send and "box-shadow: none" in _send
      and "body.chat-page .send-btn.icon-btn"
          " { color: var(--accent); }" in CSS,
      _send.replace("\n", " ")[:140])
check("composer glyphs one size, smaller (17px)",
      "body.chat-page .chat-bar .composer-btn svg {\n"
      "  width: 17px; height: 17px;" in CSS
      and "body.chat-page .chat-bar .send-btn svg {\n"
      "  width: 17px; height: 17px;" in CSS)
_bar = CSS[CSS.index("body.chat-page .chat-bar {"):]
_bar = _bar[:_bar.index("}")]
check("composer cluster tight (2px gaps) + roomy comfort box",
      "gap: 2px" in _bar and "border-radius: 28px" in _bar
      and "padding: 12px 14px" in _bar
      and "align-items: flex-end" in _bar
      and "gap: 2px; align-items: center;" in CSS,
      _bar.replace("\n", " ")[:160])
check("tap targets stay ~40px (36px button + halo)",
      "width: 36px; height: 36px; min-height: 36px;" in CSS
      and ".chat-bar .composer-btn::after" in CSS
      and "inset: -2px;" in CSS)
check("textarea auto-grow still wired (to 160px, then scroll)",
      "Math.min(box.scrollHeight, 160)" in PAGE)

# --- 7. Any-file picker -------------------------------------------
_pi = PAGE[PAGE.index('id="photo-input"') - 30:
           PAGE.index('id="photo-input"') + 40]
check("attach picker offers EVERY file type (no accept)",
      "accept=" not in _pi and "/file-extract" in PAGE, _pi)
check("file messages ride js_t in the page payload",
      "js_file_reading" in PAGE and "js_file_unsupported" in PAGE
      and "js_file_too_large" in PAGE)

# --- 8. Font scale, one notch down ---------------------------------
check("chat fonts: 13 / 14 / 13.5 / 14.5 / 12, lh 1.65",
      "body.chat-page .bubble { font-size: 13px;"
      " line-height: 1.65; }" in CSS
      and "font-size: 14px; line-height: 1.8;" in CSS
      and "font-size: 13.5px; line-height: 1.55;" in CSS
      and "font-size: 14.5px; line-height: 1.5;" in CSS
      and "font-size: 12px; letter-spacing: .04em;" in CSS)

# --- Delivery hygiene + frozen logo ---------------------------------
check("stylesheet bumped to ?v=27 (template + served)",
      "v='27'" in BASE and "style.css?v=27" in PAGE)
check("service worker cache bumped to v4",
      'GANITRA_CACHE = "ganitra-static-v4"' in SW)
for _name, _want in (
        ("logo-full-t.png", "f18c8e42"), ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"), ("logo-mark.png", "03bc03dc")):
    _digest = hashlib.sha256(
        open(os.path.join("static", _name), "rb").read()).hexdigest()
    check(f"frozen logo {_name} untouched",
          _digest.startswith(_want), _digest[:12])

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
