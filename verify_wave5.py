"""Wave-5 verification: chat homepage (no example chips), Board Mode
(Classes 6-12, NCERT chapters, chapter practice + timed chapter
tests), Mistake Notebook fed by quizzes and chapter tests, and the
print/PDF solution page. Also re-checks i18n completeness for the
wave-5 keys across all 6 languages.

The chat thread itself (bubbles appending live) is browser behaviour;
what is verified here is the server contract it relies on: the chat
markup on /, the /api/solve JSON (answer + steps + explanation), the
session-history recording, and the classic POST /solve fallback.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
# Wave 10 rerun note: account names are unique per DB, so
# sign-ups below use a per-run random suffix (RUN_ID) — a
# rerun can never collide with the previous run.
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave5.db"  # Wave 10: FORCE a scratch account DB (assignment, not setdefault — a stray env value must not point these checks at a shared/real DB)
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from board_data import (CHAPTERS, CLASS_NUMBERS, KNOWN_TOPICS,  # noqa: E402
                        get_chapter, get_chapters)
from i18n import (ADVICE, SPEECH_LANGS, STRINGS,  # noqa: E402
                  SUPPORTED_LANGS, advice_for)
from markupsafe import escape as _markupsafe_escape  # noqa: E402
from solver.router import solve_question  # noqa: E402


def esc(text):
    """How Jinja renders a string into HTML (apostrophes become
    &#39; etc.) — expected UI strings must be compared in this form."""
    return str(_markupsafe_escape(text))

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:30} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()

# --- 1. Board data sanity -------------------------------------------------
check("classes 6-12 present",
      tuple(CLASS_NUMBERS) == tuple(range(6, 13))
      and all(get_chapters(n) for n in CLASS_NUMBERS),
      f"counts={[len(get_chapters(n)) for n in CLASS_NUMBERS]}")
bad_topics = [(n, c["title"], c["topic"]) for n in CLASS_NUMBERS
              for c in get_chapters(n) if c["topic"] not in KNOWN_TOPICS]
check("every chapter topic mapped", not bad_topics, str(bad_topics))
dupes = [(n, s) for n in CLASS_NUMBERS
         for s in [c["slug"] for c in get_chapters(n)]
         if [c["slug"] for c in get_chapters(n)].count(s) > 1]
check("chapter slugs unique", not dupes, str(dupes))
check("class 10 quadratic chapter",
      get_chapter(10, "quadratic-equations")["title"]
      == "Quadratic Equations")
check("class 12 determinants chapter",
      get_chapter(12, "determinants")["topic"] == "linear_algebra")
check("class 6 chapters present",
      any(c["title"] == "Fractions" for c in get_chapters(6)))

# --- 2. i18n completeness (incl. wave-5 keys) ------------------------------
en_keys = set(STRINGS["en"])
w5_keys = {k for k in en_keys if k.startswith(
    ("board_", "mistakes_", "chat_", "nav_board", "nav_mistakes",
     "pdf_link", "print_"))}
check("wave-5 keys exist", len(w5_keys) >= 25, f"count={len(w5_keys)}")
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")

# --- 3. Chat homepage -------------------------------------------------------
client = app.test_client()
# Wave 10: / is login-gated — sign up a test student first so the
# homepage under test is his chat screen.
client.post("/signup", data={"name": "W5 Tester " + RUN_ID, "class": "8",
                             "board": "CBSE", "goal": "Doctor",
                             "hobby": "Cricket", "favourite": "Pizza",
                             "password": "w5test-pass"})
r = client.get("/")
body = r.get_data(as_text=True)
check("GET / (chat)", r.status_code == 200, f"status={r.status_code}")
check("NO example chips", 'class="chip"' not in body
      and 'class="chips"' not in body)
check("chat log + bar present", 'id="chat-log"' in body
      and 'class="chat-bar"' in body and 'id="chat-form"' in body)
check("chat form contract", 'action="/solve"' in body
      and 'name="question"' in body)
# Wave 10: a signed-in student's empty state greets him by name,
# so the plain chat_welcome string renders in the chat's welcome
# bubble (after the first question), not the empty state. The
# homepage contract here is the personalised greeting pair.
# Wave 11: the empty state is greeting ONLY — the chat_empty_sub
# "Type it, speak it..." line was removed by Suraj's design, so
# the welcome contract is now the named greeting + the sub-line's
# ABSENCE from the homepage.
check("welcome bubble",
      esc(STRINGS["en"]["saathi_welcome_name"].format(
          name="W5 Tester " + RUN_ID)) in body
      and esc(STRINGS["en"]["chat_empty_sub"]) not in body)
check("voice + photo in bar", 'id="mic-btn"' in body
      and 'id="photo-input"' in body)

# --- 4. /api/solve drives the chat + history --------------------------------
r = client.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
result = data.get("result") or {}
check("POST /api/solve", r.status_code == 200 and data.get("ok") is True,
      f"status={r.status_code}")
check("api answer", result.get("answer") == "x = 2, x = 3",
      str(result.get("answer")))
check("api steps non-empty", len(result.get("steps") or []) > 0,
      f"steps={len(result.get('steps') or [])}")
check("api explanation", bool(data.get("explanation")))
r = client.get("/history")
check("api solve in history", "x^2-5x+6=0"
      in r.get_data(as_text=True))

# --- 5. Classic fallback + PDF link + print page ----------------------------
r = client.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("classic POST /solve", r.status_code == 200
      and "x = 2, x = 3" in body)
check("answer page PDF link", "/solution/print" in body
      and STRINGS["en"]["pdf_link"] in body)
r = client.get("/solution/print")
body = r.get_data(as_text=True)
check("print page", r.status_code == 200 and "x^2-5x+6=0" in body
      and "x = 2, x = 3" in body and "Ganitra" in body
      and STRINGS["en"]["print_btn"] in body,
      f"status={r.status_code}")

# --- 6. Board pages ---------------------------------------------------------
r = client.get("/board")
body = r.get_data(as_text=True)
check("GET /board", r.status_code == 200 and "CBSE" in body
      and "MP Board" in body and "UP Board" in body
      and "Rajasthan Board" in body,
      f"status={r.status_code}")
client.get("/board/select/mp-board")
r = client.get("/board")
check("board choice saved", "MP Board" in r.get_data(as_text=True))
r = client.get("/board/10")
body = r.get_data(as_text=True)
check("/board/10 chapters", r.status_code == 200
      and "Quadratic Equations" in body
      and "Arithmetic Progressions" in body)
r = client.get("/board/5")
check("invalid class redirects", r.status_code == 302,
      f"status={r.status_code}")
r = client.get("/board/10/quadratic-equations")
body = r.get_data(as_text=True)
check("chapter page", r.status_code == 200
      and 'action="/board/test/start"' in body
      and "/practice" in body)
r = client.get("/board/10/quadratic-equations/practice")
body = r.get_data(as_text=True)
check("chapter practice", r.status_code == 200
      and body.count("practice-q") >= 5 and "Show answer" in body,
      f"sets={body.count('practice-q')}")

# --- 7. Chapter test: scoring + mistakes (existing topic) -------------------
c = app.test_client()
r = c.post("/board/test/start",
           data={"class_num": "10", "slug": "quadratic-equations"})
body = r.get_data(as_text=True)
check("chapter test starts", r.status_code == 200
      and body.count('name="answer_') == 5,
      f"inputs={body.count(chr(110) + 'ame=' + chr(34) + 'answer_')}")
with c.session_transaction() as sess:
    answers = [q["answer"] for q in sess["board_test"]["questions"]]
form = {f"answer_{i}": str(a) for i, a in enumerate(answers)}
r = c.post("/board/test/submit", data=form)
check("chapter test all-correct = 5/5",
      "5 / 5" in r.get_data(as_text=True))
r = c.get("/mistakes")
check("no mistakes after perfect test",
      STRINGS["en"]["mistakes_empty"] in r.get_data(as_text=True))

c.post("/board/test/start",
       data={"class_num": "10", "slug": "quadratic-equations"})
with c.session_transaction() as sess:
    wrong_questions = [q["question"]
                       for q in sess["board_test"]["questions"]]
form = {f"answer_{i}": "-99999" for i in range(5)}
r = c.post("/board/test/submit", data=form)
check("chapter test all-wrong = 0/5",
      "0 / 5" in r.get_data(as_text=True))
r = c.get("/mistakes")
body = r.get_data(as_text=True)
check("wrong answers in notebook",
      any(q in body for q in wrong_questions),
      f"sample={wrong_questions[0][:40]}")
r = c.get("/mistakes/practice")
body = r.get_data(as_text=True)
check("mistakes retry round", r.status_code == 200
      and any(q in body for q in wrong_questions))
r = c.post("/mistakes/clear")
r = c.get("/mistakes")
check("notebook clears",
      STRINGS["en"]["mistakes_empty"] in r.get_data(as_text=True))

# --- 8. Chapter test on a NEW generator topic (probability) -----------------
c = app.test_client()
c.post("/board/test/start",
       data={"class_num": "10", "slug": "probability"})
with c.session_transaction() as sess:
    answers = [q["answer"] for q in sess["board_test"]["questions"]]
check("probability test has 5 answers", len(answers) == 5)
form = {f"answer_{i}": str(a) for i, a in enumerate(answers)}
r = c.post("/board/test/submit", data=form)
check("probability test 5/5", "5 / 5" in r.get_data(as_text=True))

# --- 9. Timed quiz mistakes integration --------------------------------------
c = app.test_client()
c.post("/practice/start", data={"topic": "algebra",
                                "difficulty": "medium"})
with c.session_transaction() as sess:
    quiz_questions = [q["question"] for q in sess["quiz"]["questions"]]
form = {f"answer_{i}": "-99999" for i in range(5)}
c.post("/practice/submit", data=form)
r = c.get("/mistakes")
body = r.get_data(as_text=True)
check("quiz mistakes recorded",
      any(q in body for q in quiz_questions),
      f"sample={quiz_questions[0][:40]}")

# --- 10. Board + mistakes pages localised (Hindi) ----------------------------
c = app.test_client()
c.get("/set-lang/hi")
r = c.get("/board")
check("board page (hi)", STRINGS["hi"]["board_heading"]
      in r.get_data(as_text=True))
r = c.get("/mistakes")
check("mistakes page (hi)", STRINGS["hi"]["mistakes_heading"]
      in r.get_data(as_text=True))
# Wave 10: the chat welcome lives behind the login gate — sign up
# a test student in this Hindi session to see his chat homepage.
# The named empty state renders the PERSONALISED welcome line
# (chat_welcome is the no-name fallback, unused once signed in),
# so the Hindi contract here is the personalised greeting.
c.post("/signup", data={"name": "W5 Hindi Tester " + RUN_ID, "class": "8",
                        "board": "CBSE", "goal": "Doctor",
                        "hobby": "Cricket", "favourite": "Pizza",
                        "password": "w5test-pass"})
r = c.get("/")
check("chat welcome (hi)", esc(STRINGS["hi"][
    "saathi_welcome_name"].format(name="W5 Hindi Tester " + RUN_ID))
      in r.get_data(as_text=True))

# --- 11. Teacher's Advice + Listen button -----------------------------------
_required_advice = {
    "algebra:equation", "algebra:quadratic", "trigonometry",
    "calculus:derivative", "calculus:integral",
    "calculus:definite_integral", "statistics",
    "statistics:probability", "distributions", "geometry",
    "sequences", "generic",
}
for code in SUPPORTED_LANGS:
    keys = set(ADVICE.get(code, {}))
    check(f"advice complete ({code})",
          _required_advice <= keys and keys == set(ADVICE["en"]),
          f"missing={sorted(_required_advice - keys)}")
_quad = solve_question("x^2-5x+6=0")
check("quadratic advice selected",
      advice_for(_quad, "en") == ADVICE["en"]["algebra:quadratic"])
_lin = solve_question("solve 2x+3=7")
check("linear advice selected",
      advice_for(_lin, "en") == ADVICE["en"]["algebra:equation"])

c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("answer page advice card (en)",
      esc(STRINGS["en"]["advice_heading"]) in body
      and esc(ADVICE["en"]["algebra:quadratic"]) in body)
check("listen button (en)", 'id="listen-btn"' in body
      and esc(STRINGS["en"]["listen_btn"]) in body
      and "speechSynthesis" in body
      and f'"{SPEECH_LANGS["en"]}"' in body)
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
check("api advice field",
      (r.get_json() or {}).get("advice")
      == ADVICE["en"]["algebra:quadratic"])

c = app.test_client()
c.get("/set-lang/hi")
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("answer page advice card (hi)",
      esc(STRINGS["hi"]["advice_heading"]) in body
      and esc(ADVICE["hi"]["algebra:quadratic"]) in body)
check("listen button (hi)", esc(STRINGS["hi"]["listen_btn"]) in body
      and f'"{SPEECH_LANGS["hi"]}"' in body)

r = client.get("/board")
body = r.get_data(as_text=True)
check("advice of the day on /board",
      esc(STRINGS["en"]["advice_day_heading"]) in body
      and any(esc(STRINGS["en"][f"tip_day_{i}"]) in body
              for i in range(7)))

# --- 12. Suno: step-by-step speech queue ------------------------------------
import json  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402

c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
_m = re.search(r"var SPEAK = (\{.*?\});", body, re.S)
speak_data = {}
if _m:
    try:
        speak_data = json.loads(_m.group(1))
    except ValueError:
        speak_data = {}
_expected = solve_question("x^2-5x+6=0")
check("suno queue data embedded", bool(speak_data))
check("suno queue order + content",
      speak_data.get("question") == "x^2-5x+6=0"
      and speak_data.get("steps") == (_expected.get("steps") or [])
      and speak_data.get("answer") == "x = 2, x = 3"
      and speak_data.get("advice")
      == ADVICE["en"]["algebra:quadratic"],
      f"steps={len(speak_data.get('steps') or [])}")
check("suno stop hooks", "speechSynthesis.cancel" in body
      and "SpeechSynthesisUtterance" in body
      and "buildQueue" in body and "STOP_LABEL" in body
      and "Stop" in body)
_node = shutil.which("node")
if _node:
    _scripts = [s for s in re.findall(r"<script>(.*?)</script>", body,
                                      re.S) if s.strip()]
    _ok = True
    for _i, _s in enumerate(_scripts):
        _p = f"/tmp/w5-suno-{_i}.js"
        open(_p, "w").write(_s)
        _ok = _ok and subprocess.run(
            [_node, "--check", _p], capture_output=True).returncode == 0
    check("answer page JS syntax", _ok, f"scripts={len(_scripts)}")
else:
    check("answer page JS syntax", True, "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
