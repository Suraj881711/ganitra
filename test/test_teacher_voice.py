"""Wave 22 (Suraj, 12 Nov 2026): "aisa bilkul nhi lagna
chahiye ki koi AI samjha raha ho — aisa lagna chahiye ki
koi teacher padha raha ho" + "icon chote karo".

The spoken track (Listen + Teach, chat and classic answer
page) is rebuilt by a client-side teacher-narration layer:
narrateSolution() wraps the written steps in spoken teacher
lines and tuneUtterance() picks a natural voice at rate
0.95. These tests pin the two halves of the contract that
Python can see: (1) the narration layer is wired into both
templates and the icons shrank, and (2) the WRITTEN payload
— API result and the classic page's SPEAK data — is still
the solver's raw steps/answer, byte for byte. (The spoken
behaviour itself is exercised under node in
verify_wave18.py.)
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
ANSWER = (ROOT / "templates" / "answer.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_narration_layer_wired_in_both_templates():
    for src in (INDEX, ANSWER):
        assert "function narrateSolution" in src
        assert "var TEACHER" in src
        assert "function pickVoice" in src
        assert "function tuneUtterance" in src
        assert "u.rate = 0.95" in src
        assert "u.pitch = 1.0" in src
    # Chat: bubble Listen + Teach + method Listen all narrate.
    # (Wave 25: the bubble feeds its displaySteps — the solver
    # steps minus a trailing answer restatement.)
    assert "narrateSolution(displaySteps" in INDEX
    assert "narrateSolution(method.steps" in INDEX
    # Classic page: buildQueue narrates from the raw SPEAK data.
    assert "narrateSolution(SPEAK.steps" in ANSWER


def test_teacher_templates_have_no_numbers_of_their_own():
    """The maths rule: template lines may not invent values —
    the only placeholder allowed is {ans} (the real answer),
    and no template string carries a digit."""
    for src in (INDEX, ANSWER):
        block = src[src.index("var TEACHER = {"):
                    src.index("function pickLine")]
        for line in block.splitlines():
            if '"' in line:
                assert not any(ch.isdigit() for ch in line), line


def test_action_icons_shrunk_wave22():
    assert "Wave 22" in CSS
    # Wave 24 final word (Suraj, 13 Nov 2026, Muse-row
    # screenshot): borderless outline glyphs at 18px (20px
    # until the same-night design change) — no
    # background, no border (supersedes 34px -> 36px boxes).
    assert ".act-btn svg { width: 18px; height: 18px; }" in CSS
    assert "background: transparent; border: none;" \
        " box-shadow: none;" in CSS
    # Composer glyphs trimmed slightly (buttons stay 40px).
    assert ".chat-bar .composer-btn svg" in CSS


def test_written_api_payload_unchanged(client):
    from solver.router import solve_question
    expected = solve_question("x^2-5x+6=0")
    r = client.post("/api/solve", json={"question": "x^2-5x+6=0"})
    d = r.get_json() or {}
    res = d.get("result") or {}
    assert res.get("steps") == (expected.get("steps") or [])
    assert res.get("answer") == expected.get("answer")


def test_written_speak_payload_unchanged(client):
    """The classic page still embeds the RAW written solution
    in SPEAK — narration is built from it in the browser, the
    payload itself is not rewritten."""
    from solver.router import solve_question
    expected = solve_question("x^2-5x+6=0")
    body = client.post(
        "/solve", data={"question": "x^2-5x+6=0"}).get_data(as_text=True)
    m = re.search(r"var SPEAK = (\{.*?\});", body, re.S)
    assert m, "SPEAK payload missing"
    speak = json.loads(m.group(1))
    assert speak.get("steps") == (expected.get("steps") or [])
    assert speak.get("answer") == "x = 2, x = 3"
