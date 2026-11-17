"""Wave 127 — conversation context ("baat-cheet wali samajh").

The big chat AIs understand references to earlier turns: after
an answer, a student writes "uska answer batao", "usi ka ek aur
example do", "dusra tarika batao", "ye wala phir se samjhao" —
and means a turn that already happened IN THIS CHAT. Until this
wave Ganitra treated every such message as a brand-new question
(the only exception was Wave 96's doubt layer, which re-explains
one STEP of the LAST answer).

This module is a resolver that runs in the chat path BEFORE the
normal solve (and before Wave 96 — see the precedence rules
below). It fires ONLY when the message is a REFERENCE to an
earlier turn, never when it carries a self-contained new
question:

* ``parse_context_ref(question)`` — deterministic detector
  (EN / Hindi / Hinglish phrase sets). It returns None for:
  - anything containing a digit or a maths operator symbol
    (a fresh computation's payload);
  - anything with a step word (step / चरण / स्टेप) — those are
    Wave 96 doubt territory and are NEVER claimed here;
  - concept asks ("kya hai", "what is", "matlab", "define");
  - a message naming a topic WITHOUT a possessive reference
    ("example ke saath HCF samjhao" is a FRESH concept ask —
    it solves normally; "HCF wale ka ek aur example do" names
    a previous TURN and is a reference);
  - any message with a leftover substantive word once the
    reference / intent / topic / filler vocabulary is removed
    (the remainder veto — a word problem that merely contains
    "uska" in its story keeps its payload words and is vetoed).

* ``build_context_response(...)`` — resolves the reference
  against the chat's solved-turn log (maintained by api.py in
  the session, keyed per chat) and builds the reply:
  - answer: re-show the referenced turn's final answer
    BYTE-IDENTICAL from the log — never recomputed;
  - example: a NEW worked example on the same question with
    one number nudged, solved by the solver alone (no
    fallback / AI); when no nudge solves with a different
    answer, returns None — the normal path's honest one-liner
    answers instead of an invented example;
  - method: the first alternate method from the Wave 12
    machinery (solver.methods.alternate_methods) for the
    referenced question; when the question honestly has one
    method, an explicit honest line + the original answer;
  - reexplain: the referenced answer's own steps re-served
    with a "simpler words" opener (full result recovered from
    the session's last result, or by re-solving the stored
    question ONLY when the solver reproduces the stored
    answer exactly); when recovery is impossible, just the
    stored answer is re-shown — nothing is paraphrased or
    invented;
  - ambiguity: a "pehle wala" (earlier-one) reference with no
    topic, pointing into 2+ earlier turns on different
    topics, gets ONE short clarifying question naming the
    two candidate topics — never a guess. A topic-named
    reference always settles by recency (latest matching
    turn wins).

Precedence vs Wave 96 (doubt): step references belong to
doubt. This layer defers by construction — a step word
anywhere in the message makes parse_context_ref return None,
and api.py calls this layer first only for the intents above
(answer / example / method / re-explain), which doubt's
detector does not claim as step explanations (its "pichle
wale ka answer batao" mis-claim — explaining the last step
when the student asked for the ANSWER — is exactly what this
ordering fixes).
"""

import re

from doubt import style_for, working_steps, eligible_result
from i18n import solve_failed
from solver.methods import alternate_methods
from solver.router import solve_question

__all__ = ["parse_context_ref", "build_context_response",
           "topic_label_for", "make_turn"]

# ------------------------------------------------------------------ #
# Vocabulary
# ------------------------------------------------------------------ #

_STEP_WORDS = {"step", "steps", "चरण", "स्टेप"}

# Pronouns / positionals pointing at the LATEST turn.
_REF_LAST = {
    "uska", "uske", "uski", "iska", "iske", "iski", "usi", "isi",
    "us", "is", "that", "this", "wahi", "vahi", "ye", "yeh",
    "उसका", "उसके", "उसकी", "इसका", "इसके", "इसकी", "उसी", "इसी",
    "वही", "यह", "ये",
}
# Positionals pointing BEFORE the latest turn.
_REF_PREV = {
    "pichla", "pichle", "pichhla", "pehle", "previous", "earlier",
    "पिछला", "पिछले", "पहले",
}
_PREV_PHRASES = ("pehle wala", "pehle wale", "usse pehle",
                 "पहले वाला", "पहले वाले")
# Possessive markers that turn a topic NAME into a reference to
# a previous TURN ("HCF wale ka ..." vs the fresh "HCF samjhao").
_POSSESSIVE = {"wala", "wale", "wali", "वाला", "वाले", "वाली"}
_ORDINALS = {"dusra", "doosra", "dusre", "doosre", "another",
             "दूसरा", "दूसरे"}

_SHOW_VERBS = {"batao", "bata", "do", "dikhao", "dedo", "de",
               "show", "give", "बताओ", "बता", "दो", "दिखाओ"}
_EXPLAIN_WORDS = {"samjhao", "samjhaiye", "samjhaye", "samjhado",
                  "samjha", "explain", "समझाओ", "समझाइए", "समझा"}

# A fresh concept ask is never a reference.
_CONCEPT_VETO = (
    "kya hai", "kya hota", "kya hote", "kya hoti", "matlab",
    "what is", "what are", "define", "definition",
    "क्या है", "क्या होता", "क्या होते",
)

# Canonical topic labels: (keywords, solver ops). Keywords are
# matched as whole words for Latin script, as substrings for
# Devanagari. The label is what the clarify line names and what
# topic-matching groups turns by.
TOPIC_ALIASES = (
    ("HCF", {"hcf", "gcd", "महत्तम"}, {"gcd"}),
    ("LCM", {"lcm", "लघुत्तम"}, {"lcm"}),
    ("Percentage", {"percentage", "percent", "pratishat",
                    "प्रतिशत"}, {"percentage"}),
    ("Perimeter", {"perimeter", "parimap", "परिमाप"},
     {"perimeter"}),
    ("Area", {"area", "kshetrafal", "क्षेत्रफल"}, {"area"}),
    ("Volume", {"volume", "aayatan", "आयतन"}, {"volume"}),
    ("Average", {"average", "mean", "ausat", "औसत"},
     {"average", "mean"}),
    ("Equation", {"equation", "samikaran", "समीकरण"},
     {"equation"}),
    ("Interest", {"interest", "byaaj", "ब्याज"},
     {"simple_interest", "compound_interest", "interest"}),
    ("Profit and Loss", {"profit", "loss", "laabh", "haani",
                         "लाभ", "हानि"}, {"profit_loss"}),
    ("Ratio", {"ratio", "anupaat", "अनुपात"}, {"ratio"}),
    ("Fraction", {"fraction", "fractions", "bhinn", "भिन्न"},
     {"fraction"}),
    ("Probability", {"probability", "प्रायिकता"},
     {"probability"}),
    ("Speed and Distance", {"speed", "distance", "chaal",
                            "चाल", "दूरी"}, {"speed"}),
    ("Triangle", {"triangle", "tribhuj", "त्रिभुज"}, set()),
    ("Circle", {"circle", "vritt", "वृत्त"}, set()),
    ("Angle", {"angle", "kon", "कोण"}, {"angle"}),
    ("Prime Numbers", {"prime", "अभाज्य"}, {"prime"}),
)
_TOPIC_KEYWORDS = set()
for _label, _kws, _ops in TOPIC_ALIASES:
    _TOPIC_KEYWORDS |= _kws

# Words that may appear in a bare reference and carry no new
# question payload. Anything outside this vocabulary (plus the
# reference / intent / topic words) vetoes the reference.
_FILLER = {
    "ka", "ki", "ke", "ko", "me", "mein", "hai", "na", "zara",
    "aur", "or", "ek", "bhi", "chahiye", "please", "plz", "bro",
    "bhai", "mujhe", "mera", "mere", "meri", "the", "a", "an",
    "of", "for", "to", "one", "more", "again", "phir", "se",
    "dobara", "bar", "baar", "karke", "krke", "aap", "tum",
    "samajh", "nahi", "nhi", "aaya", "aayi", "aasan", "asaan",
    "सरल", "समझ", "नहीं", "नही", "आया", "फिर", "से", "मुझे",
    "एक", "बार", "और", "का", "की", "को", "में", "है", "भी",
    "मेरा", "मेरे", "चाहिए", "दोबारा", "सरलता",
}

_INTENT_WORDS = {
    "answer", "jawab", "उत्तर", "जवाब",
    "example", "examples", "udahaaran", "udaharan", "उदाहरण",
    "tarika", "tarike", "तरीका", "तरीके", "method", "methods",
    "repeat",
} | _SHOW_VERBS | _EXPLAIN_WORDS

_ALLOWED = (_REF_LAST | _REF_PREV | _POSSESSIVE | _ORDINALS
            | _TOPIC_KEYWORDS | _INTENT_WORDS | _FILLER)


def _words(text):
    # Same tokeniser as doubt._words: split on whitespace and
    # strip punctuation characters only (a \w cleanup would
    # tear Devanagari vowel signs apart).
    import unicodedata
    out = []
    for tok in str(text).lower().split():
        word = "".join(ch for ch in tok
                       if not unicodedata.category(ch).startswith("P"))
        if word:
            out.append(word)
    return out


def _has_devanagari(text):
    return any("\u0900" <= ch <= "\u097f" for ch in str(text))


def topic_label_for(question, op=""):
    """The canonical topic label for a turn: first alias whose
    keyword appears in the question text or whose op set holds
    the turn's solver op. None when nothing matches."""
    text = " " + str(question or "").lower() + " "
    words = set(_words(text))
    for label, keywords, ops in TOPIC_ALIASES:
        if op and op in ops:
            return label
        for kw in keywords:
            if _has_devanagari(kw):
                if kw in text:
                    return label
            elif kw in words:
                return label
    return None


def _topic_in_message(words, text):
    """The canonical topic a MESSAGE names, or None."""
    wordset = set(words)
    for label, keywords, _ops in TOPIC_ALIASES:
        for kw in keywords:
            if _has_devanagari(kw):
                if kw in text:
                    return label
            elif kw in wordset:
                return label
    return None


def make_turn(question, result):
    """One solved-turn log entry (api.py stores these per
    chat): the question, the final answer (byte-identical to
    what the student saw), the solver type/op and the topic
    label. Sizes are capped — the log rides in the session
    cookie (see api.py)."""
    result = result or {}
    return {
        "q": str(question or "")[:160],
        "a": str(result.get("answer", "") or "")[:300],
        "t": str(result.get("type", "") or ""),
        "op": str(result.get("op", "") or ""),
        "topic": topic_label_for(question, result.get("op", "")),
    }


# ------------------------------------------------------------------ #
# Detection
# ------------------------------------------------------------------ #

def parse_context_ref(question):
    """Classify a chat message as a reference to an earlier
    turn. Returns None for a fresh question, else a dict:
    {"intent": "answer"|"example"|"method"|"reexplain",
     "topic": label|None, "positional": "last"|"prev"|None}."""
    raw = str(question or "")
    text = " " + raw.lower().strip() + " "
    words = _words(text)
    if not words:
        return None
    wordset = set(words)

    # A fresh computation carries digits or operator symbols.
    if any(ch.isdigit() for ch in raw):
        return None
    if any(ch in raw for ch in ("=", "%", "+", "×", "÷", "^")):
        return None

    # Step references are Wave 96 doubt territory — never ours.
    if wordset & _STEP_WORDS:
        return None

    # Fresh concept asks are never references.
    if any(p in text for p in _CONCEPT_VETO):
        return None

    # ---- intent ------------------------------------------------
    intent = None
    if wordset & {"tarika", "tarike", "तरीका", "तरीके",
                  "method", "methods"}:
        intent = "method"
    elif wordset & {"example", "examples", "उदाहरण",
                    "udahaaran", "udaharan"}:
        intent = "example"
    elif (wordset & {"answer", "jawab", "उत्तर", "जवाब"}):
        intent = "answer"
    elif (("phir se" in text or "dobara" in text
           or "फिर से" in text or "दोबारा" in text
           or "repeat" in wordset)
          and wordset & (_EXPLAIN_WORDS | _SHOW_VERBS)) \
            or (wordset & {"aasan", "asaan", "सरल"}
                and wordset & _EXPLAIN_WORDS):
        intent = "reexplain"
    if intent is None:
        return None

    # ---- reference shape ---------------------------------------
    topic = _topic_in_message(words, text)
    has_ref = bool(wordset & (_REF_LAST | _REF_PREV | _ORDINALS)) \
        or any(p in text for p in _PREV_PHRASES)
    has_possessive = bool(wordset & _POSSESSIVE)

    # A topic named WITHOUT any reference to a previous turn is
    # a fresh ask about that topic ("example ke saath HCF
    # samjhao") — unless a possessive makes it a turn reference
    # ("HCF wale ka ek aur example do").
    if topic is not None and not has_ref and not has_possessive:
        return None

    positional = None
    if wordset & _REF_PREV or any(p in text for p in _PREV_PHRASES):
        positional = "prev"
    elif wordset & _REF_LAST:
        positional = "last"

    # ---- remainder veto ----------------------------------------
    # Remove every reference / intent / topic / filler word;
    # any substantive leftover is a fresh question's payload
    # ("Ram ne uska paisa..." keeps paisa/katha words -> veto).
    if any(w not in _ALLOWED for w in words):
        return None

    return {"intent": intent, "topic": topic,
            "positional": positional}


# ------------------------------------------------------------------ #
# Resolution + responses
# ------------------------------------------------------------------ #

_T = {
    "clarify": {
        "en": "Which one — the {a} one or the {b} one?",
        "hinglish": "Kis wale ka — {a} wala ya {b} wala?",
        "hindi": "किस वाले का — {a} वाला या {b} वाला?"},
    "no_method": {
        "en": "This question has just one method for now — "
              "the one already shown above.",
        "hinglish": "Is sawal ka abhi ek hi tarika hai — wahi "
                    "jo upar dikhaya tha.",
        "hindi": "इस सवाल का अभी एक ही तरीका है — वही जो ऊपर "
                 "दिखाया था।"},
    "simpler": {
        "en": "Same answer, in simpler words:",
        "hinglish": "Wahi jawab, aur aasan shabdo me:",
        "hindi": "वही उत्तर, और सरल शब्दों में:"},
}


def _resolve_target(ref, turns):
    """Pick the referenced turn. Returns ("turn", turn) or
    ("clarify", (label_a, label_b)) or (None, None)."""
    if not turns:
        return None, None
    topic = ref.get("topic")
    if topic is not None:
        matches = [t for t in turns if t.get("topic") == topic]
        if not matches:
            return None, None
        if ref.get("positional") == "prev" and len(matches) >= 2:
            return "turn", matches[-2]
        return "turn", matches[-1]
    if ref.get("positional") == "prev":
        earlier = turns[:-1]
        if not earlier:
            return "turn", turns[-1]
        if len(earlier) >= 2:
            last_two = earlier[-2:]
            topics = [t.get("topic") for t in last_two]
            if topics[0] and topics[1] and topics[0] != topics[1]:
                # Two different topics could be meant — ask.
                return "clarify", (topics[1], topics[0])
        return "turn", earlier[-1]
    return "turn", turns[-1]


def _nudged_questions(question):
    """The referenced question with ONE number nudged, in a
    deterministic try-order (last number first; +1, +2, -1,
    +5, x2). Only plain integers/decimals in the text are
    nudged; the wording is otherwise byte-identical."""
    nums = [(m.start(), m.group(0))
            for m in re.finditer(r"\d+(?:\.\d+)?", question)]
    out = []
    for idx in range(len(nums) - 1, -1, -1):
        start, tok = nums[idx]
        try:
            value = float(tok)
        except ValueError:
            continue
        for new in (value + 1, value + 2, value - 1,
                    value + 5, value * 2):
            if new <= 0 or new == value:
                continue
            new_tok = str(int(new)) if float(new).is_integer() \
                else str(new)
            if new_tok == tok:
                continue
            out.append(question[:start] + new_tok
                       + question[start + len(tok):])
    return out


def _recover_full_result(turn, prev_question, prev_result):
    """The referenced turn's FULL result dict, or None.

    The session's last result is used when the referenced turn
    IS the last one. An older turn is recovered by re-solving
    its stored question with the solver alone — accepted ONLY
    when the solver reproduces the stored final answer
    exactly, so nothing different is ever served in the old
    answer's name."""
    if prev_result is not None \
            and str(prev_question or "") == turn.get("q") \
            and eligible_result(prev_result):
        return prev_result
    try:
        fresh = solve_question(turn.get("q", ""))
    except Exception:
        return None
    if solve_failed(turn.get("q", ""), fresh):
        return None
    if str(fresh.get("answer", "")).strip() \
            != str(turn.get("a", "")).strip():
        return None
    if not eligible_result(fresh):
        return None
    return fresh


def build_context_response(question, ref, turns,
                           prev_question=None, prev_result=None,
                           lang=None):
    """Build the reply for a reference message.

    `turns` is the chat's solved-turn log (oldest first, see
    make_turn). Returns (result_dict, advice_source) or None —
    None means "not honestly answerable as a reference" and
    the caller falls through to the normal solve path.
    advice_source is the result dict the caller should derive
    Teacher's Advice / teach lines from (or None)."""
    if ref is None or not turns:
        return None
    kind, payload = _resolve_target(ref, turns)
    if kind is None:
        return None
    style = style_for(question, lang)

    if kind == "clarify":
        label_a, label_b = payload
        line = _T["clarify"][style].format(a=label_a, b=label_b)
        result = {"type": "context", "op": "clarify",
                  "steps": [], "answer": line, "context": True}
        return result, None

    turn = payload
    intent = ref.get("intent")

    if intent == "answer":
        # Byte-identical re-show of the stored final answer.
        result = {"type": "context", "op": "show_answer",
                  "steps": [], "answer": turn.get("a", ""),
                  "context": True,
                  "context_question": turn.get("q", "")}
        return result, {"type": turn.get("t", ""),
                        "op": turn.get("op", "")}

    if intent == "example":
        for candidate in _nudged_questions(turn.get("q", "")):
            try:
                fresh = solve_question(candidate)
            except Exception:
                continue
            if solve_failed(candidate, fresh):
                continue
            if str(fresh.get("answer", "")).strip() \
                    == str(turn.get("a", "")).strip():
                continue  # same answer — not a new example
            fresh = dict(fresh)
            fresh["context"] = True
            fresh["example_of"] = turn.get("q", "")
            fresh["example_question"] = candidate
            return fresh, fresh
        return None

    if intent == "method":
        full = _recover_full_result(turn, prev_question,
                                    prev_result)
        if full is None:
            return None
        methods = alternate_methods(turn.get("q", ""), full)
        if methods:
            first = methods[0]
            result = {"type": "context", "op": "alt_method",
                      "steps": list(first.get("steps") or []),
                      "answer": first.get("answer", ""),
                      "context": True,
                      "method_label": first.get("label", "")}
            return result, full
        result = {"type": "context", "op": "no_alt_method",
                  "steps": [_T["no_method"][style]],
                  "answer": turn.get("a", ""), "context": True}
        return result, full

    if intent == "reexplain":
        full = _recover_full_result(turn, prev_question,
                                    prev_result)
        if full is None:
            # Cannot recover the working — re-show the stored
            # answer alone rather than invent an explanation.
            result = {"type": "context", "op": "show_answer",
                      "steps": [], "answer": turn.get("a", ""),
                      "context": True,
                      "context_question": turn.get("q", "")}
            return result, {"type": turn.get("t", ""),
                            "op": turn.get("op", "")}
        steps = [_T["simpler"][style]] + working_steps(full)
        result = {"type": "context", "op": "reexplain",
                  "steps": steps, "answer": turn.get("a", ""),
                  "context": True}
        return result, full

    return None
