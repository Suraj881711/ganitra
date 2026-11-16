"""Wave 83: photo question -> solve (server-side OCR pipeline).

What exists before this wave (Waves 27-29): the browser OCRs a
photo with Tesseract.js and POSTs the text to /photo-solve,
which cleans it with normalize_ocr_text and solves it. What
this wave adds:

- ocr.py — a PLUGGABLE server-side OCR backend. Feasibility,
  checked first: this environment has no tesseract binary (and
  no way to install one), and PythonAnywhere's free tier cannot
  install system binaries either — so on today's host NO server
  backend exists and /photo-ocr honestly answers
  {"code": "ocr_unavailable"}; the client then falls back to
  the browser flow, and beyond that to "please type the
  question". Where a tesseract binary DOES exist, the backend
  activates with no code change. Nothing fakes a read.
- POST /photo-ocr — same upload rules as /file-extract (2 MB,
  magic bytes, nothing stored); returns the recognised text
  (already cleaned), a confidence and a low_confidence flag.
- normalize_ocr_text grows the classic digit confusions
  (O->0, l/I->1, digit-fenced), vulgar fractions and the full
  superscript-digit set — each rule fenced so a correctly read
  question is never rewritten into a different one.
- The chat script tries /photo-ocr first; a low-confidence
  read lands in the composer for the student to fix BEFORE
  solving instead of being solved blind.

The OCR ENGINE itself cannot run in this environment (no
binary — see above), so the backend's real code path
(preprocess -> subprocess -> TSV parse -> confidence) is
exercised against a FAKE tesseract executable that emits
canned TSV, and the solve path is verified end-to-end with
that injected OCR text, exactly as the wave brief allows.
"""
import io
import os
import stat
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ocr  # noqa: E402
from app import normalize_ocr_text  # noqa: E402


# ------------------------------------------------------------ fixtures

def _render_printed(text):
    """A printed-style question photo: clean DejaVu Sans on
    white, generous margins — what a textbook page photo looks
    like after cropping."""
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    img = Image.new("RGB", (1100, 160), "white")
    ImageDraw.Draw(img).text((40, 55), text, fill="black",
                             font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _render_handwritten(text):
    """A simulated handwritten-style render: oblique face,
    per-character vertical jitter, a slight page tilt and a
    grey smudge — the shape of a neat notebook photo."""
    import random
    from PIL import Image, ImageDraw, ImageFont
    random.seed(83)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/"
        "DejaVuSansMono-Oblique.ttf", 42)
    img = Image.new("RGB", (1100, 180), (248, 246, 238))
    draw = ImageDraw.Draw(img)
    x = 40
    for ch in text:
        y = 60 + random.randint(-5, 5)
        draw.text((x, y), ch, fill=(25, 25, 90), font=font)
        x += draw.textlength(ch, font=font) + 1
    img = img.rotate(1.2, resample=Image.BICUBIC,
                     fillcolor=(248, 246, 238))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _tsv(lines):
    """Build tesseract-style TSV from [(line_text, conf)]."""
    rows = ["level\tpage_num\tblock_num\tpar_num\tline_num\t"
            "word_num\tleft\ttop\twidth\theight\tconf\ttext"]
    for li, (text, conf) in enumerate(lines, start=1):
        for wi, word in enumerate(text.split(), start=1):
            rows.append("\t".join([
                "5", "1", "1", "1", str(li), str(wi),
                str(10 + wi * 60), "10", "50", "20",
                str(conf), word]))
    return "\n".join(rows) + "\n"


FAKE_TESSERACT = """\
import os, sys
path = os.environ.get("FAKE_TESS_TSV", "")
sys.stdout.write(open(path, encoding="utf-8").read()
                 if path else "")
"""


@pytest.fixture()
def fake_tesseract(tmp_path):
    """Install the fake tesseract executable + a TSV writer."""
    exe = tmp_path / "faketesseract"
    exe.write_text("#!/usr/bin/env python3\n" + FAKE_TESSERACT,
                   encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)

    def install(monkeypatch, lines):
        tsv = tmp_path / "out.tsv"
        tsv.write_text(_tsv(lines), encoding="utf-8")
        monkeypatch.setenv("GANITRA_TESSERACT_CMD", str(exe))
        monkeypatch.setenv("FAKE_TESS_TSV", str(tsv))

    return install


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _signup(client):
    r = client.post("/signup", data={
        "name": "W83 Photo Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w83-photo-pass"})
    assert r.status_code in (200, 302)


def _post_photo(client, data, name="photo.png"):
    return client.post(
        "/photo-ocr",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data")


# ------------------------------------------------- preprocessing units

def test_preprocess_printed_fixture():
    out = ocr.preprocess_image(
        _render_printed("What is 15% of 200?"))
    assert out[:8] == b"\x89PNG\r\n\x1a\n"
    from PIL import Image
    img = Image.open(io.BytesIO(out))
    assert img.mode == "L"


def test_preprocess_handwritten_fixture():
    out = ocr.preprocess_image(
        _render_handwritten("Solve: 3x + 7 = 22"))
    assert out[:8] == b"\x89PNG\r\n\x1a\n"


def test_preprocess_rejects_non_image():
    with pytest.raises(ocr.OcrFailed):
        ocr.preprocess_image(b"this is not an image at all")


def test_preprocess_rejects_pixel_bomb():
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (6000, 5000), "white").save(
        buf, format="PNG")  # 30M pixels, tiny compressed size
    with pytest.raises(ocr.OcrFailed):
        ocr.preprocess_image(buf.getvalue())


# ------------------------------------------------------- backend units

def test_no_backend_without_binary(monkeypatch):
    monkeypatch.delenv("GANITRA_TESSERACT_CMD", raising=False)
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    assert ocr.backend_available() is False
    with pytest.raises(ocr.OcrUnavailable):
        ocr.ocr_image(_render_printed("2 + 2 = ?"))


def test_backend_via_fake_tesseract(fake_tesseract, monkeypatch):
    fake_tesseract(monkeypatch, [("What is 15% of 200?", 96)])
    outcome = ocr.ocr_image(
        _render_printed("What is 15% of 200?"))
    assert outcome.text == "What is 15% of 200?"
    assert outcome.backend == "tesseract"
    assert outcome.confidence == pytest.approx(96.0)
    assert outcome.low_confidence is False


def test_backend_low_confidence(fake_tesseract, monkeypatch):
    fake_tesseract(monkeypatch, [("What is 15% of 200?", 25)])
    outcome = ocr.ocr_image(
        _render_handwritten("What is 15% of 200?"))
    assert outcome.low_confidence is True


def test_tsv_parser_regroups_lines():
    text, conf = ocr._parse_tsv(_tsv(
        [("First line here", 90), ("Second line", 80)]))
    assert text == "First line here\nSecond line"
    assert conf == pytest.approx((90 * 3 + 80 * 2) / 5)


# ------------------------------------------------------------ endpoint

def test_photo_ocr_unavailable_on_this_host(client, monkeypatch):
    # This environment (like PA free) has no tesseract binary.
    monkeypatch.delenv("GANITRA_TESSERACT_CMD", raising=False)
    monkeypatch.setattr(ocr.shutil, "which", lambda cmd: None)
    _signup(client)
    r = _post_photo(client, _render_printed("What is 2 + 2?"))
    body = r.get_json()
    assert body["ok"] is False
    assert body["code"] == "ocr_unavailable"


def test_photo_ocr_with_fake_backend(client, fake_tesseract,
                                     monkeypatch):
    fake_tesseract(monkeypatch, [("What is 15% of 200?", 95)])
    _signup(client)
    r = _post_photo(client, _render_printed("What is 15% of 200?"))
    body = r.get_json()
    assert body["kind"] == "text"
    assert body["text"] == "What is 15% of 200?"
    assert body["low_confidence"] is False
    assert body["backend"] == "tesseract"


def test_photo_ocr_handwritten_fixture(client, fake_tesseract,
                                       monkeypatch):
    fake_tesseract(monkeypatch, [("Solve: 3x + 7 = 22", 88)])
    _signup(client)
    r = _post_photo(
        client, _render_handwritten("Solve: 3x + 7 = 22"))
    body = r.get_json()
    assert body["kind"] == "text"
    assert "3x + 7 = 22" in body["text"]


def test_photo_ocr_low_confidence_flag(client, fake_tesseract,
                                       monkeypatch):
    fake_tesseract(monkeypatch, [("What is 15% of 200?", 20)])
    _signup(client)
    r = _post_photo(client, _render_printed("What is 15% of 200?"))
    assert r.get_json()["low_confidence"] is True


def test_photo_ocr_cleans_confusions(client, fake_tesseract,
                                     monkeypatch):
    fake_tesseract(monkeypatch, [("What is 2O% of 5O0?", 93)])
    _signup(client)
    r = _post_photo(client, _render_printed("What is 20% of 500?"))
    assert r.get_json()["text"] == "What is 20% of 500?"


def test_photo_ocr_empty_read(client, fake_tesseract, monkeypatch):
    fake_tesseract(monkeypatch, [])
    _signup(client)
    r = _post_photo(client, _render_printed("blank page"))
    assert r.get_json()["code"] == "empty"


def test_photo_ocr_too_large(client):
    _signup(client)
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (2 * 1024 * 1024)
    r = _post_photo(client, big)
    assert r.get_json()["code"] == "too_large"


def test_photo_ocr_unsupported_type(client):
    _signup(client)
    r = _post_photo(client, b"plain text, not an image",
                    name="note.txt")
    assert r.get_json()["code"] == "unsupported"


def test_photo_ocr_no_file(client):
    _signup(client)
    r = client.post("/photo-ocr", data={},
                    content_type="multipart/form-data")
    assert r.status_code == 400
    assert r.get_json()["code"] == "no_file"


def test_chat_page_wires_server_ocr_first(client):
    _signup(client)
    html = client.get("/").get_data(as_text=True)
    assert "ocrImageSmart" in html
    assert '"/photo-ocr"' in html
    # the browser fallback survives untouched
    assert "ocrBlob" in html
    # low-confidence reads land in the composer (id="q")
    assert "js_photo_check" in html or "check it" in html


# ------------------------------------------- OCR text cleanup (Wave 83)

@pytest.mark.parametrize("raw, want", [
    ("What is 2O% of 5O0?", "What is 20% of 500?"),
    ("1O5 + 25", "105 + 25"),
    ("Rs 5O", "Rs 50"),
    ("l5 students", "15 students"),
    ("1l5", "115"),
    ("O25 students", "025 students"),
    ("½ of 200", "1/2 of 200"),
    ("Find x⁴ + 2", "Find x^4 + 2"),
])
def test_confusion_corrections(raw, want):
    assert normalize_ocr_text(raw) == want


@pytest.mark.parametrize("raw", [
    "A tank holds 10l of water",      # 10 litres, NOT 101
    "Out of 10 questions",            # the word Out, NOT 0ut
    "I solved it myself",             # the pronoun I
    "the point O is the origin",      # O the origin point
    "Find log 100",                   # log keeps its l
    "Solve for x please",             # plain words untouched
])
def test_no_false_corrections(raw):
    assert normalize_ocr_text(raw) == raw


def test_existing_cleanups_still_hold():
    # The pre-Wave-83 contract (verify_wave3 pins these too).
    assert normalize_ocr_text("3X4") == "3*4"
    assert normalize_ocr_text("x2 + 5") == "x^2 + 5"
    assert normalize_ocr_text("10 ÷ 2") == "10 / 2"
    # A lone O + ONE digit is deliberately NOT turned into a
    # number by Wave 83 (O is also the origin point); the
    # pre-existing exponent rule reads it as the variable O
    # squared-style, exactly as before this wave.
    assert normalize_ocr_text("O5") == "O^5"


# --------------------------------------------------------- end-to-end

def test_photo_question_solves_end_to_end(client, fake_tesseract,
                                          monkeypatch):
    """Server OCR (fake engine) -> returned text -> the normal
    /photo-solve path -> the normal answer card."""
    fake_tesseract(monkeypatch, [("What is 15% of 200?", 95)])
    _signup(client)
    body = _post_photo(
        client, _render_printed("What is 15% of 200?")).get_json()
    page = client.post("/photo-solve", data={
        "question": body["text"], "source": "photo"})
    html = page.get_data(as_text=True)
    assert "30" in html


def test_handwritten_photo_solves_end_to_end(client, fake_tesseract,
                                             monkeypatch):
    """The simulated handwritten photo rides the same chain:
    /photo-ocr (fake engine) -> /photo-solve -> x = 5."""
    fake_tesseract(monkeypatch, [("Solve: 3x + 7 = 22", 88)])
    _signup(client)
    body = _post_photo(
        client, _render_handwritten("Solve: 3x + 7 = 22")
    ).get_json()
    page = client.post("/photo-solve", data={
        "question": body["text"], "source": "photo"})
    html = page.get_data(as_text=True)
    assert "x = 5" in html


def test_injected_ocr_text_solves_via_photo_solve(client):
    """OCR text carrying the classic confusions, injected the
    way the browser flow delivers it, solves correctly."""
    _signup(client)
    page = client.post("/photo-solve", data={
        "question": "What is 2O% of 5O0?", "source": "photo"})
    html = page.get_data(as_text=True)
    assert "100" in html
    # the recognised (cleaned) text is shown back to the student
    assert "20% of 500" in html


def test_non_maths_photo_gets_not_found(client, fake_tesseract,
                                        monkeypatch):
    """A photographed non-maths question rides the whole
    pipeline and still lands on the one-line not-found /
    science behaviour — never a solved card."""
    fake_tesseract(monkeypatch,
                   [("What is the capital of India?", 97)])
    _signup(client)
    body = _post_photo(
        client, _render_printed("What is the capital of India"
                                "?")).get_json()
    assert body["kind"] == "text"
    page = client.post("/photo-solve", data={
        "question": body["text"], "source": "photo"})
    html = page.get_data(as_text=True)
    # The Wave 68 non-maths guard line, not a solved card and
    # not a maths answer.
    assert "not a maths question" in html
    assert "New Delhi" not in html
