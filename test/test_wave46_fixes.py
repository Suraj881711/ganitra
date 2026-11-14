"""Wave 46: the SAFE fixes from the Wave 45 audit.

F1a — the primary solve gets a wall-clock budget plus pre-guards
on the known symbolic blow-up shapes, and a global
MAX_CONTENT_LENGTH. The audit's proof case — POST /api/solve
{"question": "expand (x + y + z + w)^60"} — hung past a 25 s
kill; it must now answer fast with the graceful fallback guide.
F1b — /file-extract's pdftoppm render is capped at ~2 MP by
computing the DPI from the page's MediaBox: the audit's
433-byte blank PDF claiming 7920x7920 pt took 22.7 s / ~1 GB;
a normal scanned page must still come back as an OCR image.
F2 — after a login lockout EXPIRES, the stale fail count is
reset: one new failure must not instantly re-lock for 30 min.
F4 — session history stores trimmed entries (question + answer
+ op + fallback_kind), so a 30-solve session cookie stays
comfortably under the ~4,096 B browser limit; the full latest
result still lives in session["last_result"] for /download and
/solution/print, which genuinely read it.
F5 — /account/photo enforces its 2 MB limit via a capped read
BEFORE parsing, mirroring /file-extract.
"""
import base64
import io
import os
import shutil
import sqlite3
import time

import pytest

CLEAN_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

SIGNUP = {"name": "W46 Tester", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
          "password": "w46-pass"}


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def _signup(client, **over):
    r = client.post("/signup", data={**SIGNUP, **over})
    assert r.status_code == 302
    return r


# ------------------------------------------------------------- F1a guards

def test_dangerous_shape_guard():
    from solver.router import _dangerous_shape
    # The audit's proof case and its family.
    assert _dangerous_shape("expand (x + y + z + w)^60")
    assert _dangerous_shape("expand (x + y + z + w)**60")
    assert _dangerous_shape("10^10^10")          # power tower
    assert _dangerous_shape("what is 10^30000")  # digit bomb
    # Legit school-sized shapes stay allowed.
    assert _dangerous_shape("expand (x + y)^10") is None
    assert _dangerous_shape("expand (x + 1)^5") is None
    assert _dangerous_shape("expand (x + y)^100") is None
    assert _dangerous_shape("what is 2^10") is None
    assert _dangerous_shape("2^3^2") is None
    assert _dangerous_shape("solve 2x + 3 = 7") is None
    assert _dangerous_shape("(x + 2)(x + 3)") is None


def test_expand_bomb_solve_question_is_fast_and_refused():
    from solver.router import solve_question
    start = time.time()
    result = solve_question("expand (x + y + z + w)^60")
    elapsed = time.time() - start
    assert elapsed < 2.0, elapsed
    # The solver's standard failure shape: the app layer's
    # fallback turns this into the friendly guide.
    assert result["op"] == "error"


def test_expand_bomb_via_api_is_graceful_and_fast(client):
    start = time.time()
    r = client.post("/api/solve",
                    json={"question": "expand (x + y + z + w)^60"})
    elapsed = time.time() - start
    assert r.status_code == 200
    assert elapsed < 5.0, elapsed
    body = r.get_json()
    assert body["ok"] is True
    result = body["result"]
    # A graceful fallback/guide result, not a hang and not the
    # raw expansion.
    assert result.get("fallback_kind") in (
        "guide", "similar", "concept", "salvage")
    assert "^60" not in str(result.get("answer", ""))


def test_normal_expansions_still_solve():
    from solver.router import solve_question
    r = solve_question("expand (x + 1)^5")
    assert r["op"] == "expand"
    assert "x^5" in r["answer"] and "5·x^4" in r["answer"]
    r = solve_question("expand (x + y)^10")
    assert r["op"] == "expand"
    assert r["answer"].startswith("x^10")


def test_solve_budget_times_out_a_slow_solve(monkeypatch):
    import solver.router as router

    def slow(question):
        time.sleep(2)
        return {"type": "algebra", "op": "expand",
                "answer": "late", "steps": []}

    monkeypatch.setattr(router, "_solve_question_uncached", slow)
    start = time.time()
    result = router._solve_with_budget("anything", budget=0.2)
    elapsed = time.time() - start
    assert elapsed < 1.5, elapsed
    assert result["op"] == "error"


def test_solve_budget_passes_results_and_exceptions(monkeypatch):
    import solver.router as router

    good = {"type": "arithmetic", "op": "evaluate",
            "answer": "4", "steps": []}
    monkeypatch.setattr(router, "_solve_question_uncached",
                        lambda q: good)
    assert router._solve_with_budget("2 + 2", budget=2.0) is good

    def boom(question):
        raise ValueError("nope")

    monkeypatch.setattr(router, "_solve_question_uncached", boom)
    with pytest.raises(ValueError):
        router._solve_with_budget("boom", budget=2.0)


def test_max_content_length_rejects_huge_body(client):
    big = b"x" * (5 * 1024 * 1024)
    r = client.post(
        "/file-extract",
        data={"file": (io.BytesIO(big), "big.txt")},
        content_type="multipart/form-data")
    assert r.status_code == 413


# ------------------------------------------------------------------- F1b

def _giant_pdf_bytes():
    pypdf = pytest.importorskip("pypdf")
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=7920, height=7920)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _png_dims(png):
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    return (int.from_bytes(png[16:20], "big"),
            int.from_bytes(png[20:24], "big"))


@pytest.mark.skipif(shutil.which("pdftoppm") is None,
                    reason="poppler not installed here")
def test_giant_mediabox_pdf_renders_small_and_fast(client):
    start = time.time()
    r = client.post(
        "/file-extract",
        data={"file": (io.BytesIO(_giant_pdf_bytes()), "giant.pdf")},
        content_type="multipart/form-data")
    elapsed = time.time() - start
    assert elapsed < 5.0, elapsed
    body = r.get_json()
    assert body["kind"] == "image"
    width, height = _png_dims(base64.b64decode(body["image"]))
    # ~2 MP cap: the audit's bomb rendered 16,500 x 16,500 px.
    assert width * height <= 2_100_000, (width, height)
    assert width <= 1500 and height <= 1500, (width, height)


@pytest.mark.skipif(shutil.which("pdftoppm") is None,
                    reason="poppler not installed here")
def test_normal_scanned_pdf_still_returns_ocr_image(client):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 200), "white")
    ImageDraw.Draw(img).text((20, 80), "2 + 2 = ?", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    r = client.post(
        "/file-extract",
        data={"file": (io.BytesIO(buf.getvalue()), "scan.pdf")},
        content_type="multipart/form-data")
    body = r.get_json()
    assert body["kind"] == "image"
    width, height = _png_dims(base64.b64decode(body["image"]))
    # A normal page still renders at the historical ~150 DPI
    # (400 pt wide -> ~833 px), so browser OCR quality is
    # unchanged.
    assert width >= 800, (width, height)


# --------------------------------------------------------------------- F2

def test_failed_login_counter_resets_when_lock_expires(
        tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "u.db"))
    import accounts
    key = "wave46 ghost"
    locked = False
    for _ in range(accounts.LOGIN_ATTEMPT_LIMIT):
        locked = accounts.record_failed_login(key)
    assert locked and accounts.is_locked(key)
    # Force the lock into the past (the audit's probe technique).
    conn = sqlite3.connect(str(tmp_path / "u.db"))
    conn.execute("UPDATE login_attempts SET locked_until = ?"
                 " WHERE name_key = ?",
                 (int(time.time()) - 5, key))
    conn.commit()
    conn.close()
    assert not accounts.is_locked(key)
    # ONE new failure must NOT re-lock (the F2 flaw).
    assert accounts.record_failed_login(key) is False
    assert not accounts.is_locked(key)
    # A full fresh window is required: fails 2..7 stay open,
    # the 8th locks again.
    for _ in range(accounts.LOGIN_ATTEMPT_LIMIT - 2):
        assert accounts.record_failed_login(key) is False
    assert accounts.record_failed_login(key) is True
    assert accounts.is_locked(key)


def test_lockout_expiry_gives_a_fair_window_over_http(app, client):
    from i18n import STRINGS
    from markupsafe import escape as esc
    lockout = esc(STRINGS["en"]["auth_err_lockout"])
    login_err = esc(STRINGS["en"]["auth_err_login"])
    _signup(client)
    client.get("/logout")
    for _ in range(8):
        r = client.post("/login", data={
            "name": SIGNUP["name"], "password": "bad-pass"})
    assert lockout in r.get_data(as_text=True)
    db = os.environ["GANITRA_DB_PATH"]
    conn = sqlite3.connect(db)
    conn.execute("UPDATE login_attempts SET locked_until = ?",
                 (int(time.time()) - 5,))
    conn.commit()
    conn.close()
    # The audit's probe used a FRESH session (the server-side
    # counter is the victim-facing one; a per-session counter
    # in the attacker's own browser is a separate signal).
    fresh = app.test_client()
    # One wrong password after expiry: the generic error, NOT
    # an instant fresh 30-minute lockout.
    r = fresh.post("/login", data={
        "name": SIGNUP["name"], "password": "bad-pass"})
    body = r.get_data(as_text=True)
    assert login_err in body and lockout not in body
    # And the student's correct password works right after.
    r = fresh.post("/login", data={
        "name": SIGNUP["name"], "password": SIGNUP["password"]})
    assert r.status_code == 302


# --------------------------------------------------------------------- F4

_QUESTIONS_30 = [
    "What is 15% of 240?",
    "Solve 2x + 3 = 7",
    "Find the HCF of 12 and 18",
    "Find the LCM of 8 and 12",
    "What is 3/4 + 2/3?",
    "Find the mean of 2, 4, 6, 8 and 10",
    "Find the area of a circle of radius 7 cm",
    "Find the simple interest on Rs 1000 at 5% for 2 years",
    "Solve x + y = 10 and x - y = 2",
    "Maximise Z = 3x + 4y subject to x + y \u2264 4, x \u2265 0,"
    " y \u2265 0",
    "What is 48 + 37?",
    "What is 125 - 58?",
    "What is 20% of 450?",
    "What is 5/6 - 1/4?",
    "Find the HCF of 24 and 36",
    "Find the LCM of 5 and 7",
    "What is 99 + 101?",
    "What is 250 - 175?",
    "What is 12.5% of 800?",
    "What is 2/5 + 3/10?",
    "Find the mean of 5, 10 and 15",
    "What is 64 + 128?",
    "What is 1000 - 999?",
    "What is 30% of 90?",
    "What is 7/8 - 1/2?",
    "Find the HCF of 18 and 27",
    "What is 45 + 55?",
    "What is 300 - 123?",
    "What is 10% of 250?",
    "What is 1/3 + 1/6?",
]


def _session_cookie_value(response):
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("session="):
            return header.split(";", 1)[0][len("session="):]
    return ""


def test_history_entries_are_trimmed(client):
    client.post("/api/solve", json={"question": "Solve 2x + 3 = 7"})
    client.post("/api/solve", json={"question": "What is 15% of 240?"})
    with client.session_transaction() as sess:
        history = sess["history"]
    assert len(history) == 2
    for entry in history:
        assert set(entry["result"]) == {
            "answer", "op", "fallback_kind"}
        assert "steps" not in entry["result"]
    # The /history page renders from the trimmed shape.
    r = client.get("/history")
    page = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Solve 2x + 3 = 7" in page and "x = 2" in page


def test_cookie_stays_small_over_30_solves(client):
    response = None
    for question in _QUESTIONS_30:
        response = client.post("/api/solve",
                               json={"question": question})
        assert response.status_code == 200
    cookie = _session_cookie_value(response)
    assert cookie, "no session cookie on the 30th solve"
    # The browser limit is ~4,096 B; the audit measured 3,630 B
    # with FULL result dicts. Trimmed entries must stay
    # comfortably under the limit.
    assert len(cookie) < 3400, len(cookie)
    with client.session_transaction() as sess:
        assert len(sess["history"]) == 30


def test_download_and_print_still_use_the_full_last_result(client):
    r = client.post("/solve", data={"question": "Solve 2x + 3 = 7"})
    assert r.status_code == 200
    r = client.get("/download")
    assert r.status_code == 200
    text = r.get_data(as_text=True)
    assert "Answer: x = 2" in text
    assert "Step-by-step solution:" in text  # steps: needs full dict
    r = client.get("/solution/print")
    assert r.status_code == 200
    assert "x = 2" in r.get_data(as_text=True)


# --------------------------------------------------------------------- F5

def _upload_photo(client, data, filename):
    return client.post(
        "/account/photo",
        data={"photo": (io.BytesIO(data), filename)},
        content_type="multipart/form-data")


def test_photo_oversize_gets_the_friendly_size_error(client):
    from i18n import STRINGS
    from markupsafe import escape as esc
    size_err = esc(STRINGS["en"]["acct_err_photo_size"])
    _signup(client)
    # 3 MB: over the 2 MB photo cap, under the 4 MB global cap,
    # so the route's own friendly error must answer (not a 413,
    # and not after parsing a fake image).
    big = CLEAN_PNG + b"\x00" * (3 * 1024 * 1024)
    r = _upload_photo(client, big, "big.png")
    assert r.status_code == 200
    assert size_err in r.get_data(as_text=True)
    r = client.get("/account/photo/file")
    assert r.status_code == 404  # nothing was stored


def test_photo_normal_upload_still_works(client):
    _signup(client)
    r = _upload_photo(client, CLEAN_PNG, "me.png")
    assert r.status_code == 302
    r = client.get("/account/photo/file")
    assert r.status_code == 200
    assert r.data == CLEAN_PNG
