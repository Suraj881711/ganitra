"""Wave 166 — "AUR ASAAN BATAO": the simpler re-serve.

Wave 162's all-AI comparison (#4 adoption, from Claude's
style system): students control HOW an answer is pitched,
not just WHAT it says — "explain like I'm younger" is one
of the most-used student prompts everywhere. Ganitra had
the other direction only: Wave 136's detail-on-demand goes
LONGER when asked. Nothing went SIMPLER. A Class 6 student
stuck on a Class 8-style explanation had no way to ask for
the same answer in easier words.

This module is that way, with the discipline the app
already trusts:

- TRIGGER: a BARE simpler request sent as its own message
  right after an answer — "aur asaan batao", "samajh nahi
  aaya, easy me batao", "simpler please", "explain more
  simply", "आसान भाषा में बताओ". BARE is the whole
  discipline (Wave 148's, mirrored exactly): the message
  must consist ONLY of a simpler-request phrase plus
  filler (ask / address / complaint glue). Any digit, "="
  or "%", any step word ("step" / "स्टेप" / "चरण"), or any
  leftover content word makes it something else's message:
  a question+request keeps its normal path, a step ask
  stays with the Wave-96 doubt layer, and a bare "samajh
  nahi aaya" — confusion with NO simpler phrase — stays
  with the doubt layer too (it explains the last step;
  that behaviour is pinned and unchanged). "detail me
  batao" stays Wave 136/148, "step by step batao" stays
  Wave 123/148: neither carries a simpler phrase, so this
  detector never fires for them.
- THE RE-SERVE: the SAME verified answer, re-presented —
  never re-computed, never re-solved, never sent to an AI
  leg. The deterministic pass over the answer's own lines:
  long lines split into one-idea lines (sentence split,
  label split at ": ", working split at a repeated " = "),
  a small pinned set of formal words swapped for everyday
  ones, and — only for a single whole-number binary
  calculation whose answer is a bare number — ONE
  daily-life example line built from the question's own
  numbers. The result's answer field is never touched.
- HARD INVARIANT (Wave 132's value-preservation
  discipline, enforced by ganitra_voice.extract_values on
  every call): every maths value of the original answer
  must survive in the simpler version, and no value may
  appear that was not already in the question or the
  answer. If the check fails — or no transform changed
  anything — there is no simpler version, and api.py
  serves the stored answer itself, byte-identical. A
  simplification is NEVER served unverified.
- Proofs are excluded (detail.py's rule: a proof IS its
  own why; its lines are its argument, not dressing) —
  the stored proof is served unchanged.

Language: the intro and example lines follow the answer's
flavour (followups.flavour_for — en / roman / dev, with
Wave 107's explicit-request rule), exactly like every
other re-serve. The word swaps are script-disjoint pinned
sets, so a line is only ever swapped in its own language.

MERGE SEAMS: this module is new and self-contained; the
only other change is ONE additive block in api.py's
api_solve, immediately after the Wave-148 bare-view block
and before the Wave-96 doubt block (the position is the
spec: the tone block above has already declined the
message, Wave 148 has already declined it, and the doubt
layer below must never see a message this wave claims —
while every message this wave declines reaches the doubt
layer byte-identically to before). followups.py is NOT
modified: the existing "simpler" follow-up CHIP keeps its
Wave-122 semantics (an alternate method / the doubt
layer's last-step explanation) — this wave's phrase path
is a different, value-locked re-presentation, and
unifying the two would change pinned chip behaviour.
The flag-off streaming endpoint is deliberately untouched
(Wave 163's precedent): with GANITRA_AI_STREAM unset it
answers 404 and the chat uses /api/solve.
"""

import re

from followups import flavour_for, is_solved_result
from ganitra_voice import extract_values

__all__ = ["parse_bare_simple_request", "simplify_result"]


# ------------------------------------------------------------------
# The bare simpler-request detector.
#
# FIRE condition — an explicit simpler phrase:
#   Latin (matched on the normalised text — lowercased,
#   hyphens turned to spaces):
#     "aur <asaan|asan|easy|simple>"      ("aur asaan batao")
#     "asaan/asan <me|mein|mai|se> <verb>" ("asaan me batao")
#     "asaan/asan <verb>"                 ("asaan samjhao")
#     "asaan/asan <me|mein|mai|se|bhasha|language|words|
#       shabdon>"                         ("asaan bhasha me")
#     "asaani se"                         ("asaani se samjhao")
#     "easy <me|mein|mai> <verb>", "easy <me|...|language|
#       words|way|bhasha>", "easy <verb>"
#     "in <easy|simple> <words|language|bhasha>"
#     "simpler", "more simply",
#     "simple <words|language|bhasha|me|mein|mai|way>",
#     "simple <verb>", "explain [more] simply"
#     "chhoti class"  ("chhoti class ke hisaab se samjhao")
#   Devanagari (exact substrings, the house style):
#     "आसान भाषा", "आसान शब्दों", "आसान में", "आसान से",
#     "आसान करके", "और आसान", "सरल भाषा", "सरल में"
#
# "simple" ALONE never fires ("simple interest samjhao"
# is a topic ask), and neither does "samajh nahi aaya"
# alone (Wave-96 doubt owns it — see the module docstring).
# ------------------------------------------------------------------

_SIMPLE_PATTERNS = tuple(re.compile(p) for p in (
    r"\baur (?:asaan|asan|easy|simple)\b",
    r"\b(?:asaan|asan) (?:me|mein|mai|se) "
    r"(?:batao|samjhao|samjhaao|dikhao|do|karo)\b",
    r"\b(?:asaan|asan) "
    r"(?:batao|samjhao|samjhaao|dikhao|karo|kar do)\b",
    r"\b(?:asaan|asan) "
    r"(?:me|mein|mai|se|bhasha|language|words?|shabdon)\b",
    r"\basaani se\b",
    r"\beasy (?:me|mein|mai) "
    r"(?:batao|samjhao|samjhaao|dikhao|do|karo)\b",
    r"\beasy "
    r"(?:me|mein|mai|language|words?|way|bhasha)\b",
    r"\beasy (?:batao|samjhao|samjhaao|karo)\b",
    r"\bin (?:easy|simple) (?:words?|language|bhasha)\b",
    r"\bsimpler\b",
    r"\bmore simply\b",
    r"\bsimple (?:words?|language|bhasha|me|mein|mai|way)\b",
    r"\bsimple (?:batao|samjhao|samjhaao|karo)\b",
    r"\bexplain (?:more )?simply\b",
    r"\bchhoti class\b",
))
_SIMPLE_PHRASES_DEV = (
    "आसान भाषा", "आसान शब्दों", "आसान में", "आसान से",
    "आसान करके", "और आसान", "सरल भाषा", "सरल में",
)

# Confusion glue a simpler ask may ride on ("samajh nahi
# aaya, easy me batao") — removed before the leftover
# check. The phrases carry no question payload; WITHOUT a
# simpler phrase they never fire this detector (the fire
# condition above runs first), so the Wave-96 doubt path
# for a bare confusion message is untouched.
_CONFUSION_REMOVALS = tuple(re.compile(p) for p in (
    r"\bmujhe samajh nahi (?:aaya|aata|aa raha)\b",
    r"\bsamajh nahi (?:aaya|aata|aa raha)\b",
    r"\bsamajh nhi (?:aaya|aata)\b",
    r"\bnahi samajh (?:aaya|aata)\b",
    r"\bdon'?t understand\b",
    r"\bdo not understand\b",
    r"\bnot understand\b",
    r"\bnot clear\b",
))
_CONFUSION_DEV = (
    "मुझे समझ नहीं आया", "समझ नहीं आया", "समझ नही आया",
    "समझ नहीं आता", "समझ नहीं आ रहा",
)

# The Wave-148 view phrases a simpler ask may ALSO carry
# ("aur asaan step by step batao" — the w122 gate reads
# the same message and opens the step labels on the
# re-serve, exactly as it does for a Wave-148 re-serve).
# Mirrored from followups' removal sets (same shapes, so
# the two bare detectors can never disagree about what a
# view phrase is).
_VIEW_STEP_REMOVALS = tuple(re.compile(p) for p in (
    r"step by step",
    r"\bstepwise\b",
    r"\bstep karke\b",
    r"\bek ek step\b",
    r"\b(?:saare|sare|sab|har|each|all) steps?\b",
    r"\bsteps? (?:me|mein|mai|se) "
    r"(?:batao|samjhao|samjhaao|dikhao|chahiye|do)\b",
    r"\bsteps? (?:batao|samjhao|samjhaao|dikhao|chahiye)\b",
    r"\bwith steps\b",
    r"\bsteps? ke saath\b",
    r"\bshow (?:me )?(?:all )?(?:the )?steps\b",
))
_VIEW_DETAIL_REMOVALS = tuple(re.compile(p) for p in (
    r"\bin detail\b",
    r"\bdetailed (?:answer|solution|explanation|working)\b",
    r"\bdetail (?:me|mein|mai|se) "
    r"(?:batao|samjhao|samjhaao|dikhao|chahiye|do|samjha)\b",
    r"\bdetailme (?:batao|samjhao|samjhaao|dikhao|chahiye|do)\b",
    r"\bdetail (?:batao|samjhao|samjhaao|dikhao|chahiye)\b",
    r"\bvistar se\b",
    r"\bvistaar se\b",
    r"\blamba (?:answer|jawab|solution)\b",
    r"\blong (?:answer|explanation|solution)\b",
    r"\bfull (?:solution|answer|explanation)\b",
    r"\bpoora (?:samjhao|samjha|batao|answer|jawab|solution)\b",
    r"\bpoori detail\b",
    r"\bexplain fully\b",
))
_VIEW_DEV_PHRASES = (
    "स्टेप बाय स्टेप", "चरण दर चरण",
    "क्रम से समझाओ", "क्रम से बताओ", "क्रम से बताइए",
    "विस्तार से", "विस्तार में", "विस्तारपूर्वक", "विस्तृत",
    "डिटेल में", "डिटेल से", "डिटेल बताओ", "डिटेल समझाओ",
    "लंबा उत्तर", "लम्बा उत्तर", "लंबा जवाब",
)

# Words that may remain once the request phrases are
# removed — ask / address / glue words and the request
# families' own nouns. Never content: a leftover topic,
# object or verb of a NEW question ("percentage asaan me
# batao", "isko solve karke asaan batao") fails the check
# and keeps its normal path.
_FILLER = {
    # Wave 148's filler set (the shared glue vocabulary).
    "batao", "bata", "bataao", "samjhao", "samjhaao",
    "samjha", "do", "dikhao", "chahiye", "please", "plz",
    "me", "mein", "mai", "se", "ko", "ke", "ka", "ki",
    "the", "a", "an", "ye", "yeh", "is", "wala", "wale",
    "aur", "or", "and", "bhi", "hi", "ek", "baar", "phir",
    "dobara", "again", "ab", "zara", "tum", "mujhe",
    "mere", "liye",
    "step", "steps", "detail", "vistar", "vistaar",
    "lamba", "full", "poora", "poori", "long", "answer",
    "jawab", "solution", "explanation", "working", "in",
    "with", "show", "all", "each", "har", "sab", "saare",
    "sare", "karke", "saath", "explain",
    "बताओ", "बताइए", "समझाओ", "समझाइए", "में", "से", "दो",
    "दीजिए", "चरण", "दर", "स्टेप", "बाय", "विस्तार",
    "लंबा", "लम्बा", "उत्तर", "जवाब", "डिटेल", "विस्तृत",
    "क्रम", "पूर्वक",
    # This wave's own vocabulary: the simpler family's
    # nouns/heads and the complaint glue a simpler ask
    # rides on. ("samajh / nahi / aaya" are glue ONLY
    # here — the fire condition has already required a
    # simpler phrase, so these words can never make a
    # bare confusion message fire on their own.)
    "asaan", "asan", "asaani", "simple", "simply",
    "simpler", "easy", "easily", "bhasha", "language",
    "words", "word", "shabdon", "shabd", "tarike",
    "tarika", "class", "chhoti", "chhote", "hisaab",
    "hisab", "bachcho", "bachon", "baccho", "bacche",
    "isko", "isey", "karo", "kar", "thoda", "bahut",
    "mushkil", "kathin", "hai", "hain", "lag", "raha",
    "tough", "hard", "difficult",
    "samajh", "nahi", "nhi", "aaya", "aata",
    "समझ", "नहीं", "नही", "आया", "आता", "रहा", "मुझे",
    "आसान", "सरल", "भाषा", "शब्दों", "और",
}

_STEP_WORD = re.compile(r"step|स्टेप|चरण", re.I)


def parse_bare_simple_request(text):
    """True when `text` is ONLY a simpler request (see the
    module docstring for the exact discipline). False for
    everything else — a plain question, a question carrying
    a simpler phrase, a step-targeted ask, a bare detail /
    steps ask, a bare confusion message."""
    raw = str(text or "")
    if not raw.strip():
        return False
    # A digit, "=" or "%" is question payload — the
    # message is a question WITH a request, never bare.
    if any(ch.isdigit() for ch in raw) \
            or "=" in raw or "%" in raw:
        return False
    # A step word makes it the doubt layer's (or Wave
    # 148's) message — a simpler re-serve of the whole
    # answer is never the reply to "dusra step ...".
    # ("step by step" alone is already Wave 148's; with a
    # simpler phrase riding along the outcome is the same
    # as before this wave, by design.)
    if _STEP_WORD.search(raw):
        return False
    # FIRE condition: an explicit simpler phrase.
    fired = any(phrase in raw for phrase in _SIMPLE_PHRASES_DEV)
    normalised = re.sub(r"\s+", " ",
                        raw.lower().replace("-", " "))
    if not fired:
        fired = any(p.search(normalised)
                    for p in _SIMPLE_PATTERNS)
    if not fired:
        return False
    # BARE check: strip every request phrase; only filler
    # may remain.
    cleaned = raw
    for phrase in _SIMPLE_PHRASES_DEV + _CONFUSION_DEV \
            + _VIEW_DEV_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    normalised = re.sub(r"\s+", " ",
                        cleaned.lower().replace("-", " "))
    for pattern in _SIMPLE_PATTERNS + _CONFUSION_REMOVALS \
            + _VIEW_STEP_REMOVALS + _VIEW_DETAIL_REMOVALS:
        normalised = pattern.sub(" ", normalised)
    words = [w for w in re.split(r"[\s.,;:!?\"'()।/]+",
                                  normalised) if w]
    return all(w in _FILLER for w in words)


# ------------------------------------------------------------------
# The simplification pass.
# ------------------------------------------------------------------

_INTRO_LINES = {
    "en": "In simple words:",
    "roman": "Asaan shabdon me:",
    "dev": "आसान शब्दों में:",
}

# Formal -> everyday word swaps. Whole-word, pinned, and
# deliberately small: every entry is a plain-language swap
# a teacher would make, none is a maths term, a unit word
# (ganitra_voice.UNITS is never touched) or a variable.
# The three sets are script-disjoint, so a line is only
# ever swapped in its own language.
_SWAPS_EN = (
    ("prime factorisation", "prime factors"),
    ("prime factorization", "prime factors"),
    ("therefore", "so"),
    ("hence", "so"),
    ("thus", "so"),
    ("consequently", "so"),
    ("lowest", "smallest"),
    ("obtain", "get"),
    ("calculate", "find"),
    ("determine", "find"),
    ("approximately", "about"),
    ("remaining", "left"),
)
_SWAPS_ROMAN = (
    ("arthaat", "matlab"),
    ("atah", "to"),
    ("isiliye", "isliye"),
)
_SWAPS_DEV = (
    ("अर्थात", "मतलब"),
    ("अतः", "तो"),
)
_SWAP_RES = tuple(
    (re.compile(r"\b" + re.escape(src) + r"\b", re.I), dst)
    for src, dst in _SWAPS_EN + _SWAPS_ROMAN) + tuple(
    (re.compile(re.escape(src)), dst)
    for src, dst in _SWAPS_DEV)


def _swap_words(line):
    def _sub(match, dst):
        src = match.group(0)
        if src[:1].isupper():
            return dst[:1].upper() + dst[1:]
        return dst
    for pattern, dst in _SWAP_RES:
        line = pattern.sub(lambda m, d=dst: _sub(m, d), line)
    return line


# A sentence boundary (ganitra_voice's discipline): a
# . ! ? or danda preceded by a letter / bracket / digit
# and followed by whitespace + a capital / opening
# bracket / Devanagari letter. A decimal point never
# splits; neither does a period before a digit.
_SENT_SPLIT_RE = re.compile(
    r"(?<=[A-Za-z\)\u0900-\u097F0-9])([.!?।])\s+"
    r"(?=[A-Z\(\u0900-\u097F])")


def _split_sentences(line):
    parts = []
    start = 0
    for m in _SENT_SPLIT_RE.finditer(line):
        end = m.start() + 1
        parts.append(line[start:end])
        start = m.end()
    parts.append(line[start:])
    return [p for p in (p.strip() for p in parts) if p]


def _split_label(line):
    """Split "Label: working" at the FIRST ": " when the
    tail does real work (carries a digit or "=") — one
    idea per line. A time ("3:30") has no space after the
    colon and never splits; a label-only head with a
    word-only tail stays whole."""
    head, sep, tail = line.partition(": ")
    if not sep or not head.strip() or not tail.strip():
        return [line]
    if len(head.split()) > 6:
        return [line]
    # A colon that completes a value is a ratio colon
    # ("Ratio = 3: 2"), not a label — never split there.
    # (A label that merely ENDS in a number — "Multiply
    # by 200: ..." — still splits.)
    if re.search(r"=\s*\d+(?:\.\d+)?$", head) \
            or head.strip().isdigit():
        return [line]
    if not (any(ch.isdigit() for ch in tail) or "=" in tail):
        return [line]
    return [head.strip(), tail.strip()]


def _split_chain(line):
    """Split a working chain at a repeated " = " —
    "Area = length × breadth = 12 × 5 = 60" becomes
    "Area = length × breadth" / "= 12 × 5" / "= 60" (the
    house style the solver itself uses for the train
    family). Values are untouched: the split only moves
    line breaks. An inequality line is never split (its
    " = " is not a stage separator this wave can read)."""
    if "<" in line or ">" in line:
        return [line]
    parts = line.split(" = ")
    if len(parts) < 3:
        return [line]
    out = [parts[0] + " = " + parts[1]]
    out.extend("= " + p for p in parts[2:])
    if any(not p.strip() or p.strip() == "=" for p in out):
        return [line]
    return out


def _simplify_lines(steps):
    out = []
    for raw in steps:
        line = str(raw).strip()
        if not line:
            continue
        for frag in _split_sentences(line):
            for piece in _split_label(frag):
                for chunk in _split_chain(piece):
                    out.append(_swap_words(chunk))
    return out


# ------------------------------------------------------------------
# ONE daily-life example line — the narrow honest slice.
#
# Only when the question itself is a single whole-number
# binary calculation and the answer is that calculation's
# bare-number result: the operands are read from the
# question, the operation is recomputed HERE and must
# equal the served answer exactly, and the story reuses
# those very numbers. Anything richer — units, a
# fraction operand, more than one operation, an answer
# that is not a bare number — earns no example: a story
# that does not fit is worse than none.
# ------------------------------------------------------------------

_BINOP_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(×|x|\*|÷|/|\+|-)\s*(\d+(?:\.\d+)?)")
_BARE_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")

_EXAMPLE_LINES = {
    "en": {
        "×": "Think of it like this: {a} boxes with {b} "
             "pencils in each box — {c} pencils in all.",
        "+": "Think of it like this: you have {a} marbles "
             "and you get {b} more — now you have {c} "
             "marbles.",
        "-": "Think of it like this: you have {a} marbles "
             "and you give away {b} — {c} marbles are left.",
        "÷": "Think of it like this: {a} sweets shared "
             "equally among {b} friends — each friend "
             "gets {c} sweets.",
    },
    "roman": {
        "×": "Aise samjho: {a} dabbe, har dabbe me {b} "
             "pencils — kul {c} pencils.",
        "+": "Aise samjho: tumhare paas {a} goli hain, "
             "{b} aur mil gayi — ab kul {c} goli hain.",
        "-": "Aise samjho: tumhare paas {a} goli hain, "
             "{b} de di — ab {c} goli bachi.",
        "÷": "Aise samjho: {a} mithaas {b} doston me "
             "barabar baanti — har dost ko {c} mithaas "
             "mili.",
    },
    "dev": {
        "×": "ऐसे समझो: {a} डिब्बे, हर डिब्बे में {b} "
             "पेंसिल — कुल {c} पेंसिल।",
        "+": "ऐसे समझो: तुम्हारे पास {a} गोली हैं, {b} "
             "और मिल गईं — अब कुल {c} गोली हैं।",
        "-": "ऐसे समझो: तुम्हारे पास {a} गोली हैं, {b} "
             "दे दीं — अब {c} गोली बचीं।",
        "÷": "ऐसे समझो: {a} मिठास {b} दोस्तों में बराबर "
             "बाँटी — हर दोस्त को {c} मिठास मिली।",
    },
}
_OP_CANON = {"x": "×", "*": "×", "/": "÷"}


def _whole(token):
    try:
        value = float(token)
    except ValueError:
        return None
    if value != int(value) or value < 0:
        return None
    return int(value)


def _example_line(question, steps, answer, flavour):
    answer = str(answer or "").strip()
    if not _BARE_NUMBER_RE.match(answer):
        return None
    try:
        target = float(answer)
    except ValueError:
        return None
    found = []
    for m in _BINOP_RE.finditer(str(question or "")):
        found.append((m.group(1), m.group(2), m.group(3)))
    # Exactly ONE binary operation in the QUESTION — the
    # same one may repeat, but two different operations
    # earn no story. The steps are never scanned: a
    # factorisation line ("12 = 2^2 × 3") carries a
    # multiplication that is NOT the question's
    # calculation, and a story built on it would teach
    # the wrong picture.
    shapes = {(a, _OP_CANON.get(op, op), b)
              for a, op, b in found}
    if len(shapes) != 1:
        return None
    a_tok, op, b_tok = next(iter(shapes))
    a, b = _whole(a_tok), _whole(b_tok)
    if a is None or b is None:
        return None
    if op == "×":
        got = a * b
    elif op == "+":
        got = a + b
    elif op == "-":
        got = a - b
    elif op == "÷":
        if b == 0 or a % b != 0:
            return None
        got = a // b
    else:
        return None
    if float(got) != target:
        return None
    template = _EXAMPLE_LINES[flavour].get(op)
    if template is None:
        return None
    return template.format(a=a_tok, b=b_tok, c=answer)


# ------------------------------------------------------------------
# The entry point api.py calls (only when a bare simpler
# request was detected — with no request this module is
# never called and every answer is byte-identical to
# before).
# ------------------------------------------------------------------

def simplify_result(prev_result, prev_question, lang=None,
                    lang_request=None):
    """Return the SIMPLER version of `prev_result` — a
    copy; the input dict is never mutated — or None when
    no value-locked simplification exists (the caller then
    serves the stored answer itself, unchanged: see the
    module docstring's invariant)."""
    if not is_solved_result(prev_result):
        return None
    if prev_result.get("fallback_kind") == "proof" \
            or "proof" in str(prev_result.get("op") or ""):
        return None
    old_steps = [str(s) for s in (prev_result.get("steps")
                                  or []) if str(s).strip()]
    if not old_steps:
        return None
    answer = str(prev_result.get("answer") or "")
    text = " ".join([str(prev_question or ""), answer]
                    + old_steps)
    flavour = flavour_for(text, lang=lang,
                          lang_request=lang_request)
    new_steps = _simplify_lines(old_steps)
    example = _example_line(prev_question, old_steps,
                            answer, flavour)
    if example is not None:
        new_steps = new_steps + [example]
    if new_steps == old_steps:
        return None
    # The HARD INVARIANT, checked on every call with
    # Wave 132's own value extractor: the answer's values
    # must ALL survive, and nothing may appear that the
    # question / answer did not already carry.
    must_keep = extract_values("\n".join(old_steps)
                               + "\n" + answer)
    allowed = extract_values("\n".join(
        [str(prev_question or "")] + old_steps) + "\n"
        + answer)
    got = extract_values("\n".join(new_steps) + "\n"
                         + answer)
    if not (must_keep <= got <= allowed):
        return None
    simplified = dict(prev_result)
    simplified["steps"] = [_INTRO_LINES[flavour]] + new_steps
    simplified["followup"] = "simpler"
    return simplified
