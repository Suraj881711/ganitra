"""Wave 137 — photo partial-read analysis ("kuch word se
analysis karke padhna").

Suraj's approved design (17 Nov 2026): when a photo reads only
PARTIALLY, Ganitra must not give up with the raw garble. It
analyses the surviving words, works out the question TYPE,
rebuilds the full question, and puts the REBUILT question in
the editable composer (Wave 126's check path). Any part that
is unclear earns exactly ONE short confirmation line naming
that one thing ("Speed 60 hai ya 80?"). A guess is NEVER
solved directly — the student sees the reconstruction, fixes
or confirms it, and only then presses Solve.

This module is the deterministic brain of that flow:

    analyse(text) -> {"question": str, "confirm": str | None,
                      "family": str} | None

* ``text`` is the OCR read AFTER ``normalize_ocr_text`` (the
  OCR callers normalise first — this module never re-guesses
  what the normaliser already fixed). Wave 203 exception:
  the /photo-vision caller passes the RAW vision
  transcription, per gemini_vision.py's own contract that
  the OCR normaliser never rewrites vision text; this
  module's own digit translation + whitespace collapse are
  all the preparation a vision read needs.
* Numbers in a reconstruction come ONLY from the OCR text
  itself. A slot with two surviving candidates is filled with
  the first and named in the confirmation line; a slot with
  NO candidate stays a visible ``___`` placeholder and the
  confirmation line says it is missing. Nothing is invented.
* When no known family matches confidently, ``analyse``
  returns None and the caller falls back to Wave 126's raw
  editable text — never worse than before this wave.
* No AI, no network, no randomness: same input, same output.

Families (the solver's own bread-and-butter question types):
simple interest, train / speed-time-distance, HCF/LCM,
percentage, mensuration (area/perimeter), ratio, average,
and basic algebra equations. Reconstruction templates are
phrased the way the solver demonstrably accepts (checked
against the solver's own test corpus), in the language of
the surviving text: English, Hindi (Devanagari) or Hinglish
(Roman Hindi), detected with langdetect_local.
"""
import re

try:
    from langdetect_local import detect_language
except Exception:  # pragma: no cover - langdetect is in-tree
    detect_language = None

__all__ = ["analyse", "unsure_confirm", "more_notice"]

# ------------------------------------------------------------------ basics

_DEVA = re.compile(r"[ऀ-ॿ]")
_DEVA_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUM = r"\d+(?:\.\d+)?"
_NUM_RE = re.compile(r"\d+(?:\.\d+)?(?:\s*/\s*\d+)?")
_PLACEHOLDER = "___"
_MAX_WORDS = 40          # longer reads are multi-part: raw is safer


def _language(text):
    """'hi' = Devanagari Hindi, 'hinglish' = Roman Hindi,
    'en' = English (the default, as everywhere in Ganitra)."""
    if _DEVA.search(text):
        return "hi"
    if detect_language is not None:
        try:
            if detect_language(text) == "hi":
                return "hinglish"
        except Exception:
            pass
    return "en"


def _fmt(value):
    """Tidy an extracted number for display: '60.0' -> '60',
    '1,000' -> '1000'; fractions and decimals pass through."""
    v = str(value).replace(",", "").strip()
    if re.fullmatch(r"\d+\.0+", v):
        v = v.split(".")[0]
    return v


def _numbers(text):
    """Every number token in reading order: (value, start, end)."""
    out = []
    for m in _NUM_RE.finditer(text):
        out.append((_fmt(m.group(0).replace(" ", "")), m.start(),
                    m.end()))
    return out


def _has(text, *words):
    return any(w in text for w in words)


# ------------------------------------------------------- confirmation line

_SLOT_NAMES = {
    "speed": {"en": "speed", "hi": "गति", "hinglish": "Speed"},
    "distance": {"en": "distance", "hi": "दूरी",
                 "hinglish": "Distance"},
    "time": {"en": "time", "hi": "समय", "hinglish": "Time"},
    "principal": {"en": "principal", "hi": "मूलधन",
                  "hinglish": "Principal"},
    "rate": {"en": "rate", "hi": "दर", "hinglish": "Rate"},
    "second number": {"en": "second number", "hi": "दूसरा नंबर",
                      "hinglish": "Dusra number"},
    "number": {"en": "number", "hi": "संख्या", "hinglish": "Number"},
    "length": {"en": "length", "hi": "लंबाई", "hinglish": "Length"},
    "breadth": {"en": "breadth", "hi": "चौड़ाई",
                "hinglish": "Breadth"},
    "side": {"en": "side", "hi": "भुजा", "hinglish": "Side"},
    "radius": {"en": "radius", "hi": "त्रिज्या",
               "hinglish": "Radius"},
    "diameter": {"en": "diameter", "hi": "व्यास",
                 "hinglish": "Diameter"},
    "base": {"en": "base", "hi": "आधार", "hinglish": "Base"},
    "height": {"en": "height", "hi": "ऊँचाई", "hinglish": "Height"},
}


def _confirm_line(unclear, lang):
    """ONE short line naming the FIRST unclear thing — never a
    list of questions (Suraj's contract)."""
    if not unclear:
        return None
    u = unclear[0]
    name = _SLOT_NAMES[u["slot"]][lang]
    kind = u["kind"]
    if kind == "ambiguous":
        if lang == "hi":
            return f"क्या {name} {u['a']} है या {u['b']}?"
        if lang == "hinglish":
            return f"{name} {u['a']} hai ya {u['b']}?"
        return f"Is the {name} {u['a']} or {u['b']}?"
    if kind == "unit":
        if lang == "hi":
            return f"क्या {name} km/h में है या m/s में?"
        if lang == "hinglish":
            return f"{name} km/h me hai ya m/s me?"
        return f"Is the {name} in km/h or m/s?"
    if kind == "garble":
        if lang == "hi":
            return f"क्या समीकरण में वह संख्या {u['a']} है?"
        if lang == "hinglish":
            return f"Equation me woh number {u['a']} hai?"
        return f"In the equation, is that number {u['a']}?"
    # missing: the slot stays a ___ placeholder in the question
    if lang == "hi":
        return (f"{name} photo में साफ़ नहीं पढ़ा — "
                f"कृपया उसे भर दीजिए।")
    if lang == "hinglish":
        return f"{name} photo me saaf nahi padha — use bhar do."
    return (f"The {name} is not clear in the photo — "
            f"please fill it in.")


def _result(family, question, unclear, lang):
    return {"family": family, "question": question,
            "confirm": _confirm_line(unclear, lang)}


# ------------------------------------------------ Wave 203 vision lines

def unsure_confirm(text, unsure):
    """Wave 203: ONE confirmation line for a VISION read whose
    model flagged a span as unsure (gemini_vision's UNSURE
    channel). Same contract as _confirm_line: one line, the
    FIRST unsure thing only, in the read's language. The read
    itself still only prefills the editable composer — this
    line names what to check, and nothing is ever solved on
    the flagged guess. Returns None for an empty flag list."""
    spans = [str(s).strip() for s in (unsure or ()) if str(s).strip()]
    if not spans:
        return None
    span = spans[0]
    lang = _language(text)
    if lang == "hi":
        return (f"एक हिस्सा साफ़ नहीं पढ़ा — क्या वह {span} है? "
                f"ऊपर जाँच लीजिए।")
    if lang == "hinglish":
        return (f"Ek hissa saaf nahi padha — woh {span} hai? "
                f"Upar check kar lo.")
    return (f"One part was not read clearly — is it {span}? "
            f"Please check it above.")


def more_notice(text):
    """Wave 203: ONE line when a photo held more questions
    than the first (gemini_vision's MORE channel) — the drop
    is no longer silent. This is fixed system text, so
    Suraj's system-message rule applies: English or Hinglish
    (Roman) only, never Devanagari — a Devanagari read gets
    the Hinglish line."""
    if _language(text) == "en":
        return ("Your photo had more than one question — I "
                "took only the first one. Send the next "
                "question separately.")
    return ("Photo me ek se zyada sawal the — maine sirf "
            "pehla liya hai. Agla sawal alag se bhejo.")


# ------------------------------------------------------- shared slot tools

def _unit_numbers(text, unit_re):
    """Numbers immediately followed by a unit pattern:
    [(value, unit_text)] in reading order."""
    out = []
    for m in re.finditer(r"(" + _NUM + r")\s*(" + unit_re + r")",
                         text):
        out.append((_fmt(m.group(1)), m.group(2)))
    return out


def _after_keyword(text, keyword_re):
    """First number appearing shortly after a keyword pattern:
    '(?:speed|गति) ... 60'."""
    m = re.search(keyword_re + r"[^0-9]{0,24}?(" + _NUM + r")", text)
    return _fmt(m.group(1)) if m else None


# ------------------------------------------------------- simple interest

def _match_simple_interest(t, low, lang):
    signal = _has(low, "simple interest", "interest") or \
        _has(t, "साधारण ब्याज", "ब्याज")
    if not signal:
        return None
    if not (_has(low, "interest", "rate", "principal", "annum",
                 "per cent", "%") or
            _has(t, "ब्याज", "दर", "मूलधन", "वार्षिक")):
        return None
    principal = None
    m = re.search(r"(?:rs\.?|₹|रुपये|रुपया|रु\.)\s*(" + _NUM + r")",
                  t, re.IGNORECASE)
    if m:
        principal = _fmt(m.group(1))
    if principal is None:
        principal = _after_keyword(
            t, r"(?:principal|sum of|मूलधन|धनराशि)")
    if principal is None:
        m = re.search(r"(" + _NUM + r")\s*(?:rs\.?|rupees|रुपये)",
                      low)
        if m:
            principal = _fmt(m.group(1))
    rate = None
    m = re.search(r"(" + _NUM + r")\s*(?:%|percent|per cent|प्रतिशत)",
                  low)
    if m:
        rate = _fmt(m.group(1))
    if rate is None:
        rate = _after_keyword(t, r"(?:rate|दर)")
    time = None
    m = re.search(r"(" + _NUM + r")\s*(?:years?|yrs?|saal|वर्षों|"
                  r"वर्ष|साल)", t)
    if m:
        time = _fmt(m.group(1))
    filled = [x for x in (principal, rate, time) if x is not None]
    if len(filled) < 2:
        return None
    ask_amount = _has(low, "amount") or _has(t, "मिश्रधन", "कुल राशि")
    p = principal if principal is not None else _PLACEHOLDER
    r_ = rate if rate is not None else _PLACEHOLDER
    ti = time if time is not None else _PLACEHOLDER
    if lang == "hi":
        q = (f"{p} रुपये पर {r_}% वार्षिक दर से {ti} वर्षों "
             f"का साधारण ब्याज ज्ञात कीजिए।")
        if ask_amount:
            q = (f"{p} रुपये पर {r_}% वार्षिक दर से {ti} "
                 f"वर्षों का मिश्रधन ज्ञात कीजिए।")
    elif lang == "hinglish":
        q = (f"Rs {p} par {r_}% per annum ki dar se {ti} saal ka "
             f"simple interest nikalo.")
        if ask_amount:
            q = (f"Rs {p} par {r_}% per annum ki dar se {ti} saal "
                 f"baad kul rashi (amount) nikalo.")
    else:
        q = (f"Find the simple interest on Rs {p} at {r_}% "
             f"per annum for {ti} years.")
        if ask_amount:
            q = (f"Find the amount on Rs {p} at {r_}% per annum "
                 f"for {ti} years.")
    unclear = []
    for slot, val in (("principal", principal), ("rate", rate),
                      ("time", time)):
        if val is None:
            unclear.append({"kind": "missing", "slot": slot})
    return _result("simple_interest", q, unclear, lang)


# ------------------------------------------- train / speed-time-distance

_SPEED_KM = r"(?:km/h|kmph|km/hr|किमी/घंटा|किमी प्रति घंटा)"
_SPEED_MS = r"(?:m/s|m/sec|मी/से|मीटर/सेकंड)"
_TIME_UNITS = (
    (r"(?:hours?|hrs?|घंटों|घंटे|घंटा)", "hours",
     {"en": "hours", "hi": "घंटे", "hinglish": "hours"}),
    (r"(?:minutes?|mins?|मिनट)", "minutes",
     {"en": "minutes", "hi": "मिनट", "hinglish": "minutes"}),
    (r"(?:seconds?|secs?|सेकंड|सेकण्ड)", "seconds",
     {"en": "seconds", "hi": "सेकंड", "hinglish": "seconds"}),
)


def _speed_candidates(t, low):
    """All (value, unit|None) speed readings, in order."""
    out = []
    for m in re.finditer(r"(" + _NUM + r")\s*(" + _SPEED_KM + r")", t):
        out.append((_fmt(m.group(1)), "km/h", m.start()))
    for m in re.finditer(r"(" + _NUM + r")\s*(" + _SPEED_MS + r")", t):
        out.append((_fmt(m.group(1)), "m/s", m.start()))
    if not out:
        v = _after_keyword(t, r"(?:speed|गति|चाल|रफ़्तार|रफ्तार)")
        if v is None:
            m = re.search(r"(" + _NUM + r")\s*(?:की|ki)?\s*"
                          r"(?:speed|गति|चाल)", t)
            if m:
                v = _fmt(m.group(1))
        if v is not None:
            out.append((v, None, 0))
    else:
        # a second, unit-less speed mention with a DIFFERENT
        # value ("...60 km/h ... speed 80 bhi likha hai") is a
        # genuine ambiguity: the student must confirm which
        # one. A number carrying its own unit (the distance
        # after "गति से 240 km") is NOT a speed mention.
        known = {v for v, _u, _p in out}
        for m in re.finditer(
                r"(?:speed|गति|चाल|रफ़्तार|रफ्तार)[^0-9]{0,24}?"
                r"(" + _NUM + r")", t):
            v = _fmt(m.group(1))
            tail = t[m.end():m.end() + 8]
            if re.match(r"\s*(?:km|m|cm|mm|मीटर|किमी|%)", tail):
                continue
            if v not in known:
                out.append((v, None, len(t)))
            break
    out.sort(key=lambda x: x[2])
    return [(v, u) for v, u, _ in out]


def _time_reading(t):
    """(value, unit_key) of the first time reading, or
    (None, None)."""
    best = None
    for unit_re, key, _words in _TIME_UNITS:
        for m in re.finditer(r"(" + _NUM + r")\s*" + unit_re, t):
            if best is None or m.start() < best[2]:
                best = (_fmt(m.group(1)), key, m.start())
    if best is None:
        return None, None
    return best[0], best[1]


def _time_phrase(value, key, lang):
    for _re, k, words in _TIME_UNITS:
        if k == key:
            return f"{value} {words[lang]}"
    return value


def _match_train_std(t, low, lang):
    train = _has(low, "train", "traln", "rail") or \
        _has(t, "ट्रेन", "रेलगाड़ी", "रेलगाडी", "रेल")
    speed_kw = _has(low, "speed", "spead") or \
        _has(t, "गति", "चाल", "रफ़्तार", "रफ्तार")
    if not (train or speed_kw or "km/h" in low or "kmph" in low):
        return None

    speeds = _speed_candidates(t, low)
    speed = speeds[0][0] if speeds else None
    speed_unit = speeds[0][1] if speeds else None
    unclear = []
    distinct_speeds = []
    for v, _u in speeds:
        if v not in distinct_speeds:
            distinct_speeds.append(v)
    if len(distinct_speeds) >= 2:
        unclear.append({"kind": "ambiguous", "slot": "speed",
                        "a": distinct_speeds[0],
                        "b": distinct_speeds[1]})

    # distance: km first, then metres (but not a train length
    # next to 'long' — that belongs to the pole form below)
    distance = None
    distance_unit = None
    km = _unit_numbers(t, r"(?:km(?!\s*/\s*h)|किमी|"
                          r"kilometres?|kilometers?)")
    if km:
        distance, distance_unit = km[0][0], "km"
    if distance is None:
        v = _after_keyword(t, r"(?:distance|दूरी)")
        if v is not None:
            distance = v
    time, time_unit = _time_reading(t)

    # --- pole-crossing form: train + pole + length + time ---
    pole = _has(low, "pole") or _has(t, "खंभा", "खम्भा", "खंभे")
    length = None
    m = re.search(r"(" + _NUM + r")\s*(?:m|मीटर)\s*"
                  r"(?:long|lambi|lamba|लंबी|लम्बी|लंबा)", t)
    if m:
        length = _fmt(m.group(1))
    if train and pole and length is not None:
        ti = time if time is not None else _PLACEHOLDER
        tw = _time_phrase(ti, time_unit or "seconds", lang) \
            if time is not None else ti + " " + \
            {"en": "seconds", "hi": "सेकंड",
             "hinglish": "seconds"}[lang]
        if lang == "hi":
            q = (f"{length} m लंबी एक ट्रेन एक खंभे को {tw} में "
                 f"पार करती है। ट्रेन की गति ज्ञात कीजिए।")
        elif lang == "hinglish":
            q = (f"A train {length} m long crosses a pole in "
                 f"{tw}. Speed nikalo.")
        else:
            q = (f"A train {length} m long crosses a pole in "
                 f"{tw}. Find the speed of the train.")
        if time is None:
            unclear.append({"kind": "missing", "slot": "time"})
        return _result("train_pole", q, unclear, lang)

    metres = _unit_numbers(t, r"(?:metres?|meters|मीटर)")
    if distance is None and metres:
        distance, distance_unit = metres[0][0], "m"

    # what is asked?
    ask = None
    if _has(low, "time taken", "how long", "find the time",
            "find time", "time nikalo", "kitna time") or \
            _has(t, "कितना समय", "कितने समय", "समय ज्ञात",
                 "लगा समय"):
        ask = "time"
    elif _has(low, "find the speed", "find its speed",
              "speed of the train", "speed nikalo") or \
            _has(t, "गति ज्ञात", "चाल ज्ञात", "कितनी गति",
                 "गति निकाल"):
        ask = "speed"
    elif _has(low, "distance covered", "distance travelled",
              "find the distance", "distance nikalo",
              "kitni doori") or \
            _has(t, "दूरी ज्ञात", "कितनी दूरी", "दूरी निकाल"):
        ask = "distance"
    given = {"speed": speed, "distance": distance, "time": time}
    if ask is None:
        missing = [k for k, v in given.items() if v is None]
        if len(missing) == 1:
            ask = missing[0]
        else:
            return None
    needed = [k for k in ("speed", "distance", "time") if k != ask]
    if all(given[k] is None for k in needed):
        return None  # nothing survived to rebuild from

    for k in needed:
        if given[k] is None:
            unclear.append({"kind": "missing", "slot": k})
    if speed is not None and speed_unit is None and not unclear:
        unclear.append({"kind": "unit", "slot": "speed"})

    s_str = speed if speed is not None else _PLACEHOLDER
    if speed is not None and speed_unit:
        s_str = f"{speed} {speed_unit}"
    d_str = distance if distance is not None else _PLACEHOLDER
    if distance is not None and distance_unit:
        d_str = f"{distance} {distance_unit}"
    elif distance is not None:
        d_str = {"en": f"a distance of {distance}",
                 "hi": f"{distance} की दूरी",
                 "hinglish": f"{distance} ki doori"}[lang]
    t_str = _time_phrase(time, time_unit, lang) \
        if time is not None else _PLACEHOLDER

    # Template phrasings were each verified against the real
    # solver (Wave-137 build): every form below either solves
    # directly or fails honestly into the fallback chain —
    # none produces a wrong answer.
    if lang == "hi":
        if ask == "time":
            q = (f"एक ट्रेन {s_str} की गति से {d_str} तय करती है। "
                 f"लिया गया समय ज्ञात कीजिए।") if train else \
                (f"{s_str} की चाल से {d_str} जाने में कितना "
                 f"समय लगेगा?")
        elif ask == "speed":
            q = (f"एक ट्रेन {t_str} में {d_str} तय करती है। "
                 f"उसकी गति ज्ञात कीजिए।") if train else \
                (f"{d_str} तय करने में {t_str} लगते हैं। "
                 f"गति ज्ञात कीजिए।")
        else:
            q = (f"एक ट्रेन {s_str} की गति से {t_str} में "
                 f"कितनी दूरी तय करेगी?") if train else \
                (f"{s_str} की चाल से {t_str} में कितनी दूरी "
                 f"तय होगी?")
    elif lang == "hinglish":
        if ask == "time":
            q = (f"Ek train {d_str} jaati hai {s_str} ki "
                 f"speed se, kitna time lagega?") if train else \
                (f"How long does it take to travel {d_str} at "
                 f"a speed of {s_str}? Time nikalo.")
        elif ask == "speed":
            q = (f"A train travels {d_str} in {t_str}. Uski "
                 f"speed nikalo.") if train else \
                (f"Find the speed to travel {d_str} in "
                 f"{t_str}. Speed nikalo.")
        else:
            q = (f"Ek train {s_str} ki speed se {t_str} chalti "
                 f"hai. Tay ki gayi distance nikalo.") if train \
                else (f"{s_str} ki speed se {t_str} me tay ki "
                      f"gayi distance nikalo.")
    else:
        if ask == "time":
            q = (f"How long will a train take to travel "
                 f"{d_str} at a speed of {s_str}?") if train \
                else (f"How long does it take to travel "
                      f"{d_str} at a speed of {s_str}?")
        elif ask == "speed":
            q = (f"A train travels {d_str} in {t_str}. Find "
                 f"its speed.") if train else \
                (f"Find the speed to travel {d_str} in "
                 f"{t_str}.")
        else:
            q = (f"A train runs at a speed of {s_str} for "
                 f"{t_str}. Find the distance covered.") \
                if train else \
                (f"Find the distance travelled at a speed of "
                 f"{s_str} for {t_str}.")
    return _result("speed_time_distance", q, unclear, lang)


# ------------------------------------------------------------- HCF / LCM

def _match_hcf_lcm(t, low, lang):
    hcf = _has(low, "hcf", "h.c.f", "highest common") or \
        _has(t, "महत्तम", "म.स.")
    lcm = _has(low, "lcm", "l.c.m", "lowest common") or \
        _has(t, "लघुत्तम", "ल.स.")
    if hcf == lcm:      # both or neither: not this family
        return None
    kind = "HCF" if hcf else "LCM"
    nums = [v for v, _s, _e in _numbers(t)][:4]
    if not nums:
        return None
    unclear = []
    if len(nums) == 1:
        nums = nums + [_PLACEHOLDER]
        unclear.append({"kind": "missing", "slot": "second number"})
    if lang == "hi":
        joined = " और ".join(nums)
        q = f"{joined} का {kind} ज्ञात कीजिए।"
    elif lang == "hinglish":
        joined = " aur ".join(nums)
        q = f"{joined} ka {kind} nikalo."
    else:
        if len(nums) == 2:
            joined = f"{nums[0]} and {nums[1]}"
        else:
            joined = ", ".join(nums[:-1]) + f" and {nums[-1]}"
        q = f"Find the {kind} of {joined}."
    return _result("hcf_lcm", q, unclear, lang)


# ------------------------------------------------------------ percentage

def _match_percentage(t, low, lang):
    pct = re.search(r"(" + _NUM + r")\s*(?:%|percent|per cent)", low)
    marks = _has(low, "out of", "marks", "scored") or \
        _has(t, "में से", "अंक")
    what_pct = _has(low, "what percent", "what percentage") or \
        _has(t, "कितना प्रतिशत", "कितने प्रतिशत")
    if pct is None and not marks and not what_pct:
        if not _has(t, "प्रतिशत"):
            return None
    nums = [v for v, _s, _e in _numbers(t)]
    # --- what percent of n is a (no number rides the % sign) ---
    if what_pct:
        whole = part = None
        hindi_form = re.search(
            r"(" + _NUM + r")\s*का\s*कितना\s*प्रतिशत\s*"
            r"(" + _NUM + r")", t)
        if hindi_form:      # "200 का कितना प्रतिशत 50 है?"
            whole, part = _fmt(hindi_form.group(1)), \
                _fmt(hindi_form.group(2))
        if whole is None:
            whole = _after_keyword(t, r"(?:of|का)")
        m = re.search(r"(?:is|है)\s*(" + _NUM + r")", t)
        if part is None and m:
            part = _fmt(m.group(1))
        rest = [n for n in nums if n != whole]
        if whole is None and rest:
            whole = rest[0]
            rest = rest[1:]
        if part is None and rest:
            part = rest[0]
        if whole is None or part is None:
            return None
        if lang == "hi":
            q = f"{part}, {whole} का कितना प्रतिशत है?"
        elif lang == "hinglish":
            q = f"{part}, {whole} ka kitna percent hai?"
        else:
            q = f"What percent of {whole} is {part}?"
        return _result("percentage", q, [], lang)
    # --- marks form: scored a out of b ---
    if marks and len(nums) >= 2 and \
            (_has(low, "out of") or _has(t, "में से")):
        a, b = nums[0], nums[1]
        hindi_order = re.search(
            r"(" + _NUM + r")\s*में से\s*(" + _NUM + r")", t)
        if hindi_order:     # "50 में से 45": total comes first
            b, a = _fmt(hindi_order.group(1)), \
                _fmt(hindi_order.group(2))
        if lang == "hi":
            q = f"{b} में से {a} अंक मिले। प्रतिशत ज्ञात कीजिए।"
        elif lang == "hinglish":
            q = (f"Ek student ne {b} me se {a} marks liye. "
                 f"Percentage nikalo.")
        else:
            q = (f"A student scored {a} marks out of {b}. "
                 f"Find the percentage.")
        return _result("percentage", q, [], lang)
    if pct is None:
        return None
    p = _fmt(pct.group(1))
    rest = [n for n in nums if n != p]
    # --- find p% of n ---
    base = _after_keyword(t, r"(?:of|का)")
    if base is None and rest:
        base = rest[0]
    unclear = []
    if base is None:
        base = _PLACEHOLDER
        unclear.append({"kind": "missing", "slot": "number"})
    if lang == "hi":
        q = f"{base} का {p}% ज्ञात कीजिए।"
    elif lang == "hinglish":
        q = f"{base} ka {p}% nikalo."
    else:
        q = f"Find {p}% of {base}."
    return _result("percentage", q, unclear, lang)


# ------------------------------------------------------------ mensuration

_SHAPES = (
    ("rectangle", (r"rectangle", r"rectangular"),
     ("आयत",)),
    ("square", (r"square",), ("वर्ग",)),
    ("circle", (r"circle", r"circular"), ("वृत्त",)),
    ("triangle", (r"triangle",), ("त्रिभुज",)),
)


def _dim(t, keyword_re):
    v = _after_keyword(t, keyword_re)
    if v is not None:
        return v
    return None


def _match_mensuration(t, low, lang):
    shape = None
    for name, en_words, hi_words in _SHAPES:
        if any(re.search(w, low) for w in en_words) or \
                _has(t, *hi_words):
            shape = name
            break
    if shape is None:
        return None
    ask = None
    if _has(low, "circumference") or _has(t, "परिधि"):
        ask = "circumference"
    elif _has(low, "perimeter") or _has(t, "परिमाप"):
        ask = "perimeter"
    elif _has(low, "area", "eria") or _has(t, "क्षेत्रफल"):
        ask = "area"
    if ask is None:
        return None
    if shape != "circle" and ask == "circumference":
        return None
    unit = ""
    um = re.search(r"\d\s*(cm|mm|km|m)\b", low)
    if um:
        unit = " " + um.group(1)
    nums = [v for v, _s, _e in _numbers(t)]
    unclear = []
    dims = {}

    def need(slot, value):
        if value is None:
            unclear.append({"kind": "missing", "slot": slot})
            return _PLACEHOLDER
        return value

    if shape == "rectangle":
        dims["length"] = need("length", _dim(
            t, r"(?:length|लंबाई|लम्बाई)"))
        dims["breadth"] = need("breadth", _dim(
            t, r"(?:breadth|width|चौड़ाई)"))
        if dims["length"] == _PLACEHOLDER and len(nums) >= 1:
            dims["length"] = nums[0]
            unclear = [u for u in unclear
                       if u["slot"] != "length"]
        if dims["breadth"] == _PLACEHOLDER and len(nums) >= 2:
            dims["breadth"] = nums[1]
            unclear = [u for u in unclear
                       if u["slot"] != "breadth"]
    elif shape == "square":
        dims["side"] = need("side", _dim(t, r"(?:side|भुजा)"))
        if dims["side"] == _PLACEHOLDER and nums:
            dims["side"] = nums[0]
            unclear = [u for u in unclear if u["slot"] != "side"]
    elif shape == "circle":
        r_ = _dim(t, r"(?:radius|त्रिज्या)")
        d_ = _dim(t, r"(?:diameter|व्यास)")
        if r_ is not None:
            dims["radius"] = r_
        elif d_ is not None:
            dims["diameter"] = d_
        elif nums:
            dims["radius"] = nums[0]
        else:
            dims["radius"] = need("radius", None)
    else:  # triangle
        if ask == "perimeter":
            if len(nums) < 3:
                return None
            dims["sides"] = nums[:3]
        else:
            dims["base"] = need("base", _dim(
                t, r"(?:base|आधार)"))
            dims["height"] = need("height", _dim(
                t, r"(?:height|ऊँचाई|ऊंचाई)"))
            if dims["base"] == _PLACEHOLDER and len(nums) >= 1:
                dims["base"] = nums[0]
                unclear = [u for u in unclear
                           if u["slot"] != "base"]
            if dims["height"] == _PLACEHOLDER and len(nums) >= 2:
                dims["height"] = nums[1]
                unclear = [u for u in unclear
                           if u["slot"] != "height"]
    if not dims:
        return None

    ask_word = {"area": {"en": "area", "hi": "क्षेत्रफल",
                         "hinglish": "area"},
                "perimeter": {"en": "perimeter", "hi": "परिमाप",
                              "hinglish": "perimeter"},
                "circumference": {"en": "circumference",
                                  "hi": "परिधि",
                                  "hinglish": "circumference"}}[ask][lang]
    if lang == "hi":
        if shape == "rectangle":
            q = (f"एक आयत की लंबाई {dims['length']}{unit} और "
                 f"चौड़ाई {dims['breadth']}{unit} है। उसका "
                 f"{ask_word} ज्ञात कीजिए।")
        elif shape == "square":
            q = (f"एक वर्ग की भुजा {dims['side']}{unit} है। "
                 f"उसका {ask_word} ज्ञात कीजिए।")
        elif shape == "circle" and "diameter" in dims:
            q = (f"एक वृत्त का व्यास {dims['diameter']}{unit} "
                 f"है। उसका {ask_word} ज्ञात कीजिए।")
        elif shape == "circle":
            q = (f"एक वृत्त की त्रिज्या {dims['radius']}{unit} "
                 f"है। उसका {ask_word} ज्ञात कीजिए।")
        elif ask == "perimeter":
            a, b, c = dims["sides"]
            q = (f"एक त्रिभुज की भुजाएँ {a}{unit}, {b}{unit} "
                 f"और {c}{unit} हैं। उसका परिमाप ज्ञात कीजिए।")
        else:
            q = (f"एक त्रिभुज का आधार {dims['base']}{unit} और "
                 f"ऊँचाई {dims['height']}{unit} है। उसका "
                 f"क्षेत्रफल ज्ञात कीजिए।")
    elif lang == "hinglish":
        if shape == "rectangle":
            q = (f"Ek rectangle ki length {dims['length']}{unit} "
                 f"aur breadth {dims['breadth']}{unit} hai. Uska "
                 f"{ask_word} nikalo.")
        elif shape == "square":
            q = (f"Ek square ki side {dims['side']}{unit} hai. "
                 f"Uska {ask_word} nikalo.")
        elif shape == "circle" and "diameter" in dims:
            q = (f"Ek circle ka diameter {dims['diameter']}"
                 f"{unit} hai. Uska {ask_word} nikalo.")
        elif shape == "circle":
            q = (f"Ek circle ki radius {dims['radius']}{unit} "
                 f"hai. Uska {ask_word} nikalo.")
        elif ask == "perimeter":
            a, b, c = dims["sides"]
            q = (f"Ek triangle ki sides {a}{unit}, {b}{unit} "
                 f"aur {c}{unit} hain. Uska perimeter nikalo.")
        else:
            q = (f"Ek triangle ka base {dims['base']}{unit} aur "
                 f"height {dims['height']}{unit} hai. Uska area "
                 f"nikalo.")
    else:
        if shape == "rectangle":
            q = (f"Find the {ask_word} of a rectangle whose "
                 f"length is {dims['length']}{unit} and breadth "
                 f"is {dims['breadth']}{unit}.")
        elif shape == "square":
            q = (f"Find the {ask_word} of a square whose side "
                 f"is {dims['side']}{unit}.")
        elif shape == "circle" and "diameter" in dims:
            q = (f"Find the {ask_word} of a circle whose "
                 f"diameter is {dims['diameter']}{unit}.")
        elif shape == "circle":
            q = (f"Find the {ask_word} of a circle whose radius "
                 f"is {dims['radius']}{unit}.")
        elif ask == "perimeter":
            a, b, c = dims["sides"]
            q = (f"Find the perimeter of a triangle whose sides "
                 f"are {a}{unit}, {b}{unit} and {c}{unit}.")
        else:
            q = (f"Find the area of a triangle whose base is "
                 f"{dims['base']}{unit} and height is "
                 f"{dims['height']}{unit}.")
    return _result("mensuration", q, unclear, lang)


# ------------------------------------------------------------------ ratio

def _match_ratio(t, low, lang):
    if not (_has(low, "ratio") or _has(t, "अनुपात")):
        return None
    pair = re.search(r"(" + _NUM + r")\s*[:：]\s*(" + _NUM + r")"
                     r"(?:\s*[:：]\s*(" + _NUM + r"))?", t)
    amount = None
    m = re.search(r"(?:rs\.?|₹|रुपये)\s*(" + _NUM + r")", t,
                  re.IGNORECASE)
    if m:
        amount = _fmt(m.group(1))
    if amount is None:
        m = re.search(r"(" + _NUM + r")\s*(?:rs\.?|rupees|rupaye|"
                      r"रुपये|रुपया)", t, re.IGNORECASE)
        if m:
            amount = _fmt(m.group(1))
    if pair is not None:
        parts = [_fmt(g) for g in pair.groups() if g is not None]
        ratio_str = ":".join(parts)
        if amount is not None:
            if lang == "hi":
                q = (f"{amount} रुपये को {ratio_str} के अनुपात "
                     f"में बाँटिए।")
            elif lang == "hinglish":
                q = (f"{amount} rupaye ko {ratio_str} ke ratio "
                     f"me baanto.")
            else:
                q = f"Divide Rs {amount} in the ratio {ratio_str}."
            return _result("ratio", q, [], lang)
        if len(parts) == 2:
            a, b = parts
            if lang == "hi":
                q = f"{a} और {b} का अनुपात ज्ञात कीजिए।"
            elif lang == "hinglish":
                q = f"Ratio of {a} and {b} nikalo."
            else:
                q = f"Find the ratio of {a} and {b}."
            return _result("ratio", q, [], lang)
        return None
    nums = [v for v, _s, _e in _numbers(t)]
    if len(nums) == 2:
        a, b = nums
        if lang == "hi":
            q = f"{a} और {b} का अनुपात ज्ञात कीजिए।"
        elif lang == "hinglish":
            q = f"Ratio of {a} and {b} nikalo."
        else:
            q = f"Find the ratio of {a} and {b}."
        return _result("ratio", q, [], lang)
    return None


# ---------------------------------------------------------------- average

def _match_average(t, low, lang):
    if not (_has(low, "average") or _has(t, "औसत")):
        return None
    nums = [v for v, _s, _e in _numbers(t)][:8]
    if len(nums) < 3:
        return None
    if lang == "hi":
        joined = ", ".join(nums[:-1]) + f" और {nums[-1]}"
        q = f"{joined} का औसत ज्ञात कीजिए।"
    elif lang == "hinglish":
        joined = ", ".join(nums[:-1]) + f" aur {nums[-1]}"
        q = f"{joined} ka average nikalo."
    else:
        joined = ", ".join(nums[:-1]) + f" and {nums[-1]}"
        q = f"Find the average of {joined}."
    return _result("average", q, [], lang)


# ---------------------------------------------------------------- algebra

_CONFUSION_DIGIT = {"S": "5", "Z": "2", "B": "8", "O": "0",
                    "g": "9"}
_EQ_CHARS = set("0123456789abcdefghijklmnopqrstuvwxyz"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/^().= ")


def _clean_equation(t):
    """Pull the equation out of a garbled read: the run around
    '=' trimmed of the ask-words that rode along with it."""
    i = t.find("=")
    if i < 0:
        return None
    lo = i
    while lo > 0 and t[lo - 1] in _EQ_CHARS:
        lo -= 1
    hi = i + 1
    while hi < len(t) and t[hi] in _EQ_CHARS:
        hi += 1
    seg = t[lo:hi].strip()
    left, _, right = seg.partition("=")
    ltoks = left.split()
    # Drop leading ask-words ("solve", "find the value of x
    # if"...) from the left side. A pure-letter token is
    # dropped only while what follows is not an operator —
    # a lone variable right before an operator is a genuine
    # first term ("x + B = 12"), while one before another
    # term is the ask-word's variable ("find x 3x + 5 = 20").
    while len(ltoks) >= 2:
        tok = ltoks[0]
        if not re.fullmatch(r"[A-Za-z]+", tok):
            break
        if len(tok) == 1 and ltoks[1] in ("+", "-", "*", "/",
                                          "^"):
            break
        ltoks.pop(0)
    rtoks = right.split()
    cut = []
    seen_term = False
    for tok in rtoks:
        if re.fullmatch(r"[A-Za-z]{2,}", tok) and seen_term:
            break
        cut.append(tok)
        if re.search(r"[0-9A-Za-z]", tok):
            seen_term = True
    rtoks = cut
    left = " ".join(ltoks).strip()
    right = " ".join(rtoks).strip()
    if not left or not right:
        return None
    eq = f"{left} = {right}"
    if not re.search(r"[A-Za-z]", eq) or not re.search(r"\d", eq):
        return None
    if len(eq) > 60:
        return None
    return eq


def _match_algebra(t, low, lang):
    eq = _clean_equation(t)
    if eq is None:
        return None
    unclear = []
    # a lone OCR-confusion letter standing where a digit
    # belongs ("3x + S = 20") — only when x is the one real
    # variable, so a genuine second variable is never touched
    letters = set(re.findall(r"[A-Za-z]", eq))
    stray = letters - {"x", "X"}
    if len(stray) == 1:
        ch = next(iter(stray))
        if ch in _CONFUSION_DIGIT and \
                re.search(r"(?<![A-Za-z0-9])" + ch +
                          r"(?![A-Za-z0-9])", eq):
            eq = re.sub(r"(?<![A-Za-z0-9])" + ch +
                        r"(?![A-Za-z0-9])",
                        _CONFUSION_DIGIT[ch], eq, count=1)
            unclear.append({"kind": "garble", "slot": "number",
                            "a": _CONFUSION_DIGIT[ch]})
    for_x = _has(low, "value of x", "find x") or \
        _has(t, "x का मान")
    if lang == "hi":
        q = f"x का मान ज्ञात कीजिए: {eq}" if for_x else \
            f"हल कीजिए: {eq}"
    elif lang == "hinglish":
        q = f"Solve karo: {eq}"
    else:
        q = f"Solve for x: {eq}" if for_x else f"Solve: {eq}"
    return _result("algebra", q, unclear, lang)


# ------------------------------------------------------------------ entry

_MATCHERS = (_match_simple_interest, _match_train_std,
             _match_hcf_lcm, _match_percentage,
             _match_mensuration, _match_ratio, _match_average,
             _match_algebra)


def analyse(text):
    """Rebuild a partially-read photo question, or return None.

    OCR callers pass text that has already been through
    ``normalize_ocr_text``; the vision caller passes the raw
    transcription (Wave 203 — see the module docstring).
    The result is shown to the student for confirmation — it
    is NEVER solved directly (the callers' contract, pinned
    by test_wave137)."""
    if not text or not text.strip():
        return None
    t = text.translate(_DEVA_DIGITS)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t.split()) > _MAX_WORDS:
        return None
    lang = _language(t)
    low = t.lower()
    for fn in _MATCHERS:
        try:
            r = fn(t, low, lang)
        except Exception:
            r = None
        if r is not None:
            return r
    return None
