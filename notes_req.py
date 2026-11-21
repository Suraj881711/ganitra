"""Wave 212: the NOTES-REQUEST intent (Suraj, 21 Nov 2026).

In chat, a student saying "trigonometry ke notes do" /
"notes chahiye" / "quadratic equations ke notes bhejo"
is asking for revision notes on a chapter/topic.  Before
this wave NO layer recognised the ask: practice_req owns
requests for questions, the concept layers own "what is
X" asks, and a bare notes request fell through to the
not-found line.

The module mirrors practice_req's contract: handle_message
returns the api payload dict ({"ok", "result", "intro",
"followup_note"}) or None when the message is not a notes
request.  Notes content comes only from verified in-app
sources — the topics library (concept_topics) first, then
the concepts table (concepts.find_concept) — repackaged as
a notes card (definition, formula/key points, one example).
When the request names no topic, the chat's last solved
question supplies the topic; when neither exists, the
student is asked which chapter (a clarification, never a
dead end).

Discipline: a message carrying a concrete problem (digits
with an operator, an equation) is NEVER captured — the
vetoes run first, exactly like practice_req's.
"""

import re

_NOTES_WORDS = ("notes", "नोट्स", "note")
_ASK_WORDS = ("do", "दो", "chahiye", "चाहिए", "bhejo",
              "भेजो", "send", "give", "de", "dedo", "दे",
              "दे दो", "bana", "बना", "please", "pls",
              "chahiye mujhe", "milenge", "milega")
_STRIP_WORDS = {
    "notes", "नोट्स", "note", "ke", "ka", "ki", "के", "का",
    "की", "for", "chapter", "topic", "par", "पर", "do",
    "दो", "chahiye", "चाहिए", "bhejo", "भेजो", "send",
    "give", "de", "dedo", "दे", "bana", "बना", "please",
    "pls", "mujhe", "मुझे", "mere", "liye", "लिए", "short",
    "quick", "revision", "wala", "वाला", "wale", "वाले",
    "a", "an", "the", "of", "on", "in", "me", "mein", "में",
    "hai", "है", "kuch", "कुछ", "bana do", "se",
}

_LINES = {
    "en": {
        "head": "{topic} — Notes",
        "ask": "Bilkul! Kis chapter ya topic ke notes "
               "chahiye? Bas naam bata do — jaise "
               "'trigonometry' ya 'quadratic equations'.",
        "tail": "In notes ko padh kar topic ke questions "
                "bhejo, main solve karke dunga.",
    },
    "roman": {
        "head": "{topic} — Notes",
        "ask": "Bilkul! Kis chapter ya topic ke notes "
               "chahiye? Bas naam bata do — jaise "
               "'trigonometry' ya 'quadratic equations'.",
        "tail": "In notes ko padh kar topic ke questions "
                "bhejo, main solve karke dunga.",
    },
    "dev": {
        "head": "{topic} — Notes",
        "ask": "बिल्कुल! किस अध्याय या topic के notes "
               "चाहिए? बस नाम बता दो — जैसे 'trigonometry' "
               "या 'quadratic equations'।",
        "tail": "इन notes को पढ़कर topic के questions "
                "भेजो, मैं हल करके दूँगा।",
    },
}


def _tokens(text):
    return [w for w in re.split(
        r"[\s.,;:!?\"'()।/]+", str(text or "").lower()) if w]


def parse_notes_request(text):
    """A parsed notes request {"topic_query": str | None},
    or None when the message is not asking FOR notes.

    topic_query is the chapter/topic named in the message
    (possibly None — the caller may fall back to the chat's
    last topic)."""
    raw = str(text or "")
    t = raw.lower()
    # The notes word must be a WORD: "notebook" is a thing
    # you buy, and a "100 rupee note" is money — neither is
    # a request for study notes.
    if not (re.search(r"\bnotes?\b", t) or "नोट्स" in t):
        return None
    if any(ch.isdigit() for ch in raw) and any(
            w in t for w in ("rupee", "rs", "₹", "paisa",
                             "paise", "रुपये", "रुपए",
                             "notebook")):
        return None
    # Vetoes: a concrete problem is never a notes request,
    # and "note down" is an instruction about the answer,
    # not a request for notes.
    if "note down" in t or "note kar" in t:
        return None
    if any(ch.isdigit() for ch in raw) and any(
            ch in t for ch in "+-*/^="):
        return None
    if "=" in t:
        return None
    has_ask = any(re.search(r"\b" + re.escape(w) + r"\b", t)
                  if w.isascii() else w in t
                  for w in _ASK_WORDS)
    possessive = ("ke notes" in t or "ka notes" in t
                  or "के notes" in t or "notes do" in t
                  or "notes chahiye" in t)
    if not (has_ask or possessive):
        return None
    words = [w for w in _tokens(t) if w not in _STRIP_WORDS]
    topic = " ".join(words).strip()
    return {"topic_query": topic or None}


def _flavour_of(text, lang_request=None):
    if lang_request == "hi":
        return "dev"
    if lang_request == "hinglish":
        return "roman"
    if lang_request == "en":
        return "en"
    try:
        from fallback import _flavour
        return _flavour(text)
    except Exception:
        return "en"


def _card(topic_label, lines, flavour):
    ln = _LINES[flavour]
    steps = list(lines)
    steps.append(ln["tail"])
    return {"type": "Notes", "op": "notes_req",
            "answer": ln["head"].format(topic=topic_label),
            "steps": steps,
            "fallback_kind": "notes_req"}


def _plain(op, line):
    return {"type": "Ganitra", "op": op, "answer": line,
            "steps": [], "fallback_kind": "notes_req",
            "plain_reply": True, "plain": True}


def _payload(result):
    return {"ok": True, "result": result, "intro": None,
            "followup_note": None}


def _notes_lines_from_concept_result(res):
    lines = []
    ans = str(res.get("answer") or "").strip()
    if ans:
        lines.append(ans)
    for s in res.get("steps") or []:
        s = str(s).strip()
        if s and s not in lines:
            lines.append(s)
    return lines


def _notes_lines_from_concept(entry, flavour):
    lines = []
    if flavour == "dev" and entry.get("hinglish"):
        lines.append(str(entry["hinglish"]))
    if entry.get("formula"):
        lines.append("Formula: " + str(entry["formula"]))
    if entry.get("explain"):
        lines.append(str(entry["explain"]))
    if flavour != "dev" and entry.get("hinglish") \
            and flavour == "roman":
        lines.insert(0, str(entry["hinglish"]))
    ex = entry.get("example") or {}
    if ex.get("q"):
        lines.append("Example: " + str(ex["q"]))
    if ex.get("a"):
        lines.append("Answer: " + str(ex["a"]))
    return [ln for ln in lines if ln.strip()]


def handle_message(session, user_id, chat_id, text,
                   lang="en", lang_request=None,
                   student_class=None):
    """One chat message through the notes-request flow.
    Returns the api payload, or None when the message is
    not a notes request."""
    parsed = parse_notes_request(text)
    if parsed is None:
        return None
    flavour = _flavour_of(text, lang_request)
    ln = _LINES[flavour]
    topic_query = parsed.get("topic_query")
    if not topic_query and isinstance(session, dict):
        last_q = session.get("last_question")
        if last_q:
            topic_query = str(last_q)
    if not topic_query:
        return _payload(_plain("notes_req_ask", ln["ask"]))
    # Source 1: the topics library.
    try:
        from concept_topics import topic_concept_result
        res = topic_concept_result(topic_query)
    except Exception:
        res = None
    if res is not None:
        lines = _notes_lines_from_concept_result(res)
        if lines:
            label = topic_query.title() \
                if len(topic_query) <= 40 else "Notes"
            return _payload(_card(label, lines, flavour))
    # Source 2: the concepts table.
    try:
        from concepts import find_concept
        entry = find_concept(topic_query)
    except Exception:
        entry = None
    if entry is not None:
        lines = _notes_lines_from_concept(entry, flavour)
        if lines:
            return _payload(_card(
                str(entry.get("title") or topic_query),
                lines, flavour))
    # A named topic with no notes on file: ask kindly for
    # another chapter rather than dead-ending (and never a
    # "not found").
    return _payload(_plain("notes_req_ask", ln["ask"]))


__all__ = ["parse_notes_request", "handle_message"]
