"""Wave 98: kam-net (offline-basic) mode.

When the phone has no/slow internet the chat page must still
(a) load from the service-worker cache — the worker now
PRECACHES the chat shell on install (page, pinned stylesheet,
the offline evaluator, the two logo files the chat shows, the
typing-boy sprite, favicon, manifest) instead of caching only
whatever a visit happened to fetch; and
(b) answer BASIC arithmetic locally in the browser when the
/api/solve fetch fails or times out (45 s abort): a small
client-side evaluator (static/offline.js) for + - × ÷,
fractions, percentages, squares/roots and simple one-step
equations, rendered through the very same addAnswerBubble
house card. Anything beyond basics returns null in the
evaluator and the page shows the honest localised
check-your-connection one-liner (i18n chat_offline_note) —
never a fake answer. When the server answers, nothing in
the flow changes.

The evaluator is exercised for real under node (the same
file the browser loads); the wiring and the cache manifest
are asserted as text, like the other wave tests.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
OFFLINE_JS = ROOT / "static" / "offline.js"

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None,
                                reason="node not available")


def _run_evaluator(questions):
    script = (
        "const G = require(%s);\n"
        "const qs = JSON.parse(process.argv[1]);\n"
        "process.stdout.write(JSON.stringify("
        "qs.map(q => G.solve(q))));\n"
    ) % json.dumps(str(OFFLINE_JS))
    out = subprocess.run(
        [NODE, "-e", script, json.dumps(questions)],
        capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


# ------------------------------------------------------------------
# The offline evaluator itself (real runs under node)
# ------------------------------------------------------------------

@needs_node
def test_offline_plain_arithmetic():
    res = _run_evaluator(["12 * 5", "144 / 12", "7 + 8", "100 - 37",
                          "(2 + 3) * 4", "2.5 * 4", "2^10"])
    assert [r["answer"] for r in res] == \
        ["60", "12", "15", "63", "20", "10", "1024"]
    assert all(r["type"] == "arithmetic" and r["op"] == "evaluate"
               for r in res)
    # House style: plain solving lines, no numbering/labels.
    assert res[0]["steps"] == ["12 × 5 = 60"]


@needs_node
def test_offline_fractions():
    res = _run_evaluator(["3/4 + 1/2", "3/6", "1 1/2 + 1/2",
                          "1/2 of 60", "2/3 of 90"])
    assert [r["answer"] for r in res] == \
        ["5/4", "1/2", "2", "30", "60"]
    assert res[3]["type"] == "junior"
    assert res[3]["op"] == "fraction_of"
    # Same step wording as the server's fraction-of family.
    assert res[3]["steps"][0] == \
        "Divide 60 into 2 equal parts: 60 ÷ 2 = 30"


@needs_node
def test_offline_percentages():
    res = _run_evaluator(["15% of 200", "25% of 80", "50% of 36",
                          "200 ka 15 persent",
                          "what is 15% of 200?"])
    assert [r["answer"] for r in res] == ["30", "20", "18", "30", "30"]
    # Byte-identical step style to the server solver's output.
    assert res[0]["steps"] == [
        "15% means 15/100 = 0.15",
        "Multiply by 200: 0.15 × 200 = 30"]
    assert res[0]["type"] == "arithmetic"
    assert res[0]["op"] == "percentage"


@needs_node
def test_offline_powers_and_roots():
    res = _run_evaluator(["5 squared", "cube of 3",
                          "square root of 144", "√81",
                          "square root of 50"])
    assert [r["answer"] for r in res] == \
        ["25", "27", "12", "9", "≈ 7.0711"]
    assert res[2]["type"] == "exponents_logs"
    assert res[2]["op"] == "nth_root"


@needs_node
def test_offline_simple_equations():
    res = _run_evaluator(["x + 5 = 12", "x - 7 = 9", "2x + 3 = 7",
                          "3x = 12", "x/4 = 5", "10 - x = 4",
                          "12/x = 3"])
    assert [r["answer"] for r in res] == \
        ["x = 7", "x = 16", "x = 2", "x = 4", "x = 20",
         "x = 6", "x = 4"]
    assert all(r["type"] == "algebra" and r["op"] == "equation"
               for r in res)
    # The final step restates the answer (the chat renderer
    # drops it, exactly as it does for server answers).
    assert res[0]["steps"][-1] == "x = 7"


@needs_node
def test_offline_refuses_beyond_basics():
    """Anything that is not basic arithmetic MUST come back
    null so the page shows the honest offline line instead
    of a guessed answer."""
    res = _run_evaluator([
        "what is the capital of india",
        "a train travels 360 km in 4 hours, find its speed",
        "find the area of a circle with radius 7 cm",
        "if a shirt costs 500 and discount is 20 percent find price",
        "hello", "", "42", "10/0", "x + y = 5",
        "solve the quadratic equation x^2 - 5x + 6 = 0",
    ])
    assert res == [None] * len(res)


# ------------------------------------------------------------------
# Chat-page wiring
# ------------------------------------------------------------------

def test_offline_script_loaded_before_chat_script():
    tag = "filename='offline.js'"
    assert tag in INDEX
    # The evaluator must exist before the chat IIFE runs.
    assert INDEX.index(tag) < INDEX.index("var CHAT = {")


def test_submit_handler_falls_back_offline_only_on_failure():
    assert "window.GanitraOffline.solve(question)" in INDEX
    # The offline answer rides the same house card renderer.
    assert "addAnswerBubble(question, odata)" in INDEX
    assert 'offline: true' in INDEX
    # Beyond-basics: the honest one-liner, from i18n.
    assert "CHAT.offlineNote" in INDEX
    assert "chat_offline_note" in INDEX
    # The classic form fallback survives ONLY for the case
    # where the evaluator script itself never loaded.
    catch = INDEX.index("window.GanitraOffline.solve(question)")
    classic = INDEX.index("form.submit()", catch)
    assert classic > catch


def test_solve_fetch_has_a_timeout():
    assert "AbortController" in INDEX
    assert "45000" in INDEX
    assert "solveCtl.abort()" in INDEX


def test_offline_note_string_in_all_languages():
    import i18n
    for lang in i18n.SUPPORTED_LANGS:
        note = i18n.get_strings(lang).get("chat_offline_note")
        assert note and len(note) > 10, lang


# ------------------------------------------------------------------
# Service worker: pins + shell precache
# ------------------------------------------------------------------

def test_sw_cache_name_bumped():
    assert 'GANITRA_CACHE = "ganitra-static-v31"' in SW


def test_stylesheet_pin_bumped():
    assert "v='54'" in BASE
    assert "v='39'" not in BASE


def test_sw_precaches_the_chat_shell():
    assert "GANITRA_SHELL" in SW
    for url in ("/",
                "/static/style.css?v=54",
                "/static/offline.js",
                "/static/logo-mark-t.png",
                "/static/logo-full-t.png",
                "/static/scene-boy.webp?v=29",
                "/static/favicon.png",
                "/manifest.webmanifest"):
        assert '"%s"' % url in SW, url
    # Install waits for the precache, tolerating single
    # failures, and still activates immediately.
    install = SW[SW.index('"install"'):SW.index('"activate"')]
    assert "cache.add(url)" in install
    assert "skipWaiting" in install
    # The fetch rules are the Wave-25/26 ones, unchanged:
    # code network-first with revalidation, navigations
    # network-first with the cached shell as fallback.
    assert 'cache: "no-cache"' in SW
    assert 'req.mode === "navigate"' in SW
