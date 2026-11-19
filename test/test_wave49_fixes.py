"""Wave 49 (Suraj, 15 Nov 2026 ~01:22 IST): chat-box
COMFORT — "Abhi bhi comfortable nhi lg rha hai", said after
the Wave 27/28 comfort pass, looking at the live site.

A screenshot audit at 390px + 1280px (empty / short answer
/ long answer / long draft; wave49-shots/) measured the
causes this wave fixes:
  1. the 📎 attach button squashed to 21px (phone) / 29px
     (desktop) by flex-shrink while its neighbours stood
     at 36px — buttons now never shrink and stand at 40px
     (Wave-27 halo -> a true 44px tap target);
  2. the composer typed in the browser's MONOSPACE — the
     textarea now inherits the site font;
  3. the composer floated mid-screen before the first
     question (scroll area collapsed pre-chat) — it now
     docks at the bottom in every state and the empty
     state centres above it;
  4. a roomier bar (14px 16px) and textarea (8px 10px),
     and more air in the thread (28/20/24 desktop,
     20/12/24 phone);
  5. scrollLog glides on short hops, jumps on far ones;
     a grown composer / opened keyboard re-pins the
     bottom; an IME-composition Enter no longer sends;
     the textarea carries enterkeyhint="send";
  6. iOS only: the composer renders at 16px so focus
     never force-zooms (answers stay 13px; Android and
     desktop keep the composer's 13.5px);
  7. 100vh fallback before 100dvh, notch side insets.
Delivery hygiene: stylesheet ?v=31, worker cache v8
(merge-2 reconciliation — this wave's CSS needed a fresh
cache key because Wave 43 had already landed ?v=30 / v7).
Sprite URLs stay ?v=29 — no sprite file changed, and
sprite pins move only with sprite changes (Wave 28).
Frozen, as always: the logo artwork, the Wave-24 answer
card + icon row, the scene timing, the Teach wiring.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

W49 = CSS[CSS.index("Wave 49: chat-box COMFORT"):]


@pytest.fixture()
def page(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W49 Fixes Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w49-fixes-pass"})
    return client.get("/").get_data(as_text=True)


# --- 1. The squashed attach button ------------------------------

def test_bar_buttons_never_shrink_and_stand_at_40px():
    assert "flex: none; width: 40px; height: 40px; min-height: 40px;" \
        in W49
    # The textarea gives up the 100% width that inflated its
    # flex base size and starved the button.
    assert "width: auto; font-family: inherit; padding: 8px 10px;" \
        in W49


def test_composer_no_longer_types_in_monospace():
    assert "font-family: inherit" in W49


def test_send_sign_stays_plain():
    # Wave 49 grows the send button's target, never its fill.
    block = W49[W49.index("body.chat-page .chat-bar .composer-btn,"):]
    block = block[:block.index("}")]
    assert "background" not in block
    assert "var(--accent)" not in block


# --- 2. Docked composer + centred empty state -------------------

def test_composer_docked_before_first_question_too():
    assert "body.chat-page:not(.chat-active) .chat-scroll" \
           " { flex: 1 1 auto; }" in W49
    assert ".chat-empty { margin: auto 0;" in W49
    assert "min-height: 100%; box-sizing: border-box;" in W49


# --- 3. Roomier bar + thread air --------------------------------

def test_roomier_bar_and_thread_padding():
    assert "body.chat-page .chat-bar { padding: 14px 16px; }" in W49
    assert "body.chat-page .chat-log { padding: 28px 20px 24px; }" \
        in W49
    assert "body.chat-page .chat-log { padding: 20px 12px 24px; }" \
        in W49


# --- 4. Scroll + keyboard behaviour (index.html) -----------------

def test_scrolllog_glides_short_hops_jumps_far_ones():
    assert 'behavior: dist < scroller.clientHeight * 1.5' in INDEX
    assert '? "smooth" : "auto"' in INDEX


def test_grown_composer_and_resize_repins():
    assert 'box.style.height = Math.min(box.scrollHeight, 128)' \
        in INDEX
    inp = INDEX[INDEX.index('box.addEventListener("input"'):]
    assert "scrollLog();" in inp[:inp.index("});")]
    assert 'window.addEventListener("resize"' in INDEX
    assert "if (stickBottom) scrollLog(true);" in INDEX


def test_ime_composition_enter_is_not_a_send(page):
    assert "ev.isComposing || ev.keyCode === 229" in INDEX
    # The send wiring itself is unchanged.
    assert 'if (ev.key === "Enter" && !ev.shiftKey)' in INDEX
    tag = re.search(r'<textarea id="q"[^>]*>', page)
    assert tag is not None and 'enterkeyhint="send"' in tag.group(0)


# --- 5. iOS zoom guard, scoped to iOS only -----------------------

def test_ios_composer_16px_only_under_ios_supports():
    marker = "@supports (-webkit-touch-callout: none)"
    assert "@media (pointer: coarse)" in W49
    assert marker in W49
    rule = "body.chat-page .chat-bar textarea { font-size: 16px; }"
    assert W49.index(marker) < W49.index(rule)
    # The base composer size (what Android/desktop render,
    # and what the computed-style tests pin) is untouched.
    assert "font-size: 13.5px; line-height: 1.55;" in CSS


# --- 6. Height fallback + notch sides ----------------------------

def test_height_fallback_and_safe_area_sides():
    assert "height: 100vh; height: 100dvh;" in W49
    assert "max(14px, env(safe-area-inset-left))" in W49
    assert "max(10px, env(safe-area-inset-left))" in W49


# --- 7. Delivery pins ---------------------------------------------

def test_delivery_versions_wave49():
    assert "v='60'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in SW
    # Sprites did not change, so their pins do not move.
    assert "filename='scene-eagle.webp', v='29'" in INDEX
    assert '"/static/scene-boy.webp?v=29"' in INDEX


# --- 8. Frozen things stay frozen ---------------------------------

def test_teach_wiring_untouched():
    assert "function startTeachPlayback()" in INDEX
