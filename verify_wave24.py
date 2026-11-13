"""Wave-24 verification: THE ANSWER SEQUENCE + CHATBOX POLISH.

Contract (Suraj, 12 Nov 2026, ~23:44 IST): after a question,
the answer "pura kachra ki tarah lagta hai, sequence mai nahi
lagta bilkul bhi" — it read as a mess, in no order at all.
Audit found why: addAnswerBubble appended the final answer
FIRST, the Teacher's Advice before the steps, the action
buttons in the middle, and the steps themselves LAST inside a
collapsed <details>; the /solve answer page had the same
scramble (answer at the top, steps near the bottom after the
advice, listen button and graph). The action buttons were
styled by three competing rulesets plus an invisible halo
pseudo-element, so they never rendered truly equal (~46x37).

Wave 24 contract — ONE reading sequence in both renderers:
  badge → explanation → STEPS (open, plain unnumbered lines) →
  graph → PLAIN ANSWER LINE — all inside the one bordered
  CARD (the bubble) → ACTION ROW BELOW/OUTSIDE the card →
  on-demand panels (advice / methods) → full-solution link.
The answer is NOT highlighted (Suraj, 13 Nov ~00:15-00:16
IST, final word): no tinted box, no border — a plain bold
line at the end of the solving lines; the icon row renders
underneath the card, not inside it. (The /solve answer PAGE
keeps its document box + in-page advice card.)
Steps carry NO numbering at all (Suraj, 13 Nov ~00:11 IST:
"bs solve kar — 1,2,3 likhne ki jarurat nahi hai"): no
badges, no native markers — the lines simply flow in order.
Wave 21/22 Teach + narration and Wave 23's boy-writer hooks
are untouched, and the answer cache still stores the result
DATA only (layout is assembled per render), so the reorder
is cache-safe.

SPEC CHANGE (Suraj, 13 Nov 2026 ~00:00 IST, screenshot of
Muse's own answer row: "aise use karana hai") — this
OVERRIDES the boxed-square action buttons this wave first
shipped: the row is BORDERLESS Muse-style — plain outline
glyphs, NO background, NO border, NO text labels, muted ink,
equal tap size via equal padding, and More Methods is
literally the "•••" ellipsis (three dots).

DESIGN CHANGE (Suraj, 13 Nov 2026 ~00:08 IST): Teacher's
Advice is ON-DEMAND — NOT shown automatically. The default
flow is steps → final-answer box → icon row; the advice
card sits hidden below the row and toggles from a FIFTH
sign (lightbulb outline). Row order: Copy, Listen, Teach
(circled play outline), Advice (bulb), More (•••). Glyphs
shrank to 18px the same night ("woh bhi or chote"), and the
row is one TIGHT left-aligned cluster (~00:10 IST): 2px gap
+ 2px side padding, glyphs ~6px apart — never spread out.

FONT SCALE (same night, corrected once — "bahut jyada hai",
the first ~2px cut was not enough): chat text noticeably
smaller — body/steps 14px, handwriting steps 15px,
question/composer 14px, final answer 15.5px, section
headings 13px (small-caps style), line-height ~1.65.
Wave 27 takes one more notch: 13 / 14 / 13.5 / 14.5 / 12.

Run:  python verify_wave24.py
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

RUN_ID = uuid.uuid4().hex[:8]
_DB = f"/tmp/ganitra-verify-wave24-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass

ROOT = Path(__file__).parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


# --- 1. Chat assembly: ONE sequence, appended once, in order -
_asm = INDEX[INDEX.index("/* Wave 24: THE reading sequence"):]
_asm = _asm[:_asm.index("log.appendChild(wrap);")]
_seq = ["div.appendChild(badge);",
        "if (explEl) div.appendChild(explEl);",
        "if (stepsSection) div.appendChild(stepsSection);",
        "if (graphImg) div.appendChild(graphImg);",
        "div.appendChild(ans);",
        "wrap.appendChild(div);",
        "if (actions.children.length) wrap.appendChild(actions);",
        "if (adviceEl) wrap.appendChild(adviceEl);",
        "if (methodsPanel) wrap.appendChild(methodsPanel);",
        "wrap.appendChild(full);"]
_pos = [_asm.find(s) for s in _seq]
check("chat assembly appends in the Wave-24 sequence",
      all(p >= 0 for p in _pos) and _pos == sorted(_pos),
      f"positions={_pos}")
check("no section is appended early any more",
      INDEX.count("div.appendChild(badge);") == 1
      and INDEX.count("div.appendChild(ans);") == 1
      and INDEX.count("wrap.appendChild(full);") == 1
      and "div.appendChild(expl);" not in INDEX
      and "div.appendChild(card);" not in INDEX
      and "div.appendChild(det);" not in INDEX
      and "div.appendChild(img);" not in INDEX)
check("answer is a PLAIN line in the card (no box)",
      "ansBox" not in INDEX
      and "final-answer" not in INDEX
      and "div.appendChild(ans);" in INDEX
      and 'wrap.className = "answer-wrap";' in INDEX)
check("steps section starts OPEN, steps UNNUMBERED",
      'det.className = "steps-section";' in INDEX
      and "det.open = true;" in INDEX
      and '"steps notebook seq"' not in INDEX
      and '"steps notebook"' in INDEX)
check("teacher advice ON-DEMAND (bulb sign, hidden default)",
      "card.hidden = true;" in INDEX
      and "ICON_ADVICE" in INDEX
      and 'adviceBtn.dataset.action = "advice";' in INDEX
      and "M9 18h6" in INDEX
      and ".advice-card[hidden]" in CSS)
check("Wave 21/22/23 hooks survive the reorder",
      "startTeachPlayback" in INDEX and "narrateSolution" in INDEX
      and "showBoyWriter();" in INDEX
      and "scheduleBoyWriterHide();" in INDEX
      and 'if (boyBroken || !stepsDet) return;' in INDEX)

# --- 2. Answer page: same sequence in the template ----------
_t_order = [ANSWER.index('{% if explanation %}'),
            ANSWER.index('{% if result.steps %}'),
            ANSWER.index('{% if result.image %}'),
            ANSWER.index('class="final-answer"'),
            ANSWER.index('{% if advice %}'),
            ANSWER.index('{% if methods %}'),
            ANSWER.index('{% if teach %}')]
check("answer page template follows the same sequence",
      _t_order == sorted(_t_order), f"positions={_t_order}")
check("answer page keeps its pinned hooks",
      'class="steps notebook handwriting-on" id="steps-list"'
      in ANSWER and 'id="hw-toggle"' in ANSWER
      and 'class="answer-big"' in ANSWER)

# --- 3. CSS: box, badges, equal buttons ----------------------
check("final-answer box styled (teal/gold tint)",
      ".final-answer {" in CSS
      and "border-left: 4px solid var(--accent);" in CSS
      and ".final-answer .answer-big { margin: 0; }" in CSS)
_fa = CSS[CSS.rindex("body.chat-page .bubble .answer-big {"):]
_fa = _fa[:_fa.index("}")]
check("chat answer line UNSTYLED (no tint/border) + wrap",
      "background" not in _fa and "border" not in _fa
      and "font-size: 14.5px" in _fa
      and ".answer-wrap { min-width: 0; }" in CSS
      and "padding-top: 2px; margin-top: 6px;" in CSS)
check("NO step numbering anywhere (badges removed)",
      "w24step" not in CSS
      and "counter(w24step)" not in CSS
      and "ol.steps.seq" not in CSS
      and "ol.steps, #steps-list, .method-steps" in CSS
      and "list-style-type: none" in CSS)
check("action row BORDERLESS, Muse-style (spec change)",
      "background: transparent; border: none;"
      " box-shadow: none;" in CSS
      and ".act-btn::after" not in CSS
      and ".act-btn svg { width: 18px; height: 18px; }" in CSS
      and "padding: 10px 2px;" in CSS
      and "color: var(--muted);" in CSS)
check("icon row is one TIGHT left-aligned cluster",
      "justify-content: flex-start; gap: 2px;" in CSS)
check("more-methods glyph is the three-dot ellipsis",
      'cx="5" cy="12" r="2"' in INDEX
      and 'cx="12" cy="12" r="2"' in INDEX
      and 'cx="19" cy="12" r="2"' in INDEX)
check("chat font scale (wave 27 sizes, Suraj 13 Nov)",
      "body.chat-page .bubble { font-size: 13px;"
      " line-height: 1.65; }" in CSS
      and "body.chat-page .chat-bar textarea {" in CSS
      and "font-size: 13.5px; line-height: 1.55;" in CSS
      and "font-size: 14.5px; line-height: 1.5;" in CSS
      and "font-size: 14px; line-height: 1.8;" in CSS
      and "font-size: 12px; letter-spacing: .04em;" in CSS)
check("boy-writer rail untouched by the reorder",
      ".bubble details.boy-host > ol.steps {"
      " padding-right: 62px; }" in CSS)

# --- 4. Rendered answer page order (Flask test client) ------
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True
c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("answer page renders", r.status_code == 200)
_i_steps = body.index('id="steps-list"')
_i_box = body.index('class="final-answer"')
_i_big = body.index('class="answer-big"')
check("rendered: steps before the final-answer box",
      _i_steps < _i_box < _i_big,
      f"steps={_i_steps} box={_i_box} big={_i_big}")
if 'class="advice-card"' in body:
    check("rendered: advice below the answer box",
          _i_box < body.index('class="advice-card"'))
else:
    check("rendered: advice below the answer box", True,
          "no advice for this question — template order pins it")

# --- 5. API payload + cache contract unchanged --------------
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
d = r.get_json() or {}
check("api success shape unchanged (data, not layout)",
      r.status_code == 200 and d.get("ok") is True
      and isinstance((d.get("result") or {}).get("steps"), list)
      and "explanation" in d and "advice" in d
      and "methods" in d)
from solver.answer_cache import cache_stats, clear_cache  # noqa: E402
clear_cache()
c.post("/api/solve", json={"question": "15 + 27"})
s1 = cache_stats()
c.post("/api/solve", json={"question": "15 + 27"})
s2 = cache_stats()
check("answer cache still serves repeat questions",
      s2["hits"] > s1["hits"], f"hits {s1['hits']} -> {s2['hits']}")

# --- 6. jsdom: the REAL chat page renders the sequence ------
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
                   # Wave 25: the REAL algebra payload also
                   # carries a `latex` field — for an equation
                   # it holds the EQUATION, not the answer (the
                   # old fixture omitted it, which hid the
                   # latex-first answer-line bug).
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


_node = shutil.which("node")
_cands = _node_modules_candidates()
if _node and _cands:
    # Render the real chat page (signed in) + inline the CSS so
    # jsdom can resolve the cascade for the geometry checks.
    r = c.post("/signup", data={
        "name": "W24 Sequence Tester", "class": "10",
        "board": "CBSE", "goal": "Doctor", "hobby": "Cricket",
        "favourite": "Pizza", "password": "w24-sequence-pass"})
    assert r.status_code in (200, 302)
    page = c.get("/").get_data(as_text=True)
    page, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page)
    assert n_in == 1
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "page.html").write_text(page, encoding="utf-8")
        (td / "payloads.json").write_text(
            json.dumps(PAYLOADS), encoding="utf-8")
        (td / "driver.js").write_text(DRIVER_JS, encoding="utf-8")
        env = dict(os.environ)
        env["NODE_PATH"] = os.pathsep.join(_cands)
        p = subprocess.run([_node, str(td / "driver.js"),
                            str(td / "page.html"),
                            str(td / "payloads.json")],
                           capture_output=True, text=True, env=env)
    try:
        out = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        out = {}
    if out.get("skipped"):
        check("jsdom DOM sequence (node)", True,
              "jsdom unavailable — skipped")
    else:
        s1 = out.get("s1") or {}
        check("jsdom: full answer in the Wave-24 sequence",
              s1.get("order") == ["explain", "steps", "answer",
                                  "actions", "advice", "methods"],
              f"order={s1.get('order')}")
        check("jsdom: card holds ONLY the solve; row OUTSIDE it",
              s1.get("cardOrder") == ["explain", "steps", "answer"]
              and s1.get("rowInBubble") is False
              and s1.get("rowParentWrap") is True
              and "answer-wrap" in (s1.get("wrapClass") or ""),
              f"card={s1.get('cardOrder')} "
              f"rowIn={s1.get('rowInBubble')}")
        check("jsdom: badge first, steps open, NO numbering UI",
              s1.get("firstChildClass") == "badge"
              and s1.get("detOpen") is True
              and "seq" not in (s1.get("olClasses") or "")
              and s1.get("listStyle") == "none",
              f"first={s1.get('firstChildClass')} "
              f"open={s1.get('detOpen')} ol={s1.get('olClasses')} "
              f"list={s1.get('listStyle')}")
        # Wave 25: the trailing step that only restates the
        # answer ("Solution: x = 2, x = 3") is dropped from
        # the shown list — the answer line carries it.
        _want_steps = PAYLOADS["s1"]["result"]["steps"][:-1]
        check("jsdom: steps in ascending payload order "
              "(answer restatement dropped)",
              s1.get("stepTexts") == _want_steps,
              f"steps={s1.get('stepTexts')}")
        check("jsdom: answer line holds ONLY the final answer",
              s1.get("answerText") == "Answer: x = 2, x = 3"
              and s1.get("answerHasStepText") is False
              and s1.get("answerHasAdvice") is False,
              f"answer={s1.get('answerText')!r}")
        _as = s1.get("answerStyle") or {}
        check("jsdom: answer line is PLAIN (no box/tint/border)",
              s1.get("boxInBubble") is False
              and _as.get("bg") == "rgba(0, 0, 0, 0)"
              and _as.get("border") == "none",
              f"style={_as} box={s1.get('boxInBubble')}")
        check("jsdom: five signs in order, methods panel hidden",
              s1.get("panelHidden") is True
              and s1.get("actions") == ["copy", "listen", "teach",
                                        "advice", "methods"],
              f"actions={s1.get('actions')}")
        check("jsdom: advice hidden by default, bulb toggles it",
              s1.get("advicePresent") is True
              and s1.get("adviceHiddenDefault") is True
              and s1.get("adviceOpensOnTap") is True
              and s1.get("adviceClosesOnTap") is True,
              f"present={s1.get('advicePresent')} "
              f"hidden={s1.get('adviceHiddenDefault')} "
              f"opens={s1.get('adviceOpensOnTap')}")
        _bs = s1.get("btnStyles") or []
        check("jsdom: action row borderless, unlabelled, "
              "equal tap padding",
              len(_bs) == 5
              and all(b.get("pad") == "10px 2px"
                      and b.get("bg") == "rgba(0, 0, 0, 0)"
                      and b.get("border") == "none"
                      and b.get("labels") is True for b in _bs),
              f"styles={_bs}")
        _rs = s1.get("rowStyle") or {}
        check("jsdom: row is a tight left-aligned cluster",
              _rs.get("justify") == "flex-start"
              and (_rs.get("columnGap") == "2px"
                   or "2px" in (_rs.get("gap") or "")),
              f"row={_rs}")
        check("jsdom: methods button is the ••• ellipsis",
              s1.get("methodsDots") == 3,
              f"dots={s1.get('methodsDots')}")
        _f = s1.get("fonts") or {}
        _step_want = "14px" if "handwriting-on" in (
            s1.get("olClasses") or "") else "13px"
        check("jsdom: chat font scale (wave 27 sizes)",
              _f.get("step") == _step_want
              and _f.get("answer") == "14.5px"
              and _f.get("summary") == "12px"
              and _f.get("composer") == "13.5px",
              f"fonts={_f} step_want={_step_want}")
        check("jsdom: Teach + boy-writer still work in order",
              s1.get("teachPlaying") is True
              and s1.get("boyAtBoard") is True
              and s1.get("teachStopped") is True,
              f"teach={s1.get('teachPlaying')} "
              f"boy={s1.get('boyAtBoard')}")
        s2 = out.get("s2") or {}
        check("jsdom: bare answer keeps the sequence",
              s2.get("order") == ["steps", "answer", "actions"]
              and s2.get("cardOrder") == ["steps", "answer"]
              and s2.get("rowInBubble") is False
              and s2.get("actions") == ["copy", "listen", "teach"]
              and s2.get("advicePresent") is False
              and all(b.get("pad") == "10px 2px"
                      and b.get("border") == "none"
                      for b in (s2.get("btnStyles") or [])),
              f"order={s2.get('order')} "
              f"actions={s2.get('actions')}")
else:
    check("jsdom DOM sequence (node)", True,
          "node/jsdom unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
