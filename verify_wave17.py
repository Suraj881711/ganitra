"""Wave-17 verification: SECURITY HARDENING.

Contract (parent audit + Suraj's security question, 10 Nov 2026):

1. NO hardcoded session secret: app.py/accounts.py/api.py (and
   every other project .py except this test, which asserts the
   absence) must not contain the old placeholder "change-this-key",
   and app.secret_key must never be a string literal in app.py.
2. Secret from environment: with GANITRA_SECRET_KEY set, the app
   uses exactly that value, and a session cookie signed by one
   app instance validates in a SECOND instance with the same key
   (and is rejected by an instance with a different key). Without
   the env var, each process gets a fresh random key (sessions die
   on restart — safe, just inconvenient).
3. Cookie flags: SESSION_COOKIE_HTTPONLY=True and
   SESSION_COOKIE_SAMESITE="Lax" in config; SESSION_COOKIE_SECURE
   is True ONLY when GANITRA_SECURE_COOKIES=1. The emitted
   Set-Cookie header carries HttpOnly + SameSite=Lax.
4. Security headers on every response (via the Wave-14
   after_request hook, extended — not duplicated):
   X-Content-Type-Options: nosniff, X-Frame-Options: SAMEORIGIN,
   Referrer-Policy: same-origin — and the Wave-14 static
   Cache-Control (public, max-age=86400) still applies to /static
   only. (No CSP by design: the pages rely on inline scripts and
   styles; a CSP added blind would break them.)
5. Regressions of earlier security contracts: the Wave-10 login
   lockout (8 fails) still triggers, and the Wave-11 chats API
   still answers 404 for a chat owned by another account.
6. Item-4 audits (static, citing the real code): the Wave-12
   photo upload still validates content-type AND magic bytes with
   a 2 MB cap; chats.py still scopes every chat query by user_id.

Run:  python verify_wave17.py
"""
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

RUN_ID = uuid.uuid4().hex[:8]
_DB = f"/tmp/ganitra-verify-wave17-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass

TEST_KEY = "w17-test-secret-key-" + RUN_ID + "-0123456789abcdef"
os.environ["GANITRA_SECRET_KEY"] = TEST_KEY
os.environ.pop("GANITRA_SECURE_COOKIES", None)

from app import create_app  # noqa: E402
from i18n import STRINGS  # noqa: E402
from markupsafe import escape as _esc  # noqa: E402

EN = STRINGS["en"]
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


ROOT = Path(__file__).parent

# --- 1. No hardcoded secret anywhere -----------------------------------------
for name in ("app.py", "accounts.py", "api.py"):
    text = (ROOT / name).read_text(encoding="utf-8")
    check(f"no placeholder secret in {name}",
          "change-this-key" not in text)
offenders = []
for py in ROOT.rglob("*.py"):
    if py.name == "verify_wave17.py" or "__pycache__" in str(py):
        continue
    if "change-this-key" in py.read_text(encoding="utf-8",
                                          errors="ignore"):
        offenders.append(str(py.relative_to(ROOT)))
check("placeholder gone from whole project", not offenders,
      f"offenders={offenders}")
app_src = (ROOT / "app.py").read_text(encoding="utf-8")
check("app.secret_key is never a string literal",
      not re.search(r"""secret_key\s*=\s*["']""", app_src))
check("secret read from GANITRA_SECRET_KEY env",
      'os.environ.get("GANITRA_SECRET_KEY"' in app_src)
check("random fallback uses secrets.token_hex",
      "secrets.token_hex" in app_src)

# --- 2. Env secret + cross-instance cookie validation ------------------------
app1 = create_app()
check("app uses the env secret exactly",
      app1.secret_key == TEST_KEY
      and app1.config.get("GANITRA_SECRET_FROM_ENV") is True)

c1 = app1.test_client()
USER = {"name": "W17 User " + RUN_ID, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w17test-pass"}
r = c1.post("/signup", data=USER)
check("signup succeeds (env-key app)", r.status_code == 302,
      f"status={r.status_code}")
set_cookies = r.headers.getlist("Set-Cookie")
session_cookie = next(
    (h for h in set_cookies if h.startswith("session=")), "")
cookie_value = (session_cookie.split(";", 1)[0].split("=", 1)[1]
                if session_cookie else "")
check("session cookie was set", bool(cookie_value))
check("Set-Cookie carries HttpOnly",
      "HttpOnly" in session_cookie, session_cookie[:80])
check("Set-Cookie carries SameSite=Lax",
      "SameSite=Lax" in session_cookie, session_cookie[:80])
check("Set-Cookie has NO Secure (flag off)",
      "Secure" not in session_cookie, session_cookie[:80])


def _client_with_cookie(app, value):
    client = app.test_client()
    try:
        client.set_cookie("session", value)
    except TypeError:  # older Werkzeug signature
        client.set_cookie("localhost", "session", value)
    return client


app2 = create_app()
check("second instance uses same env secret",
      app2.secret_key == TEST_KEY)
c2 = _client_with_cookie(app2, cookie_value)
body2 = c2.get("/").get_data(as_text=True)
check("cookie from instance 1 validates in instance 2",
      'id="chat-form"' in body2 and 'id="signup-card"' not in body2)

os.environ["GANITRA_SECRET_KEY"] = "different-key-" + RUN_ID
try:
    app_bad = create_app()
    c_bad = _client_with_cookie(app_bad, cookie_value)
    body_bad = c_bad.get("/").get_data(as_text=True)
finally:
    os.environ["GANITRA_SECRET_KEY"] = TEST_KEY
check("cookie rejected under a different key",
      'id="signup-card"' in body_bad)

# Random fallback: no env -> fresh random key per instance.
saved = os.environ.pop("GANITRA_SECRET_KEY")
try:
    app_r1 = create_app()
    app_r2 = create_app()
finally:
    os.environ["GANITRA_SECRET_KEY"] = saved
check("no env -> random per-process keys",
      app_r1.secret_key != app_r2.secret_key
      and len(str(app_r1.secret_key)) >= 32
      and app_r1.config.get("GANITRA_SECRET_FROM_ENV") is False)

# --- 3. Cookie flag config + Secure toggle ------------------------------------
check("config HttpOnly on",
      app1.config.get("SESSION_COOKIE_HTTPONLY") is True)
check("config SameSite=Lax",
      app1.config.get("SESSION_COOKIE_SAMESITE") == "Lax")
check("config Secure off by default (local http)",
      app1.config.get("SESSION_COOKIE_SECURE") is False)
os.environ["GANITRA_SECURE_COOKIES"] = "1"
try:
    app_secure = create_app()
finally:
    os.environ.pop("GANITRA_SECURE_COOKIES", None)
check("config Secure on with GANITRA_SECURE_COOKIES=1",
      app_secure.config.get("SESSION_COOKIE_SECURE") is True)
from datetime import timedelta  # noqa: E402
check("permanent lifetime present (30d, behaviour unchanged)",
      app1.config.get("PERMANENT_SESSION_LIFETIME")
      == timedelta(days=30))

# --- 4. Security headers + Wave-14 static cache intact -------------------------
client = app1.test_client()
r = client.get("/")
for header, want in (("X-Content-Type-Options", "nosniff"),
                     ("X-Frame-Options", "SAMEORIGIN"),
                     ("Referrer-Policy", "same-origin")):
    check(f"page header {header}", r.headers.get(header) == want,
          f"got={r.headers.get(header)}")
check("page still has NO public cache header",
      "max-age" not in (r.headers.get("Cache-Control") or ""))
r = client.get("/static/style.css")
check("static keeps Wave-14 cache header",
      r.status_code == 200
      and "max-age=86400" in (r.headers.get("Cache-Control") or ""))
check("static also carries the security headers",
      r.headers.get("X-Content-Type-Options") == "nosniff"
      and r.headers.get("X-Frame-Options") == "SAMEORIGIN"
      and r.headers.get("Referrer-Policy") == "same-origin")

# --- 5a. Lockout still triggers (Wave-10 pattern) ------------------------------
c5 = app1.test_client()
for _ in range(8):
    c5.post("/login", data={"name": USER["name"], "password": "bad"})
r = c5.post("/login", data={"name": USER["name"],
                            "password": USER["password"]})
check("9th attempt (even correct) is locked out",
      _esc(EN["auth_err_lockout"]) in r.get_data(as_text=True))

# --- 5b. Cross-account chat access still 404 (Wave-11 pattern) -----------------
ca = app1.test_client()
r = ca.post("/signup", data={**USER, "name": "W17 A " + RUN_ID})
check("owner signup ok", r.status_code == 302)
r = ca.post("/api/chats")
chat_id = (r.get_json() or {}).get("chat", {}).get("id")
check("owner created a chat", bool(chat_id), f"id={chat_id}")
cb = app1.test_client()
r = cb.post("/signup", data={**USER, "name": "W17 B " + RUN_ID})
check("other signup ok", r.status_code == 302)
for method in ("get", "delete"):
    r = getattr(cb, method)(f"/api/chats/{chat_id}")
    check(f"other account {method.upper()} chat -> 404",
          r.status_code == 404, f"status={r.status_code}")
r = cb.put(f"/api/chats/{chat_id}",
           json={"messages": [{"role": "user", "text": "hi"}]})
check("other account PUT chat -> 404", r.status_code == 404)

# --- 6. Item-4 static audits -----------------------------------------------------
check("photo cap is 2 MB in code",
      "_PHOTO_MAX_BYTES = 2 * 1024 * 1024" in app_src)
check("photo magic-bytes check present",
      "def _photo_kind(data):" in app_src
      and 'b"\\x89PNG\\r\\n\\x1a\\n"' in app_src
      and 'b"\\xff\\xd8\\xff"' in app_src)
check("photo content-type check present",
      'upload.content_type' in app_src
      and '"image/png"' in app_src and '"image/jpeg"' in app_src)
chats_src = (ROOT / "chats.py").read_text(encoding="utf-8")
check("chats scoped by user_id (get/save/delete)",
      "WHERE id = ? AND user_id = ?" in chats_src
      and "DELETE FROM chats WHERE user_id = ?" in chats_src)
accounts_src = (ROOT / "accounts.py").read_text(encoding="utf-8")
check("favourite column SQL uses allowlist only",
      "_FAVOURITE_COLUMNS" in accounts_src
      and "SET {column} = ?" in accounts_src)

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
