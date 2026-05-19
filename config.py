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
    "lobby_banner": "https://placehold.co/600x300?text=Lobby+Banner",
    "night_phase": "https://placehold.co/600x300?text=Night+Phase",
    "day_phase": "https://placehold.co/600x300?text=Day+Phase",
    "werewolf": "https://placehold.co/400x400?text=Werewolf",
    "villager": "https://placehold.co/400x400?text=Villager",
    "witch": "https://placehold.co/400x400?text=Witch",
    "seer": "https://placehold.co/400x400?text=Seer",
    "hunter": "https://placehold.co/400x400?text=Hunter",
    "detective": "https://placehold.co/400x400?text=Detective",
    "bodyguard": "https://placehold.co/400x400?text=Bodyguard",
    "king": "https://placehold.co/400x400?text=King",
    "mayor": "https://placehold.co/400x400?text=Mayor",
    "doctor": "https://placehold.co/400x400?text=Doctor",
    "seductress": "https://placehold.co/400x400?text=Seductress",
    "om_zaki": "https://placehold.co/400x400?text=Om+Zaki",
    "werewolf_victory": "https://placehold.co/600x300?text=Werewolves+Win",
    "villager_victory": "https://placehold.co/600x300?text=Villagers+Win",
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
