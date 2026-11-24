"""Wave 222 — unit conversion, jad se (DeepSeek Job 3).

Bug (live checker, ChatGPT Jobs A/B/C, 23 Nov 2026):
"3 ghante me kitne minute" was served "0 hours 3 minutes"
(sahi: 180), and the composite rendering glued its parts
("0 hours3 minutes").  ROOT CAUSE: the minutes<->hours
block in solver/wave212.py's _time_calendar fired on ANY
one-number question naming both a minute-word and an
hour-word and unconditionally treated the number as
MINUTES — it never read the direction from the unit the
number is attached to.  Every Hinglish dress of the other
families ("2.5 kg ko gram me badlo") had no path at all
and errored in the expression parser.

Fix: solver/unitconvert.py reads a conversion
STRUCTURALLY — a quantity glued to its source unit plus
exactly one other unit of the same category — computes
exactly with Fractions, and answers in the student's own
unit words.  The router tries it before the Wave 212
gate and Wave 212's broken block delegates to it.  These
tests pin the reported failure, both directions of all
four families in English and Hinglish, decimal / fraction
/ word quantities, the glued-rendering defect, and the
foreign shapes the converter must never touch.
"""
import re

import pytest

from solver.router import solve_question
from solver.unitconvert import solve_unitconvert
from solver.wave212 import solve_wave212


def _full_text(result):
    parts = [str(result.get("answer") or "")]
    parts += [str(s) for s in result.get("steps") or []]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The reported failure, through every path that can serve it
# ---------------------------------------------------------------------------

def test_reported_failure_full_pipeline():
    r = solve_question("3 ghante me kitne minute")
    assert r is not None
    assert r["answer"] == "180 minute"
    text = _full_text(r)
    assert "1 ghanta = 60 minute" in text
    assert "3 ghante = 3 × 60 = 180 minute" in text
    assert "0 hours" not in text


def test_reported_failure_wave212_delegation():
    # Direct solve_wave212 calls (fallback repair hooks use
    # them) must be fixed too — the broken block delegates.
    r = solve_wave212("3 ghante me kitne minute")
    assert r is not None
    assert r["answer"] == "180 minute"


def test_reported_failure_chat_path():
    from api import _solve_friendly
    r = _solve_friendly("3 ghante me kitne minute")
    assert r is not None
    assert "180" in str(r.get("answer"))
    assert "0 hours" not in str(r.get("answer"))


# ---------------------------------------------------------------------------
# Both directions, all four families, English + Hinglish
# ---------------------------------------------------------------------------

CASES = [
    # time: hours <-> minutes
    ("3 ghante me kitne minute", "180 minute"),
    ("3 ghante me kitne minute hote hain", "180 minute"),
    ("2 ghante kitne minute hote hain", "120 minute"),
    ("2 hours in minutes", "120 minutes"),
    ("90 minute ko ghante me badlo", "1.5 ghante"),
    ("75 minute ko ghante me badlo", "1.25 ghante"),
    ("90 minutes in hours", "1.5 hours"),
    ("180 minuts me kitne hours hote h", "3 hours"),
    # time: minutes <-> seconds, hours <-> seconds, days
    ("2 minute me kitne second", "120 second"),
    ("3600 second kitne ghante hote hain", "1 ghanta"),
    ("1 ghante me kitne second", "3600 second"),
    ("3 din me kitne ghante", "72 ghante"),
    # length
    ("1.5 km me kitne meter", "1500 m"),
    ("250 cm me kitne metre", "2.5 m"),
    ("45 mm ko cm me badlo", "4.5 cm"),
    ("2 metres ko mm me badlo", "2000 mm"),
    # mass
    ("2.5 kg ko gram me badlo", "2500 g"),
    ("2500 gram kitne kg hote hain", "2.5 kg"),
    # volume
    ("3 litre me kitne ml", "3000 ml"),
    ("1500 ml ko litre me badlo", "1.5 litres"),
    # Devanagari dress
    ("३ घंटे में कितने मिनट", "180 मिनट"),
]


@pytest.mark.parametrize("question,want", CASES)
def test_conversion_cases(question, want):
    r = solve_question(question)
    assert r is not None, question
    assert r["answer"] == want, (question, r["answer"])
    # The working must be genuine: a unit fact and the
    # actual multiplication / division — never a self-echo.
    text = _full_text(r)
    assert "Evaluate:" not in text
    assert ("×" in text) or ("÷" in text)


# ---------------------------------------------------------------------------
# Decimal, fraction and word quantities
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question,want", [
    ("1.5 ghante me kitne minute", "90 minute"),
    ("1/2 ghante me kitne minute", "30 minute"),
    ("dedh ghante me kitne minute", "90 minute"),
    ("dhai kg kitne gram hote hain", "2500 g"),
    ("aadha litre me kitne ml", "500 ml"),
])
def test_quantity_forms(question, want):
    r = solve_question(question)
    assert r is not None, question
    assert r["answer"] == want, (question, r["answer"])


def test_word_quantity_ek():
    # The converter itself reads "ek" as 1...
    r = solve_unitconvert("ek ghante me kitne minute "
                          "hote hain")
    assert r is not None
    assert r["answer"] == "60 minute"
    # ...while the full pipeline may first translate this
    # dress to English, where the standing unit-fact serve
    # ("60 minutes") is equally correct.
    r2 = solve_question("ek ghante me kitne minute "
                        "hote hain")
    assert r2 is not None
    assert r2["answer"].startswith("60 minute")


# ---------------------------------------------------------------------------
# The glued-rendering defect can never come back: no served
# answer or step may glue a unit word to a digit.
# ---------------------------------------------------------------------------

_GLUED = re.compile(r"(hours|hour|minutes|minute|ghante|"
                    r"ghanta|seconds|second)\d|\d(hours|"
                    r"minutes|ghante|seconds)")


@pytest.mark.parametrize("question,want", CASES)
def test_no_glued_rendering(question, want):
    r = solve_question(question)
    assert r is not None, question
    text = _full_text(r)
    assert not _GLUED.search(text), (question, text)
    assert "0 hours 3 minutes" not in text
    assert "0 hours3 minutes" not in text


# ---------------------------------------------------------------------------
# Direction is read, never guessed: the old block's exact
# wrong serves are pinned as impossible.
# ---------------------------------------------------------------------------

def test_direction_never_guessed():
    r = solve_question("2 hours in minutes")
    assert r["answer"] == "120 minutes"
    r = solve_question("2 ghante kitne minute hote hain")
    assert r["answer"] == "120 minute"
    r = solve_question("1.5 ghante me kitne minute")
    assert r["answer"] == "90 minute"


# ---------------------------------------------------------------------------
# Foreign shapes: the converter itself must decline — stories,
# SDT, composite times, sharing, percent and non-maths keep
# their own owners.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "car travels 60 km in 2 hours, find speed",
    "train 60 km/h ki speed se 3 ghante me kitna distance "
    "jayegi",
    "2 hours 30 minutes in seconds",
    "8.4 kg sugar ko 4 dabbo mein barabar bharna hai",
    "a rope is 5 m long, cut into 50 cm pieces, how many "
    "pieces",
    "50% of 2 hours in minutes",
    "what is photosynthesis",
    "5 + 3 kitna hoga",
])
def test_foreign_shapes_declined(question):
    assert solve_unitconvert(question) is None, question


# ---------------------------------------------------------------------------
# Spelled-out English numbers stay with their owner: the
# deep-solve "numbers" rescue serves "How many minutes are
# there in two hours?" — the converter must not pre-empt
# it, and the student must still get 120.
# ---------------------------------------------------------------------------

def test_english_word_numbers_not_preempted():
    assert solve_unitconvert(
        "How many minutes are there in two hours?") is None
    from fallback import fallback_answer
    r = fallback_answer("How many minutes are there in "
                        "two hours?")
    assert "120" in str(r.get("answer"))


# ---------------------------------------------------------------------------
# Wave 221 guard: the arithmetic with-working serve is
# untouched by this wave.
# ---------------------------------------------------------------------------

def test_wave221_guard_unchanged():
    r = solve_question("502 - 178")
    assert r is not None
    assert r["answer"] == "324"
    text = _full_text(r)
    assert "borrow" in text
    assert "502 - 178 = 324" in text
    assert "Evaluate:" not in text
