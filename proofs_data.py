"""Wave 95, tier 2: standard textbook proofs served as content.

Only results whose proof is a fixed, classical text — the
irrationality of sqrt(2), sqrt(3) and sqrt(5) by contradiction
(NCERT Class 10, Real Numbers). The lines below are the standard
school proof, written out in full; nothing here is generated or
guessed. Each proof exists in English and in Hindi (Devanagari);
a Hinglish (Roman) ask is served the English text — recorded as
an honest limit in the wave notes.

Keys are the radicands as strings ("2", "3", "5"). Matching is
done by proofs.py, never by keyword soup: the question must be
a proof ask AND name exactly one of these roots as irrational.

Wave 101 adds PYTHAGOREAN_PROOFS below: the three Pythagorean
identities, proved genuinely — sin²+cos² from a right-angled
triangle (Pythagoras' theorem, then divide by the hypotenuse
squared), the other two FROM sin²+cos² = 1 by dividing every
term by cos² / sin². Wave 95's SymPy transform path proved
sin²+cos² = 1 with a single step labelled "using sin²x + cos²x
= 1" — the identity citing itself — so these three are served
as textbook content instead. The "{v}" token is the student's
own variable (A, θ, x, ...), substituted by proofs.py; the
matching there is structural (the parsed statement must be
exactly one of these identities, in any arrangement), never
keyword soup either.
"""

PROOFS = {
    "2": {
        "statement": {
            "en": "√2 is irrational",
            "hi": "√2 अपरिमेय है",
        },
        "steps": {
            "en": [
                "We prove this by contradiction. Suppose √2 is rational.",
                "Then √2 = a/b, where a and b are co-prime positive "
                "integers (b ≠ 0) — the fraction is in its lowest form.",
                "So a² = 2b², which means a² is even, and therefore "
                "a itself is even. Write a = 2c.",
                "Then (2c)² = 2b², so 4c² = 2b², so b² = 2c² — "
                "which means b² is even, and therefore b is also even.",
                "So a and b are both even: they share the common "
                "factor 2. But we assumed a and b are co-prime — "
                "a contradiction.",
                "Therefore our supposition is wrong, and √2 is "
                "irrational. ∎",
            ],
            "hi": [
                "हम इसे विरोधाभास (contradiction) से सिद्ध करते हैं। "
                "मान लीजिए √2 एक परिमेय संख्या है।",
                "तब √2 = a/b, जहाँ a और b सह-अभाज्य धनात्मक पूर्णांक "
                "हैं (b ≠ 0) — अर्थात भिन्न अपने सरलतम रूप में है।",
                "तो a² = 2b², अर्थात a² सम है, इसलिए a भी सम है। "
                "मान लीजिए a = 2c।",
                "तब (2c)² = 2b², अर्थात 4c² = 2b², अर्थात b² = 2c² — "
                "इससे b² सम है, इसलिए b भी सम है।",
                "अर्थात a और b दोनों सम हैं — दोनों में 2 उभयनिष्ठ "
                "गुणनखंड है। लेकिन हमने माना था कि a और b सह-अभाज्य "
                "हैं — यह विरोधाभास है।",
                "अतः हमारी मान्यता गलत है, और √2 अपरिमेय है। ∎",
            ],
        },
    },
    "3": {
        "statement": {
            "en": "√3 is irrational",
            "hi": "√3 अपरिमेय है",
        },
        "steps": {
            "en": [
                "We prove this by contradiction. Suppose √3 is rational.",
                "Then √3 = a/b, where a and b are co-prime positive "
                "integers (b ≠ 0) — the fraction is in its lowest form.",
                "So a² = 3b², which means 3 divides a², and therefore "
                "3 divides a. Write a = 3c.",
                "Then (3c)² = 3b², so 9c² = 3b², so b² = 3c² — "
                "which means 3 divides b², and therefore 3 divides b.",
                "So 3 divides both a and b: they share the common "
                "factor 3. But we assumed a and b are co-prime — "
                "a contradiction.",
                "Therefore our supposition is wrong, and √3 is "
                "irrational. ∎",
            ],
            "hi": [
                "हम इसे विरोधाभास (contradiction) से सिद्ध करते हैं। "
                "मान लीजिए √3 एक परिमेय संख्या है।",
                "तब √3 = a/b, जहाँ a और b सह-अभाज्य धनात्मक पूर्णांक "
                "हैं (b ≠ 0) — अर्थात भिन्न अपने सरलतम रूप में है।",
                "तो a² = 3b², अर्थात 3, a² को विभाजित करता है, इसलिए "
                "3, a को भी विभाजित करता है। मान लीजिए a = 3c।",
                "तब (3c)² = 3b², अर्थात 9c² = 3b², अर्थात b² = 3c² — "
                "इससे 3, b² को विभाजित करता है, इसलिए 3, b को भी "
                "विभाजित करता है।",
                "अर्थात 3, a और b दोनों को विभाजित करता है — दोनों "
                "में 3 उभयनिष्ठ गुणनखंड है। लेकिन हमने माना था कि a "
                "और b सह-अभाज्य हैं — यह विरोधाभास है।",
                "अतः हमारी मान्यता गलत है, और √3 अपरिमेय है। ∎",
            ],
        },
    },
    "5": {
        "statement": {
            "en": "√5 is irrational",
            "hi": "√5 अपरिमेय है",
        },
        "steps": {
            "en": [
                "We prove this by contradiction. Suppose √5 is rational.",
                "Then √5 = a/b, where a and b are co-prime positive "
                "integers (b ≠ 0) — the fraction is in its lowest form.",
                "So a² = 5b², which means 5 divides a², and therefore "
                "5 divides a. Write a = 5c.",
                "Then (5c)² = 5b², so 25c² = 5b², so b² = 5c² — "
                "which means 5 divides b², and therefore 5 divides b.",
                "So 5 divides both a and b: they share the common "
                "factor 5. But we assumed a and b are co-prime — "
                "a contradiction.",
                "Therefore our supposition is wrong, and √5 is "
                "irrational. ∎",
            ],
            "hi": [
                "हम इसे विरोधाभास (contradiction) से सिद्ध करते हैं। "
                "मान लीजिए √5 एक परिमेय संख्या है।",
                "तब √5 = a/b, जहाँ a और b सह-अभाज्य धनात्मक पूर्णांक "
                "हैं (b ≠ 0) — अर्थात भिन्न अपने सरलतम रूप में है।",
                "तो a² = 5b², अर्थात 5, a² को विभाजित करता है, इसलिए "
                "5, a को भी विभाजित करता है। मान लीजिए a = 5c।",
                "तब (5c)² = 5b², अर्थात 25c² = 5b², अर्थात b² = 5c² — "
                "इससे 5, b² को विभाजित करता है, इसलिए 5, b को भी "
                "विभाजित करता है।",
                "अर्थात 5, a और b दोनों को विभाजित करता है — दोनों "
                "में 5 उभयनिष्ठ गुणनखंड है। लेकिन हमने माना था कि a "
                "और b सह-अभाज्य हैं — यह विरोधाभास है।",
                "अतः हमारी मान्यता गलत है, और √5 अपरिमेय है। ∎",
            ],
        },
    },
}

PYTHAGOREAN_PROOFS = {
    "sin_cos": {
        "statement": {
            "en": "sin²{v} + cos²{v} = 1",
            "hi": "sin²{v} + cos²{v} = 1",
        },
        "steps": {
            "en": [
                "Take a right-angled triangle whose one acute "
                "angle is {v}. Call the side opposite {v} (the "
                "perpendicular) p, the side next to {v} (the "
                "base) b, and the hypotenuse h.",
                "Then sin {v} = p/h and cos {v} = b/h, so "
                "sin²{v} + cos²{v} = p²/h² + b²/h² = (p² + b²)/h².",
                "By Pythagoras' theorem for this triangle, "
                "p² + b² = h².",
                "So sin²{v} + cos²{v} = h²/h² = 1.",
            ],
            "hi": [
                "एक समकोण त्रिभुज लीजिए जिसका एक न्यून कोण {v} "
                "है। {v} के सामने वाली भुजा (लंब) को p, {v} से "
                "सटी भुजा (आधार) को b और कर्ण को h मानिए।",
                "तब sin {v} = p/h और cos {v} = b/h, अतः "
                "sin²{v} + cos²{v} = p²/h² + b²/h² = (p² + b²)/h²।",
                "इस त्रिभुज के लिए पाइथागोरस प्रमेय से, "
                "p² + b² = h²।",
                "अतः sin²{v} + cos²{v} = h²/h² = 1।",
            ],
        },
    },
    "sec_tan": {
        "statement": {
            "en": "sec²{v} − tan²{v} = 1",
            "hi": "sec²{v} − tan²{v} = 1",
        },
        "steps": {
            "en": [
                "Start from sin²{v} + cos²{v} = 1 — the "
                "right-triangle identity (perpendicular² + "
                "base² = hypotenuse², divided by hypotenuse²).",
                "Divide every term by cos²{v}: "
                "sin²{v}/cos²{v} + cos²{v}/cos²{v} = 1/cos²{v}.",
                "Now sin {v}/cos {v} = tan {v} and "
                "1/cos {v} = sec {v}, so this says "
                "tan²{v} + 1 = sec²{v}.",
                "Rearranging, sec²{v} − tan²{v} = 1.",
            ],
            "hi": [
                "sin²{v} + cos²{v} = 1 से शुरू करते हैं — यह "
                "समकोण त्रिभुज वाली सर्वसमिका है (लंब² + आधार² "
                "= कर्ण², कर्ण² से भाग देने पर)।",
                "प्रत्येक पद को cos²{v} से भाग देने पर: "
                "sin²{v}/cos²{v} + cos²{v}/cos²{v} = 1/cos²{v}।",
                "अब sin {v}/cos {v} = tan {v} और "
                "1/cos {v} = sec {v}, अतः tan²{v} + 1 = sec²{v}।",
                "पक्ष बदलने पर, sec²{v} − tan²{v} = 1।",
            ],
        },
    },
    "cosec_cot": {
        "statement": {
            "en": "cosec²{v} − cot²{v} = 1",
            "hi": "cosec²{v} − cot²{v} = 1",
        },
        "steps": {
            "en": [
                "Start from sin²{v} + cos²{v} = 1 — the "
                "right-triangle identity (perpendicular² + "
                "base² = hypotenuse², divided by hypotenuse²).",
                "Divide every term by sin²{v}: "
                "sin²{v}/sin²{v} + cos²{v}/sin²{v} = 1/sin²{v}.",
                "Now cos {v}/sin {v} = cot {v} and "
                "1/sin {v} = cosec {v}, so this says "
                "1 + cot²{v} = cosec²{v}.",
                "Rearranging, cosec²{v} − cot²{v} = 1.",
            ],
            "hi": [
                "sin²{v} + cos²{v} = 1 से शुरू करते हैं — यह "
                "समकोण त्रिभुज वाली सर्वसमिका है (लंब² + आधार² "
                "= कर्ण², कर्ण² से भाग देने पर)।",
                "प्रत्येक पद को sin²{v} से भाग देने पर: "
                "sin²{v}/sin²{v} + cos²{v}/sin²{v} = 1/sin²{v}।",
                "अब cos {v}/sin {v} = cot {v} और "
                "1/sin {v} = cosec {v}, अतः 1 + cot²{v} = cosec²{v}।",
                "पक्ष बदलने पर, cosec²{v} − cot²{v} = 1।",
            ],
        },
    },
}

__all__ = ["PROOFS", "PYTHAGOREAN_PROOFS"]
