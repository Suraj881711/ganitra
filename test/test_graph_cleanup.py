"""Graph cleanup (K9, Kami audit 12 Nov 2026): old, unreferenced
plot PNGs are deleted; files a saved chat still shows, fresh files,
and everything when the DB cannot be read are kept."""
import json
import os
import sqlite3
import time

import solver.plotting as plotting


def _make_db(path, referenced_names):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE chats (id INTEGER PRIMARY KEY,"
                " messages_json TEXT NOT NULL DEFAULT '[]')")
    msgs = [{"role": "bot",
             "result": {"type": "plot", "image": f"graphs/{n}"}}
            for n in referenced_names]
    con.execute("INSERT INTO chats (messages_json) VALUES (?)",
                (json.dumps(msgs),))
    con.commit()
    con.close()


def _make_png(graphs_dir, name, age_days):
    fpath = graphs_dir / name
    fpath.write_bytes(b"fake-png")
    old = time.time() - age_days * 86400
    os.utime(fpath, (old, old))
    return fpath


def test_cleanup_deletes_only_old_unreferenced(tmp_path, monkeypatch):
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    monkeypatch.setattr(plotting, "_GRAPHS_DIR", graphs_dir)
    db = tmp_path / "test_users.db"
    _make_db(db, ["plot_kept.png"])
    old_gone = _make_png(graphs_dir, "plot_old.png", 10)
    old_kept = _make_png(graphs_dir, "plot_kept.png", 10)
    fresh = _make_png(graphs_dir, "plot_fresh.png", 1)

    result = plotting.cleanup_old_graphs(db_path=db)

    assert result["deleted"] == ["plot_old.png"]
    assert result["kept_referenced"] == 1
    assert result["kept_fresh"] == 1
    assert result["skipped_no_db"] is False
    assert result["errors"] == []
    assert not old_gone.exists()
    assert old_kept.exists()
    assert fresh.exists()


def test_cleanup_skips_everything_without_db(tmp_path, monkeypatch):
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    monkeypatch.setattr(plotting, "_GRAPHS_DIR", graphs_dir)
    stale = _make_png(graphs_dir, "plot_old.png", 30)

    result = plotting.cleanup_old_graphs(
        db_path=tmp_path / "no_such.db")

    assert result["skipped_no_db"] is True
    assert result["deleted"] == []
    assert stale.exists()


def test_cleanup_dry_run_deletes_nothing(tmp_path, monkeypatch):
    graphs_dir = tmp_path / "graphs"
    graphs_dir.mkdir()
    monkeypatch.setattr(plotting, "_GRAPHS_DIR", graphs_dir)
    db = tmp_path / "test_users.db"
    _make_db(db, [])
    stale = _make_png(graphs_dir, "plot_old.png", 10)

    result = plotting.cleanup_old_graphs(dry_run=True, db_path=db)

    assert result["deleted"] == ["plot_old.png"]
    assert stale.exists()


def test_maybe_cleanup_runs_at_most_once_a_day(tmp_path, monkeypatch):
    marker = tmp_path / ".graphs_last_cleanup"
    monkeypatch.setattr(plotting, "_CLEANUP_MARKER", marker)
    calls = []
    monkeypatch.setattr(plotting, "cleanup_old_graphs",
                        lambda: calls.append(1))

    plotting._maybe_cleanup_graphs()
    plotting._maybe_cleanup_graphs()

    assert len(calls) == 1
    assert marker.exists()
