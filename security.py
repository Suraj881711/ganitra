"""Wave 232 (security wave): the external audit's security rows,
fixed at the root — CSRF tokens, a Content-Security-Policy, and a
per-IP throttle on the auth endpoints as a second dimension next
to the Wave-17b per-name lockout.

Three pieces live here so app.py only wires them:

1. CSRF — a synchronizer token. One random token per session,
   issued when a page renders (app.py's context processor) and
   carried back either as the hidden ``csrf_token`` form field or
   as the ``X-CSRFToken`` header. base.html ships the token in a
   meta tag; a small script there arms every POST form with the
   hidden field and wraps ``fetch`` so every state-changing
   same-origin fetch carries the header — the real UI therefore
   keeps working byte-for-byte in behaviour.

   When is a token REQUIRED? CSRF is a browser attack: a victim's
   browser is tricked into sending a state-changing request with
   the victim's cookies attached. Two triggers, either one turns
   enforcement on for a request:
     * the request carries an ``Origin`` header — every modern
       browser sends one on every POST/PUT/DELETE (form post or
       fetch), so every real browser request is always checked;
     * the app runs with GANITRA_CSRF_PROTECT=1 (the production
       switch, same pattern as GANITRA_SECURE_COOKIES) — then
       EVERY state-changing request is checked, browser or not.
   A request with neither (a plain HTTP client, the test harness)
   cannot be a CSRF attack — it does not ride a victim's ambient
   cookies — and is allowed through. SameSite=Lax on the session
   cookie (Wave 17) stays as defence-in-depth underneath.

   A failed check is a clean 403 — JSON for /api/ paths, a short
   friendly HTML page for form posts — never a 500. The token
   ROTATES whenever an account session is established (signup /
   login / favourite login), so a token fixed before sign-in is
   worthless afterwards.

2. CSP — Wave 17 deliberately shipped no Content-Security-Policy
   ("the pages rely on inline scripts/styles"). This wave ships
   the conservative policy below: it allows exactly what the app
   already loads (its own origin, inline script/style, the
   jsDelivr CDN for MathJax + Tesseract, Google Fonts) and shuts
   the doors the audit named — no plugins/objects, no <base>
   hijack, forms post only to this origin, no cross-origin
   framing. What it does NOT do: with 'unsafe-inline' (required
   by the app's inline-heavy templates) it is not an XSS cure;
   that needs a nonce migration, a separate wave. The other
   Wave-17 headers (nosniff, X-Frame-Options, Referrer-Policy,
   conditional HSTS) already live in app.py's after-request hook
   and are unchanged; this module only adds the CSP value.

3. AUTH IP THROTTLE — the Wave-17b lockout is keyed by NAME
   (8 fails -> a wait). That stops guessing against ONE account
   but not password SPRAYING (one common password tried against
   many names) or bulk fake signups. A second, per-IP counter
   now tracks FAILED CREDENTIAL attempts (bad login password,
   bad favourite, and signups that probe an already-taken name)
   across all three auth endpoints: 100 failures inside 15
   minutes from one IP and further auth POSTs from that IP get
   the same friendly lockout page the name lockout shows. Pure
   form fumbling (an empty field, a too-short new password) does
   NOT count, and successful sign-ins never count — so a whole
   classroom behind one school NAT (hundreds of successful
   logins, a handful of typos) can never trip it;
   a sprayer burning through names hits it after 100 tries
   total, whatever names they used. Bookkeeping is the same
   in-memory, fail-open pattern as api.py's solve rate limit
   (Wave 227): a limiter bug must never lock students out.
   Numbers are env-tunable: GANITRA_AUTH_IP_LIMIT (default
   100, 0 disables), GANITRA_AUTH_IP_WINDOW seconds (default
   900).
"""
import os
import secrets
import time

from flask import Response, current_app, jsonify, request, session

# ------------------------------------------------------------------ CSRF

CSRF_SESSION_KEY = "csrf_token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRFToken"

_STATE_CHANGING = frozenset(("POST", "PUT", "DELETE", "PATCH"))


def csrf_protect_forced():
    """True when the operator switched full CSRF enforcement on
    (GANITRA_CSRF_PROTECT=1 in the WSGI environment)."""
    return os.environ.get(
        "GANITRA_CSRF_PROTECT", "").strip() == "1"


def issue_csrf_token():
    """Return this session's CSRF token, minting one if needed.
    Called by app.py's context processor on every page render, so
    any browser that has loaded any page holds a token."""
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def rotate_csrf_token():
    """Mint a fresh token, discarding the old one. Called when an
    account session is established so a pre-login token (which an
    attacker could have fixated) no longer validates."""
    token = secrets.token_urlsafe(32)
    session[CSRF_SESSION_KEY] = token
    return token


def csrf_enforced():
    """True when THIS request must present a valid token: forced
    mode, or the request carries an Origin header (a real
    browser state-changing request — the only CSRF surface)."""
    if csrf_protect_forced():
        return True
    return bool(request.headers.get("Origin"))


def _csrf_failure():
    """The clean 403: JSON for API paths, a short friendly page
    for form posts. Never a 500, never a stack trace."""
    if request.path.startswith("/api/"):
        return jsonify({
            "ok": False,
            "error": "csrf_failed",
            "message": "This request could not be verified. "
                       "Please reload the page and try again.",
        }), 403
    body = (
        "<!doctype html><html><head><meta charset=\"utf-8\" />"
        "<title>Ganitra</title></head><body>"
        "<p>This request could not be verified, so it was not "
        "carried out. Please go back, reload the page and try "
        "again.</p>"
        "<p><a href=\"/\">Back to Ganitra</a></p>"
        "</body></html>")
    return Response(body, status=403, mimetype="text/html")


def check_csrf():
    """before_request hook body: None lets the request through; a
    403 response stops it. GET/HEAD/OPTIONS are never checked —
    they change nothing."""
    if request.method not in _STATE_CHANGING:
        return None
    if not csrf_enforced():
        return None
    expected = session.get(CSRF_SESSION_KEY)
    sent = (request.form.get(CSRF_FORM_FIELD)
            or request.headers.get(CSRF_HEADER))
    if not expected or not sent:
        return _csrf_failure()
    if not secrets.compare_digest(str(sent), str(expected)):
        return _csrf_failure()
    return None


# ------------------------------------------------------------------- CSP

# Every source below is one the app already loads today:
#   'self'                 — the app itself (pages, API, static,
#                            graphs, the student's own photo).
#   'unsafe-inline'        — the templates' inline <script> and
#                            <style> (the reason Wave 17 shipped
#                            no CSP at all). Kept, documented:
#                            this policy is NOT an XSS cure.
#   'wasm-unsafe-eval'     — Tesseract.js compiles WebAssembly
#                            for OCR; without it Chrome refuses
#                            the WASM while CSP is on. It does
#                            NOT allow JavaScript eval.
#   cdn.jsdelivr.net       — MathJax (base.html) and the
#                            Tesseract engine/worker/traineddata
#                            (chat photo OCR).
#   fonts.googleapis.com   — the font stylesheet in base.html.
#   fonts.gstatic.com      — the font files themselves (and
#                            jsDelivr serves MathJax's fonts).
#   data: / blob:          — canvas photo handling, OCR images
#                            and generated media in the page.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval' "
    "https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' "
    "https://fonts.googleapis.com; "
    "font-src 'self' data: https://fonts.gstatic.com "
    "https://cdn.jsdelivr.net; "
    "img-src 'self' data: blob:; "
    "media-src 'self' data: blob:; "
    "connect-src 'self' https://cdn.jsdelivr.net; "
    "worker-src 'self' blob: https://cdn.jsdelivr.net; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'self'; "
    "manifest-src 'self'"
)


def apply_csp(resp):
    """Stamp the CSP on a response (setdefault: a route that
    ever sets its own policy keeps it)."""
    resp.headers.setdefault(
        "Content-Security-Policy", CONTENT_SECURITY_POLICY)
    return resp


# ------------------------------------------------------- auth IP throttle

_AUTH_IP_LIMIT = int(os.environ.get("GANITRA_AUTH_IP_LIMIT",
                                    "100"))
_AUTH_IP_WINDOW = float(os.environ.get("GANITRA_AUTH_IP_WINDOW",
                                       "900"))


def _auth_ip_hits():
    """The live (unexpired) failure timestamps for this IP.
    Fail-open: any bookkeeping error reads as no hits."""
    store = current_app.extensions.setdefault(
        "ganitra_auth_ip_fails", {})
    ip = request.remote_addr or "unknown"
    now = time.monotonic()
    hits = [t for t in store.get(ip, [])
            if now - t < _AUTH_IP_WINDOW]
    store[ip] = hits
    return hits


def auth_ip_throttled():
    """True when this IP has burned its failed-auth budget.
    Fail-open on any error: a limiter bug must never lock a
    classroom out."""
    if _AUTH_IP_LIMIT <= 0:
        return False
    try:
        return len(_auth_ip_hits()) >= _AUTH_IP_LIMIT
    except Exception:
        return False


def record_auth_ip_failure():
    """Count one FAILED auth attempt (bad login, bad favourite,
    failed signup) against this IP. Successful attempts are
    never recorded — that is what keeps a school NAT safe."""
    if _AUTH_IP_LIMIT <= 0:
        return
    try:
        hits = _auth_ip_hits()
        hits.append(time.monotonic())
        store = current_app.extensions.setdefault(
            "ganitra_auth_ip_fails", {})
        store[request.remote_addr or "unknown"] = hits
    except Exception:
        pass
