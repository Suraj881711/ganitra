"""Wave 72: critical CSS inlined in base.html.

Suraj (16 Nov 2026): "menu achhe kaam nhi kar rha hai". A
live check found the menu works, but the free plan
intermittently fails the style.css request (502), so pages
arrive unstyled and the menu renders as plain inline links
instead of its full-screen panel. Fix (no design change):
the layout-critical rules from style.css are copied
verbatim into a <style id="wave72-critical"> block in
base.html BEFORE the stylesheet link — the sheet overrides
them with identical values when it loads, and the page
still lays out when it does not.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def _critical_block():
    start = BASE.index('<style id="wave72-critical">')
    end = BASE.index("</style>", start)
    return BASE[start:end]


def test_critical_block_exists_and_precedes_stylesheet():
    assert '<style id="wave72-critical">' in BASE
    assert BASE.index('<style id="wave72-critical">') \
        < BASE.index("style.css', v='43'")


def test_critical_block_carries_the_menu_panel_rule():
    block = _critical_block()
    # The full-screen menu panel rule — the exact fix target.
    assert ".nav-menu[open] .nav-dropdown" in block
    assert "position: fixed; inset: 0; z-index: 200;" in block
    for needle in (".nav-menu-btn", ".menu-panel-inner",
                   ".menu-items", ".menu-gold-strip",
                   "@keyframes ganitra-menu-in"):
        assert needle in block, needle


def test_critical_block_carries_layout_basics():
    block = _critical_block()
    for needle in (":root", ".chat-header", ".chat-brand",
                   ".empty-logo-img", ".composer-wrap",
                   ".backnav-btn", "body.chat-page"):
        assert needle in block, needle


def test_critical_rules_match_style_css_verbatim():
    # The panel declaration inlined in base.html must be the
    # same one style.css carries (no design drift).
    decl = "position: fixed; inset: 0; z-index: 200;"
    assert decl in CSS and decl in _critical_block()


def test_stylesheet_link_unchanged():
    assert "filename='style.css', v='43'" in BASE
