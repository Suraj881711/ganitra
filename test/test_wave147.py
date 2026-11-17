"""Wave 147 — "Pyar se baat": Ganitra's kind-tone layer.

Suraj's rule (17 Nov 2026): Ganitra always talks in good,
kind, loving language. A stuck student may swear or vent —
Ganitra never swears back, never scolds, never lectures:

- abuse/frustration RIDING WITH a real question: the abusive
  words are cleaned off and the CLEANED question is solved —
  the result is byte-identical to the polite question's
  result, and the abuse is never mentioned;
- abuse/frustration ALONE: ONE short kind line in the
  student's own language (EN / Hinglish / Hindi), door left
  open — never the not-found line, never a lecture;
- anger about the last answer ("tumne galat jawab diya"):
  one short apology line and the same answer served once
  more, so the student can point at the doubted step (the
  Wave-96 machinery then takes over);
- a substantial but questionless remainder (word soup with a
  stray venting word) flows on completely unchanged — Wave
  92's gibberish pin is the authority there;
- no abuse/frustration -> the layer is invisible: analyse is
  untriggered and the pre-pass returns None, which is the
  mechanism that keeps every normal answer byte-identical.

False-positive discipline is pinned hard: word-boundary
matching keeps "class"/"pass"/"assignment" innocent, and
lookalike innocents — "kamini" (a name), "maa ki umar" (an
ages problem), "kutta" (a dog), "saala" (a relative) — never
trigger.
"""
import pytest

from tone import (analyse, apology_line, kind_line,
                  kind_result, prepass)

SIGNUP = {"name": "W147 User", "class": "8", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w147-pass"}

KIND_ROMAN = ("Koi baat nahi — hota hai. 😊 Chalo phir se "
              "try karte hain: apna maths ka sawal bhejo, "
              "hum saath me step-by-step hal karenge.")
KIND_DEV = ("कोई बात नहीं — होता है। 😊 चलिए फिर से कोशिश "
            "करते हैं: अपना गणित का सवाल भेजिए, हम साथ में "
            "चरण-दर-चरण हल करेंगे।")
KIND_EN = ("No worries — it happens. 😊 Take a breath and "
           "send your maths question once more; we'll solve "
           "it together, step by step.")
APOLOGY_ROMAN = ("Sorry 🙏 Wahi jawab ek baar phir dikha "
                 "raha hoon — jo step galat lage, uska "
                 "number bata do, main use samjha dunga.")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


@pytest.fixture()
def signed(client):
    client.post("/signup", data=SIGNUP)
    return client


def solve(client, question):
    return client.post("/api/solve",
                       json={"question": question}).get_json()


def fresh_signed(application_client, name):
    application_client.post(
        "/signup", data={**SIGNUP, "name": name})
    return application_client


# ---------------------------------------------------------------------------
# Detection + cleaning (unit level)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("msg,cleaned", [
    ("abe chutiya, 12 aur 18 ka HCF batao",
     "12 aur 18 ka HCF batao"),
    ("stupid app, solve 3x + 5 = 20", "solve 3x + 5 = 20"),
    ("12 aur 18 ka HCF batao bekar app",
     "12 aur 18 ka HCF batao"),
    ("तुम बहुत बेकार हो, 12 और 18 का HCF बताओ",
     "12 और 18 का HCF बताओ"),
    ("damn, find the area of a circle with radius 7",
     "find the area of a circle with radius 7"),
    ("2+2 batao chutiya", "2+2 batao"),
    ("what is a prime number, bekar app",
     "what is a prime number"),
])
def test_cleaning_yields_the_polite_question(msg, cleaned):
    a = analyse(msg)
    assert a["triggered"] and a["has_question"]
    assert a["cleaned"] == cleaned
    assert prepass(msg) == {"question": cleaned}


@pytest.mark.parametrize("msg", [
    "tum bekar ho",
    "tum bahut bekar ho",
    "you are useless",
    "shut up",
    "bakwaas hai ye app",
    "kuch nahi aata tumhe",
    "i hate maths",
    "तुम बेकार हो",
    "चूतिया कहीं के",
    "what a bakwaas app",
    "what the fuck",
])
def test_abuse_only_gets_the_kind_line(msg):
    out = prepass(msg)
    assert out is not None and "result" in out
    r = out["result"]
    assert r["fallback_kind"] == "kind"
    assert r["plain"] and r["plain_reply"]
    assert r["steps"] == []


def test_kind_lines_are_the_pinned_texts():
    assert kind_line("tum bekar ho") == KIND_ROMAN
    assert kind_line("तुम बेकार हो") == KIND_DEV
    assert kind_line("you are useless") == KIND_EN
    assert kind_result("tum bekar ho")["answer"] == KIND_ROMAN
    assert apology_line("tumne galat jawab diya") == \
        APOLOGY_ROMAN


@pytest.mark.parametrize("msg", [
    # substring traps: word boundaries keep these innocent
    "class 10 ka syllabus batao",
    "pass hone ke liye kitne marks chahiye",
    "assignment ke 5 sawal batao",
    "median aur mode me kya antar hai",
    # lookalike innocents: a name, a relative, an animal,
    # a mother's age — none of these are abuse
    "kamini ke marks 40, 50, 60 hai, average batao",
    "meri maa ki umar mere se dugni hai",
    "ek kutta aur 2 billi hai, kul kitne janwar hai",
    "mere saala ki umar 30 saal hai",
    "2+2 batao",
    "solve 3x + 5 = 20",
    "hello",
    "step 2 galat hai",
    "ye step samajh nahi aaya",
])
def test_false_positive_battery_never_triggers(msg):
    a = analyse(msg)
    assert not a["triggered"], msg
    assert prepass(msg) is None


def test_word_soup_with_stray_venting_flows_unchanged():
    # Wave 92's pin, at the tone layer: the soup contains
    # "bakwaas" but is not a frustrated student addressing
    # Ganitra — it must reach the normal flow untouched and
    # earn the honest not-found line there.
    assert prepass("ulta seedha bakwaas km per hour "
                   "ghante lagenge") is None


def test_anger_detection_is_answer_anchored():
    assert analyse("tumne galat jawab diya")["anger"]
    assert analyse("ye jawab galat hai")["anger"]
    assert analyse("wrong answer दिया तुमने")["anger"] or \
        analyse("tumne wrong answer diya")["anger"]
    # a step complaint is NOT answer anger (Wave 96's turf)
    assert not analyse("step 2 galat hai")["anger"]
    assert not analyse("dusra step galat lag raha hai")["anger"]


# ---------------------------------------------------------------------------
# Through the real chat path (/api/solve)
# ---------------------------------------------------------------------------

def test_rude_question_answer_identical_to_polite(client):
    polite_client = fresh_signed(client, "W147 Polite")
    rude_client = client.application.test_client()
    fresh_signed(rude_client, "W147 Rude")
    polite = solve(polite_client, "12 aur 18 ka HCF batao")
    rude = solve(rude_client,
                 "abe chutiya, 12 aur 18 ka HCF batao")
    assert rude["ok"] is True
    assert rude["result"] == polite["result"]
    assert rude["result"]["answer"] == "6"


def test_rude_english_question_identical_to_polite(client):
    polite_client = fresh_signed(client, "W147 Polite2")
    rude_client = client.application.test_client()
    fresh_signed(rude_client, "W147 Rude2")
    polite = solve(polite_client, "solve 3x + 5 = 20")
    rude = solve(rude_client, "stupid app, solve 3x + 5 = 20")
    assert rude["result"] == polite["result"]
    assert rude["result"]["answer"] == "x = 5"


def test_rude_hindi_question_identical_to_polite(client):
    polite_client = fresh_signed(client, "W147 Polite3")
    rude_client = client.application.test_client()
    fresh_signed(rude_client, "W147 Rude3")
    polite = solve(polite_client, "12 और 18 का HCF बताओ")
    rude = solve(rude_client,
                 "तुम बहुत बेकार हो, 12 और 18 का HCF बताओ")
    assert rude["result"] == polite["result"]


@pytest.mark.parametrize("msg,line", [
    ("tum bekar ho", KIND_ROMAN),
    ("तुम बेकार हो", KIND_DEV),
    ("you are useless", KIND_EN),
    ("kuch nahi aata tumhe", KIND_ROMAN),
    ("bakwaas hai ye app", KIND_ROMAN),
])
def test_abuse_only_through_chat(signed, msg, line):
    data = solve(signed, msg)
    assert data["ok"] is True
    r = data["result"]
    assert r["fallback_kind"] == "kind"
    assert r["answer"] == line
    assert r["plain"] and r["plain_reply"]


def test_anger_after_solve_apologises_and_reserves(signed):
    base = solve(signed, "solve 3x + 5 = 20")
    assert base["result"]["answer"] == "x = 5"
    data = solve(signed, "tumne galat jawab diya")
    assert data["ok"] is True
    assert data["intro"] == APOLOGY_ROMAN
    assert data["result"] == base["result"]
    # ...and the doubt machinery still owns the next turn:
    follow = solve(signed, "dusra step samjhao")
    assert follow["ok"] is True
    assert follow.get("intro") != APOLOGY_ROMAN


def test_app_anger_after_solve_apologises_and_reserves(signed):
    base = solve(signed, "solve 3x + 5 = 20")
    data = solve(signed, "ye app bekar hai")
    assert data["intro"] == APOLOGY_ROMAN
    assert data["result"] == base["result"]


def test_anger_with_no_previous_answer_gets_kind_line(signed):
    data = solve(signed, "tumne galat jawab diya")
    assert data["result"]["fallback_kind"] == "kind"
    assert data["result"]["answer"] == KIND_ROMAN


def test_anger_with_a_new_question_solves_the_question(signed):
    solve(signed, "solve 3x + 5 = 20")
    data = solve(signed,
                 "tumne galat jawab diya, ab 12 aur 18 ka "
                 "HCF batao")
    assert data["ok"] is True
    assert data["result"]["answer"] == "6"
    assert data.get("intro") != APOLOGY_ROMAN


def test_step_complaint_stays_with_doubt(signed):
    base = solve(signed, "solve 3x + 5 = 20")
    data = solve(signed, "step 2 galat hai")
    # NOT the apology re-serve: the doubt layer answers.
    assert data.get("intro") != APOLOGY_ROMAN
    assert data["result"] != base["result"] or \
        data["result"].get("fallback_kind") != \
        base["result"].get("fallback_kind")


def test_normal_questions_untouched(signed):
    data = solve(signed, "12 aur 18 ka HCF batao")
    assert data["result"]["answer"] == "6"
    assert data["result"].get("fallback_kind") != "kind"
    data = solve(signed, "What is the capital of France?")
    assert data["result"]["fallback_kind"] == "nonmaths"


# ---------------------------------------------------------------------------
# Tone pins: nothing Ganitra says back is ever abusive or blaming
# ---------------------------------------------------------------------------

_BANNED_OUTPUT = (
    "chutiya", "madarchod", "behenchod", "bhosdika", "gandu",
    "randi", "harami", "kamina", "bewakoof", "nalayak",
    "idiot", "moron", "stupid", "shut up", "useless",
    "चूतिया", "मादरचोद", "बहनचोद", "हरामी", "कमीना",
    "बेवकूफ़", "नालायक", "shame", "careless", "lapaarwah",
    "तुम्हारी गलती", "tumhari galti", "your fault",
)


def test_no_response_ever_mirrors_abuse(signed):
    solve(signed, "solve 3x + 5 = 20")
    battery = [
        "abe chutiya, 12 aur 18 ka HCF batao",
        "tum bekar ho",
        "तुम बेकार हो",
        "you are useless",
        "tumne galat jawab diya",
        "ye app bekar hai",
        "kuch nahi aata tumhe, madarchod",
        "bakwaas hai ye app",
    ]
    for msg in battery:
        data = solve(signed, msg)
        texts = [str(data.get("result", {}).get("answer", "")),
                 str(data.get("intro") or "")]
        for text in texts:
            low = text.lower()
            for banned in _BANNED_OUTPUT:
                assert banned not in low, (msg, banned, text)
