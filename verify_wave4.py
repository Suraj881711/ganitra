"""Wave-4 verification: multi-language UI (en/hi/bn/mr/ta/te), language
switcher with session persistence, localised explanation line on the
answer page, and voice-input language following the UI language.

Note: real speech recognition in each language can only be exercised
in a real browser with a microphone. What is verified here is the
server-visible pipeline: the switcher route, session persistence, the
rendered UI strings per language, the speech-lang value handed to the
page's JS, and the explanation line end to end.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from i18n import EXPLANATIONS, SPEECH_LANGS, STRINGS  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:28} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()

# --- 1. Default English homepage -----------------------------------------
client = app.test_client()
r = client.get("/")
body = r.get_data(as_text=True)
check("GET / (en)", r.status_code == 200, f"status={r.status_code}")
check("en hero string", "Ask any maths question" in body)
check("en tagline", STRINGS["en"]["tagline"] in body)
check("en solve button", STRINGS["en"]["solve_btn"] in body)
check("en speech lang", f'"{SPEECH_LANGS["en"]}"' in body)
check("lang switcher", 'id="lang-select"' in body
      and "/set-lang/" in body)

# --- 2. Hindi: switch, strings, persistence -------------------------------
r = client.get("/set-lang/hi")
check("set-lang hi redirects", r.status_code == 302,
      f"status={r.status_code}")
r = client.get("/")
body = r.get_data(as_text=True)
hi = STRINGS["hi"]
hindi_hits = [k for k in ("nav_solve", "solve_btn", "topics_heading",
                          "voice_btn", "hero_tag", "enter_question")
              if hi[k] in body]
check("hindi UI strings >= 3", len(hindi_hits) >= 3,
      f"found={hindi_hits}")
check("hindi is Devanagari", "हल कीजिए" in body and "अभ्यास" in body)
check("hindi speech lang", f'"{SPEECH_LANGS["hi"]}"' in body)
r = client.get("/history")
check("lang persists (history)", hi["history_heading"]
      in r.get_data(as_text=True))
r = client.get("/practice")
check("lang persists (practice)", hi["quiz_heading"]
      in r.get_data(as_text=True))

# --- 3. Hindi solve: localised explanation line ---------------------------
r = client.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("POST /solve (hi)", r.status_code == 200,
      f"status={r.status_code}")
check("hindi explanation heading",
      STRINGS["hi"]["explanation_heading"] in body)
expected_expl = EXPLANATIONS["hi"]["algebra:equation"].format(
    answer="x = 2, x = 3")
check("hindi explanation line", expected_expl in body,
      expected_expl[:60] + "…")
check("steps stay English", STRINGS["hi"]["steps_heading"] in body
      and "Step-by-step" not in body)

# --- 4. bn / mr / ta / te homepages ---------------------------------------
for code in ("bn", "mr", "ta", "te"):
    c = app.test_client()
    c.get(f"/set-lang/{code}")
    r = c.get("/")
    b = r.get_data(as_text=True)
    strings = STRINGS[code]
    check(f"GET / ({code})", r.status_code == 200,
          f"status={r.status_code}")
    check(f"{code} tagline/button",
          strings["tagline"] in b or strings["solve_btn"] in b)
    check(f"{code} speech lang", f'"{SPEECH_LANGS[code]}"' in b)

# --- 5. Invalid language falls back to English ----------------------------
c = app.test_client()
r = c.get("/set-lang/xx")
check("set-lang invalid redirects", r.status_code == 302,
      f"status={r.status_code}")
r = c.get("/")
b = r.get_data(as_text=True)
check("invalid lang -> English", STRINGS["en"]["solve_btn"] in b
      and '<html lang="en">' in b)

# --- 6. Open-redirect guard on ?next= --------------------------------------
c = app.test_client()
r = c.get("/set-lang/hi?next=https://evil.example.com/")
loc = r.headers.get("Location", "")
check("next= guard", "evil.example.com" not in loc, f"Location={loc}")
r = c.get("/set-lang/hi?next=/history")
check("next= local ok", r.headers.get("Location", "").endswith("/history"),
      f"Location={r.headers.get('Location')}")

# --- 7. English explanation line (default session) -------------------------
c = app.test_client()
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
b = r.get_data(as_text=True)
expected_en = EXPLANATIONS["en"]["algebra:equation"].format(
    answer="x = 2, x = 3")
check("en explanation line", expected_en in b, expected_en[:60] + "…")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
