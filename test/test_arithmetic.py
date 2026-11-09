from solver.router import solve_question

def test_basic_arithmetic():
    r = solve_question("2+2*5")
    assert r["type"] == "arithmetic"
    assert r["numeric"] == 12.0
