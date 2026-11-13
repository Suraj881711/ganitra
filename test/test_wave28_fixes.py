"""Wave 28 (Suraj, 13 Nov 2026): fix the two REAL failures
the Wave 27 LIVE verification found (the local suite was
green; the live site was not).

Failure 1 — scenes never played live. Reproduced in jsdom
against the real served page (see the boot driver below):
with document.hidden true when the first-scene timer fired —
a background-opened tab, an automated checker, a phone waking
up — playNext re-armed with the 25-75s gap, DEMOTING the
guaranteed 2-4s first scene to "maybe in a minute";
visibilitychange re-armed the long gap too. And the
parse-time sprite probe (img.complete && naturalWidth === 0)
plus the error -> stopScenes wiring meant ONE sprite that
had failed by parse time silenced every scene for the whole
session. The init-exception theory was tested and excluded:
the untouched page boots with zero window errors and plays
on time when visible with healthy sprites.

The fix is structural, and this file's BOOT SMOKE TEST is
the permanent guard: it executes the served page's full
script set in jsdom, in order, with real timers, fails on
ANY window error, and asserts a scene is scheduled inside
the 2-4s window and plays — on a fresh load, on a simulated
second load, after a hidden->visible flip, and with one
sprite broken (the other scenes must still play).

Failure 2 (cosmetic) — a .txt/.pdf upload's answer page
still said "फ़ोटो से पढ़ा गया प्रश्न" and carried the OCR
misread warning. The upload now reports its source
(photo / file / file-ocr) through the /photo-solve form;
the answer page words the box by source in all 6 languages
(file_heading / file_text / file_ocr_text), and the OCR
warning appears only when OCR actually ran.
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
        "name": "W28 Fixes Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w28-fixes-pass"})
    return c


# --- Failure 1: structural pins --------------------------------

def test_first_scene_is_owed_until_it_plays():
    assert "var firstPending = true;" in INDEX
    assert "schedule(firstPending);" in INDEX
    # playNext's hidden branch re-arms at the same urgency —
    # the old demotion line is gone.
    assert "if (document.hidden) { schedule(); return; }" not in INDEX


def test_sprite_kill_switch_removed():
    # The parse-time probe + global stop wiring is gone…
    assert "if (img.complete && img.naturalWidth === 0) stopScenes();" \
        not in INDEX
    assert 'addEventListener("error", stopScenes)' not in INDEX
    # …replaced by per-sprite broken tracking + a load probe.
    assert "function markBroken(shortName)" in INDEX
    assert 'window.addEventListener("load", function () {' in INDEX
    assert "pickSceneName(lastScene, null, broken)" in INDEX
    assert "SCENE_SPRITES" in INDEX


def test_tesseract_no_longer_blocks_the_parser():
    assert '<script defer src="https://cdn.jsdelivr.net/npm/' \
           'tesseract.js@5/dist/tesseract.min.js"></script>' in INDEX


def test_sprite_urls_versioned_everywhere(client):
    page = client.get("/").get_data(as_text=True)
    # Preload + stage <img> for each sprite; the boy also has
    # two JS-built writer sprites in the inline scripts.
    assert page.count("scene-eagle.webp?v=28") == 2
    assert page.count("scene-tiger.webp?v=28") == 2
    assert page.count("scene-boy.webp?v=28") == 4
    # No unversioned sprite URL survives anywhere in the page:
    # every mention of a sprite file carries the version query.
    for name in ("eagle", "tiger", "boy"):
        assert page.count(f"scene-{name}.webp") \
            == page.count(f"scene-{name}.webp?v=28"), name
    # The two JS-built boy-writer sprites use the versioned URL.
    assert INDEX.count('"/static/scene-boy.webp?v=28"') == 2


def test_delivery_versions_wave28():
    assert "v='28'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v5"' in SW
    for old in ("ganitra-static-v4", "ganitra-static-v3",
                "ganitra-static-v2", "ganitra-static-v1"):
        assert old not in SW


# --- Failure 2: file wording ------------------------------------

def _photo_solve(client, source_marker):
    data = {"question": "Solve 2x + 3 = 7"}
    if source_marker is not None:
        data["source"] = source_marker
    r = client.post("/photo-solve", data=data)
    assert r.status_code == 200
    return r.get_data(as_text=True)


def test_file_source_gets_file_wording_without_ocr_warning(client):
    import i18n
    en = i18n.get_strings("en")
    page = _photo_solve(client, "file")
    assert en["file_heading"] in page
    assert en["file_text"] in page
    assert en["photo_heading"] not in page
    # The OCR warning (photo_text) must NOT appear for clean
    # text-layer extraction.
    assert en["photo_text"] not in page
    assert "OCR sometimes misreads" not in page


def test_file_ocr_source_gets_file_heading_with_ocr_warning(client):
    import i18n
    en = i18n.get_strings("en")
    page = _photo_solve(client, "file-ocr")
    assert en["file_heading"] in page
    # (Asserted in fragments: Jinja escapes the apostrophe in
    # "file's" when rendering.)
    assert "was read like a photo" in page
    assert "(OCR sometimes misreads a number or sign" in page
    assert en["photo_heading"] not in page


def test_photo_source_unchanged(client):
    import i18n
    en = i18n.get_strings("en")
    for marker in ("photo", None, "garbage-value"):
        page = _photo_solve(client, marker)
        assert en["photo_heading"] in page
        assert en["photo_text"] in page
        assert en["file_heading"] not in page


def test_file_wording_in_hindi(client):
    import i18n
    hi = i18n.get_strings("hi")
    client.get("/set-lang/hi")
    page = _photo_solve(client, "file")
    assert hi["file_heading"] in page
    assert hi["photo_heading"] not in page
    assert hi["photo_text"] not in page


def test_file_keys_in_all_languages_without_ocr_in_clean_text():
    import i18n
    for lang in ("en", "hi", "bn", "mr", "ta", "te"):
        s = i18n.get_strings(lang)
        assert s["file_heading"], lang
        assert s["file_text"], lang
        assert s["file_ocr_text"], lang
        # Clean-extraction copy never mentions OCR; the OCR
        # variant always does.
        assert "OCR" not in s["file_text"], lang
        assert "OCR" in s["file_ocr_text"], lang
        assert "📄" in s["file_heading"], lang


def test_upload_flow_reports_its_source():
    # The hidden form carries the source; the JS sets it per
    # path (photo default, file for clean text, file-ocr for a
    # scanned page).
    assert 'id="photo-source"' in INDEX
    assert 'sendQuestionText(d.text, "file")' in INDEX
    assert 'ocrBlob(blob, "file-ocr")' in INDEX


# --- The boot smoke test -----------------------------------------

BOOT_DRIVER_JS = r"""
const fs = require("fs");
let JSDOM, VirtualConsole;
try { ({ JSDOM, VirtualConsole } = require("jsdom")); }
catch (e) {
  console.log(JSON.stringify({ skipped: "jsdom unavailable" }));
  process.exit(0);
}
const html = fs.readFileSync(process.argv[2], "utf8");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function makeDom(mode) {
  const errors = [];
  const timeouts = [];
  let hiddenNow = mode === "hiddenflip";
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => {
    errors.push("jsdomError: " +
      (e.detail && e.detail.message || e.message));
  });
  vc.on("error", (m) => errors.push("console.error: " + m));
  const dom = new JSDOM(html, {
    url: "https://localhost/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      window.addEventListener("error", (ev) => {
        errors.push("window.onerror: " + ev.message);
      });
      const realSetTimeout = window.setTimeout.bind(window);
      window.setTimeout = function (fn, delay) {
        timeouts.push(delay);
        return realSetTimeout(fn, delay);
      };
      window.fetch = function (url, opts) {
        const u = String(url);
        let body = { ok: true };
        if (u.indexOf("/api/chats") >= 0
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
      if (!("speechSynthesis" in window)) {
        window.SpeechSynthesisUtterance = function (text) {
          this.text = text || ""; this.lang = "";
          this.addEventListener = function () {};
        };
        window.speechSynthesis = {
          getVoices: function () { return []; },
          speak: function () {}, cancel: function () {},
          addEventListener: function () {},
          speaking: false, pending: false, paused: false
        };
      }
      /* Sprites: model the production truth (they serve 200).
         brokeneagle: only the eagle reports no pixels. */
      Object.defineProperty(window.HTMLImageElement.prototype,
        "naturalWidth", { configurable: true,
          get: function () {
            if (mode === "brokeneagle"
                && this.id === "scene-eagle") return 0;
            return 384;
          } });
      Object.defineProperty(window.HTMLImageElement.prototype,
        "complete", { configurable: true,
          get: function () { return true; } });
      if (mode === "hiddenflip") {
        Object.defineProperty(window.document, "hidden",
          { configurable: true,
            get: function () { return hiddenNow; } });
        Object.defineProperty(window.document, "visibilityState",
          { configurable: true,
            get: function () {
              return hiddenNow ? "hidden" : "visible"; } });
      }
    }
  });
  return { dom, errors, timeouts,
           flip: function () {
             hiddenNow = false;
             dom.window.document.dispatchEvent(
               new dom.window.Event("visibilitychange"));
           } };
}

async function watchScene(dom, timeoutMs) {
  const stage = dom.window.document.getElementById("scene-stage");
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const m = (stage.className || "")
      .match(/playing-(eagle|tiger|chase)/);
    if (m) return m[1];
    await sleep(100);
  }
  return null;
}

async function scenario(mode, flipAfterMs) {
  const { dom, errors, timeouts, flip } = makeDom(mode);
  let scene = null;
  if (flipAfterMs) {
    const watching = watchScene(dom, flipAfterMs + 6000);
    await sleep(flipAfterMs);
    flip();
    scene = await watching;
  } else {
    scene = await watchScene(dom, 7000);
  }
  const firstBand = timeouts.filter(
    (d) => d >= 2000 && d < 4000);
  const out = { scene: scene, errors: errors,
                firstBandCount: firstBand.length,
                emptyPresent: !!dom.window.document
                  .getElementById("chat-empty") };
  dom.window.close();
  return out;
}

(async function () {
  const res = {};
  res.fresh = await scenario("fresh", 0);
  res.second = await scenario("fresh", 0);
  res.hiddenflip = await scenario("hiddenflip", 1000);
  res.brokeneagle = await scenario("brokeneagle", 0);
  console.log(JSON.stringify(res));
  process.exit(0);
})();
"""


def _node_modules_candidates():
    cands = []
    env = os.environ.get("GANITRA_NODE_MODULES")
    if env:
        cands.append(env)
    cands.append("/tmp/w28-jsdom/node_modules")
    cands.append("/tmp/w23-jsdom/node_modules")
    cands.append(str(Path.home() / "workspace" / ".w24-scratch"
                     / "jsdom" / "node_modules"))
    return [p for p in cands if (Path(p) / "jsdom").is_dir()]


def test_boot_smoke_scenes_play_on_every_load(client, tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    cands = _node_modules_candidates()
    if not cands:
        pytest.skip("jsdom unavailable")
    page = client.get("/").get_data(as_text=True)
    (tmp_path / "page.html").write_text(page, encoding="utf-8")
    (tmp_path / "boot.js").write_text(BOOT_DRIVER_JS,
                                      encoding="utf-8")
    env = dict(os.environ)
    env["NODE_PATH"] = os.pathsep.join(cands)
    r = subprocess.run(
        [node, str(tmp_path / "boot.js"), str(tmp_path / "page.html")],
        capture_output=True, text=True, env=env, timeout=180)
    out = json.loads(r.stdout.strip().splitlines()[-1])
    if out.get("skipped"):
        pytest.skip(out["skipped"])
    for name in ("fresh", "second", "hiddenflip", "brokeneagle"):
        s = out[name]
        # ANY window error during boot fails the smoke test.
        assert s["errors"] == [], f"{name}: {s['errors']}"
        # A scene timer inside the 2-4s window was scheduled…
        assert s["firstBandCount"] >= 1, f"{name}: {s}"
        # …the empty state was really up…
        assert s["emptyPresent"] is True, f"{name}: {s}"
        # …and a scene actually played.
        assert s["scene"] in ("eagle", "tiger", "chase"), \
            f"{name}: {s}"
    # With the eagle broken, its scene must never be the one
    # that plays — the others carry on.
    assert out["brokeneagle"]["scene"] in ("tiger", "chase")
