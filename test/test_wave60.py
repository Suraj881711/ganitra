"""Wave 60: the ONE back system (Suraj: "Ganitra ke andar
back system nahi hai").

Pins: the _backnav_for_path map (which pages get the bar and
where the no-history fallback points), the rendered bar on
every inner page with the right fallback, NO bar on the chat
home, the timed-test confirmation gates (/test while the
paper is on screen, the classic quiz while its form is on
screen, the Board chapter test always while questions show),
the print views' back links, the i18n keys in all six
languages, the bumped delivery pins (?v=35 / cache v10), and
that visiting inner pages never disturbs a saved chat.
"""
from pathlib import Path

import pytest

from app import _backnav_for_path
from i18n import get_strings, SUPPORTED_LANGS
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
        "name": "W60 Test Tester", "class": "10", "board": "CBSE",
        "goal": "Engineer", "hobby": "Football",
        "favourite": "Mango", "password": "w60-test-pass"})
    return c


# --- the path map ------------------------------------------------

@pytest.mark.parametrize("path,want", [
    ("/", None),
    ("/board/test/start", None),
    ("/test", ("/", "#test-paper")),
    ("/practice/start", ("/", "#quiz-form")),
    ("/practice/submit", ("/practice", None)),
    ("/board/test/submit", ("/practice", None)),
    ("/board", ("/", None)),
    ("/board/10", ("/board", None)),
    ("/board/10/quadratic-equations", ("/board/10", None)),
    ("/board/10/quadratic-equations/practice",
     ("/board/10/quadratic-equations", None)),
    ("/papers", ("/", None)),
    ("/papers/analysis", ("/papers", None)),
    ("/papers/anything", ("/papers", None)),
    ("/mistakes", ("/", None)),
    ("/mistakes/practice", ("/mistakes", None)),
    ("/topics", ("/", None)),
    ("/chats", ("/", None)),
    ("/account", ("/", None)),
    ("/practice-mode", ("/", None)),
    ("/history", ("/", None)),
    ("/parent-report", ("/", None)),
    ("/solve", ("/", None)),
])
def test_backnav_map(path, want):
    assert _backnav_for_path(path) == want


# --- rendered pages ----------------------------------------------

@pytest.mark.parametrize("path,fallback", [
    ("/chats", "/"),
    ("/topics", "/"),
    ("/board", "/"),
    ("/board/10", "/board"),
    ("/board/10/quadratic-equations", "/board/10"),
    ("/board/10/quadratic-equations/practice",
     "/board/10/quadratic-equations"),
    ("/papers", "/"),
    ("/papers/analysis", "/papers"),
    ("/papers/generate", "/papers"),
    ("/practice", "/"),
    ("/practice-mode", "/"),
    ("/test", "/"),
    ("/mistakes", "/"),
    ("/history", "/"),
    ("/parent-report", "/"),
    ("/account", "/"),
])
def test_inner_pages_carry_the_bar(client, path, fallback):
    body = client.get(path).get_data(as_text=True)
    assert 'class="backnav-btn"' in body
    assert f'data-fallback="{fallback}"' in body


def test_paper_view_fallback_is_papers(client):
    body = client.get(
        "/papers/" + papers_data.PAPERS[0]["id"]).get_data(as_text=True)
    assert 'data-fallback="/papers"' in body


def test_chat_home_has_no_bar(client):
    body = client.get("/").get_data(as_text=True)
    assert 'class="backnav-btn"' not in body


def test_chapter_test_bar_asks_only_while_paper_on_screen(client):
    body = client.get("/test").get_data(as_text=True)
    assert 'data-confirm-if="#test-paper"' in body
    assert "data-confirm-msg" in body


def test_answer_page_carries_the_bar(client):
    body = client.post(
        "/solve", data={"question": "2 + 2"}).get_data(as_text=True)
    assert 'class="backnav-btn"' in body
    assert 'data-fallback="/"' in body


def test_classic_quiz_bar_asks_while_quiz_on_screen(client):
    body = client.post("/practice/start", data={
        "topic": "arithmetic", "difficulty": "easy"}).get_data(
            as_text=True)
    assert 'data-confirm-if="#quiz-form"' in body


def test_board_test_bar_chapter_fallback_and_always_asks(client):
    body = client.post("/board/test/start", data={
        "class_num": "10",
        "slug": "quadratic-equations"}).get_data(as_text=True)
    assert 'data-fallback="/board/10/quadratic-equations"' in body
    assert "data-confirm-msg" in body
    assert 'data-confirm-if="' not in body


def test_print_views_have_back_links(client):
    # Wave 121: the print views' way back is the BARE ARROW
    # (class print-back), not the boxed print-btn link Wave 60
    # shipped — Suraj's spec: no box, no "Back" word, anywhere.
    client.post("/solve", data={"question": "2 + 2"})
    body = client.get("/solution/print").get_data(as_text=True)
    assert 'class="print-back" href="/"' in body
    client.post("/papers/generate", data={"class_num": "10"})
    body = client.get("/papers/print").get_data(as_text=True)
    assert 'class="print-back" href="/papers"' in body


def test_chat_survives_inner_page_visits(client):
    chat = client.post("/api/chats").get_json()["chat"]
    client.get("/topics")
    client.get("/papers")
    client.get("/board")
    got = client.get(f"/api/chats/{chat['id']}").get_json()
    assert got["chat"]["id"] == chat["id"]


# --- i18n + pins ---------------------------------------------------

def test_back_strings_in_all_languages():
    for lang in SUPPORTED_LANGS:
        strings = get_strings(lang)
        assert strings["nav_back"]
        assert strings["nav_back_test_confirm"]


def test_delivery_pins_bumped_for_new_css():
    base = (ROOT / "templates" / "base.html").read_text(
        encoding="utf-8")
    sw = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")
    css = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
    assert "v='43'" in base
    assert 'GANITRA_CACHE = "ganitra-static-v20"' in sw
    assert ".backnav-btn" in css
    assert "min-height: 44px" in css
