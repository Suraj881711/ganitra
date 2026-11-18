"""Wave 103: audit-gap solver cleanup.

The Wave 81 starter-probing pass flagged eight solver gaps
(the concept layer could not author topics for them because a
topic needs a solver-verified worked example), and Wave 81
itself left exactly one concept ask unanswered. This module
closes them with METHOD schemas — each parses the student's
own numbers out of the question and computes:

1. Quadrilateral / polygon angle sums (360° for a
   quadrilateral, (n - 2) x 180° in general) and the fourth
   angle of a quadrilateral given the other three — the
   "chaturbhuj ke chaaro kono ka yog" leftover included.
2. Occurrence counting: how many times a digit occurs in
   1..N (counted place by place), and how many times a value
   occurs in a given data list.
3. n(A) / set cardinality read off a set literal.
4. (In fallback.py) polynomial degree — see degree_upgrade.
5. Degree <-> radian conversion, both directions, exact in
   pi where the value allows.
6. Quadrant identification for a point (and for an angle in
   degrees); a point on an axis is answered honestly as
   on-axis, never forced into a quadrant.
7. Sample-space counting and listing basics for one coin /
   one die (and a coin tossed twice) — the no-numeral forms
   papers10's outcome counter cannot see.
8. f(n) evaluation for the phrasings the router's own
   function path misses ("find the value of f(4)",
   "f(10) ka maan kya hoga").

Hooking: solver/router.py calls solve_gaps103 at the very
end of _solve_question_uncached, behind the same failure-only
gate as Waves 77/94 (_w77_needs_core), so a question the
solver already answers is never displaced — these schemas
only convert failures. Gap 4 is the exception: the primary
"simplify" path returns a plausible-looking expression for
"degree of <poly>" (it eats the words into the expression),
which the failure gate cannot see, so fallback.py consults
degree_upgrade() below as an upgrade hook next to the
Wave 95 proof upgrade — it fires only on a strict degree
ask whose current answer is not already the true degree.
"""

import math
import re
from fractions import Fraction

_DEV = str.maketrans("०१२३४५६७८९", "0123456789")


def _prep(q):
    s = str(q or "").translate(_DEV)
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    return s


def _hindi(q):
    return any("ऀ" <= ch <= "ॿ" for ch in str(q or ""))


def _mk(type_, op, answer, steps):
    return {"type": type_, "op": op, "answer": answer,
            "steps": steps}


_NUM = r"(-?\d+(?:\.\d+)?)"


def _num(text):
    f = float(text)
    return int(f) if f == int(f) else f


# ---------------------------------------------------------------------------
# 1a. Polygon angle sum (quadrilateral first — the Wave 81 leftover)
# ---------------------------------------------------------------------------

_POLY_SIDES = [
    (r"quadrilateral|chaturbhuj|चतुर्भुज|चतुर्भुज़", 4,
     "quadrilateral", "चतुर्भुज"),
    (r"pentagon|पंचभुज|panchbhuj", 5, "pentagon", "पंचभुज"),
    (r"hexagon|षट्भुज|shatbhuj", 6, "hexagon", "षट्भुज"),
    (r"heptagon|सप्तभुज", 7, "heptagon", "सप्तभुज"),
    (r"octagon|अष्टभुज", 8, "octagon", "अष्टभुज"),
    (r"triangle|त्रिभुज|tribhuj", 3, "triangle", "त्रिभुज"),
]


def _angle_sum(q):
    """Sum of interior angles: quadrilateral -> 360, named
    polygon / n-sided polygon -> (n - 2) x 180. Exterior sums
    are 360 for every polygon and are answered as such."""
    ql = q.lower()
    asks_sum = re.search(
        r"sum|total|yog|योग|जोड़|कुल", q, re.I)
    if not asks_sum:
        return None
    hi = _hindi(q)
    if re.search(r"exterior|बाह्य|bahari|bahya", q, re.I):
        # Any missing-angle wording belongs to the fourth-
        # angle schema, not this fact.
        if re.search(r"fourth|chautha|चौथा|missing|remaining",
                     q, re.I):
            return None
        steps = [
            "किसी भी बहुभुज के सभी बाह्य कोणों का योग हमेशा 360° होता है।"
            if hi else
            "The exterior angles of any polygon always add "
            "up to 360°."]
        return _mk("geometry", "w103_angle_sum", "360°", steps)
    if not re.search(r"angle|kon|कोण|interior|आंतरिक|antarik",
                     q, re.I):
        return None
    sides = None
    name_en = name_hi = None
    for pat, n, en, hin in _POLY_SIDES:
        if re.search(pat, q, re.I):
            sides, name_en, name_hi = n, en, hin
            break
    if sides is None:
        m = re.search(r"(\d+)\s*(?:sides?|भुजा|bhuja)", q, re.I)
        if m and re.search(r"polygon|बहुभुज", q, re.I):
            sides = int(m.group(1))
            name_en = f"{sides}-sided polygon"
            name_hi = f"{sides} भुजाओं वाला बहुभुज"
    if sides is None or sides < 3 or sides > 20:
        return None
    # A question carrying three concrete angles and asking
    # for the fourth is the fourth-angle schema's job.
    if re.search(r"fourth|chautha|चौथा", q, re.I):
        return None
    total = (sides - 2) * 180
    if hi:
        steps = [
            f"{name_hi} को एक विकर्ण से {sides - 2} त्रिभुजों "
            f"में बाँटा जा सकता है।",
            f"कोणों का योग = {sides - 2} × 180° = {total}°",
        ]
    elif sides == 3:
        steps = [
            "The three angles of a triangle always add up "
            "to 180°.",
            f"Sum of angles = (3 − 2) × 180° = {total}°",
        ]
    else:
        steps = [
            f"A {name_en} splits into {sides - 2} triangles "
            f"along its diagonals.",
            f"Sum of angles = {sides - 2} × 180° = {total}°",
        ]
    return _mk("geometry", "w103_angle_sum", f"{total}°", steps)


# ---------------------------------------------------------------------------
# 1b. Fourth angle of a quadrilateral
# ---------------------------------------------------------------------------

def _fourth_angle(q):
    if not re.search(r"quadrilateral|chaturbhuj|चतुर्भुज",
                     q, re.I):
        return None
    if not re.search(r"fourth|chautha|चौथा|missing|remaining|"
                     r"find|kitna|कितना|ज्ञात|calculate", q, re.I):
        return None
    vals = [float(v) for v in
            re.findall(r"(\d+(?:\.\d+)?)\s*°", q)]
    if len(vals) != 3:
        # Angles listed without the degree sign: only trust a
        # clean three-number list in an angle context.
        if re.search(r"angles?|kon|कोण", q, re.I):
            m = re.search(
                r"(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*"
                r"(?:,|and|aur|और|तथा)\s*(\d+(?:\.\d+)?)", q)
            if m:
                vals = [float(m.group(i)) for i in (1, 2, 3)]
    if len(vals) != 3:
        return None
    if any(v <= 0 or v >= 360 for v in vals):
        return None
    given = sum(vals)
    if given >= 360:
        return None
    fourth = 360 - given
    hi = _hindi(q)
    show = [str(int(v)) if v == int(v) else str(v) for v in vals]
    fshow = (str(int(fourth)) if fourth == int(fourth)
             else str(fourth))
    gshow = str(int(given)) if given == int(given) else str(given)
    if hi:
        steps = [
            "चतुर्भुज के चारों कोणों का योग 360° होता है।",
            f"चौथा कोण = 360° − ({' + '.join(show)}°) "
            f"= 360° − {gshow}° = {fshow}°",
        ]
    else:
        steps = [
            "The four angles of a quadrilateral add up to "
            "360°.",
            f"Fourth angle = 360° − ({' + '.join(show)}°) "
            f"= 360° − {gshow}° = {fshow}°",
        ]
    return _mk("geometry", "w103_fourth_angle", f"{fshow}°",
               steps)


# ---------------------------------------------------------------------------
# 2. Occurrence counting
# ---------------------------------------------------------------------------

def _digit_occurrences(digit, lo, hi_n):
    """Occurrences of `digit` in every integer lo..hi_n,
    counted place by place. Returns (total, [(place, count)])
    with place = 1, 10, 100, ... Only places that contribute
    are listed."""
    total = 0
    per_place = []
    place = 1
    while place <= hi_n:
        higher = hi_n // (place * 10)
        cur = (hi_n // place) % 10
        lower = hi_n % place
        if digit == 0:
            cnt = 0
            if higher > 0:
                cnt = (higher - 1) * place
                cnt += (lower + 1) if cur == 0 else place
        else:
            cnt = higher * place
            if cur > digit:
                cnt += place
            elif cur == digit:
                cnt += lower + 1
        if lo > 1:
            cnt -= _digit_occurrences_upto(digit, lo - 1, place)
        if cnt > 0:
            per_place.append((place, cnt))
            total += cnt
        place *= 10
    return total, per_place


def _digit_occurrences_upto(digit, n, place):
    """Occurrences of `digit` at one place in 1..n."""
    if n < 1:
        return 0
    higher = n // (place * 10)
    cur = (n // place) % 10
    lower = n % place
    if digit == 0:
        if higher == 0:
            return 0
        cnt = (higher - 1) * place
        cnt += (lower + 1) if cur == 0 else place
        return cnt
    cnt = higher * place
    if cur > digit:
        cnt += place
    elif cur == digit:
        cnt += lower + 1
    return cnt


_PLACE_NAMES = {1: "units", 10: "tens", 100: "hundreds",
                1000: "thousands", 10000: "ten-thousands",
                100000: "lakhs"}


def _occurrence(q):
    if not re.search(r"how many times|occur|appear|aata|आता|"
                     r"kitni\s*baar|कितनी\s*बार", q, re.I):
        return None
    hi = _hindi(q)
    # --- Form A: a digit in a range a..b -------------------
    digit = None
    m = (re.search(r"(?:digit|ank|अंक|number)\s*(\d)\b", q, re.I)
         or re.search(r"does\s+(?:the\s+)?(?:digit\s+|number\s+)?"
                      r"(\d)\b", q, re.I)
         or re.search(r"\b(\d)\s+kitni\s*baar", q, re.I)
         or re.search(r"अंक\s*(\d)", q))
    if m:
        digit = int(m.group(1))
    rng = (re.search(r"from\s+(\d+)\s+to\s+(\d+)", q, re.I)
           or re.search(r"(\d+)\s*(?:se|से)\s*(\d+)\s*(?:tak|तक)",
                        q, re.I)
           or re.search(r"between\s+(\d+)\s+and\s+(\d+)", q,
                        re.I))
    if digit is not None and rng:
        lo, hi_n = int(rng.group(1)), int(rng.group(2))
        if lo < 0 or hi_n < lo or hi_n - lo > 200000:
            return None
        total, per_place = _digit_occurrences(digit, lo, hi_n)
        if hi:
            steps = [f"{lo} से {hi_n} तक की संख्याओं में अंक "
                     f"{digit} गिनते हैं:"]
            for place, cnt in per_place:
                steps.append(f"स्थान {place} पर: {cnt} बार")
            steps.append(f"कुल = {total} बार")
        else:
            steps = [f"Count the digit {digit} in every number "
                     f"from {lo} to {hi_n}, place by place:"]
            for place, cnt in per_place:
                steps.append(
                    f"In the {_PLACE_NAMES.get(place, str(place))} "
                    f"place: {cnt} times")
            steps.append(f"Total = {total} times")
        return _mk("statistics", "w103_occurrence", str(total),
                   steps)
    # --- Form C: a digit inside one given number -----------
    m = (re.search(r"in the number\s+(\d+)", q, re.I)
         or re.search(r"संख्या\s*(\d+)", q))
    if m and digit is not None:
        s = m.group(1)
        total = s.count(str(digit))
        if hi:
            steps = [f"संख्या {s} में अंक {digit} कुल "
                     f"{total} बार आया है।"]
        else:
            steps = [f"In the number {s}, the digit {digit} "
                     f"appears {total} times."]
        return _mk("statistics", "w103_occurrence", str(total),
                   steps)
    # --- Form B: a value in a data list --------------------
    m = (re.search(r"does\s+(?:the\s+)?(?:digit\s+|number\s+)?"
                   r"(-?\d+(?:\.\d+)?)\s+(?:occur|appear)",
                   q, re.I)
         or re.search(r"(-?\d+(?:\.\d+)?)\s+kitni\s*baar", q,
                      re.I))
    if m:
        target = _num(m.group(1))
        rest = q[:m.start()] + " " + q[m.end():]
        lists = re.findall(
            r"-?\d+(?:\.\d+)?(?:\s*,\s*-?\d+(?:\.\d+)?){2,}",
            rest)
        if lists:
            items = [_num(v) for v in
                     re.findall(r"-?\d+(?:\.\d+)?", lists[0])]
            count = sum(1 for v in items if v == target)
            shown = ", ".join(
                str(int(v)) if float(v) == int(float(v))
                else str(v) for v in items)
            tshow = (str(int(target))
                     if float(target) == int(float(target))
                     else str(target))
            if hi:
                steps = [f"आँकड़े: {shown}",
                         f"इनमें {tshow} कुल {count} बार "
                         f"आया है।"]
            else:
                steps = [f"Data: {shown}",
                         f"The value {tshow} appears {count} "
                         f"times in this data."]
            return _mk("statistics", "w103_occurrence",
                       str(count), steps)
    return None


# ---------------------------------------------------------------------------
# 3. n(A) — cardinality of a set literal
# ---------------------------------------------------------------------------

def _set_elements(text):
    """Elements of a flat {...} literal, or None if the
    literal is nested or unparseable. Duplicates collapse —
    a set never counts an element twice."""
    if "{" in text or "}" in text:
        return None
    parts = [p.strip() for p in text.split(",")]
    if len(parts) == 1 and parts[0] == "":
        return []
    if any(p == "" for p in parts):
        return None
    return list(dict.fromkeys(parts))


def _set_cardinality(q):
    if re.search(r"∪|∩|union|intersection", q, re.I):
        return None
    asks = (re.search(r"n\s*\(\s*([A-Za-z])\s*\)", q)
            or re.search(r"how many elements|number of elements|"
                         r"cardinal|कितने अवयव|अवयवों की संख्या|"
                         r"kitne\s+avayav|elements?\s+are\s+"
                         r"(?:there\s+)?in", q, re.I))
    if not asks:
        return None
    labelled = {}
    plain = []
    for m in re.finditer(r"([A-Za-z])\s*=\s*\{([^}]*)\}", q):
        labelled[m.group(1)] = m.group(2)
    for m in re.finditer(r"\{([^}]*)\}", q):
        plain.append(m.group(1))
    letter = None
    body = None
    m = re.search(r"n\s*\(\s*([A-Za-z])\s*\)", q)
    if m:
        letter = m.group(1)
        if letter in labelled:
            body = labelled[letter]
        elif len(plain) == 1:
            body = plain[0]
        else:
            return None
    elif len(plain) == 1:
        body = plain[0]
        if labelled:
            letter = next(iter(labelled))
    else:
        return None
    elems = _set_elements(body)
    if elems is None:
        return None
    n = len(elems)
    hi = _hindi(q)
    shown = "{" + ", ".join(elems) + "}"
    if hi:
        steps = [f"समुच्चय = {shown}",
                 f"अवयव गिनने पर कुल {n} अवयव हैं।"]
        if letter:
            steps.append(f"n({letter}) = {n}")
    else:
        steps = [f"The set is {shown}",
                 f"Counting its distinct elements gives {n}."]
        if letter:
            steps.append(f"n({letter}) = {n}")
    return _mk("sets", "w103_cardinality", str(n), steps)


# ---------------------------------------------------------------------------
# 5. Degree <-> radian conversion
# ---------------------------------------------------------------------------

def _deg_rad(q):
    if not re.search(r"radian|रेडियन", q, re.I):
        return None
    if not re.search(r"convert|badl|बदल|express|in\s+radian|"
                     r"in\s+degree|equal|kitn|कितन|मान|value|"
                     r"measure", q, re.I):
        return None
    hi = _hindi(q)
    # --- radians -> degrees --------------------------------
    m = re.search(
        r"(\d+(?:\.\d+)?)?\s*(?:pi|π)\s*"
        r"(?:/\s*(\d+(?:\.\d+)?))?\s*(?:radian|रेडियन|rad\b)",
        q, re.I)
    plain = None
    if m is None:
        plain = re.search(
            r"(-?\d+(?:\.\d+)?)\s*(?:radian|रेडियन|rad\b)",
            q, re.I)
    if m is not None or plain is not None:
        if m is not None:
            num = float(m.group(1)) if m.group(1) else 1.0
            den = float(m.group(2)) if m.group(2) else 1.0
            rad_frac = Fraction(num).limit_denominator(1000) \
                / Fraction(den).limit_denominator(1000)
            deg = rad_frac * 180
            rad_show = ("π" if rad_frac == 1 else
                        f"{rad_frac}π" if rad_frac.denominator == 1
                        else f"π/{rad_frac.denominator}"
                        if rad_frac.numerator == 1
                        else f"{rad_frac.numerator}π/"
                             f"{rad_frac.denominator}")
            if deg.denominator == 1:
                deg_show = str(deg.numerator)
                steps = [
                    f"{rad_show} radian = {rad_show} × "
                    f"(180/π)°" if not hi else
                    f"{rad_show} रेडियन = {rad_show} × "
                    f"(180/π)°",
                    f"= {deg_show}°",
                ]
                return _mk("trigonometry", "w103_rad_to_deg",
                           f"{deg_show}°", steps)
            deg_f = float(deg)
            return _mk("trigonometry", "w103_rad_to_deg",
                       f"{deg_f:.4g}°",
                       [f"{rad_show} radian × (180/π) = "
                        f"{deg_f:.4g}°"])
        val = float(plain.group(1))
        deg_f = val * 180.0 / math.pi
        deg_show = (str(int(deg_f)) if deg_f == int(deg_f)
                    else f"{deg_f:.4g}")
        steps = [
            f"1 radian = 180/π degrees ≈ 57.3°" if not hi else
            "1 रेडियन = 180/π डिग्री ≈ 57.3°",
            f"{plain.group(1)} radian = {plain.group(1)} × "
            f"57.2958° ≈ {deg_show}°",
        ]
        return _mk("trigonometry", "w103_rad_to_deg",
                   f"{deg_show}°", steps)
    # --- degrees -> radians --------------------------------
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:degrees?|°|डिग्री)",
                  q, re.I)
    if m is None:
        return None
    deg = Fraction(m.group(1))
    rad = deg / 180  # in units of pi
    if rad.denominator == 1:
        rad_show = "π" if rad == 1 else f"{rad.numerator}π"
    elif rad.numerator == 1:
        rad_show = f"π/{rad.denominator}"
    else:
        rad_show = f"{rad.numerator}π/{rad.denominator}"
    approx = float(rad) * math.pi
    deg_show = (str(deg.numerator) if deg.denominator == 1
                else m.group(1))
    if hi:
        steps = [
            "डिग्री को रेडियन में बदलने के लिए π/180 से गुणा "
            "करते हैं।",
            f"{deg_show}° = {deg_show} × π/180 = {rad_show} "
            f"रेडियन ≈ {approx:.4g}",
        ]
    else:
        steps = [
            "To change degrees into radians, multiply by "
            "π/180.",
            f"{deg_show}° = {deg_show} × π/180 = {rad_show} "
            f"radians ≈ {approx:.4g}",
        ]
    return _mk("trigonometry", "w103_deg_to_rad",
               f"{rad_show} radians", steps)


# ---------------------------------------------------------------------------
# 6. Quadrant identification
# ---------------------------------------------------------------------------

_QUAD_EN = {1: "First quadrant (I)", 2: "Second quadrant (II)",
            3: "Third quadrant (III)",
            4: "Fourth quadrant (IV)"}
_QUAD_HI = {1: "प्रथम चतुर्थांश (I)", 2: "द्वितीय चतुर्थांश (II)",
            3: "तृतीय चतुर्थांश (III)",
            4: "चतुर्थ चतुर्थांश (IV)"}


def _quadrant_of_signs(x, y):
    if x > 0 and y > 0:
        return 1
    if x < 0 and y > 0:
        return 2
    if x < 0 and y < 0:
        return 3
    if x > 0 and y < 0:
        return 4
    return 0


def _quadrant(q):
    if not re.search(r"quadrant|चतुर्थांश|chaturthansh", q,
                     re.I):
        return None
    hi = _hindi(q)
    m = re.search(r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*"
                  r"(-?\d+(?:\.\d+)?)\s*\)", q)
    if m:
        x, y = float(m.group(1)), float(m.group(2))
        xs = m.group(1)
        ys = m.group(2)
        quad = _quadrant_of_signs(x, y)
        if quad == 0:
            if x == 0 and y == 0:
                ans = ("मूल बिंदु (origin)" if hi
                       else "The origin")
                steps = ["बिंदु (0, 0) मूल बिंदु है — यह किसी "
                         "चतुर्थांश में नहीं होता।" if hi else
                         "The point (0, 0) is the origin — it "
                         "lies in no quadrant."]
            elif x == 0:
                ans = "y-axis" if not hi else "y-अक्ष"
                steps = [f"x = 0 है, इसलिए बिंदु ({xs}, {ys}) "
                         f"y-अक्ष पर स्थित है — किसी चतुर्थांश "
                         f"में नहीं।" if hi else
                         f"x = 0, so the point ({xs}, {ys}) "
                         f"lies on the y-axis — in no quadrant."]
            else:
                ans = "x-axis" if not hi else "x-अक्ष"
                steps = [f"y = 0 है, इसलिए बिंदु ({xs}, {ys}) "
                         f"x-अक्ष पर स्थित है — किसी चतुर्थांश "
                         f"में नहीं।" if hi else
                         f"y = 0, so the point ({xs}, {ys}) "
                         f"lies on the x-axis — in no quadrant."]
            return _mk("geometry", "w103_quadrant", ans, steps)
        sx = "+" if x > 0 else "−"
        sy = "+" if y > 0 else "−"
        if hi:
            steps = [
                f"बिंदु ({xs}, {ys}): x {sx} है और y {sy} है।",
                f"चिह्न ({sx}, {sy}) वाला बिंदु "
                f"{_QUAD_HI[quad]} में होता है।",
            ]
            ans = _QUAD_HI[quad]
        else:
            steps = [
                f"Point ({xs}, {ys}): x is "
                f"{'positive' if x > 0 else 'negative'} and y "
                f"is {'positive' if y > 0 else 'negative'}.",
                f"Signs ({sx}, {sy}) place it in the "
                f"{_QUAD_EN[quad]}.",
            ]
            ans = _QUAD_EN[quad]
        return _mk("geometry", "w103_quadrant", ans, steps)
    # Angle in degrees, standard position.
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:°|degrees?)", q,
                  re.I)
    if m:
        ang = float(m.group(1)) % 360
        if ang in (0, 90, 180, 270):
            steps = [f"{m.group(1)}° एक अक्ष पर पड़ता है — "
                     f"किसी चतुर्थांश में नहीं।" if hi else
                     f"{m.group(1)}° lies on an axis — in no "
                     f"quadrant."]
            return _mk("geometry", "w103_quadrant",
                       "On an axis" if not hi else "अक्ष पर",
                       steps)
        quad = int(ang // 90) + 1
        if hi:
            steps = [f"{m.group(1)}° का कोण "
                     f"{_QUAD_HI[quad]} में पड़ता है।"]
            return _mk("geometry", "w103_quadrant",
                       _QUAD_HI[quad], steps)
        steps = [f"An angle of {m.group(1)}° lies in the "
                 f"{_QUAD_EN[quad]}."]
        return _mk("geometry", "w103_quadrant", _QUAD_EN[quad],
                   steps)
    return None


# ---------------------------------------------------------------------------
# 7. Sample space — one coin / one die basics
# ---------------------------------------------------------------------------

def _sample_space(q):
    if re.search(r"probabilit|प्रायिकता|prayikta", q, re.I):
        return None
    asks = re.search(r"sample\s*space|how many outcomes|"
                     r"outcomes?|परिणाम|parinaam|प्रतिदर्श|"
                     r"kitne.*sambhav|संभाव", q, re.I)
    if not asks:
        return None
    hi = _hindi(q)
    list_ask = re.search(r"sample\s*space|प्रतिदर्श|list|"
                         r"लिख", q, re.I)
    is_coin = re.search(r"coin|सिक्क|सिक्का|sikka", q, re.I)
    is_die = re.search(r"\bdie\b|\bdice\b|पासा|पासे|pasa\b",
                       q, re.I)
    twice = re.search(r"twice|two times|दो बार|do baar", q,
                      re.I)
    if is_coin and not is_die:
        if twice:
            outcomes = ["HH", "HT", "TH", "TT"]
            if list_ask:
                ans = "{" + ", ".join(outcomes) + "}"
            else:
                ans = "4"
            steps = [
                "एक सिक्के को दो बार उछालने पर हर बार H या T "
                "आ सकता है।" if hi else
                "Tossing one coin twice gives H or T each "
                "time.",
                "Sample space = {HH, HT, TH, TT} — "
                "कुल 4 परिणाम।" if hi else
                "Sample space = {HH, HT, TH, TT} — 4 outcomes "
                "in all.",
            ]
            return _mk("probability", "w103_sample_space",
                       ans, steps)
        if list_ask:
            ans = "{H, T}"
        else:
            ans = "2"
        steps = [
            "सिक्का उछालने पर दो ही परिणाम संभव हैं: चित "
            "(H) या पट (T)।" if hi else
            "A tossed coin can only land Heads (H) or "
            "Tails (T).",
            "Sample space S = {H, T}, इसलिए n(S) = 2।" if hi
            else "Sample space S = {H, T}, so n(S) = 2.",
        ]
        return _mk("probability", "w103_sample_space", ans,
                   steps)
    if is_die and not is_coin:
        if twice:
            steps = [
                "एक पासे के 6 परिणाम होते हैं; दो बार फेंकने "
                "पर कुल 6 × 6 = 36 परिणाम होते हैं।" if hi
                else "One die has 6 outcomes; thrown twice "
                "that gives 6 × 6 = 36 outcomes.",
            ]
            return _mk("probability", "w103_sample_space",
                       "36", steps)
        if list_ask:
            ans = "{1, 2, 3, 4, 5, 6}"
        else:
            ans = "6"
        steps = [
            "पासा फेंकने पर 1 से 6 तक कोई भी संख्या आ सकती "
            "है।" if hi else
            "A thrown die can show any number from 1 to 6.",
            "Sample space S = {1, 2, 3, 4, 5, 6}, इसलिए "
            "n(S) = 6।" if hi else
            "Sample space S = {1, 2, 3, 4, 5, 6}, so "
            "n(S) = 6.",
        ]
        return _mk("probability", "w103_sample_space", ans,
                   steps)
    return None


# ---------------------------------------------------------------------------
# 8. f(n) evaluation — the phrasings the router misses
# ---------------------------------------------------------------------------

def _function_value(q):
    if "f'" in q or "f '" in q or "derivative" in q.lower() \
            or "differentiat" in q.lower():
        return None
    m = re.search(r"f\s*\(\s*x\s*\)\s*=\s*([^,;]+)", q, re.I)
    if not m:
        return None
    expr_text = m.group(1).strip().rstrip(".?")
    # The definition may run straight into the ask with no
    # comma ("f(x) = 2x - 5 hai to f(10) ka maan..."): cut at
    # the target f( and at Roman-Hindi filler, then let the
    # parse loop below trim any remaining trailing words.
    expr_text = re.split(r"f\s*\(", expr_text)[0]
    expr_text = re.split(r"\s+(?:hai|hain|toh)\b", expr_text)[0]
    targets = re.findall(r"f\s*\(\s*(-?\d+(?:\.\d+)?)\s*\)",
                         q)
    uniq = {t for t in targets}
    if len(uniq) != 1:
        return None
    if not re.search(r"find|value|evaluate|maan|मान|ज्ञात|"
                     r"gyat|calculate|what|kya|क्या|nikal",
                     q, re.I):
        return None
    from .papers10 import _sympify
    import sympy as sp
    x = sp.symbols("x")
    expr = None
    toks = expr_text.split()
    for cut in range(len(toks), 0, -1):
        cand = " ".join(toks[:cut]).rstrip(".?,")
        e = _sympify(cand)
        if e is not None and e.free_symbols <= {x}:
            expr = e
            break
    if expr is None:
        return None
    n_text = targets[0]
    n = Fraction(n_text)
    try:
        val = expr.subs(x, sp.nsimplify(n_text, rational=True))
        val = sp.simplify(val)
    except Exception:
        return None
    if val.has(sp.zoo, sp.nan, sp.oo):
        return None
    from .expression_parser import fmt_num
    val_show = fmt_num(val)
    n_show = (str(n.numerator) if n.denominator == 1
              else n_text)
    expr_show = str(expr).replace("**", "^").replace("*", "·")
    hi = _hindi(q)
    if hi:
        steps = [
            f"f(x) = {expr_show}",
            f"x = {n_show} रखने पर: f({n_show}) = {val_show}",
        ]
    else:
        steps = [
            f"f(x) = {expr_show}",
            f"Put x = {n_show}: f({n_show}) = {val_show}",
        ]
    return _mk("algebra", "w103_function_value",
               f"f({n_show}) = {val_show}", steps)


# ---------------------------------------------------------------------------
# 4. Degree upgrade (consulted by fallback.py, Wave 95 style)
# ---------------------------------------------------------------------------

def degree_upgrade(question, result):
    """For a polynomial-degree ask whose served result is
    NOT the true degree (the primary simplify path eats
    'degree of 3x^3...' into the expression and returns the
    mangled expression as its answer), return the verified
    degree result from papers10's own degree schema.
    Returns None — leave the result untouched — for every
    other question, including differential-equation degree
    asks (Wave 100's territory) and asks whose answer
    already IS the degree."""
    if not isinstance(result, dict):
        return None
    if result.get("op") == "w94_poly_degree":
        return None
    q = str(question or "")
    ql = q.lower()
    if "differential" in ql or "dy/dx" in ql or "order" in ql:
        return None
    # Wave 156 (Wave 153 audit book-022): a proof / verify
    # prompt that merely MENTIONS a degree ("verify that
    # ... is a homogeneous equation of degree two") is not
    # a degree ask — the upgrade harvested the combined
    # equation's degree (1) and served it as the answer.
    # Proof prompts abstain, and the degree must be ASKED
    # ("degree of ...", "what is the degree", घात), not
    # just named.
    if re.search(r"\bprove\b|\bshow that\b|\bverify\b|"
                 r"\bv\s+erify\b|सिद्ध", q, re.I):
        return None
    if not re.search(r"\bdegree\s+of\b|what\s+is\s+the\s+"
                     r"degree|find\s+(?:the\s+)?degree|घात",
                     q, re.I):
        return None
    try:
        from .papers10 import _poly_degree, _prep as _p10_prep
        deg_result = _poly_degree(_p10_prep(q))
    except Exception:
        return None
    if deg_result is None:
        return None
    if str(result.get("answer", "")).strip() == \
            str(deg_result.get("answer", "")).strip():
        return None
    return deg_result


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_SCHEMAS = [
    _fourth_angle, _angle_sum, _occurrence, _set_cardinality,
    _deg_rad, _quadrant, _sample_space, _function_value,
]


# Proof asks belong to the proof layer (or to an honest
# not-found — test_wave95 pins "Prove that the sum of the
# angles of a triangle is 180 degrees" as a fall-through),
# and why/explain asks belong to the concept layer
# (test_wave75 pins "tribhuj ke teeno kono ka yog 180 hi
# kyun hota hai?" to its topic; test_wave81 pins "sikka
# uchale to sample space kya banega samjhao?" likewise).
# None of these schemas may touch them.
_VETO = re.compile(
    r"\bprove\b|\bproof\b|siddh|सिद्ध|साबित|saabit|"
    r"\bwhy\b|kyun|kyon|क्यों|samjh|समझ|\bexplain\b",
    re.I)


def solve_gaps103(question):
    """Wave 103 entry point: the audit-gap method schemas.
    Returns a solver result dict or None. Called by the
    router only when the primary solve failed, so a None
    here leaves behaviour byte-identical."""
    q = _prep(question)
    if not q.strip():
        return None
    if _VETO.search(q):
        return None
    for schema in _SCHEMAS:
        try:
            out = schema(q)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
