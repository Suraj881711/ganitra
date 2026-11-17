"""Wave 129 — "meri galti kahan hai", the natural way.

Wave 85 built the step checker, but only behind a written
convention: the student had to type the question, then a
"my solution:" marker line, then their working. Real students
do not know the convention — they just write like they talk:

    Solve 2x + 3 = 11
    maine aise kiya hai, galti kahan hai?
    2x = 11 - 3
    2x = 9
    x = 4.5

This module turns that into a chat feature students will
actually use, WITHOUT touching the Wave 85 checker itself:

* ``split_intent_message`` recognises a check-my-work intent
  (EN / HI / Hinglish phrase sets below) and splits the message
  into (question, steps) by REMOVING the intent phrase wherever
  it sits — its own line, glued to the question line, at the
  very start or at the very end. The parts are then handed to
  the UNCHANGED Wave 85 machinery (``step_check_result`` on a
  synthesised marker message), so every verdict — first wrong
  step, all-correct, different-but-valid method, honest
  out-of-scope — is exactly Wave 85's.

* When the intent arrives WITHOUT steps ("mera solution check
  karo" / "2x + 3 = 11 ki galti batao"), ``prompt_result``
  builds the one-line ask ("apne steps bhejo — ek line me ek
  step") and api.py parks the question in
  ``session["galti_pending"]``; the student's next message is
  then read as the steps (``check_pending_steps``). One turn
  only: any other next message quietly expires the pending
  state and is answered normally — the student is never
  trapped in the flow.

* When the steps arrive WITHOUT a question (the student just
  solved that question in this chat), api.py offers
  ``session["last_question"]`` as the question — see
  ``steps_only`` from ``split_intent_message``.

The gate stays strict, Wave 85-style: an intent phrase alone
never produces a verdict (steps + a reference solve + checkable
lines are all still required, inside stepcheck), and a fresh
question that merely CONTAINS the word "check" ("check karo
15% of 240 kitna hoga") carries no intent phrase — the phrase
sets require a self-reference (my / mera / meri / apna) or an
explicit mistake ask (galti kahan / where is my mistake) — so
it solves exactly as before.
"""

import re

from fallback import _flavour
from stepcheck import step_check_result

__all__ = ["split_intent_message", "natural_check_result",
           "check_pending_steps", "prompt_result", "flavour_of",
           "INTENT_PATTERNS"]


# ---------------------------------------------------------------------------
# The intent phrase sets (verbatim — also in the wave notes)
# ---------------------------------------------------------------------------
# Every pattern carries either a self-reference (the student's
# OWN solution/steps/answer) or an explicit mistake ask. Bare
# "check" / "check karo" is deliberately NOT an intent.

INTENT_PATTERNS = [
    # English
    r"check\s+my\s+(solution|working|steps|answer|copy|work)",
    r"check\s+(this|the)\s+(solution|working)",
    r"is\s+(this|it|my\s+solution|my\s+answer|my\s+working)"
    r"\s+(correct|right)",
    r"is\s+my\s+(solution|answer|working)\s+(correct|right|ok)",
    r"where\s+(did|have)\s+i\s+(go\s+wrong|gone\s+wrong"
    r"|made?\s+an?\s*mistake)",
    r"where\s+is\s+(my|the)\s+mistake",
    r"find\s+(my|the)\s+mistake",
    r"what\s+is\s+my\s+mistake",
    r"did\s+i\s+(do|solve)\s+(it|this)\s+(right|correctly)",
    r"am\s+i\s+(right|correct)",
    # Hinglish (Roman) — longer phrases first: at one start
    # position the regex takes the FIRST alternative that
    # matches, so "maine aise kiya hai" must precede the
    # shorter "maine aise kiya" or "hai" survives as a line.
    r"(mera|meri|apna|apni)\s+(solution|hal|answer|jawab|copy"
    r"|working|steps)\s+check\s+karo",
    r"maine\s+aise\s+kiya\s+hai",
    r"maine\s+aisa\s+kiya\s+hai",
    r"(meri|apni)\s+galti\s+batao",
    # Deploy-27 merge fix: the full phrase must precede the
    # bare "(meri|apni) galti" fallback below — regex takes
    # the leftmost match, so "meri galti kahan hai" used to
    # match only "meri galti" and park "kahan" as a bogus
    # pending question, breaking the two-turn flow for the
    # wave's own canonical phrase.
    r"(meri|apni)\s+galti\s+(kahan|kaha|kahaan|kidhar)\s+hai",
    r"galti\s+(kahan|kaha|kahaan|kidhar)\s+hai",
    r"galti\s+batao",
    r"galtiya?n?\s+batao",
    r"(meri|apni)\s+galti",
    r"(mera|meri|apna|apni)\s+(solution|hal|answer|jawab|copy"
    r"|working|steps)\s+check",
    r"(solution|hal|copy|answer|jawab|steps)\s+check\s+karo",
    r"check\s+karo\s+(mera|meri|apna|apni)",
    r"maine\s+aise\s+(kiya|solve\s+kiya|hal\s+kiya)",
    r"maine\s+aisa\s+kiya",
    r"sahi\s+hai\s+kya",
    r"sahi\s+hua\s+kya",
    r"(ye|yeh)\s+sahi\s+hai",
    r"(mera|meri)\s+(hal|solution|answer|jawab)\s+sahi\s+hai",
    # Hindi (Devanagari)
    r"मेरी\s+गलती\s+बताओ",
    r"मेरी\s+गलती",
    r"गलती\s+(कहाँ|कहां|किधर)",
    r"गलती\s+बताओ",
    r"मैंने\s+ऐसे\s+किया\s+है",
    r"मैंने\s+ऐसे\s+किया",
    r"मेरा\s+हल\s+(जाँचो|जांचो|चेक\s+करो)",
    r"मेरी\s+कॉपी\s+(जाँचो|जांचो|चेक\s+करो)",
    r"क्या\s+यह\s+सही\s+है",
    r"ये\s+सही\s+है\s+क्या",
    r"मेरा\s+हल\s+सही\s+है",
]

_INTENT_RE = re.compile(
    "(" + "|".join(INTENT_PATTERNS) + ")", re.I)

# Leftover fragments of an intent phrase that may survive the
# span removal ("mera solution check karo" can leave a lone
# "karo" line). A line made ONLY of such words is debris, not
# a question and not a step — it is dropped before the parts
# are assigned, so it can never shift Wave 85's step numbers.
_JUNK_WORDS = {"hai", "karo", "krke", "karke", "batao", "bata",
               "please", "plz", "aur", "bro", "bhai", "check",
               "galti", "mera", "meri", "solution", "hal", "do",
               "ye", "yeh", "kahan", "kaha", "kahaan", "kidhar",
               "बताओ", "है", "करो"}


def _is_junk_line(line):
    toks = [t.strip(".,;:!?-–—") for t in str(line).lower().split()]
    toks = [t for t in toks if t]
    return bool(toks) and all(t in _JUNK_WORDS for t in toks)


def _clean_question(text):
    q = re.sub(r"\s+", " ", str(text or "")).strip()
    q = q.strip(" :,-–—")
    q = re.sub(r"(?i)^(please|plz)\s+", "", q)
    q = re.sub(r"(?i)\s+(check\s+)?karo$", "", q)
    q = re.sub(r"(?i)\s+hai$", "", q)
    return q.strip(" :,-–—")


# A first line carrying one of these reads as a QUESTION, not
# as working — used only when the intent phrase came first and
# the layout is otherwise ambiguous.
_QUESTION_WORDS = re.compile(
    r"(solve|find|calculate|simplify|factor|expand|prove|"
    r"evaluate|what|when|given|kitna|kitne|value|"
    r"hal\s+karo|निकालो|ज्ञात|कीजिए|हल\s+करो)", re.I)

# "I did it like this" phrases ANNOUNCE working: what follows
# them is steps, even when the first step line could double as
# a bare-equation question.
_ANNOUNCE_RE = re.compile(
    r"(maine\s+(aise|aisa)\s+kiya|मैंने\s+ऐसे\s+किया)", re.I)


def _chain_split(line):
    parts = re.split(r"→|->|;", str(line or ""))
    return [p.strip() for p in parts if p.strip()]


def split_intent_message(text):
    """Split a check-my-work message into its parts.

    Returns None when the message carries no intent phrase.
    Else a dict:
      {"question": str | None,   — the question line, cleaned
       "steps":    [str] | None, — >= 2 working lines, if sent
       "steps_only": bool}       — steps sent but no question
    The intent phrase itself is removed wherever it sat (its
    own line, glued to the question, first or last line), so
    what remains is question line(s) followed by working
    lines — the first remaining line is the question, the rest
    are the steps (a single remaining step line may still be
    an arrow/semicolon chain)."""
    text = str(text or "")
    first = _INTENT_RE.search(text)
    if not first:
        return None
    # Did any real content precede the intent phrase? When it
    # did, the layout is question-first (the intent may sit on
    # its own middle line or at the very end). When it did
    # not, the intent came first and the layout is ambiguous —
    # resolved by _ANNOUNCE_RE / _QUESTION_WORDS below.
    head_has_content = any(
        ln.strip(" :,-–—?") and not _is_junk_line(ln)
        for ln in text[:first.start()].splitlines())
    announces_steps = bool(_ANNOUNCE_RE.match(first.group(0)))
    # Remove every intent phrase, leaving a line boundary
    # where it sat so line structure survives.
    cleaned = _INTENT_RE.sub("\n", text)
    lines = [ln.strip() for ln in cleaned.splitlines()]
    lines = [ln for ln in lines
             if ln.strip(" :,-–—?") and not _is_junk_line(ln)]
    if not lines:
        return {"question": None, "steps": None,
                "steps_only": False}
    if len(lines) == 1:
        # One line left: either the question alone (no steps
        # sent) or one chained line of steps for a question
        # asked earlier. A chain line reads as steps only when
        # the intent came first (nothing before it) — after a
        # question line it would have been handled below.
        only = lines[0]
        chained = _chain_split(only)
        if len(chained) >= 2 and "=" in only \
                and not head_has_content:
            return {"question": None, "steps": chained,
                    "steps_only": True}
        return {"question": _clean_question(only),
                "steps": None, "steps_only": False}
    if not head_has_content and (
            announces_steps
            or (not _QUESTION_WORDS.search(lines[0])
                and "=" not in lines[0])):
        # The intent came first and what follows is working,
        # not a question: an announcing phrase ("maine aise
        # kiya hai:") or a first line that is neither worded
        # like a question nor an equation. The steps belong
        # to a question already asked in this chat.
        return {"question": None, "steps": lines,
                "steps_only": True}
    question = _clean_question(lines[0])
    steps = lines[1:]
    if len(steps) == 1:
        chained = _chain_split(steps[0])
        if len(chained) >= 2:
            steps = chained
    if len(steps) < 2:
        # A question plus a single working line is not yet a
        # checkable solution — treat as "no steps sent" and
        # let the prompt flow ask for the full working.
        return {"question": question, "steps": None,
                "steps_only": False}
    return {"question": question, "steps": steps,
            "steps_only": False}


def _synthesised(question, steps):
    return (str(question) + "\nmy solution:\n"
            + "\n".join(str(s) for s in steps))


def natural_check_result(text, lang=None):
    """The Wave 85 verdict for a natural (marker-less)
    check-my-work message, or None — the message is not one,
    or its steps/question do not pass Wave 85's own gate, in
    which case the normal solve flow answers it untouched."""
    split = split_intent_message(text)
    if split is None or not split.get("question") \
            or not split.get("steps"):
        return None
    # The reply flavour comes from the student's ORIGINAL
    # message — the synthesised marker text no longer
    # contains their intent phrase, hence no language signal.
    return step_check_result(
        _synthesised(split["question"], split["steps"]),
        lang=lang, flavour_hint=_flavour(text))


def flavour_of(text):
    """The reply flavour (en / roman / dev) of a message —
    parked alongside a pending prompt so the verdict two
    turns later still speaks the student's language."""
    return _flavour(text)


def check_pending_steps(pending_question, text, lang=None,
                        flavour_hint=None):
    """The verdict for the message that follows the "apne
    steps bhejo" prompt, or None when it cannot be read as
    steps (the caller then expires the pending state and
    answers the message normally).

    With a parked question, the whole message is the working
    (Wave 85's own splitter handles one-line arrow chains).
    Without one, the message must carry its own question —
    the marker convention, the natural split, or (because
    the prompt just asked for exactly this layout) a bare
    first-line-question + step-lines layout all work."""
    direct = step_check_result(text, lang=lang,
                               flavour_hint=flavour_hint)
    if direct is not None:
        return direct
    if pending_question:
        return step_check_result(
            _synthesised(pending_question,
                         [str(text or "").strip()]),
            lang=lang, flavour_hint=flavour_hint)
    lines = [ln.strip() for ln in str(text or "").splitlines()
             if ln.strip()]
    if len(lines) >= 2:
        steps = lines[1:]
        if len(steps) == 1:
            chained = _chain_split(steps[0])
            if len(chained) >= 2:
                steps = chained
        if len(steps) >= 2:
            verdict = step_check_result(
                _synthesised(_clean_question(lines[0]), steps),
                lang=lang, flavour_hint=flavour_hint)
            if verdict is not None:
                return verdict
    return natural_check_result(text, lang=lang)


# ---------------------------------------------------------------------------
# The "apne steps bhejo" prompt — one short line, student's flavour
# ---------------------------------------------------------------------------

_PROMPT = {
    ("en", True):
        "Send your steps for this question — one step per "
        "line — and I will check them and show you the first "
        "mistake.",
    ("en", False):
        "Send the question and your steps — question on the "
        "first line, then one step per line — and I will "
        "check them and show you the first mistake.",
    ("roman", True):
        "Is sawal ke apne steps bhejo — ek line me ek step — "
        "main check karke pehli galti bata dunga.",
    ("roman", False):
        "Sawal aur apne steps bhejo — pehli line me sawal, "
        "phir ek line me ek step — main check karke pehli "
        "galti bata dunga.",
    ("dev", True):
        "इस सवाल के अपने steps भेजो — एक पंक्ति में एक step — "
        "मैं जाँच करके पहली गलती बता दूँगा।",
    ("dev", False):
        "सवाल और अपने steps भेजो — पहली पंक्ति में सवाल, फिर "
        "एक पंक्ति में एक step — मैं जाँच करके पहली गलती बता "
        "दूँगा।",
}


def prompt_result(text, has_question):
    """The one-line prompt result, in the normal result shape
    (plain, so the chat renders it as a simple bubble with no
    explanation/advice/teach attached — exactly like the
    Wave 67 one-liners)."""
    flavour = _flavour(text)
    line = _PROMPT.get((flavour, bool(has_question)),
                       _PROMPT[("en", bool(has_question))])
    return {
        "type": "step_check",
        "op": "check_steps_ask",
        "answer": "",
        "steps": [line],
        "step_check": True,
        "galti_ask": True,
        "plain": True,
    }
