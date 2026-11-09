"""Function plotting with matplotlib (Agg backend, no display needed)."""
import hashlib
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402

from .expression_parser import parse_expression  # noqa: E402

_GRAPHS_DIR = Path(__file__).resolve().parent.parent / "static" / "graphs"


def extract_function(question: str) -> str:
    t = question.strip()
    t = re.sub(r"^\s*(please\s+)?(plot|graph|draw)\b", "", t, flags=re.I)
    t = re.sub(r"\b(of|the|function)\b", "", t, flags=re.I)
    t = re.sub(r"^\s*(f\s*\(\s*x\s*\)|y)\s*=", "", t.strip(), flags=re.I)
    return t.strip(" :?")


def solve_plot(question: str):
    expr_text = extract_function(question)
    expr = parse_expression(expr_text)
    var = next(iter(expr.free_symbols), sp.symbols("x"))

    f = sp.lambdify(var, expr, "numpy")
    xs = np.linspace(-10, 10, 800)
    with np.errstate(all="ignore"):
        ys = f(xs)
    ys = np.asarray(ys, dtype=float)
    finite = np.isfinite(ys)
    if finite.sum() > 10:
        lo, hi = np.nanpercentile(ys[finite], [1, 99])
        pad = max((hi - lo) * 0.4, 1.0)
        ymin, ymax = lo - pad, hi + pad
    else:
        ymin, ymax = -10, 10

    _GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
    digest = hashlib.md5(str(expr).encode()).hexdigest()[:10]
    fname = f"plot_{digest}.png"
    fpath = _GRAPHS_DIR / fname

    fig, ax = plt.subplots(figsize=(6.4, 4.2), dpi=130)
    ax.plot(xs, ys, color="#6aa6ff", linewidth=2)
    ax.axhline(0, color="#666", linewidth=0.8)
    ax.axvline(0, color="#666", linewidth=0.8)
    ax.set_xlim(-10, 10)
    ax.set_ylim(ymin, ymax)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel(str(var))
    ax.set_ylabel("y")
    ax.set_title(f"y = {expr}")
    fig.tight_layout()
    fig.savefig(fpath)
    plt.close(fig)

    return {
        "type": "plot",
        "op": "graph",
        "expression": str(expr),
        "answer": f"Graph of y = {expr} (x from -10 to 10)",
        "image": f"graphs/{fname}",
        "steps": [
            f"Take sample x values from -10 to 10 and compute "
            f"y = {expr} for each.",
            "Plot the (x, y) points and join them into a curve.",
        ],
    }
