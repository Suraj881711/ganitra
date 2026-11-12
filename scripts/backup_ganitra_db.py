"""Weekly-safe backup for Ganitra's account database (K9 companion,
Kami audit 12 Nov 2026 — Suraj's rule: "data ki problem nahi honi
chahiye").

Run from the PythonAnywhere console (or any shell next to the app):

    python scripts/backup_ganitra_db.py

It copies ``ganitra_users.db`` with SQLite's own backup API, so the
copy is consistent even while the site is running — a plain file
copy of a live SQLite file can be corrupt. Backups land in
``backups/ganitra_users_YYYYMMDD-HHMMSS.db`` and only the newest 4
are kept, so backups themselves never fill the 512 MB disk.

Nothing here touches the live site or the running app: no routes,
no imports from app.py, stdlib only. The DB path follows the same
rule as accounts.py (GANITRA_DB_PATH env, else ganitra_users.db
beside the project).
"""
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

KEEP_NEWEST = 4


def db_path():
    env = os.environ.get("GANITRA_DB_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "ganitra_users.db"


def backup(db=None, dest_dir=None):
    src = Path(db) if db else db_path()
    if not src.is_file():
        raise SystemExit(f"DB not found: {src}")
    out_dir = Path(dest_dir) if dest_dir else src.parent / "backups"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = out_dir / f"ganitra_users_{stamp}.db"
    source = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    try:
        target = sqlite3.connect(dest)
        try:
            source.backup(target)
        finally:
            target.close()
    finally:
        source.close()
    kept = sorted(out_dir.glob("ganitra_users_*.db"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    for stale in kept[KEEP_NEWEST:]:
        stale.unlink()
    return dest


if __name__ == "__main__":
    made = backup()
    print(f"Backup saved: {made}")
