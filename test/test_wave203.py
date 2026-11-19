"""Wave 203: photo-path small-mistake fixes (photo audit,
20 Nov 2026).

The audit found the vision skeleton right — transcribe-only,
composer confirmation before any solve, own quota bucket —
with the mistake surface exactly where Suraj pointed:

1. A readable NON-maths photo collapsed into the same
   NO_QUESTION outcome as a blurry one, so the student was
   told "No question found in the photo — send a clear photo
   again" (factually wrong; an endless re-send loop) instead
   of the maths-only one-liner. Fix: a distinct NOT_MATHS
   vision outcome -> code "not_maths" + the typed guard's
   own line (fallback._NONMATHS_LINES) in the read
   question's flavour.
2. The vision path had NO uncertainty channel: a confidently
   misread blurred digit reached the composer with only the
   generic "please check" line — photofix's one-line
   confirmation could never fire on a clean-looking vision
   read. Fix: the model flags unsure spans on a trailing
   UNSURE: line; the server strips it and serves photofix's
   ONE confirmation line naming the first flagged span.
   Nothing is ever solved on the flagged guess (the route
   still only prefills the composer).
3. VisionFailed (transport/timeout — ~1 in 4 live calls in
   the audit) dropped straight to the weaker OCR chain.
   Fix: ONE same-model retry; quota and clean outcomes are
   never retried.
4. A second question in the photo was dropped silently
   (first-question-only design). Fix: a MORE: trailer earns
   one short notice line (system text: English/Hinglish
   Roman only).
5. /photo-vision ran photofix on normalize_ocr_text(text),
   contradicting gemini_vision.py's own contract (the OCR
   normaliser never rewrites vision text). Fix: photofix
   reads the RAW transcription.

NO real API calls: the Gemini HTTP layer is mocked at
gemini_vision._post_json, exactly as in test_wave144.
"""
import io
import os
import re
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fallback  # noqa: E402
import gemini_vision  # noqa: E402
import photofix  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"wave203-fake-png-body"
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")

ROOT = os.path.join(os.path.dirname(__file__), "..")
with open(os.path.join(ROOT, "templates", "index.html"),
          encoding="utf-8") as fh:
    INDEX = fh.read()


# ------------------------------------------------------------ fixtures

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mpl"))
    from app import create_app
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _signup(client):
    r = client.post("/signup", data={
        "name": "W203 Photo Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w203-photo-pass"})
    assert r.status_code in (200, 302)


def _post_vision(client, data=PNG, name="photo.png"):
    return client.post(
        "/photo-vision",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data")


def _gemini_reply(text):
    return {"candidates": [{
        "content": {"parts": [{"text": text}]},
        "finishReason": "STOP"}]}


@pytest.fixture()
def vision_http(monkeypatch):
    """Mock the Gemini HTTP layer. `state["reply"]` is a
    response dict or an exception; `state["script"]` (a list)
    overrides it per call — each entry is popped in order and
    the last one repeats."""
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "w203-test-key")
    calls = []
    state = {"reply": _gemini_reply("Find the value of 3/4 + 1/2."),
             "script": None}

    def fake_post(url, payload, api_key, timeout):
        calls.append({"url": url, "payload": payload,
                      "api_key": api_key, "timeout": timeout})
        if state["script"]:
            item = state["script"].pop(0) \
                if len(state["script"]) > 1 else state["script"][0]
        else:
            item = state["reply"]
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(gemini_vision, "_post_json", fake_post)
    return {"calls": calls, "state": state}


def _set_reply(vision_http, text):
    vision_http["state"]["reply"] = _gemini_reply(text)
    vision_http["state"]["script"] = None


# ------------------------------------------- fix 1: NOT_MATHS split

def test_not_maths_english_gets_the_typed_guard_line(client,
                                                     vision_http):
    _set_reply(vision_http,
               "NOT_MATHS\nWhat is the capital of France?")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["ok"] is False
    assert d["code"] == "not_maths"
    # The very line the typed guard serves — never the
    # photo not-found line.
    assert d["message"] == fallback._NONMATHS_LINES["en"]
    assert "No question found" not in d["message"]


def test_not_maths_devanagari_gets_devanagari_line(client,
                                                   vision_http):
    read = "फ्रांस की राजधानी क्या है?"
    _set_reply(vision_http, "NOT_MATHS\n" + read)
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["code"] == "not_maths"
    assert d["message"] == fallback._NONMATHS_LINES["dev"]
    assert d["message"] == fallback.nonmaths_line_for(read)


def test_not_maths_roman_gets_roman_line(client, vision_http):
    read = "France ki rajdhani kya hai?"
    _set_reply(vision_http, "NOT_MATHS\n" + read)
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["code"] == "not_maths"
    assert d["message"] == fallback.nonmaths_line_for(read)
    assert d["message"] != fallback._NONMATHS_LINES["en"]


def test_no_question_stays_the_not_found_outcome(client,
                                                 vision_http):
    """Genuinely unreadable / empty photos keep the existing
    no_question code and payload shape, byte for byte."""
    _set_reply(vision_http, "NO_QUESTION")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d == {"ok": False, "code": "no_question"}


def test_not_maths_module_outcome(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "k")
    monkeypatch.setattr(
        gemini_vision, "_post_json",
        lambda *a, **k: _gemini_reply(
            "NOT_MATHS\nWhat is the capital of France?"))
    out = gemini_vision.transcribe_detailed(PNG, "image/png")
    assert out["outcome"] == "not_maths"
    assert out["read"] == "What is the capital of France?"
    assert out["text"] is None
    # The Wave-144 wrapper contract is unchanged: no maths
    # text in the photo -> None.
    assert gemini_vision.transcribe_image(PNG, "image/png") \
        is None


# ------------------------------------- fix 2: uncertainty channel

TRAIN_CLEAN = ("A train travels 240 km in 4 hours. "
               "Find its speed.")


def test_unsure_flag_earns_one_confirmation_line(client,
                                                 vision_http):
    """The model flags the 240 it could not read surely: the
    composer still gets the transcription (never a solve),
    plus ONE line naming the flagged span."""
    assert photofix.analyse(TRAIN_CLEAN)["confirm"] is None
    _set_reply(vision_http, TRAIN_CLEAN + "\nUNSURE: 240")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["kind"] == "text"
    assert d["text"] == TRAIN_CLEAN          # trailer stripped
    assert d["prefill"] == TRAIN_CLEAN       # composer, not a solve
    assert d["confirm"] == photofix.unsure_confirm(
        TRAIN_CLEAN, ["240"])
    assert "240" in d["confirm"]
    assert set(d) == {"kind", "text", "prefill", "confirm",
                      "backend"}


def test_unsure_line_is_in_the_reads_language(client,
                                              vision_http):
    hindi = ("एक ट्रेन 240 किमी की दूरी 4 घंटे में तय करती है। "
             "उसकी गति ज्ञात कीजिए।")
    _set_reply(vision_http, hindi + "\nUNSURE: 240")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["kind"] == "text"
    assert d["confirm"] == photofix.unsure_confirm(hindi, ["240"])
    assert "240" in d["confirm"]


def test_photofix_confirm_wins_over_unsure_line(client,
                                                vision_http):
    """When photofix itself finds an unclear slot, ITS
    confirmation (which names the alternative) is the one
    line served — never two lines."""
    raw = ("A train runs at 60 km/h or 80 km/h for 5 hours. "
           "Find the distance covered.")
    fixed = photofix.analyse(raw)
    assert fixed is not None and fixed["confirm"]
    _set_reply(vision_http, raw + "\nUNSURE: 60")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["prefill"] == fixed["question"]
    assert d["confirm"] == fixed["confirm"]


def test_unsure_parse_strips_trailer_and_lists_spans(
        monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "k")
    monkeypatch.setattr(
        gemini_vision, "_post_json",
        lambda *a, **k: _gemini_reply(
            TRAIN_CLEAN + "\nUNSURE: 240, 4"))
    out = gemini_vision.transcribe_detailed(PNG, "image/png")
    assert out["outcome"] == "text"
    assert out["text"] == TRAIN_CLEAN
    assert out["unsure"] == ["240", "4"]
    assert out["more"] is False


def test_no_flag_no_confirmation_behaviour_unchanged(client,
                                                     vision_http):
    _set_reply(vision_http, TRAIN_CLEAN)
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["confirm"] is None
    assert "notice" not in d


def test_unsure_confirm_helper_contract():
    assert photofix.unsure_confirm(TRAIN_CLEAN, []) is None
    assert photofix.unsure_confirm(TRAIN_CLEAN, None) is None
    line = photofix.unsure_confirm(TRAIN_CLEAN, ["60", "80"])
    assert "60" in line and "80" not in line  # first span only


# ------------------------------------------------ fix 3: one retry

def test_transport_failure_retried_once_then_succeeds(
        client, vision_http):
    vision_http["state"]["script"] = [
        urllib.error.URLError("down"),
        _gemini_reply("Find the value of 3/4 + 1/2.")]
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["kind"] == "text"
    assert len(vision_http["calls"]) == 2


def test_transport_failure_twice_is_vision_failed(client,
                                                  vision_http):
    vision_http["state"]["reply"] = urllib.error.URLError("down")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["code"] == "vision_failed"
    # Exactly one retry — not a chain.
    assert len(vision_http["calls"]) == 2


def test_quota_is_never_retried(client, vision_http):
    vision_http["state"]["reply"] = urllib.error.HTTPError(
        "https://example.invalid", 429, "quota", None, None)
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["code"] == "vision_quota"
    assert len(vision_http["calls"]) == 1


def test_clean_no_question_is_never_retried(client, vision_http):
    _set_reply(vision_http, "NO_QUESTION")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["code"] == "no_question"
    assert len(vision_http["calls"]) == 1


def test_not_maths_is_never_retried(client, vision_http):
    _set_reply(vision_http, "NOT_MATHS\nWhat is the capital "
                            "of France?")
    _signup(client)
    _post_vision(client)
    assert len(vision_http["calls"]) == 1


# --------------------------------------- fix 4: second-question notice

def test_second_question_earns_the_notice(client, vision_http):
    _set_reply(vision_http, "1) 12 + 8 = ?\nMORE: YES")
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["kind"] == "text"
    assert d["text"] == "1) 12 + 8 = ?"       # trailer stripped
    assert "notice" in d
    assert "first" in d["notice"]
    assert "separately" in d["notice"]


def test_notice_for_hinglish_read_is_hinglish(client, vision_http):
    _set_reply(vision_http,
               "ram ke paas 15 aam hai, kitne bache?\nMORE: YES")
    _signup(client)
    d = _post_vision(client).get_json()
    assert "pehla" in d["notice"]
    assert not _DEVANAGARI.search(d["notice"])


def test_notice_for_devanagari_read_is_never_devanagari(
        client, vision_http):
    """System-text rule: even for a Devanagari question the
    fixed notice is Hinglish (Roman), never Devanagari."""
    _set_reply(vision_http,
               "राम के पास 15 आम हैं, कितने बचे?\nMORE: YES")
    _signup(client)
    d = _post_vision(client).get_json()
    assert "notice" in d
    assert not _DEVANAGARI.search(d["notice"])
    assert "pehla" in d["notice"]


def test_more_parse_module_level(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "k")
    monkeypatch.setattr(
        gemini_vision, "_post_json",
        lambda *a, **k: _gemini_reply("12 + 8 = ?\nMORE: YES"))
    out = gemini_vision.transcribe_detailed(PNG, "image/png")
    assert out["outcome"] == "text"
    assert out["text"] == "12 + 8 = ?"
    assert out["more"] is True
    assert out["unsure"] == []


# ------------------------------------- fix 5: photofix on the raw read

def test_photofix_sees_the_raw_transcription(client, vision_http,
                                             monkeypatch):
    """gemini_vision's contract: the OCR normaliser never
    rewrites vision text. Spy on photofix.analyse — the route
    must hand it the transcription exactly as read (the ÷ and
    × below are characters normalize_ocr_text would rewrite
    to / and *)."""
    raw = "Simplify: (3/4) ÷ (9/8) + 2^2 × 3"
    seen = []
    real_analyse = photofix.analyse

    def spy(text):
        seen.append(text)
        return real_analyse(text)

    monkeypatch.setattr(photofix, "analyse", spy)
    _set_reply(vision_http, raw)
    _signup(client)
    d = _post_vision(client).get_json()
    assert d["kind"] == "text"
    assert seen == [raw]


# ------------------------------------------------- clean read + wiring

def test_clean_read_payload_shape_unchanged(client, vision_http):
    _set_reply(vision_http, "Find the value of 3/4 + 1/2.")
    _signup(client)
    d = _post_vision(client).get_json()
    assert set(d) == {"kind", "text", "prefill", "confirm",
                      "backend"}
    assert d["confirm"] is None


def test_prompt_carries_the_wave203_channels():
    assert "NOT_MATHS" in gemini_vision._PROMPT
    assert "UNSURE:" in gemini_vision._PROMPT
    assert "MORE: YES" in gemini_vision._PROMPT
    # The Wave-144 pins survive.
    assert "do NOT solve" in gemini_vision._PROMPT
    assert "NO_QUESTION" in gemini_vision._PROMPT


def test_chat_page_wires_not_maths_and_notice():
    assert 'd.code === "not_maths"' in INDEX
    assert "d.message" in INDEX
    assert "d.notice" in INDEX
    # The not-found line still serves the no_question code.
    assert 'd.code === "no_question"' in INDEX
