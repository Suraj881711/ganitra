"""Wave 131: REAL streaming for the AI fallback leg —
transport only.

The big AIs stream their answers token-by-token; Ganitra's
answers arrived in one block because the whole chain ran
inside one request/response. This module streams the one
leg where streaming is real: the AI fallback (Gemini →
Groq → OpenRouter), whose provider waits last seconds. The
deterministic solver answers in ~0.13 s median (Wave 97) —
there is nothing to stream there, and this module never
touches it.

What this module is NOT: it does not change what is
answered. The prompt, the reply shaping and the Wave-119
truncation guard all live in the provider modules and are
shared with the non-streamed path — a streamed answer is
assembled from the provider's own pieces and shaped by the
very same code, so the final result dict is byte-identical
to the one the classic chain would have produced for the
same reply text. Nor is anything here simulated: the pieces
yielded are the provider's own streamed output, forwarded
verbatim — since Wave 231, forwarded after the
verification gate has passed the leg they belong to (see
the merge-seam note below), not as they arrive. (The
client-side reveal other waves added is a separate,
purely cosmetic layer over finished answers; this is the
server transport underneath it.)

Feasibility (full evidence in ganitra-wave131-notes.md):
progressive flushing is PROVEN on the local Flask/Werkzeug
stack; PythonAnywhere's own Buffering help page documents
the mechanism that makes it work through their nginx
layers — the header `X-Accel-Buffering: no` plus
newline-terminated yields, both of which the endpoint in
api.py follows — but whether PA's free tier honours it
end-to-end for this app is UNVERIFIED until a live deploy
tests it. The whole feature therefore sits behind the
GANITRA_AI_STREAM environment flag, default OFF: with the
flag unset, nothing in the app behaves any differently.

MERGE SEAM — CLOSED by Wave 231 (BUG-009). Wave 133's
verification gate (aiverify.verify_chain, the Wave 226
fail-closed gate) landed after this module, and for a while
the streamed path bypassed it: pieces reached the screen
token-by-token, and a gate that must pass BEFORE an answer
is served cannot un-send pieces already shown. The
reconciliation the Wave 131 note prescribed is now built:
stream_ai_events BUFFERS each leg's pieces (nothing is
yielded while a leg runs), hands the shaped results to the
very same verify_chain the classic path uses, and only
then REVEALS the winning leg's buffered pieces, in order,
as the delta events the client already renders. A leg the
gate rejects reveals nothing; when nothing verifies, no
delta is emitted at all and the caller serves the honest
fallback, exactly as the classic chain does. The flag
stays OFF (enabling it is Suraj's call) — what changed is
that the code path behind it is now safe by design.
"""
import json
import os

ENV_FLAG = "GANITRA_AI_STREAM"


def stream_enabled():
    """The one switch: GANITRA_AI_STREAM=1 in the
    environment (set in the PythonAnywhere WSGI file, the
    same pattern as the AI keys). Anything else — unset,
    empty, any other value — is OFF."""
    return os.environ.get(ENV_FLAG, "").strip() == "1"


def sse_event(event):
    """One Server-Sent Events frame for an event dict. The
    trailing blank line is load-bearing twice over: it is
    the SSE frame terminator, and PythonAnywhere's Buffering
    guidance requires every yielded string to end with a
    newline for its proxies to flush instead of buffer."""
    return "data: " + json.dumps(event, ensure_ascii=False) \
        + "\n\n"


def stream_ai_events(question, hindi, lang_request=None):
    """Drive the three AI legs in the classic chain's order
    (Gemini, then Groq, then OpenRouter — fallback.py's
    order and language rules, via fallback._ai_lang) behind
    the Wave 133/226 verification gate, buffer-then-reveal
    (Wave 231, BUG-009).

    Each leg's stream is DRAINED into a buffer — a leg's
    STREAM_RESET simply restarts its own buffer, since
    nothing has been shown yet — and its shaped result goes
    to aiverify.verify_chain as that leg's candidate, in
    exactly the callable shape the classic path's
    _verified_ai_answer hands the same gate. verify_chain
    decides what may be served (sanity, deterministic check,
    cross-leg consensus; fail-closed on its own errors).
    Only the WINNING leg's buffered pieces are then yielded,
    in order, as {"type": "delta", "text": ...} events —
    the same events, in the same order, the pre-gate stream
    produced for that leg, so the client renders identically;
    they simply arrive after verification instead of before
    it. No {"type": "reset"} is ever needed: nothing
    unverified is ever on screen to clear (the Wave-119
    truncation guard is subsumed — a truncated leg shapes
    to None and never becomes a candidate).

    Returns, as the generator's return value, the verified
    result dict (verify_chain's own, marks included — the
    same dict the classic path serves) — or None when every
    leg missed, failed or was rejected, in which case the
    caller serves the honest fallback exactly as the classic
    chain does. Never raises."""
    from fallback import _ai_lang
    from gemini_fallback import STREAM_RESET, \
        stream_gemini_answer
    from groq_fallback import stream_groq_answer
    from openrouter_fallback import stream_openrouter_answer

    ai_lang = _ai_lang(hindi, lang_request)
    stream_legs = (
        ("gemini", stream_gemini_answer, ai_lang),
        ("groq", stream_groq_answer, ai_lang),
        # Wave 108's rule, mirrored: the third leg takes the
        # plain Hindi flag, not the Wave-107 request object.
        ("openrouter", stream_openrouter_answer,
         "hi" if hindi else None),
    )
    buffered = {}

    def _drain(name, leg_fn, lang):
        """A verify_chain leg callable: run one leg's stream
        to completion, buffering its pieces, and return its
        shaped result (or None) — the gate's own contract."""
        def call():
            pieces = []
            status, shaped = "error", None
            try:
                gen = leg_fn(question, lang)
                while True:
                    try:
                        item = next(gen)
                    except StopIteration as stop:
                        status, shaped = stop.value or (
                            "error", None)
                        break
                    if item is STREAM_RESET:
                        # The leg restarted itself (its next
                        # model): the buffer belongs to the old
                        # attempt. Nothing was ever shown, so
                        # the restart is a plain buffer clear.
                        pieces = []
                        continue
                    pieces.append(item)
            except Exception:
                status, shaped = "error", None
            if status == "ok" and shaped is not None:
                buffered[name] = (pieces, shaped)
                return shaped
            buffered[name] = (pieces, None)
            return None
        return call

    legs = [(name, _drain(name, leg_fn, lang))
            for name, leg_fn, lang in stream_legs]
    try:
        from aiverify import verify_chain
        winner = verify_chain(question, legs)
    except Exception:
        # The gate could not even be imported/run: NOT
        # verified (the classic path's Wave 226 fail-closed
        # rule) — serve nothing from the legs.
        winner = None
    if winner is None:
        return None
    # Reveal: identify the winning leg by its own result —
    # verify_chain returns the leg's dict, marked with its
    # ai_verification keys when it marks at all; strip those
    # and compare with the buffered candidates.
    stripped = {k: v for k, v in winner.items()
                if k not in ("ai_verification",
                             "ai_verify_check")}
    for _name, (pieces, shaped) in buffered.items():
        if shaped is not None and shaped == stripped:
            for piece in pieces:
                yield {"type": "delta", "text": piece}
            break
    return winner


__all__ = ["stream_enabled", "sse_event", "stream_ai_events",
           "ENV_FLAG"]
