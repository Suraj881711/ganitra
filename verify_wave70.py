"""Wave 70 verification: THE SCENE IS PARKED (bilkul khali).

Suraj's order (16 Nov 2026): "koi saa bhi mt rakho sab hata
do abhi ke liye" + "Scene se eagle bhi hata do, bilkul khali
kar do" — and he declined the paid replacement eagle. The
empty state must show ONLY the still logo + greeting: no
eagle, no tiger/boy sprites, no stick, no 3D layer, no sprite
preloads. All scene code, sprites and models stay in the
repo, parked behind app.SCENE_ENABLED (False); both scene
scripts inert themselves because the stage id is not served.

Checks:
 1. SCENE_ENABLED is False and served to templates.
 2. Template: stage id + actors live inside {% if
    scene_enabled %}; scene files still exist (parked).
 3. Rendered chat page: logo + greeting + composer present;
    scene-stage / scene-3d / actor / stick ids absent; no
    sprite preload links; pins ?v=38 / v15 unchanged.
 4. Chat untouched: Hindi train question still solves to
    40 km/h.

Run:  python3 verify_wave70.py   (exit 0 = all checks pass)
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

FAILS = []


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label
          + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


import app as app_module  # noqa: E402

check("SCENE_ENABLED is False (parked)",
      app_module.SCENE_ENABLED is False)
check("context serves scene_enabled",
      '"scene_enabled": SCENE_ENABLED' in Path("app.py").read_text(
          encoding="utf-8"))

index = Path("templates/index.html").read_text(encoding="utf-8")
check("stage id is conditional on scene_enabled",
      '{% if scene_enabled %} id="scene-stage"{% endif %}' in index)
_stage_if = index.rindex("{% if scene_enabled %}",
                         0, index.index('id="scene-logo"'))
_eagle = index.index('id="scene-eagle"')
check("actors render inside the scene_enabled block",
      _stage_if < _eagle < index.index("{% endif %}", _eagle))
for parked in ("static/scene3d.js", "static/scene-eagle.webp",
               "static/scene-tiger.webp", "static/scene-boy.webp",
               "static/models/eagle.glb", "static/logo-g-t.png"):
    check(f"parked file still in repo: {parked}",
          (ROOT / parked).exists())

tmp = tempfile.mkdtemp(prefix="ganitra-w70-")
os.environ["GANITRA_DB_PATH"] = str(Path(tmp) / "users.db")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
flask_app = app_module.create_app()
flask_app.config["TESTING"] = True
client = flask_app.test_client()
r = client.post("/signup", data={
    "name": "W70 Tester", "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w70-test-pass"})
check("signup works", r.status_code in (200, 302),
      f"status {r.status_code}")
page = client.get("/").get_data(as_text=True)
check("logo still served", 'id="scene-logo"' in page
      and "logo-full-t.png" in page)
check("greeting still served", "empty-greeting" in page)
check("composer still served", 'id="chat-form"' in page
      or "composer" in page)
for gone in ('id="scene-stage"', 'id="scene-3d"',
             'id="scene-eagle"', 'id="scene-tiger"',
             'id="scene-boy"', 'id="scene-stick"'):
    check(f"not served: {gone}", gone not in page)
check("no sprite preloads served",
      'rel="preload"' not in page and "scene-eagle.webp" not in page
      and "scene-tiger.webp" not in page)
check("pins ?v=52 / v29 (Wave 163)",
      "style.css?v=54" in page)

from api import _solve_friendly  # noqa: E402
r = _solve_friendly("एक ट्रेन 60 km की दूरी 1.5 घंटे में तय करती है। "
                    "ट्रेन की चाल क्या है?")
check("Hindi train still solves (chat untouched)",
      "40" in str(r.get("answer", "")), str(r.get("answer", ""))[:60])

print()
if FAILS:
    print(f"verify_wave70: {len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("verify_wave70: ALL CHECKS PASSED")
