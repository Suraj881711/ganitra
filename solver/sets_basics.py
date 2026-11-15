"""Sets basics: union, intersection, difference, symmetric difference."""
import re


def _parse_sets(text: str):
    sets = []
    for m in re.finditer(r"\{([^}]*)\}", text):
        items = [v.strip() for v in m.group(1).split(",") if v.strip()]
        parsed = []
        for v in items:
            try:
                parsed.append(int(v))
            except ValueError:
                try:
                    parsed.append(float(v))
                except ValueError:
                    parsed.append(v)
        sets.append(set(parsed))
    return sets


def _show(s) -> str:
    def key(v):
        return (0, v) if isinstance(v, (int, float)) else (1, str(v))
    return "{" + ", ".join(str(v) for v in sorted(s, key=key)) + "}"


def _cardinality56(q: str):
    """Wave 56: set COUNTING schemas (no literal sets) —
    the power-set count 2^n, inclusion-exclusion for
    n(A)/n(B)/n(A union B)/n(A intersection B) with any
    one of them missing, and the two-activity class form
    ("30 play cricket, 25 play football, 12 play both —
    how many play neither?"). solve_sets used to answer
    "Give me two sets" to all of these."""
    # Power set: |P(A)| = 2^n.
    # Wave 59: the plain subsets count is the same 2^n —
    # "a set has 5 elements, how many subsets does it have"
    # had no form (only the words "power set" triggered it).
    if "power set" in q or "subset" in q:
        m = re.search(r"(\d+)\s+elements", q)
        if m:
            n = int(m.group(1))
            return {"type": "sets", "op": "power_set",
                    "answer": str(2 ** n), "value": 2 ** n,
                    "steps": [
                        f"A set with {n} elements has "
                        f"2^{n} subsets, and the power set is "
                        f"the set of all its subsets.",
                        f"Number of elements in the power "
                        f"set = 2^{n} = {2 ** n}"]}
        return None
    # Two-activity class form.
    m = re.search(r"class\s+of\s+(\d+)", q)
    mp = re.findall(r"(\d+)\s+play\s+([a-z]+)", q)
    mb = re.search(r"(\d+)\s+play\s+both", q)
    if m and len(mp) >= 2 and mb:
        total, both = int(m.group(1)), int(mb.group(1))
        a, b = int(mp[0][0]), int(mp[1][0])
        union = a + b - both
        steps = [
            f"Students playing at least one game = "
            f"{a} + {b} - {both} (the {both} who play both "
            f"were counted twice) = {union}.",
        ]
        if "neither" in q:
            val = total - union
            steps.append(
                f"Playing neither = {total} - {union} "
                f"= {val}.")
            return {"type": "sets", "op": "play_neither",
                    "answer": str(val), "value": val,
                    "steps": steps}
        if "both" in q and "how many" in q:
            return {"type": "sets", "op": "play_both",
                    "answer": str(both), "value": both,
                    "steps": steps}
        return {"type": "sets", "op": "play_union",
                "answer": str(union), "value": union,
                "steps": steps}
    # n(...) notation: solve inclusion-exclusion for the
    # one missing quantity.
    singles = dict(re.findall(
        r"n\(\s*([a-z])\s*\)\s*=\s*(\d+)", q))
    mu = re.search(r"n\(\s*([a-z])\s*(?:union|∪)\s*([a-z])"
                   r"\s*\)\s*=\s*(\d+)", q)
    mi = re.search(r"n\(\s*([a-z])\s*(?:intersection|∩)\s*"
                   r"([a-z])\s*\)\s*=\s*(\d+)", q)
    if len(singles) >= 2 and (mu or mi):
        names = sorted(singles)
        a = int(singles[names[0]])
        b = int(singles[names[1]])
        ask_union = re.search(
            r"find\s+n\(\s*[a-z]\s*(?:union|∪)", q)
        ask_inter = re.search(
            r"find\s+n\(\s*[a-z]\s*(?:intersection|∩)", q)
        if mu and ask_inter:
            union = int(mu.group(3))
            val = a + b - union
            steps = [
                "n(A ∪ B) = n(A) + n(B) - n(A ∩ B)",
                f"{union} = {a} + {b} - n(A ∩ B), so "
                f"n(A ∩ B) = {a} + {b} - {union} = {val}",
            ]
            return {"type": "sets", "op": "cardinality",
                    "answer": str(val), "value": val,
                    "steps": steps}
        if mi and ask_union:
            inter = int(mi.group(3))
            val = a + b - inter
            steps = [
                "n(A ∪ B) = n(A) + n(B) - n(A ∩ B)",
                f"n(A ∪ B) = {a} + {b} - {inter} = {val}",
            ]
            return {"type": "sets", "op": "cardinality",
                    "answer": str(val), "value": val,
                    "steps": steps}
        # Wave 59: "find n(only A)" — elements in A but not B.
        _only59 = re.search(r"only\s+(?:in\s+)?([a-z])\b", q)
        if mi and _only59:
            inter = int(mi.group(3))
            base = a if _only59.group(1) == names[0] else b
            val = base - inter
            steps = [
                f"Elements only in {_only59.group(1).upper()} "
                f"= n({_only59.group(1).upper()}) - "
                f"n(A ∩ B)",
                f"= {base} - {inter} = {val}",
            ]
            return {"type": "sets", "op": "cardinality",
                    "answer": str(val), "value": val,
                    "steps": steps}
    return None


def solve_sets(question: str):
    q = question.lower()
    _card56 = _cardinality56(q)
    if _card56 is not None:
        return _card56
    sets = _parse_sets(question)
    if len(sets) < 2:
        return {"type": "sets", "op": "unknown",
                "answer": "Give me two sets, e.g. '{1,2,3} union "
                          "{3,4,5}'.",
                "steps": []}
    A, B = sets[0], sets[1]
    steps = [f"A = {_show(A)}", f"B = {_show(B)}"]
    if "symmetric" in q:
        res = A ^ B
        steps.append("Symmetric difference = elements in exactly one "
                     "of A and B.")
        op = "symmetric_difference"
    elif "intersection" in q or "∩" in question:
        res = A & B
        steps.append("Intersection = elements common to both A and B.")
        op = "intersection"
    elif re.search(r"only\s+in\s+a\b", q):
        # Wave 59: "elements only in A" is the difference
        # A - B; it used to fall into the union default.
        res = A - B
        steps.append("Only in A = elements of A that are not "
                     "in B (the difference A - B).")
        op = "difference"
    elif "difference" in q or re.search(r"\bA\s*-\s*B\b", question):
        res = A - B
        steps.append("Difference A - B = elements in A but not in B.")
        op = "difference"
    else:  # union is the default set operation
        res = A | B
        steps.append("Union = all elements that are in A or in B "
                     "(counted once).")
        op = "union"
    steps.append(f"Result: {_show(res)}")
    return {"type": "sets", "op": op, "answer": _show(res),
            "elements": sorted(res, key=lambda v: (0, v) if isinstance(
                v, (int, float)) else (1, str(v))),
            "steps": steps}
