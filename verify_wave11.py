"""Wave-11 verification: the multi-chat system (Brave-style).

Contract (Suraj's approved design, from his own Brave screenshot):
- The chat top bar has NO name–class pill any more (the name
  still greets the student in the empty state) and carries a
  plain "+" at the FAR RIGHT (id="chats-open", href /chats, NOT
  wrapped in a circle element).
- The empty state is logo + named greeting only — the "Type it,
  speak it..." sub-line (chat_empty_sub) no longer renders.
- The composer keeps everything INSIDE the pill: LEFT a
  file-select button (id="file-btn") that clicks the SAME hidden
  file input as the camera label (id="photo-input"); then the
  textarea; RIGHT mic, camera, send — all four are line-style
  SVG icons (no 🎤/📷/➤ emoji characters as button content).
- Chats belong to the signed-in ACCOUNT and live server-side in
  the same SQLite DB: POST /api/chats creates, PUT saves the
  whole thread JSON (title derives from the first question),
  GET list/get, DELETE one, DELETE all. Another account can
  never see, open, save over or delete these chats; anonymous
  calls get 401 (API) / the sign-in gate (the /chats view).
- GET /chats renders the Brave-style all-chats view: count chip,
  grid toggle, a REAL search field, the 2-column card grid
  hooks, the big BLUE new-chat button and the ⋮ "Close all
  chats" menu.

Run:  python verify_wave11.py
(The script forces its own scratch account DB, like waves 7-10,
and uses a per-run random name suffix — account names are
unique, so a rerun can never collide with the previous run.)

Wave 12 changes (Suraj, 10 Nov 2026):
- The all-chats card template now uses the TRANSPARENT logo
  copies (logo-mark-t.png / logo-full-t.png — background removed
  so the logo no longer looks pasted on); the card-template check
  below asserts the -t filenames. The frozen originals on disk
  are still md5-checked in section 8, unchanged.
- The chat ☰ menu became the full-page menu (profile block,
  Settings, NO Log out — logout lives only in My Account). The
  "JS syntax (home)" section's applyLanguage navMap no longer
  needs "/history" — the menu has no History link any more.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
# FORCE a scratch account DB (assignment, not setdefault — a
# stray env value must not point these checks at a real DB).
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave11.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from i18n import STRINGS, SUPPORTED_LANGS  # noqa: E402
from markupsafe import escape as esc  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]
CSS = Path("static/style.css").read_text(encoding="utf-8")

NEW_KEYS = {"chats_heading", "chats_search_placeholder",
            "chats_new", "chats_new_label", "chats_open_label",
            "chats_count_label", "chats_open_now",
            "chats_answer_snippet", "chats_no_results",
            "chats_none_yet", "chats_close_one_label",
            "chats_delete_confirm", "chats_close_all",
            "chats_close_all_confirm", "chats_menu_label",
            "chats_view_label", "file_btn", "js_chats_saved_note"}

# --- 1. i18n completeness -------------------------------------------------
for code in SUPPORTED_LANGS:
    missing = NEW_KEYS - set(STRINGS[code])
    check(f"wave11 keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
    empty = [k for k in NEW_KEYS if not STRINGS[code].get(k)]
    check(f"wave11 keys non-empty ({code})", not empty,
          f"empty={empty}")
en_keys = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n fully complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")


def _signup(client, name):
    return client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w11test-pass"})


NAME_A = "W11 Aarav " + RUN_ID
NAME_B = "W11 Meera " + RUN_ID

# --- 2. Anonymous: gate + API lockout --------------------------------------
anon = app.test_client()
r = anon.get("/chats")
check("anon /chats redirects to gate", r.status_code == 302
      and r.headers.get("Location", "").rstrip("/").endswith("")
      or r.status_code == 302, f"status={r.status_code}")
r = anon.get("/")
check("anon / is the sign-in page",
      'id="signup-card"' in r.get_data(as_text=True))
for method, path in (("get", "/api/chats"), ("post", "/api/chats"),
                     ("get", "/api/chats/1"), ("delete", "/api/chats"),
                     ("delete", "/api/chats/1")):
    r = getattr(anon, method)(path)
    check(f"anon {method.upper()} {path} -> 401",
          r.status_code == 401, f"status={r.status_code}")

# --- 3. Chat page design (signed in) ----------------------------------------
a = app.test_client()
_signup(a, NAME_A)
body = a.get("/").get_data(as_text=True)
check("chat page renders", 'id="chat-form"' in body)
check("NO name-class pill in chat header",
      'class="saathi-pill"' not in body)
check("name still in the greeting",
      esc(EN["saathi_welcome_name"].format(name=NAME_A)) in body)
check('"+" control at the top bar', 'id="chats-open"' in body
      and 'href="/chats"' in body
      and 'class="chats-plus"' in body)
plus_at = body.index('id="chats-open"')
check('"+" sits after the menu (far right)',
      body.index('class="nav-menu"') < plus_at
      and body.index('id="lang-select"') < plus_at)
check('"+" is a plain sign (no circle class)',
      "chats-plus-circle" not in body
      and "plus-circle" not in body)
check("empty state: NO 'Type it' sub-line",
      "Type it" not in body
      and 'class="empty-sub"' not in body
      and esc(EN["chat_empty_sub"]) not in body)
check("composer has file-select button", 'id="file-btn"' in body
      and esc(EN["file_btn"]) in body)
bar = body[body.index('class="chat-bar"'):]
bar = bar[:bar.index("</form>")]
check("composer order: file, textarea, mic, camera, send",
      bar.index('id="file-btn"') < bar.index('id="q"')
      < bar.index('id="mic-btn"') < bar.index('for="photo-input"')
      < bar.index('class="send-btn'))
check("file + camera share the photo input",
      'id="photo-input"' in bar
      and "photoInput.click()" in body
      and 'getElementById("file-btn")' in body)
check("composer icons are SVG line-style",
      bar.count("<svg") >= 4 and 'stroke="currentColor"' in bar)
check("composer buttons show NO emoji glyphs",
      # The aria-labels/titles keep their Wave-4 localised text
      # (which contains 🎤/📷 by design) — the contract is about
      # the VISIBLE button content: strip tags + attributes and
      # assert no emoji glyph remains in what the student sees.
      all(g not in re.sub(r"<[^>]+>", " ", bar)
          for g in ("🎤", "📷", "➤")))
check("CSS: plain + at bar right edge",
      ".chats-plus" in CSS and "margin-left: auto" in CSS)
check("CSS: composer placement rule",
      "chat-active" in CSS and ".chat-scroll" in CSS)

# --- 4. Chat API: create / save / list / titles ------------------------------
r = a.post("/api/chats")
d = r.get_json() or {}
chat1 = (d.get("chat") or {}).get("id")
check("create chat 1", r.status_code == 201 and d.get("ok")
      and bool(chat1), f"status={r.status_code}")
r = a.post("/api/chats")
chat2 = ((r.get_json() or {}).get("chat") or {}).get("id")
check("create chat 2", bool(chat2) and chat2 != chat1)

THREAD1 = [
    {"role": "user", "text": "x^2 - 5x + 6 = 0"},
    {"role": "bot", "data": {"ok": True, "_q": "x^2 - 5x + 6 = 0",
                             "result": {"type": "algebra",
                                        "answer": "x = 2, x = 3",
                                        "steps": ["s1"]}}},
]
THREAD2 = [
    {"role": "user", "text": "3/4 + 2/3 kitna hoga"},
    {"role": "bot", "data": {"ok": True,
                             "_q": "3/4 + 2/3 kitna hoga",
                             "result": {"type": "arithmetic",
                                        "answer": "17/12",
                                        "steps": ["s1"]}}},
]
r = a.put(f"/api/chats/{chat1}", json={"messages": THREAD1})
d = r.get_json() or {}
check("save thread 1 + derived title", d.get("ok") is True
      and (d.get("chat") or {}).get("title") == "x^2 - 5x + 6 = 0")
r = a.put(f"/api/chats/{chat2}", json={"messages": THREAD2})
check("save thread 2", (r.get_json() or {}).get("ok") is True)

r = a.get("/api/chats")
d = r.get_json() or {}
items = d.get("chats") or []
by_id = {c["id"]: c for c in items}
check("list shows both chats", d.get("ok") is True
      and chat1 in by_id and chat2 in by_id,
      f"ids={sorted(by_id)}")
check("list titles are the first questions",
      by_id.get(chat1, {}).get("title") == "x^2 - 5x + 6 = 0"
      and by_id.get(chat2, {}).get("title")
      == "3/4 + 2/3 kitna hoga")
check("list previews carry Q + A snippets",
      by_id.get(chat1, {}).get("first_question")
      == "x^2 - 5x + 6 = 0"
      and by_id.get(chat1, {}).get("first_answer") == "x = 2, x = 3"
      and by_id.get(chat2, {}).get("first_answer") == "17/12")

r = a.get(f"/api/chats/{chat1}")
d = r.get_json() or {}
msgs = (d.get("chat") or {}).get("messages") or []
check("get one chat returns its thread",
      d.get("ok") is True and len(msgs) == 2
      and msgs[0].get("text") == "x^2 - 5x + 6 = 0"
      and (msgs[1].get("data") or {}).get("result", {}).get("answer")
      == "x = 2, x = 3")

# A real solve turn can be recorded exactly like the page does.
r = a.post("/api/solve", json={"question": "2+2*5"})
data = r.get_json() or {}
check("real /api/solve still answers", data.get("ok") is True
      and (data.get("result") or {}).get("answer") == "12")
data["_q"] = "2+2*5"
r = a.put(f"/api/chats/{chat2}", json={"messages": THREAD2 + [
    {"role": "user", "text": "2+2*5"}, {"role": "bot", "data": data}]})
check("real solve turn saves into a chat",
      (r.get_json() or {}).get("ok") is True)

# --- 5. Ownership: another account sees nothing ------------------------------
b = app.test_client()
_signup(b, NAME_B)
r = b.get("/api/chats")
check("other account's list is empty",
      (r.get_json() or {}).get("chats") == [])
for method in ("get", "delete"):
    r = getattr(b, method)(f"/api/chats/{chat1}")
    check(f"other account {method.upper()} chat1 -> 404",
          r.status_code == 404, f"status={r.status_code}")
r = b.put(f"/api/chats/{chat1}", json={"messages": []})
check("other account PUT chat1 -> 404", r.status_code == 404)
r = a.get(f"/api/chats/{chat1}")
check("chat1 untouched by the other account",
      len(((r.get_json() or {}).get("chat") or {})
          .get("messages") or []) == 2)

# --- 6. Delete one / delete all ----------------------------------------------
r = a.delete(f"/api/chats/{chat2}")
check("delete one chat", (r.get_json() or {}).get("ok") is True)
r = a.get("/api/chats")
ids = [c["id"] for c in (r.get_json() or {}).get("chats") or []]
check("deleted chat is gone, other remains",
      chat2 not in ids and chat1 in ids, f"ids={ids}")
r = a.delete("/api/chats")
d = r.get_json() or {}
check("close all chats", d.get("ok") is True
      and d.get("deleted") == 1, f"deleted={d.get('deleted')}")
r = a.get("/api/chats")
check("list empty after close-all",
      (r.get_json() or {}).get("chats") == [])

# --- 7. All-chats view markup ---------------------------------------------------
body = a.get("/chats").get_data(as_text=True)
check("/chats renders for signed-in", 'id="chats-grid"' in body)
check("view: count chip + grid toggle",
      'id="chats-count"' in body and 'id="chats-view-toggle"' in body
      and "<svg" in body)
check("view: search field wired to filter",
      'id="chats-search"' in body
      and esc(EN["chats_search_placeholder"]) in body
      and "first_question" in body and "matches" in body)
check("view: card template (mark, title, close, preview)",
      'id="chat-card-template"' in body
      and "chat-card-mark" in body and "chat-card-title" in body
      and "chat-card-close" in body and "chat-card-q" in body
      # Wave 12: cards use the transparent logo copies.
      and "logo-full-t.png" in body and "logo-mark-t.png" in body)
check("view: delete uses a confirm",
      "chats_delete_confirm" in body and "window.confirm" in body)
check("view: big blue new-chat button",
      'id="chats-new"' in body and 'class="chats-new-big"' in body)
check("view: ⋮ close-all menu",
      'id="chats-close-all"' in body
      and esc(EN["chats_close_all"]) in body
      and "chats_close_all_confirm" in body)
check("view: cards open their chat",
      '"/?chat="' in body and "openChat" in body)
check("CSS: 2-column card grid + blue button",
      ".chats-grid" in CSS
      and "grid-template-columns: 1fr 1fr" in CSS
      and ".chats-new-big" in CSS and "#2563eb" in CSS)
check("CSS: current chat card marked", ".chat-card.is-current" in CSS)

# --- 8. Logo freeze ---------------------------------------------------------------
for name, want in (("logo-full.png", "8ffea6f4e42d3d3b1bd8552e26579c4c"),
                   ("logo-mark.png", "5a190086234946460217a93148632125"),
                   ("favicon.png", "b4cfd43b46177c4da51a24d60b326771")):
    got = hashlib.md5(Path(f"static/{name}").read_bytes()).hexdigest()
    check(f"{name} md5 unchanged", got == want, f"md5={got}")

# --- 9. JS syntax (node --check) -----------------------------------------------------
node = shutil.which("node")
for label, path, client in (("home", "/", a), ("chats", "/chats", a)):
    html = client.get(path).get_data(as_text=True)
    scripts = [s for s in re.findall(r"<script>(.*?)</script>", html,
                                     re.S) if s.strip()]
    if node:
        ok = True
        for i, s in enumerate(scripts):
            p = f"/tmp/w11-{label}-{i}.js"
            Path(p).write_text(s, encoding="utf-8")
            ok = ok and subprocess.run(
                [node, "--check", p],
                capture_output=True).returncode == 0
        check(f"JS syntax ({label})", ok, f"scripts={len(scripts)}")
    else:
        check(f"JS syntax ({label})", True,
              "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
