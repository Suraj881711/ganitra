# Maths GPT — Solving Your Maths Problems

A maths question-answering app powered by **Flask + SymPy**. Type a question
in plain English (or basic Hinglish), and it routes the question to the right
solver, works it out symbolically, and shows a **step-by-step solution** —
in the web UI, through a JSON API, or on the command line.

## Features

- **Step-by-step solutions** for the main categories (arithmetic reduction
  steps, linear/quadratic working, power-rule steps for derivatives and
  integrals, GCD/LCM via prime factorisation, probability working, ...).
- **Function plotting** — `plot x^2 - 3x + 2` renders a real graph (PNG).
- **Practice mode** — `/practice` generates random questions with
  reveal-on-click answers.
- **Hinglish input** — e.g. `5 aur 3 ko jodo`, `240 ka 15 pratishat`,
  `2, 4, 6 ka ausat`, `sin 30 ka maan`.
- **Pretty maths** — MathJax rendering in the web UI.
- Three interfaces: web UI, REST API (`POST /api/solve`), and a CLI.

## Topics covered

| Area | Examples |
|---|---|
| Arithmetic, fractions, percentages | `2+2*5` · `3/4 + 1/2` · `15% of 240` |
| Algebra | `2x + 3 = 7` · `x^2 - 5x + 6 = 0` · `x + y = 10 and x - y = 4` · `2x + 3 > 7` · `factor x^2 - 5x + 6` · `expand (x+2)(x+3)` · `simplify (x^2-1)/(x-1)` |
| Exponents & logarithms | `log base 2 of 32` · `log2(32)` · `solve 2^x = 32` |
| Trigonometry | `sin 30` · `cos(pi/3)` · `prove sin^2(x) + cos^2(x) = 1` · `solve sin(x) = 1/2` · `arcsin(0.5)` (bare numbers = degrees) |
| Calculus | `limit x->0 of sin(x)/x` · `derivative of x^3 + 2x` · `partial derivative of x^2*y with respect to y` · `find dy/dx for x^2 + y^2 = 25` · `integrate x^2 from 0 to 1` · `solve dy/dx = 2x` |
| Linear algebra | `determinant of [[1,2],[3,4]]` · `inverse of ...` · `eigenvalues of ...` · `rank of ...` · `multiply [[..]] and [[..]]` · `A=[[2,1],[1,3]], b=[[5],[10]]` |
| Geometry | `area of circle with radius 5` · `volume of sphere with radius 3` · `perimeter of rectangle ...` · Heron's formula |
| Coordinate geometry | `distance between (1,2) and (4,6)` · `midpoint of ...` · `slope ...` · `equation of line through (1,2) and (3,6)` · `equation of circle with centre (1,2) and radius 3` |
| Statistics | `mean/median/mode of ...` · `standard deviation of ...` · `variance of ...` · `range of ...` |
| Probability & counting | `probability of getting a 6 on a dice` · `probability of sum 7 with two dice` · `probability of exactly 2 heads in 3 coin tosses` · balls-in-a-bag · cards · binomial `exactly 3 successes in 10 trials with p = 0.5` · `P(5,2)` · `C(5,2)` · `factorial of 5` |
| Number theory | `is 97 prime?` · `factor 360` · `gcd of 12 and 18` · `lcm of 4 and 6` · `17 mod 5` · `is 144 divisible by 12` |
| Sequences & series | `10th term of AP 2, 5, 8` · `sum of first 10 terms of AP 2, 5, 8` · `5th term of GP 3, 6, 12` · `sum of first 10 natural numbers` (also squares/cubes) |
| Complex numbers | `(2+3i)*(1-i)` · `modulus of 3+4i` · `conjugate of 3+4i` · `argument of 1+i` |
| Sets | `{1,2,3} union {3,4,5}` · `{1,2,3} intersection {2,3,4}` · difference · symmetric difference |
| Unit conversion | `convert 5 km to miles` · `convert 2 kg to grams` · `convert 37 celsius to fahrenheit` · length, mass, time, volume, area, temperature |
| Word problems | `increase by 15% of 240` · `60 km/h for 2 hours` · `sum is 10 and product is 21` · `simple interest on 1000 at 5% for 2 years` |
| Graphs | `plot x^2 - 3x + 2` · `graph sin(x)` |

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

Tests and a full end-to-end check (80 sample questions, one per feature):

```bash
pytest            # 23 tests
python verify_all.py
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
app.py                  Flask app (/, /solve, /practice)
api.py                  JSON API blueprint (/api/solve)
cli.py                  Command-line interface
solver/
  router.py             Hinglish normalisation + topic routing + fallback
  expression_parser.py  parse_expression (the SymPy parsing core), helpers
  arithmetic.py         expressions, fractions, percentages (+ BODMAS steps)
  algebra.py            equations, systems, inequalities, factor/expand/simplify
  exponents_logs.py     logarithms and exponential/log equations
  calculus.py           limits, derivatives (partial/implicit), integrals, ODEs
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
  plotting.py           matplotlib graph generation
  practice.py           random practice-question generator
templates/, static/     Jinja templates and CSS (graphs land in static/graphs/)
test/                   pytest suite
verify_all.py           end-to-end verification script (not part of the app)
```

## Notes & honest limits

- Trigonometry treats a bare number as **degrees** (`sin 30` = 1/2) unless
  the question mentions radians or uses `pi`.
- Standard deviation is the **population** standard deviation.
- Differential equations cover basic first-order forms (`dy/dx = ...`).
- The solver understands common phrasings; very free-form word problems
  outside the listed patterns may not parse — the answer page then says so
  instead of guessing.
