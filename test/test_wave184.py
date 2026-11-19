"""Wave 184 (Suraj, 19 Nov 2026): the voice "Heard:" line is GONE.

After voice dictation, a status line appeared under the
composer:

    Heard: "<transcript>" — now press Solve.

Suraj circled it in his screenshot and ordered it removed:
"ye neeche kyu, nhi hona chahiye naa". The transcript
landing in the composer box is the whole feedback — the
student checks it there and presses send themselves.

What this wave pins:

  * NO Heard line anywhere: the js_voice_heard string is
    removed from i18n (all six languages + the JS key list),
    the chat template no longer renders it, and the served
    chat page carries neither the key nor the text.
  * Voice input itself is UNCHANGED: the mic button, the
    language fallback chain, the spoken-maths normaliser,
    the transcript appended into the composer box with the
    input event + focus — and the other voice notes
    (speak-now prompt, permission denied, could-not-
    understand) all stay exactly as they were. On a
    successful result the note is simply CLEARED, so
    nothing is left sitting under the composer.
  * Pins move together, as always: stylesheet ?v=59,
    worker cache ganitra-static-v36.
"""
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
I18N = (ROOT / "i18n.py").read_text(encoding="utf-8")

SIGNUP = {"name": "W184 User", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
          "password": "w184-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mpl"))
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code == 302
    return c


# --- The Heard line is gone ------------------------------------------

def test_heard_string_removed_from_i18n():
    assert "js_voice_heard" not in I18N
    assert "now press Solve" not in I18N


def test_heard_line_not_rendered_by_template():
    assert "js_voice_heard" not in INDEX
    assert "now press Solve" not in INDEX
    # The old render call itself is gone.
    assert 'say(L.js_voice_heard' not in INDEX


def test_served_chat_page_has_no_heard_line(client):
    page = client.get("/").get_data(as_text=True)
    assert "js_voice_heard" not in page
    assert "now press Solve" not in page
    assert "Heard:" not in page


# --- Voice input itself is unchanged ---------------------------------

def test_transcript_still_lands_in_composer():
    # Spoken maths is normalised, then the text is put in
    # the box (appended after anything already typed), the
    # input event fires and the box keeps focus — the
    # student still presses send themselves.
    assert "text = normalizeSpokenMaths(text);" in INDEX
    assert "box.value = text;" in INDEX
    assert 'box.dispatchEvent(new Event("input"));' in INDEX
    assert "box.focus();" in INDEX


def test_result_clears_the_note_instead_of_posting_heard():
    # After a successful dictation the status note is
    # cleared — no Heard text, and the "Speak now…" prompt
    # is not left sitting under the composer either.
    assert 'say("");' in INDEX


def test_mic_wiring_and_other_voice_notes_unchanged():
    assert 'id="mic-btn"' in INDEX
    assert "SpeechRecognition" in INDEX
    assert "webkitSpeechRecognition" in INDEX
    assert "function speechLangs()" in INDEX
    assert "startRecognition(0)" in INDEX
    # The listening prompt and the two error notes stay.
    assert "say(L.js_voice_speak);" in INDEX
    assert "L.js_voice_denied" in INDEX
    assert "L.js_voice_failed" in INDEX
    assert "say(L.js_voice_no_api);" in INDEX
    assert 'micBtn.style.display = "none"' in INDEX
    # The shared status-note element itself stays — photo
    # and other flows still post their notes there.
    assert 'id="input-note"' in INDEX


def test_served_chat_page_keeps_mic(client):
    page = client.get("/").get_data(as_text=True)
    assert 'id="mic-btn"' in page
    assert "normalizeSpokenMaths" in page


# --- Pins --------------------------------------------------------------

def test_wave184_pins():
    assert "v='59'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v36"' in SW
    assert '"/static/style.css?v=59"' in SW
