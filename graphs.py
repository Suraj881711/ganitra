"""Wave 128: function graphs & general diagrams (SVG).

Extends Wave 86's answer-figure system (figures.py) from
mensuration shapes to the pictures the big AIs draw on
request — function graphs, coordinate-geometry plots,
number lines and data charts. Everything here is a
hand-built inline SVG in the figures.py style; no external
libraries (the matplotlib PNG path in solver/plotting.py
stays at router level for direct solve_question callers,
but the chat now prefers this verified SVG — see the
op == "graph" attach case below).

The figures.py discipline is the law here too:

1. A graph appears ONLY when the student asked for one
   (graph / plot / number-line / chart words — English,
   Hinglish, Devanagari) or the question IS a plotting
   question. A plain solve never gains a graph.
2. The picture is built only from a supported, parsed
   target: a SymPy-validated function form, points stated
   in the question, an inequality re-solved here, or
   chart data stated in the question. On the attach path
   the target is cross-checked against the solver's own
   answer; any mismatch means no figure, and the answer
   is returned byte-identical.
3. Everything interpolated into the SVG is a formatted
   number, a validated short label, or fixed text —
   never raw question text.

Entry points (all never raise; None = "not mine / not
safe"), called from fallback.py:

- graph_figure_for(question, result): attach-only figures
  for real answers — a matplotlib plot result rebuilt as
  a verified SVG, an inequality solve with a number-line
  ask, a coordinate solve with a plot ask.
- graph_upgrade(question, result, hindi): a PURE graph
  request the solver answered as something else ("y =
  2x + 3 ka graph banao" came back as a hindi_equation
  solve "y = 2") — the graph IS the answer asked for.
- graph_result(question, hindi): a full graph answer
  for graph requests every solving layer missed.
"""

import math
import re
from xml.sax.saxutils import escape as _xml_escape

import sympy as sp

from solver.expression_parser import (extract_points, fmt,
                                      fmt_num, parse_expression)

_INK = "#25324e"      # --text (figures.py palette)
_ACCENT = "#2f7d6e"   # --accent
_ACCENT2 = "#b3541e"  # marker / second curve
_MUTED = "#66738d"    # --muted
_GRID = "#dde2ec"
_FILL = "rgba(47, 125, 110, 0.08)"

_X = sp.symbols("x")
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUM_RE = r"(-?\d+(?:\.\d+)?)"


def _norm(question):
    return str(question or "").lower().translate(_DEVA_DIGITS)


# ---------------------------------------------------------------------------
# Triggers — the student must have ASKED for a picture
# ---------------------------------------------------------------------------

_GRAPH_RE = re.compile(r"\b(graphs?|plots?|plotting)\b|ग्राफ|प्लॉट|आलेख")
_BAR_RE = re.compile(r"\bbar\s*(graph|chart)\b|दंड\s*आलेख|दण्ड\s*आलेख")
_PIE_RE = re.compile(r"\bpie\s*(chart|graph)\b|वृत्त\s*आलेख|पाई\s*चार्ट")
_NUMLINE_RE = re.compile(r"number\s*line|संख्या\s*रेखा|sankhya\s*rekha")
# "draw a line through…", "draw the triangle with
# vertices…" — an explicit coordinate-drawing request
# even without the word graph/plot.
_COORD_DRAW_RE = re.compile(
    r"\bdraw\b.*\b(line|points?|triangle)\b")


def _wants_graph(q):
    return bool(_GRAPH_RE.search(q))


def _wants_bar(q):
    return bool(_BAR_RE.search(q))


def _wants_pie(q):
    return bool(_PIE_RE.search(q))


def _wants_numline(q):
    return bool(_NUMLINE_RE.search(q))


def _any_trigger(q):
    return (_wants_graph(q) or _wants_bar(q) or _wants_pie(q)
            or _wants_numline(q)
            or bool(_COORD_DRAW_RE.search(q)))


# A graph/chart request is "pure" when nothing else is
# being asked — no solve/find/calculate verb survives.
# Mixed asks keep whatever the solver did (the attach
# path may still add a picture to a real answer).
_SOLVE_VERBS = {
    "solve", "find", "calculate", "compute", "evaluate",
    "simplify", "factorise", "factorize", "expand",
    "differentiate", "integrate", "prove", "verify",
    "हल", "निकालो", "निकाल", "ज्ञात", "मान",
}

# Compute-words that veto the CHART builder: "the bar
# graph shows A 10, B 20 — how many more…" is a question
# ABOUT a chart, not a request to draw one.
_CHART_VETO = {
    "how", "kitne", "kitna", "kitni", "difference",
    "antar", "अंतर", "total", "yog", "योग", "more",
    "less", "percentage", "pratishat", "प्रतिशत",
}


def _tokens(q):
    return set(re.findall(r"[a-z]+|[ऀ-ॏ]+", q))


def _is_pure(q):
    return not (_tokens(q) & _SOLVE_VERBS)


# ---------------------------------------------------------------------------
# Small SVG helpers (figures.py style)
# ---------------------------------------------------------------------------

def _svg_open(width, height, caption):
    cap = _xml_escape(caption, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" '
        f'role="img" aria-label="{cap}" '
        f'style="max-width:100%;height:auto">'
        f"<title>{cap}</title>")


def _text(x, y, s, size=11, fill=_INK, anchor="middle",
          weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" '
            f'text-anchor="{anchor}" font-size="{size}" '
            f'fill="{fill}"{w}>{_xml_escape(str(s))}</text>')


def _tick_label(v, step):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    dec = 0 if step >= 1 else (1 if step >= 0.1 else 2)
    s = f"{v:.{dec}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _nice_step(span, target=6):
    raw = span / max(target, 1)
    for s in (0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25,
              50, 100, 200, 500, 1000):
        if s >= raw:
            return s
    return 1000.0


def _ticks(lo, hi, step):
    out = []
    v = math.ceil(lo / step - 1e-9) * step
    while v <= hi + 1e-9:
        out.append(round(v, 9))
        v += step
    return out


class _Plot:
    """A cartesian SVG canvas: grid, axes, curves, markers."""

    W, H = 340, 300
    L, R, T, B = 38, 12, 12, 28

    def __init__(self, xmin, xmax, ymin, ymax, caption):
        self.xmin, self.xmax = float(xmin), float(xmax)
        self.ymin, self.ymax = float(ymin), float(ymax)
        self.caption = caption
        self.parts = []
        self._clip = "w128" + str(abs(hash(caption)) % 99991)
        pw = self.W - self.L - self.R
        ph = self.H - self.T - self.B
        self.parts.append(
            f'<defs><clipPath id="{self._clip}">'
            f'<rect x="{self.L}" y="{self.T}" width="{pw}" '
            f'height="{ph}"/></clipPath></defs>')
        self.parts.append(
            f'<rect x="{self.L}" y="{self.T}" width="{pw}" '
            f'height="{ph}" fill="#ffffff" '
            f'stroke="{_GRID}"/>')

    def X(self, x):
        return self.L + (x - self.xmin) / (self.xmax - self.xmin) \
            * (self.W - self.L - self.R)

    def Y(self, y):
        return self.T + (self.ymax - y) / (self.ymax - self.ymin) \
            * (self.H - self.T - self.B)

    def grid(self, xticks=None, yticks=None, xlabels=None,
             ylabels=None):
        xs = _nice_step(self.xmax - self.xmin) \
            if xticks is None else None
        xt = xticks if xticks is not None else \
            _ticks(self.xmin, self.xmax, xs)
        ys = _nice_step(self.ymax - self.ymin) \
            if yticks is None else None
        yt = yticks if yticks is not None else \
            _ticks(self.ymin, self.ymax, ys)
        xl = {round(k, 6): v for k, v in
              (xlabels or {}).items()}
        yl = {round(k, 6): v for k, v in
              (ylabels or {}).items()}
        for v in xt:
            px = self.X(v)
            self.parts.append(
                f'<line x1="{px:.1f}" y1="{self.T}" '
                f'x2="{px:.1f}" y2="{self.H - self.B}" '
                f'stroke="{_GRID}" stroke-width="1"/>')
            lab = xl.get(round(v, 6),
                         _tick_label(v, xs or 1))
            if lab != "":
                self.parts.append(_text(
                    px, self.H - self.B + 16, lab, 10, _MUTED))
        for v in yt:
            py = self.Y(v)
            self.parts.append(
                f'<line x1="{self.L}" y1="{py:.1f}" '
                f'x2="{self.W - self.R}" y2="{py:.1f}" '
                f'stroke="{_GRID}" stroke-width="1"/>')
            lab = yl.get(round(v, 6),
                         _tick_label(v, ys or 1))
            if lab != "":
                self.parts.append(_text(
                    self.L - 5, py + 3.5, lab, 10, _MUTED,
                    anchor="end"))
        # axes through 0 when in range, else the near edge
        ax = self.X(0) if self.xmin <= 0 <= self.xmax else self.L
        ay = self.Y(0) if self.ymin <= 0 <= self.ymax \
            else self.H - self.B
        self.parts.append(
            f'<line x1="{ax:.1f}" y1="{self.T}" x2="{ax:.1f}" '
            f'y2="{self.H - self.B}" stroke="{_MUTED}" '
            f'stroke-width="1.4"/>')
        self.parts.append(
            f'<line x1="{self.L}" y1="{ay:.1f}" '
            f'x2="{self.W - self.R}" y2="{ay:.1f}" '
            f'stroke="{_MUTED}" stroke-width="1.4"/>')
        self.parts.append(_text(self.W - self.R - 2,
                                ay - 5 if ay > self.T + 14
                                else ay + 14,
                                "x", 11, _MUTED, anchor="end"))
        self.parts.append(_text(ax + 8 if ax < self.W - 30
                                else ax - 8, self.T + 10,
                                "y", 11, _MUTED))

    def curve(self, segments, colour=_ACCENT, width=2.2):
        for seg in segments:
            if len(seg) < 2:
                continue
            d = "M " + " L ".join(
                f"{self.X(x):.1f} {self.Y(y):.1f}"
                for x, y in seg)
            self.parts.append(
                f'<path d="{d}" fill="none" stroke="{colour}" '
                f'stroke-width="{width}" '
                f'clip-path="url(#{self._clip})"/>')

    def line(self, p1, p2, colour=_ACCENT, width=2.0,
             dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<line x1="{self.X(p1[0]):.1f}" '
            f'y1="{self.Y(p1[1]):.1f}" '
            f'x2="{self.X(p2[0]):.1f}" '
            f'y2="{self.Y(p2[1]):.1f}" stroke="{colour}" '
            f'stroke-width="{width}"{d} '
            f'clip-path="url(#{self._clip})"/>')

    def dot(self, x, y, label=None, colour=_ACCENT2,
            dy=-9, anchor="middle"):
        self.parts.append(
            f'<circle cx="{self.X(x):.1f}" '
            f'cy="{self.Y(y):.1f}" r="3.4" fill="{colour}" '
            f'stroke="#ffffff" stroke-width="1.2"/>')
        if label:
            self.parts.append(_text(
                self.X(x), self.Y(y) + dy, label, 10.5,
                _INK, anchor=anchor))

    def polygon(self, pts, colour=_ACCENT):
        joined = " ".join(
            f"{self.X(x):.1f},{self.Y(y):.1f}" for x, y in pts)
        self.parts.append(
            f'<polygon points="{joined}" fill="{_FILL}" '
            f'stroke="{colour}" stroke-width="2" '
            f'clip-path="url(#{self._clip})"/>')

    def svg(self):
        return (_svg_open(self.W, self.H, self.caption)
                + "".join(self.parts) + "</svg>")


def _linspace(lo, hi, n):
    if n <= 1:
        return [float(lo)]
    step = (hi - lo) / (n - 1)
    return [lo + i * step for i in range(n)]


def _sample(expr, xs):
    """(x, y|None) pairs — None where the function is not a
    finite real number."""
    try:
        f = sp.lambdify(_X, expr, "math")
    except Exception:
        return [(v, None) for v in xs]
    out = []
    for v in xs:
        try:
            y = f(v)
        except Exception:
            y = None
        if isinstance(y, complex) or y is None:
            out.append((v, None))
            continue
        try:
            y = float(y)
        except (TypeError, ValueError):
            out.append((v, None))
            continue
        out.append((v, y if math.isfinite(y) else None))
    return out


def _segments(samples, break_at=()):
    """Split sampled points into drawable runs: a run ends
    at an undefined point, at a break x (an asymptote), or
    where the curve jumps implausibly fast (a pole the
    sampling stepped over)."""
    segs, cur = [], []
    prev = None
    for x, y in samples:
        if y is None:
            if len(cur) >= 2:
                segs.append(cur)
            cur, prev = [], None
            continue
        if prev is not None:
            px, py = prev
            if any(px < b <= x for b in break_at) or \
                    abs(y - py) > 60 * max(1.0, abs(py)) + 60:
                if len(cur) >= 2:
                    segs.append(cur)
                cur = []
        cur.append((x, y))
        prev = (x, y)
    if len(cur) >= 2:
        segs.append(cur)
    return segs


# ---------------------------------------------------------------------------
# Function extraction & the supported forms
# ---------------------------------------------------------------------------

_CUT_TOKENS = {
    "ka", "ki", "ke", "kaa", "ko", "par", "me", "mein",
    "wala", "wali", "hai", "graph", "graphs", "plot",
    "banao", "banaiye", "bana", "dikhao", "dikhaiye",
    "karo", "karke", "please", "banana", "banaye",
    "chahiye", "draw", "drawn", "aalekh",
    "ग्राफ", "ग्राफ़", "आलेख", "बनाओ", "दिखाओ", "करो",
    "का", "की", "के", "को", "पर", "में", "है",
}


def _cut_tail(tail):
    """Cut a captured expression tail at the first filler
    token ("… + 3 ka graph banao" -> "… + 3")."""
    kept = []
    for tok in tail.replace(",", " , ").split():
        word = tok.strip(" .:?।!\"'()")
        if word.lower() in _CUT_TOKENS:
            break
        kept.append(tok)
    return " ".join(kept).strip(" .:?।")


def _expr_texts(question):
    """Candidate function-expression texts in the question,
    most specific first: after "y =" / "f(x) =", after
    "of", then the whole question minus its trigger words."""
    q = _norm(question)
    out = []
    m = re.search(r"(?:\by|f\s*\(\s*x\s*\))\s*=\s*(.+)$", q)
    if m:
        out.append(_cut_tail(m.group(1)))
    m = re.search(r"\bof\s+(.+)$", q)
    if m:
        out.append(_cut_tail(m.group(1)))
    stripped = _GRAPH_RE.sub(" ", q)
    stripped = re.sub(r"\b(draw|the|a|an|please|of|for|me|"
                      r"function|curve)\b", " ", stripped)
    out.append(_cut_tail(stripped))
    seen, uniq = set(), []
    for t in out:
        if t and t not in seen:
            seen.add(t)
            uniq.append(t)
    return uniq


def _classify(expr):
    """The supported-form verdict for a SymPy expression in
    x, or None. Supported: polynomial of degree 1–3 with
    rational coefficients; a·sin(kx) / a·cos(kx) with
    rational a, k; |ax + b| with rational a ≠ 0; c/(x − a)
    with rational c ≠ 0, a."""
    if not isinstance(expr, sp.Expr) or expr.has(sp.Equality):
        return None
    syms = expr.free_symbols
    if not syms or not syms.issubset({_X}):
        return None
    try:
        poly = sp.Poly(expr, _X)
    except Exception:
        poly = None
    if poly is not None:
        if poly.degree() in (1, 2, 3) and all(
                c.is_rational for c in poly.all_coeffs()):
            return ("poly", poly)
        return None
    # a·sin(kx) / a·cos(kx)
    func, amp = expr, sp.Integer(1)
    if expr.is_Mul:
        coeff, rest = expr.as_coeff_mul()
        if coeff.is_rational and len(rest) == 1:
            amp, func = coeff, rest[0]
    if isinstance(func, (sp.sin, sp.cos)):
        arg = func.args[0]
        try:
            ap = sp.Poly(arg, _X)
        except Exception:
            ap = None
        if ap is not None and ap.degree() == 1 and \
                ap.nth(0) == 0 and ap.nth(1).is_rational \
                and ap.nth(1) != 0:
            return ("trig", func.func.__name__, amp,
                    ap.nth(1))
        return None
    # |ax + b|
    if isinstance(expr, sp.Abs):
        try:
            ap = sp.Poly(expr.args[0], _X)
        except Exception:
            ap = None
        if ap is not None and ap.degree() == 1 and all(
                c.is_rational for c in ap.all_coeffs()) \
                and ap.nth(1) != 0:
            return ("abs", ap)
        return None
    # c/(x − a)
    base, coeff = expr, sp.Integer(1)
    if expr.is_Mul:
        c, rest = expr.as_coeff_mul()
        if c.is_rational and len(rest) == 1:
            coeff, base = c, rest[0]
    if isinstance(base, sp.Pow) and base.exp == -1:
        try:
            bp = sp.Poly(base.base, _X)
        except Exception:
            bp = None
        if bp is not None and bp.degree() == 1 and \
                bp.nth(1) == 1 and bp.nth(0).is_rational:
            return ("recip", coeff, -bp.nth(0))
    return None


def _parse(text):
    """parse_expression + the school modulus notation:
    |x + 2| means Abs(x + 2), which the parser itself
    does not accept."""
    text = re.sub(r"\|([^|]+)\|", r"Abs(\1)", text)
    return parse_expression(text)


def _extract_function(question, multi=False):
    """(classify-tuple, expr) for the question's function,
    or None. With multi=True (the matplotlib attach path),
    also accept "expr and expr" and return a list."""
    for text in _expr_texts(question):
        if multi and " and " in text:
            parts = [p.strip() for p in text.split(" and ")
                     if p.strip()]
            if len(parts) == 2:
                got = []
                for p in parts:
                    try:
                        e = _parse(p)
                    except Exception:
                        got = None
                        break
                    c = _classify(e)
                    if c is None or c[0] != "poly":
                        got = None
                        break
                    got.append((c, e))
                if got:
                    return got
            continue
        try:
            e = _parse(text)
        except Exception:
            continue
        c = _classify(e)
        if c is not None:
            return [(c, e)]
    return None


def _exactish(value):
    """True when an exact SymPy value is short enough to
    print as a marker label (a rational, or a simple surd
    like sqrt(2)) — markers are only ever exact values."""
    if value is None or not getattr(value, "is_real", None):
        return False
    s = fmt(value)
    return len(s) <= 9 and "I" not in s and ".." not in s


def _function_figure(kind, expr):
    """(svg-plot, facts) for one supported function. facts
    carries the exact key points for the answer's steps:
    roots / vertex / intercepts as SymPy values."""
    caption = f"Graph of y = {fmt(expr)}"
    facts = {}
    if kind[0] == "poly":
        poly = kind[1]
        deg = poly.degree()
        roots = []
        try:
            for r in sp.solve(expr, _X):
                if r.is_real:
                    roots.append(r)
        except Exception:
            roots = []
        facts["roots"] = roots
        facts["y0"] = poly.nth(0)
        anchors = [0.0] + [float(r) for r in roots]
        vertex = None
        if deg == 2:
            a, b = poly.nth(2), poly.nth(1)
            vertex = -b / (2 * a)
            facts["vertex"] = (vertex, sp.expand(expr).subs(
                _X, vertex))
            anchors.append(float(vertex))
        lo = min(min(anchors) - 2.0, -3.0)
        hi = max(max(anchors) + 2.0, 3.0)
        if deg == 3 and hi - lo > 12:
            mid = (lo + hi) / 2
            lo, hi = mid - 6, mid + 6
        lo, hi = max(lo, -15.0), min(hi, 15.0)
        samples = _sample(expr, _linspace(lo, hi, 220))
        ys = [y for _, y in samples if y is not None]
        ymin, ymax = min(ys), max(ys)
        pad = max((ymax - ymin) * 0.12, 0.6)
        ymin, ymax = min(ymin - pad, 0.0), max(ymax + pad, 0.0)
        if ymax - ymin < 2:
            ymin, ymax = ymin - 1, ymax + 1
        plot = _Plot(lo, hi, ymin, ymax, caption)
        plot.grid()
        plot.curve(_segments(samples))
        for r in roots:
            if lo <= float(r) <= hi and _exactish(r):
                plot.dot(float(r), 0, fmt(r))
        if facts["y0"] != 0 and ymin <= float(facts["y0"]) \
                <= ymax:
            plot.dot(0, float(facts["y0"]),
                     fmt_num(facts["y0"]), dy=15)
        if vertex is not None:
            vx, vy = facts["vertex"]
            if lo <= float(vx) <= hi and \
                    ymin <= float(vy) <= ymax:
                plot.dot(float(vx), float(vy),
                         f"({fmt_num(vx)}, {fmt_num(vy)})",
                         dy=-10 if vy >= 0 else 16)
        return plot, facts
    if kind[0] == "trig":
        _, name, amp, k = kind
        a = abs(float(amp))
        plot = _Plot(-2 * math.pi, 2 * math.pi,
                     -1.4 * a - 0.2, 1.4 * a + 0.2, caption)
        pi = math.pi
        xticks = [-2 * pi, -pi, 0, pi, 2 * pi]
        xlabels = {-2 * pi: "-2π", -pi: "-π", 0.0: "0",
                   pi: "π", 2 * pi: "2π"}
        plot.grid(xticks=xticks, xlabels=xlabels)
        samples = _sample(expr, _linspace(-2 * pi, 2 * pi,
                                          260))
        plot.curve(_segments(samples))
        facts["trig"] = (name, amp, k)
        return plot, facts
    if kind[0] == "abs":
        ap = kind[1]
        vx = -ap.nth(0) / ap.nth(1)
        facts["vertex_x"] = vx
        lo, hi = float(vx) - 4, float(vx) + 4
        samples = _sample(expr, _linspace(lo, hi, 180))
        ys = [y for _, y in samples if y is not None]
        ymax = max(ys) if ys else 4
        plot = _Plot(lo, hi, -max(ymax * 0.18, 1.0),
                     ymax * 1.15 + 0.4, caption)
        plot.grid()
        plot.curve(_segments(samples))
        plot.dot(float(vx), 0, f"({fmt_num(vx)}, 0)")
        return plot, facts
    # reciprocal c/(x − a)
    _, coeff, a = kind
    facts["asymptote"] = a
    facts["y0"] = (coeff / (-a)) if a != 0 else None
    lo, hi = float(a) - 5, float(a) + 5
    xs = [v for v in _linspace(lo, hi, 260)
          if abs(v - float(a)) > 0.03]
    samples = _sample(expr, xs)
    ys = [y for _, y in samples if y is not None
          and abs(y) <= 40]
    ymin = min(min(ys), -1.0) if ys else -10
    ymax = max(max(ys), 1.0) if ys else 10
    ymin, ymax = max(ymin, -14.0), min(ymax, 14.0)
    plot = _Plot(lo, hi, ymin, ymax, caption)
    plot.grid()
    plot.curve(_segments(samples, break_at=(float(a),)))
    plot.line((float(a), ymin), (float(a), ymax),
              colour=_MUTED, width=1.1, dash="5 4")
    if facts["y0"] is not None and \
            ymin <= float(facts["y0"]) <= ymax:
        plot.dot(0, float(facts["y0"]), fmt_num(facts["y0"]),
                 dy=15)
    return plot, facts


# ---------------------------------------------------------------------------
# Inequalities & the number line
# ---------------------------------------------------------------------------

_REL_MAP = {">=": ">=", "<=": "<=", "≥": ">=", "≤": "<=",
            ">": ">", "<": "<"}
_INEQ_RE = re.compile(r"(.+?)(>=|<=|≥|≤|>|<)(.+)")

_LHS_FILLER = {"solve", "the", "inequality", "find",
               "solution", "of", "हल", "असमीका"}


def _clean_side(text, left):
    """Trim solver-question framing from one side of an
    inequality ("solve the inequality 2x - 4" / "6 and
    show on number line") so the side parses."""
    toks = text.split()
    if left:
        while toks and toks[0].lower() in _LHS_FILLER:
            toks.pop(0)
        return " ".join(toks)
    text = re.split(r"\s+and\s+", " ".join(toks))[0]
    toks = text.split()
    while toks and toks[-1].lower() in {
            "show", "shown", "on", "the", "number",
            "line", "dikhao", "par", "display"}:
        toks.pop()
    return " ".join(toks)


def _solve_inequality(question):
    """Re-solve a LINEAR inequality in x from the question.

    Returns (solution, steps_info) or None. solution is
    ("ray", bound, direction, closed) with direction
    +1 (x > b) / -1 (x < b), or ("interval", lo, hi,
    lo_closed, hi_closed); bounds are exact SymPy values.
    steps_info carries the algebra for the constructed
    answer: (lhs_text, rel, rhs_text, coeff, rhs2,
    final_rel, bound)."""
    q = _norm(question)
    m = None
    for cand in _INEQ_RE.finditer(q):
        lhs, rhs = cand.group(1), cand.group(3)
        if "x" in lhs or "x" in rhs:
            m = cand
            break
    if m is None:
        return None
    rel = _REL_MAP[m.group(2)]
    try:
        lhs = parse_expression(_clean_side(
            _cut_tail(m.group(1)), left=True))
        rhs = parse_expression(_clean_side(
            _cut_tail(m.group(3)), left=False))
    except Exception:
        return None
    try:
        lp, rp = sp.Poly(lhs, _X), sp.Poly(rhs, _X)
    except Exception:
        return None
    if lp is None or rp is None or lp.degree() > 1 \
            or rp.degree() > 1 or (lp.degree() == 0
                                   and rp.degree() == 0):
        return None
    a = lp.nth(1) - rp.nth(1)          # x coefficient
    b = rp.nth(0) - lp.nth(0)          # moved constant
    if a == 0:
        return None
    closed = rel in (">=", "<=")
    frel = rel
    if a < 0:
        frel = {"<": ">", ">": "<", "<=": ">=",
                ">=": "<="}[rel]
    bound = b / a
    direction = 1 if frel in (">", ">=") else -1
    sol = ("ray", bound, direction,
           frel in (">=", "<="))
    steps = (fmt(lhs), rel, fmt(rhs), a, b, frel, bound)
    return sol, steps


def _solution_text(sol):
    if sol[0] == "ray":
        _, bound, direction, closed = sol
        rel = (">=" if closed else ">") if direction > 0 \
            else ("<=" if closed else "<")
        rel = rel.replace(">=", "≥").replace("<=", "≤")
        return f"x {rel} {fmt_num(bound)}"
    _, lo, hi, lc, hc = sol
    lrel = "≤" if lc else "<"
    hrel = "≤" if hc else "<"
    return f"{fmt_num(lo)} {lrel} x {hrel} {fmt_num(hi)}"


def _numline_figure(sol):
    caption = f"Number line: {_solution_text(sol)}"
    if sol[0] == "ray":
        _, bound, direction, closed = sol
        b = float(bound)
        lo = b - 3 if direction > 0 else b - 4
        hi = b + 4 if direction > 0 else b + 3
    else:
        _, l, h, _, _ = sol
        lo, hi = float(l) - 2, float(h) + 2
    width, height = 340, 92
    L, R, T = 16, 22, 30
    pw = width - L - R

    def X(v):
        return L + (v - lo) / (hi - lo) * pw

    parts = [
        f'<line x1="{L}" y1="{T}" x2="{width - 6}" y2="{T}" '
        f'stroke="{_INK}" stroke-width="1.6"/>',
        f'<polygon points="{width - 6},{T} {width - 14},'
        f'{T - 4} {width - 14},{T + 4}" fill="{_INK}"/>',
    ]
    step = _nice_step(hi - lo, target=7)
    for v in _ticks(lo, hi, step):
        parts.append(
            f'<line x1="{X(v):.1f}" y1="{T - 4}" '
            f'x2="{X(v):.1f}" y2="{T + 4}" '
            f'stroke="{_INK}" stroke-width="1"/>')
        parts.append(_text(X(v), T + 18,
                           _tick_label(v, step), 10, _MUTED))
    if sol[0] == "ray":
        _, bound, direction, closed = sol
        b = float(bound)
        x1 = X(b)
        x2 = X(hi) if direction > 0 else X(lo)
        fill = _ACCENT2 if closed else "#ffffff"
        parts.append(
            f'<line x1="{x1:.1f}" y1="{T}" x2="{x2:.1f}" '
            f'y2="{T}" stroke="{_ACCENT}" stroke-width="4"/>')
        parts.append(
            f'<circle cx="{x1:.1f}" cy="{T}" r="5" '
            f'fill="{fill}" stroke="{_ACCENT2}" '
            f'stroke-width="2"/>')
        parts.append(_text(x1, T - 12, fmt_num(bound), 11,
                           _INK, weight="bold"))
    else:
        _, l, h, lc, hc = sol
        parts.append(
            f'<line x1="{X(float(l)):.1f}" y1="{T}" '
            f'x2="{X(float(h)):.1f}" y2="{T}" '
            f'stroke="{_ACCENT}" stroke-width="4"/>')
        for v, cl in ((l, lc), (h, hc)):
            fill = _ACCENT2 if cl else "#ffffff"
            parts.append(
                f'<circle cx="{X(float(v)):.1f}" cy="{T}" '
                f'r="5" fill="{fill}" stroke="{_ACCENT2}" '
                f'stroke-width="2"/>')
            parts.append(_text(X(float(v)), T - 12,
                               fmt_num(v), 11, _INK,
                               weight="bold"))
    parts.append(_text(width - 8, T + 18, "x", 11, _MUTED))
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


def _ineq_matches_result(sol, result):
    """Cross-check for the attach path: the solver's own
    answer must state the same bound(s) and direction."""
    ans = str(result.get("answer", "") or "")
    steps = " ".join(str(s) for s in result.get("steps") or [])
    hay = ans + " " + steps
    nums = set(re.findall(r"-?\d+(?:\.\d+)?", hay))
    if sol[0] == "ray":
        _, bound, direction, _ = sol
        if fmt_num(bound) not in nums and \
                str(float(bound)) not in nums:
            return False
        if direction > 0:
            return "oo" in ans or ">" in ans
        return "-oo" in ans or "(-oo" in ans or "<" in ans
    _, lo, hi, _, _ = sol
    return fmt_num(lo) in nums and fmt_num(hi) in nums


# ---------------------------------------------------------------------------
# Coordinate geometry: points, a line, a triangle
# ---------------------------------------------------------------------------

def _points(question):
    pts = extract_points(_norm(question))
    return [(float(a), float(b)) for a, b in pts]


def _pt_label(p):
    return f"({fmt_num(p[0])}, {fmt_num(p[1])})"


def _coord_range(pts):
    xs = [p[0] for p in pts] + [0.0]
    ys = [p[1] for p in pts] + [0.0]
    lo_x, hi_x = min(xs) - 2, max(xs) + 2
    lo_y, hi_y = min(ys) - 2, max(ys) + 2
    if hi_x - lo_x < 6:
        lo_x, hi_x = lo_x - 1, hi_x + 1
    if hi_y - lo_y < 6:
        lo_y, hi_y = lo_y - 1, hi_y + 1
    return lo_x, hi_x, lo_y, hi_y


def _coord_figure(question, result=None):
    """The coordinate figure for the question's points,
    or None. Modes: triangle (3 points + triangle word),
    line (2 points + line word), segment (attach path,
    result-gated by the caller), points (otherwise)."""
    q = _norm(question)
    pts = _points(question)
    if not pts or len(pts) > 6:
        return None
    mode = None
    if len(pts) == 3 and ("triangle" in q or "त्रिभुज" in q):
        mode = "triangle"
    elif len(pts) == 2 and ("line" in q or "रेखा" in q):
        mode = "line"
    elif result is not None and len(pts) == 2:
        mode = "segment"
    elif "point" in q or "बिंदु" in q or "बिन्दु" in q:
        mode = "points"
    if mode is None:
        return None
    rng = _coord_range(pts)
    if mode == "triangle":
        caption = "Triangle with vertices " + ", ".join(
            _pt_label(p) for p in pts)
    elif mode == "line":
        caption = (f"Line through {_pt_label(pts[0])} and "
                   f"{_pt_label(pts[1])}")
    elif mode == "segment":
        caption = (f"Points {_pt_label(pts[0])} and "
                   f"{_pt_label(pts[1])}")
    else:
        caption = "Points " + ", ".join(
            _pt_label(p) for p in pts)
    plot = _Plot(rng[0], rng[1], rng[2], rng[3], caption)
    plot.grid()
    if mode == "triangle":
        plot.polygon(pts)
    elif mode == "line":
        (x1, y1), (x2, y2) = pts
        if x1 == x2:
            plot.line((x1, rng[2]), (x1, rng[3]))
        else:
            m = (y2 - y1) / (x2 - x1)
            plot.line((rng[0], y1 + m * (rng[0] - x1)),
                      (rng[1], y1 + m * (rng[1] - x1)))
    elif mode == "segment":
        plot.line(pts[0], pts[1], colour=_MUTED, width=1.6,
                  dash="5 4")
    for p in pts:
        plot.dot(p[0], p[1], _pt_label(p), dy=-9)
    return {"svg": plot.svg(), "caption": caption,
            "_mode": mode, "_pts": pts}


def _line_equation(pts):
    """(expr in x, or ('vertical', a)) through two points,
    exact — or None."""
    (x1, y1), (x2, y2) = [
        (sp.nsimplify(a, rational=True),
         sp.nsimplify(b, rational=True)) for a, b in pts]
    if x1 == x2:
        return ("vertical", x1)
    m = (y2 - y1) / (x2 - x1)
    return m * _X + (y1 - m * x1)


# ---------------------------------------------------------------------------
# Statistics charts: bar & pie from data in the question
# ---------------------------------------------------------------------------

_LABEL_RE = re.compile(
    r"^[A-Za-z\u0900-\u097F][A-Za-z0-9\u0900-\u097F .\-]{0,11}$")
_PALETTE = ["#2f7d6e", "#b3541e", "#405a8c", "#8c6d1f",
            "#6e4a8c", "#35707e", "#94568a", "#5d7a2e"]


def _chunked_pairs(seg):
    """Comma-chunks that are EACH one "Label 40" or
    "Label: 40" pair ("Maths 40, English 30, Science
    25"). Every chunk must match — a single stray chunk
    kills the shape, so prose never becomes data."""
    chunks = [c for c in re.split(r"[,;]", seg) if c.strip()]
    if not (2 <= len(chunks) <= 8):
        return []
    for pat in (r"^\s*([A-Za-z\u0900-\u097F]"
                r"[A-Za-z\u0900-\u097F ]{0,11}?)\s*[:=]\s*"
                r"(\d+(?:\.\d+)?)\s*%?\s*$",
                r"^\s*([A-Za-z\u0900-\u097F]"
                r"[A-Za-z\u0900-\u097F ]{0,11}?)\s+"
                r"(\d+(?:\.\d+)?)\s*%?\s*$"):
        pairs = []
        for c in chunks:
            cm = re.match(pat, c)
            if cm is None:
                pairs = None
                break
            pairs.append((cm.group(1).strip(),
                          float(cm.group(2))))
        if pairs:
            return pairs
    return []


def _pairs_from_seg(seg):
    """The stated (label, value) pairs in one data
    segment, trying each stated shape in turn."""
    seg = seg.strip().lstrip(":;-–— ").strip()
    for w in ("for ", "of ", "the "):
        if seg.lower().startswith(w):
            seg = seg[len(w):]
            break
    pairs = _chunked_pairs(seg)
    if len(pairs) >= 2:
        return pairs
    pairs = []
    for lm in re.finditer(
            r"([A-Za-z\u0900-\u097F][A-Za-z\u0900-\u097F ]{0,11}?)"
            r"\s*[:=]\s*(\d+(?:\.\d+)?)", seg):
        pairs.append((lm.group(1).strip(),
                      float(lm.group(2))))
    if len(pairs) >= 2:
        return pairs
    pairs = []
    for lm in re.finditer(
            r"\b([A-Za-z])\s+(\d+(?:\.\d+)?)\b", seg):
        pairs.append((lm.group(1), float(lm.group(2))))
    if len(pairs) >= 2:
        return pairs
    lm = re.search(
        r"([A-Za-z][A-Za-z, ]*?)\s*(?:are|:|-)\s*"
        r"((?:\d+(?:\.\d+)?\s*,\s*)*\d+(?:\.\d+)?)", seg)
    if lm:
        labels = [s.strip() for s in
                  lm.group(1).split(",") if s.strip()]
        values = [float(v) for v in
                  lm.group(2).split(",")]
        if len(labels) == len(values) and len(labels) >= 2:
            return list(zip(labels, values))
    return []


def _chart_data(question, trigger_re):
    """[(label, value)] stated in the question after the
    chart trigger, or None. Stated shapes: comma-chunked
    "Label 40" / "Label: 40" pairs, "A: 10" pairs, "A 10"
    single-letter pairs, and the two-list form "A, B, C
    are 10, 20, 15". A "topic:" prefix ("for fruits:
    Mango 30, …") is tried both whole and dropped."""
    q_raw = str(question or "")
    m = trigger_re.search(_norm(q_raw))
    if m is None:
        return None
    seg = q_raw[m.end():]
    candidates = [seg]
    if ":" in seg:
        head, rest = seg.split(":", 1)
        if not any(ch.isdigit() for ch in head) \
                and len(head) <= 30:
            candidates.append(rest)
    pairs = []
    for cand in candidates:
        pairs = _pairs_from_seg(cand)
        if len(pairs) >= 2:
            break
    if not (2 <= len(pairs) <= 8):
        return None
    seen, out = set(), []
    for label, value in pairs:
        label = " ".join(label.split())
        if label.lower() in seen or value < 0:
            return None
        if not _LABEL_RE.match(label):
            return None
        seen.add(label.lower())
        out.append((label, value))
    if sum(v for _, v in out) <= 0:
        return None
    return out


def _bar_figure(data):
    caption = "Bar graph: " + ", ".join(
        f"{label} = {fmt_num(v)}" for label, v in data)
    width, height = 340, 268
    L, R, T, B = 36, 10, 14, 34
    pw, ph = width - L - R, height - T - B
    vmax = max(v for _, v in data)
    step = _nice_step(vmax, target=5)
    top = math.ceil(vmax / step) * step
    parts = []
    for v in _ticks(0, top, step):
        py = T + ph - v / top * ph
        parts.append(
            f'<line x1="{L}" y1="{py:.1f}" x2="{width - R}" '
            f'y2="{py:.1f}" stroke="{_GRID}" '
            f'stroke-width="1"/>')
        parts.append(_text(L - 5, py + 3.5,
                           _tick_label(v, step), 10, _MUTED,
                           anchor="end"))
    parts.append(
        f'<line x1="{L}" y1="{T}" x2="{L}" y2="{T + ph}" '
        f'stroke="{_MUTED}" stroke-width="1.4"/>')
    parts.append(
        f'<line x1="{L}" y1="{T + ph}" x2="{width - R}" '
        f'y2="{T + ph}" stroke="{_MUTED}" stroke-width="1.4"/>')
    slot = pw / len(data)
    bw = min(slot * 0.58, 54)
    for i, (label, v) in enumerate(data):
        cx = L + slot * (i + 0.5)
        bh = v / top * ph if top else 0
        parts.append(
            f'<rect x="{cx - bw / 2:.1f}" y="{T + ph - bh:.1f}" '
            f'width="{bw:.1f}" height="{bh:.1f}" '
            f'fill="{_PALETTE[i % len(_PALETTE)]}" '
            f'fill-opacity="0.85"/>')
        parts.append(_text(cx, T + ph - bh - 5, fmt_num(v),
                           11, _INK, weight="bold"))
        parts.append(_text(cx, T + ph + 16,
                           _xml_escape(label), 11, _INK))
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


def _pie_figure(data):
    total = sum(v for _, v in data)
    caption = "Pie chart: " + ", ".join(
        f"{label} = {fmt_num(v)}" for label, v in data)
    width, height = 340, 250
    cx, cy, r = 118, 122, 96
    parts = []
    ang = -90.0
    legend = []
    for i, (label, v) in enumerate(data):
        sweep = v / total * 360.0
        a1 = math.radians(ang)
        a2 = math.radians(ang + sweep)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        x2, y2 = cx + r * math.cos(a2), cy + r * math.sin(a2)
        large = 1 if sweep > 180 else 0
        colour = _PALETTE[i % len(_PALETTE)]
        if sweep >= 359.9:
            parts.append(
                f'<circle cx="{cx}" cy="{cy}" r="{r}" '
                f'fill="{colour}" fill-opacity="0.85"/>')
        else:
            parts.append(
                f'<path d="M {cx} {cy} L {x1:.1f} {y1:.1f} '
                f'A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z" '
                f'fill="{colour}" fill-opacity="0.85" '
                f'stroke="#ffffff" stroke-width="1.5"/>')
        pct = v / total * 100.0
        pct_s = (str(int(round(pct))) if abs(pct - round(pct))
                 < 0.05 else f"{pct:.1f}")
        if sweep >= 28:
            mid = math.radians(ang + sweep / 2)
            lx, ly = cx + r * 0.62 * math.cos(mid), \
                cy + r * 0.62 * math.sin(mid)
            parts.append(_text(lx, ly + 4, pct_s + "%", 11,
                               "#ffffff", weight="bold"))
        legend.append((colour, label, pct_s))
        ang += sweep
    ly = cy - r + 6
    for colour, label, pct_s in legend:
        parts.append(
            f'<rect x="232" y="{ly - 9}" width="11" '
            f'height="11" fill="{colour}"/>')
        parts.append(_text(248, ly + 2,
                           f"{label} {pct_s}%",
                           11, _INK, anchor="start"))
        ly += 21
    return {"svg": _svg_open(width, height, caption)
            + "".join(parts) + "</svg>",
            "caption": caption}


# ---------------------------------------------------------------------------
# Constructed graph answers (steps + figure)
# ---------------------------------------------------------------------------

_CHART_VETO = {"kitne", "kitna", "kitni", "difference",
               "antar", "अंतर", "more", "less"}


def _function_steps(kind, expr, facts, hindi):
    f = fmt(expr)
    if kind[0] == "poly":
        poly = kind[1]
        deg = poly.degree()
        steps = [f"y = {f} लो।" if hindi else f"Take y = {f}."]
        roots = [r for r in facts.get("roots", [])
                 if _exactish(r)]
        if deg == 1:
            c = poly.nth(0)
            steps.append(
                f"y-अंतःखंड: x = 0 रखने पर → y = {fmt_num(c)}।"
                if hindi else
                f"y-intercept: put x = 0 → y = {fmt_num(c)}.")
            if roots:
                steps.append(
                    f"x-अंतःखंड: y = 0 रखने पर → "
                    f"x = {fmt_num(roots[0])}।" if hindi else
                    f"x-intercept: put y = 0 → "
                    f"x = {fmt_num(roots[0])}.")
            steps.append(
                "दोनों बिंदुओं को सीधी रेखा से जोड़ो।"
                if hindi else
                "Join the two points with a straight line.")
            return steps
        if deg == 2:
            if len(roots) >= 2:
                steps.append(
                    f"मूल: x = {fmt_num(roots[0])} और "
                    f"x = {fmt_num(roots[1])} — वक्र x-अक्ष को "
                    f"यहाँ काटता है।" if hindi else
                    f"Roots: x = {fmt_num(roots[0])} and "
                    f"x = {fmt_num(roots[1])} — the curve "
                    f"cuts the x-axis here.")
            elif len(roots) == 1:
                steps.append(
                    f"मूल: x = {fmt_num(roots[0])} — वक्र "
                    f"x-अक्ष को यहाँ छूता है।" if hindi else
                    f"Root: x = {fmt_num(roots[0])} — the "
                    f"curve touches the x-axis here.")
            else:
                steps.append(
                    "कोई वास्तविक मूल नहीं — वक्र x-अक्ष को "
                    "नहीं काटता।" if hindi else
                    "No real roots — the curve does not "
                    "cut the x-axis.")
            vx, vy = facts["vertex"]
            steps.append(
                f"शीर्ष: ({fmt_num(vx)}, {fmt_num(vy)})।"
                if hindi else
                f"Vertex: ({fmt_num(vx)}, {fmt_num(vy)}).")
            steps.append(
                f"y-अंतःखंड: x = 0 रखने पर → "
                f"y = {fmt_num(facts['y0'])}।" if hindi else
                f"y-intercept: put x = 0 → "
                f"y = {fmt_num(facts['y0'])}.")
            steps.append(
                "बिंदुओं को चिकने परवलय से जोड़ो।"
                if hindi else
                "Join the points with a smooth parabola.")
            return steps
        steps.append(
            f"y-अंतःखंड: x = 0 रखने पर → "
            f"y = {fmt_num(facts['y0'])}।" if hindi else
            f"y-intercept: put x = 0 → "
            f"y = {fmt_num(facts['y0'])}.")
        if roots:
            steps.append(
                "वास्तविक मूल: " if hindi else "Real roots: "
                + ", ".join(f"x = {fmt_num(r)}"
                            for r in roots) + "।"
                if hindi else
                "Real roots: " + ", ".join(
                    f"x = {fmt_num(r)}" for r in roots) + ".")
        steps.append(
            "बिंदुओं को चिकने वक्र से जोड़ो।" if hindi
            else "Join the plotted points with a smooth "
                 "curve.")
        return steps
    if kind[0] == "trig":
        _, name, amp, _k = kind
        a = abs(amp)
        steps = [f"y = {f} लो।" if hindi else f"Take y = {f}."]
        steps.append(
            f"तरंग हर 2π पर दोहराती है; सबसे ऊँचा मान "
            f"{fmt_num(a)} और सबसे नीचा {fmt_num(-a)} है।"
            if hindi else
            f"The wave repeats every 2π; its highest "
            f"value is {fmt_num(a)} and lowest is "
            f"{fmt_num(-a)}.")
        steps.append(
            "वही तरंग दोनों ओर चलती रहती है।" if hindi
            else "The same wave continues on both sides.")
        return steps
    if kind[0] == "abs":
        vx = facts["vertex_x"]
        return [
            f"y = {f} लो।" if hindi else f"Take y = {f}.",
            f"V का कोना ({fmt_num(vx)}, 0) पर है।" if hindi
            else f"The corner of the V is at "
                 f"({fmt_num(vx)}, 0).",
            "कोने से दोनों ओर ऊपर जाती सीधी किरणें बनाओ।"
            if hindi else
            "From the corner, draw the two straight rays "
            "going up on both sides.",
        ]
    a = facts["asymptote"]
    steps = [f"y = {f} लो।" if hindi else f"Take y = {f}."]
    steps.append(
        f"वक्र x = {fmt_num(a)} वाली रेखा को कभी नहीं "
        f"छूता — यह उसकी ऊर्ध्वाधर अनंतस्पर्शी है।"
        if hindi else
        f"The curve never touches the line "
        f"x = {fmt_num(a)} — that is its vertical "
        f"asymptote.")
    if facts.get("y0") is not None:
        steps.append(
            f"y-अंतःखंड: x = 0 रखने पर → "
            f"y = {fmt_num(facts['y0'])}।" if hindi else
            f"y-intercept: put x = 0 → "
            f"y = {fmt_num(facts['y0'])}.")
    steps.append(
        "अनंतस्पर्शी के दोनों ओर बिंदु बनाकर हर ओर चिकना "
        "वक्र जोड़ो।" if hindi else
        "Plot points on both sides of the asymptote and "
        "join each side with a smooth curve.")
    return steps


def _function_answer(found, hindi):
    kind, expr = found[0]
    plot, facts = _function_figure(kind, expr)
    answer = (f"y = {fmt(expr)} का ग्राफ" if hindi
              else f"Graph of y = {fmt(expr)}")
    return {"type": "plot", "op": "graph",
            "answer": answer,
            "steps": _function_steps(kind, expr, facts,
                                     hindi),
            "figure": {"svg": plot.svg(),
                       "caption": plot.caption}}


def _coord_answer(question, hindi):
    fig = _coord_figure(question)
    if fig is None:
        return None
    mode = fig.pop("_mode")
    pts = fig.pop("_pts")
    labels = ", ".join(_pt_label(p) for p in pts)
    if mode == "points":
        steps = [
            f"बिंदु: {labels}।" if hindi
            else f"Points: {labels}.",
            "हर बिंदु को वहाँ बनाओ जहाँ उसके x और y मान "
            "मिलते हैं, और नाम लिखो।" if hindi else
            "Mark each point where its x and y values "
            "meet, and label it.",
        ]
        answer = (f"बिंदु बनाए गए: {labels}" if hindi
                  else f"Points plotted: {labels}")
    elif mode == "line":
        eq = _line_equation(pts)
        if isinstance(eq, tuple):  # ("vertical", a)
            va = eq[1]
            steps = [
                f"बिंदु: {_pt_label(pts[0])}, "
                f"{_pt_label(pts[1])}।" if hindi else
                f"Points: {_pt_label(pts[0])}, "
                f"{_pt_label(pts[1])}.",
                f"दोनों बिंदुओं का x = {fmt_num(va)} है, "
                f"इसलिए रेखा ऊर्ध्वाधर है: x = "
                f"{fmt_num(va)}।" if hindi else
                f"Both points have x = {fmt_num(va)}, "
                f"so the line is vertical: "
                f"x = {fmt_num(va)}.",
            ]
            answer = (f"{_pt_label(pts[0])} और "
                      f"{_pt_label(pts[1])} से जाने वाली "
                      f"रेखा: x = {fmt_num(va)}" if hindi
                      else f"Line through "
                           f"{_pt_label(pts[0])} and "
                           f"{_pt_label(pts[1])}: "
                           f"x = {fmt_num(va)}")
        else:
            (x1, y1), (x2, y2) = pts
            m = (sp.nsimplify(y2, rational=True)
                 - sp.nsimplify(y1, rational=True)) / \
                (sp.nsimplify(x2, rational=True)
                 - sp.nsimplify(x1, rational=True))
            steps = [
                f"बिंदु: {_pt_label(pts[0])}, "
                f"{_pt_label(pts[1])}।" if hindi else
                f"Points: {_pt_label(pts[0])}, "
                f"{_pt_label(pts[1])}.",
                f"ढाल m = ({fmt_num(y2)} − {fmt_num(y1)}) "
                f"/ ({fmt_num(x2)} − {fmt_num(x1)}) = "
                f"{fmt_num(m)}।" if hindi else
                f"Slope m = ({fmt_num(y2)} − "
                f"{fmt_num(y1)}) / ({fmt_num(x2)} − "
                f"{fmt_num(x1)}) = {fmt_num(m)}.",
                f"रेखा: y = {fmt(eq)}।" if hindi
                else f"Line: y = {fmt(eq)}.",
                "दोनों बिंदुओं से जाने वाली रेखा बनाओ।"
                if hindi else
                "Draw the line through both points.",
            ]
            answer = (f"{_pt_label(pts[0])} और "
                      f"{_pt_label(pts[1])} से जाने वाली "
                      f"रेखा: y = {fmt(eq)}" if hindi else
                      f"Line through {_pt_label(pts[0])} "
                      f"and {_pt_label(pts[1])}: "
                      f"y = {fmt(eq)}")
    else:  # triangle
        steps = [
            f"शीर्ष: {labels}।" if hindi
            else f"Vertices: {labels}.",
            "तीनों बिंदुओं को एक-एक करके जोड़ो और "
            "त्रिभुज बंद करो।" if hindi else
            "Join the three points one by one and "
            "close the triangle.",
        ]
        answer = (f"त्रिभुज जिसके शीर्ष {labels} हैं"
                  if hindi else
                  f"Triangle with vertices {labels}")
    return {"type": "geometry", "op": "graph",
            "answer": answer, "steps": steps,
            "figure": fig}


def _inequality_answer(question, hindi):
    got = _solve_inequality(question)
    if got is None:
        return None
    sol, (lhs_t, rel, rhs_t, a, b, frel, bound) = got
    steps = [f"{lhs_t} {rel} {rhs_t}"]
    moved = f"{fmt_num(a)}x {rel} {fmt_num(b)}"
    if moved != steps[0]:
        steps.append(moved)
    final = _solution_text(sol)
    if final != steps[-1]:
        steps.append(final)
    if sol[0] == "ray":
        _, _, direction, closed = sol
        side = "दाईं" if direction > 0 else "बाईं"
        cir = "भरा गोला (शामिल है)" if closed \
            else "खुला गोला (शामिल नहीं है)"
        steps.append(
            f"संख्या रेखा पर {fmt_num(bound)} पर {cir} "
            f"और {side} ओर छाया।" if hindi else
            f"On the number line: a "
            f"{'filled' if closed else 'open'} circle at "
            f"{fmt_num(bound)} "
            f"({'included' if closed else 'not included'})"
            f" and shading to the "
            f"{'right' if direction > 0 else 'left'}.")
    else:
        steps.append(
            "संख्या रेखा पर दोनों सिरों के बीच का हिस्सा "
            "छाया है।" if hindi else
            "On the number line, the part between the "
            "two ends is shaded.")
    return {"type": "algebra", "op": "graph",
            "answer": final, "steps": steps,
            "figure": _numline_figure(sol)}


def _bar_answer(data, hindi):
    fig = _bar_figure(data)
    listing = ", ".join(f"{label} = {fmt_num(v)}"
                        for label, v in data)
    steps = [
        f"मान: {listing}।" if hindi
        else f"Values: {listing}.",
        "हर item के लिए उसके मान के बराबर ऊँचाई का "
        "दंड बनाओ।" if hindi else
        "Draw one bar for each item, with height "
        "equal to its value.",
    ]
    answer = (f"दंड आलेख: {listing}" if hindi
              else fig["caption"])
    return {"type": "plot", "op": "graph",
            "answer": answer, "steps": steps,
            "figure": fig}


def _pie_answer(data, hindi):
    fig = _pie_figure(data)
    total = sum(v for _, v in data)
    angles = ", ".join(
        f"{label}: {fmt_num(v / total * 360)}°"
        for label, v in data)
    steps = [
        f"कुल = {fmt_num(total)}।" if hindi
        else f"Total = {fmt_num(total)}.",
        "हर हिस्से का कोण = हिस्सा ÷ कुल × 360°।"
        if hindi else
        "Angle of each slice = value ÷ total × 360°.",
        f"कोण: {angles}।" if hindi else f"Angles: {angles}.",
    ]
    answer = (f"वृत्त आलेख: " + ", ".join(
        f"{label} = {fmt_num(v)}" for label, v in data)
        if hindi else fig["caption"])
    return {"type": "plot", "op": "graph",
            "answer": answer, "steps": steps,
            "figure": fig}


def _build_answer(question, hindi=False):
    """A full graph answer for a PURE graph/chart/number-
    line request, or None. Shared by graph_result (the
    failure-path layer) and graph_upgrade (the real-branch
    repair): both gates live here — an explicit picture
    trigger AND no surviving solve verb."""
    q = _norm(question)
    if not _any_trigger(q) or not _is_pure(q):
        return None
    if _wants_bar(q):
        if _tokens(q) & _CHART_VETO:
            return None
        data = _chart_data(question, _BAR_RE)
        return _bar_answer(data, hindi) if data else None
    if _wants_pie(q):
        if _tokens(q) & _CHART_VETO:
            return None
        data = _chart_data(question, _PIE_RE)
        return _pie_answer(data, hindi) if data else None
    if _wants_numline(q) or _wants_graph(q):
        ineq = _inequality_answer(question, hindi)
        if ineq is not None:
            return ineq
    coord = _coord_answer(question, hindi)
    if coord is not None:
        return coord
    found = _extract_function(question)
    if found:
        return _function_answer(found, hindi)
    return None


# ---------------------------------------------------------------------------
# Entry points for fallback.py — never raise
# ---------------------------------------------------------------------------

def graph_result(question, hindi=False):
    """The graph layer: a full answer for a graph request
    every solving layer missed, or None."""
    try:
        return _build_answer(question, hindi)
    except Exception:
        return None


def graph_upgrade(question, result, hindi=False):
    """Repair a PURE graph request the solver answered as
    something else (a stray equation solve). Fires only
    when the built graph answer exists and the standing
    result is not itself a graph answer."""
    try:
        if not isinstance(result, dict):
            return None
        if result.get("op") == "graph" \
                or result.get("figure"):
            return None
        if result.get("fallback") \
                or result.get("fallback_kind"):
            return None
        return _build_answer(question, hindi)
    except Exception:
        return None


def _plot_result_figure(question, result):
    """Rebuild a matplotlib plot result (op == "graph") as
    a verified SVG: the function parsed from the question
    must equal the expression the plotter itself used."""
    theirs = str(result.get("expression", "") or "")
    if not theirs:
        return None
    found = _extract_function(question, multi=True)
    if not found:
        return None
    their_exprs = []
    for part in theirs.split(" and "):
        try:
            their_exprs.append(parse_expression(part.strip()))
        except Exception:
            return None
    if len(their_exprs) != len(found):
        return None
    used = set()
    for _, e in found:
        hit = None
        for i, t in enumerate(their_exprs):
            if i not in used and sp.simplify(e - t) == 0:
                hit = i
                break
        if hit is None:
            return None
        used.add(hit)
    if len(found) == 1:
        plot, _ = _function_figure(found[0][0], found[0][1])
        return {"svg": plot.svg(), "caption": plot.caption}
    (c1, e1), (c2, e2) = found
    p1, _ = _function_figure(c1, e1)
    p2, _ = _function_figure(c2, e2)
    lo = min(p1.xmin, p2.xmin)
    hi = max(p1.xmax, p2.xmax)
    ymin = min(p1.ymin, p2.ymin)
    ymax = max(p1.ymax, p2.ymax)
    caption = f"Graphs of y = {fmt(e1)} and y = {fmt(e2)}"
    plot = _Plot(lo, hi, ymin, ymax, caption)
    plot.grid()
    plot.curve(_segments(_sample(e1, _linspace(lo, hi, 220))))
    plot.curve(_segments(_sample(e2, _linspace(lo, hi, 220))),
               colour=_ACCENT2)
    return {"svg": plot.svg(), "caption": caption}


def graph_figure_for(question, result):
    """Attach-only figures for real answers (see the
    module docstring). The caller (fallback._with_figure)
    drops the matplotlib "image" when this returns a
    figure for an op == "graph" result — one graph, not
    two."""
    try:
        return _graph_figure_for(question, result)
    except Exception:
        return None


def _graph_figure_for(question, result):
    if not isinstance(result, dict):
        return None
    if result.get("fallback") or result.get("fallback_kind"):
        return None
    q = _norm(question)
    op = str(result.get("op", ""))
    if op == "graph":
        return _plot_result_figure(question, result)
    if op == "inequality" and (_wants_numline(q)
                               or _wants_graph(q)):
        got = _solve_inequality(question)
        if got is not None and \
                _ineq_matches_result(got[0], result):
            return _numline_figure(got[0])
        return None
    if (_wants_graph(q) or _wants_numline(q)) \
            and op in ("distance", "midpoint"):
        pts = _points(question)
        if len(pts) != 2:
            return None
        ans = str(result.get("answer", "") or "")
        if op == "distance":
            (x1, y1), (x2, y2) = [
                (sp.nsimplify(a, rational=True),
                 sp.nsimplify(b, rational=True))
                for a, b in pts]
            d = sp.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if fmt(d) not in ans and \
                    fmt_num(float(d)) not in ans:
                return None
        else:
            mx = (pts[0][0] + pts[1][0]) / 2
            my = (pts[0][1] + pts[1][1]) / 2
            if fmt_num(mx) not in ans or \
                    fmt_num(my) not in ans:
                return None
        fig = _coord_figure(question, result=result)
        if fig is None:
            return None
        fig.pop("_mode", None)
        fig.pop("_pts", None)
        return fig
    return None
