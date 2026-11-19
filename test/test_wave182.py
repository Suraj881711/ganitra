"""Wave 182: session-cookie bloat fix + Wave 178 end-to-end.

Bug (live, Deploy-44): POST /api/solve with an exact paper
request ("Mp board ka maths ka paper chahiye 12th class ka
2025") returned PythonAnywhere's 502 page. The PA error log
showed no traceback — only Werkzeug warnings that the Flask
'session' cookie was too large (4,192 / 5,648 bytes against
the 4,093 limit). Root cause: a paper card carries the
whole typed paper in its steps (~8-11 KB JSON) and the
routes store the full result in session["last_result"], so
ONE paper serve bloated the cookie past the limit and it
GREW with a bigger second paper (4,170 -> 5,727 bytes in
the local repro).

Fix: a paper card is deterministic — paper_requests
rebuilds it from (paper_id, flavour, year note) — so the
session stores only that small reference
(paper_requests.paper_session_ref). app.py's Wave-182
hooks slim last_result to the reference after every
request and expand it back to the full card at the start
of the next one, so /download, /solution/print and the
follow-up layers read the exact full body as before.

These tests pin:
- both live paper phrasings serve 200 + the right paper,
  with the session cookie under 4,000 bytes after each;
- five paper asks in a row keep the cookie under 4,000;
- the stored last_result is the small reference, yet
  /download still returns the full paper;
- the ref <-> card round-trip is exact for every paper
  in every flavour, with and without a year note;
- Wave 178 variation really triggers end-to-end through
  /api/solve in one session (guidance + knowledge asked
  twice: the 2nd serve differs, core content unchanged).
"""
import pytest

SIGNUP = {"name": "W182 User", "class": "12", "board": "MP Board",
          "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
          "password": "w182-pass"}

MP_Q = "Mp board ka maths ka paper chahiye 12th class ka 2025"
CBSE_Q = "CBSE class 10 maths paper 2025"
COOKIE_CAP = 4000


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "mpl"))
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    c = app.test_client()
    r = c.post("/signup", data=SIGNUP)
    assert r.status_code == 302
    return c


def _session_cookie_len(response):
    """Length of the session cookie VALUE in the response's
    Set-Cookie header, or None when the response did not
    (re)send the session cookie."""
    for header in response.headers.getlist("Set-Cookie"):
        if header.startswith("session="):
            return len(header.split(";")[0].split("=", 1)[1])
    return None


def _ask(client, question, **kw):
    body = {"question": question}
    body.update(kw)
    return client.post("/api/solve", json=body)


def _result(response):
    return (response.get_json() or {}).get("result") or {}


# ---------------------------------------------------------------
# The 502 fix
# ---------------------------------------------------------------

def test_live_paper_phrasings_serve_and_cookie_stays_small(client):
    r = _ask(client, MP_Q)
    assert r.status_code == 200
    res = _result(r)
    assert res.get("fallback_kind") == "paper"
    assert res.get("paper_id") == "mpbse-12-2025"
    assert len(res.get("steps") or []) > 20  # full paper served
    n = _session_cookie_len(r)
    assert n is not None and n < COOKIE_CAP, n

    r = _ask(client, CBSE_Q)
    assert r.status_code == 200
    res = _result(r)
    assert res.get("fallback_kind") == "paper"
    assert res.get("paper_id") == "cbse-10-2025"
    assert len(res.get("steps") or []) > 20
    n = _session_cookie_len(r)
    assert n is not None and n < COOKIE_CAP, n


def test_five_paper_asks_in_a_row_keep_cookie_under_cap(client):
    asks = [MP_Q, CBSE_Q, "RBSE class 12 maths paper 2025",
            MP_Q, "CBSE class 12 maths paper 2024"]
    for q in asks:
        r = _ask(client, q)
        assert r.status_code == 200
        assert _result(r).get("fallback_kind") == "paper"
        n = _session_cookie_len(r)
        if n is not None:
            assert n < COOKIE_CAP, (q, n)
    # The stored last_result is the small reference, not the
    # paper body.
    with client.session_transaction() as sess:
        stored = sess.get("last_result") or {}
    assert stored.get("fallback_kind") == "paper"
    assert stored.get("steps") == []
    assert "_paper_flavour" in stored


def test_download_after_paper_serve_returns_full_paper(client):
    _ask(client, MP_Q)
    r = client.get("/download")
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    # The full typed paper, not just the card title.
    assert len(body) > 4000
    assert "Maximum Marks" in body


def test_paper_ref_round_trip_is_exact():
    import papers_data
    from paper_requests import (_paper_card, expand_paper_ref,
                                paper_session_ref)
    notes = {
        "en": "Note: the 2024 paper is not in the library yet "
              "— this is the 2025 paper.",
        "roman": "Note: 2024 ka paper abhi library me nahi "
                 "hai — ye 2025 wala paper hai.",
        "dev": "नोट: 2024 का पेपर अभी लाइब्रेरी में नहीं है "
               "— यह 2025 वाला पेपर है।",
    }
    for paper in papers_data.PAPERS:
        for flavour in ("en", "roman", "dev"):
            for note in (None, notes[flavour]):
                card = _paper_card(paper, flavour, note)
                ref = paper_session_ref(card)
                assert ref is not None
                assert expand_paper_ref(ref) == card


def test_non_paper_results_are_never_slimmed():
    from paper_requests import paper_session_ref
    solved = {"type": "Ganitra", "op": "evaluate",
              "answer": "4", "steps": ["2 + 2 = 4"],
              "fallback_kind": None}
    assert paper_session_ref(solved) is None
    plain = {"type": "Ganitra", "op": "paper_ask_board",
             "answer": "Which board?", "steps": [],
             "fallback": True, "fallback_kind": "paper",
             "plain": True}
    assert paper_session_ref(plain) is None


# ---------------------------------------------------------------
# Wave 178 end-to-end (one logged-in session, /api/solve)
# ---------------------------------------------------------------

def _assert_varied(first, second):
    assert second != first
    assert second.get("w178_repeat") == 2
    # Core content unchanged: same answer, and every base
    # step still present, in order, inside the varied card.
    assert second.get("answer") == first.get("answer")
    base = list(first.get("steps") or [])
    shown = list(second.get("steps") or [])
    it = iter(shown)
    assert all(any(s == step for s in it) for step in base)


def test_wave178_guidance_repeat_varies_end_to_end(client):
    r1 = _result(_ask(client, "maths me kya scope hai"))
    r2 = _result(_ask(client, "maths me kya scope hai"))
    assert r1.get("fallback_kind") == "guidance"
    assert r1.get("w178_repeat") is None
    _assert_varied(r1, r2)


def test_wave178_knowledge_repeat_varies_end_to_end(client):
    r1 = _result(_ask(client, "0 ki khoj kisne ki hai"))
    r2 = _result(_ask(client, "0 ki khoj kisne ki hai"))
    assert r1.get("fallback_kind") == "history"
    assert r1.get("meta_id") == "zero"
    assert r1.get("w178_repeat") is None
    _assert_varied(r1, r2)


def test_wave178_repeat_varies_with_chat_id_too(client):
    r1 = _result(_ask(client, "0 ki khoj kisne ki hai",
                      chat_id=5))
    r2 = _result(_ask(client, "0 ki khoj kisne ki hai",
                      chat_id=5))
    assert r1.get("w178_repeat") is None
    _assert_varied(r1, r2)
