"""Wave 188: probability in WORD dress + the probability-
distribution mean/variance WRONG-SERVE fix (form-audit
top-10 item #3; audit rows 13, 14 and 31; spot-check
probes 20, 21, 22, 30).

Why this module exists (measured on main, Deploy-46 state):

- Probe 20: "Compute P(A|B), if P(B) = 0.5 and P(A
  intersection B) = 0.32" fell to the statistics guide
  (op "unknown").  The SYMBOLIC dress ("P(A∩B)") solves
  via depth125's relations family; the gap was purely the
  wording layer — "intersection" / "union" / "not A" /
  "A but not B" spelled out inside P(...).
- Probe 21: the NCERT Ex 13.3 hosteller / day-scholar
  Bayes problem, stated entirely in prose percentages,
  also fell to the statistics guide.  depth125's Bayes
  covers the E1/E2 formula dress and one factory dress;
  the sentence dresses (residence groups, factories /
  machines with % shares, bags with ball counts) had no
  schema.
- Probe 22 (WRONG SERVE, the priority): "A random
  variable X has the following probability distribution:
  X = 0, 1, 2 with P(X) = 0.2, 0.5, 0.3. Find the mean
  of X" was served **1** — statistics' PLAIN mean of the
  values 0, 1, 2 — instead of Σx·P(x) = **1.1**.  The
  variance dress was likewise served the plain variance
  of the value list (0.452222 instead of 0.49).
  tierA169's distribution family covers the TABLE dress
  and explicitly declines mean/variance asks; the
  sentence dress was hijacked by plain-mean.  A
  correctness bug under the 101% rule, not just a gap.

Design, in the house style of Waves 169/171/175/187:
every schema fires only when it settles the question
COMPLETELY with exact rational arithmetic (Fractions
throughout; decimals parsed exactly).  A prose Bayes
variant that cannot be parsed with certainty declines
(None) — numbers are never guessed.  Distribution
probabilities must sum to exactly 1 or the schema
declines.

Wiring (router.py, after the Wave 175 gate):
- solve_probwords188 behind the failure-only gate —
  probes 20/21 (primary op "unknown") and any other
  failure on these dresses.
- repair_probwords188 as a Wave 171-style repair block:
  the primary statistics result is a REAL answer
  (op mean / variance / std), so the failure gate never
  fires; the repair runs this module's distribution
  schema and displaces ONLY when the schema's parse is
  certain AND its value for the asked quantity provably
  differs from the served value (or the serve is a
  fragment of a combined mean+variance ask).  A correct
  primary answer is never displaced.
"""
import re
from fractions import Fraction

import sympy as sp

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")

_NUM = r"\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"


def _prep(q):
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    return s


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


def _num_str(fr):
    """Fraction -> clean student-facing number: integers
    plain, terminating decimals as decimals (1.1, 0.49),
    other rationals as 'a/b ≈ d.dddd'."""
    fr = Fraction(fr)
    if fr.denominator == 1:
        return str(fr.numerator)
    d = fr.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    if d == 1:
        return f"{float(fr):.10f}".rstrip("0").rstrip(".")
    return f"{_frac(fr)} ≈ {float(fr):.4f}"


def _step_num(fr):
    """Step-display number: terminating decimals as
    decimals (0.2), other rationals as plain fractions
    (1/6) — never an '≈' inside a sum."""
    fr = Fraction(fr)
    d = fr.denominator
    for p in (2, 5):
        while d % p == 0:
            d //= p
    if d == 1:
        return _num_str(fr)
    return _frac(fr)


def _pfrac(text):
    text = str(text).replace(" ", "")
    if "/" in text:
        a, b = text.split("/", 1)
        return Fraction(a) / Fraction(b)
    return Fraction(text)


# ===========================================================================
# (a) Word-dress probability relations
# ===========================================================================
#
# Normalise every P(...) span: spelled-out set words become
# the symbols depth125's relations family computes with
# ("intersection" -> ∩, "union"/"or" -> ∪, "and" -> ∩,
# "not A" / "A complement" / "A'" -> A′,
# "A but not B" -> A∩B′).  The given-data sentences use the
# same P(...) dress, so one normalisation covers givens
# and the ask.  The computation itself is the (P(A), P(B),
# P(A∩B)) triangle: every compound target over A, B and
# complements is derivable from those three, conditionals
# from the intersection, exactly as in the textbook.

_PVAL = re.compile(
    r"P\(\s*([^)]*?)\s*\)\s*=\s*"
    r"(\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)")


def _norm_span(inner):
    s = str(inner).strip()
    s = s.replace("'", "′").replace("’", "′").replace("`", "′")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\b([AB])\s+but\s+not\s+([AB])\b",
               r"\1∩\2′", s, flags=re.I)
    s = re.sub(r"\bnot\s+([AB])\s+and\s+not\s+([AB])\b",
               r"\1′∩\2′", s, flags=re.I)
    s = re.sub(r"\bnot\s+([AB])\s+or\s+not\s+([AB])\b",
               r"\1′∪\2′", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+and\s+not\s+([AB])\b",
               r"\1∩\2′", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+or\s+not\s+([AB])\b",
               r"\1∪\2′", s, flags=re.I)
    s = re.sub(r"\bnot\s+([AB])\b", r"\1′", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+intersection\s+([AB])\b",
               r"\1∩\2", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+union\s+([AB])\b",
               r"\1∪\2", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+and\s+([AB])\b",
               r"\1∩\2", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+or\s+([AB])\b",
               r"\1∪\2", s, flags=re.I)
    s = re.sub(r"\b([AB])\s+complement\b", r"\1′", s,
               flags=re.I)
    return s.replace(" ", "").upper()


def _normalise_p_spans(q):
    return re.sub(r"P\(\s*([^)]*?)\s*\)",
                  lambda m: "P(" + _norm_span(m.group(1)) + ")",
                  q)


def _word_relations(q):
    qn = _normalise_p_spans(q)
    if qn == q and "′" not in q and "∩" not in q \
            and "∪" not in q:
        return None          # nothing this layer adds
    ql = qn.lower()
    assigns = {}
    for m in _PVAL.finditer(qn):
        key = re.sub(r"\s+", "", m.group(1))
        try:
            val = _pfrac(m.group(2))
        except Exception:
            return None
        if qn[m.end():m.end() + 1] == "%":
            val = val / 100
        assigns[key] = val
    if not assigns:
        return None
    targets = []
    for m in re.finditer(r"P\(\s*([^)]*?)\s*\)", qn):
        if _PVAL.match(qn, m.start()):
            continue
        targets.append(re.sub(r"\s+", "", m.group(1)))
    if not targets:
        return None
    target = targets[-1]

    given_ind = bool(re.search(
        r"independent events?\s+with|are independent|"
        r"swatantra (hai|hain)|स्वतंत्र (है|हैं)", ql))
    given_mut = bool(re.search(
        r"mutually exclusive|paraspar apvarji|परस्पर अपवर्जी",
        ql))

    pa, pb = assigns.get("A"), assigns.get("B")
    pacb, pbca = assigns.get("A|B"), assigns.get("B|A")
    paub_g = assigns.get("A∪B")

    # The intersection, by whichever route the givens allow.
    inter = assigns.get("A∩B")
    inter_how = None
    if inter is not None:
        inter_how = "given"
    elif pacb is not None and pb is not None:
        inter = pacb * pb
        inter_how = "cond_b"
    elif pbca is not None and pa is not None:
        inter = pbca * pa
        inter_how = "cond_a"
    elif paub_g is not None and pa is not None \
            and pb is not None:
        inter = pa + pb - paub_g
        inter_how = "union"
    elif given_ind and pa is not None and pb is not None:
        inter = pa * pb
        inter_how = "independent"
    elif given_mut:
        inter = Fraction(0)
        inter_how = "mutual"

    def res(fr, steps):
        return _mk("statistics", "probability", _prob_str(fr),
                   steps)

    def inter_steps():
        """Steps that establish P(A ∩ B), when the target
        needs it and it was not directly given."""
        if inter_how == "cond_b":
            return ["From the definition of conditional "
                    "probability, P(A ∩ B) = P(A|B) × P(B) "
                    f"= {_frac(pacb)} × {_frac(pb)} "
                    f"= {_frac(inter)}."]
        if inter_how == "cond_a":
            return ["From the definition of conditional "
                    "probability, P(A ∩ B) = P(B|A) × P(A) "
                    f"= {_frac(pbca)} × {_frac(pa)} "
                    f"= {_frac(inter)}."]
        if inter_how == "union":
            return ["From the addition rule, P(A ∩ B) = "
                    "P(A) + P(B) − P(A ∪ B) "
                    f"= {_frac(pa)} + {_frac(pb)} − "
                    f"{_frac(paub_g)} = {_frac(inter)}."]
        if inter_how == "independent":
            return ["A and B are independent, so "
                    "P(A ∩ B) = P(A) × P(B) "
                    f"= {_frac(pa)} × {_frac(pb)} "
                    f"= {_frac(inter)}."]
        if inter_how == "mutual":
            return ["A and B are mutually exclusive, so "
                    "P(A ∩ B) = 0."]
        return []

    # Pure complements: P(A′) / P(B′)
    if target in ("A′", "B′"):
        base = pa if target == "A′" else pb
        if base is None:
            return None
        val = 1 - base
        ev = target[0]
        return res(val, [
            f"P({target}) = 1 − P({ev}) (complement rule).",
            f"P({target}) = 1 − {_frac(base)} = {_frac(val)}.",
        ])
    # Conditionals: P(A|B) / P(B|A)
    if target in ("A|B", "B|A"):
        num_ev, den_ev = target[0], target[2]
        den = pb if den_ev == "B" else pa
        if inter is None or den is None or den == 0:
            return None
        val = inter / den
        steps = inter_steps()
        steps += [
            f"By definition, P({num_ev}|{den_ev}) = "
            f"P(A ∩ B) / P({den_ev}).",
            f"P({num_ev}|{den_ev}) = {_frac(inter)} / "
            f"{_frac(den)} = {_frac(val)}.",
        ]
        return res(val, steps)
    # The intersection / union themselves
    if target == "A∩B":
        if inter is None:
            return None
        if inter_how == "given":
            return None      # given, not asked — no serve
        return res(inter, inter_steps())
    if target == "A∪B":
        if paub_g is not None:
            return None      # given, not asked
        if pa is None or pb is None or inter is None:
            return None
        val = pa + pb - inter
        steps = inter_steps()
        steps += [
            "By the addition rule, P(A ∪ B) = P(A) + P(B) "
            "− P(A ∩ B).",
            f"P(A ∪ B) = {_frac(pa)} + {_frac(pb)} − "
            f"{_frac(inter)} = {_frac(val)}.",
        ]
        return res(val, steps)
    # Compounds over A / B / complements: X op Y with one
    # A-side and one B-side event.
    m = re.fullmatch(r"([AB]′?)(∩|∪)([AB]′?)", target)
    if m:
        x, op_, y = m.group(1), m.group(2), m.group(3)
        if x[0] == y[0]:
            return None      # same-side compound: not a form
        if inter is None:
            return None

        def _p_event(e):
            base = pa if e[0] == "A" else pb
            if base is None:
                return None
            return base if len(e) == 1 else 1 - base

        def _p_inter(e1, e2):
            """P(e1 ∩ e2) for one A-side and one B-side
            event, or None when a needed given is missing:
            A∩B′ needs only P(A) and the intersection,
            A′∩B′ needs all three, and so on."""
            a_side = e1 if e1[0] == "A" else e2
            b_side = e2 if e1[0] == "A" else e1
            if a_side == "A" and b_side == "B":
                return inter
            if a_side == "A":            # A ∩ B′
                return None if pa is None else pa - inter
            if b_side == "B":            # A′ ∩ B
                return None if pb is None else pb - inter
            if pa is None or pb is None:  # A′ ∩ B′
                return None
            return 1 - pa - pb + inter

        if op_ == "∩":
            val = _p_inter(x, y)
            if val is None:
                return None
            steps = inter_steps()
            steps += [
                f"P(A ∩ B) = {_frac(inter)} is the part "
                f"common to A and B, so P({target}) = "
                f"{_frac(val)}.",
            ]
            return res(val, steps)
        # Union: addition rule when both event values are
        # known, else De Morgan on the complements.
        px, py = _p_event(x), _p_event(y)
        pxy = _p_inter(x, y)
        if px is not None and py is not None \
                and pxy is not None:
            val = px + py - pxy
            steps = inter_steps()
            steps += [
                "By the addition rule, "
                f"P({target}) = P({x}) + P({y}) − "
                f"P({x} ∩ {y}).",
                f"P({target}) = {_frac(px)} + {_frac(py)} − "
                f"{_frac(pxy)} = {_frac(val)}.",
            ]
            return res(val, steps)
        xc = x[0] + ("" if len(x) > 1 else "′")
        yc = y[0] + ("" if len(y) > 1 else "′")
        pcomp = _p_inter(xc, yc)
        if pcomp is None:
            return None
        val = 1 - pcomp
        steps = inter_steps()
        steps += [
            f"By De Morgan's law, P({target}) = 1 − "
            f"P({xc} ∩ {yc}) = 1 − {_frac(pcomp)} "
            f"= {_frac(val)}.",
        ]
        return res(val, steps)
    return None


# ===========================================================================
# (b) Bayes in sentence dress
# ===========================================================================

def _bayes_result(groups, target_idx, event_label):
    """groups: [(name, prior Fraction, rate Fraction)].
    Mechanical Bayes with exact fractions; steps in the
    house style."""
    joints = [p * r for _n, p, r in groups]
    total = sum(joints)
    if total <= 0:
        return None
    post = joints[target_idx] / total
    names = [g[0] for g in groups]
    steps = [
        "Priors: " + ", ".join(
            f"P({n}) = {_frac(p)}" for n, p, _r in groups)
        + ".",
        f"P({event_label} | group): " + ", ".join(
            f"{_frac(r)} for {n}" for n, _p, r in groups)
        + ".",
        "By the law of total probability, "
        f"P({event_label}) = " + " + ".join(
            f"{_frac(p)} × {_frac(r)}" for _n, p, r in groups)
        + f" = {_frac(total)}.",
        f"By Bayes' theorem, P({names[target_idx]} | "
        f"{event_label}) = {_frac(groups[target_idx][1])} × "
        f"{_frac(groups[target_idx][2])} / {_frac(total)} "
        f"= {_frac(post)}.",
    ]
    return _mk("statistics", "probability", _prob_str(post),
               steps)


def _group_match(name, target):
    """Loose-but-safe group-name matching: equal after
    singularising, or one is a prefix of the other
    ('hostel' ~ 'hosteller', 'day scholars' ~ 'day
    scholar')."""
    def norm(s):
        s = re.sub(r"\s+", " ", str(s).strip().lower())
        words = s.split(" ")
        if words and len(words[-1]) > 1 \
                and words[-1].endswith("s"):
            words[-1] = words[-1][:-1]
        return " ".join(words)
    a, b = norm(name), norm(target)
    if not a or not b:
        return False
    return a == b or a.startswith(b) or b.startswith(a)


def _bayes_residence(q):
    """Probe 21 dress: 'N% reside in <place> and M% are
    <group>. R% of all students who reside in <place>
    <event> and S% of <group> <event>. ... found to have
    <event-past>. What is the probability that the student
    is a <group-word>?'"""
    ql = q.lower()
    mp = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+(?:of\s+(?:the\s+)?"
        r"(?:students|children|people)\s+)?reside in\s+"
        r"(?:the\s+)?([a-z]+)\s+and\s+(\d+(?:\.\d+)?)\s*%\s+"
        r"are\s+([a-z][a-z ]*?)(?:\.|,|;|$)", ql)
    if not mp:
        return None
    p1 = Fraction(mp.group(1)) / 100
    g1 = mp.group(2)
    p2 = Fraction(mp.group(3)) / 100
    g2 = mp.group(4).strip()
    if p1 + p2 != 1:
        return None
    mr = re.search(
        r"(\d+(?:\.\d+)?)\s*%\s+of\s+(?:all\s+)?(?:the\s+)?"
        r"students who reside in\s+(?:the\s+)?([a-z]+)\s+"
        r"(.+?)\s+and\s+(\d+(?:\.\d+)?)\s*%\s+of\s+"
        r"([a-z][a-z ]*?)\s+\3", q, flags=re.I)
    if not mr:
        return None
    r1 = Fraction(mr.group(1)) / 100
    if mr.group(2).lower() != g1:
        return None
    event = mr.group(3).strip()
    r2 = Fraction(mr.group(4)) / 100
    if not _group_match(g2, mr.group(5)):
        return None
    if not (0 <= r1 <= 1 and 0 <= r2 <= 1):
        return None
    # the observed event must be the rates' event, reported
    # as found ("found to have attained A grade")
    mo = re.search(r"found to have\s+([a-z]+)", ql)
    if not mo:
        return None
    ev_first = event.split()[0].lower()
    if not mo.group(1).startswith(ev_first[:5]):
        return None
    mt = re.search(r"probability that the student is an?\s+"
                   r"([a-z][a-z ]*?)\s*\??\s*$", ql)
    if not mt:
        return None
    tgt_word = mt.group(1).strip()
    if _group_match(g1, tgt_word):
        idx = 0
    elif _group_match(g2, tgt_word):
        idx = 1
    else:
        return None
    groups = [(g1, p1, r1), (g2, p2, r2)]
    return _bayes_result(groups, idx, event)


def _bayes_factories(q):
    """NCERT Ex 13.3 factory/machine dress, 2 or 3 groups:
    'Factory A produces 50% of the items, factory B
    produces 30% ...' (or 'N% of the items are produced by
    machine A'), 'R% of items from machine A are defective
    ...', item found defective, 'probability that it came
    from / was produced by factory B?'"""
    ql = q.lower()
    if "defective" not in ql:
        return None
    priors = {}
    for m in re.finditer(
            r"(?:factory|machine|plant)\s+([A-Z])\s+"
            r"produces?\s+(\d+(?:\.\d+)?)\s*%", q, flags=re.I):
        priors[m.group(1).upper()] = Fraction(m.group(2)) / 100
    if len(priors) < 2:
        priors = {}
        for m in re.finditer(
                r"(\d+(?:\.\d+)?)\s*%\s+of\s+(?:the\s+)?items\s+"
                r"(?:are\s+)?produced\s+by\s+(?:factory|"
                r"machine|plant)\s+([A-Z])", q, flags=re.I):
            priors[m.group(2).upper()] = \
                Fraction(m.group(1)) / 100
    if len(priors) < 2 or len(priors) > 3:
        return None
    if sum(priors.values()) != 1:
        return None
    rates = {}
    for m in re.finditer(
            r"(\d+(?:\.\d+)?)\s*%\s+of\s+(?:the\s+)?items\s+"
            r"(?:produced\s+)?(?:from|by)\s+(?:factory|"
            r"machine|plant)\s+([A-Z])\s+are\s+defective", q,
            flags=re.I):
        rates[m.group(2).upper()] = Fraction(m.group(1)) / 100
    if len(rates) < len(priors):
        for m in re.finditer(
                r"(?:factory|machine|plant)\s+([A-Z])\s+"
                r"(?:has|have)\s+(\d+(?:\.\d+)?)\s*%\s+"
                r"defective", q, flags=re.I):
            rates.setdefault(m.group(1).upper(),
                             Fraction(m.group(2)) / 100)
    if set(rates) != set(priors):
        return None
    if any(not (0 <= r <= 1) for r in rates.values()):
        return None
    # the item must be REPORTED defective, and the target
    # group named in the ask
    if not re.search(r"found\s+(?:to\s+be\s+)?defective|"
                     r"is\s+defective", ql):
        return None
    mt = None
    for m in re.finditer(
            r"(?:produced\s+by|came\s+from|come\s+from|"
            r"from)\s+(?:the\s+)?(?:factory|machine|plant)\s+"
            r"([A-Z])\b", q, flags=re.I):
        mt = m
    if mt is None:
        return None
    tgt = mt.group(1).upper()
    if tgt not in priors:
        return None
    noun = ("machine" if "machine" in ql else
            "factory" if "factory" in ql else "plant")
    letters = sorted(priors)
    groups = [(f"{noun} {L}", priors[L], rates[L])
              for L in letters]
    idx = letters.index(tgt)
    return _bayes_result(groups, idx, "defective")


def _bayes_bags(q):
    """NCERT Ex 13.3 bag dress: 'Bag I contains 3 red and
    4 black balls, Bag II contains 4 red and 5 black
    balls. A bag is chosen at random and a ball drawn is
    found to be red. ... probability it came from Bag I?'
    Equal priors (chosen at random)."""
    ql = q.lower()
    if "chosen at random" not in ql:
        return None
    bags = {}
    for m in re.finditer(
            r"bag\s+(I{1,3}|[12])\s+contains\s+(\d+)\s+red\s+"
            r"and\s+(\d+)\s+black\s+balls", q, flags=re.I):
        bags[m.group(1).upper()] = (int(m.group(2)),
                                    int(m.group(3)))
    if len(bags) != 2:
        return None
    mc = re.search(r"(?:found to be|is|was)\s+(red|black)\b",
                   ql)
    if not mc:
        return None
    colour = mc.group(1)
    mt = None
    for m in re.finditer(r"from\s+bag\s+(I{1,3}|[12])\b", q,
                         flags=re.I):
        mt = m
    if mt is None:
        return None
    tgt = mt.group(1).upper()
    if tgt not in bags:
        return None
    keys = sorted(bags)
    groups = []
    for k in keys:
        red, black = bags[k]
        tot = red + black
        if tot <= 0:
            return None
        cnt = red if colour == "red" else black
        groups.append((f"Bag {k}", Fraction(1, 2),
                       Fraction(cnt, tot)))
    return _bayes_result(groups, keys.index(tgt),
                          f"{colour} ball")


# ===========================================================================
# (c) Probability distribution in sentence dress
# ===========================================================================

_TOKEN = re.compile(r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?")


def _distribution_parse(q):
    """Strict sentence-dress parse -> (xs, ps, asks) with
    exact Fractions, or None.  asks is a subset of
    {'mean', 'variance', 'std'}."""
    ql = q.lower()
    if "probability distribution" not in ql and not (
            "random variable" in ql and "probabilit" in ql):
        return None
    mx = re.search(r"(?<![A-Za-z])X\s*=\s*(.+?)(?:\bwith\b|"
                   r"\bP\s*\()", q)
    if not mx:
        mx = re.search(r"takes values\s+(.+?)(?:\bwith\b|"
                       r"\bprobabilit)", q, flags=re.I)
    if mx:
        xtoks = _TOKEN.findall(mx.group(1))
        mp = re.search(r"P\s*\(\s*X\s*\)\s*=\s*(.*)", q)
        if not mp:
            mp = re.search(r"probabilities\s+(?:are\s+)?(.*)",
                           q, flags=re.I)
        if not mp:
            return None
        ptoks = _TOKEN.findall(mp.group(1))[:len(xtoks)]
    else:
        # Linearised table dress (the book-paste form
        # tierA169 parses for P-asks and declines for
        # mean/variance asks): "… probability distribution
        # : X 0 1 2 P (X) 0.2 0.3 0.5 Find the mean …".
        # Strict: the segment between the last
        # "distribution" mention and P(X must be NOTHING
        # but the X row (digits, dots, signs, the letters
        # of "r.v." / "X" themselves).
        mp2 = re.search(r"P\s*\(\s*X\s*(?:=\s*x)?\s*\)", q)
        if not mp2 or "distribution" not in ql:
            return None
        head = q[:mp2.start()]
        di = head.lower().rfind("distribution")
        xseg = head[di + len("distribution"):]
        xseg = re.sub(r"r\.\s*v\.|discrete|random variable",
                      " ", xseg, flags=re.I)
        xseg = re.sub(r"[Xx:=]", " ", xseg)
        if re.search(r"[A-Za-z]", xseg):
            return None
        xtoks = _TOKEN.findall(xseg)
        ptoks = _TOKEN.findall(q[mp2.end():])[:len(xtoks)]
    if len(xtoks) < 2 or len(xtoks) > 12:
        return None
    if len(ptoks) != len(xtoks):
        return None
    try:
        xs = [_pfrac(t) for t in xtoks]
        ps = [_pfrac(t) for t in ptoks]
    except Exception:
        return None
    if len(set(xs)) != len(xs):
        return None
    if any(p < 0 or p > 1 for p in ps):
        return None
    if sum(ps) != 1:
        return None          # not a valid distribution
    asks = set()
    if re.search(r"\bmean\b|e\s*\(\s*x\s*\)|expected value",
                 ql):
        asks.add("mean")
    if re.search(r"\bvariance\b|var\s*\(\s*x\s*\)", ql):
        asks.add("variance")
    if "standard deviation" in ql:
        asks.add("std")
    if not asks:
        return None
    return xs, ps, asks


def _distribution_values(xs, ps):
    mean = sum(x * p for x, p in zip(xs, ps))
    ex2 = sum(x * x * p for x, p in zip(xs, ps))
    var = ex2 - mean * mean
    return mean, ex2, var


def _distribution_result(q):
    got = _distribution_parse(q)
    if got is None:
        return None
    xs, ps, asks = got
    mean, ex2, var = _distribution_values(xs, ps)
    terms = " + ".join(f"{_step_num(x)}×{_step_num(p)}"
                       for x, p in zip(xs, ps))
    steps = [
        "For a probability distribution, the mean is "
        "E(X) = Σ x·P(x).",
        f"E(X) = {terms} = {_num_str(mean)}.",
    ]
    parts = []
    if "mean" in asks:
        parts.append(f"Mean = {_num_str(mean)}")
    if "variance" in asks or "std" in asks:
        terms2 = " + ".join(
            f"{_step_num(x)}²×{_step_num(p)}"
            for x, p in zip(xs, ps))
        steps.append(
            f"E(X²) = Σ x²·P(x) = {terms2} = "
            f"{_num_str(ex2)}.")
        steps.append(
            "Variance = E(X²) − (E(X))² = "
            f"{_num_str(ex2)} − {_num_str(mean)}² = "
            f"{_num_str(var)}.")
    if "variance" in asks:
        parts.append(f"Variance = {_num_str(var)}")
    sd_val = None
    if "std" in asks:
        sd_r = sp.sqrt(sp.Rational(var.numerator,
                                   var.denominator))
        if sd_r.is_rational:
            sd_val = Fraction(int(sd_r.p), int(sd_r.q))
            sd_str = _num_str(sd_val)
        else:
            sd_val = float(sd_r)
            sd_str = f"{sd_val:.4f}"
        steps.append(
            f"Standard deviation = √Variance = "
            f"√{_num_str(var)} = {sd_str}.")
        parts.append(f"Standard deviation = {sd_str}")
    if len(asks) == 1:
        op = {"mean": "distribution_mean",
              "variance": "distribution_variance",
              "std": "distribution_sd"}[next(iter(asks))]
        value = float(mean if op == "distribution_mean"
                      else var if op == "distribution_variance"
                      else sd_val)
    else:
        op = "distribution_mean_variance"
        value = float(mean)
    return _mk("statistics", op, ", ".join(parts), steps,
               value=value)


def repair_probwords188(question, result):
    """Wave 171-style hijack repair for the distribution
    sentence dress.  The primary statistics solver served
    a REAL answer (plain mean / variance / std of the
    value list) to a probability-distribution question.
    Displace ONLY when this module's strict parse settles
    the question AND the served value for the asked
    quantity provably differs, or the serve is a fragment
    of a combined ask.  A correct serve stands."""
    if not isinstance(result, dict):
        return None
    if result.get("type") != "statistics":
        return None
    op = result.get("op")
    if op not in ("mean", "variance", "std"):
        return None
    q = _prep(question)
    got = _distribution_parse(q)
    if got is None:
        return None
    xs, ps, asks = got
    mean, _ex2, var = _distribution_values(xs, ps)
    correct = {"mean": float(mean), "variance": float(var),
               "std": float(var) ** 0.5}[op]
    served = result.get("value")
    if not isinstance(served, (int, float)):
        m = re.search(r"-?\d+(?:\.\d+)?",
                      str(result.get("answer") or ""))
        if not m:
            return None
        served = float(m.group(0))
    differs = abs(float(served) - correct) > 1e-9
    fragment = asks != {op if op != "std" else "std"}
    if not differs and not fragment:
        return None
    return _distribution_result(q)


# ===========================================================================
# Entry point (failure-only gate)
# ===========================================================================

def solve_probwords188(question):
    """Wave 188 schemas; None unless one settles the
    question completely."""
    try:
        q = _prep(question)
    except Exception:
        return None
    if not q.strip():
        return None
    for fn in (_distribution_result, _word_relations,
               _bayes_residence, _bayes_factories,
               _bayes_bags):
        try:
            out = fn(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
