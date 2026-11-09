"""Probability distributions — computed with the stdlib `math` module only
(no scipy), so the Render deployment stays light.

- Normal:  P(X<x), P(X>x), P(a<X<b), z-scores, inverse (value for a
  given left-tail probability).
- Poisson: P(X=k), P(X<=k) for rate lambda.
- Binomial: P(X=k), P(X<=k) for n trials with success probability p.
Every answer shows the formula and the substitution as steps.
"""
import math
import re

from .expression_parser import fmt_num


# ---------------------------------------------------------------- helpers
def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _norm_ppf(p: float) -> float:
    """Inverse normal CDF (Acklam's rational approximation, |err| ~ 1e-9)."""
    if not 0.0 < p < 1.0:
        raise ValueError("probability must be between 0 and 1")
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285984469534e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= phigh:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r
                + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r
                                  + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
             + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def _poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam + k * math.log(lam) - math.lgamma(k + 1))


def _binom_pmf(k: int, n: int, p: float) -> float:
    return math.comb(n, k) * p**k * (1 - p) ** (n - k)


def _params(q: str):
    """Pull named parameters (mean, sd, sigma, mu, lambda, lam, n, p, k)
    plus positional numbers from the question text."""
    out = {}
    patterns = {
        "mean": r"(?:mean|mu|μ)\s*(?:=|is|of|:)?\s*(-?\d+(?:\.\d+)?)",
        "sd": r"(?:standard\s+deviation|sd|sigma|σ)\s*"
              r"(?:=|is|of|:)?\s*(\d+(?:\.\d+)?)",
        "lambda": r"(?:lambda|lam|λ|rate|average\s+rate)\s*"
                  r"(?:=|is|of|:)?\s*(\d+(?:\.\d+)?)",
        "n": r"\bn\s*=\s*(\d+)",
        "p": r"\bp\s*=\s*(\d+(?:\.\d+)?)",
        "k": r"\bk\s*=\s*(\d+)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, q, re.I)
        if m:
            v = float(m.group(1))
            out[key] = int(v) if float(v).is_integer() and key in "nk" \
                else v
    return out


# ---------------------------------------------------------------- normal
def _normal(q: str):
    prm = _params(q)
    mu = prm.get("mean")
    sd = prm.get("sd")
    if mu is None or sd is None:
        return None

    # Inverse: value such that P(X < x) = p  ("find x so that P(X<x)=0.95",
    # "95th percentile", "top 5%")
    m = re.search(r"(?:less\s+than|below|<)\s*(?:x\s*)?(?:=|is)\s*"
                  r"(0?\.\d+)", q) or re.search(
        r"[pP]\s*\(\s*[xX]\s*<\s*[xX]\s*\)\s*=\s*(0?\.\d+)", q)
    pct = re.search(r"(\d+(?:\.\d+)?)\s*(?:th|st|nd|rd)?\s*percentile", q, re.I)
    top = re.search(r"\btop\s+(\d+(?:\.\d+)?)\s*%", q, re.I)
    if m or pct or top:
        if m:
            p = float(m.group(1))
        elif pct:
            p = float(pct.group(1)) / 100.0
        else:
            p = 1.0 - float(top.group(1)) / 100.0
        z = _norm_ppf(p)
        x = mu + z * sd
        steps = [
            f"X ~ N(μ = {fmt_num(mu)}, σ = {fmt_num(sd)}). "
            f"We need x with P(X < x) = {fmt_num(p)}.",
            f"Inverse standard normal: z = Φ⁻¹({fmt_num(p)}) = {z:.4f}",
            f"x = μ + z·σ = {fmt_num(mu)} + {z:.4f} × {fmt_num(sd)}",
        ]
        return {
            "type": "distributions", "op": "normal_inverse",
            "answer": f"x ≈ {x:.4f}", "value": x, "steps": steps,
        }

    # z-score only
    zm = re.search(r"z[\s-]*score\s*(?:of|for)?\s*(-?\d+(?:\.\d+)?)", q, re.I)
    if zm and re.search(r"z[\s-]*score", q, re.I) and \
            not re.search(r"probab|p\s*\(", q, re.I):
        x = float(zm.group(1))
        z = (x - mu) / sd
        steps = [
            "z-score formula: z = (x − μ) / σ",
            f"z = ({fmt_num(x)} − {fmt_num(mu)}) / {fmt_num(sd)}",
            f"z = {z:.4f}",
        ]
        return {
            "type": "distributions", "op": "z_score",
            "answer": f"z = {z:.4f}", "value": z, "steps": steps,
        }

    # Between: P(a < X < b)
    mb = re.search(
        r"between\s+(-?\d+(?:\.\d+)?)\s+and\s+(-?\d+(?:\.\d+)?)", q, re.I) \
        or re.search(r"p\s*\(\s*(-?\d+(?:\.\d+)?)\s*<\s*x\s*<\s*"
                     r"(-?\d+(?:\.\d+)?)\s*\)", q, re.I)
    if mb:
        a, b = float(mb.group(1)), float(mb.group(2))
        za, zb = (a - mu) / sd, (b - mu) / sd
        prob = _norm_cdf(zb) - _norm_cdf(za)
        steps = [
            f"X ~ N(μ = {fmt_num(mu)}, σ = {fmt_num(sd)}). "
            "Standardise with z = (x − μ) / σ.",
            f"z₁ = ({fmt_num(a)} − {fmt_num(mu)}) / {fmt_num(sd)} "
            f"= {za:.4f}",
            f"z₂ = ({fmt_num(b)} − {fmt_num(mu)}) / {fmt_num(sd)} "
            f"= {zb:.4f}",
            f"P({fmt_num(a)} < X < {fmt_num(b)}) = Φ({zb:.4f}) − "
            f"Φ({za:.4f}) = {_norm_cdf(zb):.4f} − {_norm_cdf(za):.4f}",
        ]
        return {
            "type": "distributions", "op": "normal_between",
            "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps,
        }

    # One-sided: P(X < x) / P(X > x) / P(X <= x) ...
    mo = re.search(
        r"p\s*\(\s*x\s*(<=?|>=?)\s*(-?\d+(?:\.\d+)?)\s*\)", q, re.I) \
        or re.search(
            r"(less\s+than|more\s+than|greater\s+than|at\s+most|"
            r"at\s+least|exceeds?|below|above)\s+(-?\d+(?:\.\d+)?)", q, re.I)
    if mo:
        if mo.re.pattern.startswith("p"):
            direction, x = mo.group(1), float(mo.group(2))
            greater = direction in (">", ">=")
        else:
            word, x = mo.group(1).lower(), float(mo.group(2))
            greater = word in ("more than", "greater than", "at least",
                               "exceeds", "exceed", "above")
        z = (x - mu) / sd
        cdf = _norm_cdf(z)
        prob = 1.0 - cdf if greater else cdf
        steps = [
            f"X ~ N(μ = {fmt_num(mu)}, σ = {fmt_num(sd)}). "
            "Standardise with z = (x − μ) / σ.",
            f"z = ({fmt_num(x)} − {fmt_num(mu)}) / {fmt_num(sd)} "
            f"= {z:.4f}",
            f"Φ({z:.4f}) = {cdf:.4f} (area to the left)",
        ]
        if greater:
            steps.append(
                f"P(X > {fmt_num(x)}) = 1 − Φ({z:.4f}) = 1 − {cdf:.4f}")
        else:
            steps.append(f"P(X < {fmt_num(x)}) = Φ({z:.4f})")
        return {
            "type": "distributions", "op": "normal_probability",
            "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps,
        }
    return None


# ---------------------------------------------------------------- poisson
def _poisson(q: str):
    prm = _params(q)
    lam = prm.get("lambda")
    if lam is None:
        return None
    lam = float(lam)
    cumulative = bool(re.search(
        r"at\s+most|no\s+more\s+than|fewer\s+than|"
        r"<=|≤|cumulative", q, re.I))
    # Find the target k: prefer explicit "at most/at least/exactly N",
    # then "X <=/>= N", then the k= parameter. (The lambda value itself
    # must never be mistaken for k.)
    k = prm.get("k")
    if k is None:
        m = re.search(r"(?:exactly|at\s+most|at\s+least)\s+(\d+)", q, re.I)
        if m:
            k = int(m.group(1))
    if k is None:
        m = re.search(r"[xX]\s*(?:<=?|>=?)\s*(\d+)", q)
        if m:
            k = int(m.group(1))
    at_least = bool(re.search(r"at\s+least", q, re.I))
    if k is not None and at_least:
        cdf_below = sum(_poisson_pmf(i, lam) for i in range(k))
        prob = 1.0 - cdf_below
        steps = [
            "Poisson: P(X = k) = e^(−λ) · λ^k / k!, "
            f"with λ = {fmt_num(lam)}.",
            f"P(X ≥ {k}) = 1 − P(X ≤ {k - 1}) = 1 − {cdf_below:.4f}",
        ]
        return {"type": "distributions", "op": "poisson_probability",
                "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps}
    if k is not None and cumulative:
        prob = sum(_poisson_pmf(i, lam) for i in range(k + 1))
        terms = " + ".join(f"P(X={i})" for i in range(k + 1))
        steps = [
            "Poisson: P(X = k) = e^(−λ) · λ^k / k!, "
            f"with λ = {fmt_num(lam)}.",
            f"P(X ≤ {k}) = {terms} = {prob:.4f}",
        ]
        return {"type": "distributions", "op": "poisson_probability",
                "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps}
    if k is not None:
        prob = _poisson_pmf(k, lam)
        steps = [
            "Poisson formula: P(X = k) = e^(−λ) · λ^k / k!",
            f"Substitute λ = {fmt_num(lam)}, k = {k}: "
            f"P(X = {k}) = e^(−{fmt_num(lam)}) · "
            f"{fmt_num(lam)}^{k} / {k}!",
            f"= {math.exp(-lam):.4f} · {lam ** k:.4f} / "
            f"{math.factorial(k)}",
        ]
        return {"type": "distributions", "op": "poisson_probability",
                "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps}
    return None


# ---------------------------------------------------------------- binomial
def _binomial(q: str):
    prm = _params(q)
    n, p, k = prm.get("n"), prm.get("p"), prm.get("k")
    if n is None or p is None:
        m = re.search(
            r"binomial\s+(?:with\s+)?n\s*=\s*(\d+)\s*(?:,|and)\s*p\s*=\s*"
            r"(\d+(?:\.\d+)?)", q, re.I)
        if m:
            n, p = int(m.group(1)), float(m.group(2))
    if n is None or p is None:
        # Plain phrasing: "binomial distribution n = 10, p = 0.5"
        mn = re.search(r"\bn\s*=\s*(\d+)", q)
        mp = re.search(r"\bp\s*=\s*(\d+(?:\.\d+)?)", q)
        if mn and mp:
            n, p = int(mn.group(1)), float(mp.group(1))
    if n is None or p is None:
        return None
    n, p = int(n), float(p)
    if k is None:
        m = re.search(r"[xX]\s*(?:<=?|>=?|=)\s*(\d+)", q) or re.search(
            r"exactly\s+(\d+)", q, re.I) or re.search(
            r"(?:at\s+most|at\s+least)\s+(\d+)", q, re.I)
        if m:
            k = int(m.group(1))
    if k is None:
        return None
    k = int(k)
    cumulative = bool(re.search(
        r"at\s+most|no\s+more\s+than|≤|<=|cumulative", q, re.I)) and \
        not re.search(r"at\s+least", q, re.I)
    at_least = bool(re.search(r"at\s+least", q, re.I))
    if at_least:
        below = sum(_binom_pmf(i, n, p) for i in range(k))
        prob = 1.0 - below
        steps = [
            "Binomial formula: P(X = k) = C(n, k) · p^k · (1−p)^(n−k)",
            f"Substitute n = {n}, p = {fmt_num(p)}.",
            f"P(X ≥ {k}) = 1 − P(X ≤ {k - 1}) = 1 − {below:.4f}",
        ]
    elif cumulative:
        prob = sum(_binom_pmf(i, n, p) for i in range(k + 1))
        steps = [
            "Binomial formula: P(X = k) = C(n, k) · p^k · (1−p)^(n−k)",
            f"Substitute n = {n}, p = {fmt_num(p)} and add the terms "
            f"for k = 0 to {k}.",
            f"P(X ≤ {k}) = {prob:.4f}",
        ]
    else:
        prob = _binom_pmf(k, n, p)
        steps = [
            "Binomial formula: P(X = k) = C(n, k) · p^k · (1−p)^(n−k)",
            f"C({n}, {k}) = {math.comb(n, k)}",
            f"P(X = {k}) = {math.comb(n, k)} · {fmt_num(p)}^{k} · "
            f"{fmt_num(1 - p)}^{n - k}",
        ]
    return {"type": "distributions", "op": "binomial_probability",
            "answer": f"P ≈ {prob:.4f}", "value": prob, "steps": steps}


def solve_distributions(question: str):
    q = question.strip()
    ql = q.lower()
    out = None
    if "poisson" in ql:
        out = _poisson(q)
    elif "binomial" in ql:
        out = _binomial(q)
    elif "normal" in ql or "z-score" in ql or "z score" in ql or \
            "percentile" in ql or re.search(r"\btop\s+\d", ql):
        out = _normal(q)
    if out:
        return out
    return {
        "type": "distributions",
        "op": "unknown",
        "answer": "Tell me the distribution and its numbers, e.g. "
                  "'normal distribution mean 100 sd 15, P(X < 115)', "
                  "'Poisson lambda 3, probability of exactly 2', or "
                  "'binomial n=10 p=0.5, P(X=5)'.",
        "steps": [],
    }


__all__ = ["solve_distributions"]
