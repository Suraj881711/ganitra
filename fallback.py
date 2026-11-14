"""Wave 18: the no-dead-end answer layer.

Suraj's direction (10 Nov 2026): "Muse or ChatGPT ki tarah
comfortable hona chahiye, har ek question ka answer milna
chahiye." The rule-based solver is exact but narrow: concept
asks ("pythagoras theorem kya hai"), greetings, messy word
problems and off-topic questions used to end at the friendly
error card — or worse, at a letter-multiplied nonsense "answer"
(sympy happily turns unknown words into a product of letters).

`with_fallback(question, result)` sits between the solver and
the routes (api.py's _solve_friendly and app.py's classic
/solve + /photo-solve). A REAL solver answer is returned
untouched. Anything else is routed through the layers:

  0. greetings / small talk (checked before everything — the
     solver turns "hi" into "h*i", which must never be shown)
  0b. known non-maths topics (capital of India, cricket score,
     photosynthesis...) — a friendly maths-only reply, never a
     fake answer
  1. salvage: strip conversational filler (batao, samjhao,
     please, "my homework says..."), extract an embedded
     expression/equation and solve THAT; the reply says plainly
     that it solved the maths part of the question
  2. concepts: the curated concepts.py library (formula + one
     worked example) for "what is X / X kya hai / X ka formula"
  3. topic guess: a similar SOLVED example with different
     numbers, honestly labelled "similar example", plus one
     short line asking for the exact missing detail
  4. vague / gibberish / guide: a friendly reply that shows how
     to ask, with a tiny solved example — never a bare error

Wave 39 adds one layer to this chain, between the science
guard and salvage: the Verified Data Bank (bank.py). When the
solver could not really answer and the question is an EXACT
normalised match with a banked item, the item's own steps +
final answer are served instead of a salvaged fragment, a
similar example or the general guide — every banked answer was
independently SymPy-verified before banking. A real solver
answer is still served untouched above it, a science question
never reaches it, and a miss changes nothing: the rest of the
flow is byte-for-byte the pre-Wave-39 behaviour.

HONESTY RULE: a fallback result is flagged (fallback=True,
fallback_kind=...) and never presents a guessed or similar
answer as the exact answer to the student's question.

Result dicts keep the solver's shape ({type, op, answer,
steps, ...}) so every existing renderer (chat bubble, answer
page, print, download, history) works unchanged: the gibberish
guard in i18n only fires for type arithmetic/algebra with
op == "simplify", which no fallback result ever uses.
"""
import re

from concepts import find_concept
from i18n import solve_failed
from solver.router import has_science_signal, solve_question

# ---------------------------------------------------------------------------
# Detectors for "the solver did not really answer"
# ---------------------------------------------------------------------------

# Soft non-answers: the solver asking for more input instead of
# answering ("Tell me the data...", "I need the first term...",
# the word-problem catch-all). These are not answers, so the
# fallback may improve on them — but ONLY via its honest layers.
_SOFT_PREFIXES = (
    "tell me", "i need", "no word-problem pattern matched",
    "give a number", "give me", "please tell", "please give",
    "could not", "enter a", "try a form",
)


def _answer_text(result):
    return str((result or {}).get("answer", "") or "")


def _is_soft(result):
    ans = _answer_text(result).strip().lower()
    return bool(ans) and ans.startswith(_SOFT_PREFIXES)


_SYMBOLIC_COMMANDS = ("simplify", "expand", "factor", "factorise",
                      "factorize", "collect")


def _is_junk(question, result):
    """Letter-soup detection: sympy turned the question's words
    into a product of single letters ("what is pythagoras
    theorem" -> a**2*e**2*g*h**2*...). A genuine symbolic answer
    almost never mentions 4+ DISTINCT single letters, and real
    simplify/expand/factor asks are excluded up front."""
    q = str(question or "").lower()
    if any(cmd in q for cmd in _SYMBOLIC_COMMANDS):
        return False
    ans = _answer_text(result)
    letters = set(re.findall(r"(?<![A-Za-z])[a-z](?![A-Za-z])", ans))
    if any(mark in ans for mark in ("**", "·", "^")):
        return len(ans) >= 8 and len(letters) >= 4
    # Plain-product form: "a*b*d*m*o*s" — the whole answer is
    # single letters multiplied together, 5+ distinct letters.
    compact = ans.replace(" ", "").replace("·", "*")
    if re.fullmatch(r"[a-z](\*\*\d+)?(\*[a-z](\*\*\d+)?)+",
                    compact):
        return len(letters) >= 5
    return False


def _is_real(question, result):
    """True when the solver's result may be shown as-is."""
    if not isinstance(result, dict):
        return False
    if solve_failed(question, result):
        return False
    if _is_soft(result) or _is_junk(question, result):
        return False
    return bool(_answer_text(result).strip())


# ---------------------------------------------------------------------------
# Layer 0: greetings & small talk; Layer 0b: known non-maths topics
# ---------------------------------------------------------------------------

_GREETING_EXACT = {
    "hi", "hii", "hiii", "hello", "helo", "hey", "namaste",
    "namaskar", "kaise ho", "how are you", "kese ho",
    "thank you", "thanks", "dhanyavaad", "dhanyavad", "shukriya",
    "tum kaun ho", "who are you", "your name", "tumhara naam",
    "tumhara naam kya hai", "good morning", "good evening",
    "good afternoon", "good night", "bye", "ok", "okay",
    "haan", "yes", "no", "nahi",
}

_GREETING_STARTS = ("hello", "hi ", "hey ", "namaste", "good morning",
                    "good evening", "good afternoon", "thank you",
                    "thanks", "kaise ho", "how are you")

_HINDI_MARKERS = ("kya", "hai", "ho", "kaise", "tum", "mera",
                  "ka", "ki", "batao", "samjhao", "dhanyavaad",
                  "shukriya", "nahi", "haan", "namaste", "ganit")


def _looks_hindi(question):
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return True
    words = set(re.findall(r"[a-z]+", q.lower()))
    return bool(words & set(_HINDI_MARKERS))


def _greeting_kind(question):
    """Return a greeting key when the WHOLE message (short, no
    digits, no operators) is small talk, else None. A greeting
    glued to a real question ("hello, solve 2+2") is NOT small
    talk — the salvage layer handles those."""
    q = str(question or "").strip().lower()
    q = re.sub(r"[!?.,;:\"]+", "", q).strip()
    if not q or any(ch.isdigit() for ch in q):
        return None
    if any(ch in q for ch in "+-*/^=<>%"):
        return None
    if len(q.split()) > 5:
        return None
    if q in _GREETING_EXACT:
        return q
    for start in _GREETING_STARTS:
        if q.startswith(start):
            return start.strip()
    return None


_NONMATHS_KEYWORDS = (
    "capital of", "capital kya", "rajdhaani", "prime minister",
    "pradhan mantri", "president of", "cricket", "football",
    "movie", "film", "song", "gaana", "weather", "mausam",
    "photosynthesis", "prakash sanshleshan", "sky blue",
    "aasmaan neela", "news", "khabar", "meaning of love",
    "girlfriend", "boyfriend", "joke", "chutkula",
    "who won", "match ka score", "score kya",
)


def _is_nonmaths(question):
    q = str(question or "").lower()
    if any(ch.isdigit() for ch in q) and any(
            ch in q for ch in "+-*/^=%"):
        return False  # an actual calculation rides along; not ours
    return any(kw in q for kw in _NONMATHS_KEYWORDS)


def _friendly_result(kind, answer, steps, hindi):
    return {
        "type": "Ganitra",
        "op": kind,
        "answer": answer,
        "steps": steps,
        "fallback": True,
        "fallback_kind": kind,
    }


def _greeting_result(question, hindi):
    g = _greeting_kind(question)
    if g is None:
        return None
    if g in ("thank you", "thanks", "dhanyavaad", "dhanyavad",
             "shukriya"):
        if hindi:
            return _friendly_result(
                "greeting",
                "Koi baat nahi! 😊 Kuch aur maths ka sawal hai to "
                "bhejo, main hal karke deta hoon.",
                [], hindi)
        return _friendly_result(
            "greeting",
            "You're welcome! 😊 Send me any maths question and "
            "I'll solve it step by step.",
            [], hindi)
    if g in ("tum kaun ho", "who are you", "your name",
             "tumhara naam", "tumhara naam kya hai"):
        if hindi:
            return _friendly_result(
                "greeting",
                "Main Ganitra hoon — tumhara maths dost. Koi bhi "
                "ganit ka sawal likho, photo bhejo ya bolkar puchho; "
                "main step-by-step hal dunga.",
                [], hindi)
        return _friendly_result(
            "greeting",
            "I am Ganitra — your maths friend. Type, speak or "
            "photograph any maths question and I'll solve it step "
            "by step.",
            [], hindi)
    if g in ("bye",):
        return _friendly_result(
            "greeting",
            "Bye! 👋 Jab bhi maths me atak jao, main yahi hoon.",
            [], hindi)
    if hindi:
        return _friendly_result(
            "greeting",
            "Namaste! 😊 Main bilkul theek hoon. Apna maths ka "
            "sawal bhejo — jaise '2x + 3 = 7' ya '240 ka 15% "
            "kitna hoga' — main step-by-step hal dunga.",
            [], hindi)
    return _friendly_result(
        "greeting",
        "Hello! 😊 I'm doing great. Send me a maths question — "
        "like 'solve 2x + 3 = 7' or 'what is 15% of 240' — and "
        "I'll solve it step by step.",
        [], hindi)


def _nonmaths_result(hindi):
    if hindi:
        return _friendly_result(
            "nonmaths",
            "Ye sawal maths ka nahi hai — main sirf ganit ke sawal "
            "hal karta hoon. 😊 Koi maths ka sawal bhejo, jaise "
            "'sin 30 ka maan' ya 'x^2 - 5x + 6 = 0'; main turant "
            "step-by-step hal dunga.",
            [], hindi)
    return _friendly_result(
        "nonmaths",
        "That's not a maths question — I only solve maths. 😊 "
        "Try me with something like 'sin 30' or 'solve x^2 - 5x "
        "+ 6 = 0' and I'll solve it step by step.",
        [], hindi)


# ---------------------------------------------------------------------------
# Layer 0c (Wave 20, Suraj 12 Nov 2026): SCIENCE questions. A
# Physics/Chemistry/Biology question must get an honest
# "Ganitra is for Maths" reply plus the concept's formula as
# GUIDANCE — never a force-solved fake answer. (The reported
# case: a refractive-index question was salvaged into the
# fragment "2 x 10" from "2 x 10^8" and answered by the junior
# times-pair solver.) This layer runs only when the solver did
# NOT really answer, so genuine maths that merely mentions a
# science word (a calculus velocity problem the solver solves
# properly) is never disturbed.
# ---------------------------------------------------------------------------

def _science_result(question, hindi):
    q = str(question or "").lower()
    if "refractive" in q or "speed of light" in q \
            or "ray of light" in q or "light ray" in q:
        topic, steps = "optics", [
            "Formula (guidance): refractive index of B with "
            "respect to A, n = (speed of light in A) ÷ "
            "(speed of light in B).",
            "So speed in B = (speed in A) ÷ n — put your values "
            "into this formula and the Physics answer follows.",
        ]
        if hindi:
            topic_line = ("Ye Physics (Prakash / Optics) ka sawal "
                          "hai — Ganitra sirf Maths ke sawal hal "
                          "karta hai, isliye main iska nakli hal "
                          "nahi dunga. 😊")
        else:
            topic_line = ("This is a Physics (Light / Optics) "
                          "question — Ganitra only solves Maths, "
                          "so I won't fake an answer for it. 😊")
    elif any(w in q for w in ("velocity", "acceleration", "force",
                              "newton", "momentum", "friction",
                              "gravity", "kinetic energy",
                              "potential energy")):
        topic, steps = "motion", [
            "Useful formulas (guidance): speed v = distance ÷ "
            "time; acceleration a = (v − u) ÷ t; force F = "
            "mass × acceleration.",
        ]
        topic_line = ("This is a Physics (Motion / Force) "
                      "question — Ganitra only solves Maths, "
                      "so I won't fake an answer for it. 😊")
        if hindi:
            topic_line = ("Ye Physics (Gati / Bal) ka sawal hai "
                          "— Ganitra sirf Maths ke sawal hal "
                          "karta hai, isliye main iska nakli hal "
                          "nahi dunga. 😊")
    elif any(w in q for w in ("voltage", "ampere", "resistance",
                              "ohm", "electric current", "circuit",
                              "capacitor")):
        topic, steps = "electricity", [
            "Useful formula (guidance): Ohm's law — V = I × R "
            "(voltage = current × resistance).",
        ]
        topic_line = ("This is a Physics (Electricity) question "
                      "— Ganitra only solves Maths, so I won't "
                      "fake an answer for it. 😊")
        if hindi:
            topic_line = ("Ye Physics (Bijli / Electricity) ka "
                          "sawal hai — Ganitra sirf Maths ke sawal "
                          "hal karta hai, isliye main iska nakli "
                          "hal nahi dunga. 😊")
    else:
        topic, steps = "general", []
        topic_line = ("This is a Science question — Ganitra "
                      "only solves Maths, so I won't fake an "
                      "answer for it. 😊")
        if hindi:
            topic_line = ("Ye Science ka sawal hai — Ganitra "
                          "sirf Maths ke sawal hal karta hai, "
                          "isliye main iska nakli hal nahi "
                          "dunga. 😊")
    if hindi:
        steps = steps + [
            "Maths ka koi sawal ho to bhejo — jaise 'train ki "
            "speed' wala sum ya 'x^2 - 5x + 6 = 0' — main "
            "step-by-step hal dunga."]
    else:
        steps = steps + [
            "Send me any Maths question — like a train "
            "speed–distance sum or 'x^2 - 5x + 6 = 0' — and "
            "I'll solve it step by step."]
    return _friendly_result("science", topic_line, steps, hindi)


# ---------------------------------------------------------------------------
# Layer 1: salvage — strip the chatter, solve the maths inside
# ---------------------------------------------------------------------------

_FILLER_WORDS = {
    "please", "plz", "batao", "bata", "samjhao", "samjha", "do",
    "karo", "kar", "nikalo", "help", "me", "my", "homework",
    "says", "say", "question", "sawal", "wala", "wali", "hai",
    "kitna", "kitne", "hoga", "hoge", "chahiye", "mujhe", "mera",
    "mere", "find", "the", "value", "what", "is", "when", "tell",
    "usko", "isko", "yeh", "ye", "aur", "ka", "ki", "ke", "ko",
    "se", "me", "mein", "par", "bhi", "toh", "to", "a", "an",
    "of", "for", "solve", "this", "that", "it", "just", "can",
    "you", "could", "would", "dear", "teacher", "sir", "madam",
    "bhai", "bro", "yar", "yaar", "abhi", "jaldi", "zara",
    "thoda", "answer", "ans", "solution", "hal",
}


def _strip_filler(question):
    tokens = re.findall(r"[^\s]+", str(question or ""))
    kept = [t for t in tokens
            if t.strip(".,?!;:\"'").lower() not in _FILLER_WORDS]
    return " ".join(kept).strip(" .,?!;:")


_MATHY_TOKEN = re.compile(r"^[0-9a-zA-Z\.\+\-\*/\^\(\)%]+$")


def _mathy(token):
    """A token that can belong to an equation: only maths
    characters, and either it carries a digit, is an operator,
    or is a short symbol (x, x^2, 3x). Plain English/Hindi words
    ("when", "please", "batao") are never mathy — they bound the
    extraction."""
    t = token.strip(".,?!;:\"'")
    if not t or not _MATHY_TOKEN.match(t):
        return False
    if any(ch.isdigit() for ch in t):
        return True
    if t in ("+", "-", "*", "/", "=", "^", "(", ")", "x", "×"):
        return True
    return len(t) <= 3 and not t.isalpha() or (
        len(t) <= 3 and t.lower() in ("x", "y", "z", "a", "b"))


def _extract_equation(question):
    """Find "3x + 7 = 22" inside "my homework says find x when
    3x + 7 = 22 please batao": locate the '=' and expand token
    by token while the neighbours are mathy."""
    tokens = str(question or "").split()
    for i, tok in enumerate(tokens):
        if "=" not in tok:
            continue
        lo = i
        while lo > 0 and _mathy(tokens[lo - 1]):
            lo -= 1
        hi = i
        while hi < len(tokens) - 1 and _mathy(tokens[hi + 1]):
            hi += 1
        cand = " ".join(tokens[lo:hi + 1]).strip(" .,?!;:")
        if any(ch.isdigit() for ch in cand) and \
                any(ch.isalpha() for ch in cand.split("=")[0]):
            return cand
    return None


def _candidates(question):
    """Possible maths cores inside a messy question, most
    specific first: an equation, a percentage, an arithmetic
    chain (only when there is no equation — a chain inside an
    equation is a fragment, not the question), then the
    filler-stripped whole."""
    q = str(question or "")
    out = []

    def add(cand):
        cand = (cand or "").strip(" .,?!;:")
        if cand and cand not in out and any(ch.isdigit()
                                            for ch in cand):
            out.append(cand)

    equation = _extract_equation(q)
    if equation:
        add(equation)
    m = re.search(r"(\d+(?:\.\d+)?\s*%\s*of\s*\d+(?:\.\d+)?)", q,
                  re.I)
    if m:
        add(m.group(1))
    if not equation:
        for m in re.finditer(
                r"(\d+(?:\.\d+)?(?:\s*[-+\*/x×]\s*"
                r"\d+(?:\.\d+)?)+)", q):
            # Wave 20: a chain that runs straight into a "^" is
            # scientific notation, not a multiplication sum —
            # "2 x 10^8" must never be salvaged as "2 x 10".
            if q[m.end():].lstrip().startswith("^"):
                continue
            add(m.group(1))
    add(_strip_filler(q))
    return out


def _salvage(question, hindi):
    # Wave 20: never salvage a science question — its numbers
    # are not a maths sum hiding in the text (see Layer 0c).
    if has_science_signal(question):
        return None
    for cand in _candidates(question):
        if cand.strip().lower() == str(question).strip().lower():
            continue  # identical to the original: already failed
        try:
            result = solve_question(cand)
        except Exception:
            continue
        if _is_real(cand, result):
            note = (f"Solved the maths part of your question: "
                    f"{cand}")
            result = dict(result)
            result["steps"] = [note] + list(
                result.get("steps") or [])
            result["fallback"] = True
            result["fallback_kind"] = "salvage"
            result["salvaged_from"] = cand
            return result
    return None


# ---------------------------------------------------------------------------
# Layer 2: concepts
# ---------------------------------------------------------------------------

def _concept_result(question, hindi):
    entry = find_concept(question)
    if entry is None:
        return None
    ex = entry["example"]
    steps = [entry["explain"],
             f"Hinglish me: {entry['hinglish']}",
             f"Example: {ex['q']}"]
    steps.extend(ex["steps"])
    steps.append(f"Example answer: {ex['answer']}")
    return {
        "type": "Concept",
        "op": entry["id"],
        "answer": f"{entry['title']} — {entry['formula']}",
        "steps": steps,
        "fallback": True,
        "fallback_kind": "concept",
        "concept_id": entry["id"],
    }


# ---------------------------------------------------------------------------
# Layer 3: topic guess + a similar SOLVED example (honestly labelled)
# ---------------------------------------------------------------------------

_TOPIC_EXAMPLES = (
    (("train", "speed", "chaal", "distance", "doori", "yatra",
      "km/h", "kmh"),
     "Speed–Distance",
     "A train travels at 60 km/h for 2 hours. How far does it go?",
     "60 km/h for 2 hours"),
    (("interest", "byaj", "ब्याज", "bank"),
     "Simple Interest",
     "Find the simple interest on ₹1,000 at 5% for 2 years.",
     "simple interest on 1000 at 5% for 2 years"),
    (("percent", "%", "pratishat", "प्रतिशत", "discount"),
     "Percentage",
     "Find 15% of 240.",
     "15% of 240"),
    (("quadratic", "x^2", "x²"),
     "Quadratic Equations",
     "Solve x² - 7x + 12 = 0.",
     "x^2 - 7x + 12 = 0"),
    (("equation", "find x", "solve x", "samikaran"),
     "Equations",
     "Solve 2x + 3 = 11.",
     "2x + 3 = 11"),
    (("area", "kshetrafal", "क्षेत्रफल", "perimeter", "parimap"),
     "Area",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
    (("sin", "cos", "tan", "trig"),
     "Trigonometry",
     "Find the value of sin 30.",
     "sin 30"),
    (("mean", "average", "ausat", "median"),
     "Statistics",
     "Find the mean of 3, 6, 9, 12.",
     "mean of 3, 6, 9, 12"),
    (("rupee", "rupaye", "रुपये", "money", "paisa", "paise",
      "cost", "price", "keemat"),
     "Money Maths",
     "Find 15% of ₹200.",
     "15% of 200"),
    (("triangle", "tribhuj", "त्रिभुज"),
     "Triangles",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
)


def _similar_result(question, hindi):
    q = str(question or "").lower()
    for keywords, label, example_q, example_solve in _TOPIC_EXAMPLES:
        if any(kw in q for kw in keywords):
            try:
                solved = solve_question(example_solve)
            except Exception:
                solved = None
            if solved is not None and _is_real(example_solve,
                                               solved):
                if hindi:
                    head = ("Tumhare sawal ka exact hal abhi nahi "
                            "mila, lekin usi topic ka ek solved "
                            "example ye raha:")
                    ask = ("Apne sawal ki exact sankhyayen (numbers) "
                           "ek baar saaf-saaf likh kar bhejo, main "
                           "usi ka hal dunga.")
                else:
                    head = ("I couldn't solve your exact question "
                            "yet, but here is a solved example from "
                            "the same topic:")
                    ask = ("Now type your question once more with "
                           "its exact numbers, and I'll solve yours.")
                steps = [head, f"Similar example: {example_q}"]
                steps.extend(
                    str(s) for s in (solved.get("steps") or []))
                steps.append(ask)
                return {
                    "type": "Similar example",
                    "op": label,
                    "answer": (f"Similar example ({label}): "
                               f"{solved.get('answer', '')}"),
                    "steps": steps,
                    "fallback": True,
                    "fallback_kind": "similar",
                }
    return None


# ---------------------------------------------------------------------------
# Layer 4: vague asks, gibberish, and the general guide
# ---------------------------------------------------------------------------

_VAGUE_WORDS = {
    "samjhao", "samjha", "batao", "bata", "solve", "help",
    "explain", "ye", "yeh", "wala", "wali", "this", "that",
    "isko", "usko", "karo", "kar", "do", "please", "plz",
    "maths", "math", "ganit", "question", "sawal", "abhi",
    "kuch", "bhi", "ek", "the", "a", "an", "it", "me", "my",
}


def _is_vague(question):
    words = re.findall(r"[a-z]+", str(question or "").lower())
    if not words or len(words) > 6:
        return False
    if any(ch.isdigit() for ch in str(question or "")):
        return False
    return all(w in _VAGUE_WORDS for w in words)


_KNOWN_WORDS = _VAGUE_WORDS | _FILLER_WORDS | {
    "what", "is", "of", "the", "a", "an", "in", "on", "for",
    "and", "or", "to", "how", "why", "when", "which", "find",
    "value", "area", "volume", "radius", "circle", "square",
    "triangle", "rectangle", "angle", "degree", "degrees",
    "percent", "percentage", "probability", "derivative",
    "integral", "integrate", "limit", "equation", "root",
    "roots", "power", "cube", "prime", "factor", "factors",
    "expand", "simplify", "graph", "plot", "sin", "cos", "tan",
    "log", "mean", "mode", "median", "hcf", "lcm", "gcd",
    "theorem", "formula", "interest", "speed", "distance",
    "time", "number", "numbers", "sum", "product", "difference",
}


def _is_gibberish(question):
    q = str(question or "")
    if any(ch.isdigit() for ch in q):
        return False
    if any(ch in q for ch in "+-*/^=<>%"):
        return False
    words = [w for w in re.findall(r"[a-z]+", q.lower())
             if len(w) >= 3]
    if len(words) < 2:
        return False
    unknown = [w for w in words if w not in _KNOWN_WORDS]
    return len(unknown) >= 2 and len(unknown) == len(words)


def _guide_result(question, hindi, kind):
    if kind == "vague":
        if hindi:
            return _friendly_result(
                "vague",
                "Bilkul samjha dunga! 😊 Bas apna maths ka sawal "
                "poora likh kar bhejo — jaise 'solve 2x + 3 = 7' "
                "ya 'ek train 60 km/h se 2 ghante me kitni door "
                "jayegi'. Photo bhejoge to wo bhi chalega.",
                ["Example: '240 ka 15% kitna hoga' likhne par "
                 "main har step ke saath hal deta hoon."], hindi)
        return _friendly_result(
            "vague",
            "Of course I'll explain! 😊 Just send the full maths "
            "question — like 'solve 2x + 3 = 7' or 'a train goes "
            "60 km/h for 2 hours, how far does it go'. A photo "
            "of the question works too.",
            ["Tip: writing the numbers clearly ('15% of 240') "
             "gets you a full step-by-step solution."], hindi)
    if kind == "gibberish":
        if hindi:
            return _friendly_result(
                "gibberish",
                "Ye kuch samajh nahi aaya 😅 — lagta hai words "
                "idhar-udhar ho gaye hain. Apna maths ka sawal "
                "ek baar saaf-saaf likh kar bhejo, main turant "
                "hal dunga.",
                ["Aise likho: '2x + 3 = 7', 'sin 30', ya "
                 "'240 ka 15 pratishat'."], hindi)
        return _friendly_result(
            "gibberish",
            "Hmm, that didn't look like a maths question 😅 — "
            "the words seem jumbled. Type your maths question "
            "once more, clearly, and I'll solve it right away.",
            ["Try writing it like: '2x + 3 = 7', 'sin 30', or "
             "'15% of 240'."], hindi)
    if hindi:
        return _friendly_result(
            "guide",
            "Is sawal ka exact hal abhi mujhse nahi ban paya — "
            "maafi chahta hoon. 🙏 Ek baar sawal ko thoda saaf "
            "likh kar bhejo (numbers aur kya nikalna hai, bas "
            "itna), main poori koshish karunga.",
            ["Aise sawal main pakka hal karta hoon: samikaran "
             "(2x + 3 = 7), pratishat (15% of 240), sin/cos, "
             "kshetrafal, ausat, aur Class 0-12 ke roz ke sawal.",
             "Photo wala sawal bhej rahe ho to text ko ek baar "
             "check karke bhejo — kabhi-kabhi ek number galat "
             "padh liya jata hai."], hindi)
    return _friendly_result(
        "guide",
        "I couldn't solve this exact question yet — sorry about "
        "that. 🙏 Please type it once more a little more clearly "
        "(the numbers and what to find), and I'll give it my "
        "full try.",
        ["Questions I solve for sure: equations (2x + 3 = 7), "
         "percentages (15% of 240), sin/cos, areas, averages, "
         "and everyday Class 0-12 maths.",
         "If this came from a photo, check the read text once — "
         "sometimes one number gets misread."], hindi)


# ---------------------------------------------------------------------------
# Wave 37: the Gemini free-tier second brain (gemini_fallback.py)
# Wave 41: Groq (groq_fallback.py) joins as the second brain —
# consulted only when Gemini returned None.
# ---------------------------------------------------------------------------

# The fallback kinds that mean "the student's OWN question is
# still unanswered": a similar example, a concept card, or the
# general guide. Only these may be upgraded by an AI brain.
# Real solver answers, salvage solves, greetings, non-maths
# and science replies never reach the check at all (they
# return earlier), and vague/gibberish asks have no real
# question to send.
_GEMINI_KINDS = ("similar", "concept", "guide")


def _gemini_answer(question, hindi):
    """Ask Gemini for the student's own question. Lazy import
    so the module (and its env key) stays fully optional; ANY
    failure returns None and the honest Wave-18 fallback is
    served exactly as before."""
    try:
        from gemini_fallback import try_gemini_answer
        return try_gemini_answer(question,
                                 "hi" if hindi else None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wave 39: the Verified Data Bank (bank.py) — exact matches only
# ---------------------------------------------------------------------------

def _bank_answer(question):
    """The banked, SymPy-verified answer for this EXACT question
    (bank.lookup_result), or None. Lazy import + blanket guard,
    same pattern as the Gemini layer: the bank snapshot is an
    optional file and any failure must leave the Wave-18 flow
    exactly as it was."""
    try:
        from bank import lookup_result
        return lookup_result(question)
    except Exception:
        return None


def _groq_answer(question, hindi):
    """Wave 41: ask Groq for the student's own question —
    only ever called when Gemini returned None. Same contract
    as _gemini_answer: lazy import, ANY failure returns None
    and the honest Wave-18 fallback is served unchanged."""
    try:
        from groq_fallback import try_groq_answer
        return try_groq_answer(question,
                               "hi" if hindi else None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------

def with_fallback(question, result):
    """Return `result` unchanged when it is a real solver
    answer; otherwise return an honest fallback result (never
    None, never an error dict)."""
    hindi = _looks_hindi(question)

    # Layer 0 / 0b run before the solver result is even looked
    # at: the solver's letter-products for "hi" / "what is the
    # capital of india" are not answers at all.
    greeting = _greeting_result(question, hindi)
    if greeting is not None:
        return greeting
    if _is_nonmaths(question):
        return _nonmaths_result(hindi)

    if _is_real(question, result):
        return result

    # Wave 20, Layer 0c: a SCIENCE question the solver could not
    # really answer gets the honest maths-only reply + formula
    # guidance — BEFORE salvage, which would otherwise carve a
    # fake "maths part" out of it (the refractive-index case).
    if has_science_signal(question):
        return _science_result(question, hindi)

    # Wave 39: the Verified Data Bank exact-match layer. It sits
    # AFTER the science guard (a science question is never
    # served from the bank) and after a real solver answer has
    # been served untouched above — what it upgrades is the
    # fall-through: a question the solver could not really
    # answer, whose EXACT normalised text matches a banked item,
    # gets that item's SymPy-verified steps + final answer
    # instead of a salvaged fragment, a similar example or the
    # general guide. Exact-only, so it can never shadow the
    # solver for a non-identical question; on a miss the layers
    # below run exactly as before.
    banked = _bank_answer(question)
    if banked is not None:
        return banked

    # The solver did not really answer. Work the layers.
    salvaged = _salvage(question, hindi)
    if salvaged is not None:
        return salvaged

    concept = _concept_result(question, hindi)
    if concept is not None:
        result_out = concept
    else:
        similar = _similar_result(question, hindi)
        if similar is not None:
            result_out = similar
        elif _is_vague(question):
            result_out = _guide_result(question, hindi, "vague")
        elif _is_gibberish(question):
            result_out = _guide_result(question, hindi, "gibberish")
        else:
            result_out = _guide_result(question, hindi, "guide")

    # Wave 37: when the honest layers still could not answer
    # the student's own question (similar example, concept card
    # or the general guide), ask Gemini (free tier) before
    # settling — solver first, AI only as the fallback. Any
    # Gemini failure leaves the Wave-18 answer untouched.
    # Wave 41: when Gemini returns None, Groq (also free tier)
    # gets the same question before we settle. Exact solves,
    # salvage, greetings, non-maths and science replies have
    # all returned earlier, so neither brain can reach them.
    if result_out.get("fallback_kind") in _GEMINI_KINDS:
        ai_result = _gemini_answer(question, hindi)
        if ai_result is None:
            ai_result = _groq_answer(question, hindi)
        if ai_result is not None:
            return ai_result
    return result_out


def fallback_answer(question, result=None):
    """Convenience wrapper: solve (if no result was given) and
    guarantee a presentable answer dict."""
    if result is None:
        try:
            result = solve_question(question)
        except Exception as e:  # solver must never leak a crash
            result = {"type": "solver", "op": "error",
                      "answer": f"Could not solve this one: {e}",
                      "steps": []}
    return with_fallback(question, result)


__all__ = ["with_fallback", "fallback_answer"]
