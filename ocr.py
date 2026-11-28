"""Wave 83 (photo question -> solve): pluggable server-side OCR.

Why this module exists
----------------------
Up to Wave 29 the photo flow OCR'd in the BROWSER (Tesseract.js
from a CDN): fine on a good phone connection, dead offline and
slow on weak ones. Wave 83 adds a SERVER-side OCR step behind a
pluggable backend, so the same upload can be read on the server
wherever a real OCR engine exists — and, just as importantly,
can say so honestly where none does.

Feasibility, checked 16 Nov 2026 in this environment AND for the
production host (PythonAnywhere free tier):

- this sandbox has NO tesseract binary, no pytesseract, and no
  apt package lists to install one from;
- PythonAnywhere free accounts cannot install system binaries
  at all, and their image does not ship tesseract.

So on today's production host NO server backend is available,
and this module's job there is to report that cleanly
(``code="ocr_unavailable"``) so the client falls back to the
browser Tesseract.js flow, and beyond that to the honest
"please type the question" line. Nothing here fakes OCR: no
backend, no text. The tesseract backend activates automatically
wherever a ``tesseract`` binary IS present (a dev machine, a
future paid host, a PA image that grows one) — no code change,
just the binary (or the GANITRA_TESSERACT_CMD env var pointing
at it).

Pipeline
--------
``preprocess_image`` (Pillow): decode from bytes in memory,
refuse decompression bombs, greyscale + autocontrast, upscale
small photos, cap the long edge — the standard tesseract-
friendly prep. ``TesseractBackend`` runs the binary on a
throwaway temp PNG (deleted with the request; the uploaded
bytes themselves are never written to disk and never retained)
and parses its TSV output for the text plus a mean word
confidence. ``ocr_image`` is the one entry point the route
uses; it returns an :class:`OcrOutcome` or raises
:class:`OcrUnavailable` / :class:`OcrFailed`.

Confidence: tesseract reports a per-word confidence (0-100).
The mean over recognised words below ``LOW_CONFIDENCE`` marks
the read ``low_confidence`` — the client then shows the text
to the student for editing BEFORE solving instead of solving
a possibly-misread question blind. Wave 231 (BUG-010): the
mean alone can hide a single misread symbol (a minus read as
a plus at low confidence, averaged away by confident prose),
so a symbol-bearing token (digit / operator) under the same
bar also marks the read ``low_confidence`` — see
``OcrOutcome.symbol_confidence``.
"""

import io
import os
import shutil
import subprocess
import tempfile

LOW_CONFIDENCE = 60          # mean tesseract word confidence
MAX_IMAGE_PIXELS = 25_000_000  # decompression-bomb guard
MAX_EDGE = 3000              # px; bigger photos are shrunk
MIN_EDGE = 1000              # px; smaller photos are enlarged
_TESSERACT_TIMEOUT = 25      # seconds, hard cap per read


class OcrUnavailable(Exception):
    """No OCR backend exists on this host."""


class OcrFailed(Exception):
    """A backend exists but this read failed."""


class OcrOutcome:
    def __init__(self, text, confidence, backend,
                 symbol_confidence=None):
        self.text = text
        self.confidence = confidence
        self.backend = backend
        # Wave 231 (BUG-010): the lowest confidence among
        # symbol-bearing tokens (digits / operators), or None
        # when the read carried none.
        self.symbol_confidence = symbol_confidence

    @property
    def low_confidence(self):
        if (self.confidence is not None
                and self.confidence < LOW_CONFIDENCE):
            return True
        # Wave 231 (BUG-010): the mean over ALL words can hide
        # one misread symbol — ninety-five confident prose
        # words average away a "-" read at 40 that was really
        # a "+", and the solver then solves a different
        # question with full confidence. A symbol-bearing
        # token under the SAME bar drags the whole read into
        # the confirm-before-solving behaviour, however high
        # the mean sits.
        return (self.symbol_confidence is not None
                and self.symbol_confidence < LOW_CONFIDENCE)


def _tesseract_cmd():
    """The tesseract executable to use: the env override wins,
    else a PATH lookup. None when no binary exists."""
    override = os.environ.get("GANITRA_TESSERACT_CMD", "").strip()
    if override:
        return override
    return shutil.which("tesseract")


def preprocess_image(data):
    """Decode uploaded image bytes and prepare a PNG tesseract
    reads well. Returns PNG bytes. Raises OcrFailed for bytes
    that are not a decodable image and for pixel bombs.
    Pillow arrives with matplotlib (requirements); the import
    is local so a missing Pillow degrades to OcrUnavailable,
    never an import-time crash."""
    try:
        from PIL import Image, ImageOps
    except Exception:
        raise OcrUnavailable("Pillow is not installed")
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise OcrFailed("image could not be decoded")
    width, height = img.size
    if width * height > MAX_IMAGE_PIXELS:
        raise OcrFailed("image has too many pixels")
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    edge = max(img.size)
    if edge > MAX_EDGE:
        scale = MAX_EDGE / edge
        img = img.resize(
            (max(1, int(img.width * scale)),
             max(1, int(img.height * scale))),
            Image.LANCZOS)
    elif 0 < edge < MIN_EDGE:
        scale = MIN_EDGE / edge
        img = img.resize(
            (max(1, int(img.width * scale)),
             max(1, int(img.height * scale))),
            Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


_SYMBOL_CHARS = set("+-−–—×*/÷=<>≤≥^√π%()")


def _is_symbol_bearing(word):
    """Wave 231 (BUG-010): a token whose misread can change
    the QUESTION — anything carrying a digit ("12", "3x",
    "2.5") or built from operator characters ("+", "−", "=",
    "×", a lone "x"). Plain prose words are not symbol-
    bearing: their misreads garble wording, not values."""
    w = str(word or "")
    if any(ch.isdigit() for ch in w):
        return True
    return bool(w) and all(
        ch in _SYMBOL_CHARS or ch == "x" for ch in w)


def _parse_tsv_rows(tsv):
    """Tesseract TSV -> (text, [(word, conf), ...]). Words are
    regrouped into their printed lines so the solver sees the
    question's line structure (collapsed later by
    normalize_ocr_text, exactly like the browser flow's
    text)."""
    lines = {}
    order = []
    pairs = []
    rows = tsv.splitlines()
    for row in rows[1:]:  # first row is the header
        parts = row.split("\t")
        if len(parts) < 12:
            continue
        try:
            conf = float(parts[10])
        except ValueError:
            continue
        word = parts[11].strip()
        if not word or conf < 0:
            continue
        key = (parts[2], parts[3], parts[4])  # block, par, line
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append(word)
        pairs.append((word, conf))
    text = "\n".join(" ".join(lines[key]) for key in order)
    return text.strip(), pairs


def _parse_tsv(tsv):
    """Tesseract TSV -> (text, mean word confidence or None)."""
    text, pairs = _parse_tsv_rows(tsv)
    confs = [conf for _word, conf in pairs]
    confidence = (sum(confs) / len(confs)) if confs else None
    return text, confidence


def _symbol_min_confidence(pairs):
    """The lowest confidence among symbol-bearing tokens, or
    None when the read carried none."""
    vals = [conf for word, conf in pairs
            if _is_symbol_bearing(word)]
    return min(vals) if vals else None


class TesseractBackend:
    """OCR via a tesseract binary (system install or the
    GANITRA_TESSERACT_CMD override). Shelling out keeps the
    dependency surface at zero: no pytesseract needed."""

    name = "tesseract"

    def __init__(self, cmd):
        self.cmd = cmd

    def run(self, data):
        png = preprocess_image(data)
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "in.png")
            with open(src, "wb") as fh:
                fh.write(png)
            try:
                proc = subprocess.run(
                    [self.cmd, src, "stdout",
                     "--psm", "6", "tsv"],
                    capture_output=True, timeout=_TESSERACT_TIMEOUT)
            except subprocess.TimeoutExpired:
                raise OcrFailed("tesseract timed out")
            except OSError as exc:
                raise OcrFailed(f"tesseract could not run: {exc}")
        if proc.returncode != 0:
            raise OcrFailed(
                f"tesseract exited {proc.returncode}")
        text, pairs = _parse_tsv_rows(
            proc.stdout.decode("utf-8", "replace"))
        confs = [conf for _word, conf in pairs]
        confidence = (sum(confs) / len(confs)) if confs else None
        return OcrOutcome(text, confidence, self.name,
                          symbol_confidence=_symbol_min_confidence(
                              pairs))


def available_backend():
    """The backend this host can actually run, or None."""
    cmd = _tesseract_cmd()
    if cmd:
        return TesseractBackend(cmd)
    return None


def backend_available():
    return available_backend() is not None


def ocr_image(data):
    """Read one uploaded image's text. Raises OcrUnavailable
    when this host has no OCR engine, OcrFailed when the read
    itself fails. The caller still runs the returned text
    through normalize_ocr_text before solving."""
    backend = available_backend()
    if backend is None:
        raise OcrUnavailable("no OCR backend on this host")
    return backend.run(data)
