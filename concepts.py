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
        "keywords": ("pythagoras", "पाइथागोरस", "paithagoras",
                     "right angled triangle",
                     "right angle triangle", "समकोण त्रिभुज"),
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
                     "श्रीधराचार्य", "द्विघात समीकरण",
                     "quadratic equation"),
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
                     "identity kya",
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
        # Wave 65: sits AFTER root2_irrational on purpose —
        # "अपरिमेय"/"aparimey" asks must keep hitting the
        # irrational entry above; only the bare rational ask
        # ("परिमेय संख्या क्या होती है?", "parimey sankhya
        # matlab kya hota hai", "define a rational number")
        # falls through to here.
        "id": "rational_number",
        "keywords": ("rational number", "rational numbers",
                     "परिमेय", "parimey"),
        "title": "Rational Number (परिमेय संख्या)",
        "formula": "A rational number is any number that "
                   "can be written as p/q, where p and q "
                   "are integers and q ≠ 0.",
        "explain": "3/4, -5, 0.25 and 7 (= 7/1) are all "
                   "rational. Numbers like √2 and π cannot "
                   "be written exactly as p/q, so they are "
                   "irrational.",
        "hinglish": "Jo sankhya p/q ke roop me likhi ja "
                    "sake (q zero na ho), wahi parimey "
                    "sankhya hai.",
        "example": {
            "q": "Is 0.5 a rational number?",
            "steps": ["0.5 = 1/2, which is p/q form"],
            "answer": "Yes, 0.5 is rational",
        },
    },
    {
        "id": "area_circle",
        "keywords": ("area of circle", "area of a circle",
                     "वृत्त का क्षेत्रफल", "वृत्त के क्षेत्रफल",
                     "vritt ka kshetrafal",
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
        # Wave 65: radius/diameter definition asks in all
        # three languages ("वृत्त की त्रिज्या किसे कहते
        # हैं?", "vritt ki trijya kya hoti hai?").
        "id": "radius_diameter",
        "keywords": ("त्रिज्या", "trijya", "व्यास", "vyaas",
                     "what is radius", "what is the radius",
                     "radius kya", "diameter kya",
                     "what is diameter", "what is the diameter"),
        "title": "Radius (त्रिज्या) and Diameter (व्यास)",
        "formula": "Radius = the distance from the centre "
                   "of a circle to any point on it. Diameter "
                   "= 2 × radius — the longest chord, passing "
                   "through the centre.",
        "explain": "Every radius of a circle is equal. If "
                   "the radius is 7 cm, the diameter is "
                   "14 cm.",
        "hinglish": "Kendr se paridhi tak ki doori trijya "
                    "hai; uska dugna vyaas hota hai.",
        "example": {
            "q": "Radius is 5 cm. What is the diameter?",
            "steps": ["Diameter = 2 × 5 = 10 cm"],
            "answer": "Diameter = 10 cm",
        },
    },
    {
        "id": "area_triangle",
        "keywords": ("area of triangle", "area of a triangle",
                     "त्रिभुज का क्षेत्रफल", "tribhuj ka kshetrafal",
                     "triangle ka area", "tribhuj ka area", "heron"),
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
        # Wave 65: the difference ask ("वर्ग और आयत में क्या
        # अंतर है?", "what is the difference between a
        # square and a rectangle?") — the area entry below
        # never matched it.
        "id": "square_vs_rectangle",
        "keywords": ("square and rectangle",
                     "square and a rectangle",
                     "वर्ग और आयत", "वर्ग तथा आयत",
                     "varg aur aayat", "square aur rectangle",
                     "difference between a square and a "
                     "rectangle",
                     "difference between square and rectangle"),
        "title": "Square vs Rectangle (वर्ग बनाम आयत)",
        "formula": "Square: all four sides equal, all "
                   "angles 90°. Rectangle: only opposite "
                   "sides equal, all angles 90°.",
        "explain": "Every square is a rectangle, but a "
                   "rectangle is a square only when all its "
                   "sides become equal. Both have 4 sides, "
                   "4 right angles and equal diagonals.",
        "hinglish": "Varg ki chaaro bhujaayein barabar "
                    "hoti hain; aayat ki sirf aamne-saamne "
                    "wali bhujaayein barabar hoti hain.",
        "example": {
            "q": "Sides 6, 6, 6, 6 — square or rectangle?",
            "steps": ["All four sides are equal and "
                      "angles are 90°"],
            "answer": "It is a square (and also a rectangle)",
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
                     "least common multiple", "hcf aur lcm",
                     "hcf lcm me antar", "hcf kya", "lcm kya"),
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
                     "abhaajy", "abajya", "abhayj", "abhajya", "prime no"),
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
                     "sadharan byaj", "saadharan byaaj", "byaj",
                     "ब्याज", "sadharan byaj kya",
                     "byaj kaise nikalte", "byaj kese"),
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
                     "percent kya", "percent kaise",
                     "percent ka matlab", "pratishat ka matlab",
                     "percent kya hota", "percentage ka matlab"),
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
                     "maadhya", "madhyika", "ausat aur", "ausat",
                     "औसत", "mean aur median", "ausat aur madhyika",
                     "bahulak kya", "bahulak", "mode kya hota",
                     "median kya hota"),
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
                     "prayekta", "संभावना", "sambhavna",
                     "probability kaise", "probability kese",
                     "sambhavna kaise", "probability kya hoti"),
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
                     "समांतर श्रेणी", "ज्यामितीय श्रेणी",
                     "समान्तर श्रेणी", "समान्तर श्रेढ़ी",
                     "samaantar shreni", "ap ka formula",
                     "gp ka formula", "ap kya hoti", "gp kya hoti",
                     "ap kya hota", "gp kya hota", "ap aur gp",
                     "ap kya hai", "gp kya hai", "common difference",
                     "gp ka sum formula", "ap ka nth"),
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
                     "doori samay", "चाल दूरी", "दूरी और समय",
                     "speed ka formula", "distance ka formula",
                     "speed distance time", "chaal doori samay",
                     "speed doori"),
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
                     "trikonmiti", "sin cos tan", "trig ratio",
                     "trikonmiti kya", "trigonometry kya",
                     "cosec", "secant", "cosecant",
                     "sec aur cosec"),
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
                     "bijganit", "samikaran", "गुणनखंड",
                     "gunaankhand"),
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
        "keywords": ("factorial", "फैक्टोरियल", "क्रमगुणित"),
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
    # ---- Wave 59: Hinglish deep-training concept entries ----
    # Appended AFTER the Wave 18 entries: find_concept returns
    # the first match in list order, so every older match keeps
    # winning exactly as before.
    {
        "id": "variance_sd",
        "keywords": ("variance", "standard deviation",
                     "prasaran", "manak vichalan"),
        "title": "Variance and Standard Deviation",
        "formula": "Variance = average of (each value - mean)²; "
                   "Standard Deviation = √Variance",
        "explain": "They measure how spread out the data is. "
                   "SD = 0 means every value is the same.",
        "hinglish": "Data kitna phaila hua hai, ye variance aur "
                    "SD batate hain — zyada SD matlab zyada "
                    "bikhraav.",
        "example": {
            "q": "Find the variance of 2, 4, 6 (mean = 4).",
            "steps": ["Squared gaps: (2-4)², (4-4)², (6-4)² "
                      "= 4, 0, 4",
                      "Variance = (4 + 0 + 4) / 3 = 8/3 ≈ 2.67"],
            "answer": "Variance ≈ 2.67, SD ≈ 1.63",
        },
    },
    {
        "id": "ogive",
        "keywords": ("ogive", "toj"),
        "title": "Ogive (Cumulative Frequency Curve)",
        "formula": "Plot cumulative frequency against the upper "
                   "class limit ('less than' ogive); the median "
                   "is where the two ogives cross.",
        "explain": "An ogive is the smooth curve of running "
                   "totals (cumulative frequencies). It is mainly "
                   "used to read the median from a graph.",
        "hinglish": "Sanchayi barambarta (cumulative frequency) "
                    "ko graph par banane se ogive banta hai — "
                    "isse madhyika aasani se milti hai.",
        "example": {
            "q": "Frequencies 3, 5, 2 — write the cumulative "
                 "frequencies.",
            "steps": ["Running totals: 3, 3 + 5 = 8, 8 + 2 = 10"],
            "answer": "Cumulative frequencies: 3, 8, 10",
        },
    },
    {
        "id": "function_basics",
        "keywords": ("function kya", "function hota",
                     "function ka matlab", "falan kya"),
        "title": "What is a Function?",
        "formula": "A function gives exactly ONE output for "
                   "every input: y = f(x).",
        "explain": "Think of it as a machine: you put in x, you "
                   "get one fixed answer f(x). The same input can "
                   "never give two different outputs.",
        "hinglish": "Function ek machine jaisa hai — ek input "
                    "daalo, hamesha ek hi pakka output milega.",
        "example": {
            "q": "If f(x) = x + 3, find f(5).",
            "steps": ["Put x = 5: f(5) = 5 + 3 = 8"],
            "answer": "f(5) = 8",
        },
    },
    {
        "id": "domain_range",
        "keywords": ("domain aur range", "domain range",
                     "prant aur parisar"),
        "title": "Domain and Range of a Function",
        "formula": "Domain = all allowed inputs (x values); "
                   "Range = all outputs the function actually "
                   "gives.",
        "explain": "Domain asks 'which x can I put in?', range "
                   "asks 'which y values can come out?'.",
        "hinglish": "Domain matlab kaunsi x value daal sakte "
                    "hain, range matlab kaunsi y value bahar "
                    "aayegi.",
        "example": {
            "q": "Domain and range of f(x) = x² (real x)?",
            "steps": ["x can be any real number; x² is never "
                      "negative",
                      "Range = all y ≥ 0"],
            "answer": "Domain = all real numbers, Range = [0, ∞)",
        },
    },
    {
        "id": "surd",
        "keywords": ("surd", "karni"),
        "title": "Surds (Karni)",
        "formula": "A surd is an irrational root: √2, √3, ∛5 — "
                   "roots that cannot be written as a simple "
                   "fraction.",
        "explain": "√4 = 2 is NOT a surd (it comes out exact), "
                   "but √5 is, because it never ends or repeats "
                   "as a decimal.",
        "hinglish": "Jo mool (root) exact na nikle — jaise √2, "
                    "√3 — wahi karni (surd) hai.",
        "example": {
            "q": "Simplify √12.",
            "steps": ["√12 = √(4 × 3) = 2√3"],
            "answer": "√12 = 2√3",
        },
    },
    {
        "id": "radian",
        "keywords": ("radian", "degree kitne radian",
                     "degree aur radian"),
        "title": "Radians",
        "formula": "π radians = 180°, so 1 radian ≈ 57.3° and "
                   "1° = π/180 radian.",
        "explain": "The radian is the SI unit of angle: it is "
                   "the angle made when the arc length equals "
                   "the radius.",
        "hinglish": "Radian kon naapne ki dusri unit hai — π "
                    "radian matlab 180 degree.",
        "example": {
            "q": "Convert 90° to radians.",
            "steps": ["90 × π/180 = π/2"],
            "answer": "90° = π/2 radian",
        },
    },
    {
        "id": "sequence_series",
        "keywords": ("sequence aur series", "sequence aur shreni",
                     "anukram aur shreni", "sequence kya",
                     "series kya"),
        "title": "Sequence vs Series",
        "formula": "Sequence = an ordered list (2, 4, 6, ...); "
                   "Series = the SUM of its terms (2 + 4 + 6).",
        "explain": "Same numbers, two ideas: the list itself is "
                   "the sequence, adding them makes the series.",
        "hinglish": "Anukram sirf kram me likhi sankhyaye hain; "
                    "unhi ka yog bana do to woh shreni (series) "
                    "ho gayi.",
        "example": {
            "q": "Sequence 1, 3, 5 — its series?",
            "steps": ["Add them: 1 + 3 + 5 = 9"],
            "answer": "Series = 1 + 3 + 5 = 9",
        },
    },
    {
        "id": "sets_basics",
        "keywords": ("union aur intersection", "samuchchay",
                     "set kya", "empty set", "universal set",
                     "cardinal number of set"),
        "title": "Sets: Union, Intersection, Empty & Universal",
        "formula": "A ∪ B = elements in A or B; A ∩ B = elements "
                   "in both; n(A) = number of elements in A.",
        "explain": "The empty set { } (or ∅) has no elements; "
                   "the universal set U holds every element "
                   "under discussion.",
        "hinglish": "Union me dono set ke saare tatva, "
                    "intersection me sirf common wale aate hain.",
        "example": {
            "q": "A = {1, 2}, B = {2, 3}. Find A ∪ B and A ∩ B.",
            "steps": ["A ∪ B = {1, 2, 3}", "A ∩ B = {2}"],
            "answer": "A ∪ B = {1, 2, 3}, A ∩ B = {2}",
        },
    },
    {
        "id": "subset_concept",
        "keywords": ("subset", "upasamuchchay"),
        "title": "Subset (Upasamuchchay)",
        "formula": "B ⊆ A when EVERY element of B is also in A. "
                   "A set with n elements has 2^n subsets.",
        "explain": "Every set is a subset of itself, and the "
                   "empty set is a subset of every set.",
        "hinglish": "Chhota set jiske saare tatva bade set me "
                    "bhi hon — wahi uska upasamuchchay hai.",
        "example": {
            "q": "How many subsets does {1, 2} have?",
            "steps": ["2² = 4: { }, {1}, {2}, {1, 2}"],
            "answer": "4 subsets",
        },
    },
    {
        "id": "events_types",
        "keywords": ("mutually exclusive", "impossible event",
                     "certain event", "sure event",
                     "nishchit ghatna", "asambhav ghatna"),
        "title": "Types of Events",
        "formula": "Sure event: P = 1; Impossible event: P = 0; "
                   "Mutually exclusive events can never happen "
                   "together.",
        "explain": "Getting a head and a tail in ONE coin toss "
                   "are mutually exclusive — only one can occur.",
        "hinglish": "Jo ghatna pakki ghatti hai uski probability "
                    "1, jo ho hi nahi sakti uski 0 hoti hai.",
        "example": {
            "q": "P(getting 7 on one die)?",
            "steps": ["A die has only 1-6, so 7 is impossible"],
            "answer": "P = 0 (impossible event)",
        },
    },
    {
        "id": "sample_space",
        "keywords": ("sample space", "pratidarsh samashti"),
        "title": "Sample Space",
        "formula": "Sample space S = the set of ALL possible "
                   "outcomes of an experiment.",
        "explain": "For one coin: S = {H, T}. For one die: "
                   "S = {1, 2, 3, 4, 5, 6}. Probabilities are "
                   "counted inside this set.",
        "hinglish": "Kisi prayog ke saare sambhavit parinaam "
                    "milakar sample space banta hai.",
        "example": {
            "q": "Sample space of tossing two coins?",
            "steps": ["S = {HH, HT, TH, TT} — 4 outcomes"],
            "answer": "S = {HH, HT, TH, TT}",
        },
    },
    {
        "id": "similar_congruent",
        "keywords": ("congruent", "sarvangsam", "samroop",
                     "similar triangles"),
        "title": "Similar vs Congruent Triangles",
        "formula": "Similar = same shape, sizes may differ "
                   "(angles equal, sides in proportion). "
                   "Congruent = same shape AND same size.",
        "explain": "Every congruent pair is similar, but a "
                   "similar pair need not be congruent.",
        "hinglish": "Samroop matlab aakar ek jaisa; sarvangsam "
                    "matlab aakar ke saath naap bhi bilkul ek "
                    "jaisa.",
        "example": {
            "q": "Sides 3-4-5 and 6-8-10: similar or congruent?",
            "steps": ["Ratios 3:6 = 4:8 = 5:10 = 1:2, sizes "
                      "differ"],
            "answer": "Similar, not congruent",
        },
    },
    {
        "id": "conjugate",
        "keywords": ("conjugate", "sanyugmi"),
        "title": "Conjugate of a Surd / Complex Number",
        "formula": "Conjugate of a + √b is a - √b; of a + bi is "
                   "a - bi. Their product is always rational "
                   "(or real).",
        "explain": "Multiplying by the conjugate removes the "
                   "root (or the i) — that is how denominators "
                   "are rationalised.",
        "hinglish": "Beech wala chinh badal do — + ka - — wahi "
                    "sanyugmi hai; guna karne par karni khatm "
                    "ho jati hai.",
        "example": {
            "q": "Conjugate of 3 + √5?",
            "steps": ["Flip the sign: 3 - √5"],
            "answer": "3 - √5",
        },
    },
    {
        "id": "complex_basics",
        "keywords": ("complex number", "sammishra sankhya",
                     "imaginary number", "kalpanik sankhya",
                     "iota"),
        "title": "Complex Numbers and i (Iota)",
        "formula": "i = √(-1), so i² = -1. A complex number is "
                   "a + bi: a = real part, b = imaginary part.",
        "explain": "Complex numbers were created because "
                   "x² = -1 has no real answer. |a + bi| "
                   "(modulus) = √(a² + b²).",
        "hinglish": "i matlab √-1; a + bi me a asal bhaag hai "
                    "aur b kalpanik bhaag.",
        "example": {
            "q": "Modulus of 3 + 4i?",
            "steps": ["√(3² + 4²) = √25 = 5"],
            "answer": "|3 + 4i| = 5",
        },
    },
    {
        "id": "matrix_basics",
        "keywords": ("matrix", "avyooh"),
        "title": "Matrix and its Order",
        "formula": "A matrix is a rectangular array of numbers. "
                   "Order = rows × columns. Two matrices add "
                   "only when their orders are equal.",
        "explain": "A 2×3 matrix has 2 rows and 3 columns. "
                   "Addition/subtraction is element-by-element "
                   "and needs the same order.",
        "hinglish": "Matrix sankhyaon ki aayatakar vyavastha "
                    "hai; order pehle rows, phir columns se "
                    "likhte hain.",
        "example": {
            "q": "Order of [[1, 2, 3], [4, 5, 6]]?",
            "steps": ["2 rows, 3 columns"],
            "answer": "Order = 2 × 3",
        },
    },
    {
        "id": "midpoint_section",
        "keywords": ("midpoint formula", "madhya bindu ka sutra",
                     "section formula"),
        "title": "Midpoint and Section Formula",
        "formula": "Midpoint of (x₁,y₁), (x₂,y₂) = "
                   "((x₁+x₂)/2, (y₁+y₂)/2).",
        "explain": "The midpoint is just the average of the "
                   "two x's and the average of the two y's.",
        "hinglish": "Beech wala bindu dono x ka ausat aur dono "
                    "y ka ausat hota hai.",
        "example": {
            "q": "Midpoint of (2, 4) and (6, 8)?",
            "steps": ["((2+6)/2, (4+8)/2) = (4, 6)"],
            "answer": "(4, 6)",
        },
    },
    {
        "id": "distance_formula",
        "keywords": ("distance formula", "doori ka sutra"),
        "title": "Distance Formula",
        "formula": "Distance between (x₁,y₁) and (x₂,y₂) = "
                   "√((x₂-x₁)² + (y₂-y₁)²).",
        "explain": "It is Pythagoras' theorem applied to the "
                   "gap between the two points.",
        "hinglish": "Do binduo ki doori asal me Pythagoras se "
                    "hi aati hai — x ka antar aur y ka antar.",
        "example": {
            "q": "Distance between (0, 0) and (3, 4)?",
            "steps": ["√(3² + 4²) = √25 = 5"],
            "answer": "5 units",
        },
    },
    {
        "id": "ci_vs_si",
        "keywords": ("compound interest", "chakravridhi byaj",
                     "compound interest aur simple interest",
                     "ci aur si"),
        "title": "Compound Interest (and how it differs from SI)",
        "formula": "Amount = P(1 + R/100)^T; CI = Amount - P. "
                   "In SI the interest is on P only; in CI it "
                   "is on P + past interest.",
        "explain": "That 'interest on interest' is why CI is "
                   "always a little more than SI for the same "
                   "P, R, T (after the first year).",
        "hinglish": "Chakravridhi byaj me har saal byaj par bhi "
                    "byaj lagta hai, isliye SI se zyada hota hai.",
        "example": {
            "q": "CI on ₹1000 at 10% for 2 years?",
            "steps": ["Amount = 1000 × (1.1)² = 1210",
                      "CI = 1210 - 1000 = 210"],
            "answer": "CI = ₹210",
        },
    },
    {
        "id": "pi_concept",
        "keywords": ("π", "pi ki value", "what is pi",
                     "pi ka matlab"),
        "title": "What is Pi (π)?",
        "formula": "π = circumference / diameter of ANY circle "
                   "≈ 3.14159 (school value 22/7).",
        "explain": "Whatever the circle's size, its boundary "
                   "is always π times its diameter.",
        "hinglish": "Pi har gol ki paridhi aur vyas ka ratio "
                    "hai — hamesha ek hi, lagbhag 3.14159.",
        "example": {
            "q": "Circumference of a circle with diameter 7?",
            "steps": ["C = π × d = (22/7) × 7 = 22"],
            "answer": "22 units",
        },
    },
    {
        "id": "profit_loss",
        "keywords": ("profit aur loss", "labh aur hani",
                     "labh hani", "profit loss kya"),
        "title": "Profit and Loss",
        "formula": "Profit = SP - CP; Loss = CP - SP; "
                   "Profit % = (Profit / CP) × 100.",
        "explain": "Percent is ALWAYS calculated on the cost "
                   "price (CP), never on the selling price.",
        "hinglish": "Bechne ki keemat kharid se zyada to labh, "
                    "kam to hani — percent hamesha kharid "
                    "keemat par nikalta hai.",
        "example": {
            "q": "Bought for ₹400, sold for ₹500. Profit %?",
            "steps": ["Profit = 100; % = 100/400 × 100 = 25%"],
            "answer": "25% profit",
        },
    },
    {
        "id": "discount_concept",
        "keywords": ("discount kese", "discount kaise",
                     "discount kya", "chhoot kese",
                     "discount ka matlab"),
        "title": "How Discount Works",
        "formula": "Discount = Marked Price - Selling Price; "
                   "Discount % is always on the marked price.",
        "explain": "A 20% discount on ₹500 means you pay "
                   "500 - 100 = ₹400.",
        "hinglish": "Chhoot ankit mulya (tag wali keemat) par "
                    "milti hai; dena padta hai keemat minus "
                    "chhoot.",
        "example": {
            "q": "₹800 par 25% discount — kitna dena hoga?",
            "steps": ["Discount = 200; pay 800 - 200 = 600"],
            "answer": "₹600",
        },
    },
    {
        "id": "slope_concept",
        "keywords": ("slope kya", "dhal kya", "slope (dhal)"),
        "title": "Slope of a Line",
        "formula": "Slope m = (y₂ - y₁) / (x₂ - x₁) — how steep "
                   "the line is.",
        "explain": "Bigger slope = steeper line. A horizontal "
                   "line has slope 0; a vertical line's slope is "
                   "undefined.",
        "hinglish": "Dhal batati hai ki line kitni khadi (steep) "
                    "hai — y ka badlav ÷ x ka badlav.",
        "example": {
            "q": "Slope through (1, 2) and (3, 8)?",
            "steps": ["(8 - 2) / (3 - 1) = 6/2 = 3"],
            "answer": "Slope = 3",
        },
    },
    {
        "id": "poly_zeroes",
        "keywords": ("zeroes ka matlab", "shunyak ka matlab",
                     "polynomial ke zeroes", "zeroes (shunyak)"),
        "title": "Zeroes of a Polynomial",
        "formula": "A zero of p(x) is a value of x where "
                   "p(x) = 0. For x² + bx + c style quadratics: "
                   "sum of zeroes = -b/a, product = c/a.",
        "explain": "Graphically, the zeroes are the x-points "
                   "where the graph cuts the x-axis.",
        "hinglish": "x ki woh value jispar polynomial ki value "
                    "zero ho jaye — wahi uska shunyak hai.",
        "example": {
            "q": "Zeroes of x² - 5x + 6?",
            "steps": ["(x - 2)(x - 3) = 0, so x = 2 or 3"],
            "answer": "Zeroes are 2 and 3",
        },
    },
    {
        "id": "poly_degree",
        "keywords": ("polynomial ki degree", "degree kya hoti",
                     "bahupad ki ghaat", "degree of polynomial"),
        "title": "Degree of a Polynomial",
        "formula": "Degree = the HIGHEST power of x in the "
                   "polynomial.",
        "explain": "Degree 1 = linear, 2 = quadratic, 3 = "
                   "cubic. The degree also caps how many zeroes "
                   "the polynomial can have.",
        "hinglish": "Sabse badi ghaat (power) hi polynomial ki "
                    "degree hoti hai.",
        "example": {
            "q": "Degree of 4x³ + 2x + 7?",
            "steps": ["Highest power is 3"],
            "answer": "Degree = 3 (cubic)",
        },
    },
    {
        "id": "data_frequency",
        "keywords": ("data kya", "frequency kya", "barambarta",
                     "class interval", "varg antaral",
                     "data hota hai"),
        "title": "Data, Frequency and Class Interval",
        "formula": "Data = collected facts/numbers. Frequency "
                   "= how many times a value occurs. A class "
                   "interval groups values, e.g. 10-20.",
        "explain": "Statistics starts by organising raw data "
                   "into classes and counting frequencies.",
        "hinglish": "Jama ki gayi jaankari data hai; koi value "
                    "kitni baar aayi, wahi uski barambarta hai.",
        "example": {
            "q": "Frequency of 5 in 2, 5, 3, 5, 5?",
            "steps": ["5 appears 3 times"],
            "answer": "Frequency of 5 = 3",
        },
    },
    {
        "id": "heron_concept",
        "keywords": ("heron",),
        "title": "Heron's Formula",
        "formula": "Area = √(s(s-a)(s-b)(s-c)), where "
                   "s = (a+b+c)/2 is the semi-perimeter.",
        "explain": "Use it when all three sides of a triangle "
                   "are known but the height is not.",
        "hinglish": "Teeno side pata hon aur unchai na pata ho, "
                    "tab Heron ka formula area deta hai.",
        "example": {
            "q": "Area of a 3-4-5 triangle?",
            "steps": ["s = 6; √(6 × 3 × 2 × 1) = √36 = 6"],
            "answer": "6 square units",
        },
    },
    {
        "id": "tangent_concept",
        "keywords": ("tangent (sparsh", "sparsh rekha kya",
                     "tangent kya"),
        "title": "Tangent to a Circle",
        "formula": "A tangent touches the circle at exactly "
                   "ONE point, and the radius to that point is "
                   "perpendicular to it.",
        "explain": "From one outside point, the two tangents "
                   "to a circle are always equal in length.",
        "hinglish": "Sparsh rekha vritt ko sirf ek bindu par "
                    "chhooti hai aur trijya uspar lamb (90°) "
                    "hoti hai.",
        "example": {
            "q": "Tangent length from a point 13 cm from the "
                 "centre, radius 5 cm?",
            "steps": ["√(13² - 5²) = √144 = 12"],
            "answer": "12 cm",
        },
    },
    {
        "id": "sector_concept",
        "keywords": ("sector kya", "trijyakhand", "sector ("),
        "title": "Sector and Segment of a Circle",
        "formula": "Sector area = (θ/360°) × πr². A sector is "
                   "the 'pizza slice'; a segment is the part cut "
                   "off by a chord.",
        "explain": "The sector's share of the full circle is "
                   "exactly its angle's share of 360°.",
        "hinglish": "Do trijya aur chaap se ghira hissa sector "
                    "(trijyakhand) hota hai.",
        "example": {
            "q": "Sector area: r = 6, θ = 90°?",
            "steps": ["(90/360) × π × 36 = 9π ≈ 28.27"],
            "answer": "≈ 28.27 square units",
        },
    },
    {
        "id": "log_concept",
        "keywords": ("log kya", "logarithm", "laghuganak",
                     "log (logarithm)"),
        "title": "What is a Logarithm?",
        "formula": "log_b(x) asks: 'b to what power gives x?' "
                   "log₂8 = 3 because 2³ = 8.",
        "explain": "A logarithm is just the exponent written "
                   "the other way round: if b^y = x, then "
                   "log_b(x) = y.",
        "hinglish": "Log matlab ghaat ko ulta puchhna — 2 ki "
                    "kaunsi power 8 degi? log₂8 = 3.",
        "example": {
            "q": "Find log₁₀100.",
            "steps": ["10² = 100, so the power is 2"],
            "answer": "log₁₀100 = 2",
        },
    },
    {
        "id": "linear_eq_concept",
        "keywords": ("linear equation kya", "rekhik samikaran",
                     "do charo wali", "pair of linear"),
        "title": "Linear Equations",
        "formula": "A linear equation has degree 1: ax + by + "
                   "c = 0. A pair of them can have one solution, "
                   "none, or infinitely many.",
        "explain": "Its graph is always a straight line — "
                   "that is where the name 'linear' comes from.",
        "hinglish": "Jiski sabse badi power 1 ho, woh rekhik "
                    "samikaran hai; graph hamesha seedhi line "
                    "banta hai.",
        "example": {
            "q": "Solve 2x + 4 = 10.",
            "steps": ["2x = 6, so x = 3"],
            "answer": "x = 3",
        },
    },
    {
        "id": "derivative_concept",
        "keywords": ("derivative kya", "derivative hota",
                     "avakalan kya"),
        "title": "What is a Derivative?",
        "formula": "The derivative f'(x) is the rate of change "
                   "of f at x — the slope of its graph there. "
                   "d/dx (xⁿ) = n·xⁿ⁻¹.",
        "explain": "Speed is the derivative of distance; "
                   "acceleration is the derivative of speed.",
        "hinglish": "Derivative matlab koi cheez kitni tezi se "
                    "badal rahi hai, usi pal par.",
        "example": {
            "q": "Derivative of x³?",
            "steps": ["3 × x² = 3x²"],
            "answer": "3x²",
        },
    },
    {
        "id": "integral_concept",
        "keywords": ("integral ka matlab", "integral kya",
                     "samakalan kya", "integral hota",
                     "integration derivative ka ulta"),
        "title": "What is an Integral?",
        "formula": "Integration is the reverse of "
                   "differentiation; ∫xⁿ dx = xⁿ⁺¹/(n+1) + C. A "
                   "definite integral gives the area under a "
                   "curve.",
        "explain": "If the derivative breaks a quantity into "
                   "its rate, the integral adds the rate back "
                   "up into the quantity.",
        "hinglish": "Samakalan derivative ka ulta hai — rate "
                    "ko jodkar asal matra wapas milti hai.",
        "example": {
            "q": "∫ x² dx?",
            "steps": ["x³/3 + C"],
            "answer": "x³/3 + C",
        },
    },
    {
        "id": "limit_concept",
        "keywords": ("limit kya", "limit hoti", "seema kya"),
        "title": "What is a Limit?",
        "formula": "lim (x→a) f(x) = the value f(x) approaches "
                   "as x gets closer and closer to a.",
        "explain": "The function may not even be defined AT a "
                   "(like (x²-4)/(x-2) at x = 2), yet it clearly "
                   "approaches a value near a.",
        "hinglish": "Limit woh value hai jiske paas function "
                    "pahunchta hai jab x kisi point ke bilkul "
                    "kareeb jata hai.",
        "example": {
            "q": "lim (x→2) (x² - 4)/(x - 2)?",
            "steps": ["(x-2)(x+2)/(x-2) = x + 2 → 4"],
            "answer": "4",
        },
    },
    {
        "id": "exponent_rules",
        "keywords": ("exponent", "ghaat ke niyam", "ghaatank"),
        "title": "Laws of Exponents",
        "formula": "aᵐ × aⁿ = aᵐ⁺ⁿ; aᵐ ÷ aⁿ = aᵐ⁻ⁿ; "
                   "(aᵐ)ⁿ = aᵐⁿ; a⁰ = 1; a⁻ⁿ = 1/aⁿ.",
        "explain": "Same base: multiplying adds the powers, "
                   "dividing subtracts them.",
        "hinglish": "Aadhar ek ho to guna me ghaate judti "
                    "hain, bhaag me ghatti hain.",
        "example": {
            "q": "2³ × 2⁴?",
            "steps": ["2⁷ = 128"],
            "answer": "128",
        },
    },
    {
        "id": "determinant_concept",
        "keywords": ("determinant kya", "saaranik"),
        "title": "What is a Determinant?",
        "formula": "For [[a, b], [c, d]]: det = ad - bc. It is "
                   "ONE number computed from a square matrix.",
        "explain": "A determinant of 0 means the matrix cannot "
                   "be inverted and its equations have no unique "
                   "solution.",
        "hinglish": "Determinant matrix se nikla ek khaas "
                    "number hai — 2×2 ke liye ad - bc.",
        "example": {
            "q": "det [[2, 3], [1, 4]]?",
            "steps": ["2×4 - 3×1 = 8 - 3 = 5"],
            "answer": "5",
        },
    },
    {
        "id": "axes_quadrants",
        "keywords": ("quadrant", "chaturthansh",
                     "x-axis aur y-axis", "aksh kya"),
        "title": "Axes and Quadrants",
        "formula": "The x-axis and y-axis divide the plane "
                   "into 4 quadrants. On the y-axis x = 0; on "
                   "the x-axis y = 0.",
        "explain": "Quadrants go anti-clockwise from the top "
                   "right: I (+,+), II (-,+), III (-,-), IV (+,-).",
        "hinglish": "Do aksh plane ko 4 hisso (quadrants) me "
                    "baant-te hain; y-axis par x hamesha 0 "
                    "hota hai.",
        "example": {
            "q": "Which quadrant is (-3, 5) in?",
            "steps": ["x negative, y positive → Quadrant II"],
            "answer": "Quadrant II",
        },
    },
    {
        "id": "angle_sum_property",
        "keywords": ("teeno kono ka yog", "konon ka yog 180",
                     "angle sum property"),
        "title": "Angle Sum Property of a Triangle",
        "formula": "The three angles of any triangle always "
                   "add up to 180°.",
        "explain": "So if two angles are known, the third is "
                   "simply 180° minus their sum.",
        "hinglish": "Kisi bhi tribhuj ke teeno kono ka yog "
                    "hamesha 180 degree hi hota hai.",
        "example": {
            "q": "Angles 60° and 50° — third angle?",
            "steps": ["180 - 60 - 50 = 70°"],
            "answer": "70°",
        },
    },
    {
        "id": "right_triangle",
        "keywords": ("samkon tribhuj kise", "samkon tribhuj kya",
                     "right triangle kya"),
        "title": "Right-Angled Triangle",
        "formula": "A triangle with ONE angle exactly 90°. The "
                   "side opposite it (the longest) is the "
                   "hypotenuse.",
        "explain": "All of Pythagoras and basic trigonometry "
                   "lives inside right-angled triangles.",
        "hinglish": "Jis tribhuj ka ek kon pura 90 degree ho, "
                    "wohi samkon tribhuj hai.",
        "example": {
            "q": "Sides 3, 4, 5 — right-angled?",
            "steps": ["3² + 4² = 25 = 5² — yes"],
            "answer": "Yes, right-angled",
        },
    },
    {
        "id": "area_vs_perimeter",
        "keywords": ("kshetrafal aur parimaap",
                     "area aur perimeter", "area and perimeter"),
        "title": "Area vs Perimeter",
        "formula": "Perimeter = length of the boundary (in "
                   "cm); Area = surface covered (in cm²).",
        "explain": "Fencing a field uses the perimeter; "
                   "tiling its floor uses the area.",
        "hinglish": "Parimaap kinare ki lambai hai, kshetrafal "
                    "andar bhari hui jagah.",
        "example": {
            "q": "Rectangle 5 × 3: perimeter and area?",
            "steps": ["P = 2(5 + 3) = 16; A = 5 × 3 = 15"],
            "answer": "Perimeter 16, Area 15",
        },
    },
    {
        "id": "mensuration_formulas",
        "keywords": ("volume formula", "aayatan ka formula",
                     "aayatan (volume) kya", "aayatan kya hota",
                     "surface area aur volume",
                     "surface area formula",
                     "ka volume cylinder"),
        "title": "Volume and Surface Area — the Main Formulas",
        "formula": "Cuboid V = l×b×h; Cylinder V = πr²h; Cone "
                   "V = (1/3)πr²h; Sphere V = (4/3)πr³, "
                   "surface = 4πr².",
        "explain": "Volume is the space INSIDE (cm³); surface "
                   "area is the skin OUTSIDE (cm²). A cone is "
                   "exactly one-third of its cylinder.",
        "hinglish": "Aayatan andar ki jagah hai, prasth "
                    "kshetrafal bahar ki satah — dono alag "
                    "cheezein hain.",
        "example": {
            "q": "Volume of a cylinder, r = 7, h = 10?",
            "steps": ["π × 49 × 10 ≈ 1539.38"],
            "answer": "≈ 1539.38 cubic units",
        },
    },
    {
        "id": "ratio_proportion",
        "keywords": ("ratio aur proportion",
                     "anupat aur samanupat", "ratio proportion"),
        "title": "Ratio vs Proportion",
        "formula": "A ratio compares two quantities (3:4). A "
                   "proportion says two ratios are EQUAL "
                   "(3:4 = 6:8).",
        "explain": "In a proportion, cross-products are equal: "
                   "if a:b = c:d then a×d = b×c.",
        "hinglish": "Anupat sirf tulna hai; samanupat me do "
                    "anupat barabar hote hain.",
        "example": {
            "q": "Is 2:3 = 4:6 a proportion?",
            "steps": ["2 × 6 = 12 and 3 × 4 = 12 — equal"],
            "answer": "Yes, it is a proportion",
        },
    },
    {
        "id": "coordinate_geometry_concept",
        "keywords": ("coordinate geometry",
                     "nirdeshank jyamiti"),
        "title": "Coordinate Geometry",
        "formula": "Points are written as (x, y); distance "
                   "between (x1, y1) and (x2, y2) is "
                   "√((x2−x1)² + (y2−y1)²).",
        "explain": "Coordinate geometry studies shapes with "
                   "numbers: every point has an x (horizontal) "
                   "and a y (vertical) position, and distances, "
                   "midpoints and areas are found with formulas.",
        "hinglish": "Coordinate geometry me har bindu ko "
                    "(x, y) se likhte hain aur doori, madhy "
                    "bindu aadi formula se nikalte hain.",
        "example": {
            "q": "Distance between (0, 0) and (3, 4)?",
            "steps": ["√((3−0)² + (4−0)²) = √(9 + 16) = √25"],
            "answer": "5",
        },
    },
    {
        # Wave 65: definition asks the earlier list never
        # carried, in the students' own words (Devanagari,
        # Roman Hindi and English). Appended last: every
        # older entry keeps priority for its own keywords.
        "id": "equilateral_triangle",
        "keywords": ("equilateral", "समबाहु", "sambahu",
                     "samabahu"),
        "title": "Equilateral Triangle (समबाहु त्रिभुज)",
        "formula": "All three sides are equal and all "
                   "three angles are 60° each. Perimeter = "
                   "3 × side; Area = (√3/4) × side².",
        "explain": "Because the sides are equal, the "
                   "angles opposite them are equal too — "
                   "and angles sum to 180°, so each is 60°.",
        "hinglish": "Teeno bhujaayein barabar aur teeno "
                    "kon 60° ke hote hain — wahi samabahu "
                    "tribhuj hai.",
        "example": {
            "q": "Perimeter of an equilateral triangle "
                 "with side 5 cm?",
            "steps": ["3 × 5 = 15 cm"],
            "answer": "15 cm",
        },
    },
    {
        "id": "right_triangle",
        "keywords": ("samkon tribhuj", "samkon",
                     "right triangle", "right-angled triangle",
                     "right angled triangle"),
        "title": "Right Triangle (समकोण त्रिभुज)",
        "formula": "A triangle with one angle of exactly "
                   "90°. The side opposite the right angle "
                   "is the hypotenuse, and a² + b² = c² "
                   "(Pythagoras).",
        "explain": "The two sides forming the right angle "
                   "are the legs (perpendicular and base); "
                   "the hypotenuse is always the longest "
                   "side.",
        "hinglish": "Jis tribhuj ka ek kon 90° ka ho, "
                    "use samkon tribhuj kehte hain; 90° ke "
                    "saamne wali bhuja karn hoti hai.",
        "example": {
            "q": "Legs 3 and 4 — hypotenuse?",
            "steps": ["√(3² + 4²) = √25 = 5"],
            "answer": "Hypotenuse = 5",
        },
    },
    {
        "id": "ratio_concept",
        "keywords": ("anupaat", "anupat", "अनुपात",
                     "what is a ratio", "what is ratio",
                     "ratio kya", "ratio matlab",
                     "ratio ka matlab"),
        "title": "Ratio (अनुपात)",
        "formula": "A ratio compares two quantities of "
                   "the same kind: a : b means a/b. Ratios "
                   "have no unit and are written in the "
                   "simplest form.",
        "explain": "If a class has 12 boys and 18 girls, "
                   "the ratio of boys to girls is 12 : 18 "
                   "= 2 : 3.",
        "hinglish": "Do cheezon ki tulna ko anupaat "
                    "kehte hain — jaise 2 : 3 matlab 2/3.",
        "example": {
            "q": "Ratio of 20 cm to 1 m?",
            "steps": ["1 m = 100 cm, so 20 : 100 = 1 : 5"],
            "answer": "1 : 5",
        },
    },
    {
        "id": "identity_concept",
        "keywords": ("sarvsamika", "सर्वसमिका",
                     "what is an identity",
                     "algebraic identity", "identity kya"),
        "title": "Identity (सर्वसमिका)",
        "formula": "An identity is an equality that is "
                   "true for EVERY value of the variable — "
                   "like (a + b)² = a² + 2ab + b².",
        "explain": "An equation (2x + 3 = 7) is true "
                   "only for one value; an identity holds "
                   "for all values, so it can be used to "
                   "expand and factorise.",
        "hinglish": "Jo barabari har value par sach ho, "
                    "wo sarvsamika hai; samikaran sirf kuch "
                    "values par sach hota hai.",
        "example": {
            "q": "Expand (x + 3)² using the identity.",
            "steps": ["(a + b)² = a² + 2ab + b² gives "
                      "x² + 6x + 9"],
            "answer": "x² + 6x + 9",
        },
    },
    {
        "id": "factors_concept",
        "keywords": ("gunankhand", "गुणनखण्ड", "गुणनखंड",
                     "what are factors", "factors kya"),
        "title": "Factors (गुणनखण्ड)",
        "formula": "A factor of a number divides it "
                   "exactly, leaving no remainder. 12 = "
                   "3 × 4, so 3 and 4 are factors of 12.",
        "explain": "Factors of 12: 1, 2, 3, 4, 6, 12. "
                   "Prime factors use only primes: 12 = "
                   "2 × 2 × 3.",
        "hinglish": "Jo sankhya kisi sankhya ko poora "
                    "bhaag de de, wo uska gunankhand hai.",
        "example": {
            "q": "Factors of 18?",
            "steps": ["18 = 1 × 18, 2 × 9, 3 × 6"],
            "answer": "1, 2, 3, 6, 9, 18",
        },
    },
    {
        "id": "line_segment_concept",
        "keywords": ("rekha khand", "रेखा खण्ड", "रेखा खंड",
                     "line segment", "rekha aur rekha khand",
                     "difference between a line and a line "
                     "segment"),
        "title": "Line vs Line Segment (रेखा बनाम रेखा खण्ड)",
        "formula": "A line goes on forever in both "
                   "directions and has no length. A line "
                   "segment is the part of a line between "
                   "two endpoints — it has a fixed length.",
        "explain": "A ray is the third member of the "
                   "family: it starts at one point and "
                   "goes on forever in one direction.",
        "hinglish": "Rekha dono taraf ant tak jaati "
                    "hai; rekha khand do binduon ke beech "
                    "ka hissa hai, uski lambaai hoti hai.",
        "example": {
            "q": "Can you measure a line?",
            "steps": ["A line is endless, so no; a "
                      "segment can be measured"],
            "answer": "Only the segment has a length",
        },
    },
    {
        "id": "quadrilateral_angles",
        "keywords": ("chaturbhuj", "चतुर्भुज",
                     "sum of angles of a quadrilateral",
                     "quadrilateral ke kono"),
        "title": "Quadrilateral (चतुर्भुज): Angle Sum",
        "formula": "The four interior angles of any "
                   "quadrilateral add up to 360°.",
        "explain": "A quadrilateral splits into two "
                   "triangles along a diagonal, and each "
                   "triangle's angles sum to 180° — so the "
                   "total is 2 × 180° = 360°.",
        "hinglish": "Chaturbhuj ke chaaro kono ka yog "
                    "360° hota hai.",
        "example": {
            "q": "Three angles are 90°, 80°, 100°. "
                 "Fourth angle?",
            "steps": ["360 - (90 + 80 + 100) = 90"],
            "answer": "90°",
        },
    },
    {
        "id": "quadratic_equation_concept",
        "keywords": ("vargeeya samikaran", "वर्गीय समीकरण",
                     "dvighat samikaran", "द्विघात समीकरण",
                     "what is a quadratic equation",
                     "quadratic equation kise"),
        "title": "Quadratic Equation (द्विघात समीकरण)",
        "formula": "An equation of the form ax² + bx + "
                   "c = 0 (a ≠ 0). It has at most two "
                   "solutions, found by factorising or by "
                   "x = (-b ± √(b² - 4ac)) / 2a.",
        "explain": "The highest power of the variable "
                   "is 2 — that is what makes it quadratic "
                   "(dvighat).",
        "hinglish": "Jis samikaran me variable ki sabse "
                    "badi ghaat 2 ho, wo dvighat samikaran "
                    "hai.",
        "example": {
            "q": "Solve x² - 5x + 6 = 0.",
            "steps": ["(x - 2)(x - 3) = 0"],
            "answer": "x = 2 or x = 3",
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
