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
- **🧒 Mera Saathi (Wave 6)** — a friendly optional companion:
  on the first visit a small card asks *"Tumhara naam kya hai?"*
  — the student can enter a first name (and optionally a class),
  or skip it and keep using everything. Once set, the chat
  welcome bubble greets the student by name, the header shows a
  small "🧒 Name · Class 8" pill with an Edit option, and quiz
  remarks speak to the student personally. The tone is always
  encouraging, never scolding: after wrong answers and on the
  friendly error card, Ganitra says the localised version of
  *"Koi baat nahi — galti se hi seekhte hain, ek baar phir try
  karo!"* The name is cleaned before it is stored (tags stripped,
  30-character cap, escaped again on render). There is **no
  login and no database**: the profile lives in the Flask
  session and is mirrored in the browser's `localStorage`.
  **Wave 10 supersedes this for the homepage:** the chat now
  sits behind a real account sign-in (next bullet), and the
  account itself supplies the Saathi name + class — the
  first-visit card no longer renders for signed-in students.
  The `/saathi` endpoint and the localStorage mirror remain
  for the other pages' personalisation.
- **🔐 Real sign-in first page (Wave 10)** — the chat opens
  only after sign-in, exactly as designed and approved by the
  user: ONE page, ONE warm background, the frozen logo blended
  in at the top, and **every field type-in** (no option chips
  anywhere — the student writes everything himself): name,
  class (text; accepts "8", "Class 8", "8th", must be 6–12),
  board (free text, mapped to the Board Mode slug), a
  gold-tinted **"Your 3 Favourite Things"** card (My Goal, My
  Hobby, My Favourite) with the password inside it, and a teal
  **Create my account** button. Returning students use
  **Welcome back** (name + password). The favourite-things
  login card stays **hidden until "Forgot password?" is
  tapped** (the user's explicit refinement); then the student
  types ANY ONE of his 3 favourite things plus a NEW password
  and is logged in with the password reset in the same step.
  Accounts live in **SQLite** (`accounts.py`, stdlib only):
  passwords AND favourite answers are stored as salted
  **PBKDF2-HMAC-SHA256** hashes — never plaintext. Sign-up
  also sets the Mera Saathi session (name + class) and the
  board session, so personalisation and Board Mode work
  immediately; **Log out** sits in the chat ☰ menu. After 8
  failed login attempts for a name in one session, that name
  is locked out with a friendly "try later" message.
  **Honest limits:** (1) Render's free filesystem is
  **ephemeral** — the SQLite file (path from
  `GANITRA_DB_PATH`, default `ganitra_users.db` beside the
  app) is wiped on redeploy/restart, so **accounts are
  per-deployment until a hosted database is added**;
  (2) names are the login key, so a second student with the
  **exact same name** cannot register under it — sign-up
  shows a friendly error asking him to add something to the
  name (e.g. "Aarav S.") and never overwrites the first
  account; (3) the gate applies to **`/` (the chat home)
  only** — `/solve`, `/board`, `/topics` and the other pages
  keep their previous behaviour.
- **🗂️ Many chats, like browser tabs (Wave 11)** — a signed-in
  student can keep **many chats at once**, in the style the
  user approved from his own Brave-browser screenshot. The
  chat top bar no longer shows the name–class pill (the name
  still greets him in the empty state, which is now just the
  logo + greeting — the "Type it, speak it…" line is gone);
  at the **far right edge** sits a plain **+** sign (no circle)
  that opens the **all-chats view**: a chats-count chip and a
  grid/list toggle on top, a **"Search your chats"** bar that
  really filters the cards by title/first question, the chats
  as a **2-column grid of preview cards** (mini logo + title +
  ✕ close with a confirm, and a preview body with the first
  question and first answer; the currently-open chat's card
  is marked), a **big blue + button** bottom-centre that
  creates and opens a new chat, and a **⋮ menu** holding
  "Close all chats" (with a confirm). The composer gained a
  **📎 file-select button on the LEFT inside the pill** — it
  opens the same picker/input as the 📷 camera button (same
  OCR flow); all four composer controls are clean line-style
  SVG icons in the site teal. In the empty state the composer
  sits directly under the greeting; once chatting starts it
  stays pinned to the bottom. **Chats are stored per
  account, server-side**, in the same SQLite file as the
  accounts (a `chats` table via `chats.py`; JSON endpoints
  `GET/POST /api/chats`, `GET/PUT/DELETE
  /api/chats/<id>`, `DELETE /api/chats`, every query scoped
  to the signed-in user) — so a student's chats now **follow
  his account across devices**, replacing the earlier
  per-browser behaviour for the chat page. The classic
  `/solve`, photo and other flows are unchanged.
- **💬 Pure chat screen (Wave 7)** — the homepage is now
  *only* a chat, ChatGPT-style (the landing-style front was
  rejected by the user): a slim top bar (Ganitra brand, the
  Saathi pill, a compact Dhyaan pill, the language switch and
  one ☰ menu linking Board Mode, Practice, Mistakes, History,
  For Parents and Topics), the message thread in the middle,
  and the composer **fixed at the bottom** of the viewport —
  one rounded bar with the auto-growing textarea, 🎤 mic and
  📷 photo buttons inside it, and a round ➤ send button. No
  hero, no marketing sections, no topic grid on the home page:
  the topic list and "How it works" moved to their own page,
  **`/topics`**. The empty state is just a centred greeting
  (personalised with the Saathi name when set) plus one short
  line, with the small Mera Saathi card inside it on a first
  visit. Chat behaviour fixes from a real phone report ("kaam
  nahi kar raha, bas normal dikh raha hai"): after sending,
  the thread **auto-scrolls** to the newest answer; a typing
  indicator shows the localised **"Ganitra is thinking…"**
  line with animated dots, and if the wait passes ~6 seconds
  it swaps to the calm server-waking-up note, so a cold start
  never looks like a hang. Also fixed: the Board chapter
  page's **"Chapter test (timed)" button** rendered white text
  on a white button (its `.hero-solve` gold gradient reads
  `var(--gold)`, a variable defined only inside `.hero`, so
  the background was invalid outside the hero) — it now uses
  its own `.board-test-btn` rule with an explicit teal
  background and white text. All other pages keep their
  existing look; the chat layout is scoped to a `chat-page`
  body class.
- **🎨 Final logo (Wave 8)** — Suraj's approved logo is wired
  in, prepared from his own delivered file
  (`Ganitra_Logo_Final.png`, 1920×1020: the dark-teal
  silk-ribbon "G" monogram above the serif word "Ganitra" —
  at his word the "MATHS" line under the name was removed,
  *"maths ko hata do"*). Three web assets live in `static/`:
  `logo-full.png` (900px-wide resize of that final file,
  artwork otherwise untouched), `logo-mark.png` (a tight crop
  of the ribbon-G monogram alone, cropped from the same
  artwork) and `favicon.png` (64×64, the monogram composited
  on the artwork's sampled cream background `#f3ebe0`). Where
  used: the chat homepage's **empty state** shows the full
  logo above the greeting (on its cream tone with soft rounded
  corners, since the page background `#fdfaf3` is close but
  not identical), the **slim chat top bar** shows the mark at
  30px next to the HTML "Ganitra" wordmark (the full lockup is
  not baked into the bar), and **every page** gets the favicon
  via `base.html`. Other pages' headers are unchanged.
- **👨‍👩‍👧 Parent Report (Wave 6)** — `/parent-report` (linked as
  "For Parents" in the nav and footer) builds a calm report
  from data the app already tracks: how many questions are in
  this session's history, today's Dhyaan record (minutes
  studied + questions solved today, read from this browser's
  `localStorage`), the Mistake Notebook (how many questions are
  waiting, and their topics), the last test report (score +
  topics where marks were lost), and a simple **star** summary
  — the rule is stated on the page: **1 star for every 5
  questions in the session history, plus 1 star for each test
  scored at 80% or more**. A **📤 Share on WhatsApp** button
  opens WhatsApp with the same numbers as a short prefilled
  text. Honest scope, also stated on the page: the report
  covers **this device and browser only** (this session + the
  record stored here) — there is no account system yet, so it
  is the child's activity on this phone, not a cloud record.
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
- **Auto language (Wave 9)** 🪄 — the site language stays
  **English by default**, but when a student chats in another
  language the site switches to it **automatically**: ask in
  Hindi, Hinglish ("mujhe ye sawaal samjhao"), Marathi — including
  WhatsApp-style Roman Marathi ("mala ha prashna samjat nahiye,
  sanga na") — Bengali, Tamil or Telugu, and the answer, the
  interface and the voice all follow, with a small "language
  changed" note in the chat. Detection is local and deterministic
  (`langdetect_local.py`: script ranges + curated marker words —
  no external service). The manual language switcher is always
  available and is never fought: auto-switch only reacts to a chat
  message written in a different language.
- **Pretty maths** — MathJax rendering in the web UI.
- Three interfaces: web UI, REST API (`POST /api/solve`), and a CLI.

### Wave 12 — the menu-inside package (10 Nov 2026)

- **Full-page menu** 🎛️ — the ☰ menu on the chat and all-chats
  pages is now a full-screen panel, LinkedIn-style: a **profile
  block** (the student's photo, or the Ganitra mark, plus name,
  "Class N Student", board and "Ganitra Maths") that opens My
  Account; **live stats** ("N questions solved", "N chats" —
  counted from the student's own saved chats, blue numbers);
  bold entries for Your chats, Board Mode, Practice Test, Topics,
  Mistake Notebook, Copy Style, Parent Report; a Language row
  that expands to the six languages; a **Settings** row that
  opens My Account; and a gold strip — *"Keep learning, keep
  shining."* There is deliberately **no History link and no Log
  out in this menu**: Log out lives only inside My Account.
- **My Account (`/account`)** ⚙️ — a simple settings list: change
  the profile photo (PNG/JPEG, max 2 MB, checked by file magic —
  not just the file name), edit Name / Class / Board, replace any
  of the three favourite things, and change the password (the
  current password is required). Saved changes apply everywhere
  at once — the menu stats, the board page and the greeting.
- **More methods + Teach me** 🧮 — every answer still shows ONE
  method first, fully solved. Beside it, small gold chips offer
  **More methods** (only methods that genuinely differ and agree
  with the same answer: factorisation, completing the square and
  the graph method for quadratics; the graph method for linear
  equations; fraction and unitary methods for percentages; a
  bracket-first grouping for multi-step arithmetic), **Listen**,
  and **Teach me** — short teacher-style concept lines for the
  question type (real content in English and Hindi; the other
  four languages fall back to the English lines for now, the same
  precedent as the step text). The classic answer page shows the
  same methods and teaching under the solution.
- **Small polish** — the chat composer is slimmer, the method
  chips are small (13px), the sign-in boxes are plain white, and
  the pages use **transparent logo copies**
  (`logo-full-t.png` / `logo-mark-t.png` — the cream background
  removed) so the logo blends into the page instead of looking
  pasted on. The frozen original logo files are untouched.
- **All devices** 📱💻 — the layout is checked at 360px (small
  Android), 390–430px (iPhone), 768px (tablet) and 1280px+
  (laptop/desktop): no horizontal scroll, the all-chats grid goes
  to 3 columns on wide screens, the full-page menu is a centred
  640px column on desktop, account rows stack on small phones,
  tap targets are at least 44px and inputs at least 16px (the
  iOS zoom guard), and long maths expressions wrap instead of
  overflowing.

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
GANITRA_DB_PATH=/tmp/w10-test.db python verify_wave10.py
                        # wave-10 sign-in system (needs the scratch
                        # DB path; the older wave scripts force their
                        # own /tmp scratch account DBs themselves)
python verify_wave11.py # wave-11 multi-chat system (forces its
                        # own /tmp scratch account DB)
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
                        /solution/print, /set-lang/<code>,
                        /saathi, /parent-report, plus Wave-10
                        sign-in: /signup, /login, /login-favourite,
                        /logout and the login gate on /)
accounts.py             Wave-10 account store: SQLite (stdlib),
                        PBKDF2-hashed passwords + favourite
                        answers, name/class/board helpers
api.py                  JSON API blueprint (/api/solve)
langdetect_local.py     Wave-9 dependency-free chat-language
                        detection (script ranges + marker words)
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
verify_wave6.py         wave-6 verification: Mera Saathi (personal
                        greeting, encouragement, XSS-safe name) and
                        the Parent Report (not part of the app)
verify_wave7.py         wave-7 verification: pure chat homepage
                        (not part of the app)
verify_wave8.py         wave-8 verification: frozen logo wiring
                        (not part of the app)
verify_wave9.py         wave-9 verification: auto language
                        detection/switching (not part of the app)
verify_wave10.py        wave-10 verification: sign-in gate,
                        sign-up/login/favourite-login flows,
                        lockout, no-plaintext storage (run it with
                        GANITRA_DB_PATH=/tmp/w10-test.db)
verify_wave11.py        wave-11 verification: per-account
                        multi-chat API, ownership, header "+",
                        composer icons, all-chats view (own
                        scratch DB)
templates/auth.html     Wave-10 sign-in page (sign-up + Welcome
                        back + hidden favourite-login card)
templates/chats.html    Wave-11 all-chats view (Brave-style chat
                        cards grid + search + blue new-chat button)
chats.py                Wave-11 per-account chat storage (same
                        SQLite file as accounts.py)
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
- **Mera Saathi and the Parent Report are device/session-based
  too**: the Saathi name/class live in the Flask session and in
  this browser's `localStorage` (no account, no server database),
  and the Parent Report is assembled from this session plus this
  browser's stored Dhyaan record — clearing the browser data or
  switching phones starts both from zero. The session history
  behind the report is also capped (30 entries), so the report
  is a friendly family summary, not an official record.
- **Auto-language detection (Wave 9) is heuristic, honestly**:
  questions written in the Bengali, Tamil, Telugu or Devanagari
  scripts are detected solidly (Devanagari Hindi vs Marathi is
  decided by Marathi-only letters/words like ळ / आहे / मला).
  Roman-script detection is strongest for Hinglish and Roman
  Marathi, which have curated marker lists; Roman Bengali, Tamil
  and Telugu are covered conservatively (two or more strong,
  distinctive marker words are required), so a short or unusual
  Roman sentence in those languages may stay in English until the
  student uses the manual switcher. Genuinely mixed Hindi–Marathi
  Roman text prefers Hindi. Pure maths ("x^2-5x+6=0") carries no
  language signal and never triggers a switch. As before, the
  step-by-step working remains in English in every language.
- **Wave 12 limits, honestly**: the profile photo is stored in
  the same SQLite database as the accounts and chats, so it is
  **per-deployment** until a hosted database is added — a fresh
  deploy starts with no photos, exactly like the accounts and
  chats themselves. The three favourite things are **write-only
  secrets**: they are stored hashed and are never displayed
  anywhere, including My Account — a "change" always replaces the
  old one blind. The account **name IS the login id**, so renaming
  in My Account changes the name the student must type at login
  (old-name logins stop working immediately). Multi-method answers
  are honest: a question with only one genuine method (a plain
  "2+2") gets **no** extra methods rather than a dressed-up copy
  of the same working, and every extra method is generated from
  the same question and checked to reach the same answer.
  Teach-me lines are full in English and Hindi; Bengali, Marathi,
  Tamil and Telugu fall back to the English lines until native
  translations are added. The all-device check is verified
  through the test client's HTML and the CSS rules (breakpoints,
  meta tags, size guards), **not on physical devices**.

---

## Wave 13 — Classes 0–12 coverage + more methods

Wave 13 (Suraj's directive, 10 Nov 2026: *"0-12th tak sabhi
question solve hone chahiye"* and *"Question ke method badane
hai"*) widens the solver so every class band's standard
question families solve, and adds genuinely-distinct alternate
methods where they exist. Two new solver modules:
`solver/junior.py` (Classes 0–5) and `solver/applied.py`
(Classes 6–8 applied maths + two Class 9–10 gaps), wired into
the router after all established intents so nothing that
worked before changes its path.

**Coverage by class band**

- **Classes 0–2** — number names ("write 457 in words" →
  "Four hundred fifty-seven", international system, no
  "and"), tables ("table of 7", "7 ka table"), small-number
  commands ("add 245 and 178", "subtract 96 from 250",
  "product of 12 and 5"), add/take-away stories ("Ram has 15
  mangoes. He gives 6 to Sita. How many are left?"), even/odd
  ("is 47 odd or even", including correcting a wrong claim:
  "47 is even" → "47 is odd").
- **Classes 3–5** — place value and expanded form, fraction
  basics ("1/2 of 18", "half of 24", "quarter of 100",
  fraction ↔ decimal, comparing two fractions by
  cross-multiplication), money ("cost of 5 pens at Rs 12
  each", change-making stories), clock maths ("45 minutes
  after 3:30", "from 2 pm to 5 pm how many hours"), unit
  conversions ("convert 3 km into metres", "5 kg = how many
  grams", hours↔minutes, days↔weeks, months↔years), shape
  facts ("how many sides does a hexagon have", "name the
  shape with 3 sides"), perimeter/area of square and
  rectangle in plain words, sequences ("next number: 2, 4, 6,
  8, ?", missing middle number, odd numbers between),
  multiples ("multiples of 6 up to 30", "first 5 multiples
  of 6"), prime numbers between two numbers. "Factors of 12"
  keeps its established prime-factorisation answer, and
  HCF/LCM route to the number-theory solver as before.
- **Classes 6–8** — ratio (simplify, "ratio of 20 to 45",
  divide an amount in a ratio, two numbers in a ratio with
  a given sum), the unitary method ("5 pens cost Rs 60,
  cost of 8 pens"), simple interest in every NCERT phrasing
  (Rs amounts, months converted to years, SI + amount),
  profit & loss with profit/loss percent, speed–distance–
  time stories plus km/h ↔ m/s conversion, and simple
  linear word equations ("a number increased by 7 is 15",
  "twice a number is 26").
- **Classes 9–10** — discriminant and nature of roots of a
  quadratic (new in Wave 13); AP/GP nth term and sums,
  coordinate geometry (distance, midpoint, slope),
  mensuration (circle, sphere, cylinder, cone, cube, square,
  rectangle, triangle) and mean/median/mode were already
  covered by earlier solvers and are unchanged.
- **Classes 11–12** — calculus, matrices, trigonometry,
  probability and distributions from earlier waves,
  unchanged.

**New alternate methods (Wave 13)** — every alternate is
computed independently and only shown when its answer equals
the primary answer:

- Linear equations: **transposition** (move terms across
  `=` with sign change), alongside the existing graph
  method — up to 3 methods total.
- Percentage: **proportion** (x/base = pct/100,
  cross-multiply) — up to 4 methods total.
- Simple interest: **year-by-year breakup** (one year's
  interest × number of years).
- HCF: **Euclid's division**; LCM: **via the HCF relation**
  (a × b = HCF × LCM).
- Distance between points: **graph method** (the two points
  plotted, legs Δx/Δy drawn and read as a right triangle).
- Triangle area: **half of a rectangle** reasoning.
- AP/GP nth term (n ≤ 12): **writing out the terms**.
- Mean (≥ 4 numbers): **assumed mean method**.
- Two candidates were deliberately **not** added: a
  profit-percent "per Rs 100" alternate and a rectangle-area
  alternate — neither is a genuinely distinct school method,
  and the honesty rule prefers no method over a dressed-up
  copy.

**Honest limits (Wave 13)**

- Word-problem solving is **pattern-based**, not general
  language understanding. The recognised story patterns are:
  has→gives/loses away (subtraction), has→gets/buys more
  (addition), money spent with left/change asked, groups with
  "each"/"in all" (multiplication), sharing equally
  (division), and the value commands listed above. A story
  outside these patterns falls through to the existing
  friendly "couldn't solve" card — it never receives a
  guessed answer.
- Coverage means the standard question *families* of each
  class band, not arbitrary textbook prose: theorem proofs,
  constructions, "show that" questions and multi-step
  reasoning chains are out of scope for a step solver.
- Mensuration uses π = 3.14159 in the geometry solver (the
  junior fallback patterns mirror the same value); answers
  are rounded the way the existing solvers round.
- Steps for all new solvers are in English, like every other
  solver; the explanation line, teacher's advice and Teach-me
  lines cover the new types (Teach-me in English and Hindi,
  other languages fall back to English as documented).
- `verify_wave13.py` guards this wave: a coverage battery of
  90+ sample questions across all five class bands, a
  methods battery asserting every new alternate agrees with
  its primary answer, a gibberish fuzz check (no fabricated
  answers from the new types), and the i18n completeness of
  the new keys in all 6 languages.
