"""Wave 232 (security wave): the audit's security rows, pinned.

Three fixes, each tested the way a browser would meet it:

1. CSRF — a per-session token (security.py). Browsers always
   send an Origin header on state-changing requests, so the
   tests below post WITH Origin to stand in for a real browser:
   no token -> a clean 403 (never a 500), the form field and the
   X-CSRFToken header both accepted, GETs untouched, the token
   rotating when an account session starts. One test also flips
   GANITRA_CSRF_PROTECT=1 (the production switch) and shows even
   a headerless request is then checked.

2. Headers + CSP — the Wave-17 headers stay, HSTS still rides
   the secure-cookie switch, and the new CSP names exactly the
   sources the app already loads (jsDelivr for MathJax/Tesseract,
   Google Fonts) while shutting object/base/form-action/framing
   abuse. The chat, papers and group pages still render 200 with
   their inline scripts intact, and the service worker still
   serves.

3. Auth hardening — the per-IP failed-credential throttle as a
   second dimension next to the Wave-17b name lockout (which is
   asserted UNCHANGED), and the password minimum 4 -> 6 for NEW
   passwords only: signup, favourite reset and the Account-page
   change all refuse 5 characters, while an account created
   earlier with a 4-character password still logs in.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import accounts  # noqa: E402
import security  # noqa: E402
from app import create_app  # noqa: E402

ORIGIN = {"Origin": "http://localhost"}
SIGNUP = {
    "class": "10", "board": "CBSE", "goal": "Doctor",
    "hobby": "Cricket", "favourite": "Pizza",
}


def _client():
    app = create_app()
    app.config["TESTING"] = True
    return app, app.test_client()


def _token(client, path="/"):
    """The token this session currently holds, read from the
    page meta exactly like base.html's script reads it."""
    resp = client.get(path)
    assert resp.status_code == 200
    match = re.search(r'name="csrf-token" content="([^"]+)"',
                      resp.get_data(as_text=True))
    assert match, "the csrf meta tag must be on every page"
    return match.group(1)


def _signup(client, name, password="topsecret1"):
    data = dict(SIGNUP, name=name, password=password)
    resp = client.post("/signup", data=data)
    assert resp.status_code == 302, resp.status_code
    return resp


# ---------------------------------------------------------------- CSRF

def test_csrf_token_is_issued_in_the_page_meta():
    _app, client = _client()
    token = _token(client, "/?mode=login")
    assert len(token) >= 32


def test_csrf_missing_token_on_a_form_post_is_a_clean_403():
    _app, client = _client()
    _signup(client, "Csrf Form Kid")
    client.get("/logout")
    client.get("/?mode=login")  # a browser holds a token by now
    resp = client.post(
        "/login", data={"name": "Csrf Form Kid",
                        "password": "topsecret1"},
        headers=ORIGIN)
    assert resp.status_code == 403  # clean 403 — never a 500
    assert "could not be verified" in resp.get_data(as_text=True)


def test_csrf_wrong_token_is_also_403():
    _app, client = _client()
    _signup(client, "Csrf Wrong Kid")
    client.get("/logout")
    client.get("/?mode=login")
    resp = client.post(
        "/login", data={"name": "Csrf Wrong Kid",
                        "password": "topsecret1",
                        "csrf_token": "not-the-real-token"},
        headers=ORIGIN)
    assert resp.status_code == 403


def test_csrf_form_field_token_is_accepted():
    _app, client = _client()
    _signup(client, "Csrf Field Kid")
    client.get("/logout")
    token = _token(client, "/?mode=login")
    resp = client.post(
        "/login", data={"name": "Csrf Field Kid",
                        "password": "topsecret1",
                        "csrf_token": token},
        headers=ORIGIN)
    assert resp.status_code == 302  # signed in, off to the chat


def test_csrf_header_token_is_accepted_on_the_api():
    _app, client = _client()
    _signup(client, "Csrf Api Kid")
    token = _token(client)
    resp = client.post("/api/solve", json={"question": "2+2"},
                       headers=dict(ORIGIN, **{
                           "X-CSRFToken": token}))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["ok"] is True and body["result"]


def test_csrf_missing_token_on_the_api_is_a_json_403():
    _app, client = _client()
    _signup(client, "Csrf Json Kid")
    client.get("/")  # the browser holds a token; the POST omits it
    resp = client.post("/api/solve", json={"question": "2+2"},
                       headers=ORIGIN)
    assert resp.status_code == 403
    body = resp.get_json()
    assert body["ok"] is False
    assert body["error"] == "csrf_failed"


def test_csrf_covers_group_phone_and_chat_delete():
    _app, client = _client()
    _signup(client, "Csrf Routes Kid")
    token = _token(client)
    # Group phone update without the token: refused.
    resp = client.post("/groups/phone",
                       data={"phone": "9812345678"}, headers=ORIGIN)
    assert resp.status_code == 403
    # The same request with the token: goes through (the groups
    # page comes back carrying the saved-number notice).
    resp = client.post(
        "/groups/phone",
        data={"phone": "9812345678", "csrf_token": token},
        headers=ORIGIN)
    assert resp.status_code == 200
    assert "add ho gaya" in resp.get_data(as_text=True)
    # Chat delete without the token: refused...
    made = client.post("/api/chats")
    chat_id = made.get_json()["chat"]["id"]
    resp = client.delete("/api/chats/%s" % chat_id, headers=ORIGIN)
    assert resp.status_code == 403
    # ...and with the header token it deletes.
    resp = client.delete("/api/chats/%s" % chat_id,
                         headers=dict(ORIGIN, **{
                             "X-CSRFToken": token}))
    assert resp.status_code == 200


def test_csrf_token_rotates_when_the_account_session_starts():
    _app, client = _client()
    _signup(client, "Csrf Rotate Kid")
    client.get("/logout")
    before = _token(client, "/?mode=login")
    resp = client.post(
        "/login", data={"name": "Csrf Rotate Kid",
                        "password": "topsecret1",
                        "csrf_token": before},
        headers=ORIGIN)
    assert resp.status_code == 302
    after = _token(client)
    assert after != before
    # The pre-login token is worthless now.
    resp = client.post("/api/chats",
                       headers=dict(ORIGIN, **{
                           "X-CSRFToken": before}))
    assert resp.status_code == 403


def test_csrf_forced_mode_checks_even_without_origin(monkeypatch):
    monkeypatch.setenv("GANITRA_CSRF_PROTECT", "1")
    _app, client = _client()
    token = _token(client, "/?mode=login")
    resp = client.post("/login", data={"name": "Nobody Here",
                                       "password": "whatever1"})
    assert resp.status_code == 403
    resp = client.post(
        "/login", data={"name": "Nobody Here",
                        "password": "whatever1",
                        "csrf_token": token})
    # The token passed, so the request reached the login view
    # (which answers with its ordinary friendly error page).
    assert resp.status_code == 200


def test_get_requests_need_no_token():
    _app, client = _client()
    _signup(client, "Csrf Get Kid")
    for path in ("/", "/papers", "/groups", "/account", "/chats"):
        resp = client.get(path, headers=ORIGIN)
        assert resp.status_code == 200, path


# ------------------------------------------------------- headers + CSP

def test_security_headers_present_on_pages_and_api():
    _app, client = _client()
    _signup(client, "Header Kid")
    for resp in (client.get("/"),
                 client.post("/api/solve",
                             json={"question": "2+2"})):
        assert resp.headers.get(
            "X-Content-Type-Options") == "nosniff"
        assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert resp.headers.get("Referrer-Policy") == "same-origin"
        assert "Content-Security-Policy" in resp.headers


def test_hsts_present_when_secure_cookies_are_on(monkeypatch):
    monkeypatch.setenv("GANITRA_SECURE_COOKIES", "1")
    _app, client = _client()
    resp = client.get("/")
    assert resp.headers.get("Strict-Transport-Security") == (
        "max-age=31536000; includeSubDomains")


def test_csp_names_the_apps_real_sources_and_shuts_abuse():
    _app, client = _client()
    csp = client.get("/").headers["Content-Security-Policy"]
    # What the app genuinely loads stays allowed...
    assert "https://cdn.jsdelivr.net" in csp        # MathJax/OCR
    assert "'wasm-unsafe-eval'" in csp              # Tesseract WASM
    assert "https://fonts.googleapis.com" in csp    # font CSS
    assert "https://fonts.gstatic.com" in csp       # font files
    assert "'unsafe-eval'" not in csp.replace(
        "'wasm-unsafe-eval'", "")
    # ...and the abuse doors the audit named are shut.
    assert "object-src 'none'" in csp
    assert "base-uri 'self'" in csp
    assert "form-action 'self'" in csp
    assert "frame-ancestors 'self'" in csp


def test_pages_render_with_csp_and_inline_scripts_intact():
    _app, client = _client()
    _signup(client, "Render Kid")
    chat = client.get("/")
    assert chat.status_code == 200
    body = chat.get_data(as_text=True)
    # The inline machinery the chat runs on is all still there.
    assert "<script" in body
    assert 'name="csrf-token"' in body
    assert "GANITRA_CSRF_TOKEN" in body
    assert client.get("/papers").status_code == 200
    assert client.get("/groups").status_code == 200
    # The PWA service worker still serves (it is never patched).
    assert client.get("/sw.js").status_code == 200


# --------------------------------------------------------- IP throttle

def test_ip_throttle_trips_after_the_threshold(monkeypatch):
    monkeypatch.setattr(security, "_AUTH_IP_LIMIT", 5)
    _app, client = _client()
    _signup(client, "Throttle Real")
    client.get("/logout")
    for i in range(5):
        resp = client.post("/login", data={
            "name": "Spray Name %d" % i, "password": "guess123"})
        assert resp.status_code == 200  # ordinary friendly error
    # The budget is burned: even the REAL name + password waits.
    resp = client.post("/login", data={
        "name": "Throttle Real", "password": "topsecret1"})
    assert resp.status_code == 200
    assert "Too many tries" in resp.get_data(as_text=True)


def test_ip_throttle_counts_failures_only(monkeypatch):
    monkeypatch.setattr(security, "_AUTH_IP_LIMIT", 5)
    _app, client = _client()
    _signup(client, "Throttle Mixed")
    client.get("/logout")
    for i in range(4):
        client.post("/login", data={
            "name": "Mixed Miss %d" % i, "password": "guess123"})
    # A success in between neither counts nor clears the slate.
    resp = client.post("/login", data={
        "name": "Throttle Mixed", "password": "topsecret1"})
    assert resp.status_code == 302
    client.get("/logout")
    client.post("/login", data={"name": "Mixed Miss 9",
                                "password": "guess123"})
    # That was failure number five — the next attempt waits.
    resp = client.post("/login", data={
        "name": "Throttle Mixed", "password": "topsecret1"})
    assert resp.status_code == 200
    assert "Too many tries" in resp.get_data(as_text=True)


def test_name_lockout_behaviour_is_unchanged():
    _app, client = _client()
    _signup(client, "Lockout Kid")
    _signup(client, "Lockout Bystander")
    client.get("/logout")
    for _i in range(8):
        client.post("/login", data={
            "name": "Lockout Kid", "password": "wrongpass"})
    # The Wave-17b rule exactly: that NAME waits, even with the
    # right password...
    resp = client.post("/login", data={
        "name": "Lockout Kid", "password": "topsecret1"})
    assert resp.status_code == 200
    assert "Too many tries" in resp.get_data(as_text=True)
    # ...while everyone else signs in as normal (8 failures is
    # nowhere near the IP budget of 100).
    resp = client.post("/login", data={
        "name": "Lockout Bystander", "password": "topsecret1"})
    assert resp.status_code == 302


# ---------------------------------------------------- password minimum

def test_signup_rejects_five_chars_and_accepts_six():
    _app, client = _client()
    resp = client.post("/signup", data=dict(
        SIGNUP, name="Short Pass Kid", password="abc45"))
    assert resp.status_code == 200
    assert "at least 6" in resp.get_data(as_text=True)
    assert accounts.get_user("Short Pass Kid") is None
    resp = client.post("/signup", data=dict(
        SIGNUP, name="Short Pass Kid", password="abc456"))
    assert resp.status_code == 302
    assert accounts.get_user("Short Pass Kid") is not None


def test_signup_form_states_the_password_rule():
    _app, client = _client()
    body = client.get("/").get_data(as_text=True)
    assert "At least 6 characters" in body


def test_favourite_reset_rejects_a_short_new_password():
    _app, client = _client()
    _signup(client, "Reset Kid")
    client.get("/logout")
    resp = client.post("/login-favourite", data={
        "name": "Reset Kid", "favourite": "Pizza",
        "new_password": "abc45"})
    assert resp.status_code == 200
    assert "at least 6" in resp.get_data(as_text=True)
    # The frozen flow itself is untouched: any one favourite +
    # a proper new password still signs in and resets.
    resp = client.post("/login-favourite", data={
        "name": "Reset Kid", "favourite": "Pizza",
        "new_password": "brandnew6"})
    assert resp.status_code == 302
    client.get("/logout")
    resp = client.post("/login", data={
        "name": "Reset Kid", "password": "brandnew6"})
    assert resp.status_code == 302


def test_account_password_change_rejects_short():
    _app, client = _client()
    _signup(client, "Change Kid")
    resp = client.post("/account/password", data={
        "old_password": "topsecret1", "new_password": "abc45"})
    assert resp.status_code == 200
    assert "at least 6" in resp.get_data(as_text=True)
    resp = client.post("/account/password", data={
        "old_password": "topsecret1", "new_password": "abc456"})
    assert resp.status_code == 302


def test_existing_short_password_still_logs_in():
    _app, client = _client()
    # An account from before this wave, with a 4-character
    # password, created straight in the store (the signup form
    # itself would refuse it today).
    user_id, problem = accounts.create_user(
        "Old Timer", "10", "CBSE", 10, "abc4",
        "Doctor", "Cricket", "Pizza")
    assert problem is None and user_id
    resp = client.post("/login", data={
        "name": "Old Timer", "password": "abc4"})
    assert resp.status_code == 302  # verify-only path unchanged
