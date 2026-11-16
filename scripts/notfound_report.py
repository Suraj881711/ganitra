"""Wave 90: owner report for the not-found learning log.

Run from the PythonAnywhere console (or any shell next to the
app):

    python scripts/notfound_report.py                 # top 20
    python scripts/notfound_report.py --limit 50
    python scripts/notfound_report.py --export nf.jsonl

It prints the questions students asked that ended in "Answer
not found", grouped by the bank normalisation (one row per
distinct question, repeats counted), most-asked first — the
target list for the next solver wave. --export writes every
logged row as JSONL (question_norm, question_text, language,
student_class, stage, terminal_kind, hits, first_seen,
last_seen) for wave-building use.

Read-only: the report never creates or modifies the database
(a missing DB / table simply reads as an empty log). The DB
path follows the same rule as accounts.py (GANITRA_DB_PATH
env, else ganitra_users.db beside the project); --db overrides
it. Stdlib + the app's own notfound_log reader only.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from notfound_log import all_rows, top_failures  # noqa: E402


def _when(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime(
            "%d %b %Y")
    except (TypeError, ValueError, OSError):
        return "?"


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Top grouped not-found questions (Wave 90).")
    parser.add_argument("--limit", type=int, default=20,
                        help="how many rows to print (default 20)")
    parser.add_argument("--db", default=None,
                        help="DB path (default: accounts.db_path())")
    parser.add_argument("--export", default=None,
                        help="also write every row to this"
                             " JSONL file")
    args = parser.parse_args(argv)

    rows = top_failures(limit=args.limit, db_path=args.db)
    total_rows = all_rows(db_path=args.db)
    total_hits = sum(r["hits"] for r in total_rows)

    if args.export:
        with open(args.export, "w", encoding="utf-8") as fh:
            for row in total_rows:
                fh.write(json.dumps(row, ensure_ascii=False)
                         + "\n")
        print(f"Exported {len(total_rows)} rows to"
              f" {args.export}")

    if not total_rows:
        print("No not-found questions logged yet.")
        return 0

    print(f"Not-found log: {len(total_rows)} distinct questions,"
          f" {total_hits} total asks. Top {len(rows)}:")
    print()
    for i, row in enumerate(rows, 1):
        cls = row["student_class"]
        cls_text = f"Class {cls}" if cls is not None else "—"
        print(f"{i:>3}. x{row['hits']:<4} [{cls_text},"
              f" {row['language'] or '?'},"
              f" {row['terminal_kind'] or row['stage']},"
              f" last {_when(row['last_seen'])}]")
        print(f"     {row['question_text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
