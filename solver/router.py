"""Question router: normalises Hinglish, detects the topic, dispatches
to the right solver, and falls back to a generic SymPy solve/simplify.

Every result is a dict with at least: type, answer, steps.
"""
import re

from .algebra import solve_algebra
from .answer_cache import get_cached, put_cached
from .applied import solve_applied
from .arithmetic import solve_arithmetic
from .calculus import solve_calculus
from .complex_numbers import solve_complex
from .distributions import solve_distributions
from .exponents_logs import solve_exponents_logs
from .geometry import solve_geometry
from .junior import solve_junior
from .linear_algebra import solve_linear_algebra
from .number_theory import solve_number_theory
from .plotting import solve_plot
from .sequences import solve_sequences
from .sets_basics import solve_sets
from .statistics import solve_statistics
from .transforms import solve_transforms
from .trigonometry import solve_trigonometry
from .units import solve_units
from .word_problems import solve_word_problem

# --------------------------------------------------------------------------
# Hinglish normalisation:  "5 aur 3 ko jodo" -> "5 + 3",
# "240 ka 15 pratishat" -> "15% of 240",  "2, 4, 6 ka ausat" -> mean, ...
# --------------------------------------------------------------------------
def normalize_hinglish(question: str) -> str:
    q = " " + question.strip() + " "
    ql = q.lower()

    # Percentage: "240 ka 15 pratishat (kitna hoga)" -> "15% of 240"
    m = re.search(r"(\d+(?:\.\d+)?)\s+ka\s+(\d+(?:\.\d+)?)\s+pratishat",
                  ql)
    if m:
        return f"{m.group(2)}% of {m.group(1)}"

    # Average: "2, 4, 6 ka ausat" -> "mean of 2, 4, 6"
    m = re.search(r"([\d][\d\s,\.]*?)\s+ka\s+ausat", ql)
    if m:
        return f"mean of {m.group(1).strip()}"

    # Multiply: "4 guna 5", "4 aur 5 ka guna", "4 ko 5 se guna"
    m = re.search(r"(\d+(?:\.\d+)?)\s*guna\s*(\d+(?:\.\d+)?)", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+guna",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)\s+se\s+guna",
                  ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"

    # Divide: "20 ko 4 se bhaag (do)", "20 bhaag 4",
    # "20 aur 4 ka bhaag" (noun form — same gap as "ka jod", below)
    m = re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)\s+se\s+bhaag",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+bhaag\s+(\d+(?:\.\d+)?)", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+bhaag\b",
                  ql)
    if m:
        return f"{m.group(1)} / {m.group(2)}"

    # Subtract: "20 mein se 7 ghatana/ghatavo",
    # "27 aur 15 ka ghata/ghatav" (noun form — same gap as "ka jod")
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+mein?\s+se\s+(\d+(?:\.\d+)?)\s+ghatana", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+"
                     r"(?:ghata|ghatav|ghataav)\b", ql)
    if m:
        return f"{m.group(1)} - {m.group(2)}"

    # Add: "5 aur 3 ko jodo", "5 mein 3 jodo", "5 jodo 3",
    # "15 aur 27 ka jod (kitna hoga/hai)", "15 aur 27 (ko) jodkar /
    # jod ke batao", "15 aur 27 jodo". The noun form "ka jod" was
    # missing (live bug, 12 Nov 2026): the question fell through to
    # the SymPy expression parser, which read "jod" as the variables
    # j*o*d next to 15*27 and answered "405*d*j*o" instead of 42.
    m = re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ko\s+jodo",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+mein\s+(\d+(?:\.\d+)?)\s+jodo", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+jodo\s+(\d+(?:\.\d+)?)", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+jod\b",
                     ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+"
                  r"(?:ko\s+)?jodkar\b", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+"
                  r"(?:ko\s+)?jod\s+ke\b", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+jodo\b", ql)
    if m:
        return f"{m.group(1)} + {m.group(2)}"

    # "ka maan (nikalo)" = "the value of": strip it and route normally.
    t = re.sub(r"\s+ka\s+maan\b.*$", "", ql).strip()
    t = re.sub(r"\s+(kitna\s+hoga|batao|nikalo|karo|kar\s+do)\s*$", "", t)
    return t.strip()


# --------------------------------------------------------------------------
# Wave 20 (Suraj, 12 Nov 2026): science-scope guard. Ganitra is
# MATHS-ONLY, but a Physics question ("refractive index ... speed
# of light ... 2 x 10^8 m/s") used to be force-fit into a junior
# maths intent / salvage fragment and answered with nonsense.
# These are SCIENCE-SPECIFIC signals — bare "speed" is NOT one
# (speed-distance-time sums are real maths), and neither is bare
# "current" or "element" (maths uses both legitimately). The
# router uses this to refuse the weak junior intent for such
# questions, and fallback.py uses it to answer honestly instead
# of salvaging a fake "maths part".
# --------------------------------------------------------------------------
_SCIENCE_RE = re.compile(
    r"(refractive|speed\s+of\s+light|ray\s+of\s+light|light\s+ray|"
    r"photosynthesis|velocity|acceleration|\bforce\b|newtons?\b|"
    r"voltage|ampere|electric\s+current|resistance|ohms?\b|"
    r"chemical|atom|atomic|molecule|electron|proton|neutron|"
    r"friction|momentum|gravity|gravitational|wavelength|"
    r"circuit|capacitor|kinetic\s+energy|potential\s+energy)",
    re.I)


def has_science_signal(question: str) -> bool:
    return bool(_SCIENCE_RE.search(str(question or "")))


# --------------------------------------------------------------------------
# Intent detection
# --------------------------------------------------------------------------
def route_intent(question: str) -> str:
    q = question.lower()

    # Probability distributions (before statistics: "binomial" with
    # n=/p= belongs here, plain probability stories stay statistics).
    if "poisson" in q or "normal distribution" in q \
            or "z-score" in q or "z score" in q:
        return "distributions"
    if "binomial" in q and re.search(r"\bn\s*=", q) and \
            re.search(r"\bp\s*=", q):
        return "distributions"
    if re.search(r"\bpercentile\b", q) and re.search(
            r"(mean|sd|sigma|standard deviation)", q):
        return "distributions"

    # Transforms & series (before calculus/algebra: "series" and
    # "partial fractions" would otherwise fall through).
    if "laplace" in q or "partial fraction" in q or \
            re.search(r"\b(taylor|maclaurin)\b", q) or \
            re.search(r"series\s+expansion", q) or \
            re.search(r"expansion\s+of", q):
        return "transforms"

    if re.search(r"\b(plot|graph|draw)\b", q) and not re.search(
            r"\bintegrat", q):
        return "plot"

    # Unit conversion: explicit "convert" is handled in solve_question via
    # solve_units() first; here match "<number> <unit> to/in <unit>".
    if re.search(
            r"\d\s*(km|cm|mm|miles?|kg|grams?|litres?|liters?|hours?|"
            r"minutes?|seconds?|inches|feet|yards?|pounds?|ounces?|"
            r"hectares?|acres?)\b.{0,12}?\b(to|in)\b", q):
        return "units"

    # Calculus. Word boundaries so words like "derivative" are not
    # mangled mid-word by solvers ("deriv" must not eat "derivative").
    # Also catch "integrate ... and show the graph" style requests
    # and d2y/dx2-style second-order ODE notation.
    if re.search(
            r"(dy/dx|d2y|y\'|differential|dsolve|derivative|"
            r"differentiate|integration|integral|integrate|"
            r"\blimit\b|\blim\b|d/d|partial)", q) or re.search(
            r"\bintegrat\w*\b.+\b(graph|shade|plot)\b", q):
        return "calculus"

    # Linear algebra
    if "[[" in q or re.search(
            r"\b(matrix|determinant|eigen|inverse|transpose|rank|trace)\b",
            q):
        return "linear_algebra"

    # Sets
    if "{" in q and re.search(r"\b(union|intersection|difference)\b", q):
        return "sets"

    # Trigonometry (incl. inverse functions like arcsin)
    if re.search(
            r"(arc\s*(sin|cos|tan)|\b(sin|cos|tan)\s*\^\s*\(?\s*-1|"
            r"inverse\s+(sin|cos|tan)|\ba(sin|cos|tan)\b)", q) or re.search(
            r"\b(sin|cos|tan|cot|sec|csc|cosec|sine|cosine|tangent|"
            r"trigonometr\w*)\b", q) or "trig" in q:
        return "trigonometry"

    # Counting notation: C(5,2), P(5,2), 5C2, 5P2
    if re.search(r"\b[CP]\s*\(\s*\d+\s*,\s*\d+\s*\)", question) or \
            re.search(r"\d+\s*[CP]\s*\d+", question):
        return "statistics"

    # Statistics & probability ("mode" as a standalone word only, so
    # "model" etc. are not hijacked; dice handled by word boundary)
    if re.search(
            r"(probabilit|permutation|combination|factorial|\bmean\b|"
            r"median|\bmode\b|standard deviation|variance|\bdice\b|"
            r"\bdie\b|coin|choose|arrange)", q):
        return "statistics"

    # Geometry
    if re.search(
            r"(\barea\b|perimeter|volume|circumference|surface area|"
            r"distance between|midpoint|slope|hypotenuse|equation of)", q):
        return "geometry"

    # Sequences & series
    if re.search(
            r"(\bap\b|\bgp\b|arithmetic (progression|series|sequence)|"
            r"geometric (progression|series|sequence)|nth term|"
            r"sum of (the )?first|sum of .* series)",
            q) or re.search(r"\d+\s*(st|nd|rd|th)\s+term", q):
        return "sequences"

    # Complex numbers (bare "i" expressions need digits around the i)
    if re.search(r"\bcomplex\b|conjugate|modulus|argument of|"
                 r"real part|imaginary part", q) or (
            "i" in q and re.search(r"\d\s*i\b|\bi\s*[\+\)\*]|\(\s*\d+\s*[\+\-]\s*\d+\s*i", q)):
        return "complex"

    # Logarithms / exponents (before algebra: log equations contain '=')
    if re.search(r"\b(log|ln|logarithm|antilog)\b", q):
        return "exponents_logs"

    # Number theory. "mod" must be a standalone token so words like
    # "mode"/"model" are not matched; factor-of-a-number check: strip the
    # word "factor..." and filler; if no letters remain it is a number.
    # Wave 13: "prime numbers between A and B" is a LIST question —
    # the junior solver owns it (the single-number prime check
    # below cannot answer it).
    if re.search(r"\bprime\s+numbers?\s+(between|from)\b", q):
        return "junior"
    if re.search(r"\b(prime|gcd|hcf|lcm|modulo|divisible)\b", q) or \
            re.search(r"(?<![a-z])mod(?![a-z])", q):
        return "number_theory"
    if re.search(r"\bfactor", q) and not re.search(r"[a-z]", re.sub(
            r"\bfactors?\b|\bfactorise\b|\bfactorize\b|\bof\b|"
            r"\bthe\b|\bis\b|\bplease\b", "", q)):
        return "number_theory"

    # Wave 13 junior families (Classes 0-5). Deliberately
    # placed late: every established intent above keeps its
    # priority, and these triggers are phrase-specific. The
    # junior solver itself returns None when its stricter
    # patterns do not extract clean numbers (see solve_question
    # for the fallback).
    if re.search(
            r"(\bin\s+words\b|\bnumber\s+name\b|\bplace\s+value\b|"
            r"\bexpanded\s+form\b|\btable\s+of\s+\d|"
            r"\d\s+ka\s+table\b|\bhalf\s+of\s+\d|"
            r"\bquarter\s+of\s+\d|\d\s*/\s*\d\s+of\s+\d|"
            r"\bas\s+(a\s+)?decimal\b|\bin\s+decimal\b|"
            r"\bas\s+(a\s+)?fraction\b|"
            r"\bwhich\s+is\s+(bigger|greater|larger|smaller)\b|"
            r"\badd\s+\d|\bsubtract\s+\d|\bsum\s+of\s+\d|"
            r"\bdifference\s+between\s+\d|\bproduct\s+of\s+\d|"
            r"\bdivide\s+\d|\bmultiply\s+\d|"
            r"\bshared\s+equally\b|\bdivided\s+equally\b|"
            r"\bhow\s+many\s+months\s+in\s+\d|"
            r"\bminutes?\s+after\s+\d|\bhours?\s+after\s+\d|"
            r"\bfrom\s+\d{1,2}(?::\d{2})?\s*(am|pm)\s+to\s+\d|"
            r"\bhow\s+many\s+(sides|corners|vertices)\b|"
            r"\bshape\s+with\s+\d+\s+sides|\b\d\s*-\s*sided\b|"
            r"\bname\s+the\s+shape\b|\bodd\s+or\s+even\b|"
            r"\b(odd|even)\s+numbers?\s+(between|from)\b|"
            r"\bnext\s+number\b|\bwhat\s+comes\s+next\b|"
            r"\bcomes\s+next\s*:?\s*\d|\bmissing\s+number\b|"
            r"^\s*\d+\s+is\s+(odd|even)\b|"
            r"\bmultiples?\s+of\s+\d|\bfirst\s+\d+\s+multiples?\b|"
            r"\bprime\s+numbers?\s+(between|from)\b)", q) or \
            re.search(r"\bhas\s+(?:rs\.?\s+|₹\s*|rupees\s+)?"
                      r"\d+\b.{0,90}?\b(gives|gave|lost|loses|"
                      r"eats|ate|buys|bought|gets|got|sells|"
                      r"sold)\b", q) or \
            re.search(r"\d\s+\w+\s+(have|has|contain|contains)\s+"
                      r"\d.{0,40}?\beach\b", q) or \
            re.search(r"\bcost\s+of\s+\d.{0,40}?\beach\b", q) or \
            re.search(r"^\s*(what\s+is\s+)?\d{1,3}\s*(x|×)\s*"
                      r"\d{1,3}\s*\?*\s*$", q.strip()):
        return "junior"

    # Wave 13 applied families (Classes 6-12 gaps): ratio,
    # simple interest (all forms — solve_question falls back
    # to word_problems when applied returns None), profit &
    # loss, speed stories, word equations, discriminant.
    if re.search(
            r"(\bratio\b|\bsimple\s+interest\b|\bprofit\b|"
            r"\bloss\b|\bdiscriminant\b|"
            r"\bnature\s+of\s+(the\s+)?roots\b|"
            r"km/h\s+(to|in)\s+m/s|m/s\s+(to|in)\s+km/h|"
            r"\bnumber\s+(increased|decreased|multiplied)\s+by\b|"
            r"\b(twice|thrice|double)\s+(a\s+)?number\b|"
            r"\bsum\s+of\s+a\s+number\s+and\s+\d|"
            r"\bwhen\s+\d+\s+is\s+added\s+to\s+a\s+number\b|"
            r"\btravels?\b.{0,40}?\bkm\b|\bcovers\s+\d+\s*km\b)",
            q):
        return "applied"

    # Word problems
    if re.search(
            r"(increase by|decrease by|sum is|product is|"
            r"simple interest)", q) or re.search(
                r"\d\s*(km/h|mph|m/s)\s+for\s+\d", q):
        return "word_problems"

    # Algebra: equations, inequalities, factor/expand/simplify commands
    if "=" in q or re.search(r"(<=|>=|<|>)", q) or re.search(
            r"\b(solve|factorise|factorize|factor|expand|simplify)\b", q):
        return "algebra"

    return "arithmetic"


_SOLVERS = {
    "arithmetic": solve_arithmetic,
    "algebra": solve_algebra,
    "junior": solve_junior,
    "applied": solve_applied,
    "calculus": solve_calculus,
    "linear_algebra": solve_linear_algebra,
    "number_theory": solve_number_theory,
    "word_problems": solve_word_problem,
    "trigonometry": solve_trigonometry,
    "statistics": solve_statistics,
    "geometry": solve_geometry,
    "sequences": solve_sequences,
    "complex": solve_complex,
    "sets": solve_sets,
    "exponents_logs": solve_exponents_logs,
    "plot": solve_plot,
    "distributions": solve_distributions,
    "transforms": solve_transforms,
}

_TOPICS = (
    "junior maths for Classes 0-5 (number names, place value, "
    "tables, story sums, fraction basics, money, clock and shape "
    "facts), arithmetic & percentages, algebra (equations, systems, "
    "inequalities, factor/expand/simplify), exponents & logarithms, "
    "trigonometry, calculus (limits, derivatives, integrals, ODEs "
    "incl. second-order and initial conditions), Laplace transforms "
    "and series, linear algebra (matrices), geometry & coordinate "
    "geometry, statistics & probability (incl. normal, Poisson and "
    "binomial distributions), number theory, sequences & series, "
    "ratio & proportion, simple interest, profit & loss, speed, "
    "complex numbers, sets, unit conversion, word problems and graphs "
    "(one or two functions, shaded integral area)"
)


def solve_question(question: str):
    """Cached entry point (Kami audit 2c-1): repeat questions are
    served from the in-memory answer cache at zero CPU cost; the
    first ask, and anything uncacheable, runs the solver below."""
    cached = get_cached(question)
    if cached is not None:
        return cached
    result = _solve_question_uncached(question)
    put_cached(question, result)
    return result


def _solve_question_uncached(question: str):
    original = question
    translated = normalize_hinglish(question)
    was_translated = translated.strip().lower() != question.strip().lower()
    working = translated if was_translated else question

    # Explicit unit conversion ("convert 5 km to miles", temperatures):
    # try it directly first; solve_units returns None when it is not a
    # conversion, and we then fall through to normal routing.
    # Wave 13: "how many minutes in 3 hours" is the same conversion
    # asked as a question — solve_units validates the units itself
    # and returns None for non-unit "how many" questions.
    if re.search(r"\bconvert\b", working, re.I) or re.search(
            r"\bhow\s+many\b", working, re.I):
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out

    intent = route_intent(working)

    # Wave 20 science guard: a science question whose ONLY match
    # is a weak junior phrase must never be force-solved by the
    # Classes 0-5 solver. Downgrade to arithmetic (which honestly
    # fails), so the app layer's Wave-18/20 fallback can give the
    # kind "this is Science, Ganitra is for Maths" reply instead
    # of a made-up junior answer.
    if intent == "junior" and has_science_signal(working):
        intent = "arithmetic"

    if intent == "units":
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        # Wave 13: the units pattern also catches speed stories
        # ("180 km in 3 hours") and km/h <-> m/s requests, which
        # are not unit conversions — the applied solver owns them.
        out = solve_applied(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "arithmetic"

    # Wave 13: the unitary-cost story ("5 pens cost Rs 60, cost
    # of 8 pens") names no intent keyword, so when the classic
    # pipeline cannot even parse the question, give the applied
    # patterns one chance before reporting the error.
    if intent in ("arithmetic", "algebra"):
        probe_solver = _SOLVERS.get(intent, solve_arithmetic)
        try:
            probe = probe_solver(working)
        except Exception:
            probe = None
        if probe is None or (isinstance(probe, dict)
                             and probe.get("op") == "error"):
            alt = solve_applied(working)
            if alt is not None:
                if was_translated:
                    alt["interpreted_as"] = translated
                return alt

    # Wave 13 solvers return None when their strict patterns do
    # not match; fall back to the closest established pipeline
    # instead of failing (junior -> arithmetic, applied -> the
    # classic word-problem patterns).
    if intent == "junior":
        out = solve_junior(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "arithmetic"

    if intent == "applied":
        out = solve_applied(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "word_problems"

    solver = _SOLVERS.get(intent, solve_arithmetic)
    try:
        result = solver(working)
    except Exception as e:
        result = {"type": intent, "op": "error",
                  "answer": f"Could not solve this one: {e}",
                  "steps": []}
    if isinstance(result, dict):
        if was_translated:
            result.setdefault("interpreted_as", translated)
        result.setdefault("steps", [])
        result.setdefault("answer", "")
        return result
    # Safety net: a solver returned a bare string.
    return {"type": intent, "answer": str(result), "steps": []}


__all__ = ["solve_question", "route_intent", "normalize_hinglish",
           "has_science_signal"]
