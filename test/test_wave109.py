"""Wave 109 (17 Nov 2026): the chat page's main inline script
did not parse — one closing brace was missing at the end of
``ocrImageSmart`` in templates/index.html, so the browser threw
"Unexpected token ')'" and the WHOLE script died: the composer
fell back to a classic full-page POST and every chat feature
(menu stats, voice, photo, in-page answers) silently stopped.

The fix restored the single ``}``. This test is the permanent
guard: it renders the real pages through the test client,
extracts every inline <script> block that is JavaScript (not
JSON-LD / importmap, not an external src) and syntax-checks
each one with ``node --check`` — the exact check that would
have caught Wave 109's bug the day it was merged.
"""
import re
import shutil
import subprocess

import pytest


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


def _signup(client):
    r = client.post("/signup", data={
        "name": "W109 Syntax Tester", "class": "10",
        "board": "CBSE", "goal": "Doctor", "hobby": "Cricket",
        "favourite": "Pizza", "password": "w109-syntax-pass"})
    assert r.status_code in (200, 302)


def _js_blocks(html):
    """Inline JavaScript bodies: skip JSON-LD / importmap data
    blocks and external scripts (their body is empty anyway)."""
    out = []
    for attrs, body in re.findall(
            r"<script([^>]*)>(.*?)</script>", html, re.S):
        if "ld+json" in attrs or "importmap" in attrs:
            continue
        if "src=" in attrs:
            continue
        if body.strip():
            out.append(body)
    return out


def _assert_scripts_parse(client, tmp_path, path, min_biggest=0):
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    html = client.get(path).get_data(as_text=True)
    blocks = _js_blocks(html)
    assert blocks, f"{path}: no inline JS blocks found to check"
    assert max(len(b) for b in blocks) >= min_biggest, (
        f"{path}: biggest inline block is only "
        f"{max(len(b) for b in blocks)} chars — the main script "
        "was not among them, so this guard would pass vacuously")
    failures = []
    for i, body in enumerate(blocks):
        f = tmp_path / f"block_{i}.js"
        f.write_text(body, encoding="utf-8")
        p = subprocess.run([node, "--check", str(f)],
                           capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            first = (p.stderr or "").strip().splitlines()
            failures.append(f"block {i} ({len(body)} chars): "
                            + " | ".join(first[:3]))
    assert not failures, (
        f"{path}: inline script(s) do not parse:\n"
        + "\n".join(failures))


def test_wave109_chat_page_inline_scripts_parse(client, tmp_path):
    _signup(client)
    # The chat page's main script is ~100k chars; demanding a
    # block at least half that size proves the guard really
    # checked the main script and not just the small helpers.
    _assert_scripts_parse(client, tmp_path, "/", min_biggest=50_000)


def test_wave109_chats_page_inline_scripts_parse(client, tmp_path):
    _signup(client)
    _assert_scripts_parse(client, tmp_path, "/chats",
                          min_biggest=5_000)


def test_wave109_account_page_inline_scripts_parse(client, tmp_path):
    _signup(client)
    _assert_scripts_parse(client, tmp_path, "/account")
