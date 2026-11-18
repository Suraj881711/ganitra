"""Wave 136 — DETAIL ON DEMAND (Suraj's LAMBA ANSWER RULE).

Suraj's standing rule (17 Nov 2026): Ganitra's answers stay
SHORT by default. ONLY when the student explicitly asks for
a long / detailed answer — "detail me samjhao", "vistar se
batao", "lamba answer chahiye", "explain in detail" — does
the SAME answer come in a detailed version: the reason
behind the working plus one example. Never long without
being asked.

This module is the server-side expansion half. The intent
detector itself lives with the other request detectors
(langdetect_local.detect_detail_request, mirroring Wave
107's language-request and Wave 123's steps-request
detectors). api.py detects the intent on the student's
original message and threads a `detail` flag through
_solve_friendly -> fallback.with_fallback (where it selects
the AI legs' DETAIL prompt variant — see gemini_fallback)
and, for the deterministic answers, into expand_detail
below, which appends honest detail built ONLY from
Ganitra's own material:

- SOLVER answers (plain solver, bank, live bank, salvage,
  MCQ / format / proof-upgrade solves — anything
  _is_solved_result accepts, proofs excluded): the topic's
  formula + why block from the curated concept layer
  (concepts.find_concept — the same entries the concept
  card serves, in the same words), then ONE worked example
  of the same question type: one number of the student's
  own question nudged and re-solved with the solver alone,
  accepted only when it really solves AND its answer
  differs from the original (the Wave 127 regeneration
  discipline). When neither exists, the answer is served
  exactly as it was — a reason or an example is NEVER
  invented. Per-step reasons are not fabricated either:
  the solver's steps carry no reason text, so the "why"
  Ganitra can honestly add is the topic's own formula /
  concept block (for AI answers the detail prompt asks the
  model itself for a short reason per step instead).
- CONCEPT answers: the card already carries its worked
  example by construction, so the detail delta is a small
  practice set for the same topic from the verified
  practice generator (practice_gen — answers correct by
  construction), appended only when the topic maps
  confidently onto a practice topic; otherwise the card is
  served as-is.
- AI answers (gemini / groq / openrouter): NOT expanded
  here — they are detailed at the source by the detail
  prompt variant, and the normal shaping path stays in
  charge of the result.
- Everything else (the one-line replies — not-found,
  greeting, non-maths, science, vague — history / advice
  cards, step-check cards, proofs): served exactly as-is.
  A proof IS its own why; the one-liners stay one line
  even when the student asked for detail (there is no
  solved answer to detail).

Language: the appended headings follow the answer's
flavour (en / roman / dev) with Wave 107's rule — an
explicit language request outranks the question's text.
The block BODIES are Ganitra's own stored text, in the
same form the concept card itself serves them (English
explain + the Hinglish line), because that is the only
honest text the app has for them.

MERGE SEAMS (Deploy-26/27, Waves 122/123/127/132):
- followups.py (Wave 122/123) owns is_solved_result and
  flavour_for; this tree carried deliberate mirrors (same
  sets, same rules) because followups.py was not in it.
  DONE at the Deploy-27 merge: the mirrors are deleted and
  both predicates are imported from followups.
- Step labels: Wave 123's w122 gate computes labels from
  detect_steps_request / is_proof_type. A detail request
  is also a steps request (Suraj's detail version shows
  the working's structure), so at the merge the labels
  condition gains one disjunct: `or
  detect_detail_request(ask)`. Nothing in this tree
  renders labels (the w122 payload lands with Deploy-26),
  so the gate change is recorded here and in the wave
  notes rather than faked in this tree.
- Wave 132's house prompt: the detail variant is a
  {detail_block} placeholder appended after {lang_line}
  in gemini_fallback._PROMPT, so Wave 132's rewritten
  prompt takes the same one-line placeholder and the
  detail rules ride along unchanged.
"""

import re

from concepts import find_concept
from followups import flavour_for as _flavour_for
from followups import is_solved_result as _is_solved_result
from i18n import solve_failed
from solver.router import solve_question

__all__ = ["expand_detail"]

_AI_KINDS = ("gemini", "groq", "openrouter")

# Deploy-27 merge: the Wave-122 predicates this module used
# to mirror (see the docstring's merge seams) are now
# imported from followups.py, their single owner — the
# underscore aliases keep the call sites below unchanged.


# ------------------------------------------------------------------
# The "kyon" block — the topic's formula + why, from the
# curated concept layer, in the concept card's own words.
# ------------------------------------------------------------------

_WHY_HEADINGS = {
    "en": "Why this works:",
    "roman": "Ye aise kyon hota hai:",
    "dev": "यह ऐसे क्यों होता है:",
}
_FORMULA_LABELS = {"en": "Formula:", "roman": "Formula:",
                   "dev": "सूत्र:"}


def _kyon_block(question, flavour):
    """The matched concept entry's formula + explain lines,
    or [] when the concept layer has no entry for this
    question's topic. The entry text is served exactly as
    stored (the concept card serves the same words); only
    the heading and the formula label follow the flavour.
    For roman / dev flavours the entry's Hinglish line is
    appended too — the same extra line the concept card
    itself serves for those students."""
    try:
        entry = find_concept(question)
    except Exception:
        return []
    if not entry:
        return []
    lines = [_WHY_HEADINGS[flavour]]
    formula = str(entry.get("formula") or "").strip()
    if formula:
        lines.append(f"{_FORMULA_LABELS[flavour]} {formula}")
    explain = str(entry.get("explain") or "").strip()
    if explain:
        lines.append(explain)
    if flavour in ("roman", "dev"):
        hinglish = str(entry.get("hinglish") or "").strip()
        if hinglish:
            lines.append(f"Hinglish me: {hinglish}")
    return lines if len(lines) > 1 else []


# ------------------------------------------------------------------
# One worked example — the Wave 127 regeneration discipline:
# nudge ONE number of the student's own question, re-solve
# with the solver alone, accept only a real solve whose
# answer DIFFERS from the original.
# ------------------------------------------------------------------

_EXAMPLE_HEADINGS = {
    "en": "One more example:",
    "roman": "Ek aur example:",
    "dev": "एक और उदाहरण:",
}


def _nudged_questions(question):
    """`question` with ONE number nudged, in a deterministic
    try-order (last number first; +1, +2, -1, +5, x2) —
    mirrored from context_ref._nudged_questions (Wave 127).
    Only plain integers/decimals in the text are nudged;
    the wording is otherwise byte-identical."""
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


def _example_block(question, original_answer, flavour):
    """One verified worked example of the same question
    type, as step lines, or [] when no nudged variant
    honestly solves with a different answer."""
    if not question:
        return []
    for candidate in _nudged_questions(question):
        try:
            fresh = solve_question(candidate)
        except Exception:
            continue
        if solve_failed(candidate, fresh):
            continue
        if not _is_solved_result(fresh):
            continue
        if str(fresh.get("answer", "")).strip() \
                == str(original_answer or "").strip():
            continue  # same answer — not a new example
        lines = [_EXAMPLE_HEADINGS[flavour], candidate]
        lines.extend(str(s) for s in (fresh.get("steps")
                                      or []))
        lines.append(
            f"Example answer: {fresh.get('answer', '')}")
        return lines
    return []


# ------------------------------------------------------------------
# Concept answers: a small practice set on the same topic,
# from the verified practice generator (answers correct by
# construction), only on a confident topic mapping.
# ------------------------------------------------------------------

_PRACTICE_HEADINGS = {
    "en": "Practice — try these yourself:",
    "roman": "Abhyas — ye sawal khud karke dekho:",
    "dev": "अभ्यास — ये सवाल खुद करके देखो:",
}
_PRACTICE_KEYS = {"en": "Answers:", "roman": "Jawab:",
                  "dev": "उत्तर:"}
_Q_PREFIXES = {"en": "Q{n}.", "roman": "Q{n}.",
               "dev": "प्रश्न {n}."}

# Confident keyword -> practice_gen topic mapping (the
# followups._test mapping, widened with the concept layer's
# own vocabulary). No hit -> no practice block: a
# wrong-topic practice set is worse than none. Order is
# specific-before-general: "hcf" / "lcm" must win over the
# "factor" in "prime factorisation" (an HCF concept's own
# text), and bare "factor" maps nowhere — factorisation
# spans arithmetic and algebra alike.
_PRACTICE_BY_KEYWORD = (
    ("probab", "probability"),
    ("hcf", "arithmetic"), ("lcm", "arithmetic"),
    ("gcd", "arithmetic"),
    ("area", "mensuration"), ("volume", "mensuration"),
    ("perimeter", "mensuration"), ("surface", "mensuration"),
    ("circle", "mensuration"), ("mensuration", "mensuration"),
    ("quadratic", "algebra"), ("equation", "algebra"),
    ("polynomial", "algebra"), ("algebra", "algebra"),
    ("triangle", "geometry"), ("angle", "geometry"),
    ("pythagor", "geometry"), ("geometry", "geometry"),
)


def _practice_block(result, flavour):
    """Up to 3 generated practice questions on the concept
    answer's topic (+ the answer key as the last line), or
    [] when the topic does not map confidently or the
    generator cannot serve it."""
    haystack = " ".join([
        str(result.get("answer") or ""),
        str(result.get("concept_id") or ""),
        str(result.get("topic_slug") or ""),
        str(result.get("op") or ""),
    ]).lower()
    topic = None
    for needle, mapped in _PRACTICE_BY_KEYWORD:
        if needle in haystack:
            topic = mapped
            break
    if topic is None:
        return []
    class_num = result.get("topic_class")
    if class_num not in (6, 7, 8, 9, 10):
        class_num = 8
    try:
        from practice_gen import generate_set
        seed = sum(ord(ch) for ch in
                   (str(result.get("concept_id") or "")
                    + str(result.get("answer") or "")))
        items = generate_set(class_num, topic, count=3,
                             seed=seed)
    except Exception:
        return []
    if not items:
        return []
    prefix = _Q_PREFIXES[flavour]
    lines = [_PRACTICE_HEADINGS[flavour]]
    lines.extend(
        prefix.format(n=i + 1) + " " + str(item["question"])
        for i, item in enumerate(items))
    lines.append(_PRACTICE_KEYS[flavour] + " " + "; ".join(
        f"{i + 1}) {item['answer']}"
        for i, item in enumerate(items)))
    return lines


def _guidance_block(result, flavour):
    """Wave 154: the DETAIL lines of the guidance card's
    own entry, in the card's flavour — or [] when the
    result carries no guidance id or the entry has no
    detail lines. guidance.py owns the content; this is
    only the lookup."""
    gid = result.get("guidance_id")
    if not gid:
        return []
    # The card's own stamped flavour wins: a bare "detail
    # me batao" follow-up carries no language of its own,
    # and the expansion must speak the card's language.
    flavour = result.get("guidance_flavour") or flavour
    try:
        from guidance import guidance_detail_steps
        return guidance_detail_steps(gid, flavour)
    except Exception:
        return []


# ------------------------------------------------------------------
# The entry point api.py calls (only when a detail request
# was detected — with no request this function is never
# called and every answer is byte-identical to before).
# ------------------------------------------------------------------

def expand_detail(question, result, lang=None,
                  lang_request=None):
    """Return the DETAILED version of `result` — an expanded
    COPY; the input dict is never mutated — or `result`
    itself, unchanged, when nothing honest can be added
    (see the module docstring for what expands and what
    never does)."""
    if not isinstance(result, dict):
        return result
    kind = result.get("fallback_kind")
    if result.get("ai_generated") or kind in _AI_KINDS:
        # Detailed at the source by the detail prompt
        # variant; the normal shaping path stays in charge.
        return result
    flavour = _flavour_for(question, lang, lang_request)
    if kind == "concept":
        block = _practice_block(result, flavour)
        if not block:
            return result
        expanded = dict(result)
        expanded["steps"] = [str(s) for s in
                             (result.get("steps") or [])] \
            + block
        return expanded
    if kind == "guidance":
        # Wave 154: a guidance card expands with its own
        # authored DETAIL lines (guidance.py owns the
        # content; the short card is the default and the
        # detail lines exist only for this ask — the
        # Wave 136 rule). No detail lines -> the card
        # itself, unchanged.
        block = _guidance_block(result, flavour)
        if not block:
            return result
        expanded = dict(result)
        expanded["steps"] = [str(s) for s in
                             (result.get("steps") or [])] \
            + block
        return expanded
    if kind == "proof" or not _is_solved_result(result):
        return result
    block = _kyon_block(question, flavour)
    block += _example_block(question, result.get("answer"),
                            flavour)
    if not block:
        return result
    expanded = dict(result)
    expanded["steps"] = [str(s) for s in
                         (result.get("steps") or [])] + block
    return expanded
