"""Wave 228 — SAATHI MODE (Suraj's spec, 23 Nov 2026).

In the 1:1 chat a student sometimes stops asking maths and
shares something personal: feeling disturbed or anxious,
overthinking, a health worry, being stuck somewhere, a
trouble they cannot tell anyone at home. The standing
maths-only discipline must NOT answer that with the
maths-only one-liner (or the not-found line, or a study
motivation card — the three outcomes these messages got
before this wave). Ganitra listens like a trusted
companion / teacher instead: kind, warm, unhurried; it
comforts, and gently shows a sensible next step. On a
serious health / mental-health crisis it kindly encourages
telling a trusted adult or a professional — no lecture, no
frightening language, never dismissive.

SCOPE BOUNDARY (binding): the override applies ONLY to the
personal / emotional category. A straight study question on
another subject keeps the maths-only rule, and a maths
question is NEVER diverted here. Detection is therefore
meaning-based and triple-gated — a message qualifies only
when ALL THREE hold:

  1. SELF-REFERENCE — the student is talking about
     themselves (I / me / my, mujhe / mera / main, मैं /
     मुझे / मेरा, or a first-person frame like "rona aa
     raha hai" whose subject can only be the speaker);
  2. A PERSONAL / EMOTIONAL THEME — distress, anxiety,
     overthinking, sadness, fear, loneliness, a health
     worry, being stuck, having no one to tell, personal
     exam fear, or (the crisis set) self-harm thoughts;
  3. NO MATHS PAYLOAD — no computation rides along. The
     vetoes are strict: digits with an operator, two or
     more numbers, digits with a maths topic / ask word,
     or number words with a quantity ask all refuse. So
     "a string under tension of 10 N..." (a physics-worded
     ask carrying numbers) and a sad-sounding word problem
     ("Rahul is sad, he lost 15 of his 40 marbles — how
     many are left?") stay on the maths path, and the word
     "tension" alone never fires anything.

The reply is a PLAIN result (fallback._plain_result), in
the student's own language / script (en / Hinglish-Roman /
Hindi-Devanagari, selected exactly like the Wave 207
defective-question lines). Plain results are refused by
the Live Bank's own classifier, so a saathi reply is never
recorded into — or served from — the maths answer bank;
the layer also sits ahead of the bank lookup in the chain,
so no stored maths answer can ever be served to a personal
share either.
"""

import re

__all__ = ["saathi_result", "detect_saathi"]


# ---------------------------------------------------------------------------
# Gate 3 first (cheapest and strictest): the maths-payload vetoes
# ---------------------------------------------------------------------------

_OPERATOR_CHARS = set("+-*/=^%×÷")
_ASK_WORDS = (
    "kitna", "kitne", "kitni", "how many", "how much",
    "कितना", "कितने", "कितनी",
)
_TOPIC_WORDS = (
    "area", "perimeter", "volume", "percent", "average",
    "ratio", "hcf", "lcm", "gcd", "angle", "triangle",
    "circle", "radius", "diameter", "equation", "solve",
    "simplify", "factor", "sum of", "product of",
    "kshetrafal", "paridhi", "aayatan", "ausat", "anupat",
    "क्षेत्रफल", "परिधि", "आयतन", "औसत", "अनुपात", "त्रिभुज",
)
_NUMBER_WORD_RE = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen|twenty|thirty|forty|"
    r"fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"ek|do|teen|char|chaar|paanch|panch|chhah|saat|aath|"
    r"nau|das|gyarah|barah|terah|chaudah|pandrah|solah|"
    r"satrah|atharah|bees|tees|sau|hazaar|hazar)\b",
    re.IGNORECASE)


def _has_maths_payload(q):
    """True when a computation rides along — the message is
    a maths ask whatever emotional words dress it."""
    digits = re.findall(r"\d+", q)
    if digits:
        if any(ch in q for ch in _OPERATOR_CHARS):
            return True
        if len(digits) >= 2:
            return True
        if any(w in q for w in _ASK_WORDS + _TOPIC_WORDS):
            return True
    # Number words + a quantity ask is a word problem even
    # with no digits ("...had forty marbles and lost
    # fifteen — how many are left?").
    if len(_NUMBER_WORD_RE.findall(q)) >= 2 and \
            any(w in q for w in _ASK_WORDS):
        return True
    return False


# ---------------------------------------------------------------------------
# Gate 1: self-reference
# ---------------------------------------------------------------------------

_SELF_RE = re.compile(
    r"\b(i|me|my|mine|myself|i'm|im|i am|i feel|i have|"
    r"i can't|i cant|i cannot)\b"
    r"|mujhe|mujhko|mera|meri|mere|main hoon|mai hoon|"
    r"मैं|मुझे|मुझको|मेरा|मेरी|मेरे",
    re.IGNORECASE)

# First-person frames: feeling phrases whose unstated
# subject, in a chat with a tutor, is the speaker — plus
# the Hinglish first-person verb forms themselves
# (hoon / jaunga / phas gaya can only be the speaker
# talking about themselves).
_SELF_FRAMES = (
    "aa raha hai", "aa rahi hai", "ho raha hai",
    "ho rahi hai", "lag raha hai", "lag rahi hai",
    "nahi aati", "nahi aata", "nahi sakta", "nahi sakti",
    "बता नहीं सकता", "बता नहीं सकती", "आ रहा है",
    "हो रहा है", "लग रहा है",
    "hoon", "हूँ", "jaunga", "jaungi", "jaaunga",
    "kharab hai", "phas gaya", "phas gayi", "fasa hua",
    "fasi hui", "gaya hoon", "gayi hoon",
)


# ---------------------------------------------------------------------------
# Gate 2: the personal / emotional themes
# ---------------------------------------------------------------------------

_CRISIS_PHRASES = (
    "mar jaunga", "mar jaaunga", "mar jaungi", "marne ka mann",
    "mar jana hai", "jeene ka mann nahi", "zinda nahi rehna",
    "zindagi khatm", "jaan de dunga", "jaan de dungi",
    "suicide", "khud ko nuksan", "khud ko chot",
    "aatmahatya", "आत्महत्या", "मर जाऊंगा", "मर जाऊंगी",
    "जीने का मन नहीं",
)

_THEME_PHRASES = (
    # distress / anxiety / overthinking
    "tension ho", "bahut tension", "tension hai", "tension me",
    "pareshan", "परेशान", "anxious", "anxiety", "overthinking",
    "overthink", "stressed", "stress ho", "stress hai",
    "depress",
    "dukh", "दुख", "akela", "akele", "lonely", "अकेला",
    "rona", "रोना", "darr lag", "dar lag", "डर लग",
    "ghabra", "घबरा",
    "neend nahi", "नींद नहीं", "so nahi pa",
    "bura lag raha", "acha nahi lag raha", "achha nahi lag raha",
    "mann kar raha", "himmat nahi", "thak gaya", "thak gayi",
    "sad feel", "feel sad", "feeling sad", "feeling low",
    "bahut bura feel", "mood kharab",
    # health worry
    "tabiyat", "तबीयत", "bimar", "बीमार", "bukhaar", "bukhar",
    # stuck somewhere
    "fasa hua", "fasi hui", "phas gaya", "phas gayi",
    "phase hue", "stuck ho gaya", "stuck hu",
    # no one to tell / no one understands
    "kisi ko bata nahi", "kisi ko nahi bata",
    "ghar par bata nahi", "gharwalo ko bata nahi",
    "koi samajhta nahi", "koi samajh nahi",
    "किसी को बता नहीं", "कोई समझता नहीं",
    # personal exam fear
    "fail ho jaunga", "fail ho jaungi", "fail ho jaaunga",
    "fail hone ka darr", "fail hone ka dar",
)


# Weak themes: a wandering mind is, BY ITSELF, the Wave
# 154 guidance layer's pinned motivation case ("mann nahi
# lag raha padhai me" -> the motivation card). It counts
# as a personal share only with company — another theme
# above, or a distress intensifier widening it beyond
# studies ("kisi cheez me mann nahi lag raha").
_WEAK_THEMES = ("mann nahi lag", "man nahi lag", "dil nahi lag")
_WEAK_COMPANIONS = ("bahut", "bilkul", "kisi cheez",
                    "kuch bhi", "kahi bhi", "ab to")


def detect_saathi(text):
    """Classify a message: "crisis", "saathi", or None.

    All three gates must pass (see the module docstring);
    anything else returns None and the normal layers answer
    exactly as before."""
    if not text:
        return None
    raw = str(text).strip()
    if not raw or len(raw) > 500:
        return None
    q = re.sub(r"\s+", " ", raw.lower())
    if _has_maths_payload(q):
        return None
    # The crisis set needs no separate self-reference: its
    # phrases ARE first-person forms ("mar jaunga", "khud
    # ko nuksan") — the speaker is the only possible
    # subject, and this is the one set that must never be
    # missed for want of a pronoun.
    if any(p in q for p in _CRISIS_PHRASES):
        return "crisis"
    if not (_SELF_RE.search(q)
            or any(f in q for f in _SELF_FRAMES)):
        return None
    if any(p in q for p in _THEME_PHRASES):
        return "saathi"
    if any(p in q for p in _WEAK_THEMES) and (
            any(c in q for c in _WEAK_COMPANIONS)):
        return "saathi"
    return None


# ---------------------------------------------------------------------------
# The replies — kind, warm, unhurried; a gentle next step;
# crisis adds the trusted-adult / professional encouragement.
# Ganitra's own voice, matching the app's authored lines.
# ---------------------------------------------------------------------------

_LINES = {
    "saathi": {
        "en": "I hear you — and I'm really glad you told "
              "me. What you're feeling is completely okay; "
              "even the strongest students feel exactly "
              "like this sometimes. Take a slow breath, "
              "have some water, and rest a little — and if "
              "you can, tell someone you trust at home, or "
              "a teacher, how you feel; sharing it genuinely "
              "makes the heart lighter. I'm right here — "
              "talk to me whenever you want, and whenever "
              "you're ready, I'll help you with maths one "
              "small step at a time. 😊",
        "roman": "Main sun raha hoon — aur tumne mujhe "
                 "bataya, ye bahut achhi baat hai. Jo tum "
                 "feel kar rahe ho, wo bilkul theek hai; "
                 "kabhi-kabhi sabse achhe students bhi aisa "
                 "hi feel karte hain. Ek lambi saans lo, "
                 "thoda paani piyo, thoda rest karo — aur ho "
                 "sake to ghar par kisi bade ya kisi teacher "
                 "ko, jin par tumhe bharosa ho, apne mann ki "
                 "baat batao; baat baantne se mann sach me "
                 "halka hota hai. Main yahi hoon — jab mann "
                 "kare baat kar lena, aur jab ready ho, "
                 "maths me chhote-chhote steps se main "
                 "tumhari madad kar dunga. 😊",
        "dev": "मैं सुन रहा हूँ — और तुमने मुझे बताया, यह "
               "बहुत अच्छी बात है। जो तुम महसूस कर रहे हो, "
               "वह बिल्कुल ठीक है; कभी-कभी सबसे अच्छे छात्र "
               "भी ऐसा ही महसूस करते हैं। एक लंबी साँस लो, "
               "थोड़ा पानी पियो, थोड़ा आराम करो — और हो सके "
               "तो घर पर किसी बड़े या किसी शिक्षक को, जिन "
               "पर तुम्हें भरोसा हो, अपने मन की बात बताओ; "
               "बात बाँटने से मन सच में हल्का होता है। मैं "
               "यहीं हूँ — जब मन करे बात कर लेना, और जब "
               "तैयार हो, गणित में छोटे-छोटे चरणों से मैं "
               "तुम्हारी मदद कर दूँगा। 😊",
    },
    "crisis": {
        "en": "I hear you — and I'm really glad you told "
              "me. Please don't carry this alone: tell a "
              "grown-up you trust — a parent, a teacher, "
              "someone at home — today itself, just like "
              "you told me. You matter, and asking for help "
              "is a strong, right step, never a weakness. "
              "If the feeling gets heavier, talking to a "
              "doctor or a counsellor is also a completely "
              "right step. I'm right here with you — and "
              "whenever you're ready, we'll take everything "
              "else one small step at a time. 😊",
        "roman": "Main sun raha hoon — aur tumne mujhe "
                 "bataya, ye bahut achhi baat hai. Please ye "
                 "baat akele mat sehna: kisi bade ko, jin par "
                 "tumhe bharosa ho — maa-papa, koi teacher, "
                 "ghar par koi apna — aaj hi batao, jaise "
                 "tumne mujhe bataya. Tum important ho, aur "
                 "madad maangna ek sahi aur himmat wala "
                 "kadam hai, kamzori bilkul nahi. Agar mann "
                 "aur bhaari ho, to kisi doctor ya "
                 "counsellor se baat karna bhi bilkul sahi "
                 "kadam hai. Main yahi hoon, tumhare saath — "
                 "aur jab ready ho, baaki sab hum "
                 "chhote-chhote steps me sambhal lenge. 😊",
        "dev": "मैं सुन रहा हूँ — और तुमने मुझे बताया, यह "
               "बहुत अच्छी बात है। कृपया यह बात अकेले मत "
               "सहना: किसी बड़े को, जिन पर तुम्हें भरोसा "
               "हो — माँ-पापा, कोई शिक्षक, घर पर कोई अपना — "
               "आज ही बताओ, जैसे तुमने मुझे बताया। तुम "
               "महत्वपूर्ण हो, और मदद माँगना एक सही और "
               "हिम्मत वाला कदम है, कमज़ोरी बिल्कुल नहीं। "
               "अगर मन और भारी हो, तो किसी डॉक्टर या "
               "काउंसलर से बात करना भी बिल्कुल सही कदम "
               "है। मैं यहीं हूँ, तुम्हारे साथ — और जब "
               "तैयार हो, बाकी सब हम छोटे-छोटे चरणों में "
               "सँभाल लेंगे। 😊",
    },
}


def _line(kind, question, hindi, lang=None, lang_request=None):
    """The reply in the student's own language — selection
    mirrors fallback's Wave 207 line picker (an explicit
    request first, then the question's script, then the UI
    language). Flavours shipped: en / roman / dev; other
    languages fall back to en (dev for Marathi's script)."""
    lines = _LINES[kind]
    if lang_request == "hi":
        return lines["dev"]
    if lang_request == "hinglish":
        return lines["roman"]
    if lang_request == "en":
        return lines["en"]
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return lines["dev"]
    if hindi:
        return lines["roman"]
    if lang == "mr":
        return lines["dev"]
    return lines["en"]


def saathi_result(question, hindi, lang=None, lang_request=None):
    """The Saathi serve for a personal / emotional message,
    or None. A plain result in the nonmaths tradition — and
    plain results are refused by the Live Bank's own
    classifier, so this reply is never stored as (or served
    from) a maths answer."""
    kind = detect_saathi(question)
    if kind is None:
        return None
    from fallback import _plain_result
    return _plain_result(
        "saathi",
        _line(kind, question, hindi, lang=lang,
              lang_request=lang_request),
        hindi)
