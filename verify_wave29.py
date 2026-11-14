#!/usr/bin/env python3
"""Wave 29 (Suraj, 14 Nov 2026): the chat Teach button that
"did nothing" in the Wave 28 LIVE verification.

Investigation before any fix (the drivers below ARE the
reproduction): the served page was booted in jsdom and
answer cards were added through the app's OWN flows — a
fresh submit, a Hindi question (the language-switch path),
and a chat restored from the account store — with real
/api/solve payloads. On EVERY path the Teach click engaged
synchronously (button -> stop state, steps blanked, then
revealed one by one, boy writer at the board) with zero
window errors. The handler is bound per card at build time
inside addAnswerBubble; the Wave 28 diff does not touch
that binding (only the boy-writer sprite URL inside it),
and there is no overlay, delegation gap or boot-order
defect in the shipped code. A negative control (the start
call removed from a copy of the page) reproduces the live
fingerprint exactly — card fine, Advice fine, Teach silent,
no errors — proving both that the symptom means "the start
never ran" and that the new regression test catches it.
The dead click therefore does NOT reproduce from the code;
it points at click delivery / observation in the checking
rig (an even number of toggle clicks ends in the stopped
state; a background tab never repaints). Wave 29 ships the
guarantee, not a guess:

1. THE TEACH REGRESSION is now part of the boot smoke,
   permanently: an answer card added the way the app adds
   it must open the teaching UI when Teach is clicked —
   synchronously and as playback reveals a step — with
   zero window errors, on a fresh card and on a restored
   one (see test/test_wave29_fixes.py, TEACH_DRIVER_JS).
2. SPEECH-API ISOLATION in speakPart: the utterance was
   built unguarded; on browsers/WebViews whose speech
   constructor or voice tuning throws, the narration chain
   died inside the click. An unvoiceable part now falls
   back to the timer pacing (the no-speech path), so the
   board always advances and the tap always shows.
3. The /photo-solve accessible name follows the source
   (it was one hardcoded photo line for every upload, in
   every language): the textarea now takes the same i18n
   heading as the visible box — file / file-ocr / photo,
   all 6 languages.
Delivery hygiene: stylesheet ?v=29, worker cache v6,
sprite URLs ?v=29 — all pins move together, as always.
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
with open("templates/answer.html", encoding="utf-8") as fh:
    ANSWER = fh.read()
with open("static/sw.js", encoding="utf-8") as fh:
    SW = fh.read()

os.environ["GANITRA_DB_PATH"] = os.path.join(
    tempfile.mkdtemp(), "w29.db")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
from app import create_app  # noqa: E402
import i18n  # noqa: E402

_app = create_app()
_app.config.update(TESTING=True)
_c = _app.test_client()
_c.post("/signup", data={
    "name": "W29 Verify", "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w29-verify-pass"})
PAGE = _c.get("/").get_data(as_text=True)

# --- 1. Speech-API isolation in the Teach click path ---------
check("utterance built behind a guard (Wave 29 note present)",
      "/* Wave 29: build the utterance behind a guard." in INDEX)
_b = INDEX.index("u = new SpeechSynthesisUtterance(part.text);")
_g = INDEX.index("catch (e) { u = null; }")
_br = INDEX.index("if (u) {", _b)
check("guard wraps construction + tuning, branch keys off it",
      _b < _g < _br)
check("timer fallback (no-speech pacing) still present",
      "Math.max(1800, part.text.length * 65)" in INDEX)

# --- 2. Accessible name follows the source --------------------
check("hardcoded photo aria-label gone from answer.html",
      'aria-label="Photo se padha gaya sawaal"' not in ANSWER)
check("aria-label takes the visible heading per source",
      'aria-label="{{ t.file_heading }}"' in ANSWER
      and 'aria-label="{{ t.photo_heading }}"' in ANSWER)
for _src, _key in (("file", "file_heading"),
                   ("file-ocr", "file_heading"),
                   ("photo", "photo_heading")):
    _html = _c.post("/photo-solve", data={
        "question": "2x + 3 = 7", "source": _src,
    }).get_data(as_text=True)
    _want = i18n.get_strings("en")[_key]
    _other = i18n.get_strings("en")[
        "photo_heading" if _key == "file_heading" else "file_heading"]
    check(f"rendered aria names the {_src} source (en)",
          f'aria-label="{_want}"' in _html
          and f'aria-label="{_other}"' not in _html)
_c.get("/set-lang/hi")
_html = _c.post("/photo-solve", data={
    "question": "2x + 3 = 7", "source": "file",
}).get_data(as_text=True)
check("rendered aria names the file source (hi)",
      f'aria-label="{i18n.get_strings("hi")["file_heading"]}"' in _html)
_c.get("/set-lang/en")

# --- 3. Delivery hygiene --------------------------------------
for _name, _count in (("eagle", 2), ("tiger", 2), ("boy", 4)):
    check(f"sprite {_name}: every URL versioned ?v=29",
          PAGE.count(f"scene-{_name}.webp") == _count
          and PAGE.count(f"scene-{_name}.webp?v=29") == _count,
          f"plain={PAGE.count(f'scene-{_name}.webp')} "
          f"versioned={PAGE.count(f'scene-{_name}.webp?v=29')}")
check("JS boy-writer sprites use the versioned URL",
      INDEX.count('"/static/scene-boy.webp?v=29"') == 2)
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

# --- 4. BOOT SMOKE (jsdom): scenes still play -----------------
sys.path.insert(0, os.path.join(ROOT, "test"))
_node = shutil.which("node")
try:
    from test_wave28_fixes import BOOT_DRIVER_JS, \
        _node_modules_candidates
    _have_boot = True
except Exception as _exc:  # pragma: no cover
    print("boot driver import failed:", _exc)
    _have_boot = False
try:
    from test_wave29_fixes import TEACH_DRIVER_JS
    _have_teach = True
except Exception as _exc:  # pragma: no cover
    print("teach driver import failed:", _exc)
    _have_teach = False


def _run_driver(driver_js, extra_files):
    _tmp = tempfile.mkdtemp()
    _pf = os.path.join(_tmp, "page.html")
    _bf = os.path.join(_tmp, "driver.js")
    open(_pf, "w", encoding="utf-8").write(PAGE)
    open(_bf, "w", encoding="utf-8").write(driver_js)
    _env = dict(os.environ)
    _env["NODE_PATH"] = os.pathsep.join(_node_modules_candidates())
    _args = [_node, _bf, _pf] + extra_files(_tmp)
    _r = subprocess.run(_args, capture_output=True, text=True,
                        env=_env, timeout=180)
    try:
        return json.loads(_r.stdout.strip().splitlines()[-1])
    except Exception:
        print("driver stderr:", _r.stderr[:300])
        return {}


if _node and _have_boot and _node_modules_candidates():
    _out = _run_driver(BOOT_DRIVER_JS, lambda _t: [])
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
    print("  --  node/jsdom unavailable: boot smoke skipped")

# --- 5. TEACH REGRESSION (jsdom): the click must open it ------
if _node and _have_teach and _node_modules_candidates():
    _payload = _c.post("/api/solve", json={
        "question": "2x + 3 = 7"}).get_json()

    def _extra(_tmp, _p=_payload):
        _pp = os.path.join(_tmp, "payload.json")
        open(_pp, "w", encoding="utf-8").write(json.dumps(_p))
        return [_pp]

    _out = _run_driver(TEACH_DRIVER_JS, _extra)
    if _out.get("skipped"):
        print("  --  teach regression skipped:", _out["skipped"])
    else:
        check("teach regression: driver completed",
              "fatal" not in _out, f"out={_out}")
        for _mode in ("fresh", "restored"):
            _s = _out.get(_mode) or {}
            _sync = _s.get("sync") or {}
            check(f"teach [{_mode}]: zero window errors",
                  _s.get("errors") == [],
                  f"errors={_s.get('errors')}")
            check(f"teach [{_mode}]: card added by the app's "
                  "own flow + Advice control works",
                  _s.get("cardAppeared") is True
                  and _s.get("adviceToggled") is True,
                  f"out={_s}")
            check(f"teach [{_mode}]: click opens the teaching "
                  "UI synchronously",
                  _sync.get("teaching") is True
                  and _sync.get("stopIcon") is True
                  and _sync.get("playing") is True
                  and (_sync.get("blanked") or 0) >= 1
                  and _sync.get("ansHeld") is True,
                  f"sync={_sync}")
            check(f"teach [{_mode}]: a step reveals as it plays",
                  _s.get("revealed") is True, f"out={_s}")
            check(f"teach [{_mode}]: second tap stops + restores",
                  _s.get("stopped") is True, f"out={_s}")
else:
    print("  --  node/jsdom unavailable: teach regression skipped")

print()
print(f"RESULT: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
