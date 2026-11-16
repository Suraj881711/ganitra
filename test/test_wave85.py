"""Wave 85: the step checker — "meri galti kahan hai".

A chat message with the question, a "my solution:" marker
and the student's own working lines is CHECKED against the
solver's solution: the first wrong step is quoted with its
correction, a fully-correct solution is praised plainly, a
different-but-valid method is never flagged, and question
families the checker cannot evaluate get an honest
"can't check this type yet" plus the correct solution.
"""
from api import _solve_friendly
from stepcheck import step_check_result


def _steps(result):
    return "\n".join(str(s) for s in result.get("steps") or [])


def _check(msg):
    r = _solve_friendly(msg)
    assert r.get("type") == "step_check", r
    assert r.get("step_check") is True
    return r


LINEAR = "Solve 2x + 3 = 11"
QUAD = "Solve x^2 - 5x + 6 = 0"
DISCOUNT = ("A shirt costs Rs 800 and is sold at 15% discount. "
            "What is the selling price?")


# --- equations: correct / mistake positions -------------------

def test_wave85_correct_linear_solution():
    r = _check(f"{LINEAR}\nmy solution:\n"
               "2x = 11 - 3\n2x = 8\nx = 4")
    assert r["answer"] == "x = 4"
    assert "Every step is correct" in _steps(r)


def test_wave85_mistake_on_first_step():
    r = _check(f"{LINEAR}\nmy solution:\n"
               "2x + 3 = 12\n2x = 9\nx = 4.5")
    s = _steps(r)
    assert "very first step" in s
    assert '"2x + 3 = 12"' in s
    # A copy slip: the correction restores the real equation.
    assert "2·x + 3 = 11" in s


def test_wave85_mistake_in_middle_step():
    r = _check(f"{LINEAR}\nmy solution:\n"
               "2x = 11 - 3\n2x = 9\nx = 4.5")
    s = _steps(r)
    assert "correct up to step 1" in s
    assert "Step 2 is where it first goes wrong" in s
    assert '"2x = 9"' in s
    assert "That step should be: 2·x = 8" in s
    # The full correct solution follows the feedback.
    assert "Divide both sides by 2" in s


def test_wave85_mistake_on_last_step():
    # Only one side divided: x = 8 instead of x = 4.
    r = _check(f"{LINEAR}\nmy solution:\n2x = 8\nx = 8")
    s = _steps(r)
    assert "Step 2 is where it first goes wrong" in s
    assert "That step should be: x = 4" in s


def test_wave85_wrong_bare_final_answer():
    r = _check(f"{LINEAR}\nmy solution:\n2x = 8\n5")
    s = _steps(r)
    assert "Step 2 is where it first goes wrong" in s
    assert "That step should be: x = 4" in s


def test_wave85_annotations_are_not_accused():
    r = _check(f"{LINEAR}\nmy solution:\n"
               "3 ko dusri taraf le jao\n"
               "2x = 11 - 3\n2x = 8\nx = 4")
    assert "Every step is correct" in _steps(r)


def test_wave85_unfinished_solution_is_incomplete():
    r = _check(f"{LINEAR}\nmy solution:\n2x = 11 - 3\n2x = 8")
    s = _steps(r)
    assert "not finished yet" in s
    assert "Divide both sides by 2" in s  # full solution shown


def test_wave85_arrow_separated_steps():
    r = _check(f"{LINEAR}\nmy solution: 2x = 8 -> x = 4")
    assert "Every step is correct" in _steps(r)


# --- quadratics: factoring, branches, roots --------------------

def test_wave85_quadratic_factoring_is_a_valid_method():
    r = _check(f"{QUAD}\nmy solution:\n"
               "(x - 2)(x - 3) = 0\n"
               "x - 2 = 0 or x - 3 = 0\n"
               "x = 2, x = 3")
    s = _steps(r)
    assert r["answer"] == "x = 2, x = 3"
    assert "Every step is correct" in s
    # The reference uses the quadratic formula; factoring is a
    # genuinely different method and is praised as such.
    assert "different from mine" in s


def test_wave85_quadratic_branch_by_branch():
    r = _check(f"{QUAD}\nmy solution:\n"
               "(x - 2)(x - 3) = 0\n"
               "x - 2 = 0\nx = 2\nx - 3 = 0\nx = 3")
    assert "Every step is correct" in _steps(r)


def test_wave85_quadratic_wrong_root():
    r = _check(f"{QUAD}\nmy solution:\n"
               "(x - 2)(x - 3) = 0\nx = 2, x = 4")
    s = _steps(r)
    assert "Step 2 is where it first goes wrong" in s
    assert '"x = 2, x = 4"' in s


def test_wave85_quadratic_missing_root_is_incomplete():
    r = _check(f"{QUAD}\nmy solution:\n"
               "(x - 2)(x - 3) = 0\nx = 2")
    s = _steps(r)
    assert "not finished yet" in s
    assert "One more root is still missing" in s


# --- simplify chains -------------------------------------------

def test_wave85_simplify_correct():
    r = _check("Simplify 3(x + 2) + 2x\nmy solution:\n"
               "3x + 6 + 2x\n5x + 6")
    assert r["answer"] == "5·x + 6"
    assert "Every step is correct" in _steps(r)


def test_wave85_simplify_partial_claims_not_accused():
    # A claim about a sub-expression is a side note, not the
    # whole state — it must not be flagged.
    r = _check("Simplify 3(x + 2) + 2x\nmy solution:\n"
               "3(x + 2) = 3x + 6\n3x + 6 + 2x\n5x + 6")
    assert "Every step is correct" in _steps(r)


def test_wave85_simplify_wrong_expansion():
    r = _check("Simplify 3(x + 2) + 2x\nmy solution:\n"
               "3x + 2 + 2x\n5x + 2")
    s = _steps(r)
    assert "very first step" in s
    assert '"3x + 2 + 2x"' in s
    assert "That step should be: 5·x + 6" in s


# --- percentages / applied: numeric claims ----------------------

def test_wave85_percentage_correct():
    r = _check("What is 15% of 800?\nmy solution:\n"
               "15/100 x 800\n= 120")
    assert r["answer"] == "120"
    assert "Every step is correct" in _steps(r)


def test_wave85_percentage_wrong_claim():
    r = _check("What is 15% of 800?\nmy solution:\n"
               "15% of 800 = 100\n100")
    s = _steps(r)
    assert "very first step" in s
    assert "15% of 800 = 120" in s


def test_wave85_discount_correct():
    r = _check(f"{DISCOUNT}\nmy solution:\n"
               "Discount = 15% of 800 = 120\n"
               "Selling price = 800 - 120 = 680")
    assert r["answer"] == "Rs 680"
    assert "Every step is correct" in _steps(r)


def test_wave85_discount_wrong_final_with_right_steps():
    r = _check(f"{DISCOUNT}\nmy solution:\n"
               "Discount = 15% of 800 = 120\n"
               "Selling price = 800 - 120 = 700")
    s = _steps(r)
    assert "correct up to step 1" in s
    assert "Step 2 is where it first goes wrong" in s
    assert "800 - 120 = 680" in s


# --- out of scope ------------------------------------------------

def test_wave85_out_of_scope_type_gets_solution_not_silence():
    r = _check("Find the value of sin 30 degrees\nmy solution:\n"
               "sin 30 = 1/2\nanswer = 0.5")
    s = _steps(r)
    assert r["answer"] == "1/2"
    assert "can't check steps for this type of question yet" in s
    assert "standard values" in s  # the correct solution follows


# --- Hindi / Hinglish ---------------------------------------------

def test_wave85_hindi_equation_all_correct():
    r = _check("2x + 3 = 11 हल करो\nमेरा हल:\n"
               "2x = 11 - 3\n2x = 8\nx = 4")
    s = _steps(r)
    assert r["answer"] == "x = 4"
    assert "हर चरण सही है" in s


def test_wave85_hinglish_mistake_feedback():
    r = _check(f"{LINEAR}\nmera solution:\n"
               "2x = 11 - 3\n2x = 10\nx = 5")
    s = _steps(r)
    assert "Pehli galti step 2 par hai" in s
    assert "Ye step aisa hona chahiye tha: 2·x = 8" in s
    assert "Ye raha poora sahi solution" in s


def test_wave85_hinglish_discount_correct():
    r = _check("ek shirt 800 rupaye ki hai, us par 15% chhoot "
               "hai. selling price kitni hogi?\nmera solution:\n"
               "chhoot = 15% of 800 = 120\n"
               "selling price = 800 - 120 = 680")
    s = _steps(r)
    assert r["answer"] == "Rs 680"
    assert "Har step sahi hai" in s


# --- the gate: everything else is untouched ------------------------

def test_wave85_plain_question_is_not_a_check_request():
    r = _solve_friendly(LINEAR)
    assert r.get("type") != "step_check"
    assert r["answer"] == "x = 4"


def test_wave85_marker_without_working_is_not_a_check():
    assert step_check_result(f"{LINEAR}\nmy solution:") is None
    assert step_check_result(f"{LINEAR}\nmy solution:\nx = 4") \
        is None


def test_wave85_gibberish_still_gets_one_line_not_found():
    r = _solve_friendly("asdf qwer zxq\nmy solution:\n"
                        "foo bar\nbaz qux")
    assert r.get("fallback_kind") == "not_found"


def test_wave85_unsolvable_question_falls_back_to_normal_flow():
    # The solver itself cannot solve this question, so there
    # is no reference to check against: the gate stays shut.
    assert step_check_result(
        "एक शर्ट ₹800 की है, 15% छूट के बाद कितने में मिलेगी?\n"
        "मेरा हल:\nछूट = 120\nविक्रय मूल्य = 680") is None
