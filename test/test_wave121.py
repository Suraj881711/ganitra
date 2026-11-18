"""Wave 121: the back button, set properly on every page.

Suraj (17 Nov 2026): "Back ka button achhe se set karo sabhi
jagah" + the binding design spec "Back nhi likhana, circle
nhi lagana, bs arrow lagao" — the control is a BARE ARROW:
no "Back" word, no pill/circle/box, just the ← glyph at the
top-left with an invisible 44px tap target (the localised
word survives only as the aria-label).

Pins: the Wave 60 map's logical-parent fixes (the sign-in
gate re-rendered by a failed login gets NO bar; /practice/
classic's parent is /practice; exam-mode intro/result live
under their paper; weak-topic practice/result live under
/weak-topics), the arrow-only rendered markup on the base
block AND both template overrides (Board test, full-paper
attempt), the bare-arrow CSS rule kept identical in
style.css and base.html's Wave-72 inline mirror, the print
views' bare-arrow way back, and the bumped delivery pins
(?v=43 / cache v19 — Wave 116 bumps to the same numbers in
its own tree; the second merge must go to v43/v20).
"""
import re
from pathlib import Path

import pytest

from app import _backnav_for_path
import papers_data

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W121 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w121-test-pass"})
    return c


def _button_text(body):
    """The visible text of the rendered back button."""
    m = re.search(
        r'<button[^>]*class="backnav-btn"[^>]*>(.*?)</button>',
        body, re.S)
    assert m, "no backnav button rendered"
    inner = re.sub(r"<[^>]+>", "", m.group(1))
    return inner.strip(), m.group(0)


# --- the path map: Wave 121 logical-parent fixes ---------------

@pytest.mark.parametrize("path,want", [
    # The sign-in gate is a root screen, including when a
    # failed POST re-renders it at the POST's own path.
    ("/login", None),
    ("/signup", None),
    ("/login-favourite", None),
    ("/practice/classic", ("/practice", None)),
    ("/weak-topics", ("/", None)),
    ("/weak-topics/start", ("/weak-topics", None)),
    ("/weak-topics/submit", ("/weak-topics", None)),
])
def test_backnav_map_wave121(path, want):
    assert _backnav_for_path(path) == want


def test_backnav_map_paper_attempt_lives_under_its_paper():
    pid = papers_data.PAPERS[0]["id"]
    assert _backnav_for_path(f"/papers/{pid}/attempt") == \
        (f"/papers/{pid}", None)
    assert _backnav_for_path(f"/papers/{pid}/attempt/submit") == \
        (f"/papers/{pid}", None)
    # ...while the paper page itself still parents to the list.
    assert _backnav_for_path(f"/papers/{pid}") == ("/papers", None)


# --- the gate gets no bar, even after a failed login -----------

def test_signed_out_gate_has_no_bar(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    body = c.get("/").get_data(as_text=True)
    assert 'class="backnav-btn"' not in body
    # A failed login re-renders the gate at /login — still none.
    body = c.post("/login", data={
        "name": "Nobody Here", "password": "wrong-pass"}
    ).get_data(as_text=True)
    assert 'class="backnav-btn"' not in body


# --- rendered markup: bare arrow everywhere ---------------------

@pytest.mark.parametrize("path", [
    "/topics", "/chats", "/account", "/papers", "/board",
    "/board/10", "/history", "/parent-report", "/progress",
    "/practice", "/practice-mode", "/test", "/mistakes",
])
def test_back_button_is_a_bare_arrow(client, path):
    body = client.get(path).get_data(as_text=True)
    text, tag = _button_text(body)
    assert text == "←", (path, text)
    assert 'aria-label="' in tag  # the word survives for AT


def test_paper_attempt_intro_fallback_is_the_paper(client):
    pid = papers_data.PAPERS[0]["id"]
    body = client.get(f"/papers/{pid}/attempt").get_data(
        as_text=True)
    assert f'data-fallback="/papers/{pid}"' in body
    text, _ = _button_text(body)
    assert text == "←"


def test_classic_practice_fallback_is_practice(client):
    body = client.get("/practice/classic").get_data(as_text=True)
    assert 'data-fallback="/practice"' in body


def test_board_test_override_button_is_bare_arrow(client):
    body = client.post("/board/test/start", data={
        "class_num": "10",
        "slug": "quadratic-equations"}).get_data(as_text=True)
    text, _ = _button_text(body)
    assert text == "←"
    assert 'data-fallback="/board/10/quadratic-equations"' in body


def test_full_paper_attempt_override_button_is_bare_arrow(client):
    pid = papers_data.PAPERS[0]["id"]
    client.get(f"/papers/{pid}/attempt")
    body = client.post(
        f"/papers/{pid}/attempt/start").get_data(as_text=True)
    text, _ = _button_text(body)
    assert text == "←"
    assert f'data-fallback="/papers/{pid}"' in body


def test_answer_page_button_is_bare_arrow(client):
    body = client.post(
        "/solve", data={"question": "2 + 2"}).get_data(as_text=True)
    text, _ = _button_text(body)
    assert text == "←"


def test_weak_practice_fallback_is_weak_topics(client):
    # Record a real mistake (a wrong chapter-test answer), then
    # start weak practice: its bar must parent to /weak-topics.
    client.post("/test/start", json={
        "class_num": 10, "topic": "arithmetic"})
    client.post("/test/submit", json={
        "answers": ["definitely-wrong"] * 10, "time_taken": 42})
    body = client.post("/weak-topics/start").get_data(as_text=True)
    if 'class="backnav-btn"' in body:  # a set was built
        assert 'data-fallback="/weak-topics"' in body


# --- CSS: bare arrow, mirrored identically -----------------------

def _backnav_btn_rule(text):
    m = re.search(r"\.backnav-btn\s*\{(.*?)\}", text, re.S)
    assert m, ".backnav-btn rule missing"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def test_backnav_css_is_bare_arrow_and_mirrored():
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    base = (ROOT / "templates" / "base.html").read_text(
        encoding="utf-8")
    rule_css = _backnav_btn_rule(css)
    rule_base = _backnav_btn_rule(base)
    assert rule_css == rule_base
    for decl in ("background: none", "border: 0",
                 "box-shadow: none", "min-height: 44px",
                 "width: 44px"):
        assert decl in rule_css, decl
    assert "999px" not in rule_css  # no pill
    assert "#fff" not in rule_css   # no filled disc/box


def test_templates_carry_no_visible_back_word():
    for name in ("base.html", "board_test.html",
                 "full_paper_attempt.html"):
        text = (ROOT / "templates" / name).read_text(
            encoding="utf-8")
        assert "</span> {{ t.nav_back }}</button>" not in text, name


# --- print views: bare arrow too ---------------------------------

def test_print_views_way_back_is_a_bare_arrow(client):
    client.post("/solve", data={"question": "2 + 2"})
    body = client.get("/solution/print").get_data(as_text=True)
    m = re.search(
        r'<a class="print-back" href="/"[^>]*>(.*?)</a>', body, re.S)
    assert m and m.group(1).strip() == "←"
    body = client.get("/progress/print").get_data(as_text=True)
    m = re.search(
        r'<a class="print-back" href="/progress"[^>]*>(.*?)</a>',
        body, re.S)
    assert m and m.group(1).strip() == "←"


# --- pins ----------------------------------------------------------

def test_delivery_pins_bumped_for_new_css():
    base = (ROOT / "templates" / "base.html").read_text(
        encoding="utf-8")
    sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
    assert "v='53'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v30"' in sw
