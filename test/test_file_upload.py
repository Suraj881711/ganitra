"""Wave 27 (Suraj, 13 Nov 2026): ANY-FILE upload in the chat.

Suraj: "PDF file wala option nahi aa raha select karne ka",
then, wider: "Koi si bhi file ho, all file ko select karane
kaa option hona chahiye." So the attach input carries NO
accept restriction (the picker offers every file), and the
handling is tiered by MAGIC BYTES on the server:

- image  -> the browser's existing Tesseract flow (an image
  reaching /file-extract anyway is handed back for it);
- PDF    -> text layer via pypdf; no text layer -> the
  first page rendered by poppler, returned as an image for
  the same browser OCR;
- .docx  -> document text via zipfile + XML (no new dep);
- .txt   -> the contents as the question;
- anything else (a plain .zip, an executable, ...) -> the
  honest "ye file type abhi nahi padh sakta" code, which the
  chat script turns into that line in the student's
  language. Never a dead end, never a fake solve.

Size cap matches the profile photo's 2 MB (Wave 17 rules:
content sniffing, no executable handling, nothing stored).
"""
import io
import shutil
import zipfile

import pytest

ROOT = None  # (paths are not needed; everything is HTTP)


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
        "name": "W27 Upload Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w27-upload-pass"})
    assert r.status_code in (200, 302)


def _post(client, data, name):
    return client.post(
        "/file-extract",
        data={"file": (io.BytesIO(data), name)},
        content_type="multipart/form-data")


def _solve_via_photo_flow(client, question):
    """The extracted text rides the same /photo-solve form a
    photo's OCR text uses (hidden field + submit)."""
    return client.post("/photo-solve", data={"question": question})


def test_picker_has_no_accept_restriction(client):
    _signup(client)
    html = client.get("/").get_data(as_text=True)
    tag = html[html.index('id="photo-input"') - 30:
               html.index('id="photo-input"') + 40]
    assert "accept=" not in tag


def test_txt_file_solves(client):
    r = _post(client, "15 aur 27 ka jod kitna hoga?".encode("utf-8"),
              "note.txt")
    body = r.get_json()
    assert body["kind"] == "text"
    assert "15" in body["text"]
    page = _solve_via_photo_flow(client, body["text"])
    assert "42" in page.get_data(as_text=True)


def test_pdf_with_text_layer_solves(client):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure()
    fig.text(0.1, 0.5, "Solve 2x + 3 = 7")
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf")
    r = _post(client, buf.getvalue(), "homework.pdf")
    body = r.get_json()
    assert body["kind"] == "text"
    assert "2x + 3 = 7" in body["text"]
    page = _solve_via_photo_flow(client, body["text"])
    assert "x = 2" in page.get_data(as_text=True)


@pytest.mark.skipif(shutil.which("pdftoppm") is None,
                    reason="poppler not installed here")
def test_scanned_pdf_returns_first_page_image(client):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 200), "white")
    ImageDraw.Draw(img).text((20, 80), "2 + 2 = ?", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    r = _post(client, buf.getvalue(), "scan.pdf")
    body = r.get_json()
    assert body["kind"] == "image"
    import base64
    png = base64.b64decode(body["image"])
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def _docx_bytes(text):
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/'
        'wordprocessingml/2006/main"><w:body><w:p><w:r>'
        f"<w:t>{text}</w:t>"
        "</w:r></w:p></w:body></w:document>")
    types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/'
        'package/2006/content-types"><Default Extension="xml" '
        'ContentType="application/xml"/><Override '
        'PartName="/word/document.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.wordprocessingml.'
        'document.main+xml"/></Types>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", types)
        zf.writestr("word/document.xml", document)
    return buf.getvalue()


def test_docx_extracts_and_solves(client):
    r = _post(client, _docx_bytes("Solve 2x + 3 = 7"),
              "homework.docx")
    body = r.get_json()
    assert body["kind"] == "text"
    assert "2x + 3 = 7" in body["text"]
    page = _solve_via_photo_flow(client, body["text"])
    assert "x = 2" in page.get_data(as_text=True)


def test_plain_zip_is_unsupported_not_solved(client):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", "Solve 2x + 3 = 7")
    r = _post(client, buf.getvalue(), "bundle.zip")
    body = r.get_json()
    assert body.get("ok") is False
    assert body.get("code") == "unsupported"


def test_executable_bytes_are_unsupported(client):
    r = _post(client, b"MZ" + b"\x00" * 200, "setup.exe")
    body = r.get_json()
    assert body.get("ok") is False
    assert body.get("code") == "unsupported"


def test_oversize_file_is_too_large(client):
    big = b"Solve 2x + 3 = 7\n" * (2 * 1024 * 1024 // 17 + 1)
    r = _post(client, big, "big.txt")
    body = r.get_json()
    assert body.get("ok") is False
    assert body.get("code") == "too_large"


def test_empty_txt_is_honest_empty(client):
    r = _post(client, b"   \n", "blank.txt")
    body = r.get_json()
    assert body.get("ok") is False
    assert body.get("code") == "empty"


def test_image_reaching_server_is_handed_back_for_ocr(client):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buf, format="PNG")
    r = _post(client, buf.getvalue(), "photo.png")
    body = r.get_json()
    assert body["kind"] == "image"


def test_file_messages_exist_in_every_language(client):
    # The chat script speaks the honest lines from js_t —
    # every language carries the three new keys.
    import i18n
    for lang in ("en", "hi", "bn", "mr", "ta", "te"):
        strings = i18n.get_strings(lang)
        assert strings["js_file_reading"]
        assert strings["js_file_unsupported"]
        assert strings["js_file_too_large"]
    _signup(client)
    html = client.get("/").get_data(as_text=True)
    assert "js_file_unsupported" in html
    assert '"/file-extract"' in html or "/file-extract" in html
