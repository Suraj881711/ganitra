"""Wave 118 (Suraj, 17 Nov 2026): chat COMFORT, the deep pass.

Wave 105 took the best static layout of the big AIs; Suraj's
verdict was still "baaki AI jaisa comfortable kyu nhi lag
raha hai" — so this wave measured the INTERACTION feel in a
real browser (390x667 + 390x844 phones, 1280px desktop) and
fixed what the numbers actually showed:

  - a tall answer landed BOTTOM-first: its start sat ~121px
    above the visible area, so the student had to scroll up
    to find where the answer begins. The big AIs settle a
    long answer so it is read FROM ITS START. Wave 118: the
    student's own just-asked turn (and only that turn —
    restored chats keep the Wave-18 bottom landing) aligns
    to its start once the typeset settles: his question at
    the top, the answer flowing below it. A turn that fits
    the screen keeps the bottom landing.
  - late growth inside the card (MathJax typesetting, a
    graph image) pushed the final answer line out of view
    with zero compensation (simulated +190px growth: the
    answer line went from visible to gone). A ~3s
    ResizeObserver settle window now re-applies the
    alignment while the card grows — unless the student
    takes over the scroll (wheel / touch / pointer, or a
    scroll position the aligner did not set).
  - tap targets: the answer glyph row was 24x40px (Wave 105
    fixed the height only) and the composer signs' tap halo
    ~40px. Both are a full 44px now; no glyph changed size.
  - phone keyboard: the chat follows visualViewport resizes
    (iOS Safari fires no window resize when its keyboard
    overlays), and the viewport meta asks Android Chrome to
    resize the layout for the keyboard instead of covering
    the composer.

Presentation/interaction only: no answer content, format,
font size, colour, logo, menu or feature changed. The
reading rhythm was measured against the Wave-105 spec and
was on-spec, so it is untouched. Pins move to ?v=43 /
ganitra-static-v21 with this wave's CSS (Wave 116 may pick
the same numbers in its tree — the parent renumbers one at
merge).
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

W118 = CSS[CSS.index("Wave 118: chat comfort (arrival + taps)"):]
ALIGNER = INDEX[INDEX.index("Wave 118: answer-arrival comfort"):
                INDEX.index("function hideEmpty()")]


@pytest.fixture()
def page(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": "W118 Comfort Tester", "class": "10", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w118-comfort-pass"})
    return client.get("/").get_data(as_text=True)


# --- The aligner exists and is wired to the live turn only -------

def test_aligner_present_with_start_rule():
    assert "function alignLiveAnswer(el, ready)" in ALIGNER
    # tall turn: align to the turn's start (the question anchor)
    assert "er.height > scroller.clientHeight * 0.92" in ALIGNER
    assert "(ar.top - sr.top) - 10" in ALIGNER
    # fitting turn: the bottom landing. Positioning is instant
    # on purpose — a glide's mid-flight scroll positions are
    # indistinguishable from a student scroll, which broke the
    # takeover check in the first browser pass of this wave.
    assert "scroller.scrollTop = scroller.scrollHeight;" in ALIGNER
    assert 'behavior: "auto"' in ALIGNER


def test_only_the_submit_handler_arms_the_aligner():
    assert "liveAnswerPending = true;  // Wave 118" in INDEX
    # restored/replayed chats explicitly disarm it
    assert "liveAnswerPending = false;  // Wave 118" in INDEX
    # the render paths consult it before the classic landing
    assert "if (!w118Live) scrollLog();" in INDEX
    assert "if (!liveAnswerPending) scrollLog();" in INDEX


def test_aligner_stands_down_if_student_scrolled_up_while_waiting():
    # Wave 18's rule outranks the aligner: a student who
    # scrolled up to re-read during the solve is never yanked.
    assert "if (liveScrollAway) { stopLiveSettle(); return; }" in ALIGNER
    # The away-detection is direction-aware (a falling
    # scrollTop against the turn's high-water mark) — the
    # naive stickBottom check raced the submit glide's own
    # scroll events and stood the aligner down on fast
    # answers in this wave's browser pass.
    assert "scroller.scrollTop < liveTurnMaxTop - 6" in INDEX
    assert "liveTurnMaxTop = scroller ? scroller.scrollTop : 0;" in INDEX


def test_settle_window_watches_growth_and_yields_to_student():
    assert "new ResizeObserver" in ALIGNER
    assert "window.setTimeout(stopLiveSettle, 3000)" in ALIGNER
    for evt in ('"wheel"', '"touchstart"', '"pointerdown"'):
        assert evt in ALIGNER
    # a scroll position the aligner did not set = the student
    assert "Math.abs(scroller.scrollTop - state.lastTop) > 6" in ALIGNER


def test_aligner_waits_for_typeset_but_never_hangs():
    assert "w118Typeset = window.MathJax.typesetPromise([div])" in INDEX
    assert "if (w118Live) alignLiveAnswer(wrap, w118Typeset);" in INDEX
    # the 600ms cap: a stuck typeset can never hold the landing
    assert "window.setTimeout(start, 600);" in ALIGNER


# --- Keyboard / viewport ------------------------------------------

def test_visual_viewport_keeps_bottom_riders_pinned():
    assert "window.visualViewport.addEventListener" in INDEX
    assert "interactive-widget=resizes-content" in BASE


# --- Tap targets ----------------------------------------------------

def test_glyph_row_is_a_full_44px_target():
    assert "body.chat-page .answer-actions .act-btn " \
           "{ padding: 13px 13px; }" in W118
    assert "body.chat-page .answer-actions { gap: 4px; }" in W118
    # Wave 105's 40px-height rule stays in place below ours in
    # the cascade history — the appended block wins by order.
    assert CSS.index("Wave 118: chat comfort") > \
        CSS.index("Wave 105: compact + comfortable chat")


def test_composer_halo_reaches_44px():
    assert "body.chat-page .chat-bar .composer-btn::after" in W118
    assert "inset: -4px;" in W118


# --- Pins -------------------------------------------------------------

def test_pins_bumped_to_v42_v19():
    assert "v='51'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v28"' in SW
    assert '"/static/style.css?v=51"' in SW


# --- The served page carries the wave -------------------------------

def test_served_page_has_aligner_and_new_pins(page):
    assert "alignLiveAnswer" in page
    assert "style.css?v=51" in page
    assert "interactive-widget=resizes-content" in page
