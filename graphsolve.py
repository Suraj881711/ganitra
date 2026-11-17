"""Wave 143: graph-METHOD solving ("graph se solve").

Wave 128 (graphs.py) draws a verified graph when the
student asks for a picture — and deliberately stays out
of everything else: its purity gate vetoes any ask that
also carries a solve verb, and its chart builder refuses
chart-READING questions. Suraj's standing order (17 Nov
2026) is the opposite for genuine graph questions: "agar
question graph waale hai toh graph se solve karana hai"
— a graph-type question must be SOLVED USING THE GRAPH,
not merely answered with a graph attached.

This module lifts exactly those two limits, for three
genuine graph-method shapes, under Wave 128's own
correctness law (the picture is built from the same
numbers the answer uses, and every read-off is
cross-checked before it is served):

1. A PAIR OF LINEAR EQUATIONS by the graphical method
   ("by graphical method", "graph se hal karo", "draw
   the graph and find the solution", "ग्राफीय विधि…").
   Both lines are drawn from exact table points; the
   solution is READ OFF the intersection of the drawn
   lines — computed from the drawn lines' own points by
   an independent determinant formula — and served only
   when that read-off agrees exactly with the algebraic
   solution of the same pair. On any disagreement this
   layer returns None and the chain serves the plain
   algebraic answer WITHOUT the graph claim (the picture
   never lies). Parallel lines are read off as "no
   solution" (they never meet) and coincident lines as
   "infinitely many solutions" (the same line twice) —
   both facts verified from the drawn points themselves.

2. ZEROS OF A POLYNOMIAL from its graph ("graph se
   zeros batao", "draw the graph … and find its zeros",
   "graph se kitne zero hai"): the Wave 128 figure with
   its x-intercepts marked; the zeros are the intercepts,
   cross-checked two independent ways (sp.solve vs
   sp.real_roots, each root plugged back into the
   polynomial). Only Wave 128's supported range
   (polynomials of degree 2–3 with exact roots).

3. CHART READING with the data IN the question text
   ("bar graph banao: A 10, B 20, C 15 — sabse zyada kis
   ka hai", "… A aur B me kitna antar hai", "… kul
   kitna hai"): the chart is drawn (Wave 128's builder)
   AND the sub-question is answered from the chart data
   — maximum / minimum / total / the difference of two
   named items — computed exactly from the parsed pairs
   and stated as read off the graph.

Routing law: an EXPLICIT graph-method phrase is what
routes a question here. A pair with no graph phrase
keeps its byte-identical algebraic answer; a solve verb
with an incidental graph mention ("solve 2x + 3 = 7 and
draw its graph") keeps Wave 128's veto; a pure plotting
ask stays Wave 128's. Entry points (never raise; None =
"not mine / not safe"), called from fallback.py:

- graphsolve_upgrade(question, result, hindi): the real
  branch — a graphical pair (or zeros ask) the solver
  already answered algebraically; the graphical answer
  stands instead only when it agrees with the standing
  answer, so a disagreement can never replace a correct
  algebraic answer with a graph claim.
- graphsolve_result(question, hindi): the failure path —
  graph-method asks every solving layer missed (the
  parallel / coincident phrasings and the mixed
  "draw the graph and find…" shapes end at not-found
  today, and "kitne zero hai graph se" ends at a salvage
  fragment).
"""

import math
import re

import sympy as sp

import graphs as _g
from solver.expression_parser import fmt, fmt_num, parse_expression

_X, _Y = sp.symbols("x y")


def _norm(question):
    return _g._norm(question)


# ---------------------------------------------------------------------------
# 1. A linear pair by the graphical method
# ---------------------------------------------------------------------------

# The explicit graph-METHOD phrases. A parseable pair is
# also required, so an incidental "graph" word alone can
# never route a question here.
_PAIR_TRIGGER = re.compile(
    r"graphical|ग्राफीय|ग्राफ़ीय|ग्राफ\s*विधि|graph\s+vidhi|"
    r"graph\s+se\b|by\s+graph\b|using\s+(the\s+)?graph|"
    r"graph\s+bana\s*kar|graph\s+banakar|"
    r"draw\s+the\s+graph\s+and\s+(?:find|solve)|"
    r"aalekh\s+se|आलेख\s+से|graph\s+method")

_PAIR_SPLIT = re.compile(r"[,;]|\band\b|\baur\b|तथा|&")


def _kept_tokens(seg):
    """The maths tokens of one segment: a token survives
    when it carries a digit, is exactly x / y, or consists
    only of maths characters — framing words ("graphical
    method se solve karo", "ko", "the pair of") drop out,
    so the segment that remains is the bare equation."""
    out = []
    for tok in seg.split():
        t = tok.strip(" \t:?।!\"'")
        if not t:
            continue
        if any(ch.isdigit() for ch in t):
            out.append(t)
        elif t in ("x", "y"):
            out.append(t)
        elif all(ch in "+-*/^()=.<>≤≥√" for ch in t):
            out.append(t)
        elif all(ch in "0123456789xy+-*/^()=." for ch in t):
            out.append(t)
    return out


def _parse_equation(seg):
    """One segment -> (a, b, c) with a·x + b·y = c in exact
    rationals, or None. The segment must reduce to exactly
    one '=' whose two sides parse to a linear form in x
    and y only."""
    toks = _kept_tokens(seg)
    if not toks:
        return None
    text = " ".join(toks)
    if text.count("=") != 1:
        return None
    lhs_t, rhs_t = text.split("=")
    if not lhs_t.strip() or not rhs_t.strip():
        return None
    try:
        expr = parse_expression(lhs_t) - parse_expression(rhs_t)
    except Exception:
        return None
    if not isinstance(expr, sp.Expr):
        return None
    if not expr.free_symbols.issubset({_X, _Y}):
        return None
    try:
        poly = sp.Poly(expr, _X, _Y)
    except Exception:
        return None
    if poly is None or poly.total_degree() > 1:
        return None
    coeffs = []
    for mon in (_X, _Y, sp.Integer(1)):
        v = poly.coeff_monomial(mon)
        try:
            v = sp.nsimplify(v, rational=True)
        except Exception:
            return None
        if not isinstance(v, sp.Rational) or v.q > 1000:
            return None
        coeffs.append(v)
    a, b, k = coeffs
    if a == 0 and b == 0:
        return None
    return a, b, -k          # a·x + b·y + k = 0 → = c


def _extract_pair(question):
    """[(a, b, c), (a, b, c)] for the question's pair of
    linear equations, or None. Exactly two segments may
    parse as equations — a third kills the shape (it is
    no longer a pair ask)."""
    q = _norm(question)
    eqs, seen = [], set()
    for seg in _PAIR_SPLIT.split(q):
        got = _parse_equation(seg)
        if got is not None and got not in seen:
            seen.add(got)
            eqs.append(got)
    if len(eqs) != 2:
        return None
    return eqs


def _eq_text(a, b, c):
    return f"{fmt(a * _X + b * _Y)} = {fmt_num(c)}"


def _pair_classify(e1, e2):
    """("unique", (sx, sy)) / ("parallel", None) /
    ("coincident", None) for two (a, b, c) triples,
    solved exactly."""
    a1, b1, c1 = e1
    a2, b2, c2 = e2
    d = a1 * b2 - a2 * b1
    if d != 0:
        try:
            sol = sp.solve(
                [sp.Eq(a1 * _X + b1 * _Y, c1),
                 sp.Eq(a2 * _X + b2 * _Y, c2)],
                (_X, _Y), dict=True)
        except Exception:
            return None, None
        if len(sol) != 1:
            return None, None
        sx = sp.simplify(sol[0][_X])
        sy = sp.simplify(sol[0][_Y])
        if not (sx.is_rational and sy.is_rational):
            return None, None
        return "unique", (sx, sy)
    if a1 * c2 == a2 * c1 and b1 * c2 == b2 * c1:
        return "coincident", None
    return "parallel", None


def _pair_table_points(a, b, c):
    """Two exact points of the line a·x + b·y = c — the
    table the graphical method is built from: the two
    intercepts when both exist, else x = 0 and x = 1
    points (a vertical line takes two heights)."""
    if b != 0:
        p1 = (sp.Integer(0), c / b)
        if a != 0 and c != 0:
            p2 = (c / a, sp.Integer(0))
        else:
            p2 = (sp.Integer(1), (c - a) / b)
        if p2 == p1:
            p2 = (sp.Integer(2), (c - 2 * a) / b)
        return p1, p2
    return (c / a, sp.Integer(0)), (c / a, sp.Integer(1))


def _pair_intersection_from_points(p1, p2, p3, p4):
    """The crossing point of the line through p1, p2 with
    the line through p3, p4 — the graph READ-OFF, computed
    from the drawn points alone (exact determinant
    formula), or None when the drawn lines are parallel.
    This is the independent computation the algebraic
    solution is cross-checked against."""
    (x1, y1), (x2, y2) = p1, p2
    (x3, y3), (x4, y4) = p3, p4
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if d == 0:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4)
          - (x1 - x2) * (x3 * y4 - y3 * x4)) / d
    py = ((x1 * y2 - y1 * x2) * (y3 - y4)
          - (y1 - y2) * (x3 * y4 - y3 * x4)) / d
    return sp.simplify(px), sp.simplify(py)


def _pair_figure(eqs, pts_list, cls, sol):
    """The two-line SVG: both lines drawn across the plot
    from their table points, table points dotted, and —
    for a unique solution — the crossing point marked
    with its coordinates (the read-off made visible)."""
    xs, ys = [0.0], [0.0]
    for pts in pts_list:
        for px, py in pts:
            xs.append(float(px))
            ys.append(float(py))
    if sol is not None:
        xs.append(float(sol[0]))
        ys.append(float(sol[1]))
    lo_x = math.floor(min(xs) - 2)
    hi_x = math.ceil(max(xs) + 2)
    lo_y = math.floor(min(ys) - 2)
    hi_y = math.ceil(max(ys) + 2)
    if hi_x - lo_x < 7:
        lo_x, hi_x = lo_x - 2, hi_x + 2
    if hi_y - lo_y < 7:
        lo_y, hi_y = lo_y - 2, hi_y + 2
    if hi_x - lo_x > 34:
        mid = (lo_x + hi_x) / 2
        lo_x, hi_x = math.floor(mid - 17), math.ceil(mid + 17)
    if hi_y - lo_y > 34:
        mid = (lo_y + hi_y) / 2
        lo_y, hi_y = math.floor(mid - 17), math.ceil(mid + 17)
    eq1, eq2 = (_eq_text(*eqs[0]), _eq_text(*eqs[1]))
    if cls == "parallel":
        caption = f"Graphs of {eq1} and {eq2} — parallel lines"
    elif cls == "coincident":
        caption = f"Graphs of {eq1} and {eq2} — the same line"
    else:
        caption = f"Graphical solution of {eq1} and {eq2}"
    plot = _g._Plot(lo_x, hi_x, lo_y, hi_y, caption)
    plot.grid()
    colours = (_g._ACCENT, _g._ACCENT2)
    for i, ((a, b, c), pts) in enumerate(zip(eqs, pts_list)):
        col = colours[i]
        if cls == "coincident" and i == 0:
            col = _g._ACCENT
        if b == 0:
            vx = float(c / a)
            plot.line((vx, lo_y), (vx, hi_y), colour=col,
                      width=2.0,
                      dash="5 4" if (cls == "coincident"
                                     and i == 1) else None)
        else:
            (x1, y1), (x2, y2) = [(float(px), float(py))
                                  for px, py in pts]
            m = (y2 - y1) / (x2 - x1)
            plot.line((lo_x, y1 + m * (lo_x - x1)),
                      (hi_x, y1 + m * (hi_x - x1)), colour=col,
                      width=2.0,
                      dash="5 4" if (cls == "coincident"
                                     and i == 1) else None)
        if cls != "coincident":
            for px, py in pts:
                plot.dot(float(px), float(py), None,
                         colour=_g._MUTED)
    if sol is not None:
        plot.dot(float(sol[0]), float(sol[1]),
                 f"({fmt_num(sol[0])}, {fmt_num(sol[1])})")
    return {"svg": plot.svg(), "caption": caption}


def _pair_line_step(a, b, c, pts, hindi):
    """One line's table step, in the graphical method's
    own words: intercepts when both exist, the vertical /
    horizontal fact when the line is axis-parallel, else
    the two table points."""
    text = _eq_text(a, b, c)
    if b == 0:
        return (f"{text} — यह खड़ी line है: x = "
                f"{fmt_num(c / a)}।" if hindi else
                f"{text} — the vertical line "
                f"x = {fmt_num(c / a)}.")
    if a == 0:
        return (f"{text} — यह आड़ी line है: y = "
                f"{fmt_num(c / b)}।" if hindi else
                f"{text} — the horizontal line "
                f"y = {fmt_num(c / b)}.")
    if c != 0:
        return (f"{text}: x = 0 रखने पर y = "
                f"{fmt_num(c / b)}; y = 0 रखने पर "
                f"x = {fmt_num(c / a)} — बिंदु "
                f"(0, {fmt_num(c / b)}) और "
                f"({fmt_num(c / a)}, 0) जोड़ो।" if hindi else
                f"{text}: put x = 0 → y = {fmt_num(c / b)}; "
                f"put y = 0 → x = {fmt_num(c / a)} — join "
                f"(0, {fmt_num(c / b)}) and "
                f"({fmt_num(c / a)}, 0).")
    (x1, y1), (x2, y2) = pts
    return (f"{text}: बिंदु ({fmt_num(x1)}, {fmt_num(y1)}) "
            f"और ({fmt_num(x2)}, {fmt_num(y2)}) जोड़ो।"
            if hindi else
            f"{text}: join the points ({fmt_num(x1)}, "
            f"{fmt_num(y1)}) and ({fmt_num(x2)}, "
            f"{fmt_num(y2)}).")


def _pair_build(question, hindi=False):
    """(result, info) for a graphical pair ask, or
    (None, None). info = {"class": ..., "sol": (sx, sy) |
    None}. The cross-check law: a unique solution is
    served only when the intersection read off the DRAWN
    lines (from their table points) equals the algebraic
    solution exactly; the parallel / coincident verdicts
    are served only when the drawn points themselves
    confirm them (directions parallel; the second line's
    points lying on the first line)."""
    q = _norm(question)
    if not _PAIR_TRIGGER.search(q):
        return None, None
    eqs = _extract_pair(question)
    if eqs is None:
        return None, None
    cls, sol = _pair_classify(*eqs)
    if cls is None:
        return None, None
    pts_list = [_pair_table_points(*e) for e in eqs]
    if cls == "unique":
        read = _pair_intersection_from_points(
            pts_list[0][0], pts_list[0][1],
            pts_list[1][0], pts_list[1][1])
        if read is None or read != sol:
            return None, None     # the picture would lie
    else:
        (x1, y1), (x2, y2) = pts_list[0]
        (x3, y3), (x4, y4) = pts_list[1]
        cross = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
        if cross != 0:
            return None, None     # drawn lines not parallel
        a1, b1, c1 = eqs[0]
        on_line = all(a1 * px + b1 * py == c1
                      for px, py in pts_list[1])
        if on_line != (cls == "coincident"):
            return None, None
    fig = _pair_figure(eqs, pts_list, cls, sol)
    steps = [
        "ग्राफीय विधि: हर equation की line बनाओ और "
        "मिलने का बिंदु पढ़ो।" if hindi else
        "Graphical method: draw the line of each "
        "equation and read the point where they meet.",
        _pair_line_step(*eqs[0], pts_list[0], hindi),
        _pair_line_step(*eqs[1], pts_list[1], hindi),
    ]
    if cls == "unique":
        sx, sy = sol
        steps.append(
            f"दोनों lines ({fmt_num(sx)}, {fmt_num(sy)}) "
            f"पर मिलती हैं — graph से यही बिंदु पढ़ा "
            f"गया।" if hindi else
            f"The two lines cross at ({fmt_num(sx)}, "
            f"{fmt_num(sy)}) — this point is read off "
            f"the graph.")
        answer = f"x = {fmt_num(sx)}, y = {fmt_num(sy)}"
    elif cls == "parallel":
        steps.append(
            "दोनों lines parallel हैं — वे कभी नहीं "
            "मिलतीं, इसलिए कोई साझा बिंदु नहीं है।"
            if hindi else
            "The two lines are parallel — they never "
            "meet, so the pair has no common point.")
        answer = "कोई हल नहीं" if hindi else "No solution"
    else:
        steps.append(
            "दोनों equations से एक ही line बनती है — "
            "line का हर बिंदु इस जोड़ी का हल है।"
            if hindi else
            "Both equations draw the same line — every "
            "point on the line solves the pair.")
        answer = ("अनन्त हल" if hindi
                  else "Infinitely many solutions")
    result = {"type": "algebra", "op": "graph_solve",
              "answer": answer, "steps": steps,
              "figure": fig}
    return result, {"class": cls, "sol": sol}


# ---------------------------------------------------------------------------
# 2. Zeros of a polynomial, read off its graph
# ---------------------------------------------------------------------------

_ZERO_RE = re.compile(r"\bzeros?\b|\bzeroes\b|शून्यक|शून्यांक")

_ZERO_STRIP = re.compile(
    r"\b(?:graphs?|plots?|plotting|draw|drawn|the|and|"
    r"find|its|of|polynomial|how|many|does|do|have|has|"
    r"from|in|is|are|zeros?|zeroes|ke|kitne|batao|se|"
    r"hai|ka|ki|ko|banao|banakar|karke|dikhao|par|"
    r"chahiye|please)\b|ग्राफ|शून्यक|शून्यांक|बनाओ|दिखाओ")


def _zeros_expr(question):
    """(classify-tuple, expr) for the polynomial whose
    zeros are asked, restricted to Wave 128's supported
    range (degree 2–3), or None. Candidates: the text
    after the last ':', after 'of', the question with the
    ask's own words stripped, and Wave 128's extractor."""
    q = _norm(question)
    cands = []
    if ":" in q:
        cands.append(q.rsplit(":", 1)[1])
    m = re.search(r"\bof\s+(.+)$", q)
    if m:
        cands.append(m.group(1))
    cands.append(_ZERO_STRIP.sub(" ", q))
    for cand in cands:
        cand = re.sub(r"^y\s*=\s*", "",
                      cand.strip(" .:?।"))
        if not cand:
            continue
        try:
            e = _g._parse(cand)
        except Exception:
            continue
        c = _g._classify(e)
        if c is not None and c[0] == "poly" \
                and c[1].degree() in (2, 3):
            return c, e
    found = _g._extract_function(question)
    if found:
        c, e = found[0]
        if c[0] == "poly" and c[1].degree() in (2, 3):
            return c, e
    return None


def _zeros_verified(expr):
    """The distinct real roots of the polynomial, exact
    and printably short, or None. Cross-checked two
    independent ways: sp.solve's root set must equal
    sp.real_roots' root set, and every root must plug
    back into the polynomial to exactly 0."""
    try:
        solved = {r for r in sp.solve(expr, _X)
                  if r.is_real}
        reals = set(sp.real_roots(expr, _X))
    except Exception:
        return None
    if len(solved) != len(reals):
        return None
    roots = []
    for r in solved:
        if not any(sp.simplify(r - s) == 0 for s in reals):
            return None
        if sp.simplify(expr.subs(_X, r)) != 0:
            return None
        if not _g._exactish(r):
            return None
        roots.append(r)
    roots.sort(key=lambda r: float(r))
    return roots


def _zeros_build(question, hindi=False):
    """(result, roots) for a zeros-from-graph ask, or
    (None, None). The figure is Wave 128's own function
    figure (its intercepts are marked from the same root
    set — asserted equal here before anything is
    served)."""
    q = _norm(question)
    if not _g._GRAPH_RE.search(q) or not _ZERO_RE.search(q):
        return None, None
    got = _zeros_expr(question)
    if got is None:
        return None, None
    kind, expr = got
    roots = _zeros_verified(expr)
    if roots is None:
        return None, None
    plot, facts = _g._function_figure(kind, expr)
    fig_roots = sorted(
        (r for r in facts.get("roots", []) if r.is_real),
        key=lambda r: float(r))
    if len(fig_roots) != len(roots) or any(
            sp.simplify(a - b) != 0
            for a, b in zip(fig_roots, roots)):
        return None, None
    f = fmt(expr)
    steps = [
        f"y = {f} का ग्राफ बनाओ।" if hindi else
        f"Draw the graph of y = {f}."]
    deriv = sp.diff(expr, _X)
    if not roots:
        steps.append(
            "ग्राफ x-अक्ष को कहीं नहीं काटता।" if hindi
            else "The graph does not cut the x-axis "
                 "anywhere.")
        answer = ("कोई शून्यक नहीं (0 शून्यक)" if hindi
                  else "No zeros (0 zeros)")
    else:
        names = " और ".join(f"x = {fmt_num(r)}"
                             for r in roots) \
            if hindi else " and ".join(
                f"x = {fmt_num(r)}" for r in roots)
        touches = [sp.simplify(deriv.subs(_X, r)) == 0
                   for r in roots]
        if len(roots) == 1 and touches[0]:
            steps.append(
                f"ग्राफ x-अक्ष को {names} पर छूता है।"
                if hindi else
                f"The graph touches the x-axis at "
                f"{names}.")
        else:
            steps.append(
                f"ग्राफ x-अक्ष को {names} पर काटता है।"
                if hindi else
                f"The graph cuts the x-axis at {names}.")
        steps.append(
            "इन्हीं बिंदुओं के x-मान ही शून्यक हैं।"
            if hindi else
            "The x-values of these points are the zeros.")
        listing = ", ".join(fmt_num(r) for r in roots)
        if hindi:
            answer = (f"शून्यक: {listing} "
                      f"(कुल {len(roots)} शून्यक)")
        else:
            answer = (f"Zeros: {listing} "
                      f"({len(roots)} zero"
                      f"{'s' if len(roots) != 1 else ''})")
    result = {"type": "algebra", "op": "graph_zeros",
              "answer": answer, "steps": steps,
              "figure": {"svg": plot.svg(),
                         "caption": plot.caption}}
    return result, roots


# ---------------------------------------------------------------------------
# 3. Chart reading: the data is IN the question
# ---------------------------------------------------------------------------

_MAX_RE = re.compile(
    r"sabse\s*(?:zyada|jyada|adhik|bada|uncha)|"
    r"सबसे\s*(?:ज़्यादा|अधिक|बड़ा|ऊँचा)|"
    r"\bmost\b|\bhighest\b|\blargest\b|\bmaximum\b|"
    r"\bbiggest\b")
_MIN_RE = re.compile(
    r"sabse\s*kam|सबसे\s*कम|"
    r"\bleast\b|\blowest\b|\bsmallest\b|\bminimum\b")
_TOTAL_RE = re.compile(
    r"कुल|\bkull?\b|\btotal\b|योग|\bsum\b|in\s+all\b")
_DIFF_RE = re.compile(
    r"अंतर|\bantar\b|\bdifference\b|फर्क|\bfark\b|"
    r"how\s+many\s+more|how\s+much\s+more")


def _chart_data_regions(question, trigger_re):
    """(data, head, tail) for a chart question, or
    (None, "", ""). data is Wave 128's validated
    [(label, value)] parse; head / tail are the
    NORMALISED texts before the chart trigger and after
    the data segment — the only places a sub-question
    can live. Candidate data segments are the text after
    the trigger cut at each sentence boundary (?, —, –,
    '. ', ';'): the shortest segment that still parses
    as complete data wins, but a candidate whose cut-off
    tail carries any digit is rejected (the sub-questions
    in scope name items and ask — they never carry a
    value; a digit in the tail means the cut ate part of
    the data or a numeric claim)."""
    raw = str(question or "")
    qn = _norm(raw)
    m = trigger_re.search(qn)
    if m is None:
        return None, "", ""
    head = qn[:m.start()]
    seg_full = raw[m.end():]
    cuts = [(len(seg_full), "")]
    for pat in (r"[?।]", r"\s+—\s+", r"\s+–\s+",
                r"\.\s+", r";\s*"):
        cm = re.search(pat, seg_full)
        if cm:
            cuts.append((cm.start(), seg_full[cm.end():]))
    for end, tail_raw in sorted(cuts, key=lambda c: c[0]):
        cand_q = raw[:m.end()] + seg_full[:end]
        data = _g._chart_data(cand_q, trigger_re)
        if not data:
            continue
        tail = _norm(tail_raw)
        if tail and any(ch.isdigit() for ch in tail):
            continue          # the cut ate real data
        return data, head, tail
    return None, "", ""


def _region_labels(region, data):
    """The data labels actually named in the sub-question
    region (whole-word, case-insensitive)."""
    out = []
    for label, _ in data:
        pat = r"(?<![a-z])" + re.escape(label.lower()) \
            + r"(?![a-z])"
        if re.search(pat, region):
            out.append(label)
    return out


def _chart_reading_build(question, hindi=False):
    """(result, data) for a chart-reading ask, or
    (None, None): the chart drawn AND one sub-question —
    difference of two named items, maximum, minimum or
    total — answered from the chart's own data, stated
    as read off the graph. No recognisable sub-question
    (or an unanswerable one) -> None, and Wave 128's
    draw-only answer stands."""
    q = _norm(question)
    is_bar = _g._wants_bar(q)
    is_pie = _g._wants_pie(q)
    if not (is_bar or is_pie):
        return None, None
    trigger_re = _g._BAR_RE if is_bar else _g._PIE_RE
    data, head, tail = _chart_data_regions(question,
                                           trigger_re)
    if data is None:
        return None, None
    head_q = head if ("?" in head or "बताओ" in head
                      or "batao" in head
                      or "sabse" in head
                      or "सबसे" in head) else ""
    region = (head_q + " " + tail).strip()
    if not region:
        return None, None
    values = {label: v for label, v in data}
    listing = ", ".join(f"{label} = {fmt_num(v)}"
                        for label, v in data)
    steps = [
        f"मान: {listing}।" if hindi
        else f"Values: {listing}.",
        "हर item के लिए उसके मान के बराबर ऊँचाई का दंड "
        "बनाओ।" if hindi and is_bar else
        "Draw one bar for each item, with height equal "
        "to its value." if is_bar else
        "हर हिस्से का कोण = हिस्सा ÷ कुल × 360°।"
        if hindi else
        "Angle of each slice = value ÷ total × 360°.",
    ]
    fig = _g._bar_figure(data) if is_bar \
        else _g._pie_figure(data)
    kind_word = ("bar" if is_bar else "slice")
    kind_word_hi = ("दंड" if is_bar else "हिस्सा")

    def _serve(answer, read_step):
        return {"type": "plot", "op": "graph_read",
                "answer": answer,
                "steps": steps + [read_step],
                "figure": fig}, data

    if _DIFF_RE.search(region):
        named = _region_labels(region, data)
        if len(named) == 2:
            (l1, v1), (l2, v2) = [(n, values[n])
                                  for n in named]
            big, small = (l1, l2) if v1 >= v2 else (l2, l1)
            d = abs(v1 - v2)
            step = (
                f"ग्राफ से पढ़ा गया: {big} "
                f"({fmt_num(values[big])}) − {small} "
                f"({fmt_num(values[small])}) = "
                f"{fmt_num(d)}।" if hindi else
                f"Read from the graph: {big} "
                f"({fmt_num(values[big])}) − {small} "
                f"({fmt_num(values[small])}) = "
                f"{fmt_num(d)}.")
            answer = (f"अंतर: {fmt_num(d)}" if hindi
                      else f"Difference: {fmt_num(d)}")
            return _serve(answer, step)
    if _MAX_RE.search(region):
        top = max(v for _, v in data)
        labels = [l for l, v in data if v == top]
        names = ", ".join(labels)
        step = (
            f"ग्राफ से पढ़ा गया: सबसे बड़ा {kind_word_hi} "
            f"{names} का है — {fmt_num(top)}।" if hindi
            else f"Read from the graph: the biggest "
                 f"{kind_word} is {names} — "
                 f"{fmt_num(top)}.")
        answer = (f"{names} — {fmt_num(top)} (सबसे ज़्यादा)"
                  if hindi else
                  f"{names} — {fmt_num(top)} (the most)")
        return _serve(answer, step)
    if _MIN_RE.search(region):
        low = min(v for _, v in data)
        labels = [l for l, v in data if v == low]
        names = ", ".join(labels)
        step = (
            f"ग्राफ से पढ़ा गया: सबसे छोटा {kind_word_hi} "
            f"{names} का है — {fmt_num(low)}।" if hindi
            else f"Read from the graph: the smallest "
                 f"{kind_word} is {names} — "
                 f"{fmt_num(low)}.")
        answer = (f"{names} — {fmt_num(low)} (सबसे कम)"
                  if hindi else
                  f"{names} — {fmt_num(low)} (the least)")
        return _serve(answer, step)
    if _TOTAL_RE.search(region):
        total = sum(v for _, v in data)
        added = " + ".join(fmt_num(v) for _, v in data)
        step = (
            f"ग्राफ से पढ़ा गया: {added} = "
            f"{fmt_num(total)}।" if hindi else
            f"Read from the graph: {added} = "
            f"{fmt_num(total)}.")
        answer = (f"कुल: {fmt_num(total)}" if hindi
                  else f"Total: {fmt_num(total)}")
        return _serve(answer, step)
    return None, None


# ---------------------------------------------------------------------------
# Entry points for fallback.py — never raise
# ---------------------------------------------------------------------------

def graphsolve_result(question, hindi=False):
    """The failure-path layer: a graph-METHOD question
    every solving layer missed — a pair solved by its
    graph, zeros read off a graph, a chart read from its
    stated data — or None."""
    try:
        built, _ = _pair_build(question, hindi)
        if built is not None:
            return built
        built, _ = _zeros_build(question, hindi)
        if built is not None:
            return built
        built, _ = _chart_reading_build(question, hindi)
        if built is not None:
            return built
    except Exception:
        return None
    return None


def _standing_xy(result):
    """The (x, y) a standing system answer claims, parsed
    from its answer text, or None."""
    ans = str(result.get("answer", "") or "")
    mx = re.search(r"\bx\s*=\s*(-?\d+(?:\.\d+)?"
                   r"(?:\s*/\s*\d+)?)", ans)
    my = re.search(r"\by\s*=\s*(-?\d+(?:\.\d+)?"
                   r"(?:\s*/\s*\d+)?)", ans)
    if not mx or not my:
        return None
    try:
        return (sp.nsimplify(mx.group(1).replace(" ", ""),
                             rational=True),
                sp.nsimplify(my.group(1).replace(" ", ""),
                             rational=True))
    except Exception:
        return None


def _standing_numbers(result):
    ans = str(result.get("answer", "") or "")
    out = set()
    for s in re.findall(r"-?\d+(?:\.\d+)?", ans):
        try:
            out.add(float(s))
        except ValueError:
            pass
    return out


def graphsolve_upgrade(question, result, hindi=False):
    """Repair a graph-METHOD ask the solver answered
    algebraically. The graphical answer stands instead
    ONLY when it agrees with the standing answer: for a
    pair, the standing (x, y) must equal the graphical
    solution; for zeros, the standing answer must name
    exactly the graph's zeros (or itself be the router's
    plot answer). Any disagreement keeps the standing
    answer byte-identical — the algebraic answer is
    served WITHOUT the graph claim."""
    try:
        if not isinstance(result, dict):
            return None
        if result.get("fallback") \
                or result.get("fallback_kind"):
            return None
        if result.get("figure"):
            return None
        q = _norm(question)
        if _PAIR_TRIGGER.search(q):
            built, info = _pair_build(question, hindi)
            if built is not None \
                    and info["class"] == "unique":
                claimed = _standing_xy(result)
                if claimed is not None \
                        and claimed == info["sol"]:
                    return built
            return None
        if _g._GRAPH_RE.search(q) and _ZERO_RE.search(q):
            built, roots = _zeros_build(question, hindi)
            if built is None:
                return None
            if result.get("op") == "graph":
                return built
            if roots:
                nums = _standing_numbers(result)
                if all(any(abs(float(r) - n) < 1e-9
                           for n in nums) for r in roots):
                    return built
            return None
    except Exception:
        return None
    return None
