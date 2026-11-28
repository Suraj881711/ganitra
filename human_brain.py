"""Wave 214 — the HUMAN BRAIN layer, phase 1 (Suraj, 22 Nov 2026:
"Ganitra ko humans ki tarah kaam karna chahiye — jaise mai Muse se
baat karta hu, waise hi Ganitra students se baat kare").

A real student test (Claude acting as a student, 22 Nov) found the
gap plainly: Ganitra solves well but does not CONVERSE like a
human. Three failures, one root cause — bare conversational
follow-ups fell through every layer to the generic line:

  * "samjhao, step 2 me 3 udhar kaise gaya?"  (step doubt — Wave 96
    territory, phase 2 of this wave)
  * "galat hai, phir se karo"                 (a redo request)
  * "sin 30 degree ka value kya hai?"         (the word "degree"
    and the filler tail defeated the solver's parser)

This module is deliberately narrow and conservative, in the same
discipline as context_ref (Wave 127): it only ever touches a
message that carries NO fresh maths payload of its own.

1. ``normalize_human_text`` — meaning-first normalisation applied
   to the text that is solved (never to the student's shown
   message): the word "degree(s)" after a number becomes "°", and
   conversational filler tails ("ka value kya hai", "kitna hoga",
   "batao na"...) are stripped when a substantive question remains.
   Idempotent; a text with no such pattern comes back unchanged,
   so the bank's exact match and every existing layer see exactly
   what they saw before for all ordinary questions.

2. ``parse_human_followup`` — recognises the two bare follow-ups
   phase 1 serves in the chat route (see api.py's Wave-214 block):
   "redo" (the student says the answer is wrong / do it again)
   and "explain" (a bare "samjhao" with no step reference and no
   new question). Returns None for anything with a fresh payload
   (a digit next to an operator, a question word + payload), for
   step references (Wave 96 owns those), and for everything else —
   the normal layers then answer exactly as before.
"""

import re

__all__ = ["normalize_human_text", "parse_human_followup",
           "intro_line"]

# ------------------------------------------------------------------
# 1. Normalisation
# ------------------------------------------------------------------

_DEGREE_NUM = re.compile(r"(\d+(?:\.\d+)?)\s*degrees?\b", re.IGNORECASE)
_DEGREE_TRIG = re.compile(
    r"\b(sin|cos|tan|cot|sec|cosec|cosine|sine|tangent)\s+degrees?\b",
    re.IGNORECASE)

# Conversational tails a student adds that carry no maths meaning.
# Each is only stripped from the END of the text (after an optional
# question mark), and only when something substantive remains.
_FILLER_TAILS = [
    r"(ka|ki|ke)\s+value\s+kya\s+hai",
    r"(ka|ki|ke)\s+value\s+batao",
    r"value\s+kya\s+hai",
    r"kitna\s+hoga",
    r"kitna\s+hai",
    r"kitne\s+hai",
    r"kya\s+hoga",
    r"kya\s+hai",
    r"batao\s+na",
    r"bata\s+do",
    r"batao",
    r"please\s+batao",
    r"pls\s+batao",
    r"samjhao\s+na",
]
_FILLER_TAIL_RE = re.compile(
    r"[\s,]*(" + "|".join(_FILLER_TAILS) + r")\s*\?*\s*$",
    re.IGNORECASE)


_NUM_ONES = {
    # "zero" is deliberately absent: in student questions it is
    # usually the concept ("kitne zero hote hai"), not a number
    # to rewrite.
    "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "teen": 3, "char": 4, "chaar": 4, "paanch": 5,
    "panch": 5, "chhah": 6, "chhe": 6, "saat": 7, "aath": 8,
    "nau": 9, "das": 10, "gyarah": 11, "barah": 12, "terah": 13,
    "chaudah": 14, "pandrah": 15, "solah": 16, "satrah": 17,
    "atharah": 18, "unnees": 19, "unnis": 19,
}
_NUM_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "bees": 20, "tees": 30, "chaalis": 40, "chalis": 40,
    "pachaas": 50, "pachas": 50, "sattar": 70,
    "assi": 80, "nabbe": 90,
}
_NUM_MULT = {
    "hundred": 100, "sau": 100, "thousand": 1000,
    "hazaar": 1000, "hazar": 1000, "lakh": 100000,
    "lac": 100000, "crore": 10000000, "karod": 10000000,
}
# "do" is the Hinglish verb "give" as often as the number 2,
# and "ek" is the article "a" as often as the number 1 — both
# count as numbers ONLY inside a sequence that goes on to a
# multiplier ("do sau" = 200, "ek hazaar" = 1000), never
# standing alone ("example do", "ek sawal" stay untouched).
_GUARDED_ONES = {"do": 2, "ek": 1}
_NUM_WORDS = set(_NUM_ONES) | set(_NUM_TENS) | set(_NUM_MULT)


def _words_to_digits(text):
    """Replace English/Hinglish number-word sequences with
    digits ("thirty" -> "30", "one hundred twenty five" ->
    "125", "do sau" -> "200"). Text without number words comes
    back byte-identical, so ordinary questions are untouched."""
    tokens = re.split(r"(\W+)", text)
    words = [t.lower() for t in tokens]
    out = []
    i = 0
    n = len(tokens)

    def is_num_word(idx):
        if idx >= n:
            return False
        w = words[idx]
        return w in _NUM_WORDS or w in _GUARDED_ONES or w == "and"

    while i < n:
        w = words[i]
        # A sequence never STARTS at a bare multiplier: "1 crore"
        # is a phrase the fact cards and solvers already know —
        # rewriting it to "1 10000000" would break them.
        # Multipliers only continue a sequence ("do sau" = 200).
        starts = w in _NUM_ONES or w in _NUM_TENS or (
            w in _GUARDED_ONES and i + 2 < n
            and words[i + 2] in _NUM_MULT)
        if not starts:
            out.append(tokens[i])
            i += 1
            continue
        # Parse one maximal number sequence starting here.
        total = 0
        current = 0
        seen = False
        j = i
        last_mult = 1
        prev_kind = None
        poisoned = False
        while j < n:
            wj = words[j]
            if wj in _NUM_ONES:
                if prev_kind == "ones":
                    # Wave 231: two bare ones-words in a row
                    # never compose ONE quantity in English or
                    # Hinglish. The old scan SUMMED the pair, so
                    # "one-one" reached the solver as "2" — the
                    # function term was silently destroyed and
                    # the chat path served the onto-only
                    # concept card for "Define one-one and
                    # onto…" (Deploy-73). Two shapes:
                    # - hyphen-joined ("one-one"): ONE term,
                    #   not a sum — the whole run stays in
                    #   words, exactly as written (poisoned).
                    # - any other separator ("eleven, twelve"):
                    #   a LIST of two numbers — the sequence
                    #   simply ends here and the second word
                    #   converts on its own (plain break).
                    # (Composition stays legal after a tens or
                    # a multiplier: "twenty-one" = 21,
                    # "one hundred one" = 101.)
                    if str(tokens[j - 1]).strip() in (
                            "-", "–", "—"):
                        poisoned = True
                    break
                current += _NUM_ONES[wj]
                seen = True
                prev_kind = "ones"
            elif wj in _NUM_TENS:
                current += _NUM_TENS[wj]
                seen = True
                prev_kind = "tens"
            elif wj in _GUARDED_ONES and seen is False and \
                    j + 2 < n and words[j + 2] in _NUM_MULT:
                current += _GUARDED_ONES[wj]
                seen = True
                prev_kind = "ones"
            elif wj in _NUM_MULT:
                mult = _NUM_MULT[wj]
                if mult >= 1000:
                    total += (current or 1) * mult
                    current = 0
                else:
                    current = (current or 1) * mult
                last_mult = mult
                seen = True
                prev_kind = "mult"
            elif wj == "and" and seen and last_mult >= 100 \
                    and j + 2 < n and \
                    (words[j + 2] in _NUM_ONES or
                     words[j + 2] in _NUM_TENS):
                # "one hundred and five" — the "and" joins
                # INSIDE one quantity, and only once a scale
                # word (hundred / thousand / lakh...) has
                # taken part. Wave 228: without a scale word
                # the "and" is a CONJUNCTION between two
                # operands — "twelve and eighteen" is 12 and
                # 18, never 30 — so the sequence ends here
                # and the second number converts on its own.
                # (deep_solve.digitise states the same rule:
                # the "and" may only join after a scale word.
                # The old unconditional skip summed the pair:
                # "HCF of twelve and eighteen" reached the
                # solver as "HCF of 30".)
                pass  # skip the "and", stay in the sequence
            else:
                break
            j += 2  # step over the separator token
        if poisoned:
            # Emit the whole run — the consumed words AND the
            # offending second ones-word at j — exactly as
            # written, and continue after it. Neither word
            # converts, so the term survives intact.
            out.extend(tokens[i:j + 1])
            i = j + 1
            continue
        if not seen:
            out.append(tokens[i])
            i += 1
            continue
        out.append(str(total + current))
        # Consume the sequence but keep the separator that
        # follows its last word.
        i = j - 1 if j - 1 > i else i + 1
        if i < n and re.fullmatch(r"\W+", tokens[i]) and \
                (i + 1 >= n or not is_num_word(i + 1)):
            out.append(tokens[i])
            i += 1
    return "".join(out)


def normalize_human_text(text):
    """Return the text a human listener would hand to the solver:
    the same question, with spoken-style dressing removed. Never
    raises; never returns an empty string for a non-empty input."""
    if not text:
        return text
    out = text.strip()
    out = _words_to_digits(out)
    # Fraction words the solver knows in one spelling only:
    # "50 ka half" / "50 ka adha" mean "50 ka aadha" (op half).
    out = re.sub(r"\b(k[aei])\s+half\b", r"\1 aadha", out,
                 flags=re.IGNORECASE)
    out = re.sub(r"\badha\b", "aadha", out, flags=re.IGNORECASE)
    out = _DEGREE_NUM.sub(r"\1°", out)
    out = _DEGREE_TRIG.sub(r"\1", out)
    m = _FILLER_TAIL_RE.search(out)
    if m and len(out[:m.start()].strip()) >= 3:
        out = out[:m.start()].strip()
    return out or text


# ------------------------------------------------------------------
# 2. Bare conversational follow-ups
# ------------------------------------------------------------------

_REDO_PHRASES = (
    "galat hai", "galat jawab", "galat answer", "wrong hai",
    "wrong answer", "ye sahi nahi", "sahi nahi hai",
    "nahi ye galat", "phir se karo", "fir se karo",
    "dobara karo", "phir se solve", "dobara solve",
    "phir se batao", "dobara batao", "galat ho gaya",
    "answer galat", "jawab galat", "phir se kar do",
    "dobara kar do", "ek baar phir karo",
)

_EXPLAIN_PHRASES = (
    "samjhao", "samjha do", "samjhaao", "samajh nahi aaya",
    "samajh nahi aya", "samajh nahi aaya mujhe", "explain karo",
    "explain kar do", "explain", "samjha", "nahi samjha",
    "samajh me nahi aaya",
)

_STEP_WORD_RE = re.compile(
    r"\b(step|steps|charan|स्टेप|चरण)\b", re.IGNORECASE)
_PAYLOAD_RE = re.compile(r"\d\s*[-+*/x×=^]|\d\s+(plus|minus|into)\b",
                         re.IGNORECASE)
# A number riding with a maths topic word is a fresh ask, not a
# bare follow-up ("galat hai, 12 ka HCF batao" must solve the
# HCF — the Wave-147 anger layer's pinned case, caught by the
# 23 Nov 2026 regression pass).
_TOPIC_WORD_RE = re.compile(
    r"\b(hcf|lcm|gcd|area|perimeter|volume|percent\w*|average|"
    r"ratio|guna|jod\w*|ghata\w*|ausat|byaj|lambai|chaudai|"
    r"unchai|radius|trijya|vyas|diameter|bhuja|keemat)\b",
    re.IGNORECASE)


def _clean(text):
    return re.sub(r"\s+", " ",
                  (text or "").strip().lower().strip("?!., "))


def parse_human_followup(text):
    """Return "redo" / "explain" for a bare conversational
    follow-up, else None. Conservative by design (see module
    docstring): a fresh question is never claimed."""
    if not text:
        return None
    t = _clean(text)
    if len(t) > 60:
        return None
    if _STEP_WORD_RE.search(t):
        return None  # Wave 96 doubt layer owns step references
    if _PAYLOAD_RE.search(t):
        return None  # carries its own computation — a new question
    if len(re.findall(r"\d+", t)) >= 2:
        return None  # two numbers = a fresh question riding along
    if re.search(r"\d", t) and _TOPIC_WORD_RE.search(t):
        return None  # one number + a topic word = a fresh ask
    for phrase in _REDO_PHRASES:
        if phrase in t:
            return "redo"
    # A bare explain ask: the whole message is (modulo politeness
    # words) just the ask itself — "samjhao", "samjha do na",
    # "mujhe samajh nahi aaya" — never an explain ask glued to a
    # fresh topic ("photosynthesis samjhao" is not ours to claim;
    # it falls through to the normal layers).
    residue = t
    for word in ("mujhe", "please", "pls", "na", "toh", "zara",
                 "ek baar", "phir", "bhai", "yaar", "sir", "mam",
                 "teacher", "aap", "tum"):
        residue = re.sub(r"\b" + word + r"\b", " ", residue)
    residue = re.sub(r"\s+", " ", residue).strip()
    for phrase in _EXPLAIN_PHRASES:
        if residue == phrase or residue == phrase + " do" \
                or residue == "mujhe " + phrase:
            return "explain"
    if t in _EXPLAIN_PHRASES:
        return "explain"
    return None


# ------------------------------------------------------------------
# 3. The kind opening line (system text — English / Roman Hinglish
#    only, per Suraj's standing system-message rule)
# ------------------------------------------------------------------

_INTROS = {
    "redo": {
        "en": "You are right to check — let me solve it again, "
              "carefully, step by step.",
        "hi": "Bilkul, ek baar phir dhyaan se solve karta hoon — "
              "step by step.",
    },
    "explain": {
        "en": "Of course — let me explain the same question again, "
              "in more detail.",
        "hi": "Bilkul — wahi sawal ek baar aur, zyada detail me "
              "samjhata hoon.",
    },
}


def intro_line(kind, lang=None):
    flavour = "hi" if lang == "hi" else "en"
    return _INTROS.get(kind, {}).get(flavour)
