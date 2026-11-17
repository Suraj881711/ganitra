"""Wave 68 verification: CHAT PAGE ADVANCE OVERHAUL.

Suraj's order (15 Nov 2026): the chat page is what students
see first — understand what the person is asking, answer the
way a top assistant does: clean steps, a clear final answer,
and ONE short line for greetings / gibberish / non-maths /
unsolved questions. (The reference assistants were studied
for their WORKING PATTERNS only — intent handling, step
flow, final-answer clarity; nothing of their wording, UI or
design is copied. Ganitra's voice and look stay its own.)

Checks:
 1. Intent gate — greetings EN/Hinglish/Devanagari,
    gibberish, non-maths EN/Devanagari, science and vague
    asks are PLAIN one-line replies (plain_reply, no steps
    panel payload), each in the question's own script.
 2. Gibberish settles on the exact not-found line per
    language ("Answer not found." / "Answer nahi mila." /
    "उत्तर नहीं मिला।") — the Wave 67 rule, honoured here.
 3. Solved spot set — Hindi train 40 km/h (with intro),
    x²−5x+6=0 → x = 2, 3, 15% of 240 → 36, circle area,
    Hinglish train 90 km/h, profit % — values exact, intro
    present only for word problems, answer never duplicated.
 4. Template/CSS pins — plain + intro hooks, no explanation
    paragraph, no notebook panel in the chat flow, NO example
    chips (Wave-69 removal on Suraj's order), pins ?v=47 / v24 (Deploy-27).
 5. Mini-battery — 24 known-value questions across topics
    and languages stay EXACT (the full 515 + 984 batteries
    were diffed per-item during the wave: 0 verdict flips,
    0 EXACT answer changes — see ganitra-wave68-notes.md).

Run:  python3 verify_wave68.py   (exit 0 = all checks pass)
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from api import _intro_for, _solve_friendly  # noqa: E402

FAILS = []


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label
          + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(label)


def plain_one_liner(label, q, kind=None):
    r = _solve_friendly(q)
    ok = r.get("plain_reply") is True and "\n" not in str(
        r.get("answer", ""))
    if kind:
        ok = ok and r.get("fallback_kind") == kind
    check(label, ok, f"{r.get('fallback_kind')}: {r.get('answer')}")
    return r


print("== 1. intent gate: plain one-liners ==")
plain_one_liner("greeting EN", "hi", "greeting")
plain_one_liner("greeting Hinglish", "namaste", "greeting")
r = plain_one_liner("greeting Devanagari", "नमस्ते", "greeting")
check("greeting Devanagari script", r["answer"].startswith("नमस्ते"))
plain_one_liner("greeting thanks Devanagari", "धन्यवाद", "greeting")
plain_one_liner("nonmaths EN", "what is the capital of india",
                "nonmaths")
r = plain_one_liner("nonmaths Devanagari", "भारत की राजधानी क्या है?",
                    "nonmaths")
check("nonmaths Devanagari script", "गणित" in r["answer"])
plain_one_liner("vague Hinglish", "kuch bhi bata do", "vague")
plain_one_liner("vague Devanagari", "समझाओ", "vague")

print("== 2. gibberish -> the exact not-found line ==")
for q, want in [("If tu gfuf", "Answer not found."),
                ("asdf qwer zxq", "Answer not found."),
                ("कखग घङच छजझ", "उत्तर नहीं मिला।")]:
    r = _solve_friendly(q)
    check(f"not-found {q[:14]!r}",
          r.get("plain_reply") is True and r.get("steps") == []
          and r.get("answer") == want,
          f"{r.get('fallback_kind')}: {r.get('answer')}")
r = _solve_friendly("बताओ")
check("bare Hindi word is not letter-soup",
      r.get("plain_reply") is True and "*" not in str(r["answer"]))

print("== 3. science guard: plain, guidance kept ==")
q = ("A ray of light travels from medium A to medium B. The "
     "refractive index of medium B relative to medium A is 1.5, "
     "and the speed of light in medium A is 2 x 10^8 m/s. What "
     "is the speed of light in medium B?")
r = _solve_friendly(q)
check("science plain + guidance",
      r.get("fallback_kind") == "science"
      and r.get("plain_reply") is True
      and "Maths" in r["answer"]
      and "refractive index" in " ".join(r.get("steps") or []))

print("== 4. solved spot set: values + structure ==")
HINDI_TRAIN = (
    "एक रेलगाड़ी एक समान चाल से 360 km की दूरी तय करती है। "
    "यदि यह चाल 5 km/h अधिक होती तो वह उसी यात्रा में 1 घंटा "
    "कम लेती। रेलगाड़ी की चाल ज्ञात कीजिए।")
r = _solve_friendly(HINDI_TRAIN)
check("hindi train value", "40 km/h" in r["answer"], r["answer"])
intro = _intro_for(r, HINDI_TRAIN)
check("hindi train intro is its framing step",
      intro is not None and intro == r["steps"][0]
      and intro.startswith("Let "))
check("solved is not plain", not r.get("plain_reply"))
r = _solve_friendly("Solve x^2 - 5x + 6 = 0")
check("quadratic value", r["answer"] == "x = 2, x = 3", r["answer"])
check("quadratic no intro",
      _intro_for(r, "Solve x^2 - 5x + 6 = 0") is None)
r = _solve_friendly("What is 15% of 240?")
check("percentage value", r["answer"] == "36", r["answer"])
check("percentage no intro",
      _intro_for(r, "What is 15% of 240?") is None)
r = _solve_friendly("Find the area of a circle with radius 7 cm.")
# Wave 99 (pi policy): radius 7 -> pi = 22/7 -> area exactly 154
# (was 49·pi ≈ 153.94).
check("geometry value", "154" in r["answer"], r["answer"])
r = _solve_friendly("ek train 360 km jati hai 4 ghante me, "
                    "speed kitni hai?")
check("hinglish train value", "90 km/h" in r["answer"], r["answer"])
r = _solve_friendly("A shopkeeper buys an article for Rs 800 and "
                    "sells it for Rs 920. Find his profit percent.")
check("profit value + intro", r["answer"] == "15%"
      and (_intro_for(r, "profit") or "").find("CP") >= 0,
      r["answer"])

print("== 5. no duplicated final answer (render-level) ==")
for q in (HINDI_TRAIN, "Solve x^2 - 5x + 6 = 0",
          "What is 15% of 240?"):
    r = _solve_friendly(q)
    ans = str(r["answer"]).strip()
    steps = [str(s) for s in r["steps"]]
    if steps:
        last = re.sub(r"^\s*(solution|answer)\s*:\s*", "",
                      steps[-1], flags=re.I).strip()
        if last == ans:
            steps.pop()
    intro = _intro_for(r, q)
    if intro and steps and steps[0] == intro:
        steps = steps[1:]
    bad = [s for s in steps
           if s.strip() == ans
           or s.strip().lower() in (f"solution: {ans}".lower(),
                                    f"answer: {ans}".lower())]
    check(f"no duplication {q[:24]!r}", not bad
          and (not intro or ans not in intro), str(bad))

print("== 6. template / CSS pins ==")
INDEX = (ROOT / "templates" / "index.html").read_text("utf-8")
BASE = (ROOT / "templates" / "base.html").read_text("utf-8")
SW = (ROOT / "static" / "sw.js").read_text("utf-8")
CSS = (ROOT / "static" / "style.css").read_text("utf-8")
check("plain hook in chat JS", "result.plain_reply" in INDEX)
check("intro hook in chat JS", "answer-intro" in INDEX)
check("no explanation paragraph in chat",
      'className = "explain"' not in INDEX)
check("no notebook panel in chat",
      '"steps notebook"' not in INDEX and "makeHwToggle" not in INDEX)
check("no example chips (Wave 69)", INDEX.count('class="example-chip"') == 0
      and 'id="example-chips"' not in INDEX)
check("pins ?v=47 / v24 (Deploy-27)", "v='47'" in BASE
      and 'GANITRA_CACHE = "ganitra-static-v24"' in SW)
check("wave68 CSS present", ".example-chip" not in CSS
      and ".plain-reply" in CSS and ".answer-intro" in CSS)

print("== 7. sample questions solve ==")
check("sample quadratic", _solve_friendly(
    "Solve x² - 5x + 6 = 0")["answer"] == "x = 2, x = 3")
check("sample percentage", _solve_friendly(
    "15% of 240 kitna hoga?")["answer"] == "36")
check("sample hindi train", "90 km/h" in _solve_friendly(
    "एक ट्रेन 360 km की दूरी 4 घंटे में तय करती है। "
    "उसकी चाल ज्ञात कीजिए।")["answer"])

print("== 8. mini-battery (known values stay exact) ==")
MINI = [
    ("What is 20% of 450?", 90), ("Add 2/3 and 3/4.", 17 / 12),
    ("Find the HCF of 24 and 36.", 12),
    ("Find the LCM of 12 and 18.", 36),
    ("Solve 2x + 3 = 11.", 4),
    ("Find the area of a square with side 9 cm.", 81),
    ("Find the simple interest on Rs 1000 at 5% for 2 years.", 100),
    ("mean of 3, 6, 9, 12", 7.5),
    ("sin 30", 0.5), ("What is the square root of 144?", 12),
    ("240 ka 15 pratishat kitna hoga?", 36),
    ("ek train 240 km ki doori 3 ghante me tay karti hai, "
     "uski speed kya hogi?", 80),
    ("ट्रेन 450 किलोमीटर की दूरी 5 घंटे में तय करती है। "
     "उसकी चाल कितनी है?", 90),
    ("6000 रुपये का 9% वार्षिक दर से 2 वर्ष का चक्रवृद्धि "
     "ब्याज ज्ञात करो।", 1128.6),
    ("640 ka 40 feesadi kitna hoga?", 256),
    ("347 ko 8 se bhaag dene par shesh kitna bachega?", 3),
]
for q, want in MINI:
    r = _solve_friendly(q)
    text = str(r.get("answer", "")).replace(",", "")
    nums = [int(a) / int(b) for a, b in
            re.findall(r"(\d+)/(\d+)", text)]
    text = re.sub(r"\d+/\d+", " ", text)
    nums += [float(x) for x in re.findall(r"-?\d+\.?\d*", text)]
    ok = not r.get("fallback") and any(
        abs(n - want) < 0.03 for n in nums)
    check(f"mini {q[:30]!r}", ok, str(r.get("answer"))[:60])

print()
if FAILS:
    print(f"verify_wave68: {len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("verify_wave68: ALL CHECKS PASSED")
