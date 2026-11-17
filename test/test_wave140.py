"""Wave 140: square-system fixes (Suraj's live check,
17 Nov 2026 — a throwaway account on the production
Deploy-25 build surfaced five real defects):

1. A bare typed "√144" was SERVED as "144*q*r*s*t" — the
   expression parser's normaliser replaced √ with the bare
   word "sqrt", and SymPy multiplied the letters out.
2. "(3/4) ka square batao" answered "3/4" (the square was
   dropped) and "3/4 ka varg" answered 16 (only the
   denominator was squared): the square/cube handlers'
   operand grammar knew only a lone number, and the
   router's squared/cubed rewrite bound the power to the
   denominator digit too.
3. "1024 perfect square hai ya nahi?" had no deterministic
   owner and went to the AI fallback (~30 s).
4. Mensuration answers dropped the question's unit:
   "bhuja 5 cm, kshetrafal?" -> "25", not "25 cm²" (the
   router translations dropped the unit, and geometry never
   re-attached it); cube volumes lost their cm³ the same
   way.
5. "Find the square root of 729" solved, but its working
   line read "The 2th root of 729.0 ...".

Tests run the real solver entry (solve_question); the
headline cases are also checked through the chat path
(api._solve_friendly) to pin that no AI leg is involved.
"""
import pytest

from solver.router import solve_question


def _r(q):
    return solve_question(q)


def _ans(q):
    return str(_r(q).get("answer", ""))


# --- Defect 1: bare √ expressions -------------------------

def test_bare_root_number():
    assert _ans("√144") == "12"


def test_bare_root_625():
    assert _ans("√625") == "25"


def test_bare_root_bracketed():
    assert _ans("√(144)") == "12"


def test_bare_root_sum():
    assert _ans("√144 + √25") == "17"


def test_bare_root_inside_expression():
    assert _ans("√144 × √9") == "36"
    assert _ans("√(25+144)") == "13"


def test_bare_root_variable_and_decimal():
    assert _ans("√x") == "sqrt(x)"
    assert _ans("√12.25") == "7/2"


def test_bare_root_never_letter_product():
    for q in ("√144", "√625", "√144 + √25"):
        a = _ans(q)
        assert "q*r*s*t" not in a
        assert "*" not in a or q == "√144 × √9"


# --- Defect 2: fraction ka square / varg ------------------

def test_bracketed_fraction_ka_square():
    assert _ans("(3/4) ka square batao") == "9/16"


def test_fraction_ka_varg():
    assert _ans("3/4 ka varg") == "9/16"
    assert _ans("(3/4) ka varg") == "9/16"


def test_square_of_fraction_unchanged():
    assert _ans("square of 3/4") == "9/16"


def test_decimal_ka_square_in_decimals():
    assert _ans("0.5 ka square") == "0.25"
    assert _ans("0.5 ka varg") == "0.25"


def test_fraction_cube_forms():
    assert _ans("(2/3) ka cube") == "8/27"
    assert _ans("3/4 ka ghan") == "27/64"
    assert _ans("cube of 2/3") == "8/27"


def test_fraction_squared_cubed_words():
    # The router's Wave-65 rewrite bound the power to the
    # denominator ("2/3 squared" -> "2/3^2" = 2/9).
    assert _ans("2/3 squared") == "4/9"
    assert _ans("2/3 cubed") == "8/27"
    assert _ans("(2/3) squared") == "4/9"


def test_plain_square_unchanged():
    assert _ans("25 ka square") == "625"
    r = _r("25 ka square")
    assert r["steps"] == ["Square of 25 = 25 × 25 = 625"]


def test_fraction_ka_square_root():
    assert _ans("9/4 ka square root") == "3/2"


# --- Defect 3: perfect square / cube haan-nahi ------------

def test_perfect_square_hinglish_yes():
    r = _r("1024 perfect square hai ya nahi?")
    assert r.get("op") == "perfect_square_check"
    assert _ans("1024 perfect square hai ya nahi?") == \
        "Haan — 1024 = 32²"


def test_perfect_square_english_yes():
    r = _r("is 1024 a perfect square")
    assert r.get("op") == "perfect_square_check"
    assert r["answer"] == "Yes — 1024 = 32²"


def test_perfect_square_hinglish_no_nearest_reasoning():
    r = _r("1023 perfect square hai ya nahi?")
    assert r.get("op") == "perfect_square_check"
    assert r["answer"].startswith("Nahi")
    assert "31² = 961" in r["steps"][0]
    assert "32² = 1024" in r["steps"][0]


def test_perfect_square_purna_varg():
    assert _ans("1024 purna varg hai") == "Haan — 1024 = 32²"


def test_perfect_square_devanagari():
    r = _r("क्या 1024 पूर्ण वर्ग है?")
    assert r.get("op") == "perfect_square_check"
    assert r["answer"] == "हाँ — 1024 = 32²"


def test_perfect_cube_family():
    assert _ans("27 perfect cube hai ya nahi?") == \
        "Haan — 27 = 3³"
    assert _ans("is 100 a perfect cube") == \
        "No — 100 is not a perfect cube"
    assert _ans("क्या 1000 पूर्ण घन है?") == "हाँ — 1000 = 10³"


def test_perfect_square_small_edges():
    assert _ans("is 1 a perfect square") == "Yes — 1 = 1²"
    assert _ans("is 0 a perfect square") == "Yes — 0 = 0²"


def test_perfect_square_word_problem_not_hijacked():
    # A word problem that merely mentions a perfect square
    # must NOT be answered with the yes/no check.
    r = _r("find the smallest number by which 9408 must be "
           "multiplied so that the product is a perfect square")
    assert r.get("op") not in ("perfect_square_check",
                               "perfect_cube_check")


# --- Defect 4: units on area / volume answers -------------

def test_square_area_hindi_keeps_cm2():
    assert _ans("Ek varg ki bhuja 5 cm hai, uska kshetrafal "
                "batao") == "25 cm²"


def test_square_area_english_keeps_cm2():
    assert _ans("area of a square with side 5 cm") == "25 cm²"
    assert _ans("area of a square with side 5 m") == "25 m²"


def test_square_area_no_unit_stays_plain():
    assert _ans("area of a square with side 5") == "25"


def test_cube_volume_keeps_cm3():
    assert _ans("Ek ghan ki bhuja 5 cm hai, uska aayatan "
                "batao") == "125 cm³"
    assert _ans("volume of a cube with side 5 cm") == "125 cm³"
    assert _ans("5 cm bhuja wale ghan ka aayatan batao") == \
        "125 cm³"


def test_circle_and_rectangle_area_units():
    assert _ans("area of a circle with radius 7 cm") == \
        "154 cm²"
    assert _ans("area of a rectangle with length 5 cm and "
                "breadth 3 cm") == "15 cm²"


def test_perimeter_not_suffixed():
    # Lengths are out of this wave's scope: unchanged.
    assert _ans("perimeter of a square with side 5 cm") == "20"


# --- Defect 5: root wording -------------------------------

def test_square_root_wording():
    r = _r("Find the square root of 729")
    assert r["answer"] == "27"
    assert r["steps"][0] == ("The square root of 729 is the "
                             "number whose square is 729.")


def test_cube_root_wording():
    r = _r("Find the cube root of 729")
    assert r["answer"] == "9"
    assert r["steps"][0] == ("The cube root of 729 is the "
                             "number whose cube is 729.")


def test_nth_root_ordinal_wording():
    r = _r("find the 4th root of 81")
    assert r["answer"] == "3"
    assert "4th root of 81" in r["steps"][0]
    assert "2th" not in str(r["steps"])
    assert "3th" not in str(_r("Find the cube root of 729")
                            ["steps"])


# --- Neighbours pinned unchanged --------------------------

def test_sqrt_by_words_unchanged():
    assert _ans("625 ka square root") == "25"
    assert _ans("625 ka square root kya hai?") == "25"


def test_fraction_arithmetic_unchanged():
    assert _ans("1/2 + 1/4") == "3/4"


def test_word_power_compound_unchanged():
    # Wave 65's compound form still works end to end.
    assert _ans("15 squared minus 9 squared") == "144"


# --- Chat path: headline cases need no AI -----------------

def test_chat_path_headlines():
    from api import _solve_friendly
    assert str(_solve_friendly("√144").get("answer")) == "12"
    assert str(_solve_friendly("(3/4) ka square batao")
               .get("answer")) == "9/16"
    r = _solve_friendly("1024 perfect square hai ya nahi?")
    assert str(r.get("answer")) == "Haan — 1024 = 32²"
    assert str(_solve_friendly(
        "Ek varg ki bhuja 5 cm hai, uska kshetrafal batao")
        .get("answer")) == "25 cm²"
