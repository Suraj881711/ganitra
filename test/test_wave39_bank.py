"""Wave 39: the Verified Data Bank exact-match layer.

The bank (bank.py + the bank_data.jsonl snapshot shipped with
the app) serves a question ONLY on an exact normalised match —
every banked answer was independently SymPy-verified before
banking. Pinned here:

- exact EN and Hindi questions hit through the real fallback
  seam, shaped like a normal result (Wave 24 house style) and
  flagged fallback_kind="bank" / source="bank" / verified=True;
- a banked question the solver cannot really answer is served
  by the bank end-to-end (api._solve_friendly), while a real
  solver answer is never shadowed by the bank;
- the same question asked "as another class" still hits
  (class-agnostic index);
- a paraphrase and a number-changed question MISS and fall
  through to the old flow untouched;
- a missing bank snapshot never breaks the app;
- a science question is still refused by the science guard —
  the bank is never consulted for it, even if it would match.
"""
import json
import os
import shutil
import subprocess
import sys

import bank
import fallback
from api import _solve_friendly
from fallback import with_fallback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

COINS_Q = ("Two coins are tossed simultaneously. What is the "
           "probability of getting at most one head?")
HINDI_Q = ("दो रेलगाड़ियाँ एक ही स्टेशन से एक साथ निकलती हैं। "
           "पहली रेलगाड़ी हर 12 मिनट में और दूसरी हर 18 मिनट में "
           "स्टेशन से छूटती है। वे अगली बार कितने समय बाद एक "
           "साथ छूटेंगी?")
PHYSICS_Q = ("A ray of light travels from medium A to medium B. "
             "The refractive index of medium B relative to "
             "medium A is 1.5, and the speed of light in medium "
             "A is 2 x 10^8 m/s. What is the speed of light in "
             "medium B?")

FAILED = {"type": "solver", "op": "error",
          "answer": "Could not solve this one: test", "steps": []}


def _record(question):
    """The snapshot's own record for a question — expectations
    come from the data file, not from bank.py internals."""
    with open(os.path.join(ROOT, "bank_data.jsonl"),
              encoding="utf-8") as fh:
        for line in fh:
            item = json.loads(line)
            if item.get("question") == question:
                return item
    raise AssertionError(f"question not in snapshot: {question!r}")


def test_exact_english_hit():
    record = _record(COINS_Q)
    result = with_fallback(COINS_Q, dict(FAILED))
    assert result.get("fallback_kind") == "bank"
    assert result.get("source") == "bank"
    assert result.get("verified") is True
    assert result.get("answer") == record["final_answer"]
    assert result.get("steps") == record["steps"]


def test_exact_hindi_hit():
    record = _record(HINDI_Q)
    result = with_fallback(HINDI_Q, dict(FAILED))
    assert result.get("fallback_kind") == "bank"
    assert result.get("answer") == record["final_answer"]
    assert "36" in result["answer"]
    assert result.get("steps") == record["steps"]


SHOP_Q = ("A shopkeeper sells 11 notebooks for ₹22 each and "
          "7 pens for ₹33 each. He then gives a discount of ₹44 "
          "on the total bill. Find the final amount to be paid "
          "using the expression (11 * 22) + (7 * 33) - 44.")


def test_end_to_end_bank_hit_via_solve_friendly():
    # A banked question the solver itself can only meet with a
    # salvaged fragment is served by the bank instead, end to
    # end through the real chat path.
    record = _record(SHOP_Q)
    result = _solve_friendly(SHOP_Q)
    assert result.get("fallback_kind") == "bank"
    assert result.get("verified") is True
    assert result.get("answer") == record["final_answer"]


def test_solver_real_answer_not_shadowed():
    # The two-coins question is banked AND exactly solved by
    # the solver (Waves 31-33 guards pin its solver output):
    # a real solver answer is served untouched — the bank only
    # upgrades questions the solver could not really answer.
    result = _solve_friendly(COINS_Q)
    assert result.get("fallback_kind") != "bank"
    assert str(result.get("answer", "")).startswith("3/4")


def test_same_question_other_class_still_hits():
    record = _record(COINS_Q)
    assert record["class"] == 10
    # Asked "as" a Class 6 student: the class-aware index
    # misses, the class-agnostic index still serves the item.
    assert bank.lookup(COINS_Q, student_class=6)["id"] == record["id"]
    assert bank.lookup(COINS_Q, student_class=10)["id"] == record["id"]
    assert bank.lookup(COINS_Q)["id"] == record["id"]


def test_normalisation_variants_still_hit():
    messy = ("  two   coins are tossed simultaneously,   what is "
             "the probability of getting at most one head ")
    assert bank.lookup(messy) is not None
    assert bank.lookup(COINS_Q.upper()) is not None


def test_number_changed_question_misses():
    changed = ("Three coins are tossed simultaneously. What is "
               "the probability of getting at most one head?")
    assert bank.lookup(changed) is None
    result = with_fallback(changed, dict(FAILED))
    assert result.get("fallback_kind") != "bank"


def test_paraphrase_misses():
    paraphrase = ("Two coins are tossed together. Find the "
                  "probability of getting at most one head.")
    assert bank.lookup(paraphrase) is None
    result = with_fallback(paraphrase, dict(FAILED))
    assert result.get("fallback_kind") != "bank"


def test_missing_bank_file_does_not_break_app(tmp_path):
    # bank.py alone in an empty folder (no bank_data.jsonl
    # beside it): imports cleanly, bank is empty, lookups miss.
    shutil.copy(os.path.join(ROOT, "bank.py"), tmp_path / "bank.py")
    code = ("import bank\n"
            "print(bank.bank_size())\n"
            "print(bank.lookup('What is 2 + 2?'))\n")
    out = subprocess.run([sys.executable, "-c", code],
                         cwd=tmp_path, capture_output=True,
                         text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines() == ["0", "None"]


def test_empty_bank_falls_through_to_old_flow(monkeypatch):
    monkeypatch.setattr(bank, "_BY_QUESTION", {})
    monkeypatch.setattr(bank, "_BY_CLASS", {})
    result = with_fallback(COINS_Q, dict(FAILED))
    assert result.get("fallback_kind") != "bank"


def test_science_question_still_refused():
    result = _solve_friendly(PHYSICS_Q)
    assert result.get("fallback_kind") == "science"


def test_science_guard_runs_before_bank(monkeypatch):
    # Even if the bank COULD match a science question, the
    # guard wins: the bank layer is never consulted for it.
    fake = {"type": "Ganitra", "op": "bank", "answer": "fake",
            "steps": [], "fallback": True,
            "fallback_kind": "bank", "source": "bank",
            "verified": True}
    monkeypatch.setattr(bank, "lookup_result", lambda q, c=None: fake)
    result = with_fallback(PHYSICS_Q, dict(FAILED))
    assert result.get("fallback_kind") == "science"


def test_house_style_shape():
    record = _record(COINS_Q)
    result = bank.bank_result(record)
    for key in ("type", "op", "answer", "steps"):
        assert key in result
    # Plain solving lines only — no "Step 1:" style labels —
    # and the final answer rides as one normal answer line.
    for line in result["steps"]:
        assert not line.lower().startswith(("step ", "step:"))
    assert result["answer"] == record["final_answer"]
