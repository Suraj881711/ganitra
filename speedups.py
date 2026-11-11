"""Wave 14 (speed): the auto-teach payload can never block an answer.

What "learning" happens per chat request in Ganitra (audited in
Wave 14 across api.py / app.py / solver/):

1. The primary solve itself — the answer; obviously synchronous.
2. The AUTO-TEACH payload: for every successful answer the app
   automatically computes the Wave-12/13 extras — genuinely
   different alternate methods (``solver.methods.alternate_methods``)
   plus the "Teach me" concept lines. The teach lines are a plain
   i18n dict lookup (microseconds). The alternate methods are real
   extra compute — parsing + occasional extra sympy solves — and
   they used to run inline, so a slow methods pass delayed the
   answer bubble itself.
3. Persistence of the thread: NOT part of the solve request at
   all. The browser saves the thread with its own debounced,
   fire-and-forget PUT /api/chats/<id> (errors swallowed client
   side), so saving can never block an answer either.

The alternate-methods list is part of the /api/solve RESPONSE
contract (Wave 12: the chips render with the answer, and saved
chats store the whole payload to re-render identically), so it
cannot simply be dropped from the response. Instead it is now
computed on a background daemon thread with a hard time budget:
in every normal case the computation finishes well inside the
budget and the response carries exactly the same data as before;
if it ever overruns, the answer goes out WITHOUT the extra
methods (logged) instead of being held hostage. Errors inside
the computation are swallowed + logged — alternate_methods
already never raises, this is belt and braces.
"""

import logging
import threading

from solver.methods import alternate_methods

log = logging.getLogger("ganitra.speedups")

# Generous next to the real cost (a warm alternate-methods pass
# is tens of milliseconds; see verify_wave14's measurements),
# small next to a student's patience for the answer bubble.
METHODS_BUDGET_SECONDS = 2.5


def methods_nonblocking(question, primary_result,
                        budget=METHODS_BUDGET_SECONDS):
    """alternate_methods() with a hard wall-clock budget.

    Returns exactly what alternate_methods returns when it
    finishes inside the budget (the normal case); returns []
    when it overruns or blows up — the primary answer is never
    delayed by the teach extras.
    """
    box = {}

    def _run():
        try:
            box["methods"] = alternate_methods(question,
                                               primary_result)
        except Exception:  # never propagate, never block
            log.exception("auto-teach methods computation failed")
            box["methods"] = []

    worker = threading.Thread(target=_run, daemon=True,
                              name="ganitra-auto-teach")
    worker.start()
    worker.join(budget)
    if worker.is_alive():
        log.warning(
            "auto-teach methods exceeded %.1fs budget for %r; "
            "answering without the extra methods",
            budget, str(question)[:80])
        return []
    return box.get("methods", [])
