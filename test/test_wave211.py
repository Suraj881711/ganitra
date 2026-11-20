"""Wave 211: the classic /solve page honours an explicit
in-message language request again — in BOTH directions.

Root cause (traced, not guessed): the angle-sum serve itself
was never wrong (solver geometry w103_angle_sum, answer 180°,
identical on the chat path, where Wave 107 works). The /solve
route also decided the language correctly — session lang,
advice and UI strings all followed the request. What was lost
was the EXPLANATION surface: Wave 208's answer-page cleanup
removed the `{% if explanation %}` block from answer.html as
"filler", so the explanation the route still computes in the
requested language was rendered NOWHERE. A Hindi question with
"answer in English" therefore got a classic page whose summary
line could never be the English one (the pre-Wave-208 tree
passes test_wave107; the Wave-208 tree fails it).

The fix is failure-only: answer.html renders the one-line
explanation again ONLY when the serve carried an explicit
language request (the route passes lang_requested), in its
pre-208 position, with Jinja whitespace control so a
no-request page stays byte-identical to the Wave 208 page
(verified byte-for-byte against the pre-fix tree for English,
Hindi, algebra and percent no-request serves, and for a
request serve whose result is quiet). Serves with no request,
quiet (one-line) serves, the chat path and the photo page
(which renders answer.html without a request) are untouched.
"""
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    return application.test_client()


def _page(client, question):
    return client.post(
        "/solve", data={"question": question}
    ).get_data(as_text=True)


TRIANGLE_EN = "What is the sum of angles of a triangle?"
TRIANGLE_HI = "त्रिभुज के कोणों का योग कितना होता है?"
AGES = ("Ten years ago, a father was twelve times as old as "
        "his son and ten years hence, he will be twice as old "
        "as his son. Find their present ages.")

EN_GEOMETRY = "Using the relevant area/volume formulae"
HI_GEOMETRY = "संबंधित क्षेत्रफल"


# --- 1. The fixed case, both directions -----------------------

def test_hindi_question_english_request_shows_english_line(
        client):
    html = _page(client, TRIANGLE_HI + " answer in English")
    assert 'class="explain"' in html
    assert EN_GEOMETRY in html
    assert HI_GEOMETRY not in html
    # The serve itself is unchanged: same answer, still 180°.
    assert "180°" in html


def test_english_question_hindi_request_shows_hindi_line(
        client):
    html = _page(client, TRIANGLE_EN + " Answer in Hindi")
    assert 'class="explain"' in html
    assert HI_GEOMETRY in html
    assert EN_GEOMETRY not in html
    assert "180" in html


# --- 2. No request: the Wave 208 page stands ------------------

def test_no_request_hindi_question_has_no_explanation_block(
        client):
    html = _page(client, TRIANGLE_HI)
    # No explanation block at all (the Wave 208 format lock),
    # while the page itself is still the Hindi page.
    assert 'class="explain"' not in html
    assert EN_GEOMETRY not in html
    assert "180°" in html


def test_no_request_english_question_has_no_explanation_block(
        client):
    html = _page(client, TRIANGLE_EN)
    assert 'class="explain"' not in html
    assert EN_GEOMETRY not in html
    assert "180°" in html


def test_request_on_quiet_serve_still_has_no_explanation_block(
        client):
    # An unsolved question is a quiet one-line serve: the route
    # passes explanation=None, so even WITH a request there is
    # no block to bring back.
    html = _page(client, AGES + " Answer in Hindi")
    assert 'class="explain"' not in html


# --- 3. Other families honour the request the same way --------

def test_percent_family_hindi_question_english_request(client):
    # Wave 207's native Indic percent serve (applied family,
    # not geometry/facts): the summary line follows the
    # request into English.
    html = _page(client, "240 का 15% कितना है? answer in English")
    assert 'class="explain"' in html
    assert "Working it out step by step gives 36" in html
    assert "36" in html


def test_percent_family_no_request_has_no_explanation_block(
        client):
    html = _page(client, "240 का 15% कितना है?")
    assert 'class="explain"' not in html
    assert "36" in html


def test_equation_family_english_question_hindi_request(
        client):
    # Algebra family, the into-Hindi direction.
    html = _page(client, "3x + 5 = 20, answer in Hindi")
    assert 'class="explain"' in html
    assert "समीकरण को चरण-दर-चरण हल करने से" in html
    assert "x = 5" in html
