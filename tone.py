"""Wave 147 — "Pyar se baat": Ganitra's kind-tone layer.

Suraj's standing rule (17 Nov 2026): Ganitra always talks in
good, kind, loving language — the way a patient teacher talks.
A student who is stuck sometimes gets frustrated and swears.
Ganitra never swears back, never scolds, never lectures, never
mirrors the abuse — it stays calm, answers the maths if there
is a maths question inside the message, and otherwise replies
with ONE short kind line that leaves the door open.

This module is deterministic (no AI, no randomness) and hooks
the chat solve path in two places:

* ``api._solve_friendly`` — the pre-pass (:func:`prepass`):
  a message carrying abuse/frustration is cleaned of exactly
  the abusive words, and the cleaned text is what gets solved
  — so "abe chutiya, 12 aur 18 ka HCF batao" earns exactly the
  answer the polite question earns, with no mention of the
  abuse. A message that is ONLY abuse/frustration (nothing
  question-shaped remains after cleaning) gets the kind line
  (:func:`kind_result`) instead of the not-found line.

* ``api.api_solve`` — the wrong-answer branch: "tumne galat
  jawab diya" / "ye app bekar hai" with a real previous answer
  in the chat earns one short apology line (:func:`apology_line`)
  and that answer served once more, so the student can point
  at the step they doubt (Wave 96 then takes over). It is
  never argued with.

Detection discipline (the false-positive battery in
test_wave147 pins these):

* Latin abuse words match on WORD BOUNDARIES only — "class",
  "pass", "assignment" can never trip the "ass"-family, and
  innocent lookalikes stay innocent: "kamini" (a girl's name
  in word problems) is NOT in the list (only "kamina"/
  "kamine" are), "kutta" (a dog in animal stories) is not in
  the list, "saala" (a relative in ages problems) is not in
  the list, "maa ki" (a mother's age in ages problems) is
  not a phrase.
* Devanagari abuse matches by substring, the codebase norm
  for Devanagari (see fallback._NONMATHS_KEYWORDS) — the
  listed words have no innocent school use.
* A trigger alone never decides the outcome: the CLEANED
  remainder does. Question-shaped remainder -> solved;
  filler-only remainder -> kind line; a substantial but
  questionless remainder (word soup that merely contains a
  stray venting word — Wave 92's pinned case) -> the message
  flows on completely unchanged, exactly as before this wave.
"""

import re

# ---------------------------------------------------------------------------
# Trigger vocabularies
# ---------------------------------------------------------------------------

# Latin-script profanity / direct abuse. Word-boundary matched.
_PROFANITY_WORDS = (
    "fuck", "fucking", "fucker", "fuckers", "motherfucker",
    "shit", "bullshit", "bitch", "bitches", "bastard",
    "bastards", "asshole", "assholes", "dickhead", "whore",
    "slut", "chutiya", "chutiye", "chutiyo", "madarchod",
    "madarchode", "behenchod", "bhenchod", "bhenchode",
    "bhosdika", "bhosdike", "gandu", "randi", "harami",
    "haramkhor", "haramzada", "kamina", "kamine", "nalayak",
    "bewakoof", "bewkoof", "idiot", "idiots", "moron",
    "morons", "dumbass",
)

# Latin-script frustration words (no profanity, pure venting).
# Word-boundary matched, same discipline.
_FRUSTRATION_WORDS = (
    "bekar", "bekaar", "bakwaas", "bakwas", "ghatiya",
    "faltu", "faaltu", "nikamma", "useless", "stupid",
    "dumb", "sucks", "suck", "damn", "crap", "wtf",
)

# Multi-word frustration phrases — substring on the lowered
# text, removed case-insensitively when cleaning.
_FRUSTRATION_PHRASES = (
    "waste of time", "time waste", "waste time", "shut up",
    "i hate", "hate this", "hate you", "hate maths",
    "hate math", "kuch nahi aata", "kuch nhi aata",
    "kuch nahi ata", "kuch bhi nahi aata", "nahi aata tumhe",
    "tumhe kuch nahi", "you know nothing", "u know nothing",
    "you cant solve", "you can't solve", "cant even solve",
    "can't even solve", "bekar hai", "bakwaas hai",
    "bakwas hai", "faltu hai", "useless app", "stupid app",
    "dumb app", "ghatiya app", "faltu app", "bekar app",
    "app bekar",
)

# Wrong-answer complaints (the api-level branch). Answer-
# anchored on purpose: a STEP complaint ("step 2 galat hai")
# contains none of these and stays with the Wave-96 doubt
# machinery.
_ANGER_PHRASES = (
    "galat jawab", "jawab galat", "galat answer",
    "answer galat", "wrong answer", "tumne galat",
    "tum ne galat", "galat bataya", "galat bata diya",
    "galat bta diya", "galat solve kiya", "you are wrong",
    "you're wrong", "ur wrong", "sab galat",
    "गलत जवाब", "जवाब गलत", "गलत बता दिया", "गलत बताया",
    "तुमने गलत", "गलत हल किया",
)

# Devanagari abuse / frustration — substring matched (these
# words have no innocent school use; animal words like
# कुत्ता and relative words like साला are deliberately NOT
# here, they appear in innocent word problems).
_DEV_TRIGGERS = (
    "चूतिया", "चूतिये", "मादरचोद", "बहनचोद", "भोसड़ी",
    "भोसडी", "हरामी", "कमीना", "कमीने", "गांडू",
    "बेवकूफ़", "बेवकूफ", "बकवास", "बेकार", "घटिया",
    "नालायक", "निकम्मा", "फ़ालतू", "फालतू",
    "कुछ नहीं आता", "कुछ न आता", "समय बर्बाद", "टाइम वेस्ट",
    "चुप करो",
)

_PROFANITY_RE = re.compile(
    r"\b(?:" + "|".join(_PROFANITY_WORDS) + r")\b",
    re.IGNORECASE)
_FRUSTRATION_RE = re.compile(
    r"\b(?:" + "|".join(_FRUSTRATION_WORDS) + r")\b",
    re.IGNORECASE)
_TRIGGER_RE = re.compile(
    r"\b(?:" + "|".join(_PROFANITY_WORDS + _FRUSTRATION_WORDS)
    + r")\b", re.IGNORECASE)
_PHRASE_RES = tuple(
    re.compile(re.escape(p), re.IGNORECASE)
    for p in _FRUSTRATION_PHRASES + _ANGER_PHRASES)

# Words that may surround abuse without being content: used
# ONLY (a) to decide that a trigger-carrying clause is pure
# venting and can be dropped whole, (b) to decide that a
# cleaned remainder is filler-only, and (c) to trim rude
# address words off the remainder's edges. A real question
# word (solve, batao, a digit, an operator) is never here.
_FILLER_LATIN = {
    "tum", "tumhe", "tumko", "tu", "tujhe", "hai", "ho",
    "hain", "bahut", "bohot", "bilkul", "ekdum", "are",
    "arre", "abe", "abey", "oye", "bhi", "toh", "to", "ka",
    "ki", "ke", "kahi", "kahin", "ye", "yeh", "wo", "woh",
    "app", "you", "are", "is", "the", "a", "an", "so",
    "very", "really", "just", "man", "dude", "this", "that",
    "it", "its", "of", "for", "me", "my", "i", "we", "he",
    "she", "they", "and", "or", "but", "please", "pls",
    "sun", "suno", "dekh", "dekho", "kar", "karo", "karke",
    "diya", "diye", "tha", "thi", "wala", "wali", "wale",
    "ne", "se", "mein", "par", "pe", "ko", "bhai", "kya",
    "kyaa", "maths", "math", "ganit", "subject", "padhai",
    "aisa", "aisi", "sab", "kuch", "nahi", "nhi", "what",
    "which", "hota",
    "hoti", "raha", "rahi", "rahe", "gaya", "gayi", "hua",
    "hui", "mere", "mera", "meri", "apna", "apni", "apne",
    "mujhe", "hum", "humne", "tumne", "usne", "ek", "do",
    "bhi", "hi", "mat", "kabhi", "abhi", "phir", "fir",
    "chalo", "acha", "accha", "theek", "thik",
}
_FILLER_DEV = {
    "तुम", "तुम्हें", "तुमको", "तू", "तुझे", "है", "हो",
    "हैं", "बहुत", "अरे", "कहीं", "के", "का", "की", "ये",
    "यह", "वह", "वो", "ऐप", "एप", "भी", "तो", "और",
    "मुझे", "मेरा", "मेरी", "मेरे", "सुनो", "देखो", "कर",
    "करो", "दिया", "था", "थी", "ने", "से", "में", "पर",
    "को", "एक", "क्या", "गणित", "सब", "कुछ", "ऐसा",
    "ऐसी", "नहीं", "होता", "होती", "रहा", "रही", "गया",
    "गई", "हुआ", "हुई", "अपना", "अपनी", "अपने", "हम",
    "तुमने", "फिर", "चलो", "अच्छा", "ठीक", "ही", "मत",
    "अभी", "जी",
}

# Rude address / app words trimmed off the cleaned
# remainder's edges (never from its middle, never content).
_EDGE_WORDS = {"abe", "abey", "oye", "are", "arre", "tum",
               "tumhe", "you", "app", "ऐप", "एप", "तुम",
               "तुम्हें"}

# A remainder is question-shaped when it carries a digit, a
# maths operator, or an ask/topic word. Bias is generous on
# purpose: mistaking venting for a question only costs the
# old behaviour, mistaking a question for venting would cost
# the student their answer.
_ASK_RE = re.compile(
    r"(solve|find|calculate|compute|evaluate|simplify|"
    r"factorise|factorize|factor|expand|kitna|"
    r"kitne|kitni|batao|bata|samjhao|samjha|jawab|answer|"
    r"hcf|lcm|gcd|plus|minus|multiply|divide|jodo|jod|"
    r"ghatao|guna|bhaag|area|perimeter|volume|surface|"
    r"angle|degree|equation|root|square|cube|percent|"
    r"percentage|probability|mean|median|mode|average|"
    r"ausat|औसत|हल|बताओ|बता|समझाओ|समझा|कितना|कितने|कितनी|"
    r"क्षेत्रफल|आयतन|परिमाप|कोण|समीकरण|मूल|वर्ग|घन|"
    r"प्रतिशत|माध्य|संख्या|अंक|जोड़|घटा|गुणा|भाग)",
    re.IGNORECASE)
_OPERATORS = set("+*^=<>%×÷√")

# "what"/"which" open a question only with an ask-verb after
# them — "what is the HCF" is a question, "what a bakwaas
# app" / "what the fuck" are exclamations.
_WHAT_ASK_RE = re.compile(
    r"\b(?:what|which)\s+(?:is|are|was|were|do|does|did|"
    r"will|would|can|one|of)\b", re.IGNORECASE)


def _has_question_shape(text):
    t = str(text or "")
    if any(ch.isdigit() for ch in t):
        return True
    if any(ch in _OPERATORS for ch in t):
        return True
    return bool(_ASK_RE.search(t) or _WHAT_ASK_RE.search(t))


def _triggers_in(text):
    """(profanity, frustration, anger) flags for a text."""
    t = str(text or "")
    low = t.lower()
    profanity = bool(_PROFANITY_RE.search(t)) or any(
        d in t for d in _DEV_TRIGGERS[:10])
    frustration = bool(_FRUSTRATION_RE.search(t)) or any(
        d in t for d in _DEV_TRIGGERS[10:]) or any(
        p in low for p in _FRUSTRATION_PHRASES)
    anger = any(p in low or p in t for p in _ANGER_PHRASES)
    return profanity, frustration, anger


def _strip_triggers(text):
    """Remove every trigger token/phrase from `text`.

    Latin words go by word-boundary regex, phrases by
    case-insensitive substring, Devanagari by substring —
    only the abusive words themselves; everything else in
    the sentence is preserved byte for byte."""
    t = str(text or "")
    t = _TRIGGER_RE.sub(" ", t)
    for rx in _PHRASE_RES:
        t = rx.sub(" ", t)
    for d in _DEV_TRIGGERS:
        t = t.replace(d, " ")
    return t


def _words_of(text):
    """Content tokens of a (cleaned) fragment: Latin words
    plus Devanagari whitespace tokens, punctuation dropped."""
    out = []
    for tok in str(text or "").split():
        tok = tok.strip(".,;:!?\"'()[]{}।")
        if tok:
            out.append(tok.lower())
    return out


def _all_filler(text):
    """True when every word of `text` is filler (or there are
    no words at all) — the fragment carries no content."""
    for w in _words_of(text):
        if w in _FILLER_LATIN or w in _FILLER_DEV:
            continue
        # A Latin word written inside a Devanagari fragment
        # (and vice versa) still counts by either table.
        if re.search(r"[a-z]", w) and w not in _FILLER_LATIN:
            return False
        if not re.search(r"[a-z]", w) and w not in _FILLER_DEV:
            return False
    return True


def _clean(text):
    """The message with its abuse/frustration removed.

    A clause (split on , ; ।) that carries a trigger and
    nothing but filler besides is dropped whole — "abe
    chutiya, 12 aur 18 ka HCF batao" loses its first clause
    exactly, so the remainder is the polite question byte for
    byte. Inside surviving clauses only the trigger words
    themselves are removed, then rude address words are
    trimmed off the remainder's edges."""
    parts = re.split(r"([,;।])", str(text or ""))
    kept = []
    i = 0
    while i < len(parts):
        clause = parts[i]
        sep = parts[i + 1] if i + 1 < len(parts) else ""
        profanity, frustration, anger = _triggers_in(clause)
        if (profanity or frustration or anger) and _all_filler(
                _strip_triggers(clause)):
            i += 2  # drop the clause AND its separator
            continue
        kept.append(_strip_triggers(clause))
        kept.append(sep)
        i += 2
    t = "".join(kept)
    t = re.sub(r"\s+", " ", t).strip(" ,;।")
    # Trim rude address words off the edges ("... batao app",
    # "tum ... batao") without ever touching the middle.
    words = t.split(" ")
    while len(words) > 1 and words[0].strip(".,;:!?").lower() \
            in _EDGE_WORDS:
        words.pop(0)
    while len(words) > 1 and words[-1].strip(".,;:!?").lower() \
            in _EDGE_WORDS:
        words.pop()
    return " ".join(words).strip(" ,;।")


def analyse(text):
    """Full tone analysis of one student message.

    Returns a dict: triggered / profanity / frustration /
    anger / app_directed (frustration aimed at the app
    itself) / cleaned (the message minus its abuse) /
    has_question (the cleaned text still asks something)."""
    t = str(text or "")
    profanity, frustration, anger = _triggers_in(t)
    triggered = profanity or frustration or anger
    cleaned = _clean(t) if triggered else t
    app_directed = bool(
        (profanity or frustration)
        and re.search(r"\bapp\b|ऐप|एप", t.lower()))
    return {
        "triggered": triggered,
        "profanity": profanity,
        "frustration": frustration,
        "anger": anger,
        "app_directed": app_directed,
        "cleaned": cleaned,
        "has_question": _has_question_shape(cleaned),
    }


# ---------------------------------------------------------------------------
# The kind line (abuse/frustration only) and the apology line
# ---------------------------------------------------------------------------

_KIND_LINES = {
    "en": "No worries — it happens. 😊 Take a breath and "
          "send your maths question once more; we'll solve "
          "it together, step by step.",
    "roman": "Koi baat nahi — hota hai. 😊 Chalo phir se "
             "try karte hain: apna maths ka sawal bhejo, "
             "hum saath me step-by-step hal karenge.",
    "dev": "कोई बात नहीं — होता है। 😊 चलिए फिर से कोशिश "
           "करते हैं: अपना गणित का सवाल भेजिए, हम साथ में "
           "चरण-दर-चरण हल करेंगे।",
}

_APOLOGY_LINES = {
    "en": "Sorry about that 🙏 Here's that answer once "
          "more — if a step still looks wrong, tell me its "
          "number and I'll explain it.",
    "roman": "Sorry 🙏 Wahi jawab ek baar phir dikha raha "
             "hoon — jo step galat lage, uska number bata "
             "do, main use samjha dunga.",
    "dev": "माफ़ कीजिए 🙏 वही जवाब एक बार फिर दिखा रहा "
           "हूँ — जो चरण गलत लगे, उसका नंबर बता दीजिए, "
           "मैं उसे समझा दूँगा।",
}

_HINGLISH_HINTS = {
    "kya", "hai", "ho", "kaise", "tum", "tumhe", "mera",
    "meri", "kuch", "bata", "sawal", "jawab", "kitna",
    "kitne", "nahi", "haan", "mujhe", "bekar", "bakwaas",
    "ghatiya", "faltu", "galat", "yeh", "mein", "kar",
    "karo", "bhejo", "phir", "karte", "hain", "hoga",
    "chahiye", "wala", "wali", "aata", "samajh", "mera",
}


def flavour_of(text, lang_request=None):
    """The reply flavour for a tone line: an explicit
    language request (Wave 107) outranks the message's own
    script/words, exactly as everywhere else; otherwise
    Devanagari -> "dev", Roman Hindi -> "roman", else "en"."""
    if lang_request == "hi":
        return "dev"
    if lang_request == "hinglish":
        return "roman"
    if lang_request == "en":
        return "en"
    q = str(text or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return "dev"
    words = set(re.findall(r"[a-z]+", q.lower()))
    return "roman" if words & _HINGLISH_HINTS else "en"


def kind_line(text, lang_request=None):
    return _KIND_LINES[flavour_of(text, lang_request)]


def apology_line(text, lang_request=None):
    return _APOLOGY_LINES[flavour_of(text, lang_request)]


def _plain_result(kind, answer):
    """A one-line plain reply in the exact shape fallback's
    plain results use (greeting / nonmaths / not-found), so
    every renderer treats it the same way."""
    return {
        "type": "Ganitra",
        "op": kind,
        "answer": answer,
        "steps": [],
        "fallback": True,
        "fallback_kind": kind,
        "plain_reply": True,
        "plain": True,
    }


def kind_result(text, lang_request=None):
    """The abuse-only / frustration-only reply: ONE short
    kind line in the student's language, plain rendering,
    no lecture, no blame, the door left open."""
    return _plain_result("kind", kind_line(text, lang_request))


# ---------------------------------------------------------------------------
# The _solve_friendly pre-pass
# ---------------------------------------------------------------------------

def prepass(question, lang_request=None):
    """Decide what the tone layer does with one message.

    Returns None when the message carries no abuse or
    frustration (the overwhelming majority — the normal flow
    is then byte-identical), else a dict:

    * {"question": cleaned} — a real question rides along:
      solve the CLEANED text, so the answer is exactly the
      polite question's answer and the abuse is never
      mentioned.
    * {"result": kind_result} — the message is only venting
      (nothing but filler remains after cleaning): serve the
      one kind line.
    * None (again) — a substantial but questionless
      remainder: word soup with a stray venting word. It
      flows on completely unchanged (Wave 92's pin: such
      soup still earns the honest not-found line, not a
      kind line meant for a frustrated student)."""
    a = analyse(question)
    if not a["triggered"]:
        return None
    if a["has_question"]:
        return {"question": a["cleaned"]}
    if _all_filler(a["cleaned"]):
        return {"result": kind_result(question, lang_request)}
    return None
