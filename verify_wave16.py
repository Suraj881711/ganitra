"""Wave-16 verification: PREVIOUS PAPERS (Suraj's idea, 10 Nov 2026).

Contract:
1. /papers, /papers/<id>, /papers/analysis, /papers/generate and
   /papers/print are behind the login gate: anonymous visitors are
   redirected to / (the sign-in gate); a signed-in student gets 200.
2. Library integrity (papers_data.PAPERS): every paper entry has a
   source URL (http...) and a year; every question has a section
   from the CBSE A-E structure, a positive marks value, and a
   chapter slug that exists in board_data for the paper's class.
3. Analysis honesty: analysis_for_class() totals (marks,
   questions, per-chapter marks) equal sums recomputed directly
   from the library here in the test.
4. Generator: for Class 10 AND Class 12 the generated paper
   follows PAPER_STRUCTURE exactly and totals 80 marks; every
   question carries chapter + marks; generated questions are
   labelled (origin text + the "practice question" tag rendered
   on the page).
5. Menu: the home page menu contains Previous Papers immediately
   after Board Mode.

Run:  python verify_wave16.py
"""
import html as _html
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")
os.environ["GANITRA_DB_PATH"] = "/tmp/ganitra-verify-wave16.db"
import uuid as _uuid
RUN_ID = _uuid.uuid4().hex[:8]

from app import create_app  # noqa: E402
from i18n import STRINGS  # noqa: E402
import papers_data  # noqa: E402
from board_data import get_chapter  # noqa: E402

EN = STRINGS["en"]
fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:46} {detail}")
    if not cond:
        fails.append((cat, detail))


def esc(text):
    return _html.escape(str(text), quote=True)


# --- 2. Library integrity ----------------------------------------------------
check("library: at least 3 real papers collected",
      len(papers_data.PAPERS) >= 3,
      f"papers={len(papers_data.PAPERS)}")
for paper in papers_data.PAPERS:
    pid = paper["id"]
    check(f"library[{pid}]: source URL + year present",
          str(paper.get("source_url", "")).startswith("http")
          and isinstance(paper.get("year"), int)
          and bool(paper.get("source_name")))
    bad = [q for q in paper["questions"]
           if q["section"] not in papers_data.PAPER_STRUCTURE
           or not isinstance(q["marks"], int) or q["marks"] <= 0
           or get_chapter(paper["class_num"], q["chapter"]) is None
           or not str(q["text"]).strip()]
    check(f"library[{pid}]: every question has chapter+marks",
          not bad, f"bad={len(bad)}")
    # Merge fix (Waves 38–46): Term-2 papers added in Wave 44 are
    # complete 40-mark papers that genuinely have 14 questions, so
    # the blanket >=30 floor (written before they existed) gets a
    # Term-2 exception — >=14 when the paper's total is 40 marks.
    paper_total_marks = sum(q["marks"] for q in paper["questions"])
    min_questions = 14 if paper_total_marks == 40 else 30
    check(f"library[{pid}]: questions present",
          len(paper["questions"]) >= min_questions,
          f"questions={len(paper['questions'])}")

# --- 3. Analysis totals recomputed -------------------------------------------
for class_num in papers_data.CLASSES_WITH_PAPERS:
    marks = questions = 0
    per_chapter = {}
    for paper in papers_data.papers_for_class(class_num):
        for q in paper["questions"]:
            marks += q["marks"]
            questions += 1
            per_chapter[q["chapter"]] = \
                per_chapter.get(q["chapter"], 0) + q["marks"]
    a = papers_data.analysis_for_class(class_num)
    check(f"analysis[{class_num}]: totals == library sums",
          a["total_marks"] == marks
          and a["total_questions"] == questions
          and a["paper_count"]
          == len(papers_data.papers_for_class(class_num)),
          f"marks={a['total_marks']} vs {marks}")
    got = {row["slug"]: row["marks"] for row in a["chapters"]}
    check(f"analysis[{class_num}]: per-chapter marks == sums",
          got == per_chapter)
    check(f"analysis[{class_num}]: shares add to ~100",
          abs(sum(r["share"] for r in a["chapters"]) - 100.0) < 0.6,
          f"sum={sum(r['share'] for r in a['chapters'])}")

# --- 4. Generator structure (data level) --------------------------------------
for class_num in (10, 12):
    gen = papers_data.generate_practice_paper(class_num, seed=7)
    structure_ok = all(
        len(sec["questions"])
        == papers_data.PAPER_STRUCTURE[sec["section"]][0]
        and all(q["marks"]
                == papers_data.PAPER_STRUCTURE[sec["section"]][1]
                for q in sec["questions"])
        for sec in gen["sections"])
    check(f"generator[{class_num}]: section structure A-E exact",
          structure_ok
          and [s["section"] for s in gen["sections"]]
          == list(papers_data.PAPER_STRUCTURE))
    check(f"generator[{class_num}]: TOTAL marks = 80",
          gen["total_marks"] == 80
          and sum(q["marks"] for s in gen["sections"]
                  for q in s["questions"]) == 80,
          f"total={gen['total_marks']}")
    labelled = all(
        q.get("chapter") and q.get("marks")
        and (q["source"] != "generated"
             or "practice question" in q["origin"].lower())
        for s in gen["sections"] for q in s["questions"])
    check(f"generator[{class_num}]: chapter+marks, generated labelled",
          labelled)
    real_ok = all(
        q["answer_key"].get("url", "").startswith("http")
        for s in gen["sections"] for q in s["questions"]
        if q["source"] == "real")
    check(f"generator[{class_num}]: real questions link to source",
          real_ok)

# --- 1 + 4 + 5. Routes ---------------------------------------------------------
app = create_app()
anon = app.test_client()
for path in ("/papers", "/papers/analysis", "/papers/generate",
             "/papers/print",
             "/papers/" + papers_data.PAPERS[0]["id"]):
    r = anon.get(path)
    loc = r.headers.get("Location", "")
    check(f"gate: anonymous GET {path} redirects to sign-in",
          r.status_code in (301, 302) and loc in ("/", ""),
          f"status={r.status_code} loc={loc}")

client = app.test_client()
NAME = "W16 Papers " + RUN_ID
r = client.post("/signup", data={
    "name": NAME, "class": "10", "board": "CBSE",
    "goal": "Engineer", "hobby": "Reading", "favourite": "Mango",
    "password": "w16test-pass"})
check("signup for papers test user", r.status_code in (200, 302),
      f"status={r.status_code}")

r = client.get("/papers")
body = r.get_data(as_text=True)
check("GET /papers (signed in) -> 200 + library listed",
      r.status_code == 200
      and all(p["source_url"] in body for p in papers_data.PAPERS))

first = papers_data.PAPERS[0]
r = client.get("/papers/" + first["id"])
body = r.get_data(as_text=True)
check("GET /papers/<id> -> 200 + questions rendered",
      r.status_code == 200
      and body.count('class="paper-q"') == len(first["questions"]),
      f"rendered={body.count('paper-q')}")

r = client.get("/papers/analysis")
body = r.get_data(as_text=True)
a10 = papers_data.analysis_for_class(10)
check("GET /papers/analysis -> 200 + real totals shown",
      r.status_code == 200 and str(a10["total_marks"]) in body
      and esc(EN["papers_weightage_heading"]) in body)

r = client.get("/papers/generate")
check("GET /papers/generate -> 200 (form)",
      r.status_code == 200
      and esc(EN["papers_make_btn"]) in
      r.get_data(as_text=True))

for class_num in (10, 12):
    r = client.post("/papers/generate",
                    data={"class_num": str(class_num)})
    body = r.get_data(as_text=True)
    check(f"POST /papers/generate class {class_num} -> 200, "
          "80-mark paper + labels",
          r.status_code == 200
          and body.count('class="paper-q"') >= 76
          and esc(EN["papers_practice_tag"]) in body
          and esc(EN["papers_answer_key_heading"]) in body,
          f"paper-q blocks={body.count('paper-q')}")
    r = client.get("/papers/print")
    check(f"GET /papers/print class {class_num} -> 200",
          r.status_code == 200
          and "Ganitra Practice Paper" in
          r.get_data(as_text=True))

# --- 5. Menu order -------------------------------------------------------------
home = client.get("/").get_data(as_text=True)
_dd = home[home.index('class="nav-dropdown'):] \
    if 'class="nav-dropdown' in home else ""
board_pos = _dd.find(esc(EN["nav_board"]))
papers_pos = _dd.find(esc(EN["menu_papers"]))
practice_pos = _dd.find(esc(EN["nav_practice"]))
check("menu: Previous Papers present after Board Mode",
      0 <= board_pos < papers_pos < practice_pos,
      f"board={board_pos} papers={papers_pos} "
      f"practice={practice_pos}")
check("menu: papers link points to /papers",
      'href="/papers"' in _dd)

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
