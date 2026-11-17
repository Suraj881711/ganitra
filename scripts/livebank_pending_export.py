"""Wave 117: pending-verification export for the Live Bank.

Run from the PythonAnywhere console (or any shell next to
the app):

    python scripts/livebank_pending_export.py OUT.jsonl
    python scripts/livebank_pending_export.py OUT.jsonl --db PATH

Writes every PENDING Live Bank item (questions an AI brain
answered at ask time — never served to anyone) as JSONL in
the master bank's own item shape:

    {live_bank_id, question, question_norm, lang, steps,
     final_answer, kind, source, hits, first_seen, last_seen}

This file is the hand-off the 2-hourly databank cron
consumes: each item goes through the databank's verify.py
exactly like a generated item; the ones that pass are
imported into the master bank and flipped to "verified" in
the live store (livebank.set_status). Read-only: the export
never modifies the database (a missing DB / table simply
reads as an empty store). The DB path follows the same rule
as accounts.py (GANITRA_DB_PATH env, else ganitra_users.db
beside the project); --db overrides it. Stdlib + the app's
own livebank reader only.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import livebank  # noqa: E402


def main():
    parser = argparse.ArgumentParser(
        description="Export pending Live Bank items as JSONL")
    parser.add_argument("out", help="output .jsonl path")
    parser.add_argument("--db", default=None,
                        help="accounts DB path (default: the "
                             "app's own rule)")
    parser.add_argument("--limit", type=int, default=None,
                        help="max items (default: all pending)")
    args = parser.parse_args()
    count = livebank.write_pending_export(
        args.out, limit=args.limit, db_path=args.db)
    print(f"{count} pending item(s) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
