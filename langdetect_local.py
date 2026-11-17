"""Wave 9 — dependency-free, deterministic chat-language detection.

Suraj's rule: the site stays in **English by default**, but when a
student chats in another language the site language switches
AUTOMATICALLY to that language. This module decides, from one chat
message, which of the six UI languages (en/hi/bn/mr/ta/te) it is
written in — with plain Unicode ranges and curated marker-word
lists only. No external APIs, no new dependencies.

Detection order (first solid signal wins):

1. **Script** (solid by construction):
   - Bengali script -> ``bn``; Tamil script -> ``ta``;
     Telugu script -> ``te``.
   - Devanagari -> ``mr`` when distinctly-Marathi material is
     present (the letter ळ, or words like आहे / नाही / मला /
     माझा / कसा / सांगा / पाहिजे / कुठे / कधी / सोडवा), else
     ``hi``.
2. **Roman-script Indian languages** ("WhatsApp language"): the
   student types English letters but the language is Hindi,
   Marathi, Bengali, Tamil or Telugu.
   - Roman **Marathi**: >= 2 distinct STRONG Marathi markers
     (mala, maza, ahe/ahet, nahiye, sanga, karaycha, pahije,
     kuthe, kadhi, ...) and strictly more strong markers than
     Hindi -> ``mr``. A lighter path (1 strong + >= 3 Marathi
     markers overall, no Hindi-strong) also counts.
   - Roman **Hindi (Hinglish)**: >= 2 distinct Hindi markers
     (strong + common), or 1 strong marker with no clear English
     sentence structure -> ``hi``.
   - Roman **Bengali / Tamil / Telugu**: conservative — only
     >= 2 distinct STRONG markers of that language (ami,
     kivabe / enakku, eppadi / naaku, ela ...) -> ``bn``/``ta``/
     ``te``.
   - Conflict rule: distinctly-Marathi markers outrank
     shared/generic ones; pure Hindi markers -> ``hi``; genuinely
     mixed or tied evidence prefers ``hi``.
3. **English**: >= 2 common English words and no competing Indian
   markers -> ``en`` (solid). A plain English question must NEVER
   switch the site language, and pure maths ("x^2-5x+6=0") carries
   no signal at all.

``detect_language_confident(text)`` returns ``(code, solid)`` —
the app only auto-switches when ``solid`` is True. When nothing is
solid the best guess is returned with ``solid == False`` and the
caller keeps the current language.
"""
import re

__all__ = ["detect_language", "detect_language_confident",
           "detect_language_request", "detect_steps_request",
           "detect_detail_request"]

# ---------------------------------------------------------------- scripts
# (language key or "deva", first codepoint, last codepoint)
_SCRIPT_RANGES = (
    ("deva", 0x0900, 0x097F),   # Devanagari (Hindi / Marathi)
    ("bn", 0x0980, 0x09FF),     # Bengali
    ("ta", 0x0B80, 0x0BFF),     # Tamil
    ("te", 0x0C00, 0x0C7F),     # Telugu
)

# Distinctly Marathi material inside Devanagari text. ळ never
# appears in Hindi. The words are common Marathi function words /
# question verbs that standard Hindi does not use in these forms.
_MARATHI_DEVA_CHARS = {"ळ"}
_MARATHI_DEVA_WORDS = {
    "आहे", "आहेत", "नाही", "नाहीये", "मला", "माझा", "माझी", "माझे",
    "कसा", "कशी", "कसे", "सांगा", "सांग", "पाहिजे", "कुठे", "कधी",
    "सोडवा", "सोडव", "येतो", "येते", "जातो", "खूप",
    "मुलगा", "मुलगी", "शाळा",
    "समजत", "कळत", "बघ", "ऐक", "काय",
}
# Wave 38: shared tatsama vocabulary — गणित (maths), प्रश्न
# (question), उत्तर (answer), अभ्यास (practice) are IDENTICAL in
# standard Hindi. They used to sit in the Marathi set above, so
# a single one of them flipped an otherwise plain Hindi maths
# question to Marathi (seen live 15 Nov: a Hindi answer card's
# summary line rendered in Marathi). They no longer trigger a
# switch on their own; real Marathi questions virtually always
# carry a distinctly-Marathi function word from the set above.
_SHARED_DEVA_WORDS = {"गणित", "प्रश्न", "उत्तर", "अभ्यास",
                      # जाते: Marathi verb form, but also the
                      # everyday Hindi passive auxiliary —
                      # "सिक्के उछाले जाते हैं" is pure Hindi
                      # (and was the live mis-detection).
                      "जाते"}

# ---------------------------------------------------------------- Hindi (Roman)
# Strong: essentially only Hindi in Roman spelling.
_HI_STRONG = {
    "mujhe", "mujhko", "muje", "batao", "bata", "samjhao", "samjha",
    "chahiye", "kaise", "kaisa", "kaisi", "kya", "kyun", "kyon",
    "kyunki", "mera", "meri", "mere", "hamara", "hamari", "tumhara",
    "tumhe", "aapko", "nahin", "kitna", "kitni", "kitne", "wala",
    "wali", "wale", "iska", "iski", "iske", "uska", "uski", "uske",
    "isme", "usme", "karke", "sawaal", "sawal", "jawab", "ganit",
    "prashn",
}
# Common: everyday Hindi words (also counted, need company).
_HI_COMMON = {
    "hai", "hain", "ka", "ki", "ke", "ko", "aur", "me", "mein",
    "mai", "main", "ye", "yeh", "wo", "woh", "bhi", "toh", "jab",
    "kab", "par", "per", "se", "ne", "ho", "hota", "hoti", "hote",
    "gaya", "gayi", "raha", "rahi", "rahe", "karo", "kar", "karke",
    "ek", "matlab", "agar", "phir", "abhi", "kuch", "bahut",
    "samajh", "aata", "aati", "jata", "jati",
}
_HI_ALL = _HI_STRONG | _HI_COMMON

# ---------------------------------------------------------------- Marathi (Roman)
# Strong: distinctly Marathi — Hindi does not use these forms.
_MR_STRONG = {
    "mala", "maza", "mazi", "maze", "mazya", "ahe", "ahet", "aahe",
    "nahiye", "nahi", "sanga", "sangto", "samjat", "samajla",
    "samajle", "karaycha", "karayche", "karaychi", "karaych",
    "pahije", "kuthe", "kadhi", "yeto", "yete", "yet", "jaato",
    "jaate", "jaat", "bagh", "bagha", "aik", "eik", "khup",
    "sodva", "sodava", "sodav", "zala", "zale", "kay",
}
# Leaning: Marathi-flavoured but shared with Hindi/Sanskrit roots —
# counted towards the total, never enough on their own unless there
# are several and no Hindi-strong competition.
_MR_LEANING = {
    "kasa", "kashi", "kase", "sang", "pan", "bara", "bari", "bare",
    "shala", "abhyas", "ganit", "prashna", "uttar", "kalat",
    "kalala", "bhet", "hota", "hoti", "hote", "mulga", "mulgi",
    "mhanje", "nakki", "khara", "khare",
}
_MR_ALL = _MR_STRONG | _MR_LEANING

# ---------------------------------------------------------------- Bengali (Roman)
# Conservative strong list: spellings distinctive to Roman Bengali
# (ami = I, amar = my, kivabe = how, keno = why, ache = is/has).
_BN_STRONG = {
    "ami", "tumi", "amar", "tomar", "amader", "tomader", "kivabe",
    "kibhabe", "keno", "ache", "nei", "hobe", "korechi", "korecho",
    "bujhi", "bujhte", "bujhlam", "gonit", "proshno", "uttor",
    "bolte", "ekhane", "okhane", "kokhon", "kothay",
}

# ---------------------------------------------------------------- Tamil (Roman)
# Conservative strong list (enakku = to me, eppadi = how,
# enna = what, sollu = tell, puriyala = don't understand).
_TA_STRONG = {
    "enakku", "unakku", "eppadi", "epdi", "enna", "sollu",
    "sollunga", "puriyala", "puriyavillai", "puriyum", "theriyala",
    "theriyum", "venum", "vendum", "kanaku", "kanakku", "kelvi",
    "eppo", "eppodhu", "inge", "ange", "romba", "konjam",
    "paarunga",
}

# ---------------------------------------------------------------- Telugu (Roman)
# Conservative strong list (naaku = to me, ela = how, enti = what,
# cheppu = tell, ardham kaaledu = don't understand).
_TE_STRONG = {
    "naaku", "neeku", "ela", "enti", "enduku", "cheppu",
    "cheppandi", "ardham", "kaaledu", "kaadu", "kavali",
    "eppudu", "ikkada", "akkada", "ekkada", "chaala", "chala",
    "ledu", "unnadi", "vastundi",
}

# ---------------------------------------------------------------- English
_EN_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "solve", "find",
    "calculate", "what", "how", "why", "when", "which", "this",
    "that", "these", "those", "equation", "equations", "value",
    "value", "for", "of", "in", "on", "to", "and", "or", "if",
    "then", "please", "explain", "show", "give", "given", "let",
    "prove", "simplify", "factorise", "factorize", "derivative",
    "integral", "graph", "plot", "mean", "median", "mode",
    "probability", "triangle", "angle", "angles", "circle",
    "area", "perimeter", "volume", "root", "roots", "square",
    "cube", "power", "sum", "difference", "product", "ratio",
    "percent", "percentage", "number", "numbers", "question",
    "answer", "solution", "step", "steps", "with", "without",
    "between", "from", "into", "does", "do", "did", "can",
    "could", "would", "should", "i", "you", "we", "they", "it",
    "its", "my", "your", "his", "her", "their", "our", "me",
    "him", "them", "us", "am", "be", "been", "have", "has",
    "had", "will", "shall", "may", "might", "not", "no", "yes",
    "all", "any", "some", "each", "every", "both", "than",
    "more", "less", "first", "second", "third", "using", "use",
    "used", "make", "made", "get", "gets", "take", "takes",
}


def _dominant_script(text):
    """Return the Indian-script key with the most letters, or None."""
    counts = {}
    for ch in text:
        if not ch.isalpha():
            continue
        cp = ord(ch)
        for key, lo, hi in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[key] = counts.get(key, 0) + 1
                break
    if not counts:
        return None
    return max(counts, key=counts.get)


def _roman_tokens(text):
    return re.findall(r"[a-z]+", text.lower())


def detect_language_confident(text):
    """Return ``(code, solid)`` for a chat message.

    ``code`` is one of en/hi/bn/mr/ta/te; ``solid`` is True only
    when the evidence is strong enough to auto-switch the site.
    """
    text = (text or "").strip()
    if not text:
        return "en", False

    # --- 1. Script-based (solid) -------------------------------------
    script = _dominant_script(text)
    if script in ("bn", "ta", "te"):
        return script, True
    if script == "deva":
        words = set(re.findall(r"[ऀ-ॏ]+", text))
        if (_MARATHI_DEVA_CHARS & set(text)) or (words & _MARATHI_DEVA_WORDS):
            return "mr", True
        return "hi", True

    # --- 2. Roman-script Indian languages -----------------------------
    tokens = _roman_tokens(text)
    token_set = set(tokens)
    if not token_set:
        return "en", False  # pure maths / symbols: no signal

    hi_strong = len(token_set & _HI_STRONG)
    hi_all = len(token_set & _HI_ALL)
    mr_strong = len(token_set & _MR_STRONG)
    mr_all = len(token_set & _MR_ALL)
    en_hits = len(token_set & _EN_WORDS)
    english_structure = en_hits >= 2

    # Marathi (WhatsApp-style Roman) — distinctly-Marathi markers
    # outrank shared/generic ones; a tie falls through to Hindi.
    if mr_strong >= 2 and mr_strong > hi_strong:
        return "mr", True
    if mr_strong >= 1 and mr_all >= 3 and hi_strong == 0 \
            and not english_structure:
        return "mr", True

    # Hindi (Hinglish).
    if hi_all >= 2 and hi_strong >= 1:
        return "hi", True
    if hi_all >= 3:
        return "hi", True
    if hi_strong >= 1 and not english_structure:
        return "hi", True

    # Bengali / Tamil / Telugu in Roman letters — conservative:
    # only >= 2 distinct STRONG markers, and only when Hindi and
    # Marathi did not already claim the message.
    if hi_all == 0 and mr_strong == 0:
        bn = len(token_set & _BN_STRONG)
        ta = len(token_set & _TA_STRONG)
        te = len(token_set & _TE_STRONG)
        best = max((bn, "bn"), (ta, "ta"), (te, "te"))
        if best[0] >= 2:
            return best[1], True

    # --- 3. English ----------------------------------------------------
    if english_structure:
        return "en", True
    if en_hits >= 1 and hi_all == 0 and mr_all == 0:
        return "en", False  # a lone English word: guess, not solid

    return "en", False


def detect_language(text):
    """Best-guess language code for ``text`` (no confidence flag)."""
    return detect_language_confident(text)[0]


# ---------------------------------------------------------------------------
# Wave 107: explicit language requests inside a message.
#
# Suraj's order (17 Nov 2026): the standing rule above (answer in
# the language the student types in) is EXTENDED — an explicit
# request inside the message overrides the question's language.
# "What is the sum of angles of a triangle? Answer in Hindi"
# must be answered in Hindi even though the question is English,
# and symmetrically for English / Hinglish requests.
#
# ``detect_language_request(text)`` returns ``(target, cleaned)``
# or None. ``target`` is "hi" (Hindi), "en" (English) or
# "hinglish" (Roman Hindi). ``cleaned`` is the message with the
# request phrase removed, so the phrase never reaches the
# solver / bank / fallback layers as if it were question
# content. When no request-shaped phrase is present the
# function returns None and every caller behaves exactly as
# before this wave.
#
# False-positive design (the reason this is not a bare keyword
# search): a language name alone is CONTENT in plenty of real
# maths questions ("A Hindi textbook costs Rs 200 and an English
# textbook costs Rs 150. What is the total cost?"). A match
# therefore needs a request SHAPE around the language name:
#   A. "in <language>" ("answer in Hindi", "in english please")
#      — the English preposition directly before the name.
#   B. "<language> me/mein/mai/में" (the Hindi postposition
#      directly after the name, or attached: "hindime",
#      "हिंदीमें") PLUS a request word within 3 tokens on
#      either side, or the phrase trailing at the very end of
#      the message. The postposition alone is content-shaped
#      ("20 छात्र हिंदी में पढ़ते हैं" — students studying IN
#      Hindi in a sets problem), so it never fires by itself
#      mid-message.
#   C. A request word (answer / jawab / samjhao / batao /
#      chahiye / explain / reply ...) within 3 tokens of the
#      language name, either side ("Hindi answer do", "mujhe
#      english jawab chahiye"). The window is kept tight on
#      purpose: ordinary asks put their verb much further from
#      a content language name ("English book ki price batao"
#      has "batao" 4 tokens away and must NOT fire).
# Maths-ask verbs that appear in every question ("find",
# "solve", "what", "kitna") are deliberately NOT request words.
# When several requests fire, the LAST one wins (a student
# correcting themselves: "hindi me nahi, english me do").

_REQ_LANG_NAMES = {
    "hindi": "hi", "हिंदी": "hi", "हिन्दी": "hi",
    "hinglish": "hinglish", "हिंग्लिश": "hinglish",
    "english": "en", "angrezi": "en", "angreji": "en",
    "अंग्रेज़ी": "en", "अंग्रेजी": "en", "इंग्लिश": "en",
}
_REQ_POSTPOSITIONS = {"me", "mein", "mai", "में", "मे"}
_REQ_WORDS = {
    "answer", "ans", "jawab", "reply", "respond", "explain",
    "samjhao", "samjha", "batao", "bata", "bolo", "likho",
    "do", "dein", "dena", "chahiye",
    "जवाब", "समझाओ", "समझा", "बताओ", "बताइए", "बता",
    "चाहिए", "उत्तर", "दीजिए", "दो", "देना",
}
_REQ_FILLERS = {"please", "plz", "kripya", "कृपया",
                "language", "bhasha", "भाषा"}
# Tokens a request phrase can be built from — used to find the
# full span to strip out of the message before solving.
_REQ_RUN_VOCAB = (set(_REQ_LANG_NAMES) | _REQ_POSTPOSITIONS
                  | _REQ_WORDS | _REQ_FILLERS | {"in"})
_REQ_EDGE_PUNCT = ".,?!;:।\"'()[]–—-"


def _req_token_key(raw):
    return raw.strip(_REQ_EDGE_PUNCT).lower()


def _req_token_lang(key):
    """(target, attached_postposition) when ``key`` is a
    language name — including the attached-postposition forms
    students actually type ("hindime", "हिंदीमें") — else
    (None, False)."""
    if key in _REQ_LANG_NAMES:
        return _REQ_LANG_NAMES[key], False
    for suffix in ("में", "मे"):
        if key.endswith(suffix) and key[:-len(suffix)] \
                in _REQ_LANG_NAMES:
            return _REQ_LANG_NAMES[key[:-len(suffix)]], True
    if key.endswith("me") and key[:-2] in _REQ_LANG_NAMES \
            and key[:-2].isascii():
        return _REQ_LANG_NAMES[key[:-2]], True
    return None, False


def _req_tokens(text):
    """Whitespace tokens of ``text`` with match keys and char
    spans: (key, start, end, lang_target, attached_post)."""
    out = []
    for m in re.finditer(r"\S+", text):
        key = _req_token_key(m.group(0))
        target, attached = _req_token_lang(key)
        out.append((key, m.start(), m.end(), target, attached))
    return out


def _req_fires(tokens, i):
    """True when the language-name token at index ``i`` sits in
    a request-shaped phrase (see the design note above)."""
    n = len(tokens)
    # Shape A: "in <language>".
    if i > 0 and tokens[i - 1][0] == "in":
        return True
    # The postposition slot: the token after the name, or the
    # name token itself when the postposition is attached.
    post_idx = None
    if tokens[i][4]:
        post_idx = i
    elif i + 1 < n and tokens[i + 1][0] in _REQ_POSTPOSITIONS:
        post_idx = i + 1
    if post_idx is not None:
        # Shape B: postposition + a request word within 3
        # tokens on either side of the phrase...
        for j in range(max(0, i - 3), i):
            if tokens[j][0] in _REQ_WORDS:
                return True
        for j in range(post_idx + 1, min(n, post_idx + 4)):
            if tokens[j][0] in _REQ_WORDS:
                return True
        # ...or the phrase trailing at the message end (only
        # filler words after the postposition).
        if all(tokens[j][0] in _REQ_FILLERS
               for j in range(post_idx + 1, n)):
            return True
    # Shape C: a request word within 3 tokens either side.
    for j in range(max(0, i - 3), min(n, i + 4)):
        if j != i and tokens[j][0] in _REQ_WORDS:
            return True
    return False


def _req_run_span(tokens, i):
    """Char span of the whole request phrase around token
    ``i``: extend over consecutive request-vocabulary tokens
    (language names, postpositions, request words, fillers,
    "in") so "please answer in hindi" is stripped as one
    phrase, never half of it."""
    lo = i
    while lo > 0 and tokens[lo - 1][0] in _REQ_RUN_VOCAB:
        lo -= 1
    hi = i
    while hi + 1 < len(tokens) \
            and tokens[hi + 1][0] in _REQ_RUN_VOCAB:
        hi += 1
    return tokens[lo][1], tokens[hi][2]


def _req_tidy(text):
    """Normalise a message after phrase removal: collapse
    whitespace, drop punctuation orphaned at the cut edges and
    a dangling connector ("aur" / "and") at either end."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,?!;:।])", r"\1", text)
    text = text.strip(" .,?!;:।-—")
    for connector in ("aur", "and"):
        if text.lower().startswith(connector + " "):
            text = text[len(connector) + 1:].lstrip(" .,")
        if text.lower().endswith(" " + connector):
            text = text[:-(len(connector) + 1)].rstrip(" .,")
    return text.strip(" .,?!;:।-—")


def detect_language_request(text):
    """Wave 107: ``(target, cleaned)`` when the message carries
    an explicit answer-language request, else None.

    ``target`` is "hi" / "en" / "hinglish"; ``cleaned`` is the
    message with every firing request phrase stripped (it can
    be "" when the message was ONLY a request — callers then
    keep the original text for the solve pipeline and apply
    just the language). The LAST firing request wins."""
    text = str(text or "")
    if not text.strip():
        return None
    tokens = _req_tokens(text)
    hits = []
    for i, tok in enumerate(tokens):
        if tok[3] is not None and _req_fires(tokens, i):
            hits.append(i)
    if not hits:
        return None
    target = tokens[hits[-1]][3]
    spans = sorted((_req_run_span(tokens, i) for i in hits),
                   reverse=True)
    cleaned = text
    for start, end in spans:
        cleaned = cleaned[:start] + " " + cleaned[end:]
    return target, _req_tidy(cleaned)


# ---------------------------------------------------------------------------
# Wave 123: explicit STEP requests inside a message.
#
# Suraj's revision (17 Nov 2026, after seeing Wave 122's
# screenshots): step numbers must NOT be given by default —
# "agar woh chat par bolta hai jabhi do" — only when the student
# asks for steps in the chat (or the question is a proof /
# derivation, which followups.is_proof_type covers). Otherwise
# the answer stays simple plain.
#
# ``detect_steps_request(text)`` returns True only for a
# request-shaped steps phrase, in the spirit of Wave 107's
# detect_language_request: a bare "step" is CONTENT in real
# maths questions ("step function", "one step me answer do"),
# so it never fires by itself — every pattern below carries a
# request shape around the word. The exact phrase set:
#
#   English / Roman (matched on the normalised text —
#   lowercased, hyphens turned to spaces):
#     "step by step"            (incl. "step by step batao /
#                                samjhao" and "step-by-step")
#     "stepwise"
#     "step karke"              ("step karke batao")
#     "ek ek step"              ("ek-ek step samjhao")
#     "saare step(s)" / "sare step(s)" / "sab step(s)" /
#       "har step" / "each step" / "all steps"
#     "step(s) <me|mein|mai|se> <batao|samjhao|samjhaao|
#       dikhao|chahiye|do>"     ("steps me batao", "step se
#                                samjhao" — the postposition
#                                alone never fires: "one step
#                                me answer do" stays plain)
#     "step(s) <batao|samjhao|samjhaao|dikhao|chahiye>"
#                                ("step batao", "steps chahiye")
#     "with steps" / "step(s) ke saath"
#     "show steps" / "show me steps" / "show all the steps"
#   Devanagari (exact phrases):
#     "स्टेप बाय स्टेप", "चरण दर चरण",
#     "क्रम से समझाओ", "क्रम से बताओ", "क्रम से बताइए"
#     ("क्रम से" alone never fires — "आरोही क्रम में लिखो"
#     is an ordering instruction, not a steps request.)
# ---------------------------------------------------------------------------

_STEPS_PATTERNS = tuple(re.compile(p) for p in (
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
_STEPS_PHRASES_DEV = (
    "स्टेप बाय स्टेप",
    "चरण दर चरण",
    "क्रम से समझाओ",
    "क्रम से बताओ",
    "क्रम से बताइए",
)


def detect_steps_request(text):
    """Wave 123: True when the student's message explicitly
    asks for step-by-step working (see the phrase set above).
    Deterministic; no match means the answer renders with
    plain unnumbered lines, exactly as before Wave 122."""
    text = str(text or "")
    if not text.strip():
        return False
    for phrase in _STEPS_PHRASES_DEV:
        if phrase in text:
            return True
    normalised = re.sub(r"\s+", " ",
                        text.lower().replace("-", " "))
    return any(p.search(normalised) for p in _STEPS_PATTERNS)
# ---------------------------------------------------------------------------
# Wave 136: explicit DETAIL requests inside a message.
#
# Suraj's LAMBA ANSWER RULE (17 Nov 2026, standing): Ganitra's
# answers stay SHORT by default; ONLY when the student
# explicitly asks for a long / detailed answer does the SAME
# answer come in a detailed version (the reason behind the
# working + one example). Never long without being asked.
#
# ``detect_detail_request(text)`` returns True only for a
# request-shaped detail phrase — the same discipline as Wave
# 107's detect_language_request and Wave 123's
# detect_steps_request: the bare words "detail" / "long" /
# "full" / "lamba" are CONTENT in real maths questions ("the
# details are given below", "how long is the train", "full
# marks", "train kitni lambi hai"), so every pattern below
# carries a request shape around the word. The exact set:
#
#   English / Roman (matched on the normalised text —
#   lowercased, hyphens turned to spaces):
#     "in detail"
#     "detailed <answer|solution|explanation|working>"
#     "detail <me|mein|mai|se> <batao|samjhao|samjhaao|
#       dikhao|chahiye|do|samjha>"   ("detail me samjhao",
#       "detail mein batao" — the postposition alone never
#       fires: "detail galat hai" stays plain)
#     "detailme <verb>"              (attached postposition,
#       as students type it)
#     "detail <batao|samjhao|samjhaao|dikhao|chahiye>"
#     "vistar se" / "vistaar se"     (Hinglish: in detail)
#     "lamba <answer|jawab|solution>"
#     "long <answer|explanation|solution>"
#     "full <solution|answer|explanation>"
#     "poora <samjhao|samjha|batao|answer|jawab|solution>"
#     "poori detail"
#     "explain fully"
#   Devanagari (exact substrings):
#     "विस्तार से", "विस्तार में", "विस्तारपूर्वक", "विस्तृत"
#       ("विस्तार" ALONE never fires — in Hindi maths it is
#       the algebra instruction EXPAND: "(x + 3)^2 का विस्तार
#       कीजिए" is a plain expand ask, not a detail request)
#     "डिटेल में", "डिटेल से", "डिटेल बताओ", "डिटेल समझाओ"
#     "लंबा उत्तर", "लम्बा उत्तर", "लंबा जवाब"
#
# A steps request ("step by step batao") is NOT a detail
# request — Wave 123's gate owns it; the two compose (a
# detail ask also earns step labels at the w122 gate, see
# detail.py's notes) but neither detector fires for the
# other's phrases.
# ---------------------------------------------------------------------------

_DETAIL_PATTERNS = tuple(re.compile(p) for p in (
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
_DETAIL_PHRASES_DEV = (
    "विस्तार से",
    "विस्तार में",
    "विस्तारपूर्वक",
    "विस्तृत",
    "डिटेल में",
    "डिटेल से",
    "डिटेल बताओ",
    "डिटेल समझाओ",
    "लंबा उत्तर",
    "लम्बा उत्तर",
    "लंबा जवाब",
)


def detect_detail_request(text):
    """Wave 136: True when the student's message explicitly
    asks for a LONG / DETAILED answer (see the phrase set
    above). Deterministic; no match means the answer stays
    SHORT, exactly as before this wave — Suraj's rule is
    that length is earned by asking, never given by
    default."""
    text = str(text or "")
    if not text.strip():
        return False
    for phrase in _DETAIL_PHRASES_DEV:
        if phrase in text:
            return True
    normalised = re.sub(r"\s+", " ",
                        text.lower().replace("-", " "))
    return any(p.search(normalised) for p in _DETAIL_PATTERNS)
