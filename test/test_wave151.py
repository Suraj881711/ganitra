"""Wave 151 (Suraj, 18 Nov 2026): wrong-serve vetoes,
round 2 — built from Board 8's post-Wave-150
calibration (~/workspace/ganitra-wave135h-haryana-work/):
Boards 5/6's 591 book questions re-run against the
Wave-150-gated solver; serves fell 109 -> 64, but 33 of
the 64 remaining serves were still WRONG. This battery
is that calibration set: the 33 wrong serves (must now
decline), the 19 genuine serves and the 12 partial
serves (every served part correct but incomplete) as
controls (must keep serving). FED text is the exact
text Board 8 fed the solver, keyed by the row's idx
in the Boards 5/6 extraction (ganitra-book-questions
rows for Classes 7/8, Haryana calibration numbering).

Fixes (fallback._w151_veto, rules W26-W44, wired into
_is_real, both multipart seams, and — new in this wave —
the formats and graph layer seams, which returned their
results ungated):
 * W26 print-furniture numbers harvested as data
 * W27 multipart parts provably wrong (count part served
   a non-integer; why part served a bare number)
 * W28 unit-rate ask answered by a mean
 * W29 evaluator identity carve under a form / multi-
   part / expression-op / long ask-less page ask
 * W30 word-equation mashup across 3+ sub-problems
 * W31/W43 right-triangle verdicts for non-verdict asks
   / multi-triple asks checked once
 * W32 Kruti-glyph soup in the serve (त*र*्)
 * W33 figure-only ask with no numeric given, served a
   number
 * W34 pie serve contradicting the stated total / the
   total served as a slice
 * W35 probability computed for the wrong event (the
   steps name a different favourable colour)
 * W36 list-the-outcomes ask served a count/probability
 * W37 fabricated "0 - k = -k" evaluator carve
 * W38 Hindi cost-at-a-rate ask served money-less
 * W39 root self-verification (serve must root a
   stated radicand)
 * W40 comparison ask served a bare number
 * W41 form ask served a bare number
 * W42 expression-operation ask served a bare number
 * W44 smallest-square/cube-number ask served a
   perfect-square/cube verdict

Documented follow-ups (need real schemas, not vetoes):
the garbled-table means of Board 8 idx 63 part (i)/(iii)
(the card declines via its why-part), and the Class 8
Ch 2 equations whose Kruti parse is destroyed upstream
(their serves decline via W32; a Kruti-aware equation
parse would serve them correctly).
"""

import pytest

from api import _solve_friendly
from fallback import _w151_veto


@pytest.fixture(autouse=True)
def _hermetic(tmp_path, monkeypatch):
    """Fresh DB per test (the live bank must never
    replay a stored answer inside this battery) and
    no AI keys."""
    monkeypatch.setenv("GANITRA_DB_PATH",
                       str(tmp_path / "t.db"))
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/mplconfig")
    for name in ("GANITRA_GEMINI_API_KEY",
                 "GANITRA_GROQ_API_KEY",
                 "GANITRA_OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)


FED = {
    26: {'q': 'विद्या और प्रताप पिकनिक पर गए। उनकी माँ ने उन्हें 5 लीटर पानी वाली एक बोतल दी। विद्या ने वुफल पानी का 2 5 उपयोग किया। शेष पानी प्रताप ने पिया। (i) विद्या ने कितना पानी पिया? (ii) पानी की वुफल मात्राा का कितना भिन्न (fraction) प्रताप ने पिया? 2024.25 भिन्न एवं दशमलव 27 2.1ण्2 भिन्न का भिन्न से गुणन पफरीदा के पास 9 बउ लंबी एक रिबन की पटðी थी। उसने इस पटðी को चार समान भागों में काटा। उसने यह किस प्रकार किया? उसने पटðी को दो बार मोड़ा। प्रत्येक भाग वुफल लंबाई के किस भिन्न को निरूपित करेगा। प्रत्येक भाग, पटðी का 9 4 होगा। उसने इनमें से एक भाग लिया और इस भाग को एक बार मोड़ते हुए इसे दो बराबर भागों में बाँट दिया। इन दो टुकड़ों में से एक टुकड़ा क्या निरूपित करेगा? यह 9 4 का 1 2 अर्थात् 1 2 × 9 4 को निरूपित करेगा। आइए देखते हैं कि दो भिन्नों का गुणनपफल जैसे 1 × 9 को वैफसे ज्ञात किया जाए। इसे ज्ञात करने के लिए आइए सर्वप्रथम हम 1 2 × 1 3 जैसा गुणनपफल ज्ञात करना सीखते हैं। (ं) किसी संपूर्ण भाग का 1 3 हम वैफसे ज्ञात करते हैं? हम संपूर्ण को तीन समान भागों में बाँटते है। तीनों में से प्रत्येक भाग संपूर्ण के 1 3 भाग को निरूपित करता है। इन तीनों में से एक हिस्सा लीजिए और इसे छायांकित कर दीजिए जैसा कि आ कृति 2.8 में दर्शाया गया है। (इ) आप इस छायांकित भाग का 1 2 भाग वैफसे ज्ञात करोगे? इस छायांकित एक तिहाई (1 3 ) भाग को 2 समान भागों में बाँटिए। इन दोनों में से प्रत्येक भाग 1 3 के 1 2 को निरूपित करता है अर्थात् 1 2 × 1 3 को निरूपित करता है (आकृति 2.9)। इन दो भागों में से एक को बाहर निकाल लीजिए और इसे ष्।ष् नाम दे दीजिए। ष्।ष् 1 2 × 1 3 को निरूपित करता है। (ब) ष्।ष् संपूर्ण का कितना भाग है? यह जानने के लिए शेष 1 3 भागों में से प्रत्येक को 2 समान भागों में बाँटिए। अब आपके पास ऐसे कितने समान भाग हैं? ऐसे 6 समान भाग हैं। ष्।ष् इनमें से एक भाग है। अतः ष्।ष् संपूर्ण का 1 6 भाग है। इस प्रकार 1 2 × 1 3 त्र 1 6 आकृति 2.8 आकृति 2.9 । 2024.25 गणित28 हमने यह वैफसे निर्णय लिया कि ष्।ष् संपूर्ण का 1 6 भाग है? संपूर्ण को 2 × 3 त्र 6 भागों में बाँटा गया और 1 भाग इसमें से बाहर निकाला गया। अतः 1 2 × 1 3 त्र 1 6 त्र 1×1 2×3 अथवा 1 2 × 1 3 त्र 1×1 2×3 3 × 1 2 का मान भी इसी प्रकार ज्ञात किया जा सकता है। संपूर्ण को 2 समान भागों में बाँटिए और तब इनमें से किसी एक भाग को 3 समान भागों में बाँटिए। इनमें से एक भाग को लीजिए। यह 1 3 × 1 2 अर्थात् 1 6 भाग को निरूपित करेगा। इसलिए जैसा कि पहले चर्चा की जा चुकी है 1 3 × 1 2 त्र 1 6 त्र 1×1 3× 2 अतः 1 2 × 1 3 त्र 1 3 × 1 2 त्र 1 6 3 × 1 4 और 1 4 × 1 3 य 1 2 × 1 5 और 1 5 × 1 2 ज्ञात कीजिए और जाँच कीजिए कि क्या आप 3 × 1 4 त्र 1 4 × 1 3 य 1 2 × 1 5 त्र 1 5 × 1 2 पाते हैं? निम्नलिखित बक्सों को भरिए : (i) 1 2 × 1 7 त्र 1×1 2 × 7 त्र (ii) 1 5 × 1 7 त्र त्र (iii) 1 7 × 1 2 त्र त्र (iv) 1 7 × 1 5 त्र त्र', 'cls': 7},
    41: {'q': 'एक आयत की लंबाई 7.1 बउ और इसकी चौड़ाई 2.5 बउ है। आयत का क्षेत्रापफल क्या है?', 'cls': 7},
    42: {'q': 'ज्ञात कीजिए : (i) 0.2 × 6 (ii) 8 × 4.6 (iii) 2.71 × 5 (iv) 20.1 × 4 (v) 0.05 × 7 (vi) 211.02 × 4 (vii) 2 × 0.86', 'cls': 7},
    43: {'q': 'एक आयत का क्षेत्रापफल ज्ञात कीजिए जिसकी लंबाई 5.7 बउ और चौड़ाई 3 बउ है।', 'cls': 7},
    44: {'q': 'ज्ञात कीजिए : (i) 1.3 × 10 (ii) 36.8 × 10 (iii) 153.7 × 10 (iv) 168.07 × 10 (v) 31.1 × 100 (vi) 156.1 × 100 (vii) 3.62 × 100 (viii) 43.07 × 100 (पग) 0.5 × 10 (x) 0.08 × 10 (xi) 0.9 × 100 (xii) 0.03 × 1000', 'cls': 7},
    47: {'q': '4.2ए 3.8 और 7.6 का औसत ज्ञात कीजिए।', 'cls': 7},
    49: {'q': 'एक कार 2.2 घंटे में 89.1 ाउ की दूरी तय करती है। कार द्वारा 1 घंटे में तय की गई औसत दूरी कितनी है?', 'cls': 7},
    56: {'q': 'आशिष तीन क्रमागत दिनों में क्रमशः 4 घंटे, 5 घंटे और 3 घंटे पढ़ता है। उसके प्रतिदिन पढ़ने का औसत समय क्या है?', 'cls': 7},
    57: {'q': 'एक बल्लेबाज ने 6 पारियों (पददपदहे) में निम्नलिखित संख्याओं में रन बनाए: 36ए 35ए 50ए 46ए 60ए 55 एक पारी में उसके द्वारा बनाए गए रनों का माध्य ज्ञात कीजिए।', 'cls': 7},
    62: {'q': 'एक क्रिकेट खिलाड़ी ने 8 पारियों में निम्नलिखित रन बनाए : 58ए 76ए 40ए 35ए 46ए 50ए 0ए 100. उसका माध्य स्कोर (score) या रन ज्ञात कीजिए। 2024.25 आँकड़ों का प्रबंधन 51', 'cls': 7},
    63: {'q': 'निम्नलिखित सारणी प्रत्येक खिलाड़ी द्वारा चार खेलों में अर्जित किए गए अंकों को दर्शाती है: खिलाड़ी खेल खेल खेल खेल 1 2 3 4 । 14 16 10 10 ठ 0 8 6 4 ब् 8 11 खेला 13 नहीं अब निम्नलिखित प्रश्नों के उत्तर दीजिए : (i) प्रत्येक खेल में । द्वारा अर्जित औसत अंक ज्ञात करने के लिए, माध्य ज्ञात कीजिए। (ii) प्रत्येक खेल में ब् द्वारा अर्जित माध्य अंक ज्ञात करने के लिए, आप वुफल अंकों को 3 से भाग देंगे या 4 से? क्यों? (iii) ठ ने सभी चार खेलों में भाग लिया है। आप उसके अंकों का माध्य किस प्रकार ज्ञात करेंगे? (iv) किसका प्रदर्शन सबसे अच्छा है?', 'cls': 7},
    65: {'q': 'छह क्रमागत वर्षों में एक स्कूल में विद्यार्थियों की संख्या निम्नलिखित थी : 1555ए 1670ए 1750ए 2013ए 2540ए 2820 इस समय काल में स्कूल के विद्यार्थियों की माध्य संख्या ज्ञात कीजिए।', 'cls': 7},
    66: {'q': 'एक नगर में किसी विशेष सप्ताह के 7 दिनों में हुई वर्षा (उउ में) निम्नलिखित रूप से रिकॉर्ड की गई: दिन सोमवार मंगलवार बुधवार वृहस्पतिवार शुक्रवार शनिवार रविवार वर्षा 0.0 12.2 2.1 0.0 20.5 5.5 1.0 (उउ) (i) उपरोक्त आँकड़ों से वर्षा का परिसर ज्ञात कीजिए। (ii) इस सप्ताह की माध्य वर्षा ज्ञात कीजिए। (iii) कितने दिन वर्षा, माध्य वर्षा से कम रही?', 'cls': 7},
    67: {'q': '10 लड़कियों की ऊँचाइयाँ बउ में मापी गईं और निम्नलिखित परिणाम प्राप्त हुए: 135ए 150ए 139ए 128ए 151ए 132ए 146ए 149ए 143ए 141. (i) सबसे लंबी लड़की की लंबाई क्या है? 2024.25 गणित52 (ii) सबसे छोटी लड़की की लंबाई क्या है? (iii) इन आँकड़ों का परिसर क्या है? (iv) लड़कियों की माध्य ऊँचाई (लंबाई) क्या है? (v) कितनी लड़कियों की लंबाई, माध्य लंबाई से अधिक है?', 'cls': 7},
    68: {'q': 'निम्नलिखित संख्याओं का बहुलक ज्ञात कीजिए: 1ए 1ए 2ए 4ए 3ए 2ए 1ए 2ए 2ए 4', 'cls': 7},
    69: {'q': 'टीमों के एक समूह में खेले गए पुफटबॉल के मैचों में, जीतने के अंतर गोलों में (पद हवंसे) निम्नलिखित हैं : 1ए 3ए 2ए 5ए 1ए 4ए 6ए 2ए 5ए 2ए 2ए 2ए 4ए 1ए 2ए 3ए 1ए 1ए 2ए 3ए 2ए 6ए 4ए 3ए 2ए 1ए 1ए 4ए 2ए 1ए 5ए 3ए 3ए 2ए 3ए 2ए 4ए 2ए 1ए 2 इन आँकड़ों का बहुलक ज्ञात कीजिए।', 'cls': 7},
    70: {'q': 'निम्नलिखित संख्याओं का बहुलक ज्ञात कीजिए: 2ए 2ए 2ए 3ए 3ए 4ए 5ए 5ए 5ए 6ए 6ए 8', 'cls': 7},
    71: {'q': 'निम्नलिखित आँकड़ों का माध्यक ज्ञात कीजिए : 24ए 36ए 46ए 17ए 18ए 25ए 35', 'cls': 7},
    73: {'q': 'एक क्रिकेट मैच में खिलाड़ियों द्वारा बनाए गए रन इस प्रकार हैं : 6ए 15ए 120ए 50ए 100ए 80ए 10ए 15ए 8ए 10ए 15 इन आँकड़ों के माध्य, बहुलक और माध्यक ज्ञात कीजिए। क्या ये तीनों समान हैं?', 'cls': 7},
    74: {'q': 'एक कक्षा के 15 विद्यार्थियों के भार (ाह में) इस प्रकार हैं : 38ए 42ए 35ए 37ए 45ए 50ए 32ए 43ए 43ए 40ए 36ए 38ए 43ए 38ए 47 (i) इन आँकड़ों के बहुलक और माध्यक ज्ञात कीजिए। (ii) क्या इनके एक से अधिक बहुलक हैं?', 'cls': 7},
    75: {'q': 'निम्नलिखित आँकड़ों के बहुलक और माध्यक ज्ञात कीजिए : 13ए 16ए 12ए 14ए 19ए 12ए 14ए 13ए 14', 'cls': 7},
    96: {'q': 'त्र 3 × 5 त्र 15. समिका सत्य है। 2024.25 गणित72 एक संतुलित समीकरण तराजू जैसी है जिसके दोनों पलड़ों में बराबर बाँट रखें हों। आइए अब हम उपरोक्त समिका के दोनों पक्षों को 2 से भाग करें । LHS त्र 5(8 3. 2 5 2 2− झ् त्र झ् त्र RHS त्र 5(4', 'cls': 7},
    109: {'q': 'निम्नलिखित को हल कीजिए : (ं) अध्यापिका बताती है कि उनकी कक्षा में एक विद्यार्थी द्वारा प्राप्त किए गए अध्कितम अंक, प्राप्त किए न्यूनतम अंक का दुगुना जमा 7 है। प्राप्त किए गए अध्कितम अंक 87 हैं। प्राप्त किए गए न्यूनतम अंक क्या हैं? (इ) किसी समद्विबाहु त्रिभुज में आधर कोण बराबर होते हैं। शीर्ष कोण 40° है। इस त्रिभुज के आधार कोण क्या हैं? (याद कीजिए कि त्रिभुज के तीनों कोणों का योग 180° होता है।) (ब) सचिन द्वारा बनाए गए रनों की संख्या राहुल द्वारा बनाए गए रनों की संख्या की दुगुनी है। उन दोनों द्वारा मिलकर बनाए गए वुफल रन एक दोहरे शतक से 2 रन कम हैं। प्रत्येक ने कितने रन बनाए थे?', 'cls': 7},
    137: {'q': 'एक त्रिभुज के दो कोण 30° तथा 80° हैं । इस त्रिभुज का तीसरा कोण ज्ञात कीजिए ।', 'cls': 7},
    139: {'q': 'किसी त्रिभुज के तीनों कोणों में 1 : 2 : 1 का अनुपात है । त्रिभुज के तीनों कोण ज्ञात कीजिए । त्रिभुज का दोनों प्रकार से वर्गीकरण भी कीजिए ।', 'cls': 7},
    144: {'q': 'त्रिभुज ABC की एक माध्यिका ।ड है । बताइए कि क्या ।ठ ़ BC ़ CA झ 2 AM? (संकेत : ∆।ठड तथा ∆।डब् की भुजाओं पर विचार कीजिए ।) 2024.25 त्रिभुज और उसके गुण 111', 'cls': 7},
    148: {'q': 'एक त्रिभुज की भुजाएँ 3 बउए 4बउ तथा 5बउ लंबी हैं। निर्धरित कीजिए कि क्या वह एक समकोण त्रिभुज है ?', 'cls': 7},
    153: {'q': 'निम्नलिखित में भुजाओं के कौन से समूह एक समकोण त्रिभुज बना सकते हैं ? (i) 2.5 बउए 6.5 बउए6 बउ (ii) 2 बउए 2 बउए 5 बउ (iii) 1.5 बउए 2 बउए 2.5 बउ समकोण त्रिभुज होने की स्थिति में उसके समकोण को भी पहचानिए ।', 'cls': 7},
    216: {'q': 'त्रिभुज ABC, । पर समकोण है (आकृति 9.16), और AD भुजा BC पर लंब है। यदि ।ठ त्र 5 बउ, BC त्र 13 बउ और AC त्र 12 बउ है, तो ∆।ठब् का क्षेत्रापफल ज्ञात कीजिए। AD की लंबाई भी ज्ञात कीजिए। 2024.25 परिमाप और क्षेत्रापफल 165', 'cls': 7},
    219: {'q': 'एक वृत्ताकार तश्तरी (कपेब) की परिधि् ज्ञात कीजिए जिसकी त्रिज्या 14 बउ है। प्रयोग करें π त्र\uf8eb \uf8ed\uf8ec \uf8f6 \uf8f8\uf8f722 7', 'cls': 7},
    276: {'q': 'निम्नलिखित संख्याओं की तुलना कीजिए : (i) 2.7 × 1012 य 1.5 × 108 (ii) 4 × 1014 य 3 × 1017', 'cls': 7},
    280: {'q': '8 × 8 × 8 × 8 के लिए, आधर 2 लेते हुए, इसे घातांकीय रूप में लिखिए।', 'cls': 7},
    290: {'q': 'निम्नलिखित प्रसारित रूपों में से प्रत्येक के लिए संख्या ज्ञात कीजिए : (ं) 8 ×104 ़ 6 ×103 ़ 0×102 ़ 4×101 ़ 5×100 (इ) 4 ×105 ़ 5×103 ़ 3×102 ़ 2×100 (ब) 3 ×104 ़ 7×102 ़ 5×100 (क) 9 ×105 ़ 2×102 ़ 3×101', 'cls': 7},
    292: {'q': 'निम्नलिखित कथनों में प्रकट होने वाली (आने वाली) संख्याओं को मानक रूप में व्यक्त कीजिए। (ं) पृथ्वी और चंद्रमा के बीच की दूरी 384ए000ए000 उ है। (इ) निर्वात स्थान में प्रकाश की चाल (या वेग) 300ए000ए000 उधेमबण् है। (ब) पृथ्वी का व्यास 12756000 उ है। (क) सूर्य का व्यास 1ए400ए000ए000 उ है। (म) एक आकाशगंगा में औसतन 100ए000ए000ए000 तारे हैं। (द्धि विश्व मंडल (या सौर मंडल) 12ए000ए000ए000 वर्ष पुराना आकलित किया गया है। (ह) आकाशगंगा के मध्य से सूर्य की दूरी 300ए000ए000ए000ए000ए000ए000 उ आकलित की गई है। (ी) 1.8 ह भार वाली पानी की एक बूंद में 60ए230ए000ए000ए000ए000ए000ए000 अणु (उवसमबनसमे) होते हैं। (i) पृथ्वी में 1ए353ए000ए000 ाउ3 समुद्र जल है। (र) मार्च 2001 में भारत की जनसंख्या 1ए027ए000ए000 थी। 2024.25 गणित198', 'cls': 7},
    339: {'q': '5ज – 3 त्र 3ज – 5', 'cls': 8},
    342: {'q': '2ग – 1 त्र 14 – ग', 'cls': 8},
    347: {'q': '3उ त्र 5 उ – 8 5', 'cls': 8},
    353: {'q': '5 3 3 5 ग ग− −त्र', 'cls': 8},
    380: {'q': 'संलग्न आवृफति HOPE एक समांतर चतुर्भुज है। गए ल और ्र कोणों की माप ज्ञात कीजिए। ज्ञात करने में प्रयोग किए गए गुणों को बताइए।', 'cls': 8},
    395: {'q': 'रू एक विशेष दिन किसी बेकरी की दुकान में हुई विभिन्न वस्तुओं की बिक्री (रुपयों मेंद्ध नीचे दी गई है: सामान्य ब्रेड : 320 Úूट ब्रेड : 80 केक और पेस्ट्री : 160 इन आँकड़ों के लिए एक पाई चार्ट खींचिए। बिस्वुफट : 120 अन्य : 40 वुफल : 720', 'cls': 8},
    401: {'q': 'रू एक थैले में 4 लाल गेंदें और 2 पीली गेंदें हैं। (ये गेंदें रंग के अतिरिक्त सभी प्रकार से एक जैसी, अर्थात् सर्वसम (identical) हैं।द्ध थैले के अंदर से बिना देखे एक गेंद निकाली जाती है। एक लाल गेंद प्राप्त करने की क्या प्रायिकता है? क्या यह एक पीली गेंद प्राप्त करने की प्रायिकता से अध्कि है या कम?', 'cls': 8},
    402: {'q': 'इन प्रयोगों में आप जो परिणाम देख सकते हैं उन्हें लिखिए : (ं) पहिए को घुमाना (इ) दो सिक्कों को एक साथ उछालना', 'cls': 8},
    403: {'q': 'जब एक पासे को पेंफका जाता है, तब निम्नलिखित प्रत्येक घटना से प्राप्त होने वाले परिणामों को लिखिए : (i) (ं) एक अभाज्य संख्या (इ) एक अभाज्य संख्या नहीं (ii) (ं) 5 से बड़ी एक संख्या (इ) 5 से बड़ी संख्या नहीं', 'cls': 8},
    404: {'q': 'ज्ञात कीजिए : (ं) (प्रश्न 1(ं) मेंद्धसूचक के क् पर रुकने की प्रायिकता। (इ) अच्छी प्रकार से पेफटी हुई 52 ताशों की एक गड्डी में से 1 इक्का प्राप्त करने की प्रायिकता। (ब) एक लाल सेब प्राप्त करने की प्रायिकता (दी हुई आकृति से देखिएद्ध।', 'cls': 8},
    420: {'q': 'रू 6400 का वर्गमूल ज्ञात कीजिए?', 'cls': 8},
    421: {'q': 'रू क्या 90 एक पूर्ण वर्ग है?', 'cls': 8},
    422: {'q': 'रू क्या 2352 एक पूर्ण वर्ग संख्या है? यदि नहीं तो 2352 का सबसे छोटा गुणज प्राप्त कीजिए जो कि पूर्ण वर्ग संख्या हो तथा नयी संख्या का वर्गमूल ज्ञात कीजिए। 2 256 2 128 2 64 2 16 2 8 2 4 2 2352 2 1176 2 588 2 294 7 49 2 6400 2 3200 2 1600 2 400 2 200 2 100 2 50 5 25 2 90 3 45 3 15 2024.25 वर्ग और वर्गमूल 69', 'cls': 8},
    427: {'q': 'बार-बार घटाने की विधि् से 100 और 169 का वर्गमूल ज्ञात कीजिए।', 'cls': 8},
    434: {'q': 'वह सबसे छोटी वर्ग संख्या ज्ञात कीजिए जो प्रत्येक 8, 15 और 20 से विभाजित हो जाए। 5.5ण्4 भागपफल विधि् से वर्गमूल ज्ञात करना जब संख्याएँ बड़ी हों तब अभाज्य गुणनखंड विधि् से वर्गमूल ज्ञात करना लंबा और कठिन होता है। इस समस्या से निकलने के लिए हम दीर्घ विभाजन विधि् का प्रयोग करते हैं। इसके लिए हमें वर्गमूल में अंकों की संख्या को ज्ञात करने की आवश्यकता है। निम्नलिखित सारणी को देखिए : संख्या वर्ग 10 100 जो 3 अंकों की सबसे छोटी पूर्ण वर्ग संख्या है। 961 जो 3 अंकों की सबसे बड़ी पूर्ण वर्ग संख्या है। 32 1024 जो 4 अंकों की सबसे छोटी पूर्ण वर्ग संख्या है। 99 9801 जो 4 अंकों की सबसे बड़ी पूर्ण वर्ग संख्या है। अतः वर्गमूल में अंकों की संख्या के बारे में हम क्या कह सकते हैं यदि एक पूर्ण वर्ग संख्या 3 अंकों या 4 अंकों की हो? हम कह सकते हैं कि यदि एक पूर्ण वर्ग संख्या 3 अंकों की या 4 अंकों की है तब इसका वर्गमूल 2 अंकों का होगा। क्या आप हमें 5 या 6 अंकों वाली संख्या के वर्गमूल में अंकों की संख्या बता सकते हैं? सबसे छोटी 3 अंकों की पूर्ण वर्ग संख्या 100 है जो कि 10 का वर्ग है और 3 अंकों की सबसे बड़ी पूर्ण वर्ग संख्या 961 है जो कि 31 का वर्ग है। सबसे छोटी 4 अंकों की पूर्ण वर्ग संख्या 1024 है जो 32 का वर्ग है और सबसे बड़ी 4 अंकों की संख्या 9801 है जो 99 का वर्ग है। 2024.25 वर्ग और वर्गमूल 71', 'cls': 8},
    439: {'q': 'रू 12.25 का वर्गमूल ज्ञात कीजिए।', 'cls': 8},
    448: {'q': 'किसी समकोण त्रिभुज ABC मेंए ∠ठ त्र 90° (ं) यदि ।ठ त्र 6 बउए BC त्र 8 बउए है तो AC ज्ञात कीजिए। (इ) यदि AC त्र 13 बउए BC त्र 5 बउए है तो ।ठ ज्ञात कीजिए।', 'cls': 8},
    451: {'q': 'रू क्या 243 एक पूर्ण घन है?', 'cls': 8},
    452: {'q': 'रू क्या 392 एक पूर्ण घन है? यदि नहीं, तो ऐसी सबसे छोटी प्राकृत संख्या ज्ञात कीजिए जिससे 392 को गुणा करने पर गुणनपफल एक पूर्ण घन प्राप्त हो जाए।', 'cls': 8},
    453: {'q': 'रू क्या 53240 एक पूर्ण घन है? यदि नहीं, तो 53240 को किस सबसे छोटी प्राकृत संख्या से भाग दिया जाए कि भागपफल एक पूर्ण घन प्राप्त हो?', 'cls': 8},
    454: {'q': 'रू क्या 1188 एक पूर्ण घन है? यदि नहीं, तो किस सबसे छोटी प्राकृत संख्या से 1188 को भाग दिया जाए कि भागपफल एक पूर्ण घन प्राप्त हो जाए?', 'cls': 8},
    455: {'q': 'रू क्या 68600 एक पूर्ण घन है? यदि नहीं, तो वह सबसे छोटी प्राकृत संख्या ज्ञात कीजिए जिससे 68ए600 को गुणा करने पर एक पूर्ण घन प्राप्त हो जाए?', 'cls': 8},
    460: {'q': 'रू 8ए000 का घनमूल ज्ञात कीजिए।', 'cls': 8},
    489: {'q': 'रू 7ग2 – 4गल ़ 8ल2 ़ 5ग – 3ल में से 5ग2 – 4ल2 ़ 6ल – 3 को घटाइए।', 'cls': 8},
    491: {'q': '(ं) 12ं – 9ंइ ़ 5इ – 3 में से 4ं – 7ंइ ़ 3इ ़ 12 को घटाइए। (इ) 5गल – 2ल्र – 2्रग ़ 10गल्र में से 3गल ़ 5ल्र – 7्रग को घटाइए। (ब) 18 – 3च – 11ु ़ 5चु – 2चु2 ़ 5च2ु में से 4च2ु – 3चु ़ 5चु2 – 8च ़ 7ु – 10 को घटाइए।', 'cls': 8},
    529: {'q': 'रू एक भवन में 24 बेलनाकार खंभे हैं। प्रत्येक खंभे की त्रिज्या 28 सेमी और ऊँचाई 4 मी है। ृ 8 प्रति वर्ग मीटर की दर से सभी खंभे के वक्र पृष्ठीय क्षेत्रापफल पर पेंट कराने का व्यय ज्ञात कीजिए।', 'cls': 8},
    553: {'q': 'रू मान ज्ञात कीजिए : (i) 2–3 (ii) 2 3−', 'cls': 8},
    555: {'q': 'रू 4– 3 को घात और उसके आधर 2 के रूप में लिखिए।', 'cls': 8},
    564: {'q': 'उ का मान ज्ञात कीजिए जिसके लिए 5 उ झ् 5– 3 त्र 55', 'cls': 8},
    629: {'q': 'रू 44(ग4 – 5ग3 – 24ग2द्ध को 11 ग (ग – 8द्ध से भाग दीजिए।', 'cls': 8},
}

# Board 8 verdict "wrong": every one of these serves was
# hand-verified wrong; each must now decline to the
# honest fallback (none can serve correctly without a
# new solver schema — see the notes).
WRONG = [26, 49, 62, 63, 66, 67, 96, 109, 144, 153, 216,
         276, 280, 290, 292, 339, 342, 347, 353, 380, 395,
         401, 402, 403, 434, 448, 460, 489, 491, 529, 553,
         555, 629]

# Board 8 verdicts "genuine" (19) and "partial" (12):
# must keep serving, with the recorded answer token.
CONTROLS = {
    41: "17.75", 43: "17.1", 47: "5.2", 56: "4", 57: "47",
    65: "2058", 68: "2", 69: "2", 70: "2, 5", 71: "25",
    75: "14", 137: "70", 148: "right-angled", 219: "88",
    420: "80", 421: "90", 439: "7/2", 451: "243",
    564: "2",
    42: "6/5", 44: "3110", 73: "15", 74: "38, 43",
    139: "45°", 404: "1/13", 422: "2352", 427: "13",
    452: "392", 453: "53240", 454: "1188", 455: "68600",
}


def _served(result):
    return (isinstance(result, dict)
            and result.get("fallback_kind") is None
            and not result.get("fallback")
            and bool((result.get("answer") or "").strip()))


def _solve(idx):
    row = FED[idx]
    return _solve_friendly(row["q"], lang=None,
                           student_class=row["cls"])


@pytest.mark.parametrize("idx", WRONG)
def test_wave151_wrong_rows_now_decline(idx):
    r = _solve(idx)
    assert not _served(r), (
        f"idx {idx} still served: "
        f"{(r.get('answer') or '')[:120]}")


@pytest.mark.parametrize("idx", sorted(CONTROLS))
def test_wave151_control_rows_still_served(idx):
    r = _solve(idx)
    assert _served(r), f"control idx {idx} regressed to a decline"
    ans = r.get("answer") or ""
    assert CONTROLS[idx] in ans, (
        f"control idx {idx} answer changed: {ans[:120]}")


# ---------------------------------------------------------------------------
# Direct veto pins: fabricated results, one per rule,
# plus the near-miss serves that must NOT be vetoed.
# ---------------------------------------------------------------------------

def _res(answer, op="", steps=(), **kw):
    r = {"answer": answer, "op": op, "steps": list(steps)}
    r.update(kw)
    return r


def test_w26_furniture_value_in_harvest_vetoes():
    q = ("Find the mean of 10, 20, 30. 2024.25 Data "
         "Handling 51")
    r = _res("25", op="mean",
             steps=["Add all values: 10 + 20 + 30 + 51 = 111",
                    "Divide by the count (4): 111 ÷ 4 = 25"])
    assert _w151_veto(q, r)


def test_w26_clean_harvest_kept():
    q = "Find the mean of 10, 20, 30."
    r = _res("20", op="mean",
             steps=["Add all values: 10 + 20 + 30 = 60",
                    "Divide by the count (3): 60 ÷ 3 = 20"])
    assert not _w151_veto(q, r)


def test_w27_count_part_non_integer_vetoes():
    q = ("(i) Find the mean of 2, 4, 6. (ii) How many "
         "numbers are greater than the mean?")
    r = _res("(i) 4; (ii) 4", op="multipart_general",
             steps=["(i) mean steps", "(ii) mean steps"],
             multipart={"kind": "general"})
    assert not _w151_veto(q, r)  # integer count is fine
    r2 = _res("(i) 4; (ii) 4.5", op="multipart_general",
              steps=["(i) mean steps", "(ii) mean steps"],
              multipart={"kind": "general"})
    assert _w151_veto(q, r2)


def test_w27_why_part_bare_number_vetoes():
    q = ("(i) Find the mean of 2, 4, 6. (ii) Will you "
         "divide by 2 or 3? Why?")
    r = _res("(i) 4; (ii) 3.5", op="multipart_general",
             steps=["(i) mean steps", "(ii) mean steps"],
             multipart={"kind": "general"})
    assert _w151_veto(q, r)


def test_w28_rate_ask_mean_vetoes():
    q = ("A car covers 89.1 km in 2.2 hours. What is the "
         "average distance covered in 1 hour?")
    r = _res("30.7667", op="mean",
             steps=["Add all values: 2.2 + 89.1 + 1 = 92.3"])
    assert _w151_veto(q, r)


def test_w29_identity_under_multipart_vetoes():
    q = "Find: (i) 3 + 4 (ii) 5 + 6"
    r = _res("18", op="evaluate", steps=["Evaluate: 18 = 18"],
             expression="18")
    assert _w151_veto(q, r)


def test_w29_identity_clean_value_ask_kept():
    # Board 8 idx 564 shape: a genuine solve whose final
    # formatting is an identity line.
    q = "उ का मान ज्ञात कीजिए जिसके लिए 5^m ÷ 5^-3 = 5^5"
    r = _res("2", op="evaluate", steps=["Evaluate: 2 = 2"],
             expression="2")
    assert not _w151_veto(q, r)


def test_w29_identity_bare_expression_kept():
    # Wave 150 control idx 503: "5 + (3 × 7)" -> 26.
    q = "5 + (3 × 7)"
    r = _res("26", op="evaluate", steps=["Evaluate: 26 = 26"],
             expression="26")
    assert not _w151_veto(q, r)


def test_w30_word_equation_mashup_vetoes():
    q = ("(ं) पहला प्रश्न यहाँ है। (इ) दूसरा प्रश्न यहाँ "
         "है। (ब) तीसरा प्रश्न यहाँ है।")
    r = _res("120", op="hindi_word_equation",
             steps=["Let the smaller number be x"])
    assert _w151_veto(q, r)


def test_w31_verdict_without_verdict_ask_vetoes():
    q = ("In right triangle ABC, AB = 6 cm, BC = 8 cm. "
         "Find AC.")
    r = _res("No, it is not a right-angled triangle",
             op="pythagoras_check",
             steps=["Sides: 6, 8, 90"])
    assert _w151_veto(q, r)


def test_w31_verdict_with_verdict_ask_kept():
    q = "Determine whether 3 cm, 4 cm, 5 cm form a right-angled triangle?"
    r = _res("Yes, it is a right-angled triangle",
             op="pythagoras_check",
             steps=["Sides: 3, 4, 5"])
    assert not _w151_veto(q, r)


def test_w43_multi_triple_single_check_vetoes():
    q = ("Which of these can form a right triangle? "
         "(i) 2.5 cm, 6 cm, 6.5 cm (ii) 2 cm, 2 cm, 5 cm "
         "(iii) 1.5 cm, 2 cm, 2.5 cm")
    r = _res("Yes, it is a right-angled triangle",
             op="pythagoras_check",
             steps=["Sides: 2.5, 6, 6.5"])
    assert _w151_veto(q, r)


def test_w32_glyph_soup_vetoes():
    q = "5x - 3 = 3x - 5 हल कीजिए"
    r = _res("-9*ज*त*र*् + 5*ज - 5", op="simplify",
             steps=["Simplify: -9*ज*त*र*् + 5*ज - 5"],
             expression="-9*ज*त*र*् + 5*ज - 5")
    assert _w151_veto(q, r)


def test_w33_figure_only_no_data_vetoes():
    q = ("संलग्न आकृति HOPE एक समांतर चतुर्भुज है। x और "
         "y कोणों की माप ज्ञात कीजिए।")
    r = _res("360°", op="w103_angle_sum",
             steps=["कोणों का योग = 360°"])
    assert _w151_veto(q, r)


def test_w33_figure_with_data_kept():
    q = ("In the figure, a triangle has sides 3 cm and "
         "4 cm. Find the area.")
    r = _res("6", op="area", steps=["Area = 6"])
    assert not _w151_veto(q, r)


def test_w34_pie_total_contradiction_vetoes():
    q = "Sales: bread 320, cake 160, कुल : 720. Draw a pie chart."
    r = _res("वृत्त आलेख: bread = 320, कुल = 720",
             op="graph", type="plot",
             steps=["कुल = 880।"])
    assert _w151_veto(q, r)


def test_w35_wrong_event_probability_vetoes():
    q = ("एक थैले में 4 लाल गेंदें और 2 पीली गेंदें हैं। "
         "एक लाल गेंद प्राप्त करने की क्या प्रायिकता है?")
    r = _res("1/3 ≈ 0.3333", op="probability",
             steps=["Count the balls: 4 red, 2 yellow — total 6",
                    "Favourable (yellow) = 2",
                    "Probability = 1/3"])
    assert _w151_veto(q, r)


def test_w35_right_event_probability_kept():
    q = ("एक थैले में 4 लाल गेंदें और 2 पीली गेंदें हैं। "
         "एक लाल गेंद प्राप्त करने की क्या प्रायिकता है?")
    r = _res("2/3 ≈ 0.6667", op="probability",
             steps=["Count the balls: 4 red, 2 yellow — total 6",
                    "Favourable (red) = 4",
                    "Probability = 2/3"])
    assert not _w151_veto(q, r)


def test_w36_list_outcomes_bare_number_vetoes():
    q = "इन प्रयोगों में आप जो परिणाम देख सकते हैं उन्हें लिखिए : दो सिक्कों को एक साथ उछालना"
    r = _res("4", op="w94_outcome_count",
             steps=["2^2 = 4"])
    assert _w151_veto(q, r)


def test_w36_how_many_outcomes_kept():
    q = "दो सिक्कों को उछालने पर कितने परिणाम संभव हैं?"
    r = _res("4", op="w94_outcome_count", steps=["2^2 = 4"])
    assert not _w151_veto(q, r)


def test_w37_zero_carve_vetoes():
    # Board 8 idx 553 shape: a multi-part value ask whose
    # superscript glyphs collapsed ("2–3" for 2^-3); the
    # evaluator carved a bare negative out of one part.
    q = ("निम्नलिखित का मान ज्ञात कीजिए : (i) 2–3 "
         "(ii) 4–1 (iii) 3–2")
    r = _res("-1", op="evaluate",
             steps=["Write the expression: - 1", "0 - 1 = -1"],
             expression="-1")
    assert _w151_veto(q, r)


def test_w37_genuine_zero_minus_kept():
    q = "Find the value of 0 - 5."
    r = _res("-5", op="evaluate", steps=["0 - 5 = -5"],
             expression="-5")
    assert not _w151_veto(q, r)


def test_w37_genuine_negative_results_kept():
    # The evaluate layer presents EVERY bare negative
    # result with a "0 - k = -k" step; single arithmetic
    # asks and value-assignment asks are genuine serves
    # (Wave 55 integer examples; Band B polynomial value).
    for q, k in (("What is -12 + 7?", "5"),
                 ("What is -48 / 6?", "8"),
                 ("What is (-6) * 4?", "24")):
        r = _res("-" + k, op="evaluate",
                 steps=[f"Write the expression: - {k}",
                        f"0 - {k} = -{k}"],
                 expression="-" + k)
        assert not _w151_veto(q, r), q
    q = "Find the value of the polynomial 5x - 4x^2 + 3 at x = 2"
    r = _res("-3", op="evaluate",
             steps=["Write the expression: - 3", "0 - 3 = -3"],
             expression="-3")
    assert not _w151_veto(q, r)


def test_w38_hindi_cost_at_rate_vetoes():
    q = ("एक भवन में 24 बेलनाकार खंभे हैं। प्रत्येक खंभे "
         "की त्रिज्या 28 सेमी और ऊँचाई 4 मी है। ₹8 प्रति "
         "वर्ग मीटर की दर से सभी खंभों पर पेंट कराने का "
         "व्यय ज्ञात कीजिए।")
    r = _res("704", op="hindi_mensuration",
             steps=["Curved surface area = 2πrh", "= 704"])
    assert _w151_veto(q, r)


def test_w39_root_mismatch_vetoes():
    q = "8000 का घनमूल ज्ञात कीजिए।"
    r = _res("0", op="evaluate", steps=["Evaluate: 0 = 0"],
             expression="0")
    assert _w151_veto(q, r)


def test_w39_root_verified_kept():
    q = "6400 का वर्गमूल ज्ञात कीजिए?"
    r = _res("80", op="evaluate", steps=["Evaluate: 80 = 80"],
             expression="80")
    assert not _w151_veto(q, r)
    q2 = "बार-बार घटाने की विधि से 100 और 169 का वर्गमूल ज्ञात कीजिए।"
    r2 = _res("13", op="evaluate", steps=["Evaluate: 13 = 13"],
              expression="13")
    assert not _w151_veto(q2, r2)  # 13^2 = 169, partial but correct


def test_w40_compare_bare_number_vetoes():
    q = "निम्नलिखित संख्याओं की तुलना कीजिए : (i) 2.7 × 10^12 व 1.5 × 10^8"
    r = _res("13662/5", op="evaluate",
             steps=["Evaluate: 2732.4 = 13662/5"], expression="2732.4")
    assert _w151_veto(q, r)


def test_w41_form_ask_bare_number_vetoes():
    q = "8 × 8 × 8 × 8 को, आधार 2 लेते हुए, घातांकीय रूप में लिखिए।"
    r = _res("4096", op="evaluate", steps=["Evaluate: 4096 = 4096"],
             expression="4096")
    assert _w151_veto(q, r)


def test_w42_expression_subtraction_bare_number_vetoes():
    q = ("7ग2 – 4गल + 8ल2 + 5ग – 3ल में से 5ग2 – 4ल2 + "
         "6ल – 3 को घटाइए।")
    r = _res("-2", op="evaluate",
             steps=["Write the expression: - 2", "0 - 2 = -2"],
             expression="-2")
    assert _w151_veto(q, r)


def test_w42_plain_multiply_kept():
    # Wave 150 control idx 4211 shape: plain arithmetic
    # with OCR noise must not read as algebra.
    q = ("Multiply 95 and 99, L.H.S. R.HS. 95 -5 99 N -] "
         "94 / 00 1S D4. 05 Ans, - 9405")
    r = _res("9405", op="multiply",
             steps=["Multiply: 95 × 99 = 9405"])
    assert not _w151_veto(q, r)


def test_w44_smallest_square_verdict_vetoes():
    q = ("वह सबसे छोटी वर्ग संख्या ज्ञात कीजिए जो प्रत्येक "
         "8, 15 और 20 से विभाजित हो जाए।")
    r = _res("नहीं — 8 पूर्ण वर्ग नहीं है",
             op="perfect_square_check", steps=[])
    assert _w151_veto(q, r)


def test_w44_verdict_ask_first_part_kept():
    # Board 8 idx 422 shape: the verdict IS the asked
    # first part; the smallest-multiplier part is unserved.
    q = ("क्या 2352 एक पूर्ण वर्ग संख्या है? यदि नहीं तो "
         "2352 का सबसे छोटा गुणज प्राप्त कीजिए जो कि पूर्ण "
         "वर्ग संख्या हो।")
    r = _res("नहीं — 2352 पूर्ण वर्ग नहीं है",
             op="perfect_square_check", steps=[])
    assert not _w151_veto(q, r)
