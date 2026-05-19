import os

TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = '-'
FOOTER = "تحفظ كل الحقوق لي Vale Community"

MIN_PLAYERS = 6
MAX_PLAYERS = 12
WEREWOLF_VOTE_TIME = 25
NIGHT_ACTIONS_TIME = 40
DAY_VOTE_TIME = 45
KING_ACTION_TIME = 20

GAME_GRAPHICS = {
    "lobby_banner": "https://placehold.co/600x300/1a1a2e/f5d742?text=Werewolf+Game+Lobby",
    "night_phase": "https://placehold.co/600x300/0d0d1a/4a4ae0?text=🌙+Night+Falls",
    "day_phase": "https://placehold.co/600x300/f5d742/1a1a2e?text=☀️+Day+Phase",
    "werewolf": "https://placehold.co/400x400/1a1a2e/ff4444?text=🐺+Werewolf",
    "villager": "https://placehold.co/400x400/2b2d31/ffffff?text=🧑‍🌾+Villager",
    "detective": "https://placehold.co/400x400/1a3a5c/00ccff?text=🔍+Detective",
    "bodyguard": "https://placehold.co/400x400/3a2a1a/ff8800?text=🛡️+Bodyguard",
    "king": "https://placehold.co/400x400/3a1a2a/ffd700?text=👑+King",
    "mayor": "https://placehold.co/400x400/2a3a1a/44ff44?text=🏛️+Mayor",
    "doctor": "https://placehold.co/400x400/1a3a2a/00ff88?text=⚕️+Doctor",
    "seductress": "https://placehold.co/400x400/3a1a3a/ff66ff?text=💃+Seductress",
    "om_zaki": "https://placehold.co/400x400/3a2a2a/ffaa66?text=👵+Om+Zaki",
    "werewolf_victory": "https://placehold.co/600x300/1a0000/ff4444?text=🐺+Werewolves+Win",
    "villager_victory": "https://placehold.co/600x300/001a00/44ff44?text=🎉+Village+Wins",
}

AI_ART_PROMPTS = {
    "lobby_banner": "Dark fantasy desert village at dusk, square banner, glowing moon silhouette, ancient arabic-inspired architecture, moody purple-orange sky, cinematic lighting, 2D illustration style",
    "night_phase": "Dark starry desert night, crescent moon casting silver light on sand dunes, mysterious glowing eyes in the darkness, arabian nights atmosphere, 2D fantasy illustration, moody dark blues and purples",
    "day_phase": "Golden sunrise over an arabian-style village, warm sand-colored buildings, market stalls, villagers gathering in the square, hopeful warm atmosphere, 2D fantasy illustration",
    "werewolf": "Fierce werewolf transformation under full moon, dark fur, glowing red eyes, standing on two legs, arabian desert background, dramatic lighting, dark fantasy character art, 2D illustration",
    "villager": "Simple arabian village man in traditional thawb and shemagh, kind face, holding a lantern, mud-brick buildings background, warm colors, 2D character portrait",
    "detective": "Mysterious detective in arabian-inspired outfit with a magnifying glass and notebook, searching for clues, dark alley background, intense focused expression, 2D character art",
    "bodyguard": "Powerful warrior in traditional arabian armor with a large shield, protective stance, muscular build, desert fortress background, bronze and steel tones, 2D character art",
    "king": "Majestic arabian king on ornate throne, golden crown, royal robes, sceptre in hand, grand palace hall with pillars, warm gold and crimson, 2D royal portrait",
    "mayor": "Dignified mayor figure in formal arabian attire, standing at a podium, scroll in hand, village council chamber background, wise expression, 2D character portrait",
    "doctor": "Traditional arabian healer with herbal pouch, surgical mask, holding medical tools, cozy lamp-lit tent interior with medicine shelves, caring expression, 2D character art",
    "seductress": "Enchanting arabian dancer with flowing silk veil, mysterious smile, dark eyeshadow, intricate gold jewelry, moonlit balcony background, elegant and dangerous, 2D character art",
    "om_zaki": "Elderly arabian grandmother with a knowing smirk, traditional embroidered dress, holding a small dagger hidden in her sleeve, wise weathered face, 2D character portrait",
    "werewolf_victory": "Werewolf pack howling at giant crimson moon, defeated village in background, victory stance, dark fantasy scene, cinematic wide shot, 2D illustration",
    "villager_victory": "Village celebration at sunrise, villagers cheering, werewolf pelts on display, children playing, hopeful triumphant atmosphere, warm golden lighting, 2D illustration",
}

ROLES_CONFIG = {
    "werewolf": {
        "name": "الذيب",
        "emoji": "🐺",
        "image": GAME_GRAPHICS["werewolf"],
        "description": "يحاول التخلص من جميع الشخصيات والسيطرة على اللعبة بالكامل.",
        "team": "werewolf",
        "night_action": True,
    },
    "villager": {
        "name": "القروي",
        "emoji": "🧑‍🌾",
        "image": GAME_GRAPHICS["villager"],
        "description": "شخصية عادية، ما عنده قدرة خاصة لكن يشارك بالتصويت ويكشف الذيابة بالذكاء والتحليل.",
        "team": "village",
        "night_action": False,
    },
    "mayor": {
        "name": "العمدة",
        "emoji": "🏛️",
        "image": GAME_GRAPHICS["mayor"],
        "description": "صوته أقوى من الجميع، حيث يُحسب التصويت الخاص فيه بصوتين!",
        "team": "village",
        "night_action": False,
    },
    "detective": {
        "name": "المحقق",
        "emoji": "🔍",
        "image": GAME_GRAPHICS["detective"],
        "description": "يقدر يكشف هوية أي لاعب مرة واحدة فقط طوال الجيم.",
        "team": "village",
        "night_action": True,
    },
    "doctor": {
        "name": "الطبيب",
        "emoji": "⚕️",
        "image": GAME_GRAPHICS["doctor"],
        "description": "يستطيع حماية أي لاعب من القتل كل ليلة (يقدر يحمي نفسه، وما يقدر يكرر نفس الشخص).",
        "team": "village",
        "night_action": True,
    },
    "bodyguard": {
        "name": "الحارس",
        "emoji": "🛡️",
        "image": GAME_GRAPHICS["bodyguard"],
        "description": "يعطي درع حماية لأي لاعب ويحميه من القتل مرة واحدة فقط بالقيم.",
        "team": "village",
        "night_action": True,
    },
    "seductress": {
        "name": "المغرية",
        "emoji": "💃",
        "image": GAME_GRAPHICS["seductress"],
        "description": "كل ليلة تزور شخص. إذا كان ذيب تموت معه. إذا كان شخص عادي وهاجمته الذئابة تحميه.",
        "team": "village",
        "night_action": True,
    },
    "om_zaki": {
        "name": "أم زكي",
        "emoji": "👵",
        "image": GAME_GRAPHICS["om_zaki"],
        "description": "إذا قتلتها الذئابة، تقوم بفضح أحد الذيابة قبل موتها في الشات العام.",
        "team": "village",
        "night_action": False,
    },
    "king": {
        "name": "الملك",
        "emoji": "👑",
        "image": GAME_GRAPHICS["king"],
        "description": "يملك سلطة تحويل جميع الأصوات على لاعب واحد وطرده مباشرة مرة واحدة فقط بالقيم.",
        "team": "village",
        "night_action": False,
    },
}

NIGHT_ROLES_ACTION = ["detective", "doctor", "bodyguard", "seductress"]

DEATH_MESSAGES = [
    "🕊️ طيروا جبهة {player}.. عظم الله أجركم فيه وخيرها بغيرها!",
    "💀 {player} ودعنا.. خلصت النبضات يا جماعة الخير!",
    "😴 {player} رقد وما قام.. النومة الأبدية ياصاحبي!",
    "🌬️ شيلوا {player} طار مع الريح! الله معاك يا حبيبنا",
    "🐑 {player} انذبح ذبح النعاج! عظم الله أجركم",
    "⚰️ طلع برا {player}.. المقعد ضيق وما يسعش لشخصين!",
    "☠️ {player} صفيناها! سوينا له تنقية عامة للقائمة",
    "🔪 {player} انغدر به محد درى عنه للأسف!",
    "😭 وداعاً {player}.. ما كان يعرف إنها آخر جلسة لعب",
    "🎭 انفضح أمر {player} وطيرناه برا!",
    "🚀 {player} طار صاروخ! ما شاء الله سرعة انطلاقه",
    "🪦 {player} صار قبره في وسع الصحرا.. الله يرحمه",
    "💔 {player} خذوه رحمة الله.. كان فاضي بس والله",
    "🥀 {player} ذبلت وردته وطحت! خلاص مشى",
    "🔥 {player} طار بالهواء! بسبب السوالف الزايدة",
]

WEREWOLF_WIN_MESSAGES = [
    "🐺 انتصرت الذئاب! القرويين كلهم صاروا عشاء فاخر! ألف مبروك يا وحوش 🌕",
    "🐺 الذئاب فازت ألف مبروك! القرويين كانوا قطيع غنم وهم نايمين! استاهلوا 😂",
    "🐺 فوز ساحق للذئاب! يا ناس القرويين كانوا فاضحين حقيقة 🎉👏",
]

VILLAGER_WIN_MESSAGES = [
    "🎉 القرويون انتصروا! طلعتوا الذئاب من جحورهم ودحدرتوهم! ما عليكم إلا العوض يا ذياب 😂",
    "🎉 القرية فازت! الذئاب انجلدت جلدة عمرها وتستاهل! أبطال والله 💪",
    "🎉 انتصار القرويين! الذئاب راحت فيها وصارت عظم بالصحراء ☠️😂",
]

SEDUCER_DEATH_MESSAGES = [
    "💃 {seducer} زارت {target} وطلعت ذيب! ماتوا سوا يا ناس 🔥🐺",
    "💃 {seducer} اكتشفت أن {target} ذيب وقضت عليه! بس راحت معاه 🌙",
    "💃 المغرية {seducer} ضحّت بنفسها عشان تكشف {target}! تصفيق 👏",
]

SEDUCER_SAVE_MESSAGES = [
    "💃 {seducer} كانت عند {target} الليلة! الذئاب هجموا عليه بس هي حمته 💪",
    "💃 المغرية {seducer} أنقذت {target} من براثن الذئابة!",
]

OM_ZAKI_EXPOSE_MESSAGES = [
    "👵 أم زكي قبل لا تموت: **{werewolf}** هو الذيب! فضحته لكم 😱😱",
    "👵 أم زكي فضحت أحد الذيابة قبل وفاتها: **{werewolf}** ذيب يا ناس! ☠️",
    "👵 أم زكي صاحت: {werewolf} ذيب! خذوه قبل لا يهرب 🐺🚨",
]

DETECTIVE_REVEAL_PHRASES = [
    "🔍 بعد تحري دقيق، **{target}** هو {emoji} **{role}**!",
    "🔍 المحقق كشف المستور: **{target}** = {emoji} **{role}**!",
]

BODYGUARD_SAVE_MSGS = [
    "🛡️ الحارس حمى {player} من الموت الليلة! درعه ما ينكسر 💪",
    "🛡️ {player} كان ميت لولا الحارس! حماية بطولية 🔥",
]

DOCTOR_HEAL_MSGS = [
    "⚕️ الطبيب عالج {player} وأنقذه من الموت! حكمة يدويه 💉",
    "⚕️ {player} نجا بفضل الطبيب! حقنة في وقتها 🔄",
]

KING_DECREE_MSGS = [
    "👑 الملك أصدر أمره: {player} يُطرد فوراً! ما حد يعارض أمر الملك 📜",
    "👑 بأمر الملك: {player} برا اللعبة! الملك يقرر والكل ينفذ ⚖️",
]

MAYOR_VOTE_NOTIFY = "🏛️ العمدة **{player}**: صوت = **{votes}** (صوتين)"

LOBBY_GUIDE_TEXT = (
    "**🎮 لعبة الذئب (Werewolf) - الدليل الشامل**\n\n"
    "**📖 القصة:**\n"
    "في قرية صغيرة، فيه ذئاب شريرة متخفية بين القرويين. النهار الكل يتصوت، والليل الذئاب تقتل!\n\n"
    "**👥 الأدوار (9 شخصيات):**\n\n"
    "**🐺 الذيب** - فريقه: الذئاب\n"
    "يحاول التخلص من جميع الشخصيات والسيطرة على اللعبة بالكامل.\n\n"
    "**🧑‍🌾 القروي** - فريقه: القرية\n"
    "شخصية عادية، ما عنده قدرة خاصة لكن يشارك بالتصويت.\n\n"
    "**🔍 المحقق** - فريقه: القرية\n"
    "يقدر يكشف هوية أي لاعب **مرة واحدة** فقط.\n\n"
    "**🛡️ الحارس** - فريقه: القرية\n"
    "يعطي درع حماية لأي لاعب ويحميه من القتل **مرة واحدة**.\n\n"
    "**👑 الملك** - فريقه: القرية\n"
    "يملك سلطة طرد أي لاعب مباشرة **مرة واحدة** (بدون تصويت).\n\n"
    "**🏛️ العمدة** - فريقه: القرية\n"
    "صوته يحسب بـ **صوتين** في التصويت النهاري.\n\n"
    "**⚕️ الطبيب** - فريقه: القرية\n"
    "يقدر يحمي شخص كل ليلة (يقدر يحمي نفسه).\n\n"
    "**💃 المغرية** - فريقه: القرية\n"
    "تزور شخص بالليل: لو كان ذيب يموتون سوا، لو طبيعي تحميه.\n\n"
    "**👵 أم زكي** - فريقه: القرية\n"
    "إذا ماتت على يد الذئاب تفضح واحد منهم قبل لا تموت.\n\n"
    "**🏆 الفوز:**\n"
    "• القرية تفوز إذا ماتت كل الذئاب 🎉\n"
    "• الذئاب تفوز إذا صار عددهم >= عدد القرويين 🐺\n\n"
    "**⭐ استمتعوا باللعبة!**"
)

DEVELOPER_INFO = "**🛠️ مطور البوت**\n\n**الاسم:** Laaw.q\n**الإنستغرام:** i7_tp2\n\nتم تطوير هذا البوت بعناية ❤️"

COLOR_PRIMARY = 0x2b2d31
COLOR_SUCCESS = 0x57F287
COLOR_DANGER = 0xED4245
COLOR_NIGHT = 0x1a1a2e
COLOR_DAY = 0xf5d742
COLOR_LOBBY = 0x5865F2
