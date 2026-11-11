"""Wave-15 verification: MENU POLISH (design unchanged).

Contract: the Wave-12 full-page menu keeps Suraj's approved
design, item set and order — Wave 15 adds only MOTION + FEEL:
the overlay fades/slides in (CSS keyframes on the [open]
panel), tappable rows get smooth transitions + subtle :active
press feedback, stats numbers use tabular figures, and a
prefers-reduced-motion block disables the animation. Log out
stays OUT of the menu and INSIDE My Account (/account) only.

Checks:
1. Pages render for a logged-in user: /, /account, /chats
   all 200.
2. The menu (nav-dropdown segment of /) contains every
   expected item, in the approved order: Your chats, Board
   Mode, Previous Papers (added by Wave 16, Suraj 10 Nov 2026),
   Practice Test, Topics, Mistake Notebook, Copy Style,
   Parent Report, Language, Settings (+ the gold keep-line).
3. NO logout anywhere in the menu segment; /account DOES
   contain the logout link (exactly the Wave-12 rule).
4. style.css carries the Wave-15 polish: the menu keyframes,
   the [open] animation rules, transition rules, :active
   press feedback, tabular stats numbers, reduced-motion
   guard — and still carries the Wave-12 structural rules.

Run:  python verify_wave15.py
"""
import html as _html
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave15.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from i18n import STRINGS  # noqa: E402

EN = STRINGS["en"]
CSS = Path("static/style.css").read_text(encoding="utf-8")

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


def esc(text):
    return _html.escape(str(text), quote=True)


app = create_app()
client = app.test_client()
NAME = "W15 Menu " + RUN_ID
r = client.post("/signup", data={
    "name": NAME, "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w15test-pass"})
check("signup for menu test user", r.status_code in (200, 302),
      f"status={r.status_code}")

# --- 1. Pages render ---------------------------------------------------------
home_r = client.get("/")
home = home_r.get_data(as_text=True)
check("GET / (signed in) -> 200", home_r.status_code == 200)
acct_r = client.get("/account")
acct = acct_r.get_data(as_text=True)
check("GET /account -> 200", acct_r.status_code == 200)
chats_r = client.get("/chats")
check("GET /chats -> 200", chats_r.status_code == 200)

# --- 2. Menu items, in order ---------------------------------------------------
check("menu panel present on home",
      'class="nav-dropdown menu-panel"' in home)
_dd = home[home.index('class="nav-dropdown'):] \
    if 'class="nav-dropdown' in home else ""
# Wave 16 (Suraj, 10 Nov 2026): "Previous Papers" was added to the
# menu right AFTER Board Mode — the expected list below includes it
# in exactly that position; every other item keeps its Wave-12 order.
ITEM_KEYS = ["menu_your_chats", "nav_board", "menu_papers",
             "nav_practice",
             "nav_topics", "nav_mistakes", "menu_copy_style",
             "nav_parents", "menu_language", "menu_settings"]
positions = []
for key in ITEM_KEYS:
    label = esc(EN[key])
    positions.append(_dd.find(label))
check("menu: all 10 items present",
      all(p >= 0 for p in positions),
      f"missing={[k for k, p in zip(ITEM_KEYS, positions) if p < 0]}")
check("menu: items in approved order",
      all(p >= 0 for p in positions)
      and positions == sorted(positions),
      f"positions={positions}")
check("menu: gold keep-line after the items",
      esc(EN["menu_keep_line"]) in _dd
      and _dd.find(esc(EN["menu_keep_line"])) > positions[-1])
check("menu: profile block + stats ids intact",
      'class="menu-profile"' in _dd
      and 'id="menu-stat-questions"' in _dd
      and 'id="menu-stat-chats"' in _dd)
check("menu: language row expands to 6 links",
      _dd.count('class="menu-lang-link"') == 6,
      f"links={_dd.count('class=' + chr(34) + 'menu-lang-link' + chr(34))}")

# --- 3. Logout placement (Wave-12 rule, re-asserted) ---------------------------
check("menu: NO logout link in the menu",
      'href="/logout"' not in _dd
      and esc(EN["nav_logout"]) not in _dd)
check("/account: logout link present (only there)",
      'href="/logout"' in acct and esc(EN["nav_logout"]) in acct)
check("home page: exactly one logout href (in account only)",
      home.count('href="/logout"') == 0)

# --- 4. CSS polish ------------------------------------------------------------
check("css: menu open keyframes",
      "@keyframes ganitra-menu-in" in CSS
      and "@keyframes ganitra-menu-col-in" in CSS)
check("css: [open] panel animation wired",
      ".nav-menu[open] .nav-dropdown" in CSS
      and "animation: ganitra-menu-in" in CSS
      and "animation: ganitra-menu-col-in" in CSS)
check("css: row transition rules",
      "transition: background-color .15s ease" in CSS)
check("css: press feedback (:active) on rows",
      ".menu-items > a:active" in CSS
      and ".menu-settings-row:active" in CSS
      and ".menu-close:active" in CSS)
check("css: stats numbers tabular",
      ".menu-stat-num" in CSS
      and "font-variant-numeric: tabular-nums" in CSS)
check("css: reduced-motion guard",
      "prefers-reduced-motion" in CSS)
check("css: Wave-12 structure untouched",
      ".menu-panel-inner" in CSS and "max-width: 640px" in CSS
      and ".menu-photo" in CSS and ".menu-gold-strip" in CSS)

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
