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

Pins moved with the CSS: ?v=60 / ganitra-static-v38.

Wave 181 update (19 Nov 2026): Suraj replaced the robot
and its card with the new rendered mascot in a WHITE
CIRCLE (his approved preview). The card-specific pins
below were updated to the circle reality; the soft
background half of this wave is untouched and still
pinned exactly as before.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

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

def test_circle_wraps_mascot_inside_top_wrapper():
    top = INDEX.index('<div class="empty-robot-top"')
    home = INDEX.index('<div class="mascot-home"')
    circle = INDEX.index('<div class="mascot-circle">')
    # Mascot inside the Wave 168 top wrapper, circle inside it.
    assert top < home < circle
    # …and the whole mascot still precedes the scrolling thread.
    assert circle < INDEX.index('<div class="chat-scroll"')


def test_circle_has_no_name_plate():
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — he never asked for the name plate under the
    # circle ("maine toh nhi bola waha par ganitra ko
    # likho"), so there is no name plate anywhere now.
    # (This test pinned the plate's presence until now.)
    assert "mascot-name" not in INDEX
    assert '<div class="mascot-name">Ganitra</div>' not in INDEX


def test_circle_still_gated_on_named_student():
    shell = INDEX.index('<div class="chat-shell">')
    circle = INDEX.index('<div class="mascot-circle">')
    assert "{% if saathi_name %}" in INDEX[shell:circle]


def test_circle_adds_no_letter_g_anywhere():
    # The mascot is photographs of the robot only — no SVG
    # artwork, no logo machinery in the mascot region.
    home_open = INDEX.index('<div class="mascot-home"')
    home_close = INDEX.index('<div class="chat-scroll"')
    home_region = INDEX[home_open:home_close]
    assert home_region.count("<svg") == 0
    assert "logo" not in home_region


# --- 2. Card styling: soft, rounded, Ganitra palette ------------------

def test_mascot_circle_rule_is_white_and_round():
    # Wave 181: Suraj's approved preview — a WHITE circle
    # with a soft teal ring and a soft shadow.
    rule = _rule(".mascot-circle")
    assert "border-radius: 50%" in rule
    assert "background: #ffffff" in rule
    assert "rgba(10, 122, 100" in rule  # the teal ring
    assert "box-shadow:" in rule  # the soft lift


def test_mascot_name_rule_removed():
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the .mascot-name rule is gone with the plate.
    # (This test pinned the rule's deep-teal colour until
    # now.)
    assert ".mascot-name" not in CSS


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


# --- 4. The old artwork is gone --------------------------------

def test_old_svg_robot_fully_gone():
    # Wave 181 replaced the character: no SVG robot, no
    # robot card, none of its CSS survives anywhere.
    assert '<svg class="robot"' not in INDEX
    assert 'class="robot-card"' not in INDEX
    assert ".robot-card" not in CSS
    assert ".robot {" not in CSS
    assert "@keyframes robot-" not in CSS


# --- 5. The mascot hides when a chat starts -----------------------------

def test_circle_hides_with_top_wrapper_on_chat_active():
    # The Wave 168 hide rule covers the wrapper; the mascot
    # lives inside it, and no rule re-shows the circle.
    assert "body.chat-active .empty-robot-top { display: none; }" in CSS
    assert "chat-active .mascot-circle" not in CSS
    circle = INDEX.index('<div class="mascot-circle">')
    assert INDEX.index('<div class="empty-robot-top"') < circle
    assert circle < INDEX.index('<div class="chat-scroll"')


# --- 6. Pins ------------------------------------------------------------

def test_pins_v58_v35():
    assert "filename='style.css', v='61'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v38"' in SW
    assert '"/static/style.css?v=61"' in SW
    assert "v='53'" not in BASE
    assert "ganitra-static-v30" not in SW
