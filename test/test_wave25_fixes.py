"""Wave 25 (Suraj, 13 Nov 2026): THE DELIVERY + SEQUENCE FIXES.

The Waves 23+24 live check found four violations every
earlier suite had passed. Root causes pinned here:

1. Numbered steps — the standalone print page never had the
   no-numbering rule (its <ol> computed `decimal`), and the
   service worker served style.css cache-first under a
   fixed cache name, so returning browsers never received
   the Wave-24 rule. Fixes: print.html + the notebook rule
   carry `list-style: none` themselves; the worker is
   network-first for CSS/JS.
2. No answer line + gold strip — the real algebra payload's
   `latex` is the EQUATION, and the answer line rendered it
   first; the solver's trailing "Solution: x = 2" step
   duplicated the answer; .explain kept its gold tint.
   Fixes: label + answer text line, trailing restatement
   dropped from shown/spoken/copied steps, chat .explain
   transparent with no border.
3. Giant static sprites — their CSS is in the very file the
   worker froze; the 1600px sprites rendered at natural
   size. Fixes: worker v2 + width/height attributes on
   every sprite (HTML and JS-created).
4. Teach reveal invisible — engines that fire onend
   instantly burned the narration queue in a blink. Fix: a
   ~1s minimum on-board beat per part (advTimed). The jsdom
   test stubs speech with a SYNCHRONOUS onend (worst case)
   and samples the board mid-playback.
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
PRINT = (ROOT / "templates" / "print.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _signup(client):
    r = client.post("/signup", data={
        "name": "W25 Pytest Tester", "class": "10", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w25-pytest-pass"})
    assert r.status_code in (200, 302)


# --- The payload trap (why the old fixture missed bug 2) ----

def test_real_payload_shape():
    from solver.router import solve_question
    r = solve_question("solve 2x+3=7")
    assert r["answer"] == "x = 2"
    # latex is the EQUATION here, not the answer.
    assert r["latex"] == "2 x + 3 = 7"
    # The final step merely restates the answer.
    assert r["steps"][-1] == "Solution: x = 2"


# --- Bug 3's root: the service worker ------------------------

def test_service_worker_never_freezes_code_again():
    assert 'GANITRA_CACHE = "ganitra-static-v4"' in SW
    assert "ganitra-static-v2" not in SW
    assert "ganitra-static-v1" not in SW
    assert r"/\.(css|js)$/" in SW          # code: network-first
    assert 'cache: "no-cache"' in SW       # Wave 26: + revalidation
    assert "return hit || refresh;" in SW  # media: stale-while-revalidate


# --- Bug 1: no-numbering on every path -----------------------

def test_no_numbering_rules_on_every_path():
    nb = CSS[CSS.index("ol.steps.notebook {"):]
    nb = nb[:nb.index("}")]
    assert "list-style: none" in nb
    assert "list-style-type: none" in CSS
    # The standalone print page carries the rule itself.
    assert "ol.steps { list-style: none; }" in PRINT


# --- Bug 2: plain summary + labelled answer line -------------

def test_chat_explain_is_plain():
    assert "body.chat-page .bubble .explain {\n" \
        "  background: transparent; border-left: none;" in CSS


def test_answer_line_and_dedupe_wiring():
    assert "answerHeading: {{ t.answer_heading | tojson }}" in INDEX
    assert "var displaySteps" in INDEX
    assert "displaySteps.pop();" in INDEX
    # The answer line is built from the answer TEXT, and the
    # latex branch is only a fallback when there is none.
    i = INDEX.index('ans.className = "answer-big";')
    seg = INDEX[i:i + 1400]
    assert seg.index("if (result.answer)") \
        < seg.index("else if (result.latex)")


# --- Bug 3: sprite size pins ---------------------------------

def test_sprite_attribute_sizes(client):
    _signup(client)
    page = client.get("/").get_data(as_text=True)
    for actor, size in (("scene-eagle", "92"), ("scene-tiger", "104"),
                        ("scene-boy", "96")):
        assert re.search(
            rf'id="{actor}"\s+width="{size}"\s+height="{size}"', page)
    assert "boyWriter.width = 82" in INDEX
    assert "boy.width = 54" in INDEX


# --- Bug 4: the Teach minimum-beat floor ---------------------

def test_teach_minimum_beat_floor():
    assert "function advTimed()" in INDEX
    assert "1000 - (Date.now() - startedAt)" in INDEX


# --- jsdom: real page + real payload + instant speech --------

DRIVER_JS = r"""
const fs = require("fs");
let JSDOM;
try { ({ JSDOM } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const html = fs.readFileSync(process.argv[2], "utf8");
const sleep = function (ms) {
  return new Promise(function (r) { setTimeout(r, ms); });
};
(async function () {
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
                   addListener: function () {} };
        };
      }
      /* Instant engine: onend fires synchronously. */
      window.SpeechSynthesisUtterance = function (text) {
        this.text = text || ""; this.lang = "";
        this.rate = 1; this.pitch = 1; this.volume = 1;
        this.voice = null; this.onend = null; this.onerror = null;
        this.addEventListener = function () {};
        this.removeEventListener = function () {};
      };
      window.speechSynthesis = {
        getVoices: function () { return []; },
        speak: function (u) { if (u && u.onend) u.onend(); },
        cancel: function () {},
        addEventListener: function () {},
        speaking: false, pending: false, paused: false
      };
    }
  });
  const window = dom.window, document = window.document;
  await new Promise(function (r) {
    if (document.readyState === "complete") r();
    else window.addEventListener("load", r);
  });
  const eagle = document.getElementById("scene-eagle");
  if (eagle) {
    const cs = window.getComputedStyle(eagle);
    out.eagle = { w: cs.width, h: cs.height,
                  opacity: cs.opacity, visibility: cs.visibility,
                  attrW: eagle.getAttribute("width") };
  }
  document.getElementById("q").value = "solve 2x+3=7";
  document.getElementById("chat-form").dispatchEvent(
    new window.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(900);
  const bubbles = [...document.querySelectorAll(".bubble.bot")];
  const b = bubbles[bubbles.length - 1];
  if (!b) { out.error = "no bubble"; console.log(JSON.stringify(out)); return; }
  const ans = b.querySelector(".answer-big");
  out.answerText = ans ? ans.textContent.trim() : null;
  out.answerIsLast = !!ans && b.lastElementChild === ans;
  out.answerBg = ans
    ? window.getComputedStyle(ans).backgroundColor : null;
  const ol = b.querySelector("ol.steps");
  out.stepTexts = ol
    ? [...ol.children].map(function (li) { return li.textContent; })
    : null;
  out.liListAllNone = ol
    ? [...ol.children].every(function (li) {
        return window.getComputedStyle(li).listStyleType === "none";
      }) : null;
  const ex = b.querySelector(".explain");
  if (ex) {
    const ecs = window.getComputedStyle(ex);
    out.explainBg = ecs.backgroundColor;
    out.explainBorderLeft = ecs.borderLeftStyle;
  }
  const wrap = b.parentElement;
  const teachBtn = wrap.querySelector('[data-action="teach"]');
  const det = b.querySelector("details.steps-section");
  if (teachBtn && ol && det) {
    teachBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    await sleep(250);
    out.teachStartAllWaiting = [...ol.children].every(
      function (li) { return li.classList.contains("teach-wait"); });
    const boy = det.querySelector(".boy-writer");
    out.boySize = boy ? window.getComputedStyle(boy).width : null;
    out.boyAttr = boy ? boy.getAttribute("width") : null;
    await sleep(2350);
    const lis = [...ol.children];
    out.teachMidFirstRevealed = lis.length > 0
      && !lis[0].classList.contains("teach-wait");
    out.teachMidLastWaiting = lis.length > 0
      && lis[lis.length - 1].classList.contains("teach-wait");
    teachBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    await sleep(200);
    out.teachStoppedClean = !ol.classList.contains("teach-playing")
      && [...ol.children].every(function (li) {
           return !li.classList.contains("teach-wait"); });
  }
  window.close();
  console.log(JSON.stringify(out));
  process.exit(0);
})();
"""


def _node_modules_candidates():
    cands = []
    env = os.environ.get("GANITRA_NODE_MODULES")
    if env:
        cands.append(env)
    cands.append("/tmp/w23-jsdom/node_modules")
    cands.append(str(Path.home() / "workspace" / ".w24-scratch"
                     / "jsdom" / "node_modules"))
    return [p for p in cands if (Path(p) / "jsdom").is_dir()]


def test_jsdom_wave25_fixes(client, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    cands = _node_modules_candidates()
    if not cands:
        pytest.skip("jsdom unavailable")
    _signup(client)
    payload = client.post(
        "/api/solve", json={"question": "solve 2x+3=7"}).get_json()
    page = client.get("/").get_data(as_text=True)
    page, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page)
    assert n_in == 1
    (tmp_path / "page.html").write_text(page, encoding="utf-8")
    (tmp_path / "payload.json").write_text(
        json.dumps(payload), encoding="utf-8")
    (tmp_path / "driver.js").write_text(DRIVER_JS, encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(cands)
    p = subprocess.run(
        [node, str(tmp_path / "driver.js"), str(tmp_path / "page.html"),
         str(tmp_path / "payload.json")],
        capture_output=True, text=True, env=env)
    out = json.loads(p.stdout.strip().splitlines()[-1])
    if out.get("skipped"):
        pytest.skip("jsdom unavailable")

    # Sprites: spec size + hidden at rest + attribute pin.
    assert out["eagle"]["w"] == "92px" and out["eagle"]["h"] == "92px"
    assert out["eagle"]["opacity"] == "0"
    assert out["eagle"]["visibility"] == "hidden"
    assert out["eagle"]["attrW"] == "92"
    # Bug 2: labelled plain answer line, last in the card.
    assert out["answerText"] == "Answer: x = 2"
    assert out["answerIsLast"] is True
    assert out["answerBg"] == "rgba(0, 0, 0, 0)"
    # Steps: deduped, plain, unnumbered on the <ol> AND each <li>.
    assert out["stepTexts"] == payload["result"]["steps"][:-1]
    assert out["liListAllNone"] is True
    # The gold strip is gone from the chat card.
    assert out["explainBg"] == "rgba(0, 0, 0, 0)"
    assert out["explainBorderLeft"] == "none"
    # Bug 4: even with an instant speech engine, Teach blanks
    # everything first, then reveals step by step.
    assert out["teachStartAllWaiting"] is True
    assert out["boySize"] == "82px" and out["boyAttr"] == "82"
    assert out["teachMidFirstRevealed"] is True
    assert out["teachMidLastWaiting"] is True
    assert out["teachStoppedClean"] is True
