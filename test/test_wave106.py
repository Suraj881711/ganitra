"""Wave 106: the Dhyaan system is REMOVED (Suraj's order,
17 Nov 2026: "dhyaan waale system ko hata do").

Gone completely:
- the 🧘 Dhyaan pill from every header (chat page, all-chats
  page, and the shared base.html header on all other pages);
- the base.html meter script that painted the pill and
  accumulated study minutes in localStorage every 15 s;
- dhyaanSolved() in the chat page and its two call sites in
  the solve paths (server answer + offline-evaluator answer);
- the language-switch label updater for the pill, and the
  dhyaan_label / dhyaan_today plumbing through app.py's
  template context and api.py's language-switch payload;
- the i18n keys dhyaan_label / dhyaan_today in all 6
  languages;
- the Parent Report's "today" card, whose only data source
  was the Dhyaan localStorage record (minutes + today's
  question count), and the matching WhatsApp share lines.

NOT part of the system and deliberately untouched: the
ordinary Hindi word "dhyaan" inside explanation sentences
(concepts.py, i18n.py), and the menu's own account stats
lines (menu-stat-questions / menu-stat-chats).

These pins keep the system from creeping back, and the
smoke tests prove the solve flow serves exactly as before
minus the counter.
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

_FILES = {
    "index": ROOT / "templates" / "index.html",
    "base": ROOT / "templates" / "base.html",
    "chats": ROOT / "templates" / "chats.html",
    "parent_report": ROOT / "templates" / "parent_report.html",
    "style.css": ROOT / "static" / "style.css",
}
_TEXT = {name: path.read_text(encoding="utf-8")
         for name, path in _FILES.items()}

_FORBIDDEN = (
    "dhyaan-pill", "dhyaanSolved", "ganitra-dhyaan-",
    "dhyaan-text", "ganitraDhyaanPaint",
    "dhyaan_label", "dhyaan_today",
)


@pytest.mark.parametrize("needle", _FORBIDDEN)
def test_no_dhyaan_system_strings_in_templates_or_css(needle):
    for name, text in _TEXT.items():
        assert needle not in text, f"{needle!r} still in {name}"


def test_dhyaan_css_rules_gone():
    css = _TEXT["style.css"]
    assert ".dhyaan-pill" not in css
    assert ".dhyaan-label" not in css
    base = _TEXT["base"]
    assert ".dhyaan-pill" not in base
    assert ".dhyaan-label" not in base


def test_dhyaan_i18n_keys_gone_everywhere():
    import i18n
    for code, strings in i18n.STRINGS.items():
        assert "dhyaan_label" not in strings, code
        assert "dhyaan_today" not in strings, code


def test_parent_report_today_card_gone():
    page = _TEXT["parent_report"]
    assert 'id="parent-minutes"' not in page
    assert 'id="parent-today-count"' not in page
    assert 'id="parent-record-status"' not in page


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_home_serves_without_dhyaan(client):
    body = client.get("/").get_data(as_text=True)
    assert "dhyaan-pill" not in body
    assert "ganitra-dhyaan" not in body
    assert "ganitraDhyaanPaint" not in body


def test_parent_report_serves_without_dhyaan(client):
    r = client.get("/parent-report")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "ganitra-dhyaan" not in body
    assert 'id="parent-minutes"' not in body
    assert 'id="parent-today-count"' not in body


def test_solve_flow_works_without_the_counter(client):
    d = client.post("/api/solve",
                    json={"question": "What is 2 + 2?"}).get_json()
    assert d["ok"] is True
    assert d["result"]["answer"] in ("4", "4.0")
