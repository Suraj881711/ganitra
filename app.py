import base64
import io
import math
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
import zipfile
import xml.etree.ElementTree as ET
from datetime import timedelta
from fractions import Fraction

from flask import (Flask, Response, jsonify, render_template, request,
                   redirect, session, url_for, flash)
from api import (api_bp, trimmed_history_entry,
                 _methods_localised)
from i18n import (LANG_NAMES, SPEECH_LANGS, SUPPORTED_LANGS,
                  advice_for, explanation_for, get_strings,
                  normalise_lang, remark_key_for, result_is_plain,
                  result_unsolvable, solve_failed, teach_for)
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
import practice_gen
import topics_data
from test_mode import (TEST_TIME_LIMIT, TOPIC_LABELS as TEST_TOPICS,
                       check_test_answer, generate_test, worked_steps)
from solver.answer_cache import get_negative, put_negative
from solver.router import solve_question
from fallback import nonmaths_line_for, with_fallback
from notation import annotate_method, annotate_result
from langdetect_local import detect_language_confident, \
    detect_language_request
import accounts
import groups as study_groups
import ocr
import photofix
import gemini_vision
import weak_practice
import full_paper
import progress as progress_mod
import chats
import thoughts
import security

_HISTORY_LIMIT = 30
_MISTAKE_LIMIT = 50
_QUESTION_LIMIT = 500
_SAATHI_NAME_LIMIT = 30
# Wave 10: after this many failed login attempts for one name in a
# session, further attempts get the friendly "try later" message.
_LOGIN_ATTEMPT_LIMIT = 8
# Wave 232 (security): the minimum length for a NEW password —
# set at sign-up, at favourite-login reset, or on the Account
# page. It was 4 (the audit's row); it is 6 now. The check lives
# only where a password is SET: verify-only paths never look at
# the length, so every existing password keeps working exactly
# as before, however short it is.
_PASSWORD_MIN_LENGTH = 6
# Wave 70 (Suraj, 16 Nov 2026): the Logo Jungle scene is OFF —
# "scene se eagle bhi hata do, bilkul khali kar do". The empty
# state shows only the still logo + greeting. All scene code,
# sprites and models stay in the repo, parked behind this flag;
# flip it to True to bring the scene back.
SCENE_ENABLED = False


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


def _short_greeting(strings, name):
    """Wave 155 (Suraj, 18 Nov 2026): the chat home's greeting
    line stays SHORT — just "Hello <name>", the first clause of
    the personalised welcome line in the student's own UI
    language ("नमस्ते <name>" in Hindi, and so on). The day's
    rotating thought rides BELOW it as a small muted line
    (thoughts.py); the long welcome text no longer renders on
    the chat home."""
    line = _personal_line(strings, "saathi_welcome_name",
                          "chat_welcome", name)
    if name and "!" in line:
        return line.split("!", 1)[0].strip()
    return line


def _w178_shown_page(question, result, lang_request=None,
                     lang=None):
    """Wave 178: the repeat-varied copy of a finished
    classic-page answer for DISPLAY, or None (first ask /
    uncountable / any failure — the base result renders
    exactly as before). The classic pages share one
    session history, so they share one counting bucket
    ("page"); the chat API counts per chat instead. The
    session's stored result stays the base — only the
    rendered copy varies (the Wave-138 pattern). An
    explicit language request is a presentation channel,
    never a repeat (see api._w178_shown)."""
    if lang_request:
        return None
    try:
        from repeat import flavour_for, session_variation
        flavour = flavour_for(question, result,
                              lang_request=lang_request,
                              lang=lang)
        return session_variation(session, "page", question,
                                 result, flavour)
    except Exception:
        return None


def _ask_again(question):
    """Wave 5b: re-ask the same question with a gentle pre-filled hint
    appended. The hint is plain English (the router understands plain
    maths English; the friendly card in the default language explains
    the situation before the button is pressed), and the expression
    guard lives in the solver, so this never turns a solvable
    question into a failure."""
    return f"{question} find the value"


def _backnav_for_path(path):
    """Wave 60: the ONE back system (Suraj: "Ganitra ke andar
    back system nahi hai"). Every inner page gets the same
    top-left "← Back" button (rendered by base.html); this pure
    function decides, from the request path alone, whether the
    bar shows and where its no-history fallback points:

    - returns None -> no bar (the chat home / sign-in gate at
      "/", the sign-in POST endpoints whose failure responses
      re-render that same gate — Wave 121 found the bar leaking
      onto it after a failed login — and the in-progress Board
      chapter test, whose template overrides the block with its
      chapter URL and an always-on confirmation);
    - returns (fallback, confirm_if) -> show the bar. The
      button first tries history.back() when the referrer is
      same-origin; `fallback` is only used when there is no
      in-app history (fresh tab, PWA launch, deep link).
      `confirm_if` is a CSS selector for a timed-test element:
      while that element is visible the button first asks with
      the localised nav_back_test_confirm message, because
      leaving would lose the typed answers.
    """
    if path == "/" or path == "/board/test/start":
        return None
    if path in ("/login", "/signup", "/login-favourite"):
        # Wave 121: these POSTs re-render the sign-in gate on
        # failure — the gate is a root screen and gets no bar.
        return None
    if path == "/practice/classic":
        # Wave 121: the classic set's parent is the practice hub.
        return ("/practice", None)
    if path == "/test":
        # Chapter Test: the paper card exists only while a test
        # is running (setup/result need no confirmation).
        return ("/", "#test-paper")
    if path == "/practice/start":
        # The timed classic quiz is on screen only in this
        # POST's response (practice.html's #quiz-form).
        return ("/", "#quiz-form")
    if path == "/practice/submit" or path == "/board/test/submit":
        return ("/practice", None)
    seg = [s for s in path.split("/") if s]
    if seg[:1] == ["board"]:
        if len(seg) <= 2 or seg[1] == "select":
            return ("/board" if len(seg) >= 2 else "/", None)
        if len(seg) == 3:
            return (f"/board/{seg[1]}", None)
        return (f"/board/{seg[1]}/{seg[2]}", None)
    if seg[:1] == ["papers"]:
        if len(seg) >= 3 and seg[2] == "attempt":
            # Wave 121: the exam-mode intro/result live UNDER one
            # paper — their parent is that paper's page, not the
            # whole list. (The attempt itself overrides the block
            # with the same fallback + a confirmation.)
            return (f"/papers/{seg[1]}", None)
        return ("/papers", None) if len(seg) >= 2 else ("/", None)
    if seg[:1] == ["mistakes"] and len(seg) >= 2:
        return ("/mistakes", None)
    if seg[:1] == ["weak-topics"] and len(seg) >= 2:
        # Wave 121: the weak-topic practice/result pages' parent
        # is the weak-topics list, not the chat home.
        return ("/weak-topics", None)
    return ("/", None)


def normalize_ocr_text(text):
    """Conservatively clean text recognised from a photo (Tesseract.js).

    Only unambiguous maths fixes are applied — anything doubtful is left
    untouched so the user can correct it in the editable confirm box:
    unicode minus/dashes -> -, superscript ²/³ -> ^2/^3, ×/✕ -> *,
    ÷ -> /, an X between two digits -> *, and an isolated variable letter
    immediately followed by digits ("x2", "x 2") -> exponent ("x^2").

    Wave 83 adds the classic OCR digit confusions, each fenced in
    by digits so ordinary words can never trip it: an O/o with a
    digit on BOTH sides is a 0 ("1O5" -> "105"), an O right after
    a digit at a token's end is a 0 ("Rs 5O" -> "Rs 50"), an l/I
    between digits or right before a digit is a 1 ("1l5" ->
    "115", "l5" -> "15"), and a leading O before 2+ digits is a
    0 ("O25" -> "025"; a lone "O5" is left alone — O is also the
    origin point in coordinate geometry). Vulgar fractions
    (½ ¼ ¾ …) become a/b, and the remaining superscript digits
    (⁰¹⁴⁵⁶⁷⁸⁹) become ^n like ²/³ already did. These run BEFORE
    the exponent rule below, which would otherwise read "l5" as
    the variable l to the power 5.

    Wave 126 adds the next tier of measured confusions (each one
    seen in the Wave-126 Chromium OCR runs, each fenced so plain
    words cannot trip it): an S/s between digits or an S right
    after a digit at a token's end is a 5 ("3S" -> "35", the
    handwritten "35" the engine read as "3S"), a Z/z between
    digits is a 2, a B between digits is an 8, a g between
    digits is a 9, a digit followed by "o/o" is a percent
    ("15 o/o" -> "15%"), a decimal point split by spaces is
    rejoined ("3. 5" / "3 .5" -> "3.5"), and a V or ✓ touching
    digits with no letter/digit before it is a square root
    ("V625" -> "√625" — the solver reads √ natively; this runs
    before the exponent rule, which would otherwise read "V625"
    as the variable V to the power 625). Deliberately NOT fixed:
    "3°" for 3³ — ° is a real angle mark in geometry, so
    rewriting it would corrupt genuine angle questions; the
    student's editable check path covers that one instead.
    """
    if not text:
        return ""
    t = text
    # Unicode minus and dash variants -> ASCII hyphen-minus
    t = t.replace("−", "-").replace("–", "-").replace("—", "-")
    # Superscript powers OCR sometimes produces
    t = t.replace("²", "^2").replace("³", "^3")
    for sup, digit in (("⁰", "0"), ("¹", "1"), ("⁴", "4"),
                       ("⁵", "5"), ("⁶", "6"), ("⁷", "7"),
                       ("⁸", "8"), ("⁹", "9")):
        t = t.replace(sup, "^" + digit)
    # Vulgar fractions -> a/b (spaced, so "200½" cannot fuse
    # into "2001/2"; the whitespace collapse below tidies up)
    for frac, ab in (("½", "1/2"), ("¼", "1/4"), ("¾", "3/4"),
                     ("⅓", "1/3"), ("⅔", "2/3"), ("⅛", "1/8"),
                     ("⅜", "3/8"), ("⅝", "5/8"), ("⅞", "7/8")):
        t = t.replace(frac, " " + ab + " ")
    # Multiplication / division symbols
    t = t.replace("×", "*").replace("✕", "*").replace("÷", "/")
    # Wave 126: "%" read as "o/o" — must run BEFORE the Wave-83
    # O->0 rule below, which would otherwise eat the first o
    # ("15o/o" -> "150/o" instead of "15%")
    t = re.sub(r"(\d)\s*o/o(?![A-Za-z])", r"\g<1>%", t)
    # Wave 83: digit confusions, fenced by digits (see docstring)
    t = re.sub(r"(\d)[Oo](?=\d)", r"\g<1>0", t)
    t = re.sub(r"(\d)[Oo]\b", r"\g<1>0", t)
    t = re.sub(r"(\d)[lI](?=\d)", r"\g<1>1", t)
    t = re.sub(r"(?<![A-Za-z])[lI](?=\d)", "1", t)
    t = re.sub(r"(?<![A-Za-z0-9])O(?=\d{2,})", "0", t)
    # Wave 126: the next tier of digit confusions (see docstring)
    t = re.sub(r"(\d)[Ss](?=\d)", r"\g<1>5", t)
    t = re.sub(r"(\d)S\b", r"\g<1>5", t)
    t = re.sub(r"(\d)[Zz](?=\d)", r"\g<1>2", t)
    t = re.sub(r"(\d)B(?=\d)", r"\g<1>8", t)
    t = re.sub(r"(\d)g(?=\d)", r"\g<1>9", t)
    t = re.sub(r"(\d)\s*\.\s+(?=\d)", r"\g<1>.", t)
    t = re.sub(r"(\d)\s+\.(?=\d)", r"\g<1>.", t)
    t = re.sub(r"(?<![A-Za-z0-9])[V✓]\s*(?=\d)", "√", t)
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
        # Wave 120 (Suraj, 17 Nov 2026): no "Step-by-step
        # solution:" label line — the steps stand on their
        # own, in the download exactly as on the card.
        lines.append("")
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
        # Wave 46 (audit F1): a hard ceiling on request bodies.
        # The largest legitimate uploads are the 2 MB photo and
        # /file-extract caps, so 4 MB leaves multipart headroom
        # while stopping unbounded spooling of an attacker's body
        # to the 512 MB disk. Bodies past this get a plain 413;
        # the per-route 2 MB friendly errors still fire first for
        # anything under it.
        MAX_CONTENT_LENGTH=4 * 1024 * 1024,
    )

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    # Wave 182: a served PAPER card's body (the whole typed
    # paper in its steps, ~8-11 KB) must never ride in the
    # session cookie — one paper serve in session
    # ["last_result"] pushed the signed cookie past the
    # 4,093-byte browser limit and PythonAnywhere answered
    # live paper requests with a 502. The card is
    # deterministic (paper_requests rebuilds it from
    # paper_id + flavour + year note), so the cookie stores
    # only that small reference: the after-request hook
    # converts any full paper card held as last_result into
    # its reference before the cookie is written, and the
    # before-request hook expands a stored reference back
    # into the full card for the duration of the request,
    # so /download, /solution/print and every follow-up
    # layer keep reading the exact full body, byte for
    # byte, exactly as before this wave.
    # Wave 232 (security): CSRF — every state-changing request
    # that a browser could have been tricked into sending must
    # carry this session's token (security.check_csrf decides
    # when a token is required; GET routes are never checked).
    # Registered on the app, so it covers the /api blueprint
    # exactly like the routes below.
    @app.before_request
    def _wave232_csrf_check():
        return security.check_csrf()

    @app.before_request
    def _wave182_expand_paper_last_result():
        try:
            stored = session.get("last_result")
            if isinstance(stored, dict) \
                    and "_paper_flavour" in stored:
                from paper_requests import expand_paper_ref
                full = expand_paper_ref(stored)
                if full is not None:
                    session["last_result"] = full
        except Exception:
            pass

    @app.after_request
    def _wave182_slim_paper_last_result(resp):
        try:
            stored = session.get("last_result")
            if isinstance(stored, dict):
                from paper_requests import paper_session_ref
                ref = paper_session_ref(stored)
                if ref is not None:
                    session["last_result"] = ref
        except Exception:
            pass
        return resp

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

    # Wave 50 (SEO basics): let search engines find the public
    # site. robots.txt allows everything and points at the
    # sitemap; the sitemap lists ONLY pages an anonymous visitor
    # can actually open (verified 200s) — account pages such as
    # /papers, /practice-mode, /chats and /account redirect
    # anonymous visitors to the sign-in gate, so listing them
    # would send crawlers to a login page. Personal session
    # pages (/history, /mistakes, /parent-report) render the
    # visitor's own state and are likewise left out.
    SITE_ORIGIN = "https://suraj881711.pythonanywhere.com"
    SITEMAP_PATHS = ["/", "/welcome", "/topics", "/board",
                     "/practice", "/test"]

    @app.route("/robots.txt")
    def ganitra_robots():
        body = ("User-agent: *\n"
                "Allow: /\n"
                "Disallow: /api/\n"
                "Disallow: /account\n"
                "Disallow: /chats\n"
                "Disallow: /history\n"
                "Disallow: /logout\n"
                "Disallow: /practice/start\n"
                "Disallow: /practice/submit\n"
                "Disallow: /test/start\n"
                "Disallow: /test/submit\n"
                "Disallow: /solve\n"
                "\n"
                f"Sitemap: {SITE_ORIGIN}/sitemap.xml\n")
        return Response(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def ganitra_sitemap():
        urls = "".join(
            f"<url><loc>{SITE_ORIGIN}{path}</loc></url>"
            for path in SITEMAP_PATHS)
        body = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/'
                f'sitemap/0.9">{urls}</urlset>\n')
        return Response(body, mimetype="application/xml")

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
        # Wave 232 (security): the CSP joins the Wave-17 headers
        # here — see security.py for exactly what the policy
        # allows and what it does not claim to stop.
        security.apply_csp(resp)
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
        # Wave 232 (security): a fresh CSRF token rides the new
        # privilege level — the pre-login token stops validating
        # the moment an account session exists.
        security.rotate_csrf_token()
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
    def inject_csrf_token():
        # Wave 232 (security): base.html carries the token in a
        # meta tag; its script arms every POST form with the
        # hidden field and wraps fetch with the header. Issuing
        # here means any rendered page hands the browser its
        # token — including the sign-in page itself.
        return {"csrf_token": security.issue_csrf_token()}

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
                              "file_btn",
                              "chats_new", "voice_btn", "photo_btn",
                              "solve_btn", "acct_stats_questions",
                              "acct_stats_chats")},
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
            # Wave 70: Logo Jungle scene kill-switch (see
            # SCENE_ENABLED at the top of this file).
            "scene_enabled": SCENE_ENABLED,
            "saathi_edit": request.args.get("saathi") == "edit",
            "saathi_greeting": _personal_line(
                strings, "saathi_welcome_name", "chat_welcome",
                saathi_name),
            # Wave 155 (Suraj, 18 Nov 2026): the chat home's
            # greeting stays SHORT ("Hello <name>") and the
            # current time slot's rotating thought — 10 a day,
            # time-divided (thoughts.py) — rides below it as a
            # small muted line. The thought's variant follows
            # the session language, the same machinery the
            # greeting itself used.
            "saathi_greeting_short": _short_greeting(
                strings, saathi_name),
            "daily_thought": thoughts.thought_text(lang=lang),
            "saathi_encouragement": _personal_line(
                strings, "saathi_wrong_name", "saathi_wrong",
                saathi_name),
            "error_encouragement": _personal_line(
                strings, "error_encourage_name", "error_encourage",
                saathi_name),
        }

    @app.context_processor
    def inject_backnav():
        # Wave 60: feed base.html's back bar from the path map
        # (see _backnav_for_path). Templates that need a custom
        # target (the Board chapter test) override the block.
        spec = _backnav_for_path(request.path)
        if spec is None:
            return {"backnav": None}
        fallback, confirm_if = spec
        nav = {"fallback": fallback}
        if confirm_if:
            nav["confirm_if"] = confirm_if
            nav["confirm_msg"] = _t()["nav_back_test_confirm"]
        return {"backnav": nav}

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
        # Wave 131: the chat page learns whether the streamed
        # solve endpoint is live (GANITRA_AI_STREAM) — with the
        # flag off (the default) the page renders
        # AI_STREAM=false and behaves exactly as before.
        from ai_stream import stream_enabled
        return render_template(
            "index.html", ai_stream_enabled=stream_enabled())

    # ------------------------------------------------------ wave 10 auth
    @app.post("/signup")
    def signup():
        form = {key: request.form.get(key, "")
                for key in ("name", "class", "board", "goal",
                            "hobby", "favourite", "password")}
        strings = _t()
        # Wave 232 (security): the per-IP failed-auth throttle —
        # this IP has burned its failure budget across the auth
        # endpoints, so it waits, whatever name it tries next.
        if security.auth_ip_throttled():
            return _signin("signup", strings["auth_err_lockout"],
                           form)
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
        if len(form["password"]) < _PASSWORD_MIN_LENGTH:
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
            security.record_auth_ip_failure()
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
        # Wave 232 (security): per-IP throttle first — a sprayer
        # rotating through names meets the same wall everywhere.
        if security.auth_ip_throttled():
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name})
        if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name})
        user = accounts.get_user(name)
        if user is None or not accounts.verify_password(user, password):
            # One friendly error for both cases — never a hint
            # about which part (name vs password) was wrong.
            _record_failed_login(key)
            security.record_auth_ip_failure()
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
        # Wave 232 (security): the per-IP throttle guards the
        # favourite door exactly like the password door.
        if security.auth_ip_throttled():
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name}, fav_error=True)
        if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
            return _signin("login", strings["auth_err_lockout"],
                           {"name": name}, fav_error=True)
        user = accounts.get_user(name)
        if user is None or not accounts.verify_favourite(user, typed):
            _record_failed_login(key)
            security.record_auth_ip_failure()
            if _failed_logins(key) >= _LOGIN_ATTEMPT_LIMIT:
                return _signin("login",
                               strings["auth_err_lockout"],
                               {"name": name}, fav_error=True)
            return _signin("login", strings["auth_err_fav"],
                           {"name": name}, fav_error=True)
        if len(new_password) < _PASSWORD_MIN_LENGTH:
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
        if len(new) < _PASSWORD_MIN_LENGTH:
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
        # Wave 46 (audit F5): read at most the cap + 1 byte and
        # enforce the size limit BEFORE the bytes are parsed —
        # the old code read the whole upload into memory first
        # and only measured it afterwards. Mirrors /file-extract.
        data = upload.stream.read(_PHOTO_MAX_BYTES + 1)
        if len(data) > _PHOTO_MAX_BYTES:
            return _account_page(user,
                                 strings["acct_err_photo_size"])
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
            # Wave 233: the menu line reads "{count} questions
            # solved" — it is fed by solved_count (served
            # answers in the student's own chats), not by the
            # asked-turns count it used before.
            "questions": accounts.solved_count(user["id"]),
            "chats": accounts.chats_count(user["id"]),
        })

    # ------------------------------------------------- wave 233 errors
    # Localised error pages: Flask's built-in 404/500 pages are
    # English-only, so a Hindi (or Bengali / Marathi / Tamil /
    # Telugu) student who followed a stale link met a foreign
    # page. API paths keep a JSON body; page paths get a short
    # page in the student's own language. Explicit 404 returns
    # (e.g. a missing account photo) are unaffected — handlers
    # only fire for unmatched routes and real server errors.
    def _error_page(key, status):
        strings = _t()
        if request.path.startswith("/api/"):
            return jsonify({
                "ok": False,
                "error": "not_found" if status == 404
                         else "server_error",
                "message": strings[key],
            }), status
        body = (
            "<!doctype html><html><head><meta charset=\"utf-8\" />"
            "<title>Ganitra</title></head><body>"
            f"<p>{strings[key]}</p>"
            f"<p><a href=\"/\">{strings['error_page_home']}</a></p>"
            "</body></html>")
        return Response(body, status=status,
                        mimetype="text/html")

    @app.errorhandler(404)
    def _wave233_not_found(_err):
        return _error_page("error_page_not_found", 404)

    @app.errorhandler(500)
    def _wave233_server_error(_err):
        return _error_page("error_page_server", 500)

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

    # -- Wave 213: Group Study (menu-only entry; see groups.py).
    # Chat + study groups keyed to mobile numbers. The base
    # login is untouched; only these routes ask for a number.

    def _groups_page(user, error=None, notice=None, failures=None):
        return render_template(
            "groups.html", user_id=user["id"],
            my_phone=study_groups.get_phone(user["id"]),
            my_groups=study_groups.list_groups_for(user["id"]),
            error=error, notice=notice, failures=failures or [])

    @app.get("/groups")
    def groups_view():
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        return _groups_page(user)

    @app.post("/groups/phone")
    def groups_phone():
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        phone, error = study_groups.set_phone(
            user["id"], request.form.get("phone", ""))
        if error:
            return _groups_page(user, error=error)
        return _groups_page(
            user, notice=f"Mobile number {phone} add ho gaya.")

    @app.post("/account/phone")
    def account_phone():
        # The same number, settable from the profile side too;
        # it only ever feeds Group Study (groups.py owns it).
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        phone, error = study_groups.set_phone(
            user["id"], request.form.get("phone", ""))
        if error:
            return _groups_page(user, error=error)
        return _groups_page(
            user, notice=f"Mobile number {phone} add ho gaya.")

    @app.post("/groups/create")
    def groups_create():
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        raw = request.form.get("member_phones", "")
        texts = [p for p in re.split(r"[\s,;]+", raw) if p]
        group, failures, error = study_groups.create_group(
            user["id"], request.form.get("name", ""), texts)
        if error:
            return _groups_page(user, error=error, failures=failures)
        if failures:
            # The group exists, but some numbers could not be
            # added (Suraj's rule: no number, no membership) —
            # say exactly which and why instead of hiding it.
            return _groups_page(
                user, failures=failures,
                notice=f"Group '{group['name']}' ban gaya, lekin "
                       "kuch number add nahi ho paye:")
        return redirect(url_for("group_view", group_id=group["id"]))

    def _group_page(user, group, error=None, notice=None):
        members = study_groups.list_members(group["id"])
        viewer_is_admin = group["admin_id"] == user["id"]
        if not viewer_is_admin:
            for m in members:
                m.pop("phone", None)
        return render_template(
            "group.html", user_id=user["id"], group=group,
            members=members, is_admin=viewer_is_admin,
            posts=study_groups.list_posts(group["id"]),
            error=error, notice=notice)

    @app.get("/groups/<int:group_id>")
    def group_view(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        group = study_groups.get_group(group_id)
        if group is None or not study_groups.is_member(
                group_id, user["id"]):
            return _groups_page(
                user, error=_t()["group_err_not_member"])
        return _group_page(user, group)

    @app.post("/groups/<int:group_id>/post")
    def group_post(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        reply_raw = request.form.get("reply_to", "")
        reply_to = int(reply_raw) if reply_raw.isdigit() else None
        _post, _ganitra, error = study_groups.post_message(
            group_id, user["id"], request.form.get("text", ""),
            reply_to=reply_to)
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(user, group, error=error)

    @app.post("/groups/<int:group_id>/add")
    def group_add(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        ok, error = study_groups.add_member(
            group_id, user["id"], request.form.get("phone", ""))
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(
            user, group, error=error,
            notice=_t()["group_notice_member_added"]
            if ok else None)

    @app.post("/groups/<int:group_id>/remove")
    def group_remove(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        target = request.form.get("user_id", "")
        ok, error = study_groups.remove_member(
            group_id, user["id"],
            int(target) if target.isdigit() else -1)
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(
            user, group, error=error,
            notice=_t()["group_notice_member_removed"]
            if ok else None)

    @app.post("/groups/<int:group_id>/leave")
    def group_leave(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        ok, error = study_groups.leave_group(group_id, user["id"])
        if ok:
            return redirect(url_for("groups_view"))
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(user, group, error=error)

    @app.post("/groups/<int:group_id>/close")
    def group_close(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        ok, error = study_groups.close_group(group_id, user["id"])
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(
            user, group, error=error,
            notice=_t()["group_notice_closed"] if ok else None)

    @app.post("/groups/<int:group_id>/report")
    def group_report(group_id):
        user = _account_user()
        if user is None:
            return redirect(url_for("index"))
        post_raw = request.form.get("post_id", "")
        ok, error = study_groups.report_post(
            group_id, user["id"],
            int(post_raw) if post_raw.isdigit() else -1,
            request.form.get("reason", ""))
        group = study_groups.get_group(group_id)
        if group is None:
            return redirect(url_for("groups_view"))
        return _group_page(
            user, group, error=error,
            notice=_t()["group_notice_reported"] if ok else None)

    # -- Wave 213: owner dashboard (Suraj's account, id 1 only).

    def _owner_page(error=None, notice=None):
        all_groups, reports = study_groups.owner_overview()
        return render_template(
            "owner_groups.html", all_groups=all_groups,
            reports=reports, error=error, notice=notice)

    @app.get("/owner/groups")
    def owner_groups_view():
        user = _account_user()
        if user is None or user["id"] != study_groups.OWNER_ID:
            return redirect(url_for("index"))
        return _owner_page()

    @app.post("/owner/groups/<int:group_id>/close")
    def owner_group_close(group_id):
        user = _account_user()
        if user is None or user["id"] != study_groups.OWNER_ID:
            return redirect(url_for("index"))
        ok, error = study_groups.close_group(
            group_id, user["id"], owner=True)
        return _owner_page(
            error=error,
            notice=_t()["group_notice_closed"] if ok else None)

    @app.post("/owner/groups/<int:group_id>/remove")
    def owner_group_remove(group_id):
        user = _account_user()
        if user is None or user["id"] != study_groups.OWNER_ID:
            return redirect(url_for("index"))
        target = request.form.get("user_id", "")
        ok, error = study_groups.remove_member(
            group_id, user["id"],
            int(target) if target.isdigit() else -1, owner=True)
        return _owner_page(
            error=error,
            notice=_t()["group_notice_member_removed"]
            if ok else None)

    @app.get("/topics")
    def topics():
        """Wave 7: the topic list that used to sit under the chat on
        the homepage now lives on its own simple page — the home
        page is a pure chat screen (ChatGPT-style), nothing else.

        Wave 55: below the original subject cards, the page now
        also carries the per-class topic directory from
        topics_data.py — every NCERT chapter for Classes 6-12
        broken into its teachable sub-topics, each with its method
        (idea + steps), one verified worked example, and a link to
        its parent chapter (chapter page + practice + test)."""
        class_topics = []
        for class_num in topics_data.CLASS_NUMBERS:
            rows = []
            for topic in topics_data.topics_for_class(class_num):
                chapter = get_chapter(class_num, topic["chapter"])
                row = dict(topic)
                row["chapter_title"] = (
                    chapter["title"] if chapter else topic["chapter"])
                rows.append(row)
            class_topics.append(
                {"class_num": class_num, "topics": rows})
        return render_template("topics.html", class_topics=class_topics)

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
        # Wave 107: an explicit language request in the message
        # outranks detection here too (same rule as the chat
        # API), and the request phrase is stripped from the text
        # that is solved (solve_text); the page still shows the
        # student's original message as the question.
        lang_request = None
        solve_text = question
        req = detect_language_request(question)
        if req is not None:
            lang_request, req_cleaned = req
            if req_cleaned:
                solve_text = req_cleaned
            req_lang = ("hi" if lang_request in ("hi", "hinglish")
                        else "en")
            if req_lang != _lang():
                session["lang"] = req_lang
        else:
            detected, solid = detect_language_confident(question)
            if solid and detected != _lang():
                session["lang"] = detected
        # Wave 48: same negative-cache seam as api._solve_friendly
        # — a recently-failed question serves its finished fallback
        # result instead of re-paying the whole solve.
        # Wave 107: keyed per explicit language request, as
        # in api._solve_friendly.
        neg_variant = lang_request
        result = get_negative(solve_text, variant=neg_variant)
        if result is None:
            result = solve_question(solve_text)
            # Wave 5b: on failure, gently re-ask once with a hint;
            # the second result decides what the student sees.
            if solve_failed(solve_text, result):
                retry = solve_question(_ask_again(solve_text))
                if not solve_failed(solve_text, retry):
                    result = retry
            # Wave 18: no dead-end — failures, letter-soup
            # "answers" and soft non-answers become honest fallback
            # answers (salvage / concept / similar example /
            # friendly guide), so the error card below is now only
            # a last resort that the fallback itself could not
            # cover.
            result = with_fallback(
                solve_text, result, lang=_lang(),
                student_class=session.get("saathi_class"),
                lang_request=lang_request)
            put_negative(solve_text, result,
                         variant=neg_variant)
        failed = solve_failed(solve_text, result)
        # Wave 67: a one-line response (not-found / maths-only
        # guard) gets NO explanation, advice, methods or teach
        # extras on the answer page either — just its line.
        quiet = failed or result_is_plain(result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        # Wave 46 (audit F4): trimmed entry — see
        # api.trimmed_history_entry.
        history.insert(0, trimmed_history_entry(question, result))
        session["history"] = history[:_HISTORY_LIMIT]
        # Wave 178: a repeat ask renders a varied copy of the
        # answer (see _w178_shown_page) — the session's
        # stored result above stays the base, exactly like
        # the Wave-138 display annotation below.
        shown178 = _w178_shown_page(
            solve_text, result, lang_request=lang_request,
            lang=_lang())
        return render_template("answer.html", question=question,
                               # Wave 211: the template brings
                               # back the one-line explanation
                               # ONLY for an explicit language
                               # request serve (see answer.html);
                               # a no-request page renders exactly
                               # as Wave 208 left it.
                               lang_requested=(
                                   lang_request is not None),
                               # Wave 138: typeset variants are a
                               # display concern — annotated on a
                               # copy for the template only; the
                               # session's stored result (print,
                               # history) stays the solver's own.
                               result=annotate_result(
                                   dict(shown178 or result)),
                               explanation=(None if quiet
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if quiet
                                       else advice_for(result, _lang())),
                               # Wave 14: same non-blocking
                               # auto-teach budget as /api/solve.
                               # Wave 130: an explicit language
                               # request relanguages the method
                               # steps too (api._methods_localised
                               # does the same for the chat API).
                               methods=([] if quiet
                                        else [annotate_method(m)
                                              for m in
                                              _methods_localised(
                                                  solve_text,
                                                  result,
                                                  lang_request)]),
                               teach=([] if quiet
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

    _PDF_RENDER_MAX_PIXELS = 2_000_000  # ~2 megapixels
    _PDF_RENDER_MAX_DPI = 150           # the historical fixed DPI

    def _pdf_render_dpi(data):
        """The DPI at which pdftoppm may render this PDF's first
        page so the output stays within ~2 MP, however large the
        page CLAIMS to be. Wave 46 (audit F1b): the render used a
        fixed 150 DPI with no page-size cap, so a 433-byte blank
        PDF whose MediaBox claims 7920x7920 pt (110 in square)
        rendered at 16,500x16,500 px — 23 s and ~1 GB RAM, from
        an anonymous route. Normal pages (A4 and friends) still
        get ~150 DPI; only absurd pages scale down. The size is
        the max of MediaBox and CropBox, times any /UserUnit
        scale, so a small MediaBox cannot hide a huge page.
        Returns None when the size cannot be read — the caller
        then caps the render with pdftoppm's own -scale-to."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            if not reader.pages:
                return None
            page = reader.pages[0]
            width = height = 0.0
            for box in (page.mediabox, page.cropbox):
                width = max(width, abs(float(box.width)))
                height = max(height, abs(float(box.height)))
            try:
                unit = abs(float(page.user_unit or 1.0))
            except Exception:
                unit = 1.0
            width *= unit
            height *= unit
        except Exception:
            return None
        if width <= 0 or height <= 0:
            return None
        # pixels = (w/72 * dpi) * (h/72 * dpi) <= MAX_PIXELS
        dpi = 72.0 * math.sqrt(
            _PDF_RENDER_MAX_PIXELS / (width * height))
        return max(1, min(_PDF_RENDER_MAX_DPI, int(dpi)))

    def _pdf_first_page_png(data):
        """A PDF's first page rendered to PNG bytes by poppler
        (pdftoppm), or None when poppler is missing or the
        render fails. Wave 46 (audit F1b): the render is capped
        at ~2 MP of output (see _pdf_render_dpi) and the
        subprocess timeout drops from 30 s to 10 s."""
        exe = shutil.which("pdftoppm")
        if not exe:
            return None
        dpi = _pdf_render_dpi(data)
        if dpi is not None:
            size_args = ["-r", str(dpi)]
        else:
            side = int(math.sqrt(_PDF_RENDER_MAX_PIXELS))
            size_args = ["-scale-to", str(side)]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                src = os.path.join(tmp, "in.pdf")
                with open(src, "wb") as fh:
                    fh.write(data)
                subprocess.run(
                    [exe, "-png", "-f", "1", "-l", "1",
                     *size_args,
                     src, os.path.join(tmp, "page")],
                    check=True, timeout=10,
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

    @app.post("/photo-ocr")
    def photo_ocr():
        # Wave 83: SERVER-side OCR of a photographed question,
        # behind the pluggable backend in ocr.py. Same upload
        # rules as /file-extract (2 MB cap, magic bytes, nothing
        # stored — the bytes live in memory and the backend's
        # throwaway temp dir only, and are dropped with the
        # request). Replies the chat script understands:
        #   {"kind": "text", "text": ..., "confidence": ...,
        #    "low_confidence": bool, "backend": ...}
        #        -> the recognised question, already cleaned by
        #           normalize_ocr_text; low_confidence asks the
        #           script to show it for editing BEFORE solving
        #   {"ok": false, "code": "ocr_unavailable"}
        #        -> this host has no OCR engine (today's
        #           PythonAnywhere free tier is one) — the script
        #           falls back to the browser Tesseract.js flow,
        #           never a fake read
        #   {"ok": false, "code": "ocr_failed" | "empty" |
        #    "too_large" | "unsupported"} -> same fallback.
        upload = request.files.get("file")
        if upload is None:
            return jsonify({"ok": False, "code": "no_file"}), 400
        data = upload.stream.read(_FILE_MAX_BYTES + 1)
        if len(data) > _FILE_MAX_BYTES:
            return jsonify({"ok": False, "code": "too_large"})
        is_image = _photo_kind(data) or data[:4] == b"GIF8" or \
            data[:2] == b"BM" or \
            (data[:4] == b"RIFF" and data[8:12] == b"WEBP") or \
            (data[4:8] == b"ftyp" and data[8:12] in
             (b"heic", b"heix", b"mif1", b"msf1"))
        if not is_image:
            return jsonify({"ok": False, "code": "unsupported"})
        try:
            outcome = ocr.ocr_image(data)
        except ocr.OcrUnavailable:
            return jsonify({"ok": False,
                            "code": "ocr_unavailable"})
        except ocr.OcrFailed:
            return jsonify({"ok": False, "code": "ocr_failed"})
        text = normalize_ocr_text(outcome.text)
        if not text:
            return jsonify({"ok": False, "code": "empty"})
        payload = {
            "kind": "text",
            "text": text[:_FILE_TEXT_LIMIT],
            "confidence": (None if outcome.confidence is None
                           else round(outcome.confidence, 1)),
            "low_confidence": bool(outcome.low_confidence),
            "backend": outcome.backend,
        }
        if outcome.low_confidence:
            # Wave 137: a weak read earns the partial-read
            # analysis — when the surviving words identify the
            # question family, the composer is prefilled with
            # the REBUILT question (plus at most one short
            # confirmation line) instead of the raw garble.
            # No match -> no extra fields -> Wave 126 behaviour.
            fixed = photofix.analyse(text)
            if fixed is not None:
                payload["prefill"] = fixed["question"]
                payload["confirm"] = fixed["confirm"]
        return jsonify(payload)

    def _vision_mime(data):
        """The IANA mime type for an upload's MAGIC BYTES (the
        same image set /photo-ocr accepts), or None — the
        vision API needs the type declared, and it is never
        taken from the file name."""
        kind = _photo_kind(data)
        if kind == "png":
            return "image/png"
        if kind == "jpeg":
            return "image/jpeg"
        if data[:4] == b"GIF8":
            return "image/gif"
        if data[:2] == b"BM":
            return "image/bmp"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        if data[4:8] == b"ftyp" and data[8:12] in \
                (b"heic", b"heix", b"mif1", b"msf1"):
            return "image/heic"
        return None

    @app.post("/photo-vision")
    def photo_vision():
        # Wave 144: the photo system's PRIMARY read — Gemini
        # vision TRANSCRIBES the photographed question (see
        # gemini_vision.py; it never solves). Same upload rules
        # as /photo-ocr (2 MB cap, magic bytes, nothing stored:
        # the bytes live in memory for this request only and
        # are dropped with it). Replies the chat script
        # understands:
        #   {"kind": "text", "text": ..., "prefill": ...,
        #    "confirm": ... | null, "backend": "gemini-vision"}
        #        -> the transcription, which the script ALWAYS
        #           lands in the editable composer (never
        #           auto-solved): prefill is the Wave 137
        #           reconstruction when photofix found an
        #           unclear slot (confirm names it, at most
        #           one line), else the transcription itself.
        #   {"ok": false, "code": "vision_unavailable" |
        #    "vision_quota" | "vision_failed"}
        #        -> the script falls back silently to the old
        #           chain (/photo-ocr -> browser Tesseract).
        #   {"ok": false, "code": "no_question"}
        #        -> the photo WAS read; there is no readable
        #           question in it at all (blank / too blurry).
        #           No fallback (a second read would only
        #           garble) — the script says the one honest
        #           not-found line.
        #   {"ok": false, "code": "not_maths", "message": ...}
        #        -> Wave 203: the photo WAS read and its
        #           question is readable — but it is not maths.
        #           The message is the maths-only one-liner (the
        #           typed guard's own line, in the read
        #           question's flavour). Never the not-found
        #           line: the question WAS found, and "send a
        #           clear photo again" would loop forever.
        #   {"ok": false, "code": "too_large" | "unsupported" |
        #    "no_file"} -> same meanings as /photo-ocr.
        #        A success payload gains a "notice" field only
        #        when the photo held further questions beyond
        #        the first (Wave 203 MORE channel).
        upload = request.files.get("file")
        if upload is None:
            return jsonify({"ok": False, "code": "no_file"}), 400
        data = upload.stream.read(_FILE_MAX_BYTES + 1)
        if len(data) > _FILE_MAX_BYTES:
            return jsonify({"ok": False, "code": "too_large"})
        mime = _vision_mime(data)
        if mime is None:
            return jsonify({"ok": False, "code": "unsupported"})
        try:
            outcome = gemini_vision.transcribe_detailed(data, mime)
        except gemini_vision.VisionUnavailable:
            return jsonify({"ok": False,
                            "code": "vision_unavailable"})
        except gemini_vision.VisionQuota:
            return jsonify({"ok": False, "code": "vision_quota"})
        except gemini_vision.VisionFailed:
            return jsonify({"ok": False, "code": "vision_failed"})
        if outcome["outcome"] == "not_maths":
            return jsonify({
                "ok": False, "code": "not_maths",
                "message": nonmaths_line_for(
                    outcome.get("read") or "")})
        text = outcome["text"]
        if outcome["outcome"] != "text" or not text:
            return jsonify({"ok": False, "code": "no_question"})
        payload = {
            "kind": "text",
            "text": text[:_FILE_TEXT_LIMIT],
            "prefill": text[:_FILE_TEXT_LIMIT],
            "confirm": None,
            "backend": "gemini-vision",
        }
        # Wave 137 discipline, unchanged: when the surviving
        # words identify the family but a slot is unclear, the
        # composer is prefilled with the REBUILT question plus
        # the one confirmation line — never a silent guess.
        # Wave 203 (audit fix 5): photofix reads the RAW
        # transcription — gemini_vision.py's contract is that
        # the OCR normaliser never rewrites vision text (its
        # digit-fenced corrections are for Tesseract garble;
        # a vision read is not garble).
        fixed = photofix.analyse(text)
        if fixed is not None and fixed.get("confirm"):
            payload["prefill"] = fixed["question"]
            payload["confirm"] = fixed["confirm"]
        if payload["confirm"] is None and outcome["unsure"]:
            # Wave 203 (audit fix 2): the vision model itself
            # flagged a span it could not read surely — the
            # photofix-style ONE confirmation line names it.
            # The read still only prefills the composer; the
            # flagged guess is never solved unseen.
            line = photofix.unsure_confirm(text,
                                           outcome["unsure"])
            if line:
                payload["confirm"] = line
        if outcome["more"]:
            # Wave 203 (audit fix 4): the photo held further
            # questions; only the first was taken and the
            # student is TOLD so (one line, system text).
            payload["notice"] = photofix.more_notice(text)
        return jsonify(payload)

    @app.post("/photo-fix")
    def photo_fix():
        # Wave 137: partial-read analysis for the BROWSER OCR
        # flow (the server backend above is unavailable on the
        # free host, so the browser's weak reads come here).
        # The chat script posts the recognised text whenever
        # Wave 126's confidence gate decides the read must be
        # checked before solving; the reply either carries a
        # rebuilt question (+ at most one confirmation line)
        # for the editable composer, or {"reconstructed":
        # false}, which leaves the raw text in the composer
        # exactly as Wave 126 did. This route NEVER solves
        # anything — a reconstruction reaches the solver only
        # after the student sees it, fixes it and presses
        # Solve himself (Suraj's rule: pehle confirm, phir
        # solve).
        data = request.get_json(silent=True) or {}
        raw = data.get("text") or request.form.get("text") or ""
        text = normalize_ocr_text(raw)
        if not text:
            return jsonify({"ok": False, "code": "empty"})
        fixed = photofix.analyse(text)
        if fixed is None:
            return jsonify({"ok": True, "reconstructed": False})
        return jsonify({"ok": True, "reconstructed": True,
                        "question": fixed["question"],
                        "confirm": fixed["confirm"]})

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
        # Wave 48: negative-cache seam, as in /solve above.
        result = get_negative(question)
        if result is None:
            result = solve_question(question)
            if solve_failed(question, result):
                retry = solve_question(_ask_again(question))
                if not solve_failed(question, retry):
                    result = retry
            # Wave 18: same no-dead-end fallback as /solve.
            result = with_fallback(
                question, result, lang=_lang(),
                student_class=session.get("saathi_class"))
            put_negative(question, result)
        failed = solve_failed(question, result)
        # Wave 67: one-line responses get no extras (as /solve).
        quiet = failed or result_is_plain(result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        # Wave 46 (audit F4): trimmed entry — see
        # api.trimmed_history_entry.
        history.insert(0, trimmed_history_entry(question, result))
        session["history"] = history[:_HISTORY_LIMIT]
        # Wave 178: repeat-ask variation, as in /solve above
        # (the photo route shares the "page" counting
        # bucket; the session keeps the base result).
        shown178 = _w178_shown_page(question, result,
                                    lang=_lang())
        return render_template("answer.html", question=question,
                               # Wave 138: as in /solve above.
                               result=annotate_result(
                                   dict(shown178 or result)),
                               photo_text=question,
                               source=source,
                               explanation=(None if quiet
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if quiet
                                       else advice_for(result, _lang())),
                               # Wave 14: same non-blocking
                               # auto-teach budget as /api/solve.
                               methods=([] if quiet
                                        else [annotate_method(m)
                                              for m in
                                              methods_nonblocking(
                                                  question,
                                                  result)]),
                               teach=([] if quiet
                                      else teach_for(result, _lang())),
                               unsolvable=failed)

    # Public identity page (Suraj, 23 Nov 2026): anyone arriving
    # from Google sees what Ganitra is — Classes 1–12 maths, free,
    # step-by-step answers, the robot, and one clear button into
    # the app. A separate page on purpose: the app's own pages
    # and flow are untouched.
    @app.get("/welcome")
    def welcome():
        return render_template("welcome.html")

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
        session Mistake Notebook and the last test report. There
        is no account or cloud record behind it. (Wave 106: the
        Dhyaan localStorage record the page's JS used to read was
        removed on Suraj's order.)"""
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

    # ------------------------------------------------- wave 89 progress
    def _progress_page_data():
        """Wave 89: the My Progress record for the signed-in
        student — account data aggregated by progress.py from
        the chats/users tables (questions asked/answered,
        chats, weekly activity, learning-since), plus the two
        session-side pieces that exist nowhere else: the
        Mistake Notebook (weak-topic counts, labelled exactly
        like the Wave 6 Parent Report) and the last test
        report. Only the caller's own rows are ever read."""
        uid = session.get("user_id")
        user = accounts.get_user_by_id(uid)
        strings = _t()
        mistakes = session.get("mistakes", [])
        counts, order = {}, []
        for entry in mistakes:
            source = (entry.get("source") or "").strip()
            topic = (entry.get("topic") or "").strip()
            if source and source != "quiz":
                label = source
            elif topic:
                label = strings.get(f"quiz_topic_{topic}", topic)
            else:
                label = ""
            if not label:
                continue
            if label not in counts:
                counts[label] = 0
                order.append(label)
            counts[label] += 1
        weak = [{"label": label, "count": counts[label]}
                for label in order]
        weak.sort(key=lambda w: -w["count"])
        last_report = session.get("last_test_report") or None
        last_score_text = None
        if last_report:
            last_score_text = (f"{last_report.get('score', 0)} / "
                               f"{last_report.get('total', 0)}")
        return {
            "progress": progress_mod.collect_progress(uid),
            "account_name": user["name"] if user else "",
            "class_num": user["class_num"] if user else None,
            "board_text": user["board_text"] if user else "",
            "since_text": progress_mod.format_date(
                user["created_at"]) if user else None,
            "weak_topics": weak[:5],
            "mistakes_count": len(mistakes),
            "last_report": last_report,
            "last_score_text": last_score_text,
        }

    @app.get("/progress")
    def progress_page():
        """Wave 89: My Progress — the student's own record,
        to show a parent or teacher. An account page like
        /chats: anonymous visitors go back to the sign-in
        gate at /."""
        if not session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("progress.html",
                               **_progress_page_data())

    @app.get("/progress/print")
    def progress_print():
        """Wave 89: the print-friendly My Progress sheet
        (standalone, like the papers print view) — share it
        as a printout or a browser-saved PDF."""
        if not session.get("user_id"):
            return redirect(url_for("index"))
        return render_template("progress_print.html",
                               **_progress_page_data())

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

    # ------------------------------------------------- wave 43 tests
    # Chapter Test Mode: a timed 10-question test over the
    # practice_gen topics (Classes 6-10), scored EXACTLY with
    # fractions (test_mode.py) — the Board Mode chapter test
    # (Wave 5) covers NCERT chapters; this one covers the topic
    # generator that had no route until now. Like /practice it is
    # an open page (no sign-in gate); the answers stay server-side
    # in the session and are never sent to the browser.
    def _test_labels():
        strings = _t()
        return {topic: strings.get(f"quiz_topic_{topic}", label)
                for topic, label in TEST_TOPICS.items()}

    @app.get("/test")
    def chapter_test():
        return render_template(
            "test.html", classes=practice_gen.CLASSES,
            topics=practice_gen.TOPICS, labels=_test_labels(),
            time_limit=TEST_TIME_LIMIT)

    @app.post("/test/start")
    def chapter_test_start():
        data = request.get_json(silent=True) or request.form
        try:
            class_num = int(data.get("class_num", ""))
        except (TypeError, ValueError):
            class_num = -1
        topic = str(data.get("topic", "")).strip()
        if (class_num not in practice_gen.CLASSES
                or topic not in practice_gen.TOPICS):
            return jsonify({"ok": False,
                            "error": "bad_class_or_topic"}), 400
        items = generate_test(class_num, topic)
        session["topic_test"] = {
            "class_num": class_num, "topic": topic, "items": items}
        return jsonify({
            "ok": True,
            "class_num": class_num,
            "topic": topic,
            "topic_label": _test_labels().get(topic, topic),
            "time_limit_seconds": TEST_TIME_LIMIT,
            "questions": [{"question": it["question"]}
                          for it in items],
        })

    @app.post("/test/submit")
    def chapter_test_submit():
        test = session.get("topic_test")
        if not test:
            return jsonify({"ok": False,
                            "error": "no_test_in_progress"}), 400
        data = request.get_json(silent=True) or {}
        answers = data.get("answers")
        if not isinstance(answers, list):
            answers = []
        try:
            time_taken = int(data.get("time_taken", ""))
        except (TypeError, ValueError):
            time_taken = None
        rows, score = [], 0
        for i, item in enumerate(test["items"]):
            given = answers[i] if i < len(answers) else ""
            if given is None:
                given = ""
            ok = check_test_answer(item, str(given))
            score += 1 if ok else 0
            rows.append({
                "question": item["question"],
                "expected": item["answer"],
                "given": str(given),
                "correct": ok,
                "topic": test["topic"],
                "steps": worked_steps(item),
            })
        _record_mistakes(
            rows, f"Class {test['class_num']} · "
                  f"{_test_labels().get(test['topic'], test['topic'])}"
                  " test")
        _copycheck(rows, score, len(rows),
                   {test["topic"]: _test_labels().get(
                       test["topic"], test["topic"])})
        session.pop("topic_test", None)
        return jsonify({
            "ok": True,
            "score": score,
            "total": len(rows),
            "time_taken": time_taken,
            "rows": rows,
        })

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
            "print.html", question=question,
            # Wave 138: typeset variants on a display copy.
            result=annotate_result(dict(result)),
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

    # ------------------------------------------------- wave 63 typed papers
    # Wave 63 (Suraj, 15 Nov 2026): "practice paper kaa link nhi
    # chahiye" — no external links anywhere in the Previous Papers
    # flow. Every stored paper now opens INSIDE the app, typed out
    # like the real exam paper (the sheet partial
    # templates/_paper_sheet.html, shared by the paper page and
    # the stored-paper print view). The helpers below build that
    # sheet from papers_data ONLY:
    # - question text is never added to, dropped or reworded —
    #   _paper_q_lines only inserts display line-breaks (internal
    #   choices, sub-parts, MCQ options) into the stored text;
    # - a question that leans on a figure printed in the real
    #   paper (the data holds no figures) gets a neat [Figure]
    #   marker under its text;
    # - the header's Maximum Marks and the instruction counts are
    #   the REAL paper's totals, derived from the stored sections
    #   plus the omissions the data itself records (numbering
    #   gaps, and section deficits where a section follows the
    #   standard pattern's count and marks — e.g. a last
    #   case-study question the transcription could not keep).
    #   Time allowed is not in the data, so the header omits it.
    _FIGURE_REF = re.compile(
        r"in the (given )?figure|given figure|figure below|in fig\b"
        r"|in figure\b|as shown in fig|diagram printed in the paper"
        r"|venn diagram represents|shown in the paper \(figures",
        re.IGNORECASE)
    # Wave 64: the same figure-reference test for the Hindi-medium
    # papers — the printed Hindi phrases that point at a figure the
    # data does not hold (a labelled diagram / graph / Venn /
    # matchstick pattern). Draw-it-yourself instructions ("आकृति
    # खींचिए", "आलेख बनाइए") and decorative photos (which the
    # question text never leans on) do NOT match, mirroring the
    # English rule.
    _FIGURE_REF_HI = re.compile(
        r"दी गई आकृति|निम्न आकृति|वेन-आकृति|आकृति \d"
        r"|आकृतियों में प्रयुक्त|नीचे दर्शाया गया")

    def _has_figure(text):
        return bool(_FIGURE_REF.search(text)
                    or _FIGURE_REF_HI.search(text))

    def _option_run_lines(piece):
        """Wave 229: split one piece's MCQ option run into one
        display line per option, or None when the piece holds
        no such run. A run is at least THREE sequential labels
        — (a) (b) (c) [(d)], or the (A)-(D) capitals — in
        order. The Wave 63/64 branches below only ever split
        SPACED capitals (and spaced lowercase on Hindi-medium
        sheets), so a lowercase run on an English paper — 732
        stored questions — rendered as one continuous line,
        and a run stored without spaces around its labels
        ("(a)2(b)6(c)20(d)1", Suraj's screenshot) rendered
        fully glued. Display only, like everything in
        _paper_q_lines: every word of the stored text
        survives, in order; the only normalisation is one
        space after a label that was stored glued to its
        option text. A label counts only when the character
        before "(" is not a letter, so "f(a)", "P(A)" and
        "Assertion (A):" never start a run."""
        for labels in ("abcd", "ABCD"):
            starts = []
            pos = 0
            for ch in labels:
                label = "(" + ch + ")"
                found = -1
                while True:
                    i = piece.find(label, pos)
                    if i < 0:
                        break
                    if i == 0 or not piece[i - 1].isalpha():
                        found = i
                        break
                    pos = i + 1
                if found < 0:
                    break
                starts.append(found)
                pos = found + len(label)
            if len(starts) < 3:
                continue
            out = []
            stem = piece[:starts[0]].strip()
            if stem:
                out.append(stem)
            for k, s in enumerate(starts):
                e = (starts[k + 1] if k + 1 < len(starts)
                     else len(piece))
                opt = piece[s:e].strip()
                label = "(" + labels[k] + ")"
                rest = opt[len(label):]
                if rest and not rest[0].isspace():
                    opt = label + " " + rest
                out.append(opt)
            return out
        return None

    def _paper_q_lines(text, or_word="OR", lower_options=False):
        """Display lines for one stored question text: a list of
        (kind, text) with kind "or" for the centred OR divider
        between internal choices, "line" otherwise. Whitespace
        only — every word of the stored text survives, in order.
        Wave 64: Hindi-medium papers split on their printed
        divider "अथवा" (or_word) and their MCQ options may be
        printed (a)–(d) instead of (A)–(D) (lower_options)."""
        lines = []
        if or_word == "अथवा":
            # Hindi: "अथवा" is also an ordinary word inside some
            # questions (e.g. the MCQ option "8 अथवा −8" = "8 or
            # −8"), so it only counts as the internal-choice
            # divider when a labelled alternative follows —
            # (क)/(ख)/(A)/(B) or (iii) (…).
            parts = re.split(
                r"\s+अथवा\s+(?=\((?:क|ख|A|B)\)|\((?:iii)\))", text)
        else:
            parts = text.split(" " + or_word + " ")
        for i, part in enumerate(parts):
            if i:
                lines.append(("or", or_word))
            for chunk in re.split(
                    r"(?<=[.;:।])\s+(?=(?:Reason \(R\):|तर्क \(R\) :))",
                    part):
                for piece in re.split(
                        r"(?<=[.;:।])\s+"
                        r"(?=\((?:i|ii|iii|iv|a|b|क|ख)\))",
                        chunk):
                    # Wave 229: a 3+ label option run (either
                    # case, spaced or stored glued) splits
                    # first; the Wave 63/64 branches below keep
                    # their exact behaviour for the 2-label
                    # pieces they have always owned.
                    run = _option_run_lines(piece)
                    if run is not None:
                        lines.extend(("line", opt) for opt in run)
                    elif "(A)" in piece and " (B) " in piece:
                        lines.extend(
                            ("line", opt) for opt in re.split(
                                r"\s+(?=\([A-D]\)\s)", piece))
                    elif (lower_options and "(a)" in piece
                            and " (b) " in piece):
                        lines.extend(
                            ("line", opt) for opt in re.split(
                                r"\s+(?=\([a-d]\)\s)", piece))
                    else:
                        lines.append(("line", piece))
        return lines

    # Wave 64: Hindi-medium sheet chrome — the section names and
    # descriptive subtitles the Hindi papers themselves print.
    _HI_SECTION = {"A": "क", "B": "ख", "C": "ग", "D": "घ", "E": "ङ"}
    _HI_SUBTITLES = {
        "A": "बहुविकल्पीय प्रश्न तथा अभिकथन-तर्क प्रश्न "
             "(प्रत्येक 1 अंक)",
        "B": "अति लघु-उत्तरीय प्रश्न (प्रत्येक 2 अंक)",
        "C": "लघु-उत्तरीय प्रश्न (प्रत्येक 3 अंक)",
        "D": "दीर्घ-उत्तरीय प्रश्न (प्रत्येक 5 अंक)",
        "E": "प्रकरण अध्ययन आधारित प्रश्न (प्रत्येक 4 अंक)",
    }

    def _paper_sheet(paper):
        """View-model for the typed exam-paper sheet of one stored
        paper (Wave 63). See the block comment above for the
        honesty rules behind every derived number.

        Wave 66: other boards' layouts genuinely differ from the
        CBSE pattern this builder was written for, so a paper may
        carry optional overrides, all derived from its own printed
        header/structure (never invented): "section_titles"
        {section: full English title}, "section_titles_hindi"
        {section: Hindi subtitle}, "hindi_section_letters"
        {section: letter} (e.g. RBSE prints खण्ड अ/ब/स/द, not
        क/ख/ग/घ), "full_marks"/"full_count" {section: value}
        replacing the derived section totals, and "max_marks"/
        "max_questions" replacing the header totals (e.g. ISC,
        where Sections B and C are alternatives and must not be
        added together)."""
        hindi = paper.get("medium") == "hindi"
        hi_letters = paper.get("hindi_section_letters") or _HI_SECTION
        stored = paper["questions"]
        by_section = {}
        for q in stored:
            by_section.setdefault(q["section"], []).append(q)
        stored_numbers = {q["number"] for q in stored}
        sections = []
        full_marks = 0
        full_count = 0
        # Wave 179: sections beyond the CBSE A-E pattern
        # (stored by boards with more groups — CGBSE F,
        # WBBSE A-P) render after the standard ones, in
        # stored order; previously they were silently
        # dropped from the sheet.
        _section_order = [s for s in papers_data.PAPER_STRUCTURE
                          if s in by_section]
        _section_order += [s for s in by_section
                           if s not in _section_order]
        for section in _section_order:
            qs = by_section.get(section)
            if not qs:
                continue
            qs = sorted(qs, key=lambda q: q["number"])
            marks_set = {q["marks"] for q in qs}
            sec_count = len(qs)
            sec_marks = sum(q["marks"] for q in qs)
            # Omissions inside the section's number span (the
            # transcription notes name them; the gap in the
            # numbering is the in-data trace).
            for n in range(qs[0]["number"], qs[-1]["number"] + 1):
                if n not in stored_numbers:
                    near = min(qs, key=lambda q: abs(q["number"] - n))
                    sec_count += 1
                    sec_marks += near["marks"]
            # Trailing / leading omissions leave no gap in the
            # span; they show only as a deficit against the
            # standard pattern, and only where the section's
            # marks match that pattern exactly.
            std_count, std_marks = papers_data.PAPER_STRUCTURE.get(
                section, (0, 0))
            if marks_set == {std_marks} and sec_count < std_count:
                sec_marks += (std_count - sec_count) * std_marks
                sec_count = std_count
            # Wave 66: a paper's own printed totals win over the
            # derived ones (see the docstring above).
            if section in paper.get("full_count", {}):
                sec_count = paper["full_count"][section]
            if section in paper.get("full_marks", {}):
                sec_marks = paper["full_marks"][section]
            title = paper.get("section_titles", {}).get(
                section) or papers_data.section_title_for(section, qs)
            subtitle = ""
            if " — " in title:
                subtitle = title.split(" — ", 1)[1]
            elif title.startswith(f"Section {section} ("):
                subtitle = title[len(f"Section {section} "):]
            heading = f"SECTION {section}"
            if hindi:
                heading = f"खण्ड {hi_letters.get(section, section)}"
                if section in paper.get("section_titles_hindi", {}):
                    subtitle = paper["section_titles_hindi"][section]
                else:
                    std = papers_data.PAPER_STRUCTURE.get(
                        section, (0, 0))
                    if (sec_count, qs[0]["marks"]) == std \
                            and len(marks_set) == 1:
                        subtitle = _HI_SUBTITLES[section]
                    elif len(marks_set) == 1:
                        subtitle = (f"{sec_count} प्रश्न "
                                    f"(प्रत्येक {qs[0]['marks']} अंक)")
                    else:
                        subtitle = f"{sec_count} प्रश्न"
            sections.append({
                "section": section,
                "heading": heading,
                "subtitle": subtitle,
                "full_count": sec_count,
                "marks_each": (qs[0]["marks"]
                               if len(marks_set) == 1 else None),
                "questions": [{
                    "number": q["number"],
                    "marks": q["marks"],
                    "lines": _paper_q_lines(
                        q["text"],
                        or_word="अथवा" if hindi else "OR",
                        lower_options=hindi),
                    "has_figure": _has_figure(q["text"]),
                } for q in qs],
            })
            full_marks += sec_marks
            full_count += sec_count
        # Wave 66: header totals override (alternative sections
        # such as ISC's B/C must not be summed).
        if "max_marks" in paper:
            full_marks = paper["max_marks"]
        if "max_questions" in paper:
            full_count = paper["max_questions"]
        if hindi:
            # The same derived facts, in the paper's own language
            # (mirrors the printed Hindi सामान्य निर्देश).
            instructions = [
                f"इस प्रश्न-पत्र में {full_count} प्रश्न हैं। "
                "सभी प्रश्न अनिवार्य हैं।",
            ]
            for sec in sections:
                name = hi_letters.get(sec["section"],
                                      sec["section"])
                if sec["marks_each"] is not None:
                    instructions.append(
                        f"खण्ड {name} में {sec['full_count']} प्रश्न "
                        f"हैं, जिनमें प्रत्येक के "
                        f"{sec['marks_each']} अंक हैं।")
                else:
                    instructions.append(
                        f"खण्ड {name} में {sec['full_count']} प्रश्न "
                        "हैं।")
            if any(" अथवा " in q["text"] for q in stored):
                instructions.append(
                    "कुछ प्रश्नों में आंतरिक विकल्प दिया गया है।")
        else:
            instructions = [
                f"This question paper contains {full_count} questions. "
                "All questions are compulsory.",
            ]
            for sec in sections:
                if sec["marks_each"] is not None:
                    word = "mark" if sec["marks_each"] == 1 else "marks"
                    instructions.append(
                        f"Section {sec['section']} contains "
                        f"{sec['full_count']} questions of "
                        f"{sec['marks_each']} {word} each.")
                else:
                    instructions.append(
                        f"Section {sec['section']} contains "
                        f"{sec['full_count']} questions.")
            if any(" OR " in q["text"] for q in stored):
                instructions.append(
                    "Internal choices are provided in some questions.")
        subject = paper.get("subject_label") or "Mathematics"
        if not paper.get("subject_label"):
            m = re.search(r"Mathematics( \((?:Standard|Basic)\))?",
                          paper["set_label"])
            if m:
                subject = m.group(0)
        return {
            "set_label": paper["set_label"],
            "subject": subject,
            "class_num": paper["class_num"],
            "board": paper["board"],
            "year": paper["year"],
            "full_marks": full_marks,
            "full_count": full_count,
            "instructions": instructions,
            "instructions_title": ("सामान्य निर्देश :"
                                   if hindi else
                                   "General Instructions:"),
            "marks_label": ("अधिकतम अंक" if hindi
                            else "Maximum Marks"),
            "class_label": "कक्षा" if hindi else "Class",
            "sections": sections,
        }

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
        # Wave 63: the page IS the paper — the typed exam-paper
        # sheet (header, instructions, sections, every stored
        # question in full). Chapter tags moved off this page;
        # they live in the pattern analysis now.
        return render_template(
            "paper_view.html", paper=paper,
            sheet=_paper_sheet(paper))

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
        the browser's Print -> Save as PDF makes the PDF).

        Wave 63: ?paper=<id> prints a STORED previous paper in
        the same typed exam-paper layout as its in-app page, so
        printing gives the real paper — no external links."""
        if not _papers_signed_in():
            return redirect(url_for("index"))
        stored_id = request.args.get("paper", "")
        stored = (papers_data.get_paper(stored_id)
                  if stored_id else None)
        if stored is not None:
            return render_template(
                "papers_print.html", paper=None, stored=stored,
                sheet=_paper_sheet(stored))
        ref = session.get("practice_paper_ref") or {}
        paper = None
        if ref.get("class_num") in papers_data.CLASSES_WITH_PAPERS:
            paper = papers_data.generate_practice_paper(
                ref["class_num"], seed=ref.get("seed"))
        if not paper:
            return redirect(url_for("papers_generate"))
        return render_template("papers_print.html", paper=paper)

    # ------------------------------------------------- wave 88 full paper
    # Full Paper Mode (full_paper.py): attempt one whole stored
    # paper like an exam — every question in paper order, the
    # paper's full time (its own stored duration when the data
    # carries one, else the board-standard 3 hours, always
    # shown on the intro page before the timer starts), the
    # attempt page auto-submits at zero, and checking follows
    # full_paper.py's honesty contract: MCQs and short answers
    # the solver can settle are auto-checked and scored; long /
    # proof / case-study / assertion-reason questions are
    # self-check with the model answer shown, never scored and
    # never sent to the Mistake Notebook. The attempt state in
    # the session is only {paper_id, started, duration} — the
    # paper itself is re-read from papers_data by id, and the
    # typed answers ride in the submit POST, exactly like the
    # Board chapter test. Answers are NOT autosaved: leaving
    # mid-attempt loses them, which is why the attempt template
    # overrides the back bar with the Wave 60 always-confirm
    # pattern.
    @app.get("/papers/<paper_id>/attempt")
    def full_paper_intro(paper_id):
        if not _papers_signed_in():
            return redirect(url_for("index"))
        paper = papers_data.get_paper(paper_id)
        if paper is None:
            return redirect(url_for("papers_home"))
        duration = full_paper.duration_for(paper)
        attempt = session.get("full_paper_attempt") or {}
        return render_template(
            "full_paper_intro.html", paper=paper,
            question_count=len(paper["questions"]),
            total_marks=papers_data.paper_total_marks(paper),
            duration_seconds=duration,
            duration_label=full_paper.duration_label(duration),
            in_progress=attempt.get("paper_id") == paper_id)

    @app.post("/papers/<paper_id>/attempt/start")
    def full_paper_start(paper_id):
        if not _papers_signed_in():
            return redirect(url_for("index"))
        paper = papers_data.get_paper(paper_id)
        if paper is None:
            return redirect(url_for("papers_home"))
        override = None
        if app.config.get("TESTING"):
            # Tests inject a tiny duration to exercise the
            # timer; the real UI never sends this field.
            override = request.form.get("duration_seconds")
        duration = full_paper.duration_for(paper, override=override)
        session["full_paper_attempt"] = {
            "paper_id": paper_id,
            "started": int(time.time()),
            "duration": duration,
        }
        return render_template(
            "full_paper_attempt.html", paper=paper,
            view=full_paper.attempt_view(
                paper, _paper_q_lines, _has_figure),
            total_marks=papers_data.paper_total_marks(paper),
            duration_seconds=duration,
            remaining_seconds=duration)

    @app.post("/papers/<paper_id>/attempt/submit")
    def full_paper_submit(paper_id):
        if not _papers_signed_in():
            return redirect(url_for("index"))
        paper = papers_data.get_paper(paper_id)
        attempt = session.get("full_paper_attempt") or {}
        if paper is None or attempt.get("paper_id") != paper_id:
            return redirect(url_for("papers_home"))
        answers = [request.form.get(f"answer_{i}", "")
                   for i in range(len(paper["questions"]))]
        graded = full_paper.grade_attempt(paper, answers)
        rows, summary = graded["rows"], graded["summary"]
        _record_mistakes(
            [{"question": r["question"], "expected": r["expected"],
              "given": r["given"], "topic": r["chapter"],
              "correct": False}
             for r in rows if r["status"] == "wrong"],
            f"Class {paper['class_num']} · {paper['board']} "
            f"{paper['year']} full paper")
        checked = [r for r in rows if r["settled"]]
        copycheck = None
        if checked:
            labels = {}
            for q in paper["questions"]:
                labels[q["chapter"]] = papers_data.chapter_title(
                    paper["class_num"], q["chapter"])
            copycheck = _copycheck(
                [{"question": r["question"],
                  "expected": r["expected"], "given": r["given"],
                  "correct": r["status"] == "correct",
                  "topic": r["chapter"]} for r in checked],
                sum(1 for r in checked
                    if r["status"] == "correct"),
                len(checked), labels)
        try:
            time_taken = int(request.form.get("time_taken", ""))
        except (TypeError, ValueError):
            time_taken = max(0, int(time.time())
                             - int(attempt.get("started", 0)))
        session.pop("full_paper_attempt", None)
        return render_template(
            "full_paper_result.html", paper=paper, rows=rows,
            summary=summary, copycheck=copycheck,
            time_taken=time_taken)

    # ------------------------------------------------- wave 40 practice mode
    # Practice Mode (Wave 40): one fresh generated question at a
    # time from practice_gen.py (Wave 34 — Classes 6-10 x
    # arithmetic / algebra / geometry / mensuration /
    # probability; every answer exact by construction). The
    # current question's answer state rides in the session
    # (small: kind + params + answer text), the same trick the
    # papers generator uses with its seed reference. /practice
    # itself is the older quiz, so this lives at /practice-mode.
    # Account page like /papers: anonymous visitors go back to
    # the sign-in gate at /, and the JSON endpoints answer
    # 401 login-required like the chats endpoints.
    def _pm_fmt(value):
        value = Fraction(value)
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"

    def _pm_steps(item):
        """Worked-answer lines for a practice_gen item, in house
        style (plain lines; the caller adds the final answer
        line). Built from the generator's own params, so the
        working always matches the question that was asked."""
        p = item["params"]
        kind = item["kind"]
        if kind == "expression":
            return [f"Multiply first: {p['b']} × {p['c']} = "
                    f"{p['b'] * p['c']}",
                    f"{p['a']} + {p['b'] * p['c']} − {p['d']}"]
        if kind == "fraction_add":
            num = p["a"] * p["d"] + p["c"] * p["b"]
            den = p["b"] * p["d"]
            lines = [f"{p['a']}/{p['b']} + {p['c']}/{p['d']} "
                     f"= {num}/{den}"]
            if f"{num}/{den}" != item["answer"]:
                lines.append(f"{num}/{den} = {item['answer']}")
            return lines
        if kind == "percent":
            return [f"{p['p']}% means {p['p']}/100",
                    f"{p['p']}/100 × {p['n']}"]
        if kind == "simple_interest":
            return ["Simple interest = P × R × T / 100",
                    f"= {p['principal']} × {p['rate']} × "
                    f"{p['years']} / 100"]
        if kind == "linear_equation":
            rhs = p["c"] - p["b"]
            move = (f"{p['a']}x = {p['c']} − {p['b']} = {rhs}"
                    if p["b"] >= 0 else
                    f"{p['a']}x = {p['c']} + {abs(p['b'])} = {rhs}")
            return [move, f"x = {rhs} / {p['a']}"]
        if kind == "evaluate_linear":
            b = p["b"]
            tail = f"+ {b}" if b >= 0 else f"− {abs(b)}"
            return [f"Put x = {p['x']} in {p['a']}x {tail}",
                    f"{p['a']} × {p['x']} {tail}"]
        if kind == "expand_binomials":
            return [f"(x + {p['a']})(x + {p['b']}) = x² + "
                    f"({p['a']} + {p['b']})x + "
                    f"({p['a']})({p['b']})"]
        if kind == "ap_nth_term":
            return ["nth term = a + (n − 1)d",
                    f"= {p['a']} + ({p['n']} − 1) × {p['d']} "
                    f"= {p['a']} + "
                    f"{(p['n'] - 1) * p['d']}"]
        if kind == "quadratic_roots":
            s = p["r1"] + p["r2"]
            prod = p["r1"] * p["r2"]
            return [f"The two roots add to {s} and multiply "
                    f"to {prod}",
                    f"(x − ({p['r1']}))(x − ({p['r2']})) = 0"]
        if kind == "supplementary_angle":
            return ["Supplementary angles add to 180°",
                    f"Other angle = 180° − {p['a']}°"]
        if kind == "triangle_third_angle":
            return ["Angles of a triangle add to 180°",
                    f"Third angle = 180° − {p['a']}° − "
                    f"{p['b']}°"]
        if kind == "rectangle_area":
            return [f"Area = length × breadth = {p['length']} "
                    f"× {p['breadth']}"]
        if kind == "circle_circumference":
            return [f"Circumference = 2πr = 2 × 22/7 × {p['r']}"]
        if kind == "cuboid_volume":
            return [f"Volume = length × breadth × height = "
                    f"{p['length']} × {p['breadth']} × "
                    f"{p['height']}"]
        if kind == "cube_surface_area":
            return [f"Total surface area = 6 × side² = 6 × "
                    f"{p['side']} × {p['side']}"]
        if kind == "cylinder_volume":
            return [f"Volume = πr²h = 22/7 × {p['r']}² × "
                    f"{p['h']}"]
        if kind == "cone_volume":
            return [f"Volume = (1/3)πr²h = 1/3 × 22/7 × "
                    f"{p['r']}² × {p['h']}"]
        if kind == "bag_probability":
            total = p["red"] + p["blue"]
            return [f"Total balls = {p['red']} + {p['blue']} "
                    f"= {total}",
                    f"P(red) = {p['red']}/{total}"]
        if kind == "die_greater":
            fav = 6 - p["k"]
            nums = ", ".join(str(i) for i in range(p["k"] + 1, 7))
            return [f"Numbers greater than {p['k']}: {nums} "
                    f"— {fav} outcomes",
                    f"P = {fav}/6"]
        if kind == "coins_at_least_one_head":
            none = _pm_fmt(Fraction(1, 2 ** p["n"]))
            return [f"P(no head at all) = (1/2)^{p['n']} = {none}",
                    f"P(at least one head) = 1 − {none}"]
        # ---------------- Wave 54 kinds ----------------
        if kind == "integer_add_sub":
            if p["op"] == "add":
                return [f"({p['a']}) + ({p['b']})"]
            return [f"({p['a']}) − ({p['b']})"]
        if kind == "fraction_subtract":
            num = p["a"] * p["d"] - p["c"] * p["b"]
            den = p["b"] * p["d"]
            lines = [f"{p['a']}/{p['b']} − {p['c']}/{p['d']} "
                     f"= {num}/{den}"]
            if f"{num}/{den}" != item["answer"]:
                lines.append(f"{num}/{den} = {item['answer']}")
            return lines
        if kind == "fraction_of":
            return [f"{p['n']}/{p['d']} of {p['quantity']} "
                    f"= {p['n']} × {p['quantity']} ÷ {p['d']}"]
        if kind == "fraction_multiply":
            return [f"Numerators: {p['a']} × {p['c']} "
                    f"= {p['a'] * p['c']}",
                    f"Denominators: {p['b']} × {p['d']} "
                    f"= {p['b'] * p['d']}"]
        if kind == "fraction_divide":
            return [f"{p['a']}/{p['b']} ÷ {p['c']}/{p['d']} "
                    f"= {p['a']}/{p['b']} × {p['d']}/{p['c']}"]
        if kind == "mixed_fraction_add":
            top1 = p["w1"] * p["d1"] + p["n1"]
            top2 = p["w2"] * p["d2"] + p["n2"]
            return [f"{p['w1']} {p['n1']}/{p['d1']} "
                    f"= {top1}/{p['d1']} and "
                    f"{p['w2']} {p['n2']}/{p['d2']} "
                    f"= {top2}/{p['d2']}",
                    f"{top1}/{p['d1']} + {top2}/{p['d2']}"]
        if kind == "decimal_add":
            return ["Line up the decimal points",
                    f"{p['a']} + {p['b']}"]
        if kind == "decimal_multiply":
            ia = int(p["a"].replace(".", ""))
            ib = int(p["b"].replace(".", ""))
            return [f"{ia} × {ib} = {ia * ib}, then place "
                    f"2 decimal digits"]
        if kind == "percent_increase":
            inc = _pm_fmt(Fraction(p["price"] * p["p"], 100))
            return [f"Increase = {p['p']}% of {p['price']} "
                    f"= {inc}",
                    f"New price = {p['price']} + {inc}"]
        if kind == "discount_price":
            off = _pm_fmt(Fraction(p["price"] * p["p"], 100))
            return [f"Discount = {p['p']}% of ₹{p['price']} "
                    f"= ₹{off}",
                    f"Selling price = {p['price']} − {off}"]
        if kind == "find_whole_from_percent":
            return [f"Number = {p['part']} ÷ {p['p']} × 100"]
        if kind == "ratio_share":
            parts = p["a"] + p["b"]
            each = p["total"] // parts
            share = p["a"] if p["ask"] == "first" else p["b"]
            return [f"Total parts = {parts}, each part "
                    f"= ₹{each}",
                    f"{p['ask']} part = {share} × {each}"]
        if kind == "ratio_simplify":
            g = math.gcd(p["a"], p["b"])
            return [f"HCF of {p['a']} and {p['b']} is {g}",
                    f"Divide both numbers by {g}"]
        if kind == "unitary_method":
            return [f"Cost of 1 pen = ₹{p['total']} ÷ "
                    f"{p['n']} = ₹{p['unit']}",
                    f"Cost of {p['m']} pens = {p['unit']} × "
                    f"{p['m']}"]
        if kind == "average":
            return [f"Sum = {' + '.join(str(x) for x in p['nums'])} "
                    f"= {sum(p['nums'])}",
                    f"Average = {sum(p['nums'])} ÷ "
                    f"{len(p['nums'])}"]
        if kind == "hcf":
            x, y = max(p["a"], p["b"]), min(p["a"], p["b"])
            lines = []
            while y:
                lines.append(f"{x} = {x // y} × {y} + {x % y}")
                x, y = y, x % y
            return lines
        if kind == "lcm":
            g = math.gcd(p["a"], p["b"])
            return [f"LCM = {p['a']} × {p['b']} ÷ "
                    f"HCF({p['a']}, {p['b']}) "
                    f"= {p['a'] * p['b']} ÷ {g}"]
        if kind == "compound_interest":
            lines = ["Amount = P × (1 + R/100)^T"]
            amt = Fraction(p["principal"])
            for yr in range(1, p["years"] + 1):
                iy = Fraction(amt * p["rate"], 100)
                amt += iy
                lines.append(f"Year {yr}: interest "
                             f"= {_pm_fmt(iy)}, amount "
                             f"= {_pm_fmt(amt)}")
            lines.append(f"Interest = {_pm_fmt(amt)} − "
                         f"{p['principal']}")
            return lines
        if kind == "square_of":
            return [f"{p['n']}² = {p['n']} × {p['n']}"]
        if kind == "sqrt_perfect":
            return [f"{p['root']} × {p['root']} "
                    f"= {p['number']}"]
        if kind == "cube_of":
            return [f"{p['n']}³ = {p['n']} × {p['n']} × "
                    f"{p['n']}"]
        if kind == "exponent_value":
            chain = " × ".join([str(p["base"])] * p["exp"])
            return [f"{p['base']}^{p['exp']} = {chain}"]
        if kind == "profit_loss":
            if p["variant"] == "profit":
                return [f"Profit = SP − CP = {p['sp']} − "
                        f"{p['cp']}"]
            return [f"Loss = CP − SP = {p['cp']} − {p['sp']}"]
        if kind == "speed_distance_time":
            if p["variant"] == "speed":
                return [f"Speed = {p['distance']} ÷ "
                        f"{p['time']}"]
            if p["variant"] == "distance":
                return [f"Distance = {p['speed']} × "
                        f"{p['time']}"]
            return [f"Time = {p['distance']} ÷ {p['speed']}"]
        if kind == "evaluate_quadratic":
            return [f"Put x = {p['x']}: {p['a']} × "
                    f"({p['x']})² + {p['b']} × ({p['x']}) "
                    f"+ {p['c']}",
                    f"= {p['a'] * p['x'] * p['x']} + "
                    f"{p['b'] * p['x']} + {p['c']}"]
        if kind == "evaluate_two_vars":
            return [f"Put x = {p['x']}, y = {p['y']}: "
                    f"{p['a']} × {p['x']} + {p['b']} × "
                    f"{p['y']}",
                    f"= {p['a'] * p['x']} + "
                    f"{p['b'] * p['y']}"]
        if kind == "equation_both_sides":
            return [f"{p['a']}x − {p['c']}x = {p['d']} − "
                    f"({p['b']}) = {p['d'] - p['b']}",
                    f"{p['a'] - p['c']}x = {p['d'] - p['b']}"]
        if kind == "simultaneous":
            s = p["x"] + p["y"]
            d = p["x"] - p["y"]
            lines = [f"Adding the equations: 2x = {s} + "
                     f"{d} = {2 * p['x']}",
                     f"x = {p['x']}"]
            if p["ask"] == "y":
                lines.append(f"y = {s} − {p['x']}")
            return lines
        if kind == "factorise_quadratic":
            return [f"Two numbers with sum "
                    f"{p['a'] + p['b']} and product "
                    f"{p['a'] * p['b']}: {p['a']} and "
                    f"{p['b']}"]
        if kind == "identity_square":
            return [f"(x + b)² = x² + 2bx + b² with "
                    f"b = {p['a']}",
                    f"= x² + {2 * p['a']}x + "
                    f"{p['a'] * p['a']}"]
        if kind == "identity_diff_square":
            return [f"(x + a)(x − a) = x² − a²",
                    f"= x² − {p['a'] * p['a']}"]
        if kind == "identity_numeric":
            if p["variant"] == "square":
                k = p["n"] - 100
                if k > 0:
                    return [f"{p['n']}² = (100 + {k})² "
                            f"= 10000 + {200 * k} + "
                            f"{k * k}"]
                k = -k
                return [f"{p['n']}² = (100 − {k})² "
                        f"= 10000 − {200 * k} + {k * k}"]
            return [f"{p['m'] - p['k']} × {p['m'] + p['k']} "
                    f"= {p['m']}² − {p['k']}² "
                    f"= {p['m'] * p['m']} − "
                    f"{p['k'] * p['k']}"]
        if kind == "ap_sum":
            return [f"S{p['n']} = {p['n']}/2 × (2 × "
                    f"{p['a']} + {p['n'] - 1} × {p['d']})"]
        if kind == "gp_nth_term":
            return [f"nth term = {p['a']} × "
                    f"{p['r']}^{p['n'] - 1}"]
        if kind == "gp_sum":
            return [f"S{p['n']} = {p['a']} × "
                    f"({p['r']}^{p['n']} − 1) ÷ "
                    f"({p['r']} − 1)"]
        if kind == "polynomial_add_sub":
            if p["variant"] == "add":
                return [f"x terms: {p['a1']}x + {p['a2']}x",
                        f"Constants: {p['b1']} + "
                        f"({p['b2']})"]
            return [f"x terms: {p['a1']}x − {p['a2']}x",
                    f"Constants: {p['b1']} − ({p['b2']})"]
        if kind == "simplify_like_terms":
            return [f"({p['a']} + {p['b']} − {p['c']})x"]
        if kind == "index_laws":
            if p["variant"] == "product":
                return [f"{p['base']}^{p['m']} × "
                        f"{p['base']}^{p['n']} "
                        f"= {p['base']}^{p['m'] + p['n']}"]
            if p["variant"] == "quotient":
                return [f"{p['base']}^{p['m']} ÷ "
                        f"{p['base']}^{p['n']} "
                        f"= {p['base']}^{p['m'] - p['n']}"]
            return [f"({p['base']}^{p['m']})^{p['n']} "
                    f"= {p['base']}^{p['m'] * p['n']}"]
        if kind == "complementary_angle":
            return ["Complementary angles add to 90°",
                    f"Other angle = 90° − {p['a']}°"]
        if kind == "triangle_exterior_angle":
            if p["variant"] == "exterior":
                return ["Exterior angle = sum of the two "
                        "opposite interior angles",
                        f"= {p['p']}° + {p['q']}°"]
            return ["Exterior angle = sum of the two "
                    "opposite interior angles",
                    f"Other angle = {p['exterior']}° − "
                    f"{p['p']}°"]
        if kind == "isosceles_angle":
            if p["variant"] == "base":
                return [f"Each base angle = (180° − "
                        f"{p['vertex']}°) ÷ 2"]
            return [f"Vertex angle = 180° − 2 × "
                    f"{p['base']}°"]
        if kind == "quadrilateral_fourth_angle":
            rest = p["a"] + p["b"] + p["c"]
            return ["Angles of a quadrilateral add to 360°",
                    f"Fourth angle = 360° − {rest}°"]
        if kind == "parallelogram_angle":
            if p["variant"] == "opposite":
                return ["Opposite angles of a parallelogram "
                        "are equal"]
            return ["Adjacent angles add to 180°",
                    f"Adjacent angle = 180° − {p['a']}°"]
        if kind == "square_area":
            return [f"Area = side × side = {p['side']} × "
                    f"{p['side']}"]
        if kind == "square_perimeter":
            return [f"Perimeter = 4 × side = 4 × "
                    f"{p['side']}"]
        if kind == "rectangle_perimeter":
            return [f"Perimeter = 2 × ({p['length']} + "
                    f"{p['breadth']})"]
        if kind == "triangle_area":
            return [f"Area = 1/2 × {p['base']} × "
                    f"{p['height']}"]
        if kind == "triangle_perimeter":
            return [f"Perimeter = {p['a']} + {p['b']} + "
                    f"{p['c']}"]
        if kind == "rhombus_area":
            return [f"Area = 1/2 × {p['d1']} × {p['d2']}"]
        if kind == "trapezium_area":
            return [f"Area = 1/2 × ({p['a']} + {p['b']}) "
                    f"× {p['h']}"]
        if kind == "circle_area":
            return [f"Area = πr² = 22/7 × {p['r']}²"]
        if kind == "circle_radius_from_circumference":
            return [f"r = {p['circumference']} × 7 ÷ 44"]
        if kind == "polygon_interior_sum":
            return [f"Sum = ({p['n']} − 2) × 180°"]
        if kind == "regular_polygon_exterior":
            return [f"Exterior angle = 360° ÷ {p['n']}"]
        if kind == "parallel_lines_angle":
            if p["variant"] == "corresponding":
                return ["Corresponding angles are equal"]
            return ["Co-interior angles add to 180°",
                    f"Angle = 180° − {p['a']}°"]
        if kind == "pythagoras":
            if p["variant"] == "hypotenuse":
                return [f"h² = {p['p']}² + {p['q']}² "
                        f"= {p['h'] * p['h']}",
                        f"h = √{p['h'] * p['h']}"]
            given = p["given_leg"]
            other = p["q"] if given == p["p"] else p["p"]
            return [f"Other leg² = {p['h']}² − {given}² "
                    f"= {other * other}",
                    f"Other leg = √{other * other}"]
        if kind == "sector_area":
            return [f"Area = {p['theta']}/360 × 22/7 × "
                    f"{p['r']}²"]
        if kind == "coordinate_distance":
            if p["variant"] == "axis":
                return [f"Distance = |{p['x2']} − "
                        f"({p['x1']})|"]
            return [f"Distance = √({p['x']}² + "
                    f"{p['y']}²)"]
        if kind == "coordinate_midpoint":
            return [f"Midpoint = (({p['x1']} + "
                    f"{p['x2']})/2, ({p['y1']} + "
                    f"{p['y2']})/2)"]
        if kind == "cube_volume":
            return [f"Volume = side³ = {p['side']}³"]
        if kind == "cuboid_surface_area":
            return [f"TSA = 2 × ({p['length']} × "
                    f"{p['breadth']} + {p['breadth']} × "
                    f"{p['height']} + {p['height']} × "
                    f"{p['length']})"]
        if kind == "cuboid_lsa":
            return [f"LSA = 2 × {p['height']} × "
                    f"({p['length']} + {p['breadth']})"]
        if kind == "cylinder_csa":
            return [f"CSA = 2πrh = 2 × 22/7 × {p['r']} × "
                    f"{p['h']}"]
        if kind == "cylinder_tsa":
            return [f"TSA = 2πr(r + h) = 2 × 22/7 × "
                    f"{p['r']} × ({p['r']} + {p['h']})"]
        if kind == "sphere_volume":
            return [f"Volume = 4/3 × 22/7 × {p['r']}³"]
        if kind == "sphere_surface_area":
            return [f"Surface area = 4 × 22/7 × "
                    f"{p['r']}²"]
        if kind == "hemisphere_volume":
            return [f"Volume = 2/3 × 22/7 × {p['r']}³"]
        if kind == "hemisphere_tsa":
            return [f"TSA = 3 × 22/7 × {p['r']}²"]
        if kind == "cone_csa":
            return [f"Slant height l = √({p['r']}² + "
                    f"{p['h']}²) = {p['l']}",
                    f"CSA = πrl = 22/7 × {p['r']} × "
                    f"{p['l']}"]
        if kind == "fencing_cost":
            perim = 2 * (p["length"] + p["breadth"])
            return [f"Perimeter = {perim} m",
                    f"Cost = {perim} × ₹{p['rate']}"]
        if kind == "tiling_cost":
            area = p["length"] * p["breadth"]
            return [f"Area = {p['length']} × "
                    f"{p['breadth']} = {area} m²",
                    f"Cost = {area} × ₹{p['rate']}"]
        if kind == "litres_capacity":
            vol = (p["length"] * p["breadth"]
                   * p["height"])
            return [f"Volume = {vol} cm³",
                    f"Litres = {vol} ÷ 1000"]
        if kind == "bag_three_colours":
            total = p["red"] + p["blue"] + p["green"]
            return [f"Total balls = {total}",
                    f"P({p['ask']}) = {p[p['ask']]}/{total}"]
        if kind == "die_event":
            if p["variant"] == "even":
                listing, count = "2, 4, 6", 3
            elif p["variant"] == "odd":
                listing, count = "1, 3, 5", 3
            elif p["variant"] == "prime":
                listing, count = "2, 3, 5", 3
            else:
                nums = [x for x in range(1, 7)
                        if x % p["k"] == 0]
                listing = ", ".join(str(x) for x in nums)
                count = len(nums)
            return [f"Favourable outcomes: {listing} — "
                    f"{count} out of 6",
                    f"P = {count}/6"]
        if kind == "coins_exactly_heads":
            ways = math.comb(p["n"], p["k"])
            return [f"Total outcomes = {2 ** p['n']}, "
                    f"favourable = {ways}",
                    f"P = {ways}/{2 ** p['n']}"]
        if kind == "card_probability":
            return [f"Favourable cards "
                    f"= {p['favourable']} out of 52",
                    f"P = {p['favourable']}/52"]
        if kind == "two_dice_sum":
            s = p["s"]
            pairs = [(i, s - i) for i in range(1, 7)
                     if 1 <= s - i <= 6]
            listing = ", ".join(f"({i}, {j})"
                                for i, j in pairs)
            return [f"Outcomes: {listing} — "
                    f"{len(pairs)} out of 36",
                    f"P = {len(pairs)}/36"]
        if kind == "two_draw_probability":
            total = p["red"] + p["blue"]
            return [f"P(first red) = {p['red']}/{total}",
                    f"P(second red) = {p['red'] - 1}/"
                    f"{total - 1}",
                    f"P(both) = {p['red']}/{total} × "
                    f"{p['red'] - 1}/{total - 1}"]
        if kind == "complement_probability":
            return [f"P(not E) = 1 − {p['a']}/{p['b']}"]
        if kind == "word_letter_probability":
            word = p["word"]
            if p["variant"] == "vowel":
                count = sum(1 for ch in word
                            if ch in "AEIOU")
                return [f"Vowels in {word}: {count} of "
                        f"{len(word)} letters",
                        f"P = {count}/{len(word)}"]
            count = word.count(p["letter"])
            return [f"Letter {p['letter']} appears "
                    f"{count} time(s) in {word}",
                    f"P = {count}/{len(word)}"]
        return []

    def _pm_parse_number(text):
        """Parse a student's typed answer to an exact Fraction.

        Accepts integers, decimals ("0.75") and fractions
        ("3/4"); a leading "x =" or "Answer:" is forgiven.
        Returns None when the text is not a single number."""
        if not isinstance(text, str):
            return None
        t = text.strip().replace("−", "-").replace(",", "")
        t = re.sub(r"^(x\s*=|answer\s*:)\s*", "", t,
                   flags=re.IGNORECASE)
        if not t:
            return None
        try:
            return Fraction(t)
        except (ValueError, ZeroDivisionError):
            return None

    def _pm_poly_coeffs(text):
        """Parse an expanded quadratic in x into (x^2, x,
        constant) coefficients, or None (Wave 54 — mirrors
        test_mode._poly_coeffs for the Practice Mode checker)."""
        t = str(text).strip().lower().replace(" ", "")
        t = t.replace("²", "^2").replace("**", "^").replace(
            "−", "-")
        if "=" in t:
            t = t.split("=")[-1]
        if "x" not in t:
            return None
        coeffs = [Fraction(0), Fraction(0), Fraction(0)]
        for term in re.findall(r"[+-]?[^+-]+", t):
            if not term:
                continue
            sign = 1
            if term[0] == "+":
                term = term[1:]
            elif term[0] == "-":
                sign = -1
                term = term[1:]
            if not term:
                return None
            try:
                if term.endswith("x^2"):
                    num = term[:-3]
                    coeffs[0] += sign * (
                        Fraction(num) if num else Fraction(1))
                elif term.endswith("x"):
                    num = term[:-1]
                    coeffs[1] += sign * (
                        Fraction(num) if num else Fraction(1))
                else:
                    coeffs[2] += sign * Fraction(term)
            except (ValueError, ZeroDivisionError):
                return None
        return tuple(coeffs)

    def _pm_check(state, given):
        """Fraction-exact check of a typed answer against the
        generator's answer for the session's current item."""
        if state.get("answer_value") is not None:
            expected = Fraction(state["answer_value"])
            got = _pm_parse_number(given)
            return got is not None and got == expected
        if state.get("kind") == "quadratic_roots":
            p = state["params"]
            nums = re.findall(r"-?\d+(?:\.\d+)?(?:/\d+)?",
                              str(given).replace("−", "-"))
            got = set()
            for token in nums:
                try:
                    got.add(Fraction(token))
                except (ValueError, ZeroDivisionError):
                    pass
            return got == {Fraction(p["r1"]), Fraction(p["r2"])}
        # Wave 54 text-answer kinds — checked from params,
        # mirroring test_mode's checkers.
        kind = state.get("kind")
        p = state["params"]
        if kind == "ratio_simplify":
            g = math.gcd(p["a"], p["b"])
            m = re.search(r"(\d+)\s*[:/]\s*(\d+)", str(given))
            return bool(m) and (
                int(m.group(1)), int(m.group(2))) == (
                p["a"] // g, p["b"] // g)
        if kind == "factorise_quadratic":
            t = str(given).replace("−", "-")
            found = [int(num) if sign == "+" else -int(num)
                     for sign, num in
                     re.findall(r"x\s*([+-])\s*(\d+)", t)]
            return len(found) == 2 and sorted(found) == sorted(
                [p["a"], p["b"]])
        if kind in ("identity_square", "identity_diff_square",
                    "polynomial_add_sub"):
            if kind == "identity_square":
                a = p["a"]
                expected = (Fraction(1), Fraction(2 * a),
                            Fraction(a * a))
            elif kind == "identity_diff_square":
                a = p["a"]
                expected = (Fraction(1), Fraction(0),
                            Fraction(-a * a))
            else:
                s = 1 if p["variant"] == "add" else -1
                expected = (Fraction(0),
                            Fraction(p["a1"] + s * p["a2"]),
                            Fraction(p["b1"] + s * p["b2"]))
            return _pm_poly_coeffs(given) == expected
        if kind == "simplify_like_terms":
            total = p["a"] + p["b"] - p["c"]
            t = str(given).strip().replace(
                "−", "-").replace(" ", "")
            m = re.fullmatch(r"([+-]?\d+)x", t)
            if m:
                return int(m.group(1)) == total
            return (t in ("x", "+x") and total == 1) or (
                t == "-x" and total == -1)
        if kind == "coordinate_midpoint":
            expected = [Fraction(p["x1"] + p["x2"], 2),
                        Fraction(p["y1"] + p["y2"], 2)]
            found = []
            for token in re.findall(
                    r"[+-]?\d+(?:\.\d+)?(?:\s*/\s*\d+)?",
                    str(given).replace("−", "-")):
                try:
                    found.append(Fraction(
                        token.replace(" ", "")))
                except (ValueError, ZeroDivisionError):
                    continue
            return found == expected
        # expand_binomials: a text answer — compare with spaces
        # and ^2/² spelling normalised.
        def _norm(s):
            return (re.sub(r"\s+", "", str(s).lower())
                    .replace("**2", "²").replace("^2", "²"))
        return _norm(given) == _norm(state["answer"])

    @app.get("/practice-mode")
    def practice_mode():
        if not _papers_signed_in():
            return redirect(url_for("index"))
        return render_template(
            "practice_mode.html",
            classes=practice_gen.CLASSES,
            topics=practice_gen.TOPICS)

    @app.post("/practice-mode/question")
    def practice_mode_question():
        if not _papers_signed_in():
            return jsonify({"ok": False,
                            "error": "login-required"}), 401
        data = request.get_json(silent=True) or {}
        try:
            class_num = int(data.get("class_num"))
        except (TypeError, ValueError):
            class_num = -1
        topic = data.get("topic", "")
        if class_num not in practice_gen.CLASSES or \
                topic not in practice_gen.TOPICS:
            return jsonify({"ok": False,
                            "error": "bad-request"}), 400
        previous = (session.get("pm_item") or {}).get("question")
        previous_kind = (session.get("pm_item") or {}).get("kind")
        item = None
        for _ in range(6):
            item = practice_gen.generate_question(
                class_num, topic,
                seed=secrets.randbelow(1 << 30))
            # Wave 54: with the 100-template pool, also avoid
            # serving the same TEMPLATE twice in a row, not
            # just the same question text.
            if item["question"] != previous and \
                    item["kind"] != previous_kind:
                break
        session["pm_item"] = {
            "class_num": item["class_num"],
            "topic": item["topic"],
            "kind": item["kind"],
            "question": item["question"],
            "answer": item["answer"],
            "answer_value": (_pm_fmt(item["answer_value"])
                             if item["answer_value"] is not None
                             else None),
            "params": item["params"],
        }
        return jsonify({
            "ok": True,
            "question": item["question"],
            "class_num": item["class_num"],
            "topic": item["topic"],
            "kind": item["kind"],
        })

    @app.post("/practice-mode/check")
    def practice_mode_check():
        if not _papers_signed_in():
            return jsonify({"ok": False,
                            "error": "login-required"}), 401
        state = session.get("pm_item")
        if not state:
            return jsonify({"ok": False,
                            "error": "no-question"}), 400
        data = request.get_json(silent=True) or {}
        given = str(data.get("answer", ""))
        return jsonify({
            "ok": True,
            "correct": _pm_check(state, given),
            "given": given,
            "expected": state["answer"],
            "steps": _pm_steps(state),
        })

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

    # ------------------------------------------------ weak topics
    # Wave 87: "My Weak Topics" — a personal practice set built
    # from this session's own Mistake Notebook: topics ranked by
    # mistake count, fresh questions generated per topic, and only
    # questions the solver itself answers correctly are served
    # (weak_practice.build_weak_set).  Data never leaves the
    # student's own session.
    def _weak_topic_label(topic):
        strings = _t()
        return (strings.get(f"quiz_topic_{topic}")
                or TEST_TOPICS.get(topic) or topic)

    def _weak_class_num(mistakes):
        """Class for generation: the signed-in student's own
        class, else the class named most often in the notebook's
        source strings ("Class 9 · ..."), else 8.  Clamped to the
        practice_gen range 6-10."""
        cls = session.get("saathi_class")
        if isinstance(cls, int) and 6 <= cls <= 12:
            return min(10, cls)
        seen = {}
        for entry in mistakes:
            m = re.search(r"Class\s+(\d+)", entry.get("source") or "")
            if m:
                n = int(m.group(1))
                if n in practice_gen.CLASSES:
                    seen[n] = seen.get(n, 0) + 1
        if seen:
            return max(seen, key=seen.get)
        return 8

    @app.get("/weak-topics")
    def weak_topics():
        mistakes = session.get("mistakes", [])
        ranked = weak_practice.aggregate_weak_topics(mistakes)
        rows = [{"topic": r["topic"], "count": r["count"],
                 "label": _weak_topic_label(r["topic"]),
                 "has_generator":
                     weak_practice.topic_backend(r["topic"])
                     is not None}
                for r in ranked]
        return render_template(
            "weak_topics.html", ranked=rows,
            total_mistakes=len(mistakes),
            gen_failed=request.args.get("gen_failed") == "1")

    @app.post("/weak-topics/start")
    def weak_topics_start():
        mistakes = session.get("mistakes", [])
        if not mistakes:
            return redirect(url_for("weak_topics"))
        built = weak_practice.build_weak_set(
            mistakes, _weak_class_num(mistakes))
        if not built["items"]:
            return redirect(url_for("weak_topics", gen_failed=1))
        session["weak_practice"] = {
            "items": built["items"],
            "general": built["general"],
        }
        questions = [{"question": it["question"],
                      "topic_label": _weak_topic_label(it["topic"])}
                     for it in built["items"]]
        return render_template("weak_practice.html",
                               questions=questions)

    @app.post("/weak-topics/submit")
    def weak_topics_submit():
        saved = session.pop("weak_practice", None)
        if not saved:
            return redirect(url_for("weak_topics"))
        items = saved["items"]
        rows, flags = [], []
        for i, item in enumerate(items):
            given = request.form.get(f"answer_{i}", "")
            ok = weak_practice.check_weak_answer(item, given)
            flags.append(ok)
            rows.append({
                "question": item["question"],
                "expected": display_answer(item["answer"]),
                "given": given,
                "correct": ok,
                "topic": item["topic"],
            })
        _record_mistakes(rows, "weak practice")
        summary = weak_practice.summarise_results(items, flags)
        for row in summary["topics"]:
            row["label"] = _weak_topic_label(row["topic"])
        return render_template(
            "weak_result.html", rows=rows,
            score=summary["score"], total=summary["total"],
            topic_rows=summary["topics"],
            kind_rows=summary["kinds"])

    # Wave 14: warm the solver + DB before the first request.
    _warm_up(app)

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
