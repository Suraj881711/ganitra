"""Wave 168: the home robot moves to the very top.

Suraj, 18 Nov 2026 (late night, reacting to the Deploy-36
home screenshot): "Robot ko upar rakho bilkul" — refined:
"Jo menu wali line hai naa, uske neeche rakhana hai" (put
it right below the menu/header line) and "Muse hai
jaise" (like Muse's character at the top).

So the Wave 160/161 home robot no longer rides inside the
vertically centred empty-state block (.chat-empty, below
the logo, inside .empty-hello). Its SVG — moved verbatim,
same character, same animations — now stands in a new
.empty-robot-top wrapper at the very top of .chat-shell,
immediately below the header/menu line, top-centred. The
logo, greeting and thought stay in the centred block
below, in their existing order. It still renders only for
a named student ({% if saathi_name %}), and CSS hides it
the moment a chat starts (body.chat-active), when the
Wave 161 header buddy takes over — the two never show
together. Pure placement: no artwork, colour, animation,
greeting, thought or composer change.

Pins moved with the CSS: ?v=60 / ganitra-static-v37.

Wave 181 update (19 Nov 2026): the SVG robot that stood in
the wrapper was replaced by the new rendered mascot in a
white circle (.mascot-home / .mascot-circle). The wrapper,
its top placement, the named-student gate and the
hide-on-chat-start rule are exactly as this wave built
them; only the artwork assertions below moved.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def _rule(selector):
    block = CSS[CSS.index(selector + " {"):]
    return block[:block.index("}")]


# --- 1. The robot is the FIRST element of the empty state -------------

def test_robot_block_at_top_of_chat_shell():
    assert '<div class="empty-robot-top" aria-hidden="true">' in INDEX
    top = INDEX.index('<div class="empty-robot-top"')
    # …inside the chat shell, before the scrolling thread…
    assert INDEX.index('<div class="chat-shell">') < top
    assert top < INDEX.index('<div class="chat-scroll"')
    # …and before the empty state itself.
    assert top < INDEX.index('id="chat-empty"')


def test_robot_before_logo_greeting_and_thought():
    robot = INDEX.index('class="mascot-circle"')
    assert robot < INDEX.index('class="empty-logo"')
    assert robot < INDEX.index('id="scene-logo"')
    assert robot < INDEX.index("{{ saathi_greeting_short }}")
    assert robot < INDEX.index("{{ daily_thought }}")


def test_robot_no_longer_inside_empty_hello():
    hello = INDEX[INDEX.index('<div class="empty-hello">'):]
    hello = hello[:hello.index("</div>")]
    assert 'class="mascot-circle"' not in hello
    # The greeting itself still lives there.
    assert "{{ saathi_greeting_short }}" in hello


# --- 2. Top placement is carried by the wrapper's CSS -----------------

def test_top_placement_rule():
    rule = _rule(".empty-robot-top")
    assert "display: flex" in rule
    assert "justify-content: center" in rule
    assert "padding-top:" in rule  # the small top margin under the header line
    assert "flex: none" in rule


def test_top_robot_hides_when_chat_starts():
    # hideEmpty() puts chat-active on the body as it removes
    # the empty state; the header buddy takes over from there.
    assert "body.chat-active .empty-robot-top { display: none; }" in CSS
    assert 'classList.add("chat-active")' in INDEX


# --- 3. Nothing else about the robot changed --------------------------

def test_robot_still_gated_on_named_student():
    shell = INDEX.index('<div class="chat-shell">')
    top = INDEX.index('<div class="empty-robot-top"')
    assert "{% if saathi_name %}" in INDEX[shell:top]


def test_mascot_block_is_the_new_robot():
    # Wave 181: inside the top wrapper stands the new
    # rendered mascot — four local pose images in the white
    # circle, no SVG artwork at all.
    # Wave 197 (Suraj, 20 Nov): name/motion removed on his
    # order — the circle now holds ONLY the wave portrait
    # (the laugh/kiss portraits ride the .mascot-pop
    # overlay below, outside this block). The slice used
    # to end at the name plate; it now ends at the close
    # of the .mascot-home block.
    home = INDEX[INDEX.index('<div class="mascot-home"'):]
    home = home[:home.index("{% endif %}")]
    assert "robot-wave.webp" in home
    for name in ("robot-think.webp", "robot-laugh.webp",
                 "robot-kiss.webp"):
        assert name not in home
    assert "<svg" not in home
    assert "http" not in home
