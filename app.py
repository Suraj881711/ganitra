import re

from flask import (Flask, Response, render_template, request, redirect,
                   session, url_for, flash)
from api import api_bp
from i18n import (LANG_NAMES, SPEECH_LANGS, SUPPORTED_LANGS,
                  advice_for, explanation_for, get_strings,
                  normalise_lang, remark_key_for, result_unsolvable,
                  solve_failed)
from solver.practice import (QUIZ_DIFFICULTIES, QUIZ_QUESTION_COUNT,
                             QUIZ_SECONDS_PER_QUESTION, QUIZ_TOPICS,
                             check_quiz_answer, generate_practice,
                             generate_quiz)
from board_data import (BOARD_NAMES, BOARDS, CLASS_NUMBERS,
                        get_chapter, get_chapters)
from board_quiz import (CLASSIC_QUESTION_COUNT, display_answer,
                        generate_chapter_questions)
from solver.router import solve_question

_HISTORY_LIMIT = 30
_MISTAKE_LIMIT = 50
_QUESTION_LIMIT = 500


def _ask_again(question):
    """Wave 5b: re-ask the same question with a gentle pre-filled hint
    appended. The hint is plain English (the router understands plain
    maths English; the friendly card in the default language explains
    the situation before the button is pressed), and the expression
    guard lives in the solver, so this never turns a solvable
    question into a failure."""
    return f"{question} find the value"


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

    def _record_mistakes(rows, source):
        """Wave 5: save the WRONG rows of a quiz/chapter test into the
        session Mistake Notebook, newest first."""
        wrong = [{"question": r["question"], "expected": r["expected"],
                  "given": r.get("given", ""), "topic": r.get("topic"),
                  "source": source}
                 for r in rows if not r["correct"]]
        if wrong:
            notebook = session.get("mistakes", [])
            session["mistakes"] = (wrong + notebook)[:_MISTAKE_LIMIT]

    def _copycheck(rows, score, total, topic_labels, chapter=None):
        """Wave 5e: build the board-style copy-check card data and
        persist the last test report in the session, so the result
        page can be re-rendered with the same card. The card checks
        FINAL ANSWERS only (like a teacher checking a copy): marks,
        a remark by score band, per-question ticks, and the topics /
        chapters where marks were lost. `topic_labels` maps a row's
        topic key to its display name (quiz topic names or the
        chapter title)."""
        lost, seen = [], set()
        for r in rows:
            if not r["correct"]:
                label = topic_labels.get(r.get("topic"),
                                         r.get("topic") or "")
                if label and label not in seen:
                    seen.add(label)
                    lost.append(label)
        report = {
            "score": score,
            "total": total,
            "remark_key": remark_key_for(score, total),
            "lost_topics": lost,
            "chapter": chapter,
            "celebrate": bool(total) and score / total >= 0.8,
        }
        session["last_test_report"] = report
        return report

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
                     if k.startswith("js_") or k.startswith("error_")
                     or k in ("chat_waking_note", "flash_too_long",
                              "dhyaan_today")},
            "dhyaan_today": strings["dhyaan_today"],
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
        if len(question) > _QUESTION_LIMIT:
            flash(_t()["flash_too_long"])
            return redirect(url_for("index"))
        result = solve_question(question)
        # Wave 5b: on failure, gently re-ask once with a hint; the
        # second result decides what the student sees.
        if solve_failed(question, result):
            retry = solve_question(_ask_again(question))
            if not solve_failed(question, retry):
                result = retry
        failed = solve_failed(question, result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result,
                               explanation=(None if failed
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if failed
                                       else advice_for(result, _lang())),
                               unsolvable=failed)

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
            flash(_t()["photo_no_text"])
            return redirect(url_for("index"))
        if len(question) > _QUESTION_LIMIT:
            flash(_t()["flash_too_long"])
            return redirect(url_for("index"))
        result = solve_question(question)
        if solve_failed(question, result):
            retry = solve_question(_ask_again(question))
            if not solve_failed(question, retry):
                result = retry
        failed = solve_failed(question, result)
        session["last_question"] = question
        session["last_result"] = result
        history = session.get("history", [])
        history.insert(0, {"question": question, "result": result})
        session["history"] = history[:_HISTORY_LIMIT]
        return render_template("answer.html", question=question,
                               result=result, photo_text=question,
                               explanation=(None if failed
                                            else explanation_for(result,
                                                                 _lang())),
                               advice=(None if failed
                                       else advice_for(result, _lang())),
                               unsolvable=failed)

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
                "topic": quiz["topic"],
            })
        _record_mistakes(rows, "quiz")
        session.pop("quiz", None)
        t = _t()
        copycheck = _copycheck(
            rows, score, len(rows),
            {quiz["topic"]: t[f"quiz_topic_{quiz['topic']}"]})
        return render_template(
            "practice_result.html",
            rows=rows,
            score=score,
            total=len(rows),
            topic=quiz["topic"],
            difficulty=quiz["difficulty"],
            time_taken=request.form.get("time_taken", ""),
            copycheck=copycheck,
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

    # ------------------------------------------------------------ print
    @app.get("/solution/print")
    def solution_print():
        """Print-friendly solution page (Wave 5): the browser's own
        Print -> Save as PDF produces the PDF, so the app needs no
        PDF library at all."""
        question = session.get("last_question")
        result = session.get("last_result")
        if not question or not result:
            flash(_t()["flash_download_first"])
            return redirect(url_for("index"))
        return render_template(
            "print.html", question=question, result=result,
            explanation=explanation_for(result, _lang()),
            advice=advice_for(result, _lang()),
            handwriting_style=(request.args.get("style") == "hand"))

    # -------------------------------------------------------- board mode
    @app.get("/board")
    def board_home():
        from datetime import date

        board_slug = session.get("board", "cbse")
        # Teacher's Advice of the Day: 7 curated tips, one per day,
        # rotated by calendar date (same tip all day, all visitors).
        tip_key = f"tip_day_{date.today().toordinal() % 7}"
        return render_template(
            "board.html", boards=BOARDS,
            board_slug=board_slug,
            board_name=BOARD_NAMES.get(board_slug, "CBSE"),
            class_numbers=CLASS_NUMBERS,
            day_tip=_t()[tip_key])

    @app.get("/board/select/<board_slug>")
    def board_select(board_slug):
        if board_slug in BOARD_NAMES:
            session["board"] = board_slug
        return redirect(url_for("board_home"))

    @app.get("/board/<int:class_num>")
    def board_class(class_num):
        chapters = get_chapters(class_num)
        if not chapters:
            return redirect(url_for("board_home"))
        board_slug = session.get("board", "cbse")
        return render_template(
            "board_class.html", class_num=class_num,
            chapters=chapters,
            board_name=BOARD_NAMES.get(board_slug, "CBSE"))

    @app.get("/board/<int:class_num>/<slug>")
    def board_chapter(class_num, slug):
        chapter = get_chapter(class_num, slug)
        if chapter is None:
            return redirect(url_for("board_home"))
        return render_template(
            "board_chapter.html", class_num=class_num,
            chapter=chapter)

    @app.get("/board/<int:class_num>/<slug>/practice")
    def board_chapter_practice(class_num, slug):
        chapter = get_chapter(class_num, slug)
        if chapter is None:
            return redirect(url_for("board_home"))
        items = generate_chapter_questions(
            chapter["topic"], count=CLASSIC_QUESTION_COUNT)
        questions = [{"question": it["question"],
                      "answer": display_answer(it["answer"])}
                     for it in items]
        return render_template(
            "board_practice.html", class_num=class_num,
            chapter=chapter, questions=questions)

    @app.post("/board/test/start")
    def board_test_start():
        try:
            class_num = int(request.form.get("class_num", ""))
        except ValueError:
            class_num = -1
        chapter = get_chapter(class_num,
                              request.form.get("slug", ""))
        if chapter is None:
            return redirect(url_for("board_home"))
        items = generate_chapter_questions(chapter["topic"])
        session["board_test"] = {
            "class_num": class_num,
            "slug": chapter["slug"],
            "chapter_title": chapter["title"],
            "topic": chapter["topic"],
            "questions": items,
        }
        return render_template(
            "board_test.html", class_num=class_num, chapter=chapter,
            test=session["board_test"],
            time_limit=QUIZ_QUESTION_COUNT
            * QUIZ_SECONDS_PER_QUESTION)

    @app.post("/board/test/submit")
    def board_test_submit():
        test = session.get("board_test")
        if not test:
            flash(_t()["flash_start_quiz"])
            return redirect(url_for("board_home"))
        rows, score = [], 0
        for i, item in enumerate(test["questions"]):
            given = request.form.get(f"answer_{i}", "")
            ok = check_quiz_answer(item["answer"], given)
            score += 1 if ok else 0
            rows.append({
                "question": item["question"],
                "expected": display_answer(item["answer"]),
                "given": given,
                "correct": ok,
                "topic": test["topic"],
            })
        _record_mistakes(
            rows, f"Class {test['class_num']} · "
                  f"{test['chapter_title']}")
        session.pop("board_test", None)
        copycheck = _copycheck(
            rows, score, len(rows),
            {test["topic"]: test["chapter_title"]},
            chapter=test["chapter_title"])
        return render_template(
            "practice_result.html",
            rows=rows,
            score=score,
            total=len(rows),
            topic=test["topic"],
            difficulty="medium",
            time_taken=request.form.get("time_taken", ""),
            copycheck=copycheck,
        )

    # -------------------------------------------------- mistake notebook
    @app.get("/mistakes")
    def mistakes():
        entries = [{"question": e["question"],
                    "expected": display_answer(e["expected"]),
                    "source": e.get("source", "")}
                   for e in session.get("mistakes", [])]
        return render_template("mistakes.html", entries=entries)

    @app.get("/mistakes/practice")
    def mistakes_practice():
        entries = session.get("mistakes", [])
        if not entries:
            return redirect(url_for("mistakes"))
        questions = [{"question": e["question"],
                      "answer": display_answer(e["expected"])}
                     for e in entries]
        session["mistakes_round"] = [
            {"question": e["question"], "expected": e["expected"]}
            for e in entries]
        return render_template("mistakes_practice.html",
                               questions=questions)

    @app.post("/mistakes/practice/submit")
    def mistakes_practice_submit():
        """Wave 5e: finishing the mistakes-retry round shows the
        Badhai card. The round is the classic reveal-answer practice
        (answers are shown on the page), so completing it means the
        student worked through every saved mistake — no score is
        claimed, just the celebration + the count."""
        round_items = session.pop("mistakes_round", None)
        if round_items is None:
            entries = session.get("mistakes", [])
            round_items = [{"question": e["question"],
                            "expected": e["expected"]}
                           for e in entries]
        questions = [{"question": it["question"],
                      "answer": display_answer(it["expected"])}
                     for it in round_items]
        return render_template(
            "mistakes_practice.html", questions=questions,
            round_done=True, round_count=len(round_items))

    @app.post("/mistakes/clear")
    def mistakes_clear():
        session.pop("mistakes", None)
        return redirect(url_for("mistakes"))

    return app


if __name__ == "__main__":
    import os

    app = create_app()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
