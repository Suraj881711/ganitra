"""Wave 20 (Suraj, 12 Nov 2026): "login once, stay logged in".

Bug: app.py configured PERMANENT_SESSION_LIFETIME=30 days but no
sign-in path ever set session.permanent, so Flask sent a browser
SESSION cookie (no Expires/Max-Age) and Chrome/Brave dropped the
login whenever the browser session ended — students had to sign
in again and again.

Fix: _set_account_session (the one helper behind /signup, /login
and /login-favourite) sets session.permanent = True. These tests
prove every sign-in path now returns a session cookie carrying a
~30-day Max-Age, with the Wave-17 flags (HttpOnly, SameSite=Lax)
intact.
"""
import re

import pytest

SIGNUP = {"name": "W20 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
          "password": "w20-pass"}

THIRTY_DAYS = 30 * 24 * 3600


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _session_cookie(response):
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("session="):
            return header
    return ""


def _assert_persistent(cookie):
    assert cookie, "no session cookie was set"
    # A permanent cookie carries Max-Age and/or an Expires date
    # ~30 days out; a browser-session cookie carries NEITHER —
    # that absence was the bug. (This Werkzeug sends Expires.)
    m = re.search(r"Max-Age=(\d+)", cookie)
    if m:
        max_age = int(m.group(1))
        assert THIRTY_DAYS - 3600 < max_age <= THIRTY_DAYS, max_age
    else:
        m = re.search(r"Expires=([^;]+)", cookie)
        assert m, f"cookie has no Expires either (not permanent): {cookie[:90]}"
        from datetime import datetime, timezone
        from email.utils import parsedate_to_datetime
        expires = parsedate_to_datetime(m.group(1).strip())
        delta = expires - datetime.now(timezone.utc)
        assert 29 * 24 * 3600 < delta.total_seconds() <= THIRTY_DAYS + 3600, delta
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie


def test_signup_cookie_is_persistent(client):
    r = client.post("/signup", data=SIGNUP)
    assert r.status_code == 302
    _assert_persistent(_session_cookie(r))


def test_login_cookie_is_persistent(client):
    client.post("/signup", data=SIGNUP)
    client.get("/logout")
    r = client.post("/login", data={"name": SIGNUP["name"],
                                    "password": SIGNUP["password"]})
    assert r.status_code == 302
    _assert_persistent(_session_cookie(r))


def test_favourite_login_cookie_is_persistent(client):
    client.post("/signup", data=SIGNUP)
    client.get("/logout")
    r = client.post("/login-favourite",
                    data={"name": SIGNUP["name"],
                          "favourite": SIGNUP["favourite"],
                          "new_password": "w20-new-pass"})
    assert r.status_code == 302
    _assert_persistent(_session_cookie(r))


def test_persistent_session_still_logs_in(client):
    client.post("/signup", data=SIGNUP)
    body = client.get("/").get_data(as_text=True)
    assert 'id="chat-form"' in body
    assert 'id="signup-card"' not in body
