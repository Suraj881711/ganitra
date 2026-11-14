#!/usr/bin/env python3
"""Wave 28 (Suraj, 13 Nov 2026): fix the two REAL failures
from the Wave 27 LIVE verification (the local suite was
green; the live site was not).

Failure 1 — scenes never played live. Reproduced in jsdom
against the real served page (boot driver below):
- With document.hidden true when the first-scene timer
  fired (background-opened tab, automated checker, phone
  waking), playNext re-armed with the 25-75s gap, demoting
  the guaranteed 2-4s first scene to "maybe in a minute";
  visibilitychange re-armed the long gap too.
- The parse-time sprite probe (complete && naturalWidth
  === 0) plus error -> stopScenes wiring meant ONE sprite
  failed by parse time silenced EVERY scene all session.
The fixes are structural: the first scene is OWED until it
plays in front of the student (firstPending re-arms short
on hidden fires, visibilitychange and pageshow); a failed
sprite marks only itself broken (error event + post-load
probe) and only its scenes leave the rotation; the
parser-blocking Tesseract CDN script now carries defer.
The sprite URLs are versioned (?v=28) like the stylesheet
(PythonAnywhere's day-long /static/ max-age + the worker's
stale-while-revalidate could replay the old card sprites
for up to a day — the stale tan-card eagle seen live).
Delivery hygiene: stylesheet ?v=28, worker cache v5.

Failure 2 — a .txt/.pdf upload's answer page kept the
photo wording ("फ़ोटो से पढ़ा गया प्रश्न") and the OCR
misread warning. The upload now reports its source
(photo / file / file-ocr) through /photo-solve; the answer
page uses file_heading / file_text / file_ocr_text (all 6
languages) and shows the OCR warning only when OCR ran.

The BOOT SMOKE TEST below is the permanent guard for
Failure 1: it runs the served page's full script set in
jsdom, in order, with real timers, fails on ANY window
error, and asserts a scene is scheduled inside the 2-4s
window and plays — fresh load, second load, hidden ->
visible flip, and with one sprite broken.
"""
import hashlib
import json
import os
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
with open("static/sw.js", encoding="utf-8") as fh:
    SW = fh.read()

os.environ["GANITRA_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(), "w28.db")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
from app import create_app  # noqa: E402
import i18n  # noqa: E402

_app = create_app()
_app.config.update(TESTING=True)
_c = _app.test_client()
_c.post("/signup", data={
    "name": "W28 Verify", "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w28-verify-pass"})
PAGE = _c.get("/").get_data(as_text=True)

# --- 1. The first scene is owed until it plays ------------------
check("firstPending tracks the owed first scene",
      "var firstPending = true;" in INDEX
      and "firstPending = false;" in INDEX
      and "schedule(firstPending);" in INDEX)
check("hidden fire no longer demotes to the long gap",
      "if (document.hidden) { schedule(); return; }" not in INDEX
      and "schedule(firstPending);\n          return;" in INDEX)
check("pageshow (bfcache) re-arms the director",
      'addEventListener("pageshow"' in INDEX)

# --- 2. The sprite kill-switch is gone ---------------------------
check("parse-time naturalWidth kill removed",
      "if (img.complete && img.naturalWidth === 0) stopScenes();"
      not in INDEX)
check("sprite error no longer stops every scene",
      'addEventListener("error", stopScenes)' not in INDEX
      and "function markBroken(shortName)" in INDEX
      and "markBroken(pair[1])" in INDEX)
check("broken judged at window load, not at parse time",
      'window.addEventListener("load", function () {' in INDEX
      and "img.complete && img.naturalWidth === 0" in INDEX)
check("picker receives the broken map",
      "pickSceneName(lastScene, null, broken)" in INDEX
      and "SCENE_SPRITES" in INDEX)

# --- 3. Tesseract deferred ---------------------------------------
check("Tesseract CDN script carries defer",
      '<script defer src="https://cdn.jsdelivr.net/npm/'
      'tesseract.js@5/dist/tesseract.min.js"></script>' in INDEX)

# --- 4. Sprite URLs versioned -------------------------------------
for _name, _count in (("eagle", 2), ("tiger", 2), ("boy", 4)):
    check(f"sprite {_name}: every URL versioned ?v=29",
          PAGE.count(f"scene-{_name}.webp") == _count
          and PAGE.count(f"scene-{_name}.webp?v=29") == _count,
          f"plain={PAGE.count(f'scene-{_name}.webp')} "
          f"versioned={PAGE.count(f'scene-{_name}.webp?v=29')}")
check("JS boy-writer sprites use the versioned URL",
      INDEX.count('"/static/scene-boy.webp?v=29"') == 2)

# --- 5. Delivery hygiene ------------------------------------------
check("stylesheet bumped to ?v=29 (template + served)",
      "v='29'" in BASE and "style.css?v=29" in PAGE)
check("service worker cache bumped to v6, older names absent",
      'GANITRA_CACHE = "ganitra-static-v6"' in SW
      and all(f"ganitra-static-v{n}" not in SW
              for n in (1, 2, 3, 4, 5)))
for _name, _want in (
        ("logo-full-t.png", "f18c8e42"), ("logo-full.png", "07009560"),
        ("logo-mark-t.png", "01aa3d23"), ("logo-mark.png", "03bc03dc")):
    _digest = hashlib.sha256(
        open(os.path.join("static", _name), "rb").read()).hexdigest()
    check(f"frozen logo {_name} untouched",
          _digest.startswith(_want), _digest[:12])

# --- 6. Scene logic under node (broken-map behaviour) --------------
_node = shutil.which("node")
if _node:
    _s = INDEX.index("/* SCENE-LOGIC-BEGIN")
    _e = INDEX.index("/* SCENE-LOGIC-END */") + \
        len("/* SCENE-LOGIC-END */")
    _driver = INDEX[_s:_e] + r"""
var out = {};
// No broken sprites: the Wave 23-27 behaviour is unchanged.
var prev = null, rep = 0;
for (var k = 0; k < 3000; k++) {
  var nx = pickSceneName(prev);
  if (nx === prev || nx === null) rep++;
  prev = nx;
}
out.clean_repeats_or_nulls = rep;
// Eagle broken: only tiger/chase are ever picked.
var seenE = {}, badE = 0;
for (var i = 0; i < 600; i++) {
  var s1 = pickSceneName(null, null, { eagle: true });
  seenE[s1] = 1;
  if (s1 === "eagle" || s1 === null) badE++;
}
out.eagle_broken_seen = Object.keys(seenE).sort();
out.eagle_broken_bad = badE;
// Tiger broken: tiger AND chase need it — only eagle plays.
var seenT = {}, badT = 0;
for (var j = 0; j < 600; j++) {
  var s2 = pickSceneName(null, null, { tiger: true });
  seenT[s2] = 1;
  if (s2 !== "eagle") badT++;
}
out.tiger_broken_seen = Object.keys(seenT).sort();
out.tiger_broken_bad = badT;
// Everything broken: the picker honestly gives up (null).
out.all_broken = pickSceneName(null, null,
  { eagle: true, tiger: true, boy: true });
// Playability map itself.
out.play = {
  eagle_ok: scenePlayable("eagle", {}),
  tiger_needs_boy: scenePlayable("tiger", { boy: true }),
  chase_needs_tiger: scenePlayable("chase", { tiger: true })
};
console.log(JSON.stringify(out));
"""
    _p = "/tmp/w28-scenes.js"
    open(_p, "w", encoding="utf-8").write(_driver)
    _r = subprocess.run([_node, _p], capture_output=True, text=True)
    try:
        _out = json.loads(_r.stdout.strip().splitlines()[-1])
    except Exception:
        _out = {}
        print("node stderr:", _r.stderr[:300])
    check("picker unchanged when nothing is broken",
          _out.get("clean_repeats_or_nulls") == 0, f"out={_out}")
    check("eagle broken -> tiger/chase still rotate",
          _out.get("eagle_broken_seen") == ["chase", "tiger"]
          and _out.get("eagle_broken_bad") == 0, f"out={_out}")
    check("tiger broken -> only the eagle plays",
          _out.get("tiger_broken_seen") == ["eagle"]
          and _out.get("tiger_broken_bad") == 0, f"out={_out}")
    check("all sprites broken -> picker returns null",
          _out.get("all_broken") is None, f"out={_out}")
    check("scenePlayable honours the sprite map",
          _out.get("play") == {"eagle_ok": True,
                               "tiger_needs_boy": False,
                               "chase_needs_tiger": False},
          f"out={_out}")
else:
    print("  --  node not found: scene-logic checks skipped")

# --- 7. File wording over HTTP --------------------------------------
_en = i18n.get_strings("en")


def _solve(source_marker):
    _data = {"question": "Solve 2x + 3 = 7"}
    if source_marker is not None:
        _data["source"] = source_marker
    _r = _c.post("/photo-solve", data=_data)
    return _r.get_data(as_text=True)


_pg = _solve("file")
check("file source: file heading + text, no photo, no OCR warn",
      _en["file_heading"] in _pg and _en["file_text"] in _pg
      and _en["photo_heading"] not in _pg
      and _en["photo_text"] not in _pg
      and "OCR sometimes misreads" not in _pg)
_pg = _solve("file-ocr")
check("file-ocr source: file heading + OCR warning kept",
      _en["file_heading"] in _pg
      and "was read like a photo" in _pg
      and "(OCR sometimes misreads a number or sign" in _pg
      and _en["photo_heading"] not in _pg)
_pg = _solve("photo")
check("photo source: wording exactly as before",
      _en["photo_heading"] in _pg and _en["photo_text"] in _pg
      and _en["file_heading"] not in _pg)
_pg = _solve(None)
check("missing source defaults to the photo wording",
      _en["photo_heading"] in _pg)
_c.get("/set-lang/hi")
_hi = i18n.get_strings("hi")
_pg = _solve("file")
check("Hindi file source: फ़ाइल heading, no photo heading",
      _hi["file_heading"] in _pg and _hi["photo_heading"] not in _pg)
_c.get("/set-lang/en")
check("file keys complete + OCR-free clean text in all 6 languages",
      all(i18n.get_strings(_l)["file_heading"]
          and i18n.get_strings(_l)["file_text"]
          and i18n.get_strings(_l)["file_ocr_text"]
          and "OCR" not in i18n.get_strings(_l)["file_text"]
          and "OCR" in i18n.get_strings(_l)["file_ocr_text"]
          for _l in ("en", "hi", "bn", "mr", "ta", "te")))
check("upload flow reports its source end to end",
      'id="photo-source"' in PAGE
      and 'sendQuestionText(d.text, "file")' in INDEX
      and 'ocrBlob(blob, "file-ocr")' in INDEX)

# --- 8. BOOT SMOKE TEST (jsdom, full page, real timers) -------------
sys.path.insert(0, os.path.join(ROOT, "test"))
try:
    from test_wave28_fixes import BOOT_DRIVER_JS, \
        _node_modules_candidates
    _have_driver = True
except Exception as _exc:  # pragma: no cover
    print("boot driver import failed:", _exc)
    _have_driver = False
if _node and _have_driver:
    _cands = _node_modules_candidates()
    if _cands:
        _tmp = tempfile.mkdtemp()
        _pf = os.path.join(_tmp, "page.html")
        _bf = os.path.join(_tmp, "boot.js")
        open(_pf, "w", encoding="utf-8").write(PAGE)
        open(_bf, "w", encoding="utf-8").write(BOOT_DRIVER_JS)
        _env = dict(os.environ)
        _env["NODE_PATH"] = os.pathsep.join(_cands)
        _r = subprocess.run([_node, _bf, _pf], capture_output=True,
                            text=True, env=_env, timeout=180)
        try:
            _out = json.loads(_r.stdout.strip().splitlines()[-1])
        except Exception:
            _out = {}
            print("boot stderr:", _r.stderr[:300])
        if _out.get("skipped"):
            print("  --  boot smoke skipped:", _out["skipped"])
        else:
            for _name in ("fresh", "second", "hiddenflip",
                          "brokeneagle"):
                _s2 = _out.get(_name) or {}
                check(f"boot smoke [{_name}]: zero window errors",
                      _s2.get("errors") == [],
                      f"errors={_s2.get('errors')}")
                check(f"boot smoke [{_name}]: scene scheduled "
                      "in the 2-4s window and played",
                      (_s2.get("firstBandCount") or 0) >= 1
                      and _s2.get("scene")
                      in ("eagle", "tiger", "chase"),
                      f"out={_s2}")
            check("boot smoke [brokeneagle]: a surviving scene "
                  "played, never the broken one",
                  (_out.get("brokeneagle") or {}).get("scene")
                  in ("tiger", "chase"),
                  f"out={_out.get('brokeneagle')}")
    else:
        print("  --  jsdom not found: boot smoke skipped")
else:
    print("  --  node/jsdom unavailable: boot smoke skipped")

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
