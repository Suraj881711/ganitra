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
- **Chat homepage** 💬 — the home page is a chat: ask a question and
  the answer appears right there as a conversation (your question on
  the right, Ganitra's answer — with collapsible step-by-step working
  — on the left), so follow-up questions stay in one thread. Enter
  sends, Shift+Enter adds a line, and there is a calm "Solving…"
  indicator while it works. It is progressively enhanced: with
  JavaScript the chat uses the JSON API in place; without it, the
  same form simply opens the classic full answer page.
- **Student-proofing (Wave 5b)** 🛟 — *"student ko koi problem nhi
  honi chahiye"*: if a question can't be solved, the student never
  sees a raw error or a JSON dump — the answer page and the chat
  show a gentle localised card (all 6 languages) saying what likely
  went wrong, with three tips (check for a typing mistake, write
  powers as `x^2`, one question at a time) and a **↻ Try again**
  button. The chat renders the same card as a Ganitra bubble with a
  Retry button that resends the same question. A soft note under
  the chat input warns that the first answer can take a moment
  (the free server wakes up). Empty questions get a friendly
  prompt (no crash), questions over ~500 characters get a friendly
  "a bit long" note, and word-salad input (e.g. `asdf qwer zxq`,
  which the solver would otherwise "simplify" into a meaningless
  letter product) is recognised and treated as unsolvable —
  while real symbolic simplifies like `x + y` or `2x + 3x` still
  solve normally. Empty pages (history, mistakes, practice sets)
  show friendly localised empty-state text. Comfort audit: input
  text is ≥ 16 px (no iOS zoom), tap targets are ≥ 44 px, answer
  text line-height is ≥ 1.6, and there is no horizontal scrolling
  at 360 px width.
- **✍️ Copy Style — handwriting-style steps (Wave 5d)** — the
  step-by-step solution is presented **like a teacher's
  hand-written copy**: the steps render in the **Kalam** handwriting
  font (Caveat as fallback) on a notebook page — ivory paper,
  faint ruled lines and a soft pink margin line, with extra
  line-height and letter spacing. It is a handwriting-style
  *presentation* of the same solver steps (the text is unchanged,
  and MathJax expressions keep their normal rendering). The style
  is **ON by default** on the answer page and in chat bubbles; the
  "✍️ Copy Style (handwriting)" toggle switches back to the clean
  printed style, and the choice is remembered in `localStorage`.
  The answer page also has a "Print in copy style" link that opens
  the print page with `?style=hand`, so the saved PDF keeps the
  notebook look.
- **📋 Copy Check (Wave 5e)** — after a timed quiz or a chapter
  test, the result page shows a **board-style copy-check card**
  like a teacher checking your answer copy: your marks
  (`7 / 10` style), a warm teacher remark chosen by score band
  (perfect / great / good / keep going / try again), the
  per-question ✓/✗ list with the correct answers for the wrong
  ones, and a line naming the topics or chapters **where marks
  were lost**, with a link to practise them (the Mistake
  Notebook). Honest scope: the copy check looks at your **final
  answers** and where marks were lost by topic — it does **not**
  judge handwriting or step presentation. The last test report is
  kept in the session for the result page.
- **🧘 Dhyaan meter + 🎉 Badhai (Wave 5e)** — a small calm pill in
  the header shows **today's study record**: minutes spent on
  Ganitra today (counted while a page is open and visible) and
  questions solved today, stored only in your browser's
  `localStorage` and reset each calendar day. And when you score
  **80% or more** on a quiz/test, or finish a Mistake Notebook
  practice round, a gentle **Badhai** card celebrates with a
  light pure-CSS confetti burst (no library, no sound, and it
  respects `prefers-reduced-motion`).
- **Board Mode** 📚 — `/board`: pick a board (CBSE, ICSE, MP Board,
  Rajasthan Board, UP Board, or Other State Board) and a class
  (6–12), then open any **NCERT maths chapter** for untimed practice
  or a **timed chapter test** (5 questions, 150 seconds,
  server-checked score) built from the chapter's topic.
- **Mistake Notebook** 📒 — `/mistakes`: questions you get wrong in
  the timed quiz or a chapter test are saved here (newest first,
  with the correct answer) so you can practise exactly those again.
- **Teacher's Advice** 👩‍🏫 — under every answer (answer page and
  chat bubble) a small card gives a curated teacher tip for that
  question's topic: the concept to revise, the common mistake
  students make on this type, and a quick practice suggestion.
  Tips are hand-written templates per topic (quadratic, equations,
  trigonometry, calculus, statistics, probability, distributions,
  geometry, sequences, and more, with a generic fallback) in all
  6 languages. Board Mode also shows a rotating **Advice of the
  Day** (7 tips, one per weekday).
- **🔊 Suno — step-by-step audio samjhaya** — the "🔊 Suno" button
  on the answer page and in every chat answer reads the solution
  aloud like a teacher, in order: **the question → each step one
  by one → the final answer → the Teacher's Advice**. Maths
  symbols are cleaned up before speaking (`x^2` → "x squared",
  `*` → "multiplied by", `/` → "divided by", `√` → "square root
  of", `=` → "equals", with per-language words for all six
  languages). While it plays, the button becomes "⏸ Ruko / Stop"
  and clicking it stops the voice; it resets when the queue ends.
  The question, answer and advice are spoken in the UI language;
  **the steps are spoken in English** (the steps themselves are in
  English, as noted above). It uses the browser's built-in
  `speechSynthesis` — voice quality and language support depend
  on the device/browser, and the button hides itself when speech
  is unavailable. (Audio only — there are no video lessons.)
- **History & download** — `/history` lists the questions you solved in
  this session (click to re-open a solution), and every answer page can
  download its step-by-step solution as a `.txt` file, or open a
  clean **print page to save as PDF** (see the honest note below).
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
- **Multi-language UI** 🌐 — the whole interface is available in
  **6 languages**: English, हिन्दी (Hindi), বাংলা (Bengali), मराठी
  (Marathi), தமிழ் (Tamil) and తెలుగు (Telugu). Use the language
  dropdown in the header; the choice is remembered for your session
  (stored server-side, set via `/set-lang/<code>`). Voice input also
  listens in the selected language, and every answer page adds one
  short **explanation line** in the selected language under the
  answer. Honest scope: the UI, voice and that summary line are
  localised — the step-by-step working itself is still shown in
  English (full step translation is future work).
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
app.py                  Flask app (/, /solve, /chat API history,
                        /practice + timed quiz, /board Board Mode,
                        /mistakes, /history, /download,
                        /solution/print, /set-lang/<code>)
api.py                  JSON API blueprint (/api/solve)
board_data.py           NCERT chapter lists for Classes 6-12, each
                        chapter mapped to a practice topic
board_quiz.py           chapter-test generators for the topics
                        solver/practice.py does not cover (sequences,
                        probability, calculus, linear algebra,
                        geometry); delegates to it for the rest
i18n.py                 UI strings + explanation templates in 6 languages
                        (en/hi/bn/mr/ta/te); English is the fallback
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
verify_wave4.py         wave-4 verification: multi-language UI (not part of the app)
verify_wave5.py         wave-5 verification: chat homepage, Board Mode,
                        Mistake Notebook, print/PDF page (not part of the app)
verify_wave5b.py        wave-5b/5d/5e verification: friendly errors,
                        Copy Style (handwriting), Copy Check, Dhyaan
                        meter + Badhai (not part of the app)
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
- Multi-language support covers the interface, the voice-input
  language and a one-line explanation summary on the answer page.
  The step-by-step working is **not** translated yet — it stays in
  English in every language mode. The explanation line is a fixed
  template sentence (per topic/operation) with the final answer
  filled in, not a free-form translation.
- Board Mode chapter lists are the rationalised NCERT lists, and the
  chapter list is NCERT-common across boards — the board choice does
  not change the chapters, because CBSE/ICSE/state-board maths
  chapters for Classes 6–12 are essentially the same list. Each
  chapter's practice/test questions come from the closest matching
  question generator; chapters whose match is only approximate are
  marked "≈" in the UI rather than presented as an exact fit, and
  some chapters (e.g. Symmetry, Sets) currently borrow a neighbouring
  topic's questions until a dedicated generator exists.
- The "Download PDF" button does not generate a PDF on the server —
  it opens a clean print-friendly page and the **browser's own
  Print → Save as PDF** produces the file. That keeps the app free
  of PDF libraries and extra dependencies.
- The Mistake Notebook (like History) is **session-based**: it lives
  in your browser session and clears when the session ends. Student
  accounts with a permanent notebook are a future wave.
- **Copy Style is a presentation, not handwriting generation**: the
  steps are the solver's own text set in a handwriting font on a
  notebook-styled page — nothing is drawn or re-written by hand.
  The Dhyaan meter counts only time with a Ganitra page open and
  visible in this browser, and solves done in this browser; it is
  a gentle study diary, not a proctored record. The Copy Check
  compares final answers only.
