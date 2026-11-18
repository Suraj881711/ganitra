"""Wave 163: hint-first guided solve — "Seekh ke solve karo".

The Wave 162 all-AI comparison found the single biggest
pedagogical gap between Ganitra and the big AIs: ChatGPT's
Study Mode and Gemini's Guided Learning refuse to hand over
the answer first — they give one step at a time, let the
student try, check the attempt, and advance only as needed.
Ganitra already owned every ingredient (the solver's steps,
the Wave 85 step-checker's maths, the Wave 147 kind tone);
this module wires them into one guided flow, Ganitra's own
way:

* ENTRY is always the student's own ask — a learn-intent
  phrase in the message ("hint do", "seekh ke solve karo",
  "mujhe khud try karna hai", "step by step sikhao",
  "हिंट दो", "सीख के हल करो" ...), the same phrase sent
  alone right after an answer (it then guides the LAST
  question), or the "Seekh ke solve karo" row in the answer
  card's ••• menu (the client posts followup="guided" with
  the card's question as hidden context, exactly like a
  Wave 122 chip tap). A plain question with no learn-intent
  is NEVER claimed: it keeps the normal solve path
  byte-for-byte.
* THE FLOW: the question is solved ONCE by the caller's
  normal friendly pipeline, and that verified solution's
  own steps become the path. One step is posed at a time
  with its computed result masked ("Subtract 7 from both
  sides: 3x = ?") — the step's own instruction line is the
  hint, so nothing is paraphrased or invented. The student
  replies with their attempt, or "agla step" to have the
  step shown, and the next step is posed only then.
* ATTEMPT CHECKING reuses the Wave 85 step-checker's own
  machinery (stepcheck's parsers and invariants): equation
  attempts pass when they are PROPORTIONAL to the expected
  step (every legal move preserves that invariant, so a
  different-but-valid move is accepted, exactly like the
  step checker accepts a different method); numeric and
  expression attempts pass when they evaluate to the masked
  value. A wrong attempt earns a kind re-pose (Wave 147
  tone — never blame, never the answer); an unreadable one
  earns a gentle "write just the value" line. After two
  wrong attempts the options line is repeated.
* THE ANSWER IS NEVER WITHHELD (Suraj's "jawab milega hi"
  rule; answer-withholding sits on Wave 162's do-NOT-adopt
  list): "jawab bata do" / "poora jawab dikhao" / "show
  the answer" at ANY point serves the stored full answer
  immediately, exactly as the normal path served it. A
  student who jumps straight to the correct final answer
  is accepted and completes the flow. Guidance is an
  offer, never a lock.
* EXIT: "band karo" / "stop" ends guided mode with one
  kind line; a message that is plainly a NEW question (or
  a step-check message) exits silently back to the normal
  chat — the student is never trapped in the flow.
* LANGUAGE: every line follows the student's language /
  script (followups.flavour_for, the app's standing rule);
  the posed steps are the solver's own lines, already in
  the answer's language via the normal pipeline (Wave 130).

STATE: per (user, chat) in the accounts DB (table
guided_state), mirroring chat_test's storage; with no user
or chat id it rides in the Flask session under
"guided::<chat>". The full verified result is stored with
the state so escape / completion serve the very answer the
normal path produced — guided mode re-presents the SAME
solution in steps, never a different computation.

SCOPE v1: any solved answer with at least two steps and at
least one maskable (computational) step. Anything else —
unsolved, one-line, proof-shaped with no maskable step —
is not claimed, and the normal path answers untouched.
"""

import json
import re
import sqlite3
import time

import sympy as sp

import accounts
from followups import flavour_for, is_solved_result
from stepcheck import _clean_line, _parse_eq_line, \
    _proportional, _ref_number, _seg_value, _split_message, \
    _try_parse, _num_eq, _pct

__all__ = ["detect_learn_trigger", "parse_guided_command",
           "handle_message", "load_state", "clear_state"]


# ------------------------------------------------------------------
# Trigger: the learn-intent phrases.
#
# The discipline mirrors Wave 123/136's detectors: every
# pattern carries a LEARN shape (hint / seekh-sikh / khud
# try), never a bare content word — "step by step batao"
# stays a Wave 123 steps request, "detail me samjhao" a
# Wave 136 detail request; only the sikhao (teach-me) form
# of a step ask is a learn ask. Plain questions can contain
# none of these phrases, so the no-hijack guarantee is
# structural, not tuned.
# ------------------------------------------------------------------

_TRIGGER_PATTERNS = tuple(re.compile(p) for p in (
    r"\bhint\b",
    r"\bseekh\s*ke\b",
    r"\bsikha(?:o|ao|iye|te|ta|ti)?\b",
    r"\bseekh\s*kar\b",
    r"\bkhud\s+(?:try|solve|karna|karunga|karungi|se)\b",
    r"\btry\s+karna\s+hai\b",
    r"\blet\s+me\s+try\b",
    r"\bi\s+want\s+to\s+try\b",
    r"\bmujhe\s+khud\b",
    r"\bmain\s+khud\b",
    r"\bkhud\s+try\b",
))
_TRIGGER_SUBSTRINGS = (
    "हिंट", "सीख के", "सीखकर", "सिखा", "खुद try", "खुद solve",
)
_TRIGGER_STRIP = tuple(re.compile(p, re.I) for p in (
    r"\bhints?\b",
    r"\bseekh\s*ke\b",
    r"\bsikha(?:o|ao|iye|te|ta|ti)?\b",
    r"\bseekh\s*kar\b",
    r"\bkhud\s+(?:try|solve|karna|karunga|karungi|se)\b",
    r"\btry\s+karna\s+hai\b",
    r"\blet\s+me\s+try\b",
    r"\bi\s+want\s+to\s+try\b",
    r"\bmujhe\s+khud\b",
    r"\bmain\s+khud\b",
    r"\bkhud\s+try\b",
    r"\btry\b",
    r"\bkarna\s+hai\b",
    r"\bseekhna\s+hai\b",
    r"\bstep\s+by\s+step\b",
))
_DEV_TRIGGER_WORDS = ("हिंट दो", "हिंट", "सीख के", "सीखकर",
                      "सिखाओ", "सिखाइए", "सिखाते", "सिखा",
                      "खुद try", "खुद solve")

# Words that may surround a learn ask without being content
# — the bare-trigger discipline of followups'
# parse_bare_view_request: if NOTHING but these survive the
# stripping, the message is ONLY a learn ask.
_BARE_FILLER = {
    "batao", "bata", "bataao", "samjhao", "samjhaao", "samjha",
    "dikhao", "do", "de", "karo", "kar", "chahiye", "please",
    "plz", "me", "mein", "mai", "se", "ko", "ke", "ka", "ki",
    "the", "a", "an", "ye", "yeh", "is", "wala", "wale",
    "aur", "or", "and", "bhi", "hi", "ek", "baar", "phir",
    "ab", "zara", "tum", "aap", "mujhe", "mere", "liye",
    "bhai", "yaar", "sir", "madam", "teacher", "ganitra",
    "na", "toh", "solve", "hal", "question", "sawal",
    "step", "steps", "by",
    "karna", "hai", "hain", "karunga", "karungi", "give",
    "want", "try", "let", "seekhna", "seekh", "sikh",
    "raha", "rahi", "rahe",
    "बताओ", "बताइए", "समझाओ", "समझाइए", "में", "से", "दो",
    "दीजिए", "करो", "चाहिए", "एक", "हल", "सवाल", "स्टेप",
    "बाय", "चरण",
}


def _normalised(text):
    return re.sub(r"\s+", " ",
                  str(text or "").lower().replace("-", " "))


# Ask-verbs that may cling to a stripped residue's edges
# ("3x + 7 = 22 hint do" -> "...22 do"): trimming them off
# the EDGES leaves the question itself untouched.
_EDGE_FILLER = {"do", "de", "karo", "kar", "batao",
                "dikhao", "samjhao", "please", "plz", "zara"}


def _tidy_residue(residue):
    words = residue.split()
    while words and words[-1].lower().strip(".,") in _EDGE_FILLER:
        words.pop()
    while words and words[0].lower().strip(".,") in _EDGE_FILLER:
        words.pop(0)
    return " ".join(words).strip(" :,-।")


def detect_learn_trigger(text):
    """Classify a learn-intent message.

    Returns ("question", residue) when the message carries
    a learn phrase AND a question (the residue is the
    message with the learn phrases stripped — the text to
    solve), ("bare", None) when the message is ONLY a learn
    ask (guide the session's last question), else None.
    A step-check message ("my solution:" ...) is never a
    trigger — it belongs to the Wave 85 checker."""
    raw = str(text or "")
    if not raw.strip():
        return None
    if _split_message(raw) is not None:
        return None
    low = _normalised(raw)
    hit = any(p.search(low) for p in _TRIGGER_PATTERNS) \
        or any(s in raw for s in _TRIGGER_SUBSTRINGS)
    if not hit:
        return None
    residue = raw
    for word in _DEV_TRIGGER_WORDS:
        residue = residue.replace(word, " ")
    for pattern in _TRIGGER_STRIP:
        residue = pattern.sub(" ", residue)
    residue = _tidy_residue(re.sub(r"\s+", " ", residue))
    words = [w for w in re.split(r"[\s.,;:!?\"'()/]+", residue.lower())
             if w]
    if not words or all(w in _BARE_FILLER for w in words):
        return ("bare", None)
    return ("question", residue)


# ------------------------------------------------------------------
# In-flow commands: escape / next / stop.
# ------------------------------------------------------------------

_ESCAPE_PATTERNS = tuple(re.compile(p) for p in (
    r"\bjawab\s+(?:bata|dikha|de|do)\b",
    r"\bpoora\s+(?:jawab|solution|hal|answer)\b",
    r"\bpoori\s+detail\b",
    r"\banswer\s+(?:bata|dikha|de|do)\b",
    r"\bshow\s+(?:me\s+)?(?:the\s+)?(?:full\s+)?answer\b",
    r"\bfull\s+answer\b",
    r"\bseedha\s+jawab\b",
    r"\bdirect\s+(?:answer|jawab)\b",
    r"\bbas\s+jawab\b",
    r"\bsirf\s+jawab\b",
))
_ESCAPE_SUBSTRINGS = ("पूरा जवाब", "जवाब बता", "जवाब दिखा",
                      "जवाब दे दो", "जवाब दो", "पूरा हल",
                      "पूरा solution")
_NEXT_PATTERNS = tuple(re.compile(p) for p in (
    r"\bagla\s+(?:step|charan)\b",
    r"\bnext\s+step\b",
    r"\bagla\s+batao\b",
    r"\baage\s+badho\b",
    r"\bnext\b",
    r"\bagla\b",
))
_NEXT_SUBSTRINGS = ("अगला step", "अगला चरण", "अगला बताओ")
_STOP_PATTERNS = tuple(re.compile(p) for p in (
    r"\bband\s+karo\b",
    r"\bstop\b",
    r"\bruk\s*jao\b",
    r"\bchhodo\b",
    r"\brehne\s+do\b",
    r"\bcancel\b",
    r"\bkhatam\s+karo\b",
))
_STOP_SUBSTRINGS = ("बंद करो", "रुको", "छोड़ो", "खत्म करो")


def parse_guided_command(text):
    """One of "escape" / "next" / "stop" / None for a
    message received while guided mode is active. Escape
    outranks the rest: a frustrated "band karo, jawab bata
    do" wants the answer, and gets it."""
    raw = str(text or "")
    if not raw.strip():
        return None
    low = _normalised(raw)
    if any(p.search(low) for p in _ESCAPE_PATTERNS) \
            or any(s in raw for s in _ESCAPE_SUBSTRINGS):
        return "escape"
    if any(p.search(low) for p in _STOP_PATTERNS) \
            or any(s in raw for s in _STOP_SUBSTRINGS):
        return "stop"
    if any(p.search(low) for p in _NEXT_PATTERNS) \
            or any(s in raw for s in _NEXT_SUBSTRINGS):
        return "next"
    return None


# ------------------------------------------------------------------
# Lines — kind teacher, in the student's flavour (the
# stepcheck._STR pattern).
# ------------------------------------------------------------------

_STR = {
    "en": {
        "intro": "Learn mode — one step at a time. I will "
                 "show a step with its answer hidden; try it "
                 "yourself first. Say 'next step' if you want "
                 "the step shown, and 'show the answer' any "
                 "time for the full answer.",
        "pose": "Step {k} of {n}: {task}",
        "hint_value": "Find this value yourself.",
        "praise": "Correct — very well done!",
        "wrong": "Not quite — try once more, slowly.",
        "options": "You can say 'next step' to see this "
                   "step, or 'show the answer' for the full "
                   "answer.",
        "unread": "I could not read that as a step. Write "
                  "just the value or the full line — or say "
                  "'next step'.",
        "complete": "You solved it yourself — very well "
                    "done! Here is the full solution to "
                    "check against.",
        "stop": "No problem — learn mode is off. Ask me "
                "anything, any time.",
    },
    "roman": {
        "intro": "Seekh ke solve karte hain — ek samay par "
                 "ek step. Main step dikhaunga, uska jawab "
                 "chhupa rahega; pehle tum try karo. 'agla "
                 "step' bolo to step dikha dunga, aur 'jawab "
                 "bata do' bolo to poora jawab mil jayega.",
        "pose": "Step {k} of {n}: {task}",
        "hint_value": "Ye maan khud nikaal ke dekho.",
        "praise": "Bilkul sahi — bahut badhiya!",
        "wrong": "Bilkul sahi nahi hua — ek baar phir, "
                 "aaram se try karo.",
        "options": "'agla step' bolo to ye step dikha dunga, "
                   "ya 'jawab bata do' bolo to poora jawab "
                   "mil jayega.",
        "unread": "Ye step ke roop me samajh nahi aaya. "
                  "Sirf maan likh ke bhejo, ya poori line "
                  "likho — ya 'agla step' bolo.",
        "complete": "Tumne khud solve kar liya — bahut "
                    "badhiya! Ye raha poora solution, mila "
                    "ke dekh lo.",
        "stop": "Koi baat nahi — learn mode band kar diya. "
                "Kuch bhi poochna ho, kabhi bhi pooch lo.",
    },
    "dev": {
        "intro": "सीखकर हल करते हैं — एक बार में एक चरण। "
                 "मैं चरण दिखाऊँगा, उसका उत्तर छिपा रहेगा; "
                 "पहले तुम कोशिश करो। 'अगला step' बोलो तो "
                 "चरण दिखा दूँगा, और 'जवाब बता दो' बोलो तो "
                 "पूरा जवाब मिल जाएगा।",
        "pose": "चरण {k} / {n}: {task}",
        "hint_value": "यह मान खुद निकालकर देखो।",
        "praise": "बिल्कुल सही — बहुत बढ़िया!",
        "wrong": "बिल्कुल सही नहीं हुआ — एक बार फिर, आराम "
                 "से कोशिश करो।",
        "options": "'अगला step' बोलो तो यह चरण दिखा दूँगा, "
                   "या 'जवाब बता दो' बोलो तो पूरा जवाब मिल "
                   "जाएगा।",
        "unread": "यह चरण के रूप में समझ नहीं आया। सिर्फ़ "
                  "मान लिखकर भेजो, या पूरी पंक्ति लिखो — या "
                  "'अगला step' बोलो।",
        "complete": "तुमने खुद हल कर लिया — बहुत बढ़िया! "
                    "यह रहा पूरा हल, मिलाकर देख लो।",
        "stop": "कोई बात नहीं — learn mode बंद कर दिया। "
                "कुछ भी पूछना हो, कभी भी पूछ लो।",
    },
}


def _strings(flavour):
    return _STR.get(flavour, _STR["en"])


# ------------------------------------------------------------------
# State storage — chat_test's pattern: DB per (user, chat),
# Flask session otherwise.
# ------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS guided_state (
    user_id     TEXT NOT NULL,
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
    return f"guided::{chat_id or 'local'}"


def load_state(session, user_id, chat_id):
    if user_id and chat_id:
        try:
            conn = _connect()
            try:
                row = conn.execute(
                    "SELECT state_json FROM guided_state"
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
                "INSERT INTO guided_state (user_id, chat_id,"
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
                "DELETE FROM guided_state WHERE user_id = ?"
                " AND chat_id = ?", (user_id, str(chat_id)))
            conn.commit()
        finally:
            conn.close()
        return
    session.pop(_session_key(chat_id), None)


# ------------------------------------------------------------------
# Masking a step: the posed task hides the computed result.
# ------------------------------------------------------------------

def _split_instruction(step):
    """(instruction, body): split on the first ": " when the
    head is a short instruction with no "=" of its own —
    the Wave 149 shape ("Subtract 7 from both sides: 3x =
    15"). The instruction IS the hint; only the result is
    masked."""
    s = str(step or "").strip()
    if ": " in s:
        head, body = s.split(": ", 1)
        if "=" not in head and len(head) <= 60 and body.strip():
            return head.strip(), body.strip()
    return None, s


def _mask_step(step):
    """(pose_text, expected_value) — the step with everything
    after its LAST "=" replaced by "?", and the masked-off
    value. (step_text, None) when the step carries no
    computable result (a framing / givens line): such steps
    are shown in full as context, never posed as tasks."""
    head, body = _split_instruction(step)
    if "=" not in body:
        return str(step or "").strip(), None
    before, _, after = body.rpartition("=")
    if not before.strip() or not after.strip():
        return str(step or "").strip(), None
    masked = before.rstrip() + " = ?"
    pose = f"{head}: {masked}" if head else masked
    return pose, after.strip()


_RESTATE_HEADS = {"solution", "answer", "ans", "उत्तर", "हल"}


def _is_restatement(step, answer):
    """True when a step merely restates the final answer —
    the solver's trailing "Solution: x = 5" line, or a step
    whose whole body IS the answer text. Such a step is not
    a task: the guided path ends at the last real
    computation, and completion serves the original result
    (this line included) whole. A step like "GCD = 6" for
    the answer "6" is NOT a restatement — it is the final
    computation itself."""
    if not str(answer or "").strip():
        return False
    head, body = _split_instruction(step)
    # A bare step whose whole text is the answer restates
    # it. (A step WITH an instruction — "Divide both sides
    # by 3: x = 5" — is the final computation itself, never
    # a restatement, though its body equals the answer.)
    if head is None and _norm_text(body) == _norm_text(answer):
        return True
    if head and head.strip().lower() in _RESTATE_HEADS:
        claimed = _claimed_part(body)
        ans = _claimed_part(answer) if "=" in answer else answer
        return _match_value(claimed, ans) is True
    return False


def _task_index(state, frm):
    """The first maskable step at or after `frm`, plus the
    framing lines before it (shown in full). (None, [...])
    when no task remains."""
    steps = state["steps"]
    framing = []
    k = frm
    while k < len(steps):
        _pose, expected = _mask_step(steps[k])
        if expected is not None:
            return k, framing
        framing.append(str(steps[k]).strip())
        k += 1
    return None, framing


# ------------------------------------------------------------------
# Attempt checking — the Wave 85 step-checker's invariants.
# ------------------------------------------------------------------

def _norm_text(s):
    return re.sub(r"\s+", "", str(s or "").lower()).rstrip(".")


def _expr_of(text):
    try:
        return _try_parse(_pct(str(text or "")))
    except Exception:
        return None


def _match_value(claimed, expected):
    """True / False / None: does `claimed` carry the same
    value as `expected`? Exact text first, then SymPy
    equivalence / numeric equality (stepcheck's _num_eq),
    then unit-carrying numbers (stepcheck's _seg_value)."""
    if not str(claimed or "").strip() \
            or not str(expected or "").strip():
        return None
    if _norm_text(claimed) == _norm_text(expected):
        return True
    ce, ee = _expr_of(claimed), _expr_of(expected)
    if ce is not None and ee is not None:
        try:
            if ce.is_number and ee.is_number:
                return bool(_num_eq(ce, ee))
            return bool(sp.simplify(ce - ee) == 0)
        except Exception:
            return None
    cv = _seg_value(_pct(str(claimed)))
    ev = _seg_value(_pct(str(expected)))
    if cv is not None and ev is not None:
        return bool(_num_eq(cv, ev))
    return None


def _claimed_part(text):
    """What the student claims the masked value is: the part
    after the last "=" of their line, or the whole line."""
    t = _clean_line(text)
    if "=" in t:
        return t.rpartition("=")[2].strip()
    return t


def _check_attempt(text, state):
    """Judge one attempt at the posed step.

    Returns True (the step is done), "complete" (the student
    jumped straight to the correct final answer — accept
    and finish), False (judged, and wrong), or None (the
    reply cannot be read as maths at all)."""
    steps = state["steps"]
    k = state["index"]
    _head, body = _split_instruction(steps[k])
    _pose, expected = _mask_step(steps[k])
    if expected is None:
        return None
    attempt = str(text or "").strip()
    if not attempt:
        return None
    claimed = _claimed_part(attempt)
    # (0) Straight to the final answer: the claim matches
    # the stored answer's own value. Kindness over pedantry
    # — a student who solved it whole is done.
    answer = str(state.get("answer") or "")
    ans_claim = _claimed_part(answer) if "=" in answer else answer
    if _match_value(claimed, ans_claim) is True \
            and state["index"] < len(steps):
        # Only a genuine jump: the claim must not be merely
        # this step's own expected value restated (that is
        # path (2) below, a normal step success).
        if _match_value(claimed, expected) is not True:
            return "complete"
    # (1) Whole-line equation equivalence — stepcheck's
    # legal-move invariant: the attempt's (lhs - rhs) must
    # be proportional to the expected step's.
    a_eq = _parse_eq_line(_clean_line(attempt))
    e_eq = _parse_eq_line(_clean_line(body))
    if a_eq is not None and e_eq is not None:
        da = sp.expand(a_eq[0] - a_eq[1])
        de = sp.expand(e_eq[0] - e_eq[1])
        syms = da.free_symbols | de.free_symbols
        if len(syms) == 1 and de != 0:
            try:
                if _proportional(da, de, next(iter(syms))):
                    return True
            except Exception:
                pass
    # (2) The claimed value against the masked value.
    m = _match_value(claimed, expected)
    if m is not None:
        return m
    # (3) The whole attempt as an expression for the value
    # ("800 × 15/100" for a masked 120).
    if claimed != attempt:
        m = _match_value(attempt, expected)
        if m is not None:
            return m
    # (4) On the last step, a bare final-answer value also
    # completes the step (the answer's number, however the
    # student writes it).
    if k == len(steps) - 1:
        ref = _ref_number(answer)
        if ref is not None:
            cv = _seg_value(_pct(claimed))
            if cv is None:
                e = _expr_of(claimed)
                cv = e if e is not None and e.is_number else None
            if cv is not None and _num_eq(cv, ref):
                return True
    # Judged-wrong only when the reply is maths-SHAPED: an
    # equation, a parseable expression / value, or a bare
    # string of maths characters. Prose that merely carries
    # digits ("12 aur 18 ka HCF nikalo" — a NEW question) is
    # unreadable as an attempt, never accused; the caller
    # routes it back to the normal chat.
    if "=" in attempt or _expr_of(attempt) is not None \
            or _seg_value(_pct(_clean_line(attempt))) is not None \
            or re.fullmatch(r"[\d\s.,/+*×xX^()%-]+",
                            attempt or ""):
        return False
    return None


# ------------------------------------------------------------------
# Payloads — plain chat turns, exactly like chat_test's.
# ------------------------------------------------------------------

def _plain_payload(lines):
    """A plain chat result (answer = first line, steps = the
    rest): no card, no answer box, no step labels, no chips
    — the chat JS renders plain results as one simple
    bubble."""
    result = {
        "type": "Ganitra",
        "op": "guided_step",
        "answer": lines[0] if lines else "",
        "steps": lines[1:],
        "plain": True,
        "plain_reply": True,
        "fallback_kind": "guided",
    }
    return {"ok": True, "result": result, "intro": None,
            "followup_note": None}


def _full_payload(state, intro):
    """The stored full answer, served whole — the escape and
    completion serve. `w163_set_last` tells the caller to
    make it the session's last solution (the api layer owns
    those writes, mirroring chat_test's w124 pattern)."""
    return {"ok": True, "result": state["result"],
            "intro": intro, "followup_note": None,
            "w163_full": True, "w163_set_last": True,
            "w163_question": state["question"]}


# ------------------------------------------------------------------
# The flow
# ------------------------------------------------------------------

def _pose_lines(state, first=False):
    """Lines posing the current task: framing lines in full,
    then the masked step, then the find-it-yourself hint
    when the step carries no instruction of its own. Also
    advances state["index"] onto the task step (framing
    steps before it are consumed by being shown). Returns
    None when no task remains (the caller completes)."""
    S = _strings(state["flavour"])
    k, framing = _task_index(state, state["index"])
    if k is None:
        return None
    state["index"] = k
    pose, _expected = _mask_step(state["steps"][k])
    head, _body = _split_instruction(state["steps"][k])
    lines = []
    if first:
        lines.append(S["intro"])
    lines.extend(framing)
    lines.append(S["pose"].format(k=k + 1, n=len(state["steps"]),
                                  task=pose))
    if head is None:
        lines.append(S["hint_value"])
    return lines


def _start(session, user_id, chat_id, question, lang,
           lang_request, solve_fn, flavour_text=None):
    """Solve `question` through the caller's normal pipeline
    and, when the answer honestly supports guided mode (a
    solved result, 2+ steps, 1+ maskable step), open the
    flow and pose step 1. Otherwise None — the caller runs
    the completely normal path, so the student always gets
    the normal answer (jawab milega hi)."""
    question = str(question or "").strip()
    if not question or solve_fn is None:
        return None
    try:
        result = solve_fn(question)
    except Exception:
        return None
    if not is_solved_result(result):
        return None
    steps = [str(s).strip() for s in (result.get("steps") or [])
             if str(s).strip()]
    if len(steps) < 2:
        return None
    # Trailing restatements of the answer ("Solution: x =
    # 5") are not tasks — the path ends at the last real
    # computation; completion still serves the ORIGINAL
    # result, restatement line and all.
    while steps and _is_restatement(
            steps[-1], str(result.get("answer") or "")):
        steps.pop()
    if not steps:
        return None
    if not any(_mask_step(s)[1] is not None for s in steps):
        return None
    # The flavour reads the student's own words first (their
    # script is the standing signal), then the question and
    # the solution's lines.
    flavour = flavour_for(
        " ".join([str(flavour_text or ""), question,
                  str(result.get("answer") or "")] + steps),
        lang=lang, lang_request=lang_request)
    state = {"question": question, "steps": steps,
             "answer": str(result.get("answer") or ""),
             "result": result, "index": 0, "attempts": 0,
             "flavour": flavour}
    lines = _pose_lines(state, first=True)
    if lines is None:
        return None
    _save_state(session, user_id, chat_id, state)
    return _plain_payload(lines)


def _advance(session, user_id, chat_id, state, prefix_lines):
    """The current step is done (attempt correct, or the
    student asked to see it): pose the next task, or
    complete the flow with the full answer when none
    remains."""
    S = _strings(state["flavour"])
    state["index"] += 1
    state["attempts"] = 0
    lines = _pose_lines(state)
    if lines is None:
        clear_state(session, user_id, chat_id)
        return _full_payload(state, S["complete"])
    _save_state(session, user_id, chat_id, state)
    return _plain_payload(list(prefix_lines) + lines)


def _looks_like_new_question(text):
    """Off-flow detection: a message that plainly starts a
    NEW problem (a question mark, or maths payload plus a
    question verb) is not an attempt — guided mode exits
    and the normal chat answers it."""
    raw = str(text or "")
    if "?" in raw or "？" in raw:
        return True
    low = _normalised(raw)
    if not any(ch.isdigit() for ch in raw):
        return False
    return bool(re.search(
        r"\b(?:find|solve|calculate|compute|what|how many|"
        r"how much|nikalo|nikaal|batao|kya|kitna|kitne)\b",
        low))


def handle_message(session, user_id, chat_id, text, lang="en",
                   lang_request=None, solve_fn=None,
                   start_question=None):
    """The guided-solve entry, mirroring chat_test's
    handle_message contract: a payload dict when this
    message belongs to guided mode, else None (the caller
    runs the normal path byte-for-byte).

    `start_question` is set by the caller for a •••-menu
    "Seekh ke solve karo" tap (followup="guided"): start
    guided mode on that question directly."""
    state = load_state(session, user_id, chat_id)

    if start_question is not None:
        q = str(start_question or "").strip() \
            or str(session.get("last_question") or "").strip()
        if q:
            payload = _start(session, user_id, chat_id, q,
                             lang, lang_request, solve_fn,
                             flavour_text=q)
            if payload is not None:
                return payload
        # No honest guided start: fall through — an active
        # state (if any) still owns the message; otherwise
        # the normal path answers the tap's label text.

    if state is not None:
        command = parse_guided_command(text)
        if command == "escape":
            clear_state(session, user_id, chat_id)
            return _full_payload(state, None)
        if command == "stop":
            clear_state(session, user_id, chat_id)
            return _plain_payload(
                [_strings(state["flavour"])["stop"]])
        trigger = detect_learn_trigger(text)
        if trigger is not None and trigger[0] == "question":
            # A learn ask about a NEW question restarts the
            # flow on it; if that start fails, exit cleanly
            # and let the normal path answer the message.
            payload = _start(session, user_id, chat_id,
                             trigger[1], lang, lang_request,
                             solve_fn, flavour_text=text)
            if payload is not None:
                return payload
            clear_state(session, user_id, chat_id)
            return None
        if trigger is not None:
            # A bare learn ask mid-flow: re-pose the step.
            lines = _pose_lines(state)
            if lines is None:
                clear_state(session, user_id, chat_id)
                return _full_payload(
                    state, _strings(state["flavour"])["complete"])
            return _plain_payload(lines)
        if command == "next":
            step_text = str(state["steps"][state["index"]])
            return _advance(session, user_id, chat_id, state,
                            [step_text])
        if _split_message(str(text or "")) is not None:
            # A step-check message belongs to Wave 85.
            clear_state(session, user_id, chat_id)
            return None
        verdict = _check_attempt(text, state)
        if verdict == "complete":
            clear_state(session, user_id, chat_id)
            return _full_payload(
                state, _strings(state["flavour"])["complete"])
        if verdict is True:
            S = _strings(state["flavour"])
            done = str(state["steps"][state["index"]])
            return _advance(session, user_id, chat_id, state,
                            [S["praise"], done])
        if verdict is False:
            S = _strings(state["flavour"])
            state["attempts"] = int(state.get("attempts") or 0) + 1
            _save_state(session, user_id, chat_id, state)
            lines = _pose_lines(state)
            out = [S["wrong"]] + (lines or [])
            if state["attempts"] >= 2:
                out.append(S["options"])
            return _plain_payload(out)
        # Unreadable as maths: a fresh question exits to the
        # normal chat; anything else (doubt, "samajh nahi",
        # small talk) earns a gentle re-pose inside the flow.
        if _looks_like_new_question(text):
            clear_state(session, user_id, chat_id)
            return None
        S = _strings(state["flavour"])
        lines = _pose_lines(state)
        return _plain_payload([S["unread"]] + (lines or []))

    # No active flow: only an explicit learn ask starts one.
    trigger = detect_learn_trigger(text)
    if trigger is None:
        return None
    if trigger[0] == "question":
        return _start(session, user_id, chat_id, trigger[1],
                      lang, lang_request, solve_fn,
                      flavour_text=text)
    last_q = str(session.get("last_question") or "").strip()
    if last_q:
        return _start(session, user_id, chat_id, last_q,
                      lang, lang_request, solve_fn,
                      flavour_text=text)
    return None
