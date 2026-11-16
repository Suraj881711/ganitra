"""Wave 102: trailing proof phrases reach the proof layer.

Wave 95's detection required an explicit proof phrase, and
the phrase regex always searched the whole question — but
_statement() stripped the filler verbs that come WITH the
phrase ("karo", करो, the "it" of "prove it") only at the
START of the text. NCERT exercises put the phrase last
("sec²θ − tan²θ = 1 सिद्ध करो"), so the trailing filler
survived into the statement, the shape guard rightly
rejected the poisoned side, and the ask fell through to a
concept card or the not-found line (found in Deploy-21
live verification). Wave 102, all inside proofs.py:

- _statement strips the same filler tokens at the end too
  (repeatedly), so a trailing-phrase statement parses
  exactly as the leading-phrase form does;
- the phrase regex consumes the full verb: साबित करो (the
  old pattern matched only साबित कर and left a stray "ो"
  behind, breaking even the leading form) and Roman
  saabit/sabit/saabito/sabito + kar/karo;
- "kijiye" joins the connector tokens (for "siddh kijiye");
- _clean_for_parse normalises unicode superscripts
  (sin²A -> sin^2 A): ² is a Unicode word character, so it
  glued onto the function name and the residual kept "sin"
  as a "long word" for the shape guard to reject;
- the irrationality gate accepts the common Roman
  misspelling "aprimey" alongside "aparimey".

The gate is unchanged: no proof phrase anywhere, no
proof. Bare "dikhao" is deliberately NOT a proof phrase —
it is a generic "show me", not a proof imperative.
"""
import pytest

from api import _solve_friendly
from proofs import _has_proof_intent, _statement, proof_result


def _joined(r):
    return " ".join(r["steps"])


# --- The five Deploy-21 probes, through the chat path ---------

def test_probe_sec_tan_siddh_karo():
    r = _solve_friendly("sec^2 A - tan^2 A = 1 siddh karo")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"
    assert "Divide every term by cos²A" in _joined(r)


def test_probe_sec_tan_unicode_hindi():
    r = _solve_friendly("sec²θ - tan²θ = 1 सिद्ध करो")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"
    assert "सिद्ध हुआ" in str(r.get("answer", ""))
    assert "cos²θ से भाग देने पर" in _joined(r)


def test_probe_sin_cos_siddh_karo_not_concept():
    # Was hijacked by the Trigonometric Identity concept card.
    r = _solve_friendly("sin^2 A + cos^2 A = 1 siddh karo")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"
    assert "right-angled triangle" in _joined(r)


def test_probe_cosec_cot_siddh_karo():
    r = _solve_friendly("cosec^2 A - cot^2 A = 1 siddh karo")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"
    assert "Divide every term by sin²A" in _joined(r)


def test_probe_prove_karo_upgrades_bare_verdict():
    # Was the solver's bare "Identity verified ✔" with no
    # working; the proof upgrade hook now fires.
    r = _solve_friendly("sec^2 A - tan^2 A = 1 prove karo")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"
    assert "identity proved ✔" in str(r.get("answer", ""))


# --- Trailing variants: all three Pythagorean identities ------

@pytest.mark.parametrize("q, marker", [
    # sin² + cos² = 1 — the right-triangle proof
    ("sin^2 A + cos^2 A = 1 prove it", "right-angled triangle"),
    ("sin^2 A + cos^2 A = 1 सिद्ध करो", "पाइथागोरस प्रमेय"),
    ("sin^2 A + cos^2 A = 1 सिद्ध कीजिए", "पाइथागोरस प्रमेय"),
    ("sin^2 A + cos^2 A = 1 sabito karo", "right-angled triangle"),
    # sec² − tan² = 1 — divide sin²+cos² = 1 by cos²
    ("1 + tan^2 A = sec^2 A siddh karo", "Divide every term by cos²A"),
    ("tan^2 A + 1 = sec^2 A prove karo", "Divide every term by cos²A"),
    ("sec^2 A - tan^2 A = 1 साबित करो", "cos²A से भाग देने पर"),
    # cosec² − cot² = 1 — divide by sin²
    ("1 + cot^2 theta = cosec^2 theta siddh kijiye",
     "Divide every term by sin²theta"),
    ("cosec^2 A - cot^2 A = 1 saabit karo",
     "Divide every term by sin²A"),
])
def test_trailing_pythagorean_variants(q, marker):
    r = proof_result(q, False)
    assert r is not None, q
    assert r["fallback_kind"] == "proof"
    assert r["op"] == "proof_identity"
    assert r["verified"] is True
    assert marker in _joined(r), q


# --- Trailing and leading forms give the SAME proof -----------

@pytest.mark.parametrize("leading, trailing", [
    ("Prove that sec^2 A - tan^2 A = 1",
     "sec^2 A - tan^2 A = 1 siddh karo"),
    ("Prove that sin^2 A + cos^2 A = 1",
     "sin^2 A + cos^2 A = 1 prove it"),
    ("सिद्ध कीजिए कि sec^2 A - tan^2 A = 1",
     "sec^2 A - tan^2 A = 1 सिद्ध करो"),
    ("siddh karo ki cosec^2 A - cot^2 A = 1",
     "cosec^2 A - cot^2 A = 1 siddh karo"),
])
def test_trailing_matches_leading_byte_for_byte(leading, trailing):
    a = proof_result(leading, False)
    b = proof_result(trailing, False)
    assert a is not None and b is not None
    assert a["answer"] == b["answer"]
    assert a["steps"] == b["steps"]


def test_saabit_karo_leading_form_fixed():
    # साबित\s*कर used to leave a stray "ो" in the statement,
    # so even the leading form failed; the phrase now
    # consumes the whole verb.
    r = proof_result("साबित करो कि sin^2 A + cos^2 A = 1", True)
    assert r is not None
    assert "पाइथागोरस प्रमेय" in _joined(r)


# --- Unicode superscripts --------------------------------------

@pytest.mark.parametrize("q", [
    "sin²A + cos²A = 1 siddh karo",        # argument attached
    "sin² A + cos² A = 1 siddh karo",      # argument spaced
    "sin²θ + cos²θ = 1 सिद्ध करो",         # Greek argument
    "tan²A + 1 = sec²A siddh karo",
    "sin²30 + cos²30 = 1 siddh karo",      # numeric (degrees)
])
def test_unicode_superscript_statements(q):
    r = proof_result(q, False)
    assert r is not None, q
    assert r["fallback_kind"] == "proof"
    assert r["verified"] is True


# --- Tier-1 (non-Pythagorean) identities, trailing phrase -----

def test_tier1_identity_trailing_phrase():
    a = proof_result("Prove that (sin A + cos A)^2 = "
                     "1 + 2 sin A cos A", False)
    b = proof_result("(sin A + cos A)^2 = "
                     "1 + 2 sin A cos A siddh karo", False)
    assert a is not None and b is not None
    assert b["steps"] == a["steps"]
    assert b["answer"] == a["answer"]


def test_double_angle_trailing_phrase():
    # The solver alone "solves" this as an equation (A = 1);
    # the proof upgrade hook must replace that reading.
    r = _solve_friendly("sin 2A = 2 sin A cos A siddh karo")
    assert r.get("source") == "proofs"
    assert "double-angle" in _joined(r)


# --- Irrationality with trailing phrases -----------------------

@pytest.mark.parametrize("q, answer", [
    ("√2 aprimey hai siddh karo", "√2 is irrational — proved ✔"),
    ("√5 aprimey hai siddh karo", "√5 is irrational — proved ✔"),
    ("√3 अपरिमेय है सिद्ध करो", "√3 अपरिमेय है — सिद्ध हुआ ✔"),
])
def test_irrationality_trailing_phrase(q, answer):
    r = proof_result(q, False)
    assert r is not None, q
    assert r["op"] == "proof_irrational"
    assert r["answer"] == answer


def test_irrationality_trailing_chat_path_not_concept():
    # Was served the concepts.py "proof idea" card because
    # the gate only knew the book spelling "aparimey".
    r = _solve_friendly("√2 aprimey hai siddh karo")
    assert r.get("source") == "proofs"
    assert r.get("fallback_kind") == "proof"


# --- Statement extraction (the mechanism) ----------------------

@pytest.mark.parametrize("q, stmt", [
    ("sec^2 A - tan^2 A = 1 siddh karo", "sec^2 A - tan^2 A = 1"),
    ("sec^2 A - tan^2 A = 1 सिद्ध करो", "sec^2 A - tan^2 A = 1"),
    ("sin^2 A + cos^2 A = 1 prove it", "sin^2 A + cos^2 A = 1"),
    ("sin^2 A + cos^2 A = 1 siddh karo.", "sin^2 A + cos^2 A = 1"),
    ("Prove that sec^2 A - tan^2 A = 1", "sec^2 A - tan^2 A = 1"),
])
def test_statement_extraction(q, stmt):
    assert _has_proof_intent(q)
    assert _statement(q) == stmt


# --- Guards: the gate stays strict ------------------------------

def test_bare_statements_have_no_proof_intent():
    assert not _has_proof_intent("sin^2 A + cos^2 A = 1")
    assert proof_result("sin^2 A + cos^2 A = 1", False) is None
    assert proof_result("sec^2 A - tan^2 A = 1", False) is None


def test_bare_statement_chat_answers_unchanged():
    # Byte-identical to the pre-Wave-102 behaviour.
    r = _solve_friendly("sin^2 A + cos^2 A = 1")
    assert r.get("fallback_kind") == "concept"
    assert r.get("op") == "trig_identity"
    assert r.get("answer") == (
        "Trigonometric Identity: sin²θ + cos²θ = 1 — "
        "sin²θ + cos²θ = 1 (true for every angle θ)")
    r = _solve_friendly("sec^2 A - tan^2 A = 1")
    assert r.get("answer") == "Answer not found."


def test_false_identity_trailing_phrase_not_a_proof():
    assert proof_result("sin^2 A + cos^2 A = 2 siddh karo",
                        False) is None
    assert proof_result("sec^2 A - tan^2 A = 5 सिद्ध करो",
                        True) is None
    # Chat path: exactly what the baseline served — the
    # concept card for the sin² case (same result as the
    # bare true statement gets), not-found for the sec² case.
    bare = _solve_friendly("sin^2 A + cos^2 A = 1")
    false = _solve_friendly("sin^2 A + cos^2 A = 2 siddh karo")
    assert false.get("source") != "proofs"
    assert false.get("answer") == bare.get("answer")
    assert false.get("steps") == bare.get("steps")
    r = _solve_friendly("sec^2 A - tan^2 A = 5 सिद्ध करो")
    assert r.get("answer") == "उत्तर नहीं मिला।"


def test_dikhao_is_not_a_proof_phrase():
    # "dikhao" = generic "show me" (solve karke dikhao) —
    # deliberately not enough to trigger the proof layer.
    assert not _has_proof_intent("sin^2 A + cos^2 A = 1 dikhao")
    assert proof_result("sin^2 A + cos^2 A = 1 dikhao",
                        False) is None


def test_prove_it_no_longer_a_false_not_an_identity():
    # Baseline: the solver parsed "it" as i·t and answered
    # "Not an identity" for a true identity. The proof
    # upgrade now replaces that wrong verdict.
    r = _solve_friendly("sin^2 A + cos^2 A = 1 prove it")
    assert r.get("source") == "proofs"
    assert "identity proved ✔" in str(r.get("answer", ""))


def test_non_proof_questions_untouched():
    assert _solve_friendly("What is 15% of 240?").get("answer") == "36"
    r = _solve_friendly("ek tren 360 km jati hai 40 km per hour "
                        "ki speed se, kitne ghante lagenge")
    assert r.get("answer") == "9 hours"
    assert _solve_friendly("circal area radius 7").get("answer") == "154"
