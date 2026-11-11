"""Wave-6 verification: Mera Saathi (optional personal name/class,
safe personalised greeting, friendly never-scolding encouragement)
and the Parent Report (session + this-device data, honest scope,
star rule, WhatsApp share hook).

Run with the project venv:  python verify_wave6.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
# Wave 10 rerun note: account names are unique per DB, so
# sign-ups below use a per-run random suffix (RUN_ID) — a
# rerun can never collide with the previous run.
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave6.db"  # Wave 10: FORCE a scratch account DB (assignment, not setdefault — a stray env value must not point these checks at a shared/real DB)
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from i18n import STRINGS, SUPPORTED_LANGS  # noqa: E402
from markupsafe import escape as _markupsafe_escape  # noqa: E402


def esc(text):
    return str(_markupsafe_escape(text))


fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:42} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]
HI = STRINGS["hi"]

NEW_KEYS = {
    "saathi_card_heading", "saathi_card_text", "saathi_name_label",
    "saathi_name_placeholder", "saathi_class_label",
    "saathi_class_any", "saathi_class_word", "saathi_save_btn",
    "saathi_skip_btn", "saathi_edit", "saathi_welcome_name",
    "saathi_wrong_name", "saathi_wrong", "error_encourage_name",
    "error_encourage", "nav_parents", "parent_heading",
    "parent_intro_name", "parent_intro", "parent_student_label",
    "parent_solved_label", "parent_today_heading",
    "parent_minutes_label", "parent_today_questions_label",
    "parent_record_loading", "parent_mistakes_heading",
    "parent_mistakes_count_label", "parent_topics_label",
    "parent_none", "parent_last_test_heading",
    "parent_last_test_label", "parent_last_test_none",
    "parent_stars_heading", "parent_stars_count",
    "parent_stars_rule", "parent_scope_note", "parent_share_btn",
}

# --- 1. i18n completeness ---------------------------------------------------
for code in SUPPORTED_LANGS:
    missing = NEW_KEYS - set(STRINGS[code])
    check(f"wave6 keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
    empty = [k for k in NEW_KEYS if not STRINGS[code].get(k)]
    check(f"wave6 keys non-empty ({code})", not empty,
          f"empty={empty}")
en_keys = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n fully complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")

# --- 2. First-visit card + skip path -----------------------------------------
# Wave 10 note: the sign-in page IS the first page now, and a
# signed-in student's name comes from his ACCOUNT — the old
# first-visit Saathi card no longer renders on the chat page at
# all (its section id was renamed in Wave 10 precisely so the
# sync script can't auto-submit it), so the anonymous homepage
# checks below moved to verify_wave10, which asserts the card
# form's ABSENCE for signed-in users. What remains verifiable
# here is the /saathi ENDPOINT contract itself (skip stores no
# name, save cleans + stores), exercised directly.
c = app.test_client()
r = c.post("/saathi", data={"action": "skip", "next": "/"},
           follow_redirects=True)
check("skip path returns (to the gate)", r.status_code == 200)
with c.session_transaction() as sess:
    check("skip stores no name", sess.get("saathi_skipped") is True
          and not sess.get("saathi_name"))
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
check("site fully usable after skip", r.status_code == 200
      and "x = 2, x = 3" in r.get_data(as_text=True))

# --- 3. Save path, personalised greeting, XSS safety --------------------------
# Wave 10: the personalised greeting now belongs to signed-in
# students (the account sets the Saathi session at sign-up), so
# this section signs up instead of posting /saathi. The save
# endpoint's own cleaning contract is asserted separately below.
c = app.test_client()
raw_name = "<img src=x onerror=alert(1)>Aarav " + RUN_ID
r = c.post("/signup", data={"name": raw_name, "class": "8",
                            "board": "CBSE", "goal": "Doctor",
                            "hobby": "Cricket", "favourite": "Pizza",
                            "password": "w6test-pass"},
           follow_redirects=True)
body = r.get_data(as_text=True)
with c.session_transaction() as sess:
    check("name cleaned + class stored",
          sess.get("saathi_name") == "Aarav " + RUN_ID
          and sess.get("saathi_class") == 8,
          f"session={sess.get('saathi_name')!r}/{sess.get('saathi_class')!r}")
check("personalised greeting on homepage",
      esc(EN["saathi_welcome_name"].format(name="Aarav " + RUN_ID)) in body)
check("raw HTML name NOT rendered", raw_name not in body
      and "<img src=x" not in body)
# Wave 10: the pill no longer offers Edit for account users (the
# name comes from the account) — it shows name + class only.
# Wave 11: the chat top bar drops the name–class pill ENTIRELY
# (Suraj's approved multi-chat header) — the cleaned name and
# class still live in the session/greeting (asserted above);
# this check now pins the pill's ABSENCE on the chat page.
check("header Saathi pill REMOVED (wave 11)",
      'class="saathi-pill"' not in body
      and "saathi=edit" not in body)

# /saathi save cleaning contract (unchanged endpoint behaviour).
c = app.test_client()
long_name = "A" * 40
c.post("/saathi", data={"name": long_name, "class": "99",
                        "action": "save", "next": "/"})
with c.session_transaction() as sess:
    check("name capped at 30 chars", sess.get("saathi_name") == "A" * 30)
    check("invalid class ignored", sess.get("saathi_class") is None)

# Hindi greeting follows the UI language.
# Wave 10: account names are unique — section 3 already signed
# "Aarav" up, so this Hindi client uses its own name (before
# Wave 10 the same name could be re-saved freely via /saathi).
c = app.test_client()
c.get("/set-lang/hi")
c.post("/signup", data={"name": "Aarav Hindi " + RUN_ID, "class": "8",
                        "board": "CBSE", "goal": "Doctor",
                        "hobby": "Cricket", "favourite": "Pizza",
                        "password": "w6test-pass"})
r = c.get("/")
check("Hindi personalised greeting",
      esc(HI["saathi_welcome_name"].format(name="Aarav Hindi " + RUN_ID))
      in r.get_data(as_text=True))

# --- 4. Encouragement: friendly errors + wrong quiz answers -------------------
c = app.test_client()
c.post("/saathi", data={"name": "Aarav", "class": "8",
                        "action": "save", "next": "/"})
r = c.post("/solve", data={"question": "asdf qwer zxq"})
body = r.get_data(as_text=True)
# Wave 18 amendment (Suraj, 10 Nov 2026): gibberish gets the
# friendly fallback reply instead of the error card, named
# session or not — so the encouragement line no longer renders
# here. The Saathi encouragement strings themselves are
# asserted intact in i18n (the error card remains the answer
# template's last resort).
check("named session gibberish -> friendly fallback",
      esc("didn't look like a maths question") in body
      and "error-card" not in body)
check("encouragement strings intact in i18n",
      "Aarav" in EN["error_encourage_name"].format(name="Aarav")
      and bool(EN["error_encourage"]))
r = c.post("/api/solve", json={"question": "asdf qwer zxq"})
data = r.get_json() or {}
check("api gibberish -> fallback reply (Wave 18)",
      data.get("ok") is True
      and (data.get("result") or {}).get("fallback_kind")
      == "gibberish")

c = app.test_client()
r = c.post("/solve", data={"question": "asdf qwer zxq"})
check("anonymous gibberish -> friendly fallback",
      esc("didn't look like a maths question")
      in r.get_data(as_text=True))

# Wrong timed-quiz answers -> the never-scolding line (named + anon).
def run_wrong_quiz(client):
    client.post("/practice/start", data={"topic": "algebra",
                                         "difficulty": "easy"})
    form = {f"answer_{i}": "-99999" for i in range(5)}
    return client.post("/practice/submit", data=form)


c = app.test_client()
c.post("/saathi", data={"name": "Aarav", "action": "save",
                        "next": "/"})
r = run_wrong_quiz(c)
check("named encouragement after wrong quiz",
      esc(EN["saathi_wrong_name"].format(name="Aarav"))
      in r.get_data(as_text=True))
c = app.test_client()
r = run_wrong_quiz(c)
check("anonymous encouragement after wrong quiz",
      esc(EN["saathi_wrong"]) in r.get_data(as_text=True))

# --- 5. Parent Report: empty state ---------------------------------------------
c = app.test_client()
r = c.get("/parent-report")
body = r.get_data(as_text=True)
check("parent report 200 + sections", r.status_code == 200
      and esc(EN["parent_heading"]) in body
      and esc(EN["parent_solved_label"]) in body
      and esc(EN["parent_today_heading"]) in body
      and esc(EN["parent_mistakes_heading"]) in body
      and esc(EN["parent_last_test_heading"]) in body
      and esc(EN["parent_stars_heading"]) in body)
check("parent report honest scope note",
      esc(EN["parent_scope_note"]) in body)
check("parent report empty values", 'data-history-count="0"' in body
      and 'data-mistakes-count="0"' in body
      and 'data-total-stars="0"' in body
      and esc(EN["parent_last_test_none"]) in body)
check("parent report star rule stated",
      esc(EN["parent_stars_rule"]) in body)
check("WhatsApp share hook", 'id="parent-whatsapp"' in body
      and "https://wa.me/?text=" in body
      and "encodeURIComponent" in body)
check("parent report Dhyaan JS hooks", "ganitra-dhyaan" in body
      and 'id="parent-minutes"' in body
      and 'id="parent-today-count"' in body)
check("parents link in nav + footer", body.count("/parent-report") >= 1
      and esc(EN["nav_parents"]) in body)

# --- 6. Parent Report: solved question + completed test -------------------------
c = app.test_client()
c.post("/saathi", data={"name": "Aarav", "class": "8",
                        "action": "save", "next": "/"})
c.post("/solve", data={"question": "x^2-5x+6=0"})
c.post("/board/test/start",
       data={"class_num": "10", "slug": "quadratic-equations"})
with c.session_transaction() as sess:
    answers = [q["answer"] for q in sess["board_test"]["questions"]]
c.post("/board/test/submit",
       data={f"answer_{i}": str(a) for i, a in enumerate(answers)})
r = c.get("/parent-report")
body = r.get_data(as_text=True)
check("report shows the student", "Aarav" in body
      and esc(EN["parent_intro_name"].format(name="Aarav")) in body)
check("report session count = 1", 'data-history-count="1"' in body)
check("report last test 5 / 5", 'id="parent-last-score"' in body
      and "5 / 5" in body)
check("report stars = 1 perfect test", 'data-total-stars="1"' in body
      and esc(EN["parent_stars_count"].format(stars=1)) in body)

# A second >=80% test adds another star (the stated rule).
c.post("/board/test/start",
       data={"class_num": "10", "slug": "quadratic-equations"})
with c.session_transaction() as sess:
    answers = [q["answer"] for q in sess["board_test"]["questions"]]
c.post("/board/test/submit",
       data={f"answer_{i}": str(a) for i, a in enumerate(answers)})
with c.session_transaction() as sess:
    check("test star count accumulates",
          sess.get("test_star_count") == 2,
          f"count={sess.get('test_star_count')}")
r = c.get("/parent-report")
check("report stars = 2 after two good tests",
      'data-total-stars="2"' in r.get_data(as_text=True))

# Wrong test -> mistakes + lost topics appear in the report.
c = app.test_client()
c.post("/board/test/start",
       data={"class_num": "10", "slug": "quadratic-equations"})
c.post("/board/test/submit",
       data={f"answer_{i}": "-99999" for i in range(5)})
r = c.get("/parent-report")
body = r.get_data(as_text=True)
check("report mistakes count = 5", 'data-mistakes-count="5"' in body)
check("report mistakes topics shown", "Quadratic Equations" in body)
check("report last test 0 / 5", "0 / 5" in body)

# --- 7. JS syntax (node --check) --------------------------------------------------
node = shutil.which("node")
for page, maker in (
        # Wave 10: the chat homepage is login-gated — the maker
        # signs up a test student so the scripts checked are the
        # chat page's (incl. the Saathi mirror hooks).
        ("home-saathi", lambda cl: (cl.post(
            "/signup", data={"name": "W6 JS Tester " + RUN_ID, "class": "8",
                             "board": "CBSE", "goal": "Doctor",
                             "hobby": "Cricket", "favourite": "Pizza",
                             "password": "w6test-pass"}),
            cl.get("/"))[1]),
        ("parent-report", lambda cl: cl.get("/parent-report"))):
    cl = app.test_client()
    html = maker(cl).get_data(as_text=True)
    scripts = [s for s in re.findall(r"<script>(.*?)</script>", html,
                                     re.S) if s.strip()]
    if node:
        ok = True
        for i, s in enumerate(scripts):
            p = f"/tmp/w6-{page}-{i}.js"
            Path(p).write_text(s, encoding="utf-8")
            ok = ok and subprocess.run(
                [node, "--check", p],
                capture_output=True).returncode == 0
        check(f"JS syntax ({page})", ok, f"scripts={len(scripts)}")
    else:
        check(f"JS syntax ({page})", True, "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
