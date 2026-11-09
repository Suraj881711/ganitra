from flask import Flask, render_template, request, redirect, url_for, flash
from api import api_bp
from solver.practice import generate_practice
from solver.router import solve_question


def create_app():
    app = Flask(__name__)
    app.secret_key = "change-this-key"  # for flash messages

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/solve")
    def solve():
        question = request.form.get("question", "").strip()
        if not question:
            flash("Please enter a question.")
            return redirect(url_for("index"))
        result = solve_question(question)
        return render_template("answer.html", question=question, result=result)

    @app.get("/practice")
    def practice():
        questions = generate_practice(7)
        return render_template("practice.html", questions=questions)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
