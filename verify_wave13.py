"""Wave-13 verification: Classes 0-12 solver coverage expansion
+ more methods per question.

Contract (Suraj's directive, 10 Nov 2026):
- "0-12th tak sabhi question solve hone chahiye. Chaye koi
  nhi method ho" — every class band's standard question
  families must solve, whatever method it takes.
- "Question ke method badane hai" — more alternate methods
  per question where genuine methods exist (Wave-12 honesty
  rule unchanged: no fabricated methods, every alternate's
  answer must equal the primary answer).

Sections:
1. i18n completeness for the Wave-13 keys (method labels in
   all 6 languages; full STRINGS completeness; EXPLANATIONS
   and ADVICE key sets identical across languages).
2. COVERAGE BATTERY: sample questions per class band
   (0-2, 3-5, 6-8, 9-10, 11-12), each asserted to solve with
   the expected answer.
3. METHODS BATTERY: the new Wave-13 alternates exist and
   agree with the primary answer.
4. No-crash fuzz: gibberish must not produce a fabricated
   answer from the new Wave-13 types.
5. API integration: a junior and an applied question ride
   the normal /api/solve contract (ok + explanation +
   teach lines).

Run:  python verify_wave13.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave13.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from i18n import (ADVICE, EXPLANATIONS, STRINGS,  # noqa: E402
                  SUPPORTED_LANGS)
from solver.methods import alternate_methods  # noqa: E402
from solver.router import solve_question  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


# --- 1. i18n completeness -------------------------------------------------
EN = STRINGS["en"]
W13_KEYS = {k for k in EN if k.startswith("mm_label_")}
check("wave13 label keys exist", len(W13_KEYS) >= 14,
      f"keys={len(W13_KEYS)}")
for code in SUPPORTED_LANGS:
    missing = W13_KEYS - set(STRINGS[code])
    check(f"wave13 keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
    empty = [k for k in W13_KEYS if not STRINGS[code].get(k)]
    check(f"wave13 keys non-empty ({code})", not empty,
          f"empty={empty}")
    check(f"i18n fully complete ({code})",
          set(EN) <= set(STRINGS[code]))
    check(f"explanations key parity ({code})",
          set(EXPLANATIONS[code]) == set(EXPLANATIONS["en"]))
    check(f"advice key parity ({code})",
          set(ADVICE[code]) == set(ADVICE["en"]))
for key in ("junior", "applied"):
    check(f"explanation for new type '{key}'",
          key in EXPLANATIONS["en"] and key in EXPLANATIONS["hi"])
    check(f"advice for new type '{key}'",
          key in ADVICE["en"] and key in ADVICE["hi"])

# --- 2. Coverage battery ----------------------------------------------------
# (question, expected substring of the answer, band)
COVERAGE = [
    # Band 0-2: counting, names, tables, tiny stories
    ("write 45 in words", "forty-five", "0-2"),
    ("write 457 in words", "four hundred fifty-seven", "0-2"),
    ("number name of 230", "two hundred thirty", "0-2"),
    ("table of 7", "56", "0-2"),
    ("7 ka table", "42", "0-2"),
    ("7 x 8", "56", "0-2"),
    ("add 245 and 178", "423", "0-2"),
    ("Ram has 15 mangoes. He gives 6 to Sita. How many are "
     "left?", "9", "0-2"),
    ("Rita has 20 stickers. She buys 8 more. How many does "
     "she have now?", "28", "0-2"),
    ("is 47 odd or even", "47 is odd", "0-2"),
    # Band 3-5: place value, fractions, money, clock, shapes
    ("place value of 7 in 457", "7", "3-5"),
    ("expanded form of 457", "400 + 50 + 7", "3-5"),
    ("subtract 96 from 250", "154", "3-5"),
    ("difference between 90 and 34", "56", "3-5"),
    ("product of 12 and 5", "60", "3-5"),
    ("divide 24 by 6", "4", "3-5"),
    ("5 boxes have 6 pencils each. How many pencils in all?",
     "30", "3-5"),
    ("24 sweets shared equally among 6 children. How many "
     "each?", "4", "3-5"),
    ("what is 1/2 of 18", "9", "3-5"),
    ("half of 24", "12", "3-5"),
    ("quarter of 100", "25", "3-5"),
    ("write 3/5 as decimal", "0.6", "3-5"),
    ("0.75 as fraction", "3/4", "3-5"),
    ("which is bigger 2/3 or 3/4", "3/4 is bigger", "3-5"),
    ("cost of 5 pens at Rs 12 each", "60", "3-5"),
    ("Ravi has Rs 100. He buys a book for Rs 65. How much "
     "money is left?", "35", "3-5"),
    ("how many minutes in 3 hours", "180", "3-5"),
    ("how many days in 4 weeks", "28", "3-5"),
    ("how many months in 3 years", "36", "3-5"),
    ("convert 3 km into metres", "3000", "3-5"),
    ("5 kg = how many grams", "5000", "3-5"),
    ("what is 45 minutes after 3:30", "4:15", "3-5"),
    ("from 2 pm to 5 pm how many hours", "3 hours", "3-5"),
    ("how many sides does a hexagon have", "6", "3-5"),
    ("name the shape with 3 sides", "Triangle", "3-5"),
    ("perimeter of rectangle 8 cm by 5 cm", "26", "3-5"),
    ("area of rectangle 8 by 5", "40", "3-5"),
    ("next number: 2, 4, 6, 8, ?", "10", "3-5"),
    ("what comes next 5, 10, 15, ?", "20", "3-5"),
    ("missing number: 3, 6, ?, 12, 15", "9", "3-5"),
    ("odd numbers between 10 and 20", "11", "3-5"),
    ("factors of 12", "2^2", "3-5"),
    ("multiples of 6 up to 30", "30", "3-5"),
    ("first 5 multiples of 6", "18", "3-5"),
    ("prime numbers between 1 and 20", "19", "3-5"),
    ("is 29 prime", "prime", "3-5"),
    ("HCF of 12 and 18", "6", "3-5"),
    ("LCM of 4 and 6", "12", "3-5"),
    # Band 6-8: ratio, SI, profit-loss, speed, word equations
    ("ratio of 20 to 45", "4 : 9", "6-8"),
    ("simplify ratio 12:18", "2 : 3", "6-8"),
    ("divide Rs 600 in the ratio 2:3", "240", "6-8"),
    ("two numbers are in ratio 3:5 and sum is 40, find them",
     "15 and 25", "6-8"),
    ("if 5 pens cost Rs 60, cost of 8 pens", "96", "6-8"),
    ("(-5) + 8", "3", "6-8"),
    ("simple interest on Rs 5000 at 6% per annum for 3 years",
     "900", "6-8"),
    ("simple interest on 1000 at 5% for 2 years", "100", "6-8"),
    ("simple interest on Rs 12000 at 5% per annum for 6 "
     "months", "300", "6-8"),
    ("bought for Rs 800, sold for Rs 920. Profit or loss?",
     "Profit of Rs 120", "6-8"),
    ("bought for Rs 800, sold for Rs 920. Find profit percent",
     "15%", "6-8"),
    ("bought for Rs 500, sold for Rs 400. Loss percent?",
     "20%", "6-8"),
    ("a car travels 180 km in 3 hours. speed?", "60 km/h",
     "6-8"),
    ("speed 60 km/h for 2.5 hours, distance?", "150", "6-8"),
    ("convert 36 km/h to m/s", "10 m/s", "6-8"),
    ("convert 10 m/s to km/h", "36 km/h", "6-8"),
    ("a number increased by 7 is 15. find the number", "8",
     "6-8"),
    ("a number decreased by 5 is 11", "16", "6-8"),
    ("twice a number is 26", "13", "6-8"),
    ("sum of a number and 9 is 20", "11", "6-8"),
    ("when 6 is added to a number, the result is 19", "13",
     "6-8"),
    # Band 9-10: AP/GP, discriminant, mensuration, coordinate
    ("10th term of AP 3, 7, 11", "39", "9-10"),
    ("sum of first 20 terms of AP 2, 5, 8", "610", "9-10"),
    ("5th term of GP 3, 6, 12", "48", "9-10"),
    ("discriminant of x^2 - 5x + 6", "1", "9-10"),
    ("nature of roots of x^2 - 5x + 6 = 0", "distinct real",
     "9-10"),
    ("nature of roots of x^2 + 2x + 5", "No real roots", "9-10"),
    ("distance between (2,3) and (5,7)", "5", "9-10"),
    ("midpoint of (2,3) and (6,9)", "(4, 6)", "9-10"),
    ("slope of line joining (1,2) and (4,8)", "2", "9-10"),
    ("volume of a cylinder radius 7 height 10", "1539", "9-10"),
    ("surface area of sphere radius 5", "314", "9-10"),
    ("area of a circle radius 7", "153.9", "9-10"),
    ("circumference of circle radius 7", "43.98", "9-10"),
    ("volume of cube side 4", "64", "9-10"),
    ("area of triangle base 6 height 4", "12", "9-10"),
    ("mean of 4, 8, 15, 16, 23", "13.2", "9-10"),
    ("median of 3, 7, 9, 12", "8", "9-10"),
    ("mode of 2, 3, 3, 5, 7", "3", "9-10"),
    # Band 11-12: established senior coverage still intact
    ("integrate x^2", "x^3/3", "11-12"),
    ("derivative of x^3", "3", "11-12"),
    ("determinant of [[1,2],[3,4]]", "-2", "11-12"),
    ("sin 30", "1/2", "11-12"),
    ("probability of getting a head in a coin toss", "1/2",
     "11-12"),
]

band_counts = {}
for question, expected, band in COVERAGE:
    band_counts[band] = band_counts.get(band, 0) + 1
    try:
        r = solve_question(question)
        ans = str(r.get("answer") or "")
        ok = (r.get("op") != "error" and bool(ans)
              and expected.lower() in ans.lower())
        check(f"coverage[{band}] {question[:44]}", ok,
              f"-> {r.get('type')}/{r.get('op')} {ans[:40]!r}")
    except Exception as e:  # a crash is a failure, not a skip
        check(f"coverage[{band}] {question[:44]}", False,
              f"raised {e!r}")
for band in ("0-2", "3-5", "6-8", "9-10", "11-12"):
    check(f"band {band} has >= 3 samples",
          band_counts.get(band, 0) >= 3,
          f"count={band_counts.get(band, 0)}")
check("coverage battery size >= 45", len(COVERAGE) >= 45,
      f"total={len(COVERAGE)}")

# --- 3. Methods battery -----------------------------------------------------
def _method_ids(q):
    r = solve_question(q)
    return r, [m["id"] for m in alternate_methods(q, r)]


r, ids = _method_ids("2*x + 3 = 7")
check("methods: linear has transposition + graph",
      "transposition" in ids and "graph" in ids, f"ids={ids}")
check("methods: linear alternates agree",
      all(m["answer"] == r["answer"] and m["steps"]
          for m in alternate_methods("2*x + 3 = 7", r)))
r, ids = _method_ids("15% of 240")
check("methods: percentage has proportion",
      "proportion" in ids and "fraction" in ids
      and "unitary" in ids, f"ids={ids}")
r, ids = _method_ids(
    "simple interest on Rs 5000 at 6% per annum for 3 years")
check("methods: SI has yearly breakup",
      ids == ["yearly_breakup"], f"ids={ids}")
r, ids = _method_ids("HCF of 12 and 18")
check("methods: HCF has Euclid alternate",
      ids == ["euclid"], f"ids={ids}")
r, ids = _method_ids("LCM of 4 and 6")
check("methods: LCM has HCF-relation alternate",
      ids == ["hcf_relation"], f"ids={ids}")
r, ids = _method_ids("distance between (2,3) and (5,7)")
check("methods: distance has graph alternate",
      ids == ["graph"], f"ids={ids}")
r, ids = _method_ids("area of triangle base 6 height 4")
check("methods: triangle area has half-rectangle alternate",
      ids == ["half_rectangle"], f"ids={ids}")
r, ids = _method_ids("10th term of AP 3, 7, 11")
check("methods: AP nth term has listing alternate",
      ids == ["listing"], f"ids={ids}")
r, ids = _method_ids("5th term of GP 3, 6, 12")
check("methods: GP nth term has listing alternate",
      ids == ["listing"], f"ids={ids}")
r, ids = _method_ids("mean of 4, 8, 15, 16, 23")
check("methods: mean has assumed-mean alternate",
      ids == ["assumed_mean"], f"ids={ids}")
for q in ("simple interest on Rs 5000 at 6% per annum for "
          "3 years", "HCF of 12 and 18",
          "distance between (2,3) and (5,7)",
          "mean of 4, 8, 15, 16, 23"):
    r = solve_question(q)
    check(f"methods agree: {q[:38]}",
          all(m["answer"] == r["answer"] and len(m["steps"]) >= 2
              for m in alternate_methods(q, r)))
check("methods: honest empty for 20th AP term listing",
      _method_ids("20th term of AP 3, 7, 11")[1] == [])
check("methods: honest empty for 2-value mean",
      _method_ids("mean of 5, 10")[1] == [])

# --- 4. No-crash fuzz ---------------------------------------------------------
NEW_TYPES = {"junior", "applied"}
for q in ("banana split 3 ways please", "asdf",
          "tell me a joke", "how are you doing today",
          "Ram has some mangoes and gives some away"):
    try:
        r = solve_question(q)
        fabricated = (r.get("type") in NEW_TYPES
                      and r.get("op") not in (None, "error")
                      and bool(str(r.get("answer") or "").strip()))
        check(f"fuzz: no fabrication for {q[:30]!r}",
              not fabricated,
              f"-> {r.get('type')}/{r.get('op')}")
    except Exception as e:
        check(f"fuzz: no crash for {q[:30]!r}", False,
              f"raised {e!r}")
check("fuzz: methods never crash on gibberish",
      isinstance(alternate_methods(
          "asdf qwer", solve_question("asdf qwer")), list))

# --- 5. API integration ---------------------------------------------------------
app = create_app()
c = app.test_client()
name = "W13 Tester " + RUN_ID
r = c.post("/signup", data={"name": name, "class": "8",
                            "board": "CBSE", "goal": "Doctor",
                            "hobby": "Cricket",
                            "favourite": "Pizza",
                            "password": "w13test-pass"})
check("api: signup for wave13 checks", r.status_code == 302,
      f"status={r.status_code}")
d = (c.post("/api/solve",
            json={"question": "table of 7"}).get_json() or {})
check("api: junior question solves via /api/solve",
      d.get("ok") is True
      and "56" in str((d.get("result") or {}).get("answer", ""))
      and len(d.get("teach") or []) >= 3)
d = (c.post("/api/solve",
            json={"question": "ratio of 20 to 45"}).get_json()
     or {})
check("api: applied question solves via /api/solve",
      d.get("ok") is True
      and "4 : 9" in str((d.get("result") or {}).get("answer", ""))
      and bool(d.get("explanation")))
d = (c.post("/api/solve",
            json={"question": "2*x + 3 = 7"}).get_json() or {})
check("api: linear now serves 2 methods",
      d.get("ok") is True and len(d.get("methods") or []) == 2
      and {m["id"] for m in d["methods"]}
      == {"transposition", "graph"})

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
