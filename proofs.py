"""Wave 95: proof questions ("prove that ..."), handled honestly.

Three tiers, in order:

1. VERIFIABLE IDENTITIES. The statement after the proof phrase
   must be a single equation whose two sides parse as maths
   (a strict shape guard keeps prose out). The identity is
   verified with SymPy (simplify / trigsimp / expand_log on
   LHS - RHS). Only when SymPy confirms it do we answer, with
   a derivation built from the actual transformation path
   (expand / expand_trig / trigsimp / factor / cancel / log
   rules) that takes LHS to RHS. If SymPy cannot verify, this
   layer returns None — a false or unprovable "identity" is
   NEVER dressed up as a proof, and the existing behaviour
   (e.g. the trig solver's own "Not an identity") stands.

2. TEXTBOOK PROOFS. Irrationality of sqrt(2), sqrt(3), sqrt(5):
   the standard contradiction proof, served verbatim from
   proofs_data.py in the question's language (English / Hindi;
   Hinglish asks get the English text — see wave notes).

3. Everything else returns None: geometry proofs, general
   theorems and anything unparseable fall through to the
   existing chain untouched.

Detection is deliberately tight: an explicit proof phrase
("prove", "show that", "verify that", सिद्ध, साबित कर,
"siddh karo", "prove karo") is required. Ordinary questions
that merely contain the word "that" never reach this layer.

Result dicts follow the house shape (type / op / answer /
steps) with fallback_kind == "proof" and source == "proofs",
so no renderer changes are needed and the AI-upgrade layer
(which keys on other kinds) never rewrites a proof.
"""
import re

import sympy as sp

from solver.expression_parser import parse_expression
from proofs_data import PROOFS

# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

_PROOF_PHRASE = re.compile(
    r"\bprove\b"
    r"|\bshow\s+that\b"
    r"|\bverify\s+that\b"
    r"|सिद्ध"
    r"|साबित\s*कर"
    r"|\bsiddh\b"
    r"|\bsa{1,2}bit\s+kar\b",
    re.IGNORECASE,
)

# Connectors / filler verbs that may sit between the phrase
# and the statement ("prove karo ki X", "सिद्ध करो कि X").
_CONNECTOR = re.compile(
    r"^\s*(?:that|karo|ki|कि|kro|kar|करो|कीजिए|करें|ke)"
    r"(?=\s|$)\s*",
    re.IGNORECASE)

_FUNCS = ("sin", "cos", "tan", "cot", "sec", "csc", "log")

_GREEK = (("theta", "u", "θ"), ("alpha", "v", "α"),
          ("beta", "w", "β"), ("gamma", "z", "γ"))


def _has_proof_intent(question):
    return bool(_PROOF_PHRASE.search(str(question or "")))


def _statement(question):
    """The question with every proof phrase (and a leading
    connector) removed — the bare statement to prove."""
    text = _PROOF_PHRASE.sub(" ", str(question or ""))
    text = text.strip()
    while True:
        stripped = _CONNECTOR.sub("", text)
        if stripped == text:
            break
        text = stripped
    # A connector can also survive mid-text ("prove karo ki X"):
    # phrase removal leaves "ki X", handled above; a trailing
    # full stop is punctuation, not maths.
    return text.strip().rstrip(".").strip()


# ---------------------------------------------------------------------------
# Tier 2: textbook irrationality proofs
# ---------------------------------------------------------------------------

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_ROOT_RE = re.compile(
    r"(?:√|sqrt|root|वर्गमूल)\s*\(?\s*(\d+)")


def _irrationality_result(question, hindi):
    q = str(question or "")
    qn = q.translate(_DEV_DIGITS)
    radicands = set(_ROOT_RE.findall(qn))
    if len(radicands) != 1:
        return None
    n = radicands.pop()
    entry = PROOFS.get(n)
    if entry is None:
        return None
    low = qn.lower()
    if not ("irrational" in low or "अपरिमेय" in q
            or "aparimey" in low):
        return None
    lang = "hi" if hindi else "en"
    statement = entry["statement"][lang]
    return {
        "type": "Proof",
        "op": "proof_irrational",
        "answer": statement + (" — सिद्ध हुआ ✔" if hindi
                               else " — proved ✔"),
        "steps": list(entry["steps"][lang]),
        "fallback": True,
        "fallback_kind": "proof",
        "source": "proofs",
        "verified": True,
    }


# ---------------------------------------------------------------------------
# Tier 1: SymPy-verified identities
# ---------------------------------------------------------------------------

def _clean_for_parse(text):
    """Prepare one side of the identity for parse_expression.

    Returns (cleaned_text, display_subs, used_degrees) or None
    when the text is prose, not maths (the shape guard).

    The app parser mishandles bare function products —
    "2 sin A cos A" became sin(A·cos(A)) — so function
    applications are parenthesised explicitly here first:
    sin^2 A -> (sin(A))^2, sin 2A -> sin(2*A), sin A -> sin(A),
    sin 30 -> sin(30*pi/180) (school identities are in degrees).
    """
    t = " " + str(text or "").strip() + " "
    subs = {}
    # Greek: symbols and names -> placeholder letters (as the
    # trig solver does), remembering how to display them back.
    for name, letter, symbol in _GREEK:
        if symbol in t:
            t = t.replace(symbol, f" {letter} ")
            subs[letter] = symbol
        elif re.search(rf"\b{name}\b", t, flags=re.I):
            t = re.sub(rf"\b{name}\b", letter, t, flags=re.I)
            subs[letter] = name
    t = re.sub(r"\bcosec\b", "csc", t, flags=re.I)
    t = t.replace("√", "sqrt").replace("−", "-").replace("×", "*")

    degrees = False

    def _pow(m):
        arg = m.group(3)
        if arg.isdigit():
            # sin^2 30: the numeric angle is in degrees.
            return f"({m.group(1)}({arg}*pi/180))^{m.group(2)}"
        return f"({m.group(1)}({arg}))^{m.group(2)}"

    # sin^2 A / sin^2 30 (before the bare passes below)
    t = re.sub(r"\b(sin|cos|tan|cot|sec|csc)\s*\^\s*(\d+)\s+"
               r"([A-Za-z]|\d+)", _pow, t)
    # sin 2A -> sin(2*A)
    t = re.sub(r"\b(sin|cos|tan)\s+2\s*([A-Za-z])\b",
               r"\1(2*\2)", t)
    # sin 30 -> sin(30*pi/180): numeric args are degrees
    def _num(m):
        nonlocal degrees
        degrees = True
        return f"{m.group(1)}({m.group(2)}*pi/180)"
    t = re.sub(r"\b(sin|cos|tan|cot|sec|csc)\s+(\d+(?:\.\d+)?)\b",
               _num, t)
    # sin A -> sin(A); log a -> log(a)
    t = re.sub(r"\b(sin|cos|tan|cot|sec|csc|log)\s+([A-Za-z])\b",
               r"\1(\2)", t)
    t = re.sub(r"\blog\s+(\d+(?:\.\d+)?)\b", r"log(\1)", t)

    # Shape guard: after removing function names, any remaining
    # long word is prose ("solution", "angles", "degrees",
    # Devanagari text) — not an identity side. Two-letter
    # products (ab, xy) are maths, so only a small stoplist of
    # two-letter prose words is rejected at that length.
    residual = t
    for fn in _FUNCS + ("sqrt", "pi", "exp"):
        residual = re.sub(rf"\b{fn}\b", " ", residual)
    if any("ऀ" <= ch <= "ॿ" for ch in residual):
        return None
    if re.search(r"[A-Za-z]{3,}", residual):
        return None
    if re.search(r"\b(is|of|to|an|be|in|on|or|if|so|no|by)\b",
                 residual):
        return None
    if not re.search(r"[A-Za-z0-9]", residual):
        return None
    return t.strip(), subs, degrees


def _disp(expr, subs):
    """House-style display: ^ for powers, · for products,
    placeholders back to the student's own Greek letters."""
    if subs:
        expr = expr.subs({sp.Symbol(k): sp.Symbol(v)
                          for k, v in subs.items()})
    s = sp.sstr(expr)
    # cos(A)^(-2) reads as 1/cos(A)^2 in school books.
    s = re.sub(r"([A-Za-z]+\([^()]*\)|[A-Za-z])\*\*\(-(\d+)\)",
               r"1/\1^\2", s)
    s = s.replace("**", "^").replace("*", "·")
    s = s.replace("pi", "π").replace("csc(", "cosec(")
    s = s.replace("sqrt", "√")
    return s


def _verified(lhs, rhs):
    """True only when SymPy proves LHS == RHS."""
    try:
        if sp.simplify(lhs - rhs) == 0:
            return True
    except Exception:
        pass
    try:
        if sp.trigsimp(lhs - rhs) == 0:
            return True
    except Exception:
        pass
    try:
        if sp.simplify(sp.expand_log(lhs, force=True)
                       - sp.expand_log(rhs, force=True)) == 0:
            return True
    except Exception:
        pass
    try:
        return sp.fu(lhs - rhs) == 0
    except Exception:
        return False


_LABELS = {
    "expand": ("expanding", "विस्तार करने पर"),
    "expand_trig": ("expanding the double-angle formula",
                    "द्वि-कोण सूत्र से"),
    "rewrite_sincos": ("writing in sin and cos",
                       "sin और cos में लिखने पर"),
    "pythag": ("using sin²x + cos²x = 1",
               "sin²x + cos²x = 1 से"),
    "trigsimp": ("simplifying", "सरल करने पर"),
    "simplify": ("simplifying", "सरल करने पर"),
    "factor": ("factorising", "गुणनखंड करने पर"),
    "cancel": ("simplifying", "सरल करने पर"),
    "expand_log": ("using the log rules", "log नियम से"),
}


def _pythagoras(e):
    """One textbook step: replace sin²t by 1 - cos²t (or the
    mirror) wherever a squared trig term appears, then tidy.
    This is the move school proofs actually make — trigsimp
    instead folds 2 sin t cos t into sin 2t, which reads as a
    step backwards when the target keeps 2 sin t cos t."""
    args = {a.args[0] for a in e.atoms(sp.sin, sp.cos) if a.args}
    for t in args:
        for f, g in ((sp.sin, sp.cos), (sp.cos, sp.sin)):
            if e.has(f(t) ** 2):
                # NOT sp.simplify: it folds 2 sin t cos t into
                # sin 2t. together + cancel only merges the
                # fractions and lets the -g² + g² pair cancel.
                out = sp.cancel(sp.together(
                    e.subs(f(t) ** 2, 1 - g(t) ** 2)))
                if out != e:
                    return out
    return e


def _sincos(e):
    """Write tan / cot / sec / cosec in sin and cos, by direct
    substitution. (SymPy's own rewrite() is unusable here: it
    turned sin A into cos(A - pi/2) and left sec A untouched.)"""
    e = e.replace(lambda x: isinstance(x, sp.tan),
                  lambda x: sp.sin(x.args[0]) / sp.cos(x.args[0]))
    e = e.replace(lambda x: isinstance(x, sp.cot),
                  lambda x: sp.cos(x.args[0]) / sp.sin(x.args[0]))
    e = e.replace(lambda x: isinstance(x, sp.sec),
                  lambda x: 1 / sp.cos(x.args[0]))
    e = e.replace(lambda x: isinstance(x, sp.csc),
                  lambda x: 1 / sp.sin(x.args[0]))
    return e


def _double_angles(e):
    out = set()
    for a in e.atoms(sp.sin, sp.cos, sp.tan):
        arg = a.args[0]
        if arg.is_Mul and sp.Integer(2) in arg.args:
            out.add(a.func)
    return out


def _transform_path(lhs, rhs, has_trig, has_log):
    """Walk LHS toward RHS with real SymPy transforms.

    Returns a list of (label_key, expression) for each distinct
    new form, ending at RHS — or None when no honest path is
    found (the caller then uses the LHS − RHS display, which
    is still the actual verification, never an invented step).
    """
    transforms = [("expand", lambda e: sp.expand(e))]
    if has_trig:
        # expand_trig only when a double angle is actually
        # present — otherwise it "expands" sec² into cos^-2
        # under a double-angle label, which is the wrong story.
        if _double_angles(lhs) | _double_angles(rhs):
            transforms.append(("expand_trig",
                               lambda e: sp.expand_trig(e)))
        transforms.append(("rewrite_sincos", _sincos))
    transforms.append(("factor", lambda e: sp.factor(e)))
    transforms.append(("cancel", lambda e: sp.cancel(e)))
    if has_trig:
        transforms.append(("pythag", _pythagoras))
        transforms.append(("trigsimp",
                           lambda e: sp.trigsimp(e)))
    if has_log:
        transforms.append(("expand_log",
                           lambda e: sp.expand_log(e, force=True)))
    transforms.append(("simplify", lambda e: sp.simplify(e)))

    # A transform that INVENTS a double angle the question
    # never had (trigsimp folding 2 sin A cos A into sin 2A)
    # reads as a step backwards — skip such results.
    allowed_doubles = _double_angles(lhs) | _double_angles(rhs)

    seen = {lhs}
    path = []
    cur = lhs
    for key, fn in transforms:
        if cur == rhs:
            break
        try:
            nxt = fn(cur)
        except Exception:
            continue
        if nxt == cur or nxt in seen:
            continue
        if _double_angles(nxt) - allowed_doubles:
            continue
        seen.add(nxt)
        path.append((key, nxt))
        cur = nxt
        if len(path) > 6:
            return None
    if cur == rhs:
        return path
    # Meeting in the middle: transform RHS the same way.
    # expand_trig is skipped here — it rewrites sec² as
    # cos(A)^(-2), which is the same form but the wrong story
    # for a "RHS = ..." line.
    for key, fn in transforms:
        if key == "expand_trig":
            continue
        try:
            rform = fn(rhs)
        except Exception:
            continue
        if rform == cur and rform != rhs:
            path.append((key + "_rhs", rform))
            return path
    return None


def _identity_result(question, hindi):
    stmt = _statement(question)
    if stmt.count("=") != 1 or len(stmt) > 140:
        return None
    left_text, right_text = (s.strip() for s in stmt.split("=", 1))
    if not left_text or not right_text:
        return None
    cleaned_l = _clean_for_parse(left_text)
    cleaned_r = _clean_for_parse(right_text)
    if cleaned_l is None or cleaned_r is None:
        return None
    subs = dict(cleaned_l[1])
    subs.update(cleaned_r[1])
    try:
        lhs = parse_expression(cleaned_l[0])
        rhs = parse_expression(cleaned_r[0])
    except Exception:
        return None
    if not isinstance(lhs, sp.Expr) or not isinstance(rhs, sp.Expr):
        return None
    if len(lhs.free_symbols | rhs.free_symbols) > 4:
        return None
    if not _verified(lhs, rhs):
        return None

    has_trig = any(fn in stmt for fn in
                   ("sin", "cos", "tan", "cot", "sec", "csc"))
    has_log = "log" in stmt
    li = 1 if hindi else 0
    # The framing lines echo the student's own statement text;
    # only the intermediate forms come from SymPy.
    steps = [f"LHS = {left_text}"]
    path = _transform_path(lhs, rhs, has_trig, has_log)
    if path is not None and not path:
        # Already equal at parse time (a numeric identity like
        # sin^2 30 + cos^2 30, whose values the parser knows).
        steps.append(f"= {_disp(rhs, subs)}  "
                     f"({_LABELS['simplify'][li]})")
    elif path:
        for key, form in path:
            base = key.replace("_rhs", "")
            label = _LABELS.get(base, _LABELS["simplify"])[li]
            if key.endswith("_rhs"):
                steps.append(f"RHS = {right_text} = "
                             f"{_disp(form, subs)}  ({label})")
            else:
                steps.append(f"= {_disp(form, subs)}  ({label})")
    else:
        # No clean one-sided path: show the verification itself
        # (LHS - RHS simplifies to 0) — true, but labelled as a
        # check, not dressed as a textbook derivation.
        steps.append(f"LHS - RHS = {left_text} - ({right_text})")
        steps.append(("सरल करने पर LHS - RHS = 0"
                      if hindi else
                      "Simplifying, LHS - RHS = 0"))
    steps.append("= RHS")
    statement_disp = f"{left_text} = {right_text}"
    return {
        "type": "Proof",
        "op": "proof_identity",
        "answer": statement_disp + (" — सिद्ध हुआ ✔ (identity proved)"
                                    if hindi else
                                    " — identity proved ✔"),
        "steps": steps,
        "fallback": True,
        "fallback_kind": "proof",
        "source": "proofs",
        "verified": True,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def proof_result(question, hindi=False):
    """The Wave 95 proof answer for `question`, or None.

    None means: not a proof ask, or a proof ask this wave
    cannot honestly answer — the caller's chain runs exactly
    as before.

    Language follows the question's SCRIPT (the app's
    auto-match rule): a Devanagari question gets the Hindi
    proof text and labels; a Roman question — English or
    Hinglish — gets English. (The caller's `hindi` flag is
    marker-based and fires for Roman Hinglish too, which
    would have served a Devanagari proof to a student who
    typed in Roman letters.)"""
    if not question or not _has_proof_intent(question):
        return None
    hindi = any("ऀ" <= ch <= "ॿ" for ch in str(question))
    try:
        result = _irrationality_result(question, hindi)
        if result is not None:
            return result
        return _identity_result(question, hindi)
    except Exception:
        return None


__all__ = ["proof_result"]
