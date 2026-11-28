"""Wave 132: Ganitra's OWN voice for AI-fallback answers.

Suraj's standing rule (17 Nov 2026): "Agar kisi AI se
Ganitra ans leta hai to usko apni hi language me ans de,
na ki kisi aur AI ka ans same de de — aisa nahi hona
chahiye. Ganitra ki ek apni language honi chahiye, ek alag
simple normal language."

The AI fallback chain (Gemini -> Groq -> OpenRouter) only
supplies the WORKING for questions Ganitra's own solver
could not answer. What the student reads must be Ganitra
speaking in its own house style — the same plain
school-teacher language as its solver answers — never the
source AI's text served same-to-same. The prompt in
gemini_fallback.py asks for that voice; THIS module is the
guarantee: a deterministic re-voicing normalizer that every
AI leg's raw reply passes through inside
gemini_fallback._shape_result (which all three legs share)
before it can become a result.

GANITRA VOICE (the spec this module enforces):
- Short plain steps, one step per line, in the solver's own
  patterns ("Divide both sides by 2: x = 2", "= 60 × 2 =
  120", "Distance = speed × time").
- Simple normal words a Class 6-10 student uses every day.
- No markdown: no headings, no bold/italic walls, no
  bullets-as-decoration, no code fences, no tables.
- No AI-isms and no self-reference: no "Sure!", "Of
  course", "Great question", "Here's the solution",
  "Let's solve step by step", "As an AI", "I will solve",
  "Hope this helps", "Let me know", emojis, or any closing
  chatter. The working starts at once and stops at the
  answer.
- Exactly ONE final line: "Answer: ..." carrying the raw
  reply's OWN stated final answer (enforced by
  gemini_fallback._shape_result with this module's help).
- The student's language and script are kept (the existing
  rule) — re-voicing never translates.

HARD INVARIANT: the normalizer must NEVER alter maths
content. Every maths value in the raw reply — every
number, fraction, expression token and unit that takes
part in the working or the answer — must survive. The
module checks this itself (values_preserved) on every
call: if the normalized text lost or invented a value,
normalize_ai_text DECLINES and returns the raw text
unchanged, so a normalizer bug can never silently corrupt
an answer — worst case the student gets the old
Wave-37-style shaping of the un-normalized text.

What counts as a maths value (the checker's definition,
pinned): a token extracted from the reply by
extract_values — fractions (a/b, incl. the LaTeX
\\frac{a}{b} form, which is the same value), numbers
(incl. decimals), variable powers (x^2, 2x^2) and
coefficient tokens (45x), function calls with a numeric
argument (sqrt(2), sin(30)), and the pinned unit words
(cm, years, Rs, %, degrees, सेमी, वर्ग, ...). Line-start
list/step markers ("1.", "Step 2:") are numbering, not
values — the app has stripped them since Wave 37; the
same holds for line-start sequence openers ("First,",
"Second," — the enumeration word, not the time unit).
A line is
only ever DROPPED whole when it carries no digit at all
and matches the pinned fluff/label patterns below, so a
drop can never remove a number; the remaining transforms
(markdown strip, LaTeX-symbol conversion, sentence
splitting, opener/sequence stripping, table-row joining)
do not touch digit or letter content, and the value check
proves it per call. Duplicate restatements of the final
answer may collapse to the single final line (the value
itself always survives there); that is the one permitted
count change, so the checker compares value SETS, not
counts.

Honest limits (also in the wave notes): the normalizer
re-voices FORM, not wording — a content sentence the AI
wrote in fancy words keeps its words (only the pinned
AI-ism phrases, sequence openers and "We <verb>" starts
are rewritten). LaTeX conversion covers the small pinned
symbol set below; exotic LaTeX (\\dfrac, \\left() stays
as-is — values still survive, only the dressing does.
"""
import difflib
import re

# ---------------------------------------------------------------------------
# The pinned AI-ism phrase lists (verbatim — the wave notes
# quote these; test_wave132 pins their coverage).
#
# Matching is case-insensitive, on the line/sentence with
# markdown stripped and whitespace collapsed. A phrase only
# ever matches at the START of a line/sentence (prefix
# openers), as a WHOLE line/sentence (fluff), or as a whole
# trailing sentence (closers) — never mid-content.
# ---------------------------------------------------------------------------

# Openers stripped from the start of a line/sentence. What
# follows them (if it is real content) is kept.
PREFIX_OPENERS = (
    # English enthusiasm / framing
    "sure", "sure thing", "of course", "certainly",
    "absolutely", "definitely", "great question",
    "good question", "nice question", "excellent question",
    "here's the solution", "here is the solution",
    "here's how to solve it", "here is how to solve it",
    "here's how to solve this", "here is how to solve this",
    "here's the step-by-step solution",
    "here is the step-by-step solution",
    "here's a step-by-step solution",
    "here is a step-by-step solution",
    "here's the working", "here is the working",
    "here's how", "here is how",
    "let's solve this step by step",
    "let's solve it step by step",
    "let's solve this question", "let's solve this problem",
    "let's solve this", "let's solve it", "let's solve",
    "let us solve", "let's break it down", "let's find out",
    "let's get started", "let's start", "let's begin",
    "let me solve this", "let me explain",
    "i will solve", "i'll solve", "i will explain",
    "i'll explain", "i'll walk you through this",
    "i will walk you through this",
    "i can help you with that", "i'll help you with this",
    "as an ai language model", "as a language model",
    "as an ai", "as your ai tutor", "as your tutor",
    # Hinglish (Roman) openers
    "bilkul", "bilkul sahi sawal", "zaroor", "jarur",
    "chalo dekhte hain", "chalo dekhte hai",
    "chalo shuru karte hain", "chalo shuru karte hai",
    "chalo solve karte hain", "ye raha hal",
    "ye raha solution", "ye raha jawab", "ye raha answer",
    "dekhiye", "dekho",
    # Hindi (Devanagari) openers
    "बिल्कुल", "ज़रूर", "जरूर", "चलिए", "आइए",
    "यहाँ हल है", "ये रहा हल", "यह रहा हल",
    "देखिए",
)

# Whole lines/sentences that are ONLY an opener, a closer
# or self-reference — dropped when the line carries no
# digit (the no-digit drop rule: a drop can never remove a
# number). Closers also match as a trailing sentence of a
# longer line.
FLUFF_LINES = (
    # Bare enthusiasm (a whole line/fragment that is only
    # praise — "Great!", "Perfect!")
    "great", "perfect", "excellent", "awesome",
    "wonderful", "brilliant", "superb", "nice", "wow",
    "great job", "well done", "good job",
    # English openers / framing
    "here is the step-by-step solution",
    "here's the step-by-step solution",
    "here is the solution", "here's the solution",
    "let's solve this step by step",
    "let's solve it step by step",
    "let's solve this", "let's solve it", "let's solve",
    "let us solve", "let's break it down",
    "let's find out", "let's get started",
    "let's start", "let's begin", "let me explain",
    "i'll walk you through this",
    "i will walk you through this",
    "as an ai language model", "as a language model",
    "as an ai", "i am an ai", "i'm an ai",
    # English closers
    "hope this helps", "i hope this helps",
    "hope it helps", "i hope it is helpful",
    "i hope this is helpful", "i hope you understood",
    "hope you understood", "let me know if you have any "
    "questions", "let me know if you have any doubts",
    "let me know if you need more help",
    "let me know if you need anything else",
    "feel free to ask", "feel free to ask anytime",
    "feel free to ask if you have any doubts",
    "if you have any doubts, feel free to ask",
    "if you have any questions, feel free to ask",
    "let me know if you have any other questions",
    "happy learning", "keep practicing", "keep practising",
    "practice more", "that's all", "that is all",
    "you're welcome", "thank you", "thanks",
    # Hinglish (Roman) closers / openers
    "koi doubt ho to pucho", "koi doubt ho to poochho",
    "koi doubt ho to batao", "samajh aa gaya hoga",
    "umeed hai samajh aa gaya hoga",
    "asha hai samajh aa gaya hoga",
    "chalo dekhte hain", "chalo dekhte hai",
    "chalo shuru karte hain", "chalo shuru karte hai",
    "ye raha hal", "ye raha solution",
    # Hindi (Devanagari) closers / openers
    "आशा है यह मदद करेगा", "आशा है कि यह मदद करेगा",
    "उम्मीद है समझ आ गया होगा", "आशा है समझ आ गया होगा",
    "कोई doubt हो तो पूछो", "कोई शंका हो तो पूछिए",
    "आइए इसे हल करते हैं", "आइए हल करते हैं",
    "चलिए हल करते हैं", "चलिए शुरू करते हैं",
    "धन्यवाद",
)

# Pure label lines (nothing after the word/colon) — the
# heading dressing AIs put over a working. A label WITH
# content ("Solution: x = 2") is a step and is kept.
LABEL_LINES = (
    "solution", "working", "explanation", "calculation",
    "method", "steps", "step-by-step solution",
    "step by step solution", "answer", "final answer",
    "result", "given", "to find", "find",
    "हल", "समाधान", "दिया है", "दिया गया है",
    "ज्ञात करना है",
    # Wave 233: the Hindi / Roman answer labels join the
    # English "answer" / "final answer" above — a bare
    # "उत्तर:" / "जवाब:" line is the same dressing and is
    # dropped the same way (gemini_fallback._shape_result
    # drops them again at shaping, for the replies whose
    # normalisation this module declines).
    "उत्तर", "अंतिम उत्तर", "जवाब",
)

# Words that may remain after an opener is stripped without
# the line carrying any content — a remainder made ONLY of
# these (and no digit) is dropped with the opener.
_FILLER_WORDS = {
    "this", "it", "the", "a", "an", "question", "problem",
    "step", "steps", "by", "now", "then", "to", "of",
    "for", "us", "we", "hai", "hain", "karke", "kar",
    "दें", "देते", "करते", "हैं", "इसे", "इस", "हल",
}

# Sequence/discourse openers stripped from a line start —
# the solver's own steps never begin with them.
_SEQUENCE_OPENERS = (
    "firstly", "secondly", "thirdly", "first", "second",
    "third", "then", "next", "now", "finally", "lastly",
    "after that", "afterwards", "so", "therefore", "hence",
    "thus", "consequently", "now we get", "now we have",
)

# "We <verb>" starts rewritten to the solver's imperative
# style ("We divide both sides by 2" -> "Divide both sides
# by 2"). Only these verbs — a "We" start that is real
# content ("We need two numbers...") is teacher talk and
# stays.
_WE_VERBS = (
    "know that", "can write", "can take", "take", "divide",
    "multiply", "add", "subtract", "put", "use", "write",
    "get", "find", "solve", "substitute", "replace",
    "expand", "factorise", "factorize", "simplify",
    "rearrange", "calculate", "count", "let", "set",
)

# Words that make a short fragment CONTENT (a verb or a
# relation) rather than a bare noun phrase.
_CONTENT_WORDS = {
    "is", "are", "was", "were", "gives", "give", "means",
    "mean", "equals", "equal", "take", "set", "put",
    "divide", "multiply", "add", "subtract", "find",
    "solve", "calculate", "write", "use", "get", "count",
    "substitute", "replace", "expand", "simplify",
    "rearrange", "let", "know", "make", "makes", "draw",
    "plot", "join", "mark", "choose", "assume", "suppose",
    "putting", "using", "taking", "adding", "dividing",
    "multiplying", "subtracting",
}

# First words capitalised after a start-strip when they are
# plain sentence words (never a variable: single letters
# and tokens with digits/operators are untouched).
_CAPITALISE_FIRST = {
    "the", "this", "that", "it", "divide", "multiply",
    "add", "subtract", "take", "put", "use", "write",
    "get", "find", "solve", "calculate", "count",
    "substitute", "replace", "expand", "simplify",
    "factorise", "factorize", "rearrange", "let",
}

# Pinned unit words for the value checker (whole-word,
# case-insensitive for the Latin ones).
UNITS = (
    "cm", "mm", "km", "m", "sq", "square", "units", "unit",
    "years", "year", "months", "month", "weeks", "week",
    "days", "day", "hours", "hour", "minutes", "minute",
    "seconds", "second", "litres", "litre", "liters",
    "liter", "kg", "g", "mg", "ml", "rupees", "rupee",
    "rs", "%", "percent", "degrees", "degree", "°",
    "सेमी", "मिमी", "किमी", "मीटर", "वर्ग", "लीटर",
    "किग्रा", "ग्राम", "वर्ष", "साल", "महीने", "महीना",
    "दिन", "घंटे", "घंटा", "मिनट", "सेकंड", "रुपये",
    "रुपया", "₹",
)

# ---------------------------------------------------------------------------
# LaTeX -> plain conversion (the pinned small set). The
# value checker treats these forms as the SAME value (see
# extract_values), so converting them can never trip the
# invariant.
# ---------------------------------------------------------------------------

# The argument charset is deliberately narrow: digits,
# letters, dots and powers (x^2). An argument with + or -
# (\frac{x-1}{2}) is NOT converted — plain "x-1/2" would
# read as a different value, and an unconverted \frac is
# an honest limit while a changed value would be a bug.
_FRAC_RE = re.compile(
    r"\\d?frac\{([0-9A-Za-z.^]+)\}\{([0-9A-Za-z.^]+)\}")
_SQRT_RE = re.compile(r"\\sqrt\{([0-9A-Za-z.^]+)\}")
_LATEX_SYMBOLS = (
    ("\\times", "×"), ("\\div", "÷"), ("\\cdot", "·"),
    ("\\pi", "π"), ("\\leq", "<="), ("\\geq", ">="),
    ("\\neq", "!="), ("\\pm", "±"), ("\\degree", "°"),
    ("^\\circ", "°"),
)


def _latex_to_plain(text):
    text = _FRAC_RE.sub(lambda m: f"{m.group(1)}/{m.group(2)}",
                        text)
    text = _SQRT_RE.sub(lambda m: f"sqrt({m.group(1)})", text)
    for src, dst in _LATEX_SYMBOLS:
        text = text.replace(src, dst)
    text = text.replace("\\(", " ").replace("\\)", " ")
    text = text.replace("\\[", " ").replace("\\]", " ")
    text = text.replace("$$", " ")
    # Paired $...$ math delimiters: strip the dollars, keep
    # the content. A lone $ (a price) is left alone.
    text = re.sub(r"\$([^$\n]+)\$", r"\1", text)
    return text


# ---------------------------------------------------------------------------
# The value checker
# ---------------------------------------------------------------------------

_LIST_MARKER_RE = re.compile(
    r"^\s*(?:step\s*\d+\s*[:.)\-]?\s*|\d+\s*[.)]\s+)",
    re.IGNORECASE | re.MULTILINE)

_FRAC_PLAIN_RE = re.compile(
    r"(?:\d+(?:\.\d+)?|[A-Za-z])(?:\^\d+)?\s*/\s*"
    r"(?:\d+(?:\.\d+)?|[A-Za-z])(?:\^\d+)?")


def extract_values(text):
    """The set of maths values in a text, per the pinned
    definition in the module docstring. Both the runtime
    guard and the wave battery use this one function."""
    text = str(text or "")
    values = set()

    def _blank(m):
        return " " * (m.end() - m.start())

    # Line-start list/step markers ("1.", "Step 2:") are
    # numbering, not values — the app has stripped them
    # since Wave 37 (_STEP_PREFIX), so they are blanked
    # before extraction on both sides alike.
    text = _LIST_MARKER_RE.sub(_blank, text)
    # Line-start sequence openers ("First,", "Second,")
    # are structure, not values — the normalizer strips
    # them by design, and "second" would otherwise be
    # misread as the time unit. (A "second" anywhere else
    # in a line still counts as the unit it may be.)
    text = re.sub(
        r"^\s*(?:first|second|third|finally|then|next)"
        r"\s*,\s*", _blank, text,
        flags=re.IGNORECASE | re.MULTILINE)

    # LaTeX fractions / roots are the same values as their
    # plain forms — extract them first, in plain form.
    for m in _FRAC_RE.finditer(text):
        values.add(f"{m.group(1)}/{m.group(2)}")
    text = _FRAC_RE.sub(_blank, text)
    for m in _SQRT_RE.finditer(text):
        values.add(f"sqrt({m.group(1)})")
    text = _SQRT_RE.sub(_blank, text)
    # Plain fractions: a/b where at least one side is a
    # number and the other is a number or a single letter
    # (1/2, 1/x, x/2). A letter/letter pair ("and/or",
    # "km/h") is not a fraction and is never extracted.
    for m in _FRAC_PLAIN_RE.finditer(text):
        if any(ch.isdigit() for ch in m.group(0)):
            values.add(re.sub(r"\s+", "", m.group(0)))
    text = _FRAC_PLAIN_RE.sub(
        lambda m: _blank(m) if any(
            ch.isdigit() for ch in m.group(0)) else m.group(0),
        text)
    # Variable powers (x^2, 2x^2) — token keeps the whole
    # coefficient+variable+power run.
    for m in re.finditer(r"\d*[A-Za-z]\^\d+", text):
        values.add(m.group(0))
    text = re.sub(r"\d*[A-Za-z]\^\d+", _blank, text)
    # Function calls with a simple argument: sqrt(2),
    # sin(30), sqrt(x^2).
    for m in re.finditer(r"[A-Za-z]{2,}\([0-9A-Za-z.^]+\)",
                         text):
        values.add(m.group(0))
    text = re.sub(r"[A-Za-z]{2,}\([0-9A-Za-z.^]+\)", _blank,
                  text)
    # Coefficient tokens (45x).
    for m in re.finditer(r"\d+[A-Za-z]", text):
        values.add(m.group(0))
    text = re.sub(r"\d+[A-Za-z]", _blank, text)
    # Plain numbers (incl. decimals).
    for m in re.finditer(r"\d+(?:\.\d+)?", text):
        values.add(m.group(0))
    # Units (whole word; % and ° and ₹ are symbols).
    low = " " + text.lower() + " "
    for unit in UNITS:
        if unit in ("%", "°", "₹"):
            if unit in text:
                values.add(unit)
        elif re.search(r"(?<![a-z])" + re.escape(unit) +
                       r"(?![a-z])", low):
            values.add(unit)
    return values


def values_preserved(raw, served):
    """True when `served` carries exactly the same SET of
    maths values as `raw` — nothing lost, nothing invented.
    (Counts may differ only by duplicate restatements of
    the final answer collapsing to the one final line.)"""
    return extract_values(raw) == extract_values(served)


# ---------------------------------------------------------------------------
# The sameness metric (the wave battery's proof that the
# served answer is not the source AI's text copied over)
# ---------------------------------------------------------------------------

def _is_formula_line(line):
    """A line that is (almost) pure maths: it carries a
    digit and no word longer than 4 letters. Formula lines
    are EXPECTED to survive near-verbatim (they are the
    working, not the voice), so the sameness metric
    excludes them."""
    if not any(ch.isdigit() for ch in line):
        return False
    return not any(len(w) > 4
                   for w in re.findall(r"[A-Za-z]+", line))


def shared_line_ratio(raw, served):
    """Share of the raw reply's NON-formula lines that
    appear verbatim (whitespace-stripped) among the served
    lines. Returns None when the raw reply has no
    non-formula lines. 1.0 would mean the prose was served
    same-to-same."""
    raw_lines = [ln.strip() for ln in
                 str(raw or "").splitlines() if ln.strip()]
    served_set = {ln.strip() for ln in
                  str(served or "").splitlines() if ln.strip()}
    prose = [ln for ln in raw_lines if not _is_formula_line(ln)]
    if not prose:
        return None
    shared = sum(1 for ln in prose if ln in served_set)
    return shared / len(prose)


def word_overlap(raw, served):
    """LCS-style word-sequence similarity (difflib ratio)
    between the raw reply and the served text."""
    a = re.findall(r"\S+", str(raw or ""))
    b = re.findall(r"\S+", str(served or ""))
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


# ---------------------------------------------------------------------------
# The normalizer
# ---------------------------------------------------------------------------

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u262F\u263B-\u266F"
    "\u2700-\u27BF\uFE0F]")
_HR_RE = re.compile(r"^\s*([-*_]\s*){3,}$")
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*")
_FENCE_RE = re.compile(r"^\s*```")
_SENTINEL_RE = re.compile(r"^\s*NOT_MATHS[.!]?\s*$",
                          re.IGNORECASE)

# Sentence boundary: a . ! or ? (or the Hindi danda) that
# ENDS a sentence — preceded by a letter, a closing
# bracket or a digit, followed by whitespace and a
# capital letter / opening bracket. A decimal point never
# splits (3.5 has no whitespace after the point), and
# neither does a period before a digit (Rs. 500). A split
# can leave a bare list marker behind ("1." / "Step 1.")
# — _process_sentence drops those.
_SENT_SPLIT_RE = re.compile(
    r"(?<=[A-Za-z\)\u0900-\u097F0-9])([.!?।])\s+"
    r"(?=[A-Z\(\u0900-\u097F])")


def _strip_markdown(line):
    """Remove markdown decoration from one line: heading
    marks, blockquote marks, bold/italic/strike markers,
    backticks, star emphasis around plain phrases. Digit
    and letter content is never touched: `**`/`__` pairs
    are decoration in this app's notation (exponents are
    ^), and single-* emphasis is stripped only around a
    phrase with a space and no digit/operator."""
    line = _HEADING_RE.sub("", line)
    line = re.sub(r"^\s*>\s?", "", line)
    line = line.replace("`", "")
    line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
    line = re.sub(r"__(.+?)__", r"\1", line)
    line = re.sub(r"~~(.+?)~~", r"\1", line)
    line = line.replace("**", "").replace("__", "")

    def _star(m):
        inner = m.group(1)
        if " " in inner and not any(
                ch.isdigit() or ch in "=+*/^<>%"
                for ch in inner):
            return inner
        return m.group(0)

    line = re.sub(r"\*([^*\n]+)\*", _star, line)
    return line.strip()


def _norm_key(text):
    """The comparison form of a line/sentence for fluff
    matching: lowercase, punctuation (incl. the danda and
    sentence enders) stripped, whitespace collapsed."""
    text = str(text or "").lower()
    text = re.sub(r"[.!?।,;:\"'()\[\]{}—–\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


_FLUFF_KEYS = {_norm_key(p) for p in FLUFF_LINES}
_LABEL_KEYS = {_norm_key(p) for p in LABEL_LINES}
_OPENER_KEYS = sorted(PREFIX_OPENERS,
                      key=lambda p: -len(_norm_key(p)))


def _strip_prefix_opener(text):
    """Strip ONE pinned opener phrase from the start of
    `text` (already markdown-stripped). Returns
    (new_text, stripped_anything). Matching is on the
    normalised key; the cut is made in the original text
    by walking its words until their normalised forms
    cover the phrase exactly, so the remainder keeps its
    exact characters even when punctuation makes the word
    counts differ ("step-by-step:" is one raw word but
    three key words)."""
    key = _norm_key(text)
    for phrase in _OPENER_KEYS:
        pk = _norm_key(phrase)
        if key == pk:
            return "", True
        if not key.startswith(pk + " "):
            continue
        target = pk.split()
        acc = []
        for m in re.finditer(r"\S+", text):
            acc.extend(_norm_key(m.group(0)).split())
            if acc == target:
                rest = text[m.end():]
                rest = rest.lstrip(" .!?,;:—–-।")
                return rest.strip(), True
            if len(acc) > len(target):
                break
        # The phrase boundary falls inside a raw word —
        # do not guess a cut; leave the line as it is.
    return text, False


def _strip_sequence_opener(text):
    """Strip one sequence/discourse opener ("First,",
    "Therefore,", "Now") from the start. Returns
    (new_text, stripped)."""
    m = re.match(
        r"^(firstly|secondly|thirdly|first|second|third|"
        r"then|next|now|finally|lastly|afterwards|so|"
        r"therefore|hence|thus|consequently)\b[\s,]*",
        text, re.IGNORECASE)
    if m:
        return text[m.end():].strip(), True
    m = re.match(r"^after\s+that\b[\s,]*", text,
                 re.IGNORECASE)
    if m:
        return text[m.end():].strip(), True
    return text, False


def _strip_we_start(text):
    """Rewrite a "We <verb> ..." start to the solver's
    imperative style. Returns (new_text, stripped)."""
    m = re.match(r"^we\s+(.+)$", text, re.IGNORECASE)
    if not m:
        return text, False
    rest = m.group(1)
    for verb in _WE_VERBS:
        if rest.lower().startswith(verb + " ") or \
                rest.lower() == verb:
            out = rest[len(verb):].strip()
            if verb == "know that":
                return out, True
            head = verb.split(None, 1)[1] \
                if verb.startswith("can ") else verb
            return (head[0].upper() + head[1:] +
                    (" " + out if out else "")), True
    return text, False


def _capitalise_first(text):
    """Capitalise the first word after a start-strip when
    it is a plain sentence word (never a variable or an
    expression start)."""
    m = re.match(r"^([A-Za-z]+)\b", text)
    if m and m.group(1).lower() in _CAPITALISE_FIRST:
        return m.group(1)[0].upper() + text[1:]
    return text


def _is_fluff(text):
    """True when a line/sentence is only pinned fluff (an
    opener, a closer, self-reference) — checked on the
    normalised key, with light suffix tolerance (a
    trailing "!" / "step by step" tail)."""
    key = _norm_key(text)
    if key in _FLUFF_KEYS:
        return True
    # "let's solve this step by step" arrives via several
    # keys; also catch opener+fluff-tail combinations.
    for fk in _FLUFF_KEYS:
        if key.startswith(fk) and len(key) - len(fk) <= 12:
            return True
    return False


def _is_filler_only(text):
    """True when what remains after stripping carries no
    content: no digit, and every word is a filler word."""
    if any(ch.isdigit() for ch in text):
        return False
    words = re.findall(r"[^\s]+", _norm_key(text))
    return bool(words) and all(w in _FILLER_WORDS
                               for w in words)


def _is_bare_noun_phrase(text):
    """True for a short fragment with no digit, no
    operator and no content word — the tail of an opener
    ("Let's solve this quadratic equation" -> "quadratic
    equation"), which is framing, not a step. An imperative
    or a relation ("Set up the integral:", "Putting the
    given value:") has a content word and is kept."""
    if any(ch.isdigit() for ch in text):
        return False
    if any(ch in text for ch in "=+*/^<>%"):
        return False
    words = _norm_key(text).split()
    if not words or len(words) > 5:
        return False
    return not any(w in _CONTENT_WORDS for w in words)


def _cut_fluff_edges(sent):
    """Cut a fluff sentence glued to a content sentence
    inside one fragment ("x = 5. Hope this helps!" or
    "Great! Now x = 5"): the sentence splitter cannot see
    every boundary (a period after a digit never splits),
    so a pinned-fluff head or tail across a ". "/"! "
    boundary is cut here."""
    changed = True
    while changed:
        changed = False
        for m in re.finditer(r"[.!?।]\s+", sent):
            head, tail = sent[:m.end()].strip(), \
                sent[m.end():].strip()
            if tail and _is_fluff(head):
                sent, changed = tail, True
                break
            if head and _is_fluff(tail):
                sent, changed = head, True
                break
    return sent


def _process_sentence(sent):
    """Re-voice one sentence/line fragment. Returns the
    cleaned fragment, or "" when it is pure fluff."""
    sent = sent.strip()
    if not sent:
        return ""
    # A bare list/step marker ("1.", "Step 2") is a label,
    # not a step. A bare number with no punctuation is NOT
    # dropped — it may be content, and the value guard
    # would rather keep it.
    if re.fullmatch(r"(?i)step\s*\d+\s*[.)]?", sent) or \
            re.fullmatch(r"\d+\s*[.)]", sent):
        return ""
    sent = _cut_fluff_edges(sent)
    stripped_any = False
    # Opener / sequence / we-start stripping, looped until
    # stable ("Sure! Let's solve..." sheds two layers).
    for _ in range(4):
        if _is_fluff(sent):
            return ""
        new, did = _strip_prefix_opener(sent)
        if did:
            sent, stripped_any = new, True
            continue
        new, did = _strip_sequence_opener(sent)
        if did:
            sent, stripped_any = new, True
            continue
        new, did = _strip_we_start(sent)
        if did:
            sent, stripped_any = new, True
            continue
        break
    if not sent or _is_fluff(sent) or _is_filler_only(sent):
        return ""
    if stripped_any and _is_bare_noun_phrase(sent):
        # The tail of an opener ("...this quadratic
        # equation") — framing, not a step.
        return ""
    if stripped_any:
        sent = _capitalise_first(sent)
    # "let's <verb> ..." -> the imperative, when the whole
    # sentence is that instruction ("Let's calculate the
    # mean." -> "Calculate the mean."). Fluff forms of
    # "let's solve..." were already handled above.
    m = re.match(r"^let's\s+([a-z]+)\b", sent,
                 re.IGNORECASE)
    if m and m.group(1).lower() in _CAPITALISE_FIRST:
        verb = m.group(1)
        sent = verb[0].upper() + verb[1:] + sent[m.end(1):]
    # Excitement at a sentence end is not the house style;
    # a factorial (digit + !) is maths and is kept.
    sent = re.sub(r"(?<=[A-Za-z])!$", ".", sent)
    return sent.strip()


def _split_sentences(line):
    """Split a wall-of-text line into sentence fragments
    (the terminator stays with its fragment). Lines with
    no real boundary come back as one fragment."""
    parts = []
    start = 0
    for m in _SENT_SPLIT_RE.finditer(line):
        end = m.start() + 1  # keep the terminator
        parts.append(line[start:end])
        start = m.end()
    parts.append(line[start:])
    return [p for p in (p.strip() for p in parts) if p]


def _process_line(line):
    """Re-voice one raw line. Returns a list of served
    lines (a wall of text becomes several; a fluff line
    becomes none)."""
    line = line.replace("\u00a0", " ").replace("\u2212", "-")
    line = _EMOJI_RE.sub("", line).strip()
    if not line:
        return []
    if _FENCE_RE.match(line) or _HR_RE.match(line):
        return []
    # Markdown table rows: a separator row is decoration;
    # a data row becomes its cells joined plainly. Only a
    # line that starts AND ends with | is a table row (an
    # absolute-value |x| inside a normal line is content).
    stripped = line.strip()
    if stripped.startswith("|") and stripped.endswith("|"):
        cells = [c.strip() for c in stripped.strip("|")
                 .split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c or "-")
               for c in cells):
            return []
        joined = ", ".join(c for c in cells if c != "")
        return [_strip_markdown(joined)] if joined else []
    line = _strip_markdown(line)
    if not line:
        return []
    # Pure label line ("## Solution:" / "**Given:**") — the
    # heading dressing, dropped (it carries no digit by
    # construction of the label list; double-guard anyway).
    if _norm_key(line) in _LABEL_KEYS and \
            not any(ch.isdigit() for ch in line):
        return []
    if _is_fluff(line) and \
            not any(ch.isdigit() for ch in line):
        return []
    out = []
    for frag in _split_sentences(line):
        done = _process_sentence(frag)
        if done:
            out.append(done)
    return out


def _normalize(text):
    text = _latex_to_plain(str(text or ""))
    out = []
    for raw_line in text.splitlines():
        out.extend(_process_line(raw_line))
    # Collapse runs of identical consecutive lines (an AI
    # that repeats a step line verbatim is decoration, not
    # working).
    deduped = []
    for ln in out:
        if not deduped or deduped[-1] != ln:
            deduped.append(ln)
    return "\n".join(deduped).strip()


def normalize_ai_text(text):
    """Re-voice one AI leg's raw reply into Ganitra's
    house style (see the module docstring).

    Returns:
    - "NOT_MATHS" when the reply carries the NOT_MATHS
      sentinel on its own line anywhere (the sentinel
      leaking mid-reply is still the sentinel — the caller
      serves the honest fallback, per the existing rule);
    - "" when nothing usable remains (a reply of pure
      fluff is not an answer);
    - the normalized text otherwise — or the RAW text,
      unchanged, when the value invariant would break
      (the self-decline guard)."""
    raw = str(text or "")
    if not raw.strip():
        return ""
    for ln in raw.splitlines():
        if _SENTINEL_RE.match(ln.strip()):
            return "NOT_MATHS"
    out = _normalize(raw)
    if not out:
        return ""
    if not values_preserved(raw, out):
        return raw.strip()
    return out


__all__ = [
    "normalize_ai_text", "extract_values", "values_preserved",
    "shared_line_ratio", "word_overlap",
    "PREFIX_OPENERS", "FLUFF_LINES", "LABEL_LINES", "UNITS",
]
