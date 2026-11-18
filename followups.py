"""Wave 122 — the conditional answer features' server half.

Suraj approved all four Wave-118 decision items on 17 Nov 2026
("Charo ko done karo or condition ke hisab se ans dena") — each
feature appears ONLY when its condition matches:

1. Streaming / typing reveal — client-side only (templates/
   index.html); nothing in this module.
2. Final-answer box — client adds the box class when
   ``is_solved_result`` (mirrored in the chat JS) is true.
3. Follow-up chips — the /api/solve payload gains a ``w122``
   field (see ``w122_payload``): the three chip labels in the
   ANSWER's language, present only under a solved maths
   answer. Tapping a chip POSTs /api/solve again with
   ``followup`` = the chip kind and ``context_question`` = the
   original question (HIDDEN context — the visible user bubble
   carries only the chip's own label); ``build_followup_response``
   below answers it deterministically from the session's last
   solution. No chips exist anywhere else: the home / empty
   state stays chip-free (Suraj's Wave-69 order stands — those
   were example-question chips, a different thing).
4. "Step 1 / Step 2" labels — the payload's ``w122.step_label``
   is the localised word ("Step" / "चरण"); the client numbers
   the solving lines only when a card shows 2+ of them. The
   removed overall "STEP-BY-STEP SOLUTION" heading (Wave 120)
   does NOT come back.

Wave 123 REVISION (Suraj, 17 Nov 2026, on seeing Wave 122's
screenshots): features 3 and 4 are ON-DEMAND now — default
OFF. "Step or niche more options hai aise nhi dene — agar
woh chat par bolta hai jabhi do, yaa jis type kaa question
hai us hisab se ans do, nhi toh simple plain rahane do."
So the payload also carries ``w122.labels`` (True only when
the student asked for steps — langdetect_local.
detect_steps_request — or the question is a proof /
derivation: ``is_proof_type``), and the chips are gated on
``detect_more_intent`` (the triggering message itself carries
more / continue intent), not on solved status alone. Answers
built by tapping a chip keep their chips (the caller passes
followup=True): a more-thread continues until the student
asks something plain again. Features 1 (reveal) and 2 (the
answer box) are unchanged from Wave 122.

Language flavour follows the answer, exactly like the rest of
the app: an explicit request (Wave 107) outranks the text,
Devanagari text is "dev" (Hindi labels), a Hindi session with
Roman text is "roman" (Hinglish labels), everything else "en".
"""

import re

from langdetect_local import detect_detail_request, \
    detect_steps_request

__all__ = ["is_solved_result", "flavour_for", "w122_payload",
           "build_followup_response", "FOLLOWUP_KINDS",
           "detect_more_intent", "is_proof_type",
           "parse_bare_view_request"]

FOLLOWUP_KINDS = ("example", "test", "simpler")

# Result kinds that are NOT a solved answer to the student's own
# question: the one-line replies (rendered plain, never reach
# the card), the concept / history / advice cards (real content,
# but not a solve), the step-check feedback card, and this
# wave's own test card. AI answers (gemini / groq / openrouter),
# bank hits, salvage, proofs and plain solver results carry
# other kinds (or none) and DO count as solved.
_NOT_SOLVED_KINDS = {
    "not_found", "concept", "history", "advice", "greeting",
    "nonmaths", "science", "vague", "gibberish", "guide",
    "similar", "step_check", "followup_test",
    # Wave 154: the guidance card and the small-talk line
    # are real content, not solves — no answer box, no
    # follow-up chips, exactly like history/advice.
    "guidance", "baat",
    # Wave 163: a guided-solve step turn is a plain teaching
    # bubble, never a solved card (its escape / completion
    # serve carries the real result and counts normally).
    "guided",
}
_NOT_SOLVED_OPS = {"error", "explain_step", "check_steps",
                   "not_found"}

STEP_LABELS = {"en": "Step", "roman": "Step", "dev": "चरण"}

CHIP_LABELS = {
    "en": {"example": "Give one more example",
           "test": "Give a small test on this topic",
           "simpler": "Explain more simply"},
    "dev": {"example": "एक और उदाहरण दो",
            "test": "इसी topic का छोटा test दो",
            "simpler": "और आसान में समझाओ"},
    "roman": {"example": "Ek aur example do",
              "test": "Isi topic ka chhota test do",
              "simpler": "Aur asaan me samjhao"},
}

_EXAMPLE_NOTES = {"en": "One more example:",
                  "roman": "Ek aur example:",
                  "dev": "एक और उदाहरण:"}
_SIMPLER_NOTES = {"en": "A simpler way:",
                  "roman": "Ek asaan tarika:",
                  "dev": "एक आसान तरीका:"}
_TEST_NOTES = {"en": "Small test — 3 questions on this topic:",
               "roman": "Chhota test — isi topic ke 3 sawal:",
               "dev": "छोटा test — इसी topic के 3 सवाल:"}
_TEST_LINES = {
    "en": "Tap the 💡 bulb below to check the answers.",
    "roman": "Jawab check karne ke liye neeche 💡 dabao.",
    "dev": "जवाब देखने के लिए नीचे 💡 दबाएँ।",
}
_KEY_HEADINGS = {"en": "Answer key", "roman": "Answer key",
                 "dev": "उत्तर कुंजी"}
_Q_PREFIXES = {"en": "Q{n}.", "roman": "Q{n}.",
               "dev": "प्रश्न {n}."}

_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def flavour_for(text, lang=None, lang_request=None):
    """The answer's language flavour: "en" / "dev" / "roman".

    An explicit language request (Wave 107) decides first;
    then the text's own script; a Hindi session answering in
    Roman script is Hinglish ("roman"); anything else is
    English."""
    if lang_request == "hi":
        return "dev"
    if lang_request == "hinglish":
        return "roman"
    if lang_request == "en":
        return "en"
    if text and _DEVANAGARI.search(str(text)):
        return "dev"
    if lang == "hi":
        return "roman"
    return "en"


def is_solved_result(result):
    """True when `result` is a solved maths answer carrying a
    distinct final answer — the ONE condition behind the
    Wave-122 answer box and the follow-up chips (the chat JS
    mirrors this predicate exactly)."""
    if not isinstance(result, dict):
        return False
    if not str(result.get("answer") or "").strip():
        return False
    if result.get("plain_reply") or result.get("plain"):
        return False
    if result.get("fallback_kind") in _NOT_SOLVED_KINDS:
        return False
    if result.get("op") in _NOT_SOLVED_OPS:
        return False
    return True


# ------------------------------------------------------------------
# Wave 123: the on-demand gates for features 3 and 4.
# ------------------------------------------------------------------

# More / continue intent — the words that make a message a
# "tell me more" ask rather than a plain question. The exact
# set (matched on the normalised text — lowercased, hyphens
# turned to spaces):
#   "example" / "examples", "udaharan" / "udahaaran" /
#     "udahran" / "udhaaran", "उदाहरण"
#   "test" — EXCEPT "divisibility test" (a maths topic, not
#     a request for a test)
#   "practice", "abhyas" / "abhyaas", "अभ्यास"
#   "samjhao" / "samjhaao" / "samjha", "समझाओ" / "समझाइए"
#   "explain" / "explanation"
#   "revise" / "revision"
#   "another", "dusra" / "doosra" / "dusri" / "doosri",
#     "दूसरा" / "दूसरी" / "दूसरे"
#   "more" — EXCEPT "more than" ("5 more than x" is content)
#   "aur" ONLY in compounds: "ek aur", or "aur" directly
#     before example / samjhao / batao / dikhao / chahiye /
#     ek. A bare "aur" is the Hinglish word for "and" —
#     "12 aur 18 ka HCF nikalo" is a plain question and must
#     NOT trigger (Suraj's tightness rule).
_MORE_PATTERNS = tuple(re.compile(p) for p in (
    r"\bexamples?\b",
    r"\btest\b",
    r"\bpractice\b",
    r"\bsamjhaa?o?\b",
    r"\bexplain\b",
    r"\bexplanation\b",
    r"\brevise\b",
    r"\brevision\b",
    r"\banother\b",
    r"\b(?:dusra|doosra|dusri|doosri)\b",
    r"\bek aur\b",
    r"\baur (?:example|samjhao|samjhaao|batao|dikhao|chahiye|ek)\b",
    r"\bmore\b(?!\s+than\b)",
))
_MORE_SUBSTRINGS = (
    "udaharan", "udahaaran", "udahran", "udhaaran",
    "abhyas", "abhyaas",
    "उदाहरण", "अभ्यास", "समझाओ", "समझाइए",
    "दूसरा", "दूसरी", "दूसरे",
)


def detect_more_intent(text):
    """Wave 123: True when the student's message itself asks
    for MORE — another example, a test, practice, a simpler
    explanation, a revision (see the exact set above). This
    gates the follow-up chips: a plain solved question earns
    no chips any more."""
    text = str(text or "")
    if not text.strip():
        return False
    for needle in _MORE_SUBSTRINGS:
        if needle in text:
            return True
    normalised = re.sub(r"\s+", " ",
                        text.lower().replace("-", " "))
    for pattern in _MORE_PATTERNS:
        if pattern.pattern == r"\btest\b":
            # "divisibility test" names a topic, not an ask.
            if re.search(r"(?<!divisibility )\btest\b",
                         normalised):
                return True
            continue
        if pattern.search(normalised):
            return True
    return False


# Proof / derivation signals in the question text — the same
# family the app's own proof layer vetoes on (solver/
# gaps103.py): prove / proof / siddh / सिद्ध / saabit /
# साबित, plus "show that" and the derive family.
_PROOF_TEXT = re.compile(
    r"\bprove[sd]?\b|\bproof\b|\bshow\s+that\b"
    r"|\bderiv(?:e|es|ed|ing|ations?)\b"
    r"|siddh|सिद्ध|saabit|साबित",
    re.I)


def is_proof_type(result, question=""):
    """Wave 123: True when this answer IS a proof / derivation
    — either the result came from the proof layer
    (fallback_kind "proof", ops like proof_irrational /
    proof_identity) or the question text itself carries a
    prove / show that / siddh karo / सिद्ध करो / derive
    signal. Proof answers carry step labels without being
    asked: a proof IS its steps (the big AIs structure proofs
    the same way)."""
    result = result or {}
    if result.get("fallback_kind") == "proof":
        return True
    if "proof" in str(result.get("op") or ""):
        return True
    return bool(_PROOF_TEXT.search(str(question or "")))


def w122_payload(result, lang=None, lang_request=None,
                 question="", ask_text=None, followup=False):
    """The ``w122`` field of an /api/solve response: the step
    label word for this answer's language, its flavour, the
    Wave-123 ``labels`` gate, and the follow-up chips.

    ``question`` is the text the flavour is read from (as in
    Wave 122). ``ask_text`` is the student's triggering
    message for the on-demand gates; it defaults to
    ``question``. ``followup`` is True when this answer was
    itself produced by a chip tap — a more-thread continues,
    so its chips stay.

    Wave 123 gates: ``labels`` is True only when the student
    asked for steps (detect_steps_request) or the answer is
    a proof / derivation (is_proof_type); the chips ride
    only on a solved answer whose ask carries more-intent
    (detect_more_intent) or that continues a chip thread."""
    result = result or {}
    text = " ".join([str(question or ""),
                     str(result.get("answer") or "")]
                    + [str(s) for s in (result.get("steps")
                                        or [])])
    flavour = flavour_for(text, lang=lang,
                          lang_request=lang_request)
    ask = str(ask_text if ask_text is not None
              else question or "")
    payload = {"step_label": STEP_LABELS[flavour],
               "flavour": flavour,
               # Wave 136 (Deploy-27 merge): an explicit
               # detail request also earns the labels — the
               # detailed version shows the working's
               # structure (see ganitra-wave136-notes.md).
               "labels": bool(detect_steps_request(ask)
                              or detect_detail_request(ask)
                              or is_proof_type(result, ask)),
               "chips": []}
    if is_solved_result(result) \
            and (followup or detect_more_intent(ask)):
        labels = CHIP_LABELS[flavour]
        payload["chips"] = [{"kind": kind, "label": labels[kind]}
                            for kind in FOLLOWUP_KINDS]
    return payload


# ------------------------------------------------------------------
# Follow-up builders. Each returns (result, note, advice, new_q)
# or None — None means "no honest follow-up", and the caller
# falls through to the normal solve path.
# ------------------------------------------------------------------

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def _perturbations(question):
    """Candidate re-asks of `question` with ONE number nudged —
    the raw material for a fresh worked example. Conservative:
    integer tokens only (plus a decimal fallback), never a
    year-like token, a fixed strategy order, each candidate
    different from the original."""
    tokens = [(m.start(), m.end(), m.group())
              for m in _NUMBER.finditer(question)]
    ints = []
    for start, end, text in tokens:
        if "." in text:
            continue
        value = int(text)
        if 1900 <= value <= 2100 or value < 1:
            continue
        ints.append((start, end, value))
    out = []

    def swap(tok, new_value):
        start, end, _ = tok
        cand = (question[:start] + str(new_value)
                + question[end:])
        if cand != question and cand not in out:
            out.append(cand)

    if ints:
        first, last = ints[0], ints[-1]
        swap(last, last[2] + 1)
        swap(last, last[2] + 2)
        swap(first, first[2] + 1)
        if last[2] * 2 <= 1000:
            swap(last, last[2] * 2)
        swap(first, first[2] + 10)
        if last[2] > 2:
            swap(last, last[2] - 1)
        if first[2] * 2 <= 1000:
            swap(first, first[2] * 2)
    else:
        for start, end, text in tokens:
            try:
                bumped = float(text) + 1
            except ValueError:
                continue
            rendered = (str(int(bumped)) if bumped == int(bumped)
                        else str(bumped))
            cand = question[:start] + rendered + question[end:]
            if cand != question and cand not in out:
                out.append(cand)
            break
    return out


def _example(context_question, lang):
    """A NEW worked example: nudge one number of the original
    question and re-solve it with the solver alone (no fallback
    layers, no AI — the example must be a verified solve)."""
    if not context_question:
        return None
    from i18n import solve_failed
    from solver.router import solve_question
    for candidate in _perturbations(context_question):
        try:
            result = solve_question(candidate)
        except Exception:
            continue
        if solve_failed(candidate, result):
            continue
        if not is_solved_result(result):
            continue
        result = dict(result)
        result["followup"] = "example"
        return result, candidate
    return None


_TEST_TOPIC_BY_OP = (
    ("probab", "probability"),
    ("area", "mensuration"), ("volume", "mensuration"),
    ("perimeter", "mensuration"), ("surface", "mensuration"),
)
_TEST_TOPIC_BY_TYPE = {"algebra": "algebra",
                       "geometry": "geometry",
                       "arithmetic": "arithmetic",
                       "applied": "arithmetic"}


def _test(context_question, prev_result, flavour,
          student_class):
    """A small 3-question practice test on the same topic,
    generated by the app's own verified practice generator
    (practice_gen — every answer correct by construction).
    The questions ride in the card's steps; the answer key
    rides in the Teacher's Advice (bulb), so the test is a
    test until the student chooses to check."""
    prev = prev_result or {}
    op = str(prev.get("op") or "").lower()
    topic = None
    for needle, mapped in _TEST_TOPIC_BY_OP:
        if needle in op:
            topic = mapped
            break
    if topic is None:
        topic = _TEST_TOPIC_BY_TYPE.get(
            str(prev.get("type") or "").lower(), "arithmetic")
    class_num = None
    try:
        class_num = int(str(student_class).strip())
    except (TypeError, ValueError):
        class_num = None
    if class_num not in (6, 7, 8, 9, 10):
        class_num = 8
    try:
        from practice_gen import generate_set
        seed = sum(ord(ch) for ch in (context_question or "test"))
        items = generate_set(class_num, topic, count=3, seed=seed)
    except Exception:
        return None
    if not items:
        return None
    prefix = _Q_PREFIXES[flavour]
    steps = [prefix.format(n=i + 1) + " " + str(item["question"])
             for i, item in enumerate(items)]
    key = _KEY_HEADINGS[flavour] + ": " + "; ".join(
        f"{i + 1}) {item['answer']}" for i, item in enumerate(items))
    result = {"type": "Ganitra", "op": "followup_test",
              "answer": _TEST_LINES[flavour], "steps": steps,
              "fallback": True, "fallback_kind": "followup_test",
              "followup": "test"}
    return result, key


def _simpler(prev_result, prev_question, flavour, lang):
    """A simpler take on the SAME answer, two honest routes:
    (1) a genuinely different alternate method that is no
    longer than the original working — served as a fresh
    solved card; (2) the doubt layer's plain-language
    re-explanation of the last working step. Never an invented
    simplification."""
    from doubt import build_doubt_response, eligible_result, \
        working_steps
    if not eligible_result(prev_result):
        return None
    prev_steps = working_steps(prev_result)
    try:
        from solver.methods import alternate_methods
        methods = alternate_methods(prev_question or "",
                                    prev_result)
    except Exception:
        methods = []
    for method in methods or []:
        steps = [str(s) for s in (method.get("steps") or [])
                 if str(s).strip()]
        if steps and len(steps) <= len(prev_steps):
            result = {"type": prev_result.get("type") or "Ganitra",
                      "op": prev_result.get("op") or "",
                      "answer": prev_result.get("answer")
                      or method.get("answer") or "",
                      "steps": steps, "followup": "simpler"}
            return result, _SIMPLER_NOTES[flavour], None
    built = build_doubt_response(
        CHIP_LABELS[flavour]["simpler"],
        {"index": None, "relative": "last", "op_hint": None},
        prev_result, lang=lang)
    if built is None:
        return None
    result, _index = built
    result = dict(result)
    result["followup"] = "simpler"
    return result, _SIMPLER_NOTES[flavour], None


def build_followup_response(kind, context_question, prev_result,
                            prev_question, lang=None,
                            student_class=None, lang_request=None):
    """Answer one follow-up chip tap.

    Returns (result, followup_note, advice_override, new_question)
    or None. `new_question` is set only for the example kind
    (the perturbed question that was actually solved) so the
    caller can make it the session's last solution; the other
    kinds leave the last solution pointing at the original
    answer. The flavour comes from the ORIGINAL question and
    answer — the language the chips were shown in."""
    if kind not in FOLLOWUP_KINDS:
        return None
    if not is_solved_result(prev_result):
        return None
    context_question = (context_question or prev_question
                        or "").strip()
    text = " ".join([context_question,
                     str(prev_result.get("answer") or "")]
                    + [str(s) for s in
                       (prev_result.get("steps") or [])])
    flavour = flavour_for(text, lang=lang,
                          lang_request=lang_request)
    if kind == "example":
        built = _example(context_question, lang)
        if built is None:
            return None
        result, new_question = built
        return result, _EXAMPLE_NOTES[flavour], None, new_question
    if kind == "test":
        built = _test(context_question, prev_result, flavour,
                      student_class)
        if built is None:
            return None
        result, key = built
        return result, _TEST_NOTES[flavour], key, None
    built = _simpler(prev_result, prev_question or context_question,
                     flavour, lang)
    if built is None:
        return None
    result, note, _unused = built
    return result, note, None, None


# ------------------------------------------------------------------
# Wave 148: a BARE view request — "step by step batao" /
# "detail me batao" / "vistar se samjhao" sent ALONE, as its
# own message, right after an answer.
#
# Wave 123 put the labels on the ANSWER THE MESSAGE CARRIES;
# a bare request carries no question, so it fell through to
# the new-question path and earned an AI-fallback "please
# write your question in a complete sentence" — the student
# never got the stepped version of the answer sitting right
# above (live check, Deploy-28). The design intent is that
# an explicit step/detail request applies to the LAST
# answer in the chat; api_solve now re-serves that stored
# answer when this detector fires (labels via the w122 ask
# gate for a steps ask, the Wave-136 expansion for a detail
# ask).
#
# BARE is the whole discipline: the message must consist of
# ONLY a steps/detail request phrase plus filler (address
# and ask words). Any digit, "=" or "%", and any leftover
# content word (a topic, a number, a new question) makes it
# a question+request message — "12 aur 18 ka HCF step by
# step batao", "HCF detail me batao hindi me" — which keeps
# its ordinary Wave-123/136 path byte-for-byte. The fire
# decision itself reuses the Wave-123/136 detectors, so the
# phrase families can never drift apart.
# ------------------------------------------------------------------

_VIEW_STEP_REMOVALS = tuple(re.compile(p) for p in (
    r"step by step",
    r"\bstepwise\b",
    r"\bstep karke\b",
    r"\bek ek step\b",
    r"\b(?:saare|sare|sab|har|each|all) steps?\b",
    r"\bsteps? (?:me|mein|mai|se) "
    r"(?:batao|samjhao|samjhaao|dikhao|chahiye|do)\b",
    r"\bsteps? (?:batao|samjhao|samjhaao|dikhao|chahiye)\b",
    r"\bwith steps\b",
    r"\bsteps? ke saath\b",
    r"\bshow (?:me )?(?:all )?(?:the )?steps\b",
))
_VIEW_DETAIL_REMOVALS = tuple(re.compile(p) for p in (
    r"\bin detail\b",
    r"\bdetailed (?:answer|solution|explanation|working)\b",
    r"\bdetail (?:me|mein|mai|se) "
    r"(?:batao|samjhao|samjhaao|dikhao|chahiye|do|samjha)\b",
    r"\bdetailme (?:batao|samjhao|samjhaao|dikhao|chahiye|do)\b",
    r"\bdetail (?:batao|samjhao|samjhaao|dikhao|chahiye)\b",
    r"\bvistar se\b",
    r"\bvistaar se\b",
    r"\blamba (?:answer|jawab|solution)\b",
    r"\blong (?:answer|explanation|solution)\b",
    r"\bfull (?:solution|answer|explanation)\b",
    r"\bpoora (?:samjhao|samjha|batao|answer|jawab|solution)\b",
    r"\bpoori detail\b",
    r"\bexplain fully\b",
))
_VIEW_DEV_PHRASES = (
    "स्टेप बाय स्टेप", "चरण दर चरण",
    "क्रम से समझाओ", "क्रम से बताओ", "क्रम से बताइए",
    "विस्तार से", "विस्तार में", "विस्तारपूर्वक", "विस्तृत",
    "डिटेल में", "डिटेल से", "डिटेल बताओ", "डिटेल समझाओ",
    "लंबा उत्तर", "लम्बा उत्तर", "लंबा जवाब",
)
_VIEW_FILLER = {
    # Latin ask / address / glue words — never content.
    "batao", "bata", "bataao", "samjhao", "samjhaao",
    "samjha", "do", "dikhao", "chahiye", "please", "plz",
    "me", "mein", "mai", "se", "ko", "ke", "ka", "ki",
    "the", "a", "an", "ye", "yeh", "is", "wala", "wale",
    "aur", "or", "and", "bhi", "hi", "ek", "baar", "phir",
    "dobara", "again", "ab", "zara", "tum", "mujhe",
    "mere", "liye",
    # The request families' own nouns/heads: a leftover one
    # ("step", "detail", "full") is still just the request.
    "step", "steps", "detail", "vistar", "vistaar",
    "lamba", "full", "poora", "poori", "long", "answer",
    "jawab", "solution", "explanation", "working", "in",
    "with", "show", "all", "each", "har", "sab", "saare",
    "sare", "karke", "saath",
    # Devanagari equivalents.
    "बताओ", "बताइए", "समझाओ", "समझाइए", "में", "से", "दो",
    "दीजिए", "चरण", "दर", "स्टेप", "बाय", "विस्तार",
    "लंबा", "लम्बा", "उत्तर", "जवाब", "डिटेल", "विस्तृत",
    "क्रम", "पूर्वक",
}


def parse_bare_view_request(text):
    """Classify a message that is ONLY a view request.

    Returns "detail" for a bare detail ask ("detail me
    batao", "vistar se samjhao", "डिटेल में बताओ"), "steps"
    for a bare steps ask ("step by step batao", "steps me
    batao", "स्टेप बाय स्टेप बताओ"), else None. A detail
    ask outranks a steps ask when both ride in one bare
    message — the detailed version carries the labels too
    (the Wave-136 w122 gate)."""
    raw = str(text or "")
    if not raw.strip():
        return None
    wants_detail = detect_detail_request(raw)
    wants_steps = detect_steps_request(raw)
    if not (wants_detail or wants_steps):
        return None
    # A digit, "=" or "%" is question payload — the message
    # is a question WITH a request, never a bare request.
    if any(ch.isdigit() for ch in raw) \
            or "=" in raw or "%" in raw:
        return None
    cleaned = raw
    for phrase in _VIEW_DEV_PHRASES:
        cleaned = cleaned.replace(phrase, " ")
    normalised = re.sub(r"\s+", " ",
                        cleaned.lower().replace("-", " "))
    for pattern in _VIEW_STEP_REMOVALS + _VIEW_DETAIL_REMOVALS:
        normalised = pattern.sub(" ", normalised)
    words = [w for w in re.split(r"[\s.,;:!?\"'()।/]+",
                                  normalised) if w]
    if any(w not in _VIEW_FILLER for w in words):
        return None
    return "detail" if wants_detail else "steps"
