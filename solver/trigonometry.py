"""Trigonometry: values (degrees by default), identities, equations.

School convention used here: a bare number argument ("sin 30") is in
DEGREES unless the question mentions radians or the argument uses pi.
"""
import re

import sympy as sp

from .expression_parser import fmt, fmt_num, parse_expression

_FUNCS = ("sin", "cos", "tan", "cot", "sec", "csc", "cosec")
_WORD_FUNCS = [
    (r"\bsine\b", "sin"),
    (r"\bcosine\b", "cos"),
    (r"\btangent\b", "tan"),
    (r"\bcotangent\b", "cot"),
    (r"\bsecant\b", "sec"),
    (r"\bcosecant\b", "cosec"),
]


def _normalise(q: str) -> str:
    t = q
    for pat, rep in _WORD_FUNCS:
        t = re.sub(pat, rep, t, flags=re.I)
    t = t.replace("cosec", "csc")
    return t


def _degrees_mode(q: str) -> bool:
    if re.search(r"\brad", q, re.I):
        return False
    if "pi" in q or "π" in q:
        return False
    return True


def _convert_degrees(q: str):
    """Rewrite sin(30)/sin 30 as sin(30*pi/180); returns (text, conversions)."""
    conversions = []

    def repl(m):
        fn, val = m.group(1).lower(), m.group(2)
        conversions.append((fn, val))
        return f"{fn}({val}*pi/180)"

    t = re.sub(
        r"\b(sin|cos|tan|cot|sec|csc)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
        repl, q, flags=re.I,
    )
    t = re.sub(
        r"\b(sin|cos|tan|cot|sec|csc)\s+(-?\d+(?:\.\d+)?)\b",
        repl, t, flags=re.I,
    )
    return t, conversions


def solve_trigonometry(question: str):
    q = _normalise(question.strip())
    qlow = q.lower()
    deg = _degrees_mode(q)

    # --- Identity proof / verification -------------------------------------
    if "=" in q and re.search(r"\b(prove|verify|identity|show)\b", qlow):
        text = re.sub(r"\b(prove|verify|show\s+that)\b", "", q, flags=re.I)
        if deg:
            text, _ = _convert_degrees(text)
        left, right = text.split("=", 1)
        diff_expr = sp.trigsimp(
            parse_expression(left) - parse_expression(right)
        )
        ok = diff_expr == 0
        steps = [
            "Take LHS - RHS and simplify using trig identities "
            "(sin^2 t + cos^2 t = 1, tan t = sin t / cos t, ...).",
            f"LHS - RHS simplifies to {fmt(diff_expr)}",
            "Since LHS - RHS = 0, the identity is "
            + ("TRUE (verified)." if ok else "NOT an identity."),
        ]
        return {
            "type": "trigonometry",
            "op": "identity",
            "answer": "Identity verified ✔" if ok else "Not an identity",
            "verified": bool(ok),
            "steps": steps,
        }

    # --- One ratio given, another asked (Wave 30) ------------------
    # "If sin A = 3/5, find cos A": build the right-triangle
    # triple (3-4-5 style) from the given ratio and read the
    # asked ratio off it. This used to fall through to the
    # expression parser, which "solved" a stray fragment.
    mr = re.search(
        r"\b(sin|cos|tan)\s*(theta|θ|[a-z])\s*=\s*(\d+(?:\.\d+)?"
        r"(?:\s*/\s*\d+(?:\.\d+)?)?)", qlow)
    if mr and "find" in qlow:
        _fn = mr.group(1)
        # Wave 33: "theta" / "θ" name the angle too — display
        # it as θ (the single-letter path upper-cases its
        # letter, which would print "THETA").
        _ang = "θ" if mr.group(2) in ("theta", "θ") \
            else mr.group(2).upper()
        _raw = mr.group(3).replace(" ", "")
        _val = sp.Rational(_raw) if "/" in _raw else \
            sp.nsimplify(float(_raw), rational=True)
        if _val > 0 and (_fn == "tan" or _val < 1):
            if _fn == "sin":
                _opp, _hyp = _val.p, _val.q
                _adj = sp.sqrt(_hyp ** 2 - _opp ** 2)
                _given = (f"sin {_ang} = opposite/hypotenuse "
                          f"= {_opp}/{_hyp}, so take opposite "
                          f"= {_opp} and hypotenuse = {_hyp}")
                _third = (f"adjacent = sqrt({_hyp}^2 - "
                          f"{_opp}^2) = {fmt(_adj)} "
                          f"(Pythagoras)")
            elif _fn == "cos":
                _adj, _hyp = _val.p, _val.q
                _opp = sp.sqrt(_hyp ** 2 - _adj ** 2)
                _given = (f"cos {_ang} = adjacent/hypotenuse "
                          f"= {_adj}/{_hyp}, so take adjacent "
                          f"= {_adj} and hypotenuse = {_hyp}")
                _third = (f"opposite = sqrt({_hyp}^2 - "
                          f"{_adj}^2) = {fmt(_opp)} "
                          f"(Pythagoras)")
            else:
                _opp, _adj = _val.p, _val.q
                _hyp = sp.sqrt(_opp ** 2 + _adj ** 2)
                _given = (f"tan {_ang} = opposite/adjacent "
                          f"= {_opp}/{_adj}, so take opposite "
                          f"= {_opp} and adjacent = {_adj}")
                _third = (f"hypotenuse = sqrt({_opp}^2 + "
                          f"{_adj}^2) = {fmt(_hyp)} "
                          f"(Pythagoras)")
            _vals = {"sin": _opp / _hyp, "cos": _adj / _hyp,
                     "tan": _opp / _adj}
            _tail = qlow[qlow.index("find"):]
            _asked = [f for f in ("sin", "cos", "tan")
                      if f != _fn
                      and re.search(rf"\b{f}\s*{mr.group(2)}\b",
                                    _tail)]
            if not _asked:
                _asked = [f for f in ("sin", "cos", "tan")
                          if f != _fn]
            steps = [_given, _third]
            for f in _asked:
                _num_name = {"sin": "opposite", "cos": "adjacent",
                             "tan": "opposite"}[f]
                _den_name = {"sin": "hypotenuse",
                             "cos": "hypotenuse",
                             "tan": "adjacent"}[f]
                steps.append(
                    f"{f} {_ang} = {_num_name}/{_den_name} "
                    f"= {fmt(_vals[f])}")
            return {
                "type": "trigonometry",
                "op": "ratio_from_ratio",
                "answer": ", ".join(
                    f"{f} {_ang} = {fmt(_vals[f])}"
                    for f in _asked),
                "steps": steps,
            }

    # --- Trig equation: solve sin(x) = 1/2 --------------------------------
    if "=" in q and re.search(r"(sin|cos|tan)\s*\(", q):
        text = re.sub(r"^\s*solve\b", "", q, flags=re.I).strip()
        left, right = text.split("=", 1)
        var_syms = parse_expression(left).free_symbols
        var = sorted(var_syms, key=lambda s: s.name)[0] if var_syms \
            else sp.symbols("x")
        expr = parse_expression(left) - parse_expression(right)
        sols = sp.solveset(expr, var, domain=sp.Interval(0, 2 * sp.pi))
        deg_sols = sorted(
            float(sp.deg(sp.N(s))) if hasattr(sp, "deg") else
            float(s * 180 / sp.pi)
            for s in sols
        ) if sols else []
        deg_sols = [round(d, 4) for d in deg_sols]
        steps = [
            f"Solve {left.strip()} = {right.strip()} for angles between "
            "0° and 360°.",
            "Use the unit circle: note the sign of the function in each "
            "quadrant to find every solution in the range.",
            "Solutions (degrees): "
            + (", ".join(fmt_num(d) + "°" for d in deg_sols) or "none"),
        ]
        return {
            "type": "trigonometry",
            "op": "equation",
            "answer": ", ".join(f"{fmt_num(d)}°" for d in deg_sols)
            or "No solution in [0°, 360°)",
            "solutions": [f"{fmt_num(d)} degrees" for d in deg_sols],
            "steps": steps,
        }

    # --- Inverse trig: arcsin(0.5), sin^-1(0.5), inverse sin of 0.5 --------
    m = re.search(
        r"(?:arc|a)(sin|cos|tan)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)"
        r"|(sin|cos|tan)\s*\^\s*\(\s*-1\s*\)\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)"
        r"|inverse\s+(sin|cos|tan)\s*(?:of\s*)?(-?\d+(?:\.\d+)?)",
        q, re.I,
    )
    if m:
        fn = (m.group(1) or m.group(3) or m.group(5)).lower()
        val = float(m.group(2) or m.group(4) or m.group(6))
        func = {"sin": sp.asin, "cos": sp.acos, "tan": sp.atan}[fn]
        res = func(sp.nsimplify(val, rational=True))
        deg_val = float(res * 180 / sp.pi)
        steps = [
            f"arc{fn}({fmt_num(val)}) asks: which angle has "
            f"{fn} = {fmt_num(val)}?",
            f"Angle = {fmt(res)} radians = {fmt_num(deg_val)}°",
        ]
        return {
            "type": "trigonometry",
            "op": "inverse_value",
            "answer": f"{fmt_num(deg_val)}° ({fmt(res)} rad)",
            "value": deg_val,
            "steps": steps,
        }

    # --- Heights & distances (Wave 30) ------------------------------
    # Ladder against a wall: the ladder is the hypotenuse.
    _ml = re.search(r"ladder\s+(?:of\s+length\s+)?"
                    r"(\d+(?:\.\d+)?)\s*m\s*(?:long)?", qlow)
    _ma = re.search(r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)\s+with\s+"
                    r"the\s+(ground|wall)", qlow)
    if _ml and _ma:
        _L = sp.Rational(_ml.group(1))
        _fmt_l = fmt_num(_L)
        _th = sp.Rational(_ma.group(1))
        _with = _ma.group(2)
        if _with == "ground":
            _h = _L * sp.sin(_th * sp.pi / 180)
            steps = [
                f"The ladder itself is the hypotenuse "
                f"({_fmt_l} m), and the height reached on the "
                f"wall is the side opposite the "
                f"{fmt_num(_th)}° angle with the ground.",
                f"sin {fmt_num(_th)}° = height / ladder length, "
                f"so height = {_fmt_l} × sin {fmt_num(_th)}°",
                f"Height = {fmt(_h)} m ≈ {float(_h):.2f} m",
            ]
        else:
            _h = _L * sp.cos(_th * sp.pi / 180)
            steps = [
                f"The ladder itself is the hypotenuse "
                f"({_fmt_l} m); with the angle measured from "
                f"the wall, the height reached is the side "
                f"adjacent to the {fmt_num(_th)}° angle.",
                f"cos {fmt_num(_th)}° = height / ladder length, "
                f"so height = {_fmt_l} × cos {fmt_num(_th)}°",
                f"Height = {fmt(_h)} m ≈ {float(_h):.2f} m",
            ]
        return {
            "type": "trigonometry",
            "op": "heights_distances",
            "answer": f"{fmt(_h)} m ≈ {float(_h):.2f} m",
            "value": float(_h),
            "steps": steps,
        }
    # --- Wave 32: angle of depression ---------------------------
    if "angle of depression" in qlow:
        _degs = re.findall(r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)",
                           qlow)
        _mh = re.search(r"(\d+(?:\.\d+)?)\s*m\s+(?:high|tall)",
                        qlow) or re.search(
                            r"height[^.]{0,30}?(\d+(?:\.\d+)?)"
                            r"\s*m\b", qlow)
        _md = re.search(r"distance[^.]{0,30}?(\d+(?:\.\d+)?)"
                        r"\s*m\b", qlow)
        if _degs and _mh:
            _th = sp.Rational(_degs[-1])
            _h = sp.Rational(_mh.group(1))
            _d = _h / sp.tan(_th * sp.pi / 180)
            steps = [
                "The angle of depression equals the angle of "
                "elevation from the object (alternate angles).",
                f"tan {_th}° = height / distance = "
                f"{fmt_num(_h)} / d",
                f"Distance d = {fmt_num(_h)} / tan {_th}° "
                f"= {fmt(_d)} m ≈ {float(_d):.2f} m",
            ]
            return {
                "type": "trigonometry",
                "op": "angle_of_depression",
                "answer": f"{fmt(_d)} m ≈ {float(_d):.2f} m",
                "value": float(_d),
                "steps": steps,
            }
        if _degs and _md:
            _th = sp.Rational(_degs[-1])
            _d = sp.Rational(_md.group(1))
            _h = _d * sp.tan(_th * sp.pi / 180)
            steps = [
                "The angle of depression equals the angle of "
                "elevation from the object (alternate angles).",
                f"tan {_th}° = height / {fmt_num(_d)}, so "
                f"height = {fmt_num(_d)} × tan {_th}°",
                f"Height = {fmt(_h)} m ≈ {float(_h):.2f} m",
            ]
            return {
                "type": "trigonometry",
                "op": "angle_of_depression",
                "answer": f"{fmt(_h)} m ≈ {float(_h):.2f} m",
                "value": float(_h),
                "steps": steps,
            }

    # --- Wave 32: two-observation heights & distances -----------
    _two_obs = re.findall(r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)",
                          qlow)
    if len(_two_obs) >= 2 and "angle of elevation" in qlow and (
            "apart" in qlow or "between" in qlow):
        _md = re.search(r"(\d+(?:\.\d+)?)\s*m\s+(?:apart|from)",
                        qlow) or re.search(
                            r"distance[^.]{0,30}?(\d+(?:\.\d+)?)"
                            r"\s*m\b", qlow)
        if _md:
            _a1, _a2 = (sp.Rational(_two_obs[0]),
                        sp.Rational(_two_obs[1]))
            _d = sp.Rational(_md.group(1))
            _cot = lambda t: 1 / sp.tan(t * sp.pi / 180)
            _den = abs(_cot(_a1) - _cot(_a2))
            if _den != 0:
                _h = _d / _den
                steps = [
                    "If the tower's height is h, the distances "
                    "of the two points from its foot are "
                    "h·cot(angle) each.",
                    f"The gap between the points is "
                    f"h × |cot {_a1}° - cot {_a2}°| "
                    f"= {fmt_num(_d)}",
                    f"Height h = {fmt_num(_d)} / "
                    f"{fmt(_den)} = {fmt(_h)} m "
                    f"≈ {float(_h):.2f} m",
                ]
                return {
                    "type": "trigonometry",
                    "op": "two_observation_height",
                    "answer": f"{fmt(_h)} m ≈ "
                              f"{float(_h):.2f} m",
                    "value": float(_h),
                    "steps": steps,
                }

    # --- Wave 32: inverse trig evaluations ----------------------
    _inv_sum = re.search(
        r"(sin|cos)\^-1\s*\(\s*([^()]+?)\s*\)\s*\+\s*"
        r"(sin|cos)\^-1\s*\(\s*([^()]+?)\s*\)", qlow)
    if _inv_sum and _inv_sum.group(1) != _inv_sum.group(3) \
            and _inv_sum.group(2) == _inv_sum.group(4):
        steps = [
            "Identity: sin^-1 x + cos^-1 x = pi/2 for the "
            "same x.",
            "So the value is pi/2 = 90 degrees.",
        ]
        return {
            "type": "trigonometry", "op": "inverse_trig_sum",
            "answer": "pi/2 (90 degrees)", "steps": steps,
            "value": 1.5707963,
        }
    _inv_red = re.search(
        r"(sin|cos|tan)\^-1\s*\(\s*(sin|cos|tan)\s+"
        r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)\s*\)", qlow)
    if _inv_red and _inv_red.group(1) == _inv_red.group(2):
        _fn = _inv_red.group(1)
        _th = float(_inv_red.group(3))
        if _fn == "sin":
            _r = _th if _th <= 90 else (180 - _th if _th <= 270
                                        else _th - 360)
        elif _fn == "cos":
            _r = _th if _th <= 180 else 360 - _th
        else:
            if _th == 90 or _th == 270:
                _r = None
            else:
                _r = _th if _th < 90 else (_th - 180
                                           if _th < 270
                                           else _th - 360)
        if _r is not None:
            steps = [
                f"{_fn}^-1({_fn} theta) must lie in the "
                f"principal range of {_fn}^-1.",
                f"{_th:g} degrees reduces to {_r:g} degrees "
                f"in that range.",
            ]
            return {
                "type": "trigonometry",
                "op": "inverse_trig_reduction",
                "answer": f"{_r:g} degrees", "steps": steps,
                "value": float(_r),
            }
    _tan_sum = re.search(
        r"tan\^-1\s*\(\s*(-?\d+(?:\.\d+)?(?:\s*/\s*"
        r"\d+(?:\.\d+)?)?)\s*\)\s*\+\s*tan\^-1\s*\(\s*"
        r"(-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?)\s*\)",
        qlow)
    if _tan_sum:
        _x = sp.Rational(_tan_sum.group(1).replace(" ", ""))
        _y = sp.Rational(_tan_sum.group(2).replace(" ", ""))
        if _x * _y != 1:
            _val = sp.atan((_x + _y) / (1 - _x * _y))
            if _x * _y > 1:
                _val = _val + sp.pi
            steps = [
                "Formula: tan^-1 x + tan^-1 y = tan^-1("
                "(x + y)/(1 - xy)).",
                f"= tan^-1(({fmt(_x)} + {fmt(_y)}) / (1 - "
                f"{fmt(_x * _y)})) = {fmt(_val)}",
            ]
            return {
                "type": "trigonometry",
                "op": "inverse_trig_formula",
                "answer": fmt(_val), "steps": steps,
                "value": float(_val),
            }
    _inv = re.search(
        r"(sec|cosec|csc|cot|sin|cos|tan)\^-1\s*\(?\s*"
        r"(-?\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)?"
        r"|sqrt\s*\(?\s*\d+(?:\.\d+)?\s*\)?)\s*\)?", qlow)
    if _inv:
        _fn = _inv.group(1)
        _arg_raw = _inv.group(2).replace(" ", "")
        try:
            if _arg_raw.startswith("sqrt"):
                _num = re.search(r"\d+(?:\.\d+)?", _arg_raw)
                _arg = sp.sqrt(sp.Rational(_num.group(0)))
            else:
                _arg = sp.Rational(_arg_raw)
            if _fn in ("sec",):
                _val = sp.acos(1 / _arg)
            elif _fn in ("cosec", "csc"):
                _val = sp.asin(1 / _arg)
            elif _fn == "cot":
                _val = sp.atan(1 / _arg) if _arg > 0 else \
                    sp.pi + sp.atan(1 / _arg)
            elif _fn == "sin":
                _val = sp.asin(_arg)
            elif _fn == "cos":
                _val = sp.acos(_arg)
            else:
                _val = sp.atan(_arg)
            _degf = float(sp.deg(_val))
            if abs(_degf - round(_degf / 15) * 15) < 1e-9:
                steps = [
                    f"Principal value of {_fn}^-1"
                    f"({fmt(_arg)}):",
                    f"= {fmt(_val)} = {_degf:.0f} degrees",
                ]
                return {
                    "type": "trigonometry",
                    "op": "inverse_trig_value",
                    "answer": f"{fmt(_val)} "
                              f"({_degf:.0f} degrees)",
                    "steps": steps, "value": float(_val),
                }
        except Exception:
            pass

    # --- Wave 32: complementary-angle ratios --------------------
    _comp = re.search(
        r"\b(tan|sin|cos|sec|cosec|cot)\s+(\d+(?:\.\d+)?)"
        r"\s*(?:degrees?|°)\s*/\s*(tan|sin|cos|sec|cosec|cot)"
        r"\s+(\d+(?:\.\d+)?)\s*(?:degrees?|°)", qlow)
    if _comp:
        _pairs = {("tan", "cot"), ("cot", "tan"),
                  ("sin", "cos"), ("cos", "sin"),
                  ("sec", "cosec"), ("cosec", "sec")}
        _a1, _a2 = float(_comp.group(2)), float(_comp.group(4))
        if (_comp.group(1), _comp.group(3)) in _pairs \
                and abs(_a1 + _a2 - 90) < 1e-9:
            steps = [
                f"{_comp.group(3)} {_a2:g}° = "
                f"{_comp.group(3)} (90° - {_a1:g}°) = "
                f"{_comp.group(1)} {_a1:g}° (complementary "
                f"angles).",
                "So the ratio is 1.",
            ]
            return {
                "type": "trigonometry",
                "op": "complementary_ratio",
                "answer": "1", "steps": steps, "value": 1.0,
            }

    # --- Wave 32: standard values, "degrees" written out --------
    if "degrees" in qlow and re.search(
            r"\b(sin|cos|tan|sec|cosec|cot)\b", qlow):
        _t = qlow.replace("cosec", "csc")
        _t = re.sub(
            r"\b(sin|cos|tan|sec|csc|cot)\s*\^\s*2\s+"
            r"(\d+(?:\.\d+)?)\s*degrees?",
            r"(\1(\2*pi/180))^2", _t)
        _t = re.sub(
            r"\b(sin|cos|tan|sec|csc|cot)\s+"
            r"(\d+(?:\.\d+)?)\s*degrees?",
            r"\1(\2*pi/180)", _t)
        _t = re.sub(r"\b(evaluate|find|value of|calculate)\b",
                    "", _t).strip(" ?.=")
        try:
            _expr = parse_expression(_t)
            if not _expr.free_symbols:
                _val = sp.simplify(_expr)
                steps = [
                    "Use the standard values (sin 30 = 1/2, "
                    "cos 30 = sqrt(3)/2, sin 60 = sqrt(3)/2, "
                    "cos 60 = 1/2, ...).",
                    f"The expression simplifies to "
                    f"{fmt(_val)} ≈ "
                    f"{fmt_num(float(_val))}",
                ]
                return {
                    "type": "trigonometry", "op": "value",
                    "answer": fmt(_val), "steps": steps,
                    "value": float(_val),
                }
        except Exception:
            pass

    # Angle of elevation of a tower from a ground point.
    if "angle of elevation" in qlow:
        _degs = re.findall(r"(\d+(?:\.\d+)?)\s*(?:degrees?|°)",
                           qlow)
        _md = re.search(r"(\d+(?:\.\d+)?)\s*m\s+(?:away|from)\b",
                        qlow)
        if _degs and _md:
            _th = sp.Rational(_degs[-1])
            _d = sp.Rational(_md.group(1))
            _h = _d * sp.tan(_th * sp.pi / 180)
            steps = [
                "tan(angle of elevation) = height of the tower "
                "/ distance of the point from its foot",
                f"tan {fmt_num(_th)}° = h / {fmt_num(_d)}, so "
                f"h = {fmt_num(_d)} × tan {fmt_num(_th)}°",
                f"Height of the tower = {fmt(_h)} m "
                f"≈ {float(_h):.2f} m",
            ]
            return {
                "type": "trigonometry",
                "op": "heights_distances",
                "answer": f"{fmt(_h)} m ≈ {float(_h):.2f} m",
                "value": float(_h),
                "steps": steps,
            }

    # --- Plain value: sin 30, cos(pi/3), sin 30 + cos 60 ------------------
    text = q
    conversions = []
    if deg:
        text, conversions = _convert_degrees(text)
    expr = parse_expression(text)
    value = sp.simplify(expr)
    steps = []
    for fn, val in conversions:
        steps.append(
            f"{fn} {val}° = {fn}({val}·pi/180) "
            f"[converting degrees to radians]"
        )
    if not expr.free_symbols:
        steps.append(f"Evaluate: {fmt(value)} ≈ {fmt_num(float(value))}")
        return {
            "type": "trigonometry",
            "op": "value",
            "answer": fmt(value),
            "value": float(value),
            "steps": steps,
        }
    simplified = sp.trigsimp(value)
    steps.append(f"Simplify: {fmt(simplified)}")
    return {
        "type": "trigonometry",
        "op": "simplify",
        "answer": fmt(simplified),
        "steps": steps,
    }
