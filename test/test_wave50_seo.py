"""Wave 50: SEO basics — robots.txt, sitemap.xml, meta/OG tags,
JSON-LD on the homepage.

Pinned here:

- /robots.txt is 200 text/plain, allows all and points at the
  sitemap on the live origin;
- /sitemap.xml is 200, parses as XML, and lists ONLY pages an
  anonymous visitor can open (each listed path is re-fetched and
  must be 200) — no login-gated pages (/papers, /practice-mode,
  /chats, /account), no API routes, no personal session pages;
- the homepage (anonymous sign-in view AND the signed-in chat
  view) carries the meta description, Open Graph tags with the
  existing frozen logo file as og:image, a canonical URL, and
  the WebApplication JSON-LD block.
"""
import re
import xml.etree.ElementTree as ET

import pytest

ORIGIN = "https://suraj881711.pythonanywhere.com"
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@pytest.fixture()
def anon_client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "anon.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    c.post("/signup", data={
        "name": "W50 SEO Tester", "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "w50-seo-pass"})
    return c


def test_robots_txt(anon_client):
    r = anon_client.get("/robots.txt")
    assert r.status_code == 200
    assert r.mimetype == "text/plain"
    body = r.get_data(as_text=True)
    assert "User-agent: *" in body
    assert "Allow: /" in body
    assert f"Sitemap: {ORIGIN}/sitemap.xml" in body


def _sitemap_paths(anon_client):
    r = anon_client.get("/sitemap.xml")
    assert r.status_code == 200
    assert "xml" in r.mimetype
    root = ET.fromstring(r.get_data(as_text=True))
    locs = [el.text for el in root.findall("sm:url/sm:loc", SITEMAP_NS)]
    assert locs, "sitemap must list at least the homepage"
    paths = []
    for loc in locs:
        assert loc.startswith(ORIGIN), loc
        paths.append(loc[len(ORIGIN):] or "/")
    return paths


def test_sitemap_lists_home_and_public_pages(anon_client):
    paths = _sitemap_paths(anon_client)
    assert "/" in paths
    for expected in ("/topics", "/board", "/practice", "/test"):
        assert expected in paths


def test_sitemap_excludes_gated_api_and_personal(anon_client):
    paths = _sitemap_paths(anon_client)
    for banned in ("/papers", "/practice-mode", "/chats", "/account",
                   "/history", "/mistakes", "/parent-report"):
        assert banned not in paths
    assert not any(p.startswith("/api") for p in paths)


def test_sitemap_urls_all_return_200_anonymously(anon_client):
    for path in _sitemap_paths(anon_client):
        r = anon_client.get(path)
        assert r.status_code == 200, (path, r.status_code)


def _assert_homepage_meta(html):
    assert 'name="description"' in html
    assert "free maths help for Classes 6" in html
    assert 'property="og:title"' in html
    assert 'property="og:type" content="website"' in html
    assert 'property="og:image"' in html
    assert f'content="{ORIGIN}/static/logo-full.png"' in html
    assert 'rel="canonical"' in html
    assert f'href="{ORIGIN}/"' in html
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>',
                  html, re.S)
    assert m, "homepage must carry JSON-LD"
    assert '"WebApplication"' in m.group(1)
    assert '"name": "Ganitra"' in m.group(1)
    assert '"EducationalApplication"' in m.group(1)


def test_homepage_meta_anonymous(anon_client):
    r = anon_client.get("/")
    assert r.status_code == 200
    _assert_homepage_meta(r.get_data(as_text=True))


def test_homepage_meta_signed_in(client):
    r = client.get("/")
    assert r.status_code == 200
    _assert_homepage_meta(r.get_data(as_text=True))
