"""Wave 176 (Suraj, 19 Nov 2026): the thinking bubble loses
its passengers.

On his morning live test Suraj circled BOTH figures inside
the "Ganitra is thinking..." bubble — the cream robot on the
left (Wave 160's mini duo) and the jungle boy on the right
(Wave 23's writer) — and asked what they were doing there:
"ye dono yaha kya kar rhe hai, inki jarurat nhi hai"
(neither of them is needed here).

So both injectors (addTypingRobot / addTypingBoy) and their
calls in addTyping() are removed, on BOTH construction paths
(template clone + no-template fallback). The bubble is the
plain Wave 145 indicator again: the localised thinking line
plus the three bouncing dots, sized to its content.

Strictly bubble-scoped:
- the home robot card (Wave 170) and the header buddy are
  untouched, including the buddy's busy face while a typing
  bubble exists (body:has(.bubble.typing) rules stay);
- the robotSvg artwork generator stays (the laughing mini
  on a correct chat-test answer still uses it);
- the boy still writes at the Teach board (showBoyWriter,
  .boy-writer.at-board) — only his typing post is gone,
  together with its CSS (.robot-duo, .bubble.typing
  .robot-host / .boy-host, .boy-writer.in-typing).

Deploy-44 merge note (19 Nov 2026): Wave 181, merged in
this same deploy AFTER this wave, replaced the home robot
card and the header buddy with the rendered mascot on
Suraj's later order and retired the robotSvg generator —
the laugh on a correct chat-test answer is now the
mascot's laugh pop. The two "neighbours" tests below were
updated at merge time to pin those successors; this
wave's own bubble pins are unchanged.

Delivery pins move together, as always: stylesheet ?v=60,
worker cache ganitra-static-v37 (sprite URLs stay ?v=29 —
no sprite file changed).
"""
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W176 Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w176-pass"})
    return c


# --- the injectors are gone ---------------------------------------------

def test_typing_figure_injectors_removed():
    assert "function addTypingRobot" not in INDEX
    assert "function addTypingBoy" not in INDEX
    assert "addTypingRobot(" not in INDEX
    assert "addTypingBoy(" not in INDEX
    assert "robot-duo" not in INDEX
    assert "robot-host" not in INDEX
    # The boy's typing sprite is never built any more.
    assert 'boy.src = "/static/scene-boy.webp' not in INDEX
    assert "boy-writer in-typing" not in INDEX


def test_add_typing_builds_plain_bubble_on_both_paths():
    seg = INDEX[INDEX.index("function addTyping()"):]
    seg = seg[:seg.index("/* ---------- Wave 12")]
    # No figure of any kind is attached inside addTyping.
    assert "boy" not in seg
    assert "robot" not in seg
    assert "appendChild(node)" in seg or "log.appendChild(node)" in seg


# --- the bubble itself: text + dots, nothing else ------------------------

def test_typing_template_is_text_and_dots_only():
    tpl = INDEX[INDEX.index('<template id="typing-template">'):]
    tpl = tpl[:tpl.index("</template>")]
    assert "chat_thinking" in tpl
    assert 'class="dots"' in tpl
    assert tpl.count("<i></i>") == 3
    assert "<svg" not in tpl
    assert "<img" not in tpl
    assert "boy" not in tpl and "robot" not in tpl


def test_typing_css_keeps_dots_drops_figure_rules():
    # Wave 145 dots survive, exactly as ordered.
    assert ".bubble.typing .dots" in CSS
    assert ".bubble.typing .dots i" in CSS
    assert "@keyframes softpulse" in CSS
    # The figure layout rules are gone.
    assert ".robot-duo" not in CSS
    assert ".bubble.typing.robot-host" not in CSS
    assert ".bubble.typing.boy-host" not in CSS
    assert ".boy-writer.in-typing" not in CSS


# --- the neighbours are untouched ----------------------------------------

def test_home_card_and_header_buddy_untouched():
    # Deploy-44 merge update: Wave 181 (merged after this
    # wave) replaced the robot card + header buddy with the
    # rendered mascot in the same seats — the wrapper and
    # the buddy's typing reaction survive in successor form.
    assert "empty-robot-top" in INDEX
    assert "mascot-home" in INDEX
    assert "mascot-circle" in INDEX
    assert "mascot-buddy" in INDEX
    # The header buddy still reacts while a typing bubble
    # exists (Wave 181 tilt rule) — the bubble still exists,
    # it just carries no figures now.
    assert "body:has(.bubble.typing) .mascot-buddy" in CSS


def test_robot_artwork_and_teach_boy_untouched():
    # Deploy-44 merge update: the robotSvg generator was
    # retired by Wave 181; the laughing moment on a correct
    # chat-test answer is now the mascot's laugh pop.
    assert "function robotSvg" not in INDEX
    assert 'showMascotPop("laugh", 1900)' in INDEX
    # The boy still writes at the Teach board.
    assert "function showBoyWriter" in INDEX
    assert 'boyWriter.src = "/static/scene-boy.webp?v=29"' in INDEX
    assert ".boy-writer.at-board" in CSS
    assert ".bubble details.boy-host" in CSS
    assert "@keyframes boy-write" in CSS


def test_served_page_bubble_has_no_figures(client):
    page = client.get("/").get_data(as_text=True)
    assert 'id="typing-template"' in page
    assert "robot-duo" not in page
    assert "addTypingBoy" not in page
    assert "addTypingRobot" not in page
    # Home mascot + header buddy still served (Wave 181's
    # successors of the robot card + buddy).
    assert "mascot-home" in page
    assert "mascot-buddy" in page


# --- delivery pins --------------------------------------------------------

def test_delivery_versions_wave176():
    assert "v='60'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in SW
    assert '"/static/style.css?v=60"' in SW
    assert "v='54'" not in BASE
    assert "ganitra-static-v31" not in SW
