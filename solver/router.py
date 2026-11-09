"""Question router: normalises Hinglish, detects the topic, dispatches
to the right solver, and falls back to a generic SymPy solve/simplify.

Every result is a dict with at least: type, answer, steps.
"""
import re

from .algebra import solve_algebra
from .arithmetic import solve_arithmetic
from .calculus import solve_calculus
from .complex_numbers import solve_complex
from .exponents_logs import solve_exponents_logs
from .geometry import solve_geometry
from .linear_algebra import solve_linear_algebra
from .number_theory import solve_number_theory
from .plotting import solve_plot
from .sequences import solve_sequences
from .sets_basics import solve_sets
from .statistics import solve_statistics
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

    # Divide: "20 ko 4 se bhaag (do)", "20 bhaag 4"
    m = re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)\s+se\s+bhaag",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+bhaag\s+(\d+(?:\.\d+)?)", ql)
    if m:
        return f"{m.group(1)} / {m.group(2)}"

    # Subtract: "20 mein se 7 ghatana/ghatavo"
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+mein?\s+se\s+(\d+(?:\.\d+)?)\s+ghatana", ql)
    if m:
        return f"{m.group(1)} - {m.group(2)}"

    # Add: "5 aur 3 ko jodo", "5 mein 3 jodo", "5 jodo 3"
    m = re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ko\s+jodo",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+mein\s+(\d+(?:\.\d+)?)\s+jodo", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+jodo\s+(\d+(?:\.\d+)?)", ql)
    if m:
        return f"{m.group(1)} + {m.group(2)}"

    # "ka maan (nikalo)" = "the value of": strip it and route normally.
    t = re.sub(r"\s+ka\s+maan\b.*$", "", ql).strip()
    t = re.sub(r"\s+(kitna\s+hoga|batao|nikalo|karo|kar\s+do)\s*$", "", t)
    return t.strip()


# --------------------------------------------------------------------------
# Intent detection
# --------------------------------------------------------------------------
def route_intent(question: str) -> str:
    q = question.lower()

    if re.search(r"\b(plot|graph|draw)\b", q):
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
    if re.search(
            r"(dy/dx|y\'|differential|dsolve|derivative|differentiate|"
            r"integration|integral|integrate|\blimit\b|\blim\b|d/d|"
            r"partial)", q):
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
    if re.search(r"\b(prime|gcd|hcf|lcm|modulo|divisible)\b", q) or \
            re.search(r"(?<![a-z])mod(?![a-z])", q):
        return "number_theory"
    if re.search(r"\bfactor", q) and not re.search(r"[a-z]", re.sub(
            r"\bfactors?\b|\bfactorise\b|\bfactorize\b|\bof\b|"
            r"\bthe\b|\bis\b|\bplease\b", "", q)):
        return "number_theory"

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
}

_TOPICS = (
    "arithmetic & percentages, algebra (equations, systems, "
    "inequalities, factor/expand/simplify), exponents & logarithms, "
    "trigonometry, calculus (limits, derivatives, integrals, basic "
    "ODEs), linear algebra (matrices), geometry & coordinate geometry, "
    "statistics & probability, number theory, sequences & series, "
    "complex numbers, sets, unit conversion, word problems and graphs"
)


def solve_question(question: str):
    original = question
    translated = normalize_hinglish(question)
    was_translated = translated.strip().lower() != question.strip().lower()
    working = translated if was_translated else question

    # Explicit unit conversion ("convert 5 km to miles", temperatures):
    # try it directly first; solve_units returns None when it is not a
    # conversion, and we then fall through to normal routing.
    if re.search(r"\bconvert\b", working, re.I):
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out

    intent = route_intent(working)

    if intent == "units":
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "arithmetic"

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


__all__ = ["solve_question", "route_intent", "normalize_hinglish"]
