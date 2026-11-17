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
as they arrive. (The client-side reveal other waves added
is a separate, purely cosmetic layer over finished
answers; this is the server transport underneath it.)

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

MERGE SEAM (for Wave 133, AI-answer verification — see the
feasibility section of ganitra-wave131-notes.md): this
module forwards a leg's pieces live, as they arrive. A
verification gate that must pass BEFORE an AI answer is
served cannot un-send pieces already shown, so when Wave
133 lands, stream_ai_events is where the reconciliation
belongs: buffer one leg's pieces here, verify the shaped
result, and only then release them (buffer-then-reveal).
Until that is built, the streamed path and Wave 133's
verification must not be enabled together.
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
    order and language rules, via fallback._ai_lang),
    forwarding each leg's pieces as they arrive.

    Yields event dicts:
    - {"type": "delta", "text": ...} — a piece of the
      current leg's reply, fit to show live;
    - {"type": "reset"} — the leg that produced the pieces
      on screen failed, truncated or missed, and the next
      leg is starting: the consumer clears its live text.
      A truncated leg's partial text is NEVER left standing
      as if it were the answer (the Wave-119 guard, applied
      to the stream).

    Returns, as the generator's return value, the shaped
    result dict of the first leg that finished cleanly with
    a usable answer — or None when every leg missed or
    failed, in which case the caller serves the honest
    fallback exactly as the classic chain does."""
    from fallback import _ai_lang
    from gemini_fallback import STREAM_RESET, \
        stream_gemini_answer
    from groq_fallback import stream_groq_answer
    from openrouter_fallback import stream_openrouter_answer

    ai_lang = _ai_lang(hindi, lang_request)
    legs = (
        (stream_gemini_answer, ai_lang),
        (stream_groq_answer, ai_lang),
        # Wave 108's rule, mirrored: the third leg takes the
        # plain Hindi flag, not the Wave-107 request object.
        (stream_openrouter_answer, "hi" if hindi else None),
    )
    shown = False
    for leg_fn, lang in legs:
        gen = leg_fn(question, lang)
        status, shaped = "error", None
        while True:
            try:
                item = next(gen)
            except StopIteration as stop:
                status, shaped = stop.value or ("error", None)
                break
            except Exception:
                status, shaped = "error", None
                break
            if item is STREAM_RESET:
                # The leg restarted itself (its next model):
                # what is on screen belongs to the old attempt.
                if shown:
                    yield {"type": "reset"}
                    shown = False
                continue
            shown = True
            yield {"type": "delta", "text": item}
        if status == "ok" and shaped is not None:
            return shaped
        # This leg produced nothing servable. If its pieces
        # reached the screen, clear them before the next leg
        # (or the honest fallback) replaces them.
        if shown:
            yield {"type": "reset"}
            shown = False
    return None


__all__ = ["stream_enabled", "sse_event", "stream_ai_events",
           "ENV_FLAG"]
