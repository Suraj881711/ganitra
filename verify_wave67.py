"""Wave 67 verify: the SHORT not-found fallback.

Suraj's complaint (15 Nov 2026, phone screenshots): gibberish
("If tu gfuf") earned a huge guide card — guide text, the
"Questions I solve for sure" notebook panel, a long answer
paragraph, Teacher's Advice, the icon row. His order: unsolved
= ONE short line ("Answer not found." / "उत्तर नहीं मिला।" /
"Answer nahi mila."), nothing else.

Checks:
  A. payload level — gibberish / unsolvable inputs collapse
     to fallback_kind "not_found" with exactly the one line
     in the right language and no steps; the AI chain still
     runs before the line (proven in test_wave37/41; here:
     no keys -> the line);
  A2. Merge-5 (decided rule 1) — greetings / small talk and
     vague asks do NOT collapse: they get Wave 68's friendly
     per-flavour one line (kinds "greeting" / "vague", plain
     rendering), still one line and no steps;
  B. guards — science / nonmaths keep their own one-line
     wording with plain=True, science payload guidance intact;
  C. API level — /api/solve JSON for gibberish carries no
     explanation / advice / methods / teach; a solved
     question's payload is byte-for-byte the old shape; the
     chat page ships the Wave-67 minimal-bubble gate; the
     classic /solve page for gibberish shows the line with no
     advice section;
  D. browser level (when the tools venv + headless Chromium
     are available) — a real chat: gibberish renders as a
     single-line bubble with NO icon row / advice card /
     steps section in the DOM, and a solved answer renders
     the full card exactly as before. Screenshots are saved
     to ~/workspace/ganitra-wave67-shots/.
  E. stored-history coherence — a LEGACY long-guide payload
     (kind "guide", no plain flag, as old chats stored it)
     does NOT trip the minimal gate, so old chats keep
     rendering exactly as saved.

Run: python3 verify_wave67.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("GANITRA_DB_PATH",
                      os.path.join(tempfile.mkdtemp(), "v67.db"))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

passed = 0
failed = 0


def check(name, cond, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  ok  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}  {detail}")


from fallback import fallback_answer, with_fallback  # noqa: E402
from i18n import advice_for, explanation_for, teach_for  # noqa: E402
from solver.router import solve_question  # noqa: E402

print("== A. not-solved inputs -> exactly one line ==")
CASES = [
    ("If tu gfuf", "Answer not found."),
    ("asdf qwer", "Answer not found."),
    ("कुछ भी लिख दिया बकवास", "उत्तर नहीं मिला।"),
    ("ek ladke ke paas 50 rupaye hai usne 3 chocolate 10 "
     "rupaye ki kharidi kitne bache", "Answer nahi mila."),
    ("Ten years ago, a father was twelve times as old as his "
     "son and ten years hence, he will be twice as old as his "
     "son. Find their present ages.", "Answer not found."),
]
for q, line in CASES:
    res = fallback_answer(q)
    check(f"one line: {q[:32]!r}",
          res.get("fallback_kind") == "not_found"
          and res.get("answer") == line
          and res.get("steps") == [],
          f"kind={res.get('fallback_kind')} ans={res.get('answer')!r}")

print("== A2. Merge-5 rule 1: greetings / vague -> friendly line ==")
FRIENDLY_CASES = [
    ("hello bro", "greeting",
     "Hello! 😊 I'm doing great. Send me a maths question "
     "and I'll solve it step by step."),
    ("thank you", "greeting",
     "You're welcome! 😊 Send me another maths question "
     "any time."),
    ("नमस्ते", "greeting",
     "नमस्ते! 😊 मैं बिल्कुल ठीक हूँ। अपना गणित का सवाल "
     "भेजिए — मैं चरण-दर-चरण हल दूँगा।"),
    ("samjhao", "vague",
     "Bilkul! 😊 Apna maths ka sawal poora likh kar bhejo "
     "— jaise 'solve 2x + 3 = 7' — main step-by-step hal "
     "dunga."),
]
for q, kind, line in FRIENDLY_CASES:
    res = fallback_answer(q)
    check(f"friendly line: {q[:32]!r}",
          res.get("fallback_kind") == kind
          and res.get("answer") == line
          and res.get("steps") == []
          and res.get("plain_reply") is True
          and res.get("plain") is True,
          f"kind={res.get('fallback_kind')} ans={res.get('answer')!r}")

for lang, line in (("bn", "উত্তর পাওয়া যায়নি।"),
                   ("ta", "பதில் கிடைக்கவில்லை."),
                   ("te", "సమాధానం దొరకలేదు.")):
    res = fallback_answer("asdf qwer", lang=lang)
    check(f"UI language {lang}", res.get("answer") == line,
          repr(res.get("answer")))

print("== B. guards: one line, own wording, intact ==")
SCI_Q = ("A ray of light travels from medium A to medium B. "
         "The refractive index of medium B relative to medium A "
         "is 1.5, and the speed of light in medium A is "
         "2 x 10^8 m/s. What is the speed of light in medium B?")
res = with_fallback(SCI_Q, solve_question(SCI_Q))
check("science kind + plain",
      res.get("fallback_kind") == "science"
      and res.get("plain") is True)
check("science line keeps guard wording",
      "Ganitra only solves Maths" in str(res.get("answer", "")))
check("science guidance steps still in payload",
      "refractive index" in " ".join(res.get("steps") or []))
res = fallback_answer("capital of India kya hai")
check("nonmaths one line (Hindi)",
      res.get("fallback_kind") == "nonmaths"
      and res.get("plain") is True
      and res.get("answer") == ("Ye sawal maths ka nahi hai — "
                                "Ganitra sirf Maths ke sawal "
                                "hal karta hai।"),
      repr(res.get("answer")))

print("== C. API + pages ==")
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True
client = app.test_client()

body = client.post("/api/solve",
                   json={"question": "If tu gfuf"}).get_json()
check("api gibberish minimal",
      body["ok"] is True
      and body["result"].get("fallback_kind") == "not_found"
      and body["result"].get("answer") == "Answer not found."
      and body["explanation"] == "" and body["advice"] == ""
      and body["methods"] == [] and body["teach"] == [],
      json.dumps(body)[:200])

body = client.post(
    "/api/solve", json={"question": "x^2 - 5x + 6 = 0"}).get_json()
check("api solved payload unchanged",
      body["ok"] is True
      and body["result"].get("answer") == "x = 2, x = 3"
      and bool(body["result"].get("steps"))
      and bool(body["explanation"]) and bool(body["advice"])
      and bool(body["methods"]) and bool(body["teach"]))

# The chat page itself is served to signed-in students; sign
# up a throwaway account on the throwaway DB to fetch it.
client.post("/signup", data={
    "name": "V67 Tester", "class": "8", "board": "CBSE",
    "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
    "password": "v67-pass"})
home = client.get("/").get_data(as_text=True)
check("chat page ships the Wave-67 gate",
      'fallback_kind === "not_found"' in home
      and "plain === true" in home)

page = client.post("/solve", data={"question": "If tu gfuf"})
html = page.get_data(as_text=True)
check("classic /solve: line only, no advice card",
      "Answer not found." in html
      and "advice-card" not in html
      and "Questions I solve for sure" not in html)

res = fallback_answer("x² - 5x + 6 = 0")
check("solved extras still exist",
      bool(explanation_for(res, "en"))
      and bool(advice_for(res, "en"))
      and bool(teach_for(res, "en")))

print("== E. legacy stored payloads do not trip the gate ==")
legacy = {"type": "Ganitra", "op": "guide",
          "answer": "I couldn't solve this exact question yet…",
          "steps": ["Questions I solve for sure: …"],
          "fallback": True, "fallback_kind": "guide"}
check("legacy guide payload is not plain/not_found",
      legacy.get("fallback_kind") != "not_found"
      and legacy.get("plain") is not True)

print("== D. browser DOM (optional) ==")
VENV_PY = os.path.expanduser("~/workspace/tools/venv/bin/python")
EXE = ("/home/hatch/.cache/ms-playwright/"
       "chromium_headless_shell-1255/chrome-headless-shell-linux64/"
       "chrome-headless-shell")
SHOTS = os.path.expanduser("~/workspace/ganitra-wave67-shots")
if os.path.exists(VENV_PY) and os.path.exists(EXE):
    os.makedirs(SHOTS, exist_ok=True)
    helper = os.path.join(tempfile.mkdtemp(), "shot67.py")
    with open(helper, "w") as f:
        f.write('''\
import asyncio, json, sys
from playwright.async_api import async_playwright

EXE = ("/home/hatch/.cache/ms-playwright/"
       "chromium_headless_shell-1255/chrome-headless-shell-linux64/"
       "chrome-headless-shell")
BASE, SHOTS = sys.argv[1], sys.argv[2]

async def ask(page, q):
    await page.fill("#q", q)
    await page.click(".send-btn")
    await page.wait_for_timeout(400)

async def main():
    out = {}
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path=EXE,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = await browser.new_page(
            viewport={"width": 430, "height": 860})
        # The chat needs an account: sign up a throwaway one
        # on the verify server's throwaway DB first.
        await page.goto(BASE + "/?mode=signup",
                        wait_until="networkidle")
        card = page.locator("#signup-card")
        await card.locator('input[name="name"]').fill(
            "V67 Browser")
        await card.locator('input[name="class"]').fill("8")
        await card.locator('input[name="board"]').fill("CBSE")
        await card.locator('input[name="goal"]').fill("Doctor")
        await card.locator('input[name="hobby"]').fill("Cricket")
        await card.locator('input[name="favourite"]').fill(
            "Pizza")
        await card.locator('input[name="password"]').fill(
            "v67-pass")
        await card.locator('button[type="submit"]').click()
        await page.wait_for_selector("#q", timeout=30000)
        await ask(page, "If tu gfuf")
        await page.wait_for_function(
            "document.querySelectorAll('#chat-log .bubble.bot')"
            ".length >= 1", timeout=30000)
        await page.wait_for_timeout(600)
        out["gibberish"] = await page.evaluate("""() => {
          const bots = document.querySelectorAll(
            '#chat-log .bubble.bot');
          const b = bots[bots.length - 1];
          return {
            text: b ? b.textContent.trim() : null,
            actions: document.querySelectorAll(
              '#chat-log .answer-actions').length,
            advice: document.querySelectorAll(
              '#chat-log .advice-card').length,
            steps: document.querySelectorAll(
              '#chat-log .steps-section').length,
            wraps: document.querySelectorAll(
              '#chat-log .answer-wrap').length,
          }; }""")
        await page.screenshot(
            path=SHOTS + "/wave67-gibberish.png")
        await ask(page, "x^2 - 5x + 6 = 0")
        await page.wait_for_function(
            "document.querySelectorAll("
            "'#chat-log .steps-section').length >= 1",
            timeout=30000)
        await page.wait_for_timeout(600)
        out["solved"] = await page.evaluate("""() => {
          const acts = document.querySelectorAll(
            '#chat-log .answer-actions');
          return {
            actions: acts.length,
            steps: document.querySelectorAll(
              '#chat-log .steps-section').length,
            hasAnswer: document.body.textContent.includes(
              'x = 2, x = 3'),
          }; }""")
        await page.screenshot(
            path=SHOTS + "/wave67-solved.png", full_page=True)
        await browser.close()
    print(json.dumps(out))

asyncio.run(main())
''')
    env = dict(os.environ, PORT="5177",
               GANITRA_SECRET_KEY="verify-wave67")
    server = subprocess.Popen(
        [sys.executable, "app.py"], env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        up = False
        for _ in range(60):
            try:
                urllib.request.urlopen("http://127.0.0.1:5177/",
                                       timeout=2)
                up = True
                break
            except Exception:
                time.sleep(1)
        if not up:
            check("browser server up", False)
        else:
            proc = subprocess.run(
                [VENV_PY, helper, "http://127.0.0.1:5177/", SHOTS],
                capture_output=True, text=True, timeout=300)
            lines = proc.stdout.strip().splitlines()
            if not lines:
                check("browser DOM ran", False,
                      proc.stderr.strip()[-400:])
                dom = None
            else:
                dom = json.loads(lines[-1])
            if dom is not None:
                g = dom["gibberish"]
                check("DOM gibberish = single line, no extras",
                      g["text"] == "Answer not found."
                      and g["actions"] == 0 and g["advice"] == 0
                      and g["steps"] == 0 and g["wraps"] == 0,
                      json.dumps(g))
                s = dom["solved"]
                check("DOM solved = full card as before",
                      s["actions"] >= 1 and s["steps"] >= 1
                      and s["hasAnswer"], json.dumps(s))
                check("screenshots saved",
                      os.path.exists(
                          SHOTS + "/wave67-gibberish.png")
                      and os.path.exists(
                          SHOTS + "/wave67-solved.png"))
    finally:
        server.terminate()
else:
    print("  skip  browser DOM (playwright venv not available)")

print(f"\nWave 67 verify: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
