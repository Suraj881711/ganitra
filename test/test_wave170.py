"""Wave 170: robot avatar card + soft home background.

Suraj, 19 Nov 2026: shown a screenshot of the Muse app,
he said "Aisa design karana hai background kaa" — and on
being offered the two halves separately, he chose "Dono
karo" (do both):

1. ROBOT CARD — the home robot (Wave 168: standing in
   .empty-robot-top at the very top of .chat-shell, below
   the header/menu line) now sits inside a soft rounded
   CARD with the name "Ganitra" under it, avatar-card
   style. The card is a pure container: the robot SVG is
   byte-identical to main's Wave 160/161 artwork (pinned
   by SHA-256 below), its Wave 161 palette and every
   animation are untouched, no letter G appears anywhere,
   and the frozen logo below is untouched.
2. SOFT BACKGROUND — the home/empty-state backdrop goes
   soft and calm, Muse-app-like in FEEL only, built from
   Ganitra's own cream/teal palette (cream wash, a whisper
   of the antenna-mint teal, the app's own gold). It is
   scoped to body.chat-page WITHOUT chat-active, so the
   active chat view and every other page keep the exact
   backdrop they already had; no bubble, answer card,
   menu or composer rule changed.

Adapted, never copied: no Muse branding and none of
Claude's palette hexes appear (pinned below). The app
has no dark mode (single light theme), so there is no
dark variant to keep readable. The greeting still says
"Hello <name>" — Suraj's Hii/Hello decision is pending
and this wave does not touch it. The card hides with
.empty-robot-top the moment a chat starts
(body.chat-active), when the header buddy takes over.

Pins moved with the CSS: ?v=54 / ganitra-static-v31.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

# The robot SVG block exactly as it stands in main
# (Deploy-38 tree) — recorded 19 Nov 2026 before this
# wave's edits. Wave 170 changes presentation only, so
# the block must stay byte-identical.
ROBOT_SVG_SHA256 = (
    "b62bbe63553d031e5a92dd167535423cb4f143a8ed7d9c227859c13fd379772a"
)
ROBOT_SVG_LEN = 10678

# Claude/Anthropic brand palette — must never appear in
# Ganitra's stylesheet. The look is adapted in Ganitra's
# own cream/teal family instead.
CLAUDE_HEXES = [
    "#d97757",  # Claude orange (primary brand colour)
    "#cc785c",  # Claude coral
    "#da7756",  # Claude orange variant
    "#c15f3c",  # Anthropic "crail" dark orange
    "#f0eee6",  # Claude app cream background
    "#faf9f5",  # Claude light background
    "#262624",  # Claude dark background
]


def _rule(selector):
    block = CSS[CSS.index(selector + " {"):]
    return block[:block.index("}")]


def _robot_svg_block():
    start = INDEX.index('<svg class="robot"')
    end = INDEX.index("</svg>", start) + len("</svg>")
    return INDEX[start:end]


# --- 1. The card wraps the robot at the very top ----------------------

def test_card_wraps_robot_inside_top_wrapper():
    top = INDEX.index('<div class="empty-robot-top"')
    card = INDEX.index('<div class="robot-card">')
    robot = INDEX.index('<svg class="robot"')
    # Card inside the Wave 168 top wrapper, robot inside the card.
    assert top < card < robot
    # …and the whole card still precedes the scrolling thread.
    assert card < INDEX.index('<div class="chat-scroll"')


def test_card_shows_the_name_ganitra():
    robot_end = INDEX.index("</svg>", INDEX.index('<svg class="robot"'))
    name = INDEX.index('<div class="robot-card-name">Ganitra</div>')
    # The name sits under the robot, inside the card, and
    # there is exactly one such name plate on the page.
    assert robot_end < name
    assert INDEX.count('<div class="robot-card-name">Ganitra</div>') == 1
    # Still inside the top wrapper (before the thread starts).
    assert name < INDEX.index('<div class="chat-scroll"')


def test_card_still_gated_on_named_student():
    shell = INDEX.index('<div class="chat-shell">')
    card = INDEX.index('<div class="robot-card">')
    assert "{% if saathi_name %}" in INDEX[shell:card]


def test_card_adds_no_letter_g_anywhere():
    # The name plate is text only; no new artwork, no G mark.
    card_open = INDEX.index('<div class="robot-card">')
    card_close = INDEX.index('<div class="chat-scroll"')
    card_region = INDEX[card_open:card_close]
    assert card_region.count("<svg") == 1  # only the robot itself
    assert "logo" not in card_region


# --- 2. Card styling: soft, rounded, Ganitra palette ------------------

def test_robot_card_rule_is_soft_and_rounded():
    rule = _rule(".robot-card")
    assert "border-radius:" in rule
    assert "background:" in rule
    assert "#fdf6e1" in rule or "#fffef9" in rule  # Ganitra creams
    assert "box-shadow:" in rule  # the soft lift


def test_robot_card_name_rule_uses_deep_teal():
    rule = _rule(".robot-card-name")
    assert "#074335" in rule  # Wave 161 deep teal


# --- 3. Soft background, Ganitra colours only -------------------------

def test_soft_background_scoped_to_empty_state():
    rule = _rule("body.chat-page:not(.chat-active)")
    # A calm warm wash: cream gradient + Ganitra tints.
    assert "#fbf4e6" in rule and "#f8efdc" in rule
    assert "rgba(43, 217, 169" in rule   # antenna-mint teal whisper
    assert "rgba(231, 200, 119" in rule  # the app's own gold


def test_no_claude_brand_colours_in_stylesheet():
    low = CSS.lower()
    for hexcode in CLAUDE_HEXES:
        assert hexcode not in low, hexcode


def test_global_body_background_untouched():
    # Other pages share the global body rule; Wave 170 did
    # not restyle it (the soft backdrop is the scoped
    # chat-page rule above, nothing wider).
    body = _rule("body")
    assert "radial-gradient(900px 420px at 85% -5%" in body
    assert "linear-gradient(180deg, #fffdf8 0%, var(--bg) 320px)" in body


# --- 4. The artwork itself did not change -----------------------------

def test_robot_svg_byte_identical_to_main():
    block = _robot_svg_block()
    assert len(block) == ROBOT_SVG_LEN
    digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
    assert digest == ROBOT_SVG_SHA256


def test_robot_palette_still_wave161_dark():
    block = _robot_svg_block()
    assert "#f0d3a0" in block  # darkened cream body
    assert "#0a7a64" in block  # darkened teal
    assert "#074335" in block  # deep teal
    assert "#2fe8b8" in block  # antenna lights stay bright


# --- 5. The card hides when a chat starts -----------------------------

def test_card_hides_with_top_wrapper_on_chat_active():
    # The Wave 168 hide rule covers the wrapper; the card
    # lives inside it, and no rule re-shows the card.
    assert "body.chat-active .empty-robot-top { display: none; }" in CSS
    assert "chat-active .robot-card" not in CSS
    card = INDEX.index('<div class="robot-card">')
    assert INDEX.index('<div class="empty-robot-top"') < card
    assert card < INDEX.index('<div class="chat-scroll"')


# --- 6. Pins ------------------------------------------------------------

def test_pins_v54_v31():
    assert "filename='style.css', v='54'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v31"' in SW
    assert '"/static/style.css?v=54"' in SW
    assert "v='53'" not in BASE
    assert "ganitra-static-v30" not in SW
