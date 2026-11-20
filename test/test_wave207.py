"""Wave 207 (final self-audit fix wave, 20 Nov 2026):
the seven findings of the launch self-audit
(~/workspace/ganitra-audit/SUMMARY.md), pinned.

A. The one-entry-short flattened matrix-equality paste
   (Suraj's own live screenshot) serves the native
   'ye sawal galat hai' line at once, in the student's
   language — never the AI chain, never "Server is slow".
   The complete flattened paste solves even without the
   literal words "matrix"/"find" when its shape is
   unambiguous.
B. Percent questions in Bengali / Marathi / Tamil /
   Telugu script solve natively; a serve-time guard
   suppresses unresolved symbol-algebra answers
   (Mod(...) wrappings, combining-mark products) so the
   simplify nonsense can never reach a student again.
C. The form-audit pair fp12 / fp13 (AOD cubes-minimum,
   balloon dV/dr) serve through the chat path
   (_solve_friendly), not only the raw router.
D. Messy-but-real Hinglish with common misspellings
   (aru/aur, jodd/jod, btao/batao) solves natively.
E. A class-named practice request serves real practice
   questions through _solve_friendly too (the route
   already served it live; the no-context path fell to
   the practice-ADVICE card).
F. The 4-equation consistency item answers its verdict
   fast: prose glued to a system no longer feeds the
   generic solver a degree-56 letter product, purely
   linear systems take linsolve, and the matrix-method
   schema declines a system it can only partially see
   instead of solving a subset.
G. "who is the PM of India" earns the maths-only
   one-liner, like the cricket question — while a maths
   question mentioning a time "5 pm" stays maths.
"""
import time

import pytest

import fallback
from api import _solve_friendly
from solver import matrix190
from solver.matrixeq175 import (matrixeq_near_miss,
                                solve_matrix_equality)
from solver.router import _w77_is_soup, solve_question
from solver.wave207 import (solve_min_sum_cubes,
                            solve_percent_native,
                            solve_sphere_dvdr, typo_variant)


@pytest.fixture(autouse=True)
def _no_ai_keys(monkeypatch):
    """Hermetic: the real AI legs stay inert."""
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


SCREENSHOT_Q = (
    "Finding Unknown Values (Matrix Equality) Find the "
    "values of x, y, z, and w from the following equation: "
    "-1 5 x-y 2x-y 3z + w 0 13")
BK12_15 = (
    "Test the consistency of the following system of "
    "linear equations x − y + z = −9, 2x − y + z = 4, "
    "3x − y + z = 6, 4 x − y + 2 z = 7")
FP12 = ("The sum of two numbers is 16. Find the two "
        "numbers if the sum of their cubes is minimum.")
FP13 = ("A spherical balloon is being inflated. Find the "
        "rate of change of its volume with respect to the "
        "radius when the radius is 10 cm.")


# ------------------------------------------------------------------
# A. The defective flattened paste
# ------------------------------------------------------------------

def test_a_near_miss_detector():
    miss = matrixeq_near_miss(SCREENSHOT_Q)
    assert miss == {"n": 2, "entries": 7}


def test_a_screenshot_question_serves_wrong_question():
    out = _solve_friendly(SCREENSHOT_Q)
    assert out["fallback_kind"] == "wrong_question"
    assert "missing" in out["answer"]
    assert "matrix" in out["answer"]


def test_a_wrong_question_line_follows_language():
    # The route strips an explicit in-message language
    # request (Wave 107) and passes it as lang_request;
    # the verdict line must follow it.
    out = _solve_friendly(SCREENSHOT_Q, lang_request="hi")
    assert out["fallback_kind"] == "wrong_question"
    assert "गड़बड़" in out["answer"]


def test_a_complete_flat_without_matrix_word_solves():
    out = solve_question(
        "Find x, y, z, w: x-y 2x+z 2x-y 2x+w -1 0 5 13")
    assert out["op"] == "matrix_equality"
    assert out["answer"] == "x = 6, y = 7, z = -12, w = 1"


def test_a_complete_flat_is_not_a_near_miss():
    assert matrixeq_near_miss(
        "Find the values of x, y, z, and w from the "
        "following equation: -1 5 x-y 2x+z 2x-y 2x+w "
        "0 13") is None


def test_a_non_matrix_colon_question_not_flagged():
    assert matrixeq_near_miss(
        "ratio of two numbers is 3:5 and their sum is 40, "
        "find the numbers") is None


def test_a_bracketed_classic_still_solves():
    out = solve_matrix_equality(
        "If [[x-y, 2x+z],[2x-y, 2x+w]] = [[-1, 0],[5, 13]], "
        "find x, y, z and w")
    assert out["answer"] == "x = 6, y = 7, z = -12, w = 1"


# ------------------------------------------------------------------
# B. Regional percent + the symbol-soup guard
# ------------------------------------------------------------------

@pytest.mark.parametrize("q,expected", [
    ("५० चा २०% किती?", "10"),          # Marathi (audit)
    ("80 లో 50% ఎంత?", "40"),           # Telugu (audit)
    ("২০ এর ৫০% কত?", "10"),            # Bengali (audit)
    ("200 இன் 25% எவ்வளவு?", "50"),     # Tamil (audit)
    ("६० चे २५ टक्के किती?", "15"),     # percent word, mr
    ("৩০০ এর ১০ শতাংশ কত?", "30"),      # percent word, bn
])
def test_b_percent_native(q, expected):
    out = _solve_friendly(q)
    assert out["op"] == "w207_percent_native", out
    assert out["answer"] == expected


def test_b_percent_schema_declines_english():
    # The English percent family is owned by the
    # pre-existing percent solver; the wave's schema
    # requires a regional script and declines.
    assert solve_percent_native("what is 20% of 50") is None


def test_b_percent_schema_declines_two_step():
    assert solve_percent_native("५० चा २०% अधिक १० किती?") \
        is None


def test_b_marathi_multiply_is_not_garbage():
    out = _solve_friendly("१२ × ८ = किती?")
    assert out["answer"] == "96"
    assert out["op"] != "simplify"


_GARBAGE_MR = {"type": "algebra", "op": "simplify",
               "answer": "त*ि*ी*(Mod(1000*च*ा, क))",
               "steps": []}
_GARBAGE_TE = {"type": "algebra", "op": "simplify",
               "answer": "ం*త*(Mod(4000*ల*ో, ఎ))",
               "steps": []}
_GARBAGE_EQ = {"type": "algebra", "op": "equation",
               "answer": "क = 96/(त·ि·ी)", "steps": []}


@pytest.mark.parametrize("bad", [_GARBAGE_MR, _GARBAGE_TE,
                                 _GARBAGE_EQ])
def test_b_guard_suppresses_symbol_soup(bad):
    assert fallback._is_junk("q", bad) is True
    assert _w77_is_soup("q", bad) is True


@pytest.mark.parametrize("good", [
    {"type": "calculus", "op": "integrate",
     "answer": "(x - 1)·exp(x) + C", "steps": []},
    {"type": "algebra", "op": "matrix_equality",
     "answer": "x = 6, y = 7", "steps": []},
    {"type": "algebra", "op": "simplify",
     "answer": "2·x + 3", "steps": []},
])
def test_b_guard_keeps_legit_answers(good):
    assert fallback._is_junk("q", good) is False
    assert _w77_is_soup("q", good) is False


# ------------------------------------------------------------------
# C. fp12 / fp13 through the chat path
# ------------------------------------------------------------------

def test_c_fp12_chat_path():
    out = _solve_friendly(FP12)
    assert out["answer"] == "8 and 8"


def test_c_fp13_chat_path():
    out = _solve_friendly(FP13)
    assert "400" in out["answer"]
    assert "pi" in out["answer"]


def test_c_cubes_schema_verifies_and_declines():
    out = solve_min_sum_cubes(FP12)
    assert out["answer"] == "8 and 8"
    # A product-maximum dress is a different problem.
    assert solve_min_sum_cubes(
        "The sum of two numbers is 10. Find the two "
        "numbers if the product is maximum") is None
    # A squares dress is a different schema's family.
    assert solve_min_sum_cubes(
        "The sum of two numbers is 16. Find the two "
        "numbers if the sum of their squares is "
        "minimum") is None


def test_c_dvdr_schema_and_time_rate_veto():
    out = solve_sphere_dvdr(FP13)
    assert "400" in out["answer"]
    # The dV/dt dress (radius growing with time) is NOT
    # this schema: it declines rather than mislabel.
    assert solve_sphere_dvdr(
        "The radius of a balloon is increasing at the "
        "rate of 2 cm/s. Find the rate of change of its "
        "volume with respect to time when the radius "
        "is 10 cm") is None


# ------------------------------------------------------------------
# D. Typo tolerance
# ------------------------------------------------------------------

def test_d_typo_sum_solves():
    out = _solve_friendly("btao 17 aru 25 kaa jodd "
                          "kyaa hoga??")
    assert out["answer"] == "42"


def test_d_typo_variant_unit():
    assert typo_variant("btao 17 aru 25") == \
        "batao 17 aur 25"
    # Nothing to respell -> None (the gate skips the retry).
    assert typo_variant("17 aur 25 ka jod batao") is None


def test_d_correct_hinglish_unchanged():
    out = _solve_friendly("17 aur 25 ka jod batao")
    assert out["answer"] == "42"


# ------------------------------------------------------------------
# E. Practice intent on the no-context path
# ------------------------------------------------------------------

def test_e_practice_class_named_serves_questions():
    out = _solve_friendly("class 10 ke practice "
                          "questions do")
    assert out["fallback_kind"] == "practice_req"
    assert len(out["steps"]) >= 3


def test_e_practice_advice_not_hijacked():
    out = _solve_friendly("practice kaise karu maths ki")
    assert out["fallback_kind"] != "practice_req"


def test_e_normal_question_unaffected():
    out = _solve_friendly("what is 2 + 2")
    assert out["answer"] == "4"


# ------------------------------------------------------------------
# F. The consistency item: fast, and the verdict stands
# ------------------------------------------------------------------

def test_f_consistency_fast_and_correct():
    start = time.time()
    out = _solve_friendly(BK12_15)
    elapsed = time.time() - start
    assert "No solution" in out["answer"]
    assert "inconsistent" in out["answer"]
    assert elapsed < 8.0, elapsed


def test_f_matrix_schema_declines_partial_system():
    out = matrix190.solve_matrix190(BK12_15)
    assert out is None or "x = 2" not in out["answer"]


def test_f_systems_still_solve():
    out = solve_question("x + y = 10, x - y = 4")
    assert out["op"] == "system"
    assert "x = 7" in out["answer"]
    out = solve_question("x + y + z = 6, x - y = 1")
    assert out["op"] == "system"
    out = solve_question(
        "Solve the following system of equations by "
        "matrix method: x + y = 5, x - y = 1")
    assert "x = 3" in out["answer"]


def test_f_nonlinear_system_still_solves():
    out = solve_question("x^2 + y = 11, y = 2")
    assert "x = -3" in out["answer"]


# ------------------------------------------------------------------
# G. Nonmaths: the PM abbreviation
# ------------------------------------------------------------------

def test_g_pm_gets_maths_only_line():
    out = _solve_friendly("who is the PM of India")
    assert out["fallback_kind"] == "nonmaths"


def test_g_cricket_still_nonmaths():
    out = _solve_friendly("kal ke cricket match me "
                          "kya hua")
    assert out["fallback_kind"] == "nonmaths"


def test_g_time_pm_stays_maths():
    assert fallback._is_nonmaths(
        "ek train 5 pm ko chali aur 8 pm ko pahuchi, "
        "kitne ghante lage") is False


def test_w207_matrix_two_entries_short_also_wrong_question():
    """Parent extension (Deploy-52): Suraj's second screenshot
    paste was TWO entries short (6 of 8) — same defective shape,
    same native wrong-question serve; three short is too far."""
    from api import _solve_friendly
    q = ("Finding Unknown Values (Matrix Equality) Find the "
         "values of x, y, z, and w from the following equation: "
         "-1 5 x-y 2x-y 3z + w 0")
    r = _solve_friendly(q)
    assert r.get("fallback_kind") == "wrong_question", r.get("fallback_kind")
    q3 = ("Matrix equality, find x, y, z, w: -1 5 x-y 2x-y 3z")
    r3 = _solve_friendly(q3)
    assert r3.get("fallback_kind") != "wrong_question"
