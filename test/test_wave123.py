"""Wave 123: ON-DEMAND steps & options (Suraj's revision of
Wave 122, 17 Nov 2026: "Step or niche more options hai aise
nhi dene — agar woh chat par bolta hai jabhi do, yaa jis
type kaa question hai us hisab se ans do, nhi toh simple
plane rahane do").

Step labels and the follow-up chips are DEFAULT OFF:

- Labels ("Step 1" / "चरण 1") appear only when the student
  asked for steps in the chat (detect_steps_request) or the
  question is a proof / derivation (is_proof_type) — and
  even then only on a card with 2+ solving lines (the
  Wave-122 rule, client-side).
- Chips appear only when the triggering message itself
  carries more / continue intent (detect_more_intent), or
  the answer continues a chip thread (followup=True). All
  Wave-122 chip conditions still hold on top (solved only,
  latest turn only, never home / not-found / concept /
  history / advice).
- Everything else renders simple plain: unnumbered solving
  lines + the answer (boxed when solved — Wave 122's
  feature 2, unchanged), the streaming reveal unchanged.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(
    encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

SIGNUP = {"name": "W123 Tester", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w123-test-pass"}


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code in (200, 302)
    return c


def _solve(client, question, **extra):
    payload = {"question": question}
    payload.update(extra)
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


# --- The detectors (unit batteries) ---------------------------

def test_detect_steps_request_battery():
    from langdetect_local import detect_steps_request
    asked = [
        "step by step batao",
        "Find the HCF of 12 and 18 step by step",
        "stepwise solve karo",
        "step karke batao",
        "ek ek step samjhao",
        "saare steps dikhao",
        "steps me batao",
        "step se samjhao",
        "step batao",
        "steps chahiye",
        "solve with steps",
        "steps ke saath samjhao",
        "show all the steps",
        "स्टेप बाय स्टेप बताओ",
        "चरण दर चरण समझाओ",
        "क्रम से समझाओ",
    ]
    plain = [
        "Find the HCF of 12 and 18",
        "step function kya hai",
        "What is a step function?",
        "one step me answer do",       # "in one step" = content
        "संख्याओं को आरोही क्रम में लिखो",  # ordering, not steps
        "12 aur 18 ka HCF nikalo",
        "footsteps batao",
        "",
    ]
    for text in asked:
        assert detect_steps_request(text) is True, text
    for text in plain:
        assert detect_steps_request(text) is False, text


def test_detect_more_intent_battery():
    from followups import detect_more_intent
    more = [
        "HCF aur example ke saath samjhao",   # Suraj's MUST case
        "give one more example",
        "ek aur example do",
        "ek test do",
        "practice karni hai",
        "abhyas karna hai",
        "aur samjhao",
        "samjha do isko",
        "explain this",
        "revision karna hai",
        "dusra example do",
        "another example",
        "एक और उदाहरण दो",
        "अभ्यास के सवाल दो",
        "aur batao",
    ]
    plain = [
        "Find the HCF of 12 and 18",          # Suraj's MUST-NOT
        "12 aur 18 ka HCF nikalo",            # bare aur = "and"
        "HCF nikalo aur LCM bhi",             # bare aur again
        "What is 5 more than 3?",             # "more than"
        "divisibility test se 144 check karo",  # a topic name
        "Find the latest value",              # no word boundary
        "240 ka 15 percent kitna hoga",
        "",
    ]
    for text in more:
        assert detect_more_intent(text) is True, text
    for text in plain:
        assert detect_more_intent(text) is False, text


def test_is_proof_type_battery():
    from followups import is_proof_type
    assert is_proof_type({"fallback_kind": "proof"}, "x")
    assert is_proof_type({"op": "proof_identity"}, "x")
    assert is_proof_type({}, "Prove that root 5 is irrational")
    assert is_proof_type({}, "सिद्ध करो कि √2 अपरिमेय है")
    assert is_proof_type({}, "Show that 3 + 2 = 5")
    assert is_proof_type({}, "Derive the area formula")
    assert not is_proof_type({}, "Find the HCF of 12 and 18")
    assert not is_proof_type({"fallback_kind": "concept"},
                             "What is a prime number?")


# --- End to end: the five pinned behaviours -------------------

def test_plain_compute_is_simple_plain(client):
    # (1) Plain compute question: solved (so the Wave-122
    # box condition holds), but NO labels gate, NO chips.
    from followups import is_solved_result
    d = _solve(client, "Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["result"]["answer"] == "6"
    assert len(d["result"]["steps"]) >= 2  # would have numbered in 122
    assert is_solved_result(d["result"]) is True
    assert d["w122"]["labels"] is False
    assert d["w122"]["chips"] == []


def test_steps_ask_turns_labels_on(client):
    # (2) The same question + "step by step batao": labels ON,
    # chips still OFF (batao is not a more-intent word).
    d = _solve(client, "Find the HCF of 12 and 18, step by step batao")
    assert d["ok"] is True
    assert d["result"]["answer"] == "6"
    assert d["w122"]["labels"] is True
    assert d["w122"]["step_label"] == "Step"
    assert d["w122"]["chips"] == []


def test_proof_turns_labels_on_without_asking(client):
    # (3) A proof question: labels ON with no steps ask,
    # in English and in Hindi.
    d = _solve(client, "Prove that root 5 is irrational")
    assert d["ok"] is True
    assert d["result"].get("fallback_kind") == "proof"
    assert d["w122"]["labels"] is True
    assert d["w122"]["chips"] == []
    d2 = _solve(client, "सिद्ध करो कि √2 अपरिमेय संख्या है")
    assert d2["ok"] is True
    assert d2["result"].get("fallback_kind") == "proof"
    assert d2["w122"]["labels"] is True
    assert d2["w122"]["step_label"] == "चरण"


def test_more_intent_turns_chips_on(client):
    # (4) An "aur example ke saath samjhao" ask: chips ON on
    # its (solved) answer; labels stay OFF (no steps asked).
    d = _solve(client,
               "Find the HCF of 12 and 18 aur example ke saath samjhao")
    assert d["ok"] is True
    assert d["result"]["answer"] == "6"
    assert [c["kind"] for c in d["w122"]["chips"]] == [
        "example", "test", "simpler"]
    assert d["w122"]["labels"] is False
    # Hindi intent earns the Devanagari chip labels.
    d2 = _solve(client, "240 का 15% कितना होगा, एक और उदाहरण दो")
    assert d2["ok"] is True
    assert str(d2["result"]["answer"]).strip() == "36"
    assert d2["w122"]["chips"][0]["label"] == "एक और उदाहरण दो"


def test_chip_thread_keeps_its_chips(client):
    # A chip tap continues the more-thread: its answer keeps
    # chips even though the original ask was plain — and the
    # plain thread's label gate stays off on it.
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "Give one more example", followup="example",
               context_question="Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["result"].get("followup") == "example"
    assert [c["kind"] for c in d["w122"]["chips"]] == [
        "example", "test", "simpler"]
    assert d["w122"]["labels"] is False


def test_intent_does_not_override_the_wave122_conditions(client):
    # More-intent words on a CONCEPT ask: still no chips
    # (Wave 122: solved answers only).
    d = _solve(client, "HCF aur example ke saath samjhao")
    assert d["ok"] is True
    assert d["result"].get("fallback_kind") == "concept"
    assert d["w122"]["chips"] == []


def test_not_found_has_none_of_the_features(client):
    # (5) Not-found: unchanged — one plain line, no labels
    # gate, no chips (and the client never boxes it).
    d = _solve(client, "zxqw jklm asdfgh qwerty")
    result = d["result"]
    assert result.get("fallback_kind") == "not_found"
    assert result.get("plain_reply") is True
    assert d["w122"]["chips"] == []
    assert d["w122"]["labels"] is False


# --- Source pins ------------------------------------------------

def test_client_gates_labels_on_the_payload_flag():
    assert "data.w122.labels === true" in INDEX
    assert "boardSteps.length >= 2" in INDEX
    # The label itself still rides in the data attribute.
    assert 'li.setAttribute("data-w122-step"' in INDEX


def test_pins_bumped_for_wave123():
    assert "filename='style.css', v='58'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v35"' in SW
    assert '"/static/style.css?v=58"' in SW
