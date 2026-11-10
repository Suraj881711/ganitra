"""Wave-7 verification: the homepage is a PURE CHAT SCREEN
(ChatGPT-style — slim top bar, message thread, composer fixed at
the bottom, nothing else), the topic list moved to /topics, the
chat auto-scrolls + shows a typing indicator that swaps to the
calm waking-up note on a slow answer, and the Board chapter
page's timed-test button label is visible again.

Run with the project venv:  python verify_wave7.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from i18n import STRINGS, SUPPORTED_LANGS  # noqa: E402
from markupsafe import escape as esc  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:44} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]
HI = STRINGS["hi"]
CSS = Path("static/style.css").read_text(encoding="utf-8")

NEW_KEYS = {"nav_topics", "menu_label", "chat_greeting_plain",
            "chat_empty_sub", "chat_thinking"}

# --- 1. i18n completeness -------------------------------------------------
for code in SUPPORTED_LANGS:
    missing = NEW_KEYS - set(STRINGS[code])
    check(f"wave7 keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
    empty = [k for k in NEW_KEYS if not STRINGS[code].get(k)]
    check(f"wave7 keys non-empty ({code})", not empty,
          f"empty={empty}")
en_keys = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n fully complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")
check("209+ keys per language", len(en_keys) >= 214,
      f"en keys={len(en_keys)}")

# --- 2. Homepage = pure chat screen -----------------------------------------
c = app.test_client()
r = c.get("/")
body = r.get_data(as_text=True)
check("GET / 200", r.status_code == 200, f"status={r.status_code}")
check("NO topics grid on homepage",
      esc(EN["topics_heading"]) not in body
      and "topic-grid" not in body and "topic-card" not in body)
check("NO how-it-works on homepage",
      esc(EN["how_heading"]) not in body and "how-grid" not in body)
check("NO NEW badges strip", "new-badge" not in body
      and "new-strip" not in body and "✨ NEW" not in body)
check("NO hero marketing", "hero-tag" not in body
      and 'class="hero rise"' not in body
      and esc(EN["hero_tag"]) not in body)
check("chat shell + scroll thread", 'class="chat-shell"' in body
      and 'id="chat-scroll"' in body and 'id="chat-log"' in body)
check("empty state greeting", 'id="chat-empty"' in body
      and esc(EN["chat_greeting_plain"]) in body
      and esc(EN["chat_welcome"]) in body)
check("chat body/main classes", 'class="chat-page"' in body
      and 'class="chat-main"' in body)
check("no footer on chat page", "<footer>" not in body)

# --- 3. Slim top bar + menu ---------------------------------------------------
check("chat header bar", 'class="chat-header"' in body
      and 'class="chat-brand"' in body)
check("menu dropdown present", 'class="nav-menu"' in body
      and 'class="nav-dropdown"' in body
      and esc(EN["menu_label"]) in body)
for href, key in (("/practice", "nav_practice"),
                  ("/board", "nav_board"),
                  ("/mistakes", "nav_mistakes"),
                  ("/history", "nav_history"),
                  ("/parent-report", "nav_parents"),
                  ("/topics", "nav_topics")):
    check(f"menu link {href}", f'href="{href}"' in body
          and esc(EN[key]) in body)
check("compact dhyaan pill in bar", 'id="dhyaan-pill"' in body
      and 'id="dhyaan-text"' in body)
check("language switch in bar", 'id="lang-select"' in body)

# --- 4. Composer fixed at the bottom -------------------------------------------
check("composer wrap + form", 'class="composer-wrap"' in body
      and 'id="chat-form"' in body and 'action="/solve"' in body
      and 'class="chat-bar"' in body)
check("composer textarea", 'id="q"' in body and 'name="question"' in body
      and esc(EN["enter_question"]) in body)
check("composer mic + photo + send", 'id="mic-btn"' in body
      and 'id="photo-input"' in body and 'class="send-btn"' in body
      and esc(EN["voice_btn"]) in body and esc(EN["photo_btn"]) in body
      and esc(EN["solve_btn"]) in body)
check("css composer fixed-bottom layout",
      "body.chat-page" in CSS and "100dvh" in CSS
      and ".composer-wrap" in CSS and "flex: none" in CSS)
check("css thread scrolls, page does not",
      ".chat-scroll" in CSS and "overflow-y: auto" in CSS)
check("css textarea >= 16px in composer",
      "body.chat-page .chat-bar textarea" in CSS
      and "font-size: 16px" in CSS)

# --- 5. Typing indicator + waking swap + auto-scroll ------------------------------
check("typing indicator element", 'id="typing-template"' in body
      and "typing-indicator" in body
      and esc(EN["chat_thinking"]) in body)
c_hi = app.test_client()
c_hi.get("/set-lang/hi")
hi_body = c_hi.get("/").get_data(as_text=True)
check("typing indicator text (hi)", esc(HI["chat_thinking"]) in hi_body)
check("personal greeting text (hi) present",
      esc(HI["chat_welcome"]) in hi_body)
check("waking note carried for swap", 'id="waking-note-text"' in body
      and esc(EN["chat_waking_note"]) in body
      and "6000" in body and "wakingText" in body)
check("auto-scroll code", "scrollLog" in body
      and "scroller.scrollTop = scroller.scrollHeight" in body
      and "requestAnimationFrame" in body)
check("empty state hides on send", "hideEmpty" in body
      and "chat-empty" in body)

# --- 6. Saathi: personalised empty state + compact card ---------------------------
c = app.test_client()
c.post("/saathi", data={"name": "Aarav", "class": "8",
                        "action": "save", "next": "/"})
r = c.get("/")
body_named = r.get_data(as_text=True)
check("named greeting in empty state",
      esc(EN["saathi_welcome_name"].format(name="Aarav")) in body_named
      and esc(EN["chat_empty_sub"]) in body_named)
check("saathi pill in chat bar", 'class="saathi-pill"' in body_named
      and "Aarav" in body_named)
c = app.test_client()
r = c.get("/")
check("first-visit saathi card (compact, in empty state)",
      'id="saathi-card"' in r.get_data(as_text=True)
      and 'id="chat-empty"' in r.get_data(as_text=True))

# --- 7. /topics page ----------------------------------------------------------------
r = c.get("/topics")
tbody = r.get_data(as_text=True)
check("GET /topics 200", r.status_code == 200,
      f"status={r.status_code}")
check("topics page lists the areas", "topic-grid" in tbody
      and esc(EN["topics_heading"]) in tbody
      and esc(EN["t_algebra"]) in tbody
      and esc(EN["t_calculus"]) in tbody
      and esc(EN["t_distributions"]) in tbody
      and tbody.count("topic-card") >= 17,
      f"cards={tbody.count('topic-card')}")
check("topics page keeps how-it-works", esc(EN["how_heading"]) in tbody)
check("topics page uses normal shell", "<footer>" in tbody
      and 'class="chat-page"' not in tbody)
c_hi2 = app.test_client()
c_hi2.get("/set-lang/hi")
check("topics page (hi)", esc(HI["topics_heading"]) in
      c_hi2.get("/topics").get_data(as_text=True))

# --- 8. Board timed-test button fix ---------------------------------------------------
r = c.get("/board/10/quadratic-equations")
bbody = r.get_data(as_text=True)
check("chapter page 200", r.status_code == 200,
      f"status={r.status_code}")
check("timed-test button has fixed class",
      'class="board-opt board-test-btn"' in bbody
      and esc(EN["board_test_btn"]) in bbody)
check("timed-test button no longer hero-solve",
      "hero-solve" not in bbody)
check("practice button unchanged", 'class="board-opt"' in bbody
      and esc(EN["board_practice_btn"]) in bbody)
check("css board-test-btn visible label",
      ".board-test-btn" in CSS and "background: var(--accent)" in CSS
      and "color: #fff" in CSS)

# --- 9. API contracts unchanged ---------------------------------------------------------
c = app.test_client()
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("api success contract", r.status_code == 200
      and sorted(data.keys()) == ["advice", "explanation", "ok", "result"]
      and data.get("ok") is True
      and (data.get("result") or {}).get("answer") == "x = 2, x = 3")
r = c.post("/api/solve", json={"question": "asdf qwer zxq"})
data = r.get_json() or {}
err = data.get("error") or {}
check("api error contract", data.get("ok") is False
      and data.get("unsolvable") is True
      and err.get("heading") == EN["error_heading"]
      and len(err.get("tips") or []) == 3
      and bool(err.get("retry_label")))
r = c.post("/api/solve", json={"question": ""})
data = r.get_json() or {}
check("api empty contract", data.get("ok") is False
      and data.get("message") == EN["flash_no_question"])
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
check("classic /solve unchanged", r.status_code == 200
      and "x = 2, x = 3" in r.get_data(as_text=True))

# --- 10. Other pages keep their shell ------------------------------------------------------
for path in ("/board", "/practice", "/history", "/parent-report"):
    b = app.test_client().get(path).get_data(as_text=True)
    check(f"normal shell kept ({path})", "<footer>" in b
          and 'class="chat-page"' not in b)

# --- 11. JS syntax (node --check) -----------------------------------------------------------
node = shutil.which("node")
cl = app.test_client()
html = cl.get("/").get_data(as_text=True)
scripts = [s for s in re.findall(r"<script>(.*?)</script>", html, re.S)
           if s.strip()]
if node:
    ok = True
    for i, s in enumerate(scripts):
        p = f"/tmp/w7-home-{i}.js"
        Path(p).write_text(s, encoding="utf-8")
        ok = ok and subprocess.run([node, "--check", p],
                                   capture_output=True).returncode == 0
    check("JS syntax (home)", ok, f"scripts={len(scripts)}")
else:
    check("JS syntax (home)", True, "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
