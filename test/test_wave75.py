"""Wave 75: the concept-answer layer (topics library).

The Wave 71 solver-health audit's biggest failure family
(~214 of 489) was students asking to be TAUGHT — definitions,
formula requests, how-to method asks, difference-between
asks, why-questions — and getting only a generic concepts.py
keyword card, while the app's own topics library
(topics_data.py: 230 topics, each with a method + a worked
example verified through the app's own solve path in
Wave 55) was never routed to from chat.

concept_topics.topic_concept_result now sits in fallback.py
between salvage and the concepts.py card: a genuine concept
ask with a confident topic match is answered with that
topic's method + worked example (fallback_kind stays
"concept"; the result is marked source="topics" +
topic_slug). Everything else falls through unchanged.

The questions below are REAL asks sampled from the Wave 71
battery (ganitra-wave71-results.jsonl, verdict CONCEPT rows)
across English, Hindi and Hinglish — plus the hijack guards:
concrete problems that must still solve numerically and must
never be captured by the concept layer, including ones
carrying the words "formula" and "difference" with numbers.
"""
import pytest

from api import _solve_friendly
from concept_topics import topic_concept_result

# --- Concept asks -> the topic that must answer them --------
# (question, expected topic_slug)

CONCEPT_ASKS = [
    # definitions — English
    ("what is a prime number", "prime-and-composite-numbers"),
    ("what is HCF", "hcf-and-lcm"),
    ("what are mean median and mode", "mean-median-and-mode"),
    ("what is the discriminant", "discriminant-and-nature-of-roots"),
    ("what is trigonometry", "trigonometric-ratios"),
    ("explain probability in simple words", "classical-probability"),
    ("what does BODMAS mean", "bodmas"),
    ("what is a quadratic equation", "quadratic-formula"),
    ("what is a right angled triangle", "pythagoras-property"),
    ("what is factorial", "permutations"),
    ("what is an irrational number", "irrational-numbers-and-surds"),
    ("अपरिमेय संख्या क्या होती है?", "irrational-numbers-and-surds"),
    ("wwhat is mean median mode", "mean-median-and-mode"),
    ("sec aur cosec kya hote hain?", "trigonometric-ratios"),
    ("what is pythagorus theorm", "pythagoras-theorem"),
    ("probablity kya hai", "classical-probability"),
    ("mutually exclusive events matlab kya?",
     "mutually-exclusive-events"),
    ("variance aur standard deviation kya hota hai?",
     "variance-and-standard-deviation"),
    # definitions — Hinglish
    ("prime number kya hota hai?", "prime-and-composite-numbers"),
    ("AP kya hoti hai?", "nth-term-of-an-ap"),
    ("GP kya hoti hai?", "geometric-progressions"),
    ("LCM kya hota hai?", "lcm-of-numbers"),
    ("sin cos tan kya hote hain?", "trigonometric-ratios"),
    ("matrix kya hoti hai batao?", "matrix-operations"),
    ("mode (bahulak) kya hota hai?", "mode-of-data"),
    ("tangent (sparsh rekha) kya hoti hai circle me?",
     "length-of-a-tangent"),
    ("sector kya hota hai circle ka?", "area-of-a-sector"),
    ("exponent (ghaat) ke niyam batao?", "laws-of-exponents"),
    ("linear equation kya hoti hai?", "solving-simple-equations"),
    ("madhyika ka matlab btao na", "median-of-ungrouped-data"),
    ("chakrvridhi byaaj kya hota hai?", "compound-interest"),
    ("sarvsamika kise kehte hain?", "algebraic-identities"),
    ("gunankhand matlab kya hota hai?", "factors-and-multiples"),
    ("samkon tribhuj kise kehte hain?", "pythagoras-property"),
    ("conjugate kya hota hai complex number ka?",
     "conjugate-of-a-complex-number"),
    ("modulus kya hota hai complex number ka?",
     "modulus-and-conjugate"),
    ("kisi polynomial ke zeroes (shunyak) ka matlab kya hai?",
     "zeroes-of-a-polynomial"),
    ("slope (dhal) kya hoti hai kisi line ki?", "slope-of-a-line"),
    # definitions — Devanagari
    ("पाइथागोरस प्रमेय क्या है?", "pythagoras-theorem"),
    ("अभाज्य संख्या क्या होती है?", "prime-and-composite-numbers"),
    ("माध्य माध्यक और बहुलक क्या होते हैं?", "mean-median-and-mode"),
    ("समांतर श्रेणी क्या होती है?", "nth-term-of-an-ap"),
    ("महत्तम समापवर्तक क्या होता है?", "hcf-and-lcm"),
    # formula requests
    ("What is the formula for the area of a circle?",
     "circumference-and-area-of-a-circle"),
    ("AP ka nth term ka formula batao", "nth-term-of-an-ap"),
    ("Compound interest ka formula kya hota hai?",
     "compound-interest"),
    ("what is the formula of simple interest", "simple-interest"),
    ("what is the formula for circumference of a circle",
     "circumference-of-a-circle"),
    ("what is the quadratic formula", "quadratic-formula"),
    ("what is the formula of speed distance and time",
     "speed-distance-and-time"),
    ("vritt ka kshetrafal ka formula kya hai?",
     "circumference-and-area-of-a-circle"),
    ("वृत्त के क्षेत्रफल का सूत्र क्या है?",
     "circumference-and-area-of-a-circle"),
    ("द्विघात सूत्र क्या है?", "quadratic-formula"),
    ("probability ka formula kya hota hai?",
     "classical-probability"),
    ("Heron ka formula kya hota hai?", "heron-s-formula"),
    ("distance formula kya hai coordinate me?", "distance-formula"),
    ("GP ka sum formula kese aata hai?", "sum-of-a-gp"),
    ("belan (cylinder) ka volume formula kese bana?",
     "volume-of-a-cylinder"),
    ("gola (sphere) ka surface area formula kya hai?",
     "surface-area-of-a-sphere"),
    # difference-between asks
    ("HCF aur LCM me kya antar hai?", "hcf-and-lcm"),
    ("what is LCM and how is it different from HCF", "hcf-and-lcm"),
    ("mean aur median me kya fark hai?", "mean-median-and-mode"),
    ("union aur intersection set me kya antar hai?",
     "operations-on-sets"),
    ("kshetrafal aur parimaap me kya antar hai?",
     "area-of-rectangles-and-squares"),
    # how-to method asks
    ("how do we find probability", "classical-probability"),
    ("HCF kaise nikale?", "hcf-and-lcm"),
    ("byaj kaise nikalte hai?", "simple-interest"),
    ("pratishat kaise nikale?", "percentage"),
    ("ausat kaise nikalte hai?", "mean-of-data"),
    ("tribhuj ka area kaise nikale?", "area-of-a-triangle"),
    ("samikaran kaise hal karte hai?", "solving-simple-equations"),
    ("औसत कैसे निकालते हैं?", "mean-of-data"),
    ("LCM nikaalne ka tarika batao?", "lcm-of-numbers"),
    ("sin theta ki value kese aati hai samjhao?",
     "standard-angle-values"),
    ("do charo wali linear equations kese solve karte hain?",
     "substitution-method"),
    ("profit aur loss kese nikaalte hain?", "profit-and-loss"),
    ("plz yr HCF LCM ka simple tarika bta do, exam kal hai?",
     "hcf-and-lcm"),
    ("द्विघात समीकरण कैसे हल करते हैं?", "quadratic-formula"),
    ("साधारण ब्याज कैसे निकालते हैं, तरीका बताइए।",
     "simple-interest"),
    ("how to find the lcm of two numbers?", "lcm-of-numbers"),
    ("explain how to calculate the area of a circle",
     "circumference-and-area-of-a-circle"),
    # why / when asks
    ("midpoint formula kya hai aur kyun kaam karta hai?",
     "section-formula-and-midpoint"),
    ("events ki probability hamesha 0 aur 1 ke beech hi kyun "
     "hoti hai?", "classical-probability"),
    ("median aur mode kab use karte hain?", "median-and-mode"),
    ("shanku (cone) ka volume cylinder ka teesra hissa kyun "
     "hota hai?", "volume-of-a-cone"),
    ("tribhuj ke teeno kono ka yog 180 hi kyun hota hai?",
     "angle-sum-property-of-a-triangle"),
    ("nth term ko an kyun likhte hain AP me?", "nth-term-of-an-ap"),
    ("trig ratios sirf samkon tribhuj me hi kyun hote hain?",
     "trigonometric-ratios"),
    ("integration derivative ka ulta kyun kahlata hai?",
     "indefinite-integrals"),
    ("do matrix kab jode ja sakte hain?", "matrix-operations"),
]


@pytest.mark.parametrize("question,slug", CONCEPT_ASKS)
def test_concept_asks_answered_from_topics(question, slug):
    res = _solve_friendly(question)
    assert res.get("source") == "topics", res.get("answer")
    assert res.get("topic_slug") == slug, res.get("topic_slug")
    assert res.get("fallback_kind") == "concept"
    # The card carries the topic's own content: its name in
    # the answer line and its worked example in the steps.
    from topics_data import TOPICS_BY_CLASS
    topic = next(t for ts in TOPICS_BY_CLASS.values()
                 for t in ts if t["slug"] == slug)
    assert topic["name"] in str(res.get("answer", ""))
    steps = res.get("steps") or []
    assert any(s.startswith("Example") for s in steps), steps
    assert any(topic["answer"] in s for s in steps), steps


def test_difference_answer_carries_both_topics():
    res = _solve_friendly(
        "compound interest aur simple interest me kya antar hai?")
    assert res.get("source") == "topics"
    assert res.get("topic_slug") == "simple-interest"
    assert res.get("topic_slug_b") == "compound-interest"
    blob = str(res.get("answer", "")) + " " + \
        " ".join(res.get("steps") or [])
    assert "Simple Interest" in blob
    assert "Compound Interest" in blob


def test_ap_gp_difference_answer():
    res = _solve_friendly(
        "guru AP aur GP me confuse ho gaya hu, fark bta do?")
    assert res.get("source") == "topics"
    assert {res.get("topic_slug"), res.get("topic_slug_b")} == \
        {"nth-term-of-an-ap", "geometric-progressions"}


# --- Honest fall-through: no confident topic, no capture ----
# These keep exactly today's behaviour (a concepts.py card or
# the not-found line) — the layer must return None for them.

FALL_THROUGH = [
    "what is a theorem",                    # no generic topic
    "derivative kya hota hai yr?",          # no definition topic
    "polynomial ki degree kya hoti hai?",   # no degree topic
    "ratio aur proportion me kya fark hai?",
    "congruent aur similar triangles me kya fark hai?",
    "surface area aur volume me kya antar hai?",
    "sequence aur series me kya antar hai?",
    "rekha aur rekha khand me kya antar hai?",
    "discount kese kaam karta hai dukaan par?",
    "iota (i) kya hai aur kyun banaya gaya?",
    "what is the difference between a square and a rectangle?",
]


@pytest.mark.parametrize("question", FALL_THROUGH)
def test_unmatched_concept_asks_fall_through(question):
    assert topic_concept_result(question) is None


# --- Hijack guards: concrete problems ------------------------
# At the LAYER level each of these must return None — the
# words "formula" / "difference" / a concept name must never
# capture a problem that carries numbers to compute with.

LAYER_VETOED = [
    "using the quadratic formula solve x^2 - 3x + 2 = 0",
    "द्विघात सूत्र का उपयोग कर समीकरण x² + 7x − 60 = 0 का मूल निकालें।",
    "find the difference between 45 and 17",
    "what is the difference between 250 and 175?",
    "what is the HCF of 12 and 18",
    "Find the mean of 3, 6, 9, 12.",
    "can u tell the volume of a cuboid 9 x 6 x 5 cm?",
    "Sphere ka radius 7 cm hai to uska surface area find karo?",
    "oye 1/2 + 1/3 kitna hoga plz yr?",
    "A lot consists of 200 pens of which 180 are good. What is "
    "the probability that the customer will not buy it?",
    "ek thaili me 3 laal 2 safed gende hain, safed aane ki "
    "probability kitni thi?",
    "The sum of first n odd natural numbers is (A) n² − 1 "
    "(B) n + 1 (C) 2n − 1 (D) n²",
    "बिन्दुओं (5, −6) और (−1, −4) को जोड़ने वाले रेखाखंड को "
    "x-अक्ष किस अनुपात में विभाजित करती है?",
    "अभिकथन (A): √3 एक अपरिमेय संख्या का उदाहरण है। कारण (R): "
    "सभी धनात्मक पूर्णांकों के वर्गमूल अपरिमेय संख्या होती हैं।",
    "Prove that: √(1 + sin A)/√(1 − sin A) = sec A + tan A.",
    "Check Whether 301 is a term of the list of numbers "
    "5, 11, 17, 23, … ?",
    "240 ka 15 parsent ktna hoga?",
]


@pytest.mark.parametrize("question", LAYER_VETOED)
def test_layer_never_captures_concrete_problems(question):
    assert topic_concept_result(question) is None


# And end-to-end, the concrete problems still solve
# numerically through the normal path, untouched.

NUMERIC_SOLVES = {
    "what is the HCF of 12 and 18": "6",
    "Find the mean of 3, 6, 9, 12.": "7.5",
    "Find the area of a circle with radius 7 cm.":
        "49·pi ≈ 153.9380",
    "Solve x^2 - 5x + 6 = 0": "x = 2, x = 3",
    "find the difference between 45 and 17": "28",
    "what is the difference between 250 and 175?": "75",
    "What is 15% of 240?": "36",
    "using the quadratic formula solve x^2 - 3x + 2 = 0":
        "x = 1, x = 2",
}


@pytest.mark.parametrize("question,want", NUMERIC_SOLVES.items())
def test_concrete_problems_still_solve_numerically(question, want):
    res = _solve_friendly(question)
    assert res.get("source") != "topics"
    # A plain solver answer — or, for the chat-wrapped
    # quadratic, the pre-existing salvage of its maths part.
    # Never the concept layer.
    assert res.get("fallback_kind") in (None, "salvage"), \
        res.get("fallback_kind")
    assert want in str(res.get("answer", "")), res.get("answer")
