"""Wave-12 verification: the menu-inside package + My Account +
multi-method answers + Teach me + the all-device pass.

Contract (Suraj's approved designs, 10 Nov 2026):
- The chat ☰ menu is a FULL-PAGE overlay: profile block (photo or
  logo-mark, name + ✓, "Class N Student", board line, "Ganitra
  Maths") linking to /account; blue-number stats lines filled
  from /account/stats.json; bold items Your chats / Board Mode /
  Practice Test / Topics / Mistake Notebook / Copy Style /
  Parent Report; Language as an expanding row; a Settings row
  (-> /account); a gold "Keep learning, keep shining" strip.
  NO Log out in the menu, NO History link in the menu.
- My Account (/account): photo upload/change/remove (PNG/JPEG,
  <= 2 MB, magic bytes), profile edit (name/class/board — a name
  change renames the LOGIN too and is refused when taken),
  write-only favourite changes (current values never shown),
  password change guarded by the current password, and the ONLY
  Log out link. Another account sees none of it.
- Multi-method: a question is solved ONE way first; genuinely
  different extra methods ride in the /api/solve response
  ("methods") and the classic answer page, with "Teach me"
  concept lines ("teach") beside them. POST /api/solve-method
  re-serves one method by id.
- Sizes/look: composer padding 10px (wave 21 comfort; was the
  wave-12 slim 5px), small gold method
  chips (13px), PLAIN white sign-in boxes, and TRANSPARENT logo
  variants (logo-full-t.png / logo-mark-t.png) on the pages —
  the frozen originals stay byte-identical.
- All devices: viewport meta everywhere via base.html, a
  min-width 900px chats-grid 3-column rule, the menu overlay's
  desktop max-width column, account inputs >= 16px.

Run:  python verify_wave12.py
(The script forces its own scratch account DB, like waves 7-11,
and uses a per-run random name suffix — account names are
unique, so a rerun can never collide with the previous run.)
"""
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
# FORCE a scratch account DB (assignment, not setdefault — a
# stray env value must not point these checks at a real DB).
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave12.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from PIL import Image  # noqa: E402

from app import create_app  # noqa: E402
from i18n import STRINGS, SUPPORTED_LANGS  # noqa: E402
from markupsafe import escape as esc  # noqa: E402
from solver.methods import alternate_methods  # noqa: E402
from solver.router import solve_question  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]
CSS = Path("static/style.css").read_text(encoding="utf-8")

NEW_KEYS = {k for k in EN if k.startswith(("acct_", "mm_", "field_"))}
NEW_KEYS |= {"menu_keep_line", "menu_settings", "menu_language",
             "menu_copy_style", "menu_your_chats", "menu_new_here"}

# --- 1. i18n completeness -------------------------------------------------
for code in SUPPORTED_LANGS:
    missing = NEW_KEYS - set(STRINGS[code])
    check(f"wave12 keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
    empty = [k for k in NEW_KEYS if not STRINGS[code].get(k)]
    check(f"wave12 keys non-empty ({code})", not empty,
          f"empty={empty}")
en_keys = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n fully complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")


def _signup(client, name, password="w12test-pass", **over):
    data = {"name": name, "class": "8", "board": "CBSE",
            "goal": "Doctor", "hobby": "Cricket",
            "favourite": "Pizza", "password": password}
    data.update(over)
    return client.post("/signup", data=data)


NAME_A = "W12 Aarav " + RUN_ID
NAME_A2 = "W12 Aarav Kumar " + RUN_ID
NAME_B = "W12 Meera " + RUN_ID

# --- 2. Anonymous lockout ---------------------------------------------------
anon = app.test_client()
r = anon.get("/account")
check("anon /account redirects to gate", r.status_code == 302,
      f"status={r.status_code}")
r = anon.get("/account/stats.json")
check("anon stats.json -> 401", r.status_code == 401)
r = anon.get("/account/photo/file")
check("anon photo file -> redirect (no photo)",
      r.status_code in (302, 404), f"status={r.status_code}")
for path in ("/account/profile", "/account/favourite/goal",
             "/account/password", "/account/photo",
             "/account/photo/delete"):
    r = anon.post(path, data={"name": "X", "class": "8",
                              "board": "CBSE", "value": "Y",
                              "old_password": "a",
                              "new_password": "bbbb"})
    check(f"anon POST {path} not a success page",
          r.status_code in (302, 401, 404)
          and 'class="acct-wrap"' not in r.get_data(as_text=True),
          f"status={r.status_code}")
r = anon.get("/")
check("anon / is the sign-in page",
      'id="signup-card"' in r.get_data(as_text=True))

# --- 3. Account page basics ---------------------------------------------------
a = app.test_client()
_signup(a, NAME_A)
r = a.get("/account")
body = r.get_data(as_text=True)
check("/account renders 200", r.status_code == 200)
check("account shows name + class + board",
      esc(NAME_A) in body and 'value="8"' in body
      and 'value="CBSE"' in body)
check("account heading + logout link",
      esc(EN["acct_heading"]) in body
      and 'href="/logout"' in body
      and esc(EN["nav_logout"]) in body)
check("account photo row present",
      'class="acct-photo"' in body
      and 'action="/account/photo"' in body)
check("account shows NO favourite values",
      "Doctor" not in body and "Cricket" not in body
      and "Pizza" not in body)
check("account shows NO password",
      "w12test-pass" not in body)
check("account menu has NO logout",
      body.count('href="/logout"') == 1)

# --- 4. Profile edit ------------------------------------------------------------
r = a.post("/account/profile",
           data={"name": NAME_A, "class": "9", "board": "MP Board"})
check("profile edit redirects saved", r.status_code == 302
      and "saved=1" in r.headers.get("Location", ""))
body = a.get("/account").get_data(as_text=True)
check("profile edit: class + board updated",
      'value="9"' in body and 'value="MP Board"' in body)
board_body = a.get("/board").get_data(as_text=True)
check("profile edit: board slug follows (MP Board active)",
      'board-opt active' in board_body
      and "Madhya Pradesh" in board_body
      or "MP Board" in board_body)
r = a.post("/account/profile",
           data={"name": NAME_A, "class": "5", "board": "MP Board"})
check("profile edit: class 5 refused with error",
      r.status_code == 200
      and esc(EN["auth_err_class"]) in r.get_data(as_text=True))

# --- 5. Rename ------------------------------------------------------------------
b = app.test_client()
_signup(b, NAME_B, password="w12meera-pass")
r = a.post("/account/profile",
           data={"name": NAME_B, "class": "9", "board": "MP Board"})
check("rename to a taken name refused",
      r.status_code == 200
      and esc(EN["auth_err_name_taken"])
      in r.get_data(as_text=True))
body = a.get("/account").get_data(as_text=True)
check("name unchanged after refused rename", esc(NAME_A) in body)
r = a.post("/account/profile",
           data={"name": NAME_A2, "class": "9", "board": "MP Board"})
check("rename to a fresh name works", r.status_code == 302)
a.get("/logout")
r = a.post("/login", data={"name": NAME_A,
                           "password": "w12test-pass"})
check("OLD name login fails after rename",
      esc(EN["auth_err_login"]) in r.get_data(as_text=True))
r = a.post("/login", data={"name": NAME_A2,
                           "password": "w12test-pass"})
check("NEW name login works after rename", r.status_code == 302)

# --- 6. Favourite change ----------------------------------------------------------
r = a.post("/account/favourite/goal", data={"value": "Pilot"})
check("favourite change redirects saved", r.status_code == 302)
a.get("/logout")
r = a.post("/login-favourite",
           data={"name": NAME_A2, "favourite": "Doctor",
                 "new_password": "w12test-pass"})
check("OLD goal no longer logs in",
      esc(EN["auth_err_fav"]) in r.get_data(as_text=True))
r = a.post("/login-favourite",
           data={"name": NAME_A2, "favourite": "pilot",
                 "new_password": "w12test-pass"})
check("NEW goal logs in (normalised)", r.status_code == 302)

# --- 7. Password change --------------------------------------------------------------
r = a.post("/account/password",
           data={"old_password": "wrong-old",
                 "new_password": "w12new-pass"})
check("wrong current password refused",
      r.status_code == 200
      and esc(EN["acct_err_password_wrong"])
      in r.get_data(as_text=True))
r = a.post("/account/password",
           data={"old_password": "w12test-pass",
                 "new_password": "ab"})
check("short new password refused",
      esc(EN["auth_err_password_short"])
      in r.get_data(as_text=True))
r = a.post("/account/password",
           data={"old_password": "w12test-pass",
                 "new_password": "w12new-pass"})
check("password change works", r.status_code == 302)
a.get("/logout")
r = a.post("/login", data={"name": NAME_A2,
                           "password": "w12test-pass"})
check("old password fails after change",
      esc(EN["auth_err_login"]) in r.get_data(as_text=True))
r = a.post("/login", data={"name": NAME_A2,
                           "password": "w12new-pass"})
check("new password works after change", r.status_code == 302)

# --- 8. Photo --------------------------------------------------------------------------
buf = io.BytesIO()
Image.new("RGB", (24, 24), (47, 125, 110)).save(buf, format="PNG")
PNG_BYTES = buf.getvalue()
r = a.post("/account/photo",
           data={"photo": (io.BytesIO(PNG_BYTES), "me.png")},
           content_type="multipart/form-data")
check("photo upload redirects saved", r.status_code == 302)
r = a.get("/account/photo/file")
check("photo file serves image/png", r.status_code == 200
      and r.content_type.startswith("image/png")
      and r.data[:8] == PNG_BYTES[:8]
      and r.headers.get("Cache-Control") == "private",
      f"status={r.status_code} type={r.content_type}")
home = a.get("/").get_data(as_text=True)
check("menu profile uses the uploaded photo",
      "/account/photo/file" in home)
r = a.post("/account/photo",
           data={"photo": (io.BytesIO(b"not an image at all"),
                           "x.png")},
           content_type="multipart/form-data")
check("non-image upload refused with friendly error",
      r.status_code == 200
      and esc(EN["acct_err_photo_type"])
      in r.get_data(as_text=True))
r = a.post("/account/photo/delete")
check("photo delete redirects", r.status_code == 302)
r = a.get("/account/photo/file")
check("photo gone after delete -> 404", r.status_code == 404)

# --- 9. Ownership ----------------------------------------------------------------------
r = b.get("/account/photo/file")
check("other account photo file -> 404", r.status_code == 404)
body_b = b.get("/account").get_data(as_text=True)
check("other account page shows only its own data",
      esc(NAME_B) in body_b and esc(NAME_A2) not in body_b)

# --- 10. Menu + stats ---------------------------------------------------------------------
home = a.get("/").get_data(as_text=True)
check("menu: profile block", 'class="menu-profile"' in home
      and esc(NAME_A2) in home and "menu-photo" in home)
check("menu: class + board lines",
      esc(EN["acct_student_line"].format(**{"class": 9})) in home
      and "MP Board" in home
      and esc(EN["acct_verified_line"]) in home)
check("menu: stats span ids", 'id="menu-stat-questions"' in home
      and 'id="menu-stat-chats"' in home
      and "/account/stats.json" in home)
_dd = home[home.index('class="nav-dropdown'):]
_dd = _dd[:_dd.index("</nav>")]
for href in ("/chats", "/board", "/practice", "/topics",
             "/mistakes", "/parent-report", "/account"):
    check(f"menu item {href}", f'href="{href}"' in _dd)
check("menu: Copy Style item", "/solution/print?style=hand" in _dd)
check("menu: NO language row (Suraj's auto-language rule, 12 Nov 2026)",
      _dd.count("/set-lang/") == 0)
check("menu: Settings row", esc(EN["menu_settings"]) in _dd
      and 'href="/account"' in _dd)
check("menu: gold strip line",
      esc(EN["menu_keep_line"]) in _dd)
check("menu: NO logout anywhere on chat page",
      'href="/logout"' not in home)
check("menu: NO history link inside the menu",
      'href="/history"' not in _dd)

cid = (a.post("/api/chats").get_json() or {}).get("chat", {}).get("id")
thread = [
    {"role": "user", "text": "2+2"},
    {"role": "bot", "data": {"ok": True, "_q": "2+2",
                             "result": {"answer": "4"}}},
    {"role": "user", "text": "3+3"},
    {"role": "bot", "data": {"ok": True, "_q": "3+3",
                             "result": {"answer": "6"}}},
]
a.put(f"/api/chats/{cid}", json={"messages": thread})
d = a.get("/account/stats.json").get_json() or {}
check("stats.json counts questions + chats",
      d.get("ok") is True and d.get("questions", 0) >= 2
      and d.get("chats", 0) >= 1, f"stats={d}")

# --- 11. Multi-method units ---------------------------------------------------------------
res = solve_question("x^2 - 5x + 6 = 0")
ms = alternate_methods("x^2 - 5x + 6 = 0", res)
ids = [m["id"] for m in ms]
check("quadratic: factor + complete_square + graph",
      "factor" in ids and "complete_square" in ids
      and "graph" in ids, f"ids={ids}")
check("quadratic: every method agrees + has steps",
      all(m["steps"] and "2" in m["answer"] and "3" in m["answer"]
          for m in ms))
res = solve_question("2*x + 3 = 7")
ms = alternate_methods("2*x + 3 = 7", res)
# Wave 13 (Suraj's directive, 10 Nov 2026: "Question ke method
# badane hai" — more methods per question): the linear family
# gained the transposition method ahead of the graph method.
check("linear: transposition + graph methods, answer 2",
      [m["id"] for m in ms] == ["transposition", "graph"]
      and all("2" in m["answer"] for m in ms))
res = solve_question("15% of 240")
ms = alternate_methods("15% of 240", res)
# Wave 13 (same directive): the percentage family gained the
# proportion method alongside fraction + unitary.
check("percent: fraction + unitary + proportion, answer 36",
      {m["id"] for m in ms} == {"fraction", "unitary",
                                "proportion"}
      and all("36" in m["answer"] for m in ms))
check("single-method question gets none",
      alternate_methods("2+2", solve_question("2+2")) == [])
check("gibberish never crashes methods",
      isinstance(alternate_methods(
          "asdf qwer", solve_question("asdf qwer")), list))

# --- 12. API: solve + solve-method ---------------------------------------------------------
r = a.post("/api/solve", json={"question": "x^2 - 5x + 6 = 0"})
d = r.get_json() or {}
check("/api/solve carries methods>=2 + teach",
      d.get("ok") is True and len(d.get("methods") or []) >= 2
      and len(d.get("teach") or []) >= 3)
r = a.post("/api/solve-method",
           json={"question": "x^2 - 5x + 6 = 0", "method": "factor"})
d = r.get_json() or {}
check("/api/solve-method factor ok with steps",
      d.get("ok") is True
      and (d.get("method") or {}).get("id") == "factor"
      and len((d.get("method") or {}).get("steps") or []) >= 3)
r = a.post("/api/solve-method",
           json={"question": "x^2 - 5x + 6 = 0", "method": "bogus"})
check("/api/solve-method bogus id -> ok:false",
      (r.get_json() or {}).get("ok") is False)

# --- 13. Classic answer page ------------------------------------------------------------------
r = a.post("/solve", data={"question": "x^2 - 5x + 6 = 0"})
body = r.get_data(as_text=True)
check("classic page: methods block + factor label",
      esc(EN["mm_more"]) in body and "Factorisation" in body
      and 'class="methods-block"' in body)
check("classic page: teach lines present",
      'class="teach-block"' in body and "balance" in body)

# --- 14. Chips / sizes / plain boxes (CSS) ------------------------------------------------------
bar = re.search(r"body\.chat-page \.chat-bar \{([^}]*)\}", CSS)
check("composer bar comfortable (padding 10px, wave 21)",
      bar is not None and "padding: 10px" in bar.group(1))
chip = re.search(r"\.method-chip \{([^}]*)\}", CSS)
check("method chips are small (13px)",
      chip is not None and "font-size: 13px" in chip.group(1))
auth_input = re.search(r"\.auth-input \{([^}]*)\}", CSS)
check("auth inputs PLAIN white (no teal tint)",
      auth_input is not None
      and "background: #fff" in auth_input.group(1)
      and "#dcefe9" not in auth_input.group(1))
fav_card = re.search(r"\.auth-fav-card \{([^}]*)\}", CSS)
check("favourites card PLAIN (no gold gradient)",
      fav_card is not None and "faf0d7" not in fav_card.group(1)
      and "linear-gradient" not in fav_card.group(1))

# --- 15. Transparent logo variants --------------------------------------------------------------
for name, orig in (("logo-full-t.png", "logo-full.png"),
                   ("logo-mark-t.png", "logo-mark.png")):
    p = Path(f"static/{name}")
    check(f"{name} exists", p.exists())
    if p.exists():
        im = Image.open(p)
        o = Image.open(f"static/{orig}")
        check(f"{name} is RGBA with clear corners",
              im.mode == "RGBA"
              and im.getpixel((2, 2))[3] == 0)
        alpha = im.getchannel("A")
        check(f"{name} artwork still opaque somewhere",
              alpha.getextrema()[1] == 255)
        check(f"{name} same size as its original",
              im.size == o.size, f"{im.size} vs {o.size}")
for name, want in (("logo-full.png", "8ffea6f4e42d3d3b1bd8552e26579c4c"),
                   ("logo-mark.png", "5a190086234946460217a93148632125"),
                   ("favicon.png", "b4cfd43b46177c4da51a24d60b326771")):
    got = hashlib.md5(Path(f"static/{name}").read_bytes()).hexdigest()
    check(f"FROZEN {name} md5 unchanged", got == want, f"md5={got}")
check("pages reference the -t logos",
      "logo-full-t.png" in home and "logo-mark-t.png" in home)

# --- 16. Responsive / all-device ------------------------------------------------------------------
for path in ("/", "/account", "/chats", "/board"):
    b = a.get(path).get_data(as_text=True)
    check(f"viewport meta on {path}",
          'name="viewport"' in b
          and "width=device-width" in b)
check("CSS: small-phone media query exists",
      "@media (max-width: 560px)" in CSS)
grid900 = re.search(r"@media \(min-width: 900px\) \{([^@]*)\}", CSS)
check("CSS: >=900px chats grid goes 3 columns",
      grid900 is not None
      and ".chats-grid" in grid900.group(1)
      and "1fr 1fr 1fr" in grid900.group(1))
check("CSS: menu overlay inner column capped + centred",
      ".menu-panel-inner" in CSS and "max-width: 640px" in CSS
      and ".nav-menu[open] .nav-dropdown" in CSS
      and "position: fixed" in CSS)
w12 = CSS[CSS.index("/* Wave 12"):] if "/* Wave 12" in CSS else ""
# Breakpoint values inside @media queries aren't widths; drop
# them before scanning for fixed container widths.
w12_q = re.sub(r"@media \([^)]*\)", "", w12)
wide = [int(n) for n in re.findall(r"(?<!max-)width:\s*(\d+)px",
                                   w12_q)]
check("CSS: no Wave-12 fixed width over 430px",
      all(n <= 430 for n in wide), f"widths={sorted(set(wide))}")
acct_input = re.search(r"\.acct-input \{([^}]*)\}", CSS)
check("account inputs >= 16px (iOS zoom guard)",
      acct_input is not None
      and "font-size: 16px" in acct_input.group(1)
      and "min-height: 44px" in acct_input.group(1))
check("CSS: photos are circles with object-fit cover",
      "object-fit: cover" in CSS and ".acct-photo" in CSS
      and ".menu-photo" in CSS)
check("CSS: long maths wraps (overflow-wrap anywhere)",
      "overflow-wrap: anywhere" in CSS)

# --- 17. JS syntax (node --check) ---------------------------------------------------------------------
node = shutil.which("node")
for label, path, client in (("home", "/", a),
                            ("chats", "/chats", a),
                            ("account", "/account", a)):
    html = client.get(path).get_data(as_text=True)
    scripts = [s for s in re.findall(r"<script>(.*?)</script>", html,
                                     re.S) if s.strip()]
    if node:
        ok = True
        for i, s in enumerate(scripts):
            p = f"/tmp/w12-{label}-{i}.js"
            Path(p).write_text(s, encoding="utf-8")
            ok = ok and subprocess.run(
                [node, "--check", p],
                capture_output=True).returncode == 0
        check(f"JS syntax ({label})", ok, f"scripts={len(scripts)}")
    else:
        check(f"JS syntax ({label})", True,
              "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
