"""Wave-8 verification: Suraj's FINAL approved logo is wired in.

- static/logo-full.png — ribbon-G monogram + serif "Ganitra" ONLY.
  It is a pure resize of the user-delivered final file
  `Ganitra_Logo_Final.png` (1920x1020: monogram + name, NO "MATHS"
  text — he said "maths ko hata do"). Resize only; the artwork is
  otherwise untouched.
- static/logo-mark.png — tight crop of the monogram alone, used in
  the slim chat top bar next to the HTML "Ganitra" wordmark.
- static/favicon.png — 64x64, monogram on the artwork's cream tone,
  linked from base.html so every page gets it.

The empty state of the chat homepage shows logo-full; the top bar
shows logo-mark. Run with the project venv:  python verify_wave8.py

Wave 12 note (Suraj, 10 Nov 2026): the logo looked "cropped and
pasted" because the artwork sits on its cream background — so the
pages now use TRANSPARENT presentation copies (logo-full-t.png /
logo-mark-t.png, background removed). The originals below stay
byte-identical frozen source files; only the two homepage
filename assertions now point at the -t variants. All disk
geometry checks on the originals are unchanged.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
# Wave 10 rerun note: account names are unique per DB, so
# sign-ups below use a per-run random suffix (RUN_ID) — a
# rerun can never collide with the previous run.
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave8.db"  # Wave 10: FORCE a scratch account DB (assignment, not setdefault — a stray env value must not point these checks at a shared/real DB)
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from PIL import Image  # noqa: E402

from app import create_app  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:44} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
c = app.test_client()
# Wave 10: the chat homepage is login-gated — sign up a test
# student so the logo wiring below is checked on his homepage.
# (The sign-in page itself also carries the logo; asserted in
# verify_wave10.)
c.post("/signup", data={"name": "W8 Tester " + RUN_ID, "class": "8",
                        "board": "CBSE", "goal": "Doctor",
                        "hobby": "Cricket", "favourite": "Pizza",
                        "password": "w8test-pass"})

# --- 1. Asset files on disk ------------------------------------------------
STATIC = Path("static")
for name, min_bytes in (("logo-full.png", 50_000),
                        ("logo-mark.png", 50_000),
                        ("favicon.png", 1_000)):
    p = STATIC / name
    check(f"{name} exists, non-trivial size",
          p.exists() and p.stat().st_size >= min_bytes,
          f"size={p.stat().st_size if p.exists() else 'MISSING'}")

# --- 2. Asset geometry ------------------------------------------------------
full = Image.open(STATIC / "logo-full.png")
mark = Image.open(STATIC / "logo-mark.png")
fav = Image.open(STATIC / "favicon.png")
check("logo-full web width ~900", full.size[0] == 900,
      f"size={full.size}")
check("logo-full cropped above the MATHS line",
      full.size[1] < 540,
      f"height={full.size[1]} (uncropped 900-wide would be 600)")
check("logo-mark square-ish", abs(mark.size[0] - mark.size[1])
      <= 0.25 * max(mark.size), f"size={mark.size}")
check("favicon is 64x64", fav.size == (64, 64), f"size={fav.size}")

# --- 3. Homepage wiring ------------------------------------------------------
r = c.get("/")
body = r.get_data(as_text=True)
check("GET / 200", r.status_code == 200)
check("top bar uses logo-mark", 'class="brand-mark"' in body
      and "logo-mark-t.png" in body)
check("top bar keeps HTML Ganitra wordmark", "> Ganitra</a>" in body)
check("empty state uses logo-full (final-file asset)",
      'class="empty-logo-img"' in body and "logo-full-t.png" in body)
check("rendered logo-full is the verified final file's resize",
      full.size == (900, 478),
      f"size={full.size} (resize of the 1920x1020 final file)")
check("empty state shows logo-full above the greeting",
      body.index("logo-full-t.png") < body.index("empty-greeting"))
check("old empty-state emoji gone", '<div class="empty-logo"'
      ' aria-hidden="true">🧮' not in body)

# --- 4. Static files served ---------------------------------------------------
for name in ("logo-full.png", "logo-mark.png", "favicon.png"):
    r = c.get(f"/static/{name}")
    check(f"/static/{name} served as image", r.status_code == 200
          and r.content_type.startswith("image/")
          and len(r.data) >= 1_000,
          f"status={r.status_code} type={r.content_type} "
          f"bytes={len(r.data)}")

# --- 5. Favicon link on base pages --------------------------------------------
for path in ("/", "/board", "/topics", "/parent-report"):
    r = c.get(path)
    b = r.get_data(as_text=True)
    check(f"favicon link on {path}", 'rel="icon"' in b
          and "favicon.png" in b, f"status={r.status_code}")

# --- 6. CSS hooks ---------------------------------------------------------------
CSS = Path("static/style.css").read_text(encoding="utf-8")
check("css brand-mark height", ".brand-mark" in CSS
      and "height: 30px" in CSS)
check("css empty-logo-img width", ".empty-logo-img" in CSS
      and "min(340px, 70vw)" in CSS)

# --- 7. Other pages keep their text brand (no logo baked in) --------------------
r = c.get("/board")
b = r.get_data(as_text=True)
check("/board keeps text brand, no logo images",
      "logo-full.png" not in b and "logo-mark.png" not in b)

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
