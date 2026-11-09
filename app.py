import re

from flask import (Flask, Response, render_template, request, redirect,
                   session, url_for, flash)
from api import api_bp
from i18n import (LANG_NAMES, SPEECH_LANGS, SUPPORTED_LANGS,
                  explanation_for, get_strings, normalise_lang)
from solver.practice import (QUIZ_DIFFICULTIES, QUIZ_QUESTION_COUNT,
                             QUIZ_SECONDS_PER_QUESTION, QUIZ_TOPICS,
                             check_quiz_answer, generate_practice,
                             generate_quiz)
from solver.router import solve_question

_HISTORY_LIMIT = 30


def normalize_ocr_text(text):
    """Conservatively clean text recognised from a photo (Tesseract.js).

    Only unambiguous maths fixes are applied — anything doubtful is left
    untouched so the user can correct it in the editable confirm box:
    unicode minus/dashes -> -, superscript ²/³ -> ^2/^3, ×/✕ -> *,
    ÷ -> /, an X between two digits -> *, and an isolated variable letter
    immediately followed by digits ("x2", "x 2") -> exponent ("x^2").
    """
    if not text:
        return ""
    t = text
    # Unicode minus and dash variants -> ASCII hyphen-minus
    t = t.replace("−", "-").replace("–", "-").replace("—", "-")
    # Superscript powers OCR sometimes produces
    t = t.replace("²", "^2").replace("³", "^3")
    # Multiplication / division symbols
    t = t.replace("×", "*").replace("✕", "*").replace("÷", "/")
    # "3X4" / "3 x 4" style: an X between two digits is multiplication
    t = re.sub(r"(\d)\s*[Xx]\s*(?=\d)", r"\1*", t)
    # "x2" / "x 2": isolated variable letter + digits is an exponent
    t = re.sub(r"(?<![A-Za-z])([A-Za-z])\s*(\d+)(?![A-Za-z])",
               r"\1^\2", t)
    # Collapse all whitespace (OCR line breaks) to single spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _solution_text(question, result):
    lines = [f"Question: {question}", ""]
    label = result.get("type", "")
    if result.get("op"):
        label = f"{label} · {result['op']}".strip(" ·")
    lines.append(f"Topic: {label}" if label else "Topic: -")
    lines.append(f"Answer: {result.get('answer', '')}")
    steps = result.get("steps") or []
    if steps:
        lines.append("")
        lines.append("Step-by-step solution:")
        for i, step in enumerate(steps, 1):
            lines.append(f"{i}. {step}")
    if result.get("interpreted_as"):
        lines.append("")
        lines.append(f"(Understood as: {result['interpreted_as']})")
    lines.append("")
    lines.append("— Solved by Ganitra (Flask + SymPy)")
    return "\n".join(lines)


def create_app():
    app = Flask(__name__)
    app.secret_key = "change-this-key"  # for flash messages + session

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    def _lang():
        return normalise_lang(session.get("lang", "en"))

    def _t():
        return get_strings(_lang())

    @app.context_processor
    def inject_i18n():
        lang = _lang()
        strings = get_strings(lang)
        try:
            strings["quiz_intro"] = strings["quiz_intro"].format(
                count=QUIZ_QUESTION_COUNT,
                seconds=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION)
        except (KeyError, IndexError, ValueError):
            pass
        return {
            "lang": lang,
            "t": strings,
            "lang_options": [(code, LANG_NAMES[code])
                             for code in SUPPORTED_LANGS],
            "speech_lang": SPEECH_LANGS[lang],
            "js_t": {k: v for k, v in strings.items()
                     if k.startswith("js_")},
            "voice_label": strings["voice_btn"],
        }

    @app.get("/set-lang/<code>")
    def set_lang(code):
        if code in SUPPORTED_LANGS:
            session["lang"] = code
        target = request.args.get("next") or ""
        if not target.startswith("/") or target.startswith("//"):
            target = url_for("index")
        return redirect(target)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/solve")
    def solve():
        question = request.form.get("question", "").strip()
        if not question:
            flash(_t()["flash_no_question"])
            return redirect(url_for("index"))
        result = solve_question(question)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result,
                               explanation=explanation_for(result,
                                                           _lang()))

    @app.post("/photo-solve")
    def photo_solve():
        # Text recognised from a photo by Tesseract.js in the browser.
        # Normalise it, solve it, and render the answer page with the
        # recognised text in an editable box on top — agar OCR ne galat
        # padha ho, user text theek karke normal /solve se dobara bhej
        # sakta hai.
        raw = request.form.get("question", "")
        question = normalize_ocr_text(raw)
        if not question:
            flash(_t()["flash_photo_empty"])
            return redirect(url_for("index"))
        result = solve_question(question)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result, photo_text=question,
                               explanation=explanation_for(result,
                                                           _lang()))

    @app.get("/download")
    def download():
        question = session.get("last_question")
        result = session.get("last_result")
        if not question or not result:
            flash(_t()["flash_download_first"])
            return redirect(url_for("index"))
        body = _solution_text(question, result)
        return Response(
            body,
            mimetype="text/plain; charset=utf-8",
            headers={"Content-Disposition":
                     "attachment; filename=solution.txt"},
        )

    @app.get("/history")
    def history():
        return render_template(
            "history.html", entries=session.get("history", []))

    @app.post("/history/clear")
    def history_clear():
        session.pop("history", None)
        return redirect(url_for("history"))

    @app.get("/practice")
    def practice():
        return render_template(
            "practice.html",
            questions=None,
            quiz=None,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    @app.post("/practice/start")
    def practice_start():
        topic = request.form.get("topic", "arithmetic")
        difficulty = request.form.get("difficulty", "easy")
        if topic not in QUIZ_TOPICS:
            topic = "arithmetic"
        if difficulty not in QUIZ_DIFFICULTIES:
            difficulty = "easy"
        items = generate_quiz(topic, difficulty)
        quiz = {"topic": topic, "difficulty": difficulty,
                "questions": items}
        session["quiz"] = quiz
        return render_template(
            "practice.html",
            questions=None,
            quiz=quiz,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    @app.post("/practice/submit")
    def practice_submit():
        quiz = session.get("quiz")
        if not quiz:
            flash(_t()["flash_start_quiz"])
            return redirect(url_for("practice"))
        rows, score = [], 0
        for i, item in enumerate(quiz["questions"]):
            given = request.form.get(f"answer_{i}", "")
            ok = check_quiz_answer(item["answer"], given)
            score += 1 if ok else 0
            rows.append({
                "question": item["question"],
                "expected": item["answer"],
                "given": given,
                "correct": ok,
            })
        session.pop("quiz", None)
        return render_template(
            "practice_result.html",
            rows=rows,
            score=score,
            total=len(rows),
            topic=quiz["topic"],
            difficulty=quiz["difficulty"],
            time_taken=request.form.get("time_taken", ""),
        )

    @app.get("/practice/classic")
    def practice_classic():
        return render_template(
            "practice.html",
            questions=generate_practice(7),
            quiz=None,
            topics=QUIZ_TOPICS,
            difficulties=QUIZ_DIFFICULTIES,
            time_limit=QUIZ_QUESTION_COUNT * QUIZ_SECONDS_PER_QUESTION,
        )

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
