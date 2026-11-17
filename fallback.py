"""Wave 18: the no-dead-end answer layer.

Suraj's direction (10 Nov 2026): "Muse or ChatGPT ki tarah
comfortable hona chahiye, har ek question ka answer milna
chahiye." The rule-based solver is exact but narrow: concept
asks ("pythagoras theorem kya hai"), greetings, messy word
problems and off-topic questions used to end at the friendly
error card — or worse, at a letter-multiplied nonsense "answer"
(sympy happily turns unknown words into a product of letters).

`with_fallback(question, result)` sits between the solver and
the routes (api.py's _solve_friendly and app.py's classic
/solve + /photo-solve). A REAL solver answer is returned
untouched. Anything else is routed through the layers:

  0. greetings / small talk (checked before everything — the
     solver turns "hi" into "h*i", which must never be shown)
  0b. known non-maths topics (capital of India, cricket score,
     photosynthesis...) — a friendly maths-only reply, never a
     fake answer
  1. salvage: strip conversational filler (batao, samjhao,
     please, "my homework says..."), extract an embedded
     expression/equation and solve THAT; the reply says plainly
     that it solved the maths part of the question
  2. concepts: the curated concepts.py library (formula + one
     worked example) for "what is X / X kya hai / X ka formula"
  3. topic guess: a similar SOLVED example with different
     numbers, honestly labelled "similar example", plus one
     short line asking for the exact missing detail
  4. vague / gibberish / guide: a friendly reply that shows how
     to ask, with a tiny solved example — never a bare error

Wave 39 adds one layer to this chain, between the science
guard and salvage: the Verified Data Bank (bank.py). When the
solver could not really answer and the question is an EXACT
normalised match with a banked item, the item's own steps +
final answer are served instead of a salvaged fragment, a
similar example or the general guide — every banked answer was
independently SymPy-verified before banking. A real solver
answer is still served untouched above it, a science question
never reaches it, and a miss changes nothing: the rest of the
flow is byte-for-byte the pre-Wave-39 behaviour.

HONESTY RULE: a fallback result is flagged (fallback=True,
fallback_kind=...) and never presents a guessed or similar
answer as the exact answer to the student's question.

Result dicts keep the solver's shape ({type, op, answer,
steps, ...) so every existing renderer (chat bubble, answer
page, print, download, history) works unchanged: the gibberish
guard in i18n only fires for type arithmetic/algebra with
op == "simplify", which no fallback result ever uses.

Wave 67 (Suraj, 15 Nov 2026, with phone screenshots): the
no-dead-end layers above were honest but LOUD — gibberish like
"If tu gfuf" earned the full guide card (mixed-language guide
text, the "Questions I solve for sure" notebook panel, a long
final-answer paragraph and Teacher's Advice). His order:
"jab kuch bhi likh diya to itna bada answer dene ki jarurat
nahi hai — bas 'answer not found' bol do, itna hi." So now
anything that is NOT actually solved — greetings/small talk,
vague asks, gibberish, a similar example, the general guide —
collapses to ONE short line in the question's own language
(fallback_kind == "not_found", see _not_found_result), after
the AI chain has had its chance (solver -> bank -> AI ->
one-line not-found). Real answers are untouched: solver,
salvage, bank, concept cards and AI answers render exactly as
before. The maths-only guards keep their own one-line wording
and gain plain=True so the chat shows just that line: the
science payload keeps its formula-guidance steps for the
full-solution page, the non-maths line is trimmed to the
guard sentence itself.
Wave 90: every outcome that collapses to the one-line
not-found is recorded in the not-found learning log
(notfound_log.py) — question text, detected language, the
student's class when known, and how the chain gave up — so
future waves target real student failures instead of
hand-built audits. The log is purely observational: the hook
below is guarded end to end, a logging failure is a silent
no-op, and no answer changes in any way (proven byte-for-byte
in test_wave90, logging on and off).
"""
import re
from fractions import Fraction

from concepts import find_concept
from concept_topics import topic_concept_result
from i18n import get_strings, solve_failed
from solver.router import has_science_signal, normalize_spelling, \
    solve_question

# ---------------------------------------------------------------------------
# Detectors for "the solver did not really answer"
# ---------------------------------------------------------------------------

# Soft non-answers: the solver asking for more input instead of
# answering ("Tell me the data...", "I need the first term...",
# the word-problem catch-all). These are not answers, so the
# fallback may improve on them — but ONLY via its honest layers.
_SOFT_PREFIXES = (
    "tell me", "i need", "no word-problem pattern matched",
    "give a number", "give me", "please tell", "please give",
    "could not", "enter a", "try a form",
)


def _answer_text(result):
    return str((result or {}).get("answer", "") or "")


def _is_soft(result):
    ans = _answer_text(result).strip().lower()
    return bool(ans) and ans.startswith(_SOFT_PREFIXES)


_SYMBOLIC_COMMANDS = ("simplify", "expand", "factor", "factorise",
                      "factorize", "collect")


def _single_letter_factors(text):
    """Distinct single-letter factors of the *-products in a
    text, in ANY script: split on * and ·, strip the exponent
    off each factor (\"ए**2\" -> \"ए\") and keep the factors
    that are exactly one letter (\"c\", \"m\", \"क\", \"ा\").
    Latin-only counting missed the Devanagari letter-soup —
    the Wave 35 audit's 22 Hindi WRONGs are products of the
    question's own Devanagari letters (Wave 52)."""
    out = set()
    for fac in re.split(r"[*·]", str(text or "")):
        f = fac.strip().strip("()")
        f = re.sub(r"(?:\*\*|\^)\s*\d+(?:\.\d+)?$", "", f).strip()
        if len(f) == 1 and f.isalpha():
            out.add(f)
    return out


def _single_letter_factors(ans):
    """Distinct single-character letter/mark factors of a product
    answer, in ANY script. Wave 58: the old detector counted only
    Latin [a-z] singles, so Devanagari soup ("12*c*m*इ*ए**2*क**4…")
    — two Latin letters and a dozen Devanagari ones, vowel signs
    included — sailed through as a genuine answer."""
    import unicodedata
    t = str(ans).replace("·", "*").replace(" ", "")
    t = re.sub(r"\*\*\d+", "", t)
    out = set()
    for fac in t.split("*"):
        fac = fac.strip("()")
        if len(fac) == 1 and unicodedata.category(fac)[0] in ("L", "M"):
            out.add(fac)
    return out


def _is_junk(question, result):
    """Letter-soup detection: sympy turned the question's words
    into a product of single letters ("what is pythagoras
    theorem" -> a**2*e**2*g*h**2*...). A genuine symbolic answer
    almost never mentions 4+ DISTINCT single letters, and real
    simplify/expand/factor asks are excluded up front.

    Wave 52: the letter count now covers every script (the
    Hindi questions' soup is Devanagari: "12*c*m*इ*ए**2*क**4*…"
    carries only 2 Latin letters but a dozen Devanagari ones),
    and a bare *-chain of 5+ distinct single letters is soup
    even without an exponent mark ("Find the square of 15"
    salvaged to "15*a*e*q*r*s*u" — the word "square" itself,
    letter-multiplied)."""
    q = str(question or "").lower()
    if any(cmd in q for cmd in _SYMBOLIC_COMMANDS):
        return False
    ans = _answer_text(result)
    letters = set(re.findall(r"(?<![A-Za-z])[a-z](?![A-Za-z])", ans))
    factors = _single_letter_factors(ans)
    if any(mark in ans for mark in ("**", "·", "^")):
        if len(ans) >= 8 and len(letters | factors) >= 4:
            return True
        # Wave 57 (merge-3 hand-merge into Wave 52's branch):
        # a SHORT whole-answer product of single letters is
        # soup too — it slipped under the length threshold
        # ("what is HCF" -> "C·F·H", three distinct letters).
        compact0 = ans.replace(" ", "").replace("·", "*")
        if re.fullmatch(r"[A-Za-z](\*\*\d+)?"
                        r"(\*[A-Za-z](\*\*\d+)?)+", compact0):
            if len(set(re.findall(r"[A-Za-z]",
                                  compact0))) >= 3:
                return True
        # Wave 57: Devanagari letter-soup fragments — a
        # product with 4+ short non-Latin fragments is sympy
        # multiplying Hindi words letter-wise (catches the
        # shapes whose factor count stays under the rules
        # above, e.g. two-codepoint fragments).
        parts = re.split(r"[*·]", ans)
        frags = 0
        for part in parts:
            core = re.sub(r"\*\*\d+$", "", part.strip()) \
                .strip("()")
            if 1 <= len(core) <= 2 and \
                    any(ord(c) > 127 for c in core):
                frags += 1
        if len(parts) >= 4 and frags >= 4:
            return True
    if ("*" in ans or "·" in ans) and len(factors) >= 5:
        return True
    # Plain-product form: "a*b*d*m*o*s" — the whole answer is
    # single letters multiplied together, 5+ distinct letters.
    compact = ans.replace(" ", "").replace("·", "*")
    if re.fullmatch(r"[a-z](\*\*\d+)?(\*[a-z](\*\*\d+)?)+",
                    compact):
        return len(letters) >= 5
    # Wave 68: Devanagari letter-soup — a bare Hindi word
    # ("बताओ") letter-multiplied by sympy ("ओ*त*ब*ा") slipped
    # under the Latin thresholds (4 factors, no exponents,
    # and the plain-product regex is Latin-only). A product
    # of 4+ distinct single NON-Latin letters/marks with no
    # digit anywhere in the answer is soup, never a genuine
    # solution (real symbolic answers use Latin symbols).
    if not any(ch.isdigit() for ch in ans) \
            and ("*" in ans or "·" in ans):
        nonlatin = {f for f in factors if ord(f) > 127}
        if len(nonlatin) >= 4:
            return True
    return False


def _is_real(question, result):
    """True when the solver's result may be shown as-is."""
    if not isinstance(result, dict):
        return False
    if solve_failed(question, result):
        return False
    if _is_soft(result) or _is_junk(question, result):
        return False
    return bool(_answer_text(result).strip())


def _with_figure(question, result):
    """Wave 86: attach the labelled diagram (figures.py) to a
    real mensuration solve — only when the shape and its
    dimensions are unambiguous in the question AND the
    figure's numbers reproduce the solved answer. Anything
    else returns the result untouched (byte-identical). The
    result is copied before the key is added: the router's
    positive answer cache hands out shared dicts, and they
    must never gain keys."""
    try:
        from figures import figure_for
        fig = figure_for(question, result)
    except Exception:
        fig = None
    if fig is None:
        return result
    out = dict(result)
    out["figure"] = fig
    return out


# ---------------------------------------------------------------------------
# Layer 0: greetings & small talk; Layer 0b: known non-maths topics
# ---------------------------------------------------------------------------

_GREETING_EXACT = {
    "hi", "hii", "hiii", "hello", "helo", "hey", "namaste",
    "namaskar", "kaise ho", "how are you", "kese ho",
    "thank you", "thanks", "dhanyavaad", "dhanyavad", "shukriya",
    "tum kaun ho", "who are you", "your name", "tumhara naam",
    "tumhara naam kya hai", "good morning", "good evening",
    "good afternoon", "good night", "bye", "ok", "okay",
    "haan", "yes", "no", "nahi",
    # Wave 68: Devanagari small talk — "नमस्ते" alone used to
    # fall through to the long guide card because the exact
    # set only knew the Roman spellings.
    "नमस्ते", "नमस्कार", "हेलो", "हाय", "धन्यवाद", "शुक्रिया",
    "कैसे हो", "कैसे हो आप", "तुम कौन हो", "तुम्हारा नाम",
    "तुम्हारा नाम क्या है", "अलविदा", "शुभ प्रभात",
    "शुभ रात्रि", "हाँ", "नहीं", "ठीक है",
}

_GREETING_STARTS = ("hello", "hi ", "hey ", "namaste", "good morning",
                    "good evening", "good afternoon", "thank you",
                    "thanks", "kaise ho", "how are you",
                    "नमस्ते", "नमस्कार", "धन्यवाद", "शुक्रिया",
                    "कैसे हो", "शुभ प्रभात")

_HINDI_MARKERS = ("kya", "hai", "ho", "kaise", "tum", "mera",
                  "ka", "ki", "batao", "samjhao", "dhanyavaad",
                  "shukriya", "nahi", "haan", "namaste", "ganit")


def _looks_hindi(question):
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return True
    words = set(re.findall(r"[a-z]+", q.lower()))
    return bool(words & set(_HINDI_MARKERS))


# Extra Roman-Hindi markers used ONLY for flavour choice:
# _HINDI_MARKERS misses everyday Hinglish words like "kuch",
# "bata", "sawal", "kitna" — "kuch bhi bata do" read as
# English and got the English reply line.
_FLAVOUR_MARKERS = set(_HINDI_MARKERS) | {
    "kuch", "bata", "chahiye", "sawal", "jawab", "kitna",
    "kitne", "kitni", "wala", "wali", "mujhe", "hain",
    "dunga", "hoga", "hogi", "raha", "rahi", "mera", "mere",
}


def _flavour(question):
    """Wave 68: the script flavour of a question — "dev"
    (Devanagari Hindi), "roman" (Hinglish in Latin letters)
    or "en". The friendly one-line replies (greeting,
    maths-only guard, not-found) are written per flavour, so
    a Devanagari question no longer gets a Roman-Hindi reply
    (the mixed-language mess Suraj flagged on 15 Nov 2026)
    and a Hinglish question gets Hinglish back."""
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        return "dev"
    if _looks_hindi(q):
        return "roman"
    words = set(re.findall(r"[a-z]+", q.lower()))
    return "roman" if words & _FLAVOUR_MARKERS else "en"


def _greeting_kind(question):
    """Return a greeting key when the WHOLE message (short, no
    digits, no operators) is small talk, else None. A greeting
    glued to a real question ("hello, solve 2+2") is NOT small
    talk — the salvage layer handles those."""
    q = str(question or "").strip().lower()
    q = re.sub(r"[!?.,;:\"।]+", "", q).strip()
    if not q or any(ch.isdigit() for ch in q):
        return None
    if any(ch in q for ch in "+-*/^=<>%"):
        return None
    if len(q.split()) > 5:
        return None
    if q in _GREETING_EXACT:
        return q
    for start in _GREETING_STARTS:
        if q.startswith(start):
            return start.strip()
    return None


_NONMATHS_KEYWORDS = (
    "capital of", "capital kya", "rajdhaani", "prime minister",
    "pradhan mantri", "president of", "cricket", "football",
    "movie", "film", "song", "gaana", "weather", "mausam",
    "photosynthesis", "prakash sanshleshan", "sky blue",
    "aasmaan neela", "news", "khabar", "meaning of love",
    "girlfriend", "boyfriend", "joke", "chutkula",
    "who won", "match ka score", "score kya",
    # Wave 68: the same topics in Devanagari — "भारत की
    # राजधानी क्या है?" used to miss every Roman keyword and
    # land on the long guide card.
    "राजधानी", "प्रधानमंत्री", "प्रधान मंत्री", "राष्ट्रपति",
    "मौसम", "फ़िल्म", "फिल्म", "गाना", "चुटकुला",
    "मैच का स्कोर",
)


def _is_nonmaths(question):
    q = str(question or "").lower()
    if any(ch.isdigit() for ch in q) and any(
            ch in q for ch in "+-*/^=%"):
        return False  # an actual calculation rides along; not ours
    # Wave 56: set-counting word problems legitimately talk
    # about games — "30 play cricket and 25 play football.
    # If 12 play both, how many play neither?" is a Class
    # 10 sets question with real numbers, not a sports
    # question. The counting shape (digits + play
    # both/neither, or the power-set ask) is maths.
    if any(ch.isdigit() for ch in q) and (
            "play both" in q or "play neither" in q
            or "power set" in q):
        return False
    # Wave 59: Hinglish story dressing — sets/ages/geometry
    # word problems mention cricket or football as scene
    # colour ("30 ladke cricket khelte hain... dono khelte
    # hain, kitne ladke?", a brother who "cricket khelta
    # hai" in an ages story, a sphere described as a
    # football). Digits + a quantitative ask + a maths
    # context word is a maths question, not sports chat.
    if any(ch.isdigit() for ch in q) and (
            "kitna" in q or "kitne" in q or "kitni" in q
            or "how many" in q or "how much" in q
            or "कितना" in q or "कितने" in q or "कितनी" in q) and any(
            w in q for w in (
                "dono", "khelte", "khelta", "umar", "yog",
                "antar", "trijya", "volume", "kshetrafal",
                "paridhi", "doori", "unchai", "anupat",
                "anupaat", "sambhavna", "probability",
                "ausat", "byaj", "speed", "train",
                # Wave 68: the same maths-context words in
                # Devanagari, so a Hindi sets/ages/geometry
                # story that merely mentions a game stays a
                # maths question.
                "दोनों", "खेलते", "खेलता", "उम्र", "योग",
                "अंतर", "त्रिज्या", "आयतन", "क्षेत्रफल",
                "परिधि", "दूरी", "ऊँचाई", "अनुपात",
                "संभावना", "औसत", "ब्याज", "चाल")):
        return False
    return any(kw in q for kw in _NONMATHS_KEYWORDS)


def _friendly_result(kind, answer, steps, hindi):
    return {
        "type": "Ganitra",
        "op": kind,
        "answer": answer,
        "steps": steps,
        "fallback": True,
        "fallback_kind": kind,
    }


def _plain_result(kind, answer, hindi, steps=None):
    """Wave 68: a PLAIN reply — the chat renders it as one
    simple bubble line (plus any guidance lines in `steps` as
    quiet sub-lines), never as an answer card with a badge,
    steps panel, advice or icon row. Suraj's rule (15 Nov
    2026): greetings, the maths-only guard, gibberish and
    unsolved questions get ONE short line, nothing more.
    `plain_reply` is the sentinel the chat renderer keys on;
    the classic pages render the same text plainly too.
    Merge-5: the result ALSO carries Wave 67's `plain` flag,
    so both waves' renderers and i18n gates (result_is_plain)
    treat it as the same one-line reply."""
    result = _friendly_result(kind, answer, steps or [], hindi)
    result["plain_reply"] = True
    result["plain"] = True
    return result


# ---------------------------------------------------------------------------
# Wave 67: the one-line not-found answer
# ---------------------------------------------------------------------------

_HINGLISH_NOT_FOUND = "Answer nahi mila."


def _not_found_line(question, hindi, lang=None, lang_request=None):
    """The not-found line in the question's own language:
    Devanagari question -> Hindi (Marathi UI keeps its own
    line), Roman Hinglish -> "Answer nahi mila.", a bn/mr/ta/te
    UI language -> its i18n line, otherwise English. The
    Devanagari/Hinglish wording is Suraj's spec verbatim; the
    rest ride the i18n "answer_not_found" key.

    Wave 107: an explicit language request in the message
    (lang_request: "hi" / "en" / "hinglish") outranks the
    question's own language here exactly as it does for the
    answer itself."""
    if lang_request == "hi":
        return get_strings("hi")["answer_not_found"]
    if lang_request == "hinglish":
        return _HINGLISH_NOT_FOUND
    if lang_request == "en":
        return get_strings("en")["answer_not_found"]
    q = str(question or "")
    if any("ऀ" <= ch <= "ॿ" for ch in q):
        if lang == "mr":
            return get_strings("mr")["answer_not_found"]
        return get_strings("hi")["answer_not_found"]
    if hindi:
        return _HINGLISH_NOT_FOUND
    if lang in ("bn", "mr", "ta", "te"):
        return get_strings(lang)["answer_not_found"]
    if lang == "hi":
        return _HINGLISH_NOT_FOUND
    return get_strings("en")["answer_not_found"]


def _not_found_result(question, hindi, lang=None, lang_request=None):
    """The ONLY answer to anything that was not solved: one
    short line, no steps, nothing else. fallback_kind ==
    "not_found" is the sentinel every renderer gates on (the
    chat shows a plain minimal bubble; i18n gives it no
    explanation / advice / teach lines)."""
    return {
        "type": "Ganitra",
        "op": "not_found",
        "answer": _not_found_line(question, hindi, lang,
                                  lang_request),
        "steps": [],
        "fallback": True,
        "fallback_kind": "not_found",
        # Merge-5: Wave 68's chat renderer keys on plain_reply,
        # Wave 67's on plain / the not_found kind — carry both
        # flags so the one line renders plainly everywhere.
        "plain": True,
        "plain_reply": True,
    }


_GREETING_LINES = {
    "default": {
        "en": "Hello! 😊 I'm doing great. Send me a maths "
              "question and I'll solve it step by step.",
        "roman": "Namaste! 😊 Main bilkul theek hoon. Apna "
                 "maths ka sawal bhejo — main step-by-step "
                 "hal dunga.",
        "dev": "नमस्ते! 😊 मैं बिल्कुल ठीक हूँ। अपना गणित का "
               "सवाल भेजिए — मैं चरण-दर-चरण हल दूँगा।",
    },
    "thanks": {
        "en": "You're welcome! 😊 Send me another maths "
              "question any time.",
        "roman": "Koi baat nahi! 😊 Kuch aur maths ka sawal "
                 "ho to bhejo.",
        "dev": "कोई बात नहीं! 😊 और कोई गणित का सवाल हो तो "
               "भेजिए।",
    },
    "who": {
        "en": "I'm Ganitra — your maths friend. Type or "
              "photograph any maths question and I'll solve "
              "it step by step.",
        "roman": "Main Ganitra hoon — tumhara maths dost. "
                 "Koi bhi ganit ka sawal likho ya photo bhejo, "
                 "main step-by-step hal dunga.",
        "dev": "मैं Ganitra हूँ — आपका गणित दोस्त। कोई भी "
               "गणित का सवाल लिखिए या फ़ोटो भेजिए, मैं "
               "चरण-दर-चरण हल दूँगा।",
    },
    "bye": {
        "en": "Bye! 👋 Whenever maths gets stuck, I'm right "
              "here.",
        "roman": "Bye! 👋 Jab bhi maths me atak jao, main "
                 "yahi hoon.",
        "dev": "अलविदा! 👋 जब भी गणित में अटकें, मैं यहीं हूँ।",
    },
}


def _greeting_result(question, hindi, flavour=None):
    # Merge-5 (decided rule 1): a greeting gets Wave 68's
    # friendly per-flavour ONE line with plain rendering —
    # NOT Wave 67's "Answer not found." (a friendly hello
    # deserves a friendly line).
    g = _greeting_kind(question)
    if g is None:
        return None
    if flavour is None:
        flavour = _flavour(question)
    if g in ("thank you", "thanks", "dhanyavaad", "dhanyavad",
             "shukriya", "धन्यवाद", "शुक्रिया"):
        group = "thanks"
    elif g in ("tum kaun ho", "who are you", "your name",
               "tumhara naam", "tumhara naam kya hai",
               "तुम कौन हो", "तुम्हारा नाम",
               "तुम्हारा नाम क्या है"):
        group = "who"
    elif g in ("bye", "अलविदा"):
        group = "bye"
    else:
        group = "default"
    return _plain_result(
        "greeting", _GREETING_LINES[group][flavour], hindi)


_NONMATHS_LINES = {
    # Merge-5 (decided rule 3): ONE guard line in the
    # question's own flavour, plain rendering (Wave 68
    # behaviour, Wave 67's plain flag preserved via
    # _plain_result). The en/roman texts are Wave 67's
    # trimmed guard sentences verbatim (pinned by
    # test_wave67); the Devanagari line is Wave 68's, so a
    # Hindi question gets a Hindi guard line.
    "en": "That's not a maths question — Ganitra only "
          "solves Maths.",
    "roman": "Ye sawal maths ka nahi hai — Ganitra sirf Maths "
             "ke sawal hal karta hai।",
    "dev": "यह सवाल गणित का नहीं है — मैं सिर्फ़ गणित के "
           "सवाल हल करता हूँ। 😊 कोई गणित का सवाल भेजिए, "
           "चरण-दर-चरण हल दूँगा।",
}


def _nonmaths_result(question, hindi, flavour=None):
    if flavour is None:
        flavour = _flavour(question)
    return _plain_result(
        "nonmaths", _NONMATHS_LINES[flavour], hindi)


# ---------------------------------------------------------------------------
# Layer 0c (Wave 20, Suraj 12 Nov 2026): SCIENCE questions. A
# Physics/Chemistry/Biology question must get an honest
# "Ganitra is for Maths" reply plus the concept's formula as
# GUIDANCE — never a force-solved fake answer. (The reported
# case: a refractive-index question was salvaged into the
# fragment "2 x 10" from "2 x 10^8" and answered by the junior
# times-pair solver.) This layer runs only when the solver did
# NOT really answer, so genuine maths that merely mentions a
# science word (a calculus velocity problem the solver solves
# properly) is never disturbed.
# ---------------------------------------------------------------------------

def _science_result(question, hindi, flavour=None):
    # Merge-5: Wave 68's per-flavour version, kept as-is;
    # _plain_result now also sets Wave 67's `plain` flag,
    # so the guard renders plainly under both waves.
    # Wave 68: the topic line now comes in the question's own
    # script (a Devanagari Physics question used to get the
    # Roman-Hindi line), and the result is a PLAIN reply: the
    # guard line plus the formula guidance as quiet sub-lines
    # — no answer card, no extra invitation step (the guard
    # line already says what Ganitra does). The guidance
    # content itself is Wave 20's, unchanged.
    q = str(question or "").lower()
    if flavour is None:
        flavour = _flavour(question)
    if "refractive" in q or "speed of light" in q \
            or "ray of light" in q or "light ray" in q:
        steps = [
            "Formula (guidance): refractive index of B with "
            "respect to A, n = (speed of light in A) ÷ "
            "(speed of light in B).",
            "So speed in B = (speed in A) ÷ n — put your values "
            "into this formula and the Physics answer follows.",
        ]
        topic_line = {
            "en": "This is a Physics (Light / Optics) "
                  "question — Ganitra only solves Maths, "
                  "so I won't fake an answer for it. 😊",
            "roman": "Ye Physics (Prakash / Optics) ka sawal "
                     "hai — Ganitra sirf Maths ke sawal hal "
                     "karta hai, isliye main iska nakli hal "
                     "nahi dunga. 😊",
            "dev": "यह Physics (प्रकाश / Optics) का सवाल है — "
                   "Ganitra सिर्फ़ Maths के सवाल हल करता है, "
                   "इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    elif any(w in q for w in ("velocity", "acceleration", "force",
                              "newton", "momentum", "friction",
                              "gravity", "kinetic energy",
                              "potential energy")):
        steps = [
            "Useful formulas (guidance): speed v = distance ÷ "
            "time; acceleration a = (v − u) ÷ t; force F = "
            "mass × acceleration.",
        ]
        topic_line = {
            "en": "This is a Physics (Motion / Force) "
                  "question — Ganitra only solves Maths, "
                  "so I won't fake an answer for it. 😊",
            "roman": "Ye Physics (Gati / Bal) ka sawal hai "
                     "— Ganitra sirf Maths ke sawal hal "
                     "karta hai, isliye main iska nakli hal "
                     "nahi dunga. 😊",
            "dev": "यह Physics (गति / बल) का सवाल है — "
                   "Ganitra सिर्फ़ Maths के सवाल हल करता है, "
                   "इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    elif any(w in q for w in ("voltage", "ampere", "resistance",
                              "ohm", "electric current", "circuit",
                              "capacitor")):
        steps = [
            "Useful formula (guidance): Ohm's law — V = I × R "
            "(voltage = current × resistance).",
        ]
        topic_line = {
            "en": "This is a Physics (Electricity) question "
                  "— Ganitra only solves Maths, so I won't "
                  "fake an answer for it. 😊",
            "roman": "Ye Physics (Bijli / Electricity) ka "
                     "sawal hai — Ganitra sirf Maths ke sawal "
                     "hal karta hai, isliye main iska nakli "
                     "hal nahi dunga. 😊",
            "dev": "यह Physics (बिजली / Electricity) का सवाल "
                   "है — Ganitra सिर्फ़ Maths के सवाल हल करता "
                   "है, इसलिए मैं इसका नकली हल नहीं दूँगा। 😊",
        }[flavour]
    else:
        steps = []
        topic_line = {
            "en": "This is a Science question — Ganitra "
                  "only solves Maths, so I won't fake an "
                  "answer for it. 😊",
            "roman": "Ye Science ka sawal hai — Ganitra "
                     "sirf Maths ke sawal hal karta hai, "
                     "isliye main iska nakli hal nahi "
                     "dunga. 😊",
            "dev": "यह Science का सवाल है — Ganitra सिर्फ़ "
                   "Maths के सवाल हल करता है, इसलिए मैं इसका "
                   "नकली हल नहीं दूँगा। 😊",
        }[flavour]
    return _plain_result("science", topic_line, hindi, steps)


# ---------------------------------------------------------------------------
# Layer 1: salvage — strip the chatter, solve the maths inside
# ---------------------------------------------------------------------------

_FILLER_WORDS = {
    "please", "plz", "batao", "bata", "samjhao", "samjha", "do",
    "karo", "kar", "nikalo", "help", "me", "my", "homework",
    "says", "say", "question", "sawal", "wala", "wali", "hai",
    "kitna", "kitne", "hoga", "hoge", "chahiye", "mujhe", "mera",
    "mere", "find", "the", "value", "what", "is", "when", "tell",
    "usko", "isko", "yeh", "ye", "aur", "ka", "ki", "ke", "ko",
    "se", "me", "mein", "par", "bhi", "toh", "to", "a", "an",
    "of", "for", "solve", "this", "that", "it", "just", "can",
    "you", "could", "would", "dear", "teacher", "sir", "madam",
    "bhai", "bro", "yar", "yaar", "abhi", "jaldi", "zara",
    "thoda", "answer", "ans", "solution", "hal",
}


def _strip_filler(question):
    tokens = re.findall(r"[^\s]+", str(question or ""))
    kept = [t for t in tokens
            if t.strip(".,?!;:\"'").lower() not in _FILLER_WORDS]
    return " ".join(kept).strip(" .,?!;:")


_MATHY_TOKEN = re.compile(r"^[0-9a-zA-Z\.\+\-\*/\^\(\)%]+$")


def _mathy(token):
    """A token that can belong to an equation: only maths
    characters, and either it carries a digit, is an operator,
    or is a short symbol (x, x^2, 3x). Plain English/Hindi words
    ("when", "please", "batao") are never mathy — they bound the
    extraction."""
    t = token.strip(".,?!;:\"'")
    if not t or not _MATHY_TOKEN.match(t):
        return False
    if any(ch.isdigit() for ch in t):
        return True
    if t in ("+", "-", "*", "/", "=", "^", "(", ")", "x", "×"):
        return True
    return len(t) <= 3 and not t.isalpha() or (
        len(t) <= 3 and t.lower() in ("x", "y", "z", "a", "b"))


def _extract_equation(question):
    """Find "3x + 7 = 22" inside "my homework says find x when
    3x + 7 = 22 please batao": locate the '=' and expand token
    by token while the neighbours are mathy."""
    tokens = str(question or "").split()
    for i, tok in enumerate(tokens):
        if "=" not in tok:
            continue
        lo = i
        while lo > 0 and _mathy(tokens[lo - 1]):
            lo -= 1
        hi = i
        while hi < len(tokens) - 1 and _mathy(tokens[hi + 1]):
            hi += 1
        cand = " ".join(tokens[lo:hi + 1]).strip(" .,?!;:")
        if any(ch.isdigit() for ch in cand) and \
                any(ch.isalpha() for ch in cand.split("=")[0]):
            return cand
    return None


def _candidates(question):
    """Possible maths cores inside a messy question, most
    specific first: an equation, a percentage, an arithmetic
    chain (only when there is no equation — a chain inside an
    equation is a fragment, not the question), then the
    filler-stripped whole."""
    q = str(question or "")
    out = []

    def add(cand):
        cand = (cand or "").strip(" .,?!;:")
        if cand and cand not in out and any(ch.isdigit()
                                            for ch in cand):
            out.append(cand)

    equation = _extract_equation(q)
    if equation:
        add(equation)
    m = re.search(r"(\d+(?:\.\d+)?\s*%\s*of\s*\d+(?:\.\d+)?)", q,
                  re.I)
    if m:
        add(m.group(1))
    if not equation:
        for m in re.finditer(
                r"(\d+(?:\.\d+)?(?:\s*[-+\*/x×]\s*"
                r"\d+(?:\.\d+)?)+)", q):
            # Wave 20: a chain that runs straight into a "^" is
            # scientific notation, not a multiplication sum —
            # "2 x 10^8" must never be salvaged as "2 x 10".
            if q[m.end():].lstrip().startswith("^"):
                continue
            add(m.group(1))
    add(_strip_filler(q))
    return out


_FRAC52 = r"\d+\s*/\s*\d+"


def _fraction_ask_value(question):
    """Wave 52 (audit #15): the exact value a two-fraction
    Add/Subtract question asks for, or None. Salvage used to
    "solve" these by solving ONE operand — 'Add 2/3 and 3/4'
    came back as '2/3', the first fraction echoed (31 of 52
    salvage answers in the Wave 35 audit carried a wrong
    value, and the fraction echo was the flagship case). The
    primary solver owns these asks now (solver/arithmetic.py);
    this is the salvage-side guard for any phrasing variant
    that still slips past it: a salvaged result for such a
    question is only believable if its value IS the sum /
    difference."""
    from fractions import Fraction
    q = str(question or "").lower()
    fracs = re.findall(_FRAC52, q)
    if len(fracs) < 2:
        return None
    first = Fraction(fracs[0].replace(" ", ""))
    second = Fraction(fracs[1].replace(" ", ""))
    if re.search(r"\bsubtract\b", q):
        # "Subtract A from B": the first fraction named is
        # the one taken away.
        return second - first
    if re.search(r"\badd\b|\bsum\b", q):
        return first + second
    return None


def _result_value(result):
    """Best-effort numeric value of a result's answer: the
    structured value/numeric fields first, then a fraction
    or decimal read out of the answer text."""
    for key in ("value", "numeric"):
        v = (result or {}).get(key)
        if isinstance(v, (int, float)):
            return float(v)
    ans = _answer_text(result)
    m = re.search(r"(-?\d+)\s*/\s*(\d+)", ans)
    if m and int(m.group(2)):
        return int(m.group(1)) / int(m.group(2))
    m = re.search(r"-?\d+(?:\.\d+)?", ans)
    return float(m.group(0)) if m else None


def _fraction_echo(question, result):
    """Wave 58 guard: for a two-fraction add/subtract ASK, a
    salvaged answer that merely repeats one of the OPERANDS
    (and is not the asked sum/difference) is an echo, never a
    solution — reject the candidate. With the primary word
    patterns in arithmetic.py this is defence in depth for
    rewordings they do not cover."""
    ql = str(question).lower()
    if not re.search(r"\b(add|subtract|sum|difference|plus|"
                     r"minus)\b", ql):
        return False
    fr = []
    for a, b in re.findall(r"(\d+)\s*/\s*(\d+)", str(question)):
        if int(b) != 0:
            fr.append(Fraction(int(a), int(b)))
    if len(fr) != 2:
        return False
    val = result.get("numeric", result.get("value"))
    if isinstance(val, (list, tuple)):
        return False
    if val is None:
        m = re.match(r"\s*(-?\d+)\s*/\s*(\d+)\s*$",
                     str(result.get("answer", "")))
        if m:
            val = Fraction(int(m.group(1)), int(m.group(2)))
        else:
            try:
                val = Fraction(
                    str(result.get("answer", "")).strip())
            except Exception:
                return False
    try:
        fv = Fraction(val).limit_denominator(10 ** 6)
    except Exception:
        return False
    if fv in (fr[0] + fr[1], fr[0] - fr[1], fr[1] - fr[0]):
        return False
    return fv in fr


def _salvage(question, hindi):
    # Wave 20: never salvage a science question — its numbers
    # are not a maths sum hiding in the text (see Layer 0c).
    if has_science_signal(question):
        return None
    _want52 = _fraction_ask_value(question)
    for cand in _candidates(question):
        if cand.strip().lower() == str(question).strip().lower():
            continue  # identical to the original: already failed
        try:
            result = solve_question(cand)
        except Exception:
            continue
        if _is_real(cand, result):
            if _want52 is not None:
                _got52 = _result_value(result)
                if _got52 is None or abs(
                        _got52 - float(_want52)) > 0.01:
                    continue  # an echoed operand, not the answer
            note = (f"Solved the maths part of your question: "
                    f"{cand}")
            result = dict(result)
            result["steps"] = [note] + list(
                result.get("steps") or [])
            result["fallback"] = True
            result["fallback_kind"] = "salvage"
            result["salvaged_from"] = cand
            return result
    return None


# ---------------------------------------------------------------------------
# Layer 2: concepts
# ---------------------------------------------------------------------------

def _concept_result(question, hindi):
    entry = find_concept(question)
    if entry is None:
        # Wave 57: retry on the spelling-folded text — students
        # ask "byaj kaise nikalte hai?" / "ausat kaise nikale?"
        # with spellings the keyword lists are not written in.
        folded = normalize_spelling(question)
        if folded != question:
            entry = find_concept(folded)
    if entry is None:
        return None
    ex = entry["example"]
    steps = [entry["explain"],
             f"Hinglish me: {entry['hinglish']}",
             f"Example: {ex['q']}"]
    steps.extend(ex["steps"])
    steps.append(f"Example answer: {ex['answer']}")
    return {
        "type": "Concept",
        "op": entry["id"],
        "answer": f"{entry['title']} — {entry['formula']}",
        "steps": steps,
        "fallback": True,
        "fallback_kind": "concept",
        "concept_id": entry["id"],
    }


# ---------------------------------------------------------------------------
# Layer 3: topic guess + a similar SOLVED example (honestly labelled)
# ---------------------------------------------------------------------------

_TOPIC_EXAMPLES = (
    (("train", "speed", "chaal", "distance", "doori", "yatra",
      "km/h", "kmh"),
     "Speed–Distance",
     "A train travels at 60 km/h for 2 hours. How far does it go?",
     "60 km/h for 2 hours"),
    (("interest", "byaj", "ब्याज", "bank"),
     "Simple Interest",
     "Find the simple interest on ₹1,000 at 5% for 2 years.",
     "simple interest on 1000 at 5% for 2 years"),
    (("percent", "%", "pratishat", "प्रतिशत", "discount"),
     "Percentage",
     "Find 15% of 240.",
     "15% of 240"),
    (("quadratic", "x^2", "x²"),
     "Quadratic Equations",
     "Solve x² - 7x + 12 = 0.",
     "x^2 - 7x + 12 = 0"),
    (("equation", "find x", "solve x", "samikaran"),
     "Equations",
     "Solve 2x + 3 = 11.",
     "2x + 3 = 11"),
    (("area", "kshetrafal", "क्षेत्रफल", "perimeter", "parimap"),
     "Area",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
    (("sin", "cos", "tan", "trig"),
     "Trigonometry",
     "Find the value of sin 30.",
     "sin 30"),
    (("mean", "average", "ausat", "median"),
     "Statistics",
     "Find the mean of 3, 6, 9, 12.",
     "mean of 3, 6, 9, 12"),
    (("rupee", "rupaye", "रुपये", "money", "paisa", "paise",
      "cost", "price", "keemat"),
     "Money Maths",
     "Find 15% of ₹200.",
     "15% of 200"),
    (("triangle", "tribhuj", "त्रिभुज"),
     "Triangles",
     "Find the area of a circle with radius 7 cm.",
     "area of circle with radius 7"),
)


def _similar_result(question, hindi):
    # Wave 57: match topic keywords against the original text AND
    # its spelling-folded form ("tren wala sawal" -> train topic).
    q = (str(question or "") + " "
         + normalize_spelling(question)).lower()
    for keywords, label, example_q, example_solve in _TOPIC_EXAMPLES:
        if any(kw in q for kw in keywords):
            try:
                solved = solve_question(example_solve)
            except Exception:
                solved = None
            if solved is not None and _is_real(example_solve,
                                               solved):
                if hindi:
                    head = ("Tumhare sawal ka exact hal abhi nahi "
                            "mila, lekin usi topic ka ek solved "
                            "example ye raha:")
                    ask = ("Apne sawal ki exact sankhyayen (numbers) "
                           "ek baar saaf-saaf likh kar bhejo, main "
                           "usi ka hal dunga.")
                else:
                    head = ("I couldn't solve your exact question "
                            "yet, but here is a solved example from "
                            "the same topic:")
                    ask = ("Now type your question once more with "
                           "its exact numbers, and I'll solve yours.")
                steps = [head, f"Similar example: {example_q}"]
                steps.extend(
                    str(s) for s in (solved.get("steps") or []))
                steps.append(ask)
                return {
                    "type": "Similar example",
                    "op": label,
                    "answer": (f"Similar example ({label}): "
                               f"{solved.get('answer', '')}"),
                    "steps": steps,
                    "fallback": True,
                    "fallback_kind": "similar",
                }
    return None


# ---------------------------------------------------------------------------
# Layer 4: vague asks, gibberish, and the general guide
# ---------------------------------------------------------------------------

_VAGUE_WORDS = {
    "samjhao", "samjha", "batao", "bata", "solve", "help",
    "explain", "ye", "yeh", "wala", "wali", "this", "that",
    "isko", "usko", "karo", "kar", "do", "please", "plz",
    "maths", "math", "ganit", "question", "sawal", "abhi",
    "kuch", "bhi", "ek", "the", "a", "an", "it", "me", "my",
}


_VAGUE_WORDS_DEV = {
    "समझाओ", "समझा", "बताओ", "बता", "बताइए", "हल", "करो",
    "कर", "दो", "कुछ", "भी", "एक", "गणित", "सवाल", "यह",
    "ये", "वाला", "वाली", "इसको", "उसको", "अभी", "कृपया",
    "मदद",
}


def _is_vague(question):
    words = re.findall(r"[a-z]+", str(question or "").lower())
    if words:
        if len(words) > 6:
            return False
        if any(ch.isdigit() for ch in str(question or "")):
            return False
        return all(w in _VAGUE_WORDS for w in words)
    # Wave 68: the same test for Devanagari asks — "समझाओ"
    # alone used to fall to the not-found line instead of
    # the friendly send-your-question reply.
    dev_words = re.findall(r"[ऀ-ॿ]+", str(question or ""))
    if not dev_words or len(dev_words) > 6:
        return False
    if any(ch.isdigit() for ch in str(question or "")):
        return False
    return all(w in _VAGUE_WORDS_DEV for w in dev_words)


_KNOWN_WORDS = _VAGUE_WORDS | _FILLER_WORDS | {
    "what", "is", "of", "the", "a", "an", "in", "on", "for",
    "and", "or", "to", "how", "why", "when", "which", "find",
    "value", "area", "volume", "radius", "circle", "square",
    "triangle", "rectangle", "angle", "degree", "degrees",
    "percent", "percentage", "probability", "derivative",
    "integral", "integrate", "limit", "equation", "root",
    "roots", "power", "cube", "prime", "factor", "factors",
    "expand", "simplify", "graph", "plot", "sin", "cos", "tan",
    "log", "mean", "mode", "median", "hcf", "lcm", "gcd",
    "theorem", "formula", "interest", "speed", "distance",
    "time", "number", "numbers", "sum", "product", "difference",
}


def _is_gibberish(question):
    q = str(question or "")
    if any(ch.isdigit() for ch in q):
        return False
    if any(ch in q for ch in "+-*/^=<>%"):
        return False
    words = [w for w in re.findall(r"[a-z]+", q.lower())
             if len(w) >= 3]
    if len(words) < 2:
        return False
    unknown = [w for w in words if w not in _KNOWN_WORDS]
    return len(unknown) >= 2 and len(unknown) == len(words)


# Wave 68 (Suraj, 15 Nov 2026 — the rule Wave 67 also
# implements): when nothing solved, the reply is ONE short
# line in the question's own language/script. No guide card,
# no "questions I solve for sure" panel, no tips, no advice.
_NOT_FOUND_LINES = {
    "en": "Answer not found.",
    "roman": "Answer nahi mila.",
    "dev": "उत्तर नहीं मिला।",
}

_VAGUE_LINES = {
    "en": "Of course! 😊 Just send me your full maths "
          "question — like 'solve 2x + 3 = 7' — and I'll "
          "solve it step by step.",
    "roman": "Bilkul! 😊 Apna maths ka sawal poora likh kar "
             "bhejo — jaise 'solve 2x + 3 = 7' — main "
             "step-by-step hal dunga.",
    "dev": "बिल्कुल! 😊 अपना गणित का सवाल पूरा लिखकर भेजिए "
           "— जैसे '2x + 3 = 7 हल कीजिए' — मैं चरण-दर-चरण "
           "हल दूँगा।",
}


def _guide_result(question, hindi, kind, flavour=None):
    if flavour is None:
        flavour = _flavour(question)
    if kind == "vague":
        return _plain_result(
            "vague", _VAGUE_LINES[flavour], hindi)
    # "gibberish" (letter-soup / jumbled words) and "guide"
    # (a real question nothing could solve — the AI brains
    # above get their chance first, since kind "guide" is in
    # _GEMINI_KINDS and this result is only settled when they
    # return None): both are the same honest one-liner. The
    # fallback_kind is preserved for analytics/tests; the
    # content is the Wave 67/68 not-found line.
    return _plain_result(
        kind, _NOT_FOUND_LINES[flavour], hindi)


# ---------------------------------------------------------------------------
# Wave 37: the Gemini free-tier second brain (gemini_fallback.py)
# Wave 41: Groq (groq_fallback.py) joins as the second brain —
# consulted only when Gemini returned None.
# Wave 108: OpenRouter (openrouter_fallback.py) joins as the
# third brain — consulted only when Gemini AND Groq both
# returned None.
# ---------------------------------------------------------------------------

# The fallback kinds that mean "the student's OWN question is
# still unanswered": a similar example, a concept card, or the
# general guide. Only these may be upgraded by an AI brain.
# Real solver answers, salvage solves, greetings, non-maths
# and science replies never reach the check at all (they
# return earlier), and vague/gibberish asks have no real
# question to send.
_GEMINI_KINDS = ("similar", "concept", "guide")


def _ai_lang(hindi, lang_request):
    """The language instruction handed to the AI brains: a
    Wave-107 explicit request verbatim ("en" / "hi" /
    "hinglish"), else the pre-Wave-107 rule — "hi" for a
    Hindi-looking question, None (the prompt's own
    same-language rule) otherwise."""
    if lang_request in ("en", "hi", "hinglish"):
        return lang_request
    return "hi" if hindi else None


def _gemini_answer(question, hindi, lang_request=None):
    """Ask Gemini for the student's own question. Lazy import
    so the module (and its env key) stays fully optional; ANY
    failure returns None and the honest Wave-18 fallback is
    served exactly as before."""
    try:
        from gemini_fallback import try_gemini_answer
        return try_gemini_answer(question,
                                 _ai_lang(hindi, lang_request))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Wave 39: the Verified Data Bank (bank.py) — exact matches only
# ---------------------------------------------------------------------------

def _bank_answer(question):
    """The banked, SymPy-verified answer for this EXACT question
    (bank.lookup_result), or None. Lazy import + blanket guard,
    same pattern as the Gemini layer: the bank snapshot is an
    optional file and any failure must leave the Wave-18 flow
    exactly as it was."""
    try:
        from bank import lookup_result
        return lookup_result(question)
    except Exception:
        return None


def _groq_answer(question, hindi, lang_request=None):
    """Wave 41: ask Groq for the student's own question —
    only ever called when Gemini returned None. Same contract
    as _gemini_answer: lazy import, ANY failure returns None
    and the honest Wave-18 fallback is served unchanged."""
    try:
        from groq_fallback import try_groq_answer
        return try_groq_answer(question,
                               _ai_lang(hindi, lang_request))
    except Exception:
        return None


def _openrouter_answer(question, hindi):
    """Wave 108: ask OpenRouter for the student's own
    question — only ever called when Gemini AND Groq both
    returned None. Same contract as _gemini_answer: lazy
    import, ANY failure returns None and the honest Wave-18
    fallback is served unchanged."""
    try:
        from openrouter_fallback import try_openrouter_answer
        return try_openrouter_answer(question,
                                     "hi" if hindi else None)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# The entry point
# Wave 90: the not-found learning log hook (notfound_log.py)
# ---------------------------------------------------------------------------

def _log_not_found(question, lang, student_class, terminal_kind):
    """Record a collapsed not-found outcome. Double-guarded:
    notfound_log.log_not_found never raises by contract, and
    this wrapper swallows even an import failure — logging is
    observational and must never slow, break or alter the
    answer. The recorded language is the explicit `lang` when
    the caller supplied one, else the question's own flavour
    mapped to a language label (dev -> hi, roman -> hinglish,
    en -> en)."""
    try:
        from notfound_log import log_not_found
        language = lang
        if not language:
            language = {"dev": "hi", "roman": "hinglish",
                        "en": "en"}[_flavour(question)]
        log_not_found(question, lang=language,
                      student_class=student_class,
                      terminal_kind=terminal_kind)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The entry point
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------

def _with_fallback_chain(question, result, lang=None,
                         student_class=None, lang_request=None):
    """Return `result` unchanged when it is a real solver
    answer; otherwise return an honest fallback result (never
    None, never an error dict). `lang` is the app's UI /
    detected language (Wave 67: it picks the not-found line
    for the bn/mr/ta/te UIs; the line otherwise follows the
    question's own script/words). `student_class` (Wave 90)
    is the signed-in student's class when the caller knows
    it — used only by the not-found learning log.
    `lang_request` (Wave 107) is an explicit answer-language
    request detected in the message ("hi" / "en" /
    "hinglish", from langdetect_local.detect_language_request)
    — when present it outranks the question's own language for
    every language choice made in this layer: the Hindi flag,
    the one-line replies' flavour, the AI brains' prompt
    language and the not-found line. When it is None every
    choice below is exactly the pre-Wave-107 one."""
    if lang_request in ("hi", "hinglish"):
        hindi = True
    elif lang_request == "en":
        hindi = False
    else:
        hindi = _looks_hindi(question)
    req_flavour = {"en": "en", "hi": "dev",
                   "hinglish": "roman"}.get(lang_request)

    # Layer 0 / 0b run before the solver result is even looked
    # at: the solver's letter-products for "hi" / "what is the
    # capital of india" are not answers at all.
    # Merge-5 (decided rule 1): a greeting is NOT "not found" —
    # Wave 68's friendly per-flavour one line is served (kind
    # "greeting", plain rendering). Wave 67's collapse of
    # greetings to the not-found line is superseded here.
    greeting = _greeting_result(question, hindi, req_flavour)
    if greeting is not None:
        return greeting
    if _is_nonmaths(question):
        return _nonmaths_result(question, hindi, req_flavour)

    # Wave 111: the maths-META layer (maths_meta.py) — maths
    # history/creator facts and study/practice/exam advice.
    # It sits here, after the greeting and non-maths guards
    # (so the guards stay authoritative) and before every
    # solving/concept layer, because its whole point is the
    # questions those layers mishandle: a WHO-shaped ask
    # ("Pythagoras theorem kisne banaya tha?") used to be
    # served the WHAT card by the concept layers below, and
    # person/advice asks fell through to the not-found line.
    # The layer's own double gate (who shape + curated
    # topic/person keyword; advice trigger + maths gate) plus
    # its computation veto keep every real problem and every
    # concept ask out — it returns None for all of them, and
    # the flow below is then exactly the pre-Wave-111 one.
    try:
        from maths_meta import meta_result
        meta = meta_result(question,
                           req_flavour or _flavour(question))
    except Exception:
        meta = None
    if meta is not None:
        return meta

    if _is_real(question, result):
        # Wave 100: a multi-part bundle (mega-MCQ set, case
        # study) is not one question — a whole-text "solve" of
        # it is a fragment carved out of one part (the Wave 93
        # audit's regression #5 served "x = -2/7" from part
        # (iv)'s line equation as the answer to a 15-part ICSE
        # set). The parts are the authority: when the bundle
        # splits and at least one part verifiably solves, the
        # multipart answer stands instead of the fragment.
        try:
            from multipart import multipart_preferred
            mp_preferred = multipart_preferred(question, result)
        except Exception:
            mp_preferred = None
        if mp_preferred is not None:
            return _with_figure(question, mp_preferred)
        # Wave 95: for a proof ask, a SymPy-verified identity
        # derivation (proofs.py) upgrades the solver's bare
        # verdict ("Identity verified ✔" with no working, or a
        # parse-flawed "Not an identity" for true identities
        # like (sin A + cos A)^2 = 1 + 2 sin A cos A). The
        # layer returns None for anything it cannot verify,
        # so a genuinely false identity keeps the solver's
        # "Not an identity" and every non-proof real answer
        # is untouched.
        try:
            from proofs import proof_result
            proof = proof_result(question, hindi)
        except Exception:
            proof = None
        if proof is not None:
            return proof
        # Wave 76: a question that arrived WITH options gets
        # its answer named by option even when the whole text
        # solved as-is — and for MCQs the STEM solve is the
        # authority, because the option numbers pollute the
        # full-text solve (the HCF of "12 and 18 (A) 3 (B) 6
        # (C) 9 (D) 36" comes out as the HCF of all six numbers
        # — the wrong option). mcq_preferred only fires on an
        # exact one-option match and returns None otherwise,
        # leaving the real result untouched.
        try:
            from mcq import mcq_preferred
            wrapped = mcq_preferred(question, result)
        except Exception:
            wrapped = None
        if wrapped is not None:
            return _with_figure(question, wrapped)
        # Wave 82: the same authority question for OR bundles
        # and case-study sets — a whole bundle fed to the
        # solver as one text can come back as a fragment
        # dressed as an answer (the matrix/system OR bundle
        # "solves" to 2*x - y + 6, a shred of one equation).
        # formats_preferred serves the format result only
        # when a part verifiably solves AND the whole-text
        # answer matches none of the solved parts' answers;
        # a genuine whole-text solve of a part is left
        # untouched.
        try:
            from formats import formats_preferred
            preferred = formats_preferred(question, result)
        except Exception:
            preferred = None
        if preferred is not None:
            return _with_figure(question, preferred)
        # Wave 103: a polynomial-degree ask whose primary
        # result is the simplify path's mangled expression
        # ("degree of 3x^3 + 2x^2 + 5x + 7" came back as
        # "2*x**2 + 5*x + 10" — the words are eaten into the
        # expression, so the router's failure gate can never
        # see it) is upgraded to the verified degree.
        # degree_upgrade fires only on a strict degree ask
        # whose answer is not already the true degree, so
        # every other real answer is untouched.
        try:
            from solver.gaps103 import degree_upgrade
            upgraded = degree_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        # Wave 115: the hijacked Rekha Ganit asks — a 2x2
        # system solution served for a parallel/perpendicular
        # CHECK, an angle-between-lines ask or a line-through-
        # intersection ask; the ratio echoed back for a
        # dividing-POINT ask; the segment's own line served
        # for its perpendicular bisector. Those results are
        # "real" answers to different questions, so the
        # router's failure gate can never see them.
        # rekha_upgrade fires only on the strict ask shape
        # whose rekha schema settles the question completely,
        # leaving every other real answer untouched.
        try:
            from solver.rekha import rekha_upgrade
            upgraded = rekha_upgrade(question, result)
        except Exception:
            upgraded = None
        if upgraded is not None:
            return _with_figure(question, upgraded)
        return _with_figure(question, result)

    # Wave 20, Layer 0c: a SCIENCE question the solver could not
    # really answer gets the honest maths-only reply + formula
    # guidance — BEFORE salvage, which would otherwise carve a
    # fake "maths part" out of it (the refractive-index case).
    if has_science_signal(question):
        return _science_result(question, hindi, req_flavour)

    # Wave 39: the Verified Data Bank exact-match layer. It sits
    # AFTER the science guard (a science question is never
    # served from the bank) and after a real solver answer has
    # been served untouched above — what it upgrades is the
    # fall-through: a question the solver could not really
    # answer, whose EXACT normalised text matches a banked item,
    # gets that item's SymPy-verified steps + final answer
    # instead of a salvaged fragment, a similar example or the
    # general guide. Exact-only, so it can never shadow the
    # solver for a non-identical question; on a miss the layers
    # below run exactly as before.
    banked = _bank_answer(question)
    if banked is not None:
        return banked

    # Wave 117: the Live Bank (livebank.py) — questions
    # students actually asked, answered before by a
    # deterministic layer and stored VERIFIED at ask time.
    # It sits exactly where the master bank sits (after the
    # science guard, after a real solver answer, before the
    # fall-through layers it can only ever reproduce), and
    # serves only a language-key match: a repeat ask gets
    # its stored answer instantly instead of re-paying the
    # salvage / concept / AI layers. Pending (AI) rows are
    # never served — they wait for offline verification.
    live = _livebank_answer(question, lang, lang_request)
    if live is not None:
        return live

    # Wave 76: the MCQ layer (mcq.py). A question that arrives
    # WITH its options ("(a) 12 (b) 18 (c) 24 (d) 36") usually
    # defeats the solver as a whole — the Wave 71 audit counted
    # 75 such failures in a 150-question papers sample — but
    # the STEM alone often solves through the ordinary
    # machinery. This layer extracts stem + options, solves the
    # stem, and serves the stem's own steps with a final answer
    # naming the one option the computed value matches. It
    # sits here — after the science guard and the bank, before
    # salvage (which would otherwise carve a fragment out of
    # the option text) — and returns None unless the stem
    # really solved AND exactly one option matched, so on any
    # doubt the layers below run byte-for-byte as before. An
    # option is never guessed.
    try:
        from mcq import mcq_result
        mcq = mcq_result(question)
    except Exception:
        mcq = None
    if mcq is not None:
        return mcq

    # Wave 100: the multi-part layer (multipart.py) — mega-MCQ
    # bundles, case-study sets and "Hence, …" chains, the
    # paper formats the Wave 93 audit's regressions #3–#5
    # exposed as missing from the live chain. It splits the
    # format, solves the parts through the existing machinery
    # and serves only what settles exactly; unsolved parts
    # carry the one-line not-found. It sits here — after the
    # MCQ layer, before salvage (which would otherwise carve
    # a fragment out of the bundle) — and returns None on any
    # doubt, so the layers below run byte-for-byte as before.
    try:
        from multipart import multipart_result
        multi = multipart_result(question)
    except Exception:
        multi = None
    if multi is not None:
        return multi

    # Wave 95: the proof layer (proofs.py). "Prove that ..."
    # asks the solver could not answer — algebraic identities
    # (which ended at the not-found line) and the irrationality
    # proofs (which the concepts card answered for the WRONG
    # root: a sqrt(5) ask was served the sqrt(2) card) — are
    # answered here, but only when honestly possible: a
    # SymPy-verified identity derivation, or the standard
    # textbook proof from proofs_data.py. Anything else
    # returns None and the layers below run as before.
    try:
        from proofs import proof_result
        proof = proof_result(question, hindi)
    except Exception:
        proof = None
    if proof is not None:
        return proof

    # Wave 82: the paper-format layer (formats.py). Board
    # papers paste three shapes the solver and the MCQ layer
    # cannot use: OR bundles ("Solve A OR Solve B" / "…
    # अथवा …"), Assertion–Reason items, and case-study sets
    # (a passage plus labelled sub-questions). This layer
    # splits the format, solves the parts through the existing
    # machinery, and serves only what it can settle exactly —
    # an OR alternative that really solves, an Assertion–
    # Reason combination both of whose statements a decider
    # in formats.py could decide, a case-study set with at
    # least one solved part. It sits here — after the science
    # guard, the bank and the MCQ layer, before salvage
    # (which would otherwise carve a fragment out of the
    # bundle) — and returns None on any doubt, so the layers
    # below run byte-for-byte as before. An A–R option is
    # never guessed.
    try:
        from formats import formats_result
        formatted = formats_result(question)
    except Exception:
        formatted = None
    if formatted is not None:
        return formatted

    # The solver did not really answer. Work the layers.
    salvaged = _salvage(question, hindi)
    if salvaged is not None:
        return salvaged

    # Wave 75: the topics-library concept layer
    # (concept_topics.py). A genuine concept ask — definition,
    # formula, how-to, difference, why — is answered from the
    # app's own topics library (the topic's method + its
    # verified worked example) instead of the small concepts.py
    # card. It sits here, after the solver, the bank and
    # salvage, so a concrete problem has already had every
    # real chance to solve; its own gate + vetoes keep it from
    # ever capturing one. On no confident topic match the
    # Wave-18 concepts.py card runs exactly as before.
    # Wave 100: the concept layers YIELD to options-bearing
    # (MCQ-shaped) questions. A question that carries options
    # is a problem to solve, not a concept to teach — when
    # every solving layer above has failed it, serving a
    # concept card for its keywords is a hijack (the Wave 93
    # audit's regression #1: "x + 1/x = 3 … value of a - b + c
    # is: (A) 5 (B) 2 (C) 1 (D) -1" was served the Quadratic
    # Formula card). The topics layer already vetoes option
    # markers internally; the concepts.py card did not, so
    # the yield is enforced here for both layers at once.
    # Genuine concept asks carry no option list, so their
    # behaviour is untouched.
    options_bearing = False
    try:
        from mcq import extract_mcq
        options_bearing = extract_mcq(question) is not None
    except Exception:
        options_bearing = False
    concept = None
    if not options_bearing:
        try:
            concept = topic_concept_result(question)
        except Exception:
            concept = None
        if concept is None:
            concept = _concept_result(question, hindi)
    if concept is not None:
        result_out = concept
    else:
        similar = _similar_result(question, hindi)
        if similar is not None:
            result_out = similar
        elif _is_vague(question):
            result_out = _guide_result(question, hindi, "vague",
                                       req_flavour)
        elif _is_gibberish(question):
            # Wave 111: a WHO/ADVICE-shaped MATHS question the
            # curated meta layer missed ("Euler kaun the?")
            # is not gibberish — it is a real question this
            # app cannot answer itself. Classify it as
            # "guide" instead: the content served locally is
            # the identical one-line not-found (via the
            # collapse below), but "guide" is in _GEMINI_KINDS,
            # so in production the AI chain gets its chance
            # at the student's actual question first. Genuine
            # gibberish (no meta shape) is untouched.
            try:
                from maths_meta import is_meta_shaped
                meta_shaped = is_meta_shaped(question)
            except Exception:
                meta_shaped = False
            result_out = _guide_result(
                question, hindi,
                "guide" if meta_shaped else "gibberish",
                req_flavour)
        else:
            result_out = _guide_result(question, hindi, "guide",
                                       req_flavour)

    # Wave 37: when the honest layers still could not answer
    # the student's own question (similar example, concept card
    # or the general guide), ask Gemini (free tier) before
    # settling — solver first, AI only as the fallback. Any
    # Gemini failure leaves the Wave-18 answer untouched.
    # Wave 41: when Gemini returns None, Groq (also free tier)
    # gets the same question before we settle. Exact solves,
    # salvage, greetings, non-maths and science replies have
    # all returned earlier, so neither brain can reach them.
    # Wave 108: when Groq also returns None, OpenRouter (also
    # free tier) gets the same question as the last resort.
    # Wave 75: a topics-library concept answer (source
    # "topics") is verified in-app content (Wave 55) — like
    # the bank, it is exempt from the AI upgrade below, which
    # could otherwise rewrite it and burn free quota.
    if result_out.get("fallback_kind") in _GEMINI_KINDS \
            and result_out.get("source") != "topics":
        ai_result = _gemini_answer(question, hindi, lang_request)
        if ai_result is None:
            ai_result = _groq_answer(question, hindi, lang_request)
        if ai_result is None:
            ai_result = _openrouter_answer(question, hindi)
        if ai_result is not None:
            return ai_result

    # Wave 67: whatever honest layer is still standing here —
    # a similar example, gibberish, the general guide — means
    # the student's OWN question was not solved, so the whole
    # answer collapses to the one not-found line.
    # A concept card is a real answer (formula + worked
    # example for the exact concept asked) and is served as-is.
    # Merge-5 (decided rule 1): a VAGUE ask no longer collapses
    # — _guide_result already settled it as Wave 68's friendly
    # per-flavour line (kind "vague", plain rendering).
    if result_out.get("fallback_kind") in (
            "similar", "gibberish", "guide"):
        # Wave 90: this collapse is THE "Answer not found"
        # outcome — solver, bank, MCQ, salvage, concepts and
        # the AI chain all missed. Record it in the learning
        # log (observational only; the answer below is built
        # exactly as before, whether logging works or not).
        # Wave 107: a Hinglish request is logged as "hinglish"
        # (the session lang only knows it as "hi").
        _log_not_found(
            question,
            "hinglish" if lang_request == "hinglish" else lang,
            student_class, result_out.get("fallback_kind"))
        return _not_found_result(question, hindi, lang,
                                 lang_request)
    return result_out


# ---------------------------------------------------------------------------
# Wave 117: the Live Bank hooks (livebank.py)
# ---------------------------------------------------------------------------

def _livebank_lang_key(question, lang, lang_request):
    """The live bank's language key for one ask — Wave 107's
    rules, owned here because this layer owns the language
    choices: an explicit in-message request wins verbatim
    ("en" / "hi" / "hinglish"); a bn/mr/ta/te session
    language keys under itself (conservative — its answers
    are stored and served only within that language); else
    the question's own flavour decides, with the same
    mapping the Wave 90 log uses (dev -> "hi", roman ->
    "hinglish", en -> "en"). Record and lookup compute the
    key through this one function, so the two sides always
    agree."""
    if lang_request in ("en", "hi", "hinglish"):
        return lang_request
    if lang and lang not in ("en", "hi"):
        return lang
    return {"dev": "hi", "roman": "hinglish",
            "en": "en"}[_flavour(question)]


def _livebank_answer(question, lang, lang_request):
    """The Live Bank's stored VERIFIED answer for this exact
    question + language key (livebank.lookup_live_result),
    or None. Lazy import + blanket guard, same pattern as
    the bank layer above: the store is an accelerator, and
    any failure must leave the chain exactly as it was."""
    try:
        from livebank import lookup_live_result
        return lookup_live_result(
            question,
            _livebank_lang_key(question, lang, lang_request))
    except Exception:
        return None


def _record_livebank(question, result, lang, lang_request):
    """Record one finished outcome in the Live Bank.
    Double-guarded like the Wave 90 hook:
    livebank.record_answer never raises by contract, and
    this wrapper swallows even an import failure — storing
    is observational and must never slow, break or alter
    the answer. Note what is NOT passed: no student class,
    no session, no identity of any kind — the store's
    privacy rule is question text only. A result the Live
    Bank itself just served is not re-recorded (its hit was
    already counted by the serve, and re-storing the served
    copy would bake the live_bank marker into the stored
    payload)."""
    if isinstance(result, dict) and result.get("live_bank"):
        return
    try:
        from livebank import record_answer
        record_answer(
            question, result,
            _livebank_lang_key(question, lang, lang_request))
    except Exception:
        pass


def with_fallback(question, result, lang=None, student_class=None,
                  lang_request=None):
    """The chain above (_with_fallback_chain), plus Wave
    117's record hook: every finished outcome — solver,
    bank, deterministic layer or AI — is offered to the
    Live Bank, which stores the storeable ones (verified
    for deterministic answers, pending for AI answers) so a
    repeat ask can be served instantly. Recording happens
    after the answer is final and can never change it; the
    not-found / non-maths / greeting outcomes are refused
    by the store's own classifier (Wave 90's log owns the
    not-found ones)."""
    out = _with_fallback_chain(question, result, lang=lang,
                               student_class=student_class,
                               lang_request=lang_request)
    _record_livebank(question, out, lang, lang_request)
    return out


def fallback_answer(question, result=None, lang=None,
                    student_class=None, lang_request=None):
    """Convenience wrapper: solve (if no result was given) and
    guarantee a presentable answer dict."""
    if result is None:
        try:
            result = solve_question(question)
        except Exception as e:  # solver must never leak a crash
            result = {"type": "solver", "op": "error",
                      "answer": f"Could not solve this one: {e}",
                      "steps": []}
    return with_fallback(question, result, lang=lang,
                         student_class=student_class,
                         lang_request=lang_request)


__all__ = ["with_fallback", "fallback_answer"]
