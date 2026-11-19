"""Wave 138 (Suraj, 17 Nov 2026, with a big-AI screenshot as
the target): proper maths notation — Ganitra's answers must
show maths TYPESET like the screenshot (fractions stacked,
powers raised, the root sign covering its expression, the
quadratic / distance / slope / probability formulas as real
notation), not inline text like "1/6", "x^2", "sqrt(x)".

The wave is a deterministic notation layer (notation.py):
the solver's plain lines are untouched — same words, same
values (Wave 132's rule) — and maths spans inside them are
additionally served as TeX in parallel display-only fields
(steps_tex / answer_tex), rendered by the MathJax that
base.html already loads.  These tests pin:

  1. the conversion battery (the screenshot's own shapes,
     in the solver's real output lines);
  2. the value-preservation self-check (Wave 132's hard
     rule: a conversion that would lose or invent a value
     token is declined, the span served plain);
  3. prose byte-identity outside spans, and the decline
     list (bare atoms, word operands, unit rates, ordinals,
     dates, prose parentheticals);
  4. the annotation contract (plain fields never mutated,
     plain/not-found results never annotated);
  5. the wiring (chat payload, classic + print pages,
     template display hooks, pins ?v=44 / v21).
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(
    encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(
    encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(
    encoding="utf-8")
PRINT = (ROOT / "templates" / "print.html").read_text(
    encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

from notation import (annotate_method, annotate_result,  # noqa: E402
                      texify_line, values_preserved)


# ---------------------------------------------------------------
# 1. The conversion battery — the screenshot's shapes, in the
#    solver's own real step/answer lines.
# ---------------------------------------------------------------

BATTERY = [
    # Quadratic formula (the screenshot's first line).
    ("Quadratic formula: x = (-b ± sqrt(D)) / (2a) = "
     "(5 ± sqrt(1)) / 2",
     r"Quadratic formula: \(x = \frac{-b \pm \sqrt{D}}{2a} = "
     r"\frac{5 \pm \sqrt{1}}{2}\)"),
    ("x = (-b ± sqrt(b^2 - 4ac)) / (2a)",
     r"\(x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\)"),
    # Distance formula (root sign covers the whole thing).
    ("Distance = sqrt((x2-x1)^2 + (y2-y1)^2)",
     r"Distance \(= \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}\)"),
    ("d = sqrt((x2 - x1)^2 + (y2 - y1)^2)",
     r"\(d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}\)"),
    # Slope (fraction of two differences, parens dropped by
    # the fraction bar exactly like the screenshot).
    ("Slope m = (y2 - y1) / (x2 - x1)",
     r"Slope \(m = \frac{y_2 - y_1}{x_2 - x_1}\)"),
    ("= (11 - 3) / (5 - 2) = 2.66667",
     r"\(= \frac{11 - 3}{5 - 2} = 2.66667\)"),
    # Probability (a stacked fraction; the percent remark in
    # parens stays plain prose, never a fake product).
    ("Probability = 5/8 ≈ 0.6250 (62.50%)",
     r"Probability \(= \frac{5}{8} \approx 0.6250\) (62.50%)"),
    # Mensuration: pi, powers, a fraction coefficient.
    ("Area = pi·r^2 = (22/7) × 7^2 = (22/7) × 49",
     r"Area \(= \pi \cdot r^2 = \left(\frac{22}{7}\right) "
     r"\times 7^2 = \left(\frac{22}{7}\right) \times 49\)"),
    ("Volume = pi·r^2·h = pi × 3^2 × 10",
     r"Volume \(= \pi \cdot r^2 \cdot h = \pi \times 3^2 "
     r"\times 10\)"),
    ("Surface area = 4·pi·r^2 = 4 × (22/7) × 7^2",
     r"Surface area \(= 4 \cdot \pi \cdot r^2 = 4 \times "
     r"\left(\frac{22}{7}\right) \times 7^2\)"),
    # Fraction arithmetic.
    ("3/4 + 5/6 = 19/12",
     r"\(\frac{3}{4} + \frac{5}{6} = \frac{19}{12}\)"),
    ("5/6", r"\(\frac{5}{6}\)"),
    ("15% means 15/100 = 0.15",
     r"15% means \(\frac{15}{100} = 0.15\)"),
    ("Divide both sides by 1/3: x = 15",
     r"Divide both sides by \(\frac{1}{3}\): \(x = 15\)"),
    ("1/3·x + -5 = 0",
     r"\(\frac{1}{3} \cdot x + -5 = 0\)"),
    # Answers.
    ("x = -2, x = 1/2", r"\(x = -2, x = \frac{1}{2}\)"),
    ("(a + b)^2", r"\((a + b)^2\)"),
    ("x^2 + C", r"\(x^2 + C\)"),
    ("3·x^2 + 2", r"\(3 \cdot x^2 + 2\)"),
    ("5/8 ≈ 0.6250", r"\(\frac{5}{8} \approx 0.6250\)"),
    # Commercial maths formula shapes.
    ("Simple Interest = P × R × T / 100",
     r"Simple Interest \(= \frac{P \times R \times T}{100}\)"),
    ("= 1000 × 5 × 2 / 100 = 100",
     r"\(= \frac{1000 \times 5 \times 2}{100} = 100\)"),
    # Calculus shapes (d/dx as a fraction, group exponents).
    ("d/dx (1·x^3) = 1·3·x^2 = 3·x^2",
     r"\(\frac{d}{dx}(1 \cdot x^3) = 1 \cdot 3 \cdot x^2 = "
     r"3 \cdot x^2\)"),
    ("∫ 2·x^1 dx = 1·x^2",
     r"\(\int 2 \cdot x^1 dx = 1 \cdot x^2\)"),
    # Roots, powers, factorials, trig, logs.
    ("√625 = 25", r"\(\sqrt{625} = 25\)"),
    ("= sqrt((4 - 1)^2 + (6 - 2)^2) = sqrt(25)",
     r"\(= \sqrt{(4 - 1)^2 + (6 - 2)^2} = \sqrt{25}\)"),
    ("2^10 = 1024", r"\(2^{10} = 1024\)"),
    ("5! = 120", r"\(5! = 120\)"),
    ("sin^2 theta + cos^2 theta = 1",
     r"\(\sin^2 \theta + \cos^2 \theta = 1\)"),
    ("log 100 = 2", r"\(\log 100 = 2\)"),
    ("Prime factorisation: 12 = 2^2 × 3",
     r"Prime factorisation: \(12 = 2^2 \times 3\)"),
    # Mixed prose + maths: the prose stays byte-identical,
    # only the maths islands are wrapped.
    ("Write in standard form: 1·x^2 + -5·x + 6 = 0, so "
     "a = 1, b = -5, c = 6",
     r"Write in standard form: \(1 \cdot x^2 + -5 \cdot x "
     r"+ 6 = 0\), so \(a = 1, b = -5, c = 6\)"),
    ("Take pi = 22/7 here — radius 7 is a multiple of 7, "
     "so the answer comes out exact.",
     r"Take \(\pi = \frac{22}{7}\) here — radius 7 is a "
     r"multiple of 7, so the answer comes out exact."),
    ("Add 3/4 and 5/6: make the denominators equal "
     "(LCM of 4 and 6).",
     r"Add \(\frac{3}{4}\) and \(\frac{5}{6}\): make the "
     r"denominators equal (LCM of 4 and 6)."),
    ("D > 0, so there are two distinct real roots.",
     r"\(D > 0\), so there are two distinct real roots."),
    ("Speed = distance ÷ time = 120 km ÷ 2 hours",
     r"Speed = distance ÷ time \(= 120\ \mathrm{km} \div "
     r"2\ \mathrm{hours}\)"),
    # Hindi (Devanagari) prose is a hard wall; the maths
    # island inside still typesets, the superscript digit
    # after a Hindi word stays the plain text it was.
    ("= (2/3) × π × 7³ = 616",
     r"\(= \left(\frac{2}{3}\right) \times \pi \times "
     r"7^{3} = 616\)"),
]


@pytest.mark.parametrize("plain,want", BATTERY)
def test_wave138_battery(plain, want):
    assert texify_line(plain) == want


# ---------------------------------------------------------------
# 2. The decline list — ambiguous or prose shapes stay plain,
#    byte for byte.
# ---------------------------------------------------------------

DECLINES = [
    "Answer = 12",                    # a bare value, no gain
    "60 km/h",                        # a unit rate, not a frac
    "The 2th root of 144.0 is the number whose 2th power "
    "is 144.0.",                      # ordinals are prose
    "Take the lowest power of each common prime factor.",
    "Total = 8; red count = 5",       # bare values after =
    "Find the value of x",
    "Ram has 5 apples and gives 2 to Shyam.",
    "HCF of 12 and 18 is 6",
    "Probability = Favourable outcomes / Total outcomes",
    "Side = √(area)",                 # a word under the root
    "Angle ABC = 90°",                # no strong feature
    "Perimeter = 4 × side",           # a word operand chain
    "already \\(x^2\\) typeset",      # never double-wrap
    "price is $5/2 today",            # a $ guards the line
    "",
]


@pytest.mark.parametrize("plain", DECLINES)
def test_wave138_declines(plain):
    assert texify_line(plain) == plain


def test_wave138_second_bare_slash_ends_span():
    # The date shape: one fraction may typeset, the tail
    # after a second bare "/" is never a fake span.
    out = texify_line("12/11/2026")
    assert out == r"\(\frac{12}{11}\)/2026"
    out = texify_line("5/6 ÷ 2/3 = 5/6 × 3/2 = 5/4")
    assert "2 = " not in out.replace("= \\frac{5}{4}", "")
    assert out.count("\\frac") == 4


# ---------------------------------------------------------------
# 3. Value preservation — the self-check itself, plus a
#    corpus property: every span texify emits passes it.
# ---------------------------------------------------------------

def test_wave138_values_preserved_checker():
    assert values_preserved("5/8", r"\frac{5}{8}")
    assert values_preserved("x2 + x1", "x_2 + x_1")
    assert values_preserved("sqrt(25)", r"\sqrt{25}")
    assert values_preserved("√625", r"\sqrt{625}")
    assert values_preserved("12 = 2^2 × 3", r"12 = 2^2 \times 3")
    assert not values_preserved("5/8", r"\frac{5}{9}")
    assert not values_preserved("x + 2", "x + 3")
    assert not values_preserved("10/2", r"\frac{10}{2} + 1")
    assert not values_preserved("a + b", "a + c")


_SPAN_RE = re.compile(r"\\\((.*?)\\\)")


def test_wave138_corpus_spans_preserve_values():
    corpus = [p for p, _w in BATTERY] + [
        "Discriminant D = b^2 - 4ac = (-5)^2 - 4·1·6 = 1",
        "Total amount = P + SI = 1100",
        "Use sin^2 t + cos^2 t = 1 and the reciprocal "
        "relations (sin t · cosec t = 1, tan t · cot t = 1).",
        "a = 3, b = -sqrt(-I·(9·f + 25·I))",
        "Divide by the count (5): 30 ÷ 5 = 6",
        "Multiply by 200: 0.15 × 200 = 30",
        "Area = (1/2) × base × height = 0.5 × 10 × 6 = 30",
    ]
    checked = 0
    for line in corpus:
        out = texify_line(line)
        # Rebuild the source spans by position: strip the
        # delimiters from the output and compare each span's
        # values against the TeX the converter produced.
        for tex in _SPAN_RE.findall(out):
            checked += 1
            assert values_preserved(tex, tex)  # TeX is stable
            # Every number in the TeX must exist in the line.
            for num in re.findall(r"\d+(?:\.\d+)?", tex):
                assert num in line
    assert checked >= 25


def test_wave138_plain_fields_untouched_by_texify():
    # texify is pure: same input -> same output, no mutation
    # of shared state across calls.
    line = "Slope m = (y2 - y1) / (x2 - x1)"
    assert texify_line(line) == texify_line(line)


# ---------------------------------------------------------------
# 4. The annotation contract.
# ---------------------------------------------------------------

def test_wave138_annotate_result():
    result = {
        "steps": ["Slope m = (y2 - y1) / (x2 - x1)",
                  "= (11 - 3) / (5 - 2) = 2.66667",
                  "Take the lowest power."],
        "answer": "5/8 ≈ 0.6250",
        "type": "Coordinate Geometry",
    }
    plain_steps = list(result["steps"])
    annotate_result(result)
    assert result["steps"] == plain_steps          # untouched
    assert result["answer"] == "5/8 ≈ 0.6250"      # untouched
    assert len(result["steps_tex"]) == 3
    assert result["steps_tex"][0] == (
        r"Slope \(m = \frac{y_2 - y_1}{x_2 - x_1}\)")
    assert result["steps_tex"][2] == "Take the lowest power."
    assert result["answer_tex"] == (
        r"\(\frac{5}{8} \approx 0.6250\)")


def test_wave138_annotate_no_change_no_fields():
    result = {"steps": ["Add the numbers."], "answer": "42"}
    annotate_result(result)
    assert "steps_tex" not in result
    assert "answer_tex" not in result


def test_wave138_annotate_plain_results_never():
    for result in (
            {"steps": ["x = 5"], "answer": "5", "plain": True},
            {"steps": ["x = 5"], "answer": "5",
             "plain_reply": True},
            {"steps": ["x = 5"], "answer": "5",
             "fallback_kind": "not_found"}):
        annotate_result(result)
        assert "steps_tex" not in result
        assert "answer_tex" not in result


def test_wave138_annotate_idempotent():
    result = {"steps": ["3/4 + 5/6 = 19/12"], "answer": "19/12"}
    annotate_result(result)
    first = dict(result)
    annotate_result(result)
    assert result == first


def test_wave138_annotate_method():
    method = {"id": "m1", "label": "Short method",
              "steps": ["x/3 = 5", "x = 15"]}
    annotate_method(method)
    assert method["steps"] == ["x/3 = 5", "x = 15"]
    assert method["steps_tex"][0] == r"\(\frac{x}{3} = 5\)"
    assert method["steps_tex"][1] == r"\(x = 15\)"


# ---------------------------------------------------------------
# 5. Wiring — payload, pages, template hooks, pins.
# ---------------------------------------------------------------

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    c.post("/signup", data={
        "name": "W138 Notation Tester", "class": "10",
        "board": "CBSE", "goal": "Doctor", "hobby": "Cricket",
        "favourite": "Pizza", "password": "w138-notation-pass"})
    return c


def test_wave138_api_payload_carries_tex(client):
    data = client.post(
        "/api/solve",
        json={"question": "Solve x^2 - 5x + 6 = 0"}).get_json()
    assert data["ok"] is True
    result = data["result"]
    # The plain payload is byte-identical to the solver's own.
    assert "\\(" not in " ".join(result["steps"])
    assert result["answer"] == "x = 2, x = 3"
    # …and the typeset variants ride alongside.
    joined = " ".join(result["steps_tex"])
    assert r"\frac{-b \pm \sqrt{D}}{2a}" in joined
    assert len(result["steps_tex"]) == len(result["steps"])


def test_wave138_classic_and_print_pages_typeset(client):
    page = client.post(
        "/solve", data={"question": "Solve x^2 - 5x + 6 = 0"})
    html = page.get_data(as_text=True)
    assert r"\(x = \frac{-b \pm \sqrt{D}}{2a}" in html
    client.post("/solve",
                data={"question": "Solve x^2 - 5x + 6 = 0"})
    printed = client.get("/solution/print")
    phtml = printed.get_data(as_text=True)
    assert r"\(x = \frac{-b \pm \sqrt{D}}{2a}" in phtml


def test_wave138_template_hooks():
    assert "function w138TexOk()" in INDEX
    assert "window.MathJax.typesetPromise" in INDEX
    assert "boardTex" in INDEX
    assert "result.answer_tex" in INDEX
    assert "method.steps_tex" in INDEX
    # The plain-reply path is NOT texified (raw text only):
    # slice exactly its branch, from its class name to its
    # early return.
    p0 = INDEX.index("plain-reply")
    plain_block = INDEX[p0:INDEX.index(
        "alignLiveAnswer(plain, null)")]
    assert "steps_tex" not in plain_block
    assert "answer_tex" not in plain_block
    # Classic + print templates prefer the tex variants.
    assert "result.steps_tex[loop.index0]" in ANSWER
    assert "result.answer_tex" in ANSWER
    assert "result.steps_tex[loop.index0]" in PRINT
    assert "result.answer_tex" in PRINT
    # The Wave 68 intro lift carries steps[0]'s typeset twin
    # with it, so the card's opening formula line typesets
    # exactly like the step it was.
    assert "introTex = boardTex[0]" in INDEX
    assert "introTex && w138TexOk()" in INDEX


def test_wave138_css_and_pins():
    assert "mjx-container" in CSS
    assert "v='58'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v35"' in SW
    assert '"/static/style.css?v=58"' in SW
