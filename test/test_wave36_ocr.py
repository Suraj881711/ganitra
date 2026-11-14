"""Wave 36, GAP A — Hindi photo OCR.

Until this wave the browser OCR (Tesseract.js in
templates/index.html) ran with "eng" only, so a photo of a
Hindi (Devanagari) question came back as Latin-script garbage
(proven locally with the same engine: the fixture question
"दो संख्याओं का योग 27 है / और उनका अंतर 3 है।" OCR'd with
"eng" as "3 Greif waht 27 8 / 31R I9ehT 3idR 3 21").

The fix: ocrBlob first tries "eng+hin"; when the Hindi
traineddata cannot be loaded the recognize promise rejects
(verified: tesseract.js throws ENOENT for the missing
hin.traineddata) and the catch retries English-only; an
empty bilingual read also falls back. The photo flow can
therefore never dead-end on the extra language.

The live-OCR test at the bottom is OPTIONAL: it runs only
when node + a tesseract.js harness with local traineddata
are available (GANITRA_OCR_HARNESS env var pointing at the
harness dir); everywhere else it skips, per the wave spec.
"""
import os
import re
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = open(os.path.join(ROOT, "templates", "index.html"),
             encoding="utf-8").read()
FIXTURE = os.path.join(ROOT, "test", "fixtures", "hindi_question.png")

HINDI_QUESTION_TOKENS = ("योग", "अंतर", "27")


def test_ocr_tries_english_plus_hindi_first():
    assert 'recognize(blob, "eng+hin")' in INDEX


def test_ocr_has_english_only_fallback():
    # A dedicated eng-only retry path must exist and be what the
    # bilingual attempt falls back to on rejection.
    assert "function ocrBlobEngOnly" in INDEX
    assert 'recognize(blob, "eng")' in INDEX
    assert ".catch(function () { ocrBlobEngOnly(blob, source); })" in INDEX


def test_bilingual_attempt_comes_before_fallback_call():
    # Source order: the eng+hin attempt is inside ocrBlob, and the
    # file-ocr path from Wave 28 still routes through ocrBlob.
    assert INDEX.index('recognize(blob, "eng+hin")') < INDEX.index(
        'ocrBlob(blob, "file-ocr")')
    assert 'ocrBlob(blob, "file-ocr")' in INDEX


def test_normaliser_preserves_devanagari():
    # The server-side OCR normaliser must not eat the Hindi text
    # the bilingual OCR now produces (Wave 30 proved typed Hindi
    # questions solve; photo Hindi rides the same normaliser).
    from app import normalize_ocr_text
    raw = "दो संख्याओं का योग 27 है\nऔर उनका अंतर 3 है।"
    out = normalize_ocr_text(raw)
    for token in HINDI_QUESTION_TOKENS:
        assert token in out, (token, out)


def _harness_dir():
    d = os.environ.get("GANITRA_OCR_HARNESS")
    if d and os.path.isfile(os.path.join(d, "ocr.js")):
        return d
    return None


@pytest.mark.skipif(shutil.which("node") is None or _harness_dir() is None,
                    reason="node/tesseract.js harness not available")
def test_live_ocr_hindi_fixture():
    harness = _harness_dir()
    assert os.path.isfile(FIXTURE)

    def ocr(lang):
        proc = subprocess.run(
            ["node", "ocr.js", lang, FIXTURE],
            cwd=harness, capture_output=True, text=True, timeout=600)
        import json
        return json.loads(proc.stdout.strip().splitlines()[-1])

    bilingual = ocr("eng+hin")
    assert bilingual["ok"], bilingual
    for token in HINDI_QUESTION_TOKENS:
        assert token in bilingual["text"], bilingual["text"]

    # The old behaviour, documented: eng-only cannot read it.
    english = ocr("eng")
    assert english["ok"], english
    assert "योग" not in english["text"]
