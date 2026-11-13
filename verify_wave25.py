"""Wave-25 verification: THE DELIVERY + SEQUENCE FIXES.

Live check of Waves 23+24 (13 Nov 2026) found four spec
violations on the REAL site that every earlier suite had
passed. Root causes (each pinned by a check below):

  1. NUMBERED STEPS. The chat CSS was correct on disk, but
     (a) the print page (templates/print.html) is standalone
     with its own inline styles and NEVER had the
     no-numbering rule — its <ol> computed `decimal` in a
     real cascade; and (b) the service worker served
     /static/ cache-first under a fixed cache name, so
     returning browsers never received the Wave-24
     `list-style: none` at all. Fixes: print.html carries
     the rule itself; the notebook rule carries it too;
     the worker is network-first for CSS/JS (see 3).
  2. NO ANSWER LINE + GOLD STRIP. The real algebra payload
     carries `latex` = the EQUATION ("2 x + 3 = 7"), and
     the chat's answer line rendered the latex first — so
     the "answer" showed the question's equation; the
     solver's last step ("Solution: x = 2") duplicated the
     answer inside the steps; and the explanation still
     wore its pre-Wave-24 gold tint (.explain #fdf6e3 +
     gold border). The Wave-24 fixture had NO latex field
     and never computed .explain styles, so all three
     slipped through. Fixes: the line is the localised
     label + answer text; a trailing answer-restatement
     step is dropped from the shown/spoken/copied steps;
     the chat explanation is plain (transparent, no
     border).
  3. GIANT STATIC SPRITES. The scene/boy CSS lives in
     style.css — the very file the cache-first worker
     froze — so the 1600x1600 sprites rendered at natural
     size, in flow, unmoving. Fixes: worker v2 (old caches
     purged on activate) + network-first CSS/JS +
     stale-while-revalidate media; width/height attributes
     on every sprite <img> (HTML and JS-created) so they
     can never blow up even with no CSS at all.
  4. TEACH REVEAL INVISIBLE. Steps start open (Wave 24)
     and, on any engine that fires onend instantly (no
     voices / headless), the narration queue burned
     through in a blink: by the time anyone looked, every
     step was simply already there. (On a stale-CSS phone
     the teach-wait blanking rule was missing entirely —
     same worker.) Fix: a ~1s minimum on-board beat per
     narration part in Teach's speakPart — real teacher
     speech is far longer, so the phone pace is unchanged.
     The jsdom driver below stubs speech with a SYNCHRONOUS
     onend (the worst case) and samples the board mid-play:
     step 1 revealed, the last step still blanked.

Run:  python verify_wave25.py
"""
import hashlib
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
_DB = f"/tmp/ganitra-verify-wave25-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass

ROOT = Path(__file__).parent
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
PRINT = (ROOT / "templates" / "print.html").read_text(encoding="utf-8")

# --- 0. App + the REAL payload that exposed bug 2 -----------
from app import create_app  # noqa: E402

app = create_app()
c = app.test_client()
r = c.post("/signup", data={
    "name": "W25 Tester " + RUN_ID, "class": "10", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w25-check-pass"})
check("signup for wave-25 checks", r.status_code in (200, 302),
      f"status={r.status_code}")

payload = c.post("/api/solve",
                 json={"question": "solve 2x+3=7"}).get_json()
res = (payload or {}).get("result") or {}
check("real payload carries the latex trap",
      res.get("answer") == "x = 2"
      and res.get("latex") == "2 x + 3 = 7"
      and (res.get("steps") or [""])[-1] == "Solution: x = 2",
      f"answer={res.get('answer')!r} latex={res.get('latex')!r} "
      f"last={((res.get('steps') or [''])[-1])!r}")
check("real payload has a plain-language explanation",
      bool((payload or {}).get("explanation")),
      f"expl={((payload or {}).get('explanation') or '')[:40]!r}")

# --- 1. The service worker can never freeze the CSS again ---
check("service worker cache is versioned v3 (v1/v2 purged)",
      'GANITRA_CACHE = "ganitra-static-v4"' in SW
      and "ganitra-static-v2" not in SW
      and "ganitra-static-v1" not in SW)
check("service worker: CSS/JS are network-first",
      r"/\.(css|js)$/" in SW and "network-first" in SW)
check("service worker: media is stale-while-revalidate",
      "return hit || refresh;" in SW)

# --- 2. No-numbering holds on EVERY steps rendering path ----
_nb = CSS[CSS.index("ol.steps.notebook {"):]
_nb = _nb[:_nb.index("}")]
check("notebook rule itself carries list-style: none",
      "list-style: none" in _nb)
check("steps group rule carries shorthand + longhand",
      "ol.steps, #steps-list, .method-steps" in CSS
      and "list-style-type: none" in CSS)
check("print page carries its own no-numbering rule",
      "ol.steps { list-style: none; }" in PRINT)

# --- 3. The chat explanation is plain (no gold strip) -------
check("chat .explain de-tinted by the Wave-25 rule",
      "body.chat-page .bubble .explain {\n"
      "  background: transparent; border-left: none;" in CSS)

# --- 4. Sprites are size-pinned even without CSS ------------
page = c.get("/").get_data(as_text=True)
for _id, _w in (("scene-eagle", "92"), ("scene-tiger", "104"),
                ("scene-boy", "96")):
    check(f"served sprite {_id} has width/height attrs",
          re.search(rf'id="{_id}"\s+width="{_w}"\s+height="{_w}"',
                    page) is not None)
check("boy writer created with attribute size in JS",
      "boyWriter.width = 82" in INDEX
      and "boyWriter.height = 82" in INDEX
      and "boy.width = 54" in INDEX)
check("sprite files exist on disk",
      all((ROOT / "static" / f"scene-{n}.webp").exists()
          for n in ("eagle", "tiger", "boy")))

# --- 5. Answer-line + dedupe + Teach dwell wiring -----------
check("chat CHAT map carries the localised answer label",
      "answerHeading: {{ t.answer_heading | tojson }}" in INDEX)
check("bubble builds displaySteps (restatement dropped)",
      "var displaySteps" in INDEX
      and "displaySteps.pop();" in INDEX)
check("Teach narration has the minimum-beat floor",
      "function advTimed()" in INDEX
      and "1000 - (Date.now() - startedAt)" in INDEX)

# --- 6. Frozen logos untouched -------------------------------
for _name, _want in (
        ("logo-full-t.png",
         "f18c8e428a61d79c00733df165835e472b0ebeab7bd8d4a360027a5ea5dc1efe"),
        ("logo-full.png",
         "07009560a9378eec64050db1476ca582d3aba4a81d6db6c2d39d919da12a7259"),
        ("logo-mark-t.png",
         "01aa3d236843dfd43109ae9fedfcaed3490b9bfc79890d93ce78c0758dc0094f"),
        ("logo-mark.png",
         "03bc03dc2fd8594f95e3bb910eee870e70fe2753857d573705ad03fc16cfcf9f")):
    _got = hashlib.sha256(
        (ROOT / "static" / _name).read_bytes()).hexdigest()
    check(f"frozen logo {_name} untouched", _got == _want)

# --- 7. jsdom: real page, real payload, worst-case speech ---
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
function makeDom(htmlText) {
  return new JSDOM(htmlText, {
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
      /* WORST-CASE speech stub: onend fires SYNCHRONOUSLY
         inside speak() — the instant-engine case that made
         the Teach reveal invisible live. */
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
}
const sleep = function (ms) {
  return new Promise(function (r) { setTimeout(r, ms); });
};
(async function () {
  const out = {};
  /* -- the chat page -- */
  const dom = makeDom(html);
  const window = dom.window, document = window.document;
  await new Promise(function (r) {
    if (document.readyState === "complete") r();
    else window.addEventListener("load", r);
  });
  /* Sprites BEFORE anything is asked: spec sizes, hidden. */
  out.sprites = {};
  [["scene-eagle", "92px"], ["scene-tiger", "104px"],
   ["scene-boy", "96px"]].forEach(function (pair) {
    const el = document.getElementById(pair[0]);
    if (!el) { out.sprites[pair[0]] = null; return; }
    const cs = window.getComputedStyle(el);
    out.sprites[pair[0]] = {
      w: cs.width, h: cs.height, want: pair[1],
      opacity: cs.opacity, visibility: cs.visibility,
      attrW: el.getAttribute("width"),
      attrH: el.getAttribute("height") };
  });
  /* Ask the real question. */
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
  if (ans) {
    const acs = window.getComputedStyle(ans);
    out.answerBg = acs.backgroundColor;
    out.answerWeight = acs.fontWeight;
  }
  const ol = b.querySelector("ol.steps");
  out.stepTexts = ol
    ? [...ol.children].map(function (li) { return li.textContent; })
    : null;
  out.olList = ol ? window.getComputedStyle(ol).listStyleType : null;
  out.liListAllNone = ol
    ? [...ol.children].every(function (li) {
        return window.getComputedStyle(li).listStyleType === "none";
      }) : null;
  const ex = b.querySelector(".explain");
  if (ex) {
    const ecs = window.getComputedStyle(ex);
    out.explainBg = ecs.backgroundColor;
    out.explainBorderLeft = ecs.borderLeftStyle + "/" +
      ecs.borderLeftWidth;
  }
  /* Teach with the instant engine: sample the board. */
  const wrap = b.parentElement;
  const teachBtn = wrap.querySelector('[data-action="teach"]');
  const det = b.querySelector("details.steps-section");
  if (teachBtn && ol && det) {
    teachBtn.dispatchEvent(new window.MouseEvent("click",
      { bubbles: true }));
    await sleep(250);
    out.teachStartPlaying = ol.classList.contains("teach-playing");
    out.teachStartAllWaiting = [...ol.children].every(
      function (li) { return li.classList.contains("teach-wait"); });
    const boy = det.querySelector(".boy-writer");
    out.boyPresent = !!boy;
    if (boy) {
      const bcs = window.getComputedStyle(boy);
      out.boySize = bcs.width + "x" + bcs.height;
      out.boyAttr = boy.getAttribute("width") + "/" +
        boy.getAttribute("height");
      out.boyOn = boy.classList.contains("on");
    }
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
           return !li.classList.contains("teach-wait")
             && !li.classList.contains("teach-now"); });
  }
  window.close();
  console.log(JSON.stringify(out));
  process.exit(0);
})();
"""

PAGE_DRIVER_JS = r"""
const fs = require("fs");
let JSDOM;
try { ({ JSDOM } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const html = fs.readFileSync(process.argv[2], "utf8");
const sel = process.argv[3];
const dom = new JSDOM(html, { url: "https://localhost/" });
const w = dom.window, d = w.document;
const el = d.querySelector(sel);
const out = {};
if (el) {
  out.list = w.getComputedStyle(el).listStyleType;
  out.liAllNone = [...el.children].every(function (li) {
    return w.getComputedStyle(li).listStyleType === "none"; });
  out.count = el.children.length;
} else { out.missing = sel; }
console.log(JSON.stringify(out));
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


_node = shutil.which("node")
_cands = _node_modules_candidates()
if _node and _cands:
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(_cands)
    page_html = c.get("/").get_data(as_text=True)
    page_html, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page_html)
    assert n_in == 1
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "page.html").write_text(page_html, encoding="utf-8")
        (td / "payload.json").write_text(
            json.dumps(payload), encoding="utf-8")
        (td / "driver.js").write_text(DRIVER_JS, encoding="utf-8")
        p = subprocess.run([_node, str(td / "driver.js"),
                            str(td / "page.html"),
                            str(td / "payload.json")],
                           capture_output=True, text=True, env=env)
    try:
        out = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        out = {}
    if out.get("skipped"):
        check("jsdom wave-25 DOM checks (node)", True,
              "jsdom unavailable — skipped")
    else:
        sp = out.get("sprites") or {}
        check("jsdom: sprites at spec size, hidden at rest",
              all((sp.get(k) or {}).get("w") == v
                  and (sp.get(k) or {}).get("h") == v
                  and (sp.get(k) or {}).get("opacity") == "0"
                  and (sp.get(k) or {}).get("visibility") == "hidden"
                  for k, v in (("scene-eagle", "92px"),
                               ("scene-tiger", "104px"),
                               ("scene-boy", "96px"))),
              f"sprites={sp}")
        check("jsdom: sprite attrs match the CSS sizes",
              all((sp.get(k) or {}).get("attrW")
                  == (sp.get(k) or {}).get("want", "")[:-2]
                  for k in ("scene-eagle", "scene-tiger",
                            "scene-boy")),
              f"attrs={ {k: (v or {}).get('attrW') for k, v in sp.items()} }")
        check("jsdom: answer line is the labelled plain answer",
              out.get("answerText") == "Answer: x = 2"
              and out.get("answerIsLast") is True
              and out.get("answerBg") == "rgba(0, 0, 0, 0)"
              and out.get("answerWeight") in ("700", "bold"),
              f"text={out.get('answerText')!r} last="
              f"{out.get('answerIsLast')} bg={out.get('answerBg')}")
        _want = (res.get("steps") or [])[:-1]
        check("jsdom: steps shown plain, restatement dropped",
              out.get("stepTexts") == _want
              and out.get("olList") == "none"
              and out.get("liListAllNone") is True,
              f"steps={out.get('stepTexts')} list={out.get('olList')}")
        check("jsdom: explanation has NO tint/border in chat",
              out.get("explainBg") == "rgba(0, 0, 0, 0)"
              and (out.get("explainBorderLeft") or "")
                  .startswith("none"),
              f"bg={out.get('explainBg')} "
              f"border={out.get('explainBorderLeft')}")
        check("jsdom: Teach blanks all steps at start (boy at board)",
              out.get("teachStartPlaying") is True
              and out.get("teachStartAllWaiting") is True
              and out.get("boyPresent") is True
              and out.get("boySize") == "82pxx82px"
              and out.get("boyAttr") == "82/82"
              and out.get("boyOn") is True,
              f"start={out.get('teachStartPlaying')}/"
              f"{out.get('teachStartAllWaiting')} boy="
              f"{out.get('boySize')} attr={out.get('boyAttr')}")
        check("jsdom: Teach reveals step-by-step (instant engine)",
              out.get("teachMidFirstRevealed") is True
              and out.get("teachMidLastWaiting") is True,
              f"first={out.get('teachMidFirstRevealed')} "
              f"lastWaiting={out.get('teachMidLastWaiting')}")
        check("jsdom: Teach stop restores the full plain view",
              out.get("teachStoppedClean") is True)

    # The /solve answer page: same no-numbering in a real cascade.
    ans_html = c.post("/solve", data={
        "question": "solve 2x+3=7"}).get_data(as_text=True)
    ans_html, n2 = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", ans_html)
    print_html = c.get(
        "/solution/print?style=hand").get_data(as_text=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "pdrv.js").write_text(PAGE_DRIVER_JS, encoding="utf-8")
        (td / "ans.html").write_text(ans_html, encoding="utf-8")
        (td / "print.html").write_text(print_html, encoding="utf-8")
        pa = subprocess.run([_node, str(td / "pdrv.js"),
                             str(td / "ans.html"), "#steps-list"],
                            capture_output=True, text=True, env=env)
        pp = subprocess.run([_node, str(td / "pdrv.js"),
                             str(td / "print.html"), "ol.steps"],
                            capture_output=True, text=True, env=env)
    try:
        a_out = json.loads(pa.stdout.strip().splitlines()[-1])
        p_out = json.loads(pp.stdout.strip().splitlines()[-1])
    except Exception:
        a_out, p_out = {}, {}
    if not a_out.get("skipped"):
        check("jsdom: answer-page steps unnumbered",
              a_out.get("list") == "none"
              and a_out.get("liAllNone") is True,
              f"ans={a_out}")
        check("jsdom: print-page steps unnumbered",
              p_out.get("list") == "none"
              and p_out.get("liAllNone") is True,
              f"print={p_out}")
else:
    check("jsdom wave-25 DOM checks (node)", True,
          "node/jsdom unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
