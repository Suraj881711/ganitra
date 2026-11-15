"""Question router: normalises Hinglish, detects the topic, dispatches
to the right solver, and falls back to a generic SymPy solve/simplify.

Every result is a dict with at least: type, answer, steps.
"""
import logging
import math
import re
import threading

from .algebra import solve_algebra
from .answer_cache import get_cached, put_cached
from .applied import solve_applied
from .arithmetic import solve_arithmetic
from .calculus import solve_calculus
from .complex_numbers import solve_complex
from .distributions import solve_distributions
from .exponents_logs import solve_exponents_logs
from .geometry import solve_geometry
from .junior import solve_junior
from .linear_algebra import solve_linear_algebra
from .number_theory import solve_number_theory
from .plotting import solve_plot
from .sequences import solve_sequences
from .sets_basics import solve_sets
from .statistics import solve_statistics
from .transforms import solve_transforms
from .trigonometry import solve_trigonometry
from .units import solve_units
from .word_problems import solve_word_problem

# --------------------------------------------------------------------------
# Hinglish normalisation:  "5 aur 3 ko jodo" -> "5 + 3",
# "240 ka 15 pratishat" -> "15% of 240",  "2, 4, 6 ka ausat" -> mean, ...
# --------------------------------------------------------------------------
# ---------------------------------------------------------------------
# Wave 57: spelling normalisation — students type Hinglish with
# chaotic spellings (btaao, ktna, khetrafal, byaaj) and English with
# typos / OCR noise (rectangel, circumfrence, 24O, circ1e, rnaximum).
# Rather than adding every spelling as its own pattern, fold each
# token back to the canonical word BEFORE pattern matching:
#   1. a variant map for the commonest misspellings,
#   2. phonetic folding rules (doubled letters, long vowels) that
#      only fire when the folded form is a known canonical word,
#   3. consonant-skeleton matching against the canonical Hinglish
#      maths wordlist for dropped-vowel forms (ktna -> kitna),
#      gated on the question actually looking Hinglish, and never
#      applied to ordinary English words.
# Latin tokens only; Devanagari text is untouched apart from its
# digits (०१२३ -> 0123), which every solver expects in ASCII.
_DEV_DIGIT_TABLE = str.maketrans("०१२३४५६७८९", "0123456789")

_HINGLISH_VARIANTS = {
    "chaahiye": "chahiye", "chaiye": "chahiye",
    "chahiyee": "chahiye", "bataao": "batao", "btaao": "batao",
    "smjhao": "samjhao", "kitnaa": "kitna", "kitana": "kitna",
    "parcent": "pratishat", "khetrafal": "kshetrafal",
    "lambaai": "lambai", "chauraai": "chaudai",
    "unchaai": "unchai", "warg": "varg", "parimaap": "parimap",
    "vrit": "vritt", "trijiya": "trijya", "rupay": "rupaye",
    "byaaj": "byaj", "sankhyaa": "sankhya",
    "ausaat": "ausat", "sambhaavna": "sambhavna",
    "prayikta": "sambhavna", "cheet": "chit", "tribuj": "tribhuj",
    "adhar": "aadhar", "samikarn": "samikaran", "pahle": "pehle",
    "yogg": "yog", "nikaalo": "nikalo",
    "duri": "doori", "paasa": "pasa", "ghantay": "ghante",
    "jodd": "jod", "ghaata": "ghata", "gunna": "guna",
    "bhag": "bhaag", "tren": "train", "railgadi": "train",
    "ayat": "aayat", "sadharann": "sadharan",
}

_HINGLISH_CANON = frozenset(_HINGLISH_VARIANTS.values()) | frozenset(
    "batao kitna kitne kitni hai hoga hogi kya samjha samjhao "
    "chahiye pratishat kshetrafal parimap paridhi lambai chaudai "
    "unchai aadhar tribhuj chaturbhuj varg ghan ghanaab vritt "
    "trijya byaj dar saal rupaye paas sankhya ausat "
    "madhyika sambhavna "
    "sikka sikke pasa chit puchh samikaran mool yog pad padon "
    "pehle ghante ghanta doori train speed chaal gati samay karo "
    "wala wali milega mile mila milta anupat banto number gaya jati tay uchale "
    "feko sama visham sadharan".split())

# Ambiguous short forms: folded only when the question already
# looks Hinglish ("sal" is also a name, "mul" a name fragment).
_HINGLISH_VARIANTS_GATED = {"sal": "saal", "mul": "mool"}

# Real Hinglish words whose consonant skeleton collides with a
# maths word — never skeleton-folded ("paise" = money must not
# become "pasa" = die; "paas" is protected via the canon set).
_HINGLISH_NO_FOLD = frozenset({"paisa", "paise"})

_EN_TYPOS = {
    "rectangel": "rectangle", "rectnagle": "rectangle",
    "circumfrence": "circumference",
    "circumfernce": "circumference", "cirle": "circle",
    "mena": "mean", "midean": "median", "precent": "percent",
    "pecent": "percent", "intrest": "interest",
    "lenght": "length", "hieght": "height", "redius": "radius",
    "squre": "square", "triangel": "triangle",
    "traingle": "triangle", "diametre": "diameter",
    "volum": "volume", "eqaution": "equation",
    "equaton": "equation", "slove": "solve", "theorm": "theorem",
    "pythagorus": "pythagoras", "probablity": "probability",
    "probibility": "probability", "probabilty": "probability",
    "parimeter": "perimeter", "formulla": "formula",
    "avrage": "average", "substraction": "subtraction",
    "addtion": "addition", "quadretic": "quadratic",
}

# Words an rn->m or 1->l OCR repair may land on.
_EN_VOCAB = frozenset(
    "maximum minimum metre metres meter meters circle rectangle "
    "length breadth solve value radius simple area volume triangle "
    "square algebra calculate total parallel equal angle single "
    "double whole table sample example".split())

# Ordinary English words are never skeleton-folded into Hinglish.
_EN_NO_FOLD = frozenset(
    "the and for with find area what when then than that this from "
    "into have has each side mean mode root sum all two one six ten "
    "per get got set put use way day say see try its is in on of to "
    "do go no so up us we he be by my volume radius diameter square "
    "triangle rectangle length breadth height base perimeter "
    "circumference surface equation solve simplify factorise "
    "factorize expand evaluate value angle degree degrees median "
    "range data numbers number digits digit prime composite factor "
    "factors multiple product quotient remainder fraction decimal "
    "percent percentage ratio proportion interest simple compound "
    "principal rate time speed distance train travels cover covers "
    "hours minutes seconds days years rupees price cost profit loss "
    "discount marked selling total first second third term terms "
    "series sequence probability coin coins dice die head heads "
    "tail tails card cards ball balls bag box red blue green "
    "marble marbles how why who let given show prove draw plot "
    "graph line point points form take takes made make makes long "
    "much many more most less least just only also very can could "
    "will would shall should may might must average".split())

_HINGLISH_MARKERS = _HINGLISH_CANON | frozenset(_HINGLISH_VARIANTS) \
    | frozenset(
        "ka ki ke hai hain aur mein me se ko ek do teen kya par bhi "
        "ye woh bata nikal hua mile mila wala wali karo karke lagta "
        "lagega jata gaya gayi raha rahi tha thi apna apni iska iski "
        "uska uski jiska jiski kitna kitne kitni chahiye batao "
        "nikalo sankhyaon".split())


def _skeleton(word):
    """Consonant skeleton: vowels (and y) dropped — ktna and kitna
    share 'ktn'."""
    return re.sub(r"[aeiouy]+", "", word)


_SKEL_TARGETS = {}
for _w in _HINGLISH_CANON:
    if len(_w) >= 4:
        _SKEL_TARGETS.setdefault(_skeleton(_w), []).append(_w)
_SKEL_TARGETS = {k: v[0] for k, v in _SKEL_TARGETS.items()
                 if len(v) == 1}
# Merge-3: one-consonant skeletons ("g" -> gaya, "t" -> aayat)
# are dropped — they collide with ordinary English words (age,
# ago, eat, tea), and once two such tokens appear the Hinglish
# gate opens and rewrites clean English questions (it broke
# Wave 56's ages schemas: "age" became "gaya"). A dropped-vowel
# form worth folding always keeps >= 2 consonants.
_SKEL_TARGETS = {k: v for k, v in _SKEL_TARGETS.items()
                 if len(k) >= 2}
# Ambiguous skeletons whose maths-default reading is clear.
_SKEL_TARGETS.update({"ghnt": "ghante", "ktn": "kitna",
                     "skk": "sikka", "dr": "doori",
                     "ps": "pasa"})

_JOIN_VOCAB = frozenset(
    "rectangle circumference probability triangle square circle "
    "perimeter interest equation volume diameter simple area"
    .split())
_JOIN_LEFT_STOP = frozenset(
    "right acute obtuse straight reflex".split())

_NOSPACE_WORDS = sorted(
    "find the area of square circle triangle rectangle with side "
    "radius diameter perimeter circumference volume mean median "
    "mode what is solve and cm mm km in to an a".split(),
    key=len, reverse=True)


def _fold_word(w, hinglish_gate):
    """Fold one lowercase Latin token to its canonical spelling."""
    for _ in range(3):
        if w in _HINGLISH_VARIANTS:
            w = _HINGLISH_VARIANTS[w]
            continue
        if hinglish_gate and w in _HINGLISH_VARIANTS_GATED:
            w = _HINGLISH_VARIANTS_GATED[w]
            continue
        if w in _HINGLISH_CANON:
            break
        if w in _EN_TYPOS:
            w = _EN_TYPOS[w]
            break
        # OCR: rn -> m ("rnaximum"), digit 1 -> letter l ("circ1e").
        if w.startswith("rn") and "m" + w[2:] in _EN_VOCAB:
            w = "m" + w[2:]
            break
        if w.count("1") == 1 and len(w) >= 4 and \
                re.fullmatch(r"[a-z1]+", w) and \
                w.replace("1", "l") in _EN_VOCAB:
            w = w.replace("1", "l")
            break
        # Doubled letters collapsed ("kitnaaa", "joddd", "byajj").
        collapsed = re.sub(r"([a-z])\1+", r"\1", w)
        if collapsed != w and (collapsed in _HINGLISH_CANON
                               or collapsed in _HINGLISH_VARIANTS):
            w = collapsed
            continue
        # Long vowels folded ("byaaj", "chaahiye", "nikaalo").
        folded = w.replace("aa", "a").replace("ee", "i") \
            .replace("oo", "u")
        if folded != w and (folded in _HINGLISH_CANON
                            or folded in _HINGLISH_VARIANTS):
            w = folded
            continue
        break
    # Dropped-vowel forms: consonant-skeleton match, Hinglish only.
    if hinglish_gate and len(w) >= 3 and w not in _HINGLISH_CANON \
            and w not in _HINGLISH_NO_FOLD \
            and w not in _EN_NO_FOLD and w.isalpha():
        sk = _skeleton(w)
        target = _SKEL_TARGETS.get(sk)
        if target is None and sk[:1] in ("b", "v"):
            # b/v are interchangeable in Roman Hindi (britt =
            # vritt, warg = varg).
            target = _SKEL_TARGETS.get(
                ("v" if sk[0] == "b" else "b") + sk[1:])
        if target is None and sk.startswith("ch"):
            # क्षेत्र is typed both kshetra and chetra.
            target = _SKEL_TARGETS.get("ksh" + sk[2:])
        if target is None and w[0] in "aeiou":
            # Roman Hindi often drops the nasal of ऊँचाई-type
            # words: uchai for unchai.
            target = _SKEL_TARGETS.get(_skeleton("n" + w))
        if target is not None:
            w = target
    return w


def _nospace_repair(text):
    """'findtheareaofasquarewithside9cm' -> spaced words, by greedy
    longest-match over a small maths vocabulary. Returns None when
    the string does not tokenise almost completely."""
    s = text.strip()
    if " " in s or len(s) < 12 or not re.fullmatch(r"[a-z0-9%,.]+", s):
        return None
    out, i = [], 0
    while i < len(s):
        m = re.match(r"\d[\d,]*(?:\.\d+)?%?", s[i:])
        if m:
            out.append(m.group(0))
            i += len(m.group(0))
            continue
        for word in _NOSPACE_WORDS:
            if s.startswith(word, i):
                out.append(word)
                i += len(word)
                break
        else:
            return None
    return " ".join(out)


def normalize_spelling(question: str) -> str:
    """Wave 57: fold student-typing noise (Hinglish spelling chaos,
    English typos, OCR-style noise) back to canonical words before
    any pattern matching. Conservative by design: a token changes
    only when the folded form is a known word, so clean questions
    pass through byte-identical."""
    try:
        return _normalize_spelling(question)
    except Exception:
        return question


def _normalize_spelling(question: str) -> str:
    text = str(question).translate(_DEV_DIGIT_TABLE)
    repaired = _nospace_repair(text.lower())
    if repaired is not None:
        text = repaired
    # OCR digit/O swaps inside number tokens ("24O", "1OOO", "6O").
    def _o_swap(m):
        tok = m.group(0)
        if any(c.isdigit() for c in tok) and ("O" in tok
                                              or "o" in tok):
            return tok.replace("O", "0").replace("o", "0")
        return tok
    text = re.sub(r"(?<![A-Za-z0-9])[0-9Oo]+(?![A-Za-z0-9])",
                  _o_swap, text)
    low_tokens = re.findall(r"[a-z]+", text.lower())
    hinglish_gate = any("ऀ" <= c <= "ॿ" for c in text) or \
        sum(1 for t in low_tokens if t in _HINGLISH_MARKERS) >= 2
    if not hinglish_gate:
        # Short Hinglish asks may carry only one marker word
        # ("in snkhya ka osat btao: ...") — open the gate when
        # two or more tokens already skeleton-match the maths
        # wordlist.
        hits = sum(1 for t in low_tokens
                   if len(t) >= 3 and t not in _EN_NO_FOLD
                   and t not in _HINGLISH_NO_FOLD
                   and t not in _HINGLISH_CANON
                   and _skeleton(t) in _SKEL_TARGETS)
        hinglish_gate = hits >= 2

    def _sub(m):
        tok = m.group(0)
        low = tok.lower()
        if len(low) < 2:
            return tok
        # OCR digit 1 inside a word ("circ1e", "1ength", "so1ve",
        # "rad1us"): the 1 stands for l OR i — fold only when one
        # of the results is a known English word.
        if "1" in low:
            if low.count("1") == 1 and len(low) >= 4:
                for cand in (low.replace("1", "l"),
                             low.replace("1", "i")):
                    if cand in _EN_VOCAB:
                        return cand
            return tok
        if not low.isalpha():
            return tok
        folded = _fold_word(low, hinglish_gate)
        return folded if folded != low else tok
    text = re.sub(r"[A-Za-z]*1[A-Za-z]+|[A-Za-z]+", _sub, text)
    # "6 percent" -> "6%": the solvers' percent patterns are
    # written for the % sign.
    text = re.sub(r"(\d+(?:\.\d+)?)\s+percent\b", r"\1%", text)
    # "breath" is a typo for breadth only next to a measurement.
    text = re.sub(r"\bbreath\s+(is\s+)?(\d)",
                  lambda m: "breadth " + (m.group(1) or "")
                  + m.group(2), text)
    # Broken words: "rect angle", "circum ference", "sim ple".
    parts = text.split(" ")
    if len(parts) > 1:
        merged, i, changed = [], 0, False
        while i < len(parts):
            if i + 1 < len(parts):
                a, b = parts[i].lower(), parts[i + 1].lower()
                if a + b in _JOIN_VOCAB and a not in _JOIN_LEFT_STOP:
                    merged.append(a + b)
                    i += 2
                    changed = True
                    continue
            merged.append(parts[i])
            i += 1
        if changed:
            text = " ".join(merged)
    # Typed superscripts in equations: "x2 - 5x + 6 = 0" -> x^2.
    if "=" in text:
        text = re.sub(r"(?<![A-Za-z0-9])([a-z])([23])(?![0-9])",
                      r"\1^\2", text)
    return text


def normalize_hinglish(question: str) -> str:
    q = " " + question.strip() + " "
    ql = q.lower()

    # Percentage: "240 ka 15 pratishat (kitna hoga)" -> "15% of 240"
    # (Wave 57: the English word "percent" in the same slot too.
    # Guarded: with "discount" nearby the ka-phrase is a price
    # story, not a plain percent-of.)
    m = re.search(r"(\d+(?:\.\d+)?)\s+ka\s+(\d+(?:\.\d+)?)\s+"
                  r"(?:pratishat|percent)", ql)
    if m and "discount" not in ql:
        return f"{m.group(2)}% of {m.group(1)}"

    # Wave 57: Devanagari percent — "240 का 15 प्रतिशत कितना होगा?"
    m = re.search(r"(\d+(?:\.\d+)?)\s*का\s*(\d+(?:\.\d+)?)\s*"
                  r"प्रतिशत", ql)
    if m:
        return f"{m.group(2)}% of {m.group(1)}"

    # Wave 57: Devanagari roots — "144 का वर्गमूल" / "27 का
    # घनमूल" (these returned letter-soup before; the word
    # forms "square root of N" do not parse in the solver,
    # the function forms do).
    m = re.search(r"(\d+(?:\.\d+)?)\s*का\s*वर्गमूल", ql)
    if m:
        return f"sqrt({m.group(1)})"
    m = re.search(r"(\d+(?:\.\d+)?)\s*का\s*घनमूल", ql)
    if m:
        return f"cbrt({m.group(1)})"

    # Wave 57: same ask with the % sign — "240 ka 15% kitna hoga".
    # Guarded: with byaj/saal nearby it is an interest ask, not a
    # plain percent-of; with "discount" it is a price story.
    m = re.search(r"(\d+(?:\.\d+)?)\s+ka\s+(\d+(?:\.\d+)?)\s*%", ql)
    if m and "byaj" not in ql and "saal" not in ql \
            and "dar se" not in ql and "discount" not in ql:
        return f"{m.group(2)}% of {m.group(1)}"

    # Average: "2, 4, 6 ka ausat" -> "mean of 2, 4, 6"
    m = re.search(r"([\d][\d\s,\.]*?)\s+ka\s+ausat", ql)
    if m:
        return f"mean of {m.group(1).strip()}"

    # Wave 57: the list can also come AFTER "ausat batao:" —
    # "in sankhyaon ka ausat batao: 3, 6, 9, 12". A comma is
    # required, so "ausat 12 hai, yog kitna?" (mean GIVEN) is
    # never mistaken for a list.
    m = re.search(r"ausat\s*(?:batao|nikalo|bata\s*do|kya\s+hoga)?"
                  r"\s*[:\-]?\s*([\d][\d\s,\.]*)", ql)
    if m and "," in m.group(1) and len(re.findall(r"\d", m.group(1))) >= 2:
        return f"mean of {m.group(1).strip()}"

    # Multiply: "4 guna 5", "4 aur 5 ka guna", "4 ko 5 se guna"
    m = re.search(r"(\d+(?:\.\d+)?)\s*guna\s*(\d+(?:\.\d+)?)", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+guna",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)\s+se\s+guna",
                  ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"

    # Divide: "20 ko 4 se bhaag (do)", "20 bhaag 4",
    # "20 aur 4 ka bhaag" (noun form — same gap as "ka jod", below)
    m = re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)\s+se\s+bhaag",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+bhaag\s+(\d+(?:\.\d+)?)", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+ka\s+bhaag\s+(\d+(?:\.\d+)?)",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+bhaag\b",
                  ql)
    if m:
        return f"{m.group(1)} / {m.group(2)}"

    # Subtract: "20 mein se 7 ghatana/ghatavo",
    # "27 aur 15 ka ghata/ghatav" (noun form — same gap as "ka jod")
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+mein?\s+se\s+(\d+(?:\.\d+)?)\s+ghatana", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+"
                     r"(?:ghata|ghatav|ghataav)\b", ql)
    if m:
        return f"{m.group(1)} - {m.group(2)}"

    # Add: "5 aur 3 ko jodo", "5 mein 3 jodo", "5 jodo 3",
    # "15 aur 27 ka jod (kitna hoga/hai)", "15 aur 27 (ko) jodkar /
    # jod ke batao", "15 aur 27 jodo". The noun form "ka jod" was
    # missing (live bug, 12 Nov 2026): the question fell through to
    # the SymPy expression parser, which read "jod" as the variables
    # j*o*d next to 15*27 and answered "405*d*j*o" instead of 42.
    m = re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ko\s+jodo",
                  ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+mein\s+(\d+(?:\.\d+)?)\s+jodo", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+jodo\s+(\d+(?:\.\d+)?)", ql) \
        or re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+ka\s+jod\b",
                     ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+"
                  r"(?:ko\s+)?jodkar\b", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+"
                  r"(?:ko\s+)?jod\s+ke\b", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)\s+jodo\b", ql)
    if m:
        return f"{m.group(1)} + {m.group(2)}"

    # Wave 30: two numbers from their sum & difference
    # ("do sankhyaon ka jod 40 hai aur unka antar 8 hai") and
    # "number ko N se guna karne par M milta hai" (times-table
    # phrasing of "N times a number is M"), plus the Roman-Hindi
    # train distance ("72 km/h ki speed se ... 3 ghante mein").
    m = re.search(r"jod\s+(\d+(?:\.\d+)?)\s+hai\s+aur\s+"
                  r"(?:unka\s+|unaka\s+)?antar\s+(\d+(?:\.\d+)?)"
                  r"\s+hai", ql)
    if m:
        return (f"sum is {m.group(1)} and difference is "
                f"{m.group(2)}")
    m = re.search(r"(?:ek\s+)?number\s+ko\s+(\d+(?:\.\d+)?)\s+"
                  r"se\s+guna\s+karne\s+par\s+(\d+(?:\.\d+)?)\s+"
                  r"milta\s+hai", ql)
    if m:
        return f"{m.group(1)} times a number is {m.group(2)}"
    m = re.search(r"(\d+(?:\.\d+)?)\s*km/h[^0-9]{0,80}?"
                  r"(\d+(?:\.\d+)?)\s*ghante", ql)
    if m:
        return f"{m.group(1)} km/h for {m.group(2)} hours"

    # Wave 57: Roman-Hindi time ask — "train 80 km/h ki speed
    # se 240 km kitne ghante me jayegi?" (distance rule above
    # cannot match: the hours are not digit-adjacent here).
    m = re.search(r"(\d+(?:\.\d+)?)\s*km/h[^0-9]{0,60}?"
                  r"(\d+(?:\.\d+)?)\s*km\b[^0-9]{0,30}?ghante",
                  ql)
    if m:
        return (f"how long does a train take to travel "
                f"{m.group(2)} km at {m.group(1)} km/h")

    # Wave 57: Roman-Hindi word problems -> the canonical English
    # forms the solvers already accept. These run on the spelling-
    # folded text, so only canonical Hinglish words are matched
    # (btaao/ktna/khetrafal never reach here — they are folded by
    # normalize_spelling first).
    # Speed from distance + time: "ek train 360 km (ki doori)
    # 4 ghante me tay karti hai, speed/chaal kitni hai?"
    if "km/h" not in ql and ("speed" in ql or "chaal" in ql
                             or "gati" in ql):
        m = re.search(r"(\d+(?:\.\d+)?)\s*km\b[^0-9]{0,24}?"
                      r"(\d+(?:\.\d+)?)\s*ghante", ql)
        if m:
            return (f"a train travels {m.group(1)} km in "
                    f"{m.group(2)} hours, find its speed")
    # Time from distance + speed: "train ko 360 km jana hai,
    # speed 60 km/h hai, kitna time lagega?"
    if "time" in ql or "samay" in ql:
        m = re.search(r"(\d+(?:\.\d+)?)\s*km\s+jana\s+hai"
                      r"[^0-9]{0,40}?(\d+(?:\.\d+)?)\s*km/h", ql)
        if m:
            return (f"how long does a train take to travel "
                    f"{m.group(1)} km at {m.group(2)} km/h")
    # Rectangle area: lambai/chaudai or length/breadth forms.
    m = re.search(r"aayat[^0-9]{0,40}?lambai\s+(?:hai\s+)?"
                  r"(\d+(?:\.\d+)?)[^0-9]{0,20}?chaudai\s+"
                  r"(?:hai\s+)?(\d+(?:\.\d+)?)", ql) or \
        re.search(r"aayat[^0-9]{0,40}?length\s+(\d+(?:\.\d+)?)"
                  r"[^0-9]{0,20}?breadth\s+(\d+(?:\.\d+)?)", ql)
    if m:
        return (f"area of a rectangle with length {m.group(1)} "
                f"and breadth {m.group(2)}")
    # Triangle area: "tribhuj ... aadhar B ... unchai H".
    m = re.search(r"tribhuj[^0-9]{0,50}?aadhar\s+(?:hai\s+)?"
                  r"(\d+(?:\.\d+)?)[^0-9]{0,20}?unchai\s+"
                  r"(?:hai\s+)?(\d+(?:\.\d+)?)", ql)
    if m:
        return (f"area of a triangle with base {m.group(1)} "
                f"and height {m.group(2)}")
    # Square perimeter / area with "side S".
    m = re.search(r"varg\s+ka\s+parimap[^0-9]{0,30}?side\s+"
                  r"(\d+(?:\.\d+)?)", ql)
    if m:
        return f"perimeter of a square with side {m.group(1)}"
    m = re.search(r"varg\s+ka\s+(?:area|kshetrafal)[^0-9]{0,30}?"
                  r"side\s+(\d+(?:\.\d+)?)", ql)
    if m:
        return f"area of a square with side {m.group(1)}"
    # Circle area / circumference with trijya or radius.
    m = re.search(r"(?:vritt|circle)[^0-9]{0,50}?(?:kshetrafal|"
                  r"area)[^0-9]{0,50}?(?:trijya|radius)\s+"
                  r"(\d+(?:\.\d+)?)", ql)
    if m:
        return f"area of a circle with radius {m.group(1)}"
    m = re.search(r"(?:vritt|circle)[^0-9]{0,50}?paridhi"
                  r"[^0-9]{0,50}?(?:trijya|radius)\s+"
                  r"(\d+(?:\.\d+)?)", ql)
    if m:
        return f"circumference of a circle with radius {m.group(1)}"
    # Cuboid volume: "ghanaab ... lambai L chaudai B unchai H".
    m = re.search(r"ghanaab[^0-9]{0,60}?lambai\s+(\d+(?:\.\d+)?)"
                  r"[^0-9]{0,20}?chaudai\s+(\d+(?:\.\d+)?)"
                  r"[^0-9]{0,20}?unchai\s+(\d+(?:\.\d+)?)", ql)
    if m:
        return (f"volume of a cuboid with length {m.group(1)} "
                f"breadth {m.group(2)} and height {m.group(3)}")
    # Simple interest: "P rupaye ka R percent/% ... T saal ... byaj".
    m = re.search(r"(\d+(?:\.\d+)?)\s+rupaye[^0-9]{0,30}?"
                  r"(\d+(?:\.\d+)?)\s*(?:percent|pratishat)"
                  r"[^0-9]{0,40}?(\d+(?:\.\d+)?)\s+saal", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+rupaye[^0-9]{0,20}?"
                  r"(\d+(?:\.\d+)?)\s*%[^0-9]{0,50}?"
                  r"(\d+(?:\.\d+)?)\s+saal", ql)
    if m and "byaj" in ql:
        return (f"simple interest on {m.group(1)} at "
                f"{m.group(2)}% for {m.group(3)} years")
    # Marks percent: "500 me se 350 number mile, percent kitna?"
    m = re.search(r"(\d+(?:\.\d+)?)\s+me\s+se\s+(\d+(?:\.\d+)?)"
                  r"\s+(?:number|marks?)\s+mile", ql)
    if m:
        return (f"what percentage is {m.group(2)} out of "
                f"{m.group(1)}")
    # Ratio share: "1000 rupaye ko 2:3 ke anupat me banto".
    m = re.search(r"(\d+(?:\.\d+)?)\s+rupaye\s+ko\s+"
                  r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s+ke\s+"
                  r"anupat", ql)
    if m:
        return (f"divide {m.group(1)} in the ratio "
                f"{m.group(2)}:{m.group(3)} how much does the "
                f"first person get")
    # Discount: "2000 rupaye wali cheez par 10% discount".
    m = re.search(r"(\d+(?:\.\d+)?)\s+rupaye\s+wali[^0-9]{0,30}?"
                  r"(\d+(?:\.\d+)?)\s*%\s+discount", ql)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%")

    # "ka maan (nikalo)" = "the value of": strip it and route normally.
    t = re.sub(r"\s+ka\s+maan\b.*$", "", ql).strip()
    t = re.sub(r"\s+(kitna\s+hoga|batao|nikalo|karo|kar\s+do)\s*$", "", t)
    return t.strip()


# --------------------------------------------------------------------------
# Wave 20 (Suraj, 12 Nov 2026): science-scope guard. Ganitra is
# MATHS-ONLY, but a Physics question ("refractive index ... speed
# of light ... 2 x 10^8 m/s") used to be force-fit into a junior
# maths intent / salvage fragment and answered with nonsense.
# These are SCIENCE-SPECIFIC signals — bare "speed" is NOT one
# (speed-distance-time sums are real maths), and neither is bare
# "current" or "element" (maths uses both legitimately). The
# router uses this to refuse the weak junior intent for such
# questions, and fallback.py uses it to answer honestly instead
# of salvaging a fake "maths part".
# --------------------------------------------------------------------------
_SCIENCE_RE = re.compile(
    r"(refractive|speed\s+of\s+light|ray\s+of\s+light|light\s+ray|"
    r"photosynthesis|velocity|acceleration|\bforce\b|newtons?\b|"
    r"voltage|ampere|electric\s+current|resistance|ohms?\b|"
    r"chemical|atom|atomic|molecule|electron|proton|neutron|"
    r"friction|momentum|gravity|gravitational|wavelength|"
    r"circuit|capacitor|kinetic\s+energy|potential\s+energy)",
    re.I)


def has_science_signal(question: str) -> bool:
    return bool(_SCIENCE_RE.search(str(question or "")))


# --------------------------------------------------------------------------
# Intent detection
# --------------------------------------------------------------------------
def route_intent(question: str) -> str:
    q = question.lower()

    # Probability distributions (before statistics: "binomial" with
    # n=/p= belongs here, plain probability stories stay statistics).
    if "poisson" in q or "normal distribution" in q \
            or "z-score" in q or "z score" in q:
        return "distributions"
    if "binomial" in q and re.search(r"\bn\s*=", q) and \
            re.search(r"\bp\s*=", q):
        return "distributions"
    if re.search(r"\bpercentile\b", q) and re.search(
            r"(mean|sd|sigma|standard deviation)", q):
        return "distributions"

    # Transforms & series (before calculus/algebra: "series" and
    # "partial fractions" would otherwise fall through).
    if "laplace" in q or "partial fraction" in q or \
            re.search(r"\b(taylor|maclaurin)\b", q) or \
            re.search(r"series\s+expansion", q) or \
            re.search(r"expansion\s+of", q):
        return "transforms"

    if re.search(r"\b(plot|graph|draw)\b", q) and not re.search(
            r"\bintegrat", q):
        return "plot"

    # Unit conversion: explicit "convert" is handled in solve_question via
    # solve_units() first; here match "<number> <unit> to/in <unit>".
    if re.search(
            r"\d\s*(km|cm|mm|miles?|kg|grams?|litres?|liters?|hours?|"
            r"minutes?|seconds?|inches|feet|yards?|pounds?|ounces?|"
            r"hectares?|acres?)\b.{0,12}?\b(to|in)\b", q):
        return "units"

    # Calculus. Word boundaries so words like "derivative" are not
    # mangled mid-word by solvers ("deriv" must not eat "derivative").
    # Also catch "integrate ... and show the graph" style requests
    # and d2y/dx2-style second-order ODE notation.
    if re.search(
            r"(dy/dx|d2y|y\'|differential|dsolve|derivative|"
            r"differentiate|integration|integral|integrate|"
            r"\blimit\b|\blim\b|d/d|partial"
            r"|continu\w*|differentiab\w*)", q) or re.search(
            r"\bintegrat\w*\b.+\b(graph|shade|plot)\b", q) or \
            re.search(r"rate\s+of\s+change", q) or re.search(
            r"slope\s+of\s+(the\s+)?(tangent|normal)\b", q) or \
            re.search(
            r"equations?\s+of\s+(the\s+)?(tangent|normal)\b", q) or \
            re.search(
            r"(maximum|minimum)\s+value\s+of\s+(the\s+)?"
            r"(function\s+)?f\s*\(\s*x\s*\)", q):
        return "calculus"

    # Linear algebra
    if "[[" in q or re.search(
            r"\b(matrix|determinant|eigen|inverse|transpose|rank|trace)\b",
            q):
        return "linear_algebra"

    # Sets
    if "{" in q and re.search(r"\b(union|intersection|difference)\b", q):
        return "sets"

    # Trigonometry (incl. inverse functions like arcsin)
    if re.search(
            r"(arc\s*(sin|cos|tan)|\b(sin|cos|tan)\s*\^\s*\(?\s*-1|"
            r"inverse\s+(sin|cos|tan)|\ba(sin|cos|tan)\b)", q) or re.search(
            r"\b(sin|cos|tan|cot|sec|csc|cosec|sine|cosine|tangent|"
            r"trigonometr\w*)\b", q) or "trig" in q or re.search(
            r"angle\s+of\s+(elevation|depression)|\bladder\b", q):
        return "trigonometry"

    # Counting notation: C(5,2), P(5,2), 5C2, 5P2
    if re.search(r"\b[CP]\s*\(\s*\d+\s*,\s*\d+\s*\)", question) or \
            re.search(r"\d+\s*[CP]\s*\d+", question):
        return "statistics"

    # Wave 58: event-probability notation — "P(A) = 0.3 ...
    # find P(A or B)". Two or more capital-event P() mentions
    # mark a probability question even when the word
    # "probability" never appears; without this the algebra
    # intent claimed them and the system solver served
    # letter-equation garbage. (Polynomial P(x) is lowercase
    # and never matches.)
    if len(re.findall(r"P\(\s*[A-Z]\b", question)) >= 2:
        return "statistics"

    # Statistics & probability ("mode" as a standalone word only, so
    # "model" etc. are not hijacked; dice handled by word boundary)
    # Wave 33: Hindi / Hinglish statistics tokens — प्रायिकता /
    # संभावना (probability), सिक्का (coin), पासा (die), गेंद
    # (ball), पत्ते (cards), माध्य / माध्यक / बहुलक / औसत
    # (mean / median / mode / average) and their Roman forms.
    # Without them every Hindi statistics question fell to the
    # arithmetic simplifier and came back as letter-soup.
    if re.search(
            r"(probabilit|permutation|combination|factorial|\bmean\b|"
            r"median|\bmode\b|standard deviation|variance|\bdice\b|"
            r"\bdie\b|coin|choose|arrange|"
            r"प्रायिकता|संभावना|सिक्क|पासा|पासे|गेंद|पत्त|"
            r"माध्य|माध्यक|बहुलक|औसत|"
            r"sambhavna|sambhaavana|\bsikka\b|\bsikke\b|"
            r"\bpasa\b|\bpaase\b)", q):
        return "statistics"

    # Geometry
    if re.search(
            r"(\barea\b|perimeter|volume|circumference|surface area|"
            r"distance between|midpoint|slope|hypotenuse|"
            r"equation of|triangle.{0,50}angle|section\s+formula|"
            r"divides\s+the\s+line|coordinates\s+of\s+the\s+point|"
            r"diagonal|pythagor|समकोण|कर्ण|"
            r"क्षेत्रफल|परिमाप|परिधि|त्रिज्या|आयत|वर्ग\s+क|"
            r"त्रिभुज|वृत्त|भुजा|लंबाई|चौड़ाई|ऊँचाई|आधार)",
            q):
        return "geometry"

    # Sequences & series
    # Wave 42: Hindi / Hinglish sequence tokens — समांतर
    # श्रेढ़ी (AP), Devanagari/Roman ordinals with पद/pad
    # ("12वां पद", "12va pad"), "पदों का योग / padon ka yog"
    # (sum) and "अगला पद / agla pad / next term". Without
    # them every Hindi AP ask fell through to the arithmetic
    # simplifier and came back as a concept/guide fallback.
    if re.search(
            r"(\bap\b|\bgp\b|arithmetic (progression|series|sequence)|"
            r"geometric (progression|series|sequence)|nth term|"
            r"next\s+term|sum of (the )?first|sum of .* series|"
            r"समांतर|sama?ntar|shreni|shredi|shrenee|"
            r"अगला\s*पद|agla\s+pad|पदों\s*का\s*योग|"
            r"padon\s+ka\s+(yog|jod))",
            q) or re.search(r"\d+\s*(st|nd|rd|th)\s+term", q) or \
            re.search(r"\d+\s*(?:वां|वाँ|वीं)\s*पद", q) or \
            re.search(r"\d+\s*(?:va|wa|vaa)\s+pad\b", q):
        return "sequences"

    # Complex numbers (bare "i" expressions need digits around the i)
    if re.search(r"\bcomplex\b|conjugate|modulus|argument of|"
                 r"real part|imaginary part|a\s*\+\s*ib\b", q) or (
            "i" in q and re.search(r"\d\s*i\b|\bi\s*[\+\)\*]|\(\s*\d+\s*[\+\-]\s*\d+\s*i", q)):
        return "complex"

    # Logarithms / exponents (before algebra: log equations contain '=')
    # Wave 58: the subscript forms "log_2" / "log2" must count —
    # "_" is a word character, so a plain \b after "log" never
    # matched them and those questions fell through to the
    # arithmetic simplifier, which served "32*log_2" as the
    # value of log_2 32.
    if re.search(r"\b(log|ln|logarithm|antilog)(?:_?\d|\b)", q):
        return "exponents_logs"

    # Number theory. "mod" must be a standalone token so words like
    # "mode"/"model" are not matched; factor-of-a-number check: strip the
    # word "factor..." and filler; if no letters remain it is a number.
    # Wave 13: "prime numbers between A and B" is a LIST question —
    # the junior solver owns it (the single-number prime check
    # below cannot answer it).
    if re.search(r"\bprime\s+numbers?\s+(between|from)\b", q):
        return "junior"
    if re.search(r"\b(prime|gcd|hcf|lcm|modulo|divisible)\b", q) or \
            re.search(r"(?<![a-z])mod(?![a-z])", q) or \
            re.search(r"महत्तम|लघुत्तम|समापवर्त", q):
        return "number_theory"
    if re.search(r"\bfactor", q) and not re.search(r"[a-z]", re.sub(
            r"\bfactors?\b|\bfactorise\b|\bfactorize\b|\bof\b|"
            r"\bthe\b|\bis\b|\bplease\b", "", q)):
        return "number_theory"

    # Wave 13 junior families (Classes 0-5). Deliberately
    # placed late: every established intent above keeps its
    # priority, and these triggers are phrase-specific. The
    # junior solver itself returns None when its stricter
    # patterns do not extract clean numbers (see solve_question
    # for the fallback).
    if re.search(
            r"(\bin\s+words\b|\bnumber\s+name\b|\bplace\s+value\b|"
            r"\bexpanded\s+form\b|\btable\s+of\s+\d|"
            r"\d\s+ka\s+table\b|\bhalf\s+of\s+\d|"
            r"\bquarter\s+of\s+\d|\d\s*/\s*\d\s+of\s+\d|"
            r"\bas\s+(a\s+)?decimal\b|\bin\s+decimal\b|"
            r"\bas\s+(a\s+)?fraction\b|"
            r"\bwhich\s+is\s+(bigger|greater|larger|smaller)\b|"
            r"\badd\s+\d|\bsubtract\s+\d|\bsum\s+of\s+\d|"
            r"\bdifference\s+between\s+\d|\bproduct\s+of\s+\d|"
            r"\bdivide\s+\d|\bmultiply\s+\d|"
            r"\bshared\s+equally\b|\bdivided\s+equally\b|"
            r"\bhow\s+many\s+months\s+in\s+\d|"
            r"\bminutes?\s+after\s+\d|\bhours?\s+after\s+\d|"
            r"\bfrom\s+\d{1,2}(?::\d{2})?\s*(am|pm)\s+to\s+\d|"
            r"\bhow\s+many\s+(sides|corners|vertices)\b|"
            r"\bshape\s+with\s+\d+\s+sides|\b\d\s*-\s*sided\b|"
            r"\bname\s+the\s+shape\b|\bodd\s+or\s+even\b|"
            r"\b(odd|even)\s+numbers?\s+(between|from)\b|"
            r"\bnext\s+number\b|\bwhat\s+comes\s+next\b|"
            r"\bcomes\s+next\s*:?\s*\d|\bmissing\s+number\b|"
            r"^\s*\d+\s+is\s+(odd|even)\b|"
            r"\bmultiples?\s+of\s+\d|\bfirst\s+\d+\s+multiples?\b|"
            r"\bprime\s+numbers?\s+(between|from)\b)", q) or \
            re.search(r"\bhas\s+(?:rs\.?\s+|₹\s*|rupees\s+)?"
                      r"\d+\b.{0,90}?\b(gives|gave|lost|loses|"
                      r"eats|ate|buys|bought|gets|got|sells|"
                      r"sold)\b", q) or \
            re.search(r"\d\s+\w+\s+(have|has|contain|contains)\s+"
                      r"\d.{0,40}?\beach\b", q) or \
            re.search(r"\bcost\s+of\s+\d.{0,40}?\beach\b", q) or \
            re.search(r"^\s*(what\s+is\s+)?\d{1,3}\s*(x|×)\s*"
                      r"\d{1,3}\s*\?*\s*$", q.strip()):
        return "junior"

    # Wave 13 applied families (Classes 6-12 gaps): ratio,
    # simple interest (all forms — solve_question falls back
    # to word_problems when applied returns None), profit &
    # loss, speed stories, word equations, discriminant.
    if re.search(
            r"(\bratio\b|\bsimple\s+interest\b|\bprofit\b|"
            r"\bloss\b|\bdiscriminant\b|"
            r"\bnature\s+of\s+(the\s+)?roots\b|"
            r"km/h\s+(to|in)\s+m/s|m/s\s+(to|in)\s+km/h|"
            r"\bnumber\s+(increased|decreased|multiplied)\s+by\b|"
            r"\b(twice|thrice|double)\s+(a\s+)?number\b|"
            r"\bsum\s+of\s+a\s+number\s+and\s+\d|"
            r"\bwhen\s+\d+\s+is\s+added\s+to\s+a\s+number\b|"
            r"\btravels?\b.{0,40}?\bkm\b|\bcovers\s+\d+\s*km\b|"
            r"चाल|रेलगाड़ी|ट्रेन|ब्याज)",
            q):
        return "applied"

    # Word problems
    if re.search(
            r"(increase by|decrease by|sum is|product is|"
            r"simple interest)", q) or re.search(
                r"\d\s*(km/h|mph|m/s)\s+for\s+\d", q):
        return "word_problems"

    # Algebra: equations, inequalities, factor/expand/simplify commands
    # Wave 30: "zeroes of the polynomial ..." and polynomial
    # division ("divide x^3 + ... by x + 1") are algebra too.
    if "=" in q or re.search(r"(<=|>=|<|>)", q) or re.search(
            r"\b(solve|factorise|factorize|factor|expand|simplify)\b",
            q) or re.search(r"\b(zeroes|zeros)\b", q) or (
            re.search(r"\bdivide\b", q)
            and re.search(r"[a-z]\s*\^", q)):
        return "algebra"

    return "arithmetic"


_SOLVERS = {
    "arithmetic": solve_arithmetic,
    "algebra": solve_algebra,
    "junior": solve_junior,
    "applied": solve_applied,
    "calculus": solve_calculus,
    "linear_algebra": solve_linear_algebra,
    "number_theory": solve_number_theory,
    "word_problems": solve_word_problem,
    "trigonometry": solve_trigonometry,
    "statistics": solve_statistics,
    "geometry": solve_geometry,
    "sequences": solve_sequences,
    "complex": solve_complex,
    "sets": solve_sets,
    "exponents_logs": solve_exponents_logs,
    "plot": solve_plot,
    "distributions": solve_distributions,
    "transforms": solve_transforms,
}

_TOPICS = (
    "junior maths for Classes 0-5 (number names, place value, "
    "tables, story sums, fraction basics, money, clock and shape "
    "facts), arithmetic & percentages, algebra (equations, systems, "
    "inequalities, factor/expand/simplify), exponents & logarithms, "
    "trigonometry, calculus (limits, derivatives, integrals, ODEs "
    "incl. second-order and initial conditions), Laplace transforms "
    "and series, linear algebra (matrices), geometry & coordinate "
    "geometry, statistics & probability (incl. normal, Poisson and "
    "binomial distributions), number theory, sequences & series, "
    "ratio & proportion, simple interest, profit & loss, speed, "
    "complex numbers, sets, unit conversion, word problems and graphs "
    "(one or two functions, shaded integral area)"
)


log = logging.getLogger("ganitra.router")

# ---------------------------------------------------------------------------
# Wave 46 (audit F1a): a CPU budget for the primary solve.
#
# /api/solve and /solve are anonymous by design, and the host
# gives the whole site 100 CPU-seconds/day — but the primary
# solve ran unbounded: "expand (x + y + z + w)^60" was still
# running when the audit killed it at 25 s, so ~4 such requests
# could eat the site's whole day. Two defences, neither of which
# touches a normal solve (the Wave-45 battery's legit p99 was
# 1.6 s):
#
# 1. Pre-guards (_dangerous_shape): the known blow-up shapes are
#    refused BEFORE any SymPy work starts, so they cost ~0 CPU.
# 2. A wall-clock budget (_solve_with_budget): anything else
#    that still runs long is cut off at the budget and answered
#    with the solver's standard error dict, which the app
#    layer's fallback turns into its friendly guide.

SOLVE_BUDGET_SECONDS = 10.0

#: An expansion of (t1 + ... + tk)^n has C(n+k-1, k-1) terms;
#: past this many, writing it out is neither fast nor useful
#: to a student. (x + y)^100 = 101 terms stays allowed;
#: (x + y + z + w)^60 = 39,711 terms is refused.
_EXPANSION_TERM_LIMIT = 5000

#: A plain-integer power a^b whose result would have more
#: digits than this is a memory/print bomb, not a school sum.
_INT_POWER_DIGIT_LIMIT = 20000

_SUM_POWER_RE = re.compile(r"\(([^()]*)\)\s*(?:\^|\*\*)\s*(\d+)")
_INT_POWER_RE = re.compile(r"(?<![\d.])(\d+)\s*(?:\^|\*\*)\s*(\d+)")
_INT_TOWER_RE = re.compile(
    r"(\d+)\s*(?:\^|\*\*)\s*(\d+)\s*(?:\^|\*\*)\s*(\d+)")


def _dangerous_shape(question):
    """A short reason string when the question has a known
    symbolic blow-up shape, else None. Pure text scan — no
    SymPy work happens for a refused question."""
    q = str(question)
    # Power towers a^b^c evaluate right-first, so the effective
    # exponent is b**c: 10^10^10 is a 10-billion-digit result.
    for m in _INT_TOWER_RE.finditer(q):
        base_b, exp_c = int(m.group(2)), int(m.group(3))
        if base_b >= 2 and exp_c >= 2 \
                and exp_c * math.log10(base_b) > 4:
            return "power tower too large"
    # (sum)^n expansions: count the terms before paying for them.
    for m in _SUM_POWER_RE.finditer(q):
        base, exp = m.group(1), int(m.group(2))
        if exp < 2:
            continue
        terms = [part for part in re.split(r"[+-]", base)
                 if part.strip()]
        if len(terms) >= 2 and math.comb(
                exp + len(terms) - 1,
                len(terms) - 1) > _EXPANSION_TERM_LIMIT:
            return "expansion too large"
    # Plain-integer powers with absurd digit counts.
    for m in _INT_POWER_RE.finditer(q):
        base, exp = int(m.group(1)), int(m.group(2))
        if base >= 2 and exp >= 2 and exp * math.log10(base) \
                > _INT_POWER_DIGIT_LIMIT:
            return "integer power too large"
    return None


def _too_big_result():
    """The refusal for a guarded / over-budget solve, in the
    solver's standard failure shape (op == "error"): the app
    layer never shows this text — its Wave-18 fallback replaces
    it with the friendly guide, and the answer cache never
    stores op == "error" results."""
    return {"type": "algebra", "op": "error",
            "answer": "That one is too big to work out here.",
            "steps": []}


def _solve_with_budget(question, budget=SOLVE_BUDGET_SECONDS):
    """_solve_question_uncached with a wall-clock budget — the
    thread pattern from speedups.methods_nonblocking. A normal
    solve finishes far inside the budget and its result (or its
    exception) reaches the caller exactly as before; only an
    overrun changes behaviour. An overrun worker keeps running
    as a daemon (Python threads cannot be killed), which is why
    the pre-guards above stop the known bombs from starting at
    all; the budget caps the response time for the unforeseen."""
    box = {}

    def _run():
        try:
            box["result"] = _solve_question_uncached(question)
        except BaseException as exc:  # re-raised on this thread
            box["error"] = exc

    worker = threading.Thread(target=_run, daemon=True,
                              name="ganitra-solve")
    worker.start()
    worker.join(budget)
    if worker.is_alive():
        log.warning(
            "solve exceeded %.0fs budget for %r; answering with "
            "the fallback guide", budget, str(question)[:80])
        return _too_big_result()
    if "error" in box:
        raise box["error"]
    return box.get("result")


def solve_question(question: str):
    """Cached entry point (Kami audit 2c-1): repeat questions are
    served from the in-memory answer cache at zero CPU cost; the
    first ask, and anything uncacheable, runs the solver below.

    Wave 46 (audit F1a): known blow-up shapes are refused by the
    pre-guards and the solve itself runs under a wall-clock
    budget — see SOLVE_BUDGET_SECONDS above."""
    cached = get_cached(question)
    if cached is not None:
        return cached
    reason = _dangerous_shape(question)
    if reason is not None:
        log.warning("solve pre-guard refused %r (%s)",
                    str(question)[:80], reason)
        return _too_big_result()
    result = _solve_with_budget(question)
    put_cached(question, result)
    return result


def _solve_question_uncached(question: str):
    original = question
    # Wave 57: fold typing noise (Hinglish spellings, typos, OCR)
    # to canonical words first; Hinglish translation then works on
    # the folded text. Clean questions pass through unchanged.
    folded = normalize_spelling(question)
    translated = normalize_hinglish(folded)
    was_translated = translated.strip().lower() != question.strip().lower()
    working = translated if was_translated else question

    # Explicit unit conversion ("convert 5 km to miles", temperatures):
    # try it directly first; solve_units returns None when it is not a
    # conversion, and we then fall through to normal routing.
    # Wave 13: "how many minutes in 3 hours" is the same conversion
    # asked as a question — solve_units validates the units itself
    # and returns None for non-unit "how many" questions.
    if re.search(r"\bconvert\b", working, re.I) or re.search(
            r"\bhow\s+many\b", working, re.I):
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 32 (algebra): polynomial-theorem asks (remainder /
    # factor theorem, cubic zeroes relations, rationalisation)
    # route to arithmetic, which answers a stray fragment.
    # These phrases belong to solver/algebra.py; try it FIRST
    # and accept ONLY the new theorem ops, so algebra's generic
    # simplify fallthrough can never leak through this gate.
    if re.search(
            r"\ba\s+factor\s+of\b|rationali[sz]e"
            r"|remainder\b[^.]{0,80}?divided by"
            r"|α|β|γ", working, re.I):
        try:
            out = solve_algebra(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "remainder_theorem", "factor_theorem_k",
                "factor_theorem_check", "cubic_zeroe_relations",
                "verify_zeroes", "rationalise"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 32: a few very specific asks are systematically
    # HIJACKED by an earlier solver that returns a valid-looking
    # op answering a DIFFERENT question ("insert one geometric
    # mean" -> statistics' plain mean of the two numbers; "sum
    # and product of roots of ..." -> the equation's roots; "if
    # a + b = 10 and ab = 21, find a^2 + b^2" -> a garbage
    # "system"). These asks belong to solver/applied.py; try it
    # FIRST for them, and fall through to normal routing
    # unchanged whenever applied cannot solve them either.
    if re.search(
            r"insert\s+.*?(?:arithmetic|geometric)\s+means?\s+"
            r"between"
            r"|(?:sum|product)\b[^.]{0,25}?\b(?:roots|zeroes|"
            r"zeros)\b"
            r"|\bnature\s+of\s+(?:the\s+)?roots\b"
            r"|\ba\s*\+\s*b\s*=\s*-?\d", working, re.I):
        try:
            out = solve_applied(working)
        except Exception:
            out = None
        if out is not None and out.get("op") not in (
                "unknown", "error"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 32 (geometry): the same hijack problem in the other
    # direction — circle-theorem, centroid/collinearity and 3D
    # asks route to arithmetic/trigonometry/applied, which
    # either fail or answer a different question, and geometry
    # is never tried. These phrases belong to
    # solver/geometry.py; try it FIRST for them, falling
    # through to normal routing whenever it cannot solve them.
    if re.search(
            r"length of (?:the )?tangent"
            r"|angle between (?:the )?(?:two )?tangents"
            r"|\bchord\b"
            r"|\bcentroid\b"
            r"|\bcollinear\b"
            r"|\bequidistant\b"
            r"|direction (?:ratios|cosines)"
            r"|angle between (?:the )?two lines"
            r"|from the plane"
            r"|arc of (?:a |the )?circle"
            r"|sector of (?:a |the )?circle"
            r"|segment of (?:a |the )?circle"
            r"|dot\s+product|unit\s+vector"
            r"|length\s+of\s+(?:each\s+|the\s+)?tangent"
            r"|magnitude\s+of\s+(?:the\s+)?vector"
            r"|distance of (?:the )?point .* from the origin"
            r"|ratio does the (?:x|y)-axis divide"
            r"|\(\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?"
            r"\s*,\s*-?\d+(?:\.\d+)?\s*\)", working, re.I):
        try:
            out = solve_geometry(working)
        except Exception:
            out = None
        if out is not None and out.get("op") not in (
                "unknown", "error"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: Hindi / Hinglish word schemas (in
    # solver/applied.py) are systematically HIJACKED by the
    # expression parser, which reads the Hindi words as
    # letter variables and returns a "simplify" letter-soup
    # that is neither an error nor unknown — so the applied
    # second chance further down never fires ("3/4 ko
    # decimal me batao" answered '3*a*c*d*e**2...'). When
    # the question carries Devanagari or a common Hinglish
    # stem, try applied FIRST and accept ONLY the Wave 56
    # hindi_/hinglish_ ops, so no English path can change.
    # Wave 56: two algebra schemas whose questions never
    # route to algebra — "Evaluate 105^2 using the identity
    # (a + b)^2" lands in arithmetic (which simplifies the
    # sentence into letter-soup) and "Form a quadratic
    # equation whose roots are ..." lands nowhere. Try
    # algebra FIRST for those shapes and accept ONLY the
    # Wave 56 ops.
    if (re.search(r"using\s+(?:the\s+|an\s+)?identity",
                  working, re.I)
            and re.search(r"\d+\s*\^\s*2", working)) or \
            re.search(r"form\s+a\s+quadratic|quadratic\s+"
                      r"equation\s+whose\s+roots", working,
                      re.I):
        try:
            out = solve_algebra(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "identity_square", "form_quadratic"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: fraction commands with a whole-number
    # operand ("Add 1 and 1/5") route to the JUNIOR solver,
    # whose add pattern reads only whole numbers and
    # silently drops the "/5". Try arithmetic first when a
    # command verb meets a fraction token, accepting only
    # its fraction_* ops.
    if re.search(r"^\s*(add|subtract|multiply|divide)\b",
                 working, re.I) and \
            re.search(r"\d+\s*/\s*\d+", working):
        try:
            out = solve_arithmetic(working)
        except Exception:
            out = None
        if out is not None and str(
                out.get("op") or "").startswith("fraction_"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: set-counting questions (n(A) notation, the
    # power set, the play-both/neither class form) carry no
    # literal sets, so solve_sets' own gate never sees
    # them through the intent table. Try sets FIRST for
    # those shapes, accepting only the counting ops.
    if re.search(r"n\(\s*[a-z]\s*(?:\)|union|intersection)",
                 working, re.I) \
            or "power set" in working.lower() \
            or (re.search(r"\bplay\s+(?:both|neither)\b",
                          working, re.I)
                and re.search(r"\bclass\s+of\s+\d+", working,
                              re.I)):
        try:
            out = solve_sets(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "cardinality", "power_set", "play_neither",
                "play_both", "play_union"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: "Find the range of the data ..." —
    # route_intent's statistics pattern has no "range", so
    # these went to arithmetic and errored, although
    # solve_statistics implements range. Try statistics
    # first for the shape, accepting only its range op.
    if re.search(r"\brange\s+of\s+(?:the\s+)?(?:data|"
                 r"following)", working, re.I):
        try:
            out = solve_statistics(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == "range":
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: a BARE product in words — "can you solve
    # 17 x 24" — has no intent keywords at all and fell to
    # the fallback although it is one multiplication. Try
    # arithmetic first for the whole-question shape,
    # accepting only its evaluate op.
    if re.match(r"\s*(?:can\s+you\s+)?(?:please\s+)?"
                r"(?:solve|calculate|evaluate|find|what\s+is)?"
                r"\s*\d+(?:\.\d+)?\s*[x×]\s*\d+(?:\.\d+)?"
                r"\s*[=?]?\s*\.?\s*$", working, re.I):
        try:
            out = solve_arithmetic(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == "evaluate":
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: a BARE number list with a next-term ask
    # ("2, 4, 8, 16 ke baad kya aayega") carries no AP/GP
    # keyword for route_intent, so it never reached
    # sequences. Try sequences first for the shape,
    # accepting only its next-term ops.
    if re.match(r"\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+", working) \
            and re.search(r"ke\s+baad|agla|next\s+term|"
                          r"what\s+comes\s+next", working,
                          re.I):
        try:
            out = solve_sequences(working)
        except Exception:
            out = None
        if out is not None and "next" in str(
                out.get("op") or ""):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 56: heights-and-distances shapes can route to
    # geometry ("Two poles ... distance between their
    # tops") and never reach trigonometry. Try trigonometry
    # FIRST for those shapes, accepting only its
    # height_distance op.
    if re.search(r"ladder|kite|shadow|angle\s+of\s+"
                 r"elevation|angle\s+of\s+depression|"
                 r"distance\s+between\s+their\s+tops",
                 working, re.I):
        try:
            out = solve_trigonometry(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "height_distance", "two_observation_height"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # (Scan the ORIGINAL too: the normaliser strips some
    # stems, e.g. "batao", before this point.)
    _wl = (working + " " + original).lower()
    if re.search(r"[ऀ-ॿ]", _wl) or re.search(
            r"\b(?:batao|btaao|bataao|bataiye|kitna|kitne|"
            r"kitni|ghatao|ghaatao|jodne|jodo|keemat|kimat|"
            r"qeemat|daam|rupay|rupaye|bacche|bachche|"
            r"sankhya|duguna|tiguna|milega|milegi|chahiye|"
            r"chaahiye|ladkiyan|ladkiya|istemal|istemaal|"
            r"lambai|chaudai|aadhar|unchai|vyas|trijya|"
            r"paridhi|parimaap|kshetrafal|ghante|saal)\b",
            _wl):
        # Try the NORMALISED text first. The ORIGINAL is
        # tried only for equation-shaped questions: the
        # normaliser strips exactly the word the wrapped-
        # equation schema keys on ("batao" is removed from
        # '8x + 8 = 176 hai to x batao', leaving a text
        # whose equation no longer has a solve word) —
        # while for plain arithmetic the normaliser's own
        # translation ("15 aur 27 ko jodo" -> "15 + 27")
        # must keep ownership, so the original is NOT
        # retried there.
        out = None
        _cands = (working, original) if "=" in original \
            else (working,)
        for _cand in _cands:
            try:
                out = solve_applied(_cand)
            except Exception:
                out = None
            if out is not None and str(
                    out.get("op", "")).startswith(
                    ("hindi", "hinglish")):
                break
            out = None
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out

    intent = route_intent(working)

    # Wave 33: two more systematically-misrouted families get
    # the Wave-32 pre-check treatment. (a) LP from raw
    # inequalities routes to algebra ("=" + "≤"), whose parser
    # turns the sentence into letter-soup; the applied LP
    # patterns own it. (b) "Draw an ogive…" routes to plot;
    # the ogive-median pattern in statistics owns the median
    # ask. Both gates accept ONLY their own ops and fall
    # through unchanged otherwise.
    _wl = working.lower()
    if re.search(r"\bz\s*=", _wl) and \
            re.search(r"maxim|minim", _wl) and (
                "subject" in _wl or "≤" in working
                or "<=" in working or "≥" in working
                or ">=" in working):
        try:
            out = solve_applied(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "lp_maximise", "lp_minimise"):
            if was_translated:
                out["interpreted_as"] = translated
            return out
    if "ogive" in _wl:
        try:
            out = solve_statistics(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == "ogive_median":
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 58: a Devanagari question tries solve_applied FIRST
    # and accepts ONLY the hindi_* ops. Hindi mensuration / SI /
    # percentage statements had no pattern at all, so they fell
    # through routing to the generic parser, which letter-
    # multiplied the sentence and served the product as the
    # answer (audit #385-#514). The gate falls through unchanged
    # whenever applied has no Hindi pattern for the question.
    if re.search(r"[ऀ-ॿ]", working):
        try:
            out = solve_applied(working)
        except Exception:
            out = None
        if out is not None and str(out.get("op", "")).startswith(
                "hindi_"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 47: "How many factors does 36 have?" never reached
    # number theory — the intent strip-check rejected it (the
    # sentence keeps its words) and the arithmetic simplifier
    # returned a letter-product of the question (audit
    # #314-317). The divisor-count pattern lives in
    # solver/number_theory.py; try it FIRST for count asks
    # and accept only its own op.
    if re.search(
            r"(how\s+many|number\s+of|total\s+number\s+of)"
            r"\s+(factors|divisors)\b", working, re.I):
        try:
            out = solve_number_theory(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == "factor_count":
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 52: Devanagari word problems (Wave 35 audit #1).
    # A Hindi mensuration / SI / percentage statement names
    # no English intent keyword, so it routed to arithmetic,
    # whose simplifier multiplied the question's own
    # Devanagari letters together and returned the product
    # as the answer. The strict Hindi patterns live in
    # solver/applied.py (_hindi_word_problems); try applied
    # FIRST for Devanagari questions and accept only its
    # hindi_* ops, falling through unchanged otherwise.
    if any("ऀ" <= ch <= "ॿ" for ch in working):
        try:
            out = solve_applied(working)
        except Exception:
            out = None
        if out is not None and str(
                out.get("op", "")).startswith("hindi_"):
            if was_translated:
                out["interpreted_as"] = translated
            return out

    # Wave 20 science guard: a science question whose ONLY match
    # is a weak junior phrase must never be force-solved by the
    # Classes 0-5 solver. Downgrade to arithmetic (which honestly
    # fails), so the app layer's Wave-18/20 fallback can give the
    # kind "this is Science, Ganitra is for Maths" reply instead
    # of a made-up junior answer.
    if intent == "junior" and has_science_signal(working):
        intent = "arithmetic"

    if intent == "units":
        out = solve_units(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        # Wave 13: the units pattern also catches speed stories
        # ("180 km in 3 hours") and km/h <-> m/s requests, which
        # are not unit conversions — the applied solver owns them.
        out = solve_applied(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "arithmetic"

    # Wave 13: the unitary-cost story ("5 pens cost Rs 60, cost
    # of 8 pens") names no intent keyword, so when the classic
    # pipeline cannot even parse the question, give the applied
    # patterns one chance before reporting the error.
    # Wave 30: the same second chance now also fires when the
    # probe "succeeded" only by turning a word problem into a
    # letter-product simplify (a long sentence is never a bare
    # expression) — that junk result was what pushed real word
    # problems (compound interest, discount, marks-percentage)
    # down to the similar-example layer.
    if intent in ("arithmetic", "algebra"):
        probe_solver = _SOLVERS.get(intent, solve_arithmetic)
        try:
            probe = probe_solver(working)
        except Exception:
            probe = None
        if probe is None or (isinstance(probe, dict)
                             and (probe.get("op") == "error"
                                  or (probe.get("op") == "simplify"
                                      and len(working.split())
                                      >= 5))):
            alt = solve_applied(working)
            if alt is not None:
                if was_translated:
                    alt["interpreted_as"] = translated
                return alt

    # Wave 13 solvers return None when their strict patterns do
    # not match; fall back to the closest established pipeline
    # instead of failing (junior -> arithmetic, applied -> the
    # classic word-problem patterns).
    if intent == "junior":
        out = solve_junior(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "arithmetic"

    if intent == "applied":
        out = solve_applied(working)
        if out is not None:
            if was_translated:
                out["interpreted_as"] = translated
            return out
        intent = "word_problems"

    solver = _SOLVERS.get(intent, solve_arithmetic)
    try:
        result = solver(working)
    except Exception as e:
        result = {"type": intent, "op": "error",
                  "answer": f"Could not solve this one: {e}",
                  "steps": []}
    if isinstance(result, dict):
        # Wave 30 second chance: an intent solver that has no
        # pattern for a word problem reports op "unknown" (or an
        # error) — geometry's "Tell me the shape...", the word-
        # problem catch-all, a statistics shrug. Before that
        # non-answer is allowed to fall through to the fallback
        # layer's similar example, give the strict applied
        # patterns one pass: they return None unless the
        # student's own numbers form a complete known pattern,
        # so a real solver answer is never displaced.
        if result.get("op") in ("error", "unknown"):
            try:
                alt = solve_applied(working)
            except Exception:
                alt = None
            if alt is not None:
                if was_translated:
                    alt["interpreted_as"] = translated
                return alt
        if was_translated:
            result.setdefault("interpreted_as", translated)
        result.setdefault("steps", [])
        result.setdefault("answer", "")
        return result
    # Safety net: a solver returned a bare string.
    return {"type": intent, "answer": str(result), "steps": []}


__all__ = ["solve_question", "route_intent", "normalize_hinglish",
           "has_science_signal"]
