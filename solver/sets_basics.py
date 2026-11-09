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


def solve_sets(question: str):
    q = question.lower()
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
