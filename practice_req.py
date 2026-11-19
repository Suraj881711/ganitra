"""Wave 201: the PRACTICE-REQUEST intent (Suraj's live
test, 20 Nov 2026).

Suraj typed into the chat:

    "12th class ke kuch qustin milinge solve karane ke liye"

("give me some Class 12 questions to solve") and Ganitra
answered the bare not-found line. His words: "solve karne
ke liye question kyu nhi de rha, ye kuch toh bole — ye koi
baat nhi hoti ans not found."

Root cause (verified): NO recogniser existed for a
practice-question REQUEST. guidance.py / maths_meta only
give practice ADVICE ("practice kaise karu" -> the advice
card), and the ask fell through every layer to not-found —
although the app owns plenty of verified material:
practice_gen (Classes 6-10, answers correct by
construction), the concept-topic starters of topics_data /
topics_banda (Classes 4-12, verified at serve time by
chat_test's machinery), board_quiz and a 3,294-item
verified databank (exact-match only, no class retrieval —
not used here, exactly as practice_loop decided).

This module makes the request a first-class intent in the
chat pipeline, a handle_message flow in api_solve in the
Wave 124 / 163 / 165 tradition (it sits after the chat
test, the guided flow and the practice loop, before the
galti block):

  * RECOGNITION (parse_practice_request): a question NOUN
    (question / questions / sawal / प्रश्न / सवाल, common
    misspellings included) plus a request MARKER (do /
    chahiye / milenge / give me / दो / चाहिए / मिलेंगे, a
    "solve karane ke liye" / "practice ke liye" purpose
    phrase, or a bare short ask naming a class or chapter).
    Class (4-12, any script or numeral system, ordinals
    and Hindi class words included) and a chapter / topic
    are extracted when named.
  * VETOES, so no neighbour loses its messages: a paper
    ask (Wave 174 owns it), a test ask (Wave 124 owns it),
    a knowledge ask (kisne / kaun — Wave 177/183 facts own
    it), an advice ask with no explicit give-marker
    ("practice kaise karu" stays guidance/meta advice),
    an MCQ-shaped message, and anything problem-bearing
    (a concrete problem to solve — fallback's Wave-159
    shape, plus an "=" veto).
  * SERVING: a friendly card (fallback_kind
    "practice_req", never a solved result — no answer box,
    no chips) with a warm head line, SET_SIZE real
    questions numbered, WITHOUT answers, and a closing
    invitation to solve them and send the working (the
    normal solve / step-check path then handles the
    student's attempts — this module never intercepts an
    answer). Questions come from chat_test's verified
    sources only: practice_gen items for Classes 6-10 and
    serve-time-verified concept starters for every class;
    a question whose answer the system cannot check is
    never served.
  * NO CLASS NAMED: one friendly line asking which class
    (and optionally a chapter) — the ask is parked per
    chat, and the student's class reply ("12", "class
    10", "दसवीं") serves the set. Any other message
    releases the park and is answered normally — the
    student is never trapped. For this intent family the
    not-found line is unreachable: every class 4-12 has
    material, sources fall back to each other, and a
    named topic that cannot fill a set falls back to the
    class's mixed questions WITH a one-line note (the
    Wave-124 honesty rule).
  * FOLLOW-UP: "aur do" / "more" / "और दो" in the same
    chat serves the NEXT set — different questions, no
    repeats within the chat (the served texts ride in the
    per-chat state, chat_test's storage pattern: a sqlite
    table for a signed-in chat, else a session key). A
    fresh practice request replaces the state; any other
    message is answered by the normal path exactly as if
    this module did not exist.

Language: the card follows the student's own message
(followups.flavour_for — en / roman / dev, with the
Wave-107 explicit request outranking detection); the
parked ask-class flavour is remembered so a bare "12"
reply is answered in the language the student asked in.
"""

import json
import random
import re
import sqlite3
import time

import accounts
import chat_test
import practice_gen
import test_mode
from chat_test import _has_phrase, _tokens
from followups import flavour_for

__all__ = ["parse_practice_request", "is_more_request",
           "handle_message", "load_state", "clear_state"]

SET_SIZE = 4

# ------------------------------------------------------------------ #
# Recognition
# ------------------------------------------------------------------ #

_NOUNS = {"question", "questions", "qustin", "qustion",
          "questin", "qustions", "ques", "sawal", "sawaal",
          "प्रश्न", "सवाल", "प्रश्नों"}

# Explicit give-me markers: a token is enough next to the
# noun. "milinge / milenge / milega" is the live phrase's
# own verb, in the student's own spellings.
_MARKER_TOKENS = {"do", "दो", "de", "दे", "chahiye", "चाहिए",
                  "milenge", "milinge", "milega", "milege",
                  "milengi", "मिलेंगे", "मिलेगा", "bhejo",
                  "भेजो", "dijiye", "दीजिए", "give", "want",
                  "need", "bhej", "lao", "लाओ"}
_MARKER_PHRASES = (
    ["give", "me"], ["de", "do"], ["bhej", "do"],
    ["ke", "liye"], ["के", "लिए"],
    ["solve", "karane"], ["solve", "karne"],
    ["practice", "ke"], ["अभ्यास", "के"],
)
# The markers that outrank an advice word when both ride in
# one message ("questions kaise milenge" is a request FOR
# questions, not a how-to ask).
_STRONG_MARKERS = {"do", "दो", "chahiye", "चाहिए", "milenge",
                   "milinge", "milega", "मिलेंगे", "मिलेगा",
                   "give", "bhejo", "भेजो", "dijiye", "दीजिए"}

_PAPER_TOKENS = {"paper", "papers", "पेपर", "पत्र"}
_TEST_TOKENS = {"test", "quiz", "exam", "tests", "टेस्ट",
                "क्विज़", "क्विज", "परीक्षा", "एग्जाम"}
_KNOWLEDGE_TOKENS = {"kisne", "किसने", "kaun", "कौन",
                     "kyu", "क्यों", "kyon"}
_ADVICE_TOKENS = {"kaise", "कैसे", "taiyari", "तैयारी",
                  "tips", "strategy", "timetable", "schedule",
                  "improve", "padhai", "पढ़ाई", "preparation",
                  "prepare"}
# Words that kill the bare short-ask branch: the fragment
# is then a statement or a how/many ask, not a request.
_WEAK_VETO = {"solve", "find", "kya", "क्या", "kaise",
              "कैसे", "hai", "hota", "hoti", "kitne",
              "कितने", "kitna", "nikalo", "ज्ञात", "हल"}

_HINDI_ORDINALS = {
    "छठी": 6, "छठवीं": 6, "chhathi": 6,
    "सातवीं": 7, "saatvi": 7, "saatvin": 7,
    "आठवीं": 8, "aathvi": 8, "aathvin": 8,
    "नौवीं": 9, "नवमी": 9, "naavi": 9, "navi": 9,
    "दसवीं": 10, "dasvi": 10, "dasvin": 10, "daswi": 10,
    "ग्यारहवीं": 11, "gyarahvi": 11, "gyarahvin": 11,
    "बारहवीं": 12, "barahvi": 12, "barahvin": 12,
    "barahwi": 12,
}

_STOPWORDS = set(chat_test._STOPWORDS) | {
    "qustin", "qustion", "questin", "qustions", "ques",
    "solve", "karane", "karne", "karana", "karna", "liye",
    "practice", "abhyas", "अभ्यास", "milenge", "milinge",
    "milega", "kuch", "कुछ", "some", "give", "want", "need", "bhejo",
    "भेजो", "dijiye", "दीजिए", "please", "maths", "math",
    "mathematics", "ganit", "गणित", "wala", "wali", "ke",
    "लिए", "दे", "bhej", "lao", "लाओ", "batao",
}

_ORDINAL_RE = re.compile(r"^(\d{1,2})(?:st|nd|rd|th)$")


def _loop_shaped(tokens):
    """The Wave-165 loop's own shapes: "ek aur ..." /
    "aur practice ..." / "one more ..." openings, or a
    "like this" marker (aisa hi / ऐसा ही / like). The bare
    phrase "practice karna hai" also trips the loop's
    trigger, but glued to an explicit question request
    ("practice karna hai questions do") the message is a
    fresh request FOR questions — this wave's, per
    Suraj's spec — so only the loop-SHAPED asks defer."""
    if tokens[:2] in (["ek", "aur"], ["aur", "practice"],
                      ["one", "more"]):
        return True
    return any(t in ("aisa", "ऐसा", "aisi", "like")
               for t in tokens)


def _parse_class(text, tokens):
    """The class named in the message (1-12), or None:
    "class 12" / "12th class" / "12 class" / "कक्षा 12" /
    "12वीं" / Hindi ordinal words / a digit token touching
    "class" — every script and numeral system the app
    serves."""
    raw = str(text or "").lower()
    m = re.search(r"(?:class|कक्षा|kaksha)\s*(\d{1,2})\b", raw)
    if not m:
        m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\b", raw)
    if not m:
        m = re.search(r"\b(\d{1,2})\s*(?:class|कक्षा)\b", raw)
    if not m:
        m = re.search(r"\b(\d{1,2})वीं\b", raw)
    if m:
        try:
            n = int(m.group(1))
        except ValueError:
            n = None
        if n is not None and 1 <= n <= 12:
            return n
    for tok in tokens:
        if tok in _HINDI_ORDINALS:
            return _HINDI_ORDINALS[tok]
        om = _ORDINAL_RE.match(tok)
        if om:
            n = int(om.group(1))
            if 1 <= n <= 12:
                return n
        if tok.isdigit() and 1 <= int(tok) <= 12:
            i = tokens.index(tok)
            near = tokens[max(0, i - 1):i + 2]
            if "class" in near or "कक्षा" in near:
                return int(tok)
    return None


def parse_practice_request(text):
    """A parsed practice request dict, or None when the
    message is not asking FOR practice questions.

    Returns {"class_num" (or None), "topic_key" (a
    practice_gen topic or None), "topic_query" (free text
    for a concept-topic search, or None), "topic_label"}.
    """
    tokens = _tokens(text)
    if not tokens:
        return None
    # --- Vetoes first: these messages belong to others. ---
    try:
        from practice_loop import is_practice_trigger
        if is_practice_trigger(text) and _loop_shaped(tokens):
            return None  # Wave 165: "ek aur aisa hi sawal"
    except Exception:
        pass
    if any(t in _PAPER_TOKENS for t in tokens):
        return None  # Wave 174: a paper ask
    if any(t in _TEST_TOKENS for t in tokens):
        return None  # Wave 124: a test ask
    if any(t in _KNOWLEDGE_TOKENS for t in tokens):
        return None  # Wave 177/183: a who/what fact ask
    if "=" in str(text or ""):
        return None  # an equation is a problem, not a request
    if re.search(r"\(\s*[a-d]\s*\)", str(text or "").lower()):
        return None  # MCQ options ride along: a problem
    try:
        from fallback import _w159_problem_bearing
        if _w159_problem_bearing(text):
            return None  # a concrete problem to solve
    except Exception:
        pass
    # --- The gate: a question noun + a request marker. ---
    if not any(t in _NOUNS for t in tokens):
        return None
    strong = any(t in _STRONG_MARKERS for t in tokens)
    marked = strong or any(t in _MARKER_TOKENS for t in tokens) \
        or any(_has_phrase(tokens, list(p))
               for p in _MARKER_PHRASES)
    class_num = _parse_class(text, tokens)
    topic_key = None
    for tok in tokens:
        if tok in chat_test._PRACTICE_SYNONYMS:
            topic_key = chat_test._PRACTICE_SYNONYMS[tok]
            break
    topic_query = None
    if topic_key is None:
        rest = [t for t in tokens
                if t not in _STOPWORDS and not t.isdigit()
                and not _ORDINAL_RE.match(t)]
        if rest:
            topic_query = " ".join(rest)
    if not marked:
        # A bare short ask naming a class or a chapter:
        # "class 12 questions", "integrals questions".
        if len(tokens) > 7:
            return None
        if any(t in _WEAK_VETO for t in tokens):
            return None
        if class_num is None and not topic_query:
            return None
    # An advice ask ("practice kaise karu") stays with the
    # guidance / meta advice layers unless an explicit
    # give-marker outranks the advice word.
    if any(t in _ADVICE_TOKENS for t in tokens) and not strong:
        return None
    if topic_key is not None:
        topic_label = test_mode.TOPIC_LABELS[topic_key]
    elif topic_query:
        topic_label = topic_query.title() \
            if topic_query.isascii() else topic_query
    else:
        topic_label = None
    return {"class_num": class_num, "topic_key": topic_key,
            "topic_query": topic_query,
            "topic_label": topic_label}


_MORE_PHRASES = (
    ["aur", "do"], ["aur", "chahiye"], ["aur", "questions"],
    ["aur", "sawal"], ["aur", "bhejo"], ["aur", "de", "do"],
    ["aur", "milenge"], ["mujhe", "aur", "do"], ["more"],
    ["more", "questions"], ["give", "more"], ["next", "set"],
    ["और", "दो"], ["और", "चाहिए"],
)
_MORE_TAIL = {"please", "bhai", "na", "aur", "questions",
              "sawal", "कृपया", "do", "दो"}


def is_more_request(text):
    """A bare "aur do" / "more" continuation: the phrase
    must OPEN the message (a solve command like "solve
    karo aur do" merely contains the words and is never
    read as one) and the message must stay short."""
    tokens = _tokens(text)
    if not tokens or len(tokens) > 5:
        return False
    for phrase in _MORE_PHRASES:
        p = list(phrase)
        if tokens[:len(p)] == p and all(
                t in _MORE_TAIL for t in tokens[len(p):]):
            return True
    return False


def _parse_class_reply(text):
    """A bare class answer to the parked ask ("12",
    "class 10", "12th", "दसवीं"), or None."""
    tokens = _tokens(text)
    if not tokens or len(tokens) > 6:
        return None
    cls = _parse_class(text, tokens)
    if cls is not None:
        return cls
    if len(tokens) == 1 and tokens[0].isdigit():
        n = int(tokens[0])
        if 1 <= n <= 12:
            return n
    return None


def _looks_like_class_attempt(text):
    """The reply TRIED to name a class but no class could
    be read (a stray digit / ordinal): re-ask kindly
    instead of dropping the park."""
    tokens = _tokens(text)
    if not tokens or len(tokens) > 4:
        return False
    return any(t.isdigit() or _ORDINAL_RE.match(t)
               for t in tokens)


# ------------------------------------------------------------------ #
# Question gathering — chat_test's verified sources, with an
# exclusion set so a chat never sees the same question twice
# ------------------------------------------------------------------ #

def _starter_items(class_num, topic_query, count, rng,
                   exclude):
    """Concept-topic starters for the class, verified one
    by one at serve time (chat_test._verify_starter),
    skipping anything already served in this chat.
    Returns (items, fell_back) — chat_test's semantics."""
    entries = chat_test._topic_entries(class_num)
    if not entries:
        return [], False
    query_tokens = _tokens(topic_query) if topic_query else []
    scored = []
    for idx, entry in enumerate(entries):
        score = chat_test._score_entry(entry, query_tokens) \
            if query_tokens else 0
        scored.append((score, idx, entry))
    matched = [s for s in scored if s[0] > 0]
    matched.sort(key=lambda s: (-s[0], s[1]))
    rest = [s for s in scored if s[0] == 0]
    rng.shuffle(rest)
    ordered = matched + rest
    items, seen = [], set(exclude)
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
        if not chat_test._verify_starter(entry):
            continue
        if query_tokens and score == 0:
            fell_back = True
        items.append({
            "source": "starter",
            "question": starter,
            "answer": str(entry.get("answer")).strip(),
            "topic_label": entry.get("name", ""),
            "check": {"answer": str(entry.get("answer"))
                      .strip()},
            "work_steps": [str(s) for s in
                           (entry.get("steps") or [])],
        })
    return items, fell_back


def _practice_items(class_num, topic_key, count, rng,
                    exclude):
    """practice_gen items (Classes 6-10) minus the ones
    already served in this chat; the generator's variety
    makes a fresh batch on every call."""
    topics = [topic_key] if topic_key else \
        list(practice_gen.TOPICS)
    items, seen = [], set(exclude)
    for _attempt in range(3):
        if len(items) >= count:
            break
        for item in chat_test._practice_items(
                class_num, topic_key, count * 2, rng):
            if item["question"] in seen:
                continue
            seen.add(item["question"])
            items.append(item)
            if len(items) >= count:
                break
    return items[:count]


def _gather(class_num, topic_key, topic_query, count, rng,
            exclude):
    """(items, note_kind) — the Wave-124 source order with
    cross-source fallback, so classes 4-12 always have
    material: a named topic goes to the verified starters
    first (topped up from practice_gen), a named practice
    topic to its generator, anything else to the class's
    mixed practice set or its starters. note_kind is
    "topic" when a named topic fell back to mixed, "short"
    when fewer than asked could be prepared."""
    fell_back = False
    if topic_key and class_num in practice_gen.CLASSES:
        items = _practice_items(class_num, topic_key, count,
                                rng, exclude)
    elif topic_query:
        items, fell_back = _starter_items(
            class_num, topic_query, count, rng, exclude)
        if len(items) < count and class_num in \
                practice_gen.CLASSES:
            have = {i["question"] for i in items}
            items += _practice_items(
                class_num, None, count - len(items), rng,
                exclude | have)
            fell_back = True
    elif class_num in practice_gen.CLASSES:
        items = _practice_items(class_num, None, count, rng,
                                exclude)
        if len(items) < count:
            have = {i["question"] for i in items}
            extra, _ = _starter_items(
                class_num, None, count - len(items), rng,
                exclude | have)
            items += extra
    else:
        items, _ = _starter_items(class_num, None, count,
                                  rng, exclude)
    note = None
    if fell_back and items:
        note = "topic"
    elif items and len(items) < count:
        note = "short"
    return items[:count], note


# ------------------------------------------------------------------ #
# State storage — per chat, server-side (chat_test's pattern)
# ------------------------------------------------------------------ #

_SCHEMA = """
CREATE TABLE IF NOT EXISTS practice_req_state (
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
    return f"practice_req::{chat_id or 'local'}"


def load_state(session, user_id, chat_id):
    if user_id and chat_id:
        try:
            conn = _connect()
            try:
                row = conn.execute(
                    "SELECT state_json FROM practice_req_state"
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
                "INSERT INTO practice_req_state (user_id,"
                " chat_id, state_json, updated_at) VALUES"
                " (?, ?, ?, ?) ON CONFLICT(user_id, chat_id)"
                " DO UPDATE SET state_json ="
                " excluded.state_json, updated_at ="
                " excluded.updated_at",
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
                "DELETE FROM practice_req_state WHERE"
                " user_id = ? AND chat_id = ?",
                (user_id, str(chat_id)))
            conn.commit()
        finally:
            conn.close()
        return
    session.pop(_session_key(chat_id), None)


# ------------------------------------------------------------------ #
# Language lines (flavour: en / roman / dev) — Wave 147 kind tone
# ------------------------------------------------------------------ #

_LINES = {
    "en": {
        "head": "Here are {n} practice questions for Class "
                "{cls} — try them one by one:",
        "head_topic": "Here are {n} {topic} questions for "
                      "Class {cls} — try them one by one:",
        "head_more": "Here are {n} more practice questions "
                     "for Class {cls}:",
        "tail": "Solve them and send your working — I will "
                "check it. Want more? Just say 'aur do'.",
        "ask": "Sure, I will give you questions! For which "
               "class — and if there is a chapter on your "
               "mind, tell me that too.",
        "ask_again": "I did not catch the class — just tell "
                     "me the number, like 10 or 12.",
        "empty": "I have shown all the fresh Class {cls} "
                 "questions I had ready — solve these "
                 "first, then ask me for another class or "
                 "chapter.",
    },
    "roman": {
        "head": "Ye rahe Class {cls} ke {n} practice "
                "questions — ek-ek karke solve karo:",
        "head_topic": "Ye rahe Class {cls} ke {topic} ke "
                      "{n} questions — ek-ek karke solve "
                      "karo:",
        "head_more": "Ye rahe Class {cls} ke aur {n} "
                     "questions:",
        "tail": "Inhe solve karke apni working bhejo, main "
                "check kar dunga. Aur chahiye toh bas 'aur "
                "do' bolna.",
        "ask": "Bilkul milenge! Kis class ke questions "
               "chahiye — aur koi chapter hai toh wo bhi "
               "bata do.",
        "ask_again": "Class samajh nahi aaya — bas number "
                     "bata do, jaise 10 ya 12.",
        "empty": "Class {cls} ke jitne fresh questions "
                 "ready the, sab dikha diye — pehle inhe "
                 "solve karo, phir kisi aur class ya chapter "
                 "ke maang lena.",
    },
    "dev": {
        "head": "ये रहे कक्षा {cls} के {n} अभ्यास प्रश्न — "
                "एक-एक करके हल करो:",
        "head_topic": "ये रहे कक्षा {cls} के {topic} के {n} "
                      "प्रश्न — एक-एक करके हल करो:",
        "head_more": "ये रहे कक्षा {cls} के और {n} प्रश्न:",
        "tail": "इन्हें हल करके अपनी working भेजो, मैं check "
                "कर दूँगा। और चाहिए तो बस 'और दो' बोलना।",
        "ask": "बिल्कुल मिलेंगे! किस कक्षा के प्रश्न चाहिए — "
               "और कोई अध्याय हो तो वह भी बता दो।",
        "ask_again": "कक्षा समझ नहीं आई — बस number बता दो, "
                     "जैसे 10 या 12।",
        "empty": "कक्षा {cls} के जितने fresh प्रश्न तैयार थे, "
                 "सब दिखा दिए — पहले इन्हें हल करो, फिर किसी "
                 "और कक्षा या अध्याय के माँग लेना।",
    },
}


def _card(head, items, tail):
    """The serve card: the warm head line as the answer,
    the numbered questions (WITHOUT answers) and the
    closing invitation as steps — library content like
    the Wave-174 paper card, never a solved result."""
    steps = [f"{i}. {item['question']}"
             for i, item in enumerate(items, 1)]
    if tail:
        steps.append(tail)
    return {"type": "Practice Questions",
            "op": "practice_req",
            "answer": head,
            "steps": steps,
            "fallback_kind": "practice_req"}


def _plain(op, line):
    return {"type": "Ganitra", "op": op, "answer": line,
            "steps": [], "fallback_kind": "practice_req",
            "plain_reply": True, "plain": True}


def _payload(result):
    return {"ok": True, "result": result, "intro": None,
            "followup_note": None}


# ------------------------------------------------------------------ #
# The flow
# ------------------------------------------------------------------ #

def _serve(session, user_id, chat_id, class_num, topic_key,
           topic_query, topic_label, flavour, exclude,
           more=False):
    """Serve one set and remember it in the chat state.
    Returns a payload, or None when no verified question
    could be prepared at all (the caller then lets the
    normal path answer — for classes 4-12 the sources
    make this unreachable in practice)."""
    rng = random.Random()
    items, note = _gather(class_num, topic_key, topic_query,
                          SET_SIZE, rng, set(exclude))
    ln = _LINES[flavour]
    if not items:
        return None
    state = {"v": 1, "pending_class": False,
             "class_num": class_num, "topic_key": topic_key,
             "topic_query": topic_query,
             "topic_label": topic_label,
             "served": list(exclude) +
             [i["question"] for i in items]}
    _save_state(session, user_id, chat_id, state)
    if more:
        head = ln["head_more"].format(n=len(items),
                                      cls=class_num)
    elif topic_label:
        head = ln["head_topic"].format(
            n=len(items), topic=topic_label, cls=class_num)
    else:
        head = ln["head"].format(n=len(items), cls=class_num)
    steps = []
    if note == "topic":
        steps.append(chat_test._LINES[flavour]["note_topic"]
                     .format(topic=topic_label or "",
                             cls=class_num))
    elif note == "short":
        steps.append(chat_test._LINES[flavour]["note_short"]
                     .format(n=len(items)))
    card = _card(head, items, ln["tail"])
    card["steps"] = steps + card["steps"]
    return _payload(card)


def _serve_more(session, user_id, chat_id, state, flavour):
    ln = _LINES[flavour]
    payload = _serve(
        session, user_id, chat_id, state["class_num"],
        state.get("topic_key"), state.get("topic_query"),
        state.get("topic_label"), flavour,
        exclude=state.get("served") or [], more=True)
    if payload is not None:
        return payload
    # The ready pool for this class/topic is exhausted:
    # one honest friendly line (never the not-found line),
    # and the state is kept so a fresh request can restart.
    return _payload(_plain(
        "practice_req_empty",
        ln["empty"].format(cls=state["class_num"])))


def handle_message(session, user_id, chat_id, text,
                   lang="en", lang_request=None,
                   student_class=None):
    """One chat message through the practice-request flow.

    Returns a payload dict (the api layer adds the
    language fields, explanation/teach and the w122
    payload), or None when the message has nothing to do
    with a practice request and no request is parked in
    this chat.
    """
    state = load_state(session, user_id, chat_id)
    # Flavour exactly as the fallback chain computes it for
    # its request layers (paper / meta / guidance): an
    # explicit Wave-107 request first, else the message's
    # own script flavour — so a Hinglish ask ("...kuch
    # qustin milinge...") is answered in Hinglish even when
    # the session language never switched.
    if lang_request:
        flavour = flavour_for(text, lang=lang,
                              lang_request=lang_request)
    else:
        try:
            from fallback import _flavour
            flavour = _flavour(text)
        except Exception:
            flavour = flavour_for(text, lang=lang)
    if state and state.get("pending_class"):
        req = parse_practice_request(text)
        if req is not None and req["class_num"] is not None:
            return _serve(session, user_id, chat_id,
                          req["class_num"], req["topic_key"],
                          req["topic_query"],
                          req["topic_label"], flavour,
                          exclude=[])
        cls = _parse_class_reply(text)
        if cls is not None:
            return _serve(session, user_id, chat_id, cls,
                          state.get("topic_key"),
                          state.get("topic_query"),
                          state.get("topic_label"),
                          state.get("flavour") or flavour,
                          exclude=[])
        if _looks_like_class_attempt(text):
            ln = _LINES[state.get("flavour") or flavour]
            return _payload(_plain("practice_req_ask",
                                   ln["ask_again"]))
        # Anything else releases the park and is answered
        # by the normal path below / beyond — never trapped.
        clear_state(session, user_id, chat_id)
        state = None
    req = parse_practice_request(text)
    if req is not None:
        if req["class_num"] is None:
            _save_state(session, user_id, chat_id, {
                "v": 1, "pending_class": True,
                "class_num": None,
                "topic_key": req["topic_key"],
                "topic_query": req["topic_query"],
                "topic_label": req["topic_label"],
                "flavour": flavour, "served": []})
            return _payload(_plain("practice_req_ask",
                                   _LINES[flavour]["ask"]))
        return _serve(session, user_id, chat_id,
                      req["class_num"], req["topic_key"],
                      req["topic_query"], req["topic_label"],
                      flavour, exclude=[])
    if state and is_more_request(text):
        return _serve_more(session, user_id, chat_id, state,
                           flavour)
    return None
