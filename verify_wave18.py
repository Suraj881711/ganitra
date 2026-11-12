"""Wave-18 verification: COMFORT + NO DEAD-END ANSWERS.

Contract (Suraj, 10 Nov 2026, ~23:24 IST): "Muse or ChatGPT ki
tarah comfortable hona chahiye, har ek question ka answer milna
chahiye" — copy the COMFORT of Muse/ChatGPT, not their layout
(the premium warm design stays; the ChatGPT-style layout was
rejected in Wave 7).

Part A — no dead-end (fallback.py + concepts.py):
  * A REAL solver answer is returned untouched (no fallback flag).
  * Solver failures, letter-soup "answers" (sympy multiplying
    unknown words), and soft non-answers ("Tell me the data...")
    are routed through the layers: salvage (solve the maths
    core inside a messy question) -> concepts (curated formula
    + worked example) -> similar example (honestly labelled) ->
    friendly vague/gibberish/guide replies.
  * Greetings and known non-maths questions get friendly
    replies, never fake answers.
  * NO battery question returns an error/empty answer, and
    every fallback result is flagged (fallback=True) and never
    uses op == "error".

Part B — comfort (static checks on templates/index.html +
static/style.css; the thinking indicator, fade-in, auto-grow
composer, Enter/Shift+Enter and focus-return predate Wave 18
and are asserted to still exist):
  * thinking indicator template + animated dots CSS
  * answer fade-in keyframes
  * stick-to-bottom scrolling that respects a scrolled-up user
  * 📋 Copy and 🔁 Explain-more-simply buttons wired in the
    answer renderer, labels from the Wave-18 i18n keys (all 6
    languages complete)

Run:  python verify_wave18.py
"""
import hashlib
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

RUN_ID = uuid.uuid4().hex[:8]
_DB = f"/tmp/ganitra-verify-wave18-{RUN_ID}.db"
os.environ["GANITRA_DB_PATH"] = _DB
for suffix in ("", "-wal", "-shm"):
    try:
        os.remove(_DB + suffix)
    except OSError:
        pass

from fallback import fallback_answer  # noqa: E402
from i18n import STRINGS  # noqa: E402

ROOT = Path(__file__).parent
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


def kind_of(result):
    return result.get("fallback_kind", "REAL")


def presentable(result):
    """A result a student may be shown: non-empty answer, never
    a raw solver error."""
    ans = str(result.get("answer", "") or "").strip()
    return (bool(ans) and result.get("op") != "error"
            and not ans.startswith("Could not solve"))


# --- Battery: (question, expected kind, substring in answer) ------------------
BATTERY = [
    # REAL solver answers — must stay real and untouched
    ("2+2*5", "REAL", "12"),
    ("solve x^2 - 5x + 6 = 0", "REAL", "x = 2"),
    ("integrate x^2 from 0 to 1", "REAL", "1/3"),
    ("sin 30", "REAL", "1/2"),
    ("mean of 2, 4, 6, 8", "REAL", "5"),
    ("derivative of x^3 + 2x", "REAL", "3"),
    ("area of circle with radius 5", "REAL", "78.5"),
    ("5 aur 3 ko jodo", "REAL", "8"),
    ("what is 15% of 200 batao", "REAL", "30"),
    ("240 ka 15 pratishat kitna hoga", "REAL", "36"),
    ("find the hcf of 12 and 18", "REAL", "6"),
    ("lcm of 4 and 6", "REAL", "12"),
    ("what is the value of pi", "REAL", "3.14159"),
    ("simplify (x^2-1)/(x-1)", "REAL", "x + 1"),
    ("expand (x+2)(x+3)", "REAL", "5"),
    ("10th term of AP 2, 5, 8", "REAL", "29"),
    # Concepts — en + Hinglish
    ("what is pythagoras theorem", "concept", "a² + b²"),
    ("pythagoras theorem kya hai", "concept", "Pythagoras"),
    ("quadratic formula kya hota hai", "concept", "4ac"),
    ("discriminant kya hota hai", "concept", "b² - 4ac"),
    ("what is bodmas", "concept", "Brackets"),
    ("bodmas kya hai", "concept", "BODMAS"),
    ("simple interest ka formula", "concept", "P × R × T"),
    ("what is probability", "concept", "favourable"),
    ("probability kya hoti hai", "concept", "Probability"),
    ("hcf aur lcm me kya antar hai", "concept", "HCF"),
    ("what is a prime number", "concept", "Prime"),
    ("abajya sankhya kya hoti hai", "concept", "Prime"),
    ("area of circle formula", "concept", "πr²"),
    ("perimeter of rectangle", "concept", "Perimeter"),
    ("mean median mode kya hai", "concept", "Median"),
    ("ap ka nth term", "concept", "(n - 1)d"),
    ("distance speed time formula", "concept", "Speed × Time"),
    ("percentage kaise nikale", "concept", "Percentage"),
    ("sin^2 + cos^2 = 1 prove karo", "concept", "sin²θ + cos²θ = 1"),
    ("prove that root 2 is irrational", "concept", "Irrational"),
    ("factorial kya hota hai", "concept", "n!"),
    ("what is algebra", "concept", "Algebra"),
    ("trigonometry kya hai", "concept", "sin θ"),
    ("theorem kya hota hai", "concept", "Theorem"),
    # Salvage — a solvable core inside a messy question
    ("a train covers 25 x 4 km in a journey, how far did it go",
     "salvage", "100"),
    ("my homework says find x when 3x + 7 = 22 please help me batao",
     "salvage", "x = 5"),
    ("2 + 2 kitna hota hai batao please", "salvage", "4"),
    ("please solve this equation for me 4x - 8 = 16 batao",
     "salvage", "x = 6"),
    # Similar example — honestly labelled, different numbers
    ("ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 rupaye "
     "ki kharidi kitne bache", "similar", "Similar example"),
    ("ek train 60 km/h se 2 ghante chalti hai kitni door gayi",
     "similar", "Similar example"),
    # Greetings / small talk
    ("hello", "greeting", "Hello"),
    ("hi", "greeting", "Hello"),
    ("kaise ho", "greeting", "Namaste"),
    ("thank you", "greeting", "welcome"),
    ("tum kaun ho", "greeting", "Ganitra"),
    ("namaste", "greeting", "Namaste"),
    # Non-maths — friendly maths-only reply, no fake answer
    ("what is the capital of india", "nonmaths", "maths"),
    ("cricket ka score kya hai", "nonmaths", "maths"),
    ("photosynthesis kya hai", "nonmaths", "ganit"),
    ("why is sky blue", "nonmaths", "maths"),
    # Gibberish
    ("asdf qwer zxq", "gibberish", "maths question"),
    ("xkcd blah zzz", "gibberish", "maths question"),
    ("blorp snizzle wumpus", "gibberish", "maths question"),
    # Vague asks
    ("ye wala samjhao", "vague", "sawal"),
    ("samjhao", "vague", "sawal"),
    ("solve this", "vague", "explain"),
    ("help me", "vague", "explain"),
    # Guide — the honest last resort, still a real reply
    ("?", "guide", "couldn't solve"),
    ("what is the formula for volume of sphere", "guide",
     "couldn't solve"),
]

for q, want_kind, want_text in BATTERY:
    r = fallback_answer(q)
    ok_kind = kind_of(r) == want_kind
    ok_text = want_text in str(r.get("answer", ""))
    ok_show = presentable(r)
    flag_ok = (r.get("fallback") is True) if want_kind != "REAL" \
        else ("fallback" not in r)
    check(f"battery [{want_kind}] {q[:38]!r}",
          ok_kind and ok_text and ok_show and flag_ok,
          f"kind={kind_of(r)} ans={str(r.get('answer', ''))[:44]!r}")

# Empty-ish input still gets a friendly, non-error reply.
for q in ("", "   "):
    r = fallback_answer(q)
    check(f"battery [guide] empty {q!r}",
          kind_of(r) == "guide" and presentable(r),
          f"kind={kind_of(r)}")

# --- Honesty: labels on the non-exact layers ----------------------------------
r = fallback_answer(
    "ek train 60 km/h se 2 ghante chalti hai kitni door gayi")
steps_text = " ".join(r.get("steps") or [])
check("similar example is labelled + asks for exact numbers",
      str(r.get("answer", "")).startswith("Similar example")
      and "exact" in steps_text)
r = fallback_answer(
    "my homework says find x when 3x + 7 = 22 please help me batao")
check("salvage says it solved the maths part",
      (r.get("steps") or [""])[0].startswith(
          "Solved the maths part"))

# --- Concepts library integrity (spot-check the maths itself) ------------------
from concepts import CONCEPTS, get_concept  # noqa: E402
check("concepts library size", len(CONCEPTS) >= 18,
      f"count={len(CONCEPTS)}")
check("pythagoras formula correct",
      "c² = a² + b²" in get_concept("pythagoras")["formula"])
check("SI worked example = 100",
      "100" in get_concept("simple_interest")["example"]["answer"])
check("probability worked example = 1/6",
      get_concept("probability")["example"]["answer"] == "1/6")
check("BODMAS worked example = 14, not 20",
      get_concept("bodmas")["example"]["answer"].startswith("14"))
check("factorial worked example = 120",
      "120" in get_concept("factorial")["example"]["answer"])
check("AP worked example = 29",
      "29" in get_concept("ap_gp")["example"]["answer"])

# --- API + classic routes ------------------------------------------------------
from app import create_app  # noqa: E402

app = create_app()
client = app.test_client()
USER = {"name": "W18 User " + RUN_ID, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w18test-pass"}
r = client.post("/signup", data=USER)
check("signup succeeds", r.status_code == 302,
      f"status={r.status_code}")

r = client.post("/api/solve",
                json={"question": "what is pythagoras theorem"})
d = r.get_json() or {}
res = d.get("result") or {}
check("api concept ask -> ok + concept fallback",
      d.get("ok") is True and res.get("fallback_kind") == "concept"
      and "Pythagoras" in str(res.get("answer", "")),
      f"ok={d.get('ok')} kind={res.get('fallback_kind')}")
check("api concept ask is NOT the unsolvable card",
      "unsolvable" not in d)

r = client.post("/api/solve", json={"question": "hello"})
d = r.get_json() or {}
check("api greeting -> ok",
      d.get("ok") is True
      and (d.get("result") or {}).get("fallback_kind")
      == "greeting")

r = client.post("/api/solve", json={"question": "asdf qwer zxq"})
d = r.get_json() or {}
check("api gibberish -> ok friendly reply, not error card",
      d.get("ok") is True
      and (d.get("result") or {}).get("fallback_kind")
      == "gibberish")

r = client.post("/api/solve", json={"question": "2+2*5"})
d = r.get_json() or {}
res = d.get("result") or {}
check("api real solve untouched by the fallback",
      d.get("ok") is True and "fallback" not in res
      and str(res.get("answer", "")) == "12",
      f"ans={res.get('answer')}")

r = client.post("/solve", data={"question": "what is bodmas"})
body = r.get_data(as_text=True)
check("classic concept ask renders the concept, no error card",
      r.status_code == 200 and "BODMAS" in body
      and "error-card" not in body)
r = client.post("/solve", data={"question": "2+2*5"})
body = r.get_data(as_text=True)
check("classic real solve still renders its answer",
      r.status_code == 200 and "12" in body)

# --- Part B: comfort wiring (static) --------------------------------------------
index_src = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")
css_src = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
check("thinking indicator template present",
      'id="typing-template"' in index_src
      and "chat_thinking" in index_src)
check("thinking dots animated (CSS)",
      "softpulse" in css_src and ".dots i" in css_src)
check("answers fade in (CSS rise keyframes on bubbles)",
      "@keyframes rise" in css_src
      and "animation: rise" in css_src)
check("composer auto-grows + Enter sends + Shift+Enter newline",
      "box.scrollHeight" in index_src
      and 'ev.key === "Enter"' in index_src
      and "ev.shiftKey" in index_src)
check("focus returns to composer after an answer",
      "box.focus()" in index_src)
check("scroll respects a scrolled-up user (stick-to-bottom)",
      "stickBottom" in index_src and "updateStick" in index_src
      and 'addEventListener("scroll", updateStick' in index_src)
check("copy button wired (clipboard + fallback)",
      "mm_copy_btn" in index_src and "clipboard.writeText"
      in index_src and "execCommand" in index_src)
check("teach playback wired (step-video: voice + synced board)",
      "startTeachPlayback" in index_src
      and 'setAttribute("data-role", "teach")' in index_src
      and "teach-playing" in css_src
      and "teach-wait" in index_src and "teach-now" in index_src)
check("answer actions = exactly 4 sign-only buttons",
      all(tok in index_src for tok in (
          'dataset.action = "copy"', 'dataset.action = "listen"',
          'dataset.action = "teach"', 'dataset.action = "methods"'))
      and "🔁" not in index_src and "👩‍🏫" not in index_src)
check("method rows are full-width tap targets (wave 21)",
      "method-row-btn" in index_src and "method-row-btn" in css_src
      and "showMethodFailed" in index_src)
check("Wave-18 CSS block appended",
      "Wave 18 comfort" in css_src and ".util-btn" in css_src)
for key in ("mm_copy_btn", "mm_copied", "mm_simple_btn"):
    check(f"i18n {key} in all 6 languages",
          all(key in STRINGS[code] for code in STRINGS))

# --- Frozen logos ----------------------------------------------------------------
for name, want in (("logo-full.png",
                    "8ffea6f4e42d3d3b1bd8552e26579c4c"),
                   ("logo-mark.png",
                    "5a190086234946460217a93148632125")):
    digest = hashlib.md5(
        (ROOT / "static" / name).read_bytes()).hexdigest()
    check(f"frozen logo {name} untouched", digest == want, digest)

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
