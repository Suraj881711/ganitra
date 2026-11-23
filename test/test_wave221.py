"""Wave 221 — arithmetic WITH-WORKING (jad se fix).

Bug (live, Deploy-62 retest, 23 Nov 2026): a plain arithmetic
question like "347 + 258" was answered with fake working —
"Evaluate: 605 = 605" — and then the final answer. ROOT CAUSE:
parse_expression EVALUATES a numeric expression while parsing
("347+258" -> Integer 605), so solve_arithmetic ran
reduction_steps over str(expr) = "605", got no steps back, and
fell back to the self-echo "Evaluate: {expr} = {value}".

Fix (solver/arithmetic.py, _evaluate_steps221): the working is
built from the ORIGINAL expression text — a single +, - or x
between two whole numbers gets school column working (digit by
digit, right to left, with carry / borrow lines, per DeepSeek
Job 7's verified spec); anything else gets genuine BODMAS
reduction steps from the original text. These tests pin the
required cases so the fake line can never come back.
"""
from solver.arithmetic import solve_arithmetic


def _steps_text(result):
    return "\n".join(result["steps"])


def _assert_genuine(result, answer):
    assert result["answer"] == answer
    text = _steps_text(result)
    assert "Evaluate:" not in text
    return text


def test_addition_with_carry_working():
    r = solve_arithmetic("347 + 258")
    text = _assert_genuine(r, "605")
    # Column working, right to left, with the carry spoken.
    assert "carry" in text
    assert "7 + 8 = 15" in text
    assert "347 + 258 = 605" in text


def test_subtraction_borrow_across_zero():
    r = solve_arithmetic("502 - 178")
    text = _assert_genuine(r, "324")
    # The tens column is 0, so the borrow must come from the
    # hundreds — and the working must say so.
    assert "borrow" in text
    assert "12 - 8 = 4" in text
    assert "502 - 178 = 324" in text


def test_multiplication_with_carry_working():
    r = solve_arithmetic("24 * 6")
    text = _assert_genuine(r, "144")
    assert "4 × 6 = 24" in text
    assert "carry" in text
    assert "24 × 6 = 144" in text


def test_subtraction_no_pointless_zero_column():
    # Job 7 draft defect: 1000 - 645 used to grow a pointless
    # "Thousands: 0 - 0 = 0" step. The leading zero column
    # must never be emitted.
    r = solve_arithmetic("1000 - 645")
    text = _assert_genuine(r, "355")
    assert "0 - 0" not in text
    assert "borrow" in text
    assert "1000 - 645 = 355" in text


def test_hinglish_addition_gets_column_working():
    # Verified phrasing: the Hinglish filler ("kitna hoga") is
    # stripped upstream and the question lands on this same
    # evaluate path — it must get the same real working.
    r = solve_arithmetic("347 + 258 kitna hoga")
    text = _assert_genuine(r, "605")
    assert "carry" in text
    assert "347 + 258 = 605" in text


def test_multi_op_expression_gets_real_reduction_steps():
    # The self-echo also swallowed multi-operation questions
    # ("Evaluate: 45 = 45"); they now get BODMAS steps from
    # the original text.
    r = solve_arithmetic("27 + 2 * 12 - 6")
    text = _assert_genuine(r, "45")
    assert "2 × 12 = 24" in text


def test_multi_digit_multiplication_partial_products():
    r = solve_arithmetic("24 * 16")
    text = _assert_genuine(r, "384")
    assert "24 × 6 = 144" in text
    assert "24 × 10 = 240" in text
    assert "24 × 16 = 384" in text
