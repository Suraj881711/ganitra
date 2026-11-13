"""Wave 24 (Suraj, 12 Nov 2026, ~23:44 IST): THE ANSWER
SEQUENCE + chatbox polish.

The complaint: after a question, the answer "pura kachra ki
tarah lagta hai, sequence mai nahi lagta bilkul bhi". Audit:
addAnswerBubble appended the final answer FIRST, Teacher's
Advice before the steps, the action buttons mid-bubble, and
the steps LAST inside a collapsed <details>; templates/
answer.html had the same scramble; the action buttons were
styled by three competing rulesets plus an invisible halo,
so they never rendered truly equal (~46x37 measured live).

The fix pinned here: both renderers assemble ONE reading
sequence — steps (open, plain UNNUMBERED lines) → plain
answer line, all inside the one bordered CARD → icon row
BELOW/OUTSIDE the card → on-demand panels (advice /
methods) → full-solution link. The jsdom test drives the
REAL rendered chat page (fetch stubbed) and asserts the
DOM order of a produced answer; Wave 21/22 Teach +
narration and the Wave 23 boy writer are asserted intact
in sequence.

SPEC CHANGE (Suraj, 13 Nov 2026 ~00:00 IST, Muse-row
screenshot "aise use karana hai"): the action row is
BORDERLESS — plain outline glyphs, no background, no border,
no labels, muted ink, equal tap size via equal padding, and
More Methods is the "•••" ellipsis. This overrides the boxed
36x36 buttons first shipped.
DESIGN CHANGE (same night ~00:08–00:16 IST): Teacher's
Advice is ON-DEMAND (fifth sign, lightbulb; hidden by
default — the default flow no longer contains visible
advice); glyphs shrink to 18px; the five signs form one
TIGHT left-aligned cluster (2px gap); step NUMBERING IS
REMOVED entirely ("bs solve kar — 1,2,3 likhne ki jarurat
nahi hai"); and finally the whole solve + answer sit
inside the ONE bordered card while the icon row renders
BELOW/OUTSIDE it, with the answer as a NORMAL plain bold
line — no highlight box, no tint ("ans itna highlight nahi
karna, bas normal hona chahiye"). An in-between "big hero
answer box" instruction (~00:12 IST) was superseded.
FONT SCALE (same night, corrected — "bahut jyada hai"):
chat body/steps 14px, handwriting steps 15px, question/
composer 14px, final answer 15.5px, section headings 13px
(wave 27: 13 / 14 / 13.5 / 14.5 / 12),
line-height ~1.65.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


# --- Source-level sequence pins --------------------------------

def test_chat_assembly_single_ordered_block():
    asm = INDEX[INDEX.index("/* Wave 24: THE reading sequence"):]
    asm = asm[:asm.index("log.appendChild(wrap);")]
    seq = ["div.appendChild(badge);",
           "if (explEl) div.appendChild(explEl);",
           "if (stepsSection) div.appendChild(stepsSection);",
           "if (graphImg) div.appendChild(graphImg);",
           "div.appendChild(ans);",
           "wrap.appendChild(div);",
           "if (actions.children.length) wrap.appendChild(actions);",
           "if (adviceEl) wrap.appendChild(adviceEl);",
           "if (methodsPanel) wrap.appendChild(methodsPanel);",
           "wrap.appendChild(full);"]
    pos = [asm.find(s) for s in seq]
    assert all(p >= 0 for p in pos)
    assert pos == sorted(pos)


def test_chat_no_early_appends():
    # badge/ans/full are appended exactly once (in the
    # assembly); the old immediate appends are gone.
    assert INDEX.count("div.appendChild(badge);") == 1
    assert INDEX.count("div.appendChild(ans);") == 1
    assert INDEX.count("wrap.appendChild(full);") == 1
    for gone in ("div.appendChild(expl);",
                 "div.appendChild(card);", "div.appendChild(det);",
                 "div.appendChild(img);"):
        assert gone not in INDEX


def test_chat_steps_open_unnumbered_and_answer_plain():
    assert 'det.className = "steps-section";' in INDEX
    assert "det.open = true;" in INDEX
    # NO numbering (Suraj: "1,2,3 likhne ki jarurat nahi"):
    # the seq badge class is gone from the steps list.
    assert '"steps notebook seq"' not in INDEX
    assert '"steps notebook"' in INDEX
    # NO answer box in the chat (Suraj: "ans itna highlight
    # nahi karna") — a plain line inside the card, and the
    # row/panels live in the wrap outside the card.
    assert "ansBox" not in INDEX
    assert "final-answer" not in INDEX
    assert "div.appendChild(ans);" in INDEX
    assert 'wrap.className = "answer-wrap";' in INDEX


def test_advice_on_demand_static():
    # Design change: the advice card starts hidden and is
    # toggled by the bulb sign (fifth in the row).
    assert "card.hidden = true;" in INDEX
    assert "ICON_ADVICE" in INDEX
    assert 'adviceBtn.dataset.action = "advice";' in INDEX
    assert "M9 18h6" in INDEX  # lightbulb glyph path
    assert ".advice-card[hidden]" in CSS


def test_teach_and_boy_hooks_survive():
    assert "function startTeachPlayback()" in INDEX
    # Wave 25: narration is fed the bubble's displaySteps
    # (the solver steps minus a trailing answer restatement).
    assert "narrateSolution(displaySteps" in INDEX
    assert "showBoyWriter();" in INDEX
    assert "scheduleBoyWriterHide();" in INDEX
    assert "if (boyBroken || !stepsDet) return;" in INDEX


def test_answer_template_sequence():
    order = [ANSWER.index('{% if explanation %}'),
             ANSWER.index('{% if result.steps %}'),
             ANSWER.index('{% if result.image %}'),
             ANSWER.index('class="final-answer"'),
             ANSWER.index('{% if advice %}'),
             ANSWER.index('{% if methods %}'),
             ANSWER.index('{% if teach %}')]
    assert order == sorted(order)
    # Pinned hooks from earlier waves stay byte-identical.
    assert 'class="steps notebook handwriting-on" id="steps-list"' \
        in ANSWER
    assert 'id="hw-toggle"' in ANSWER
    assert 'class="answer-big"' in ANSWER


# --- CSS pins ----------------------------------------------------

def test_final_answer_box_css():
    # The .final-answer box survives ONLY as the /solve
    # answer PAGE's document box.
    assert ".final-answer {" in CSS
    assert "border-left: 4px solid var(--accent);" in CSS
    assert "rgba(47, 125, 110, .10)" in CSS  # brand teal tint
    assert ".final-answer .answer-big { margin: 0; }" in CSS
    # The CHAT answer line is plain: no background, no
    # border — just the 14.5px bold line inside the card.
    fa = CSS[CSS.rindex("body.chat-page .bubble .answer-big {"):]
    fa = fa[:fa.index("}")]
    assert "background" not in fa and "border" not in fa
    assert "font-size: 14.5px" in fa
    # The wrap exists and the row hugs the card from outside.
    assert ".answer-wrap { min-width: 0; }" in CSS
    assert "padding-top: 2px; margin-top: 6px;" in CSS


def test_no_step_numbering_css():
    # Numbering REMOVED: no counter badges anywhere, and the
    # native markers are switched off on every steps list.
    assert "w24step" not in CSS
    assert "ol.steps.seq" not in CSS
    assert "ol.steps, #steps-list, .method-steps" in CSS
    assert "list-style-type: none" in CSS


def test_action_buttons_borderless_css():
    # Spec change (Muse-row screenshot): NO background, NO
    # border, NO halo; glyph 18px; equal tap size from the
    # same padding on every act-btn; muted ink. The row is
    # one TIGHT left-aligned cluster (2px gap).
    assert "background: transparent; border: none;" \
        " box-shadow: none;" in CSS
    assert ".act-btn::after" not in CSS
    assert ".act-btn svg { width: 18px; height: 18px; }" in CSS
    assert "padding: 10px 2px;" in CSS
    assert "color: var(--muted);" in CSS
    assert "justify-content: flex-start; gap: 2px;" in CSS
    w24 = CSS[CSS.index("Wave 24: the answer SEQUENCE"):]
    assert ".answer-actions .act-btn" in w24
    # State feedback is colour-only, never a box.
    assert ".teach-btn.teaching {" in w24
    assert "background: transparent; color: var(--accent);" \
        in w24


def test_methods_glyph_is_ellipsis():
    assert 'cx="5" cy="12" r="2"' in INDEX
    assert 'cx="12" cy="12" r="2"' in INDEX
    assert 'cx="19" cy="12" r="2"' in INDEX


def test_chat_font_scale_css():
    # Corrected sizes (Suraj: "bahut jyada hai").
    assert "body.chat-page .bubble { font-size: 13px;" \
        " line-height: 1.65; }" in CSS
    assert "font-size: 13.5px; line-height: 1.55;" in CSS
    assert "font-size: 14.5px; line-height: 1.5;" in CSS
    assert "font-size: 14px; line-height: 1.8;" in CSS
    assert "font-size: 12px; letter-spacing: .04em;" in CSS
    assert "text-transform: uppercase;" in CSS


def test_boy_rail_unchanged():
    assert ".bubble details.boy-host > ol.steps {" \
        " padding-right: 62px; }" in CSS


# --- Rendered answer page ----------------------------------------

def test_rendered_answer_page_order(client):
    r = client.post("/solve", data={"question": "x^2-5x+6=0"})
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    i_steps = body.index('id="steps-list"')
    i_box = body.index('class="final-answer"')
    i_big = body.index('class="answer-big"')
    assert i_steps < i_box < i_big
    if 'class="advice-card"' in body:
        assert i_box < body.index('class="advice-card"')


def test_api_payload_and_cache_unchanged(client):
    from solver.answer_cache import cache_stats, clear_cache
    r = client.post("/api/solve", json={"question": "x^2-5x+6=0"})
    d = r.get_json() or {}
    assert d.get("ok") is True
    assert isinstance((d.get("result") or {}).get("steps"), list)
    for key in ("explanation", "advice", "methods"):
        assert key in d
    clear_cache()
    client.post("/api/solve", json={"question": "15 + 27"})
    hits_before = cache_stats()["hits"]
    client.post("/api/solve", json={"question": "15 + 27"})
    assert cache_stats()["hits"] > hits_before


# --- jsdom: the real chat page renders the sequence --------------

DRIVER_JS = r"""
const fs = require("fs");
let JSDOM;
try { ({ JSDOM } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const pageFile = process.argv[2];
const payloadFile = process.argv[3];
const payloads = JSON.parse(fs.readFileSync(payloadFile, "utf8"));
const html = fs.readFileSync(pageFile, "utf8");
const LANDMARKS = [
  [".explain", "explain"],
  ["details.steps-section", "steps"],
  [".answer-big", "answer"],
  [".advice-card", "advice"],
  [".methods-panel", "methods"],
  [".answer-actions", "actions"]
];
function namesInOrder(bubble) {
  const sel = LANDMARKS.map(function (p) { return p[0]; }).join(",");
  return [...bubble.querySelectorAll(sel)].map(function (el) {
    for (const p of LANDMARKS) if (el.matches(p[0])) return p[1];
    return "?";
  });
}
async function scenario(payload) {
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
                ? payload : { ok: true });
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
      /* Speech stub: jsdom has no speechSynthesis, which
         would hide the Listen sign — the row must render all
         FIVE signs here exactly as in a real browser. */
      if (!("speechSynthesis" in window)) {
        window.SpeechSynthesisUtterance = function (text) {
          this.text = text || ""; this.lang = "";
          this.rate = 1; this.pitch = 1; this.volume = 1;
          this.voice = null; this.onend = null;
          this.onerror = null; this.onboundary = null;
          this.addEventListener = function () {};
          this.removeEventListener = function () {};
        };
        window.speechSynthesis = {
          getVoices: function () { return []; },
          speak: function (u) {
            setTimeout(function () {
              if (u && typeof u.onend === "function") u.onend();
            }, 5);
          },
          cancel: function () {},
          addEventListener: function () {},
          removeEventListener: function () {},
          speaking: false, pending: false, paused: false
        };
      }
    }
  });
  const window = dom.window;
  const document = window.document;
  await new Promise(function (r) {
    if (document.readyState === "complete") r();
    else window.addEventListener("load", r);
  });
  const box = document.getElementById("q");
  const form = document.getElementById("chat-form");
  box.value = payload.question;
  form.dispatchEvent(new window.Event("submit",
    { bubbles: true, cancelable: true }));
  await new Promise(function (r) { setTimeout(r, 800); });
  const bubbles = [...document.querySelectorAll(".bubble.bot")];
  const bubble = bubbles[bubbles.length - 1];
  if (!bubble || !bubble.querySelector(".answer-big")) {
    out.error = "no answer bubble rendered";
    window.close();
    return out;
  }
  /* The card (bubble) holds ONLY the solve; the row and the
     panels live in the wrap, OUTSIDE and below the card. */
  const wrap = bubble.parentElement;
  out.wrapClass = wrap ? wrap.className : null;
  out.order = namesInOrder(wrap);
  out.cardOrder = namesInOrder(bubble);
  out.rowInBubble = !!bubble.querySelector(".answer-actions");
  const rowEl0 = wrap.querySelector(".answer-actions");
  out.rowParentWrap = !!rowEl0 && rowEl0.parentElement === wrap;
  out.firstChildClass = bubble.firstElementChild
    ? bubble.firstElementChild.className : null;
  const det = bubble.querySelector("details.steps-section");
  out.detOpen = det ? det.open : null;
  const ol = bubble.querySelector("ol.steps");
  out.olClasses = ol ? ol.className : null;
  out.stepTexts = ol
    ? [...ol.children].map(function (li) { return li.textContent; })
    : null;
  const ansEl = bubble.querySelector(".answer-big");
  out.answerText = ansEl ? ansEl.textContent.trim() : null;
  out.answerHasStepText = (ansEl && payload.result.steps)
    ? payload.result.steps.some(function (s) {
        return ansEl.textContent.indexOf(s) >= 0; })
    : null;
  out.answerHasAdvice = (ansEl && payload.advice)
    ? ansEl.textContent.indexOf(payload.advice) >= 0 : null;
  out.boxInBubble = !!bubble.querySelector(".final-answer");
  if (ansEl) {
    const acs = window.getComputedStyle(ansEl);
    out.answerStyle = { bg: acs.backgroundColor,
                        border: acs.borderTopStyle };
  }
  const panel = wrap.querySelector(".methods-panel");
  out.panelHidden = panel ? panel.hidden : null;
  const btns = [...wrap.querySelectorAll(
    ".answer-actions [data-action]")];
  out.actions = btns.map(function (b) { return b.dataset.action; });
  /* Wave 24 spec change: the row is BORDERLESS — assert no
     background, no border, no visible text label, and the
     equal tap size (same padding on every button). */
  out.btnStyles = btns.map(function (b) {
    const cs = window.getComputedStyle(b);
    return { pad: cs.padding, bg: cs.backgroundColor,
             border: cs.borderTopStyle,
             labels: [...b.children].every(function (el) {
               return el.tagName.toLowerCase() === "svg"
                 || el.classList.contains("sr-only"); }) };
  });
  const methodsBtn = wrap.querySelector(
    '[data-action="methods"]');
  out.methodsDots = methodsBtn
    ? methodsBtn.querySelectorAll("svg circle").length : null;
  /* Font scale (corrected sizes): step li (15px while the
     handwriting style is on, else the 14px body size), the
     final-answer line, the section heading, the composer. */
  const firstLi = ol ? ol.querySelector("li") : null;
  const sumEl = det ? det.querySelector("summary") : null;
  out.fonts = {
    step: firstLi
      ? window.getComputedStyle(firstLi).fontSize : null,
    answer: ansEl ? window.getComputedStyle(
      ansEl).fontSize : null,
    summary: sumEl
      ? window.getComputedStyle(sumEl).fontSize : null,
    composer: window.getComputedStyle(box).fontSize
  };
  /* Design change: the advice card exists but starts
     HIDDEN; the bulb sign toggles it below the row. Also
     probe the tight cluster + the unnumbered steps list. */
  const adviceCard = wrap.querySelector(".advice-card");
  out.advicePresent = !!adviceCard;
  out.adviceHiddenDefault = adviceCard
    ? adviceCard.hidden : null;
  const adviceBtn = wrap.querySelector(
    '[data-action="advice"]');
  if (adviceBtn && adviceCard) {
    adviceBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    out.adviceOpensOnTap = adviceCard.hidden === false;
    adviceBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    out.adviceClosesOnTap = adviceCard.hidden === true;
  }
  if (rowEl0) {
    const rcs = window.getComputedStyle(rowEl0);
    out.rowStyle = { gap: rcs.gap, columnGap: rcs.columnGap,
                     justify: rcs.justifyContent };
  }
  out.listStyle = ol
    ? window.getComputedStyle(ol).listStyleType : null;
  const teachBtn = wrap.querySelector('[data-action="teach"]');
  if (teachBtn && ol && det) {
    teachBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    await new Promise(function (r) { setTimeout(r, 150); });
    out.teachPlaying = ol.classList.contains("teach-playing");
    out.boyAtBoard = !!det.querySelector(".boy-writer");
    teachBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    await new Promise(function (r) { setTimeout(r, 80); });
    out.teachStopped = !ol.classList.contains("teach-playing");
  }
  window.close();
  return out;
}
(async function () {
  const res = {};
  res.s1 = await scenario(payloads.s1);
  res.s2 = await scenario(payloads.s2);
  console.log(JSON.stringify(res));
  process.exit(0);
})();
"""

PAYLOADS = {
    "s1": {
        "ok": True, "question": "Solve x^2 - 5x + 6 = 0",
        "result": {"type": "Algebra", "op": "quadratic",
                   "answer": "x = 2, x = 3",
                   # Wave 25: mirror the REAL algebra payload —
                   # it carries a `latex` field holding the
                   # EQUATION (the old fixture omitted it).
                   "latex": "x^2 - 5x + 6 = 0",
                   "steps": [
                       "Write in standard form: x^2 - 5x + 6 = 0, "
                       "so a = 1, b = -5, c = 6",
                       "Discriminant D = b^2 - 4ac = 25 - 24 = 1",
                       "Quadratic formula: x = (-b +/- sqrt(D)) "
                       "/ (2a)",
                       "Solution: x = 2, x = 3"]},
        "explanation": "Pehle standard form me likho, phir "
                       "discriminant nikalo.",
        "advice": "Discriminant hamesha dhyaan se calculate karo.",
        "methods": [{"id": "factor", "label": "Factorisation",
                     "steps": ["Split the middle term: -5x = "
                               "-2x - 3x",
                               "Factor by grouping: (x - 2)(x - 3) "
                               "= 0"]}],
        "teach": [], "language_switched": False, "language": "en",
    },
    "s2": {
        "ok": True, "question": "What is 15 + 27?",
        "result": {"type": "Arithmetic", "op": "add",
                   "answer": "42",
                   "steps": ["15 + 20 = 35", "35 + 7 = 42"]},
        "explanation": "", "advice": "", "methods": [],
        "teach": [], "language_switched": False, "language": "en",
    },
}


def _node_modules_candidates():
    cands = []
    env = os.environ.get("GANITRA_NODE_MODULES")
    if env:
        cands.append(env)
    cands.append("/tmp/w23-jsdom/node_modules")
    cands.append(str(Path.home() / "workspace" / ".w24-scratch"
                     / "jsdom" / "node_modules"))
    return [p for p in cands if (Path(p) / "jsdom").is_dir()]


def test_jsdom_answer_sequence(client, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    cands = _node_modules_candidates()
    if not cands:
        pytest.skip("jsdom unavailable")
    r = client.post("/signup", data={
        "name": "W24 Sequence Tester", "class": "10",
        "board": "CBSE", "goal": "Doctor", "hobby": "Cricket",
        "favourite": "Pizza", "password": "w24-sequence-pass"})
    assert r.status_code in (200, 302)
    page = client.get("/").get_data(as_text=True)
    page, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page)
    assert n_in == 1
    (tmp_path / "page.html").write_text(page, encoding="utf-8")
    (tmp_path / "payloads.json").write_text(
        json.dumps(PAYLOADS), encoding="utf-8")
    (tmp_path / "driver.js").write_text(DRIVER_JS, encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(cands)
    p = subprocess.run(
        [node, str(tmp_path / "driver.js"), str(tmp_path / "page.html"),
         str(tmp_path / "payloads.json")],
        capture_output=True, text=True, env=env)
    out = json.loads(p.stdout.strip().splitlines()[-1])
    if out.get("skipped"):
        pytest.skip("jsdom unavailable")

    s1 = out["s1"]
    # The full sequence across the wrap: solve inside the
    # card, then the row + panels OUTSIDE/below it.
    assert s1["order"] == ["explain", "steps", "answer",
                           "actions", "advice", "methods"]
    assert s1["cardOrder"] == ["explain", "steps", "answer"]
    assert s1["rowInBubble"] is False
    assert s1["rowParentWrap"] is True
    assert "answer-wrap" in s1["wrapClass"]
    assert s1["firstChildClass"] == "badge"
    # Steps: open section, payload order, NO numbering UI.
    assert s1["detOpen"] is True
    assert "seq" not in s1["olClasses"]
    assert s1["listStyle"] == "none"
    # Wave 25: the trailing "Solution: ..." restatement is
    # dropped from the shown steps; the answer line holds it.
    assert s1["stepTexts"] == PAYLOADS["s1"]["result"]["steps"][:-1]
    # The answer is a PLAIN line holding ONLY the answer.
    assert s1["answerText"] == "Answer: x = 2, x = 3"
    assert s1["answerHasStepText"] is False
    assert s1["answerHasAdvice"] is False
    assert s1["boxInBubble"] is False
    assert s1["answerStyle"]["bg"] == "rgba(0, 0, 0, 0)"
    assert s1["answerStyle"]["border"] == "none"
    # Five signs in order; methods panel hidden; the advice
    # card hidden by default and toggled by the bulb sign.
    assert s1["panelHidden"] is True
    assert s1["actions"] == ["copy", "listen", "teach",
                             "advice", "methods"]
    assert s1["advicePresent"] is True
    assert s1["adviceHiddenDefault"] is True
    assert s1["adviceOpensOnTap"] is True
    assert s1["adviceClosesOnTap"] is True
    # Borderless row, equal tap padding, tight cluster.
    assert len(s1["btnStyles"]) == 5
    for b in s1["btnStyles"]:
        assert b["pad"] == "10px 2px"
        assert b["bg"] == "rgba(0, 0, 0, 0)"
        assert b["border"] == "none"
        assert b["labels"] is True
    assert s1["rowStyle"]["justify"] == "flex-start"
    assert s1["rowStyle"]["columnGap"] == "2px" \
        or "2px" in (s1["rowStyle"]["gap"] or "")
    assert s1["methodsDots"] == 3
    # Font scale: corrected sizes, computed live.
    step_want = "14px" if "handwriting-on" in s1["olClasses"] \
        else "13px"
    assert s1["fonts"]["step"] == step_want
    assert s1["fonts"]["answer"] == "14.5px"
    assert s1["fonts"]["summary"] == "12px"
    assert s1["fonts"]["composer"] == "13.5px"
    # Teach playback + the boy writer ride the reordered board.
    assert s1["teachPlaying"] is True
    assert s1["boyAtBoard"] is True
    assert s1["teachStopped"] is True

    s2 = out["s2"]
    assert s2["order"] == ["steps", "answer", "actions"]
    assert s2["cardOrder"] == ["steps", "answer"]
    assert s2["rowInBubble"] is False
    assert s2["actions"] == ["copy", "listen", "teach"]
    assert s2["advicePresent"] is False
    assert all(b["pad"] == "10px 2px" and b["border"] == "none"
               for b in s2["btnStyles"])
