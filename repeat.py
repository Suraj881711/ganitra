"""Wave 178: repeat-ask variation (Suraj's standing rule,
19 Nov 2026 ~09:52 IST).

"agar student ek hi sawal baar-baar puche (khaas kar
guidance ke liye), to har baar kuch ALAG ya SPECIAL mile —
same jawab copy-paste kabhi nahi. Pehli baar normal short
jawab, dusri baar naya example ya extra tip, teesri baar
aur depth / related fact / practice sawal — asli teacher
ki tarah."

Mechanism, in three parts:

1. COUNTING (this module + the routes). Every finished
   answer gets a repeat KEY (result_key): the guidance /
   baat / knowledge TOPIC id when the conversational
   layers own the answer — so the same topic asked in
   different words, or in another of the student's
   languages, is still the same ask — and the normalised
   question text for a solved maths answer. The routes
   keep a small per-chat count store in the session
   (session["w178_counts"], the same cookie discipline
   as api.py's Wave-127 turn log: last few chats, bounded
   keys) and bump the count once per finished ask.

2. VARIATION (this module + the content tables in
   guidance.py / maths_meta.py). From the 2nd ask on,
   apply_variation returns a COPY of the result, varied:
   - guidance / knowledge cards: a warm acknowledgement
     opener ("ye sawal tum pehle bhi puch chuke ho…") as
     the first line, the base card untouched in the
     middle, and fresh authored extra lines at the end —
     a new example or extra tip on the 2nd ask, depth /
     a related fact / a practice step from the 3rd.
   - small talk (baat): the topic's alternate authored
     line replaces the one-liner (it has no steps to
     append to).
   - solved maths: the working is NEVER touched — a
     warm framing line goes before it and an offer line
     (detail version / a similar practice question)
     after it. The maths and the answer value are the
     solver's own, byte for byte.
   Openers and extra lines rotate with the count, so the
   3rd ask differs from the 2nd and the 4th from the 3rd.

3. PLACEMENT. The variation is layered on by the ROUTES,
   after the answer is final — the same seam the answer
   cache's design already blesses ("personalisation is
   layered on by the routes, outside the result dict").
   The negative cache and the Live Bank therefore keep
   storing the BASE answer; the chain (fallback.py,
   guidance.py's and maths_meta's matchers, the solver)
   is untouched, and a first ask of anything is
   byte-identical to before this wave. Session state
   (last_result, the turn log, history) also keeps the
   base result, so doubt follow-ups and detail expansion
   always point at the canonical answer.

Anti-hijack: a DIFFERENT question is a different key —
a different guidance topic, a different knowledge entry,
or different question content — so it counts as a first
ask and is never varied. Not-found lines, the maths-only
guard, greetings, science/vague outcomes, step checks
and test/practice turns get no key at all: they are not
answers a student "re-asks" in this sense, and several
of them must stay exact one-liners by standing rule.
"""
import re
import unicodedata

# ---------------------------------------------------------------------------
# Question normalisation (solved-maths keys)
# ---------------------------------------------------------------------------

_DEV_DIGITS = {ord("०"): "0", ord("१"): "1", ord("२"): "2",
               ord("३"): "3", ord("४"): "4", ord("५"): "5",
               ord("६"): "6", ord("७"): "7", ord("८"): "8",
               ord("९"): "9"}

# Sentence glue that carries no question identity: the
# same ask typed with or without it is the same ask.
_FILLER_LATIN = {
    "kya", "hai", "hota", "hoti", "hote", "batao", "bata",
    "bataiye", "dijiye", "please", "solve", "karo", "kar",
    "do", "tell", "me", "mujhe", "zara", "what", "is",
    "the", "value", "of", "find", "calculate", "evaluate",
    "ka", "ki", "ke", "mein",
}
_FILLER_DEV = {
    "क्या", "है", "होता", "होती", "होते", "बताओ", "बता",
    "बताइए", "दीजिए", "करो", "कर", "दो", "मुझे", "का",
    "की", "के", "में",
}

# Maths operators survive normalisation as themselves —
# "5+3" and "5-3" are different questions and must never
# share a key. Everything else in the Unicode P/S
# categories becomes a space (bank.normalise_question's
# convention), and spacing around operators is then
# tightened so "5 + 3", "5+3" and "5 +3" agree.
_OPERATORS = set("+-*/=%×÷^")
_SPACES = re.compile(r"\s+")
_OP_SPACE = re.compile(r"\s*([+\-*/=%×÷^])\s*")


def normalise_question(text):
    """The repeat key form of a solved-maths question:
    case / punctuation / spacing insensitive, Devanagari
    digits folded to Latin, sentence glue dropped,
    operators kept and tightened. The multiplication
    spellings a student mixes freely — ×, * and a bare x
    between two numbers — fold to one form, and ÷ folds
    to /, so the same sum typed three ways is one ask."""
    text = unicodedata.normalize("NFC", str(text or ""))
    text = text.translate(_DEV_DIGITS)
    text = text.lower()
    text = text.replace("×", "x").replace("*", "x") \
        .replace("÷", "/")
    text = "".join(
        ch if ch in _OPERATORS
        else (" " if unicodedata.category(ch)[0] in ("P", "S")
              else ch)
        for ch in text)
    text = _OP_SPACE.sub(r"\1", text)
    tokens = [t for t in text.split()
              if t not in _FILLER_LATIN and t not in _FILLER_DEV]
    text = " ".join(tokens)
    text = re.sub(r"(\d)\s*x\s*(\d)", r"\1x\2", text)
    return _SPACES.sub(" ", text).strip()


# ---------------------------------------------------------------------------
# Repeat keys
# ---------------------------------------------------------------------------

# Mirror of followups._NOT_SOLVED_KINDS (the app's own
# "not a solved card" set) — kept local so this module
# imports nothing from the request path. The guidance /
# baat / knowledge kinds are claimed by their own key
# branches above this test, so they never reach it.
_NOT_SOLVED_KINDS = {
    "not_found", "concept", "history", "advice", "greeting",
    "nonmaths", "science", "vague", "gibberish", "guide",
    "similar", "step_check", "followup_test", "guidance",
    "baat", "guided", "chat_test", "practice_loop",
}
_NOT_SOLVED_OPS = {"error", "explain_step", "check_steps",
                   "not_found"}


def _is_solved(result):
    """followups.is_solved_result's predicate, mirrored:
    a real solved-maths card (native solver, verified
    bank, proof, AI serve) — never a plain one-liner or
    a fallback outcome."""
    if not str(result.get("answer") or "").strip():
        return False
    if result.get("plain_reply") or result.get("plain"):
        return False
    if result.get("fallback_kind") in _NOT_SOLVED_KINDS:
        return False
    if result.get("op") in _NOT_SOLVED_OPS:
        return False
    return True


def result_key(question, result):
    """The repeat-counting key for one finished answer,
    or None when this outcome is never counted / varied.

    Conversational layers key by TOPIC (the entry id), so
    reworded and cross-language re-asks of the same topic
    count together; solved maths keys by the normalised
    question text."""
    if not isinstance(result, dict):
        return None
    kind = result.get("fallback_kind")
    if kind == "guidance" and result.get("guidance_id"):
        return "g:" + str(result["guidance_id"])
    if kind == "baat" and result.get("baat_id"):
        return "b:" + str(result["baat_id"])
    if kind in ("history", "fact", "advice") \
            and result.get("meta_id"):
        return "m:%s:%s" % (kind, result["meta_id"])
    if _is_solved(result):
        key = normalise_question(question)
        if key:
            return "q:" + key
    return None


# ---------------------------------------------------------------------------
# Flavour of the varied lines
# ---------------------------------------------------------------------------

def flavour_for(question, result, lang_request=None,
                lang=None):
    """The en / roman / dev flavour the VARIATION lines
    must speak — the language of the card the student is
    looking at. The card's own recorded flavour wins
    (guidance results carry it); then an explicit
    in-message language request (Wave 107's mapping);
    then guidance's per-question derivation (script +
    Roman-Hindi hints — the same rule the meta layer
    flavours its cards by). The session language is only
    a tie-breaker for a question with no words of its own
    (a bare calculation from a Hindi-UI student)."""
    if isinstance(result, dict):
        own = result.get("guidance_flavour")
        if own in ("en", "roman", "dev"):
            return own
    if lang_request == "hi":
        return "dev"
    if lang_request == "hinglish":
        return "roman"
    if lang_request == "en":
        return "en"
    try:
        from guidance import _resolve_flavour
        flavour = _resolve_flavour(question, None)
    except Exception:
        q = str(question or "")
        flavour = "dev" if any("ऀ" <= ch <= "ॿ" for ch in q) \
            else "en"
    if flavour == "en" and lang == "hi" \
            and not re.search(r"[a-z]",
                              str(question or "").lower()):
        return "dev"
    return flavour


# ---------------------------------------------------------------------------
# The counting store (routes persist it in the session)
# ---------------------------------------------------------------------------

_STORE_CHATS = 3        # like api.py's ctx log
_STORE_KEYS_PER_CHAT = 64


def _bump(store, chat_key, key):
    """Increment (store[chat_key])[key] and return the new
    count. `store` is mutated in place; the caller
    persists it. Bounded on both levels — the oldest chat
    bucket / oldest key is evicted, cookie discipline."""
    bucket = store.pop(chat_key, None)
    if not isinstance(bucket, dict):
        bucket = {}
    bucket[key] = int(bucket.get(key) or 0) + 1
    while len(bucket) > _STORE_KEYS_PER_CHAT:
        bucket.pop(next(iter(bucket)))
    store[chat_key] = bucket
    while len(store) > _STORE_CHATS:
        store.pop(next(iter(store)))
    return bucket[key]


# ---------------------------------------------------------------------------
# Variation wording owned here: the warm openers and the
# solved-card offer lines. (Topic extra lines live with
# their topics: guidance.GUIDANCE_VARIATIONS /
# guidance.BAAT_AGAIN, maths_meta.META_VARIATIONS.)
# ---------------------------------------------------------------------------

_OPENERS = {
    "en": [
        "You asked this once before — happy to go over it "
        "again, a little differently this time.",
        "Same question again — no problem at all. Here is "
        "another way to look at it.",
        "Asking again is a good sign — it means you want "
        "it fully clear. One more angle on it:"],
    "roman": [
        "Ye sawal tum pehle bhi puch chuke ho — koi baat "
        "nahi, is baar thoda dusre tareeke se batata hu.",
        "Wahi sawal dobara — bilkul theek hai, samajhna "
        "hi asli baat hai. Ek aur nazariya dekho:",
        "Dobara puchna achhi baat hai — matlab tumhe ye "
        "pakka karna hai. Ek nayi baat aur jod deta hu:"],
    "dev": [
        "यह सवाल तुम पहले भी पूछ चुके हो — कोई बात नहीं, "
        "इस बार थोड़ा दूसरे तरीके से बताता हूँ।",
        "वही सवाल दोबारा — बिल्कुल ठीक है, समझना ही असली "
        "बात है। एक और नज़रिया देखो:",
        "दोबारा पूछना अच्छी बात है — मतलब तुम्हें यह "
        "पक्का करना है। एक नई बात और जोड़ देता हूँ:"],
}

_SOLVED_OPENERS = {
    "en": [
        "You have done this one with me before — same "
        "method, once more:",
        "This question again — good, revision is how it "
        "becomes permanent. The same method:"],
    "roman": [
        "Ye sawal hum pehle bhi kar chuke hai — wahi "
        "tareeka, ek baar phir dekh lo:",
        "Ye sawal dobara — bahut badhiya, revision se hi "
        "pakka hota hai. Wahi tareeka:"],
    "dev": [
        "यह सवाल हम पहले भी कर चुके हैं — वही तरीका, एक "
        "बार फिर देख लो:",
        "यह सवाल दोबारा — बहुत बढ़िया, revision से ही "
        "पक्का होता है। वही तरीका:"],
}

_OFFER_LINES = {
    "en": [
        "Want this in detail? Just say 'detail me batao' "
        "— or ask me for a similar practice question.",
        "If you want, say 'ek aur aisa sawal' and I will "
        "give you a similar one to try yourself."],
    "roman": [
        "Detail me chahiye toh 'detail me batao' likh do "
        "— ya bolo, ek aisa hi practice sawal deta hu.",
        "Chaho toh 'ek aur aisa sawal' likho — tumhare "
        "liye ek milta-julta sawal dunga, khud try "
        "karna."],
    "dev": [
        "Detail में चाहिए तो 'detail me batao' लिख दो — "
        "या बोलो, एक ऐसा ही practice सवाल देता हूँ।",
        "चाहो तो 'ek aur aisa sawal' लिखो — तुम्हारे लिए "
        "एक मिलता-जुलता सवाल दूँगा, ख़ुद try करना।"],
}


def _pick(pool, count):
    return pool[(count - 2) % len(pool)]


# ---------------------------------------------------------------------------
# The variation itself
# ---------------------------------------------------------------------------

def _card_variation(result, count, flavour, extra):
    """A guidance / knowledge card, varied: warm opener
    first, the base card's own lines untouched in the
    middle, the topic's fresh extra lines at the end."""
    steps = list(result.get("steps") or [])
    new_steps = [_pick(_OPENERS[flavour], count)] + steps \
        + list(extra or [])
    out = dict(result)
    out["steps"] = new_steps
    out["w178_repeat"] = count
    return out


def apply_variation(question, result, count, flavour):
    """The varied COPY of `result` for its `count`-th ask
    (count >= 2), or None when this result kind is never
    varied. The base result is never mutated; the maths
    of a solved card — every step and the answer value —
    is carried across byte for byte."""
    if count < 2 or not isinstance(result, dict):
        return None
    if flavour not in ("en", "roman", "dev"):
        flavour = "en"
    kind = result.get("fallback_kind")
    if kind == "baat":
        from guidance import baat_variation
        line = baat_variation(result.get("baat_id"),
                              flavour, count)
        if line is None or line == result.get("answer"):
            return None
        out = dict(result)
        out["answer"] = line
        out["w178_repeat"] = count
        return out
    if kind == "guidance":
        from guidance import guidance_variation
        extra = guidance_variation(result.get("guidance_id"),
                                   flavour, count)
        return _card_variation(result, count, flavour, extra)
    if kind in ("history", "fact", "advice"):
        from maths_meta import meta_variation
        extra = meta_variation(kind, result.get("meta_id"),
                               flavour, count)
        return _card_variation(result, count, flavour, extra)
    if _is_solved(result):
        steps = list(result.get("steps") or [])
        if not steps:
            return None
        out = dict(result)
        out["steps"] = [_pick(_SOLVED_OPENERS[flavour],
                              count)] + steps \
            + [_pick(_OFFER_LINES[flavour], count)]
        out["w178_repeat"] = count
        return out
    return None


def session_variation(session, chat_key, question, result,
                      flavour):
    """The route seam: count this finished ask in the
    session's Wave-178 store and return the varied copy
    to SHOW for a repeat ask — None on a first ask, an
    uncountable outcome, or any failure (the base result
    is then shown exactly as before this wave). The
    session keeps the BASE result everywhere else; only
    the displayed copy varies."""
    try:
        key = result_key(question, result)
        if key is None:
            return None
        store = session.get("w178_counts")
        if not isinstance(store, dict):
            store = {}
        count = _bump(store, str(chat_key or "default"), key)
        session["w178_counts"] = store
        if count < 2:
            return None
        return apply_variation(question, result, count,
                               flavour)
    except Exception:
        return None


__all__ = ["normalise_question", "result_key",
           "flavour_for", "apply_variation",
           "session_variation"]
