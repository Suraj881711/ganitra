"""Wave 137: photo partial-read analysis ("kuch word se
analysis karke padhna").

Suraj's approved design (17 Nov 2026, on top of Wave 126):
when a photo reads only PARTIALLY, Ganitra analyses the
surviving words, works out the question TYPE, rebuilds the
full question into the editable composer, and asks about
the ONE unclear part in ONE short line ("Speed 60 hai ya
80?"). A guess is NEVER solved directly — confirm first,
then solve.

Pinned here:
* photofix.analyse: family match + reconstruction for the
  solver's bread-and-butter families (train/STD, pole,
  HCF/LCM, percentage, simple interest, mensuration, ratio,
  average, algebra), in EN / Hindi / Hinglish;
* ambiguous slot -> exactly ONE confirmation line naming it;
  missing slot -> a ___ placeholder + the line says so;
* reconstructed numbers come ONLY from the OCR text;
* no family match -> None (the caller falls back to Wave
  126's raw editable text — never worse than before);
* POST /photo-fix NEVER solves anything (the no-auto-solve
  pin: solve_question is rigged to explode, the route still
  answers, and no solve lands in the session);
* /photo-ocr: a low-confidence read gains prefill/confirm
  fields ONLY when a family matches; a confident read gains
  nothing at all (Wave 126 behaviour byte-identical);
* the page wiring: weak browser reads route through
  ocrFixAndShow, the reconstruction is shown — never
  submitted — from that path;
* a rebuilt question, once the student sends it himself,
  actually solves end-to-end via /photo-solve.
"""
import io
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import photofix  # noqa: E402
from photofix import analyse  # noqa: E402

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
        "name": "W137 Photo Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w137-photo-pass"})
    assert r.status_code in (200, 302)


# ------------------------------------------------ train / STD family

def test_train_ambiguous_speed_en():
    r = analyse("A traln travels 240 km at a speed of 60 km/h. "
                "Speed was 80 km/h also. Find the time taken.")
    assert r["family"] == "speed_time_distance"
    assert r["question"] == ("How long will a train take to "
                             "travel 240 km at a speed of "
                             "60 km/h?")
    assert r["confirm"] == "Is the speed 60 or 80?"


def test_train_ambiguous_speed_hinglish_brief_example():
    """Suraj's own example line: 'Speed 60 hai ya 80?'"""
    r = analyse("Ek train 60 km/h ki speed se jaati hai, speed "
                "80 bhi likha hai, 240 km jaane me time nikalo")
    assert r["question"] == ("Ek train 240 km jaati hai "
                             "60 km/h ki speed se, kitna time "
                             "lagega?")
    assert r["confirm"] == "Speed 60 hai ya 80?"


def test_train_clean_read_no_confirm():
    r = analyse("A train travels 360 km at speed of 90 km/h "
                "find the time taken")
    assert r["confirm"] is None
    assert "360 km" in r["question"]
    assert "90 km/h" in r["question"]


def test_train_hindi():
    r = analyse("एक ट्रेन 60 km/h की गति से 240 km जाती है। "
                "कितना समय लगेगा?")
    assert r["family"] == "speed_time_distance"
    assert "240 km" in r["question"]     # NOT the speed's 60
    assert "60 km/h" in r["question"]
    assert r["confirm"] is None


def test_train_unit_unclear_confirm():
    r = analyse("Train ki speed 60 hai, 300 km jaana hai, "
                "time nikalo")
    assert r is not None
    assert r["confirm"] is not None
    assert "km/h" in r["confirm"] and "m/s" in r["confirm"]


def test_train_missing_distance_placeholder():
    r = analyse("Ek train 60 km/h ki speed se jaati hai, "
                "time nikalo")
    assert r is not None
    assert "___" in r["question"]
    assert "istance" in (r["confirm"] or "")


def test_pole_form_en_and_hinglish():
    r = analyse("A train 240 m long crosses a pole in "
                "12 seconds. Find the speed of the train.")
    assert r["family"] == "train_pole"
    assert "240 m" in r["question"]
    assert "12 seconds" in r["question"]
    r2 = analyse("Ek train 240 m lambi hai ek pole ko "
                 "12 seconds me paar karti hai speed nikalo")
    assert r2["family"] == "train_pole"
    assert "Speed nikalo" in r2["question"]


# ------------------------------------------------------- HCF / LCM

def test_hcf_lcm_all_languages():
    assert analyse("Find the HCF of 12 and 18")["question"] == \
        "Find the HCF of 12 and 18."
    assert analyse("12 और 18 का HCF ज्ञात कीजिए")["question"] == \
        "12 और 18 का HCF ज्ञात कीजिए।"
    assert analyse("Find the HCF of 12, 18 and 24")["question"] == \
        "Find the HCF of 12, 18 and 24."
    r = analyse("12 aur 18 ka LCM nikalo")
    assert "12" in r["question"] and "18" in r["question"]
    assert "LCM" in r["question"]


def test_hcf_missing_second_number():
    r = analyse("Find the HCF of 24")
    assert "___" in r["question"]
    assert r["confirm"] == ("The second number is not clear "
                            "in the photo — please fill it in.")


# ------------------------------------------------------ percentage

def test_percentage_forms():
    assert analyse("Find 15% of 200")["question"] == \
        "Find 15% of 200."
    assert analyse("A student scored 45 marks out of 50. "
                   "Find the percentage.")["question"] == \
        "A student scored 45 marks out of 50. " \
        "Find the percentage."
    # Hindi order: total first ("50 में से 45")
    assert analyse("एक छात्र ने 50 में से 45 अंक प्राप्त किए। "
                   "प्रतिशत ज्ञात कीजिए।")["question"] == \
        "50 में से 45 अंक मिले। प्रतिशत ज्ञात कीजिए।"
    assert analyse("What percent of 200 is 50?")["question"] == \
        "What percent of 200 is 50?"


def test_percentage_missing_base():
    r = analyse("Find 20% of")
    assert r["question"] == "Find 20% of ___."
    assert "number is not clear" in r["confirm"]


# -------------------------------------------------- simple interest

def test_simple_interest_full_and_missing():
    r = analyse("Find the simple interest on Rs 1000 at 5% "
                "per annum for 2 years")
    assert r["question"] == ("Find the simple interest on "
                             "Rs 1000 at 5% per annum for "
                             "2 years.")
    assert r["confirm"] is None
    r = analyse("5000 रुपये पर 6% वार्षिक दर से 3 वर्षों का "
                "साधारण ब्याज ज्ञात कीजिए")
    assert r["question"] == ("5000 रुपये पर 6% वार्षिक दर से "
                             "3 वर्षों का साधारण ब्याज "
                             "ज्ञात कीजिए।")
    r = analyse("Find simple interest on Rs 5000 at 6% "
                "per annum")
    assert "___ years" in r["question"]
    assert r["confirm"] == ("The time is not clear in the "
                            "photo — please fill it in.")


def test_two_unclear_slots_still_one_line():
    """Ambiguous speed AND missing distance -> ONE line,
    naming the FIRST unclear thing (the speed), never a
    list of questions."""
    r = analyse("Ek train 60 km/h ki speed se jaati hai, "
                "speed 80 bhi likha hai, time nikalo")
    assert r is not None
    assert "___" in r["question"]            # distance blank
    assert r["confirm"] == "Speed 60 hai ya 80?"
    assert "\n" not in r["confirm"]


# ----------------------------------------------------- mensuration

def test_mensuration_forms():
    assert analyse("Find the area of a rectangle whose "
                   "length is 12 cm and breadth is 8 cm"
                   )["question"] == \
        "Find the area of a rectangle whose length is 12 cm " \
        "and breadth is 8 cm."
    assert analyse("एक वृत्त की त्रिज्या 7 cm है। उसका "
                   "क्षेत्रफल ज्ञात कीजिए।")["question"] == \
        "एक वृत्त की त्रिज्या 7 cm है। उसका क्षेत्रफल " \
        "ज्ञात कीजिए।"
    assert analyse("Find the perimeter of a square whose "
                   "side is 5 cm")["question"] == \
        "Find the perimeter of a square whose side is 5 cm."
    assert analyse("Find the perimeter of a triangle whose "
                   "sides are 3 cm, 4 cm and 5 cm")["question"] == \
        "Find the perimeter of a triangle whose sides are " \
        "3 cm, 4 cm and 5 cm."


def test_mensuration_missing_dimension():
    r = analyse("Find the area of a rectangle length 12 cm")
    assert "___" in r["question"]
    assert "breadth is not clear" in r["confirm"]


# ------------------------------------------------------------ ratio

def test_ratio_forms():
    assert analyse("Divide Rs 1000 in the ratio 2:3"
                   )["question"] == \
        "Divide Rs 1000 in the ratio 2:3."
    # amount AFTER the currency word (OCR reading order)
    assert analyse("1000 rupaye ko 2:3 ke ratio me baanto"
                   )["question"] == \
        "1000 rupaye ko 2:3 ke ratio me baanto."
    assert analyse("₹600 को 1:2 के अनुपात में बाँटिए"
                   )["question"] == \
        "600 रुपये को 1:2 के अनुपात में बाँटिए।"
    assert analyse("Find the ratio of 12 and 18")["question"] == \
        "Find the ratio of 12 and 18."


# ----------------------------------------------------------- average

def test_average_forms():
    assert analyse("Find the average of 10, 20, 30 and 40"
                   )["question"] == \
        "Find the average of 10, 20, 30 and 40."
    assert analyse("5, 10, 15, 20, 25 का औसत ज्ञात कीजिए"
                   )["question"] == \
        "5, 10, 15, 20 और 25 का औसत ज्ञात कीजिए।"
    assert analyse("Find the average of 10 and 20") is None


# ----------------------------------------------------------- algebra

def test_algebra_garble_digit_confirmed():
    r = analyse("Solve 3x + S = 20")
    assert r["question"] == "Solve: 3x + 5 = 20"
    assert r["confirm"] == "In the equation, is that number 5?"
    r = analyse("Find the value of x if x + B = 12")
    assert r["question"] == "Solve for x: x + 8 = 12"
    assert r["confirm"] == "In the equation, is that number 8?"


def test_algebra_two_variables_untouched():
    r = analyse("Solve x + y = 10")
    assert r["question"] == "Solve: x + y = 10"
    assert r["confirm"] is None


# ------------------------------------------- no match -> raw fallback

@pytest.mark.parametrize("text", [
    "What is the capital of France?",
    "Draw a neat diagram of the human heart and label it",
    "asdf 123 qwer 456 zxcv",
    "Explain the process of photosynthesis in detail with "
    "the help of a labelled diagram and also mention the "
    "factors affecting it in the summer season of the year",
    "",
    "   ",
])
def test_no_family_match_returns_none(text):
    assert analyse(text) is None


# --------------------------------- numbers are never invented (rule d)

@pytest.mark.parametrize("raw", [
    "A traln travels 240 km at a speed of 60 km/h. Speed was "
    "80 km/h also. Find the time taken.",
    "Find the HCF of 12 and 18",
    "Find 15% of 200",
    "Find the simple interest on Rs 1000 at 5% per annum "
    "for 2 years",
    "Divide Rs 1000 in the ratio 2:3",
    "Find the average of 10, 20, 30 and 40",
    "Find the area of a rectangle whose length is 12 cm "
    "and breadth is 8 cm",
    "Solve 3x + S = 20",
])
def test_reconstruction_numbers_come_from_the_read(raw):
    r = analyse(raw)
    assert r is not None
    src = set(re.findall(r"\d+(?:\.\d+)?", raw))
    if "S" in raw:      # the one sanctioned garble-digit fix
        src.add("5")
    got = set(re.findall(r"\d+(?:\.\d+)?", r["question"]))
    assert got <= src, (raw, r["question"])


# ------------------------------------------------ /photo-fix route

def test_photo_fix_reconstructs_and_never_solves(client,
                                                  monkeypatch):
    import app as app_module
    _signup(client)

    def _boom(*a, **k):
        raise AssertionError("photo-fix must never solve")

    monkeypatch.setattr(app_module, "solve_question", _boom)
    r = client.post("/photo-fix", json={
        "text": "A traln travels 240 km at a speed of "
                "60 km/h. Speed was 80 km/h also. Find the "
                "time taken."})
    assert r.status_code == 200
    d = r.get_json()
    assert d["reconstructed"] is True
    assert d["question"] == ("How long will a train take to "
                             "travel 240 km at a speed of "
                             "60 km/h?")
    assert d["confirm"] == "Is the speed 60 or 80?"
    with client.session_transaction() as sess:
        assert "last_result" not in sess
        assert "last_question" not in sess


def test_photo_fix_no_match_is_raw_fallback(client):
    r = client.post("/photo-fix", json={
        "text": "What is the capital of France?"})
    assert r.get_json() == {"ok": True, "reconstructed": False}


def test_photo_fix_empty(client):
    r = client.post("/photo-fix", json={"text": "   "})
    assert r.get_json() == {"ok": False, "code": "empty"}


# ------------------------------------- /photo-ocr prefill contract

_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _fake_outcome(text, confidence):
    import ocr
    return ocr.OcrOutcome(text, confidence, "fake-backend")


def _post_photo(client):
    return client.post(
        "/photo-ocr",
        data={"file": (io.BytesIO(_PNG), "q.png")},
        content_type="multipart/form-data")


def test_photo_ocr_low_confidence_gains_prefill(client,
                                                monkeypatch):
    import app as app_module
    _signup(client)
    monkeypatch.setattr(
        app_module.ocr, "ocr_image",
        lambda data: _fake_outcome(
            "A traln travels 240 km at a speed of 60 km/h. "
            "Speed was 80 km/h also. Find the time taken.", 42.0))
    d = _post_photo(client).get_json()
    assert d["low_confidence"] is True
    assert d["prefill"] == ("How long will a train take to "
                            "travel 240 km at a speed of "
                            "60 km/h?")
    assert d["confirm"] == "Is the speed 60 or 80?"
    assert d["text"]          # the raw read still rides along


def test_photo_ocr_low_confidence_no_match_no_prefill(
        client, monkeypatch):
    import app as app_module
    _signup(client)
    monkeypatch.setattr(
        app_module.ocr, "ocr_image",
        lambda data: _fake_outcome(
            "Blah blah no maths here at all", 30.0))
    d = _post_photo(client).get_json()
    assert d["low_confidence"] is True
    assert "prefill" not in d and "confirm" not in d


def test_photo_ocr_confident_read_unchanged(client, monkeypatch):
    """Clean/good reads: Wave 126 behaviour byte-identical —
    no photofix fields are added at all."""
    import app as app_module
    _signup(client)
    monkeypatch.setattr(
        app_module.ocr, "ocr_image",
        lambda data: _fake_outcome("Find the HCF of 12 and 18",
                                    95.0))
    d = _post_photo(client).get_json()
    assert d["low_confidence"] is False
    assert "prefill" not in d and "confirm" not in d
    assert d["text"] == "Find the HCF of 12 and 18"


# ------------------------------------------------------- page wiring

def test_page_wiring_wave137():
    assert "function ocrFixAndShow" in INDEX
    assert '"/photo-fix"' in INDEX
    assert "function ocrShowReconstruction" in INDEX
    assert "d.prefill || d.text" in INDEX
    # weak reads route through the analysis before the raw show
    assert "ocrFixAndShow(text);" in INDEX
    # Wave 126 pins still intact
    assert "function ocrShowForCheck" in INDEX
    assert "say(L.js_photo_check)" in INDEX
    assert "function ocrDeliverRead" in INDEX


def test_reconstruction_is_never_auto_submitted():
    """The fix path may only FILL the composer — submitting
    stays the student's own press of Solve."""
    body = INDEX[INDEX.index("function ocrFixAndShow"):
                 INDEX.index("function ocrDeliverRead")]
    assert "sendQuestionText" not in body
    assert "photoForm.submit" not in body
    assert "ocrShowForCheck" in body      # raw fallback kept


def test_wave137_static_pins():
    assert "style.css?v=61" in SW
    assert "ganitra-static-v38" in SW


# --------------------------- rebuilt questions solve when SENT by the
# student himself (the confirm-then-solve contract, end to end)

def test_rebuilt_questions_solve_via_photo_solve(client):
    from app import solve_failed
    _signup(client)
    cases = [
        ("A traln travels 240 km at a speed of 60 km/h. "
         "Speed was 80 km/h also. Find the time taken.", "4"),
        ("12 और 18 का HCF ज्ञात कीजिए", "6"),
        ("Find the simple interest on Rs 1000 at 5% per annum "
         "for 2 years", "100"),
    ]
    for raw, want in cases:
        fixed = analyse(raw)
        assert fixed is not None
        page = client.post("/photo-solve", data={
            "question": fixed["question"], "source": "photo"})
        assert page.status_code == 200
        with client.session_transaction() as sess:
            result = sess["last_result"]
        assert not solve_failed(fixed["question"], result)
        assert want in str(result.get("answer")), \
            (fixed["question"], result.get("answer"))
