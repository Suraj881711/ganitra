"""Wave 218 (Suraj, 23 Nov 2026): Group Study leave option.

Any member can leave a group. If the admin leaves, admin
passes to the earliest-joined remaining member; if nobody
remains, the group closes. (The creation page was also made
WhatsApp-simple in this wave — template only, no test here.)
"""
import pytest

import groups as study_groups
import solver.answer_cache as cache


@pytest.fixture(autouse=True)
def _clean_caches():
    cache.clear_cache()
    yield
    cache.clear_cache()


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH", str(tmp_path / "users.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    monkeypatch.delenv("GANITRA_GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY", raising=False)
    from app import create_app
    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


def _signup(app, name):
    client = app.test_client()
    r = client.post("/signup", data={
        "name": name, "class": "8", "board": "CBSE",
        "goal": "Doctor", "hobby": "Cricket", "favourite": "Pizza",
        "password": "test-pass-218"})
    assert r.status_code == 302, (name, r.status_code)
    return client


def _uid(client):
    with client.session_transaction() as sess:
        return sess["user_id"]


@pytest.fixture()
def trio(app):
    admin = _signup(app, "Admin Anita")
    a = _signup(app, "Asha Verma")
    b = _signup(app, "Ravi Kumar")
    admin.post("/groups/phone", data={"phone": "9800000000"})
    a.post("/groups/phone", data={"phone": "9811111111"})
    b.post("/groups/phone", data={"phone": "9822222222"})
    r = admin.post("/groups/create", data={
        "name": "Maths Dost",
        "member_phones": "9811111111\n9822222222"})
    assert r.status_code in (200, 302)
    gid = study_groups.list_groups_for(_uid(a))[0]["id"]
    return gid, _uid(admin), _uid(a), _uid(b), admin, a


def test_member_can_leave(trio):
    gid, admin_id, a_id, b_id, _ac, _a = trio
    ok, err = study_groups.leave_group(gid, b_id)
    assert ok and err is None
    assert not study_groups.is_member(gid, b_id)
    assert study_groups.is_member(gid, a_id)


def test_admin_leave_passes_admin_to_earliest_member(trio):
    gid, admin_id, a_id, b_id, _ac, _a = trio
    ok, err = study_groups.leave_group(gid, admin_id)
    assert ok and err is None
    group = study_groups.get_group(gid)
    assert group["admin_id"] == a_id
    assert group["closed_at"] is None


def test_last_member_leaving_closes_group(trio):
    gid, admin_id, a_id, b_id, _ac, _a = trio
    assert study_groups.leave_group(gid, a_id)[0]
    assert study_groups.leave_group(gid, b_id)[0]
    assert study_groups.leave_group(gid, admin_id)[0]
    group = study_groups.get_group(gid)
    assert group["closed_at"] is not None


def test_non_member_cannot_leave(trio):
    gid, admin_id, a_id, b_id, _ac, _a = trio
    ok, err = study_groups.leave_group(gid, 99999)
    assert not ok and err


def test_leave_route_redirects_member_to_groups_list(trio):
    gid, admin_id, a_id, b_id, _ac, a_client = trio
    r = a_client.post(f"/groups/{gid}/leave")
    assert r.status_code == 302
    assert not study_groups.is_member(gid, a_id)
