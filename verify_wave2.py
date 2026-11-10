"""Wave-2 verification: distributions, ODE upgrade, transforms & series,
graph upgrade (two functions + shaded integral area), timed quiz flow,
session history, solution download, and the premium homepage."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from solver.router import solve_question  # noqa: E402

fails = []


def check(cat, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {cat:28} {detail}")
    if not cond:
        fails.append((cat, detail))


def close(a, b, tol=0.001):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


# --- 1. Distributions ---------------------------------------------------
r = solve_question("normal distribution mean 0 sd 1, P(X < 1)")
check("normal P(X<1) std", close(r.get("value"), 0.8413),
      f"value={r.get('value')} (expect 0.8413) steps={len(r['steps'])}")
check("normal steps show formula",
      any("z = (x" in s or "Standardise" in s for s in r["steps"]))
r = solve_question("normal distribution mean 100 sd 15, P(X > 130)")
check("normal P(X>130)", close(r.get("value"), 0.0228),
      f"value={r.get('value')} (expect 0.0228)")
r = solve_question("normal distribution mean 50 sd 10, probability "
                   "between 40 and 60")
check("normal between", close(r.get("value"), 0.6827),
      f"value={r.get('value')} (expect 0.6827)")
r = solve_question("z-score of 130 with mean 100 and standard deviation 15")
check("z-score", close(r.get("value"), 2.0), f"value={r.get('value')}")
r = solve_question("normal distribution mean 0 sd 1, find x so that "
                   "P(X < x) = 0.95")
check("normal inverse", close(r.get("value"), 1.6449, 0.01),
      f"value={r.get('value')} (expect ~1.6449)")
r = solve_question("Poisson lambda 3, probability of exactly 2 events")
check("poisson P(X=2)", close(r.get("value"), 0.2240),
      f"value={r.get('value')} (expect 0.2240)")
r = solve_question("Poisson distribution lambda = 4, probability of "
                   "at most 1 event")
check("poisson P(X<=1)", close(r.get("value"), 0.0916),
      f"value={r.get('value')} (expect 0.0916)")
r = solve_question("binomial n=10 p=0.5, P(X=5)")
check("binomial P(X=5)", close(r.get("value"), 0.2461),
      f"value={r.get('value')} (expect 0.2461)")
r = solve_question("binomial n=20 p=0.3, P(X <= 4)")
check("binomial P(X<=4)", close(r.get("value"), 0.2375),
      f"value={r.get('value')} (expect 0.2375)")

# --- 2. ODE upgrade -----------------------------------------------------
r = solve_question("solve dy/dx = x*y")
check("ode separable", "exp(x^2/2)" in r["answer"]
      and r.get("op") == "differential_equation", r["answer"])
r = solve_question("solve dy/dx + y = x")
check("ode linear", "exp(-x)" in r["answer"], r["answer"])
r = solve_question("solve d2y/dx2 + y = 0")
check("ode second order", "sin(x)" in r["answer"]
      and "cos(x)" in r["answer"], r["answer"])
r = solve_question("solve y'' + y = 0")
check("ode y'' form", "sin(x)" in r["answer"], r["answer"])
r = solve_question("solve dy/dx = 2x, y(0) = 1")
check("ode initial condition", r["answer"].replace(" ", "") == "y=x^2+1",
      r["answer"])
r = solve_question("find dy/dx for x^2 + y^2 = 25")
check("implicit diff intact", r.get("op") == "implicit_derivative"
      and "-x/y" in r["answer"], r["answer"])

# --- 3. Transforms & series ---------------------------------------------
r = solve_question("Laplace transform of t")
check("laplace t", "s^(-2)" in r["answer"], r["answer"])
r = solve_question("Laplace transform of exp(-2t)")
check("laplace exp(-2t)", "1/(s + 2)" in r["answer"], r["answer"])
r = solve_question("inverse Laplace transform of 1/s^2")
check("inverse laplace 1/s^2", r["answer"].strip() == "t", r["answer"])
r = solve_question("inverse Laplace of 1/(s^2+1)")
check("inverse laplace 1/(s^2+1)", "sin(t)" in r["answer"], r["answer"])
r = solve_question("Taylor series of e^x up to order 4")
check("taylor e^x order 4", "x^4/24" in r["answer"]
      and "x^3/6" in r["answer"], r["answer"])
r = solve_question("Maclaurin series of sin(x) up to order 5")
check("maclaurin sin order 5", "x^5/120" in r["answer"], r["answer"])
r = solve_question("partial fractions of 1/(x^2-1)")
check("partial fractions", "1/(2" in r["answer"]
      and "x - 1" in r["answer"] and "x + 1" in r["answer"], r["answer"])

# --- 4. Graph upgrade ----------------------------------------------------
base = Path(__file__).parent / "static"
r = solve_question("plot x^2 and x+1")
img = base / (r.get("image") or "missing")
check("two-function plot", img.exists() and img.stat().st_size > 3000
      and "x + 1" in r["answer"],
      f"{r.get('image')} size={img.stat().st_size if img.exists() else 0}")
r = solve_question("plot x^2 - 3x + 2")
img = base / (r.get("image") or "missing")
check("single plot intact", img.exists() and img.stat().st_size > 3000,
      str(r.get("image")))
r = solve_question("integrate x^2 from 0 to 1 and show the graph")
img = base / (r.get("image") or "missing")
check("integral + shaded graph", r["answer"] == "1/3" and img.exists()
      and img.stat().st_size > 3000,
      f"answer={r['answer']} image={r.get('image')}")
r = solve_question("integrate x^2 from 0 to 1")
check("integral without graph has no image",
      r["answer"] == "1/3" and not r.get("image"), r["answer"])

# --- 5-7. Quiz flow, history, download (test client) ---------------------
app = create_app()
client = app.test_client()

r = client.get("/")
body = r.get_data(as_text=True)
# Wave 7: the homepage is now a PURE chat screen (the user rejected
# the landing-style front), so this check asserts the new contract —
# chat shell + composer, and NO hero / topic grid / how-it-works on
# the home page (the topics moved to /topics) — instead of the old
# wave-2/5 hero-and-topics contract.
check("homepage premium", r.status_code == 200 and 'class="chat-shell"' in body
      and 'name="question"' in body and 'action="/solve"' in body
      and 'id="chat-log"' in body and 'class="chat-bar"' in body
      and 'class="chip"' not in body and "topic-grid" not in body
      and 'class="hero rise"' not in body,
      f"status={r.status_code} chips={body.count(chr(34).join(['class=', 'chip', '']))}")

r = client.post("/solve", data={"question": "mean of 2, 4, 6, 8"})
body = r.get_data(as_text=True)
check("solve page + download link", r.status_code == 200
      and "/download" in body, f"status={r.status_code}")

r = client.get("/history")
body = r.get_data(as_text=True)
check("history records question", r.status_code == 200
      and "mean of 2, 4, 6, 8" in body, f"status={r.status_code}")

r = client.get("/download")
body = r.get_data(as_text=True)
disp = r.headers.get("Content-Disposition", "")
check("download solution txt", r.status_code == 200
      and "attachment" in disp and "solution.txt" in disp
      and "Question: mean of 2, 4, 6, 8" in body
      and "Step-by-step" in body,
      f"status={r.status_code} disp={disp}")

r = client.get("/practice")
body = r.get_data(as_text=True)
check("practice setup form", r.status_code == 200
      and 'name="topic"' in body and 'name="difficulty"' in body,
      f"status={r.status_code}")

r = client.post("/practice/start",
                data={"topic": "algebra", "difficulty": "medium"})
body = r.get_data(as_text=True)
check("quiz starts with 5 inputs + timer",
      r.status_code == 200 and body.count('name="answer_') == 5
      and 'id="timer"' in body,
      f"inputs={body.count(chr(34).join([]) or 'name=')} status={r.status_code}")

with client.session_transaction() as sess:
    quiz = sess.get("quiz") or {}
check("quiz in session", quiz.get("topic") == "algebra"
      and len(quiz.get("questions", [])) == 5,
      f"topic={quiz.get('topic')}")

answers = {f"answer_{i}": item["answer"]
           for i, item in enumerate(quiz.get("questions", []))}
answers["time_taken"] = "37"
r = client.post("/practice/submit", data=answers)
body = r.get_data(as_text=True)
check("quiz all-correct scores 5/5", "Score: 5 / 5" in body,
      f"status={r.status_code}")

client.post("/practice/start",
            data={"topic": "stats", "difficulty": "easy"})
r = client.post("/practice/submit",
                data={f"answer_{i}": "99999" for i in range(5)})
check("quiz all-wrong scores 0/5",
      "Score: 0 / 5" in r.get_data(as_text=True), "")

r = client.get("/practice/classic")
body = r.get_data(as_text=True)
check("classic practice intact", r.status_code == 200
      and body.count("practice-q") >= 7 and "Show answer" in body,
      f"status={r.status_code} sets={body.count('practice-q')}")

print()
print("FAILURES:", len(fails))
for cat, detail in fails:
    print(" -", cat, "|", detail)
