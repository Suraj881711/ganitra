"""Wave 154: the normal-baat + maths GUIDANCE layer.

Suraj's order (18 Nov 2026): Ganitra should also talk a
little like a person — small talk ("bore ho raha hai",
"tum kya kar sakte ho", "tum robot ho kya") deserves a
short human reply, not the not-found line — and when a
student asks about the FUTURE of maths ("maths me kya
scope hai", "12th ke baad maths leke kya kar sakte hai",
"maths lu ya biology", "exam aa gaye, kya karu", "mann
nahi lag raha padhai me"), Ganitra should GUIDE them like
a teacher, not collapse to "Answer not found".

Two curated layers, both in the maths_meta.py (Wave 111)
spirit — hand-written content, matched by question SHAPE
+ specific trigger phrases, in the student's own flavour
(en / roman / dev):

  * BAAT (Part A): pure small talk only. An entry fires
    when a known small-talk phrase is present AND the
    rest of the message is filler (the tone.py discipline:
    trigger + filler remainder = the whole message is
    small talk). One or two warm lines, plain rendering,
    gently pointing back to maths. The older greeting
    layer (fallback Layer 0) keeps its exact-match
    territory — this layer covers what it misses.

  * GUIDANCE (Part B): authored guidance cards —
    maths scope/careers, after-12th routes, subject
    choice (Maths vs Biology/Commerce), entrance exams,
    how to improve, EXAM PREPARATION (weak chapters
    first, daily revision rounds, previous papers and
    mock tests via Ganitra's own Papers / Chapter Test /
    Practice, likh-likh practice, the mistake copy) and
    MOTIVATION (kind, honest, no false guarantee, one
    small next step, and a talk-to-an-elder line when a
    student sounds deeply distressed). Short by default;
    a detail ask expands the card with the entry's
    detail lines (detail.py's guidance branch, Wave 136
    machinery). Content is evergreen and qualitative:
    NO salary figures, NO percentages, NO guarantees —
    test_wave154 scans every line for exactly that.

HARD GUARDS (the Wave 148 lesson — meta hijack is the
known failure of layers like this):

  * A real maths problem ALWAYS wins: the fresh-problem
    veto (maths_meta's digit-op-digit / table / "% of"
    shapes), an operator-character veto, an MCQ-options
    veto, and a digit+ask payload veto run before either
    layer is even consulted.
  * A concept ask ("trigonometry samjhao", "circle ka
    area kya hai") is the solver/concept layers'
    territory: a topic word + an ask word vetoes both
    layers.
  * Career entries need a maths anchor or a maths-less
    career shape with NO other field named — "doctor
    kaise bane" (no maths anchor, another field named)
    never becomes maths guidance; it keeps the standing
    out-of-scope handling.
  * Exam-prep / motivation / improve entries follow the
    maths_meta advice gate: a maths signal, or no OTHER
    subject named ("history exam ka stress" is not
    ours).
  * Small talk does NOT open general chat: a general
    non-maths question (capital of France) still gets
    the standing maths-only one-liner from the layers
    before/after this one — nothing here matches it.

Hook: fallback.with_fallback calls wave154_result right
after the maths_meta layer (which keeps its own
territory: practice/exam-strategy/fear/weak phrasings it
already owns). fallback_kind is "guidance" / "baat" —
deliberately NOT in fallback._GEMINI_KINDS: curated,
hand-checked content is served as-is, never upgraded or
replaced by an AI guess.
"""
import re

from maths_meta import _has_fresh_problem, \
    _names_other_subject
from tone import _FILLER_DEV, _FILLER_LATIN, _words_of

# ---------------------------------------------------------------------------
# Shared gates
# ---------------------------------------------------------------------------

# Class mentions are not problem payload: "12th ke baad"
# is a guidance ask, not a computation. Stripped before
# every digit check below.
_CLASS_STRIP = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)\b"
    r"|\bclass\s*\d{1,2}\b"
    r"|कक्षा\s*\d{1,2}"
    r"|बारहवीं|ग्यारहवीं|दसवीं",
    re.I)

# Operator characters never appear in small talk or in a
# guidance ask; their presence means a problem rides
# along (the fresh-problem veto only catches digit-op-
# digit, this catches "x^2 ..." and "a+b" shapes too).
_OPERATOR_CHARS = set("=+*^%×÷√∫")

# Ask / topic payload words: with a digit beside them the
# message is a problem to solve, whatever else it says.
_ASK_WORDS = (
    "solve", "find", "calculate", "compute", "evaluate",
    "simplify", "factorise", "factorize", "factor",
    "batao", "bata", "kitna", "kitne", "kitni", "hcf",
    "lcm", "gcd", "area", "perimeter", "volume", "angle",
    "equation", "root", "percent", "percentage",
    "probability", "mean", "median", "mode", "average",
    "table",
    "बताओ", "बता", "कितना", "कितने", "कितनी", "हल करो",
    "क्षेत्रफल", "आयतन", "परिमाप", "समीकरण", "प्रतिशत",
    "औसत",
)

# Concept-ask shape: a maths TOPIC word + an ask word is
# the solver/concept layers' question ("trigonometry
# samjhao", "circle ka area kya hai") — never guidance,
# never small talk. Bare "maths"/"ganit" are signals, not
# topics, and are deliberately absent here: "maths kaise
# improve karu" is a guidance ask, not a concept ask.
_TOPIC_WORDS = (
    "trigonometry", "algebra", "geometry", "calculus",
    "theorem", "triangle", "circle", "equation",
    "fraction", "percentage", "probability", "logarithm",
    "matrix", "vector", "derivative", "integral",
    "त्रिकोणमिति", "बीजगणित", "ज्यामिति", "प्रमेय",
    "त्रिभुज", "वृत्त", "समीकरण", "भिन्न",
)
_CONCEPT_ASK_WORDS = (
    "samjhao", "samjha", "batao", "explain", "kya hai",
    "kya hota", "samajh nahi", "समझाओ", "बताओ",
    "क्या है", "क्या होता",
)

# Fields whose career questions are NOT maths guidance
# when no maths anchor rides along ("doctor kaise bane",
# "biology lekar kya kar sakte hai", "commerce me scope").
_OTHER_FIELDS = (
    "doctor", "neet", "mbbs", "medical", "lawyer",
    "llb", "vakeel", "biology", "pcb", "डॉक्टर",
    "जीव विज्ञान", "बायोलॉजी",
)
_MATHS_ANCHORS = (
    "maths", "math", "ganit", "गणित", "pcm",
)


def _strip_class_mentions(q):
    return _CLASS_STRIP.sub(" ", q)


def _has_ask_word(q):
    return any(w in q for w in _ASK_WORDS)


# Solve-nouns: an ask built on one of these is a maths
# ask even with no digits in it — "kal exam hai, HCF
# batao" wants the HCF (however incompletely), not exam
# advice, and "bore ho raha hai, hcf batao" is not small
# talk.
_SOLVE_NOUNS = (
    "hcf", "lcm", "gcd", "ka value", "ki value",
    "ka answer", "ka hal", "ka solution", "solve karo",
    "solve kar do", "hal karo", "हल करो", "का हल",
    "का मान",
)


def _has_problem_payload(q):
    """True when a real problem to solve rides in the
    text — the layers in this module must never fire."""
    if _has_fresh_problem(q):
        return True
    if any(ch in q for ch in _OPERATOR_CHARS):
        return True
    if sum(q.count(m) for m in ("(a)", "(b)", "(c)", "(d)")) >= 2:
        return True
    if any(n in q for n in _SOLVE_NOUNS):
        return True
    stripped = _strip_class_mentions(q)
    if any(ch.isdigit() for ch in stripped) and _has_ask_word(q):
        return True
    return False


def _is_concept_ask(q):
    return any(t in q for t in _TOPIC_WORDS) \
        and any(a in q for a in _CONCEPT_ASK_WORDS)


def _names_other_field(q):
    if any(f in q for f in _OTHER_FIELDS):
        return True
    if ("commerce" in q or "arts" in q) \
            and not any(a in q for a in _MATHS_ANCHORS):
        return True
    return False


def _career_gate(q):
    """Career entries: a maths anchor always passes; with
    no anchor, another named field blocks."""
    if any(a in q for a in _MATHS_ANCHORS):
        return True
    return not _names_other_field(q)


# Strong maths anchors for the subject gate: narrower
# than maths_meta's broad signal list on purpose — its
# "table" signal fires inside "timetable", which would
# let a HISTORY timetable ask pass as maths prep.
_STRONG_ANCHORS = (
    "maths", "math", "ganit", "गणित", "algebra",
    "geometry", "trigonometry", "calculus", "pcm",
)


def _subject_gate(q):
    """The maths_meta advice gate, tightened: a strong
    maths anchor always passes; with no anchor, a named
    OTHER subject blocks ("history exam ka stress" is
    not ours; "exam ka stress" names nothing and is)."""
    if any(a in q for a in _STRONG_ANCHORS):
        return True
    return not _names_other_subject(q)


_DIFF_MARKERS = ("fark", "antar", "difference",
                 " versus ", " vs ")


def _resolve_flavour(question, flavour):
    """The reply flavour: the caller's flavour (fallback's
    per-question flavour, itself outranked by an explicit
    language request — Wave 107) stands; a missing/invalid
    one is derived from the script, and a Roman-Hindi ask
    upgrades an "en" guess to "roman" (the maths_meta
    rule: genuine English asks carry none of these words).
    """
    q = str(question or "").lower()
    if flavour not in ("en", "roman", "dev"):
        flavour = "dev" if any("ऀ" <= ch <= "ॿ" for ch in q) \
            else "en"
    if flavour == "en":
        words = set(re.findall(r"[a-z]+", q))
        if words & _ROMAN_HINTS:
            flavour = "roman"
    return flavour


_ROMAN_HINTS = {
    "kya", "hai", "kaise", "mera", "meri", "mujhe",
    "nahi", "karu", "karun", "chahiye", "lagta", "raha",
    "rahi", "jaunga", "jaungi", "banege", "sakta",
    "sakti", "sakte", "lekar", "leke", "baad", "padhai",
    "taiyari", "batao", "kyu", "kyon", "hoga", "hogi",
    "aata", "aati", "bahut", "kuch", "mann", "man",
    "pareshan", "demotivate", "hounga",
    # Wave 154's own small-talk shapes: none of these is
    # an English word, so genuine English asks stay "en".
    "kisne", "banaya", "tumhe", "tum", "mere", "ho",
    "rahe", "gaya", "kharab", "lu", "lun",
}


# ---------------------------------------------------------------------------
# Part A: BAAT — pure small talk
# Each entry: trigger phrases + one warm line per flavour.
# An entry fires only when a phrase matches AND the rest
# of the message is filler (tone.py's discipline) — so
# the WHOLE message is small talk, nothing is swallowed.
# ---------------------------------------------------------------------------

# Extra filler for this layer only: class mentions and
# first-person glue around a feeling ("mai class 10 me hu
# bore ho raha hu" is a feeling, not a question).
_BAAT_FILLER_EXTRA = {
    "mai", "main", "class", "kaksha", "कक्षा", "student",
    "school", "padhta", "padhti", "padh", "hu", "hoon",
    "हु", "हूँ", "मैं", "मै", "में", "padhai", "पढ़ाई",
    "aaj", "आज", "kal", "कल", "ganitra",
}


def _all_filler_ext(text):
    for w in _words_of(text):
        if w in _FILLER_LATIN or w in _FILLER_DEV \
                or w in _BAAT_FILLER_EXTRA:
            continue
        if re.search(r"[a-z]", w) and w not in _FILLER_LATIN \
                and w not in _BAAT_FILLER_EXTRA:
            return False
        if not re.search(r"[a-z]", w) \
                and w not in _FILLER_DEV \
                and w not in _BAAT_FILLER_EXTRA:
            return False
    return True


BAAT = [
    {
        "id": "haal",
        "phrases": ("kya haal hai", "kya haal chaal",
                    "kya haal", "कैसे हो आप", "क्या हाल है"),
        "en": "All good here! 😊 How are YOU doing — "
              "send me a maths question and we'll crack "
              "it together.",
        "roman": "Yahan sab badhiya! 😊 Tum sunao, kaise "
                 "ho — maths ka koi sawal hai toh bhejo, "
                 "saath me hal karte hain.",
        "dev": "यहाँ सब बढ़िया! 😊 आप सुनाइए, कैसे हैं — "
               "गणित का कोई सवाल है तो भेजिए, साथ में हल "
               "करते हैं।",
    },
    {
        "id": "doing",
        "phrases": ("kya kar rahe ho", "kya kar rahi ho",
                    "kya kar rahe", "what are you doing",
                    "क्या कर रहे हो"),
        "en": "Just waiting for your maths questions! 😊 "
              "That's my favourite work — send one.",
        "roman": "Bas tumhare maths ke sawalon ka "
                 "intezaar kar raha hoon! 😊 Wahi mera "
                 "pasandeeda kaam hai — ek bhejo toh.",
        "dev": "बस आपके गणित के सवालों का इंतज़ार कर रहा "
               "हूँ! 😊 वही मेरा पसंदीदा काम है — एक "
               "भेजिए तो।",
    },
    {
        "id": "can_do",
        "phrases": ("kya kar sakte ho", "kya kar sakti ho",
                    "kya kya kar sakte", "what can you do",
                    "kya help kar sakte", "kya sikha sakte",
                    "help kar sakte ho", "tum kya kar sakte",
                    "तुम क्या कर सकते हो"),
        "en": "I solve maths questions step by step, "
              "explain any step you doubt, give practice "
              "questions and small tests, and read "
              "questions from photos too. Try me — send "
              "a question! 😊",
        "roman": "Main maths ke sawal step-by-step hal "
                 "karta hoon, jo step samajh na aaye use "
                 "samjhata hoon, practice ke sawal aur "
                 "chhote test deta hoon, aur photo se "
                 "sawal padh kar bhi hal karta hoon. "
                 "Aazma kar dekho — ek sawal bhejo! 😊",
        "dev": "मैं गणित के सवाल चरण-दर-चरण हल करता हूँ, "
               "जो चरण समझ न आए उसे समझाता हूँ, अभ्यास के "
               "सवाल और छोटे test देता हूँ, और फ़ोटो से "
               "सवाल पढ़कर भी हल करता हूँ। आज़मा कर "
               "देखिए — एक सवाल भेजिए! 😊",
    },
    {
        "id": "robot",
        "phrases": ("tum robot ho", "robot ho kya",
                    "kya tum robot", "are you a robot",
                    "are you human", "tum insaan ho",
                    "tum insan ho", "insaan ho kya",
                    "तुम रोबोट हो", "रोबोट हो क्या"),
        "en": "Ha, fair question! I'm Ganitra — a maths "
              "helper who lives in this app, not a person. "
              "But I talk like a friend, and maths is "
              "where I shine. 😊",
        "roman": "Ha, sahi sawal! Main Ganitra hoon — is "
                 "app me rehne wala maths dost, insaan "
                 "nahi. Lekin baat dost ki tarah karta "
                 "hoon, aur maths me toh main kaam ka "
                 "hoon. 😊",
        "dev": "हा, सही सवाल! मैं Ganitra हूँ — इस ऐप में "
               "रहने वाला गणित दोस्त, इंसान नहीं। लेकिन "
               "बात दोस्त की तरह करता हूँ, और गणित में "
               "तो मैं काम का हूँ। 😊",
    },
    {
        "id": "creator",
        "phrases": ("kisne banaya", "who made you",
                    "who created you", "किसने बनाया",
                    "kisne banaya hai"),
        "en": "I was made for students like you — so "
              "that nobody has to feel stuck in maths "
              "alone. And my favourite thing is solving "
              "your next question. 😊",
        "roman": "Mujhe tum jaise students ke liye "
                 "banaya gaya hai — taaki maths me koi "
                 "akele atka na mehsoos kare. Aur mera "
                 "sabse pasandeeda kaam hai tumhara agla "
                 "sawal hal karna. 😊",
        "dev": "मुझे आप जैसे छात्रों के लिए बनाया गया "
               "है — ताकि गणित में कोई अकेले अटका न "
               "महसूस करे। और मेरा सबसे पसंदीदा काम है "
               "आपका अगला सवाल हल करना। 😊",
    },
    {
        "id": "age_place",
        "phrases": ("kitne saal ke", "tumhari age",
                    "your age", "tumhari umar",
                    "kahan rehte", "kaha rehte",
                    "where do you live", "कहाँ रहते",
                    "तुम्हारी उम्र"),
        "en": "No age, no address — I live right here "
              "in Ganitra, awake whenever you open the "
              "app. Your turn: send a maths question! 😊",
        "roman": "Na umar, na pata — main yahi Ganitra "
                 "me rehta hoon, jab bhi app kholo main "
                 "jaga hua. Ab tumhari baari: ek maths "
                 "ka sawal bhejo! 😊",
        "dev": "न उम्र, न पता — मैं यहीं Ganitra में "
               "रहता हूँ, जब भी ऐप खोलिए मैं जगा हुआ। "
               "अब आपकी बारी: एक गणित का सवाल भेजिए! 😊",
    },
    {
        "id": "compliment",
        "phrases": ("bahut ache ho", "bahut achhe ho",
                    "bahut ache", "bahut achhe",
                    "bahut smart", "you are great",
                    "you are smart", "you are the best",
                    "tum best ho", "bahut badhiya",
                    "mast ho tum", "you are awesome",
                    "तुम बहुत अच्छे", "बहुत बढ़िया"),
        "en": "Thank you! 😊 That made my day. The real "
              "credit is yours — you are the one "
              "practising maths. One more question?",
        "roman": "Shukriya! 😊 Din ban gaya. Asli "
                 "credit tumhara hai — maths ki mehnat "
                 "toh tum kar rahe ho. Ek sawal aur?",
        "dev": "शुक्रिया! 😊 दिन बन गया। असली श्रेय "
               "आपका है — गणित की मेहनत तो आप कर रहे "
               "हैं। एक सवाल और?",
    },
    {
        "id": "dost",
        "phrases": ("mere dost ho", "dost ho tum",
                    "you are my friend", "मेरे दोस्त हो",
                    "tum dost ho"),
        "en": "Of course — your maths dost, always. 🤝 "
              "Dost ka kaam hai saath dena: jab maths "
              "me atkoge, main yahi milunga.",
        "roman": "Bilkul — tumhara maths dost, hamesha. "
                 "🤝 Dost ka kaam hai saath dena: jab "
                 "maths me atkoge, main yahi milunga.",
        "dev": "बिल्कुल — आपका गणित दोस्त, हमेशा। 🤝 "
               "दोस्त का काम है साथ देना: जब गणित में "
               "अटकेंगे, मैं यहीं मिलूँगा।",
    },
    {
        "id": "love",
        "phrases": ("i love you", "love you ganitra",
                    "love you"),
        "en": "Haha, thank you! 😊 I like you too — "
              "especially when you send maths questions. "
              "Chalo, ek sawal ho jaye?",
        "roman": "Haha, shukriya! 😊 Tum mujhe bhi "
                 "bahut pasand ho — khaas karke jab "
                 "maths ke sawal bhejte ho. Chalo, ek "
                 "sawal ho jaye?",
        "dev": "हाहा, शुक्रिया! 😊 आप मुझे भी बहुत पसंद "
               "हैं — ख़ास करके जब गणित के सवाल भेजते "
               "हैं। चलिए, एक सवाल हो जाए?",
    },
    {
        "id": "bore",
        "phrases": ("bore ho raha", "bore ho gaya",
                    "bore ho rahi", "bore lag raha",
                    "boring lag raha", "बोर हो रहा",
                    "बोर हो रही", "bore feel ho raha"),
        "en": "Bored? Then it's the perfect time for a "
              "fun one 😊 — send me any small question "
              "you like, or say the word and I'll give "
              "you an easy puzzle-type question. Being "
              "bored just means the right question hasn't "
              "found you yet!",
        "roman": "Bore ho rahe ho? Toh ek mazedaar "
                 "sawal try karo 😊 — khud koi chhota "
                 "sawal bhejo, ya bolo toh main ek easy "
                 "puzzle-type sawal deta hoon. Bore "
                 "hona maths se bhaagne ki nahi, sahi "
                 "sawal milne ki der hai!",
        "dev": "बोर हो रहे हैं? तो एक मज़ेदार सवाल try "
               "कीजिए 😊 — ख़ुद कोई छोटा सवाल भेजिए, या "
               "कहिए तो मैं एक easy puzzle-type सवाल "
               "देता हूँ। बोर होना गणित से भागने की "
               "नहीं, सही सवाल मिलने की देर है!",
    },
    {
        "id": "tired",
        "phrases": ("neend aa rahi", "neend aa raha",
                    "thak gaya", "thak gayi", "नींद आ रही",
                    "थक गया", "थक गई"),
        "en": "Then rest a little — a fresh mind solves "
              "faster than a tired one. 😊 Thoda paani "
              "piyo, 10 minute break lo, Ganitra yahi "
              "hai jab wapas aaoge.",
        "roman": "Toh thoda aaram kar lo — thaka dimaag "
                 "se fresh dimaag tez hal karta hai. 😊 "
                 "Thoda paani piyo, 10 minute break lo, "
                 "Ganitra yahi hai jab wapas aaoge.",
        "dev": "तो थोड़ा आराम कीजिए — थके दिमाग़ से "
               "ताज़ा दिमाग़ तेज़ हल करता है। 😊 थोड़ा "
               "पानी पीजिए, 10 minute break लीजिए, "
               "Ganitra यहीं है जब वापस आएँगे।",
    },
    {
        "id": "fun",
        "phrases": ("maza aa raha", "maza aa gaya",
                    "mazaa aa raha", "मज़ा आ रहा",
                    "मज़ा आ गया"),
        "en": "Bas yahi toh chahiye tha! 😊 Maths mazaa "
              "ban jaye toh rukna mushkil hota hai. Ek "
              "aur sawal ho jaye isi flow me?",
        "roman": "Bas yahi toh chahiye tha! 😊 Maths "
                 "mazaa ban jaye toh rukna mushkil hota "
                 "hai. Ek aur sawal ho jaye isi flow me?",
        "dev": "बस यही तो चाहिए था! 😊 गणित मज़ा बन "
               "जाए तो रुकना मुश्किल होता है। एक और "
               "सवाल हो जाए इसी flow में?",
    },
    {
        "id": "mood",
        "phrases": ("mood kharab", "mood off",
                    "मूड ख़राब", "मूड खराब"),
        "en": "Hota hai — kuch din aise hi hote hain. "
              "😊 Zabaradasti mat karo; chaaho toh ek "
              "bahut easy sawal se shuru karte hain, "
              "nahi toh thodi der baad aana, main yahi "
              "hoon.",
        "roman": "Hota hai — kuch din aise hi hote "
                 "hain. 😊 Zabaradasti mat karo; chaaho "
                 "toh ek bahut easy sawal se shuru karte "
                 "hain, nahi toh thodi der baad aana, "
                 "main yahi hoon.",
        "dev": "होता है — कुछ दिन ऐसे ही होते हैं। 😊 "
               "ज़बरदस्ती मत कीजिए; चाहें तो एक बहुत "
               "easy सवाल से शुरू करते हैं, नहीं तो "
               "थोड़ी देर बाद आइए, मैं यहीं हूँ।",
    },
]

# Thank-you is a PREFIX pattern, not a whole message:
# "thank you ganitra, tumne meri bahut help ki" is pure
# gratitude even though its tail is not filler. The gate
# is: starts with a thanks phrase, no ask payload, no
# problem payload, short.
_THANKS_STARTS = ("thank you", "thanks", "dhanyavaad",
                  "dhanyavad", "shukriya", "धन्यवाद",
                  "शुक्रिया")

_THANKS_LINES = {
    "en": "You're most welcome! 😊 Helping you is "
          "literally my job. Kuch aur maths ka sawal ho "
          "toh main yahi hoon.",
    "roman": "Dil se shukriya tumhara! 😊 Tumhari help "
             "karna hi mera kaam hai. Kuch aur maths ka "
             "sawal ho toh main yahi hoon.",
    "dev": "दिल से स्वागत है! 😊 आपकी मदद करना ही मेरा "
           "काम है। कुछ और गणित का सवाल हो तो मैं यहीं "
           "हूँ।",
}


def _plain_baat(entry_id, line):
    """A one-line plain reply in tone.py's shape, so
    every renderer treats it like the greeting/kind
    lines."""
    return {
        "type": "Ganitra",
        "op": f"baat_{entry_id}",
        "answer": line,
        "steps": [],
        "fallback": True,
        "fallback_kind": "baat",
        "baat_id": entry_id,
        "plain_reply": True,
        "plain": True,
    }


def baat_result(question, flavour=None):
    """The small-talk reply for `question`, or None.

    Assumes the caller's global vetoes already ran
    (wave154_result); the gates here are the baat-specific
    ones: short message, no digit (after class mentions
    are stripped), phrase + filler remainder."""
    q = str(question or "").lower()
    q = re.sub(r"[!?.,;:\"।]+", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    if not q or len(q.split()) > 12:
        return None
    if any(ch.isdigit() for ch in _strip_class_mentions(q)):
        return None
    flavour = _resolve_flavour(question, flavour)
    # Thanks first (prefix gate): a longer thank-you must
    # not fall to the filler gate and die.
    for start in _THANKS_STARTS:
        if q == start or q.startswith(start + " "):
            if not _has_ask_word(q) \
                    and not _has_problem_payload(q):
                return _plain_baat("thanks",
                                   _THANKS_LINES[flavour])
            return None
    for entry in BAAT:
        for phrase in entry["phrases"]:
            if phrase in q:
                remainder = q.replace(phrase, " ", 1)
                if _all_filler_ext(remainder):
                    return _plain_baat(entry["id"],
                                       entry[flavour])
    return None


# ---------------------------------------------------------------------------
# Part B: GUIDANCE — authored maths guidance cards
# Each entry: trigger phrases + per-flavour answer gist,
# SHORT steps (the default card) and DETAIL lines (only
# ever appended when the student asks for detail — the
# Wave 136 rule). Content rules: evergreen facts only,
# every claim qualitative — no salary figures, no
# percentages, no guarantees (test_wave154 scans for it).
# ---------------------------------------------------------------------------

GUIDANCE = [
    {
        "id": "scope_career",
        "gate": "career",
        "triggers": (
            "maths me scope", "maths ka scope",
            "maths me kya scope", "scope of maths",
            "scope in maths", "maths me career",
            "maths me kya career", "career in maths",
            "maths lekar kya banege", "maths lekar kya ban",
            "maths leke kya", "maths lene se kya",
            "maths ka future", "maths padhne se kya",
            "maths me fayda", "maths lena faydemand",
            "ganit me scope", "ganit me career",
            "गणित में स्कोप", "गणित में करियर",
            "गणित लेकर क्या", "गणित में scope",
        ),
        "en": {
            "answer": "Scope of Maths — maths keeps the "
                      "most doors open after school",
            "steps": [
                "Engineering and technology: with Physics, "
                "Chemistry and Maths you can sit for JEE "
                "Main/Advanced and study B.Tech — the "
                "biggest route after 12th with Maths.",
                "Data and computers: Data Science, AI and "
                "software all stand on maths — a strong "
                "maths base makes these fields much "
                "easier to enter.",
                "Maths itself: B.Sc./B.S. in Maths or "
                "Statistics leads to research and "
                "teaching, and to institutes like ISI "
                "and CMI.",
                "More routes: Actuarial Science "
                "(insurance maths), NDA/Defence, "
                "Architecture, and banking & SSC exams — "
                "all of them ask for maths.",
            ],
            "detail": [
                "Actuarial Science: actuaries calculate "
                "risk for insurance and pension work; "
                "entry is through the ACET exam after "
                "12th with Maths.",
                "ISI (Kolkata) and CMI (Chennai) run "
                "their own entrance tests for B.Stat / "
                "B.Math and B.Sc. Maths — the pure-maths "
                "research route.",
                "Architecture (B.Arch) also needs Maths "
                "in Class 12, with JEE Main Paper 2 or "
                "NATA as the entrance.",
                "Whichever route you pick, the same thing "
                "matters most in school: concepts clear, "
                "not just formulas memorised.",
            ],
        },
        "roman": {
            "answer": "Maths ka Scope — maths school ke "
                      "baad sabse zyada raaste kholta hai",
            "steps": [
                "Engineering aur technology: Physics, "
                "Chemistry aur Maths ke saath tum JEE "
                "Main/Advanced dekar B.Tech kar sakte ho "
                "— 12th-maths ka sabse bada raasta.",
                "Data aur computer: Data Science, AI aur "
                "software — sab maths par khade hain; "
                "maths mazboot ho toh ye field aasan ho "
                "jaati hai.",
                "Khud Maths: B.Sc./B.S. Maths ya "
                "Statistics se research aur teaching ka "
                "raasta khulta hai, aur ISI, CMI jaise "
                "institutes bhi.",
                "Aur raaste: Actuarial Science (beema "
                "ka maths), NDA/Defence, Architecture, "
                "aur bank aur SSC exams — sab me maths "
                "kaam aata hai.",
            ],
            "detail": [
                "Actuarial Science: actuary beema aur "
                "pension ke risk ka hisaab lagate hain; "
                "entry 12th-maths ke baad ACET exam se "
                "hoti hai.",
                "ISI (Kolkata) aur CMI (Chennai) apne "
                "entrance test se B.Stat / B.Math aur "
                "B.Sc. Maths me lete hain — ye shudh "
                "maths-research ka raasta hai.",
                "Architecture (B.Arch) ke liye bhi Class "
                "12 me Maths chahiye; entrance JEE Main "
                "Paper 2 ya NATA hota hai.",
                "Jo bhi raasta chuno, school me ek hi "
                "baat sabse kaam ki hai: concept saaf, "
                "sirf formula ratta nahi.",
            ],
        },
        "dev": {
            "answer": "गणित का Scope — गणित school के बाद "
                      "सबसे ज़्यादा रास्ते खोलता है",
            "steps": [
                "Engineering और technology: Physics, "
                "Chemistry और गणित के साथ आप JEE "
                "Main/Advanced देकर B.Tech कर सकते हैं — "
                "12वीं-गणित का सबसे बड़ा रास्ता।",
                "Data और computer: Data Science, AI और "
                "software — सब गणित पर खड़े हैं; गणित "
                "मज़बूत हो तो ये क्षेत्र आसान हो जाते "
                "हैं।",
                "ख़ुद गणित: B.Sc./B.S. गणित या Statistics "
                "से research और शिक्षण का रास्ता खुलता "
                "है, और ISI, CMI जैसे संस्थान भी।",
                "और रास्ते: Actuarial Science (बीमा का "
                "गणित), NDA/Defence, Architecture, और "
                "bank व SSC परीक्षाएँ — सब में गणित काम "
                "आता है।",
            ],
            "detail": [
                "Actuarial Science: actuary बीमा और "
                "pension के risk का हिसाब लगाते हैं; "
                "entry 12वीं-गणित के बाद ACET परीक्षा से "
                "होती है।",
                "ISI (Kolkata) और CMI (Chennai) अपने "
                "entrance test से B.Stat / B.Math और "
                "B.Sc. गणित में लेते हैं — यह शुद्ध "
                "गणित-research का रास्ता है।",
                "Architecture (B.Arch) के लिए भी Class "
                "12 में गणित चाहिए; entrance JEE Main "
                "Paper 2 या NATA होता है।",
                "जो भी रास्ता चुनें, school में एक ही "
                "बात सबसे काम की है: concept स्पष्ट, "
                "सिर्फ़ सूत्र रट्टा नहीं।",
            ],
        },
    },
    {
        "id": "after_12th",
        "gate": "career",
        "triggers": (
            "12th ke baad", "12th ke bad", "12 ke baad",
            "after 12th", "12th pass ke baad",
            "inter ke baad", "12vi ke baad",
            "बारहवीं के बाद", "12वी के बाद",
            "12th ke baad kya", "12th ke baad course",
            "12th ke baad career",
        ),
        "en": {
            "answer": "After 12th with Maths — your main "
                      "routes",
            "steps": [
                "Engineering: JEE Main (for NITs, IIITs "
                "and most colleges) and JEE Advanced "
                "(for the IITs) — needs Physics, "
                "Chemistry and Maths in 12th.",
                "Universities: CUET-UG is the common "
                "entrance for central universities — "
                "B.Sc. Maths, Statistics, Computer "
                "Science and many more courses.",
                "Pure maths route: ISI and CMI hold "
                "their own entrance tests for B.Stat / "
                "B.Math and B.Sc. programmes.",
                "Also open to you: NDA (defence), B.Arch "
                "(architecture), Actuarial Science "
                "through ACET, and integrated M.Sc. "
                "programmes.",
            ],
            "detail": [
                "Fix your target early: one main route "
                "plus one backup route is a healthy "
                "plan.",
                "Check every exam's official website for "
                "dates and eligibility — they change "
                "every year, so never trust old "
                "screenshots or rumours.",
                "If you are in Class 11, this is the "
                "best time to build: JEE and CUET both "
                "test the Class 11 + 12 syllabus, so "
                "strong concepts now pay off twice.",
                "Commerce-side doors like BBA and CA "
                "Foundation also stay open to many Maths "
                "students — check each course's own "
                "eligibility before deciding.",
            ],
        },
        "roman": {
            "answer": "12th ke baad Maths se — tumhare "
                      "main raaste",
            "steps": [
                "Engineering: JEE Main (NITs, IIITs aur "
                "zyadatar colleges ke liye) aur JEE "
                "Advanced (IITs ke liye) — 12th me "
                "Physics, Chemistry, Maths chahiye.",
                "Universities: CUET-UG central "
                "universities ka common entrance hai — "
                "B.Sc. Maths, Statistics, Computer "
                "Science aur kai courses.",
                "Shudh maths ka raasta: ISI aur CMI "
                "apne entrance test se B.Stat / B.Math "
                "aur B.Sc. me lete hain.",
                "Ye bhi khule hain: NDA (defence), "
                "B.Arch (architecture), ACET se "
                "Actuarial Science, aur integrated "
                "M.Sc. programmes.",
            ],
            "detail": [
                "Target pehle tay karo: ek main raasta "
                "aur ek backup raasta — ye sahi plan "
                "hai.",
                "Har exam ki dates aur eligibility uski "
                "official website par dekho — ye har "
                "saal badalti hain, purane screenshot "
                "ya afwaah par bharosa mat karo.",
                "Agar tum Class 11 me ho, yahi sabse "
                "acha time hai: JEE aur CUET dono 11 + "
                "12 ka syllabus poochte hain, toh ab "
                "ke mazboot concept do jagah kaam "
                "aayenge.",
                "Commerce-side ke raaste jaise BBA aur "
                "CA Foundation bhi kai Maths students "
                "ke liye khule rehte hain — faisla "
                "karne se pehle course ki apni "
                "eligibility dekh lena.",
            ],
        },
        "dev": {
            "answer": "12वीं के बाद गणित से — आपके मुख्य "
                      "रास्ते",
            "steps": [
                "Engineering: JEE Main (NITs, IIITs और "
                "अधिकांश colleges के लिए) और JEE "
                "Advanced (IITs के लिए) — 12वीं में "
                "Physics, Chemistry, गणित चाहिए।",
                "Universities: CUET-UG central "
                "universities का common entrance है — "
                "B.Sc. गणित, Statistics, Computer "
                "Science और कई courses।",
                "शुद्ध गणित का रास्ता: ISI और CMI अपने "
                "entrance test से B.Stat / B.Math और "
                "B.Sc. में लेते हैं।",
                "ये भी खुले हैं: NDA (रक्षा), B.Arch "
                "(architecture), ACET से Actuarial "
                "Science, और integrated M.Sc. "
                "programmes।",
            ],
            "detail": [
                "लक्ष्य पहले तय कीजिए: एक मुख्य रास्ता "
                "और एक backup रास्ता — यह सही plan है।",
                "हर परीक्षा की dates और eligibility "
                "उसकी official website पर देखिए — ये हर "
                "साल बदलती हैं, पुराने screenshot या "
                "अफ़वाह पर भरोसा मत कीजिए।",
                "अगर आप Class 11 में हैं, यही सबसे "
                "अच्छा समय है: JEE और CUET दोनों 11 + "
                "12 का syllabus पूछते हैं, तो अब के "
                "मज़बूत concept दो जगह काम आएँगे।",
                "Commerce-side के रास्ते जैसे BBA और CA "
                "Foundation भी कई गणित छात्रों के लिए "
                "खुले रहते हैं — फ़ैसला करने से पहले "
                "course की अपनी eligibility देख "
                "लीजिए।",
            ],
        },
    },
    {
        "id": "subject_choice",
        "gate": "career",
        "triggers": (
            "maths lu ya", "maths lun ya", "maths ya bio",
            "maths ya biology", "maths lu ya bio",
            "pcm ya pcb", "pcm lu ya", "maths lu ya "
            "commerce", "maths ya commerce",
            "maths lena chahiye ya", "kaun si stream",
            "konsi stream", "kaunsi stream",
            "stream kaun si", "pcm vs pcb",
            "maths vs biology", "maths vs bio",
            "maths or biology", "maths or bio",
            "pcm or pcb", "take maths or",
            "गणित लूँ या", "गणित या जीव",
        ),
        "en": {
            "answer": "Maths or Biology in Class 11 — "
                      "decide by the door you want open",
            "steps": [
                "Maths keeps more doors open: "
                "engineering, data, defence, "
                "architecture and B.Sc. courses accept "
                "Maths students, and most commerce-side "
                "courses do too.",
                "Biology is a must only for the medical "
                "route — MBBS and related fields, "
                "through NEET.",
                "Many boards let you take BOTH Maths "
                "and Biology — heavier, but it keeps "
                "both doors open if you are truly "
                "unsure.",
                "Ask yourself two things: which subject "
                "will you enjoy studying every day, and "
                "which career sounds like yours?",
            ],
            "detail": [
                "A subject dropped in Class 11 is very "
                "hard to add back later; a subject you "
                "keep can always be left after 12th.",
                "If you enjoy solving problems and "
                "logic, Maths usually rewards practice "
                "well; Biology asks for lots of reading "
                "and memory.",
                "Talk it over with your teachers and "
                "parents with a target in mind — but "
                "the daily studying is yours, so your "
                "own interest matters most.",
                "Whatever you choose, Ganitra is here "
                "for the maths side, chapter by "
                "chapter.",
            ],
        },
        "roman": {
            "answer": "Class 11 me Maths ya Biology — "
                      "us darwaze se socho jo khula "
                      "rakhna hai",
            "steps": [
                "Maths zyada darwaze khule rakhta hai: "
                "engineering, data, defence, "
                "architecture aur B.Sc. courses Maths "
                "students ko lete hain, aur commerce-"
                "side ke zyadatar courses bhi.",
                "Biology sirf medical raaste ke liye "
                "compulsory hai — MBBS aur usse jude "
                "fields, NEET ke through.",
                "Kai boards me Maths aur Biology DONO "
                "lene ki suvidha hoti hai — thoda "
                "bhaari padta hai, lekin sach me "
                "confused ho toh dono darwaze khule "
                "rehte hain.",
                "Khud se do sawal poochho: kaun sa "
                "subject tumhe roz padhne me acha "
                "lagega, aur kaun sa career tumhara "
                "lagta hai?",
            ],
            "detail": [
                "Class 11 me chhoda hua subject baad "
                "me wapas jodna bahut mushkil hota "
                "hai; rakha hua subject 12th ke baad "
                "hamesha chhoda ja sakta hai.",
                "Agar tumhe problems aur logic pasand "
                "hai, Maths aam taur par practice ka "
                "acha phal deta hai; Biology me "
                "padhna aur yaad rakhna zyada hota "
                "hai.",
                "Teachers aur parents se target saamne "
                "rakh kar baat karo — lekin roz ki "
                "padhai tumhari hai, isliye tumhari "
                "apni pasand sabse zyada maayne "
                "rakhti hai.",
                "Jo bhi chuno, maths ki taraf ke liye "
                "Ganitra yahi hai, chapter by "
                "chapter.",
            ],
        },
        "dev": {
            "answer": "Class 11 में गणित या जीव विज्ञान — "
                      "उस दरवाज़े से सोचिए जो खुला रखना है",
            "steps": [
                "गणित ज़्यादा दरवाज़े खुले रखता है: "
                "engineering, data, रक्षा, "
                "architecture और B.Sc. courses गणित "
                "छात्रों को लेते हैं, और commerce-side "
                "के अधिकांश courses भी।",
                "जीव विज्ञान सिर्फ़ medical रास्ते के "
                "लिए ज़रूरी है — MBBS और उससे जुड़े "
                "क्षेत्र, NEET के माध्यम से।",
                "कई boards में गणित और जीव विज्ञान "
                "दोनों लेने की सुविधा होती है — थोड़ा "
                "भारी पड़ता है, लेकिन सच में असमंजस "
                "हो तो दोनों दरवाज़े खुले रहते हैं।",
                "ख़ुद से दो सवाल पूछिए: कौन सा विषय "
                "आपको रोज़ पढ़ने में अच्छा लगेगा, और "
                "कौन सा career आपका लगता है?",
            ],
            "detail": [
                "Class 11 में छोड़ा हुआ विषय बाद में "
                "वापस जोड़ना बहुत मुश्किल होता है; "
                "रखा हुआ विषय 12वीं के बाद हमेशा "
                "छोड़ा जा सकता है।",
                "अगर आपको problems और तर्क पसंद है, "
                "गणित आमतौर पर अभ्यास का अच्छा फल देता "
                "है; जीव विज्ञान में पढ़ना और याद "
                "रखना ज़्यादा होता है।",
                "Teachers और parents से लक्ष्य सामने "
                "रखकर बात कीजिए — लेकिन रोज़ की पढ़ाई "
                "आपकी है, इसलिए आपकी अपनी पसंद सबसे "
                "ज़्यादा मायने रखती है।",
                "जो भी चुनें, गणित की तरफ़ के लिए "
                "Ganitra यहीं है, chapter by chapter।",
            ],
        },
    },
    {
        "id": "entrance_exams",
        "gate": "career",
        "triggers": (
            "jee main", "jee advanced", "jee exam",
            "jee kya", "jee ke liye", "jee ke baare",
            "cuet", "isi exam", "isi kya", "cmi exam",
            "nda exam", "nda kya", "bitsat",
            "entrance exam", "entrance test",
            "engineering entrance", "engineering ka exam",
            "engineering ke liye exam", "kaun sa entrance",
            "konsa entrance", "प्रवेश परीक्षा",
        ),
        "en": {
            "answer": "Entrance Exams after 12th Maths — "
                      "the main ones",
            "steps": [
                "JEE Main (by NTA): for NITs, IIITs and "
                "most engineering colleges — and it is "
                "also the qualifying test for JEE "
                "Advanced.",
                "JEE Advanced: for the IITs — only the "
                "top JEE Main performers can sit for "
                "it.",
                "CUET-UG: the common test for central "
                "universities — B.Sc. Maths, "
                "Statistics, Computer Science and many "
                "other courses.",
                "ISI and CMI: their own demanding "
                "entrance tests — B.Stat / B.Math at "
                "ISI, B.Sc. Maths and Computer Science "
                "at CMI; the research route.",
            ],
            "detail": [
                "NDA (by UPSC, held twice a year): for "
                "the defence forces — its written test "
                "has a full Maths paper, and Maths in "
                "12th is required.",
                "BITSAT: BITS Pilani's own entrance "
                "test for its engineering programmes.",
                "JEE Main Paper 2 and NATA: the "
                "architecture (B.Arch) entrances — "
                "Maths in 12th is compulsory for them.",
                "Dates and eligibility change every "
                "year — always confirm them on the "
                "exam's official website before "
                "applying.",
            ],
        },
        "roman": {
            "answer": "12th Maths ke baad Entrance Exams — "
                      "main exams",
            "steps": [
                "JEE Main (NTA karata hai): NITs, IIITs "
                "aur zyadatar engineering colleges ke "
                "liye — aur yahi JEE Advanced ke liye "
                "qualify karne ka test bhi hai.",
                "JEE Advanced: IITs ke liye — isme "
                "sirf JEE Main ke top students baith "
                "sakte hain.",
                "CUET-UG: central universities ka "
                "common test — B.Sc. Maths, "
                "Statistics, Computer Science aur kai "
                "courses.",
                "ISI aur CMI: inke apne kathin entrance "
                "test hote hain — ISI me B.Stat / "
                "B.Math, CMI me B.Sc. Maths aur "
                "Computer Science; ye research ka "
                "raasta hai.",
            ],
            "detail": [
                "NDA (UPSC, saal me do baar): defence "
                "forces ke liye — iske written test me "
                "ek poora Maths paper hota hai, aur "
                "12th me Maths compulsory hai.",
                "BITSAT: BITS Pilani ka apna entrance "
                "test, uske engineering programmes ke "
                "liye.",
                "JEE Main Paper 2 aur NATA: "
                "architecture (B.Arch) ke entrance — "
                "inke liye 12th me Maths compulsory "
                "hai.",
                "Dates aur eligibility har saal "
                "badalti hain — apply karne se pehle "
                "exam ki official website par hi "
                "confirm karo.",
            ],
        },
        "dev": {
            "answer": "12वीं गणित के बाद प्रवेश परीक्षाएँ — "
                      "मुख्य परीक्षाएँ",
            "steps": [
                "JEE Main (NTA कराता है): NITs, IIITs "
                "और अधिकांश engineering colleges के "
                "लिए — और यही JEE Advanced के लिए "
                "qualify करने का test भी है।",
                "JEE Advanced: IITs के लिए — इसमें "
                "सिर्फ़ JEE Main के शीर्ष छात्र बैठ "
                "सकते हैं।",
                "CUET-UG: central universities का "
                "common test — B.Sc. गणित, Statistics, "
                "Computer Science और कई courses।",
                "ISI और CMI: इनके अपने कठिन entrance "
                "test होते हैं — ISI में B.Stat / "
                "B.Math, CMI में B.Sc. गणित और "
                "Computer Science; यह research का "
                "रास्ता है।",
            ],
            "detail": [
                "NDA (UPSC, साल में दो बार): रक्षा "
                "बलों के लिए — इसके written test में "
                "एक पूरा गणित paper होता है, और 12वीं "
                "में गणित ज़रूरी है।",
                "BITSAT: BITS Pilani का अपना entrance "
                "test, उसके engineering programmes के "
                "लिए।",
                "JEE Main Paper 2 और NATA: "
                "architecture (B.Arch) के entrance — "
                "इनके लिए 12वीं में गणित अनिवार्य है।",
                "Dates और eligibility हर साल बदलती "
                "हैं — आवेदन से पहले परीक्षा की "
                "official website पर ही confirm "
                "कीजिए।",
            ],
        },
    },
]


GUIDANCE += [
    {
        "id": "improve",
        "gate": "subject",
        "triggers": (
            "improve", "improvement", "strong kaise",
            "mazboot kaise", "मज़बूत कैसे", "behtar kaise",
            "बेहतर कैसे", "better kaise", "sudhar kaise",
            "सुधार कैसे", "कैसे सुधार", "कैसे बेहतर",
            "कैसे मज़बूत", "maths acha kaise",
            "maths achha kaise", "maths achcha kaise",
            "maths weak hai", "mera maths weak",
            "maths me acha kaise", "maths better kaise",
            "ganit sudhar", "maths strong",
            "weak hai maths",
        ),
        "en": {
            "answer": "Improve Your Maths — repair the "
                      "base, then climb",
            "steps": [
                "Find the exact weak chapters first — "
                "most of 'weak in maths' is really two "
                "or three weak chapters, often "
                "fractions, sign rules and tables.",
                "For each weak chapter: study the "
                "solved examples first, then do the "
                "exercises in writing — maths improves "
                "by doing, not by watching.",
                "Give maths 30–45 minutes daily; small "
                "daily practice beats one long weekly "
                "sitting.",
                "Keep a mistake copy: every wrong "
                "question goes into it, and you redo "
                "it after 2–3 days.",
            ],
            "detail": [
                "Use Ganitra's Practice for daily "
                "questions and Chapter Test to check "
                "one chapter at a time — that shows "
                "exactly which chapter is still weak.",
                "Never leave a doubt overnight — ask "
                "your teacher, a friend, or send the "
                "question here the same day.",
                "Always write full steps, never only "
                "the answer: in exams, written steps "
                "earn marks even when the final answer "
                "slips.",
                "Judge your progress once a month with "
                "one full test — not every day with "
                "worry.",
            ],
        },
        "roman": {
            "answer": "Maths Improve Karo — pehle neev, "
                      "phir unchai",
            "steps": [
                "Sabse pehle exact weak chapters "
                "dhoondo — 'maths me weak' aksar asal "
                "me do-teen weak chapter hote hain, "
                "khaas taur par fractions, sign ke "
                "niyam aur pahade.",
                "Har weak chapter ke liye: pehle "
                "solved examples padho, phir exercises "
                "likh-likh kar karo — maths dekhne se "
                "nahi, karne se sudharta hai.",
                "Maths ko roz 30–45 minute do; roz ki "
                "chhoti practice hafte ki ek lambi "
                "baithak se behtar hai.",
                "Galtiyon ki copy banao: har galat "
                "sawal usme likho, aur 2–3 din baad "
                "use dobara karo.",
            ],
            "detail": [
                "Ganitra ke Practice se roz ke sawal "
                "karo aur Chapter Test se ek-ek "
                "chapter check karo — pata chalega "
                "kaun sa chapter ab bhi weak hai.",
                "Koi doubt raat bhar mat rakho — usi "
                "din teacher, dost ya yahan bhej kar "
                "saaf karo.",
                "Hamesha poore steps likho, sirf jawab "
                "nahi: exam me likhe hue steps par "
                "bhi marks milte hain, bhale hi aakhiri "
                "jawab fisal jaye.",
                "Apni progress mahine me ek baar ek "
                "full test se naapo — roz marks ki "
                "chinta se nahi.",
            ],
        },
        "dev": {
            "answer": "गणित सुधारिए — पहले नींव, फिर ऊँचाई",
            "steps": [
                "सबसे पहले exact weak chapters खोजिए — "
                "'गणित में कमज़ोर' असल में अक्सर दो-"
                "तीन weak chapter होते हैं, ख़ास तौर "
                "पर भिन्न, चिह्नों के नियम और पहाड़े।",
                "हर weak chapter के लिए: पहले हल किए "
                "उदाहरण पढ़िए, फिर अभ्यास लिख-लिखकर "
                "कीजिए — गणित देखने से नहीं, करने से "
                "सुधरता है।",
                "गणित को रोज़ 30–45 minute दीजिए; "
                "रोज़ का छोटा अभ्यास हफ़्ते की एक लंबी "
                "बैठक से बेहतर है।",
                "ग़लतियों की copy बनाइए: हर ग़लत सवाल "
                "उसमें लिखिए, और 2–3 दिन बाद उसे "
                "दोबारा कीजिए।",
            ],
            "detail": [
                "Ganitra के Practice से रोज़ के सवाल "
                "कीजिए और Chapter Test से एक-एक "
                "chapter check कीजिए — पता चलेगा कौन "
                "सा chapter अब भी weak है।",
                "कोई doubt रात भर मत रखिए — उसी दिन "
                "शिक्षक, दोस्त या यहाँ भेजकर साफ़ "
                "कीजिए।",
                "हमेशा पूरे चरण लिखिए, सिर्फ़ उत्तर "
                "नहीं: परीक्षा में लिखे हुए चरणों पर "
                "भी अंक मिलते हैं, भले ही अंतिम उत्तर "
                "फिसल जाए।",
                "अपनी प्रगति महीने में एक बार एक full "
                "test से नापिए — रोज़ अंकों की चिंता "
                "से नहीं।",
            ],
        },
    },
    {
        "id": "exam_prep",
        "gate": "subject",
        "triggers": (
            "exam aa gaye", "exam aa gaya",
            "exam aane wala", "exam aane wale",
            "exam near", "exam paas hai", "exam pas hai",
            "exam close hai", "kal exam", "parso exam",
            "exam is near", "exams are near",
            "exam is close", "exams aa gaye",
            "exam aa raha",
            "boards aa gaye", "board exam aa",
            "board aa gaye", "timetable", "time table",
            "समय सारणी", "समय-सारणी", "study plan",
            "padhai ka plan", "revision plan",
            "plan kaise banau", "plan banau",
            "last moment", "last time revision",
            "परीक्षा आ गई", "परीक्षा आने वाली",
            "कल परीक्षा",
        ),
        "en": {
            "answer": "Exam Preparation — weak chapters "
                      "first, papers daily",
            "steps": [
                "Start from your weak chapters: list "
                "the chapters you fear most and finish "
                "those first — the easy ones only need "
                "revision.",
                "Revise in short rounds: whatever you "
                "study today, revise it after 1 day, "
                "then after 3 days, then after a week "
                "— that is how it stays till the exam.",
                "Solve previous years' papers and take "
                "mock tests in full exam timing — "
                "Ganitra's Papers section has board "
                "papers, and Chapter Test checks one "
                "chapter at a time.",
                "Write everything by hand: reading a "
                "solution is not preparation — solving "
                "it on paper is.",
            ],
            "detail": [
                "Timetable kaise banaye: give the "
                "biggest daily slot to your weakest "
                "chapter, keep one fixed slot only for "
                "revision, and one full mock paper "
                "every week.",
                "Keep a galtiyon ki copy (mistake "
                "notebook): write down every mistake "
                "from your tests — before the exam, "
                "this copy becomes your best revision "
                "book.",
                "In the last week: no new chapters — "
                "only papers, the mistake copy and "
                "formula revision.",
                "Sleep properly the night before the "
                "exam; a fresh mind earns more than one "
                "extra chapter.",
            ],
        },
        "roman": {
            "answer": "Exam ki Taiyari — pehle weak "
                      "chapters, roz papers",
            "steps": [
                "Apne weak chapters se shuru karo: jin "
                "chapters se sabse zyada dar lagta "
                "hai unki list banao aur pehle unhe "
                "khatm karo — aasan chapters ko sirf "
                "revision chahiye.",
                "Chhote rounds me revision karo: jo "
                "aaj padha, use 1 din baad, phir 3 din "
                "baad, phir ek hafte baad dohrao — "
                "aise hi woh exam tak yaad rehta hai.",
                "Pichle saalon ke papers solve karo "
                "aur pure exam-time me mock test do — "
                "Ganitra ke Papers section me board "
                "papers hain, aur Chapter Test se ek-"
                "ek chapter check hota hai.",
                "Sab kuch haath se likh kar karo: "
                "solution padhna taiyari nahi hai — "
                "paper par solve karna taiyari hai.",
            ],
            "detail": [
                "Timetable kaise banaye: sabse badi "
                "daily slot sabse weak chapter ko do, "
                "ek slot sirf revision ke liye rakho, "
                "aur har hafte ek full mock paper do.",
                "Galtiyon ki copy rakho: tests me hui "
                "har galti usme likho — exam se pehle "
                "ye copy tumhari sabse achi revision "
                "book banegi.",
                "Aakhiri hafte me: koi naya chapter "
                "nahi — sirf papers, galtiyon ki copy "
                "aur formula revision.",
                "Exam se ek raat pehle theek se so "
                "jao; taaza dimaag ek extra chapter se "
                "zyada kaam aata hai.",
            ],
        },
        "dev": {
            "answer": "परीक्षा की तैयारी — पहले weak "
                      "chapters, रोज़ papers",
            "steps": [
                "अपने weak chapters से शुरू कीजिए: जिन "
                "chapters से सबसे ज़्यादा डर लगता है "
                "उनकी सूची बनाइए और पहले उन्हें ख़त्म "
                "कीजिए — आसान chapters को सिर्फ़ "
                "revision चाहिए।",
                "छोटे rounds में revision कीजिए: जो "
                "आज पढ़ा, उसे 1 दिन बाद, फिर 3 दिन "
                "बाद, फिर एक हफ़्ते बाद दोहराइए — ऐसे "
                "ही वह परीक्षा तक याद रहता है।",
                "पिछले सालों के papers हल कीजिए और "
                "पूरे exam-time में mock test दीजिए — "
                "Ganitra के Papers section में board "
                "papers हैं, और Chapter Test से एक-एक "
                "chapter check होता है।",
                "सब कुछ हाथ से लिखकर कीजिए: solution "
                "पढ़ना तैयारी नहीं है — paper पर हल "
                "करना तैयारी है।",
            ],
            "detail": [
                "Timetable कैसे बनाएँ: सबसे बड़ी "
                "daily slot सबसे weak chapter को "
                "दीजिए, एक slot सिर्फ़ revision के "
                "लिए रखिए, और हर हफ़्ते एक full mock "
                "paper दीजिए।",
                "ग़लतियों की copy रखिए: tests में हुई "
                "हर ग़लती उसमें लिखिए — परीक्षा से "
                "पहले यह copy आपकी सबसे अच्छी "
                "revision book बनेगी।",
                "आख़िरी हफ़्ते में: कोई नया chapter "
                "नहीं — सिर्फ़ papers, ग़लतियों की "
                "copy और सूत्र revision।",
                "परीक्षा से एक रात पहले ठीक से सो "
                "जाइए; ताज़ा दिमाग़ एक extra chapter "
                "से ज़्यादा काम आता है।",
            ],
        },
    },
    {
        "id": "motivation",
        "gate": "subject",
        "triggers": (
            "mann nahi lag", "man nahi lag",
            "mann nhi lag", "man nhi lag",
            "मन नहीं लग", "पढ़ाई में मन नहीं",
            "padhai me man nahi", "fail ho jaunga",
            "fail ho jaaunga", "fail ho jaungi",
            "fail hone ka dar", "fail ka dar",
            "फेल हो जाऊंगा", "फेल हो जाऊँगी",
            "फेल होने का डर", "demotivate",
            "demotivated", "motivation nahi",
            "stress hai", "stress ho raha",
            "stressed hu", "stressed hoon", "stressed",
            "exam stress", "exam ka stress",
            "padhai ka stress", "tension ho rahi",
            "tension ho raha",
            "tension hai", "टेंशन हो रही", "तनाव है",
            "pareshan hu", "pareshan hoon",
            "bahut pareshan", "परेशान हूँ",
            "himmat nahi ho rahi", "haar maan",
            "haar man li", "give up kar",
            "padhai chhod", "रोना आ रहा",
        ),
        "en": {
            "answer": "Listen — one weak chapter does "
                      "not mean failure",
            "steps": [
                "Feeling like this before exams is "
                "very common — even toppers have felt "
                "it. It says nothing about your "
                "ability.",
                "Do not fight the whole syllabus "
                "today. Take ONE easy chapter and "
                "solve just 5 questions from it — "
                "starting small is what breaks the "
                "fear.",
                "Compare yourself only with your own "
                "last month, never with classmates — "
                "your race is with your own yesterday.",
                "And if the stress ever feels too "
                "heavy — sleep gone, crying often, "
                "mind never settling — please talk to "
                "a parent, a teacher or an elder you "
                "trust. Asking for help is strength, "
                "not weakness.",
            ],
            "detail": [
                "A small fixed routine helps more "
                "than motivation videos: same study "
                "time daily, phone in another room, "
                "one chapter at a time.",
                "Write the worry on paper and next to "
                "it one small action for today — "
                "worries shrink when they turn into "
                "tasks.",
                "Send me the chapter that scares you "
                "most — we will start from its "
                "easiest question, together.",
            ],
        },
        "roman": {
            "answer": "Suno — ek weak chapter ka matlab "
                      "fail hona nahi hai",
            "steps": [
                "Exam se pehle aisa mehsoos hona bahut "
                "aam hai — toppers ko bhi hua hai. Isse "
                "tumhari kabiliyat naapi nahi jaati.",
                "Aaj poore syllabus se mat lado. Ek "
                "easy chapter lo aur uske sirf 5 sawal "
                "hal karo — chhoti shuruaat hi dar ko "
                "todti hai.",
                "Apni tulna sirf apne pichle mahine se "
                "karo, classmates se kabhi nahi — "
                "tumhari daud tumhare apne kal se hai.",
                "Aur agar kabhi stress bahut zyada "
                "bhaari lage — neend ud jaye, baar-"
                "baar rona aaye, man kahin na lage — "
                "toh kisi bade se baat karo: maa-baap, "
                "teacher, ya jis par bharosa ho. Madad "
                "maangna taakat hai, kamzori nahi.",
            ],
            "detail": [
                "Ek chhoti fix routine motivation "
                "videos se zyada kaam karti hai: roz "
                "ek hi study time, phone dusre kamre "
                "me, ek baar me ek chapter.",
                "Apni chinta kagaz par likho aur uske "
                "saamne aaj ka ek chhota kaam — "
                "chintaein kaam ban jaye toh chhoti "
                "ho jaati hain.",
                "Mujhe woh chapter bhejo jisse sabse "
                "zyada dar lagta hai — hum uske sabse "
                "easy sawal se shuru karenge, saath "
                "me.",
            ],
        },
        "dev": {
            "answer": "सुनिए — एक weak chapter का मतलब "
                      "fail होना नहीं है",
            "steps": [
                "परीक्षा से पहले ऐसा महसूस होना बहुत "
                "आम है — toppers को भी हुआ है। इससे "
                "आपकी क़ाबिलियत नहीं नापी जाती।",
                "आज पूरे syllabus से मत लड़िए। एक "
                "easy chapter लीजिए और उसके सिर्फ़ 5 "
                "सवाल हल कीजिए — छोटी शुरुआत ही डर "
                "को तोड़ती है।",
                "अपनी तुलना सिर्फ़ अपने पिछले महीने "
                "से कीजिए, classmates से कभी नहीं — "
                "आपकी दौड़ आपके अपने कल से है।",
                "और अगर कभी stress बहुत ज़्यादा भारी "
                "लगे — नींद उड़ जाए, बार-बार रोना आए, "
                "मन कहीं न लगे — तो किसी बड़े से बात "
                "कीजिए: माँ-बाप, शिक्षक, या जिस पर "
                "भरोसा हो। मदद माँगना ताक़त है, "
                "कमज़ोरी नहीं।",
            ],
            "detail": [
                "एक छोटी fix routine motivation "
                "videos से ज़्यादा काम करती है: रोज़ "
                "एक ही study time, phone दूसरे कमरे "
                "में, एक बार में एक chapter।",
                "अपनी चिंता काग़ज़ पर लिखिए और उसके "
                "सामने आज का एक छोटा काम — चिंताएँ "
                "काम बन जाएँ तो छोटी हो जाती हैं।",
                "मुझे वह chapter भेजिए जिससे सबसे "
                "ज़्यादा डर लगता है — हम उसके सबसे "
                "easy सवाल से शुरू करेंगे, साथ में।",
            ],
        },
    },
]

# Sequence words for the after_12th entry: "12 ke baad
# kya aayega" is a number-series question, not a career
# ask — the bare "12 ke baad" trigger must not swallow
# it.
_SEQUENCE_WORDS = (
    "sankhya", "संख्या", "series", "agla", "अगला",
    "aayega", "आएगा", "pattern",
)


# Solver-topic remnant words for the entrance entry: a
# JEE/CUET-flavoured PROBLEM ("JEE Main: derivative of
# sin x") must stay with the solver even though it names
# an exam. Guidance asks about exams never carry these.
_ENTRANCE_PROBLEM_WORDS = (
    "derivative", "integral", "differentiate", "sin ",
    "cos ", "tan ", "log ", "matrix", "determinant",
    "limit ", "summation", "probability of", "equation of",
)


def _guidance_result(entry, flavour):
    text = entry[flavour]
    return {
        "type": "Maths guidance",
        "op": f"guidance_{entry['id']}",
        "answer": text["answer"],
        "steps": list(text["steps"]),
        "fallback": True,
        "fallback_kind": "guidance",
        "guidance_id": entry["id"],
        # The card's own flavour, so a later detail ask
        # expands it in the SAME language (detail.py
        # prefers this over re-deriving a flavour from
        # the follow-up's text).
        "guidance_flavour": flavour,
    }


def guidance_detail_steps(entry_id, flavour):
    """The DETAIL lines of one guidance entry in one
    flavour (detail.py's guidance branch appends them
    when the student asks for detail). [] when the id
    or flavour is unknown."""
    if flavour not in ("en", "roman", "dev"):
        flavour = "en"
    for entry in GUIDANCE:
        if entry["id"] == entry_id:
            return list(entry[flavour].get("detail") or [])
    return []


def guidance_result(question, flavour=None):
    """The authored guidance card for `question`, or
    None. Assumes the caller's global vetoes already ran
    (wave154_result); the gates here are per-entry."""
    q = str(question or "").lower()
    if not q.strip():
        return None
    flavour = _resolve_flavour(question, flavour)
    # Subject choice first: its "maths vs biology" shape
    # is a guidance ask, not a difference-card ask, so it
    # is checked before the difference veto below.
    for entry in GUIDANCE:
        if entry["id"] != "subject_choice":
            continue
        if _career_gate(q) and any(
                t in q for t in entry["triggers"]):
            return _guidance_result(entry, flavour)
    if any(m in q for m in _DIFF_MARKERS):
        return None
    # after_12th outranks scope_career when both match:
    # "12th ke baad maths leke kya kar sakte hai" carries
    # the scope trigger "maths leke kya", but the precise
    # intent is the after-12th routes card.
    ordered = sorted(
        GUIDANCE,
        key=lambda e: 0 if e["id"] == "after_12th" else 1)
    for entry in ordered:
        if entry["id"] == "subject_choice":
            continue
        if not any(t in q for t in entry["triggers"]):
            continue
        if entry["id"] == "after_12th" and any(
                w in q for w in _SEQUENCE_WORDS):
            continue
        if entry["gate"] == "career":
            if not _career_gate(q):
                return None
            if entry["id"] == "entrance_exams" and any(
                    w in q for w in _ENTRANCE_PROBLEM_WORDS):
                return None
        elif not _subject_gate(q):
            return None
        return _guidance_result(entry, flavour)
    return None


def wave154_result(question, flavour=None):
    """The Wave 154 entry point (fallback.with_fallback,
    right after the maths_meta layer): guidance first
    (the substantive ask), then small talk. None when
    neither layer honestly owns the message.

    The global anti-hijack vetoes run here, once, before
    either layer is consulted: a real problem, an MCQ
    set, a digit+ask payload or a concept ask is NEVER
    small talk and NEVER guidance."""
    q = str(question or "").lower()
    if not q.strip():
        return None
    if _has_problem_payload(q) or _is_concept_ask(q):
        return None
    result = guidance_result(question, flavour)
    if result is not None:
        return result
    return baat_result(question, flavour)
