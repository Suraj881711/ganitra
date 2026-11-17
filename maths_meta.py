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
    # Devanagari: किसने alone is unambiguous; कौन needs its
    # verb phrase (कौन सा is a which-question).
    "किसने", "किसके द्वारा",
    "कौन था", "कौन थी", "कौन थे", "कौन है",
)

_WHO_WORD_EN = re.compile(r"\bwho\b")

# A real computation riding in the text (digit op digit) is a
# problem to solve, never a meta question.
_COMPUTATION = re.compile(r"\d\s*[-+*/=×÷]\s*\d")


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
        "keywords": ("zero", "shunya", "शून्य", "sifar", "सिफ़र"),
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
        "keywords": ("shakuntala", "शकुंतला", "शकुन्तला"),
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
        "keywords": ("aryabhata", "aryabhatta", "आर्यभट"),
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
        "type": "Maths fact" if kind == "history"
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
    if _COMPUTATION.search(q):
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
            "kisne", "kaun tha", "kaun thi", "kaun the")):
        flavour = "roman"
    # History first: a who-shaped ask about a curated
    # topic/person is answered by the FACT layer, before
    # any concept card can serve the WHAT instead.
    if _has_who_shape(q):
        for entry in HISTORY:
            if _entry_hit(q, entry):
                return _result("history", entry, flavour)
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
    if maths_ok:
        for entry in ADVICE:
            if any(t in q for t in entry["triggers"]):
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
    if not q.strip() or _COMPUTATION.search(q):
        return False
    if _has_who_shape(q) and (
            _has_maths_signal(q)
            or any(w in q for w in _WHO_CONTEXT_WORDS)
            or any(_entry_hit(q, e) for e in HISTORY)):
        return True
    if _has_maths_signal(q) and any(
            w in q for w in _ADVICE_SHAPE_WORDS):
        return True
    return False


__all__ = ["HISTORY", "ADVICE", "meta_result", "is_meta_shaped"]
