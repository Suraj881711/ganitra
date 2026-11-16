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

__all__ = ["PROOFS"]
