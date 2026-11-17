"""Wave 143: GRAPH SE SOLVE — graph-method solving.

Suraj's standing order (17 Nov 2026): "agar question
graph waale hai toh graph se solve karana hai" — a
graph-type question is SOLVED USING THE GRAPH, not
merely answered with a graph attached. Wave 128
(graphs.py) draws verified graphs but deliberately
vetoes mixed solve+graph asks and chart-reading
questions; Wave 143 (graphsolve.py) lifts exactly those
limits for three genuine graph-method shapes:

1. A PAIR OF LINEAR EQUATIONS by the graphical method
   ("by graphical method", "graph se hal karo", "draw
   the graph and find the solution"): both lines drawn
   from exact table points, the solution READ OFF the
   plotted intersection — computed from the drawn lines'
   own points — and served only when that read-off
   equals the algebraic solution exactly. Parallel ->
   "No solution" (the lines never meet); coincident ->
   "Infinitely many solutions" (the same line). On any
   disagreement the layer returns None and the plain
   algebraic answer stands WITHOUT the graph claim.
2. ZEROS OF A POLYNOMIAL read off its graph ("graph se
   zeros batao", "kitne zero hai graph se"): Wave 128's
   figure with intercepts marked; the zeros are the
   intercepts (sp.solve cross-checked against
   sp.real_roots, each root plugged back), count stated.
3. CHART READING with the data IN the question ("bar
   graph banao: A 10, B 20, C 15 — sabse zyada kis ka
   hai"): the chart is drawn AND the sub-question —
   sabse zyada / sabse kam / kul / do items ka antar —
   is answered from the chart data, stated as read off
   the graph.

Routing law: only an EXPLICIT graph-method phrase
routes a question here. A pair with no graph phrase
keeps its byte-identical algebraic answer; an
incidental graph mention keeps Wave 128's veto; pure
plotting asks stay Wave 128's.

Pins stay ?v=43 / ganitra-static-v20: the figure rides
the existing result.figure slot (Wave 86/128), so no
template or static change was needed.
"""
import re

import pytest

import graphsolve
from api import _solve_friendly


@pytest.fixture(autouse=True)
def _env(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig143")
    for k in ("GANITRA_GEMINI_API_KEY", "GEMINI_API_KEY",
              "GOOGLE_API_KEY", "GANITRA_GROQ_API_KEY",
              "GROQ_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(k, raising=False)


def _axis_maps(svg):
    """Rebuild the data->pixel maps from the SVG's OWN
    tick labels (Wave 128's discipline: trust nothing but
    what the student sees)."""
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
    (py1, w1), (py2, w2) = ((float(yt[0][0]) - 3.5,
                             float(yt[0][1])),
                            (float(yt[-1][0]) - 3.5,
                             float(yt[-1][1])))

    def to_data(px, py):
        x = v1 + (px - px1) * (v2 - v1) / (px2 - px1)
        y = w1 + (py - py1) * (w2 - w1) / (py2 - py1)
        return x, y

    return to_data


# --- 1. The pair, solved by its graph (chain) --------------

def test_pair_by_graphical_method_english():
    r = _solve_friendly(
        "solve the pair of linear equations x + y = 5 and "
        "x - y = 1 by graphical method")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "x = 3, y = 2"
    assert r["figure"]["svg"].startswith("<svg")
    assert r["figure"]["caption"].startswith(
        "Graphical solution of")
    assert "read off the graph" in r["steps"][-1]


def test_pair_graphical_method_se_hinglish():
    r = _solve_friendly(
        "graphical method se solve karo x + y = 5 and "
        "x - y = 1")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "x = 3, y = 2"
    assert r.get("figure")


def test_pair_draw_the_graph_and_find():
    r = _solve_friendly(
        "draw the graph and find the solution of "
        "x + y = 5 and x - y = 1")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "x = 3, y = 2"
    assert r.get("figure")


def test_pair_graph_se_hal_karo():
    r = _solve_friendly("graph se hal karo: 2x + y = 6, "
                        "x + y = 4")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "x = 2, y = 2"
    assert r.get("figure")


def test_pair_parallel_no_solution():
    r = _solve_friendly(
        "x + y = 4 and x + y = 6 graphical method se "
        "solve karo")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "No solution"
    assert "parallel" in r["figure"]["caption"]
    assert r.get("figure")


def test_pair_coincident_infinitely_many():
    r = _solve_friendly(
        "x + y = 4 and 2x + 2y = 8 ko graphical method "
        "se solve karo")
    assert r["op"] == "graph_solve"
    assert r["answer"] == "Infinitely many solutions"
    assert "same line" in r["figure"]["caption"]
    assert r.get("figure")


def test_pair_svg_lines_pass_through_the_solution():
    """The picture must not lie: BOTH lines drawn in the
    served SVG pass through the claimed solution (3, 2),
    read back off the SVG's own tick labels."""
    r = _solve_friendly(
        "solve the pair of linear equations x + y = 5 and "
        "x - y = 1 by graphical method")
    svg = r["figure"]["svg"]
    to_data = _axis_maps(svg)
    lines = re.findall(
        r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" '
        r'y2="([\d.]+)" stroke="(#[0-9a-f]+)" '
        r'stroke-width="2\.0"', svg)
    by_colour = {c: tuple(float(v) for v in vals)
                 for *vals, c in lines}
    assert "#2f7d6e" in by_colour      # line 1
    assert "#b3541e" in by_colour      # line 2
    for x1, y1, x2, y2 in by_colour.values():
        (dx1, dy1), (dx2, dy2) = to_data(x1, y1), \
            to_data(x2, y2)
        # the drawn line, evaluated at x = 3, gives y = 2
        t = (3.0 - dx1) / (dx2 - dx1)
        assert abs(dy1 + t * (dy2 - dy1) - 2.0) < 0.35


def test_pair_hindi_steps_module():
    r = graphsolve.graphsolve_result(
        "ग्राफीय विधि से हल करो x + y = 5 and x - y = 1",
        hindi=True)
    assert r is not None and r["op"] == "graph_solve"
    assert r["answer"] == "x = 3, y = 2"
    assert "ग्राफीय विधि" in r["steps"][0]


def test_pair_vertical_horizontal_module():
    r = graphsolve.graphsolve_result(
        "graphical method se solve karo x = 3 and y = 2",
        hindi=False)
    assert r is not None
    assert r["answer"] == "x = 3, y = 2"
    joined = " ".join(r["steps"])
    assert "vertical line" in joined
    assert "horizontal line" in joined


def test_pair_fraction_coefficients_module():
    r = graphsolve.graphsolve_result(
        "graphical method: x/2 + y/3 = 2 and x + y = 5",
        hindi=False)
    assert r is not None
    assert r["answer"] == "x = 2, y = 3"


# --- 2. The cross-check: the picture never lies -------------

def test_crosscheck_disagreement_module_returns_none(
        monkeypatch):
    """Force the plotted-intersection read-off to a wrong
    point: the graphical answer must be REFUSED (None),
    never served."""
    monkeypatch.setattr(
        graphsolve, "_pair_intersection_from_points",
        lambda *pts: (0, 0))
    assert graphsolve.graphsolve_result(
        "solve the pair of linear equations x + y = 5 "
        "and x - y = 1 by graphical method") is None


def test_crosscheck_disagreement_chain_keeps_algebra(
        monkeypatch):
    """Same forced disagreement through the chain: the
    plain algebraic answer stands, with NO figure and NO
    graph claim."""
    monkeypatch.setattr(
        graphsolve, "_pair_intersection_from_points",
        lambda *pts: (0, 0))
    r = _solve_friendly(
        "solve the pair of linear equations x + y = 5 "
        "and x - y = 1 by graphical method")
    assert r["op"] == "system"
    assert r["answer"] == "x = 3, y = 2"
    assert not r.get("figure")


# --- 3. Zeros read off the graph -----------------------------

def test_zeros_draw_and_find_chain():
    r = _solve_friendly(
        "draw the graph of y = x^2 - 4x + 3 and find "
        "its zeros")
    assert r["op"] == "graph_zeros"
    assert r["answer"] == "Zeros: 1, 3 (2 zeros)"
    assert r.get("figure")


def test_zeros_kitne_zero_hai_graph_se_chain():
    """Before this wave this phrasing ended at a salvage
    fragment ("-2"); now the zeros come off the graph."""
    r = _solve_friendly(
        "is polynomial ke kitne zero hai graph se: "
        "x^2 - 4x + 3")
    assert r["op"] == "graph_zeros"
    assert "1, 3" in r["answer"]
    assert r.get("figure")


def test_zeros_none_when_graph_never_cuts_chain():
    r = _solve_friendly(
        "graph se batao x^2 + 1 ke kitne zero hai")
    assert r["op"] == "graph_zeros"
    assert "(0 zeros)" in r["answer"] \
        or "(0 शून्यक)" in r["answer"]
    assert r.get("figure")


def test_zeros_repeated_root_touches_chain():
    r = _solve_friendly(
        "draw the graph of y = x^2 - 2x + 1 and find "
        "its zeros")
    assert r["op"] == "graph_zeros"
    assert r["answer"].startswith("Zeros: 1")
    assert "touches" in " ".join(r["steps"])


def test_zeros_cubic_module():
    r = graphsolve.graphsolve_result(
        "graph se zeros batao: x^3 - 6x^2 + 11x - 6",
        hindi=False)
    assert r is not None
    assert r["answer"] == "Zeros: 1, 2, 3 (3 zeros)"


def test_zeros_unsupported_function_vetoed_module():
    assert graphsolve.graphsolve_result(
        "graph se zeros batao of y = tan x") is None


# --- 4. Chart reading ----------------------------------------

def test_chart_sabse_zyada_chain():
    """Before this wave Wave 128 drew the chart and left
    the sub-question unanswered; now it is read off."""
    r = _solve_friendly(
        "bar graph banao: A 10, B 20, C 15 — sabse zyada "
        "kis ka hai")
    assert r["op"] == "graph_read"
    assert "B" in r["answer"] and "20" in r["answer"]
    assert r.get("figure")


def test_chart_who_scored_the_most_chain():
    r = _solve_friendly(
        "draw a bar graph: Maths 40, English 30, "
        "Science 25. Who scored the most?")
    assert r["op"] == "graph_read"
    assert r["answer"] == "Maths — 40 (the most)"
    assert r.get("figure")


def test_chart_antar_chain():
    r = _solve_friendly(
        "bar graph: A 10, B 20, C 15 — A aur B me kitna "
        "antar hai")
    assert r["op"] == "graph_read"
    assert "10" in r["answer"]
    assert r.get("figure")


def test_chart_pie_kul_chain():
    r = _solve_friendly(
        "pie chart banao: A 50, B 30, C 20 — kul kitna "
        "hai")
    assert r["op"] == "graph_read"
    assert "100" in r["answer"]
    assert r.get("figure")


def test_chart_how_many_more_in_head_chain():
    r = _solve_friendly(
        "the bar graph shows runs: A 10, B 20 — how many "
        "more runs did B score than A")
    assert r["op"] == "graph_read"
    assert r["answer"] == "Difference: 10"
    assert r.get("figure")


def test_chart_sabse_kam_module():
    r = graphsolve.graphsolve_result(
        "bar graph: A 10, B 20, C 15 — sabse kam kis "
        "ka hai", hindi=True)
    assert r is not None
    assert r["answer"] == "A — 10 (सबसे कम)"


def test_chart_no_data_no_reading_module():
    assert graphsolve.graphsolve_result(
        "bar graph banao — sabse zyada kis ka hai") \
        is None


# --- 5. Veto battery: non-graph questions byte-identical ----

def test_veto_plain_pair_stays_algebraic():
    r = _solve_friendly("solve x + y = 5 and x - y = 1")
    assert r["op"] == "system"
    assert r["answer"] == "x = 3, y = 2"
    assert not r.get("figure")


def test_veto_incidental_graph_mention():
    r = _solve_friendly("solve 2x + 3 = 7 and draw its "
                        "graph")
    assert r["answer"] == "x = 2"
    assert not r.get("figure")


def test_veto_pure_plot_stays_wave128():
    r = _solve_friendly("draw the graph of y = x^2 - 4x + 3")
    assert r["op"] == "graph"
    assert r["answer"] == "Graph of y = x^2 - 4·x + 3"
    assert r["figure"]["caption"] == \
        "Graph of y = x^2 - 4·x + 3"


def test_veto_pure_bar_chart_stays_wave128():
    r = _solve_friendly("make a bar graph for runs: "
                        "A 10, B 20, C 15")
    assert r["op"] == "graph"
    assert r["figure"]["caption"] == \
        "Bar graph: A = 10, B = 20, C = 15"
    assert len(r["steps"]) == 2        # no reading step


def test_veto_matplotlib_wording_ask_unchanged():
    r = _solve_friendly("find the graph of y = x^2")
    assert "Graph of y = x**2" in r["answer"]
    assert r.get("figure")


def test_veto_elimination_method_not_graphical():
    r = _solve_friendly(
        "solve x + y = 5 and x - y = 1 by elimination "
        "method")
    assert r["op"] == "system"
    assert r["answer"] == "x = 3, y = 2"
    assert not r.get("figure")


def test_veto_dual_plot_is_not_a_pair_ask():
    assert graphsolve.graphsolve_result(
        "draw the graph of y = 2x + 3 and y = x + 1") \
        is None


def test_veto_graph_banao_aur_solve_not_explicit_method():
    assert graphsolve.graphsolve_result(
        "x + y = 5 and x - y = 1 ka graph banao aur "
        "solve bhi karo") is None


def test_veto_junk_never_raises():
    assert graphsolve.graphsolve_result(None) is None
    assert graphsolve.graphsolve_result("") is None
    assert graphsolve.graphsolve_result("hello") is None
    assert graphsolve.graphsolve_upgrade(
        "by graphical method x + y = 5 and x - y = 1",
        None) is None
    assert graphsolve.graphsolve_upgrade(
        "by graphical method x + y = 5 and x - y = 1",
        {"op": "system", "answer": "x = 3, y = 2",
         "fallback": True}) is None
