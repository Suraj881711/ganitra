"""Wave 174: paper-request routing (Suraj's live test,
19 Nov 2026).

Suraj typed into the chat:

    "Mp board ka maths ka paper chahiye 12th class ka 2025"
    "Mp board ke exams paper 12th class"

and got the bare not-found line both times — although the
exact paper he asked for (MP Board Class 12 Maths 2025) sits
in the Previous Papers library (papers_data.py, Wave 16/63).
No intent layer recognised a paper request: the solver tried
to parse the sentence as an expression (op "error"), the
greeting / non-maths / meta / guidance layers all passed,
and the chain ended at the not-found line.

This module is that missing layer, shaped like the Wave 111
meta and Wave 154 guidance layers: a strict parser plus a
serve builder, hooked into fallback's chain right after the
non-maths guard and before maths_meta (a paper request is a
concrete artefact ask; neither the meta facts nor the exam-
preparation advice may steal it, and the solver / AI legs
never see it — see fallback.py).

THE GATE (all of it must hold, else None):
  1. a paper word: paper / papers / पेपर / प्रश्नपत्र /
     प्रश्न पत्र / prashn patra;
  2. a board (catalogue family or a recognised Indian board
     with no papers yet) OR a class — a bare "paper" maths
     question ("a sheet of paper is folded…") has neither
     and is never touched;
  3. no problem payload: once the board / class / year /
     subject / request filler is stripped, no operator,
     equals sign, ask-verb or leftover maths content may
     remain — a pasted exam question that merely MENTIONS
     a board paper ("CBSE class 10 paper Q5: find the
     area…") declines here and is solved normally;
  4. maths only: a clear non-maths subject with no maths
     word gets the honest maths-only line, never a paper of
     the wrong subject.

SERVE RULES (papers_data is the only source; nothing is
invented):
  a. exact board + class (+ year when asked) exists ->
     the typed paper itself, as an answer card whose steps
     are the exam sheet (header, sections, every stored
     question with its marks) — the established Wave 63
     papers format, in the chat;
  b. board + class exists, asked year doesn't -> the
     closest available year, with ONE clear line naming
     the year actually served;
  c. the board has no paper for that class (or the board
     itself has no papers yet) -> ONE honest line naming
     the boards that DO have that class — never the bare
     not-found line;
  d. board or class missing -> one short line naming what
     is available (boards for the class / classes for the
     board) so the student can complete the ask.

Medium: a Devanagari ask, or "hindi medium / हिंदी माध्यम",
prefers the stored Hindi-medium variant of the paper when
one exists; anything else prefers the English variant.
No year asked -> the latest available year is served.
"""
import re

import papers_data

_DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


def _norm(text):
    s = str(text or "").translate(_DEV_DIGITS).lower()
    # Keep ASCII letters/digits and the whole Devanagari
    # block (its vowel signs and virama are combining marks
    # that \w-style classes mangle — "प्रश्न" must survive as
    # one word); everything else becomes a space.
    s = re.sub(r"[^a-z0-9\sऀ-ॿ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# Board families. `tokens` are substrings of the lowercased
# catalogue board string in papers_data (so the two
# Maharashtra spellings and the two Kerala spellings each
# form one family). `aliases` are word-boundary regexes run
# on the normalised question. Families with tokens=None are
# real Indian boards the library has no papers for yet —
# they still get the honest rule-(c) line.
# ---------------------------------------------------------------------------
_FAMILIES = [
    ("CBSE", "cbse",
     [r"\bcbse\b", r"\bcentral board\b", "सीबीएसई"]),
    ("ICSE (CISCE)", "icse",
     [r"\bicse\b", "आईसीएसई"]),
    ("ISC (CISCE)", "isc",
     [r"\bisc\b"]),
    ("MP Board (MPBSE)", "mp board",
     [r"\bmpbse\b", r"\bmp\s+board\b", r"\bmadhya\s+pradesh\b",
      "मध्य प्रदेश", "एमपी"]),
    ("UP Board (UPMSP)", "up board",
     [r"\bupmsp\b", r"\bup\s+board\b", r"\buttar\s+pradesh\b",
      "उत्तर प्रदेश", "यूपी"]),
    ("BSEB (Bihar Board)", "bseb",
     [r"\bbseb\b", r"\bbihar\b", "बिहार"]),
    ("RBSE (Rajasthan Board)", "rbse",
     [r"\brbse\b", r"\brajasthan\b", "राजस्थान"]),
    ("HBSE (Haryana Board)", "hbse",
     [r"\bhbse\b", r"\bharyana\b", "हरियाणा"]),
    ("Maharashtra Board", "maharashtra",
     [r"\bmsbshse\b", r"\bmaharashtra\b", "महाराष्ट्र"]),
    ("GSEB (Gujarat Board)", "gseb",
     [r"\bgseb\b", r"\bgujarat\b", "गुजरात"]),
    ("Karnataka Board (KSEAB)", "kseab",
     [r"\bkseab\b", r"\bkarnataka\b", "कर्नाटक"]),
    ("Kerala Board", "kerala",
     [r"\bkerala\b", "केरल"]),
    ("Tamil Nadu Board (DGE)", "tamil nadu",
     [r"\btamil\s*nadu\b", "तमिलनाडु", r"\btn\s+board\b"]),
    ("UBSE (Uttarakhand Board)", "ubse",
     [r"\bubse\b", r"\buttarakhand\b", "उत्तराखंड"]),
    ("Jharkhand Academic Council (JAC)", "jharkhand",
     [r"\bjharkhand\b", "झारखंड", r"\bjac\b"]),
    # Wave 179: the ten boards below gained papers in
    # Phase 1 of the papers expansion (real 2025 papers).
    ("West Bengal Board", "west bengal",
     [r"\bwbbse\b", r"\bwest\s+bengal\b", "पश्चिम बंगाल"]),
    ("Punjab Board (PSEB)", "pseb",
     [r"\bpseb\b", r"\bpunjab\s+board\b", "पंजाब बोर्ड"]),
    ("Assam Board (SEBA)", "assam board",
     [r"\bseba\b", r"\bassam\s+board\b"]),
    ("Chhattisgarh Board (CGBSE)", "cgbse",
     [r"\bcgbse\b", r"\bchhattisgarh\b", "छत्तीसगढ़"]),
    ("Himachal Board (HPBOSE)", "hpbose",
     [r"\bhpbose\b", r"\bhimachal\b", "हिमाचल"]),
    ("J&K Board (JKBOSE)", "jkbose",
     [r"\bjkbose\b", r"\bjammu\b", "जम्मू",
      r"\bj\s+k\s+board\b", r"\bkashmir\b"]),
    ("Odisha Board", "odisha",
     [r"\bodisha\s+board\b", r"\borissa\s+board\b"]),
    ("Andhra Pradesh Board", "andhra pradesh",
     [r"\bandhra\s+pradesh\b", "आंध्र प्रदेश",
      r"\bap\s+board\b", r"\bbseap\b", r"\bbieap\b"]),
    ("Telangana Board", "telangana",
     [r"\btelangana\b", "तेलंगाना"]),
    ("Goa Board", "gbshse",
     [r"\bgoa\s+board\b"]),
]

_PAPER_WORDS = ("paper", "papers", "पेपर", "प्रश्नपत्र",
                "प्रश्न पत्र", "prashn patra")

_MATHS_WORDS = ("maths", "math", "mathematics", "ganit",
                "गणित", "algebra", "geometry", "बीजगणित",
                "रेखागणित")

_OTHER_SUBJECTS = (
    "science", "विज्ञान", "social", "sst", "physics", "भौतिकी",
    "chemistry", "रसायन", "biology", "जीव विज्ञान", "history",
    "इतिहास", "geography", "भूगोल", "economics", "अर्थशास्त्र",
    "sanskrit", "संस्कृत", "accounts", "accountancy", "commerce",
    "political", "civics", "computer", "कंप्यूटर",
)
# "english" / "hindi" name a subject AND a medium; they only
# count as an other-subject ask when no maths word is present
# AND no medium word rescues them (handled in the parser).
_AMBIG_SUBJECTS = ("english", "अंग्रेज़ी", "अंग्रेजी", "hindi",
                   "हिंदी", "हिन्दी")

_HINDI_ORDINALS = {
    "छठी": 6, "छठवीं": 6, "chhathi": 6,
    "सातवीं": 7, "saatvi": 7, "saatvin": 7,
    "आठवीं": 8, "aathvi": 8, "aathvin": 8,
    "नौवीं": 9, "नवमी": 9, "naavi": 9, "navi": 9,
    "दसवीं": 10, "dasvi": 10, "dasvin": 10, "daswi": 10,
    "ग्यारहवीं": 11, "gyarahvi": 11, "gyarahvin": 11,
    "बारहवीं": 12, "barahvi": 12, "barahvin": 12,
    "barahwi": 12,
}

_ASK_VERBS = ("find", "solve", "prove", "calculate", "compute",
              "evaluate", "simplify", "factorise", "factorize",
              "ज्ञात", "हल करो", "हल कीजिए", "सिद्ध", "मान निकालो",
              "what is", "कितना", "कितने", "कितनी")

_FILLER = {
    "ka", "ke", "ki", "ko", "kaa", "me", "mein", "hai", "h",
    "chahiye", "chaahiye", "do", "dikhao", "dikha", "batao",
    "bata", "please", "mujhe", "exam", "exams", "board",
    "बोर्ड", "का", "के", "की", "को", "चाहिए", "दो", "दिखाओ",
    "बताओ", "मुझे", "कक्षा", "साल", "वर्ष", "year", "wala",
    "वाला", "वाली", "previous", "last", "pichhle", "पिछले",
    "model", "sample", "question", "प्रश्न", "पत्र", "और",
    "and", "the", "a", "an", "of", "for", "me", "में", "है",
    "हिंदी", "हिन्दी", "hindi", "english", "अंग्रेज़ी",
    "अंग्रेजी", "medium", "माध्यम", "class", "kaksha",
    "paper", "papers", "पेपर", "prashn", "patra", "subject",
    "विषय", "maths", "math", "mathematics", "ganit", "गणित",
    "algebra", "geometry", "march", "february", "annual",
    "वार्षिक", "set", "code", "full", "poora", "पूरा",
    "download", "print", "attempt", "chahie", "chaiye",
    "de", "dijiye", "दीजिए", "kripya", "कृपया",
}


def _find_board(q):
    """(display, token-or-None) of the first board family
    named in the normalised question, else None."""
    for display, token, aliases in _FAMILIES:
        for alias in aliases:
            if alias.startswith("\\") or alias.startswith("["):
                if re.search(alias, q):
                    return display, token
            elif alias in q:
                return display, token
    return None


def _find_class(q):
    m = re.search(r"(?:class|कक्षा|kaksha)\s*(\d{1,2})\b", q)
    if not m:
        m = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)\b", q)
    if not m:
        m = re.search(r"\b(\d{1,2})\s*(?:class|कक्षा)\b", q)
    if not m:
        m = re.search(r"\b(\d{1,2})वीं\b", q)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 12 else None
    for word, n in _HINDI_ORDINALS.items():
        if word in q:
            return n
    return None


def _find_year(q):
    m = re.search(r"\b((?:19|20)\d{2})\b", q)
    return int(m.group(1)) if m else None


def _payload_veto(raw, q):
    """True when the message carries a real maths problem
    beyond the paper metadata — those are solved normally,
    never answered with a paper."""
    if len(raw) > 200:
        return True
    rest = q
    for display, token, aliases in _FAMILIES:
        for alias in aliases:
            if alias.startswith("\\") or alias.startswith("["):
                rest = re.sub(alias, " ", rest)
            else:
                rest = rest.replace(alias, " ")
    rest = re.sub(r"(?:class|कक्षा|kaksha)\s*\d{1,2}\b", " ", rest)
    rest = re.sub(r"\b\d{1,2}(?:st|nd|rd|th)\b", " ", rest)
    rest = re.sub(r"\b\d{1,2}\s*(?:class|कक्षा)\b", " ", rest)
    rest = re.sub(r"\b(?:19|20)\d{2}\b", " ", rest)
    for word in _HINDI_ORDINALS:
        rest = rest.replace(word, " ")
    words = [w for w in rest.split() if w not in _FILLER]
    rest_joined = " ".join(words)
    if any(v in rest_joined for v in _ASK_VERBS):
        return True
    if re.search(r"[=+*/^%∫√<>]", rest_joined):
        return True
    if re.search(r"\d\s*[-+]\s*\d", rest_joined):
        return True
    digits = re.findall(r"\d", rest_joined)
    if digits and len(words) >= 2:
        return True
    return len(words) >= 4


def _family_papers(token, class_num=None):
    out = [p for p in papers_data.PAPERS
           if token in p["board"].lower()]
    if class_num is not None:
        out = [p for p in out if p["class_num"] == class_num]
    return out


def _boards_for_class(class_num):
    seen = []
    for p in papers_data.PAPERS:
        if p["class_num"] == class_num and p["board"] not in seen:
            seen.append(p["board"])
    return seen


def _pick(pool, q, year, hindi_wanted):
    """Deterministic choice inside one board+class pool."""
    def score(p):
        s = 0
        if hindi_wanted:
            s += 0 if p.get("medium") == "hindi" else 4
        else:
            s += 4 if p.get("medium") == "hindi" else 0
        pid = p["id"]
        if "basic" in pid and "basic" not in q:
            s += 2
        if "sample" in pid or "model" in pid:
            s += 0 if ("sample" in q or "model" in q) else 2
        if "term1" in pid or "term2" in pid:
            # A term paper loses to a full paper of the same
            # year (score 0 above); between the two terms of
            # a split year the fuller one wins via fullest().
            s += 2
        if "jul" in pid and "jul" not in q:
            s += 1
        if "algebra" in q and "algebra" not in pid:
            s += 2
        if "geometry" in q and "geometry" not in pid:
            s += 2
        return s
    def fullest(cands):
        return min(cands,
                   key=lambda p: (score(p), -len(p["questions"])))
    if year is not None:
        exact = [p for p in pool if p["year"] == year]
        if exact:
            return fullest(exact), False
        closest = min(pool,
                      key=lambda p: (abs(p["year"] - year),
                                     -p["year"]))
        return fullest([p for p in pool
                        if p["year"] == closest["year"]]), True
    # No year asked: the latest REAL paper — a sample/model
    # paper (CBSE's 2026 sample) only wins when the pool has
    # nothing else (JAC's papers are all model papers) or
    # when one was explicitly asked for.
    real = [p for p in pool
            if "sample" not in p["id"] and "model" not in p["id"]]
    if real and "sample" not in q and "model" not in q:
        pool = real
    latest = max(p["year"] for p in pool)
    return fullest([p for p in pool if p["year"] == latest]), False


_SUBJECT_NAME = {"en": "Mathematics", "roman": "Maths",
                 "dev": "गणित"}


def _plain(kind, line):
    return {"type": "Ganitra", "op": kind, "answer": line,
            "steps": [], "fallback": True,
            "fallback_kind": "paper", "plain_reply": True,
            "plain": True}


def _paper_card(paper, flavour, year_note=None):
    board = paper["board"]
    cls = paper["class_num"]
    year = paper["year"]
    hindi_medium = paper.get("medium") == "hindi"
    subject = _SUBJECT_NAME[flavour]
    if flavour == "dev" and paper.get("subject_label"):
        subject = paper["subject_label"]
    if flavour == "en":
        title = f"{board} — Class {cls} {subject} Paper, {year}"
    elif flavour == "roman":
        title = f"{board} — Class {cls} {subject} Paper, {year}"
    else:
        title = f"{board} — कक्षा {cls} {subject} प्रश्न पत्र, {year}"
    steps = []
    if year_note:
        steps.append(year_note)
    header = []
    if paper.get("set_label"):
        header.append(paper["set_label"])
    total = papers_data.paper_total_marks(paper)
    n_q = len(paper["questions"])
    if flavour == "dev":
        header.append(f"पूर्णांक: {total} · प्रश्न: {n_q}")
    elif flavour == "roman":
        header.append(f"Maximum Marks: {total} · Questions: {n_q}")
    else:
        header.append(f"Maximum Marks: {total} · Questions: {n_q}")
    steps.append(" · ".join(header))
    by_section = {}
    for ques in paper["questions"]:
        by_section.setdefault(ques["section"], []).append(ques)
    order = [s for s in papers_data.PAPER_STRUCTURE
             if s in by_section]
    order += [s for s in by_section if s not in order]
    titles = paper.get("section_titles") or {}
    titles_hi = paper.get("section_titles_hindi") or {}
    for section in order:
        qs = by_section[section]
        if len(order) > 1 or section in titles:
            if hindi_medium and flavour == "dev" \
                    and section in titles_hi:
                steps.append(titles_hi[section])
            elif section in titles:
                steps.append(titles[section])
            else:
                steps.append(papers_data.section_title_for(
                    section, qs))
        for ques in qs:
            marks = ques["marks"]
            if flavour == "dev":
                steps.append(
                    f"प्रश्न {ques['number']}. {ques['text']} "
                    f"({marks} अंक)")
            else:
                steps.append(
                    f"Q{ques['number']}. {ques['text']} "
                    f"({marks} marks)")
    if flavour == "dev":
        steps.append("इसी पेपर को Papers सेक्शन से प्रिंट भी कर "
                     "सकते हो और परीक्षा की तरह attempt भी।")
    elif flavour == "roman":
        steps.append("Isi paper ko Papers section se print bhi "
                     "kar sakte ho aur exam ki tarah attempt bhi.")
    else:
        steps.append("You can also print this paper or attempt "
                     "it like an exam from the Papers section.")
    return {"type": "Ganitra", "op": "paper", "answer": title,
            "steps": steps, "fallback": True,
            "fallback_kind": "paper", "paper_id": paper["id"]}


def paper_result(question, flavour=None):
    """The paper-request answer for `question`, or None when
    the message is not a paper request this layer owns.
    `flavour` is fallback.py's per-question flavour
    ("en" / "roman" / "dev"); derived from the script when
    omitted, exactly like the meta/guidance layers."""
    raw = str(question or "")
    q = _norm(raw)
    if not q or not any(w in q for w in _PAPER_WORDS):
        return None
    if flavour not in ("en", "roman", "dev"):
        flavour = "dev" if any("ऀ" <= ch <= "ॿ" for ch in raw) \
            else "en"
    found = _find_board(q)
    class_num = _find_class(q)
    if found is None and class_num is None:
        return None
    if _payload_veto(raw, q):
        return None
    has_maths = any(w in q for w in _MATHS_WORDS)
    other_subject = any(w in q for w in _OTHER_SUBJECTS)
    if not has_maths:
        ambig = any(w in q for w in _AMBIG_SUBJECTS) \
            and "medium" not in q and "माध्यम" not in q
        if other_subject or ambig:
            board_txt = found[0] if found else ""
            cls_txt = class_num or ""
            if flavour == "dev":
                line = ("गणित्रा के पास सिर्फ गणित के पेपर हैं"
                        + (f" — {board_txt} कक्षा {cls_txt} का "
                           "गणित का पेपर चाहिए तो 'maths paper' "
                           "लिखकर माँगो, मैं खोल दूँगा।"
                           if board_txt else "।"))
            elif flavour == "roman":
                line = ("Ganitra ke paas sirf Maths ke papers "
                        "hain"
                        + (f" — {board_txt} Class {cls_txt} ka "
                           "Maths paper chahiye to 'maths paper' "
                           "likh kar maango, main khol dunga."
                           if board_txt else "."))
            else:
                line = ("Ganitra only has Mathematics papers"
                        + (f" — for {board_txt} Class {cls_txt}, "
                           "ask for the 'maths paper' and I'll "
                           "open it." if board_txt else "."))
            return _plain("paper_subject", line)
    year = _find_year(q)
    hindi_wanted = flavour == "dev" or "hindi medium" in q \
        or "हिंदी माध्यम" in q or "hindi me" in q \
        or "हिंदी में" in q
    # --- board missing: name the boards that have the class
    if found is None:
        boards = _boards_for_class(class_num)
        if not boards:
            classes = ", ".join(
                str(c) for c in papers_data.CLASSES_WITH_PAPERS)
            if flavour == "dev":
                line = (f"कक्षा {class_num} के पेपर अभी नहीं हैं "
                        f"— पेपर कक्षा {classes} के लिए हैं।")
            elif flavour == "roman":
                line = (f"Class {class_num} ke papers abhi nahi "
                        f"hain — papers Class {classes} ke liye "
                        "hain.")
            else:
                line = (f"No papers for Class {class_num} yet — "
                        f"papers are available for Classes "
                        f"{classes}.")
            return _plain("paper_none", line)
        names = ", ".join(boards)
        if flavour == "dev":
            line = (f"कक्षा {class_num} का पेपर किस बोर्ड का "
                    f"चाहिए? इन बोर्डों के पेपर हैं: {names}।")
        elif flavour == "roman":
            line = (f"Class {class_num} ka paper kis board ka "
                    f"chahiye? In boards ke papers hain: {names}.")
        else:
            line = (f"Which board's Class {class_num} paper? "
                    f"I have papers of: {names}.")
        return _plain("paper_ask_board", line)
    display, token = found
    # --- class missing: name the classes this board has
    if class_num is None:
        if token is None:
            classes_txt = ""
            pool = []
        else:
            pool = _family_papers(token)
            classes_txt = ", ".join(str(c) for c in sorted(
                {p["class_num"] for p in pool}))
        if not pool:
            boards = sorted({p["board"] for p in papers_data.PAPERS})
            names = ", ".join(boards)
            if flavour == "dev":
                line = (f"{display} के पेपर अभी मेरे पास नहीं "
                        f"हैं। इन बोर्डों के पेपर हैं: {names}।")
            elif flavour == "roman":
                line = (f"{display} ke papers abhi mere paas "
                        f"nahi hain. In boards ke papers hain: "
                        f"{names}.")
            else:
                line = (f"I don't have {display} papers yet. "
                        f"I have papers of: {names}.")
            return _plain("paper_none", line)
        if flavour == "dev":
            line = (f"{display} का पेपर किस कक्षा का चाहिए? "
                    f"कक्षा {classes_txt} के पेपर हैं।")
        elif flavour == "roman":
            line = (f"{display} ka paper kis class ka chahiye? "
                    f"Class {classes_txt} ke papers hain.")
        else:
            line = (f"Which class? For {display} I have Class "
                    f"{classes_txt} papers.")
        return _plain("paper_ask_class", line)
    # --- board + class known
    if token is None:
        pool = []
    else:
        pool = _family_papers(token, class_num)
    if not pool:
        boards = _boards_for_class(class_num)
        if boards:
            names = ", ".join(boards)
            if flavour == "dev":
                line = (f"{display} कक्षा {class_num} का पेपर "
                        f"अभी मेरे पास नहीं है। कक्षा {class_num} "
                        f"के लिए इन बोर्डों के पेपर हैं: {names}।")
            elif flavour == "roman":
                line = (f"{display} Class {class_num} ka paper "
                        f"abhi mere paas nahi hai. Class "
                        f"{class_num} ke liye in boards ke papers "
                        f"hain: {names}.")
            else:
                line = (f"I don't have the {display} Class "
                        f"{class_num} paper yet. For Class "
                        f"{class_num} I have papers of: {names}.")
        else:
            classes = ", ".join(
                str(c) for c in papers_data.CLASSES_WITH_PAPERS)
            if flavour == "dev":
                line = (f"कक्षा {class_num} के पेपर अभी किसी "
                        f"बोर्ड के नहीं हैं — पेपर कक्षा {classes} "
                        "के लिए हैं।")
            elif flavour == "roman":
                line = (f"Class {class_num} ke papers abhi kisi "
                        f"board ke nahi hain — papers Class "
                        f"{classes} ke liye hain.")
            else:
                line = (f"No Class {class_num} papers for any "
                        f"board yet — papers are available for "
                        f"Classes {classes}.")
        return _plain("paper_none", line)
    paper, substituted = _pick(pool, q, year, hindi_wanted)
    note = None
    if substituted:
        if flavour == "dev":
            note = (f"नोट: {year} का पेपर अभी लाइब्रेरी में नहीं "
                    f"है — यह {paper['year']} वाला पेपर है।")
        elif flavour == "roman":
            note = (f"Note: {year} ka paper abhi library me "
                    f"nahi hai — ye {paper['year']} wala paper "
                    "hai.")
        else:
            note = (f"Note: the {year} paper is not in the "
                    f"library yet — this is the {paper['year']} "
                    "paper.")
    return _paper_card(paper, flavour, note)


# ---------------------------------------------------------------------------
# Wave 182: session-cookie discipline for paper cards.
#
# A served paper card carries the WHOLE typed paper in its
# steps (~8-11 KB of JSON). The routes keep the last result
# in the Flask session (session["last_result"], for
# /download, /solution/print and the follow-up layers), so
# one paper serve pushed the signed session cookie past the
# 4,093-byte browser limit (4,170 B after one paper, 5,727 B
# after a bigger one) — PythonAnywhere answered the live
# paper requests with a 502 and browsers silently dropped
# the cookie. The card is fully deterministic, though: it
# is rebuilt from (paper_id, flavour, year_note) by
# _paper_card, so the session only ever needs that small
# reference. paper_session_ref() converts a card into the
# reference (routes store the reference — app.py's Wave-182
# hooks do it for every response); expand_paper_ref()
# rebuilds the exact card from a reference (the same hooks
# expand it back at the start of the next request, so every
# in-request reader sees the full body, byte for byte).

_NOTE_PREFIXES = ("Note:", "नोट:")


def _ref_flavour_note(steps, answer):
    """Recover the (flavour, year_note) a paper card was
    built with, from the card itself. The note, when the
    served paper substituted for the asked year, is always
    steps[0] and always opens with Note:/नोट: (the header
    line that otherwise opens the steps never does). The
    flavour is read off the card's own language: a
    Devanagari title means "dev"; the Roman-Hinglish
    closing line (or note wording) means "roman";
    everything else in a card is word-for-word identical
    between "roman" and "en" except those two lines, so
    the closing line decides."""
    note = None
    body = steps
    if steps and isinstance(steps[0], str) \
            and steps[0].startswith(_NOTE_PREFIXES):
        note = steps[0]
        body = steps[1:]
    # Only the TITLE decides "dev": a dev card's title is
    # itself Devanagari, an en/roman title never is — while
    # the question lines of a Hindi-medium paper carry
    # Devanagari text in EVERY flavour, so they must not be
    # consulted for this.
    if any("ऀ" <= ch <= "ॿ" for ch in (answer or "")):
        return "dev", note
    closing = body[-1] if body else ""
    if isinstance(closing, str) \
            and closing.startswith("Isi paper ko"):
        return "roman", note
    if note and "ka paper abhi library" in note:
        return "roman", note
    return "en", note


def paper_session_ref(result):
    """The small session reference for a paper card, or
    None when `result` is not a full paper card (anything
    else is stored exactly as before). The reference keeps
    every small field of the card and replaces the paper
    body (steps / steps_tex) with the rebuild keys."""
    if not isinstance(result, dict):
        return None
    if result.get("fallback_kind") != "paper" \
            or result.get("op") != "paper" \
            or not result.get("paper_id"):
        return None
    steps = result.get("steps")
    if not isinstance(steps, list) or not steps:
        return None
    flavour, note = _ref_flavour_note(steps,
                                      result.get("answer"))
    ref = {k: v for k, v in result.items()
           if k not in ("steps", "steps_tex")}
    ref["steps"] = []
    ref["_paper_flavour"] = flavour
    ref["_paper_note"] = note
    return ref


def expand_paper_ref(ref):
    """Rebuild the full paper card from its session
    reference, or None when the reference is not one, the
    paper has left the library, or the rebuilt card no
    longer matches the reference's title (data drift — the
    caller then keeps the reference, degraded, rather than
    serving a different paper under the old title)."""
    if not isinstance(ref, dict) \
            or "_paper_flavour" not in ref \
            or ref.get("fallback_kind") != "paper":
        return None
    paper = papers_data.get_paper(ref.get("paper_id"))
    if paper is None:
        return None
    card = _paper_card(paper, ref["_paper_flavour"],
                       ref.get("_paper_note"))
    if card.get("answer") != ref.get("answer"):
        return None
    return card


__all__ = ["paper_result", "paper_session_ref",
           "expand_paper_ref"]
