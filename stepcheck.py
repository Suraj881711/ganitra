"""Wave 85: the step checker — "meri galti kahan hai".

A student pastes a question AND their own worked solution into
the chat; Ganitra checks the working against its own solved
steps and replies like a kind teacher: the first step that goes
wrong (quoted), what that step should be, and the full correct
solution. If every step is right, it says so plainly.

INPUT CONTRACT (the light convention, documented for students
in the reply style itself): the chat message is

    <the question>
    my solution:
    <one working step per line>
    <one working step per line>

The marker line may be any of: "my solution:", "my working:",
"my steps:", "mera solution:", "meri solution:", "mera hal:",
"मेरा हल:", "मेरा solution:", "solution:" — followed by the
working lines. Steps may also be separated by "->" / "→" / ";"
when they arrive on one line.

DESIGN — validate steps on their own logic, never by diffing
against the reference method's text:

* Equations (linear/quadratic): an equation step follows from
  the previous one iff the two (lhs - rhs) differences are
  PROPORTIONAL by a non-zero constant — the exact invariant of
  every legal move (add/subtract the same thing both sides,
  multiply/divide both sides, move a term across). A different
  but valid method therefore passes untouched; the first
  non-proportional step is the first real mistake.
* Simplify/expand chains: each expression must be EQUIVALENT
  to the previous one (sympy simplify(a - b) == 0).
* Arithmetic / percentages / applied numeric problems: every
  "expr = value" claim inside a line is checked numerically;
  a wrong claim is the mistake. The final value is compared
  with the reference answer.

Only flag a step when the maths SAYS it is wrong: lines that
cannot be parsed (labels, Hindi text, annotations) are skipped,
never accused. A question family the checker cannot evaluate
(trig, geometry, calculus...) gets an honest "can't check this
type yet" reply PLUS the correct solution — never silence and
never a fake check.

SCOPE v1: arithmetic, linear/quadratic equations,
simplification, percentages (incl. discount/profit-style
applied questions whose answers are numeric).

The hook is strictly gated (marker + a reference solve + at
least one checkable working line); anything else returns None
and the normal solve flow is byte-for-byte untouched, so a
gibberish message still earns the Wave 67 one-line not-found.
"""
import re

import sympy as sp

from fallback import _flavour
from i18n import solve_failed
from solver.expression_parser import fmt, fmt_num, parse_expression
from solver.router import solve_question


# ---------------------------------------------------------------------------
# The marker convention
# ---------------------------------------------------------------------------

_MARKER_RE = re.compile(
    r"(my\s+solution|my\s+working|my\s+steps|mera\s+solution|"
    r"meri\s+solution|mera\s+hal|मेरा\s+हल|मेरा\s+solution|"
    r"मेरी\s+working|solution)\s*[:\-–—]\s*",
    re.I,
)

_QUESTION_TAIL_JUNK = re.compile(
    r"(?i)[\s,;]*(please\s+)?(check|galti\s+batao|check\s+karo)\s*$")


def _split_message(text):
    """(question, [working lines]) or None when the message is
    not a step-check request at all."""
    m = _MARKER_RE.search(str(text or ""))
    if not m:
        return None
    question = str(text)[:m.start()]
    work = str(text)[m.end():]
    question = _QUESTION_TAIL_JUNK.sub("", question.strip())
    question = re.sub(r"\s+", " ", question).strip(" :,-")
    if not question:
        return None
    lines = [ln.strip() for ln in work.splitlines()]
    lines = [ln for ln in lines if ln]
    if len(lines) < 2:
        # One physical line: steps may be chained with arrows
        # or semicolons instead of newlines.
        if lines:
            parts = re.split(r"→|->|;", lines[0])
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= 2:
                lines = parts
    if len(lines) < 2:
        return None
    return question, lines


# ---------------------------------------------------------------------------
# Feedback strings — kind teacher, in the question's flavour
# ---------------------------------------------------------------------------

_STR = {
    "en": {
        "checked": "I checked your solution step by step.",
        "first_wrong": "The very first step already goes wrong: "
                       "\"{line}\"",
        "upto": "Your steps are correct up to step {k}.",
        "wrong": "Step {k} is where it first goes wrong: \"{line}\"",
        "should": "That step should be: {s}",
        "not_follow": "That step does not follow from the step "
                      "before it — look at that line once more.",
        "full": "Here is the full correct solution:",
        "all_ok": "Every step is correct — very well done!",
        "diff_method": "Your method is different from mine, but "
                       "every step is valid and the answer is "
                       "right.",
        "incomplete": "Every step you have written is correct "
                      "so far, but the solution is not finished "
                      "yet.",
        "incomplete_root": "One more root is still missing.",
        "no_final": "I could not spot a final answer in your "
                    "steps, but every step you wrote checks out.",
        "oos": "I can't check steps for this type of question "
               "yet — but here is the correct solution:",
    },
    "roman": {
        "checked": "Maine tumhara solution step by step check kiya.",
        "first_wrong": "Pehla step hi galat ho gaya hai: \"{line}\"",
        "upto": "Step {k} tak tumhare saare step sahi hai.",
        "wrong": "Pehli galti step {k} par hai: \"{line}\"",
        "should": "Ye step aisa hona chahiye tha: {s}",
        "not_follow": "Ye step pichhle step se nahi banta — is "
                      "line ko ek baar phir dekho.",
        "full": "Ye raha poora sahi solution:",
        "all_ok": "Har step sahi hai — bahut badhiya!",
        "diff_method": "Tumhara tareeka mere tareeke se alag hai, "
                       "par har step sahi hai aur jawab bhi sahi "
                       "hai.",
        "incomplete": "Abhi tak ke saare step sahi hai, par "
                      "solution abhi poora nahi hua.",
        "incomplete_root": "Ek root abhi aur bacha hai.",
        "no_final": "Tumhare steps me final jawab saaf nahi mila, "
                    "par jo steps likhe hai wo sab sahi hai.",
        "oos": "Is type ke sawal ke steps main abhi check nahi "
               "kar sakta — par ye raha sahi solution:",
    },
    "dev": {
        "checked": "मैंने तुम्हारा हल ध्यान से जाँचा।",
        "first_wrong": "पहला चरण ही गलत हो गया है: \"{line}\"",
        "upto": "चरण {k} तक तुम्हारे सारे चरण सही हैं।",
        "wrong": "पहली गलती चरण {k} पर है: \"{line}\"",
        "should": "यह चरण ऐसा होना चाहिए था: {s}",
        "not_follow": "यह चरण पिछले चरण से नहीं बनता — इस पंक्ति "
                      "को एक बार फिर देखो।",
        "full": "यह रहा पूरा सही हल:",
        "all_ok": "हर चरण सही है — बहुत बढ़िया!",
        "diff_method": "तुम्हारा तरीका मेरे तरीके से अलग है, पर "
                       "हर चरण सही है और उत्तर भी सही है।",
        "incomplete": "अभी तक के सारे चरण सही हैं, पर हल अभी "
                      "पूरा नहीं हुआ।",
        "incomplete_root": "एक मूल (root) अभी और बचा है।",
        "no_final": "तुम्हारे चरणों में अंतिम उत्तर साफ़ नहीं "
                    "मिला, पर जो चरण लिखे हैं वे सब सही हैं।",
        "oos": "इस तरह के सवाल के चरण मैं अभी जाँच नहीं सकता — "
               "पर यह रहा सही हल:",
    },
}


def _result(ref, steps):
    """A step-check reply in the normal result shape, so every
    existing renderer (chat card, print, history) works as-is.
    op is deliberately not "error"/"simplify", so the display
    layer never treats it as a failure or as gibberish."""
    return {
        "type": "step_check",
        "op": "check_steps",
        "answer": ref.get("answer", ""),
        "steps": steps,
        "step_check": True,
        "fallback_kind": "step_check",
    }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _clean_line(line):
    t = str(line or "").strip().strip('"').strip()
    t = re.sub(r"(?i)^step\s*\d+\s*[:\.\)]\s*", "", t)
    t = re.sub(r"^चरण\s*\d+\s*[:\.\)]\s*", "", t)
    t = re.sub(r"^(=>|→|->)\s*", "", t)
    t = re.sub(r"(?i)^(ans|answer|उत्तर)\s*[:\-]\s*", "", t)
    return t.strip()


_FUNC_NAMES = ("sin", "cos", "tan", "cot", "sec", "csc", "sqrt",
               "log", "exp", "pi", "asin", "acos", "atan", "sinh",
               "cosh", "tanh", "abs")


def _maths_only(text):
    """True when every Latin letter-run in the text is a single
    letter (a variable) or a known function name. Without this
    guard SymPy parses ordinary words as letter products —
    "Solve 2x + 3" becomes S*o*l*v*e*2*x + 3 and poisons every
    extraction downstream."""
    t = str(text or "")
    for name in _FUNC_NAMES:
        t = re.sub(rf"\b{name}\b", " ", t)
    return all(len(run) <= 1 for run in re.findall(r"[A-Za-z]+", t))


def _try_parse(text):
    """Parse maths text to a SymPy Expr, or None. Relations,
    tuples and booleans are not expressions. A parse whose
    free symbols are not single ASCII letters is word soup
    (SymPy happily turns "11 हल करो" into 11*क*र*ल*ह*ो) and
    is rejected too."""
    if not _maths_only(text):
        return None
    try:
        e = parse_expression(text)
    except Exception:
        return None
    if not isinstance(e, sp.Expr):
        return None
    for s in e.free_symbols:
        if not (len(s.name) == 1 and s.name.isascii()
                and s.name.isalpha()):
            return None
    return e


def _trim_to_expr(text, from_left):
    """Longest token-trimmed slice of `text` that parses —
    pulls the maths out of "Solve the equation 2x + 3" /
    "11 hai to" style surroundings."""
    tokens = str(text or "").split()
    for k in range(len(tokens)):
        cand = " ".join(tokens[k:] if from_left
                        else tokens[:len(tokens) - k])
        e = _try_parse(cand)
        if e is not None:
            return e
    return None


def _extract_equation(text):
    """(lhs, rhs, var) for a single-variable equation inside
    the question text, or None."""
    if str(text).count("=") != 1:
        return None
    lhs_t, rhs_t = str(text).split("=", 1)
    lhs = _trim_to_expr(lhs_t, from_left=True)
    rhs = _trim_to_expr(rhs_t, from_left=False)
    if lhs is None or rhs is None:
        return None
    symbols = (lhs - rhs).free_symbols
    if len(symbols) != 1:
        return None
    return lhs, rhs, next(iter(symbols))


def _extract_expression(text):
    e = _try_parse(text)
    if e is not None:
        return e
    e = _trim_to_expr(text, from_left=True)
    if e is not None:
        return e
    return _trim_to_expr(text, from_left=False)


def _parse_eq_line(line):
    """(lhs, rhs) when the line is one clean equation."""
    if line.count("=") != 1:
        return None
    if any(s in line for s in (">=", "<=", "==", "!=")):
        return None
    l, r = line.split("=", 1)
    le, re_ = _try_parse(l), _try_parse(r)
    if le is None or re_ is None:
        return None
    return le, re_


# ---------------------------------------------------------------------------
# Equation-mode maths
# ---------------------------------------------------------------------------

def _proportional(d1, d2, var):
    """True iff d1 = c * d2 for a non-zero constant c — the
    invariant of every legal equation move."""
    d1, d2 = sp.expand(d1), sp.expand(d2)
    if d1 == 0 or d2 == 0:
        return False
    try:
        p1, p2 = sp.Poly(d1, var), sp.Poly(d2, var)
    except Exception:
        ratio = sp.simplify(d1 / d2)
        return ratio != 0 and var not in ratio.free_symbols
    a, b = p1.as_dict(), p2.as_dict()
    if set(a) != set(b):
        return False
    ratios = {sp.simplify(a[k] / b[k]) for k in b}
    return len(ratios) == 1 and ratios.pop() != 0


def _divides(big, small, var):
    """True iff `small` is a polynomial factor of `big`."""
    return _quotient(big, small, var) is not None


def _quotient(big, small, var):
    """big / small as a polynomial, or None when `small` is
    not a polynomial factor of `big`."""
    try:
        q, rem = sp.div(sp.Poly(sp.expand(big), var),
                        sp.Poly(sp.expand(small), var))
        if rem == 0:
            return q.as_expr()
    except Exception:
        pass
    return None


def _same_values(values, targets):
    """Set equality of sympy numbers, exactly where possible."""
    remaining = list(targets)
    for v in values:
        hit = None
        for t in remaining:
            try:
                if sp.simplify(v - t) == 0:
                    hit = t
                    break
            except Exception:
                continue
        if hit is None:
            return False
        remaining.remove(hit)
    return not remaining


def _suggest_eq(prev_lr, stu_lr, var):
    """The corrected version of a wrong equation step, when
    the student's own move can be inferred:

    * one side scaled by c != 1, the other untouched — they
      scaled one side only; complete the scaling.
    * one side shifted/untouched pairings that amount to a
      copy slip — restore the previous equation.
    * both sides changed — infer the move (shift or scale)
      from the lhs and apply it to the rhs; keep it only if
      the result is genuinely equivalent to the previous
      equation.
    Returns (lhs, rhs) or None."""
    pl, pr = prev_lr
    sl, sr = stu_lr

    def _shift(a_old, a_new):
        d = sp.expand(a_new - a_old)
        return d if d != 0 and var not in d.free_symbols else None

    def _scale(a_old, a_new):
        if a_old == 0:
            return None
        r = sp.simplify(a_new / a_old)
        if r != 0 and r != 1 and var not in r.free_symbols:
            return r
        return None

    lhs_same = sp.expand(sl - pl) == 0
    rhs_same = sp.expand(sr - pr) == 0
    if lhs_same and rhs_same:
        return None
    if lhs_same != rhs_same:
        # Exactly one side changed. A constant SHIFT of that
        # side (11 -> 12, 8 -> 9) is most often a copy slip —
        # the correction is the previous equation itself. A
        # SCALING (2x -> x) is a half-finished operation —
        # complete it on the other side. (Testing the ratio
        # first was a bug: 9/8 is a "constant ratio" too, and
        # produced nonsense like 9x/4 = 9.)
        old, new = (pr, sr) if lhs_same else (pl, sl)
        if _shift(old, new) is not None:
            return (pl, pr)
        c = _scale(old, new)
        if c is not None:
            if lhs_same:
                return (sp.expand(pl * c), sr)
            return (sl, sp.expand(pr * c))
        return (pl, pr)
    # Both sides changed: infer from the lhs.
    d = _shift(pl, sl)
    if d is not None:
        cand = (sl, sp.expand(pr + d))
        if _proportional(sp.expand(cand[0] - cand[1]),
                         sp.expand(pl - pr), var):
            return cand
    c = _scale(pl, sl)
    if c is not None:
        cand = (sl, sp.expand(pr * c))
        if _proportional(sp.expand(cand[0] - cand[1]),
                         sp.expand(pl - pr), var):
            return cand
    # ...or from the rhs.
    d = _shift(pr, sr)
    if d is not None:
        cand = (sp.expand(pl + d), sr)
        if _proportional(sp.expand(cand[0] - cand[1]),
                         sp.expand(pl - pr), var):
            return cand
    return None


def _degree(diff, var):
    try:
        return sp.Poly(sp.expand(diff), var).degree()
    except Exception:
        return 0


def _uses_factoring(lines):
    """A product of two parenthesised groups in a working
    line — the visible signature of the factoring method."""
    return any(re.search(r"\)\s*\(", _clean_line(ln))
               for ln in lines)


# ---------------------------------------------------------------------------
# Shared reply builders
# ---------------------------------------------------------------------------

def _mistake(ref, S, lineno, raw_line, suggestion):
    steps = [S["checked"]]
    if lineno <= 1:
        steps.append(S["first_wrong"].format(line=raw_line))
    else:
        steps.append(S["upto"].format(k=lineno - 1))
        steps.append(S["wrong"].format(k=lineno, line=raw_line))
    if suggestion:
        steps.append(S["should"].format(s=suggestion))
    else:
        steps.append(S["not_follow"])
    steps.append(S["full"])
    steps.extend(str(s) for s in ref.get("steps") or [])
    return _result(ref, steps)


def _all_correct(ref, S, different_method):
    steps = [S["checked"], S["all_ok"]]
    if different_method:
        steps.append(S["diff_method"])
    return _result(ref, steps)


def _incomplete(ref, S, root_missing=False, no_final=False):
    steps = [S["checked"], S["incomplete"]]
    if root_missing:
        steps.append(S["incomplete_root"])
    if no_final:
        steps.append(S["no_final"])
    steps.append(S["full"])
    steps.extend(str(s) for s in ref.get("steps") or [])
    return _result(ref, steps)


def _out_of_scope(ref, S):
    steps = [S["oos"]]
    steps.extend(str(s) for s in ref.get("steps") or [])
    return _result(ref, steps)


# ---------------------------------------------------------------------------
# Mode 1: equations (linear / quadratic)
# ---------------------------------------------------------------------------

def _check_equations(question, ref, lines, S):
    extracted = _extract_equation(question)
    if extracted is None:
        return _out_of_scope(ref, S)
    lhs0, rhs0, var = extracted
    d0 = sp.expand(lhs0 - rhs0)
    try:
        roots = sp.solve(d0, var)
    except Exception:
        return _out_of_scope(ref, S)
    if not roots or any(not r.is_number for r in roots):
        return _out_of_scope(ref, S)

    # The pool of equation "threads" the student has validly
    # established. A new equation step is legal when it is
    # PROPORTIONAL to a thread (an ordinary equivalent move)
    # or DIVIDES one (splitting a factored equation into a
    # factor branch — the sibling factor joins the pool, so
    # "x - 2 = 0 ... x = 2 ... x - 3 = 0 ... x = 3" checks
    # cleanly). The pool only ever holds states derived from
    # valid steps, so consulting it can never excuse a wrong
    # step: the first line that matches no thread is the
    # first mistake.
    pool = [d0]
    prev_lr = (lhs0, rhs0)
    final_roots = None
    final_line = None
    checkable = 0

    def _accept(d):
        """Validate diff d against the pool; on success add
        d (and a sibling factor, when d split one off)."""
        for b in list(pool):
            if _proportional(d, b, var):
                pool.append(d)
                return True
        if _degree(d, var) >= 1:
            for b in list(pool):
                q = _quotient(b, d, var)
                if q is not None:
                    pool.append(d)
                    if _degree(q, var) >= 1:
                        pool.append(sp.expand(q))
                    return True
        return False

    for lineno, raw in enumerate(lines, 1):
        line = _clean_line(raw)
        if not line:
            continue
        low = line.lower()
        # "x - 2 = 0 or x - 3 = 0" / "x = 2, x = 3" branch lines.
        parts = None
        if " or " in low or " या " in line:
            parts = re.split(r"\s+or\s+|\s+या\s+", line,
                             flags=re.I)
        elif line.count("=") >= 2 and "," in line:
            parts = [p.strip() for p in line.split(",")]
        if parts and len(parts) >= 2:
            parsed = [_parse_eq_line(p) for p in parts]
            if all(p is not None for p in parsed):
                diffs = [sp.expand(a - b) for a, b in parsed]
                if any(not d.free_symbols <= {var} for d in diffs):
                    continue  # foreign symbols: not ours to judge
                checkable += 1
                if not all(_accept(d) for d in diffs):
                    return _mistake(ref, S, lineno, raw, None)
                got = set()
                for d in diffs:
                    try:
                        got.update(sp.solve(d, var))
                    except Exception:
                        pass
                if got:
                    final_roots = (final_roots or set()) | got
                    final_line = lineno
                continue
        pe = _parse_eq_line(line)
        if pe is not None:
            d = sp.expand(pe[0] - pe[1])
            if d == 0:
                continue  # identity line ("8 = 8"): no information
            if not d.free_symbols <= {var}:
                continue  # foreign symbols: not ours to judge
            checkable += 1
            # An isolated "x = value" line is a root CLAIM: it
            # can be verified directly against the original
            # equation, whatever path the student took to it.
            iso = None
            for side, other in ((pe[0], pe[1]), (pe[1], pe[0])):
                if side == var and other.is_number:
                    iso = other
            if iso is not None:
                if any(sp.simplify(iso - r) == 0 for r in roots):
                    final_roots = (final_roots or set()) | {iso}
                    final_line = lineno
                    pool.append(sp.expand(var - iso))
                    prev_lr = pe
                    continue
                sugg_text = ", ".join(
                    f"{var} = {fmt_num(r)}" for r in roots)
                return _mistake(ref, S, lineno, raw, sugg_text)
            if _accept(d):
                prev_lr = pe
                continue
            sugg = _suggest_eq(prev_lr, pe, var)
            sugg_text = None
            if sugg is not None:
                sugg_text = f"{fmt(sugg[0])} = {fmt(sugg[1])}"
            return _mistake(ref, S, lineno, raw, sugg_text)
        # A bare number as a line claims the (single) root.
        val = _try_parse(line)
        if val is not None and val.is_number \
                and not re.search(r"[a-zA-Z]", line):
            checkable += 1
            if any(sp.simplify(val - r) == 0 for r in roots):
                final_roots = {val}
                final_line = lineno
                continue
            sugg_text = None
            if len(roots) == 1:
                sugg_text = f"{var} = {fmt_num(roots[0])}"
            return _mistake(ref, S, lineno, raw, sugg_text)
        # Anything else (labels, prose, annotations): skipped.

    if checkable == 0:
        return None
    if final_roots is not None:
        if _same_values(final_roots, roots):
            ref_factoring = any(
                re.search(r"\)\s*\(", str(s))
                for s in ref.get("steps") or [])
            different = _uses_factoring(lines) and not ref_factoring
            return _all_correct(ref, S, different)
        if len(final_roots) < len(roots):
            return _incomplete(ref, S, root_missing=True)
        return _mistake(ref, S, final_line or len(lines),
                        lines[(final_line or 1) - 1], None)
    return _incomplete(ref, S)


# ---------------------------------------------------------------------------
# Mode 2: simplify / expand expression chains
# ---------------------------------------------------------------------------

def _check_expressions(question, ref, lines, S):
    e0 = _extract_expression(question)
    if e0 is None or "=" in str(question):
        return _out_of_scope(ref, S)
    ref_expr = _try_parse(str(ref.get("answer", "")).replace("·", "*"))
    if ref_expr is None:
        return _out_of_scope(ref, S)

    prev = e0
    checkable = 0
    for lineno, raw in enumerate(lines, 1):
        line = _clean_line(raw)
        if not line:
            continue
        if line.count("=") == 1:
            # A claim line: "3(x + 2) = 3x + 6". The claim
            # itself must be true. It moves the working state
            # only when one side IS the current expression —
            # a claim about a sub-expression ("3(x + 2) = 3x
            # + 6" inside a longer simplify) is a side note
            # and leaves the state alone, so a valid partial
            # step is never accused.
            l, r = line.split("=", 1)
            le, re_ = _try_parse(l), _try_parse(r)
            if le is None or re_ is None:
                continue
            checkable += 1
            if sp.simplify(le - re_) != 0:
                sugg = f"{fmt(le)} = {fmt(sp.expand(le))}"
                return _mistake(ref, S, lineno, raw, sugg)
            if sp.simplify(le - prev) == 0:
                prev = re_
            elif sp.simplify(re_ - prev) == 0:
                prev = le
            continue
        if "=" in line:
            continue
        e = _try_parse(line)
        if e is None:
            continue
        checkable += 1
        if sp.simplify(e - prev) == 0:
            prev = e
            continue
        sugg = fmt(sp.simplify(prev))
        return _mistake(ref, S, lineno, raw, sugg)
    if checkable == 0:
        return None
    if sp.simplify(prev - ref_expr) == 0:
        return _all_correct(ref, S, False)
    return _incomplete(ref, S)


# ---------------------------------------------------------------------------
# Mode 3: numeric claims (arithmetic, percentages, applied)
# ---------------------------------------------------------------------------

def _pct(text):
    """Make percent text parseable: "15% of 800" -> ((15/100)*800),
    a bare "15%" -> (15/100); currency words removed."""
    t = str(text or "")
    t = t.replace("₹", " ")
    t = re.sub(r"\bRs\.?\b", " ", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)",
               r"((\1/100)*\2)", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*%", r"(\1/100)", t)
    return t


_UNITS = {"cm", "mm", "km", "m", "kg", "g", "mg", "l", "ml",
          "hr", "hrs", "hour", "hours", "min", "mins", "sec",
          "secs", "rupees", "metre", "metres", "meter", "meters",
          "litre", "litres", "percent", "paise", "years", "days"}


def _seg_value(seg):
    """The numeric value of one '='-segment, or None when the
    segment is a label, prose, or symbolic."""
    s = str(seg or "").strip()
    if not s or not any(ch.isdigit() for ch in s):
        return None
    cands = [s]
    # A trailing UNIT word may be dropped ("120 cm" -> 120) —
    # but only a known unit: trimming any trailing letters
    # turned "2x" into the bogus value 2.
    m = re.match(r"^(.*?)\s*([a-zA-Z]+)$", s)
    if m and m.group(2).lower() in _UNITS and m.group(1).strip():
        cands.append(m.group(1).strip())
    trimmed2 = re.sub(r"^[a-zA-Z\s]+?(?=[\d(])", "", s).strip()
    if trimmed2 and trimmed2 != s:
        cands.append(trimmed2)
    for cand in cands:
        e = _try_parse(cand)
        if e is not None and e.is_number and not e.free_symbols:
            try:
                v = sp.nsimplify(e, rational=True)
            except Exception:
                v = e
            if isinstance(v, sp.Rational) and v.q > 10 ** 6:
                return float(e)
            return v
    return None


def _num_eq(a, b):
    try:
        if sp.simplify(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(a)))
    except Exception:
        return False


def _ref_number(answer):
    """The numeric value inside a reference answer ("Rs 680",
    "120", "20%"), or None."""
    t = _pct(answer)
    m = re.search(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?", t)
    if not m:
        return None
    e = _try_parse(m.group(0))
    if e is None or not e.is_number:
        return None
    try:
        return sp.nsimplify(e, rational=True)
    except Exception:
        return e


def _check_claims(question, ref, lines, S):
    ref_val = _ref_number(ref.get("answer", ""))
    if ref_val is None:
        return _out_of_scope(ref, S)
    checkable = 0
    final_val = None
    final_line = None
    final_raw = None
    for lineno, raw in enumerate(lines, 1):
        line = _clean_line(raw)
        if not line:
            continue
        if "=" in line:
            disp_segs = [s.strip() for s in line.split("=")]
            vals = [_seg_value(_pct(s)) for s in disp_segs]
            if any(v is not None for v in vals):
                checkable += 1
            prev_val = None
            prev_idx = None
            bad = None
            for i, v in enumerate(vals):
                if v is None:
                    continue
                if prev_val is not None and not _num_eq(prev_val, v):
                    bad = (prev_idx, prev_val)
                    break
                prev_val, prev_idx = v, i
            if bad is not None:
                p_idx, p_val = bad
                sugg = f"{disp_segs[p_idx]} = {fmt_num(p_val)}"
                return _mistake(ref, S, lineno, raw, sugg)
            nums = [v for v in vals if v is not None]
            if nums:
                final_val = nums[-1]
                final_line = lineno
                final_raw = raw
            continue
        v = _seg_value(_pct(line))
        if v is not None:
            checkable += 1
            final_val = v
            final_line = lineno
            final_raw = raw
    if checkable == 0:
        return None
    if final_val is None:
        return _incomplete(ref, S, no_final=True)
    if _num_eq(final_val, ref_val):
        return _all_correct(ref, S, False)
    segs = [s.strip() for s in _clean_line(final_raw).split("=")]
    if len(segs) >= 2:
        sugg = " = ".join(segs[:-1] + [fmt_num(ref_val)])
    else:
        sugg = fmt_num(ref_val)
    return _mistake(ref, S, final_line, final_raw, sugg)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

_SIMPLIFY_OPS = {"simplify", "expand", "factor", "factorise",
                 "factorize", "collect"}


def _scope_of(ref):
    rtype = ref.get("type", "")
    rop = ref.get("op", "")
    # Equation questions wear several op names: the algebra
    # solver's "equation" and applied.py's wrapped-equation
    # ops ("hindi_equation", "hinglish_equation"). Word
    # equations and differential equations stay out of v1.
    if rop == "equation" or (rop.endswith("_equation")
                             and "word" not in rop
                             and "differential" not in rop):
        return "eq"
    if rtype == "algebra" and rop in _SIMPLIFY_OPS:
        return "expr"
    if rtype in ("arithmetic", "applied", "word_problem"):
        return "claims"
    return None


def step_check_result(question, lang=None, flavour_hint=None):
    """The step-check reply for a chat message, or None when
    the message is not a checkable step-check request (the
    caller then runs the completely normal solve flow).

    Wave 129: ``flavour_hint`` lets the two-turn chat flow
    (galti.py) keep the reply in the flavour of the student's
    ORIGINAL intent message — the steps message on its own is
    bare maths and carries no language signal. Default None
    keeps the Wave 85 behaviour byte-for-byte."""
    split = _split_message(question)
    if split is None:
        return None
    q_text, lines = split
    ref = solve_question(q_text)
    if solve_failed(q_text, ref) or not str(ref.get("answer", "")).strip():
        return None
    # A letter-soup "solve" (the app's known failure shape on
    # some phrasings) is not a reference solution — never
    # present it as the correct working. Returning None lets
    # the normal fallback layer handle the message instead.
    from fallback import _is_junk
    if _is_junk(q_text, ref):
        return None
    scope = _scope_of(ref)
    flavour = flavour_hint or _flavour(question)
    S = _STR.get(flavour, _STR["en"])
    if scope is None:
        return _out_of_scope(ref, S)
    if scope == "eq":
        return _check_equations(q_text, ref, lines, S)
    if scope == "expr":
        return _check_expressions(q_text, ref, lines, S)
    return _check_claims(q_text, ref, lines, S)
