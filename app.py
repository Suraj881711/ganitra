import base64
import io
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from datetime import timedelta

from flask import (Flask, Response, jsonify, render_template, request,
                   redirect, session, url_for, flash)
from api import api_bp
from i18n import (LANG_NAMES, SPEECH_LANGS, SUPPORTED_LANGS,
                  advice_for, explanation_for, get_strings,
                  normalise_lang, remark_key_for, result_unsolvable,
                  solve_failed, teach_for)
from solver.methods import alternate_methods
from speedups import methods_nonblocking
from solver.practice import (QUIZ_DIFFICULTIES, QUIZ_QUESTION_COUNT,
                             QUIZ_SECONDS_PER_QUESTION, QUIZ_TOPICS,
                             check_quiz_answer, generate_practice,
                             generate_quiz)
from board_data import (BOARD_NAMES, BOARDS, CLASS_NUMBERS,
                        get_chapter, get_chapters)
from board_quiz import (CLASSIC_QUESTION_COUNT, display_answer,
                        generate_chapter_questions)
import papers_data
from solver.router import solve_question
from fallback import with_fallback
from langdetect_local import detect_language_confident
import accounts
import chats

_HISTORY_LIMIT = 30
_MISTAKE_LIMIT = 50
_QUESTION_LIMIT = 500
_SAATHI_NAME_LIMIT = 30
# Wave 10: after this many failed login attempts for one name in a
# session, further attempts get the friendly "try later" message.
_LOGIN_ATTEMPT_LIMIT = 8


def _signin(mode="signup", error=None, form=None, fav_error=False):
    """Wave 10: render the first-page sign-in (sign-up by default;
    "login" is the Welcome-back mode). fav_error=True re-opens the
    favourite-things card (it is hidden until "Forgot password?"
    is tapped, but a failed favourite login must land back on the
    open card with its error visible)."""
    form = form or {}
    return render_template(
        "auth.html", mode=mode, error=error, fav_error=fav_error,
        form_name=form.get("name", ""), form_class=form.get("class", ""),
        form_board=form.get("board", ""), form_goal=form.get("goal", ""),
        form_hobby=form.get("hobby", ""),
        form_favourite=form.get("favourite", ""))


def _clean_saathi_name(value):
    """Wave 6: keep only a short, plain-text first name for Mera
    Saathi. Tags are removed (never stored), whitespace is collapsed,
    and the result is capped at 30 characters; templates also escape
    it on render, so a name can never inject markup."""
    if not isinstance(value, str):
        return ""
    text = re.sub(r"<[^>]*>", "", value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:_SAATHI_NAME_LIMIT].strip()


def _clean_saathi_class(value):
    """Wave 6: the optional Saathi class is a whole number 1-12."""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 12 else None


def _personal_line(strings, name_key, plain_key, name):
    """Format a personalised i18n line, falling back safely."""
    template = strings.get(name_key if name else plain_key, "")
    if name:
        try:
            return template.format(name=name)
        except (IndexError, KeyError, ValueError):
            return template
    return template


def _ask_again(question):
    """Wave 5b: re-ask the same question with a gentle pre-filled hint
    appended. The hint is plain English (the router understands plain
    maths English; the friendly card in the default language explains
    the situation before the button is pressed), and the expression
    guard lives in the solver, so this never turns a solvable
    question into a failure."""
    return f"{question} find the value"


def normalize_ocr_text(text):
    """Conservatively clean text recognised from a photo (Tesseract.js).

    Only unambiguous maths fixes are applied — anything doubtful is left
    untouched so the user can correct it in the editable confirm box:
    unicode minus/dashes -> -, superscript ²/³ -> ^2/^3, ×/✕ -> *,
    ÷ -> /, an X between two digits -> *, and an isolated variable letter
    immediately followed by digits ("x2", "x 2") -> exponent ("x^2").
    """
    if not text:
        return ""
    t = text
    # Unicode minus and dash variants -> ASCII hyphen-minus
    t = t.replace("−", "-").replace("–", "-").replace("—", "-")
    # Superscript powers OCR sometimes produces
    t = t.replace("²", "^2").replace("³", "^3")
    # Multiplication / division symbols
    t = t.replace("×", "*").replace("✕", "*").replace("÷", "/")
    # "3X4" / "3 x 4" style: an X between two digits is multiplication
    t = re.sub(r"(\d)\s*[Xx]\s*(?=\d)", r"\1*", t)
    # "x2" / "x 2": isolated variable letter + digits is an exponent
    t = re.sub(r"(?<![A-Za-z])([A-Za-z])\s*(\d+)(?![A-Za-z])",
               r"\1^\2", t)
    # Collapse all whitespace (OCR line breaks) to single spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _solution_text(question, result):
    lines = [f"Question: {question}", ""]
    label = result.get("type", "")
    if result.get("op"):
        label = f"{label} · {result['op']}".strip(" ·")
    lines.append(f"Topic: {label}" if label else "Topic: -")
    lines.append(f"Answer: {result.get('answer', '')}")
    steps = result.get("steps") or []
    if steps:
        lines.append("")
        lines.append("Step-by-step solution:")
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")
    if result.get("interpreted_as"):
        lines.append("")
        lines.append(f"(Understood as: {result['interpreted_as']})")
    lines.append("")
    lines.append("— Solved by Ganitra (Flask + SymPy)")
    return "\n".join(lines)


def _warm_up(app):
    """Wave 14 (speed): pay the cold-start costs ONCE, here at
    start-up, so the first real student request feels instant:

    - the heavy imports (sympy via the solver, matplotlib via the
      plotting module) are forced to load now;
    - one simple solve + one equation solve run end-to-end (plus
      the auto-teach methods pass), warming sympy's lazy internals
      and the router's pattern tables;
    - the accounts/chats SQLite schema + indexes are created (and
      WAL enabled) via their init_db().

    Guarded end-to-end: ANY warm-up failure is logged and ignored
    — a slow start is acceptable, a broken start is not.
    """
    try:
        import solver.plotting  # noqa: F401  (matplotlib import)
        solve_question("2+2")
        warm = solve_question("x^2 - 5x + 6 = 0")
        methods_nonblocking("x^2 - 5x + 6 = 0", warm, budget=10)
        accounts.init_db()
        chats.init_db()
        app.config["GANITRA_WARMED_UP"] = True
    except Exception:  # warm-up must never break start-up
        app.logger.exception("Wave 14 warm-up failed (continuing)")


def create_app():
    app = Flask(__name__)
    # Wave 17 (security): the session-signing key comes from the
    # GANITRA_SECRET_KEY environment variable. If it is unset (or
    # empty), a fresh random key is generated for THIS process —
    # sessions then die on restart (everyone is logged out), which
    # is safe but inconvenient; there is NO hardcoded fallback.
    _secret = os.environ.get("GANITRA_SECRET_KEY", "").strip()
    if _secret:
        app.secret_key = _secret
        app.config["GANITRA_SECRET_FROM_ENV"] = True
    else:
        app.secret_key = secrets.token_hex(32)
        app.config["GANITRA_SECRET_FROM_ENV"] = False
        app.logger.warning(
            "GANITRA_SECRET_KEY is not set: generated a random "
            "session key for this process — all sessions will be "
            "invalidated on restart. Set GANITRA_SECRET_KEY to a "
            "long random value in production.")
    # Wave 17 (security): session-cookie flags. HttpOnly keeps the
    # cookie away from JS; SameSite=Lax blocks cross-site sending
    # on POSTs (CSRF defence-in-depth for the form posts). Secure
    # is opt-in via GANITRA_SECURE_COOKIES=1 so local http testing
    # keeps working; production (HTTPS) must set it.
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(
            os.environ.get("GANITRA_SECURE_COOKIES", "").strip()
            == "1"),
        # Wave 20 (Suraj, 12 Nov 2026): sign-in sessions ARE marked
        # permanent (see _set_account_session), so this lifetime is
        # the real cookie lifetime — log in once, stay logged in
        # for 30 days, ChatGPT-style.
        PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    )

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    # Wave 19 (PWA basics): manifest + service worker are served
    # from the site root so the service worker's scope covers the
    # whole app (a worker under /static/ could only control
    # /static/). Files themselves live in static/ and are the
    # frozen assets — the manifest references the existing logo
    # files exactly as they are.
    @app.route("/manifest.webmanifest")
    def ganitra_manifest():
        resp = app.send_static_file("manifest.webmanifest")
        resp.headers["Content-Type"] = "application/manifest+json"
        return resp

    @app.route("/sw.js")
    def ganitra_service_worker():
        resp = app.send_static_file("sw.js")
        resp.headers["Content-Type"] = "application/javascript"
        resp.headers["Service-Worker-Allowed"] = "/"
        return resp

    # iOS home-screen icon: serves the frozen logo-mark file
    # byte-for-byte under the conventional name (the file itself
    # is never modified or redrawn).
    @app.route("/apple-touch-icon.png")
    def ganitra_apple_touch_icon():
        return app.send_static_file("logo-mark.png")

    # Wave 14: browser caching for static assets ONLY — the logo,
    # CSS and graph PNGs (graph files are content-hash named, so
    # a cached copy can never go stale against new content).
    # HTML pages and API responses get no such header here.
    # Wave 17: the same hook also stamps the security headers on
    # EVERY response (no CSP — see verify_wave17.py header note).
    @app.after_request
    def _wave14_static_cache(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "same-origin"
        # Wave 17b (pen-test F5): HSTS only where HTTPS is the
        # deal — production sets GANITRA_SECURE_COOKIES=1 (which
        # is exactly what SESSION_COOKIE_SECURE records); local
        # http must never see it, or the browser would refuse
        # http on that host for a year. (CSP stays deliberately
        # OFF — the pages rely on inline scripts/styles.)
        if app.config.get("SESSION_COOKIE_SECURE"):
            resp.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains")
        if request.path.startswith("/static/"):
            resp.headers["Cache-Control"] = "public, max-age=86400"
        return resp

    def _record_mistakes(rows, source):
        """Wave 5: save the WRONG rows of a quiz/chapter test into the
        session Mistake Notebook, newest first."""
        wrong = [{"question": r["question"], "expected": r["expected"],
                  "given": r.get("given", ""), "topic": r.get("topic"),
                  "source": source}
                 for r in rows if not r["correct"]]
        if wrong:
            notebook = session.get("mistakes", [])
            session["mistakes"] = (wrong + notebook)[:_MISTAKE_LIMIT]

    def _copycheck(rows, score, total, topic_labels, chapter=None):
        """Wave 5e: build the board-style copy-check card data and
        persist the last test report in the session, so the result
        page can be re-rendered with the same card. The card checks
        FINAL ANSWERS only (like a teacher checking a copy): marks,
        a remark by score band, per-question ticks, and the topics /
        chapters where marks were lost. `topic_labels` maps a row's
        topic key to its display name (quiz topic names or the
        chapter title)."""
        lost, seen = [], set()
        for r in rows:
            if not r["correct"]:
                label = topic_labels.get(r.get("topic"),
                                         r.get("topic") or "")
                if label and label not in seen:
                    seen.add(label)
                    lost.append(label)
        report = {
            "score": score,
            "total": total,
            "remark_key": remark_key_for(score, total),
            "lost_topics": lost,
            "chapter": chapter,
            "celebrate": bool(total) and score / total >= 0.8,
        }
        # Wave 6: keep a running count of >=80% tests for the Parent
        # Report star rule. If older session data has only the last
        # report, treat a celebrating last report as one such test.
        star_count = session.get("test_star_count")
        if not isinstance(star_count, int) or star_count < 0:
            previous = session.get("last_test_report") or {}
            star_count = 1 if previous.get("celebrate") else 0
        if report["celebrate"]:
            star_count += 1
        session["test_star_count"] = star_count
        session["last_test_report"] = report
        return report

    def _lang():
        return normalise_lang(session.get("lang", "en"))

    def _t():
        return get_strings(_lang())

    def _set_account_session(user):
        """Wave 10: a signed-in account IS the student's identity —
        the session keeps only the user id + name (secrets never
        enter the cookie), and the Wave-6 Saathi name/class + the
        Board Mode board choice are filled from the account so the
        greeting, Board Mode and personalisation work immediately.

        Wave 20 (Suraj, 12 Nov 2026): the session is marked
        PERMANENT — Flask then sends the cookie with a 30-day
        Expires/Max-Age (PERMANENT_SESSION_LIFETIME), so the
        student logs in ONCE and stays logged in across browser
        restarts, like ChatGPT. Without this flag the cookie died
        with the browser session and students had to sign in again
        every time. Every sign-in path (sign-up, password login,
        favourite login) goes through this helper, and the profile
        refresh re-asserts it, so all of them get the long cookie.
        The Wave-17/17b cookie flags (HttpOnly, SameSite=Lax,
        Secure opt-in) and the server-side lockout are unchanged."""
        session.permanent = True
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["saathi_name"] = user["name"]
        session["saathi_class"] = user["class_num"]
        session["saathi_skipped"] = False
        session["board"] = user["board"]

    def _failed_logins(name_key):
        # Wave 17b (pen-test F1): the SERVER-SIDE counter in
        # accounts.py is authoritative — a running server lock
        # reports as a full count no matter what this session's
        # cookie says, so throwing the cookie away no longer
        # resets anything. The per-session counter below it is
        # kept as a harmless second signal.
        if accounts.is_locked(name_key):
            return _LOGIN_ATTEMPT_LIMIT
        attempts = session.get("login_attempts") or {}
        return attempts.get(name_key, 0)

    def _record_failed_login(name_key):
        attempts = dict(session.get("login_attempts") or {})
        attempts[name_key] = attempts.get(name_key, 0) + 1
        session["login_attempts"] = attempts
        accounts.record_failed_login(name_key)

    def _clear_failed_logins(name_key):
        attempts = dict(session.get("login_attempts") or {})
        attempts.pop(name_key, None)
        session["login_attempts"] = attempts
        accounts.clear_login_failures(name_key)

    @app.context_processor
    def inject_i18n():
        lang = _lang()
        strings = get_strings(lang)
        try:
            strings["quiz_intro"] = strings["quiz_intro"].format(
                count=QUIZ_QUESTION_COUNT,
                seconds=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION)
        except (KeyError, IndexError, ValueError):
            pass
        # Wave 12: the full-page menu's profile block needs the
        # account's own board text and whether a photo exists.
        # Both come from the account row (one cheap query when
        # signed in); anonymous visitors get the empty defaults.
        _uid = session.get("user_id")
        _account = accounts.get_user_by_id(_uid) if _uid else None
        user_board_text = (_account["board_text"] if _account
                           else BOARD_NAMES.get(
                               session.get("board", "cbse"), "CBSE"))
        try:
            strings["acct_student_line"] = strings[
                "acct_student_line"].format(
                    **{"class": _account["class_num"]}
                ) if _account else strings["acct_student_line"]
        except (KeyError, IndexError, ValueError):
            pass
        saathi_name = _clean_saathi_name(session.get("saathi_name", ""))
        saathi_class = _clean_saathi_class(session.get("saathi_class"))
        return {
            "lang": lang,
            "t": strings,
            "lang_options": [(code, LANG_NAMES[code])
                             for code in SUPPORTED_LANGS],
            "speech_lang": SPEECH_LANGS[lang],
            "js_t": {k: v for k, v in strings.items()
                     if k.startswith("js_") or k.startswith("error_")
                     or k.startswith("chats_")
                     or k.startswith("mm_")
                     or k in ("chat_waking_note", "flash_too_long",
                              "dhyaan_today", "file_btn",
                              "chats_new", "voice_btn", "photo_btn",
                              "solve_btn", "acct_stats_questions",
                              "acct_stats_chats")},
            "dhyaan_today": strings["dhyaan_today"],
            "voice_label": strings["voice_btn"],
            "saathi_name": saathi_name,
            "saathi_class": saathi_class,
            "saathi_skipped": bool(session.get("saathi_skipped"))
                              and not saathi_name,
            # Wave 10: a signed-in account replaces the optional
            # first-visit Saathi card entirely (the name/class come
            # from the account now). Templates use this to hide the
            # card/edit affordances; the session fallbacks stay for
            # anonymous/other-page visits.
            "user_name": session.get("user_name", ""),
            # Wave 12: menu profile block + My Account links.
            "user_board_text": user_board_text,
            "user_has_photo": bool(_uid and accounts.get_photo(_uid)),
            "board_display": BOARD_NAMES.get(
                session.get("board", "cbse"), "CBSE"),
            "saathi_edit": request.args.get("saathi") == "edit",
            "saathi_greeting": _personal_line(
                strings, "saathi_welcome_name", "chat_welcome",
                saathi_name),
            "saathi_encouragement": _personal_line(
                strings, "saathi_wrong_name", "saathi_wrong",
                saathi_name),
            "error_encouragement": _personal_line(
                strings, "error_encourage_name", "error_encourage",
                saathi_name),
        }

    @app.get("/set-lang/<code>")
    def set_lang(code):
        if code in SUPPORTED_LANGS:
            session["lang"] = code
        target = request.args.get("next") or ""
        if not target.startswith("/") or target.startswith("//"):
            target = url_for("index")
        return redirect(target)

    @app.post("/saathi")
    def saathi_save():
        """Wave 6: save (or skip) the optional Mera Saathi profile.
        Only a cleaned first name and an optional class number ever
        enter the session — no account, no database, and skipping
        never blocks any part of the site."""
        if request.form.get("action") == "skip":
            session.pop("saathi_name", None)
            session.pop("saathi_class", None)
            session["saathi_skipped"] = True
        else:
            name = _clean_saathi_name(request.form.get("name", ""))
            if name:
                session["saathi_name"] = name
                class_num = _clean_saathi_class(
                    request.form.get("class", ""))
                if class_num is None:
                    session.pop("saathi_class", None)
                else:
                    session["saathi_class"] = class_num
                session["saathi_skipped"] = False
            else:
                session.pop("saathi_name", None)
                session.pop("saathi_class", None)
                session["saathi_skipped"] = True
        target = request.form.get("next") or ""
        if not target.startswith("/") or target.startswith("//"):
            target = url_for("index")
        return redirect(target)

    @app.get("/")
    def index():
        # Wave 10: the FIRST page is the sign-in (Suraj ordered:
        # "pahale login kaa page dena hai"). Anonymous visitors see
        # the sign-up / Welcome-back page; a signed-in student sees
        # the chat. The gate applies to / (chat home) ONLY — the
        # other pages keep their Wave 1-9 behaviour (see README).
        if not session.get("user_id"):
            mode = request.args.get("mode", "")
            if mode != "login":
                mode = "signup"
            return _signin(mode)
        return render_template("index.html")

    # ------------------------------------------------------ wave 10 auth
    @app.post("/signup")
    def signup():
        form = {key: request.form.get(key, "")
                for key in ("name", "class", "board", "goal",
                            "hobby", "favourite", "password")}
        strings = _t()
        # The account display name uses the same cleaning as Mera
        # Saathi (tags stripped, whitespace collapsed, 30-char cap).
        name = _clean_saathi_name(form["name"])
        fields = [name, form["class"], form["board"], form["goal"],
                  form["hobby"], form["favourite"], form["password"]]
        if any(not str(v).strip() for v in fields):
            return _signin("signup", strings["auth_err_fill_all"],
                           form)
        class_num = accounts.parse_class(form["class"])
        if class_num is None:
            return _signin("signup", strings["auth_err_class"], form)
        if len(form["password"]) < 4:
            return _signin("signup",
                           strings["auth_err_password_short"], form)
        # Wave 17b (pen-test F1): a favourite thing is a recovery
        # secret — too-short answers ("om", "ok") are far too easy
        # to guess, so new favourites need at least 3 letters
        # (measured after the same normalisation recovery uses).
        # Existing shorter favourites still WORK at recovery —
        # the minimum is enforced only when one is set/changed.
        if any(len(accounts.normalise_answer(form[key])) < 3
               for key in ("goal", "hobby", "favourite")):
            return _signin("signup",
                           strings["auth_err_fav_short"], form)
        _user_id, problem = accounts.create_user(
            name, form["class"], form["board"], class_num,
            form["password"], form["goal"], form["hobby"],
            form["favourite"])
        if problem == "exists":
            return _signin("signup", strings["auth_err_name_taken"],
                           form)
        user = accounts.get_user(name)
        _set_account_session(user)
        return redirect(url_for("index"))

    @app.post("/login")
    def login():
        strings = _t()
        name = request.form.get("name", "")
        password = request.form.get("password", "")
        key = accounts.normalise_name_key(name)
        if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name})
        user = accounts.get_user(name)
        if user is None or not accounts.verify_password(user, password):
            # One friendly error for both cases — never a hint
            # about which part (name vs password) was wrong.
            _record_failed_login(key)
            if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
                return _signin("login", strings["auth_err_lockout"],
                               {"name": name})
            return _signin("login", strings["auth_err_login"],
                           {"name": name})
        _clear_failed_logins(key)
        _set_account_session(user)
        return redirect(url_for("index"))

    @app.post("/login-favourite")
    def login_favourite():
        """Forgot-password login, Suraj's design: name + ANY ONE
        of the 3 favourite things (matching sign-up) logs the
        student in AND sets a new password right there."""
        strings = _t()
        name = request.form.get("name", "")
        typed = request.form.get("favourite", "")
        new_password = request.form.get("new_password", "")
        key = accounts.normalise_name_key(name)
        if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name}, fav_error=True)
        user = accounts.get_user(name)
        if user is None or not accounts.verify_favourite(user, typed):
            _record_failed_login(key)
            if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
                return _signin("login",
                               strings["auth_err_lockout"],
                               {"name": name}, fav_error=True)
            return _signin("login", strings["auth_err_fav"],
                           {"name": name}, fav_error=True)
        if len(new_password) < 4:
            return _signin("login",
                           strings["auth_err_password_short"],
                           {"name": name}, fav_error=True)
        accounts.update_password(user["id"], new_password)
        _clear_failed_logins(key)
        user = accounts.get_user(name)
        _set_account_session(user)
        return redirect(url_for("index"))

    @app.get("/logout")
    def logout():
        for key in ("user_id", "user_name", "saathi_name",
                    "saathi_class"):
            session.pop(key, None)
        session["saathi_skipped"] = False
        return redirect(url_for("index"))

    # --------------------------------------------------- wave 12 account
    # My Account (Wave 12): everything about the account can be
    # changed later — name, class, board, the 3 favourite things,
    # the password, plus the student's own photo. Favourites are
    # write-only: the page never shows their current values (they
    # are stored as hashes and cannot be shown anyway). Log out
    # lives at the bottom of THIS page only. Every route needs the
    # login session; anonymous visitors go back to the sign-in
    # gate, exactly like /chats.
    _PHOTO_MAX_BYTES = 2 * 1024 * 1024

    def _account_user():
        uid = session.get("user_id")
        return accounts.get_user_by_id(uid) if uid else None

    def _account_page(user, error=None):
        return render_template(
            "account.html", account=user, error=error,
            has_photo=bool(accounts.get_photo(user["id"])),
            saved=request.args.get("saved") == "1" and not error)

    def _photo_kind(data):
        """'png' / 'jpeg' by MAGIC BYTES (never by the file name),
        or None — uploads are only ever these two formats."""
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if data[:3] == b"\xff\xd8\xff":
            return "jpeg"
        return None

    def _photo_end(data, kind):
        """Offset just past the image's own terminator — the end
        of the PNG IEND chunk, or just past the JPEG EOI marker
        (FF D9) — or None when the stream is malformed / has no
        terminator. Wave 17b (pen-test F3): an upload whose bytes
        CONTINUE past this offset is a polyglot (e.g. a script
        appended after the image) and is refused outright, not
        stored. (JPEG uses the LAST FF D9: an EXIF thumbnail is a
        whole JPEG embedded before the main image's own EOI.)"""
        if kind == "png":
            pos = 8  # signature (already verified by _photo_kind)
            while pos + 8 <= len(data):
                length = int.from_bytes(data[pos:pos + 4], "big")
                ctype = data[pos + 4:pos + 8]
                end = pos + 8 + length + 4  # header+payload+CRC
                if end > len(data):
                    return None
                if ctype == b"IEND":
                    return end
                pos = end
            return None
        idx = data.rfind(b"\xff\xd9")
        return idx + 2 if idx >= 0 else None

    @app.get("/account")
    def account_page():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        return _account_page(user)

    @app.post("/account/profile")
    def account_profile():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        strings = _t()
        name = _clean_saathi_name(request.form.get("name", ""))
        class_text = request.form.get("class", "").strip()
        board_text = request.form.get("board", "").strip()
        if not name or not class_text or not board_text:
            return _account_page(user, strings["acct_err_required"])
        class_num = accounts.parse_class(class_text)
        if class_num is None:
            return _account_page(user, strings["auth_err_class"])
        if name != user["name"]:
            if accounts.rename_user(user["id"], name) == "exists":
                return _account_page(
                    user, strings["auth_err_name_taken"])
        accounts.update_profile(user["id"], class_text, class_num,
                                board_text)
        fresh = accounts.get_user_by_id(user["id"])
        _set_account_session(fresh)
        return redirect(url_for("account_page", saved=1))

    @app.post("/account/favourite/<field>")
    def account_favourite(field):
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        if field not in ("goal", "hobby", "favourite"):
            return redirect(url_for("account_page"))
        value = request.form.get("value", "").strip()
        if not value:
            return _account_page(user, _t()["acct_err_required"])
        # Wave 17b: same 3-letter minimum as sign-up (see signup).
        if len(accounts.normalise_answer(value)) < 3:
            return _account_page(user,
                                 _t()["auth_err_fav_short"])
        accounts.update_favourites(user["id"], field, value)
        return redirect(url_for("account_page", saved=1))

    @app.post("/account/password")
    def account_password():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        strings = _t()
        old = request.form.get("old_password", "")
        new = request.form.get("new_password", "")
        if not old:
            return _account_page(user,
                                 strings["acct_err_old_password"])
        if not accounts.verify_password(user, old):
            return _account_page(
                user, strings["acct_err_password_wrong"])
        if len(new) < 4:
            return _account_page(
                user, strings["auth_err_password_short"])
        accounts.update_password(user["id"], new)
        return redirect(url_for("account_page", saved=1))

    @app.post("/account/photo")
    def account_photo_upload():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        strings = _t()
        upload = request.files.get("photo")
        if upload is None or not upload.filename:
            return _account_page(user, strings["acct_err_required"])
        data = upload.read()
        ctype = (upload.content_type or "").lower()
        kind = _photo_kind(data)
        if kind is None or ctype not in (
                "image/png", "image/jpeg", "image/jpg"):
            return _account_page(user,
                                 strings["acct_err_photo_type"])
        # Wave 17b (pen-test F3): nothing may live after the
        # image's own end — trailing bytes mean a polyglot file.
        if _photo_end(data, kind) != len(data):
            return _account_page(user,
                                 strings["acct_err_photo_type"])
        if len(data) > _PHOTO_MAX_BYTES:
            return _account_page(user,
                                 strings["acct_err_photo_size"])
        accounts.set_photo(user["id"], data)
        return redirect(url_for("account_page", saved=1))

    @app.post("/account/photo/delete")
    def account_photo_delete():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        accounts.delete_photo(user["id"])
        return redirect(url_for("account_page", saved=1))

    @app.get("/account/photo/file")
    def account_photo_file():
        user = _account_user()
        if not user:
            return redirect(url_for("index"))
        data = accounts.get_photo(user["id"])
        if not data:
            return ("", 404)
        kind = _photo_kind(data) or "png"
        resp = Response(data, mimetype=f"image/{kind}")
        resp.headers["Cache-Control"] = "private"
        return resp

    @app.get("/account/stats.json")
    def account_stats():
        user = _account_user()
        if not user:
            return jsonify({"ok": False,
                            "error": "login-required"}), 401
        return jsonify({
            "ok": True,
            "questions": accounts.questions_count(user["id"]),
            "chats": accounts.chats_count(user["id"]),
        })

    # ------------------------------------------------------ wave 11 chats
    # Multi-chat (Brave-style tabs): chats belong to the signed-in
    # ACCOUNT and live server-side in the accounts SQLite file
    # (chats.py). Every endpoint requires the login session and
    # only ever touches the caller's own chats. Anonymous callers
    # get the sign-in gate (a redirect for the view, 401 JSON for
    # the API) — chats are account data, never public.
    def _chat_uid():
        return session.get("user_id")

    @app.get("/chats")
    def chats_view():
        if not _chat_uid():
            return redirect(url_for("index"))
        return render_template("chats.html")

    @app.get("/api/chats")
    def api_chats_list():
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        return jsonify({"ok": True, "chats": chats.list_chats(uid)})

    @app.post("/api/chats")
    def api_chats_create():
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        return jsonify({"ok": True, "chat": chats.create_chat(uid)}), 201

    @app.get("/api/chats/<int:chat_id>")
    def api_chats_get(chat_id):
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        chat = chats.get_chat(uid, chat_id)
        if chat is None:
            return jsonify({"ok": False, "error": "not-found"}), 404
        return jsonify({"ok": True, "chat": chat})

    @app.put("/api/chats/<int:chat_id>")
    def api_chats_save(chat_id):
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        # Wave 17b (pen-test F2 pattern): a non-object JSON body
        # or a non-list "messages" is a client error (400) with
        # the friendly JSON shape — never a 500. A missing/null
        # messages field keeps the old behaviour (save_chat
        # refuses it -> 404 not-found).
        data = request.get_json(silent=True)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            return jsonify({"ok": False,
                            "error": "bad-request"}), 400
        messages = data.get("messages")
        if messages is not None and not isinstance(messages, list):
            return jsonify({"ok": False,
                            "error": "bad-request"}), 400
        chat = chats.save_chat(uid, chat_id, messages)
        if chat is None:
            return jsonify({"ok": False, "error": "not-found"}), 404
        return jsonify({"ok": True, "chat": chat})

    @app.delete("/api/chats/<int:chat_id>")
    def api_chats_delete(chat_id):
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        if not chats.delete_chat(uid, chat_id):
            return jsonify({"ok": False, "error": "not-found"}), 404
        return jsonify({"ok": True})

    @app.delete("/api/chats")
    def api_chats_delete_all():
        uid = _chat_uid()
        if not uid:
            return jsonify({"ok": False, "error": "login-required"}), 401
        removed = chats.delete_all_chats(uid)
        return jsonify({"ok": True, "deleted": removed})

    @app.get("/topics")
    def topics():
        """Wave 7: the topic list that used to sit under the chat on
        the homepage now lives on its own simple page — the home
        page is a pure chat screen (ChatGPT-style), nothing else."""
        return render_template("topics.html")

    @app.post("/solve")
    def solve():
        question = request.form.get("question", "").strip()
        if not question:
            flash(_t()["flash_no_question"])
            return redirect(url_for("index"))
        if len(question) > _QUESTION_LIMIT:
            flash(_t()["flash_too_long"])
            return redirect(url_for("index"))
        # Wave 9: auto language — the same rule as the chat API: a
        # solidly detected different language becomes the session
        # language BEFORE the answer page renders, so the whole
        # page (headings, explanation, advice) uses the new one.
        detected, solid = detect_language_confident(question)
        if solid and detected != _lang():
            session["lang"] = detected
        result = solve_question(question)
        # Wave 5b: on failure, gently re-ask once with a hint; the
        # second result decides what the student sees.
        if solve_failed(question, result):
            retry = solve_question(_ask_again(question))
            if not solve_failed(question, retry):
                result = retry
        # Wave 18: no dead-end — failures, letter-soup "answers"
        # and soft non-answers become honest fallback answers
        # (salvage / concept / similar example / friendly guide),
        # so the error card below is now only a last resort that
        # the fallback itself could not cover.
        result = with_fallback(question, result)
        failed = solve_failed(question, result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result,
                               explanation=(None if failed
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if failed
                                       else advice_for(result, _lang())),
                               # Wave 14: same non-blocking
                               # auto-teach budget as /api/solve.
                               methods=([] if failed
                                        else methods_nonblocking(
                                            question, result)),
                               teach=([] if failed
                                      else teach_for(result, _lang())),
                               unsolvable=failed)

    # ------------------------------------------------- wave 27 files
    # Any-file upload (Wave 27): the chat's attach picker now
    # offers EVERY file type (Suraj: "koi si bhi file ho, all
    # file ko select karane kaa option hona chahiye"). Images
    # keep the browser-side Tesseract flow; everything else is
    # posted here. The type is decided by MAGIC BYTES, never
    # by the file name (the Wave 17 rule), executables are
    # never touched or run, and nothing is stored — bytes are
    # handled in memory (poppler gets a throwaway temp dir)
    # and dropped. Replies the chat script understands:
    #   {"kind": "text", "text": ...}        -> solve it
    #   {"kind": "image", "image": <base64>} -> a scanned PDF's
    #        first page; the browser OCRs it like a photo
    #   {"ok": false, "code": ...}           -> the script
    #        answers with the honest friendly line in the
    #        student's language — never a dead end, never a
    #        fake solve.
    _FILE_MAX_BYTES = 2 * 1024 * 1024  # same cap as the photo
    _FILE_TEXT_LIMIT = 6000

    def _pdf_text(data):
        """A PDF's text layer via pypdf; None when pypdf is
        unavailable or the file does not parse. An empty
        string means it parsed but carries no text (a scan)."""
        try:
            from pypdf import PdfReader
        except Exception:
            return None
        try:
            reader = PdfReader(io.BytesIO(data))
            parts = []
            for page in reader.pages[:50]:
                parts.append(page.extract_text() or "")
            return "\n".join(parts).strip()
        except Exception:
            return None

    def _pdf_first_page_png(data):
        """A PDF's first page rendered to PNG bytes by poppler
        (pdftoppm), or None when poppler is missing or the
        render fails."""
        exe = shutil.which("pdftoppm")
        if not exe:
            return None
        try:
            with tempfile.TemporaryDirectory() as tmp:
                src = os.path.join(tmp, "in.pdf")
                with open(src, "wb") as fh:
                    fh.write(data)
                subprocess.run(
                    [exe, "-png", "-f", "1", "-l", "1", "-r", "150",
                     src, os.path.join(tmp, "page")],
                    check=True, timeout=30,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
                out = os.path.join(tmp, "page-1.png")
                if not os.path.exists(out):
                    return None
                with open(out, "rb") as fh:
                    return fh.read()
        except Exception:
            return None

    def _docx_text(data):
        """A .docx's text via zipfile + XML (no new dependency);
        None when the bytes are not a real Word document (any
        other zip — a .zip of photos, an .xlsx — lands here
        too and is refused). Zip-bomb guards: the entry count
        and document.xml's size are both capped."""
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if len(zf.namelist()) > 200:
                    return None
                info = zf.getinfo("word/document.xml")
                if info.file_size > 5 * 1024 * 1024:
                    return None
                xml_bytes = zf.read("word/document.xml")
            root = ET.fromstring(xml_bytes)
        except Exception:
            return None
        w_ns = "{http://schemas.openxmlformats.org/" \
               "wordprocessingml/2006/main}"
        paras = []
        for para in root.iter(w_ns + "p"):
            runs = [node.text or ""
                    for node in para.iter(w_ns + "t")]
            if runs:
                paras.append("".join(runs))
        return "\n".join(paras).strip()

    def _plain_text(data):
        """A .txt file's contents; None when the bytes are not
        readable text (undecodable, NULs, mostly control
        characters) — binaries never pass as text."""
        try:
            text = data.decode("utf-8-sig")
        except Exception:
            return None
        if "\x00" in text:
            return None
        if text:
            printable = sum(1 for ch in text
                            if ch.isprintable() or ch in "\n\r\t")
            if printable / len(text) < 0.95:
                return None
        return text.strip()

    @app.post("/file-extract")
    def file_extract():
        upload = request.files.get("file")
        if upload is None:
            return jsonify({"ok": False, "code": "no_file"}), 400
        data = upload.stream.read(_FILE_MAX_BYTES + 1)
        if len(data) > _FILE_MAX_BYTES:
            return jsonify({"ok": False, "code": "too_large"})
        if data[:5] == b"%PDF-":
            text = _pdf_text(data)
            if text:
                return jsonify({"kind": "text",
                                "text": text[:_FILE_TEXT_LIMIT]})
            if text == "":
                png = _pdf_first_page_png(data)
                if png:
                    return jsonify({
                        "kind": "image",
                        "image": base64.b64encode(png)
                        .decode("ascii")})
            return jsonify({"ok": False, "code": "empty"})
        if data[:2] == b"PK":
            text = _docx_text(data)
            if text:
                return jsonify({"kind": "text",
                                "text": text[:_FILE_TEXT_LIMIT]})
            if text == "":
                return jsonify({"ok": False, "code": "empty"})
            return jsonify({"ok": False, "code": "unsupported"})
        if _photo_kind(data) or data[:4] == b"GIF8" or \
                data[:2] == b"BM" or \
                (data[:4] == b"RIFF" and data[8:12] == b"WEBP") or \
                (data[4:8] == b"ftyp" and data[8:12] in
                 (b"heic", b"heix", b"mif1", b"msf1")):
            # An image that reached the server anyway (the
            # browser normally OCRs these itself) — hand it
            # back for the same OCR flow.
            return jsonify({"kind": "image",
                            "image": base64.b64encode(data)
                            .decode("ascii")})
        text = _plain_text(data)
        if text:
            return jsonify({"kind": "text",
                            "text": text[:_FILE_TEXT_LIMIT]})
        if text == "":
            return jsonify({"ok": False, "code": "empty"})
        return jsonify({"ok": False, "code": "unsupported"})

    @app.post("/photo-solve")
    def photo_solve():
        # Text recognised from a photo by Tesseract.js in the browser.
        # Normalise it, solve it, and render the answer page with the
        # recognised text in an editable box on top — agar OCR ne galat
        # padha ho, user text theek karke normal /solve se dobara bhej
        # sakta hai.
        # Wave 28: the form also carries WHERE the text came from
        # (Wave 27's any-file upload rides this same route): "photo"
        # (a real photo, OCR'd in the browser), "file" (clean text
        # extracted from a PDF/.docx/.txt — no OCR ran) or "file-ocr"
        # (a scanned file page, OCR'd). The answer page words its
        # header accordingly and shows the OCR-misread warning only
        # when OCR actually ran. Anything unexpected counts as a
        # photo (the historical behaviour of this route).
        source = request.form.get("source", "photo")
        if source not in ("photo", "file", "file-ocr"):
            source = "photo"
        raw = request.form.get("question", "")
        question = normalize_ocr_text(raw)
        if not question:
            flash(_t()["photo_no_text"])
            return redirect(url_for("index"))
        if len(question) > _QUESTION_LIMIT:
            flash(_t()["flash_too_long"])
            return redirect(url_for("index"))
        result = solve_question(question)
        if solve_failed(question, result):
            retry = solve_question(_ask_again(question))
            if not solve_failed(question, retry):
                result = retry
        # Wave 18: same no-dead-end fallback as /solve.
        result = with_fallback(question, result)
        failed = solve_failed(question, result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result, photo_text=question,
                               source=source,
                               explanation=(None if failed
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if failed
                                       else advice_for(result, _lang())),
                               # Wave 14: same non-blocking
                               # auto-teach budget as /api/solve.
                               methods=([] if failed
                                        else methods_nonblocking(
                                            question, result)),
                               teach=([] if failed
                                      else teach_for(result, _lang())),
                               unsolvable=failed)

    @app.get("/download")
    def download():
        question = session.get("last_question")
        result = session.get("last_result")
        if not question or not result:
            flash(_t()["flash_download_first"])
            return redirect(url_for("index"))
        body = _solution_text(question, result)
        return Response(
            body,
            mimetype="text/plain; charset=utf-8",
            headers={"Content-Disposition":
                     "attachment; filename=solution.txt"},
        )

    @app.get("/history")
    def history():
        return render_template(
            "history.html", entries=session.get("history", []))

    @app.post("/history/clear")
    def history_clear():
        session.pop("history", None)
        return redirect(url_for("history"))

    @app.get("/parent-report")
    def parent_report():
        """Wave 6: a calm report for parents, built only from data
        this browser/session already holds — session history, the
        session Mistake Notebook, the last test report, and (filled
        in by the page's JS) today's Dhyaan record in localStorage.
        There is no account or cloud record behind it."""
        strings = _t()
        history_count = len(session.get("history", []))
        mistakes = session.get("mistakes", [])
        topics, seen = [], set()
        for entry in mistakes:
            source = (entry.get("source") or "").strip()
            topic = (entry.get("topic") or "").strip()
            if source and source != "quiz":
                label = source
            elif topic:
                label = strings.get(f"quiz_topic_{topic}", topic)
            else:
                label = ""
            if label and label not in seen:
                seen.add(label)
                topics.append(label)
        last_report = session.get("last_test_report") or None
        test_star_count = session.get("test_star_count")
        if not isinstance(test_star_count, int) or test_star_count < 0:
            test_star_count = 1 if (
                last_report and last_report.get("celebrate")) else 0
        total_stars = history_count // 5 + test_star_count
        last_score_text = None
        if last_report:
            last_score_text = (f"{last_report.get('score', 0)} / "
                               f"{last_report.get('total', 0)}")
        return render_template(
            "parent_report.html",
            history_count=history_count,
            mistakes_count=len(mistakes),
            mistake_topics=topics,
            last_report=last_report,
            last_score_text=last_score_text,
            test_star_count=test_star_count,
            total_stars=total_stars)

    @app.get("/practice")
    def practice():
        return render_template(
            "practice.html",
            questions=None,
            quiz=None,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    @app.post("/practice/start")
    def practice_start():
        topic = request.form.get("topic", "arithmetic")
        difficulty = request.form.get("difficulty", "easy")
        if topic not in QUIZ_TOPICS:
            topic = "arithmetic"
        if difficulty not in QUIZ_DIFFICULTIES:
            difficulty = "easy"
        items = generate_quiz(topic, difficulty)
        quiz = {"topic": topic, "difficulty": difficulty,
                "questions": items}
        session["quiz"] = quiz
        return render_template(
            "practice.html",
            questions=None,
            quiz=quiz,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    @app.post("/practice/submit")
    def practice_submit():
        quiz = session.get("quiz")
        if not quiz:
            flash(_t()["flash_start_quiz"])
            return redirect(url_for("practice"))
        rows, score = [], 0
        for i, item in enumerate(quiz["questions"]):
            given = request.form.get(f"answer_{i}", "")
            ok = check_quiz_answer(item["answer"], given)
            score += 1 if ok else 0
            rows.append({
                "question": item["question"],
                "expected": item["answer"],
                "given": given,
                "correct": ok,
                "topic": quiz["topic"],
            })
        _record_mistakes(rows, "quiz")
        session.pop("quiz", None)
        t = _t()
        copycheck = _copycheck(
            rows, score, len(rows),
            {quiz["topic"]: t[f"quiz_topic_{quiz['topic']}"]})
        return render_template(
            "practice_result.html",
            rows=rows,
            score=score,
            total=len(rows),
            topic=quiz["topic"],
            difficulty=quiz["difficulty"],
            time_taken=request.form.get("time_taken", ""),
            copycheck=copycheck,
        )

    @app.get("/practice/classic")
    def practice_classic():
        return render_template(
            "practice.html",
            questions=generate_practice(7),
            quiz=None,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    # ------------------------------------------------------------ print
    @app.get("/solution/print")
    def solution_print():
        """Print-friendly solution page (Wave 5): the browser's own
        Print -> Save as PDF produces the PDF, so the app needs no
        PDF library at all."""
        question = session.get("last_question")
        result = session.get("last_result")
        if not question or not result:
            flash(_t()["flash_download_first"])
            return redirect(url_for("index"))
        return render_template(
            "print.html", question=question, result=result,
            explanation=explanation_for(result, _lang()),
            advice=advice_for(result, _lang()),
            handwriting_style=(request.args.get("style") == "hand"))

    # -------------------------------------------------------- board mode
    @app.get("/board")
    def board_home():
        from datetime import date

        board_slug = session.get("board", "cbse")
        # Teacher's Advice of the Day: 7 curated tips, one per day,
        # rotated by calendar date (same tip all day, all visitors).
        tip_key = f"tip_day_{date.today().toordinal() % 7}"
        return render_template(
            "board.html", boards=BOARDS,
            board_slug=board_slug,
            board_name=BOARD_NAMES.get(board_slug, "CBSE"),
            class_numbers=CLASS_NUMBERS,
            day_tip=_t()[tip_key])

    @app.get("/board/select/<board_slug>")
    def board_select(board_slug):
        if board_slug in BOARD_NAMES:
            session["board"] = board_slug
        return redirect(url_for("board_home"))

    @app.get("/board/<int:class_num>")
    def board_class(class_num):
        chapters = get_chapters(class_num)
        if not chapters:
            return redirect(url_for("board_home"))
        board_slug = session.get("board", "cbse")
        return render_template(
            "board_class.html", class_num=class_num,
            chapters=chapters,
            board_name=BOARD_NAMES.get(board_slug, "CBSE"))

    @app.get("/board/<int:class_num>/<slug>")
    def board_chapter(class_num, slug):
        chapter = get_chapter(class_num, slug)
        if chapter is None:
            return redirect(url_for("board_home"))
        return render_template(
            "board_chapter.html", class_num=class_num,
            chapter=chapter)

    @app.get("/board/<int:class_num>/<slug>/practice")
    def board_chapter_practice(class_num, slug):
        chapter = get_chapter(class_num, slug)
        if chapter is None:
            return redirect(url_for("board_home"))
        items = generate_chapter_questions(
            chapter["topic"], count=CLASSIC_QUESTION_COUNT)
        questions = [{"question": it["question"],
                      "answer": display_answer(it["answer"])}
                     for it in items]
        return render_template(
            "board_practice.html", class_num=class_num,
            chapter=chapter, questions=questions)

    @app.post("/board/test/start")
    def board_test_start():
        try:
            class_num = int(request.form.get("class_num", ""))
        except ValueError:
            class_num = -1
        chapter = get_chapter(class_num,
                              request.form.get("slug", ""))
        if chapter is None:
            return redirect(url_for("board_home"))
        items = generate_chapter_questions(chapter["topic"])
        session["board_test"] = {
            "class_num": class_num,
            "slug": chapter["slug"],
            "chapter_title": chapter["title"],
            "topic": chapter["topic"],
            "questions": items,
        }
        return render_template(
            "board_test.html", class_num=class_num, chapter=chapter,
            test=session["board_test"],
            time_limit=QUIZ_QUESTION_COUNT
            * QUIZ_SECONDS_PER_QUESTION)

    @app.post("/board/test/submit")
    def board_test_submit():
        test = session.get("board_test")
        if not test:
            flash(_t()["flash_start_quiz"])
            return redirect(url_for("board_home"))
        rows, score = [], 0
        for i, item in enumerate(test["questions"]):
            given = request.form.get(f"answer_{i}", "")
            ok = check_quiz_answer(item["answer"], given)
            score += 1 if ok else 0
            rows.append({
                "question": item["question"],
                "expected": display_answer(item["answer"]),
                "given": given,
                "correct": ok,
                "topic": test["topic"],
            })
        _record_mistakes(
            rows, f"Class {test['class_num']} · "
                  f"{test['chapter_title']}")
        session.pop("board_test", None)
        copycheck = _copycheck(
            rows, score, len(rows),
            {test["topic"]: test["chapter_title"]},
            chapter=test["chapter_title"])
        return render_template(
            "practice_result.html",
            rows=rows,
            score=score,
            total=len(rows),
            topic=test["topic"],
            difficulty="medium",
            time_taken=request.form.get("time_taken", ""),
            copycheck=copycheck,
        )

    # ------------------------------------------------- wave 16 papers
    # Previous Papers (Suraj's idea, 10 Nov 2026): a small library
    # of REAL previous board papers (papers_data.py — every entry
    # carries its public source name + URL; nothing is invented),
    # a pattern analysis computed from that library, and the
    # "Apna Paper Banao" generator (real questions reused where
    # the library has them, generated questions always labelled
    # "practice question"). All pages are account pages like
    # /chats: anonymous visitors are sent back to the sign-in
    # gate at /.
    def _papers_signed_in():
        return bool(session.get("user_id"))

    @app.get("/papers")
    def papers_home():
        if not _papers_signed_in():
            return redirect(url_for("index"))
        groups = []
        for class_num in papers_data.CLASSES_WITH_PAPERS:
            rows = []
            for paper in papers_data.papers_for_class(class_num):
                rows.append({
                    "paper": paper,
                    "question_count": len(paper["questions"]),
                    "total_marks": papers_data.paper_total_marks(
                        paper),
                })
            groups.append({"class_num": class_num, "papers": rows})
        return render_template("papers.html", groups=groups)

    @app.get("/papers/<paper_id>")
    def papers_view(paper_id):
        if not _papers_signed_in():
            return redirect(url_for("index"))
        paper = papers_data.get_paper(paper_id)
        if paper is None:
            return redirect(url_for("papers_home"))
        sections = []
        for section in papers_data.PAPER_STRUCTURE:
            qs = [q for q in paper["questions"]
                  if q["section"] == section]
            if qs:
                sections.append({
                    "section": section,
                    "title": papers_data.SECTION_TITLES[section],
                    "questions": qs,
                })
        chapters = {q["chapter"]: papers_data.chapter_title(
            paper["class_num"], q["chapter"])
            for q in paper["questions"]}
        return render_template(
            "paper_view.html", paper=paper, sections=sections,
            chapters=chapters,
            total_marks=papers_data.paper_total_marks(paper))

    @app.get("/papers/analysis")
    def papers_analysis():
        if not _papers_signed_in():
            return redirect(url_for("index"))
        analyses = [papers_data.analysis_for_class(class_num)
                    for class_num
                    in papers_data.CLASSES_WITH_PAPERS]
        return render_template("papers_analysis.html",
                               analyses=analyses)

    @app.get("/papers/generate")
    def papers_generate():
        if not _papers_signed_in():
            return redirect(url_for("index"))
        return render_template(
            "papers_generate.html", paper=None,
            classes=papers_data.CLASSES_WITH_PAPERS)

    @app.post("/papers/generate")
    def papers_generate_post():
        if not _papers_signed_in():
            return redirect(url_for("index"))
        try:
            class_num = int(request.form.get("class_num", ""))
        except ValueError:
            class_num = -1
        if class_num not in papers_data.CLASSES_WITH_PAPERS:
            return redirect(url_for("papers_generate"))
        # Only the seed + class ride in the session cookie (the
        # full paper is far too big for a cookie); the generator
        # is deterministic for a seed, so the print view rebuilds
        # the identical paper from this reference.
        import random as _random
        seed = _random.SystemRandom().randint(0, 10 ** 9)
        paper = papers_data.generate_practice_paper(
            class_num, seed=seed)
        session["practice_paper_ref"] = {"class_num": class_num,
                                          "seed": seed}
        return render_template(
            "papers_generate.html", paper=paper,
            classes=papers_data.CLASSES_WITH_PAPERS)

    @app.get("/papers/print")
    def papers_print():
        """Print/PDF-friendly view of the last generated practice
        paper (same standalone-serif approach as /solution/print:
        the browser's Print -> Save as PDF makes the PDF)."""
        if not _papers_signed_in():
            return redirect(url_for("index"))
        ref = session.get("practice_paper_ref") or {}
        paper = None
        if ref.get("class_num") in papers_data.CLASSES_WITH_PAPERS:
            paper = papers_data.generate_practice_paper(
                ref["class_num"], seed=ref.get("seed"))
        if not paper:
            return redirect(url_for("papers_generate"))
        return render_template("papers_print.html", paper=paper)

    # -------------------------------------------------- mistake notebook
    @app.get("/mistakes")
    def mistakes():
        entries = [{"question": e["question"],
                    "expected": display_answer(e["expected"]),
                    "source": e.get("source", "")}
                   for e in session.get("mistakes", [])]
        return render_template("mistakes.html", entries=entries)

    @app.get("/mistakes/practice")
    def mistakes_practice():
        entries = session.get("mistakes", [])
        if not entries:
            return redirect(url_for("mistakes"))
        questions = [{"question": e["question"],
                      "answer": display_answer(e["expected"])}
                     for e in entries]
        session["mistakes_round"] = [
            {"question": e["question"], "expected": e["expected"]}
            for e in entries]
        return render_template("mistakes_practice.html",
                               questions=questions)

    @app.post("/mistakes/practice/submit")
    def mistakes_practice_submit():
        """Wave 5e: finishing the mistakes-retry round shows the
        Badhai card. The round is the classic reveal-answer practice
        (answers are shown on the page), so completing it means the
        student worked through every saved mistake — no score is
        claimed, just the celebration + the count."""
        round_items = session.pop("mistakes_round", None)
        if round_items is None:
            entries = session.get("mistakes", [])
            round_items = [{"question": e["question"],
                            "expected": e["expected"]}
                           for e in entries]
        questions = [{"question": it["question"],
                      "answer": display_answer(it["expected"])}
                     for it in round_items]
        return render_template(
            "mistakes_practice.html", questions=questions,
            round_done=True, round_count=len(round_items))

    @app.post("/mistakes/clear")
    def mistakes_clear():
        session.pop("mistakes", None)
        return redirect(url_for("mistakes"))

    # Wave 14: warm the solver + DB before the first request.
    _warm_up(app)

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
