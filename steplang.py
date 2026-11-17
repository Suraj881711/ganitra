"""Wave 130 — solver-step re-languaging for explicit language
requests (the Wave 107 leftover).

Wave 107 (live since Deploy-24) made an explicit request in the
message ("answer Hindi me chahiye") switch the UI language, the
explanation, the advice and the AI prompt — but the SOLVER's own
step sentences kept coming out in the QUESTION's language: an
English question with "answer in Hindi" got a Hindi card whose
working lines were still English ("Write in standard form: ...",
"Divide both sides by 3: ..."). Suraj approved closing that gap
on 17 Nov 2026 ("ye saare kaam start kar do").

How this module works — deterministic, no AI, no machine
translation of free text:

* The solver's steps are template output. A step is either a
  pure formula line ("= 154", "GCD = 6", "x = 2") — language-
  free, never touched — or a boilerplate sentence from a finite
  set of templates with maths spans embedded. This module
  carries that mined template set (see _RULES, built from the
  Wave 130 battery: 74 questions, 189 step lines, 107 distinct
  skeletons) with a rendering in each of the three request
  languages: English, Hindi (Devanagari) and Hinglish (Roman).
* A rule matches a WHOLE step line (anchored regex); the maths
  spans are captured and re-emitted byte-for-byte. Numbers,
  formulas and answer values are never altered. A step that
  matches no rule is left exactly as the solver wrote it —
  counted, never guessed at (see analyse_steps).
* The transform runs ONLY when an explicit Wave-107 request
  is in force (lang_request is not None) and only on solver-
  family results (see relanguage_result's gate). With no
  request, nothing in this module is ever called and behaviour
  is byte-identical to before this wave.
"""
import re

__all__ = ["translate_step", "relanguage_steps",
           "relanguage_result", "relanguage_methods",
           "analyse_steps", "step_language"]

_DEV = re.compile(r"[ऀ-ॿ]")
# English function/label words that mark a step as carrying
# English boilerplate (formula lines never contain them).
_EN_HINT = re.compile(
    r"\b(the|both|sides?|values?|roots?|answers?|solutions?|"
    r"total|amount|interest|factorisation|factorization|"
    r"standard|formula|terms?|count|order|middle|frequent|"
    r"appears?|cancel|combine|brackets|highest|lowest|power|"
    r"prime|common|every|each|using|symbolic|methods?|"
    r"evaluates?|simplifies|expression|convert|base unit|"
    r"part\(s\)|equal parts|raised|gives|fair coin|equally|"
    r"likely|outcomes?|favourable|probability|circumference|"
    r"perimeter|volume|median|mean|means|area|discriminant|"
    r"vertex|slope|distance|midpoint|"
    r"profit|loss|price|selling|equations?|cancel|of|"
    r"remainder|multiple|exact|here|radius|diameter|angles?|add|"
    r"subtract|multiply|divide|bring|move|take|write|put|"
    r"find|solve|expand|simplify|factorise|factorize|draw|"
    r"arrange|step|why|check|backwards|fits?|clear now|"
    r"next|explain|root|asks|question|part of your)\b",
    re.IGNORECASE)


def step_language(step):
    """The boilerplate language of one step line: "hi" when it
    carries Devanagari prose, "en" when it carries English
    boilerplate words, None when the line is language-free
    (a pure formula / value line)."""
    s = str(step or "")
    if _DEV.search(s):
        return "hi"
    if _EN_HINT.search(s):
        return "en"
    return None


# ---------------------------------------------------------------------------
# Small word maps used inside captured spans.
# ---------------------------------------------------------------------------

_COLOURS = {  # English colour word -> Hindi (for probability steps)
    "red": "लाल", "blue": "नीला", "green": "हरा",
    "black": "काला", "white": "सफ़ेद", "yellow": "पीला",
    "orange": "नारंगी", "pink": "गुलाबी", "brown": "भूरा",
    "purple": "बैंगनी", "grey": "स्लेटी", "gray": "स्लेटी",
}
_HI_WORD_EN = {  # Devanagari content word -> English (formula spans)
    "भुजा": "side", "त्रिज्या": "radius", "लंबाई": "length",
    "चौड़ाई": "breadth", "ऊँचाई": "height", "विकर्ण": "diagonal",
    "दूरी": "distance", "प्रवणता": "slope", "बिंदु": "point",
    "रेखा": "line", "कोण": "angle", "वर्ष": "years",
    "परिमाप": "perimeter", "क्षेत्रफल": "area",
    "आयतन": "volume", "घन": "cube",
}
_ORDINALS = {"प्रथम": "first", "द्वितीय": "second",
             "तृतीय": "third", "चतुर्थ": "fourth",
             "पंचम": "fifth"}
_POLYGONS_HI = {
    "triangle": "त्रिभुज", "quadrilateral": "चतुर्भुज",
    "pentagon": "पंचभुज", "hexagon": "षट्भुज",
    "heptagon": "सप्तभुज", "octagon": "अष्टभुज",
    "nonagon": "नवभुज", "decagon": "दशभुज",
}
_UNITS_HI = {
    "hours": "घंटे", "hour": "घंटा", "minutes": "मिनट",
    "minute": "मिनट", "seconds": "सेकंड", "second": "सेकंड",
    "days": "दिन", "weeks": "सप्ताह", "months": "महीने",
    "years": "वर्ष", "year": "वर्ष",
}


def _sub_en_words(text, mapping):
    def repl(m):
        return mapping.get(m.group(0).lower(), m.group(0))
    return re.sub(r"[A-Za-z]+", repl, str(text))


def _sub_hi_words(text):
    out = str(text)
    for hi_word, en_word in _HI_WORD_EN.items():
        out = out.replace(hi_word, en_word)
    return out


def _units_to_hi(text):
    return _sub_en_words(text, _UNITS_HI)


# ---------------------------------------------------------------------------
# The rule table. Each rule: (source language, regex, renderings).
# A rendering is a format template using the regex's named groups,
# or a callable(groups, target) -> str. Templates exist for every
# target except the source language itself.
# ---------------------------------------------------------------------------

def _R(pat, src="en", en=None, hi=None, hinglish=None):
    return (src, re.compile(pat),
            {"en": en, "hi": hi, "hinglish": hinglish})


_RULES = [
    # ---- quadratic / equations (EN source) -------------------------
    _R(r"^D > 0, so there are two distinct real roots\.$",
       hi="D > 0 है, इसलिए दो भिन्न वास्तविक मूल हैं।",
       hinglish="D > 0 hai, isliye do alag real roots hain."),
    _R(r"^D = 0, so there is one repeated real root\.$",
       hi="D = 0 है, इसलिए एक ही मूल दोहराया जाता है।",
       hinglish="D = 0 hai, isliye ek hi root dohraata hai."),
    _R(r"^D < 0, so the roots are complex \(non-real\)\.$",
       hi="D < 0 है, इसलिए मूल सम्मिश्र (गैर-वास्तविक) हैं।",
       hinglish="D < 0 hai, isliye roots complex (non-real) hain."),
    _R(r"^Write in standard form: (?P<rest>.+)$",
       hi="मानक रूप में लिखिए: {rest}",
       hinglish="Standard form me likho: {rest}"),
    _R(r"^Discriminant (?P<rest>.+)$",
       hi="विविक्तकर {rest}",
       hinglish="Discriminant {rest}"),
    _R(r"^Quadratic formula: (?P<rest>.+)$",
       hi="द्विघात सूत्र: {rest}",
       hinglish="Quadratic formula: {rest}"),
    _R(r"^Solution: (?P<rest>.+)$",
       hi="हल: {rest}",
       hinglish="Solution: {rest}"),
    _R(r"^Answer: (?P<rest>.+)$",
       hi="उत्तर: {rest}",
       hinglish="Answer: {rest}"),
    _R(r"^Answer = (?P<rest>.+)$",
       hi="उत्तर = {rest}",
       hinglish="Answer = {rest}"),
    _R(r"^Bring all terms to one side: (?P<rest>.+)$",
       hi="सभी पदों को एक ओर लाइए: {rest}",
       hinglish="Saare terms ek side lao: {rest}"),
    _R(r"^Move everything to one side: (?P<rest>.+)$",
       hi="सब कुछ एक ओर ले जाइए: {rest}",
       hinglish="Sab kuch ek side le jao: {rest}"),
    _R(r"^(?P<verb>Add|Subtract) (?P<n>.+?) from both sides: "
       r"(?P<rest>.+)$",
       hi=lambda g, t: "%s: %s" % (
           {"Add": "दोनों ओर %s जोड़िए" % g["n"],
            "Subtract": "दोनों ओर से %s घटाइए" % g["n"]}[g["verb"]],
           g["rest"]),
       hinglish=lambda g, t: "%s: %s" % (
           {"Add": "Dono side %s add karo" % g["n"],
            "Subtract": "Dono side se %s subtract karo"
            % g["n"]}[g["verb"]], g["rest"])),
    _R(r"^Divide both sides by (?P<n>.+?): (?P<rest>.+)$",
       hi="दोनों ओर {n} से भाग दीजिए: {rest}",
       hinglish="Dono side ko {n} se divide karo: {rest}"),
    _R(r"^Multiply both sides by (?P<n>.+?): (?P<rest>.+)$",
       hi="दोनों ओर {n} से गुणा कीजिए: {rest}",
       hinglish="Dono side ko {n} se multiply karo: {rest}"),
    _R(r"^Divide every term by (?P<n>.+?): (?P<rest>.+)$",
       hi="प्रत्येक पद को {n} से भाग दीजिए: {rest}",
       hinglish="Har term ko {n} se divide karo: {rest}"),
    _R(r"^Divide by the count \((?P<n>.+?)\): (?P<rest>.+)$",
       hi="संख्या ({n}) से भाग दीजिए: {rest}",
       hinglish="Count ({n}) se divide karo: {rest}"),
    _R(r"^Divide by (?P<n>.+?): (?P<rest>.+)$",
       hi="{n} से भाग दीजिए: {rest}",
       hinglish="{n} se divide karo: {rest}"),
    _R(r"^Divide (?P<a>.+?) by (?P<b>.+?): (?P<rest>.+)$",
       hi="{a} को {b} से भाग दीजिए: {rest}",
       hinglish="{a} ko {b} se divide karo: {rest}"),
    _R(r"^Simplify both sides: (?P<rest>.+)$",
       hi="दोनों पक्षों को सरल कीजिए: {rest}",
       hinglish="Dono sides simplify karo: {rest}"),
    _R(r"^Solve for (?P<v>.+?): (?P<rest>.+)$",
       hi="{v} के लिए हल कीजिए: {rest}",
       hinglish="{v} ke liye solve karo: {rest}"),
    _R(r"^Solve for (?P<rest>.+) using symbolic methods "
       r"\(SymPy\)\.$",
       hi="प्रतीकात्मक विधि (SymPy) से हल कीजिए: {rest}",
       hinglish="Symbolic method (SymPy) se solve karo: {rest}"),
    _R(r"^Find the roots: (?P<rest>.+?) — each root r gives a "
       r"factor \(x - r\)$",
       hi="मूल ज्ञात कीजिए: {rest} — प्रत्येक मूल r एक "
          "गुणनखंड (x - r) देता है",
       hinglish="Roots nikalo: {rest} — har root r ek factor "
                "(x - r) deta hai"),
    _R(r"^Factorise the left side: (?P<rest>.+)$",
       hi="बाएँ पक्ष का गुणनखंड कीजिए: {rest}",
       hinglish="Left side ko factorise karo: {rest}"),
    _R(r"^Factorise (?P<rest>.+)$",
       hi="गुणनखंड कीजिए: {rest}",
       hinglish="Factorise karo: {rest}"),
    _R(r"^(?P<expr>.+?) = 0 gives (?P<rest>.+)$",
       hi="{expr} = 0 से {rest} मिलता है",
       hinglish="{expr} = 0 se {rest} milta hai"),
    _R(r"^Move the constant to the right: (?P<rest>.+)$",
       hi="अचर को दाईं ओर ले जाइए: {rest}",
       hinglish="Constant ko right side le jao: {rest}"),
    _R(r"^Add (?P<x>.+?) to both sides to complete the square: "
       r"(?P<rest>.+)$",
       hi="वर्ग पूरा करने के लिए दोनों ओर {x} जोड़िए: {rest}",
       hinglish="Square complete karne ke liye dono side {x} "
                "add karo: {rest}"),
    _R(r"^Left side is a perfect square: (?P<rest>.+)$",
       hi="बायाँ पक्ष एक पूर्ण वर्ग है: {rest}",
       hinglish="Left side ek perfect square hai: {rest}"),
    _R(r"^Take square roots: (?P<rest>.+)$",
       hi="वर्गमूल लीजिए: {rest}",
       hinglish="Square roots lo: {rest}"),
    _R(r"^Equations: (?P<rest>.+)$",
       hi=lambda g, t: "समीकरण: " + g["rest"].replace(
           " and ", " और "),
       hinglish="Equations: {rest}"),
    _R(r"^Add the two equations — the (?P<v>.+?) terms cancel: "
       r"(?P<rest>.+)$",
       hi="दोनों समीकरणों को जोड़िए — {v} पद कट जाते हैं: {rest}",
       hinglish="Dono equations ko add karo — {v} terms cancel "
                "ho jate hain: {rest}"),
    _R(r"^Put (?P<lhs>.+?) in equation \((?P<k>.+?)\): "
       r"(?P<rest>.+)$",
       hi="{lhs} को समीकरण ({k}) में रखिए: {rest}",
       hinglish="{lhs} ko equation ({k}) me rakho: {rest}"),
    _R(r"^Put (?P<lhs>.+?): (?P<rest>.+)$",
       hi="{lhs} रखिए: {rest}",
       hinglish="{lhs} rakho: {rest}"),
    # ---- number theory ----------------------------------------------
    _R(r"^Prime factorisation: (?P<rest>.+)$",
       hi="अभाज्य गुणनखंड: {rest}",
       hinglish="Prime factorisation: {rest}"),
    _R(r"^Take the lowest power of each common prime factor\.$",
       hi="प्रत्येक उभयनिष्ठ अभाज्य गुणनखंड की सबसे छोटी घात "
          "लीजिए।",
       hinglish="Har common prime factor ki sabse chhoti power "
                "lo."),
    _R(r"^Take the highest power of every prime factor\.$",
       hi="प्रत्येक अभाज्य गुणनखंड की सबसे बड़ी घात लीजिए।",
       hinglish="Har prime factor ki sabse badi power lo."),
    _R(r"^Euclid's method: divide the bigger number by the "
       r"smaller; the HCF of the divisor and the remainder is "
       r"the same HCF\. Repeat until the remainder is 0\.$",
       hi="यूक्लिड की विधि: बड़ी संख्या को छोटी संख्या से भाग "
          "दीजिए; भाजक और शेषफल का HCF वही HCF होता है। शेषफल "
          "0 आने तक दोहराइए।",
       hinglish="Euclid ki method: badi number ko chhoti number "
                "se divide karo; divisor aur remainder ka HCF "
                "wahi HCF hota hai. Remainder 0 aane tak repeat "
                "karo."),
    _R(r"^(?P<a>.+?) ÷ (?P<b>.+?) = (?P<q>.+?) remainder "
       r"(?P<r>.+)$",
       hi="{a} ÷ {b} = {q}, शेषफल {r}",
       hinglish="{a} ÷ {b} = {q} remainder {r}"),
    _R(r"^The last non-zero divisor is the HCF: (?P<rest>.+)$",
       hi="आखिरी अशून्य भाजक ही HCF है: {rest}",
       hinglish="Last non-zero divisor hi HCF hai: {rest}"),
    # ---- percent / interest / commercial ----------------------------
    _R(r"^(?P<p>.+?)% means (?P<rest>.+)$",
       hi="{p}% का अर्थ है {rest}",
       hinglish="{p}% ka matlab hai {rest}"),
    _R(r"^Multiply by (?P<n>.+?): (?P<rest>.+)$",
       hi="{n} से गुणा कीजिए: {rest}",
       hinglish="{n} se guna karo: {rest}"),
    _R(r"^(?P<p>.+?)% of (?P<n>.+?) = (?P<rest>.+)$",
       hi="{n} का {p}% = {rest}",
       hinglish="{n} ka {p}% = {rest}"),
    _R(r"^Simple Interest = (?P<rest>.+)$",
       hi="साधारण ब्याज = {rest}",
       hinglish="Simple Interest = {rest}"),
    _R(r"^Simple interest = (?P<rest>.+)$",
       hi="साधारण ब्याज = {rest}",
       hinglish="Simple interest = {rest}"),
    _R(r"^Total amount = (?P<rest>.+)$",
       hi="कुल राशि = {rest}",
       hinglish="Total amount = {rest}"),
    _R(r"^Compound interest: (?P<rest>.+)$",
       hi="चक्रवृद्धि ब्याज: {rest}",
       hinglish="Compound interest: {rest}"),
    _R(r"^Compound interest = (?P<rest>.+)$",
       hi="चक्रवृद्धि ब्याज = {rest}",
       hinglish="Compound interest = {rest}"),
    _R(r"^Cost price \(CP\) = (?P<rest>.+)$",
       hi="क्रय मूल्य (CP) = {rest}",
       hinglish="Cost price (CP) = {rest}"),
    _R(r"^Profit % = (?P<rest>.+)$",
       hi="लाभ % = {rest}",
       hinglish="Profit % = {rest}"),
    _R(r"^Profit = (?P<rest>.+)$",
       hi="लाभ = {rest}",
       hinglish="Profit = {rest}"),
    _R(r"^Loss = (?P<rest>.+)$",
       hi="हानि = {rest}",
       hinglish="Loss = {rest}"),
    # ---- mensuration / geometry labels ------------------------------
    _R(r"^Take pi = (?P<a>.+?) here — (?P<reason>.+?), so the "
       r"answer comes out exact\.$",
       hi=lambda g, t: "यहाँ pi = %s लीजिए — %s, इसलिए उत्तर "
           "ठीक-ठीक आएगा।" % (
               g["a"],
               _sub_en_words(
                   g["reason"].replace(
                       "is a multiple of", "का गुणज है").replace(
                       "are multiples of", "के गुणज हैं"),
                   {"radius": "त्रिज्या", "diameter": "व्यास",
                    "circumference": "परिधि"})),
       hinglish="Yahan pi = {a} lo — {reason}, isliye answer "
                "exact aayega."),
    _R(r"^Area = (?P<rest>.+)$",
       hi="क्षेत्रफल = {rest}",
       hinglish="Area = {rest}"),
    _R(r"^Circumference = (?P<rest>.+)$",
       hi="परिधि = {rest}",
       hinglish="Circumference = {rest}"),
    _R(r"^Perimeter = (?P<rest>.+)$",
       hi="परिमाप = {rest}",
       hinglish="Perimeter = {rest}"),
    _R(r"^Volume = (?P<rest>.+)$",
       hi="आयतन = {rest}",
       hinglish="Volume = {rest}"),
    _R(r"^Distance = (?P<rest>.+)$",
       hi="दूरी = {rest}",
       hinglish="Distance = {rest}"),
    _R(r"^Midpoint = (?P<rest>.+)$",
       hi="मध्य बिंदु = {rest}",
       hinglish="Midpoint = {rest}"),
    _R(r"^Median = (?P<rest>.+)$",
       hi="माध्यक = {rest}",
       hinglish="Median = {rest}"),
    _R(r"^A (?P<poly>[a-z]+) splits into (?P<n>.+?) triangles "
       r"along its diagonals\.$",
       hi=lambda g, t: "एक %s अपने विकर्णों के साथ %s "
           "त्रिभुजों में बँटता है।" % (
               _POLYGONS_HI.get(g["poly"], g["poly"]), g["n"]),
       hinglish="Ek {poly} apne diagonals ke saath {n} "
                "triangles me bant-ta hai."),
    _R(r"^Sum of angles = (?P<rest>.+)$",
       hi="कोणों का योग = {rest}",
       hinglish="Angles ka sum = {rest}"),
    _R(r"^The angles of a triangle add to (?P<rest>.+)$",
       hi="त्रिभुज के कोणों का योग {rest} होता है",
       hinglish="Triangle ke angles ka sum {rest} hota hai"),
    _R(r"^Third angle = (?P<rest>.+)$",
       hi="तीसरा कोण = {rest}",
       hinglish="Third angle = {rest}"),
    # ---- statistics ---------------------------------------------------
    _R(r"^Add all values: (?P<rest>.+)$",
       hi="सभी मानों को जोड़िए: {rest}",
       hinglish="Saare values add karo: {rest}"),
    _R(r"^Arrange in order: (?P<rest>.+)$",
       hi="क्रम में लगाइए: {rest}",
       hinglish="Order me lagao: {rest}"),
    _R(r"^Take the middle value\.$",
       hi="बीच वाला मान लीजिए।",
       hinglish="Beech wala value lo."),
    _R(r"^Count how often each value appears in: (?P<rest>.+)$",
       hi="गिनिए कि प्रत्येक मान कितनी बार आया है: {rest}",
       hinglish="Gino ki har value kitni baar aayi hai: {rest}"),
    _R(r"^The most frequent value\(s\): (?P<rest>.+)$",
       hi="सबसे अधिक बार आने वाला मान: {rest}",
       hinglish="Sabse zyada baar aane wala value: {rest}"),
    # ---- sequences ----------------------------------------------------
    _R(r"^AP with a = (?P<rest>.+)$",
       hi="समांतर श्रेणी (AP) में a = {rest}",
       hinglish="AP me a = {rest}"),
    _R(r"^nth term: (?P<rest>.+)$",
       hi="nवाँ पद: {rest}",
       hinglish="nth term: {rest}"),
    _R(r"^Sum of first n terms: (?P<rest>.+)$",
       hi="प्रथम n पदों का योग: {rest}",
       hinglish="First n terms ka sum: {rest}"),
    _R(r"^Write out all the terms of the GP: ?(?P<rest>.*)$",
       hi="GP के सभी पद लिखिए: {rest}",
       hinglish="GP ke saare terms likho: {rest}"),
    # ---- evaluate / simplify / misc -----------------------------------
    _R(r"^Use the standard values \((?P<rest>.+)\)\.$",
       hi="मानक मानों का उपयोग कीजिए ({rest})।",
       hinglish="Standard values use karo ({rest})."),
    _R(r"^The expression evaluates to (?P<rest>.+)$",
       hi="व्यंजक का मान {rest} आता है",
       hinglish="Expression ka value {rest} aata hai"),
    _R(r"^The expression simplifies to (?P<rest>.+)$",
       hi="व्यंजक सरल होकर {rest} आता है",
       hinglish="Expression simplify hokar {rest} aata hai"),
    _R(r"^Evaluate: (?P<rest>.+)$",
       hi="मान निकालिए: {rest}",
       hinglish="Evaluate karo: {rest}"),
    _R(r"^Expand: (?P<rest>.+)$",
       hi="विस्तार कीजिए: {rest}",
       hinglish="Expand karo: {rest}"),
    _R(r"^Expanded form: (?P<rest>.+)$",
       hi="विस्तारित रूप: {rest}",
       hinglish="Expanded form: {rest}"),
    _R(r"^Simplify (?P<expr>.+): cancel common factors and "
       r"combine like terms\.$",
       hi="सरल कीजिए {expr}: उभयनिष्ठ गुणनखंड काटिए और समान "
          "पदों को मिलाइए।",
       hinglish="Simplify karo {expr}: common factors cancel "
                "karo aur like terms combine karo."),
    _R(r"^Simplify: (?P<rest>.+)$",
       hi="सरल कीजिए: {rest}",
       hinglish="Simplify karo: {rest}"),
    _R(r"^Simplify (?P<rest>.+)$",
       hi="सरल कीजिए {rest}",
       hinglish="Simplify karo {rest}"),
    _R(r"^Multiply out the brackets in (?P<expr>.+) term by "
       r"term \(FOIL for two brackets\)\.$",
       hi="{expr} में कोष्ठकों को पद-दर-पद खोलिए (दो कोष्ठकों "
          "के लिए FOIL)।",
       hinglish="{expr} ke brackets ko term by term kholo (do "
                "brackets ke liye FOIL)."),
    _R(r"^The highest power of x is (?P<rest>.+)\.$",
       hi="x की सबसे बड़ी घात {rest} है।",
       hinglish="x ki sabse badi power {rest} hai."),
    _R(r"^Write the expression: (?P<rest>.+)$",
       hi="व्यंजक लिखिए: {rest}",
       hinglish="Expression likho: {rest}"),
    _R(r"^Write as (?P<form>.+?): (?P<rest>.+)$",
       hi="{form} के रूप में लिखिए: {rest}",
       hinglish="{form} ke roop me likho: {rest}"),
    _R(r"^Convert to the base unit: (?P<rest>.+)$",
       hi="आधार इकाई में बदलिए: {rest}",
       hinglish="Base unit me convert karo: {rest}"),
    _R(r"^Convert to (?P<u>.+?): (?P<rest>.+)$",
       hi="{u} में बदलिए: {rest}",
       hinglish="{u} me convert karo: {rest}"),
    _R(r"^Time = distance ÷ speed = (?P<rest>.+)$",
       hi=lambda g, t: "समय = दूरी ÷ चाल = "
           + _units_to_hi(g["rest"]),
       hinglish="Time = distance ÷ speed = {rest}"),
    _R(r"^Cube of (?P<n>.+?) = (?P<rest>.+)$",
       hi="{n} का घन = {rest}",
       hinglish="{n} ka cube = {rest}"),
    _R(r"^Divide (?P<a>.+?) into (?P<b>.+?) equal parts: "
       r"(?P<rest>.+)$",
       hi="{a} को {b} बराबर भागों में बाँटिए: {rest}",
       hinglish="{a} ko {b} equal parts me baanto: {rest}"),
    _R(r"^Take (?P<n>.+?) part\(s\): (?P<rest>.+)$",
       hi="{n} भाग लीजिए: {rest}",
       hinglish="{n} part(s) lo: {rest}"),
    _R(r"^The (?P<n>.+?)th root of (?P<x>.+?) is the number "
       r"whose (?P<n2>.+?)th power is (?P<x2>.+?)\.$",
       hi="{x} का {n}वाँ मूल वह संख्या है जिसकी {n}वीं घात "
          "{x} है।",
       hinglish="{x} ka {n}th root woh number hai jiski {n}th "
                "power {x} hai."),
    _R(r"^log base (?P<b>.+?) of (?P<x>.+?) asks: (?P<b2>.+?) "
       r"raised to what power gives (?P<x2>.+?)\?$",
       hi="log आधार {b} का {x} पूछता है: {b} की कौन-सी घात "
          "{x} देगी?",
       hinglish="log base {b} of {x} poochta hai: {b} ki "
                "kaun-si power {x} degi?"),
    _R(r"^(?P<lhs>.+?), so the answer is (?P<rest>.+)$",
       hi="{lhs}, इसलिए उत्तर है {rest}",
       hinglish="{lhs}, isliye answer hai {rest}"),
    # ---- probability ----------------------------------------------------
    _R(r"^A fair coin has (?P<n>.+?) equally likely outcomes; "
       r"heads is (?P<m>.+?) of them\.$",
       hi="एक निष्पक्ष सिक्के के {n} समान संभावना वाले परिणाम "
          "होते हैं; चित (heads) उनमें से {m} है।",
       hinglish="Ek fair coin ke {n} equally likely outcomes "
                "hote hain; heads unme se {m} hai."),
    _R(r"^Total = (?P<t>.+?); (?P<w>[a-z]+) count = (?P<n>.+)$",
       hi=lambda g, t: "कुल = %s; %s की संख्या = %s" % (
           g["t"], _COLOURS.get(g["w"], g["w"]), g["n"]),
       hinglish="Total = {t}; {w} count = {n}"),
    _R(r"^Count the balls: (?P<rest>.+)$",
       hi=lambda g, t: "गेंदें गिनिए: "
           + _sub_en_words(g["rest"], _COLOURS),
       hinglish="Balls gino: {rest}"),
    _R(r"^Favourable \((?P<w>.+?)\) = (?P<rest>.+)$",
       hi=lambda g, t: "अनुकूल (%s) = %s" % (
           _COLOURS.get(g["w"], g["w"]), g["rest"]),
       hinglish="Favourable ({w}) = {rest}"),
    _R(r"^Probability = (?P<rest>.+)$",
       hi="प्रायिकता = {rest}",
       hinglish="Probability = {rest}"),
    # ---- graph method (alternate methods) -------------------------------
    _R(r"^Draw (?P<expr>.+?) — a parabola opening upwards\.$",
       hi="{expr} का ग्राफ़ बनाइए — यह ऊपर की ओर खुलने वाला "
          "परवलय (parabola) है।",
       hinglish="{expr} ka graph banao — ye upar ki taraf "
                "khulne wala parabola hai."),
    _R(r"^Draw (?P<expr>.+?) — a parabola opening downwards\.$",
       hi="{expr} का ग्राफ़ बनाइए — यह नीचे की ओर खुलने वाला "
          "परवलय (parabola) है।",
       hinglish="{expr} ka graph banao — ye neeche ki taraf "
                "khulne wala parabola hai."),
    _R(r"^Vertex: (?P<rest>.+)$",
       hi="शीर्ष (vertex): {rest}",
       hinglish="Vertex: {rest}"),
    _R(r"^y-intercept \(x = 0\) is (?P<rest>.+)\.$",
       hi="y-अंतःखंड (x = 0) {rest} है।",
       hinglish="y-intercept (x = 0) {rest} hai."),
    _R(r"^The roots are the x-values where the parabola crosses "
       r"the x-axis \(y = 0\): (?P<rest>.+)$",
       hi="मूल वे x-मान हैं जहाँ परवलय x-अक्ष को काटता है "
          "(y = 0): {rest}",
       hinglish="Roots woh x-values hain jahan parabola x-axis "
                "ko cross karta hai (y = 0): {rest}"),
    # ---- salvage note + step-explain scaffolding -------------------------
    _R(r"^Solved the maths part of your question: (?P<rest>.+)$",
       hi="आपके सवाल का गणित वाला हिस्सा हल किया: {rest}",
       hinglish="Tumhare sawaal ka maths wala hissa solve "
                "kiya: {rest}"),
    _R(r"^Step (?P<n>\d+): (?P<rest>.+)$",
       hi=lambda g, t: "चरण %s: %s" % (
           g["n"], translate_step(g["rest"], "hi")),
       hinglish=lambda g, t: "Step %s: %s" % (
           g["n"], translate_step(g["rest"], "hinglish"))),
    _R(r"^Why: (?P<rest>.+)$",
       hi="क्यों: {rest}",
       hinglish="Why: {rest}"),
    _R(r"^If this is clear now, type 'next step samjhao' and I "
       r"will explain the next step too\.$",
       hi="अब यह समझ आ गया हो तो 'next step samjhao' लिखिए, "
          "मैं अगला चरण भी समझा दूँगा।",
       hinglish="Ab ye clear ho gaya ho to 'next step samjhao' "
                "likho, main agla step bhi samjha dunga."),

    # ---- Hindi (Devanagari) source rules -------------------------------
    _R(r"^मूलधन P = Rs (?P<p>.+?), दर R = (?P<r>.+?)%, समय "
       r"T = (?P<t>.+?) वर्ष$",
       src="hi",
       en="Principal P = Rs {p}, rate R = {r}%, time T = {t} "
          "years",
       hinglish="Mooldhan P = Rs {p}, dar R = {r}%, samay "
                "T = {t} saal"),
    _R(r"^साधारण ब्याज = (?P<rest>.+)$",
       src="hi",
       en="Simple interest = {rest}",
       hinglish="Sadharan byaaj = {rest}"),
    _R(r"^यहाँ pi = (?P<a>.+?) लिया है, इसलिए उत्तर ठीक-ठीक "
       r"आएगा।$",
       src="hi",
       en="Take pi = {a} here, so the answer comes out exact.",
       hinglish="Yahan pi = {a} liya hai, isliye answer exact "
                "aayega."),
    _R(r"^वृत्त का क्षेत्रफल = (?P<rest>.+)$",
       src="hi",
       en=lambda g, t: "Area of the circle = "
           + _sub_hi_words(g["rest"]),
       hinglish=lambda g, t: "Circle ka area = "
           + _sub_hi_words(g["rest"])),
    _R(r"^(?P<shape>वर्ग|आयत|त्रिभुज|वृत्त) का परिमाप = "
       r"(?P<rest>.+)$",
       src="hi",
       en=lambda g, t: "Perimeter = " + _sub_hi_words(
           g["rest"]),
       hinglish=lambda g, t: "Perimeter = " + _sub_hi_words(
           g["rest"])),
    _R(r"^(?P<what>.+?) का क्षेत्रफल = (?P<rest>.+)$",
       src="hi",
       en=lambda g, t: "Area = " + _sub_hi_words(g["rest"]),
       hinglish=lambda g, t: "Area = " + _sub_hi_words(
           g["rest"])),
    _R(r"^बिंदु \((?P<p>.+?)\) की रेखा (?P<line>.+?) से दूरी "
       r"= (?P<rest>.+)$",
       src="hi",
       en="Distance of point ({p}) from the line {line} = "
          "{rest}",
       hinglish="Point ({p}) ki line {line} se doori = {rest}"),
    _R(r"^प्रवणता (?P<rest>.+)$",
       src="hi",
       en="Slope {rest}",
       hinglish="Slope {rest}"),
    _R(r"^बिंदु \((?P<p>.+?)\): x (?P<sx>[+−-]) है और y "
       r"(?P<sy>[+−-]) है।$",
       src="hi",
       en=lambda g, t: "Point (%s): x is %s and y is %s." % (
           g["p"],
           "positive" if g["sx"] == "+" else "negative",
           "positive" if g["sy"] == "+" else "negative"),
       hinglish=lambda g, t: "Point (%s): x %s hai aur y %s "
           "hai." % (
               g["p"],
               "positive" if g["sx"] == "+" else "negative",
               "positive" if g["sy"] == "+" else "negative")),
    _R(r"^चिह्न \((?P<s>.+?)\) वाला बिंदु (?P<q>प्रथम|द्वितीय|"
       r"तृतीय|चतुर्थ|पंचम) चतुर्थांश \((?P<r>.+?)\) में होता "
       r"है।$",
       src="hi",
       en=lambda g, t: "A point with signs (%s) lies in the "
           "%s quadrant (%s)." % (
               g["s"], _ORDINALS.get(g["q"], g["q"]), g["r"]),
       hinglish=lambda g, t: "Sign (%s) wala point %s quadrant "
           "(%s) me hota hai." % (
               g["s"], _ORDINALS.get(g["q"], g["q"]), g["r"])),
]

_RULES_BY_SRC = {"en": [], "hi": []}
for _rule in _RULES:
    _RULES_BY_SRC[_rule[0]].append(_rule)


def _render(tmpl, groups, target):
    if tmpl is None:
        return None
    if callable(tmpl):
        return tmpl(groups, target)
    return tmpl.format_map(groups)


def translate_step(step, target):
    """One step line rendered in ``target`` ("en" / "hi" /
    "hinglish") when a rule covers it; the line itself,
    unchanged, otherwise. A line already in the target
    language, or carrying no boilerplate at all, is returned
    as-is."""
    s = str(step or "")
    if target not in ("en", "hi", "hinglish"):
        return s
    src = step_language(s)
    if src is None or src == target:
        return s
    for _src, pat, renderings in _RULES_BY_SRC.get(src, ()):
        m = pat.match(s)
        if m is None:
            continue
        out = _render(renderings.get(target), m.groupdict(),
                      target)
        if out is not None:
            return out
    return s


def _step_handled(step, target):
    """True when ``step`` needs no work for ``target``: it is
    language-free, already in the target, or a rule renders
    it."""
    s = str(step or "")
    src = step_language(s)
    if src is None or src == target:
        return True
    return translate_step(s, target) != s or _matches(s, src,
                                                     target)


def _matches(step, src, target):
    for _src, pat, renderings in _RULES_BY_SRC.get(src, ()):
        if renderings.get(target) is not None \
                and pat.match(step) is not None:
            return True
    return False


def analyse_steps(steps, target):
    """Coverage accounting for a list of step lines: how many
    carry boilerplate in a language other than ``target``
    (``foreign``) and how many of those a rule renders
    (``covered``). Language-free and already-target lines are
    not counted either way."""
    foreign = covered = 0
    for s in steps or ():
        src = step_language(s)
        if src is None or src == target:
            continue
        foreign += 1
        if _matches(str(s), src, target):
            covered += 1
    return {"foreign": foreign, "covered": covered}


def relanguage_steps(steps, target):
    """``steps`` with every covered line rendered in
    ``target``. Returns the ORIGINAL list object when nothing
    changed, so callers can tell."""
    if not steps:
        return steps
    out = [translate_step(s, target) for s in steps]
    if all(a == b for a, b in zip(out, steps)):
        return steps
    return out


# Result kinds whose steps are solver-family template output:
# the raw solver (no kind), the Wave-76 MCQ wrap (no kind) and
# the salvage layer ("salvage" — a solver result plus one note
# line). Everything else — concept cards, proofs (bilingual
# data, switched by the chain's own flag), the AI legs
# (kind gemini/groq/openrouter), one-line replies — is built
# language-aware already and is never touched here.
_SOLVER_KINDS = (None, "salvage")


def relanguage_result(result, target):
    """A copy of ``result`` with its steps rendered in
    ``target`` when the result is solver-family output;
    ``result`` itself, unchanged, in every other case (and
    whenever no step actually changes). The input dict and
    its steps list are never mutated — the solver's answer
    cache shares them."""
    if not isinstance(result, dict):
        return result
    if result.get("fallback_kind") not in _SOLVER_KINDS:
        return result
    if result.get("ai_generated"):
        return result
    steps = result.get("steps")
    if not isinstance(steps, list) or not steps:
        return result
    new_steps = relanguage_steps(steps, target)
    if new_steps is steps:
        return result
    out = dict(result)
    out["steps"] = new_steps
    return out


# ---------------------------------------------------------------------------
# Alternate-method labels (solver/methods.py). Only the Hindi
# (Devanagari) renderings are tabled; a Hinglish request keeps
# the English label, which is how Hinglish students write them.
# ---------------------------------------------------------------------------

_METHOD_LABELS_HI = {
    "Adding all the sides": "सभी भुजाओं को जोड़कर",
    "Adding the terms": "पदों को जोड़कर",
    "Assumed mean method": "कल्पित माध्य विधि",
    "Base area × height method": "आधार क्षेत्रफल × ऊँचाई विधि",
    "Complement method": "पूरक विधि",
    "Completing the square": "वर्ग पूरा करने की विधि",
    "Counting unit squares": "इकाई वर्ग गिनकर",
    "Cross-multiplication method": "वज्र-गुणन विधि",
    "Direct percentage method": "सीधी प्रतिशत विधि",
    "Division method": "भाग विधि",
    "Elimination method": "विलोपन विधि",
    "Euclid's division method": "यूक्लिड की भाग विधि",
    "Factorisation method": "गुणनखंड विधि",
    "Fraction method": "भिन्न विधि",
    "Fraction of the whole method": "पूरे के भिन्न की विधि",
    "From the standard triangles": "मानक त्रिभुजों से",
    "Graph method": "ग्राफ़ विधि",
    "Half of a rectangle method": "आयत के आधे वाली विधि",
    "Identity method": "सर्वसमिका विधि",
    "Layer method": "परत विधि",
    "One-third of the cylinder": "बेलन का एक-तिहाई",
    "Pairing method": "जोड़ी विधि",
    "Position formula method": "स्थिति सूत्र विधि",
    "Proportion method": "समानुपात विधि",
    "Quadratic formula": "द्विघात सूत्र",
    "Single equivalent discount": "एकल समतुल्य छूट",
    "Step-by-step BODMAS": "चरण-दर-चरण BODMAS",
    "Substitution method": "प्रतिस्थापन विधि",
    "Transposition method": "पक्षांतरण विधि",
    "Unitary method": "ऐकिक विधि",
    "Using Euclid and the product relation":
        "यूक्लिड और गुणनफल संबंध का उपयोग",
    "Using the HCF relation": "HCF संबंध का उपयोग",
    "Using the diameter": "व्यास का उपयोग",
    "Writing out the terms": "पदों को लिखकर",
    "Year-by-year method": "वर्ष-दर-वर्ष विधि",
}


def relanguage_methods(methods, target):
    """Alternate-method payloads with steps (and, for a Hindi
    request, labels) rendered in ``target``. Returns the
    original list when nothing changes."""
    if not methods or target not in ("hi", "hinglish"):
        return methods
    out = []
    changed_any = False
    for method in methods:
        if not isinstance(method, dict):
            out.append(method)
            continue
        new = dict(method)
        steps = method.get("steps")
        if isinstance(steps, list) and steps:
            new_steps = relanguage_steps(steps, target)
            if new_steps is not steps:
                new["steps"] = new_steps
                changed_any = True
        if target == "hi":
            label = _METHOD_LABELS_HI.get(method.get("label"))
            if label:
                new["label"] = label
                changed_any = True
        out.append(new)
    return out if changed_any else methods
