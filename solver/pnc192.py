"""Wave 192: Permutations & Combinations counting WORD forms.

Why this module exists (form audit, 19 Nov 2026, item B.7 /
table row 21; spot-check probes 25 and 26): statistics.py
computes nPr / nCr only from the explicit "nPr" / "nCr" /
structured choose dress, so the NCERT Ex 6.1-6.4 WORD forms
had no parser at all and both audit probes parse-errored:

  25  "In how many ways can a team of 3 boys and 3 girls be
       selected from 5 boys and 4 girls?"            -> 40
  26  "A committee of 7 has to be formed from 9 boys and
       4 girls. In how many ways can this be done when
       the committee consists of exactly 3 girls?"  -> 504

This module is that word-form parser, in the house style of
Waves 169/175: it fires only when a strict schema settles
the question COMPLETELY, every count is an exact integer
(math.comb / math.perm / math.factorial, or an exact
subset-DP for digit numbers), and anything doubtful returns
None so routing continues unchanged.  Wiring: a failure-only
gate at the end of router._solve_question_uncached, after
the Wave 175 block — a question the solver already answers
(explicit nCr/nPr, factorial, probability schemas, named-
polygon diagonals) is never displaced.

Families (general schemas, never one-question patches):
  A. Selections from group pools: mixed explicit splits
     (a of group A and b of group B), total size with an
     exactly / at least / at most condition on one group
     (the range is summed mechanically), a two-group pool
     with a bare total, and plain single-group selection.
     Group nouns are generic (boys/girls, men/women,
     students, persons/people, members, ...); simple
     Hinglish-Roman dresses ("kitne tarike se ... me se
     ... chune", ladke/ladkiyan) follow the same schemas.
  B. Letter arrangements of a named word: plain (repeats
     divided out from the word itself), vowels together /
     consonants together (block as one unit, internal
     arrangements of the block's own multiset), and vowels
     (or consonants) occupying even / odd places.
  C. Digit numbers: a stated length, a stated digit set
     (list or range dress), repetition allowed / not
     allowed (must be stated), and positional conditions —
     even / odd / divisible by 5 or 10 (units digit),
     begins with a stated digit string.  Counting is exact:
     a subset DP over positions when repetition is off
     (so the leading-zero / units-digit interaction is
     never approximated), a per-position product when
     repetition is on.  Any other divisor, a greater-than
     bound, or an unstated repetition rule declines.
  D. Geometric counting that reduces to C(n, 2) / C(n, 3):
     chords through n points on a circle, handshakes among
     n people, diagonals of an n-sided polygon
     (C(n, 2) - n), straight lines and triangles from n
     points (with the collinear-points subtraction only
     when stated plainly), and arranging n distinct
     people / objects in a row (n!).

Probability questions decline outright: counting inside a
probability ask belongs to statistics.py's own schemas.
Steps stay English, as everywhere in the solver.
"""
import re
from math import comb, factorial

# ------------------------------------------------------------------
# small helpers
# ------------------------------------------------------------------

_NUM_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30,
}
_NUM = (r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|"
        r"ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
        r"seventeen|eighteen|nineteen|twenty|thirty)")


def _n(tok):
    tok = str(tok).strip().lower()
    if tok.isdigit():
        return int(tok)
    return _NUM_WORDS.get(tok)


def _comb(n, k):
    """C(n, k) with the counting convention: an impossible
    selection (k < 0 or k > n) contributes 0, never an error."""
    if n < 0 or k < 0 or k > n:
        return 0
    return comb(n, k)


def _result(answer, steps):
    return {"type": "statistics", "op": "pnc_word",
            "answer": str(answer), "value": int(answer),
            "steps": steps}


def _factorial_str(n):
    if n <= 1:
        return "1"
    if n <= 10:
        return " × ".join(str(i) for i in range(n, 0, -1))
    return f"{n} × {n - 1} × ... × 1"


# ------------------------------------------------------------------
# A. selections from group pools
# ------------------------------------------------------------------

_GROUPS = {
    "boys": "boy", "boy": "boy",
    "girls": "girl", "girl": "girl",
    "men": "man", "man": "man",
    "women": "woman", "woman": "woman",
    "students": "student", "student": "student",
    "persons": "person", "person": "person",
    "people": "person",
    "members": "member", "member": "member",
    "children": "child", "child": "child",
    "teachers": "teacher", "teacher": "teacher",
    "players": "player", "player": "player",
    "candidates": "candidate", "candidate": "candidate",
    "workers": "worker", "worker": "worker",
    "ladies": "lady", "lady": "lady",
    "gentlemen": "gentleman", "gentleman": "gentleman",
    "officers": "officer", "officer": "officer",
    # Hinglish-Roman group nouns (statistics.py's Hindi
    # probability block uses the same Roman spellings).
    "ladke": "boy", "ladka": "boy", "ladko": "boy",
    "ladkiyan": "girl", "ladki": "girl", "ladkiyo": "girl",
}
_G = (r"(?:boys|girls|men|women|students|persons|people|"
      r"members|children|teachers|players|candidates|workers|"
      r"ladies|gentlemen|officers|boy|girl|man|woman|student|"
      r"person|member|child|teacher|player|candidate|worker|"
      r"lady|gentleman|officer|ladke|ladka|ladko|ladkiyan|"
      r"ladki|ladkiyo)")
_PLURAL = {"boy": "boys", "girl": "girls", "man": "men",
           "woman": "women", "student": "students",
           "person": "people", "member": "members",
           "child": "children", "teacher": "teachers",
           "player": "players", "candidate": "candidates",
           "worker": "workers", "lady": "ladies",
           "gentleman": "gentlemen", "officer": "officers"}


def _grp(word):
    return _GROUPS.get(word.lower())


def _pool_pair(ql):
    """Two-group pool {group: count} from a 'from ...' clause
    or a 'there are ...' statement, or None."""
    m = re.search(r"from\s+(?:a\s+total\s+of\s+)?(" + _NUM +
                  r")\s+(" + _G + r")\s+and\s+(" + _NUM +
                  r")\s+(" + _G + r")", ql)
    if not m:
        m = re.search(r"(?:there\s+are|there\s+is|has|have)\s+("
                      + _NUM + r")\s+(" + _G + r")\s+and\s+("
                      + _NUM + r")\s+(" + _G + r")", ql)
    if m:
        a, b = _grp(m.group(2)), _grp(m.group(4))
        na, nb = _n(m.group(1)), _n(m.group(3))
        if a and b and a != b and na is not None and nb is not None:
            return {a: na, b: nb}
    return None


def _pool_single(ql):
    """Single-group pool (count, group) from a 'from' clause."""
    m = re.search(r"from\s+(?:a\s+total\s+of\s+)?(" + _NUM +
                  r")\s+(" + _G + r")\b", ql)
    if m:
        g = _grp(m.group(2))
        n = _n(m.group(1))
        if g and n is not None:
            return n, g
    return None


def _split_pair(ql):
    """Explicit split {group: count}: 'team/committee of
    a A and b B' or 'a A and b B be selected/chosen'."""
    m = re.search(r"(?:team|committee|group|selection|"
                  r"delegation)\s+of\s+(" + _NUM + r")\s+(" +
                  _G + r")\s+and\s+(" + _NUM + r")\s+(" +
                  _G + r")", ql)
    if not m:
        m = re.search(r"(" + _NUM + r")\s+(" + _G +
                      r")\s+and\s+(" + _NUM + r")\s+(" + _G +
                      r")\s+(?:be\s+)?(?:selected|chosen|taken|"
                      r"picked)", ql)
    if m:
        a, b = _grp(m.group(2)), _grp(m.group(4))
        ka, kb = _n(m.group(1)), _n(m.group(3))
        if a and b and a != b and ka is not None and kb is not None:
            return {a: ka, b: kb}
    return None


def _total_size(ql):
    """The selection's total size from 'committee/team/group
    of T' (T not followed by a group noun — that is a split)
    or a bare 'select/choose T'."""
    m = re.search(r"(?:committee|team|group|delegation)\s+of\s+("
                  + _NUM + r")\b(?!\s+" + _G + r"\b)", ql)
    if m:
        return _n(m.group(1))
    m = re.search(r"(?:select|choose|pick|take)\s+(?:any\s+)?("
                  + _NUM + r")\b", ql)
    if m:
        return _n(m.group(1))
    return None


def _condition(ql):
    """(kind, k, group) for exactly / at least / at most /
    consists-of conditions, or None."""
    pats = [
        (r"exactly\s+(" + _NUM + r")\s+(" + _G + r")\b", "exactly"),
        (r"at\s+least\s+(" + _NUM + r")\s+(" + _G + r")\b", "at least"),
        (r"not\s+less\s+than\s+(" + _NUM + r")\s+(" + _G + r")\b",
         "at least"),
        (r"at\s+most\s+(" + _NUM + r")\s+(" + _G + r")\b", "at most"),
        (r"not\s+more\s+than\s+(" + _NUM + r")\s+(" + _G + r")\b",
         "at most"),
        (r"(?:consists?|consisting|contains?|containing|having)"
         r"\s+of\s+(" + _NUM + r")\s+(" + _G + r")\b", "exactly"),
        (r"(?:consists?|contains?)\s+(" + _NUM + r")\s+(" + _G +
         r")\b", "exactly"),
    ]
    for pat, kind in pats:
        m = re.search(pat, ql)
        if m:
            k, g = _n(m.group(1)), _grp(m.group(2))
            if k is not None and g:
                return kind, k, g
    return None


def _sel_steps_product(terms):
    """terms = [(n, k, group)] -> (total, steps)."""
    total = 1
    parts = []
    steps = []
    for n, k, g in terms:
        v = _comb(n, k)
        total *= v
        parts.append(f"C({n}, {k})")
        steps.append(f"Choose {k} {_PLURAL[g]} from {n}: "
                     f"C({n}, {k}) = {v}")
    if len(terms) > 1:
        steps.append("Multiply the independent choices: "
                     + " × ".join(parts) + f" = {total}")
    return total, steps


def _selections(q, ql):
    # Three-or-more counted groups are outside these
    # schemas: a pair pattern would silently drop the
    # third group and serve a wrong count.
    counted = {_grp(mm.group(2)) for mm in
               re.finditer(r"(" + _NUM + r")\s+(" + _G + r")\b",
                           ql)}
    counted.discard(None)
    if len(counted) > 2:
        return None
    # Hinglish split dress: "<pool> me se <split>" — the pool
    # sits before 'me se', the chosen counts after it.
    if "me se" in ql or "mein se" in ql:
        seg = re.split(r"mein\s+se|me\s+se", ql, maxsplit=1)
        if len(seg) == 2 and ("kitne tarike" in ql
                              or "chun" in ql or "select" in ql
                              or "choose" in ql):
            before, after = seg
            pool = {}
            for mm in re.finditer(r"(" + _NUM + r")\s+(" + _G +
                                  r")\b", before):
                g = _grp(mm.group(2))
                if g:
                    pool[g] = _n(mm.group(1))
            chosen = {}
            for mm in re.finditer(r"(" + _NUM + r")\s+(" + _G +
                                  r")\b", after):
                g = _grp(mm.group(2))
                if g:
                    chosen[g] = _n(mm.group(1))
            if pool and chosen and set(chosen) <= set(pool) \
                    and len(chosen) == len(pool):
                terms = [(pool[g], chosen[g], g) for g in pool]
                total, steps = _sel_steps_product(terms)
                return _result(total, steps)
            if len(pool) == 1 and not chosen:
                mm = re.search(r"(" + _NUM + r")\b", after)
                if mm:
                    (g, n), k = next(iter(pool.items())), _n(mm.group(1))
                    if k is not None:
                        total, steps = _sel_steps_product([(n, k, g)])
                        return _result(total, steps)
        # An English 'from' dress never contains 'me se';
        # if the Hinglish parse failed, fall through only
        # when the text also carries English selection words.
        if not re.search(r"\bfrom\b|\bselected\b|\bcommittee\b|"
                         r"\bteam\b", ql):
            return None

    pool2 = _pool_pair(ql)
    split = _split_pair(ql)
    if pool2 and split and set(split) == set(pool2):
        terms = [(pool2[g], split[g], g) for g in pool2]
        total, steps = _sel_steps_product(terms)
        return _result(total, steps)

    total_size = _total_size(ql)
    if pool2 and total_size is not None:
        cond = _condition(ql)
        if cond is not None:
            kind, k, g = cond
            if g not in pool2:
                return None
            other = next(x for x in pool2 if x != g)
            ng, no = pool2[g], pool2[other]
            lo = max(0, total_size - no)
            hi = min(ng, total_size)
            if kind == "exactly":
                ks = [k]
            elif kind == "at least":
                ks = list(range(max(k, lo), hi + 1))
            else:
                ks = list(range(lo, min(k, hi) + 1))
            steps = [
                f"The selection has {total_size} members: "
                f"j {_PLURAL[g]} and {total_size} - j "
                f"{_PLURAL[other]}, summed over the allowed j "
                f"({kind} {k} {_PLURAL[g]})."]
            total = 0
            for j in ks:
                term = _comb(ng, j) * _comb(no, total_size - j)
                total += term
                steps.append(
                    f"j = {j}: C({ng}, {j}) × "
                    f"C({no}, {total_size - j}) = "
                    f"{_comb(ng, j)} × {_comb(no, total_size - j)}"
                    f" = {term}")
            if not ks:
                steps.append(
                    f"No value of j is possible, so the count "
                    f"is 0.")
            else:
                steps.append(f"Add the cases: total = {total}")
            return _result(total, steps)
        # Bare total from a two-group pool: choose from the
        # combined pool.
        n_all = sum(pool2.values())
        v = _comb(n_all, total_size)
        steps = [
            f"Pool together: {' + '.join(str(v2) for v2 in pool2.values())}"
            f" = {n_all} people",
            f"Choose {total_size} from {n_all}: "
            f"C({n_all}, {total_size}) = {v}"]
        return _result(v, steps)

    # Plain single-group selection.
    single = _pool_single(ql)
    if single is not None:
        n, g = single
        if total_size is not None and total_size != n:
            v = _comb(n, total_size)
            steps = [f"Choose {total_size} {_PLURAL[g]} from "
                     f"{n}: C({n}, {total_size}) = {v}"]
            return _result(v, steps)
        m = re.search(r"(" + _NUM + r")\s+(" + _G +
                      r")\s+(?:can\s+be\s+|to\s+be\s+|be\s+)?"
                      r"(?:selected|chosen|picked)\b", ql)
        if m and _grp(m.group(2)) == g:
            k = _n(m.group(1))
            if k is not None and k != n:
                v = _comb(n, k)
                steps = [f"Choose {k} {_PLURAL[g]} from {n}: "
                         f"C({n}, {k}) = {v}"]
                return _result(v, steps)
    return None


# ------------------------------------------------------------------
# B. letter arrangements
# ------------------------------------------------------------------

_VOWELS = set("AEIOU")


def _multiset_factorial(items):
    """(count!, repeat counts) for a list of letters."""
    from collections import Counter
    counts = Counter(items)
    denom = 1
    for c in counts.values():
        denom *= factorial(c)
    return factorial(len(items)) // denom, counts


def _repeat_note(counts, letters_desc):
    reps = [f"{ch} × {c}" for ch, c in sorted(counts.items())
            if c > 1]
    if not reps:
        return None
    return (f"Repeated letters in {letters_desc}: "
            + ", ".join(reps))


def _letters(q, ql):
    if "letter" not in ql:
        return None
    m = re.search(r"letters?\s+of\s+(?:the\s+)?word\s+\"?"
                  r"([A-Za-z]{2,})\"?", q, re.I)
    word = None
    if m:
        word = m.group(1).upper()
    if word is None:
        # A bare all-caps token next to 'letters'.
        m = re.search(r"\b([A-Z]{3,})\b", q)
        if m:
            word = m.group(1)
    if word is None or not word.isalpha():
        return None
    if not re.search(r"arrang|formed|bana", ql):
        return None
    # "vowels never / not together", "no two vowels
    # together" — a separation condition this family does
    # not model exactly; decline rather than serve the
    # together count for its opposite.
    if re.search(r"\bnever\b|\bnot\s+(?:come\s+|be\s+)?"
                 r"together\b|\bno\s+two\b", ql):
        return None
    letters = list(word)
    n = len(letters)
    if n < 2 or n > 20:
        return None
    vowels = [c for c in letters if c in _VOWELS]
    cons = [c for c in letters if c not in _VOWELS]
    total_plain, counts = _multiset_factorial(letters)

    # --- vowels / consonants in even or odd places ---
    m = re.search(r"(vowels?|consonants?)\s+(?:occupy|occupies|"
                  r"are\s+in|be\s+in|in)\s+(?:the\s+)?"
                  r"(even|odd)\s+(?:places|positions)", ql)
    if m:
        group = vowels if m.group(1).startswith("vowel") else cons
        other = cons if group is vowels else vowels
        if not group or not other:
            return None
        places = n // 2 if m.group(2) == "even" else (n + 1) // 2
        g = len(group)
        if g < places:
            # Ambiguous dress: "vowels occupy even places"
            # can mean every even place holds a vowel
            # (impossible here) or every vowel sits in an
            # even place (consonants take the leftover even
            # places).  The readings agree only when the
            # counts match (or the ask is impossible), so a
            # shortfall declines.
            return None
        if g > places:
            return _result(0, [
                f"{word} has {g} {m.group(1)} but only "
                f"{places} {m.group(2)} places, so the count "
                f"is 0."])
        gv, gc = _multiset_factorial(group)
        ov, oc = _multiset_factorial(other)
        ways_group = _comb(places, g) * gv
        total = ways_group * ov
        steps = [
            f"{word} has {n} letters and {places} "
            f"{m.group(2)} places.",
            f"Arrange the {g} {m.group(1)} in the "
            f"{m.group(2)} places: C({places}, {g}) × {gv} "
            f"= {ways_group}",
            f"Arrange the remaining {len(other)} letters in "
            f"the remaining places: {ov}",
            f"Multiply: {ways_group} × {ov} = {total}"]
        return _result(total, steps)

    # --- a block kept together ---
    together = re.search(
        r"(vowels?|consonants?)\s+(?:are\s+|always\s+|come\s+|"
        r"comes\s+)?(?:always\s+)?together", ql) or re.search(
        r"(vowels?|consonants?)\s+.*?\btogether\b", ql)
    if together or "together" in ql:
        if not together:
            return None
        block = vowels if together.group(1).startswith("vowel") \
            else cons
        rest = cons if block is vowels else vowels
        if not block or not rest:
            return None
        bv, _bc = _multiset_factorial(block)
        # Units: the rest letters (with their repeats) plus
        # ONE block unit.
        from collections import Counter
        rc = Counter(rest)
        denom = 1
        for c in rc.values():
            denom *= factorial(c)
        units = factorial(len(rest) + 1) // denom
        total = units * bv
        steps = [
            f"Treat the {len(block)} {together.group(1)} of "
            f"{word} as one block.",
            f"Arrange the {len(rest)} other letters + 1 block "
            f"({len(rest) + 1} units): {units}",
            f"Arrange the letters inside the block: {bv}",
            f"Multiply: {units} × {bv} = {total}"]
        return _result(total, steps)

    if "together" in ql or "never" in ql or "not" in ql \
            and "arrang" in ql:
        # An arrangement condition we do not model exactly
        # (e.g. 'vowels never together') declines.
        if re.search(r"\bnot\b|\bnever\b|\bno\s+two\b", ql):
            return None

    # --- plain arrangement ---
    steps = [f"{word} has {n} letters."]
    note = _repeat_note(counts, word)
    if note:
        steps.append(note)
        denom = 1
        for c in counts.values():
            denom *= factorial(c)
        steps.append(f"Arrangements = {n}! / {denom} "
                     f"= {_factorial_str(n)} / {denom} "
                     f"= {total_plain}")
    else:
        steps.append(f"All letters are different, so "
                     f"arrangements = {n}! = "
                     f"{_factorial_str(n)} = {total_plain}")
    return _result(total_plain, steps)


# ------------------------------------------------------------------
# C. digit numbers
# ------------------------------------------------------------------

def _digit_set(ql):
    """The stated digit set (list of ints) or None."""
    m = re.search(r"digits?\s+(?:from\s+)?(\d)\s*(?:to|–|-)\s*(\d)",
                  ql)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if 0 <= a <= b <= 9:
            return list(range(a, b + 1))
    m = re.search(r"digits?\s*(?:are|:|is)?\s*"
                  r"((?:\d\s*,\s*|\d\s+and\s+|\d\s*,\s*and\s+)*\d)"
                  r"(?=\s+(?:without|with|if|when|that|to\s+form|"
                  r"such|so|and\s+no|no\s+digit|repetition|"
                  r"digits?\s+(?:are|is)\s+not)|\s*$|[?.])", ql)
    if m:
        ds = [int(c) for c in re.findall(r"\d", m.group(1))]
        if 2 <= len(ds) <= 10 and len(set(ds)) == len(ds):
            return ds
    # Space-separated list closed by a repetition keyword.
    m = re.search(r"digits?\s+((?:\d\s+){1,9}\d)\s+(?:without|with)",
                  ql)
    if m:
        ds = [int(c) for c in re.findall(r"\d", m.group(1))]
        if len(set(ds)) == len(ds):
            return ds
    return None


def _digits(q, ql):
    if "digit" not in ql:
        return None
    if not re.search(r"numbers?\s+(?:can|could|are|be)\s|"
                     r"how\s+many\s+(?:\d+|one|two|three|four|"
                     r"five|six|seven|eight|nine|ten)[ -]?digit|"
                     r"numbers?\s+of\s", ql):
        return None
    m = re.search(r"(" + _NUM + r")[ -]?digit", ql) or \
        re.search(r"numbers?\s+of\s+(" + _NUM + r")\s+digits", ql)
    if not m:
        return None
    length = _n(m.group(1))
    if length is None or not (1 <= length <= 10):
        return None
    dset = _digit_set(ql)
    if dset is None:
        return None
    # Repetition must be stated; unstated declines.
    if re.search(r"without\s+repetition|no\s+digit\s+is\s+"
                 r"repeated|digits?\s+(?:are\s+)?not\s+repeated|"
                 r"no\s+repetition", ql):
        rep = False
    elif re.search(r"with\s+repetition|repetition\s+is\s+"
                   r"allowed|digits?\s+can\s+be\s+repeated|"
                   r"repetition\s+allowed|may\s+be\s+repeated",
                   ql):
        rep = True
    else:
        return None
    # Conditions we cannot count positionally decline.
    if re.search(r"divisible\s+by\s+(3|4|6|7|8|9|11|12|25)\b",
                 ql) or re.search(r"greater\s+than|less\s+than|"
                                   r"between\s+\d", ql):
        return None
    units_allowed = None
    cond_label = None
    if re.search(r"divisible\s+by\s+10\b", ql):
        units_allowed, cond_label = {0}, "divisible by 10"
    elif re.search(r"divisible\s+by\s+5\b", ql):
        units_allowed, cond_label = {0, 5}, "divisible by 5"
    elif re.search(r"\beven\b", ql) or \
            re.search(r"divisible\s+by\s+2\b", ql):
        units_allowed, cond_label = {0, 2, 4, 6, 8}, "even"
    elif re.search(r"\bodd\b", ql):
        units_allowed, cond_label = {1, 3, 5, 7, 9}, "odd"
    prefix = None
    m = re.search(r"(?:starts?|begins?|beginning)\s+with\s+"
                  r"(?:the\s+digits?\s+)?(\d+)", ql)
    if m:
        prefix = [int(c) for c in m.group(1)]
        if len(prefix) >= length:
            return None
        if any(d not in dset for d in prefix):
            return _result(0, [
                f"The number must begin with "
                f"{''.join(str(d) for d in prefix)}, but that "
                f"uses a digit outside the given set, so the "
                f"count is 0."])
        if not rep and len(set(prefix)) != len(prefix):
            return _result(0, [
                "The required beginning repeats a digit but "
                "repetition is not allowed, so the count "
                "is 0."])

    # Per-position allowed sets.
    allowed = []
    for pos in range(length):
        s = set(dset)
        if pos == 0 and length > 1:
            s.discard(0)
        if pos == 0 and length == 1:
            s.discard(0)
        if prefix and pos < len(prefix):
            s &= {prefix[pos]}
        if pos == length - 1 and units_allowed is not None:
            s &= units_allowed
        allowed.append(s)

    steps = [
        f"Digits available: {', '.join(str(d) for d in dset)}; "
        f"the number has {length} digits; repetition is "
        f"{'allowed' if rep else 'not allowed'}."]
    if prefix:
        steps.append(f"The number begins with "
                     f"{''.join(str(d) for d in prefix)}.")
    if cond_label:
        steps.append(f"The number is {cond_label}, so the "
                     f"units digit must be one of: "
                     + ", ".join(str(d) for d in
                                 sorted(units_allowed & set(dset))))

    if rep:
        total = 1
        counts = []
        for pos in range(length):
            c = len(allowed[pos])
            counts.append(c)
            total *= c
        steps.append("Choices per position: "
                     + " × ".join(str(c) for c in counts)
                     + f" = {total}")
        return _result(total, steps)

    # No repetition: exact subset DP over positions — the
    # count of completions depends on WHICH digits are used
    # (the leading-zero and units conditions), never just
    # on how many.
    index = {d: i for i, d in enumerate(dset)}
    masks = []
    for s in allowed:
        mask = 0
        for d in s:
            mask |= 1 << index[d]
        masks.append(mask)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def dp(pos, used):
        if pos == length:
            return 1
        avail = masks[pos] & ~used
        total = 0
        while avail:
            bit = avail & -avail
            total += dp(pos + 1, used | bit)
            avail ^= bit
        return total

    total = dp(0, 0)
    steps.append("Counting position by position (first "
                 "digit cannot be 0, no digit repeats): "
                 f"total = {total}")
    return _result(total, steps)


# ------------------------------------------------------------------
# D. geometric counting + row arrangements
# ------------------------------------------------------------------

_NAMED_POLYGONS = {"triangle": 3, "quadrilateral": 4,
                   "pentagon": 5, "hexagon": 6, "heptagon": 7,
                   "octagon": 8, "nonagon": 9, "decagon": 10,
                   "dodecagon": 12}


def _collinear(ql):
    # "no three of which are collinear" states the OPPOSITE
    # (no subtraction) — never read its number as a collinear
    # subset.
    if re.search(r"\bno\s+(?:three|two|points?)\b[^.]{0,40}?"
                 r"collinear", ql):
        return None
    m = re.search(r"(" + _NUM + r")\s+(?:of\s+(?:them|which)\s+)?"
                  r"(?:are\s+|being\s+)?collinear", ql)
    return _n(m.group(1)) if m else None


def _geometric(q, ql):
    # Chords through points on a circle.
    if "chord" in ql:
        m = re.search(r"(" + _NUM + r")\s+points?\s+on\s+a\s+"
                      r"circle", ql) or re.search(
                          r"joining\s+(" + _NUM + r")\s+points?",
                          ql)
        if m:
            n = _n(m.group(1))
            if n and n >= 2:
                v = _comb(n, 2)
                return _result(v, [
                    "Each chord joins 2 of the points, and "
                    "every pair gives one chord.",
                    f"Number of chords = C({n}, 2) = {v}"])
        return None
    # Handshakes.
    if "handshake" in ql or "shake hands" in ql or \
            "shakes hands" in ql:
        m = re.search(r"(" + _NUM + r")\s+(?:people|persons|"
                      r"students|men|women|children|players|"
                      r"friends)", ql)
        if m:
            n = _n(m.group(1))
            if n and n >= 2:
                v = _comb(n, 2)
                return _result(v, [
                    "Each handshake is between 2 people, and "
                    "every pair shakes hands once.",
                    f"Number of handshakes = C({n}, 2) = {v}"])
        return None
    # Diagonals of a polygon.
    if "diagonal" in ql:
        n = None
        m = re.search(r"(" + _NUM + r")[ -]?sided\s+polygon", ql) \
            or re.search(r"polygon\s+(?:with|of|having)\s+(" +
                         _NUM + r")\s+sides", ql) \
            or re.search(r"(" + _NUM + r")\s+sides", ql)
        if m:
            n = _n(m.group(1))
        if n is None:
            for name, sides in _NAMED_POLYGONS.items():
                if name in ql:
                    n = sides
                    break
        if n and n >= 3:
            v = _comb(n, 2) - n
            return _result(v, [
                f"Joining every pair of the {n} vertices "
                f"gives C({n}, 2) = {_comb(n, 2)} segments; "
                f"{n} of them are the sides, not diagonals.",
                f"Diagonals = {_comb(n, 2)} - {n} = {v}"])
        return None
    # Triangles / lines from points.
    if "point" in ql and ("triangle" in ql or "line" in ql):
        m = re.search(r"(" + _NUM + r")\s+points?", ql)
        if m:
            n = _n(m.group(1))
            col = _collinear(ql)
            if n and "triangle" in ql and n >= 3:
                v = _comb(n, 3)
                steps = [
                    f"Each triangle is fixed by 3 of the "
                    f"{n} points: C({n}, 3) = {v}"]
                if col:
                    sub = _comb(col, 3)
                    v -= sub
                    steps.append(
                        f"The {col} collinear points form no "
                        f"triangle: subtract C({col}, 3) "
                        f"= {sub}")
                    steps.append(f"Triangles = {v}")
                return _result(v, steps)
            if n and "line" in ql and n >= 2 and \
                    "triangle" not in ql:
                v = _comb(n, 2)
                steps = [
                    f"Each line joins 2 of the {n} points: "
                    f"C({n}, 2) = {v}"]
                if col and col >= 2:
                    sub = _comb(col, 2) - 1
                    v -= sub
                    steps.append(
                        f"The {col} collinear points give "
                        f"only 1 line, not C({col}, 2) = "
                        f"{_comb(col, 2)}: subtract {sub}")
                    steps.append(f"Lines = {v}")
                return _result(v, steps)
        return None
    return None


def _row_arrangement(q, ql):
    if not re.search(r"how\s+many\s+ways|kitne\s+tarike", ql):
        return None
    if not re.search(r"arrang|seated|in\s+a\s+row|in\s+a\s+line|"
                     r"in\s+a\s+queue", ql):
        return None
    m = re.search(r"(" + _NUM + r")\s+(?:different\s+|distinct\s+)?"
                  r"(people|persons|students|boys|girls|men|"
                  r"women|children|players|books|objects|"
                  r"things|items)\b", ql)
    if not m:
        return None
    n = _n(m.group(1))
    if n is None or not (1 <= n <= 30):
        return None
    v = factorial(n)
    return _result(v, [
        f"{n} distinct {m.group(2)} in a row: the first "
        f"place can be filled in {n} ways, the next in "
        f"{n - 1} ways, and so on.",
        f"Arrangements = {n}! = {_factorial_str(n)} = {v}"])


# ------------------------------------------------------------------
# entry point
# ------------------------------------------------------------------

def solve_pnc_word(question):
    """Wave 192 P&C counting word forms; None unless one of
    the strict schemas settles the question completely with
    an exact integer count."""
    try:
        q = str(question)
    except Exception:
        return None
    if not q.strip():
        return None
    ql = q.lower()
    # Counting intent is mandatory (coordinator repair at the
    # Wave 192 gate): a question that merely MENTIONS a
    # countable object is not a counting ask.  The first gate
    # run served 0 for a why-question about a quadrilateral's
    # diagonal (test_wave151_cont diagonal_why) and 3 for
    # "what is collinearity of three points" (topics bandc),
    # displacing the concept layer with bare counts.  So: a
    # concept / why / define dress vetoes outright, and one
    # of the counting markers must be present, before any
    # schema runs.
    if any(v in ql for v in (
            "what is", "what are", "why", "define",
            "definition of", "explain", "justify",
            "is it true", "shown below", "as shown",
            "kya hai", "kya hota", "kya hoti", "kya hote",
            "kyun", "ka matlab")):
        return None
    if not any(m in ql for m in (
            "how many", "number of", "in how many ways",
            "kitne", "kitni", "kitna", "tarike")):
        return None
    # Probability asks belong to statistics.py's schemas —
    # counting inside them is never served from here.
    if "probability" in ql or "chance of" in ql:
        return None
    # Explicit nPr / nCr / P(n, r) dress is statistics.py's.
    if re.search(r"\d+\s*[cp]\s*\d+|\b[cp]\s*\(\s*\d+\s*,", ql):
        return None
    # Multi-part batteries are multipart.py's territory.
    if re.search(r"\(\s*(?:i{1,3}|iv|v)\s*\)", ql):
        return None
    for path in (_geometric, _letters, _digits, _selections,
                 _row_arrangement):
        try:
            out = path(q, ql)
        except Exception:
            out = None
        if out is not None:
            return out
    return None
