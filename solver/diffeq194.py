"""Wave 194: differential equations in NCERT dress + the
verify-the-solution wrong-serve fix (form-audit top-10
item #9; audit rows 15-17, probes 14 and 15).

Why this module exists (form audit, 19 Nov 2026):

* Probe 14 — "Find the general solution of the
  differential equation (x^2 + xy) dy = (x^2 + y^2) dx"
  came back a parse ERROR.  depth125's homogeneous family
  owns the dy/dx dress (incl. Hindi/Hinglish), but the
  English NCERT bracketed dress "(...) dy = (...) dx"
  (Ex 9.3/9.4) reached no schema at all.
* Probe 15 (WRONG SERVE, the priority) — "Verify that
  y = e^x + 1 is a solution of the differential equation
  y'' - y' = 0" was "solved" for the letter e and served
  the nonsense "e = (y - 1)^(1/x)".  No verification
  schema existed, so every verify-form was a hijack risk.
* The dy/dx dress of the same families served
  letter-soup: "Find the general solution of dy/dx +
  y = e^x" (Ex 9.5 linear) and "... dy/dx = e^(x+y)"
  (Ex 9.3 separable) both left the router as
  op "implicit_derivative" with the question's words
  letter-split into a product of symbols.

What is built here — strict, family-level schemas; each
fires only when it settles the question COMPLETELY and
every served result is verified before serving:

(a) First-order general solutions, from either dress
    ("(A) dy = (B) dx" / "(B) dx = (A) dy", or a dy/dx
    equation), by deterministic textbook methods only:
      - homogeneous: y = vx, separate, integrate; the
        implicit result is verified by implicit
        differentiation against the student's own f.
      - separable: the f_x*f_y == f*f_xy test, factor
        extraction, integrate both sides; verified the
        same implicit way (explicit serve when h == 1).
      - linear in y: integrating factor mu = e^(int P),
        y*mu = int Q*mu dx + C; the explicit result is
        verified by differentiating it back.
    NO dsolve anywhere: measured on probe 14, SymPy's
    dsolve dies with RecursionError on this family, and
    the Wave 186 warning stands — an unbounded heuristic
    search has no place on arbitrary student input.
    Anything these methods cannot solve AND verify
    returns None (the fallback chain handles it); a
    wrong or fragment DE answer is never served.

(b) Verify-the-solution (Ex 9.2): "Verify / show that
    y = <explicit function of x> is a solution of <DE in
    y, y', y''>".  The candidate is differentiated,
    substituted into the DE, and the residual simplified:
    residual == 0 serves a VERIFIED verdict with the
    differentiation steps; a provably nonzero residual
    (symbolic + numeric spot-check) serves the computed
    NOT-a-solution verdict with both sides shown.  The
    schema can never solve the DE for a variable — the
    probe-15 nonsense class is structurally impossible
    in this dress.  An undecidable residual returns
    None, never an assertion.

(c) Order & degree: rechecked — calculus.py's Wave 100
    schema already serves the NCERT dresses (pinned as
    controls in test/test_wave194.py); nothing built.

Wiring (router.py, after the Wave 175 block): a
failure-only gate like Waves 125/142/169/175 for all
three families, PLUS a Wave 171-style displacement block
for the verify dress alone — probe 15's primary result
is a "real" op (equation), so the failure gate can never
see it; displacement happens only when the strict verify
schema settles the question with a computed verdict the
primary did not serve.  depth125's dresses keep their
behaviour: its gate sits earlier, and this module's
dy/dx extractor declines initial-condition asks and
second-order dresses outright.
"""

import re

import sympy as sp

from .expression_parser import fmt, parse_expression

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")
_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")

_x = sp.symbols("x")
_y = sp.symbols("y")
_C1 = sp.symbols("C1")
_E_SYM = sp.symbols("e")

_MAX_OPS = 80


def _prep(q):
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("′", "'").replace("″", "''")
    s = s.replace("≤", "<=").replace("≥", ">=")
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


def _parse(text):
    """Parse an expression in x / y, folding the letter e
    to Euler's number (the shared parser keeps it a plain
    symbol, whose powers differentiate into log(e) soup).
    None on any failure or any symbol beyond x and y."""
    try:
        expr = parse_expression(text)
    except Exception:
        return None
    if isinstance(expr, tuple) or expr is None:
        return None
    try:
        if _E_SYM in expr.free_symbols:
            expr = expr.subs(_E_SYM, sp.E)
    except Exception:
        return None
    if expr.free_symbols - {_x, _y}:
        return None
    return expr


def _verify_implicit(rel, f):
    """rel(x, y) = C solves dy/dx = f iff -rel_x/rel_y == f
    identically (the depth125 check, reused verbatim in
    spirit: a solution is served only when this holds)."""
    try:
        fy = sp.diff(rel, _y)
        if fy == 0:
            return False
        return sp.simplify(
            -sp.diff(rel, _x) / fy - f) == 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# The deterministic first-order solver core
# ---------------------------------------------------------------------------

def _serve_implicit(rel, f, head_steps, mid_steps, hi):
    if not _verify_implicit(rel, f):
        return None
    ans = fmt(rel) + " = C"
    steps = head_steps + list(mid_steps or []) + [
        (f"अतः व्यापक हल (अस्पष्ट रूप में): {ans}।"
         if hi else
         f"So the general solution (in implicit form) "
         f"is: {ans}."),
    ]
    return _mk("calculus", "differential_equation", ans,
               steps)


def _solve_first_order(f, hi, head_steps):
    """General solution of dy/dx = f(x, y) by textbook
    methods, each verified before serving; None when no
    method both solves and verifies."""
    if f is None or sp.count_ops(f) > _MAX_OPS:
        return None
    x, y = _x, _y

    # --- homogeneous: y = vx -------------------------------------------
    try:
        t = sp.symbols("t", positive=True)
        homog = sp.simplify(
            f.subs({x: t * x, y: t * y}) - f) == 0
    except Exception:
        homog = False
    if homog and y in f.free_symbols:
        v = sp.symbols("v")
        try:
            g = sp.simplify(f.subs(y, v * x))
        except Exception:
            g = None
        if g is not None and not (g.free_symbols - {v}):
            head = head_steps + ([
                "जाँच: f(tx, ty) = f(x, y), अतः समीकरण "
                "समघातीय है।",
                "y = vx रखिए, तो dy/dx = v + x dv/dx।",
                f"रखने पर: v + x dv/dx = {fmt(g)} अर्थात् "
                f"x dv/dx = {fmt(g)} - v।",
            ] if hi else [
                "Check: f(tx, ty) = f(x, y), so the "
                "equation is homogeneous.",
                "Put y = vx, so dy/dx = v + x dv/dx.",
                f"Substituting: v + x dv/dx = {fmt(g)}, "
                f"so x dv/dx = {fmt(g)} - v.",
            ])
            if sp.simplify(g - v) != 0:
                try:
                    sep = sp.integrate(1 / (g - v), v)
                except Exception:
                    sep = None
                if sep is not None and not sep.has(
                        sp.Integral):
                    rel = sp.simplify(
                        sep.subs(v, y / x) - sp.log(x))
                    if fmt(rel).startswith("-") and \
                            _verify_implicit(-rel, f):
                        rel = -rel
                    tail = ([
                        "चरों को अलग करके समाकलन करने पर: "
                        f"{fmt(sep)} = log|x| + C।",
                        "v = y/x वापस रखिए।",
                    ] if hi else [
                        "Separating the variables and "
                        "integrating: "
                        f"{fmt(sep)} = log|x| + C.",
                        "Put v = y/x back.",
                    ])
                    out = _serve_implicit(rel, f, head,
                                          tail, hi)
                    if out is not None:
                        return out
            # g - v == 0 means f == y/x in disguise: that
            # family is separable, handled below.

    # --- separable: f = g(x) * h(y) ------------------------------------
    try:
        if x not in f.free_symbols:
            g, h = sp.Integer(1), f
        elif y not in f.free_symbols:
            g, h = f, sp.Integer(1)
        else:
            fx = sp.diff(f, x)
            fy = sp.diff(f, y)
            fxy = sp.diff(fx, y)
            if sp.simplify(fx * fy - f * fxy) != 0:
                g = h = None
            else:
                g = h = None
                for y0 in (0, 1, 2, -1, sp.Rational(1, 2)):
                    try:
                        cand_g = f.subs(y, y0)
                        if cand_g == 0 or cand_g.has(
                                sp.zoo, sp.nan):
                            continue
                        cand_h = sp.simplify(f / cand_g)
                    except Exception:
                        continue
                    if cand_h.free_symbols - {y}:
                        continue
                    if cand_g.free_symbols - {x}:
                        continue
                    if sp.simplify(cand_g * cand_h
                                   - f) == 0:
                        g, h = cand_g, cand_h
                        break
    except Exception:
        g = h = None
    if g is not None and h is not None:
        try:
            iy = sp.integrate(1 / h, y)
            ix = sp.integrate(g, x)
        except Exception:
            iy = ix = None
        if iy is not None and not iy.has(sp.Integral) \
                and not ix.has(sp.Integral):
            head = head_steps + ([
                "चरों को अलग कीजिए: "
                f"dy/({fmt(h)}) = ({fmt(g)}) dx।",
                "दोनों पक्षों का समाकलन करने पर: "
                f"{fmt(iy)} = {fmt(ix)} + C।",
            ] if hi else [
                "Separate the variables: "
                f"dy/({fmt(h)}) = ({fmt(g)}) dx.",
                "Integrating both sides: "
                f"{fmt(iy)} = {fmt(ix)} + C.",
            ])
            if h == 1:
                # explicit: y = ix + C, still verified
                sol = ix + _C1
                try:
                    ok = sp.simplify(
                        sp.diff(sol, x)
                        - f.subs(y, sol)) == 0
                except Exception:
                    ok = False
                if ok:
                    ans = "y = " + fmt(sol)
                    return _mk(
                        "calculus",
                        "differential_equation", ans,
                        head + [(
                            f"अतः व्यापक हल: {ans}।"
                            if hi else
                            f"So the general solution "
                            f"is: {ans}.")],
                        latex=sp.latex(sp.Eq(y, sol)))
            else:
                rel = iy - ix
                if fmt(rel).startswith("-") and \
                        _verify_implicit(-rel, f):
                    rel = -rel
                out = _serve_implicit(rel, f, head, None,
                                      hi)
                if out is not None:
                    return out

    # --- linear in y: dy/dx + P(x) y = Q(x) ----------------------------
    try:
        poly = sp.Poly(f, y)
    except Exception:
        poly = None
    if poly is not None and poly.degree() == 1:
        a = poly.nth(1)          # f = a(x)*y + b(x)
        b = poly.nth(0)
        if not (a.free_symbols - {x}) and \
                not (b.free_symbols - {x}):
            P = -a
            Q = b
            try:
                int_p = sp.integrate(P, x)
                if int_p.has(sp.Integral):
                    raise ValueError("IF integral failed")
                mu = sp.exp(int_p)
                int_qmu = sp.integrate(Q * mu, x)
                if int_qmu.has(sp.Integral):
                    raise ValueError("Q*mu integral failed")
                sol = (int_qmu + _C1) / mu
                ok = sp.simplify(
                    sp.diff(sol, x)
                    - f.subs(y, sol)) == 0
            except Exception:
                ok = False
                sol = None
            if ok and sol is not None:
                ans = "y = " + fmt(sol)
                head = head_steps + ([
                    "यह y में रैखिक समीकरण है: "
                    f"dy/dx + ({fmt(P)}) y = {fmt(Q)}।",
                    f"समाकलन गुणक IF = e^(∫P dx) = "
                    f"{fmt(mu)}।",
                    "IF से गुणा करके समाकलन करने पर: "
                    f"y × {fmt(mu)} = {fmt(int_qmu)} + C।",
                ] if hi else [
                    "This is linear in y: "
                    f"dy/dx + ({fmt(P)}) y = {fmt(Q)}.",
                    "Integrating factor IF = e^(∫P dx) "
                    f"= {fmt(mu)}.",
                    "Multiplying by the IF and "
                    "integrating: "
                    f"y × {fmt(mu)} = {fmt(int_qmu)} + C.",
                ])
                return _mk(
                    "calculus", "differential_equation",
                    ans,
                    head + [(f"अतः व्यापक हल: {ans}।"
                             if hi else
                             f"So the general solution "
                             f"is: {ans}.")],
                    latex=sp.latex(sp.Eq(y, sol)))
    return None


# ---------------------------------------------------------------------------
# (a1) The bracketed dress: (A) dy = (B) dx
# ---------------------------------------------------------------------------

_BRACKET_RE = re.compile(
    r"^(?P<a>.*?)\s*(?P<d1>dy|dx)\s*=\s*"
    r"(?P<b>.*?)\s*(?P<d2>dy|dx)\s*[.?।]*$")


def _bracket_solve(q):
    low = q.lower()
    if "differential equation" not in low and \
            "general solution" not in low and \
            not low.lstrip().startswith("solve"):
        return None
    s = q
    mde = re.search(r"differential\s+equation", s, re.I)
    if mde:
        s = s[mde.end():]
    s = s.strip(" :,-")
    s = re.sub(r"^(of|the)\s+", "", s, flags=re.I)
    m = _BRACKET_RE.match(s.strip())
    if not m or m.group("d1") == m.group("d2"):
        return None
    sides = {m.group("d1"): m.group("a"),
             m.group("d2"): m.group("b")}

    def coeff(text):
        t = text.strip()
        if not t:
            return sp.Integer(1)
        if t.startswith("(") and t.endswith(")"):
            t = t[1:-1].strip()
        return _parse(t)

    a_dy = coeff(sides["dy"])
    b_dx = coeff(sides["dx"])
    if a_dy is None or b_dx is None or a_dy == 0:
        return None
    f = sp.simplify(b_dx / a_dy)
    hi = _hindi(q)
    head = ([
        f"दिया गया समीकरण: ({fmt(a_dy)}) dy = "
        f"({fmt(b_dx)}) dx, अर्थात् dy/dx = {fmt(f)}।",
    ] if hi else [
        f"The equation is ({fmt(a_dy)}) dy = "
        f"({fmt(b_dx)}) dx, so dy/dx = {fmt(f)}.",
    ])
    return _solve_first_order(f, hi, head)


# ---------------------------------------------------------------------------
# (a2) The dy/dx dress (separable / linear forms depth125 declines)
# ---------------------------------------------------------------------------

_IC_RE = re.compile(
    r"y\s*\(\s*-?[\d.]+\s*\)\s*=|"
    r"\by\s*=\s*-?[\d.]+\s+when\s+x\s*=", re.I)


def _dydx_solve(q):
    low = q.lower()
    if "differential equation" not in low and \
            "general solution" not in low and \
            not re.match(r"\s*solve\b", low):
        return None
    if re.search(r"find\s+(the\s+)?dy/dx\s+if", low):
        return None            # implicit differentiation
    if "d^2y/dx^2" in low.replace(" ", "") or "y''" in q:
        return None            # second order: not ours
    if _IC_RE.search(q):
        return None            # particular-solution ask
    s = q
    mde = re.search(r"differential\s+equation", s, re.I)
    if mde:
        s = s[mde.end():]
    else:
        s = re.sub(r"^\s*solve\s+(the\s+)?", "", s,
                   flags=re.I)
        s = re.sub(r"^\s*find\s+the\s+general\s+solution"
                   r"\s+of\s+(the\s+)?", "", s, flags=re.I)
    s = s.strip(" :,-")
    s = re.sub(r"^(of|the)\s+", "", s, flags=re.I)
    s = re.sub(r"dy\s*/\s*dx", "dy/dx", s)
    if s.count("dy/dx") != 1 or s.count("=") != 1:
        return None
    w = sp.symbols("w")
    left, right = s.split("=", 1)
    lexpr = _parse_side(left, w)
    rexpr = _parse_side(right, w)
    if lexpr is None or rexpr is None:
        return None
    expr = lexpr - rexpr
    try:
        poly = sp.Poly(expr, w)
    except Exception:
        return None
    if poly is None or poly.degree() != 1:
        return None
    A = poly.nth(1)
    B = poly.nth(0)
    if A == 0 or A.free_symbols - {_x, _y} or \
            B.free_symbols - {_x, _y}:
        return None
    f = sp.simplify(-B / A)
    hi = _hindi(q)
    head = ([
        f"दिया गया अवकल समीकरण: dy/dx = {fmt(f)}।",
    ] if hi else [
        f"The differential equation is dy/dx = "
        f"{fmt(f)}.",
    ])
    return _solve_first_order(f, hi, head)


def _parse_side(text, w):
    """Parse one side of a dy/dx equation, with the
    dy/dx token already normalised: swap it for the
    placeholder symbol before parsing."""
    t = text.replace("dy/dx", " w ")
    try:
        expr = parse_expression(t)
    except Exception:
        return None
    if isinstance(expr, tuple) or expr is None:
        return None
    if _E_SYM in expr.free_symbols:
        expr = expr.subs(_E_SYM, sp.E)
    if expr.free_symbols - {_x, _y, w}:
        return None
    return expr


# ---------------------------------------------------------------------------
# (b) Verify that y = ... is a solution of ...
# ---------------------------------------------------------------------------

_VERIFY_VERB = re.compile(
    r"\b(verify|show|prove|check)\b", re.I)
_DERIV_TOKEN = re.compile(
    r"y''|y'|dy\s*/\s*dx|d\^?2y/dx\^?2", re.I)


def _tokenise_de(text):
    """(expr in x, y, w=y', v=y'', rhs_text) or None.
    Derivative tokens are hidden behind placeholders
    before parsing (the calculus.py Wave-80 trick), so
    'dy/dx' is never letter-split into d*y/d*x."""
    whole = text.replace("d^2y/dx^2", "\x01")
    whole = whole.replace("d2y/dx2", "\x01")
    whole = re.sub(r"dy\s*/\s*dx", "\x02", whole)
    whole = whole.replace("y''", "\x01").replace(
        "y'", "\x02")
    if "\x01" not in whole and "\x02" not in whole:
        return None
    tokens = re.findall(
        r"\x01|\x02|[A-Za-z]+|\d+(?:\.\d+)?|\S", whole)

    def rebuild(toks):
        out = []
        for tk in toks:
            if tk == "\x01":
                out.append(" v ")
            elif tk == "\x02":
                out.append(" w ")
            elif tk.isalpha() and len(tk) > 1 and \
                    tk.lower() not in (
                        "sin", "cos", "tan", "exp", "log",
                        "sqrt", "cot", "sec", "csc", "asin",
                        "acos", "atan", "sinh", "cosh",
                        "tanh", "abs"):
                out.append("*".join(tk))
            else:
                out.append(tk)
        return " ".join(out)

    joined = rebuild(tokens)
    if joined.count("=") != 1:
        return None
    l2, r2 = joined.split("=", 1)
    v, w = sp.symbols("v w")
    try:
        lexpr = parse_expression(l2)
        rexpr = parse_expression(r2)
    except Exception:
        return None
    for e in (lexpr, rexpr):
        if isinstance(e, tuple) or e is None:
            return None
    expr = lexpr - rexpr
    if _E_SYM in expr.free_symbols:
        expr = expr.subs(_E_SYM, sp.E)
    extra = expr.free_symbols - {_x, _y, v, w}
    if any(len(str(s)) != 1 for s in extra):
        return None
    if v not in expr.free_symbols and \
            w not in expr.free_symbols:
        return None
    return expr, v, w


def verify_solution_result(q):
    """The strict verify-the-solution schema (Ex 9.2).
    Returns a computed verdict dict, or None when the
    dress is not exactly this ask or the verdict cannot
    be computed with certainty."""
    if not isinstance(q, str):
        return None
    s = _prep(q)
    low = s.lower()
    if not _VERIFY_VERB.search(low):
        return None
    if "solution" not in low and "satisf" not in low:
        return None
    # Split candidate / DE at the strongest marker.
    mde = re.search(r"differential\s+equation", s, re.I)
    if mde:
        cand_text = s[:mde.start()]
        de_text = s[mde.end():]
    else:
        mso = re.search(
            r"is\s+a\s+solution\s+of|satisfies", s, re.I)
        if not mso:
            return None
        cand_text = s[:mso.start()]
        de_text = s[mso.end():]
    de_text = de_text.strip(" :,-")
    de_text = re.sub(r"^(of|the)\s+", "", de_text,
                     flags=re.I).strip(" :,-")
    if not _DERIV_TOKEN.search(de_text):
        return None
    # The candidate: the last 'y = ...' before the split.
    mc = None
    for mc in re.finditer(r"\by\s*=\s*", cand_text):
        pass
    if mc is None:
        return None
    cand_raw = cand_text[mc.end():].strip(" .,;")
    for _ in range(4):
        nxt = re.sub(
            r"\s+(is\s+a\s+solution\s+of|satisfies|of|"
            r"the|a)$", "", cand_raw, flags=re.I)
        if nxt == cand_raw:
            break
        cand_raw = nxt.strip(" .,;")
    if not cand_raw or "=" in cand_raw:
        return None
    try:
        cand = parse_expression(cand_raw)
    except Exception:
        return None
    if isinstance(cand, tuple) or cand is None:
        return None
    if _E_SYM in cand.free_symbols:
        cand = cand.subs(_E_SYM, sp.E)
    if _y in cand.free_symbols:
        return None
    params = cand.free_symbols - {_x}
    if any(len(str(p)) != 1 for p in params):
        return None
    got = _tokenise_de(de_text)
    if got is None:
        return None
    expr, v, w = got
    order = 2 if v in expr.free_symbols else 1
    d1 = sp.diff(cand, _x)
    subs = {w: d1, _y: cand}
    d2 = None
    if order == 2:
        d2 = sp.diff(cand, _x, 2)
        subs[v] = d2
    try:
        residual = expr.subs(subs)
        residual = sp.simplify(
            sp.trigsimp(sp.expand(residual)))
    except Exception:
        return None
    hi = _hindi(q)
    de_disp = de_text.strip(" .")
    if residual == 0:
        steps = [
            f"Given function: y = {fmt(cand)}.",
            f"Differentiating with respect to x: "
            f"y' = {fmt(d1)}.",
        ]
        if order == 2:
            steps.append(
                f"Differentiating again: "
                f"y'' = {fmt(d2)}.")
        steps += [
            f"Substituting these values in {de_disp}: "
            f"the left and right sides come out equal.",
            f"Hence y = {fmt(cand)} is a solution of "
            f"the differential equation.",
        ]
        if hi:
            steps = [
                f"दिया गया फलन: y = {fmt(cand)}।",
                f"x के सापेक्ष अवकलन करने पर: "
                f"y' = {fmt(d1)}।",
            ]
            if order == 2:
                steps.append(
                    f"पुनः अवकलन करने पर: "
                    f"y'' = {fmt(d2)}।")
            steps += [
                f"इन मानों को {de_disp} में रखने पर "
                f"दोनों पक्ष बराबर आते हैं।",
                f"अतः y = {fmt(cand)} दिए गए अवकल "
                f"समीकरण का हल है। (सत्यापित)",
            ]
        ans = (f"Yes — y = {fmt(cand)} is a solution "
               f"of {de_disp} (verified by substitution)")
        return _mk("calculus", "de_verification", ans,
                   steps)
    # Nonzero verdict: demand numeric confirmation too,
    # so an unsimplified identity can never be declared
    # false.
    try:
        pt = {_x: sp.Rational(7, 10)}
        for p in params:
            pt[p] = 1
        for p in expr.free_symbols - {_x, _y, v, w}:
            pt[p] = 1
        val = complex(residual.subs(pt).evalf())
        if abs(val) < 1e-6:
            return None
    except Exception:
        return None
    steps = [
        f"Given function: y = {fmt(cand)}.",
        f"Differentiating with respect to x: "
        f"y' = {fmt(d1)}.",
    ]
    if order == 2:
        steps.append(
            f"Differentiating again: y'' = {fmt(d2)}.")
    steps += [
        f"Substituting in {de_disp}: the two sides "
        f"differ — (left side) - (right side) "
        f"= {fmt(residual)}, which is not zero.",
        f"Hence y = {fmt(cand)} is NOT a solution of "
        f"the differential equation.",
    ]
    if hi:
        steps = [
            f"दिया गया फलन: y = {fmt(cand)}।",
            f"x के सापेक्ष अवकलन करने पर: "
            f"y' = {fmt(d1)}।",
        ]
        if order == 2:
            steps.append(
                f"पुनः अवकलन करने पर: y'' = {fmt(d2)}।")
        steps += [
            f"{de_disp} में रखने पर दोनों पक्षों का "
            f"अंतर = {fmt(residual)} आता है, जो शून्य "
            f"नहीं है।",
            f"अतः y = {fmt(cand)} दिए गए अवकल समीकरण "
            f"का हल नहीं है।",
        ]
    ans = (f"No — y = {fmt(cand)} is not a solution "
           f"of {de_disp}: on substituting, the two "
           f"sides differ by {fmt(residual)}")
    return _mk("calculus", "de_verification", ans, steps)


# ---------------------------------------------------------------------------
# Entry points (router)
# ---------------------------------------------------------------------------

def solve_diffeq194(question):
    """Failure-gate entry: strict schemas, each returns
    None unless it settles the question completely with
    a verified result."""
    q = _prep(question)
    for fn in (verify_solution_result, _bracket_solve,
               _dydx_solve):
        try:
            out = fn(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
