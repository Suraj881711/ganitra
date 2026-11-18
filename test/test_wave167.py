"""Wave 167: board-aware chapter grounding.

Adoption #5 of the Wave-162 all-AI comparison: a solved
answer's payload may carry ONE extra field, "grounding" —
the short line naming the chapter the answer belongs to in
the STUDENT'S OWN board book ("RBSE · Class 8 ·
Mensuration"), built by board_context.py from
board_syllabus.json (the mechanical extract of the Wave-135
programme file, all 20 boards).

Pinned here:
- board normalisation: abbreviations, full names, common
  misspellings and suffixed forms resolve; ambiguous texts
  ("BSE" alone, two boards in one string) and unknown boards
  resolve to None; the login slug is only a fallback;
- placement facts are read from the shipped JSON, never
  hard-coded into the module: for every asserted line, the
  named chapter is verified present in the shipped list for
  that board + class, and (when the programme source file is
  present and unchanged) every shipped chapter name is
  verified traceable to a raw string the programme recorded;
- the line fires for board-mapped students on confident
  solves (RBSE mensuration, Odisha Class 9 Sets and
  Trigonometry, Kerala's "Mathematics of Chance", Punjab
  Class 6 Playing with Numbers) and is ABSENT for CBSE
  students, unknown boards, ambiguous chapter matches
  (NCERT-pattern Class 10 trigonometry, Kerala Class 10
  sequences), topics the board's class does not teach
  (Assam Class 9 probability), broad solver families, plain
  replies, not-found outcomes and chat-test turns;
- the result dict and the answer values are never touched:
  the same question earns byte-identical answer + steps for
  a grounded and an ungrounded student, and "grounding"
  never appears inside the result dict itself.
"""
import copy
import json
import os
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SHIPPED = json.loads((ROOT / "board_syllabus.json")
                     .read_text(encoding="utf-8"))
BOARDS = SHIPPED["boards"]
SOURCE = Path(os.path.expanduser(
    "~/workspace/ganitra-syllabus-chapters.json"))

import board_context  # noqa: E402
from board_context import canonical_board, chapter_for, \
    grounding_line, state_hint  # noqa: E402

RBSE = "Rajasthan (RBSE)"
ODISHA = "Odisha (BSE / CHSE)"
KERALA = "Kerala (SCERT)"
PUNJAB = "Punjab (PSEB)"
MAHA = "Maharashtra (MSBSHSE / Balbharati)"
ASSAM = "Assam (SEBA / AHSEC)"
TGAP = "Telangana (SCERT Telangana / TGBIE) + Andhra Pradesh " \
       "(SCERT AP / BIEAP)"

SETS_RESULT = {"type": "sets", "op": "union",
               "answer": "{1, 2, 3, 4}", "steps": ["A ∪ B"]}
TRIG_RESULT = {"type": "trigonometry", "op": "value",
               "answer": "1", "steps": ["sin 30 = 1/2"]}
AREA_RESULT = {"type": "geometry", "op": "area",
               "answer": "154 cm²", "steps": ["A = π r²"]}
PROB_RESULT = {"type": "statistics", "op": "probability",
               "answer": "1/2", "steps": ["P = 1/2"]}
GCD_RESULT = {"type": "number_theory", "op": "gcd",
              "answer": "12", "steps": ["HCF = 12"]}


# ------------------------------------------------------------------
# Board normalisation battery
# ------------------------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("RBSE", RBSE), ("Rajasthan Board", RBSE),
    ("rajasthan", RBSE), ("RBSE Board 2026", RBSE),
    ("Board of Secondary Education Rajasthan", RBSE),
    ("Odisha", ODISHA), ("BSE Odisha", ODISHA),
    ("orissa", ODISHA), ("CHSE", ODISHA),
    ("Kerala", KERALA), ("SCERT Kerala", KERALA),
    ("DHSE", KERALA),
    ("Punjab Board", PUNJAB), ("pseb", PUNJAB),
    ("Maharashtra", MAHA), ("Balbharati", MAHA),
    ("MSBSHSE", MAHA),
    ("SEBA", ASSAM), ("AHSEC", ASSAM), ("Assam Board", ASSAM),
    ("West Bengal", "West Bengal (WBBSE / WBCHSE)"),
    ("wbbse", "West Bengal (WBBSE / WBCHSE)"),
    ("Samacheer Kalvi", "Tamil Nadu (Samacheer Kalvi)"),
    ("Tamilnadu", "Tamil Nadu (Samacheer Kalvi)"),
    ("Telangana", TGAP), ("Andhra Pradesh", TGAP),
    ("TGBIE", TGAP), ("BIEAP", TGAP),
    ("Gujrat", "Gujarat (GSEB)"), ("GSEB", "Gujarat (GSEB)"),
    ("Uttrakhand", "Uttarakhand (UBSE)"),
    ("Chattisgarh", "Chhattisgarh (CGBSE)"),
    ("Karnataka", "Karnataka (KSEAB)"), ("PUC", "Karnataka (KSEAB)"),
    ("UP Board", "UP Board (UPMSP)"), ("UP", "UP Board (UPMSP)"),
    ("MP", "MP Board (MPBSE)"), ("MPBSE", "MP Board (MPBSE)"),
    ("BSEB", "Bihar (BSEB)"), ("Bihar Board", "Bihar (BSEB)"),
    ("JAC", "Jharkhand (JAC)"),
    ("HBSE", "Haryana (HBSE)"), ("ICSE", "ICSE/ISC (CISCE)"),
    ("CISCE", "ICSE/ISC (CISCE)"),
    ("CBSE", "CBSE/NCERT"), ("NCERT", "CBSE/NCERT"),
    ("cbsc", "CBSE/NCERT"),
])
def test_board_names_resolve(text, expected):
    assert canonical_board(text) == expected


@pytest.mark.parametrize("text", [
    "BSE",               # Bihar's BSEB or Odisha's BSE: ambiguous
    "State Board", "Board", "SSC", "Narnia Board", "",
    "Bihar and Odisha board",   # two boards in one string
    "some random text",
])
def test_board_names_silent(text):
    assert canonical_board(text) is None


def test_board_slug_fallback_only():
    assert canonical_board(None, slug="rajasthan-board") == RBSE
    assert canonical_board("", slug="cbse") == "CBSE/NCERT"
    assert canonical_board("gibberish", slug="other-state-board") \
        is None
    # A resolvable typed text outranks the slug.
    assert canonical_board("Kerala", slug="cbse") == KERALA
    # An ambiguous typed text does NOT fall through to the slug.
    assert canonical_board("Bihar and Odisha board",
                           slug="cbse") is None


def test_state_hint():
    assert state_hint("Telangana Board") == "TG"
    assert state_hint("TS SCERT") == "TG"
    assert state_hint("Andhra Pradesh") == "AP"
    assert state_hint("AP Board") == "AP"
    assert state_hint("Telangana / AP") is None
    assert state_hint("RBSE") is None


# ------------------------------------------------------------------
# Shipped-data integrity: no invented chapters
# ------------------------------------------------------------------

def _raw_strings(entry):
    """Every chapter-ish string an entry records, gathered
    independently of the generator: chapters / units lists,
    term / volume lists, and part sub-dicts' chapters."""
    out = []
    if isinstance(entry, list):
        return [s for s in entry if isinstance(s, str)]
    if not isinstance(entry, dict):
        return out
    for key in ("chapters", "units"):
        value = entry.get(key)
        if isinstance(value, list):
            out.extend(s for s in value if isinstance(s, str))
    for key, value in entry.items():
        if (key.startswith("term_") or key.startswith("volume_")) \
                and isinstance(value, list):
            out.extend(s for s in value if isinstance(s, str))
        elif isinstance(value, dict) \
                and isinstance(value.get("chapters"), list):
            out.extend(s for s in value["chapters"]
                       if isinstance(s, str))
    return out


def _display_forms(raw):
    """The display forms a raw recorded name may legitimately
    ship as: itself, unit-tag-stripped, book-tag-stripped,
    its parenthesised gloss, or its head before the gloss."""
    forms = {raw}
    stripped = re.sub(r"^U\d+\s*:\s*", "", raw).strip()
    stripped = re.sub(r"\s*\[[^\]]*\]\s*$", "", stripped).strip()
    forms.add(stripped)
    m = re.match(r"^(.*?)\(([^()]*)\)\s*$", stripped)
    if m:
        forms.add(m.group(1).strip())
        forms.add(m.group(2).strip())
    return forms


def test_shipped_chapters_traceable_to_source():
    if not SOURCE.exists():
        pytest.skip("programme source not present")
    st = SOURCE.stat()
    meta = SHIPPED["meta"]
    if (st.st_mtime, st.st_size) != (meta["source_mtime"],
                                     meta["source_size"]):
        pytest.skip("programme source changed since generation")
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    src_boards = {b["board"]: b for b in source["boards"]}
    cbse_entries = src_boards["CBSE/NCERT"]["classes"]
    checked = 0
    for board, classes in BOARDS.items():
        src_classes = src_boards[board]["classes"]
        for class_key, names in classes.items():
            if board == TGAP:
                prefix, num = class_key.split(" ", 1)
                raw = []
                for key, entry in src_classes.items():
                    if re.match(rf"^{prefix}\s+{num}\b", key):
                        raw.extend(_raw_strings(entry))
            else:
                entry = src_classes.get(class_key)
                if isinstance(entry, dict) and "adopts" in entry:
                    entry = cbse_entries.get(class_key)
                raw = _raw_strings(entry)
            allowed = set()
            for r in raw:
                allowed |= _display_forms(r)
            for name in names:
                assert name in allowed, \
                    f"{board} class {class_key}: {name!r} not " \
                    f"traceable to the programme record"
                checked += 1
    assert checked > 1500  # the extract really is the programme


def test_adopted_boards_carry_cbse_lists():
    cbse = BOARDS["CBSE/NCERT"]
    for board, cls in [("UP Board (UPMSP)", "10"),
                       ("Bihar (BSEB)", "11"),
                       ("MP Board (MPBSE)", "9")]:
        assert BOARDS[board][cls] == cbse[cls]
    # Haryana Class 7 is NOT an adoption in the record: its
    # prescribed book is the retired rationalised NCERT
    # printing (DIKSHA-identical to Rajasthan's extraction),
    # so its own recorded list ships — starting "Integers",
    # not the current CBSE Class 7 list.
    assert BOARDS["Haryana (HBSE)"]["7"][0] == "Integers"
    assert BOARDS["Haryana (HBSE)"]["7"] != cbse["7"]


def test_stream_split_and_partial_classes_have_no_list():
    # Maharashtra 11/12 split by stream (Commerce / Science):
    # the student's stream is unknown, so no list ships.
    assert "11" not in BOARDS[MAHA]
    assert "12" not in BOARDS[MAHA]
    # West Bengal 7's record is a partial "named" list, not a
    # chapter list — it must not ship as one.
    assert "7" not in BOARDS["West Bengal (WBBSE / WBCHSE)"]
    # ICSE Classes 6-8 are unverified status strings.
    assert "6" not in BOARDS["ICSE/ISC (CISCE)"]


# ------------------------------------------------------------------
# Grounding facts (expectations cross-checked against the
# shipped JSON inside each test)
# ------------------------------------------------------------------

def test_rbse_class8_mensuration():
    assert "Mensuration" in BOARDS[RBSE]["8"]
    assert grounding_line("RBSE", 8, AREA_RESULT) == \
        "RBSE · Class 8 · Mensuration"


def test_odisha_class9_sets_and_trigonometry():
    chapters = BOARDS[ODISHA]["9"]
    assert "Set Operations and Applications of Sets" in chapters
    assert "Trigonometry" in chapters
    assert grounding_line("Odisha Board", 9, SETS_RESULT) == \
        "BSE Odisha · Class 9 · " \
        "Set Operations and Applications of Sets"
    assert grounding_line("Odisha", 9, TRIG_RESULT) == \
        "BSE Odisha · Class 9 · Trigonometry"


def test_kerala_mathematics_of_chance():
    assert "Mathematics of Chance" in BOARDS[KERALA]["10"]
    assert grounding_line("Kerala", 10, PROB_RESULT) == \
        "Kerala SCERT · Class 10 · Mathematics of Chance"


def test_punjab_class6_playing_with_numbers():
    assert "Playing with Numbers" in BOARDS[PUNJAB]["6"]
    assert grounding_line("Punjab Board", 6, GCD_RESULT) == \
        "PSEB · Class 6 · Playing with Numbers"


def test_maharashtra_financial_planning_book_grounding():
    # The chapter exists in the student's book (the line for
    # a mensuration solve names Mensuration from the same
    # unioned Algebra + Geometry list).
    chapters = BOARDS[MAHA]["10"]
    assert "Financial Planning" in chapters
    assert "Mensuration" in chapters
    assert grounding_line("Maharashtra Board", 10,
                          AREA_RESULT) == \
        "Maharashtra Board · Class 10 · Mensuration"


def test_cbse_and_unknown_get_no_line():
    assert grounding_line("CBSE", 11, SETS_RESULT) is None
    assert grounding_line("NCERT", 8, AREA_RESULT) is None
    assert grounding_line("Narnia Board", 9, SETS_RESULT) is None
    assert grounding_line(None, 9, SETS_RESULT) is None
    assert grounding_line("", 9, SETS_RESULT,
                          slug="other-state-board") is None


def test_ambiguous_chapter_match_stays_silent():
    # NCERT-pattern Class 10 lists carry TWO trigonometry
    # chapters; a plain trig solve cannot be placed honestly.
    rbse10 = BOARDS[RBSE]["10"]
    trig = [c for c in rbse10 if "trigonometr" in c.lower()]
    assert len(trig) == 2
    assert grounding_line("RBSE", 10, TRIG_RESULT) is None
    # Kerala Class 10 carries two sequences chapters.
    ker10 = BOARDS[KERALA]["10"]
    seq = [c for c in ker10 if "sequence" in c.lower()]
    assert len(seq) == 2
    assert grounding_line("Kerala", 10,
                          {"type": "sequences",
                           "op": "ap_nth_term",
                           "answer": "20", "steps": []}) is None


def test_topic_not_in_boards_class_stays_silent():
    # Assam's Class 9 book excludes Probability (recorded in
    # the programme file): a probability solve earns no line,
    # and no line ever claims otherwise.
    assam9 = BOARDS[ASSAM]["9"]
    assert not any("probabil" in c.lower() for c in assam9)
    assert grounding_line("SEBA", 9, PROB_RESULT) is None
    # Odisha Class 10 has no Sets chapter (Sets sits at 9).
    odo10 = BOARDS[ODISHA]["10"]
    assert not any(re.search(r"\bsets?\b", c.lower())
                   for c in odo10)
    assert grounding_line("Odisha", 10, SETS_RESULT) is None


def test_broad_families_and_bad_inputs_stay_silent():
    for result in ({"type": "algebra", "op": "factor"},
                   {"type": "arithmetic", "op": "evaluate"},
                   {"type": "applied", "op": "interest"},
                   {"type": "word_problem", "op": "age"},
                   {"type": "geometry", "op": "slope"},
                   {"type": "geometry", "op": "distance"},
                   {}, None, "not a dict"):
        assert grounding_line("RBSE", 8, result) is None
    assert grounding_line("RBSE", None, AREA_RESULT) is None
    assert grounding_line("RBSE", "eight", AREA_RESULT) is None
    assert grounding_line("RBSE", 8, AREA_RESULT) is not None


def test_result_dict_never_touched():
    result = {"type": "sets", "op": "union",
              "answer": "{1, 2, 3, 4}",
              "steps": ["A ∪ B = {1, 2, 3, 4}"],
              "value": "x"}
    before = copy.deepcopy(result)
    line = grounding_line("Odisha", 9, result)
    assert line is not None
    assert result == before
    assert chapter_for("Odisha", 9, result) == \
        (ODISHA, "Set Operations and Applications of Sets")
    assert result == before


def test_every_line_names_a_recorded_chapter():
    """Sweep: for every board, class and topic result in a
    battery, any line produced must name a chapter that the
    shipped JSON records for that board + class, at that
    class — the module can never invent a placement."""
    battery = [
        SETS_RESULT, TRIG_RESULT, AREA_RESULT, PROB_RESULT,
        GCD_RESULT,
        {"type": "statistics", "op": "mean", "answer": "6",
         "steps": []},
        {"type": "sequences", "op": "gp_sum", "answer": "9",
         "steps": []},
        {"type": "vectors", "op": "dot_product", "answer": "1",
         "steps": []},
        {"type": "linear_algebra", "op": "determinant",
         "answer": "5", "steps": []},
        {"type": "linear_algebra", "op": "add", "answer": "1",
         "steps": []},
        {"type": "calculus", "op": "derivative", "answer": "1",
         "steps": []},
        {"type": "calculus", "op": "continuity_limit",
         "answer": "1", "steps": []},
        {"type": "exponents_logs", "op": "evaluate",
         "answer": "3", "steps": []},
    ]
    lines = 0
    for board, classes in BOARDS.items():
        if board == "CBSE/NCERT":
            continue
        for class_key in classes:
            if board == TGAP:
                num = int(class_key.split(" ")[1])
            else:
                num = int(class_key)
            for result in battery:
                line = grounding_line(board, num, result)
                if line is None:
                    continue
                lines += 1
                chapter = line.rsplit(" · ", 1)[1]
                assert f"Class {num}" in line
                if board == TGAP:
                    pool = set()
                    for key in (f"TG {num}", f"AP {num}"):
                        pool |= set(classes.get(key) or [])
                    assert chapter in pool
                else:
                    assert chapter in classes[class_key]
    assert lines > 40  # the feature genuinely fires, broadly


# ------------------------------------------------------------------
# End-to-end through /api/solve
# ------------------------------------------------------------------

def _signup(board, class_text):
    return {"name": f"W167 {board} {class_text}",
            "class": class_text, "board": board,
            "goal": "Doctor", "hobby": "Cricket",
            "favourite": "Pizza", "password": "w167-test-pass"}


@pytest.fixture()
def make_client(tmp_path, monkeypatch):
    db = tmp_path / "users.db"
    monkeypatch.setenv("GANITRA_DB_PATH", str(db))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True

    def _make(board, class_text):
        c = app.test_client()
        r = c.post("/signup", data=_signup(board, class_text))
        assert r.status_code in (200, 302)
        return c
    return _make


def _solve(client, question, **extra):
    payload = {"question": question}
    payload.update(extra)
    r = client.post("/api/solve", json=payload)
    return r.get_json() or {}


AREA_Q = "Find the area of a circle with radius 7 cm"
SETS_Q = "If A = {1,2,3} and B = {3,4}, find A union B"


def test_api_rbse_student_gets_grounding_line(make_client):
    c = make_client("RBSE", "8")
    payload = _solve(c, AREA_Q)
    assert payload.get("ok") is True
    assert payload.get("grounding") == \
        "RBSE · Class 8 · Mensuration"
    # The line is a payload field only — never inside the
    # result dict (stored chats / last_result stay pristine).
    assert "grounding" not in payload["result"]


def test_api_odisha_student_gets_own_book_chapter(make_client):
    c = make_client("Odisha Board", "9")
    payload = _solve(c, SETS_Q)
    assert payload.get("grounding") == \
        "BSE Odisha · Class 9 · " \
        "Set Operations and Applications of Sets"


def test_api_cbse_and_unknown_students_get_no_line(make_client):
    for board in ("CBSE", "Some Random Board"):
        c = make_client(board, "8")
        payload = _solve(c, AREA_Q)
        assert payload.get("ok") is True
        assert "grounding" not in payload


def test_api_values_identical_with_and_without_line(make_client):
    grounded = _solve(make_client("RBSE", "8"), AREA_Q)
    plain = _solve(make_client("CBSE", "8"), AREA_Q)
    assert grounded["result"]["answer"] == \
        plain["result"]["answer"]
    assert grounded["result"]["steps"] == \
        plain["result"]["steps"]


def test_api_plain_and_notfound_have_no_line(make_client):
    c = make_client("RBSE", "8")
    hello = _solve(c, "hello")
    assert "grounding" not in hello
    gibberish = _solve(c, "asdf qwer zxcv")
    assert "grounding" not in gibberish


def test_api_chat_test_turns_have_no_line(make_client):
    c = make_client("RBSE", "8")
    start = _solve(c, "test do")
    # Chat-test turns build their own payload in api_solve and
    # never pass through _solve_response_payload.
    assert "grounding" not in start
