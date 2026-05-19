import os

MIN_PLAYERS = 6
MAX_PLAYERS = 20
LOBBY_COUNTDOWN = 60
NIGHT_DURATION = 50
VOTE_DURATION = 60
DISCUSS_DURATION = 30

ROLE_INFO = {
    "wolf": {
        "emoji": "🐺", "name": "الذيب", "team": "wolf", "night_action": True,
        "desc": "تصوت مع باقي الذيابة بالليل لاغتيال شخص. تفوزون عندما يصبح عددكم ≥ القرويين.",
        "ability": "تقتل لاعباً كل ليلة"
    },
    "villager": {
        "emoji": "🧑‍🌾", "name": "القروي", "team": "village", "night_action": False,
        "desc": "ليس لديك قدرة خاصة. تعتمد على تحليلك وصوتك في النهار لفضح الذيابة.",
        "ability": "لا توجد"
    },
    "detective": {
        "emoji": "🔍", "name": "المحقق", "team": "village", "night_action": True,
        "desc": "تستطيع كشف هوية أي لاعب (مرة واحدة فقط في اللعبة).",
        "ability": "تكشف هوية لاعب (مرة واحدة)"
    },
    "guardian": {
        "emoji": "🛡️", "name": "الحارس", "team": "village", "night_action": True,
        "desc": "تحمي لاعباً واحداً من هجوم الذيابة (مرة واحدة فقط).",
        "ability": "تحمي لاعباً (مرة واحدة)"
    },
    "king": {
        "emoji": "👑", "name": "الملك", "team": "village", "night_action": False,
        "desc": "تقلب كل الأصوات على لاعب واحد وتخرجه فوراً. تستخدمها مرة أثناء التصويت.",
        "ability": "تقلب الأصوات وتطرد لاعباً (مرة واحدة)"
    },
    "mayor": {
        "emoji": "🏛️", "name": "العمدة", "team": "village", "night_action": False,
        "desc": "قدرة خاملة: صوتك في التصويت يحسب بصوتين.",
        "ability": "صوتك = 2 أصوات"
    },
    "doctor": {
        "emoji": "⚕️", "name": "الطبيب", "team": "village", "night_action": True,
        "desc": "تحمي لاعباً واحداً كل ليلة من الموت (تستطيع حماية نفسك).",
        "ability": "تحمي لاعباً كل ليلة"
    },
    "seductress": {
        "emoji": "💃", "name": "المغرية", "team": "village", "night_action": True,
        "desc": "تختارين شخصاً كل ليلة. إن كان ذئباً تموتين معه. إن كان بريئاً وهاجمه الذيابة تموتين بداله.",
        "ability": "تختبر شخصاً كل ليلة"
    },
    "um_fadi": {
        "emoji": "👵", "name": "أم فادي", "team": "village", "night_action": False,
        "desc": "إن قتلك الذيابة بالليل، يفضح البوت أحد الذيابة عشوائياً قبل أن تودعي.",
        "ability": "تكشف ذيباً إذا ماتت"
    }
}

SPECIAL_ROLES = ["detective", "doctor", "king", "mayor", "guardian", "seductress", "um_fadi"]
