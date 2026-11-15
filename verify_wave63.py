"""Wave 63 verification (15 Nov 2026).

WHAT THIS WAVE CHANGED (Suraj's instruction: "practice paper
kaa link nhi chahiye, paper ko download karake photo lagana
hai but real paper ki tarah khud type karo"):

Previous Papers no longer link out anywhere. Every stored
paper opens inside the app as the COMPLETE paper, typed out
like the real exam paper:

1. NO LINKS: the source anchors on /papers and /papers/<id>,
   the generated paper's marking-scheme anchor and the printed
   source URL in /papers/print are gone. source_url stays in
   papers_data (provenance metadata) but is never rendered;
   the source is still NAMED as plain text.
2. THE SHEET (templates/_paper_sheet.html, shared by the
   paper page and /papers/print?paper=<id>): exam header
   (stored code/set line, subject from the stored label,
   class/board/year, Maximum Marks derived from the stored
   sections plus the omissions the data records — 80 for every
   full paper, 40 for the 2022 Term-2 papers; time allowed is
   not in the data and is not printed), General Instructions
   derived from the paper's own section counts/marks, sections
   in order, every stored question typed in full with its
   number and right-margin marks. Display line-breaks only —
   no word of any question is added, dropped or changed.
3. [Figure] markers where a question leans on a figure
   printed in the real paper that the data does not hold:
   33 across the library (census in ganitra-wave63-notes.md).
4. Delivery pins ?v=35 / cache ganitra-static-v15.

Run:  python3 verify_wave63.py
"""

import html as _html

import markupsafe
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
RUN_ID = uuid.uuid4().hex[:8]
os.environ["GANITRA_DB_PATH"] = f"/tmp/ganitra-verify-wave63-{RUN_ID}.db"

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

FIGURE_COUNTS = {
    "cbse-12-2024": 1, "cbse-12-2023": 1, "cbse-10-2024": 3,
    "hbse-10-2024": 3, "cbse-10-2025": 4, "cbse-12-2025": 0,
    "cbse-10-2024-basic": 3, "cbse-10-2023": 5,
    "cbse-10-2025-basic": 7, "cbse-10-2020": 4,
    "cbse-10-2022-term2": 2, "cbse-12-2022-term2": 0,
    "hbse-12-2024": 0,
    # Wave 64: Hindi-medium papers (hand census on the Hindi
    # texts — ganitra-wave64-notes.md).
    "cbse-12-2024-hindi": 2, "cbse-12-2023-hindi": 3,
    "cbse-10-2024-hindi": 4, "cbse-10-2022-term2-hindi": 3,
}

# --- 1. Pins + sheet assets ------------------------------------
print("== 1. Pins and sheet assets ==")
base = (ROOT / "templates" / "base.html").read_text()
sw = (ROOT / "static" / "sw.js").read_text()
css = (ROOT / "static" / "style.css").read_text()
check("stylesheet pin ?v=38", "v='38'" in base)
check("service worker cache v13",
      'GANITRA_CACHE = "ganitra-static-v15"' in sw)
check("sheet partial exists",
      (ROOT / "templates" / "_paper_sheet.html").exists())
for sel in (".exam-sheet", ".sheet-section", ".q-figure", ".q-or"):
    check(f"sheet CSS {sel}", sel in css)

# --- 2. Templates carry no paper links ---------------------------
print("== 2. No external paper links in templates ==")
for tpl in ("papers.html", "paper_view.html",
            "papers_generate.html", "papers_print.html"):
    text = (ROOT / "templates" / tpl).read_text()
    check(f"{tpl}: no source_url rendered",
          "source_url" not in text)
    check(f"{tpl}: no answer-key URL rendered",
          "answer_key.url" not in text)

# --- 3. Served pages ---------------------------------------------
print("== 3. Served papers pages ==")
from app import create_app  # noqa: E402

app = create_app()
app.config["TESTING"] = True

anon = app.test_client()
r = anon.get("/papers/cbse-12-2024")
check("anonymous paper page redirects to sign-in",
      r.status_code in (301, 302), f"status={r.status_code}")

client = app.test_client()
r = client.post("/signup", data={
    "name": "W63 Papers " + RUN_ID, "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w63-test-pass"})
check("signup", r.status_code in (200, 302), f"status={r.status_code}")

body = client.get("/papers").get_data(as_text=True)
check("/papers lists all papers, sources named, none linked",
      all(str(markupsafe.escape(p["source_name"])) in body
          for p in papers_data.PAPERS)
      and all(p["source_url"] not in body
              for p in papers_data.PAPERS)
      and body.count('class="paper-entry"') == len(papers_data.PAPERS))

total_fig = 0
for p in papers_data.PAPERS:
    r = client.get("/papers/" + p["id"])
    b = r.get_data(as_text=True)
    want_marks = 40 if "term2" in p["id"] else 80
    n_fig = b.count("[Figure]")
    total_fig += n_fig
    flat = " ".join(_html.unescape(
        re.sub(r"<[^>]+>", " ", b)).split())
    texts_ok = all(" ".join(q["text"].split()) in flat
                   for q in p["questions"])
    hindi = p.get("medium") == "hindi"
    marks_line = (f"अधिकतम अंक : {want_marks}" if hindi
                  else f"Maximum Marks : {want_marks}")
    instr_title = "सामान्य निर्देश :" if hindi \
        else "General Instructions:"
    check(f"{p['id']}: complete typed sheet, marks {want_marks}, "
          f"figures {FIGURE_COUNTS[p['id']]}, no links",
          r.status_code == 200
          and b.count('class="paper-q"') == len(p["questions"])
          and marks_line in b
          and instr_title in b
          and p["set_label"] in b
          and n_fig == FIGURE_COUNTS[p["id"]]
          and texts_ok
          and all(o["source_url"] not in b
                  for o in papers_data.PAPERS),
          f"status={r.status_code} fig={n_fig} texts_ok={texts_ok}")
check("figure markers total 45", total_fig == 45,
      f"total={total_fig}")

body = client.get("/papers/cbse-12-2024").get_data(as_text=True)
check("internal choices get OR dividers",
      'class="q-or"' in body and "√tan x" in body)
check("instructions use the paper's own sections (2024: E = 3 x 4)",
      "Section E contains 3 questions of 4 marks each." in body
      and "This question paper contains 38 questions." in body)
body = client.get("/papers/cbse-10-2020").get_data(as_text=True)
check("2020 paper keeps its own structure (no Section E)",
      "SECTION E" not in body
      and "Section D contains 6 questions of 4 marks each." in body)

# --- 4. Print views ----------------------------------------------
print("== 4. Print views ==")
r = client.get("/papers/print?paper=cbse-12-2024")
b = r.get_data(as_text=True)
check("stored print: full sheet, no links",
      r.status_code == 200
      and b.count('class="paper-q"') == 38
      and "Maximum Marks : 80" in b
      and all(o["source_url"] not in b
              for o in papers_data.PAPERS))
r = client.post("/papers/generate", data={"class_num": "10"})
b = r.get_data(as_text=True)
check("generated paper page: no source links",
      r.status_code == 200
      and all(o["source_url"] not in b
              for o in papers_data.PAPERS))
r = client.get("/papers/print")
b = r.get_data(as_text=True)
check("generated print: still works, no source URLs",
      r.status_code == 200
      and all(o["source_url"] not in b
              for o in papers_data.PAPERS))

print(f"\nWave 63: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
