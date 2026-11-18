"""Wave 122: the four Wave-118 decision items, each CONDITIONAL
(Suraj, 17 Nov 2026: "Charo ko done karo or condition ke hisab
se ans dena").

1. Streaming reveal — fresh in-page turns only (the Wave-118
   arming flag); restored history / print / classic page land
   whole; reduced-motion lands whole; any tap finishes it.
2. Final-answer BOX — only a solved maths answer (the exact
   predicate followups.is_solved_result, mirrored in the chat
   JS); not-found / non-maths / greeting / concept / history /
   advice / error cards keep the plain bold line. This flips
   the Wave-24 plain-line rule BY SURAJ'S APPROVAL, under this
   one condition only (the two jsdom bg pins in
   test_answer_sequence.py / test_wave25_fixes.py were flipped
   deliberately with it).
3. Follow-up chips — only under a solved answer, only on the
   LATEST live answer, labels in the answer's language, served
   per-answer by the server (``w122.chips``); a chip tap posts
   the kind + original question as hidden context and
   followups.py answers deterministically. The home/empty
   state stays chip-free (Wave 69 stands).
4. "Step N" labels — only when a card shows 2+ solving lines,
   via a data attribute + CSS ::before; the step TEXT is never
   touched (copy / narration / saved chats byte-identical),
   and the Wave-120 removal of the overall heading stands.

WAVE 123 FLIPS (Suraj's on-demand revision, 17 Nov 2026):
features 3 and 4 are default-OFF now — chips need a
more-intent ask (or a chip thread), labels need a steps
request or a proof. The payload / DOM tests below were
updated to the new gates (each flip is marked in place);
test_wave123.py pins the new behaviour end to end.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(
    encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

SIGNUP = {"name": "W122 Tester", "class": "10", "board": "CBSE",
          "goal": "Doctor", "hobby": "Cricket",
          "favourite": "Pizza", "password": "w122-test-pass"}


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


# --- The solved predicate (server mirror of the chat JS) -----

def test_is_solved_result_battery():
    from followups import is_solved_result
    solved = [
        {"answer": "6", "steps": ["a", "b"]},                    # solver
        {"answer": "6", "fallback_kind": "bank"},                # bank
        {"answer": "6", "fallback_kind": "salvage"},             # salvage
        {"answer": "6", "fallback_kind": "gemini",
         "fallback": True},                                      # AI leg
        {"answer": "6", "fallback_kind": "groq", "fallback": True},
        {"answer": "6", "fallback_kind": "openrouter",
         "fallback": True},
        {"answer": "QED", "fallback_kind": "proof"},             # proof
    ]
    not_solved = [
        {"answer": "Answer not found", "fallback_kind": "not_found",
         "plain": True, "plain_reply": True},
        {"answer": "x", "fallback_kind": "concept"},
        {"answer": "x", "fallback_kind": "history"},
        {"answer": "x", "fallback_kind": "advice"},
        {"answer": "x", "fallback_kind": "step_check"},
        {"answer": "x", "fallback_kind": "followup_test"},
        {"answer": "x", "op": "explain_step"},
        {"answer": "x", "op": "check_steps"},
        {"answer": "x", "op": "error"},
        {"answer": "Hello!", "plain_reply": True},
        {"answer": "", "steps": ["a"]},
        {"steps": ["a"]},
        None,
        "not a dict",
    ]
    for result in solved:
        assert is_solved_result(result) is True, result
    for result in not_solved:
        assert is_solved_result(result) is False, result


def test_w122_payload_flavours():
    from followups import w122_payload
    result = {"answer": "6", "steps": ["12 = 2 × 3", "18 = 2 × 9"]}
    # WAVE 123 FLIP: chips now need a more-intent ask, so the
    # flavour calls carry one in ask_text (the chip LABELS
    # themselves are unchanged in all three flavours).
    en = w122_payload(
        result, lang="en", question="HCF of 12, 18",
        ask_text="HCF of 12 and 18, give one more example")
    assert en["step_label"] == "Step"
    assert en["labels"] is False  # no steps asked, not a proof
    assert [c["label"] for c in en["chips"]] == [
        "Give one more example",
        "Give a small test on this topic",
        "Explain more simply"]
    dev = w122_payload(
        result, lang="hi", lang_request="hi", question="HCF batao",
        ask_text="HCF batao, ek aur udaharan do")
    assert dev["step_label"] == "चरण"
    assert dev["chips"][0]["label"] == "एक और उदाहरण दो"
    assert dev["chips"][1]["label"] == "इसी topic का छोटा test दो"
    assert dev["chips"][2]["label"] == "और आसान में समझाओ"
    roman = w122_payload(
        result, lang="hi", lang_request="hinglish",
        question="HCF batao",
        ask_text="HCF batao, ek aur example do")
    assert roman["step_label"] == "Step"
    assert roman["chips"][0]["label"] == "Ek aur example do"
    assert roman["chips"][1]["label"] == "Isi topic ka chhota test do"
    assert roman["chips"][2]["label"] == "Aur asaan me samjhao"
    # WAVE 123: a plain ask of the same solved result earns
    # NO chips and NO labels — the answer stays simple plain.
    plain = w122_payload(result, lang="en",
                         question="HCF of 12, 18")
    assert plain["chips"] == []
    assert plain["labels"] is False
    # ...and a steps ask turns the label gate on (word only —
    # the 2+ rule still lives in the client).
    stepped = w122_payload(
        result, lang="en", question="HCF of 12, 18",
        ask_text="HCF of 12 and 18, step by step batao")
    assert stepped["labels"] is True
    # A non-solved result never carries chips, in any flavour.
    nf = w122_payload({"answer": "Answer not found",
                       "fallback_kind": "not_found",
                       "plain": True, "plain_reply": True},
                      lang="en", question="zzz")
    assert nf["chips"] == []
    assert nf["labels"] is False


# --- /api/solve payloads: chips only under solved answers ----

def test_plain_solved_answer_has_no_chips_no_labels(client):
    # WAVE 123 FLIP (was test_solved_answer_carries_chips_en):
    # a plain solved question now stays simple plain — no
    # chips, labels gate off. The box condition (solved) is
    # unchanged; test_wave123.py pins the intent variants.
    d = _solve(client, "Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["result"]["answer"] == "6"
    assert d["w122"]["step_label"] == "Step"
    assert d["w122"]["chips"] == []
    assert d["w122"]["labels"] is False


def test_hindi_plain_answer_has_no_chips(client):
    # WAVE 123 FLIP (was
    # test_hindi_answer_carries_devanagari_chips): the plain
    # Hindi ask earns no chips now; the Devanagari chip
    # labels themselves are pinned in
    # test_w122_payload_flavours and test_wave123.py.
    d = _solve(client, "240 का 15% कितना होगा?")
    assert d["ok"] is True
    assert str(d["result"]["answer"]).strip() == "36"
    assert d["w122"]["step_label"] == "चरण"
    assert d["w122"]["chips"] == []
    assert d["w122"]["labels"] is False


def test_hinglish_plain_answer_has_no_chips(client):
    # WAVE 123 FLIP (was
    # test_hinglish_answer_carries_roman_chips): same flip —
    # flavour and label word are unchanged, chips now wait
    # for a more-intent ask.
    d = _solve(client, "240 ka 15 percent kitna hoga")
    assert d["ok"] is True
    assert str(d["result"]["answer"]).strip() == "36"
    assert d["w122"]["flavour"] == "roman"
    assert d["w122"]["chips"] == []
    assert d["w122"]["step_label"] == "Step"
    assert d["w122"]["labels"] is False


def test_concept_answer_has_no_chips(client):
    d = _solve(client, "What is a prime number?")
    assert d["ok"] is True
    assert d["result"].get("fallback_kind") == "concept"
    assert d["w122"]["chips"] == []


def test_history_answer_has_no_chips(client):
    d = _solve(client, "Zero kisne invent kiya?")
    assert d["ok"] is True
    assert d["result"].get("fallback_kind") == "history"
    assert d["w122"]["chips"] == []


def test_not_found_has_no_chips_and_stays_one_line(client):
    d = _solve(client, "zxqw jklm asdfgh qwerty")
    result = d["result"]
    assert result.get("fallback_kind") == "not_found"
    assert result.get("plain_reply") is True
    assert result.get("steps") == []
    assert d["w122"]["chips"] == []


def test_greeting_has_no_chips(client):
    d = _solve(client, "hello")
    assert d["w122"]["chips"] == []


# --- Follow-ups end to end ------------------------------------

def test_followup_example_solves_a_new_question(client):
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "Give one more example", followup="example",
               context_question="Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["followup_note"] == "One more example:"
    result = d["result"]
    assert result.get("followup") == "example"
    # A genuinely NEW worked example: different numbers, a real
    # solver answer, its own steps.
    assert result["answer"]
    assert len(result["steps"]) >= 2
    assert "19" in " ".join(result["steps"]) \
        or "20" in " ".join(result["steps"]) \
        or "13" in " ".join(result["steps"])


def test_followup_test_gives_three_questions_and_key(client):
    _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "Give a small test on this topic",
               followup="test",
               context_question="Find the HCF of 12 and 18")
    assert d["ok"] is True
    result = d["result"]
    assert result.get("fallback_kind") == "followup_test"
    assert len(result["steps"]) == 3
    assert result["steps"][0].startswith("Q1.")
    assert result["steps"][2].startswith("Q3.")
    # The key waits behind the bulb (the advice field), and a
    # test card itself earns no chips and no box.
    assert "Answer key" in (d["advice"] or "")
    assert d["w122"]["chips"] == []


def test_followup_simpler_explains_the_same_answer(client):
    first = _solve(client, "Find the HCF of 12 and 18")
    d = _solve(client, "Explain more simply", followup="simpler",
               context_question="Find the HCF of 12 and 18")
    assert d["ok"] is True
    assert d["followup_note"] == "A simpler way:"
    result = d["result"]
    assert result.get("followup") == "simpler"
    assert result["steps"]
    # The simpler take never invents a different final answer
    # family: it re-presents THIS answer (or explains its last
    # step, whose text carries the answer).
    joined = " ".join(result["steps"]) + str(result.get("answer"))
    assert "6" in joined


def test_followup_without_a_solved_answer_falls_through(client):
    # No previous solve in this session: the chip fields are
    # ignored and the label text is answered as an ordinary
    # message — never a fabricated follow-up.
    d = _solve(client, "Give one more example", followup="example",
               context_question="Find the HCF of 12 and 18")
    assert (d.get("result") or {}).get("followup") is None
    assert d.get("followup_note") is None


# --- Template / CSS source pins --------------------------------

def test_box_is_gated_on_the_solved_predicate():
    assert 'ans.classList.add("w122-answer-box")' in INDEX
    assert "if (result.answer && w122Solved(result))" in INDEX
    assert ".answer-big.w122-answer-box" in CSS
    assert "#fdf6e0" in CSS  # the warm cream tint
    # Print keeps the answer plain: no tint in print.
    print_block = CSS[CSS.index("@media print"):]
    assert ".answer-big.w122-answer-box" in print_block
    assert "background: none" in print_block


def test_step_labels_ride_in_a_data_attribute():
    assert 'li.setAttribute("data-w122-step"' in INDEX
    assert "boardSteps.length >= 2" in INDEX
    # WAVE 123: the 2+ rule now sits behind the server's
    # on-demand gate — no labels flag, no numbering.
    assert "data.w122.labels === true" in INDEX
    assert "li.textContent = step;" in INDEX  # text untouched
    assert "li[data-w122-step]::before" in CSS
    assert "content: attr(data-w122-step)" in CSS
    # The list itself stays unnumbered (no markers return).
    assert 'ol.style.listStyleType = "none";' in INDEX
    # Wave 120 stands: the overall heading never comes back.
    assert "steps_heading" not in INDEX
    assert 'sum.textContent = "";' in INDEX


def test_chips_are_live_turn_and_server_driven():
    assert 'className = "followup-chips"' in INDEX or \
        '"followup-chips"' in INDEX
    assert "w122LiveTurn && !data.offline && data.w122" in INDEX
    assert "data.w122.chips" in INDEX
    assert "sendFollowup(chip.kind, chip.label, question)" in INDEX
    # Hidden context: kind + original question ride in the body.
    assert "context_question: contextQuestion" in INDEX
    assert '"followup: kind"' in INDEX or \
        "followup: kind" in INDEX
    # Asking a new question retires the old chips.
    assert "clearFollowupChips();" in INDEX
    # Wave 69 stands: no example-question chips anywhere.
    assert 'id="example-chips"' not in INDEX
    assert 'class="example-chip"' not in INDEX


def test_reveal_is_fresh_turn_only_and_motion_safe():
    assert "function w122MaybeReveal(" in INDEX
    assert "if (w122LiveTurn) {" in INDEX
    assert "prefers-reduced-motion" in INDEX
    assert ".w122-wait" in CSS
    assert "window.setTimeout(step, 150)" in INDEX
    # The reveal hides lines with visibility (layout kept), so
    # MathJax typesets the real card before anything shows.
    assert "typeset.then(start, start)" in INDEX


def test_not_found_path_never_reaches_the_features():
    # The plain-reply branch returns before every Wave-122
    # card feature inside addAnswerBubble itself.
    body = INDEX[INDEX.index("function addAnswerBubble"):]
    plain_at = body.index('result.fallback_kind === "not_found"')
    box_at = body.index('ans.classList.add("w122-answer-box")')
    chips_at = body.index('"followup-chips"')
    assert plain_at < box_at and plain_at < chips_at


def test_pins_bumped_for_wave122():
    assert "filename='style.css', v='50'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v27"' in SW
    assert '"/static/style.css?v=50"' in SW


# --- jsdom: the real page, conditions in the DOM --------------

PAYLOADS = {
    "s1": {
        # WAVE 123: the fixture ask now carries BOTH intents
        # (steps + samjhao), so its server payload legitimately
        # carries labels:true AND the chips — the DOM checks
        # below verify the client honours the payload.
        "question": "Find the HCF of 12 and 18, step by step samjhao",
        "ok": True,
        "result": {"type": "Arithmetic", "op": "hcf",
                   "steps": ["12 = 2^2 × 3", "18 = 2 × 3^2",
                             "GCD = 6"],
                   "answer": "6"},
        "intro": None, "advice": "Check by dividing.",
        "methods": [], "teach": [],
        "w122": {"step_label": "Step", "flavour": "en",
                 "labels": True,
                 "chips": [
                     {"kind": "example",
                      "label": "Give one more example"},
                     {"kind": "test",
                      "label": "Give a small test on this topic"},
                     {"kind": "simpler",
                      "label": "Explain more simply"}]},
    },
    "fu": {
        "question": "Give one more example",
        "ok": True,
        "result": {"type": "Arithmetic", "op": "hcf",
                   "steps": ["12 = 2^2 × 3", "19 = 19",
                             "GCD = 1"],
                   "answer": "1", "followup": "example"},
        "intro": None, "followup_note": "One more example:",
        "advice": "Check by dividing.", "methods": [],
        "teach": [],
        "w122": {"step_label": "Step", "flavour": "en",
                 "labels": True,
                 "chips": [
                     {"kind": "example",
                      "label": "Give one more example"},
                     {"kind": "test",
                      "label": "Give a small test on this topic"},
                     {"kind": "simpler",
                      "label": "Explain more simply"}]},
    },
    "s2": {
        # WAVE 123: a plain ask — the server payload now
        # carries labels:false and NO chips (the Wave-122
        # fixture carried chips here; that is the flip).
        "question": "What is 6 × 7?",
        "ok": True,
        "result": {"type": "Arithmetic", "op": "multiply",
                   "steps": ["6 × 7 = 42"], "answer": "42"},
        "intro": None, "advice": None, "methods": [],
        "teach": [],
        "w122": {"step_label": "Step", "flavour": "en",
                 "labels": False, "chips": []},
    },
    "nf": {
        "question": "zxqw jklm",
        "ok": True,
        "result": {"type": "Ganitra", "op": "not_found",
                   "answer": "Answer not found", "steps": [],
                   "fallback": True,
                   "fallback_kind": "not_found",
                   "plain": True, "plain_reply": True},
        "intro": None, "advice": None, "methods": [],
        "teach": [],
        "w122": {"step_label": "Step", "flavour": "en",
                 "labels": False, "chips": []},
    },
}

DRIVER_JS = r"""
const fs = require("fs");
let JSDOM;
try { ({ JSDOM } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const payloads = JSON.parse(
  fs.readFileSync(process.argv[3], "utf8"));
const html = fs.readFileSync(process.argv[2], "utf8");
const queue = [payloads.s1, payloads.fu, payloads.s2,
               payloads.nf];
async function main() {
  const out = {};
  const dom = new JSDOM(html, {
    url: "https://localhost/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    beforeParse(window) {
      window.fetch = function (url) {
        return Promise.resolve({
          json: function () {
            return Promise.resolve(
              String(url).indexOf("/api/solve") >= 0
                ? (queue.shift() || { ok: true })
                : { ok: true });
          }
        });
      };
      if (!window.matchMedia) {
        window.matchMedia = function (q) {
          return { matches: false, media: q,
                   addEventListener: function () {},
                   removeEventListener: function () {},
                   addListener: function () {},
                   removeListener: function () {} };
        };
      }
      if (!("speechSynthesis" in window)) {
        window.SpeechSynthesisUtterance = function (text) {
          this.text = text || ""; this.lang = "";
          this.onend = null; this.onerror = null;
          this.addEventListener = function () {};
          this.removeEventListener = function () {};
        };
        window.speechSynthesis = {
          getVoices: function () { return []; },
          speak: function () {}, cancel: function () {},
          addEventListener: function () {},
          speaking: false, pending: false, paused: false
        };
      }
    }
  });
  const window = dom.window, document = window.document;
  await new Promise(function (r) {
    if (document.readyState === "complete") r();
    else window.addEventListener("load", r);
  });
  const sleep = function (ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  };
  async function ask(text) {
    const box = document.getElementById("q");
    box.value = text;
    document.getElementById("chat-form").dispatchEvent(
      new window.Event("submit",
        { bubbles: true, cancelable: true }));
    await sleep(60);
  }
  function lastBot() {
    const bs = [...document.querySelectorAll(".bubble.bot")];
    return bs[bs.length - 1];
  }
  /* --- Turn 1: solved, multi-step --- */
  const askP = ask(payloads.s1.question);
  let sawWait = false;
  for (let i = 0; i < 40; i++) {
    if (document.querySelector(".w122-wait")) {
      sawWait = true; break;
    }
    await sleep(25);
  }
  out.sawRevealWait = sawWait;
  await sleep(1400);
  let b = lastBot();
  let ans = b.querySelector(".answer-big");
  out.s1Boxed = !!ans
    && ans.classList.contains("w122-answer-box");
  out.s1Answer = ans ? ans.textContent.trim() : null;
  const lis = [...b.querySelectorAll("ol.steps li")];
  out.s1StepLabels = lis.map(function (li) {
    return li.getAttribute("data-w122-step");
  });
  out.s1StepTexts = lis.map(function (li) {
    return li.textContent;
  });
  out.s1WaitLeft = document.querySelectorAll(
    ".w122-wait").length;
  let chips = document.querySelectorAll(".followup-chips");
  out.s1ChipRows = chips.length;
  out.s1Chips = chips.length
    ? [...chips[0].querySelectorAll(".followup-chip")].map(
        function (c) { return c.textContent; })
    : [];
  /* --- Chip tap: the example follow-up --- */
  const chipBtn = document.querySelector(".followup-chip");
  if (chipBtn) chipBtn.click();
  await sleep(1200);
  const userBubbles = [...document.querySelectorAll(
    ".bubble.user")].map(function (u) {
      return u.textContent.trim();
    });
  out.fuUserBubble = userBubbles[userBubbles.length - 1];
  out.fuChipRows = document.querySelectorAll(
    ".followup-chips").length;
  b = lastBot();
  out.fuIntro = b.querySelector(".answer-intro")
    ? b.querySelector(".answer-intro").textContent : null;
  /* --- Turn 2: solved, SINGLE step --- */
  await ask(payloads.s2.question);
  await sleep(1200);
  b = lastBot();
  ans = b.querySelector(".answer-big");
  out.s2Boxed = !!ans
    && ans.classList.contains("w122-answer-box");
  const lis2 = [...b.querySelectorAll("ol.steps li")];
  out.s2StepLabels = lis2.map(function (li) {
    return li.getAttribute("data-w122-step");
  });
  out.s2ChipRows = document.querySelectorAll(
    ".followup-chips").length;
  /* --- Turn 3: not found — NONE of the four --- */
  await ask(payloads.nf.question);
  await sleep(900);
  b = lastBot();
  out.nfPlain = b.classList.contains("plain-reply");
  out.nfHasAnswerBig = !!b.querySelector(".answer-big");
  out.nfChipRows = document.querySelectorAll(
    ".followup-chips").length;
  out.nfStepLabels = document.querySelectorAll(
    "[data-w122-step]").length;
  window.close();
  console.log(JSON.stringify(out));
}
main().catch(function (e) {
  console.log(JSON.stringify({ error: String(e) }));
});
"""


def _node_modules_candidates():
    cands = []
    for base in (ROOT, ROOT.parent, Path.home()):
        nm = base / "node_modules"
        if (nm / "jsdom").exists():
            cands.append(str(nm))
    try:
        out = subprocess.run(
            ["npm", "root", "-g"], capture_output=True,
            text=True, timeout=15)
        g = out.stdout.strip()
        if g and (Path(g) / "jsdom").exists():
            cands.append(g)
    except Exception:
        pass
    return cands


def test_wave122_jsdom_conditions(client, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    cands = _node_modules_candidates()
    if not cands:
        pytest.skip("jsdom unavailable")
    page = client.get("/").get_data(as_text=True)
    page, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page)
    assert n_in == 1
    (tmp_path / "page.html").write_text(page, encoding="utf-8")
    (tmp_path / "payloads.json").write_text(
        json.dumps(PAYLOADS), encoding="utf-8")
    (tmp_path / "driver.js").write_text(DRIVER_JS,
                                        encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(cands)
    p = subprocess.run(
        [node, str(tmp_path / "driver.js"),
         str(tmp_path / "page.html"),
         str(tmp_path / "payloads.json")],
        capture_output=True, text=True, env=env, timeout=120)
    out = json.loads(p.stdout.strip().splitlines()[-1])
    if out.get("skipped"):
        pytest.skip("jsdom unavailable")
    assert "error" not in out, out
    # (1) The reveal ran on the fresh turn and completed.
    assert out["sawRevealWait"] is True
    assert out["s1WaitLeft"] == 0
    # (2) Solved + multi-step: box, labels, chips — all four.
    assert out["s1Boxed"] is True
    assert out["s1Answer"] == "Answer: 6"
    assert out["s1StepLabels"] == ["Step 1", "Step 2", "Step 3"]
    assert out["s1StepTexts"] == PAYLOADS["s1"]["result"]["steps"]
    assert out["s1ChipRows"] == 1
    assert out["s1Chips"] == [
        "Give one more example",
        "Give a small test on this topic",
        "Explain more simply"]
    # Chip tap: label becomes the user turn, the follow-up
    # answer lands with its framing line, and exactly ONE
    # chip row exists (the latest answer's).
    assert out["fuUserBubble"] == "Give one more example"
    assert out["fuIntro"] == "One more example:"
    assert out["fuChipRows"] == 1
    # Single-step solved answer, plain ask (WAVE 123 FLIP):
    # the box stays (solved), but NO label and NO chip row —
    # simple plain.
    assert out["s2Boxed"] is True
    assert out["s2StepLabels"] == [None]
    assert out["s2ChipRows"] == 0
    # Not found: NONE of the four features.
    assert out["nfPlain"] is True
    assert out["nfHasAnswerBig"] is False
    assert out["nfChipRows"] == 0
