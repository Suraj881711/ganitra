"""Wave 125: solver depth — the families the Wave 93 audit
left unsolved, closed with METHOD schemas (each parses the
student's own numbers and computes; nothing is ever answered
with a similar question's answer):

1. LPP (Class 12 linear programming): the symbolic form in
   Hindi / Hinglish dress ("Z = 3x + 5y ko adhiktam karo
   jabki …", "अधिकतम कीजिए Z = … जबकि …") — the English form
   already lives in applied.py, but its maxim/minim gate
   never fires for these — plus the three canonical NCERT
   word templates (two products × two resources with an
   optional per-unit profit; the cake/flour-fat form; the
   diet minimum-cost form), in English and Hinglish.
2. Probability relations (Class 12): P(A|B) / P(B|A) /
   P(A ∩ B) / P(A ∪ B) computed from the given P-values
   (including the via-union route), independence CHECKS,
   independence / mutual-exclusivity GIVEN, and the
   two-hypothesis Bayes / total-probability formula forms.
3. Conditional probability on a sample space the existing
   probability path answers UNconditionally: dice with a
   "given that the first/second die shows k" condition,
   cards given a face card, and the coin + die joint forms.
4. Homogeneous differential equations by the textbook
   method (check homogeneity, put y = vx, separate,
   integrate, put v = y/x back) — every served solution is
   verified with sympy's checkodesol — plus particular
   solutions for the "y = a when x = b" initial-condition
   phrasings the dsolve path misses, and the Hindi /
   Hinglish / "show that … and solve" wrappers.
5. Area between curves (Class 12): two explicit curves,
   curve + line, parabola y² = kx forms, two parabolas,
   circle + vertical line, sin/cos between given limits,
   the full ellipse — by exact SymPy integration.
6. Wave 103 leftovers: quadrilateral (and triangle) angles
   in a ratio, coin + die outcome counting, and g(x)-style
   function evaluation for any function letter.

Hooking (the house pattern): solver/router.py calls
solve_depth125 at the very end of _solve_question_uncached
behind the same failure-only gate as Waves 77/94/103/115,
so a question the solver already answers is never
displaced. The hijack shapes — a real-looking answer to a
different question (the Hindi-equation "z = 3" for an LPP
ask, the unconditional 5/36 for a conditional dice ask,
"y = 1" for a DE-with-IC ask, "x = 0" for a sin/cos area
ask) — are repaired by depth125_upgrade() in fallback.py,
which fires only when a strict schema settles the question
completely AND the served answer is not already the
schema's value.
"""

import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

_x = sp.symbols("x")
_y = sp.symbols("y")


def _prep(q):
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("≤", "<=").replace("≥", ">=")
    # superscript digits glued to a symbol: x² -> x^2
    s = re.sub(r"([A-Za-z\)])(\^?)([⁰¹²³⁴⁵⁶⁷⁸⁹]+)",
               lambda m: m.group(1) + "^" +
               m.group(3).translate(_SUP), s)
    return s


def _hindi(q):
    return any("ऀ" <= ch <= "ॿ" for ch in str(q or ""))


def _mk(type_, op, answer, steps, **extra):
    out = {"type": type_, "op": op, "answer": answer,
           "steps": steps}
    out.update(extra)
    return out


def _frac(fr):
    """Fraction -> 'a/b' or 'a' (the house probability style)."""
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    return f"{fr.numerator}/{fr.denominator}"


def _prob_str(fr):
    return f"{_frac(fr)} ≈ {float(fr):.4f}"


# ---------------------------------------------------------------------------
# 1. LPP — corner-point machinery (exact rational arithmetic)
# ---------------------------------------------------------------------------

def _lp_finish(oc_a, oc_b, cons, want_max, want_min, hi,
               obj_disp, names=("x", "y")):
    """cons: [(a, b, c, sense)] meaning a*x + b*y <sense> c.
    Returns the result dict, or None when the feasible
    region is empty. Unbounded directions are reported
    honestly, exactly like the Class-12 textbook."""
    x, y = _x, _y

    def feasible(px, py):
        for a, b, c, s in cons:
            v = a * px + b * py
            if s == "<=" and v > c:
                return False
            if s == ">=" and v < c:
                return False
            if s == "==" and v != c:
                return False
        return True

    corners = []
    lines = [(a, b, c) for a, b, c, _s in cons]
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            a1, b1, c1 = lines[i]
            a2, b2, c2 = lines[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = (c1 * b2 - c2 * b1) / det
            py = (a1 * c2 - a2 * c1) / det
            if feasible(px, py) and (px, py) not in corners:
                corners.append((px, py))
    if feasible(sp.Integer(0), sp.Integer(0)) and \
            (sp.Integer(0), sp.Integer(0)) not in corners:
        corners.append((sp.Integer(0), sp.Integer(0)))
    if not corners:
        return None

    def improves(dx, dy, for_max):
        for a, b, c, s in cons:
            v = a * dx + b * dy
            if s == "<=" and v > 0:
                return False
            if s == ">=" and v < 0:
                return False
            if s == "==" and v != 0:
                return False
        d = oc_a * dx + oc_b * dy
        return d > 0 if for_max else d < 0

    dirs = set()
    for a, b, c in lines:
        dirs.add((-b, a))
        dirs.add((b, -a))
    unb_max = want_max and any(improves(dx, dy, True)
                               for dx, dy in dirs)
    unb_min = want_min and any(improves(dx, dy, False)
                               for dx, dy in dirs)
    if hi:
        steps = ["व्यवहार्य क्षेत्र के कोने-बिंदु प्रतिबंधों की "
                 "सीमा रेखाओं के प्रतिच्छेद से मिलते हैं "
                 "(रैखिक Z का इष्टतम मान हमेशा किसी कोने पर "
                 "होता है):"]
    else:
        steps = ["The feasible region's corner points come "
                 "from intersecting the boundary lines of the "
                 "constraints (the optimum of a linear Z is "
                 "always at a corner):"]
    vals = []
    for (px, py) in corners:
        v = oc_a * px + oc_b * py
        vals.append((v, (px, py)))
        steps.append(f"({fmt(px)}, {fmt(py)}): "
                     f"Z = {fmt(v)}")
    parts = []
    word = None
    best = None
    if want_max:
        word = "Maximum" if not hi else "अधिकतम"
        if unb_max:
            steps.append(
                "The feasible region is unbounded in a "
                "direction that keeps increasing Z, so Z "
                "has no maximum value." if not hi else
                "व्यवहार्य क्षेत्र उस दिशा में अपरिबद्ध है "
                "जिसमें Z बढ़ता रहता है, अतः Z का कोई "
                "अधिकतम मान नहीं है।")
            parts.append("No maximum value (feasible region "
                         "is unbounded)")
        else:
            best = max(vals, key=lambda t: float(t[0]))
            steps.append(
                f"Maximum value of Z is {fmt(best[0])} at "
                f"({fmt(best[1][0])}, {fmt(best[1][1])})."
                if not hi else
                f"Z का अधिकतम मान {fmt(best[0])} है, बिंदु "
                f"({fmt(best[1][0])}, {fmt(best[1][1])}) पर।")
            parts.append(f"Maximum Z = {fmt(best[0])} at "
                         f"({fmt(best[1][0])}, "
                         f"{fmt(best[1][1])})")
    if want_min:
        word = "Minimum" if not hi else "न्यूनतम"
        if unb_min:
            steps.append(
                "The feasible region is unbounded in a "
                "direction that keeps decreasing Z, so Z "
                "has no minimum value." if not hi else
                "व्यवहार्य क्षेत्र उस दिशा में अपरिबद्ध है "
                "जिसमें Z घटता रहता है, अतः Z का कोई "
                "न्यूनतम मान नहीं है।")
            parts.append("No minimum value (feasible region "
                         "is unbounded)")
        else:
            best = min(vals, key=lambda t: float(t[0]))
            steps.append(
                f"Minimum value of Z is {fmt(best[0])} at "
                f"({fmt(best[1][0])}, {fmt(best[1][1])})."
                if not hi else
                f"Z का न्यूनतम मान {fmt(best[0])} है, बिंदु "
                f"({fmt(best[1][0])}, {fmt(best[1][1])}) पर।")
            parts.append(f"Minimum Z = {fmt(best[0])} at "
                         f"({fmt(best[1][0])}, "
                         f"{fmt(best[1][1])})")
    if not parts:
        return None
    out = _mk("applied",
              "lp_maximise" if want_max else "lp_minimise",
              "; ".join(parts), steps)
    if best is not None:
        out["value"] = float(best[0])
    return out


_MAX_WORDS = (r"maxim|adhiktam|adhik se adhik|अधिकतम|"
              r"largest|greatest|maximum")
_MIN_WORDS = (r"minim|nyoonatam|न्यूनतम|kam se kam|"
              r"least|smallest|minimum")


def _lp_symbolic(q):
    """Z = <linear expr> with inequality constraints in the
    text — any language dress. The objective must name Z and
    the constraints must ALL parse as linear inequalities in
    x and y (a strict schema: one unparseable piece and the
    whole schema declines)."""
    ql = q.lower()
    want_max = bool(re.search(_MAX_WORDS, ql))
    want_min = bool(re.search(_MIN_WORDS, ql))
    if not (want_max or want_min):
        return None
    if "corner point" in ql or "कोने" in q:
        return None  # applied._lp_corners owns that form
    mo = re.search(r"\bz\s*=\s*(.+?)(?=\s+subject\b|\s+jabki|"
                   r"\s+जबकि|\s+ka\s|\s+ko\s|,|;|$)",
                   q, re.I)
    if not mo:
        return None
    obj_text = mo.group(1).strip()
    rest = q[mo.end():]
    mc = re.search(r"subject\s+to\s+(?:the\s+)?"
                   r"(?:constraints?\s+)?|jabki|जबकि", rest, re.I)
    ctext = rest[mc.end():] if mc else rest.lstrip(" ,;")
    # the tail of a "… ka adhiktam maan nikalo jabki …" ask:
    # everything before the constraint list is wrapper.
    ctext = re.sub(r"^[^0-9xy(]*(?=[0-9xy(])", "", ctext)
    try:
        oexpr = sp.expand(parse_expression(obj_text))
    except Exception:
        return None
    x, y = _x, _y
    if not oexpr.free_symbols or \
            not oexpr.free_symbols <= {x, y}:
        return None
    oc_a, oc_b = oexpr.coeff(x), oexpr.coeff(y)
    if oexpr.subs({x: 0, y: 0}) != 0:
        return None  # a constant term: not the NCERT form
    if oc_a == 0 and oc_b == 0:
        return None
    cons = []
    if re.search(r"\bx\s*,\s*y\s*>=\s*0", ctext):
        cons += [(sp.Integer(1), sp.Integer(0), sp.Integer(0),
                  ">="),
                 (sp.Integer(0), sp.Integer(1), sp.Integer(0),
                  ">=")]
        ctext = re.sub(r"\bx\s*,\s*y\s*>=\s*0", " ", ctext)
    pieces = [p.strip(" .")
              for p in re.split(r"[,;]|\band\b|\baur\b", ctext)
              if p.strip(" .")]
    if not pieces:
        return None
    sense_map = {"<=": "<=", ">=": ">=", "=": "==",
                 "<": "<=", ">": ">="}
    for p in pieces:
        m = re.match(r"^(.*?)(<=|>=|=|<|>)\s*"
                     r"(-?\d+(?:\.\d+)?)\s*$", p)
        if not m:
            return None
        try:
            lhs = sp.expand(parse_expression(m.group(1)))
        except Exception:
            return None
        if not lhs.free_symbols or \
                not lhs.free_symbols <= {x, y}:
            return None
        rhs = sp.Rational(m.group(3))
        cons.append((lhs.coeff(x), lhs.coeff(y),
                     rhs - lhs.subs({x: 0, y: 0}),
                     sense_map[m.group(2)]))
    if len(cons) < 2:
        return None
    return _lp_finish(oc_a, oc_b, cons, want_max, want_min,
                      _hindi(q), f"Z = {fmt(oexpr)}")


# --- LPP word templates -------------------------------------------------
# Each template is STRICT: every number it needs must be
# found in its named slot, in order, or the template
# declines. Variables: x = units of the first product,
# y = units of the second.

def _lp_word_result(cons, oc_a, oc_b, want_max, want_min, hi,
                    setup_steps):
    out = _lp_finish(oc_a, oc_b, cons, want_max, want_min, hi,
                     "")
    if out is None:
        return None
    out["steps"] = setup_steps + out["steps"]
    return out


def _lp_cakes(q):
    """NCERT cake form: 'One kind of cake requires A g of
    flour and B g of fat, and another kind requires C g of
    flour and D g of fat. … maximum number of cakes from
    F kg of flour and T kg of fat.'"""
    m1 = re.search(
        r"one kind of cake requires\s+(\d+(?:\.\d+)?)\s*g\s+of\s+"
        r"flour\s+and\s+(\d+(?:\.\d+)?)\s*g\s+of\s+fat", q, re.I)
    m2 = re.search(
        r"another kind of cake requires\s+(\d+(?:\.\d+)?)\s*g\s+"
        r"of\s+flour\s+and\s+(\d+(?:\.\d+)?)\s*g\s+of\s+fat",
        q, re.I)
    mt = re.search(
        r"from\s+(\d+(?:\.\d+)?)\s*(kg|g)\s+of\s+flour\s+and\s+"
        r"(\d+(?:\.\d+)?)\s*(kg|g)\s+of\s+fat", q, re.I)
    if not (m1 and m2 and mt):
        return None
    a1, b1 = sp.Rational(m1.group(1)), sp.Rational(m1.group(2))
    a2, b2 = sp.Rational(m2.group(1)), sp.Rational(m2.group(2))
    tf = sp.Rational(mt.group(1)) * (1000 if mt.group(2) == "kg"
                                     else 1)
    tt = sp.Rational(mt.group(3)) * (1000 if mt.group(4) == "kg"
                                     else 1)
    cons = [(a1, a2, tf, "<="), (b1, b2, tt, "<="),
            (sp.Integer(1), sp.Integer(0), sp.Integer(0), ">="),
            (sp.Integer(0), sp.Integer(1), sp.Integer(0), ">=")]
    steps = [
        "Let x = number of cakes of the first kind and "
        "y = number of cakes of the second kind.",
        f"Flour: {fmt(a1)}x + {fmt(a2)}y <= {fmt(tf)}; "
        f"Fat: {fmt(b1)}x + {fmt(b2)}y <= {fmt(tt)}; "
        "x, y >= 0.",
        "Maximise the total number of cakes, Z = x + y.",
    ]
    return _lp_word_result(cons, sp.Integer(1), sp.Integer(1),
                           True, False, False, steps)


def _lp_toys_en(q):
    """Two products A and B, two machines with per-unit hours
    and availability caps, per-unit profits, maximum profit."""
    ma = re.search(
        r"each\s+(?:toy|unit|item)\s*A\s+requires\s+"
        r"(\d+(?:\.\d+)?)\s+hours?\s+on\s+machine\s+I\s+and\s+"
        r"(\d+(?:\.\d+)?)\s+hours?\s+on\s+machine\s+II", q, re.I)
    mb = re.search(
        r"each\s+(?:toy|unit|item)\s*B\s+requires\s+"
        r"(\d+(?:\.\d+)?)\s+hours?\s+on\s+machine\s+I\s+and\s+"
        r"(\d+(?:\.\d+)?)\s+hours?\s+on\s+machine\s+II", q, re.I)
    mcap = re.search(
        r"machine\s+I\s+is\s+available\s+for\s+at\s+most\s+"
        r"(\d+(?:\.\d+)?)\s+hours?\s+and\s+machine\s+II\s+for\s+"
        r"at\s+most\s+(\d+(?:\.\d+)?)\s+hours?", q, re.I)
    mp = re.search(
        r"profit\s+is\s+Rs\.?\s*(\d+(?:\.\d+)?)\s+per\s+"
        r"(?:toy|unit|item)\s*A\s+and\s+Rs\.?\s*"
        r"(\d+(?:\.\d+)?)\s+per\s+(?:toy|unit|item)\s*B",
        q, re.I)
    if not (ma and mb and mcap and mp):
        return None
    a1, a2 = sp.Rational(ma.group(1)), sp.Rational(ma.group(2))
    b1, b2 = sp.Rational(mb.group(1)), sp.Rational(mb.group(2))
    c1, c2 = sp.Rational(mcap.group(1)), sp.Rational(mcap.group(2))
    p1, p2 = sp.Rational(mp.group(1)), sp.Rational(mp.group(2))
    cons = [(a1, b1, c1, "<="), (a2, b2, c2, "<="),
            (sp.Integer(1), sp.Integer(0), sp.Integer(0), ">="),
            (sp.Integer(0), sp.Integer(1), sp.Integer(0), ">=")]
    steps = [
        "Let x = number of A and y = number of B made.",
        f"Machine I: {fmt(a1)}x + {fmt(b1)}y <= {fmt(c1)}; "
        f"Machine II: {fmt(a2)}x + {fmt(b2)}y <= {fmt(c2)}; "
        "x, y >= 0.",
        f"Maximise the profit Z = {fmt(p1)}x + {fmt(p2)}y "
        "(in rupees).",
    ]
    out = _lp_word_result(cons, p1, p2, True, False, False,
                          steps)
    if out is not None:
        out["answer"] = out["answer"] + " (profit in rupees)"
    return out


def _lp_toys_hi(q):
    """The same toy template in Hinglish dress."""
    ma = re.search(
        r"khilona\s+A\s+banane\s+me\s+(\d+(?:\.\d+)?)\s+ghante\s+"
        r"machine\s+I\s+par\s+aur\s+(\d+(?:\.\d+)?)\s+ghanta\s+"
        r"machine\s+II\s+par", q, re.I)
    mb = re.search(
        r"khilona\s+B\s+banane\s+me\s+(\d+(?:\.\d+)?)\s+ghanta\s+"
        r"machine\s+I\s+par\s+aur\s+(\d+(?:\.\d+)?)\s+ghante\s+"
        r"machine\s+II\s+par", q, re.I)
    mcap = re.search(
        r"machine\s+I\s+adhik\s+se\s+adhik\s+(\d+(?:\.\d+)?)\s+"
        r"ghante\s+aur\s+machine\s+II\s+adhik\s+se\s+adhik\s+"
        r"(\d+(?:\.\d+)?)\s+ghante\s+uplabdh", q, re.I)
    mp = re.search(
        r"prati\s+khilona\s+A\s+par\s+labh\s+(\d+(?:\.\d+)?)\s+"
        r"rupaye\s+aur\s+B\s+par\s+(\d+(?:\.\d+)?)\s+rupaye",
        q, re.I)
    if not (ma and mb and mcap and mp):
        return None
    a1, a2 = sp.Rational(ma.group(1)), sp.Rational(ma.group(2))
    b1, b2 = sp.Rational(mb.group(1)), sp.Rational(mb.group(2))
    c1, c2 = sp.Rational(mcap.group(1)), sp.Rational(mcap.group(2))
    p1, p2 = sp.Rational(mp.group(1)), sp.Rational(mp.group(2))
    cons = [(a1, b1, c1, "<="), (a2, b2, c2, "<="),
            (sp.Integer(1), sp.Integer(0), sp.Integer(0), ">="),
            (sp.Integer(0), sp.Integer(1), sp.Integer(0), ">=")]
    steps = [
        "Let x = number of A and y = number of B made.",
        f"Machine I: {fmt(a1)}x + {fmt(b1)}y <= {fmt(c1)}; "
        f"Machine II: {fmt(a2)}x + {fmt(b2)}y <= {fmt(c2)}; "
        "x, y >= 0.",
        f"Maximise the profit Z = {fmt(p1)}x + {fmt(p2)}y "
        "(in rupees).",
    ]
    out = _lp_word_result(cons, p1, p2, True, False, False,
                          steps)
    if out is not None:
        out["answer"] = out["answer"] + " (profit in rupees)"
    return out


def _lp_diet(q):
    """NCERT diet form: two foods, two nutrients with minimum
    demands, per-unit costs — minimise the cost."""
    mcost = re.findall(
        r"food\s+(\w+)\s+costs?\s+Rs\.?\s*(\d+(?:\.\d+)?)\s+"
        r"per\s+unit", q, re.I)
    mcont = re.findall(
        r"one\s+unit\s+of\s+food\s+(\w+)\s+contains\s+"
        r"(\d+(?:\.\d+)?)\s+units?\s+of\s+([a-z ]+?)\s+and\s+"
        r"(\d+(?:\.\d+)?)\s+units?\s+of\s+([a-z ]+?)"
        r"(?=\s*(?:\.|,|one\s+unit|find|the\s+diet))", q, re.I)
    mdem = re.search(
        r"at\s+least\s+(\d+(?:\.\d+)?)\s+units?\s+of\s+"
        r"([a-z ]+?)\s+and\s+(\d+(?:\.\d+)?)\s+units?\s+of\s+"
        r"([a-z ]+?)(?=\s*(?:\.|,|food))", q, re.I)
    if len(mcost) != 2 or len(mcont) != 2 or not mdem:
        return None
    costs = {name: sp.Rational(v) for name, v in mcost}
    cont = {}
    for name, v1, n1, v2, n2 in mcont:
        cont[name] = {n1.strip().lower(): sp.Rational(v1),
                      n2.strip().lower(): sp.Rational(v2)}
    names = [name for name, _v in mcost]
    if any(n not in cont for n in names):
        return None
    nut1 = mdem.group(2).strip().lower()
    nut2 = mdem.group(4).strip().lower()
    d1, d2 = sp.Rational(mdem.group(1)), sp.Rational(mdem.group(3))
    try:
        a1 = cont[names[0]][nut1]
        a2 = cont[names[1]][nut1]
        b1 = cont[names[0]][nut2]
        b2 = cont[names[1]][nut2]
    except KeyError:
        return None
    cons = [(a1, a2, d1, ">="), (b1, b2, d2, ">="),
            (sp.Integer(1), sp.Integer(0), sp.Integer(0), ">="),
            (sp.Integer(0), sp.Integer(1), sp.Integer(0), ">=")]
    steps = [
        f"Let x = units of food {names[0]} and y = units of "
        f"food {names[1]} in the diet.",
        f"{nut1}: {fmt(a1)}x + {fmt(a2)}y >= {fmt(d1)}; "
        f"{nut2}: {fmt(b1)}x + {fmt(b2)}y >= {fmt(d2)}; "
        "x, y >= 0.",
        f"Minimise the cost Z = {fmt(costs[names[0]])}x + "
        f"{fmt(costs[names[1]])}y (in rupees).",
    ]
    out = _lp_word_result(cons, costs[names[0]],
                          costs[names[1]], False, True, False,
                          steps)
    if out is not None:
        out["answer"] = out["answer"] + " (cost in rupees)"
    return out


# ---------------------------------------------------------------------------
# 2. Probability relations — the P(...) formula family
# ---------------------------------------------------------------------------

_PVAL = re.compile(
    r"P\(\s*([^)]*?)\s*\)\s*=\s*"
    r"(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)")


def _pfrac(text):
    text = text.replace(" ", "")
    if "/" in text:
        a, b = text.split("/", 1)
        return Fraction(a) / Fraction(b)
    return Fraction(text)


def _prob_relations(q):
    ql = q.lower()
    assigns = {}
    for m in _PVAL.finditer(q):
        key = re.sub(r"\s+", "", m.group(1))
        val = _pfrac(m.group(2))
        if q[m.end():m.end() + 1] == "%":
            val = val / 100
        assigns[key] = val
    # factory dress: "E1 and E2 produce 60% and 40%"
    if "E1" not in assigns or "E2" not in assigns:
        mpct = re.search(
            r"(\d+(?:\.\d+)?)\s*%\s+and\s+(\d+(?:\.\d+)?)\s*%",
            q)
        if mpct and "E1" in q and "E2" in q:
            assigns.setdefault(
                "E1", Fraction(mpct.group(1)) / 100)
            assigns.setdefault(
                "E2", Fraction(mpct.group(2)) / 100)
    if len(assigns) < 2:
        return None
    hi = _hindi(q)
    # the asked quantity: the last P(...) NOT given a value
    targets = []
    for m in re.finditer(r"P\(\s*([^)]*?)\s*\)", q):
        if _PVAL.match(q, m.start()):
            continue
        targets.append(re.sub(r"\s+", "", m.group(1)))
    target = targets[-1] if targets else None

    def res(fr, steps):
        return _mk("statistics", "probability", _prob_str(fr),
                   steps)

    check_sig = bool(re.search(
        r"\bcheck\b|\bwhether\b|jaanch|जाँच|hai kya|है क्या|"
        r"independent\?|independent events\?", ql))
    given_ind = (not check_sig) and bool(re.search(
        r"independent events?\s+with|are independent|"
        r"swatantra (hai|hain)|स्वतंत्र (है|हैं)", ql))
    given_mut = bool(re.search(
        r"mutually exclusive|paraspar apvarji|परस्पर अपवर्जी",
        ql))

    pa, pb = assigns.get("A"), assigns.get("B")
    pab = assigns.get("A∩B")
    paub = assigns.get("A∪B")
    pacb = assigns.get("A|B")
    pbca = assigns.get("B|A")

    # independence CHECK
    if check_sig and pa is not None and pb is not None \
            and pab is not None:
        prod = pa * pb
        yes = (prod == pab)
        steps = [
            f"P(A) × P(B) = {_frac(pa)} × {_frac(pb)} = "
            f"{_frac(prod)}.",
            f"P(A ∩ B) is given as {_frac(pab)}.",
            ("Since P(A ∩ B) = P(A) × P(B), A and B ARE "
             "independent events." if yes else
             "Since P(A ∩ B) ≠ P(A) × P(B), A and B are NOT "
             "independent events."),
        ]
        return _mk("statistics", "probability",
                   ("Yes — A and B are independent"
                    if yes else
                    "No — A and B are not independent"),
                   steps)
    # Bayes / total probability over E1, E2
    e1, e2 = assigns.get("E1"), assigns.get("E2")
    ae1, ae2 = assigns.get("A|E1"), assigns.get("A|E2")
    if target is None and e1 is not None and e2 is not None \
            and ae1 is not None and ae2 is not None:
        # "… find the probability of A" — A itself is the
        # only quantity not given a value
        target = "A"
    if e1 is not None and e2 is not None and ae1 is not None \
            and ae2 is not None:
        total = e1 * ae1 + e2 * ae2
        if target == "A":
            return res(total, [
                "By the law of total probability, "
                "P(A) = P(E1)·P(A|E1) + P(E2)·P(A|E2).",
                f"P(A) = {_frac(e1)} × {_frac(ae1)} + "
                f"{_frac(e2)} × {_frac(ae2)} = {_frac(total)}.",
            ])
        for tgt, ei, aei in (("E1|A", e1, ae1),
                             ("E2|A", e2, ae2)):
            if target == tgt:
                post = ei * aei / total
                return res(post, [
                    "By Bayes' theorem, "
                    f"P({tgt[0:2]}|A) = P({tgt[0:2]}) · "
                    f"P(A|{tgt[0:2]}) / P(A).",
                    "First, P(A) = P(E1)·P(A|E1) + "
                    "P(E2)·P(A|E2) (total probability).",
                    f"P(A) = {_frac(e1)} × {_frac(ae1)} + "
                    f"{_frac(e2)} × {_frac(ae2)} = "
                    f"{_frac(total)}.",
                    f"P({tgt[0:2]}|A) = {_frac(ei)} × "
                    f"{_frac(aei)} / {_frac(total)} = "
                    f"{_frac(post)}.",
                ])
    if target == "A|B" or target == "B|A":
        given_ev = "B" if target == "A|B" else "A"
        p_given = pb if target == "A|B" else pa
        if pab is not None and p_given is not None:
            val = pab / p_given
            return res(val, [
                f"By definition, P({target[0]}|{given_ev}) "
                f"= P(A ∩ B) / P({given_ev}).",
                f"P({target[0]}|{given_ev}) = {_frac(pab)} / "
                f"{_frac(p_given)} = {_frac(val)}.",
            ])
        if paub is not None and pa is not None \
                and pb is not None and p_given is not None:
            inter = pa + pb - paub
            val = inter / p_given
            return res(val, [
                "First find P(A ∩ B) from the addition rule: "
                "P(A ∩ B) = P(A) + P(B) − P(A ∪ B).",
                f"P(A ∩ B) = {_frac(pa)} + {_frac(pb)} − "
                f"{_frac(paub)} = {_frac(inter)}.",
                f"Then P({target[0]}|{given_ev}) = "
                f"P(A ∩ B) / P({given_ev}) = {_frac(inter)} "
                f"/ {_frac(p_given)} = {_frac(val)}.",
            ])
        return None
    if target == "A∩B":
        if pacb is not None and pb is not None:
            val = pacb * pb
            return res(val, [
                "From the definition of conditional "
                "probability, P(A ∩ B) = P(A|B) × P(B).",
                f"P(A ∩ B) = {_frac(pacb)} × {_frac(pb)} = "
                f"{_frac(val)}.",
            ])
        if pbca is not None and pa is not None:
            val = pbca * pa
            return res(val, [
                "From the definition of conditional "
                "probability, P(A ∩ B) = P(B|A) × P(A).",
                f"P(A ∩ B) = {_frac(pbca)} × {_frac(pa)} = "
                f"{_frac(val)}.",
            ])
        if given_ind and pa is not None and pb is not None:
            val = pa * pb
            return res(val, [
                "A and B are independent, so "
                "P(A ∩ B) = P(A) × P(B).",
                f"P(A ∩ B) = {_frac(pa)} × {_frac(pb)} = "
                f"{_frac(val)}.",
            ])
        return None
    if target == "A∪B":
        if pa is not None and pb is not None:
            if pab is not None:
                val = pa + pb - pab
                return res(val, [
                    "By the addition rule, "
                    "P(A ∪ B) = P(A) + P(B) − P(A ∩ B).",
                    f"P(A ∪ B) = {_frac(pa)} + {_frac(pb)} − "
                    f"{_frac(pab)} = {_frac(val)}.",
                ])
            if given_ind:
                inter = pa * pb
                val = pa + pb - inter
                return res(val, [
                    "A and B are independent, so "
                    "P(A ∩ B) = P(A) × P(B) "
                    f"= {_frac(inter)}.",
                    "By the addition rule, "
                    "P(A ∪ B) = P(A) + P(B) − P(A ∩ B).",
                    f"P(A ∪ B) = {_frac(pa)} + {_frac(pb)} − "
                    f"{_frac(inter)} = {_frac(val)}.",
                ])
            if given_mut:
                val = pa + pb
                return res(val, [
                    "A and B are mutually exclusive, so "
                    "P(A ∩ B) = 0 and "
                    "P(A ∪ B) = P(A) + P(B).",
                    f"P(A ∪ B) = {_frac(pa)} + {_frac(pb)} = "
                    f"{_frac(val)}.",
                ])
    return None


# ---------------------------------------------------------------------------
# 3. Conditional probability on the sample space + coin & die
# ---------------------------------------------------------------------------

def _prob_conditional(q):
    ql = q.lower()
    hi = _hindi(q)
    # two dice, given the first/second die shows k, sum = s
    mg = re.search(
        r"given that the (first|second) (?:die|dice) "
        r"(?:shows?|is)\s+(\d)", ql)
    ms = re.search(
        r"sum of the numbers is\s+(\d{1,2})|"
        r"sum (?:is|of|to be)\s+(\d{1,2})", ql)
    if mg and ms and ("dice" in ql or "die" in ql
                      or "pasa" in ql or "पासा" in q):
        k = int(mg.group(2))
        s = int(ms.group(1) or ms.group(2))
        other = s - k
        fav = 1 if 1 <= other <= 6 else 0
        fr = Fraction(fav, 6)
        steps = [
            f"Given that the {mg.group(1)} die shows {k}, "
            "only 6 outcomes remain possible (the other die "
            "can show 1 to 6).",
            (f"For the sum to be {s}, the other die must "
             f"show {other} — exactly 1 favourable outcome."
             if fav else
             f"For the sum to be {s}, the other die would "
             f"have to show {other}, which is impossible — "
             "0 favourable outcomes."),
            f"So the probability is {fav}/6 = {_frac(fr)}.",
        ]
        return _mk("statistics", "probability",
                   _prob_str(fr), steps)
    # card, given it is a face card
    if ("card" in ql or "taash" in ql or "ताश" in q) and \
            re.search(r"face card", ql):
        mface = re.search(r"\b(king|queen|jack)\b", ql)
        if mface:
            fr = Fraction(4, 12)
            steps = [
                "There are 12 face cards in a pack (4 kings, "
                "4 queens, 4 jacks).",
                f"Given the card is a face card, the "
                f"favourable outcomes are the 4 "
                f"{mface.group(1)}s.",
                f"So the probability is 4/12 = {_frac(fr)}.",
            ]
            return _mk("statistics", "probability",
                       _prob_str(fr), steps)
    return None


def _coin_die(q):
    ql = q.lower()
    has_pair = (("coin" in ql and "die" in ql) or
                ("sikka" in ql and "pasa" in ql) or
                ("सिक्का" in q and "पासा" in q))
    if not has_pair:
        return None
    hi = _hindi(q)
    if re.search(r"how many (total )?outcomes|total number "
                 r"of outcomes|kitne parinaam|कितने परिणाम",
                 ql):
        steps = ([
            "सिक्के के 2 परिणाम होते हैं (चित या पट) और "
            "पासे के 6 परिणाम होते हैं।",
            "कुल परिणाम = 2 × 6 = 12।",
        ] if hi else [
            "A coin has 2 outcomes (head or tail) and a die "
            "has 6 outcomes.",
            "Total outcomes = 2 × 6 = 12.",
        ])
        return _mk("statistics", "probability", "12", steps,
                   value=12.0)
    side = None
    num = None
    m = re.search(r"(head|tail|chit|pat)\s+and\s+(?:a\s+)?"
                  r"(\d)", ql)
    if m:
        side, num = m.group(1), m.group(2)
    if not side:
        m = re.search(r"(\d)\s+and\s+(?:a\s+)?"
                      r"(head|tail|chit|pat)", ql)
        if m:
            num, side = m.group(1), m.group(2)
    if not side:
        m = re.search(r"(head|tail)\s+aur\s+pase\s+par\s+"
                      r"(\d)", ql)
        if m:
            side, num = m.group(1), m.group(2)
    if not side:
        m = re.search(r"pase\s+par\s+(\d)\s+aur\s+sikke\s+par\s+"
                      r"(head|tail)", ql)
        if m:
            num, side = m.group(1), m.group(2)
    if side and num:
        fr = Fraction(1, 12)
        steps = [
            "Tossing a coin and rolling a die together "
            "gives 2 × 6 = 12 equally likely outcomes.",
            f"Only one of them is ({side}, {num}).",
            f"So the probability is 1/12 = {_frac(fr)}.",
        ]
        return _mk("statistics", "probability",
                   _prob_str(fr), steps)
    return None


# --- probability word templates ------------------------------------------

def _prob_two_bags(q):
    """Total probability, NCERT dress: two bags with red /
    black counts, a bag chosen at random, P(ball is red)."""
    bags = re.findall(
        r"bag contains\s+(\d+)\s+red\s+and\s+(\d+)\s+black\s+"
        r"balls", q, re.I)
    if len(bags) != 2:
        return None
    if not re.search(r"bag is chosen at random", q, re.I):
        return None
    if not re.search(r"probability that the ball is red",
                     q, re.I):
        return None
    (r1, b1), (r2, b2) = [(int(a), int(b)) for a, b in bags]
    p1 = Fraction(r1, r1 + b1)
    p2 = Fraction(r2, r2 + b2)
    total = (p1 + p2) / 2
    steps = [
        "Each bag is equally likely to be chosen, so "
        "P(bag 1) = P(bag 2) = 1/2.",
        f"P(red | bag 1) = {r1}/{r1 + b1} = {_frac(p1)} "
        f"and P(red | bag 2) = {r2}/{r2 + b2} = "
        f"{_frac(p2)}.",
        "By the law of total probability, P(red) = "
        "1/2 × P(red | bag 1) + 1/2 × P(red | bag 2).",
        f"P(red) = 1/2 × {_frac(p1)} + 1/2 × {_frac(p2)} "
        f"= {_frac(total)}.",
    ]
    return _mk("statistics", "probability", _prob_str(total),
               steps)


def _prob_factory_ab(q):
    """Bayes, factory dress: machines A and B produce X% /
    Y% of the items, with D% / E% defective rates; an item
    found defective came from machine A (or B)?"""
    mp = re.search(
        r"machine\s+A\s+produces\s+(\d+(?:\.\d+)?)\s*%\s+of\s+"
        r"the\s+items\s+and\s+machine\s+B\s+produces\s+"
        r"(\d+(?:\.\d+)?)\s*%", q, re.I)
    md = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+of\s+items\s+from\s+machine\s+"
        r"A\s+are\s+defective\s+and\s+(\d+(?:\.\d+)?)\s*%\s+"
        r"from\s+machine\s+B\s+are\s+defective", q, re.I)
    mt = re.search(
        r"produced by machine\s+([AB])", q, re.I)
    if not (mp and md and mt):
        return None
    pa = Fraction(mp.group(1)) / 100
    pb = Fraction(mp.group(2)) / 100
    da = Fraction(md.group(1)) / 100
    db = Fraction(md.group(2)) / 100
    total = pa * da + pb * db
    tgt = mt.group(1).upper()
    post = (pb * db if tgt == "B" else pa * da) / total
    steps = [
        f"P(A) = {_frac(pa)}, P(B) = {_frac(pb)} (share of "
        "production).",
        f"P(defective | A) = {_frac(da)} and "
        f"P(defective | B) = {_frac(db)}.",
        "Total probability of a defective item: "
        f"P(D) = {_frac(pa)} × {_frac(da)} + {_frac(pb)} × "
        f"{_frac(db)} = {_frac(total)}.",
        f"By Bayes' theorem, P({tgt} | D) = "
        f"{_frac(pb if tgt == 'B' else pa)} × "
        f"{_frac(db if tgt == 'B' else da)} / {_frac(total)} "
        f"= {_frac(post)}.",
    ]
    return _mk("statistics", "probability", _prob_str(post),
               steps)


# ---------------------------------------------------------------------------
# 4. Differential equations — homogeneous method + IC particulars
# ---------------------------------------------------------------------------

def _de_extract(q):
    """(rhs_text, (x0, y0) or None) or None. Strips the
    language wrappers (English / Hinglish / Hindi, 'show
    that … homogeneous and solve', trailing commands) and
    reads the initial condition in its school phrasings.
    The LAST 'dy/dx =' wins — a question may mention
    another dy/dx form before the real ask ('… e^(y/x)
    type nahi — solve dy/dx = …')."""
    starts = [m.end() for m in re.finditer(
        r"dy\s*/\s*dx\s*=\s*", q)]
    if not starts:
        return None
    rhs = q[starts[-1]:]
    # a coefficient on dy/dx itself ("x dy/dx = y + x^2")
    # divides through: the equation is dy/dx = rhs / coeff
    mstart = starts[-1]
    mpre = re.search(r"dy\s*/\s*dx\s*=\s*$", q[:mstart])
    if mpre:
        prefix = q[:mstart - len(mpre.group(0))]
        mc = re.search(r"(\d*x(?:\^\d+)?)\s*$", prefix)
        if mc:
            rhs = f"({rhs}) / ({mc.group(1)})"
    ic = None
    mic = re.search(
        r"y\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)\s*=\s*"
        r"(-?\d+(?:\.\d+)?)", rhs)
    if mic:
        ic = (sp.Rational(mic.group(1)),
              sp.Rational(mic.group(2)))
        rhs = rhs[:mic.start()] + " " + rhs[mic.end():]
    else:
        mic = re.search(
            r"y\s*=\s*(-?\d+(?:\.\d+)?)\s+when\s+x\s*=\s*"
            r"(-?\d+(?:\.\d+)?)", rhs)
        if mic:
            ic = (sp.Rational(mic.group(2)),
                  sp.Rational(mic.group(1)))
            rhs = rhs[:mic.start()] + " " + rhs[mic.end():]
    # cut trailing wrapper text at the first sentence word
    # that cannot belong to an expression
    rhs = re.split(
        r"\b(given|find|solve|show|hal|nikalo|batao|ko|is|"
        r"and|homogeneous|the)\b|"
        r"(हल|दीजिए|कीजिए|को)", rhs)[0]
    rhs = rhs.strip(" .,;")
    if not rhs:
        return None
    return rhs, ic


def _verify_implicit(rel, f):
    """rel(x, y) = C defines y(x) implicitly; it solves
    dy/dx = f(x, y) iff −rel_x / rel_y == f identically."""
    x, y = _x, _y
    try:
        fx = sp.diff(rel, x)
        fy = sp.diff(rel, y)
        if fy == 0:
            return False
        return sp.simplify(-fx / fy - f) == 0
    except Exception:
        return False


def _de_solve(q):
    got = _de_extract(q)
    if not got:
        return None
    rhs_text, ic = got
    x, y = _x, _y
    try:
        f = parse_expression(rhs_text)
    except Exception:
        return None
    if f.free_symbols - {x, y}:
        return None
    if y not in f.free_symbols and x not in f.free_symbols:
        return None
    hi = _hindi(q)
    t = sp.symbols("t", positive=True)
    try:
        homog = sp.simplify(
            f.subs({x: t * x, y: t * y}) - f) == 0
    except Exception:
        homog = False
    yf = sp.Function("y")(x)
    # The equation must be built with y(x), not the symbol
    # y: dsolve on a mixed equation (y'(x) = f(x, y-symbol))
    # returns "solutions" still containing the symbol y
    # (Eq(y(x), C1 + y*log(x)) for dy/dx = y/x) and
    # checkodesol rubber-stamps them — the exact implicit
    # garbage the primary DE path serves today.
    eq = sp.Eq(yf.diff(x), f.subs(y, yf))

    def verify(sol_expr, with_ic):
        """A solution is served only if SymPy confirms it."""
        try:
            ok = sp.checkodesol(eq, sp.Eq(yf, sol_expr),
                                order=1, solve_for_func=False)
            if not (isinstance(ok, tuple) and ok[0]):
                return False
        except Exception:
            return False
        if with_ic:
            try:
                return sp.simplify(
                    sol_expr.subs(x, ic[0]) - ic[1]) == 0
            except Exception:
                return False
        return True

    def finish(sol_expr, steps):
        ans = "y = " + fmt(sol_expr)
        return _mk("calculus", "differential_equation", ans,
                   steps, latex=sp.latex(sp.Eq(y, sol_expr)))

    if ic is not None:
        # particular solution: dsolve with the IC, verified
        # against BOTH the equation and the condition
        try:
            sol = sp.dsolve(eq, yf, ics={yf.subs(x, ic[0]):
                                         ic[1]})
            if isinstance(sol, list):
                sol = sol[0] if sol else None
        except Exception:
            sol = None
        if sol is not None and not sol.rhs.has(yf) \
                and verify(sol.rhs, True):
            steps = ([
                f"दिया गया अवकल समीकरण: dy/dx = {fmt(f)}।",
                f"प्रारंभिक शर्त y = {fmt(ic[1])} जब "
                f"x = {fmt(ic[0])} रखकर व्यापक हल से C "
                "ज्ञात करते हैं।",
                f"अतः अभीष्ट विशेष हल: y = {fmt(sol.rhs)}।",
            ] if hi else [
                f"The differential equation is "
                f"dy/dx = {fmt(f)}.",
                f"Solving it and fixing the constant from "
                f"the condition y = {fmt(ic[1])} when "
                f"x = {fmt(ic[0])} gives the particular "
                "solution.",
                f"Particular solution: y = {fmt(sol.rhs)}.",
            ])
            return finish(sol.rhs, steps)
        return None

    if homog:
        # textbook method: y = v x
        v = sp.symbols("v")
        try:
            g = sp.simplify(f.subs(y, v * x))
            if g.free_symbols - {v}:
                return None
        except Exception:
            return None
        head = ([
            "जाँच: f(tx, ty) = f(x, y), अतः समीकरण "
            "समघातीय है।",
            "y = vx रखिए, तो dy/dx = v + x dv/dx।",
            f"रखने पर: v + x dv/dx = {fmt(g)} अर्थात् "
            f"x dv/dx = {fmt(g)} - v।",
        ] if hi else [
            "Check: f(tx, ty) = f(x, y), so the equation "
            "is homogeneous.",
            "Put y = vx, so dy/dx = v + x dv/dx.",
            f"Substituting: v + x dv/dx = {fmt(g)}, so "
            f"x dv/dx = {fmt(g)} - v.",
        ])
        # explicit solution first (dsolve, verified)
        sol_expr = None
        try:
            gen = sp.dsolve(eq, yf)
            if isinstance(gen, list):
                gen = gen[0]
            if not gen.rhs.has(yf) and verify(gen.rhs, False):
                sol_expr = gen.rhs
        except Exception:
            sol_expr = None
        if sol_expr is not None:
            try:
                sep = sp.integrate(1 / (g - v), v)
                mid = ([
                    "चरों को अलग करके समाकलन करने पर: "
                    f"∫ dv/({fmt(g)} - v) = ∫ dx/x + C, "
                    f"अर्थात् {fmt(sep)} = log|x| + C।",
                ] if hi else [
                    "Separating the variables and "
                    "integrating: "
                    f"∫ dv/({fmt(g)} - v) = ∫ dx/x + C, "
                    f"giving {fmt(sep)} = log|x| + C.",
                ])
            except Exception:
                mid = (["चरों को अलग करके समाकलन करने पर "
                        "व्यापक हल मिलता है।"] if hi else
                       ["Separating the variables and "
                        "integrating gives the general "
                        "solution."])
            tail = ([
                "v = y/x वापस रखने पर व्यापक हल मिलता है: "
                f"y = {fmt(sol_expr)}।",
            ] if hi else [
                "Putting v = y/x back, the general "
                f"solution is: y = {fmt(sol_expr)}.",
            ])
            return finish(sol_expr, head + mid + tail)
        # implicit solution from the separation itself,
        # verified by implicit differentiation
        if sp.simplify(g - v) == 0:
            return None
        try:
            sep = sp.integrate(1 / (g - v), v)
            rel = sp.simplify(sep.subs(v, y / x) - sp.log(x))
        except Exception:
            return None
        if not _verify_implicit(rel, f):
            return None
        ans = fmt(rel) + " = C"
        steps = head + ([
            "चरों को अलग करके समाकलन करने पर: "
            f"{fmt(sep)} = log|x| + C।",
            "v = y/x वापस रखने पर व्यापक हल (अस्पष्ट रूप "
            f"में) मिलता है: {ans}।",
        ] if hi else [
            "Separating the variables and integrating: "
            f"{fmt(sep)} = log|x| + C.",
            "Putting v = y/x back, the general solution "
            f"(in implicit form) is: {ans}.",
        ])
        return _mk("calculus", "differential_equation", ans,
                   steps)

    # non-homogeneous but dsolve-able: serve only verified
    # EXPLICIT solutions (an implicit rhs with y(x) inside
    # is not an answer a student can use)
    try:
        gen = sp.dsolve(eq, yf)
        if isinstance(gen, list):
            gen = gen[0]
        sol_expr = gen.rhs
    except Exception:
        return None
    if sol_expr.has(yf) or not verify(sol_expr, False):
        return None
    steps = ([
        f"अवकल समीकरण dy/dx = {fmt(f)} को हल करने पर "
        "व्यापक हल मिलता है:",
        f"y = {fmt(sol_expr)} (C स्वेच्छ अचर है)।",
    ] if hi else [
        f"Solving the differential equation "
        f"dy/dx = {fmt(f)} gives the general solution:",
        f"y = {fmt(sol_expr)} (C is an arbitrary constant).",
    ])
    return finish(sol_expr, steps)


# ---------------------------------------------------------------------------
# 5. Area between curves
# ---------------------------------------------------------------------------

_AREA_WORDS = re.compile(
    r"area|kshetrafal|क्षेत्रफल|bounded|enclosed", re.I)


def _area_result(val, steps, hi):
    ans = fmt(val)
    try:
        if not float(val).is_integer() and \
                abs(float(val) - round(float(val))) > 1e-9:
            ans = f"{fmt(val)} ≈ {float(val):.4f}"
    except Exception:
        pass
    ans = ans + " square units"
    steps = steps + [("अतः अभीष्ट क्षेत्रफल "
                      f"= {ans}।" if hi else
                      f"So the required area = {ans}.")]
    return _mk("calculus", "area_between_curves", ans, steps,
               value=float(val))


def _area_integrate(fexpr, gexpr, lo, hi_, hi, names):
    """∫|f − g| between consecutive intersections lo..hi_
    (sign fixed by a midpoint sample)."""
    diff = sp.expand(fexpr - gexpr)
    mid = (lo + hi_) / 2
    sgn = 1
    try:
        if float(diff.subs(_x, mid)) < 0:
            sgn = -1
    except Exception:
        pass
    val = sp.integrate(sgn * diff, (_x, lo, hi_))
    val = sp.simplify(val)
    if val.is_negative or (val.is_real and float(val) < 0):
        val = -val
    steps = ([
        f"दोनों वक्रों के प्रतिच्छेद बिंदु: "
        f"x = {fmt(lo)} और x = {fmt(hi_)}।",
        f"क्षेत्रफल = ∫[{fmt(lo)} से {fmt(hi_)}] "
        f"|{names[0]} − ({names[1]})| dx = {fmt(val)}।",
    ] if hi else [
        f"The curves meet where x = {fmt(lo)} and "
        f"x = {fmt(hi_)}.",
        f"Area = ∫ from {fmt(lo)} to {fmt(hi_)} of "
        f"|{names[0]} − ({names[1]})| dx = {fmt(val)}.",
    ])
    return _area_result(val, steps, hi)


def _area_between(q):
    if not _AREA_WORDS.search(q):
        return None
    hi = _hindi(q)
    x, y = _x, _y
    ql = q.lower()

    # ellipse x^2/a^2 + y^2/b^2 = 1
    me = re.search(r"x\^2\s*/\s*(\d+(?:\.\d+)?)\s*\+\s*"
                   r"y\^2\s*/\s*(\d+(?:\.\d+)?)\s*=\s*1", q)
    if me and ("ellipse" in ql or "दीर्घवृत्त" in q):
        a = sp.sqrt(sp.Rational(me.group(1)))
        b = sp.sqrt(sp.Rational(me.group(2)))
        val = sp.pi * a * b
        steps = ([
            f"दीर्घवृत्त x²/{me.group(1)} + y²/{me.group(2)} "
            f"= 1 के लिए a = {fmt(a)}, b = {fmt(b)}।",
            f"क्षेत्रफल = πab = {fmt(val)}।",
        ] if hi else [
            f"For the ellipse x²/{me.group(1)} + "
            f"y²/{me.group(2)} = 1, a = {fmt(a)} and "
            f"b = {fmt(b)}.",
            f"Area = πab = {fmt(val)}.",
        ])
        return _area_result(val, steps, hi)

    # circle x^2 + y^2 = r^2 with the vertical line x = a
    mc = re.search(r"x\^2\s*\+\s*y\^2\s*=\s*(\d+(?:\.\d+)?)",
                   q)
    ml = re.search(r"(?:line\s+)?x\s*=\s*(-?\d+(?:\.\d+)?)\b",
                   q)
    if mc and ml:
        r2 = sp.Rational(mc.group(1))
        a = sp.Rational(ml.group(1))
        r = sp.sqrt(r2)
        if a > 0 and a < r:
            # smaller segment: 2 ∫[a..r] sqrt(r² − x²) dx
            val = sp.simplify(2 * sp.integrate(
                sp.sqrt(r2 - x**2), (x, a, r)))
            steps = ([
                f"वृत्त x² + y² = {fmt(r2)} और रेखा "
                f"x = {fmt(a)} के बीच का छोटा भाग:",
                "क्षेत्रफल = 2 ∫["
                f"{fmt(a)} से {fmt(r)}] √({fmt(r2)} − x²) "
                f"dx = {fmt(val)}।",
            ] if hi else [
                f"The smaller region between the circle "
                f"x² + y² = {fmt(r2)} and the line "
                f"x = {fmt(a)}:",
                f"Area = 2 ∫ from {fmt(a)} to {fmt(r)} of "
                f"√({fmt(r2)} − x²) dx = {fmt(val)}.",
            ])
            return _area_result(val, steps, hi)

    # explicit limits: "between x = A and x = B" / "from A to B"
    mlim = re.search(
        r"(?:between\s+)?x\s*=\s*(-?[\w./^() -]+?)\s+and\s+"
        r"x\s*=\s*(-?[\w./^() -]+?)(?=\s*(?:by|is|,|\.|$))",
        q)
    if mlim is None:
        mlim = re.search(
            r"from\s+x\s*=\s*(-?[\w./^() -]+?)\s+to\s+"
            r"x\s*=\s*(-?[\w./^() -]+?)(?=\s*(?:by|is|,|\.|$))",
            q)
    lims = None
    if mlim:
        try:
            lims = (parse_expression(mlim.group(1)
                                     .replace("pi", "π")),
                    parse_expression(mlim.group(2)
                                     .replace("pi", "π")))
        except Exception:
            lims = None

    # gather curve expressions: y = f(x) pieces and the
    # parabola y^2 = kx (handled as y = ±sqrt(kx), x >= 0)
    yeqs = []
    for m in re.finditer(
            r"y\s*=\s*([^,;]+?)(?=\s+and\s+y\s*=|"
            r"\s+and\s+the|\s+aur\s+(?:rekha\s+|vakr\s+)?y\s*=|"
            r"\s+और\s+(?:रेखा\s+)?y\s*=|,|;|$)", q):
        yeqs.append(m.group(1).strip())
    mpar = re.search(r"y\^2\s*=\s*(\d+(?:\.\d+)?)\s*x\b", q)
    mparx = re.search(r"x\^2\s*=\s*(\d+(?:\.\d+)?)\s*y\b", q)

    exprs = []
    for t in yeqs:
        t = re.split(r"\bbetween\b|\bfrom\b|\bke\s+beech\b|"
                     r"\bke\s+madhya\b|\bkshetrafal\b|"
                     r"के\s+बीच|क्षेत्रफल", t)[0].strip()
        if not t:
            continue
        try:
            e = parse_expression(t)
        except Exception:
            return None
        if e.free_symbols - {x}:
            return None
        exprs.append((e, "y = " + fmt(e)))

    if mpar and mparx:
        # two parabolas y^2 = k1 x and x^2 = k2 y
        k1 = sp.Rational(mpar.group(1))
        k2 = sp.Rational(mparx.group(1))
        ftop = sp.sqrt(k1 * x)
        gbot = x**2 / k2
        sols = sp.solve(sp.Eq(ftop, gbot), x)
        reals = sorted({s for s in sols
                        if s.is_real and s >= 0})
        if len(reals) < 2:
            return None
        return _area_integrate(ftop, gbot, reals[0],
                               reals[-1], hi,
                               (fmt(ftop), fmt(gbot)))
    if mpar and not mparx and len(exprs) == 1:
        # parabola y^2 = kx against a line/curve y = g(x):
        # the enclosed region is bounded above by the
        # parabola's upper branch y = sqrt(kx) — fold it
        # into the two-curve machinery below.
        k = sp.Rational(mpar.group(1))
        exprs.append((sp.sqrt(k * x),
                      "y = √(" + fmt(k) + "x)"))
    if len(exprs) == 2:
        (f1, n1), (f2, n2) = exprs
        if lims is not None:
            return _area_integrate(f1, f2, lims[0], lims[1],
                                   hi, (n1, n2))
        try:
            sols = sp.solve(sp.Eq(f1, f2), x)
        except Exception:
            return None
        reals = sorted({s for s in sols
                        if s.is_real})
        if len(reals) < 2:
            return None
        return _area_integrate(f1, f2, reals[0], reals[-1],
                               hi, (n1, n2))
    if len(exprs) == 1 and lims is not None:
        f1, n1 = exprs[0]
        return _area_integrate(f1, sp.Integer(0), lims[0],
                               lims[1], hi, (n1, "y = 0"))
    return None





# ---------------------------------------------------------------------------
# 6. Wave 103 leftovers — ratio angles, function evaluation
# ---------------------------------------------------------------------------

def _ratio_angles(q):
    """Angles of a quadrilateral (sum 360°) or triangle
    (sum 180°) given in a ratio a:b:c[:d]."""
    ql = q.lower()
    is_quad = ("quadrilateral" in ql or "chaturbhuj" in ql
               or "चतुर्भुज" in q)
    is_tri = ("triangle" in ql or "tribhuj" in ql
              or "त्रिभुज" in q)
    if not (is_quad or is_tri):
        return None
    m = re.search(r"(\d+)\s*:\s*(\d+)\s*:\s*(\d+)"
                  r"(?:\s*:\s*(\d+))?", q)
    if not m:
        return None
    parts = [int(g) for g in m.groups() if g is not None]
    total_deg = 360 if is_quad else 180
    if is_quad and len(parts) != 4:
        return None
    if is_tri and len(parts) != 3:
        return None
    hi = _hindi(q)
    s = sum(parts)
    unit = sp.Rational(total_deg, s)
    angles = [p * unit for p in parts]
    want_small = bool(re.search(
        r"smallest|chhota|छोटा|sabse chhota", ql))
    want_large = bool(re.search(
        r"largest|biggest|bada|बड़ा|sabse bada", ql))
    shape = "quadrilateral" if is_quad else "triangle"
    steps = ([
        f"अनुपात के भागों का योग = {s} है और {shape} के "
        f"कोणों का योग {total_deg}° होता है।",
        f"अतः 1 भाग = {total_deg}°/{s} = {fmt(unit)}°।",
        "कोण हैं: " + ", ".join(
            f"{p} × {fmt(unit)}° = {fmt(a)}°"
            for p, a in zip(parts, angles)) + "।",
    ] if hi else [
        f"The ratio parts add to {s}, and the angles of a "
        f"{shape} add to {total_deg}°.",
        f"So 1 part = {total_deg}°/{s} = {fmt(unit)}°.",
        "The angles are: " + ", ".join(
            f"{p} × {fmt(unit)}° = {fmt(a)}°"
            for p, a in zip(parts, angles)) + ".",
    ])
    if want_small:
        ans = fmt(min(angles)) + "°"
        steps.append(("सबसे छोटा कोण = " if hi else
                      "The smallest angle is ") + ans + "।"
                     if hi else "The smallest angle is " + ans
                     + ".")
    elif want_large:
        ans = fmt(max(angles)) + "°"
        steps.append(("सबसे बड़ा कोण = " if hi else
                      "The largest angle is ") + ans + "।"
                     if hi else "The largest angle is " + ans
                     + ".")
    else:
        ans = ", ".join(fmt(a) + "°" for a in angles)
    return _mk("geometry", "ratio_angles", ans, steps)


def _func_eval(q):
    """f(x) = <expr> … find f/g/h(…) — any function letter,
    including the Hinglish 'g(x) = … hai to g(n) ka maan'
    dress. (gaps103 owns most f-forms; this gate runs after
    it, so only its leftovers arrive here.)"""
    # an explicit ask must be present — the bare stripped
    # core the Wave 77 pass re-solves ("If f(x) = 3x + 1,
    # f(4)") carries no ask word, and that form is
    # gaps103's to answer in its own format at the outer
    # gate; claiming it here would change a pinned answer
    if not re.search(r"find|value of|maan|nikalo|batao|"
                     r"hai to|ज्ञात|मान", q, re.I):
        return None
    hi = _hindi(q)
    mdef = None
    for m in re.finditer(
            r"\b([a-zA-Z])\s*\(\s*x\s*\)\s*=\s*"
            r"([0-9xX+\-*/^(). ]+?)(?=\s+hai\b|\s+then\b|"
            r"\s+find\b|\s+to\b|,|;|$)", q):
        mdef = m
    if not mdef:
        return None
    letter = mdef.group(1)
    expr_text = mdef.group(2).strip()
    try:
        expr = parse_expression(expr_text)
    except Exception:
        return None
    if expr.free_symbols - {_x}:
        return None
    asks = [m for m in re.finditer(
        r"\b" + letter + r"\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
        q) if m.start() != mdef.start()]
    if not asks:
        # "… ka maan nikalo" without a repeated call: look
        # for the value in words after the definition
        return None
    val_at = sp.Rational(asks[-1].group(1))
    got = expr.subs(_x, val_at)
    steps = ([
        f"{letter}(x) = {fmt(expr)} दिया है।",
        f"x = {fmt(val_at)} रखने पर: {letter}({fmt(val_at)}) "
        f"= {fmt(got)}।",
    ] if hi else [
        f"Given {letter}(x) = {fmt(expr)}.",
        f"Put x = {fmt(val_at)}: {letter}({fmt(val_at)}) "
        f"= {fmt(got)}.",
    ])
    return _mk("algebra", "function_value", fmt(got), steps,
               value=float(got))


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def solve_depth125(question):
    """Failure-gate entry (router): strict schemas, each
    returns None unless it settles the question fully."""
    q = _prep(question)
    for fn in (_lp_symbolic, _lp_cakes, _lp_toys_en,
               _lp_toys_hi, _lp_diet, _prob_relations,
               _prob_two_bags, _prob_factory_ab,
               _prob_conditional, _coin_die, _de_solve,
               _area_between, _ratio_angles, _func_eval):
        try:
            out = fn(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None


def depth125_upgrade(question, result):
    """Hijack repair (fallback.py): the primary chain
    produced a real-looking answer to a DIFFERENT question.
    Fire only when a strict schema settles this question
    AND the served answer is not already the schema's
    value — a correct primary answer is never displaced."""
    if not isinstance(result, dict):
        return None
    op = result.get("op")
    ans = str(result.get("answer") or "")
    q = _prep(question)
    try:
        if op == "hindi_equation":
            cand = _lp_symbolic(q)
            if cand is not None:
                val = cand.get("value")
                if val is None or not _ans_has(ans, val):
                    return cand
        if op == "probability":
            cand = (_prob_two_bags(q) or _prob_factory_ab(q)
                    or _prob_conditional(q) or _coin_die(q))
            if cand is not None and \
                    not _same_prob(ans, cand["answer"]):
                return cand
        if op == "differential_equation":
            # the primary DE path sometimes serves an
            # implicit dsolve form (y still inside the
            # answer) or a general solution for a
            # particular-solution ask — replace it with
            # the verified Wave 125 solution
            got = _de_extract(q)
            if got is not None:
                cand = _de_solve(q)
                if cand is not None and \
                        cand["answer"] != ans:
                    if got[1] is not None:
                        return cand
                    if _implicit_shaped(ans):
                        return cand
        if op == "equation":
            got = _de_extract(q)
            if got is not None:
                cand = _de_solve(q)
                if cand is not None:
                    return cand
            if _AREA_WORDS.search(q):
                cand = _area_between(q)
                if cand is not None:
                    return cand
    except Exception:
        return None
    return None


def _implicit_shaped(ans):
    """True when a 'y = …' answer still contains y on the
    right-hand side (an implicit dsolve form, not a usable
    explicit solution)."""
    if "y(x)" in ans:
        return True
    m = re.match(r"\s*y\s*=\s*(.*)$", ans)
    rhs = m.group(1) if m else ans
    return bool(re.search(r"(?<![A-Za-z])y(?![A-Za-z])",
                          rhs))


def _ans_has(ans, val):
    try:
        target = float(val)
    except Exception:
        return False
    for tok in re.findall(r"-?\d+(?:\.\d+)?", ans):
        try:
            if abs(float(tok) - target) < 0.011:
                return True
        except Exception:
            pass
    return False


def _same_prob(ans, cand_ans):
    def nums(s):
        out = []
        for tok in re.findall(r"\d+(?:\.\d+)?(?:/\d+)?", s):
            try:
                out.append(float(Fraction(tok)))
            except Exception:
                pass
        return out
    a, c = nums(ans), nums(cand_ans)
    return any(abs(x - y) < 0.011 for x in a for y in c)
