from flask import Blueprint, request, jsonify, session
from i18n import (advice_for, explanation_for, get_strings,
                  normalise_lang, result_unsolvable, solve_failed)
from solver.router import solve_question

api_bp = Blueprint("api", __name__)

_HISTORY_LIMIT = 30
_QUESTION_LIMIT = 500


def _solve_friendly(question):
    """Wave 5b: solve, and on failure gently re-ask once with a hint
    appended (same behaviour as the classic /solve route), so the
    chat never shows a raw solver failure when a small nudge fixes
    it. Returns the final result dict."""
    result = solve_question(question)
    if solve_failed(question, result):
        retry = solve_question(f"{question} find the value")
        if not solve_failed(question, retry):
            return retry
    return result


@api_bp.post("/solve")
def api_solve():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    lang = normalise_lang(session.get("lang", "en"))
    strings = get_strings(lang)
    if not question:
        # Wave 5b: friendly localised message, never a bare error.
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"]})
    if len(question) > _QUESTION_LIMIT:
        return jsonify({"ok": False,
                        "message": strings["flash_too_long"]})

    result = _solve_friendly(question)

    # Wave 5 (additive): a chat solve on the homepage counts exactly
    # like a classic /solve — it lands in the session history and
    # becomes the "last solution" for /history, /download and the
    # print/PDF page. Existing response fields are unchanged.
    session["last_question"] = question
    session["last_result"] = result
    history = session.get("history", [])
    history.insert(0, {"question": question, "result": result})
    session["history"] = history[:_HISTORY_LIMIT]

    if solve_failed(question, result):
        # Wave 5b: the friendly error contract for the chat — the
        # client renders the localised error card + Retry in a
        # Ganitra bubble. No raw solver text leaves the server.
        return jsonify({
            "ok": False,
            "unsolvable": True,
            "question": question,
            "error": {
                "heading": strings["error_heading"],
                "intro": strings["error_intro"],
                "tips": [strings["error_tip1"], strings["error_tip2"],
                         strings["error_tip3"]],
                "retry_label": strings["error_retry_btn"],
            },
        })
    return jsonify({
        "ok": True,
        "result": result,
        "explanation": explanation_for(result, lang),
        "advice": advice_for(result, lang),
    })
