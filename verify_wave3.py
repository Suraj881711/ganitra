"""Wave-3 verification: voice input (Web Speech API) and photo input
(Tesseract.js OCR in the browser + POST /photo-solve + OCR normaliser).

Note: real camera-photo OCR accuracy and real microphone recognition can
only be exercised in a real browser. What is verified here is the whole
server-visible pipeline: homepage controls/CDN tags, the normaliser, and
the /photo-solve route end to end.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app, normalize_ocr_text  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:28} {detail}")
    if not cond:
        fails.append((cat, detail))


# --- 1. OCR normaliser unit checks --------------------------------------
cases = [
    ("x2 − 5x + 6 = 0", "x^2 - 5x + 6 = 0"),       # unicode minus + x2
    ("x 2 - 5x + 6 = 0", "x^2 - 5x + 6 = 0"),      # spaced exponent
    ("3 × 4", "3 * 4"),                            # multiplication sign
    ("3X4", "3*4"),                                # X between digits
    ("10 ÷ 2 = 5", "10 / 2 = 5"),                  # division sign
    ("x² + 2x + 1", "x^2 + 2x + 1"),               # superscript two
    ("solve   2x+3=7\n", "solve 2x+3=7"),         # whitespace collapse
    ("sin 30 ka maan", "sin 30 ka maan"),          # no false changes
    ("P(X < 1)", "P(X < 1)"),                      # no false changes
    ("integrate x^2 from 0 to 1", "integrate x^2 from 0 to 1"),
]
for raw, expected in cases:
    got = normalize_ocr_text(raw)
    check("normaliser", got == expected, f"{raw!r} -> {got!r}")

# --- 2. Homepage carries both input methods ------------------------------
app = create_app()
client = app.test_client()
r = client.get("/")
body = r.get_data(as_text=True)
check("GET /", r.status_code == 200, f"status={r.status_code}")
check("mic button", 'id="mic-btn"' in body)
check("voice API guarded", "SpeechRecognition" in body
      and "webkitSpeechRecognition" in body)
check("photo input", 'id="photo-input"' in body
      and 'accept="image/*"' in body)
check("tesseract CDN", "cdn.jsdelivr.net/npm/tesseract.js" in body)
check("photo form route", 'action="/photo-solve"' in body)

# --- 3. /photo-solve end to end ------------------------------------------
r = client.post("/photo-solve", data={"question": "x2 − 5x + 6 = 0"})
body = r.get_data(as_text=True)
check("POST /photo-solve", r.status_code == 200, f"status={r.status_code}")
check("photo confirm box", "photo-box" in body
      and "Photo se padha gaya sawaal" in body)
check("normalised text shown", "x^2 - 5x + 6 = 0" in body)
check("solved x=2", "x = 2" in body)
check("solved x=3", "x = 3" in body)
check("edit box posts to /solve", 'action="/solve"' in body)

r = client.post("/photo-solve", data={"question": "   "})
check("empty photo text redirects", r.status_code == 302,
      f"status={r.status_code}")

# --- 4. Existing flow untouched ------------------------------------------
r = client.post("/solve", data={"question": "2+2*5"})
check("POST /solve still works", r.status_code == 200
      and "12" in r.get_data(as_text=True))

print()
print("FAILURES:", len(fails))
for cat, detail in fails:
    print(" -", cat, "|", detail)
