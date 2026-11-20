"""Wave 126: photo-question strengthening (browser-side only).

Suraj's order (17 Nov 2026): develop against the big-AI gaps,
paid hosting excluded — so NO server OCR (impossible on free
hosting). This wave squeezes the browser pipeline that already
exists (Wave 83: Tesseract.js + /photo-solve):

1. CLIENT-SIDE PREPROCESSING before OCR (canvas): EXIF
   auto-rotate, grayscale, percentile contrast stretch,
   upscale of small photos, white-border padding, and an
   Otsu-binarized variant for the retry pass. Any failure
   resolves to the original photo — preprocessing can never
   become a new way to fail.
2. A CONFIDENCE GATE with a measured, honest limit: a read
   under 60 (the server backend's own threshold) earns one
   binarized retry, and a read that is still weak — or that
   carries no maths signal at all — lands EDITABLE in the
   composer (the js_photo_check path) instead of being solved
   blind. Wave-126 Chromium measurements (notes file) showed
   Tesseract confidence runs 85-94 even on its two WRONG
   reads, so the gate is a garbage-catcher, not a digit
   checker; the editable answer-page box remains the safety
   net for digit-level errors. Tuning evidence, also measured:
   the default page-seg mode is already SINGLE_BLOCK, PSM 4
   changed nothing, and a char whitelist made every test
   photo WORSE (it eats word-problem letters and all of
   Devanagari) — so the Wave-36-pinned recognize() calls are
   deliberately untouched.
3. POST-CORRECTION grows the next tier of measured
   confusions in normalize_ocr_text (S->5, Z->2, B->8, g->9,
   "o/o"->%, split decimals, V/✓->√), each digit-fenced and
   each pinned below with a never-rewrite guard beside it.

The browser engine itself is verified in headless Chromium
against rendered test photos (before/after table in
~/workspace/ganitra-wave126-photo-notes.md); these tests pin
the code and the server-side cleanup contract.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import normalize_ocr_text  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
with open(os.path.join(ROOT, "templates", "index.html"),
          encoding="utf-8") as fh:
    INDEX = fh.read()
with open(os.path.join(ROOT, "static", "sw.js"),
          encoding="utf-8") as fh:
    SW = fh.read()


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
        "name": "W126 Photo Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w126-photo-pass"})
    assert r.status_code in (200, 302)


# --------------------------------------- post-correction: new fixes

@pytest.mark.parametrize("raw,want", [
    ("Find the sum of 48 and 3S.", "Find the sum of 48 and 35."),
    ("1S5", "155"),                    # S between digits
    ("1s5", "155"),                    # lowercase s between digits
    ("2Z5", "225"),                    # Z -> 2
    ("3B4", "384"),                    # B -> 8
    ("1g2", "192"),                    # g -> 9
    ("Find 15 o/o of 200", "Find 15% of 200"),
    ("Find 15o/o of 200", "Find 15% of 200"),
    ("3. 5", "3.5"),                   # split decimal, space after
    ("3 .5", "3.5"),                   # split decimal, space before
    ("3 . 25", "3.25"),                # split decimal, both sides
    ("Find V625", "Find √625"),        # V read for the root sign
    ("Find V49 and V9", "Find √49 and √9"),
    ("✓625", "√625"),                  # check-mark read for √
])
def test_wave126_corrections(raw, want):
    assert normalize_ocr_text(raw) == want


@pytest.mark.parametrize("raw", [
    "Angle ABC is 90°",                # ° is a real angle mark
    "V is the volume",                 # V the variable, no digits
    "Section B has 5 questions",       # B the section, no fence
    "Chapter 5: Sets and Zeros",       # plain words untouched
    "a bag of 5 kg rice",              # kg unit untouched
    "Out of 10 questions, 8 were easy",  # the Wave-83 guards
    "He has 10l of water",
    "the point O is the origin",
    "Find log 100",
    "Solve for x please",
])
def test_wave126_no_false_corrections(raw):
    assert normalize_ocr_text(raw) == raw


def test_wave126_older_corrections_still_hold():
    assert normalize_ocr_text("3X4") == "3*4"
    assert normalize_ocr_text("x2 + 5") == "x^2 + 5"
    assert normalize_ocr_text("10 ÷ 2") == "10 / 2"
    assert normalize_ocr_text("O5") == "O^5"
    assert normalize_ocr_text("1O5") == "105"
    assert normalize_ocr_text("Rs 5O") == "Rs 50"


# ------------------------------------------------- end-to-end solves

def test_wave126_handwritten_style_text_solves(client):
    """The exact raw read the browser produced for the Wave-126
    handwriting photo ("3S" for 35) now solves as 48 + 35."""
    _signup(client)
    page = client.post("/photo-solve", data={
        "question": "Find the sum of 48 and 3S.",
        "source": "photo"})
    html = page.get_data(as_text=True)
    assert "48 and 35" in html         # cleaned question shown
    assert "83" in html                # 48 + 35 solved


def test_wave126_percent_confusion_solves(client):
    _signup(client)
    page = client.post("/photo-solve", data={
        "question": "Find 15 o/o of 200", "source": "photo"})
    html = page.get_data(as_text=True)
    assert "15%" in html
    assert "30" in html


def test_wave126_root_sign_confusion_solves(client):
    _signup(client)
    page = client.post("/photo-solve", data={
        "question": "Find V625", "source": "photo"})
    html = page.get_data(as_text=True)
    assert "√625" in html
    assert "25" in html


# ------------------------------------------------------- page wiring

def test_preprocessing_present_and_failsafe():
    assert "function ocrPreprocess" in INDEX
    assert "function ocrProcessPixels" in INDEX
    assert 'imageOrientation: "from-image"' in INDEX   # EXIF
    assert 'createImageBitmap' in INDEX
    # resolves with the original blob on failure, never rejects
    assert "resolve(b || blob)" in INDEX


def test_confidence_gate_present():
    assert "var OCR_LOW_CONFIDENCE = 60;" in INDEX
    assert "function ocrMeanConfidence" in INDEX
    assert "function ocrDeliverRead" in INDEX
    assert "function ocrBinarizedRetry" in INDEX
    # the weak read lands in the composer via the existing
    # js_photo_check message, same as the server path
    assert "function ocrShowForCheck" in INDEX
    assert "say(L.js_photo_check)" in INDEX
    # both OCR entry points deliver through the gate
    assert INDEX.count("ocrDeliverRead(") >= 3


def test_maths_signal_check_present():
    assert "function ocrLooksLikeMaths" in INDEX


def test_wave36_recognize_calls_untouched():
    """The pinned bilingual-first calls stay byte-identical;
    preprocessing feeds them a cleaned blob instead."""
    assert 'recognize(blob, "eng+hin")' in INDEX
    assert 'recognize(blob, "eng")' in INDEX
    assert "function ocrBlobEngOnly" in INDEX
    assert ".catch(function () { ocrBlobEngOnly(blob, source); })" \
        in INDEX
    assert INDEX.index('recognize(blob, "eng+hin")') < \
        INDEX.index('ocrBlob(blob, "file-ocr")')


def test_no_whitelist_or_psm_override_shipped():
    """Measured WORSE in the Wave-126 Chromium runs — the page
    must not grow a tessedit whitelist/PSM override."""
    assert "tessedit_char_whitelist" not in INDEX
    assert "tessedit_pageseg_mode" not in INDEX


def test_engine_still_lazy_and_deferred():
    """The wrapper script stays deferred (the heavy engine
    loads only inside the first recognize call)."""
    tag = ('<script defer src="https://cdn.jsdelivr.net/npm/'
           'tesseract.js@5/dist/tesseract.min.js"></script>')
    assert tag in INDEX


def test_wave126_static_pins():
    assert "style.css?v=61" in SW
    assert "ganitra-static-v38" in SW
