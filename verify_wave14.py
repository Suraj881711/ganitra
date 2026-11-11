"""Wave-14 verification: SPEED / instant feel.

Contract (Suraj's instruction, 10 Nov 2026: "koi error nhi
aani chahiye... load hone mai time lag raha ho aisa nhi hona
chahiye, haathohaath kaam hona chahiye"):

1. Pre-warm at start-up: create_app() eagerly loads the heavy
   solver stack, runs dummy solves, and initialises the DB —
   flagged via config GANITRA_WARMED_UP; a warm-up failure must
   never break start-up (it is fully guarded in app._warm_up).
2. Auto-teach never blocks: the Wave-12/13 alternate-methods
   pass behind /api/solve runs via speedups.methods_nonblocking
   (daemon thread + hard budget). The response still carries
   the SAME methods data (Wave-12 contract unchanged); a forced
   tiny budget proves the answer survives a teach overrun, and
   a forced exception inside the computation is swallowed.
3. DB speed: WAL journal mode + the hot-lookup indexes exist
   (users by name_key, chats by user_id / user+updated_at,
   photos by user_id).
4. Static assets carry a browser cache header; HTML does not.
5. TIMINGS (honest, local only): cold start-up in a FRESH
   interpreter (imports + create_app incl. warm-up), the first
   /api/solve after it, a repeat identical solve, the raw
   alternate-methods cost, and signup+login+chats-list. These
   numbers measure THIS machine's code-path cost — Render's
   free-tier cold start (process spin-up after sleep) is a
   platform cost on top and is NOT measured here.

Run:  python verify_wave14.py
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave14.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(os.environ["GANITRA_DB_PATH"] + suffix)
    except OSError:
        pass

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


def ms(seconds):
    return f"{seconds * 1000:.0f} ms"


timings = {}

# --- 1. Cold start-up in a fresh interpreter ------------------------------
# A subprocess so the measurement includes the real import cost
# (sympy, matplotlib) + create_app() WITH the Wave-14 warm-up.
_COLD = r"""
import json, os, sys, time
sys.path.insert(0, os.environ["W14_ROOT"])
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave14-cold.db"
t0 = time.perf_counter()
import app as app_module
t_import = time.perf_counter()
flask_app = app_module.create_app()
t_create = time.perf_counter()
client = flask_app.test_client()
t1 = time.perf_counter()
r = client.post("/api/solve", json={"question": "x^2 - 5x + 6 = 0"})
t_first = time.perf_counter()
d = r.get_json() or {}
t2 = time.perf_counter()
r = client.post("/api/solve", json={"question": "x^2 - 5x + 6 = 0"})
t_repeat = time.perf_counter()
print(json.dumps({
    "import_s": t_import - t0,
    "create_s": t_create - t_import,
    "warmed": bool(flask_app.config.get("GANITRA_WARMED_UP")),
    "first_solve_s": t_first - t1,
    "first_ok": d.get("ok") is True,
    "first_answer": (d.get("result") or {}).get("answer", ""),
    "first_methods": [m.get("id") for m in d.get("methods") or []],
    "repeat_solve_s": t_repeat - t2,
}))
"""
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove("/tmp/ganitra-verify-wave14-cold.db" + suffix)
    except OSError:
        pass
env = dict(os.environ, W14_ROOT=str(Path(__file__).parent))
proc = subprocess.run([sys.executable, "-c", _COLD], env=env,
                      capture_output=True, text=True, timeout=300)
cold = {}
try:
    cold = json.loads(proc.stdout.strip().splitlines()[-1])
except (ValueError, IndexError):
    check("cold-start subprocess produced timings", False,
          (proc.stdout + proc.stderr)[-300:])
if cold:
    timings["cold import (fresh interpreter)"] = cold["import_s"]
    timings["create_app incl. warm-up"] = cold["create_s"]
    timings["first /api/solve after cold start"] = \
        cold["first_solve_s"]
    timings["repeat identical /api/solve"] = cold["repeat_solve_s"]
    check("warm-up ran during cold create_app",
          cold["warmed"] is True)
    check("first solve after cold start is correct",
          cold["first_ok"] is True
          and "x = 2" in str(cold.get("first_answer", "")),
          f"answer={cold.get('first_answer')!r}")
    check("first solve carries the teach methods",
          set(cold["first_methods"])
          == {"factor", "complete_square", "graph"},
          f"methods={cold['first_methods']}")

# --- 2. In-process app: API surface + login + chats timings ----------------
from app import create_app  # noqa: E402
from solver.methods import alternate_methods  # noqa: E402
from solver.router import solve_question  # noqa: E402
from speedups import methods_nonblocking  # noqa: E402
import speedups  # noqa: E402

app = create_app()
check("warm-up flag set (in-process app)",
      app.config.get("GANITRA_WARMED_UP") is True)
client = app.test_client()

t0 = time.perf_counter()
r = client.post("/api/solve",
                json={"question": "what is 15% of 240"})
timings["/api/solve (warm, percentage)"] = time.perf_counter() - t0
d = r.get_json() or {}
check("warm solve ok + methods intact",
      d.get("ok") is True and len(d.get("methods") or []) >= 2,
      f"methods={[m.get('id') for m in d.get('methods') or []]}")

# Raw auto-teach cost vs the non-blocking wrapper (same data).
q = "x^2 - 5x + 6 = 0"
primary = solve_question(q)
t0 = time.perf_counter()
direct = alternate_methods(q, primary)
timings["alternate_methods raw cost"] = time.perf_counter() - t0
wrapped = methods_nonblocking(q, primary)
check("non-blocking teach == direct teach (same data)",
      wrapped == direct and len(direct) == 3,
      f"direct={len(direct)} wrapped={len(wrapped)}")

# Budget enforcement: a 1ms budget against a patched slow
# computation must return [] fast and never raise.
_orig = speedups.alternate_methods


def _slow(question, result):
    time.sleep(1.0)
    return [{"id": "slow", "label": "Slow", "steps": [],
             "answer": ""}]


speedups.alternate_methods = _slow
try:
    t0 = time.perf_counter()
    out = methods_nonblocking(q, primary, budget=0.05)
    elapsed = time.perf_counter() - t0
finally:
    speedups.alternate_methods = _orig
check("teach overrun -> answer not blocked ([] fast)",
      out == [] and elapsed < 0.9, f"elapsed={ms(elapsed)}")


def _boom(question, result):
    raise RuntimeError("teach exploded")


speedups.alternate_methods = _boom
try:
    out = methods_nonblocking(q, primary)
finally:
    speedups.alternate_methods = _orig
check("teach exception swallowed -> []", out == [])

# Login + chats list timing (the Wave-10/11 hot path).
name = "W14 Speed " + RUN_ID
t0 = time.perf_counter()
r = client.post("/signup", data={
    "name": name, "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w14test-pass"})
timings["signup (4 PBKDF2 hashes)"] = time.perf_counter() - t0
check("signup succeeds", r.status_code in (200, 302),
      f"status={r.status_code}")
t0 = time.perf_counter()
r = client.get("/api/chats")
timings["GET /api/chats (signed in)"] = time.perf_counter() - t0
check("chats list ok after signup",
      r.status_code == 200
      and (r.get_json() or {}).get("ok") is True)
t0 = time.perf_counter()
r = client.get("/account/stats.json")
timings["GET /account/stats.json"] = time.perf_counter() - t0
check("stats.json ok", r.status_code == 200
      and (r.get_json() or {}).get("ok") is True)

# --- 3. DB: WAL + indexes ---------------------------------------------------
conn = sqlite3.connect(os.environ["GANITRA_DB_PATH"])
mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
check("SQLite journal mode is WAL", str(mode).lower() == "wal",
      f"mode={mode}")
indexes = {row[0] for row in conn.execute(
    "SELECT name FROM sqlite_master WHERE type = 'index'")}
for wanted in ("idx_users_name_key", "idx_user_photos_user",
               "idx_chats_user", "idx_chats_user_updated"):
    check(f"index exists: {wanted}", wanted in indexes)
conn.close()

# --- 4. Static cache headers --------------------------------------------------
r = client.get("/static/style.css")
check("static CSS cached (public, max-age)",
      r.status_code == 200
      and "max-age=86400" in (r.headers.get("Cache-Control") or ""),
      f"CC={r.headers.get('Cache-Control')}")
r = client.get("/static/logo-full.png")
check("static logo cached (public, max-age)",
      r.status_code == 200
      and "max-age=86400" in (r.headers.get("Cache-Control") or ""))
r = client.get("/")
check("HTML home has NO public cache header",
      r.status_code == 200
      and "max-age" not in (r.headers.get("Cache-Control") or ""))
r = client.post("/api/solve", json={"question": "2+2"})
check("API response has NO public cache header",
      "max-age" not in (r.headers.get("Cache-Control") or ""))

# --- Timings table (measured, local code-path cost only) ---------------------
print()
print("Wave-14 measured timings (this machine, local only —")
print("Render's platform cold start is NOT included):")
for label, seconds in timings.items():
    print(f"  {label:42} {ms(seconds)}")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
