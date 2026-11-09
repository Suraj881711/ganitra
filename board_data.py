"""Board Mode data (Wave 5): NCERT maths chapters for Classes 6-12.

Chapter lists follow the current rationalised NCERT textbooks (Class 6
uses the 2024 "Ganita Prakash" book; Classes 7-12 use the rationalised
editions). 6-12 maths chapters are NCERT-common: CBSE, ICSE and the
state boards (MP, Rajasthan, UP, ...) teach essentially the same
chapter list, which is why one list serves every board choice.

Each chapter maps to the practice/quiz topic whose question generator
fits it best. Topics with a dedicated generator in solver/practice.py
are: arithmetic, algebra, trig, stats. board_quiz.py adds generators
for: sequences, probability, calculus, linear_algebra, geometry.

HONEST MAPPING NOTE: "approximate" is True where the mapped topic is
only the closest available generator, not a true match for the chapter
(e.g. "Symmetry" -> geometry: questions are mensuration-flavoured;
"Sets" -> arithmetic: there is no sets quiz generator yet). The
chapter page shows a note for those chapters instead of pretending
the match is exact.
"""

BOARDS = [
    ("cbse", "CBSE"),
    ("icse", "ICSE"),
    ("mp-board", "MP Board"),
    ("rajasthan-board", "Rajasthan Board"),
    ("up-board", "UP Board"),
    ("other-state-board", "Other State Board"),
]

BOARD_NAMES = dict(BOARDS)

CLASS_NUMBERS = tuple(range(6, 13))

# topic key -> nothing here; labels come from i18n ("quiz_topic_<key>").
KNOWN_TOPICS = ("arithmetic", "algebra", "trig", "stats", "sequences",
                "probability", "calculus", "linear_algebra", "geometry")


def _ch(slug, title, topic, approximate=False):
    return {"slug": slug, "title": title, "topic": topic,
            "approximate": approximate}


CHAPTERS = {
    6: [  # Ganita Prakash (2024)
        _ch("patterns-in-mathematics", "Patterns in Mathematics",
            "sequences"),
        _ch("lines-and-angles", "Lines and Angles", "geometry", True),
        _ch("number-play", "Number Play", "arithmetic"),
        _ch("data-handling-and-presentation",
            "Data Handling and Presentation", "stats"),
        _ch("prime-time", "Prime Time", "arithmetic", True),
        _ch("perimeter-and-area", "Perimeter and Area", "geometry"),
        _ch("fractions", "Fractions", "arithmetic"),
        _ch("playing-with-constructions", "Playing with Constructions",
            "geometry", True),
        _ch("symmetry", "Symmetry", "geometry", True),
        _ch("the-other-side-of-zero", "The Other Side of Zero",
            "arithmetic"),
    ],
    7: [
        _ch("integers", "Integers", "arithmetic"),
        _ch("fractions-and-decimals", "Fractions and Decimals",
            "arithmetic"),
        _ch("data-handling", "Data Handling", "stats"),
        _ch("simple-equations", "Simple Equations", "algebra"),
        _ch("lines-and-angles", "Lines and Angles", "geometry", True),
        _ch("the-triangle-and-its-properties",
            "The Triangle and Its Properties", "geometry", True),
        _ch("comparing-quantities", "Comparing Quantities",
            "arithmetic"),
        _ch("rational-numbers", "Rational Numbers", "arithmetic"),
        _ch("perimeter-and-area", "Perimeter and Area", "geometry"),
        _ch("algebraic-expressions", "Algebraic Expressions",
            "algebra"),
        _ch("exponents-and-powers", "Exponents and Powers",
            "algebra", True),
        _ch("symmetry", "Symmetry", "geometry", True),
        _ch("visualising-solid-shapes", "Visualising Solid Shapes",
            "geometry", True),
    ],
    8: [
        _ch("rational-numbers", "Rational Numbers", "arithmetic"),
        _ch("linear-equations-in-one-variable",
            "Linear Equations in One Variable", "algebra"),
        _ch("understanding-quadrilaterals",
            "Understanding Quadrilaterals", "geometry", True),
        _ch("data-handling", "Data Handling", "stats"),
        _ch("squares-and-square-roots", "Squares and Square Roots",
            "arithmetic", True),
        _ch("cubes-and-cube-roots", "Cubes and Cube Roots",
            "arithmetic", True),
        _ch("comparing-quantities", "Comparing Quantities",
            "arithmetic"),
        _ch("algebraic-expressions-and-identities",
            "Algebraic Expressions and Identities", "algebra"),
        _ch("mensuration", "Mensuration", "geometry"),
        _ch("exponents-and-powers", "Exponents and Powers",
            "algebra", True),
        _ch("direct-and-inverse-proportions",
            "Direct and Inverse Proportions", "arithmetic"),
        _ch("factorisation", "Factorisation", "algebra"),
        _ch("introduction-to-graphs", "Introduction to Graphs",
            "geometry", True),
    ],
    9: [
        _ch("number-systems", "Number Systems", "arithmetic", True),
        _ch("polynomials", "Polynomials", "algebra"),
        _ch("coordinate-geometry", "Coordinate Geometry", "geometry"),
        _ch("linear-equations-in-two-variables",
            "Linear Equations in Two Variables", "algebra"),
        _ch("introduction-to-euclids-geometry",
            "Introduction to Euclid's Geometry", "geometry", True),
        _ch("lines-and-angles", "Lines and Angles", "geometry", True),
        _ch("triangles", "Triangles", "geometry", True),
        _ch("quadrilaterals", "Quadrilaterals", "geometry", True),
        _ch("circles", "Circles", "geometry"),
        _ch("herons-formula", "Heron's Formula", "geometry"),
        _ch("surface-areas-and-volumes", "Surface Areas and Volumes",
            "geometry"),
        _ch("statistics", "Statistics", "stats"),
    ],
    10: [
        _ch("real-numbers", "Real Numbers", "arithmetic", True),
        _ch("polynomials", "Polynomials", "algebra"),
        _ch("pair-of-linear-equations",
            "Pair of Linear Equations in Two Variables", "algebra"),
        _ch("quadratic-equations", "Quadratic Equations", "algebra"),
        _ch("arithmetic-progressions", "Arithmetic Progressions",
            "sequences"),
        _ch("triangles", "Triangles", "geometry", True),
        _ch("coordinate-geometry", "Coordinate Geometry", "geometry"),
        _ch("introduction-to-trigonometry",
            "Introduction to Trigonometry", "trig"),
        _ch("some-applications-of-trigonometry",
            "Some Applications of Trigonometry", "trig"),
        _ch("circles", "Circles", "geometry"),
        _ch("areas-related-to-circles", "Areas Related to Circles",
            "geometry"),
        _ch("surface-areas-and-volumes", "Surface Areas and Volumes",
            "geometry"),
        _ch("statistics", "Statistics", "stats"),
        _ch("probability", "Probability", "probability"),
    ],
    11: [
        _ch("sets", "Sets", "arithmetic", True),
        _ch("relations-and-functions", "Relations and Functions",
            "algebra", True),
        _ch("trigonometric-functions", "Trigonometric Functions",
            "trig"),
        _ch("complex-numbers-and-quadratic-equations",
            "Complex Numbers and Quadratic Equations", "algebra",
            True),
        _ch("linear-inequalities", "Linear Inequalities", "algebra"),
        _ch("permutations-and-combinations",
            "Permutations and Combinations", "probability", True),
        _ch("binomial-theorem", "Binomial Theorem", "algebra", True),
        _ch("sequences-and-series", "Sequences and Series",
            "sequences"),
        _ch("straight-lines", "Straight Lines", "geometry"),
        _ch("conic-sections", "Conic Sections", "geometry", True),
        _ch("introduction-to-three-dimensional-geometry",
            "Introduction to Three Dimensional Geometry", "geometry",
            True),
        _ch("limits-and-derivatives", "Limits and Derivatives",
            "calculus"),
        _ch("statistics", "Statistics", "stats"),
        _ch("probability", "Probability", "probability"),
    ],
    12: [
        _ch("relations-and-functions", "Relations and Functions",
            "algebra", True),
        _ch("inverse-trigonometric-functions",
            "Inverse Trigonometric Functions", "trig"),
        _ch("matrices", "Matrices", "linear_algebra"),
        _ch("determinants", "Determinants", "linear_algebra"),
        _ch("continuity-and-differentiability",
            "Continuity and Differentiability", "calculus"),
        _ch("application-of-derivatives", "Application of Derivatives",
            "calculus"),
        _ch("integrals", "Integrals", "calculus"),
        _ch("application-of-integrals", "Application of Integrals",
            "calculus", True),
        _ch("differential-equations", "Differential Equations",
            "calculus", True),
        _ch("vector-algebra", "Vector Algebra", "linear_algebra",
            True),
        _ch("three-dimensional-geometry", "Three Dimensional Geometry",
            "geometry", True),
        _ch("linear-programming", "Linear Programming", "algebra",
            True),
        _ch("probability", "Probability", "probability"),
    ],
}


def get_chapters(class_num):
    """Chapter list for a class (6-12), or [] for anything else."""
    return CHAPTERS.get(class_num, [])


def get_chapter(class_num, slug):
    """One chapter dict by class + slug, or None."""
    for chapter in get_chapters(class_num):
        if chapter["slug"] == slug:
            return chapter
    return None


__all__ = ["BOARDS", "BOARD_NAMES", "CLASS_NUMBERS", "KNOWN_TOPICS",
           "CHAPTERS", "get_chapters", "get_chapter"]
