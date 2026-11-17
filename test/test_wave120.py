"""Wave 120: the answer card loses its heading, its play sign,
and its standalone Full Solution link (Suraj, 17 Nov 2026).

Suraj's three orders, looking at the card:
1. "Step by step solution hai usse hata di" — the
   "STEP-BY-STEP SOLUTION" heading (and its EN/HI/Hinglish
   variants) is REMOVED from the card. The solving lines
   themselves stay, unlabelled, exactly as his settled
   no-labels design always wanted.
2. "Speaker or video ka jo icon hai woh ek hi kaam krta hai
   toh dono mai se ek hi rakho" — the speaker (Listen) and
   the play (Teach) signs both drove the SAME job: speaking
   the teacher narration of the answer aloud (both build
   their voice track from narrateSolution(...) over
   speechSynthesis; Teach additionally revealed steps on the
   board while it spoke). Only the speaker stays; the play
   sign is out of the row. Teach's playback machinery stays
   in the page, dormant and unreachable — like the parked
   3D scene — it is not deleted.
3. "Full solution kaa option 3 dot mai hi add kar do" — the
   standalone "Full solution page →" link under the card is
   GONE; the ••• (More) panel now rides on EVERY answer card
   and its FIRST item is the Full Solution page — the very
   same POST /solve form (question in a hidden field) the
   link used to submit. Alternate methods still list below
   it, under their heading, when they exist.

Runtime behaviour of the JS card (icon row contents, ••• on a
plain answer, the form's action + hidden question, the empty
hidden <summary>) is pinned live in jsdom by
test_answer_sequence.py (scenarios s1/s2) and
test_wave25_fixes.py / test_wave29_fixes.py; the download
text is pinned by test_wave46_fixes.py. This file pins what
those do not: the i18n/API removal, the template sources,
and the SERVER-rendered pages (full-solution + print) in
English and Hindi.
"""
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
INDEX = (TEMPLATES / "index.html").read_text(encoding="utf-8")
ANSWER = (TEMPLATES / "answer.html").read_text(encoding="utf-8")
PRINT = (TEMPLATES / "print.html").read_text(encoding="utf-8")
I18N_SRC = (ROOT / "i18n.py").read_text(encoding="utf-8")

SIGNUP = {"name": "W120 Tester", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
          "password": "w120-test-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code in (200, 302)
    return c


# --- 1. The heading is gone from the language machinery ------

def test_steps_heading_key_removed_from_every_language():
    import i18n
    for code, strings in i18n.STRINGS.items():
        assert "steps_heading" not in strings, code
    # And it is not hiding in the source as a literal key.
    assert '"steps_heading":' not in I18N_SRC


def test_steps_heading_not_shipped_in_language_switch_ui():
    # api._lang_fields ships _UI_EXTRA_KEYS in the `ui` payload
    # on a language switch; the heading must not ride along.
    import api
    assert "steps_heading" not in api._UI_EXTRA_KEYS


def test_templates_no_longer_render_the_heading():
    assert "{{ t.steps_heading }}" not in ANSWER
    assert "{{ t.steps_heading }}" not in PRINT
    # The chat page no longer seeds CHAT.steps from it either.
    assert "t.steps_heading" not in INDEX
    assert "ui.steps_heading" not in INDEX
    assert "steps_heading" not in INDEX


def test_js_card_renders_an_empty_hidden_summary():
    # A <details> without a <summary> grows a UA-default
    # "Details" label, so the element stays — rendering
    # nothing at all.
    assert 'sum.textContent = "";' in INDEX
    assert 'sum.style.display = "none";' in INDEX


# --- 2. Play sign out, speaker stays --------------------------

def test_teach_button_is_never_created():
    assert 'teachBtn = document.createElement("button");' not in INDEX
    assert 'setAttribute("data-role", "teach");' not in INDEX
    assert 'teachBtn.className = "method-chip act-btn teach-btn";' \
        not in INDEX


def test_listen_button_still_built_from_the_same_narration():
    assert "makeListenButton(parts," in INDEX
    assert 'listenBtn.dataset.action = "listen";' in INDEX
    # The Listen parts are the teacher narration of the
    # solution — the same narrateSolution(...) track the
    # removed Teach playback spoke. One voice sign, one job.
    assert "narrateSolution(displaySteps," in INDEX


def test_teach_machinery_stays_dormant_not_deleted():
    # Suraj removed the SIGN, not the feature: the playback
    # machinery remains in the page, unreachable (no button
    # calls it), exactly like the parked 3D scene.
    assert "function startTeachPlayback()" in INDEX
    assert "function stopTeachPlayback()" in INDEX
    assert "var teachBtn = null;" in INDEX


# --- 3. Full Solution inside the ••• panel --------------------

def test_full_solution_form_appended_to_panel_not_wrap():
    assert "wrap.appendChild(full);" not in INDEX
    assert INDEX.count("methodsPanel.appendChild(full);") == 1


def test_full_solution_form_is_the_old_links_post():
    # Same form the standalone link submitted: POST /solve
    # with the question in a hidden field, as a menu row.
    assert 'full.method = "post";' in INDEX
    assert 'full.action = "/solve";' in INDEX
    assert 'fullHidden.name = "question";' in INDEX
    assert 'fullHidden.value = question;' in INDEX
    assert 'fullBtn.className = "method-row-btn";' in INDEX
    # The label is the link's own text, trailing arrow off.
    assert "CHAT.fullSolution.replace(" in INDEX


def test_full_solution_is_the_panels_first_item():
    full_at = INDEX.index("methodsPanel.appendChild(full);")
    heading_at = INDEX.index("methodsPanel.appendChild(mh);")
    assert full_at < heading_at


def test_methods_panel_built_unconditionally():
    # The ••• chip + panel are built for EVERY card now (the
    # old `if (methods.length)` guard around them is gone);
    # the guard survives only around the methods heading +
    # rows inside the panel.
    m = re.search(r"var methodsPanel = null;\s*\{\s*"
                  r"var chip = document\.createElement", INDEX)
    assert m is not None
    assert 'chip.dataset.action = "methods";' in INDEX
    # Panel starts hidden, chip toggles it (unchanged).
    assert "methodsPanel.hidden = true;" in INDEX


# --- 4. Server-rendered pages: no heading, steps stay ---------

def test_full_solution_page_english_no_heading(client):
    r = client.post("/solve", data={"question": "Solve 2x + 3 = 7"})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Step-by-step solution" not in body
    assert 'id="steps-list"' in body       # the steps stay
    assert "x = 2" in body                 # the answer stays


def test_full_solution_page_hindi_no_heading(client):
    r = client.get("/set-lang/hi")
    assert r.status_code == 302
    r = client.post("/solve", data={"question": "x^2-5x+6=0"})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # The HI heading is gone. (The bare phrase survives in
    # the site tagline inside <title> — "गणित, चरण-दर-चरण हल
    # किया गया" — a different element, not the card heading,
    # and not Wave 120's to change.)
    assert "<h2>चरण-दर-चरण हल</h2>" not in body
    assert "Step-by-step solution" not in body
    assert 'id="steps-list"' in body
    assert "x = 2, x = 3" in body


def test_print_page_no_heading(client):
    r = client.post("/solve", data={"question": "Solve 2x + 3 = 7"})
    assert r.status_code == 200
    r = client.get("/solution/print")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "Step-by-step solution" not in body
    assert "x = 2" in body


def test_chat_page_no_longer_seeds_the_heading(client):
    body = client.get("/").get_data(as_text=True)
    # The old seed rendered as: steps: "Step-by-step solution"
    assert not re.search(r'steps:\s*"Step-by-step', body)
    assert "steps_heading" not in body
