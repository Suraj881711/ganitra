"""Wave 177: anti-hijack guard + maths-knowledge class.

Suraj's live test (19 Nov 2026, 09:44 IST): "0 ki khoj
kisne ki hai" (who discovered zero?) and "0 ko kisne
banaya hai" were both served chip "arithmetic · evaluate",
body "Evaluate: 0 = 0", final answer "0". TRACE: SymPy's
implicit multiplication (solver/expression_parser) reads
a sentence's words as letter factors; a literal 0 among
them annihilates the product, so solver/arithmetic's
parse returned the bare number 0 with NO free symbols —
slipping past the Wave 73 word-soup defence (which needs
symbols to inspect) — and fallback._is_real passed the
fragment because no veto covered a sentence question.
The AI legs never saw it (they are failure-only, and this
counted as success), and Wave 133's verification only
checks AI answers for arithmetic correctness — "0 = 0"
is arithmetically true; nothing checked RELEVANCE.

Fix, in three layers:
  1. solver/arithmetic.py refuses the annihilation parse
     itself (sentence words left in the parser input + a
     knowledge-question shape -> ValueError, like any
     unparseable input).
  2. fallback._w177_veto — the serve-time relevance veto
     in _is_real: an op-"evaluate" bare-token self-echo
     (expression == answer == a literal of the question)
     can never serve a sentence/knowledge question that
     carries no computation shape of its own.
  3. The maths-KNOWLEDGE class (maths_meta.py): the zero
     entry gained the digit keywords "0"/"०" (students
     type the digit, not the word); three who entries were
     added (Archimedes / Gauss / Fibonacci); a FACT layer
     (~30 entries from Suraj's web-sourced GK seed list)
     covers superlatives, counting facts, definitions and
     word origins; and is_knowledge_shaped routes the rest
     of the class to the AI chain ("guide", not
     "gibberish") via the Wave 111 decision point.

Also in this wave: solver/statistics.py learned the
Hinglish factorial word order ("0 ka factorial kya hota
hai" -> 0! = 1 natively; the computation wins over the
"kya hota hai" knowledge phrasing), and 0!/1! steps no
longer render the empty product "0! = ".
"""
import pytest

from fallback import _is_real, _w177_veto, with_fallback
from maths_meta import is_knowledge_shaped
from solver.router import solve_question

HIJACK = {
    "type": "arithmetic", "op": "evaluate", "expression": "0",
    "answer": "0", "numeric": 0.0, "steps": ["Evaluate: 0 = 0"],
}


def serve(q):
    return with_fallback(q, solve_question(q))


def blob(out):
    return (str(out.get("answer") or "") + " "
            + " ".join(out.get("steps") or []))


# ---------------------------------------------------------------------------
# The two live questions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "0 ki khoj kisne ki hai",
    "0 ko kisne banaya hai",
])
def test_live_zero_questions_serve_history_not_fragment(q):
    out = serve(q)
    assert out["op"] == "history_zero"
    assert out["fallback_kind"] == "history"
    # The seed list's two-name rule: both names must appear.
    assert "Brahmagupta" in blob(out)
    assert "Aryabhata" in blob(out)
    assert "0 = 0" not in blob(out)


def test_live_zero_questions_english():
    for q in ("Who discovered 0?", "Who invented zero?",
              "0 ka avishkar kisne kiya",
              "0 ki khoj kisne ki thi"):
        out = serve(q)
        assert out["op"] == "history_zero", q
        assert "Brahmagupta" in blob(out), q


def test_solver_no_longer_succeeds_on_live_questions():
    for q in ("0 ki khoj kisne ki hai", "0 ko kisne banaya hai",
              "Who discovered 0?"):
        raw = solve_question(q)
        assert not (raw.get("op") == "evaluate"
                    and str(raw.get("answer")) == "0"), q


# ---------------------------------------------------------------------------
# The relevance veto, unit-level (both directions)
# ---------------------------------------------------------------------------

def test_veto_fires_on_sentence_question_fragment():
    assert _w177_veto("0 ki khoj kisne ki hai", HIJACK) is True
    assert _is_real("0 ki khoj kisne ki hai", HIJACK) is False
    assert _w177_veto("Who discovered 0?", HIJACK) is True
    assert _w177_veto("0 ka avishkar kab hua tha", HIJACK) is True


def test_veto_spares_genuine_computations():
    # A digit-operator-digit ask: the 0 IS the computed value.
    assert _w177_veto("0/5 kitna hota hai", HIJACK) is False
    # A sentence computation whose answer is NOT a token of
    # the question (5 aur 3 ka jod = 8).
    jod = dict(HIJACK, expression="8", answer="8", numeric=8.0,
               steps=["Evaluate: 8 = 8"])
    assert _w177_veto("5 aur 3 ka jod kitna hoga", jod) is False
    # A real expression serve: answer is no literal of the ask.
    expr = dict(HIJACK, expression="0.800000000000000",
                answer="4/5", numeric=0.8,
                steps=["Evaluate: 0.800000000000000 = 4/5"])
    assert _w177_veto("0.5 + 0.3 kitna hai", expr) is False
    # An explicit value-of ask keeps its (correct) serve.
    assert _w177_veto("0 ka value kya hai", HIJACK) is False
    # Non-evaluate ops are never this veto's business.
    assert _w177_veto("0 ki khoj kisne ki hai",
                      dict(HIJACK, op="simplify")) is False


# ---------------------------------------------------------------------------
# Knowledge battery — built-in set (seed list), EN/HI/Hinglish
# ---------------------------------------------------------------------------

KNOWLEDGE = [
    # (question, expected op, key fact in the served text)
    ("pi ki khoj kisne ki", "history_pi", "Archimedes"),
    ("Aryabhata kaun the", "history_aryabhata", "Aryabhata"),
    ("Ramanujan kaun the", "history_ramanujan", "Ramanujan"),
    ("Gauss kaun the", "history_gauss", "Gauss"),
    ("maths ke janak kaun hai", "history_archimedes",
     "Archimedes"),
    ("Who is the father of mathematics?", "history_archimedes",
     "Archimedes"),
    ("father of indian mathematics kaun hai",
     "history_aryabhata", "Aryabhata"),
    ("human computer kise kehte hai", "history_shakuntala_devi",
     "Shakuntala"),
    ("fibonacci sequence kisne diya", "history_fibonacci",
     "Fibonacci"),
    ("sabse chhota prime number kaun sa hai", "fact_prime_two",
     "2"),
    ("sabse bada prime number kaun sa hai",
     "fact_largest_prime_none", "anant"),
    ("sabse chhota composite number kaun sa hai",
     "fact_smallest_composite", "4"),
    ("sabse chhoti prakritik sankhya kaun si hai",
     "fact_smallest_natural", "1"),
    ("sabse chhoti purn sankhya kaun si hai",
     "fact_smallest_whole", "0"),
    ("1 prime number hai ya composite", "fact_one_neither",
     "na composite"),
    ("kis sankhya ka reciprocal nahi hota", "fact_no_reciprocal",
     "0"),
    ("infinity kya hota hai", "fact_infinity", "∞"),
    ("anant kya hota hai", "fact_infinity", "∞"),
    ("What is infinity?", "fact_infinity", "Infinity"),
    ("1 crore me kitne zero", "fact_crore_zeros", "7"),
    ("1 lakh me kitne zero hote hai", "fact_lakh_zeros", "5"),
    ("1 million me kitne zero hote hai", "fact_million_zeros",
     "6"),
    ("How many zeros are there in 1 crore?", "fact_crore_zeros",
     "7"),
    ("1 dozen me kitne hote hai", "fact_dozen", "12"),
    ("1 gross me kitne hote hai", "fact_gross", "144"),
    ("1729 kyu famous hai", "fact_hardy_ramanujan", "1729"),
    ("decimal system kisne banaya", "fact_decimal_system",
     "Bharat"),
    ("geometry shabd kaha se aaya", "fact_geometry_origin",
     "geo"),
    ("algebra naam kaha se aaya", "fact_algebra_origin",
     "al-jabr"),
    ("trigonometry shabd ka matlab kya hai",
     "fact_trigonometry_origin", "trigonon"),
    ("maths ka full form kya hai", "fact_maths_full_form",
     "Mathematics"),
    ("barabar ka sign kisne banaya", "fact_equals_sign",
     "Recorde"),
    ("pi day kab manaya jata hai", "fact_pi_day", "14 March"),
    # NOTE: the angle-sum asks (triangle 180° / quadrilateral
    # 360°, seed items 45-46) are served NATIVELY by the
    # Wave 103 schema with the crisp answer — pinned
    # separately in test_angle_sums_stay_native below; a
    # fact entry here would displace that better serve.
    ("sabse badi sankhya kaun si hai", "fact_largest_number",
     "nahi"),
    ("sabse chhoti sankhya kaun si hai", "fact_smallest_number",
     "nahi"),
]


@pytest.mark.parametrize("q,op,key", KNOWLEDGE)
def test_knowledge_battery(q, op, key):
    out = serve(q)
    assert out["op"] == op, q
    assert out["fallback_kind"] in ("history", "fact"), q
    assert key in blob(out), q
    assert out["op"] != "evaluate", q


# ---------------------------------------------------------------------------
# The rest of the class goes to the AI chain, not gibberish
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("q", [
    "abacus kya hota hai",
    "angle kya hota hai",
    "vedic maths kya hota hai",
    "calculator kisne banaya tha",
    "Euler kaun the",
])
def test_uncovered_knowledge_is_ai_shaped(q):
    assert is_knowledge_shaped(q) is True, q
    out = serve(q)
    # Locally (no AI keys in tests) the honest line may be
    # all that remains — but never a fragment serve.
    assert out["op"] != "evaluate", q
    assert "0 = 0" not in blob(out), q


@pytest.mark.parametrize("q", [
    "cricket ka score kya hai",
    "delhi ki rajdhani kya hai",
    "2 + 2 kitna hota hai",
])
def test_non_maths_and_computations_are_not_knowledge_shaped(q):
    assert is_knowledge_shaped(q) is False, q


def test_true_non_maths_still_gets_the_maths_only_line():
    out = serve("cricket ka score kya hai")
    assert out["fallback_kind"] == "nonmaths"


def test_fact_layer_never_displaces_native_owners():
    # Two displacements the full suite caught, both fixed:
    # (a) "what does BODMAS mean" belongs to the Wave 75
    # topics card — the bodmas FACT entry was removed.
    # (b) "How many diagonals does a hexagon have?" is a
    # native computation — the polygons entry now requires
    # a sides/name ask, never a bare "how many".
    from maths_meta import meta_result
    assert meta_result("what does BODMAS mean") is None
    assert meta_result(
        "How many diagonals does a hexagon have?") is None
    assert meta_result(
        "How many diagonals does an octagon have?") is None
    # …while the sides/name asks the entry exists for
    # still serve the fact.
    r = meta_result("hexagon me kitni sides hoti hai")
    assert r and r.get("op") == "fact_polygons", r
    assert "6" in str(r.get("answer", "")), r


def test_angle_sums_stay_native():
    # Seed items 45-46 were ALREADY covered before this
    # wave: the solver serves them via the Wave 103 schema
    # (exact "180°" / "360°", pinned by test_wave103 /
    # test_wave107) and the fallback path serves the
    # concept card. The knowledge layer must not displace
    # either serve (a fact entry did, briefly — removed).
    r = solve_question("triangle ke konon ka yog kitna hota hai")
    assert r.get("op") == "w103_angle_sum", r
    assert r.get("answer") == "180°", r
    r = solve_question(
        "chaturbhuj ke chaaro kono ka yog kitna hota hai?")
    assert r.get("op") == "w103_angle_sum", r
    assert r.get("answer") == "360°", r
    r = serve("triangle ke konon ka yog kitna hota hai")
    assert not str(r.get("op", "")).startswith("fact_"), r
    # And the WHY form keeps its Wave 103 concept topic
    # (through api._solve_friendly, the same entry
    # test_wave103 pins it through).
    from api import _solve_friendly
    r = _solve_friendly("tribhuj ke teeno kono ka yog 180 hi "
                        "kyun hota hai?")
    assert r.get("source") == "topics", r


# ---------------------------------------------------------------------------
# Must still solve — genuine computations, incl. sentence dress
# ---------------------------------------------------------------------------

MUST_SOLVE = [
    ("0.5 + 0.3", "evaluate", "4/5"),
    ("5 + 0", "evaluate", "5"),
    ("0/5 kitna hota hai", "evaluate", "0"),
    ("0.5 + 0.3 kitna hai", "evaluate", "4/5"),
    ("5 aur 3 ka jod kitna hoga", "evaluate", "8"),
    ("0 ka factorial", "factorial", "1"),
    ("0 ka factorial kya hota hai", "factorial", "1"),
    ("5 ka factorial kya hota hai", "factorial", "120"),
    ("factorial of 0", "factorial", "1"),
]


@pytest.mark.parametrize("q,op,answer", MUST_SOLVE)
def test_must_still_solve(q, op, answer):
    out = serve(q)
    assert out["op"] == op, q
    assert str(out["answer"]) == answer, q


def test_wave171_between_serve_unchanged():
    out = serve("Find two rational numbers between 3/5 and 4/5")
    assert out["op"] == "w169_rationals_between"
    assert out["answer"] == "2/3, 11/15"


def test_audit_sibling_sec_ratios_stays_correct():
    # Form-audit probe 28: "sec θ = 13/5, find all other
    # ratios" was a fragment serve at Deploy-38; current
    # main already serves the full ratio set via its own
    # trigonometry schema (a different mechanism from this
    # wave's veto — pinned here against regression).
    out = serve("If sec θ = 13/5, find all other "
                "trigonometric ratios")
    assert out["op"] == "ratio_from_ratio"
    assert "12/13" in blob(out)
