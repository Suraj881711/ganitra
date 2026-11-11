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


def result_unsolvable(result):
    """Wave 5b: presentation-layer flag — did the solver fail?

    The solver signals failure with op == "error" and the raw wording
    "Could not solve this one: <detail>", which is a programmer
    message and must never reach a student. app.py/api.py use this
    detector to render the friendly localised error card instead.
    Conservative on purpose: op == "error" is the solver's only
    failure signal and real solves never use it.
    """
    result = result or {}
    return (result.get("op") == "error"
            or str(result.get("answer", "")).startswith(
                "Could not solve"))


# Wave 5b: keyboard-mash / nonsense-word guard. The solver's
# arithmetic path happily "simplifies" a string of unknown words by
# multiplying their letters together ("asdf qwer zxq" ->
# a*d*e*f*q**2*r*s*w*x*z), which looks like an answer but teaches
# nothing. A result is treated as unsolvable for display when ALL of
# these hold (kept deliberately narrow so real symbolic simplifies
# like "x + y", "(x+1)(x+2)", "2x + 3x" or "abc" are NEVER flagged):
#   * the result is an arithmetic/algebra "simplify", and
#   * the question has at least two multi-letter words (len >= 3),
#     none of which is a known maths/command word, and
#   * the question has no digits and no operator characters.
_GIBBERISH_SAFE_WORDS = {
    "sin", "cos", "tan", "sec", "csc", "cot", "log", "exp", "sqrt",
    "lim", "sum", "int", "gcd", "lcm", "hcf", "mod", "abs", "max",
    "min", "mean", "mode", "median", "prime", "factor", "factors",
    "expand", "simplify", "solve", "find", "value", "graph", "plot",
    "area", "volume", "radius", "circle", "square", "triangle",
    "rectangle", "angle", "degree", "degrees", "percent", "percentage",
    "probability", "derivative", "integral", "differentiate",
    "integrate", "limit", "equation", "root", "roots", "power",
    "cube", "cubed", "the", "and", "for", "with", "from", "what",
    "when", "is", "of", "to", "in", "a", "an",
    "jodo", "ghatana", "guna", "bhaag", "pratishat", "ausat",
}


def question_looks_like_gibberish(question, result):
    """True when `question` is word-salad that the solver merely
    letter-multiplied (see the note above). Presentation-layer only:
    the solver itself is untouched."""
    result = result or {}
    if result.get("op") != "simplify":
        return False
    if result.get("type") not in ("arithmetic", "algebra"):
        return False
    q = str(question or "").lower()
    if any(ch.isdigit() for ch in q):
        return False
    if any(ch in q for ch in "+-*/^=()<>%"):
        return False
    words = [w.strip(".,?!;:") for w in q.split()]
    words = [w for w in words if w]
    long_words = [w for w in words if len(w) >= 3 and w.isalpha()]
    if len(long_words) < 2:
        return False
    return not any(w in _GIBBERISH_SAFE_WORDS for w in long_words)


def solve_failed(question, result):
    """Wave 5b: the single display-time failure test used by app.py
    and api.py — a solver error result OR word-salad input."""
    return (result_unsolvable(result)
            or question_looks_like_gibberish(question, result))


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


# ---------------------------------------------------------------------------
# Wave 5 strings: chat homepage, Board Mode, Mistake Notebook, PDF/print.
# Kept as one block per language and merged into the main dicts below so
# the completeness rule still holds: every key exists in all 6 languages
# (get_strings() additionally falls back to English for anything missed).
# ---------------------------------------------------------------------------

_EN_W5 = {
    "nav_board": "Board Mode",
    "nav_mistakes": "Mistakes",
    # chat homepage
    "chat_welcome": "Namaste! 🙏 Ask me any maths question — type it, "
                    "speak it 🎤, or send a photo 📷 — and I will solve "
                    "it step by step, right here in the chat.",
    "chat_solving": "Solving…",
    "chat_full_solution": "Full solution page →",
    "chat_error": "Something went wrong — please try again.",
    # board mode
    "board_heading": "Board Mode 📚",
    "board_intro": "NCERT maths chapters for Classes 6–12. The chapter "
                   "list is the same for CBSE, ICSE and state boards, "
                   "so pick your board, choose your class, and practise "
                   "chapter by chapter.",
    "board_choose_board": "Your board",
    "board_choose_class": "Choose your class",
    "board_class_word": "Class",
    "board_chapters_heading": "Chapters",
    "board_practice_btn": "Practice (untimed)",
    "board_test_btn": "Chapter test (timed)",
    "board_back": "← Board Mode",
    "board_test_heading": "Chapter test 🎯",
    "board_start_test": "Start chapter test",
    "board_topic_label": "Questions from:",
    "board_fallback_note": "Closest topic match — a dedicated "
                           "generator for this chapter is still "
                           "to come.",
    "quiz_topic_sequences": "Sequences & Series",
    "quiz_topic_probability": "Probability",
    "quiz_topic_calculus": "Calculus",
    "quiz_topic_linear_algebra": "Linear Algebra",
    "quiz_topic_geometry": "Geometry",
    # mistake notebook
    "mistakes_heading": "Mistake Notebook 📒",
    "mistakes_intro": "Questions you got wrong in quizzes and chapter "
                      "tests, newest first. This notebook is kept "
                      "only in your browser session — it clears when "
                      "the session ends.",
    "mistakes_empty": "No mistakes recorded yet — take a quiz or a "
                      "chapter test and the questions you miss will "
                      "appear here.",
    "mistakes_practice_btn": "↻ Practice these again",
    "mistakes_clear_btn": "Clear notebook",
    "mistakes_correct_is": "Correct answer:",
    # pdf / print
    "pdf_link": "🖨 Download PDF",
    "print_btn": "Print / Save as PDF",
    "print_footer": "Solved by Ganitra",
}

_HI_W5 = {
    "nav_board": "बोर्ड मोड",
    "nav_mistakes": "ग़लतियाँ",
    "chat_welcome": "नमस्ते! 🙏 कोई भी गणित का प्रश्न पूछिए — लिखकर, "
                    "बोलकर 🎤, या फ़ोटो भेजकर 📷 — और मैं उसे यहीं "
                    "चैट में चरण-दर-चरण हल कर दूँगा।",
    "chat_solving": "हल हो रहा है…",
    "chat_full_solution": "पूरे हल का पृष्ठ →",
    "chat_error": "कुछ गड़बड़ हो गई — कृपया फिर प्रयास कीजिए।",
    "board_heading": "बोर्ड मोड 📚",
    "board_intro": "कक्षा 6–12 के NCERT गणित अध्याय। अध्याय सूची "
                   "CBSE, ICSE और राज्य बोर्डों के लिए एक समान है — "
                   "अपना बोर्ड चुनिए, कक्षा चुनिए और अध्याय-दर-अध्याय "
                   "अभ्यास कीजिए।",
    "board_choose_board": "आपका बोर्ड",
    "board_choose_class": "अपनी कक्षा चुनिए",
    "board_class_word": "कक्षा",
    "board_chapters_heading": "अध्याय",
    "board_practice_btn": "अभ्यास (बिना समय सीमा)",
    "board_test_btn": "अध्याय परीक्षा (समयबद्ध)",
    "board_back": "← बोर्ड मोड",
    "board_test_heading": "अध्याय परीक्षा 🎯",
    "board_start_test": "अध्याय परीक्षा शुरू कीजिए",
    "board_topic_label": "प्रश्न इस विषय से:",
    "board_fallback_note": "सबसे निकट विषय मेल — इस अध्याय के लिए "
                           "अलग जनरेटर अभी आना बाकी है।",
    "quiz_topic_sequences": "अनुक्रम और श्रेणियाँ",
    "quiz_topic_probability": "प्रायिकता",
    "quiz_topic_calculus": "कलन (कैलकुलस)",
    "quiz_topic_linear_algebra": "रैखिक बीजगणित",
    "quiz_topic_geometry": "ज्यामिति",
    "mistakes_heading": "ग़लतियों की नोटबुक 📒",
    "mistakes_intro": "क्विज़ और अध्याय परीक्षाओं में ग़लत हुए "
                      "प्रश्न, सबसे नए पहले। यह नोटबुक केवल आपके "
                      "ब्राउज़र सत्र में रहती है — सत्र समाप्त होते "
                      "ही साफ़ हो जाती है।",
    "mistakes_empty": "अभी कोई ग़लती दर्ज नहीं है — क्विज़ या अध्याय "
                      "परीक्षा दीजिए, ग़लत हुए प्रश्न यहाँ आएँगे।",
    "mistakes_practice_btn": "↻ इन्हें फिर से अभ्यास कीजिए",
    "mistakes_clear_btn": "नोटबुक साफ़ कीजिए",
    "mistakes_correct_is": "सही उत्तर:",
    "pdf_link": "🖨 PDF डाउनलोड कीजिए",
    "print_btn": "प्रिंट / PDF के रूप में सहेजिए",
    "print_footer": "Ganitra द्वारा हल किया गया",
}

_BN_W5 = {
    "nav_board": "বোর্ড মোড",
    "nav_mistakes": "ভুলগুলি",
    "chat_welcome": "নমস্কার! 🙏 যেকোনো গণিতের প্রশ্ন জিজ্ঞাসা করুন — "
                    "লিখে, বলে 🎤, বা ছবি পাঠিয়ে 📷 — আমি এখানেই "
                    "চ্যাটে ধাপে ধাপে সমাধান করে দেব।",
    "chat_solving": "সমাধান হচ্ছে…",
    "chat_full_solution": "সম্পূর্ণ সমাধানের পৃষ্ঠা →",
    "chat_error": "কিছু একটা ভুল হয়েছে — আবার চেষ্টা করুন।",
    "board_heading": "বোর্ড মোড 📚",
    "board_intro": "ষষ্ঠ থেকে দ্বাদশ শ্রেণির NCERT গণিত অধ্যায়। "
                   "অধ্যায়ের তালিকা CBSE, ICSE ও রাজ্য বোর্ডগুলির "
                   "জন্য একই — আপনার বোর্ড বেছে নিন, শ্রেণি বেছে "
                   "নিন এবং অধ্যায় অনুযায়ী অনুশীলন করুন।",
    "board_choose_board": "আপনার বোর্ড",
    "board_choose_class": "আপনার শ্রেণি বেছে নিন",
    "board_class_word": "শ্রেণি",
    "board_chapters_heading": "অধ্যায়সমূহ",
    "board_practice_btn": "অনুশীলন (সময়সীমা ছাড়া)",
    "board_test_btn": "অধ্যায় পরীক্ষা (সময়বদ্ধ)",
    "board_back": "← বোর্ড মোড",
    "board_test_heading": "অধ্যায় পরীক্ষা 🎯",
    "board_start_test": "অধ্যায় পরীক্ষা শুরু করুন",
    "board_topic_label": "প্রশ্ন এই বিষয় থেকে:",
    "board_fallback_note": "সবচেয়ে কাছের বিষয়ের মিল — এই অধ্যায়ের "
                           "জন্য আলাদা জেনারেটর এখনও আসতে বাকি।",
    "quiz_topic_sequences": "অনুক্রম ও ধারা",
    "quiz_topic_probability": "সম্ভাবনা",
    "quiz_topic_calculus": "ক্যালকুলাস",
    "quiz_topic_linear_algebra": "রৈখিক বীজগণিত",
    "quiz_topic_geometry": "জ্যামিতি",
    "mistakes_heading": "ভুলের খাতা 📒",
    "mistakes_intro": "কুইজ ও অধ্যায় পরীক্ষায় ভুল করা প্রশ্নগুলি, "
                      "সবচেয়ে নতুন আগে। এই খাতাটি শুধু আপনার "
                      "ব্রাউজার সেশনে থাকে — সেশন শেষ হলেই মুছে "
                      "যায়।",
    "mistakes_empty": "এখনও কোনো ভুল লেখা নেই — কুইজ বা অধ্যায় "
                      "পরীক্ষা দিন, ভুল করা প্রশ্নগুলি এখানে আসবে।",
    "mistakes_practice_btn": "↻ এগুলি আবার অনুশীলন করুন",
    "mistakes_clear_btn": "খাতা পরিষ্কার করুন",
    "mistakes_correct_is": "সঠিক উত্তর:",
    "pdf_link": "🖨 PDF ডাউনলোড করুন",
    "print_btn": "প্রিন্ট / PDF হিসেবে সংরক্ষণ করুন",
    "print_footer": "Ganitra দ্বারা সমাধান করা হয়েছে",
}

_MR_W5 = {
    "nav_board": "बोर्ड मोड",
    "nav_mistakes": "चुका",
    "chat_welcome": "नमस्कार! 🙏 कोणताही गणिताचा प्रश्न विचारा — "
                    "लिहून, बोलून 🎤, किंवा फोटो पाठवून 📷 — आणि "
                    "मी तो इथेच चॅटमध्ये टप्प्याटप्प्यात सोडवून "
                    "देईन.",
    "chat_solving": "सोडवत आहे…",
    "chat_full_solution": "संपूर्ण उत्तराचे पान →",
    "chat_error": "काहीतरी चुकले — कृपया पुन्हा प्रयत्न करा.",
    "board_heading": "बोर्ड मोड 📚",
    "board_intro": "इयत्ता ६–१२ साठी NCERT गणित प्रकरणे. "
                   "प्रकरणांची यादी CBSE, ICSE आणि राज्य बोर्डांसाठी "
                   "सारखीच आहे — तुमचे बोर्ड निवडा, इयत्ता निवडा "
                   "आणि प्रकरणानुसार सराव करा.",
    "board_choose_board": "तुमचे बोर्ड",
    "board_choose_class": "तुमची इयत्ता निवडा",
    "board_class_word": "इयत्ता",
    "board_chapters_heading": "प्रकरणे",
    "board_practice_btn": "सराव (वेळेमर्यादेशिवाय)",
    "board_test_btn": "प्रकरण चाचणी (वेळेबद्ध)",
    "board_back": "← बोर्ड मोड",
    "board_test_heading": "प्रकरण चाचणी 🎯",
    "board_start_test": "प्रकरण चाचणी सुरू करा",
    "board_topic_label": "प्रश्न या विषयातून:",
    "board_fallback_note": "सर्वात जवळचा विषय जुळतो — या प्रकरणासाठी "
                           "स्वतंत्र जनरेटर अजून यायचा आहे.",
    "quiz_topic_sequences": "अनुक्रम व श्रेणी",
    "quiz_topic_probability": "संभाव्यता",
    "quiz_topic_calculus": "कलनशास्त्र (कॅल्क्युलस)",
    "quiz_topic_linear_algebra": "रेषीय बीजगणित",
    "quiz_topic_geometry": "भूमिती",
    "mistakes_heading": "चुकांची वही 📒",
    "mistakes_intro": "क्विझ आणि प्रकरण चाचण्यांमध्ये चुकलेले "
                      "प्रश्न, सर्वात नवीन आधी. ही वही फक्त तुमच्या "
                      "ब्राउझर सत्रात राहते — सत्र संपताच ती साफ "
                      "होते.",
    "mistakes_empty": "अजून एकही चूक नोंदवलेली नाही — क्विझ किंवा "
                      "प्रकरण चाचणी द्या, चुकलेले प्रश्न इथे येतील.",
    "mistakes_practice_btn": "↻ हे पुन्हा सराव करा",
    "mistakes_clear_btn": "वही साफ करा",
    "mistakes_correct_is": "बरोबर उत्तर:",
    "pdf_link": "🖨 PDF डाउनलोड करा",
    "print_btn": "प्रिंट / PDF म्हणून जतन करा",
    "print_footer": "Ganitra ने सोडवले",
}

_TA_W5 = {
    "nav_board": "போர்டு பயன்முறை",
    "nav_mistakes": "தவறுகள்",
    "chat_welcome": "வணக்கம்! 🙏 எந்தக் கணிதக் கேள்வியையும் "
                    "கேளுங்கள் — தட்டச்சு செய்து, பேசி 🎤, அல்லது "
                    "புகைப்படம் அனுப்பி 📷 — நான் இங்கேயே "
                    "அரட்டையில் படிப்படியாகத் தீர்த்து வைப்பேன்.",
    "chat_solving": "தீர்த்து வருகிறது…",
    "chat_full_solution": "முழு தீர்வுப் பக்கம் →",
    "chat_error": "ஏதோ தவறு நடந்துவிட்டது — மீண்டும் முயற்சிக்கவும்.",
    "board_heading": "போர்டு பயன்முறை 📚",
    "board_intro": "6–12 ஆம் வகுப்புகளுக்கான NCERT கணித "
                   "அத்தியாயங்கள். அத்தியாயப் பட்டியல் CBSE, ICSE "
                   "மற்றும் மாநில போர்டுகளுக்கு ஒன்றே — உங்கள் "
                   "போர்டைத் தேர்ந்தெடுத்து, வகுப்பைத் "
                   "தேர்ந்தெடுத்து, அத்தியாயம் வாரியாகப் பயிற்சி "
                   "செய்யுங்கள்.",
    "board_choose_board": "உங்கள் போர்டு",
    "board_choose_class": "உங்கள் வகுப்பைத் தேர்ந்தெடுங்கள்",
    "board_class_word": "வகுப்பு",
    "board_chapters_heading": "அத்தியாயங்கள்",
    "board_practice_btn": "பயிற்சி (நேர வரம்பின்றி)",
    "board_test_btn": "அத்தியாயத் தேர்வு (நேர அடிப்படையில்)",
    "board_back": "← போர்டு பயன்முறை",
    "board_test_heading": "அத்தியாயத் தேர்வு 🎯",
    "board_start_test": "அத்தியாயத் தேர்வைத் தொடங்குங்கள்",
    "board_topic_label": "கேள்விகள் இந்தத் தலைப்பிலிருந்து:",
    "board_fallback_note": "மிக அருகிலுள்ள தலைப்புப் பொருத்தம் — "
                           "இந்த அத்தியாயத்திற்கான தனி ஜெனரேட்டர் "
                           "இன்னும் வரவில்லை.",
    "quiz_topic_sequences": "தொடர்கள் & தொடர்வரிசைகள்",
    "quiz_topic_probability": "நிகழ்தகவு",
    "quiz_topic_calculus": "கால்குலஸ்",
    "quiz_topic_linear_algebra": "நேரியல் இயற்கணிதம்",
    "quiz_topic_geometry": "வடிவியல்",
    "mistakes_heading": "தவறுகள் குறிப்பேடு 📒",
    "mistakes_intro": "வினாடி வினாக்கள் மற்றும் அத்தியாயத் "
                      "தேர்வுகளில் நீங்கள் தவறவிட்ட கேள்விகள், "
                      "புதியவை முதலில். இந்தக் குறிப்பேடு உங்கள் "
                      "உலாவி அமர்வில் மட்டுமே இருக்கும் — அமர்வு "
                      "முடிந்ததும் அழிந்துவிடும்.",
    "mistakes_empty": "இன்னும் தவறுகள் எதுவும் பதிவாகவில்லை — ஒரு "
                      "வினாடி வினா அல்லது அத்தியாயத் தேர்வு "
                      "எழுதுங்கள், தவறவிட்ட கேள்விகள் இங்கே வரும்.",
    "mistakes_practice_btn": "↻ இவற்றை மீண்டும் பயிற்சி செய்யுங்கள்",
    "mistakes_clear_btn": "குறிப்பேட்டை அழிக்கவும்",
    "mistakes_correct_is": "சரியான விடை:",
    "pdf_link": "🖨 PDF பதிவிறக்கவும்",
    "print_btn": "அச்சிடு / PDF ஆகச் சேமி",
    "print_footer": "Ganitra ஆல் தீர்க்கப்பட்டது",
}

_TE_W5 = {
    "nav_board": "బోర్డు మోడ్",
    "nav_mistakes": "తప్పులు",
    "chat_welcome": "నమస్తే! 🙏 ఏ గణిత ప్రశ్ననైనా అడగండి — టైప్ "
                    "చేసి, మాట్లాడి 🎤, లేదా ఫోటో పంపి 📷 — నేను "
                    "ఇక్కడే చాట్‌లో దశలవారీగా పరిష్కరిస్తాను.",
    "chat_solving": "పరిష్కరిస్తోంది…",
    "chat_full_solution": "పూర్తి పరిష్కార పేజీ →",
    "chat_error": "ఏదో తప్పు జరిగింది — దయచేసి మళ్లీ ప్రయత్నించండి.",
    "board_heading": "బోర్డు మోడ్ 📚",
    "board_intro": "6–12 తరగతుల కోసం NCERT గణిత అధ్యాయాలు. "
                   "అధ్యాయాల జాబితా CBSE, ICSE మరియు రాష్ట్ర "
                   "బోర్డులకు ఒకటే — మీ బోర్డును ఎంచుకోండి, "
                   "తరగతిని ఎంచుకోండి, అధ్యాయాల వారీగా సాధన "
                   "చేయండి.",
    "board_choose_board": "మీ బోర్డు",
    "board_choose_class": "మీ తరగతిని ఎంచుకోండి",
    "board_class_word": "తరగతి",
    "board_chapters_heading": "అధ్యాయాలు",
    "board_practice_btn": "సాధన (సమయ పరిమితి లేకుండా)",
    "board_test_btn": "అధ్యాయ పరీక్ష (సమయంతో)",
    "board_back": "← బోర్డు మోడ్",
    "board_test_heading": "అధ్యాయ పరీక్ష 🎯",
    "board_start_test": "అధ్యాయ పరీక్ష ప్రారంభించండి",
    "board_topic_label": "ప్రశ్నలు ఈ అంశం నుండి:",
    "board_fallback_note": "అత్యంత దగ్గరి అంశ సరిపోలిక — ఈ అధ్యాయం "
                           "కోసం ప్రత్యేక జనరేటర్ ఇంకా రావాలి.",
    "quiz_topic_sequences": "శ్రేణులు & క్రమాలు",
    "quiz_topic_probability": "సంభావ్యత",
    "quiz_topic_calculus": "కాల్కులస్",
    "quiz_topic_linear_algebra": "రేఖీయ బీజగణితం",
    "quiz_topic_geometry": "జ్యామితి",
    "mistakes_heading": "తప్పుల నోట్‌బుక్ 📒",
    "mistakes_intro": "క్విజ్‌లు మరియు అధ్యాయ పరీక్షల్లో మీరు "
                      "తప్పు చేసిన ప్రశ్నలు, కొత్తవి ముందు. ఈ "
                      "నోట్‌బుక్ మీ బ్రౌజర్ సెషన్‌లో మాత్రమే "
                      "ఉంటుంది — సెషన్ ముగిస్తే తుడిచిపోతుంది.",
    "mistakes_empty": "ఇంకా తప్పులు ఏవీ నమోదు కాలేదు — ఒక క్విజ్ "
                      "లేదా అధ్యాయ పరీక్ష రాయండి, తప్పు చేసిన "
                      "ప్రశ్నలు ఇక్కడ వస్తాయి.",
    "mistakes_practice_btn": "↻ వీటిని మళ్లీ సాధన చేయండి",
    "mistakes_clear_btn": "నోట్‌బుక్ తుడిచేయండి",
    "mistakes_correct_is": "సరైన సమాధానం:",
    "pdf_link": "🖨 PDF డౌన్‌లోడ్ చేయండి",
    "print_btn": "ప్రింట్ / PDF గా సేవ్ చేయండి",
    "print_footer": "Ganitra చే పరిష్కరించబడింది",
}

STRINGS["en"].update(_EN_W5)
STRINGS["hi"].update(_HI_W5)
STRINGS["bn"].update(_BN_W5)
STRINGS["mr"].update(_MR_W5)
STRINGS["ta"].update(_TA_W5)
STRINGS["te"].update(_TE_W5)


# ---------------------------------------------------------------------------
# Wave 5b: Teacher's Advice — curated study tips per solver topic.
# Same pattern as EXPLANATIONS: lookup "type:op" -> quadratic special
# case (below) -> "type" -> English fallback -> "generic". Each line
# combines the concept to revise, the classic student mistake on this
# question type, and a practice suggestion. These are standard,
# generic teaching points — no curriculum claims are made.
# ---------------------------------------------------------------------------

_ADVICE_EN = {
    "generic": "Read the question twice and underline what is "
               "actually asked. After solving, put your answer back "
               "into the question to check it — this one habit "
               "catches most silly mistakes.",
    "arithmetic": "Do one operation per line and follow BODMAS "
                  "strictly. Common mistake: rushing the sign when "
                  "subtracting a negative — put brackets around "
                  "negatives until it becomes habit.",
    "algebra": "Write each step on its own line and keep the equation "
               "balanced. Most algebra marks are lost to sign slips, "
               "not hard ideas — slow down at every minus sign.",
    "algebra:equation": "Revise balancing: whatever you do to one "
                        "side, do to the other. The most common slip "
                        "is a sign error when a term crosses the "
                        "'=' — always check by putting your answer "
                        "back into the original equation. Try 2 more "
                        "like this in Practice.",
    "algebra:quadratic": "For quadratics, first try factorising; if "
                         "that fails, the quadratic formula always "
                         "works. Common mistakes: dropping the ± and "
                         "sign errors with b. The discriminant "
                         "(b²−4ac) tells you how many real roots to "
                         "expect — check it before you start.",
    "trigonometry": "Revise the standard values (sin/cos/tan of 0°, "
                    "30°, 45°, 60°, 90°) until they are automatic. "
                    "Common mistake: mixing up sin and cos, or using "
                    "radians when the question is in degrees.",
    "calculus": "Learn the basic rules (power rule, chain rule, "
                "standard integrals) as a small table and revise it "
                "weekly — calculus rewards steady practice more than "
                "last-minute cramming.",
    "calculus:derivative": "Revise the power rule: the derivative of "
                           "x^n is n·x^(n−1). Common mistake: "
                           "forgetting the chain rule for brackets "
                           "like (2x+1)^3 — differentiate the outside, "
                           "then multiply by the derivative of the "
                           "inside.",
    "calculus:integral": "Integration is differentiation backwards — "
                         "check any integral by differentiating your "
                         "answer. Common mistake: forgetting the "
                         "constant of integration (+C).",
    "calculus:definite_integral": "Integration is differentiation "
                                  "backwards — check the indefinite "
                                  "integral by differentiating it. "
                                  "Then substitute the top limit "
                                  "minus the bottom limit carefully; "
                                  "sign slips there are the classic "
                                  "mistake.",
    "statistics": "First decide what is being asked — mean, median "
                  "and mode are different tools. Common mistake: "
                  "computing the mean when the question wants the "
                  "median (the middle value, after sorting).",
    "statistics:probability": "Probability = favourable outcomes ÷ "
                              "total outcomes, and the total must "
                              "count equally likely cases. Common "
                              "mistake: with two dice, treating sums "
                              "as equally likely — they are not; "
                              "list the pairs.",
    "distributions": "For the normal distribution, always convert to "
                     "a z-score first and sketch the curve — the "
                     "picture prevents most errors. Common mistake: "
                     "using the variance where the standard deviation "
                     "belongs.",
    "geometry": "Write the formula first, then substitute — and keep "
                "units with every number. Common mistake: using the "
                "diameter where the formula needs the radius.",
    "sequences": "Identify whether it is an AP (same difference) or "
                 "GP (same ratio) before touching a formula. Common "
                 "mistake: using n instead of (n−1) in the nth-term "
                 "formula.",
}

_ADVICE_HI = {
    "generic": "प्रश्न दो बार पढ़िए और जो पूछा है उसे रेखांकित "
               "कीजिए। हल के बाद उत्तर को प्रश्न में वापस रखकर "
               "जाँचिए — यही एक आदत अधिकांश छोटी ग़लतियाँ पकड़ "
               "लेती है।",
    "arithmetic": "एक पंक्ति में एक ही संक्रिया कीजिए और BODMAS "
                  "क्रम का कड़ाई से पालन कीजिए। आम ग़लती: "
                  "ऋणात्मक संख्या घटाते समय जल्दबाज़ी — आदत बनने "
                  "तक ऋणात्मक संख्याओं पर कोष्ठक लगाइए।",
    "algebra": "हर चरण अलग पंक्ति में लिखिए और समीकरण संतुलित "
               "रखिए। बीजगणित में अधिकांश अंक कठिन विचारों से "
               "नहीं, चिह्न की छोटी भूलों से कटते हैं — हर ऋण "
               "चिह्न पर धीरे चलिए।",
    "algebra:equation": "संतुलन याद रखिए: जो एक तरफ करें, वही "
                        "दूसरी तरफ भी। सबसे आम ग़लती है पद को '=' "
                        "के पार ले जाते समय चिह्न की भूल — अपना "
                        "उत्तर मूल समीकरण में रखकर हमेशा जाँचिए। "
                        "अभ्यास में ऐसे 2 प्रश्न और हल कीजिए।",
    "algebra:quadratic": "द्विघात समीकरणों में पहले गुणनखंड "
                         "आज़माइए; न बने तो द्विघात सूत्र हमेशा "
                         "काम करता है। आम ग़लतियाँ: ± भूल जाना और "
                         "b के चिह्न की भूल। विविक्तकर (b²−4ac) "
                         "बता देता है कि कितने वास्तविक मूल "
                         "आएँगे — शुरू करने से पहले उसे देख "
                         "लीजिए।",
    "trigonometry": "मानक मान (0°, 30°, 45°, 60°, 90° के sin/cos/"
                    "tan) इतने अभ्यास कीजिए कि वे अपने आप याद आ "
                    "जाएँ। आम ग़लती: sin और cos में गड़बड़ी, या "
                    "डिग्री वाले प्रश्न में रेडियन का उपयोग।",
    "calculus": "बुनियादी नियमों (घात नियम, शृंखला नियम, मानक "
                "समाकल) की छोटी-सी तालिका बनाकर हर सप्ताह "
                "दोहराइए — कलन अंतिम समय की घबराहट से नहीं, "
                "नियमित अभ्यास से आता है।",
    "calculus:derivative": "घात नियम याद रखिए: x^n का अवकलज "
                           "n·x^(n−1) होता है। आम ग़लती: (2x+1)^3 "
                           "जैसे कोष्ठकों में शृंखला नियम भूल "
                           "जाना — पहले बाहर का अवकलज, फिर अंदर "
                           "के अवकलज से गुणा।",
    "calculus:integral": "समाकलन अवकलन का उल्टा है — अपने उत्तर "
                         "का अवकलन करके हर समाकल जाँचिए। आम "
                         "ग़लती: समाकलन स्थिरांक (+C) भूल जाना।",
    "calculus:definite_integral": "समाकलन अवकलन का उल्टा है — "
                                  "अनिश्चित समाकल को अवकलन करके "
                                  "जाँचिए। फिर ऊपर की सीमा घटा "
                                  "नीचे की सीमा सावधानी से रखिए; "
                                  "वहीं चिह्न की भूल सबसे आम "
                                  "है।",
    "statistics": "पहले तय कीजिए कि पूछा क्या है — माध्य, माध्यक "
                  "और बहुलक अलग-अलग साधन हैं। आम ग़लती: जहाँ "
                  "माध्यक (क्रम में रखने पर बीच का मान) चाहिए, "
                  "वहाँ माध्य निकाल देना।",
    "statistics:probability": "प्रायिकता = अनुकूल परिणाम ÷ कुल "
                              "परिणाम, और कुल में सभी समान "
                              "संभावना वाले मामले गिनने चाहिए। "
                              "आम ग़लती: दो पासों के योगों को "
                              "समान संभावना मान लेना — वे नहीं "
                              "होते; जोड़ियाँ लिखकर गिनिए।",
    "distributions": "सामान्य बंटन में पहले z-स्कोर बनाइए और वक्र "
                     "का चित्र अवश्य बनाइए — चित्र अधिकांश "
                     "ग़लतियाँ रोक देता है। आम ग़लती: जहाँ मानक "
                     "विचलन चाहिए, वहाँ प्रसरण रख देना।",
    "geometry": "पहले सूत्र लिखिए, फिर मान रखिए — और हर संख्या के "
                "साथ इकाई भी। आम ग़लती: जहाँ सूत्र में त्रिज्या "
                "चाहिए, वहाँ व्यास रख देना।",
    "sequences": "सूत्र छूने से पहले पहचानिए कि यह AP है (समान "
                 "अंतर) या GP (समान अनुपात)। आम ग़लती: nवें पद "
                 "के सूत्र में (n−1) की जगह n रख देना।",
}

ADVICE = {"en": _ADVICE_EN, "hi": _ADVICE_HI}

_ADVICE_BN = {
    "generic": "প্রশ্নটি দুবার পড়ুন এবং যা চাওয়া হয়েছে তার "
               "নিচে দাগ দিন। সমাধানের পর উত্তরটি প্রশ্নে ফিরিয়ে "
               "বসিয়ে যাচাই করুন — এই একটি অভ্যাসই বেশিরভাগ "
               "ছোট ভুল ধরে ফেলে।",
    "arithmetic": "এক লাইনে একটি করে ক্রিয়া করুন এবং BODMAS "
                  "ক্রম কঠোরভাবে মানুন। সাধারণ ভুল: ঋণাত্মক "
                  "সংখ্যা বিয়োগের সময় তাড়াহুড়ো — অভ্যাস না "
                  "হওয়া পর্যন্ত ঋণাত্মক সংখ্যায় বন্ধনী দিন।",
    "algebra": "প্রতিটি ধাপ আলাদা লাইনে লিখুন এবং সমীকরণের "
               "ভারসাম্য রাখুন। বীজগণিতের বেশিরভাগ নম্বর কঠিন "
               "ধারণায় নয়, চিহ্নের ছোট ভুলে কাটা যায় — "
               "প্রতিটি বিয়োগ চিহ্নে ধীরে চলুন।",
    "algebra:equation": "ভারসাম্য মনে রাখুন: এক পাশে যা করবেন, "
                        "অন্য পাশেও তাই। সবচেয়ে সাধারণ ভুল হলো "
                        "পদকে '=' চিহ্নের ওপারে নেওয়ার সময় "
                        "চিহ্নের ভুল — আপনার উত্তরটি মূল সমীকরণে "
                        "বসিয়ে সবসময় যাচাই করুন। অনুশীলনে এমন "
                        "আরও ২টি প্রশ্ন করুন।",
    "algebra:quadratic": "দ্বিঘাত সমীকরণে প্রথমে উৎপাদকে "
                         "বিশ্লেষণ চেষ্টা করুন; না হলে দ্বিঘাত "
                         "সূত্র সবসময় কাজ করে। সাধারণ ভুল: ± "
                         "ভুলে যাওয়া এবং b-এর চিহ্নের ভুল। "
                         "নিরূপক (b²−4ac) বলে দেয় কয়টি বাস্তব "
                         "মূল আসবে — শুরু করার আগে তা দেখে নিন।",
    "trigonometry": "মানক মানগুলি (0°, 30°, 45°, 60°, 90°-এর "
                    "sin/cos/tan) এতটাই অনুশীলন করুন যেন সেগুলি "
                    "নিজে থেকেই মনে থাকে। সাধারণ ভুল: sin ও cos "
                    "গুলিয়ে ফেলা, কিংবা ডিগ্রির প্রশ্নে রেডিয়ান "
                    "ব্যবহার করা।",
    "calculus": "মৌলিক নিয়মগুলির (ঘাত নিয়ম, শৃঙ্খল নিয়ম, মানক "
                "সমাকল) একটি ছোট তালিকা তৈরি করে প্রতি সপ্তাহে "
                "পুনরাবৃত্তি করুন — ক্যালকুলাস শেষ মুহূর্তের "
                "তাড়ায় নয়, নিয়মিত অনুশীলনে আসে।",
    "calculus:derivative": "ঘাত নিয়মটি মনে রাখুন: x^n-এর "
                           "অন্তরকলজ n·x^(n−1)। সাধারণ ভুল: "
                           "(2x+1)^3-এর মতো বন্ধনীতে শৃঙ্খল নিয়ম "
                           "ভুলে যাওয়া — প্রথমে বাইরের অন্তরকলজ, "
                           "তারপর ভেতরের অন্তরকলজ দিয়ে গুণ।",
    "calculus:integral": "সমাকলন হলো অন্তরকলনের উল্টো — আপনার "
                         "উত্তরকে অন্তরকলন করে প্রতিটি সমাকল "
                         "যাচাই করুন। সাধারণ ভুল: সমাকলন ধ্রুবক "
                         "(+C) ভুলে যাওয়া।",
    "calculus:definite_integral": "সমাকলন হলো অন্তরকলনের উল্টো — "
                                  "অনির্দিষ্ট সমাকলকে অন্তরকলন "
                                  "করে যাচাই করুন। তারপর ঊর্ধ্ব "
                                  "সীমা বিয়োগ নিম্ন সীমা "
                                  "সাবধানে বসান; চিহ্নের ভুল "
                                  "সেখানেই সবচেয়ে বেশি হয়।",
    "statistics": "প্রথমে ঠিক করুন কী চাওয়া হয়েছে — গড়, মধ্যক "
                  "ও প্রচুরক আলাদা হাতিয়ার। সাধারণ ভুল: যেখানে "
                  "মধ্যক (সাজানোর পর মাঝের মান) চাই, সেখানে গড় "
                  "বের করা।",
    "statistics:probability": "সম্ভাবনা = অনুকূল ফলাফল ÷ মোট "
                              "ফলাফল, এবং মোটে সম-সম্ভাব্য সব "
                              "ক্ষেত্র গুনতে হবে। সাধারণ ভুল: "
                              "দুটি পাশার যোগফলগুলিকে সম-সম্ভাব্য "
                              "ধরা — তারা তা নয়; জোড়গুলি লিখে "
                              "গুনুন।",
    "distributions": "স্বাভাবিক বণ্টনে প্রথমে z-স্কোর বের করুন "
                     "এবং বক্ররেখার ছবি আঁকুন — ছবিই বেশিরভাগ "
                     "ভুল আটকায়। সাধারণ ভুল: যেখানে প্রমাণ "
                     "বিচ্যুতি দরকার, সেখানে ভেদাঙ্ক ব্যবহার "
                     "করা।",
    "geometry": "প্রথমে সূত্র লিখুন, তারপর মান বসান — প্রতিটি "
                "সংখ্যার সঙ্গে একক রাখুন। সাধারণ ভুল: যেখানে "
                "সূত্রে ব্যাসার্ধ দরকার, সেখানে ব্যাস ব্যবহার "
                "করা।",
    "sequences": "সূত্র ছোঁয়ার আগে চিনুন এটি AP (সমান অন্তর) "
                 "নাকি GP (সমান অনুপাত)। সাধারণ ভুল: n-তম পদের "
                 "সূত্রে (n−1)-এর বদলে n ব্যবহার করা।",
}

_ADVICE_MR = {
    "generic": "प्रश्न दोनदा वाचा आणि जे विचारले आहे त्याखाली "
               "रेघ ओढा। सोडवल्यानंतर उत्तर प्रश्नात परत ठेवून "
               "तपासा — ही एकच सवय बहुतेक छोट्या चुका पकडते.",
    "arithmetic": "एका ओळीत एकच क्रिया करा आणि BODMAS क्रम "
                  "काटेकोरपणे पाळा। सामान्य चूक: ऋण संख्या वजा "
                  "करताना घाई — सवय होईपर्यंत ऋण संख्यांभोवती "
                  "कंस घाला.",
    "algebra": "प्रत्येक पायरी वेगळ्या ओळीत लिहा आणि समीकरण "
               "संतुलित ठेवा। बीजगणितातील बहुतेक गुण कठीण "
               "कल्पनांमुळे नाही, तर चिन्हांच्या छोट्या "
               "चुकांमुळे जातात — प्रत्येक वजाबाकीच्या "
               "चिन्हाजवळ सावकाश व्हा.",
    "algebra:equation": "संतुलन लक्षात ठेवा: एका बाजूला जे कराल "
                        "तेच दुसऱ्या बाजूलाही। सर्वात सामान्य चूक "
                        "म्हणजे पद '=' चिन्हाच्या पलीकडे नेताना "
                        "चिन्हाची चूक — तुमचे उत्तर मूळ समीकरणात "
                        "ठेवून नेहमी तपासा। सरावात अशी आणखी २ "
                        "उदाहरणे सोडवा.",
    "algebra:quadratic": "वर्ग समीकरणांमध्ये आधी अवयव पाडून "
                         "पाहा; जमले नाही तर वर्ग सूत्र नेहमी "
                         "काम करते। सामान्य चुका: ± विसरणे आणि "
                         "b च्या चिन्हाची चूक। विवेचक (b²−4ac) "
                         "किती वास्तव मुळे येतील ते सांगतो — "
                         "सुरुवात करण्याआधी तो पाहा.",
    "trigonometry": "प्रमाण मूल्ये (0°, 30°, 45°, 60°, 90° चे "
                    "sin/cos/tan) आपोआप आठवतील इतका सराव करा। "
                    "सामान्य चूक: sin आणि cos ची गल्लत, किंवा "
                    "अंशांच्या प्रश्नात रेडियन वापरणे.",
    "calculus": "मूलभूत नियमांची (घात नियम, साखळी नियम, प्रमाण "
                "समाकले) छोटी यादी करून दर आठवड्याला उजळणी "
                "करा — कॅल्क्युलस शेवटच्या क्षणाच्या गडबडीने "
                "नाही, तर नियमित सरावाने येते.",
    "calculus:derivative": "घात नियम लक्षात ठेवा: x^n चे विकलज "
                           "n·x^(n−1)। सामान्य चूक: (2x+1)^3 "
                           "सारख्या कंसांमध्ये साखळी नियम "
                           "विसरणे — आधी बाहेरचे विकलज, मग "
                           "आतल्या विकलजाने गुणा.",
    "calculus:integral": "समाकलन म्हणजे विकलनाची उलटी क्रिया — "
                         "तुमच्या उत्तराचे विकलज काढून प्रत्येक "
                         "समाकल तपासा। सामान्य चूक: समाकलन स्थिरांक "
                         "(+C) विसरणे.",
    "calculus:definite_integral": "समाकलन म्हणजे विकलनाची उलटी "
                                  "क्रिया — अनिश्चित समाकलाचे "
                                  "विकलज काढून ते तपासा। मग वरची "
                                  "मर्यादा वजा खालची मर्यादा "
                                  "काळजीपूर्वक ठेवा; चिन्हाची "
                                  "चूक तिथेच सर्वाधिक होते.",
    "statistics": "आधी ठरवा काय विचारले आहे — मध्य, मध्यक आणि "
                  "बहुलक ही वेगळी साधने आहेत। सामान्य चूक: जिथे "
                  "मध्यक (क्रम लावल्यानंतरचे मधले मूल्य) हवा "
                  "असतो तिथे मध्य काढणे.",
    "statistics:probability": "संभाव्यता = अनुकूल निष्पत्ती ÷ "
                              "एकूण निष्पत्ती, आणि एकूणमध्ये "
                              "सर्व समान-शक्य प्रकरणे मोजली "
                              "पाहिजेत। सामान्य चूक: दोन "
                              "फाशांच्या बेरजांना समान-शक्य मानणे "
                              "— त्या नसतात; जोड्या लिहून मोजा.",
    "distributions": "सामान्य वितरणात आधी z-गुण काढा आणि "
                     "वक्राची आकृती अवश्य काढा — आकृती "
                     "बहुतेक चुका टाळते। सामान्य चूक: जिथे "
                     "प्रमाण विचलन हवे तिथे प्रसरण वापरणे.",
    "geometry": "आधी सूत्र लिहा, मग किमती ठेवा — आणि प्रत्येक "
                "संख्येसोबत एकक ठेवा। सामान्य चूक: सूत्रात "
                "त्रिज्या हवी असताना व्यास वापरणे.",
    "sequences": "सूत्राला हात लावण्याआधी ओळखा की ही AP आहे "
                 "(समान फरक) की GP (समान गुणोत्तर)। सामान्य "
                 "चूक: n व्या पदाच्या सूत्रात (n−1) ऐवजी n "
                 "वापरणे.",
}

ADVICE["bn"] = _ADVICE_BN
ADVICE["mr"] = _ADVICE_MR

_ADVICE_TA = {
    "generic": "கேள்வியை இருமுறை படித்து, என்ன கேட்கப்படுகிறது "
               "என்பதை அடிக்கோடிடுங்கள். தீர்த்த பின் உங்கள் "
               "விடையைக் கேள்வியில் மீண்டும் இட்டுச் "
               "சரிபாருங்கள் — இந்த ஒரு பழக்கமே பெரும்பாலான "
               "சிறு தவறுகளைப் பிடிக்கும்.",
    "arithmetic": "ஒரு வரியில் ஒரு செயலை மட்டும் செய்து "
                  "BODMAS வரிசையைக் கடுமையாகப் பின்பற்றுங்கள். "
                  "பொதுவான தவறு: எதிர்மறை எண்ணைக் "
                  "கழிக்கும்போது அவசரம் — பழக்கமாகும் வரை "
                  "எதிர்மறை எண்களை அடைப்புக்குள் வைக்கவும்.",
    "algebra": "ஒவ்வொரு படியையும் தனி வரியில் எழுதி "
               "சமன்பாட்டைச் சமநிலையில் வைக்கவும். இயற்கணித "
               "மதிப்பெண்கள் பெரும்பாலும் கடினமான கருத்துகளால் "
               "அல்ல, குறியீட்டுச் சிறு பிழைகளால் "
               "இழக்கப்படுகின்றன — ஒவ்வொரு கழித்தல் "
               "குறியிடமும் மெதுவாகச் செல்லுங்கள்.",
    "algebra:equation": "சமநிலையை நினைவில் கொள்ளுங்கள்: ஒரு "
                        "பக்கத்தில் என்ன செய்கிறீர்களோ அதையே "
                        "மறு பக்கத்திலும் செய்யுங்கள். மிகப் "
                        "பொதுவான தவறு, உறுப்பை '=' குறியின் "
                        "மறுபுறம் கொண்டு செல்லும்போது ஏற்படும் "
                        "குறியீட்டுப் பிழை — உங்கள் விடையை "
                        "மூலச் சமன்பாட்டில் இட்டு எப்போதும் "
                        "சரிபாருங்கள். பயிற்சியில் இது போல் "
                        "மேலும் 2 கேள்விகளை முயற்சிக்கவும்.",
    "algebra:quadratic": "இருபடிச் சமன்பாடுகளில் முதலில் "
                         "காரணிப்படுத்திப் பாருங்கள்; "
                         "முடியாவிட்டால் இருபடி சூத்திரம் "
                         "எப்போதும் வேலை செய்யும். பொதுவான "
                         "தவறுகள்: ± ஐ மறப்பது மற்றும் b இன் "
                         "குறியீட்டுப் பிழை. பிரித்தறிவான் "
                         "(b²−4ac) எத்தனை மெய் மூலங்கள் வரும் "
                         "என்பதைச் சொல்லும் — தொடங்குவதற்கு "
                         "முன் அதைப் பாருங்கள்.",
    "trigonometry": "நிலையான மதிப்புகளை (0°, 30°, 45°, 60°, "
                    "90° இன் sin/cos/tan) தானாகவே நினைவுக்கு "
                    "வரும் அளவுக்குப் பயிற்சி செய்யுங்கள். "
                    "பொதுவான தவறு: sin மற்றும் cos ஐக் "
                    "குழப்புவது, அல்லது டிகிரி கேள்வியில் "
                    "ரேடியனைப் பயன்படுத்துவது.",
    "calculus": "அடிப்படை விதிகளை (அடுக்கு விதி, சங்கிலி விதி, "
                "நிலையான தொகையீடுகள்) சிறு அட்டவணையாக்கி "
                "வாரந்தோறும் மீள்பார்வை செய்யுங்கள் — "
                "கால்குலஸ் கடைசி நிமிட அவசரத்தால் அல்ல, "
                "தொடர் பயிற்சியால் வரும்.",
    "calculus:derivative": "அடுக்கு விதியை நினைவில் "
                           "கொள்ளுங்கள்: x^n இன் வகைக்கெழு "
                           "n·x^(n−1). பொதுவான தவறு: (2x+1)^3 "
                           "போன்ற அடைப்புகளில் சங்கிலி விதியை "
                           "மறப்பது — முதலில் வெளிப்புறத்தின் "
                           "வகைக்கெழு, பின் உட்புறத்தின் "
                           "வகைக்கெழுவால் பெருக்கவும்.",
    "calculus:integral": "தொகையீடு என்பது வகையீட்டின் "
                         "எதிர்மறை — உங்கள் விடையை வகைக்கெழு "
                         "எடுத்து ஒவ்வொரு தொகையீட்டையும் "
                         "சரிபாருங்கள். பொதுவான தவறு: தொகையீட்டு "
                         "மாறிலியை (+C) மறப்பது.",
    "calculus:definite_integral": "தொகையீடு என்பது வகையீட்டின் "
                                  "எதிர்மறை — வரையறா "
                                  "தொகையீட்டை வகைக்கெழு எடுத்து "
                                  "சரிபாருங்கள். பின் மேல் "
                                  "எல்லை கழித்தல் கீழ் எல்லையை "
                                  "கவனமாக இடுங்கள்; குறியீட்டுப் "
                                  "பிழை அங்கேயே அதிகம் "
                                  "நடக்கும்.",
    "statistics": "முதலில் என்ன கேட்கப்படுகிறது என்பதை "
                  "முடிவு செய்யுங்கள் — சராசரி, இடைநிலை, "
                  "ஆகாரம் வெவ்வேறு கருவிகள். பொதுவான தவறு: "
                  "இடைநிலை (வரிசைப்படுத்திய பின் நடு மதிப்பு) "
                  "வேண்டிய இடத்தில் சராசரியைக் கணக்கிடுவது.",
    "statistics:probability": "நிகழ்தகவு = சாதகமான விளைவுகள் ÷ "
                              "மொத்த விளைவுகள், மொத்தத்தில் சம "
                              "வாய்ப்புள்ள எல்லா நிகழ்வுகளும் "
                              "எண்ணப்பட வேண்டும். பொதுவான "
                              "தவறு: இரு பகடைகளின் "
                              "கூட்டுத்தொகைகளை சம வாய்ப்புள்ளவை "
                              "எனக் கருதுவது — அவை அப்படியல்ல; "
                              "இணைகளை எழுதி எண்ணுங்கள்.",
    "distributions": "இயல்புப் பரவலில் முதலில் z-மதிப்பெண்ணாக "
                     "மாற்றி வளைவரையின் படத்தை வரையுங்கள் — "
                     "படமே பெரும்பாலான பிழைகளைத் தடுக்கும். "
                     "பொதுவான தவறு: நிலையான விலக்கம் வேண்டிய "
                     "இடத்தில் மாறுபாட்டைப் பயன்படுத்துவது.",
    "geometry": "முதலில் சூத்திரத்தை எழுதி, பின் மதிப்புகளை "
                "இடுங்கள் — ஒவ்வொரு எண்ணுடனும் அலகையும் "
                "வைக்கவும். பொதுவான தவறு: சூத்திரத்தில் ஆரம் "
                "வேண்டிய இடத்தில் விட்டத்தைப் பயன்படுத்துவது.",
    "sequences": "சூத்திரத்தைத் தொடுவதற்கு முன் அது AP (சம "
                 "வித்தியாசம்) அல்லது GP (சம விகிதம்) என்பதை "
                 "அடையாளம் காணுங்கள். பொதுவான தவறு: n-ஆம் "
                 "உறுப்பு சூத்திரத்தில் (n−1) க்குப் பதில் n "
                 "ஐப் பயன்படுத்துவது.",
}

_ADVICE_TE = {
    "generic": "ప్రశ్నను రెండుసార్లు చదివి, ఏమి అడుగుతున్నారో "
               "దాని కింద గీత గీయండి. పరిష్కరించిన తరువాత మీ "
               "సమాధానాన్ని ప్రశ్నలో తిరిగి ఉంచి పరీక్షించండి "
               "— ఈ ఒక్క అలవాటే చాలా చిన్న తప్పులను "
               "పట్టుకుంటుంది.",
    "arithmetic": "ఒక వరుసలో ఒకే క్రియ చేసి BODMAS క్రమాన్ని "
                  "కఠినంగా పాటించండి. సాధారణ తప్పు: రుణ "
                  "సంఖ్యను తీసివేసేటప్పుడు తొందర — అలవాటయ్యే "
                  "వరకు రుణ సంఖ్యల చుట్టూ బ్రాకెట్లు వేయండి.",
    "algebra": "ప్రతి దశను ప్రత్యేక వరుసలో రాసి సమీకరణాన్ని "
               "సమతుల్యంగా ఉంచండి. బీజగణిత మార్కులు ఎక్కువగా "
               "కఠినమైన ఆలోచనల వల్ల కాక, గుర్తుల చిన్న "
               "పొరపాట్ల వల్లే పోతాయి — ప్రతి మైనస్ గుర్తు "
               "దగ్గర నెమ్మదిగా వెళ్లండి.",
    "algebra:equation": "సమతుల్యతను గుర్తుంచుకోండి: ఒక వైపు "
                        "ఏది చేస్తారో అదే మరో వైపు కూడా "
                        "చేయండి. అత్యంత సాధారణ తప్పు, పదాన్ని "
                        "'=' గుర్తుకు అవతలికి తీసుకెళ్లేటప్పుడు "
                        "గుర్తు పొరపాటు — మీ సమాధానాన్ని అసలు "
                        "సమీకరణంలో ఉంచి ఎప్పుడూ పరీక్షించండి. "
                        "సాధనలో ఇలాంటివి మరో 2 ప్రయత్నించండి.",
    "algebra:quadratic": "వర్గ సమీకరణాల్లో ముందు కారణాంకాలుగా "
                         "విడగొట్టి చూడండి; కుదరకపోతే వర్గ "
                         "సూత్రం ఎప్పుడూ పనిచేస్తుంది. సాధారణ "
                         "తప్పులు: ± ను మరచిపోవడం మరియు b గుర్తు "
                         "పొరపాటు. విచక్షణి (b²−4ac) ఎన్ని "
                         "వాస్తవ మూలాలు వస్తాయో చెబుతుంది — "
                         "మొదలుపెట్టే ముందు దాన్ని చూడండి.",
    "trigonometry": "ప్రామాణిక విలువలను (0°, 30°, 45°, 60°, "
                    "90° ల sin/cos/tan) అవి స్వయంచాలకంగా "
                    "గుర్తుకు వచ్చేంతగా సాధన చేయండి. సాధారణ "
                    "తప్పు: sin మరియు cos లను కలగలపడం, లేదా "
                    "డిగ్రీల ప్రశ్నలో రేడియన్లు వాడటం.",
    "calculus": "ప్రాథమిక నియమాలను (ఘాత నియమం, శృంఖల నియమం, "
                "ప్రామాణిక సమాకలనులు) చిన్న పట్టికగా చేసి "
                "ప్రతి వారం పునరావృతం చేయండి — కాల్కులస్ "
                "చివరి నిమిషపు హడావుడితో కాక, క్రమ సాధనతో "
                "వస్తుంది.",
    "calculus:derivative": "ఘాత నియమాన్ని గుర్తుంచుకోండి: x^n "
                           "యొక్క అవకలజం n·x^(n−1). సాధారణ "
                           "తప్పు: (2x+1)^3 వంటి బ్రాకెట్లలో "
                           "శృంఖల నియమాన్ని మరచిపోవడం — "
                           "ముందు బయటి అవకలజం, తరువాత లోపలి "
                           "అవకలజంతో గుణించండి.",
    "calculus:integral": "సమాకలనం అంటే అవకలనానికి వ్యతిరేకం — "
                         "మీ సమాధానాన్ని అవకలజం చేసి ప్రతి "
                         "సమాకలనిని పరీక్షించండి. సాధారణ "
                         "తప్పు: సమాకలన స్థిరాంకాన్ని (+C) "
                         "మరచిపోవడం.",
    "calculus:definite_integral": "సమాకలనం అంటే అవకలనానికి "
                                  "వ్యతిరేకం — అనిశ్చిత "
                                  "సమాకలనిని అవకలజం చేసి "
                                  "పరీక్షించండి. తరువాత పై "
                                  "హద్దు మైనస్ కింది హద్దును "
                                  "జాగ్రత్తగా ఉంచండి; గుర్తు "
                                  "పొరపాటు అక్కడే ఎక్కువగా "
                                  "జరుగుతుంది.",
    "statistics": "ముందు ఏమి అడుగుతున్నారో నిర్ణయించండి — "
                  "సగటు, మధ్యగతం, బాహుళ్యం వేర్వేరు సాధనాలు. "
                  "సాధారణ తప్పు: మధ్యగతం (క్రమంలో పెట్టిన "
                  "తరువాత మధ్య విలువ) కావలసిన చోట సగటును "
                  "లెక్కించడం.",
    "statistics:probability": "సంభావ్యత = అనుకూల ఫలితాలు ÷ "
                              "మొత్తం ఫలితాలు, మొత్తంలో సమాన "
                              "అవకాశం ఉన్న అన్ని సందర్భాలను "
                              "లెక్కించాలి. సాధారణ తప్పు: రెండు "
                              "పాచికల మొత్తాలను సమాన అవకాశం "
                              "ఉన్నవిగా భావించడం — అవి అలా కావు; "
                              "జతలను రాసి లెక్కించండి.",
    "distributions": "సాధారణ పంపిణీలో ముందు z-స్కోరుగా మార్చి "
                     "వక్రరేఖ చిత్రాన్ని తప్పకుండా గీయండి — "
                     "చిత్రమే చాలా తప్పులను ఆపుతుంది. సాధారణ "
                     "తప్పు: ప్రామాణిక విచలనం కావలసిన చోట "
                     "విస్తృతిని వాడటం.",
    "geometry": "ముందు సూత్రాన్ని రాయండి, తరువాత విలువలు "
                "ఉంచండి — ప్రతి సంఖ్యతో పాటు ప్రమాణాన్ని "
                "కూడా ఉంచండి. సాధారణ తప్పు: సూత్రంలో "
                "వ్యాసార్థం కావలసిన చోట వ్యాసాన్ని వాడటం.",
    "sequences": "సూత్రాన్ని తాకే ముందు అది AP (సమాన భేదం) "
                 "లేక GP (సమాన నిష్పత్తి) అనేది గుర్తించండి. "
                 "సాధారణ తప్పు: nవ పద సూత్రంలో (n−1) కు "
                 "బదులు n ను వాడటం.",
}

ADVICE["ta"] = _ADVICE_TA
ADVICE["te"] = _ADVICE_TE


def advice_for(result, lang):
    """The curated teacher's-advice line for a solver result dict.

    Fallback chain: "type:op" -> (algebra equations whose steps use
    the discriminant/quadratic formula -> "algebra:quadratic") ->
    "type" -> English equivalents -> "generic". Never raises.
    """
    table = ADVICE.get(lang) or ADVICE["en"]
    fallback = ADVICE["en"]
    result = result or {}
    rtype = result.get("type", "") or ""
    rop = result.get("op", "") or ""
    key = f"{rtype}:{rop}"
    if key == "algebra:equation":
        steps_text = " ".join(result.get("steps") or []).lower()
        if "discriminant" in steps_text or "quadratic" in steps_text:
            key = "algebra:quadratic"
    return (table.get(key) or table.get(rtype)
            or fallback.get(key) or fallback.get(rtype)
            or table.get("generic") or fallback["generic"])


# ---------------------------------------------------------------------------
# Wave 5b UI strings: Teacher's Advice headings, the Listen button,
# and the rotating Advice of the Day (7 tips, one per weekday cycle).
# ---------------------------------------------------------------------------

_EN_W5B = {
    "advice_heading": "👩‍🏫 Teacher's Advice",
    "advice_day_heading": "👩‍🏫 Teacher's Advice of the Day",
    "listen_btn": "🔊 Listen",
    "tip_day_0": "Revise a little every day — 20 focused minutes "
                 "beat 3 hours the night before an exam.",
    "tip_day_1": "Keep a mistake notebook: write every question you "
                 "got wrong and redo it after two days.",
    "tip_day_2": "Always check your answer by putting it back into "
                 "the question.",
    "tip_day_3": "Draw the diagram. Half of geometry and "
                 "trigonometry becomes easy once the picture is on "
                 "paper.",
    "tip_day_4": "Learn formulas by using them: solve two questions "
                 "right after learning any new formula.",
    "tip_day_5": "In the exam, attempt the questions you know first "
                 "and mark the hard ones for later.",
    "tip_day_6": "Write every step — in board exams, correct steps "
                 "earn marks even if the final answer slips.",
}

_HI_W5B = {
    "advice_heading": "👩‍🏫 शिक्षक की सलाह",
    "advice_day_heading": "👩‍🏫 आज की शिक्षक सलाह",
    "listen_btn": "🔊 सुनिए",
    "tip_day_0": "रोज़ थोड़ा-थोड़ा दोहराइए — परीक्षा से पहली रात "
                 "के 3 घंटे से 20 मिनट का नियमित अभ्यास बेहतर "
                 "है।",
    "tip_day_1": "ग़लतियों की नोटबुक रखिए: जो प्रश्न ग़लत हो उसे "
                 "लिखिए और दो दिन बाद फिर हल कीजिए।",
    "tip_day_2": "अपना उत्तर हमेशा प्रश्न में वापस रखकर जाँचिए।",
    "tip_day_3": "चित्र बनाइए। ज्यामिति और त्रिकोणमिति का आधा "
                 "हिस्सा काग़ज़ पर चित्र बनते ही आसान हो जाता "
                 "है।",
    "tip_day_4": "सूत्र उन्हें इस्तेमाल करके सीखिए: नया सूत्र "
                 "सीखते ही तुरंत दो प्रश्न हल कीजिए।",
    "tip_day_5": "परीक्षा में पहले वे प्रश्न कीजिए जो आते हैं, "
                 "कठिन प्रश्नों को बाद के लिए चिह्नित कीजिए।",
    "tip_day_6": "हर चरण लिखिए — बोर्ड परीक्षा में अंतिम उत्तर "
                 "फिसल भी जाए तो सही चरणों के अंक मिलते हैं।",
}

_BN_W5B = {
    "advice_heading": "👩‍🏫 শিক্ষকের পরামর্শ",
    "advice_day_heading": "👩‍🏫 আজকের শিক্ষকের পরামর্শ",
    "listen_btn": "🔊 শুনুন",
    "tip_day_0": "রোজ অল্প অল্প করে পুনরাবৃত্তি করুন — পরীক্ষার "
                 "আগের রাতের ৩ ঘণ্টার চেয়ে ২০ মিনিটের নিয়মিত "
                 "অনুশীলন ভালো।",
    "tip_day_1": "ভুলের খাতা রাখুন: যে প্রশ্ন ভুল হবে তা লিখে "
                 "রাখুন এবং দুদিন পরে আবার করুন।",
    "tip_day_2": "আপনার উত্তর সর্বদা প্রশ্নে ফিরিয়ে বসিয়ে "
                 "যাচাই করুন।",
    "tip_day_3": "ছবি আঁকুন। কাগজে ছবি আঁকলেই জ্যামিতি ও "
                 "ত্রিকোণমিতির অর্ধেক সহজ হয়ে যায়।",
    "tip_day_4": "সূত্র ব্যবহার করে শিখুন: নতুন সূত্র শেখার "
                 "সঙ্গে সঙ্গে দুটি প্রশ্ন সমাধান করুন।",
    "tip_day_5": "পরীক্ষায় প্রথমে জানা প্রশ্নগুলি করুন এবং "
                 "কঠিনগুলি পরে করার জন্য চিহ্নিত রাখুন।",
    "tip_day_6": "প্রতিটি ধাপ লিখুন — বোর্ড পরীক্ষায় শেষ উত্তর "
                 "ভুল হলেও সঠিক ধাপের জন্য নম্বর মেলে।",
}

_MR_W5B = {
    "advice_heading": "👩‍🏫 शिक्षकांचा सल्ला",
    "advice_day_heading": "👩‍🏫 आजचा शिक्षकांचा सल्ला",
    "listen_btn": "🔊 ऐका",
    "tip_day_0": "रोज थोडा थोडा अभ्यास करा — परीक्षेच्या आदल्या "
                 "रात्रीच्या ३ तासांपेक्षा २० मिनिटांचा नियमित "
                 "सराव चांगला.",
    "tip_day_1": "चुकांची वही ठेवा: जे उदाहरण चुकेल ते लिहा आणि "
                 "दोन दिवसांनी पुन्हा सोडवा.",
    "tip_day_2": "तुमचे उत्तर नेहमी प्रश्नात परत ठेवून तपासा.",
    "tip_day_3": "आकृती काढा। कागदावर आकृती आली की भूमिती आणि "
                 "त्रिकोणमितीचा अर्धा भाग सोपा होतो.",
    "tip_day_4": "सूत्रे वापरून शिका: नवीन सूत्र शिकताच लगेच "
                 "दोन उदाहरणे सोडवा.",
    "tip_day_5": "परीक्षेत आधी येत असलेली उदाहरणे सोडवा आणि "
                 "कठीण उदाहरणे नंतरसाठी चिन्हांकित करा.",
    "tip_day_6": "प्रत्येक पायरी लिहा — बोर्ड परीक्षेत अंतिम "
                 "उत्तर चुकले तरी बरोबर पायऱ्यांना गुण मिळतात.",
}

_TA_W5B = {
    "advice_heading": "👩‍🏫 ஆசிரியரின் அறிவுரை",
    "advice_day_heading": "👩‍🏫 இன்றைய ஆசிரியர் அறிவுரை",
    "listen_btn": "🔊 கேளுங்கள்",
    "tip_day_0": "தினமும் கொஞ்சம் கொஞ்சமாக மீள்பார்வை "
                 "செய்யுங்கள் — தேர்வுக்கு முந்தைய இரவின் 3 "
                 "மணி நேரத்தை விட 20 நிமிட தொடர் பயிற்சி "
                 "சிறந்தது.",
    "tip_day_1": "தவறுகள் குறிப்பேட்டை வைத்திருங்கள்: "
                 "தவறவிட்ட கேள்வியை எழுதி, இரண்டு "
                 "நாட்களுக்குப் பின் மீண்டும் செய்யுங்கள்.",
    "tip_day_2": "உங்கள் விடையை எப்போதும் கேள்வியில் மீண்டும் "
                 "இட்டுச் சரிபாருங்கள்.",
    "tip_day_3": "படத்தை வரையுங்கள். வடிவியல் மற்றும் "
                 "முக்கோணவியலின் பாதி, காகிதத்தில் படம் "
                 "வந்ததுமே எளிதாகிவிடும்.",
    "tip_day_4": "சூத்திரங்களைப் பயன்படுத்திக் கற்றுக் "
                 "கொள்ளுங்கள்: புதிய சூத்திரத்தைக் கற்ற உடனே "
                 "இரண்டு கேள்விகளைத் தீர்க்கவும்.",
    "tip_day_5": "தேர்வில் முதலில் தெரிந்த கேள்விகளை "
                 "முயற்சித்து, கடினமானவற்றைப் பின்னர் செய்யக் "
                 "குறித்து வைக்கவும்.",
    "tip_day_6": "ஒவ்வொரு படியையும் எழுதுங்கள் — போர்டு "
                 "தேர்வுகளில் இறுதி விடை தவறினாலும் சரியான "
                 "படிகளுக்கு மதிப்பெண் கிடைக்கும்.",
}

_TE_W5B = {
    "advice_heading": "👩‍🏫 గురువు సలహా",
    "advice_day_heading": "👩‍🏫 ఈ రోజు గురువు సలహా",
    "listen_btn": "🔊 వినండి",
    "tip_day_0": "రోజూ కొంచెం కొంచెంగా పునరావృతం చేయండి — "
                 "పరీక్షకు ముందు రాత్రి 3 గంటల కంటే 20 నిమిషాల "
                 "క్రమ సాధన మేలు.",
    "tip_day_1": "తప్పుల నోట్‌బుక్ ఉంచండి: తప్పు చేసిన "
                 "ప్రశ్నను రాసి, రెండు రోజుల తరువాత మళ్లీ "
                 "చేయండి.",
    "tip_day_2": "మీ సమాధానాన్ని ఎప్పుడూ ప్రశ్నలో తిరిగి ఉంచి "
                 "పరీక్షించండి.",
    "tip_day_3": "చిత్రాన్ని గీయండి. కాగితంపై చిత్రం వస్తే "
                 "జ్యామితి మరియు త్రికోణమితిలో సగం "
                 "సులభమవుతుంది.",
    "tip_day_4": "సూత్రాలను వాడుతూ నేర్చుకోండి: కొత్త సూత్రం "
                 "నేర్చుకున్న వెంటనే రెండు ప్రశ్నలు "
                 "పరిష్కరించండి.",
    "tip_day_5": "పరీక్షలో ముందు తెలిసిన ప్రశ్నలను "
                 "ప్రయత్నించి, కఠినమైన వాటిని తరువాత కోసం "
                 "గుర్తు పెట్టండి.",
    "tip_day_6": "ప్రతి దశను రాయండి — బోర్డు పరీక్షల్లో తుది "
                 "సమాధానం తప్పినా సరైన దశలకు మార్కులు "
                 "వస్తాయి.",
}

STRINGS["en"].update(_EN_W5B)
STRINGS["hi"].update(_HI_W5B)
STRINGS["bn"].update(_BN_W5B)
STRINGS["mr"].update(_MR_W5B)
STRINGS["ta"].update(_TA_W5B)
STRINGS["te"].update(_TE_W5B)


# Wave 5c: stop label for the step-by-step Suno (Listen) control.
_STRINGS_STOP = {
    "en": "⏸ Stop",
    "hi": "⏸ रुकिए",
    "bn": "⏸ থামুন",
    "mr": "⏸ थांबा",
    "ta": "⏸ நிறுத்துங்கள்",
    "te": "⏸ ఆపండి",
}
for _code, _label in _STRINGS_STOP.items():
    STRINGS[_code]["listen_stop_btn"] = _label


# ---------------------------------------------------------------------------
# Wave 5b: student-proofing strings — friendly solve errors (no raw
# error text ever), the chat slow-server note, the too-long note, the
# photo no-text message and the generic "no questions here yet" empty
# state. Same completeness rule as every wave: every key exists in
# all 6 languages (get_strings() also falls back to English).
# ---------------------------------------------------------------------------

_EN_W5C = {
    "error_heading": "🤔 Hmm, I couldn't solve this one",
    "error_intro": "No problem — this can happen when the question is "
                   "unclear or in a form I don't recognise yet. "
                   "Try once more like this:",
    "error_tip1": "Check the question once for any typing mistake.",
    "error_tip2": "Write powers like this: x^2 (not x2 or x²).",
    "error_tip3": "Ask one question at a time, with all its numbers.",
    "error_retry_btn": "↻ Try again",
    "try_again_link": "✏️ Ask again",
    "chat_waking_note": "⏳ The first answer can take a little time — "
                        "the free server wakes up. Please wait a "
                        "moment.",
    "flash_too_long": "That question is a bit long — please keep it "
                      "under about 500 characters and ask one part at "
                      "a time.",
    "photo_no_text": "📷 I couldn't read any text in that photo. "
                     "Please pick a clearer photo of the question.",
    "empty_no_questions": "No questions here yet — check back in a "
                          "moment.",
}

_HI_W5C = {
    "error_heading": "🤔 हम्म, यह प्रश्न हल नहीं हो पाया",
    "error_intro": "कोई बात नहीं — ऐसा तब होता है जब प्रश्न स्पष्ट "
                   "न हो या ऐसे रूप में हो जिसे मैं अभी पहचान "
                   "नहीं पाया। एक बार ऐसे आज़माएँ:",
    "error_tip1": "प्रश्न को एक बार ध्यान से देखें — कोई लिखने की "
                  "ग़लती तो नहीं।",
    "error_tip2": "घात इस तरह लिखें: x^2 (x2 या x² नहीं)।",
    "error_tip3": "एक बार में एक ही प्रश्न पूछें, सारे अंकों के साथ।",
    "error_retry_btn": "↻ फिर से कोशिश करें",
    "try_again_link": "✏️ फिर से पूछें",
    "chat_waking_note": "⏳ पहला उत्तर आने में थोड़ा समय लग सकता है — "
                        "मुफ़्त सर्वर जागता है। कृपया थोड़ा "
                        "रुकें।",
    "flash_too_long": "यह प्रश्न थोड़ा लंबा है — कृपया इसे लगभग 500 "
                      "अक्षरों से छोटा रखें और एक बार में एक भाग "
                      "पूछें।",
    "photo_no_text": "📷 इस फ़ोटो में कोई प्रश्न नहीं पढ़ा जा सका। "
                     "कृपया प्रश्न की साफ़ फ़ोटो चुनें।",
    "empty_no_questions": "यहाँ अभी कोई प्रश्न नहीं है — थोड़ी देर "
                          "में फिर देखें।",
}

_BN_W5C = {
    "error_heading": "🤔 হুম, এই প্রশ্নটি সমাধান করা গেল না",
    "error_intro": "কোনো সমস্যা নেই — প্রশ্নটি অস্পষ্ট হলে বা আমি "
                   "এখনও চিনতে পারি না এমন আকারে থাকলে এমন হয়। "
                   "আরেকবার এভাবে চেষ্টা করুন:",
    "error_tip1": "প্রশ্নটি একবার দেখে নিন — কোনো লেখার ভুল আছে "
                  "কিনা।",
    "error_tip2": "ঘাত এভাবে লিখুন: x^2 (x2 বা x² নয়)।",
    "error_tip3": "একবারে একটি প্রশ্নই করুন, সব সংখ্যাসহ।",
    "error_retry_btn": "↻ আবার চেষ্টা করুন",
    "try_again_link": "✏️ আবার জিজ্ঞাসা করুন",
    "chat_waking_note": "⏳ প্রথম উত্তরে একটু সময় লাগতে পারে — "
                        "ফ্রি সার্ভার জেগে ওঠে। একটু অপেক্ষা "
                        "করুন।",
    "flash_too_long": "এই প্রশ্নটি একটু লম্বা — অনুগ্রহ করে এটি "
                      "প্রায় 500 অক্ষরের মধ্যে রাখুন এবং একবারে "
                      "একটি অংশ জিজ্ঞাসা করুন।",
    "photo_no_text": "📷 এই ছবিতে কোনো লেখা পড়া গেল না। অনুগ্রহ করে "
                     "প্রশ্নের আরও পরিষ্কার ছবি বেছে নিন।",
    "empty_no_questions": "এখানে এখনও কোনো প্রশ্ন নেই — একটু পরে আবার "
                          "দেখুন।",
}

_MR_W5C = {
    "error_heading": "🤔 हं, हा प्रश्न सोडवता आला नाही",
    "error_intro": "काही हरकत नाही — प्रश्न स्पष्ट नसल्यास किंवा मी "
                   "अजून ओळखत नाही अशा रूपात असल्यास असं होतं. "
                   "एकदा असा प्रयत्न करा:",
    "error_tip1": "प्रश्न एकदा नीट पाहा — लिहिताना काही चूक झाली "
                  "आहे का.",
    "error_tip2": "घात असा लिहा: x^2 (x2 किंवा x² नाही).",
    "error_tip3": "एकावेळी एकच प्रश्न विचारा, सर्व संख्यांसह.",
    "error_retry_btn": "↻ पुन्हा प्रयत्न करा",
    "try_again_link": "✏️ पुन्हा विचारा",
    "chat_waking_note": "⏳ पहिल्या उत्तराला थोडा वेळ लागू शकतो — "
                        "मोफत सर्व्हर जागा होतो. कृपया थोडं "
                        "थांबा.",
    "flash_too_long": "हा प्रश्न थोडा लांब आहे — कृपया तो सुमारे 500 "
                      "अक्षरांपेक्षा कमी ठेवा आणि एकावेळी एक भाग "
                      "विचारा.",
    "photo_no_text": "📷 या फोटोत काही मजकूर वाचता आला नाही. कृपया "
                     "प्रश्नाचा अधिक स्पष्ट फोटो निवडा.",
    "empty_no_questions": "इथे अजून एकही प्रश्न नाही — थोड्या वेळाने "
                          "पुन्हा पाहा.",
}

_TA_W5C = {
    "error_heading": "🤔 ம்ம், இந்த கேள்வியை தீர்க்க முடியவில்லை",
    "error_intro": "பரவாயில்லை — கேள்வி தெளிவில்லாமல் இருந்தாலோ, "
                   "நான் இன்னும் அடையாளம் காணாத வடிவில் இருந்தாலோ "
                   "இப்படி நடக்கும். இப்படி மீண்டும் முயற்சிக்கவும்:",
    "error_tip1": "கேள்வியை ஒருமுறை சரிபார்க்கவும் — தட்டச்சுப் "
                  "பிழை உள்ளதா என்று.",
    "error_tip2": "அடுக்குகளை இப்படி எழுதவும்: x^2 (x2 அல்லது x² "
                  "அல்ல).",
    "error_tip3": "ஒரு நேரத்தில் ஒரு கேள்வி மட்டும், எல்லா "
                  "எண்களுடன் கேட்கவும்.",
    "error_retry_btn": "↻ மீண்டும் முயற்சிக்கவும்",
    "try_again_link": "✏️ மீண்டும் கேட்கவும்",
    "chat_waking_note": "⏳ முதல் பதில் வர சிறிது நேரம் ஆகலாம் — "
                        "இலவச சர்வர் விழித்தெழுகிறது. சற்று "
                        "காத்திருக்கவும்.",
    "flash_too_long": "இந்த கேள்வி சற்று நீளமானது — சுமார் 500 "
                      "எழுத்துகளுக்குள் வைத்து, ஒரு நேரத்தில் ஒரு "
                      "பகுதியைக் கேட்கவும்.",
    "photo_no_text": "📷 இந்த புகைப்படத்தில் எந்த உரையும் படிக்க "
                     "முடியவில்லை. கேள்வியின் தெளிவான புகைப்படத்தைத் "
                     "தேர்ந்தெடுக்கவும்.",
    "empty_no_questions": "இங்கே இன்னும் கேள்விகள் இல்லை — சற்று "
                          "நேரத்தில் மீண்டும் பார்க்கவும்.",
}

_TE_W5C = {
    "error_heading": "🤔 హ్మ్, ఈ ప్రశ్నను పరిష్కరించలేకపోయాను",
    "error_intro": "పర్వాలేదు — ప్రశ్న స్పష్టంగా లేకపోతే లేదా నేను "
                   "ఇంకా గుర్తించని రూపంలో ఉంటే ఇలా జరుగుతుంది. "
                   "ఇలా మళ్ళీ ప్రయత్నించండి:",
    "error_tip1": "ప్రశ్నను ఒక్కసారి సరిచూడండి — టైపింగ్ పొరపాటు "
                  "ఉందేమో.",
    "error_tip2": "ఘాతాలను ఇలా రాయండి: x^2 (x2 లేదా x² కాదు).",
    "error_tip3": "ఒకసారి ఒకే ప్రశ్న, అన్ని సంఖ్యలతో అడగండి.",
    "error_retry_btn": "↻ మళ్ళీ ప్రయత్నించండి",
    "try_again_link": "✏️ మళ్ళీ అడగండి",
    "chat_waking_note": "⏳ మొదటి సమాధానం రావడానికి కొంచెం సమయం "
                        "పట్టవచ్చు — ఉచిత సర్వర్ మేల్కొంటుంది. "
                        "కొంచెం వేచి ఉండండి.",
    "flash_too_long": "ఈ ప్రశ్న కొంచెం పొడవుగా ఉంది — దయచేసి దీన్ని "
                      "సుమారు 500 అక్షరాల్లోపు ఉంచి, ఒకసారి ఒక "
                      "భాగాన్ని అడగండి.",
    "photo_no_text": "📷 ఈ ఫోటోలో ఏ వచనమూ చదవలేకపోయాను. దయచేసి "
                     "ప్రశ్న యొక్క స్పష్టమైన ఫోటోను ఎంచుకోండి.",
    "empty_no_questions": "ఇక్కడ ఇంకా ప్రశ్నలు లేవు — కొంచెం సేపట్లో "
                          "మళ్ళీ చూడండి.",
}

STRINGS["en"].update(_EN_W5C)
STRINGS["hi"].update(_HI_W5C)
STRINGS["bn"].update(_BN_W5C)
STRINGS["mr"].update(_MR_W5C)
STRINGS["ta"].update(_TA_W5C)
STRINGS["te"].update(_TE_W5C)


# ---------------------------------------------------------------------------
# Wave 5d: ✍️ Copy Style (handwriting) strings — the steps can be read
# like a teacher's hand-written copy. Label + the print-in-copy-style
# link, in all 6 languages (same completeness rule as every wave).
# ---------------------------------------------------------------------------

_EN_W5D = {
    "handwriting_btn": "✍️ Copy Style (handwriting)",
    "print_copy_link": "🖨 Print in copy style",
}

_HI_W5D = {
    "handwriting_btn": "✍️ कॉपी शैली (हस्तलेख)",
    "print_copy_link": "🖨 कॉपी शैली में प्रिंट करें",
}

_BN_W5D = {
    "handwriting_btn": "✍️ খাতার শৈলী (হাতের লেখা)",
    "print_copy_link": "🖨 খাতার শৈলীতে প্রিন্ট করুন",
}

_MR_W5D = {
    "handwriting_btn": "✍️ वही शैली (हस्ताक्षर)",
    "print_copy_link": "🖨 वही शैलीत प्रिंट करा",
}

_TA_W5D = {
    "handwriting_btn": "✍️ நோட்டு பாணி (கையெழுத்து)",
    "print_copy_link": "🖨 நோட்டு பாணியில் அச்சிடவும்",
}

_TE_W5D = {
    "handwriting_btn": "✍️ నోట్‌బుక్ శైలి (చేతిరాత)",
    "print_copy_link": "🖨 నోట్‌బుక్ శైలిలో ప్రింట్ చేయండి",
}

STRINGS["en"].update(_EN_W5D)
STRINGS["hi"].update(_HI_W5D)
STRINGS["bn"].update(_BN_W5D)
STRINGS["mr"].update(_MR_W5D)
STRINGS["ta"].update(_TA_W5D)
STRINGS["te"].update(_TE_W5D)


# ---------------------------------------------------------------------------
# Wave 5e: board-style copy check + Dhyaan meter + Badhai celebration.
# Copy check = the teacher-checked answer copy after a quiz/test:
# marks, a remark by score band, where marks were lost (topics) — it
# checks FINAL ANSWERS only, honestly; no handwriting/step claims.
# Dhyaan = today's study record (localStorage, per calendar day).
# Badhai = the gentle congratulations shown on >= 80% results and on
# finishing a mistakes-retry round. All 6 languages, zero missing.
# ---------------------------------------------------------------------------

_EN_W5E = {
    "copycheck_heading": "📋 Copy Check (teacher style)",
    "copycheck_note": "Your answers were checked like a copy — "
                      "final answers only.",
    "copycheck_lost_label": "Marks were lost in these topics:",
    "copycheck_all_clear": "No marks lost anywhere — every topic "
                           "is clear. 🎉",
    "copycheck_practice_link": "Practise the lost topics",
    "remark_perfect": "Perfect — every answer is right. Bahut "
                      "badhiya! 🌟",
    "remark_great": "Bahut badhiya — almost everything is right!",
    "remark_good": "Achha kiya — keep going, a little more practice "
                   "and it will be perfect.",
    "remark_keep": "Good effort — marks were lost in a few places. "
                   "Check them below and practise those topics.",
    "remark_try": "Koi baat nahi — every mistake teaches you. Look "
                  "at the correct answers and try once more.",
    "celebrate_msg": "🎉 Badhai ho! Excellent work — keep this "
                     "rhythm going!",
    "mistakes_done_msg": "🎉 Badhai ho! You finished the mistakes "
                         "practice round.",
    "dhyaan_label": "🧘 Dhyaan",
    "dhyaan_today": "Today: {minutes} min · {count} questions",
}

_HI_W5E = {
    "copycheck_heading": "📋 कॉपी जाँच (शिक्षक शैली)",
    "copycheck_note": "आपके उत्तर कॉपी की तरह जाँचे गए — केवल अंतिम "
                      "उत्तर।",
    "copycheck_lost_label": "इन विषयों में अंक कटे:",
    "copycheck_all_clear": "कहीं अंक नहीं कटे — हर विषय स्पष्ट है। 🎉",
    "copycheck_practice_link": "कटे हुए विषयों का अभ्यास करें",
    "remark_perfect": "एकदम सही — हर उत्तर सही है। बहुत बढ़िया! 🌟",
    "remark_great": "बहुत बढ़िया — लगभग सब कुछ सही है!",
    "remark_good": "अच्छा किया — ऐसे ही आगे बढ़ें, थोड़ा और अभ्यास "
                   "और सब एकदम सही होगा।",
    "remark_keep": "अच्छा प्रयास — कुछ जगहों पर अंक कटे हैं। नीचे "
                   "देखें और उन विषयों का अभ्यास करें।",
    "remark_try": "कोई बात नहीं — हर ग़लती कुछ सिखाती है। सही उत्तर "
                  "देखें और एक बार फिर कोशिश करें।",
    "celebrate_msg": "🎉 बधाई हो! शानदार काम — यही लय बनाए रखें!",
    "mistakes_done_msg": "🎉 बधाई हो! आपने ग़लतियों के अभ्यास का दौर "
                         "पूरा किया।",
    "dhyaan_label": "🧘 ध्यान",
    "dhyaan_today": "आज: {minutes} मिनट · {count} प्रश्न",
}

_BN_W5E = {
    "copycheck_heading": "📋 খাতা যাচাই (শিক্ষকের শৈলী)",
    "copycheck_note": "আপনার উত্তরগুলো খাতার মতো যাচাই করা হয়েছে — "
                      "শুধু চূড়ান্ত উত্তর।",
    "copycheck_lost_label": "এই বিষয়গুলোতে নম্বর কাটা গেছে:",
    "copycheck_all_clear": "কোথাও নম্বর কাটা যায়নি — সব বিষয় পরিষ্কার। 🎉",
    "copycheck_practice_link": "কাটা যাওয়া বিষয়গুলো অনুশীলন করুন",
    "remark_perfect": "নিখুঁত — সব উত্তর সঠিক। বাহ, খুব ভালো! 🌟",
    "remark_great": "খুব ভালো — প্রায় সবকিছুই সঠিক!",
    "remark_good": "ভালো করেছেন — এগিয়ে যান, আরেকটু অনুশীলনেই "
                   "সব নিখুঁত হবে।",
    "remark_keep": "ভালো চেষ্টা — কয়েক জায়গায় নম্বর কেটেছে। নীচে "
                   "দেখুন এবং ওই বিষয়গুলো অনুশীলন করুন।",
    "remark_try": "কোনো সমস্যা নেই — প্রতিটি ভুল কিছু শেখায়। সঠিক "
                  "উত্তর দেখুন এবং আরেকবার চেষ্টা করুন।",
    "celebrate_msg": "🎉 অভিনন্দন! দুর্দান্ত কাজ — এই ছন্দ ধরে "
                     "রাখুন!",
    "mistakes_done_msg": "🎉 অভিনন্দন! আপনি ভুলের অনুশীলন পর্ব শেষ "
                         "করেছেন।",
    "dhyaan_label": "🧘 মনোযোগ",
    "dhyaan_today": "আজ: {minutes} মিনিট · {count}টি প্রশ্ন",
}

_MR_W5E = {
    "copycheck_heading": "📋 वही तपासणी (शिक्षक शैली)",
    "copycheck_note": "तुमची उत्तरं वहीसारखी तपासली — फक्त अंतिम "
                      "उत्तरं.",
    "copycheck_lost_label": "या विषयांमध्ये गुण कटले:",
    "copycheck_all_clear": "कुठेही गुण कटले नाहीत — प्रत्येक विषय "
                           "स्पष्ट आहे. 🎉",
    "copycheck_practice_link": "कटलेल्या विषयांचा सराव करा",
    "remark_perfect": "अगदी अचूक — प्रत्येक उत्तर बरोबर. खूप छान! 🌟",
    "remark_great": "खूप छान — जवळजवळ सर्व काही बरोबर आहे!",
    "remark_good": "छान केलंत — असंच पुढे चला, थोडा आणखी सराव आणि "
                   "सर्व अचूक होईल.",
    "remark_keep": "चांगला प्रयत्न — काही ठिकाणी गुण कटले. खाली "
                   "पाहा आणि त्या विषयांचा सराव करा.",
    "remark_try": "काही हरकत नाही — प्रत्येक चूक काहीतरी शिकवते. "
                  "बरोबर उत्तरं पाहा आणि पुन्हा एकदा प्रयत्न करा.",
    "celebrate_msg": "🎉 अभिनंदन! अप्रतिम काम — हीच लय कायम ठेवा!",
    "mistakes_done_msg": "🎉 अभिनंदन! तुम्ही चुकांच्या सरावाची फेरी "
                         "पूर्ण केली.",
    "dhyaan_label": "🧘 लक्ष",
    "dhyaan_today": "आज: {minutes} मि. · {count} प्रश्न",
}

_TA_W5E = {
    "copycheck_heading": "📋 நோட்டு சரிபார்ப்பு (ஆசிரியர் பாணி)",
    "copycheck_note": "உங்கள் விடைகள் நோட்டைப் போல சரிபார்க்கப்பட்டன "
                      "— இறுதி விடைகள் மட்டும்.",
    "copycheck_lost_label": "இந்த தலைப்புகளில் மதிப்பெண்கள் "
                            "குறைந்தன:",
    "copycheck_all_clear": "எங்கும் மதிப்பெண் குறையவில்லை — ஒவ்வொரு "
                           "தலைப்பும் தெளிவு. 🎉",
    "copycheck_practice_link": "குறைந்த தலைப்புகளைப் பயிற்சி செய்யவும்",
    "remark_perfect": "சரியானது — ஒவ்வொரு விடையும் சரி. மிகவும் "
                      "நன்று! 🌟",
    "remark_great": "மிகவும் நன்று — கிட்டத்தட்ட எல்லாமே சரி!",
    "remark_good": "நன்றாகச் செய்தீர்கள் — தொடரவும், இன்னும் கொஞ்சம் "
                   "பயிற்சி செய்தால் எல்லாம் சரியாகும்.",
    "remark_keep": "நல்ல முயற்சி — சில இடங்களில் மதிப்பெண்கள் "
                   "குறைந்தன. கீழே பார்த்து அந்த தலைப்புகளைப் "
                   "பயிற்சி செய்யவும்.",
    "remark_try": "பரவாயில்லை — ஒவ்வொரு தவறும் கற்றுத் தரும். சரியான "
                  "விடைகளைப் பார்த்து மீண்டும் முயற்சிக்கவும்.",
    "celebrate_msg": "🎉 வாழ்த்துகள்! அருமையான வேலை — இந்த வேகத்தைத் "
                     "தொடரவும்!",
    "mistakes_done_msg": "🎉 வாழ்த்துகள்! தவறுகள் பயிற்சிச் சுற்றை "
                         "முடித்தீர்கள்.",
    "dhyaan_label": "🧘 கவனம்",
    "dhyaan_today": "இன்று: {minutes} நிமி · {count} கேள்விகள்",
}

_TE_W5E = {
    "copycheck_heading": "📋 నోట్‌బుక్ తనిఖీ (ఉపాధ్యాయ శైలి)",
    "copycheck_note": "మీ సమాధానాలు నోట్‌బుక్‌లా తనిఖీ చేయబడ్డాయి — "
                      "చివరి సమాధానాలు మాత్రమే.",
    "copycheck_lost_label": "ఈ అంశాలలో మార్కులు తగ్గాయి:",
    "copycheck_all_clear": "ఎక్కడా మార్కులు తగ్గలేదు — ప్రతి అంశం "
                           "స్పష్టంగా ఉంది. 🎉",
    "copycheck_practice_link": "తగ్గిన అంశాలను సాధన చేయండి",
    "remark_perfect": "పరిపూర్ణం — ప్రతి సమాధానం సరైనదే. చాలా "
                      "బాగుంది! 🌟",
    "remark_great": "చాలా బాగుంది — దాదాపు అన్నీ సరైనవే!",
    "remark_good": "బాగా చేశారు — ఇలాగే కొనసాగండి, కొంచెం ఎక్కువ "
                   "సాధన చేస్తే అన్నీ సరిగ్గా వస్తాయి.",
    "remark_keep": "మంచి ప్రయత్నం — కొన్ని చోట్ల మార్కులు తగ్గాయి. "
                   "క్రింద చూసి ఆ అంశాలను సాధన చేయండి.",
    "remark_try": "పర్వాలేదు — ప్రతి తప్పు ఏదో నేర్పుతుంది. సరైన "
                  "సమాధానాలు చూసి మళ్ళీ ప్రయత్నించండి.",
    "celebrate_msg": "🎉 అభినందనలు! అద్భుతమైన పని — ఈ లయను "
                     "కొనసాగించండి!",
    "mistakes_done_msg": "🎉 అభినందనలు! మీరు తప్పుల సాధన రౌండ్‌ను "
                         "పూర్తి చేశారు.",
    "dhyaan_label": "🧘 ధ్యానం",
    "dhyaan_today": "ఈరోజు: {minutes} నిమి · {count} ప్రశ్నలు",
}

STRINGS["en"].update(_EN_W5E)
STRINGS["hi"].update(_HI_W5E)
STRINGS["bn"].update(_BN_W5E)
STRINGS["mr"].update(_MR_W5E)
STRINGS["ta"].update(_TA_W5E)
STRINGS["te"].update(_TE_W5E)


def remark_key_for(score, total):
    """Wave 5e: the teacher-style remark for a score band.

    Bands (share of total): 100% -> perfect; >= 80% -> great;
    >= 60% -> good; >= 40% -> keep going; below -> try again.
    """
    if total <= 0:
        return "remark_good"
    ratio = score / total
    if ratio >= 1.0:
        return "remark_perfect"
    if ratio >= 0.8:
        return "remark_great"
    if ratio >= 0.6:
        return "remark_good"
    if ratio >= 0.4:
        return "remark_keep"
    return "remark_try"


# ---------------------------------------------------------------------------
# Wave 6: Mera Saathi (optional first name + class, friendly personal
# greeting and never-scolding encouragement) and the Parent Report
# (this device/session only). Every key exists in all 6 languages.
# ---------------------------------------------------------------------------

_EN_W6 = {
    "saathi_card_heading": "🧒 Mera Saathi",
    "saathi_card_text": "Tell Ganitra your first name, and it will "
                        "greet you like a friend. This is optional — "
                        "you can skip it and keep learning.",
    "saathi_name_label": "Your first name",
    "saathi_name_placeholder": "e.g. Aarav",
    "saathi_class_label": "Class (optional)",
    "saathi_class_any": "No class selected",
    "saathi_class_word": "Class",
    "saathi_save_btn": "Save — let's learn",
    "saathi_skip_btn": "Skip for now",
    "saathi_edit": "Edit",
    "saathi_welcome_name": "Hello {name}! What shall we solve today?",
    "saathi_wrong_name": "No problem, {name} — mistakes are how we "
                         "learn. Look at the correct answer once, "
                         "then try again!",
    "saathi_wrong": "No problem — mistakes are how we learn. Look at "
                    "the correct answer once, then try again!",
    "error_encourage_name": "Don't give up, {name} — try once more "
                            "with the tips below.",
    "error_encourage": "Don't give up — try once more with the tips "
                       "below.",
    "nav_parents": "For Parents",
    "parent_heading": "👨‍👩‍👧 Parent Report",
    "parent_intro_name": "A calm summary of {name}'s learning on "
                         "Ganitra.",
    "parent_intro": "A calm summary of your child's learning on "
                    "Ganitra.",
    "parent_student_label": "Student",
    "parent_solved_label": "Questions in this session's history",
    "parent_today_heading": "Today on this device",
    "parent_minutes_label": "Minutes studied today",
    "parent_today_questions_label": "Questions solved today",
    "parent_record_loading": "Reading today's record from this "
                             "device…",
    "parent_mistakes_heading": "Mistake Notebook",
    "parent_mistakes_count_label": "Questions waiting to practise",
    "parent_topics_label": "Topics",
    "parent_none": "None yet",
    "parent_last_test_heading": "Last test",
    "parent_last_test_label": "Last test score",
    "parent_last_test_none": "No test has been completed in this "
                             "session yet.",
    "parent_stars_heading": "Stars & progress",
    "parent_stars_count": "{stars} stars",
    "parent_stars_rule": "How stars are counted: 1 star for every 5 "
                         "questions in this session's history, plus "
                         "1 star for each test scored at 80% or more.",
    "parent_scope_note": "Please note: this report is made on this "
                         "device and browser. It covers this session "
                         "and today's record stored here — there is "
                         "no account or cloud record yet, so activity "
                         "on another phone will not appear here.",
    "parent_share_btn": "📤 Share on WhatsApp",
}

_HI_W6 = {
    "saathi_card_heading": "🧒 मेरा साथी",
    "saathi_card_text": "अपना पहला नाम बताइए, Ganitra आपको दोस्त की "
                        "तरह बुलाएगा। यह वैकल्पिक है — आप इसे "
                        "छोड़कर भी पढ़ाई जारी रख सकते हैं।",
    "saathi_name_label": "आपका पहला नाम",
    "saathi_name_placeholder": "जैसे आरव",
    "saathi_class_label": "कक्षा (वैकल्पिक)",
    "saathi_class_any": "कोई कक्षा नहीं चुनी",
    "saathi_class_word": "कक्षा",
    "saathi_save_btn": "सहेजें — चलिए सीखते हैं",
    "saathi_skip_btn": "अभी छोड़ें",
    "saathi_edit": "बदलें",
    "saathi_welcome_name": "नमस्ते {name}! आज क्या हल करें?",
    "saathi_wrong_name": "कोई बात नहीं, {name} — गलतियों से ही सीखते "
                         "हैं। सही उत्तर एक बार देखें, फिर फिर से "
                         "कोशिश करें!",
    "saathi_wrong": "कोई बात नहीं — गलतियों से ही सीखते हैं। सही "
                    "उत्तर एक बार देखें, फिर फिर से कोशिश करें!",
    "error_encourage_name": "हार मत मानो, {name} — नीचे दिए सुझावों "
                            "के साथ एक बार फिर कोशिश करो।",
    "error_encourage": "हार मत मानो — नीचे दिए सुझावों के साथ एक बार "
                       "फिर कोशिश करो।",
    "nav_parents": "माता-पिता के लिए",
    "parent_heading": "👨‍👩‍👧 अभिभावक रिपोर्ट",
    "parent_intro_name": "{name} की Ganitra पर पढ़ाई का शांत सारांश।",
    "parent_intro": "आपके बच्चे की Ganitra पर पढ़ाई का शांत सारांश।",
    "parent_student_label": "छात्र",
    "parent_solved_label": "इस सत्र के इतिहास में प्रश्न",
    "parent_today_heading": "आज इस डिवाइस पर",
    "parent_minutes_label": "आज पढ़ाई के मिनट",
    "parent_today_questions_label": "आज हल किए गए प्रश्न",
    "parent_record_loading": "इस डिवाइस से आज का रिकॉर्ड पढ़ा जा रहा "
                             "है…",
    "parent_mistakes_heading": "गलतियों की कॉपी",
    "parent_mistakes_count_label": "अभ्यास के लिए बचे प्रश्न",
    "parent_topics_label": "विषय",
    "parent_none": "अभी कोई नहीं",
    "parent_last_test_heading": "पिछली परीक्षा",
    "parent_last_test_label": "पिछली परीक्षा का अंक",
    "parent_last_test_none": "इस सत्र में अभी कोई परीक्षा पूरी नहीं "
                             "हुई है।",
    "parent_stars_heading": "सितारे और प्रगति",
    "parent_stars_count": "{stars} सितारे",
    "parent_stars_rule": "सितारे ऐसे गिने जाते हैं: इस सत्र के इतिहास "
                         "में हर 5 प्रश्नों पर 1 सितारा, और 80% या "
                         "अधिक अंक वाली हर परीक्षा पर 1 सितारा।",
    "parent_scope_note": "कृपया ध्यान दें: यह रिपोर्ट इसी डिवाइस और "
                         "ब्राउज़र पर बनी है। इसमें यह सत्र और यहाँ "
                         "सहेजा आज का रिकॉर्ड शामिल है — अभी कोई खाता "
                         "या क्लाउड रिकॉर्ड नहीं है, इसलिए दूसरे फ़ोन "
                         "की गतिविधि यहाँ नहीं दिखेगी।",
    "parent_share_btn": "📤 WhatsApp पर साझा करें",
}

_BN_W6 = {
    "saathi_card_heading": "🧒 আমার সাথি",
    "saathi_card_text": "Ganitra-কে তোমার প্রথম নাম বলো, সে তোমাকে "
                        "বন্ধুর মতো ডাকবে। এটি ঐচ্ছিক — এড়িয়ে "
                        "গিয়েও শেখা চালিয়ে যেতে পারো।",
    "saathi_name_label": "তোমার প্রথম নাম",
    "saathi_name_placeholder": "যেমন আরভ",
    "saathi_class_label": "শ্রেণি (ঐচ্ছিক)",
    "saathi_class_any": "কোনো শ্রেণি বাছা হয়নি",
    "saathi_class_word": "শ্রেণি",
    "saathi_save_btn": "সংরক্ষণ করো — চলো শিখি",
    "saathi_skip_btn": "এখন এড়িয়ে যাও",
    "saathi_edit": "বদলাও",
    "saathi_welcome_name": "নমস্কার {name}! আজ কী সমাধান করব?",
    "saathi_wrong_name": "কোনো সমস্যা নেই, {name} — ভুল থেকেই আমরা "
                         "শিখি। সঠিক উত্তরটি একবার দেখে আবার চেষ্টা "
                         "করো!",
    "saathi_wrong": "কোনো সমস্যা নেই — ভুল থেকেই আমরা শিখি। সঠিক "
                    "উত্তরটি একবার দেখে আবার চেষ্টা করো!",
    "error_encourage_name": "হাল ছেড়ো না, {name} — নীচের পরামর্শসহ "
                            "আরেকবার চেষ্টা করো।",
    "error_encourage": "হাল ছেড়ো না — নীচের পরামর্শসহ আরেকবার চেষ্টা "
                       "করো।",
    "nav_parents": "অভিভাবকদের জন্য",
    "parent_heading": "👨‍👩‍👧 অভিভাবক প্রতিবেদন",
    "parent_intro_name": "{name}-এর Ganitra-তে শেখার শান্ত সারাংশ।",
    "parent_intro": "আপনার সন্তানের Ganitra-তে শেখার শান্ত সারাংশ।",
    "parent_student_label": "শিক্ষার্থী",
    "parent_solved_label": "এই সেশনের ইতিহাসে প্রশ্ন",
    "parent_today_heading": "আজ এই ডিভাইসে",
    "parent_minutes_label": "আজ পড়াশোনার মিনিট",
    "parent_today_questions_label": "আজ সমাধান করা প্রশ্ন",
    "parent_record_loading": "এই ডিভাইস থেকে আজকের রেকর্ড পড়া হচ্ছে…",
    "parent_mistakes_heading": "ভুলের খাতা",
    "parent_mistakes_count_label": "অনুশীলনের জন্য অপেক্ষমাণ প্রশ্ন",
    "parent_topics_label": "বিষয়",
    "parent_none": "এখনও নেই",
    "parent_last_test_heading": "শেষ পরীক্ষা",
    "parent_last_test_label": "শেষ পরীক্ষার নম্বর",
    "parent_last_test_none": "এই সেশনে এখনও কোনো পরীক্ষা শেষ হয়নি।",
    "parent_stars_heading": "তারা ও অগ্রগতি",
    "parent_stars_count": "{stars}টি তারা",
    "parent_stars_rule": "তারা এভাবে গণনা হয়: এই সেশনের ইতিহাসে "
                         "প্রতি 5টি প্রশ্নে 1টি তারা, এবং 80% বা "
                         "তার বেশি নম্বর পাওয়া প্রতিটি পরীক্ষায় "
                         "1টি তারা।",
    "parent_scope_note": "মনে রাখবেন: এই প্রতিবেদন এই ডিভাইস ও "
                         "ব্রাউজারেই তৈরি। এতে এই সেশন এবং এখানে "
                         "সংরক্ষিত আজকের রেকর্ড আছে — এখনও কোনো "
                         "অ্যাকাউন্ট বা ক্লাউড রেকর্ড নেই, তাই অন্য "
                         "ফোনের কার্যকলাপ এখানে দেখা যাবে না।",
    "parent_share_btn": "📤 WhatsApp-এ শেয়ার করুন",
}

_MR_W6 = {
    "saathi_card_heading": "🧒 माझा साथी",
    "saathi_card_text": "Ganitra ला तुझं पहिलं नाव सांग, तो तुला "
                        "मित्रासारखा हाक मारेल. हे ऐच्छिक आहे — "
                        "वगळूनही शिकणं सुरू ठेवता येईल.",
    "saathi_name_label": "तुझं पहिलं नाव",
    "saathi_name_placeholder": "उदा. आरव",
    "saathi_class_label": "वर्ग (ऐच्छिक)",
    "saathi_class_any": "वर्ग निवडलेला नाही",
    "saathi_class_word": "वर्ग",
    "saathi_save_btn": "जतन करा — चला शिकूया",
    "saathi_skip_btn": "आता वगळा",
    "saathi_edit": "बदला",
    "saathi_welcome_name": "नमस्कार {name}! आज काय सोडवूया?",
    "saathi_wrong_name": "काही हरकत नाही, {name} — चुकांमधूनच शिकतो. "
                         "बरोबर उत्तर एकदा पाहा आणि पुन्हा प्रयत्न "
                         "करा!",
    "saathi_wrong": "काही हरकत नाही — चुकांमधूनच शिकतो. बरोबर उत्तर "
                    "एकदा पाहा आणि पुन्हा प्रयत्न करा!",
    "error_encourage_name": "हार मानू नकोस, {name} — खालील सूचनांसह "
                            "पुन्हा एकदा प्रयत्न कर.",
    "error_encourage": "हार मानू नकोस — खालील सूचनांसह पुन्हा एकदा "
                       "प्रयत्न कर.",
    "nav_parents": "पालकांसाठी",
    "parent_heading": "👨‍👩‍👧 पालक अहवाल",
    "parent_intro_name": "{name} च्या Ganitra वरील शिकण्याचा शांत "
                         "सारांश.",
    "parent_intro": "तुमच्या मुलाच्या Ganitra वरील शिकण्याचा शांत "
                    "सारांश.",
    "parent_student_label": "विद्यार्थी",
    "parent_solved_label": "या सत्राच्या इतिहासातील प्रश्न",
    "parent_today_heading": "आज या डिव्हाइसवर",
    "parent_minutes_label": "आज अभ्यासाची मिनिटे",
    "parent_today_questions_label": "आज सोडवलेले प्रश्न",
    "parent_record_loading": "या डिव्हाइसवरून आजचा रेकॉर्ड वाचत आहे…",
    "parent_mistakes_heading": "चुकांची वही",
    "parent_mistakes_count_label": "सरावासाठी राहिलेले प्रश्न",
    "parent_topics_label": "विषय",
    "parent_none": "अजून एकही नाही",
    "parent_last_test_heading": "शेवटची चाचणी",
    "parent_last_test_label": "शेवटच्या चाचणीचे गुण",
    "parent_last_test_none": "या सत्रात अजून एकही चाचणी पूर्ण झालेली "
                             "नाही.",
    "parent_stars_heading": "तारे आणि प्रगती",
    "parent_stars_count": "{stars} तारे",
    "parent_stars_rule": "तारे असे मोजले जातात: या सत्राच्या "
                         "इतिहासातील प्रत्येक 5 प्रश्नांसाठी 1 "
                         "तारा, आणि 80% किंवा अधिक गुण मिळालेल्या "
                         "प्रत्येक चाचणीसाठी 1 तारा.",
    "parent_scope_note": "कृपया लक्षात घ्या: हा अहवाल याच डिव्हाइस आणि "
                         "ब्राउझरवर तयार होतो. यात हे सत्र आणि इथे "
                         "जतन केलेला आजचा रेकॉर्ड आहे — अजून खाते "
                         "किंवा क्लाउड रेकॉर्ड नाही, त्यामुळे दुसऱ्या "
                         "फोनवरील हालचाल इथे दिसणार नाही.",
    "parent_share_btn": "📤 WhatsApp वर शेअर करा",
}

_TA_W6 = {
    "saathi_card_heading": "🧒 என் தோழன்",
    "saathi_card_text": "உங்கள் முதல் பெயரை Ganitra-விடம் சொல்லுங்கள்; "
                        "அது உங்களை நண்பரைப் போல அழைக்கும். இது "
                        "விருப்பமானது — தவிர்த்துவிட்டும் கற்றுக் "
                        "கொள்ளலாம்.",
    "saathi_name_label": "உங்கள் முதல் பெயர்",
    "saathi_name_placeholder": "எ.கா. ஆரவ்",
    "saathi_class_label": "வகுப்பு (விருப்பம்)",
    "saathi_class_any": "வகுப்பு தேர்ந்தெடுக்கப்படவில்லை",
    "saathi_class_word": "வகுப்பு",
    "saathi_save_btn": "சேமிக்கவும் — கற்றுக் கொள்ளலாம்",
    "saathi_skip_btn": "இப்போது தவிர்க்கவும்",
    "saathi_edit": "மாற்றவும்",
    "saathi_welcome_name": "வணக்கம் {name}! இன்று எதைத் தீர்க்கலாம்?",
    "saathi_wrong_name": "பரவாயில்லை, {name} — தவறுகளிலிருந்தே "
                         "கற்றுக்கொள்கிறோம். சரியான விடையை ஒருமுறை "
                         "பார்த்து மீண்டும் முயற்சிக்கவும்!",
    "saathi_wrong": "பரவாயில்லை — தவறுகளிலிருந்தே கற்றுக்கொள்கிறோம். "
                    "சரியான விடையை ஒருமுறை பார்த்து மீண்டும் "
                    "முயற்சிக்கவும்!",
    "error_encourage_name": "விட்டுவிடாதீர்கள், {name} — கீழே உள்ள "
                            "குறிப்புகளுடன் மீண்டும் முயற்சிக்கவும்.",
    "error_encourage": "விட்டுவிடாதீர்கள் — கீழே உள்ள குறிப்புகளுடன் "
                       "மீண்டும் முயற்சிக்கவும்.",
    "nav_parents": "பெற்றோருக்கு",
    "parent_heading": "👨‍👩‍👧 பெற்றோர் அறிக்கை",
    "parent_intro_name": "Ganitra-இல் {name} கற்றதின் அமைதியான "
                         "சுருக்கம்.",
    "parent_intro": "Ganitra-இல் உங்கள் குழந்தை கற்றதின் அமைதியான "
                    "சுருக்கம்.",
    "parent_student_label": "மாணவர்",
    "parent_solved_label": "இந்த அமர்வின் வரலாற்றில் உள்ள கேள்விகள்",
    "parent_today_heading": "இன்று இந்த சாதனத்தில்",
    "parent_minutes_label": "இன்று படித்த நிமிடங்கள்",
    "parent_today_questions_label": "இன்று தீர்க்கப்பட்ட கேள்விகள்",
    "parent_record_loading": "இந்த சாதனத்திலிருந்து இன்றைய பதிவைப் "
                             "படிக்கிறது…",
    "parent_mistakes_heading": "தவறுகள் குறிப்பேடு",
    "parent_mistakes_count_label": "பயிற்சிக்காக காத்திருக்கும் "
                                   "கேள்விகள்",
    "parent_topics_label": "தலைப்புகள்",
    "parent_none": "இன்னும் இல்லை",
    "parent_last_test_heading": "கடைசி தேர்வு",
    "parent_last_test_label": "கடைசி தேர்வு மதிப்பெண்",
    "parent_last_test_none": "இந்த அமர்வில் இன்னும் எந்த தேர்வும் "
                             "முடிக்கப்படவில்லை.",
    "parent_stars_heading": "நட்சத்திரங்கள் & முன்னேற்றம்",
    "parent_stars_count": "{stars} நட்சத்திரங்கள்",
    "parent_stars_rule": "நட்சத்திரங்கள் இப்படி கணக்கிடப்படுகின்றன: "
                         "இந்த அமர்வின் வரலாற்றில் ஒவ்வொரு 5 "
                         "கேள்விகளுக்கும் 1 நட்சத்திரம், மற்றும் 80% "
                         "அல்லது அதற்கு மேல் மதிப்பெண் பெற்ற "
                         "ஒவ்வொரு தேர்வுக்கும் 1 நட்சத்திரம்.",
    "parent_scope_note": "கவனிக்கவும்: இந்த அறிக்கை இந்த சாதனம் "
                         "மற்றும் உலாவியிலேயே உருவாக்கப்படுகிறது. "
                         "இதில் இந்த அமர்வு மற்றும் இங்கு "
                         "சேமிக்கப்பட்ட இன்றைய பதிவு உள்ளது — இன்னும் "
                         "கணக்கு அல்லது கிளவுட் பதிவு இல்லை, எனவே "
                         "மற்றொரு தொலைபேசியின் செயல்பாடு இங்கே "
                         "தெரியாது.",
    "parent_share_btn": "📤 WhatsApp இல் பகிரவும்",
}

_TE_W6 = {
    "saathi_card_heading": "🧒 నా స్నేహితుడు",
    "saathi_card_text": "మీ మొదటి పేరును Ganitra కి చెప్పండి; అది "
                        "మిమ్మల్ని స్నేహితుడిలా పిలుస్తుంది. ఇది "
                        "ఐచ్ఛికం — దాటవేసి కూడా నేర్చుకోవచ్చు.",
    "saathi_name_label": "మీ మొదటి పేరు",
    "saathi_name_placeholder": "ఉదా. ఆరవ్",
    "saathi_class_label": "తరగతి (ఐచ్ఛికం)",
    "saathi_class_any": "తరగతి ఎంచుకోలేదు",
    "saathi_class_word": "తరగతి",
    "saathi_save_btn": "సేవ్ చేయండి — నేర్చుకుందాం",
    "saathi_skip_btn": "ఇప్పుడు దాటవేయండి",
    "saathi_edit": "మార్చండి",
    "saathi_welcome_name": "నమస్తే {name}! ఈరోజు ఏమి పరిష్కరిద్దాం?",
    "saathi_wrong_name": "పర్వాలేదు, {name} — తప్పుల నుండే "
                         "నేర్చుకుంటాం. సరైన సమాధానాన్ని ఒకసారి "
                         "చూసి మళ్ళీ ప్రయత్నించండి!",
    "saathi_wrong": "పర్వాలేదు — తప్పుల నుండే నేర్చుకుంటాం. సరైన "
                    "సమాధానాన్ని ఒకసారి చూసి మళ్ళీ ప్రయత్నించండి!",
    "error_encourage_name": "వదిలిపెట్టకండి, {name} — క్రింది "
                            "సూచనలతో మళ్ళీ ప్రయత్నించండి.",
    "error_encourage": "వదిలిపెట్టకండి — క్రింది సూచనలతో మళ్ళీ "
                       "ప్రయత్నించండి.",
    "nav_parents": "తల్లిదండ్రుల కోసం",
    "parent_heading": "👨‍👩‍👧 తల్లిదండ్రుల నివేదిక",
    "parent_intro_name": "Ganitra లో {name} నేర్చుకున్నదాని ప్రశాంత "
                         "సారాంశం.",
    "parent_intro": "Ganitra లో మీ పిల్లలు నేర్చుకున్నదాని ప్రశాంత "
                    "సారాంశం.",
    "parent_student_label": "విద్యార్థి",
    "parent_solved_label": "ఈ సెషన్ చరిత్రలోని ప్రశ్నలు",
    "parent_today_heading": "ఈరోజు ఈ పరికరంలో",
    "parent_minutes_label": "ఈరోజు చదివిన నిమిషాలు",
    "parent_today_questions_label": "ఈరోజు పరిష్కరించిన ప్రశ్నలు",
    "parent_record_loading": "ఈ పరికరం నుండి ఈరోజు రికార్డును "
                             "చదువుతోంది…",
    "parent_mistakes_heading": "తప్పుల నోట్‌బుక్",
    "parent_mistakes_count_label": "సాధన కోసం వేచి ఉన్న ప్రశ్నలు",
    "parent_topics_label": "అంశాలు",
    "parent_none": "ఇంకా లేవు",
    "parent_last_test_heading": "చివరి పరీక్ష",
    "parent_last_test_label": "చివరి పరీక్ష స్కోరు",
    "parent_last_test_none": "ఈ సెషన్‌లో ఇంకా ఏ పరీక్ష పూర్తి "
                             "కాలేదు.",
    "parent_stars_heading": "నక్షత్రాలు & పురోగతి",
    "parent_stars_count": "{stars} నక్షత్రాలు",
    "parent_stars_rule": "నక్షత్రాలు ఇలా లెక్కించబడతాయి: ఈ సెషన్ "
                         "చరిత్రలోని ప్రతి 5 ప్రశ్నలకు 1 నక్షత్రం, "
                         "మరియు 80% లేదా అంతకంటే ఎక్కువ స్కోరు "
                         "సాధించిన ప్రతి పరీక్షకు 1 నక్షత్రం.",
    "parent_scope_note": "గమనించండి: ఈ నివేదిక ఈ పరికరం మరియు "
                         "బ్రౌజర్‌లోనే తయారవుతుంది. ఇందులో ఈ సెషన్ "
                         "మరియు ఇక్కడ నిల్వ ఉన్న ఈరోజు రికార్డు "
                         "ఉంటుంది — ఇంకా ఖాతా లేదా క్లౌడ్ రికార్డు "
                         "లేదు, కాబట్టి మరో ఫోన్‌లోని కార్యకలాపం "
                         "ఇక్కడ కనిపించదు.",
    "parent_share_btn": "📤 WhatsApp లో పంచుకోండి",
}

STRINGS["en"].update(_EN_W6)
STRINGS["hi"].update(_HI_W6)
STRINGS["bn"].update(_BN_W6)
STRINGS["mr"].update(_MR_W6)
STRINGS["ta"].update(_TA_W6)
STRINGS["te"].update(_TE_W6)

# ---------------------------------------------------------------------------
# Wave 7 strings: the pure chat-screen homepage (ChatGPT-style — slim
# top bar, message thread, bottom composer, nothing else) and the
# /topics page that now holds the topic list. Every key exists in
# all 6 languages.
# ---------------------------------------------------------------------------

_EN_W7 = {
    "nav_topics": "Topics",
    "menu_label": "Menu",
    "chat_greeting_plain": "Namaste! 👋",
    "chat_empty_sub": "Type it, speak it 🎤, or send a photo 📷 — "
                      "step-by-step solution, right here.",
    "chat_thinking": "Ganitra is thinking…",
}

_HI_W7 = {
    "nav_topics": "विषय",
    "menu_label": "मेनू",
    "chat_greeting_plain": "नमस्ते! 👋",
    "chat_empty_sub": "लिखिए, बोलिए 🎤 या फ़ोटो भेजिए 📷 — "
                      "चरण-दर-चरण हल, यहीं।",
    "chat_thinking": "Ganitra सोच रहा है…",
}

_BN_W7 = {
    "nav_topics": "বিষয়সমূহ",
    "menu_label": "মেনু",
    "chat_greeting_plain": "নমস্কার! 👋",
    "chat_empty_sub": "লিখুন, বলুন 🎤 বা ছবি পাঠান 📷 — "
                      "ধাপে ধাপে সমাধান, এখানেই।",
    "chat_thinking": "Ganitra ভাবছে…",
}

_MR_W7 = {
    "nav_topics": "विषय",
    "menu_label": "मेनू",
    "chat_greeting_plain": "नमस्कार! 👋",
    "chat_empty_sub": "लिहा, बोला 🎤 किंवा फोटो पाठवा 📷 — "
                      "टप्प्याटप्प्याने उत्तर, इथेच.",
    "chat_thinking": "Ganitra विचार करत आहे…",
}

_TA_W7 = {
    "nav_topics": "தலைப்புகள்",
    "menu_label": "பட்டி",
    "chat_greeting_plain": "வணக்கம்! 👋",
    "chat_empty_sub": "தட்டச்சு செய்யுங்கள், பேசுங்கள் 🎤 அல்லது "
                      "புகைப்படம் அனுப்புங்கள் 📷 — படிப்படியான "
                      "தீர்வு, இங்கேயே.",
    "chat_thinking": "Ganitra யோசித்து வருகிறது…",
}

_TE_W7 = {
    "nav_topics": "అంశాలు",
    "menu_label": "మెను",
    "chat_greeting_plain": "నమస్తే! 👋",
    "chat_empty_sub": "టైప్ చేయండి, మాట్లాడండి 🎤 లేదా ఫోటో "
                      "పంపండి 📷 — దశలవారీ పరిష్కారం, ఇక్కడే.",
    "chat_thinking": "Ganitra ఆలోచిస్తోంది…",
}

STRINGS["en"].update(_EN_W7)
STRINGS["hi"].update(_HI_W7)
STRINGS["bn"].update(_BN_W7)
STRINGS["mr"].update(_MR_W7)
STRINGS["ta"].update(_TA_W7)
STRINGS["te"].update(_TE_W7)

# --- Wave 9 additions: auto-language switch toast --------------------------
# Shown once in the chat after an automatic language switch (the
# student chatted in another language). "{lang}" is the language's
# own name (e.g. हिन्दी). The client also receives the full chat-UI
# string set in the NEW language inside the /api/solve response so
# it can re-skin the page without a reload.
STRINGS["en"].update({
    "lang_switched_toast": "🌐 Language changed to {lang} — "
                           "keep asking in any language!",
})
STRINGS["hi"].update({
    "lang_switched_toast": "🌐 भाषा {lang} में बदल गई है — "
                           "किसी भी भाषा में पूछते रहो!",
})
STRINGS["bn"].update({
    "lang_switched_toast": "🌐 ভাষা {lang}-এ বদলে গেছে — "
                           "যেকোনো ভাষায় জিজ্ঞেস করতে থাকো!",
})
STRINGS["mr"].update({
    "lang_switched_toast": "🌐 भाषा {lang} मध्ये बदलली आहे — "
                           "कोणत्याही भाषेत विचारत राहा!",
})
STRINGS["ta"].update({
    "lang_switched_toast": "🌐 மொழி {lang} ஆக மாறிவிட்டது — "
                           "எந்த மொழியிலும் கேட்கலாம்!",
})
STRINGS["te"].update({
    "lang_switched_toast": "🌐 భాష {lang}కి మారింది — "
                           "ఏ భాషలోనైనా అడగండి!",
})

# --- Wave 10 additions: the first-page sign-in ---------------------------
# Suraj's approved design (one page, one background, logo on top):
# name + class + board are all TYPE-IN fields (no ready-made chips),
# then the gold "Your 3 Favourite Things" card (goal, hobby,
# favourite) with the password inside it, one big button, and the
# forgot line. Returning students use the Welcome-back mode on the
# same page: name + password, or name + ANY ONE favourite thing
# (+ a new password) when the password is forgotten. Every key
# exists in all 6 languages.
_EN_W10 = {
    "nav_logout": "Log out",
    "auth_name_label": "Your name",
    "auth_name_placeholder": "Enter your name",
    "auth_class_label": "Class",
    "auth_class_placeholder": "Write your class (6 to 12)",
    "auth_board_label": "Board",
    "auth_board_placeholder": "Write your board (CBSE, ICSE...)",
    "auth_fav_heading": "Your 3 Favourite Things",
    "auth_goal_label": "My Goal",
    "auth_hobby_label": "My Hobby",
    "auth_fav_label": "My Favourite",
    "auth_password_label": "Password",
    "auth_new_password_label": "New password",
    "auth_signup_btn": "Create my account",
    "auth_forgot_line": "Forgot password? Any one favourite thing "
                        "will log you in",
    "auth_welcome_back": "Welcome back",
    "auth_have_account": "Already have an account? Log in",
    "auth_new_here": "New here? Create your account",
    "auth_login_btn": "Log in",
    "auth_login_fav_link": "Forgot password? Log in with a "
                           "favourite thing",
    "auth_fav_field_label": "Any one of your 3 favourite things",
    "auth_fav_login_btn": "Log in & set new password",
    "auth_err_fill_all": "Please fill every field — name, class, "
                         "board, all 3 favourite things and a "
                         "password.",
    "auth_err_class": "Class must be between 6 and 12 — please "
                      "write it like 8 or Class 8.",
    "auth_err_password_short": "Password needs at least 4 "
                               "characters — pick one you will "
                               "remember.",
    "auth_err_name_taken": "This name is already registered. Add "
                           "something to your name to make it "
                           "yours — like Aarav S. — and try again.",
    "auth_err_login": "Name or password did not match. Please "
                      "check and try again.",
    "auth_err_fav": "That does not match any of your 3 favourite "
                    "things. Try another one, exactly as you "
                    "wrote it.",
    "auth_err_lockout": "Too many tries — please wait a little "
                        "and try again.",
    "auth_err_fav_short": "Each favourite thing needs at least "
                          "3 letters — write the full word, like "
                          "Cricket or Pizza.",
}

_HI_W10 = {
    "nav_logout": "लॉग आउट",
    "auth_name_label": "तुम्हारा नाम",
    "auth_name_placeholder": "अपना नाम लिखो",
    "auth_class_label": "कक्षा",
    "auth_class_placeholder": "अपनी कक्षा लिखो (6 से 12)",
    "auth_board_label": "बोर्ड",
    "auth_board_placeholder": "अपना बोर्ड लिखो (CBSE, ICSE...)",
    "auth_fav_heading": "तुम्हारी 3 पसंदीदा चीज़ें",
    "auth_goal_label": "मेरा लक्ष्य",
    "auth_hobby_label": "मेरा शौक",
    "auth_fav_label": "मेरी पसंदीदा चीज़",
    "auth_password_label": "पासवर्ड",
    "auth_new_password_label": "नया पासवर्ड",
    "auth_signup_btn": "मेरा खाता बनाओ",
    "auth_forgot_line": "पासवर्ड भूल गए? कोई एक पसंदीदा चीज़ "
                        "तुम्हें लॉग इन करा देगी",
    "auth_welcome_back": "फिर से स्वागत है",
    "auth_have_account": "पहले से खाता है? लॉग इन करो",
    "auth_new_here": "यहाँ नए हो? अपना खाता बनाओ",
    "auth_login_btn": "लॉग इन",
    "auth_login_fav_link": "पासवर्ड भूल गए? पसंदीदा चीज़ से "
                           "लॉग इन करो",
    "auth_fav_field_label": "तुम्हारी 3 पसंदीदा चीज़ों में से "
                            "कोई एक",
    "auth_fav_login_btn": "लॉग इन करो और नया पासवर्ड बनाओ",
    "auth_err_fill_all": "कृपया हर खाना भरो — नाम, कक्षा, बोर्ड, "
                         "तीनों पसंदीदा चीज़ें और पासवर्ड।",
    "auth_err_class": "कक्षा 6 से 12 के बीच होनी चाहिए — ऐसे "
                      "लिखो जैसे 8 या Class 8।",
    "auth_err_password_short": "पासवर्ड कम से कम 4 अक्षरों का हो "
                               "— ऐसा चुनो जो याद रहे।",
    "auth_err_name_taken": "यह नाम पहले से दर्ज है। अपने नाम में "
                           "कुछ जोड़कर उसे अपना बनाओ — जैसे "
                           "Aarav S. — और फिर कोशिश करो।",
    "auth_err_login": "नाम या पासवर्ड मेल नहीं खाया। जाँचकर फिर "
                      "कोशिश करो।",
    "auth_err_fav": "यह तुम्हारी 3 पसंदीदा चीज़ों में से किसी से "
                    "मेल नहीं खाता। कोई और, बिल्कुल वैसी ही "
                    "लिखकर देखो जैसी लिखी थी।",
    "auth_err_lockout": "बहुत कोशिशें हो गईं — थोड़ी देर रुककर "
                        "फिर कोशिश करो।",
    "auth_err_fav_short": "हर पसंदीदा चीज़ कम से कम 3 अक्षरों "
                          "की हो — पूरा शब्द लिखो, जैसे Cricket "
                          "या Pizza।",
}

_BN_W10 = {
    "nav_logout": "লগ আউট",
    "auth_name_label": "তোমার নাম",
    "auth_name_placeholder": "তোমার নাম লেখো",
    "auth_class_label": "শ্রেণি",
    "auth_class_placeholder": "তোমার শ্রেণি লেখো (6 থেকে 12)",
    "auth_board_label": "বোর্ড",
    "auth_board_placeholder": "তোমার বোর্ড লেখো (CBSE, ICSE...)",
    "auth_fav_heading": "তোমার 3টি প্রিয় জিনিস",
    "auth_goal_label": "আমার লক্ষ্য",
    "auth_hobby_label": "আমার শখ",
    "auth_fav_label": "আমার প্রিয় জিনিস",
    "auth_password_label": "পাসওয়ার্ড",
    "auth_new_password_label": "নতুন পাসওয়ার্ড",
    "auth_signup_btn": "আমার অ্যাকাউন্ট তৈরি করো",
    "auth_forgot_line": "পাসওয়ার্ড ভুলে গেছো? যেকোনো একটি প্রিয় "
                        "জিনিস দিয়েই লগ ইন হয়ে যাবে",
    "auth_welcome_back": "আবার স্বাগতম",
    "auth_have_account": "আগে থেকেই অ্যাকাউন্ট আছে? লগ ইন করো",
    "auth_new_here": "এখানে নতুন? তোমার অ্যাকাউন্ট তৈরি করো",
    "auth_login_btn": "লগ ইন",
    "auth_login_fav_link": "পাসওয়ার্ড ভুলে গেছো? প্রিয় জিনিস "
                           "দিয়ে লগ ইন করো",
    "auth_fav_field_label": "তোমার 3টি প্রিয় জিনিসের যেকোনো একটি",
    "auth_fav_login_btn": "লগ ইন করো ও নতুন পাসওয়ার্ড বসাও",
    "auth_err_fill_all": "অনুগ্রহ করে প্রতিটি ঘর পূরণ করো — নাম, "
                         "শ্রেণি, বোর্ড, 3টি প্রিয় জিনিসই এবং "
                         "পাসওয়ার্ড।",
    "auth_err_class": "শ্রেণি 6 থেকে 12-এর মধ্যে হতে হবে — "
                      "এভাবে লেখো যেমন 8 বা Class 8।",
    "auth_err_password_short": "পাসওয়ার্ড অন্তত 4 অক্ষরের হতে "
                               "হবে — এমন একটি বেছে নাও যা মনে "
                               "থাকবে।",
    "auth_err_name_taken": "এই নামটি আগেই নথিভুক্ত আছে। তোমার "
                           "নামের সঙ্গে কিছু যোগ করে সেটাকে "
                           "তোমার নিজের করে নাও — যেমন Aarav S. "
                           "— তারপর আবার চেষ্টা করো।",
    "auth_err_login": "নাম বা পাসওয়ার্ড মেলেনি। যাচাই করে আবার "
                      "চেষ্টা করো।",
    "auth_err_fav": "এটি তোমার 3টি প্রিয় জিনিসের কোনোটির সঙ্গে "
                    "মিলছে না। অন্যটি, ঠিক যেমন লিখেছিলে "
                    "তেমনভাবেই লিখে দেখো।",
    "auth_err_lockout": "অনেকবার চেষ্টা হয়ে গেছে — একটু অপেক্ষা "
                        "করে আবার চেষ্টা করো।",
    "auth_err_fav_short": "প্রতিটি প্রিয় জিনিস অন্তত 3 অক্ষরের "
                          "হতে হবে — পুরো শব্দটি লেখো, যেমন "
                          "Cricket বা Pizza।",
}

_MR_W10 = {
    "nav_logout": "लॉग आउट",
    "auth_name_label": "तुमचे नाव",
    "auth_name_placeholder": "तुमचे नाव लिहा",
    "auth_class_label": "इयत्ता",
    "auth_class_placeholder": "तुमची इयत्ता लिहा (6 ते 12)",
    "auth_board_label": "बोर्ड",
    "auth_board_placeholder": "तुमचे बोर्ड लिहा (CBSE, ICSE...)",
    "auth_fav_heading": "तुमच्या 3 आवडत्या गोष्टी",
    "auth_goal_label": "माझे ध्येय",
    "auth_hobby_label": "माझा छंद",
    "auth_fav_label": "माझी आवडती गोष्ट",
    "auth_password_label": "पासवर्ड",
    "auth_new_password_label": "नवीन पासवर्ड",
    "auth_signup_btn": "माझे खाते तयार करा",
    "auth_forgot_line": "पासवर्ड विसरलात? कोणतीही एक आवडती गोष्ट "
                        "तुम्हाला लॉग इन करेल",
    "auth_welcome_back": "पुन्हा स्वागत आहे",
    "auth_have_account": "आधीपासून खाते आहे? लॉग इन करा",
    "auth_new_here": "इथे नवीन आहात? तुमचे खाते तयार करा",
    "auth_login_btn": "लॉग इन",
    "auth_login_fav_link": "पासवर्ड विसरलात? आवडत्या गोष्टीने "
                           "लॉग इन करा",
    "auth_fav_field_label": "तुमच्या 3 आवडत्या गोष्टींपैकी "
                            "कोणतीही एक",
    "auth_fav_login_btn": "लॉग इन करा आणि नवीन पासवर्ड ठेवा",
    "auth_err_fill_all": "कृपया प्रत्येक रकाना भरा — नाव, "
                         "इयत्ता, बोर्ड, तिन्ही आवडत्या गोष्टी "
                         "आणि पासवर्ड.",
    "auth_err_class": "इयत्ता 6 ते 12 च्या दरम्यान हवी — अशी "
                      "लिहा जसे 8 किंवा Class 8.",
    "auth_err_password_short": "पासवर्ड किमान 4 अक्षरांचा हवा "
                               "— लक्षात राहील असा निवडा.",
    "auth_err_name_taken": "हे नाव आधीच नोंदवलेले आहे. तुमच्या "
                           "नावात काही जोडून ते तुमचे स्वतःचे "
                           "करा — जसे Aarav S. — आणि पुन्हा "
                           "प्रयत्न करा.",
    "auth_err_login": "नाव किंवा पासवर्ड जुळला नाही. तपासून "
                      "पुन्हा प्रयत्न करा.",
    "auth_err_fav": "हे तुमच्या 3 आवडत्या गोष्टींपैकी कोणत्याही "
                    "गोष्टीशी जुळत नाही. दुसरी गोष्ट, जशी "
                    "लिहिली होती तशीच लिहून पहा.",
    "auth_err_lockout": "खूप प्रयत्न झाले — थोडा वेळ थांबून "
                        "पुन्हा प्रयत्न करा.",
    "auth_err_fav_short": "प्रत्येक आवडती गोष्ट किमान 3 "
                          "अक्षरांची हवी — पूर्ण शब्द लिहा, जसे "
                          "Cricket किंवा Pizza.",
}

_TA_W10 = {
    "nav_logout": "வெளியேறு",
    "auth_name_label": "உங்கள் பெயர்",
    "auth_name_placeholder": "உங்கள் பெயரை எழுதுங்கள்",
    "auth_class_label": "வகுப்பு",
    "auth_class_placeholder": "உங்கள் வகுப்பை எழுதுங்கள் (6 முதல் 12)",
    "auth_board_label": "வாரியம்",
    "auth_board_placeholder": "உங்கள் வாரியத்தை எழுதுங்கள் (CBSE, ICSE...)",
    "auth_fav_heading": "உங்களுக்குப் பிடித்த 3 விஷயங்கள்",
    "auth_goal_label": "என் இலக்கு",
    "auth_hobby_label": "என் பொழுதுபோக்கு",
    "auth_fav_label": "எனக்கு மிகவும் பிடித்தது",
    "auth_password_label": "கடவுச்சொல்",
    "auth_new_password_label": "புதிய கடவுச்சொல்",
    "auth_signup_btn": "என் கணக்கை உருவாக்கு",
    "auth_forgot_line": "கடவுச்சொல் மறந்துவிட்டதா? ஏதேனும் "
                        "ஒரு பிடித்த விஷயம் உங்களை உள்நுழைய "
                        "வைக்கும்",
    "auth_welcome_back": "மீண்டும் வருக",
    "auth_have_account": "ஏற்கனவே கணக்கு உள்ளதா? உள்நுழையுங்கள்",
    "auth_new_here": "இங்கு புதியவரா? உங்கள் கணக்கை உருவாக்குங்கள்",
    "auth_login_btn": "உள்நுழை",
    "auth_login_fav_link": "கடவுச்சொல் மறந்துவிட்டதா? பிடித்த "
                           "விஷயத்தால் உள்நுழையுங்கள்",
    "auth_fav_field_label": "உங்களுக்குப் பிடித்த 3 விஷயங்களில் "
                            "ஏதேனும் ஒன்று",
    "auth_fav_login_btn": "உள்நுழைந்து புதிய கடவுச்சொல் "
                          "அமைக்கவும்",
    "auth_err_fill_all": "ஒவ்வொரு புலத்தையும் நிரப்புங்கள் — "
                         "பெயர், வகுப்பு, வாரியம், பிடித்த "
                         "3 விஷயங்களும் மற்றும் கடவுச்சொல்.",
    "auth_err_class": "வகுப்பு 6 முதல் 12 வரை இருக்க வேண்டும் "
                      "— 8 அல்லது Class 8 என எழுதுங்கள்.",
    "auth_err_password_short": "கடவுச்சொல் குறைந்தது 4 "
                               "எழுத்துகள் இருக்க வேண்டும் — "
                               "நினைவில் இருக்கும் ஒன்றைத் "
                               "தேர்ந்தெடுங்கள்.",
    "auth_err_name_taken": "இந்தப் பெயர் ஏற்கனவே பதிவு "
                           "செய்யப்பட்டுள்ளது. Aarav S. போல "
                           "உங்கள் பெயருடன் ஏதாவது சேர்த்து "
                           "அதை உங்களுடையதாக்கி மீண்டும் "
                           "முயற்சிக்கவும்.",
    "auth_err_login": "பெயர் அல்லது கடவுச்சொல் பொருந்தவில்லை. "
                      "சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    "auth_err_fav": "இது உங்களுக்குப் பிடித்த 3 விஷயங்களில் "
                    "எதுவும் பொருந்தவில்லை. மற்றொன்றை, "
                    "எழுதியது போலவே எழுதி முயற்சிக்கவும்.",
    "auth_err_lockout": "பல முயற்சிகள் ஆகிவிட்டன — சிறிது "
                        "காத்திருந்து மீண்டும் முயற்சிக்கவும்.",
    "auth_err_fav_short": "ஒவ்வொரு பிடித்த விஷயமும் குறைந்தது "
                          "3 எழுத்துகள் இருக்க வேண்டும் — "
                          "Cricket அல்லது Pizza போல முழு "
                          "வார்த்தையை எழுதுங்கள்.",
}

_TE_W10 = {
    "nav_logout": "లాగ్ అవుట్",
    "auth_name_label": "మీ పేరు",
    "auth_name_placeholder": "మీ పేరు రాయండి",
    "auth_class_label": "తరగతి",
    "auth_class_placeholder": "మీ తరగతి రాయండి (6 నుండి 12)",
    "auth_board_label": "బోర్డు",
    "auth_board_placeholder": "మీ బోర్డు రాయండి (CBSE, ICSE...)",
    "auth_fav_heading": "మీకు ఇష్టమైన 3 విషయాలు",
    "auth_goal_label": "నా లక్ష్యం",
    "auth_hobby_label": "నా అభిరుచి",
    "auth_fav_label": "నాకు అత్యంత ఇష్టమైనది",
    "auth_password_label": "పాస్‌వర్డ్",
    "auth_new_password_label": "కొత్త పాస్‌వర్డ్",
    "auth_signup_btn": "నా ఖాతాను సృష్టించు",
    "auth_forgot_line": "పాస్‌వర్డ్ మర్చిపోయారా? ఏదైనా ఒక "
                        "ఇష్టమైన విషయం మిమ్మల్ని లాగిన్ చేస్తుంది",
    "auth_welcome_back": "మళ్లీ స్వాగతం",
    "auth_have_account": "ఇప్పటికే ఖాతా ఉందా? లాగిన్ చేయండి",
    "auth_new_here": "ఇక్కడ కొత్తవారా? మీ ఖాతాను సృష్టించండి",
    "auth_login_btn": "లాగిన్",
    "auth_login_fav_link": "పాస్‌వర్డ్ మర్చిపోయారా? ఇష్టమైన "
                           "విషయంతో లాగిన్ చేయండి",
    "auth_fav_field_label": "మీకు ఇష్టమైన 3 విషయాలలో ఏదైనా ఒకటి",
    "auth_fav_login_btn": "లాగిన్ చేసి కొత్త పాస్‌వర్డ్ పెట్టండి",
    "auth_err_fill_all": "ప్రతి ఫీల్డ్ నింపండి — పేరు, తరగతి, "
                         "బోర్డు, ఇష్టమైన 3 విషయాలు మరియు "
                         "పాస్‌వర్డ్.",
    "auth_err_class": "తరగతి 6 నుండి 12 మధ్య ఉండాలి — 8 లేదా "
                      "Class 8 అని రాయండి.",
    "auth_err_password_short": "పాస్‌వర్డ్ కనీసం 4 అక్షరాలు "
                               "ఉండాలి — గుర్తుండే దాన్ని "
                               "ఎంచుకోండి.",
    "auth_err_name_taken": "ఈ పేరు ఇప్పటికే నమోదైంది. Aarav S. "
                           "లాగా మీ పేరుకు ఏదైనా జోడించి దాన్ని "
                           "మీ స్వంతం చేసుకుని మళ్లీ "
                           "ప్రయత్నించండి.",
    "auth_err_login": "పేరు లేదా పాస్‌వర్డ్ సరిపోలలేదు. "
                      "సరిచూసి మళ్లీ ప్రయత్నించండి.",
    "auth_err_fav": "ఇది మీకు ఇష్టమైన 3 విషయాలలో దేనితోనూ "
                    "సరిపోలలేదు. మరొకటి, రాసినట్లుగానే రాసి "
                    "ప్రయత్నించండి.",
    "auth_err_lockout": "చాలా ప్రయత్నాలు అయ్యాయి — కొంచెం "
                        "ఆగి మళ్లీ ప్రయత్నించండి.",
    "auth_err_fav_short": "ప్రతి ఇష్టమైన విషయం కనీసం 3 అక్షరాలు "
                          "ఉండాలి — Cricket లేదా Pizza లాగా "
                          "పూర్తి పదం రాయండి.",
}

STRINGS["en"].update(_EN_W10)
STRINGS["hi"].update(_HI_W10)
STRINGS["bn"].update(_BN_W10)
STRINGS["mr"].update(_MR_W10)
STRINGS["ta"].update(_TA_W10)
STRINGS["te"].update(_TE_W10)

# --- Wave 11 additions: multiple chats (Brave-style all-chats view) -------
# Suraj's approved design (from his own Brave screenshot): the
# chat top bar loses the name–class pill and gains a plain "+" at
# the far right; tapping it opens the all-chats view — a chats
# count chip, a "Search your chats" bar that really filters, the
# chats as a 2-column grid of preview cards (mini logo + title +
# ✕ + a preview body), a big blue "+" button bottom-centre for a
# new chat, and a ⋮ menu holding "Close all chats". Chats belong
# to the signed-in account (server-side, see chats.py). Every key
# exists in all 6 languages.
_EN_W11 = {
    "chats_heading": "Your chats",
    "chats_search_placeholder": "Search your chats",
    "chats_new": "New chat",
    "chats_new_label": "New chat",
    "chats_open_label": "All chats",
    "chats_count_label": "{count} chats",
    "chats_open_now": "Open now",
    "chats_answer_snippet": "Ganitra's answer",
    "chats_no_results": "No chat matches your search.",
    "chats_none_yet": "No chats yet — tap + to start your first chat!",
    "chats_close_one_label": "Close this chat",
    "chats_delete_confirm": "Delete this chat? Its questions and "
                            "answers will be gone.",
    "chats_close_all": "Close all chats",
    "chats_close_all_confirm": "Close ALL your chats? Every chat's "
                               "questions and answers will be gone.",
    "chats_menu_label": "More options",
    "chats_view_label": "Grid or list view",
    "file_btn": "📎 Choose a file",
    "js_chats_saved_note": "Chats are saved to your account.",
}

_HI_W11 = {
    "chats_heading": "तुम्हारी चैट्स",
    "chats_search_placeholder": "अपनी चैट खोजो",
    "chats_new": "नई चैट",
    "chats_new_label": "नई चैट",
    "chats_open_label": "सारी चैट्स",
    "chats_count_label": "{count} चैट्स",
    "chats_open_now": "अभी खुली है",
    "chats_answer_snippet": "Ganitra का जवाब",
    "chats_no_results": "तुम्हारी खोज से कोई चैट नहीं मिली।",
    "chats_none_yet": "अभी कोई चैट नहीं — + दबाकर अपनी पहली चैट "
                      "शुरू करो!",
    "chats_close_one_label": "यह चैट बंद करो",
    "chats_delete_confirm": "यह चैट हटा दें? इसके सवाल और जवाब "
                            "चले जाएँगे।",
    "chats_close_all": "सारी चैट्स बंद करो",
    "chats_close_all_confirm": "तुम्हारी सारी चैट्स बंद कर दें? "
                               "हर चैट के सवाल-जवाब चले जाएँगे।",
    "chats_menu_label": "और विकल्प",
    "chats_view_label": "ग्रिड या सूची दृश्य",
    "file_btn": "📎 फ़ाइल चुनो",
    "js_chats_saved_note": "चैट्स तुम्हारे खाते में सहेजी जाती हैं।",
}

_BN_W11 = {
    "chats_heading": "তোমার চ্যাটগুলো",
    "chats_search_placeholder": "তোমার চ্যাট খোঁজো",
    "chats_new": "নতুন চ্যাট",
    "chats_new_label": "নতুন চ্যাট",
    "chats_open_label": "সব চ্যাট",
    "chats_count_label": "{count}টি চ্যাট",
    "chats_open_now": "এখন খোলা আছে",
    "chats_answer_snippet": "Ganitra-র উত্তর",
    "chats_no_results": "তোমার খোঁজের সঙ্গে কোনো চ্যাট মেলেনি।",
    "chats_none_yet": "এখনো কোনো চ্যাট নেই — + চেপে তোমার প্রথম "
                      "চ্যাট শুরু করো!",
    "chats_close_one_label": "এই চ্যাটটি বন্ধ করো",
    "chats_delete_confirm": "এই চ্যাটটি মুছে ফেলবে? এর প্রশ্ন ও "
                            "উত্তর চলে যাবে।",
    "chats_close_all": "সব চ্যাট বন্ধ করো",
    "chats_close_all_confirm": "তোমার সব চ্যাট বন্ধ করবে? প্রতিটি "
                               "চ্যাটের প্রশ্ন ও উত্তর চলে যাবে।",
    "chats_menu_label": "আরও বিকল্প",
    "chats_view_label": "গ্রিড বা তালিকা দৃশ্য",
    "file_btn": "📎 ফাইল বেছে নাও",
    "js_chats_saved_note": "চ্যাটগুলো তোমার অ্যাকাউন্টে সংরক্ষিত হয়।",
}

_MR_W11 = {
    "chats_heading": "तुमच्या चॅट्स",
    "chats_search_placeholder": "तुमच्या चॅट्स शोधा",
    "chats_new": "नवीन चॅट",
    "chats_new_label": "नवीन चॅट",
    "chats_open_label": "सर्व चॅट्स",
    "chats_count_label": "{count} चॅट्स",
    "chats_open_now": "आता उघडी आहे",
    "chats_answer_snippet": "Ganitra चे उत्तर",
    "chats_no_results": "तुमच्या शोधाशी कोणतीही चॅट जुळली नाही.",
    "chats_none_yet": "अजून एकही चॅट नाही — + दाबून तुमची पहिली "
                      "चॅट सुरू करा!",
    "chats_close_one_label": "ही चॅट बंद करा",
    "chats_delete_confirm": "ही चॅट हटवायची? तिचे प्रश्न आणि "
                            "उत्तरे जातील.",
    "chats_close_all": "सर्व चॅट्स बंद करा",
    "chats_close_all_confirm": "तुमच्या सर्व चॅट्स बंद करायच्या? "
                               "प्रत्येक चॅटचे प्रश्न-उत्तरे जातील.",
    "chats_menu_label": "अधिक पर्याय",
    "chats_view_label": "ग्रिड किंवा यादी दृश्य",
    "file_btn": "📎 फाइल निवडा",
    "js_chats_saved_note": "चॅट्स तुमच्या खात्यात जतन होतात.",
}

_TA_W11 = {
    "chats_heading": "உங்கள் அரட்டைகள்",
    "chats_search_placeholder": "உங்கள் அரட்டைகளைத் தேடுங்கள்",
    "chats_new": "புதிய அரட்டை",
    "chats_new_label": "புதிய அரட்டை",
    "chats_open_label": "எல்லா அரட்டைகளும்",
    "chats_count_label": "{count} அரட்டைகள்",
    "chats_open_now": "இப்போது திறந்துள்ளது",
    "chats_answer_snippet": "Ganitra-வின் பதில்",
    "chats_no_results": "உங்கள் தேடலுடன் எந்த அரட்டையும் "
                        "பொருந்தவில்லை.",
    "chats_none_yet": "இன்னும் அரட்டைகள் இல்லை — + ஐத் தட்டி "
                      "உங்கள் முதல் அரட்டையைத் தொடங்குங்கள்!",
    "chats_close_one_label": "இந்த அரட்டையை மூடு",
    "chats_delete_confirm": "இந்த அரட்டையை நீக்கவா? அதன் "
                            "கேள்விகளும் பதில்களும் போய்விடும்.",
    "chats_close_all": "எல்லா அரட்டைகளையும் மூடு",
    "chats_close_all_confirm": "உங்கள் எல்லா அரட்டைகளையும் "
                               "மூடவா? ஒவ்வொரு அரட்டையின் "
                               "கேள்விகளும் பதில்களும் போய்விடும்.",
    "chats_menu_label": "மேலும் விருப்பங்கள்",
    "chats_view_label": "கட்டம் அல்லது பட்டியல் காட்சி",
    "file_btn": "📎 கோப்பைத் தேர்ந்தெடு",
    "js_chats_saved_note": "அரட்டைகள் உங்கள் கணக்கில் "
                           "சேமிக்கப்படுகின்றன.",
}

_TE_W11 = {
    "chats_heading": "మీ చాట్‌లు",
    "chats_search_placeholder": "మీ చాట్‌లను వెతకండి",
    "chats_new": "కొత్త చాట్",
    "chats_new_label": "కొత్త చాట్",
    "chats_open_label": "అన్ని చాట్‌లు",
    "chats_count_label": "{count} చాట్‌లు",
    "chats_open_now": "ఇప్పుడు తెరిచి ఉంది",
    "chats_answer_snippet": "Ganitra సమాధానం",
    "chats_no_results": "మీ శోధనకు ఏ చాట్ సరిపోలలేదు.",
    "chats_none_yet": "ఇంకా చాట్‌లు లేవు — + నొక్కి మీ మొదటి "
                      "చాట్‌ను ప్రారంభించండి!",
    "chats_close_one_label": "ఈ చాట్‌ను మూసివేయి",
    "chats_delete_confirm": "ఈ చాట్‌ను తొలగించాలా? దాని "
                            "ప్రశ్నలు, సమాధానాలు పోతాయి.",
    "chats_close_all": "అన్ని చాట్‌లను మూసివేయి",
    "chats_close_all_confirm": "మీ అన్ని చాట్‌లను మూసివేయాలా? "
                               "ప్రతి చాట్ ప్రశ్నలు, సమాధానాలు "
                               "పోతాయి.",
    "chats_menu_label": "మరిన్ని ఎంపికలు",
    "chats_view_label": "గ్రిడ్ లేదా జాబితా వీక్షణ",
    "file_btn": "📎 ఫైల్‌ను ఎంచుకోండి",
    "js_chats_saved_note": "చాట్‌లు మీ ఖాతాలో సేవ్ అవుతాయి.",
}

STRINGS["en"].update(_EN_W11)
STRINGS["hi"].update(_HI_W11)
STRINGS["bn"].update(_BN_W11)
STRINGS["mr"].update(_MR_W11)
STRINGS["ta"].update(_TA_W11)
STRINGS["te"].update(_TE_W11)

# --- Wave 12 additions: menu-inside package + My Account + methods --------
# Suraj's approved full-page menu (LinkedIn-style): the profile block
# links to the new My Account page, where the student can change
# EVERYTHING (name, class, board, the 3 favourite things, password)
# and add his own photo. Log out lives ONLY on that page. The menu
# also carries the real stats lines ("{n} questions solved",
# "{n} chats") filled from /account/stats.json. The mm_* keys label
# the Wave-12 multi-method chips on chat bubbles and the answer
# page. Every key exists in all 6 languages.
_EN_W12 = {
    "acct_heading": "My Account",
    "acct_student_line": "Class {class} Student",
    "acct_stats_questions": "{count} questions solved",
    "acct_stats_chats": "{count} chats",
    "acct_verified_line": "Ganitra Maths student",
    "acct_questions_word": "questions solved",
    "acct_chats_word": "chats",
    "menu_new_here": "New chat",
    "menu_keep_line": "Keep learning, keep shining",
    "menu_settings": "Settings",
    "menu_language": "Language",
    "menu_copy_style": "Copy Style",
    "menu_your_chats": "Your chats",
    "mm_more": "More methods",
    "mm_more_prefix": "More methods available —",
    "mm_methods_suffix": "more ways to solve this",
    "mm_other_heading": "Other methods:",
    "mm_method_label": "Method",
    "mm_method_word": "method",
    "mm_listen": "Listen",
    "mm_suno": "Listen",
    "mm_teach_btn": "Teach me",
    "mm_teacher_mode": "Teacher mode",
    "mm_solve_btn": "Solve",
    "mm_solution_label": "Solution",
    "mm_steps_word": "steps",
    "field_name": "Name",
    "field_class": "Class",
    "field_board": "Board",
    "field_goal": "My Goal",
    "field_hobby": "My Hobby",
    "field_favourite": "My Favourite",
    "field_password": "Password",
    "field_old_password": "Old password",
    "field_new_password": "New password",
    "acct_edit_btn": "Edit",
    "acct_save_btn": "Save changes",
    "acct_change_btn": "Change",
    "acct_change_photo": "Change photo",
    "acct_upload_photo": "Upload photo",
    "acct_remove_photo": "Remove photo",
    "acct_saved_note": "Saved ✓",
    "acct_current_password_label": "Current password",
    "acct_photo_hint": "PNG or JPG, up to 2 MB",
    "acct_err_required": "Please fill this in.",
    "acct_err_photo_type": "Please choose a PNG or JPG photo.",
    "acct_err_photo_size": "That photo is too big — please pick "
                           "one under 2 MB.",
    "acct_err_password_wrong": "That password did not match. "
                               "Please check and try again.",
    "acct_err_old_password": "Please type your current password "
                             "first.",
}

_HI_W12 = {
    "acct_heading": "मेरा खाता",
    "acct_student_line": "कक्षा {class} का छात्र",
    "acct_stats_questions": "{count} सवाल हल किए",
    "acct_stats_chats": "{count} चैट्स",
    "acct_verified_line": "Ganitra Maths का छात्र",
    "acct_questions_word": "सवाल हल किए",
    "acct_chats_word": "चैट्स",
    "menu_new_here": "नई चैट",
    "menu_keep_line": "पढ़ते रहो, चमकते रहो",
    "menu_settings": "सेटिंग्स",
    "menu_language": "भाषा",
    "menu_copy_style": "कॉपी स्टाइल",
    "menu_your_chats": "तुम्हारी चैट्स",
    "mm_more": "और तरीक़े",
    "mm_more_prefix": "और तरीक़े उपलब्ध हैं —",
    "mm_methods_suffix": "इसे हल करने के और तरीक़े",
    "mm_other_heading": "दूसरे तरीक़े:",
    "mm_method_label": "तरीक़ा",
    "mm_method_word": "तरीक़ा",
    "mm_listen": "सुनो",
    "mm_suno": "सुनो",
    "mm_teach_btn": "मुझे पढ़ाओ",
    "mm_teacher_mode": "टीचर मोड",
    "mm_solve_btn": "हल करो",
    "mm_solution_label": "हल",
    "mm_steps_word": "कदम",
    "field_name": "नाम",
    "field_class": "कक्षा",
    "field_board": "बोर्ड",
    "field_goal": "मेरा लक्ष्य",
    "field_hobby": "मेरा शौक",
    "field_favourite": "मेरी पसंदीदा चीज़",
    "field_password": "पासवर्ड",
    "field_old_password": "पुराना पासवर्ड",
    "field_new_password": "नया पासवर्ड",
    "acct_edit_btn": "बदलो",
    "acct_save_btn": "बदलाव सहेजो",
    "acct_change_btn": "बदलो",
    "acct_change_photo": "फ़ोटो बदलो",
    "acct_upload_photo": "फ़ोटो लगाओ",
    "acct_remove_photo": "फ़ोटो हटाओ",
    "acct_saved_note": "सहेजा गया ✓",
    "acct_current_password_label": "मौजूदा पासवर्ड",
    "acct_photo_hint": "PNG या JPG, 2 MB तक",
    "acct_err_required": "कृपया यह भर दो।",
    "acct_err_photo_type": "कृपया PNG या JPG फ़ोटो चुनो।",
    "acct_err_photo_size": "यह फ़ोटो बहुत बड़ी है — 2 MB से छोटी "
                           "फ़ोटो चुनो।",
    "acct_err_password_wrong": "यह पासवर्ड मेल नहीं खाया। जाँचकर "
                               "फिर कोशिश करो।",
    "acct_err_old_password": "पहले अपना मौजूदा पासवर्ड लिखो।",
}

_BN_W12 = {
    "acct_heading": "আমার অ্যাকাউন্ট",
    "acct_student_line": "{class} শ্রেণির ছাত্র",
    "acct_stats_questions": "{count}টি প্রশ্ন সমাধান হয়েছে",
    "acct_stats_chats": "{count}টি চ্যাট",
    "acct_verified_line": "Ganitra Maths-এর ছাত্র",
    "acct_questions_word": "প্রশ্ন সমাধান হয়েছে",
    "acct_chats_word": "চ্যাট",
    "menu_new_here": "নতুন চ্যাট",
    "menu_keep_line": "শিখতে থাকো, উজ্জ্বল হতে থাকো",
    "menu_settings": "সেটিংস",
    "menu_language": "ভাষা",
    "menu_copy_style": "কপি স্টাইল",
    "menu_your_chats": "তোমার চ্যাটগুলো",
    "mm_more": "আরও পদ্ধতি",
    "mm_more_prefix": "আরও পদ্ধতি আছে —",
    "mm_methods_suffix": "এটি সমাধানের আরও উপায়",
    "mm_other_heading": "অন্যান্য পদ্ধতি:",
    "mm_method_label": "পদ্ধতি",
    "mm_method_word": "পদ্ধতি",
    "mm_listen": "শোনো",
    "mm_suno": "শোনো",
    "mm_teach_btn": "আমাকে শেখাও",
    "mm_teacher_mode": "শিক্ষক মোড",
    "mm_solve_btn": "সমাধান করো",
    "mm_solution_label": "সমাধান",
    "mm_steps_word": "ধাপ",
    "field_name": "নাম",
    "field_class": "শ্রেণি",
    "field_board": "বোর্ড",
    "field_goal": "আমার লক্ষ্য",
    "field_hobby": "আমার শখ",
    "field_favourite": "আমার প্রিয় জিনিস",
    "field_password": "পাসওয়ার্ড",
    "field_old_password": "পুরোনো পাসওয়ার্ড",
    "field_new_password": "নতুন পাসওয়ার্ড",
    "acct_edit_btn": "বদলাও",
    "acct_save_btn": "পরিবর্তন সংরক্ষণ করো",
    "acct_change_btn": "বদলাও",
    "acct_change_photo": "ছবি বদলাও",
    "acct_upload_photo": "ছবি দাও",
    "acct_remove_photo": "ছবি সরাও",
    "acct_saved_note": "সংরক্ষিত হয়েছে ✓",
    "acct_current_password_label": "বর্তমান পাসওয়ার্ড",
    "acct_photo_hint": "PNG বা JPG, 2 MB পর্যন্ত",
    "acct_err_required": "অনুগ্রহ করে এটি পূরণ করো।",
    "acct_err_photo_type": "অনুগ্রহ করে PNG বা JPG ছবি বেছে নাও।",
    "acct_err_photo_size": "এই ছবিটি খুব বড় — 2 MB-এর ছোট ছবি "
                           "বেছে নাও।",
    "acct_err_password_wrong": "পাসওয়ার্ডটি মেলেনি। যাচাই করে "
                               "আবার চেষ্টা করো।",
    "acct_err_old_password": "আগে তোমার বর্তমান পাসওয়ার্ড লেখো।",
}

_MR_W12 = {
    "acct_heading": "माझे खाते",
    "acct_student_line": "इयत्ता {class} चा विद्यार्थी",
    "acct_stats_questions": "{count} प्रश्न सोडवले",
    "acct_stats_chats": "{count} चॅट्स",
    "acct_verified_line": "Ganitra Maths चा विद्यार्थी",
    "acct_questions_word": "प्रश्न सोडवले",
    "acct_chats_word": "चॅट्स",
    "menu_new_here": "नवीन चॅट",
    "menu_keep_line": "शिकत राहा, चमकत राहा",
    "menu_settings": "सेटिंग्ज",
    "menu_language": "भाषा",
    "menu_copy_style": "कॉपी स्टाइल",
    "menu_your_chats": "तुमच्या चॅट्स",
    "mm_more": "आणखी पद्धती",
    "mm_more_prefix": "आणखी पद्धती उपलब्ध आहेत —",
    "mm_methods_suffix": "हे सोडवण्याचे आणखी मार्ग",
    "mm_other_heading": "इतर पद्धती:",
    "mm_method_label": "पद्धत",
    "mm_method_word": "पद्धत",
    "mm_listen": "ऐका",
    "mm_suno": "ऐका",
    "mm_teach_btn": "मला शिकवा",
    "mm_teacher_mode": "शिक्षक मोड",
    "mm_solve_btn": "सोडवा",
    "mm_solution_label": "उत्तर",
    "mm_steps_word": "पायऱ्या",
    "field_name": "नाव",
    "field_class": "इयत्ता",
    "field_board": "बोर्ड",
    "field_goal": "माझे ध्येय",
    "field_hobby": "माझा छंद",
    "field_favourite": "माझी आवडती गोष्ट",
    "field_password": "पासवर्ड",
    "field_old_password": "जुना पासवर्ड",
    "field_new_password": "नवीन पासवर्ड",
    "acct_edit_btn": "बदला",
    "acct_save_btn": "बदल जतन करा",
    "acct_change_btn": "बदला",
    "acct_change_photo": "फोटो बदला",
    "acct_upload_photo": "फोटो लावा",
    "acct_remove_photo": "फोटो काढा",
    "acct_saved_note": "जतन झाले ✓",
    "acct_current_password_label": "सध्याचा पासवर्ड",
    "acct_photo_hint": "PNG किंवा JPG, 2 MB पर्यंत",
    "acct_err_required": "कृपया हे भरा.",
    "acct_err_photo_type": "कृपया PNG किंवा JPG फोटो निवडा.",
    "acct_err_photo_size": "हा फोटो खूप मोठा आहे — 2 MB पेक्षा "
                           "लहान फोटो निवडा.",
    "acct_err_password_wrong": "पासवर्ड जुळला नाही. तपासून "
                               "पुन्हा प्रयत्न करा.",
    "acct_err_old_password": "आधी तुमचा सध्याचा पासवर्ड लिहा.",
}

_TA_W12 = {
    "acct_heading": "என் கணக்கு",
    "acct_student_line": "{class} ஆம் வகுப்பு மாணவன்",
    "acct_stats_questions": "{count} கேள்விகள் தீர்க்கப்பட்டன",
    "acct_stats_chats": "{count} அரட்டைகள்",
    "acct_verified_line": "Ganitra Maths மாணவன்",
    "acct_questions_word": "கேள்விகள் தீர்க்கப்பட்டன",
    "acct_chats_word": "அரட்டைகள்",
    "menu_new_here": "புதிய அரட்டை",
    "menu_keep_line": "கற்றுக்கொண்டே இரு, ஒளிர்ந்துகொண்டே இரு",
    "menu_settings": "அமைப்புகள்",
    "menu_language": "மொழி",
    "menu_copy_style": "நகல் பாணி",
    "menu_your_chats": "உங்கள் அரட்டைகள்",
    "mm_more": "மேலும் முறைகள்",
    "mm_more_prefix": "மேலும் முறைகள் உள்ளன —",
    "mm_methods_suffix": "இதைத் தீர்க்க மேலும் வழிகள்",
    "mm_other_heading": "பிற முறைகள்:",
    "mm_method_label": "முறை",
    "mm_method_word": "முறை",
    "mm_listen": "கேளுங்கள்",
    "mm_suno": "கேளுங்கள்",
    "mm_teach_btn": "எனக்குக் கற்பியுங்கள்",
    "mm_teacher_mode": "ஆசிரியர் முறை",
    "mm_solve_btn": "தீர்வு காண்",
    "mm_solution_label": "தீர்வு",
    "mm_steps_word": "படிகள்",
    "field_name": "பெயர்",
    "field_class": "வகுப்பு",
    "field_board": "வாரியம்",
    "field_goal": "என் இலக்கு",
    "field_hobby": "என் பொழுதுபோக்கு",
    "field_favourite": "எனக்கு மிகவும் பிடித்தது",
    "field_password": "கடவுச்சொல்",
    "field_old_password": "பழைய கடவுச்சொல்",
    "field_new_password": "புதிய கடவுச்சொல்",
    "acct_edit_btn": "திருத்து",
    "acct_save_btn": "மாற்றங்களைச் சேமி",
    "acct_change_btn": "மாற்று",
    "acct_change_photo": "புகைப்படத்தை மாற்று",
    "acct_upload_photo": "புகைப்படம் சேர்",
    "acct_remove_photo": "புகைப்படத்தை நீக்கு",
    "acct_saved_note": "சேமிக்கப்பட்டது ✓",
    "acct_current_password_label": "தற்போதைய கடவுச்சொல்",
    "acct_photo_hint": "PNG அல்லது JPG, 2 MB வரை",
    "acct_err_required": "தயவுசெய்து இதை நிரப்புங்கள்.",
    "acct_err_photo_type": "தயவுசெய்து PNG அல்லது JPG "
                           "புகைப்படத்தைத் தேர்ந்தெடுங்கள்.",
    "acct_err_photo_size": "இந்தப் புகைப்படம் மிகப் பெரியது — "
                           "2 MB க்கும் குறைவான ஒன்றைத் "
                           "தேர்ந்தெடுங்கள்.",
    "acct_err_password_wrong": "கடவுச்சொல் பொருந்தவில்லை. "
                               "சரிபார்த்து மீண்டும் முயற்சிக்கவும்.",
    "acct_err_old_password": "முதலில் உங்கள் தற்போதைய "
                             "கடவுச்சொல்லை எழுதுங்கள்.",
}

_TE_W12 = {
    "acct_heading": "నా ఖాతా",
    "acct_student_line": "{class}వ తరగతి విద్యార్థి",
    "acct_stats_questions": "{count} ప్రశ్నలు పరిష్కరించబడ్డాయి",
    "acct_stats_chats": "{count} చాట్‌లు",
    "acct_verified_line": "Ganitra Maths విద్యార్థి",
    "acct_questions_word": "ప్రశ్నలు పరిష్కరించబడ్డాయి",
    "acct_chats_word": "చాట్‌లు",
    "menu_new_here": "కొత్త చాట్",
    "menu_keep_line": "నేర్చుకుంటూ ఉండండి, మెరుస్తూ ఉండండి",
    "menu_settings": "సెట్టింగ్‌లు",
    "menu_language": "భాష",
    "menu_copy_style": "కాపీ స్టైల్",
    "menu_your_chats": "మీ చాట్‌లు",
    "mm_more": "మరిన్ని పద్ధతులు",
    "mm_more_prefix": "మరిన్ని పద్ధతులు అందుబాటులో ఉన్నాయి —",
    "mm_methods_suffix": "దీన్ని పరిష్కరించే మరిన్ని మార్గాలు",
    "mm_other_heading": "ఇతర పద్ధతులు:",
    "mm_method_label": "పద్ధతి",
    "mm_method_word": "పద్ధతి",
    "mm_listen": "వినండి",
    "mm_suno": "వినండి",
    "mm_teach_btn": "నాకు నేర్పించండి",
    "mm_teacher_mode": "టీచర్ మోడ్",
    "mm_solve_btn": "పరిష్కరించు",
    "mm_solution_label": "పరిష్కారం",
    "mm_steps_word": "దశలు",
    "field_name": "పేరు",
    "field_class": "తరగతి",
    "field_board": "బోర్డు",
    "field_goal": "నా లక్ష్యం",
    "field_hobby": "నా అభిరుచి",
    "field_favourite": "నాకు అత్యంత ఇష్టమైనది",
    "field_password": "పాస్‌వర్డ్",
    "field_old_password": "పాత పాస్‌వర్డ్",
    "field_new_password": "కొత్త పాస్‌వర్డ్",
    "acct_edit_btn": "మార్చు",
    "acct_save_btn": "మార్పులను సేవ్ చేయి",
    "acct_change_btn": "మార్చు",
    "acct_change_photo": "ఫోటో మార్చు",
    "acct_upload_photo": "ఫోటో పెట్టు",
    "acct_remove_photo": "ఫోటో తీసెయ్",
    "acct_saved_note": "సేవ్ అయింది ✓",
    "acct_current_password_label": "ప్రస్తుత పాస్‌వర్డ్",
    "acct_photo_hint": "PNG లేదా JPG, 2 MB వరకు",
    "acct_err_required": "దయచేసి ఇది నింపండి.",
    "acct_err_photo_type": "దయచేసి PNG లేదా JPG ఫోటోను "
                           "ఎంచుకోండి.",
    "acct_err_photo_size": "ఆ ఫోటో చాలా పెద్దది — 2 MB కంటే "
                           "తక్కువది ఎంచుకోండి.",
    "acct_err_password_wrong": "పాస్‌వర్డ్ సరిపోలలేదు. సరిచూసి "
                               "మళ్లీ ప్రయత్నించండి.",
    "acct_err_old_password": "ముందు మీ ప్రస్తుత పాస్‌వర్డ్ "
                             "రాయండి.",
}

STRINGS["en"].update(_EN_W12)
STRINGS["hi"].update(_HI_W12)
STRINGS["bn"].update(_BN_W12)
STRINGS["mr"].update(_MR_W12)
STRINGS["ta"].update(_TA_W12)
STRINGS["te"].update(_TE_W12)


# ---------------------------------------------------------------------------
# Wave 12: "Teach me" — short teacher-style concept lines per topic.
#
# TEACH[lang][key] is a list of 3-5 short lines: what the question
# type is really asking, the key idea/formula in words, one line of
# guidance for the steps above, and a tiny practice line. Lookup
# mirrors explanation_for: "type:op" -> "type" -> "generic".
# Full content exists for en + hi; the other four languages fall
# back to the English lines (same documented fallback style as
# get_strings merging English underneath).
# ---------------------------------------------------------------------------

TEACH = {
    "en": {
        "algebra:equation": [
            "An equation is a balance: both sides must stay equal, "
            "like the two pans of a weighing scale.",
            "Whatever you do to one side, do the same to the other "
            "side — that is the whole secret.",
            "Bring the letter (variable) alone on one side, step by "
            "step, and the number on the other side is your answer.",
            "Quick check: put the answer back into the question — "
            "both sides should come out equal.",
            "Practice: try solving 3x + 4 = 19 the same way.",
        ],
        "algebra": [
            "Algebra is arithmetic with a letter standing in for a "
            "number you do not know yet.",
            "Treat the letter like a hidden number: collect its "
            "terms together and simplify slowly.",
            "Work bracket by bracket, and keep every '=' line "
            "balanced — nothing appears or disappears for free.",
            "Practice: simplify 2(x + 3) + 4x on your own first.",
        ],
        "arithmetic:percentage": [
            "Percent simply means 'out of 100' — 15% is 15 out of "
            "every 100.",
            "To find a percentage of a number, change the percent "
            "into a fraction (15% = 15/100) and multiply.",
            "The unitary way also works: find 1% first, then "
            "multiply by how many percent you need.",
            "Practice: find 20% of 150 using both ways.",
        ],
        "arithmetic": [
            "Arithmetic questions are solved in a fixed order — "
            "BODMAS: Brackets, Orders (powers), Division and "
            "Multiplication, then Addition and Subtraction.",
            "Do one small step at a time and rewrite the whole line "
            "after each step; most mistakes come from rushing.",
            "Equal-priority steps (x and ÷, + and -) are done left "
            "to right.",
            "Practice: work out 6 + 2 x 3 - remembering the order!",
        ],
        "calculus": [
            "Calculus studies change: a derivative measures how "
            "fast something is changing at one exact moment.",
            "For x^n the rule is friendly: bring the power down and "
            "reduce the power by 1 (x^3 becomes 3x^2).",
            "Integration is the reverse journey — it collects "
            "change back into a total, like area under a curve.",
            "Practice: differentiate x^4 using the power rule.",
        ],
        "trigonometry": [
            "Trigonometry links the angles of a triangle with the "
            "lengths of its sides.",
            "Remember SOH-CAH-TOA: sin = Opposite/Hypotenuse, "
            "cos = Adjacent/Hypotenuse, tan = Opposite/Adjacent.",
            "The famous values (0°, 30°, 45°, 60°, 90°) are worth "
            "learning by heart — exams love them.",
            "Practice: write sin, cos and tan for a 3-4-5 triangle.",
        ],
        "geometry": [
            "Geometry questions usually hide in one picture and one "
            "formula — draw the figure first, always.",
            "Write the formula down (area, perimeter, volume) "
            "before putting any numbers in.",
            "Keep the units with the numbers: cm for length, cm² "
            "for area, cm³ for volume.",
            "Practice: find the area of a circle with radius 7.",
        ],
        "statistics": [
            "Statistics turns a list of numbers into a story: its "
            "centre (mean, median, mode) and its spread.",
            "Mean = total of all values ÷ how many values there "
            "are. Median is the middle value after sorting.",
            "For probability: favourable outcomes ÷ total possible "
            "outcomes — count both carefully.",
            "Practice: find the mean and median of 2, 5, 5, 8, 10.",
        ],
        "generic": [
            "Every maths question has a pattern — first ask "
            "yourself: what is given, and what is being asked?",
            "Solve slowly, one honest step at a time, and write "
            "each step down; a written step can be checked, a "
            "rushed one cannot.",
            "When you get an answer, do a 10-second sense check: "
            "is it roughly the size you expected?",
            "Practice: re-solve this same question on paper "
            "without looking at the steps.",
        ],
    },
    "hi": {
        "algebra:equation": [
            "Equation ek tarazu jaisi hoti hai — dono taraf hamesha "
            "barabar rehna chahiye।",
            "Jo ek taraf karo, wahi dusri taraf bhi karo — yahi "
            "poora raaz hai।",
            "Akshar (variable) ko ek taraf akela karo, kadam-dar-"
            "kadam; dusri taraf bachi sankhya hi jawaab hai।",
            "Jaanch: jawaab ko sawaal me wapas rakho — dono taraf "
            "barabar aana chahiye।",
            "Abhyaas: 3x + 4 = 19 ko isi tareeke se hal karo।",
        ],
        "algebra": [
            "Algebra me ek akshar us sankhya ki jagah khada hota "
            "hai jo abhi pata nahi hai।",
            "Akshar ko chhupi hui sankhya samjho: uske hisse ek "
            "saath jodo aur dheere-dheere saral karo।",
            "Koshthak (bracket) ek-ek karke kholo, aur har '=' "
            "wali line ko santulit rakho।",
            "Abhyaas: 2(x + 3) + 4x ko khud saral karke dekho।",
        ],
        "arithmetic:percentage": [
            "Percent ka matlab hai 'har 100 me se' — 15% matlab "
            "har 100 me se 15।",
            "Kisi sankhya ka percent nikaalne ke liye percent ko "
            "bhinn (fraction) bana lo (15% = 15/100) aur guna kar "
            "do।",
            "Unitary tareeka bhi chalega: pehle 1% nikaalo, phir "
            "jitne percent chahiye utne se guna kar do।",
            "Abhyaas: 150 ka 20% dono tareeko se nikaalo।",
        ],
        "arithmetic": [
            "Arithmetic ke sawaal ek tay kram se bante hai — "
            "BODMAS: pehle koshthak, phir ghaat (powers), phir "
            "bhaag aur guna, aakhir me jod aur ghata।",
            "Ek baar me ek chhota kadam lo aur har kadam ke baad "
            "poori line dobara likho; galti aksar jaldi se hoti "
            "hai।",
            "Barabar mahatva wale kadam (x aur ÷, + aur -) baaye "
            "se daaye kiye jaate hai।",
            "Abhyaas: 6 + 2 x 3 ko kram yaad rakhkar hal karo!",
        ],
        "calculus": [
            "Calculus badlav ka adhyayan hai: derivative batata "
            "hai ki koi cheez ek pal me kitni tezi se badal rahi "
            "hai।",
            "x^n ke liye niyam aasan hai: ghaat ko neeche le aao "
            "aur ghaat 1 kam kar do (x^3 banta hai 3x^2)।",
            "Integration iski ulti yatra hai — badlav ko jodkar "
            "kul me badalna, jaise vakr ke neeche ka kshetrafal।",
            "Abhyaas: power rule se x^4 ka derivative nikaalo।",
        ],
        "trigonometry": [
            "Trigonometry tribhuj ke kono ko uski bhujaon ki "
            "lambai se jodti hai।",
            "SOH-CAH-TOA yaad rakho: sin = Lamb/Karn, cos = "
            "Aadhar/Karn, tan = Lamb/Aadhar।",
            "Khaas maan (0°, 30°, 45°, 60°, 90°) rat lene layak "
            "hai — pareeksha me aksar aate hai।",
            "Abhyaas: 3-4-5 wale tribhuj ke liye sin, cos, tan "
            "likho।",
        ],
        "geometry": [
            "Geometry ke sawaal aksar ek chitra aur ek sutra me "
            "chhupe hote hai — pehle aakriti banao, hamesha।",
            "Sankhyaye rakhne se pehle sutra (kshetrafal, parimap, "
            "aayatan) likh lo।",
            "Ikaai (unit) sankhya ke saath rakho: lambai cm, "
            "kshetrafal cm², aayatan cm³।",
            "Abhyaas: trijya 7 wale vritt ka kshetrafal nikaalo।",
        ],
        "statistics": [
            "Statistics sankhyao ki list ko ek kahani banati hai: "
            "uska kendra (mean, median, mode) aur uska phailav।",
            "Mean = saari sankhyao ka yog ÷ kul sankhyaye। "
            "Median kram me lagi list ka beech wala maan hai।",
            "Probability ke liye: anukool parinaam ÷ kul sambhav "
            "parinaam — dono dhyaan se gino।",
            "Abhyaas: 2, 5, 5, 8, 10 ka mean aur median nikaalo।",
        ],
        "generic": [
            "Har maths sawaal ka ek pattern hota hai — pehle khud "
            "se poochho: diya kya hai, aur poochha kya gaya hai?",
            "Dheere, ek-ek imandaar kadam se hal karo aur har "
            "kadam likho; likha hua kadam jaancha ja sakta hai, "
            "jaldi wala nahi।",
            "Jawaab milne par 10-second ki samajh-jaanch karo: "
            "kya ye lagbhag utna hi bada hai jitna socha tha?",
            "Abhyaas: isi sawaal ko kadam dekhe bina copy par "
            "dobara hal karo।",
        ],
    },
}


def teach_for(result, lang):
    """Wave 12 'Teach me': short teacher-style concept lines for a
    solver result. Lookup mirrors explanation_for ("type:op" ->
    "type" -> "generic"); languages without their own TEACH table
    use the English lines. Never raises; always returns a list."""
    try:
        result = result or {}
        rtype = result.get("type", "") or ""
        rop = result.get("op", "") or ""
        table = TEACH.get(lang) or TEACH["en"]
        fallback = TEACH["en"]
        lines = (table.get(f"{rtype}:{rop}") or table.get(rtype)
                 or fallback.get(f"{rtype}:{rop}")
                 or fallback.get(rtype) or fallback["generic"])
        return list(lines)
    except Exception:
        return list(TEACH["en"]["generic"])


# ---------------------------------------------------------------------------
# Wave 13: Classes 0-12 coverage expansion. Method labels for the
# new Wave-13 methods (plus bank entries for the Wave-12 ids) as
# STRINGS keys in all 6 languages — app.py already exposes every
# "mm_" key to the chat JS as js_t. Explanation and advice keys
# for the new "junior"/"applied" result types are added to ALL
# six tables because explanation/advice lookups require the key
# sets to stay identical across languages (verify_wave5 asserts
# this for ADVICE; the same discipline is kept for EXPLANATIONS).
# TEACH grows by update for en + hi only (other languages fall
# back to English lines — documented TEACH behaviour).
# ---------------------------------------------------------------------------

_EN_W13 = {
    "mm_label_transposition": "Transposition method",
    "mm_label_proportion": "Proportion method",
    "mm_label_yearly_breakup": "Year-by-year method",
    "mm_label_euclid": "Euclid's division method",
    "mm_label_hcf_relation": "Using the HCF relation",
    "mm_label_graph": "Graph method",
    "mm_label_half_rectangle": "Half of a rectangle method",
    "mm_label_listing": "Writing out the terms",
    "mm_label_assumed_mean": "Assumed mean method",
    "mm_label_factor": "Factorisation method",
    "mm_label_complete_square": "Completing the square",
    "mm_label_formula": "Quadratic formula",
    "mm_label_fraction": "Fraction method",
    "mm_label_unitary": "Unitary method",
    "mm_label_bodmas_grouped": "Step-by-step BODMAS",
}

_HI_W13 = {
    "mm_label_transposition": "स्थानांतरण विधि (Transposition)",
    "mm_label_proportion": "समानुपात विधि (Proportion)",
    "mm_label_yearly_breakup": "वर्ष-दर-वर्ष विधि",
    "mm_label_euclid": "यूक्लिड विभाजन विधि",
    "mm_label_hcf_relation": "HCF संबंध से",
    "mm_label_graph": "ग्राफ़ विधि",
    "mm_label_half_rectangle": "आयत के आधे वाली विधि",
    "mm_label_listing": "पद लिखकर निकालना",
    "mm_label_assumed_mean": "कल्पित माध्य विधि",
    "mm_label_factor": "गुणनखंड विधि",
    "mm_label_complete_square": "पूर्ण वर्ग विधि",
    "mm_label_formula": "द्विघात सूत्र",
    "mm_label_fraction": "भिन्न विधि",
    "mm_label_unitary": "ऐकिक विधि (Unitary)",
    "mm_label_bodmas_grouped": "चरण-दर-चरण BODMAS",
}

_BN_W13 = {
    "mm_label_transposition": "পক্ষান্তর পদ্ধতি (Transposition)",
    "mm_label_proportion": "সমানুপাত পদ্ধতি (Proportion)",
    "mm_label_yearly_breakup": "বছর-ধরে-বছর পদ্ধতি",
    "mm_label_euclid": "ইউক্লিডের ভাগ পদ্ধতি",
    "mm_label_hcf_relation": "HCF সম্পর্ক ব্যবহার করে",
    "mm_label_graph": "গ্রাফ পদ্ধতি",
    "mm_label_half_rectangle": "আয়তক্ষেত্রের অর্ধেক পদ্ধতি",
    "mm_label_listing": "পদগুলো লিখে বের করা",
    "mm_label_assumed_mean": "অনুমিত গড় পদ্ধতি",
    "mm_label_factor": "উৎপাদকে বিশ্লেষণ পদ্ধতি",
    "mm_label_complete_square": "পূর্ণবর্গ পদ্ধতি",
    "mm_label_formula": "দ্বিঘাত সূত্র",
    "mm_label_fraction": "ভগ্নাংশ পদ্ধতি",
    "mm_label_unitary": "ঐকিক পদ্ধতি (Unitary)",
    "mm_label_bodmas_grouped": "ধাপে ধাপে BODMAS",
}

_MR_W13 = {
    "mm_label_transposition": "पक्षांतर पद्धत (Transposition)",
    "mm_label_proportion": "प्रमाण पद्धत (Proportion)",
    "mm_label_yearly_breakup": "वर्ष-दर-वर्ष पद्धत",
    "mm_label_euclid": "युक्लिडची भागाकार पद्धत",
    "mm_label_hcf_relation": "HCF संबंध वापरून",
    "mm_label_graph": "आलेख पद्धत",
    "mm_label_half_rectangle": "आयताच्या निम्म्या भागाची पद्धत",
    "mm_label_listing": "पदे लिहून काढणे",
    "mm_label_assumed_mean": "गृहित मध्य पद्धत",
    "mm_label_factor": "अवयव पद्धत",
    "mm_label_complete_square": "पूर्ण वर्ग पद्धत",
    "mm_label_formula": "वर्ग सूत्र",
    "mm_label_fraction": "अपूर्णांक पद्धत",
    "mm_label_unitary": "एकक पद्धत (Unitary)",
    "mm_label_bodmas_grouped": "पायरी-पायरी BODMAS",
}

_TA_W13 = {
    "mm_label_transposition": "இடமாற்று முறை (Transposition)",
    "mm_label_proportion": "விகித முறை (Proportion)",
    "mm_label_yearly_breakup": "ஆண்டு வாரியான முறை",
    "mm_label_euclid": "யூக்ளிட் வகுத்தல் முறை",
    "mm_label_hcf_relation": "HCF தொடர்பைப் பயன்படுத்தி",
    "mm_label_graph": "வரைபட முறை",
    "mm_label_half_rectangle": "செவ்வகத்தின் பாதி முறை",
    "mm_label_listing": "உறுப்புகளை எழுதி காணுதல்",
    "mm_label_assumed_mean": "ஊக சராசரி முறை",
    "mm_label_factor": "காரணிப்படுத்தும் முறை",
    "mm_label_complete_square": "வர்க்கத்தை நிறைவு செய்தல்",
    "mm_label_formula": "இருபடி சூத்திரம்",
    "mm_label_fraction": "பின்ன முறை",
    "mm_label_unitary": "அலகு முறை (Unitary)",
    "mm_label_bodmas_grouped": "படிப்படியான BODMAS",
}

_TE_W13 = {
    "mm_label_transposition": "స్థానమార్పిడి పద్ధతి (Transposition)",
    "mm_label_proportion": "నిష్పత్తి పద్ధతి (Proportion)",
    "mm_label_yearly_breakup": "సంవత్సరాల వారీ పద్ధతి",
    "mm_label_euclid": "యూక్లిడ్ భాగహార పద్ధతి",
    "mm_label_hcf_relation": "HCF సంబంధం ఉపయోగించి",
    "mm_label_graph": "గ్రాఫ్ పద్ధతి",
    "mm_label_half_rectangle": "దీర్ఘచతురస్రంలో సగం పద్ధతి",
    "mm_label_listing": "పదాలను వ్రాసి కనుగొనడం",
    "mm_label_assumed_mean": "ఊహించిన సగటు పద్ధతి",
    "mm_label_factor": "కారణాంక పద్ధతి",
    "mm_label_complete_square": "వర్గాన్ని పూర్తి చేయడం",
    "mm_label_formula": "వర్గ సూత్రం",
    "mm_label_fraction": "భిన్న పద్ధతి",
    "mm_label_unitary": "ఏకక పద్ధతి (Unitary)",
    "mm_label_bodmas_grouped": "దశలవారీ BODMAS",
}

STRINGS["en"].update(_EN_W13)
STRINGS["hi"].update(_HI_W13)
STRINGS["bn"].update(_BN_W13)
STRINGS["mr"].update(_MR_W13)
STRINGS["ta"].update(_TA_W13)
STRINGS["te"].update(_TE_W13)

# --- Explanations for the new types (all 6 languages) ---------
_EXPLAIN_W13 = {
    "en": {
        "junior": "Here is the junior maths answer: {answer} — "
                  "the steps above show the counting and working.",
        "applied": "Working it out step by step gives {answer} — "
                   "see the steps above.",
        "algebra:discriminant": "The discriminant of the quadratic "
                                "is {answer} — the steps above show "
                                "b^2 - 4ac being worked out.",
        "algebra:nature_of_roots": "Looking at the discriminant, "
                                   "the roots are: {answer} — see "
                                   "the steps above.",
    },
    "hi": {
        "junior": "छोटी कक्षाओं के गणित का उत्तर है: {answer} — "
                  "गिनती और काम ऊपर के चरणों में दिखाया गया है।",
        "applied": "चरण-दर-चरण हल करने पर मिलता है {answer} — "
                   "ऊपर के चरण देखें।",
        "algebra:discriminant": "द्विघात समीकरण का विविक्तकर "
                                "(discriminant) {answer} है — ऊपर "
                                "b^2 - 4ac का काम दिखाया गया है।",
        "algebra:nature_of_roots": "विविक्तकर को देखकर, मूल हैं: "
                                   "{answer} — ऊपर के चरण देखें।",
    },
    "bn": {
        "junior": "ছোটোদের গণিতের উত্তর হলো: {answer} — গণনা ও "
                  "কাজ উপরের ধাপগুলোতে দেখানো হয়েছে।",
        "applied": "ধাপে ধাপে করলে পাওয়া যায় {answer} — উপরের "
                   "ধাপগুলো দেখুন।",
        "algebra:discriminant": "দ্বিঘাত সমীকরণের নিশ্চায়ক "
                                "(discriminant) হলো {answer} — "
                                "উপরে b^2 - 4ac-এর কাজ দেখানো "
                                "হয়েছে।",
        "algebra:nature_of_roots": "নিশ্চায়ক দেখে, মূলগুলো হলো: "
                                   "{answer} — উপরের ধাপগুলো "
                                   "দেখুন।",
    },
    "mr": {
        "junior": "लहान वर्गांच्या गणिताचे उत्तर आहे: {answer} — "
                  "मोजणी आणि काम वरील पायऱ्यांमध्ये दाखवले आहे।",
        "applied": "पायरी-पायरीने केल्यावर मिळते {answer} — वरील "
                   "पायऱ्या पहा।",
        "algebra:discriminant": "वर्ग समीकरणाचा विवेचक "
                                "(discriminant) {answer} आहे — "
                                "वर b^2 - 4ac चे काम दाखवले आहे।",
        "algebra:nature_of_roots": "विवेचक पाहता, मुळे आहेत: "
                                   "{answer} — वरील पायऱ्या पहा।",
    },
    "ta": {
        "junior": "சிறுவர் கணித விடை: {answer} — எண்ணுதலும் "
                  "செயல்முறையும் மேலே உள்ள படிகளில் "
                  "காட்டப்பட்டுள்ளது।",
        "applied": "படிப்படியாகச் செய்தால் கிடைப்பது {answer} — "
                   "மேலே உள்ள படிகளைப் பாருங்கள்।",
        "algebra:discriminant": "இருபடிச் சமன்பாட்டின் பகுத்தறி "
                                "(discriminant) {answer} — மேலே "
                                "b^2 - 4ac கணக்கு "
                                "காட்டப்பட்டுள்ளது।",
        "algebra:nature_of_roots": "பகுத்தறியைப் பார்த்தால், "
                                   "மூலங்கள்: {answer} — மேலே "
                                   "உள்ள படிகளைப் பாருங்கள்।",
    },
    "te": {
        "junior": "చిన్న తరగతుల గణిత జవాబు: {answer} — లెక్కింపు "
                  "మరియు పని పై దశలలో చూపబడింది।",
        "applied": "దశలవారీగా చేస్తే వచ్చేది {answer} — పై "
                   "దశలను చూడండి।",
        "algebra:discriminant": "వర్గ సమీకరణం యొక్క వివక్షత "
                                "(discriminant) {answer} — పైన "
                                "b^2 - 4ac పని చూపబడింది।",
        "algebra:nature_of_roots": "వివక్షతను చూస్తే, మూలాలు: "
                                   "{answer} — పై దశలను చూడండి।",
    },
}
for _code, _extra in _EXPLAIN_W13.items():
    EXPLANATIONS[_code].update(_extra)

# --- Advice for the new types (all 6 languages) ---------------
_ADVICE_W13 = {
    "en": {
        "junior": "For little learners: count slowly, use your "
                  "fingers or draw the objects — a picture makes "
                  "every story sum easy.",
        "applied": "Applied sums always start from what one unit "
                   "is worth — find the value of 1 first, then "
                   "scale up.",
        "word_problem": "Read the story twice: once for the "
                        "story, once to underline the numbers and "
                        "what is being asked.",
    },
    "hi": {
        "junior": "छोटे छात्रों के लिए: धीरे-धीरे गिनो, उंगलियों "
                  "का उपयोग करो या वस्तुएँ बनाकर देखो — तस्वीर से "
                  "हर कहानी वाला सवाल आसान हो जाता है।",
        "applied": "ऐसे सवाल हमेशा एक इकाई के मान से शुरू होते "
                   "हैं — पहले 1 का मान निकालो, फिर बढ़ाओ।",
        "word_problem": "कहानी को दो बार पढ़ो: एक बार कहानी के "
                        "लिए, दूसरी बार संख्याओं और पूछी गई बात "
                        "को रेखांकित करने के लिए।",
    },
    "bn": {
        "junior": "ছোটো শিক্ষার্থীদের জন্য: ধীরে ধীরে গুনো, "
                  "আঙুল ব্যবহার করো বা জিনিসগুলো এঁকে দেখো — "
                  "ছবি আঁকলে প্রতিটি গল্পের অঙ্ক সহজ হয়ে যায়।",
        "applied": "এমন অঙ্ক সবসময় এক এককের মান থেকে শুরু হয় — "
                   "আগে 1-এর মান বের করো, তারপর বাড়াও।",
        "word_problem": "গল্পটি দুবার পড়ো: একবার গল্পের জন্য, "
                        "আরেকবার সংখ্যা ও যা জানতে চাওয়া হয়েছে "
                        "তা দাগ দেওয়ার জন্য।",
    },
    "mr": {
        "junior": "लहान विद्यार्थ्यांसाठी: हळूहळू मोजा, बोटे वापरा "
                  "किंवा वस्तू काढून पहा — चित्रामुळे प्रत्येक "
                  "गोष्टीचे गणित सोपे होते।",
        "applied": "असे गणित नेहमी एका एककाच्या मूल्यापासून "
                   "सुरू होते — आधी 1 चे मूल्य काढा, मग वाढवा।",
        "word_problem": "गोष्ट दोनदा वाचा: एकदा गोष्टीसाठी, "
                        "दुसऱ्यांदा संख्या आणि विचारलेली गोष्ट "
                        "अधोरेखित करण्यासाठी।",
    },
    "ta": {
        "junior": "சிறு மாணவர்களுக்கு: மெதுவாக எண்ணுங்கள், "
                  "விரல்களைப் பயன்படுத்துங்கள் அல்லது "
                  "பொருட்களை வரைந்து பாருங்கள் — படம் ஒவ்வொரு "
                  "கதைக் கணக்கையும் எளிதாக்கும்।",
        "applied": "இத்தகைய கணக்குகள் எப்போதும் ஒரு அலகின் "
                   "மதிப்பிலிருந்து தொடங்கும் — முதலில் 1-இன் "
                   "மதிப்பைக் கண்டுபிடியுங்கள், பின் பெருக்குங்கள்।",
        "word_problem": "கதையை இருமுறை படியுங்கள்: ஒருமுறை "
                        "கதைக்காக, மறுமுறை எண்களையும் "
                        "கேட்கப்பட்டதையும் அடிக்கோடிடுவதற்காக।",
    },
    "te": {
        "junior": "చిన్న విద్యార్థుల కోసం: నెమ్మదిగా లెక్కించండి, "
                  "వేళ్లను ఉపయోగించండి లేదా వస్తువులను గీయండి — "
                  "చిత్రం ప్రతి కథా లెక్కను సులభం చేస్తుంది।",
        "applied": "ఇలాంటి లెక్కలు ఎల్లప్పుడూ ఒక యూనిట్ "
                   "విలువతో మొదలవుతాయి — ముందు 1 విలువను "
                   "కనుగొనండి, తర్వాత పెంచండి।",
        "word_problem": "కథను రెండుసార్లు చదవండి: ఒకసారి "
                        "కథ కోసం, మరోసారి సంఖ్యలను మరియు "
                        "అడిగినదానిని గుర్తించడానికి।",
    },
}
for _code, _extra in _ADVICE_W13.items():
    ADVICE[_code].update(_extra)

# --- Teach me for the biggest new types (en + hi) -------------
TEACH["en"].update({
    "junior": [
        "Junior maths is about real things: mangoes, pencils, "
        "rupees and clocks — always picture the objects.",
        "Adding means putting together, taking away means "
        "subtracting; the story tells you which to do.",
        "For groups ('5 boxes, 6 in each'), multiply; for "
        "sharing equally, divide.",
        "Practice: make up your own story for 12 - 5 and solve "
        "it.",
    ],
    "applied": [
        "Applied maths is one idea in many costumes: find what "
        "ONE unit is worth, then scale to what is asked.",
        "Ratio compares parts of a whole — divide both sides "
        "by the same number to simplify.",
        "Write the formula first (interest, profit, speed), "
        "then put the numbers in.",
        "Practice: if 4 notebooks cost Rs 80, what do 7 cost?",
    ],
    "applied:ratio": [
        "A ratio compares two amounts the way a recipe compares "
        "ingredients — 2:3 means 2 parts to 3 parts.",
        "Simplify a ratio by dividing both sides by their HCF, "
        "just like simplifying a fraction.",
        "To share in a ratio, add the parts, find one part's "
        "value, then multiply back.",
        "Practice: simplify the ratio 18:24.",
    ],
    "word_problem:simple_interest": [
        "Simple interest is the rent money paid for using "
        "someone else's money — it grows by the same amount "
        "every year.",
        "SI = P x R x T / 100: Principal (the money kept), "
        "Rate (% per year), Time (in years).",
        "Months must become years first: 6 months = 1/2 year.",
        "Practice: find the simple interest on Rs 2000 at 5% "
        "for 2 years.",
    ],
    "sequences": [
        "A sequence is a pattern of numbers — your job is to "
        "find the rule the pattern is following.",
        "In an AP the same number is added each time (the "
        "common difference d); in a GP the same number is "
        "multiplied each time (the ratio r).",
        "nth term: AP uses a + (n-1)d; GP uses a x r^(n-1) — "
        "count the jumps, not the terms.",
        "Practice: write the 6th term of 5, 9, 13, ...",
    ],
    "geometry:distance": [
        "The distance between two points is the straight line "
        "joining them — the hypotenuse of a right triangle.",
        "The legs of the triangle are the gaps in x and in y; "
        "Pythagoras does the rest.",
        "Distance = sqrt((x2-x1)^2 + (y2-y1)^2). Squaring makes "
        "the direction (plus or minus) not matter.",
        "Practice: find the distance between (0, 0) and "
        "(6, 8).",
    ],
    "number_theory": [
        "HCF is the biggest number that divides both numbers; "
        "LCM is the smallest number both numbers divide into.",
        "Prime factorisation is the master key: HCF takes the "
        "LOWEST powers of common primes, LCM the HIGHEST of "
        "all.",
        "Euclid's trick also works: keep dividing and taking "
        "remainders until the remainder is 0.",
        "Practice: find the HCF and LCM of 18 and 30.",
    ],
})
TEACH["hi"].update({
    "junior": [
        "छोटी कक्षाओं का गणित असली चीज़ों के बारे में है: आम, "
        "पेंसिल, रुपये और घड़ी — हमेशा वस्तुओं की कल्पना करो।",
        "जोड़ना मतलब एक साथ रखना, निकालना मतलब घटाना; कहानी "
        "बताती है कि क्या करना है।",
        "समूहों के लिए ('5 डिब्बे, हर एक में 6') गुणा करो; "
        "बराबर बाँटने के लिए भाग दो।",
        "अभ्यास: 12 - 5 के लिए अपनी कहानी बनाओ और हल करो।",
    ],
    "applied": [
        "व्यावहारिक गणित एक ही विचार है कई रूपों में: एक इकाई "
        "का मान निकालो, फिर जितना पूछा गया है उतना बढ़ाओ।",
        "अनुपात पूरे के हिस्सों की तुलना करता है — सरल करने के "
        "लिए दोनों पक्षों को एक ही संख्या से भाग दो।",
        "पहले सूत्र लिखो (ब्याज, लाभ, गति), फिर संख्याएँ रखो।",
        "अभ्यास: 4 कॉपियों की कीमत Rs 80 है, तो 7 की कितनी "
        "होगी?",
    ],
    "applied:ratio": [
        "अनुपात दो मात्राओं की तुलना करता है, जैसे किसी "
        "व्यंजन में सामग्री — 2:3 मतलब 2 हिस्से और 3 हिस्से।",
        "अनुपात को सरल करने के लिए दोनों पक्षों को उनके HCF "
        "से भाग दो, बिल्कुल भिन्न की तरह।",
        "अनुपात में बाँटने के लिए हिस्से जोड़ो, एक हिस्से का "
        "मान निकालो, फिर वापस गुणा करो।",
        "अभ्यास: अनुपात 18:24 को सरल करो।",
    ],
    "word_problem:simple_interest": [
        "साधारण ब्याज दूसरे के पैसे के उपयोग का किराया है — "
        "यह हर वर्ष एक ही मात्रा में बढ़ता है।",
        "SI = P x R x T / 100: मूलधन (रखी गई रकम), दर "
        "(% प्रति वर्ष), समय (वर्षों में)।",
        "महीने पहले वर्षों में बदलने होते हैं: 6 महीने = "
        "1/2 वर्ष।",
        "अभ्यास: Rs 2000 पर 5% की दर से 2 वर्ष का साधारण "
        "ब्याज निकालो।",
    ],
    "sequences": [
        "अनुक्रम संख्याओं का एक पैटर्न है — तुम्हारा काम वह "
        "नियम ढूँढना है जिसका पैटर्न पालन कर रहा है।",
        "AP में हर बार एक ही संख्या जुड़ती है (सार्व अंतर d); "
        "GP में हर बार एक ही संख्या से गुणा होता है (अनुपात "
        "r)।",
        "nवाँ पद: AP में a + (n-1)d; GP में a x r^(n-1) — "
        "छलाँगें गिनो, पद नहीं।",
        "अभ्यास: 5, 9, 13, ... का 6ठा पद लिखो।",
    ],
    "geometry:distance": [
        "दो बिंदुओं के बीच की दूरी उन्हें जोड़ने वाली सीधी "
        "रेखा है — एक समकोण त्रिभुज का कर्ण।",
        "त्रिभुज की भुजाएँ x और y के अंतर हैं; बाकी काम "
        "पाइथागोरस करता है।",
        "दूरी = sqrt((x2-x1)^2 + (y2-y1)^2)। वर्ग करने से "
        "दिशा (धन या ऋण) का फर्क नहीं पड़ता।",
        "अभ्यास: (0, 0) और (6, 8) के बीच की दूरी निकालो।",
    ],
    "number_theory": [
        "HCF वह सबसे बड़ी संख्या है जो दोनों संख्याओं को "
        "भाग देती है; LCM वह सबसे छोटी संख्या है जिसमें दोनों "
        "समाती हैं।",
        "अभाज्य गुणनखंड ही मास्टर चाबी है: HCF में उभयनिष्ठ "
        "अभाज्यों की सबसे छोटी घात, LCM में सभी की सबसे बड़ी "
        "घात लेते हैं।",
        "यूक्लिड की तरकीब भी चलती है: भाग देते रहो और शेषफल "
        "लेते रहो जब तक शेषफल 0 न हो जाए।",
        "अभ्यास: 18 और 30 का HCF और LCM निकालो।",
    ],
})


# --- Wave 16 additions: Previous Papers (Suraj, 10 Nov 2026) -------------
# Real previous years' papers + chapter-wise pattern analysis +
# "Apna Paper Banao" practice-paper generator. en + hi are complete;
# bn/mr/ta/te fall back to English via get_strings(), like the other
# partially translated features.
_EN_W16 = {
    "menu_papers": "📄 Previous Papers",
    "papers_heading": "Previous Papers 📄",
    "papers_intro": "Real board exam papers from previous years, "
                    "with the chapter of every question marked. "
                    "Read them, see the pattern, then make your own "
                    "practice paper.",
    "papers_analysis_btn": "📊 See the pattern (analysis)",
    "papers_generate_btn": "📝 Apna Paper Banao — make a practice paper",
    "papers_class_heading": "Class {n} papers",
    "papers_source_label": "Source",
    "papers_view_btn": "View paper →",
    "papers_questions_word": "questions",
    "papers_marks_word": "marks",
    "papers_section_word": "Section",
    "papers_chapter_word": "Chapter",
    "papers_back": "← Previous Papers",
    "papers_analysis_heading": "Paper Pattern Analysis 📊",
    "papers_analysis_intro": "This analysis is counted only from "
                             "the papers actually collected below "
                             "— nothing is guessed.",
    "papers_coverage_line": "Counted from {papers} real paper(s) · "
                            "years: {years} · {questions} questions · "
                            "{marks} marks in total",
    "papers_weightage_heading": "Chapter-wise marks weightage",
    "papers_chapter_col": "Chapter",
    "papers_marks_col": "Marks",
    "papers_share_col": "Share",
    "papers_focus_heading": "Expected focus — practise these first",
    "papers_repeat_heading": "Most questions asked from",
    "papers_generate_heading": "Apna Paper Banao 📝",
    "papers_generate_intro": "Ganitra builds a fresh 80-mark "
                             "practice paper in the current CBSE "
                             "pattern (Sections A–E), using the "
                             "chapter weightage from the real papers "
                             "above. Real previous-paper questions "
                             "are reused where available; the rest "
                             "are new practice questions and are "
                             "always marked as such.",
    "papers_choose_class": "Choose your class",
    "papers_make_btn": "Make my practice paper →",
    "papers_gen_title": "Ganitra Practice Paper — Class {n} Maths",
    "papers_gen_sub": "80 marks · Sections A–E · built from the "
                      "pattern of {papers} real paper(s)",
    "papers_real_tag": "Real paper question · {origin}",
    "papers_practice_tag": "Practice question",
    "papers_answer_key_heading": "Answer Key",
    "papers_print_btn": "🖨 Print / Save as PDF",
    "papers_again_btn": "↻ Make another paper",
    "papers_answer_label": "Answer",
    "papers_from_source": "From the source paper above",
}

_HI_W16 = {
    "menu_papers": "📄 पिछले पेपर",
    "papers_heading": "पिछले पेपर 📄",
    "papers_intro": "पिछले वर्षों के असली बोर्ड परीक्षा पेपर, हर "
                    "प्रश्न के अध्याय के साथ। इन्हें पढ़िए, पैटर्न "
                    "देखिए, फिर अपना अभ्यास पेपर बनाइए।",
    "papers_analysis_btn": "📊 पैटर्न देखिए (विश्लेषण)",
    "papers_generate_btn": "📝 अपना पेपर बनाओ — अभ्यास पेपर बनाइए",
    "papers_class_heading": "कक्षा {n} के पेपर",
    "papers_source_label": "स्रोत",
    "papers_view_btn": "पेपर देखिए →",
    "papers_questions_word": "प्रश्न",
    "papers_marks_word": "अंक",
    "papers_section_word": "खंड",
    "papers_chapter_word": "अध्याय",
    "papers_back": "← पिछले पेपर",
    "papers_analysis_heading": "पेपर पैटर्न विश्लेषण 📊",
    "papers_analysis_intro": "यह विश्लेषण केवल नीचे इकट्ठा किए गए "
                             "असली पेपरों से गिना गया है — कुछ भी "
                             "अनुमान नहीं है।",
    "papers_coverage_line": "{papers} असली पेपरों से गिना गया · "
                            "वर्ष: {years} · {questions} प्रश्न · "
                            "कुल {marks} अंक",
    "papers_weightage_heading": "अध्याय अनुसार अंक-वज़न",
    "papers_chapter_col": "अध्याय",
    "papers_marks_col": "अंक",
    "papers_share_col": "हिस्सा",
    "papers_focus_heading": "संभावित फोकस — पहले इनका अभ्यास कीजिए",
    "papers_repeat_heading": "सबसे ज़्यादा प्रश्न इनसे आए",
    "papers_generate_heading": "अपना पेपर बनाओ 📝",
    "papers_generate_intro": "Ganitra वर्तमान CBSE पैटर्न (खंड "
                             "A–E) में नया 80 अंकों का अभ्यास पेपर "
                             "बनाता है, ऊपर के असली पेपरों के "
                             "अध्याय-वज़न का उपयोग करके। जहाँ उपलब्ध "
                             "हैं वहाँ असली पिछले पेपर के प्रश्न लिए "
                             "जाते हैं; बाकी नए अभ्यास प्रश्न होते "
                             "हैं और हमेशा ऐसे ही चिह्नित रहते हैं।",
    "papers_choose_class": "अपनी कक्षा चुनिए",
    "papers_make_btn": "मेरा अभ्यास पेपर बनाइए →",
    "papers_gen_title": "Ganitra अभ्यास पेपर — कक्षा {n} गणित",
    "papers_gen_sub": "80 अंक · खंड A–E · {papers} असली पेपरों के "
                      "पैटर्न से बनाया गया",
    "papers_real_tag": "असली पेपर का प्रश्न · {origin}",
    "papers_practice_tag": "अभ्यास प्रश्न",
    "papers_answer_key_heading": "उत्तर कुंजी",
    "papers_print_btn": "🖨 प्रिंट / PDF सहेजिए",
    "papers_again_btn": "↻ दूसरा पेपर बनाइए",
    "papers_answer_label": "उत्तर",
    "papers_from_source": "ऊपर के स्रोत पेपर से",
}

STRINGS["en"].update(_EN_W16)
STRINGS["hi"].update(_HI_W16)

_BN_W16 = {
    "menu_papers": "📄 আগের বছরের পেপার",
    "papers_heading": "আগের বছরের পেপার 📄",
    "papers_intro": "আগের বছরের আসল বোর্ড পরীক্ষার পেপার, প্রতিটি "
                    "প্রশ্নের অধ্যায় চিহ্নিত করে। পড়ুন, প্যাটার্ন "
                    "দেখুন, তারপর নিজের অনুশীলন পেপার বানান।",
    "papers_analysis_btn": "📊 প্যাটার্ন দেখুন (বিশ্লেষণ)",
    "papers_generate_btn": "📝 নিজের পেপার বানান — অনুশীলন পেপার",
    "papers_class_heading": "শ্রেণি {n}-এর পেপার",
    "papers_source_label": "উৎস",
    "papers_view_btn": "পেপার দেখুন →",
    "papers_questions_word": "প্রশ্ন",
    "papers_marks_word": "নম্বর",
    "papers_section_word": "বিভাগ",
    "papers_chapter_word": "অধ্যায়",
    "papers_back": "← আগের পেপার",
    "papers_analysis_heading": "পেপার প্যাটার্ন বিশ্লেষণ 📊",
    "papers_analysis_intro": "এই বিশ্লেষণ শুধু নিচে সংগ্রহ করা আসল "
                             "পেপারগুলো থেকেই গণনা করা — কিছুই "
                             "অনুমান করা হয়নি।",
    "papers_coverage_line": "{papers}টি আসল পেপার থেকে গণনা · বছর: "
                            "{years} · {questions}টি প্রশ্ন · মোট "
                            "{marks} নম্বর",
    "papers_weightage_heading": "অধ্যায় অনুযায়ী নম্বরের ওজন",
    "papers_chapter_col": "অধ্যায়",
    "papers_marks_col": "নম্বর",
    "papers_share_col": "অংশ",
    "papers_focus_heading": "সম্ভাব্য ফোকাস — আগে এগুলো অনুশীলন করুন",
    "papers_repeat_heading": "সবচেয়ে বেশি প্রশ্ন এসেছে",
    "papers_generate_heading": "নিজের পেপার বানান 📝",
    "papers_generate_intro": "Ganitra বর্তমান CBSE প্যাটার্নে "
                             "(বিভাগ A–E) নতুন 80 নম্বরের অনুশীলন "
                             "পেপার বানায়, উপরের আসল পেপারগুলোর "
                             "অধ্যায়-ওজন ব্যবহার করে। যেখানে পাওয়া "
                             "যায় সেখানে আসল আগের পেপারের প্রশ্ন "
                             "পুনরায় ব্যবহার করা হয়; বাকিগুলো নতুন "
                             "অনুশীলন প্রশ্ন এবং সবসময় সেভাবেই "
                             "চিহ্নিত থাকে।",
    "papers_choose_class": "আপনার শ্রেণি বেছে নিন",
    "papers_make_btn": "আমার অনুশীলন পেপার বানান →",
    "papers_gen_title": "Ganitra অনুশীলন পেপার — শ্রেণি {n} গণিত",
    "papers_gen_sub": "80 নম্বর · বিভাগ A–E · {papers}টি আসল "
                      "পেপারের প্যাটার্ন থেকে তৈরি",
    "papers_real_tag": "আসল পেপারের প্রশ্ন · {origin}",
    "papers_practice_tag": "অনুশীলন প্রশ্ন",
    "papers_answer_key_heading": "উত্তর সূচি",
    "papers_print_btn": "🖨 প্রিন্ট / PDF সংরক্ষণ করুন",
    "papers_again_btn": "↻ আরেকটি পেপার বানান",
    "papers_answer_label": "উত্তর",
    "papers_from_source": "উপরের উৎস পেপার থেকে",
}

_MR_W16 = {
    "menu_papers": "📄 मागील पेपर",
    "papers_heading": "मागील पेपर 📄",
    "papers_intro": "मागील वर्षांचे खरे बोर्ड पेपर, प्रत्येक "
                    "प्रश्नाचा प्रकरणासह. वाचा, पॅटर्न पहा, मग "
                    "स्वतःचा सराव पेपर बनवा.",
    "papers_analysis_btn": "📊 पॅटर्न पहा (विश्लेषण)",
    "papers_generate_btn": "📝 आपला पेपर बनवा — सराव पेपर",
    "papers_class_heading": "इयत्ता {n} चे पेपर",
    "papers_source_label": "स्रोत",
    "papers_view_btn": "पेपर पहा →",
    "papers_questions_word": "प्रश्न",
    "papers_marks_word": "गुण",
    "papers_section_word": "विभाग",
    "papers_chapter_word": "प्रकरण",
    "papers_back": "← मागील पेपर",
    "papers_analysis_heading": "पेपर पॅटर्न विश्लेषण 📊",
    "papers_analysis_intro": "हे विश्लेषण फक्त खाली गोळा केलेल्या "
                             "खऱ्या पेपरवरूनच मोजले आहे — काहीही "
                             "अंदाजे नाही.",
    "papers_coverage_line": "{papers} खऱ्या पेपरवरून मोजले · वर्षे: "
                            "{years} · {questions} प्रश्न · एकूण "
                            "{marks} गुण",
    "papers_weightage_heading": "प्रकरणानुसार गुणांचे वजन",
    "papers_chapter_col": "प्रकरण",
    "papers_marks_col": "गुण",
    "papers_share_col": "वाटा",
    "papers_focus_heading": "संभाव्य लक्ष — आधी यांचा सराव करा",
    "papers_repeat_heading": "सर्वाधिक प्रश्न यांमधून आले",
    "papers_generate_heading": "आपला पेपर बनवा 📝",
    "papers_generate_intro": "Ganitra सध्याच्या CBSE पॅटर्नमध्ये "
                             "(विभाग A–E) नवीन 80 गुणांचा सराव पेपर "
                             "बनवते, वरील खऱ्या पेपरच्या "
                             "प्रकरण-वजनाचा वापर करून. जिथे उपलब्ध "
                             "आहेत तिथे खरे मागील पेपरचे प्रश्न "
                             "पुन्हा वापरले जातात; बाकी नवीन सराव "
                             "प्रश्न असतात आणि नेहमी तसेच चिन्हांकित "
                             "असतात.",
    "papers_choose_class": "तुमची इयत्ता निवडा",
    "papers_make_btn": "माझा सराव पेपर बनवा →",
    "papers_gen_title": "Ganitra सराव पेपर — इयत्ता {n} गणित",
    "papers_gen_sub": "80 गुण · विभाग A–E · {papers} खऱ्या पेपरच्या "
                      "पॅटर्नवरून बनवले",
    "papers_real_tag": "खऱ्या पेपरचा प्रश्न · {origin}",
    "papers_practice_tag": "सराव प्रश्न",
    "papers_answer_key_heading": "उत्तरतालिका",
    "papers_print_btn": "🖨 प्रिंट / PDF जतन करा",
    "papers_again_btn": "↻ दुसरा पेपर बनवा",
    "papers_answer_label": "उत्तर",
    "papers_from_source": "वरील स्रोत पेपरमधून",
}

_TA_W16 = {
    "menu_papers": "📄 முந்தைய தாள்கள்",
    "papers_heading": "முந்தைய தாள்கள் 📄",
    "papers_intro": "முந்தைய ஆண்டுகளின் உண்மையான போர்டு தேர்வுத் "
                    "தாள்கள், ஒவ்வொரு கேள்வியின் அத்தியாயமும் "
                    "குறிக்கப்பட்டு. படியுங்கள், முறையைப் பாருங்கள், "
                    "பிறகு உங்கள் பயிற்சித் தாளை உருவாக்குங்கள்.",
    "papers_analysis_btn": "📊 முறையைப் பாருங்கள் (பகுப்பாய்வு)",
    "papers_generate_btn": "📝 உங்கள் தாளை உருவாக்குங்கள் — பயிற்சித் தாள்",
    "papers_class_heading": "வகுப்பு {n} தாள்கள்",
    "papers_source_label": "மூலம்",
    "papers_view_btn": "தாளைப் பாருங்கள் →",
    "papers_questions_word": "கேள்விகள்",
    "papers_marks_word": "மதிப்பெண்கள்",
    "papers_section_word": "பிரிவு",
    "papers_chapter_word": "அத்தியாயம்",
    "papers_back": "← முந்தைய தாள்கள்",
    "papers_analysis_heading": "தாள் முறை பகுப்பாய்வு 📊",
    "papers_analysis_intro": "இந்தப் பகுப்பாய்வு கீழே சேகரிக்கப்பட்ட "
                             "உண்மையான தாள்களிலிருந்து மட்டுமே "
                             "கணக்கிடப்பட்டது — எதுவும் ஊகிக்கப்படவில்லை.",
    "papers_coverage_line": "{papers} உண்மையான தாள்களிலிருந்து "
                            "கணக்கிடப்பட்டது · ஆண்டுகள்: {years} · "
                            "{questions} கேள்விகள் · மொத்தம் {marks} "
                            "மதிப்பெண்கள்",
    "papers_weightage_heading": "அத்தியாய வாரியான மதிப்பெண் எடை",
    "papers_chapter_col": "அத்தியாயம்",
    "papers_marks_col": "மதிப்பெண்கள்",
    "papers_share_col": "பங்கு",
    "papers_focus_heading": "எதிர்பார்க்கப்படும் கவனம் — முதலில் இவற்றைப் பயிற்சி செய்யுங்கள்",
    "papers_repeat_heading": "அதிக கேள்விகள் வந்தவை",
    "papers_generate_heading": "உங்கள் தாளை உருவாக்குங்கள் 📝",
    "papers_generate_intro": "Ganitra தற்போதைய CBSE முறையில் "
                             "(பிரிவுகள் A–E) புதிய 80 மதிப்பெண் "
                             "பயிற்சித் தாளை உருவாக்குகிறது, மேலே "
                             "உள்ள உண்மையான தாள்களின் அத்தியாய "
                             "எடையைப் பயன்படுத்தி. கிடைக்கும் இடங்களில் "
                             "உண்மையான முந்தைய தாள் கேள்விகள் மீண்டும் "
                             "பயன்படுத்தப்படும்; மற்றவை புதிய பயிற்சிக் "
                             "கேள்விகள், எப்போதும் அப்படியே "
                             "குறிக்கப்படும்.",
    "papers_choose_class": "உங்கள் வகுப்பைத் தேர்ந்தெடுங்கள்",
    "papers_make_btn": "என் பயிற்சித் தாளை உருவாக்குங்கள் →",
    "papers_gen_title": "Ganitra பயிற்சித் தாள் — வகுப்பு {n} கணிதம்",
    "papers_gen_sub": "80 மதிப்பெண்கள் · பிரிவுகள் A–E · {papers} "
                      "உண்மையான தாள்களின் முறையிலிருந்து உருவாக்கப்பட்டது",
    "papers_real_tag": "உண்மையான தாள் கேள்வி · {origin}",
    "papers_practice_tag": "பயிற்சிக் கேள்வி",
    "papers_answer_key_heading": "விடைக் குறிப்பு",
    "papers_print_btn": "🖨 அச்சிடு / PDF ஆகச் சேமி",
    "papers_again_btn": "↻ மற்றொரு தாளை உருவாக்குங்கள்",
    "papers_answer_label": "விடை",
    "papers_from_source": "மேலே உள்ள மூலத் தாளிலிருந்து",
}

_TE_W16 = {
    "menu_papers": "📄 గత పేపర్లు",
    "papers_heading": "గత పేపర్లు 📄",
    "papers_intro": "గత సంవత్సరాల నిజమైన బోర్డు పరీక్ష పేపర్లు, "
                    "ప్రతి ప్రశ్న యొక్క అధ్యాయం గుర్తించబడి. "
                    "చదవండి, నమూనా చూడండి, ఆపై మీ సాధన పేపర్‌ను "
                    "తయారు చేయండి.",
    "papers_analysis_btn": "📊 నమూనా చూడండి (విశ్లేషణ)",
    "papers_generate_btn": "📝 మీ పేపర్ తయారు చేయండి — సాధన పేపర్",
    "papers_class_heading": "తరగతి {n} పేపర్లు",
    "papers_source_label": "మూలం",
    "papers_view_btn": "పేపర్ చూడండి →",
    "papers_questions_word": "ప్రశ్నలు",
    "papers_marks_word": "మార్కులు",
    "papers_section_word": "విభాగం",
    "papers_chapter_word": "అధ్యాయం",
    "papers_back": "← గత పేపర్లు",
    "papers_analysis_heading": "పేపర్ నమూనా విశ్లేషణ 📊",
    "papers_analysis_intro": "ఈ విశ్లేషణ క్రింద సేకరించిన నిజమైన "
                             "పేపర్ల నుండి మాత్రమే లెక్కించబడింది — "
                             "ఏదీ ఊహించబడలేదు.",
    "papers_coverage_line": "{papers} నిజమైన పేపర్ల నుండి "
                            "లెక్కించబడింది · సంవత్సరాలు: {years} · "
                            "{questions} ప్రశ్నలు · మొత్తం {marks} "
                            "మార్కులు",
    "papers_weightage_heading": "అధ్యాయాల వారీ మార్కుల బరువు",
    "papers_chapter_col": "అధ్యాయం",
    "papers_marks_col": "మార్కులు",
    "papers_share_col": "వాటా",
    "papers_focus_heading": "ఆశించిన దృష్టి — ముందు వీటిని సాధన చేయండి",
    "papers_repeat_heading": "అత్యధిక ప్రశ్నలు వచ్చినవి",
    "papers_generate_heading": "మీ పేపర్ తయారు చేయండి 📝",
    "papers_generate_intro": "Ganitra ప్రస్తుత CBSE నమూనాలో "
                             "(విభాగాలు A–E) కొత్త 80 మార్కుల సాధన "
                             "పేపర్‌ను తయారు చేస్తుంది, పైన ఉన్న "
                             "నిజమైన పేపర్ల అధ్యాయ బరువును "
                             "ఉపయోగించి. లభించే చోట నిజమైన గత పేపర్ "
                             "ప్రశ్నలు మళ్లీ ఉపయోగించబడతాయి; "
                             "మిగిలినవి కొత్త సాధన ప్రశ్నలు, "
                             "ఎల్లప్పుడూ అలాగే గుర్తించబడతాయి.",
    "papers_choose_class": "మీ తరగతిని ఎంచుకోండి",
    "papers_make_btn": "నా సాధన పేపర్ తయారు చేయండి →",
    "papers_gen_title": "Ganitra సాధన పేపర్ — తరగతి {n} గణితం",
    "papers_gen_sub": "80 మార్కులు · విభాగాలు A–E · {papers} "
                      "నిజమైన పేపర్ల నమూనా నుండి తయారు చేయబడింది",
    "papers_real_tag": "నిజమైన పేపర్ ప్రశ్న · {origin}",
    "papers_practice_tag": "సాధన ప్రశ్న",
    "papers_answer_key_heading": "జవాబు కీ",
    "papers_print_btn": "🖨 ప్రింట్ / PDF గా సేవ్ చేయండి",
    "papers_again_btn": "↻ మరో పేపర్ తయారు చేయండి",
    "papers_answer_label": "జవాబు",
    "papers_from_source": "పైన ఉన్న మూల పేపర్ నుండి",
}

STRINGS["bn"].update(_BN_W16)
STRINGS["mr"].update(_MR_W16)
STRINGS["ta"].update(_TA_W16)
STRINGS["te"].update(_TE_W16)

# --- Wave 18 additions: comfort buttons under each chat answer -----------
# The 📋 Copy and 🔁 "explain more simply" text buttons in the chat
# (Suraj, 10 Nov 2026: "Muse or ChatGPT ki tarah comfortable hona
# chahiye"). Every key exists in all 6 languages, like every wave
# before. mm_* keys already reach the chat JS via js_t in app.py.
_EN_W18 = {
    "mm_copy_btn": "Copy",
    "mm_copied": "Copied ✓",
    "mm_simple_btn": "Explain more simply",
}
_HI_W18 = {
    "mm_copy_btn": "कॉपी करो",
    "mm_copied": "कॉपी हो गया ✓",
    "mm_simple_btn": "दूसरी तरह समझाओ",
}
_BN_W18 = {
    "mm_copy_btn": "কপি করুন",
    "mm_copied": "কপি হয়েছে ✓",
    "mm_simple_btn": "অন্যভাবে বোঝাও",
}
_MR_W18 = {
    "mm_copy_btn": "कॉपी करा",
    "mm_copied": "कॉपी झाले ✓",
    "mm_simple_btn": "दुसऱ्या प्रकारे समजावा",
}
_TA_W18 = {
    "mm_copy_btn": "நகலெடு",
    "mm_copied": "நகலெடுக்கப்பட்டது ✓",
    "mm_simple_btn": "வேறு விதமாக விளக்கு",
}
_TE_W18 = {
    "mm_copy_btn": "కాపీ చేయండి",
    "mm_copied": "కాపీ అయింది ✓",
    "mm_simple_btn": "మరో విధంగా వివరించండి",
}

STRINGS["en"].update(_EN_W18)
STRINGS["hi"].update(_HI_W18)
STRINGS["bn"].update(_BN_W18)
STRINGS["mr"].update(_MR_W18)
STRINGS["ta"].update(_TA_W18)
STRINGS["te"].update(_TE_W18)
