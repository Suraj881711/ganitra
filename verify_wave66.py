"""Wave 66 verification (15 Nov 2026).

WHAT THIS WAVE CHANGED (Suraj's instruction: "All paper
sabhi board ke chahiye, hindi or english dono ke"):

The Wave 63/64 typed-paper library grows from 17 papers
(567 questions, CBSE + HBSE) to 39 papers (1,486 questions)
across 9 boards — every paper a REAL printed board paper
transcribed question-by-question from its full text (board
booklets mirrored by AglaSem, cross-checked against a
second source or the bilingual other half), in the same
no-external-links typed style. New in this wave (21 papers):

- RBSE 10/12 2025, English + Hindi (80 marks each)
- CBSE 12 2022 Term-2 Hindi half (40 marks)
- ISC 12 2025 + ICSE 10 2025 (CISCE, English only — CISCE
  publishes Maths in English only; stored sums 95/110 with
  max_marks 80 for the alternative-section papers)
- UP Board 10 2025 (70) + 12 2025 (100), English + Hindi
- HBSE 10/12 2024 Hindi halves (80 each; the English
  hbse-12-2024 entry's Q11/Q23/Q30 were also corrected
  against the printed pages)
- MP Board 10 2025 (75) + 12 2025 Higher Maths (80),
  English + Hindi
- BSEB 10 2025 + 12 2025, English + Hindi (138 questions
  each; stored sums 200 with max_marks 100 — any-50/15/4)
- Maharashtra SSC Algebra Part I 2025, English (40 marks;
  the board publishes English + Marathi, not Hindi)

Gaps are documented in ganitra-wave66-notes.md (GSEB/UBSE
full texts located but not transcribed this wave; CGBSE /
JAC not reached; CBSE 2025 Hindi halves not genuinely
sourceable as printed booklets). No solver / chat / scene /
auth changes, and no CSS/JS changes — the delivery
pins stay whatever the tree carries.

Run:  python3 verify_wave66.py
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
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave66-{RUN_ID}.db"

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

# id -> (questions, stored marks, header marks shown)
EXPECTED = {
    "rbse-10-2025": (20, 80, 80), "rbse-10-2025-hindi": (20, 80, 80),
    "rbse-12-2025": (20, 80, 80), "rbse-12-2025-hindi": (20, 80, 80),
    "cbse-12-2022-term2-hindi": (14, 40, 40),
    "isc-12-2025": (22, 95, 80), "icse-10-2025": (10, 110, 80),
    "up-10-2025": (25, 70, 70), "up-10-2025-hindi": (25, 70, 70),
    "up-12-2025": (9, 100, 100), "up-12-2025-hindi": (9, 100, 100),
    "hbse-10-2024-hindi": (38, 80, 80),
    "hbse-12-2024-hindi": (38, 80, 80),
    "mpbse-10-2025": (23, 75, 75), "mpbse-10-2025-hindi": (23, 75, 75),
    "mpbse-12-2025": (23, 80, 80), "mpbse-12-2025-hindi": (23, 80, 80),
    "bseb-10-2025": (138, 200, 100),
    "bseb-10-2025-hindi": (138, 200, 100),
    "bseb-12-2025": (138, 200, 100),
    "bseb-12-2025-hindi": (138, 200, 100),
    "msbshse-10-2025-algebra": (5, 40, 40),
}
DEV = re.compile(r"[ऀ-ॿ]")

# --- 1. Data -------------------------------------------------
print("== 1. Library data ==")
check("library holds 39 papers", len(papers_data.PAPERS) == 39,
      f"total={len(papers_data.PAPERS)}")
check("library holds 1,486 questions",
      sum(len(p["questions"]) for p in papers_data.PAPERS) == 1486)
check("15 Hindi-medium papers",
      sum(1 for p in papers_data.PAPERS
          if p.get("medium") == "hindi") == 15)
for pid, (nq, stored, header) in EXPECTED.items():
    p = papers_data.get_paper(pid)
    ok = (p is not None and len(p["questions"]) == nq
          and papers_data.paper_total_marks(p) == stored
          and p.get("max_marks", stored) == header)
    check(f"{pid}: {nq} questions, stored {stored}, header {header}",
          ok, "" if p is None else
          f"nq={len(p['questions'])} stored="
          f"{papers_data.paper_total_marks(p)}")
    if p is not None and p.get("medium") == "hindi":
        verbal = [q for q in p["questions"] if len(q["text"]) > 40]
        hindi_qs = [q for q in verbal
                    if len(DEV.findall(q["text"])) >= 3]
        # BSEB-12 Hindi scores 74/127: its 100 objective
        # questions are largely pure expressions, printed
        # once for both mediums in the booklet itself.
        check(f"{pid}: genuine Hindi text (not translation filler)",
              len(hindi_qs) >= 0.5 * len(verbal)
              and sum(len(DEV.findall(q["text"]))
                      for q in p["questions"]) >= 150,
              f"hindi_qs={len(hindi_qs)}/{len(verbal)}")

# HBSE-12 English corrections (image-verified this wave)
hb = papers_data.get_paper("hbse-12-2024")
qmap = {q["number"]: q["text"] for q in hb["questions"]}
check("hbse-12-2024 Q11 carries the printed outer square",
      "[1 + (dy/dx)²]²" in qmap[11])
check("hbse-12-2024 Q23 carries the printed radical + bound",
      "√((1 - cos x)/(1 + cos x))" in qmap[23]
      and "π/4 < x < π/4" in qmap[23])
check("hbse-12-2024 Q30 integrand is √tan x as printed",
      "√tan x" in qmap[30])

# --- 2. Pins ---------------------------------------------------
# Wave 66 changes no CSS/JS, so it must not move the delivery
# pins: they stay whatever the tree carries (?v=36 / v13 in
# the Wave-66 working copy; the original tree has since moved
# to ?v=38 / v14 under Waves 67/68, whose bump this wave
# neither needs nor touches).
print("== 2. Delivery pins (present, not moved by Wave 66) ==")
base = (ROOT / "templates" / "base.html").read_text()
sw = (ROOT / "static" / "sw.js").read_text()
check("stylesheet pin present", re.search(r"v='\d+'", base))
check("service worker cache pin present",
      re.search(r'GANITRA_CACHE = "ganitra-static-v\d+"', sw))

# --- 3. Served pages -------------------------------------------
print("== 3. Served pages ==")
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True
client = app.test_client()
r = client.post("/signup", data={
    "name": "W66 Papers " + RUN_ID, "class": "12", "board": "RBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w66-test-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")

body = client.get("/papers").get_data(as_text=True)
check("/papers labels every medium",
      body.count("हिंदी माध्यम · Hindi Medium</span>") == 15
      and body.count("English Medium</span>") == 24)
check("/papers shows every board name",
      all(p["board"] in body for p in papers_data.PAPERS))
check("/papers has no external paper links",
      all(p["source_url"] not in body for p in papers_data.PAPERS))

def _stream(s):
    s = re.sub(r"<[^>]+>", " ", _html.unescape(s))
    return re.sub(r"[^0-9a-zA-Z\u0900-\u097F]+", "", s)


for pid in EXPECTED:
    p = papers_data.get_paper(pid)
    b = client.get("/papers/" + pid).get_data(as_text=True)
    flat = _stream(b)
    probe = _stream(p["questions"][0]["text"])[:36]
    probe_last = _stream(p["questions"][-1]["text"])[:36]
    check(f"{pid}: page renders all questions, no links",
          b.count('class="paper-q"') == len(p["questions"])
          and p["source_url"] not in b
          and probe in flat and probe_last in flat,
          f"qcount={b.count(chr(34) + 'paper-q' + chr(34))}")
    check(f"{pid}: print view renders the sheet",
          client.get("/papers/print?paper=" + pid).status_code == 200)

# BSEB header sanity: the sheet must show Maximum Marks 100,
# not the 200 the full typed texts sum to.
b = client.get("/papers/bseb-10-2025").get_data(as_text=True)
check("bseb-10-2025 sheet shows Maximum Marks : 100",
      "Maximum Marks : 100" in b
      and "Maximum Marks : 200" not in b)
b = client.get("/papers/isc-12-2025").get_data(as_text=True)
check("isc-12-2025 sheet shows Maximum Marks : 80",
      "Maximum Marks : 80" in b)

print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
