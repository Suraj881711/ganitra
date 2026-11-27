"""Wave 111: the maths-META layer — maths history/creator facts
and study/practice/exam advice.

Suraj raised this himself (17 Nov 2026): students ask maths
questions that are not computations — "maths kaise practice
karu", "exam me question kaise solve karne chahiye", "ye topic
kisne banaya", "ye theorem kisne prove ki". Before this wave
those asks were mishandled in three ways:

  * a WHO question got the WHAT card ("Pythagoras theorem
    kisne banaya tha?" -> the theorem STATEMENT card) because
    the concept layers match the topic keyword and never look
    at the question's shape;
  * a person question ("Shakuntala Devi kaun thi?") and every
    advice question ("Maths ki practice kaise karu?") fell
    through every layer to the one-line not-found;
  * nothing in between was offered to the AI fallback either,
    because those asks classify as "gibberish" — a kind the
    AI chain never sees.

This module is a small CURATED layer, in the same spirit as
concepts.py: hand-checked facts and teacher advice, matched
by question SHAPE + topic, never by keyword alone.

  * HISTORY entries fire only when a WHO shape (kisne / kaun
    tha / who / father of / किसने / कौन था ...) AND one of
    the entry's topic/person keywords are both present. The
    double gate is what keeps "Pythagoras theorem kya hai?"
    (no who shape) on its statement card and "Trigonometry
    me kaun sa formula lagta hai?" (no who PHRASE — "kaun sa"
    is not a marker) on the concept layers.
  * ADVICE entries fire on study-behaviour trigger phrases
    (practice, revision, silly mistakes ...) gated by a
    maths signal — or, when no maths word is present, by the
    absence of any OTHER named subject ("History ki
    taiyaari kaise karu?" must not become maths advice).
    Concept how-tos ("area kaise nikalte hai?") carry none
    of the triggers and are untouched.
  * A computation veto (digit-operator-digit) keeps every
    real problem out, whatever words it carries.

Facts are the scholarly consensus, kept short and honest
about shared/earlier credit (Pythagoras was known in Babylon
and India earlier; Pascal's triangle is India's Meru-prastara
long before Pascal; calculus is Newton AND Leibniz). No
invented dates; circa markers (~) where the year is not exact.

Result dicts mirror the concept-card shape ({type, op,
answer, steps, fallback, fallback_kind}) so every renderer
works unchanged. fallback_kind is "history" / "advice" —
deliberately NOT in fallback._GEMINI_KINDS: curated,
fact-checked content is served as-is (like the topics
library), never upgraded or replaced by an AI guess, and
never collapsed to the not-found line.

`is_meta_shaped(question)` is the wider net used by
fallback.py for ONE purpose: a who/advice-shaped
maths-related question that misses these curated entries
classifies as "guide" (an AI kind) instead of "gibberish",
so in production Gemini/Groq/OpenRouter get their chance at
it before the honest not-found line — the science/non-maths
guards still run before any AI leg, exactly as before.
"""
import re

# ---------------------------------------------------------------------------
# Shape detectors
# ---------------------------------------------------------------------------

# WHO markers: phrases that ask WHO did something. Deliberately
# phrase-shaped, not bare words — bare "kaun" would fire on
# "kaun sa formula" (a which-question, not a who-question).
_WHO_MARKERS = (
    # English: the word "who" itself (word-boundary matched
    # below), plus by-phrases and titles.
    "father of", "mother of", "creator of", "founder of",
    "invented by", "discovered by", "proved by", "given by",
    "by whom",
    # Roman Hinglish: "kisne" alone is unambiguous (it only
    # ever means "who did"); person asks need the full phrase.
    "kisne",
    "kaun tha", "kaun thi", "kaun the", "kaun hai",
    "kaun hote", "kis ke dwara", "kisake dwara",
    # Wave 177: "kise kehte hai" (who is called ...) is a
    # who-shape — it is how students ask title questions
    # ("human computer kise kehte hai").
    "kise kehte", "kise kaha jata",
    # Devanagari: किसने alone is unambiguous; कौन needs its
    # verb phrase (कौन सा is a which-question).
    "किसने", "किसके द्वारा",
    "कौन था", "कौन थी", "कौन थे", "कौन है",
)

_WHO_WORD_EN = re.compile(r"\bwho\b")

# A real computation riding in the text (digit op digit) is a
# problem to solve, never a meta question.
# Wave 146: the operator class also covers the Unicode minus
# signs (U+2212 −, U+2013 –, U+2014 —) that board-paper text
# extraction produces — "x = 100 − 4p" (with U+2212) slipped
# past the veto and a marginal-revenue problem was served
# the Zero history card (CISCE audit idx 190).
_COMPUTATION = re.compile(r"\d\s*[-+*/=×÷−–—]\s*\d")

# Wave 148: a fresh, self-contained problem that is not
# digit-op-digit — a multiplication-table request ("7 ka
# table", "table of 7", "7 ka pahada") or an "X% of Y" /
# "a/b of c" computation — is likewise a problem to solve,
# never a meta question. "mujhe kuch samajh nahi aa raha,
# tum bhi bekaar ho, 7 ka table hi bata do" was served the
# fear-advice card (the "samajh nahi" trigger) while the
# student's actual request — the table — went unanswered;
# the solver had it all along.
_TABLE_REQUEST = re.compile(
    r"\d{1,3}\s+(?:ka|ki)\s+table\b"
    r"|\btable\s+of\s+\d{1,3}\b"
    r"|\bmultiplication\s+table\s+of\s+\d{1,3}\b"
    r"|\d{1,3}\s+(?:ka|ki)\s+pahada\b"
    r"|\d{1,3}\s+का\s+पहाड़ा",
    re.I)
_FRESH_OF = re.compile(
    r"\d+(?:\.\d+)?\s*%\s*of\s*\d+"
    r"|\d+\s*/\s*\d+\s+of\s+\d+",
    re.I)


# Wave 159: the sweep's hijack family — real problems whose
# numbers are separated by prose, not operators, slipped
# past every shape above: a Hindi mean question (data list
# + "माध्य ज्ञात कीजिए") was served the exam-advice card
# because the statement mentions "परीक्षा", and a Hindi SI
# question (9000, 6%, 4 years, "कितना होगा") reached the
# concept layer. The Wave 148 principle, extended to all
# three scripts: >= 2 numeric literals (Devanagari digits
# folded) plus a computation ask or a problem-schema
# keyword is a concrete solvable problem, never a meta
# question. fallback.py's _w159_problem_bearing is the
# mirror used at the chain's other card layers.
_W159_DEV = str.maketrans("०१२३४५६७८९", "0123456789")

_W159_ASK_WORDS = (
    "ज्ञात कीजिए", "ज्ञात करो", "ज्ञात करें", "निकालिए",
    "निकालो", "गणना कीजिए", "गणना करो", "हल कीजिए", "हल करो",
    "बताइए", "क्या होगा", "क्या होगी", "क्या होंगे",
    "क्या है", "क्या हैं", "कितना", "कितने", "कितनी",
    "का मान", "मान ज्ञात",
    "find", "calculate", "compute", "evaluate", "determine",
    "how many", "how much", "what is", "value of",
    "batao", "nikalo", "kitna", "kitne", "kitni", "gyat",
)

_W159_SCHEMA_WORDS = (
    "ब्याज", "interest", "क्षेत्रफल", "area", "परिमाप",
    "परिधि", "perimeter", "circumference", "आयतन", "volume",
    "लघुत्तम", "महत्तम", "lcm", "hcf", "गति", "चाल", "speed",
    "दूरी", "distance", "छूट", "discount", "लाभ", "profit",
    "हानि", "loss", "प्रतिशत", "percent", "अनुपात", "ratio",
    "त्रिज्या", "radius", "व्यास", "diameter", "माध्य",
    "औसत", "mean", "average", "माध्यक", "median", "बहुलक",
    "mode", "प्रायिकता", "probability", "ऊँचाई", "height",
)


def _w159_problem_shapes(q):
    """Wave 159: >= 2 numeric literals plus a computation
    ask or a problem-schema keyword (any script)."""
    t = str(q or "").translate(_W159_DEV)
    if len(re.findall(r"\d+(?:\.\d+)?", t)) < 2:
        return False
    if any(w in t for w in _W159_ASK_WORDS):
        return True
    return any(w in t for w in _W159_SCHEMA_WORDS)


def _has_fresh_problem(q):
    """True when the text carries a real problem to solve
    (the _COMPUTATION veto's shapes plus Wave 148's)."""
    if _COMPUTATION.search(q) or _TABLE_REQUEST.search(q) \
            or _FRESH_OF.search(q) \
            or _w159_problem_shapes(q):
        return True
    # Wave 156: a stated data set — a colon list of >= 5
    # numbers — together with a statistics ask is a
    # problem to solve, not an advice question. "गणित की
    # एक परीक्षा में, 15 विद्यार्थियों द्वारा प्राप्त अंक
    # निम्नलिखित हैं: 19, 25, 23, ..." was served the
    # exam-advice card because the word परीक्षा matched
    # the advice trigger while the data list matched no
    # veto shape (Wave 153 audit book-079).
    if ":" in q and re.search(
            r"माध्यक|बहुलक|माध्य|median|mode|mean|average",
            q):
        _tail = q.split(":", 1)[1]
        if len(re.findall(r"\d+(?:\.\d+)?", _tail)) >= 5:
            return True
    return False


def _trigger_hit(q, t):
    """Wave 146: ADVICE triggers match on WORD BOUNDARIES for
    plain-ASCII triggers. The old bare-substring test let the
    problem-statement verb "prepared" (inside "a mixture is
    prepared by mixing...", "the machine prepares...") fire
    the practice-advice card on real problems (CISCE audit
    idx 9 and 52). A genuine "How to prepare for maths exam?"
    still matches — "prepare" stands alone there. A light
    inflection tolerance (a trailing s/es/d/ed on the last
    word) keeps the curated singular forms matching natural
    text — "silly mistake" must still catch "Silly mistakes
    kaise kam karu?" and "confuse" must catch "confused" —
    with ONE exception: "prepare" itself, whose inflected
    forms are exactly the audited hijack. Non-ASCII
    (Devanagari) triggers keep substring matching, where
    word boundaries do not apply."""
    if t.isascii() and re.fullmatch(r"[a-z ]+", t):
        if re.search(r"\b" + re.escape(t) + r"\b", q):
            return True
        if t == "prepare":
            return False
        return re.search(
            r"\b" + re.escape(t) + r"(?:s|es|d|ed)\b",
            q) is not None
    return t in q


def _has_who_shape(q):
    if _WHO_WORD_EN.search(q):
        return True
    return any(m in q for m in _WHO_MARKERS)


# Wave 183: WHY markers — a question that also asks WHY a
# thing was made/needed ("...aur kyon", "क्यों बनाया था",
# "why was zero invented"). Used twice: the zero entry's
# origin pass below fires on it, and a served entry that
# carries a "why" line adds that line (see _with_why).
_WHY_MARKERS = (
    "why", "kyon", "kyun", "kyu",
    "क्यों", "क्यूँ", "क्यूं",
    "kis liye", "kisliye", "किस लिए",
)


def _has_why_shape(q):
    return any(m in q for m in _WHY_MARKERS)


# Wave 183: CONTRIBUTION markers — "what did X do" shapes.
# Suraj's live test (19 Nov 2026, 13:52 IST): "Aryabhata
# ne kya kiya tha" and "Brahmagupta ne kya kiya tha" both
# collapsed to not-found — the person entries only fired
# on WHO shapes ("kaun tha"), never on the contribution
# shape students naturally use. The Roman kya-kiya family
# deliberately requires the "ne" frame ("X ne kya kiya")
# so a concept ask like "trigonometry me kya kiya jata
# hai" (no "ne", no person) stays with the concept layers.
# Everywhere these markers are used they are DOUBLE-gated
# with a curated person/topic keyword (or a who-context
# word in the wide nets), exactly like the WHO shapes.
_CONTRIBUTION_MARKERS = (
    # Roman Hinglish
    "ne kya kiya", "ne kya diya", "ne kya banaya",
    # Wave 185: the same shapes in voice-typing dress —
    # "aryabhat ne kya kia tha" (kia for kiya) and
    # "Bhaskara ne kya khoja tha" (a discovery ask) both
    # missed every marker here and one of them classified
    # as gibberish in the prediction battery.
    "ne kya kia", "ne kya khoja", "ne kya khoj",
    "ka yogdan", "ka yogdaan", "ki yogdan",
    "yogdan kya", "yogdaan kya",
    "kis liye mashhoor", "kis liye mashoor", "kis liye mashhur",
    "mashhoor hai", "mashoor hai", "mashhoor the", "mashhoor thi",
    "ke baare me batao", "ke bare me batao",
    "ke baare me bata", "ke bare me bata",
    # Wave 185: "about X" asks in their other natural
    # orders — "Euclid ke baare me kuch batao" (kuch
    # between) and "aur detail me batao zero ke baare me"
    # (batao first, topic last; that one was deep-solved
    # into a bare "0 = 0"). The pass stays double-gated
    # with a curated HISTORY keyword, so only maths
    # topics/people can fire it.
    "ke baare me kuch batao", "ke bare me kuch batao",
    "ke baare me", "ke bare me",
    # English
    "what did", "contribution", "contributions",
    "contribute", "contributed",
    "famous for", "known for", "tell me about",
    # Devanagari
    "ने क्या किया", "ने क्या दिया", "ने क्या बनाया",
    "ने क्या खोजा",
    "योगदान", "किस लिए प्रसिद्ध", "किस लिए मशहूर",
    "प्रसिद्ध है", "मशहूर है",
    "के बारे में बताओ", "के बारे में बता",
    "के बारे में",
)


def _has_contribution_shape(q):
    return any(m in q for m in _CONTRIBUTION_MARKERS)


# Wave 183: ORIGIN-creation markers for the zero entry —
# a zero question whose core asks who made zero OR why
# it was made ("zero kyon banaya gaya tha", "जीरो क्यों
# बनाया था") carries no WHO marker, so the who-gated
# HISTORY pass missed it. These markers are only ever
# consulted together with the zero entry's own keyword
# hit (the standalone digit / zero word), which is what
# keeps every real 0-computation out.
_ORIGIN_CREATION_MARKERS = (
    "banaya", "banaye", "बनाया", "बनाये", "बना",
    "khoj", "खोज", "invent", "discover",
    "avishkar", "आविष्कार", "ijad", "ईजाद",
)


def _has_origin_shape(q):
    return _has_who_shape(q) or _has_why_shape(q) \
        or any(m in q for m in _ORIGIN_CREATION_MARKERS)


# Maths signal for the advice gate and the wide shape net:
# broad maths vocabulary in all three scripts.
_MATHS_SIGNALS = (
    "maths", "math", "ganit", "गणित", "formula", "sutra",
    "सूत्र", "theorem", "प्रमेय", "algebra", "geometry",
    "trigonometry", "calculus", "arithmetic", "अंकगणित",
    "calculation", "गणना", "percent", "प्रतिशत", "triangle",
    "त्रिभुज", "circle", "वृत्त", "equation", "समीकरण",
    "संख्या", "number", "table", "pahade", "पहाड़े",
)

# Another subject named in the question blocks the generic
# advice triggers when no maths signal is present.
_OTHER_SUBJECTS = (
    "history", "itihas", "इतिहास", "physics", "chemistry",
    "biology", "science", "vigyan", "विज्ञान", "geography",
    "bhugol", "भूगोल", "social science", "civics", "economics",
    "arthshastra", "grammar", "vyakaran", "व्याकरण",
    "sanskrit", "संस्कृत", "computer", "कंप्यूटर",
    "english", "angrezi",
)


def _has_maths_signal(q):
    return any(s in q for s in _MATHS_SIGNALS)


def _names_other_subject(q):
    return any(s in q for s in _OTHER_SUBJECTS)


def _keyword_hit(q, keyword):
    """Substring match, with a word boundary for short Latin
    keywords so "pi" does not fire inside "pick"/"capital"
    and "log" not inside "logic"."""
    if keyword.isascii() and len(keyword) <= 3 \
            and keyword.isalpha():
        return re.search(r"\b" + re.escape(keyword) + r"\b",
                         q) is not None
    # Wave 177: an all-digit keyword (the zero entry's "0" /
    # "०") matches only as a STANDALONE number — not inside
    # "10", "100", "2024" or a decimal like "0.5". Students
    # ask "0 ki khoj kisne ki hai" with the digit, never the
    # word, and the entry used to miss every such ask.
    if keyword.isdigit():
        return re.search(
            r"(?<![0-9०-९])" + re.escape(keyword) +
            r"(?![0-9०-९])(?!\.[0-9])", q) is not None
    return keyword in q


def _entry_hit(q, entry):
    return any(_keyword_hit(q, kw) for kw in entry["keywords"])


# ---------------------------------------------------------------------------
# Layer 1: HISTORY / CREATOR facts
# Each entry: keywords (topic/person names, any script),
# and per-flavour (en / roman / dev) answer gist + plain
# steps whose LAST line is the one-line gist.
# ---------------------------------------------------------------------------

HISTORY = [
    {
        "id": "zero",
        "keywords": ("zero", "shunya", "शून्य", "sifar", "सिफ़र",
                     # Wave 177: the digit itself — students
                     # type "0 ki khoj kisne ki hai", and the
                     # digit-boundary match in _keyword_hit
                     # keeps it out of "10"/"0.5".
                     "0", "०",
                     # Wave 183: the SPOKEN forms — a voice-
                     # typed question says "जीरो" (or Roman
                     # "jeero"), never "शून्य"/"zero". Suraj's
                     # live test: "जीरो की खोज किसने की थी और
                     # क्यों की थी क्यों बनाया था" missed every
                     # keyword above and collapsed.
                     "जीरो", "ज़ीरो", "jeero",
                     # Wave 185: more voice-typing spellings
                     # of the same spoken forms — "jero
                     # kisne banaya" and "sifr kisne banaya"
                     # (sifr for sifar) both missed every
                     # keyword above and classified as
                     # gibberish in the prediction battery.
                     "jero", "sifr"),
        # Wave 183: when the ask also carries a WHY ("aur
        # kyon", "क्यों बनाया था"), meta_result inserts
        # this one line before the closing gist (see
        # _with_why). The need came first; the rules came
        # from Brahmagupta.
        "why": {
            "en": "Why was it made? Big calculations and "
                  "the rules of maths needed a number for "
                  "'nothing' — that need created zero, and "
                  "Brahmagupta gave its addition-subtraction "
                  "rules.",
            "roman": "Kyon banaya gaya? Bade hisaab-kitab "
                     "aur ganit ke niyam pure karne ke liye "
                     "zero ki zaroorat padi — Brahmagupta ne "
                     "iske jod-ghataav ke niyam diye.",
            "dev": "क्यों बनाया गया? बड़े हिसाब-किताब और "
                   "गणित के नियम पूरे करने के लिए शून्य की "
                   "ज़रूरत पड़ी — ब्रह्मगुप्त ने इसके "
                   "जोड़-घटाव के नियम दिए।",
        },
        # Wave 198 (Suraj, 20 Nov 2026): the answer line
        # credits ARYABHATA with the khoj of zero — the
        # standard school answer, corrected on his live
        # phone test (the old answer led with Brahmagupta).
        # Brahmagupta stays in the steps below: he is the
        # one who first wrote zero's arithmetic rules
        # (628 CE).
        "en": {
            "answer": "Zero — invented by Aryabhata "
                      "(India, 5th century CE)",
            "steps": [
                "Zero was invented by Aryabhata (5th century "
                "CE) — he gave zero its place in the "
                "place-value system and used it as a real "
                "number, not just an empty space in a number.",
                "Brahmagupta, in his book Brahmasphutasiddhanta "
                "(628 CE), first gave clear rules for adding, "
                "subtracting and multiplying with zero.",
                "From India, zero travelled to the Arab world "
                "and then to Europe, and became the base of "
                "all modern maths.",
                "Short me: zero is India's gift to maths.",
            ],
        },
        "roman": {
            "answer": "Zero ki khoj Aryabhata ne ki thi "
                      "(India, 5th century)",
            "steps": [
                "Zero ki khoj Aryabhata ne ki thi (5th "
                "century) — unhone zero ko place-value "
                "system me jagah di aur use ek asal number "
                "ki tarah istemal kiya, sirf khaali jagah "
                "ke roop me nahi.",
                "Brahmagupta ne apni kitab Brahmasphutasiddhanta "
                "(628 CE) me zero ke jod-ghata-guna ke saaf "
                "niyam sabse pehle diye.",
                "India se zero Arab duniya aur phir Europe "
                "pahuncha, aur aaj ke pure maths ki neev "
                "ban gaya.",
                "Short me: zero India ki den hai.",
            ],
        },
        "dev": {
            "answer": "शून्य की खोज आर्यभट ने की थी "
                      "(भारत, 5वीं शताब्दी)",
            "steps": [
                "शून्य की खोज आर्यभट ने की थी (5वीं शताब्दी) "
                "— उन्होंने शून्य को स्थानीय-मान प्रणाली में "
                "स्थान दिया और उसे एक असली संख्या के रूप में "
                "उपयोग किया, सिर्फ़ खाली स्थान के रूप में नहीं।",
                "ब्रह्मगुप्त ने अपनी पुस्तक ब्राह्मस्फुटसिद्धांत "
                "(628 ई.) में शून्य के जोड़, घटाव और गुणा के "
                "स्पष्ट नियम सबसे पहले दिए।",
                "भारत से शून्य अरब दुनिया और फिर यूरोप पहुँचा, "
                "और आज के पूरे गणित की नींव बन गया।",
                "संक्षेप में: शून्य भारत की देन है।",
            ],
        },
    },
    {
        "id": "pythagoras",
        "keywords": ("pythagoras", "paithagoras", "पाइथागोरस",
                     "पैथागोरस", "पाइथागोरस"),
        "en": {
            "answer": "Pythagoras Theorem — credited to "
                      "Pythagoras (Greek, ~570–495 BCE)",
            "steps": [
                "The theorem is named after the Greek "
                "mathematician Pythagoras and his school, who "
                "are credited with its first general proof.",
                "The relation itself was known even earlier: "
                "Babylonian clay tablets (~1800 BCE) use it, "
                "and in India the Baudhayana Sulba Sutra "
                "(~800 BCE) states it for building altars.",
                "Short me: the name is Pythagoras's, the "
                "knowledge is much older.",
            ],
        },
        "roman": {
            "answer": "Pythagoras Theorem — iska shrey "
                      "Pythagoras ko jata hai (Greek, ~570–495 BCE)",
            "steps": [
                "Ye theorem Greek ganitagya Pythagoras aur unke "
                "school ke naam par hai — iska pehla aam proof "
                "unhi ko mana jata hai.",
                "Lekin ye sambandh isse bhi pehle se jana jata "
                "tha: Babylon ki mitti ki takhtiyon (~1800 BCE) "
                "me iska upyog hai, aur India me Baudhayana "
                "Sulba Sutra (~800 BCE) me ye vedi banane ke "
                "liye diya gaya hai.",
                "Short me: naam Pythagoras ka hai, gyaan usse "
                "bahut purana hai.",
            ],
        },
        "dev": {
            "answer": "पाइथागोरस प्रमेय — इसका श्रेय पाइथागोरस "
                      "को जाता है (यूनानी, ~570–495 ई.पू.)",
            "steps": [
                "यह प्रमेय यूनानी गणितज्ञ पाइथागोरस और उनके "
                "विद्यालय के नाम पर है — इसका पहला सामान्य "
                "प्रमाण उन्हीं को माना जाता है।",
                "लेकिन यह संबंध इससे भी पहले से ज्ञात था: "
                "बेबीलोन की मिट्टी की पट्टियों (~1800 ई.पू.) "
                "में इसका उपयोग है, और भारत में बौधायन शुल्ब "
                "सूत्र (~800 ई.पू.) में यह वेदी बनाने के लिए "
                "दिया गया है।",
                "संक्षेप में: नाम पाइथागोरस का है, ज्ञान उससे "
                "बहुत पुराना है।",
            ],
        },
    },
    {
        "id": "algebra",
        "keywords": ("algebra", "बीजगणित", "beejganit",
                     "bijganit", "al-jabr", "khwarizmi",
                     "ख्वारिज़्मी",
                     # Wave 185: the voice spelling
                     # "aljebra kahan se aaya" missed.
                     "aljebra"),
        "en": {
            "answer": "Algebra — Al-Khwarizmi (Baghdad, ~820 CE); "
                      "the word comes from his book's 'al-jabr'",
            "steps": [
                "Muhammad ibn Musa al-Khwarizmi wrote 'Al-Kitab "
                "al-mukhtasar fi hisab al-jabr' — the word "
                "'algebra' comes from 'al-jabr' in that title.",
                "His book taught equation-solving step by step; "
                "the word 'algorithm' also comes from his name.",
                "India's Brahmagupta and Bhaskara had solved "
                "many equation types even earlier — algebra "
                "grew from the work of many lands.",
                "Short me: algebra ko kitab ki shakal "
                "Al-Khwarizmi ne di.",
            ],
        },
        "roman": {
            "answer": "Algebra — Al-Khwarizmi (Baghdad, ~820 CE); "
                      "shabd unki kitab ke 'al-jabr' se aaya",
            "steps": [
                "Muhammad ibn Musa al-Khwarizmi ne 'Al-Kitab "
                "al-mukhtasar fi hisab al-jabr' kitab likhi — "
                "'algebra' shabd usi ke 'al-jabr' se bana hai.",
                "Unki kitab ne samikaran hal karne ka tareeka "
                "step-by-step sikhaya; 'algorithm' shabd bhi "
                "unke naam se aaya hai.",
                "India ke Brahmagupta aur Bhaskara ne kai "
                "samikaran isse pehle bhi hal kiye the — "
                "algebra kai deshon ke kaam se bana hai.",
                "Short me: algebra ko kitab ki shakal "
                "Al-Khwarizmi ne di.",
            ],
        },
        "dev": {
            "answer": "बीजगणित (Algebra) — अल-ख्वारिज़्मी "
                      "(बग़दाद, ~820 ई.); शब्द उनकी पुस्तक के "
                      "'अल-जब्र' से आया",
            "steps": [
                "मुहम्मद इब्न मूसा अल-ख्वारिज़्मी ने 'अल-किताब "
                "अल-मुख्तसर फ़ी हिसाब अल-जब्र' पुस्तक लिखी — "
                "'algebra' शब्द उसी के 'अल-जब्र' से बना है।",
                "उनकी पुस्तक ने समीकरण हल करने की विधि चरण-दर-"
                "चरण सिखाई; 'algorithm' शब्द भी उनके नाम से "
                "आया है।",
                "भारत के ब्रह्मगुप्त और भास्कर ने कई समीकरण "
                "इससे पहले भी हल किए थे — बीजगणित कई देशों के "
                "कार्य से बना है।",
                "संक्षेप में: बीजगणित को पुस्तक का रूप "
                "अल-ख्वारिज़्मी ने दिया।",
            ],
        },
    },
    {
        "id": "euclid",
        "keywords": ("euclid", "यूक्लिड", "father of geometry",
                     "geometry ke father", "geometry ke pita",
                     "geometry ka janak", "ज्यामिति के जनक",
                     "ज्यामिति के पिता",
                     # Wave 185: the Roman "ka" forms of the
                     # same titles ("geometry ka pita kaun
                     # hai") — the archimedes entry below
                     # carries the maths-wide pair.
                     "geometry ka pita"),
        "en": {
            "answer": "Geometry — Euclid is called the Father "
                      "of Geometry",
            "steps": [
                "Euclid (Alexandria, ~300 BCE) wrote 'Elements' "
                "— 13 books that organised geometry into "
                "definitions, postulates and proved theorems.",
                "For about 2,000 years, 'Elements' remained "
                "the world's main geometry textbook.",
                "Short me: geometry ko ek vyavasthit vigyaan "
                "Euclid ne banaya.",
            ],
        },
        "roman": {
            "answer": "Geometry — Euclid ko Geometry ka Pita "
                      "(Father of Geometry) kaha jata hai",
            "steps": [
                "Euclid (Alexandria, ~300 BCE) ne 'Elements' "
                "kitab likhi — 13 bhaagon me geometry ko "
                "paribhasha, siddhanton aur saabit theorems me "
                "sajaya gaya.",
                "Lagbhag 2,000 saal tak 'Elements' duniya ki "
                "sabse badi geometry ki kitab rahi.",
                "Short me: geometry ko ek vyavasthit vigyaan "
                "Euclid ne banaya.",
            ],
        },
        "dev": {
            "answer": "ज्यामिति — यूक्लिड को ज्यामिति का जनक "
                      "(Father of Geometry) कहा जाता है",
            "steps": [
                "यूक्लिड (अलेक्ज़ेंड्रिया, ~300 ई.पू.) ने "
                "'Elements' पुस्तक लिखी — 13 भागों में "
                "ज्यामिति को परिभाषाओं, अभिगृहीतों और सिद्ध "
                "प्रमेयों में व्यवस्थित किया।",
                "लगभग 2,000 वर्षों तक 'Elements' दुनिया की "
                "प्रमुख ज्यामिति पुस्तक रही।",
                "संक्षेप में: ज्यामिति को एक व्यवस्थित विज्ञान "
                "यूक्लिड ने बनाया।",
            ],
        },
    },
    {
        "id": "calculus",
        "keywords": ("calculus", "कैलकुलस", "कलन"),
        "en": {
            "answer": "Calculus — Isaac Newton and Gottfried "
                      "Wilhelm Leibniz, independently",
            "steps": [
                "In the late 1600s, Newton (England) and "
                "Leibniz (Germany) developed calculus "
                "separately — Newton called his version "
                "'fluxions'.",
                "The notation we still use — dy/dx and the ∫ "
                "sign — is Leibniz's.",
                "Both built on earlier work, including ideas "
                "from the Kerala school in India and from "
                "European mathematicians.",
                "Short me: calculus ek ka nahi, do mahaan "
                "dimaagon ka kaam hai.",
            ],
        },
        "roman": {
            "answer": "Calculus — Isaac Newton aur Gottfried "
                      "Wilhelm Leibniz, dono ne alag-alag",
            "steps": [
                "1600s ke aakhir me Newton (England) aur "
                "Leibniz (Germany) ne calculus ko alag-alag "
                "banaya — Newton ne apne version ko 'fluxions' "
                "kaha tha.",
                "Aaj jo sanket hum use karte hain — dy/dx aur "
                "∫ — ye Leibniz ke diye hue hain.",
                "Dono ne purane kaam par aage badhaya, jisme "
                "India ke Kerala school aur Europe ke "
                "ganitagyaon ke vichaar bhi the.",
                "Short me: calculus ek ka nahi, do mahaan "
                "dimaagon ka kaam hai.",
            ],
        },
        "dev": {
            "answer": "कलन (Calculus) — आइज़क न्यूटन और गॉटफ़्रीड "
                      "विल्हेम लाइबनिज़, दोनों ने स्वतंत्र रूप से",
            "steps": [
                "1600 के दशक के अंत में न्यूटन (इंग्लैंड) और "
                "लाइबनिज़ (जर्मनी) ने कलन को अलग-अलग विकसित "
                "किया — न्यूटन ने अपने रूप को 'fluxions' कहा "
                "था।",
                "आज जो संकेत हम उपयोग करते हैं — dy/dx और ∫ — "
                "ये लाइबनिज़ के दिए हुए हैं।",
                "दोनों ने पुराने कार्य को आगे बढ़ाया, जिसमें "
                "भारत के केरल विद्यालय और यूरोपीय गणितज्ञों के "
                "विचार भी थे।",
                "संक्षेप में: कलन एक का नहीं, दो महान मस्तिष्कों "
                "का कार्य है।",
            ],
        },
    },
    {
        "id": "fermat",
        "keywords": ("fermat", "फ़र्मा", "फर्मा"),
        "en": {
            "answer": "Fermat's Last Theorem — proved by "
                      "Andrew Wiles (1994)",
            "steps": [
                "Pierre de Fermat wrote the claim in 1637 in "
                "a book's margin, but never published a proof.",
                "For 358 years, the world's best mathematicians "
                "tried and failed to prove it.",
                "British mathematician Andrew Wiles proved it "
                "in 1994 (published 1995) after about 7 years "
                "of secret work; one small gap was fixed with "
                "Richard Taylor's help.",
                "Short me: 358 saal purane sawal ko Wiles ne "
                "hal kiya.",
            ],
        },
        "roman": {
            "answer": "Fermat's Last Theorem — Andrew Wiles ne "
                      "prove kiya (1994)",
            "steps": [
                "Pierre de Fermat ne 1637 me ye daava ek kitab "
                "ke kinare likha tha, lekin proof kabhi nahi "
                "diya.",
                "358 saal tak duniya ke bade-bade ganitagya "
                "koshish karke haar gaye.",
                "British ganitagya Andrew Wiles ne 1994 me "
                "ise prove kiya (1995 me publish hua) — "
                "lagbhag 7 saal ki chhupi mehnat ke baad; ek "
                "chhoti kami Richard Taylor ki madad se "
                "theek hui.",
                "Short me: 358 saal purane sawal ko Wiles ne "
                "hal kiya.",
            ],
        },
        "dev": {
            "answer": "फ़र्मा का अंतिम प्रमेय — एंड्रयू वाइल्स "
                      "ने सिद्ध किया (1994)",
            "steps": [
                "पियरे डे फ़र्मा ने 1637 में यह दावा एक पुस्तक "
                "के हाशिये पर लिखा था, लेकिन प्रमाण कभी नहीं "
                "दिया।",
                "358 वर्षों तक दुनिया के बड़े-बड़े गणितज्ञ "
                "प्रयास करके असफल रहे।",
                "ब्रिटिश गणितज्ञ एंड्रयू वाइल्स ने 1994 में "
                "इसे सिद्ध किया (1995 में प्रकाशित) — लगभग 7 "
                "वर्षों के गुप्त परिश्रम के बाद; एक छोटी कमी "
                "रिचर्ड टेलर की सहायता से ठीक हुई।",
                "संक्षेप में: 358 साल पुराने प्रश्न को वाइल्स "
                "ने हल किया।",
            ],
        },
    },
    {
        "id": "coordinate_geometry",
        "keywords": ("coordinate geometry", "cartesian",
                     "descartes", "देकार्त", "निर्देशांक ज्यामिति",
                     "nirdeshank jyamiti"),
        "en": {
            "answer": "Coordinate Geometry — René Descartes "
                      "(France, 1637)",
            "steps": [
                "Descartes' book 'La Géométrie' (1637) joined "
                "algebra and geometry: every point became a "
                "pair of numbers (x, y).",
                "That is why the axes are called Cartesian "
                "coordinates, after his name.",
                "Pierre de Fermat had similar ideas at almost "
                "the same time — the credit is mostly "
                "Descartes' because he published first.",
                "Short me: bindu ko sankhya banane ka vichaar "
                "Descartes ka hai.",
            ],
        },
        "roman": {
            "answer": "Coordinate Geometry — René Descartes "
                      "(France, 1637)",
            "steps": [
                "Descartes ki kitab 'La Géométrie' (1637) ne "
                "algebra aur geometry ko joda: har bindu ek "
                "sankhya-jodi (x, y) ban gaya.",
                "Isi liye akshon (axes) ko unke naam par "
                "Cartesian coordinates kaha jata hai.",
                "Pierre de Fermat ke paas bhi lagbhag usi samay "
                "aise hi vichaar the — shrey zyada Descartes "
                "ko mila kyunki unhone pehle publish kiya.",
                "Short me: bindu ko sankhya banane ka vichaar "
                "Descartes ka hai.",
            ],
        },
        "dev": {
            "answer": "निर्देशांक ज्यामिति — रेने देकार्त "
                      "(फ़्रांस, 1637)",
            "steps": [
                "देकार्त की पुस्तक 'La Géométrie' (1637) ने "
                "बीजगणित और ज्यामिति को जोड़ा: हर बिंदु एक "
                "संख्या-युग्म (x, y) बन गया।",
                "इसीलिए अक्षों को उनके नाम पर Cartesian "
                "निर्देशांक कहा जाता है।",
                "पियरे डे फ़र्मा के पास भी लगभग उसी समय ऐसे "
                "ही विचार थे — श्रेय अधिक देकार्त को मिला "
                "क्योंकि उन्होंने पहले प्रकाशित किया।",
                "संक्षेप में: बिंदु को संख्या बनाने का विचार "
                "देकार्त का है।",
            ],
        },
    },
    {
        "id": "pi",
        "keywords": ("pi", "π", "पाई"),
        # Wave 198 (audit 20 Nov): the answer line leads
        # with ARYABHATA — the school-taught fact ("pi ka
        # maan kisne diya?" -> Aryabhata, 3.1416).
        # Archimedes stays credited second, exactly like
        # Brahmagupta in the fixed zero card. Steps keep
        # their chronological order, unchanged.
        "en": {
            "answer": "π (pi) — Aryabhata gave 3.1416 "
                      "(499 CE); Archimedes had made the "
                      "first accurate calculation long "
                      "before (~250 BCE)",
            "steps": [
                "Archimedes (Greece) trapped π between two "
                "polygons and showed 3.1408 < π < 3.1429.",
                "Aryabhata (499 CE) gave π ≈ 3.1416 — correct "
                "to 4 decimal places — in the Aryabhatiya.",
                "Later, Madhava of Kerala (~1400s) found an "
                "infinite series for π, centuries before "
                "Europe.",
                "Short me: π kisi ek ki khoj nahi — kai "
                "sabhyataon ki mehnat hai.",
            ],
        },
        "roman": {
            "answer": "π (pi) — Aryabhata ne 3.1416 diya "
                      "(499 CE); sabse pehli sahi ganana "
                      "Archimedes ne bahut pehle ki thi "
                      "(~250 BCE)",
            "steps": [
                "Archimedes (Greece) ne π ko do bahubhujon ke "
                "beech phansa kar dikhaya: 3.1408 < π < 3.1429.",
                "Aryabhata (499 CE) ne Aryabhatiya me π ≈ "
                "3.1416 diya — 4 decimal sthanon tak sahi.",
                "Baad me Kerala ke Madhava (~1400s) ne π ke "
                "liye anant shreni (infinite series) khoji, "
                "Europe se kai shatabdi pehle.",
                "Short me: π kisi ek ki khoj nahi — kai "
                "sabhyataon ki mehnat hai.",
            ],
        },
        "dev": {
            "answer": "π (पाई) — आर्यभट ने 3.1416 दिया "
                      "(499 ई.); सबसे पहली सही गणना "
                      "आर्किमिडीज़ ने बहुत पहले की थी "
                      "(~250 ई.पू.)",
            "steps": [
                "आर्किमिडीज़ (यूनान) ने π को दो बहुभुजों के बीच "
                "रखकर दिखाया: 3.1408 < π < 3.1429।",
                "आर्यभट (499 ई.) ने आर्यभटीय में π ≈ 3.1416 "
                "दिया — 4 दशमलव स्थानों तक सही।",
                "बाद में केरल के माधव (~1400s) ने π के लिए "
                "अनंत श्रेणी खोजी, यूरोप से कई शताब्दी पहले।",
                "संक्षेप में: π किसी एक की खोज नहीं — कई "
                "सभ्यताओं की मेहनत है।",
            ],
        },
    },
    {
        "id": "venn",
        "keywords": ("venn", "वेन"),
        "en": {
            "answer": "Venn Diagram — John Venn (England, 1880)",
            "steps": [
                "John Venn introduced these overlapping-circle "
                "diagrams in 1880 to show sets and their "
                "relations clearly.",
                "Euler had used similar circles earlier, so "
                "some books call them Euler–Venn diagrams.",
                "Short me: sets ko aakriti me dikhane ka "
                "tareeka Venn ne lokpriya kiya.",
            ],
        },
        "roman": {
            "answer": "Venn Diagram — John Venn (England, 1880)",
            "steps": [
                "John Venn ne 1880 me ye overlap karte golon "
                "wale diagram diye, taaki sets aur unke sambandh "
                "saaf dikhayi dein.",
                "Euler ne aise gole pehle bhi use kiye the, "
                "isiliye kuch kitabon me inhe Euler–Venn "
                "diagram bhi kaha jata hai.",
                "Short me: sets ko aakriti me dikhane ka "
                "tareeka Venn ne lokpriya kiya.",
            ],
        },
        "dev": {
            "answer": "वेन आरेख — जॉन वेन (इंग्लैंड, 1880)",
            "steps": [
                "जॉन वेन ने 1880 में ये अतिव्यापी वृत्तों वाले "
                "आरेख दिए, ताकि समुच्चय और उनके संबंध स्पष्ट "
                "दिखें।",
                "ऑयलर ने ऐसे वृत्त पहले भी उपयोग किए थे, "
                "इसलिए कुछ पुस्तकों में इन्हें ऑयलर–वेन आरेख "
                "भी कहा जाता है।",
                "संक्षेप में: समुच्चयों को आकृति में दिखाने "
                "का तरीका वेन ने लोकप्रिय किया।",
            ],
        },
    },
    {
        "id": "pascal_triangle",
        "keywords": ("pascal", "पास्कल"),
        "en": {
            "answer": "Pascal's Triangle — popularised by "
                      "Blaise Pascal (1654); known in India "
                      "long before as Meru-prastara",
            "steps": [
                "Pascal wrote the famous treatise on this "
                "triangle of numbers in 1654, so it carries "
                "his name.",
                "But it was known much earlier: in India as "
                "Meru-prastara (described by Halayudha, ~10th "
                "century, from Pingala's work) and in China "
                "as Yang Hui's triangle.",
                "Short me: naam Pascal ka, itihaas bahut "
                "purana hai.",
            ],
        },
        "roman": {
            "answer": "Pascal's Triangle — Blaise Pascal ne "
                      "lokpriya kiya (1654); India me ye bahut "
                      "pehle se Meru-prastara ke naam se jana "
                      "jata tha",
            "steps": [
                "Pascal ne 1654 me is sankhya-trikon par "
                "prasiddh granth likha, isiliye ye unke naam "
                "se jana jata hai.",
                "Lekin ye bahut pehle se jana jata tha: India "
                "me Meru-prastara ke naam se (Halayudha, ~10th "
                "century, Pingala ke kaam se) aur China me "
                "Yang Hui ke trikon ke naam se.",
                "Short me: naam Pascal ka, itihaas bahut "
                "purana hai.",
            ],
        },
        "dev": {
            "answer": "पास्कल का त्रिभुज — ब्लेज़ पास्कल ने "
                      "लोकप्रिय किया (1654); भारत में यह बहुत "
                      "पहले से मेरु-प्रस्तार के नाम से ज्ञात था",
            "steps": [
                "पास्कल ने 1654 में इस संख्या-त्रिभुज पर "
                "प्रसिद्ध ग्रंथ लिखा, इसलिए यह उनके नाम से "
                "जाना जाता है।",
                "लेकिन यह बहुत पहले से ज्ञात था: भारत में "
                "मेरु-प्रस्तार के नाम से (हलायुध, ~10वीं "
                "शताब्दी, पिंगल के कार्य से) और चीन में यांग "
                "हुई के त्रिभुज के नाम से।",
                "संक्षेप में: नाम पास्कल का, इतिहास बहुत "
                "पुराना है।",
            ],
        },
    },
    {
        "id": "trigonometry",
        "keywords": ("trigonometry", "त्रिकोणमिति", "trikonmiti",
                     "hipparchus", "हिप्पार्कस"),
        "en": {
            "answer": "Trigonometry — Hipparchus is called its "
                      "father (~150 BCE)",
            "steps": [
                "Hipparchus (Greek astronomer) made the first "
                "table of chords — the true beginning of "
                "trigonometry.",
                "Indian mathematicians (Aryabhata and others) "
                "later created the sine (jya) we use today, "
                "which reached Europe through Arabic books.",
                "Short me: shuruaat Hipparchus se, aaj ka "
                "roop India ki den ke saath bana.",
            ],
        },
        "roman": {
            "answer": "Trigonometry — Hipparchus ko iska pita "
                      "kaha jata hai (~150 BCE)",
            "steps": [
                "Hipparchus (Greek khagolshastri) ne jeevaon "
                "(chords) ki pehli table banayi — yahi "
                "trigonometry ki asal shuruaat thi.",
                "Baad me Bharatiya ganitagyaon (Aryabhata "
                "aadi) ne aaj wala sine (jya) banaya, jo Arabi "
                "kitabon ke dwara Europe pahuncha.",
                "Short me: shuruaat Hipparchus se, aaj ka "
                "roop India ki den ke saath bana.",
            ],
        },
        "dev": {
            "answer": "त्रिकोणमिति — हिप्पार्कस को इसका जनक "
                      "कहा जाता है (~150 ई.पू.)",
            "steps": [
                "हिप्पार्कस (यूनानी खगोलशास्त्री) ने जीवाओं "
                "(chords) की पहली सारणी बनाई — यही त्रिकोणमिति "
                "की असली शुरुआत थी।",
                "बाद में भारतीय गणितज्ञों (आर्यभट आदि) ने आज "
                "वाला sine (ज्या) बनाया, जो अरबी पुस्तकों के "
                "द्वारा यूरोप पहुँचा।",
                "संक्षेप में: शुरुआत हिप्पार्कस से, आज का रूप "
                "भारत की देन के साथ बना।",
            ],
        },
    },
    {
        "id": "logarithm",
        "keywords": ("logarithm", "लघुगणक", "napier", "नेपियर",
                     "log table"),
        "en": {
            "answer": "Logarithms — John Napier (Scotland, 1614)",
            "steps": [
                "Napier published logarithms in 1614 to turn "
                "slow, hard multiplication into quick addition.",
                "Henry Briggs then built the base-10 (common) "
                "log tables that students used for centuries.",
                "Short me: badi guna ko aasan banane ke liye "
                "Napier ne log banaya.",
            ],
        },
        "roman": {
            "answer": "Logarithms — John Napier (Scotland, 1614)",
            "steps": [
                "Napier ne 1614 me logarithms diye, taaki lambi "
                "aur kathin guna (multiplication) aasan jod me "
                "badal jaye.",
                "Phir Henry Briggs ne base-10 (common) log ki "
                "tables banayi, jo shatabdiyon tak chhatra use "
                "karte rahe.",
                "Short me: badi guna ko aasan banane ke liye "
                "Napier ne log banaya.",
            ],
        },
        "dev": {
            "answer": "लघुगणक (Logarithms) — जॉन नेपियर "
                      "(स्कॉटलैंड, 1614)",
            "steps": [
                "नेपियर ने 1614 में लघुगणक दिए, ताकि लंबा और "
                "कठिन गुणा आसान जोड़ में बदल जाए।",
                "फिर हेनरी ब्रिग्स ने आधार-10 (common) log की "
                "सारणियाँ बनाईं, जो शताब्दियों तक छात्र उपयोग "
                "करते रहे।",
                "संक्षेप में: बड़े गुणा को आसान बनाने के लिए "
                "नेपियर ने log बनाया।",
            ],
        },
    },
    {
        "id": "binary",
        "keywords": ("binary", "बाइनरी", "द्विआधारी"),
        "en": {
            "answer": "Binary Numbers — Leibniz published the "
                      "modern system (1703); Pingala described "
                      "a binary-like system in India long before",
            "steps": [
                "Gottfried Wilhelm Leibniz published the "
                "modern binary system (only 0 and 1) in 1703 "
                "— the system every computer uses today.",
                "Long before, Pingala (~3rd–2nd century BCE) "
                "described a binary-like counting system in "
                "his Chhandahshastra, a work on Sanskrit "
                "poetry metres.",
                "Short me: aaj ka binary Leibniz ka, iska "
                "purana roop Pingala ka.",
            ],
        },
        "roman": {
            "answer": "Binary Numbers — aaj ki binary pranali "
                      "Leibniz ne di (1703); India me Pingala "
                      "ne is jaisi pranali bahut pehle di thi",
            "steps": [
                "Gottfried Wilhelm Leibniz ne 1703 me aadhunik "
                "binary pranali (sirf 0 aur 1) publish ki — "
                "yahi pranali aaj har computer use karta hai.",
                "Bahut pehle, Pingala (~3rd–2nd century BCE) "
                "ne apne Chhandahshastra (Sanskrit kavita ke "
                "chhandon par granth) me binary jaisi ginati "
                "pranali ka varnan kiya tha.",
                "Short me: aaj ka binary Leibniz ka, iska "
                "purana roop Pingala ka.",
            ],
        },
        "dev": {
            "answer": "द्विआधारी (Binary) संख्याएँ — आज की binary "
                      "प्रणाली लाइबनिज़ ने दी (1703); भारत में "
                      "पिंगल ने इस जैसी प्रणाली बहुत पहले दी थी",
            "steps": [
                "गॉटफ़्रीड विल्हेम लाइबनिज़ ने 1703 में आधुनिक "
                "binary प्रणाली (सिर्फ़ 0 और 1) प्रकाशित की — "
                "यही प्रणाली आज हर कंप्यूटर उपयोग करता है।",
                "बहुत पहले, पिंगल (~तीसरी–दूसरी शताब्दी ई.पू.) "
                "ने अपने छंदःशास्त्र (संस्कृत कविता के छंदों "
                "पर ग्रंथ) में binary जैसी गिनती प्रणाली का "
                "वर्णन किया था।",
                "संक्षेप में: आज का binary लाइबनिज़ का, इसका "
                "पुराना रूप पिंगल का।",
            ],
        },
    },
    {
        "id": "shakuntala_devi",
        "keywords": ("shakuntala", "शकुंतला", "शकुन्तला",
                     # Wave 177: the title IS the question in
                     # school GK ("human computer kise kehte
                     # hai").
                     "human computer", "human calculator",
                     "manav computer", "मानव कंप्यूटर"),
        "en": {
            "answer": "Shakuntala Devi (1929–2013) — the "
                      "'Human Computer' of India",
            "steps": [
                "An Indian mental-calculation genius from "
                "Bengaluru: in 1980 she multiplied two "
                "13-digit numbers in just 28 seconds — a "
                "Guinness world record.",
                "She wrote popular maths books like 'Puzzles "
                "to Puzzle You' and showed the world that fast "
                "calculation is a trainable skill, not magic.",
                "Short me: dimag ki tez ganana ka sabse bada "
                "naam — Shakuntala Devi.",
            ],
        },
        "roman": {
            "answer": "Shakuntala Devi (1929–2013) — India ki "
                      "'Human Computer'",
            "steps": [
                "Bengaluru ki is Bharatiya pratibha ne 1980 me "
                "do 13-ankon wali sankhyaon ka guna sirf 28 "
                "second me karke dikhaya — ek Guinness world "
                "record.",
                "Unhone 'Puzzles to Puzzle You' jaisi lokpriya "
                "maths kitabein likhi aur dikhaya ki tez "
                "ganana ek seekhi ja sakne wali kala hai, "
                "jadu nahi.",
                "Short me: dimag ki tez ganana ka sabse bada "
                "naam — Shakuntala Devi.",
            ],
        },
        "dev": {
            "answer": "शकुंतला देवी (1929–2013) — भारत की "
                      "'Human Computer'",
            "steps": [
                "बेंगलुरु की इस भारतीय प्रतिभा ने 1980 में दो "
                "13-अंकों वाली संख्याओं का गुणा सिर्फ़ 28 "
                "सेकंड में करके दिखाया — एक Guinness विश्व "
                "रिकॉर्ड।",
                "उन्होंने 'Puzzles to Puzzle You' जैसी "
                "लोकप्रिय गणित पुस्तकें लिखीं और दिखाया कि "
                "तेज़ गणना एक सीखी जा सकने वाली कला है, जादू "
                "नहीं।",
                "संक्षेप में: दिमाग़ की तेज़ गणना का सबसे "
                "बड़ा नाम — शकुंतला देवी।",
            ],
        },
    },
    {
        "id": "ramanujan",
        "keywords": ("ramanujan", "रामानुजन",
                     # Wave 185: voice spelling "ramanuja
                     # kaun tha" (final n dropped) missed.
                     "ramanuja"),
        "en": {
            "answer": "Srinivasa Ramanujan (1887–1920) — "
                      "India's self-taught maths genius",
            "steps": [
                "Born in Erode, Tamil Nadu, Ramanujan taught "
                "himself advanced maths from borrowed books "
                "and filled notebooks with about 3,900 "
                "original results.",
                "He worked with G. H. Hardy in Cambridge on "
                "number theory and partitions, and became a "
                "Fellow of the Royal Society — with almost no "
                "formal training.",
                "Short me: bina teacher ke duniya ke sabse "
                "bade ganitagyaon me se ek.",
            ],
        },
        "roman": {
            "answer": "Srinivasa Ramanujan (1887–1920) — India "
                      "ke khud-se-seekhe hue maths genius",
            "steps": [
                "Erode, Tamil Nadu me janme Ramanujan ne "
                "udhaar ki kitabon se khud uncha ganit seekha "
                "aur lagbhag 3,900 naye parinaamon se "
                "notebook bhar diye.",
                "Unhone Cambridge me G. H. Hardy ke saath "
                "number theory aur partitions par kaam kiya "
                "aur Royal Society ke Fellow bane — bina kisi "
                "formal training ke.",
                "Short me: bina teacher ke duniya ke sabse "
                "bade ganitagyaon me se ek.",
            ],
        },
        "dev": {
            "answer": "श्रीनिवास रामानुजन (1887–1920) — भारत "
                      "के स्वयं-शिक्षित गणित प्रतिभा",
            "steps": [
                "इरोड, तमिलनाडु में जन्मे रामानुजन ने उधार की "
                "पुस्तकों से स्वयं उच्च गणित सीखा और लगभग "
                "3,900 नए परिणामों से नोटबुक भर दीं।",
                "उन्होंने कैम्ब्रिज में G. H. Hardy के साथ "
                "संख्या सिद्धांत और विभाजनों पर कार्य किया "
                "और Royal Society के Fellow बने — बिना किसी "
                "औपचारिक प्रशिक्षण के।",
                "संक्षेप में: बिना शिक्षक के दुनिया के सबसे "
                "बड़े गणितज्ञों में से एक।",
            ],
        },
    },
    {
        "id": "aryabhata",
        "keywords": ("aryabhata", "aryabhatta", "आर्यभट",
                     # Wave 185: voice spelling "aryabhat
                     # ne kya kia tha" (final a dropped)
                     # missed; as a substring it also matches
                     # the full name, which is the same entry.
                     "aryabhat",
                     # Wave 177: seed-list item 3 — the
                     # school-GK title for Aryabhata.
                     "father of indian mathematics",
                     "father of indian maths",
                     "bharatiya ganit ke janak",
                     "भारतीय गणित के जनक"),
        "en": {
            "answer": "Aryabhata (476–550 CE) — author of the "
                      "Aryabhatiya",
            "steps": [
                "At just 23, Aryabhata wrote the Aryabhatiya "
                "(499 CE), covering place value, π ≈ 3.1416 "
                "and a sine (jya) table.",
                "He also explained that the Earth rotates on "
                "its own axis — centuries before this was "
                "accepted in Europe.",
                "India's first satellite was named Aryabhata "
                "after him.",
                "Short me: Bharat ke sabse purane mahaan "
                "ganitagyaon me se ek.",
            ],
        },
        "roman": {
            "answer": "Aryabhata (476–550 CE) — Aryabhatiya ke "
                      "lekhak",
            "steps": [
                "Sirf 23 saal ki umr me Aryabhata ne "
                "Aryabhatiya (499 CE) likhi — jisme sthaniya "
                "maan (place value), π ≈ 3.1416 aur sine "
                "(jya) ki table di gayi.",
                "Unhone ye bhi bataya ki Prithvi apni dhuri "
                "par ghoomti hai — Europe me ye baat "
                "shatabdiyon baad maani gayi.",
                "India ke pehle upgrah (satellite) ka naam "
                "unke samman me Aryabhata rakha gaya.",
                "Short me: Bharat ke sabse purane mahaan "
                "ganitagyaon me se ek.",
            ],
        },
        "dev": {
            "answer": "आर्यभट (476–550 ई.) — आर्यभटीय के लेखक",
            "steps": [
                "सिर्फ़ 23 वर्ष की आयु में आर्यभट ने आर्यभटीय "
                "(499 ई.) लिखी — जिसमें स्थानीय मान (place "
                "value), π ≈ 3.1416 और sine (ज्या) की सारणी "
                "दी गई।",
                "उन्होंने यह भी बताया कि पृथ्वी अपनी धुरी पर "
                "घूमती है — यूरोप में यह बात शताब्दियों बाद "
                "मानी गई।",
                "भारत के पहले उपग्रह का नाम उनके सम्मान में "
                "आर्यभट रखा गया।",
                "संक्षेप में: भारत के सबसे प्राचीन महान "
                "गणितज्ञों में से एक।",
            ],
        },
    },
    {
        "id": "brahmagupta",
        "keywords": ("brahmagupta", "ब्रह्मगुप्त",
                     # Wave 185: voice spellings "brahmgupt
                     # kaun tha" / "brahmagupt" (a dropped)
                     # missed every keyword above.
                     "brahmgupt", "brahmagupt"),
        "en": {
            "answer": "Brahmagupta (598–668 CE) — the first to "
                      "give clear rules for zero",
            "steps": [
                "His book Brahmasphutasiddhanta (628 CE) gave "
                "clear rules for zero and for negative numbers "
                "(which he treated as 'debts').",
                "He also gave a famous formula for the area of "
                "a cyclic quadrilateral and methods for hard "
                "equations that Europe learnt much later.",
                "Short me: zero aur negative numbers ke niyam "
                "dene wale pehle ganitagya.",
            ],
        },
        "roman": {
            "answer": "Brahmagupta (598–668 CE) — zero ke saaf "
                      "niyam dene wale pehle ganitagya",
            "steps": [
                "Unki kitab Brahmasphutasiddhanta (628 CE) "
                "me zero aur negative numbers (jinhe ve "
                "'rina' yani karz kehte the) ke saaf niyam "
                "diye gaye.",
                "Unhone chakriya chaturbhuj ke kshetrafal ka "
                "prasiddh sutra aur kathin samikaranon ke "
                "tareeke bhi diye, jo Europe ne bahut baad "
                "me seekhe.",
                "Short me: zero aur negative numbers ke niyam "
                "dene wale pehle ganitagya.",
            ],
        },
        "dev": {
            "answer": "ब्रह्मगुप्त (598–668 ई.) — शून्य के "
                      "स्पष्ट नियम देने वाले पहले गणितज्ञ",
            "steps": [
                "उनकी पुस्तक ब्राह्मस्फुटसिद्धांत (628 ई.) "
                "में शून्य और ऋणात्मक संख्याओं (जिन्हें वे "
                "'ऋण' कहते थे) के स्पष्ट नियम दिए गए।",
                "उन्होंने चक्रीय चतुर्भुज के क्षेत्रफल का "
                "प्रसिद्ध सूत्र और कठिन समीकरणों की विधियाँ "
                "भी दीं, जो यूरोप ने बहुत बाद में सीखीं।",
                "संक्षेप में: शून्य और ऋणात्मक संख्याओं के "
                "नियम देने वाले पहले गणितज्ञ।",
            ],
        },
    },
    {
        "id": "bhaskara",
        "keywords": ("bhaskara", "bhaskaracharya", "भास्कर",
                     "lilavati", "लीलावती"),
        "en": {
            "answer": "Bhaskara II (1114–1185) — author of "
                      "the famous Lilavati",
            "steps": [
                "Bhaskaracharya's Lilavati is a beloved book "
                "of arithmetic problems written in verse — "
                "tradition says it is named after his "
                "daughter.",
                "His work covered equations and geometry, "
                "solved hard equations by the chakravala "
                "method, and used ideas close to calculus "
                "centuries before Newton.",
                "Short me: Lilavati wale Bhaskaracharya — "
                "kavita me ganit sikhane wale.",
            ],
        },
        "roman": {
            "answer": "Bhaskara II (1114–1185) — prasiddh "
                      "Lilavati ke lekhak",
            "steps": [
                "Bhaskaracharya ki Lilavati kavita me likhi "
                "ganit ki priya kitab hai — katha hai ki ye "
                "unki beti ke naam par hai.",
                "Unke kaam me samikaran aur geometry ke "
                "saath-saath chakravala vidhi se kathin "
                "samikaranon ke hal aur calculus ke kareeb "
                "ke vichaar the — Newton se shatabdiyon "
                "pehle.",
                "Short me: Lilavati wale Bhaskaracharya — "
                "kavita me ganit sikhane wale.",
            ],
        },
        "dev": {
            "answer": "भास्कर द्वितीय (1114–1185) — प्रसिद्ध "
                      "लीलावती के लेखक",
            "steps": [
                "भास्कराचार्य की लीलावती कविता में लिखी गणित "
                "की प्रिय पुस्तक है — कथा है कि यह उनकी बेटी "
                "के नाम पर है।",
                "उनके कार्य में समीकरण और ज्यामिति के "
                "साथ-साथ चक्रवाल विधि से कठिन समीकरणों के हल "
                "और कलन के करीब के विचार थे — न्यूटन से "
                "शताब्दियों पहले।",
                "संक्षेप में: लीलावती वाले भास्कराचार्य — "
                "कविता में गणित सिखाने वाले।",
            ],
        },
    },
    # Wave 177: three seed-list titles/persons the who layer
    # missed (Suraj's web-sourced GK list, 19 Nov 2026).
    {
        "id": "archimedes",
        "keywords": ("archimedes", "आर्किमिडीज़",
                     "father of mathematics", "father of maths",
                     "maths ke janak", "maths ke pita",
                     "ganit ke janak", "गणित के जनक",
                     "गणित के पिता",
                     # Wave 185: the Roman "ka" forms —
                     # "ganit ka pita kaun hai" and "ganit
                     # ka janak kise kehte hai" reached only
                     # the AI legs although this entry is
                     # exactly that fact in its "ke" dress.
                     "ganit ka pita", "ganit ka janak",
                     "ganit ke pita", "maths ka pita"),
        "en": {
            "answer": "Father of Mathematics — Archimedes is "
                      "commonly called the Father of "
                      "Mathematics",
            "steps": [
                "Archimedes (Greek, ~287–212 BCE) was the "
                "greatest mathematician of the ancient world "
                "— he found a close value of pi and ways to "
                "measure areas and volumes that later grew "
                "into calculus.",
                "Short me: school ki kitabon me aksar "
                "Archimedes ko hi 'Father of Mathematics' "
                "kaha jata hai.",
            ],
        },
        "roman": {
            "answer": "Father of Mathematics — aksar "
                      "Archimedes ko 'Father of Mathematics' "
                      "kaha jata hai",
            "steps": [
                "Archimedes (Greek, ~287–212 BCE) prachin "
                "duniya ke sabse bade ganitagya the — unhone "
                "pi ka acha maan aur kshetrafal-aayatan "
                "naapne ke tareeke diye, jinse aage chal kar "
                "calculus bana.",
                "Short me: school ki kitabon me aksar "
                "Archimedes ko hi 'Father of Mathematics' "
                "kaha jata hai.",
            ],
        },
        "dev": {
            "answer": "गणित के जनक — अक्सर आर्किमिडीज़ को "
                      "'Father of Mathematics' कहा जाता है",
            "steps": [
                "आर्किमिडीज़ (यूनानी, ~287–212 ई.पू.) प्राचीन "
                "दुनिया के सबसे बड़े गणितज्ञ थे — उन्होंने "
                "pi का अच्छा मान और क्षेत्रफल-आयतन मापने की "
                "विधियाँ दीं, जिनसे आगे चलकर कलन बना।",
                "संक्षेप में: विद्यालय की पुस्तकों में अक्सर "
                "आर्किमिडीज़ को ही 'Father of Mathematics' "
                "कहा जाता है।",
            ],
        },
    },
    {
        "id": "gauss",
        "keywords": ("gauss", "गाउस", "father of number theory",
                     "sankhya siddhant ke janak"),
        "en": {
            "answer": "Gauss — Carl Friedrich Gauss, called "
                      "the Prince of Mathematics and the "
                      "Father of Number Theory",
            "steps": [
                "Gauss (German, 1777–1855) organised number "
                "theory in his book 'Disquisitiones "
                "Arithmeticae' (1801).",
                "Prasiddh katha hai ki bachpan me unhone 1 "
                "se 100 tak ka yog (5050) kuch hi pal me "
                "nikaal diya tha — jodi banakar: 101 × 50.",
                "Short me: number theory ka vyavasthit roop "
                "Gauss ki den hai.",
            ],
        },
        "roman": {
            "answer": "Gauss — Carl Friedrich Gauss, jinhe "
                      "Prince of Mathematics aur Father of "
                      "Number Theory kaha jata hai",
            "steps": [
                "Gauss (German, 1777–1855) ne apni kitab "
                "'Disquisitiones Arithmeticae' (1801) me "
                "number theory ko vyavasthit roop diya.",
                "Prasiddh katha hai ki bachpan me unhone 1 "
                "se 100 tak ka yog (5050) kuch hi pal me "
                "nikaal diya tha — jodi banakar: 101 × 50.",
                "Short me: number theory ka vyavasthit roop "
                "Gauss ki den hai.",
            ],
        },
        "dev": {
            "answer": "गाउस — कार्ल फ़्रेडरिक गाउस, जिन्हें "
                      "गणित का राजकुमार और संख्या सिद्धांत का "
                      "जनक कहा जाता है",
            "steps": [
                "गाउस (जर्मन, 1777–1855) ने अपनी पुस्तक "
                "'Disquisitiones Arithmeticae' (1801) में "
                "संख्या सिद्धांत को व्यवस्थित रूप दिया।",
                "प्रसिद्ध कथा है कि बचपन में उन्होंने 1 से "
                "100 तक का योग (5050) कुछ ही पल में निकाल "
                "दिया था — जोड़ी बनाकर: 101 × 50।",
                "संक्षेप में: संख्या सिद्धांत का व्यवस्थित "
                "रूप गाउस की देन है।",
            ],
        },
    },
    {
        "id": "fibonacci",
        "keywords": ("fibonacci", "fibonachi", "फिबोनाची"),
        "en": {
            "answer": "Fibonacci sequence — Leonardo "
                      "Fibonacci; 0, 1, 1, 2, 3, 5, 8, 13, …",
            "steps": [
                "Har agla number pichle do numbers ka yog "
                "hota hai: 0, 1, 1, 2, 3, 5, 8, 13, 21, …",
                "Italian mathematician Leonardo Fibonacci "
                "ne apni kitab 'Liber Abaci' (1202) se is "
                "anukram ko Europe me prasiddh kiya; ye "
                "anukram Bharat me Pingala ke kaam me aur "
                "bhi pehle milta hai.",
                "Ye sequence prakriti me bhi dikhta hai — "
                "phoolon ki pankhudiyon aur shankhon me.",
                "Short me: Fibonacci sequence = pichle do "
                "ka yog, har kadam par.",
            ],
        },
        "roman": {
            "answer": "Fibonacci sequence — Leonardo "
                      "Fibonacci; 0, 1, 1, 2, 3, 5, 8, 13, …",
            "steps": [
                "Har agla number pichle do numbers ka yog "
                "hota hai: 0, 1, 1, 2, 3, 5, 8, 13, 21, …",
                "Italian mathematician Leonardo Fibonacci "
                "ne apni kitab 'Liber Abaci' (1202) se is "
                "anukram ko Europe me prasiddh kiya; ye "
                "anukram Bharat me Pingala ke kaam me aur "
                "bhi pehle milta hai.",
                "Ye sequence prakriti me bhi dikhta hai — "
                "phoolon ki pankhudiyon aur shankhon me.",
                "Short me: Fibonacci sequence = pichle do "
                "ka yog, har kadam par.",
            ],
        },
        "dev": {
            "answer": "फिबोनाची अनुक्रम — लियोनार्डो "
                      "फिबोनाची; 0, 1, 1, 2, 3, 5, 8, 13, …",
            "steps": [
                "हर अगली संख्या पिछली दो संख्याओं का योग "
                "होती है: 0, 1, 1, 2, 3, 5, 8, 13, 21, …",
                "इतालवी गणितज्ञ लियोनार्डो फिबोनाची ने "
                "अपनी पुस्तक 'Liber Abaci' (1202) से इस "
                "अनुक्रम को यूरोप में प्रसिद्ध किया; यह "
                "अनुक्रम भारत में पिंगल के कार्य में और भी "
                "पहले मिलता है।",
                "यह अनुक्रम प्रकृति में भी दिखता है — "
                "फूलों की पंखुड़ियों और शंखों में।",
                "संक्षेप में: फिबोनाची अनुक्रम = पिछले दो "
                "का योग, हर कदम पर।",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Layer 1b (Wave 177): FACTS — school maths-GK that is not a
# WHO question: superlatives ("sabse chhota prime"), counting
# facts ("1 crore me kitne zero"), definitions of maths
# objects ("infinity kya hota hai") and word origins ("algebra
# naam kaha se aaya"). Built from Suraj's web-sourced seed
# list (19 Nov 2026, ~/workspace/ganitra-maths-knowledge-
# web.md; cross-checked school-GK sources). An entry fires
# when a TOPIC keyword AND an ASK phrase are both present
# (plus optional ask2, a bound guard against "100 se chhota"
# bounded asks, and a literal cap against list problems like
# "5, 9, 2 me sabse bada number"). The concept library keeps
# the topics it already defines well (prime kya hota hai, pi
# kya hai, Roman numerals) — this layer only takes the
# specific FACT asks those cards cannot answer. The angle
# sums (triangle 180°, quadrilateral 360°) are likewise NOT
# here: the Wave 103 native schema serves those asks with
# the crisp exact answer, and a fact entry would displace
# it (proven by the wave103/wave107 pins).
# ---------------------------------------------------------------------------

# A bounded ask ("100 se chhota sabse bada prime") is a
# computation, not this fact. The bound phrases must match
# as separate words: "sabse chhota" CONTAINS the substring
# "se chhota" (sab+se), so a plain substring test would
# veto every superlative ask — the lookbehind demands a
# non-letter before "se" (and before Devanagari "से",
# where "सबसे" hides the same trap).
_FACT_BOUND_RE = re.compile(
    r"(?<![a-zA-Z])se (?:chhota|chhoti|kam|bada|badi|pehle)\b"
    r"|(?<![ऀ-ॿ])से (?:छोटा|छोटी|कम|बड़ा|बड़ी)"
    r"|\b(?:below|under|less than|greater than|between)\b"
    r"|ke beech"
    # Wave 212: an N-digit bound ("2 digit ki sabse badi
    # prime number") bounds the ask just as surely — the
    # unbounded fact card must decline it (the solver's
    # N-digit schema owns the bounded ask).
    r"|\b\d+\s*(?:digit|digits|अंक)\b"
    r"|\b(?:single|double|two|three)\s+digit\b")


def _fact_hit(q, entry):
    if not _entry_hit(q, entry):
        return False
    ask = entry.get("ask") or ()
    if ask and not any(a in q for a in ask):
        return False
    ask2 = entry.get("ask2") or ()
    if ask2 and not any(a in q for a in ask2):
        return False
    if entry.get("bound_guard") and _FACT_BOUND_RE.search(q):
        return False
    max_lit = entry.get("max_literals")
    if max_lit is not None:
        t = q.translate(_W159_DEV)
        if len(re.findall(r"\d+(?:\.\d+)?", t)) > max_lit:
            return False
    return True


_PRIME_KW = ("prime", "abhaajya", "अभाज्य", "abhaajy")
_ZERO_COUNT_ASK = ("zero", "zeros", "shunya", "शून्य")

FACTS = [
    {
        "id": "one_neither",
        "keywords": _PRIME_KW + ("composite", "bhaajya", "भाज्य"),
        "ask": ("1 prime hai ya", "1 prime number hai ya",
                "is 1 a prime", "is 1 prime", "1 composite hai ya",
                "kya 1 prime", "1 abhaajya hai ya",
                "1 prime hai ya composite", "one prime or",
                "1 prime or composite", "1 prime hai ki"),
        "en": {
            "answer": "1 is neither prime nor composite",
            "steps": [
                "Prime numbers ke exactly 2 factors hote "
                "hai (1 aur woh khud); composite ke 2 se "
                "zyada. 1 ka sirf ek hi factor hai — isliye "
                "woh na prime hai, na composite.",
                "Short me: 1 ek khaas number hai — neither "
                "prime, nor composite.",
            ],
        },
        "roman": {
            "answer": "1 na prime hai, na composite",
            "steps": [
                "Prime number ke exactly 2 factors hote hai "
                "(1 aur woh khud); composite ke 2 se zyada. "
                "1 ka sirf ek hi factor hai — isliye woh na "
                "prime hai, na composite.",
                "Short me: 1 ek khaas number hai — neither "
                "prime, nor composite.",
            ],
        },
        "dev": {
            "answer": "1 न अभाज्य है, न भाज्य",
            "steps": [
                "अभाज्य संख्याओं के ठीक 2 गुणनखंड होते हैं "
                "(1 और वह स्वयं); भाज्य के 2 से अधिक। 1 का "
                "केवल एक ही गुणनखंड है — इसलिए वह न अभाज्य "
                "है, न भाज्य।",
                "संक्षेप में: 1 एक ख़ास संख्या है — न "
                "अभाज्य, न भाज्य।",
            ],
        },
    },
    {
        "id": "largest_2digit_prime",
        "keywords": _PRIME_KW,
        "ask": ("sabse bada", "sabse badi", "largest",
                "biggest"),
        "ask2": ("two-digit", "two digit", "2-digit",
                 "do ankon", "do ank", "दो अंकों", "2 ankon"),
        "en": {
            "answer": "The largest two-digit prime number "
                      "is 97",
            "steps": [
                "99 = 9 × 11 aur 98 even hai; 97 ko koi "
                "chhoti sankhya baant nahi sakti — woh "
                "prime hai.",
                "Short me: do ankon ka sabse bada prime = 97.",
            ],
        },
        "roman": {
            "answer": "Do ankon ka sabse bada prime number "
                      "97 hai",
            "steps": [
                "99 = 9 × 11 aur 98 even hai; 97 ko koi "
                "chhoti sankhya baant nahi sakti — woh "
                "prime hai.",
                "Short me: do ankon ka sabse bada prime = 97.",
            ],
        },
        "dev": {
            "answer": "दो अंकों की सबसे बड़ी अभाज्य संख्या "
                      "97 है",
            "steps": [
                "99 = 9 × 11 और 98 सम है; 97 को कोई छोटी "
                "संख्या बाँट नहीं सकती — वह अभाज्य है।",
                "संक्षेप में: दो अंकों की सबसे बड़ी अभाज्य "
                "= 97।",
            ],
        },
    },
    {
        "id": "smallest_2digit_prime",
        "keywords": _PRIME_KW,
        "ask": ("sabse chhota", "sabse chhoti", "smallest"),
        "ask2": ("two-digit", "two digit", "2-digit",
                 "do ankon", "do ank", "दो अंकों", "2 ankon"),
        "en": {
            "answer": "The smallest two-digit prime number "
                      "is 11",
            "steps": [
                "10 even hai, uske baad 11 aata hai — 11 ko "
                "sirf 1 aur 11 baant sakte hai.",
                "Short me: do ankon ka sabse chhota prime = 11.",
            ],
        },
        "roman": {
            "answer": "Do ankon ka sabse chhota prime number "
                      "11 hai",
            "steps": [
                "10 even hai, uske baad 11 aata hai — 11 ko "
                "sirf 1 aur 11 baant sakte hai.",
                "Short me: do ankon ka sabse chhota prime = 11.",
            ],
        },
        "dev": {
            "answer": "दो अंकों की सबसे छोटी अभाज्य संख्या "
                      "11 है",
            "steps": [
                "10 सम है, उसके बाद 11 आता है — 11 को "
                "केवल 1 और 11 बाँट सकते हैं।",
                "संक्षेप में: दो अंकों की सबसे छोटी अभाज्य "
                "= 11।",
            ],
        },
    },
    {
        "id": "primes_below_20",
        "keywords": _PRIME_KW,
        "ask": ("kitne", "how many", "batao", "kaun kaun",
                "kaun se"),
        "ask2": ("20 se chhote", "20 se kam", "below 20",
                 "under 20", "20 tak", "20 ke andar"),
        "en": {
            "answer": "20 se chhote kul 8 prime numbers hai",
            "steps": [
                "Woh hai: 2, 3, 5, 7, 11, 13, 17, 19 — kul 8.",
                "Short me: 20 se neeche 8 prime numbers.",
            ],
        },
        "roman": {
            "answer": "20 se chhote kul 8 prime numbers hai",
            "steps": [
                "Woh hai: 2, 3, 5, 7, 11, 13, 17, 19 — kul 8.",
                "Short me: 20 se neeche 8 prime numbers.",
            ],
        },
        "dev": {
            "answer": "20 से छोटे कुल 8 अभाज्य संख्याएँ हैं",
            "steps": [
                "वे हैं: 2, 3, 5, 7, 11, 13, 17, 19 — कुल 8।",
                "संक्षेप में: 20 से नीचे 8 अभाज्य संख्याएँ।",
            ],
        },
    },
    {
        "id": "largest_prime_none",
        "keywords": _PRIME_KW,
        "ask": ("largest prime", "sabse bada prime",
                "sabse badi prime", "sabse bada abhaajya",
                "how many prime numbers are there",
                "kul kitne prime", "total kitne prime",
                "kitne prime number hote hai",
                "prime numbers kitne hote"),
        "bound_guard": True,
        "max_literals": 1,
        "en": {
            "answer": "There is no largest prime number — "
                      "primes are endless",
            "steps": [
                "Euclid ne 2,000 saal se bhi pehle saabit "
                "kiya tha ki prime numbers anant hai — jitna "
                "bada prime socho, usse bada hamesha mil "
                "jayega.",
                "Short me: sabse bada prime koi nahi; primes "
                "kabhi khatm nahi hote.",
            ],
        },
        "roman": {
            "answer": "Koi sabse bada prime number nahi hai — "
                      "prime numbers anant hai",
            "steps": [
                "Euclid ne 2,000 saal se bhi pehle saabit "
                "kiya tha ki prime numbers anant hai — jitna "
                "bada prime socho, usse bada hamesha mil "
                "jayega.",
                "Short me: sabse bada prime koi nahi; primes "
                "kabhi khatm nahi hote.",
            ],
        },
        "dev": {
            "answer": "कोई सबसे बड़ी अभाज्य संख्या नहीं है — "
                      "अभाज्य संख्याएँ अनंत हैं",
            "steps": [
                "यूक्लिड ने 2,000 वर्ष से भी पहले सिद्ध किया "
                "था कि अभाज्य संख्याएँ अनंत हैं — जितनी बड़ी "
                "अभाज्य सोचो, उससे बड़ी हमेशा मिल जाएगी।",
                "संक्षेप में: सबसे बड़ी अभाज्य कोई नहीं; "
                "अभाज्य कभी ख़त्म नहीं होते।",
            ],
        },
    },
    {
        "id": "smallest_odd_prime",
        "keywords": _PRIME_KW,
        "ask": ("smallest odd prime", "sabse chhota odd prime",
                "sabse chhoti odd prime",
                "sabse chhota visham prime",
                "sabse chhoti visham abhaajya"),
        "en": {
            "answer": "The smallest odd prime number is 3",
            "steps": [
                "2 sabse chhota prime hai par woh even hai; "
                "uske baad pehla odd prime 3 hai.",
                "Short me: sabse chhota odd (visham) prime = 3.",
            ],
        },
        "roman": {
            "answer": "Sabse chhota odd prime number 3 hai",
            "steps": [
                "2 sabse chhota prime hai par woh even hai; "
                "uske baad pehla odd prime 3 hai.",
                "Short me: sabse chhota odd (visham) prime = 3.",
            ],
        },
        "dev": {
            "answer": "सबसे छोटी विषम अभाज्य संख्या 3 है",
            "steps": [
                "2 सबसे छोटी अभाज्य है पर वह सम है; उसके "
                "बाद पहली विषम अभाज्य 3 है।",
                "संक्षेप में: सबसे छोटी विषम अभाज्य = 3।",
            ],
        },
    },
    {
        "id": "prime_two",
        "keywords": _PRIME_KW,
        "ask": ("smallest prime", "sabse chhota prime",
                "sabse chhoti prime", "only even prime",
                "ekmatra even prime", "ekmatra sam prime",
                "sabse chhota abhaajya",
                "sabse chhoti abhaajya"),
        "bound_guard": True,
        "en": {
            "answer": "2 — the smallest prime number, and "
                      "the only even prime",
            "steps": [
                "2 ke factors sirf 1 aur 2 hai, isliye woh "
                "prime hai — aur sabse chhota bhi.",
                "2 ke baad har even number 2 se kat jata "
                "hai, isliye 2 hi ekmatra even prime hai.",
                "Short me: sabse chhota prime = 2.",
            ],
        },
        "roman": {
            "answer": "2 — sabse chhota prime number, aur "
                      "ekmatra even prime",
            "steps": [
                "2 ke factors sirf 1 aur 2 hai, isliye woh "
                "prime hai — aur sabse chhota bhi.",
                "2 ke baad har even number 2 se kat jata "
                "hai, isliye 2 hi ekmatra even prime hai.",
                "Short me: sabse chhota prime = 2.",
            ],
        },
        "dev": {
            "answer": "2 — सबसे छोटी अभाज्य संख्या, और "
                      "एकमात्र सम अभाज्य",
            "steps": [
                "2 के गुणनखंड केवल 1 और 2 हैं, इसलिए वह "
                "अभाज्य है — और सबसे छोटी भी।",
                "2 के बाद हर सम संख्या 2 से कट जाती है, "
                "इसलिए 2 ही एकमात्र सम अभाज्य है।",
                "संक्षेप में: सबसे छोटी अभाज्य = 2।",
            ],
        },
    },
    {
        "id": "smallest_composite",
        "keywords": ("composite", "bhaajya", "भाज्य",
                     "samyukt", "संयुक्त"),
        "ask": ("sabse chhota", "sabse chhoti", "smallest"),
        "bound_guard": True,
        "en": {
            "answer": "The smallest composite number is 4",
            "steps": [
                "Composite matlab 1 aur khud ke alawa koi "
                "aur factor bhi ho: 4 = 2 × 2, isliye 4 "
                "pehla composite hai (1 na prime hai na "
                "composite; 2, 3 prime hai).",
                "Short me: sabse chhota composite = 4.",
            ],
        },
        "roman": {
            "answer": "Sabse chhota composite number 4 hai",
            "steps": [
                "Composite matlab 1 aur khud ke alawa koi "
                "aur factor bhi ho: 4 = 2 × 2, isliye 4 "
                "pehla composite hai (1 na prime hai na "
                "composite; 2, 3 prime hai).",
                "Short me: sabse chhota composite = 4.",
            ],
        },
        "dev": {
            "answer": "सबसे छोटी भाज्य संख्या 4 है",
            "steps": [
                "भाज्य मतलब 1 और स्वयं के अलावा कोई और "
                "गुणनखंड भी हो: 4 = 2 × 2, इसलिए 4 पहली "
                "भाज्य है (1 न अभाज्य है न भाज्य; 2, 3 "
                "अभाज्य हैं)।",
                "संक्षेप में: सबसे छोटी भाज्य = 4।",
            ],
        },
    },
    {
        "id": "smallest_natural",
        "keywords": ("natural number", "prakritik sankhya",
                     "प्राकृतिक संख्या", "natural sankhya",
                     # Wave 185: the doubled-a voice spelling
                     # "praakritik sankhya" (board-dress ask
                     # in the prediction battery) missed.
                     "praakritik sankhya"),
        "ask": ("sabse chhota", "sabse chhoti", "smallest"),
        "bound_guard": True,
        "en": {
            "answer": "The smallest natural number is 1",
            "steps": [
                "Natural numbers ginne wali sankhyayen hai: "
                "1, 2, 3, 4, … — shuruaat 1 se hoti hai.",
                "Short me: sabse chhoti prakritik sankhya = 1.",
            ],
        },
        "roman": {
            "answer": "Sabse chhoti natural (prakritik) "
                      "sankhya 1 hai",
            "steps": [
                "Natural numbers ginne wali sankhyayen hai: "
                "1, 2, 3, 4, … — shuruaat 1 se hoti hai.",
                "Short me: sabse chhoti prakritik sankhya = 1.",
            ],
        },
        "dev": {
            "answer": "सबसे छोटी प्राकृतिक संख्या 1 है",
            "steps": [
                "प्राकृतिक संख्याएँ गिनने वाली संख्याएँ हैं: "
                "1, 2, 3, 4, … — शुरुआत 1 से होती है।",
                "संक्षेप में: सबसे छोटी प्राकृतिक संख्या = 1।",
            ],
        },
    },
    {
        "id": "smallest_whole",
        "keywords": ("whole number", "purn sankhya",
                     "पूर्ण संख्या", "whole sankhya"),
        "ask": ("sabse chhota", "sabse chhoti", "smallest"),
        "bound_guard": True,
        "en": {
            "answer": "The smallest whole number is 0",
            "steps": [
                "Whole numbers 0 se shuru hote hai: 0, 1, 2, "
                "3, … — natural numbers me 0 judne se whole "
                "numbers bante hai.",
                "Short me: sabse chhoti purn sankhya = 0.",
            ],
        },
        "roman": {
            "answer": "Sabse chhoti whole (purn) sankhya 0 hai",
            "steps": [
                "Whole numbers 0 se shuru hote hai: 0, 1, 2, "
                "3, … — natural numbers me 0 judne se whole "
                "numbers bante hai.",
                "Short me: sabse chhoti purn sankhya = 0.",
            ],
        },
        "dev": {
            "answer": "सबसे छोटी पूर्ण संख्या 0 है",
            "steps": [
                "पूर्ण संख्याएँ 0 से शुरू होती हैं: 0, 1, 2, "
                "3, … — प्राकृतिक संख्याओं में 0 जुड़ने से "
                "पूर्ण संख्याएँ बनती हैं।",
                "संक्षेप में: सबसे छोटी पूर्ण संख्या = 0।",
            ],
        },
    },
    {
        "id": "no_reciprocal",
        "keywords": ("reciprocal", "vyutkram", "व्युत्क्रम"),
        "ask": ("nahi hota", "nahi hai", "nahin hota",
                "no reciprocal", "kis sankhya", "which number",
                "kaun si sankhya", "kaunsi sankhya"),
        "en": {
            "answer": "0 — zero is the only number with no "
                      "reciprocal",
            "steps": [
                "Reciprocal matlab 1 ko us sankhya se baantna; "
                "1/0 undefined hai (0 se bhaag dena hi mana "
                "hai), isliye 0 ka reciprocal nahi hota.",
                "Short me: reciprocal nahi hai — sirf 0 ka.",
            ],
        },
        "roman": {
            "answer": "0 — zero hi ekmatra sankhya hai jiska "
                      "reciprocal nahi hota",
            "steps": [
                "Reciprocal matlab 1 ko us sankhya se "
                "baantna; 1/0 undefined hai (0 se bhaag dena "
                "hi mana hai), isliye 0 ka reciprocal nahi "
                "hota.",
                "Short me: reciprocal nahi hai — sirf 0 ka.",
            ],
        },
        "dev": {
            "answer": "0 — शून्य ही एकमात्र संख्या है जिसका "
                      "व्युत्क्रम नहीं होता",
            "steps": [
                "व्युत्क्रम मतलब 1 को उस संख्या से बाँटना; "
                "1/0 अपरिभाषित है (0 से भाग देना ही मना है), "
                "इसलिए 0 का व्युत्क्रम नहीं होता।",
                "संक्षेप में: व्युत्क्रम नहीं है — केवल 0 का।",
            ],
        },
    },
    {
        "id": "zero_neither_sign",
        "keywords": ("positive", "negative", "dhanatmak",
                     "rinatmak", "धनात्मक", "ऋणात्मक"),
        "ask": ("neither", "na positive na", "na dhanatmak na",
                "kaun si sankhya", "which number",
                "ekmatra", "only number", "na positive hai na"),
        "en": {
            "answer": "0 — the only number that is neither "
                      "positive nor negative",
            "steps": [
                "0 se badi sankhyayen positive (+), 0 se "
                "chhoti negative (−) hoti hai; 0 beech me "
                "khada hai — na idhar, na udhar.",
                "Short me: na positive, na negative — sirf 0.",
            ],
        },
        "roman": {
            "answer": "0 — ekmatra sankhya jo na positive "
                      "hai, na negative",
            "steps": [
                "0 se badi sankhyayen positive (+), 0 se "
                "chhoti negative (−) hoti hai; 0 beech me "
                "khada hai — na idhar, na udhar.",
                "Short me: na positive, na negative — sirf 0.",
            ],
        },
        "dev": {
            "answer": "0 — एकमात्र संख्या जो न धनात्मक है, न "
                      "ऋणात्मक",
            "steps": [
                "0 से बड़ी संख्याएँ धनात्मक (+), 0 से छोटी "
                "ऋणात्मक (−) होती हैं; 0 बीच में खड़ा है — "
                "न इधर, न उधर।",
                "संक्षेप में: न धनात्मक, न ऋणात्मक — केवल 0।",
            ],
        },
    },
    {
        "id": "lakh_zeros",
        "keywords": ("lakh", "लाख"),
        "ask": _ZERO_COUNT_ASK,
        "en": {
            "answer": "1 lakh has 5 zeros — 1,00,000",
            "steps": [
                "1 lakh = 100000 — gin lo: kul 5 zero.",
                "Short me: 1 lakh me 5 zero.",
            ],
        },
        "roman": {
            "answer": "1 lakh me 5 zero hote hai — 1,00,000",
            "steps": [
                "1 lakh = 100000 — gin lo: kul 5 zero.",
                "Short me: 1 lakh me 5 zero.",
            ],
        },
        "dev": {
            "answer": "1 लाख में 5 शून्य होते हैं — 1,00,000",
            "steps": [
                "1 लाख = 100000 — गिन लो: कुल 5 शून्य।",
                "संक्षेप में: 1 लाख में 5 शून्य।",
            ],
        },
    },
    {
        "id": "crore_zeros",
        "keywords": ("crore", "करोड़", "karod"),
        "ask": _ZERO_COUNT_ASK,
        "en": {
            "answer": "1 crore has 7 zeros — 1,00,00,000",
            "steps": [
                "1 crore = 10000000 — 1 ke peeche kul 7 zero.",
                "Yaad rakho: 1 lakh (5 zero) ke aage 2 zero "
                "aur = 1 crore (7 zero).",
                "Short me: 1 crore me 7 zero.",
            ],
        },
        "roman": {
            "answer": "1 crore me 7 zero hote hai — 1,00,00,000",
            "steps": [
                "1 crore = 10000000 — 1 ke peeche kul 7 zero.",
                "Yaad rakho: 1 lakh (5 zero) ke aage 2 zero "
                "aur = 1 crore (7 zero).",
                "Short me: 1 crore me 7 zero.",
            ],
        },
        "dev": {
            "answer": "1 करोड़ में 7 शून्य होते हैं — "
                      "1,00,00,000",
            "steps": [
                "1 करोड़ = 10000000 — 1 के पीछे कुल 7 शून्य।",
                "याद रखो: 1 लाख (5 शून्य) के आगे 2 शून्य "
                "और = 1 करोड़ (7 शून्य)।",
                "संक्षेप में: 1 करोड़ में 7 शून्य।",
            ],
        },
    },
    {
        "id": "million_zeros",
        "keywords": ("million", "मिलियन"),
        "ask": _ZERO_COUNT_ASK,
        "en": {
            "answer": "1 million has 6 zeros — 1,000,000",
            "steps": [
                "1 million = 10 lakh hota hai — 1 ke peeche "
                "kul 6 zero.",
                "Short me: 1 million me 6 zero.",
            ],
        },
        "roman": {
            "answer": "1 million me 6 zero hote hai — 1,000,000",
            "steps": [
                "1 million = 10 lakh hota hai — 1 ke peeche "
                "kul 6 zero.",
                "Short me: 1 million me 6 zero.",
            ],
        },
        "dev": {
            "answer": "1 मिलियन में 6 शून्य होते हैं — "
                      "1,000,000",
            "steps": [
                "1 मिलियन = 10 लाख होता है — 1 के पीछे कुल "
                "6 शून्य।",
                "संक्षेप में: 1 मिलियन में 6 शून्य।",
            ],
        },
    },
    {
        "id": "billion_zeros",
        "keywords": ("billion", "arab", "अरब"),
        "ask": _ZERO_COUNT_ASK,
        "en": {
            "answer": "1 billion (1 arab) has 9 zeros — "
                      "1,000,000,000",
            "steps": [
                "1 billion = 100 crore hota hai — 1 ke "
                "peeche kul 9 zero.",
                "Short me: 1 billion / 1 arab me 9 zero.",
            ],
        },
        "roman": {
            "answer": "1 billion (1 arab) me 9 zero hote hai "
                      "— 1,000,000,000",
            "steps": [
                "1 billion = 100 crore hota hai — 1 ke "
                "peeche kul 9 zero.",
                "Short me: 1 billion / 1 arab me 9 zero.",
            ],
        },
        "dev": {
            "answer": "1 बिलियन (1 अरब) में 9 शून्य होते हैं "
                      "— 1,000,000,000",
            "steps": [
                "1 बिलियन = 100 करोड़ होता है — 1 के पीछे "
                "कुल 9 शून्य।",
                "संक्षेप में: 1 बिलियन / 1 अरब में 9 शून्य।",
            ],
        },
    },
    {
        "id": "dozen",
        "keywords": ("dozen", "darjan", "दर्जन"),
        "ask": ("kitne", "kya", "how many", "what", "hota",
                "hote"),
        "en": {
            "answer": "1 dozen = 12",
            "steps": [
                "Darjan ginne ki purani ikai hai — 1 darjan "
                "me hamesha 12 cheezein (12 kele, 12 ande).",
                "Short me: 1 dozen = 12.",
            ],
        },
        "roman": {
            "answer": "1 dozen (darjan) me 12 hote hai",
            "steps": [
                "Darjan ginne ki purani ikai hai — 1 darjan "
                "me hamesha 12 cheezein (12 kele, 12 ande).",
                "Short me: 1 dozen = 12.",
            ],
        },
        "dev": {
            "answer": "1 दर्जन = 12",
            "steps": [
                "दर्जन गिनने की पुरानी इकाई है — 1 दर्जन में "
                "हमेशा 12 चीज़ें (12 केले, 12 अंडे)।",
                "संक्षेप में: 1 दर्जन = 12।",
            ],
        },
    },
    {
        "id": "gross",
        "keywords": ("gross", "ग्रॉस"),
        "ask": ("kitne", "kya", "how many", "what", "hota",
                "hote"),
        "en": {
            "answer": "1 gross = 144 (12 dozen)",
            "steps": [
                "1 gross = 12 darjan = 12 × 12 = 144.",
                "Short me: 1 gross = 144.",
            ],
        },
        "roman": {
            "answer": "1 gross me 144 hote hai (12 dozen)",
            "steps": [
                "1 gross = 12 darjan = 12 × 12 = 144.",
                "Short me: 1 gross = 144.",
            ],
        },
        "dev": {
            "answer": "1 ग्रॉस = 144 (12 दर्जन)",
            "steps": [
                "1 ग्रॉस = 12 दर्जन = 12 × 12 = 144।",
                "संक्षेप में: 1 ग्रॉस = 144।",
            ],
        },
    },
    {
        "id": "hardy_ramanujan",
        "keywords": ("1729", "hardy ramanujan",
                     "hardy-ramanujan", "ramanujan number",
                     "taxicab"),
        "ask": ("kya", "kyu", "kyon", "why", "famous",
                "khaas", "special", "mahatva"),
        "en": {
            "answer": "1729 — the Hardy–Ramanujan number",
            "steps": [
                "1729 sabse chhoti sankhya hai jo do alag "
                "tareekon se do cubes ke yog ke roop me likhi "
                "ja sakti hai: 1729 = 1³ + 12³ = 9³ + 10³.",
                "Katha hai: Hardy ne hospital me Ramanujan "
                "ko ye number 'neeras' kaha, aur Ramanujan "
                "ne turant iski ye khaasiyat bata di.",
                "Short me: 1729 = Ramanujan ki pehchan wala "
                "number.",
            ],
        },
        "roman": {
            "answer": "1729 — Hardy–Ramanujan number",
            "steps": [
                "1729 sabse chhoti sankhya hai jo do alag "
                "tareekon se do cubes ke yog ke roop me likhi "
                "ja sakti hai: 1729 = 1³ + 12³ = 9³ + 10³.",
                "Katha hai: Hardy ne hospital me Ramanujan "
                "ko ye number 'neeras' kaha, aur Ramanujan "
                "ne turant iski ye khaasiyat bata di.",
                "Short me: 1729 = Ramanujan ki pehchan wala "
                "number.",
            ],
        },
        "dev": {
            "answer": "1729 — हार्डी–रामानुजन संख्या",
            "steps": [
                "1729 सबसे छोटी संख्या है जो दो अलग तरीकों "
                "से दो घनों के योग के रूप में लिखी जा सकती "
                "है: 1729 = 1³ + 12³ = 9³ + 10³।",
                "कथा है: हार्डी ने अस्पताल में रामानुजन को "
                "यह संख्या 'नीरस' कही, और रामानुजन ने तुरंत "
                "इसकी यह ख़ासियत बता दी।",
                "संक्षेप में: 1729 = रामानुजन की पहचान वाली "
                "संख्या।",
            ],
        },
    },
    {
        "id": "infinity",
        "keywords": ("infinity", "infinite", "anant",
                     "अनंत", "अनन्त", "∞"),
        "ask": ("kya", "matlab", "what", "meaning", "symbol",
                "chinh", "kisne", "who", "kaun"),
        "en": {
            "answer": "Infinity (∞) — a quantity with no end; "
                      "it is not a number",
            "steps": [
                "Infinity ka matlab hai jo kabhi khatm na ho "
                "— jaise sankhyayen: kitni bhi badi sankhya "
                "socho, usse badi hamesha hai.",
                "Iska chinh ∞ sabse pehle John Wallis ne "
                "diya tha (1655).",
                "Short me: ∞ = ant-heen, jo gina na ja sake.",
            ],
        },
        "roman": {
            "answer": "Infinity (∞) — jo kabhi khatm na ho; "
                      "ye koi number nahi hai",
            "steps": [
                "Infinity ka matlab hai ant-heen — jaise "
                "sankhyayen: kitni bhi badi sankhya socho, "
                "usse badi hamesha hai.",
                "Iska chinh ∞ sabse pehle John Wallis ne "
                "diya tha (1655).",
                "Short me: ∞ = ant-heen, jo gina na ja sake.",
            ],
        },
        "dev": {
            "answer": "अनंत (∞) — जो कभी ख़त्म न हो; यह कोई "
                      "संख्या नहीं है",
            "steps": [
                "अनंत का मतलब है अंत-हीन — जैसे संख्याएँ: "
                "कितनी भी बड़ी संख्या सोचो, उससे बड़ी हमेशा "
                "है।",
                "इसका चिह्न ∞ सबसे पहले जॉन वॉलिस ने दिया "
                "था (1655)।",
                "संक्षेप में: ∞ = अंत-हीन, जो गिना न जा सके।",
            ],
        },
    },
    {
        "id": "decimal_system",
        "keywords": ("decimal", "dashamlav", "दशमलव",
                     "place value", "place-value",
                     "hindu-arabic", "hindu arabic"),
        "ask": ("kisne", "kaha", "kahan", "origin", "where",
                "who", "kab", "banaya", "aaya", "aayi",
                "invent"),
        "en": {
            "answer": "The decimal place-value system comes "
                      "from India",
            "steps": [
                "0 aur sthan-man (place value) wala aaj ka "
                "number system Bharat me bana; Arab "
                "vyapariyon ke dwara ye duniya bhar gaya — "
                "isiliye in ankon ko 'Hindu-Arabic numerals' "
                "kehte hai.",
                "Short me: decimal system ki jad Bharat hai.",
            ],
        },
        "roman": {
            "answer": "Decimal (place-value) system Bharat "
                      "se aaya hai",
            "steps": [
                "0 aur sthan-man (place value) wala aaj ka "
                "number system Bharat me bana; Arab "
                "vyapariyon ke dwara ye duniya bhar gaya — "
                "isiliye in ankon ko 'Hindu-Arabic numerals' "
                "kehte hai.",
                "Short me: decimal system ki jad Bharat hai.",
            ],
        },
        "dev": {
            "answer": "दशमलव स्थान-मान प्रणाली भारत से आई है",
            "steps": [
                "0 और स्थान-मान वाला आज का संख्या तंत्र "
                "भारत में बना; अरब व्यापारियों के द्वारा यह "
                "दुनिया भर गया — इसीलिए इन अंकों को "
                "'Hindu-Arabic numerals' कहते हैं।",
                "संक्षेप में: दशमलव प्रणाली की जड़ भारत है।",
            ],
        },
    },
    {
        "id": "geometry_origin",
        "keywords": ("geometry", "ज्यामिति", "jyamiti"),
        "ask": ("kaha se aaya", "kahan se aaya", "naam kaha",
                "shabd kaha", "shabd ka matlab", "origin",
                "matlab kya", "meaning", "word",
                # Wave 185: the spoken origin dress —
                # "geometry ki shuruaat kahan se hui" names
                # a beginning, not an "aaya"; it matched no
                # ask phrase and classified as gibberish.
                "shuruaat", "shuruvat", "kahan se hui",
                "kahan se hua", "kahan se shuru"),
        "en": {
            "answer": "Geometry — from Greek 'geo' (earth) "
                      "+ 'metria' (measurement)",
            "steps": [
                "Geometry shabd do Greek shabdon se bana: "
                "geo = dharti (earth), metria = maap "
                "(measurement) — matlab dharti ko naapne ka "
                "vigyaan, jisse khet aur zameen naapi jaati "
                "thi.",
                "Short me: geometry = dharti ki maap.",
            ],
        },
        "roman": {
            "answer": "Geometry — Greek 'geo' (dharti) + "
                      "'metria' (maap) se bana shabd",
            "steps": [
                "Geometry do Greek shabdon se bana: geo = "
                "dharti (earth), metria = maap (measurement) "
                "— matlab dharti ko naapne ka vigyaan, jisse "
                "khet aur zameen naapi jaati thi.",
                "Short me: geometry = dharti ki maap.",
            ],
        },
        "dev": {
            "answer": "ज्यामिति — यूनानी 'geo' (धरती) + "
                      "'metria' (माप) से बना शब्द",
            "steps": [
                "Geometry दो यूनानी शब्दों से बना: geo = "
                "धरती, metria = माप — मतलब धरती को मापने का "
                "विज्ञान, जिससे खेत और ज़मीन मापी जाती थी।",
                "संक्षेप में: geometry = धरती की माप।",
            ],
        },
    },
    {
        "id": "algebra_origin",
        "keywords": ("algebra", "बीजगणित", "beejganit",
                     "bijganit",
                     # Wave 185: voice spelling, as on the
                     # HISTORY algebra entry.
                     "aljebra"),
        "ask": ("kaha se aaya", "kahan se aaya", "naam kaha",
                "shabd kaha", "shabd ka", "origin", "al-jabr",
                "word"),
        "en": {
            "answer": "Algebra — the word comes from Arabic "
                      "'al-jabr', from al-Khwarizmi's book",
            "steps": [
                "Al-Khwarizmi ki kitab 'Al-Kitab "
                "al-Mukhtasar fi Hisab al-Jabr' ke 'al-jabr' "
                "shabd se 'algebra' bana; 'algorithm' shabd "
                "bhi unke naam se aaya hai.",
                "Short me: algebra naam Arabic 'al-jabr' "
                "se aaya.",
            ],
        },
        "roman": {
            "answer": "Algebra — shabd Arabic 'al-jabr' se "
                      "aaya, al-Khwarizmi ki kitab se",
            "steps": [
                "Al-Khwarizmi ki kitab 'Al-Kitab "
                "al-Mukhtasar fi Hisab al-Jabr' ke 'al-jabr' "
                "shabd se 'algebra' bana; 'algorithm' shabd "
                "bhi unke naam se aaya hai.",
                "Short me: algebra naam Arabic 'al-jabr' "
                "se aaya.",
            ],
        },
        "dev": {
            "answer": "बीजगणित — 'algebra' शब्द अरबी "
                      "'al-jabr' से आया, अल-ख्वारिज़्मी की "
                      "पुस्तक से",
            "steps": [
                "अल-ख्वारिज़्मी की पुस्तक 'अल-किताब "
                "अल-मुख्तसर फ़ी हिसाब अल-जब्र' के 'अल-जब्र' "
                "शब्द से 'algebra' बना; 'algorithm' शब्द भी "
                "उनके नाम से आया है।",
                "संक्षेप में: algebra नाम अरबी 'al-jabr' से "
                "आया।",
            ],
        },
    },
    {
        "id": "trigonometry_origin",
        "keywords": ("trigonometry", "त्रिकोणमिति",
                     "trikonmiti"),
        "ask": ("kaha se aaya", "naam kaha", "shabd",
                "matlab", "origin", "word", "meaning",
                "kya hota"),
        "en": {
            "answer": "Trigonometry — Greek 'trigonon' "
                      "(triangle) + 'metron' (measure)",
            "steps": [
                "Trigonometry ka matlab hai tribhuj ki "
                "bhujaon aur konon ko naapna — Greek "
                "'trigonon' (tribhuj) + 'metron' (maap).",
                "Short me: trigonometry = tribhuj ki maap "
                "ka adhyayan.",
            ],
        },
        "roman": {
            "answer": "Trigonometry — Greek 'trigonon' "
                      "(tribhuj) + 'metron' (maap)",
            "steps": [
                "Trigonometry ka matlab hai tribhuj ki "
                "bhujaon aur konon ko naapna — Greek "
                "'trigonon' (tribhuj) + 'metron' (maap).",
                "Short me: trigonometry = tribhuj ki maap "
                "ka adhyayan.",
            ],
        },
        "dev": {
            "answer": "त्रिकोणमिति — यूनानी 'trigonon' "
                      "(त्रिभुज) + 'metron' (माप)",
            "steps": [
                "त्रिकोणमिति का मतलब है त्रिभुज की भुजाओं "
                "और कोणों को मापना — यूनानी 'trigonon' "
                "(त्रिभुज) + 'metron' (माप)।",
                "संक्षेप में: trigonometry = त्रिभुज की माप "
                "का अध्ययन।",
            ],
        },
    },
    {
        "id": "golden_ratio",
        "keywords": ("golden ratio", "golden anupat",
                     "swarn anupat", "sunahra anupat",
                     "स्वर्ण अनुपात"),
        "ask": ("kya", "what", "value", "maan", "kitna",
                "matlab"),
        "en": {
            "answer": "The golden ratio φ ≈ 1.618",
            "steps": [
                "Jab ek lambai ko is tarah baanta jaye ki "
                "poora : bada hissa = bada hissa : chhota "
                "hissa, to woh anupat golden ratio (φ ≈ "
                "1.618) kehlata hai — prakriti aur kala me "
                "baar-baar dikhta hai.",
                "Short me: golden ratio ≈ 1.618.",
            ],
        },
        "roman": {
            "answer": "Golden ratio φ ≈ 1.618 hota hai",
            "steps": [
                "Jab ek lambai ko is tarah baanta jaye ki "
                "poora : bada hissa = bada hissa : chhota "
                "hissa, to woh anupat golden ratio (φ ≈ "
                "1.618) kehlata hai — prakriti aur kala me "
                "baar-baar dikhta hai.",
                "Short me: golden ratio ≈ 1.618.",
            ],
        },
        "dev": {
            "answer": "स्वर्ण अनुपात φ ≈ 1.618 होता है",
            "steps": [
                "जब एक लंबाई को इस तरह बाँटा जाए कि पूरा : "
                "बड़ा हिस्सा = बड़ा हिस्सा : छोटा हिस्सा, तो "
                "वह अनुपात स्वर्ण अनुपात (φ ≈ 1.618) कहलाता "
                "है — प्रकृति और कला में बार-बार दिखता है।",
                "संक्षेप में: golden ratio ≈ 1.618।",
            ],
        },
    },
    {
        "id": "maths_full_form",
        "keywords": ("full form",),
        "ask": ("maths", "math", "ganit", "गणित",
                "mathematics"),
        "en": {
            "answer": "Maths has no full form — it is the "
                      "short form of 'Mathematics'",
            "steps": [
                "'Mathematics' Greek shabd 'mathematika' "
                "(seekhne ki cheezein) se aaya hai; 'maths' "
                "usi ka chhota roop hai — iska koi alag full "
                "form nahi hota.",
                "Short me: Maths = Mathematics ka short form.",
            ],
        },
        "roman": {
            "answer": "Maths ka koi full form nahi hota — ye "
                      "'Mathematics' ka short form hai",
            "steps": [
                "'Mathematics' Greek shabd 'mathematika' "
                "(seekhne ki cheezein) se aaya hai; 'maths' "
                "usi ka chhota roop hai — iska koi alag full "
                "form nahi hota.",
                "Short me: Maths = Mathematics ka short form.",
            ],
        },
        "dev": {
            "answer": "Maths का कोई full form नहीं होता — यह "
                      "'Mathematics' का छोटा रूप है",
            "steps": [
                "'Mathematics' यूनानी शब्द 'mathematika' "
                "(सीखने की चीज़ें) से आया है; 'maths' उसी का "
                "छोटा रूप है — इसका कोई अलग full form नहीं "
                "होता।",
                "संक्षेप में: Maths = Mathematics का short "
                "form।",
            ],
        },
    },
    {
        "id": "equals_sign",
        "keywords": ("barabar ka sign", "barabar ka chinh",
                     "barabar wala sign", "equals sign",
                     "equal sign", "बराबर का चिह्न",
                     "बराबर का चिन्ह"),
        "ask": ("kisne", "who", "kab", "banaya", "diya",
                "invent"),
        "en": {
            "answer": "The equals sign (=) was given by "
                      "Robert Recorde (1557)",
            "steps": [
                "Welsh mathematician Robert Recorde ne "
                "apni kitab 'The Whetstone of Witte' (1557) "
                "me = ka chinh sabse pehle istemal kiya — "
                "do barabar lambai ki rekhaen, kyunki unke "
                "liye barabar ki sabse sahi pehchan yahi thi.",
                "Short me: = ka chinh Robert Recorde ki den "
                "hai (1557).",
            ],
        },
        "roman": {
            "answer": "Barabar ka sign (=) Robert Recorde ne "
                      "diya tha (1557)",
            "steps": [
                "Welsh ganitagya Robert Recorde ne apni "
                "kitab 'The Whetstone of Witte' (1557) me = "
                "ka chinh sabse pehle istemal kiya — do "
                "barabar lambai ki rekhaen, kyunki unke liye "
                "barabar ki sabse sahi pehchan yahi thi.",
                "Short me: = ka chinh Robert Recorde ki den "
                "hai (1557).",
            ],
        },
        "dev": {
            "answer": "बराबर का चिह्न (=) रॉबर्ट रेकॉर्ड ने "
                      "दिया था (1557)",
            "steps": [
                "वेल्श गणितज्ञ रॉबर्ट रेकॉर्ड ने अपनी पुस्तक "
                "'The Whetstone of Witte' (1557) में = का "
                "चिह्न सबसे पहले इस्तेमाल किया — दो बराबर "
                "लंबाई की रेखाएँ, क्योंकि उनके लिए बराबर की "
                "सबसे सही पहचान यही थी।",
                "संक्षेप में: = का चिह्न रॉबर्ट रेकॉर्ड की "
                "देन है (1557)।",
            ],
        },
    },
    {
        "id": "pi_day",
        "keywords": ("pi day", "π day"),
        "ask": ("kab", "when", "date", "manaya", "celebrat"),
        "en": {
            "answer": "Pi Day is celebrated on 14 March "
                      "(3/14)",
            "steps": [
                "π ka maan 3.14… hai, isliye March (3rd "
                "mahina) ki 14 taareekh ko Pi Day manaya "
                "jata hai.",
                "Short me: Pi Day = 14 March.",
            ],
        },
        "roman": {
            "answer": "Pi Day 14 March (3/14) ko manaya jata "
                      "hai",
            "steps": [
                "π ka maan 3.14… hai, isliye March (3rd "
                "mahina) ki 14 taareekh ko Pi Day manaya "
                "jata hai.",
                "Short me: Pi Day = 14 March.",
            ],
        },
        "dev": {
            "answer": "Pi Day 14 मार्च (3/14) को मनाया जाता "
                      "है",
            "steps": [
                "π का मान 3.14… है, इसलिए मार्च (तीसरे "
                "महीने) की 14 तारीख़ को Pi Day मनाया जाता "
                "है।",
                "संक्षेप में: Pi Day = 14 मार्च।",
            ],
        },
    },
    {
        "id": "polygons",
        "keywords": ("pentagon", "hexagon", "heptagon",
                     "octagon", "nonagon", "decagon",
                     "dodecagon", "panchbhuj", "shatbhuj",
                     "अष्टभुज", "पंचभुज"),
        # Ask must be about SIDES or the NAME — a bare
        # "kitne / how many" also matches diagonals, area
        # and angle computations that native schemas own
        # (the wave55 hexagon-diagonals pin proved it).
        "ask": ("side", "bhuja", "भुजा", "kya kehte",
                "kise kehte", "called", "naam", "name"),
        "en": {
            "answer": "Pentagon 5, Hexagon 6, Heptagon 7, "
                      "Octagon 8, Nonagon 9, Decagon 10, "
                      "Dodecagon 12 sides",
            "steps": [
                "Aur yaad rakho: 3 bhujaon wali aakriti "
                "triangle (tribhuj), 4 wali quadrilateral "
                "(chaturbhuj) kehlati hai.",
                "Short me: naam me hi bhujaon ki ginati "
                "chhupi hai — penta = 5, hexa = 6, octa = 8, "
                "deca = 10.",
            ],
        },
        "roman": {
            "answer": "Pentagon 5, Hexagon 6, Heptagon 7, "
                      "Octagon 8, Nonagon 9, Decagon 10, "
                      "Dodecagon 12 bhujaen",
            "steps": [
                "Aur yaad rakho: 3 bhujaon wali aakriti "
                "triangle (tribhuj), 4 wali quadrilateral "
                "(chaturbhuj) kehlati hai.",
                "Short me: naam me hi bhujaon ki ginati "
                "chhupi hai — penta = 5, hexa = 6, octa = 8, "
                "deca = 10.",
            ],
        },
        "dev": {
            "answer": "पंचभुज 5, षट्भुज 6, सप्तभुज 7, "
                      "अष्टभुज 8, नवभुज 9, दशभुज 10, "
                      "द्वादशभुज 12 भुजाएँ",
            "steps": [
                "और याद रखो: 3 भुजाओं वाली आकृति त्रिभुज, "
                "4 वाली चतुर्भुज कहलाती है।",
                "संक्षेप में: नाम में ही भुजाओं की गिनती "
                "छुपी है — penta = 5, hexa = 6, octa = 8, "
                "deca = 10।",
            ],
        },
    },
    {
        "id": "circumference_name",
        "keywords": ("circumference", "paridhi", "परिधि"),
        "ask": ("aur kya", "another name", "dusra naam",
                "also called", "ko aur kya"),
        "en": {
            "answer": "A circle's circumference is also "
                      "called its perimeter",
            "steps": [
                "Vritt ke chaaron or ki doori (paridhi) ko "
                "hi uska perimeter (parimap) kehte hai — "
                "formula bhi ek hi hai: 2πr.",
                "Short me: circumference = circle ka "
                "perimeter.",
            ],
        },
        "roman": {
            "answer": "Circle ki circumference (paridhi) ko "
                      "uska perimeter (parimap) bhi kehte hai",
            "steps": [
                "Vritt ke chaaron or ki doori (paridhi) ko "
                "hi uska perimeter (parimap) kehte hai — "
                "formula bhi ek hi hai: 2πr.",
                "Short me: circumference = circle ka "
                "perimeter.",
            ],
        },
        "dev": {
            "answer": "वृत्त की परिधि को उसका परिमाप "
                      "(perimeter) भी कहते हैं",
            "steps": [
                "वृत्त के चारों ओर की दूरी (परिधि) को ही "
                "उसका परिमाप कहते हैं — सूत्र भी एक ही है: "
                "2πr।",
                "संक्षेप में: circumference = वृत्त का "
                "perimeter।",
            ],
        },
    },
    {
        "id": "largest_number",
        "keywords": ("sankhya", "number", "संख्या"),
        "ask": ("sabse badi sankhya", "sabse bada number",
                "largest number", "biggest number"),
        "max_literals": 1,
        "en": {
            "answer": "There is no largest number — numbers "
                      "never end",
            "steps": [
                "Jitni badi sankhya socho, usme 1 jodte hi "
                "usse badi mil jayegi — isliye sabse badi "
                "sankhya hoti hi nahi.",
                "Short me: sankhyayen anant hai, sabse badi "
                "koi nahi.",
            ],
        },
        "roman": {
            "answer": "Koi sabse badi sankhya nahi hoti — "
                      "sankhyayen kabhi khatm nahi hoti",
            "steps": [
                "Jitni badi sankhya socho, usme 1 jodte hi "
                "usse badi mil jayegi — isliye sabse badi "
                "sankhya hoti hi nahi.",
                "Short me: sankhyayen anant hai, sabse badi "
                "koi nahi.",
            ],
        },
        "dev": {
            "answer": "कोई सबसे बड़ी संख्या नहीं होती — "
                      "संख्याएँ कभी ख़त्म नहीं होतीं",
            "steps": [
                "जितनी बड़ी संख्या सोचो, उसमें 1 जोड़ते ही "
                "उससे बड़ी मिल जाएगी — इसलिए सबसे बड़ी "
                "संख्या होती ही नहीं।",
                "संक्षेप में: संख्याएँ अनंत हैं, सबसे बड़ी "
                "कोई नहीं।",
            ],
        },
    },
    {
        "id": "smallest_number",
        "keywords": ("sankhya", "number", "संख्या"),
        "ask": ("sabse chhoti sankhya", "sabse chhota number",
                "smallest number"),
        "max_literals": 1,
        "en": {
            "answer": "There is no smallest number either — "
                      "negative numbers go on forever",
            "steps": [
                "Jitni chhoti sankhya socho, usme se 1 "
                "ghatate hi aur chhoti mil jayegi: −1, −2, "
                "−3, … bina ruke.",
                "Short me: sabse chhoti sankhya bhi koi "
                "nahi.",
            ],
        },
        "roman": {
            "answer": "Sabse chhoti sankhya bhi koi nahi — "
                      "negative sankhyayen anant tak jaati hai",
            "steps": [
                "Jitni chhoti sankhya socho, usme se 1 "
                "ghatate hi aur chhoti mil jayegi: −1, −2, "
                "−3, … bina ruke.",
                "Short me: sabse chhoti sankhya bhi koi "
                "nahi.",
            ],
        },
        "dev": {
            "answer": "सबसे छोटी संख्या भी कोई नहीं — "
                      "ऋणात्मक संख्याएँ अनंत तक जाती हैं",
            "steps": [
                "जितनी छोटी संख्या सोचो, उसमें से 1 घटाते "
                "ही और छोटी मिल जाएगी: −1, −2, −3, … बिना "
                "रुके।",
                "संक्षेप में: सबसे छोटी संख्या भी कोई नहीं।",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Layer 2: ADVICE — study / practice / exam behaviour.
# Triggers are study-behaviour phrases (never concept how-tos:
# "area kaise nikalte hai" carries none of them). The maths
# gate is applied in meta_result: an entry fires when the
# question carries a maths signal, or when it names no other
# subject at all (a bare "practice kaise karu?" inside a maths
# app is a maths question).
# ---------------------------------------------------------------------------

ADVICE = [
    {
        "id": "practice",
        "triggers": ("practice", "abhyas", "अभ्यास",
                     "taiyaari", "taiyari", "तैयारी", "तैय्यारी",
                     "prepare", "preparation", "padhai kaise",
                     "पढ़ाई कैसे", "seekhu", "seekhun", "सीखूँ",
                     "seekhne ka tareeka"),
        "en": {
            "answer": "Maths Practice — a little, but every day",
            "steps": [
                "Fix a daily slot of even 30–45 minutes: maths "
                "grows by daily practice, not by one long "
                "sitting just before the exam.",
                "For every topic, first study 2–3 solved "
                "examples, then solve 5–10 questions of the "
                "same type yourself — maths is learnt by "
                "doing, not by reading.",
                "Keep a mistake notebook: write down every "
                "question you got wrong and redo it after 2–3 "
                "days.",
                "Short me: roz thoda practice + galtiyon ko "
                "dobara — yahi asli taiyaari hai.",
            ],
        },
        "roman": {
            "answer": "Maths Practice — thoda, lekin roz",
            "steps": [
                "Roz ka ek fix samay rakho, chahe 30–45 minute "
                "hi ho: maths roz ke abhyas se badhta hai, "
                "exam se pehle ek lambi baithak se nahi.",
                "Har topic me pehle 2–3 solved examples dekho, "
                "phir usi type ke 5–10 sawal khud karo — maths "
                "padhne se nahi, karne se aata hai.",
                "Ek galti wali copy (mistake notebook) rakho: "
                "jo sawal galat ho use likho aur 2–3 din baad "
                "dobara karo.",
                "Short me: roz thoda practice + galtiyon ko "
                "dobara — yahi asli taiyaari hai.",
            ],
        },
        "dev": {
            "answer": "गणित का अभ्यास — थोड़ा, लेकिन रोज़",
            "steps": [
                "रोज़ का एक निश्चित समय रखिए, चाहे 30–45 मिनट "
                "ही हो: गणित रोज़ के अभ्यास से बढ़ता है, "
                "परीक्षा से पहले एक लंबी बैठक से नहीं।",
                "हर topic में पहले 2–3 हल किए हुए उदाहरण "
                "देखिए, फिर उसी प्रकार के 5–10 प्रश्न स्वयं "
                "कीजिए — गणित पढ़ने से नहीं, करने से आता है।",
                "एक ग़लती वाली कॉपी (mistake notebook) रखिए: "
                "जो प्रश्न ग़लत हो उसे लिखिए और 2–3 दिन बाद "
                "दोबारा कीजिए।",
                "संक्षेप में: रोज़ थोड़ा अभ्यास + ग़लतियों को "
                "दोबारा — यही असली तैयारी है।",
            ],
        },
    },
    {
        "id": "exam_solve",
        "triggers": ("exam me", "exam mein", "paper me",
                     "paper mein", "परीक्षा में", "पेपर में",
                     "paper kaise", "paper attempt",
                     "attempt karu", "attempt karun",
                     "exam strategy", "exam ki strategy",
                     "time manage", "samay kaise"),
        "en": {
            "answer": "In the Exam — easy questions first, "
                      "three rounds, revision at the end",
            "steps": [
                "First 5 minutes: read the whole paper and "
                "mark each question ✓ (sure), ? (doubtful) "
                "or ✗ (hard). Solve all the ✓ questions "
                "first — they secure your marks.",
                "Round 2: attempt the ? questions. Round 3: "
                "try the ✗ ones. Never let one hard question "
                "eat 20 minutes.",
                "Keep the last 10–15 minutes only for "
                "revision: check signs, units and numbers "
                "copied from the question — most silly marks "
                "are lost right there.",
                "Short me: aasan pehle, kathin baad me, "
                "aakhir me revision.",
            ],
        },
        "roman": {
            "answer": "Exam me — aasan sawal pehle, teen round, "
                      "aakhir me revision",
            "steps": [
                "Pehle 5 minute: poora paper padho aur har "
                "sawal par ✓ (pakka), ? (doubt) ya ✗ (kathin) "
                "ka nishan lagao. Pehle saare ✓ wale sawal "
                "karo — wahi tumhare pakke number hain.",
                "Round 2: ? wale sawal karo. Round 3: ✗ walo "
                "ko try karo. Ek kathin sawal ko 20 minute "
                "kabhi mat khane do.",
                "Aakhri 10–15 minute sirf revision ke liye "
                "rakho: sign, unit aur sawal se copy ki gayi "
                "sankhyaen check karo — sabse zyada number "
                "yahi bachte hain.",
                "Short me: aasan pehle, kathin baad me, "
                "aakhir me revision.",
            ],
        },
        "dev": {
            "answer": "परीक्षा में — आसान प्रश्न पहले, तीन "
                      "चरण, अंत में दोहराव",
            "steps": [
                "पहले 5 मिनट: पूरा पेपर पढ़िए और हर प्रश्न पर "
                "✓ (पक्का), ? (संदेह) या ✗ (कठिन) का निशान "
                "लगाइए। पहले सारे ✓ वाले प्रश्न कीजिए — वही "
                "आपके पक्के अंक हैं।",
                "चरण 2: ? वाले प्रश्न कीजिए। चरण 3: ✗ वालों "
                "को प्रयास कीजिए। एक कठिन प्रश्न को 20 मिनट "
                "कभी मत खाने दीजिए।",
                "अंतिम 10–15 मिनट सिर्फ़ दोहराव के लिए रखिए: "
                "चिह्न, इकाई और प्रश्न से उतारी गई संख्याएँ "
                "जाँचिए — सबसे ज़्यादा अंक यहीं बचते हैं।",
                "संक्षेप में: आसान पहले, कठिन बाद में, अंत "
                "में दोहराव।",
            ],
        },
    },
    {
        "id": "fear",
        "triggers": ("dar lagta", "darr lagta", "डर लगता",
                     "maths se dar", "गणित से डर",
                     "confusion hota", "confuse hota",
                     "bahut confuse", "sab confuse",
                     "confusion hai", "कन्फ़्यूज़",
                     "tough lagta",
                     "mushkil lagta", "मुश्किल लगता",
                     "boring lagta", "maths samajh nahi",
                     "ganit samajh nahi", "kuch samajh nahi",
                     "sab samajh nahi", "गणित समझ नहीं",
                     "कुछ समझ नहीं"),
        "en": {
            "answer": "Maths Fear — it usually means one weak "
                      "basics chapter, not a weak brain",
            "steps": [
                "Maths fear mostly comes from a gap in an "
                "earlier class — fractions, sign rules or "
                "tables. Find that one chapter and repair it; "
                "the fear drops fast.",
                "Start every day with 5 easy questions you "
                "CAN do. Confidence in maths is built by "
                "small wins, one at a time.",
                "Never compare yourself with the fastest "
                "student in class — compare only with your "
                "own last week.",
                "Short me: dar ko nahi, basics ki kami ko "
                "theek karo.",
            ],
        },
        "roman": {
            "answer": "Maths ka Dar — iska matlab aksar ek "
                      "kamzor basics chapter hai, kamzor "
                      "dimag nahi",
            "steps": [
                "Maths ka dar aksar pichhli class ki kisi "
                "kami se aata hai — bhinn (fractions), chihn "
                "ke niyam ya pahade. Us ek chapter ko dhoondo "
                "aur theek karo; dar khud kam ho jayega.",
                "Roz ki shuruaat 5 aasan sawalon se karo jo "
                "tumhe AATE hain. Maths me bharosa chhoti-"
                "chhoti jeeton se banta hai.",
                "Class ke sabse tez chhatra se apni tulna "
                "kabhi mat karo — tulna sirf apne pichhle "
                "hafte se karo.",
                "Short me: dar ko nahi, basics ki kami ko "
                "theek karo.",
            ],
        },
        "dev": {
            "answer": "गणित का डर — इसका मतलब अक्सर एक कमज़ोर "
                      "basics chapter है, कमज़ोर दिमाग़ नहीं",
            "steps": [
                "गणित का डर अक्सर पिछली कक्षा की किसी कमी से "
                "आता है — भिन्न, चिह्नों के नियम या पहाड़े। "
                "उस एक chapter को खोजिए और ठीक कीजिए; डर "
                "खुद कम हो जाएगा।",
                "रोज़ की शुरुआत 5 आसान प्रश्नों से कीजिए जो "
                "आपको आते हैं। गणित में भरोसा छोटी-छोटी "
                "जीतों से बनता है।",
                "कक्षा के सबसे तेज़ छात्र से अपनी तुलना कभी "
                "मत कीजिए — तुलना सिर्फ़ अपने पिछले हफ़्ते "
                "से कीजिए।",
                "संक्षेप में: डर को नहीं, basics की कमी को "
                "ठीक कीजिए।",
            ],
        },
    },
    {
        "id": "formulae",
        "triggers": ("formula yaad", "formulae yaad",
                     "formulas yaad", "sutra yaad", "सूत्र याद",
                     "formula ratna", "formule yaad",
                     "formula bhool", "sutra bhool"),
        "en": {
            "answer": "Formulae — don't memorise the line, "
                      "learn where it comes from",
            "steps": [
                "Learn the derivation once (how the formula "
                "is made). Then even if you forget it in the "
                "exam hall, you can rebuild it.",
                "For each formula, solve 3–4 questions using "
                "it on the SAME day you learn it — use makes "
                "it stick, rote (ratta) does not.",
                "Keep one formula page per chapter in your "
                "notebook and revise it for 5 minutes daily.",
                "Short me: samajh + istemal = pakki yaad.",
            ],
        },
        "roman": {
            "answer": "Formulae — line mat rato, ye seekho ki "
                      "formula banta kaise hai",
            "steps": [
                "Formula ki derivation (wo banta kaise hai) "
                "ek baar seekh lo. Phir exam hall me bhool "
                "bhi jao to use dobara bana sakte ho.",
                "Har formula ke 3–4 sawal USI din karo jis "
                "din use seekha — istemal se yaad pakki "
                "hoti hai, ratta lagane se nahi.",
                "Har chapter ki ek formula-page apni copy me "
                "rakho aur roz 5 minute use dohrao.",
                "Short me: samajh + istemal = pakki yaad.",
            ],
        },
        "dev": {
            "answer": "सूत्र — पंक्ति मत रटिए, यह सीखिए कि "
                      "सूत्र बनता कैसे है",
            "steps": [
                "सूत्र की derivation (वह बनता कैसे है) एक "
                "बार सीख लीजिए। फिर परीक्षा में भूल भी जाएँ "
                "तो उसे दोबारा बना सकते हैं।",
                "हर सूत्र के 3–4 प्रश्न उसी दिन कीजिए जिस "
                "दिन उसे सीखा — इस्तेमाल से याद पक्की होती "
                "है, रटने से नहीं।",
                "हर chapter की एक सूत्र-पृष्ठ अपनी कॉपी में "
                "रखिए और रोज़ 5 मिनट उसे दोहराइए।",
                "संक्षेप में: समझ + इस्तेमाल = पक्की याद।",
            ],
        },
    },
    {
        "id": "weak",
        "triggers": ("weak hu", "weak hoon", "weak hun",
                     "kamzor", "कमज़ोर", "कमजोर",
                     "maths nahi aata", "maths nahi aati",
                     "गणित नहीं आता", "ganit nahi aata",
                     "marks nahi aate", "marks kam aate",
                     "number nahi aate", "maths me zero",
                     "maths me weak"),
        "en": {
            "answer": "Weak in Maths — fix the base first, "
                      "marks follow on their own",
            "steps": [
                "'Weak' usually means a basics gap: tables "
                "(pahade), fractions, percentage and sign "
                "rules (+ − × ÷). Spend the first 2 weeks "
                "only on these — everything else gets "
                "easier.",
                "Do the class book's solved examples first, "
                "then its exercises. Don't jump straight to "
                "hard guides and sample papers.",
                "Clear every doubt the same day — teacher, "
                "friend or Ganitra. A doubt kept for a month "
                "becomes a weak chapter.",
                "Short me: neev (base) mazboot karo, marks "
                "khud badhenge.",
            ],
        },
        "roman": {
            "answer": "Maths me Weak — pehle neev (base) "
                      "theek karo, marks khud badhenge",
            "steps": [
                "'Weak' ka matlab aksar basics ki kami hai: "
                "pahade, bhinn (fractions), pratishat "
                "(percentage) aur chihn ke niyam (+ − × ÷). "
                "Pehle 2 hafte sirf inhi par do — baaki sab "
                "aasan hone lagega.",
                "Pehle class ki kitab ke solved examples "
                "karo, phir uske exercises. Seedha kathin "
                "guide ya sample paper par mat kudo.",
                "Har doubt usi din saaf karo — teacher, dost "
                "ya Ganitra se. Ek mahina rakha doubt ek "
                "kamzor chapter ban jata hai.",
                "Short me: neev (base) mazboot karo, marks "
                "khud badhenge.",
            ],
        },
        "dev": {
            "answer": "गणित में कमज़ोर — पहले नींव (base) "
                      "ठीक कीजिए, अंक खुद बढ़ेंगे",
            "steps": [
                "'कमज़ोर' का मतलब अक्सर basics की कमी है: "
                "पहाड़े, भिन्न, प्रतिशत और चिह्नों के नियम "
                "(+ − × ÷)। पहले 2 हफ़्ते सिर्फ़ इन्हीं पर "
                "दीजिए — बाकी सब आसान होने लगेगा।",
                "पहले कक्षा की पुस्तक के हल किए उदाहरण "
                "कीजिए, फिर उसके अभ्यास। सीधे कठिन guide या "
                "sample paper पर मत कूदिए।",
                "हर doubt उसी दिन साफ़ कीजिए — शिक्षक, दोस्त "
                "या Ganitra से। एक महीना रखा doubt एक कमज़ोर "
                "chapter बन जाता है।",
                "संक्षेप में: नींव मज़बूत कीजिए, अंक खुद "
                "बढ़ेंगे।",
            ],
        },
    },
    {
        "id": "revision",
        "triggers": ("revision", "revise", "रिवीजन",
                     "दोहराना", "dohrau", "dohrana",
                     "revision kaise"),
        "en": {
            "answer": "Revision — revise in rounds of 1 day, "
                      "1 week, 1 month",
            "steps": [
                "Revise every topic three times: after 1 "
                "day, after 1 week, after 1 month. This "
                "spaced revision is what moves things into "
                "long memory.",
                "Revise by DOING, not by reading: pick 3 old "
                "questions per topic and solve them fresh.",
                "Just before the exam, revise from your "
                "mistake notebook and formula pages — not "
                "from the whole book again.",
                "Short me: 1 din, 1 hafta, 1 mahina — teen "
                "baar dohrao.",
            ],
        },
        "roman": {
            "answer": "Revision — 1 din, 1 hafta, 1 mahina ke "
                      "round me dohrao",
            "steps": [
                "Har topic ko teen baar dohrao: 1 din baad, "
                "1 hafte baad, 1 mahine baad. Yahi spaced "
                "revision cheezon ko lambi yaad me bhejta "
                "hai.",
                "Revision padh kar nahi, KAR ke karo: har "
                "topic ke 3 purane sawal uthao aur naye sire "
                "se hal karo.",
                "Exam se theek pehle apni galti wali copy "
                "aur formula pages se dohrao — poori kitab "
                "dobara mat kholo.",
                "Short me: 1 din, 1 hafta, 1 mahina — teen "
                "baar dohrao.",
            ],
        },
        "dev": {
            "answer": "Revision (दोहराव) — 1 दिन, 1 हफ़्ता, "
                      "1 महीने के चरण में दोहराइए",
            "steps": [
                "हर topic को तीन बार दोहराइए: 1 दिन बाद, 1 "
                "हफ़्ते बाद, 1 महीने बाद। यही spaced revision "
                "चीज़ों को लंबी याद में भेजता है।",
                "Revision पढ़कर नहीं, करके कीजिए: हर topic "
                "के 3 पुराने प्रश्न उठाइए और नए सिरे से हल "
                "कीजिए।",
                "परीक्षा से ठीक पहले अपनी ग़लती वाली कॉपी "
                "और सूत्र-पृष्ठों से दोहराइए — पूरी पुस्तक "
                "दोबारा मत खोलिए।",
                "संक्षेप में: 1 दिन, 1 हफ़्ता, 1 महीना — "
                "तीन बार दोहराइए।",
            ],
        },
    },
    {
        "id": "silly_mistakes",
        "triggers": ("silly mistake", "silly galti",
                     "गलतियाँ", "गलतियां", "galtiyan",
                     "galti ho jati", "galti ho jaati",
                     "careless", "chhoti galti", "छोटी गलती",
                     "galti kam"),
        "en": {
            "answer": "Silly Mistakes — almost all of them "
                      "are just 3 habits",
            "steps": [
                "The big three: sign errors (+/−), copying a "
                "wrong number from the question, and "
                "skipping steps in a hurry. Write every step "
                "— marks leak at mental jumps.",
                "After solving, give 20 seconds to checking: "
                "does the answer's size and sign make sense? "
                "If you can, put the answer back into the "
                "question.",
                "Keep a list of YOUR repeated mistakes and "
                "read it before every test.",
                "Short me: har step likho, aakhir me 20 "
                "second check karo.",
            ],
        },
        "roman": {
            "answer": "Silly Mistakes — zyadatar ye sirf 3 "
                      "aadatein hain",
            "steps": [
                "Sabse badi teen: sign ki galti (+/−), sawal "
                "se galat sankhya copy karna, aur jaldi me "
                "step chhod dena. Har step likho — number "
                "dimag ke jumps par hi kat te hain.",
                "Hal karne ke baad 20 second checking ko do: "
                "kya jawab ka size aur sign samajh me aata "
                "hai? Ho sake to jawab ko sawal me wapas "
                "rakh kar dekho.",
                "Apni dohraayi jaane wali galtiyon ki list "
                "banao aur har test se pehle use padho.",
                "Short me: har step likho, aakhir me 20 "
                "second check karo.",
            ],
        },
        "dev": {
            "answer": "Silly Mistakes — ज़्यादातर ये सिर्फ़ 3 "
                      "आदतें हैं",
            "steps": [
                "सबसे बड़ी तीन: चिह्न की ग़लती (+/−), प्रश्न "
                "से ग़लत संख्या उतारना, और जल्दबाज़ी में "
                "चरण छोड़ देना। हर चरण लिखिए — अंक दिमाग़ "
                "की छलांगों पर ही कटते हैं।",
                "हल करने के बाद 20 सेकंड जाँच को दीजिए: "
                "क्या उत्तर का आकार और चिह्न समझ में आता "
                "है? हो सके तो उत्तर को प्रश्न में वापस "
                "रखकर देखिए।",
                "अपनी दोहराई जाने वाली ग़लतियों की सूची "
                "बनाइए और हर test से पहले उसे पढ़िए।",
                "संक्षेप में: हर चरण लिखिए, अंत में 20 "
                "सेकंड जाँच कीजिए।",
            ],
        },
    },
    {
        "id": "speed",
        "triggers": ("fast kaise", "tez kaise", "तेज़ कैसे",
                     "calculation slow", "calculation fast",
                     "speed badha", "speed kaise",
                     "jaldi solve", "slow hu", "slow hoon",
                     "bahut slow", "slow hai", "slow hota",
                     "slow hoti", "गति कैसे", "time lagta hai"),
        "en": {
            "answer": "Calculation Speed — accuracy first, "
                      "speed follows on its own",
            "steps": [
                "Learn tables up to 20 and squares up to 25 "
                "by heart — these two alone remove most slow "
                "moments.",
                "Practise 10 mixed calculations daily with "
                "a timer, but never by skipping steps: a "
                "fast wrong answer still earns zero.",
                "Use splitting shortcuts (99 × 7 = 100×7 − 7) "
                "only after the normal method is fully "
                "pakka.",
                "Short me: pahade pakke karo, speed khud "
                "aayegi.",
            ],
        },
        "roman": {
            "answer": "Calculation Speed — pehle sahi, speed "
                      "khud peeche aati hai",
            "steps": [
                "20 tak pahade aur 25 tak varg (squares) "
                "muh-zabani yaad karo — sirf ye do cheezein "
                "zyadatar susti (slowness) khatm kar deti "
                "hain.",
                "Roz 10 mile-jule hisaab timer ke saath "
                "karo, lekin step chhod kar kabhi nahi: tez "
                "galat jawab par bhi zero hi milta hai.",
                "Todne wale shortcut (99 × 7 = 100×7 − 7) "
                "tabhi use karo jab aam tareeka poori tarah "
                "pakka ho jaye.",
                "Short me: pahade pakke karo, speed khud "
                "aayegi.",
            ],
        },
        "dev": {
            "answer": "गणना की गति — पहले सही, गति खुद पीछे "
                      "आती है",
            "steps": [
                "20 तक पहाड़े और 25 तक वर्ग मुँह-ज़बानी याद "
                "कीजिए — सिर्फ़ ये दो चीज़ें ज़्यादातर "
                "सुस्ती ख़त्म कर देती हैं।",
                "रोज़ 10 मिले-जुले हिसाब timer के साथ कीजिए, "
                "लेकिन चरण छोड़कर कभी नहीं: तेज़ ग़लत उत्तर "
                "पर भी शून्य ही मिलता है।",
                "तोड़ने वाले shortcut (99 × 7 = 100×7 − 7) "
                "तभी उपयोग कीजिए जब आम तरीका पूरी तरह "
                "पक्का हो जाए।",
                "संक्षेप में: पहाड़े पक्के कीजिए, गति खुद "
                "आएगी।",
            ],
        },
    },
]

# Extra context words for the wide net's WHO branch only:
# famous maths people / maths-person words that mark a
# who-question as maths-related even when the person is not
# a curated entry ("Euler kaun the?"). NOT part of the
# advice gate's maths signal — a physics-flavoured advice
# ask must not pass on "newton" alone.
_WHO_CONTEXT_WORDS = (
    "euler", "gauss", "newton", "leibniz", "mathematician",
    "ganitagya", "गणितज्ञ",
)

# Broad advice shapes for the wide net (is_meta_shaped):
# study-behaviour words that, WITH a maths signal, mark a
# question as maths-meta even when no curated entry matches.
_ADVICE_SHAPE_WORDS = (
    "practice", "abhyas", "अभ्यास", "taiyaari", "तैयारी",
    "prepare", "revision", "revise", "yaad", "याद", "weak",
    "kamzor", "कमज़ोर", "dar lagta", "डर लगता", "silly",
    "mistake", "गलती", "exam", "परीक्षा", "paper",
    "confuse", "marks",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _result(kind, entry, flavour):
    text = entry[flavour]
    return {
        "type": "Maths fact" if kind in ("history", "fact")
                else "Study advice",
        "op": f"{kind}_{entry['id']}",
        "answer": text["answer"],
        "steps": list(text["steps"]),
        "fallback": True,
        "fallback_kind": kind,
        "meta_id": entry["id"],
    }


def _with_why(res, entry, q, flavour):
    """Wave 183: an entry carrying a "why" line (today
    only zero) adds it — once, just before the closing
    gist line — when the student's ask also asks WHY
    ("0 kisne banaya aur kyon", "जीरो क्यों बनाया था").
    A plain who-ask keeps the card byte-identical to
    before, which the Wave 177 pins rely on."""
    why = entry.get("why")
    if not why or not _has_why_shape(q):
        return res
    line = why[flavour]
    steps = res["steps"]
    if line not in steps:
        res["steps"] = steps[:-1] + [line] + steps[-1:]
    return res


# Wave 185: content-ask shapes for the advice-yield guard
# in meta_result — the shapes that say "answer THIS maths
# thing" (a value, a meaning, a what-is), as opposed to
# asking how to study or attempt. Consulted only together
# with a curated HISTORY keyword hit.
_CONTENT_ASK_SHAPES = (
    "kya hota", "kya hai", "kitna hota", "kitni hoti",
    "kitna hai", "ka maan", "maan kitna", "ka matlab",
    "ki value", "ka value", "value kya",
    "क्या होता", "क्या है", "कितना होता", "का मान",
)


def meta_result(question, flavour=None):
    """The curated maths-meta answer for `question`, or
    None. `flavour` is fallback.py's per-question flavour
    ("en" / "roman" / "dev"); when omitted it is derived
    from the question's script the same way fallback does.
    """
    q = str(question or "").lower()
    if not q.strip():
        return None
    if _has_fresh_problem(q):
        return None  # a real problem rides along; not ours
    if flavour not in ("en", "roman", "dev"):
        flavour = "dev" if any("ऀ" <= ch <= "ॿ" for ch in q) \
            else "en"
    # The app's general flavour detector misses pure
    # who-questions ("kisne banaya tha?" carries none of its
    # Hindi markers), so they would be answered in English
    # although the student plainly wrote Hinglish. Inside
    # this layer only: a Roman-Hindi who marker upgrades an
    # "en" flavour to "roman". Genuine English asks carry
    # none of these words, so they are untouched.
    if flavour == "en" and any(m in q for m in (
            "kisne", "kaun tha", "kaun thi", "kaun the",
            # Wave 177: the FACT layer's Hinglish asks carry
            # the same plain markers.
            "sabse", "kitne", "kitna", "kaun sa", "kya hai",
            "kya hota", "hote hai", "hota hai",
            "kaha se", "kahan se", "shabd", "naam",
            # Wave 183: contribution / zero-why asks are
            # Hinglish too ("ne kya kiya tha", "kyon
            # banaya") and must not be answered in English.
            "kya kiya", "kya diya", "yogdan", "yogdaan",
            "baare me", "bare me", "mashhoor", "mashoor",
            "kyon", "kyun", "banaya")):
        flavour = "roman"
    # History first: a who-shaped ask about a curated
    # topic/person is answered by the FACT layer, before
    # any concept card can serve the WHAT instead.
    if _has_who_shape(q):
        for entry in HISTORY:
            if _entry_hit(q, entry):
                return _with_why(
                    _result("history", entry, flavour),
                    entry, q, flavour)
    # Wave 183: CONTRIBUTION asks — "X ne kya kiya tha",
    # "What did X do?", "X ka yogdan kya hai", "X ke baare
    # me batao". The person entries' steps ARE their
    # contributions, so the same card answers both shapes;
    # the double gate (contribution phrase + curated
    # keyword) plus the fresh-problem veto above keep real
    # problems and name-dropping word problems out.
    if _has_contribution_shape(q):
        for entry in HISTORY:
            if _entry_hit(q, entry):
                return _result("history", entry, flavour)
    # Wave 183: zero-ORIGIN asks with no who marker —
    # "zero kyon banaya gaya tha", "जीरो क्यों बनाया था"
    # (spoken form, extra clauses and all). Only the zero
    # entry is consulted here, on its own keyword, and a
    # why-bearing ask gets the why line via _with_why.
    if _has_origin_shape(q):
        for entry in HISTORY:
            if entry["id"] == "zero" and _entry_hit(q, entry):
                return _with_why(
                    _result("history", entry, flavour),
                    entry, q, flavour)
    # Wave 177: the FACT layer — non-who maths GK
    # (superlatives, counting facts, word origins). Same
    # position for the same reason: these asks are not
    # computations, and the layers below either fragment-
    # solve them or collapse them to the not-found line.
    for entry in FACTS:
        if _fact_hit(q, entry):
            return _result("fact", entry, flavour)
    # Advice: study-behaviour triggers, maths-gated. A
    # difference/comparison ask ("AP aur GP me fark") is a
    # concept ask owned by the topics library's difference
    # cards — never advice, whatever trigger word it carries
    # (a student "confused between AP and GP" wants the
    # difference, not fear counselling).
    if any(m in q for m in ("fark", "antar", "difference",
                            "versus", " vs ")):
        return None
    # Wave 185: advice also yields to an EMBEDDED CONTENT
    # ask. "exam me pucha gaya tha ki pi ka maan kitna
    # hota hai" is a pi-value question wearing exam dress
    # — the exam_solve trigger ("exam me") fired on the
    # dress and served exam strategy for it. When a
    # curated topic is named AND a content-ask shape is
    # present, the ask is the content: return None here
    # and let the concept layers answer it. A genuine
    # advice ask names no curated topic with a value /
    # what-is shape ("exam me darr lagta hai, taiyaari
    # kaise karu"), so it is untouched.
    if any(_entry_hit(q, e) for e in HISTORY) and any(
            s in q for s in _CONTENT_ASK_SHAPES):
        return None
    maths_ok = _has_maths_signal(q) \
        or not _names_other_subject(q)
    # Wave 146: a question carrying MCQ options is a problem
    # to solve, never an advice ask.
    if sum(q.count(m) for m in ("(a)", "(b)", "(c)", "(d)")) >= 2:
        maths_ok = False
    if maths_ok:
        for entry in ADVICE:
            if any(_trigger_hit(q, t) for t in entry["triggers"]):
                return _result("advice", entry, flavour)
    return None


def is_meta_shaped(question):
    """True when the question is a WHO-shaped or
    ADVICE-shaped MATHS question (curated hit or not).
    fallback.py uses this for exactly one decision: such a
    question that the curated layers miss classifies as
    "guide" (which the AI chain may answer) instead of
    "gibberish" (which collapses unseen). Non-maths shapes
    never qualify: a who shape needs a curated keyword or a
    maths signal, and an advice shape needs a maths signal —
    so "Who is the president of India?" and "History ki
    taiyaari kaise karu?" stay exactly where they were."""
    q = str(question or "").lower()
    if not q.strip() or _has_fresh_problem(q):
        return False
    # Wave 183: a CONTRIBUTION shape ("Euler ne kya kiya
    # tha", "What did Leibniz contribute?") is the same
    # family as a who shape — with the same maths anchor
    # requirement, so a non-maths person ("Shakespeare ne
    # kya kiya tha", no anchor) stays out exactly as before.
    if (_has_who_shape(q) or _has_contribution_shape(q)) and (
            _has_maths_signal(q)
            or any(w in q for w in _WHO_CONTEXT_WORDS)
            or any(_entry_hit(q, e) for e in HISTORY)):
        return True
    if _has_maths_signal(q) and any(
            _trigger_hit(q, w) for w in _ADVICE_SHAPE_WORDS):
        return True
    return False


# Wave 177: the wider KNOWLEDGE net — the mirror of
# is_meta_shaped for the whole maths-knowledge class (who /
# when / why / what-is ABOUT mathematics: its history,
# people, definitions, number facts, word origins).
# fallback.py consults it at the same decision point: a
# knowledge-shaped question the curated entries miss
# ("abacus kya hota hai", "angle kya hota hai", "vedic
# maths kya hota hai") is a genuine question for the AI
# chain, not gibberish — while a computation shape (fresh
# problem veto) and non-maths topics stay out, exactly as
# in is_meta_shaped.
_KNOWLEDGE_SHAPE_PHRASES = (
    "kya hai", "kya hota", "kya hote", "kya hoti", "matlab",
    "what is", "what does", "meaning", "kaha se aaya",
    "kahan se aaya", "kab hua", "kab bana", "sabse",
    "kitne", "kitna", "kaun", "kisne", "kab", "kyu",
    "kyon", "किसने", "कौन", "कब", "क्यों", "क्या", "मतलब",
    "सबसे", "कितने", "कितना",
    # Wave 185: ORIGIN asks in spoken dress — "abacus ka
    # avishkar kahan hua tha" carries its shape in
    # "avishkar" + "kahan hua", neither of which was a
    # shape here, so the ask classified as gibberish.
    # The topic gate below is unchanged: a non-maths
    # invention ask ("telephone ka avishkar kisne kiya")
    # still has no maths topic word and stays out.
    "kahan hua", "kahan hui", "kahan bana", "kahan bani",
    "kahan se hua", "kahan se hui", "avishkar",
    "कहाँ हुआ", "कहाँ बना", "आविष्कार",
)
_KNOWLEDGE_SHAPE_EN = re.compile(
    r"\b(who|why|when|what|which|whose|whom|largest|"
    r"smallest|biggest|"
    r"how many|invent\w*|discover\w*|origin)\b")
_KNOWLEDGE_TOPIC_WORDS = _MATHS_SIGNALS + (
    "zero", "shunya", "शून्य",
    # Wave 183: the spoken zero forms, as in the zero
    # entry's keywords — a voice-typed "जीरो" question is
    # a maths-knowledge question even when nothing else
    # in it matches.
    "जीरो", "ज़ीरो", "jeero",
    # Wave 185: the remaining voice spellings ("jero",
    # as on the zero entry) and "aljebra", so their asks
    # are knowledge-shaped even before an entry is added.
    "jero", "aljebra",
    "prime", "composite",
    "abhaajya", "अभाज्य", "infinity", "anant", "अनंत",
    "roman", "crore", "lakh", "million", "billion",
    "dozen", "gross", "decimal", "angle", "kon", "कोण",
    "triangle", "tribhuj", "त्रिभुज", "fibonacci",
    "calculator", "abacus", "vedic", "euler", "gauss",
    "newton", "archimedes", "leibniz",
    # Wave 185: more surnames that name famous
    # mathematicians and nothing else in a school
    # context — "Hilbert ne kya kiya tha" has no curated
    # entry, and without an anchor here it classified as
    # gibberish although Euler/Leibniz asks (anchored by
    # the names above) reached the AI legs.
    "hilbert", "riemann", "cantor", "noether",
    "poincare", "hardy",
    "symbol", "sign",
    "chinh", "bodmas", "pemdas", "sankhya", "संख्या",
    "ank", "अंक", "digit", "number", "algebra",
    "geometry", "trigonometry", "theorem", "factorial",
    "fraction", "percent", "ratio", "anupat", "circle",
    "vritt", "वृत्त", "square", "cube", "root", "power",
    "ganitagya", "mathematician", "itihas", "history",
    "janak", "जनक", "pita", "father",
)


def is_knowledge_shaped(question):
    """True when the question is a maths-KNOWLEDGE question
    (curated hit or not): a who/when/why/what-is shape about
    a maths topic. fallback.py uses it alongside
    is_meta_shaped for the gibberish-vs-guide decision, so
    the class always reaches the AI chain when the curated
    layers miss it."""
    q = str(question or "").lower()
    if not q.strip() or _has_fresh_problem(q):
        return False
    # Wave 183: a contribution shape ("Brahmagupta ne kya
    # diya tha") is a knowledge shape in its own right —
    # with the topic gate below unchanged, so it cannot
    # widen the net beyond maths topics/people.
    shape = _has_who_shape(q) \
        or _has_contribution_shape(q) \
        or _KNOWLEDGE_SHAPE_EN.search(q) is not None \
        or any(w in q for w in _KNOWLEDGE_SHAPE_PHRASES)
    if not shape:
        return False
    return any(w in q for w in _KNOWLEDGE_TOPIC_WORDS) \
        or any(_entry_hit(q, e) for e in HISTORY) \
        or any(_fact_hit(q, e) for e in FACTS)


# Wave 185: the FOLLOW-UP net — conversational fragments
# that plainly continue a maths conversation ("iska
# example do", "phir se samjhao", "detail me batao").
# They carry no topic of their own, so neither wide net
# above can see them; measured by the letter test they
# were "gibberish" ("iska example do": iska + example are
# both outside the known-word list), and the gibberish
# bucket never reaches the AI legs — although in the
# live chat, with the previous answer as context, the AI
# chain is exactly who should field them (its sibling
# fragments — "ye wala phir se samjhao", "iska answer
# step me chahiye" — already reach it, because their
# words happen to be known). fallback.py consults this
# net at the same decision point as the two nets above.
# The markers are whole request phrases, so letter-soup
# cannot trip them; a fresh problem vetoes, as in the
# other nets.
_FOLLOWUP_MARKERS = (
    "example do", "example batao", "example de do",
    "ek example", "udaharan do", "udaharan batao",
    "उदाहरण दो", "उदाहरण बताओ",
    "phir se samjhao", "phir se batao", "phir samjhao",
    "dobara samjhao", "dobara batao",
    "फिर से समझाओ", "फिर से बताओ",
    "detail me samjhao", "detail me batao",
    "vistar se batao", "vistar se samjhao", "विस्तार से",
    "step me batao", "step by step", "step se batao",
    "ulta batao", "iska ulta", "uska ulta", "usi ka ulta",
)


def is_followup_shaped(question):
    """True when the message is a follow-up / elaboration
    request continuing a maths conversation (see the
    _FOLLOWUP_MARKERS note). fallback.py uses it for the
    same gibberish-vs-guide decision as the nets above."""
    q = str(question or "").lower()
    if not q.strip() or _has_fresh_problem(q):
        return False
    return any(m in q for m in _FOLLOWUP_MARKERS)


# Wave 226: the DEFINITION net — "Define a hyperbola.",
# "X ki paribhasha batao", "X ka matlab kya hai". The
# knowledge net above demands a who/when/why/what-is shape
# PLUS a curated topic word, so a plain definition ask for
# a concept outside the topic list ("hyperbola", "ellipse",
# "parabola", "relation", "sequence"...) measured as
# GIBBERISH by the letter test — every word unknown — and
# the gibberish bucket never reaches the AI legs: the
# question died on the canned line even in production
# (Suraj's P0, 27 Nov 2026: definition questions must
# ALWAYS be answered). The definition shape is its own
# anchor — the request phrase IS the intent, exactly like
# the follow-up net's markers — so no topic gate is
# demanded; letter-soup cannot trip a whole-phrase marker,
# and a fresh problem vetoes, as in the nets above.
# fallback.py consults this net at the same gibberish-vs-
# guide decision point.
_DEFINITION_LEAD = re.compile(
    r"^\s*(?:define|definition\s+of)\b")


def is_definition_shaped(question):
    """True when the message is plainly a definition ask:
    it opens with "define" / "definition of", or carries a
    paribhasha / ka-matlab marker (Roman or Devanagari)."""
    raw = str(question or "")
    q = raw.lower()
    if not q.strip() or _has_fresh_problem(q):
        return False
    if _DEFINITION_LEAD.search(q):
        return True
    if "paribhasha" in q or "परिभाषा" in raw:
        return True
    if re.search(r"\b(?:ka|ki)\s+matlab\b", q) \
            or "का मतलब" in raw or "की परिभाषा" in raw:
        return True
    return False


__all__ = ["HISTORY", "FACTS", "ADVICE", "meta_result",
           "is_meta_shaped", "is_knowledge_shaped",
           "is_followup_shaped", "is_definition_shaped",
           "meta_variation"]


# ---------------------------------------------------------------------------
# Wave 178: repeat-ask VARIATIONS for the knowledge class
# (Suraj's standing rule, 19 Nov 2026 ~09:52 IST — the
# same ask again must never be the same copy-paste).
#
# repeat.py owns the counting and the warm opener; this
# module owns the extra words, like the base cards:
#   "again" (2nd ask): one fresh related detail.
#   "third" (3rd+ ask): a deeper fact and/or a practice
#       step the student can actually do.
# Authored lines exist for the most-asked entries; every
# other entry falls back to its KIND's generic pool —
# lines written to stay true no matter which entry of
# that kind they ride on (memory tricks, self-tests,
# universal study tips — never a claim about the entry
# itself). Rotation advances with the ask-count, so the
# 3rd ask is not the 2nd ask's card and the 4th is not
# the 3rd's either.
# ---------------------------------------------------------------------------

META_VARIATIONS = {
    ("history", "zero"): {
        "en": {
            "again": [
                "One more detail: zero travelled from India "
                "through Arabic books to Europe — that is "
                "why old European books call our numerals "
                "'Arabic numerals', though the system is "
                "Indian."],
            "third": [
                "Try this once: write 1005 without using 0 "
                "at all, the way the Romans had to. In one "
                "minute you will feel why zero changed "
                "maths forever."],
        },
        "roman": {
            "again": [
                "Ek aur baat: zero India se Arabi kitabon ke "
                "raaste Europe pahuncha — isiliye purani "
                "European kitabein hamare ankon ko 'Arabic "
                "numerals' kehti hai, halanki ye system "
                "Indian hai."],
            "third": [
                "Ek baar ye karke dekho: 1005 ko bina 0 "
                "istemal kiye likho, jaise Romans ko likhna "
                "padta tha. Ek minute me samjhoge ki zero "
                "ne maths hamesha ke liye kyun badal diya."],
        },
        "dev": {
            "again": [
                "एक और बात: zero India से Arabi किताबों के "
                "रास्ते Europe पहुँचा — इसीलिए पुरानी European "
                "किताबें हमारे अंकों को 'Arabic numerals' "
                "कहती हैं, हालाँकि ये system Indian है।"],
            "third": [
                "एक बार ये करके देखो: 1005 को बिना 0 इस्तेमाल "
                "किए लिखो, जैसे Romans को लिखना पड़ता था। "
                "एक minute में समझोगे कि zero ने maths "
                "हमेशा के लिए क्यों बदल दिया।"],
        },
    },
    ("history", "pi"): {
        "en": {
            # Wave 198 (audit 20 Nov): the "measuring
            # circles" method claim dropped — Aryabhata's
            # method is not recorded as circle-measuring.
            "again": [
                "One more detail: Aryabhata's value 3.1416 "
                "was so accurate that it stayed in use for "
                "centuries."],
            "third": [
                "Now measure pi yourself: wrap a thread "
                "around any round plate, measure the thread "
                "and the plate's width (diameter), and "
                "divide. You will land near 3.14 every "
                "single time — that is pi, in your own "
                "hands."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Aryabhata ki value 3.1416 "
                "itni sateek thi ki sadion tak chalti "
                "rahi."],
            "third": [
                "Ab pi ko khud naapo: kisi gol thali ke "
                "chaaron or dhaga lapeto, dhage ki lambai "
                "aur thali ki chaudi (diameter) naapo, aur "
                "bhaag do. Har baar 3.14 ke aas-paas hi "
                "aayega — yahi pi hai, tumhare apne haathon "
                "me."],
        },
        "dev": {
            "again": [
                "एक और बात: Aryabhata की value 3.1416 "
                "इतनी सटीक थी कि सदियों तक चलती रही।"],
            "third": [
                "अब pi को ख़ुद नापो: किसी गोल थाली के चारों "
                "ओर धागा लपेटो, धागे की लंबाई और थाली की "
                "चौड़ाई (diameter) नापो, और भाग दो। हर बार "
                "3.14 के आस-पास ही आएगा — यही pi है, "
                "तुम्हारे अपने हाथों में।"],
        },
    },
    ("history", "algebra"): {
        "en": {
            "again": [
                "One more detail: Al-Khwarizmi's book also "
                "gave us the word 'algorithm' — it comes "
                "from the Latin form of his own name."],
            "third": [
                "A small practice: 'al-jabr' meant restoring "
                "— moving a minus term to the other side to "
                "make it plus. Solve x − 4 = 10 by exactly "
                "that move, and you have done al-jabr "
                "yourself."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Al-Khwarizmi ki kitab se hi "
                "hame 'algorithm' shabd bhi mila — ye unke "
                "hi naam ke Latin roop se bana hai."],
            "third": [
                "Ek chhoti practice: 'al-jabr' ka matlab tha "
                "— jodna, minus wale pad ko dusri taraf le "
                "jakar plus banana. x − 4 = 10 ko bilkul "
                "usi chaal se solve karo — tumne khud "
                "al-jabr kar liya."],
        },
        "dev": {
            "again": [
                "एक और बात: Al-Khwarizmi की किताब से ही हमें "
                "'algorithm' शब्द भी मिला — ये उनके ही नाम "
                "के Latin रूप से बना है।"],
            "third": [
                "एक छोटी practice: 'al-jabr' का मतलब था — "
                "जोड़ना, minus वाले पद को दूसरी तरफ़ ले जाकर "
                "plus बनाना। x − 4 = 10 को बिल्कुल उसी चाल "
                "से solve करो — तुमने ख़ुद al-jabr कर "
                "लिया।"],
        },
    },
    ("history", "euclid"): {
        "en": {
            "again": [
                "One more detail: Euclid's book 'Elements' "
                "stayed the world's geometry textbook for "
                "about 2,000 years — among the most reprinted "
                "books in history."],
            "third": [
                "Try Euclid's way once: state one geometry "
                "fact you know, then ask 'why is it true?' "
                "three times in a row. That chain of whys "
                "is exactly how Elements is built."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Euclid ki kitab 'Elements' "
                "lagbhag 2,000 saal tak duniya ki geometry "
                "ki textbook rahi — itihaas ki sabse zyada "
                "chhapi kitabon me se ek."],
            "third": [
                "Ek baar Euclid ke tareeke se socho: ek "
                "geometry ki baat lo jo tumhe aati hai, "
                "phir teen baar pucho 'ye sach kyun hai?' "
                "Whyon ki yahi chain Elements ki buniyaad "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Euclid की किताब 'Elements' लगभग "
                "2,000 साल तक दुनिया की geometry की textbook "
                "रही — इतिहास की सबसे ज़्यादा छपी किताबों "
                "में से एक।"],
            "third": [
                "एक बार Euclid के तरीके से सोचो: एक geometry "
                "की बात लो जो तुम्हें आती है, फिर तीन बार "
                "पूछो 'ये सच क्यों है?' क्यों की यही chain "
                "Elements की बुनियाद है।"],
        },
    },
    ("history", "calculus"): {
        "en": {
            "again": [
                "One more detail: Newton and Leibniz even "
                "fought over who was first — historians now "
                "credit both, because they truly worked "
                "independently, with different notations."],
            "third": [
                "A practice thought: calculus is the maths "
                "of things that CHANGE — speed from a "
                "speedometer, water filling a tank. Name "
                "one changing thing around you right now; "
                "that is a calculus question waiting."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Newton aur Leibniz me ispar "
                "jhagda bhi hua ki pehle kisne banaya — aaj "
                "itihaaskaar dono ko shrey dete hai, kyunki "
                "dono ne sach me alag-alag, apne-apne "
                "notation se kaam kiya tha."],
            "third": [
                "Ek practice soch: calculus BADALTI cheezon "
                "ka maths hai — speedometer ki speed, tank "
                "me bharta paani. Abhi apne aas-paas ki ek "
                "badalti cheez ka naam lo; wahi ek calculus "
                "sawal banne wala hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Newton और Leibniz में इसपर झगड़ा "
                "भी हुआ कि पहले किसने बनाया — आज इतिहासकार "
                "दोनों को श्रेय देते हैं, क्योंकि दोनों ने "
                "सच में अलग-अलग, अपने-अपने notation से काम "
                "किया था।"],
            "third": [
                "एक practice सोच: calculus बदलती चीज़ों का "
                "maths है — speedometer की speed, tank में "
                "भरता पानी। अभी अपने आस-पास की एक बदलती "
                "चीज़ का नाम लो; वही एक calculus सवाल बनने "
                "वाला है।"],
        },
    },
    ("history", "aryabhata"): {
        "en": {
            "again": [
                "One more detail: Aryabhata also explained "
                "that the Earth rotates on its axis — more "
                "than a thousand years before it was "
                "accepted in Europe."],
            "third": [
                "A fact to carry away: he wrote the "
                "Aryabhatiya at just 23 years of age. Big "
                "work does not wait for old age — it waits "
                "for daily practice."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Aryabhata ne ye bhi bataya tha "
                "ki Prithvi apni dhuri par ghoomti hai — "
                "Europe me ye baat maanne se ek hazaar saal "
                "se bhi pehle."],
            "third": [
                "Ek baat saath le jao: unhone Aryabhatiya "
                "sirf 23 saal ki umar me likhi thi. Bada "
                "kaam budhape ka intezaar nahi karta — roz "
                "ki practice ka karta hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Aryabhata ने ये भी बताया था कि "
                "पृथ्वी अपनी धुरी पर घूमती है — Europe में "
                "ये बात मानने से एक हज़ार साल से भी पहले।"],
            "third": [
                "एक बात साथ ले जाओ: उन्होंने Aryabhatiya "
                "सिर्फ़ 23 साल की उम्र में लिखी थी। बड़ा "
                "काम बुढ़ापे का इंतज़ार नहीं करता — रोज़ "
                "की practice का करता है।"],
        },
    },
    ("history", "brahmagupta"): {
        "en": {
            "again": [
                "One more detail: Brahmagupta also worked on "
                "quadratic equations and gave a famous rule "
                "for the area of a cyclic quadrilateral — "
                "Class 10's Heron-style area work has roots "
                "in his writing."],
            "third": [
                "Try his zero rules yourself: what is 5 + 0, "
                "5 − 0, 5 × 0? Easy — but notice that 5 ÷ 0 "
                "still has no answer even today. Brahmagupta "
                "wrestled with exactly that one."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Brahmagupta ne quadratic "
                "equations par bhi kaam kiya aur chakriya "
                "chaturbhuj ke kshetrafal ka mashhoor niyam "
                "diya — Class 10 ke area wale kaam ki jadein "
                "unke lekhan me hai."],
            "third": [
                "Unke zero-niyam khud aazmao: 5 + 0, 5 − 0, "
                "5 × 0 kitna hota hai? Aasan hai — par dekho, "
                "5 ÷ 0 ka jawab aaj bhi nahi hai. Brahmagupta "
                "bilkul isi se jujhe the."],
        },
        "dev": {
            "again": [
                "एक और बात: Brahmagupta ने quadratic "
                "equations पर भी काम किया और चक्रीय चतुर्भुज "
                "के क्षेत्रफल का मशहूर नियम दिया — Class 10 "
                "के area वाले काम की जड़ें उनके लेखन में "
                "हैं।"],
            "third": [
                "उनके zero-नियम ख़ुद आज़माओ: 5 + 0, 5 − 0, "
                "5 × 0 कितना होता है? आसान है — पर देखो, "
                "5 ÷ 0 का जवाब आज भी नहीं है। Brahmagupta "
                "बिल्कुल इसी से जूझे थे।"],
        },
    },
    ("history", "bhaskara"): {
        "en": {
            "again": [
                "One more detail: Lilavati is written as "
                "poetry, and many problems are addressed to "
                "a young girl — 'O beautiful one, tell me…' "
                "Maths as a story, 900 years ago."],
            # Wave 198 (audit 20 Nov): "half" -> "two-
            # thirds" — half of 15 is 7.5, not the stated
            # answer 10; two-thirds of 15 = 10, with 5
            # left over. The line is consistent now.
            "third": [
                "A Lilavati-flavoured practice: a swarm of "
                "bees — two-thirds of them on one flower, "
                "and 5 left over. If the whole swarm is "
                "15, how many sit on the flower? "
                "(Answer: 10.) That playful style is "
                "Bhaskara's gift."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Lilavati kavita me likhi gayi "
                "hai, aur kai sawal ek ladki ko sambodhit "
                "hai — 'O sundari, batao…' 900 saal pehle "
                "maths ek kahani ki tarah."],
            "third": [
                "Lilavati ke andaaz ki ek practice: "
                "madhumakhkhiyon ka jhund — do-tihaai ek "
                "phool par baithi, 5 bachi rahi. Poora "
                "jhund 15 hai toh phool par kitni hai? "
                "(Jawab: 10.) Ye khel-bhara andaaz "
                "Bhaskara ki den hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Lilavati कविता में लिखी गई है, "
                "और कई सवाल एक लड़की को संबोधित हैं — 'O "
                "सुंदरी, बताओ…' 900 साल पहले maths एक कहानी "
                "की तरह।"],
            "third": [
                "Lilavati के अंदाज़ की एक practice: "
                "मधुमक्खियों का झुंड — दो-तिहाई एक फूल पर "
                "बैठीं, 5 बची रहीं। पूरा झुंड 15 है तो फूल "
                "पर कितनी हैं? (जवाब: 10।) ये खेल-भरा "
                "अंदाज़ Bhaskara की देन है।"],
        },
    },
    ("history", "ramanujan"): {
        "en": {
            "again": [
                "One more detail: Ramanujan filled notebooks "
                "with thousands of results, many without "
                "proofs — mathematicians are still proving "
                "some of them today, a century later."],
            "third": [
                "A Ramanujan-style habit to copy: he played "
                "with numbers daily, like friends. Try it — "
                "take today's date and find two different "
                "ways to build it from smaller numbers."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Ramanujan ne apni copies me "
                "hazaaron parinaam bhare, kai bina proof ke "
                "— ganitgya aaj, ek sadi baad bhi, unme se "
                "kuch ko saabit kar rahe hai."],
            "third": [
                "Ramanujan jaisi ek aadat apnao: wo roz "
                "ankon se doston ki tarah khelte the. "
                "Aazmao — aaj ki tareekh lo aur use chhote "
                "ankon se banane ke do alag tareeke dhundo."],
        },
        "dev": {
            "again": [
                "एक और बात: Ramanujan ने अपनी copies में "
                "हज़ारों परिणाम भरे, कई बिना proof के — "
                "गणितज्ञ आज, एक सदी बाद भी, उनमें से कुछ "
                "को साबित कर रहे हैं।"],
            "third": [
                "Ramanujan जैसी एक आदत अपनाओ: वो रोज़ अंकों "
                "से दोस्तों की तरह खेलते थे। आज़माओ — आज "
                "की तारीख़ लो और उसे छोटे अंकों से बनाने "
                "के दो अलग तरीके ढूँढो।"],
        },
    },
    ("history", "shakuntala_devi"): {
        "en": {
            "again": [
                "One more detail: in 1980 she multiplied "
                "two 13-digit numbers in 28 seconds — a "
                "world record at the time, done entirely in "
                "her head."],
            "third": [
                "Her secret was practice, not magic: start "
                "small like her — add today's two bus or "
                "auto numbers in your head before checking. "
                "Mental maths grows exactly like this."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 1980 me unhone do 13-ankon "
                "wali sankhyaon ka guna 28 second me kar "
                "diya tha — us samay ka world record, poora "
                "dimaag me."],
            "third": [
                "Unka raaz practice tha, jaadu nahi: unki "
                "tarah chhota shuru karo — aaj bus ya auto "
                "ke do number pehle dimaag me jodo, phir "
                "mila kar dekho. Mental maths aise hi "
                "badhta hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 1980 में उन्होंने दो 13-अंकों "
                "वाली संख्याओं का गुणा 28 second में कर "
                "दिया था — उस समय का world record, पूरा "
                "दिमाग़ में।"],
            "third": [
                "उनका राज़ practice था, जादू नहीं: उनकी तरह "
                "छोटा शुरू करो — आज bus या auto के दो number "
                "पहले दिमाग़ में जोड़ो, फिर मिला कर देखो। "
                "Mental maths ऐसे ही बढ़ता है।"],
        },
    },
    ("history", "archimedes"): {
        "en": {
            "again": [
                "One more detail: Archimedes also gave the "
                "famous shout 'Eureka!' — legend says he "
                "ran from his bath when he saw how water "
                "displacement measures volume."],
            "third": [
                "Try his idea at home: fill a mug to the "
                "brim over a plate, drop in a stone, and "
                "the water that spills IS the stone's "
                "volume. You just did Archimedes' "
                "experiment."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Archimedes ki mashhoor cheekh "
                "'Eureka!' bhi unhi ki hai — kahaani hai ki "
                "nahane ke tub me unhe samajh aaya ki paani "
                "ka visthapan aayatan naapta hai."],
            "third": [
                "Unka vichaar ghar par aazmao: ek mug ko "
                "kinaare tak bharo, ek patthar dalo — jo "
                "paani bahar gira, wahi patthar ka aayatan "
                "hai. Tumne Archimedes ka prayog kar liya."],
        },
        "dev": {
            "again": [
                "एक और बात: Archimedes की मशहूर चीख़ "
                "'Eureka!' भी उन्हीं की है — कहानी है कि "
                "नहाने के tub में उन्हें समझ आया कि पानी "
                "का विस्थापन आयतन नापता है।"],
            "third": [
                "उनका विचार घर पर आज़माओ: एक mug को किनारे "
                "तक भरो, एक पत्थर डालो — जो पानी बाहर गिरा, "
                "वही पत्थर का आयतन है। तुमने Archimedes का "
                "प्रयोग कर लिया।"],
        },
    },
    ("history", "gauss"): {
        "en": {
            "again": [
                "One more detail: as a small schoolboy Gauss "
                "stunned his teacher by adding 1 to 100 in "
                "seconds — he paired 1+100, 2+99, … into "
                "fifty pairs of 101."],
            "third": [
                "Now use his trick yourself: add 1 to 50 "
                "the pairing way (1+50, 2+49, … — 25 pairs "
                "of 51). Answer: 1275. Once seen, this "
                "trick is yours forever."],
        },
        "roman": {
            "again": [
                "Ek aur baat: chhote school-boy Gauss ne "
                "apne teacher ko hairaan kar diya tha — 1 "
                "se 100 tak ka jod kuch seconds me: 1+100, "
                "2+99, … pachas jode, har joda 101."],
            "third": [
                "Ab unki trick khud aazmao: 1 se 50 tak "
                "jodo jode bana kar (1+50, 2+49, … — 25 "
                "jode, har joda 51). Jawab: 1275. Ek baar "
                "dekh liya toh ye trick hamesha tumhari."],
        },
        "dev": {
            "again": [
                "एक और बात: छोटे school-boy Gauss ने अपने "
                "teacher को हैरान कर दिया था — 1 से 100 "
                "तक का जोड़ कुछ seconds में: 1+100, 2+99, "
                "… पचास जोड़े, हर जोड़ा 101।"],
            "third": [
                "अब उनकी trick ख़ुद आज़माओ: 1 से 50 तक "
                "जोड़ो जोड़े बना कर (1+50, 2+49, … — 25 "
                "जोड़े, हर जोड़ा 51)। जवाब: 1275। एक बार "
                "देख लिया तो ये trick हमेशा तुम्हारी।"],
        },
    },
    ("history", "fibonacci"): {
        "en": {
            "again": [
                "One more detail: Fibonacci learned the "
                "Indian number system in North Africa and "
                "carried it to Europe through his book "
                "Liber Abaci (1202)."],
            "third": [
                "Spot it in nature: count the petals of a "
                "flower near you, or the spirals on a "
                "pinecone — 3, 5, 8, 13 turn up again and "
                "again. Then continue the sequence to the "
                "next two terms yourself: 21, 34."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Fibonacci ne Bharatiya ank "
                "paddhati North Africa me seekhi aur apni "
                "kitab Liber Abaci (1202) se use Europe "
                "pahunchaya."],
            "third": [
                "Ise prakriti me dhundo: apne aas-paas ke "
                "phool ki pankhudiyan gino, ya devdaar ke "
                "shanku ke ghumav — 3, 5, 8, 13 baar-baar "
                "milte hai. Phir sequence ko aage ke do pad "
                "khud banao: 21, 34."],
        },
        "dev": {
            "again": [
                "एक और बात: Fibonacci ने भारतीय अंक पद्धति "
                "North Africa में सीखी और अपनी किताब Liber "
                "Abaci (1202) से उसे Europe पहुँचाया।"],
            "third": [
                "इसे प्रकृति में ढूँढो: अपने आस-पास के फूल "
                "की पंखुड़ियाँ गिनो, या देवदार के शंकु के "
                "घुमाव — 3, 5, 8, 13 बार-बार मिलते हैं। "
                "फिर sequence को आगे के दो पद ख़ुद बनाओ: "
                "21, 34।"],
        },
    },
    ("history", "pythagoras"): {
        "en": {
            "again": [
                "One more detail: the theorem was known in "
                "India and Babylon long before Pythagoras — "
                "Baudhayana's Sulba Sutras state it too. "
                "Pythagoras' name stuck because his school "
                "proved and taught it widely."],
            "third": [
                "Check the theorem with your hands: a 3-4-5 "
                "triangle is always right-angled, because "
                "9 + 16 = 25. Builders still use a 3-4-5 "
                "rope to make perfect corners."],
        },
        "roman": {
            "again": [
                "Ek aur baat: ye pramey Pythagoras se bahut "
                "pehle Bharat aur Babylon me jaani jaati "
                "thi — Baudhayana ke Sulba Sutron me bhi ye "
                "hai. Pythagoras ka naam isliye chipka "
                "kyunki unke school ne ise saabit karke "
                "door-door tak padhaya."],
            "third": [
                "Pramey ko haathon se parkho: 3-4-5 wala "
                "tribhuj hamesha samkon hota hai, kyunki "
                "9 + 16 = 25. Mistry aaj bhi 3-4-5 ki rassi "
                "se perfect kona banate hai."],
        },
        "dev": {
            "again": [
                "एक और बात: ये प्रमेय Pythagoras से बहुत "
                "पहले भारत और Babylon में जानी जाती थी — "
                "Baudhayana के Sulba सूत्रों में भी ये है। "
                "Pythagoras का नाम इसलिए चिपका क्योंकि "
                "उनके school ने इसे साबित करके दूर-दूर तक "
                "पढ़ाया।"],
            "third": [
                "प्रमेय को हाथों से परखो: 3-4-5 वाला त्रिभुज "
                "हमेशा समकोण होता है, क्योंकि 9 + 16 = 25। "
                "मिस्त्री आज भी 3-4-5 की रस्सी से perfect "
                "कोना बनाते हैं।"],
        },
    },
    ("fact", "hardy_ramanujan"): {
        "en": {
            "again": [
                "One more detail: Hardy had come in a taxi "
                "numbered 1729 and called it dull — "
                "Ramanujan, ill in bed, answered at once "
                "that it is the smallest number writable as "
                "a sum of two cubes in two different ways."],
            "third": [
                "Verify the magic yourself: 1³ + 12³ = 1 + "
                "1728 = 1729, and 9³ + 10³ = 729 + 1000 = "
                "1729. Two roads, one number — now it is "
                "yours too."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Hardy taxi number 1729 se aaye "
                "the aur use 'boring' kaha tha — Ramanujan "
                "ne bistar par lete-lete turant jawab diya "
                "ki ye sabse chhoti sankhya hai jo do ghanon "
                "ke jod ke roop me do alag tareekon se likhi "
                "ja sakti hai."],
            "third": [
                "Jaadu khud jaancho: 1³ + 12³ = 1 + 1728 = "
                "1729, aur 9³ + 10³ = 729 + 1000 = 1729. Do "
                "raaste, ek number — ab ye tumhara bhi "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Hardy taxi number 1729 से आए थे "
                "और उसे 'boring' कहा था — Ramanujan ने "
                "बिस्तर पर लेटे-लेटे तुरंत जवाब दिया कि ये "
                "सबसे छोटी संख्या है जो दो घनों के जोड़ के "
                "रूप में दो अलग तरीकों से लिखी जा सकती "
                "है।"],
            "third": [
                "जादू ख़ुद जाँचो: 1³ + 12³ = 1 + 1728 = "
                "1729, और 9³ + 10³ = 729 + 1000 = 1729। दो "
                "रास्ते, एक number — अब ये तुम्हारा भी "
                "है।"],
        },
    },
    ("fact", "infinity"): {
        "en": {
            "again": [
                "One more detail: the ∞ symbol was "
                "introduced by John Wallis in 1655 — its "
                "loop shape itself suggests something that "
                "never ends."],
            "third": [
                "A mind-bending practice: is the infinity "
                "of even numbers (2, 4, 6, …) smaller than "
                "the infinity of all numbers? Pair them — "
                "1↔2, 2↔4, 3↔6 — every number gets a "
                "partner, so the two infinities match. "
                "Infinity plays by strange rules."],
        },
        "roman": {
            "again": [
                "Ek aur baat: ∞ ka chinh John Wallis ne 1655 "
                "me diya tha — iski ghumavdaar aakriti khud "
                "hi 'kabhi khatm na hone' ka ishara hai."],
            "third": [
                "Dimaag ghuma dene wali ek practice: kya "
                "sam sankhyaon ki anant-ta (2, 4, 6, …) "
                "sab sankhyaon ki anant-ta se chhoti hai? "
                "Jode banao — 1↔2, 2↔4, 3↔6 — har sankhya "
                "ko saathi mil jata hai, toh dono anant-ta "
                "barabar nikli. Anant ke niyam ajeeb hai."],
        },
        "dev": {
            "again": [
                "एक और बात: ∞ का चिन्ह John Wallis ने 1655 "
                "में दिया था — इसकी घुमावदार आकृति ख़ुद ही "
                "'कभी ख़त्म न होने' का इशारा है।"],
            "third": [
                "दिमाग़ घुमा देने वाली एक practice: क्या सम "
                "संख्याओं की अनंतता (2, 4, 6, …) सब "
                "संख्याओं की अनंतता से छोटी है? जोड़े बनाओ "
                "— 1↔2, 2↔4, 3↔6 — हर संख्या को साथी मिल "
                "जाता है, तो दोनों अनंतता बराबर निकलीं। "
                "अनंत के नियम अजीब हैं।"],
        },
    },
    ("fact", "lakh_zeros"): {
        "en": {
            "again": [
                "One more detail: the Indian system groups "
                "digits as 3-2-2 (1,00,000) while the "
                "international system groups by 3s "
                "(100,000) — same number, different commas."],
            "third": [
                "Quick practice, say it without writing: "
                "how many zeros in 10 lakh? (Answer: 6 — "
                "10 lakh is 10,00,000, the same as one "
                "million.)"],
        },
        "roman": {
            "again": [
                "Ek aur baat: Bharatiya paddhati ankon ko "
                "3-2-2 me baantti hai (1,00,000), jabki "
                "antarrashtriya paddhati 3-3 me (100,000) — "
                "number wahi, bas comma alag."],
            "third": [
                "Jhatpat practice, bina likhe batao: 10 "
                "lakh me kitne zero? (Jawab: 6 — 10 lakh "
                "matlab 10,00,000, yahi ek million hai.)"],
        },
        "dev": {
            "again": [
                "एक और बात: भारतीय पद्धति अंकों को 3-2-2 में "
                "बाँटती है (1,00,000), जबकि अंतरराष्ट्रीय "
                "पद्धति 3-3 में (100,000) — number वही, बस "
                "comma अलग।"],
            "third": [
                "झटपट practice, बिना लिखे बताओ: 10 lakh में "
                "कितने zero? (जवाब: 6 — 10 lakh मतलब "
                "10,00,000, यही एक million है।)"],
        },
    },
    ("fact", "golden_ratio"): {
        "en": {
            "again": [
                "One more detail: φ hides inside the "
                "Fibonacci sequence — divide any term by "
                "the one before it (8÷5, 13÷8, 21÷13) and "
                "the answers creep closer and closer to "
                "1.618."],
            "third": [
                "Try it: 21 ÷ 13 on paper — you get 1.615…, "
                "then 34 ÷ 21 gives 1.619…. The ratio is "
                "walking towards φ step by step. Two "
                "divisions and you have met it yourself."],
        },
        "roman": {
            "again": [
                "Ek aur baat: φ Fibonacci sequence ke andar "
                "chhupa hai — kisi pad ko uske pichle pad se "
                "bhaag do (8÷5, 13÷8, 21÷13) aur jawab "
                "1.618 ke aur aur paas jate hai."],
            "third": [
                "Aazmao: 21 ÷ 13 copy par karo — 1.615… "
                "aayega, phir 34 ÷ 21 = 1.619… Anupat kadam "
                "kadam φ ki or badh raha hai. Do bhaag aur "
                "tum φ se khud mil liye."],
        },
        "dev": {
            "again": [
                "एक और बात: φ Fibonacci sequence के अंदर "
                "छुपा है — किसी पद को उसके पिछले पद से भाग "
                "दो (8÷5, 13÷8, 21÷13) और जवाब 1.618 के "
                "और और पास जाते हैं।"],
            "third": [
                "आज़माओ: 21 ÷ 13 copy पर करो — 1.615… "
                "आएगा, फिर 34 ÷ 21 = 1.619…। अनुपात कदम "
                "कदम φ की ओर बढ़ रहा है। दो भाग और तुम φ "
                "से ख़ुद मिल लिए।"],
        },
    },
    ("fact", "one_neither"): {
        "en": {
            "again": [
                "One more detail: 1 was treated as a prime "
                "in many old books — mathematicians later "
                "agreed to exclude it, because keeping 1 "
                "out makes the prime rules (like unique "
                "factorisation) work cleanly."],
            "third": [
                "Test the definition yourself: a prime must "
                "have EXACTLY two factors. Count 1's factors "
                "— only 1 itself, just one. That single "
                "count is the whole reason."],
        },
        "roman": {
            "again": [
                "Ek aur baat: kai purani kitabon me 1 ko "
                "prime mana jata tha — baad me ganitgyon ne "
                "ise bahar rakhna tay kiya, kyunki 1 ko "
                "bahar rakhne se prime ke niyam (jaise "
                "unique factorisation) saaf chalte hai."],
            "third": [
                "Paribhasha khud parkho: prime ke THIK do "
                "gunankhand hone chahiye. 1 ke gunankhand "
                "gino — sirf 1, keval ek. Yahi ek ginti "
                "poori wajah hai."],
        },
        "dev": {
            "again": [
                "एक और बात: कई पुरानी किताबों में 1 को prime "
                "माना जाता था — बाद में गणितज्ञों ने इसे "
                "बाहर रखना तय किया, क्योंकि 1 को बाहर रखने "
                "से prime के नियम (जैसे unique factorisation) "
                "साफ़ चलते हैं।"],
            "third": [
                "परिभाषा ख़ुद परखो: prime के ठीक दो गुणनखंड "
                "होने चाहिए। 1 के गुणनखंड गिनो — सिर्फ़ 1, "
                "केवल एक। यही एक गिनती पूरी वजह है।"],
        },
    },
    ("fact", "prime_two"): {
        "en": {
            "again": [
                "One more detail: every even number above 2 "
                "is divisible by 2, so it can never be "
                "prime — that one line is the whole proof "
                "that 2 stands alone."],
            "third": [
                "Quick practice: is 51 prime? It looks "
                "odd and tricky — but 5 + 1 = 6 is divisible "
                "by 3, so 51 = 3 × 17, not prime. The "
                "digit-sum trick catches it."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 2 se badi har sam sankhya 2 se "
                "katti hai, toh wo prime ho hi nahi sakti — "
                "yahi ek line poora saboot hai ki 2 akela "
                "khada hai."],
            "third": [
                "Jhatpat practice: kya 51 prime hai? Odd "
                "aur mushkil lagta hai — par 5 + 1 = 6, jo "
                "3 se katta hai, toh 51 = 3 × 17, prime "
                "nahi. Ankon ke jod wali trick ise pakad "
                "leti hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 2 से बड़ी हर सम संख्या 2 से "
                "कटती है, तो वो prime हो ही नहीं सकती — "
                "यही एक line पूरा सबूत है कि 2 अकेला खड़ा "
                "है।"],
            "third": [
                "झटपट practice: क्या 51 prime है? Odd और "
                "मुश्किल लगता है — पर 5 + 1 = 6, जो 3 से "
                "कटता है, तो 51 = 3 × 17, prime नहीं। अंकों "
                "के जोड़ वाली trick इसे पकड़ लेती है।"],
        },
    },
}

# ---------------------------------------------------------------------------
# Wave 200: AUTHORED repeat variations for EVERY remaining
# knowledge entry (Suraj, 20 Nov 2026 ~00:43 IST: "Jo 1 baar
# de diya ans toh wapas kyu deta hai, har baar Naya ans
# chahiye").
#
# Wave 178 authored variations for 20 entries; every other
# entry rode on the kind's generic pool below — true lines,
# but the SAME generic lines for every card of the kind.
# Wave 200 authors a per-entry "again" (2nd ask: a fresh
# example / extra fact) and "third" (3rd+ ask: a deeper
# fact / a practice step) for every remaining HISTORY /
# FACTS / ADVICE entry, in all three flavours, so a repeat
# ask of ANY knowledge card brings something of that
# card's own. The base cards and their answer lines are
# untouched — a varied serve still carries the base card
# and its answer verbatim; only the framing grows. The
# counting / rotation engine is Wave 178's (repeat.py +
# meta_variation below). Entries join via .update() so
# this block never collides with edits inside the base
# tables (Wave 198's zero-entry fix included).
# ---------------------------------------------------------------------------

META_VARIATIONS.update({
    ("fact", "largest_2digit_prime"): {
        "en": {
            "again": [
                "One more detail: to test 97 you only need "
                "to try dividing by the primes up to √97 — "
                "that is, up to 9: 2, 3, 5, 7. None of them "
                "divides it, so the check ends in seconds."],
            "third": [
                "Quick practice: what is the largest "
                "THREE-digit prime? Work down from 999 the "
                "same way — the answer is 997."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 97 ko parkhne ke liye sirf "
                "√97 tak ke primes se bhaag dekhna padta "
                "hai, matlab 9 tak — 2, 3, 5, 7. Koi bhi "
                "nahi kaat-ta, toh jaanch secondon me "
                "khatm."],
            "third": [
                "Jhatpat practice: sabse bada TEEN ankon "
                "ka prime kaun sa hai? 999 se neeche aate "
                "hue wahi tareeka lagao — jawab 997 hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 97 को परखने के लिए सिर्फ़ √97 "
                "तक की अभाज्य संख्याओं से भाग देखना पड़ता "
                "है, मतलब 9 तक — 2, 3, 5, 7। कोई भी नहीं "
                "काटती, तो जाँच सेकंडों में ख़त्म।"],
            "third": [
                "झटपट practice: सबसे बड़ा तीन अंकों का "
                "prime कौन सा है? 999 से नीचे आते हुए वही "
                "तरीका लगाओ — जवाब 997 है।"],
        },
    },
    ("fact", "smallest_2digit_prime"): {
        "en": {
            "again": [
                "One more detail: between 10 and 20 there "
                "are exactly four primes — 11, 13, 17, 19. "
                "Learn them as one group and two-digit "
                "prime questions become instant."],
            "third": [
                "Quick practice: is 21 prime? 2 + 1 = 3 "
                "is divisible by 3, so 21 = 3 × 7 — not "
                "prime. The digit-sum check kills it in "
                "one step."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 10 aur 20 ke beech kul "
                "chaar prime hai — 11, 13, 17, 19. Inhe "
                "ek group me yaad kar lo, phir do-ankon "
                "ke prime wale sawal turant honge."],
            "third": [
                "Jhatpat practice: kya 21 prime hai? "
                "2 + 1 = 3, jo 3 se katta hai, toh "
                "21 = 3 × 7 — prime nahi. Ankon ke jod "
                "wali jaanch ek step me khatm kar deti "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 10 और 20 के बीच कुल चार prime "
                "हैं — 11, 13, 17, 19। इन्हें एक group में "
                "याद कर लो, फिर दो-अंकों के prime वाले "
                "सवाल तुरंत होंगे।"],
            "third": [
                "झटपट practice: क्या 21 prime है? 2 + 1 = 3, "
                "जो 3 से कटता है, तो 21 = 3 × 7 — prime "
                "नहीं। अंकों के जोड़ वाली जाँच एक step में "
                "ख़त्म कर देती है।"],
        },
    },
    ("fact", "primes_below_20"): {
        "en": {
            "again": [
                "One more detail: below 50 there are 15 "
                "primes and below 100 there are 25 — the "
                "primes thin out as numbers grow, but they "
                "never stop (Euclid proved that)."],
            "third": [
                "Self-test, no writing: say the primes "
                "between 20 and 30. (They are 23 and 29 — "
                "25 is 5 × 5 and 27 is 3 × 9.) If you got "
                "both, your sieve is working."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 50 se neeche 15 prime hai "
                "aur 100 se neeche 25 — jaise-jaise "
                "sankhyayen badhti hai prime kam hote "
                "jate hai, lekin rukte kabhi nahi "
                "(Euclid ne ye saabit kiya tha)."],
            "third": [
                "Khud ko parkho, bina likhe: 20 aur 30 ke "
                "beech ke prime batao. (Wo hai 23 aur 29 "
                "— 25 = 5 × 5 hai aur 27 = 3 × 9.) Dono "
                "sahi bole toh tumhari chaalni chal rahi "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 50 से नीचे 15 prime हैं और 100 "
                "से नीचे 25 — जैसे-जैसे संख्याएँ बढ़ती हैं "
                "prime कम होते जाते हैं, लेकिन रुकते कभी "
                "नहीं (यूक्लिड ने यह सिद्ध किया था)।"],
            "third": [
                "ख़ुद को परखो, बिना लिखे: 20 और 30 के बीच "
                "के prime बताओ। (वे हैं 23 और 29 — "
                "25 = 5 × 5 है और 27 = 3 × 9।) दोनों सही "
                "बोले तो तुम्हारी छलनी चल रही है।"],
        },
    },
    ("fact", "largest_prime_none"): {
        "en": {
            "again": [
                "One more detail: Euclid's proof is "
                "beautifully simple — multiply all the "
                "primes you think are the last ones, add "
                "1, and the result forces a brand-new "
                "prime to exist."],
            "third": [
                "Try Euclid's trick with your own hands: "
                "2 × 3 × 5 × 7 × 11 × 13 + 1 = 30031 "
                "= 59 × 509. The new number's prime "
                "factors were NOT in your list — the list "
                "can never be complete."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Euclid ka saboot bahut hi "
                "saral hai — jin primes ko tum aakhiri "
                "samajhte ho, un sab ko guna karke 1 jod "
                "do; nateeja ek bilkul naya prime "
                "majboori me le aata hai."],
            "third": [
                "Euclid ki chaal khud aazmao: "
                "2 × 3 × 5 × 7 × 11 × 13 + 1 = 30031 "
                "= 59 × 509. Naye number ke prime "
                "factors tumhari list me NAHI the — list "
                "kabhi poori ho hi nahi sakti."],
        },
        "dev": {
            "again": [
                "एक और बात: यूक्लिड का प्रमाण बहुत ही सरल "
                "है — जिन अभाज्य संख्याओं को तुम अंतिम "
                "समझते हो, उन सबको गुणा करके 1 जोड़ दो; "
                "परिणाम एक बिल्कुल नया अभाज्य मजबूरी में "
                "ले आता है।"],
            "third": [
                "यूक्लिड की चाल ख़ुद आज़माओ: "
                "2 × 3 × 5 × 7 × 11 × 13 + 1 = 30031 "
                "= 59 × 509। नई संख्या के अभाज्य गुणनखंड "
                "तुम्हारी सूची में नहीं थे — सूची कभी "
                "पूरी हो ही नहीं सकती।"],
        },
    },
    ("fact", "smallest_odd_prime"): {
        "en": {
            "again": [
                "One more detail: 3 also opens a famous "
                "family — twin primes. 3 and 5 differ by "
                "2, so they are called twins; 5 and 7, "
                "11 and 13 are twin pairs too."],
            "third": [
                "Quick practice: how many odd primes are "
                "there below 10? Count them: 3, 5, 7 — "
                "three. (9 looks odd but is 3 × 3, so it "
                "stays out.)"],
        },
        "roman": {
            "again": [
                "Ek aur baat: 3 ek mashhoor jode ka pehla "
                "odd prime bhi hai — twin primes. 3 aur "
                "5 me 2 ka antar hai, isiliye inhe judwa "
                "(twin) prime kehte hai; 5 aur 7, 11 aur "
                "13 bhi judwa hai."],
            "third": [
                "Jhatpat practice: 10 se neeche kitne "
                "odd prime hai? Gino: 3, 5, 7 — teen. "
                "(9 odd lagta hai lekin 3 × 3 hai, "
                "isiliye wo bahar rahega.)"],
        },
        "dev": {
            "again": [
                "एक और बात: 3 एक मशहूर जोड़े का पहला विषम "
                "prime भी है — twin primes। 3 और 5 में 2 "
                "का अंतर है, इसलिए इन्हें जुड़वाँ (twin) "
                "prime कहते हैं; 5 और 7, 11 और 13 भी "
                "जुड़वाँ हैं।"],
            "third": [
                "झटपट practice: 10 से नीचे कितने विषम "
                "prime हैं? गिनो: 3, 5, 7 — तीन। (9 विषम "
                "लगता है लेकिन 3 × 3 है, इसलिए वह बाहर "
                "रहेगा।)"],
        },
    },
    ("fact", "smallest_composite"): {
        "en": {
            "again": [
                "One more detail: 4 is also the smallest "
                "composite perfect square — 2² = 4. The "
                "composites then run 4, 6, 8, 9, 10… "
                "notice 9 = 3 × 3 joins the list soon "
                "after."],
            "third": [
                "Quick practice: is 1 composite? No — it "
                "has only one factor. Is 9 prime? No — "
                "3 × 3. These two checks (1 and 9) are "
                "the traps in almost every test on this "
                "topic."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 4 sabse chhota composite "
                "perfect square bhi hai — 2² = 4. "
                "Composite phir chalte hai: 4, 6, 8, 9, "
                "10… dekho, 9 = 3 × 3 bhi jald hi list "
                "me aa jata hai."],
            "third": [
                "Jhatpat practice: kya 1 composite hai? "
                "Nahi — uska sirf ek factor hai. Kya 9 "
                "prime hai? Nahi — 3 × 3. Yehi do jaanch "
                "(1 aur 9) is topic ke har test ke jaal "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 4 सबसे छोटा composite पूर्ण "
                "वर्ग भी है — 2² = 4। भाज्य फिर चलते हैं: "
                "4, 6, 8, 9, 10… देखो, 9 = 3 × 3 भी जल्द "
                "ही सूची में आ जाता है।"],
            "third": [
                "झटपट practice: क्या 1 भाज्य है? नहीं — "
                "उसका सिर्फ़ एक गुणनखंड है। क्या 9 अभाज्य "
                "है? नहीं — 3 × 3। यही दो जाँच (1 और 9) "
                "इस topic के हर test के जाल हैं।"],
        },
    },
    ("fact", "smallest_natural"): {
        "en": {
            "again": [
                "One more detail: natural numbers are "
                "also called counting numbers — they are "
                "exactly the numbers you count things "
                "with: one book, two books, three books."],
            "third": [
                "A thinking step: is 0 a natural number? "
                "In school maths, no — counting never "
                "starts at 0. Add 0 to the naturals and "
                "they become the WHOLE numbers; that one "
                "step is the whole difference."],
        },
        "roman": {
            "again": [
                "Ek aur baat: natural numbers ko ginati "
                "wali sankhyayen (counting numbers) bhi "
                "kehte hai — ye wahi sankhyayen hai jinse "
                "cheezein gini jati hai: ek kitab, do "
                "kitab, teen kitab."],
            "third": [
                "Ek sochne wala step: kya 0 natural "
                "number hai? School ke maths me nahi — "
                "ginati kabhi 0 se shuru nahi hoti. "
                "Naturals me 0 jod do toh WHOLE numbers "
                "ban jate hai; yahi ek kadam poora antar "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: प्राकृतिक संख्याओं को गिनती "
                "वाली संख्याएँ (counting numbers) भी कहते "
                "हैं — ये वही संख्याएँ हैं जिनसे चीज़ें "
                "गिनी जाती हैं: एक किताब, दो किताब, तीन "
                "किताब।"],
            "third": [
                "एक सोचने वाला step: क्या 0 प्राकृतिक "
                "संख्या है? School के maths में नहीं — "
                "गिनती कभी 0 से शुरू नहीं होती। प्राकृतिक "
                "संख्याओं में 0 जोड़ दो तो पूर्ण (WHOLE) "
                "संख्याएँ बन जाती हैं; यही एक कदम पूरा "
                "अंतर है।"],
        },
    },
    ("fact", "smallest_whole"): {
        "en": {
            "again": [
                "One more detail: whole numbers are the "
                "natural numbers with 0 invited in — "
                "0, 1, 2, 3… Every natural number is a "
                "whole number, but 0 is whole without "
                "being natural."],
            "third": [
                "Quick check, answer in one line each: "
                "smallest natural? 1. Smallest whole? 0. "
                "If you can fire both answers instantly, "
                "this pair will never cost you a mark "
                "again."],
        },
        "roman": {
            "again": [
                "Ek aur baat: whole numbers matlab "
                "natural numbers me 0 ko bhi bula liya — "
                "0, 1, 2, 3… Har natural number whole "
                "number hai, lekin 0 whole hai bina "
                "natural hue."],
            "third": [
                "Jhatpat jaanch, ek-ek line me jawab: "
                "sabse chhoti natural? 1. Sabse chhoti "
                "whole? 0. Dono jawab turant nikal aaye "
                "toh ye joda phir kabhi number nahi "
                "katega."],
        },
        "dev": {
            "again": [
                "एक और बात: पूर्ण संख्याएँ मतलब प्राकृतिक "
                "संख्याओं में 0 को भी बुला लिया — 0, 1, "
                "2, 3… हर प्राकृतिक संख्या पूर्ण संख्या "
                "है, लेकिन 0 पूर्ण है बिना प्राकृतिक "
                "हुए।"],
            "third": [
                "झटपट जाँच, एक-एक line में जवाब: सबसे "
                "छोटी प्राकृतिक? 1। सबसे छोटी पूर्ण? 0। "
                "दोनों जवाब तुरंत निकल आए तो यह जोड़ा "
                "फिर कभी अंक नहीं काटेगा।"],
        },
    },
    ("fact", "no_reciprocal"): {
        "en": {
            "again": [
                "One more detail: every other number's "
                "reciprocal flips it — 2 becomes 1/2, "
                "1/5 becomes 5. Zero alone cannot flip, "
                "because flipping it would mean dividing "
                "by it."],
            "third": [
                "Think it through once: if 1/0 were some "
                "number k, then 0 × k would have to be 1 "
                "— but 0 times anything is 0. That "
                "contradiction is exactly why 1/0 is "
                "left undefined."],
        },
        "roman": {
            "again": [
                "Ek aur baat: har dusri sankhya ka "
                "reciprocal use ulta kar deta hai — 2 ka "
                "1/2, 1/5 ka 5. Zero akela ulta nahi ho "
                "sakta, kyunki use ulta karna matlab usi "
                "se bhaag dena."],
            "third": [
                "Ek baar soch kar dekho: agar 1/0 koi "
                "sankhya k hoti, toh 0 × k ko 1 hona "
                "chahiye tha — lekin 0 se guna hamesha 0 "
                "hota hai. Yahi uljhan hai ki 1/0 ko "
                "undefined chhoda gaya hai."],
        },
        "dev": {
            "again": [
                "एक और बात: हर दूसरी संख्या का व्युत्क्रम "
                "उसे उल्टा कर देता है — 2 का 1/2, 1/5 का "
                "5। शून्य अकेला उल्टा नहीं हो सकता, "
                "क्योंकि उसे उल्टा करना मतलब उसी से भाग "
                "देना।"],
            "third": [
                "एक बार सोचकर देखो: अगर 1/0 कोई संख्या k "
                "होती, तो 0 × k को 1 होना चाहिए था — "
                "लेकिन 0 से गुणा हमेशा 0 होता है। यही "
                "उलझन है कि 1/0 को अपरिभाषित छोड़ा गया "
                "है।"],
        },
    },
    ("fact", "zero_neither_sign"): {
        "en": {
            "again": [
                "One more detail: on the number line, 0 "
                "is the mirror between the two sides — "
                "+3 and −3 stand at equal distance from "
                "it. That is why 0 is also called the "
                "additive identity: adding it changes "
                "nothing."],
            "third": [
                "Quick practice: which of these are "
                "negative — −7, 0, +2, −1/2? Only −7 and "
                "−1/2. If you were about to include 0, "
                "remember: 0 stands with neither side."],
        },
        "roman": {
            "again": [
                "Ek aur baat: sankhya-rekha par 0 dono "
                "taraf ke beech ka sheesha hai — +3 aur "
                "−3 usse barabar doori par khade hai. "
                "Isiliye 0 ko additive identity bhi "
                "kehte hai: use jodne se kuch nahi "
                "badalta."],
            "third": [
                "Jhatpat practice: inme se kaun si "
                "negative hai — −7, 0, +2, −1/2? Sirf −7 "
                "aur −1/2. Agar 0 ko bhi shamil karne "
                "wale the, toh yaad rakho: 0 kisi ke "
                "saath khada nahi hai."],
        },
        "dev": {
            "again": [
                "एक और बात: संख्या-रेखा पर 0 दोनों तरफ़ "
                "के बीच का शीशा है — +3 और −3 उससे बराबर "
                "दूरी पर खड़े हैं। इसीलिए 0 को योगात्मक "
                "तत्समक (additive identity) भी कहते हैं: "
                "उसे जोड़ने से कुछ नहीं बदलता।"],
            "third": [
                "झटपट practice: इनमें से कौन सी ऋणात्मक "
                "हैं — −7, 0, +2, −1/2? सिर्फ़ −7 और "
                "−1/2। अगर 0 को भी शामिल करने वाले थे, "
                "तो याद रखो: 0 किसी के साथ खड़ा नहीं "
                "है।"],
        },
    },
    ("fact", "crore_zeros"): {
        "en": {
            "again": [
                "One more detail: 1 crore is also 10 "
                "million — the same amount in the "
                "international system. Indian commas "
                "group it 1,00,00,000; international "
                "commas write 10,000,000."],
            "third": [
                "Quick practice: how many zeros in 100 "
                "crore? 100 crore is 1 arab — "
                "1,000,000,000 — so 9 zeros. Climb the "
                "ladder one rung at a time: lakh 5, "
                "crore 7, arab 9."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 1 crore matlab 10 million "
                "bhi hai — antarrashtriya paddhati me "
                "wahi rakam. Bharatiya comma use "
                "1,00,00,000 likhte hai; antarrashtriya "
                "comma 10,000,000."],
            "third": [
                "Jhatpat practice: 100 crore me kitne "
                "zero? 100 crore matlab 1 arab — "
                "1,000,000,000 — toh 9 zero. Seedhi "
                "ek-ek karke chadho: lakh 5, crore 7, "
                "arab 9."],
        },
        "dev": {
            "again": [
                "एक और बात: 1 करोड़ मतलब 10 million भी "
                "है — अंतरराष्ट्रीय पद्धति में वही रकम। "
                "भारतीय comma उसे 1,00,00,000 लिखते हैं; "
                "अंतरराष्ट्रीय comma 10,000,000।"],
            "third": [
                "झटपट practice: 100 करोड़ में कितने "
                "शून्य? 100 करोड़ मतलब 1 अरब — "
                "1,000,000,000 — तो 9 शून्य। सीढ़ी "
                "एक-एक करके चढ़ो: लाख 5, करोड़ 7, अरब "
                "9।"],
        },
    },
    ("fact", "million_zeros"): {
        "en": {
            "again": [
                "One more detail: 'million' comes from "
                "Italian 'millione', meaning a 'big "
                "thousand' — a thousand thousands. That "
                "is exactly what it is: 1000 × 1000."],
            "third": [
                "Quick practice: how many lakh in 5 "
                "million? One million is 10 lakh, so 5 "
                "million is 50 lakh. Converting Indian "
                "and international here is just "
                "multiplying or dividing by 10."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 'million' shabd Italian "
                "'millione' se aaya hai, matlab 'bada "
                "hazaar' — hazaaron ka hazaar. Aur ye "
                "hai bhi bilkul wahi: 1000 × 1000."],
            "third": [
                "Jhatpat practice: 5 million me kitne "
                "lakh? Ek million = 10 lakh, toh 5 "
                "million = 50 lakh. Bharatiya aur "
                "antarrashtriya badlaav yahan sirf 10 se "
                "guna ya bhaag hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 'million' शब्द इतालवी "
                "'millione' से आया है, मतलब 'बड़ा "
                "हज़ार' — हज़ारों का हज़ार। और यह है भी "
                "बिल्कुल वही: 1000 × 1000।"],
            "third": [
                "झटपट practice: 5 million में कितने लाख? "
                "एक million = 10 लाख, तो 5 million = 50 "
                "लाख। भारतीय ↔ अंतरराष्ट्रीय बदलाव यहाँ "
                "सिर्फ़ 10 से गुणा या भाग है।"],
        },
    },
    ("fact", "billion_zeros"): {
        "en": {
            "again": [
                "One more detail: the world's population "
                "is about 8 billion — and a billion "
                "seconds is nearly 32 years. A billion "
                "is much bigger than it sounds."],
            "third": [
                "Quick practice: a crore is 10⁷ and a "
                "billion is 10⁹. How many crores in one "
                "billion? 10⁹ ÷ 10⁷ = 100 — the same "
                "100 crore from the card, now in powers."],
        },
        "roman": {
            "again": [
                "Ek aur baat: duniya ki aabadi lagbhag 8 "
                "billion hai — aur ek billion second "
                "matlab lagbhag 32 saal. Billion sunane "
                "se kahin bada hota hai."],
            "third": [
                "Jhatpat practice: crore hai 10⁷ aur "
                "billion hai 10⁹. Ek billion me kitne "
                "crore? 10⁹ ÷ 10⁷ = 100 — wahi 100 "
                "crore, ab ghaaton (powers) ki bhasha "
                "me."],
        },
        "dev": {
            "again": [
                "एक और बात: दुनिया की आबादी लगभग 8 "
                "billion है — और एक billion second मतलब "
                "लगभग 32 साल। Billion सुनने से कहीं बड़ा "
                "होता है।"],
            "third": [
                "झटपट practice: करोड़ है 10⁷ और billion "
                "है 10⁹। एक billion में कितने करोड़? "
                "10⁹ ÷ 10⁷ = 100 — वही 100 करोड़, अब "
                "घातों (powers) की भाषा में।"],
        },
    },
    ("fact", "dozen"): {
        "en": {
            "again": [
                "One more detail: dozens survive from "
                "old trade — eggs, bananas and pencils "
                "are still sold by the dozen today, and "
                "12 also divides neatly by 2, 3, 4 and "
                "6, which made it handy for shopkeepers."],
            "third": [
                "Quick practice: a shopkeeper sells 5 "
                "dozen bananas. How many bananas is "
                "that? 5 × 12 = 60. Now reverse it: 96 "
                "eggs is how many dozen? 96 ÷ 12 = 8."],
        },
        "roman": {
            "again": [
                "Ek aur baat: darjan purane vyapaar se "
                "aaj tak zinda hai — ande, kele aur "
                "pencil aaj bhi darjan se bikte hai, aur "
                "12 aaram se 2, 3, 4 aur 6 se kat bhi "
                "jata hai, jo dukaan-daar ke liye aasan "
                "tha."],
            "third": [
                "Jhatpat practice: ek dukaan-daar 5 "
                "darjan kele bechta hai. Kitne kele hue? "
                "5 × 12 = 60. Ab ulta: 96 ande kitne "
                "darjan? 96 ÷ 12 = 8."],
        },
        "dev": {
            "again": [
                "एक और बात: दर्जन पुराने व्यापार से आज "
                "तक ज़िंदा है — अंडे, केले और pencil आज "
                "भी दर्जन से बिकते हैं, और 12 आराम से "
                "2, 3, 4 और 6 से कट भी जाता है, जो "
                "दुकानदार के लिए आसान था।"],
            "third": [
                "झटपट practice: एक दुकानदार 5 दर्जन केले "
                "बेचता है। कितने केले हुए? 5 × 12 = 60। "
                "अब उल्टा: 96 अंडे कितने दर्जन? "
                "96 ÷ 12 = 8।"],
        },
    },
    ("fact", "gross"): {
        "en": {
            "again": [
                "One more detail: 144 is also 12² — a "
                "perfect square. A gross is literally a "
                "dozen dozens, a square of dozens, which "
                "is why traders found it easy to stack "
                "and count."],
            "third": [
                "Quick practice: a trader packs 2 gross "
                "pencils. How many pencils? 2 × 144 "
                "= 288. And half a gross? 72 — six "
                "dozen."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 144 ek perfect square bhi "
                "hai — 12². Gross matlab darjanon ka "
                "darjan, darjanon ka ek varg, isiliye "
                "vyapaariyon ko use ginna aur sajana "
                "aasan padta tha."],
            "third": [
                "Jhatpat practice: ek vyapaari 2 gross "
                "pencil pack karta hai. Kitni pencil? "
                "2 × 144 = 288. Aur aadha gross? 72 — "
                "chhah darjan."],
        },
        "dev": {
            "again": [
                "एक और बात: 144 एक पूर्ण वर्ग भी है — "
                "12²। Gross मतलब दर्जनों का दर्जन, "
                "दर्जनों का एक वर्ग, इसीलिए व्यापारियों "
                "को उसे गिनना और सजाना आसान पड़ता था।"],
            "third": [
                "झटपट practice: एक व्यापारी 2 gross "
                "pencil pack करता है। कितनी pencil? "
                "2 × 144 = 288। और आधा gross? 72 — छह "
                "दर्जन।"],
        },
    },
    ("fact", "decimal_system"): {
        "en": {
            "again": [
                "One more detail: only ten symbols — 0 "
                "to 9 — build every number you will ever "
                "meet, from your marks to the distance "
                "of a star. That economy is the system's "
                "real genius."],
            "third": [
                "Try the old way once: write 2026 in "
                "Roman numerals (MMXXVI) and then add 1 "
                "in that system. Two minutes of struggle "
                "will show you why the Indian place-value "
                "system conquered the world."],
        },
        "roman": {
            "again": [
                "Ek aur baat: sirf das chinh — 0 se 9 — "
                "har wo sankhya bana dete hai jo tum "
                "kabhi dekhoge, tumhare marks se lekar "
                "taare ki doori tak. Yahi bachat is "
                "paddhati ki asal khubi hai."],
            "third": [
                "Purana tareeka ek baar aazmao: 2026 ko "
                "Roman ankon me likho (MMXXVI) aur phir "
                "usi paddhati me 1 jodo. Do minute ki "
                "kasrat bata degi ki Bharatiya "
                "sthan-maan paddhati ne duniya kyun "
                "jeeti."],
        },
        "dev": {
            "again": [
                "एक और बात: सिर्फ़ दस चिह्न — 0 से 9 — हर "
                "वो संख्या बना देते हैं जो तुम कभी "
                "देखोगे, तुम्हारे अंकों से लेकर तारे की "
                "दूरी तक। यही बचत इस पद्धति की असली "
                "ख़ूबी है।"],
            "third": [
                "पुराना तरीका एक बार आज़माओ: 2026 को "
                "Roman अंकों में लिखो (MMXXVI) और फिर "
                "उसी पद्धति में 1 जोड़ो। दो minute की "
                "कसरत बता देगी कि भारतीय स्थान-मान "
                "पद्धति ने दुनिया क्यों जीती।"],
        },
    },
    ("fact", "geometry_origin"): {
        "en": {
            "again": [
                "One more detail: geometry was born from "
                "a practical problem — every year the "
                "Nile flooded Egyptian fields and wiped "
                "out their boundaries, so the land had "
                "to be measured and divided again. "
                "'Earth-measuring' was a real job."],
            "third": [
                "Word-building practice: 'geo' also "
                "opens geography (earth-writing) and "
                "geology (earth-study). Whenever you see "
                "geo-, think earth — the first half of "
                "geometry decodes itself."],
        },
        "roman": {
            "again": [
                "Ek aur baat: geometry ek asli zaroorat "
                "se paida hui thi — har saal Nile nadi "
                "Misr ke kheton me baadh laakar unki "
                "seemaen mita deti thi, toh zameen ko "
                "phir se naap kar baantna padta tha. "
                "'Dharti-naap' ek sach-much ka kaam "
                "tha."],
            "third": [
                "Shabd banane ki practice: 'geo' se "
                "geography (dharti ka varnan) aur "
                "geology (dharti ka adhyayan) bhi bante "
                "hai. Jab bhi geo- dikhe, dharti socho — "
                "geometry ka pehla hissa khud khul "
                "jayega."],
        },
        "dev": {
            "again": [
                "एक और बात: ज्यामिति एक असली ज़रूरत से "
                "पैदा हुई थी — हर साल Nile नदी मिस्र के "
                "खेतों में बाढ़ लाकर उनकी सीमाएँ मिटा "
                "देती थी, तो ज़मीन को फिर से मापकर "
                "बाँटना पड़ता था। 'धरती-माप' एक सचमुच "
                "का काम था।"],
            "third": [
                "शब्द बनाने की practice: 'geo' से "
                "geography (धरती का वर्णन) और geology "
                "(धरती का अध्ययन) भी बनते हैं। जब भी "
                "geo- दिखे, धरती सोचो — geometry का "
                "पहला हिस्सा ख़ुद खुल जाएगा।"],
        },
    },
    ("fact", "algebra_origin"): {
        "en": {
            "again": [
                "One more detail: al-Khwarizmi worked "
                "in Baghdad's House of Wisdom around "
                "820 CE. His book reached Europe in "
                "Latin translation, and for centuries "
                "European students learnt algebra from "
                "it."],
            "third": [
                "Decode the word once: 'al-jabr' means "
                "restoring — moving a subtracted term "
                "across and restoring it as added. "
                "Solve x − 7 = 5 by that one move: "
                "x = 12. You just used the word's own "
                "meaning."],
        },
        "roman": {
            "again": [
                "Ek aur baat: al-Khwarizmi lagbhag 820 "
                "CE me Baghdad ke 'House of Wisdom' "
                "(gyaan ke ghar) me kaam karte the. "
                "Unki kitab Latin anuvaad se Europe "
                "pahunchi, aur sadion tak European "
                "chhatra usi se algebra seekhte rahe."],
            "third": [
                "Shabd ko ek baar kholo: 'al-jabr' "
                "matlab bahaal karna — sameekaran me "
                "ghataaye hue pad ko dusri taraf le "
                "jaakar jod ke roop me bahaal karna. "
                "x − 7 = 5 ko usi ek chaal se hal karo: "
                "x = 12. Tumne shabd ka matlab hi use "
                "kar liya."],
        },
        "dev": {
            "again": [
                "एक और बात: अल-ख़्वारिज़्मी लगभग 820 ई. "
                "में बग़दाद के 'House of Wisdom' (ज्ञान "
                "के घर) में काम करते थे। उनकी पुस्तक "
                "Latin अनुवाद से यूरोप पहुँची, और सदियों "
                "तक यूरोपीय छात्र उसी से algebra सीखते "
                "रहे।"],
            "third": [
                "शब्द को एक बार खोलो: 'अल-जब्र' मतलब "
                "बहाल करना — समीकरण में घटाए हुए पद को "
                "दूसरी तरफ़ ले जाकर जोड़ के रूप में "
                "बहाल करना। x − 7 = 5 को उसी एक चाल से "
                "हल करो: x = 12। तुमने शब्द का मतलब ही "
                "उपयोग कर लिया।"],
        },
    },
    ("fact", "trigonometry_origin"): {
        "en": {
            "again": [
                "One more detail: the word 'sine' "
                "itself travelled — Sanskrit 'jya' "
                "became Arabic 'jiba', was misread as "
                "'jaib' (a bay, a fold), and Latin "
                "turned that into 'sinus'. Your sin "
                "button carries that whole journey."],
            "third": [
                "A memory hook: tri-gono-metry = "
                "three-angle-measure. Whenever a "
                "question gives a triangle and asks for "
                "a height or distance you cannot climb "
                "or cross — a tree, a tower, a river — "
                "it is trigonometry's home ground."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 'sine' shabd ne khud "
                "safar kiya hai — Sanskrit 'jya' Arabic "
                "me 'jiba' bana, galti se 'jaib' (khaadi "
                "ya teh) padha gaya, aur Latin ne use "
                "'sinus' bana diya. Tumhare sin button "
                "me wo poora safar chhupa hai."],
            "third": [
                "Ek yaad-hook: tri-gono-metry = "
                "teen-kon-maap. Jab bhi sawal me tribhuj "
                "ho aur aisi unchaai ya doori puchi jaye "
                "jahan chadh ya paar na sakte ho — ped, "
                "tower, nadi — wahi trigonometry ka apna "
                "maidan hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 'sine' शब्द ने ख़ुद सफ़र "
                "किया है — संस्कृत 'ज्या' अरबी में "
                "'जीबा' बना, ग़लती से 'जैब' (खाड़ी या "
                "तह) पढ़ा गया, और Latin ने उसे 'sinus' "
                "बना दिया। तुम्हारे sin button में वो "
                "पूरा सफ़र छुपा है।"],
            "third": [
                "एक याद-hook: tri-gono-metry = "
                "तीन-कोण-माप। जब भी सवाल में त्रिभुज हो "
                "और ऐसी ऊँचाई या दूरी पूछी जाए जहाँ चढ़ "
                "या पार न सकते हो — पेड़, tower, नदी — "
                "वही trigonometry का अपना मैदान है।"],
        },
    },
    ("fact", "maths_full_form"): {
        "en": {
            "again": [
                "One more detail: beware of made-up "
                "full forms floating around "
                "('M-A-T-H-S' backronyms). They are "
                "jokes, not history — in an exam or "
                "interview, 'short form of Mathematics' "
                "is the only correct answer."],
            "third": [
                "A word-family step: mathematika also "
                "gives us 'mathematical' and "
                "'mathematician'. And in Hindi, 'ganit' "
                "(गणित) comes from a root meaning 'to "
                "count' — both languages point at "
                "counting and learning."],
        },
        "roman": {
            "again": [
                "Ek aur baat: chaaron taraf ghumte "
                "banawati full form ('M-A-T-H-S' wale "
                "jode hue arth) se bacho. Wo mazak hai, "
                "itihaas nahi — exam ya interview me "
                "'Mathematics ka short form' hi "
                "ekmatra sahi jawab hai."],
            "third": [
                "Ek shabd-parivaar wala step: "
                "mathematika se hi 'mathematical' aur "
                "'mathematician' bane hai. Aur Hindi me "
                "'ganit' (गणित) ki jad ka matlab hai "
                "'ginna' — dono bhashayen ginati aur "
                "seekhne ki taraf ishara karti hai."],
        },
        "dev": {
            "again": [
                "एक और बात: चारों तरफ़ घूमते बनावटी full "
                "form ('M-A-T-H-S' वाले जोड़े हुए अर्थ) "
                "से बचो। वो मज़ाक है, इतिहास नहीं — "
                "exam या interview में 'Mathematics का "
                "short form' ही एकमात्र सही जवाब है।"],
            "third": [
                "एक शब्द-परिवार वाला step: mathematika "
                "से ही 'mathematical' और "
                "'mathematician' बने हैं। और हिंदी में "
                "'गणित' की जड़ का मतलब है 'गिनना' — "
                "दोनों भाषाएँ गिनती और सीखने की तरफ़ "
                "इशारा करती हैं।"],
        },
    },
    ("fact", "equals_sign"): {
        "en": {
            "again": [
                "One more detail: before Recorde, "
                "writers spelt the whole phrase out — "
                "'is equal to' — in every line. Imagine "
                "writing a full solution that way; his "
                "two lines saved mathematicians "
                "centuries of ink."],
            "third": [
                "Recorde's own reason, in the spirit of "
                "his words: he chose two parallel lines "
                "'because no two things can be more "
                "equal'. Quick check: in 7 = 7, is the "
                "= longer than either 7? Neither — "
                "that sameness is the point."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Recorde se pehle lekhak "
                "har line me poora vakya likhte the — "
                "'is equal to'. Socho poora hal usi "
                "tarah likhna pade; unki do rekhaon ne "
                "ganitgyon ki sadion ki syahi bachayi."],
            "third": [
                "Recorde ki apni wajah, unke shabdon ke "
                "bhaav me: unhone do samanantar rekhaen "
                "chuni 'kyunki do cheezein isse zyada "
                "barabar ho hi nahi sakti'. Jhatpat "
                "jaanch: 7 = 7 me = bada hai ya koi 7? "
                "Koi nahi — yahi barabari asal baat "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Recorde से पहले लेखक हर line "
                "में पूरा वाक्य लिखते थे — 'is equal "
                "to'। सोचो पूरा हल उसी तरह लिखना पड़े; "
                "उनकी दो रेखाओं ने गणितज्ञों की सदियों "
                "की स्याही बचाई।"],
            "third": [
                "Recorde की अपनी वजह, उनके शब्दों के "
                "भाव में: उन्होंने दो समांतर रेखाएँ "
                "चुनीं 'क्योंकि दो चीज़ें इससे ज़्यादा "
                "बराबर हो ही नहीं सकतीं'। झटपट जाँच: "
                "7 = 7 में = बड़ा है या कोई 7? कोई "
                "नहीं — यही बराबरी असल बात है।"],
        },
    },
    ("fact", "pi_day"): {
        "en": {
            "again": [
                "One more detail: 14 March is also "
                "Albert Einstein's birthday (born 14 "
                "March 1879) — so Pi Day quietly "
                "celebrates two kinds of genius at "
                "once."],
            "third": [
                "A Pi Day game students play: a 'piem' — "
                "write a line where each word's "
                "letter-count spells pi: 3, 1, 4, 1, "
                "5… Try making a five-word piem "
                "yourself; it fixes 3.1415 in memory "
                "forever."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 14 March Albert Einstein "
                "ka janmdin bhi hai (janm 14 March "
                "1879) — toh Pi Day chupke se ek saath "
                "do tarah ki pratibhaon ka jashn hai."],
            "third": [
                "Ek Pi Day khel jo chhatra khelte hai: "
                "'piem' — ek line likho jisme har shabd "
                "ke aksharon ki ginati pi banaye: 3, 1, "
                "4, 1, 5… Khud 5 shabdon ka piem banao; "
                "3.1415 hamesha ke liye yaad ho "
                "jayega."],
        },
        "dev": {
            "again": [
                "एक और बात: 14 मार्च Albert Einstein का "
                "जन्मदिन भी है (जन्म 14 मार्च 1879) — "
                "तो Pi Day चुपके से एक साथ दो तरह की "
                "प्रतिभाओं का जश्न है।"],
            "third": [
                "एक Pi Day खेल जो छात्र खेलते हैं: "
                "'piem' — एक line लिखो जिसमें हर शब्द "
                "के अक्षरों की गिनती pi बनाए: 3, 1, 4, "
                "1, 5… ख़ुद 5 शब्दों का piem बनाओ; "
                "3.1415 हमेशा के लिए याद हो जाएगा।"],
        },
    },
    ("fact", "polygons"): {
        "en": {
            "again": [
                "One more detail: the counting trick "
                "also works for angles — a polygon with "
                "n sides has interior angles summing to "
                "(n − 2) × 180°. Pentagon: 3 × 180° "
                "= 540°. The side-count runs the whole "
                "chapter."],
            "third": [
                "Quick practice, name them by sides "
                "alone: 3 triangle, 4 quadrilateral, 5 "
                "pentagon, 6 hexagon, 7 heptagon, 8 "
                "octagon, 9 nonagon, 10 decagon. Say "
                "the full run aloud once — it is a "
                "favourite one-mark question."],
        },
        "roman": {
            "again": [
                "Ek aur baat: ginati wali yehi trick "
                "konon par bhi chalti hai — n bhujaon "
                "wale bahubhuj ke antah-konon ka jod "
                "(n − 2) × 180° hota hai. Panchbhuj: "
                "3 × 180° = 540°. Bhujaon ki ginati "
                "poora chapter chalati hai."],
            "third": [
                "Jhatpat practice, sirf bhujaon se naam "
                "batao: 3 tribhuj, 4 chaturbhuj, 5 "
                "panchbhuj, 6 shatbhuj, 7 saptabhuj, 8 "
                "ashtabhuj, 9 navbhuj, 10 dashbhuj. "
                "Poori kataar ek baar zor se bolo — ye "
                "ek number ka pasandeeda sawal hai."],
        },
        "dev": {
            "again": [
                "एक और बात: गिनती वाली यही trick कोणों "
                "पर भी चलती है — n भुजाओं वाले बहुभुज "
                "के अंतःकोणों का जोड़ (n − 2) × 180° "
                "होता है। पंचभुज: 3 × 180° = 540°। "
                "भुजाओं की गिनती पूरा chapter चलाती "
                "है।"],
            "third": [
                "झटपट practice, सिर्फ़ भुजाओं से नाम "
                "बताओ: 3 त्रिभुज, 4 चतुर्भुज, 5 पंचभुज, "
                "6 षट्भुज, 7 सप्तभुज, 8 अष्टभुज, 9 "
                "नवभुज, 10 दशभुज। पूरी कतार एक बार "
                "ज़ोर से बोलो — यह एक अंक का पसंदीदा "
                "सवाल है।"],
        },
    },
    ("fact", "circumference_name"): {
        "en": {
            "again": [
                "One more detail: perimeter is the "
                "general word for the boundary length "
                "of ANY closed shape — square, triangle "
                "or circle. Circumference is just the "
                "special name we keep for the circle's "
                "perimeter."],
            "third": [
                "Quick practice: a circle's radius is 7 "
                "cm. Its perimeter — sorry, "
                "circumference — is 2 × (22/7) × 7 "
                "= 44 cm. Notice how the 7s cancel; "
                "exam setters love radius 7 for exactly "
                "this reason."],
        },
        "roman": {
            "again": [
                "Ek aur baat: perimeter (parimap) KISI "
                "BHI band aakriti ki seema-lambai ke "
                "liye aam shabd hai — varg, tribhuj ya "
                "vritt. Circumference bas vritt ke "
                "perimeter ka khaas naam hai."],
            "third": [
                "Jhatpat practice: ek vritt ki trijya 7 "
                "cm hai. Uska perimeter — matlab "
                "circumference — 2 × (22/7) × 7 = 44 "
                "cm. Dekho kaise 7 kat gaye; exam "
                "banane wale trijya 7 isiliye pasand "
                "karte hai."],
        },
        "dev": {
            "again": [
                "एक और बात: परिमाप (perimeter) किसी भी "
                "बंद आकृति की सीमा-लंबाई के लिए आम शब्द "
                "है — वर्ग, त्रिभुज या वृत्त। "
                "Circumference बस वृत्त के परिमाप का "
                "ख़ास नाम है।"],
            "third": [
                "झटपट practice: एक वृत्त की त्रिज्या 7 "
                "cm है। उसका परिमाप — मतलब "
                "circumference — 2 × (22/7) × 7 = 44 "
                "cm। देखो कैसे 7 कट गए; exam बनाने "
                "वाले त्रिज्या 7 इसीलिए पसंद करते "
                "हैं।"],
        },
    },
    ("fact", "largest_number"): {
        "en": {
            "again": [
                "One more detail: mathematicians still "
                "give huge numbers playful names — a "
                "googol is 1 followed by 100 zeros, and "
                "a googolplex is 1 followed by a googol "
                "of zeros. Even those giants are nowhere "
                "near 'largest'; there is always +1."],
            "third": [
                "A one-line proof to carry: suppose N "
                "is the largest number. Then N + 1 is "
                "bigger — contradiction. Whenever a "
                "question asks 'sabse bada…', run this "
                "+1 test before answering."],
        },
        "roman": {
            "again": [
                "Ek aur baat: ganitagya aaj bhi vishaal "
                "sankhyaon ko khel-ke naam dete hai — "
                "googol matlab 1 ke peeche 100 zero, "
                "aur googolplex matlab 1 ke peeche "
                "googol-bhar zero. Itne dev bhi 'sabse "
                "bade' ke paas nahi hai; hamesha +1 "
                "bacha hai."],
            "third": [
                "Ek line ka saboot hamesha ke liye: "
                "maan lo N sabse badi sankhya hai. Toh "
                "N + 1 usse bhi badi hai — virodh. Jab "
                "bhi sawal 'sabse bada…' puche, jawab "
                "se pehle ye +1 wala test chalao."],
        },
        "dev": {
            "again": [
                "एक और बात: गणितज्ञ आज भी विशाल "
                "संख्याओं को खेल-के नाम देते हैं — "
                "googol मतलब 1 के पीछे 100 शून्य, और "
                "googolplex मतलब 1 के पीछे googol-भर "
                "शून्य। इतने देव भी 'सबसे बड़े' के पास "
                "नहीं हैं; हमेशा +1 बचा है।"],
            "third": [
                "एक line का प्रमाण हमेशा के लिए: मान "
                "लो N सबसे बड़ी संख्या है। तो N + 1 "
                "उससे भी बड़ी है — विरोध। जब भी सवाल "
                "'सबसे बड़ा…' पूछे, जवाब से पहले यह +1 "
                "वाला test चलाओ।"],
        },
    },
    ("fact", "smallest_number"): {
        "en": {
            "again": [
                "One more detail: the negative side has "
                "no floor, but the positive side does "
                "have a smallest counting start — 1. "
                "The two directions behave differently, "
                "and mixing them up is the classic trap "
                "in this question."],
            "third": [
                "Sort it once, smallest to largest: "
                "−10, −2, 0, 3, 7. If that order felt "
                "instant, you already own the number "
                "line — and you can see why 'smallest "
                "number' overall can never exist."],
        },
        "roman": {
            "again": [
                "Ek aur baat: negative taraf koi farsh "
                "(floor) nahi hai, lekin positive taraf "
                "ginati ki sabse chhoti shuruaat hai — "
                "1. Dono dishayen alag vyavhaar karti "
                "hai, aur inhi ko milana is sawal ka "
                "classic jaal hai."],
            "third": [
                "Ek baar chhote se bade kram me sajao: "
                "−10, −2, 0, 3, 7. Agar ye kram turant "
                "laga, toh sankhya-rekha tumhari pakki "
                "hai — aur samajh aa gaya hoga ki kul "
                "milakar 'sabse chhoti sankhya' kyun ho "
                "hi nahi sakti."],
        },
        "dev": {
            "again": [
                "एक और बात: ऋणात्मक तरफ़ कोई फ़र्श "
                "(floor) नहीं है, लेकिन धनात्मक तरफ़ "
                "गिनती की सबसे छोटी शुरुआत है — 1। "
                "दोनों दिशाएँ अलग व्यवहार करती हैं, और "
                "इन्हीं को मिलाना इस सवाल का classic "
                "जाल है।"],
            "third": [
                "एक बार छोटे से बड़े क्रम में सजाओ: "
                "−10, −2, 0, 3, 7। अगर यह क्रम तुरंत "
                "लगा, तो संख्या-रेखा तुम्हारी पक्की है "
                "— और समझ आ गया होगा कि कुल मिलाकर "
                "'सबसे छोटी संख्या' क्यों हो ही नहीं "
                "सकती।"],
        },
    },
    ("history", "fermat"): {
        "en": {
            "again": [
                "One more detail: Fermat claimed he had "
                "a 'truly marvellous proof' that the "
                "margin was too narrow to hold. Wiles' "
                "proof runs to over 100 pages — the "
                "margin really was too small."],
            "third": [
                "The statement itself is easy to test: "
                "is 3³ + 4³ = 5³? 27 + 64 = 91, but "
                "5³ = 125. Close, not equal — and the "
                "theorem says cubes (or any higher "
                "power) NEVER fit exactly, for any "
                "numbers at all."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Fermat ne daava kiya tha "
                "ki unke paas ek 'sach-much adbhut "
                "saboot' hai, bas kinara (margin) use "
                "likhne ke liye chhota pad gaya. Wiles "
                "ka saboot 100 se zyada panno ka hai — "
                "kinara sach me chhota tha."],
            "third": [
                "Daava khud parkhna aasan hai: kya "
                "3³ + 4³ = 5³? 27 + 64 = 91, lekin "
                "5³ = 125. Paas, barabar nahi — aur "
                "pramey kehta hai ki ghano (ya unse "
                "unchi ghaaton) me aisa KABHI kisi bhi "
                "sankhya ke liye nahi hota."],
        },
        "dev": {
            "again": [
                "एक और बात: फ़र्मा ने दावा किया था कि "
                "उनके पास एक 'सचमुच अद्भुत प्रमाण' है, "
                "बस हाशिया उसे लिखने के लिए छोटा पड़ "
                "गया। Wiles का प्रमाण 100 से ज़्यादा "
                "पन्नों का है — हाशिया सच में छोटा "
                "था।"],
            "third": [
                "दावा ख़ुद परखना आसान है: क्या "
                "3³ + 4³ = 5³? 27 + 64 = 91, लेकिन "
                "5³ = 125। पास, बराबर नहीं — और प्रमेय "
                "कहता है कि घनों (या उनसे ऊँची घातों) "
                "में ऐसा कभी किसी भी संख्या के लिए "
                "नहीं होता।"],
        },
    },
    ("history", "coordinate_geometry"): {
        "en": {
            "again": [
                "One more detail: the story goes that "
                "Descartes got the idea watching a fly "
                "crawl on his ceiling — its position "
                "could be fixed by two distances, from "
                "two walls. The whole (x, y) system is "
                "that fly, made into maths."],
            "third": [
                "Practice the core move: the point "
                "(3, 4) sits 3 right and 4 up from the "
                "origin. Now you: where is (−2, 5)? Two "
                "left, five up — if you placed it "
                "instantly, Descartes' idea is already "
                "yours."],
        },
        "roman": {
            "again": [
                "Ek aur baat: katha hai ki Descartes ko "
                "ye vichaar chhat par rengti makkhi "
                "dekh kar aaya — uski jagah do divaaron "
                "se do doori me pakdi ja sakti thi. "
                "Poora (x, y) tantra wahi makkhi hai, "
                "ganit bani hui."],
            "third": [
                "Asal chaal ki practice: bindu (3, 4) "
                "mool-bindu se 3 dahine aur 4 upar hai. "
                "Ab tum batao: (−2, 5) kahan hai? Do "
                "baayein, paanch upar — turant rakh "
                "diya toh Descartes ka vichaar ab "
                "tumhara hai."],
        },
        "dev": {
            "again": [
                "एक और बात: कथा है कि देकार्त को यह "
                "विचार छत पर रेंगती मक्खी देखकर आया — "
                "उसकी जगह दो दीवारों से दो दूरी में "
                "पकड़ी जा सकती थी। पूरा (x, y) तंत्र "
                "वही मक्खी है, गणित बनी हुई।"],
            "third": [
                "असल चाल की practice: बिंदु (3, 4) "
                "मूल-बिंदु से 3 दाहिने और 4 ऊपर है। अब "
                "तुम बताओ: (−2, 5) कहाँ है? दो बाएँ, "
                "पाँच ऊपर — तुरंत रख दिया तो देकार्त "
                "का विचार अब तुम्हारा है।"],
        },
    },
    ("history", "venn"): {
        "en": {
            "again": [
                "One more detail: a two-circle Venn "
                "diagram makes exactly 4 regions — only "
                "A, only B, both, and neither (the part "
                "outside both circles). Almost every "
                "exam question on this topic is just "
                "counting those regions."],
            "third": [
                "Draw it yourself once: circle A = "
                "students who play cricket, circle B = "
                "students who play football. The "
                "overlap is 'both games'. Put three "
                "names in each region from your own "
                "class — the diagram will never feel "
                "abstract again."],
        },
        "roman": {
            "again": [
                "Ek aur baat: do golon wala Venn "
                "diagram thik 4 hisse banata hai — sirf "
                "A, sirf B, dono, aur dono se bahar "
                "wala. Is topic ka lagbhag har exam "
                "sawal bas inhi hisson ki ginati hai."],
            "third": [
                "Ek baar khud banao: gola A = cricket "
                "khelne wale chhatra, gola B = football "
                "khelne wale. Beech wala hissa 'dono "
                "khel' hai. Apni class ke 3-3 naam har "
                "hisse me rakho — diagram phir kabhi "
                "ajnabee nahi lagega."],
        },
        "dev": {
            "again": [
                "एक और बात: दो वृत्तों वाला Venn आरेख "
                "ठीक 4 हिस्से बनाता है — सिर्फ़ A, "
                "सिर्फ़ B, दोनों, और दोनों से बाहर "
                "वाला। इस topic का लगभग हर exam सवाल "
                "बस इन्हीं हिस्सों की गिनती है।"],
            "third": [
                "एक बार ख़ुद बनाओ: वृत्त A = cricket "
                "खेलने वाले छात्र, वृत्त B = football "
                "खेलने वाले। बीच वाला हिस्सा 'दोनों "
                "खेल' है। अपनी class के 3-3 नाम हर "
                "हिस्से में रखो — आरेख फिर कभी अजनबी "
                "नहीं लगेगा।"],
        },
    },
    ("history", "pascal_triangle"): {
        "en": {
            "again": [
                "One more detail: the triangle hides "
                "many patterns — each row's sum doubles "
                "(1, 2, 4, 8, 16…), the shallow "
                "diagonals build the Fibonacci numbers, "
                "and its rows give the coefficients of "
                "(a + b)ⁿ."],
            "third": [
                "Build three rows yourself: start with "
                "1; each new number is the sum of the "
                "two above it. The fifth row reads "
                "1, 4, 6, 4, 1 — and (a + b)⁴ opens "
                "with exactly those coefficients. You "
                "just used Pascal's triangle as a tool."],
        },
        "roman": {
            "again": [
                "Ek aur baat: is trikon me kai pattern "
                "chhupe hai — har kataar ka jod dugna "
                "hota hai (1, 2, 4, 8, 16…), tedhi "
                "diagonal Fibonacci sankhyayen banati "
                "hai, aur iski kataaren (a + b)ⁿ ke "
                "gunank deti hai."],
            "third": [
                "Teen kataaren khud banao: 1 se shuru "
                "karo; har nayi sankhya apne upar wali "
                "do ka jod hai. Paanchvi kataar padhti "
                "hai 1, 4, 6, 4, 1 — aur (a + b)⁴ "
                "bilkul inhi gunankon se khulta hai. "
                "Tumne Pascal ke trikon ko auzaar ki "
                "tarah use kar liya."],
        },
        "dev": {
            "again": [
                "एक और बात: इस त्रिभुज में कई pattern "
                "छुपे हैं — हर कतार का जोड़ दुगुना होता "
                "है (1, 2, 4, 8, 16…), टेढ़ी विकर्ण "
                "Fibonacci संख्याएँ बनाती है, और इसकी "
                "कतारें (a + b)ⁿ के गुणांक देती हैं।"],
            "third": [
                "तीन कतारें ख़ुद बनाओ: 1 से शुरू करो; "
                "हर नई संख्या अपने ऊपर वाली दो का जोड़ "
                "है। पाँचवीं कतार पढ़ती है 1, 4, 6, 4, "
                "1 — और (a + b)⁴ बिल्कुल इन्हीं गुणांकों "
                "से खुलता है। तुमने पास्कल के त्रिभुज "
                "को औज़ार की तरह उपयोग कर लिया।"],
        },
    },
    ("history", "trigonometry"): {
        "en": {
            "again": [
                "One more detail: Hipparchus built his "
                "chord table for astronomy — to predict "
                "the Sun, Moon and stars. Trigonometry "
                "was born looking at the sky, not at "
                "school triangles."],
            "third": [
                "A sky-practice: the angle up to a kite "
                "or a rooftop is an angle of elevation "
                "— the very first idea of this chapter. "
                "Next time you look up at something "
                "tall, you are standing inside a "
                "trigonometry question."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Hipparchus ne apni "
                "jeeva-saarani khagol (astronomy) ke "
                "liye banayi thi — Sooraj, Chaand aur "
                "taaron ki chaal pehle se batane ke "
                "liye. Trigonometry aasmaan dekhte hue "
                "paida hui thi, school ke tribhujon se "
                "nahi."],
            "third": [
                "Ek aasmaan-practice: patang ya chhat "
                "ki taraf upar wala kon 'unnayan kon' "
                "(angle of elevation) hai — is chapter "
                "ka sabse pehla vichaar. Agli baar kisi "
                "unchi cheez ko upar dekho, tum ek "
                "trigonometry sawal ke andar khade ho."],
        },
        "dev": {
            "again": [
                "एक और बात: हिप्पार्कस ने अपनी "
                "जीवा-सारणी खगोल (astronomy) के लिए "
                "बनाई थी — सूरज, चाँद और तारों की चाल "
                "पहले से बताने के लिए। त्रिकोणमिति "
                "आसमान देखते हुए पैदा हुई थी, school "
                "के त्रिभुजों से नहीं।"],
            "third": [
                "एक आसमान-practice: पतंग या छत की तरफ़ "
                "ऊपर वाला कोण 'उन्नयन कोण' (angle of "
                "elevation) है — इस chapter का सबसे "
                "पहला विचार। अगली बार किसी ऊँची चीज़ "
                "को ऊपर देखो, तुम एक trigonometry "
                "सवाल के अंदर खड़े हो।"],
        },
    },
    ("history", "logarithm"): {
        "en": {
            "again": [
                "One more detail: Napier spent about 20 "
                "years building his log tables by hand. "
                "Before calculators, those tables — and "
                "the slide rule built on them — were "
                "the engineer's computer for 300 years."],
            "third": [
                "Feel the trick once: log turns "
                "1000 × 100 into adding logs — 3 + 2 "
                "= 5 — and back to 10⁵ = 100,000. "
                "Multiplication became addition; that "
                "one swap is the whole invention."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Napier ne apni log "
                "saaraniyan haath se banane me lagbhag "
                "20 saal lagaye. Calculator se pehle "
                "wahi saaraniyan — aur unpar bani slide "
                "rule — 300 saal tak engineer ka "
                "computer rahi."],
            "third": [
                "Chaal ko ek baar mehsoos karo: log "
                "1000 × 100 ko logon ke jod me badal "
                "deta hai — 3 + 2 = 5 — aur wapas "
                "10⁵ = 100,000. Guna jod ban gayi; yahi "
                "ek badlaav poora aavishkaar hai."],
        },
        "dev": {
            "again": [
                "एक और बात: नेपियर ने अपनी log सारणियाँ "
                "हाथ से बनाने में लगभग 20 साल लगाए। "
                "Calculator से पहले वही सारणियाँ — और "
                "उनपर बनी slide rule — 300 साल तक "
                "engineer का computer रही।"],
            "third": [
                "चाल को एक बार महसूस करो: log "
                "1000 × 100 को logों के जोड़ में बदल "
                "देता है — 3 + 2 = 5 — और वापस "
                "10⁵ = 100,000। गुणा जोड़ बन गई; यही "
                "एक बदलाव पूरा आविष्कार है।"],
        },
    },
    ("history", "binary"): {
        "en": {
            "again": [
                "One more detail: Pingala's system was "
                "built for poetry — counting long and "
                "short syllable patterns. Each pattern "
                "of two choices is one binary digit in "
                "disguise; a 4-syllable line has "
                "2⁴ = 16 patterns, exactly like 4 bits."],
            "third": [
                "Count in binary once, on your fingers: "
                "thumb up = 1, index = 2, middle = 4, "
                "ring = 8, little = 16. Fingers up and "
                "down are 0s and 1s — with ten fingers "
                "you can count to 1023, not just 10."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Pingala ki paddhati "
                "kavita ke liye bani thi — lambe aur "
                "chhote akshar-chhandon ki ginati ke "
                "liye. Do chunavon wala har pattern "
                "asal me ek binary ank hai; 4 aksharon "
                "wali line ke 2⁴ = 16 pattern hote hai, "
                "bilkul 4 bits ki tarah."],
            "third": [
                "Ek baar ungliyon par binary gino: "
                "angutha upar = 1, tarjani = 2, beech "
                "wali = 4, anamika = 8, chhoti = 16. "
                "Upar-neeche ungliyan hi 0 aur 1 hai — "
                "das ungliyon se tum 1023 tak gin "
                "sakte ho, sirf 10 tak nahi."],
        },
        "dev": {
            "again": [
                "एक और बात: पिंगल की पद्धति कविता के "
                "लिए बनी थी — लंबे और छोटे अक्षर-छंदों "
                "की गिनती के लिए। दो चुनावों वाला हर "
                "pattern असल में एक binary अंक है; 4 "
                "अक्षरों वाली पंक्ति के 2⁴ = 16 pattern "
                "होते हैं, बिल्कुल 4 bits की तरह।"],
            "third": [
                "एक बार उँगलियों पर binary गिनो: अँगूठा "
                "ऊपर = 1, तर्जनी = 2, बीच वाली = 4, "
                "अनामिका = 8, छोटी = 16। ऊपर-नीचे "
                "उँगलियाँ ही 0 और 1 हैं — दस उँगलियों "
                "से तुम 1023 तक गिन सकते हो, सिर्फ़ 10 "
                "तक नहीं।"],
        },
    },
    ("advice", "practice"): {
        "en": {
            "again": [
                "One more thing that works: end each "
                "practice session by re-solving the "
                "FIRST question you did that day, from "
                "a blank page. If it flows, the day's "
                "work has actually landed."],
            "third": [
                "A 7-day experiment: same slot daily, "
                "phone in another room, 30 minutes, "
                "mistake notebook open beside you. "
                "After one week, compare your speed on "
                "the same 5 questions — the difference "
                "will convince you better than any "
                "advice."],
        },
        "roman": {
            "again": [
                "Ek aur kaam ki baat: har practice "
                "session ke aakhir me us din ka PEHLA "
                "sawal khaali panne par dobara karo. "
                "Agar wo behne lage, toh din ka kaam "
                "sach me utar gaya."],
            "third": [
                "Ek 7-din ka prayog: roz wahi samay, "
                "phone dusre kamre me, 30 minute, galti "
                "wali copy paas khuli. Ek hafte baad "
                "unhi 5 sawalon par apni raftaar milao "
                "— antar tumhe kisi salah se zyada "
                "samjhayega."],
        },
        "dev": {
            "again": [
                "एक और काम की बात: हर अभ्यास सत्र के अंत "
                "में उस दिन का पहला प्रश्न ख़ाली पन्ने "
                "पर दोबारा कीजिए। अगर वह बहने लगे, तो "
                "दिन का काम सच में उतर गया।"],
            "third": [
                "एक 7-दिन का प्रयोग: रोज़ वही समय, phone "
                "दूसरे कमरे में, 30 minute, ग़लती वाली "
                "कॉपी पास खुली। एक हफ़्ते बाद उन्हीं 5 "
                "प्रश्नों पर अपनी रफ़्तार मिलाइए — अंतर "
                "आपको किसी सलाह से ज़्यादा समझाएगा।"],
        },
    },
    ("advice", "exam_solve"): {
        "en": {
            "again": [
                "One more thing: write the question "
                "number clearly before each answer and "
                "leave two blank lines between answers. "
                "Examiners reward papers they can "
                "follow — and you can find things fast "
                "during revision."],
            "third": [
                "A small rehearsal before the real "
                "paper: take one old paper, set a timer "
                "for half its time, and practise ONLY "
                "the marking round — ✓ ? ✗ on every "
                "question in 5 minutes. The habit of "
                "choosing is itself a scoring skill."],
        },
        "roman": {
            "again": [
                "Ek aur baat: har jawab se pehle sawal "
                "ka number saaf likho aur do jawabon ke "
                "beech do khaali line chhodo. Examiner "
                "ko wahi paper pasand aata hai jo use "
                "samajh aaye — aur revision me tumhe "
                "cheezein turant milti hai."],
            "third": [
                "Asli paper se pehle ek chhoti "
                "rehearsal: ek purana paper lo, aadha "
                "samay ka timer lagao, aur sirf nishan "
                "lagane wala round practice karo — har "
                "sawal par 5 minute me ✓ ? ✗. Chunne ki "
                "aadat khud ek number-dilane wala hunar "
                "hai."],
        },
        "dev": {
            "again": [
                "एक और बात: हर जवाब से पहले सवाल का नंबर "
                "साफ़ लिखिए और दो जवाबों के बीच दो "
                "ख़ाली पंक्तियाँ छोड़िए। परीक्षक को "
                "वही paper पसंद आता है जो उसे समझ आए — "
                "और दोहराव में आपको चीज़ें तुरंत मिलती "
                "हैं।"],
            "third": [
                "असली paper से पहले एक छोटी rehearsal: "
                "एक पुराना paper लीजिए, आधे समय का "
                "timer लगाइए, और सिर्फ़ निशान लगाने "
                "वाला चरण अभ्यास कीजिए — हर प्रश्न पर "
                "5 मिनट में ✓ ? ✗। चुनने की आदत ख़ुद "
                "एक अंक-दिलाने वाला हुनर है।"],
        },
    },
    ("advice", "fear"): {
        "en": {
            "again": [
                "One more thing: fear shrinks when the "
                "questions shrink. If a full question "
                "scares you, do only its first line "
                "today. A half-finished question is "
                "still progress; an untouched one is "
                "the only real loss."],
            "third": [
                "A 10-minute daily drill for one week: "
                "3 questions you find easy, 1 you find "
                "medium, none hard. Note how many you "
                "finish. Watching that number grow is "
                "the fear leaving — in writing."],
        },
        "roman": {
            "again": [
                "Ek aur baat: dar tab ghat-ta hai jab "
                "sawal chhote hote hai. Agar poora "
                "sawal dara raha hai, toh aaj sirf uski "
                "pehli line karo. Aadha hua sawal bhi "
                "pragati hai; bina chhua sawal hi asli "
                "nuksaan hai."],
            "third": [
                "Ek hafte ka roz 10-minute drill: 3 "
                "sawal jo aasan lage, 1 jo beech ka "
                "lage, kathin ek bhi nahi. Kitne poore "
                "hue, likhte jao. Us badhti ginati ko "
                "dekhna hi dar ka jaana hai — kagaz "
                "par."],
        },
        "dev": {
            "again": [
                "एक और बात: डर तब घटता है जब प्रश्न "
                "छोटे होते हैं। अगर पूरा प्रश्न डरा "
                "रहा है, तो आज सिर्फ़ उसकी पहली पंक्ति "
                "कीजिए। आधा हुआ प्रश्न भी प्रगति है; "
                "बिना छुआ प्रश्न ही असली नुक़सान है।"],
            "third": [
                "एक हफ़्ते का रोज़ 10-minute drill: 3 "
                "प्रश्न जो आसान लगें, 1 जो बीच का लगे, "
                "कठिन एक भी नहीं। कितने पूरे हुए, "
                "लिखते जाइए। उस बढ़ती गिनती को देखना "
                "ही डर का जाना है — काग़ज़ पर।"],
        },
    },
    ("advice", "formulae"): {
        "en": {
            "again": [
                "One more thing: group formulae by "
                "family, not by chapter — all the area "
                "formulae together, all the identities "
                "together. In the exam your brain "
                "searches by family, so store them "
                "that way."],
            "third": [
                "Test one formula the strong way: "
                "close the book and DERIVE it once on "
                "paper, slowly. If the derivation "
                "flows, you no longer 'remember' the "
                "formula — you own it, and exam nerves "
                "cannot take it."],
        },
        "roman": {
            "again": [
                "Ek aur baat: formulae ko chapter ke "
                "hisaab se nahi, parivaar ke hisaab se "
                "jodo — saare kshetrafal wale ek saath, "
                "saari sarvsamikayen (identities) ek "
                "saath. Exam me dimag parivaar se "
                "dhoondhta hai, isiliye usi tarah "
                "rakho."],
            "third": [
                "Ek formula ko mazboot tareeke se "
                "parkho: kitab band karke use kagaz "
                "par ek baar dhire-dhire BANAO "
                "(derive karo). Agar banana behne "
                "lage, toh tum formula 'yaad' nahi "
                "karte — use apna chuke ho, aur exam "
                "ki ghabrahat use chheen nahi sakti."],
        },
        "dev": {
            "again": [
                "एक और बात: सूत्रों को chapter के हिसाब "
                "से नहीं, परिवार के हिसाब से जोड़िए — "
                "सारे क्षेत्रफल वाले एक साथ, सारी "
                "सर्वसमिकाएँ (identities) एक साथ। "
                "परीक्षा में दिमाग़ परिवार से खोजता "
                "है, इसलिए उसी तरह रखिए।"],
            "third": [
                "एक सूत्र को मज़बूत तरीके से परखिए: "
                "पुस्तक बंद करके उसे काग़ज़ पर एक बार "
                "धीरे-धीरे बनाइए (derive कीजिए)। अगर "
                "बनाना बहने लगे, तो तुम सूत्र 'याद' "
                "नहीं करते — उसे अपना चुके हो, और "
                "परीक्षा की घबराहट उसे छीन नहीं "
                "सकती।"],
        },
    },
    ("advice", "weak"): {
        "en": {
            "again": [
                "One more thing: pick ONE weak "
                "chapter, not five. Two weeks on a "
                "single chapter gives a visible win, "
                "and visible wins are what pull the "
                "next chapter along."],
            "third": [
                "A base-check you can do today: write "
                "tables 12 to 19 from memory, then 10 "
                "fraction additions. Every stumble "
                "marks an exact repair spot — your "
                "weakness stops being a fog and "
                "becomes a list."],
        },
        "roman": {
            "again": [
                "Ek aur baat: paanch nahi, sirf EK "
                "kamzor chapter chuno. Ek chapter par "
                "do hafte ek dikhai dene wali jeet dete "
                "hai, aur dikhai dene wali jeet hi agle "
                "chapter ko kheenchti hai."],
            "third": [
                "Ek base-jaanch jo aaj ho sakti hai: "
                "12 se 19 tak pahade yaad se likho, "
                "phir 10 bhinnon ke jod karo. Har atak "
                "ek pakki marammat-jagah batati hai — "
                "kamzori dhundh nahi rehti, list ban "
                "jati hai."],
        },
        "dev": {
            "again": [
                "एक और बात: पाँच नहीं, सिर्फ़ एक "
                "कमज़ोर chapter चुनिए। एक chapter पर "
                "दो हफ़्ते एक दिखाई देने वाली जीत देते "
                "हैं, और दिखाई देने वाली जीत ही अगले "
                "chapter को खींचती है।"],
            "third": [
                "एक base-जाँच जो आज हो सकती है: 12 से "
                "19 तक पहाड़े याद से लिखिए, फिर 10 "
                "भिन्नों के जोड़ कीजिए। हर अटक एक "
                "पक्की मरम्मत-जगह बताती है — कमज़ोरी "
                "धुंध नहीं रहती, सूची बन जाती है।"],
        },
    },
    ("advice", "revision"): {
        "en": {
            "again": [
                "One more thing: revise the SAME "
                "evening for just 5 minutes — glance "
                "through what you studied that day "
                "before sleeping. That tiny same-day "
                "round makes the 1-day revision twice "
                "as strong."],
            "third": [
                "Make revision visible: a wall "
                "calendar with three boxes per topic — "
                "1 day, 1 week, 1 month — ticked as "
                "you finish each round. An unticked "
                "box is an honest reminder no app can "
                "give you."],
        },
        "roman": {
            "again": [
                "Ek aur baat: USI shaam sirf 5 minute "
                "dohra lo — sone se pehle us din ki "
                "padhai par ek nazar. Wahi chhota "
                "usi-din wala round 1-din wali "
                "revision ko dugna mazboot kar deta "
                "hai."],
            "third": [
                "Revision ko dikhai dene wala banao: "
                "ek deewar calendar, har topic ke liye "
                "teen khaane — 1 din, 1 hafta, 1 "
                "mahina — har round ke baad tick. Bina "
                "tick wala khaana ek imaandaar "
                "yaad-dihani hai jo koi app nahi de "
                "sakta."],
        },
        "dev": {
            "again": [
                "एक और बात: उसी शाम सिर्फ़ 5 मिनट दोहरा "
                "लीजिए — सोने से पहले उस दिन की पढ़ाई "
                "पर एक नज़र। वही छोटा उसी-दिन वाला चरण "
                "1-दिन वाले दोहराव को दुगुना मज़बूत कर "
                "देता है।"],
            "third": [
                "दोहराव को दिखाई देने वाला बनाइए: एक "
                "दीवार calendar, हर topic के लिए तीन "
                "ख़ाने — 1 दिन, 1 हफ़्ता, 1 महीना — हर "
                "चरण के बाद tick। बिना tick वाला ख़ाना "
                "एक ईमानदार याद-दिहानी है जो कोई app "
                "नहीं दे सकता।"],
        },
    },
    ("advice", "silly_mistakes"): {
        "en": {
            "again": [
                "One more thing: read the question "
                "TWICE before touching the pen — once "
                "for what it asks, once for the "
                "numbers. Half of all copying errors "
                "die at that second reading."],
            "third": [
                "A 3-line ritual for every answer: "
                "units written? sign sane? size "
                "believable? Run it like a pilot's "
                "checklist for one full test and count "
                "your silly mistakes before and after "
                "— the drop will surprise you."],
        },
        "roman": {
            "again": [
                "Ek aur baat: pen uthane se pehle "
                "sawal ko DO baar padho — ek baar kya "
                "pucha hai uske liye, dusri baar "
                "sankhyaon ke liye. Copy ki aadhi "
                "galtiyaan usi dusri baar padhne par "
                "mar jati hai."],
            "third": [
                "Har jawab ke liye 3-line ki vidhi: "
                "unit likhi? sign theek? size "
                "vishwas-yogya? Ise pilot ki checklist "
                "ki tarah ek poore test me chalao aur "
                "pehle-baad ki silly mistakes gino — "
                "girawat tumhe hairaan kar degi."],
        },
        "dev": {
            "again": [
                "एक और बात: pen उठाने से पहले प्रश्न "
                "को दो बार पढ़िए — एक बार क्या पूछा है "
                "उसके लिए, दूसरी बार संख्याओं के लिए। "
                "copy की आधी ग़लतियाँ उसी दूसरी बार "
                "पढ़ने पर मर जाती हैं।"],
            "third": [
                "हर जवाब के लिए 3-पंक्ति की विधि: "
                "इकाई लिखी? चिह्न ठीक? आकार "
                "विश्वास-योग्य? इसे pilot की checklist "
                "की तरह एक पूरे test में चलाइए और "
                "पहले-बाद की silly mistakes गिनिए — "
                "गिरावट आपको हैरान कर देगी।"],
        },
    },
    ("advice", "speed"): {
        "en": {
            "again": [
                "One more thing: learn the complements "
                "to 100 — 37 needs 63, 48 needs 52. "
                "Subtraction and money sums turn "
                "instant when the partner number is "
                "already in your head."],
            "third": [
                "A timed ladder for this week: day 1, "
                "twenty additions; day 2, twenty "
                "subtractions; day 3, mixed — same 10 "
                "minutes, note the count daily. Speed "
                "you can SEE growing is speed that "
                "stays."],
        },
        "roman": {
            "again": [
                "Ek aur baat: 100 ke poorak "
                "(complements) seekh lo — 37 ko 63 "
                "chahiye, 48 ko 52. Ghataav aur paison "
                "ke hisaab turant ho jate hai jab "
                "jodi-sankhya pehle se dimag me ho."],
            "third": [
                "Is hafte ki samay wali seedhi: din 1, "
                "bees jod; din 2, bees ghataav; din 3, "
                "mile-jule — wahi 10 minute, ginati "
                "roz likho. Jo raftaar DIKHTI hui "
                "badhti hai, wahi tikti hai."],
        },
        "dev": {
            "again": [
                "एक और बात: 100 के पूरक (complements) "
                "सीख लीजिए — 37 को 63 चाहिए, 48 को 52। "
                "घटाव और पैसों के हिसाब तुरंत हो जाते "
                "हैं जब जोड़ी-संख्या पहले से दिमाग़ "
                "में हो।"],
            "third": [
                "इस हफ़्ते की समय वाली सीढ़ी: दिन 1, "
                "बीस जोड़; दिन 2, बीस घटाव; दिन 3, "
                "मिले-जुले — वही 10 मिनट, गिनती रोज़ "
                "लिखिए। जो रफ़्तार दिखती हुई बढ़ती "
                "है, वही टिकती है।"],
        },
    },
})

# Generic pools per kind — every line stays true for ANY
# entry of its kind (no claim about the entry itself).
_META_GENERIC = {
    "history": {
        "en": {
            "again": [
                "A memory trick for every 'who' question: "
                "say the pair out loud once — the name with "
                "the work, as one phrase. Exam who-questions "
                "are answered by exactly that pair.",
                "One more way to keep it: names fade, "
                "stories stay — attach one small story to "
                "the name and it will not leave you."],
            "third": [
                "Your turn, one line only: without looking, "
                "say what this person gave to maths. If you "
                "can say it, it is yours for good.",
                "A small challenge: explain this person's "
                "work to a friend in your own words "
                "tomorrow. If they understand it, you have "
                "understood it twice."],
        },
        "roman": {
            "again": [
                "Har 'kisne' wale sawal ki yaad-trick: jode "
                "ko ek baar zor se bolo — naam ke saath "
                "uska kaam, ek hi saans me. Exam ke "
                "who-sawal bilkul isi jode se bante hai.",
                "Yaad rakhne ka ek aur tareeka: naam bhul "
                "jate hai, kahani nahi — naam ke saath ek "
                "chhoti kahani jod do, phir ye nahi "
                "chhutega."],
            "third": [
                "Ab tumhari baari, sirf ek line: bina dekhe "
                "batao — is vyakti ne maths ko kya diya? "
                "Bol sakte ho toh ye hamesha ke liye "
                "tumhara ho gaya.",
                "Ek chhota challenge: kal is vyakti ke kaam "
                "ko apne shabdon me kisi dost ko samjhao. "
                "Use samajh aa gaya toh tumhe do baar "
                "samajh aa gaya."],
        },
        "dev": {
            "again": [
                "हर 'किसने' वाले सवाल की याद-trick: जोड़े "
                "को एक बार ज़ोर से बोलो — नाम के साथ उसका "
                "काम, एक ही साँस में। Exam के who-सवाल "
                "बिल्कुल इसी जोड़े से बनते हैं।",
                "याद रखने का एक और तरीका: नाम भूल जाते "
                "हैं, कहानी नहीं — नाम के साथ एक छोटी "
                "कहानी जोड़ दो, फिर ये नहीं छूटेगा।"],
            "third": [
                "अब तुम्हारी बारी, सिर्फ़ एक line: बिना "
                "देखे बताओ — इस व्यक्ति ने maths को क्या "
                "दिया? बोल सकते हो तो ये हमेशा के लिए "
                "तुम्हारा हो गया।",
                "एक छोटा challenge: कल इस व्यक्ति के काम "
                "को अपने शब्दों में किसी दोस्त को समझाओ। "
                "उसे समझ आ गया तो तुम्हें दो बार समझ आ "
                "गया।"],
        },
    },
    "fact": {
        "en": {
            "again": [
                "A way to make facts stick: say the fact "
                "once as a question and answer it yourself "
                "— 'sabse chhota …?' Facts you ask yourself "
                "stay far longer than facts you only read.",
                "One more grip on it: connect the fact to "
                "its neighbour — smallest with largest, "
                "first with last. Pairs are remembered; "
                "lonely facts are forgotten."],
            "third": [
                "Now the reverse practice: make the "
                "opposite question from this fact (sabse "
                "bada ↔ sabse chhota) and answer that too. "
                "Both directions clear means the fact is "
                "truly yours.",
                "A 10-second test: close your eyes and "
                "recall this fact once more, then check. "
                "That one recall does more than five "
                "re-readings."],
        },
        "roman": {
            "again": [
                "Facts pakke karne ka tareeka: fact ko ek "
                "baar sawal bana kar khud se pucho aur khud "
                "jawab do. Jo fact tum khud se puchte ho, "
                "wo sirf padhe hue fact se kahin zyada "
                "tikta hai.",
                "Ise pakadne ka ek aur tareeka: fact ko "
                "uske padosi se jodo — sabse chhota ke saath "
                "sabse bada, pehla ke saath aakhiri. Jode "
                "yaad rehte hai; akele fact bhul jate hai."],
            "third": [
                "Ab ulti practice: is fact ka ulta sawal "
                "banao (sabse bada ↔ sabse chhota) aur uska "
                "jawab bhi do. Dono disha saaf matlab fact "
                "sach me tumhara.",
                "10 second ka test: aankhein band karke is "
                "fact ko ek baar aur yaad karo, phir mila "
                "kar dekho. Wo ek yaad, paanch baar padhne "
                "se zyada kaam karti hai."],
        },
        "dev": {
            "again": [
                "Facts पक्के करने का तरीका: fact को एक बार "
                "सवाल बना कर ख़ुद से पूछो और ख़ुद जवाब दो। "
                "जो fact तुम ख़ुद से पूछते हो, वो सिर्फ़ "
                "पढ़े हुए fact से कहीं ज़्यादा टिकता है।",
                "इसे पकड़ने का एक और तरीका: fact को उसके "
                "पड़ोसी से जोड़ो — सबसे छोटा के साथ सबसे "
                "बड़ा, पहला के साथ आख़िरी। जोड़े याद रहते "
                "हैं; अकेले fact भूल जाते हैं।"],
            "third": [
                "अब उल्टी practice: इस fact का उल्टा सवाल "
                "बनाओ (सबसे बड़ा ↔ सबसे छोटा) और उसका जवाब "
                "भी दो। दोनों दिशा साफ़ मतलब fact सच में "
                "तुम्हारा।",
                "10 second का test: आँखें बंद करके इस fact "
                "को एक बार और याद करो, फिर मिला कर देखो। "
                "वो एक याद, पाँच बार पढ़ने से ज़्यादा काम "
                "करती है।"],
        },
    },
    "advice": {
        "en": {
            "again": [
                "One more small habit that quietly works: "
                "before starting, spend just 2 minutes "
                "revising yesterday's work — those 2 minutes "
                "join today's session to yesterday's.",
                "And one more: keep your phone in another "
                "room for the first 25 minutes. Willpower "
                "tires; distance does not."],
            "third": [
                "A 7-day mini challenge: apply this advice "
                "on just ONE chapter for a week, then judge "
                "it. Advice tested on one chapter beats "
                "advice collected for ten.",
                "Your practice step: write today's smallest "
                "possible version of this advice — so small "
                "you cannot fail it — and do only that "
                "today."],
        },
        "roman": {
            "again": [
                "Ek aur chhoti aadat jo chup-chaap kaam "
                "karti hai: shuru karne se pehle sirf 2 "
                "minute kal ka kaam dohra lo — ye 2 minute "
                "aaj ki baithak ko kal se jod dete hai.",
                "Aur ek: pehle 25 minute phone dusre kamre "
                "me rakho. Ichha-shakti thak jati hai, doori "
                "nahi thakti."],
            "third": [
                "7 din ka mini challenge: is salah ko sirf "
                "EK chapter par ek hafta aazmao, phir "
                "parkho. Ek chapter par aazmai salah, das "
                "ke liye ikatthi salah se behtar hai.",
                "Tumhara practice step: is salah ka aaj ke "
                "liye sabse chhota roop likho — itna chhota "
                "ki fail ho hi na sako — aur aaj sirf wahi "
                "karo."],
        },
        "dev": {
            "again": [
                "एक और छोटी आदत जो चुप-चाप काम करती है: "
                "शुरू करने से पहले सिर्फ़ 2 minute कल का "
                "काम दोहरा लो — ये 2 minute आज की बैठक को "
                "कल से जोड़ देते हैं।",
                "और एक: पहले 25 minute phone दूसरे कमरे में "
                "रखो। इच्छा-शक्ति थक जाती है, दूरी नहीं "
                "थकती।"],
            "third": [
                "7 दिन का mini challenge: इस सलाह को "
                "सिर्फ़ एक chapter पर एक हफ़्ता आज़माओ, "
                "फिर परखो। एक chapter पर आज़माई सलाह, दस "
                "के लिए इकट्ठी सलाह से बेहतर है।",
                "तुम्हारा practice step: इस सलाह का आज के "
                "लिए सबसे छोटा रूप लिखो — इतना छोटा कि "
                "fail हो ही न सको — और आज सिर्फ़ वही करो।"],
        },
    },
}


def _meta_stable_offset(text):
    """A small stable offset per entry id, so two
    different topics sharing a generic pool do not rotate
    in lockstep for the same student."""
    return sum((i + 1) * ord(ch) for i, ch in
               enumerate(str(text))) % 7


def meta_variation(kind, entry_id, flavour, count):
    """The Wave 178 extra lines for one knowledge entry
    (kind "history" / "fact" / "advice") at one
    ask-count: count 2 -> "again" (a fresh related
    detail / tip); count >= 3 -> "third" (deeper fact /
    practice). Authored lines win; the kind's generic
    pool covers the rest. Rotates with the count so
    consecutive repeats keep differing. [] only when
    nothing honest can be added (unknown kind)."""
    if count < 2:
        return []
    if flavour not in ("en", "roman", "dev"):
        flavour = "en"
    level = "again" if count == 2 else "third"
    table = META_VARIATIONS.get((kind, entry_id)) or {}
    lines = list(((table.get(flavour) or {}).get(level))
                 or ((table.get("en") or {}).get(level))
                 or [])
    if not lines:
        pool = ((_META_GENERIC.get(kind) or {})
                .get(flavour) or {})
        lines = list(pool.get(level) or [])
    if not lines:
        return []
    if count >= 4:
        # Wave 200: deepen long repeat runs. From the 4th
        # ask on, the authored "third" lines alone would
        # repeat (rotation cannot move a short list), so
        # one line from the kind's generic "third" pool —
        # lines written true for ANY entry of the kind —
        # joins them, rotated by the count. Consecutive
        # serves now differ in their extra lines
        # themselves, not only in repeat.py's opener.
        pool = ((_META_GENERIC.get(kind) or {})
                .get(flavour) or {})
        generic = [ln for ln in (pool.get("third") or [])
                   if ln not in lines]
        if generic:
            pick = generic[(count - 4
                            + _meta_stable_offset(entry_id))
                           % len(generic)]
            lines = lines + [pick]
    start = (count - 2 + _meta_stable_offset(entry_id)) \
        % len(lines)
    return lines[start:] + lines[:start]
