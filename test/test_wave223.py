"""Wave 223: regression tests (44) -- multipart splitter (J9).

A question that asks TWO things about ONE shape must be
served with BOTH answers, each with its working line, and
in the order the question asked them.  Tests 1-3 are the
Deploy-65 live check, run through the full router; the
rest cover the module directly, its splitter, its
declines, and the single-ask answers that must not change.
"""

from api import solve_friendly
from solver.multipart223 import solve_multipart223, split_multipart223
from solver.router import solve_question


def _full(result):
    return " ".join([result.get("answer", "")] +
                     [str(s) for s in result.get("steps", [])])


# --- Deploy-65 live check, through the full router (3) ---


def test_live_rectangle_full_pipeline():
    result = solve_question(
        "Find the area and perimeter of a rectangle "
        "with length 8 cm and breadth 5 cm")
    text = _full(result)
    assert "40" in text
    assert "26" in text


def test_live_circle_full_pipeline():
    result = solve_question(
        "Find the circumference and area of a circle "
        "with radius 7 cm")
    text = _full(result)
    assert "44" in text
    assert "154" in text


def test_live_unit_conversion_unchanged():
    result = solve_question("3 ghante me kitne minute")
    assert result["answer"] == "180 minute"
    assert "0 hours" not in _full(result)


# --- Rectangle, through the module directly (6) ---


def test_rectangle_direct():
    result = solve_multipart223(
        "Find the area and perimeter of a rectangle "
        "with length 8 cm and breadth 5 cm")
    assert result["answer"] == "Area = 40 cm\u00b2\nPerimeter = 26 cm"


def test_rectangle_reversed_order():
    result = solve_multipart223(
        "Find the perimeter and area of a rectangle "
        "with length 6 cm and breadth 4 cm")
    assert result["answer"] == "Perimeter = 20 cm\nArea = 24 cm\u00b2"


def test_rectangle_decimal_dims():
    result = solve_multipart223(
        "Find the area and perimeter of a rectangle "
        "with length 4.5 cm and breadth 2 cm")
    assert result["answer"] == "Area = 9 cm\u00b2\nPerimeter = 13 cm"


def test_rectangle_hinglish():
    result = solve_multipart223(
        "Aayat ki lambai 8 cm aur chaudai 5 cm hai, "
        "kshetrafal aur parimap nikalo")
    assert result["answer"] == "Area = 40 cm\u00b2\nPerimeter = 26 cm"


def test_rectangle_without_unit():
    result = solve_multipart223(
        "Find the area and perimeter of a rectangle "
        "with length 8 and breadth 5")
    assert "40" in result["answer"]
    assert "26" in result["answer"]


def test_rectangle_split_parts():
    assert split_multipart223(
        "Find the area and perimeter of a rectangle "
        "with length 8 cm and breadth 5 cm") == [
        "area of a rectangle with length 8 cm and breadth 5 cm",
        "perimeter of a rectangle with length 8 cm and breadth 5 cm",
    ]


# --- Circle, through the module directly (6) ---


def test_circle_direct():
    result = solve_multipart223(
        "Find the circumference and area of a circle "
        "with radius 7 cm")
    assert result["answer"] == "Circumference = 44 cm\nArea = 154 cm\u00b2"


def test_circle_reversed_order():
    result = solve_multipart223(
        "Find the area and circumference of a circle "
        "with radius 7 cm")
    assert result["answer"] == "Area = 154 cm\u00b2\nCircumference = 44 cm"


def test_circle_diameter():
    result = solve_multipart223(
        "Find the circumference and area of a circle "
        "with diameter 14 cm")
    assert result["answer"] == "Circumference = 44 cm\nArea = 154 cm\u00b2"


def test_circle_small_radius():
    result = solve_multipart223(
        "Find the circumference and area of a circle "
        "with radius 3.5 cm")
    assert result["answer"] == "Circumference = 22 cm\nArea = 38.5 cm\u00b2"


def test_circle_hinglish():
    result = solve_multipart223(
        "Vritt ki trijya 7 cm hai, paridhi aur kshetrafal nikalo")
    assert result["answer"] == "Circumference = 44 cm\nArea = 154 cm\u00b2"


def test_circle_split_parts():
    assert split_multipart223(
        "Find the circumference and area of a circle "
        "with radius 7 cm") == [
        "circumference of a circle with radius 7 cm",
        "area of a circle with radius 7 cm",
    ]


# --- Square (4) ---


def test_square_direct():
    result = solve_multipart223(
        "Find the area and perimeter of a square with side 5 cm")
    assert result["answer"] == "Area = 25 cm\u00b2\nPerimeter = 20 cm"


def test_square_side_9():
    result = solve_multipart223(
        "Find the area and perimeter of a square with side 9 cm")
    assert result["answer"] == "Area = 81 cm\u00b2\nPerimeter = 36 cm"


def test_square_reversed():
    result = solve_multipart223(
        "Find the perimeter and area of a square with side 4 cm")
    assert result["answer"] == "Perimeter = 16 cm\nArea = 16 cm\u00b2"


def test_square_split_parts():
    assert split_multipart223(
        "Find the area and perimeter of a square with side 5 cm") == [
        "area of a square with side 5 cm",
        "perimeter of a square with side 5 cm",
    ]


# --- Cuboid (3) ---


def test_cuboid_direct():
    result = solve_multipart223(
        "Find the volume and surface area of a cuboid "
        "with length 2 cm, breadth 3 cm and height 4 cm")
    assert result["answer"] == "Volume = 24 cm\u00b3\nSurface area = 52 cm\u00b2"


def test_cuboid_reversed():
    result = solve_multipart223(
        "Find the surface area and volume of a cuboid "
        "with length 2 cm, breadth 3 cm and height 4 cm")
    assert result["answer"] == "Surface area = 52 cm\u00b2\nVolume = 24 cm\u00b3"


def test_cuboid_split_parts():
    assert split_multipart223(
        "Find the volume and surface area of a cuboid "
        "with length 2 cm, breadth 3 cm and height 4 cm") == [
        "volume of a cuboid with length 2 cm, "
        "breadth 3 cm and height 4 cm",
        "surface area of a cuboid with length 2 cm, "
        "breadth 3 cm and height 4 cm",
    ]


# --- Cube (3) ---


def test_cube_direct():
    result = solve_multipart223(
        "Find the volume and surface area of a cube with side 3 cm")
    assert result["answer"] == "Volume = 27 cm\u00b3\nSurface area = 54 cm\u00b2"


def test_cube_reversed():
    result = solve_multipart223(
        "Find the surface area and volume of a cube with side 2 cm")
    assert result["answer"] == "Surface area = 24 cm\u00b2\nVolume = 8 cm\u00b3"


def test_cube_split_parts():
    assert split_multipart223(
        "Find the volume and surface area of a cube with side 3 cm") == [
        "volume of a cube with side 3 cm",
        "surface area of a cube with side 3 cm",
    ]


# --- Declines: the module must return None (10) ---


def test_single_area_returns_none():
    assert solve_multipart223(
        "Find the area of a rectangle with length 8 cm "
        "and breadth 5 cm") is None


def test_single_circumference_returns_none():
    assert solve_multipart223(
        "Find the circumference of a circle with radius 7 cm") is None


def test_unit_conversion_returns_none():
    assert solve_multipart223("3 ghante me kitne minute") is None


def test_plain_arithmetic_returns_none():
    assert solve_multipart223("Find 2 + 3 and 4 + 5") is None


def test_comparison_returns_none():
    assert solve_multipart223(
        "Which is bigger, the area or the perimeter of a "
        "rectangle with length 8 cm and breadth 5 cm?") is None


def test_sector_returns_none():
    assert solve_multipart223(
        "Find the area and circumference of a sector "
        "of a circle with radius 7 cm") is None


def test_missing_dimensions_returns_none():
    assert solve_multipart223(
        "Find the area and perimeter of a rectangle") is None


def test_three_asks_returns_none():
    assert solve_multipart223(
        "Find the area, perimeter and volume of a rectangle "
        "with length 8 cm and breadth 5 cm") is None


def test_unsupported_pair_returns_none():
    assert solve_multipart223(
        "Find the area and volume of a rectangle "
        "with length 8 cm and breadth 5 cm") is None


def test_split_empty_for_single_ask():
    assert split_multipart223(
        "Find the area of a circle with radius 7 cm") == []


# --- Router: single-ask answers must not change (9) ---


def test_single_rectangle_area_unchanged():
    result = solve_question(
        "Find the area of a rectangle with length 8 cm "
        "and breadth 5 cm")
    assert "40" in _full(result)


def test_single_circle_circumference_unchanged():
    result = solve_question(
        "Find the circumference of a circle with radius 7 cm")
    assert "44" in _full(result)


def test_single_circle_area_unchanged():
    result = solve_question(
        "Find the area of a circle with radius 7 cm")
    assert "154" in _full(result)


def test_simple_arithmetic_unchanged():
    result = solve_question("2 + 3")
    assert "5" in result["answer"]


def test_single_rectangle_perimeter_unchanged():
    result = solve_question(
        "Find the perimeter of a rectangle with length 8 cm "
        "and breadth 5 cm")
    assert "26" in _full(result)


def test_single_square_area_unchanged():
    result = solve_question(
        "Find the area of a square with side 5 cm")
    assert "25" in _full(result)


def test_chat_rectangle_multipart():
    result = solve_friendly(
        "Find the area and perimeter of a rectangle "
        "with length 8 cm and breadth 5 cm")
    text = _full(result)
    assert "40" in text
    assert "26" in text


def test_chat_circle_multipart():
    result = solve_friendly(
        "Find the circumference and area of a circle "
        "with radius 7 cm")
    text = _full(result)
    assert "44" in text
    assert "154" in text


def test_router_rectangle_other_dims():
    result = solve_question(
        "Find the area and perimeter of a rectangle "
        "with length 10 cm and breadth 3 cm")
    text = _full(result)
    assert "30" in text
    assert "26" in text
