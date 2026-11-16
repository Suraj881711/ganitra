"""Wave 88: Full Paper Mode — attempt a whole stored board
paper like an exam.

Chapter Test (/test, Wave 43) tests 10 generated questions on
one topic. This module is the exam-hall counterpart for the
Previous Papers library (papers_data.py): the student picks a
REAL stored paper, attempts every question in paper order under
the paper's full time, submits (the attempt page auto-submits
when the timer ends), and gets the paper checked.

Public API:
    duration_for(paper, override=None) -> seconds
        The paper's own stored duration when the data carries
        one (checked keys: duration_seconds, duration_minutes,
        time_allowed_minutes — NO stored paper carries any of
        them today, and the Wave 63 sheet omits time for the
        same reason), else the board-standard 3 hours that
        Class 10 and Class 12 Mathematics papers allow (every
        paper in the library is Class 10 or 12).
    duration_label(seconds) -> "3 hours" / "15 minutes" style
        text for the intro and attempt pages.
    attempt_deadline(started_epoch, duration) -> epoch
    classify_question(question) -> kind
        "mcq" | "assertion_reason" | "auto" | "self" — see
        CHECKING HONESTY below.
    grade_attempt(paper, answers) -> {"rows": [...],
                                      "summary": {...}}
        One row per stored question, in paper order.

CHECKING HONESTY (the same contract the rest of the app keeps):
the stored papers carry NO answer key — a question is only
{number, section, marks, chapter, text}. So checking works
like this, per question type:

- MCQ (Section A with printed options): the stem is solved by
  the app's own solver and the computed answer is matched
  against the printed options with the Wave 76 MCQ matchers.
  Settled only when EXACTLY ONE option matches — the student's
  chosen option is then marked correct/wrong for real.
- Short answers (Sections B/C, small marks, no proof wording):
  the solver solves the question (for an OR question, either
  alternative), and the typed answer is compared exactly
  (Fraction arithmetic via test_mode.parse_student_number, so
  "3/4", "0.75" and "6/8" agree; multi-number answers like
  roots compare as a set; unit/Rs dressing is forgiven).
- Everything else — Assertion-Reason items (judging whether R
  explains A is not a computation), proof / "show that" /
  draw / long-answer questions (Sections D and E, or marks
  >= 4), case-study sets, and any question the solver cannot
  settle — is SELF-CHECK: it is never marked correct or wrong
  by the machine. The result page shows the model answer (the
  solver's own worked answer) when the solver can produce one,
  and otherwise tells the student to compare with the marking
  scheme / NCERT solution. Self-check questions never enter
  the auto-checked score and never enter the Mistake Notebook.

The score is therefore stated as "auto-checked score: X of Y
marks", where Y counts only the questions the machine could
actually settle (attempted or not). Wrong AUTO-CHECKED answers
flow into the Mistake Notebook from app.py, like Chapter Test.

Latency: grading solves each checkable question with at most
two budgeted solver calls (the router already caps one call at
SOLVE_BUDGET_SECONDS and caches answers). A soft overall
budget (GRADE_BUDGET_SECONDS) keeps one submit request from
running away: once it is spent, remaining checkable questions
degrade to self-check instead of blocking — the row says so
via its "reason".
"""
import re
import time
from fractions import Fraction

import mcq
import papers_data
from solver.router import solve_question
from test_mode import parse_student_number

# Class 10 / Class 12 board Mathematics standard: 3 hours.
DEFAULT_DURATION_SECONDS = 3 * 60 * 60

# Soft cap on the solver time one grading pass may spend.
GRADE_BUDGET_SECONDS = 150.0

_PROOF_RE = re.compile(
    r"prove|show that|सिद्ध|derive|draw|construct|graphically"
    r"|plot the|graph of", re.IGNORECASE)

_NUM_TOKEN = re.compile(r"[+-]?\d+(?:\.\d+)?(?:\s*/\s*\d+)?")


# ------------------------------------------------------------------
# Duration
# ------------------------------------------------------------------

def duration_for(paper, override=None):
    """Attempt length in seconds for one stored paper."""
    if override is not None:
        try:
            value = int(override)
        except (TypeError, ValueError):
            value = 0
        if value > 0:
            return value
    seconds = paper.get("duration_seconds")
    if isinstance(seconds, (int, float)) and seconds > 0:
        return int(seconds)
    for key in ("duration_minutes", "time_allowed_minutes"):
        minutes = paper.get(key)
        if isinstance(minutes, (int, float)) and minutes > 0:
            return int(minutes * 60)
    return DEFAULT_DURATION_SECONDS


def duration_label(seconds):
    seconds = int(seconds)
    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} hour" + ("s" if hours != 1 else "")
    if seconds % 60 == 0:
        minutes = seconds // 60
        return f"{minutes} minute" + ("s" if minutes != 1 else "")
    return f"{seconds} seconds"


def attempt_deadline(started_epoch, duration):
    return int(started_epoch) + int(duration)


def attempt_remaining(started_epoch, duration, now=None):
    if now is None:
        now = time.time()
    return max(0, attempt_deadline(started_epoch, duration)
               - int(now))


# ------------------------------------------------------------------
# Classification — decided from the stored text alone, no solver
# ------------------------------------------------------------------

def classify_question(question):
    """The checking kind for one stored paper question."""
    text = str(question.get("text", ""))
    if mcq._ASSERTION_RE.search(text) \
            or "assertion" in text.lower():
        return "assertion_reason"
    if mcq.extract_mcq(text) is not None:
        return "mcq"
    if question.get("section") in ("D", "E") \
            or (question.get("marks") or 0) >= 4 \
            or _PROOF_RE.search(text):
        return "self"
    return "auto"


def mcq_options(text):
    """[(label, option_text), ...] for an MCQ question, else
    None (also None for Assertion-Reason items — extract_mcq
    already refuses those)."""
    extracted = mcq.extract_mcq(str(text or ""))
    if extracted is None:
        return None
    return extracted[1]


# ------------------------------------------------------------------
# Bounded solving for grading
# ------------------------------------------------------------------

def _real_result(result):
    """A solver result that really answers, else None — the
    same test papers_data._answer_key_for_generated uses, plus
    the MCQ layer's letter-soup guard."""
    if not isinstance(result, dict):
        return None
    if result.get("op") == "error":
        return None
    answer = result.get("answer")
    if answer is None or not str(answer).strip():
        return None
    if mcq._looks_junk(str(answer)):
        return None
    return result


def _solve_for_check(text):
    """Solve one question text for grading: the text as written,
    then the MCQ layer's cleaned stem — at most two calls into
    solve_question, each already wall-clock budgeted and cached
    by the router. Returns a real result dict or None."""
    candidates = []
    for cand in (str(text), mcq._clean_stem(str(text))):
        cand = cand.strip()
        if cand and cand not in candidates:
            candidates.append(cand)
    for cand in candidates:
        try:
            result = solve_question(cand)
        except Exception:
            continue
        result = _real_result(result)
        if result is not None:
            return result
    return None


def _split_or(text, hindi=False):
    """Split an internal-choice question into its alternatives,
    using the same divider rules as the paper sheet
    (app.py's _paper_q_lines): a plain " OR " split for English
    papers; for Hindi papers अथवा only counts when a labelled
    alternative follows (it is also an ordinary word)."""
    text = str(text)
    if hindi:
        parts = re.split(
            r"\s+अथवा\s+(?=\((?:क|ख|A|B)\)|\((?:iii)\))", text)
    else:
        parts = text.split(" OR ")
    parts = [p.strip() for p in parts if p.strip()]
    return parts or [text]


# ------------------------------------------------------------------
# Answer comparison (exact, Fraction-first)
# ------------------------------------------------------------------

def _clean_num_text(text):
    t = str(text or "").replace("₹", " ").replace("−", "-")
    t = re.sub(r"(?i)\brs\.?\b", " ", t)
    return t


def _numbers_in(text):
    found = []
    for token in _NUM_TOKEN.findall(_clean_num_text(text)):
        try:
            found.append(Fraction(token.replace(" ", "")))
        except (ValueError, ZeroDivisionError):
            continue
    return found


def _norm_text(text):
    t = str(text or "").lower().replace("−", "-")
    t = re.sub(r"[^a-z0-9\u0900-\u097F]+", " ", t)
    return " ".join(t.split())


def answers_match(expected, given):
    """Exact comparison of a typed answer against the solver's
    answer text: whole-number parse first (so "1 1/2" == "3/2"
    and "x = 5" == "5"), then the full number list (roots,
    coordinate pairs), then normalised text."""
    if given is None or not str(given).strip():
        return False
    e, g = str(expected), str(given)
    ef = parse_student_number(_clean_num_text(e))
    gf = parse_student_number(_clean_num_text(g))
    if ef is not None and gf is not None and ef == gf:
        return True
    if ef is not None and gf is not None \
            and str(g).strip().endswith("%") and ef < 1 \
            and gf / 100 == ef:
        return True
    en, gn = _numbers_in(e), _numbers_in(g)
    if en and gn and en == gn:
        return True
    ne = _norm_text(e)
    return bool(ne) and ne == _norm_text(g)


def _given_label(given, options):
    """The option label a student answer names: the letter
    itself ("B", "(b)", "b.") or the option's own text."""
    g = str(given or "").strip()
    if not g:
        return None
    letter = g.strip("()").strip().rstrip(".").strip().lower()
    labels = {label.lower(): label for label, _t in options}
    if len(letter) == 1 and letter in labels:
        return labels[letter]
    for label, text in options:
        if _norm_text(text) and _norm_text(text) == _norm_text(g):
            return label
    return None


# ------------------------------------------------------------------
# Per-question checking
# ------------------------------------------------------------------

def _base_row(paper, question, given):
    return {
        "number": question["number"],
        "section": question["section"],
        "marks": question["marks"],
        "chapter": question.get("chapter", ""),
        "question": question["text"],
        "given": "" if given is None else str(given),
        "status": "self",
        "kind": classify_question(question),
        "expected": "",
        "steps": [],
        "settled": False,
        "reason": "",
    }


def _settle(row, result):
    row["expected"] = str(result.get("answer", ""))
    row["steps"] = [str(s) for s in (result.get("steps") or [])]
    row["settled"] = True


def _check_mcq(row, allow_solve):
    extracted = mcq.extract_mcq(row["question"])
    if extracted is None:
        row["reason"] = "unsettled"
        return row
    stem, options = extracted
    if not allow_solve:
        row["reason"] = "budget"
        return row
    result = _solve_for_check(stem)
    if result is None:
        row["reason"] = "unsettled"
        return row
    matched = mcq._matching_labels(str(result["answer"]), options)
    if len(matched) != 1:
        row["reason"] = "unsettled"
        return row
    label = matched[0]
    _settle(row, result)
    row["expected"] = f"({label}) {dict(options)[label]}"
    if not row["given"].strip():
        row["status"] = "unattempted"
    elif _given_label(row["given"], options) == label:
        row["status"] = "correct"
    else:
        row["status"] = "wrong"
    return row


def _check_auto(row, paper, allow_solve):
    if not allow_solve:
        row["reason"] = "budget"
        return row
    hindi = paper.get("medium") == "hindi"
    solved = []
    for part in _split_or(row["question"], hindi=hindi):
        result = _solve_for_check(part)
        if result is not None:
            solved.append(result)
    if not solved:
        row["reason"] = "unsettled"
        return row
    _settle(row, solved[0])
    if not row["given"].strip():
        row["status"] = "unattempted"
    elif any(answers_match(str(r["answer"]), row["given"])
             for r in solved):
        row["status"] = "correct"
    else:
        row["status"] = "wrong"
    return row


def _model_answer(text):
    """One single budgeted solve_question call, kept light on
    purpose: a model answer for a self-check row is a courtesy,
    not worth the two-call check path."""
    try:
        return _real_result(solve_question(str(text)))
    except Exception:
        return None


def _check_self(row, paper, allow_solve):
    """Self-check rows are never machine-marked; the only job
    here is fetching a model answer (the solver's worked
    answer) when one exists."""
    row["status"] = "self"
    if row["kind"] == "assertion_reason":
        row["reason"] = "assertion_reason"
        return row
    if not allow_solve:
        row["reason"] = "budget"
        return row
    hindi = paper.get("medium") == "hindi"
    for part in _split_or(row["question"], hindi=hindi):
        result = _model_answer(part)
        if result is not None:
            _settle(row, result)
            break
    if not row["settled"]:
        row["reason"] = "no_model_answer"
    return row


def check_question(paper, question, given, allow_solve=True):
    row = _base_row(paper, question, given)
    if row["kind"] == "mcq":
        row = _check_mcq(row, allow_solve)
    elif row["kind"] == "auto":
        row = _check_auto(row, paper, allow_solve)
    else:
        row = _check_self(row, paper, allow_solve)
    if not row["given"].strip() and row["status"] == "self":
        # A blank answer is unattempted whatever the question
        # type — the self-check model answer (if any) still
        # shows, but the count tells the truth.
        row["status"] = "unattempted"
    return row


# ------------------------------------------------------------------
# Whole-paper grading
# ------------------------------------------------------------------

def grade_attempt(paper, answers, budget_seconds=None, clock=None):
    """Grade one full-paper attempt. `answers` is a list of
    typed answers in paper order (missing entries count as
    blank). Returns {"rows": [...], "summary": {...}} — the
    summary states the auto-checked score separately from the
    self-check questions, always."""
    if budget_seconds is None:
        budget_seconds = GRADE_BUDGET_SECONDS
    clock = clock or time.monotonic
    started = clock()
    rows = []
    for i, question in enumerate(paper["questions"]):
        given = answers[i] if i < len(answers) else ""
        allow_solve = (clock() - started) <= budget_seconds
        rows.append(check_question(paper, question, given,
                                   allow_solve=allow_solve))
    counts = {"correct": 0, "wrong": 0, "unattempted": 0, "self": 0}
    score_marks = 0
    checked_marks = 0
    for row in rows:
        counts[row["status"]] += 1
        if row["settled"]:
            checked_marks += row["marks"]
            if row["status"] == "correct":
                score_marks += row["marks"]
    summary = {
        "total_questions": len(rows),
        "total_marks": papers_data.paper_total_marks(paper),
        "score_marks": score_marks,
        "checked_marks": checked_marks,
        "counts": counts,
    }
    return {"rows": rows, "summary": summary}


# ------------------------------------------------------------------
# Attempt page view-model (routes pass the sheet's own helpers
# in, so question text is broken into display lines exactly the
# way the typed paper sheet breaks it — words never change)
# ------------------------------------------------------------------

def attempt_view(paper, q_lines, has_figure):
    hindi = paper.get("medium") == "hindi"
    by_section = {}
    for index, q in enumerate(paper["questions"]):
        by_section.setdefault(q["section"], []).append((index, q))
    sections = []
    for section in papers_data.PAPER_STRUCTURE:
        items = by_section.get(section)
        if not items:
            continue
        items = sorted(items, key=lambda pair: pair[1]["number"])
        questions = []
        for index, q in items:
            kind = classify_question(q)
            questions.append({
                "index": index,
                "number": q["number"],
                "marks": q["marks"],
                "kind": kind,
                "lines": q_lines(
                    q["text"],
                    or_word="अथवा" if hindi else "OR",
                    lower_options=hindi),
                "has_figure": has_figure(q["text"]),
                "options": (mcq_options(q["text"])
                            if kind == "mcq" else None),
            })
        sections.append({
            "section": section,
            "title": papers_data.section_title_for(
                section, [q for _i, q in items]),
            "questions": questions,
        })
    return {"sections": sections}


__all__ = ["duration_for", "duration_label", "attempt_deadline",
           "attempt_remaining", "classify_question", "mcq_options",
           "answers_match", "check_question", "grade_attempt",
           "attempt_view", "DEFAULT_DURATION_SECONDS",
           "GRADE_BUDGET_SECONDS"]
