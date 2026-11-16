"""Wave 95: proof questions ("prove that ..."), honestly tiered.

Before this wave (probe, 16 Nov 2026):
- Algebraic identities ("prove that (a+b)^2 = ...") all ended
  at the one-line not-found.
- Three TRUE trig identities — (sin A + cos A)^2, (sin A -
  cos A)^2, sin 2A = 2 sin A cos A — were wrongly answered
  "Not an identity" (the solver's parser read "2 sin A cos A"
  as sin(A·cos(A))); the ones that did verify got a bare
  verdict with no derivation.
- "Prove that root 5 is irrational" and "सिद्ध करो कि √3
  अपरिमेय है" were served the sqrt(2) concept card — the
  WRONG root's proof sketch.

proofs.py now sits in fallback.with_fallback (upgrading a
real solver result, and again before salvage):
  tier 1 — identities verified with SymPy, answered with a
           derivation built from the real transformation path;
           unverifiable / false identities return None and the
           old behaviour stands (never a fake proof);
  tier 2 — the standard textbook contradiction proofs for
           sqrt(2), sqrt(3), sqrt(5) from proofs_data.py, in
           the question's language;
  tier 3 — everything else (geometry proofs, theorems)
           falls through untouched.

Detection needs an explicit proof phrase, so ordinary
questions containing "that" are never captured (veto battery
below, answers recorded from the pre-wave tree).
"""
import pytest

from api import _solve_friendly
from proofs import proof_result


# --- Tier 1: verified identities get a derivation -------------

PROVABLE = [
    "Prove that sin^2 A + cos^2 A = 1",
    "Prove that tan^2 A + 1 = sec^2 A",
    "Prove that 1 + cot^2 A = cosec^2 A",
    "Prove that (sin A + cos A)^2 = 1 + 2 sin A cos A",
    "Prove that (sin A - cos A)^2 = 1 - 2 sin A cos A",
    "Prove that (1 - cos A)(1 + cos A) = sin^2 A",
    "Prove that sin 2A = 2 sin A cos A",
    "Prove that cos 2A = 2 cos^2 A - 1",
    "Prove that (a + b)^2 = a^2 + 2ab + b^2",
    "Prove that (a - b)^2 = a^2 - 2ab + b^2",
    "Prove that a^2 - b^2 = (a + b)(a - b)",
    "Prove that (x + a)(x + b) = x^2 + (a + b)x + ab",
    "Prove that (a + b)^3 = a^3 + 3a^2 b + 3ab^2 + b^3",
    "Prove that log(a*b) = log(a) + log(b)",
    "Show that (sec A - tan A)(sec A + tan A) = 1",
    "prove karo ki (a + b)^2 = a^2 + 2ab + b^2",
]


@pytest.mark.parametrize("q", PROVABLE)
def test_provable_identity_serves_proof(q):
    r = proof_result(q, False)
    assert r is not None, q
    assert r["fallback_kind"] == "proof"
    assert r["op"] == "proof_identity"
    assert r["verified"] is True
    assert "identity proved" in r["answer"]
    # A derivation, not a bare verdict: LHS line, at least one
    # working line, and the closing "= RHS".
    assert r["steps"][0].startswith("LHS = ")
    assert r["steps"][-1] == "= RHS"
    assert len(r["steps"]) >= 3


def test_hindi_identity_proof_in_hindi():
    r = proof_result("सिद्ध कीजिए कि sin^2 θ + cos^2 θ = 1", True)
    assert r is not None
    assert "सिद्ध हुआ" in r["answer"]
    assert r["steps"][0] == "LHS = sin^2 θ + cos^2 θ"


def test_formerly_wrong_identities_now_proved():
    # The pre-wave solver called these TRUE identities false.
    for q in ("Prove that (sin A + cos A)^2 = 1 + 2 sin A cos A",
              "Prove that sin 2A = 2 sin A cos A"):
        r = _solve_friendly(q)
        assert r.get("fallback_kind") == "proof", q
        assert "Not an identity" not in str(r.get("answer"))


def test_chat_path_algebraic_identity():
    r = _solve_friendly("Prove that (a + b)^2 = a^2 + 2ab + b^2")
    assert r.get("fallback_kind") == "proof"
    assert r["answer"].startswith("(a + b)^2 = a^2 + 2ab + b^2")


def test_battery_161_keeps_identity_token():
    # Wave 35 battery #161: check "token", expected "identity".
    r = _solve_friendly("Prove that sin^2 A + cos^2 A = 1.")
    assert "identity" in str(r.get("answer", "")).lower()


# --- Tier 1 honesty: false / unprovable is never proved -------

def test_false_identity_not_proved():
    assert proof_result("Prove that sin^2 A + cos^2 A = 2",
                        False) is None
    r = _solve_friendly("Prove that sin^2 A + cos^2 A = 2")
    # The solver's own honest verdict stands.
    assert r.get("answer") == "Not an identity"


def test_unverifiable_identity_falls_through():
    # A true-but-hard identity outside the transform reach and
    # a made-up one: neither may be dressed as a proof.
    assert proof_result("Prove that x = 4 is a solution of "
                        "2x = 8", False) is None


# --- Tier 2: textbook irrationality proofs --------------------

def test_sqrt2_english_proof():
    r = proof_result("Prove that √2 is irrational", False)
    assert r is not None and r["op"] == "proof_irrational"
    assert r["answer"].startswith("√2 is irrational")
    joined = " ".join(r["steps"])
    assert "contradiction" in joined and "a² = 2b²" in joined


def test_sqrt5_gets_its_own_proof():
    # Pre-wave this ask was served the sqrt(2) card.
    r = _solve_friendly("Prove that root 5 is irrational")
    assert r.get("fallback_kind") == "proof"
    assert r["answer"].startswith("√5 is irrational")
    assert "a² = 5b²" in " ".join(r["steps"])


def test_sqrt3_hindi_proof():
    r = _solve_friendly("सिद्ध करो कि √3 अपरिमेय है")
    assert r.get("fallback_kind") == "proof"
    assert r["answer"].startswith("√3 अपरिमेय है")
    assert "a² = 3b²" in " ".join(r["steps"])


def test_sqrt7_not_in_data_falls_through():
    # No textbook entry for 7 in this wave — no invented proof.
    assert proof_result("Prove that √7 is irrational",
                        False) is None


def test_irrationality_needs_proof_intent():
    # A plain concept ask (no proof phrase) keeps the old
    # concept-card behaviour; the layer must not fire.
    assert proof_result("Is root 2 irrational?", False) is None
    assert proof_result("√2 अपरिमेय संख्या है", True) is None


# --- Tier 3 + veto battery: never hijacked --------------------

VETO_UNCHANGED = [
    # (question, pre-wave answer)
    ("Solve the equation 2x + 3 = 7", "x = 2"),
    ("Find the value of x that satisfies x^2 - 5x + 6 = 0",
     "x = 2, x = 3"),
    ("Show the steps to solve 3x - 7 = 11", "x = 6"),
    ("Prove that 7 is a prime number", "7 is prime"),
    ("A train travels such that it covers 60 km in 1 hour, "
     "find its speed", "60 km/h"),
    ("solve karo equation 5x = 20", "x = 4"),
]


@pytest.mark.parametrize("q,expected", VETO_UNCHANGED)
def test_veto_answers_unchanged(q, expected):
    assert proof_result(q, False) is None
    r = _solve_friendly(q)
    assert r.get("answer") == expected
    assert r.get("fallback_kind") != "proof"


def test_geometry_proofs_fall_through():
    for q in ("Prove that the sum of the angles of a triangle "
              "is 180 degrees",
              "Prove that the diagonals of a rhombus bisect "
              "each other at right angles",
              "Prove that every even number is divisible by 2"):
        assert proof_result(q, False) is None
        r = _solve_friendly(q)
        assert r.get("fallback_kind") == "not_found"
