"""Wave 124 — chat-based test / exam (Suraj, 17 Nov 2026).

Suraj's order: *"User chat mai bhi exam yaa test bhi maang
sakta hai"* — a student must be able to ask for a test INSIDE
the chat and take it right there, the way ChatGPT-style
quizzes run inside a conversation: one question at a time,
instant checking, score at the end. The separate test pages
(Chapter Test Mode, full-paper exam mode) keep their own
timers and reports; this wave is the chat-native version.

Design (all deterministic — no AI calls anywhere):

* ``parse_test_request(text)`` decides whether a chat message
  ASKS for a test, and parses topic / class / count out of it.
  A test noun (test / quiz / exam / टेस्ट / क्विज़ / परीक्षा)
  must sit near a request verb (do / lo / karao / puchho /
  दो / लो / कराओ / पूछो …), or the message must be a bare
  short ask ("mera test", "class 10 test"), or it must use
  the "sawaal puchho mujhse" shape. Guards run FIRST:
  concept asks ("test kya hota hai"), exam-ADVICE asks
  ("exam ki taiyari kaise karu"), and maths phrases that
  merely contain "test" ("test tube", "divisibility test",
  "ratio test", "test series") never trigger.

* Question sources — VERIFIED ONLY (the standing rule: a
  question the solver cannot check is never served):
  - classes 6–10: ``practice_gen`` items (the Wave-34/43
    generator behind Practice Mode and Chapter Test Mode),
    projected and checked with ``test_mode``'s own exact
    Fraction-based checker;
  - classes 0–5 and 11–12, and any named topic outside the
    five practice topics: concept-topic starters
    (``topics_data`` / ``topics_banda``), each one VERIFIED
    AT SERVE TIME — the solver must solve the starter and
    its answer must match the stored answer under
    ``full_paper.answers_match`` — or the starter is not
    served. Answers are checked with the same comparator.
  If a named topic cannot produce enough checkable
  questions, the test falls back to the class's mixed
  topics and SAYS SO in one line — an unchecked question
  is never invented.

* State: server-side, per chat. For a signed-in student the
  state lives in a ``chat_test_state`` table in the accounts
  SQLite file (the chats.py pattern), keyed by
  (user_id, chat_id) — a test can never leak into another
  chat of the same student, and a page reload mid-test
  resumes exactly where the student was (the thread itself
  is persisted by the Wave-11 chat store; the state row is
  what the server needs to check the next answer). With no
  chat id (unsaved mode) the state rides in the Flask
  session under a per-chat key. NOTHING beyond the test
  state is stored: questions served, answers given, score.

* Flow (plain chat style — Suraj's standing rule: simple /
  plain; no step labels, no follow-up chips, no answer box
  on test turns):
  1. Start line (topic, class, kitne sawal) + Sawal 1.
  2. The student's next message is the answer attempt:
     checked exactly, replied "Sahi ✅" or "Galat — sahi
     jawab: X" in ONE line, plus progress
     "Sawal i/n • Score s" and the next question.
  3. Commands mid-test, checked in this order:
     a fresh test request (restart) → stop → solve → seen →
     skip → anything else is the answer attempt.
     - "skip" → not attempted, correct answer shown.
     - "stop / band karo / ruk jao" → ends now, partial
       result over the questions reached.
     - "answer batao / jawab batao / उत्तर बताओ" → ONLY
       the final answer is shown; the question is marked
       "answer dekha" (0 marks, counted separately from
       skip in the result), then the next question.
     - "solve karke do / हल करके दो / pura solution do" →
       the FULL solution is shown (the normal solver's own
       card for that question, via the caller's solve
       function; if the solver cannot re-solve it, the
       generator's / topic's own worked steps — never
       invented), the question is marked solved-by-Ganitra
       (0 marks, counted under "Answer dekha"), then the
       next question / result rides as a plain trailing
       bubble (``w124_next`` in the payload).
  4. End card (plain lines): Score x/y, %, time taken, the
     Sahi / Galat / Answer dekha / Skip counts, the weak
     topics (from WRONG answers only), one-line advice —
     all in the student's language flavour (en / roman /
     dev, via followups.flavour_for, incl. the Wave-107
     explicit-language override captured at test start).
     Wrong answers are also written into the existing
     Mistake Notebook session mechanism (same entry shape
     as app._record_mistakes, source "chat test").

* NO hard timer in chat v1 — deliberate: the page modes own
  timers. Elapsed time is recorded and shown in the result.

Wave 122/123 interplay: test turns are plain results
(``plain`` + ``plain_reply`` + fallback_kind "chat_test"),
so the chat JS gives them NO answer box, NO step labels and
NO streaming reveal, and ``w122_payload`` gives them no
chips; the api hook additionally forces ``w122.chips`` to
[] on every test turn. The one exception is the
solve-command turn, which is BY DESIGN the normal solved
card for that question (Suraj's spec: "pura solution milega
— normal solved card"); it still carries no chips, and its
worked-steps fallback form (op "chat_test_solve") is
excluded from step labels in the chat JS.
"""

import json
import random
import re
import sqlite3
import time
import unicodedata

import accounts
import practice_gen
import test_mode
from followups import flavour_for
from full_paper import answers_match
from i18n import solve_failed
from solver.router import solve_question

__all__ = ["parse_test_request", "is_stop_command",
           "is_skip_command", "is_seen_command",
           "is_solve_command", "handle_message",
           "load_state", "clear_state"]

DEFAULT_COUNT = 5
MAX_COUNT = 20

# ------------------------------------------------------------------ #
# Tokenising (Devanagari-safe, word-boundary safe)
# ------------------------------------------------------------------ #

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _tokens(text):
    """Lowercased word tokens with edge punctuation stripped
    by Unicode category, so "test," / "टेस्ट।" / "(test)"
    all reduce to the bare word and a word like "latest"
    never contains a phantom "test"."""
    out = []
    for raw in str(text or "").lower().translate(
            _DEV_DIGITS).split():
        tok = raw
        while tok and unicodedata.category(tok[0]).startswith(
                ("P", "S")):
            tok = tok[1:]
        while tok and unicodedata.category(tok[-1]).startswith(
                ("P", "S")):
            tok = tok[:-1]
        if tok:
            out.append(tok)
    return out


def _has_phrase(tokens, phrase):
    """True when the token sequence `phrase` (a list) appears
    contiguously in `tokens`."""
    n = len(phrase)
    if n == 0 or len(tokens) < n:
        return False
    return any(tokens[i:i + n] == phrase
               for i in range(len(tokens) - n + 1))


# ------------------------------------------------------------------ #
# Intent detection
# ------------------------------------------------------------------ #

_NOUNS = {"test", "quiz", "exam", "टेस्ट", "क्विज़", "क्विज",
          "परीक्षा", "एग्जाम", "टेस्ट्स"}
_VERBS = {"do", "lo", "karao", "karwao", "kar", "karo", "de",
          "chalu", "start", "shuru", "puchho", "pucho", "puchh",
          "bhejo", "दो", "लो", "कराओ", "करो", "दे", "शुरू",
          "चालू", "पूछो", "पूछ", "ले", "le"}
# "chahiye" is a request verb ONLY right next to the test noun
# ("test chahiye") — far away it belongs to ordinary asks like
# Wave 111's "Exam me maths ke question kaise solve karne
# chahiye?", which must never start a test.
_WANT = {"chahiye", "चाहिए"}

_GUARD_PHRASES = (
    ["test", "tube"], ["test", "series"], ["test", "match"],
    ["divisibility", "test"], ["convergence", "test"],
    ["ratio", "test"], ["root", "test"], ["t", "test"],
    ["टेस्ट", "ट्यूब"],
)
_ADVICE_WORDS = {"taiyari", "तैयारी", "preparation", "prepare",
                 "strategy", "tips", "syllabus", "timetable",
                 "schedule", "padhai", "पढ़ाई", "kaise", "कैसे"}

_PRACTICE_SYNONYMS = {
    "algebra": "algebra", "बीजगणित": "algebra",
    "algebraic": "algebra",
    "arithmetic": "arithmetic", "अंकगणित": "arithmetic",
    "geometry": "geometry", "ज्यामिति": "geometry",
    "रेखागणित": "geometry",
    "mensuration": "mensuration", "क्षेत्रमिति": "mensuration",
    "probability": "probability", "प्रायिकता": "probability",
    "संभाव्यता": "probability",
}

_STOPWORDS = {
    "test", "quiz", "exam", "tests", "mock", "practice",
    "ka", "ki", "ke", "do", "lo", "de", "mera", "meri", "mere",
    "mujhe", "mujhse", "mujh", "hai", "hain", "ho", "chahiye",
    "sawaal", "sawal", "question", "questions", "class",
    "kaksha", "please", "kripya", "ek", "aur", "for", "me",
    "mein", "mai", "start", "karao", "karwao", "karo", "kar",
    "shuru", "chalu", "puchho", "pucho", "ask", "bhejo", "le",
    "chapter", "topic", "of", "the", "a", "an", "on", "in",
    "टेस्ट", "क्विज़", "क्विज", "परीक्षा", "एग्जाम", "मॉक",
    "प्रैक्टिस", "का", "की", "के", "दो", "लो", "दे", "मेरा",
    "मेरी", "मेरे", "मुझे", "मुझसे", "है", "हैं", "हो",
    "चाहिए", "सवाल", "प्रश्न", "कक्षा", "कृपया", "एक", "और",
    "में", "शुरू", "चालू", "कराओ", "करो", "पूछो", "अध्याय",
    "विषय", "से", "पर",
}


def _parse_count(tokens):
    joined = " ".join(tokens)
    m = re.search(r"(\d{1,2})\s*(?:sawaal|sawal|questions?|प्रश्न"
                  r"|सवाल)", joined)
    if not m:
        m = re.search(r"(\d{1,2})\s*(?:ka|ke|ki)\s*(?:test|quiz"
                      r"|exam|टेस्ट|क्विज़|परीक्षा)", joined)
    if not m:
        return DEFAULT_COUNT
    try:
        n = int(m.group(1))
    except ValueError:
        return DEFAULT_COUNT
    return max(1, min(MAX_COUNT, n))


def _class_number_index(tokens):
    """The index of the digit token that names the class (the
    one touching "class" / "कक्षा"), or None."""
    for i, tok in enumerate(tokens):
        if tok in ("class", "कक्षा"):
            for j in (i + 1, i - 1):
                if 0 <= j < len(tokens) and tokens[j].isdigit():
                    n = int(tokens[j])
                    if 0 <= n <= 12:
                        return j
        if tok.isdigit() and i + 1 < len(tokens) \
                and tokens[i + 1] in ("class", "कक्षा"):
            n = int(tok)
            if 0 <= n <= 12:
                return i
    return None


def _parse_class(tokens):
    idx = _class_number_index(tokens)
    return int(tokens[idx]) if idx is not None else None


def parse_test_request(text):
    """A parsed test request dict, or None when the message is
    not asking for a chat test.

    Returns {"count", "class_num" (or None), "topic_key"
    (a practice_gen topic or None), "topic_query" (free text
    for a concept-topic search, or None), "topic_label"}.
    """
    tokens = _tokens(text)
    if not tokens:
        return None
    # --- Guards first: these never start a test. ---
    for phrase in _GUARD_PHRASES:
        if _has_phrase(tokens, phrase):
            return None
    # Concept veto: "test kya hai / what is a test / test ka
    # matlab" asks ABOUT a test, not for one.
    if ("kya" in tokens and ("hai" in tokens or "hota" in tokens
                              or "hoti" in tokens)) \
            or _has_phrase(tokens, ["what", "is"]) \
            or _has_phrase(tokens, ["what", "are"]) \
            or "matlab" in tokens or "मतलब" in tokens \
            or "define" in tokens or "meaning" in tokens:
        return None
    noun_idx = [i for i, t in enumerate(tokens) if t in _NOUNS]
    strong = False
    if noun_idx:
        for i in noun_idx:
            for j, t in enumerate(tokens):
                if t in _VERBS and abs(i - j) <= 3:
                    strong = True
                if t in _WANT and abs(i - j) <= 1:
                    strong = True
    if _has_phrase(tokens, ["mock", "test"]) \
            or _has_phrase(tokens, ["मॉक", "टेस्ट"]) \
            or _has_phrase(tokens, ["practice", "test"]) \
            or _has_phrase(tokens, ["प्रैक्टिस", "टेस्ट"]):
        strong = True
    # An explicit question-count phrase next to a test noun
    # ("10 sawal ka test class 10") is a test ask even when no
    # request verb survives in the sentence.
    if noun_idx and re.search(
            r"\d{1,2}\s*(?:sawaal|sawal|questions?|प्रश्न|सवाल)",
            " ".join(tokens)):
        strong = True
    weak = False
    if not strong:
        # A bare short ask: "test", "mera test", "class 10 test".
        # A maths phrase that merely CONTAINS the noun ("Find
        # the test value") is vetoed by its content words.
        _weak_veto = {"find", "value", "solve", "calculate",
                      "prove", "simplify", "what", "kya", "hai",
                      "hota", "matlab", "kaise", "निकालो",
                      "nikalo"}
        if noun_idx and len(tokens) <= 4 \
                and not any(t in tokens for t in _weak_veto):
            weak = True
        # "sawaal puchho mujhse" — ask me questions.
        if ("sawaal" in tokens or "sawal" in tokens
                or "सवाल" in tokens or "प्रश्न" in tokens) \
                and any(t in tokens for t in
                        ("puchho", "pucho", "पूछो", "पूछ", "ask")):
            weak = True
        # Exam-advice asks ("exam ki taiyari kaise karu") are
        # advice, never a test start — they only ever reach
        # this weak branch.
        if any(t in tokens for t in _ADVICE_WORDS):
            weak = False
    if not strong and not weak:
        return None
    class_num = _parse_class(tokens)
    # The class number is not a question count: "class 10 ka
    # test" is a class-10 test of the DEFAULT count, so the
    # class digit is removed before the count patterns run.
    count_tokens = list(tokens)
    cls_idx = _class_number_index(tokens)
    if cls_idx is not None:
        count_tokens.pop(cls_idx)
    count = _parse_count(count_tokens)
    topic_key = None
    for tok in tokens:
        if tok in _PRACTICE_SYNONYMS:
            topic_key = _PRACTICE_SYNONYMS[tok]
            break
    topic_query = None
    if topic_key is None:
        rest = [t for t in tokens
                if t not in _STOPWORDS and not t.isdigit()]
        if rest:
            topic_query = " ".join(rest)
    if topic_key is not None:
        topic_label = test_mode.TOPIC_LABELS[topic_key]
    elif topic_query:
        topic_label = topic_query.title() if topic_query.isascii() \
            else topic_query
    else:
        topic_label = None
    return {"count": count, "class_num": class_num,
            "topic_key": topic_key, "topic_query": topic_query,
            "topic_label": topic_label}


# ------------------------------------------------------------------ #
# In-test commands (checked in the order: restart, stop,
# solve, seen, skip — anything else is the answer attempt)
# ------------------------------------------------------------------ #

_STOP_PHRASES = (
    ["stop"], ["stop", "test"], ["band", "karo"], ["band", "kar"],
    ["band", "kar", "do"], ["ruk", "jao"], ["ruk"], ["रुको"],
    ["रुक", "जाओ"], ["बंद", "करो"], ["बंद", "कर", "दो"],
    ["end", "test"], ["quit"], ["khatm", "karo"], ["खत्म", "करो"],
    ["test", "band"], ["test", "stop"], ["cancel"], ["bas"],
    ["बस"],
)
_SKIP_PHRASES = (
    ["skip"], ["skip", "karo"], ["skip", "kar", "do"],
    ["chhod", "do"], ["छोड़", "दो"], ["next"], ["next", "question"],
    ["agla", "sawal"], ["अगला", "सवाल"], ["aage", "badho"],
    ["आगे", "बढ़ो"], ["pass"],
)
_SEEN_PHRASES = (
    ["answer", "batao"], ["jawab", "batao"], ["जवाब", "बताओ"],
    ["उत्तर", "बताओ"], ["answer", "kya", "hai"],
    ["jawab", "kya", "hai"], ["उत्तर", "क्या", "है"],
    ["answer", "bata", "do"], ["jawab", "bata", "do"],
    ["answer", "dikhao"], ["jawab", "dikhao"], ["जवाब", "दिखाओ"],
    ["उत्तर", "दिखाओ"], ["answer", "de", "do"],
    ["jawab", "de", "do"], ["sahi", "jawab", "batao"],
    ["सही", "उत्तर", "बताओ"], ["answer", "bata"],
)
_SOLVE_PHRASES = (
    ["solve", "karke", "do"], ["solve", "kar", "do"],
    ["solve", "karke", "batao"], ["solve", "kar", "ke", "do"],
    ["solve", "karo"], ["isko", "solve", "karo"],
    ["solve", "karke", "dikhao"], ["pura", "solution", "do"],
    ["pura", "solution", "batao"], ["full", "solution", "do"],
    ["full", "solution", "batao"], ["solution", "do"],
    ["solution", "batao"], ["हल", "करके", "दो"],
    ["हल", "करके", "बताओ"], ["हल", "कर", "दो"], ["हल", "दो"],
    ["हल", "बताओ"],
)


def _matches(text, phrases, exact_too=()):
    tokens = _tokens(text)
    if not tokens:
        return False
    if tokens in [list(p) for p in exact_too]:
        return True
    return any(_has_phrase(tokens, list(p)) for p in phrases)


def is_stop_command(text):
    return _matches(text, _STOP_PHRASES)


def is_skip_command(text):
    return _matches(text, _SKIP_PHRASES)


def is_seen_command(text):
    return _matches(text, _SEEN_PHRASES)


def is_solve_command(text):
    if _tokens(text) == ["solve"]:
        return True
    return _matches(text, _SOLVE_PHRASES)


# ------------------------------------------------------------------ #
# Language lines (flavour: en / roman / dev)
# ------------------------------------------------------------------ #

_LINES = {
    "en": {
        "start": "Test started — {topic} • Class {cls} • "
                 "{n} questions",
        "mixed": "Mixed topics",
        "note_topic": "Note: not enough checkable questions "
                      "for {topic} — mixed Class {cls} "
                      "questions given instead.",
        "note_short": "Note: only {n} checkable questions "
                      "could be prepared.",
        "q": "Question {i}/{n}: {q}",
        "hint": "Just write the answer.",
        "correct": "Correct ✅",
        "wrong": "Wrong — correct answer: {a}",
        "progress": "Question {i}/{n} • Score {s}",
        "skip": "Skip — correct answer: {a}",
        "seen": "Answer: {a} — answer dekha, 0 marks for "
                "this question.",
        "end": "Test over 🏁",
        "stopped": "Test stopped midway.",
        "score": "Score: {s}/{y} ({p}%)",
        "counts": "Correct {c} • Wrong {w} • Answer dekha "
                  "{v} • Skip {k}",
        "solved_note": "Of these, {v} question(s) were solved "
                       "and shown by Ganitra.",
        "time": "Time taken: {t}",
        "left": "{r} questions were left.",
        "weak": "Weak topics: {topics}",
        "no_weak": "No topic went wrong 🎉",
        "advice_high": "Great work — keep practising like "
                       "this daily.",
        "advice_mid": "Good effort — revise the weak topics "
                      "once and try again.",
        "advice_low": "Don't give up — first learn the weak "
                      "topics, then take the test again.",
        "sorry": "Sorry — I could not prepare checkable "
                 "questions right now. Ask me any maths "
                 "question instead.",
        "min": "min", "sec": "sec",
    },
    "roman": {
        "start": "Test shuru — {topic} • Class {cls} • "
                 "{n} sawal",
        "mixed": "Mixed topics",
        "note_topic": "Note: {topic} ke checkable sawal kam "
                      "mile — Class {cls} ke mixed sawal "
                      "diye hain.",
        "note_short": "Note: sirf {n} checkable sawal "
                      "taiyaar ho paaye.",
        "q": "Sawal {i}/{n}: {q}",
        "hint": "Sirf jawab likho.",
        "correct": "Sahi ✅",
        "wrong": "Galat — sahi jawab: {a}",
        "progress": "Sawal {i}/{n} • Score {s}",
        "skip": "Skip — sahi jawab: {a}",
        "seen": "Jawab: {a} — answer dekha, is sawal ke "
                "0 number.",
        "end": "Test khatm 🏁",
        "stopped": "Test beech me roka gaya.",
        "score": "Score: {s}/{y} ({p}%)",
        "counts": "Sahi {c} • Galat {w} • Answer dekha {v} "
                  "• Skip {k}",
        "solved_note": "Inme se {v} sawal Ganitra ne solve "
                       "karke dikhaye the.",
        "time": "Time laga: {t}",
        "left": "Baaki {r} sawal bache the.",
        "weak": "Kamzor topic: {topics}",
        "no_weak": "Koi topic galat nahi hua 🎉",
        "advice_high": "Bahut badhiya — aise hi roz practice "
                       "karte raho.",
        "advice_mid": "Achha prayas — kamzor topic ek baar "
                      "revise karke phir test do.",
        "advice_low": "Himmat mat haaro — pehle kamzor topic "
                      "seekho, phir dobara test do.",
        "sorry": "Sorry — abhi checkable sawal taiyaar nahi "
                 "ho paaye. Koi maths ka sawal puchho.",
        "min": "min", "sec": "sec",
    },
    "dev": {
        "start": "टेस्ट शुरू — {topic} • कक्षा {cls} • "
                 "{n} सवाल",
        "mixed": "मिश्रित विषय",
        "note_topic": "नोट: {topic} के जाँच योग्य सवाल कम "
                      "मिले — कक्षा {cls} के मिश्रित सवाल "
                      "दिए गए हैं।",
        "note_short": "नोट: केवल {n} जाँच योग्य सवाल तैयार "
                      "हो पाए।",
        "q": "सवाल {i}/{n}: {q}",
        "hint": "सिर्फ जवाब लिखो।",
        "correct": "सही ✅",
        "wrong": "गलत — सही जवाब: {a}",
        "progress": "सवाल {i}/{n} • स्कोर {s}",
        "skip": "छोड़ा गया — सही जवाब: {a}",
        "seen": "जवाब: {a} — उत्तर देखा गया, इस सवाल के "
                "0 अंक।",
        "end": "टेस्ट खत्म 🏁",
        "stopped": "टेस्ट बीच में रोका गया।",
        "score": "स्कोर: {s}/{y} ({p}%)",
        "counts": "सही {c} • गलत {w} • उत्तर देखा {v} • "
                  "छोड़े {k}",
        "solved_note": "इनमें से {v} सवाल गणित्र ने हल करके "
                       "दिखाए थे।",
        "time": "समय लगा: {t}",
        "left": "बाकी {r} सवाल बचे थे।",
        "weak": "कमज़ोर विषय: {topics}",
        "no_weak": "कोई विषय गलत नहीं हुआ 🎉",
        "advice_high": "बहुत बढ़िया — ऐसे ही रोज़ अभ्यास "
                       "करते रहो।",
        "advice_mid": "अच्छा प्रयास — कमज़ोर विषय एक बार "
                      "दोहराकर फिर टेस्ट दो।",
        "advice_low": "हिम्मत मत हारो — पहले कमज़ोर विषय "
                      "सीखो, फिर दोबारा टेस्ट दो।",
        "sorry": "माफ़ करो — अभी जाँच योग्य सवाल तैयार नहीं "
                 "हो पाए। कोई गणित का सवाल पूछो।",
        "min": "मिनट", "sec": "सेकंड",
    },
}


def _fmt_time(seconds, flavour):
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    ln = _LINES[flavour]
    if m:
        return f"{m} {ln['min']} {s} {ln['sec']}"
    return f"{s} {ln['sec']}"


# ------------------------------------------------------------------ #
# Question generation — verified sources only
# ------------------------------------------------------------------ #

def _practice_items(class_num, topic_key, count, rng):
    """practice_gen items for classes 6–10, projected into
    test_mode's JSON-safe shape (checked by test_mode's own
    checker). Mixed = the five topics round-robin."""
    topics = [topic_key] if topic_key else list(practice_gen.TOPICS)
    per = {}
    for topic in topics:
        need = count if topic_key else \
            (count // len(topics)) + 2
        got, seen = [], set()
        for item in practice_gen.generate_set(
                class_num, topic, count=need * 2,
                seed=rng.randrange(1 << 30)):
            if item["question"] in seen:
                continue
            seen.add(item["question"])
            got.append(item)
            if len(got) >= need:
                break
        per[topic] = got
    items = []
    if topic_key:
        pool = per[topic_key]
    else:
        pool = []
        depth = max(len(v) for v in per.values())
        for i in range(depth):
            for topic in topics:
                if i < len(per[topic]):
                    pool.append(per[topic][i])
    for item in pool[:count]:
        items.append({
            "source": "practice",
            "question": item["question"],
            "answer": item["answer"],
            "topic_label": test_mode.TOPIC_LABELS[item["topic"]],
            "check": test_mode._project(item),
            "work_steps": None,
        })
    return items


def _topic_entries(class_num):
    if 6 <= class_num <= 12:
        import topics_data
        return list(topics_data.TOPICS_BY_CLASS.get(class_num,
                                                    []))
    import topics_banda
    return list(topics_banda.TOPICS_BANDA.get(class_num, []))


def _common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _tok_match(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) >= 4 and (a.startswith(b)
                                     or b.startswith(a)):
        return True
    return _common_prefix(a, b) >= 6


def _score_entry(entry, query_tokens):
    hay = _tokens(entry.get("name", "")) + _tokens(
        str(entry.get("chapter", "")).replace("-", " "))
    score = 0
    for qt in query_tokens:
        if any(_tok_match(qt, ht) for ht in hay):
            score += 1
    return score


def _verify_starter(entry):
    """Serve-time verification: the solver must solve the
    starter AND agree with the stored answer. Anything else
    is never served."""
    starter = str(entry.get("starter") or "").strip()
    stored = str(entry.get("answer") or "").strip()
    if not starter or not stored:
        return False
    try:
        result = solve_question(starter)
    except Exception:
        return False
    if solve_failed(starter, result):
        return False
    return answers_match(stored, result.get("answer", ""))


def _starter_items(class_num, topic_query, count, rng):
    """Concept-topic starters for the class, verified one by
    one at serve time. Returns (items, fell_back) — fell_back
    is True when a named topic could not fill the test and
    mixed class topics supplemented it."""
    entries = _topic_entries(class_num)
    if not entries:
        return [], False
    query_tokens = _tokens(topic_query) if topic_query else []
    scored = []
    for idx, entry in enumerate(entries):
        score = _score_entry(entry, query_tokens) \
            if query_tokens else 0
        scored.append((score, idx, entry))
    matched = [s for s in scored if s[0] > 0]
    matched.sort(key=lambda s: (-s[0], s[1]))
    rest = [s for s in scored if s[0] == 0]
    rng.shuffle(rest)
    ordered = matched + rest
    items, seen = [], set()
    fell_back = False
    cap = max(60, count * 8)
    checked = 0
    for score, _idx, entry in ordered:
        if len(items) >= count or checked >= cap:
            break
        starter = str(entry.get("starter") or "").strip()
        if not starter or starter in seen:
            continue
        seen.add(starter)
        checked += 1
        if not _verify_starter(entry):
            continue
        if query_tokens and score == 0:
            fell_back = True
        items.append({
            "source": "starter",
            "question": starter,
            "answer": str(entry.get("answer")).strip(),
            "topic_label": entry.get("name", ""),
            "check": {"answer": str(entry.get("answer")).strip()},
            "work_steps": [str(s) for s in
                           (entry.get("steps") or [])],
        })
    return items, fell_back


def _generate(req, class_num, rng):
    """(items, note_kind) — note_kind is None, "topic" (the
    named topic fell back to mixed) or "short" (fewer
    checkable questions than asked)."""
    count = req["count"]
    topic_key = req["topic_key"]
    topic_query = req["topic_query"]
    fell_back = False
    if topic_key and class_num in practice_gen.CLASSES:
        items = _practice_items(class_num, topic_key, count, rng)
    elif topic_query:
        items, fell_back = _starter_items(class_num,
                                          topic_query, count,
                                          rng)
        if len(items) < count and class_num in \
                practice_gen.CLASSES:
            extra = _practice_items(class_num, None,
                                    count - len(items), rng)
            have = {i["question"] for i in items}
            items += [i for i in extra
                      if i["question"] not in have]
            fell_back = True
    elif class_num in practice_gen.CLASSES:
        items = _practice_items(class_num, None, count, rng)
    else:
        items, _ = _starter_items(class_num, None, count, rng)
    note = None
    if fell_back:
        note = "topic"
    elif items and len(items) < count:
        note = "short"
    return items[:count], note


def _check_answer(item, given):
    if item["source"] == "practice":
        return test_mode.check_test_answer(item["check"], given)
    return answers_match(item["check"]["answer"], given)


# ------------------------------------------------------------------ #
# State storage — per chat, server-side
# ------------------------------------------------------------------ #

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chat_test_state (
    user_id     INTEGER NOT NULL,
    chat_id     TEXT NOT NULL,
    state_json  TEXT NOT NULL DEFAULT '{}',
    updated_at  INTEGER NOT NULL,
    PRIMARY KEY (user_id, chat_id)
)
"""


def _connect():
    conn = sqlite3.connect(accounts.db_path())
    conn.execute(_SCHEMA)
    return conn


def _session_key(chat_id):
    return f"chat_test::{chat_id or 'local'}"


def load_state(session, user_id, chat_id):
    if user_id and chat_id:
        try:
            conn = _connect()
            try:
                row = conn.execute(
                    "SELECT state_json FROM chat_test_state"
                    " WHERE user_id = ? AND chat_id = ?",
                    (user_id, str(chat_id))).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            row = None
        if row:
            try:
                state = json.loads(row[0])
            except (ValueError, TypeError):
                return None
            return state if isinstance(state, dict) else None
        return None
    state = session.get(_session_key(chat_id))
    return state if isinstance(state, dict) else None


def _save_state(session, user_id, chat_id, state):
    if user_id and chat_id:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO chat_test_state (user_id, chat_id,"
                " state_json, updated_at) VALUES (?, ?, ?, ?)"
                " ON CONFLICT(user_id, chat_id) DO UPDATE SET"
                " state_json = excluded.state_json,"
                " updated_at = excluded.updated_at",
                (user_id, str(chat_id), json.dumps(state),
                 int(time.time())))
            conn.commit()
        finally:
            conn.close()
        return
    session[_session_key(chat_id)] = state


def clear_state(session, user_id, chat_id):
    if user_id and chat_id:
        conn = _connect()
        try:
            conn.execute(
                "DELETE FROM chat_test_state WHERE user_id = ?"
                " AND chat_id = ?", (user_id, str(chat_id)))
            conn.commit()
        finally:
            conn.close()
        return
    session.pop(_session_key(chat_id), None)


# ------------------------------------------------------------------ #
# Rendering helpers
# ------------------------------------------------------------------ #

def _counts(state):
    c = {"correct": 0, "wrong": 0, "seen": 0, "solved": 0,
         "skip": 0}
    for outcome in state["outcomes"]:
        if outcome["outcome"] in c:
            c[outcome["outcome"]] += 1
    return c


def _progress_line(state):
    ln = _LINES[state["flavour"]]
    return ln["progress"].format(
        i=min(state["index"] + 1, len(state["items"])),
        n=len(state["items"]), s=_counts(state)["correct"])


def _question_line(state):
    ln = _LINES[state["flavour"]]
    item = state["items"][state["index"]]
    return ln["q"].format(i=state["index"] + 1,
                          n=len(state["items"]),
                          q=item["question"])


def _advance_lines(state):
    """After an outcome is recorded and index advanced: the
    progress + next question lines, or the result lines when
    the test just finished."""
    if state["index"] < len(state["items"]):
        return [_progress_line(state), _question_line(state)]
    return _result_lines(state, stopped=False)


def _result_lines(state, stopped=False):
    ln = _LINES[state["flavour"]]
    c = _counts(state)
    reached = sum(c.values())
    total = len(state["items"])
    denom = reached if stopped else total
    score = c["correct"]
    pct = round(100 * score / denom) if denom else 0
    lines = [ln["stopped"] if stopped else ln["end"]]
    lines.append(ln["score"].format(s=score, y=denom, p=pct))
    lines.append(ln["counts"].format(
        c=c["correct"], w=c["wrong"],
        v=c["seen"] + c["solved"], k=c["skip"]))
    if c["solved"]:
        lines.append(ln["solved_note"].format(v=c["solved"]))
    lines.append(ln["time"].format(t=_fmt_time(
        time.time() - state["started_at"], state["flavour"])))
    if stopped and total - reached > 0:
        lines.append(ln["left"].format(r=total - reached))
    weak, seen_topics = [], set()
    for outcome, item in zip(state["outcomes"], state["items"]):
        if outcome["outcome"] == "wrong":
            label = item.get("topic_label") or ""
            if label and label not in seen_topics:
                seen_topics.add(label)
                weak.append(label)
    if weak:
        lines.append(ln["weak"].format(topics=", ".join(weak)))
    else:
        lines.append(ln["no_weak"])
    if denom and pct >= 80:
        lines.append(ln["advice_high"])
    elif denom and pct >= 50:
        lines.append(ln["advice_mid"])
    else:
        lines.append(ln["advice_low"])
    return lines


def _plain_payload(lines):
    """A plain chat result (answer = first line, steps = the
    rest) — the chat JS renders plain results as one simple
    bubble: no card, no answer box, no step labels, no
    chips, no streaming reveal."""
    result = {
        "type": "Chat Test",
        "op": "chat_test",
        "answer": lines[0] if lines else "",
        "steps": lines[1:],
        "plain": True,
        "plain_reply": True,
        "fallback_kind": "chat_test",
    }
    return {"ok": True, "result": result, "intro": None,
            "followup_note": None}


def _record_mistake(session, item, given):
    """The existing Mistake Notebook mechanism (the session
    list app._record_mistakes maintains), same entry shape,
    source "chat test" — wrong answers only."""
    try:
        entry = {"question": item["question"],
                 "expected": item["answer"],
                 "given": str(given or ""),
                 "topic": item.get("topic_label"),
                 "source": "chat test"}
        notebook = session.get("mistakes", [])
        if not isinstance(notebook, list):
            notebook = []
        session["mistakes"] = ([entry] + notebook)[:50]
    except Exception:
        pass


# ------------------------------------------------------------------ #
# The flow
# ------------------------------------------------------------------ #

def _start(session, user_id, chat_id, req, text, lang,
           lang_request, student_class):
    cls = req["class_num"]
    if cls is None:
        cls = student_class
    if not isinstance(cls, int) or not (0 <= cls <= 12):
        cls = 10
    flavour = flavour_for(text, lang=lang,
                          lang_request=lang_request)
    rng = random.Random()
    items, note = _generate(req, cls, rng)
    ln = _LINES[flavour]
    if not items:
        clear_state(session, user_id, chat_id)
        return _plain_payload([ln["sorry"]])
    topic_label = req["topic_label"] or ln["mixed"]
    state = {
        "v": 1,
        "class_num": cls,
        "topic_label": topic_label,
        "flavour": flavour,
        "started_at": time.time(),
        "index": 0,
        "items": items,
        "outcomes": [],
    }
    _save_state(session, user_id, chat_id, state)
    lines = [ln["start"].format(topic=topic_label, cls=cls,
                                n=len(items))]
    if note == "topic":
        lines.append(ln["note_topic"].format(
            topic=req["topic_label"] or topic_label, cls=cls))
    elif note == "short":
        lines.append(ln["note_short"].format(n=len(items)))
    lines.append(_question_line(state))
    lines.append(ln["hint"])
    return _plain_payload(lines)


def _finish_or_save(session, user_id, chat_id, state):
    if state["index"] >= len(state["items"]):
        clear_state(session, user_id, chat_id)
    else:
        _save_state(session, user_id, chat_id, state)


def _solve_payload(session, state, solve_fn, lang,
                   lang_request, student_class):
    """The solve-command turn: the FULL solution of the
    current question as the normal solved card, the question
    marked solved-by-Ganitra (0 marks), and the next
    question / result as plain trailing lines (w124_next)."""
    item = state["items"][state["index"]]
    card = None
    if solve_fn is not None:
        try:
            solved = solve_fn(item["question"])
        except Exception:
            solved = None
        if isinstance(solved, dict) and solved.get("answer") \
                and not solve_failed(item["question"], solved):
            card = solved
    if card is None:
        steps = item.get("work_steps")
        if not steps and item["source"] == "practice":
            try:
                steps = test_mode.worked_steps(item["check"])
            except Exception:
                steps = None
        card = {
            "type": "Chat Test",
            "op": "chat_test_solve",
            "answer": item["answer"],
            "steps": [str(s) for s in (steps or [])],
            "fallback_kind": "chat_test",
        }
    state["outcomes"].append({"given": "", "outcome": "solved"})
    state["index"] += 1
    next_lines = _advance_lines(state)
    return card, next_lines, item


def handle_message(session, user_id, chat_id, text, lang="en",
                   lang_request=None, student_class=None,
                   solve_fn=None):
    """One chat message through the chat-test flow.

    Returns a payload dict (the api layer adds the language
    fields, explanation/teach and the w122 payload), or None
    when the message has nothing to do with a chat test and
    no test is active in this chat.
    """
    state = load_state(session, user_id, chat_id)
    if state and state.get("items"):
        req = parse_test_request(text)
        if req is not None:
            return _start(session, user_id, chat_id, req, text,
                          lang, lang_request, student_class)
        ln = _LINES[state["flavour"]]
        item = state["items"][state["index"]]
        if is_stop_command(text):
            lines = _result_lines(state, stopped=True)
            clear_state(session, user_id, chat_id)
            return _plain_payload(lines)
        if is_solve_command(text):
            card, next_lines, solved_item = _solve_payload(
                session, state, solve_fn, lang, lang_request,
                student_class)
            _finish_or_save(session, user_id, chat_id, state)
            return {"ok": True, "result": card, "intro": None,
                    "followup_note": None,
                    "w124_next": next_lines,
                    "w124_set_last": True,
                    "w124_solved_question": solved_item[
                        "question"]}
        if is_seen_command(text):
            state["outcomes"].append(
                {"given": "", "outcome": "seen"})
            state["index"] += 1
            lines = [ln["seen"].format(a=item["answer"])]
            lines += _advance_lines(state)
            _finish_or_save(session, user_id, chat_id, state)
            return _plain_payload(lines)
        if is_skip_command(text):
            state["outcomes"].append(
                {"given": "", "outcome": "skip"})
            state["index"] += 1
            lines = [ln["skip"].format(a=item["answer"])]
            lines += _advance_lines(state)
            _finish_or_save(session, user_id, chat_id, state)
            return _plain_payload(lines)
        # Anything else is the answer attempt on the current
        # question (the documented mid-test rule).
        given = str(text or "").strip()
        correct = _check_answer(item, given)
        state["outcomes"].append(
            {"given": given,
             "outcome": "correct" if correct else "wrong"})
        state["index"] += 1
        if correct:
            lines = [ln["correct"]]
        else:
            _record_mistake(session, item, given)
            lines = [ln["wrong"].format(a=item["answer"])]
        lines += _advance_lines(state)
        _finish_or_save(session, user_id, chat_id, state)
        return _plain_payload(lines)
    req = parse_test_request(text)
    if req is None:
        return None
    return _start(session, user_id, chat_id, req, text, lang,
                  lang_request, student_class)
