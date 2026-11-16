"""Wave 86: ANSWER DIAGRAMS for mensuration solves.

When a real solver answer is about a rectangle, square,
circle or triangle whose dimensions are stated unambiguously
in the question, the result gains a "figure" — a small
server-generated inline SVG labelled with the question's OWN
numbers, plus a text caption naming the shape and dimensions
(figures.py, hooked into fallback.with_fallback's real-answer
branch).

What these tests pin:
1. Figures APPEAR for rectangle area, circle circumference
   (radius and diameter forms), triangle area and square
   perimeter — with the correct labels/numbers and caption.
2. Figures stay ABSENT for algebra / arithmetic / other
   shapes / derived-dimension questions, and the cross-check
   guard refuses a figure whose numbers do not reproduce
   the solved answer (no figure is better than a wrong one).
3. Answers without figures are untouched: no "figure" key,
   and a figure-carrying result keeps the solver's exact
   answer and steps.
4. The rendering: the chat template and the classic answer
   page both place the figure inside the card after the
   steps; the CSS keeps it within the card on mobile widths;
   pins ?v=40 / ganitra-static-v17.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from api import _solve_friendly
from figures import figure_for
from solver.router import solve_question

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


RECT_Q = ("Find the area of a rectangle whose length is "
          "12 cm and breadth is 5 cm")
CIRC_Q = "Find the circumference of a circle with radius 7 cm"
TRI_Q = ("Find the area of a triangle with base 10 cm "
         "and height 6 cm")


def _fig(question):
    r = _solve_friendly(question)
    assert r.get("figure"), r
    return r["figure"]


def _svg_root(fig):
    return ET.fromstring(fig["svg"])


# --- 1. Figures appear, with the question's own numbers ------

def test_rectangle_area_figure():
    fig = _fig(RECT_Q)
    assert fig["caption"] == "Rectangle: length 12 cm, breadth 5 cm"
    assert "<svg" in fig["svg"]
    assert "12 cm" in fig["svg"] and "5 cm" in fig["svg"]
    root = _svg_root(fig)
    assert root.tag.endswith("svg")
    assert root.get("viewBox")
    assert int(root.get("width")) <= 300
    # Accessibility: the caption rides inside the SVG too.
    assert fig["caption"] in fig["svg"]


def test_circle_circumference_figure():
    fig = _fig(CIRC_Q)
    assert fig["caption"] == "Circle: radius 7 cm"
    assert "r = 7 cm" in fig["svg"]
    assert "<circle" in fig["svg"]


def test_circle_diameter_figure():
    fig = _fig("Find the circumference of a circle whose "
               "diameter is 14 cm")
    assert fig["caption"] == "Circle: diameter 14 cm"
    assert "d = 14 cm" in fig["svg"]


def test_circle_area_figure():
    fig = _fig("Find the area of a circle with radius 5 cm")
    assert fig["caption"] == "Circle: radius 5 cm"


def test_triangle_area_figure():
    fig = _fig(TRI_Q)
    assert fig["caption"] == "Triangle: base 10 cm, height 6 cm"
    assert "10 cm" in fig["svg"] and "6 cm" in fig["svg"]
    assert "<polygon" in fig["svg"]


def test_square_perimeter_figure():
    fig = _fig("Find the perimeter of a square with side 9 cm")
    assert fig["caption"] == "Square: side 9 cm"
    assert "9 cm" in fig["svg"]


def test_rectangle_by_form_figure():
    fig = _fig("Find the area of a rectangle 8 cm by 5 cm")
    assert fig["caption"] == "Rectangle: length 8 cm, breadth 5 cm"


def test_hindi_circle_figure():
    fig = _fig("वृत्त का क्षेत्रफल ज्ञात कीजिए जिसकी "
               "त्रिज्या 7 cm है")
    assert fig["caption"] == "Circle: radius 7 cm"


# --- 2. Figures stay absent ----------------------------------

@pytest.mark.parametrize("question", [
    "Solve 2x + 3 = 7",                       # algebra
    "What is 15% of 240?",                    # arithmetic
    "Find the area of a parallelogram with base 10 cm "
    "and height 6 cm",                        # other shape
    "Find the volume of a cuboid with length 5 cm "
    "breadth 4 cm and height 3 cm",           # cuboid: out of scope
    "What is the area of a circle whose circumference "
    "is 44 cm?",                              # radius derived, not stated
    "If tu gfuf",                             # gibberish one-liner
])
def test_no_figure(question):
    r = _solve_friendly(question)
    assert "figure" not in r, r


def test_cross_check_guard_refuses_wrong_answer():
    # The figure's numbers must reproduce the solved answer:
    # a result claiming 999 for a 12 x 5 rectangle gets none.
    fake = {"type": "geometry", "op": "area", "answer": "999",
            "steps": ["Area = length × breadth"]}
    assert figure_for(RECT_Q, fake) is None


def test_fallback_result_never_gets_figure():
    fake = {"type": "geometry", "op": "area", "answer": "60",
            "steps": ["x"], "fallback_kind": "concept"}
    assert figure_for(RECT_Q, fake) is None


def test_two_shapes_is_ambiguous():
    fake = {"type": "geometry", "op": "area", "answer": "60",
            "steps": ["x"]}
    q = ("Find the area of a rectangle of length 12 cm and "
         "breadth 5 cm and a circle")
    assert figure_for(q, fake) is None


# --- 3. Non-figure payloads are untouched --------------------

def test_figure_result_keeps_solver_answer_and_steps():
    raw = solve_question(RECT_Q)
    r = _solve_friendly(RECT_Q)
    assert r["answer"] == raw["answer"]
    assert r["steps"] == raw["steps"]
    assert r["figure"]["caption"].startswith("Rectangle:")


def test_algebra_result_has_no_extra_keys():
    r = _solve_friendly("Solve 2x + 3 = 7")
    assert "figure" not in r
    assert r["answer"] == "x = 2"


# --- 4. HTTP + rendering -------------------------------------

def test_api_solve_payload_carries_figure(client):
    d = client.post("/api/solve",
                    json={"question": RECT_Q}).get_json()
    assert d["ok"] is True
    fig = d["result"]["figure"]
    assert fig["caption"] == "Rectangle: length 12 cm, breadth 5 cm"
    assert "12 cm" in fig["svg"]


def test_api_solve_algebra_payload_has_no_figure(client):
    d = client.post("/api/solve",
                    json={"question": "Solve 2x + 3 = 7"}).get_json()
    assert d["ok"] is True
    assert "figure" not in d["result"]


def test_answer_page_renders_figure(client):
    html = client.post("/solve",
                       data={"question": RECT_Q}).get_data(as_text=True)
    assert 'class="answer-figure"' in html
    assert "Rectangle: length 12 cm, breadth 5 cm" in html
    assert "<svg" in html


def test_chat_template_figure_hooks():
    assert "result.figure" in INDEX
    assert "answer-figure" in INDEX
    # Inside the card, in the graph's place in the sequence.
    assert INDEX.index("figureEl) div.appendChild(figureEl);") \
        > INDEX.index("if (stepsSection) div.appendChild(stepsSection);")
    assert "result.figure" in ANSWER


def test_figure_css_and_pins():
    assert ".answer-figure" in CSS
    assert ".answer-figure svg" in CSS
    assert "max-width: 100%" in CSS
    assert "v='40'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v17"' in SW
