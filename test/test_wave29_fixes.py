"""Wave 29 (Suraj, 14 Nov 2026): the chat Teach button that
"did nothing" in the Wave 28 LIVE verification.

Investigation first (this file's driver IS the reproduction):
the served page was booted in jsdom and answer cards were
added through the app's OWN flows — a fresh submit, a
Hindi question (the language-switch path), and a chat
restored from the account store — with real /api/solve
payloads. On EVERY path the Teach click engaged
synchronously (button -> stop state, steps blanked, then
revealed one by one, boy writer at the board) with zero
window errors. The handler is bound per card at build time
inside addAnswerBubble; the Wave 28 diff does not touch
that binding (only the boy-writer sprite URL inside it),
and no overlay, delegation gap or boot-order defect exists
in the shipped code. The dead click therefore does NOT
reproduce from the code — it points at click delivery /
observation in the checking rig (an even number of toggle
clicks ends in the stopped state; a background tab never
repaints). What ships in Wave 29 is the guarantee, not a
guess:

1. THE TEACH REGRESSION (driver below, permanent): the
   boot smoke now adds an answer card the way the app adds
   it, clicks Teach, and asserts the teaching UI actually
   opens — synchronously (teaching state, steps blanked)
   and as it plays (a step reveals). Any window error
   fails it. If the binding ever breaks for real, this
   test goes red the same day.
2. SPEECH-API ISOLATION in speakPart: the utterance was
   built unguarded — on browsers/WebViews whose speech
   constructor or voice tuning throws, the narration chain
   died inside the click. A part that cannot be voiced
   now falls back to the timer pacing (the long-standing
   no-speech path), so the board always advances.
3. The /photo-solve accessible name follows the source:
   it was one hardcoded photo line for every upload, in
   every language; it now uses the same i18n heading as
   the visible box (file / file-ocr / photo, 6 languages).
Delivery hygiene: stylesheet ?v=29, worker cache v6,
sprite URLs ?v=29 — all pins move together, as always.
(The pins later moved again — stylesheet ?v=31, worker
cache v8 — while the sprite URLs stayed at ?v=29: no
sprite file changed. The pin assertions below track the
CURRENT pins, as in every wave before this one.)

Wave 120 update (Suraj, 17 Nov 2026): the Teach (play)
sign was REMOVED from the answer row on Suraj's order
(the speaker and the play sign "do the same job" — only
Listen stays). The boot smoke in section 4 now pins the
sign's ABSENCE on both card paths (fresh submit +
restored chat), plus the surviving Advice control, the
Listen sign, and zero window errors. The speech-API
isolation (item 2) stays source-pinned above: the
playback machinery remains in the page, dormant and
unreachable, exactly like the parked 3D scene.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W29 Fixes Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w29-fixes-pass"})
    return c


# --- 1. The speech-API isolation in the Teach click path -----

def test_teach_utterance_built_behind_a_guard():
    assert "/* Wave 29: build the utterance behind a guard." in INDEX
    assert "catch (e) { u = null; }" in INDEX
    # The guarded build: construct + tune inside the try, and
    # the speech branch keys off the built utterance, so a
    # throw lands in the timer fallback instead of dying.
    build = INDEX.index("u = new SpeechSynthesisUtterance(part.text);")
    guard = INDEX.index("catch (e) { u = null; }")
    branch = INDEX.index("if (u) {", build)
    assert build < guard < branch


# --- 2. The accessible name follows the source ---------------

def test_answer_aria_label_follows_source_branch():
    assert 'aria-label="Photo se padha gaya sawaal"' not in ANSWER
    assert 'aria-label="{{ t.file_heading }}"' in ANSWER
    assert 'aria-label="{{ t.photo_heading }}"' in ANSWER


def test_photo_solve_aria_names_the_file_for_file_sources(client):
    import i18n
    en = i18n.get_strings("en")
    for source in ("file", "file-ocr"):
        html = client.post("/photo-solve", data={
            "question": "2x + 3 = 7", "source": source,
        }).get_data(as_text=True)
        assert f'aria-label="{en["file_heading"]}"' in html, source
        assert f'aria-label="{en["photo_heading"]}"' not in html, source


def test_photo_solve_aria_names_the_photo_for_photos(client):
    import i18n
    en = i18n.get_strings("en")
    html = client.post("/photo-solve", data={
        "question": "2x + 3 = 7", "source": "photo",
    }).get_data(as_text=True)
    assert f'aria-label="{en["photo_heading"]}"' in html
    assert f'aria-label="{en["file_heading"]}"' not in html


# --- 3. Delivery versions -------------------------------------

def test_delivery_versions_wave29():
    assert "v='53'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v30"' in SW
    for old in ("ganitra-static-v5", "ganitra-static-v4",
                "ganitra-static-v3", "ganitra-static-v2",
                "ganitra-static-v1"):
        # Wave 60: match the FULL quoted cache name —
        # "ganitra-static-v30" contains "ganitra-static-v1"
        # as a bare substring, which is not the old cache.
        assert f'"{old}"' not in SW


# --- 4. THE CARD BOOT SMOKE (jsdom; Wave 120: no teach sign) --

TEACH_DRIVER_JS = r"""
const fs = require("fs");
let JSDOM, VirtualConsole;
try { ({ JSDOM, VirtualConsole } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const html = fs.readFileSync(process.argv[2], "utf8");
const payload = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function makeDom(mode) {
  const errors = [];
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => {
    const m = (e.detail && e.detail.message) || e.message || "";
    if (m.indexOf("Not implemented") === -1) {
      errors.push("jsdomError: " + m);
    }
  });
  vc.on("error", (m) => errors.push("console.error: " + m));
  const dom = new JSDOM(html, {
    url: mode === "restored"
      ? "https://localhost/?chat=1" : "https://localhost/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      window.addEventListener("error", (ev) => {
        errors.push("window.onerror: " + ev.message);
      });
      window.fetch = function (url, opts) {
        const u = String(url);
        let body = { ok: true };
        if (u.indexOf("/api/solve") >= 0) {
          body = payload;
        } else if (u.indexOf("/api/chats/1") >= 0
                   && (!opts || !opts.method)) {
          body = { ok: true, chat: { id: 1, title: "t", messages: [
            { role: "user", text: "2x + 3 = 7" },
            { role: "bot", data: payload } ] } };
        } else if (u.indexOf("/api/chats") >= 0
                   && (!opts || !opts.method)) {
          body = { ok: true, chats: [] };
        } else if (u.indexOf("/api/chats") >= 0) {
          body = { ok: true, chat: { id: 1, messages: [] } };
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
                   addListener: function () {},
                   removeListener: function () {} };
        };
      }
      /* A WORKING speech engine: speak() fires onend shortly
         after, like a real browser with voices installed. */
      if (!("speechSynthesis" in window)) {
        window.SpeechSynthesisUtterance = function (text) {
          this.text = text || ""; this.lang = "";
          this.addEventListener = function () {};
        };
        window.speechSynthesis = {
          getVoices: function () { return []; },
          speak: function (u) {
            setTimeout(function () { if (u && u.onend) u.onend(); }, 30);
          },
          cancel: function () {},
          addEventListener: function () {},
          speaking: false, pending: false, paused: false
        };
      }
      Object.defineProperty(window.HTMLImageElement.prototype,
        "naturalWidth", { configurable: true,
          get: function () { return 384; } });
      Object.defineProperty(window.HTMLImageElement.prototype,
        "complete", { configurable: true,
          get: function () { return true; } });
    }
  });
  return { dom, errors };
}

async function scenario(mode) {
  const { dom, errors } = makeDom(mode);
  const doc = dom.window.document;
  const out = { errors: errors };
  await sleep(1200);
  if (mode === "fresh") {
    const q = doc.getElementById("q");
    q.value = "2x + 3 = 7";
    q.closest("form").dispatchEvent(new dom.window.Event(
      "submit", { bubbles: true, cancelable: true }));
  }
  /* Wave 120: the Teach (play) sign is REMOVED from the
     row — the card is awaited via its answer line, and
     the sign must never appear. */
  let card = null;
  for (let i = 0; i < 50; i++) {
    card = doc.querySelector(".bubble.bot .answer-big");
    if (card) break;
    await sleep(100);
  }
  out.cardAppeared = !!card;
  if (card) {
    // Control: the Advice toggle on the same card must work.
    const advBtn = doc.querySelector('[data-action="advice"]');
    const advCard = doc.querySelector(".advice-card");
    if (advBtn && advCard) {
      const before = advCard.hidden;
      advBtn.click();
      out.adviceToggled = before === true && advCard.hidden === false;
      advBtn.click();
    }
    // A beat for any late render, then the Wave 120 pins:
    // no teach sign anywhere; the speaker sign present.
    await sleep(300);
    out.teachAbsent = !doc.querySelector('[data-action="teach"]');
    out.listenPresent = !!doc.querySelector('[data-action="listen"]');
  }
  out.errors = errors;
  dom.window.close();
  return out;
}

(async function () {
  const res = {};
  res.fresh = await scenario("fresh");
  res.restored = await scenario("restored");
  console.log(JSON.stringify(res));
  process.exit(0);
})().catch((e) => {
  console.log(JSON.stringify(
    { fatal: String((e && e.stack) || e) }));
  process.exit(0);
});
"""


def _run_teach_driver(client, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    from test_wave28_fixes import _node_modules_candidates
    cands = _node_modules_candidates()
    if not cands:
        pytest.skip("jsdom unavailable")
    page = client.get("/").get_data(as_text=True)
    (tmp_path / "page.html").write_text(page, encoding="utf-8")
    payload = client.post("/api/solve", json={
        "question": "2x + 3 = 7"}).get_json()
    (tmp_path / "payload.json").write_text(
        json.dumps(payload), encoding="utf-8")
    (tmp_path / "teach.js").write_text(TEACH_DRIVER_JS,
                                       encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(cands)
    r = subprocess.run(
        [node, str(tmp_path / "teach.js"), str(tmp_path / "page.html"),
         str(tmp_path / "payload.json")],
        capture_output=True, text=True, env=env, timeout=180)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    if out.get("skipped"):
        pytest.skip(out["skipped"])
    return out


def test_no_teach_sign_on_a_dynamically_added_card(client,
                                                   tmp_path):
    out = _run_teach_driver(client, tmp_path)
    assert "fatal" not in out, out
    for mode in ("fresh", "restored"):
        s = out[mode]
        # ANY window error during boot or submit fails the
        # smoke test.
        assert s["errors"] == [], f"{mode}: {s['errors']}"
        # The answer card really arrived via the app's own flow.
        assert s["cardAppeared"] is True, f"{mode}: {s}"
        # The control on the same card works.
        assert s["adviceToggled"] is True, f"{mode}: {s}"
        # Wave 120: the play/teach sign never appears; the
        # speaker (Listen) is the row's only voice sign.
        assert s["teachAbsent"] is True, f"{mode}: {s}"
        assert s["listenPresent"] is True, f"{mode}: {s}"
