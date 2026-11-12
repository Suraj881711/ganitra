"""Function plotting with matplotlib (Agg backend, no display needed).

Supports one function, two functions together ("plot x^2 and x+1"), and
— when a definite integral question also asks for a graph — shading the
area under the curve between the integral's bounds.
"""
import hashlib
import json
import os
import re
import sqlite3
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

from .expression_parser import fmt, parse_expression  # noqa: E402

_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "static" / "graphs"

# K9 (Kami audit, 12 Nov 2026): graph PNGs used to pile up forever in
# static/graphs/ — on PythonAnywhere's 512 MB disk that is the one
# slow leak. Filenames are content-hash deterministic, so asking for
# the same function twice reuses one file; only *distinct* functions
# add files. cleanup_old_graphs() deletes files older than 7 days
# that no saved chat still references (a bot turn stores the full
# solve payload, including "image": "graphs/plot_....png", inside
# chats.messages_json). It runs at most once a day, triggered from
# solve_plot()/solve_plot_area(), and never raises — a failed
# cleanup must never break a student's solve.
_CLEANUP_MARKER = (Path(__file__).resolve().parent.parent
                   / ".graphs_last_cleanup")
_CLEANUP_INTERVAL_SECONDS = 24 * 3600
_CLEANUP_MAX_AGE_DAYS = 7
_GRAPH_NAME_RE = re.compile(r"graphs/(plot_[A-Za-z0-9_.\-]+\.png)")


def _db_path(db_path=None):
    """Account DB path: explicit arg, else GANITRA_DB_PATH, else the
    ganitra_users.db beside this project (same rule as accounts.py)."""
    if db_path:
        return Path(db_path)
    env = os.environ.get("GANITRA_DB_PATH", "").strip()
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent / "ganitra_users.db"


def referenced_graph_files(db_path=None):
    """Graph filenames still used by a saved chat, or None when the
    DB cannot be read — in that case the caller must delete nothing,
    because an unreferenced-looking file may still belong to a chat."""
    path = _db_path(db_path)
    if not path.is_file():
        return None
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True,
                              timeout=5)
        try:
            rows = con.execute(
                "SELECT messages_json FROM chats").fetchall()
        finally:
            con.close()
    except Exception:
        return None
    found = set()
    for (blob,) in rows:
        if not blob:
            continue
        found.update(_GRAPH_NAME_RE.findall(blob))
    return found


def cleanup_old_graphs(max_age_days=_CLEANUP_MAX_AGE_DAYS,
                       dry_run=False, db_path=None):
    """Delete unreferenced graph PNGs older than ``max_age_days``.

    Returns {"deleted": [...], "kept_referenced": n, "kept_fresh": n,
    "skipped_no_db": bool, "errors": [...]}. Never raises.
    """
    result = {"deleted": [], "kept_referenced": 0, "kept_fresh": 0,
              "skipped_no_db": False, "errors": []}
    try:
        referenced = referenced_graph_files(db_path)
    except Exception as exc:  # pragma: no cover - defensive
        result["errors"].append(f"db scan: {exc}")
        return result
    if referenced is None:
        result["skipped_no_db"] = True
        return result
    if not _GRAPHS_DIR.is_dir():
        return result
    cutoff = time.time() - max_age_days * 86400
    for fpath in sorted(_GRAPHS_DIR.glob("plot_*.png")):
        try:
            if fpath.name in referenced:
                result["kept_referenced"] += 1
                continue
            if fpath.stat().st_mtime >= cutoff:
                result["kept_fresh"] += 1
                continue
            if not dry_run:
                fpath.unlink()
            result["deleted"].append(fpath.name)
        except Exception as exc:
            result["errors"].append(f"{fpath.name}: {exc}")
    return result


def _maybe_cleanup_graphs():
    """Run the daily graph cleanup at most once per 24 hours.

    Best-effort only: any failure is swallowed, so plotting never
    breaks because of housekeeping. The marker lives in the project
    root (outside static/, so it is never web-served)."""
    try:
        last = float(_CLEANUP_MARKER.read_text().strip() or 0)
    except Exception:
        last = 0
    if time.time() - last < _CLEANUP_INTERVAL_SECONDS:
        return
    try:
        _CLEANUP_MARKER.write_text(str(int(time.time())))
    except Exception:
        return
    try:
        cleanup_old_graphs()
    except Exception:
        pass


def extract_function(question: str) -> str:
    t = question.strip()
    t = re.sub(r"^\s*(please\s+)?(plot|graph|draw)\b", "", t, flags=re.I)
    t = re.sub(r"\b(of|the|function)\b", "", t, flags=re.I)
    t = re.sub(r"^\s*(f\s*\(\s*x\s*\)|y)\s*=", "", t.strip(), flags=re.I)
    return t.strip(" :?")


def _split_functions(text: str):
    """Split 'x^2 and x+1' / 'x^2, sin(x)' into separate function texts.
    Splits only on top-level commas and the word 'and'."""
    parts, depth, cur = [], 0, ""
    i = 0
    text = text.strip()
    while i < len(text):
        ch = text[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if depth == 0 and ch == ",":
            parts.append(cur)
            cur = ""
            i += 1
            continue
        if depth == 0 and re.match(r"\s+and\s+", text[i:]):
            parts.append(cur)
            cur = ""
            i += len(re.match(r"\s+and\s+", text[i:]).group(0))
            continue
        cur += ch
        i += 1
    parts.append(cur)
    return [p.strip(" :") for p in parts if p.strip(" :")]


def _eval_on_grid(expr, var, xs):
    f = sp.lambdify(var, expr, "numpy")
    with np.errstate(all="ignore"):
        ys = f(xs)
    return np.asarray(ys, dtype=float)


def solve_plot(question: str):
    _maybe_cleanup_graphs()
    expr_text = extract_function(question)
    parts = _split_functions(expr_text)
    if len(parts) > 2:  # keep at most two curves
        parts = parts[:2]
    exprs = [parse_expression(p) for p in parts]
    var = next(iter(exprs[0].free_symbols), sp.symbols("x"))

    xs = np.linspace(-10, 10, 800)
    curves = [(e, _eval_on_grid(e, var, xs)) for e in exprs]

    all_ys = np.concatenate([ys for _, ys in curves])
    finite = np.isfinite(all_ys)
    if finite.sum() > 10:
        lo, hi = np.nanpercentile(all_ys[finite], [1, 99])
        pad = max((hi - lo) * 0.4, 1.0)
        ymin, ymax = lo - pad, hi + pad
    else:
        ymin, ymax = -10, 10

    _GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(
        "|".join(str(e) for e in exprs).encode()).hexdigest()[:10]
    fname = f"plot_{digest}.png"
    fpath = _GRAPHS_DIR / fname

    colours = ["#6aa6ff", "#e0a458"]
    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=130)
    for idx, (expr, ys) in enumerate(curves):
        ax.plot(xs, ys, color=colours[idx % len(colours)], linewidth=2,
                label=f"y = {expr}")
    ax.axhline(0, color="#666", linewidth=0.8)
    ax.axvline(0, color="#666", linewidth=0.8)
    ax.set_xlim(-10, 10)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(str(var))
    ax.set_ylabel("y")
    if len(curves) > 1:
        ax.legend(loc="best", fontsize=8)
        ax.set_title(" and ".join(f"y = {e}" for e in exprs))
    else:
        ax.set_title(f"y = {exprs[0]}")
    fig.tight_layout()
    fig.savefig(fpath)
    plt.close(fig)

    label = " and ".join(f"y = {e}" for e in exprs)
    return {
        "type": "plot",
        "op": "graph",
        "expression": " and ".join(str(e) for e in exprs),
        "answer": f"Graph of {label} (x from -10 to 10)",
        "image": f"graphs/{fname}",
        "steps": [
            f"Take sample x values from -10 to 10 and compute "
            + ", ".join(f"y = {e}" for e in exprs) + " for each.",
            "Plot the (x, y) points and join them into "
            + ("curves." if len(exprs) > 1 else "a curve."),
        ],
    }


def solve_plot_area(expr, var, a, b):
    """Graph of y = expr with the area under the curve shaded from a to
    b — used when a definite-integral question also asks for a graph."""
    _maybe_cleanup_graphs()
    xs = np.linspace(float(a) - 2, float(b) + 2, 600)
    ys = _eval_on_grid(expr, var, xs)
    seg_x = np.linspace(float(a), float(b), 300)
    seg_y = _eval_on_grid(expr, var, seg_x)

    _GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(
        f"area|{expr}|{a}|{b}".encode()).hexdigest()[:10]
    fname = f"plot_{digest}.png"
    fpath = _GRAPHS_DIR / fname

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=130)
    ax.plot(xs, ys, color="#6aa6ff", linewidth=2, label=f"y = {expr}")
    ax.fill_between(seg_x, seg_y, 0, color="#e0a458", alpha=0.45,
                    label=f"area from {fmt(a)} to {fmt(b)}")
    ax.axhline(0, color="#666", linewidth=0.8)
    ax.axvline(0, color="#666", linewidth=0.8)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(str(var))
    ax.set_ylabel("y")
    ax.set_title(f"Area under y = {expr} from {fmt(a)} to {fmt(b)}")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(fpath)
    plt.close(fig)
    return f"graphs/{fname}"

