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
                     "0", "०"),
        "en": {
            "answer": "Zero — developed in India; Brahmagupta "
                      "first wrote its rules (628 CE)",
            "steps": [
                "India gave the world zero as a real number, "
                "not just an empty place in a number.",
                "Aryabhata (5th century CE) used a place-value "
                "system that worked with zero.",
                "Brahmagupta, in his book Brahmasphutasiddhanta "
                "(628 CE), first gave clear rules for adding, "
                "subtracting and multiplying with zero.",
                "Short me: zero is India's gift to maths.",
            ],
        },
        "roman": {
            "answer": "Zero — India me bana; iske niyam sabse "
                      "pehle Brahmagupta ne diye (628 CE)",
            "steps": [
                "Duniya ko zero ek asal number ke roop me India "
                "ne diya — sirf khaali jagah ke roop me nahi.",
                "Aryabhata (5th century) ne place-value system "
                "me zero ka istemal kiya tha.",
                "Brahmagupta ne apni kitab Brahmasphutasiddhanta "
                "(628 CE) me zero ke jod-ghata-guna ke saaf "
                "niyam sabse pehle diye.",
                "Short me: zero India ki den hai.",
            ],
        },
        "dev": {
            "answer": "शून्य — भारत में विकसित; इसके नियम सबसे "
                      "पहले ब्रह्मगुप्त ने दिए (628 ई.)",
            "steps": [
                "दुनिया को शून्य एक असली संख्या के रूप में भारत "
                "ने दिया — सिर्फ़ खाली स्थान के रूप में नहीं।",
                "आर्यभट (5वीं शताब्दी) ने स्थानीय-मान प्रणाली "
                "में शून्य का उपयोग किया था।",
                "ब्रह्मगुप्त ने अपनी पुस्तक ब्राह्मस्फुटसिद्धांत "
                "(628 ई.) में शून्य के जोड़, घटाव और गुणा के "
                "स्पष्ट नियम सबसे पहले दिए।",
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
                     "ख्वारिज़्मी"),
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
                     "ज्यामिति के पिता"),
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
        "en": {
            "answer": "π (pi) — calculated first with real "
                      "accuracy by Archimedes (~250 BCE); "
                      "Aryabhata gave 3.1416",
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
            "answer": "π (pi) — sahi maan sabse pehle Archimedes "
                      "ne nikala (~250 BCE); Aryabhata ne 3.1416 "
                      "diya",
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
            "answer": "π (पाई) — सही मान सबसे पहले आर्किमिडीज़ "
                      "ने निकाला (~250 ई.पू.); आर्यभट ने 3.1416 "
                      "दिया",
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
        "keywords": ("ramanujan", "रामानुजन"),
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
        "keywords": ("brahmagupta", "ब्रह्मगुप्त"),
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
                     "गणित के पिता"),
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
    r"|ke beech")


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
                     "प्राकृतिक संख्या", "natural sankhya"),
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
                "matlab kya", "meaning", "word"),
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
                     "bijganit"),
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
            "kaha se", "kahan se", "shabd", "naam")):
        flavour = "roman"
    # History first: a who-shaped ask about a curated
    # topic/person is answered by the FACT layer, before
    # any concept card can serve the WHAT instead.
    if _has_who_shape(q):
        for entry in HISTORY:
            if _entry_hit(q, entry):
                return _result("history", entry, flavour)
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
    if _has_who_shape(q) and (
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
)
_KNOWLEDGE_SHAPE_EN = re.compile(
    r"\b(who|why|when|what|largest|smallest|biggest|"
    r"how many|invent\w*|discover\w*|origin)\b")
_KNOWLEDGE_TOPIC_WORDS = _MATHS_SIGNALS + (
    "zero", "shunya", "शून्य", "prime", "composite",
    "abhaajya", "अभाज्य", "infinity", "anant", "अनंत",
    "roman", "crore", "lakh", "million", "billion",
    "dozen", "gross", "decimal", "angle", "kon", "कोण",
    "triangle", "tribhuj", "त्रिभुज", "fibonacci",
    "calculator", "abacus", "vedic", "euler", "gauss",
    "newton", "archimedes", "leibniz", "symbol", "sign",
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
    shape = _has_who_shape(q) \
        or _KNOWLEDGE_SHAPE_EN.search(q) is not None \
        or any(w in q for w in _KNOWLEDGE_SHAPE_PHRASES)
    if not shape:
        return False
    return any(w in q for w in _KNOWLEDGE_TOPIC_WORDS) \
        or any(_entry_hit(q, e) for e in HISTORY) \
        or any(_fact_hit(q, e) for e in FACTS)


__all__ = ["HISTORY", "FACTS", "ADVICE", "meta_result",
           "is_meta_shaped", "is_knowledge_shaped",
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
            "again": [
                "One more detail: Aryabhata's value 3.1416 "
                "was so accurate that it stayed in use for "
                "centuries — he found it by measuring "
                "circles with great care."],
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
                "Ek aur baat: Aryabhata ki value 3.1416 itni "
                "sateek thi ki sadion tak chalti rahi — "
                "unhone golon ko bahut dhyaan se naap kar ye "
                "nikali thi."],
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
                "एक और बात: Aryabhata की value 3.1416 इतनी "
                "सटीक थी कि सदियों तक चलती रही — उन्होंने "
                "गोलों को बहुत ध्यान से नाप कर ये निकाली "
                "थी।"],
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
            "third": [
                "A Lilavati-flavoured practice: a swarm of "
                "bees — half of them on one flower, and 5 "
                "left over. If the whole swarm is 15, how "
                "many sit on the flower? (Answer: 10.) That "
                "playful style is Bhaskara's gift."],
        },
        "roman": {
            "again": [
                "Ek aur baat: Lilavati kavita me likhi gayi "
                "hai, aur kai sawal ek ladki ko sambodhit "
                "hai — 'O sundari, batao…' 900 saal pehle "
                "maths ek kahani ki tarah."],
            "third": [
                "Lilavati ke andaaz ki ek practice: "
                "madhumakhkhiyon ka jhund — aadhi ek phool "
                "par baithi, 5 bachi rahi. Poora jhund 15 "
                "hai toh phool par kitni hai? (Jawab: 10.) "
                "Ye khel-bhara andaaz Bhaskara ki den hai."],
        },
        "dev": {
            "again": [
                "एक और बात: Lilavati कविता में लिखी गई है, "
                "और कई सवाल एक लड़की को संबोधित हैं — 'O "
                "सुंदरी, बताओ…' 900 साल पहले maths एक कहानी "
                "की तरह।"],
            "third": [
                "Lilavati के अंदाज़ की एक practice: "
                "मधुमक्खियों का झुंड — आधी एक फूल पर बैठीं, "
                "5 बची रहीं। पूरा झुंड 15 है तो फूल पर "
                "कितनी हैं? (जवाब: 10.) ये खेल-भरा अंदाज़ "
                "Bhaskara की देन है।"],
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
    start = (count - 2 + _meta_stable_offset(entry_id)) \
        % len(lines)
    return lines[start:] + lines[:start]
