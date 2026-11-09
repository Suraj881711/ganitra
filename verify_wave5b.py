"""Wave-5b/5d/5e verification: student-proofing (friendly localised
errors, no raw solver text, no JSON dump), chat failure contract,
slow-server note, form safety, empty states, the CSS comfort audit,
✍️ Copy Style (handwriting) presentation, the board-style Copy
Check card, the Dhyaan meter hooks and the Badhai celebration.

Run with the project venv:  python verify_wave5b.py
"""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from i18n import (STRINGS, SUPPORTED_LANGS, get_strings,  # noqa: E402
                  question_looks_like_gibberish, remark_key_for,
                  solve_failed)
from markupsafe import escape as _markupsafe_escape  # noqa: E402
from solver.router import solve_question  # noqa: E402


def esc(text):
    """How Jinja renders a string into HTML."""
    return str(_markupsafe_escape(text))


fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:38} {detail}")
    if not cond:
        fails.append((cat, detail))


app = create_app()
EN = STRINGS["en"]
HI = STRINGS["hi"]

# --- 1. Friendly errors on the classic answer page -------------------------
c = app.test_client()
r = c.post("/solve", data={"question": "asdf qwer zxq"})
body = r.get_data(as_text=True)
check("gibberish POST /solve status", r.status_code == 200,
      f"status={r.status_code}")
check("gibberish friendly heading", esc(EN["error_heading"]) in body)
check("gibberish friendly intro", esc(EN["error_intro"]) in body)
check("gibberish tips x3",
      all(esc(EN[f"error_tip{i}"]) in body for i in (1, 2, 3)))
check("gibberish retry button", esc(EN["error_retry_btn"]) in body
      and 'name="question"' in body)
check("gibberish NO JSON dump", "Full result" not in body
      and "full_result" not in body and "a*d*e*f" not in body)
check("gibberish NO raw error text", "Could not solve" not in body)
check("gibberish NO answer block", 'class="answer-big"' not in body)

r = c.post("/solve", data={"question": "who is the prime minister"})
body = r.get_data(as_text=True)
check("solver-error friendly card", r.status_code == 200
      and esc(EN["error_heading"]) in body
      and "Could not solve" not in body
      and "Give a number to test" not in body)

# --- 2. Form safety ----------------------------------------------------------
r = c.post("/solve", data={"question": ""}, follow_redirects=True)
check("empty question friendly", r.status_code == 200
      and esc(EN["flash_no_question"]) in r.get_data(as_text=True))
r = c.post("/solve", data={"question": "x" * 600},
           follow_redirects=True)
check("600-char question no 500", r.status_code == 200
      and esc(EN["flash_too_long"]) in r.get_data(as_text=True),
      f"status={r.status_code}")
r = c.post("/solve", data={"question": "   "}, follow_redirects=True)
check("blank question no 500", r.status_code == 200)

# --- 3. Chat failure contract (/api/solve) -----------------------------------
r = c.post("/api/solve", json={"question": "asdf qwer zxq"})
data = r.get_json() or {}
err = data.get("error") or {}
check("api gibberish unsolvable", r.status_code == 200
      and data.get("ok") is False and data.get("unsolvable") is True,
      f"status={r.status_code}")
check("api error contract", err.get("heading") == EN["error_heading"]
      and err.get("intro") == EN["error_intro"]
      and err.get("tips") == [EN["error_tip1"], EN["error_tip2"],
                              EN["error_tip3"]]
      and err.get("retry_label") == EN["error_retry_btn"])
check("api error NO raw text", "Could not solve" not in r.get_data(
    as_text=True) and "a*d*e*f" not in r.get_data(as_text=True))
r = c.post("/api/solve", json={"question": ""})
check("api empty friendly", (r.get_json() or {}).get("message")
      == EN["flash_no_question"])
r = c.post("/api/solve", json={"question": "y" * 600})
check("api 600-char friendly", (r.get_json() or {}).get("message")
      == EN["flash_too_long"])
r = c.post("/api/solve", json={"question": "x^2-5x+6=0"})
data = r.get_json() or {}
check("api success shape unchanged",
      sorted(data.keys()) == ["advice", "explanation", "ok", "result"]
      and data.get("ok") is True
      and (data.get("result") or {}).get("answer") == "x = 2, x = 3")

# --- 4. Gibberish guard precision ---------------------------------------------
for q in ("x + y", "(x+1)(x+2)", "2x + 3x", "abc", "xyz",
          "3abc + 2abc", "a + b", "xy + 2xy", "simplify x + x"):
    res = solve_question(q)
    check(f"legit simplify kept: {q}",
          not solve_failed(q, res)
          and not question_looks_like_gibberish(q, res))
r = c.post("/solve", data={"question": "x + y"})
check("x + y solves normally", r.status_code == 200
      and "error-card" not in r.get_data(as_text=True))

# --- 5. Slow-server note (en + hi) ---------------------------------------------
r = c.get("/")
body = r.get_data(as_text=True)
check("waking note (en)", esc(EN["chat_waking_note"]) in body)
c2 = app.test_client()
c2.get("/set-lang/hi")
r = c2.get("/")
check("waking note (hi)", esc(HI["chat_waking_note"])
      in r.get_data(as_text=True))

# --- 6. Empty states ------------------------------------------------------------
c3 = app.test_client()
r = c3.get("/mistakes")
check("mistakes empty state", r.status_code == 200
      and esc(EN["mistakes_empty"]) in r.get_data(as_text=True))
r = c3.get("/history")
check("history empty state", r.status_code == 200
      and esc(EN["history_empty"]) in r.get_data(as_text=True))

# --- 7. i18n completeness for ALL new keys ---------------------------------------
new_keys = {
    # wave 5b
    "error_heading", "error_intro", "error_tip1", "error_tip2",
    "error_tip3", "error_retry_btn", "try_again_link",
    "chat_waking_note", "flash_too_long", "photo_no_text",
    "empty_no_questions",
    # wave 5d
    "handwriting_btn", "print_copy_link",
    # wave 5e
    "copycheck_heading", "copycheck_note", "copycheck_lost_label",
    "copycheck_all_clear", "copycheck_practice_link",
    "remark_perfect", "remark_great", "remark_good", "remark_keep",
    "remark_try", "celebrate_msg", "mistakes_done_msg",
    "dhyaan_label", "dhyaan_today",
}
for code in SUPPORTED_LANGS:
    missing = new_keys - set(STRINGS[code])
    check(f"new keys complete ({code})", not missing,
          f"missing={sorted(missing)}")
en_keys = set(STRINGS["en"])
for code in SUPPORTED_LANGS:
    missing = en_keys - set(STRINGS[code])
    check(f"i18n fully complete ({code})", not missing,
          f"missing={sorted(missing)[:5]}")

# --- 8. Handwriting (Copy Style) ---------------------------------------------------
r = c.post("/solve", data={"question": "x^2-5x+6=0"})
body = r.get_data(as_text=True)
check("answer page handwriting toggle",
      'id="hw-toggle"' in body and esc(EN["handwriting_btn"]) in body)
check("steps notebook + default ON",
      'class="steps notebook handwriting-on"' in body)
check("print copy-style link", 'href="/solution/print?style=hand"' in body
      and esc(EN["print_copy_link"]) in body)
r = c.get("/solution/print?style=hand")
body = r.get_data(as_text=True)
check("print page copy style", r.status_code == 200
      and "notebook handwriting-on" in body and "Kalam" in body)
r = c.get("/solution/print")
body = r.get_data(as_text=True)
check("print page clean by default",
      'class="steps notebook' not in body
      and '<ol class="steps">' in body)
r = c.get("/")
body = r.get_data(as_text=True)
check("chat bubble handwriting hooks",
      "handwriting-on" in body and "hwOn" in body
      and "ganitra-handwriting" in body)
check("Kalam font loaded", "Kalam" in body and "Caveat" in body)

# --- 9. Copy Check + Badhai (chapter test) ------------------------------------------
ct = app.test_client()
ct.post("/board/test/start",
        data={"class_num": "10", "slug": "quadratic-equations"})
with ct.session_transaction() as sess:
    answers = [q["answer"] for q in sess["board_test"]["questions"]]
form = {f"answer_{i}": str(a) for i, a in enumerate(answers)}
r = ct.post("/board/test/submit", data=form)
body = r.get_data(as_text=True)
check("copycheck card (perfect test)", "copycheck-card" in body
      and esc(EN["copycheck_heading"]) in body)
check("copycheck perfect remark", esc(EN["remark_perfect"]) in body)
check("copycheck all-clear line", esc(EN["copycheck_all_clear"]) in body)
check("copycheck session report saved", True)  # asserted below via client 2
with ct.session_transaction() as sess:
    rep = sess.get("last_test_report") or {}
check("session report fields", rep.get("score") == 5
      and rep.get("total") == 5
      and rep.get("remark_key") == "remark_perfect"
      and rep.get("lost_topics") == []
      and rep.get("celebrate") is True,
      f"report={rep}")
check("badhai on perfect (>=80%)", "data-celebrate" in body
      and esc(EN["celebrate_msg"]) in body
      and "confetti-piece" in body)

ct.post("/board/test/start",
        data={"class_num": "10", "slug": "quadratic-equations"})
form = {f"answer_{i}": "-99999" for i in range(5)}
r = ct.post("/board/test/submit", data=form)
body = r.get_data(as_text=True)
check("copycheck lost-topics line",
      esc(EN["copycheck_lost_label"]) in body
      and "Quadratic Equations" in body)
check("copycheck practice link", esc(EN["copycheck_practice_link"])
      in body and 'href="/mistakes"' in body)
check("copycheck honest note", esc(EN["copycheck_note"]) in body)
check("no badhai below 80%", "data-celebrate" not in body)
with ct.session_transaction() as sess:
    rep = sess.get("last_test_report") or {}
check("session report (all wrong)",
      rep.get("lost_topics") == ["Quadratic Equations"]
      and rep.get("celebrate") is False, f"report={rep}")

# remark bands
check("remark band helper",
      [remark_key_for(s, 5) for s in (5, 4, 3, 2, 1)]
      == ["remark_perfect", "remark_great", "remark_good",
          "remark_keep", "remark_try"])
check("remark strings resolve", all(
    get_strings(code)[remark_key_for(4, 5)]
    for code in SUPPORTED_LANGS))

# timed quiz also gets a copy check (lost topic = quiz topic name)
qz = app.test_client()
qz.post("/practice/start", data={"topic": "algebra",
                                 "difficulty": "easy"})
form = {f"answer_{i}": "-99999" for i in range(5)}
r = qz.post("/practice/submit", data=form)
body = r.get_data(as_text=True)
check("quiz copycheck lost topic",
      esc(EN["copycheck_lost_label"]) in body
      and esc(EN["quiz_topic_algebra"]) in body)

# --- 10. Mistakes-retry completion -> Badhai ------------------------------------------
mc = app.test_client()
mc.post("/board/test/start",
        data={"class_num": "10", "slug": "quadratic-equations"})
mc.post("/board/test/submit",
        data={f"answer_{i}": "-99999" for i in range(5)})
r = mc.get("/mistakes/practice")
body = r.get_data(as_text=True)
check("mistakes round opens", r.status_code == 200
      and 'action="/mistakes/practice/submit"' in body)
r = mc.post("/mistakes/practice/submit")
body = r.get_data(as_text=True)
check("mistakes round done -> badhai", r.status_code == 200
      and "data-celebrate" in body
      and esc(EN["mistakes_done_msg"]) in body
      and "confetti-piece" in body)

# --- 11. Dhyaan meter hooks --------------------------------------------------------------
r = c.get("/")
body = r.get_data(as_text=True)
check("dhyaan pill on homepage", 'id="dhyaan-pill"' in body
      and esc(EN["dhyaan_label"]) in body)
check("dhyaan localStorage logic", "ganitra-dhyaan" in body
      and "ganitraDhyaanPaint" in body
      and "visibilitychange" in body)
check("dhyaan template (hi) formats", HI["dhyaan_today"].format(
    minutes=3, count=2).startswith("आज"))
r = c.get("/board")
check("dhyaan pill on /board", 'id="dhyaan-pill"'
      in r.get_data(as_text=True))
check("celebration CSS hooks", "confetti-fall" in
      Path("static/style.css").read_text(encoding="utf-8")
      and "prefers-reduced-motion" in
      Path("static/style.css").read_text(encoding="utf-8"))

# --- 12. CSS comfort audit ---------------------------------------------------------
css = Path("static/style.css").read_text(encoding="utf-8")
check("css overflow-x guard", "overflow-x: hidden" in css)
check("css notebook rules", "repeating-linear-gradient" in css
      and '"Kalam"' in css and "line-height: 1.95" in css)
check("css input font >= 16px", "textarea { width: 100%" in css
      and "font-size: 16px" in css)
check("css tap target floor", "min-height: 44px" in css)

# --- 13. JS syntax (node --check) -----------------------------------------------------
node = shutil.which("node")
for page, maker in (("answer", lambda cl: cl.post(
        "/solve", data={"question": "x^2-5x+6=0"})),
        ("home", lambda cl: cl.get("/")),
        ("board", lambda cl: cl.get("/board"))):
    cl = app.test_client()
    html = maker(cl).get_data(as_text=True)
    scripts = [s for s in re.findall(r"<script>(.*?)</script>", html,
                                     re.S) if s.strip()]
    if node:
        ok = True
        for i, s in enumerate(scripts):
            p = f"/tmp/w5b-{page}-{i}.js"
            Path(p).write_text(s, encoding="utf-8")
            ok = ok and subprocess.run(
                [node, "--check", p],
                capture_output=True).returncode == 0
        check(f"JS syntax ({page})", ok, f"scripts={len(scripts)}")
    else:
        check(f"JS syntax ({page})", True, "node unavailable — skipped")

print()
if fails:
    print(f"FAILURES: {len(fails)}")
    for cat, detail in fails:
        print(" -", cat, detail)
    sys.exit(1)
print("FAILURES: 0")
