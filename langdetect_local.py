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

__all__ = ["detect_language", "detect_language_confident"]

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
    "सोडवा", "सोडव", "येतो", "येते", "जातो", "जाते", "खूप",
    "मुलगा", "मुलगी", "शाळा", "अभ्यास", "गणित", "प्रश्न", "उत्तर",
    "समजत", "कळत", "बघ", "ऐक", "काय",
}

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
