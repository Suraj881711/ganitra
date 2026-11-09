"""Function plotting with matplotlib (Agg backend, no display needed).

Supports one function, two functions together ("plot x^2 and x+1"), and
— when a definite integral question also asks for a graph — shading the
area under the curve between the integral's bounds.
"""
import hashlib
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

from .expression_parser import fmt, parse_expression  # noqa: E402

_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "static" / "graphs"


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

