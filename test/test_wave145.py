"""Wave 145 (Suraj, 17 Nov 2026): loading indicator + the
false internet-error fix.

His words: "internet toh achhe se chal raha tha fir internet
error kyu de rha tha — agar time lag raha hai toh load kar
skte hai 3 dot mai yaa circle mai." Two orders:

1. While an answer is loading, show a loading indicator —
   three dots — where the answer will appear. (A small dots
   decoration had sat beside the "thinking…" text since
   Wave 7; this wave makes the three bouncing dots THE
   indicator: prominent, present on both addTyping paths,
   shown from the moment the student sends until the answer
   replaces the placeholder — one indicator, no flicker.)

2. The "Internet is not available right now" note must fire
   ONLY on a genuine connectivity loss. Root cause of the
   false alarm: the note was rendered from the /api/solve
   fetch .catch(), which runs for EVERY rejection — the
   Wave-98 45 s abort on a slow free-tier answer, and
   resp.json() throwing on the host's 502 HTML error page
   included — and navigator.onLine was never consulted.
   Now: the offline note is gated on the browser itself
   reporting offline (navigator.onLine === false); a timeout,
   a non-JSON error page, or any other failed request while
   the browser is online shows the honest server-slow line
   (i18n chat_server_slow, a Wave-139-pinned system string).
   Wave 98 behaviour is otherwise untouched: the browser's
   basic evaluator still gets its chance on any transport
   failure, and a REAL offline state still serves offline
   basics + the offline note exactly as before.

The behavioural tests drive the real chat page in headless
Chromium (Playwright) against the real Flask app, with the
/api/solve route intercepted to simulate a slow answer, a
502 page, a hung request (the page's own 45 s abort, shimmed
shorter by the harness only), an online network failure and
a genuine browser offline state.
"""
import os
import re
import threading
import time
from pathlib import Path

import pytest

import i18n
from i18n import STRINGS, SYSTEM_MESSAGE_KEYS, get_strings

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

OFFLINE_EN = ("Internet is not available right now — "
              "please check your connection and try again.")
SLOW_EN = ("Server is slow right now — "
           "please try again in a moment.")
INDIC_SCRIPTS = re.compile(
    "[\u0900-\u097F\u0980-\u09FF\u0B80-\u0BFF\u0C00-\u0C7F]")


# ------------------------------------------------------------------
# The new system string
# ------------------------------------------------------------------

def test_server_slow_string_exists_and_is_pinned():
    assert "chat_server_slow" in SYSTEM_MESSAGE_KEYS
    for code in i18n.SUPPORTED_LANGS:
        assert STRINGS[code]["chat_server_slow"] == SLOW_EN, code
        assert get_strings(code)["chat_server_slow"] == SLOW_EN, code
        assert not INDIC_SCRIPTS.search(SLOW_EN), code


def test_i18n_key_sets_still_complete():
    base = set(STRINGS["en"])
    for code in i18n.SUPPORTED_LANGS:
        assert set(STRINGS[code]) == base, code


def test_chat_map_carries_server_slow():
    assert "serverSlow: {{ t.chat_server_slow | tojson }}" in INDEX
    assert "if (ui.chat_server_slow) CHAT.serverSlow = " \
           "ui.chat_server_slow;" in INDEX


# ------------------------------------------------------------------
# The loading indicator (three dots)
# ------------------------------------------------------------------

def test_typing_template_has_three_dots():
    tpl = INDEX.index('id="typing-template"')
    seg = INDEX[tpl:tpl + 400]
    assert 'class="dots"' in seg
    assert seg.count("<i></i>") == 3


def test_typing_dots_css_animation():
    assert ".bubble.typing .dots" in CSS
    assert ".bubble.typing .dots i" in CSS
    assert "animation: softpulse" in CSS
    assert "@keyframes softpulse" in CSS
    # a real bounce, not just a fade (Wave 145 strengthening)
    assert "translateY(-4.5px)" in CSS


def test_add_typing_fallback_also_builds_dots():
    # The no-template fallback path in addTyping() must carry
    # the same indicator.
    seg = INDEX[INDEX.index("function addTyping()"):]
    seg = seg[:seg.index("/* ---------- Wave 12")]
    assert 'dots.className = "dots"' in seg
    assert seg.count('"<i></i><i></i><i></i>"') == 1


def test_indicator_lifecycle_wiring():
    # Shown on send, removed when the answer lands — and the
    # submit handler is the only addTyping caller for a solve.
    submit = INDEX.index('form.addEventListener("submit"')
    assert INDEX.index("var typing = addTyping();", submit) > submit
    assert INDEX.index("typing.remove();", submit) > submit
    assert INDEX.count("addTyping()") >= 2  # definition + call


# ------------------------------------------------------------------
# The false-offline fix (static pins)
# ------------------------------------------------------------------

def test_offline_note_gated_on_browser_offline():
    assert "navigator.onLine === false" in INDEX
    gate = INDEX.index("var browserOffline")
    note = INDEX.index('addBubble("bot", CHAT.offlineNote', gate)
    slow = INDEX.index('addBubble("bot", CHAT.serverSlow', gate)
    assert gate < note < slow
    # the gate sits inside the fetch catch, after the offline
    # evaluator has had its chance (Wave 98 order preserved)
    ev = INDEX.index("window.GanitraOffline.solve(question)")
    assert ev < gate


def test_non_json_response_tagged_server_error():
    assert "resp.json().catch" in INDEX
    assert "ganitraServerError = true" in INDEX


def test_wave98_invariants_kept():
    assert "window.GanitraOffline.solve(question)" in INDEX
    assert "AbortController" in INDEX
    assert "45000" in INDEX
    assert "CHAT.offlineNote" in INDEX


# ------------------------------------------------------------------
# Behavioural: real page, headless Chromium, intercepted /api/solve
# ------------------------------------------------------------------

pw = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("w145")
    old = {k: os.environ.get(k) for k in
           ("GANITRA_DB_PATH", "GANITRA_SECRET_KEY", "MPLCONFIGDIR")}
    os.environ["GANITRA_DB_PATH"] = str(tmp / "t.db")
    os.environ["GANITRA_SECRET_KEY"] = "wave145-test-secret"
    os.environ["MPLCONFIGDIR"] = str(tmp / "mpl")
    from werkzeug.serving import make_server
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    srv = make_server("127.0.0.1", 0, app, threaded=True)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    yield {"base": "http://127.0.0.1:%d" % port, "app": app}
    srv.shutdown()
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


_user_n = [0]


def _fresh_page(browser, server, init_script=None):
    """A signed-in chat page for a brand-new throwaway user."""
    _user_n[0] += 1
    name = "W145 Tester %d" % _user_n[0]
    client = server["app"].test_client()
    r = client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w145-test-pass"})
    assert r.status_code in (200, 302)
    cookie = None
    get_cookie = getattr(client, "get_cookie", None)
    if get_cookie is not None:
        c = get_cookie("session")
        cookie = c.value if c is not None else None
    if not cookie:
        for c in client.cookie_jar:  # older Flask fallback
            if c.name == "session":
                cookie = c.value
    assert cookie, "signup did not produce a session cookie"
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    ctx.add_cookies([{"name": "session", "value": cookie,
                      "url": server["base"]}])
    # Keep the service worker out of these tests: the offline
    # evaluator is a plain script tag and does not need it,
    # and a worker would only add nondeterminism here.
    ctx.add_init_script(
        "if (navigator.serviceWorker) {"
        "  navigator.serviceWorker.register = function () {"
        "    return Promise.reject(new Error('stubbed')); }; }")
    # Record, in-page, whether the typing bubble (with its
    # dots) EVER appeared — catching a transient bubble by
    # polling from the driver races under CPU load; a mutation
    # observer inside the page cannot miss it.
    ctx.add_init_script(
        "window.__w145 = { dots: false };"
        "document.addEventListener('DOMContentLoaded', function () {"
        "  var log = document.getElementById('chat-log');"
        "  if (!log) return;"
        "  new MutationObserver(function (muts) {"
        "    muts.forEach(function (m) {"
        "      m.addedNodes.forEach(function (n) {"
        "        if (n.nodeType === 1 && n.classList"
        "            && n.classList.contains('typing')"
        "            && n.querySelector('.dots'))"
        "          window.__w145.dots = true;"
        "      });"
        "    });"
        "  }).observe(log, { childList: true });"
        "});")
    if init_script:
        ctx.add_init_script(init_script)
    page = ctx.new_page()
    page.goto(server["base"] + "/", wait_until="load")
    page.wait_for_selector("#q", state="visible")
    page.wait_for_timeout(400)
    return ctx, page


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception:
            pytest.skip("headless Chromium unavailable")
        yield b
        b.close()


def _send(page, question):
    page.fill("#q", question)
    page.click(".send-btn")


def _bot_texts(page):
    return page.locator(".bubble.bot").all_inner_texts()


TRIANGLE = "What is the sum of angles of a triangle?"


def test_browser_slow_answer_shows_dots_then_answer(browser, server):
    ctx, page = _fresh_page(browser, server)

    def slow(route):
        time.sleep(2.5)
        route.continue_()

    page.route("**/api/solve", slow)
    _send(page, "12 aur 18 ka HCF kya hoga?")
    # the three-dot indicator is up while the answer is in flight
    page.wait_for_selector(".bubble.typing .dots i",
                           state="visible", timeout=5000)
    assert page.locator(".bubble.typing .dots i").count() == 3
    # …and is replaced by the answer, with no error line of
    # either kind left behind
    page.wait_for_selector(".bubble.typing", state="detached",
                           timeout=20000)
    # Deploy-28 merge: the merged tree carries Wave 122's
    # line-by-line answer reveal (this wave's own tree rendered
    # the answer whole), so wait for the reveal to reach the
    # final answer line before reading the bubble texts.
    page.wait_for_function(
        "() => Array.from("
        "document.querySelectorAll('.bubble.bot'))"
        ".some(e => e.innerText.includes('6'))",
        timeout=20000)
    texts = _bot_texts(page)
    assert any("6" in t for t in texts), texts
    joined = "\n".join(texts)
    assert OFFLINE_EN not in joined
    assert SLOW_EN not in joined
    ctx.close()


def test_browser_502_shows_server_slow_not_offline(browser, server):
    ctx, page = _fresh_page(browser, server)

    def bad_gateway(route):
        time.sleep(0.8)  # long enough to see the dots first
        route.fulfill(
            status=502, content_type="text/html",
            body="<html><head><title>502 Bad Gateway</title>"
                 "</head><body>Bad Gateway</body></html>")

    page.route("**/api/solve", bad_gateway)
    _send(page, TRIANGLE)
    page.wait_for_function(
        "t => document.body.innerText.includes(t)", arg=SLOW_EN,
        timeout=15000)
    joined = "\n".join(_bot_texts(page))
    assert SLOW_EN in joined
    assert OFFLINE_EN not in joined
    # the dots indicator was up while the request was in flight
    assert page.evaluate("window.__w145.dots") is True
    ctx.close()


def test_browser_online_network_failure_shows_server_slow(
        browser, server):
    ctx, page = _fresh_page(browser, server)
    page.route("**/api/solve", lambda route: route.abort())
    _send(page, TRIANGLE)
    page.wait_for_function(
        "t => document.body.innerText.includes(t)", arg=SLOW_EN,
        timeout=15000)
    joined = "\n".join(_bot_texts(page))
    assert SLOW_EN in joined
    assert OFFLINE_EN not in joined
    ctx.close()


def test_browser_hung_request_times_out_to_server_slow(
        browser, server):
    # The harness shortens ONLY the page's own 45 s abort timer
    # (test speed); the code path exercised is the real one.
    shim = ("var _st = window.setTimeout.bind(window);"
            "window.setTimeout = function (fn, d) {"
            "  if (d === 45000) d = 1200;"
            "  return _st.apply(null, [fn, d].concat("
            "    Array.prototype.slice.call(arguments, 2))); };")
    ctx, page = _fresh_page(browser, server, init_script=shim)
    release = threading.Event()

    def hang(route):
        release.wait(timeout=20)
        try:
            route.abort()
        except Exception:
            pass

    page.route("**/api/solve", hang)
    _send(page, TRIANGLE)
    page.wait_for_function(
        "t => document.body.innerText.includes(t)", arg=SLOW_EN,
        timeout=20000)
    joined = "\n".join(_bot_texts(page))
    assert SLOW_EN in joined
    assert OFFLINE_EN not in joined
    # the dots indicator was up while the request hung
    assert page.evaluate("window.__w145.dots") is True
    release.set()
    ctx.close()


def test_browser_genuine_offline_keeps_wave98_behaviour(
        browser, server):
    ctx, page = _fresh_page(browser, server)
    ctx.set_offline(True)
    # beyond basics while truly offline: the offline note, as
    # Wave 98 designed
    _send(page, TRIANGLE)
    page.wait_for_function(
        "t => document.body.innerText.includes(t)", arg=OFFLINE_EN,
        timeout=15000)
    # a basic sum while truly offline: answered locally by the
    # browser evaluator, no error line for this turn
    _send(page, "2+2")
    page.wait_for_function(
        "() => { var b = document.querySelectorAll('.bubble.bot');"
        "  return b.length && b[b.length - 1].innerText.includes('4'); }",
        timeout=15000)
    joined = "\n".join(_bot_texts(page))
    assert joined.count(OFFLINE_EN) == 1, joined
    assert SLOW_EN not in joined
    ctx.set_offline(False)
    ctx.close()
