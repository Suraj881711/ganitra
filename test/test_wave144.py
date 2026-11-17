"""Wave 144: the real photo + file/PDF system.

What exists before this wave (Waves 27/28/36/83/126/137): a
photo is read by Tesseract.js in the browser (the server OCR
backend in ocr.py has no engine on the free host), weak reads
land in the composer via the Wave 137 reconstruction, and
files ride /file-extract (PDF text layer server-side, .docx,
.txt) straight into an auto-solve.

The phone diagnosis (full version in ganitra-wave144-notes.md):
the untouched multi-MB camera photo is POSTed to /photo-ocr
FIRST, its 2 MB cap answers "too_large", and the script
STOPS — the browser flow that could have read the photo
locally never runs. Even a small photo then waits on the
Tesseract.js CDN engine + eng/hin traineddata and a heavy
WASM read on the phone CPU. PDFs from scanner apps hit the
same 2 MB cap, and extracted document text was auto-solved
whole, unseen.

What this wave adds:

- gemini_vision.py + POST /photo-vision — Gemini vision
  TRANSCRIBES the photographed question (model
  gemini-3.1-flash-lite, its own free-quota bucket, never
  the answer fallback's). It never solves. The transcription
  lands in the editable composer under the Wave 137
  discipline (reconstruction + at most one confirmation line
  when a slot is unclear); any vision failure degrades
  silently to the old chain. Nothing is stored: the image
  bytes live in memory for the request only.
- The chat script tries vision first (after a canvas
  downscale to ~1600 px JPEG), reads PDFs in the browser
  with pdf.js (lazy CDN) into the composer, reads .txt
  straight into the composer, and no longer lets the server
  2 MB cap dead-end a photo the browser can read locally.
- New system strings (js_file_check / js_pdf_reading /
  js_pdf_unavailable) are English/Hinglish only in every
  language — Suraj's standing system-message rule.

NO real API calls happen in these tests: the Gemini HTTP
layer is mocked at gemini_vision._post_json.
"""
import io
import os
import re
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gemini_fallback  # noqa: E402
import gemini_vision  # noqa: E402
import i18n  # noqa: E402
import photofix  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"wave144-fake-png-body"
JPEG = b"\xff\xd8\xff\xe0" + b"wave144-fake-jpeg-body"
GIF = b"GIF89a" + b"wave144-fake-gif-body"
WEBP = b"RIFF\x1a\x00\x00\x00WEBP" + b"wave144-fake-webp"


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
        "name": "W144 Photo Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w144-photo-pass"})
    assert r.status_code in (200, 302)


def _post_vision(client, data, name="photo.png"):
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
    """Mock the Gemini HTTP layer; returns the call log.
    `state["reply"]` is either a response dict or an
    exception instance to raise."""
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "w144-test-key")
    calls = []
    state = {"reply": _gemini_reply("Find the value of 3/4 + 1/2.")}

    def fake_post(url, payload, api_key, timeout):
        calls.append({"url": url, "payload": payload,
                      "api_key": api_key, "timeout": timeout})
        if isinstance(state["reply"], Exception):
            raise state["reply"]
        return state["reply"]

    monkeypatch.setattr(gemini_vision, "_post_json", fake_post)
    return {"calls": calls, "state": state}


# ------------------------------------------------------- route shape

def test_vision_no_file(client):
    _signup(client)
    r = client.post("/photo-vision", data={},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert r.get_json()["code"] == "no_file"


def test_vision_anonymous_parity_with_photo_ocr(client):
    """Whatever the app's auth posture is, /photo-vision
    matches /photo-ocr exactly (both are upload reads)."""
    a = client.post("/photo-vision", data={},
                    content_type="multipart/form-data")
    b = client.post("/photo-ocr", data={},
                    content_type="multipart/form-data")
    assert a.status_code == b.status_code


def test_vision_unsupported_type(client):
    _signup(client)
    r = _post_vision(client, b"plain text, not an image",
                     name="note.txt")
    assert r.get_json()["code"] == "unsupported"


def test_vision_too_large(client):
    _signup(client)
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (2 * 1024 * 1024)
    r = _post_vision(client, big)
    assert r.get_json()["code"] == "too_large"


# ------------------------------------------------- vision outcomes

def test_vision_unavailable_without_key(client, monkeypatch):
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)

    def explode(*a, **k):  # pragma: no cover - must not run
        raise AssertionError("HTTP attempted without a key")

    monkeypatch.setattr(gemini_vision, "_post_json", explode)
    _signup(client)
    r = _post_vision(client, PNG)
    assert r.get_json()["code"] == "vision_unavailable"


def test_vision_quota_code(client, vision_http):
    vision_http["state"]["reply"] = urllib.error.HTTPError(
        "https://example.invalid", 429, "quota", None, None)
    _signup(client)
    r = _post_vision(client, PNG)
    assert r.get_json()["code"] == "vision_quota"


def test_vision_transport_failure_code(client, vision_http):
    vision_http["state"]["reply"] = urllib.error.URLError("down")
    _signup(client)
    r = _post_vision(client, PNG)
    assert r.get_json()["code"] == "vision_failed"


def test_vision_no_question_code(client, vision_http):
    vision_http["state"]["reply"] = _gemini_reply("NO_QUESTION")
    _signup(client)
    r = _post_vision(client, PNG)
    assert r.get_json()["code"] == "no_question"


def test_vision_success_transcribes_never_solves(client,
                                                 vision_http):
    _signup(client)
    r = _post_vision(client, PNG)
    d = r.get_json()
    assert d["kind"] == "text"
    assert d["text"] == "Find the value of 3/4 + 1/2."
    assert d["prefill"] == d["text"]
    assert d["confirm"] is None
    assert d["backend"] == "gemini-vision"
    # The reply carries a transcription only — no solved
    # answer field exists anywhere in the contract.
    assert set(d) == {"kind", "text", "prefill", "confirm",
                      "backend"}
    # Exactly one API call, to the VISION model's own bucket,
    # with the key from the environment and the photo inline.
    (call,) = vision_http["calls"]
    assert "gemini-3.1-flash-lite" in call["url"]
    assert gemini_fallback.MODEL not in call["url"]
    assert call["api_key"] == "w144-test-key"
    parts = call["payload"]["contents"][0]["parts"]
    assert "do NOT solve" in parts[0]["text"]
    inline = parts[1]["inline_data"]
    assert inline["mime_type"] == "image/png"
    import base64
    assert base64.b64decode(inline["data"]) == PNG


def test_vision_mime_from_magic_bytes(client, vision_http):
    _signup(client)
    for blob, mime in ((JPEG, "image/jpeg"), (GIF, "image/gif"),
                       (WEBP, "image/webp")):
        vision_http["calls"].clear()
        r = _post_vision(client, blob, name="wrong-name.png")
        assert r.get_json()["kind"] == "text"
        parts = vision_http["calls"][0]["payload"][
            "contents"][0]["parts"]
        assert parts[1]["inline_data"]["mime_type"] == mime


def test_vision_reconstruction_and_confirm(client, vision_http):
    """Wave 137 discipline on the vision path: a read whose
    family is clear but a slot is not earns the REBUILT
    question plus the ONE confirmation line."""
    raw = ("A train runs at 60 km/h or 80 km/h for 5 hours. "
           "Find the distance covered.")
    fixed = photofix.analyse(raw)
    assert fixed is not None and fixed["confirm"]
    vision_http["state"]["reply"] = _gemini_reply(raw)
    _signup(client)
    d = _post_vision(client, PNG).get_json()
    assert d["text"] == raw
    assert d["prefill"] == fixed["question"]
    assert d["confirm"] == fixed["confirm"]


def test_vision_stores_nothing(client, vision_http, tmp_path):
    """The uploaded image is processed in memory only: the
    app tree gains no file from a vision read."""
    tree = os.path.join(os.path.dirname(__file__), "..")

    def snapshot():
        out = set()
        for root, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                out.add(os.path.relpath(
                    os.path.join(root, f), tree))
        return out

    _signup(client)
    before = snapshot()
    r = _post_vision(client, PNG)
    assert r.get_json()["kind"] == "text"
    assert snapshot() == before


# ------------------------------------------------- module contract

def test_vision_model_is_its_own_quota_bucket():
    assert gemini_vision.VISION_MODEL == "gemini-3.1-flash-lite"
    assert gemini_vision.VISION_MODEL != gemini_fallback.MODEL
    assert "do NOT solve" in gemini_vision._PROMPT
    assert "NO_QUESTION" in gemini_vision._PROMPT


def test_clean_transcription_strips_wrapping():
    clean = gemini_vision._clean_transcription
    assert clean("```\nFind 2 + 2.\n```") == "Find 2 + 2."
    assert clean("Transcription: Find 2 + 2.") == "Find 2 + 2."
    assert clean('"Find 2 + 2."') == "Find 2 + 2."
    assert clean("  Find 2 + 2.  ") == "Find 2 + 2."
    # Words and numbers are never rewritten.
    assert clean("Find HCF of 12 and 18.") == \
        "Find HCF of 12 and 18."


def test_transcribe_returns_none_for_no_question(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "k")
    monkeypatch.setattr(
        gemini_vision, "_post_json",
        lambda *a, **k: _gemini_reply("NO_QUESTION"))
    assert gemini_vision.transcribe_image(PNG, "image/png") \
        is None


# ------------------------------------------------------ client wiring

def test_chat_page_wires_vision_pdf_txt(client):
    _signup(client)
    html = client.get("/").get_data(as_text=True)
    # Vision first, with the canvas downscale.
    assert "visionImageSmart" in html
    assert '"/photo-vision"' in html
    assert "visionDownscale" in html
    # PDF in the browser (lazy pdf.js) + txt into the composer.
    assert "extractPdfClient" in html
    assert "pdfjs-dist@4.2.67" in html
    assert "getTextContent" in html
    assert "readTxtClient" in html
    assert "FileReader" in html
    assert "fileShowText" in html
    # The old chain survives intact as the fallback.
    assert "ocrImageSmart" in html
    assert '"/photo-ocr"' in html
    assert "ocrBlob" in html
    assert 'sendQuestionText(d.text, "file")' in html
    # New system strings reach the page.
    assert "js_file_check" in html
    assert "js_pdf_unavailable" in html


# --------------------------------------------------------- i18n rule

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


@pytest.mark.parametrize("key", ["js_file_check",
                                 "js_pdf_reading",
                                 "js_pdf_unavailable"])
def test_new_system_strings_are_english_or_hinglish(key):
    """Suraj's standing rule: system messages are English or
    Hinglish (Roman) — never Devanagari — in every language."""
    en = i18n.STRINGS["en"][key]
    hi = i18n.STRINGS["hi"][key]
    assert not _DEVANAGARI.search(en)
    assert not _DEVANAGARI.search(hi)
    # Other locales fall back to the English line, so they
    # obey the rule too.
    for lang in ("bn", "mr", "ta", "te"):
        assert i18n.get_strings(lang)[key] == en
