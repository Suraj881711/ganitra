"""Wave 128: FUNCTION GRAPHS & GENERAL DIAGRAMS.

Wave 86 (figures.py) draws verified mensuration figures.
Wave 128 extends the same discipline to the pictures the
big AIs draw and Ganitra could not (graphs.py, hand-built
SVG, no libraries):

1. FUNCTION GRAPHS when the student asks ("graph banao",
   "plot karo", "draw the graph of..."): linear, quadratic
   (roots/vertex/intercepts from SymPy, marked only when
   exact), cubic, sin/cos, modulus, reciprocal.
2. COORDINATE figures when asked: points, a line through
   two points, a triangle from three points.
3. A NUMBER LINE for a linear-inequality solution when
   asked — attached to the solver's own inequality answer
   only when the re-solved bound matches it, or built as
   the answer when the solver missed the request.
4. STATISTICS charts from data stated in the question:
   bar graph, pie chart — only when asked, only with the
   data present.

The correctness law is Wave 86's: a figure is generated
from the same numbers the answer uses and cross-checked;
anything unsupported or ambiguous leaves the answer
byte-identical with NO figure. A plain solve never gets
a graph forced on it (Suraj's on-demand style).

Pins stay ?v=43 / ganitra-static-v20: the chat card
already renders result.figure (Wave 86), so no template
or CSS change was needed.
"""
import math
import re

import pytest

import graphs
from api import _solve_friendly


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig128")
    for k in ("GANITRA_GEMINI_API_KEY", "GEMINI_API_KEY",
              "GOOGLE_API_KEY", "GANITRA_GROQ_API_KEY",
              "GROQ_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def _fig(question):
    r = _solve_friendly(question)
    assert r.get("figure"), r
    return r


# --- 1. Trigger battery: the ask produces a figure ----------

@pytest.mark.parametrize("q", [
    "draw the graph of y = x^2",
    "draw the graph of y = x^2 - 4x + 3",
    "y = 2x + 3 ka graph banao",
    "draw the graph of sin x",
    "draw the graph of y = cos x",
    "draw the graph of y = |x|",
    "y = 1/x ka graph banao",
    "draw the graph of y = x^3",
    "ग्राफ बनाओ y = x^2 का",
    "plot the points (2, 3) and (4, 5)",
    "draw a line through points (1, 2) and (3, 6)",
    "draw a triangle with vertices (0, 0), (4, 0) and (0, 3)",
    "x > 3 ko number line par dikhao",
    "make a bar graph for runs: A 10, B 20, C 15",
    "draw a bar graph: Maths 40, English 30, Science 25",
    "draw a pie chart for: A 50%, B 30%, C 20%",
    "draw a pie chart for fruits: Mango 30, Apple 20, Banana 50",
])
def test_graph_asks_get_figures(q):
    r = _fig(q)
    assert "<svg" in r["figure"]["svg"]
    assert r["figure"]["caption"]


def test_quadratic_steps_carry_exact_roots():
    r = _fig("draw the graph of y = x^2 - 4x + 3")
    joined = " ".join(r["steps"])
    assert "x = 1" in joined and "x = 3" in joined
    assert "(2, -1)" in joined          # the vertex


def test_hindi_graph_answer_is_hindi():
    r = _fig("y = 2x + 3 ka graph banao")
    assert "ग्राफ" in r["answer"]


def test_line_through_points_answer():
    r = _fig("draw a line through points (1, 2) and (3, 6)")
    assert "y = 2·x" in r["answer"]


def test_number_line_answer():
    r = _fig("x > 3 ko number line par dikhao")
    assert r["answer"] == "x > 3"
    assert r["figure"]["caption"] == "Number line: x > 3"


def test_matplotlib_plot_is_superseded_by_svg():
    # "plot y = 2x + 3" reaches the router's matplotlib
    # plotter; the card must show ONE graph — the verified
    # SVG — and the PNG key must be gone.
    r = _fig("plot y = 2x + 3")
    assert "image" not in r
    assert r["figure"]["caption"] == "Graph of y = 2·x + 3"


# --- 2. SVG correctness: plotted points vs true values ------

def _axis_maps(svg):
    """Rebuild the data->pixel maps from the SVG's OWN
    tick labels, so the check below trusts nothing but
    what the student sees."""
    xt = re.findall(
        r'<text x="([\d.]+)" y="288\.0"[^>]*>([^<]+)</text>',
        svg)
    yt = re.findall(
        r'<text x="33\.0" y="([\d.]+)"[^>]*>([^<]+)</text>',
        svg)
    assert len(xt) >= 2 and len(yt) >= 2
    (px1, v1), (px2, v2) = ((float(xt[0][0]), float(xt[0][1])),
                            (float(xt[-1][0]),
                             float(xt[-1][1])))
    # y tick labels are baselined 3.5px below their
    # gridline (text centring) — undo that offset.
    (py1, w1), (py2, w2) = ((float(yt[0][0]) - 3.5,
                             float(yt[0][1])),
                            (float(yt[-1][0]) - 3.5,
                             float(yt[-1][1])))

    def to_data(px, py):
        x = v1 + (px - px1) * (v2 - v1) / (px2 - px1)
        y = w1 + (py - py1) * (w2 - w1) / (py2 - py1)
        return x, y

    y_span = abs(w2 - w1)
    return to_data, y_span


def _curve_points(svg):
    paths = re.findall(
        r'<path d="([^"]+)" fill="none" '
        r'stroke="#2f7d6e"[^/]*/>', svg)
    pts = []
    for d in paths:
        for x, y in re.findall(
                r'[ML] ([\d.]+) ([\d.]+)', d):
            pts.append((float(x), float(y)))
    return pts


def _check_curve(svg, f):
    to_data, y_span = _axis_maps(svg)
    pts = _curve_points(svg)
    assert len(pts) >= 40
    tol = y_span / 260.0 * 3.5      # ~3.5 px of slack
    for px, py in pts:
        x, y = to_data(px, py)
        assert abs(f(x) - y) <= tol, (x, y, f(x))


def test_quadratic_svg_points_are_true():
    r = _fig("draw the graph of y = x^2 - 4x + 3")
    _check_curve(r["figure"]["svg"],
                 lambda x: x * x - 4 * x + 3)


def test_linear_svg_points_are_true():
    r = graphs.graph_result("draw the graph of y = 2x + 3",
                            False)
    _check_curve(r["figure"]["svg"], lambda x: 2 * x + 3)


def test_quadratic_markers_at_roots_and_vertex():
    r = _fig("draw the graph of y = x^2 - 4x + 3")
    svg = r["figure"]["svg"]
    to_data, _ = _axis_maps(svg)
    dots = [(float(a), float(b)) for a, b in re.findall(
        r'<circle cx="([\d.]+)" cy="([\d.]+)" r="3\.4" '
        r'fill="#b3541e"', svg)]
    data = [to_data(px, py) for px, py in dots]
    for want in ((1, 0), (3, 0), (2, -1)):
        assert any(abs(x - want[0]) < 0.2
                   and abs(y - want[1]) < 0.2
                   for x, y in data), (want, data)


def test_trig_svg_has_pi_ticks_and_a_wave():
    r = _fig("draw the graph of sin x")
    svg = r["figure"]["svg"]
    assert ">π<" in svg and ">-π<" in svg
    assert len(_curve_points(svg)) >= 80


def test_reciprocal_svg_has_two_branches():
    r = graphs.graph_result("draw the graph of y = 1/x",
                            False)
    svg = r["figure"]["svg"]
    paths = re.findall(r'<path d="[^"]+" fill="none" '
                       r'stroke="#2f7d6e"', svg)
    assert len(paths) == 2          # one per branch
    assert 'stroke-dasharray' in svg  # the asymptote


def test_bar_chart_heights_are_proportional():
    r = _fig("make a bar graph for runs: A 10, B 20, C 15")
    svg = r["figure"]["svg"]
    bars = [(float(h), fill) for h, fill in re.findall(
        r'<rect x="[\d.]+" y="[\d.]+" width="[\d.]+" '
        r'height="([\d.]+)" fill="(#[0-9a-f]{6})"', svg)]
    heights = [h for h, _ in bars]
    assert len(heights) == 3
    assert abs(heights[1] / heights[0] - 2.0) < 0.03
    assert abs(heights[2] / heights[0] - 1.5) < 0.03
    for v in ("10", "20", "15"):
        assert f">{v}<" in svg


def test_pie_first_slice_is_a_half():
    r = _fig("draw a pie chart for: A 50%, B 30%, C 20%")
    svg = r["figure"]["svg"]
    m = re.search(
        r'<path d="M ([\d.]+) ([\d.]+) L ([\d.]+) ([\d.]+) '
        r'A [\d.]+ [\d.]+ 0 (\d) 1 ([\d.]+) ([\d.]+) Z"',
        svg)
    assert m, svg[:400]
    cx, cy = float(m.group(1)), float(m.group(2))
    ex, ey = float(m.group(6)), float(m.group(7))
    # 50% of the circle from the top lands at the bottom.
    assert abs(ex - cx) < 1.6 and abs(ey - (cy + 96)) < 1.6
    assert "50%" in svg and "30%" in svg and "20%" in svg


def test_number_line_marks_the_bound():
    r = graphs.graph_result("x > 3 ko number line par "
                            "dikhao", True)
    svg = r["figure"]["svg"]
    assert 'fill="#ffffff"' in svg      # open circle
    assert ">3<" in svg                 # the bound label
    assert 'stroke-width="4"' in svg    # the shaded ray


# --- 3. Attach path: cross-checked or nothing ---------------

def test_inequality_attach_matches_solver_bound():
    fig = graphs.graph_figure_for(
        "2x - 4 > 6 number line par dikhao",
        {"op": "inequality",
         "answer": "Interval.open(5, oo)",
         "steps": ["2x - 4 > 6", "x > 5"]})
    assert fig and fig["caption"] == "Number line: x > 5"


def test_inequality_attach_refuses_a_mismatch():
    fig = graphs.graph_figure_for(
        "2x - 4 > 6 number line par dikhao",
        {"op": "inequality",
         "answer": "Interval.open(9, oo)",
         "steps": ["x > 9"]})
    assert fig is None


def test_distance_attach_recomputes_the_distance():
    q = "plot the points and find distance between " \
        "(1, 2) and (4, 6)"
    fig = graphs.graph_figure_for(
        q, {"op": "distance", "answer": "5", "steps": []})
    assert fig and "(1, 2)" in fig["caption"]
    fig = graphs.graph_figure_for(
        q, {"op": "distance", "answer": "7", "steps": []})
    assert fig is None


# --- 4. Vetoes: no ask / no support -> no graph -------------

def test_plain_solve_gets_no_graph():
    r = _solve_friendly("solve 2x + 3 = 7")
    assert r["answer"] == "x = 2"
    assert "figure" not in r


def test_inequality_without_ask_gets_no_number_line():
    r = _solve_friendly("solve the inequality 2x - 4 > 6")
    assert r["op"] == "inequality"
    assert "figure" not in r


def test_distance_without_ask_gets_no_figure():
    r = _solve_friendly(
        "find distance between points (1, 2) and (4, 6)")
    assert r["answer"] == "5"
    assert "figure" not in r


def test_roots_solve_gets_no_graph():
    r = _solve_friendly(
        "find the roots of x^2 - 4x + 3")
    assert "figure" not in r


def test_mensuration_figure_stays_wave86():
    r = _fig("find the area of a rectangle whose length "
             "is 12 cm and breadth is 5 cm")
    assert r["figure"]["caption"].startswith("Rectangle:")


@pytest.mark.parametrize("q", [
    "draw the graph of y = tan x",
    "draw the graph of y = e^x",
    "plot y = sqrt(x)",
    "draw the graph of y = log x",
    "draw a bar graph",                    # no data
    "draw a pie chart for the class",      # no data
])
def test_unsupported_or_dataless_asks_get_no_figure(q):
    r = _solve_friendly(q)
    assert "figure" not in r
    assert graphs.graph_result(q, False) is None


def test_mixed_solve_and_graph_ask_is_not_hijacked():
    # A solve verb in the question keeps the graph layer
    # out entirely (the documented Wave 128 boundary).
    assert graphs.graph_result(
        "solve 2x + 3 = 7 and draw its graph",
        False) is None
    assert graphs.graph_result(
        "find the graph of y = x^2", False) is None


def test_chart_reading_question_is_not_redrawn():
    assert graphs.graph_result(
        "the bar graph shows runs: A 10, B 20 — how many "
        "more runs did B score than A", False) is None


def test_entry_points_never_raise_on_junk():
    for junk in ("", "graph", "plot ((", "y = ", None):
        assert graphs.graph_result(junk, False) is None
        assert graphs.graph_figure_for(
            junk, {"op": "graph"}) is None
        assert graphs.graph_upgrade(
            junk, {"op": "equation"}) is None


def test_constructed_answers_have_no_raw_markup():
    # SVG safety law (figures.py): only formatted numbers,
    # validated labels and fixed words are interpolated.
    r = graphs.graph_result(
        "draw a bar graph: A<script> 10, B 20", False)
    assert r is None or "<script>" not in r["figure"]["svg"]
