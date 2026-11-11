"""Wave-9 verification: AUTO LANGUAGE.

The site stays in English by default, but when a student chats in
another language the site language switches AUTOMATICALLY:

- langdetect_local.detect_language_confident: script-based
  detection (Devanagari hi/mr, Bengali bn, Tamil ta, Telugu te) +
  Roman-script ("WhatsApp language") detection for Hinglish,
  Roman Marathi, and conservative Roman Bengali/Tamil/Telugu.
- POST /api/solve: a solid detection in a different language moves
  the session BEFORE solving; the response gains
  language_switched/language (+ ui string map and a localised
  lang_notice toast on a switch), and every localised field of
  that response is rendered in the NEW language.
- Classic POST /solve: same rule — the answer page renders in the
  detected language.
- Manual control stays king: /set-lang still just sets the
  session language; a neutral follow-up never switches it back.
- The frozen Wave-8 logo wiring is untouched.

Run with the project venv:  python verify_wave9.py
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from i18n import (LANG_NAMES, STRINGS, SUPPORTED_LANGS,  # noqa: E402
                  explanation_for, get_strings)
from langdetect_local import (detect_language,  # noqa: E402
                              detect_language_confident)

EN, HI, BN, MR, TA, TE = (STRINGS[c] for c in
                          ("en", "hi", "bn", "mr", "ta", "te"))

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


def session_lang(client):
    with client.session_transaction() as s:
        return s.get("lang")


app = create_app()

# --- 1. Detection units -------------------------------------------------------
CASES = [
    # (text, expected code, expected solid)
    ("मुझे यह सवाल समझाओ", "hi", True),                    # Devanagari Hindi
    ("यह समीकरण कैसे हल होता है", "hi", True),
    ("mujhe ye sawaal samjhao, ye kaise hota hai", "hi", True),  # Hinglish
    ("2x + 6 = 14 kaise solve karein batao", "hi", True),
    ("আমাকে এই প্রশ্নটা বুঝিয়ে দাও", "bn", True),          # Bengali script
    ("ami ei proshno bujhi na, kivabe kore", "bn", True),   # Roman Bengali
    ("இந்த சமன்பாட்டை தீர்க்கவும்", "ta", True),            # Tamil script
    ("enakku indha kelvi puriyala, eppadi sollu", "ta", True),  # Roman Tamil
    ("ఈ సమీకరణాన్ని పరిష్కరించండి", "te", True),            # Telugu script
    ("naaku ee prashna ardham kaaledu, ela cheppu", "te", True),  # Roman Telugu
    ("मला हा प्रश्न समजत नाहीये, सांगा ना कसा करायचा", "mr", True),  # Deva Marathi
    ("हे समीकरण सोडवा", "mr", True),
    ("mala ha prashna samjat nahiye, sanga na kasa karaycha",
     "mr", True),                                            # Roman Marathi
    ("mala he sodva", "mr", True),
    ("maza abhyas ahe, mala sanga", "mr", True),
    ("solve this equation for x", "en", True),               # plain English
    ("what is the value of sin 30", "en", True),
    ("find the roots of the quadratic equation", "en", True),
    ("x^2-5x+6=0", "en", False),                             # pure maths: no signal
    ("2x+3=7", "en", False),
    ("sin 30", "en", False),
    ("", "en", False),
]
for text, want, want_solid in CASES:
    got, solid = detect_language_confident(text)
    check(f"detect {text[:34]!r}", got == want and solid == want_solid,
          f"got=({got},{solid}) want=({want},{want_solid})")
check("detect_language() agrees",
      detect_language("mala ha prashna samjat nahiye") == "mr"
      and detect_language("solve this equation for x") == "en")

# --- 2. API: Devanagari Hindi chat auto-switches -------------------------------
c = app.test_client()
r = c.post("/api/solve", json={"question": "x^2-5x+6=0 को हल करो"})
data = r.get_json() or {}
check("api Hindi question solved", r.status_code == 200
      and data.get("ok") is True, f"status={r.status_code}")
check("api Hindi switch flags", data.get("language_switched") is True
      and data.get("language") == "hi")
check("api Hindi explanation localised",
      data.get("explanation")
      == explanation_for(data.get("result") or {}, "hi")
      and data.get("explanation")
      != explanation_for(data.get("result") or {}, "en"),
      f"explanation={data.get('explanation')!r}")
check("api Hindi toast in Hindi",
      data.get("lang_notice") == HI["lang_switched_toast"].format(
          lang=LANG_NAMES["hi"]), f"notice={data.get('lang_notice')!r}")
ui = data.get("ui") or {}
check("api switch carries ui map",
      ui.get("question_placeholder") == HI["question_placeholder"]
      and ui.get("chat_thinking") == HI["chat_thinking"]
      and ui.get("nav_board") == HI["nav_board"]
      and ui.get("speech_lang") == "hi-IN",
      f"ui keys={len(ui)}")
check("session language now hi", session_lang(c) == "hi",
      f"session={session_lang(c)}")

# Follow-up neutral maths: no switch back, still served in Hindi.
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("api follow-up keeps Hindi", data.get("language_switched") is False
      and data.get("language") == "hi"
      and data.get("explanation")
      == explanation_for(data.get("result") or {}, "hi"))
check("no ui/notice when not switched",
      "ui" not in data and "lang_notice" not in data)

# --- 3. API: plain English never switches --------------------------------------
c = app.test_client()
r = c.post("/api/solve", json={"question": "solve this equation for x"})
data = r.get_json() or {}
check("api English stays English", data.get("language_switched") is False
      and data.get("language") == "en",
      f"data={ {k: data.get(k) for k in ('ok', 'language')} }")
check("session still en/unset", session_lang(c) in (None, "en"),
      f"session={session_lang(c)}")
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("api pure maths no switch", data.get("language_switched") is False
      and data.get("language") == "en" and data.get("ok") is True)

# --- 4. API: Roman Marathi (WhatsApp language) switches to mr ------------------
c = app.test_client()
r = c.post("/api/solve", json={
    "question": "mala ha prashna samjat nahiye, sanga na kasa karaycha"})
data = r.get_json() or {}
err = data.get("error") or {}
check("api Roman Marathi switch", data.get("language_switched") is True
      and data.get("language") == "mr",
      f"language={data.get('language')}")
# Wave 18 amendment: an unsolvable Marathi message now gets a
# friendly fallback answer (fallback.py), not the localised
# error card; the language switch itself is unchanged and is
# what this section exists to prove.
check("api Marathi fallback reply (Wave 18)",
      data.get("ok") is True
      and bool((data.get("result") or {}).get("fallback_kind"))
      and "error" not in data,
      f"kind={(data.get('result') or {}).get('fallback_kind')}")
check("api Marathi toast", data.get("lang_notice")
      == MR["lang_switched_toast"].format(lang=LANG_NAMES["mr"]))
check("session language now mr", session_lang(c) == "mr")

# --- 5. API: Hinglish switches to hi; Devanagari Marathi to mr -----------------
c = app.test_client()
r = c.post("/api/solve", json={
    "question": "mujhe ye sawaal samjhao, ye kaise hota hai"})
data = r.get_json() or {}
err = data.get("error") or {}
# Wave 18 amendment: the Hinglish help-ask now returns the
# Hindi fallback guide ("...exact hal...") instead of the
# Hindi error card; the switch to hi is the point of the check.
check("api Hinglish switch", data.get("language_switched") is True
      and data.get("language") == "hi"
      and data.get("ok") is True
      and "exact hal" in str(
          (data.get("result") or {}).get("answer", "")),
      f"language={data.get('language')} "
      f"ans={str((data.get('result') or {}).get('answer', ''))[:40]!r}")
c = app.test_client()
r = c.post("/api/solve", json={"question": "हे समीकरण सोडवा"})
data = r.get_json() or {}
# The solver "simplifies" this input instead of failing on it
# (pre-existing behaviour for non-English text), so localise-check
# whichever contract came back: Marathi explanation or Marathi
# error card — either proves the response renders in mr.
mr_localised = (
    (data.get("error") or {}).get("heading") == MR["error_heading"]
    or data.get("explanation")
    == explanation_for(data.get("result") or {}, "mr"))
check("api Devanagari Marathi switch",
      data.get("language_switched") is True
      and data.get("language") == "mr" and mr_localised,
      f"language={data.get('language')} ok={data.get('ok')}")

# --- 6. Manual switcher respected ----------------------------------------------
c = app.test_client()
c.get("/set-lang/mr")
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("manual mr kept for neutral maths",
      data.get("language_switched") is False
      and data.get("language") == "mr"
      and data.get("explanation")
      == explanation_for(data.get("result") or {}, "mr"))
c.get("/set-lang/en")
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("manual en kept", data.get("language") == "en"
      and data.get("language_switched") is False)

# --- 7. Classic /solve renders in the detected language -------------------------
from solver.router import solve_question  # noqa: E402

c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0 को हल करो"})
body = r.get_data(as_text=True)
expected_hi = explanation_for(solve_question("x^2-5x+6=0"), "hi")
check("classic Hindi answer page", r.status_code == 200
      and HI["answer_heading"] in body and expected_hi in body,
      f"status={r.status_code}")
check("classic session switched to hi", session_lang(c) == "hi")
c = app.test_client()
r = c.post("/solve", data={
    "question": "mujhe ye sawaal samjhao, ye kaise hota hai"})
body = r.get_data(as_text=True)
# Wave 18 amendment: the classic page renders the Hindi
# fallback guide for this Hinglish help-ask (still fully in
# Hindi, still never the English error card).
check("classic Hinglish fallback page in Hindi",
      r.status_code == 200
      and "exact hal" in body
      and EN["error_heading"] not in body)
c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("classic English unchanged", r.status_code == 200
      and EN["answer_heading"] in body
      and session_lang(c) in (None, "en"))

# --- 8. i18n completeness incl. the new toast -----------------------------------
base = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    check(f"i18n complete {code}",
          set(STRINGS[code]) == base
          and "lang_switched_toast" in STRINGS[code],
          f"keys={len(STRINGS[code])}")
    try:
        STRINGS[code]["lang_switched_toast"].format(
            lang=LANG_NAMES[code])
        ok = True
    except (KeyError, IndexError, ValueError):
        ok = False
    check(f"toast formats {code}", ok)

# --- 9. Client wiring + frozen logo untouched ------------------------------------
c = app.test_client()
home = c.get("/").get_data(as_text=True)
tpl = Path("templates/index.html").read_text(encoding="utf-8")
check("homepage 200 with frozen logo wiring",
      # Wave 12 (Suraj, 10 Nov 2026): pages now reference the
      # transparent presentation copies; the frozen originals on
      # disk are untouched (md5-checked in verify_wave8/11).
      "logo-full-t.png" in home and "logo-mark-t.png" in home)
check("client applies auto switch",
      "applyLanguage" in tpl and "data.language_switched" in tpl
      and 'fetch("/set-lang/" + data.language)' in tpl)
check("client toast bubble", "lang_notice" in tpl
      and "lang-note" in tpl)
CSS = Path("static/style.css").read_text(encoding="utf-8")
check("css lang-note style", ".bubble.lang-note" in CSS)

# --- 10. JS syntax (node --check) --------------------------------------------------
node = shutil.which("node")
scripts = [s for s in re.findall(r"<script>(.*?)</script>", home, re.S)
           if len(s.strip()) > 200]
if node:
    ok = True
    for s in scripts:
        with tempfile.NamedTemporaryFile(
                "w", suffix=".js", delete=False,
                encoding="utf-8") as f:
            f.write(s)
            p = f.name
        ok = ok and subprocess.run(
            [node, "--check", p], capture_output=True).returncode == 0
        os.unlink(p)
    check("JS syntax (home)", ok, f"scripts={len(scripts)}")
else:
    check("JS syntax (home)", True, "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
