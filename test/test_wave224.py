"""Wave 224 — the money cost+change failure that survived
Wave 223 (Deploy-66 live check, 25 Nov 2026).

The live question:

    "Ram bought 4 notebooks at 30 rupees each. He gave a
     200 rupees note. How much did he spend and how much
     change will he get?"

was served live as "Total spent = 30 + 4 = ₹34. Change =
₹200 - ₹34 = ₹166" — WRONG (sahi: spent ₹120, change ₹80).

ROOT CAUSE (two layers, both fixed jad se):

1. Wave 223's money gate DECLINED the wording on THREE
   independent pattern gaps, each verified by direct probe:
   - _PAY_ASK: the spend alternative was "how much MONEY
     ... spend" — the live ask "How much did he spend"
     has no word "money", and no pay/cost wording either.
   - _COUNT_PRICE: every pattern demanded the currency
     BEFORE the price ("at Rs 30 each"); the live wording
     is "at 30 rupees each" — number first, currency after.
   - _NOTE: the number-first pattern allowed only the
     SINGULAR "rupee"; the live wording is "a 200 rupees
     note" (plural).
   Wave 224 widens all three (plus Hinglish kharch/bache
   asks), keeping the family's structural demands intact:
   both asks, an explicit each/per/prati count x price,
   and a note that exceeds the total.

2. Wave 212's money_change then served its guess because:
   - its note test was the bare substring "note" in t,
     which fires inside "notebooks"; and
   - it sorted the three numbers and read the two smaller
     as two prices, so the item COUNT (4) became a price.
   Wave 224: the note test is a genuine whole-word test
   (_NOTE_WORD), and a count x unit-price pair among the
   three numbers (_count_price_clash) makes the schema
   DECLINE — a schema that cannot serve a shape correctly
   must not guess.  The genuine two-prices-plus-note shape
   (Wave 212's own pinned case, change ₹48.75) still serves.

These tests pin the exact live question through every
path, the wording variants, the wave212 decline shapes,
the genuine wave212 case, and the Wave 221/222/223
regression guards.
"""
from solver.multipart223 import solve_multipart223
from solver.router import solve_question
from solver.wave212 import solve_wave212

LIVE_Q = ("Ram bought 4 notebooks at 30 rupees each. "
          "He gave a 200 rupees note. How much did he "
          "spend and how much change will he get?")


def _full_text(result):
    parts = [str(result.get("answer") or "")]
    parts += [str(s) for s in result.get("steps") or []]
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The exact live failure, through every path that can serve it
# ---------------------------------------------------------------------------

def test_live_failure_multipart_gate():
    r = solve_multipart223(LIVE_Q)
    assert r is not None
    assert r["answer"] == "(a) ₹120; (b) ₹80"
    text = _full_text(r)
    assert "Total cost = 4 × ₹30 = ₹120" in text
    assert "Change = ₹200 − ₹120 = ₹80" in text
    assert "166" not in text  # the live misfire


def test_live_failure_full_pipeline():
    r = solve_question(LIVE_Q)
    assert r is not None
    assert r["answer"] == "(a) ₹120; (b) ₹80"
    assert "166" not in _full_text(r)


def test_live_failure_chat_path():
    from api import _solve_friendly
    r = _solve_friendly(LIVE_Q, {})
    assert "₹120" in str(r.get("answer"))
    assert "₹80" in str(r.get("answer"))


# ---------------------------------------------------------------------------
# Wording variants the money family must catch
# ---------------------------------------------------------------------------

def test_money_rs_form_currency_first():
    r = solve_question(
        "Ravi buys 4 notebooks at Rs 30 each. How much "
        "does he pay and how much change does he get "
        "from Rs 200?")
    assert r["answer"] == "(a) ₹120; (b) ₹80"


def test_money_rupee_symbol_form():
    r = solve_question(
        "Sita bought 5 pens at ₹20 each. She gave a "
        "₹200 note. How much did she spend and how much "
        "change will she get?")
    assert r["answer"] == "(a) ₹100; (b) ₹100"


def test_money_for_rupees_each_form():
    r = solve_question(
        "Aman bought 6 chocolates for 15 rupees each. "
        "He gave a 100 rupees note. How much did he "
        "spend and how much change will he get?")
    assert r["answer"] == "(a) ₹90; (b) ₹10"


def test_money_per_kg_form():
    r = solve_question(
        "Mohan bought 3 kg apples at 40 rupees per kg. "
        "He gave a 200 rupees note. How much did he pay "
        "and how much change will he get?")
    assert r["answer"] == "(a) ₹120; (b) ₹80"


def test_money_hinglish_kharch_bache():
    r = solve_question(
        "Ram ne 4 copy 30 rupaye prati kharidi. Usne "
        "200 rupaye ka note diya. Usne kitne kharch "
        "kiye aur kitne bache?")
    assert r is not None
    assert r["answer"] == "(a) ₹120; (b) ₹80"


def test_money_note_of_form():
    r = solve_question(
        "Kiran bought 4 notebooks at 30 rupees each "
        "and gave a note of 200 rupees. How much did "
        "he spend and how much change will he get?")
    assert r is not None
    assert r["answer"] == "(a) ₹120; (b) ₹80"


# ---------------------------------------------------------------------------
# Wave 212 alone must never serve the ₹166 shape again
# ---------------------------------------------------------------------------

def test_wave212_declines_live_question():
    assert solve_wave212(LIVE_Q) is None


def test_wave212_declines_change_only_count_price():
    # Single ask (change only): the multipart gate needs
    # both asks, so only wave212 could guess here — it
    # must decline instead of reading 4 as a price.
    assert solve_wave212(
        "Ram bought 4 notebooks at Rs 30 each and gave "
        "a 200 rupees note. How much change will he "
        "get?") is None


def test_wave212_declines_notebook_substring_only():
    # No genuine note word at all — "note" appears only
    # inside "notebook".  Three numbers must not become
    # a change sum on a substring.
    r = solve_wave212(
        "I bought a notebook for Rs 45.75 and a pencil "
        "for Rs 5.50. How much balance will I get back "
        "from 100 rupees?")
    assert r is None or r.get("op") != "w212_money_change"


def test_wave212_genuine_two_prices_note_still_serves():
    # Wave 212's own family, pinned since its queue days:
    # two real prices + a real note = a real change sum.
    r = solve_wave212(
        "I bought a notebook for Rs 45.75 and a pencil "
        "for Rs 5.50. If I give a 100 rupee note, how "
        "much balance will I get back?")
    assert r is not None
    assert r["answer"] == "₹48.75"


# ---------------------------------------------------------------------------
# Regression guards — Waves 221 / 222 / 223 byte-identical
# ---------------------------------------------------------------------------

def test_guard_wave223_rectangle_multipart():
    r = solve_question(
        "Find the area and perimeter of a rectangle "
        "whose length is 8 cm and breadth is 5 cm")
    assert r["answer"] == "(a) 40 cm²; (b) 26"
    assert r["steps"] == [
        "(a) Area = length × breadth = 8 × 5 = 40",
        "(b) Perimeter = 2(l + b) = 2(8 + 5) = 26",
    ]


def test_guard_wave222_unit_conversion():
    r = solve_question("3 ghante me kitne minute")
    assert r["answer"] == "180 minute"
    text = _full_text(r)
    assert "1 ghanta = 60 minute" in text
    assert "3 ghante = 3 × 60 = 180 minute" in text
    assert "0 hours" not in text


def test_guard_wave221_addition_working():
    r = solve_question("347 + 258")
    assert r["answer"] == "605"
    assert r["steps"] == [
        "Write the expression: 347 + 258",
        "Ones column: 7 + 8 = 15 — write 5, carry 1",
        "Tens column: 4 + 5 + 1 (carry) = 10 — write 0, carry 1",
        "Hundreds column: 3 + 2 + 1 (carry) = 6 — write 6",
        "347 + 258 = 605",
    ]


def test_guard_wave221_subtraction_working():
    r = solve_question("502 - 178")
    assert r["answer"] == "324"
    assert r["steps"] == [
        "Write the expression: 502 - 178",
        "Ones column: 2 - 8 cannot be done, and the Tens "
        "column is 0, so borrow from the Hundreds column — "
        "Hundreds digit becomes 4, the columns in between "
        "become 9, and Ones becomes 12.",
        "Ones column: 12 - 8 = 4",
        "Tens column: 9 - 7 = 2",
        "Hundreds column: 4 - 1 = 3",
        "502 - 178 = 324",
    ]
