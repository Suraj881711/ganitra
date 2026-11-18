"""Sequences & series: AP/GP nth term and sums, sums of natural
numbers / squares / cubes."""
import re

import sympy as sp

from .expression_parser import fmt_num


# Wave 42: Devanagari digits (०१२३४५६७८९) -> ASCII, for parsing
# Hindi questions that write their numbers in Devanagari.
_DEV_DIGITS_42 = {ord("०") + i: str(i) for i in range(10)}


def _parse_series(text: str):
    """Numbers of an explicit series like '2, 5, 8' (stops at '...' etc.)."""
    m = re.search(r"(-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?)+)", text)
    if not m:
        return []
    return [float(v) if "." in v else int(v)
            for v in re.findall(r"-?\d+(?:\.\d+)?", m.group(1))]


def _classify(terms):
    if len(terms) >= 3:
        diffs = [terms[i + 1] - terms[i] for i in range(len(terms) - 1)]
        if all(d == diffs[0] for d in diffs):
            return "AP", diffs[0]
        if terms[0] != 0:
            ratios = [terms[i + 1] / terms[i]
                      for i in range(len(terms) - 1)]
            if all(abs(r - ratios[0]) < 1e-12 for r in ratios):
                return "GP", ratios[0]
    if len(terms) == 2:
        return "AP", terms[1] - terms[0]
    return None, None


def _get_params(q):
    """a=.., d=../r=.., n=.. style parameters."""
    out = {}
    for name in ("a", "d", "r", "n"):
        m = re.search(rf"\b{name}\s*=\s*(-?\d+(?:\.\d+)?)", q)
        if m:
            v = m.group(1)
            out[name] = float(v) if "." in v else int(v)
    return out


def _ordinal(n):
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}" + {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def _wave65_sequences(q):
    """Wave 65: AP/GP forms the trilingual battery exposed —
    a GP term given backwards to its first term, the AP
    term-count behind a stated sum, the slot-stated AP
    ("first term 5, common difference 3 and 10 terms") asked
    for its last term, and an nth-term formula evaluated at
    a stated n. Each is gated on its full phrasing."""
    N = r"(-?\d+(?:\.\d+)?)"
    # GP: nth term and ratio given, first term asked.
    m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term\s+of\s+(?:a\s+"
                  r"|the\s+)?gp\s+is\s+" + N, q)
    mr = re.search(r"common\s+ratio\s+(?:is\s+)?" + N, q)
    if m and mr and "first term" in q:
        n, tn, r = int(m.group(1)), float(m.group(2)), \
            float(mr.group(1))
        if r:
            a = tn / r ** (n - 1)
            a = int(a) if a == int(a) else a
            return {"type": "sequences", "op": "gp_first_term",
                    "answer": fmt_num(a), "value": a,
                    "steps": [
                        f"The {_ordinal(n)} term of a GP is "
                        f"a × r^{n - 1}, so a = {fmt_num(tn)} "
                        f"/ {fmt_num(r)}^{n - 1}",
                        f"a = {fmt_num(tn)} / "
                        f"{fmt_num(r ** (n - 1))} = "
                        f"{fmt_num(a)}"]}
    # AP: how many terms make the stated sum.
    if "how many terms" in q and "ap" in q:
        terms = _parse_series(q)
        kind, d = _classify(terms) if terms else (None, None)
        ms = re.search(r"(?:to\s+get|sum\s+(?:is|of)|added\s+"
                       r"to\s+get|make)\s+" + N, q)
        if kind == "AP" and ms and d:
            a, target = terms[0], float(ms.group(1))
            # n/2 * (2a + (n-1)d) = target
            import sympy as _sp
            n = _sp.symbols("n", positive=True)
            sol = _sp.solve(
                n / 2 * (2 * a + (n - 1) * d) - target, n)
            good = [s for s in sol
                    if s.is_real and float(s) > 0
                    and abs(float(s) - round(float(s))) < 1e-9]
            if good:
                nv = int(round(float(good[0])))
                return {"type": "sequences",
                        "op": "ap_terms_for_sum",
                        "answer": str(nv), "value": nv,
                        "steps": [
                            f"S_n = n/2 × (2a + (n - 1)d) "
                            f"with a = {fmt_num(a)}, d = "
                            f"{fmt_num(d)}",
                            f"Solving S_n = {fmt_num(target)} "
                            f"gives n = {nv}"]}
    # AP slot form: first term, common difference, term
    # count all stated; last term asked.
    mf = re.search(r"first\s+term\s+(?:is\s+)?" + N, q)
    md = re.search(r"common\s+difference\s+(?:is\s+)?" + N, q)
    mn = re.search(r"(\d+)\s+terms\b", q)
    if mf and md and mn and "last term" in q and "ap" in q:
        a, d, n = float(mf.group(1)), float(md.group(1)), \
            int(mn.group(1))
        last = a + (n - 1) * d
        last = int(last) if last == int(last) else last
        return {"type": "sequences", "op": "ap_last_term",
                "answer": fmt_num(last), "value": last,
                "steps": [
                    f"Last term = a + (n - 1)d = "
                    f"{fmt_num(a)} + ({n} - 1) × "
                    f"{fmt_num(d)} = {fmt_num(last)}"]}
    # nth-term formula evaluated at a stated n.
    m = re.search(r"nth\s+term\s+of\s+an?\s+ap\s+is\s+"
                  r"([0-9n\s\+\-\*/\(\)\.]+?)(?:\.|,|\bfind\b|$)",
                  q)
    mk = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
    if m and mk and "first term" not in q:
        expr = m.group(1).strip()
        k = int(mk.group(1))
        # The formula is linear in n in this family
        # ("3n + 5"); read A and B directly — plain sympify
        # rejects the implicit multiplication in "3n".
        _lm = re.fullmatch(
            r"(\d+(?:\.\d+)?)?\s*n\s*(?:([\+\-])\s*"
            r"(\d+(?:\.\d+)?))?", expr.replace(" ", ""))
        if _lm:
            _a = float(_lm.group(1)) if _lm.group(1) else 1.0
            _b = float(_lm.group(3)) if _lm.group(3) else 0.0
            if _lm.group(2) == "-":
                _b = -_b
            val = _a * k + _b
            val = int(val) if val == int(val) else val
            return {"type": "sequences", "op": "ap_nth_formula",
                    "answer": fmt_num(val), "value": val,
                    "steps": [
                        f"a_n = {expr}; putting n = {k}",
                        f"a_{k} = {fmt_num(val)}"]}
    return None


def solve_sequences(question: str):
    q = question.lower()
    params = _get_params(q)

    _w65 = _wave65_sequences(q)
    if _w65 is not None:
        return _w65

    # Wave 156 (Wave 153 audit book-066): "sum of the
    # first 40 positive integers divisible by 6" — the
    # terms form an AP with a = d = k: S = n*k*(n+1)/2.
    _dv156 = re.search(
        r"sum of (?:the )?first (\d+) (?:positive )?"
        r"integers divisible by (\d+)", q)
    if _dv156:
        _n156 = int(_dv156.group(1))
        _k156 = int(_dv156.group(2))
        _s156 = _n156 * _k156 * (_n156 + 1) // 2
        return {"type": "sequences", "op": "ap_sum_divisible",
                "answer": fmt_num(_s156), "value": _s156,
                "steps": [
                    f"The integers divisible by {_k156} "
                    f"form an AP: {_k156}, "
                    f"{2 * _k156}, {3 * _k156}, ... with "
                    f"a = {_k156}, d = {_k156}",
                    f"Sum of first {_n156} terms = "
                    f"{_n156}/2 × (2 × {_k156} + "
                    f"({_n156} - 1) × {_k156}) = "
                    f"{fmt_num(_s156)}"]}

    # --- Wave 42: Hindi / Hinglish AP phrasing + next term ----
    # Wave 33 covered Hindi probability but left Hindi AP
    # behind: "समांतर श्रेढ़ी 5, 10, 15, ... का 12वां पद" and
    # Roman forms ("12va pad", "pehle 10 padon ka yog") matched
    # no English pattern and fell to a concept/guide fallback.
    # The ordinal/sum markers below mirror the English AP
    # coverage (nth term, sum of n terms); steps stay in
    # English, the house convention for Hindi patterns.
    _qn = question.translate(_DEV_DIGITS_42)
    _ql = _qn.lower()
    _terms42 = _parse_series(_qn)
    _kind42, _d42 = _classify(_terms42) if _terms42 \
        else (None, None)
    _hi42 = any(t in _qn for t in ("समांतर", "श्रेढ़ी",
                                   "श्रेणी")) \
        or re.search(r"sama?ntar|shreni|shredi|shrenee", _ql) \
        or re.search(r"\d+\s*(?:वां|वाँ|वीं|वा)\s*पद", _qn) \
        or re.search(r"\d+\s*(?:va|wa|vaa)\s+(?:pad|term)\b", _ql) \
        or re.search(r"पदों\s*का\s*योग|padon?\s+ka\s+"
                     r"(?:yog|jod|sum)", _ql)
    _next42 = "अगला पद" in _qn or "agla pad" in _ql \
        or "next term" in _ql or "ke baad" in _ql
    if _terms42 and _kind42 in ("AP", "GP") and \
            (_hi42 or _next42):
        _a42 = _terms42[0]
        if _next42 and not re.search(
                r"\d+\s*(?:वां|वाँ|वीं|वा)\s*पद", _qn):
            if _kind42 == "AP":
                _val = _terms42[-1] + _d42
                steps = [
                    f"AP with a = {fmt_num(_a42)}, "
                    f"d = {fmt_num(_d42)}",
                    f"Each term adds {fmt_num(_d42)}, so the "
                    f"term after {fmt_num(_terms42[-1])} is "
                    f"{fmt_num(_terms42[-1])} + "
                    f"{fmt_num(_d42)} = {fmt_num(_val)}",
                ]
                return {"type": "sequences",
                        "op": "ap_next_term",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": steps}
            _val = _terms42[-1] * _d42
            steps = [
                f"GP with a = {fmt_num(_a42)}, "
                f"r = {fmt_num(_d42)}",
                f"Each term multiplies by {fmt_num(_d42)}, "
                f"so the term after {fmt_num(_terms42[-1])} "
                f"is {fmt_num(_terms42[-1])} × "
                f"{fmt_num(_d42)} = {fmt_num(_val)}",
            ]
            return {"type": "sequences", "op": "gp_next_term",
                    "answer": fmt_num(_val), "value": _val,
                    "steps": steps}
        if _kind42 == "AP":
            _msum = re.search(r"(?:पहले|प्रथम)\s*(\d+)\s*पद",
                              _qn) \
                or re.search(r"pehle\s+(\d+)\s+pad", _ql) \
                or re.search(r"(\d+)\s*पदों\s*का\s*योग", _qn) \
                or re.search(r"(\d+)\s*padon\s+ka\s+"
                             r"(?:yog|jod)", _ql)
            if _msum and ("योग" in _qn or "जोड़" in _qn
                          or "yog" in _ql or "jod" in _ql):
                _n = int(_msum.group(1))
                _val = _n * (2 * _a42 + (_n - 1) * _d42) / 2
                steps = [
                    f"AP with a = {fmt_num(_a42)}, "
                    f"d = {fmt_num(_d42)}",
                    "Sum of first n terms: S_n = n/2 · "
                    "(2a + (n - 1)d)",
                    f"S_{_n} = {_n}/2 × (2×{fmt_num(_a42)} + "
                    f"{_n - 1}×{fmt_num(_d42)}) = "
                    f"{fmt_num(_val)}",
                ]
                return {"type": "sequences", "op": "ap_sum",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": steps}
            _mn = re.search(r"(\d+)\s*(?:वां|वाँ|वीं|वा)\s*"
                            r"पद", _qn) \
                or re.search(r"(\d+)\s*(?:va|wa|vaa)\s+"
                             r"(?:pad|term)\b", _ql)
            if _mn:
                _n = int(_mn.group(1))
                _val = _a42 + (_n - 1) * _d42
                steps = [
                    f"AP with a = {fmt_num(_a42)}, "
                    f"d = {fmt_num(_d42)}",
                    "nth term: a_n = a + (n - 1)d",
                    f"a_{_n} = {fmt_num(_a42)} + ({_n} - 1) × "
                    f"{fmt_num(_d42)} = {fmt_num(_val)}",
                ]
                return {"type": "sequences",
                        "op": "ap_nth_term",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": steps}
        # Wave 59: the GP half of this block was missing —
        # a written GP ("GP 2, 6, 18, ... ka 5wa pad") fell
        # through to the English-only code below. Mirror of
        # the AP branches: a_n = a·r^(n-1), S_n = a(r^n - 1)/
        # (r - 1) for r != 1 (a·n when r == 1).
        if _kind42 == "GP":
            _r42 = _d42
            _msum = re.search(r"(?:पहले|प्रथम)\s*(\d+)\s*पद",
                              _qn) \
                or re.search(r"pehle\s+(\d+)\s+pad", _ql) \
                or re.search(r"(\d+)\s*पदों\s*का\s*योग", _qn) \
                or re.search(r"(\d+)\s*padon?\s+ka\s+"
                             r"(?:yog|jod|sum)", _ql)
            if _msum and ("योग" in _qn or "जोड़" in _qn
                          or "yog" in _ql or "jod" in _ql
                          or "sum" in _ql):
                _n = int(_msum.group(1))
                if _r42 == 1:
                    _val = _a42 * _n
                else:
                    _val = _a42 * (_r42 ** _n - 1) / (_r42 - 1)
                steps = [
                    f"GP with a = {fmt_num(_a42)}, "
                    f"r = {fmt_num(_r42)}",
                    "Sum of first n terms: S_n = a(r^n - 1) / "
                    "(r - 1)",
                    f"S_{_n} = {fmt_num(_a42)} × "
                    f"({fmt_num(_r42)}^{_n} - 1) / "
                    f"({fmt_num(_r42)} - 1) = {fmt_num(_val)}",
                ]
                return {"type": "sequences", "op": "gp_sum",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": steps}
            _mn = re.search(r"(\d+)\s*(?:वां|वाँ|वीं|वा)\s*"
                            r"पद", _qn) \
                or re.search(r"(\d+)\s*(?:va|wa|vaa)\s+"
                             r"(?:pad|term)\b", _ql)
            if _mn:
                _n = int(_mn.group(1))
                _val = _a42 * (_r42 ** (_n - 1))
                steps = [
                    f"GP with a = {fmt_num(_a42)}, "
                    f"r = {fmt_num(_r42)}",
                    "nth term: a_n = a × r^(n - 1)",
                    f"a_{_n} = {fmt_num(_a42)} × "
                    f"{fmt_num(_r42)}^{_n - 1} = "
                    f"{fmt_num(_val)}",
                ]
                return {"type": "sequences",
                        "op": "gp_nth_term",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": steps}

    # --- Wave 59: Roman-Hindi parameters without a written
    # series — "jis AP ka pehla pad 5 aur antar 2 hai, uska
    # 12wa term kitna hoga?", "GP me pehla pad 2 hai aur har
    # baar 3 guna ho jata hai, 5wa pad?", "... pehle 10 pado
    # ka yog". The English param code below needs "first term
    # is ..." wording; these asks state the same facts in
    # Hinglish.
    _mfd2 = re.search(r"first term of an ap is "
                      r"(-?\d+(?:\.\d+)?) and the "
                      r"(\d+)(?:st|nd|rd|th) term is "
                      r"(-?\d+(?:\.\d+)?)", _ql)
    if _mfd2 and "common difference" in _ql:
        _a = float(_mfd2.group(1))
        _n = int(_mfd2.group(2))
        _v = float(_mfd2.group(3))
        _d = (_v - _a) / (_n - 1)
        return {"type": "sequences",
                "op": "ap_common_difference",
                "answer": fmt_num(_d), "value": _d,
                "steps": [
                    f"a_{_n} = a + (n - 1)d: {_v:g} = "
                    f"{_a:g} + {_n - 1}d",
                    f"d = ({_v:g} - {_a:g}) / {_n - 1} = "
                    f"{fmt_num(_d)}"]}
    _mwt2 = re.search(r"first term of an ap is "
                      r"(-?\d+(?:\.\d+)?) and the common "
                      r"difference is (-?\d+(?:\.\d+)?),?\s*"
                      r"which term is (-?\d+(?:\.\d+)?)", _ql)
    if _mwt2:
        _a = float(_mwt2.group(1))
        _d = float(_mwt2.group(2))
        _v = float(_mwt2.group(3))
        if _d != 0:
            _n = (_v - _a) / _d + 1
            if _n == int(_n) and _n >= 1:
                _n = int(_n)
                _suf = {1: "st", 2: "nd", 3: "rd"}.get(
                    _n % 10 if _n % 100 not in (11, 12, 13)
                    else 0, "th")
                return {"type": "sequences",
                        "op": "ap_which_term",
                        "answer": f"The {_n}{_suf} term",
                        "value": _n,
                        "steps": [
                            f"a_n = a + (n - 1)d: {_v:g} = "
                            f"{_a:g} + (n - 1) × {_d:g}",
                            f"n = {_n}"]}
    _pa59 = re.search(r"(?:pehla|pehle)\s+pad\s+(?:hai\s+)?"
                      r"(-?\d+(?:\.\d+)?)", _ql)
    if _pa59 and ("ap" in _ql or "gp" in _ql
                  or "antar" in _ql or "ratio" in _ql
                  or re.search(r"guna\s+ho\s+ja\w+", _ql)):
        _a59 = float(_pa59.group(1))
        _md59 = re.search(r"antar\s+(?:hai\s+)?"
                          r"(-?\d+(?:\.\d+)?)", _ql)
        _mr59 = re.search(r"ratio\s+(?:hai\s+)?"
                          r"(-?\d+(?:\.\d+)?)", _ql) \
            or re.search(r"har\s+baar\s+(-?\d+(?:\.\d+)?)\s+"
                         r"guna\s+ho\s+ja\w+", _ql)
        _is_gp = "gp" in _ql or _mr59 is not None
        _mn59 = re.search(r"(\d+)\s*(?:va|wa|vaa)\s+"
                          r"(?:pad|term)\b", _ql)
        _ms59 = re.search(r"pehle\s+(\d+)[^0-9]{0,30}?"
                          r"padon?\s+ka\s+(?:yog|jod|sum)", _ql)
        if _is_gp and _mr59 is not None:
            _r59 = float(_mr59.group(1))
            if _mn59:
                _n = int(_mn59.group(1))
                _val = _a59 * (_r59 ** (_n - 1))
                return {"type": "sequences",
                        "op": "gp_nth_term",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": [
                            f"GP with a = {fmt_num(_a59)}, "
                            f"r = {fmt_num(_r59)}",
                            "nth term: a_n = a × r^(n - 1)",
                            f"a_{_n} = {fmt_num(_a59)} × "
                            f"{fmt_num(_r59)}^{_n - 1} = "
                            f"{fmt_num(_val)}"]}
            if _ms59:
                _n = int(_ms59.group(1))
                _val = _a59 * _n if _r59 == 1 else \
                    _a59 * (_r59 ** _n - 1) / (_r59 - 1)
                return {"type": "sequences", "op": "gp_sum",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": [
                            f"GP with a = {fmt_num(_a59)}, "
                            f"r = {fmt_num(_r59)}",
                            "Sum of first n terms: S_n = "
                            "a(r^n - 1) / (r - 1)",
                            f"S_{_n} = {fmt_num(_val)}"]}
        if not _is_gp and _md59 is not None:
            _d59 = float(_md59.group(1))
            if _mn59:
                _n = int(_mn59.group(1))
                _val = _a59 + (_n - 1) * _d59
                return {"type": "sequences",
                        "op": "ap_nth_term",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": [
                            f"AP with a = {fmt_num(_a59)}, "
                            f"d = {fmt_num(_d59)}",
                            "nth term: a_n = a + (n - 1)d",
                            f"a_{_n} = {fmt_num(_a59)} + "
                            f"({_n} - 1) × {fmt_num(_d59)} = "
                            f"{fmt_num(_val)}"]}
            if _ms59:
                _n = int(_ms59.group(1))
                _val = _n * (2 * _a59 + (_n - 1) * _d59) / 2
                return {"type": "sequences", "op": "ap_sum",
                        "answer": fmt_num(_val), "value": _val,
                        "steps": [
                            f"AP with a = {fmt_num(_a59)}, "
                            f"d = {fmt_num(_d59)}",
                            "Sum of first n terms: S_n = n/2 · "
                            "(2a + (n - 1)d)",
                            f"S_{_n} = {fmt_num(_val)}"]}

    # --- Wave 56: named-series sums, common difference
    # from two terms, and the explicit-series AP sum.
    # "Sum of the first 20 even numbers" is a closed form
    # (n(n+1)); "3rd term is 11 and 8th term is 31" gives
    # d = (a_m - a_k)/(m - k); "sum of the AP 2, 7, 12, ...
    # up to 10 terms" sums the parsed series directly.
    _msum56 = re.search(
        r"sum\s+of\s+(?:the\s+)?first\s+(\d+)\s+"
        r"(even|odd|natural)\s+numbers", q)
    if _msum56:
        _n = int(_msum56.group(1))
        _kind = _msum56.group(2)
        if _kind == "even":
            _val = _n * (_n + 1)
            _f = f"Sum of the first {_n} even numbers " \
                 f"= n(n + 1) = {_n} × {_n + 1}"
        elif _kind == "odd":
            _val = _n * _n
            _f = f"Sum of the first {_n} odd numbers " \
                 f"= n^2 = {_n}^2"
        else:
            _val = _n * (_n + 1) // 2
            _f = f"Sum of the first {_n} natural numbers " \
                 f"= n(n + 1)/2 = {_n} × {_n + 1} / 2"
        return {"type": "sequences", "op": "named_series_sum",
                "answer": fmt_num(_val), "value": _val,
                "steps": [_f + f" = {fmt_num(_val)}"]}
    if "common difference" in q:
        _mt = re.findall(
            r"(\d+)(?:st|nd|rd|th)\s+term\b[^.]*?\bis\s+"
            r"(-?\d+(?:\.\d+)?)", q)
        if len(_mt) >= 2:
            (_n1, _v1), (_n2, _v2) = (int(_mt[0][0]),
                                      float(_mt[0][1])), \
                (int(_mt[1][0]), float(_mt[1][1]))
            if _n2 != _n1:
                _d = (_v2 - _v1) / (_n2 - _n1)
                steps = [
                    f"a_{_n2} - a_{_n1} = ({_n2} - {_n1})d, "
                    f"so {_n2 - _n1}d = {fmt_num(_v2)} - "
                    f"{fmt_num(_v1)} = {fmt_num(_v2 - _v1)}",
                    f"d = {fmt_num(_d)}",
                ]
                return {"type": "sequences",
                        "op": "ap_common_difference",
                        "answer": fmt_num(_d), "value": _d,
                        "steps": steps}
    if _terms42 and _kind42 == "AP" and "sum" in _ql:
        _mn56 = re.search(r"up\s+to\s+(\d+)\s+terms", _ql) \
            or re.search(r"first\s+(\d+)\s+terms", _ql) \
            or re.search(r"\b(\d+)\s+terms\b", _ql)
        if _mn56:
            _n = int(_mn56.group(1))
            _val = _n * (2 * _terms42[0]
                         + (_n - 1) * _d42) / 2
            steps = [
                f"AP with a = {fmt_num(_terms42[0])}, "
                f"d = {fmt_num(_d42)}",
                "Sum of first n terms: S_n = n/2 · "
                "(2a + (n - 1)d)",
                f"S_{_n} = {_n}/2 × (2×"
                f"{fmt_num(_terms42[0])} + {_n - 1}×"
                f"{fmt_num(_d42)}) = {fmt_num(_val)}",
            ]
            return {"type": "sequences", "op": "ap_sum",
                    "answer": fmt_num(_val), "value": _val,
                    "steps": steps}

    # --- Wave 33: nth term from a given S_n -------------------
    # "The sum of the first n terms of an AP is 3n^2 + 5n.
    # Find the nth term." a_n = S_n - S_(n-1); the params
    # path below answered "I need the first term and common
    # difference" — the very thing the student is asking to
    # derive.
    if "nth term" in q or "n-th term" in q or \
            "general term" in q or "first term" in q:
        _msn = re.search(
            r"sum\s+of\s+(?:the\s+)?first\s+n\s+terms[^.]*?"
            r"(?:is|=)\s*(.+?)\s*(?:\.|$)", q) or re.search(
                r"\bs_?n\s*=\s*(.+?)\s*(?:,|\.|$)", q)
        if _msn:
            try:
                from .expression_parser import (
                    fmt as _fmt, parse_expression as _parse)
                _n = sp.Symbol("n")
                _S = _parse(_msn.group(1))
                if _S.free_symbols and \
                        _S.free_symbols <= {_n}:
                    _an = sp.expand(_S - _S.subs(_n, _n - 1))
                    _a1 = _S.subs(_n, 1)
                    _d = sp.expand(_an - _an.subs(_n, 1))
                    if "first term" in q and \
                            "nth term" not in q and \
                            "general term" not in q:
                        return {
                            "type": "sequences",
                            "op": "ap_first_from_sum",
                            "answer": _fmt(_a1),
                            "value": float(_a1),
                            "steps": [
                                "The first term is S_1 "
                                "(the sum of just the first "
                                "term).",
                                f"S_1 = {_fmt(_S.subs(_n, 1))}",
                            ]}
                    steps = [
                        f"S_n = {_fmt(_S)}",
                        "Use a_n = S_n - S_(n-1) (the nth "
                        "term is what the sum gains at "
                        "step n).",
                        f"a_n = ({_fmt(_S)}) - "
                        f"({_fmt(_S.subs(_n, _n - 1))}) "
                        f"= {_fmt(_an)}",
                        f"Check: a = a_1 = {_fmt(_a1)}, "
                        f"d = {_fmt(_d)}.",
                    ]
                    return {"type": "sequences",
                            "op": "ap_nth_from_sum",
                            "answer": _fmt(_an), "steps": steps}
            except Exception:
                pass

    # --- Wave 32: nth term of an AP from the END -----------------
    _m_end = re.search(
        r"(\d+)(?:st|nd|rd|th)\s+term\s+from\s+the\s+end", q)
    if _m_end:
        _terms = _parse_series(q)
        _kind, _d = _classify(_terms) if _terms else (None, None)
        _m_last = re.search(r"(?:\.\.\.|…)\s*,?\s*"
                            r"(-?\d+(?:\.\d+)?)", q)
        if _kind == "AP" and _m_last and _d:
            _a = _terms[0]
            _l = float(_m_last.group(1))
            _k = int(_m_end.group(1))
            _span = (_l - _a) / _d
            if abs(_span - round(_span)) < 1e-9:
                _N = int(round(_span)) + 1
                if 1 <= _k <= _N:
                    _pos = _N - _k + 1
                    _val = _a + (_pos - 1) * _d
                    steps = [
                        f"The AP has a = {_a}, d = {_d} and "
                        f"last term l = {_l:g}.",
                        f"Number of terms N = (l - a)/d + 1 "
                        f"= {_N}.",
                        f"The {_k}th term from the end is "
                        f"term number N - {_k} + 1 = {_pos} "
                        f"from the start.",
                        f"a_{_pos} = a + ({_pos} - 1)d = "
                        f"{_val:g}",
                    ]
                    return {"type": "sequences",
                            "op": "ap_nth_from_end",
                            "answer": fmt_num(_val),
                            "value": _val, "steps": steps}

    # --- Wave 32: how many AP terms give a stated sum ------------
    if "how many terms" in q and "sum" in q:
        _terms = _parse_series(q)
        _kind, _d = _classify(_terms) if _terms else (None, None)
        _m_sum = re.search(r"sum[^.]{0,40}?(?:is|=)\s*"
                           r"(-?\d+(?:\.\d+)?)", q)
        if _kind == "AP" and _m_sum:
            from fractions import Fraction as _F
            _a = _F(str(_terms[0]))
            _df = _F(str(_d))
            _S = _F(str(_m_sum.group(1)))
            # (n/2)(2a + (n-1)d) = S ->
            # d n^2 + (2a - d) n - 2S = 0
            _A, _B, _C = _df, 2 * _a - _df, -2 * _S
            if _A != 0:
                _disc = _B * _B - 4 * _A * _C
                if _disc >= 0:
                    _sq = sp.sqrt(sp.Rational(_disc.numerator,
                                              _disc.denominator))
                    if _sq.is_number and _sq ** 2 == _disc:
                        for _cand in (
                                (-_B + _sq) / (2 * _A),
                                (-_B - _sq) / (2 * _A)):
                            if _cand > 0 and \
                                    float(_cand).is_integer():
                                _n = int(_cand)
                                steps = [
                                    f"Sum of n terms: S_n = "
                                    f"(n/2)(2a + (n - 1)d) "
                                    f"with a = {_a}, "
                                    f"d = {_df}.",
                                    f"Setting S_n = {_S} "
                                    f"gives {_A}·n^2 + "
                                    f"{_B}·n "
                                    f"{'+' if _C >= 0 else ''}"
                                    f"{_C} = 0.",
                                    f"Solving: n = {_n} "
                                    f"(the positive root).",
                                ]
                                return {
                                    "type": "sequences",
                                    "op": "ap_terms_for_sum",
                                    "answer": str(_n),
                                    "value": _n, "steps": steps}

    # Sum of first n natural numbers / squares / cubes
    m = re.search(
        r"sum\s+of\s+(?:the\s+)?first\s+(\d+)\s+(natural\s+numbers|"
        r"squares|cubes)", q)
    if m:
        n = int(m.group(1))
        kind = m.group(2)
        if kind.startswith("natural"):
            val = n * (n + 1) // 2
            steps = ["Sum of first n natural numbers = n(n + 1)/2",
                     f"= {n} × {n + 1} / 2 = {val}"]
        elif kind == "squares":
            val = n * (n + 1) * (2 * n + 1) // 6
            steps = ["Sum of squares = n(n + 1)(2n + 1)/6",
                     f"= {n} × {n + 1} × {2 * n + 1} / 6 = {val}"]
        else:
            val = (n * (n + 1) // 2) ** 2
            steps = ["Sum of cubes = [n(n + 1)/2]^2",
                     f"= [{n} × {n + 1} / 2]^2 = {val}"]
        return {"type": "sequences", "op": "series_sum",
                "answer": fmt_num(val), "value": val, "steps": steps}

    terms = _parse_series(q)
    kind, ratio_diff = (None, None)
    if terms:
        kind, ratio_diff = _classify(terms)
    # Wave 38: an explicit "GP" / "AP" label in the question
    # beats _classify's two-term default — two terms alone are
    # read as an AP (difference), so "8th term of the GP 3, 6,
    # ..." answered 24 (the AP value) instead of 384 (Wave 35
    # audit #117-119). The student's own label is authoritative.
    if terms and len(terms) >= 2:
        if re.search(r"\bgp\b|geometric", q):
            if terms[0] != 0:
                kind, ratio_diff = "GP", terms[1] / terms[0]
        elif re.search(r"\bap\b|arithmetic", q):
            kind, ratio_diff = "AP", terms[1] - terms[0]
    # Wave 38: parameters stated in words ("the first term is
    # 4 and the common ratio is 3") — _get_params only reads
    # the a= / r= forms, so these asks got "I need the first
    # term and common ratio" despite stating both.
    if "a" not in params:
        _mw = re.search(r"first\s+term\s+(?:is\s+)?(-?\d+(?:\.\d+)?)", q)
        if _mw:
            _v = float(_mw.group(1))
            params["a"] = int(_v) if _v == int(_v) else _v
    if "r" not in params:
        _mw = re.search(r"common\s+ratio\s+(?:is\s+)?(-?\d+(?:\.\d+)?)", q)
        if _mw:
            _v = float(_mw.group(1))
            params["r"] = int(_v) if _v == int(_v) else _v
    if "d" not in params:
        _mw = re.search(r"common\s+difference\s+(?:is\s+)?"
                        r"(-?\d+(?:\.\d+)?)", q)
        if _mw:
            _v = float(_mw.group(1))
            params["d"] = int(_v) if _v == int(_v) else _v
    # Wave 59: common difference from the first term and one
    # later term ("first term is 2 and the 5th term is 14,
    # find the common difference") — d = (a_n - a) / (n - 1).
    if "common difference" in q and "a" in params \
            and "d" not in params:
        _mfd = re.search(r"(\d+)(?:st|nd|rd|th)\s+term\s+is\s+"
                         r"(-?\d+(?:\.\d+)?)", q)
        if _mfd and int(_mfd.group(1)) > 1:
            _n = int(_mfd.group(1))
            _v = (float(_mfd.group(2)) - float(params["a"])) \
                / (_n - 1)
            params["d"] = int(_v) if _v == int(_v) else _v
            return {"type": "sequences",
                    "op": "ap_common_difference",
                    "answer": fmt_num(params["d"]),
                    "value": params["d"],
                    "steps": [
                        f"a_{_n} = a + (n - 1)d, so "
                        f"{fmt_num(float(_mfd.group(2)))} = "
                        f"{fmt_num(float(params['a']))} + "
                        f"({_n} - 1)d",
                        f"d = ({fmt_num(float(_mfd.group(2)))} "
                        f"- {fmt_num(float(params['a']))}) / "
                        f"{_n - 1} = {fmt_num(params['d'])}"]}
    if kind is None:
        if "gp" in q or "geometric" in q:
            kind = "GP"
        elif "ap" in q or "arithmetic" in q:
            kind = "AP"
    if kind is None:
        return {"type": "sequences", "op": "unknown",
                "answer": "Give me the series, e.g. '10th term of AP "
                          "2, 5, 8' or 'sum of first 10 terms of GP "
                          "3, 6, 12'.",
                "steps": []}

    # Wave 47: sum and product of the first three GP terms
    # given, ratio (or terms) asked — "The sum of the first
    # three terms of a GP is 39 and their product is 729.
    # Find the common ratio." With terms a/r, a, ar the
    # product is a^3 and the sum gives r + 1/r = S/a - 1, a
    # quadratic in r (Wave 35 audit #123 — it fell back
    # with "I need the first term and common ratio").
    if kind == "GP" and not terms:
        _ms = re.search(
            r"sum of (?:the )?first three terms[^.]*?"
            r"\bis\s+(-?\d+(?:\.\d+)?)", q)
        _mp = re.search(
            r"product[^.]*?\bis\s+(-?\d+(?:\.\d+)?)", q)
        if _ms and _mp:
            from fractions import Fraction as _F
            _S = _F(str(_ms.group(1)))
            _P = _F(str(_mp.group(1)))
            _a = None
            if _P.denominator == 1:
                _pi = int(_P)
                _root = round(abs(_pi) ** (1 / 3))
                for _cand in (_root - 1, _root, _root + 1):
                    if _cand ** 3 == abs(_pi):
                        _a = _F(_cand if _pi >= 0
                                else -_cand)
                        break
            if _a:
                _m = _S / _a - 1  # r + 1/r
                _disc = _m * _m - 4
                if _disc >= 0:
                    _sq = sp.sqrt(sp.Rational(
                        _disc.numerator, _disc.denominator))
                    if _sq.is_number and \
                            _sq ** 2 == _disc:
                        _sqF = _F(_sq.p, _sq.q)
                        _r1 = (_m + _sqF) / 2
                        _r2 = (_m - _sqF) / 2

                        def _rat(v):
                            return fmt_num(sp.Rational(
                                v.numerator, v.denominator))

                        _t1, _t2, _t3 = _a / _r1, _a, _a * _r1
                        steps = [
                            "Take the three terms as a/r, "
                            "a, ar.",
                            f"Product: (a/r) × a × (a·r) = "
                            f"a^3 = {_rat(_P)}, so a = "
                            f"{_rat(_a)}.",
                            f"Sum: a/r + a + a·r = "
                            f"{_rat(_S)} gives r + 1/r = "
                            f"{_rat(_m)}.",
                            f"So r^2 - {_rat(_m)}·r + 1 = 0, "
                            f"giving r = {_rat(_r1)} or "
                            f"r = {_rat(_r2)}.",
                            f"With r = {_rat(_r1)} the terms "
                            f"are {_rat(_t1)}, {_rat(_t2)}, "
                            f"{_rat(_t3)}.",
                        ]
                        if "ratio" in q:
                            _ans = f"{_rat(_r1)} or " \
                                   f"{_rat(_r2)}" \
                                if _r1 != _r2 else _rat(_r1)
                            return {
                                "type": "sequences",
                                "op": "gp_sum_product",
                                "answer": _ans,
                                "value": float(_r1),
                                "steps": steps}
                        return {
                            "type": "sequences",
                            "op": "gp_sum_product",
                            "answer": f"{_rat(_t1)}, "
                                      f"{_rat(_t2)}, "
                                      f"{_rat(_t3)}",
                            "value": [float(_t1),
                                      float(_t2),
                                      float(_t3)],
                            "steps": steps}

    a = terms[0] if terms else params.get("a")
    if kind == "AP":
        d = ratio_diff if terms else params.get("d")
        if a is None or d is None:
            return {"type": "sequences", "op": "unknown",
                    "answer": "I need the first term and common "
                              "difference.",
                    "steps": []}
        # Wave 30: "Which term of the AP ... is V?" — invert
        # a_n = a + (n-1)d instead of asking for a term number.
        if "which term" in q:
            mv = re.search(r"\bis\s+(-?\d+(?:\.\d+)?)\s*\?*\s*$",
                           q.strip())
            if mv and d != 0:
                V = float(mv.group(1))
                V = int(V) if V == int(V) else V
                num = V - a
                if num % d == 0 and num // d >= 0:
                    n = int(num // d) + 1
                    steps = [
                        f"AP with a = {fmt_num(a)}, "
                        f"d = {fmt_num(d)}",
                        "Set the nth term equal to the given "
                        "value: a + (n - 1)d = "
                        f"{fmt_num(V)}",
                        f"(n - 1) = ({fmt_num(V)} - "
                        f"{fmt_num(a)}) ÷ {fmt_num(d)} = "
                        f"{fmt_num(num // d)}, so "
                        f"n = {n}",
                    ]
                    return {"type": "sequences",
                            "op": "ap_which_term",
                            "answer": f"The {_ordinal(n)} term",
                            "value": n, "steps": steps}
                # A value WAS named and it is genuinely not
                # reachable — that is the honest exact answer.
                return {"type": "sequences", "op": "ap_which_term",
                        "answer": f"{fmt_num(V)} is not a term "
                                  f"of this AP.",
                        "steps": [
                            f"a + (n - 1)d = {fmt_num(V)} gives "
                            f"n - 1 = {fmt_num(num)} ÷ "
                            f"{fmt_num(d)}, which is not a "
                            f"whole number, so no term equals "
                            f"{fmt_num(V)}.",
                        ]}
        m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
        wants_sum = "sum" in q
        n = None
        m2 = re.search(r"first\s+(\d+)\s+terms", q)
        if m2:
            n = int(m2.group(1))
            wants_sum = True
        elif "n" in params:
            n = params["n"]
        if wants_sum and n:
            val = n * (2 * a + (n - 1) * d) / 2
            steps = [
                f"AP with a = {fmt_num(a)}, d = {fmt_num(d)}",
                "Sum of first n terms: S_n = n/2 · (2a + (n - 1)d)",
                f"S_{n} = {n}/2 × (2×{fmt_num(a)} + {n - 1}×"
                f"{fmt_num(d)}) = {fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "ap_sum",
                    "answer": fmt_num(val), "value": val, "steps": steps}
        if m:
            n = int(m.group(1))
            val = a + (n - 1) * d
            steps = [
                f"AP with a = {fmt_num(a)}, d = {fmt_num(d)}",
                "nth term: a_n = a + (n - 1)d",
                f"a_{n} = {fmt_num(a)} + ({n} - 1) × {fmt_num(d)} = "
                f"{fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "ap_nth_term",
                    "answer": fmt_num(val), "value": val, "steps": steps}

    if kind == "GP":
        r = ratio_diff if terms else params.get("r")
        if a is None or r is None:
            return {"type": "sequences", "op": "unknown",
                    "answer": "I need the first term and common ratio.",
                    "steps": []}
        # Wave 30: "Which term of the GP ... is V?"
        if "which term" in q:
            mv = re.search(r"\bis\s+(-?\d+(?:\.\d+)?)\s*\?*\s*$",
                           q.strip())
            if mv and r not in (0, 1):
                V = float(mv.group(1))
                V = int(V) if V == int(V) else V
                cur, n = a, 1
                while n <= 500 and cur != V:
                    cur = cur * r
                    n += 1
                if cur == V:
                    steps = [
                        f"GP with a = {fmt_num(a)}, "
                        f"r = {fmt_num(r)}",
                        "Keep multiplying by the common ratio "
                        "until the given value appears: it is "
                        f"reached at term {n}.",
                        f"Check: a·r^{n - 1} = {fmt_num(a)} × "
                        f"{fmt_num(r)}^{n - 1} = {fmt_num(V)}",
                    ]
                    return {"type": "sequences",
                            "op": "gp_which_term",
                            "answer": f"The {_ordinal(n)} term",
                            "value": n, "steps": steps}
                return {"type": "sequences", "op": "gp_which_term",
                        "answer": f"{fmt_num(V)} is not a term "
                                  f"of this GP.",
                        "steps": [
                            "Multiplying the first term by the "
                            "common ratio again and again never "
                            f"reaches {fmt_num(V)}.",
                        ]}
        # Wave 146: a question about the sums of SEVERAL
        # different GPs ("S1, S2, S3, ..., Sn are the sums of
        # n infinite geometric progressions...") is not a
        # single-GP ask — the parser's scavenged a = 1, r = 1
        # produced a confident "sum to infinity does not
        # exist" verdict for a series whose terms do converge.
        # Decline the whole single-GP path for that shape.
        if re.search(
                r"sums?\s+of\s+(?:\w+\s+){0,3}?geometric\s+"
                r"progressions", q) or re.search(
                r"\bS\s?1\s*,\s*S\s?2\b", q):
            return {"type": "sequences", "op": "unknown",
                    "answer": "Tell me which term or sum you "
                              "want, e.g. '10th term of AP "
                              "2, 5, 8'.",
                    "steps": []}
        # Wave 38: sum to infinity (only exists for |r| < 1).
        if "infinit" in q:
            if abs(r) < 1:
                val = a / (1 - r)
                steps = [
                    f"GP with a = {fmt_num(a)}, r = {fmt_num(r)}",
                    "Sum to infinity: S = a / (1 - r), valid "
                    "because |r| < 1",
                    f"S = {fmt_num(a)} / (1 - {fmt_num(r)}) = "
                    f"{fmt_num(val)}",
                ]
                return {"type": "sequences",
                        "op": "gp_sum_infinity",
                        "answer": fmt_num(val), "value": val,
                        "steps": steps}
            return {"type": "sequences", "op": "gp_sum_infinity",
                    "answer": "The sum to infinity does not "
                              "exist, because |r| >= 1, so the "
                              "terms do not shrink to zero.",
                    "steps": [
                        f"GP with a = {fmt_num(a)}, "
                        f"r = {fmt_num(r)}: |r| >= 1, so each "
                        "term is at least as big as the one "
                        "before and the sum grows without "
                        "bound."]}
        m = re.search(r"(\d+)(?:st|nd|rd|th)\s+term", q)
        wants_sum = "sum" in q
        n = None
        m2 = re.search(r"first\s+(\d+)\s+terms", q)
        if m2:
            n = int(m2.group(1))
            wants_sum = True
        elif "n" in params:
            n = params["n"]
        if wants_sum and n:
            if r == 1:
                val = a * n
            else:
                val = a * (r ** n - 1) / (r - 1)
            steps = [
                f"GP with a = {fmt_num(a)}, r = {fmt_num(r)}",
                "Sum of first n terms: S_n = a(r^n - 1)/(r - 1)",
                f"S_{n} = {fmt_num(a)} × ({fmt_num(r)}^{n} - 1) / "
                f"({fmt_num(r)} - 1) = {fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "gp_sum",
                    "answer": fmt_num(val), "value": val, "steps": steps}
        if m:
            n = int(m.group(1))
            val = a * r ** (n - 1)
            steps = [
                f"GP with a = {fmt_num(a)}, r = {fmt_num(r)}",
                "nth term: a_n = a·r^(n-1)",
                f"a_{n} = {fmt_num(a)} × {fmt_num(r)}^{n - 1} = "
                f"{fmt_num(val)}",
            ]
            return {"type": "sequences", "op": "gp_nth_term",
                    "answer": fmt_num(val), "value": val, "steps": steps}

    return {"type": "sequences", "op": "unknown",
            "answer": "Tell me which term or sum you want, e.g. '10th "
                      "term of AP 2, 5, 8'.",
            "steps": []}
