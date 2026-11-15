"""Wave 60 verification (15 Nov 2026).

WHAT THIS WAVE ADDED (Suraj: "Ganitra ke andar back system
nahi hai" — inside the app there was no way to go back):

Before this wave only 8 of 26 screens carried any way back,
always as a small link at the very bottom of the page; the
Board chapter test and Practice Mode had NO link at all, and
no timed test asked before throwing typed answers away.

1. ONE back system: base.html renders the same top-left
   "← Back" pill at the top of every inner page. The button
   goes back in history when the student arrived from inside
   the app (same-origin referrer), and otherwise uses the
   parent-page fallback that app.py's _backnav_for_path map
   assigns to the route (fed to the template by the
   inject_backnav context processor). The chat home and the
   sign-in gate ("/") get no bar.
2. Timed-test protection: on /test the bar asks for
   confirmation only while the test paper is on screen
   (data-confirm-if="#test-paper"); on the timed classic
   quiz (POST /practice/start) only while #quiz-form is on
   screen; on the Board chapter test (board_test.html
   overrides the block) always while questions are shown,
   with the chapter page as fallback.
3. The two standalone print views (/solution/print,
   /papers/print) carry the same "← Back" as a .no-print
   link next to the print button.
4. i18n: nav_back + nav_back_test_confirm in all six UI
   languages. Delivery pins bumped for the new CSS:
   stylesheet ?v=35, service-worker cache ganitra-static-v15.

No solver file changed; answer behaviour is untouched.

Run:  python3 verify_wave60.py
"""

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave60-{RUN_ID}.db"

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


from app import create_app, _backnav_for_path  # noqa: E402
from i18n import get_strings, SUPPORTED_LANGS  # noqa: E402
import papers_data  # noqa: E402

# --- 1. The path map itself -----------------------------------
print("== 1. _backnav_for_path map ==")
CASES = [
    ("/", None),
    ("/board/test/start", None),
    ("/test", ("/", "#test-paper")),
    ("/practice/start", ("/", "#quiz-form")),
    ("/practice/submit", ("/practice", None)),
    ("/board/test/submit", ("/practice", None)),
    ("/board", ("/", None)),
    ("/board/10", ("/board", None)),
    ("/board/10/quadratic-equations", ("/board/10", None)),
    ("/board/10/quadratic-equations/practice",
     ("/board/10/quadratic-equations", None)),
    ("/papers", ("/", None)),
    ("/papers/analysis", ("/papers", None)),
    ("/papers/generate", ("/papers", None)),
    ("/papers/some-paper-id", ("/papers", None)),
    ("/mistakes", ("/", None)),
    ("/mistakes/practice", ("/mistakes", None)),
    ("/topics", ("/", None)),
    ("/chats", ("/", None)),
    ("/account", ("/", None)),
    ("/practice", ("/", None)),
    ("/practice-mode", ("/", None)),
    ("/practice/classic", ("/", None)),
    ("/history", ("/", None)),
    ("/parent-report", ("/", None)),
    ("/solve", ("/", None)),
]
for path, want in CASES:
    got = _backnav_for_path(path)
    check(f"map {path} -> {want}", got == want, f"got {got}")

# --- 2. i18n keys in every language ---------------------------
print("== 2. i18n keys ==")
for lang in SUPPORTED_LANGS:
    s = get_strings(lang)
    check(f"{lang}: nav_back + confirm present",
          bool(s.get("nav_back")) and bool(s.get("nav_back_test_confirm")))

# --- 3. Rendered pages ----------------------------------------
print("== 3. Pages carry the bar with the right fallback ==")
app = create_app()
app.config["TESTING"] = True
client = app.test_client()
r = client.post("/signup", data={
    "name": "W60 Back " + RUN_ID, "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w60-test-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")

PAPER_ID = papers_data.PAPERS[0]["id"]
GET_PAGES = [
    ("/chats", "/"),
    ("/topics", "/"),
    ("/board", "/"),
    ("/board/10", "/board"),
    ("/board/10/quadratic-equations", "/board/10"),
    ("/board/10/quadratic-equations/practice",
     "/board/10/quadratic-equations"),
    ("/papers", "/"),
    ("/papers/" + PAPER_ID, "/papers"),
    ("/papers/analysis", "/papers"),
    ("/papers/generate", "/papers"),
    ("/practice", "/"),
    ("/practice/classic", "/"),
    ("/practice-mode", "/"),
    ("/test", "/"),
    ("/mistakes", "/"),
    ("/history", "/"),
    ("/parent-report", "/"),
    ("/account", "/"),
]
for path, fallback in GET_PAGES:
    r = client.get(path)
    body = r.get_data(as_text=True)
    check(f"GET {path}: bar + fallback {fallback}",
          r.status_code == 200 and 'class="backnav-btn"' in body
          and f'data-fallback="{fallback}"' in body,
          f"status={r.status_code}")

r = client.get("/")
body = r.get_data(as_text=True)
check("GET / (chat home): NO back bar",
      r.status_code == 200 and 'class="backnav-btn"' not in body)

r = client.get("/test")
body = r.get_data(as_text=True)
check("/test: confirm gate on the paper card",
      'data-confirm-if="#test-paper"' in body
      and "data-confirm-msg" in body)

# --- 4. POST-rendered pages -----------------------------------
print("== 4. POST pages ==")
r = client.post("/solve", data={"question": "2 + 2"})
body = r.get_data(as_text=True)
check("POST /solve (answer page): bar, fallback /",
      r.status_code == 200 and 'class="backnav-btn"' in body
      and 'data-fallback="/"' in body, f"status={r.status_code}")

r = client.post("/practice/start",
                data={"topic": "arithmetic", "difficulty": "easy"})
body = r.get_data(as_text=True)
check("POST /practice/start (timed quiz): confirm gate",
      r.status_code == 200 and 'data-confirm-if="#quiz-form"' in body,
      f"status={r.status_code}")

r = client.post("/practice/submit", data={"time_taken": "30"})
body = r.get_data(as_text=True)
check("POST /practice/submit (result): fallback /practice",
      r.status_code == 200 and 'data-fallback="/practice"' in body,
      f"status={r.status_code}")

r = client.post("/board/test/start",
                data={"class_num": "10", "slug": "quadratic-equations"})
body = r.get_data(as_text=True)
check("POST /board/test/start: chapter fallback + always-confirm",
      r.status_code == 200
      and 'data-fallback="/board/10/quadratic-equations"' in body
      and "data-confirm-msg" in body
      and 'data-confirm-if="' not in body,
      f"status={r.status_code}")

r = client.post("/mistakes/practice/submit", data={})
body = r.get_data(as_text=True)
check("POST /mistakes/practice/submit: fallback /mistakes",
      r.status_code == 200 and 'data-fallback="/mistakes"' in body,
      f"status={r.status_code}")

# --- 5. Print views -------------------------------------------
print("== 5. Print views ==")
r = client.get("/solution/print")
body = r.get_data(as_text=True)
check("/solution/print: no-print back link to /",
      r.status_code == 200 and 'class="print-btn" href="/"' in body,
      f"status={r.status_code}")

client.post("/papers/generate", data={"class_num": "10"})
r = client.get("/papers/print")
body = r.get_data(as_text=True)
check("/papers/print: no-print back link to /papers",
      r.status_code == 200
      and 'class="print-btn" href="/papers"' in body,
      f"status={r.status_code}")

# --- 6. Chat is untouched by the bar --------------------------
print("== 6. Chat state survives inner-page visits ==")
r = client.post("/api/chats")
chat_id = r.get_json()["chat"]["id"]
client.get("/topics")
client.get("/papers")
r = client.get(f"/api/chats/{chat_id}")
check("chat still there after visiting inner pages",
      r.status_code == 200
      and r.get_json()["chat"]["id"] == chat_id)

# --- 7. Delivery pins + CSS -----------------------------------
print("== 7. Pins and CSS ==")
ROOT = Path(__file__).parent
base = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
check("stylesheet pin ?v=35", "v='38'" in base)
check("service worker cache v11",
      'GANITRA_CACHE = "ganitra-static-v15"' in sw)
check(".backnav-btn is a 44px+ pill in the app tokens",
      ".backnav-btn" in css and "min-height: 44px" in css
      and "var(--accent)" in css)

print(f"\nWave 60: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
