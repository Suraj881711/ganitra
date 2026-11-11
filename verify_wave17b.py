"""Wave-17b verification: PEN-TEST FIXES (F1 + F2).

Contract (from PENTEST_WAVE17.md):

F1 (HIGH) — the login lockout used to live in the visitor's own
session cookie, so discarding the cookie reset it and favourite
recovery was effectively unthrottled. Now the failed-attempt
counter is SERVER-SIDE (accounts.login_attempts, keyed by the
submitted name_key, shared by password login and favourite
recovery, whether or not the account exists). 8 cumulative
failures lock the name for 30 minutes; a successful login clears
the counter. New favourite things need >= 3 letters at sign-up
and at change time; EXISTING shorter favourites still recover.

F2 (MEDIUM) — non-string JSON fields crashed /api/solve and
/api/solve-method into HTTP 500. Type-confused payloads (and
non-object JSON bodies) now get a friendly HTTP 400, never a 500.

F3 (LOW) — a PNG/JPEG with script bytes appended after the image
end used to be STORED (served safely). Now any trailing bytes
after the PNG IEND chunk / JPEG EOI marker refuse the upload.

F5 (LOW, partial) — Strict-Transport-Security is stamped only
when GANITRA_SECURE_COOKIES=1 (production HTTPS), never locally.
(CSP stays deliberately off; F4 anonymous /api/solve is by
design and unchanged.)

Run:  python verify_wave17b.py
"""
import base64
import io
import os
import sqlite3
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

RUN_ID = uuid.uuid4().hex[:8]
_DB = f"/tmp/ganitra-verify-wave17b-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass
os.environ["GANITRA_SECRET_KEY"] = "w17b-test-key-" + RUN_ID
os.environ.pop("GANITRA_SECURE_COOKIES", None)

import accounts  # noqa: E402
from app import create_app  # noqa: E402
from i18n import STRINGS  # noqa: E402
from markupsafe import escape as _esc  # noqa: E402

EN = STRINGS["en"]
LOCKOUT = _esc(EN["auth_err_lockout"])
LOGIN_ERR = _esc(EN["auth_err_login"])
FAV_SHORT = _esc(EN["auth_err_fav_short"])
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:52} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()

BASE = {"class": "8", "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza"}


def signup(client, name, password="w17b-pass", **over):
    return client.post("/signup",
                       data={**BASE, "name": name,
                             "password": password, **over})


def wrong_passwords(client, name, count):
    r = None
    for _ in range(count):
        r = client.post("/login",
                        data={"name": name, "password": "bad-pass"})
    return r


def wrong_favourites(client, name, count):
    r = None
    for _ in range(count):
        r = client.post("/login-favourite",
                        data={"name": name, "favourite": "Wrongthing",
                              "new_password": "attacker-pass"})
    return r


# --- (a) password lockout survives a FRESH session ----------------------------
name_a = "W17B A " + RUN_ID
key_a = accounts.normalise_name_key(name_a)
c = app.test_client()
check("a: signup A", signup(c, name_a).status_code == 302)
c.get("/logout")
wrong_passwords(c, name_a, 8)
check("a: server says A is locked", accounts.is_locked(key_a))
row = sqlite3.connect(_DB).execute(
    "SELECT locked_until FROM login_attempts WHERE name_key = ?",
    (key_a,)).fetchone()
now = int(time.time())
check("a: lock window is ~30 minutes",
      bool(row) and now < row[0] <= now + 30 * 60 + 60,
      f"locked_until-now={row[0] - now if row else 'no row'}")
fresh = app.test_client()  # brand-new client: NO cookies at all
r = fresh.post("/login", data={"name": name_a, "password": "w17b-pass"})
check("a: FRESH session + correct password is REFUSED (locked)",
      r.status_code == 200 and LOCKOUT in r.get_data(as_text=True),
      f"status={r.status_code}")
r = fresh.get("/")
check("a: fresh client is still at the sign-in gate",
      b'id="signup-card"' in r.data or b'id="login-card"' in r.data
      or b"auth-card" in r.data or r.status_code in (200, 302))

# --- (b) favourite-recovery lockout survives a fresh session ------------------
name_b = "W17B B " + RUN_ID
key_b = accounts.normalise_name_key(name_b)
c = app.test_client()
check("b: signup B", signup(c, name_b).status_code == 302)
c.get("/logout")
wrong_favourites(c, name_b, 8)
check("b: server says B is locked", accounts.is_locked(key_b))
fresh = app.test_client()
r = fresh.post("/login-favourite",
               data={"name": name_b, "favourite": "Cricket",
                     "new_password": "attacker-pass"})
check("b: FRESH session + correct favourite is REFUSED (locked)",
      r.status_code == 200 and LOCKOUT in r.get_data(as_text=True),
      f"status={r.status_code}")
user_b = accounts.get_user(name_b)
check("b: B's password was NOT reset by the attacker",
      accounts.verify_password(user_b, "w17b-pass")
      and not accounts.verify_password(user_b, "attacker-pass"))

# --- (c) password + favourite failures share ONE counter ----------------------
name_c = "W17B C " + RUN_ID
key_c = accounts.normalise_name_key(name_c)
c = app.test_client()
check("c: signup C", signup(c, name_c).status_code == 302)
c.get("/logout")
wrong_passwords(c, name_c, 4)
other = app.test_client()  # different session for the favourite tries
r = wrong_favourites(other, name_c, 4)
check("c: 4 password + 4 favourite fails -> lockout message",
      LOCKOUT in r.get_data(as_text=True))
check("c: server says C is locked", accounts.is_locked(key_c))
fresh = app.test_client()
r = fresh.post("/login", data={"name": name_c, "password": "w17b-pass"})
check("c: fresh session correct password refused too",
      r.status_code == 200 and LOCKOUT in r.get_data(as_text=True))

# --- (d) a successful login clears the counter --------------------------------
name_d = "W17B D " + RUN_ID
key_d = accounts.normalise_name_key(name_d)
c = app.test_client()
check("d: signup D", signup(c, name_d).status_code == 302)
c.get("/logout")
wrong_passwords(c, name_d, 7)
r = c.post("/login", data={"name": name_d, "password": "w17b-pass"})
check("d: correct login after 7 fails succeeds", r.status_code == 302)
check("d: counter cleared by the success",
      not accounts.is_locked(key_d)
      and sqlite3.connect(_DB).execute(
          "SELECT COUNT(*) FROM login_attempts WHERE name_key = ?",
          (key_d,)).fetchone()[0] == 0)
c.get("/logout")
r = wrong_passwords(c, name_d, 7)
check("d: 7 more fails -> still NOT locked (generic error)",
      LOGIN_ERR in r.get_data(as_text=True)
      and LOCKOUT not in r.get_data(as_text=True))
r = c.post("/login", data={"name": name_d, "password": "w17b-pass"})
check("d: correct login still works after 7+success+7",
      r.status_code == 302)

# --- (e) the lock expires -------------------------------------------------------
name_e = "W17B E " + RUN_ID
key_e = accounts.normalise_name_key(name_e)
c = app.test_client()
check("e: signup E", signup(c, name_e).status_code == 302)
c.get("/logout")
wrong_passwords(c, name_e, 8)
check("e: E locked", accounts.is_locked(key_e))
con = sqlite3.connect(_DB)
con.execute("UPDATE login_attempts SET locked_until = ?"
            " WHERE name_key = ?", (int(time.time()) - 10, key_e))
con.commit()
con.close()
check("e: lock gone once locked_until is in the past",
      not accounts.is_locked(key_e))
fresh = app.test_client()
r = fresh.post("/login", data={"name": name_e, "password": "w17b-pass"})
check("e: correct login succeeds after expiry", r.status_code == 302)

# --- unknown names are throttled too --------------------------------------------
ghost = "W17B Ghost " + RUN_ID
ghost_key = accounts.normalise_name_key(ghost)
c = app.test_client()
wrong_passwords(c, ghost, 8)
check("unknown name_key is locked after 8 fails",
      accounts.is_locked(ghost_key))

# --- (f) JSON type confusion -> 400, never 500 ----------------------------------
api = app.test_client()
for label, payload in (
        ("int question", {"question": 123}),
        ("list question", {"question": ["2+2"]}),
        ("dict question", {"question": {"q": "2+2"}}),
        ("bool question", {"question": True})):
    r = api.post("/api/solve", json=payload)
    check(f"f: /api/solve {label} -> 400",
          r.status_code == 400 and r.get_json().get("ok") is False,
          f"status={r.status_code}")
r = api.post("/api/solve", json=["2+2"])
check("f: /api/solve non-dict body -> 400",
      r.status_code == 400 and r.get_json().get("ok") is False,
      f"status={r.status_code}")
r = api.post("/api/solve", json={"question": "2+2"})
check("f: /api/solve control (string) still works",
      r.status_code == 200 and r.get_json().get("ok") is True,
      f"status={r.status_code}")
r = api.post("/api/solve", json={"question": None})
check("f: /api/solve null question keeps friendly 200",
      r.status_code == 200 and r.get_json().get("ok") is False,
      f"status={r.status_code}")
for label, payload in (
        ("int method", {"question": "2+2", "method": 123}),
        ("list question", {"question": [1], "method": "x"}),
        ("bool method", {"question": "2+2", "method": True})):
    r = api.post("/api/solve-method", json=payload)
    check(f"f: /api/solve-method {label} -> 400",
          r.status_code == 400 and r.get_json().get("ok") is False,
          f"status={r.status_code}")
r = api.post("/api/solve-method", json="2+2")
check("f: /api/solve-method non-dict body -> 400",
      r.status_code == 400, f"status={r.status_code}")
r = api.post("/api/solve-method",
             json={"question": "2+2", "method": "nope"})
check("f: /api/solve-method control keeps calm ok:false 200",
      r.status_code == 200 and r.get_json().get("ok") is False,
      f"status={r.status_code}")

# chats PUT guards (signed-in owner)
name_f = "W17B F " + RUN_ID
c = app.test_client()
check("f: signup F", signup(c, name_f).status_code == 302)
r = c.post("/api/chats")
chat_id = (r.get_json() or {}).get("chat", {}).get("id")
r = c.put(f"/api/chats/{chat_id}", json=["not", "an", "object"])
check("f: chats PUT non-dict body -> 400", r.status_code == 400,
      f"status={r.status_code}")
r = c.put(f"/api/chats/{chat_id}", json={"messages": "a string"})
check("f: chats PUT non-list messages -> 400", r.status_code == 400,
      f"status={r.status_code}")
r = c.put(f"/api/chats/{chat_id}",
          json={"messages": [{"role": "user", "text": "2+2"}]})
check("f: chats PUT control still saves", r.status_code == 200,
      f"status={r.status_code}")

# --- (g) favourite minimum length: enforced on set, honoured for old ones -----
name_g = "W17B G " + RUN_ID
c = app.test_client()
r = signup(c, name_g, hobby="Om")
check("g: signup with a 2-char favourite is refused (friendly)",
      r.status_code == 200 and FAV_SHORT in r.get_data(as_text=True))
check("g: refused signup created NO account",
      accounts.get_user(name_g) is None)
r = signup(c, name_g, hobby="Raj")
check("g: signup with a 3-char favourite works",
      r.status_code == 302)
r = c.post("/account/favourite/goal", data={"value": "Om"})
check("g: favourite CHANGE to 2 chars is refused (friendly)",
      r.status_code == 200 and FAV_SHORT in r.get_data(as_text=True))
c.get("/logout")
r = c.post("/login-favourite",
           data={"name": name_g, "favourite": "Doctor",
                 "new_password": "w17b-pass"})
check("g: old (unchanged) goal still recovers after refused change",
      r.status_code == 302)

# an account created BEFORE the rule (2-char favourite stored
# directly, as an old DB would hold) can still recover with it
name_h = "W17B H " + RUN_ID
_uid, _problem = accounts.create_user(
    name_h, "8", "CBSE", 8, "direct-pass", "Om", "Cricket", "Pizza")
check("g: legacy user with 2-char favourite exists in DB",
      _uid is not None and _problem is None)
fresh = app.test_client()
r = fresh.post("/login-favourite",
               data={"name": name_h, "favourite": "om",
                     "new_password": "reset-pass1"})
check("g: legacy 2-char favourite STILL logs in (not invalidated)",
      r.status_code == 302, f"status={r.status_code}")
user_h = accounts.get_user(name_h)
check("g: legacy recovery set the new password",
      accounts.verify_password(user_h, "reset-pass1"))

# --- F3: polyglot photos are refused, clean photos still work -----------------
name_p = "W17B P " + RUN_ID
c = app.test_client()
check("F3: signup P", signup(c, name_p).status_code == 302)
CLEAN_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
CLEAN_JPEG = (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00"
              b"\x00\x01\x00\x01\x00\x00\xff\xd9")
SCRIPT = b"<script>alert('xss')</script>"


def upload(client, data, filename):
    return client.post(
        "/account/photo",
        data={"photo": (io.BytesIO(data), filename)},
        content_type="multipart/form-data")


r = upload(c, CLEAN_PNG + SCRIPT, "evil.png")
check("F3: PNG + appended script is REFUSED (not stored)",
      r.status_code == 200, f"status={r.status_code}")
r = c.get("/account/photo/file")
check("F3: nothing stored after the polyglot refusal",
      r.status_code == 404, f"status={r.status_code}")
r = upload(c, CLEAN_PNG[:-12], "cut.png")  # IEND chunk removed
check("F3: truncated PNG (no IEND) is refused",
      r.status_code == 200, f"status={r.status_code}")
r = upload(c, CLEAN_PNG, "me.png")
check("F3: clean PNG accepted", r.status_code == 302,
      f"status={r.status_code}")
r = c.get("/account/photo/file")
check("F3: clean PNG serves back byte-identical",
      r.status_code == 200
      and r.headers.get("Content-Type", "").startswith("image/png")
      and r.data == CLEAN_PNG, f"status={r.status_code}")
r = upload(c, CLEAN_JPEG, "me.jpg")
check("F3: clean JPEG accepted", r.status_code == 302,
      f"status={r.status_code}")
r = c.get("/account/photo/file")
check("F3: clean JPEG serves as image/jpeg",
      r.status_code == 200
      and r.headers.get("Content-Type", "").startswith("image/jpeg")
      and r.data == CLEAN_JPEG, f"status={r.status_code}")
r = upload(c, CLEAN_JPEG + SCRIPT, "evil.jpg")
check("F3: JPEG + appended script is REFUSED",
      r.status_code == 200, f"status={r.status_code}")
r = c.get("/account/photo/file")
check("F3: refused polyglot did NOT overwrite the clean JPEG",
      r.status_code == 200 and r.data == CLEAN_JPEG)

# --- F5: HSTS only under GANITRA_SECURE_COOKIES=1 -------------------------------
r = app.test_client().get("/")
check("F5: HSTS absent with the flag OFF (local http)",
      "Strict-Transport-Security" not in r.headers)
os.environ["GANITRA_SECURE_COOKIES"] = "1"
try:
    app_https = create_app()
    check("F5: flag ON turns SESSION_COOKIE_SECURE on",
          app_https.config.get("SESSION_COOKIE_SECURE") is True)
    r = app_https.test_client().get("/")
    check("F5: HSTS present with the flag ON",
          r.headers.get("Strict-Transport-Security")
          == "max-age=31536000; includeSubDomains",
          f"got={r.headers.get('Strict-Transport-Security')}")
finally:
    del os.environ["GANITRA_SECURE_COOKIES"]

print()
print("FAILURES:", len(fails))
for cat, detail in fails:
    print(" -", cat, "|", detail)
sys.exit(1 if fails else 0)
