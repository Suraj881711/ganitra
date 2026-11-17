"""Wave 104: ☰ menu button to the far right, circle removed.

Suraj (17 Nov 2026): "menu ki button ko add tab wali button
hai uss side karana hai bilkul side mai or menu ki button
par jo circule hai usse hata dena" — the ☰ moves to the
same side as the "+" (add/new-chat) button, flush to the
far edge, AFTER the "+", and the circle around the ☰
(border + white background + shadow + 999px radius) is
removed so it reads as a plain glyph like the "+" itself.

What this wave changed:
- templates/index.html + templates/base.html: in the top
  bar's tools row the chats-plus anchor now comes BEFORE
  the _menu.html include, so the ☰ is the rightmost item.
- static/style.css + the wave72-critical mirror in
  base.html: .nav-menu-btn loses its circle (border: 0,
  background: none, box-shadow: none, no border-radius);
  the <=560px pin that held .nav-menu at the far LEFT is
  mirrored to the far RIGHT (right: 7px, the bar reserves
  padding-right instead of padding-left).
- Pins bumped for the CSS change: stylesheet ?v=41,
  service-worker cache ganitra-static-v18.
The full-page menu panel, the item list and its order are
untouched.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
MENU = (ROOT / "templates" / "_menu.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


def _rule(text, selector):
    """Body of the first `selector { ... }` rule in text."""
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", text)
    assert m, selector
    return m.group(1)


def _normalised(body):
    body = re.sub(r"/\*.*?\*/", "", body, flags=re.S)
    return " ".join(body.split())


def _pin_segment(text):
    """The <=560px block that pins .nav-menu inside the bar."""
    idx = text.index(".chat-header:has(.nav-menu)")
    return text[max(0, idx - 900):idx + 500]


def _header_block(text):
    start = text.index('<header class="chat-header">')
    end = text.index("</header>", start)
    return text[start:end]


# --- (a) the circle is gone ---------------------------------------------

def test_menu_button_has_no_circle_in_style_css():
    rule = _rule(CSS, ".nav-menu-btn")
    assert "999px" not in rule
    assert "border-radius" not in rule
    assert "#ddd3ba" not in rule
    assert "solid" not in rule
    assert "border: 0" in rule
    assert "background: none" in rule
    assert "box-shadow: none" in rule


def test_menu_button_has_no_circle_in_critical_mirror():
    rule = _rule(BASE, ".nav-menu-btn")
    assert "999px" not in rule
    assert "border-radius" not in rule
    assert "#ddd3ba" not in rule
    assert "solid" not in rule
    assert "border: 0" in rule
    assert "background: none" in rule
    assert "box-shadow: none" in rule


def test_menu_button_rule_identical_in_both_sheets():
    # Wave-72 mirror discipline: the rule lives in style.css
    # AND in base.html's critical block — same declarations.
    assert _normalised(_rule(CSS, ".nav-menu-btn")) \
        == _normalised(_rule(BASE, ".nav-menu-btn"))


def test_menu_button_keeps_tap_target_and_press_effect():
    rule = _rule(CSS, ".nav-menu-btn")
    assert "width: 44px" in rule and "height: 44px" in rule
    assert ".nav-menu-btn:active { transform: scale(.94); }" in CSS
    assert ".nav-menu-btn:active { transform: scale(.94); }" in BASE


# --- (b) ☰ is the rightmost item in the bar ------------------------------

def test_plus_comes_before_menu_in_chat_header():
    header = _header_block(INDEX)
    assert header.index('class="chats-plus"') \
        < header.index('{% include "_menu.html" %}')


def test_plus_comes_before_menu_in_base_header():
    header = _header_block(BASE)
    assert header.index('class="chats-plus"') \
        < header.index('{% include "_menu.html" %}')


def test_tools_row_still_packs_to_the_right():
    # Desktop placement: the tools row fills the bar and its
    # content packs to the right edge, so the last item (the
    # ☰) sits flush at the far right.
    assert ".header-tools { flex: 1 1 auto; min-width: 0;" \
        " justify-content: flex-end; }" in CSS


# --- (c) phones: the pin moved from the left edge to the right -----------

def test_phone_block_pins_menu_to_the_right():
    for text in (CSS, BASE):
        seg = _pin_segment(text)
        assert "right: 7px" in seg
        assert "padding-right: 58px" in seg
        assert "left: 7px" not in seg
        assert "padding-left: 58px" not in seg


def test_phone_pin_rules_identical_in_both_sheets():
    for selector in (".chat-header:has(.nav-menu)",
                     ".chat-header:has(.nav-menu) .nav-menu"):
        assert _normalised(_rule(CSS, selector)) \
            == _normalised(_rule(BASE, selector)), selector


# --- the panel and the pins ------------------------------------------------

def test_menu_panel_still_full_page_fixed():
    decl = "position: fixed; inset: 0; z-index: 200;"
    assert decl in CSS and decl in BASE


def test_menu_items_and_order_untouched():
    items = re.findall(r'<a href="([^"]+)">', MENU)
    assert items == ["/chats", "/board", "/papers",
                     "/practice-mode", "/practice", "/test",
                     "/topics", "/mistakes",
                     "/solution/print?style=hand",
                     "/parent-report", "/progress"]


def test_pins_bumped_for_this_css_change():
    assert "filename='style.css', v='41'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v18"' in SW
    assert '"/static/style.css?v=41"' in SW
