"""Wave 96 — doubt follow-up ("ye step samjhao").

After Ganitra answers a question, a student often wants just ONE
step of THAT answer explained again, more simply: "ye step samajh
nahi aaya", "dusra step samjhao", "why did you divide by 3",
"ye kaise aaya". Until this wave those messages were treated as
brand-new questions and died in the not-found one-liner.

How it works (fully deterministic — no AI calls):

* ``parse_followup(question)`` decides whether a chat message is
  a follow-up about the PREVIOUS answer, and if so which step it
  points at (explicit number/ordinal, an operation hint like
  "divide by 3", next/previous relative to the last explained
  step, or unspecified -> the last working step). The detector is
  deliberately conservative: strong signals (a step reference, a
  confusion phrase, "kaise aaya", "why did you ...") are required,
  OR the message must consist of nothing but follow-up filler
  words ("samjhao", "explain this step"). A fresh question that
  merely starts with "samjhao" ("samjhao HCF kya hota hai") is a
  concept question and is NEVER claimed — see the veto battery in
  test/test_wave96.py.

* The previous answer's steps are recovered from its result dict
  (``result["steps"]`` — the solver's own plain lines). That dict
  is what the chat path keeps as ``session["last_result"]`` AND
  what the client stores inside the saved chat thread
  (``messages[].data.result``), so the same recovery works for a
  reopened chat: steps were stored structurally all along.

* ``build_doubt_response(...)`` re-explains JUST the referenced
  step from its own text: what was done, why (from the step's own
  lead-in label / the transformation from the previous step), and
  a tiny canonical example for the operation involved — in the
  student's language (English / Hinglish / Devanagari Hindi).
  It returns None when there is nothing honest to explain (no
  previous answer, no steps, step number out of range, operation
  not present in any step): the caller then falls through to the
  normal solve path, whose fallback layer answers with the app's
  honest one-liner. A step is NEVER invented.
"""

import re

from i18n import result_is_plain

__all__ = ["parse_followup", "working_steps", "eligible_result",
           "build_doubt_response", "style_for"]


# ------------------------------------------------------------------ #
# Step recovery
# ------------------------------------------------------------------ #

_STEP_PREFIX = re.compile(
    r"^(solution|final answer|answer|hal|uttar|हल|उत्तर)\s*[:\-]\s*",
    re.IGNORECASE)


def working_steps(result):
    """The previous answer's WORKING steps: ``result["steps"]``
    minus a trailing line that merely restates the final answer
    (the chat drops that line from the displayed steps too, so a
    student's "last step" is the last line that does work)."""
    if not isinstance(result, dict):
        return []
    steps = [str(s).strip() for s in (result.get("steps") or [])
             if str(s).strip()]
    answer = str(result.get("answer", "") or "").strip()
    if len(steps) > 1 and answer:
        core = _STEP_PREFIX.sub("", steps[-1]).strip()
        if core == answer or steps[-1] == answer:
            steps = steps[:-1]
    return steps


def eligible_result(result):
    """True when `result` is a previous answer whose steps can be
    re-explained: a real payload with at least one working step,
    not a solver error and not one of the plain one-liners
    (not-found / science guard / greeting / vague)."""
    if not isinstance(result, dict):
        return False
    if result.get("op") == "error":
        return False
    if result_is_plain(result):
        return False
    return len(working_steps(result)) >= 1


# ------------------------------------------------------------------ #
# Follow-up detection
# ------------------------------------------------------------------ #

_ORDINALS = {
    "pehla": 1, "pehle": 1, "pahla": 1, "first": 1,
    "dusra": 2, "doosra": 2, "dusre": 2, "doosre": 2, "second": 2,
    "tisra": 3, "teesra": 3, "tisre": 3, "third": 3,
    "chautha": 4, "chautha": 4, "fourth": 4,
    "paanchva": 5, "panchva": 5, "paanchwan": 5, "fifth": 5,
    "chhatha": 6, "sixth": 6,
    "saatva": 7, "seventh": 7,
    "aathva": 8, "eighth": 8,
    "पहला": 1, "पहले": 1, "दूसरा": 2, "दूसरे": 2,
    "तीसरा": 3, "तीसरे": 3, "चौथा": 4, "चौथे": 4,
    "पाँचवाँ": 5, "पाँचवे": 5, "छठा": 6, "सातवाँ": 7, "आठवाँ": 8,
}
_LAST_WORDS = {"aakhri", "akhri", "aakhir", "last", "antim",
               "आखिरी", "आखरी", "अंतिम"}
_NEXT_WORDS = {"agla", "agle", "next", "अगला", "अगले"}
_PREV_WORDS = {"pichla", "pichle", "previous", "पिछला", "पिछले"}
_STEP_WORDS = {"step", "steps", "चरण", "स्टेप"}
_EXPLAIN_WORDS = {"samjhao", "samjhaiye", "samjhaye", "samjhado",
                  "samjha", "समझाओ", "समझाइए", "समझा", "explain",
                  "batao", "बताओ", "बताइए"}

_CONFUSION = (
    "samajh nahi", "samajh nhi", "samjh nahi", "samajh me nahi",
    "samajh mein nahi", "nahi samajh", "nhi samajh",
    "समझ नहीं", "समझ नही", "समझ में नहीं",
    "don't understand", "do not understand", "did not understand",
    "not understand", "samajh nahi aaya", "समझ नहीं आया",
    "not clear", "clear nahi", "clear नहीं",
)
_KAISE = ("kaise aaya", "ye kaise", "yeh kaise", "कैसे आया",
          "how did", "how come", "कैसे हुआ", "kaise hua")
_WHY = ("why did you", "why have you", "kyun kiya", "kyu kiya",
        "क्यों किया", "kyun diya", "kyu diya", "क्यों दिया",
        "kyun liya", "क्यों लिया")
_AGAIN = ("phir se", "फिर से", "dobara", "दोबारा")

# A message carrying one of these is asking about a NEW topic —
# a concept question, never a follow-up (unless it ALSO carries an
# explicit step number, handled by the caller order below).
_CONCEPT_VETO = (
    "kya hai", "kya hota", "kya hote", "kya hoti", "matlab",
    "what is", "what are", "define", "definition",
    "क्या है", "क्या होता", "क्या होते", "formula kya",
)

# Words that may appear in a bare follow-up and carry no new
# question payload. The weak-signal path fires only when NOTHING
# outside this vocabulary remains.
_FILLER = _EXPLAIN_WORDS | _STEP_WORDS | _LAST_WORDS | _NEXT_WORDS \
    | _PREV_WORDS | set(_ORDINALS) | {
        "ye", "yeh", "is", "this", "that", "the", "a", "an",
        "wala", "wale", "wali", "one", "ko", "ka", "ki", "ke",
        "me", "mein", "hai", "na", "zara", "aur", "or", "phir",
        "se", "dobara", "again", "please", "plz", "bro", "bhai",
        "ek", "bar", "baar", "do", "karke", "krke", "aap", "tum",
        "mujhe", "samajh", "nahi", "nhi", "aaya", "aayi",
        "समझ", "नहीं", "नही", "आया", "यह", "ये", "इस", "वाला",
        "वाले", "फिर", "से", "मुझे", "एक", "बार", "और", "का",
        "की", "को", "में", "है", "चरण", "बताओ",
        "no", "number", "num", "wala", "step",
    }

_OP_HINT_PATTERNS = (
    ("divide", r"(?:divide|division|bhaag|भाग|divide\s+by)"
               r"[^0-9]{0,12}?(\d+(?:\.\d+)?)"),
    ("divide", r"(\d+(?:\.\d+)?)\s*(?:se|से)\s*(?:bhaag|भाग)"),
    ("multiply", r"(?:multiply|guna|गुणा|times)"
                 r"[^0-9]{0,12}?(\d+(?:\.\d+)?)"),
    ("multiply", r"(\d+(?:\.\d+)?)\s*(?:se|से)\s*(?:guna|गुणा)"),
    ("add", r"(?:add|jodo|जोड़|plus)[^0-9]{0,12}?(\d+(?:\.\d+)?)"),
    ("subtract", r"(?:subtract|ghatao|घटा|minus)"
                 r"[^0-9]{0,12}?(\d+(?:\.\d+)?)"),
)


def _words(text):
    # Split into words dropping punctuation characters only.
    # (A \w-based cleanup would tear Devanagari words apart —
    # its vowel signs are combining marks, not \w characters.)
    import unicodedata
    out = []
    for tok in str(text).lower().split():
        word = "".join(ch for ch in tok
                       if not unicodedata.category(ch).startswith("P"))
        if word:
            out.append(word)
    return out


def parse_followup(question):
    """Classify a chat message as a doubt follow-up.

    Returns None for an ordinary (fresh) question, else a dict:
    {"index": int|None (0-based explicit step), "relative":
    "next"|"prev"|"last"|None, "op_hint": (op, number)|None}.
    An all-None ref means "unspecified" — the caller explains the
    last working step."""
    text = " " + str(question or "").lower().strip() + " "
    words = _words(text)
    if not words:
        return None
    wordset = set(words)
    has_step_word = bool(wordset & _STEP_WORDS)

    # --- explicit step reference --------------------------------
    index = None
    m = re.search(r"(?:step|चरण|स्टेप)\s*(?:no\.?|number|नंबर)?"
                  r"\s*(\d+)", text)
    if m is None:
        m = re.search(r"(\d+)\s*(?:st|nd|rd|th)\s*(?:step|चरण)",
                      text)
    if m is not None:
        index = int(m.group(1)) - 1
    if index is None:
        for w in words:
            if w in _ORDINALS and (
                    has_step_word or "wala" in wordset
                    or "वाला" in wordset
                    or any(p in text for p in _CONFUSION)
                    or bool(wordset & _EXPLAIN_WORDS)):
                index = _ORDINALS[w] - 1
                break

    relative = None
    if index is None:
        if wordset & _NEXT_WORDS and (
                has_step_word or wordset & _EXPLAIN_WORDS
                or any(p in text for p in _CONFUSION)):
            relative = "next"
        elif wordset & _PREV_WORDS and (
                has_step_word or wordset & _EXPLAIN_WORDS
                or any(p in text for p in _CONFUSION)):
            relative = "prev"
        elif wordset & _LAST_WORDS and (
                has_step_word or "wala" in wordset
                or "वाला" in wordset):
            relative = "last"

    op_hint = None
    for op, pattern in _OP_HINT_PATTERNS:
        m = re.search(pattern, text)
        if m:
            op_hint = (op, m.group(1))
            break

    confusion = any(p in text for p in _CONFUSION)
    kaise = any(p in text for p in _KAISE)
    why = any(p in text for p in _WHY)
    again = any(p in text for p in _AGAIN) \
        and bool(wordset & _EXPLAIN_WORDS)
    has_explain = bool(wordset & _EXPLAIN_WORDS)

    # Concept veto: a new-topic ask is never a follow-up — unless
    # it pins an explicit step number ("step 2 me HCF kya hai"
    # still points at step 2 of the previous answer).
    if index is None and any(p in text for p in _CONCEPT_VETO):
        return None

    strong = (index is not None or relative is not None or confusion
              or kaise or why or again or op_hint is not None)
    if strong:
        return {"index": index, "relative": relative,
                "op_hint": op_hint}

    # Weak path: the message is ONLY follow-up filler ("samjhao",
    # "explain this step", "ye step samjhao"). Any leftover word
    # or digit is a new question payload — veto.
    if has_explain:
        if any(ch.isdigit() for ch in text):
            return None
        if any(w not in _FILLER for w in words):
            return None
        return {"index": None, "relative": None, "op_hint": None}
    return None


# ------------------------------------------------------------------ #
# Step explanation
# ------------------------------------------------------------------ #

_OP_MARKS = {
    "divide": ("÷", "/", "divide", "bhaag", "भाग"),
    "multiply": ("×", "*", "·", "multiply", "guna", "गुणा"),
    "add": ("+", "add", "जोड़"),
    "subtract": ("-", "−", "subtract", "घटा"),
}

_TINY_EXAMPLE = {
    "divide": {"en": "Tiny example: 12 ÷ 3 = 4 — dividing just "
                     "splits a number into equal parts.",
               "hinglish": "Chhota example: 12 ÷ 3 = 4 — bhaag "
                           "matlab barabar hisso me baantna.",
               "hindi": "छोटा उदाहरण: 12 ÷ 3 = 4 — भाग मतलब किसी "
                        "संख्या को बराबर हिस्सों में बाँटना।"},
    "multiply": {"en": "Tiny example: 3 × 4 = 12 — multiply means "
                       "add the same number again and again.",
                 "hinglish": "Chhota example: 3 × 4 = 12 — guna "
                             "matlab wahi number baar-baar jodna.",
                 "hindi": "छोटा उदाहरण: 3 × 4 = 12 — गुणा मतलब वही "
                          "संख्या बार-बार जोड़ना।"},
    "add": {"en": "Tiny example: 2 + 3 = 5 — adding just joins "
                  "the two amounts.",
            "hinglish": "Chhota example: 2 + 3 = 5 — jodna matlab "
                        "dono matra ek saath karna.",
            "hindi": "छोटा उदाहरण: 2 + 3 = 5 — जोड़ना मतलब दोनों "
                     "मात्राएँ एक साथ करना।"},
    "subtract": {"en": "Tiny example: 9 − 4 = 5 — subtracting "
                       "takes one amount away from the other.",
                 "hinglish": "Chhota example: 9 − 4 = 5 — ghatana "
                             "matlab ek matra me se dusri nikaalna.",
                 "hindi": "छोटा उदाहरण: 9 − 4 = 5 — घटाना मतलब एक "
                          "मात्रा में से दूसरी निकालना।"},
}

_T = {
    "this_step": {"en": "Step {n}: {step}",
                  "hinglish": "Step {n}: {step}",
                  "hindi": "चरण {n}: {step}"},
    "prev_was": {"en": "Just before this, we had: {prev}",
                 "hinglish": "Isse just pehle humare paas tha: {prev}",
                 "hindi": "इससे ठीक पहले हमारे पास था: {prev}"},
    "offer_next": {
        "en": "If this is clear now, type 'next step samjhao' "
              "and I will explain the next step too.",
        "hinglish": "Ab samajh aa gaya ho to 'agla step samjhao' "
                    "likho — agla step bhi aise hi samjha dunga.",
        "hindi": "अब समझ आ गया हो तो 'अगला चरण समझाओ' लिखिए — "
                 "अगला चरण भी ऐसे ही समझा दूँगा।"},
    "was_last": {
        "en": "This was the last step — the final answer comes "
              "straight from here.",
        "hinglish": "Ye aakhri step tha — final answer seedha "
                    "yahi se aata hai.",
        "hindi": "यह आखिरी चरण था — अंतिम उत्तर सीधा यहीं से "
                 "आता है।"},
    "generic_why": {
        "en": "In this step we simply take the previous line and "
              "work it one small move further — nothing new is "
              "added from outside.",
        "hinglish": "Is step me bas pichli line ko lekar ek "
                    "chhota sa agla move kiya gaya hai — bahar "
                    "se kuch naya nahi joda gaya.",
        "hindi": "इस चरण में बस पिछली पंक्ति को लेकर एक छोटा सा "
                 "अगला कदम बढ़ाया गया है — बाहर से कुछ नया नहीं "
                 "जोड़ा गया।"},
}


def style_for(question, lang=None):
    """Reply style for a follow-up: Devanagari in the message ->
    Hindi; a Roman-script message in a Hindi session -> Hinglish;
    everything else -> English."""
    q = str(question or "")
    if any("\u0900" <= ch <= "\u097f" for ch in q):
        return "hindi"
    if (lang or "") == "hi":
        return "hinglish"
    return "en"


def _split_step(step):
    """Split a house step into (label, body) on its first ': '
    when the head is a short action label ("Divide both sides by
    3") and the tail carries the working. Else (None, step)."""
    if ": " in step:
        label, body = step.split(": ", 1)
        if 0 < len(label) <= 70 and not any(
                ch in label for ch in "=<>±") and body.strip():
            return label.strip(), body.strip()
    return None, step.strip()


def _num(text):
    m = re.search(r"\d+(?:\.\d+)?", text or "")
    return m.group(0) if m else None


def _why_lines(label, body, style):
    """(why_line, tiny_example_op) derived from the step's own
    label/body — deterministic templates per action family."""
    low = ((label or "") + " " + body).lower()
    n = _num(label or "") or _num(body)
    if "divide" in low and "both sides" in low:
        d = _num(label or "") or "?"
        return ({"en": f"Why: we want the unknown alone on one "
                       f"side. It was multiplied by {d}, so we "
                       f"divide BOTH sides by {d} — the opposite "
                       f"operation cancels the multiplication, and "
                       f"doing it to both sides keeps the equation "
                       f"balanced.",
                 "hinglish": f"Kyun: hume unknown ko ek taraf "
                             f"akela karna hai. Uske saath {d} se "
                             f"guna tha, isliye DONO taraf {d} se "
                             f"bhaag diya — ulta operation guna ko "
                             f"kaat deta hai, aur dono taraf karne "
                             f"se equation balance rehta hai.",
                 "hindi": f"क्यों: हमें अज्ञात को एक तरफ अकेला "
                          f"करना है। उसके साथ {d} से गुणा था, "
                          f"इसलिए दोनों तरफ {d} से भाग दिया — "
                          f"उल्टा operation गुणा को काट देता है, "
                          f"और दोनों तरफ करने से समीकरण संतुलित "
                          f"रहता है।"}[style], "divide")
    if ("add" in low or "subtract" in low or "minus" in low) \
            and "both sides" in low:
        verb_en = "add" if "add" in low else "subtract"
        return ({"en": f"Why: whatever we {verb_en} on one side "
                       f"must be done on the other side too — "
                       f"that is what keeps an equation balanced "
                       f"while we move the extra number away from "
                       f"the unknown.",
                 "hinglish": "Kyun: equation me ek taraf jo "
                             "karte hai, wahi dusri taraf bhi "
                             "karna padta hai — isi se equation "
                             "balance rehta hai, aur extra number "
                             "unknown se alag ho jata hai.",
                 "hindi": "क्यों: समीकरण में एक तरफ जो करते हैं, "
                          "वही दूसरी तरफ भी करना पड़ता है — इसी "
                          "से समीकरण संतुलित रहता है, और अतिरिक्त "
                          "संख्या अज्ञात से अलग हो जाती है।"}[style],
                "add" if verb_en == "add" else "subtract")
    if "one side" in low or "bring" in low or "collect" in low:
        return ({"en": "Why: an equation is easiest to finish "
                       "when all the unknown terms sit on one "
                       "side and the plain numbers on the other — "
                       "this step just gathers them.",
                 "hinglish": "Kyun: equation tab aasan hota hai "
                             "jab saare unknown wale terms ek "
                             "taraf aur plain numbers dusri taraf "
                             "aa jaye — is step me bas wahi ikattha "
                             "kiya gaya hai.",
                 "hindi": "क्यों: समीकरण तब आसान होता है जब "
                          "सारे अज्ञात वाले पद एक तरफ और साधारण "
                          "संख्याएँ दूसरी तरफ आ जाएँ — इस चरण में "
                          "बस वही इकट्ठा किया गया है।"}[style], None)
    if low.startswith("let ") or (label and label.lower()
                                   .startswith("let ")):
        return ({"en": "Why: this line only gives a short name "
                       "(like x) to the unknown thing we have to "
                       "find, so the maths after it stays short "
                       "and clear. No calculation happens here.",
                 "hinglish": "Kyun: is line me sirf jis cheez ko "
                             "dhoondhna hai use ek chhota naam "
                             "(jaise x) diya gaya hai, taaki aage "
                             "ka maths chhota aur saaf rahe. Yahan "
                             "koi calculation nahi hota.",
                 "hindi": "क्यों: इस पंक्ति में सिर्फ जिस चीज़ "
                          "को ढूँढना है उसे एक छोटा नाम (जैसे x) "
                          "दिया गया है, ताकि आगे का गणित छोटा और "
                          "साफ़ रहे। यहाँ कोई गणना नहीं होती।"
                 }[style], None)
    if "formula" in low or "area =" in low or "perimeter =" in low \
            or "volume =" in low:
        return ({"en": "Why: this step puts the question's "
                       "numbers into the standard formula — the "
                       "formula is fixed, only the numbers come "
                       "from the question.",
                 "hinglish": "Kyun: is step me sawal ke numbers "
                             "ko standard formula me rakha gaya "
                             "hai — formula fixed hota hai, sirf "
                             "numbers sawal se aate hai.",
                 "hindi": "क्यों: इस चरण में सवाल की संख्याओं "
                          "को मानक सूत्र में रखा गया है — सूत्र "
                          "निश्चित होता है, सिर्फ संख्याएँ सवाल "
                          "से आती हैं।"}[style], None)
    # Plain arithmetic body "a <op> b = c": verify the move with
    # its own reverse check for division.
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(÷|/)\s*(\d+(?:\.\d+)?)"
                 r"\s*=\s*(\d+(?:\.\d+)?)\s*$", body)
    if m:
        a, b, c = m.group(1), m.group(3), m.group(4)
        return ({"en": f"Why: {a} ÷ {b} asks 'how many times "
                       f"does {b} fit into {a}?' Check it "
                       f"backwards: {b} × {c} = {a}, so "
                       f"{a} ÷ {b} = {c} is right.",
                 "hinglish": f"Kyun: {a} ÷ {b} ka matlab hai "
                             f"'{a} me {b} kitni baar aata hai?' "
                             f"Ulta check karo: {b} × {c} = {a}, "
                             f"isliye {a} ÷ {b} = {c} sahi hai.",
                 "hindi": f"क्यों: {a} ÷ {b} का मतलब है '{a} "
                          f"में {b} कितनी बार आता है?' उल्टा "
                          f"जाँचो: {b} × {c} = {a}, इसलिए "
                          f"{a} ÷ {b} = {c} सही है।"}[style],
                "divide")
    return (_T["generic_why"][style], None)


def _dominant_op(body):
    low = str(body).lower()
    for op, marks in _OP_MARKS.items():
        if any(mark in low for mark in marks):
            return op
    return None


def _find_op_step(steps, op_hint):
    op, number = op_hint
    marks = _OP_MARKS.get(op, ())
    for i, step in enumerate(steps):
        if number and number not in step:
            continue
        if any(mark in step.lower() for mark in marks):
            return i
    for i, step in enumerate(steps):
        if number and number in step:
            return i
    return None



def build_doubt_response(question, ref, prev_result, lang=None,
                         last_step=None):
    """Build the step-explanation result for a follow-up.

    Returns (result_dict, step_index) or None when there is
    nothing honest to explain — the caller then falls through to
    the normal solve path (honest one-liner), never an invented
    step."""
    if ref is None or not eligible_result(prev_result):
        return None
    steps = working_steps(prev_result)
    total = len(steps)

    index = ref.get("index")
    if index is None and ref.get("op_hint"):
        index = _find_op_step(steps, ref["op_hint"])
        if index is None:
            return None
    if index is None and ref.get("relative") == "next":
        base = last_step if isinstance(last_step, int) else -1
        index = base + 1
    if index is None and ref.get("relative") == "prev":
        base = last_step if isinstance(last_step, int) else total
        index = base - 1
    if index is None:
        # "last" relative, or unspecified -> the last working step.
        index = total - 1
    if index < 0 or index >= total:
        return None

    step = steps[index]
    prev = steps[index - 1] if index > 0 else None
    style = style_for(question, lang)
    label, body = _split_step(step)

    lines = [_T["this_step"][style].format(n=index + 1, step=step)]
    if prev:
        lines.append(_T["prev_was"][style].format(prev=prev))
    why, why_op = _why_lines(label, body, style)
    lines.append(why)
    # A tiny canonical example for the operation — unless the why
    # line already IS a concrete numeric check (the a÷b=c case).
    tiny_op = why_op or _dominant_op(body)
    if tiny_op and "backwards" not in why and "Ulta check" not in why \
            and "जाँचो" not in why:
        lines.append(_TINY_EXAMPLE[tiny_op][style])
    if index < total - 1:
        lines.append(_T["offer_next"][style])
    else:
        lines.append(_T["was_last"][style])

    result = {
        "type": "doubt",
        "op": "explain_step",
        "steps": lines,
        "answer": body,
        "doubt": True,
        "step_number": index + 1,
        "of_steps": total,
    }
    return result, index
