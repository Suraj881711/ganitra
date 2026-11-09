from flask import Blueprint, request, jsonify
from solver.router import solve_question

api_bp = Blueprint("api", __name__)


@api_bp.post("/solve")
def api_solve():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"ok": False, "error": "Missing 'question'"}), 400

    result = solve_question(question)
    return jsonify({"ok": True, "result": result})

