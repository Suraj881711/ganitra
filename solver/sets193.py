"""Wave 193: Sets & Cartesian-product forms (NCERT Class 11
Ex 1.1-1.5, 2.1-2.3) + the De Morgan WRONG-SERVE fix.

Why this module exists (form audit 19 Nov 2026, item B.8 /
probes 23-24):

  * Probe 23 (WRONG SERVE): "If U = {1, ..., 9}, A = {2, 4,
    6, 8} and B = {2, 3, 5, 7}, verify that (A union B)' =
    A' intersection B'" was served **{2, 4, 6, 8}** by
    solver/sets_basics.py — it parsed the first two brace
    groups as its A and B (U and A), intersected them, and
    served the fragment A.  The correct verification
    computes BOTH sides: A union B = {2,3,4,5,6,7,8}, so
    (A union B)' = {1, 9}, and A' intersection B' = {1, 9}
    — verified equal.  This module's verify schema parses
    the NAMED sets, evaluates both sides of the identity
    with a real set-expression evaluator, and serves the
    comparison verdict with both sides shown.  A false
    identity serves the computed "not equal" verdict, never
    an assertion.
  * Probe 24 (MISS): "If (x + 1, y - 2) = (3, 1), find the
    values of x and y" parse-errored.  Ordered-pair
    equality (including the (x + y, x - y) = (5, 1) system
    variant) is schema (b) below.

Family scope — every schema fires only when it settles the
question COMPLETELY from explicitly given data, and the
whole question is accounted for (the Wave 192 lesson: a
schema must require the actual ask dress — a question that
merely MENTIONS a set, or asks why / what-is / define,
never fires):

  (a) Set-identity VERIFY with explicit U, A, B (and C):
      De Morgan both laws, distributive laws, (A')' = A —
      both sides computed from the parsed sets.  Plus
      direct complement computations ("find (A union B)'")
      — a complement must be present, so plain union /
      intersection asks stay with sets_basics untouched.
  (b) Ordered-pair equality: (expr, expr) = (a, b) with
      linear expressions in x, y; SymPy-solved and verified
      by substitution into every component.
  (c) Cartesian products: list A x B (and A x B x C) for
      small explicit sets, |A x B| counts, A x (B ∩ C) /
      A x (B ∪ C) with explicit sets, P x P x P counts and
      lists, and the "A x B has n elements, A has k
      elements, find n(B)" variant (exact division only).
  (d) Domain & range (and codomain, only in the explicit
      "relation from A to B" dress) of a relation given as
      a roster of ordered pairs.
  (e) Roster <-> set-builder conversion for DECIDABLE
      conditions only: natural / whole / integer bounds,
      even / odd / prime / multiple filters, squares and
      cubes, interval [a, b) <-> {x : a <= x < b}, the
      vowels set, letters of a word.  Anything not
      mechanically decidable declines.
  (f) Subset / membership batteries (∈ ∉ ⊂ ⊆ ⊄ verdicts
      on explicit sets) ONLY when the WHOLE battery parses
      into decidable statements — a partial battery would
      be a fragment serve, so one bad statement declines
      the whole question.

Wiring (router.py): a failure-only gate after the Wave 175
block (primary error / unknown / soft), PLUS a scoped
wrong-serve displacement: when the primary result is a
sets-typed serve and this module settles the same question
completely with a verifiably DIFFERENT answer, the
module's computed answer stands (Wave 171/187 precedent —
that is the seam the probe-23 fragment serve travels).
Concept asks ("what is a set", "define subset") decline
here, as do why-questions.
"""
import itertools
import math
import re
from fractions import Fraction

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

# ---------------------------------------------------------------------------
# Small shared helpers
# ---------------------------------------------------------------------------

_FILLER = {
    "if", "given", "that", "the", "a", "an", "find", "compute",
    "calculate", "evaluate", "determine", "what", "is", "are",
    "of", "for", "in", "on", "and", "or", "to", "with", "has",
    "have", "how", "many", "much", "number", "elements",
    "element", "list", "write", "all", "ordered", "pairs",
    "pair", "cartesian", "product", "n", "set", "sets",
    "each", "there", "do", "does", "it", "its", "from", "by",
    "as", "let", "be", "suppose", "when", "then", "so", "get",
    "give", "me", "following", "state", "whether", "true",
    "false", "statements", "statement", "domain", "range",
    "codomain", "co", "relation", "function", "roster",
    "form", "tabular", "builder", "express", "convert",
    "into", "interval", "notation", "show", "verify",
    "prove", "values", "value", "using", "above", "below",
    "where",
}


def _prep(text):
    s = str(text)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("′", "'").replace("’", "'")
    return s


def _only_filler(text, extra=frozenset()):
    """True when `text` is nothing but filler words and
    punctuation — the accounting check that keeps a schema
    from answering one part of a longer question."""
    words = re.findall(r"[A-Za-z][A-Za-z-]*", text)
    allowed = _FILLER | set(extra)
    return all(w.lower() in allowed for w in words) and \
        not re.search(r"\d", text)


def _sort_key(v):
    if isinstance(v, (int, float, Fraction)):
        return (0, float(v))
    return (1, str(v))


def _fmt_val(v):
    if isinstance(v, Fraction):
        if v.denominator == 1:
            return str(v.numerator)
        return f"{v.numerator}/{v.denominator}"
    if isinstance(v, float):
        return str(int(v)) if v == int(v) else f"{v:g}"
    return str(v)


def _show(vals):
    """Display a value list as a roster {a, b, c}, sorted
    the house way (numbers in order, then letters)."""
    return "{" + ", ".join(
        _fmt_val(v) for v in sorted(vals, key=_sort_key)) + "}"


def _parse_value(tok):
    """One roster element: int / fraction / decimal / single
    letter or short word.  None when not a plain value."""
    t = tok.strip()
    if not t:
        return None
    if re.fullmatch(r"[+-]?\d+", t):
        return int(t)
    m = re.fullmatch(r"([+-]?\d+)\s*/\s*(\d+)", t)
    if m:
        den = int(m.group(2))
        if den == 0:
            return None
        return Fraction(int(m.group(1)), den)
    if re.fullmatch(r"[+-]?\d+\.\d+", t):
        return float(t)
    if re.fullmatch(r"[A-Za-z]", t):
        return t
    return None


def _parse_roster(content):
    """'{...}' inner text -> ordered de-duplicated value
    list, or None when any element is not a plain value."""
    content = content.strip()
    if not content:
        return []
    vals = []
    for tok in content.split(","):
        v = _parse_value(tok)
        if v is None:
            return None
        if v not in vals:
            vals.append(v)
    return vals


_NAMED_RE = re.compile(r"(?<![A-Za-z])([A-Z])\s*=\s*\{([^{}]*)\}")


def _extract_named(q):
    """Named explicit sets: {'A': [values...]} plus the text
    with every assignment span blanked out.  An assignment
    whose roster does not parse as plain values (a relation
    roster, a set-builder) is left out of the dict but still
    blanked when it is a plain roster."""
    named = {}
    spans = []
    for m in _NAMED_RE.finditer(q):
        vals = _parse_roster(m.group(2))
        if vals is not None:
            named[m.group(1)] = vals
            spans.append(m.span())
    rest = list(q)
    for a, b in spans:
        for i in range(a, b):
            rest[i] = " "
    return named, "".join(rest)


# ---------------------------------------------------------------------------
# Set-expression evaluator: names, union / intersection /
# difference, postfix complement, parentheses.  Values are
# ordered lists (roster order preserved) so Cartesian
# listings come out in the order a student expects.
# ---------------------------------------------------------------------------

def _tokenize_expr(s):
    toks = []
    i = 0
    s = s.strip()
    while i < len(s):
        c = s[i]
        if c.isspace() or c == ",":
            i += 1
        elif c in "()'∪∩":
            toks.append(c)
            i += 1
        elif c == "-":
            toks.append("DIFF")
            i += 1
        elif c.isupper() and c.isalpha():
            toks.append(("NAME", c))
            i += 1
        elif s[i:i + 5].lower() == "union" and \
                (i + 5 >= len(s) or not s[i + 5].isalpha()):
            toks.append("∪")
            i += 5
        elif s[i:i + 12].lower() == "intersection" and \
                (i + 12 >= len(s) or not s[i + 12].isalpha()):
            toks.append("∩")
            i += 12
        elif s[i:i + 10].lower() == "difference" and \
                (i + 10 >= len(s) or not s[i + 10].isalpha()):
            toks.append("DIFF")
            i += 10
        else:
            return None
    return toks


class _ExprParser:
    def __init__(self, toks):
        self.toks = toks
        self.pos = 0

    def peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) \
            else None

    def parse(self):
        node = self._expr()
        if node is None or self.pos != len(self.toks):
            return None
        return node

    def _expr(self):
        node = self._term()
        if node is None:
            return None
        while self.peek() in ("∪", "DIFF"):
            op = self.toks[self.pos]
            self.pos += 1
            rhs = self._term()
            if rhs is None:
                return None
            node = ("bin", op, node, rhs)
        return node

    def _term(self):
        node = self._factor()
        if node is None:
            return None
        while self.peek() == "∩":
            self.pos += 1
            rhs = self._factor()
            if rhs is None:
                return None
            node = ("bin", "∩", node, rhs)
        return node

    def _factor(self):
        node = self._primary()
        if node is None:
            return None
        while self.peek() == "'":
            self.pos += 1
            node = ("comp", node)
        return node

    def _primary(self):
        t = self.peek()
        if isinstance(t, tuple) and t[0] == "NAME":
            self.pos += 1
            return ("name", t[1])
        if t == "(":
            self.pos += 1
            node = self._expr()
            if node is None or self.peek() != ")":
                return None
            self.pos += 1
            return node
        return None


def _parse_set_expr(text):
    toks = _tokenize_expr(text)
    if not toks:
        return None
    return _ExprParser(toks).parse()


def _expr_names(node, acc=None):
    if acc is None:
        acc = set()
    if node[0] == "name":
        acc.add(node[1])
    elif node[0] == "comp":
        _expr_names(node[1], acc)
    else:
        _expr_names(node[2], acc)
        _expr_names(node[3], acc)
    return acc


def _expr_has_comp(node):
    if node[0] == "comp":
        return True
    if node[0] == "bin":
        return _expr_has_comp(node[2]) or _expr_has_comp(node[3])
    return False


def _disp(node, top=True):
    if node[0] == "name":
        return node[1]
    if node[0] == "comp":
        # _disp(top=False) already parenthesises a compound
        # child; a bare name needs none, a complement child
        # needs its own parens: (A')'.
        inner = _disp(node[1], top=False)
        if node[1][0] == "comp":
            inner = "(" + inner + ")"
        return inner + "'"
    op = node[1]
    sym = {"∪": "∪", "∩": "∩", "DIFF": "-"}[op]
    s = f"{_disp(node[2], top=False)} {sym} " \
        f"{_disp(node[3], top=False)}"
    return s if top else "(" + s + ")"


def _eval(node, named):
    """Evaluate to an ordered value list; None when a name
    is undefined or a complement has no universal set."""
    if node[0] == "name":
        vals = named.get(node[1])
        return list(vals) if vals is not None else None
    if node[0] == "comp":
        uni = named.get("U")
        if uni is None:
            return None
        inner = _eval(node[1], named)
        if inner is None:
            return None
        iset = set(inner)
        return [v for v in uni if v not in iset]
    left = _eval(node[2], named)
    right = _eval(node[3], named)
    if left is None or right is None:
        return None
    rset = set(right)
    if node[1] == "∪":
        out = list(left)
        for v in right:
            if v not in out:
                out.append(v)
        return out
    if node[1] == "∩":
        return [v for v in left if v in rset]
    return [v for v in left if v not in rset]  # DIFF


def _eval_steps(node, named, lines, seen=None):
    """Post-order 'EXPR = {values}' lines for compound
    sub-expressions (the worked steps of a computation)."""
    if seen is None:
        seen = set()
    if node[0] == "name":
        return _eval(node, named)
    if node[0] == "comp":
        _eval_steps(node[1], named, lines, seen)
    else:
        _eval_steps(node[2], named, lines, seen)
        _eval_steps(node[3], named, lines, seen)
    vals = _eval(node, named)
    if vals is None:
        return None
    d = _disp(node)
    if d not in seen:
        seen.add(d)
        lines.append(f"{d} = {_show(vals)}")
    return vals


def _given_line(named, names):
    parts = [f"{n} = {_show(named[n])}" for n in names
             if n in named]
    return "Given: " + ", ".join(parts) + "." if parts else ""


# ---------------------------------------------------------------------------
# (a) Set-identity VERIFY + direct complement computation
# ---------------------------------------------------------------------------

def _top_level_equals(text):
    """Index of the single '=' at parenthesis depth 0, or
    None when there is not exactly one."""
    depth = 0
    hits = []
    for i, c in enumerate(text):
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "=" and depth == 0:
            hits.append(i)
    return hits[0] if len(hits) == 1 else None


def _branch_verify(q, named, rest):
    m = re.search(r"\b(?:verify|show|prove)\b\s*(?:that)?\s+",
                  rest, re.I)
    if not m:
        return None
    if len(named) < 2:
        return None
    ident = rest[m.end():].strip().rstrip("?.")
    ident = re.sub(r"\s+(?:for\s+)?(?:the\s+)?(?:given|above)"
                   r"\s+sets?\s*$", "", ident, flags=re.I)
    eq = _top_level_equals(ident)
    if eq is None:
        return None
    lhs = _parse_set_expr(ident[:eq])
    rhs = _parse_set_expr(ident[eq + 1:])
    if lhs is None or rhs is None:
        return None
    names = _expr_names(lhs) | _expr_names(rhs)
    if not names or not names <= set(named):
        return None
    # The prefix before the verify keyword must be only the
    # (blanked) assignments and filler — nothing else asked.
    if not _only_filler(rest[:m.start()]):
        return None
    lsteps, rsteps = [], []
    lvals = _eval_steps(lhs, named, lsteps)
    rvals = _eval_steps(rhs, named, rsteps)
    if lvals is None or rvals is None:
        return None
    order = [n for n in ("U", "A", "B", "C") if n in named]
    order += [n for n in named if n not in order]
    steps = [_given_line(named, order)]
    steps.append(f"LHS: {_disp(lhs)}")
    steps.extend("  " + s for s in lsteps)
    steps.append(f"RHS: {_disp(rhs)}")
    steps.extend("  " + s for s in rsteps)
    if set(lvals) == set(rvals):
        steps.append(
            f"Both sides are equal to {_show(lvals)}, so the "
            f"identity is verified.")
        return {"type": "sets", "op": "w193_verify",
                "answer": _show(lvals), "steps": steps}
    steps.append(
        f"The two sides are not equal for these sets, so "
        f"the identity does not hold here.")
    return {"type": "sets", "op": "w193_verify",
            "answer": f"LHS = {_show(lvals)}, RHS = "
                      f"{_show(rvals)} (not equal)",
            "steps": steps}


def _branch_compute(q, named, rest):
    """Direct complement computation: 'find (A union B)''
    with U, A, B given.  A complement node is REQUIRED, so
    plain union / intersection asks never land here."""
    if "U" not in named or len(named) < 2:
        return None
    # Candidate expression starts: every '(' or defined-name
    # position; the text before it must be pure ask filler
    # and the expression must consume the rest.
    starts = [m.start() for m in re.finditer(r"\(|[A-Z]", rest)]
    for st in starts:
        if not _only_filler(rest[:st]):
            continue
        tail = rest[st:].strip().rstrip("?.").strip()
        tail = re.sub(r"\s+(?:for\s+)?(?:the\s+)?(?:given|"
                      r"above)\s+sets?\s*$", "", tail,
                      flags=re.I)
        node = _parse_set_expr(tail)
        if node is None or not _expr_has_comp(node):
            continue
        names = _expr_names(node)
        if not names or not names <= set(named):
            continue
        lines = []
        vals = _eval_steps(node, named, lines)
        if vals is None:
            continue
        order = [n for n in ("U", "A", "B", "C") if n in named]
        steps = [_given_line(named, order)] + lines
        return {"type": "sets", "op": "w193_set_compute",
                "answer": _show(vals), "steps": steps}
    return None


# ---------------------------------------------------------------------------
# (b) Ordered-pair equality
# ---------------------------------------------------------------------------

_PAIR_EQ_RE = re.compile(r"\(([^()]*)\)\s*=\s*\(([^()]*)\)")
_PAIR_ALLOWED = {"x", "y"}


def _pair_component(text):
    """Parse one ordered-pair component: a number or a
    LINEAR expression in x / y.  SymPy expr or None."""
    t = text.strip()
    if not t:
        return None
    try:
        expr = parse_expression(t)
    except Exception:
        return None
    if isinstance(expr, tuple):
        return None
    syms = expr.free_symbols
    if any(str(s) not in _PAIR_ALLOWED for s in syms):
        return None
    if syms:
        try:
            poly = sp.Poly(expr, *sorted(syms, key=str))
        except Exception:
            return None
        if poly is None or poly.total_degree() > 1:
            return None
    return expr


def _branch_ordered_pair(q):
    if "{" in q or "[" in q:
        return None
    m = _PAIR_EQ_RE.search(q)
    if not m:
        return None
    if not _only_filler(q[:m.start()] + " " + q[m.end():],
                        extra={"x", "y"}):
        return None
    lparts = m.group(1).split(",")
    rparts = m.group(2).split(",")
    if len(lparts) != 2 or len(rparts) != 2:
        return None
    lexprs = [_pair_component(p) for p in lparts]
    rexprs = [_pair_component(p) for p in rparts]
    if any(e is None for e in lexprs + rexprs):
        return None
    ordered = []
    for e in lexprs + rexprs:
        for name in ("x", "y"):
            if sp.Symbol(name) in e.free_symbols and \
                    sp.Symbol(name) not in ordered:
                ordered.append(sp.Symbol(name))
    if not ordered:
        return None
    equations = []
    display = []
    for l, r in zip(lexprs, rexprs):
        if l.free_symbols or r.free_symbols:
            equations.append(sp.Eq(l, r))
            display.append(f"{fmt(l)} = {fmt(r)}")
        elif sp.simplify(l - r) != 0:
            # A constant component pair already disagrees:
            # the pairs cannot be equal — not ours to serve.
            return None
    if not equations:
        return None
    try:
        sols = sp.solve(equations, ordered, dict=True)
    except Exception:
        return None
    if len(sols) != 1:
        return None
    sol = sols[0]
    if set(sol.keys()) != set(ordered):
        return None
    for u in ordered:
        if sol[u].free_symbols or sol[u].is_real is False:
            return None
    for l, r in zip(lexprs, rexprs):
        if sp.simplify(l.subs(sol) - r.subs(sol)) != 0:
            return None
    final = ", ".join(f"{u} = {fmt_num(sol[u])}"
                      for u in ordered)
    steps = ["Equal ordered pairs have equal corresponding "
             "components — equate each pair:"]
    steps.extend(display)
    steps.append(f"Solving, we get {final}.")
    return {"type": "sets", "op": "w193_ordered_pair",
            "answer": final, "steps": steps}


# ---------------------------------------------------------------------------
# (c) Cartesian products
# ---------------------------------------------------------------------------

_OPERAND = r"(?:\((?:[^()]|\([^()]*\))*\)|[A-Z])"
_PRODUCT_RE = re.compile(
    _OPERAND + r"\s*(?:×|\bx\b|\bX\b)\s*" + _OPERAND +
    r"(?:\s*(?:×|\bx\b|\bX\b)\s*" + _OPERAND + r")?")
_WORD_PRODUCT_RE = re.compile(
    r"cartesian\s+product\s+of\s+([A-Z])\s+and\s+([A-Z])",
    re.I)
_MAX_LIST_PRODUCT = 64


def _operand_values(text, named):
    """One product operand: a defined name, or a parenthesised
    set expression over defined names.  Ordered values."""
    t = text.strip()
    if re.fullmatch(r"[A-Z]", t):
        vals = named.get(t)
        return list(vals) if vals is not None else None
    if t.startswith("(") and t.endswith(")"):
        node = _parse_set_expr(t)
        if node is None:
            return None
        if not _expr_names(node) <= set(named):
            return None
        return _eval(node, named)
    return None


def _branch_cartesian(q, named, rest):
    if len(named) < 1:
        # The count-given dress ("A x B has 6 elements and
        # A has 2 elements, find n(B)") carries no brace
        # sets at all — it is the only branch that can fire.
        return _branch_cartesian_count_given(q, named, rest)
    m = _PRODUCT_RE.search(rest)
    word = None
    if m is None:
        word = _WORD_PRODUCT_RE.search(rest)
        if word is None:
            return _branch_cartesian_count_given(q, named, rest)
        op_texts = [word.group(1), word.group(2)]
        span = word.span()
    else:
        span = m.span()
        # Split the matched product back into operands on the
        # top-level separators.
        op_texts = _split_product(m.group(0))
        if op_texts is None:
            return None
    if not _only_filler(rest[:span[0]] + " " + rest[span[1]:]):
        # Not a clean product ask — maybe the count-given
        # dress ("A x B has 6 elements and A has 2...").
        return _branch_cartesian_count_given(q, named, rest)
    operands = []
    for t in op_texts:
        vals = _operand_values(t, named)
        if vals is None:
            return _branch_cartesian_count_given(q, named,
                                                 rest)
        operands.append((t.strip(), vals))
    ql = q.lower()
    is_count = bool(re.search(
        r"how\s+many|number\s+(?:of\s+)?elements|"
        r"n\s*\(|elements\s+are\s+there|cardinality", ql))
    sizes = [len(v) for _, v in operands]
    total = 1
    for s in sizes:
        total *= s
    names_disp = " × ".join(
        t if re.fullmatch(r"[A-Z]", t) else t
        for t, _ in operands)
    if is_count:
        size_str = " × ".join(str(s) for s in sizes)
        steps = [
            "The number of elements in a Cartesian product "
            "is the product of the numbers of elements.",
            f"Number of elements in {names_disp} = {size_str}"
            f" = {total}."]
        return {"type": "sets", "op": "w193_cartesian_count",
                "answer": str(total), "steps": steps}
    if total > _MAX_LIST_PRODUCT:
        return None
    tuples = list(itertools.product(*[v for _, v in operands]))
    body = ", ".join(
        "(" + ", ".join(_fmt_val(v) for v in tup) + ")"
        for tup in tuples)
    steps = [
        f"Pair each element of the first set with each "
        f"element of the next, in order.",
        f"{names_disp} has {sizes[0]}"
        + "".join(f" × {s}" for s in sizes[1:])
        + f" = {total} ordered "
        + ("pairs." if len(operands) == 2 else "tuples.")]
    return {"type": "sets", "op": "w193_cartesian_list",
            "answer": "{" + body + "}", "steps": steps}


def _split_product(text):
    """Split 'A × (B ∩ C) × P' into operand texts on the
    top-level × / x separators."""
    parts = []
    depth = 0
    cur = ""
    i = 0
    while i < len(text):
        c = text[i]
        if c == "(":
            depth += 1
            cur += c
            i += 1
        elif c == ")":
            depth -= 1
            cur += c
            i += 1
        elif depth == 0 and (c == "×" or
                             (c in "xX" and (i == 0 or
                                             not text[i - 1].isalnum()) and
                              (i + 1 >= len(text) or
                               not text[i + 1].isalnum()))):
            parts.append(cur.strip())
            cur = ""
            i += 1
        else:
            cur += c
            i += 1
    parts.append(cur.strip())
    if any(not p for p in parts) or len(parts) < 2:
        return None
    return parts


def _branch_cartesian_count_given(q, named, rest):
    """'If A × B has 6 elements and A has 2 elements, find
    n(B)' — exact division only."""
    m1 = re.search(r"([A-Z])\s*(?:×|\bx\b)\s*([A-Z])\s+has\s+"
                   r"(\d+)\s+elements", q)
    if not m1:
        return None
    n1, n2, total = m1.group(1), m1.group(2), int(m1.group(3))
    known = None
    known_name = None
    for m2 in re.finditer(r"([A-Z])\s+has\s+(\d+)\s+elements",
                          q):
        if m2.start() < m1.end() and m1.start() < m2.end():
            continue  # inside the product statement itself
        if m2.group(1) in (n1, n2):
            known_name = m2.group(1)
            known = int(m2.group(2))
    if known is None or known == 0:
        return None
    other = n2 if known_name == n1 else n1
    m3 = re.search(r"n\s*\(\s*" + other + r"\s*\)|elements\s+"
                   r"(?:in|of)\s+" + other + r"\b", q)
    if not m3:
        return None
    if total % known != 0:
        return None
    val = total // known
    steps = [
        f"n({n1} × {n2}) = n({n1}) × n({n2}).",
        f"{total} = {known} × n({other}), so n({other}) = "
        f"{total} ÷ {known} = {val}."]
    return {"type": "sets", "op": "w193_cartesian_count",
            "answer": str(val), "steps": steps}


# ---------------------------------------------------------------------------
# (d) Domain & range of a relation given as a roster of pairs
# ---------------------------------------------------------------------------

_ROSTER_PAIRS_RE = re.compile(
    r"\{\s*\(\s*[^()]*\)\s*(?:,\s*\(\s*[^()]*\)\s*)*\}")


def _branch_domain_range(q, named, rest):
    ql = q.lower()
    want_dom = "domain" in ql
    want_range = re.search(r"\brange\b", ql) is not None
    want_cod = "codomain" in ql or "co-domain" in ql or \
        "co domain" in ql
    if not (want_dom or want_range or want_cod):
        return None
    m = _ROSTER_PAIRS_RE.search(q)
    if not m:
        return None
    pairs = []
    for pm in re.finditer(r"\(([^()]*)\)", m.group(0)):
        parts = pm.group(1).split(",")
        if len(parts) != 2:
            return None
        a = _parse_value(parts[0])
        b = _parse_value(parts[1])
        if a is None or b is None:
            return None
        pairs.append((a, b))
    if not pairs:
        return None
    codomain = None
    if want_cod:
        fm = re.search(r"from\s+([A-Z])\s*(?:=\s*\{[^{}]*\})?"
                       r"\s+to\s+([A-Z])", q)
        if fm and fm.group(2) in named:
            codomain = named[fm.group(2)]
        else:
            # Codomain cannot be read off a bare roster —
            # serving domain/range alone would be partial.
            return None
    # Accounting: blank the roster and any named-set
    # assignments; the rest must be ask filler (single
    # capital letters — set / relation names — allowed).
    text = q[:m.start()] + " " + q[m.end():]
    text = _NAMED_RE.sub(" ", text)
    words = re.findall(r"[A-Za-z][A-Za-z-]*", text)
    if any(w.lower() not in _FILLER and
           not re.fullmatch(r"[A-Z]", w) for w in words):
        return None
    if re.search(r"\d", text):
        return None
    dom = []
    rng = []
    for a, b in pairs:
        if a not in dom:
            dom.append(a)
        if b not in rng:
            rng.append(b)
    steps = ["The domain is the set of first elements of "
             "the ordered pairs, and the range is the set "
             "of second elements."]
    parts = []
    if want_dom:
        steps.append(f"Domain = {_show(dom)}")
        parts.append(f"Domain = {_show(dom)}")
    if want_range:
        steps.append(f"Range = {_show(rng)}")
        parts.append(f"Range = {_show(rng)}")
    if want_cod:
        steps.append(f"Codomain = {_show(codomain)}")
        parts.append(f"Codomain = {_show(codomain)}")
    return {"type": "sets", "op": "w193_domain_range",
            "answer": ", ".join(parts), "steps": steps}


# ---------------------------------------------------------------------------
# (e) Roster <-> set-builder conversions (decidable only)
# ---------------------------------------------------------------------------

_BUILDER_RE = re.compile(r"\{\s*x\s*[:|]\s*([^{}]*)\}")
_NUM_RE = r"-?\d+(?:\.\d+)?(?:/\d+)?"


def _is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    r = int(n ** 0.5)
    for d in range(3, r + 1, 2):
        if n % d == 0:
            return False
    return True


def _condition_values(cond):
    """A decidable set-builder condition -> ordered values,
    or None.  The condition text is consumed pattern by
    pattern; any leftover word outside the filler set
    declines the conversion (no partial parses)."""
    t = " " + re.sub(r"\s+", " ", cond.lower().strip()) + " "
    filt = None
    m = re.search(r"multiple\s+of\s+(\d+)", t) or \
        re.search(r"divisible\s+by\s+(\d+)", t)
    if m:
        filt = ("mult", int(m.group(1)))
        t = t[:m.start()] + " " + t[m.end():]
    elif "perfect square" in t or "square of a natural" in t \
            or "square of natural" in t:
        filt = ("square", None)
        t = re.sub(r"perfect\s+square|square\s+of\s+(?:a\s+)?"
                   r"natural(?:\s+number)?", " ", t)
    elif "cube of a natural" in t or "cube of natural" in t:
        filt = ("cube", None)
        t = re.sub(r"cube\s+of\s+(?:a\s+)?natural"
                   r"(?:\s+number)?", " ", t)
    elif re.search(r"\beven\b", t):
        filt = ("even", None)
        t = re.sub(r"\beven\b", " ", t)
    elif re.search(r"\bodd\b", t):
        filt = ("odd", None)
        t = re.sub(r"\bodd\b", " ", t)
    elif re.search(r"\bprime\b", t):
        filt = ("prime", None)
        t = re.sub(r"\bprime\b", " ", t)
    domain = None
    if "natural" in t:
        domain = "N"
        t = t.replace("natural", " ")
    elif "whole" in t:
        domain = "W"
        t = t.replace("whole", " ")
    elif "integer" in t:
        domain = "Z"
        t = t.replace("integer", " ")
    lo = None
    lo_inc = True
    hi = None
    hi_inc = True
    m = re.search(r"(" + _NUM_RE + r")\s*(<=|≤|<)\s*x\s*"
                  r"(<=|≤|<)\s*(" + _NUM_RE + r")", t)
    if m:
        lo = float(Fraction(m.group(1)))
        lo_inc = m.group(2) in ("<=", "≤")
        hi_inc = m.group(3) in ("<=", "≤")
        hi = float(Fraction(m.group(4)))
        t = t[:m.start()] + " " + t[m.end():]
    else:
        m = re.search(r"\bx\s*(<=|≤)\s*(" + _NUM_RE + r")", t)
        if m:
            hi, hi_inc = float(Fraction(m.group(2))), True
            t = t[:m.start()] + " " + t[m.end():]
        else:
            m = re.search(r"\bx\s*<\s*(" + _NUM_RE + r")", t)
            if m:
                hi, hi_inc = float(Fraction(m.group(1))), False
                t = t[:m.start()] + " " + t[m.end():]
            else:
                m = re.search(r"less\s+than\s+or\s+equal\s+to\s+"
                              r"(" + _NUM_RE + r")", t) or \
                    re.search(r"not\s+more\s+than\s+(" +
                              _NUM_RE + r")", t)
                if m:
                    hi, hi_inc = float(Fraction(m.group(1))), True
                    t = t[:m.start()] + " " + t[m.end():]
                else:
                    m = re.search(r"less\s+than\s+(" + _NUM_RE +
                                  r")", t)
                    if m:
                        hi, hi_inc = float(Fraction(
                            m.group(1))), False
                        t = t[:m.start()] + " " + t[m.end():]
        m = re.search(r"\bx\s*(>=|≥)\s*(" + _NUM_RE + r")", t)
        if m:
            lo, lo_inc = float(Fraction(m.group(2))), True
            t = t[:m.start()] + " " + t[m.end():]
        else:
            m = re.search(r"\bx\s*>\s*(" + _NUM_RE + r")", t)
            if m:
                lo, lo_inc = float(Fraction(m.group(1))), False
                t = t[:m.start()] + " " + t[m.end():]
            else:
                m = re.search(r"greater\s+than\s+(" + _NUM_RE +
                              r")", t)
                if m:
                    lo, lo_inc = float(Fraction(m.group(1))), \
                        False
                    t = t[:m.start()] + " " + t[m.end():]
        m = re.search(r"between\s+(" + _NUM_RE + r")\s+and\s+"
                      r"(" + _NUM_RE + r")", t)
        if m and lo is None and hi is None:
            lo = float(Fraction(m.group(1)))
            hi = float(Fraction(m.group(2)))
            lo_inc = hi_inc = False
            t = t[:m.start()] + " " + t[m.end():]
    leftover = [w for w in re.findall(r"[a-z]+", t)
                if w not in ("x", "is", "a", "an", "the", "and",
                             "number", "numbers", "belongs",
                             "to", "in", "of", "set", "all",
                             "positive")]
    if leftover:
        return None
    if hi is None:
        return None  # unbounded — not a listable roster
    if domain is None:
        domain = "Z" if (lo is not None and lo < 0) else "N"
    if lo is None:
        start = {"N": 1, "W": 0}.get(domain)
        if start is None:
            return None  # integers with no lower bound
        lo_i = start
    elif lo_inc:
        lo_i = math.ceil(lo)
    else:
        lo_i = math.floor(lo) + 1
    hi_i = math.floor(hi) if hi_inc else math.ceil(hi) - 1
    if hi_i - lo_i > 10000 or hi_i < lo_i:
        return None
    if filt and filt[0] in ("square", "cube"):
        power = 2 if filt[0] == "square" else 3
        out = []
        r = 1 if domain == "N" else 0
        while True:
            v = r ** power
            if v > hi_i and r > 0:
                break
            if lo_i <= v <= hi_i:
                out.append(v)
            r += 1
            if r > 1000:
                return None
        return out or None
    out = []
    for n in range(lo_i, hi_i + 1):
        if filt is None:
            out.append(n)
        elif filt[0] == "even" and n % 2 == 0:
            out.append(n)
        elif filt[0] == "odd" and n % 2 != 0:
            out.append(n)
        elif filt[0] == "prime" and _is_prime(n):
            out.append(n)
        elif filt[0] == "mult" and filt[1] and n % filt[1] == 0 \
                and n != 0:
            out.append(n)
    if not out or len(out) > 200:
        return None
    return out


def _branch_roster_from_builder(q, named, rest):
    ql = q.lower()
    if not any(w in ql for w in ("roster", "tabular", "list")):
        return None
    m = _BUILDER_RE.search(q)
    cond = None
    if m:
        cond = m.group(1)
    else:
        # Described set: "the set of all even natural numbers
        # less than 10" / vowels / letters of a word.
        vm = re.search(r"vowels?\s+(?:in|of)\s+the\s+(?:english"
                       r"\s+)?alphabet", ql)
        if vm:
            vals = ["a", "e", "i", "o", "u"]
            return {"type": "sets",
                    "op": "w193_roster_from_builder",
                    "answer": _show(vals),
                    "steps": ["The vowels in the English "
                              "alphabet are a, e, i, o, u.",
                              f"Roster form: {_show(vals)}"]}
        lm = re.search(r"letters?\s+(?:in|of)\s+the\s+word\s+"
                       r"['\"]([A-Za-z]+)['\"]", ql) or \
            re.search(r"letters?\s+(?:in|of)\s+the\s+word\s+"
                      r"([A-Za-z]+)", ql)
        if lm:
            word = lm.group(1)
            vals = sorted(set(word.upper()))
            return {"type": "sets",
                    "op": "w193_roster_from_builder",
                    "answer": _show(vals),
                    "steps": [f"A set lists each distinct "
                              f"letter once.",
                              f"Roster form: {_show(vals)}"]}
        dm = re.search(r"set\s+of\s+(?:all\s+)?((?:even\s+|"
                       r"odd\s+|prime\s+)?(?:natural|whole|"
                       r"integer)\s+numbers?\b[^.?]*)", ql)
        if dm:
            cond = "x is a " + re.sub(
                r"\s+in\s+(?:roster|tabular|list).*$", "",
                dm.group(1))
        else:
            return None
    vals = _condition_values(cond)
    if vals is None:
        return None
    return {"type": "sets", "op": "w193_roster_from_builder",
            "answer": _show(vals),
            "steps": [f"List every value that satisfies the "
                      f"condition, in order.",
                      f"Roster form: {_show(vals)}"]}


def _num(v):
    return float(v)


def _branch_builder_from_roster(q, named, rest):
    ql = q.lower()
    if "set-builder" not in ql and "set builder" not in ql:
        return None
    vals = None
    for m in re.finditer(r"\{([^{}]*)\}", q):
        cand = _parse_roster(m.group(1))
        if cand is not None and len(cand) >= 3 and \
                all(isinstance(v, (int, Fraction)) and
                    float(v) == int(float(v)) for v in cand):
            vals = [int(float(v)) for v in cand]
            break
    if vals is None or vals != sorted(vals):
        return None
    a, b = vals[0], vals[-1]
    builder = None
    diffs = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    if all(d == 1 for d in diffs):
        if a >= 1:
            builder = (f"{{x : x is a natural number and "
                       f"{a} ≤ x ≤ {b}}}" if a > 1 else
                       f"{{x : x is a natural number less "
                       f"than {b + 1}}}")
        else:
            builder = f"{{x : x is an integer and {a} ≤ x ≤ {b}}}"
    elif all(v % 2 == 0 for v in vals) and \
            all(d == 2 for d in diffs):
        builder = (f"{{x : x is an even natural number and "
                   f"{a} ≤ x ≤ {b}}}")
    elif all(v % 2 != 0 for v in vals) and \
            all(d == 2 for d in diffs):
        builder = (f"{{x : x is an odd natural number and "
                   f"{a} ≤ x ≤ {b}}}")
    elif all(int(round(v ** 0.5)) ** 2 == v for v in vals) and \
            [int(round(v ** 0.5)) for v in vals] == \
            list(range(int(round(a ** 0.5)),
                       int(round(a ** 0.5)) + len(vals))):
        builder = (f"{{x : x is the square of a natural "
                   f"number and x ≤ {b}}}")
    elif len(set(diffs)) == 1 and diffs[0] > 1 and \
            all(v % diffs[0] == 0 for v in vals):
        builder = (f"{{x : x is a multiple of {diffs[0]} and "
                   f"{a} ≤ x ≤ {b}}}")
    if builder is None:
        return None
    return {"type": "sets", "op": "w193_builder_from_roster",
            "answer": builder,
            "steps": [f"The elements follow one clear "
                      f"pattern, so the set-builder form is:",
                      builder]}


_INTERVAL_RE = re.compile(
    r"([\(\[])\s*(" + _NUM_RE + r")\s*,\s*(" + _NUM_RE +
    r")\s*([\)\]])")


def _branch_interval(q, named, rest):
    ql = q.lower()
    m = _INTERVAL_RE.search(q)
    if m and ("set-builder" in ql or "set builder" in ql):
        lo = _fmt_val(_parse_value(m.group(2)))
        hi = _fmt_val(_parse_value(m.group(3)))
        lop = "≤" if m.group(1) == "[" else "<"
        rop = "≤" if m.group(4) == "]" else "<"
        builder = f"{{x : {lo} {lop} x {rop} {hi}}}"
        return {"type": "sets", "op": "w193_interval",
                "answer": builder,
                "steps": ["Square bracket means the end point "
                          "is included (≤); round bracket "
                          "means it is excluded (<).",
                          f"Set-builder form: {builder}"]}
    bm = _BUILDER_RE.search(q)
    if bm and "interval" in ql:
        cond = bm.group(1)
        mm = re.fullmatch(r"\s*(" + _NUM_RE + r")\s*(<=|≤|<)"
                          r"\s*x\s*(<=|≤|<)\s*(" + _NUM_RE +
                          r")\s*", cond)
        if not mm:
            return None
        lo = _fmt_val(_parse_value(mm.group(1)))
        hi = _fmt_val(_parse_value(mm.group(4)))
        lb = "[" if mm.group(2) in ("<=", "≤") else "("
        rb = "]" if mm.group(3) in ("<=", "≤") else ")"
        interval = f"{lb}{lo}, {hi}{rb}"
        return {"type": "sets", "op": "w193_interval",
                "answer": interval,
                "steps": ["≤ means the end point is included "
                          "(square bracket); < means it is "
                          "excluded (round bracket).",
                          f"Interval form: {interval}"]}
    return None


# ---------------------------------------------------------------------------
# (f) Subset / membership batteries — whole battery or nothing
# ---------------------------------------------------------------------------

_SET_OPERAND = r"(?:\{[^{}]*\}|∅|φ|\{\}|[A-Z])"
_ELEM_OPERAND = r"(?:-?\d+(?:\.\d+)?(?:/\d+)?|[a-zA-Z])"
_STMT_RE = re.compile(
    r"(" + _SET_OPERAND + r"|" + _ELEM_OPERAND + r")\s*"
    r"(∈|∉|⊆|⊂|⊄|⊈|⊊)\s*(" + _SET_OPERAND + r")")


def _resolve_set(text, named):
    t = text.strip()
    if t in ("∅", "φ", "{}"):
        return []
    if t.startswith("{"):
        return _parse_roster(t[1:-1])
    if re.fullmatch(r"[A-Z]", t):
        vals = named.get(t)
        return list(vals) if vals is not None else None
    return None


def _eval_statement(lhs_t, op, rhs_t, named):
    """(verdict, display) or None when the statement is not
    mechanically decidable in our dress."""
    rhs = _resolve_set(rhs_t, named)
    if rhs is None:
        return None
    rset = set(rhs)
    if op in ("∈", "∉"):
        if lhs_t.strip().startswith("{"):
            return None  # a set as an element — out of dress
        elem = _parse_value(lhs_t)
        if elem is None:
            return None
        verdict = elem in rset
        if op == "∉":
            verdict = not verdict
        return verdict, f"{lhs_t.strip()} {op} {rhs_t.strip()}"
    lhs = _resolve_set(lhs_t, named)
    if lhs is None:
        return None
    lset = set(lhs)
    if op == "⊆":
        verdict = lset <= rset
    elif op == "⊂":
        verdict = lset < rset
    elif op in ("⊄", "⊈"):
        verdict = not (lset <= rset)
    else:  # ⊊
        verdict = not (lset < rset)
    return verdict, f"{lhs_t.strip()} {op} {rhs_t.strip()}"


def _branch_battery(q, named, rest):
    ql = q.lower()
    matches = list(_STMT_RE.finditer(q))
    dress = ("state whether" in ql or "true or false" in ql
             or "true/false" in ql)
    if len(matches) == 0 or (len(matches) < 2 and not dress):
        # Single word-dress statements: "Is {1, 2} a subset
        # of A?" / "Is 5 an element of A?"
        m = re.search(r"is\s+(\{[^{}]*\}|[A-Z])\s+a\s+subset"
                      r"\s+of\s+(\{[^{}]*\}|[A-Z]|∅)", q, re.I)
        op = "⊆"
        if not m:
            m = re.search(r"is\s+(" + _ELEM_OPERAND + r")\s+"
                          r"an?\s+element\s+of\s+(\{[^{}]*\}|"
                          r"[A-Z]|∅)", q, re.I)
            op = "∈"
        if not m:
            return None
        out = _eval_statement(m.group(1), op, m.group(2),
                              named)
        if out is None:
            return None
        verdict, disp = out
        word = "True" if verdict else "False"
        return {"type": "sets", "op": "w193_battery",
                "answer": word,
                "steps": [f"{disp}: {word}."]}
    # Here len(matches) >= 2, or == 1 with the state-whether
    # dress — either way the symbolic battery path applies.
    # Region accounting: between the first and last
    # statement, only separators / part markers may remain.
    region = q[matches[0].start():matches[-1].end()]
    stripped = _STMT_RE.sub(" ", region)
    stripped = re.sub(r"\(\s*(?:i{1,3}|iv|v|vi{0,3})\s*\)",
                      " ", stripped)
    if re.search(r"[^\s,;.:]", stripped):
        return None
    # Trailing accounting: anything after the last statement
    # must be filler — a further (undecidable) statement
    # hiding there would make this a fragment serve.
    tail = re.sub(r"\(\s*(?:i{1,3}|iv|v|vi{0,3})\s*\)", " ",
                  q[matches[-1].end():])
    if not _only_filler(tail):
        return None
    steps = []
    verdicts = []
    for i, m in enumerate(matches, 1):
        out = _eval_statement(m.group(1), m.group(2),
                              m.group(3), named)
        if out is None:
            return None  # one bad statement sinks the battery
        verdict, disp = out
        word = "True" if verdict else "False"
        verdicts.append(word)
        steps.append(f"({i}) {disp}: {word}")
    return {"type": "sets", "op": "w193_battery",
            "answer": ", ".join(verdicts), "steps": steps}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_CONCEPT_GUARD = re.compile(
    r"\bwhy\b|\bkyon\b|\bkyu\b|\bexplain\b|\bdefine\b|"
    r"\bmeaning\s+of\b|\bdifference\s+between\b", re.I)


def solve_sets193(question):
    """Wave 193 Sets & Cartesian-product schemas; None
    unless one strict schema settles the question
    completely from explicitly given data."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip() or _CONCEPT_GUARD.search(q):
        return None
    try:
        named, rest = _extract_named(q)
        for branch in (_branch_ordered_pair_wrap,
                       _branch_verify, _branch_compute,
                       _branch_cartesian, _branch_domain_range,
                       _branch_interval,
                       _branch_roster_from_builder,
                       _branch_builder_from_roster,
                       _branch_battery):
            try:
                out = branch(q, named, rest)
            except Exception:
                out = None
            if out is not None:
                return out
    except Exception:
        return None
    return None


def _branch_ordered_pair_wrap(q, named, rest):
    return _branch_ordered_pair(q)
