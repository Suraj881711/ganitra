"""Wave 186: implicit + logarithmic differentiation in the
"Find dy/dx if ..." dress (form-audit top-10 item #1;
NCERT Class 12 Ex 5.3 / 5.5 / 5.7).

Why this module exists (form audit, 19 Nov 2026; probes 09
and 10 in ganitra-formaudit-notes.md):

    "Find dy/dx if 2x + 3y = sin x"   -> dy/dx = (cos x - 2)/3
    "Find dy/dx if x^y + y^x = 1"     -> logarithmic form

Both burned the full 10 s solve budget and fell to the
fallback guide.  Measured root cause (this wave): the
maths was never missing — solver/c12gaps142.py has implicit
/ log schemas that settle both probes in 0.06 s / 0.58 s —
but they sit behind a FAILURE-ONLY gate at the very end of
router._solve_question_uncached, and the primary path never
gets there in time: route_intent sends the relation to
calculus, whose solve_calculus reads it as a differential
equation and calls SymPy dsolve; dsolve's odesimp /
_handle_Integral stage (heurisch + manual integration)
burns ~10.2 s of the ~10.8 s uncached solve, so the
Wave 46 wall-clock budget (SOLVE_BUDGET_SECONDS = 10)
discards the correct late-gate answer and serves the
too-big error dict instead.

Fix: an EARLY gate in router._solve_question_uncached
(after normalisation, before the intent machinery — the
Wave 140 / Wave 32 early-gate precedent), strictly gated
on the dy/dx dress, backed by this module.  This module
returns None unless the text is a dy/dx ask whose body is

  (a) a pure implicit relation in x and y (constants
      a / b / c / k allowed) — settled by differentiating
      both sides w.r.t. x with y a function of x (SymPy
      idiff), or
  (b) an explicit y = f(x) / bare f(x) containing a
      variable power (x in both base and exponent of some
      Pow: x^x, x^sin x, (sin x)^x, (log x)^log x, and
      products / quotients / sums of such) — settled by
      logarithmic differentiation, the derivative built
      factor-wise as y * (sum of log-derivatives).

Every served derivative is verified at solve time before
serving: implicit candidates by the symbolic total-
derivative identity (or the on-curve numeric check) from
c12gaps142, explicit candidates against central finite
differences of the parsed function.  Anything doubtful
returns None so routing continues unchanged — a wrong
serve is worse than a native miss.

Two NCERT forms c12gaps142's own schemas decline are
covered here at family level: "ax + by^2 = cos y" (its
token purity check rejects the glued tokens ax / by; this
module's purity check is letter-level) and "sin^2 y +
cos xy = k" (its parser dies on sin^2 — FunctionClass **
Integer; this module folds fn^n <arg> to (fn(<arg>))^n
before parsing).

Out of scope, declined by construction (routing unchanged):
parametric asks (x = ..., y = ... — probe 11, solves today
via the primary path), second derivatives, dy/dx at a
point, plain explicit differentiation (no variable power
— "differentiate x^3 + sin x" keeps its primary answer),
inverse-trig dresses, integration, prove/show asks.
"""
import re

import sympy as sp

from .c12gaps142 import (_dparse, _prep, _result,
                         _verify_implicit,
                         _verify_implicit_numeric)
from .expression_parser import fmt

x, y = sp.symbols("x y")

_MAX_BODY = 160

# Symbols a relation may contain besides x and y: the
# NCERT parameter letters, read as constants.
_ALLOWED_EXTRA = {"a", "b", "c", "k"}

_FUNCS = {"sin", "cos", "tan", "sec", "cosec", "cot",
          "log", "sqrt", "exp", "abs"}

# Letters that may appear in a pure-maths body token
# (single letters and glued products like ax, by, xy).
_PURE_LETTERS = set("xyabcek")


def _pure186(text):
    """Letter-level purity: every letter token is a known
    function name or a product of single symbol letters.
    Prose tokens ('the', 'area', 'find') contain letters
    outside the symbol set and fail."""
    for tok in re.findall(r"[a-z]+", str(text)):
        if tok in _FUNCS:
            continue
        if all(ch in _PURE_LETTERS for ch in tok):
            continue
        return False
    return True


def _fold_fn_powers(s):
    """fn^n <arg> -> (fn(<arg>))^n, the spelling the plain
    parser cannot read (sin^2 y dies as FunctionClass **
    Integer).  Also the glued book spellings sin2 y and
    (log x)log x / xsin x from the extraction."""
    s = re.sub(r"\b(sin|cos|tan|sec|cosec|cot)\s*\^\s*(\d+)"
               r"\s*\(([^()]*)\)", r"(\1(\3))^\2", s)
    s = re.sub(r"\b(sin|cos|tan|sec|cosec|cot)\s*\^\s*(\d+)"
               r"\s*(xy|yx|\d*[a-z])\b", r"(\1(\3))^\2", s)
    s = re.sub(r"\b(sin|cos|tan|sec|cosec|cot)\s*\^\s*(\d+)"
               r"(xy|yx|[a-z])\b", r"(\1(\3))^\2", s)
    s = re.sub(r"\b(sin|cos|tan|sec|cosec|cot)([23])"
               r"\s+([a-z])\b", r"(\1(\3))^\2", s)
    s = re.sub(r"\((log x)\)(cos x|sin x|log x|x)\b",
               r"(log x)^(\2)", s)
    s = re.sub(r"\bxsin\s*x\b", "x^(sin x)", s)
    return s


# Dress boilerplate stripped to reach the maths body.
# Longest phrases first; every pattern is word-bounded so
# no maths token can be eaten.
_STRIP_PHRASES = [
    r"with\s+respect\s+to\s+x\b",
    r"w\.?\s*r\.?\s*t\.?\s*x\b",
    r"ke\s+liye\b",
    r"dy\s*/\s*dx",
    r"differentiate\b",
    r"derivative\b",
    r"following\b",
    r"nikalo\b", r"nikaalo\b", r"nikal\b",
    r"batao\b", r"bataao\b",
    r"karo\b", r"kar\s+do\b",
    r"agar\b", r"find\b", r"the\b", r"of\b",
    r"if\b", r"ka\b", r"ki\b",
    r"please\b", r"plz\b",
]


def _extract_body(question):
    """The pure maths body of a dy/dx-dress question, or
    None when the text is not this family's dress."""
    s = _prep(question)
    s = s.lower()
    s = re.sub(r"dy\s*/\s*dx", "dy/dx", s)
    low = s
    # Declines: shapes owned by other families / waves,
    # whose behaviour must not change.
    if "prove" in low or "show that" in low:
        return None
    if "second" in low or "d2y" in low or "d^2y" in low:
        return None
    if "integrat" in low or "∫" in low:
        return None
    if "parametr" in low:
        return None
    if re.search(r"\bat\s+(x|t|theta)\s*=", low) \
            or re.search(r"\bat\s*\(", low) \
            or "at a point" in low:
        return None
    if "dy/dt" in low or "dx/dy" in low:
        return None
    if re.search(r"w\.?\s*r\.?\s*t\.?\s*(t|y)\b", low) \
            or "with respect to t" in low \
            or "with respect to y" in low:
        return None
    # Inverse-trig differentiation is a different, already
    # covered family; a misread sin^-1 would verify against
    # its own parse, so stay out entirely.
    if re.search(r"\ba(sin|cos|tan|cot|sec|csc)\b", low) \
            or re.search(r"\barc(sin|cos|tan)\b", low) \
            or re.search(r"(sin|cos|tan|sec|cosec|cot)"
                         r"\s*\^\s*-\s*1", low):
        return None
    # Wave 210: a dy/dx that sits INSIDE an equation — an
    # operator or "=" adjacent to it on either side
    # ("dy/dx + y = e^x", "x dy/dx + 2y = x^2",
    # "... = dy/dx") — is a differential equation to
    # SOLVE, not a "find dy/dx" ask.  The strip below
    # eats the dy/dx token as dress, so the bare DE
    # "dy/dx + y = e^x" was misread as the implicit
    # relation y = e^x and served dy/dx = exp(x) — the
    # derivative of a different question.  In this
    # family's genuine dresses ("find dy/dx if ...",
    # "dy/dx of ...") the token is a noun phrase, never
    # an operand.  Decline; the DE layers own it.
    if re.search(r"[-+*/=^]\s*dy\s*/\s*dx", low) \
            or re.search(r"dy\s*/\s*dx\s*[-+*/=^)]", low):
        return None
    # Dress: a literal dy/dx, or differentiate ... w.r.t. x.
    has_dydx = "dy/dx" in low
    has_diff_wrt = ("differentiate" in low
                    or "derivative" in low) and bool(
        re.search(r"w\.?\s*r\.?\s*t\.?\s*x\b"
                  r"|with\s+respect\s+to\s+x\b", low))
    if not (has_dydx or has_diff_wrt):
        return None
    body = s
    for pat in _STRIP_PHRASES:
        body = re.sub(pat, " ", body)
    # Trailing domain conditions (", 0 < x < 1", ", x > 1").
    body = re.sub(r",?\s*-?\d*\s*<\s*x\s*<\s*-?\d+.*$", "",
                  body)
    body = re.sub(r",?\s*x\s*>\s*-?\d+.*$", "", body)
    body = re.sub(r",?\s*x\s*!=\s*0.*$", "", body)
    body = _fold_fn_powers(body)
    body = re.sub(r"\s+", " ", body).strip(" .:,;?")
    if not body or len(body) > _MAX_BODY:
        return None
    return body


def _has_var_pow(expr):
    """A Pow with x in BOTH base and exponent (x^x,
    (sin x)^x, x^sin x, (log x)^log x ...)."""
    return any(
        isinstance(n, sp.Pow)
        and x in n.base.free_symbols
        and x in n.exp.free_symbols
        for n in sp.preorder_traversal(expr))


def _has_y_var_pow(F):
    """A Pow mixing x and y across base / exponent
    (x^y, y^x) — the log-implicit relations."""
    for n in sp.preorder_traversal(F):
        if isinstance(n, sp.Pow):
            base_s = n.base.free_symbols
            exp_s = n.exp.free_symbols
            if (x in base_s and y in exp_s) \
                    or (y in base_s and x in exp_s):
                return True
    return False


def _verify_explicit(expr, d1):
    """Central finite differences of the parsed function
    against the candidate derivative; one clean sample
    point is enough, no clean point means decline."""
    for x0 in (1.3, 2.2, 0.7, 1.8, 2.9):
        try:
            h = 1e-4
            fp = float(expr.subs(x, x0 + h))
            fm = float(expr.subs(x, x0 - h))
            got = float(d1.subs(x, x0))
        except Exception:
            continue
        if any(v != v or abs(v) == float("inf")
               for v in (fp, fm, got)):
            continue
        num = (fp - fm) / (2 * h)
        if abs(num - got) <= 1e-3 * max(1.0, abs(num)):
            return True
    return False


def _explicit186(body):
    """Explicit variable-power forms: y = f(x) (body is the
    f(x) side) or a bare f(x).  Plain explicit forms (no
    variable power) decline — the primary path owns them."""
    if not _pure186(body):
        return None
    try:
        expr = _dparse(body)
    except Exception:
        return None
    if expr is None or isinstance(expr, tuple):
        return None
    if expr.free_symbols != {x}:
        return None
    if expr.has(sp.Derivative) or expr.has(sp.Abs):
        return None
    if not _has_var_pow(expr):
        return None
    note = ("Take log on both sides and differentiate "
            "(logarithmic differentiation).")
    # Sums differentiate termwise; the raw derivative is
    # already the clean textbook form.
    if expr.is_Add:
        d1 = sp.diff(expr, x)
        if not _verify_explicit(expr, d1):
            return None
        steps = [note, f"dy/dx = {fmt(d1)}"]
        return _result("dydx", fmt(d1), steps,
                       typ="calculus")
    # Products / quotients / single powers: build the
    # derivative factor-wise as y * (log-derivative sum) —
    # the NCERT presentation, short by construction.
    factors = list(expr.args) if expr.is_Mul else [expr]
    ratio = sp.Integer(0)
    ok = True
    for f in factors:
        try:
            if isinstance(f, sp.Pow):
                term = (sp.diff(f.exp, x) * sp.log(f.base)
                        + f.exp * sp.diff(f.base, x) / f.base)
            else:
                term = sp.diff(f, x) / f
            ratio += sp.simplify(term)
        except Exception:
            ok = False
            break
    if ok:
        try:
            ratio = sp.simplify(ratio)
        except Exception:
            pass
        d1 = expr * ratio
        if len(str(ratio)) <= 70 \
                and _verify_explicit(expr, d1):
            ans = f"({fmt(expr)}) * ({fmt(ratio)})"
            steps = [note,
                     f"dy/dx = y * (log-derivative) = {ans}"]
            return _result("log_differentiation", ans,
                           steps, typ="calculus")
    # Fallback presentation: the plain derivative, still
    # numerically verified before serving.
    d1 = sp.diff(expr, x)
    if not _verify_explicit(expr, d1):
        return None
    steps = [note, f"dy/dx = {fmt(d1)}"]
    return _result("dydx", fmt(d1), steps, typ="calculus")


def _implicit186(lhs, rhs):
    if not (_pure186(lhs) and _pure186(rhs)):
        return None
    try:
        F = _dparse(lhs) - _dparse(rhs)
    except Exception:
        return None
    if F is None or isinstance(F, tuple) or F == 0:
        return None
    syms = F.free_symbols
    if x not in syms or y not in syms:
        return None
    extra = {str(s) for s in syms} - {"x", "y"}
    if not extra <= _ALLOWED_EXTRA:
        return None
    if F.has(sp.Derivative) or F.has(sp.Abs):
        return None
    try:
        cand = sp.idiff(F, y, x)
    except Exception:
        return None
    if cand is None or cand.has(sp.Derivative):
        return None
    try:
        cand = sp.simplify(cand)
    except Exception:
        pass
    if cand.has(sp.Derivative) or cand.has(sp.zoo) \
            or cand.has(sp.nan):
        return None
    if not _verify_implicit(F, cand) \
            and not _verify_implicit_numeric(F, cand):
        return None
    steps = []
    log_imp = _has_y_var_pow(F)
    if log_imp:
        steps.append("Take log on both sides and "
                     "differentiate (logarithmic "
                     "differentiation).")
    steps.append("Differentiate both sides w.r.t. x, "
                 "treating y as a function of x.")
    steps.append(f"dy/dx = {fmt(cand)}")
    op = "log_implicit_dydx" if log_imp else "implicit_dydx"
    return _result(op, fmt(cand), steps, typ="calculus")


def solve_dydx186(question):
    """Wave 186 schema: implicit + logarithmic
    differentiation in the "Find dy/dx if ..." dress.
    None unless the dress matches and a strict family
    schema settles the question with a verified answer."""
    try:
        body = _extract_body(question)
    except Exception:
        return None
    if body is None:
        return None
    try:
        # Parametric dress (x = ..., y = ...): two
        # assignments — the primary path owns it.
        if re.search(r"\bx\s*=", body) \
                and re.search(r"\by\s*=", body):
            return None
        if body.count("=") == 1:
            lhs, rhs = (part.strip()
                        for part in body.split("="))
            if not lhs or not rhs:
                return None
            if lhs == "y":
                return _explicit186(rhs)
            if re.match(r"[a-z]\s*\(", lhs):
                # f(x) = ... and friends: not this family.
                return None
            return _implicit186(lhs, rhs)
        if "=" not in body:
            return _explicit186(body)
    except Exception:
        return None
    return None
