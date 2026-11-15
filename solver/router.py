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
    "ghnta": "ghanta",
    "jodd": "jod", "ghaata": "ghata", "gunna": "guna",
    "bhag": "bhaag", "tren": "train", "railgadi": "train",
    "ayat": "aayat", "sadharann": "sadharan",
    # Wave 59: more attested Roman-Hindi spelling variants.
    "samapvartya": "samapvartak", "parimaap": "parimap",
    "anupaat": "anupat", "madhyikaa": "madhyika",
    "sambhavana": "sambhavna", "pratisht": "pratishat",
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
    "feko sama visham sadharan "
    # Wave 59: Class 11-12 Hinglish maths vocabulary.
    "samapvartak maapank unnayan avakalan samakalan "
    "upasamuchchay madhy ghanmool vargmool sparsh vikarn kendr "
    "sanchayi barambarta ghatna tatva asal saath sath "
    "bete beti beta dusra teesra chautha din log "
    "mera meri uska uski iska iski sab paisa "
    "aaj liye raha rahi "
    "gaya gayi aaya aayi karta karti hota hoti hote deta deti "
    "leta leti bada badi naya nayi lamba "
    "tez raat mahina mahine umar "
    "ladka ladki ladke aurat baccha bacche kaisa "
    "kaisi idhar udhar kidhar dheere "
    "wale".split())

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
    "avrage": "average", "averag": "average",
    "persent": "percent",
    "circl": "circle", "daimeter": "diameter",
    "dimeter": "diameter", "radias": "radius",
    "substraction": "subtraction",
    "addtion": "addition", "quadretic": "quadratic",
    # Wave 65: more attested chat-spelling slips (each seen in
    # the Wave 65 English battery's hand-written items).
    "percant": "percent", "aera": "area", "bredth": "breadth",
    "triangl": "triangle", "heigth": "height", "raduis": "radius",
    "circumfrance": "circumference", "medain": "median",
    "dise": "dice", "numbr": "number", "geting": "getting",
    "avrege": "average", "perimter": "perimeter", "slop": "slope",
    "lenght": "length", "pls": "",
    "rectanguler": "rectangular", "simlify": "simplify",
    "volme": "volume", "calulate": "calculate",
    "deterime": "determine", "probabillity": "probability",
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
    "will would shall should may might must average union "
    "intersection subset subsets elevation tower ladder wall "
    "ground function limit derivative integral calculus matrix "
    "determinant inverse transpose conjugate modulus argument "
    "complex imaginary surd radian variance ogive frequency "
    "cumulative distribution binomial".split())

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
# Wave 59: story-vocabulary additions to the canon (beta,
# asal, lamba, idhar...) share skeletons with maths words
# and knocked them out of the unique-target table; restore
# the maths defaults explicitly (the story words themselves
# are canon, so they are never skeleton-folded).
_SKEL_TARGETS.update({"bt": "batao", "lmb": "lambai",
                      "dhr": "aadhar", "sl": "saal"})

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
        if target is None and sk[:1] in ("v", "w"):
            # Wave 59: v/w are interchangeable too (javab =
            # jawab, divar = diwar) — same transliteration
            # freedom as b/v above.
            target = _SKEL_TARGETS.get(
                ("w" if sk[0] == "v" else "v") + sk[1:])
        if target is None and sk.endswith("h") and len(sk) >= 3:
            # Wave 59: a trailing h is often just aspiration
            # spelling (kitnah = kitna, hogah = hoga).
            target = _SKEL_TARGETS.get(sk[:-1])
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


_SUP_DIGITS = {chr(0x2070): "0", chr(0xB9): "1",
               chr(0xB2): "2", chr(0xB3): "3",
               chr(0x2074): "4", chr(0x2075): "5",
               chr(0x2076): "6", chr(0x2077): "7",
               chr(0x2078): "8", chr(0x2079): "9"}
_SUP_RUN = re.compile("[" + "".join(_SUP_DIGITS)
                      + chr(0x207B) + "]+")


def _superscripts_to_caret(text: str) -> str:
    """Wave 59: students type Unicode superscripts from phone
    keyboards — "x² - 5x + 6 = 0", "2x² + 3x = 0", "x⁻¹".
    The parsers only understand caret form, and a bare "²"
    was silently dropped (the quadratic above degraded to
    "5x + 6 = 0"). Convert every superscript run to ^N."""
    def _rep(m):
        run = m.group(0)
        neg = run.startswith(chr(0x207B))
        digits = "".join(_SUP_DIGITS[c] for c in run
                         if c in _SUP_DIGITS)
        if not digits:
            return run
        return "^-" + digits if neg else "^" + digits
    return _SUP_RUN.sub(_rep, text)


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
    text = _superscripts_to_caret(str(question))
    text = text.translate(_DEV_DIGIT_TABLE)
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
    # Wave 59: single-bracket matrix notation "[2 3; 1 4]"
    # (rows split by ";", entries by spaces) -> the solver's
    # "[[2, 3], [1, 4]]" form. Only fires when the bracket
    # holds nothing but numbers, spaces and semicolons.
    def _matrix_form(m):
        rows = []
        for row in m.group(1).split(";"):
            cells = row.split()
            if not cells:
                return m.group(0)
            rows.append("[" + ", ".join(cells) + "]")
        return "[" + ", ".join(rows) + "]"
    text = re.sub(r"\[(\s*-?\d+(?:\.\d+)?(?:\s+-?\d+(?:\.\d+)?)"
                  r"+\s*;\s*-?\d+(?:\.\d+)?"
                  r"(?:\s+-?\d+(?:\.\d+)?)*\s*)\]",
                  _matrix_form, text)
    # Typed superscripts in equations: "x2 - 5x + 6 = 0" -> x^2.
    # Wave 59: a coefficient glued to the letter ("2x2 - 7x + 3
    # = 0") is the same typed form; and a limit ask carries no
    # "=" — allow it there too (but never when "log" is around:
    # "log2" is a base, not a square).
    if "=" in text or (re.search(r"\blimit?\b", text, re.I)
                       and "log" not in text.lower()):
        text = re.sub(r"(?<![A-Za-z0-9])([a-z])([23])(?![0-9])",
                      r"\1^\2", text)
        text = re.sub(r"(?<![A-Za-z])(\d)([a-z])([23])(?![0-9])",
                      r"\1\2^\3", text)
    # Wave 65: Devanagari spelling slips seen in the Wave 65
    # Hindi battery (matra/conjunct drops) folded back to the
    # canonical word, token by token. Only whole-token matches
    # change; correct spellings pass through untouched.
    text = re.sub(r"[ऀ-ॿ]+",
                  lambda m: _DEV_VARIANTS.get(m.group(0),
                                              m.group(0)), text)
    # Wave 65: word-form powers — "15 squared", "4 cubed",
    # "2 to the power 10" — the expression parser wants ^.
    # (Before this, only the FIRST "squared" was ever picked
    # up downstream, so "15 squared minus 9 squared" answered
    # 225.) Digits only: letter powers ("x squared") are the
    # algebra parser's own forms.
    text = re.sub(r"(\d+(?:\.\d+)?)\s+squared\b", r"\1^2", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s+cubed\b", r"\1^3", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s+to\s+the\s+power\s+"
                  r"(\d+(?:\.\d+)?)\b", r"\1^\2", text)
    return text


# Wave 65: Devanagari mis-spellings -> canonical spellings.
# Every key is a slip attested in the Wave 65 Hindi battery;
# held-out spellings are deliberately NOT listed (they test
# whether the schemas, not the map, carry the question).
_DEV_VARIANTS = {
    "क्षेतरफल": "क्षेत्रफल", "त्रिजिया": "त्रिज्या",
    "आयत्न": "आयतन", "प्रयिकता": "प्रायिकता",
    "परिमप": "परिमाप", "दिघात": "द्विघात",
    "माधयक": "माध्यक", "समांतर": "समान्तर",
}


def normalize_hinglish(question: str) -> str:
    q = " " + question.strip() + " "
    ql = q.lower()

    # Wave 59: self-correction — "12 km 3 ghante... are nahi,
    # woh to paidal wali baat thi — woh cycle se 24 km 2 ghante
    # me jata hai". When a student corrects themselves mid-
    # question, everything before the correction dash is a
    # discarded draft; only the corrected tail is the question.
    if "—" in ql and re.search(r"(?:are|arre)\s+nahi\b|"
                               r"nahi\s+woh\s+to\b", ql):
        ql = " " + ql.split("—", 1)[1].strip() + " "
        q = ql
    # Wave 59 round 3: "chhodo" (drop it) corrections — the
    # student abandons the first draft mid-sentence; only the
    # part after the last "chhodo" is the real question.
    if "chhodo" in ql:
        _tail = ql.rsplit("chhodo", 1)[1].strip(" ,:")
        _tail = re.sub(r"^(?:seedha\s+)?(?:batao|btao)\s*:?\s*",
                       "", _tail)
        if any(ch.isdigit() for ch in _tail):
            ql = " " + _tail + " "
        else:
            # The tail only REFERENCES the setup ("safed aane
            # ki probability kitni thi?") — the numbers live
            # in the discarded head, so keep both parts.
            ql = " " + ql.rsplit("chhodo", 1)[0].strip(" ,:—") \
                + " " + _tail + " "
        q = ql

    # Wave 65 (top priority): three shapes an early generic
    # rule below answers WRONGLY — the "ko bhaag dene par
    # shesh" ask becomes a plain division, "ek sankhya ka
    # N guna M hai" becomes the product N × M, and a
    # lambai/chaudai/unchai cuboid becomes a rectangle area.
    _p = re.search(r"(\d+(?:\.\d+)?)\s+ko\s+(\d+(?:\.\d+)?)"
                   r"\s+se\s+bhaag\s+dene\s+par\s+shesh", ql)
    if _p:
        return (f"find the remainder when {_p.group(1)} is "
                f"divided by {_p.group(2)}")
    _p = re.search(r"ek\s+sankhya\s+ka\s+(\d+(?:\.\d+)?)"
                   r"\s+guna\s+(\d+(?:\.\d+)?)\s+hai", ql)
    if _p:
        return (f"{_p.group(1)} times a number is "
                f"{_p.group(2)}")
    _p = re.search(r"lambai\s+(\d+(?:\.\d+)?)[^0-9]{0,16}?"
                   r"chaudai\s+(\d+(?:\.\d+)?)[^0-9]{0,16}?"
                   r"unchai\s+(\d+(?:\.\d+)?)", ql)
    if _p and ("aayatan" in ql or "volume" in ql):
        return (f"volume of a cuboid with length "
                f"{_p.group(1)}, breadth {_p.group(2)} and "
                f"height {_p.group(3)}")

    # Percentage: "240 ka 15 pratishat (kitna hoga)" -> "15% of 240"
    # (Wave 57: the English word "percent" in the same slot too.
    # Guarded: with "discount" nearby the ka-phrase is a price
    # story, not a plain percent-of.)
    m = re.search(r"(\d+(?:\.\d+)?)\s+(?:ka|ke)\s*(\d+(?:\.\d+)?)\s*"
                  r"(?:pratishat|percent)", ql)
    if m and "discount" not in ql:
        return f"{m.group(2)}% of {m.group(1)}"
    # Wave 59 round 4: the spelling layer already turned the
    # percent word into "%", and "ka15" can arrive merged.
    m = re.search(r"(\d+(?:\.\d+)?)\s+ka\s*(\d+(?:\.\d+)?)\s*%",
                  ql)
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
    m = re.search(r"(\d+(?:\.\d+)?)\s+(?:ka|ke)\s+(\d+(?:\.\d+)?)\s*%", ql)
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

    # Wave 59: powers multiplied with "guna" ("2^3 guna 2^4")
    # must be claimed BEFORE the plain multiply rule below —
    # it otherwise reads the exponent as an operand ("3 guna
    # 2" -> 6).
    m = re.search(r"(\d+(?:\.\d+)?\s*\^\s*\d+(?:\.\d+)?)\s+guna"
                  r"\s+(\d+(?:\.\d+)?\s*\^\s*\d+(?:\.\d+)?)", ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"

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
                  r"(\d+(?:\.\d+)?)\s*(?:ghante|hours)", ql)
    if m and "had been" not in ql and "would have" not in ql \
            and "hoti to" not in ql and "agar" not in ql:
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
    # Cuboid: "ghanaab/cuboid ... lambai L chaudai B unchai H".
    m = re.search(r"(?:ghanaab|cuboid)[^0-9]{0,60}?lambai\s+"
                  r"(\d+(?:\.\d+)?)"
                  r"[^0-9]{0,20}?chaudai\s+(\d+(?:\.\d+)?)"
                  r"[^0-9]{0,20}?unchai\s+(\d+(?:\.\d+)?)", ql)
    if m:
        if "surface area" in ql or "prasth" in ql \
                or "kul satah" in ql:
            return (f"total surface area of a cuboid with "
                    f"length {m.group(1)}, breadth {m.group(2)} "
                    f"and height {m.group(3)}")
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
    # Wave 59 round 3: "595 outof 700 marks aaye".
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:out\s*of|outof)\s+"
                  r"(\d+(?:\.\d+)?)\s*(?:marks|number)", ql)
    if m:
        return (f"what percentage is {m.group(1)} out of "
                f"{m.group(2)}")
    # Ratio share: "1000 rupaye ko 2:3 ke anupat me banto".
    # Wave 59: the "rs ko ... ratio me baanto" code-mix form too.
    m = re.search(r"(\d+(?:\.\d+)?)\s+(?:rupaye|rs)\s+ko\s+"
                  r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s+ke\s+"
                  r"(?:anupat|ratio)", ql)
    if m:
        return (f"divide {m.group(1)} in the ratio "
                f"{m.group(2)}:{m.group(3)} how much does the "
                f"first person get")
    # Wave 59 round 3: ratio stated as "3 aur 5 ke anupaat" or
    # buried in a story; the ask singles out the smaller share
    # (the first-named share in these asks).
    m = re.search(r"(\d+(?:\.\d+)?)\s+(?:rupaye|rs)[^0-9]{0,40}?"
                  r"(\d+(?:\.\d+)?)\s+aur\s+(\d+(?:\.\d+)?)"
                  r"\s+ke\s+(?:anupaat|anupat|ratio)", ql) or \
        re.search(r"(\d+(?:\.\d+)?)\s+(?:rupaye|rs)[^0-9]{0,90}?"
                  r"(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)"
                  r"\s+ke\s+(?:anupaat|anupat|ratio)", ql)
    if m and ("chhot" in ql or "bada" in ql or "bade" in ql
              or "pehle" in ql or "pehla" in ql
              or "dusre" in ql or "dusra" in ql):
        if "chhot" in ql:
            _who = "first" if float(m.group(2)) <= \
                float(m.group(3)) else "second"
        elif "bada" in ql or "bade" in ql:
            _who = "first" if float(m.group(2)) >= \
                float(m.group(3)) else "second"
        elif "dusre" in ql or "dusra" in ql:
            _who = "second"
        else:
            _who = "first"
        return (f"divide {m.group(1)} in the ratio "
                f"{m.group(2)}:{m.group(3)} how much does the "
                f"{_who} person get")
    # Discount: "2000 rupaye wali cheez par 10% discount".
    m = re.search(r"(\d+(?:\.\d+)?)\s+rupaye\s+wali[^0-9]{0,30}?"
                  r"(\d+(?:\.\d+)?)\s*%\s+discount", ql)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%")

    # Wave 65 (priority): "koi rakam R% dar se T saal me A rs
    # ho jati hai, mool rakam batao" — the scattered-SI rule
    # below would read the AMOUNT as the principal and answer
    # the interest on it; the principal-reverse ask must be
    # claimed first.
    if "mool rakam" in ql and "ho jati hai" in ql:
        _p = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:salana\s+)?"
                       r"dar\s+se\s+(\d+(?:\.\d+)?)\s*saal\s+"
                       r"me\s+(\d+(?:\.\d+)?)\s*(?:rs|rupaye)",
                       q)
        if _p:
            return (f"a sum of money amounts to {_p.group(3)} "
                    f"rs in {_p.group(2)} years at "
                    f"{_p.group(1)}% simple interest. find "
                    f"the principal")
    # (The three theft-prone Wave 65 priority rules —
    # remainder, "sankhya ka guna", cuboid — sit at the very
    # top of this function, above the generic multiply and
    # rectangle rules that would otherwise answer them
    # wrongly.)

    # ==================================================================
    # Wave 59: Hinglish deep training — whole-question translations
    # for the phrasing families Waves 52-58 never covered (Class
    # 6-12 topics in Roman Hindi: full HCF/LCM names, interest in
    # "rs/dar/varsh" words, dimension-first mensuration, Roman
    # probability, calculus in Hinglish, story forms). Every rule
    # returns the canonical English form an existing solver
    # already accepts; spelling-folded text reaches here, so only
    # canonical Hinglish words are matched.
    # ==================================================================
    _N = r"(\d+(?:\.\d+)?)"

    # --- HCF / LCM by their full Hinglish names -------------------
    m = re.search(_N + r"\s+(?:aur|or|and)\s+" + _N +
                  r"\s+ka\s+mahattam\s+samapvart\w*", ql)
    if m:
        return f"HCF of {m.group(1)} and {m.group(2)}"
    m = re.search(_N + r"\s+(?:aur|or|and)\s+" + _N +
                  r"\s+ka\s+laghuttam\s+samapvart\w*", ql)
    if m:
        return f"LCM of {m.group(1)} and {m.group(2)}"
    # HCF & LCM given, one number given, other asked.
    m = re.search(r"hcf\s+" + _N + r"\s+aur\s+lcm\s+" + _N +
                  r"\s+hai,?\s+ek\s+sankhya\s+" + _N, ql)
    if m:
        return (f"the HCF of two numbers is {m.group(1)} and "
                f"their LCM is {m.group(2)}. one number is "
                f"{m.group(3)}, find the other number")

    # --- Interest: P / R / T scattered in Hinglish words ----------
    # "2500 rs par 6% ki dar se 2 saal ka byaj", "5000 rs 8%
    # salana simple interest, 3 saal baad byaj" — pull the three
    # numbers out by their anchors (money, %, saal/varsh).
    if "%" in ql and re.search(r"\b(?:saal|varsh|sal)\b", ql):
        _mp = re.search(_N + r"\s*(?:rupaye|rs|rupees|rska)\b", ql) \
            or re.search(r"(?:rs|rupaye|rupees)\s*" + _N, ql)
        _mr = re.search(_N + r"\s*%", ql)
        _mt = re.search(_N + r"\s*(?:saal|varsh|sal)\b", ql)
        if _mp and _mr and _mt:
            _P, _R, _T = (_mp.group(1), _mr.group(1),
                          _mt.group(1))
            if "compound" in ql or \
                    re.search(r"chakravridd?hi", ql):
                if re.search(r"kul\s+kitne|kul\s+rupaye|"
                             r"kul\s+amount|mishradhan|"
                             r"kul\s+raashi", ql):
                    return (f"find the compound interest on "
                            f"{_P} at {_R}% per annum for {_T} "
                            f"years, find the total amount")
                return (f"find the compound interest on {_P} at "
                        f"{_R}% per annum for {_T} years")
            if re.search(r"byaj\s+milakar|kul\s+kitne|"
                         r"kul\s+rupaye\s+milenge|"
                         r"kul\s+raashi|kul\s+amount|"
                         r"mishradhan", ql):
                return (f"simple interest on {_P} at {_R}% "
                        f"for {_T} years, find the total "
                        f"amount")
            if "byaj" in ql or "interest" in ql:
                return (f"simple interest on {_P} at {_R}% for "
                        f"{_T} years")

    # --- Mensuration: dimension-first / Hinglish-term forms -------
    # Circle: radius stated before the ask ("trijya 7 cm hai,
    # uska area kitna hoga") — the Wave 57 rules need the ask
    # word first; these accept either order.
    if re.search(r"(?:vritt|circle|gol)\b", ql):
        _mr = re.search(r"(?:trijya|radius)\s+(?:hai\s+)?" + _N,
                        ql)
        _md = re.search(r"(?:vyas|diameter)\)?\s+(?:hai\s+)?"
                        + _N, ql)
        if _mr is None:
            # "7 cm trijya wale vritt" — radius before the word.
            _mr = re.search(_N + r"\s*(?:cm|m|mm)?\s*"
                            r"(?:trijya|radius)\b", ql)
        if _mr and ("paridhi" in ql or "circumference" in ql) \
                and "ring" not in ql and "segment" not in ql:
            return (f"circumference of a circle with radius "
                    f"{_mr.group(1)}")
        if _mr and ("area" in ql or "kshetrafal" in ql) \
                and "sector" not in ql \
                and "trijyakhand" not in ql \
                and "ring" not in ql and "segment" not in ql:
            return f"area of a circle with radius {_mr.group(1)}"
        if _md and ("paridhi" in ql or "circumference" in ql) \
                and "ring" not in ql and "segment" not in ql:
            return (f"circumference of a circle with diameter "
                    f"{_md.group(1)} cm")
        if _md and ("area" in ql or "kshetrafal" in ql) \
                and "ring" not in ql and "segment" not in ql:
            return (f"area of a circle with diameter "
                    f"{_md.group(1)} cm")
        if _md and "trijya" in ql:
            return (f"find the radius of a circle with diameter "
                    f"{_md.group(1)} cm")
        # "7 cm radius wale circle ka area"
        _mr2 = re.search(_N + r"\s*(?:cm\s+)?(?:radius|trijya)"
                         r"\s+wale\s+(?:circle|vritt|gol)", ql)
        if _mr2 and ("area" in ql or "kshetrafal" in ql) \
                and "sector" not in ql \
                and "trijyakhand" not in ql \
                and "segment" not in ql:
            return (f"area of a circle with radius "
                    f"{_mr2.group(1)}")
        # Sector: radius + degree angle + sector word.
        if _mr and ("sector" in ql or "trijyakhand" in ql):
            _ma = re.search(_N + r"\s*(?:degree|°)", ql)
            if _ma:
                return (f"area of a sector of a circle with "
                        f"radius {_mr.group(1)} and angle "
                        f"{_ma.group(1)} degrees")
    # Rectangle perimeter / area with the dimensions first.
    _mrect = re.search(r"lambai\s+" + _N + r"[^0-9]{0,30}?"
                       r"chaudai\s+" + _N, ql)
    if _mrect and "aayat" in ql:
        if "parimap" in ql or "perimeter" in ql:
            return (f"perimeter of a rectangle with length "
                    f"{_mrect.group(1)} and breadth "
                    f"{_mrect.group(2)}")
        if "area" in ql or "kshetrafal" in ql:
            return (f"area of a rectangle with length "
                    f"{_mrect.group(1)} and breadth "
                    f"{_mrect.group(2)}")
    if "aayat" in ql and ("parimap" in ql or "perimeter" in ql):
        _ml = re.search(r"lambai\s+" + _N, ql)
        _mb = re.search(r"chaudai\s+" + _N, ql)
        if _ml and _mb:
            return (f"perimeter of a rectangle with length "
                    f"{_ml.group(1)} and breadth {_mb.group(1)}")
    # Square: "varg ki (ek) bhuja S hai, kshetrafal/parimap?"
    _msq = re.search(r"varg[^0-9]{0,40}?(?:bhuja|side)\s+"
                     r"(?:hai\s+)?" + _N, ql)
    if _msq:
        if "parimap" in ql or "perimeter" in ql:
            return (f"perimeter of a square with side "
                    f"{_msq.group(1)}")
        if "area" in ql or "kshetrafal" in ql:
            return f"area of a square with side {_msq.group(1)}"
    # Parallelogram: aadhar + unchai (the triangle branch used
    # to halve these — the shape word decides).
    _mpa = re.search(r"(?:samantar\s+chaturbhuj|parallelogram)"
                     r"[^0-9]{0,60}?aadhar\s+" + _N +
                     r"[^0-9]{0,30}?unchai\s+" + _N, ql)
    if _mpa:
        return (f"area of a parallelogram with base "
                f"{_mpa.group(1)} and height {_mpa.group(2)}")
    # Trapezium: "samantar side A aur B, beech ki doori D".
    _mtr = re.search(r"(?:samantar|parallel)\s+(?:side|bhuja|"
                     r"bhujaye|sides)\s+" + _N +
                     r"\s*(?:cm|m)?\s+aur\s+" + _N, ql) \
        or re.search(r"(?:samalamb|trapezium)[^0-9]{0,60}?"
                     r"(?:samantar\s+)?(?:bhujaye|side|sides)\s+"
                     + _N + r"\s*(?:cm|m)?\s+aur\s+" + _N, ql)
    _mtd = re.search(r"doori\s+" + _N, ql) \
        or re.search(r"unchai\s+" + _N, ql)
    if _mtr and _mtd and ("trapezium" in ql or "samalamb" in ql
                          or "area" in ql or "kshetrafal" in ql):
        return (f"find the area of a trapezium whose parallel "
                f"sides are {_mtr.group(1)} and {_mtr.group(2)} "
                f"and the distance between them is "
                f"{_mtd.group(1)}")
    # Rhombus: "vikarn A aur B".
    _mrh = re.search(r"(?:samchaturbhuj|rhombus)[^0-9]{0,60}?"
                     r"vikarn\s+" + _N +
                     r"\s*(?:cm|m)?\s+aur\s+" + _N, ql) \
        or re.search(r"rhombus[^0-9]{0,40}?diagonals?\s+" + _N +
                     r"\s+aur\s+" + _N, ql)
    if _mrh:
        return (f"find the area of a rhombus whose diagonals "
                f"are {_mrh.group(1)} and {_mrh.group(2)}")
    # Cone / cylinder / sphere / cuboid / cube by Hinglish dims.
    _mco = re.search(r"(?:shanku|cone)[^0-9]{0,60}?trijya\s+" +
                     _N + r"[^0-9]{0,40}?(?:unchai|height)\s+" +
                     _N, ql)
    if _mco and ("aayatan" in ql or "volume" in ql):
        return (f"volume of a cone with radius {_mco.group(1)} "
                f"and height {_mco.group(2)}")
    _mcs = re.search(r"(?:shanku|cone)[^0-9]{0,60}?trijya\s+" +
                     _N + r"[^0-9]{0,40}?tirchhi\s+unchai\s+"
                     r"(?:\(slant\s+height\)\s+)?" + _N, ql)
    if _mcs and ("surface area" in ql or "prasth" in ql):
        return (f"total surface area of a cone with radius "
                f"{_mcs.group(1)} and slant height "
                f"{_mcs.group(2)}")
    _mcy = re.search(r"(?:belan|cylinder|belanakar)[^0-9]{0,60}?"
                     r"trijya\s+" + _N + r"[^0-9]{0,40}?"
                     r"unchai\s+" + _N, ql)
    if _mcy and ("aayatan" in ql or "volume" in ql
                 or "paani aayega" in ql):
        return (f"volume of a cylinder with radius "
                f"{_mcy.group(1)} and height {_mcy.group(2)}")
    if _mcy and ("vakr" in ql or "curved" in ql or "csa" in ql
                 or "ghuma" in ql):
        return (f"curved surface area of a cylinder with radius "
                f"{_mcy.group(1)} and height {_mcy.group(2)}")
    _msp = re.search(r"(?:gole|gola|sphere)[^0-9]{0,50}?"
                     r"trijya\s+" + _N, ql)
    if _msp and ("aayatan" in ql or "volume" in ql):
        return (f"volume of a sphere with radius "
                f"{_msp.group(1)}")
    if _msp and ("prasth" in ql or "surface" in ql):
        return (f"surface area of a sphere with radius "
                f"{_msp.group(1)}")
    _mcu = re.search(r"cuboid[^0-9]{0,20}?" + _N +
                     r"\s*(?:by|x)\s*" + _N + r"\s*(?:by|x)\s*" +
                     _N, ql)
    if _mcu and ("surface area" in ql or "prasth" in ql):
        return (f"total surface area of a cuboid with length "
                f"{_mcu.group(1)}, breadth {_mcu.group(2)} and "
                f"height {_mcu.group(3)}")
    _mcb = re.search(r"(?:ghan|cube)[^0-9]{0,50}?"
                     r"(?:bhuja|side)\s+" + _N, ql)
    if _mcb and ("prasth" in ql or "surface" in ql):
        return (f"total surface area of a cube with side "
                f"{_mcb.group(1)}")
    if _mcb and ("aayatan" in ql or "volume" in ql):
        return f"volume of a cube with side {_mcb.group(1)}"
    # Wave 59 round 2: number-first forms — "5 cm kinare wale
    # ghan", "7 cm trijya wale gole", "7 cm bhuja wale varg".
    _mcube2 = re.search(_N + r"\s*(?:cm|m)?\s*(?:kinare\s+)?"
                        r"wale\s+(?:ghan|cube)", ql) or _mcb
    if _mcube2 and ("prasth" in ql or "surface" in ql):
        return (f"total surface area of a cube with side "
                f"{_mcube2.group(1)}")
    if _mcube2 and ("aayatan" in ql or "volume" in ql):
        return f"volume of a cube with side {_mcube2.group(1)}"
    _msph2 = re.search(_N + r"\s*(?:cm|m)?\s*(?:trijya|radius)"
                       r"\s+wale\s+(?:gole|gola|sphere)", ql)
    if _msph2 and ("aayatan" in ql or "volume" in ql):
        return (f"volume of a sphere with radius "
                f"{_msph2.group(1)}")
    if _msph2 and ("prasth" in ql or "surface" in ql):
        return (f"surface area of a sphere with radius "
                f"{_msph2.group(1)}")
    _msq2 = re.search(_N + r"\s*(?:cm|m)?\s*bhuja\s+wale\s+"
                      r"varg", ql)
    if _msq2 and ("parimap" in ql or "perimeter" in ql):
        return (f"perimeter of a square with side "
                f"{_msq2.group(1)}")
    if _msq2 and ("area" in ql or "kshetrafal" in ql):
        return f"area of a square with side {_msq2.group(1)}"
    # Ring between two circles.
    _mrg = re.search(r"(?:bahari|bahar\s+wale)\s+(?:radius|"
                     r"trijya)\s+" + _N + r"[^0-9]{0,40}?"
                     r"(?:andar|andar\s+ka)\s+(?:radius|trijya)?"
                     r"\s*" + _N, ql)
    if _mrg:
        return (f"two concentric circles have radii of "
                f"{_mrg.group(1)} and {_mrg.group(2)}, find the "
                f"area of the ring between them")

    # --- Triangle: third angle ("do kon A aur B, teesra kon?") -
    if "teesra" in ql and "kon" in ql and "degree" in ql:
        _angs = re.findall(_N + r"\s*degree", ql)
        if len(_angs) >= 2:
            return (f"two angles of a triangle are {_angs[0]} "
                    f"degrees and {_angs[1]} degrees, find the "
                    f"third angle")
    _mtg3 = re.search(r"do\s+kon\s+" + _N +
                      r"[^0-9]{0,20}?" + _N +
                      r"\s*(?:degree|°)", ql)
    if _mtg3 and "teesra" in ql:
        return (f"two angles of a triangle are {_mtg3.group(1)} "
                f"degrees and {_mtg3.group(2)} degrees, find "
                f"the third angle")
    _mtg2 = re.search(r"(?:angle|kon)\s+" + _N +
                      r"\s*(?:degree|°)[^0-9]{0,50}?"
                      r"(?:dusra|dusre|doosra|second)\s+" + _N, ql)
    if _mtg2 and ("third angle" in ql or "teesra" in ql):
        return (f"two angles of a triangle are {_mtg2.group(1)} "
                f"degrees and {_mtg2.group(2)} degrees, find "
                f"the third angle")

    # --- Pythagoras in Hinglish words ---------------------------
    _mhr = re.search(r"(?:tribhuj|triangle)[^0-9]{0,50}?"
                     r"(?:bhujaye|bhuja|sides?)\s+" + _N +
                     r"\s*,\s*" + _N + r"\s+aur\s+" + _N, ql)
    if _mhr and ("area" in ql or "kshetrafal" in ql
                 or "heron" in ql):
        return (f"find the area of a triangle with sides "
                f"{_mhr.group(1)}, {_mhr.group(2)} and "
                f"{_mhr.group(3)}")
    if "karn" in ql or "hypotenuse" in ql:
        _mh = re.search(r"(?:karn|hypotenuse)\s+(?:hai\s+)?" + _N,
                        ql)
        _mb = re.search(r"(?:aadhar|base)\s+(?:hai\s+)?" + _N, ql)
        _mpl = re.search(r"(?:lamb|perpendicular)\s+(?:hai\s+)?"
                         + _N, ql)
        if _mh and (_mb or _mpl):
            _leg = (_mb or _mpl).group(1)
            return (f"the hypotenuse is {_mh.group(1)} and one "
                    f"leg is {_leg}, find the other leg")
        if _mb and _mpl:
            return (f"a right triangle has legs {_mb.group(1)} "
                    f"and {_mpl.group(1)}, find the hypotenuse")
    _mpp = re.search(r"samkon\s+tribhuj[^0-9]{0,70}?"
                     r"(?:side|bhujaye|bhuja)\s+" +
                     _N + r"\s*(?:cm|m)?\s+aur\s+" + _N, ql)
    if _mpp and ("karn" in ql or "hypotenuse" in ql):
        return (f"a right triangle has legs {_mpp.group(1)} and "
                f"{_mpp.group(2)}, find the hypotenuse")

    # --- Heights & distances (unnayan kon = elevation) ----------
    if "unnayan" in ql or "angle of elevation" in ql or \
            ("tower" in ql and "kon" in ql and "degree" in ql
             and "unchai" in ql):
        _ma = re.search(_N + r"\s*(?:degree|°)", ql)
        _mh = re.search(r"(?:unchai|height)\s+(?:hai\s+)?" + _N +
                        r"\s*m\b", ql) or re.search(
                            r"tower\s+(?:ki\s+)?unchai\s+" + _N,
                            ql)
        if _ma and _mh and ("doori" in ql or "distance" in ql
                            or "door" in ql):
            return (f"a tower is {_mh.group(1)} m tall. the "
                    f"angle of elevation of its top from a point "
                    f"on the ground is {_ma.group(1)} degrees. "
                    f"find the distance of the point from the "
                    f"foot of the tower")
        _md = re.search(_N + r"\s*m\s+(?:door|doori|distance)",
                        ql)
        if _ma and _md and ("unchai" in ql or "height" in ql):
            return (f"the angle of elevation of the top of a "
                    f"tower from a point {_md.group(1)} m away "
                    f"from its foot is {_ma.group(1)} degrees, "
                    f"find the height of the tower")
    _mld = re.search(r"(?:seedhi|ladder)[^0-9]{0,50}?(?:lambai|"
                     r"length)\s+" + _N + r"\s*m[^0-9]{0,70}?" +
                     _N + r"\s*(?:degree|°)", ql)
    if _mld and ("unchai" in ql or "height" in ql or "diwar" in ql
                 or "wall" in ql):
        return (f"a ladder of length {_mld.group(1)} m makes "
                f"{_mld.group(2)} degrees with the ground, find "
                f"the height it reaches on the wall")

    # --- Train speed quadratic (Roman-Hindi story form) ---------
    # Wave 59 round 4 (Deploy-3 live gap): the Hinglish
    # conditional — "ek train 360 km jati hai, agar speed
    # 5 km/h zyada hoti to 1 ghanta kam lgta, speed ktni
    # hai btao". Fact extraction (distance / speed delta /
    # time delta) so any word order and spelling variant
    # reaches the applied speed_time_quadratic schema via
    # its NCERT English twin.
    if ("train" in ql or "rail" in ql or "relgadi" in ql) \
            and ("agar" in ql or " if " in ql):
        _mdist = re.search(_N + r"\s*km(?!\s*/)", ql)
        _minc = re.search(r"speed\s+" + _N +
                          r"\s*km/h\s+(?:zyada|jyada|adhik|"
                          r"badh\w*)", ql)
        _mdec = re.search(r"speed\s+" + _N +
                          r"\s*km/h\s+kam", ql)
        _mtl = re.search(_N + r"\s+ghant\w*\s+kam\s+"
                         r"(?:lag\w*|lgt\w*)", ql)
        _mtm = re.search(_N + r"\s+ghant\w*\s+"
                         r"(?:zyada|jyada|adhik)\s+"
                         r"(?:lag\w*|lgt\w*)", ql)
        if _mdist and _minc and _mtl:
            return (f"a train travels {_mdist.group(1)} km. "
                    f"if the speed were {_minc.group(1)} km/h "
                    f"more, it would take {_mtl.group(1)} hour "
                    f"less, find the speed")
        if _mdist and _mdec and _mtm:
            return (f"a train travels {_mdist.group(1)} km. "
                    f"if the speed were {_mdec.group(1)} km/h "
                    f"less, it would take {_mtm.group(1)} hours "
                    f"more, find the speed")
    _mtsp = re.search(r"train[^0-9]{0,60}?" + _N +
                      r"\s*km[^0-9]{0,60}?in\s+" + _N +
                      r"\s*(?:hours|hour)\b", ql)
    if _mtsp and "speed" in ql:
        return (f"a train covers {_mtsp.group(1)} km in "
                f"{_mtsp.group(2)} hours, find the speed")
    if "train" in ql and "kam lagta" in ql or \
            "train" in ql and "kam lagega" in ql:
        _md = re.search(_N + r"\s*km\b", ql)
        _mk = re.search(_N + r"\s*km/h\s*(?:zyada|adhik|badha)",
                        ql)
        _mt2 = re.search(_N + r"\s*ghanta?\s+kam", ql)
        if _md and _mk and _mt2:
            return (f"a train travels {_md.group(1)} km. if its "
                    f"speed were {_mk.group(1)} km/h more, it "
                    f"would take {_mt2.group(1)} hour less. find "
                    f"the speed of the train")

    # --- Speed unit conversion ----------------------------------
    m = re.search(_N + r"\s*km/h\s+ko\s+m/s", ql)
    if m:
        return f"convert {m.group(1)} km/h to m/s"
    m = re.search(_N + r"\s*m/s\s+ko\s+km/h", ql)
    if m:
        return f"convert {m.group(1)} m/s to km/h"

    # --- Fraction operations in words ---------------------------
    _mld2 = re.search(r"(?:seedhi|ladder)[^0-9]{0,40}?" + _N +
                      r"\s*m\s+(?:lambi|lambai)[^0-9]{0,90}?"
                      + _N + r"\s*(?:degree|°)", ql)
    if _mld2 and "unchai" in ql:
        return (f"a ladder of length {_mld2.group(1)} m makes "
                f"{_mld2.group(2)} degrees with the ground, find "
                f"the height it reaches on the wall")
    _mtw = re.search(r"tower[^0-9]{0,80}?(?:height|unchai)\s+"
                     + _N + r"\s*m[^0-9]{0,80}?angle\s+of\s+"
                     r"elevation\s+" + _N, ql)
    if _mtw and "doori" in ql:
        return (f"the angle of elevation of a tower is "
                f"{_mtw.group(2)} degrees, the tower is "
                f"{_mtw.group(1)} m tall, find the distance")
    _FR = r"(\d+)\s*/\s*(\d+)"
    m = re.search(_FR + r"\s+ka\s+" + _FR + r"\s+guna", ql)
    if m:
        return (f"{m.group(1)}/{m.group(2)} * "
                f"{m.group(3)}/{m.group(4)}")
    m = re.search(_FR + r"\s+me\s+se\s*" + _FR +
                  r"\s+gha+ta+", ql)
    if m:
        return (f"{m.group(1)}/{m.group(2)} - "
                f"{m.group(3)}/{m.group(4)}")
    m = re.search(_FR + r"\s+ko\s+" + _FR + r"\s+se\s+bhaag", ql)
    if m:
        return (f"({m.group(1)}/{m.group(2)}) / "
                f"({m.group(3)}/{m.group(4)})")

    # --- Roots in Hinglish words ----------------------------------
    m = re.search(_N + r"\s+ka\s+ghanmool", ql)
    if m:
        return f"cube root of {m.group(1)}"
    m = re.search(_N + r"\s+ka\s+(?:(\d+)\s*(?:va|wa)|"
                  r"(teesra|chautha|paanchva|chhatha|saatva|"
                  r"aathva))\s+mool", ql)
    if m:
        _ord = {"teesra": 3, "chautha": 4, "paanchva": 5,
                "chhatha": 6, "saatva": 7, "aathva": 8}
        _n59 = int(m.group(2)) if m.group(2) else _ord[m.group(3)]
        _suf = {1: "st", 2: "nd", 3: "rd"}.get(_n59, "th")
        return f"{_n59}{_suf} root of {m.group(1)}"

    # --- Logarithms: "log 2 ki base par 8", "log 8, base 2" -----
    m = re.search(r"log\s+" + _N + r"\s+ki\s+base\s+par\s+" + _N,
                  ql)
    if m:
        return f"log base {m.group(1)} of {m.group(2)}"
    m = re.search(r"log\s+" + _N + r"[^0-9]{0,30}?base\s+" + _N,
                  ql)
    if m:
        return f"log base {m.group(2)} of {m.group(1)}"

    # --- Determinant stated in words -----------------------------
    m = re.search(r"matrix\s+ke\s+tatva\s+" + _N + r",\s*" + _N +
                  r",\s*" + _N + r",\s*" + _N, ql)
    if m:
        return (f"determinant of [[{m.group(1)}, {m.group(2)}], "
                f"[{m.group(3)}, {m.group(4)}]]")
    m = re.search(r"matrix[^0-9]{0,25}?(?:pehla|pehle|first)\s+"
                  r"row\s+" + _N + r",\s*" + _N +
                  r"\s+aur\s+(?:dusra|dusre|second)\s+row\s+"
                  + _N + r",\s*" + _N, ql)
    if m:
        return (f"determinant of [[{m.group(1)}, {m.group(2)}], "
                f"[{m.group(3)}, {m.group(4)}]]")

    # --- Calculus in Hinglish ------------------------------------
    _mder = re.search(r"(.+?)\s+ka\s+(?:derivative|avakalan)\b",
                      ql)
    if _mder:
        _expr = _mder.group(1).strip()
        _expr = re.sub(r"^(?:find\s+karo\s+|batao\s+)", "", _expr)
        for _fw in range(4):
            _stripped = re.sub(
                r"^(?:find|karo|ki|batao|bta|yr|yar|yarrr|oye|"
                r"guru|bhai|please|plz)\s+", "", _expr)
            if _stripped == _expr:
                break
            _expr = _stripped
        _mat = re.search(r"x\s*=\s*(-?\d+(?:\.\d+)?)", ql)
        if _mat:
            return (f"derivative of {_expr} at x = "
                    f"{_mat.group(1)}")
        return f"derivative of {_expr}"
    _mder2 = re.search(r"(.+?)\s+ka\s+x\s*=\s*"
                       r"(-?\d+(?:\.\d+)?)\s+par\s+"
                       r"(?:derivative|avakalan)\b", ql)
    if _mder2:
        _expr = _mder2.group(1).strip()
        for _fw in range(4):
            _stripped = re.sub(
                r"^(?:find|karo|ki|batao|bta|yr|yar|yarrr|oye|"
                r"guru|bhai|please|plz)\s+", "", _expr)
            if _stripped == _expr:
                break
            _expr = _stripped
        return (f"derivative of {_expr} at x = "
                f"{_mder2.group(2)}")
    _mintA = re.search(r"(.+?)\s+ka\s+" + _N + r"\s+se\s*" + _N
                       + r"\s+tak[^0-9]{0,40}?"
                       r"(?:samakalan|integral)", ql)
    if _mintA:
        return (f"integrate {_mintA.group(1).strip()} "
                f"from {_mintA.group(2)} to {_mintA.group(3)}")
    _mintB = re.search(_N + r"\s+se\s*" + _N + r"\s+tak\s+"
                       r"(.+?)\s+ka\s+(?:integral|samakalan)",
                       ql)
    if _mintB:
        return (f"integrate {_mintB.group(3).strip()} "
                f"from {_mintB.group(1)} to {_mintB.group(2)}")
    _mint = re.search(r"(.+?)\s+ka\s+(?:integral|samakalan)\b"
                      r"[^0-9]{0,40}?" + _N + r"\s+se\s+" + _N +
                      r"\s+tak", ql)
    if _mint:
        return (f"integrate {_mint.group(1).strip()} from "
                f"{_mint.group(2)} to {_mint.group(3)}")
    _mint2 = re.search(r"(.+?)\s+ka\s+(?:integral|samakalan)\b",
                       ql)
    if _mint2:
        return f"integral of {_mint2.group(1).strip()}"

    # --- Trig values & inverse angles ----------------------------
    m = re.search(r"\b(sin|cos|tan)\s+" + _N +
                  r"\s*(?:degree|°)\s+ki\s+value", ql)
    if m:
        return f"value of {m.group(1)} {m.group(2)} degrees"
    _mtg = re.search(r"\b(sin|cos|tan)\s+theta\s*=\s*"
                     r"([0-9\s/().√a-z]+?)\s+hai\b", ql)
    if _mtg and ("theta kitne degree" in ql
                 or "theta ki value degree" in ql):
        _v = _mtg.group(2).strip().replace("√", "sqrt")
        _v = re.sub(r"sqrt\s*(\d+)", r"sqrt(\1)", _v)
        return (f"if {_mtg.group(1)} theta = {_v}, find the "
                f"value of theta in degrees")

    # --- Averages: list forms, total-from-average, matches -------
    m = re.search(r"([\d][\d\s,\.]*?)\s+ka\s+mean[^0-9]{0,60}?"
                  r"(?:aur\s+)?sankhya\s+" + _N + r"\s+jod", ql)
    if m and "," in m.group(1):
        return f"mean of {m.group(1).strip()}, {m.group(2)}"
    m = re.search(r"([\d][\d\s,\.]*?)\s+ka\s+(?:madhy|average|"
                  r"averag)\b", ql)
    if m and "," in m.group(1):
        return f"mean of {m.group(1).strip()}"
    if ("average" in ql or "ausat" in ql or "mean" in ql) \
            and "madhyika" not in ql and "geometric" not in ql \
            and "harmonic" not in ql \
            and "find the value" not in ql \
            and not re.search(r"\bf\s*:", ql):
        _mlist = re.search(r"(\d+(?:\.\d+)?(?:\s*,\s*"
                           r"\d+(?:\.\d+)?){1,}"
                           r"(?:\s*(?:aur|and)\s*"
                           r"\d+(?:\.\d+)?)?)", ql)
        if _mlist and "class interval" not in ql \
                and "frequenc" not in ql and "ogive" not in ql \
                and not re.search(
                r"(?:average|ausat|mean)\s+(?:of\s+)?\d+\s+"
                r"(?:numbers|sankhya)", ql):
            return f"mean of {re.sub(r'\s*(?:aur|and)\s*', ', ', _mlist.group(1))}"
    m = re.search(_N + r"\s+match\s+me\s+kul\s+" + _N +
                  r"\s+run", ql)
    if m and "average" in ql:
        return f"{m.group(2)} / {m.group(1)}"
    m = re.search(_N + r"\s+[^0-9]{0,30}?average\s+(?:umar\s+|"
                  r"age\s+)?" + _N, ql)
    if m and "kul" in ql:
        return (f"the average of {m.group(1)} numbers is "
                f"{m.group(2)}, find their sum")

    # --- Probability in Roman Hindi ------------------------------
    if re.search(r"sin\s*(?:square|\^2|²)\s*(?:theta)?\s*\+\s*"
                 r"cos\s*(?:square|\^2|²)", ql) \
            and "prove" not in ql and "=" not in ql:
        return "find the value of sin^2 theta + cos^2 theta"
    _ml59 = re.search(r"(\d+(?:\.\d+)?(?:\s*,\s*"
                      r"\d+(?:\.\d+)?){1,}"
                      r"(?:\s*(?:aur|and)\s*"
                      r"\d+(?:\.\d+)?)?)", ql)
    _ml59t = re.sub(r"\s*(?:aur|and)\s*", ", ",
                    _ml59.group(1)) if _ml59 else ""
    if _ml59 and ("madhyika" in ql or "median" in ql) \
            and "class interval" not in ql \
            and "frequenc" not in ql:
        return f"median of {_ml59t}"
    if _ml59 and ("bahulak" in ql or re.search(r"\bmode\b", ql)) \
            and "class interval" not in ql \
            and "frequenc" not in ql:
        return f"mode of {_ml59t}"
    m = re.search(_N + r"\s+(?:ladko|logo|students|baccho)"
                  r"[^0-9]{0,30}?(?:ausat|mean|average)[^0-9]{0,20}?"
                  + _N + r"[^0-9]{0,60}?" + _N +
                  r"\s+(?:ladko|logo|students|baccho)"
                  r"[^0-9]{0,30}?(?:ausat|mean|average)?"
                  r"[^0-9]{0,20}?" + _N, ql)
    if m and ("milakar" in ql or "combined" in ql or "kul" in ql):
        return (f"the mean of {m.group(1)} numbers is "
                f"{m.group(2)} and the mean of {m.group(3)} "
                f"numbers is {m.group(4)}, find the combined mean")
    m = re.search(_N + r"\s+sankhya\w*\s+ka\s+mean\s+" + _N +
                  r"[^0-9]{0,90}?sankhya\s+" + _N +
                  r"\s+ki\s+jagah\s+" + _N + r"\s+padh", ql)
    if m:
        return (f"the mean of {m.group(1)} numbers is "
                f"{m.group(2)}. it was found that {m.group(3)} "
                f"was wrongly read as {m.group(4)}. find the "
                f"correct mean")
    # --- Profit / loss / selling price in Hinglish ----------------
    _mpl = re.search(_N + r"\s*(?:rs|rupaye)\s+me\s+kharid\w*\s+"
                     r"aur\s+" + _N +
                     r"\s*(?:rs|rupaye)?\s*(?:me\s+)?bech\w*", ql)
    if _mpl and ("profit" in ql or "munafa" in ql or "loss" in ql
                 or "ghata" in ql or "nuksan" in ql):
        if "loss" in ql or "ghata" in ql or "nuksan" in ql:
            return (f"bought for {_mpl.group(1)} and sold for "
                    f"{_mpl.group(2)}, loss percent")
        return (f"bought for {_mpl.group(1)} and sold for "
                f"{_mpl.group(2)}, profit percent")
    _mpl = re.search(_N + r"\s*(?:rs|rupaye)\s+me[^0-9]{0,120}?"
                     r"kharid\w*.{0,220}?" + _N +
                     r"\s*(?:rs|rupaye)\s+me\s+bech\w*", ql)
    if _mpl and ("profit" in ql or "munafa" in ql or "loss" in ql
                 or "ghata" in ql or "nuksan" in ql):
        if "loss" in ql or "ghata" in ql or "nuksan" in ql:
            return (f"bought for {_mpl.group(1)} and sold for "
                    f"{_mpl.group(2)}, loss percent")
        return (f"bought for {_mpl.group(1)} and sold for "
                f"{_mpl.group(2)}, profit percent")
    _msp59 = re.search(r"cost\s+price\s+(?:is\s+)?" + _N +
                       r"[^0-9]{0,50}?" + _N + r"\s*%\s*profit",
                       ql)
    if _msp59 and "selling price" in ql:
        return (f"cost price is {_msp59.group(1)}, profit is "
                f"{_msp59.group(2)}%, find the selling price")
    _msp59 = re.search(_N + r"\s*(?:rs|rupaye)\s+me\s+kharidkar\s+"
                       + _N + r"\s*%\s*profit\s+par\s+bech\w*",
                       ql)
    if _msp59 and "selling price" in ql:
        return (f"cost price is {_msp59.group(1)}, profit is "
                f"{_msp59.group(2)}%, find the selling price")
    if "sambhavna" in ql or "probability" in ql:
        _mc = re.search(r"(do|teen|ek|char|two|three)\s+sikke"
                        r"[^0-9]{0,80}?kam\s+se\s+kam\s+ek\s+"
                        r"chit", ql)
        if _mc:
            _w = {"do": "two", "teen": "three", "ek": "one",
                  "char": "four"}.get(_mc.group(1), _mc.group(1))
            return (f"{_w} coins are tossed, find the "
                    f"probability of getting at least one head")
        _mpn = re.search(r"1\s+se\s+" + _N +
                         r"\s+tak[^0-9]{0,70}?" + _N +
                         r"\s+ka\s+gunaj", ql)
        if _mpn:
            return (f"a number is chosen from 1 to "
                    f"{_mpn.group(1)}, find the probability "
                    f"that it is a multiple of {_mpn.group(2)}")
        _mpn = re.search(r"1\s+se\s+" + _N +
                         r"\s+tak[^0-9]{0,70}?" + _N +
                         r"\s+se\s+vibhajit", ql)
        if _mpn:
            return (f"a number is chosen from 1 to "
                    f"{_mpn.group(1)}, find the probability "
                    f"that it is divisible by {_mpn.group(2)}")
        _md = re.search(r"(?:die|pasa|paasa)\b[^0-9]{0,60}?"
                        r"kam\s+se\s+kam\s+" + _N, ql)
        if _md:
            return (f"a die is thrown, find the probability of "
                    f"getting at least {_md.group(1)}")
        _md = re.search(r"(?:die|pasa|paasa)\b[^0-9]{0,60}?" +
                        _N + r"\s+na\s+aane", ql)
        if _md:
            return (f"a die is thrown, find the probability of "
                    f"not getting a {_md.group(1)}")
        _mc = re.search(r"(do|teen|ek|char|two|three)\s+sikke"
                        r"[^0-9]{0,80}?ek\s+bhi\s+chit\s+na", ql)
        if _mc:
            _w = {"do": "two", "teen": "three", "ek": "one",
                  "char": "four"}.get(_mc.group(1), _mc.group(1))
            return (f"{_w} coins are tossed, find the "
                    f"probability of getting no heads")
        if re.search(r"coin\s+ko\s+do\s+baar\s+uchala", ql) and \
                "dono baar head" in ql:
            return ("two coins are tossed, find the probability "
                    "that both coins show heads")
        _COL59 = (r"(lal|laal|red|neel\w*|blue|kaal\w*|black|"
                  r"hari|green|peel\w*|yellow|safed|white)")
        _mbg = re.search(r"(?:bag|thaili|thaile|thaila|box)\s+me"
                         r"[^0-9]{0,30}?" + _N + r"\s+" + _COL59
                         + r"\s+(?:(?:aur|or|and)\s+)?" + _N + r"\s+" + _COL59,
                         ql)
        if _mbg:
            def _cen59(w):
                if w.startswith("neel"):
                    return "blue"
                if w.startswith("kaal"):
                    return "black"
                if w.startswith("peel"):
                    return "yellow"
                return {"lal": "red", "laal": "red",
                        "hari": "green"}.get(w, w)
            _c1 = _cen59(_mbg.group(2))
            _c2 = _cen59(_mbg.group(4))
            _tot = (f"{_mbg.group(1)} {_c1} and "
                    f"{_mbg.group(3)} {_c2}")
            _tail = ql[_mbg.end():]
            _na = re.search(r"(?:na\s+hone|na\s+aane)", _tail)
            if _na:
                _pre = _tail[:_na.start()]
                _asked = _c2 if _mbg.group(4) in _pre else _c1
                return (f"a bag has {_tot} balls, find the "
                        f"probability of not getting a {_asked} "
                        f"ball")
            _asked = _c2 if _mbg.group(4) in _tail else _c1
            return (f"a bag has {_tot} balls, find the "
                    f"probability of getting a {_asked} ball")
        if ("patta" in ql or "patte" in ql or "card" in ql) \
                and not re.search(
                    r"of\s+(?:hearts|diamonds|spades|clubs)",
                    ql):
            _deck = ("a card is drawn from a deck of 52 cards, "
                     "find the probability of getting ")
            if "kaala badshah" in ql or "black king" in ql:
                return _deck + "a black king"
            if "raja ya rani" in ql or "king or queen" in ql \
                    or re.search(
                        r"(?:king|queen)\s+or\s+(?:a\s+)?"
                        r"(?:queen|king)", ql):
                return _deck + "a king or a queen"
            # Wave 65: "red king" used to fall into the
            # plain-king branch below and lose its colour
            # (answered 4/52 instead of 2/52).
            if "red king" in ql or "laal raja" in ql \
                    or "lal raja" in ql:
                return _deck + "a red king"
            if "red queen" in ql or "laal rani" in ql \
                    or "lal rani" in ql:
                return _deck + "a red queen"
            if "black queen" in ql or "kaali rani" in ql:
                return _deck + "a black queen"
            if re.search(r"\b(?:rani|queen)\b", ql):
                return _deck + "a queen"
            if re.search(r"\b(?:raja|king)\b", ql):
                return _deck + "a king"
            if "laal" in ql or "lal " in ql or " red" in ql:
                return _deck + "a red card"
    m = re.search(r"p\(e\)\s*=\s*(\d+(?:\.\d+)?(?:\s*/\s*"
                  r"\d+(?:\.\d+)?)?)\s+hai\s+to\s+p\(not\s+e\)",
                  ql)
    if m:
        return f"if P(E) = {m.group(1)}, find P(not E)"
    m = re.search(r"probability\s+(\d+)\s*/\s*(\d+)\s+hai\s+"
                  r"to\s+uske\s+na\s+hone", ql)
    if m:
        return (f"if P(E) = {m.group(1)}/{m.group(2)}, find "
                f"P(not E)")

    # --- Sets in Hinglish -----------------------------------------
    _msets = re.findall(r"\{[^}]*\}", ql)
    if len(_msets) >= 2 and ("sirf" in ql or "only" in ql):
        return (f"A = {_msets[0]} and B = {_msets[1]}, find the "
                f"elements only in A")
    m = re.search(r"(\d+)\s+tatva[^0-9]{0,50}?(?:upasamuchchay|"
                  r"subsets)", ql)
    if m:
        return (f"a set has {m.group(1)} elements, how many "
                f"subsets does it have")

    # --- Complex numbers ------------------------------------------
    _mvenn = re.search(_N + r"\s+(?:ladke|log|students|bacche)"
                       r"[^0-9]{0,50}?(\w+)\s+khelte\s+hain,\s*"
                       + _N + r"[^0-9]{0,50}?(\w+)\s+khelte\s+"
                       r"hain\s+(?:aur|or|and)\s+" + _N + r"\s+dono", ql)
    if _mvenn:
        _vb = (f"n(A) = {_mvenn.group(1)}, n(B) = "
               f"{_mvenn.group(3)} and n(A intersection B) = "
               f"{_mvenn.group(5)}")
        if "sirf" in ql and _mvenn.group(4) in \
                ql.split("sirf")[-1]:
            return _vb + ", find n(only B)"
        if "sirf" in ql:
            return _vb + ", find n(only A)"
        return _vb + ", find n(A union B)"
    _mvenn = re.search(_N + r"\s+log\s+hindi\s+bolte\s+hain,\s*"
                       + _N + r"\s+english\s+bolte\s+hain\s+"
                       r"(?:aur|or|and)\s+"
                       + _N + r"\s+dono\s+bolte", ql)
    if _mvenn:
        _vb = (f"n(A) = {_mvenn.group(1)}, n(B) = "
               f"{_mvenn.group(2)} and n(A intersection B) = "
               f"{_mvenn.group(3)}")
        if "sirf english" in ql:
            return _vb + ", find n(only B)"
        if "sirf hindi" in ql:
            return _vb + ", find n(only A)"
        return _vb + ", find n(A union B)"
    m = re.search(r"a\s+me\s+" + _N + r",?\s*b\s+me\s+" + _N +
                  r"\s+aur\s+a\s+union\s+b\s+me\s+" + _N, ql)
    if m:
        return (f"n(A) = {m.group(1)}, n(B) = {m.group(2)} and "
                f"n(A union B) = {m.group(3)}, find "
                f"n(A intersection B)")
    ql = re.sub(r"\+\s*i\s*\)", "+ 1i)", ql)
    ql = re.sub(r"-\s*i\s*\)", "- 1i)", ql)
    m = re.search(r"(?:\(|number\s+|sankhya\s+)?" + _N +
                  r"\s*\+\s*" + _N +
                  r"i\s*\)?\s*(?:ka|ki)\s+(?:modulus|maapank)",
                  ql)
    if m:
        return (f"find the modulus of {m.group(1)} + "
                f"{m.group(2)}i")
    if re.search(r"\bi\s+ka\s+varg\b|\bi\s+square\b", ql):
        return "value of i^2"
    m = re.search(r"i\s*\^\s*(\d+)", ql)
    if m and ("value" in ql or "kitni" in ql or "kya" in ql):
        return f"value of i^{m.group(1)}"
    m = re.search(r"\(\s*" + _N + r"\s*\+\s*" + _N +
                  r"i\s*\)\s*(?:ka|ki|me\s+se)\s+"
                  r"(?:asal\s+bhaag|real\s+part)", ql)
    if m:
        return (f"what is the real part of {m.group(1)} + "
                f"{m.group(2)}i")
    m = re.search(r"\(\s*" + _N + r"\s*\+\s*" + _N +
                  r"i\s*\)\s*(?:\+|aur)\s*\(\s*" + _N +
                  r"\s*\+\s*" + _N +
                  r"i\s*\)[^0-9]{0,60}?(?:kalpanik\s+bhaag|"
                  r"imaginary\s+part)", ql)
    if m:
        return (f"find the imaginary part of ({m.group(1)} + "
                f"{m.group(2)}i) + ({m.group(3)} + "
                f"{m.group(4)}i)")
    m = re.search(r"\(\s*" + _N + r"\s*\+\s*" + _N +
                  r"i\s*\)\s*me\s+se\s*\(\s*" + _N +
                  r"\s*\+\s*" + _N +
                  r"i\s*\)\s*(?:ghata\w*\s*,?\s*)?"
                  r"(?:asal\s+bhaag|real\s+part)", ql)
    if m:
        return (f"what is the real part of ({m.group(1)} + "
                f"{m.group(2)}i) - ({m.group(3)} + "
                f"{m.group(4)}i)")

    # --- Sums of natural / odd numbers -----------------------------
    m = re.search(r"(?:pehle|pehli)\s+" + _N +
                  r"\s+(?:natural|prakr[ai]t\w*)\s+"
                  r"(?:sankhya\w*|numbers?)", ql)
    if m and ("yog" in ql or "jod" in ql or "sum" in ql):
        return f"sum of the first {m.group(1)} natural numbers"
    m = re.search(r"(?:pehle|pehli)\s+" + _N +
                  r"\s+visham\s*(?:\(odd\)\s*)?sankhya\w*", ql)
    if m and ("yog" in ql or "jod" in ql or "sum" in ql):
        return f"sum of the first {m.group(1)} odd numbers"

    # --- Coordinate geometry ---------------------------------------
    _mpts = re.findall(r"\(\s*-?\d+(?:\.\d+)?\s*,\s*"
                       r"-?\d+(?:\.\d+)?\s*\)", ql)
    if len(_mpts) >= 2 and re.search(r"baantne\s+wal[ae]", ql):
        _mr = re.search(_N + r"\s*:\s*" + _N, ql)
        if _mr:
            return (f"find the point which divides the line "
                    f"joining {_mpts[0]} and {_mpts[1]} in the "
                    f"ratio {_mr.group(1)}:{_mr.group(2)}")
    if len(_mpts) >= 2 and ("equidistant" in ql
                            or "barabar doori" in ql) \
            and "x-axis" in ql:
        return (f"find the point on the x-axis which is "
                f"equidistant from {_mpts[0]} and {_mpts[1]}")

    # --- Algebra: zeroes, remainder, limits (typed x2 inside) -----
    _mpts3 = re.findall(r"\((-?\d+(?:\.\d+)?)\s*,\s*"
                        r"(-?\d+(?:\.\d+)?)\)", ql)
    if len(_mpts3) == 3 and ("area" in ql or "kshetrafal" in ql):
        _p = _mpts3[:3]
        return (f"area of a triangle with vertices "
                f"({_p[0][0]}, {_p[0][1]}), ({_p[1][0]}, "
                f"{_p[1][1]}) and ({_p[2][0]}, {_p[2][1]})")
    if len(_mpts3) >= 1 and ("mool bindu" in ql
                             or "origin" in ql) \
            and ("doori" in ql or "distance" in ql):
        return (f"distance of the point ({_mpts3[0][0]}, "
                f"{_mpts3[0][1]}) from the origin")
    if len(_mpts3) >= 2 and ("doori" in ql or "distance" in ql):
        if "mool bindu" in ql or "origin" in ql:
            return (f"distance of the point ({_mpts3[0][0]}, "
                    f"{_mpts3[0][1]}) from the origin")
        _p = _mpts3[:2]
        return (f"distance between ({_p[0][0]}, {_p[0][1]}) "
                f"and ({_p[1][0]}, {_p[1][1]})")
    def _fix_expr(e):
        e = re.sub(r"([a-z])([23])(?![0-9])", r"\1^\2", e)
        return re.sub(r"\s+by\s+", " / ", e).strip()
    if "factor" in ql:
        _mpf = re.search(r"p\(x\)\s*=\s*(.+?)\s+ka\s+factor",
                         ql)
        if _mpf:
            return f"find the zeroes of {_fix_expr(_mpf.group(1))}"
    m = re.search(r"mool\s+" + _N + r"\s+(?:aur|or|and)\s*" + _N +
                  r"\s+(?:hain|wale)", ql)
    if m and ("yog" in ql or "gunanphal" in ql):
        _poly = (f"(x - {m.group(1)})(x - {m.group(2)})")
        if ql.rfind("gunanphal") > ql.rfind("yog"):
            return f"find the product of zeroes of {_poly}"
        return f"find the sum of zeroes of {_poly}"
    m = re.search(r"p\(x\)\s*=\s*(.+?)\s+ke\s+(?:zero|shunyak|"
                  r"zeroes)\b", ql)
    if m:
        return f"find the zeroes of {_fix_expr(m.group(1))}"
    m = re.search(r"(.+?)\s+ke\s+zeroes\s+ka\s+(?:yog|jod)\b",
                  ql)
    if m and ("x" in m.group(1) or "^" in m.group(1)):
        return f"find the sum of zeroes of {_fix_expr(m.group(1))}"
    m = re.search(r"(.+?)\s+ke\s+zeroes\s+ka\s+(?:guna|"
                  r"gunanphal)\b", ql)
    if m and ("x" in m.group(1) or "^" in m.group(1)):
        return (f"find the product of zeroes of "
                f"{_fix_expr(m.group(1))}")
    m = re.search(r"(.+?)\s+ko\s*\(([^)]+)\)\s*se\s+bhaag"
                  r"[^0-9]{0,30}?(?:shesh|remainder)", ql)
    if m:
        return (f"find the remainder when "
                f"{_fix_expr(m.group(1))} is divided by "
                f"{m.group(2)}")
    m = re.search(r"(?:limit|lim)\s+x\s*(?:tends\s+to|->|→)\s*"
                  + _N +
                  r"\s*,?\s*(?:of\s+)?(.+?)\s*"
                  r"(?:ki\s+value|batao|kitni|$)",
                  ql)
    if m:
        return (f"limit of {_fix_expr(m.group(2))} as x tends "
                f"to {m.group(1)}")
    m = re.search(r"x,?\s+" + _N + r"\s+ki\s+taraf\s+ja\w+\s+"
                  r"hai\s+to\s+(.+?)\s+ki\s+limit", ql)
    if m:
        return (f"limit of {_fix_expr(m.group(2))} as x tends "
                f"to {m.group(1)}")

    _mwt59 = re.search(r"(?:pehla|pehle)\s+pad\s+" + _N +
                       r"[^0-9]{0,20}?antar\s+" + _N +
                       r"[^0-9]{0,40}?" + _N + r"\s+konsa\s+pad",
                       ql)
    if _mwt59:
        return (f"the first term of an AP is {_mwt59.group(1)} "
                f"and the common difference is "
                f"{_mwt59.group(2)}, which term is "
                f"{_mwt59.group(3)}?")
    # AP common difference from first + nth term, with the
    # nth term named by a Hindi word ordinal ("paanchva pad").
    _mfd59 = re.search(r"(?:pehla|pehle)\s+pad\s+" + _N +
                       r"[^0-9]{0,60}?(?:(\d+)\s*(?:va|wa|th|st|nd|rd)\s+pad|"
                       r"(dusra|teesra|chautha|paanchva|chhatha|"
                       r"saatva|aathva|nauva|dasva)\s+pad)\s+" +
                       _N, ql)
    if _mfd59 and ("common difference" in ql or "antar" in ql):
        _ord = {"dusra": 2, "teesra": 3, "chautha": 4,
                "paanchva": 5, "chhatha": 6, "saatva": 7,
                "aathva": 8, "nauva": 9, "dasva": 10}
        _n59 = int(_mfd59.group(2)) if _mfd59.group(2) \
            else _ord[_mfd59.group(3)]
        _suf = {1: "st", 2: "nd", 3: "rd"}.get(_n59, "th")
        return (f"the first term of an AP is {_mfd59.group(1)} "
                f"and the {_n59}{_suf} term is "
                f"{_mfd59.group(4)}, find the common difference")
    # --- Ages in ratio, proportion, tangent length -----------------
    m = re.search(r"umar\s+ka\s+yog\s+" + _N +
                  r"\s+saal\s+hai\s+aur\s+antar\s+" + _N, ql)
    if m:
        return (f"the sum of two numbers is {m.group(1)} and "
                f"their difference is {m.group(2)}, find the "
                f"larger number")
    m = re.search(r"umar\s+ki\s+" + _N + r"\s+gun\w*\s+hai"
                  r"[^0-9]{0,80}?yog\s+" + _N, ql)
    if m:
        return (f"two numbers are in the ratio {m.group(1)}:1 "
                f"and their sum is {m.group(2)}, find the "
                f"smaller number")
    m = re.search(r"umar\s+ka\s+ratio\s+" + _N + r"\s*:\s*" + _N +
                  r"[^0-9]{0,40}?kul\s+umar\s+" + _N, ql)
    if m:
        return (f"two numbers are in the ratio {m.group(1)}:"
                f"{m.group(2)} and their sum is {m.group(3)}, "
                f"find the smaller number")
    m = re.search(_N + r"\s+(\w+)\s+ki\s+keemat\s+" + _N +
                  r"\s*(?:rs|rupaye)\s+hai\s+to\s+" + _N +
                  r"\s+\1\s+ki\s+keemat", ql)
    if m:
        return (f"{m.group(1)} {m.group(2)} cost {m.group(3)} "
                f"rupees. what is the cost of {m.group(4)} "
                f"{m.group(2)}")
    m = re.search(_N + r"\s+(?:aadmi|mazdoor|log)[^0-9]{0,60}?"
                  + _N + r"\s+din\s*me[^0-9]{0,60}?" + _N +
                  r"\s+(?:aadmi|mazdoor|log)", ql)
    if m:
        return (f"{m.group(1)} men can do a work in "
                f"{m.group(2)} days. in how many days can "
                f"{m.group(3)} men do the same work")
    m = re.search(_N + r"\s*:\s*" + _N + r"\s*=\s*x\s*:\s*"
                  + _N, ql)
    if m:
        return (f"{m.group(1)}/{m.group(2)} = x/{m.group(3)}, "
                f"find x")
    m = re.search(r"x\s*:\s*" + _N + r"\s*=\s*" + _N +
                  r"\s*:\s*" + _N, ql)
    if m:
        return (f"x/{m.group(1)} = {m.group(2)}/{m.group(3)}, "
                f"find x")
    m = re.search(r"(?:rectangle|aayat)\s+ka\s+length\s+" + _N
                  + r"\s+(?:aur|or|and)\s+breadth\s+" + _N, ql)
    if m and ("area" in ql or "kshetrafal" in ql):
        return (f"area of a rectangle with length {m.group(1)} "
                f"and breadth {m.group(2)}")
    if "sparsh rekha" in ql and "lambai" in ql:
        _mk = re.search(r"kendr\s+(?:se|ki)\s+doori\s+" + _N, ql) \
            or re.search(r"kendr\s+se\s+" + _N, ql)
        _mtr2 = re.search(r"trijya\s+" + _N, ql)
        if _mk and _mtr2:
            return (f"length of tangent from a point at a "
                    f"distance of {_mk.group(1)} cm from the "
                    f"centre of a circle of radius "
                    f"{_mtr2.group(1)} cm")

    # ==================================================================
    # Wave 65: trilingual deep training — whole-question
    # translations for the phrasing families the batteries
    # exposed (Roman Hindi + Devanagari). Same contract as
    # Wave 59: every rule emits the canonical English form an
    # existing solver accepts; a rule that does not fully
    # match changes nothing.
    # ==================================================================
    # --- Roman: powers written as words ------------------------------
    m = re.search(r"" + _N + r"\s+ka\s+varg\s+aur\s+" + _N +
                  r"\s+ka\s+ghan\s+jodkar", ql)
    if m:
        return f"{m.group(1)}^2 + {m.group(2)}^3"
    m = re.search(r"" + _N + r"\s+ki\s+(?:ghaat|ghata)\s+" + _N + r"",
                  ql)
    if m:
        return f"{m.group(1)}^{m.group(2)}"
    m = re.search(r"" + _N + r"\s+ka\s+ghan\b", ql)
    if m and ("batao" in ql or "kitna" in ql or "nikalo" in ql):
        return f"{m.group(1)}^3"
    # --- Roman: yog / antar on plain numbers --------------------------
    m = re.search(r"" + _N + r"\s+aur\s+" + _N + r"\s+ka\s+"
                  r"(yog|antar|jod)", ql)
    if m and len(re.findall(r"\d", ql)) <= 8:
        if m.group(3) == "antar":
            return f"{m.group(1)} - {m.group(2)}"
        return f"{m.group(1)} + {m.group(2)}"
    # --- Roman: fraction operations ------------------------------------
    m = re.search(r"bhinn\s+(\d+/\d+)\s+aur\s+(\d+/\d+)\s+"
                  r"(?:ko|ka)\s+(jod|ghata|guna|bhaag)", ql)
    if m:
        op65 = {"jod": "+", "ghata": "-", "guna": "*",
                "bhaag": "/"}[m.group(3)]
        if op65 == "/":
            return f"({m.group(1)}) / ({m.group(2)})"
        return f"{m.group(1)} {op65} {m.group(2)}"
    m = re.search(r"bhinn\s+(\d+/\d+)\s+aur\s+(\d+/\d+)\s+ka\s+"
                  r"(jod|yog)", ql)
    if m:
        return f"{m.group(1)} + {m.group(2)}"
    # --- Roman: percent-of with feesadi --------------------------------
    m = re.search(r"" + _N + r"\s+ka\s+" + _N + r"\s+"
                  r"feesadi", ql)
    if m:
        return f"{m.group(2)}% of {m.group(1)}"
    # --- Roman: discount stories ----------------------------------------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+likh[ai]\s+(?:hai|h|he)\b"
                  r"[^0-9%]{0,40}?" + _N + r"%\s*ki\s*chhu?t",
                  ql)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%, find the selling price")
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+wali\s+"
                  r"[^0-9%]{0,40}?" + _N + r"%\s*(?:ki\s*)?"
                  r"chhu?t", ql)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%, find the selling price")
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+(?:liye|"
                  r"diye)\s+aur[^0-9%]{0,60}?" + _N +
                  r"%\s*wapas", ql)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%, find the selling price")
    # --- Roman: buy/sell at a profit or loss percent --------------------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+me\s+"
                  r"[^0-9%]{0,50}?" + _N + r"%\s*"
                  r"(munafa|munafe|ghata|ghate)\s+par\s+bech",
                  ql)
    if m:
        kind65 = "profit" if m.group(3).startswith("munaf") \
            else "loss"
        return (f"cost price is {m.group(1)}, {kind65} is "
                f"{m.group(2)}%, find the selling price")
    # --- Roman: profit percent from buy and sell prices ------------------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+ki\s+cheez"
                  r"\s+" + _N + r"\s*(?:rs|rupaye)\s+me\s+"
                  r"bechi[^0-9]{0,30}?%?\s*(munafa|munafaa)", ql)
    if m:
        return (f"an article is bought for {m.group(1)} rs "
                f"and sold for {m.group(2)} rs. find the "
                f"profit percent")
    # --- Roman: sold at a profit/loss percent, cost price asked ----------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+me\s+bechne"
                  r"\s+par\s+" + _N + r"%\s*(?:ka\s*)?"
                  r"(munafa|ghata)\s+hua", ql)
    if m:
        kind65 = "profit" if m.group(3) == "munafa" else "loss"
        return (f"an article is sold for {m.group(1)} rs at "
                f"a {kind65} of {m.group(2)}%. find the cost "
                f"price")
    # --- Roman: simple-interest rate from the interest -------------------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+me\s+" +
                  _N + r"\s*saal\s+me\s+" + _N + r"\s*"
                  r"(?:rs|rupaye)\s+byaa?j\s+mila", ql)
    if m and "dar" in ql:
        return (f"simple interest on {m.group(1)} for "
                f"{m.group(2)} years is {m.group(3)}. find "
                f"the rate")
    # --- Roman: speed with raftaar, either number order -------------------
    if "raftaar" in ql or "raftar" in ql:
        _d = re.search(r"" + _N + r"\s*km\b", ql)
        _h = re.search(r"" + _N + r"\s*ghante?\b", ql)
        if _d and _h:
            return (f"a train travels {_d.group(1)} km in "
                    f"{_h.group(1)} hours, find its speed")
    # --- Roman: distance to cover, "jana h" -------------------------------
    m = re.search(r"" + _N + r"\s*km\s+jana\s+(?:hai|h|he)"
                  r"\b[^0-9]{0,40}?" + _N + r"\s*km/h", ql)
    if m and ("time" in ql or "samay" in ql or "lagega" in ql):
        return (f"how long does a train take to travel "
                f"{m.group(1)} km at {m.group(2)} km/h")
    # --- Roman: rectangle perimeter with lambai/chaudai -------------------
    m = re.search(r"(?:rectangle|aayat)\s+ki\s+lambai\s+" +
                  _N + r"[^0-9]{0,20}?chaudai\s+" + _N + r"",
                  ql)
    if m and "parimap" in ql:
        return (f"find the perimeter of a rectangle with "
                f"length {m.group(1)} and breadth "
                f"{m.group(2)}")
    # --- Roman: field area -------------------------------------------------
    m = re.search(r"khet\s+" + _N + r"\s*m\s+lamba\s+aur\s+"
                  r"" + _N + r"\s*m\s+chauda", ql)
    if m and "kshetrafal" in ql:
        return (f"area of a rectangle with length "
                f"{m.group(1)} and breadth {m.group(2)}")
    # --- Roman: cuboid volume (tank) ----------------------------------------
    m = re.search(r"length\s+" + _N + r"[^0-9]{0,16}?"
                  r"breadth\s+" + _N + r"[^0-9]{0,16}?"
                  r"height\s+" + _N + r"", ql)
    if m and ("volume" in ql or "paani" in ql):
        return (f"volume of a cuboid with length "
                f"{m.group(1)}, breadth {m.group(2)} and "
                f"height {m.group(3)}")
    # --- Roman: surface areas ------------------------------------------------
    m = re.search(r"(?:ghan|ghhan)\s+ki\s+bhuja\s+" + _N +
                  r"", ql)
    if m and "prishtiya kshetrafal" in ql:
        return (f"find the total surface area of a cube "
                f"with side {m.group(1)}")
    m = re.search(r"gole\s+ki\s+trijya\s+" + _N + r"", ql)
    if m and "prishtiya kshetrafal" in ql:
        return (f"find the total surface area of a sphere "
                f"of radius {m.group(1)}")
    # --- Roman: midpoint -------------------------------------------------------
    m = re.search(r"bindu\w*\s*\(\s*(-?" + _N + r")\s*,\s*"
                  r"(-?" + _N + r")\s*\)\s*aur\s*\(\s*(-?" +
                  _N + r")\s*,\s*(-?" + _N + r")\s*\)\s*ka\s+"
                  r"madhy\w*\s*bindu", ql)
    if m:
        return (f"find the midpoint of ({m.group(1)}, "
                f"{m.group(3)}) and ({m.group(5)}, "
                f"{m.group(7)})")
    # --- Roman: zeroes of a polynomial -----------------------------------------
    m = re.search(r"bahupad\s+(.+?)\s*ke\s+shunyako\s+ka\s+"
                  r"(yog|gunanfal|gunanphal)", ql)
    if m:
        poly65 = re.sub(r"([a-z])(\d)", r"\1^\2",
                        m.group(1).replace("^", ""))
        what65 = "sum" if m.group(2) == "yog" else "product"
        return (f"find the {what65} of the zeroes of the "
                f"polynomial {poly65}")
    # --- Roman: linear stories --------------------------------------------------
    m = re.search(r"sankhya\s+ke\s+" + _N + r"\s+gun[ae]\s+me"
                  r"\s+se\s+" + _N + r"\s+ghatn[ae]\s+par\s+"
                  r"" + _N + r"\s+milta", ql)
    if m:
        return (f"{m.group(1)} times a number minus "
                f"{m.group(2)} is {m.group(3)}")
    m = re.search(r"ek\s+sankhya\s+ka\s+" + _N + r"\s+guna"
                  r"\s+" + _N + r"\s+hai", ql)
    if m:
        return f"{m.group(1)} times a number is {m.group(2)}"
    # --- Roman: ratio parts with a sum -------------------------------------------
    m = re.search(r"anupaa?t\s+" + _N + r"\s*:\s*" + _N +
                  r"[^0-9]{0,30}?yog\s+" + _N + r"", ql)
    if m and ("chhoti" in ql or "badi" in ql):
        which65 = "smaller" if "chhoti" in ql else "larger"
        return (f"two numbers are in the ratio {m.group(1)}:"
                f"{m.group(2)} and their sum is {m.group(3)}. "
                f"find the {which65} number")
    # --- Roman: work together -----------------------------------------------------
    m = re.search(r"(\w+)\s+" + _N + r"\s+din\s+me\s+karta"
                  r"\s+hai,?\s+(\w+)\s+" + _N + r"\s+din"
                  r"\s+me", ql)
    if m and "dono milkar" in ql:
        return (f"a can finish a job in {m.group(2)} days "
                f"and b in {m.group(4)} days. in how many "
                f"days can they finish it together?")
    # --- Roman: taps ----------------------------------------------------------------
    m = re.search(r"nali\s+tanki\s+ko\s+" + _N + r"\s+"
                  r"ghante\s+me\s+bharti\s+hai,?\s+" + _N +
                  r"\s+naliyan", ql)
    if m:
        return (f"one tap fills a tank in {m.group(1)} "
                f"hours. how long will {m.group(2)} such "
                f"taps take?")
    # --- Roman: train and pole ---------------------------------------------------------
    m = re.search(r"train\s+ki\s+lambai\s+" + _N + r"\s*m"
                  r"\s+hai[^0-9]{0,40}?" + _N + r"\s*km/h"
                  r"\s+se\s+ek\s+khambhe", ql)
    if m:
        return (f"a train {m.group(1)} m long runs at "
                f"{m.group(2)} km/h. time to cross a pole?")
    # --- Roman: population increase ------------------------------------------------------
    m = re.search(r"jansankhya\s+" + _N + r"\s+hai[^0-9%]"
                  r"{0,20}?" + _N + r"%\s+badh\s+gayi", ql)
    if m:
        return (f"the population is {m.group(1)}. it "
                f"increases by {m.group(2)}%. find the new "
                f"population")
    # --- Roman: remainder ------------------------------------------------------------------
    m = re.search(r"" + _N + r"\s+ko\s+" + _N + r"\s+se"
                  r"\s+bhaag\s+dene\s+par\s+shesh", ql)
    if m:
        return (f"find the remainder when {m.group(1)} is "
                f"divided by {m.group(2)}")
    # --- Roman: prime counting / smallest prime ----------------------------------------------
    m = re.search(r"" + _N + r"\s+aur\s+" + _N + r"\s+ke"
                  r"\s+beech\s+kitni\s+abhaajya", ql)
    if m:
        return (f"how many prime numbers are there between "
                f"{m.group(1)} and {m.group(2)}?")
    if "sabse chhoti abhaajya sankhya" in ql:
        return "what is the smallest prime number?"
    # --- Roman: sets, no total (union) and with total (neither) --------------------------------
    m = re.search(r"" + _N + r"\s+(?:bacche|students?)\s+"
                  r"cricket\s+khelte[^0-9]{0,30}?" + _N +
                  r"\s+football[^0-9]{0,30}?" + _N + r""
                  r"\s+dono", ql)
    if m and "kam se kam ek" in ql:
        return (f"{m.group(1)} play cricket, {m.group(2)} "
                f"play football and {m.group(3)} play both. "
                f"how many play at least one game?")
    m = re.search(r"" + _N + r"\s+me\s+se\s+" + _N + r""
                  r"\s+ko\s+chai\s+pasand[^0-9]{0,30}?" + _N +
                  r"\s+ko\s+coffee[^0-9]{0,30}?" + _N + r""
                  r"\s+ko\s+dono", ql)
    if m and "kuch nahi" in ql:
        return (f"in a group of {m.group(1)} people, "
                f"{m.group(2)} like tea, {m.group(3)} like "
                f"coffee and {m.group(4)} like both. how "
                f"many like neither?")
    # Structural twin of the chai/coffee rule above: the
    # two activity words are matched as bare words because
    # the spelling fold rewrites them unpredictably
    # (gana -> guna, naach -> unchai).
    m = re.search(r"" + _N + r"\s+logo\s+me\s+se\s+" + _N +
                  r"\s+ko\s+\w+\s+pasand[^0-9]{0,30}?" +
                  _N + r"\s+ko\s+\w+[^0-9]{0,30}?" + _N +
                  r"\s+ko\s+dono", ql)
    if m and "kuch nahi" in ql:
        return (f"in a group of {m.group(1)} people, "
                f"{m.group(2)} like music, {m.group(3)} like "
                f"dance and {m.group(4)} like both. how "
                f"many like neither?")
    # --- Roman: probability -----------------------------------------------------------------------
    m = re.search(r"bag\s+me\s+" + _N + r"\s+red\s+balls?"
                  r"\s+aur\s+" + _N + r"\s+blue\s+balls?",
                  ql)
    if m and "probability" in ql:
        return (f"a bag contains {m.group(1)} red balls "
                f"and {m.group(2)} blue balls. find the "
                f"probability of getting a red ball")
    m = re.search(r"bag\s+me\s+" + _N + r"\s+gende\s+hain"
                  r"\s+jinme\s+" + _N + r"\s+kaali\s+hain",
                  ql)
    if m:
        return (f"a bag has {m.group(1)} balls, "
                f"{m.group(2)} of which are black. find the "
                f"probability of getting a black ball")
    m = re.search(r"sika\s+" + _N + r"\s+baar\s+uchala",
                  ql)
    if m and "chit" in ql:
        return (f"a coin is tossed {m.group(1)} times, "
                f"find the probability of getting all heads")
    if re.search(r"do\s+sikk\w+", ql) and "chit na" in ql:
        return ("two coins are tossed, find the probability "
                "of getting no heads")
    m = re.search(r"52\s+patto[^0-9]{0,40}?laal\s+raja", ql)
    if m:
        return ("find the probability of getting a red "
                "king from a pack of 52 cards")
    m = re.search(r"52\s+patto[^0-9]{0,40}?raja\s+nikalne",
                  ql)
    if m:
        return ("find the probability of getting a king "
                "from a pack of 52 cards")
    m = re.search(r"52\s+patto[^0-9]{0,40}?kaala\s+patta",
                  ql)
    if m:
        return ("find the probability of getting a black "
                "card from a pack of 52 cards")
    # --- Roman: ladder / slant / height-angle / pythagoras ----------------------------------------------
    m = re.search(r"sidhi\s+" + _N + r"\s*m\s+lamb[ai][^0-9]"
                  r"{0,60}?" + _N + r"\s*m\s+unchai", ql)
    if m and "paon" in ql:
        return (f"a ladder {m.group(1)} m long leans "
                f"against a wall reaching a height of "
                f"{m.group(2)} m. how far is its foot from "
                f"the wall?")
    m = re.search(r"shanku\s+ki\s+trijya\s+" + _N + r""
                  r"[^0-9]{0,20}?unchai\s+" + _N + r"", ql)
    if m and "tiryak" in ql:
        return (f"find the slant height of a cone with "
                f"radius {m.group(1)} cm and height "
                f"{m.group(2)} cm")
    m = re.search(r"minaar\s+ki\s+unchai\s+" + _N + r"\s*m"
                  r"[^0-9]{0,30}?parchhai\s+" + _N + r"\s*m",
                  ql)
    if m and "unnayan" in ql:
        return (f"a tower {m.group(1)} m high casts a "
                f"shadow {m.group(2)} m long. angle of "
                f"elevation of the sun?")
    m = re.search(r"right\s+triangle\s+ki\s+do\s+bhuja\s+" +
                  _N + r"\s+aur\s+" + _N + r"", ql)
    if m and "karn" in ql:
        return (f"the legs of a right triangle are "
                f"{m.group(1)} and {m.group(2)}. find the "
                f"hypotenuse")
    m = re.search(r"sin\s+a\s*=\s*(\d+/\d+)\s+hai\s+to\s+"
                  r"cos\s+a", ql)
    if m:
        return f"if sin a = {m.group(1)}, find cos a"
    # --- Roman: fraction of a number / decimal to fraction --------------------------------------------
    m = re.search(r"(\d+/\d+)\s+of\s+a\s+number\s+is\s+" +
                  _N + r"", ql)
    if m:
        return f"{m.group(1)} of a number is {m.group(2)}, find the number"
    m = re.search(r"" + _N + r"\s+ko\s+bhinn\s+me\s+badlo",
                  ql)
    if m and "." in m.group(1):
        return (f"express {m.group(1)} as a fraction in "
                f"lowest terms")
    # --- Roman: unit facts and conversions ---------------------------------------------------------------
    if "ek ghante" in ql and "kitne minute" in ql:
        return "how many minutes are there in an hour?"
    if "ek hafte" in ql and "kitne ghante" in ql:
        return "how many hours are there in a week?"
    if "ek ghante" in ql and "kitne second" in ql:
        return "how many seconds are there in an hour?"
    m = re.search(r"" + _N + r"\s+darjan\s+\w+\s+matlab\s+"
                  r"kitne", ql)
    if m:
        return (f"how many pens are there in {m.group(1)} "
                f"dozen?")
    m = re.search(r"" + _N + r"\s+gram[^0-9]{0,20}?" + _N +
                  r"\s+pudi", ql)
    if m and "kg" in ql:
        tot65 = float(m.group(1)) * float(m.group(2))
        tot65 = int(tot65) if tot65 == int(tot65) else tot65
        return f"convert {tot65} grams to kilograms"
    m = re.search(r"" + _N + r"\s+gram[^0-9]{0,16}?kilo\s+"
                  r"me\s+kitna", ql)
    if m:
        return f"convert {m.group(1)} grams to kilograms"
    m = re.search(r"raftaar\s+" + _N + r"\s*km/h[^0-9]{0,30}"
                  r"?meter\s+per\s+second", ql)
    if m:
        return f"{m.group(1)} km/h in m/s"
    # --- Roman: one-line money / measure stories ---------------------------------------------------------------
    m = re.search(r"" + _N + r"\s+bacche[^0-9]{0,30}?"
                  r"har\s+bacche\s+se\s+" + _N + r"\s*"
                  r"(?:rs|rupaye)", ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"" + _N + r"\s+kilo\s+\w+\s+" + _N +
                  r"\s*(?:rs|rupaye)\s+kilo\s+ke\s+hisaab",
                  ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"ek\s+litr\s+doodh\s+" + _N + r"\s*"
                  r"(?:rs|rupaye)\s+ka\s+hai,?\s+" + _N +
                  r"\s+litr", ql)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"" + _N + r"\s+pankhe[^0-9]{0,30}?har"
                  r"\s+pankha\s+" + _N + r"\s+watt", ql)
    if m and "kul" in ql:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"ka\s+wazan\s+" + _N + r"\s*kg\s+hai"
                  r"\s+aur\s+\w+\s+ka\s+" + _N + r"\s*kg",
                  ql)
    if m:
        return f"{m.group(1)} + {m.group(2)}"
    m = re.search(r"kul\s+" + _N + r"\s*(?:rs|rupaye)\s+"
                  r"kharch", ql)
    if m and ("per aadmi" in ql or "har bacche par" in ql
              or "har ek par" in ql or "per baccha" in ql):
        _ppl = re.search(r"" + _N + r"\s+(?:dost|aadmi|log|logo|"
                         r"bacche|students?)", ql)
        if _ppl:
            return f"{m.group(1)} / {_ppl.group(1)}"
    m = re.search(r"auto\s+(?:wala\s+)?" + _N + r"\s*km\s+"
                  r"ke\s+" + _N + r"\s*(?:rs|rupaye)\s+leta"
                  r"[^0-9]{0,30}?per\s+km", ql)
    if m:
        return f"{m.group(2)} / {m.group(1)}"
    m = re.search(r"do\s+sankhyaon\s+ka\s+guna\s+" + _N +
                  r"\s+hai\s+aur\s+ek\s+sankhya\s+" + _N +
                  r"\s+hai", ql)
    if m:
        return f"{m.group(1)} / {m.group(2)}"
    m = re.search(r"" + _N + r"\s+over\s+me\s+" + _N +
                  r"\s+run[\s\S]{0,40}?per\s+over\s+ausat",
                  ql)
    if m:
        return f"{m.group(2)} / {m.group(1)}"
    m = re.search(r"" + _N + r"\s+(?:bje|byaj)\s+khulta\s+"
                  r"hai\s+aur\s+(?:\w+\s+)?" + _N +
                  r"\s+(?:bje|byaj)\s+band", ql)
    if m:
        _a = float(m.group(1))
        _b = float(m.group(2))
        if _b <= _a:
            _b += 12
        _b = int(_b) if _b == int(_b) else _b
        _a = int(_a) if _a == int(_a) else _a
        return f"{_b} - {_a}"
    m = re.search(r"umar\s+" + _N + r"\s+saal[^0-9]{0,40}?"
                  r"meri\s+(?:umar\s+)?" + _N, ql)
    if m and "kitni guna" in ql:
        return f"{m.group(1)} / {m.group(2)}"
    # --- Roman: clock-to-clock journey speed ------------------------------------------------------------
    m = None
    if "chali" in ql and ("pahunchi" in ql or "pahuchi" in ql) \
            and ("speed" in ql or "raftaar" in ql
                 or "chaal" in ql):
        _st = re.search(r"(shaam|subah|raat|dopahar)\s+" + _N +
                        r"\s+(?:bje|byaj)\s+chali", ql)
        _en = re.search(r"(shaam|subah|raat|dopahar)\s+" + _N +
                        r"\s+(?:bje|byaj)\s+(?:pahunchi|pahuchi)",
                        ql)
        _kd = re.search(r"" + _N + r"\s*km\b", ql)
        if _st and _en and _kd:
            m = (_kd.group(1), _st.group(1), _st.group(2),
                 _en.group(1), _en.group(2))
    if m:
        def _hr65(period, hh):
            hh = float(hh)
            if period in ("shaam", "raat") and hh < 12:
                hh += 12
            return hh
        _dur = _hr65(m[3], m[4]) - _hr65(m[1], m[2])
        if _dur <= 0:
            _dur += 24
        _dur = int(_dur) if _dur == int(_dur) else _dur
        return (f"a train travels {m[0]} km in "
                f"{_dur} hours, find its speed")
    # --- Roman: boys/girls percentage --------------------------------------
    m = re.search(r"" + _N + r"\s+ladke\s+aur\s+" + _N +
                  r"\s+ladkiya", ql)
    if m and "pratishat" in ql:
        _a65, _b65 = float(m.group(1)), float(m.group(2))
        return f"{m.group(1)} / {_a65 + _b65:g} * 100"
    # --- Roman: speed conversion, number before raftaar ---------------------
    m = re.search(r"" + _N + r"\s*km/h\s+ki\s+raftaar", ql)
    if m and "meter per second" in ql:
        return f"{m.group(1)} km/h in m/s"
    # --- Roman: dozen of a named thing ----------------------------------------
    m = re.search(r"" + _N + r"\s+darjan\s+(\w+)", ql)
    if m and "kitne" in ql and "matlab" not in ql:
        return (f"how many {m.group(2)} are there in "
                f"{m.group(1)} dozen?")
    # --- Roman: three consecutive numbers, middle asked -------------------------
    m = re.search(r"(?:teen|3|three)\s+lagatar\s+sankhyaon"
                  r"\s+ka\s+yog\s+" + _N, ql)
    if m and "beech wali" in ql:
        return (f"the sum of three consecutive numbers is "
                f"{m.group(1)}. find the middle number")
    # --- Roman: a fraction-share (hissa) of a number ------------------------------
    m = re.search(r"sankhya\s+ka\s+(\d+/\d+)\s+hissa\s+" +
                  _N + r"\s+hai", ql)
    if m:
        return (f"{m.group(1)} of a number is {m.group(2)}, "
                f"find the number")
    # --- Roman: divide money in a ratio (baanto) -------------------------------------
    m = re.search(r"" + _N + r"\s*(?:rs|rupaye)\s+ko\s+" +
                  _N + r"\s*:\s*" + _N + r"\s+me\s+(?:baanto|banto)",
                  ql)
    if m and ("chhote" in ql or "bade" in ql):
        which65 = "smaller" if "chhote" in ql else "larger"
        return (f"divide {m.group(1)} in the ratio "
                f"{m.group(2)}:{m.group(3)}, find the "
                f"{which65} share")
    # --- Roman: trig value, chat form ---------------------------------------------------
    m = re.search(r"\b(sin|cos|tan)\s+" + _N + r"\s+ki\s+"
                  r"value", ql)
    if m:
        return (f"what is the value of {m.group(1)} "
                f"{m.group(2)} degrees?")
    # --- Roman: rectangle area from two bare dimensions --------------------------------------
    # Structural on purpose: the dimension WORDS may carry
    # held-out misspellings, so only the shape words
    # (rectangle + aur + area) and the two numbers are used.
    m = re.search(r"(?:rectangle|aayat)\s+ki\s+\w+\s+" + _N +
                  r"\s*(?:cm|m)?\s+aur\s+\w+\s+" + _N, ql)
    if m and "area" in ql:
        return (f"area of a rectangle with length "
                f"{m.group(1)} and breadth {m.group(2)}")
    # --- Roman: fencing cost ----------------------------------------------------------------------
    m = re.search(r"lambai\s+" + _N + r"\s*(?:m|meter)\s+"
                  r"(?:aur\s+)?chaudai\s+" + _N +
                  r"\s*(?:m|meter)"
                  r"[^0-9]{0,60}?baad\s+lagane\s+ka\s+kharcha"
                  r"\s+" + _N + r"\s*(?:rs|rupaye)\s+per\s+"
                  r"meter", ql)
    if m:
        return (f"a rectangular garden is {m.group(1)} m "
                f"long and {m.group(2)} m wide, find cost of "
                f"fencing at {m.group(3)} rs per metre")

    # --- Devanagari: speed / distance / train conditional ----------------
    if any(w in q for w in ("किलोमीटर", "रेलगाड़ी", "ट्रेन",
                            "km")):
        _cond = re.search(
            r"" + _N + r"\s*(?:किलोमीटर|km)(?:\s+की\s+दूरी)?"
            r"[^0-9]{0,80}?चाल\s+" + _N + r"\s*(?:किलोमीटर"
            r"\s+प्रति\s+घंट[ाे]|km/h)\s+अधिक\s+होती[^0-9]"
            r"{0,40}?" + _N + r"\s*घंट[ाे]\s+कम", q)
        if _cond:
            return (f"a train travels {_cond.group(1)} km. "
                    f"if its speed is increased by "
                    f"{_cond.group(2)} km/h, it takes "
                    f"{_cond.group(3)} hour less. find its "
                    f"original speed")
        _tm = re.search(r"" + _N + r"\s*घंट[ाे]", q)
        _sm = re.search(r"चाल\s+" + _N + r"\s*(?:किलोमीटर"
                        r"\s+प्रति\s+घंट[ाे]|km/h)", q) or \
            re.search(r"" + _N + r"\s*किलोमीटर\s+प्रति\s+"
                      r"घंट[ाे]\s+की\s+चाल", q)
        # A stated speed + a time + a distance ask is the
        # DISTANCE family; it must be claimed before the
        # plain speed rule can misread the speed as a
        # distance.
        if _sm and _tm and ("दूरी" in q or "रास्ता" in q):
            return (f"a train travels at {_sm.group(1)} "
                    f"km/h for {_tm.group(1)} hours, find "
                    f"the distance")
        _dm = re.search(r"" + _N + r"\s*किलोमीटर"
                        r"(?!\s+प्रति)", q) or re.search(
            r"" + _N + r"\s*km\b", q)
        if _dm and _tm and ("चाल" in q or "गति" in q
                            or "रफ़्तार" in q or "speed" in ql
                            or ("दूरी" in q and "तय" in q)) \
                and "यदि" not in q and "अधिक" not in q:
            return (f"a train travels {_dm.group(1)} km in "
                    f"{_tm.group(1)} hours, find its speed")
    # --- Devanagari: shadow and angle of elevation -------------------------
    _sh = re.search(r"छाया\s+" + _N + r"\s*(?:मीटर|m)\b", q)
    _el = re.search(r"उन्नयन\s+कोण\s+" + _N + r"\s*°", q)
    if _sh and _el and "ऊँचाई" in q:
        return (f"a tree casts a shadow {_sh.group(1)} m "
                f"long and the angle of elevation of the sun "
                f"is {_el.group(1)} degrees. find the height "
                f"of the tree")
    # --- Devanagari: cricket run rate -----------------------------------
    _ck = re.search(r"" + _N + r"\s+रन\s+" + _N +
                    r"\s+ओवर\s+में\s+बनाए", q)
    if _ck and "औसत" in q:
        return f"{_ck.group(1)} / {_ck.group(2)}"
    # --- Devanagari: discount ----------------------------------------------
    m = re.search(r"अंकित\s+मूल्य\s+" + _N + r"\s*रुपये"
                  r"[^0-9%]{0,30}?" + _N + r"%\s*(?:की\s+)?"
                  r"छूट", q) or re.search(
        r"" + _N + r"\s*रुपय[ेा]\s+क[ीाे]\s+[^0-9%]{0,30}?"
        r"" + _N + r"%\s*(?:की\s+)?छूट", q) or re.search(
        r"" + _N + r"\s*रुपय[ेा]\s+क[ाी]\s+है[^0-9%]{0,30}?"
        r"" + _N + r"%\s*छूट", q)
    if m:
        return (f"marked price is {m.group(1)}, discount of "
                f"{m.group(2)}%, find the selling price")
    # --- Devanagari: profit / loss percent on a cost price -------------------
    m = re.search(r"" + _N + r"\s*रुपये\s+में[^0-9%]{0,40}?"
                  r"" + _N + r"%\s*(लाभ|हानि)\s+पर\s+बेच",
                  q) or re.search(
        r"" + _N + r"\s*रुपये\s+का\s+सामान[^0-9%]{0,30}?"
        r"" + _N + r"%\s*(लाभ|हानि)\s+पर\s+बेच", q) or \
        re.search(r"वस्तु\s+" + _N + r"\s*रुपये\s+में\s+"
                  r"खरीदी[^0-9%]{0,30}?" + _N + r"%\s*"
                  r"(लाभ|हानि)\s+पर\s+बेची", q)
    if m:
        kind65 = "profit" if m.group(3) == "लाभ" else "loss"
        return (f"cost price is {m.group(1)}, {kind65} is "
                f"{m.group(2)}%, find the selling price")
    # --- Devanagari: sold at a profit percent, cost price asked ----------------
    m = re.search(r"" + _N + r"\s*रुपये\s+में\s+बेचने\s+पर"
                  r"\s+" + _N + r"%\s*(लाभ|हानि)\s+हुआ[^0-9]"
                  r"{0,20}?क्रय\s+मूल्य", q)
    if m:
        kind65 = "profit" if m.group(3) == "लाभ" else "loss"
        return (f"an article is sold for {m.group(1)} rs at "
                f"a {kind65} of {m.group(2)}%. find the cost "
                f"price")
    # --- Devanagari: compound interest --------------------------------------------
    m = re.search(r"" + _N + r"\s*रुपये\s+का\s+" + _N +
                  r"%\s*वार्षिक\s+दर\s+से\s+" + _N + r"\s*"
                  r"वर्ष\s+का\s+चक्रवृद्धि\s+ब्याज", q)
    if m:
        return (f"compound interest on {m.group(1)} at "
                f"{m.group(2)}% for {m.group(3)} years")
    # --- Devanagari: length + breadth shapes ------------------------------------------
    if "ऊँचाई" not in q and "गहराई" not in q \
            and "आयतन" not in q:
        m = re.search(r"(?:लंबाई|लम्बाई)\s+" + _N + r"[^0-9]{0,20}?"
                      r"चौड़ाई\s+" + _N + r"", q)
        if m:
            if "परिमाप" in q or "बाड़" in q:
                return (f"find the perimeter of a rectangle "
                        f"with length {m.group(1)} and "
                        f"breadth {m.group(2)}")
            return (f"area of a rectangle with length "
                    f"{m.group(1)} and breadth {m.group(2)}")
    m = re.search(r"" + _N + r"\s*मीटर\s+लंब[ीा]?[^0-9]"
                  r"{0,20}?" + _N + r"\s*मीटर\s+चौड़[ीा]?",
                  q)
    if m:
        if "परिमाप" in q:
            return (f"find the perimeter of a rectangle "
                    f"with length {m.group(1)} and breadth "
                    f"{m.group(2)}")
        return (f"area of a rectangle with length "
                f"{m.group(1)} and breadth {m.group(2)}")
    # --- Devanagari: cuboid volume ----------------------------------------------------------
    m = re.search(r"(?:लंबाई|लम्बाई)\s+" + _N + r"[^0-9]{0,16}?चौड़ाई"
                  r"\s+" + _N + r"[^0-9]{0,16}?(?:गहराई|"
                  r"ऊँचाई)\s+" + _N + r"", q)
    if m and "आयतन" in q:
        return (f"volume of a cuboid with length "
                f"{m.group(1)}, breadth {m.group(2)} and "
                f"height {m.group(3)}")
    # --- Devanagari: cube volume ----------------------------------------------------------------
    m = re.search(r"घन\s+की\s+भुजा\s+" + _N + r"", q)
    if m and "आयतन" in q:
        return f"volume of a cube with side {m.group(1)}"
    # --- Devanagari: circumference -----------------------------------------------------------------
    m = re.search(r"त्रिज्या\s+" + _N + r"", q)
    if m and "परिधि" in q:
        return (f"circumference of a circle with radius "
                f"{m.group(1)}")
    # --- Devanagari: trapezium ------------------------------------------------------------------------
    m = re.search(r"(?:समांतर|समान्तर)\s+भुजाएँ\s+" + _N +
                  r"\s*(?:cm|m)?\s+और\s+" + _N +
                  r"\s*(?:cm|m)?[^0-9]{0,20}?ऊँचाई\s+" +
                  _N + r"", q)
    if m and "समलंब" in q:
        return (f"area of a trapezium with parallel sides "
                f"{m.group(1)} and {m.group(2)} and height "
                f"{m.group(3)}")
    # --- Devanagari: mean of a comma list ------------------------------------------------------------------
    if "औसत" in q or ("माध्य" in q and "माध्यक" not in q
                      and "माध्यिका" not in q):
        _lst = re.search(r"(\d+(?:\s*,\s*\d+){2,}(?:\s*और\s*"
                         r"\d+)?)", q)
        if _lst:
            nums65 = re.findall(r"\d+", _lst.group(1))
            return "mean of " + ", ".join(nums65)
    # --- Devanagari: median / range of a data list --------------------------------------------------------------
    _lst = re.search(r"(\d+(?:\s*,\s*\d+){2,}(?:\s*और\s*\d+)?)",
                     q)
    if _lst and "माध्यक" in q:
        nums65 = re.findall(r"\d+", _lst.group(1))
        return "find the median of " + ", ".join(nums65)
    if _lst and "परिसर" in q:
        nums65 = re.findall(r"\d+", _lst.group(1))
        return "find the range of " + ", ".join(nums65)
    # --- Devanagari: sum and difference pair ------------------------------------------------------------------------------
    m = re.search(r"योग\s+" + _N + r"(?:\s*वर्ष)?\s+और\s+"
                  r"अंतर\s+" + _N + r"", q)
    if m and ("संख्याओं" in q or "आयु" in q):
        return (f"sum is {m.group(1)} and difference is "
                f"{m.group(2)}")
    # --- Devanagari: fraction operations ---------------------------------------------------------------------------------------
    m = re.search(r"भिन्न\s+(\d+/\d+)\s+और\s+(\d+/\d+)\s+का"
                  r"\s+(योग|अंतर|गुणनफल|भागफल)", q)
    if m:
        op65 = {"योग": "+", "अंतर": "-", "गुणनफल": "*",
                "भागफल": "/"}[m.group(3)]
        if op65 == "/":
            return f"({m.group(1)}) / ({m.group(2)})"
        return f"{m.group(1)} {op65} {m.group(2)}"
    m = re.search(r"भिन्न\s+(\d+/\d+)\s+में\s+से\s+(\d+/\d+)"
                  r"\s+घटान", q)
    if m:
        return f"{m.group(1)} - {m.group(2)}"
    # --- Devanagari: trig values --------------------------------------------------------------------------------------------------
    m = re.search(r"(sin|cos|tan)\s+" + _N + r"°?\s*का\s+"
                  r"मान", q)
    if m:
        return (f"what is the value of {m.group(1)} "
                f"{m.group(2)} degrees?")
    # --- Devanagari: midpoint --------------------------------------------------------------------------------------------------------
    m = re.search(r"बिंदुओं\s*\(\s*(-?" + _N + r")\s*,\s*"
                  r"(-?" + _N + r")\s*\)\s*और\s*\(\s*(-?" +
                  _N + r")\s*,\s*(-?" + _N + r")\s*\)\s*का"
                  r"\s+मध्य\s*बिंदु", q)
    if m:
        return (f"find the midpoint of ({m.group(1)}, "
                f"{m.group(3)}) and ({m.group(5)}, "
                f"{m.group(7)})")
    # --- Devanagari: zeroes of a polynomial --------------------------------------------------------------------------------------------
    m = re.search(r"बहुपद\s+(.+?)\s*के\s+शून्यकों\s+का\s+"
                  r"(योग|गुणनफल)", q)
    if m:
        what65 = "sum" if m.group(2) == "योग" else "product"
        return (f"find the {what65} of the zeroes of the "
                f"polynomial {m.group(1).strip()}")
    # --- Devanagari: primes between -----------------------------------------------------------------------------------------------------
    m = re.search(r"" + _N + r"\s+और\s+" + _N + r"\s+के"
                  r"\s+बीच\s+कितनी\s+अभाज्य", q)
    if m:
        return (f"how many prime numbers are there between "
                f"{m.group(1)} and {m.group(2)}?")
    # --- Devanagari: percent of marks ---------------------------------------------------------------------------------------------------------
    m = re.search(r"" + _N + r"\s+में\s+से\s+" + _N +
                  r"\s+अंक\s+मिले", q)
    if m and "प्रतिशत" in q:
        return (f"a student scored {m.group(2)} out of "
                f"{m.group(1)}. find the percentage of marks")
    # --- Devanagari: population increase -------------------------------------------------------------------------------------------------------------
    m = re.search(r"जनसंख्या\s+" + _N + r"[^0-9%]{0,30}?"
                  r"" + _N + r"%\s*की\s*वृद्धि", q)
    if m:
        return f"{m.group(1)} increased by {m.group(2)}%"
    # --- Devanagari: work and taps ----------------------------------------------------------------------------------------------------------------
    m = re.search(r"काम\s+" + _N + r"\s+दिन\s+में[^0-9]"
                  r"{0,40}?" + _N + r"\s+मज़दूर", q)
    if m:
        return (f"one man can do a work in {m.group(1)} "
                f"days. how many days will {m.group(2)} men "
                f"take?")
    m = re.search(r"नल\s+टंकी\s+को\s+" + _N + r"\s+घंटे"
                  r"\s+में\s+भरता\s+है[^0-9]{0,20}?" + _N +
                  r"\s+(?:ऐसे\s+ही\s+)?नल", q)
    if m:
        return (f"one tap fills a tank in {m.group(1)} "
                f"hours. how long will {m.group(2)} such "
                f"taps take?")
    # --- Devanagari: bells together (LCM) --------------------------------------------------------------------------------------------------------------
    m = re.search(r"क्रमशः\s+([0-9,\sऔर]+?)\s*सेकंड\s+के\s+"
                  r"अंतराल", q)
    if m and "एक साथ" in q:
        nums65 = re.findall(r"\d+", m.group(1))
        if len(nums65) >= 3:
            return "find the lcm of " + ", ".join(nums65)
    # --- Devanagari: ratio share ----------------------------------------------------------------------------------------------------------------------------
    m = re.search(r"" + _N + r"\s*रुपये\s+को\s+" + _N +
                  r"\s*:\s*" + _N + r"\s+के\s+अनुपात\s+में",
                  q)
    if m:
        which65 = "smaller" if "छोटे भाग" in q else "larger"
        return (f"divide {m.group(1)} in the ratio "
                f"{m.group(2)}:{m.group(3)}, find the "
                f"{which65} share")
    # --- Devanagari: probability --------------------------------------------------------------------------------------------------------------
    m = re.search(r"52\s+पत्तों\s+में\s+से\s+राजा\s+आने\s+"
                  r"की\s+प्रायिकता", q)
    if m:
        return ("find the probability of getting a king "
                "from a pack of 52 cards")
    m = re.search(r"सिक्का\s+तीन\s+बार\s+उछाला[^0-9]{0,40}?"
                  r"तीनों\s+बार\s+चित", q)
    if m:
        return ("a coin is tossed 3 times, find the "
                "probability of getting all heads")
    # --- Devanagari: one-line stories --------------------------------------------------------------------------------------------------------------------
    m = re.search(r"" + _N + r"\s+और\s+" + _N + r"\s+का"
                  r"\s+योग", q)
    if m:
        return f"{m.group(1)} + {m.group(2)}"
    m = re.search(r"" + _N + r"\s+अउर\s+" + _N + r"\s+का"
                  r"\s+योग", q)
    if m:
        return f"{m.group(1)} + {m.group(2)}"
    m = re.search(r"टंकी\s+में\s+" + _N + r"\s*(?:litre|"
                  r"लीटर)\s+पानी\s+है[^0-9]{0,20}?" + _N +
                  r"\s*(?:litre|लीटर)\s+और\s+डाल", q)
    if m:
        return f"{m.group(1)} + {m.group(2)}"
    m = re.search(r"" + _N + r"\s+किलो[^0-9]{0,20}?" +
                  _N + r"\s*रुपये\s+किलो\s+के\s+भाव", q)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"रोज़\s+" + _N + r"\s*रुपये\s+कमाता"
                  r"[^0-9]{0,40}?" + _N + r"\s+दिन\s+काम",
                  q)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"" + _N + r"\s+लीटर[^0-9]{0,20}?" +
                  _N + r"\s*रुपये\s+प्रति\s+लीटर", q)
    if m:
        return f"{m.group(1)} * {m.group(2)}"
    m = re.search(r"" + _N + r"\s+रन\s+बनाए\s+और\s+" +
                  _N + r"\s+ओवर[^0-9]{0,30}?प्रति\s+ओवर"
                  r"\s+औसत", q)
    if m:
        return f"{m.group(1)} / {m.group(2)}"

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
            r"avakalan|samakalan|"
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
    if "{" in q and re.search(r"\b(union|intersection|difference|"
                              r"subset)\b|only\s+in", q):
        return "sets"
    # Wave 59: cardinality givens in n(A) = ... notation and
    # subset-count asks carry no literal sets.
    if re.search(r"\bn\(\s*[a-z]\s*\)\s*=", q) or \
            re.search(r"\bsubsets?\b|\bpower set\b", q):
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
            r"diameter|radius|"
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
            "i" in q and re.search(r"\d\s*i\b|\bi\s*[\+\)\*]|\(\s*\d+\s*[\+\-]\s*\d+\s*i", q)) or \
            re.search(r"\bi\s*\^\s*\d+", q):
        return "complex"

    # Logarithms / exponents (before algebra: log equations contain '=')
    # Wave 58: the subscript forms "log_2" / "log2" must count —
    # "_" is a word character, so a plain \b after "log" never
    # matched them and those questions fell through to the
    # arithmetic simplifier, which served "32*log_2" as the
    # value of log_2 32.
    if re.search(r"\b(log|ln|logarithm|antilog)(?:_?\d|\b)", q):
        return "exponents_logs"
    # Wave 59: word-form roots ("4th root of 16", "square root
    # of 144") belong to the exponents solver — the arithmetic
    # parser cannot read the ordinal form.
    if re.search(r"\b\d+(?:st|nd|rd|th)\s+root\s+of\b|"
                 r"\b(?:square|cube)\s+root\s+of\b", q):
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

    # Wave 59: "p(x) = <poly> ... p(2)" — the polynomial's
    # VALUE at a point. The expression parser reads the
    # definition as an equation in p and answers "p = 1/x";
    # try algebra first and accept only its poly_value op.
    if re.search(r"p\(\s*x\s*\)\s*=", working) and re.search(
            r"p\(\s*-?\d", working):
        try:
            out = solve_algebra(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == "poly_value":
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
                              re.I)) \
            or (re.search(r"\b(?:class|group|survey|school|"
                          r"town)\s+of\s+\d+", working, re.I)
                and re.search(r"\d+\s+(?:play|plays|like|likes|"
                              r"prefer|prefers)\s+[a-z]+",
                              working, re.I)
                and re.search(r"\bboth\b|\bneither\b|"
                              r"at\s+least\s+one", working,
                              re.I)) \
            or (re.search(r"\d+\s+play\s+[a-z]+", working, re.I)
                and "at least one" in working.lower()
                and re.search(r"\d+\s+play\s+both", working,
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
                 r"following|\d)", working, re.I):
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
    _calc59 = re.search(r"derivative|avakalan|samakalan|integrat",
                        working)
    if not _calc59 and (re.search(r"[ऀ-ॿ]", _wl)
                        or re.search(
            r"\b(?:batao|btaao|bataao|bataiye|kitna|kitne|"
            r"kitni|ghatao|ghaatao|jodne|jodo|keemat|kimat|"
            r"qeemat|daam|rupay|rupaye|bacche|bachche|"
            r"sankhya|duguna|tiguna|milega|milegi|chahiye|"
            r"chaahiye|ladkiyan|ladkiya|istemal|istemaal|"
            r"lambai|chaudai|aadhar|unchai|vyas|trijya|"
            r"paridhi|parimaap|kshetrafal|ghante|saal)\b",
            _wl)):
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
        # Wave 59: the retry uses the superscript-cleaned
        # original — the raw text would resurrect Unicode
        # superscripts ("x² + 7x + 12 = 0 ke mool batao")
        # that the cleaning layer already normalised, and
        # the wrapped-equation schema then drops the x²
        # term and solves "7x + 12 = 0" instead.
        _cands = (working, _superscripts_to_caret(original)) \
            if "=" in original else (working,)
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

    # Wave 65: two more misrouted families. (a) "The average
    # of 5 numbers is 27..." / "average age of 8 people..."
    # route to arithmetic (route_intent keys statistics on
    # "mean", not "average"), so statistics' mean-total /
    # mean-excluded patterns never saw them. (b) "Find the
    # remainder when A is divided by B" also routes to
    # arithmetic; number_theory's remainder patterns own it.
    # Both gates accept ONLY their own ops and fall through
    # unchanged otherwise.
    if re.search(r"(?:mean|average)(?:\s+age)?\s+of\s+\d+\s+"
                 r"(?:numbers|observations|items|values|"
                 r"people|students|persons)\s+is\s+\d", _wl) \
            or re.search(r"first\s+(?:\d+|five|seven|ten)\s+"
                         r"(?:prime\s+numbers|multiples)", _wl):
        try:
            out = solve_statistics(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "mean_total", "mean_missing", "mean_excluded",
                "first_primes_stat", "first_multiples_mean"):
            if was_translated:
                out["interpreted_as"] = translated
            return out
    if "remainder" in _wl and "divided by" in _wl:
        try:
            out = solve_number_theory(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "remainder", "modulo"):
            if was_translated:
                out["interpreted_as"] = translated
            return out
    # Wave 65: unit asks the units gate never sees (it only
    # fires on "convert" / "how many") and the dozen-cost
    # story, which no intent claims.
    if "fraction of a day" in _wl:
        try:
            out = solve_units(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == \
                "fraction_of_day":
            if was_translated:
                out["interpreted_as"] = translated
            return out
    if "dozen" in _wl and "cost" in _wl:
        try:
            out = solve_applied(working)
        except Exception:
            out = None
        if out is not None and out.get("op") == \
                "dozen_cost_one":
            if was_translated:
                out["interpreted_as"] = translated
            return out
    # Wave 65: three geometry shapes other intents steal —
    # "ladder" routes to trigonometry, "(x, 4) is at
    # distance..." and "interior angles sum to..." route to
    # arithmetic; geometry's patterns own all three.
    if ("ladder" in _wl
            or re.search(r"\(\s*x\s*,[^)]*\)\s+is\s+at\s+"
                         r"(?:a\s+)?distance", _wl)
            or "interior angle" in _wl):
        try:
            out = solve_geometry(working)
        except Exception:
            out = None
        if out is not None and out.get("op") in (
                "ladder_foot", "ladder_height",
                "coord_unknown_point",
                "polygon_sides_from_sum"):
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
