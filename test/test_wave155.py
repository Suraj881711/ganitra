"""Wave 155 (Suraj, 18 Nov 2026 — REFINED spec): chat home
greeting row — short greeting + mascot + the day's thought.

Suraj's first thought was "greeting ki jagah thought"; he then
refined it the same morning: the greeting line stays SHORT —
"Hello <name>" — with a smile element beside it, and the
thought goes BELOW the greeting as a small muted line. Plus a
custom cute mascot of his own (drawn in code, no
stock/copyright character, no external image, NOT the logo)
doing small normal activities — wave, blink, smile, gentle
bob — so a student smiles back and the empty state stays
positive. (Wave 160 replaced the original teddy with Suraj's
locked robot character; the mascot-specific assertions below
were updated to the robot reality — the thoughts, greeting,
slot and language pins are unchanged.)
(Wave 161, same day: Suraj moved the robot to a centred line
ABOVE the greeting — .empty-hello is a centred column now;
the layout assertion below was updated to pin exactly that.)

Pins:
  * thought bank — >= 50 thoughts, each with all 3 variants
    (English, Hinglish Roman, Hindi Devanagari), unattributed;
  * slot math — 10 slots of 144 minutes from 00:00 IST, exact
    boundaries, every minute of the day covered;
  * same-day slot thoughts are 10 DISTINCT thoughts; the next
    day's set changes; deterministic (same date + slot -> same
    thought, in every variant);
  * the variant follows the app's existing language machinery
    (session UI language; "hi" -> Devanagari, "hinglish" ->
    Roman, the "en" default and bn/mr/ta/te -> English);
  * the empty state renders: mascot SVG, the SHORT greeting
    "Hello <name>" (not the old long welcome line), and the
    thought line BELOW the greeting;
  * mascot animation classes + keyframes exist, and a
    prefers-reduced-motion rule stills them;
  * Wave 69 stands — no example-question chips anywhere;
  * the 3D scene stays parked (SCENE_ENABLED untouched);
  * CSS changed, so the pins moved WITH it: ?v=52 /
    ganitra-static-v31 everywhere.
"""
import re
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import thoughts

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
APP = (ROOT / "app.py").read_text(encoding="utf-8")

DAY = date(2026, 11, 18)


def _at(day, hour, minute=0):
    return datetime.combine(day, time(hour, minute),
                            tzinfo=thoughts.IST)


# --- The thought bank ----------------------------------------------

def test_bank_size_and_variants():
    assert len(thoughts.THOUGHTS) >= 50
    for entry in thoughts.THOUGHTS:
        assert set(entry) == {"en", "hinglish", "hi"}
        for variant in ("en", "hinglish", "hi"):
            text = entry[variant]
            assert isinstance(text, str) and len(text) >= 20
    ens = [t["en"] for t in thoughts.THOUGHTS]
    assert len(set(ens)) == len(ens)


def test_bank_has_no_attributed_quotes():
    banned = ("gandhi", "einstein", "kalam", "vivekananda",
              "tagore", "nehru", "once said")
    for entry in thoughts.THOUGHTS:
        for text in entry.values():
            assert not any(b in text.lower() for b in banned)


# --- Slot math -------------------------------------------------------

def test_slot_count_and_width():
    assert thoughts.SLOTS_PER_DAY == 10
    assert thoughts.SLOT_MINUTES == 144
    assert thoughts.SLOTS_PER_DAY * thoughts.SLOT_MINUTES == 24 * 60


def test_slot_boundaries():
    cases = [
        ((0, 0), 0), ((2, 23), 0), ((2, 24), 1), ((4, 47), 1),
        ((4, 48), 2), ((7, 12), 3), ((9, 36), 4), ((11, 59), 4),
        ((12, 0), 5), ((14, 24), 6), ((16, 48), 7), ((19, 12), 8),
        ((21, 35), 8), ((21, 36), 9), ((23, 59), 9),
    ]
    for (hour, minute), expected in cases:
        assert thoughts.slot_for(_at(DAY, hour, minute)) == expected


def test_every_minute_of_the_day_has_a_slot():
    seen = set()
    for minute in range(24 * 60):
        moment = _at(DAY, 0, 0) + timedelta(minutes=minute)
        slot = thoughts.slot_for(moment)
        assert 0 <= slot <= 9
        seen.add(slot)
    assert seen == set(range(10))


# --- Daily selection ---------------------------------------------------

def test_same_day_slots_are_distinct():
    selection = thoughts.day_selection(DAY)
    assert len(selection) == 10
    assert len(set(selection)) == 10
    assert all(0 <= i < len(thoughts.THOUGHTS) for i in selection)
    texts = [thoughts.thought_at(_at(DAY, h))["text"]
             for h in (0, 3, 5, 8, 10, 13, 15, 17, 20, 22)]
    assert len(set(texts)) == 10


def test_next_day_set_changes():
    today = thoughts.day_selection(DAY)
    tomorrow = thoughts.day_selection(DAY + timedelta(days=1))
    assert today != tomorrow
    assert set(today) != set(tomorrow)


def test_deterministic_same_date_and_slot():
    moment = _at(DAY, 10, 30)
    first = thoughts.thought_at(moment, "en")
    for _ in range(5):
        assert thoughts.thought_at(moment, "en") == first
    assert thoughts.day_selection(DAY) == thoughts.day_selection(DAY)


def test_variants_come_from_the_same_thought():
    moment = _at(DAY, 10, 30)
    en = thoughts.thought_at(moment, "en")
    hi = thoughts.thought_at(moment, "hi")
    hg = thoughts.thought_at(moment, "hinglish")
    assert en["index"] == hi["index"] == hg["index"]
    assert en["text"] == thoughts.THOUGHTS[en["index"]]["en"]
    assert hi["text"] == thoughts.THOUGHTS[en["index"]]["hi"]
    assert hg["text"] == thoughts.THOUGHTS[en["index"]]["hinglish"]


def test_language_variant_mapping_follows_the_app():
    assert thoughts.variant_for("hi") == "hi"
    assert thoughts.variant_for("hinglish") == "hinglish"
    assert thoughts.variant_for("en") == "en"
    assert thoughts.variant_for("bn") == "en"
    assert thoughts.variant_for("mr") == "en"
    assert thoughts.variant_for(None) == "en"
    assert thoughts.variant_for("") == "en"


def test_thought_text_timezone_conversion():
    # 04:30 UTC = 10:00 IST — same slot, same thought.
    utc_moment = datetime(2026, 11, 18, 4, 30, tzinfo=timezone.utc)
    ist_moment = _at(DAY, 10, 0)
    assert thoughts.thought_text(utc_moment, "en") == \
        thoughts.thought_text(ist_moment, "en")
    naive = datetime(2026, 11, 18, 10, 0)
    assert thoughts.thought_text(naive, "en") == \
        thoughts.thought_text(ist_moment, "en")


# --- Template + wiring ---------------------------------------------------

def test_template_greeting_row_structure():
    # Short greeting in the same .empty-greeting element…
    assert '<h2 class="empty-greeting">{{ saathi_greeting_short }}</h2>' \
        in INDEX
    # …inside the greeting container, after the mascot…
    assert '<div class="empty-hello">' in INDEX
    assert INDEX.index('class="robot"') < \
        INDEX.index("{{ saathi_greeting_short }}")
    # Wave 161 pin update (Suraj, 18 Nov 2026 — "robot ko
    # Muse ki tarah top or beech mai kar do"): the container
    # is no longer a row with the mascot at the greeting's
    # left — it is a CENTRED COLUMN, so the robot stands on
    # its own line above the greeting and both are centred.
    hello_rule = CSS[CSS.index(".empty-hello {"):]
    hello_rule = hello_rule[:hello_rule.index("}")]
    assert "flex-direction: column" in hello_rule
    assert "align-items: center" in hello_rule
    # …and the thought line BELOW the greeting.
    assert '<p class="empty-sub empty-thought">{{ daily_thought }}</p>' \
        in INDEX
    assert INDEX.index("{{ saathi_greeting_short }}") < \
        INDEX.index("{{ daily_thought }}")
    # The long greeting no longer renders in the empty state.
    assert '<h2 class="empty-greeting">{{ saathi_greeting }}</h2>' \
        not in INDEX


def test_robot_svg_is_inline_original_and_logo_free():
    assert '<svg class="robot" viewBox="0 0 100 100"' in INDEX
    assert 'class="robot-arm"' in INDEX
    assert 'class="robot-eyes"' in INDEX
    # The mascot lives in the signed-in empty-state branch only.
    assert INDEX.index('class="robot"') < \
        INDEX.index('id="signin-card-style"')
    # No external image for the mascot, and the logo is untouched.
    robot_block = INDEX[INDEX.index('<svg class="robot"'):
                        INDEX.index("</svg>", INDEX.index(
                            '<svg class="robot"'))]
    assert "http" not in robot_block
    assert "url_for" not in robot_block


def test_robot_animation_css_and_reduced_motion():
    assert ".robot {" in CSS
    assert "animation: robot-bob" in CSS
    assert "animation: robot-blink" in CSS
    assert "animation: robot-wave" in CSS
    assert "@keyframes robot-bob" in CSS
    assert "@keyframes robot-blink" in CSS
    assert "@keyframes robot-wave" in CSS
    assert ".empty-hello {" in CSS
    assert ".empty-thought {" in CSS
    reduced = re.search(
        r"@media \(prefers-reduced-motion: reduce\) \{\s*"
        r"\.robot, \.robot-eyes, \.robot-arm "
        r"\{ animation: none; \}", CSS)
    assert reduced is not None


def test_context_processor_serves_greeting_and_thought():
    assert "import thoughts" in APP
    assert '"daily_thought": thoughts.thought_text(lang=lang)' in APP
    assert '"saathi_greeting_short": _short_greeting(' in APP
    assert "def _short_greeting(" in APP


def test_short_greeting_derivation(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    import app as app_module
    strings = {"saathi_welcome_name":
               "Hello {name}! What shall we solve today?",
               "chat_welcome": "Namaste! Ask me."}
    assert app_module._short_greeting(strings, "Suraj") == "Hello Suraj"
    hindi = {"saathi_welcome_name": "नमस्ते {name}! आज क्या हल करें?",
             "chat_welcome": "नमस्ते!"}
    assert app_module._short_greeting(hindi, "Suraj") == "नमस्ते Suraj"


def test_wave69_chip_absence_still_holds():
    assert 'id="example-chips"' not in INDEX
    assert INDEX.count('class="example-chip"') == 0
    assert 'class="example-chip"' not in INDEX


def test_scene_flag_untouched():
    assert "SCENE_ENABLED = False" in APP
    assert "scene_enabled" in INDEX  # the parked block stays as-is


def test_pins_moved_with_the_css():
    assert "v='54'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v31"' in SW
    assert '"/static/style.css?v=54"' in SW


# --- The page itself -------------------------------------------------------

def _signed_in_client(tmp_path, monkeypatch, name="W155 Tester"):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w155-test-pass"})
    return client


def test_home_shows_robot_short_greeting_and_thought(
        tmp_path, monkeypatch):
    client = _signed_in_client(tmp_path, monkeypatch)
    page = client.get("/").get_data(as_text=True)
    # Mascot renders on the empty state.
    assert '<svg class="robot"' in page
    assert 'class="robot-arm"' in page
    assert 'class="robot-eyes"' in page
    # Short greeting — "Hello <name>", and NOT the long old line.
    assert 'class="empty-greeting">Hello W155 Tester</h2>' in page
    assert "What shall we solve today?" not in page
    # The thought line sits BELOW the greeting and carries a
    # thought from the bank.
    assert page.index("Hello W155 Tester") < \
        page.index('class="empty-sub empty-thought"')
    match = re.search(
        r'class="empty-sub empty-thought">([^<]+)</p>', page)
    assert match is not None
    assert match.group(1).strip() in \
        {t["en"] for t in thoughts.THOUGHTS}


def test_home_greeting_and_thought_follow_session_language(
        tmp_path, monkeypatch):
    client = _signed_in_client(tmp_path, monkeypatch,
                               name="W155 Hindi Tester")
    with client.session_transaction() as sess:
        sess["lang"] = "hi"
    page = client.get("/").get_data(as_text=True)
    assert 'class="empty-greeting">नमस्ते W155 Hindi Tester</h2>' in page
    match = re.search(
        r'class="empty-sub empty-thought">([^<]+)</p>', page)
    assert match is not None
    assert match.group(1).strip() in \
        {t["hi"] for t in thoughts.THOUGHTS}
