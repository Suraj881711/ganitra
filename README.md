# Ganitra — Maths, Solved Step by Step

**Ganitra** is a maths question-answering app powered by **Flask + SymPy**. Type a question
in plain English (or basic Hinglish), and it routes the question to the right
solver, works it out symbolically, and shows a **step-by-step solution** —
in the web UI, through a JSON API, or on the command line.

## Features

- **Step-by-step solutions** for the main categories (arithmetic reduction
  steps, linear/quadratic working, power-rule steps for derivatives and
  integrals, GCD/LCM via prime factorisation, probability working, ...).
- **Probability distributions** — Normal (probabilities, z-scores,
  percentiles/inverse lookups), Poisson and binomial, all with the
  formula and substitution shown. Computed with the standard library
  only — no SciPy.
- **Transforms & series** — Laplace and inverse Laplace transforms,
  Taylor/Maclaurin expansions to a chosen order, partial fractions.
- **Stronger ODEs** — separable, linear and second-order differential
  equations via `dsolve`, including simple initial conditions
  (`solve dy/dx = 2x, y(0) = 1`).
- **Function plotting** — `plot x^2 - 3x + 2` renders a real graph (PNG);
  two functions can be plotted together (`plot x^2 and x+1`), and a
  definite integral can shade its area
  (`integrate x^2 from 0 to 1 and show the graph`).
- **Timed quiz** — `/practice` offers a 5-question quiz by topic
  (arithmetic, algebra, trigonometry, statistics) and difficulty, with
  a countdown timer and a server-checked score; the classic
  reveal-the-answer practice set is still there too.
- **History & download** — `/history` lists the questions you solved in
  this session (click to re-open a solution), and every answer page can
  download its step-by-step solution as a `.txt` file.
- **Hinglish input** — e.g. `5 aur 3 ko jodo`, `240 ka 15 pratishat`,
  `2, 4, 6 ka ausat`, `sin 30 ka maan`.
- **Voice input** 🎤 — "Bol ke poochho": speak your question (Hindi or
  English) using the browser's Web Speech API; the transcript fills the
  box and you press Solve. Chrome recommended; nothing is sent to a
  server until you solve.
- **Photo input** 📷 — "Photo se sawaal": upload a photo of a question
  and it is read **in your browser** with Tesseract.js (no server-side
  OCR, no extra dependencies). The recognised text is cleaned up
  (e.g. `−` → `-`, `x2` → `x^2`) and shown in an **editable box** —
  check/fix it, then Solve. Works best on printed/typed questions;
  handwriting often needs a quick edit, which is exactly what the
  confirm box is for.
- **Pretty maths** — MathJax rendering in the web UI.
- Three interfaces: web UI, REST API (`POST /api/solve`), and a CLI.

## Topics covered

| Area | Examples |
|---|---|
| Arithmetic, fractions, percentages | `2+2*5` · `3/4 + 1/2` · `15% of 240` |
| Algebra | `2x + 3 = 7` · `x^2 - 5x + 6 = 0` · `x + y = 10 and x - y = 4` · `2x + 3 > 7` · `factor x^2 - 5x + 6` · `expand (x+2)(x+3)` · `simplify (x^2-1)/(x-1)` |
| Exponents & logarithms | `log base 2 of 32` · `log2(32)` · `solve 2^x = 32` |
| Trigonometry | `sin 30` · `cos(pi/3)` · `prove sin^2(x) + cos^2(x) = 1` · `solve sin(x) = 1/2` · `arcsin(0.5)` (bare numbers = degrees) |
| Calculus | `limit x->0 of sin(x)/x` · `derivative of x^3 + 2x` · `partial derivative of x^2*y with respect to y` · `find dy/dx for x^2 + y^2 = 25` · `integrate x^2 from 0 to 1` · `solve dy/dx = x*y` · `solve d2y/dx2 + y = 0` · `solve dy/dx = 2x, y(0) = 1` |
| Transforms & series | `Laplace transform of t` · `Laplace transform of exp(-2t)` · `inverse Laplace of 1/(s^2+1)` · `Taylor series of e^x up to order 4` · `Maclaurin series of sin(x) up to order 5` · `partial fractions of 1/(x^2-1)` |
| Linear algebra | `determinant of [[1,2],[3,4]]` · `inverse of ...` · `eigenvalues of ...` · `rank of ...` · `multiply [[..]] and [[..]]` · `A=[[2,1],[1,3]], b=[[5],[10]]` |
| Geometry | `area of circle with radius 5` · `volume of sphere with radius 3` · `perimeter of rectangle ...` · Heron's formula |
| Coordinate geometry | `distance between (1,2) and (4,6)` · `midpoint of ...` · `slope ...` · `equation of line through (1,2) and (3,6)` · `equation of circle with centre (1,2) and radius 3` |
| Statistics | `mean/median/mode of ...` · `standard deviation of ...` · `variance of ...` · `range of ...` |
| Probability & counting | `probability of getting a 6 on a dice` · `probability of sum 7 with two dice` · `probability of exactly 2 heads in 3 coin tosses` · balls-in-a-bag · cards · binomial `exactly 3 successes in 10 trials with p = 0.5` · `P(5,2)` · `C(5,2)` · `factorial of 5` |
| Distributions | `normal distribution mean 0 sd 1, P(X < 1)` · `normal distribution mean 100 sd 15, P(X > 130)` · `z-score of 130 with mean 100 and standard deviation 15` · `Poisson lambda 3, probability of exactly 2 events` · `binomial n=10 p=0.5, P(X=5)` · `binomial n=20 p=0.3, P(X <= 4)` |
| Distributions | `normal distribution mean 0 sd 1, P(X < 1)` · `normal distribution mean 100 sd 15, P(X > 130)` · `z-score of 130 with mean 100 and standard deviation 15` · `Poisson lambda 3, probability of exactly 2 events` · `binomial n=10 p=0.5, P(X=5)` · `binomial n=20 p=0.3, P(X <= 4)` |
| Number theory | `is 97 prime?` · `factor 360` · `gcd of 12 and 18` · `lcm of 4 and 6` · `17 mod 5` · `is 144 divisible by 12` |
| Sequences & series | `10th term of AP 2, 5, 8` · `sum of first 10 terms of AP 2, 5, 8` · `5th term of GP 3, 6, 12` · `sum of first 10 natural numbers` (also squares/cubes) |
| Complex numbers | `(2+3i)*(1-i)` · `modulus of 3+4i` · `conjugate of 3+4i` · `argument of 1+i` |
| Sets | `{1,2,3} union {3,4,5}` · `{1,2,3} intersection {2,3,4}` · difference · symmetric difference |
| Unit conversion | `convert 5 km to miles` · `convert 2 kg to grams` · `convert 37 celsius to fahrenheit` · length, mass, time, volume, area, temperature |
| Word problems | `increase by 15% of 240` · `60 km/h for 2 hours` · `sum is 10 and product is 21` · `simple interest on 1000 at 5% for 2 years` |
| Graphs | `plot x^2 - 3x + 2` · `graph sin(x)` · `plot x^2 and x+1` (two functions) · `integrate x^2 from 0 to 1 and show the graph` (shaded area) |

## How to run

```bash
pip install -r requirements.txt
python app.py          # web UI at http://127.0.0.1:5000
```

Command line:

```bash
python cli.py "derivative of x^3 + 2x"
python cli.py "integrate x^2 from 0 to 1" --json
```

API:

```bash
curl -X POST http://127.0.0.1:5000/api/solve \
  -H "Content-Type: application/json" \
  -d '{"question": "mean of 2, 4, 6, 8"}'
# -> {"ok": true, "result": {"type": "statistics", "op": "mean",
#      "answer": "5", "steps": [...], ...}}
```

Tests and end-to-end checks (sample questions for every feature,
old and new):

```bash
pytest            # 23 tests
python verify_all.py    # wave-1 samples (76 questions + flows)
python verify_wave2.py  # wave-2 samples (distributions, ODEs,
                        # transforms, graphs, quiz, history, download)
```

## Screenshots

<!-- TODO: add screenshots of the home page, a step-by-step answer page,
     a plotted graph, and the practice page here. -->

## Tech stack

- **Python + Flask** — web app, API blueprint, Jinja templates
- **SymPy** — symbolic engine (solving, calculus, matrices, trig, ...)
- **Matplotlib** — function graphs
- **MathJax** — formula rendering in the browser
- **pytest** — test suite

## Project structure

```
app.py                  Flask app (/, /solve, /practice + timed quiz,
                        /history, /download)
api.py                  JSON API blueprint (/api/solve)
cli.py                  Command-line interface
solver/
  router.py             Hinglish normalisation + topic routing + fallback
  expression_parser.py  parse_expression (the SymPy parsing core), helpers
  arithmetic.py         expressions, fractions, percentages (+ BODMAS steps)
  algebra.py            equations, systems, inequalities, factor/expand/simplify
  exponents_logs.py     logarithms and exponential/log equations
  calculus.py           limits, derivatives (partial/implicit), integrals,
                        ODEs via dsolve (separable/linear/2nd-order + ICs)
  transforms.py         Laplace & inverse Laplace, Taylor/Maclaurin
                        series, partial fractions
  distributions.py      Normal / Poisson / binomial (stdlib math only)
  linear_algebra.py     matrices: det, inverse, eigen, rank, Ax=b, ...
  trigonometry.py       values, identities, equations, inverse trig
  geometry.py           shapes + coordinate geometry
  statistics.py         descriptive stats, counting, probability
  number_theory.py      primes, factorisation, GCD/LCM, modulo
  sequences.py          AP/GP terms & sums, natural-number series
  complex_numbers.py    complex arithmetic, modulus, conjugate, argument
  sets_basics.py        union / intersection / difference
  units.py              unit & temperature conversion
  word_problems.py      percent change, distance, sum-product, simple interest
  plotting.py           matplotlib graphs (1-2 functions, integral shading)
  practice.py           practice sets + timed-quiz generators/checker
templates/, static/     Jinja templates and CSS (graphs land in static/graphs/)
test/                   pytest suite
verify_all.py           wave-1 end-to-end verification (not part of the app)
verify_wave2.py         wave-2 end-to-end verification (not part of the app)
verify_wave3.py         wave-3 verification: voice/photo inputs (not part of the app)
```

## Notes & honest limits

- Trigonometry treats a bare number as **degrees** (`sin 30` = 1/2) unless
  the question mentions radians or uses `pi`.
- Standard deviation is the **population** standard deviation.
- Differential equations cover first-order separable/linear forms and
  constant-coefficient second-order forms, with simple numeric initial
  conditions; exotic nonlinear ODEs may still defeat `dsolve`.
- Distribution questions need the distribution named (normal / Poisson /
  binomial) with its parameters (mean & sd, lambda, or n & p).
- The solver understands common phrasings; very free-form word problems
  outside the listed patterns may not parse — the answer page then says so
  instead of guessing.
- Photo OCR runs in the browser (Tesseract.js) and reads **printed or
  typed** questions best; handwritten questions may come out wrong —
  that is why the recognised text is always shown in an editable box
  before solving. Voice input depends on the browser's speech
  recognition (Chrome works best) and needs mic permission.
