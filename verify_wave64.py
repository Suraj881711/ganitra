"""Wave 64 verification (15 Nov 2026).

WHAT THIS WAVE CHANGED (Suraj's instruction: "hindi papers
bhi chahiye"):

Hindi-medium CBSE Mathematics previous papers join the
Wave 63 typed-paper library — the genuine Hindi halves of
four real bilingual board papers, transcribed
question-by-question from the printed papers (read from the
sources' page images; the sources' Hindi text layers are
legacy-font encoded and unusable). NOTHING is translated or
invented:

- cbse-12-2024-hindi        38 questions, 80 marks (65/1/1)
- cbse-12-2023-hindi        38 questions, 80 marks (65/1/1)
- cbse-10-2024-hindi        38 questions, 80 marks (30/1/1)
- cbse-10-2022-term2-hindi  14 questions, 40 marks (30/1/1)
  = 128 Hindi questions. The two full Class 10/12 Hindi
  papers even restore questions their English library
  entries omit (10-2024 Q.12 + Q.18; 12-2023 Q.13 + Q.15).

The /papers list labels every entry's medium (हिंदी माध्यम ·
Hindi Medium / English Medium). A Hindi paper's sheet is in
the paper's own language: subject as printed (गणित / गणित
(मानक)), सामान्य निर्देश derived from its sections, खण्ड
क…ङ headings, अधिकतम अंक, and अथवा dividers for internal
choices. [Figure] markers follow the same rule as Wave 63,
with the Hindi figure-reference phrases: 12 across the four
papers (2 + 3 + 4 + 3). Zero external links, as everywhere
in the papers flow. CSS changed (medium chip + Devanagari
sheet font fallbacks), so the delivery pins moved to
?v=36 / cache ganitra-static-v13.

Run:  python3 verify_wave64.py
"""

import html as _html
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave64-{RUN_ID}.db"

ROOT = Path(__file__).parent

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


import papers_data  # noqa: E402

HINDI_IDS = ["cbse-12-2024-hindi", "cbse-12-2023-hindi",
             "cbse-10-2024-hindi", "cbse-10-2022-term2-hindi"]
HINDI_FIGURES = {"cbse-12-2024-hindi": 2, "cbse-12-2023-hindi": 3,
                 "cbse-10-2024-hindi": 4,
                 "cbse-10-2022-term2-hindi": 3}
DEV = re.compile(r"[\u0900-\u097F]")

# --- 1. Data -------------------------------------------------
print("== 1. Hindi paper data ==")
total_hi = 0
for pid in HINDI_IDS:
    p = papers_data.get_paper(pid)
    total_hi += len(p["questions"])
    check(f"{pid}: present, medium=hindi, complete",
          p is not None and p.get("medium") == "hindi"
          and p.get("subject_label", "").startswith("गणित")
          and papers_data.paper_total_marks(p)
          == (40 if "term2" in pid else 80)
          and [q["number"] for q in p["questions"]]
          == list(range(1, len(p["questions"]) + 1)))
    check(f"{pid}: every question is real Hindi text",
          all(len(DEV.findall(q["text"])) >= 5
              and " OR " not in q["text"]
              for q in p["questions"]))
check("128 Hindi questions in total", total_hi == 128,
      f"total={total_hi}")
check("library now holds 17 papers", len(papers_data.PAPERS) == 17)

# --- 2. Pins ---------------------------------------------------
print("== 2. Delivery pins ==")
base = (ROOT / "templates" / "base.html").read_text()
sw = (ROOT / "static" / "sw.js").read_text()
css = (ROOT / "static" / "style.css").read_text()
check("stylesheet pin ?v=36", "v='36'" in base)
check("service worker cache v13",
      'GANITRA_CACHE = "ganitra-static-v13"' in sw)
check("medium chip CSS", ".paper-medium" in css)
check("Devanagari sheet font fallback",
      "Noto Serif Devanagari" in css)

# --- 3. Served pages -------------------------------------------
print("== 3. Served pages ==")
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True
client = app.test_client()
r = client.post("/signup", data={
    "name": "W64 Papers " + RUN_ID, "class": "12", "board": "CBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w64-test-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")

body = client.get("/papers").get_data(as_text=True)
check("/papers labels every medium",
      body.count("हिंदी माध्यम · Hindi Medium") == 4
      and body.count("English Medium") == 13
      and all(p["source_url"] not in body
              for p in papers_data.PAPERS))

for pid in HINDI_IDS:
    p = papers_data.get_paper(pid)
    b = client.get("/papers/" + pid).get_data(as_text=True)
    flat = " ".join(_html.unescape(
        re.sub(r"<[^>]+>", " ", b)).split())
    want_marks = 40 if "term2" in pid else 80
    check(f"{pid}: Hindi sheet complete, no links",
          b.count('class="paper-q"') == len(p["questions"])
          and p["subject_label"] in b
          and "सामान्य निर्देश :" in b
          and "सभी प्रश्न अनिवार्य हैं।" in b
          and f"अधिकतम अंक : {want_marks}" in b
          and "खण्ड क" in b
          and b.count("[Figure]") == HINDI_FIGURES[pid]
          and all(" ".join(q["text"].split()) in flat
                  for q in p["questions"])
          and all(o["source_url"] not in b
                  for o in papers_data.PAPERS))

b = client.get("/papers/cbse-12-2024-hindi").get_data(as_text=True)
check("Hindi internal choices get अथवा dividers",
      '<p class="q-or">अथवा</p>' in b)
heads = [b.index(f"खण्ड {s}") for s in "कखगघङ"]
check("Hindi section headings in order", heads == sorted(heads))
b = client.get("/papers/cbse-10-2024-hindi").get_data(as_text=True)
check("lowercase MCQ options split onto their own lines",
      '<p class="q-line">(a) √2</p>' in b
      and '<p class="q-line">(d) 1/2</p>' in b)
b = client.get("/papers/cbse-12-2023-hindi").get_data(as_text=True)
check("अथवा inside an option is not split as a divider",
      '<p class="q-line">(d) 8 अथवा −8</p>' in b)

# English regression spot-check
b = client.get("/papers/cbse-12-2024").get_data(as_text=True)
check("English sheet unchanged",
      "General Instructions:" in b and "Maximum Marks : 80" in b
      and '<p class="q-or">OR</p>' in b and "SECTION A" in b)

# --- 4. Print view ---------------------------------------------
print("== 4. Print view ==")
r = client.get("/papers/print?paper=cbse-12-2023-hindi")
b = r.get_data(as_text=True)
check("Hindi stored print: full sheet, Hindi chrome, no links",
      r.status_code == 200
      and b.count('class="paper-q"') == 38
      and "गणित" in b and "सामान्य निर्देश :" in b
      and "अधिकतम अंक : 80" in b
      and all(o["source_url"] not in b
              for o in papers_data.PAPERS))

print(f"\nWave 64: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
