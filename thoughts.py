"""Wave 155 (Suraj, 18 Nov 2026): daily rotating thoughts on the
chat home.

Suraj's order: the chat page's empty state showed "Hello <name>!"
as its greeting line — in its place, put the day's thoughts:
"Chat page jo hello suraj likha hai uske jagah daily kaa 10
thought daal skte hai time divide karke". So the day is divided
into 10 time slots and each slot shows its own thought; the set
of 10 changes the next day.

Design (all deterministic, no DB, no state):
  * The day (Asia/Kolkata) is split into SLOTS_PER_DAY = 10
    slots of SLOT_MINUTES = 144 minutes (2.4 h), starting at
    00:00 IST: slot 0 = 00:00-02:24, slot 1 = 02:24-04:48, ...,
    slot 9 = 21:36-24:00.
  * A date seeds a stable SHA-256-based shuffle (never Python's
    salted hash()), and the first 10 indices of that shuffle are
    the day's thoughts — always 10 DISTINCT thoughts, the same
    for every student in the same slot, and a fresh set the
    next day.
  * Each thought carries three variants — English, Hinglish
    (Roman Hindi) and Hindi (Devanagari). The variant follows
    the app's existing language machinery (the session UI
    language, which the chat itself keeps up to date — Wave 9):
    "hi" -> Devanagari, "hinglish" -> Roman, anything else
    (the "en" default, and the bn/mr/ta/te UI languages, for
    which this bank ships no variant) -> English. There is NO
    language picker (banned) and no new setting.

The thoughts are original, unattributed, teacher-like lines —
no quotations are pinned on real people.
"""

import hashlib
import random
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

SLOTS_PER_DAY = 10
SLOT_MINUTES = (24 * 60) // SLOTS_PER_DAY  # 144 minutes = 2.4 h

# Each entry: {"en": ..., "hinglish": ..., "hi": ...} — one warm
# line (never more than two short sentences), maths/study
# flavoured, written for a school student.
THOUGHTS = [
    {"en": "Every expert was once a beginner who refused to give up. One small sum today is enough.",
     "hinglish": "Har expert kabhi beginner tha — bas usne haar nahi maani. Aaj ka ek chhota sa sawal hi kaafi hai.",
     "hi": "हर विशेषज्ञ कभी शुरुआती था — बस उसने हार नहीं मानी। आज का एक छोटा सा सवाल ही काफी है।"},
    {"en": "A mistake is not failure — it is a free lesson. Note it down and move on.",
     "hinglish": "Galti fail hona nahi hai — woh ek muft ka sabak hai. Use likh lo aur aage badho.",
     "hi": "गलती असफलता नहीं है — वह एक मुफ़्त का सबक है। उसे लिख लो और आगे बढ़ो।"},
    {"en": "Maths is not about being fast. It is about understanding one step at a time.",
     "hinglish": "Maths tez hone ka khel nahi hai. Ek-ek step samajhna hi asli jeet hai.",
     "hi": "गणित तेज़ होने का खेल नहीं है। एक-एक कदम समझना ही असली जीत है।"},
    {"en": "Ten minutes of practice every day beats three hours once a month.",
     "hinglish": "Roz ke 10 minute practice, mahine me ek baar ke 3 ghante se zyada kaam ke hain.",
     "hi": "रोज़ के 10 मिनट अभ्यास, महीने में एक बार के 3 घंटे से ज़्यादा काम के हैं।"},
    {"en": "The sum you avoid today is the topic that troubles you in the exam. Try it now.",
     "hinglish": "Jis sawal ko aaj taal rahe ho, wahi exam me pareshan karega. Use abhi try karo.",
     "hi": "जिस सवाल को आज टाल रहे हो, वही परीक्षा में परेशान करेगा। उसे अभी कोशिश करो।"},
    {"en": "Nobody is born good at maths. People just practise a little more than others.",
     "hinglish": "Koi paidaishi maths me tez nahi hota. Log bas doosron se thoda zyada practice karte hain.",
     "hi": "कोई जन्म से गणित में तेज़ नहीं होता। लोग बस दूसरों से थोड़ा ज़्यादा अभ्यास करते हैं।"},
    {"en": "Read the question slowly, twice. Half the answer hides inside the question itself.",
     "hinglish": "Sawal ko dheere se do baar padho. Aadha jawab sawal ke andar hi chhupa hota hai.",
     "hi": "सवाल को धीरे से दो बार पढ़ो। आधा जवाब सवाल के अंदर ही छिपा होता है।"},
    {"en": "Small steps daily — that is how big chapters get finished.",
     "hinglish": "Roz chhote-chhote kadam — bade chapter aise hi khatm hote hain.",
     "hi": "रोज़ छोटे-छोटे कदम — बड़े अध्याय ऐसे ही खत्म होते हैं।"},
    {"en": "If a method feels hard, break the problem into smaller pieces. Small pieces are easy.",
     "hinglish": "Agar tareeka mushkil lage, toh sawal ko chhote tukdon me todo. Chhote tukde aasan hote hain.",
     "hi": "अगर तरीका मुश्किल लगे, तो सवाल को छोटे टुकड़ों में तोड़ो। छोटे टुकड़े आसान होते हैं।"},
    {"en": "Your notebook of mistakes is worth more than a book of solved examples.",
     "hinglish": "Tumhari galtiyon wali copy, solved examples ki kitab se zyada keemti hai.",
     "hi": "तुम्हारी गलतियों वाली कॉपी, हल किए उदाहरणों की किताब से ज़्यादा कीमती है।"},
    {"en": "Asking a doubt is a sign of strength, not weakness. Always ask.",
     "hinglish": "Doubt puchna kamzori nahi, takat ki nishani hai. Hamesha pucho.",
     "hi": "शंका पूछना कमज़ोरी नहीं, ताकत की निशानी है। हमेशा पूछो।"},
    {"en": "Speed comes after accuracy. First be right, then be quick.",
     "hinglish": "Speed baad me aati hai, sahi jawab pehle. Pehle sahi, phir tez.",
     "hi": "गति बाद में आती है, सही जवाब पहले। पहले सही, फिर तेज़।"},
    {"en": "A calm mind solves in minutes what a worried mind cannot solve in an hour.",
     "hinglish": "Shaant dimag woh sawal minutes me hal karta hai jo pareshan dimag ghante me nahi kar pata.",
     "hi": "शांत दिमाग वह सवाल मिनटों में हल करता है जो परेशान दिमाग घंटे में नहीं कर पाता।"},
    {"en": "Revision is not re-reading. Revision is solving the same sum again, on your own.",
     "hinglish": "Revision matlab dobara padhna nahi hai. Revision matlab wahi sawal khud se dobara hal karna.",
     "hi": "दोहराव मतलब दोबारा पढ़ना नहीं है। दोहराव मतलब वही सवाल खुद से दोबारा हल करना।"},
    {"en": "Tables learnt by heart make every big calculation feel small.",
     "hinglish": "Pahade yaad ho toh har badi calculation chhoti lagne lagti hai.",
     "hi": "पहाड़े याद हों तो हर बड़ी गणना छोटी लगने लगती है।"},
    {"en": "Do not compare your chapter 1 with someone else's chapter 10. Your pace is fine.",
     "hinglish": "Apne pehle chapter ko kisi ke dasve chapter se mat tolna. Tumhari raftaar bilkul sahi hai.",
     "hi": "अपने पहले अध्याय को किसी के दसवें अध्याय से मत तौलना। तुम्हारी रफ़्तार बिल्कुल सही है।"},
    {"en": "Write the steps neatly. A tidy page makes a tidy mind.",
     "hinglish": "Steps saaf-saaf likho. Saaf page, saaf dimag banata hai.",
     "hi": "चरण साफ़-साफ़ लिखो। साफ़ पेज, साफ़ दिमाग बनाता है।"},
    {"en": "Geometry becomes friendly the day you start drawing the figure yourself.",
     "hinglish": "Geometry usi din dost ban jati hai jab tum figure khud banana shuru kar dete ho.",
     "hi": "ज्यामिति उसी दिन दोस्त बन जाती है जब तुम आकृति खुद बनाना शुरू कर देते हो।"},
    {"en": "One formula understood deeply is worth ten formulas memorised blindly.",
     "hinglish": "Ek formula gehrai se samjha hua, bina samjhe rate hue das formulaon se behtar hai.",
     "hi": "एक सूत्र गहराई से समझा हुआ, बिना समझे रटे हुए दस सूत्रों से बेहतर है।"},
    {"en": "Exams test your preparation, not your worth. Prepare well and stay calm.",
     "hinglish": "Exam tumhari taiyari parakhte hain, tumhari keemat nahi. Achhe se taiyari karo, shaant raho.",
     "hi": "परीक्षा तुम्हारी तैयारी परखती है, तुम्हारी कीमत नहीं। अच्छे से तैयारी करो, शांत रहो।"},
    {"en": "Fractions stop being scary the day you picture a roti cut into equal parts.",
     "hinglish": "Bhinn (fractions) usi din aasan ho jate hain jab tum roti ke barabar tukde sochne lagte ho.",
     "hi": "भिन्न उसी दिन आसान हो जाते हैं जब तुम रोटी के बराबर टुकड़े सोचने लगते हो।"},
    {"en": "Every topper's secret is simple: they revised yesterday's work today.",
     "hinglish": "Har topper ka raaz seedha hai: unhone kal ka kaam aaj dobara kiya.",
     "hi": "हर टॉपर का राज़ सीधा है: उन्होंने कल का काम आज दोबारा किया।"},
    {"en": "When a sum goes wrong, smile — you just found the exact place to learn.",
     "hinglish": "Jab koi sawal galat ho jaye toh muskurao — tumhe seekhne ki sahi jagah mil gayi.",
     "hi": "जब कोई सवाल गलत हो जाए तो मुस्कुराओ — तुम्हें सीखने की सही जगह मिल गई।"},
    {"en": "Percentages are just fractions wearing a hundred's coat. Nothing to fear.",
     "hinglish": "Percentage bas sau ke coat me chhupa bhinn hai. Darne ki koi baat nahi.",
     "hi": "प्रतिशत बस सौ के कोट में छिपा भिन्न है। डरने की कोई बात नहीं।"},
    {"en": "Start with the easiest question in the set. Confidence is built, not found.",
     "hinglish": "Set ke sabse aasan sawal se shuru karo. Bharosa banta hai, milta nahi.",
     "hi": "सेट के सबसे आसान सवाल से शुरू करो। भरोसा बनता है, मिलता नहीं।"},
    {"en": "A diagram can say what ten lines of text cannot. Draw first, think next.",
     "hinglish": "Ek diagram woh keh deta hai jo das line nahi keh pati. Pehle banao, phir socho.",
     "hi": "एक चित्र वह कह देता है जो दस पंक्तियाँ नहीं कह पातीं। पहले बनाओ, फिर सोचो।"},
    {"en": "Sleep well before the exam. A rested brain is the best formula of all.",
     "hinglish": "Exam se pehle achhi neend lo. Aaram kiya hua dimag hi sabse bada formula hai.",
     "hi": "परीक्षा से पहले अच्छी नींद लो। आराम किया हुआ दिमाग ही सबसे बड़ा सूत्र है।"},
    {"en": "Algebra is only arithmetic wearing a mask — the letter is just a hidden number.",
     "hinglish": "Algebra bas mask pehna hua arithmetic hai — akshar ek chhupa hua number hi toh hai.",
     "hi": "बीजगणित बस मुखौटा पहना हुआ अंकगणित है — अक्षर एक छिपा हुआ अंक ही तो है।"},
    {"en": "Check your answer by working backwards. Toppers trust, but they verify.",
     "hinglish": "Jawab ko ulta chal kar check karo. Topper bharosa karte hain, lekin jaanchte bhi hain.",
     "hi": "जवाब को उल्टा चलकर जाँचो। टॉपर भरोसा करते हैं, लेकिन जाँचते भी हैं।"},
    {"en": "Today's homework done on time is tomorrow's top rank in the making.",
     "hinglish": "Aaj ka homework samay par, kal ki top rank ki taiyari hai.",
     "hi": "आज का गृहकार्य समय पर, कल की शीर्ष रैंक की तैयारी है।"},
    {"en": "Negative numbers are not negative thinking — they are just numbers below zero.",
     "hinglish": "Negative numbers negative soch nahi hain — woh bas zero se neeche wale number hain.",
     "hi": "ऋणात्मक संख्याएँ नकारात्मक सोच नहीं हैं — वे बस शून्य से नीचे वाली संख्याएँ हैं।"},
    {"en": "Learn the 'why' behind every rule, and you will never need to fear the 'what if'.",
     "hinglish": "Har rule ke peeche ka 'kyun' seekh lo, phir 'agar aisa ho toh' se kabhi dar nahi lagega.",
     "hi": "हर नियम के पीछे का 'क्यों' सीख लो, फिर 'अगर ऐसा हो तो' से कभी डर नहीं लगेगा।"},
    {"en": "Five sums a day keeps the fear of maths away.",
     "hinglish": "Roz ke paanch sawal, maths ka dar door bhagate hain.",
     "hi": "रोज़ के पाँच सवाल, गणित का डर दूर भगाते हैं।"},
    {"en": "Your only competition is who you were yesterday. Beat that person.",
     "hinglish": "Tumhara asli mukabla kal wale tumse hai. Use hara do.",
     "hi": "तुम्हारा असली मुकाबला कल वाले तुमसे है। उसे हरा दो।"},
    {"en": "Word problems are stories in disguise. Find the story, the maths follows.",
     "hinglish": "Word problems chhupi hui kahaniyan hain. Kahani pakdo, maths apne aap aayega.",
     "hi": "शब्द-प्रश्न छिपी हुई कहानियाँ हैं। कहानी पकड़ो, गणित अपने आप आएगा।"},
    {"en": "A chapter is never too big — it is just many small pages standing together.",
     "hinglish": "Koi chapter bada nahi hota — woh bas kai chhote pages ka jhund hota hai.",
     "hi": "कोई अध्याय बड़ा नहीं होता — वह बस कई छोटे पृष्ठों का झुंड होता है।"},
    {"en": "When stuck, change the numbers to smaller ones and try again. The method stays the same.",
     "hinglish": "Atak jao toh numbers chhote karke dobara try karo. Tareeka wahi rahta hai.",
     "hi": "अटक जाओ तो संख्याएँ छोटी करके दोबारा कोशिश करो। तरीका वही रहता है।"},
    {"en": "Marks reward clear steps. Show your working — it speaks for you.",
     "hinglish": "Marks saaf steps ko milte hain. Apna kaam dikhao — woh tumhare liye bolta hai.",
     "hi": "अंक साफ़ चरणों को मिलते हैं। अपना काम दिखाओ — वह तुम्हारे लिए बोलता है।"},
    {"en": "Curiosity is the first chapter of every subject. Keep asking 'why'.",
     "hinglish": "Jigyasa har subject ka pehla chapter hai. 'Kyun' puchna band mat karo.",
     "hi": "जिज्ञासा हर विषय का पहला अध्याय है। 'क्यों' पूछना बंद मत करो।"},
    {"en": "The calculator can give answers, but only your mind can give understanding.",
     "hinglish": "Calculator jawab de sakta hai, lekin samajh sirf tumhara dimag de sakta hai.",
     "hi": "कैलकुलेटर जवाब दे सकता है, लेकिन समझ सिर्फ़ तुम्हारा दिमाग दे सकता है।"},
    {"en": "Practise the topic you dislike for just one week — it often becomes your favourite.",
     "hinglish": "Jo topic pasand nahi, use sirf ek hafta practice karo — aksar wahi pasandeeda ban jata hai.",
     "hi": "जो विषय पसंद नहीं, उसे सिर्फ़ एक हफ़्ता अभ्यास करो — अक्सर वही पसंदीदा बन जाता है।"},
    {"en": "Units matter: a length in centimetres and metres is not the same answer.",
     "hinglish": "Units ka dhyan rakho: centimetre aur metre me lambai ek jawab nahi hoti.",
     "hi": "इकाइयों का ध्यान रखो: सेंटीमीटर और मीटर में लंबाई एक जवाब नहीं होती।"},
    {"en": "Before solving, guess roughly what the answer should look like. Estimation is a superpower.",
     "hinglish": "Hal karne se pehle andaaza lagao ki jawab kaisa hoga. Andaaza ek superpower hai.",
     "hi": "हल करने से पहले अंदाज़ा लगाओ कि जवाब कैसा होगा। अंदाज़ा एक महाशक्ति है।"},
    {"en": "Hard work in maths always pays interest — like a good recurring deposit.",
     "hinglish": "Maths me mehnat hamesha byaaj ke saath lautti hai — ek achhi recurring deposit ki tarah.",
     "hi": "गणित में मेहनत हमेशा ब्याज के साथ लौटती है — एक अच्छी आवर्ती जमा की तरह।"},
    {"en": "Do not erase your wrong attempts. They show the teacher exactly how you think.",
     "hinglish": "Apni galat koshishon ko mitao mat. Wahi teacher ko batati hain ki tum sochte kaise ho.",
     "hi": "अपनी गलत कोशिशों को मिटाओ मत। वही शिक्षक को बताती हैं कि तुम सोचते कैसे हो।"},
    {"en": "A theorem is just a shortcut that someone proved for you long ago. Use it with thanks.",
     "hinglish": "Theorem bas ek shortcut hai jo kisi ne bahut pehle tumhare liye saabit kar diya. Use shukriya ke saath apnao.",
     "hi": "प्रमेय बस एक शॉर्टकट है जो किसी ने बहुत पहले तुम्हारे लिए सिद्ध कर दिया। उसे धन्यवाद के साथ अपनाओ।"},
    {"en": "Group study works when everyone explains one sum to the others.",
     "hinglish": "Group study tab kaam karti hai jab har koi ek sawal doosron ko samjhata hai.",
     "hi": "समूह अध्ययन तब काम करता है जब हर कोई एक सवाल दूसरों को समझाता है।"},
    {"en": "The best time to start was yesterday. The second-best time is this very minute.",
     "hinglish": "Shuru karne ka sabse achha samay kal tha. Dusra sabse achha samay yahi minute hai.",
     "hi": "शुरू करने का सबसे अच्छा समय कल था। दूसरा सबसे अच्छा समय यही मिनट है।"},
    {"en": "Triangles, circles, lines — geometry is the drawing class of mathematics.",
     "hinglish": "Tribhuj, vritt, rekhaayein — geometry maths ki drawing class hai.",
     "hi": "त्रिभुज, वृत्त, रेखाएँ — ज्यामिति गणित की चित्रकला कक्षा है।"},
    {"en": "If you can explain a sum to a friend, you truly know it. Teaching is the final test.",
     "hinglish": "Agar tum ek sawal dost ko samjha sakte ho, toh tum use sach me jaante ho. Sikhana hi aakhri test hai.",
     "hi": "अगर तुम एक सवाल दोस्त को समझा सकते हो, तो तुम उसे सच में जानते हो। सिखाना ही आखिरी परीक्षा है।"},
    {"en": "Zero was India's gift to the world. Be proud of the maths in your roots.",
     "hinglish": "Shunya (zero) Bharat ka duniya ko uphaar hai. Apni jadon ke maths par garv karo.",
     "hi": "शून्य भारत का दुनिया को उपहार है। अपनी जड़ों के गणित पर गर्व करो।"},
    {"en": "Probability teaches a life lesson too: prepare for the likely, hope for the best.",
     "hinglish": "Probability ek zindagi ka sabak bhi deti hai: jo sambhav hai uski taiyari karo, sabse achhe ki ummeed rakho.",
     "hi": "प्रायिकता एक ज़िंदगी का सबक भी देती है: जो संभव है उसकी तैयारी करो, सबसे अच्छे की उम्मीद रखो।"},
    {"en": "Slow and correct beats fast and wrong — in exams and in life.",
     "hinglish": "Dheere aur sahi, tez aur galat se behtar hai — exam me bhi, zindagi me bhi.",
     "hi": "धीरे और सही, तेज़ और गलत से बेहतर है — परीक्षा में भी, ज़िंदगी में भी।"},
    {"en": "Keep a small formula diary. Reviewing it for five minutes daily works wonders.",
     "hinglish": "Ek chhoti formula diary rakho. Roz paanch minute use dekhna kamaal karta hai.",
     "hi": "एक छोटी सूत्र डायरी रखो। रोज़ पाँच मिनट उसे देखना कमाल करता है।"},
    {"en": "Every chapter you finish is a door you never have to fear again.",
     "hinglish": "Jo chapter tum khatm kar lete ho, woh darwaza phir kabhi darane wala nahi rahta.",
     "hi": "जो अध्याय तुम खत्म कर लेते हो, वह दरवाज़ा फिर कभी डराने वाला नहीं रहता।"},
    {"en": "Maths rewards the regular, not just the brilliant. Show up daily.",
     "hinglish": "Maths sirf tez dimag ko nahi, roz aane wale ko inaam deta hai. Roz aao.",
     "hi": "गणित सिर्फ़ तेज़ दिमाग को नहीं, रोज़ आने वाले को इनाम देता है। रोज़ आओ।"},
    {"en": "When the board exam feels big, remember: it is only the sums you already practised, wearing new numbers.",
     "hinglish": "Jab board exam bada lage, yaad rakho: woh wahi sawal hain jo tum practice kar chuke ho, bas naye numbers ke saath.",
     "hi": "जब बोर्ड परीक्षा बड़ी लगे, याद रखो: वे वही सवाल हैं जो तुम अभ्यास कर चुके हो, बस नए अंकों के साथ।"},
    {"en": "A rough page is a thinking page. Do your wild calculations there without fear.",
     "hinglish": "Rough page sochne ka page hai. Wahan bina dare apni saari calculation karo.",
     "hi": "रफ़ पेज सोचने का पेज है। वहाँ बिना डरे अपनी सारी गणना करो।"},
    {"en": "Graphs turn numbers into pictures. Once you see the picture, the answer is near.",
     "hinglish": "Graph numbers ko tasveer bana dete hain. Tasveer dikhi, toh jawab paas hai.",
     "hi": "ग्राफ़ संख्याओं को तस्वीर बना देते हैं। तस्वीर दिखी, तो जवाब पास है।"},
    {"en": "Believe this much at least: the next sum is solvable, and you are the one to solve it.",
     "hinglish": "Bas itna bharosa rakho: agla sawal hal ho sakta hai, aur use hal karne wale tum hi ho.",
     "hi": "बस इतना भरोसा रखो: अगला सवाल हल हो सकता है, और उसे हल करने वाले तुम ही हो।"},
]

_VARIANTS = ("en", "hinglish", "hi")


def variant_for(lang):
    """Map an app language code to a thought variant.

    Follows the app's existing language machinery: the session
    UI language is "hi" for Hindi (Devanagari UI strings), the
    answer layer's "hinglish" maps to the Roman variant, and
    everything else — the "en" default plus the bn/mr/ta/te UI
    languages, for which this bank ships no variant — falls
    back to English. No picker, no new setting.
    """
    code = (lang or "en").strip().lower()
    if code == "hi":
        return "hi"
    if code == "hinglish":
        return "hinglish"
    return "en"


def slot_for(moment):
    """Slot index (0..9) for an IST datetime: 144-minute slots
    from 00:00 IST (slot 0 = 00:00-02:24, ..., slot 9 =
    21:36-24:00)."""
    minutes = moment.hour * 60 + moment.minute
    return minutes // SLOT_MINUTES


def day_selection(day):
    """The day's 10 DISTINCT thought indices for a date.

    Seeded by the ISO date through SHA-256 (stable across
    processes and machines — Python's salted hash() is never
    used), so every student sees the same thought in the same
    slot, and the set changes the next day.
    """
    digest = hashlib.sha256(
        ("ganitra-thoughts-" + day.isoformat()).encode("utf-8")
    ).digest()
    seed = int.from_bytes(digest[:8], "big")
    rng = random.Random(seed)
    return rng.sample(range(len(THOUGHTS)), SLOTS_PER_DAY)


def thought_at(moment, lang="en"):
    """The thought for an IST moment: a dict with the slot, the
    thought index, the variant used and the text."""
    slot = slot_for(moment)
    index = day_selection(moment.date())[slot]
    variant = variant_for(lang)
    return {
        "slot": slot,
        "index": index,
        "lang": variant,
        "text": THOUGHTS[index][variant],
    }


def thought_text(now=None, lang="en"):
    """The current thought's text. `now` may be any aware
    datetime (converted to IST) or None for the live IST time;
    naive datetimes are read as IST."""
    if now is None:
        moment = datetime.now(IST)
    elif now.tzinfo is None:
        moment = now.replace(tzinfo=IST)
    else:
        moment = now.astimezone(IST)
    return thought_at(moment, lang)["text"]
