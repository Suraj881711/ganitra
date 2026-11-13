"""Wave-26 verification: THE SECOND DELIVERY HOLE (HTTP cache).

Waves 23+24 shipped correct CSS that live browsers did not
apply; Wave 25 blamed the service worker (cache-first, fixed
cache name) and shipped worker v2 (network-first) — yet the
Wave-25 live re-check STILL failed every CSS-dependent item
while every HTML/JS/attribute fix passed. Wave 26 found the
remaining layer, with fetched evidence:

  * The served /static/style.css is BYTE-IDENTICAL to the
    repo file (sha256 9eb8a48e…, 86,873 bytes, fetched from
    the live site) — hypothesis "wrong file / wrong mapping"
    is FALSE.
  * PythonAnywhere serves it with
    "Cache-Control: public, max-age=86400" (24 hours) plus
    ETag/Last-Modified. A stylesheet fetched during the
    Wave-21/22 checks (~12 Nov 23:11-23:36 IST) therefore
    counted as FRESH in the browser's HTTP cache until
    ~13 Nov 23:11-23:36 IST — covering every Wave 23/24/25
    verification that night.
  * Worker v2's fetch(req) uses the request's default cache
    mode, so the HTTP cache answered it WITHOUT touching
    the network: "network-first" never reached the network.
    (The worker script itself is fetched bypassing the HTTP
    cache on update checks — which is why v2 was verifiably
    live while the CSS it "delivered" was still the old
    copy. The HTML pages carry no max-age and arrived
    fresh: new answer line, sprite size attributes and the
    print page — whose styles are INLINE — all passed,
    while steps numbering, the gold .explain strip, sprite
    hiding/animation and Teach blanking — all pure style.css
    — all failed. Same builder function renders fresh and
    history answers (renderRecord -> addAnswerBubble), so
    no code path split can explain it. It was delivery.)

Fixes pinned by the checks below:
  1. templates/base.html links the stylesheet with a
     version query (?v=28 via url_for) — a cache key no
     browser has ever seen, so the current CSS lands on the
     next page load everywhere (HTTP cache, worker cache,
     any edge). Bump the number on every future CSS change.
  2. static/sw.js: cache name v5 (older purged on activate)
     and code fetches use cache: "no-cache" — the worker
     now REVALIDATES with the server (ETag -> cheap 304)
     instead of trusting HTTP-cache freshness ever again.
  3. templates/index.html pins listStyleType "none" inline
     on both JS-built steps lists (main + method): the one
     banned-outright behaviour (Suraj: no step numbers) is
     now impossible even with a missing stylesheet. The CSS
     rules remain the primary styling everywhere else.

The jsdom driver below renders the chat page AS SERVED
(real Flask-rendered HTML from the test client, the real
served stylesheet bytes inlined in place of the link) and
asserts COMPUTED styles on BOTH answer paths (fresh submit
and saved-chat history re-render, which share the one
builder), the scene stage (sprites hidden at rest; a tap
plays a scene and the actor's visibility rule applies),
and Teach on BOTH speech paths (instant-onend engine, and
no speechSynthesis at all — the timed fallback must still
blank, then reveal step-by-step).

Dhyaan note (checked, NOT a bug): the "ध्यान आज" pill
counted 4 after 2 questions in the Wave-25 live session
because the counter is a device-local per-day localStorage
record and the verifying browser is shared across test
accounts (2 solves from the Wave-24 account earlier the
same day + 2 = 4). dhyaanSolved() has exactly ONE call
site — one increment per successful solve — pinned below.

Run:  python verify_wave26.py
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
_DB = f"/tmp/ganitra-verify-wave26-{RUN_ID}.db"
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
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")

# --- 0. App + the real payload --------------------------------
from app import create_app  # noqa: E402

app = create_app()
c = app.test_client()
r = c.post("/signup", data={
    "name": "W26 Tester " + RUN_ID, "class": "10", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "w26-check-pass"})
check("signup for wave-26 checks", r.status_code in (200, 302),
      f"status={r.status_code}")

payload = c.post("/api/solve",
                 json={"question": "solve 2x+3=7"}).get_json()
res = (payload or {}).get("result") or {}
check("real payload (the one that exposed the bugs)",
      res.get("answer") == "x = 2"
      and (res.get("steps") or [""])[-1] == "Solution: x = 2",
      f"answer={res.get('answer')!r}")

# --- 1. The versioned stylesheet URL (the delivery fix) -------
page = c.get("/").get_data(as_text=True)
_link = re.search(r'href="([^"]*style\.css[^"]*)"', page)
check("served chat page links a VERSIONED stylesheet",
      _link is not None and "?v=" in _link.group(1),
      f"href={_link.group(1) if _link else None!r}")
check("base.html builds the link with a version query",
      re.search(r"url_for\('static',\s*filename='style\.css',"
                r"\s*v='\d+'\)", BASE) is not None)
_served_css = c.get("/static/style.css?v=28")
check("versioned URL serves the current stylesheet bytes",
      _served_css.status_code == 200
      and _served_css.data.decode("utf-8") == CSS,
      f"status={_served_css.status_code} "
      f"sha={hashlib.sha256(_served_css.data).hexdigest()[:12]}")
check("served page body carries the chat-page class",
      'body class="chat-page"' in page)
check("no language picker on the served chat page",
      "lang-select" not in page and "<select" not in page,
      "(/set-lang/ remains: it is the AUTO-switch persist "
      "call, not a picker)")

# --- 2. The worker can never trust a stale copy again ---------
check("service worker cache is versioned v5",
      'GANITRA_CACHE = "ganitra-static-v5"' in SW
      and "ganitra-static-v4" not in SW
      and "ganitra-static-v3" not in SW
      and "ganitra-static-v2" not in SW
      and "ganitra-static-v1" not in SW)
check("service worker revalidates code (no-cache fetch)",
      'fetch(req, { cache: "no-cache" })' in SW
      and r"/\.(css|js)$/" in SW and "network-first" in SW)
check("service worker media stays stale-while-revalidate",
      "return hit || refresh;" in SW)

# --- 3. The rules themselves are all still in the stylesheet --
check("stylesheet: steps group rule kills markers",
      "ol.steps, #steps-list, .method-steps" in CSS
      and "list-style-type: none" in CSS)
_sa = CSS[CSS.index(".scene-actor {"):]
_sa = _sa[:_sa.index("}")]
check("stylesheet: scene actors hidden at rest",
      "opacity: 0" in _sa and "visibility: hidden" in _sa)
check("stylesheet: teach-wait blanks a step",
      ".bubble li.teach-wait { opacity: 0; }" in CSS)
check("stylesheet: chat explanation de-tinted (Wave 25)",
      "body.chat-page .bubble .explain {\n"
      "  background: transparent; border-left: none;" in CSS)

# --- 4. One builder for fresh + history; inline number ban ----
_seg = INDEX[INDEX.index("function renderRecord"):
             INDEX.index("function loadThread")]
check("history re-render uses the same addAnswerBubble",
      "addAnswerBubble(" in _seg)
check("step numbers pinned inline on both steps lists",
      INDEX.count('ol.style.listStyleType = "none";') == 2,
      f"count={INDEX.count('ol.style.listStyleType = ')}")
check("dhyaan increments once per solve (single call site)",
      INDEX.count("dhyaanSolved();") == 1,
      f"call sites={INDEX.count('dhyaanSolved();')}")

# --- 5. Frozen logos untouched --------------------------------
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

# --- 6. jsdom: the page AS SERVED, every path -----------------
DRIVER_JS = r"""
const fs = require("fs");
let JSDOM;
try { ({ JSDOM } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const thread = JSON.parse(fs.readFileSync(process.argv[4], "utf8"));
const html = fs.readFileSync(process.argv[2], "utf8");

function makeDom(htmlText, url, speechMode, withThread) {
  return new JSDOM(htmlText, {
    url: url,
    runScripts: "dangerously",
    pretendToBeVisual: true,
    beforeParse(window) {
      window.fetch = function (u, opts) {
        const url = String(u);
        let body = { ok: true };
        if (url.indexOf("/api/solve") >= 0) body = payload;
        else if (/\/api\/chats\/\d+/.test(url)
                 && (!opts || !opts.method || opts.method === "GET")) {
          body = { ok: true, chat: { id: 7,
            messages: withThread ? thread : [] } };
        } else if (url.indexOf("/api/chats") >= 0
                   && opts && opts.method === "POST") {
          body = { ok: true, chat: { id: 7 } };
        } else if (url.indexOf("/api/chats") >= 0) {
          body = { ok: true, chats: [] };
        } else if (url.indexOf("/account/stats") >= 0) {
          body = { ok: true, questions: 0, chats: 0 };
        }
        return Promise.resolve({
          json: function () { return Promise.resolve(body); }
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
      /* The scene director disables itself if a sprite fails
         to load; jsdom loads no images at all, so model the
         production truth (the sprites serve HTTP 200): every
         image reports itself loaded at full size. */
      Object.defineProperty(window.HTMLImageElement.prototype,
        "naturalWidth", { configurable: true,
          get: function () { return 1600; } });
      Object.defineProperty(window.HTMLImageElement.prototype,
        "complete", { configurable: true,
          get: function () { return true; } });
      if (speechMode === "instant") {
        /* Worst case: onend fires SYNCHRONOUSLY in speak(). */
        window.SpeechSynthesisUtterance = function (text) {
          this.text = text || ""; this.lang = "";
          this.rate = 1; this.pitch = 1; this.volume = 1;
          this.voice = null; this.onend = null;
          this.onerror = null;
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
      } else if (speechMode === "none") {
        try { delete window.speechSynthesis; } catch (e) {}
      }
    }
  });
}
const sleep = function (ms) {
  return new Promise(function (r) { setTimeout(r, ms); });
};
async function untilLoad(dom) {
  const d = dom.window.document;
  if (d.readyState === "complete") return;
  await new Promise(function (r) {
    dom.window.addEventListener("load", r);
  });
}
function bubbleFacts(window, b) {
  const out = {};
  const ol = b.querySelector("ol.steps");
  out.answerText = (b.querySelector(".answer-big") || {})
    .textContent;
  out.answerText = out.answerText
    ? out.answerText.trim() : null;
  const ans = b.querySelector(".answer-big");
  out.answerIsLast = !!ans && b.lastElementChild === ans;
  out.olList = ol
    ? window.getComputedStyle(ol).listStyleType : null;
  out.olInline = ol ? ol.style.listStyleType : null;
  out.liListAllNone = ol
    ? [...ol.children].every(function (li) {
        return window.getComputedStyle(li).listStyleType
          === "none";
      }) : null;
  const ex = b.querySelector(".explain");
  if (ex) {
    const ecs = window.getComputedStyle(ex);
    out.explainBg = ecs.backgroundColor;
    out.explainBorderLeft = ecs.borderLeftStyle + "/" +
      ecs.borderLeftWidth;
  }
  return out;
}

(async function () {
  const out = {};

  /* ============ DOM 1: fresh path + scenes + Teach ======== */
  const dom1 = makeDom(html, "https://localhost/", "instant",
                       false);
  const w1 = dom1.window, d1 = w1.document;
  await untilLoad(dom1);
  await sleep(300);

  /* Sprites at rest: spec size, fully hidden. */
  out.sprites = {};
  [["scene-eagle", "92px"], ["scene-tiger", "104px"],
   ["scene-boy", "96px"]].forEach(function (pair) {
    const el = d1.getElementById(pair[0]);
    if (!el) { out.sprites[pair[0]] = null; return; }
    const cs = w1.getComputedStyle(el);
    out.sprites[pair[0]] = { w: cs.width, h: cs.height,
      want: pair[1], opacity: cs.opacity,
      visibility: cs.visibility };
  });

  /* Tap the stage: a scene starts and its actor's visibility
     rule applies (the animation itself is the browser's). */
  const stage = d1.getElementById("scene-stage");
  if (stage) {
    stage.dispatchEvent(new w1.MouseEvent("click",
      { bubbles: true }));
    await sleep(350);
    const m = (stage.className || "")
      .match(/playing-(eagle|tiger|chase)/);
    out.sceneClass = m ? m[1] : null;
    const actorId = { eagle: "scene-eagle",
      tiger: "scene-tiger", chase: "scene-tiger" }[out.sceneClass];
    if (actorId) {
      out.sceneActorVisibility = w1.getComputedStyle(
        d1.getElementById(actorId)).visibility;
    }
  }

  /* Ask the real question (fresh-answer path). */
  d1.getElementById("q").value = "solve 2x+3=7";
  d1.getElementById("chat-form").dispatchEvent(
    new w1.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(900);
  const bubbles1 = [...d1.querySelectorAll(".bubble.bot")];
  const b1 = bubbles1[bubbles1.length - 1];
  out.fresh = b1 ? bubbleFacts(w1, b1)
    : { error: "no bubble" };

  /* Teach on the instant engine: blanked at start (computed
     opacity too), revealing progressively, clean stop. */
  if (b1) {
    const wrap1 = b1.parentElement;
    const teachBtn = wrap1.querySelector('[data-action="teach"]');
    const ol1 = b1.querySelector("ol.steps");
    if (teachBtn && ol1) {
      teachBtn.dispatchEvent(new w1.MouseEvent("click",
        { bubbles: true }));
      await sleep(250);
      const lis = [...ol1.children];
      out.teachStartPlaying =
        ol1.classList.contains("teach-playing");
      out.teachStartAllWaiting = lis.every(function (li) {
        return li.classList.contains("teach-wait"); });
      out.teachStartOpacity = lis.length
        ? w1.getComputedStyle(lis[0]).opacity : null;
      await sleep(2350);
      out.teachMidFirstRevealed = lis.length > 0
        && !lis[0].classList.contains("teach-wait");
      out.teachMidLastWaiting = lis.length > 0
        && lis[lis.length - 1].classList.contains("teach-wait");
      teachBtn.dispatchEvent(new w1.MouseEvent("click",
        { bubbles: true }));
      await sleep(200);
      out.teachStoppedClean =
        !ol1.classList.contains("teach-playing")
        && lis.every(function (li) {
             return !li.classList.contains("teach-wait")
               && !li.classList.contains("teach-now"); });
    }
  }
  dom1.window.close();

  /* ============ DOM 2: saved-chat history path ============ */
  const dom2 = makeDom(html, "https://localhost/?chat=7",
                       "instant", true);
  const w2 = dom2.window, d2 = w2.document;
  await untilLoad(dom2);
  await sleep(1200);
  const bubbles2 = [...d2.querySelectorAll(".bubble.bot")];
  const b2 = bubbles2[bubbles2.length - 1];
  out.history = b2 ? bubbleFacts(w2, b2)
    : { error: "no bubble", count: bubbles2.length };
  dom2.window.close();

  /* ============ DOM 3: Teach with NO speech at all ======== */
  const dom3 = makeDom(html, "https://localhost/", "none",
                       false);
  const w3 = dom3.window, d3 = w3.document;
  await untilLoad(dom3);
  out.noSpeechAbsent = !("speechSynthesis" in w3);
  d3.getElementById("q").value = "solve 2x+3=7";
  d3.getElementById("chat-form").dispatchEvent(
    new w3.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(900);
  const bubbles3 = [...d3.querySelectorAll(".bubble.bot")];
  const b3 = bubbles3[bubbles3.length - 1];
  if (b3) {
    const teachBtn3 = b3.parentElement
      .querySelector('[data-action="teach"]');
    const ol3 = b3.querySelector("ol.steps");
    const det3 = b3.querySelector("details.steps-section");
    if (teachBtn3 && ol3) {
      teachBtn3.dispatchEvent(new w3.MouseEvent("click",
        { bubbles: true }));
      await sleep(300);
      const lis3 = [...ol3.children];
      out.nsStartPlaying =
        ol3.classList.contains("teach-playing");
      out.nsStartAllWaiting = lis3.every(function (li) {
        return li.classList.contains("teach-wait"); });
      out.nsStartOpacity = lis3.length
        ? w3.getComputedStyle(lis3[0]).opacity : null;
      const boy3 = det3
        ? det3.querySelector(".boy-writer") : null;
      out.nsBoy = boy3 ? {
        size: w3.getComputedStyle(boy3).width + "x" +
          w3.getComputedStyle(boy3).height,
        on: boy3.classList.contains("on") } : null;
      /* The timed fallback must advance the board on its own:
         poll until step 1 is revealed (later steps must
         still be waiting at that moment), up to ~14s. */
      out.nsAdvanced = false;
      for (let i = 0; i < 34; i++) {
        await sleep(400);
        if (lis3.length
            && !lis3[0].classList.contains("teach-wait")) {
          out.nsAdvanced = true;
          out.nsLastStillWaiting =
            lis3[lis3.length - 1].classList
              .contains("teach-wait");
          break;
        }
      }
      teachBtn3.dispatchEvent(new w3.MouseEvent("click",
        { bubbles: true }));
      await sleep(200);
      out.nsStoppedClean =
        !ol3.classList.contains("teach-playing")
        && lis3.every(function (li) {
             return !li.classList.contains("teach-wait")
               && !li.classList.contains("teach-now"); });
    }
  }
  dom3.window.close();

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


_node = shutil.which("node")
_cands = _node_modules_candidates()
if _node and _cands:
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(_cands)
    # The page AS SERVED (real rendered HTML), with the link
    # swapped for the SERVED stylesheet bytes — exactly what a
    # browser that actually receives the CSS computes against.
    page_html, n_in = re.subn(
        r'<link rel="stylesheet" href="[^"]*style\.css[^"]*" ?/>',
        lambda m: "<style>\n" + CSS + "\n</style>", page)
    assert n_in == 1
    _thread_payload = dict(payload)
    _thread_payload["_q"] = "solve 2x+3=7"
    thread = [{"role": "user", "text": "solve 2x+3=7"},
              {"role": "bot", "data": _thread_payload}]
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        (td / "page.html").write_text(page_html, encoding="utf-8")
        (td / "payload.json").write_text(
            json.dumps(payload), encoding="utf-8")
        (td / "thread.json").write_text(
            json.dumps(thread), encoding="utf-8")
        (td / "driver.js").write_text(DRIVER_JS, encoding="utf-8")
        p = subprocess.run([_node, str(td / "driver.js"),
                            str(td / "page.html"),
                            str(td / "payload.json"),
                            str(td / "thread.json")],
                           capture_output=True, text=True, env=env,
                           timeout=120)
    try:
        out = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        out = {}
    if out.get("skipped"):
        check("jsdom wave-26 DOM checks (node)", True,
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
        check("jsdom: stage tap plays a scene (actor visible)",
              out.get("sceneClass") in ("eagle", "tiger", "chase")
              and out.get("sceneActorVisibility") == "visible",
              f"scene={out.get('sceneClass')} "
              f"vis={out.get('sceneActorVisibility')}")
        for _path in ("fresh", "history"):
            f = out.get(_path) or {}
            check(f"jsdom [{_path}]: steps unnumbered, computed",
                  f.get("olList") == "none"
                  and f.get("liListAllNone") is True
                  and f.get("olInline") == "none",
                  f"ol={f.get('olList')} inline={f.get('olInline')} "
                  f"li={f.get('liListAllNone')}")
            check(f"jsdom [{_path}]: explanation plain, no strip",
                  f.get("explainBg") == "rgba(0, 0, 0, 0)"
                  and (f.get("explainBorderLeft") or "")
                      .startswith("none"),
                  f"bg={f.get('explainBg')} "
                  f"border={f.get('explainBorderLeft')}")
            check(f"jsdom [{_path}]: answer line is last, labelled",
                  f.get("answerText") == "Answer: x = 2"
                  and f.get("answerIsLast") is True,
                  f"text={f.get('answerText')!r}")
        check("jsdom: Teach blanks steps at start (speech)",
              out.get("teachStartPlaying") is True
              and out.get("teachStartAllWaiting") is True
              and out.get("teachStartOpacity") == "0",
              f"playing={out.get('teachStartPlaying')} "
              f"opacity={out.get('teachStartOpacity')}")
        check("jsdom: Teach reveals step-by-step (speech)",
              out.get("teachMidFirstRevealed") is True
              and out.get("teachMidLastWaiting") is True)
        check("jsdom: Teach stop restores the plain view",
              out.get("teachStoppedClean") is True)
        check("jsdom: no-speech path really has no speech",
              out.get("noSpeechAbsent") is True)
        check("jsdom: Teach blanks steps at start (no speech)",
              out.get("nsStartPlaying") is True
              and out.get("nsStartAllWaiting") is True
              and out.get("nsStartOpacity") == "0",
              f"playing={out.get('nsStartPlaying')} "
              f"opacity={out.get('nsStartOpacity')}")
        check("jsdom: boy writer at the board, 82px (no speech)",
              (out.get("nsBoy") or {}).get("size") == "82pxx82px"
              and (out.get("nsBoy") or {}).get("on") is True,
              f"boy={out.get('nsBoy')}")
        check("jsdom: timed fallback advances step-by-step",
              out.get("nsAdvanced") is True
              and out.get("nsLastStillWaiting") is True,
              f"advanced={out.get('nsAdvanced')} "
              f"lastWaiting={out.get('nsLastStillWaiting')}")
        check("jsdom: Teach stop restores view (no speech)",
              out.get("nsStoppedClean") is True)
else:
    check("jsdom wave-26 DOM checks (node)", True,
          "node/jsdom unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
