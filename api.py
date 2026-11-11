from flask import Blueprint, request, jsonify, session
from i18n import (LANG_NAMES, SPEECH_LANGS, advice_for,
                  explanation_for, get_strings, normalise_lang,
                  result_unsolvable, solve_failed, teach_for)
from langdetect_local import detect_language_confident
from fallback import with_fallback
from solver.methods import alternate_methods
from solver.router import solve_question
from speedups import methods_nonblocking

api_bp = Blueprint("api", __name__)

_HISTORY_LIMIT = 30
_QUESTION_LIMIT = 500


def _solve_friendly(question):
    """Wave 5b: solve, and on failure gently re-ask once with a hint
    appended (same behaviour as the classic /solve route), so the
    chat never shows a raw solver failure when a small nudge fixes
    it. Returns the final result dict.

    Wave 18: the result then passes through the no-dead-end
    layer (fallback.with_fallback) — real solver answers come
    back untouched; failures, letter-soup "answers", soft
    non-answers, greetings and non-maths asks become an honest
    fallback answer instead of the error card."""
    result = solve_question(question)
    if solve_failed(question, result):
        retry = solve_question(f"{question} find the value")
        if not solve_failed(question, retry):
            result = retry
    return with_fallback(question, result)


# --- Wave 9: auto language ---------------------------------------------
# The site language stays English by default; when a chat message is
# solidly detected in another supported language, the session
# language switches to it automatically and THIS response is already
# rendered in the new language. Every response gains
# language_switched/language; on a switch it also carries `ui` (the
# chat page's strings in the new language, so the client can re-skin
# without a reload) and a localised `lang_notice` toast line. A
# manual language pick is never overridden by anything except a
# later chat message in yet another language.

_UI_PREFIXES = ("js_", "error_", "chat_", "nav_")
_UI_EXTRA_KEYS = {
    "steps_heading", "explanation_heading", "advice_heading",
    "listen_btn", "listen_stop_btn", "handwriting_btn",
    "print_copy_link", "question_placeholder", "enter_question",
    "solve_btn", "voice_btn", "photo_btn", "lang_label", "menu_label",
    "dhyaan_today", "dhyaan_label", "chat_waking_note",
    "flash_too_long", "chat_empty_sub", "chat_welcome",
    "chat_greeting_plain", "saathi_welcome_name",
    "lang_switched_toast",
}


def _lang_fields(lang, strings, switched):
    """The Wave-9 fields added to every /api/solve response."""
    fields = {"language_switched": bool(switched), "language": lang}
    if switched:
        ui = {k: v for k, v in strings.items()
              if k.startswith(_UI_PREFIXES) or k in _UI_EXTRA_KEYS}
        ui["speech_lang"] = SPEECH_LANGS[lang]
        fields["ui"] = ui
        try:
            fields["lang_notice"] = strings[
                "lang_switched_toast"].format(lang=LANG_NAMES[lang])
        except (KeyError, IndexError, ValueError):
            fields["lang_notice"] = ""
    return fields


# --- Wave 17b: JSON type guards (pen-test F2) ---------------------------
# A non-string "question"/"method" (int, list, dict, bool) used to
# crash .strip() into an HTTP 500, and a non-object JSON body did
# the same to .get(). The rule now: a body that is not a JSON
# object, or a field that is present but not a string, is a
# friendly HTTP 400 — never a 500. A missing/null field keeps the
# old behaviour (treated as empty).

def _json_object():
    """The request's JSON body as a dict: {} when there is no
    usable body at all, None when a body WAS sent but is not a
    JSON object."""
    data = request.get_json(silent=True)
    if data is None:
        return {}
    return data if isinstance(data, dict) else None


def _json_str(data, field):
    """data[field] as text: missing/null -> "", a string ->
    itself, anything else -> None (the caller answers 400)."""
    value = data.get(field)
    if value is None:
        return ""
    return value if isinstance(value, str) else None


@api_bp.post("/solve")
def api_solve():
    data = _json_object()
    lang = normalise_lang(session.get("lang", "en"))
    strings = get_strings(lang)
    if data is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = _json_str(data, "question")
    if question is None:
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)}), 400
    question = question.strip()
    if not question:
        # Wave 5b: friendly localised message, never a bare error.
        return jsonify({"ok": False,
                        "message": strings["flash_no_question"],
                        **_lang_fields(lang, strings, False)})
    if len(question) > _QUESTION_LIMIT:
        return jsonify({"ok": False,
                        "message": strings["flash_too_long"],
                        **_lang_fields(lang, strings, False)})

    # Wave 9: auto language — detect from the question itself. A
    # solid detection in a different language moves the session to
    # that language BEFORE solving, so the answer, explanation,
    # advice and any error card below are all in the new language.
    detected, solid = detect_language_confident(question)
    switched = False
    if solid and detected != lang:
        lang = detected
        session["lang"] = lang
        strings = get_strings(lang)
        switched = True
    fields = _lang_fields(lang, strings, switched)

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
        # Wave 6: the same gentle card also carries the personal
        # Mera Saathi encouragement line (named when a name is set).
        saathi_name = session.get("saathi_name", "")
        if not isinstance(saathi_name, str):
            saathi_name = ""
        saathi_name = saathi_name[:30]
        if saathi_name:
            try:
                encouragement = strings[
                    "error_encourage_name"].format(name=saathi_name)
            except (IndexError, KeyError, ValueError):
                encouragement = strings["error_encourage_name"]
        else:
            encouragement = strings["error_encourage"]
        return jsonify({
            "ok": False,
            "unsolvable": True,
            "question": question,
            "error": {
                "heading": strings["error_heading"],
                "intro": strings["error_intro"],
                "encouragement": encouragement,
                "tips": [strings["error_tip1"], strings["error_tip2"],
                         strings["error_tip3"]],
                "retry_label": strings["error_retry_btn"],
            },
            **fields,
        })
    return jsonify({
        "ok": True,
        "result": result,
        "explanation": explanation_for(result, lang),
        "advice": advice_for(result, lang),
        # Wave 12: genuinely-different extra methods for this
        # question (possibly none) + the "Teach me" concept lines.
        # The chat renders them as the small side chips; both are
        # stored with the bot turn, so a reopened account chat
        # shows exactly the same options.
        # Wave 14: the auto-teach methods pass runs with a hard
        # time budget (speedups.methods_nonblocking) — same data
        # in every normal case, but it can never delay the answer.
        "methods": methods_nonblocking(question, result),
        "teach": teach_for(result, lang),
        **fields,
    })


@api_bp.post("/solve-method")
def api_solve_method():
    """Wave 12: re-serve ONE alternate method for a question.

    The methods already ride inside the /api/solve response (and
    inside saved chat threads), so this endpoint is the explicit
    contract the chips use when a method is opened: recompute the
    primary solve, look the method id up among ITS alternates,
    and return just that method (+ the teach lines). An unknown
    or unavailable method is a calm {ok: false}, never an error
    page.
    """
    data = _json_object()
    if data is None:
        return jsonify({"ok": False, "error": "bad-request"}), 400
    question = _json_str(data, "question")
    method_id = _json_str(data, "method")
    if question is None or method_id is None:
        return jsonify({"ok": False, "error": "bad-request"}), 400
    question = question.strip()
    method_id = method_id.strip()
    lang = normalise_lang(session.get("lang", "en"))
    if not question or not method_id \
            or len(question) > _QUESTION_LIMIT:
        return jsonify({"ok": False, "error": "method-unavailable"})
    primary = _solve_friendly(question)
    if solve_failed(question, primary):
        return jsonify({"ok": False, "error": "method-unavailable"})
    for method in alternate_methods(question, primary):
        if method.get("id") == method_id:
            return jsonify({"ok": True, "method": method,
                            "teach": teach_for(primary, lang)})
    return jsonify({"ok": False, "error": "method-unavailable"})
