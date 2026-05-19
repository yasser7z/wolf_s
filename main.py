import discord
from discord.ext import commands
from discord.ui import View, Button, Select
import asyncio
import os
import random
from threading import Thread
from flask import Flask
from config import *
from game_engine import WerewolfGame

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is alive!"


def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents, help_command=None)

active_games = {}


def make_embed(title, description, color, image_key, footer=True):
    embed = discord.Embed(title=title, description=description, color=color)
    if image_key and image_key in GAME_GRAPHICS:
        embed.set_image(url=GAME_GRAPHICS[image_key])
    if footer:
        embed.set_footer(text=FOOTER_TEXT)
    return embed


def get_humor(category):
    items = HUMOR.get(category, [])
    if items:
        return random.choice(items)
    return ""


def format_player_list(game):
    lines = []
    for mid in game.player_order:
        p = game.players[mid]
        if not p:
            continue
        status = "🟢" if p.alive else "🔴"
        role_info = ""
        if not p.alive and p.role_name and p.role_name in ROLES:
            role_info = f" ({ROLES[p.role_name]['emoji']} {ROLES[p.role_name]['name_ar']})"
        mention = f"<@{mid}>"
        if not p.alive:
            mention = f"~~{mention}~~"
        lines.append(f"{status} {mention}{role_info}")
    return "\n".join(lines)


async def update_lobby_message(game, channel):
    try:
        msg = await channel.fetch_message(game.lobby_message_id)
    except Exception:
        return

    players_str = format_player_list(game)
    embed = make_embed(
        f"🐺 ذئب VALE | لوبي",
        f"**قم بدعوة أصدقائك وانطلقوا في المغامرة!**\n\n{players_str}\n\n**عدد اللاعبين:** {len(game.players)}/{MAX_PLAYERS}\n━━━━━━━━━━━━━━━━\n**المطور:** {DEVELOPER['discord']} | {DEVELOPER['instagram']}",
        0x1a1a2e,
        "lobby"
    )
    await msg.edit(embed=embed)


async def try_dm_user(user_id, content=None, embed=None, view=None):
    try:
        user = await bot.fetch_user(user_id)
        if content:
            await user.send(content, embed=embed, view=view)
        elif embed:
            await user.send(embed=embed, view=view)
        elif view:
            await user.send(view=view)
        else:
            await user.send(content)
        return True
    except Exception:
        return False


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    game_channels = list(active_games.keys())
    for cid in game_channels:
        active_games[cid].cleanup()
        del active_games[cid]


@bot.command(name='ذئب')
async def start_lobby(ctx):
    if ctx.channel.id in active_games:
        game = active_games[ctx.channel.id]
        if game.phase == "lobby":
            await ctx.send(f"⚠️ في لوبي شغال في هالروم! استعمل الأزرار عشان تنضم.")
            return
        await ctx.send("⚠️ في جيم شغال في هالروم! استعمل -ايقاف عشان توقف الجيم القديم")
        return

    game = WerewolfGame(ctx.channel.id, ctx.author.id)
    game.add_player(ctx.author.id, ctx.author.display_name)
    active_games[ctx.channel.id] = game

    players_str = format_player_list(game)
    embed = make_embed(
        f"🐺 ذئب VALE | لوبي",
        f"**قم بدعوة أصدقائك وانطلقوا في المغامرة!**\n\n{players_str}\n\n**عدد اللاعبين:** {len(game.players)}/{MAX_PLAYERS}\n━━━━━━━━━━━━━━━━\n**المطور:** {DEVELOPER['discord']} | {DEVELOPER['instagram']}",
        0x1a1a2e,
        "lobby"
    )

    view = LobbyView(game, ctx.author.id)
    msg = await ctx.send(embed=embed, view=view)
    game.lobby_message_id = msg.id

    game.timer_task = asyncio.create_task(lobby_timer(ctx.channel, game))
    await ctx.message.delete()


@bot.command(name='ايقاف')
async def stop_game(ctx):
    if ctx.channel.id not in active_games:
        await ctx.send("⚠️ مافي جيم شغال عشان توقفه!")
        return

    game = active_games[ctx.channel.id]
    if ctx.author.id != game.creator_id:
        await ctx.send("⚠️ فقط منشئ الجيم يقدر يوقفه!")
        return

    if game.timer_task:
        game.timer_task.cancel()
        game.timer_task = None

    channel = ctx.channel
    game.cleanup()
    del active_games[ctx.channel.id]

    embed = make_embed(
        "✅ تم إيقاف الجيم",
        "تم تصفير الذاكرة وجاهزين لجيم جديد.",
        0x00ff00,
        None
    )
    await ctx.send(embed=embed)


async def lobby_timer(channel, game):
    try:
        for remaining in range(LOBBY_TIMEOUT, 0, -1):
            await asyncio.sleep(1)
            if game.phase != "lobby" or game.game_over:
                return
            if remaining % 30 == 0 or remaining <= 10:
                try:
                    msg = await channel.fetch_message(game.lobby_message_id)
                    embed = msg.embeds[0]
                    players_str = format_player_list(game)
                    timer_line = f"\n\n**⏳ تلقائي خلال {remaining} ثانية** (يلزم {MIN_PLAYERS} لاعبين)" if remaining > 0 else ""
                    embed.description = f"**قم بدعوة أصدقائك وانطلقوا في المغامرة!**\n\n{players_str}\n\n**عدد اللاعبين:** {len(game.players)}/{MAX_PLAYERS}{timer_line}\n━━━━━━━━━━━━━━━━\n**المطور:** {DEVELOPER['discord']} | {DEVELOPER['instagram']}"
                    await msg.edit(embed=embed)
                except Exception:
                    pass

        if game.phase == "lobby" and len(game.players) >= MIN_PLAYERS:
            await start_game(channel, game)
    except asyncio.CancelledError:
        pass


async def start_game(channel, game):
    if game.phase != "lobby":
        return

    if len(game.players) < MIN_PLAYERS:
        await channel.send(f"⚠️ اللاعبين قليلين! نحتاج {MIN_PLAYERS} لاعبين على الأقل.")
        return

    success = game.distribute_roles()
    if not success:
        await channel.send("⚠️ صار خطأ في توزيع الأدوار.")
        return

    game.phase = "night"
    game.day_number = 1

    embed = make_embed(
        "🎮 الجيم بدأ!",
        f"{get_humor('game_start')}\n\n**تم توزيع الأدوار بنجاح!**\nتحقق من الرسائل الخاصة.",
        0x2d2d44,
        "lobby"
    )
    await channel.send(embed=embed)

    for mid, p in game.players.items():
        role_data = ROLES[p.role_name]
        embed = make_embed(
            f"{role_data['emoji']} دورك: {role_data['name_ar']}",
            f"**{role_data['description']}**\n\n**فريقك:** {'🐺 الذئاب' if role_data['team'] == 'wolf' else '🧑‍🌾 القرية'}",
            0x2d2d44 if role_data['team'] == 'village' else 0x4a0000,
            p.role_name
        )
        sent = await try_dm_user(mid, embed=embed)
        if not sent:
            game.players[mid].dm_failed = True

    wolves = game.get_wolves()
    if len(wolves) > 1:
        wolf_list = []
        for wid in wolves:
            w = game.players[wid]
            wolf_list.append(f"{ROLES['wolf']['emoji']} {w.display_name}")
        for wid in wolves:
            w = game.players[wid]
            if not w.dm_failed:
                embed = make_embed(
                    "🐺 زملاؤك الذئاب",
                    "رفاقك في الليل:\n" + "\n".join(wolf_list),
                    0x4a0000,
                    "wolf"
                )
                await try_dm_user(wid, embed=embed)

    await night_phase(channel, game)


async def night_phase(channel, game):
    game.phase = "night"
    game.reset_night_actions()
    game.votes = {}
    game.voted_players = set()

    night_embed = make_embed(
        f"🌙 الليل - اليوم {game.day_number}",
        f"{get_humor('night_fall')}\n\nالكل نام.. أصحاب القدرات يتواصلون معك في الخاص.",
        0x0d0d1a,
        "night"
    )
    await channel.send(embed=night_embed)

    tasks = []
    for mid, p in game.players.items():
        if not p.alive:
            continue

        role_data = ROLES.get(p.role_name)
        if not role_data:
            continue

        if role_data["team"] == "wolf" and p.role_name == "wolf":
            view = WolfNightView(game, channel.id)
            t = asyncio.create_task(send_night_dm(mid, p.role_name, game, view))
            tasks.append(t)

        elif p.role_name == "doctor":
            view = DoctorNightView(game, channel.id)
            t = asyncio.create_task(send_night_dm(mid, p.role_name, game, view))
            tasks.append(t)

        elif p.role_name == "seductress":
            view = SeductressNightView(game, channel.id)
            t = asyncio.create_task(send_night_dm(mid, p.role_name, game, view))
            tasks.append(t)

        elif p.role_name == "detective" and not p.used_ability:
            view = DetectiveNightView(game, channel.id)
            t = asyncio.create_task(send_night_dm(mid, p.role_name, game, view))
            tasks.append(t)

        elif p.role_name == "guard" and not p.used_ability:
            view = GuardNightView(game, channel.id)
            t = asyncio.create_task(send_night_dm(mid, p.role_name, game, view))
            tasks.append(t)

        elif p.role_name in ("villager", "mayor", "zeki_mom", "king"):
            embed = make_embed(
                "🌙 أنت نائم",
                "الليل حل والقرية ساكنة. انتظر حتى الصباح..",
                0x1a1a2e,
                "night"
            )
            await try_dm_user(mid, embed=embed)

    await asyncio.sleep(NIGHT_TIMEOUT)

    for t in tasks:
        t.cancel()

    game.process_night()

    await day_phase(channel, game)


async def send_night_dm(mid, role_name, game, view):
    try:
        user = await bot.fetch_user(mid)
        role_data = ROLES[role_name]
        embed = make_embed(
            f"{role_data['emoji']} حان دورك: {role_data['name_ar']}",
            f"اختر هدفك لهذه الليلة.\nلديك {NIGHT_TIMEOUT} ثانية.",
            0x1a1a2e,
            role_name
        )
        await user.send(embed=embed, view=view)
    except Exception:
        pass


async def day_phase(channel, game):
    game.phase = "day"

    night_deaths = game.night_deaths
    deaths_info = ""
    if not night_deaths:
        deaths_info = "🌅 **لا قتلى الليلة!** أحدهم حمى القرية."
    else:
        for dead_id in night_deaths:
            p = game.players.get(dead_id)
            if p:
                deaths_info += f"💀 **{p.display_name}** مات\n"
                deaths_info += f"> {get_humor('death_comments')}\n\n"

    exposed_info = ""
    if game.exposed_wolf:
        wolf_player = game.players.get(game.exposed_wolf)
        if wolf_player:
            exposed_info = f"\n👵 أم زكي فضحت **{wolf_player.display_name}** 🐺 قبل لا تموت!\n"

    day_embed = make_embed(
        f"☀️ النهار - اليوم {game.day_number}",
        f"{get_humor('day_break')}\n\n{deaths_info}{exposed_info}\n**اللاعبون الأحياء:**\n{format_player_list(game)}",
        0x2d2d44,
        "day"
    )
    await channel.send(embed=day_embed)

    winner = game.check_win()
    if winner:
        await game_over(channel, game, winner)
        return

    await asyncio.sleep(DISCUSSION_TIME)

    king_player = None
    for p in game.players.values():
        if p.role_name == "king" and p.alive and not p.used_ability:
            king_player = p
            break

    if king_player and not game.king_day_used:
        view = KingDayView(game, channel.id)
        try:
            user = await bot.fetch_user(king_player.member_id)
            embed = make_embed(
                "👑 استخدم سلطتك الملكية",
                "تقدر تجبر كل الأصوات على لاعب واحد اليوم. استخدمها؟",
                0xffd700,
                "king"
            )
            await user.send(embed=embed, view=view)
        except Exception:
            pass

    await asyncio.sleep(5)

    await voting_phase(channel, game)


async def voting_phase(channel, game):
    game.phase = "voting"
    game.votes = {}
    game.voted_players = set()

    vote_embed = make_embed(
        f"🗳️ التصويت - اليوم {game.day_number}",
        "**صوتوا على مين تبي تخرجون من القرية!**\nتحقق من الرسائل الخاصة.",
        0x2d2d44,
        "day"
    )
    await channel.send(embed=vote_embed)

    tasks = []
    for mid, p in game.players.items():
        if not p.alive:
            continue
        view = VoteView(game, channel.id)
        t = asyncio.create_task(send_vote_dm(mid, game, view))
        tasks.append(t)

    await asyncio.sleep(VOTE_TIMEOUT)

    for t in tasks:
        t.cancel()

    eliminated_id, vote_counts = game.process_votes()

    if eliminated_id:
        eliminated = game.players.get(eliminated_id)
        if eliminated:
            eliminated.alive = False
            embed = make_embed(
                "🗳️ نتيجة التصويت",
                f"**{eliminated.display_name}** طار من القرية!\n{get_humor('vote_comments')}",
                0x8b0000,
                None
            )
            await channel.send(embed=embed)
    else:
        embed = make_embed(
            "🗳️ نتيجة التصويت",
            "تعادل! ما أحد طار اليوم.",
            0xffa500,
            None
        )
        await channel.send(embed=embed)

    winner = game.check_win()
    if winner:
        await game_over(channel, game, winner)
    else:
        await asyncio.sleep(5)
        game.day_number += 1

        if game.king_target:
            game.king_target = None

        await night_phase(channel, game)


async def send_vote_dm(mid, game, view):
    try:
        user = await bot.fetch_user(mid)
        embed = make_embed(
            "🗳️ التصويت النهاري",
            f"اختر من تريد طرده من القرية.\nلديك {VOTE_TIMEOUT} ثانية.",
            0x2d2d44,
            "day"
        )
        await user.send(embed=embed, view=view)
    except Exception:
        pass


async def game_over(channel, game, winner):
    game.phase = "game_over"
    game.game_over = True

    if game.timer_task:
        game.timer_task.cancel()
        game.timer_task = None

    if winner == "wolves":
        embed = make_embed(
            "🐺 انتصرت الذئاب!",
            f"{get_humor('wolf_win')}\n\n**الذئاب الفائزة:**\n",
            0x4a0000,
            "wolf_win"
        )
        for mid, p in game.players.items():
            if p.role_name == "wolf" and p.alive:
                embed.description += f"🐺 {p.display_name}\n"
        embed.description += f"\n**القرويون الخاسرون:**\n"
        for mid, p in game.players.items():
            if p.role_name != "wolf":
                embed.description += f"{ROLES[p.role_name]['emoji']} {p.display_name}\n"
    else:
        embed = make_embed(
            "🧑‍🌾 انتصرت القرية!",
            f"{get_humor('village_win')}\n\n**الناجون:**\n",
            0x006400,
            "village_win"
        )
        for mid, p in game.players.items():
            if p.alive:
                embed.description += f"{ROLES[p.role_name]['emoji']} {p.display_name}\n"
        embed.description += f"\n**الذئاب المقتولة:**\n"
        for mid, p in game.players.items():
            if p.role_name == "wolf":
                embed.description += f"🐺 {p.display_name}\n"

    await channel.send(embed=embed)

    summary = "**📋 ملخص الأدوار:**\n"
    for mid in game.player_order:
        p = game.players[mid]
        status = "🔴 ميت" if not p.alive else "🟢 حي"
        summary += f"{ROLES[p.role_name]['emoji']} {p.display_name} - {ROLES[p.role_name]['name_ar']} ({status})\n"

    await channel.send(summary)

    game.cleanup()
    if channel.id in active_games:
        del active_games[channel.id]


class LobbyView(View):
    def __init__(self, game, creator_id):
        super().__init__(timeout=None)
        self.game = game
        self.creator_id = creator_id
        self.channel_id = game.channel_id

        join_btn = Button(label="➕ انضمام", style=discord.ButtonStyle.green, custom_id=f"ljoin_{self.channel_id}")
        join_btn.callback = self.join_callback
        self.add_item(join_btn)

        leave_btn = Button(label="❌ مغادرة", style=discord.ButtonStyle.red, custom_id=f"lleave_{self.channel_id}")
        leave_btn.callback = self.leave_callback
        self.add_item(leave_btn)

        guide_btn = Button(label="📖 شرح اللعبة", style=discord.ButtonStyle.blurple, custom_id=f"lguide_{self.channel_id}")
        guide_btn.callback = self.guide_callback
        self.add_item(guide_btn)

        dev_btn = Button(label="🛠️ مطور البوت", style=discord.ButtonStyle.grey, custom_id=f"ldev_{self.channel_id}")
        dev_btn.callback = self.dev_callback
        self.add_item(dev_btn)

        start_btn = Button(label="▶️ ابدأ", style=discord.ButtonStyle.primary, custom_id=f"lstart_{self.channel_id}")
        start_btn.callback = self.start_callback
        self.add_item(start_btn)

    async def join_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "lobby":
            await interaction.response.send_message("⚠️ اللعبة انتهت أو الجيم بدأ!", ephemeral=True)
            return
        if interaction.user.id in game.players:
            await interaction.response.send_message("⚠️ أنت منضم أصلاً!", ephemeral=True)
            return
        if len(game.players) >= MAX_PLAYERS:
            await interaction.response.send_message(f"⚠️ العدد máximo {MAX_PLAYERS} لاعبين!", ephemeral=True)
            return
        game.add_player(interaction.user.id, interaction.user.display_name)
        await interaction.response.send_message(f"✅ انضممت للعبة!", ephemeral=True)
        await update_lobby_message(game, interaction.channel)

    async def leave_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "lobby":
            await interaction.response.send_message("⚠️ اللعبة انتهت!", ephemeral=True)
            return
        if interaction.user.id not in game.players:
            await interaction.response.send_message("⚠️ أنت لست في اللعبة!", ephemeral=True)
            return
        if interaction.user.id == game.creator_id and len(game.players) > 1:
            game.creator_id = list(game.players.keys())[0] if list(game.players.keys())[0] != interaction.user.id else (list(game.players.keys())[1] if len(game.players) > 1 else game.creator_id)
            for mid in game.player_order:
                if mid != interaction.user.id:
                    game.creator_id = mid
                    break
        game.remove_player(interaction.user.id)
        await interaction.response.send_message("❌ غادرت اللعبة.", ephemeral=True)
        if len(game.players) == 0:
            game.cleanup()
            if self.channel_id in active_games:
                del active_games[self.channel_id]
            await interaction.channel.send("👋 اللوبي انتهى لأن آخر لاعب غادر.")
        else:
            await update_lobby_message(game, interaction.channel)

    async def guide_callback(self, interaction):
        embed = make_embed(
            "📖 شرح اللعبة",
            GAME_RULES,
            0x1a1a2e,
            None
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def dev_callback(self, interaction):
        embed = make_embed(
            "🛠️ مطور البوت",
            f"**ديسكورد:** {DEVELOPER['discord']}\n**إنستغرام:** {DEVELOPER['instagram']}",
            0x1a1a2e,
            None
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def start_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "lobby":
            await interaction.response.send_message("⚠️ اللعبة انتهت!", ephemeral=True)
            return
        if interaction.user.id != game.creator_id:
            await interaction.response.send_message("⚠️ فقط منشئ الجيم يقدر يبدأ!", ephemeral=True)
            return
        if len(game.players) < MIN_PLAYERS:
            await interaction.response.send_message(f"⚠️ نحتاج {MIN_PLAYERS} لاعبين على الأقل!", ephemeral=True)
            return

        if game.timer_task:
            game.timer_task.cancel()
            game.timer_task = None

        await interaction.response.send_message("✅ بدأنا!", ephemeral=True)
        await start_game(interaction.channel, game)


class WolfNightView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=NIGHT_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive and p.role_name != "wolf":
                options.append(discord.SelectOption(
                    label=p.display_name[:25],
                    value=str(mid),
                    description=f"اختيارك لليلة {game.day_number}",
                    emoji="🎯"
                ))

        if options:
            select = Select(
                placeholder="🎯 اختر ضحيتك..",
                options=options[:25],
                custom_id=f"wolf_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "night":
            await interaction.response.send_message("⚠️ الليل انتهى!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.wolf_target = target_id
        target = game.players.get(target_id)
        await interaction.response.send_message(
            f"✅ اخترت **{target.display_name if target else 'مجهول'}** كضحية لهذه الليلة.",
            ephemeral=True
        )
        self.stop()


class DoctorNightView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=NIGHT_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive:
                label = f"{'🛡️ ' if game.doctor_target == mid else ''}{p.display_name}"
                options.append(discord.SelectOption(
                    label=label[:25],
                    value=str(mid),
                    description="اختر من تحمي",
                    emoji="⚕️"
                ))

        if options:
            select = Select(
                placeholder="⚕️ اختر من تحمي هذه الليلة..",
                options=options[:25],
                custom_id=f"doc_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "night":
            await interaction.response.send_message("⚠️ الليل انتهى!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.doctor_target = target_id
        target = game.players.get(target_id)
        await interaction.response.send_message(
            f"✅ قررت تحمي **{target.display_name if target else 'مجهول'}** هذه الليلة.",
            ephemeral=True
        )
        self.stop()


class SeductressNightView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=NIGHT_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive:
                options.append(discord.SelectOption(
                    label=p.display_name[:25],
                    value=str(mid),
                    description="مقامرة خطيرة",
                    emoji="💃"
                ))

        if options:
            select = Select(
                placeholder="💃 اختاري من تزورين هذه الليلة..",
                options=options[:25],
                custom_id=f"sed_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "night":
            await interaction.response.send_message("⚠️ الليل انتهى!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.seductress_target = target_id
        target = game.players.get(target_id)
        await interaction.response.send_message(
            f"✅ زرتي **{target.display_name if target else 'مجهول'}** هذه الليلة. الله يعلم وش بيصير!",
            ephemeral=True
        )
        self.stop()


class DetectiveNightView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=NIGHT_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive and mid != game.get_player_by_role("detective").member_id if game.get_player_by_role("detective") else True:
                options.append(discord.SelectOption(
                    label=p.display_name[:25],
                    value=str(mid),
                    description="تحري",
                    emoji="🔍"
                ))

        if options:
            select = Select(
                placeholder="🔍 اختر لاعباً للتحري عنه..",
                options=options[:25],
                custom_id=f"det_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "night":
            await interaction.response.send_message("⚠️ الليل انتهى!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.detective_target = target_id
        target = game.players.get(target_id)

        det_player = game.get_player_by_role("detective")
        if det_player:
            det_player.used_ability = True

        if target and target.role_name:
            role_data = ROLES[target.role_name]
            result = f"{role_data['emoji']} **{role_data['name_ar']}**"
            if target.role_name == "wolf":
                result += " 🐺 ذيب! قبضت عليه!"
            else:
                result += " ✅ بريء."
        else:
            result = "لا تستطيع تحديد هويته."

        await interaction.response.send_message(
            f"🔍 **نتيجة التحري:** {target.display_name if target else 'مجهول'} هو {result}",
            ephemeral=True
        )
        self.stop()


class GuardNightView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=NIGHT_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive:
                options.append(discord.SelectOption(
                    label=p.display_name[:25],
                    value=str(mid),
                    description="احمِه من الذئاب",
                    emoji="🛡️"
                ))

        if options:
            select = Select(
                placeholder="🛡️ اختر من تحرس هذه الليلة..",
                options=options[:25],
                custom_id=f"guard_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "night":
            await interaction.response.send_message("⚠️ الليل انتهى!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.guard_target = target_id
        target = game.players.get(target_id)

        guard_player = game.get_player_by_role("guard")
        if guard_player:
            guard_player.used_ability = True

        await interaction.response.send_message(
            f"✅ الدرع يحمي **{target.display_name if target else 'مجهول'}** هذه الليلة.",
            ephemeral=True
        )
        self.stop()


class KingDayView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=30)
        self.game = game
        self.channel_id = channel_id
        self.value = None

        use_btn = Button(label="👑 استخدم السلطة", style=discord.ButtonStyle.primary, custom_id=f"king_use_{channel_id}")
        use_btn.callback = self.use_callback
        self.add_item(use_btn)

        skip_btn = Button(label="❌ لا", style=discord.ButtonStyle.secondary, custom_id=f"king_skip_{channel_id}")
        skip_btn.callback = self.skip_callback
        self.add_item(skip_btn)

    async def use_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game:
            await interaction.response.send_message("⚠️ اللعبة انتهت!", ephemeral=True)
            return

        king_player = None
        for p in game.players.values():
            if p.role_name == "king" and p.alive:
                king_player = p
                break

        if not king_player:
            await interaction.response.send_message("⚠️ الملك مات!", ephemeral=True)
            return

        king_player.used_ability = True
        game.king_day_used = True

        await interaction.response.send_message(
            "👑 **اختر ضحية سلطتك الملكية!**",
            ephemeral=True,
            view=KingTargetView(game, self.channel_id)
        )
        self.stop()

    async def skip_callback(self, interaction):
        await interaction.response.send_message("✅ تم تخطي استخدام السلطة الملكية.", ephemeral=True)
        self.stop()


class KingTargetView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=30)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive and p.role_name != "king":
                options.append(discord.SelectOption(
                    label=p.display_name[:25],
                    value=str(mid),
                    description="كل الأصوات ضده",
                    emoji="👑"
                ))

        if options:
            select = Select(
                placeholder="👑 اختر من تسلط عليه..",
                options=options[:25],
                custom_id=f"kingt_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game:
            await interaction.response.send_message("⚠️ اللعبة انتهت!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.king_target = target_id
        target = game.players.get(target_id)

        await interaction.response.send_message(
            f"👑 **أمر ملكي!** كل الأصوات ستتجه ضد **{target.display_name if target else 'مجهول'}**!",
            ephemeral=True
        )

        channel = bot.get_channel(self.channel_id)
        if channel:
            embed = make_embed(
                "👑 أمر ملكي!",
                f"الملك استخدم سلطته! كل الأصوات ستتجه ضد لاعب واحد اليوم!",
                0xffd700,
                None
            )
            await channel.send(embed=embed)

        self.stop()


class VoteView(View):
    def __init__(self, game, channel_id):
        super().__init__(timeout=VOTE_TIMEOUT)
        self.game = game
        self.channel_id = channel_id

        options = []
        for mid, p in game.players.items():
            if p.alive:
                weight = " (صوتان)" if p.role_name == "mayor" else ""
                options.append(discord.SelectOption(
                    label=f"{p.display_name[:20]}{weight}",
                    value=str(mid),
                    description="صوتك ضده",
                    emoji="🗳️"
                ))

        if options:
            select = Select(
                placeholder="🗳️ اختر من تطرد..",
                options=options[:25],
                custom_id=f"vote_{channel_id}"
            )
            select.callback = self.select_callback
            self.add_item(select)

    async def select_callback(self, interaction):
        game = active_games.get(self.channel_id)
        if not game or game.phase != "voting":
            await interaction.response.send_message("⚠️ التصويت انتهى!", ephemeral=True)
            return

        if interaction.user.id in game.voted_players:
            await interaction.response.send_message("⚠️ لقد صوت بالفعل!", ephemeral=True)
            return

        target_id = int(interaction.data["values"][0])
        game.votes[interaction.user.id] = target_id
        game.voted_players.add(interaction.user.id)

        voter = game.players.get(interaction.user.id)
        target = game.players.get(target_id)
        weight_str = " (صوتان)" if voter and voter.role_name == "mayor" else ""

        await interaction.response.send_message(
            f"✅ تم تسجيل صوتك{weight_str} ضد **{target.display_name if target else 'مجهول'}**!",
            ephemeral=True
        )
        self.stop()


if __name__ == "__main__":
    t = Thread(target=keep_alive)
    t.daemon = True
    t.start()

    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not set!")
        exit(1)

    bot.run(DISCORD_TOKEN)
