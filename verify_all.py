"""End-to-end verification via the Flask test client + API + plot file."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("MPLCONFIGDIR", "/tmp/mplconfig")

from app import create_app  # noqa: E402
from solver.router import solve_question  # noqa: E402

SAMPLES = [
    # (category, question, substring expected in the answer)
    ("arithmetic", "2+2*5", "12"),
    ("arithmetic-fraction", "3/4 + 1/2", "5/4"),
    ("arithmetic-percent", "15% of 240", "36"),
    ("algebra-linear", "2*x + 3 = 7", "x = 2"),
    ("algebra-quadratic", "x^2 - 5x + 6 = 0", "x = 2"),
    ("algebra-system", "x + y = 10 and x - y = 4", "x = 7"),
    ("algebra-inequality", "2x + 3 > 7", "2"),
    ("algebra-factor", "factor x^2 - 5x + 6", "x - 2"),
    ("algebra-expand", "expand (x+2)(x+3)", "x^2 + 5"),
    ("algebra-simplify", "simplify (x^2-1)/(x-1)", "x + 1"),
    ("exponents-logs", "log base 2 of 32", "5"),
    ("exponents-eq", "solve 2^x = 32", "x = 5"),
    ("trig-value-deg", "sin 30", "1/2"),
    ("trig-value-rad", "cos(pi/3)", "1/2"),
    ("trig-identity", "prove sin^2(x) + cos^2(x) = 1", "verified"),
    ("trig-equation", "solve sin(x) = 1/2", "150"),
    ("trig-inverse", "arcsin(0.5)", "30"),
    ("calculus-limit", "limit x->0 of sin(x)/x", "1"),
    ("calculus-derivative", "derivative of x^3 + 2x", "3"),
    ("calculus-partial", "partial derivative of x^2*y with respect to y", "x^2"),
    ("calculus-implicit", "find dy/dx for x^2 + y^2 = 25", "-x/y"),
    ("calculus-integral-def", "integrate x^2 from 0 to 1", "1/3"),
    ("calculus-integral-indef", "integrate 2x", "x^2"),
    ("calculus-ode", "solve dy/dx = 2x", "C1"),
    ("linalg-det", "determinant of [[1,2],[3,4]]", "-2"),
    ("linalg-inverse", "inverse of [[1,2],[3,4]]", "-2"),
    ("linalg-eigen", "eigenvalues of [[2,0],[0,3]]", "3"),
    ("linalg-rank", "rank of [[1,2],[2,4]]", "1"),
    ("linalg-multiply", "multiply [[1,2],[3,4]] and [[5,6],[7,8]]", "19"),
    ("linalg-solve", "A=[[2,1],[1,3]], b=[[5],[10]]", "1"),
    ("geometry-area", "area of circle with radius 5", "78.5"),
    ("geometry-volume", "volume of sphere with radius 3", "113"),
    ("geometry-distance", "distance between (1,2) and (4,6)", "5"),
    ("geometry-midpoint", "midpoint of (1,2) and (4,6)", "(2.5, 4)"),
    ("geometry-line", "equation of line through (1,2) and (3,6)", "y = 2x"),
    ("geometry-circle-eq", "equation of circle with centre (1,2) and radius 3", "9"),
    ("stats-mean", "mean of 2, 4, 6, 8", "5"),
    ("stats-median", "median of 1, 3, 3, 6, 7, 8, 9", "6"),
    ("stats-mode", "mode of 1, 2, 2, 3", "2"),
    ("stats-std", "standard deviation of 2,4,4,4,5,5,7,9", "2"),
    ("stats-perm", "P(5,2)", "20"),
    ("stats-comb", "C(5,2)", "10"),
    ("stats-prob-dice", "probability of getting a 6 on a dice", "1/6"),
    ("stats-prob-2dice", "probability of sum 7 with two dice", "1/6"),
    ("stats-prob-coins", "probability of exactly 2 heads in 3 coin tosses", "3/8"),
    ("stats-prob-balls", "a bag has 5 red balls and 3 blue balls, probability of drawing a red ball", "5/8"),
    ("stats-prob-cards", "probability of drawing an ace from a pack of cards", "1/13"),
    ("stats-binomial", "probability of exactly 3 successes in 10 trials with p = 0.5", "0.117"),
    ("numtheory-prime", "is 97 prime?", "prime"),
    ("numtheory-factor", "factor 360", "2^3"),
    ("numtheory-gcd", "gcd of 12 and 18", "6"),
    ("numtheory-lcm", "lcm of 4 and 6", "12"),
    ("numtheory-mod", "17 mod 5", "2"),
    ("sequences-ap-term", "10th term of AP 2, 5, 8", "29"),
    ("sequences-ap-sum", "sum of first 10 terms of AP 2, 5, 8", "155"),
    ("sequences-gp-term", "5th term of GP 3, 6, 12", "48"),
    ("sequences-natural", "sum of first 10 natural numbers", "55"),
    ("complex-mult", "(2+3i)*(1-i)", "5 + I"),
    ("complex-modulus", "modulus of 3+4i", "5"),
    ("complex-conjugate", "conjugate of 3+4i", "3 - 4·I"),
    ("sets-union", "{1,2,3} union {3,4,5}", "{1, 2, 3, 4, 5}"),
    ("sets-intersection", "{1,2,3} intersection {2,3,4}", "{2, 3}"),
    ("units-length", "convert 5 km to miles", "3.106"),
    ("units-temp", "convert 37 celsius to fahrenheit", "98.6"),
    ("units-mass", "convert 2 kg to grams", "2000"),
    ("word-percent-change", "increase by 15% of 240", "276"),
    ("word-sum-product", "sum is 10 and product is 21", "(3, 7)"),
    ("word-distance", "60 km/h for 2 hours", "120"),
    ("word-si", "simple interest on 1000 at 5% for 2 years", "100"),
    ("hinglish-add", "5 aur 3 ko jodo", "8"),
    ("hinglish-subtract", "20 mein se 7 ghatana", "13"),
    ("hinglish-multiply", "4 guna 5", "20"),
    ("hinglish-divide", "20 ko 4 se bhaag do", "5"),
    ("hinglish-percent", "240 ka 15 pratishat", "36"),
    ("hinglish-average", "2, 4, 6 ka ausat", "4"),
    ("hinglish-trig", "sin 30 ka maan", "1/2"),
]

fails = []
for cat, q, expect in SAMPLES:
    r = solve_question(q)
    answer = str(r.get("answer", ""))
    ok = expect in answer and r.get("op") != "error"
    steps = len(r.get("steps") or [])
    print(f"[{'PASS' if ok else 'FAIL'}] {cat:26} {q[:52]:54} -> "
          f"{answer[:44]} (steps={steps})")
    if not ok:
        fails.append((cat, q, r))

print()
app = create_app()
client = app.test_client()

r = client.get("/")
print("GET / ->", r.status_code)
r = client.get("/practice")
body = r.get_data(as_text=True)
print("GET /practice ->", r.status_code,
      "| questions rendered:", body.count("practice-q"),
      "| has Show answer:", "Show answer" in body)
r = client.post("/solve", data={"question": "derivative of x^3 + 2x"})
body = r.get_data(as_text=True)
print("POST /solve (derivative) ->", r.status_code,
      "| steps shown:", "Step-by-step" in body,
      "| answer present:", "3" in body)
r = client.post("/api/solve", json={"question": "integrate x^2 from 0 to 1"})
data = r.get_json()
print("POST /api/solve ->", r.status_code, "| ok:", data["ok"],
      "| answer:", data["result"]["answer"],
      "| steps:", len(data["result"].get("steps", [])))

r = solve_question("plot x^2 - 3x + 2")
print("plot result:", r.get("type"), r.get("image"))
img = Path(__file__).parent / "static" / (r.get("image") or "")
print("graph PNG exists:", img.exists(),
      "| size:", img.stat().st_size if img.exists() else 0, "bytes")
if not img.exists() or img.stat().st_size < 2000:
    fails.append(("plot", "plot x^2 - 3x + 2", r))

print()
print("FAILURES:", len(fails))
for cat, q, r in fails:
    print(" -", cat, "|", q, "|", json.dumps(r, default=str)[:220])
