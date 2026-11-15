"""Wave 65 verification: DEEP TRILINGUAL TRAINING.

Solver-side only. Three fresh batteries (Hindi 197, Hinglish
206, English 202) plus sealed held-out sets (45 each) were
built for this wave; every fix is a general schema or
normalisation rule, proven again on 32 fresh rewordings per
language written after the fixes.

This script checks one representative per new family, the
regression guards for the families the wave touched
(probability unions/complements/specific cards, cone
surface areas), and — deliberately — that the two sealed
held-out English spellings ("mesn", "circumferance") still
miss: their spellings were never added to any map, so a
pass here would mean the held-out seal was broken.

Run:  python verify_wave65.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from api import _solve_friendly  # noqa: E402

FAILS = []


def _nums(q):
    text = str(_solve_friendly(q).get("answer"))
    out = [int(a) / int(b) for a, b in
           re.findall(r"(\d+)/(\d+)", text)]
    text = re.sub(r"\d+/\d+", " ", text)
    out += [float(x) for x in re.findall(r"-?\d+\.?\d*", text)]
    return out


def check(label, q, want, tol=0.02):
    ok = any(abs(n - want) < tol for n in _nums(q))
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        FAILS.append(label)


def check_concept(label, q):
    r = _solve_friendly(q)
    ok = r.get("fallback_kind") == "concept"
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        FAILS.append(label)


def check_miss(label, q, wrong_want):
    """Held-out honesty: the reserved spelling must NOT be
    rescued by a memorised map entry."""
    ok = not any(abs(n - wrong_want) < 0.02 for n in _nums(q))
    print(("PASS " if ok else "FAIL ") + label +
          " (sealed held-out spelling still an honest miss)")
    if not ok:
        FAILS.append(label)


# Hindi
check("hindi speed", "ट्रेन 450 किलोमीटर की दूरी 5 घंटे में "
      "तय करती है। उसकी चाल कितनी है?", 90)
check("hindi distance (speed-first)",
      "एक बस 40 किलोमीटर प्रति घंटे की चाल से 6 घंटे चलती "
      "है। वह कितनी दूरी तय करेगी?", 240)
check("hindi CI", "6000 रुपये का 9% वार्षिक दर से 2 वर्ष का "
      "चक्रवृद्धि ब्याज ज्ञात करो।", 1128.6)
check("hindi trig value", "sin 30° का मान बताइए।", 0.5)
check_concept("hindi concept (rational)",
              "परिमेय संख्या क्या होती है?")
check_concept("hindi concept (AP)", "समान्तर श्रेणी किसे कहते हैं?")

# Hinglish
check("hinglish feesadi", "640 ka 40 feesadi kitna hoga?", 256)
check("hinglish remainder", "347 ko 8 se bhaag dene par "
      "shesh kitna bachega?", 3)
check("hinglish cuboid", "cuboid ka aayatan btao, lambai "
      "11 cm chaudai 7 cm unchai 3 cm", 231)
check("hinglish clock speed", "train raat 10 bje chali aur "
      "subah 6 bje pahunchi, usne 560 km ki doori tay ki, "
      "uski speed kitni thi?", 70)

# English
check("english typos", "wat is 25 percant of 640?", 160)
check("english terse train", "train 756 km 9 hours speed?", 84)
check("english zeroes statement",
      "the zeroes of x^2 - 2x - 35 are?", 7)
check("english repeated root",
      "factorise x^2 - 12x + 36 and give the repeated root", 6)

# Regression guards
check("guard: probability union",
      "52 patto me se ek patta nikala to raja ya rani "
      "(king or queen) hone ki probability batao?", 0.1538)
check("guard: probability complement",
      "thaili me 3 laal aur 5 kaali gende hain, ek nikali "
      "to kaali na hone ki probability kitni hogi?", 0.375)
check("guard: specific card",
      "One card is drawn from a well-shuffled deck of 52 "
      "cards. Find the probability of getting a king of "
      "hearts.", 0.0192)
check("guard: cone CSA",
      "Find the curved surface area of a cone with radius "
      "6 cm and slant height 10 cm.", 188.5)

# Sealed held-out honesty (must stay misses)
check_miss("held-out 'mesn'", "find the mesn of 5, 15, 25, "
           "35, 45", 25)
check_miss("held-out 'circumferance'",
           "the circumferance of a circle with radius "
           "17.5 cm is?", 109.96)

print()
if FAILS:
    print(f"verify_wave65: {len(FAILS)} FAILURES: {FAILS}")
    sys.exit(1)
print("verify_wave65: ALL CHECKS PASSED")
