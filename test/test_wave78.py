"""Wave 78: plain-English commercial-maths phrasings.

The Deploy-17 live check found that standard English
textbook discount questions returned "Answer not found":
"A shirt costs Rs 800 and is sold at 15% discount. What is
the selling price?" The existing handlers covered the
Hinglish/Roman phrasings (router rewrites + hinglish_discount)
and a few rigid English shapes ("marked price is X,
discount of Y%"), but not the ordinary Class 7-8 English
family: "costs Rs X ... sold at Y% discount", "discount
is Y%", "marked at Rs X", "X% off", mark-up over cost
price, SP stated before CP, profit stated as a rupee
amount, "sells it at a loss of Y%".

Wave 78 fixes this at the applied layer: a new gated
family (_english_commercial, registered last in _FAMILIES)
plus four in-place extensions — _mbp accepts "at a loss
of P%", _profit_loss_forms accepts "sells" and "gain",
_discount answers the discount amount when that is what
is asked and no longer reads a percent as a sold price,
and the _wave65_schemas discount-percent pattern accepts
"sold for Rs S". Every expectation below is hand-computed.
"""
import pytest

from api import _solve_friendly


def _solver_answer(question):
    """The answer when the REAL solver claims the question
    (no fallback flag of any kind), else None."""
    result = _solve_friendly(question)
    if result.get("fallback_kind") is not None:
        return None
    return str(result.get("answer", ""))


# --- Single discount -> selling price -----------------------

@pytest.mark.parametrize("question,expected", [
    # The Deploy-17 live-check failure itself.
    ("A shirt costs Rs 800 and is sold at 15% discount. "
     "What is the selling price?", "Rs 680"),
    ("A shopkeeper marks a bag at Rs 950 and gives a 10% "
     "discount. What is the selling price of the bag?",
     "Rs 855"),
    ("Find the selling price of an article whose marked "
     "price is Rs 650 and discount is 12%.", "Rs 572"),
    ("A cycle is marked at Rs 2500. If a discount of 8% is "
     "allowed, find its selling price.", "Rs 2300"),
    ("A pair of shoes costs 999 rupees and is sold at a "
     "discount of 25%. Find the amount paid by the "
     "customer.", "Rs 749.25"),
    ("An item priced at Rs 400 is available at 30% off. "
     "How much will you pay for it?", "Rs 280"),
    # Shapes that already solved — pinned against flips.
    ("The marked price of a jacket is Rs 1200. A discount "
     "of 20% is given on it. Find the selling price.",
     "Rs 960"),
    ("A shirt is sold at a discount of 15% on its marked "
     "price of Rs 800. Find the selling price.", "Rs 680"),
])
def test_discount_selling_price(question, expected):
    assert _solver_answer(question) == expected


# --- Discount amount asked ----------------------------------

@pytest.mark.parametrize("question,expected", [
    ("What is the discount on a TV marked at Rs 15000 if "
     "the discount rate is 5%?", "Rs 750"),
    ("During a sale, a kurta with marked price Rs 1750 is "
     "offered at a discount of 30%. How much discount does "
     "the customer get?", "Rs 525"),
])
def test_discount_amount(question, expected):
    assert _solver_answer(question) == expected


# --- Reverse discount and successive discounts --------------

@pytest.mark.parametrize("question,expected", [
    ("A book is sold for Rs 360 after a discount of 10% on "
     "its marked price. Find the marked price.", "Rs 400"),
    ("After a discount of 20%, a watch is sold for Rs 1600. "
     "What was its marked price?", "Rs 2000"),
    ("A washing machine is sold at Rs 20400 after giving a "
     "discount of 15% on the marked price. Find the marked "
     "price.", "Rs 24000"),
    ("A saree marked at Rs 3000 is sold at two successive "
     "discounts of 10% and 5%. Find the selling price.",
     "Rs 2565"),
    ("Find the single discount equivalent to two successive "
     "discounts of 20% and 10%.", "28%"),
])
def test_discount_reverse_and_successive(question, expected):
    assert _solver_answer(question) == expected


# --- Discount percent from marked & selling prices ----------

@pytest.mark.parametrize("question,expected", [
    ("The marked price of a phone is Rs 18000 and it is "
     "sold for Rs 15300. Find the discount percent.", "15%"),
    ("A toy marked at Rs 250 is sold for Rs 200. Find the "
     "discount percent.", "20%"),
    ("If the marked price of a radio is Rs 560 and the "
     "selling price is Rs 504, find the discount percent.",
     "10%"),
])
def test_discount_percent(question, expected):
    assert _solver_answer(question) == expected


# --- Mark-up over cost price --------------------------------

@pytest.mark.parametrize("question,expected", [
    ("A shopkeeper buys an article for Rs 500 and marks it "
     "20% above the cost price. Find the marked price.",
     "Rs 600"),
    ("The cost price of a chair is Rs 750. The shopkeeper "
     "marks it at 40% above the cost price and then gives "
     "a discount of 10%. Find the selling price.", "Rs 945"),
    ("An article is marked at Rs 900. It is sold at a "
     "discount of 10%. If its cost price is Rs 700, find "
     "the profit percent.", "15.7143%"),
])
def test_markup_family(question, expected):
    assert _solver_answer(question) == expected


# --- Profit & loss ------------------------------------------

@pytest.mark.parametrize("question,expected", [
    ("A man buys a watch for Rs 450 and sells it for "
     "Rs 540. Find his profit percent.", "20%"),
    ("Rita bought a pen for Rs 60 and sold it for Rs 51. "
     "Find her loss percent.", "15%"),
    # SP stated before the CP.
    ("The selling price of an article is Rs 616 and the "
     "cost price is Rs 560. Find the profit percent.", "10%"),
    ("A grocer buys rice for Rs 2400 and sells it for "
     "Rs 2160. Find the loss percent.", "10%"),
    # Profit stated as a rupee amount, percent asked.
    ("Meena purchased a dress for Rs 1200 and sold it at a "
     "profit of Rs 180. Find her profit percent.", "15%"),
    # SP from CP and a profit/loss percent.
    ("The cost price of a bicycle is Rs 3200. It is sold "
     "at a profit of 12%. Find the selling price.",
     "Rs 3584"),
    # Was answered "99.3043%" before Wave 78: the buys/sells
    # chain read the 8 in "loss of 8%" as the selling price.
    ("A trader buys a fan for Rs 1150 and sells it at a "
     "loss of 8%. What is the selling price?", "Rs 1058"),
    ("Find the selling price of an article whose cost "
     "price is Rs 840, if it is sold at a gain of 25%.",
     "Rs 1050"),
    # CP from SP and a profit/loss percent.
    ("An article is sold for Rs 990 at a profit of 10%. "
     "Find its cost price.", "Rs 900"),
    ("A shopkeeper sells a table for Rs 1365 at a loss of "
     "9%. Find the cost price of the table.", "Rs 1500"),
])
def test_profit_loss_family(question, expected):
    assert _solver_answer(question) == expected


# --- Hinglish discount regressions (Wave 77) ----------------

@pytest.mark.parametrize("question,expected", [
    ("800 rs wali cheez par 25% ki chhoot hai, final price "
     "batao?", "Rs 600"),
    ("650 rs wali cheez par 10% ki chhoot hai, final price "
     "batao?", "Rs 585"),
    ("450 rs wali cheez par 40% ki chhoot hai, final price "
     "batao?", "Rs 270"),
    ("750 rs wali cheez par 20% ki chhoot hai, final price "
     "bataao?", "Rs 600"),
    ("500 rs wali cheez par 20% ki chhoot hay, kitnah dena "
     "hogah?", "Rs 400"),
    ("1200 rs wali cheez par 30% ki chhoot hay, kitnah dena "
     "hogah?", "Rs 840"),
    ("ek dukaan par 1200 rs ka joota rakha tha, sale me "
     "uspar 30% ki chhoot mili aur dukaan par lambi line "
     "thi, joota kitne me milega?", "Rs 840"),
])
def test_hinglish_discount_regressions(question, expected):
    assert _solver_answer(question) == expected


# --- Guards ---------------------------------------------------

def test_gibberish_still_one_line_not_found():
    result = _solve_friendly("asdfgh qwerty banana "
                             "helicopter zzz")
    assert result.get("fallback_kind") == "not_found"


def test_discount_without_price_still_not_found():
    # A discount percent with no price anywhere must not
    # be guessed into an answer.
    result = _solve_friendly(
        "There is a discount of 15% in the shop today. "
        "Tell me the selling price please.")
    assert result.get("fallback_kind") is not None
