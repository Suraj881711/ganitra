"""Wave 172: the sector radius + arc wrong serve.

Wave 171's known leftover: "Find the area of the sector of a
circle with radius 3.5 cm and length of arc 2.2 cm" was served
by the router as op "area", answer "38.5 cm²" — the FULL
circle's area — although the strict Wave 169 sector schema
settles it directly (1/2 x arc x radius = 77/20 = 3.85).

Root cause: the Wave 32 pre-intent geometry block in
solver/router.py (trigger includes "sector of (?:a |the
)?circle") tries solve_geometry FIRST and returns any
non-error result, ~500 lines before the failure-only gate
cluster — so neither the Wave 169 gate nor the Wave 171
fragment-hijack repair ever sees the question.  solve_geometry
has no radius + arc sector form, so it falls back to the
circle's area.

Fix (router.py, inside that block only): when the question
says "sector" and the strict tierA169 schema returns a
w169_sector* result that _w171_fragment_hijack confirms as a
fragment displacement (op "area", verifiably different
answer), serve the schema's answer.  Everything else in the
block is byte-identical behaviour.
"""
from solver.router import solve_question
from solver.tierA169 import solve_tierA169

BUG_Q = ("Find the area of the sector of a circle with "
         "radius 3.5 cm and length of arc 2.2 cm")


def _route(q):
    return solve_question(q)


# --- the fix: sector radius + arc serves 1/2 x r x l ---------

def test_bug_question_serves_sector_area_not_circle_area():
    out = _route(BUG_Q)
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "77/20", out
    assert abs(out["value"] - 3.85) < 1e-9, out


def test_sector_variant_radius6_arc11():
    out = _route("Find the area of a sector of a circle with "
                 "radius 6 cm and arc length 11 cm")
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "33", out  # 1/2 x 6 x 11


def test_sector_variant_radius14_arc22():
    out = _route("Find the area of a sector of a circle with "
                 "radius 14 cm and length of arc 22 cm")
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "154", out  # 1/2 x 14 x 22


def test_sector_variant_whose_arc_is():
    out = _route("Find the area of the sector of a circle "
                 "whose radius is 4 cm and arc is 5 cm")
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "10", out  # 1/2 x 4 x 5


def test_sector_variant_decimal_radius_arc():
    out = _route("Find the area of the sector of a circle of "
                 "radius 2.8 cm with arc length 1.1 cm")
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "77/50", out  # 1/2 x 2.8 x 1.1


def test_sector_without_of_a_circle_still_native():
    # Never matched the pre-intent trigger; the tail gate has
    # always served this one natively.  Unchanged.
    out = _route("Find the area of the sector with radius "
                 "5 cm and length of arc 10 cm")
    assert out["op"] == "w169_sector_arc_area", out
    assert out["answer"] == "25", out


# --- never displaced: correct serves stand -------------------

def test_genuine_circle_area_radius7_unchanged():
    out = _route("Find the area of a circle with radius 7 cm")
    assert out["op"] == "area", out
    assert out["answer"] == "154 cm²", out


def test_genuine_circle_area_same_numbers_as_bug_unchanged():
    # Same radius as the bug question, no sector word: the
    # full circle area 38.5 cm² is CORRECT here and stands.
    out = _route("Find the area of a circle whose radius "
                 "is 3.5 cm")
    assert out["op"] == "area", out
    assert out["answer"] == "38.5 cm²", out


def test_sector_with_angle_geometry_serve_unchanged():
    # Radius + degree angle is geometry's own correct sector
    # branch (38.5 = a quarter of 154); tierA169 declines the
    # angle form, so nothing is displaced.
    out = _route("Find the area of a sector of a circle with "
                 "radius 7 cm and angle 90 degrees")
    assert out["op"] == "sector area", out
    assert out["answer"] == "38.5", out


def test_sector_perimeter_serve_unchanged():
    # The fix displaces only the "area" fragment op; the
    # perimeter serve through this block is untouched.
    out = _route("Find the perimeter of a sector of a circle "
                 "with radius 3.5 cm and arc length 2.2 cm")
    assert out["op"] == "circumference", out
    assert out["answer"] == "22", out


def test_segment_area_unchanged():
    out = _route("Find the area of a segment of a circle "
                 "with radius 7 cm and angle 90 degrees")
    assert out["op"] == "segment area", out
    assert out["answer"] == "14 cm²", out


def test_ring_area_unchanged():
    out = _route("Find the area of a ring with outer radius "
                 "10 cm and inner radius 6 cm")
    assert out["op"] == "ring area", out
    assert out["answer"] == "201.062 square units", out


def test_circumference_unchanged():
    out = _route("Find the circumference of a circle with "
                 "radius 7 cm")
    assert out["op"] == "circumference", out
    assert out["answer"] == "44", out


# --- schema scope: tierA169 stays strict ---------------------

def test_schema_declines_genuine_circle_area():
    assert solve_tierA169(
        "Find the area of a circle whose radius is 3.5 cm"
    ) is None


def test_schema_declines_sector_angle_form():
    assert solve_tierA169(
        "Find the area of a sector of a circle with radius "
        "7 cm and angle 90 degrees") is None
