"""Wave 105 (Suraj, 17 Nov 2026): compact + comfortable chat.

Suraj studied the big AIs through Muse and ordered the best
of each, in Ganitra's own design: "chat choti chahiye but
achhi comfortable chahiye" — plus answer-presentation
alignment ("kaise ans deta hai, uss hisab se dekho"). The
full research + spec lives in research.md in the wave
folder. This wave is CSS rhythm + one JS cap:

  - the reading column narrows 800 -> 768px (the ChatGPT /
    Claude / Perplexity consensus), thread and composer
    together (the Wave-12 match rule still holds);
  - compactness from rhythm, never from smaller text
    (DeepSeek's flat density + Suraj's small-text rule):
    thread gap 18 -> 14, card padding 20/22 -> 16/18,
    step margins 9 -> 7, composer wrap/bar one notch
    tighter, auto-grow cap 160 -> 128px (~5 lines);
  - the working starts sooner (Perplexity's answer-first):
    intro top margin 12 -> 6;
  - display maths breathes (all five AIs): 8px air around
    a rendered display equation;
  - comfort mechanics: overscroll containment + a thin
    scrollbar on the thread, a full 40px tap height on
    the answer glyph row, a calmer card shadow (the
    shared .bubble rule — the /solve page calms too), a
    24px floor under the composer textarea (Claude's
    notepad lesson).

Frozen, as always: the answer card's internals (plain
solving lines, the plain bold answer line, advice behind
the bulb, the 5 glyphs below the card), no chips, the
logo, the menu, the scene (OFF), the composer element
order, the plain send sign, every font size, and the
header (Wave 104 owns the header buttons). Pins move to
?v=43 / ganitra-static-v20 with this wave's CSS.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

W105 = CSS[CSS.index("Wave 105: compact + comfortable chat"):]


# --- The 768px reading column ------------------------------------

def test_column_narrows_to_768_thread_and_composer():
    assert "body.chat-page .chat-log { max-width: 768px; }" in W105
    assert "body.chat-page .chat-form { max-width: 768px; }" in W105


# --- Compact rhythm ------------------------------------------------

def test_thread_gap_and_padding_tighten():
    assert "gap: 14px; padding: 20px 16px 16px;" in W105
    # phone rhythm inside the wave's own media block
    assert "body.chat-page .chat-log { padding: 16px 12px 16px; }" in W105


def test_cards_and_bubbles_slim_down():
    assert "body.chat-page .bubble.bot { padding: 16px 18px; }" in W105
    assert "body.chat-page .bubble.bot { padding: 14px 16px; }" in W105
    assert "body.chat-page .bubble.bot.plain-reply" in W105
    assert "padding: 12px 16px;" in W105
    assert "body.chat-page .bubble.user { padding: 12px 16px; }" in W105


def test_steps_tighten_but_keep_their_breathing_line_height():
    assert "body.chat-page .bubble ol.steps li { margin: 7px 0; }" in W105
    # Wave 68's step typography is untouched: 14px / 1.7.
    assert "font-size: 14px; line-height: 1.7; margin: 9px 0;" in CSS


def test_working_starts_sooner_under_the_intro():
    assert "body.chat-page .bubble .answer-intro" in W105
    assert "margin: 6px 0 2px;" in W105
    assert "body.chat-page .bubble .explain { margin: 8px 0; }" in W105


def test_advice_card_trims_with_the_card():
    assert "margin: 8px 0 4px; padding: 13px 15px;" in W105


# --- Answer presentation ------------------------------------------

def test_display_maths_gets_its_own_air():
    assert 'mjx-container[display="true"]' in W105
    assert "margin: 8px 0;" in W105


def test_card_shadow_calms_down():
    assert ".bubble { box-shadow: 0 4px 14px rgba(101, 84, 40, .07); }" \
        in W105


# --- Comfort mechanics ---------------------------------------------

def test_scroll_stays_in_the_thread():
    assert "overscroll-behavior: contain; scrollbar-width: thin;" in W105


def test_glyph_row_reaches_a_full_40px_tap():
    assert "body.chat-page .answer-actions .act-btn" in W105
    assert "padding: 11px 3px;" in W105


def test_composer_tighter_outside_floored_inside():
    assert "body.chat-page .chat-bar { padding: 12px 14px; }" in W105
    assert "min-height: 24px; max-height: 128px;" in W105
    assert "Math.min(box.scrollHeight, 128)" in INDEX


def test_empty_greeting_trims_one_notch():
    assert "clamp(24px, 4.6vw, 32px)" in W105


# --- Frozen lines ----------------------------------------------------

def test_no_font_size_moves_except_the_greeting_clamp():
    # Suraj's small-text rule stands: answers 13px, steps
    # 14px, composer 13.5px — all still pinned by the older
    # waves' tests; this wave's block re-declares none of
    # them (the greeting clamp is a display size, not text).
    assert "body.chat-page .bubble { font-size: 13px;" in CSS
    assert "font-size: 13.5px; line-height: 1.55;" in CSS
    assert W105.count("font-size") == 1  # only the greeting clamp


def test_header_and_menu_are_not_this_waves_business():
    assert ".chat-header" not in W105
    assert ".nav-menu" not in W105
    assert ".chats-plus" not in W105


def test_no_chips_creep_back_in():
    assert ".chip" not in W105
    assert "example" not in W105.lower()


def test_answer_card_internals_untouched():
    # The plain bold answer line keeps its Wave-24/27 spec.
    assert "body.chat-page .bubble .answer-big {" in CSS
    assert "font-size: 14.5px; line-height: 1.5;" in CSS


# --- Pins -------------------------------------------------------------

def test_pins_moved_with_the_css():
    assert "v='43'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v20"' in SW
    assert '"/static/style.css?v=43"' in SW


# --- The page still serves ---------------------------------------------

def test_chat_page_serves_with_the_new_sheet(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W105 Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w105-test-pass"})
    page = client.get("/").get_data(as_text=True)
    assert "style.css?v=43" in page
    assert 'id="q"' in page
