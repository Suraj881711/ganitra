"""Wave 231 — the cleanup wave: five root fixes from the
fix-queue, each pinned at the level the harness supports.

1. CHAT COMBINED-CARD PREFERENCE (Deploy-73 observation).
   "Define one-one and onto functions with examples" in chat
   served only the ONTO card, though the combined
   one_one_onto card exists (the solution page served it).
   Two roots, both fixed generally: (a) the chat path's
   human-text normaliser (_words_to_digits) SUMMED the
   hyphenated pair — "one-one" became the number 2, so the
   words never reached find_concept; (b) find_concept's
   first-match scan had no notion of a combined card. The
   fixes: hyphen-joined word-number pairs are never composed
   into a quantity, and find_concept prefers a card whose
   conjunction keyword ("X and Y" in either order) matches.

2. BUG-006 — stepcheck coverage widened from
   arithmetic/equations/simplification to the next served
   families whose workings are numeric claims (HCF/LCM,
   mean/median, mensuration, AP terms, fraction-of), ONLY
   behind a strict single-value gate on the reference
   answer; two-value answers and verdicts stay out of
   scope, and unit conversion stays out on purpose.

3. BUG-009 — ai_stream is now buffer-then-reveal: each
   leg's stream is drained into a buffer, the shaped
   results go through the SAME aiverify.verify_chain gate
   the classic path uses, and only the winning leg's
   buffered pieces are yielded. A wrong-answer stream
   reveals NOTHING. The flag stays OFF.

4. BUG-010 — OCR confidence: a low-confidence
   symbol-bearing token (digit/operator) drags the read
   into low_confidence (confirm-before-solving) even when
   the mean word confidence is high.

5. SYMPY STUDENT-FRIENDLY OUTPUT — raw SymPy forms never
   reach a student: I -> i, oo -> ∞, exp(x) -> e^x,
   Union(Interval...) -> the equivalent inequality. The
   conversion happens on solveset OBJECTS (exact), and the
   string pass in fmt() is token-guarded so it can never
   rewrite a word that merely contains the letters.
"""
import io
import os
import stat
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), ".."))

import ai_stream  # noqa: E402
import concepts  # noqa: E402
import gemini_fallback  # noqa: E402
import groq_fallback  # noqa: E402
import human_brain  # noqa: E402
import ocr  # noqa: E402
import stepcheck  # noqa: E402
from solver.expression_parser import fmt, fmt_set  # noqa: E402
from solver.router import solve_question  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for env in ("GANITRA_GEMINI_API_KEY", "GANITRA_GROQ_API_KEY",
                "GANITRA_OPENROUTER_API_KEY", "GANITRA_AI_STREAM"):
        monkeypatch.delenv(env, raising=False)
    from app import create_app
    application = create_app()
    application.config["TESTING"] = True
    c = application.test_client()
    r = c.post("/signup", data={
        "name": "Wave231 Check", "class": "10",
        "board": "CBSE", "goal": "Doctor",
        "hobby": "Cricket", "favourite": "Pizza",
        "password": "wave231pass"})
    assert r.status_code == 302, r.status_code
    return c


def _route_solve(client, question):
    r = client.post("/api/chats")
    assert r.status_code == 201, r.status_code
    chat_id = r.get_json()["chat"]["id"]
    r = client.post("/api/solve", json={
        "question": question, "chat_id": chat_id})
    assert r.status_code == 200, r.status_code
    return r.get_json()


# ---------------------------------------------------------------------------
# 1. Combined-card preference
# ---------------------------------------------------------------------------

def test_normaliser_keeps_hyphenated_concept_words():
    out = human_brain.normalize_human_text(
        "Define one-one and onto functions with examples")
    assert "one-one" in out
    assert "2" not in out  # the pair is never summed


def test_normaliser_still_converts_real_quantities():
    # The poison rule must not blunt genuine number words:
    # hyphenated quantities, hundred-chains and plain lists
    # all convert exactly as before.
    assert "21" in human_brain.normalize_human_text(
        "twenty-one students")
    assert "125" in human_brain.normalize_human_text(
        "one hundred and twenty five rupees")
    out = human_brain.normalize_human_text(
        "HCF of twelve and eighteen")
    assert "12" in out and "18" in out
    out = human_brain.normalize_human_text(
        "median of eleven, twelve and thirteen")
    assert "11" in out and "12" in out and "13" in out


def test_find_concept_prefers_combined_card_both_orders():
    for q in ("Define one-one and onto functions with examples",
              "Define onto and one-one functions"):
        card = concepts.find_concept(q)
        assert card is not None
        assert card["id"] == "one_one_onto_concept", q


def test_find_concept_combined_cards_generalise():
    # Not a one-one/onto special case: every combined card
    # wins over its single-concept siblings, either order.
    assert concepts.find_concept(
        "hcf aur lcm dono batao")["id"] == "hcf_lcm"
    assert concepts.find_concept(
        "ci aur si me antar batao")["id"] == "ci_vs_si"
    assert concepts.find_concept(
        "mean median mode batao")["id"] == "mean_median_mode"


def test_find_concept_single_asks_unchanged():
    assert concepts.find_concept(
        "one-one function kya hota hai")["id"] == \
        "one_one_concept"
    assert concepts.find_concept(
        "onto function define karo")["id"] == "onto_concept"


def test_chat_route_serves_combined_card(client):
    body = _route_solve(
        client, "Define one-one and onto functions with examples")
    result = body["result"]
    assert result.get("concept_id") == "one_one_onto_concept", \
        result.get("concept_id")
    text = (str(result.get("answer") or "") + " "
            + " ".join(str(s) for s in result.get("steps") or []))
    # The combined card teaches BOTH concepts in one answer —
    # the Deploy-73 bug served only the onto half.
    assert "One-One" in text and "Onto" in text


# ---------------------------------------------------------------------------
# 2. BUG-006 — stepcheck widening
# ---------------------------------------------------------------------------

def _verdict(question, steps):
    out = stepcheck.step_check_result(
        question + "\nMy steps:\n" + steps)
    assert out is not None
    return " ".join(str(s) for s in out.get("steps") or [])


def test_single_ref_value_gate():
    assert stepcheck._single_ref_value("6") == 6
    assert stepcheck._single_ref_value("154 cm²") == 154
    assert stepcheck._single_ref_value(
        "HCF = 6, LCM = 36") is None  # two values: stays out
    assert stepcheck._single_ref_value(
        "7 is prime") is None  # a verdict: stays out
    assert stepcheck._single_ref_value(
        "2^2 × 3^2") is None  # a form: stays out


def test_seg_value_labels_and_squared_units():
    assert stepcheck._seg_value("a10") is None  # AP label
    assert stepcheck._seg_value("2x") is None  # never a value
    assert stepcheck._seg_value("154 cm²") == 154
    assert stepcheck._seg_value("154 cm") == 154


def test_stepcheck_hcf_now_checked():
    ok = _verdict("Find HCF of 12 and 18",
                  "12 = 2 × 2 × 3\n18 = 2 × 3 × 3\n"
                  "HCF = 2 × 3 = 6")
    assert "Every step is correct" in ok
    bad = _verdict("Find HCF of 12 and 18",
                   "12 = 2 × 2 × 3\nHCF = 2 × 3 = 8")
    assert "goes wrong" in bad


def test_stepcheck_two_value_answer_stays_out_of_scope():
    out = _verdict("Find HCF and LCM of 12 and 18",
                   "HCF = 6\nLCM = 36")
    assert "can't check steps for this type" in out


def test_stepcheck_mean_and_median_now_checked():
    ok = _verdict("Find mean of 2, 4, 6, 8, 5",
                  "sum = 2 + 4 + 6 + 8 + 5 = 25\n"
                  "mean = 25 / 5 = 5")
    assert "Every step is correct" in ok
    bad = _verdict("Find mean of 2, 4, 6, 8, 5",
                   "sum = 2 + 4 + 6 + 8 + 5 = 24\n"
                   "mean = 24 / 5 = 5")
    assert "goes wrong" in bad
    med = _verdict("Find the median of 3, 1, 4, 2, 5",
                   "arranged: 1, 2, 3, 4, 5\nmedian = 3")
    assert "Every step is correct" in med


def test_stepcheck_mensuration_now_checked():
    ok = _verdict("Find the area of a circle with radius 7 cm",
                  "r = 7\nArea = 22/7 × 7 × 7 = 154 cm²")
    assert "Every step is correct" in ok
    bad = _verdict("Find the area of a circle with radius 7 cm",
                   "r = 7\nArea = 22/7 × 7 × 7 = 150 cm²")
    assert "goes wrong" in bad


def test_stepcheck_ap_term_label_not_a_value():
    ok = _verdict("Find the 10th term of AP 2, 5, 8, ...",
                  "a = 2, d = 3\na10 = 2 + 9 × 3 = 29")
    assert "Every step is correct" in ok
    bad = _verdict("Find the 10th term of AP 2, 5, 8, ...",
                   "a = 2, d = 3\na10 = 2 + 9 × 3 = 28")
    assert "goes wrong" in bad


def test_stepcheck_fraction_of_now_checked():
    ok = _verdict("What is 3/4 of 80?",
                  "3/4 × 80 = 240/4\n240/4 = 60")
    assert "Every step is correct" in ok
    bad = _verdict("What is 3/4 of 80?",
                   "3/4 × 80 = 200/4\n200/4 = 60")
    assert "goes wrong" in bad


def test_stepcheck_pre_existing_families_untouched():
    frac = _verdict("Add 3/4 and 1/2",
                    "3/4 + 1/2 = 6/8 + 4/8\n"
                    "6/8 + 4/8 = 10/8 = 5/4")
    assert "Every step is correct" in frac
    expand = _verdict("Expand (x + 2)(x + 3)",
                      "(x + 2)(x + 3) = x^2 + 3x + 2x + 6\n"
                      "= x^2 + 5x + 6")
    assert "Every step is correct" in expand


# ---------------------------------------------------------------------------
# 3. BUG-009 — ai_stream buffer-then-reveal
# ---------------------------------------------------------------------------

PROBE_Q = ("Area between curve y = x^2 and line y = x nikalo")
# The test_wave131 fixture reply, verbatim — the legs'
# shaper only accepts a fully worked reply, and the gate's
# deterministic check verifies this exact question/answer.
PIECES = ["y = x^2\ny = x\nx^2",
          " = x\nx^2 - x = 0\nx(x - 1) = 0\nx = 0 and x =",
          " ",
          "1\nArea = integral from 0 to 1 of (x - x^2) dx\n"
          "Area = [x^2/2 - x^3/3] from 0 to 1\nArea = (",
          "1/2 - 1/3) - (0 - 0)\nArea = 1/2 - 1/3\n"
          "Area = 1/6\nAnswer: 1/6 square units"]
FULL_TEXT = "".join(PIECES)
WRONG_PIECES = ["Area nikali. Answer: 1/3 square units"]


class _FakeSSE:
    """The test_wave131 transport shape, copied verbatim:
    iterating the response yields the `data: ...` byte
    lines a provider's SSE endpoint would send."""

    def __init__(self, payloads):
        import json as _json
        self._lines = [
            ("data: " + _json.dumps(p) + "\n").encode("utf-8")
            for p in payloads]

    def __iter__(self):
        return iter(self._lines)


def _gemini_stream_payloads(pieces, finish_reason):
    out = [{"candidates": [{"content": {"parts": [{"text": p}]}}]}
           for p in pieces]
    out[-1]["candidates"][0]["finishReason"] = finish_reason
    return out


def _chat_stream_payloads(pieces, finish_reason):
    out = [{"choices": [{"delta": {"content": p},
                         "finish_reason": None}]}
           for p in pieces]
    out[-1]["choices"][0]["finish_reason"] = finish_reason
    return out


def _drain(gen):
    events, ret = [], None
    while True:
        try:
            events.append(next(gen))
        except StopIteration as stop:
            ret = stop.value
            break
    return events, ret


def _only_gemini(monkeypatch, pieces, finish="STOP"):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("GANITRA_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda u, p, k, t: _FakeSSE(
            _gemini_stream_payloads(pieces, finish)))


def test_stream_flag_stays_off_by_default(monkeypatch):
    monkeypatch.delenv("GANITRA_AI_STREAM", raising=False)
    assert ai_stream.stream_enabled() is False


def test_stream_verified_leg_revealed_verbatim(monkeypatch):
    _only_gemini(monkeypatch, PIECES)
    events, result = _drain(
        ai_stream.stream_ai_events(PROBE_Q, False))
    deltas = [e for e in events if e["type"] == "delta"]
    assert "".join(e["text"] for e in deltas) == FULL_TEXT
    assert not [e for e in events if e["type"] == "reset"]
    assert result is not None
    assert result["answer"] == "1/6 square units"
    # The gate's mark rides the result, as on the classic path.
    assert result.get("ai_verification") == "deterministic"


def test_stream_wrong_answer_reveals_nothing(monkeypatch):
    # The BUG-009 pin: a stream carrying a WRONG answer must
    # not put a single token on screen — no deltas at all,
    # and the orchestrator returns None so the caller serves
    # the honest fallback.
    _only_gemini(monkeypatch, WRONG_PIECES)
    events, result = _drain(
        ai_stream.stream_ai_events(PROBE_Q, False))
    assert events == []
    assert result is None


def test_stream_wrong_leg_then_right_leg(monkeypatch):
    monkeypatch.setenv("GANITRA_GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GANITRA_GROQ_API_KEY", "test-key")
    monkeypatch.delenv("GANITRA_OPENROUTER_API_KEY",
                       raising=False)
    monkeypatch.setattr(
        gemini_fallback, "_post_sse",
        lambda u, p, k, t: _FakeSSE(
            _gemini_stream_payloads(WRONG_PIECES, "STOP")))
    monkeypatch.setattr(
        groq_fallback, "_post_sse",
        lambda u, p, k, t: _FakeSSE(
            _chat_stream_payloads(PIECES, "stop")))
    events, result = _drain(
        ai_stream.stream_ai_events(PROBE_Q, False))
    joined = "".join(e["text"] for e in events
                     if e["type"] == "delta")
    assert joined == FULL_TEXT  # only the verified leg shows
    assert "Answer: 1/3 square units" not in joined
    assert result["answer"] == "1/6 square units"


def test_stream_truncated_leg_reveals_nothing(monkeypatch):
    _only_gemini(monkeypatch, ["cut off"], finish="MAX_TOKENS")
    events, result = _drain(
        ai_stream.stream_ai_events(PROBE_Q, False))
    assert events == []
    assert result is None


# ---------------------------------------------------------------------------
# 4. BUG-010 — OCR symbol confidence
# ---------------------------------------------------------------------------

def _tsv_words(words):
    """Tesseract-style TSV from [(word, conf), ...] — one
    line, per-word confidences (the fake in test_wave83 gives
    a whole line one confidence; BUG-010 lives in the
    per-word spread, so this wave builds its own)."""
    rows = ["level\tpage_num\tblock_num\tpar_num\tline_num\t"
            "word_num\tleft\ttop\twidth\theight\tconf\ttext"]
    for wi, (word, conf) in enumerate(words, start=1):
        rows.append("\t".join([
            "5", "1", "1", "1", "1", str(wi),
            str(10 + wi * 60), "10", "50", "20",
            str(conf), word]))
    return "\n".join(rows) + "\n"


_FAKE_TESS = """\
import os, sys
path = os.environ.get("FAKE_TESS_TSV", "")
sys.stdout.write(open(path, encoding="utf-8").read()
                 if path else "")
"""


@pytest.fixture()
def fake_tess_words(tmp_path):
    exe = tmp_path / "faketesseract"
    exe.write_text("#!/usr/bin/env python3\n" + _FAKE_TESS,
                   encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)

    def install(monkeypatch, words):
        tsv = tmp_path / "out.tsv"
        tsv.write_text(_tsv_words(words), encoding="utf-8")
        monkeypatch.setenv("GANITRA_TESSERACT_CMD", str(exe))
        monkeypatch.setenv("FAKE_TESS_TSV", str(tsv))

    return install


def _render_png():
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 44)
    img = Image.new("RGB", (1100, 160), "white")
    ImageDraw.Draw(img).text((40, 55), "Solve 5 - 3",
                             fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Twenty confident prose words keep the MEAN near 94 even
# with the minus sign read at 30 — the exact BUG-010 shape.
_PROSE = [("Please", 96), ("solve", 95), ("this", 96),
          ("question", 97), ("from", 95), ("the", 96),
          ("chapter", 96), ("and", 95), ("write", 96),
          ("each", 95), ("step", 96), ("clearly", 97)]


def test_symbol_bearing_detection():
    for w in ("12", "3x", "+", "-", "x", "(2)", "2.5", "="):
        assert ocr._is_symbol_bearing(w), w
    for w in ("Solve", "chapter", "Please"):
        assert not ocr._is_symbol_bearing(w), w


def test_low_symbol_confidence_drags_outcome_down():
    words = _PROSE + [("5", 95), ("-", 30), ("3", 95)]
    _text, pairs = ocr._parse_tsv_rows(_tsv_words(words))
    mean = sum(c for _w, c in pairs) / len(pairs)
    assert mean > ocr.LOW_CONFIDENCE  # the mean looks fine
    outcome = ocr.OcrOutcome(
        _text, mean, "tesseract",
        symbol_confidence=ocr._symbol_min_confidence(pairs))
    assert outcome.symbol_confidence == 30
    assert outcome.low_confidence is True


def test_confident_symbols_keep_outcome_clean():
    outcome = ocr.OcrOutcome(
        "Solve 5 - 3", 95.0, "tesseract", symbol_confidence=92.0)
    assert outcome.low_confidence is False
    # No symbol tokens at all: the mean alone decides, as
    # before Wave 231.
    outcome = ocr.OcrOutcome(
        "wordy read", 95.0, "tesseract", symbol_confidence=None)
    assert outcome.low_confidence is False


def test_photo_ocr_route_symbol_vs_confident(
        client, fake_tess_words, monkeypatch):
    def post(words):
        fake_tess_words(monkeypatch, words)
        return client.post(
            "/photo-ocr",
            data={"file": (io.BytesIO(_render_png()),
                           "photo.png")},
            content_type="multipart/form-data").get_json()

    body = post(_PROSE + [("5", 95), ("-", 30), ("3", 95)])
    assert body["low_confidence"] is True
    body = post(_PROSE + [("5", 95), ("-", 95), ("3", 95)])
    assert body["low_confidence"] is False


# ---------------------------------------------------------------------------
# 5. SymPy student-friendly output
# ---------------------------------------------------------------------------

def test_fmt_imaginary_unit_is_lowercase_i():
    import sympy as sp
    assert fmt(sp.I) == "i"
    assert fmt(2 * sp.I) == "2·i"
    assert fmt(sp.Symbol("Interval")) == "Interval"  # safe


def test_fmt_exp_becomes_e_power():
    import sympy as sp
    x = sp.Symbol("x")
    assert fmt(sp.exp(x)) == "e^x"
    assert fmt(sp.exp(-x)) == "e^-x"
    assert fmt(sp.exp(2 * x)) == "e^(2·x)"


def test_fmt_infinity_symbol():
    import sympy as sp
    assert fmt(sp.oo) == "∞"
    assert fmt(sp.Limit(1 / sp.Symbol("x"),
                        sp.Symbol("x"), sp.oo)) == \
        "Limit(1/x, x, ∞, dir='-')"


def test_fmt_set_inequalities_exact():
    import sympy as sp
    x = sp.Symbol("x")
    assert fmt_set(sp.Interval.open(2, sp.oo), x) == "x > 2"
    assert fmt_set(sp.Interval(-sp.oo, 2), x) == "x ≤ 2"
    assert fmt_set(sp.Interval(-2, 2), x) == "-2 ≤ x ≤ 2"
    assert fmt_set(sp.Interval.open(-sp.oo, 2), x) == "x < 2"
    union = sp.Union(sp.Interval.open(-sp.oo, 1),
                     sp.Interval.open(2, sp.oo))
    assert fmt_set(union, x) == "x < 1 or x > 2"
    assert fmt_set(sp.FiniteSet(1, 2), x) == "x = 1 or x = 2"
    assert fmt_set(sp.S.EmptySet, x) == "no solution"
    assert fmt_set(sp.S.Reals, x) == "all real numbers"


def test_solve_imaginary_roots_use_i():
    r = solve_question("Solve x^2 + 1 = 0")
    assert r is not None
    assert "x = -i" in r["answer"] and "x = i" in r["answer"]
    assert "I" not in r["answer"].replace("If", "")


def test_solve_inequalities_read_as_inequalities():
    cases = {
        "x^2 - 3x + 2 > 0": "x < 1 or x > 2",
        "2x + 3 > 7": "x > 2",
        "-2x + 4 >= 0": "x ≤ 2",
        "x^2 - 4 <= 0": "-2 ≤ x ≤ 2",
    }
    for q, want in cases.items():
        r = solve_question("Solve " + q)
        assert r is not None, q
        assert r["answer"] == want, (q, r["answer"])
        for raw in ("Union", "Interval", "oo"):
            assert raw not in r["answer"], (q, r["answer"])


def test_solve_integrate_e_power_house_style():
    r = solve_question("Integrate e^x dx")
    assert r is not None
    assert r["answer"] == "e^x + C", r["answer"]
    assert "exp(" not in r["answer"]
