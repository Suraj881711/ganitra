"""Wave 84: VOICE INPUT — spoken-maths normalisation.

The chat composer already had a mic button driving the
browser's Web Speech API (Wave 3/11). Wave 84 makes what the
student SAID land in the box the way a typing student would
write it: normalizeSpokenMaths() in templates/index.html folds
spoken forms to symbols ("x square" -> "x^2", "12 bata 3" ->
"12/3", "5 guna 4" -> "5×4") before the transcript is placed
in the composer, where the student can still read and edit it.
Recognition now also walks a language fallback chain (UI
language -> hi-IN -> en-IN) on language-not-supported.

The normaliser itself is JavaScript, so these tests extract
it from the template (between the WAVE84-SPEECH-NORMALISE
markers) and run it under node, the same approach as
verify_wave18.py's teacher-narration checks. Pins ?v=43 /
cache ganitra-static-v23 (bumped this wave because the chat
page's JS changed).
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

NODE = shutil.which("node")

CASES_EN = [
    ("5 plus 3", "5+3"),
    ("12 into 4", "12×4"),
    ("10 upon 2", "10/2"),
    ("20 divided by 4", "20/4"),
    ("7 multiplied by 6", "7×6"),
    ("x square minus 5 x plus 6 equals 0", "x^2-5 x+6 = 0"),
    ("a squared plus b squared", "a^2+b^2"),
    ("2 to the power 3", "2^3"),
    ("3 point 5 plus 1 point 5", "3.5+1.5"),
    ("x plus 6", "x+6"),
    ("10 minus 2 square", "10-2^2"),
    ("5 plus 3 plus 2", "5+3+2"),
]

CASES_HINGLISH = [
    ("5 guna 4", "5×4"),
    ("12 bata 3", "12/3"),
    ("10 ghata 3", "10-3"),
    ("10 me se 3 ghatao", "10-3"),
    ("5 jod 3", "5+3"),
    ("x ka varg", "x^2"),
    ("5 ka square", "5^2"),
]

CASES_HINDI = [
    ("5 गुणा 4", "5×4"),
    ("12 बटा 3", "12/3"),
    ("10 घटा 3", "10-3"),
    ("10 में से 3 घटाओ", "10-3"),
    ("5 जोड़ 3", "5+3"),
    ("x बराबर 5", "x = 5"),
    ("५ गुणा ४", "5×4"),  # Devanagari digits fold to ASCII
]

# Phrases the normaliser must NOT touch: the solver reads
# "square root" as-is, "a square" is the shape, "batao" is
# "tell me", "aur" is too ambiguous to fold, and a letter
# operand must be a whole token ("a plus point" is prose).
CASES_UNCHANGED = [
    "square root of 16",
    "what is the square root of 16",
    "area of a square",
    "perimeter of the square",
    "mujhe batao",
    "5 aur 3",
    "a plus point",
]

ALL_PHRASES = ([p for p, _ in CASES_EN + CASES_HINGLISH + CASES_HINDI]
               + CASES_UNCHANGED)


@pytest.fixture(scope="module")
def normalised():
    if not NODE:
        pytest.skip("node unavailable — JS normaliser untested")
    seg = INDEX.split("WAVE84-SPEECH-NORMALISE-BEGIN")[1]
    seg = seg.split("WAVE84-SPEECH-NORMALISE-END")[0]
    driver = (
        "const fs = require('fs');\n" + seg + "\n"
        "const lines = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));\n"
        "process.stdout.write(JSON.stringify(lines.map(normalizeSpokenMaths)));\n"
    )
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        dp = Path(td) / "driver.js"
        pp = Path(td) / "phrases.json"
        dp.write_text(driver, encoding="utf-8")
        pp.write_text(json.dumps(ALL_PHRASES, ensure_ascii=False),
                      encoding="utf-8")
        out = subprocess.run([NODE, str(dp), str(pp)],
                             capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return dict(zip(ALL_PHRASES, json.loads(out.stdout)))


@pytest.mark.parametrize("phrase,expected", CASES_EN)
def test_spoken_maths_english(normalised, phrase, expected):
    assert normalised[phrase] == expected


@pytest.mark.parametrize("phrase,expected", CASES_HINGLISH)
def test_spoken_maths_hinglish(normalised, phrase, expected):
    assert normalised[phrase] == expected


@pytest.mark.parametrize("phrase,expected", CASES_HINDI)
def test_spoken_maths_hindi(normalised, phrase, expected):
    assert normalised[phrase] == expected


@pytest.mark.parametrize("phrase", CASES_UNCHANGED)
def test_spoken_maths_leaves_prose_alone(normalised, phrase):
    assert normalised[phrase] == phrase


def test_mic_wiring_uses_normaliser():
    assert 'id="mic-btn"' in INDEX
    assert "function normalizeSpokenMaths" in INDEX
    # The recognition result is normalised before it lands
    # in the composer box.
    assert "text = normalizeSpokenMaths(text);" in INDEX
    # Appended after anything already typed, not overwritten.
    assert "box.value.trim()" in INDEX


def test_voice_language_fallback_chain():
    assert "SpeechRecognition" in INDEX
    assert "webkitSpeechRecognition" in INDEX
    assert "function speechLangs()" in INDEX
    assert '"hi-IN"' in INDEX and '"en-IN"' in INDEX
    assert "language-not-supported" in INDEX
    # Permission denial keeps its plain-language message.
    assert "js_voice_denied" in INDEX
    # No-API browsers still hide the button.
    assert 'micBtn.style.display = "none"' in INDEX


def test_wave84_pins():
    assert "v='46'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v23"' in SW
