"""Wave 167: board-aware chapter grounding.

Adoption #5 of the Wave-162 all-AI comparison (Perplexity's
checkable citations, adapted): a small line under a solved
answer naming the chapter the answer belongs to IN THE
STUDENT'S OWN BOARD BOOK — "RBSE · Class 8 · Mensuration".

Facts discipline (the whole design):
- Every fact the line states — the board, the class, the
  chapter name — comes from board_syllabus.json, the
  mechanical extract of the Wave-135 programme file
  (ganitra-syllabus-chapters.json, all 20 boards proven from
  the boards' own books/syllabi). Nothing is typed from
  memory here except board-name aliases and short labels,
  which are presentation, not facts.
- The line appears ONLY when every link is confident: the
  student's board normalises to a mapped board, the solver
  result's (type, op) names ONE topic, and that topic matches
  EXACTLY ONE chapter in the student's own class list for
  their board. Two candidate chapters (an NCERT Class 10
  trigonometry solve, whose book carries both "Introduction
  to Trigonometry" and "Some Applications of Trigonometry")
  means silence — silence beats a wrong tag.
- CBSE/NCERT students get no line: NCERT is Ganitra's default
  framing everywhere else, so the line would add nothing.
- Unknown / unmapped boards, guests without a board, and
  unmapped classes behave EXACTLY as before this wave.
- The line is a payload field built after the solve; it never
  touches the result dict, the answer, the steps or any
  value (Waves 132/166 value discipline), and it can never
  delay, block or re-route a solve — every failure inside
  this module returns None.

Placement differences this exists for (all recorded in the
programme file): Sets sits at Class 9 in Odisha and Assam's
elective but Class 11 in NCERT; Trigonometry is a Class 9
chapter in Odisha and Chhattisgarh; Playing with Numbers is
a Class 6 chapter in Punjab's own book; Kerala calls its
probability chapter "Mathematics of Chance"; Maharashtra's
Class 10 book carries "Financial Planning". A student is
never told a topic is not in their class — this module only
ever states a positive placement it found in their book.
"""

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_FILE = os.path.join(_HERE, "board_syllabus.json")
_DATA = None

_CBSE = "CBSE/NCERT"
_ICSE = "ICSE/ISC (CISCE)"
_UP = "UP Board (UPMSP)"
_BIHAR = "Bihar (BSEB)"
_MP = "MP Board (MPBSE)"
_RBSE = "Rajasthan (RBSE)"
_MAHA = "Maharashtra (MSBSHSE / Balbharati)"
_HARYANA = "Haryana (HBSE)"
_GUJARAT = "Gujarat (GSEB)"
_WB = "West Bengal (WBBSE / WBCHSE)"
_KARNATAKA = "Karnataka (KSEAB)"
_TN = "Tamil Nadu (Samacheer Kalvi)"
_TGAP = "Telangana (SCERT Telangana / TGBIE) + Andhra Pradesh " \
        "(SCERT AP / BIEAP)"
_PUNJAB = "Punjab (PSEB)"
_UK = "Uttarakhand (UBSE)"
_CG = "Chhattisgarh (CGBSE)"
_JHARKHAND = "Jharkhand (JAC)"
_ODISHA = "Odisha (BSE / CHSE)"
_ASSAM = "Assam (SEBA / AHSEC)"
_KERALA = "Kerala (SCERT)"


def _load():
    """The shipped syllabus extract: {board: {class_key:
    [chapter display names]}}. Loaded once; a missing or
    unreadable file simply means no grounding, ever."""
    global _DATA
    if _DATA is None:
        try:
            with open(_DATA_FILE, encoding="utf-8") as f:
                _DATA = json.load(f).get("boards") or {}
        except Exception:
            _DATA = {}
    return _DATA


# ------------------------------------------------------------------
# Board normalisation: the free-typed login board text -> the
# programme file's canonical board name.
# ------------------------------------------------------------------

def _squash(text):
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


# Squashed alias -> canonical board. Matching is exact on the
# whole squashed text first; then per WORD of the typed text
# (a word equal to an alias, or a word starting with an alias
# of length >= 4 — "rbseboard" lands on RBSE). Substring
# matching on the whole string is NOT used: "rbseboard"
# contains Bihar's "bseb" as an accidental substring, and a
# false board is worse than silence. Bare "bse" is
# deliberately absent from the aliases: it could be Bihar's
# BSEB or Odisha's BSE, so it stays silent.
_ALIASES = {}


def _alias(board, *forms):
    for form in forms:
        _ALIASES[_squash(form)] = board


_alias(_CBSE, "cbse", "ncert", "cbsc", "cbse board",
       "ncert board", "central board",
       "central board of secondary education")
_alias(_ICSE, "icse", "isc", "cisce", "icse board", "isc board")
_alias(_UP, "up", "up board", "upmsp", "uttar pradesh",
       "uttar pradesh board")
_alias(_BIHAR, "bseb", "bihar", "bihar board",
       "bihar school examination board")
_alias(_MP, "mp", "mp board", "mpbse", "madhya pradesh",
       "madhya pradesh board")
_alias(_RBSE, "rbse", "rajasthan", "rajasthan board",
       "raj board", "board of secondary education rajasthan")
_alias(_MAHA, "msbshse", "maharashtra", "maharashtra board",
       "balbharati", "maharashtra state board")
_alias(_HARYANA, "hbse", "haryana", "haryana board", "bseh",
       "board of school education haryana")
_alias(_GUJARAT, "gseb", "gujarat", "gujarat board", "gujrat")
_alias(_WB, "wbbse", "wbchse", "west bengal",
       "west bengal board", "wb board")
_alias(_KARNATAKA, "kseab", "karnataka", "karnataka board",
       "kseeb", "puc", "puc board")
_alias(_TN, "tamil nadu", "tamilnadu", "samacheer",
       "samacheer kalvi", "tn board", "tamil nadu board")
_alias(_TGAP, "telangana", "telangana board", "ts scert",
       "tgbie", "ts board", "ts", "andhra pradesh", "andhra",
       "ap", "ap board", "ap scert", "bieap",
       "andhra pradesh board")
_alias(_PUNJAB, "pseb", "punjab", "punjab board",
       "punjab school education board")
_alias(_UK, "ubse", "uttarakhand", "uttrakhand", "uk board",
       "uttarakhand board")
_alias(_CG, "cgbse", "chhattisgarh", "chattisgarh",
       "cg board", "chhattisgarh board")
_alias(_JHARKHAND, "jac", "jharkhand", "jharkhand board",
       "jharkhand academic council")
_alias(_ODISHA, "odisha", "odisha board", "bse odisha", "chse",
       "chse odisha", "orissa",
       "board of secondary education odisha")
_alias(_ASSAM, "seba", "ahsec", "assam", "assam board",
       "board of secondary education assam")
_alias(_KERALA, "kerala", "kerala board", "scert kerala",
       "dhse", "dhse kerala")

# The login slug (accounts.board_slug_for) as a fallback when
# the typed text itself does not resolve. "other-state-board"
# deliberately maps to nothing — it is the slug every unmapped
# board collapses to, so it carries no information.
_SLUG_MAP = {
    "cbse": _CBSE,
    "icse": _ICSE,
    "mp-board": _MP,
    "rajasthan-board": _RBSE,
    "up-board": _UP,
}


def canonical_board(board_text, slug=None):
    """The canonical board name for a free-typed board text
    (plus the login slug as fallback), or None when the board
    is unrecognised or ambiguous."""
    squashed = _squash(board_text)
    if squashed:
        hit = _ALIASES.get(squashed)
        if hit is not None:
            return hit
        boards_hit = set()
        for token in re.split(r"[^a-z0-9]+",
                              str(board_text or "").lower()):
            if len(token) < 2:
                continue
            if token in _ALIASES:
                boards_hit.add(_ALIASES[token])
                continue
            for alias, board in _ALIASES.items():
                if len(alias) >= 4 and token.startswith(alias):
                    boards_hit.add(board)
        if len(boards_hit) == 1:
            return boards_hit.pop()
        if len(boards_hit) > 1:
            return None  # ambiguous text: silence
    if slug:
        return _SLUG_MAP.get(str(slug).strip().lower())
    return None


def state_hint(board_text):
    """"TG" / "AP" when the typed text names one state of the
    combined Telangana + AP entry, else None."""
    text = f" {str(board_text or '').lower()} "
    tg = bool(re.search(r"\btelangana\b|\bts\b|\btg\b", text))
    ap = bool(re.search(r"\bandhra\b|\bap\b", text))
    if tg and not ap:
        return "TG"
    if ap and not tg:
        return "AP"
    return None


# ------------------------------------------------------------------
# Short labels for the line. Presentation only. Boards whose
# junior and senior bodies differ get the senior label from
# Class 11 up.
# ------------------------------------------------------------------

_LABELS = {
    _ICSE: "CISCE",
    _UP: "UPMSP",
    _BIHAR: "BSEB",
    _MP: "MPBSE",
    _RBSE: "RBSE",
    _MAHA: "Maharashtra Board",
    _HARYANA: "HBSE",
    _GUJARAT: "GSEB",
    _KARNATAKA: "KSEAB",
    _TN: "Samacheer Kalvi",
    _PUNJAB: "PSEB",
    _UK: "UBSE",
    _CG: "CGBSE",
    _JHARKHAND: "JAC",
}
_SENIOR_LABELS = {
    _WB: ("WBBSE", "WBCHSE"),
    _ODISHA: ("BSE Odisha", "CHSE Odisha"),
    _ASSAM: ("SEBA", "AHSEC"),
    _KERALA: ("Kerala SCERT", "DHSE Kerala"),
}


def _label_for(board, class_num, hint):
    if board == _TGAP:
        return {"TG": "Telangana Board",
                "AP": "AP Board"}.get(hint, "TG/AP Board")
    pair = _SENIOR_LABELS.get(board)
    if pair is not None:
        return pair[1] if class_num and class_num >= 11 \
            else pair[0]
    return _LABELS.get(board, board)


# ------------------------------------------------------------------
# Topic confidence: the solver result's (type, op) -> ONE
# topic, or None. Conservative by construction — broad solver
# families (algebra, arithmetic, applied, word_problem) never
# ground, because they span many chapters.
# ------------------------------------------------------------------

def _topic_for(result):
    if not isinstance(result, dict):
        return None
    rtype = str(result.get("type") or "")
    op = str(result.get("op") or "")
    if rtype == "statistics" and op.startswith("probability"):
        return "probability"
    if rtype == "sets":
        return "sets"
    if rtype == "trigonometry":
        return "trigonometry"
    if rtype == "vectors":
        return "vectors"
    if rtype == "complex":
        return "complex_numbers"
    if rtype == "sequences":
        return "sequences"
    if rtype == "statistics":
        if op in ("permutation", "combination", "factorial"):
            return "permutations_combinations"
        return "statistics"
    if rtype == "linear_algebra":
        return "determinants" if "determinant" in op \
            else "matrices"
    if rtype == "calculus":
        if op.startswith("ode_") \
                or "differential_equation" in op \
                or op in ("order_degree", "ode_order_degree",
                          "integrating_factor"):
            return "differential_equations"
        if "integral" in op and "deriv" not in op:
            return "integrals"
        if op.startswith("continuity") or op == "limit":
            return "continuity"
        if "deriv" in op or "differentia" in op \
                or op in ("tangent_slope", "normal_slope",
                          "normal_eq", "rate_of_change"):
            return "derivatives"
        return None
    if rtype == "number_theory" and op in ("gcd", "lcm"):
        return "real_numbers"
    if rtype == "geometry" and (op in ("area", "volume")
                                or "area" in op
                                or "volume" in op):
        return "mensuration"
    if rtype == "exponents_logs":
        return "exponents_logs"
    return None


# Topic -> chapter-name patterns, matched against the student's
# own board+class chapter list (the recorded names, lowercased).
# A topic grounds only when the patterns together match
# EXACTLY ONE chapter of that list.
_TOPIC_PATTERNS = {
    "sets": [r"\bsets?\b"],
    "trigonometry": [r"trigonometr"],
    "vectors": [r"\bvectors?\b"],
    "complex_numbers": [r"\bcomplex numbers?\b"],
    "sequences": [r"\bsequences?\b", r"\bprogressions?\b",
                  r"\bseries\b"],
    "probability": [r"\bprobability\b", r"\bchance\b"],
    "statistics": [r"\bstatistics\b", r"\bdata handling\b"],
    "permutations_combinations":
        [r"\bpermutations? and combinations?\b"],
    "matrices": [r"\bmatrices\b", r"\bmatrix\b"],
    "determinants": [r"\bdeterminants?\b"],
    "integrals": [r"\bintegrals?\b"],
    "continuity": [r"\bcontinuity\b", r"\blimits?\b"],
    "derivatives": [r"\bderivatives?\b", r"\bdifferenti\w*"],
    "differential_equations": [r"\bdifferential equations?\b"],
    "real_numbers": [r"\breal numbers\b", r"\bprime time\b",
                     r"\bplaying with numbers\b"],
    "mensuration": [r"\bmensuration\b", r"\bsurface areas?\b",
                    r"\bperimeter and area\b",
                    r"\bareas? related to circles\b"],
    "exponents_logs": [r"\blogarithms?\b", r"\bexponents?\b",
                       r"\bindices\b"],
}
for _key in _TOPIC_PATTERNS:
    _TOPIC_PATTERNS[_key] = [re.compile(p)
                             for p in _TOPIC_PATTERNS[_key]]


def _chapters_for(board, class_num, hint):
    """The recorded chapter names for this board + class, or
    None. The combined TG+AP entry keys its classes per state
    ("TG 9" / "AP 9"): a state hint reads only that state's
    list; without one the two lists are unioned (the
    exactly-one-chapter rule below still guards the match)."""
    classes = _load().get(board) or {}
    if board == _TGAP:
        keys = [f"{hint} {class_num}"] if hint \
            else [f"TG {class_num}", f"AP {class_num}"]
        merged, seen = [], set()
        for key in keys:
            for name in classes.get(key) or []:
                if name not in seen:
                    seen.add(name)
                    merged.append(name)
        return merged or None
    return classes.get(str(class_num)) or None


def chapter_for(board_text, class_num, result, slug=None):
    """(board, chapter) the answer grounds to, or None.

    `result` is the finished solve's result dict — only its
    solver (type, op) is read; it is never modified."""
    board = canonical_board(board_text, slug=slug)
    if board is None or board == _CBSE:
        return None
    try:
        class_num = int(class_num)
    except (TypeError, ValueError):
        return None
    if not 1 <= class_num <= 12:
        return None
    topic = _topic_for(result)
    if topic is None:
        return None
    chapters = _chapters_for(board, class_num,
                             state_hint(board_text))
    if not chapters:
        return None
    patterns = _TOPIC_PATTERNS[topic]
    hits = [name for name in chapters
            if any(p.search(name.lower()) for p in patterns)]
    if len(hits) != 1:
        return None
    return board, hits[0]


def grounding_line(board_text, class_num, result, slug=None):
    """The one short line for a solved answer —
    "RBSE · Class 8 · Mensuration" — or None when the answer
    cannot be grounded in the student's own board book with
    confidence. Never raises."""
    try:
        got = chapter_for(board_text, class_num, result,
                          slug=slug)
        if got is None:
            return None
        board, chapter = got
        label = _label_for(board, int(class_num),
                           state_hint(board_text))
        return f"{label} · Class {int(class_num)} · {chapter}"
    except Exception:
        return None


__all__ = ["canonical_board", "state_hint", "chapter_for",
           "grounding_line"]
