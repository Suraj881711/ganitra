"""Wave 116: design polish expansion on the post-Deploy-24
design (Suraj, 17 Nov 2026: "design ka kaam badao").

Headline fix: the phone menu bug in its CURRENT (Wave 104)
form — at <=560px the .nav-menu details element was centred
with transform: translateY(-50%); a transformed element is
the containing block for its position:fixed descendants, so
the open full-screen panel was trapped inside the ☰ button's
42x44px box at the top-right. Centring is now done with a
negative margin (-22px, -21px at <=480px where the button is
42px) — same button spot, no transform, panel free.

Also pinned here: the Wave-2 hero tokens (--ink/--sub/
--gold/--gold2) promoted to :root (the chat bar, bubbles,
auth inputs and chats search already referenced them
app-wide and silently fell back); topic cards warmed to the
app palette; the all-chats "+" in the app teal; one Fraunces
heading voice on .card pages; 40px answer-panel chips; the
pins at ?v=43 / ganitra-static-v21.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


def _critical_block():
    start = BASE.index('<style id="wave72-critical">')
    end = BASE.index("</style>", start)
    return BASE[start:end]


def _menu_rule(text):
    i = text.index(".chat-header:has(.nav-menu) .nav-menu {")
    j = text.index("}", i)
    return text[i:j]


def test_menu_centring_uses_margin_not_transform():
    for text in (CSS, _critical_block()):
        rule = _menu_rule(text)
        assert "margin: -22px 0 0;" in rule
        assert "transform:" not in rule
        assert ".chat-header:has(.nav-menu) .nav-menu " \
               "{ margin-top: -21px; }" in text


def test_mirrored_root_and_menu_rules_match_style_css():
    block = _critical_block()

    def root(t):
        i = t.index(":root {")
        return t[i:t.index("}", i) + 1]

    assert root(CSS) == root(block)
    assert _menu_rule(CSS) == _menu_rule(block)


def test_hero_tokens_promoted_to_root():
    i = CSS.index(":root {")
    root = CSS[i:CSS.index("}", i)]
    for decl in ("--ink: #16213a;", "--sub: #5b6b8c;",
                 "--gold: #c9a24b;", "--gold2: #e7c877;"):
        assert decl in root, decl


def test_topic_cards_warm_and_chats_plus_teal():
    i = CSS.index(".topic-card {")
    card = CSS[i:CSS.index("}", i)]
    assert "#fdf9ef" in card and "#e7dec9" in card
    assert "#f4f7fc" not in card and "#e2e8f3" not in card
    i = CSS.index(".chats-new-big {")
    plus = CSS[i:CSS.index("}", i)]
    assert "background: var(--accent)" in plus
    assert "#2563eb" not in plus


def test_card_heading_voice_and_panel_chips():
    assert ".card > h2" in CSS and ".card > h3" in CSS
    for sel in (".method-chip {", ".listen-chip {",
                ".method-solve-btn {", ".method-listen {"):
        i = CSS.index(sel)
        assert "min-height: 40px" in CSS[i:CSS.index("}", i)], sel


def test_finish_details():
    assert "::selection" in CSS
    assert ":focus-visible" in CSS
    i = CSS.index(".bubble.bot {")
    assert "border: 1px solid var(--line);" in CSS[i:CSS.index("}", i)]


def test_pins_v42_v19():
    assert "filename='style.css', v='51'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v28"' in SW
    assert '"/static/style.css?v=51"' in SW
    # Deploy-25 merge: the final pins are ?v=43 / v20 (this
    # wave's ?v=42 / v19 superseded in the combined tree);
    # every earlier pin must be gone.
    assert "v='42'" not in BASE
    assert "v='41'" not in BASE
    # Wave 127 (Deploy-27 merge): the Deploy-25/26 pins are
    # gone too.
    assert "v='43'" not in BASE
    assert "ganitra-static-v20" not in SW
    assert "ganitra-static-v19" not in SW
    assert "ganitra-static-v18" not in SW
