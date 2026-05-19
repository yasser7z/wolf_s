"""
config.py — Werewolf Bot v3.0
================================
All constants, role definitions, image URLs, developer info,
phase banners, game rules text, and the full social-commentary
dictionary (Arabic / Saudi humour).

Every image URL below is a placeholder from placehold.co —
the developer can replace any URL with their own artwork.
"""

import os
import random

# ═══════════════════════════════════════════════════════════════
# 1. GAME TIMING CONSTANTS
# ═══════════════════════════════════════════════════════════════

MIN_PLAYERS       = 6          # Minimum to start
MAX_PLAYERS       = 20         # Lobby cap
LOBBY_COUNTDOWN   = 60         # Seconds before lobby auto-starts
NIGHT_DURATION    = 50         # Seconds for night phase
VOTE_DURATION     = 60         # Seconds for voting phase
DISCUSS_DURATION  = 30         # Seconds for day discussion before voting

# ═══════════════════════════════════════════════════════════════
# 2. BOT CORE CONFIG
# ═══════════════════════════════════════════════════════════════

BOT_PREFIX       = "-"
TOKEN            = os.getenv("DISCORD_TOKEN")

# ═══════════════════════════════════════════════════════════════
# 3. PHASE BANNERS — one image per phase, swapped dynamically
# ═══════════════════════════════════════════════════════════════

PHASE_IMAGES = {
    "lobby":    "https://placehold.co/800x200/1a1a2e/eaeaea?text=🐺+Werewolf+Lobby&font=source-code-pro",
    "night":    "https://placehold.co/800x200/0d0d1a/7b7baf?text=🌙+Night+Phase&font=source-code-pro",
    "day":      "https://placehold.co/800x200/1a2e1a/bdeabd?text=☀️+Day+Phase&font=source-code-pro",
    "voting":   "https://placehold.co/800x200/2e1a1a/eabdbd?text=🗳️+Voting+Time&font=source-code-pro",
    "gameover": "https://placehold.co/800x200/1a1a2e/eaeaea?text=🏆+Game+Over&font=source-code-pro",
}

# ═══════════════════════════════════════════════════════════════
# 4. DEVELOPER CREDIT
# ═══════════════════════════════════════════════════════════════

DEV_DISCORD    = "Laaw.q"
DEV_INSTAGRAM  = "i7_tp2"
FOOTER_TEXT    = "تحفظ كل الحقوق لي Vale Community"

# ═══════════════════════════════════════════════════════════════
# 5. ROLE DEFINITIONS  (9 roles, each with name, emoji, image)
# ═══════════════════════════════════════════════════════════════

ROLE_INFO = {
    "wolf": {
        "emoji": "🐺",
        "name": "الذيب",
        "team": "wolf",
        "night_action": True,
        "desc": "تصوت مع باقي الذيابة بالليل لاغتيال شخص. تفوزون عندما يصبح عددكم ≥ القرويين.",
        "ability": "🗡️ تقتل لاعباً كل ليلة",
        "image_url": "https://placehold.co/400x200/2d1b3e/ffffff?text=🐺+Wolf&font=source-code-pro",
    },
    "villager": {
        "emoji": "🧑‍🌾",
        "name": "القروي",
        "team": "village",
        "night_action": False,
        "desc": "ليس لديك قدرة خاصة. تعتمد على تحليلك وصوتك في النهار لفضح الذيابة.",
        "ability": "— لا توجد",
        "image_url": "https://placehold.co/400x200/3a5a3a/ffffff?text=🌾+Villager&font=source-code-pro",
    },
    "detective": {
        "emoji": "🔍",
        "name": "المحقق",
        "team": "village",
        "night_action": True,
        "desc": "تستطيع كشف هوية أي لاعب (مرة واحدة فقط في اللعبة). اختر بحكمة!",
        "ability": "🔎 تكشف هوية لاعب (مرة واحدة)",
        "image_url": "https://placehold.co/400x200/1a3e5a/ffffff?text=🔍+Detective&font=source-code-pro",
    },
    "guardian": {
        "emoji": "🛡️",
        "name": "الحارس",
        "team": "village",
        "night_action": True,
        "desc": "تحمي لاعباً واحداً من هجوم الذيابة (مرة واحدة فقط في اللعبة).",
        "ability": "🛡️ تحمي لاعباً (مرة واحدة)",
        "image_url": "https://placehold.co/400x200/2a4a3a/ffffff?text=🛡️+Guardian&font=source-code-pro",
    },
    "king": {
        "emoji": "👑",
        "name": "الملك",
        "team": "village",
        "night_action": False,
        "desc": "تقلب كل الأصوات على لاعب واحد وتخرجه فوراً من اللعبة. تستخدمها مرة أثناء التصويت.",
        "ability": "👑 تقلب الأصوات وتطرد لاعباً (مرة واحدة)",
        "image_url": "https://placehold.co/400x200/5a4a2a/ffffff?text=👑+King&font=source-code-pro",
    },
    "mayor": {
        "emoji": "🏛️",
        "name": "العمدة",
        "team": "village",
        "night_action": False,
        "desc": "قدرة خاملة: صوتك في التصويت يحسب بصوتين بدلاً من واحد.",
        "ability": "🏛️ صوتك = 2 أصوات",
        "image_url": "https://placehold.co/400x200/2a3a5a/ffffff?text=🏛️+Mayor&font=source-code-pro",
    },
    "doctor": {
        "emoji": "⚕️",
        "name": "الطبيب",
        "team": "village",
        "night_action": True,
        "desc": "تحمي لاعباً واحداً كل ليلة من الموت. تستطيع حماية نفسك أيضاً.",
        "ability": "💊 تحمي لاعباً كل ليلة",
        "image_url": "https://placehold.co/400x200/2a5a4a/ffffff?text=⚕️+Doctor&font=source-code-pro",
    },
    "seductress": {
        "emoji": "💃",
        "name": "المغرية",
        "team": "village",
        "night_action": True,
        "desc": "تختارين شخصاً كل ليلة. إن كان ذئباً تموتين معه. إن كان بريئاً وهاجمه الذيابة تموتين بداله وتحمينه.",
        "ability": "❤️‍🔥 تختبر شخصاً كل ليلة",
        "image_url": "https://placehold.co/400x200/5a2a3a/ffffff?text=💃+Seductress&font=source-code-pro",
    },
    "um_fadi": {
        "emoji": "👵",
        "name": "أم فادي",
        "team": "village",
        "night_action": False,
        "desc": "قدرة خاملة: إن قتلك الذيابة بالليل، يفضح البوت أحد الذيابة عشوائياً قبل أن تودعي اللعبة.",
        "ability": "👵 تكشف ذيباً إذا ماتت",
        "image_url": "https://placehold.co/400x200/3a2a5a/ffffff?text=👵+Um+Fadi&font=source-code-pro",
    },
}

# Roles that have unique special abilities (subset used when slots are tight)
SPECIAL_ROLES = [
    "detective", "doctor", "king", "mayor",
    "guardian", "seductress", "um_fadi",
]

# ═══════════════════════════════════════════════════════════════
# 6. GAME RULES TEXT (for the 📖 شرح اللعبة embed)
# ═══════════════════════════════════════════════════════════════

RULES_INTRO = """
**🐺 لعبة الذئب (Werewolf)** — لعبة اجتماعية تعتمد على التخمين والتحليل النفسي.

تنقسم القرية إلى فريقين:
• **🧑‍🌾 القرويون** — مهمتهم اكتشاف الذيابة وطردهم قبل أن يفنوهم.
• **🐺 الذيابة** — يتخفون بين القرويين ويغتالونهم كل ليلة.

**🏆 شروط الفوز:**
• **القرويون:** يطردون كل الذيابة (يصبح عدد الذيابة = 0).
• **الذيابة:** يصبح عددهم ≥ عدد القرويين الأحياء.

**🔄 سير اللعبة:**
1. **🌙 الليل:** ينام الجميع. الذين يملكون قدرات يصحون ويستخدمونها في السر.
2. **☀️ النهار:** يستيقظ الجميع، يعلن البوت عمن قتل، ثم يتناقش اللاعبون.
3. **🗳️ التصويت:** يصوت الجميع على من يشتبه به لإعدامه.
4. 🔄 تتكرر الدورة حتى فوز أحد الفريقين.

**💡 نصيحة:** القرويون يعتمدون على التحليل والاستنتاج. الذيابة يعتمدون على التمويه والتضليل.
"""

def build_rules_embed() -> "discord.Embed":
    """Build the full rules embed with all role descriptions."""
    import discord
    embed = discord.Embed(
        title="📖 شرح اللعبة الكامل",
        description=RULES_INTRO,
        color=discord.Color.blue(),
    )
    for rkey, rinfo in ROLE_INFO.items():
        embed.add_field(
            name=f"{rinfo['emoji']} {rinfo['name']} ({rinfo['team']})",
            value=f"{rinfo['desc']}\n✦ قدرة: {rinfo['ability']}",
            inline=False,
        )
    embed.set_footer(text=FOOTER_TEXT)
    return embed

# ═══════════════════════════════════════════════════════════════
# 7. SOCIAL COMMENTARY — Arabic / Saudi Humour Dictionary
# ═══════════════════════════════════════════════════════════════

DEATH_ROASTS = [
    "طيروا جبهته 🌚 عظم الله أجركم في {name}",
    "مسكين {name} .. مدري ليه جرب حظه مع الذيابة 🐺",
    "{name} ودعنا .. كان عنده عزيمة بس الحظ ما خدمه 😂",
    "الليلة {name} في ذمة الله .. والذياب يعدون الفلوس 🐺💰",
    "والله من بدري كان مكتوب على جبهة {name} (خروج) 💀",
    "{name} صكها مع الذياب ودخل في ذمة التاريخ 🪦",
    "ياخي {name} طلع خروف بين ذياب 🐑🐺",
    "الله يرحمك يا {name} .. كنت إنسان طيب بس شكلك مشبوه 😂",
    "{name} اكتشف متأخر انه في غابة ذياب 🐺",
    "حسبنا الله ونعم الوكيل .. {name} انتهى مشواره 🪦",
    "يا {name} والله انك ضحية فيلم رعب 🔪",
    "{name} فكنا من شرك .. نم قرير العين 🛌💀",
    "اللي ما يطول العنب .. {name} حامض عنه 😂",
    "{name} ! انصدمت من النتيجة؟ 🤯",
    "الناس تغدي على بعض .. و {name} مات على العشاء 🍽️💀",
]

WOLF_WIN_ROASTS = [
    "🐺🐺 انتصار الذيابة!\nالقرويين كانوا يحسبون أنهم فاهمين اللعبة بس الذياب كانوا فالمطبخ من البداية 😂\nيلا يا قرويين، العيد غير مرة 🎮",
    "🐺 الذياب قالوا:\n'هذي القرية ملكنا يا جماعة الخير! القرويين يا حلوين شكل موسمكم انتهى 😂'\nمبروك للذيبان الشجعان! 🏆",
    "🐺🐺🐺 الذياب فازوا ولا عليكم امر!\nترى ما يجيب الذيب إلا القروي اللي ما يعرف يخبي 🐑\nيلا ورونا شطارتكم المرة الجاية 😂",
    "🐺 القصة بدأت وانتهت بسرعة .. القرويين كانوا ديكور 😂\nالذيبان يستلمون القرية اليوم! 🏘️👑",
    "🐺 الذيب إذا جاء يخطف ما يفرق معه كبير ولا صغير .. القرويين طاروا واحد ورا الثاني 😂\nمبروك الذيبان الأبطال! 🎉",
]

VILLAGE_WIN_ROASTS = [
    "🎉🎊 القرويين أبطال! 🎊🎉\nخلصنا من شر الذياب وقالوا:\n'يلا يا ذيبان، فيه موسم ثاني وبتشوفونا 💪'\nمبروك للقرية المقدامة! 🔥",
    "🎉 انتصار القرويين!\nالذياب كانوا يحسبون اللعبة سهلة بس القرويين عطوهم درس في الفلاحة 😂\nيلا يا ذيبان ورونا شطارتكم في الجاي 🐺",
    "🎊 القرويين سحلوها!\nمن قد ما الذياب كانوا واثقين، القرويين قلبوا الطاولة عليهم 🔄\nمبروك يا أبطال! تستاهلون ✅",
    "🎊 القرية انتصرت والذيبان يعدون الحساب!\nالقرويين أثبتوا ان اللي ما يعرف الصقر يشويه 🔥\nالذيبان انفضحوا وانكشف مستواهم 😂",
    "🎉 خلاص يا ذيبان .. انتهى العز 😂\nالقرويين أظهروكم على حقيقتكم 🐺➡️🐑\nيللا وراكم ورا 🏃💨",
]

NIGHT_COMMENTS = [
    "الذياب ما قصروا هالليلة .. انتقوا ضحيتهم بعناية 😂",
    "الليل كان طويل والذيبان كانوا جوعانين 🐺",
    "صوت عظام الضحايا يتكسر في ظلمة الليل 🦴",
    "الذيبان يسهرون والقرية نايمة .. تصير خير 😂",
    "ها قد جاء الليل .. والذياب يدورون عشاء 🐺🍽️",
]

NIGHT_SAFE_COMMENTS = [
    "الليلة كانت هادئة .. الذياب نايمين ولا شفنا لهم خبر 😂",
    "لا قتلى ولا عزاء .. الذياب فيهم خير هالليلة 🤷",
    "الذيبان مساكين ما لقوا ضحية .. عسى الله يعينهم بكرة 🐺💔",
]

VOTE_COMMENTS = [
    "التصويت فتح .. والكل يبي يطقطق على الثالث 😂",
    "كل واحد يصوت على الثاني .. والذيب واقف يتفرج 🐺",
    "ترى يا جماعة .. اللي يصوت عشانه ما عنده سالفة 😂",
]

def random_death_roast(name: str) -> str:
    return random.choice(DEATH_ROASTS).format(name=name)

def random_wolf_win() -> str:
    return random.choice(WOLF_WIN_ROASTS)

def random_village_win() -> str:
    return random.choice(VILLAGE_WIN_ROASTS)

def random_night_comment(killed: bool = True) -> str:
    pool = NIGHT_COMMENTS if killed else NIGHT_SAFE_COMMENTS
    return random.choice(pool)

def random_vote_comment() -> str:
    return random.choice(VOTE_COMMENTS)
