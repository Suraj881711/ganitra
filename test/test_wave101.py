"""Wave 101: the Pythagorean identities get genuine proofs.

Wave 95's tier 1 "proved" sin²A + cos²A = 1 with a single
step — "= 1 (using sin²x + cos²x = 1)" — the identity citing
itself (found in Deploy-20 live verification). Wave 101:

- recognises the three Pythagorean identities structurally
  (the parsed statement must be exactly sin²g + cos²g = 1,
  sec²g − tan²g = 1 or cosec²g − cot²g = 1 for one argument
  g, in ANY arrangement) and serves the textbook derivation
  from proofs_data.PYTHAGOREAN_PROOFS: sin²+cos² from a
  right-angled triangle, the other two by dividing
  sin²+cos² = 1 through by cos² / sin²;
- audits tier 1: a transform path whose "pythag" step would
  cite the very statement being proved is discarded, and
  the identity falls back to the honest LHS − RHS = 0
  verification display (compound-argument case below);
- leaves every other Wave 95 derivation byte-untouched,
  including the legitimate pythag step inside
  (sin A + cos A)² = 1 + 2 sin A cos A, where sin²+cos² = 1
  is applied to a PART of a different statement.
"""
import pytest

from api import _solve_friendly
from proofs import proof_result

SELF_CITATION = "using sin²x + cos²x = 1"


# --- sin² + cos² = 1: the right-triangle proof ----------------

def test_sin_cos_english_triangle_proof():
    r = proof_result("Prove that sin^2 A + cos^2 A = 1", False)
    assert r is not None
    assert r["fallback_kind"] == "proof"
    assert r["op"] == "proof_identity"
    assert r["verified"] is True
    joined = " ".join(r["steps"])
    # The genuine derivation: triangle, ratios, Pythagoras.
    assert "right-angled triangle" in joined
    assert "sin A = p/h" in joined
    assert "p² + b² = h²" in joined
    # And never the circular step.
    assert SELF_CITATION not in joined
    assert r["steps"][0] == "LHS = sin^2 A + cos^2 A"
    assert r["steps"][-1] == "= RHS"


@pytest.mark.parametrize("q", [
    "Prove that 1 - sin^2 A = cos^2 A",
    "Prove that cos^2 A = 1 - sin^2 A",
    "Prove that 2 sin^2 A + 2 cos^2 A = 2",
    "Show that sin^2 A + cos^2 A = 1",
])
def test_sin_cos_any_arrangement(q):
    r = proof_result(q, False)
    assert r is not None, q
    joined = " ".join(r["steps"])
    assert "right-angled triangle" in joined
    assert SELF_CITATION not in joined


def test_sin_cos_hindi_proof():
    r = proof_result("सिद्ध करो कि sin^2 A + cos^2 A = 1", True)
    assert r is not None
    assert "सिद्ध हुआ" in r["answer"]
    joined = " ".join(r["steps"])
    assert "समकोण त्रिभुज" in joined
    assert "पाइथागोरस प्रमेय" in joined
    assert "sin²A + cos²A = h²/h² = 1" in joined


def test_sin_cos_theta_symbol_and_word():
    r = proof_result("सिद्ध कीजिए कि sin^2 θ + cos^2 θ = 1", True)
    assert r is not None
    assert "sin θ = p/h" in " ".join(r["steps"])
    r = proof_result("Prove that sin^2 theta + cos^2 theta = 1",
                     False)
    assert r is not None
    assert "sin²theta + cos²theta = h²/h² = 1" in " ".join(
        r["steps"])


# --- sec² − tan² = 1 and cosec² − cot² = 1: division proofs ---

@pytest.mark.parametrize("q", [
    "Prove that sec^2 A - tan^2 A = 1",
    "Prove that tan^2 A + 1 = sec^2 A",
    "Prove that 1 + tan^2 A = sec^2 A",
])
def test_sec_tan_division_proof(q):
    r = proof_result(q, False)
    assert r is not None, q
    joined = " ".join(r["steps"])
    # Derived FROM sin²+cos² = 1, with the division shown.
    assert "Divide every term by cos²A" in joined
    assert "tan²A + 1 = sec²A" in joined
    assert "sec²A − tan²A = 1" in joined


@pytest.mark.parametrize("q", [
    "Prove that 1 + cot^2 A = cosec^2 A",
    "Prove that cosec^2 A - cot^2 A = 1",
    "Prove that cosec^2 x - cot^2 x = 1",
])
def test_cosec_cot_division_proof(q):
    r = proof_result(q, False)
    assert r is not None, q
    joined = " ".join(r["steps"])
    assert "Divide every term by sin²" in joined
    assert "1 + cot²" in joined and "cosec²" in joined


def test_sec_tan_hindi_proof():
    r = proof_result("सिद्ध कीजिए कि sec^2 θ - tan^2 θ = 1", True)
    assert r is not None
    assert "सिद्ध हुआ" in r["answer"]
    joined = " ".join(r["steps"])
    assert "cos²θ से भाग देने पर" in joined
    assert "sec²θ − tan²θ = 1" in joined


def test_cosec_cot_hindi_proof():
    r = proof_result("सिद्ध करो कि 1 + cot^2 A = cosec^2 A", True)
    assert r is not None
    joined = " ".join(r["steps"])
    assert "sin²A से भाग देने पर" in joined
    assert "cosec²A − cot²A = 1" in joined


def test_chat_path_serves_textbook_proof():
    r = _solve_friendly("Prove that sin^2 A + cos^2 A = 1.")
    assert r.get("fallback_kind") == "proof"
    assert "identity" in str(r.get("answer", "")).lower()
    assert "right-angled triangle" in " ".join(r["steps"])


# --- The tier-1 audit guard -----------------------------------

def test_compound_argument_falls_back_to_verification():
    # sin²(x+y) + cos²(x+y) = 1 IS the Pythagorean identity at
    # a compound argument: the textbook matcher declines (no
    # single variable to name) and tier 1's only path is the
    # self-citing pythag step — so the answer must be the
    # honest verification display, not a fake derivation.
    r = proof_result("Prove that sin^2 (x+y) + cos^2 (x+y) = 1",
                     False)
    assert r is not None
    joined = " ".join(r["steps"])
    assert "LHS - RHS = 0" in joined
    assert SELF_CITATION not in joined


def test_legitimate_pythag_step_untouched():
    # (sin A + cos A)² is a DIFFERENT statement; using
    # sin²+cos² = 1 on its expansion is the real proof and
    # must stay exactly as Wave 95 served it.
    r = proof_result("Prove that (sin A + cos A)^2 = "
                     "1 + 2 sin A cos A", False)
    assert r is not None
    assert r["steps"] == [
        "LHS = (sin A + cos A)^2",
        "= sin(A)^2 + 2·sin(A)·cos(A) + cos(A)^2  (expanding)",
        "= 2·sin(A)·cos(A) + 1  (using sin²x + cos²x = 1)",
        "= RHS",
    ]


# --- Honesty guards -------------------------------------------

def test_false_pythagorean_identities_not_proved():
    assert proof_result("Prove that sin^2 A + cos^2 A = 2",
                        False) is None
    assert proof_result("Prove that sec^2 A - tan^2 A = 2",
                        False) is None
    r = _solve_friendly("Prove that sin^2 A + cos^2 A = 2")
    assert r.get("answer") == "Not an identity"


def test_non_proof_questions_untouched():
    # No proof phrase -> the layer never fires.
    assert proof_result("What is sin^2 A + cos^2 A?",
                        False) is None
    assert proof_result("Solve 2x + 3 = 7", False) is None
    r = _solve_friendly("Solve the equation 2x + 3 = 7")
    assert r.get("answer") == "x = 2"
    assert r.get("fallback_kind") != "proof"
