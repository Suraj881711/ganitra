"""Wave 75: the concept-answer layer — chat concept asks
answered from the app's own topics library.

The Wave 71 solver-health audit's biggest failure family
(~214 of 489 failures) was students asking to be TAUGHT:
definitions ("what is a prime number", "AP kya hoti hai?"),
how-to method asks ("HCF kaise nikale?"), formula requests
("quadratic formula kya hai?"), difference-between asks
("HCF aur LCM me kya antar hai?") and why-questions. Those
asks fell to the Wave-18 concepts.py keyword cards — a small
75-entry library — while the app's own topics library
(topics_data.py, Wave 55: 230 topics, each with a method
idea + steps and ONE worked example verified through the
app's own solve path) was never routed to from chat.

This module is that route. fallback.py consults it AFTER the
real solver, the verified bank and salvage have all had
their chance, and BEFORE the concepts.py card:

  * GATE — the question must be shaped like a concept ask
    (what is / kya hai / kaise / formula / antar / kyun /
    samjhao ... in English, Hinglish or Devanagari).
  * VETO — a question carrying a concrete problem (an
    equation to solve, a digit-operator-digit expression, a
    data list, coordinate pairs, digit+unit with a compute
    verb, MCQ option markers, assertion-reason framing ...)
    is NEVER captured, however concept-y its words sound.
    It falls through to exactly today's behaviour.
  * MATCH — the ask is normalised (spelling fold + a
    Hinglish/Devanagari concept-word translation) and matched
    to ONE topic: a curated alias table first (the phrasings
    students actually use), then a strict token-overlap score
    against topic names/chapters (unique winner required).
    Difference asks match two topics (or one combined topic)
    and answer with both.
  * ANSWER — the served card is the topic's own content:
    the answer line is "<Topic> — <idea>", the steps are the
    topic's method steps plus its worked example (starter
    question + the Wave-55-verified answer). Nothing is
    paraphrased, translated or invented: topics_data is
    English-only, so the card is English — the same
    steps-are-English convention the product already uses.

The result keeps fallback_kind == "concept" (it is the
concept layer, now topic-backed) and is marked
source="topics" + topic_slug/topic_class so analytics — and
the Wave-71 re-run — can tell a topics answer apart from a
concepts.py card.
"""
import re

from topics_data import TOPICS_BY_CLASS
from solver.router import normalize_spelling

# ---------------------------------------------------------------------------
# Topic index: slug -> (class, topic). Duplicate slugs exist
# across classes (e.g. circumference-of-a-circle in 7 and 9);
# the LOWEST class wins — the foundational treatment is the
# right default for a concept ask, and it matches how the
# /topics directory introduces the idea first.
# ---------------------------------------------------------------------------

_BY_SLUG = {}
_ORDERED = []  # (class, topic) in directory order
for _cls in sorted(TOPICS_BY_CLASS):
    for _t in TOPICS_BY_CLASS[_cls]:
        _ORDERED.append((_cls, _t))
        _BY_SLUG.setdefault(_t["slug"], (_cls, _t))


def _topic(slug):
    return _BY_SLUG.get(slug)


# ---------------------------------------------------------------------------
# Normalisation for matching: spelling fold, then a concept-word
# translation (Devanagari + Roman Hinglish -> English) so one
# alias table serves all three scripts. Applied to a MATCHING
# COPY only — served content is never touched.
# ---------------------------------------------------------------------------

# Devanagari phrases (plain substring replacement, longest
# first). Gate phrases are translated too, so the English
# gate patterns below see them.
_DEV_PHRASES = [
    ("साधारण ब्याज कैसे निकालते हैं", "how to find simple interest"),
    ("कैसे निकालते हैं", "how to find"),
    ("कैसे हल करते हैं", "how to solve"),
    ("किसे कहते हैं", "what is"),
    ("किसे कहते है", "what is"),
    ("क्या होता है", "what is"),
    ("क्या होती है", "what is"),
    ("क्या होते हैं", "what are"),
    ("क्या है", "what is"),
    ("साधारण ब्याज", "simple interest"),
    ("चक्रवृद्धि ब्याज", "compound interest"),
    ("पाइथागोरस प्रमेय", "pythagoras theorem"),
    ("समांतर श्रेणी", "arithmetic progression"),
    ("समान्तर श्रेणी", "arithmetic progression"),
    ("ज्यामितीय श्रेणी", "geometric progression"),
    ("द्विघात समीकरण", "quadratic equation"),
    ("द्विघात सूत्र", "quadratic formula"),
    ("महत्तम समापवर्तक", "hcf"),
    ("लघुत्तम समापवर्त्य", "lcm"),
    ("लघुत्तम समापवर्तक", "lcm"),
    ("अभाज्य संख्या", "prime number"),
    ("भाज्य संख्या", "composite number"),
    ("परिमेय संख्या", "rational number"),
    ("अपरिमेय संख्या", "irrational number"),
    ("समकोण त्रिभुज", "right triangle"),
    ("समबाहु त्रिभुज", "equilateral triangle"),
    ("माध्यिका", "median"),
    ("माध्यक", "median"),
    ("बहुलक", "mode"),
    ("माध्य", "mean"),
    ("औसत", "mean"),
    ("प्रतिशत", "percentage"),
    ("त्रिकोणमिति", "trigonometry"),
    ("गुणनखंड", "factors"),
    ("क्रमगुणित", "factorial"),
    ("प्रायिकता", "probability"),
    ("ब्याज", "interest"),
    ("प्रमेय", "theorem"),
    ("वृत्त", "circle"),
    ("त्रिज्या", "radius"),
    ("क्षेत्रफल", "area"),
    ("परिधि", "circumference"),
    ("परिमाप", "perimeter"),
    ("त्रिभुज", "triangle"),
    ("आयत", "rectangle"),
    ("वर्ग", "square"),
    ("कोण", "angle"),
    ("सूत्र", "formula"),
    ("अंतर", "difference"),
    ("क्यों", "why"),
    ("कैसे", "how"),
    ("क्या", "what"),
    ("समीकरण", "equation"),
    ("रेखाखंड", "line segment"),
    ("रेखाखण्ड", "line segment"),
    ("स्पर्श रेखा", "tangent"),
    ("चाल", "speed"),
    ("दूरी", "distance"),
    ("समय", "time"),
]

# Roman-Hinglish phrases (word-boundary replacement, longest
# first).
_ROMAN_PHRASES = [
    ("sadharan byaaj", "simple interest"),
    ("sadharan byaj", "simple interest"),
    ("chakrvridhi byaaj", "compound interest"),
    ("chakrvridhi byaj", "compound interest"),
    ("chakravridhi byaj", "compound interest"),
    ("dwighaat samikaran", "quadratic equation"),
    ("vargeeya samikaran", "quadratic equation"),
    ("samkon tribhuj", "right triangle"),
    ("abhajya sankhya", "prime number"),
    ("abhaajya sankhya", "prime number"),
    ("parimey sankhya", "rational number"),
    ("aparimey sankhya", "irrational number"),
    ("sparsh rekha", "tangent"),
    ("do charo", "two variable"),
    ("byaaj", "interest"),
    ("byaj", "interest"),
    ("samikaran", "equation"),
    ("tribhuj", "triangle"),
    ("abhajya", "prime"),
    ("abhaajya", "prime"),
    ("parimey", "rational"),
    ("aparimey", "irrational"),
    ("ausat", "mean"),
    ("madhyika", "median"),
    ("bahulak", "mode"),
    ("pratishat", "percentage"),
    ("feesadi", "percentage"),
    # Wave 185: voice-typing spellings from the prediction
    # battery — "parsentage kaise nikale" matched nothing
    # and classified as gibberish; "trignometry kya hai"
    # reached only the AI legs.
    ("parsentage", "percentage"),
    ("parsantage", "percentage"),
    ("trignometry", "trigonometry"),
    ("vritt", "circle"),
    ("trijya", "radius"),
    ("kshetrafal", "area"),
    ("parimaap", "perimeter"),
    ("parimap", "perimeter"),
    ("gunaankhand", "factors"),
    ("gunankhand", "factors"),
    ("anupaat", "ratio"),
    ("anupat", "ratio"),
    ("sarvsamika", "identity"),
    ("shunyak", "zeroes"),
    ("ghaat", "exponent"),
    ("karni", "surd"),
    ("aayatan", "volume"),
    ("gola", "sphere"),
    ("belan", "cylinder"),
    ("shanku", "cone"),
    ("chaal", "speed"),
    ("chakal", "speed"),
    ("doori", "distance"),
    ("samay", "time"),
    ("vivechak", "discriminant"),
    ("upasamuchchay", "subset"),
    ("dhal", "slope"),
    ("barambarta", "frequency"),
    ("pramey", "theorem"),
    ("sankhya", "number"),
    ("yog", "sum"),
    # Wave 81: line words (longest first, and after
    # "sparsh rekha" above so the tangent phrase still wins).
    ("rekha khand", "line segment"),
    ("rekha", "line"),
]


def _translate(text):
    t = " " + str(text or "").lower() + " "
    # Longest first: "अपरिमेय संख्या" (irrational number)
    # CONTAINS "परिमेय संख्या" (rational number) as a
    # substring — replacing the shorter phrase first would
    # mangle it into "अ + rational number".
    for src, dst in sorted(_DEV_PHRASES,
                           key=lambda kv: -len(kv[0])):
        if src in t:
            t = t.replace(src, " " + dst + " ")
    for src, dst in _ROMAN_PHRASES:
        t = re.sub(r"(?<![a-z])" + re.escape(src) + r"(?![a-z])",
                   " " + dst + " ", t)
    return t.strip()


def _match_text(question):
    """The normalised, translated text all matching runs on.
    Parentheses are dropped: students write the translation
    in brackets ("shanku (cone) ka volume", "mode
    (bahulak)"), and the bracket would otherwise break the
    phrase it translates."""
    folded = normalize_spelling(str(question or ""))
    t = _translate(folded)
    t = re.sub(r"[()\[\]]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------

def _tokens(text):
    """Lowercase word tokens, lightly singularised (numbers ->
    number, ratios -> ratio), pure-digit tokens dropped."""
    out = []
    for tok in re.findall(r"[a-z]+|\d+(?:\.\d+)?",
                          str(text or "").lower()):
        if tok.isdigit():
            continue
        if len(tok) > 3 and tok.endswith("s") \
                and not tok.endswith("ss"):
            tok = tok[:-1]
        out.append(tok)
    return out


def _stem_hit(tok, candidates):
    """True when tok matches a candidate token exactly, or by
    a long common prefix (trigonometry ~ trigonometric)."""
    for c in candidates:
        if tok == c:
            return True
        if len(tok) >= 7 and len(c) >= 7:
            n = 0
            for a, b in zip(tok, c):
                if a != b:
                    break
                n += 1
            if n >= 7:
                return True
    return False


# ---------------------------------------------------------------------------
# GATE: is this shaped like a concept ask at all?
# Checked against the ORIGINAL text and the translated text.
# ---------------------------------------------------------------------------

_GATE_PATTERNS = [
    r"\bwhat\b", r"\bdefine\b", r"\bexplain\b", r"\bmeaning\b",
    r"\bformula\b", r"\bhow\b", r"\bwhy\b", r"\bkab\b",
    r"\bdifference\b", r"\bdifferent\b",
    "kaise", "kese", "कैसे",
    "kya hai", "kya hota", "kya hoti", "kya hote", "क्या",
    "kise kehte", "kise kahate", "किसे कहते",
    "matlab", "kyun", "kyu", "क्यों",
    "tarika", "tareeka", "तरीका",
    "samjhao", "samjha do", "samjhado", "समझाओ",
    "batao", "btao", "बताओ",
    "antar", "fark", "अंतर", "alag",
    "hota hai", "hoti hai", "hote hain",
    "होता है", "होती है", "होते हैं",
    "nikale", "nikalne", "nikalte", "nikaale", "निकाल",
    "सूत्र",
]
_GATE_RE = [re.compile(p) for p in _GATE_PATTERNS]


def _has_gate(question, mtext):
    raw = str(question or "").lower()
    # Doubled-letter typos ("wwhat is mean median mode") are
    # gate-checked on a de-doubled copy as well — the fold in
    # normalize_spelling does not catch every doubling, and
    # the gate is the only place the typo can hurt (matching
    # itself is alias/token based and unaffected).
    dedoubled = re.sub(r"([a-z])\1+", r"\1", raw)
    for rx in _GATE_RE:
        if rx.search(raw) or rx.search(mtext) \
                or rx.search(dedoubled):
            return True
    return False


# ---------------------------------------------------------------------------
# VETO: concrete-problem signals. Any one of these means the
# question carries a problem to COMPUTE, not a concept to
# teach — the layer must not touch it. (Defence in depth: the
# layer already sits behind the real solver and salvage, so
# anything reaching here has failed both; these vetoes stop
# solver-failed concrete problems — paper questions, MCQs,
# word problems — from being captured by a concept-y word.)
# ---------------------------------------------------------------------------

_EQ_RE = re.compile(r"=")
_ARITH_RE = re.compile(r"\d\s*[+\-*/×÷]\s*\d|\d\s+x\s+\d")
_LIST_RE = re.compile(r"\d+(?:\.\d+)?\s*[,،]\s*\d+(?:\.\d+)?\s*[,،]\s*\d+")
_PAIR_RE = re.compile(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*\)")
_OF_PAIR_RE = re.compile(
    r"\b(?:of|ke|ka)\s+\d+(?:\.\d+)?\s+(?:and|aur|और|&)\s+\d+")
_OPTION_RE = re.compile(r"\(\s*[a-dA-D]\s*\)")
_UNIT_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:cm|mm|km|metre|meter|mtr|kg|gm|g|"
    r"litre|liter|ml|sec|second|min|hour|hr|₹|rs\.?|rupees|"
    r"m/s|km/h|cm/s)\b")
_UNIT_VERB_RE = re.compile(
    r"\bfind\b|\bsolve\b|\bcalculate\b|\bevaluate\b|"
    r"at what rate|rate of|increasing at|decreasing at|"
    r"kitna|kitni|ज्ञात|निकाल|गणना")
_ASSERT_RE = re.compile(
    r"assertion|अभिकथन|case study|प्रकरण अध्ययन", re.I)
_FORMULA_GATE_RE = re.compile(r"formula|सूत्र", re.I)


def _vetoed(question, mtext):
    raw = str(question or "")
    text = mtext
    # An equation to solve (papers ask "द्विघात सूत्र का उपयोग
    # कर समीकरण x² + 7x − 60 = 0 का मूल निकालें" — the word
    # सूत्र must not capture it).
    if _EQ_RE.search(raw) and re.search(r"\d", raw):
        return True
    # A bare arithmetic expression (incl. "9 x 6 x 5").
    if _ARITH_RE.search(raw) or _ARITH_RE.search(text):
        return True
    # A data list (mean/median of THESE numbers).
    if _LIST_RE.search(raw):
        return True
    # Coordinate pairs — coordinate-geometry problems.
    if _PAIR_RE.search(raw):
        return True
    # "HCF of 12 and 18" — two concrete operands.
    if _OF_PAIR_RE.search(text):
        return True
    # MCQ option markers (two or more) — a paper question.
    if len(_OPTION_RE.findall(raw)) >= 2:
        return True
    # Assertion–Reason / case-study framing.
    if _ASSERT_RE.search(raw):
        return True
    # A measurement + a compute verb — mensuration / SDT /
    # rate problems ("radius 7 cm ... find", "3 cm/s ...
    # at what rate").
    if _UNIT_RE.search(raw) and _UNIT_VERB_RE.search(text):
        return True
    # Two or more separate numbers: a concrete problem,
    # unless the ask is a pure formula request, a trig
    # identity (sin/cos present — "1 + tan²θ ... sin²A +
    # cos²A kitna hota hai"), or the digits are only the
    # probability bounds 0 and 1 being asked about.
    groups = re.findall(r"\d+(?:\.\d+)?", raw)
    if len(groups) >= 2:
        if _FORMULA_GATE_RE.search(raw):
            return False
        toks = set(_tokens(text))
        if toks & {"sin", "cos", "tan", "sec", "cosec", "cot"}:
            return False
        if set(groups) <= {"0", "1", "0.0", "1.0"}:
            return False
        return True
    return False


# ---------------------------------------------------------------------------
# MATCH: alias table (the phrasings students actually use,
# from the Wave 71 battery) -> topic slug. Longest phrase
# first, so "quadratic formula" beats "formula"-ish shorter
# keys and "mean median" beats "mean".
# ---------------------------------------------------------------------------

_ALIASES = [
    # Wave 185: "vyas" is the everyday Hindi word for
    # diameter — "2 number ka sawal hai batao vyas kya
    # hota hai" matched no alias and reached only the AI
    # legs, although the library owns the topic.
    ("vyas", "radius-and-diameter"),
    ("pythagoras theorem", "pythagoras-theorem"),
    ("pythagoras", "pythagoras-theorem"),
    ("right angled triangle", "pythagoras-property"),
    ("right triangle", "pythagoras-property"),
    ("highest common factor", "hcf-and-lcm"),
    ("least common multiple", "lcm-of-numbers"),
    ("lowest common multiple", "lcm-of-numbers"),
    ("prime factorisation", "prime-factorisation"),
    ("prime factorization", "prime-factorisation"),
    ("prime number", "prime-and-composite-numbers"),
    ("composite number", "prime-and-composite-numbers"),
    ("prime", "prime-and-composite-numbers"),
    ("bodmas", "bodmas"),
    ("mean median", "mean-median-and-mode"),
    ("median and mode", "median-and-mode"),
    ("median aur mode", "median-and-mode"),
    ("median mode", "median-and-mode"),
    ("arithmetic progression", "nth-term-of-an-ap"),
    ("geometric progression", "geometric-progressions"),
    ("quadratic formula", "quadratic-formula"),
    ("quadratic equation", "quadratic-formula"),
    ("discriminant", "discriminant-and-nature-of-roots"),
    ("trigonometric identities", "trigonometric-identities"),
    ("trig identity", "trigonometric-identities"),
    ("trigonometric ratios", "trigonometric-ratios"),
    ("trig ratios", "trigonometric-ratios"),
    ("trigonometry", "trigonometric-ratios"),
    ("standard identities", "standard-identities"),
    ("algebraic identities", "algebraic-identities"),
    ("identity", "algebraic-identities"),
    ("simple interest", "simple-interest"),
    ("compound interest", "compound-interest"),
    ("interest", "simple-interest"),
    ("percentage", "percentage"),
    ("percent", "percentage"),
    ("probability", "classical-probability"),
    ("factorial", "permutations"),
    ("factors and multiples", "factors-and-multiples"),
    ("factors", "factors-and-multiples"),
    ("area of a circle", "circumference-and-area-of-a-circle"),
    ("area of circle", "circumference-and-area-of-a-circle"),
    ("circle ka area", "circumference-and-area-of-a-circle"),
    ("circle area", "circumference-and-area-of-a-circle"),
    ("circumference", "circumference-of-a-circle"),
    ("area of a triangle", "area-of-a-triangle"),
    ("area of triangle", "area-of-a-triangle"),
    ("triangle ka area", "area-of-a-triangle"),
    ("triangle area", "area-of-a-triangle"),
    ("heron", "heron-s-formula"),
    ("distance formula", "distance-formula"),
    ("midpoint", "section-formula-and-midpoint"),
    ("nth term", "nth-term-of-an-ap"),
    ("common difference", "nth-term-of-an-ap"),
    ("sum of a gp", "sum-of-a-gp"),
    ("gp ka sum", "sum-of-a-gp"),
    ("gp sum", "sum-of-a-gp"),
    ("sum of an ap", "sum-of-first-n-terms-of-an-ap"),
    ("sum of ap", "sum-of-first-n-terms-of-an-ap"),
    ("sum of first n terms", "sum-of-first-n-terms-of-an-ap"),
    ("volume of a cone", "volume-of-a-cone"),
    ("cone ka volume", "volume-of-a-cone"),
    ("cone volume", "volume-of-a-cone"),
    ("volume of a cylinder", "volume-of-a-cylinder"),
    ("cylinder ka volume", "volume-of-a-cylinder"),
    ("cylinder volume", "volume-of-a-cylinder"),
    ("volume of a sphere", "volume-of-a-sphere"),
    ("sphere ka volume", "volume-of-a-sphere"),
    ("sphere volume", "volume-of-a-sphere"),
    ("surface area of a sphere", "surface-area-of-a-sphere"),
    ("sphere ka surface area", "surface-area-of-a-sphere"),
    ("sphere surface area", "surface-area-of-a-sphere"),
    ("surface area of a cube", "surface-area-of-a-cube"),
    ("volume of a cube", "volume-of-a-cube"),
    ("surface area of a cylinder", "surface-area-of-a-cylinder"),
    ("surface area of a cuboid", "surface-area-of-a-cuboid"),
    ("volume of a cuboid", "volume-of-a-cuboid"),
    ("surface area of a cone", "total-surface-area-of-a-cone"),
    ("speed distance", "speed-distance-and-time"),
    ("laws of exponents", "laws-of-exponents"),
    ("exponent", "laws-of-exponents"),
    ("irrational number", "irrational-numbers-and-surds"),
    ("surd", "irrational-numbers-and-surds"),
    ("slope", "slope-of-a-line"),
    ("mutually exclusive", "mutually-exclusive-events"),
    ("standard deviation", "variance-and-standard-deviation"),
    ("variance", "variance-and-standard-deviation"),
    ("modulus", "modulus-and-conjugate"),
    ("conjugate", "conjugate-of-a-complex-number"),
    ("complex number", "complex-number-arithmetic"),
    ("matrices", "matrix-operations"),
    ("matrix", "matrix-operations"),
    ("determinant", "determinants"),
    ("integration", "indefinite-integrals"),
    ("integral", "indefinite-integrals"),
    ("pair of linear equations", "substitution-method"),
    ("two variable", "substitution-method"),
    ("linear equation", "solving-simple-equations"),
    ("equation", "solving-simple-equations"),
    ("profit and loss", "profit-and-loss"),
    ("profit loss", "profit-and-loss"),
    ("tangent", "length-of-a-tangent"),
    ("sector", "area-of-a-sector"),
    ("zeroes of a polynomial", "zeroes-of-a-polynomial"),
    ("zeroes", "zeroes-of-a-polynomial"),
    ("union", "operations-on-sets"),
    ("intersection", "operations-on-sets"),
    ("sin theta", "standard-angle-values"),
    ("cosec", "trigonometric-ratios"),
    ("secant", "trigonometric-ratios"),
    ("median", "median-of-ungrouped-data"),
    ("average", "mean-of-data"),
    ("mean", "mean-of-data"),
    ("mode", "mode-of-data"),
    # Wave 81: routes for the topics added to the library in
    # the same wave. Definition-shaped phrases only, so
    # compute asks keep their current routes; two protective
    # entries keep the older topics reachable ("remainder
    # theorem" before bare "theorem", "logarithmic
    # functions" ties "logarithm" on position and wins on
    # length).
    ("remainder theorem", "remainder-theorem"),
    ("theorem", "theorem"),
    ("derivative kya", "derivative-of-a-function"),
    ("derivative hota", "derivative-of-a-function"),
    ("what is a derivative", "derivative-of-a-function"),
    ("limit kya", "limit-of-a-function"),
    ("limit hoti", "limit-of-a-function"),
    ("limit hota", "limit-of-a-function"),
    ("limit matlab", "limit-of-a-function"),
    ("what is a limit", "limit-of-a-function"),
    ("subset", "subsets"),
    ("volume kya", "volume"),
    ("volume hota", "volume"),
    ("what is volume", "volume"),
    ("logarithmic functions", "derivatives-of-logarithmic-functions"),
    ("logarithm", "logarithms"),
    ("ogive", "ogive"),
    ("frequency kya", "frequency"),
    ("discount kya", "discount"),
    ("discount kese", "discount"),
    ("discount kaise", "discount"),
    ("discount matlab", "discount"),
    ("function kya", "function"),
    ("what is a function", "function"),
    ("iota", "iota-the-imaginary-unit"),
    ("ratio kya", "ratio"),
    ("ratio kise", "ratio"),
    ("ratio matlab", "ratio"),
    ("what is a ratio", "ratio"),
]

# Whole-token aliases for the abbreviations students type.
_TOKEN_ALIASES = {
    "hcf": "hcf-and-lcm",
    "lcm": "lcm-of-numbers",
    "ap": "nth-term-of-an-ap",
    "gp": "geometric-progressions",
    # Wave 81: whole-token only, so "pie chart" can never
    # graze it the way a substring alias would.
    "pi": "pi",
}

# Unordered concept pairs for difference asks: a combined
# topic when the library has one, else the two topics to
# compose the answer from.
_DIFF_PAIRS = [
    ({"hcf"}, {"lcm"}, ("hcf-and-lcm",)),
    ({"mean"}, {"median"}, ("mean-median-and-mode",)),
    ({"union"}, {"intersection"}, ("operations-on-sets",)),
    ({"simple", "interest"}, {"compound", "interest"},
     ("simple-interest", "compound-interest")),
    ({"area"}, {"perimeter"},
     ("area-of-rectangles-and-squares",
      "perimeter-of-rectangles-and-squares")),
    ({"ap"}, {"gp"},
     ("nth-term-of-an-ap", "geometric-progressions")),
    # Wave 81: pairs for the topics added in the same wave.
    ({"ratio"}, {"proportion"},
     ("ratio", "proportion")),
    ({"congruent"}, {"similar"},
     ("congruent-triangles", "similar-triangles")),
    ({"surface", "area"}, {"volume"},
     ("surface-area", "volume")),
    ({"sequence"}, {"serie"},
     ("sequence", "series")),
    ({"line"}, {"line", "segment"},
     ("line", "line-segment")),
    ({"square"}, {"rectangle"},
     ("square", "rectangle")),
]


# ---------------------------------------------------------------------------
# Topics Expansion — Band A (Classes 0-8): topics_banda.py
# appends its foundational / middle-school topics to the
# index above and merges its routing tables into the ones
# defined in this module. topics_data.TOPICS_BY_CLASS is
# NOT touched — its per-class counts are locked by
# test_wave55_topics.py — so Band A topics live only in
# this concept index.
# ---------------------------------------------------------------------------

from topics_banda import (
    ALIASES_BANDA, DEV_PHRASES_BANDA, DIFF_PAIRS_BANDA,
    ROMAN_PHRASES_BANDA, TOKEN_ALIASES_BANDA, TOPICS_BANDA)

for _cls in sorted(TOPICS_BANDA):
    for _bt in TOPICS_BANDA[_cls]:
        _ORDERED.append((_cls, _bt))
        _BY_SLUG.setdefault(_bt["slug"], (_cls, _bt))
_ALIASES.extend(ALIASES_BANDA)
_TOKEN_ALIASES.update(TOKEN_ALIASES_BANDA)
_DEV_PHRASES.extend(DEV_PHRASES_BANDA)
_ROMAN_PHRASES.extend(ROMAN_PHRASES_BANDA)
_DIFF_PAIRS.extend(DIFF_PAIRS_BANDA)

# Topics Scale-Up, Band C: routing extensions for the topics
# in topics_bandc.py. Band C phrase aliases are PREPENDED
# (earliest position wins; ties go to the longer phrase, so a
# specific Band C phrase beats a generic built-in one at the
# same spot); token aliases and phrase translations merge
# with Band C entries first for the same reason.
from topics_bandc import (ALIASES_BANDC, TOKEN_ALIASES_BANDC,
                          DEV_PHRASES_BANDC, ROMAN_PHRASES_BANDC)

_ALIASES = ALIASES_BANDC + _ALIASES
_TOKEN_ALIASES = {**TOKEN_ALIASES_BANDC, **_TOKEN_ALIASES}
_DEV_PHRASES = DEV_PHRASES_BANDC + _DEV_PHRASES
_ROMAN_PHRASES = ROMAN_PHRASES_BANDC + _ROMAN_PHRASES


def _alias_match(mtext, toks):
    """Best alias hit for the whole question, or None.
    HCF+LCM together (a how-to ask about both) belong to the
    combined topic, not to whichever single alias sorts
    first."""
    if "hcf" in toks and "lcm" in toks:
        return _topic("hcf-and-lcm")
    # Trig token-set rule: sin+cos with an identity marker is
    # the identities topic; plain sin/cos/tan is ratios.
    if "sin" in toks and "cos" in toks:
        if toks & {"identity", "barabar", "sec", "cosec"}:
            return _topic("trigonometric-identities")
        if "tan" in toks:
            return _topic("trigonometric-ratios")
    if "trig" in toks and "identity" in toks:
        return _topic("trigonometric-identities")
    # Phrase aliases: the EARLIEST-occurring phrase wins —
    # students name the asked concept first and the context
    # second ("conjugate kya hota hai complex number ka?",
    # "two variable wali linear equations kese solve karte
    # hain?"); ties go to the longer, more specific phrase
    # ("linear equation" over "equation" at the same spot).
    best = None  # (position, -length, slug)
    for phrase, slug in _ALIASES:
        pos = mtext.find(phrase)
        if pos < 0:
            continue
        cand = (pos, -len(phrase), slug)
        if best is None or cand < best:
            best = cand
    if best is not None:
        hit = _topic(best[2])
        if hit is not None:
            return hit
    for tok, slug in _TOKEN_ALIASES.items():
        if tok in toks:
            hit = _topic(slug)
            if hit is not None:
                return hit
    return None


# ---------------------------------------------------------------------------
# MATCH (fallback): strict token-overlap scoring against
# topic names + chapters. A topic may serve only when at
# least TWO of its name tokens appear in the question and it
# is the UNIQUE best score — ties and one-token grazes fall
# through to the concepts.py card, exactly as today.
# ---------------------------------------------------------------------------

_STOP = {
    "what", "is", "the", "a", "an", "of", "are", "does", "do",
    "me", "ka", "ki", "ke", "hai", "hota", "hoti", "hote",
    "kya", "kaise", "kese", "batao", "btao", "samjhao",
    "samjha", "matlab", "aur", "please", "plz", "yr", "bhai",
    "guru", "sun", "na", "to", "hi", "bhi", "ek", "ye", "yeh",
    "wala", "wali", "simple", "words", "mein", "se", "par",
    "ko", "kitna", "kitni", "kab", "kyun", "kyu", "why",
    "how", "find", "solve", "calculate", "explain", "define",
    "meaning", "formula", "give", "tell", "about", "use",
    "used", "using", "value", "chapter", "topic", "maths",
    "math", "difference", "different", "antar", "fark",
    "kise", "kehte", "kahate", "hain", "hai", "bana", "bta",
    "do", "de", "kar", "karte", "hoga", "hogi", "chahiye",
    "aati", "aata", "jata", "jaata", "wala", "wali", "mera",
    "mere", "iska", "iska", "us", "is", "in", "on", "for",
    "and", "or", "between", "from", "with", "by",
}


def _name_tokens(topic):
    return set(_tokens(topic["name"] + " " +
                       topic["slug"].replace("-", " ")))


def _chapter_tokens(topic):
    return set(_tokens(topic["chapter"].replace("-", " ")))


_NAME_FILLER = {"of", "the", "a", "an", "and", "in", "on",
                "for", "from", "by", "to"}


def _score_match(toks):
    content = [t for t in toks if t not in _STOP]
    if not content:
        return None
    scored = []
    for cls, topic in _ORDERED:
        name_toks = _name_tokens(topic)
        hits = {t for t in content
                if _stem_hit(t, name_toks)}
        if len(hits) < 2:
            continue
        chap_hits = {t for t in content
                     if _stem_hit(t, _chapter_tokens(topic))}
        # Coverage: how much of the topic's own name the
        # question accounts for. It separates the canonical
        # topic ("Circumference and Area of a Circle") from
        # a narrower variant ("Area of a Circle Using
        # Diameter") when both match the same words.
        name_content = name_toks - _NAME_FILLER
        coverage = len(hits) / max(1, len(name_content))
        score = 2.0 * len(hits) + 1.0 * len(chap_hits) \
            + coverage
        scored.append((score, cls, topic))
    if not scored:
        return None
    scored.sort(key=lambda s: -s[0])
    top = scored[0]
    if top[0] < 4.0:
        return None
    # Unique winner required (same slug in two classes is
    # the same topic — that tie is fine).
    for other in scored[1:]:
        if other[0] == top[0] \
                and other[2]["slug"] != top[2]["slug"]:
            return None
    return (top[1], top[2])


def _match_side(text):
    """Match ONE side of a difference ask (alias, then strict
    scoring on the side's own tokens)."""
    toks = set(_tokens(text))
    hit = _alias_match(text, toks)
    if hit is not None:
        return hit
    return _score_match(toks)


# ---------------------------------------------------------------------------
# Difference asks: "X aur Y me kya antar hai", "difference
# between X and Y", "how is X different from Y".
# ---------------------------------------------------------------------------

_DIFF_SPLITTERS = [
    re.compile(r"difference between (.+?) and (.+)$"),
    re.compile(r"how is (.+?) different from (.+)$"),
    re.compile(r"(.+?) (?:aur|and|और) (.+?) (?:me |mein )?"
               r"(?:kya )?(?:antar|fark|difference)"),
    re.compile(r"(.+?) (?:vs\.?|versus) (.+)$"),
]
_DIFF_INTENT_RE = re.compile(
    r"antar|fark|difference|different|alag|अंतर")


def _clean_side(text):
    text = re.sub(r"\b(what|is|the|a|an|kya|hai|me|mein|"
                  r"batao|btao|samjhao|please|plz)\b", " ",
                  text)
    return re.sub(r"\s+", " ", text).strip(" ?.!")


def _difference_match(mtext):
    """(topicA, topicB) for a difference ask — the same topic
    twice when one combined topic covers both sides — or
    None."""
    if not _DIFF_INTENT_RE.search(mtext):
        return None
    for rx in _DIFF_SPLITTERS:
        m = rx.search(mtext)
        if not m:
            continue
        side_a = _clean_side(m.group(1))
        side_b = _clean_side(m.group(2))
        if not side_a or not side_b:
            continue
        toks_a, toks_b = set(_tokens(side_a)), set(_tokens(side_b))
        # Known pairs first (combined topics / fixed pairs).
        for keys_a, keys_b, slugs in _DIFF_PAIRS:
            if (keys_a <= toks_a and keys_b <= toks_b) or \
                    (keys_a <= toks_b and keys_b <= toks_a):
                topics = [_topic(s) for s in slugs]
                if all(topics):
                    if len(topics) == 1:
                        return (topics[0], topics[0])
                    return (topics[0], topics[1])
        hit_a = _match_side(side_a)
        hit_b = _match_side(side_b)
        if hit_a is not None and hit_b is not None:
            if hit_a[1]["slug"] == hit_b[1]["slug"]:
                return (hit_a, hit_a)
            return (hit_a, hit_b)
        return None
    return None


# ---------------------------------------------------------------------------
# Answer builders — the topic's own content, in the standard
# result shape (plain steps + answer line; Wave 24 style).
# ---------------------------------------------------------------------------

def _single_result(cls_topic):
    cls, topic = cls_topic
    steps = list(topic["steps"])
    steps.append(f"Example: {topic['starter']}")
    steps.append(f"Example answer: {topic['answer']}")
    return {
        "type": "Concept",
        "op": "concept_topic",
        "answer": f"{topic['name']} — {topic['idea']}",
        "steps": steps,
        "fallback": True,
        "fallback_kind": "concept",
        "source": "topics",
        "concept_id": f"topic:{topic['slug']}",
        "topic_slug": topic["slug"],
        "topic_class": cls,
    }


def _difference_result(pair):
    (cls_a, a), (cls_b, b) = pair
    if a["slug"] == b["slug"]:
        return _single_result((cls_a, a))
    steps = [f"{b['name']} — {b['idea']}",
             f"Example ({a['name']}): {a['starter']}",
             f"Answer: {a['answer']}",
             f"Example ({b['name']}): {b['starter']}",
             f"Answer: {b['answer']}"]
    return {
        "type": "Concept",
        "op": "concept_topic",
        "answer": f"{a['name']} — {a['idea']}",
        "steps": steps,
        "fallback": True,
        "fallback_kind": "concept",
        "source": "topics",
        "concept_id": f"topic:{a['slug']}+{b['slug']}",
        "topic_slug": a["slug"],
        "topic_class": cls_a,
        "topic_slug_b": b["slug"],
        "topic_class_b": cls_b,
    }


# ---------------------------------------------------------------------------
# The entry point fallback.py calls.
# ---------------------------------------------------------------------------

def topic_concept_result(question):
    """The topics-library answer for a genuine concept ask,
    or None (the caller then runs exactly today's layers).

    Order inside: veto first (a concrete problem is never
    captured, whatever its words), then the gate (a concept
    shape is required), then difference asks, then the
    single-topic match (aliases, then strict scoring)."""
    if not question:
        return None
    mtext = _match_text(question)
    if _vetoed(question, mtext):
        return None
    if not _has_gate(question, mtext):
        return None
    pair = _difference_match(mtext)
    if pair is not None:
        return _difference_result(pair)
    toks = set(_tokens(mtext))
    hit = _alias_match(mtext, toks)
    if hit is None:
        hit = _score_match(toks)
    if hit is None:
        return None
    return _single_result(hit)


__all__ = ["topic_concept_result"]


# --- Band B topics expansion (Classes 9-10) -------------------------------
# Register the new topics' chat aliases. Any phrase that already
# exists in _ALIASES is dropped, so a Band B alias can never
# steal an older route.
try:
    from topics_bandb import ALIASES_BANDB as _ALIASES_BANDB

    _bandb_phrases = {phrase for phrase, _slug in _ALIASES}
    _ALIASES.extend(
        (phrase, slug)
        for phrase, slug in _ALIASES_BANDB
        if phrase not in _bandb_phrases
    )
except Exception:  # pragma: no cover - topics module is optional
    pass
# --- end Band B wiring -----------------------------------------------------
