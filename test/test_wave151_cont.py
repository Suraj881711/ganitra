"""Wave 151 continuation (Suraj, 19 Nov 2026): wrong-serve
families from a FRESH book sweep — 624 extraction-reliable
rows from ganitra-book-questions.jsonl across 13 boards,
excluding the Boards 5/6 pool the 591 calibration measured
and the Wave 153 sample. 227 serves were adjudicated by
hand / SymPy recomputation: 48 correct, 18 partial,
7 unverifiable, 154 wrong. This battery pins the fixes:

Method fixes (solver/geometry.py):
 * polygon_diagonals serves only on a diagonals-count ask
   (it fired on ANY diagonal mention: rectangle area asks,
   statements, why-questions — serving 0 or 2).
 * equilateral side-from-perimeter: "perimeter is 12.9,
   find each side" divided (4.3) instead of multiplying
   (38.7); multi-perimeter lists stay silent.

Veto rules (fallback._w151c_veto, W45-W64, wired into
_is_real, the multipart / formats / graph seams, and —
new — the salvage return and the deep-solve stage, which
judge against stripped candidates and could resurrect a
vetoed serve):
 * W45 log-letter soup (g·l·o as factors)
 * W46 word-letter / option-label / ¸-glyph product soup
 * W47 diagonals serve without a diagonals ask
 * W48 ratio echo on a derived-quantity ask
 * W49/W49b statistics harvest dropped an unknown token /
   stated-statistic mismatch
 * W50 split thousands / decimal commas, mis-OCR decimals
 * W51 year column harvested as data
 * W52 probability complement / multi-toss / lone-part
 * W53 angle-sum factoid on statements / mensuration asks
 * W54 MCQ non-answers and options solved as equations
 * W55 identity-only evaluate on yes/no / operation asks
 * W56 HCF/LCM given-value echoes
 * W57 mean deviation asked, mean served
 * W58 complement comparison served the equal value
 * W59 speed-for-distance / distance-for-time serves
 * W60 sector area served for a cone ask
 * W61 sphere volume computed forward, radius asked
 * W62 remaining-sheet ask served the removed part
 * W63 equilateral perimeter served for a rectangle ask
 * W64 perimeter sum served on an equilateral side ask

Controls: the sweep's correct serves (result-dict level)
and live geometry controls must keep serving.
"""

import pytest

from api import _solve_friendly
from fallback import _w151c_veto
from solver.geometry import solve_geometry


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    """Fresh DB per test (the live bank must never
    replay a stored answer inside this battery) and
    no AI keys."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def _served(result):
    return (isinstance(result, dict)
            and result.get("fallback_kind") is None
            and not result.get("fallback")
            and bool((result.get("answer") or "").strip()))


def _res(answer, op="", steps=(), **kw):
    r = {"answer": answer, "op": op, "steps": list(steps)}
    r.update(kw)
    return r


# ---------------------------------------------------------------------------
# Pipeline pins: the sweep's wrong serves must no longer
# be served (the two method fixes serve correctly).
# ---------------------------------------------------------------------------

PIPELINE_DECLINES = {
    # W45 log-letter soup (Assam Cl 9 log values)
    "log_values_soup":
        "Find the values– (i) log66 (ii) log0.40.4 "
        "(iii) log100.1 (iv) log10010 (v) log4256",
    # W47 diagonals on a why-question (Kerala Cl 8)
    "diagonal_why":
        "The diagonal of a quadrilateral splits it into "
        "two triangles as shown below: Do these triangles "
        "have the same angles? Why?",
    # W48 ratio echo (TN Cl 6 ratio share)
    "ratio_share_echo":
        "In a family, the amount spent in a month for "
        "buying Provisions and Vegetables are in the "
        "ratio 3 : 2. If the allotted amount is `4000, "
        "then what will be the amount spent for "
        "(i) Provisions and (ii) Vegetables?",
    # W49b stated median, unknown asked (Bihar Cl 9)
    "stated_median_unknown":
        "निम्नलिखित प्रेक्षणों को आरोही क्रम में व्यवस्थित "
        "किया गया है। यदि आंकड़ों का माध्यक 63 हो, तो ग "
        "का मान ज्ञात कीजिए : 29ए 32ए 48ए 50ए गए ग ़ 2ए "
        "72ए 78ए 84ए 95",
    # W52 multi-toss probability (Maharashtra Cl 11)
    "coin_four_tosses":
        "If a fair coin is tossed 4 times, find the "
        "probability that it shows (i) 3 heads, (ii) head "
        "in the first 2 tosses and tail in last 2 tosses.",
    # W53 angle-sum on a theorem statement (Chhattisgarh)
    "exterior_angle_statement":
        "If any one side of a triangle is extended, the "
        "exterior angle so formed is equal to the sum of "
        "the interior opposite angles.",
    # W56 LCM ask served the given HCF (Chhattisgarh Cl 6)
    "lcm_hcf_echo":
        "दो संख्याएँ 24 एवं 36 है यदि उनका म.स. 12 हो तो "
        "उनका ल. स. ज्ञात कीजिए?",
    # W62 remaining sheet served the outer circle (UK Cl 7)
    "remaining_sheet":
        "From a circular sheet of radius 4 cm, a circle "
        "of radius 3 cm is removed. Find the area of the "
        "remaining sheet. (Take π = 3.14)",
    # W63/W64 equilateral serves on other shapes' asks
    "equilateral_multi_perimeter":
        "Find the side of an equilateral triangle, if "
        "the perimeter is : @ 45cm @) 69mm @i) = 117cem",
}


@pytest.mark.parametrize("key", sorted(PIPELINE_DECLINES))
def test_wave151c_wrong_serves_now_decline(key):
    r = _solve_friendly(PIPELINE_DECLINES[key], lang=None,
                        student_class=9)
    assert not _served(r), (
        f"{key} still served: "
        f"{(r.get('answer') or '')[:120]}")


def test_wave151c_equilateral_side_from_perimeter():
    r = _solve_friendly(
        "The perimeter of an equilateral triangle is "
        "12.9 centimetres. What is the length of each "
        "side?", lang=None, student_class=7)
    assert _served(r)
    assert (r.get("answer") or "").strip() == "4.3"


# ---------------------------------------------------------------------------
# Geometry route controls: the fixed branches still
# serve their genuine asks.
# ---------------------------------------------------------------------------

def test_geometry_diagonals_ask_still_serves():
    r = solve_geometry("How many diagonals does a "
                       "hexagon have?")
    assert r and r.get("op") == "polygon_diagonals"
    assert r.get("answer") == "9"


def test_geometry_equilateral_perimeter_still_serves():
    r = solve_geometry("The side of an equilateral "
                       "triangle is 9 cm. Find its "
                       "perimeter.")
    assert r and r.get("op") == "equilateral_perimeter"
    assert r.get("answer") == "27"


def test_geometry_equilateral_side_still_serves():
    r = solve_geometry("The perimeter of an equilateral "
                       "triangle is 24 cm. Find the side.")
    assert r and r.get("op") == \
        "equilateral_side_from_perimeter"
    assert r.get("answer") == "8"


def test_geometry_diagonal_given_not_a_diagonals_ask():
    r = solve_geometry(
        "Find the area and the perimeter of the "
        "rectangle whose length is 15cm and the length "
        "of one diagonal is 17cm.")
    assert not r or r.get("op") != "polygon_diagonals"


# ---------------------------------------------------------------------------
# Direct veto pins, one per rule.
# ---------------------------------------------------------------------------

def test_w45_log_letter_soup_vetoes():
    r = _res("(i) 66·g·l·o; (ii) 0", op="multipart_general",
             steps=["(i) Evaluate 66·g·l·o using "
                    "exponent/log rules."])
    assert _w151c_veto("Find the values– (i) log66 "
                       "(ii) log0.40.4", r)


def test_w46_word_letter_product_vetoes():
    r = _res("6·F·a·c·e·i·o·r·s·t·x + 45·x", op="simplify")
    assert _w151c_veto("Factorise x3 + 13x2 + 32x + 20 "
                       "into linear factors", r)


def test_w46_option_label_product_vetoes():
    r = _res("16659183057723360*a*b*c*d", op="simplify")
    assert _w151c_veto("(a) 12978 (b) 31752 (c) 17501 "
                       "(d) 2310", r)


def test_w46_division_glyph_product_vetoes():
    r = _res("9*¸*(m + 1)*(2*m - 1)", op="simplify")
    assert _w151c_veto("(2m3 + m2 + m + 9) ¸ (2m - 1)", r)


def test_w47_diagonals_without_ask_vetoes():
    r = _res("0", op="polygon_diagonals",
             steps=["A triangle has 3 sides; diagonals "
                    "= n(n - 3)/2 = 0"])
    assert _w151c_veto("A diagonal of a parallelogram "
                       "divides it into two congruent "
                       "triangles.", r)


def test_w48_ratio_echo_vetoes():
    r = _res("3 : 2", op="ratio",
             steps=["Simplest form: 3 : 2"])
    assert _w151c_veto(
        "Provisions and Vegetables are in the ratio "
        "3 : 2. If the allotted amount is 4000 rupees, "
        "how much is spent on each?", r)


def test_w48_ratio_simplest_form_kept():
    r = _res("3 : 2", op="ratio",
             steps=["Simplest form: 3 : 2"])
    assert not _w151c_veto("Express the ratio 6 : 4 in "
                           "its simplest form.", r)


def test_w49_unknown_token_in_data_vetoes():
    r = _res("33", op="mean",
             steps=["Add all values: 25 + 39 + 35 = 99",
                    "Divide by the count (3): 99 ÷ 3 = 33"])
    assert _w151c_veto(
        "नीचे दिए गए प्रेक्षणों का औसत 36 है। अज्ञात "
        "प्रेक्षण ि ज्ञात कीजिए। 25, 39, 35, ि, 46", r)


def test_w49b_stated_statistic_mismatch_vetoes():
    r = _res("50", op="median",
             steps=["Arrange in order: 2, 29, 32, 48, "
                    "50, 72, 78, 84, 95",
                    "Median = 50"])
    assert _w151c_veto(
        "यदि आंकड़ों का माध्यक 63 हो, तो ग का मान ज्ञात "
        "कीजिए : 29, 32, 48, 50, ग, 72, 78, 84, 95", r)


def test_w50a_thousands_comma_split_vetoes():
    r = _res("944.333", op="mean",
             steps=["Add all values: 2 + 825 + 2006 "
                    "= 2833"])
    assert _w151c_veto(
        "एक मशीन औसतन एक दिन में 2,825 पेंच बनाती है। "
        "जनवरी 2006 में उस मशीन ने कितने पेंच बनाए?", r)


def test_w50b_decimal_comma_split_vetoes():
    r = _res("519", op="mean",
             steps=["Add all values: 9 + 1019 + 2 + "
                    "1046 = 2076"])
    assert _w151c_veto(
        "वर्षा के आँकड़े: 880.5, 1474.9, 806.3, 1554.9, "
        "1019,2, 1046.5, 1017.2 औसत ज्ञात कीजिए।", r)


def test_w51_year_column_vetoes():
    r = _res("211.5", op="median",
             steps=["Arrange in order: 1.82, 1.85, "
                    "1960, 1964, 1968, 1972, 2.02"])
    assert _w151c_veto(
        "तालिका में ओलंपिक ऊँची कूद के आँकड़े दिए हैं। "
        "वर्ष 1960 1964 1968 1972 ऊँचाई 1.85 1.90 "
        "1.82 1.92 इनका माध्यक ज्ञात कीजिए।", r)


def test_w52a_complement_same_value_vetoes():
    r = _res("(i) 3/8 ≈ 0.3750; (ii) 3/8 ≈ 0.3750",
             op="multipart_general",
             steps=["(i) Favourable (red) = 3",
                    "(ii) Favourable (red) = 3"],
             multipart={"kind": "general"})
    assert _w151c_veto(
        "एक थैले में 3 लाल और 5 काली गेंदे हैं। गेंद "
        "निकाली जाती है। प्रायिकता क्या है कि गेंद "
        "(i) लाल हो? (ii) लाल नहीं हो?", r)


def test_w52b_multi_toss_single_template_vetoes():
    r = _res("(i) 1/2 ≈ 0.5000; (ii) 1/2 ≈ 0.5000",
             op="multipart_general",
             steps=["(i) A fair coin has 2 equally "
                    "likely outcomes; heads is 1 of "
                    "them."],
             multipart={"kind": "general"})
    assert _w151c_veto(
        "If a fair coin is tossed 4 times, find the "
        "probability that it shows (i) 3 heads, "
        "(ii) head in the first 2 tosses and tail in "
        "last 2 tosses.", r)


def test_w52c_lone_part_on_negation_multipart_vetoes():
    r = _res("3/8 ≈ 0.3750", op="probability",
             steps=["Count the balls: 3 red, 5 black",
                    "Favourable (red) = 3"])
    assert _w151c_veto(
        "एक थैले में 3 लाल और 5 काली गेंदे हैं। "
        "प्रायिकता क्या है कि गेंद (i) लाल हो? "
        "(ii) लाल नहीं हो?", r)


def test_w48b_statement_ratio_echo_vetoes():
    r = _res("10 : 3", op="ratio",
             steps=["Simplest form: 10 : 3"])
    assert _w151c_veto(
        "A ratio may be treated as a fraction, thus "
        "the ratio 10 : 3 may be treated as .", r)


def test_w52d_identical_outcome_sets_veto():
    r = _res("(a) {1, 2, 3, 4, 5, 6}; "
             "(b) {1, 2, 3, 4, 5, 6}",
             op="multipart_general",
             steps=["(a) Sample space S = {1, 2, 3, 4, "
                    "5, 6}"],
             multipart={"kind": "general"})
    assert _w151c_veto(
        "When a die is thrown, list the outcomes of "
        "an event of getting (i) (a) a prime number "
        "(b) not a prime number.", r)


def test_w52e_sample_space_on_event_ask_vetoes():
    r = _res("{1, 2, 3, 4, 5, 6}", op="w103_sample_space",
             steps=["Sample space S = {1, 2, 3, 4, 5, "
                    "6}, so n(S) = 6."])
    assert _w151c_veto(
        "When a die is thrown, list the outcomes of "
        "an event of getting a prime number.", r)


def test_w52e_sample_space_genuine_ask_kept():
    r = _res("{1, 2, 3, 4, 5, 6}", op="w103_sample_space",
             steps=["Sample space S = {1, 2, 3, 4, 5, "
                    "6}, so n(S) = 6."])
    assert not _w151c_veto(
        "Write the sample space when a die is "
        "thrown once.", r)


def test_w55b_trig_identity_vetoes():
    r = _res("900", op="evaluate",
             steps=["Evaluate: 900 = 900"])
    assert _w151c_veto(
        "Evaluate sin 60o cos 30o + sin 30o cos 60o. "
        "What is the value of sin(60o + 30o)?", r)


def test_w52c_compound_probability_serve_kept():
    # Wave 156 book_052: every part computed in one
    # compound serve — a correct answer, not a lone
    # positive part.
    r = _res("P(not A) = 0.58; P(not B) = 0.52; "
             "P(A or B) = 0.74", op="probability",
             steps=["P(not A) = 1 - P(A) = 1 - 0.42 "
                    "= 0.58"])
    assert not _w151c_veto(
        "A and B are events such that P(A) = 0.42, "
        "P(B) = 0.48 and P(A and B) = 0.16. Determine "
        "(i) P(not A), (ii) P(not B) and (iii) "
        "P(A or B)", r)


def test_w48b_hindi_write_ratio_serve_kept():
    # Wave 156 book_040: "अनुपात के रूप में लिखिए" is
    # an imperative ask — the echo-shaped serve is the
    # requested answer, not a statement carve.
    r = _res("8 : 5", op="ratio",
             steps=["Length : width = 800 : 500 = 8 : 5"])
    assert not _w151c_veto(
        "एक कमरे की लम्बाई 8 मीटर और चौड़ाई 500 "
        "सेंटीमीटर है । कमरे की लम्बाई और चौड़ाई को "
        "अनुपात के रूप में लिखिए ।", r)


def test_w53_statement_angle_sum_vetoes():
    r = _res("180°", op="w103_angle_sum",
             steps=["The three angles of a triangle "
                    "always add up to 180°."])
    assert _w151c_veto(
        "किसी त्रिभुज का बहिष्कोण दूरस्थ अन्तःकोणों के "
        "योगफल के बराबर होता है।", r)


def test_w53_stated_value_statement_kept():
    # Wave 150 controls 4142/6419/6503: a fact
    # statement that states the served value itself
    # is a designed factoid serve.
    r = _res("180°", op="w103_angle_sum",
             steps=["The three angles of a triangle "
                    "always add up to 180°."])
    assert not _w151c_veto(
        "The sum of all three interior angles of a "
        "triangle is 180°.", r)
    assert not _w151c_veto(
        "एक त्रिभुज के तीनों कोणों का योग 1800 "
        "होता है।", r)
    r360 = _res("360°", op="w103_angle_sum",
                steps=["The four angles of a "
                       "quadrilateral add up to 360°."])
    assert not _w151c_veto(
        "किसी चतुर्भुज के कोणों का योग 360° "
        "होता है।", r360)


def test_w54_genuine_equation_verdict_kept():
    # Wave 77 / test_wave150 designed serve: for a
    # genuine contradictory equation the no-variable
    # string is the answer itself.
    r = _res("The equation has no variable to solve "
             "for.", op="linear_equation",
             steps=["2x + 3 = 2x + 5 has no solution"])
    assert not _w151c_veto(
        "bhai 2x + 3 = 2x + 5 solve karo", r)


def test_w53_angle_ask_kept():
    r = _res("180°", op="w103_angle_sum",
             steps=["Sum of angles = 180°"])
    assert not _w151c_veto(
        "Find the sum of the interior angles of a "
        "triangle.", r)


def test_w54_mcq_non_answer_vetoes():
    r = _res("(1) The equation has no variable to "
             "solve for.; (2) The equation has no "
             "variable to solve for.",
             op="multipart_general",
             multipart={"kind": "general"})
    assert _w151c_veto(
        "The equation of the normal to the circle is "
        "(1) x + 2y = 3 (2) x + 2y + 3 = 0 "
        "(3) 2x + 4y + 3 = 0 (4) x − 2y + 3 = 0", r)


def test_w55_yesno_identity_vetoes():
    r = _res("100999", op="evaluate",
             steps=["Evaluate: 100999 = 100999"])
    assert _w151c_veto("Is 101000-1 divisible by both "
                       "9 and 11?", r)


def test_w55_bare_expression_kept():
    r = _res("26", op="evaluate",
             steps=["Evaluate: 26 = 26"])
    assert not _w151c_veto("5 + (3 × 7)", r)


def test_w56_lcm_ask_hcf_echo_vetoes():
    r = _res("12", op="hindi_hcf_lcm",
             steps=["HCF of 24 and 36 = 12"])
    assert _w151c_veto(
        "दो संख्याएँ 24 एवं 36 है यदि उनका म.स. 12 हो "
        "तो उनका ल. स. ज्ञात कीजिए?", r)


def test_w57_mean_deviation_vetoes():
    r = _res("10", op="mean",
             steps=["Add all values: 12 + 3 + 18 = 33"])
    assert _w151c_veto(
        "Find the mean deviation about the mean for "
        "the following data: 12, 3, 18, 17, 4, 9", r)


def test_w58_complement_comparison_vetoes():
    r = _res("45°", op="angles_equal_complement",
             steps=["Equal angles are each 90° / 2 "
                    "= 45°."])
    assert _w151c_veto(
        "An angle is greater than 45º. Is its "
        "complementary angle greater than 45º or equal "
        "to 45º or less than 45º?", r)


def test_w59_speed_for_distance_vetoes():
    r = _res("33.6 km/h", op="speed",
             steps=["Speed = 14 ÷ 0.416667 = 33.6"])
    assert _w151c_veto(
        "A loaded truck travels 14 km in 25 minutes. "
        "If the speed remains the same, how far can "
        "it travel in 5 hours?", r)


def test_w59_distance_for_time_vetoes():
    r = _res("288", op="distance",
             steps=["Distance = speed × time "
                    "= 48 × 6 = 288"])
    assert _w151c_veto(
        "A vehicle running at a speed of 48 km/hr "
        "takes 6 hours to complete the journey. How "
        "much time will be taken if its speed is "
        "72 km/hr?", r)


def test_w60_sector_for_cone_vetoes():
    r = _res("424.115", op="sector area",
             steps=["Area of a sector = (216/360) × "
                    "pi × 15^2 = 424.115"])
    assert _w151c_veto(
        "From a circle of radius 15 cm, a sector with "
        "angle 216° is cut out and its bounding radii "
        "are bent so as to form a cone. Find its "
        "volume.", r)


def test_w61_sphere_inverse_vetoes():
    r = _res("≈ 113.0973", op="volume",
             steps=["Volume = (4/3)·pi·r^3 = (4/3) × "
                    "pi × 3^3"])
    assert _w151c_veto(
        "The formula for determining the volume V of "
        "a sphere is V = 4/3 πr3. If the volume "
        "V = 15.5 cubic cm then find the radius r of "
        "the sphere.", r)


def test_w62_remaining_sheet_vetoes():
    r = _res("16·pi ≈ 50.2655 cm²", op="area",
             steps=["Area = pi·r^2 = pi × 4^2"])
    assert _w151c_veto(
        "From a circular sheet of radius 4 cm, a "
        "circle of radius 3 cm is removed. Find the "
        "area of the remaining sheet.", r)


def test_w62_remaining_correct_kept():
    r = _res("21.98 cm²", op="area",
             steps=["Remaining area = pi × 4^2 − "
                    "pi × 3^2 = 21.98"])
    assert not _w151c_veto(
        "From a circular sheet of radius 4 cm, a "
        "circle of radius 3 cm is removed. Find the "
        "area of the remaining sheet.", r)


def test_w63_equilateral_for_rectangle_vetoes():
    r = _res("6", op="equilateral_perimeter",
             steps=["All three sides are equal: "
                    "perimeter = 3 × 2 = 6"])
    assert _w151c_veto(
        "If the sides of all equilateral triangles "
        "are 2 centimetres, what is the perimeter "
        "and area of the rectangle?", r)


def test_w64_perimeter_sum_on_side_ask_vetoes():
    r = _res("115", op="perimeter",
             steps=["Perimeter = sum of the three "
                    "sides = 45 + 69 + 1 = 115"])
    assert _w151c_veto(
        "Find the side of an equilateral triangle, "
        "if the perimeter is: 45cm, 69mm, 117cm", r)


# ---------------------------------------------------------------------------
# False-positive battery: the sweep's CORRECT serves at
# result-dict level must not be vetoed.
# ---------------------------------------------------------------------------

CORRECT_SERVES = [
    # direction cosines
    ("Find the direction cosines of the vector joining "
     "A (1, 2, -3) and B(-1, -2, 1), directed from A "
     "to B.",
     _res("(-0.3333, -0.6667, 0.6667)",
          op="direction cosines")),
    # circle centre/radius
    ("The equation of a circle is x2 + y2 - 2x - 4y "
     "- 11 = 0. Find its centre and radius.",
     _res("Centre = (1, 2), radius = 4",
          op="circle_centre_radius")),
    # plain median with clean data
    ("Find the median of 9 observations 14, 36, 25, "
     "28, 35, 32, 56, 42, 50.",
     _res("35", op="median",
          steps=["Arrange in order: 14, 25, 28, 32, "
                 "35, 36, 42, 50, 56", "Median = 35"])),
    # plain mean with clean data
    ("Find the mean of the data; 10.25, 9, 4.75, 8, "
     "2.65, 12, 2.35",
     _res("7", op="mean",
          steps=["Add all values: 10.25 + 9 + 4.75 + "
                 "8 + 2.65 + 12 + 2.35 = 49"])),
    # HCF/LCM genuinely computed
    ("Given that HCF (306, 657) = 9, find LCM "
     "(306, 657).",
     _res("HCF = 9, LCM = 22338", op="hcf_lcm")),
    # single coin toss, 1/2 is right
    ("एक सिक्के को एक बार उछाला जाता है। एक चित "
     "प्राप्त करने की प्रायिकता ज्ञात कीजिए।",
     _res("1/2 ≈ 0.5000", op="probability",
          steps=["1 coin(s) tossed together give 2 "
                 "equally likely outcomes: H, T"])),
    # discount percent genuinely computed
    ("An article marked at 1920 is sold for 1840, "
     "what is discount and discount percentage?",
     _res("4.16667%", op="discount_percent")),
    # degree of a product of polynomials (identity
    # formatting, correct value)
    ("If p(u) = u2 + 3u + 4, q(u) = u2 + u - 12 and "
     "r(u) = u - 2, then find the degree of "
     "p(u)q(u)r(u).",
     _res("5", op="evaluate",
          steps=["Evaluate: 5 = 5"])),
    # sector area genuinely asked
    ("Find the area of a sector of a circle of "
     "radius 12 cm with angle 120°.",
     _res("150.796 cm²", op="sector area")),
    # speed genuinely asked
    ("A car covers a distance of 276.75 km in 4.5 "
     "hours. What is the average speed of the car?",
     _res("61.5 km/h", op="speed")),
]


@pytest.mark.parametrize("q,r", CORRECT_SERVES,
                         ids=[str(i) for i in
                              range(len(CORRECT_SERVES))])
def test_wave151c_correct_serves_not_vetoed(q, r):
    assert not _w151c_veto(q, r)
