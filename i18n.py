"""Multi-language UI strings for Ganitra (Wave 4).

Six languages: English (en, the fallback), Hindi (hi), Bengali (bn),
Marathi (mr), Tamil (ta), Telugu (te).

Scope, stated honestly: the UI chrome (navigation, headings, buttons,
labels, flash messages, JS status notes), the voice-input language, and
ONE summary "explanation" line on the answer page are localised. The
step-by-step working produced by the solver stays in English — full
step translation is future work (see README).

Every language dict is merged over the English one in get_strings(),
so a missing string always falls back to English instead of breaking.
"""

SUPPORTED_LANGS = ("en", "hi", "bn", "mr", "ta", "te")

LANG_NAMES = {
    "en": "English",
    "hi": "हिन्दी",
    "bn": "বাংলা",
    "mr": "मराठी",
    "ta": "தமிழ்",
    "te": "తెలుగు",
}

# SpeechRecognition language per UI language.
SPEECH_LANGS = {
    "en": "en-IN",
    "hi": "hi-IN",
    "bn": "bn-IN",
    "mr": "mr-IN",
    "ta": "ta-IN",
    "te": "te-IN",
}

_EN = {
    # base / chrome
    "tagline": "Maths, solved step by step",
    "lang_label": "Language:",
    "nav_solve": "Solve",
    "nav_practice": "Practice",
    "nav_history": "History",
    "footer_powered": "Powered by Flask + SymPy",
    # index / hero
    "hero_tag": "Ask any maths question — get a clear, step-by-step "
                "solution in seconds. Plain English or Hinglish, "
                "Class 10 to engineering level.",
    "enter_question": "Enter a math question:",
    "question_placeholder": "e.g., Solve 2x+3=7, integrate x^2 from 0 "
                            "to 1, sin 30 ka maan, plot x^2 - 3x + 2",
    "voice_btn": "🎤 Speak your question",
    "photo_btn": "📷 Photo question",
    "solve_btn": "Solve it →",
    "topics_heading": "Everything it can solve",
    "topics_sub": "17 topic areas — every answer comes with full working.",
    "how_heading": "How it works",
    "how_sub": "Three steps, no sign-up.",
    "how1_title": "Type, speak or photograph",
    "how1_text": "Type it, speak it 🎤, or send a photo of your "
                 "notebook 📷. Plain English or Hinglish works too.",
    "how2_title": "See every step",
    "how2_text": "The solver shows the full working, not just the "
                 "final answer.",
    "how3_title": "Save & practise",
    "how3_text": "Download the solution as a .txt file, revisit it in "
                 "History, or take a timed quiz in Practice.",
    # topic card titles
    "t_arithmetic": "Arithmetic",
    "t_algebra": "Algebra",
    "t_exponents_logs": "Exponents & Logs",
    "t_trigonometry": "Trigonometry",
    "t_calculus": "Calculus",
    "t_transforms": "Transforms & Series",
    "t_linear_algebra": "Linear Algebra",
    "t_geometry": "Geometry",
    "t_statistics": "Statistics & Probability",
    "t_distributions": "Distributions",
    "t_number_theory": "Number Theory",
    "t_sequences": "Sequences & Series",
    "t_complex": "Complex Numbers",
    "t_sets": "Sets",
    "t_units": "Unit Conversion",
    "t_word_problems": "Word Problems",
    "t_graphs": "Graphs",
    # answer page
    "question_heading": "Question",
    "answer_heading": "Answer",
    "steps_heading": "Step-by-step solution",
    "understood_as": "Understood as:",
    "full_result": "Full result (JSON)",
    "download_link": "⬇ Download solution (.txt)",
    "ask_another": "← Ask another",
    "explanation_heading": "💡 Explanation",
    "photo_heading": "📷 Photo se padha gaya sawaal (question read "
                     "from your photo)",
    "photo_text": "This is the question read from your photo — if "
                  "anything looks wrong, correct it and press Solve. "
                  "(OCR sometimes misreads a number or sign, so please "
                  "check the text first.)",
    "photo_fix_btn": "Fix & Solve →",
    "photo_below": "Below is the answer to the question as read:",
    # practice / quiz
    "quiz_heading": "Timed quiz 🎯",
    "quiz_intro": "Pick a topic and difficulty — you get {count} "
                  "questions and {seconds} seconds on the clock. "
                  "Answers are checked when you submit.",
    "topic_label": "Topic",
    "difficulty_label": "Difficulty",
    "start_quiz": "Start quiz",
    "restart_quiz": "Restart quiz",
    "time_left": "⏱ Time left:",
    "your_answer_ph": "Your answer",
    "submit_answers": "Submit answers",
    "practice_heading": "Practice questions",
    "practice_intro": "Try each question yourself first, then reveal "
                      "the answer. Reload the page for a fresh set.",
    "show_answer": "Show answer",
    "new_set": "↻ New set",
    "classic_prefer": "Prefer untimed practice?",
    "classic_open": "Open the classic practice set",
    "classic_note": "(answers hidden until you reveal them).",
    "back_to_solver": "← Back to solver",
    "result_heading": "Quiz result 🏆",
    "score_label": "Score:",
    "your_answer_label": "Your answer:",
    "correct_answer_label": "correct answer:",
    "blank": "(blank)",
    "finished_in": "finished in",
    "new_quiz": "↻ New quiz",
    "quiz_topic_arithmetic": "Arithmetic",
    "quiz_topic_algebra": "Algebra",
    "quiz_topic_trig": "Trigonometry",
    "quiz_topic_stats": "Statistics",
    "diff_easy": "Easy",
    "diff_medium": "Medium",
    "diff_hard": "Hard",
    # history
    "history_heading": "History 🕘",
    "history_intro": "Questions you solved in this session, newest "
                     "first. Click one to see its full solution again.",
    "clear_history": "Clear history",
    "history_empty": "Nothing here yet — solve a question and it will "
                     "appear in this list.",
    # flash messages
    "flash_no_question": "Please enter a question.",
    "flash_photo_empty": "Could not read any question from the photo — "
                         "please use a clearer photo, or type the "
                         "question.",
    "flash_download_first": "Solve a question first, then download "
                            "its solution.",
    "flash_start_quiz": "Start a quiz first.",
    # JS status notes (index page)
    "js_voice_listening_btn": "🎙️ Listening… speak now",
    "js_voice_heard": "Heard: “{text}” — now press Solve.",
    "js_voice_no_api": "Voice input is not available in this browser "
                       "— please try Chrome.",
    "js_voice_denied": "Microphone permission was not given — please "
                       "allow the mic in your browser settings.",
    "js_voice_failed": "Could not understand the voice, please try "
                       "again.",
    "js_voice_speak": "Speak now, I am listening…",
    "js_photo_unavailable": "The photo feature has not loaded yet — "
                            "please refresh the page and try again.",
    "js_photo_reading": "Reading the photo… ⏳ (printed questions read "
                        "most clearly)",
    "js_photo_not_found": "No question found in the photo — send a "
                          "clear, straight photo again, or type the "
                          "question.",
    "js_photo_sending": "Question found — sending…",
    "js_photo_error": "There was a problem reading the photo — please "
                      "try again or type the question.",
}

STRINGS = {"en": _EN}

_HI = {
    "tagline": "गणित, चरण-दर-चरण हल किया गया",
    "lang_label": "भाषा:",
    "nav_solve": "हल करें",
    "nav_practice": "अभ्यास",
    "nav_history": "इतिहास",
    "footer_powered": "Flask + SymPy द्वारा संचालित",
    "hero_tag": "कोई भी गणित का प्रश्न पूछिए — कुछ ही सेकंड में स्पष्ट, "
                "चरण-दर-चरण हल पाइए। कक्षा 10 से इंजीनियरिंग स्तर तक।",
    "enter_question": "गणित का प्रश्न लिखिए:",
    "question_placeholder": "जैसे, 2x+3=7 हल कीजिए, 0 से 1 तक x^2 का "
                            "समाकलन, sin 30 का मान, x^2 - 3x + 2 का ग्राफ़",
    "voice_btn": "🎤 बोलकर प्रश्न पूछिए",
    "photo_btn": "📷 फ़ोटो से प्रश्न",
    "solve_btn": "हल कीजिए →",
    "topics_heading": "यह सब कुछ हल कर सकता है",
    "topics_sub": "17 विषय क्षेत्र — हर उत्तर के साथ पूरी विधि।",
    "how_heading": "यह कैसे काम करता है",
    "how_sub": "तीन चरण, कोई साइन-अप नहीं।",
    "how1_title": "लिखिए, बोलिए या फ़ोटो भेजिए",
    "how1_text": "प्रश्न लिखिए, बोलकर पूछिए 🎤, या नोटबुक की फ़ोटो भेज "
                 "दीजिए 📷।",
    "how2_title": "हर चरण देखिए",
    "how2_text": "सॉल्वर केवल अंतिम उत्तर नहीं, पूरी विधि दिखाता है।",
    "how3_title": "सहेजिए और अभ्यास कीजिए",
    "how3_text": "हल को .txt फ़ाइल में डाउनलोड कीजिए, इतिहास में फिर "
                 "देखिए, या अभ्यास में समयबद्ध क्विज़ दीजिए।",
    "t_arithmetic": "अंकगणित",
    "t_algebra": "बीजगणित",
    "t_exponents_logs": "घातांक और लघुगणक",
    "t_trigonometry": "त्रिकोणमिति",
    "t_calculus": "कलन (कैलकुलस)",
    "t_transforms": "रूपांतरण और श्रेणियाँ",
    "t_linear_algebra": "रैखिक बीजगणित",
    "t_geometry": "ज्यामिति",
    "t_statistics": "सांख्यिकी और प्रायिकता",
    "t_distributions": "प्रायिकता बंटन",
    "t_number_theory": "संख्या सिद्धांत",
    "t_sequences": "अनुक्रम और श्रेणियाँ",
    "t_complex": "सम्मिश्र संख्याएँ",
    "t_sets": "समुच्चय",
    "t_units": "इकाई रूपांतरण",
    "t_word_problems": "शाब्दिक प्रश्न",
    "t_graphs": "ग्राफ़",
    "question_heading": "प्रश्न",
    "answer_heading": "उत्तर",
    "steps_heading": "चरण-दर-चरण हल",
    "understood_as": "इस प्रकार समझा गया:",
    "full_result": "पूरा परिणाम (JSON)",
    "download_link": "⬇ हल डाउनलोड कीजिए (.txt)",
    "ask_another": "← दूसरा प्रश्न पूछिए",
    "explanation_heading": "💡 व्याख्या",
    "photo_heading": "📷 आपकी फ़ोटो से पढ़ा गया प्रश्न",
    "photo_text": "यह प्रश्न आपकी फ़ोटो से पढ़ा गया है — यदि कुछ ग़लत "
                  "लगे तो उसे ठीक करके 'हल कीजिए' दबाइए। (OCR कभी-कभी "
                  "अंक या चिह्न ग़लत पढ़ देता है, इसलिए पहले पाठ जाँच "
                  "लीजिए।)",
    "photo_fix_btn": "ठीक करके हल कीजिए →",
    "photo_below": "नीचे पढ़े गए प्रश्न का उत्तर दिया गया है:",
    "quiz_heading": "समयबद्ध क्विज़ 🎯",
    "quiz_intro": "विषय और कठिनाई चुनिए — आपको {count} प्रश्न और "
                  "{seconds} सेकंड मिलेंगे। उत्तर जमा करने पर जाँचे "
                  "जाएँगे।",
    "topic_label": "विषय",
    "difficulty_label": "कठिनाई",
    "start_quiz": "क्विज़ शुरू कीजिए",
    "restart_quiz": "क्विज़ फिर शुरू कीजिए",
    "time_left": "⏱ शेष समय:",
    "your_answer_ph": "आपका उत्तर",
    "submit_answers": "उत्तर जमा कीजिए",
    "practice_heading": "अभ्यास प्रश्न",
    "practice_intro": "पहले हर प्रश्न स्वयं हल करने का प्रयास कीजिए, "
                      "फिर उत्तर देखिए। नए समूह के लिए पृष्ठ फिर से "
                      "लोड कीजिए।",
    "show_answer": "उत्तर देखिए",
    "new_set": "↻ नया समूह",
    "classic_prefer": "बिना समय-सीमा के अभ्यास चाहिए?",
    "classic_open": "क्लासिक अभ्यास समूह खोलिए",
    "classic_note": "(उत्तर तब तक छिपे रहेंगे जब तक आप उन्हें न खोलें)।",
    "back_to_solver": "← सॉल्वर पर वापस",
    "result_heading": "क्विज़ परिणाम 🏆",
    "score_label": "अंक:",
    "your_answer_label": "आपका उत्तर:",
    "correct_answer_label": "सही उत्तर:",
    "blank": "(खाली)",
    "finished_in": "समय लगा",
    "new_quiz": "↻ नया क्विज़",
    "quiz_topic_arithmetic": "अंकगणित",
    "quiz_topic_algebra": "बीजगणित",
    "quiz_topic_trig": "त्रिकोणमिति",
    "quiz_topic_stats": "सांख्यिकी",
    "diff_easy": "आसान",
    "diff_medium": "मध्यम",
    "diff_hard": "कठिन",
    "history_heading": "इतिहास 🕘",
    "history_intro": "इस सत्र में आपके द्वारा हल किए गए प्रश्न, नवीनतम "
                     "पहले। पूरा हल फिर देखने के लिए किसी एक पर क्लिक "
                     "कीजिए।",
    "clear_history": "इतिहास साफ़ कीजिए",
    "history_empty": "अभी यहाँ कुछ नहीं है — एक प्रश्न हल कीजिए, वह "
                     "इस सूची में दिखाई देगा।",
    "flash_no_question": "कृपया कोई प्रश्न लिखिए।",
    "flash_photo_empty": "फ़ोटो से कोई प्रश्न नहीं पढ़ा जा सका — कृपया "
                         "साफ़ फ़ोटो का उपयोग कीजिए, या प्रश्न लिख "
                         "दीजिए।",
    "flash_download_first": "पहले कोई प्रश्न हल कीजिए, फिर उसका हल "
                            "डाउनलोड कीजिए।",
    "flash_start_quiz": "पहले क्विज़ शुरू कीजिए।",
    "js_voice_listening_btn": "🎙️ सुन रहा हूँ… बोलिए",
    "js_voice_heard": "सुन लिया: “{text}” — अब 'हल कीजिए' दबाइए।",
    "js_voice_no_api": "इस ब्राउज़र में आवाज़ से प्रश्न पूछना उपलब्ध "
                       "नहीं है — Chrome में प्रयास कीजिए।",
    "js_voice_denied": "माइक की अनुमति नहीं मिली — ब्राउज़र सेटिंग में "
                       "माइक की अनुमति दीजिए।",
    "js_voice_failed": "आवाज़ समझ नहीं आई, फिर से प्रयास कीजिए।",
    "js_voice_speak": "बोलिए, मैं सुन रहा हूँ…",
    "js_photo_unavailable": "फ़ोटो वाला फ़ीचर अभी लोड नहीं हुआ — पृष्ठ "
                            "फिर से लोड करके प्रयास कीजिए।",
    "js_photo_reading": "फ़ोटो पढ़ा जा रहा है… ⏳ (छपा हुआ प्रश्न सबसे "
                        "साफ़ पढ़ा जाता है)",
    "js_photo_not_found": "फ़ोटो में प्रश्न नहीं मिल पाया — साफ़, सीधी "
                          "फ़ोटो फिर भेजिए, या प्रश्न लिख दीजिए।",
    "js_photo_sending": "प्रश्न मिल गया — भेजा जा रहा है…",
    "js_photo_error": "फ़ोटो पढ़ने में समस्या आई — फिर प्रयास कीजिए या "
                      "प्रश्न लिख दीजिए।",
}

STRINGS["hi"] = _HI

_BN = {
    "tagline": "গণিত, ধাপে ধাপে সমাধান",
    "lang_label": "ভাষা:",
    "nav_solve": "সমাধান করুন",
    "nav_practice": "অনুশীলন",
    "nav_history": "ইতিহাস",
    "footer_powered": "Flask + SymPy দ্বারা চালিত",
    "hero_tag": "যেকোনো গণিতের প্রশ্ন জিজ্ঞাসা করুন — কয়েক সেকেন্ডে "
                "স্পষ্ট, ধাপে ধাপে সমাধান পান। দশম শ্রেণি থেকে "
                "ইঞ্জিনিয়ারিং স্তর পর্যন্ত।",
    "enter_question": "গণিতের প্রশ্ন লিখুন:",
    "question_placeholder": "যেমন, 2x+3=7 সমাধান করুন, 0 থেকে 1 "
                            "পর্যন্ত x^2-এর সমাকলন, sin 30-এর মান, "
                            "x^2 - 3x + 2-এর লেখচিত্র",
    "voice_btn": "🎤 বলে প্রশ্ন করুন",
    "photo_btn": "📷 ছবি থেকে প্রশ্ন",
    "solve_btn": "সমাধান করুন →",
    "topics_heading": "এটি যা যা সমাধান করতে পারে",
    "topics_sub": "17টি বিষয় ক্ষেত্র — প্রতিটি উত্তরের সঙ্গে সম্পূর্ণ "
                  "পদ্ধতি।",
    "how_heading": "এটি কীভাবে কাজ করে",
    "how_sub": "তিনটি ধাপ, সাইন-আপ লাগবে না।",
    "how1_title": "লিখুন, বলুন বা ছবি তুলুন",
    "how1_text": "প্রশ্নটি লিখুন, বলে জিজ্ঞাসা করুন 🎤, বা খাতার ছবি "
                 "পাঠান 📷।",
    "how2_title": "প্রতিটি ধাপ দেখুন",
    "how2_text": "সলভার শুধু চূড়ান্ত উত্তর নয়, সম্পূর্ণ পদ্ধতি দেখায়।",
    "how3_title": "সংরক্ষণ ও অনুশীলন",
    "how3_text": "সমাধানটি .txt ফাইলে ডাউনলোড করুন, ইতিহাসে আবার "
                 "দেখুন, বা অনুশীলনে সময়ভিত্তিক কুইজ দিন।",
    "t_arithmetic": "পাটিগণিত",
    "t_algebra": "বীজগণিত",
    "t_exponents_logs": "সূচক ও লগারিদম",
    "t_trigonometry": "ত্রিকোণমিতি",
    "t_calculus": "ক্যালকুলাস",
    "t_transforms": "রূপান্তর ও ধারা",
    "t_linear_algebra": "রৈখিক বীজগণিত",
    "t_geometry": "জ্যামিতি",
    "t_statistics": "পরিসংখ্যান ও সম্ভাবনা",
    "t_distributions": "সম্ভাবনা বণ্টন",
    "t_number_theory": "সংখ্যা তত্ত্ব",
    "t_sequences": "অনুক্রম ও ধারা",
    "t_complex": "জটিল সংখ্যা",
    "t_sets": "সেট",
    "t_units": "একক রূপান্তর",
    "t_word_problems": "শব্দের অঙ্ক",
    "t_graphs": "লেখচিত্র",
    "question_heading": "প্রশ্ন",
    "answer_heading": "উত্তর",
    "steps_heading": "ধাপে ধাপে সমাধান",
    "understood_as": "এভাবে বোঝা হয়েছে:",
    "full_result": "সম্পূর্ণ ফলাফল (JSON)",
    "download_link": "⬇ সমাধান ডাউনলোড করুন (.txt)",
    "ask_another": "← আরেকটি প্রশ্ন করুন",
    "explanation_heading": "💡 ব্যাখ্যা",
    "photo_heading": "📷 আপনার ছবি থেকে পড়া প্রশ্ন",
    "photo_text": "এই প্রশ্নটি আপনার ছবি থেকে পড়া হয়েছে — কিছু ভুল "
                  "মনে হলে ঠিক করে 'সমাধান করুন' চাপুন। (OCR মাঝে "
                  "মাঝে সংখ্যা বা চিহ্ন ভুল পড়ে, তাই আগে লেখাটি "
                  "যাচাই করুন।)",
    "photo_fix_btn": "ঠিক করে সমাধান করুন →",
    "photo_below": "নিচে পড়া প্রশ্নটির উত্তর দেওয়া হলো:",
    "quiz_heading": "সময়ভিত্তিক কুইজ 🎯",
    "quiz_intro": "বিষয় ও কঠিনতা বেছে নিন — আপনি পাবেন {count}টি "
                  "প্রশ্ন এবং {seconds} সেকেন্ড। জমা দিলে উত্তর "
                  "যাচাই করা হবে।",
    "topic_label": "বিষয়",
    "difficulty_label": "কঠিনতা",
    "start_quiz": "কুইজ শুরু করুন",
    "restart_quiz": "কুইজ আবার শুরু করুন",
    "time_left": "⏱ বাকি সময়:",
    "your_answer_ph": "আপনার উত্তর",
    "submit_answers": "উত্তর জমা দিন",
    "practice_heading": "অনুশীলনের প্রশ্ন",
    "practice_intro": "প্রথমে প্রতিটি প্রশ্ন নিজে সমাধান করার চেষ্টা "
                      "করুন, তারপর উত্তর দেখুন। নতুন সেটের জন্য "
                      "পৃষ্ঠাটি আবার লোড করুন।",
    "show_answer": "উত্তর দেখুন",
    "new_set": "↻ নতুন সেট",
    "classic_prefer": "সময়সীমা ছাড়া অনুশীলন চান?",
    "classic_open": "ক্লাসিক অনুশীলন সেট খুলুন",
    "classic_note": "(আপনি না খুললে উত্তর লুকানো থাকবে)।",
    "back_to_solver": "← সলভারে ফিরুন",
    "result_heading": "কুইজের ফলাফল 🏆",
    "score_label": "স্কোর:",
    "your_answer_label": "আপনার উত্তর:",
    "correct_answer_label": "সঠিক উত্তর:",
    "blank": "(খালি)",
    "finished_in": "সময় লেগেছে",
    "new_quiz": "↻ নতুন কুইজ",
    "quiz_topic_arithmetic": "পাটিগণিত",
    "quiz_topic_algebra": "বীজগণিত",
    "quiz_topic_trig": "ত্রিকোণমিতি",
    "quiz_topic_stats": "পরিসংখ্যান",
    "diff_easy": "সহজ",
    "diff_medium": "মাঝারি",
    "diff_hard": "কঠিন",
    "history_heading": "ইতিহাস 🕘",
    "history_intro": "এই সেশনে আপনার সমাধান করা প্রশ্নসমূহ, নতুনটি "
                     "আগে। পুরো সমাধান আবার দেখতে যেকোনো একটিতে "
                     "ক্লিক করুন।",
    "clear_history": "ইতিহাস মুছুন",
    "history_empty": "এখানে এখনো কিছু নেই — একটি প্রশ্ন সমাধান করুন, "
                     "তা এই তালিকায় দেখা যাবে।",
    "flash_no_question": "অনুগ্রহ করে একটি প্রশ্ন লিখুন।",
    "flash_photo_empty": "ছবি থেকে কোনো প্রশ্ন পড়া যায়নি — অনুগ্রহ "
                         "করে পরিষ্কার ছবি ব্যবহার করুন, বা প্রশ্নটি "
                         "লিখে দিন।",
    "flash_download_first": "প্রথমে একটি প্রশ্ন সমাধান করুন, তারপর "
                            "তার সমাধান ডাউনলোড করুন।",
    "flash_start_quiz": "প্রথমে কুইজ শুরু করুন।",
    "js_voice_listening_btn": "🎙️ শুনছি… বলুন",
    "js_voice_heard": "শুনলাম: “{text}” — এখন 'সমাধান করুন' চাপুন।",
    "js_voice_no_api": "এই ব্রাউজারে কণ্ঠ ইনপুট উপলভ্য নয় — Chrome-এ "
                       "চেষ্টা করুন।",
    "js_voice_denied": "মাইকের অনুমতি পাওয়া যায়নি — ব্রাউজার "
                       "সেটিংসে মাইক অনুমোদন করুন।",
    "js_voice_failed": "কণ্ঠ বোঝা যায়নি, আবার চেষ্টা করুন।",
    "js_voice_speak": "বলুন, শুনছি…",
    "js_photo_unavailable": "ছবির ফিচারটি এখনো লোড হয়নি — পৃষ্ঠাটি "
                            "আবার লোড করে চেষ্টা করুন।",
    "js_photo_reading": "ছবি পড়া হচ্ছে… ⏳ (ছাপানো প্রশ্ন সবচেয়ে "
                        "স্পষ্ট পড়া যায়)",
    "js_photo_not_found": "ছবিতে প্রশ্ন পাওয়া যায়নি — পরিষ্কার, সোজা "
                          "ছবি আবার পাঠান, বা প্রশ্নটি লিখে দিন।",
    "js_photo_sending": "প্রশ্ন পাওয়া গেছে — পাঠানো হচ্ছে…",
    "js_photo_error": "ছবি পড়তে সমস্যা হয়েছে — আবার চেষ্টা করুন বা "
                      "প্রশ্নটি লিখে দিন।",
}

STRINGS["bn"] = _BN

_MR = {
    "tagline": "गणित, टप्प्याटप्पाने सोडवलेले",
    "lang_label": "भाषा:",
    "nav_solve": "सोडवा",
    "nav_practice": "सराव",
    "nav_history": "इतिहास",
    "footer_powered": "Flask + SymPy द्वारे संचालित",
    "hero_tag": "कोणताही गणिताचा प्रश्न विचारा — काही सेकंदांत स्पष्ट, "
                "टप्प्याटप्पाने उत्तर मिळवा. इयत्ता 10वी ते अभियांत्रिकी "
                "पातळीपर्यंत.",
    "enter_question": "गणिताचा प्रश्न लिहा:",
    "question_placeholder": "उदा., 2x+3=7 सोडवा, 0 ते 1 पर्यंत x^2 चे "
                            "समाकलन, sin 30 चे मूल्य, x^2 - 3x + 2 चा "
                            "आलेख",
    "voice_btn": "🎤 बोलून प्रश्न विचारा",
    "photo_btn": "📷 फोटोवरून प्रश्न",
    "solve_btn": "सोडवा →",
    "topics_heading": "हे सगळं सोडवू शकतं",
    "topics_sub": "17 विषय क्षेत्रे — प्रत्येक उत्तरासोबत संपूर्ण पद्धत.",
    "how_heading": "हे कसं काम करतं",
    "how_sub": "तीन टप्पे, साइन-अप नको.",
    "how1_title": "लिहा, बोला किंवा फोटो काढा",
    "how1_text": "प्रश्न लिहा, बोलून विचारा 🎤, किंवा वहीचा फोटो "
                 "पाठवा 📷.",
    "how2_title": "प्रत्येक टप्पा पहा",
    "how2_text": "सॉल्व्हर फक्त अंतिम उत्तर नाही, संपूर्ण पद्धत दाखवतो.",
    "how3_title": "जतन करा आणि सराव करा",
    "how3_text": "उत्तर .txt फाईलमध्ये डाउनलोड करा, इतिहासात पुन्हा "
                 "पहा, किंवा सरावात वेळेवर आधारित क्विझ द्या.",
    "t_arithmetic": "अंकगणित",
    "t_algebra": "बीजगणित",
    "t_exponents_logs": "घातांक आणि लॉगॅरिदम",
    "t_trigonometry": "त्रिकोणमिती",
    "t_calculus": "कलनशास्त्र (कॅल्क्युलस)",
    "t_transforms": "रूपांतरणे आणि श्रेणी",
    "t_linear_algebra": "रेषीय बीजगणित",
    "t_geometry": "भूमिती",
    "t_statistics": "सांख्यिकी आणि संभाव्यता",
    "t_distributions": "संभाव्यता वितरण",
    "t_number_theory": "संख्या सिद्धांत",
    "t_sequences": "अनुक्रम आणि श्रेणी",
    "t_complex": "संमिश्र संख्या",
    "t_sets": "संच",
    "t_units": "एकक रूपांतरण",
    "t_word_problems": "शाब्दिक उदाहरणे",
    "t_graphs": "आलेख",
    "question_heading": "प्रश्न",
    "answer_heading": "उत्तर",
    "steps_heading": "टप्प्याटप्पाने उत्तर",
    "understood_as": "असे समजले:",
    "full_result": "संपूर्ण निकाल (JSON)",
    "download_link": "⬇ उत्तर डाउनलोड करा (.txt)",
    "ask_another": "← दुसरा प्रश्न विचारा",
    "explanation_heading": "💡 स्पष्टीकरण",
    "photo_heading": "📷 तुमच्या फोटोवरून वाचलेला प्रश्न",
    "photo_text": "हा प्रश्न तुमच्या फोटोवरून वाचला आहे — काही चूक "
                  "वाटल्यास दुरुस्त करून 'सोडवा' दाबा. (OCR कधी कधी "
                  "अंक किंवा चिन्ह चुकीचे वाचते, म्हणून आधी मजकूर "
                  "तपासा.)",
    "photo_fix_btn": "दुरुस्त करून सोडवा →",
    "photo_below": "खाली वाचलेल्या प्रश्नाचे उत्तर दिले आहे:",
    "quiz_heading": "वेळेवर आधारित क्विझ 🎯",
    "quiz_intro": "विषय आणि कठीणपणा निवडा — तुम्हाला {count} प्रश्न "
                  "आणि {seconds} सेकंद मिळतील. उत्तरं सबमिट केल्यावर "
                  "तपासली जातील.",
    "topic_label": "विषय",
    "difficulty_label": "कठीणपणा",
    "start_quiz": "क्विझ सुरू करा",
    "restart_quiz": "क्विझ पुन्हा सुरू करा",
    "time_left": "⏱ उरलेली वेळ:",
    "your_answer_ph": "तुमचे उत्तर",
    "submit_answers": "उत्तरे सबमिट करा",
    "practice_heading": "सराव प्रश्न",
    "practice_intro": "आधी प्रत्येक प्रश्न स्वतः सोडवण्याचा प्रयत्न "
                      "करा, मग उत्तर पहा. नवीन संचासाठी पृष्ठ पुन्हा "
                      "लोड करा.",
    "show_answer": "उत्तर पहा",
    "new_set": "↻ नवीन संच",
    "classic_prefer": "वेळेच्या मर्यादेशिवाय सराव हवा?",
    "classic_open": "क्लासिक सराव संच उघडा",
    "classic_note": "(तुम्ही उघडेपर्यंत उत्तरे लपलेली राहतील).",
    "back_to_solver": "← सॉल्व्हरकडे परत",
    "result_heading": "क्विझचा निकाल 🏆",
    "score_label": "गुण:",
    "your_answer_label": "तुमचे उत्तर:",
    "correct_answer_label": "बरोबर उत्तर:",
    "blank": "(रिक्त)",
    "finished_in": "लागलेला वेळ",
    "new_quiz": "↻ नवीन क्विझ",
    "quiz_topic_arithmetic": "अंकगणित",
    "quiz_topic_algebra": "बीजगणित",
    "quiz_topic_trig": "त्रिकोणमिती",
    "quiz_topic_stats": "सांख्यिकी",
    "diff_easy": "सोपे",
    "diff_medium": "मध्यम",
    "diff_hard": "कठीण",
    "history_heading": "इतिहास 🕘",
    "history_intro": "या सत्रात तुम्ही सोडवलेले प्रश्न, नवीन आधी. "
                     "संपूर्ण उत्तर पुन्हा पाहण्यासाठी कोणत्याही "
                     "एकावर क्लिक करा.",
    "clear_history": "इतिहास साफ करा",
    "history_empty": "इथे अजून काही नाही — एक प्रश्न सोडवा, तो या "
                     "यादीत दिसेल.",
    "flash_no_question": "कृपया एक प्रश्न लिहा.",
    "flash_photo_empty": "फोटोवरून कोणताही प्रश्न वाचता आला नाही — "
                         "कृपया स्पष्ट फोटो वापरा, किंवा प्रश्न लिहा.",
    "flash_download_first": "आधी एक प्रश्न सोडवा, मग त्याचे उत्तर "
                            "डाउनलोड करा.",
    "flash_start_quiz": "आधी क्विझ सुरू करा.",
    "js_voice_listening_btn": "🎙️ ऐकतोय… बोला",
    "js_voice_heard": "ऐकले: “{text}” — आता 'सोडवा' दाबा.",
    "js_voice_no_api": "या ब्राउझरमध्ये आवाजाने प्रश्न विचारणे उपलब्ध "
                       "नाही — Chrome मध्ये प्रयत्न करा.",
    "js_voice_denied": "माइकची परवानगी मिळाली नाही — ब्राउझर सेटिंगमध्ये "
                       "माइकला परवानगी द्या.",
    "js_voice_failed": "आवाज समजला नाही, पुन्हा प्रयत्न करा.",
    "js_voice_speak": "बोला, मी ऐकतोय…",
    "js_photo_unavailable": "फोटोचे वैशिष्ट्य अजून लोड झाले नाही — "
                            "पृष्ठ पुन्हा लोड करून प्रयत्न करा.",
    "js_photo_reading": "फोटो वाचत आहे… ⏳ (छापील प्रश्न सर्वात स्पष्ट "
                        "वाचला जातो)",
    "js_photo_not_found": "फोटोमध्ये प्रश्न सापडला नाही — स्पष्ट, सरळ "
                          "फोटो पुन्हा पाठवा, किंवा प्रश्न लिहा.",
    "js_photo_sending": "प्रश्न सापडला — पाठवत आहे…",
    "js_photo_error": "फोटो वाचण्यात अडचण आली — पुन्हा प्रयत्न करा किंवा "
                      "प्रश्न लिहा.",
}

STRINGS["mr"] = _MR

_TA = {
    "tagline": "கணிதம் — படிப்படியான தீர்வுகள்",
    "lang_label": "மொழி:",
    "nav_solve": "தீர்க்கவும்",
    "nav_practice": "பயிற்சி",
    "nav_history": "வரலாறு",
    "footer_powered": "Flask + SymPy ஆல் இயக்கப்படுகிறது",
    "hero_tag": "எந்தக் கணிதக் கேள்வியையும் கேளுங்கள் — சில "
                "விநாடிகளில் தெளிவான, படிப்படியான தீர்வைப் "
                "பெறுங்கள். 10ஆம் வகுப்பு முதல் பொறியியல் நிலை வரை.",
    "enter_question": "கணிதக் கேள்வியை உள்ளிடவும்:",
    "question_placeholder": "எ.கா., 2x+3=7 ஐத் தீர்க்கவும், 0 முதல் 1 "
                            "வரை x^2 இன் தொகையீடு, sin 30 இன் மதிப்பு, "
                            "x^2 - 3x + 2 இன் வரைபடம்",
    "voice_btn": "🎤 பேசிக் கேளுங்கள்",
    "photo_btn": "📷 புகைப்படத்திலிருந்து கேள்வி",
    "solve_btn": "தீர்க்கவும் →",
    "topics_heading": "இது தீர்க்கக்கூடிய அனைத்தும்",
    "topics_sub": "17 தலைப்புப் பகுதிகள் — ஒவ்வொரு பதிலுடனும் முழு "
                  "செயல்முறையும்.",
    "how_heading": "இது எப்படி செயல்படுகிறது",
    "how_sub": "மூன்று படிகள், பதிவு தேவையில்லை.",
    "how1_title": "தட்டச்சு செய்யவும், பேசவும் அல்லது புகைப்படம் "
                  "எடுக்கவும்",
    "how1_text": "கேள்வியைத் தட்டச்சு செய்யவும், பேசிக் கேட்கவும் 🎤, "
                 "அல்லது குறிப்பேட்டின் புகைப்படத்தை அனுப்பவும் 📷.",
    "how2_title": "ஒவ்வொரு படியையும் பாருங்கள்",
    "how2_text": "தீர்வாளர் இறுதிப் பதிலை மட்டுமல்ல, முழு "
                 "செயல்முறையையும் காட்டுகிறது.",
    "how3_title": "சேமித்துப் பயிற்சி செய்யவும்",
    "how3_text": "தீர்வை .txt கோப்பாகப் பதிவிறக்கவும், வரலாற்றில் "
                 "மீண்டும் பார்க்கவும், அல்லது பயிற்சியில் நேர "
                 "வினாடிவினாவை முயற்சிக்கவும்.",
    "t_arithmetic": "எண்கணிதம்",
    "t_algebra": "இயற்கணிதம்",
    "t_exponents_logs": "அடுக்குகள் மற்றும் மடக்கைகள்",
    "t_trigonometry": "முக்கோணவியல்",
    "t_calculus": "நுண்கணிதம் (கால்குலஸ்)",
    "t_transforms": "மாற்றங்கள் மற்றும் தொடர்கள்",
    "t_linear_algebra": "நேரியல் இயற்கணிதம்",
    "t_geometry": "வடிவியல்",
    "t_statistics": "புள்ளியியல் மற்றும் நிகழ்தகவு",
    "t_distributions": "நிகழ்தகவு பரவல்கள்",
    "t_number_theory": "எண் கோட்பாடு",
    "t_sequences": "தொடர்வரிசைகள் மற்றும் தொடர்கள்",
    "t_complex": "சிக்கல் எண்கள்",
    "t_sets": "கணங்கள்",
    "t_units": "அலகு மாற்றம்",
    "t_word_problems": "வார்த்தைக் கணக்குகள்",
    "t_graphs": "வரைபடங்கள்",
    "question_heading": "கேள்வி",
    "answer_heading": "பதில்",
    "steps_heading": "படிப்படியான தீர்வு",
    "understood_as": "இவ்வாறு புரிந்துகொள்ளப்பட்டது:",
    "full_result": "முழு முடிவு (JSON)",
    "download_link": "⬇ தீர்வைப் பதிவிறக்கவும் (.txt)",
    "ask_another": "← மற்றொரு கேள்வி கேளுங்கள்",
    "explanation_heading": "💡 விளக்கம்",
    "photo_heading": "📷 உங்கள் புகைப்படத்திலிருந்து படிக்கப்பட்ட "
                     "கேள்வி",
    "photo_text": "இந்தக் கேள்வி உங்கள் புகைப்படத்திலிருந்து "
                  "படிக்கப்பட்டது — ஏதேனும் தவறாகத் தோன்றினால் "
                  "சரிசெய்து 'தீர்க்கவும்' என்பதை அழுத்தவும். (OCR "
                  "சில நேரங்களில் எண் அல்லது குறியைத் தவறாகப் "
                  "படிக்கலாம், எனவே முதலில் உரையைச் சரிபார்க்கவும்.)",
    "photo_fix_btn": "சரிசெய்து தீர்க்கவும் →",
    "photo_below": "கீழே படிக்கப்பட்ட கேள்விக்கான பதில் உள்ளது:",
    "quiz_heading": "நேர வினாடிவினா 🎯",
    "quiz_intro": "தலைப்பு மற்றும் கடினத்தைத் தேர்ந்தெடுக்கவும் — "
                  "உங்களுக்கு {count} கேள்விகளும் {seconds} "
                  "விநாடிகளும் கிடைக்கும். சமர்ப்பிக்கும்போது "
                  "பதில்கள் சரிபார்க்கப்படும்.",
    "topic_label": "தலைப்பு",
    "difficulty_label": "கடினம்",
    "start_quiz": "வினாடிவினாவைத் தொடங்கவும்",
    "restart_quiz": "வினாடிவினாவை மீண்டும் தொடங்கவும்",
    "time_left": "⏱ மீதமுள்ள நேரம்:",
    "your_answer_ph": "உங்கள் பதில்",
    "submit_answers": "பதில்களைச் சமர்ப்பிக்கவும்",
    "practice_heading": "பயிற்சிக் கேள்விகள்",
    "practice_intro": "முதலில் ஒவ்வொரு கேள்வியையும் நீங்களே தீர்க்க "
                      "முயற்சிக்கவும், பிறகு பதிலைப் பார்க்கவும். "
                      "புதிய தொகுப்புக்குப் பக்கத்தை மீண்டும் "
                      "ஏற்றவும்.",
    "show_answer": "பதிலைக் காட்டவும்",
    "new_set": "↻ புதிய தொகுப்பு",
    "classic_prefer": "நேர வரம்பில்லாத பயிற்சி வேண்டுமா?",
    "classic_open": "கிளாசிக் பயிற்சித் தொகுப்பைத் திறக்கவும்",
    "classic_note": "(நீங்கள் வெளிப்படுத்தும் வரை பதில்கள் "
                    "மறைக்கப்பட்டிருக்கும்).",
    "back_to_solver": "← தீர்வாளருக்குத் திரும்பவும்",
    "result_heading": "வினாடிவினா முடிவு 🏆",
    "score_label": "மதிப்பெண்:",
    "your_answer_label": "உங்கள் பதில்:",
    "correct_answer_label": "சரியான பதில்:",
    "blank": "(காலி)",
    "finished_in": "எடுத்த நேரம்",
    "new_quiz": "↻ புதிய வினாடிவினா",
    "quiz_topic_arithmetic": "எண்கணிதம்",
    "quiz_topic_algebra": "இயற்கணிதம்",
    "quiz_topic_trig": "முக்கோணவியல்",
    "quiz_topic_stats": "புள்ளியியல்",
    "diff_easy": "எளிது",
    "diff_medium": "நடுத்தரம்",
    "diff_hard": "கடினம்",
    "history_heading": "வரலாறு 🕘",
    "history_intro": "இந்த அமர்வில் நீங்கள் தீர்த்த கேள்விகள், "
                     "புதியவை முதலில். முழுத் தீர்வை மீண்டும் "
                     "பார்க்க எதையாவது கிளிக் செய்யவும்.",
    "clear_history": "வரலாற்றை அழிக்கவும்",
    "history_empty": "இங்கே இன்னும் எதுவும் இல்லை — ஒரு கேள்வியைத் "
                     "தீர்க்கவும், அது இந்தப் பட்டியலில் தோன்றும்.",
    "flash_no_question": "தயவுசெய்து ஒரு கேள்வியை உள்ளிடவும்.",
    "flash_photo_empty": "புகைப்படத்திலிருந்து எந்தக் கேள்வியையும் "
                         "படிக்க முடியவில்லை — தெளிவான புகைப்படத்தைப் "
                         "பயன்படுத்தவும், அல்லது கேள்வியைத் தட்டச்சு "
                         "செய்யவும்.",
    "flash_download_first": "முதலில் ஒரு கேள்வியைத் தீர்க்கவும், "
                            "பிறகு அதன் தீர்வைப் பதிவிறக்கவும்.",
    "flash_start_quiz": "முதலில் வினாடிவினாவைத் தொடங்கவும்.",
    "js_voice_listening_btn": "🎙️ கேட்கிறேன்… பேசுங்கள்",
    "js_voice_heard": "கேட்டேன்: “{text}” — இப்போது 'தீர்க்கவும்' "
                      "என்பதை அழுத்தவும்.",
    "js_voice_no_api": "இந்த உலாவியில் குரல் உள்ளீடு கிடைக்கவில்லை — "
                       "Chrome இல் முயற்சிக்கவும்.",
    "js_voice_denied": "மைக் அனுமதி வழங்கப்படவில்லை — உலாவி "
                       "அமைப்புகளில் மைக்கை அனுமதிக்கவும்.",
    "js_voice_failed": "குரலைப் புரிந்துகொள்ள முடியவில்லை, மீண்டும் "
                       "முயற்சிக்கவும்.",
    "js_voice_speak": "பேசுங்கள், கேட்கிறேன்…",
    "js_photo_unavailable": "புகைப்பட அம்சம் இன்னும் ஏற்றப்படவில்லை — "
                            "பக்கத்தைப் புதுப்பித்து மீண்டும் "
                            "முயற்சிக்கவும்.",
    "js_photo_reading": "புகைப்படத்தைப் படிக்கிறேன்… ⏳ (அச்சிடப்பட்ட "
                        "கேள்விகள் மிகத் தெளிவாகப் படிக்கப்படும்)",
    "js_photo_not_found": "புகைப்படத்தில் கேள்வி கிடைக்கவில்லை — "
                          "தெளிவான, நேரான புகைப்படத்தை மீண்டும் "
                          "அனுப்பவும், அல்லது கேள்வியைத் தட்டச்சு "
                          "செய்யவும்.",
    "js_photo_sending": "கேள்வி கிடைத்தது — அனுப்புகிறேன்…",
    "js_photo_error": "புகைப்படத்தைப் படிப்பதில் சிக்கல் ஏற்பட்டது — "
                      "மீண்டும் முயற்சிக்கவும் அல்லது கேள்வியைத் "
                      "தட்டச்சு செய்யவும்.",
}

STRINGS["ta"] = _TA

_TE = {
    "tagline": "గణితం, దశలవారీగా పరిష్కరించబడింది",
    "lang_label": "భాష:",
    "nav_solve": "పరిష్కరించండి",
    "nav_practice": "అభ్యాసం",
    "nav_history": "చరిత్ర",
    "footer_powered": "Flask + SymPy ద్వారా నడుస్తుంది",
    "hero_tag": "ఏ గణిత ప్రశ్ననైనా అడగండి — కొన్ని సెకన్లలో స్పష్టమైన, "
                "దశలవారీ పరిష్కారం పొందండి. 10వ తరగతి నుండి "
                "ఇంజినీరింగ్ స్థాయి వరకు.",
    "enter_question": "గణిత ప్రశ్నను నమోదు చేయండి:",
    "question_placeholder": "ఉదా., 2x+3=7 ను పరిష్కరించండి, 0 నుండి 1 "
                            "వరకు x^2 యొక్క సమాకలనం, sin 30 విలువ, "
                            "x^2 - 3x + 2 గ్రాఫ్",
    "voice_btn": "🎤 మాట్లాడి అడగండి",
    "photo_btn": "📷 ఫోటో నుండి ప్రశ్న",
    "solve_btn": "పరిష్కరించండి →",
    "topics_heading": "ఇది పరిష్కరించగలిగినవన్నీ",
    "topics_sub": "17 అంశాల విభాగాలు — ప్రతి సమాధానంతో పూర్తి పద్ధతి.",
    "how_heading": "ఇది ఎలా పనిచేస్తుంది",
    "how_sub": "మూడు దశలు, సైన్-అప్ అవసరం లేదు.",
    "how1_title": "టైప్ చేయండి, మాట్లాడండి లేదా ఫోటో తీయండి",
    "how1_text": "ప్రశ్నను టైప్ చేయండి, మాట్లాడి అడగండి 🎤, లేదా "
                 "నోట్‌బుక్ ఫోటో పంపండి 📷.",
    "how2_title": "ప్రతి దశను చూడండి",
    "how2_text": "సాల్వర్ చివరి సమాధానం మాత్రమే కాకుండా పూర్తి "
                 "పద్ధతిని చూపిస్తుంది.",
    "how3_title": "సేవ్ చేసి అభ్యాసం చేయండి",
    "how3_text": "పరిష్కారాన్ని .txt ఫైల్‌గా డౌన్‌లోడ్ చేయండి, "
                 "చరిత్రలో మళ్లీ చూడండి, లేదా అభ్యాసంలో సమయ క్విజ్ "
                 "ఇవ్వండి.",
    "t_arithmetic": "అంకగణితం",
    "t_algebra": "బీజగణితం",
    "t_exponents_logs": "ఘాతాంకాలు మరియు లాగరిథమ్‌లు",
    "t_trigonometry": "త్రికోణమితి",
    "t_calculus": "కలన గణితం (కాల్కులస్)",
    "t_transforms": "రూపాంతరాలు మరియు శ్రేణులు",
    "t_linear_algebra": "రేఖీయ బీజగణితం",
    "t_geometry": "జ్యామితి",
    "t_statistics": "గణాంకాలు మరియు సంభావ్యత",
    "t_distributions": "సంభావ్యత పంపిణీలు",
    "t_number_theory": "సంఖ్యా సిద్ధాంతం",
    "t_sequences": "అనుక్రమాలు మరియు శ్రేణులు",
    "t_complex": "సంకీర్ణ సంఖ్యలు",
    "t_sets": "సమితులు",
    "t_units": "ప్రమాణ మార్పిడి",
    "t_word_problems": "పద సమస్యలు",
    "t_graphs": "గ్రాఫ్‌లు",
    "question_heading": "ప్రశ్న",
    "answer_heading": "సమాధానం",
    "steps_heading": "దశలవారీ పరిష్కారం",
    "understood_as": "ఇలా అర్థం చేసుకుంది:",
    "full_result": "పూర్తి ఫలితం (JSON)",
    "download_link": "⬇ పరిష్కారాన్ని డౌన్‌లోడ్ చేయండి (.txt)",
    "ask_another": "← మరో ప్రశ్న అడగండి",
    "explanation_heading": "💡 వివరణ",
    "photo_heading": "📷 మీ ఫోటో నుండి చదివిన ప్రశ్న",
    "photo_text": "ఈ ప్రశ్న మీ ఫోటో నుండి చదవబడింది — ఏదైనా తప్పుగా "
                  "అనిపిస్తే సరిచేసి 'పరిష్కరించండి' నొక్కండి. (OCR "
                  "కొన్నిసార్లు సంఖ్య లేదా గుర్తును తప్పుగా "
                  "చదువుతుంది, కాబట్టి ముందుగా వచనాన్ని తనిఖీ "
                  "చేయండి.)",
    "photo_fix_btn": "సరిచేసి పరిష్కరించండి →",
    "photo_below": "క్రింద చదివిన ప్రశ్నకు సమాధానం ఇవ్వబడింది:",
    "quiz_heading": "సమయ క్విజ్ 🎯",
    "quiz_intro": "అంశం మరియు కష్టతను ఎంచుకోండి — మీకు {count} "
                  "ప్రశ్నలు మరియు {seconds} సెకన్లు లభిస్తాయి. "
                  "సమర్పించినప్పుడు సమాధానాలు తనిఖీ చేయబడతాయి.",
    "topic_label": "అంశం",
    "difficulty_label": "కష్టత",
    "start_quiz": "క్విజ్ ప్రారంభించండి",
    "restart_quiz": "క్విజ్ మళ్లీ ప్రారంభించండి",
    "time_left": "⏱ మిగిలిన సమయం:",
    "your_answer_ph": "మీ సమాధానం",
    "submit_answers": "సమాధానాలు సమర్పించండి",
    "practice_heading": "అభ్యాస ప్రశ్నలు",
    "practice_intro": "ముందుగా ప్రతి ప్రశ్నను మీరే పరిష్కరించడానికి "
                      "ప్రయత్నించండి, తర్వాత సమాధానం చూడండి. కొత్త "
                      "సెట్ కోసం పేజీని మళ్లీ లోడ్ చేయండి.",
    "show_answer": "సమాధానం చూపించండి",
    "new_set": "↻ కొత్త సెట్",
    "classic_prefer": "సమయ పరిమితి లేని అభ్యాసం కావాలా?",
    "classic_open": "క్లాసిక్ అభ్యాస సెట్ తెరవండి",
    "classic_note": "(మీరు చూపించే వరకు సమాధానాలు దాగి ఉంటాయి).",
    "back_to_solver": "← సాల్వర్‌కు తిరిగి వెళ్లండి",
    "result_heading": "క్విజ్ ఫలితం 🏆",
    "score_label": "స్కోరు:",
    "your_answer_label": "మీ సమాధానం:",
    "correct_answer_label": "సరైన సమాధానం:",
    "blank": "(ఖాళీ)",
    "finished_in": "పట్టిన సమయం",
    "new_quiz": "↻ కొత్త క్విజ్",
    "quiz_topic_arithmetic": "అంకగణితం",
    "quiz_topic_algebra": "బీజగణితం",
    "quiz_topic_trig": "త్రికోణమితి",
    "quiz_topic_stats": "గణాంకాలు",
    "diff_easy": "సులభం",
    "diff_medium": "మధ్యస్థం",
    "diff_hard": "కష్టం",
    "history_heading": "చరిత్ర 🕘",
    "history_intro": "ఈ సెషన్‌లో మీరు పరిష్కరించిన ప్రశ్నలు, కొత్తవి "
                     "ముందు. పూర్తి పరిష్కారాన్ని మళ్లీ చూడటానికి "
                     "ఏదైనా ఒకదానిపై క్లిక్ చేయండి.",
    "clear_history": "చరిత్రను తుడిచివేయండి",
    "history_empty": "ఇక్కడ ఇంకా ఏమీ లేదు — ఒక ప్రశ్నను "
                     "పరిష్కరించండి, అది ఈ జాబితాలో కనిపిస్తుంది.",
    "flash_no_question": "దయచేసి ఒక ప్రశ్నను నమోదు చేయండి.",
    "flash_photo_empty": "ఫోటో నుండి ఏ ప్రశ్నను చదవలేకపోయాము — "
                         "దయచేసి స్పష్టమైన ఫోటోను ఉపయోగించండి, లేదా "
                         "ప్రశ్నను టైప్ చేయండి.",
    "flash_download_first": "ముందుగా ఒక ప్రశ్నను పరిష్కరించండి, "
                            "తర్వాత దాని పరిష్కారాన్ని డౌన్‌లోడ్ "
                            "చేయండి.",
    "flash_start_quiz": "ముందుగా క్విజ్ ప్రారంభించండి.",
    "js_voice_listening_btn": "🎙️ వింటున్నాను… మాట్లాడండి",
    "js_voice_heard": "విన్నాను: “{text}” — ఇప్పుడు 'పరిష్కరించండి' "
                      "నొక్కండి.",
    "js_voice_no_api": "ఈ బ్రౌజర్‌లో వాయిస్ ఇన్‌పుట్ అందుబాటులో లేదు — "
                       "Chrome లో ప్రయత్నించండి.",
    "js_voice_denied": "మైక్ అనుమతి ఇవ్వలేదు — బ్రౌజర్ సెట్టింగ్‌లలో "
                       "మైక్‌ను అనుమతించండి.",
    "js_voice_failed": "వాయిస్ అర్థం కాలేదు, మళ్లీ ప్రయత్నించండి.",
    "js_voice_speak": "మాట్లాడండి, వింటున్నాను…",
    "js_photo_unavailable": "ఫోటో ఫీచర్ ఇంకా లోడ్ కాలేదు — పేజీని "
                            "రిఫ్రెష్ చేసి మళ్లీ ప్రయత్నించండి.",
    "js_photo_reading": "ఫోటో చదువుతున్నాను… ⏳ (అచ్చువేసిన ప్రశ్నలు "
                        "అత్యంత స్పష్టంగా చదవబడతాయి)",
    "js_photo_not_found": "ఫోటోలో ప్రశ్న కనబడలేదు — స్పష్టమైన, నిటారు "
                          "ఫోటోను మళ్లీ పంపండి, లేదా ప్రశ్నను టైప్ "
                          "చేయండి.",
    "js_photo_sending": "ప్రశ్న దొరికింది — పంపుతున్నాను…",
    "js_photo_error": "ఫోటో చదవడంలో సమస్య వచ్చింది — మళ్లీ "
                      "ప్రయత్నించండి లేదా ప్రశ్నను టైప్ చేయండి.",
}

STRINGS["te"] = _TE

# ---------------------------------------------------------------------------
# Explanation lines: ONE summary sentence per result, in the chosen
# language. These are fixed templates with the final answer interpolated
# ({answer}) — deliberately NOT a free-form translation of the steps.
# Lookup order: "type:op" -> "type" -> "generic".
# ---------------------------------------------------------------------------

_EXPLAIN_EN = {
    "generic": "The final answer is {answer} — follow the steps above "
               "to see how it was worked out.",
    "algebra": "This algebra problem comes down to the final answer "
               "{answer} — the steps above show the working.",
    "algebra:equation": "Solving the equation step by step gives "
                        "{answer} — each move keeps both sides "
                        "balanced, as shown above.",
    "arithmetic": "The calculation gives {answer} — the steps above "
                  "show the arithmetic in order.",
    "calculus": "Applying the calculus rules gives {answer} — the "
                "working is shown step by step above.",
    "calculus:derivative": "Differentiating term by term gives "
                            "{answer} — the rule applied at each step "
                            "is shown above.",
    "calculus:integral": "Integrating gives {answer} — the steps above "
                         "show the antiderivative working.",
    "calculus:definite_integral": "Integrating and then substituting "
                                  "the limits gives {answer} — the "
                                  "steps above show the evaluation.",
    "calculus:limit": "Evaluating the limit carefully gives {answer} "
                      "— the steps above show how it was resolved.",
    "complex": "Working with the real and imaginary parts gives "
               "{answer} — see the steps above.",
    "distributions": "Using the distribution's formula, the result is "
                     "{answer} — the substitution is shown in the "
                     "steps above.",
    "exponents_logs": "Using the laws of exponents and logarithms, "
                      "the answer is {answer} — see the steps above.",
    "geometry": "Using the relevant area/volume formulae, the result "
                "is {answer} — the working is shown above.",
    "linear_algebra": "Carrying out the matrix operation gives "
                      "{answer} — the steps above show the working.",
    "number_theory": "The number-theory result is {answer} — the "
                     "factorisation steps above show why.",
    "plot": "The graph has been drawn for you — the key result is "
            "{answer}, and the steps above describe the curve.",
    "sequences": "Using the sequence formula, the answer is {answer} "
                 "— the steps above show the substitution.",
    "sets": "Applying the set operation gives {answer} — the steps "
            "above show which elements were picked.",
    "statistics": "From the given data, the result is {answer} — the "
                  "steps above show how it was computed.",
    "transforms": "Applying the transform gives {answer} — the steps "
                  "above show the standard-form matching.",
    "transforms:laplace_transform": "Using the standard Laplace "
                                    "table gives {answer} — the "
                                    "matching is shown in the steps "
                                    "above.",
    "trigonometry": "Using the standard trigonometric values and "
                    "identities, the answer is {answer} — see the "
                    "steps above.",
    "units": "Converting with the standard conversion factor gives "
             "{answer} — see the steps above.",
    "word_problem": "Setting up the calculation from the problem "
                    "statement gives {answer} — the steps above show "
                    "it.",
}

_EXPLAIN_HI = {
    "generic": "अंतिम उत्तर {answer} है — यह कैसे आया, यह ऊपर के "
               "चरणों में देखें।",
    "algebra": "इस बीजगणित प्रश्न का अंतिम उत्तर {answer} है — ऊपर "
               "के चरणों में पूरी विधि दी गई है।",
    "algebra:equation": "समीकरण को चरण-दर-चरण हल करने से {answer} "
                        "मिलता है — हर चरण में दोनों पक्ष संतुलित "
                        "रखे गए हैं, जैसा ऊपर दिखाया गया है।",
    "arithmetic": "गणना करने से {answer} मिलता है — ऊपर के चरणों में "
                  "गणना क्रम से दिखाई गई है।",
    "calculus": "कलन के नियम लगाने से {answer} मिलता है — पूरी विधि "
                "ऊपर चरण-दर-चरण दी गई है।",
    "calculus:derivative": "पद-दर-पद अवकलन करने से {answer} मिलता "
                           "है — हर चरण में लगाया गया नियम ऊपर "
                           "दिखाया गया है।",
    "calculus:integral": "समाकलन करने से {answer} मिलता है — ऊपर के "
                         "चरणों में प्रतिअवकलज की विधि दिखाई गई है।",
    "calculus:definite_integral": "समाकलन करके सीमाएँ रखने से "
                                  "{answer} मिलता है — ऊपर के चरणों "
                                  "में मूल्यांकन दिखाया गया है।",
    "calculus:limit": "सीमा का सावधानी से मूल्यांकन करने से {answer} "
                      "मिलता है — ऊपर के चरणों में इसकी विधि दिखाई "
                      "गई है।",
    "complex": "वास्तविक और काल्पनिक भागों के साथ कार्य करने से "
               "{answer} मिलता है — ऊपर के चरण देखें।",
    "distributions": "बंटन के सूत्र का उपयोग करने से परिणाम {answer} "
                     "है — ऊपर के चरणों में प्रतिस्थापन दिखाया गया "
                     "है।",
    "exponents_logs": "घातांक और लघुगणक के नियमों से उत्तर {answer} "
                      "है — ऊपर के चरण देखें।",
    "geometry": "संबंधित क्षेत्रफल/आयतन के सूत्रों से परिणाम "
                "{answer} है — विधि ऊपर दिखाई गई है।",
    "linear_algebra": "आव्यूह क्रिया करने से {answer} मिलता है — "
                      "ऊपर के चरणों में विधि दिखाई गई है।",
    "number_theory": "संख्या-सिद्धांत का परिणाम {answer} है — ऊपर के "
                     "गुणनखंड चरण बताते हैं कि क्यों।",
    "plot": "ग्राफ़ आपके लिए बना दिया गया है — मुख्य परिणाम "
            "{answer} है, और ऊपर के चरण वक्र का वर्णन करते हैं।",
    "sequences": "अनुक्रम के सूत्र का उपयोग करने से उत्तर {answer} "
                 "है — ऊपर के चरणों में प्रतिस्थापन दिखाया गया है।",
    "sets": "समुच्चय क्रिया लगाने से {answer} मिलता है — ऊपर के "
            "चरणों में दिखाया गया है कि कौन-से अवयव चुने गए।",
    "statistics": "दिए गए आँकड़ों से परिणाम {answer} है — ऊपर के "
                  "चरणों में गणना दिखाई गई है।",
    "transforms": "रूपांतरण लगाने से {answer} मिलता है — ऊपर के "
                  "चरणों में मानक रूप से मिलान दिखाया गया है।",
    "transforms:laplace_transform": "मानक लाप्लास सारणी का उपयोग "
                                    "करने से {answer} मिलता है — "
                                    "मिलान ऊपर के चरणों में दिखाया "
                                    "गया है।",
    "trigonometry": "मानक त्रिकोणमितीय मानों और सर्वसमिकाओं से "
                    "उत्तर {answer} है — ऊपर के चरण देखें।",
    "units": "मानक रूपांतरण गुणक से बदलने पर {answer} मिलता है — "
             "ऊपर के चरण देखें।",
    "word_problem": "प्रश्न को ध्यान से पढ़कर गणना बनाने से "
                    "{answer} मिलता है — विधि ऊपर के चरणों में है।",
}

EXPLANATIONS = {"en": _EXPLAIN_EN, "hi": _EXPLAIN_HI}

_EXPLAIN_BN = {
    "generic": "চূড়ান্ত উত্তর হলো {answer} — এটি কীভাবে এলো, তা "
               "উপরের ধাপগুলোতে দেখুন।",
    "algebra": "এই বীজগণিত প্রশ্নের চূড়ান্ত উত্তর {answer} — উপরের "
               "ধাপগুলোতে সম্পূর্ণ পদ্ধতি দেওয়া হয়েছে।",
    "algebra:equation": "সমীকরণটি ধাপে ধাপে সমাধান করলে {answer} "
                        "পাওয়া যায় — প্রতিটি ধাপে দুই পক্ষ সমান "
                        "রাখা হয়েছে, যেমন উপরে দেখানো হয়েছে।",
    "arithmetic": "হিসাব করলে {answer} পাওয়া যায় — উপরের ধাপগুলোতে "
                  "হিসাবটি ক্রমানুসারে দেখানো হয়েছে।",
    "calculus": "ক্যালকুলাসের নিয়ম প্রয়োগ করলে {answer} পাওয়া "
                "যায় — সম্পূর্ণ পদ্ধতি উপরে ধাপে ধাপে দেওয়া হয়েছে।",
    "calculus:derivative": "পদ অনুযায়ী অন্তরকলন করলে {answer} "
                           "পাওয়া যায় — প্রতিটি ধাপে প্রয়োগ করা "
                           "নিয়ম উপরে দেখানো হয়েছে।",
    "calculus:integral": "সমাকলন করলে {answer} পাওয়া যায় — উপরের "
                         "ধাপগুলোতে প্রতিঅন্তরজের পদ্ধতি দেখানো "
                         "হয়েছে।",
    "calculus:definite_integral": "সমাকলন করে তারপর সীমা বসালে "
                                  "{answer} পাওয়া যায় — উপরের "
                                  "ধাপগুলোতে মূল্যায়ন দেখানো হয়েছে।",
    "calculus:limit": "সীমাটি সতর্কভাবে মূল্যায়ন করলে {answer} "
                      "পাওয়া যায় — উপরের ধাপগুলোতে পদ্ধতি দেখানো "
                      "হয়েছে।",
    "complex": "বাস্তব ও কাল্পনিক অংশ নিয়ে কাজ করলে {answer} পাওয়া "
               "যায় — উপরের ধাপগুলো দেখুন।",
    "distributions": "বণ্টনের সূত্র ব্যবহার করলে ফলাফল {answer} — "
                     "উপরের ধাপগুলোতে প্রতিস্থাপন দেখানো হয়েছে।",
    "exponents_logs": "সূচক ও লগারিদমের নিয়ম ব্যবহার করলে উত্তর "
                      "{answer} — উপরের ধাপগুলো দেখুন।",
    "geometry": "সংশ্লিষ্ট ক্ষেত্রফল/আয়তনের সূত্র ব্যবহার করলে "
                "ফলাফল {answer} — পদ্ধতি উপরে দেখানো হয়েছে।",
    "linear_algebra": "ম্যাট্রিক্স ক্রিয়াটি করলে {answer} পাওয়া "
                      "যায় — উপরের ধাপগুলোতে পদ্ধতি দেখানো হয়েছে।",
    "number_theory": "সংখ্যা-তত্ত্বের ফলাফল {answer} — উপরের "
                     "উৎপাদকে বিশ্লেষণের ধাপগুলো কারণ ব্যাখ্যা করে।",
    "plot": "লেখচিত্রটি আপনার জন্য আঁকা হয়েছে — মূল ফলাফল {answer}, "
            "এবং উপরের ধাপগুলো বক্ররেখাটি বর্ণনা করে।",
    "sequences": "অনুক্রমের সূত্র ব্যবহার করলে উত্তর {answer} — "
                 "উপরের ধাপগুলোতে প্রতিস্থাপন দেখানো হয়েছে।",
    "sets": "সেট ক্রিয়া প্রয়োগ করলে {answer} পাওয়া যায় — উপরের "
            "ধাপগুলোতে দেখানো হয়েছে কোন উপাদানগুলো বেছে নেওয়া "
            "হয়েছে।",
    "statistics": "প্রদত্ত তথ্য থেকে ফলাফল {answer} — উপরের "
                  "ধাপগুলোতে হিসাব দেখানো হয়েছে।",
    "transforms": "রূপান্তর প্রয়োগ করলে {answer} পাওয়া যায় — "
                  "উপরের ধাপগুলোতে মানক রূপের মিল দেখানো হয়েছে।",
    "transforms:laplace_transform": "মানক ল্যাপলাস সারণি ব্যবহার "
                                    "করলে {answer} পাওয়া যায় — মিলটি "
                                    "উপরের ধাপগুলোতে দেখানো হয়েছে।",
    "trigonometry": "মানক ত্রিকোণমিতিক মান ও অভেদ ব্যবহার করলে "
                    "উত্তর {answer} — উপরের ধাপগুলো দেখুন।",
    "units": "মানক রূপান্তর গুণক দিয়ে বদলালে {answer} পাওয়া যায় — "
             "উপরের ধাপগুলো দেখুন।",
    "word_problem": "প্রশ্নটি মনোযোগ দিয়ে পড়ে হিসাব সাজালে "
                    "{answer} পাওয়া যায় — পদ্ধতি উপরের ধাপগুলোতে "
                    "আছে।",
}

_EXPLAIN_MR = {
    "generic": "अंतिम उत्तर {answer} आहे — ते कसे आले, ते वरील "
               "टप्प्यांमध्ये पहा.",
    "algebra": "या बीजगणित प्रश्नाचे अंतिम उत्तर {answer} आहे — "
               "वरील टप्प्यांमध्ये संपूर्ण पद्धत दिली आहे.",
    "algebra:equation": "समीकरण टप्प्याटप्पाने सोडवल्यास {answer} "
                        "मिळते — प्रत्येक टप्प्यात दोन्ही बाजू "
                        "संतुलित ठेवल्या आहेत, जसे वर दाखवले आहे.",
    "arithmetic": "गणना केल्यास {answer} मिळते — वरील टप्प्यांमध्ये "
                  "गणना क्रमाने दाखवली आहे.",
    "calculus": "कलनाचे नियम लावल्यास {answer} मिळते — संपूर्ण पद्धत "
                "वर टप्प्याटप्पाने दिली आहे.",
    "calculus:derivative": "पदानुसार विकलन केल्यास {answer} मिळते — "
                           "प्रत्येक टप्प्यात लावलेला नियम वर "
                           "दाखवला आहे.",
    "calculus:integral": "समाकलन केल्यास {answer} मिळते — वरील "
                         "टप्प्यांमध्ये प्रतिविकलनाची पद्धत दाखवली "
                         "आहे.",
    "calculus:definite_integral": "समाकलन करून मग मर्यादा ठेवल्यास "
                                  "{answer} मिळते — वरील टप्प्यांमध्ये "
                                  "मूल्यांकन दाखवले आहे.",
    "calculus:limit": "मर्यादेचे काळजीपूर्वक मूल्यांकन केल्यास "
                      "{answer} मिळते — वरील टप्प्यांमध्ये पद्धत "
                      "दाखवली आहे.",
    "complex": "वास्तव आणि काल्पनिक भागांसह काम केल्यास {answer} "
               "मिळते — वरील टप्पे पहा.",
    "distributions": "वितरणाचे सूत्र वापरल्यास निकाल {answer} आहे — "
                     "वरील टप्प्यांमध्ये प्रतिस्थापन दाखवले आहे.",
    "exponents_logs": "घातांक आणि लॉगॅरिदमचे नियम वापरल्यास उत्तर "
                      "{answer} आहे — वरील टप्पे पहा.",
    "geometry": "संबंधित क्षेत्रफळ/आकारमानाच्या सूत्रांनुसार निकाल "
                "{answer} आहे — पद्धत वर दाखवली आहे.",
    "linear_algebra": "मॅट्रिक्स क्रिया केल्यास {answer} मिळते — "
                      "वरील टप्प्यांमध्ये पद्धत दाखवली आहे.",
    "number_theory": "संख्या-सिद्धांताचा निकाल {answer} आहे — वरील "
                     "अवयव पाडण्याचे टप्पे कारण स्पष्ट करतात.",
    "plot": "आलेख तुमच्यासाठी काढला आहे — मुख्य निकाल {answer} आहे, "
            "आणि वरील टप्पे वक्राचे वर्णन करतात.",
    "sequences": "अनुक्रमाचे सूत्र वापरल्यास उत्तर {answer} आहे — "
                 "वरील टप्प्यांमध्ये प्रतिस्थापन दाखवले आहे.",
    "sets": "संच क्रिया लावल्यास {answer} मिळते — वरील टप्प्यांमध्ये "
            "कोणते घटक निवडले ते दाखवले आहे.",
    "statistics": "दिलेल्या माहितीवरून निकाल {answer} आहे — वरील "
                  "टप्प्यांमध्ये गणना दाखवली आहे.",
    "transforms": "रूपांतरण लावल्यास {answer} मिळते — वरील "
                  "टप्प्यांमध्ये मानक रूपाशी जुळणी दाखवली आहे.",
    "transforms:laplace_transform": "मानक लाप्लास तक्ता वापरल्यास "
                                    "{answer} मिळते — जुळणी वरील "
                                    "टप्प्यांमध्ये दाखवली आहे.",
    "trigonometry": "मानक त्रिकोणमितीय मूल्ये आणि एकरूपता वापरल्यास "
                    "उत्तर {answer} आहे — वरील टप्पे पहा.",
    "units": "मानक रूपांतरण गुणकाने बदलल्यास {answer} मिळते — वरील "
             "टप्पे पहा.",
    "word_problem": "प्रश्न काळजीपूर्वक वाचून गणना मांडल्यास "
                    "{answer} मिळते — पद्धत वरील टप्प्यांमध्ये आहे.",
}

EXPLANATIONS["bn"] = _EXPLAIN_BN
EXPLANATIONS["mr"] = _EXPLAIN_MR

_EXPLAIN_TA = {
    "generic": "இறுதிப் பதில் {answer} — அது எப்படி வந்தது என்பதை "
               "மேலே உள்ள படிகளில் பாருங்கள்.",
    "algebra": "இந்த இயற்கணிதக் கணக்கின் இறுதிப் பதில் {answer} — "
               "மேலே உள்ள படிகளில் முழு செயல்முறையும் கொடுக்கப்பட்டுள்ளது.",
    "algebra:equation": "சமன்பாட்டைப் படிப்படியாகத் தீர்த்தால் "
                        "{answer} கிடைக்கும் — ஒவ்வொரு படியிலும் "
                        "இரு பக்கங்களும் சமமாக வைக்கப்பட்டுள்ளன, "
                        "மேலே காட்டப்பட்டுள்ளது போல.",
    "arithmetic": "கணக்கிட்டால் {answer} கிடைக்கும் — மேலே உள்ள "
                  "படிகளில் கணக்கு வரிசையாகக் காட்டப்பட்டுள்ளது.",
    "calculus": "நுண்கணித விதிகளைப் பயன்படுத்தினால் {answer} "
                "கிடைக்கும் — முழு செயல்முறையும் மேலே படிப்படியாக "
                "உள்ளது.",
    "calculus:derivative": "பதம் பதமாக வகைக்கெழு காண {answer} "
                           "கிடைக்கும் — ஒவ்வொரு படியிலும் "
                           "பயன்படுத்தப்பட்ட விதி மேலே "
                           "காட்டப்பட்டுள்ளது.",
    "calculus:integral": "தொகையீடு காண {answer} கிடைக்கும் — மேலே "
                         "உள்ள படிகளில் எதிர்-வகைக்கெழு செயல்முறை "
                         "காட்டப்பட்டுள்ளது.",
    "calculus:definite_integral": "தொகையீடு கண்டு பின் வரம்புகளைப் "
                                  "பிரதியிட {answer} கிடைக்கும் — "
                                  "மேலே உள்ள படிகளில் மதிப்பீடு "
                                  "காட்டப்பட்டுள்ளது.",
    "calculus:limit": "வரம்பைக் கவனமாக மதிப்பிட {answer} கிடைக்கும் "
                      "— மேலே உள்ள படிகளில் முறை "
                      "காட்டப்பட்டுள்ளது.",
    "complex": "மெய் மற்றும் கற்பனைப் பகுதிகளுடன் வேலை செய்தால் "
               "{answer} கிடைக்கும் — மேலே உள்ள படிகளைப் பாருங்கள்.",
    "distributions": "பரவலின் சூத்திரத்தைப் பயன்படுத்தினால் முடிவு "
                     "{answer} — மேலே உள்ள படிகளில் பிரதியீடு "
                     "காட்டப்பட்டுள்ளது.",
    "exponents_logs": "அடுக்கு மற்றும் மடக்கை விதிகளைப் பயன்படுத்தினால் "
                      "பதில் {answer} — மேலே உள்ள படிகளைப் பாருங்கள்.",
    "geometry": "தொடர்புடைய பரப்பு/கனஅளவு சூத்திரங்களைப் பயன்படுத்தினால் "
                "முடிவு {answer} — செயல்முறை மேலே "
                "காட்டப்பட்டுள்ளது.",
    "linear_algebra": "அணிச் செயல்பாட்டைச் செய்தால் {answer} "
                      "கிடைக்கும் — மேலே உள்ள படிகளில் செயல்முறை "
                      "காட்டப்பட்டுள்ளது.",
    "number_theory": "எண் கோட்பாட்டு முடிவு {answer} — மேலே உள்ள "
                     "காரணிப்படுத்தல் படிகள் காரணத்தை விளக்குகின்றன.",
    "plot": "வரைபடம் உங்களுக்காக வரையப்பட்டுள்ளது — முக்கிய முடிவு "
            "{answer}, மேலே உள்ள படிகள் வளைவை விவரிக்கின்றன.",
    "sequences": "தொடர்வரிசைச் சூத்திரத்தைப் பயன்படுத்தினால் பதில் "
                 "{answer} — மேலே உள்ள படிகளில் பிரதியீடு "
                 "காட்டப்பட்டுள்ளது.",
    "sets": "கணச் செயல்பாட்டைப் பயன்படுத்தினால் {answer} கிடைக்கும் "
            "— மேலே உள்ள படிகளில் எந்த உறுப்புகள் தேர்ந்தெடுக்கப்பட்டன "
            "என்பது காட்டப்பட்டுள்ளது.",
    "statistics": "கொடுக்கப்பட்ட தரவிலிருந்து முடிவு {answer} — மேலே "
                  "உள்ள படிகளில் கணக்கீடு காட்டப்பட்டுள்ளது.",
    "transforms": "மாற்றத்தைப் பயன்படுத்தினால் {answer} கிடைக்கும் — "
                  "மேலே உள்ள படிகளில் திட்ட வடிவப் பொருத்தம் "
                  "காட்டப்பட்டுள்ளது.",
    "transforms:laplace_transform": "திட்ட லாப்லாஸ் அட்டவணையைப் "
                                    "பயன்படுத்தினால் {answer} "
                                    "கிடைக்கும் — பொருத்தம் மேலே உள்ள "
                                    "படிகளில் காட்டப்பட்டுள்ளது.",
    "trigonometry": "திட்ட முக்கோணவியல் மதிப்புகள் மற்றும் "
                    "முற்றொருமைகளைப் பயன்படுத்தினால் பதில் {answer} "
                    "— மேலே உள்ள படிகளைப் பாருங்கள்.",
    "units": "திட்ட மாற்றக் காரணியால் மாற்றினால் {answer} கிடைக்கும் "
             "— மேலே உள்ள படிகளைப் பாருங்கள்.",
    "word_problem": "கணக்கைக் கவனமாகப் படித்துக் கணக்கீட்டை "
                    "அமைத்தால் {answer} கிடைக்கும் — செயல்முறை மேலே "
                    "உள்ள படிகளில் உள்ளது.",
}

_EXPLAIN_TE = {
    "generic": "చివరి సమాధానం {answer} — అది ఎలా వచ్చిందో పైన ఉన్న "
               "దశల్లో చూడండి.",
    "algebra": "ఈ బీజగణిత సమస్య యొక్క చివరి సమాధానం {answer} — పైన "
               "ఉన్న దశల్లో పూర్తి పద్ధతి ఇవ్వబడింది.",
    "algebra:equation": "సమీకరణాన్ని దశలవారీగా పరిష్కరిస్తే {answer} "
                        "వస్తుంది — ప్రతి దశలో రెండు వైపులా సమతుల్యంగా "
                        "ఉంచబడ్డాయి, పైన చూపినట్లుగా.",
    "arithmetic": "లెక్కిస్తే {answer} వస్తుంది — పైన ఉన్న దశల్లో "
                  "లెక్క క్రమంలో చూపబడింది.",
    "calculus": "కలన గణిత నియమాలను వర్తింపజేస్తే {answer} వస్తుంది — "
                "పూర్తి పద్ధతి పైన దశలవారీగా ఇవ్వబడింది.",
    "calculus:derivative": "పదం పదంగా అవకలనం చేస్తే {answer} "
                           "వస్తుంది — ప్రతి దశలో వర్తింపజేసిన నియమం "
                           "పైన చూపబడింది.",
    "calculus:integral": "సమాకలనం చేస్తే {answer} వస్తుంది — పైన ఉన్న "
                         "దశల్లో ప్రత్యవకలజ పద్ధతి చూపబడింది.",
    "calculus:definite_integral": "సమాకలనం చేసి తర్వాత పరిమితులను "
                                  "ప్రతిక్షేపిస్తే {answer} వస్తుంది "
                                  "— పైన ఉన్న దశల్లో మూల్యాంకనం "
                                  "చూపబడింది.",
    "calculus:limit": "పరిమితిని జాగ్రత్తగా మూల్యాంకనం చేస్తే "
                      "{answer} వస్తుంది — పైన ఉన్న దశల్లో పద్ధతి "
                      "చూపబడింది.",
    "complex": "వాస్తవ మరియు ఊహా భాగాలతో పని చేస్తే {answer} "
               "వస్తుంది — పైన ఉన్న దశలను చూడండి.",
    "distributions": "పంపిణీ సూత్రాన్ని ఉపయోగిస్తే ఫలితం {answer} — "
                     "పైన ఉన్న దశల్లో ప్రతిక్షేపణ చూపబడింది.",
    "exponents_logs": "ఘాతాంకాలు మరియు లాగరిథమ్‌ల నియమాలను "
                      "ఉపయోగిస్తే సమాధానం {answer} — పైన ఉన్న దశలను "
                      "చూడండి.",
    "geometry": "సంబంధిత వైశాల్యం/ఘనపరిమాణ సూత్రాలను ఉపయోగిస్తే "
                "ఫలితం {answer} — పద్ధతి పైన చూపబడింది.",
    "linear_algebra": "మాత్రిక చర్యను చేస్తే {answer} వస్తుంది — "
                      "పైన ఉన్న దశల్లో పద్ధతి చూపబడింది.",
    "number_theory": "సంఖ్యా సిద్ధాంత ఫలితం {answer} — పైన ఉన్న "
                     "కారణాంక దశలు కారణాన్ని వివరిస్తాయి.",
    "plot": "గ్రాఫ్ మీ కోసం గీయబడింది — ముఖ్య ఫలితం {answer}, పైన "
            "ఉన్న దశలు వక్రాన్ని వివరిస్తాయి.",
    "sequences": "అనుక్రమ సూత్రాన్ని ఉపయోగిస్తే సమాధానం {answer} — "
                 "పైన ఉన్న దశల్లో ప్రతిక్షేపణ చూపబడింది.",
    "sets": "సమితి చర్యను వర్తింపజేస్తే {answer} వస్తుంది — పైన "
            "ఉన్న దశల్లో ఏ మూలకాలు ఎంచుకున్నారో చూపబడింది.",
    "statistics": "ఇచ్చిన దత్తాంశం నుండి ఫలితం {answer} — పైన ఉన్న "
                  "దశల్లో లెక్క చూపబడింది.",
    "transforms": "రూపాంతరాన్ని వర్తింపజేస్తే {answer} వస్తుంది — "
                  "పైన ఉన్న దశల్లో ప్రామాణిక రూప సరిపోలిక చూపబడింది.",
    "transforms:laplace_transform": "ప్రామాణిక లాప్లాస్ పట్టికను "
                                    "ఉపయోగిస్తే {answer} వస్తుంది — "
                                    "సరిపోలిక పైన ఉన్న దశల్లో "
                                    "చూపబడింది.",
    "trigonometry": "ప్రామాణిక త్రికోణమితి విలువలు మరియు "
                    "సర్వసమానతలను ఉపయోగిస్తే సమాధానం {answer} — పైన "
                    "ఉన్న దశలను చూడండి.",
    "units": "ప్రామాణిక మార్పిడి కారకంతో మారిస్తే {answer} వస్తుంది "
             "— పైన ఉన్న దశలను చూడండి.",
    "word_problem": "సమస్యను జాగ్రత్తగా చదివి లెక్కను ఏర్పాటు "
                    "చేస్తే {answer} వస్తుంది — పద్ధతి పైన ఉన్న "
                    "దశల్లో ఉంది.",
}

EXPLANATIONS["ta"] = _EXPLAIN_TA
EXPLANATIONS["te"] = _EXPLAIN_TE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalise_lang(code):
    """Return a supported language code, falling back to English."""
    code = (code or "").strip().lower()
    return code if code in SUPPORTED_LANGS else "en"


def get_strings(lang):
    """UI strings for `lang`, merged over English (fallback)."""
    merged = dict(STRINGS["en"])
    if lang in STRINGS and lang != "en":
        merged.update(STRINGS[lang])
    return merged


def explanation_for(result, lang):
    """One localised summary sentence for a solver result dict.

    Template lookup: "type:op" -> "type" -> "generic", always with the
    final answer interpolated. Never raises.
    """
    table = EXPLANATIONS.get(lang) or EXPLANATIONS["en"]
    fallback = EXPLANATIONS["en"]
    answer = str((result or {}).get("answer", "")).strip()
    rtype = (result or {}).get("type", "") or ""
    rop = (result or {}).get("op", "") or ""
    template = (table.get(f"{rtype}:{rop}") or table.get(rtype)
                or fallback.get(f"{rtype}:{rop}") or fallback.get(rtype)
                or table.get("generic") or fallback["generic"])
    try:
        return template.format(answer=answer)
    except (KeyError, IndexError, ValueError):
        return fallback["generic"].format(answer=answer)
