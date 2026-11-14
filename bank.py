"""Wave 39: the Verified Data Bank — exact-match answer layer.

The data bank (~/workspace/ganitra-databank/, PLAN.md step 1)
stores maths questions whose answers were independently
recomputed with SymPy before banking — Gemini/Muse wrote the
items, but no item is served on the generator's word alone.
This module ships a static snapshot of that bank with the app
(bank_data.jsonl, app root) and answers a chat question from it
when — and only when — the question is an EXACT match after
normalisation.

Match rule (deliberately strict; a wrong match is worse than a
miss, so there is NO fuzzy/similarity matching in this wave):

  normalise = NFC + lowercase + Devanagari digits -> ASCII +
              every punctuation/symbol character -> a space +
              whitespace collapsed.

Punctuation is stripped by Unicode category (P*/S* -> space),
NOT by a \\w regex: \\w does not match Devanagari combining marks
(matras, virama, anusvara), so a \\w-based strip would shred
Hindi text. Categories keep letters (L*), marks (M*) and
numbers (N*) intact, so Hindi questions survive whole.

Two indexes are built once at import:
  * class-agnostic:  normalised question -> item
  * class-aware:     (class, normalised question) -> item
lookup() prefers the class-aware hit when a class is supplied
and falls back to the class-agnostic one, so the same question
banked under Class 10 still serves a Class 6 student who typed
it word for word.

A missing or unreadable bank_data.jsonl is NOT an error: the
bank is simply empty and every lookup misses, leaving the
solver/fallback flow exactly as it was before this wave.
"""
import json
import os
import re
import unicodedata

_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "bank_data.jsonl")

_SPACES = re.compile(r"\s+")
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def normalise_question(text):
    """The one normalisation used for BOTH indexing bank items
    and looking a student's question up — the two sides must
    agree character for character or nothing would ever match."""
    text = unicodedata.normalize("NFC", str(text or ""))
    text = text.translate(_DEVANAGARI_DIGITS)
    text = text.lower()
    text = "".join(
        " " if unicodedata.category(ch)[0] in ("P", "S") else ch
        for ch in text)
    return _SPACES.sub(" ", text).strip()


def _load(path):
    """Read a bank snapshot into (by_question, by_class) index
    dicts. Tolerant by design: a missing file, a bad line or a
    record without a usable question is skipped, never raised —
    a broken bank must not break the app."""
    by_question = {}
    by_class = {}
    try:
        fh = open(path, encoding="utf-8")
    except OSError:
        return by_question, by_class
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except ValueError:
                continue
            if not isinstance(item, dict):
                continue
            question = item.get("question")
            if not isinstance(question, str):
                continue
            norm = normalise_question(question)
            if not norm:
                continue
            # First record wins on a duplicate key: the bank is
            # deduped upstream by the same normalisation, so a
            # collision here means two records for one question
            # and either is a verified answer.
            by_question.setdefault(norm, item)
            try:
                cls = int(item.get("class"))
            except (TypeError, ValueError):
                continue
            by_class.setdefault((cls, norm), item)
    return by_question, by_class


_BY_QUESTION, _BY_CLASS = _load(_BANK_PATH)


def bank_size():
    """How many distinct questions the loaded snapshot can
    answer (0 when the snapshot file is missing)."""
    return len(_BY_QUESTION)


def lookup(question, student_class=None):
    """The banked item for this EXACT question, or None.

    With `student_class`, a same-class record is preferred; the
    class-agnostic index is the fallback, so a question banked
    under another class still hits."""
    norm = normalise_question(question)
    if not norm:
        return None
    if student_class is not None:
        try:
            cls = int(student_class)
        except (TypeError, ValueError):
            cls = None
        if cls is not None:
            item = _BY_CLASS.get((cls, norm))
            if item is not None:
                return item
    return _BY_QUESTION.get(norm)


def bank_result(item):
    """Shape a bank item EXACTLY like a solver/fallback result
    dict ({type, op, answer, steps, ...}) so every existing
    renderer — chat bubble, answer page, print, history — works
    unchanged. The bank records already follow the Wave 24 house
    style (plain solving lines; the final answer as a normal
    line), so steps and final_answer are served verbatim.

    Honesty flags mirror the Wave 18/37 convention: the result
    is marked fallback/fallback_kind="bank" + source="bank",
    and verified=True records that the answer was independently
    SymPy-recomputed before banking."""
    return {
        "type": "Ganitra",
        "op": "bank",
        "answer": str(item.get("final_answer", "") or "").strip(),
        "steps": [str(s) for s in (item.get("steps") or [])],
        "fallback": True,
        "fallback_kind": "bank",
        "source": "bank",
        "verified": True,
        "bank_id": item.get("id"),
    }


def lookup_result(question, student_class=None):
    """lookup() + bank_result(): the ready-to-serve result dict
    for an exact hit, else None."""
    item = lookup(question, student_class)
    return bank_result(item) if item is not None else None


__all__ = ["normalise_question", "lookup", "lookup_result",
           "bank_result", "bank_size"]
