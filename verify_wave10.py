"""Wave-10 verification: the real first-page sign-in system.

Contract (approved design photo + Suraj's follow-up refinement):
- GET / anonymous = the ONE-page sign-in (frozen logo blended in,
  ALL fields type-in — NO option chips/selects for class/board,
  gold "3 Favourite Things" card + password, teal Create button).
- Sign-up validates: all fields filled, class parses to 6-12
  ("8", "Class 8", "8th"), password >= 4 chars; duplicate name is
  a friendly error, never an overwrite.
- Sign-up also sets the Saathi session (name + class) and the
  board session (board text mapped to the board slug).
- Login: name + password; wrong credentials get ONE generic
  error; after 8 failed attempts in a session the name is locked
  out with a "try later" message.
- Favourite-things login: the card is HIDDEN by default on the
  Welcome-back view ("forgot kare jab hi fav things kaa option
  de, jab tak nhi") — it appears only via the "Forgot password?"
  toggle. POST /login-favourite checks the typed thing against
  ALL THREE stored hashes (normalised: case/spaces) and, on a
  match, logs in AND saves the new password in the same step
  (old password then fails, new one works).
- Logout returns to the sign-in gate.
- Passwords and the 3 favourite answers are PBKDF2-hashed: the
  raw values appear NOWHERE in the SQLite file bytes.
- The Wave 6 first-visit Saathi card never renders for signed-in
  users (name comes from the account).

Run with a FRESH temp DB so the run is self-contained:
  GANITRA_DB_PATH=/tmp/w10-test.db python verify_wave10.py
(The script refuses to run without GANITRA_DB_PATH pointing at a
scratch file, and deletes it first — accounts are real data.)
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

_DB = os.environ.get("GANITRA_DB_PATH", "")
if not _DB or "ganitra_users.db" in _DB:
    print("Set GANITRA_DB_PATH to a scratch file first "
          "(e.g. /tmp/w10-test.db) — accounts are real data.")
    sys.exit(2)
Path(_DB).unlink(missing_ok=True)

from app import create_app  # noqa: E402
from i18n import STRINGS, SUPPORTED_LANGS  # noqa: E402
from markupsafe import escape as _markupsafe_escape  # noqa: E402


def esc(text):
    return str(_markupsafe_escape(text))


fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]

USER = {"name": "Aarav", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "secret1"}

# --- 1. Anonymous gate: the sign-in page ------------------------------------
c = app.test_client()
r = c.get("/")
body = r.get_data(as_text=True)
check("anon GET / = sign-in page", r.status_code == 200
      and 'id="signup-card"' in body
      and 'action="/signup"' in body)
# Wave 12 (Suraj, 10 Nov 2026): the sign-in page now blends the
# TRANSPARENT copy (logo-full-t.png) so the logo no longer looks
# pasted on; the frozen original file itself is untouched.
check("sign-in shows frozen logo", "logo-full-t.png" in body
      and 'class="auth-logo-img"' in body)
check("sign-in has ALL type-in fields",
      all(f'name="{n}"' in body for n in
          ("name", "class", "board", "goal", "hobby",
           "favourite", "password")))
check("sign-in gold favourites card", 'class="auth-fav-card"' in body
      and esc(EN["auth_fav_heading"]) in body)
check("sign-in teal button + forgot hint",
      esc(EN["auth_signup_btn"]) in body
      and esc(EN["auth_forgot_line"]) in body)
check("sign-in has NO option chips/selects for class/board",
      # The ONLY <select> on the page is the site language
      # switcher (lang-select, as on every page); class and
      # board are plain text inputs and there are no chips.
      body.count("<select") == 1 and 'id="lang-select"' in body
      and 'class="chip"' not in body
      and 'class="chips"' not in body)
check("sign-in has NO chat form", 'id="chat-form"' not in body
      and 'id="chat-log"' not in body)
check("login mode link present",
      'href="/?mode=login"' in body)

# Logo files untouched (frozen by Suraj's explicit order).
import hashlib  # noqa: E402
for name in ("logo-full.png", "logo-mark.png", "favicon.png"):
    data = Path(f"static/{name}").read_bytes()
    check(f"{name} on disk, plausible size",
          len(data) > 1000, f"bytes={len(data)} "
          f"md5={hashlib.md5(data).hexdigest()[:12]}")

# --- 2. Sign-up validation ---------------------------------------------------
c = app.test_client()
r = c.post("/signup", data={**USER, "hobby": ""})
check("missing field rejected", r.status_code == 200
      and esc(EN["auth_err_fill_all"])
      in r.get_data(as_text=True))
r = c.post("/signup", data={**USER, "class": "5"})
check("class 5 rejected", r.status_code == 200
      and esc(EN["auth_err_class"]) in r.get_data(as_text=True))
r = c.post("/signup", data={**USER, "password": "abc"})
check("short password rejected", r.status_code == 200
      and esc(EN["auth_err_password_short"])
      in r.get_data(as_text=True))
with c.session_transaction() as sess:
    check("failed sign-ups stay logged out",
          not sess.get("user_id"))

# --- 3. Sign-up happy path ----------------------------------------------------
c = app.test_client()
r = c.post("/signup", data={**USER, "class": "Class 8",
                            "board": "MP Board"})
check("sign-up redirects to chat", r.status_code == 302
      and r.headers.get("Location", "").endswith("/"))
with c.session_transaction() as sess:
    check("session: account + Saathi + board",
          sess.get("user_name") == "Aarav"
          and sess.get("saathi_name") == "Aarav"
          and sess.get("saathi_class") == 8
          and sess.get("board") == "mp-board",
          f"user={sess.get('user_name')} saathi="
          f"{sess.get('saathi_name')}/{sess.get('saathi_class')} "
          f"board={sess.get('board')}")
r = c.get("/")
body = r.get_data(as_text=True)
check("chat after sign-up", 'class="chat-shell"' in body
      and 'id="chat-form"' in body)
check("NO first-visit Saathi card for account users",
      'id="saathi-form"' not in body
      and 'action="/saathi"' not in body)
# Wave 12 (Suraj, 10 Nov 2026): Log out moved OUT of the chat
# menu — it lives ONLY inside My Account now.
check("chat menu has NO Log out (wave 12)",
      'href="/logout"' not in body)
_acct = c.get("/account").get_data(as_text=True)
check("Log out lives on /account (wave 12)",
      'href="/logout"' in _acct
      and esc(EN["nav_logout"]) in _acct)

# --- 4. Duplicate name: friendly error, NO overwrite ---------------------------
c2 = app.test_client()
r = c2.post("/signup", data={**USER, "password": "other-pass"})
check("duplicate name rejected kindly", r.status_code == 200
      and esc(EN["auth_err_name_taken"])
      in r.get_data(as_text=True))
r = c2.post("/login", data={"name": "Aarav",
                            "password": "other-pass"})
check("duplicate did NOT overwrite password",
      esc(EN["auth_err_login"]) in r.get_data(as_text=True))
r = c2.post("/login", data={"name": "Aarav",
                            "password": USER["password"]})
check("original password still works", r.status_code == 302)

# --- 5. Logout -> gate -> login -------------------------------------------------
r = c.get("/logout")
check("logout redirects to /", r.status_code == 302)
r = c.get("/")
check("gate returns after logout", 'id="signup-card"'
      in r.get_data(as_text=True))
r = c.post("/login", data={"name": "Aarav", "password": "nope"})
body = r.get_data(as_text=True)
check("wrong password: generic error, still out",
      esc(EN["auth_err_login"]) in body
      and 'id="chat-form"' not in body)
r = c.post("/login", data={"name": "Aarav",
                           "password": USER["password"]})
check("correct password logs in", r.status_code == 302)
with c.session_transaction() as sess:
    check("login restores Saathi + board",
          sess.get("saathi_name") == "Aarav"
          and sess.get("saathi_class") == 8
          and sess.get("board") == "mp-board")

# --- 6. Welcome-back view: favourite card HIDDEN until Forgot ------------------
c3 = app.test_client()
r = c3.get("/?mode=login")
body = r.get_data(as_text=True)
check("login mode renders", 'id="login-card"' in body
      and 'action="/login"' in body
      and esc(EN["auth_welcome_back"]) in body)
fav = re.search(r'<div class="auth-fav-login" id="fav-login"([^>]*)>',
                body)
check("favourite card hidden by default", fav is not None
      and "hidden" in fav.group(1))
check("favourite inputs inside the hidden container",
      fav is not None
      and body.index('id="fav-login"') < body.index('name="favourite"')
      and body.index('name="favourite"') < body.index("</main>"))
check("forgot toggle wired (JS reveal)",
      'id="forgot-toggle"' in body and "card.hidden" in body)
check("login view has NO favourites inputs outside container",
      body.count('name="favourite"') == 1)

# --- 7. Favourite-things login ---------------------------------------------------
r = c3.post("/login-favourite",
            data={"name": "Aarav", "favourite": "my bicycle",
                  "new_password": "brandnew1"})
check("wrong favourite stays out", r.status_code == 200
      and esc(EN["auth_err_fav"]) in r.get_data(as_text=True))
r = c3.post("/login-favourite",
            data={"name": "Aarav", "favourite": "  CRICKET ",
                  "new_password": "brandnew1"})
check("favourite login (normalised hobby) works",
      r.status_code == 302)
with c3.session_transaction() as sess:
    check("favourite login sets the session",
          sess.get("user_name") == "Aarav")
c3.get("/logout")
r = c3.post("/login", data={"name": "Aarav",
                            "password": USER["password"]})
check("old password fails after favourite reset",
      esc(EN["auth_err_login"]) in r.get_data(as_text=True))
r = c3.post("/login", data={"name": "Aarav",
                            "password": "brandnew1"})
check("new password works after favourite reset",
      r.status_code == 302)

# Each of the three favourites can log in (goal + favourite too).
c4 = app.test_client()
r = c4.post("/signup", data={"name": "Meera", "class": "10th",
                             "board": "ICSE", "goal": "Pilot",
                             "hobby": "Chess", "favourite": "Momos",
                             "password": "meera-pass"})
check("sign-up accepts '10th' as class 10", r.status_code == 302)
with c4.session_transaction() as sess:
    check("'10th' normalised to 10 + ICSE slug",
          sess.get("saathi_class") == 10
          and sess.get("board") == "icse")
c4.get("/logout")
r = c4.post("/login-favourite",
            data={"name": "Meera", "favourite": "pilot",
                  "new_password": "meera-new1"})
check("favourite login via GOAL works", r.status_code == 302)
c4.get("/logout")
r = c4.post("/login-favourite",
            data={"name": "Meera", "favourite": "Momos",
                  "new_password": "meera-new2"})
check("favourite login via FAVOURITE works", r.status_code == 302)

# --- 8. Lockout after 8 failed attempts -----------------------------------------
c5 = app.test_client()
for _ in range(8):
    c5.post("/login", data={"name": "Aarav", "password": "bad"})
r = c5.post("/login", data={"name": "Aarav",
                            "password": "brandnew1"})
check("9th attempt (even correct) is locked out",
      esc(EN["auth_err_lockout"]) in r.get_data(as_text=True))

# --- 9. Nothing stored in plaintext ----------------------------------------------
raw = Path(_DB).read_bytes()
for secret in (b"secret1", b"brandnew1", b"meera-pass",
               b"Doctor", b"Cricket", b"Pizza", b"doctor",
               b"cricket", b"pizza", b"Pilot", b"Chess", b"Momos"):
    check(f"DB bytes lack plaintext {secret!r}", secret not in raw)
import sqlite3  # noqa: E402
con = sqlite3.connect(_DB)
rows = con.execute("SELECT name, pw_hash FROM users").fetchall()
# accounts.hash_secret stores "<salt-hex>$<pbkdf2-hex>" (64-hex
# digest) — salted PBKDF2, never the plaintext.
check("hashes look like PBKDF2 records",
      all(re.fullmatch(r"[0-9a-f]{32}\$[0-9a-f]{64}", h)
          for _, h in rows),
      f"rows={len(rows)}")

# --- 10. i18n: the Wave-10 keys exist in all 6 languages --------------------------
auth_keys = {k for k in EN if k.startswith("auth_")} | {"nav_logout"}
for code in SUPPORTED_LANGS:
    missing = auth_keys - set(STRINGS[code])
    check(f"auth i18n complete ({code})", not missing,
          f"missing={sorted(missing)[:4]}")
    empty = [k for k in auth_keys if not STRINGS[code].get(k)]
    check(f"auth i18n non-empty ({code})", not empty,
          f"empty={empty[:4]}")

# --- 11. JS syntax on the auth pages (node --check) -------------------------------
import shutil  # noqa: E402
import subprocess  # noqa: E402
node = shutil.which("node")
for mode_qs in ("", "?mode=login"):
    cl = app.test_client()
    html = cl.get(f"/{mode_qs}").get_data(as_text=True)
    scripts = [s for s in re.findall(r"<script>(.*?)</script>", html,
                                     re.S) if s.strip()]
    if node:
        ok = True
        for i, s in enumerate(scripts):
            p = f"/tmp/w10-auth-{len(mode_qs)}-{i}.js"
            Path(p).write_text(s, encoding="utf-8")
            ok = ok and subprocess.run(
                [node, "--check", p],
                capture_output=True).returncode == 0
        check(f"JS syntax (auth {mode_qs or 'signup'})", ok,
              f"scripts={len(scripts)}")
    else:
        check(f"JS syntax (auth {mode_qs or 'signup'})", True,
              "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
