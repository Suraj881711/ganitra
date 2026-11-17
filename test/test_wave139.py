"""Wave 139 (Suraj, 17 Nov 2026): SILENT language switch +
English/Hinglish-only system messages.

Part 1 — his words: "ye dikhana nhi chahiye, automatic hona
chahiye, yaa chat par maange jabhi ussi hisab se karana hai."
The Wave-9 "language changed" announcement (the dashed pill
"🌐 भाषा हिन्दी में बदल गई है — किसी भी भाषा में पूछते रहो!")
must NEVER be shown. The language still switches automatically
(and on an explicit in-chat request, Wave 107) — it just does so
silently: no banner, toast or pill, ever. Removed end to end:
the i18n `lang_switched_toast` strings, the api.py `lang_notice`
response field, the client bubble render in templates/index.html
and its `.bubble.lang-note` CSS.

Part 2 — his follow-up order the same evening: fixed SYSTEM/UI
messages (offline notice, error toasts, connection/retry
notices, status lines, form errors) render in English or
Hinglish (Roman) ONLY — never Devanagari — whatever language
the conversation is in. Answer content is untouched: answers,
steps and explanations still follow the student's language.
i18n.SYSTEM_MESSAGE_KEYS are pinned to their English text for
every language, in get_strings and in STRINGS itself.
"""
import re
from pathlib import Path

import pytest

import i18n
from i18n import STRINGS, SYSTEM_MESSAGE_KEYS, get_strings

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

DEVANAGARI = ("ऀ", "ॿ")
# Devanagari, Bengali, Tamil, Telugu script ranges.
INDIC_SCRIPTS = re.compile(
    "[\u0900-\u097F\u0980-\u09FF\u0B80-\u0BFF\u0C00-\u0C7F]")


def _has_devanagari(text):
    return any(DEVANAGARI[0] <= ch <= DEVANAGARI[1]
               for ch in str(text or ""))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _ask(client, question):
    return client.post(
        "/api/solve", json={"question": question}).get_json()


TRIANGLE_EN = "What is the sum of angles of a triangle?"
TRIANGLE_HI = "त्रिभुज के कोणों का योग कितना होता है?"
OFFLINE_EN = ("Internet is not available right now — "
              "please check your connection and try again.")
OFFLINE_HI_OLD = "अभी इंटरनेट नहीं है"


# --- Part 1: the announcement is gone, the switch is not ------

def test_toast_string_removed_from_all_languages():
    for code in i18n.SUPPORTED_LANGS:
        assert "lang_switched_toast" not in STRINGS[code], code
        assert "lang_switched_toast" not in get_strings(code), code


def test_i18n_key_sets_still_complete():
    base = set(STRINGS["en"])
    for code in i18n.SUPPORTED_LANGS:
        assert set(STRINGS[code]) == base, code


def test_client_has_no_notice_bubble():
    assert "lang_notice" not in INDEX
    assert "lang-note" not in INDEX
    assert ".bubble.lang-note" not in CSS


def test_auto_switch_is_silent(client):
    body = _ask(client, TRIANGLE_HI)
    assert body["ok"] is True
    assert body["language_switched"] is True
    assert body["language"] == "hi"
    assert "lang_notice" not in body
    # behaviour preserved: the answer itself is in Hindi
    assert _has_devanagari(body["explanation"])


def test_explicit_request_switch_is_silent(client):
    # Wave 107 end-to-end case: English question, Hindi requested.
    body = _ask(client, TRIANGLE_EN + " Answer in Hindi")
    assert body["ok"] is True
    assert body["language"] == "hi"
    assert body["language_switched"] is True
    assert body["result"]["answer"] == "180°"
    assert _has_devanagari(body["explanation"])
    assert _has_devanagari(body["advice"])
    assert "lang_notice" not in body
    # the ui re-skin map still arrives, without the toast string
    assert "lang_switched_toast" not in (body.get("ui") or {})


def test_no_switch_no_notice_either(client):
    body = _ask(client, TRIANGLE_EN)
    assert body["language_switched"] is False
    assert "lang_notice" not in body


# --- Part 2: system messages are English/Hinglish only ---------

def test_system_keys_pinned_for_every_language():
    canonical = STRINGS["en"]
    for code in i18n.SUPPORTED_LANGS:
        shipped = get_strings(code)
        for key in SYSTEM_MESSAGE_KEYS:
            assert shipped[key] == canonical[key], (code, key)
            assert not INDIC_SCRIPTS.search(shipped[key]), (code, key)
            # the shipped tables themselves are pinned too
            assert STRINGS[code][key] == canonical[key], (code, key)


def test_offline_note_is_the_english_one():
    for code in i18n.SUPPORTED_LANGS:
        assert get_strings(code)["chat_offline_note"] == OFFLINE_EN
    assert OFFLINE_HI_OLD not in get_strings("hi")["chat_offline_note"]


def test_hindi_conversation_keeps_hindi_answers(client):
    body = _ask(client, TRIANGLE_HI)
    assert body["language"] == "hi"
    assert _has_devanagari(body["explanation"])
    assert _has_devanagari(body["advice"])
    # ...while the system strings riding the same response are EN
    ui = body.get("ui") or {}
    assert ui["chat_offline_note"] == OFFLINE_EN
    assert ui["chat_waking_note"] == STRINGS["en"]["chat_waking_note"]
    assert ui["error_heading"] == STRINGS["en"]["error_heading"]
    assert not _has_devanagari(ui["chat_error"])


def test_chat_page_renders_english_offline_note_in_hindi(client):
    # Signed in, so GET / renders the real chat page (with the
    # CHAT string block) rather than the sign-in gate.
    r = client.post("/signup", data={
        "name": "W139 Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w139-test-pass"})
    assert r.status_code in (200, 302)
    _ask(client, TRIANGLE_HI)  # session language now Hindi
    home = client.get("/").get_data(as_text=True)
    # tojson escapes the em dash, so assert on the ASCII fragment
    assert "Internet is not available right now" in home
    assert OFFLINE_HI_OLD not in home
