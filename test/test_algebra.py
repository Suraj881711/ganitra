from solver.router import solve_question

def test_linear_equation():
    r = solve_question("2*x + 3 = 7")
    assert r["type"] == "algebra"
    sols = r.get("solutions")
    assert isinstance(sols, list) and len(sols) >= 1
