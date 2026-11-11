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
# Wave 10 rerun note: account names are unique per DB, so
# sign-ups below use a per-run random suffix (RUN_ID) — a
# rerun can never collide with the previous run.
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave7.db"  # Wave 10: FORCE a scratch account DB (assignment, not setdefault — a stray env value must not point these checks at a shared/real DB)
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

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


def _signup(client, name):
    """Wave 10: the chat homepage sits behind the sign-in gate, so
    homepage checks sign up a test student first (unique names —
    accounts persist in the dev DB across runs)."""
    return client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w7test-pass"})

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
_signup(c, "W7 Main Tester " + RUN_ID)
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
      # Wave 10: the main test client is signed in, so the empty
      # state greets him BY NAME (account name) — the plain
      # greeting for name-less visitors is asserted in wave 10's
      # anonymous checks; here the personalised greeting is the
      # contract for a signed-in homepage.
      # Wave 11: the empty state is logo + greeting ONLY — the
      # chat_empty_sub "Type it, speak it..." line no longer
      # renders on the chat page (Suraj's design), so assert its
      # absence instead of its presence.
      and esc(EN["saathi_welcome_name"].format(name="W7 Main Tester " + RUN_ID)) in body
      and esc(EN["chat_empty_sub"]) not in body)
check("chat body/main classes", 'class="chat-page"' in body
      and 'class="chat-main"' in body)
check("no footer on chat page", "<footer>" not in body)

# --- 3. Slim top bar + menu ---------------------------------------------------
check("chat header bar", 'class="chat-header"' in body
      and 'class="chat-brand"' in body)
check("menu dropdown present", 'class="nav-menu"' in body
      # Wave 12: the menu nav now carries BOTH classes —
      # "nav-dropdown menu-panel" (full-page overlay panel).
      and 'class="nav-dropdown menu-panel"' in body
      and esc(EN["menu_label"]) in body)
for href, key in (("/practice", "nav_practice"),
                  ("/board", "nav_board"),
                  ("/mistakes", "nav_mistakes"),
                  # Wave 12 (Suraj, 10 Nov 2026): the History link
                  # is DROPPED from the chat ☰ menu — the approved
                  # full-page menu has no History item. The key and
                  # the /history page itself still exist.
                  ("/parent-report", "nav_parents"),
                  ("/topics", "nav_topics")):
    check(f"menu link {href}", f'href="{href}"' in body
          and esc(EN[key]) in body)
_dd = body[body.index('class="nav-dropdown menu-panel"'):]
_dd = _dd[:_dd.index("</nav>")]
check("menu has NO history link (wave 12)",
      'href="/history"' not in _dd)
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
      # Wave 11: the send button's class list is now
      # "send-btn icon-btn" (SVG icon styling) — assert the class
      # token, not the exact attribute value.
      and 'id="photo-input"' in body and 'class="send-btn ' in body
      and esc(EN["voice_btn"]) in body and esc(EN["photo_btn"]) in body
      and esc(EN["solve_btn"]) in body)
# Wave 11: the composer also gains the 📎 file-select button
# (LEFT, inside the pill, driving the same photo input), all
# four controls are line-style SVG icons, and the top bar gains
# the plain "+" that opens the all-chats view.
check("composer file-select + svg icons (wave 11)",
      'id="file-btn"' in body and body.count("<svg") >= 4)
check("chats '+' in top bar (wave 11)", 'id="chats-open"' in body
      and 'href="/chats"' in body)
# Wave 12 (Suraj, 10 Nov 2026): Log out moved OUT of the ☰ menu —
# it lives ONLY inside My Account now ("log out ka option profile
# ke andar karana hai"). Assert absence here, presence there.
check("menu has NO logout (wave 12)", 'href="/logout"' not in body)
_acct_body = c.get("/account").get_data(as_text=True)
check("logout lives on /account (wave 12)",
      'href="/logout"' in _acct_body
      and esc(EN["nav_logout"]) in _acct_body)
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
# Wave 10: sign up in the Hindi session so / renders the chat
# homepage (login gate) rather than the sign-in page.
_signup(c_hi, "W7 Hindi Tester " + RUN_ID)
hi_body = c_hi.get("/").get_data(as_text=True)
check("typing indicator text (hi)", esc(HI["chat_thinking"]) in hi_body)
check("personal greeting text (hi) present",
      esc(HI["saathi_welcome_name"].format(name="W7 Hindi Tester " + RUN_ID)) in hi_body)
check("waking note carried for swap", 'id="waking-note-text"' in body
      and esc(EN["chat_waking_note"]) in body
      and "6000" in body and "wakingText" in body)
check("auto-scroll code", "scrollLog" in body
      and "scroller.scrollTop = scroller.scrollHeight" in body
      and "requestAnimationFrame" in body)
check("empty state hides on send", "hideEmpty" in body
      and "chat-empty" in body)

# --- 6. Saathi: personalised empty state (account-driven since Wave 10) ------
# Wave 10: a signed-in student's greeting + pill come from his
# ACCOUNT (sign-up sets the Saathi session); the old first-visit
# card no longer renders for anyone — its absence for signed-in
# users is asserted here and in verify_wave10.
c = app.test_client()
_signup(c, "Aarav " + RUN_ID)
r = c.get("/")
body_named = r.get_data(as_text=True)
check("named greeting in empty state",
      esc(EN["saathi_welcome_name"].format(name="Aarav " + RUN_ID)) in body_named
      # Wave 11: the "Type it, speak it..." sub-line is gone
      # from the empty state (logo + greeting only).
      and esc(EN["chat_empty_sub"]) not in body_named)
# Wave 11: the chat top bar no longer carries the name–class
# pill (Suraj's approved multi-chat header) — the name lives in
# the greeting only. Pins the pill's ABSENCE on the chat page.
check("saathi pill REMOVED from chat bar (wave 11)",
      'class="saathi-pill"' not in body_named)
check("NO first-visit saathi card for account users",
      'id="saathi-form"' not in body_named
      and 'id="chat-empty"' in body_named)

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
      # Wave 9: the success contract gained language_switched +
      # language (auto-language); a neutral question adds nothing
      # else, so this exact key set is the Wave-9 contract.
      # Wave 12: the success contract gains "methods" (alternate
      # methods) + "teach" (Teach-me lines) — additive only.
      and sorted(data.keys()) == ["advice", "explanation", "language",
                                  "language_switched", "methods",
                                  "ok", "result", "teach"]
      and data.get("ok") is True
      and (data.get("result") or {}).get("answer") == "x = 2, x = 3")
r = c.post("/api/solve", json={"question": "asdf qwer zxq"})
data = r.get_json() or {}
err = data.get("error") or {}
# Wave 18 amendment (Suraj, 10 Nov 2026: "har ek question ka
# answer milna chahiye"): the unsolvable error contract is
# replaced by the fallback contract — every question returns
# an answer; gibberish returns a flagged friendly fallback.
check("api error contract (Wave 18 fallback contract)",
      data.get("ok") is True
      and (data.get("result") or {}).get("fallback_kind")
      == "gibberish"
      and "error" not in data and "unsolvable" not in data)
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
# Wave 10: the JS under test is the chat homepage's — sign up so
# the gate lets this client through to it.
_signup(cl, "W7 JS Tester " + RUN_ID)
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
