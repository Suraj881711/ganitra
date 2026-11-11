"""Wave 18: curated concept answers for Ganitra's no-dead-end layer.

A small, hand-checked library of the concept questions Class 0-12
students ask most ("pythagoras theorem kya hai", "what is BODMAS",
"simple interest ka formula"...). The rule-based solver cannot
answer "what is X" questions — it either fails or, worse,
letter-multiplies the words into nonsense — so fallback.py matches
these asks by keyword (English / Hindi / Hinglish) and serves the
entry here.

Every entry is standard textbook content, kept simple and correct
rather than broad and shaky:

    id        stable key (also the result's "op")
    keywords  lowercase substrings matched against the question
    title     short English title (the answer line's lead)
    formula   the one formula/fact that matters most
    explain   one-two plain-English lines
    hinglish  the same idea in one Roman-Hindi line
    example   ONE tiny fully-worked example: q, steps, answer

fallback.py renders: answer = title + formula, steps = explanation
+ worked example. Nothing here pretends to be the answer to a
different numeric question — these entries trigger only on
concept-style asks (see fallback.py's gating).
"""

CONCEPTS = [
    {
        "id": "pythagoras",
        "keywords": ("pythagoras", "पाइथागोरस", "paithagoras"),
        "title": "Pythagoras Theorem",
        "formula": "In a right-angled triangle: (hypotenuse)² = "
                   "(base)² + (perpendicular)², i.e. c² = a² + b²",
        "explain": "It works only for right-angled triangles (one "
                   "angle = 90°). The longest side, opposite the "
                   "right angle, is the hypotenuse.",
        "hinglish": "Samkon tribhuj me karn (sabse lambi side) ka "
                    "varg baaki do side ke vargo ke yog ke barabar "
                    "hota hai.",
        "example": {
            "q": "A right triangle has sides 3 cm and 4 cm. Find "
                 "the hypotenuse.",
            "steps": ["c² = 3² + 4² = 9 + 16 = 25",
                      "c = √25 = 5"],
            "answer": "Hypotenuse = 5 cm",
        },
    },
    {
        "id": "quadratic_formula",
        "keywords": ("quadratic formula", "द्विघात सूत्र",
                     "dvighat sutra", "shridharacharya",
                     "श्रीधराचार्य"),
        "title": "Quadratic Formula",
        "formula": "For ax² + bx + c = 0:  x = (-b ± √(b² - 4ac)) "
                   "/ (2a)",
        "explain": "Use it when a quadratic equation does not "
                   "factorise easily. The part under the root, "
                   "b² - 4ac, is called the discriminant.",
        "hinglish": "Jab dvighat samikaran aasani se factor na ho, "
                    "to ye sutra seedha dono mool (roots) de deta "
                    "hai.",
        "example": {
            "q": "Solve x² - 5x + 6 = 0 by the quadratic formula.",
            "steps": ["Here a = 1, b = -5, c = 6",
                      "b² - 4ac = 25 - 24 = 1",
                      "x = (5 ± √1) / 2 = (5 ± 1) / 2"],
            "answer": "x = 3 or x = 2",
        },
    },
    {
        "id": "discriminant",
        "keywords": ("discriminant", "विविक्तकर", "nature of roots",
                     "nature of the roots", "मूलों की प्रकृति",
                     "moolon ki prakriti", "mulon ki prakriti"),
        "title": "Discriminant & Nature of Roots",
        "formula": "D = b² - 4ac  (for ax² + bx + c = 0)",
        "explain": "D > 0: two different real roots. D = 0: two "
                   "equal real roots. D < 0: no real roots.",
        "hinglish": "D batata hai ki dvighat samikaran ke mool "
                    "asli honge ya nahi, aur barabar honge ya alag.",
        "example": {
            "q": "Find the nature of roots of x² - 3x + 2 = 0.",
            "steps": ["a = 1, b = -3, c = 2",
                      "D = (-3)² - 4×1×2 = 9 - 8 = 1",
                      "D = 1 > 0"],
            "answer": "Two different real roots (they are 1 and 2)",
        },
    },
    {
        "id": "trig_identity",
        "keywords": ("sin^2", "sin²", "sin 2 + cos",
                     "trig identity", "trigonometric identity",
                     "त्रिकोणमितीय सर्वसमिका"),
        "title": "Trigonometric Identity: sin²θ + cos²θ = 1",
        "formula": "sin²θ + cos²θ = 1 (true for every angle θ)",
        "explain": "Proof sketch: in a right triangle with "
                   "hypotenuse h, sinθ = opposite/h and cosθ = "
                   "adjacent/h, so sin²θ + cos²θ = (opp² + adj²)/h². "
                   "By Pythagoras opp² + adj² = h², so the value "
                   "is h²/h² = 1.",
        "hinglish": "Ye har angle ke liye hamesha sach hai — "
                    "Pythagoras theorem se hi banta hai.",
        "example": {
            "q": "Check the identity for θ = 30°.",
            "steps": ["sin 30° = 1/2, cos 30° = √3/2",
                      "sin²30° + cos²30° = 1/4 + 3/4 = 1"],
            "answer": "1 ✓ (identity holds)",
        },
    },
    {
        "id": "root2_irrational",
        "keywords": ("irrational", "अपरिमेय", "aparimey",
                     "root 2", "√2", "sqrt 2"),
        "title": "√2 is Irrational — proof idea",
        "formula": "A rational number can be written as p/q with "
                   "p, q whole numbers and no common factor; √2 "
                   "cannot.",
        "explain": "Proof by contradiction: suppose √2 = p/q in "
                   "lowest terms. Then p² = 2q², so p² is even, so "
                   "p is even; write p = 2r. Then 4r² = 2q², so "
                   "q² = 2r², so q is also even — but p and q were "
                   "supposed to have no common factor. Contradiction, "
                   "so √2 is irrational.",
        "hinglish": "Maan lo √2 = p/q hai; phir p bhi even aur q "
                    "bhi even nikalta hai — ye 'sabse chhota roop' "
                    "wali baat ke khilaf hai, isliye √2 aparimey "
                    "hai.",
        "example": {
            "q": "Is 2/3 rational or irrational?",
            "steps": ["2/3 is already in the form p/q",
                      "So it is a rational number"],
            "answer": "2/3 is rational; √2 is not",
        },
    },
    {
        "id": "area_circle",
        "keywords": ("area of circle", "area of a circle",
                     "वृत्त का क्षेत्रफल", "vritt ka kshetrafal",
                     "circle ka area", "circumference",
                     "वृत्त की परिधि", "circle ki paridhi"),
        "title": "Circle: Area & Circumference",
        "formula": "Area = πr²,  Circumference = 2πr  (r = radius)",
        "explain": "Use π = 22/7 when the radius is a multiple of "
                   "7, otherwise π ≈ 3.14.",
        "hinglish": "Vritt ka kshetrafal πr² hota hai aur paridhi "
                    "(ghera) 2πr hoti hai.",
        "example": {
            "q": "Find the area of a circle with radius 7 cm.",
            "steps": ["Area = πr² = (22/7) × 7 × 7",
                      "= 22 × 7 = 154"],
            "answer": "Area = 154 cm²",
        },
    },
    {
        "id": "area_triangle",
        "keywords": ("area of triangle", "area of a triangle",
                     "त्रिभुज का क्षेत्रफल", "tribhuj ka kshetrafal",
                     "triangle ka area", "heron"),
        "title": "Area of a Triangle",
        "formula": "Area = ½ × base × height",
        "explain": "The height must be the perpendicular distance "
                   "from the opposite corner to the base.",
        "hinglish": "Tribhuj ka kshetrafal aadha × aadhaar × "
                    "unchai hota hai.",
        "example": {
            "q": "Find the area of a triangle with base 10 cm and "
                 "height 6 cm.",
            "steps": ["Area = ½ × 10 × 6", "= 30"],
            "answer": "Area = 30 cm²",
        },
    },
    {
        "id": "area_rect_square",
        "keywords": ("area of rectangle", "area of a rectangle",
                     "area of square", "area of a square",
                     "perimeter of rectangle",
                     "perimeter of square",
                     "आयत का क्षेत्रफल", "वर्ग का क्षेत्रफल",
                     "aayat ka kshetrafal", "varg ka kshetrafal",
                     "rectangle ka area", "square ka area",
                     "rectangle ka perimeter", "square ka perimeter"),
        "title": "Rectangle & Square: Area and Perimeter",
        "formula": "Rectangle: Area = length × breadth, "
                   "Perimeter = 2(length + breadth).  "
                   "Square: Area = side², Perimeter = 4 × side",
        "explain": "Area counts the surface covered (square "
                   "units); perimeter is the total boundary length.",
        "hinglish": "Aayat ka kshetrafal lambai × chaudai, aur "
                    "parimap (chaaron side ka yog) 2(lambai + "
                    "chaudai) hota hai.",
        "example": {
            "q": "A rectangle is 8 cm long and 5 cm wide. Find "
                 "its area and perimeter.",
            "steps": ["Area = 8 × 5 = 40",
                      "Perimeter = 2 × (8 + 5) = 26"],
            "answer": "Area = 40 cm², Perimeter = 26 cm",
        },
    },
    {
        "id": "hcf_lcm",
        "keywords": ("hcf", "lcm", "महत्तम समापवर्तक",
                     "लघुत्तम समापवर्त्य", "highest common factor",
                     "lowest common multiple",
                     "least common multiple"),
        "title": "HCF and LCM",
        "formula": "HCF = largest number dividing all the given "
                   "numbers; LCM = smallest number divisible by "
                   "all of them. For two numbers: HCF × LCM = "
                   "first number × second number.",
        "explain": "Find them from prime factors: HCF takes the "
                   "smallest power of each common prime, LCM the "
                   "largest power of every prime.",
        "hinglish": "HCF sabse badi sankhya hai jo sabko baant-ti "
                    "hai; LCM sabse chhoti sankhya hai jo sabse "
                    "baant-ti jaati hai.",
        "example": {
            "q": "Find the HCF and LCM of 12 and 18.",
            "steps": ["12 = 2² × 3,  18 = 2 × 3²",
                      "HCF = 2 × 3 = 6",
                      "LCM = 2² × 3² = 36",
                      "Check: 6 × 36 = 216 = 12 × 18 ✓"],
            "answer": "HCF = 6, LCM = 36",
        },
    },
    {
        "id": "prime_composite",
        "keywords": ("prime number", "composite number",
                     "अभाज्य संख्या", "भाज्य संख्या",
                     "abhaajy", "abajya", "abhayj"),
        "title": "Prime and Composite Numbers",
        "formula": "Prime: a number greater than 1 with exactly "
                   "two factors — 1 and itself. Composite: a "
                   "number with more than two factors.",
        "explain": "1 is neither prime nor composite. 2 is the "
                   "only even prime number.",
        "hinglish": "Jis sankhya ke sirf 2 gunankhand hon (1 aur "
                    "wo khud) wo abhaajy hai; zyada hon to bhaajy.",
        "example": {
            "q": "Is 7 prime? Is 9 prime?",
            "steps": ["Factors of 7: 1, 7 — only two, so 7 is "
                      "prime",
                      "Factors of 9: 1, 3, 9 — three, so 9 is "
                      "composite"],
            "answer": "7 is prime; 9 is composite",
        },
    },
    {
        "id": "bodmas",
        "keywords": ("bodmas", "बोडमास", "order of operations"),
        "title": "BODMAS — Order of Operations",
        "formula": "Solve in this order: Brackets → Orders "
                   "(powers/roots) → Division → Multiplication → "
                   "Addition → Subtraction",
        "explain": "Division and multiplication have equal rank "
                   "(go left to right), and so do addition and "
                   "subtraction.",
        "hinglish": "Pehle koshthak, phir ghaat, phir bhaag-guna "
                    "(baayein se daayein), aakhir me jod-ghatao.",
        "example": {
            "q": "Find 2 + 3 × 4.",
            "steps": ["Multiplication before addition: 3 × 4 = 12",
                      "2 + 12 = 14"],
            "answer": "14 (not 20 — never add first here)",
        },
    },
    {
        "id": "simple_interest",
        "keywords": ("simple interest", "साधारण ब्याज",
                     "sadharan byaj", "saadharan byaaj"),
        "title": "Simple Interest",
        "formula": "SI = (P × R × T) / 100,  Amount = P + SI",
        "explain": "P = principal (starting money), R = rate % "
                   "per year, T = time in years. The interest is "
                   "the same every year.",
        "hinglish": "Sadharan byaj mooldhan par har saal ek jaisa "
                    "lagta hai: SI = P×R×T/100.",
        "example": {
            "q": "Find the simple interest on ₹1,000 at 5% per "
                 "year for 2 years.",
            "steps": ["SI = (1000 × 5 × 2) / 100", "= 100"],
            "answer": "SI = ₹100, Amount = ₹1,100",
        },
    },
    {
        "id": "percentage",
        "keywords": ("percentage", "प्रतिशत", "pratishat",
                     "percent kya", "percent kaise"),
        "title": "Percentage",
        "formula": "x% of N = (x/100) × N;  Percentage = "
                   "(part / whole) × 100",
        "explain": "Percent means 'out of 100'. To find what "
                   "percent one number is of another, divide and "
                   "multiply by 100.",
        "hinglish": "Pratishat ka matlab hai 'har 100 me kitna'. "
                    "Hisab: bhaag do aur 100 se guna kar do.",
        "example": {
            "q": "Find 15% of 200.",
            "steps": ["15% of 200 = (15/100) × 200",
                      "= 15 × 2 = 30"],
            "answer": "30",
        },
    },
    {
        "id": "mean_median_mode",
        "keywords": ("mean median mode", "median", "mode kya",
                     "mean kya", "माध्य", "माध्यिका", "बहुलक",
                     "maadhya", "ausat aur"),
        "title": "Mean, Median and Mode",
        "formula": "Mean = (sum of all values) / (number of "
                   "values); Median = middle value after sorting; "
                   "Mode = value that appears most often",
        "explain": "For the median, always arrange the data in "
                   "order first. If two values sit in the middle, "
                   "the median is their average.",
        "hinglish": "Mean = sab ka yog ÷ kul sankhya; Median = "
                    "beech wali sankhya (saja kar); Mode = sabse "
                    "zyada baar aane wali sankhya.",
        "example": {
            "q": "Find the mean, median and mode of 2, 4, 4, 6, 8.",
            "steps": ["Mean = (2+4+4+6+8)/5 = 24/5 = 4.8",
                      "Median (middle value) = 4",
                      "Mode (appears twice) = 4"],
            "answer": "Mean = 4.8, Median = 4, Mode = 4",
        },
    },
    {
        "id": "probability",
        "keywords": ("probability", "प्रायिकता", "prayikta",
                     "prayekta"),
        "title": "Probability",
        "formula": "Probability = (number of favourable outcomes) "
                   "/ (total number of equally likely outcomes)",
        "explain": "The answer is always between 0 (impossible) "
                   "and 1 (certain). It is often written as a "
                   "fraction.",
        "hinglish": "Prayikta = manchahi ghatna ke mauke ÷ kul "
                    "mauke. Jawab hamesha 0 se 1 ke beech hota hai.",
        "example": {
            "q": "A die is thrown. What is the probability of "
                 "getting a 6?",
            "steps": ["Favourable outcomes: only 6 → 1",
                      "Total outcomes: 1, 2, 3, 4, 5, 6 → 6",
                      "Probability = 1/6"],
            "answer": "1/6",
        },
    },
    {
        "id": "ap_gp",
        "keywords": ("arithmetic progression",
                     "geometric progression", "nth term",
                     "n-th term", "समांतर श्रेढ़ी", "गुणोत्तर श्रेढ़ी",
                     "samaantar shreni", "ap ka formula",
                     "gp ka formula"),
        "title": "AP and GP: nth Term",
        "formula": "AP: aₙ = a + (n - 1)d  (same difference d "
                   "added each time).  GP: aₙ = a × r^(n-1)  "
                   "(same ratio r multiplied each time)",
        "explain": "Here a is the first term and n is the "
                   "position of the term you want.",
        "hinglish": "AP me har baar ek hi antar judta hai, GP me "
                    "ek hi sankhya se guna hota rehta hai.",
        "example": {
            "q": "Find the 10th term of the AP 2, 5, 8, ...",
            "steps": ["a = 2, d = 5 - 2 = 3",
                      "a₁₀ = 2 + (10 - 1) × 3 = 2 + 27 = 29"],
            "answer": "10th term = 29",
        },
    },
    {
        "id": "speed_distance_time",
        "keywords": ("speed distance", "distance speed",
                     "चाल और दूरी", "chaal doori", "chaal aur doori",
                     "speed ka formula", "distance ka formula"),
        "title": "Speed, Distance and Time",
        "formula": "Distance = Speed × Time;  Speed = Distance / "
                   "Time;  Time = Distance / Speed",
        "explain": "Keep the units together: km with hours gives "
                   "km/h. To change km/h into m/s, multiply by "
                   "5/18.",
        "hinglish": "Doori = chaal × samay. Unit ka dhyaan rakho: "
                    "km/h ko m/s banane ke liye 5/18 se guna karo.",
        "example": {
            "q": "A bus travels at 40 km/h for 3 hours. How far "
                 "does it go?",
            "steps": ["Distance = Speed × Time = 40 × 3",
                      "= 120"],
            "answer": "120 km",
        },
    },
    {
        "id": "trigonometry_basics",
        "keywords": ("trigonometry", "त्रिकोणमिति",
                     "trikonmiti"),
        "title": "Trigonometry — the Basic Ratios",
        "formula": "In a right triangle, for angle θ:  sin θ = "
                   "opposite/hypotenuse,  cos θ = "
                   "adjacent/hypotenuse,  tan θ = opposite/adjacent",
        "explain": "Trigonometry connects the angles of a "
                   "triangle with the lengths of its sides. The "
                   "famous values: sin 30° = 1/2, cos 60° = 1/2, "
                   "tan 45° = 1.",
        "hinglish": "Trikonmiti samkon tribhuj ke kon aur side ke "
                    "beech ka rishta batati hai — sin, cos, tan "
                    "teen mukhya anupaat hain.",
        "example": {
            "q": "What is sin 30°?",
            "steps": ["From the standard value table, "
                      "sin 30° = 1/2"],
            "answer": "sin 30° = 1/2",
        },
    },
    {
        "id": "algebra_basics",
        "keywords": ("algebra", "बीजगणित", "beejganit",
                     "bijganit"),
        "title": "Algebra — Letters for Numbers",
        "formula": "In algebra, letters like x stand for unknown "
                   "numbers. An equation like 2x + 3 = 11 stays "
                   "balanced when you do the same thing to both "
                   "sides.",
        "explain": "To find x, undo the steps in reverse: "
                   "subtract 3 from both sides, then divide by 2.",
        "hinglish": "Beejganit me akshar (x, y) anjaan sankhyaon "
                    "ke liye hote hain; samikaran ek tarazu hai — "
                    "jo ek taraf karo, wahi dusri taraf bhi.",
        "example": {
            "q": "Solve 2x + 3 = 11.",
            "steps": ["2x = 11 - 3 = 8",
                      "x = 8 / 2 = 4"],
            "answer": "x = 4",
        },
    },
    {
        "id": "factorial",
        "keywords": ("factorial", "फैक्टोरियल"),
        "title": "Factorial",
        "formula": "n! = n × (n - 1) × (n - 2) × ... × 2 × 1, "
                   "and 0! = 1",
        "explain": "The factorial of a whole number is the "
                   "product of all whole numbers from n down to "
                   "1. It is used in permutations and combinations.",
        "hinglish": "n! ka matlab hai n se 1 tak ki sab sankhyaon "
                    "ka guna — jaise 4! = 4×3×2×1 = 24.",
        "example": {
            "q": "Find 5!",
            "steps": ["5! = 5 × 4 × 3 × 2 × 1",
                      "= 120"],
            "answer": "5! = 120",
        },
    },
    {
        "id": "theorem_meaning",
        "keywords": ("theorem", "प्रमेय", "pramey"),
        "title": "What is a Theorem?",
        "formula": "A theorem is a maths statement that has been "
                   "PROVED true using logic and already-known "
                   "facts.",
        "explain": "A theorem is not a guess: it comes with a "
                   "proof. The most famous school example is the "
                   "Pythagoras theorem.",
        "hinglish": "Pramey wo baat hai jo tark (logic) se siddh "
                    "(prove) ki gayi ho — andaza nahi, saboot ke "
                    "saath wali baat.",
        "example": {
            "q": "Name one theorem.",
            "steps": ["Pythagoras theorem: in a right triangle, "
                      "c² = a² + b²",
                      "It has a full proof, so it is a theorem"],
            "answer": "Pythagoras theorem is a theorem",
        },
    },
]

_BY_ID = {c["id"]: c for c in CONCEPTS}


def find_concept(question):
    """Return the concept entry whose keyword appears in the
    question (case-insensitive substring match), else None.
    Longer/more specific keywords are checked by list order —
    specific entries (trig identity, root-2) sit before the
    general ones they could be confused with only where their
    keywords genuinely overlap."""
    q = str(question or "").lower()
    for entry in CONCEPTS:
        for kw in entry["keywords"]:
            if kw in q:
                return entry
    return None


def get_concept(concept_id):
    return _BY_ID.get(concept_id)


__all__ = ["CONCEPTS", "find_concept", "get_concept"]
