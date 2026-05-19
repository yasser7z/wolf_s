import asyncio
import logging
import os
import random
import threading
from typing import Dict, Optional, List

import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask

from config import (
    DISCUSS_DURATION, LOBBY_COUNTDOWN, MAX_PLAYERS, MIN_PLAYERS,
    NIGHT_DURATION, ROLE_INFO, VOTE_DURATION,
)
from game_engine import GameEngine, GameState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("werewolf")

# ─── Web Server ───────────────────────────────────────────────────────────────

app = Flask(__name__)

@app.route("/")
@app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def start_web():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()
    log.info("Web server started")

# ─── Bot Setup ────────────────────────────────────────────────────────────────

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Game Manager ─────────────────────────────────────────────────────────────

class GameSession:
    def __init__(self, channel: discord.TextChannel, guild: discord.Guild):
        self.channel = channel
        self.guild = guild
        self.engine = GameEngine()
        self.lobby_message: Optional[discord.Message] = None
        self.phase_task: Optional[asyncio.Task] = None
        self.current_view: Optional[discord.ui.View] = None
        self.lock = asyncio.Lock()
        self._original_perms = None

games: Dict[int, GameSession] = {}

def get_game(channel_id: int) -> Optional[GameSession]:
    return games.get(channel_id)

# ─── Helper ───────────────────────────────────────────────────────────────────

def player_options(players: list) -> List[discord.SelectOption]:
    return [discord.SelectOption(label=p.name[:80], value=str(p.id), emoji="👤") for p in players]

def safe_name(pid: int, engine: GameEngine) -> str:
    p = engine.get_player(pid)
    return p.name if p else "غير معروف"

# ─── Lobby View ───────────────────────────────────────────────────────────────

class LobbyView(discord.ui.View):
    def __init__(self, session: GameSession):
        super().__init__(timeout=LOBBY_COUNTDOWN + 15)
        self.session = session

    @discord.ui.button(label="دخول", emoji="📥", style=discord.ButtonStyle.success, custom_id="lobby_join")
    async def join_btn(self, interaction: discord.Interaction, btn: discord.ui.Button):
        if self.session.engine.state != GameState.LOBBY:
            return await interaction.response.send_message("❌ اللوبي انتهى!", ephemeral=True)
        ok = self.session.engine.add_player(interaction.user.id, interaction.user.display_name)
        if not ok:
            return await interaction.response.send_message("❌ أنت موجود بالفعل!", ephemeral=True)
        await interaction.response.send_message("✅ انضممت!", ephemeral=True)
        await self._refresh()

    @discord.ui.button(label="خروج", emoji="📤", style=discord.ButtonStyle.danger, custom_id="lobby_leave")
    async def leave_btn(self, interaction: discord.Interaction, btn: discord.ui.Button):
        ok = self.session.engine.remove_player(interaction.user.id)
        if not ok:
            return await interaction.response.send_message("❌ لست في اللعبة!", ephemeral=True)
        await interaction.response.send_message("✅ غادرت!", ephemeral=True)
        await self._refresh()

    @discord.ui.button(label="طريقة اللعب", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="lobby_rules")
    async def rules_btn(self, interaction: discord.Interaction, btn: discord.ui.Button):
        embed = discord.Embed(
            title="📜 طريقة اللعب والأدوار",
            description="**لعبة الذئب (Werewolf)** - لعبة اجتماعية تعتمد على التخمين والتحليل.",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎯 الهدف", value="**القرويون:** اكشفوا واطردوا كل الذيابة.\n**الذيابة 🐺:** اغتالوا القرويين حتى يصبح عددكم ≥ عددهم.", inline=False)
        for rkey, rinfo in ROLE_INFO.items():
            embed.add_field(name=f"{rinfo['emoji']} {rinfo['name']} ({rinfo['team']})", value=f"{rinfo['desc']}\n✦ قدرة: {rinfo['ability']}", inline=False)
        embed.set_footer(text="تحفظ كل الحقوق لي Vale Community")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _refresh(self):
        if not self.session.lobby_message:
            return
        try:
            embed = build_lobby_embed(self.session, LOBBY_COUNTDOWN)
            await self.session.lobby_message.edit(embed=embed, view=self)
        except discord.NotFound:
            pass

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.session.lobby_message:
            try:
                await self.session.lobby_message.edit(view=self)
            except discord.NotFound:
                pass
        self.stop()

def build_lobby_embed(session: GameSession, remaining: int = LOBBY_COUNTDOWN) -> discord.Embed:
    eng = session.engine
    embed = discord.Embed(title="🐺 لعبة الذئب - اللوبي", description="اضغط **دخول** للانضمام و**خروج** للمغادرة.", color=discord.Color.gold())
    players_list = "\n".join(f"{i+1}. 👤 {p.name}" for i, (_, p) in enumerate(eng.players.items())) or "لا يوجد لاعبين بعد..."
    embed.add_field(name=f"👥 اللاعبين ({eng.player_count()})", value=players_list, inline=False)
    if eng.player_count() < MIN_PLAYERS:
        status = f"⚠️ مطلوب {MIN_PLAYERS} لاعبين على الأقل ({eng.player_count()}/{MIN_PLAYERS})"
        embed.color = discord.Color.red()
    else:
        status = f"✅ العدد كافي - تبدأ اللعبة بعد {remaining} ثانية"
        embed.color = discord.Color.green()
    embed.add_field(name="الحالة", value=status, inline=False)
    return embed

# ─── Night Action View ────────────────────────────────────────────────────────

class NightActView(discord.ui.View):
    """Role-specific action buttons. Each role gets its own button; the correct
       player sees their role embed + target selection in one ephemeral message."""

    def __init__(self, session: GameSession):
        super().__init__(timeout=NIGHT_DURATION + 5)
        self.session = session
        self._add_role_buttons()

    def _add_role_buttons(self):
        eng = self.session.engine
        roles_present = {p.role for p in eng.players.values() if p.alive}

        row0 = [
            ("wolf", "صيد", discord.ButtonStyle.danger, "🐺"),
            ("detective", "تحقق", discord.ButtonStyle.primary, "🔍"),
            ("doctor", "عالج", discord.ButtonStyle.success, "⚕️"),
        ]
        row1 = [
            ("guardian", "احم", discord.ButtonStyle.success, "🛡️"),
            ("seductress", "اغوي", discord.ButtonStyle.secondary, "💃"),
        ]

        for items, row in [(row0, 0), (row1, 1)]:
            for role_name, label, style, emoji in items:
                if role_name in roles_present:
                    btn = discord.ui.Button(label=label, emoji=emoji, style=style, row=row)
                    btn.callback = self._make_role_cb(role_name)
                    self.add_item(btn)

        btn = discord.ui.Button(label="دوري", emoji="🎭", style=discord.ButtonStyle.secondary, row=2)
        btn.callback = self._myrole_cb
        self.add_item(btn)

    def _make_role_cb(self, role_name):
        async def cb(interaction: discord.Interaction):
            eng = self.session.engine
            pid = interaction.user.id
            p = eng.get_player(pid)
            if not p or not p.alive:
                return await interaction.response.send_message("❌ أنت ميت!", ephemeral=True)
            if p.role != role_name:
                return await interaction.response.send_message(f"❌ هذا الزر للـ {ROLE_INFO[role_name]['emoji']} {ROLE_INFO[role_name]['name']}!", ephemeral=True)
            if pid in eng.night_actions_done:
                return await interaction.response.send_message("✅ أديت واجبك هذه الليلة!", ephemeral=True)

            if role_name == "detective" and p.detective_used:
                return await interaction.response.send_message("🔍 استخدمت قدرتك من قبل!", ephemeral=True)
            if role_name == "guardian" and p.guardian_used:
                return await interaction.response.send_message("🛡️ استخدمت قدرتك من قبل!", ephemeral=True)

            r = ROLE_INFO[role_name]
            e = discord.Embed(title=f"{r['emoji']} دورك: {r['name']}", description=r['desc'], color=discord.Color.purple())
            e.add_field(name="✦ قدرتك", value=r['ability'], inline=False)
            e.add_field(name="🏠 الفريق", value="🐺 الذياب" if role_name == "wolf" else "🧑‍🌾 القرويين")
            if role_name == "wolf":
                fellow = [safe_name(w, eng) for w in eng.living_wolves if w != pid]
                if fellow:
                    e.add_field(name="🐺 رفاقك", value=", ".join(fellow), inline=False)
            if r.get("image_url"):
                e.set_image(url=r["image_url"])

            living = [eng.players[i] for i in eng.living_ids if i != pid]
            all_living = [eng.players[i] for i in eng.living_ids]
            v = discord.ui.View(timeout=NIGHT_DURATION)

            if role_name == "wolf":
                if not living:
                    return await interaction.response.send_message(embed=e, ephemeral=True)
                sel = discord.ui.Select(placeholder="🐺 اختر ضحيتك", options=player_options(living), min_values=1, max_values=1)
                async def wolf_sel(inter):
                    eng.set_wolf_vote(pid, int(sel.values[0]))
                    await inter.response.send_message("🐺 ✅ تم!", ephemeral=True); sel.disabled = True
                    await inter.edit_original_response(view=v); await check_night_done(self.session)
                sel.callback = wolf_sel

            elif role_name == "doctor":
                sel = discord.ui.Select(placeholder="⚕️ اختر من تعالجه", options=player_options(all_living), min_values=1, max_values=1)
                async def doc_sel(inter):
                    eng.set_doctor_target(pid, int(sel.values[0]))
                    await inter.response.send_message("⚕️ ✅ تم!", ephemeral=True); sel.disabled = True
                    await inter.edit_original_response(view=v); await check_night_done(self.session)
                sel.callback = doc_sel

            elif role_name == "seductress":
                if not living:
                    return await interaction.response.send_message(embed=e, ephemeral=True)
                sel = discord.ui.Select(placeholder="💃 اختري هدفك", options=player_options(living), min_values=1, max_values=1)
                async def sed_sel(inter):
                    eng.set_seductress_target(pid, int(sel.values[0]))
                    await inter.response.send_message("💃 ✅ تم!", ephemeral=True); sel.disabled = True
                    await inter.edit_original_response(view=v); await check_night_done(self.session)
                sel.callback = sed_sel

            elif role_name == "detective":
                if not living:
                    return await interaction.response.send_message(embed=e, ephemeral=True)
                sel = discord.ui.Select(placeholder="🔍 اختر من تحقق منه", options=player_options(living), min_values=1, max_values=1)
                async def det_sel(inter):
                    eng.set_detective_target(pid, int(sel.values[0]))
                    await inter.response.send_message("🔍 ✅ تم!", ephemeral=True); sel.disabled = True
                    await inter.edit_original_response(view=v); await check_night_done(self.session)
                sel.callback = det_sel

            elif role_name == "guardian":
                if not living:
                    return await interaction.response.send_message(embed=e, ephemeral=True)
                sel = discord.ui.Select(placeholder="🛡️ اختر من تحميه", options=player_options(living), min_values=1, max_values=1)
                async def gua_sel(inter):
                    eng.set_guardian_target(pid, int(sel.values[0]))
                    await inter.response.send_message("🛡️ ✅ تم!", ephemeral=True); sel.disabled = True
                    await inter.edit_original_response(view=v); await check_night_done(self.session)
                sel.callback = gua_sel

            else:
                return await interaction.response.send_message(embed=e, ephemeral=True)

            v.add_item(sel)
            await interaction.response.send_message(embed=e, view=v, ephemeral=True)
        return cb

    async def _myrole_cb(self, interaction: discord.Interaction):
        eng = self.session.engine
        pid = interaction.user.id
        p = eng.get_player(pid)
        if not p:
            return await interaction.response.send_message("❌ لست في اللعبة!", ephemeral=True)
        r = ROLE_INFO[p.role]
        e = discord.Embed(title=f"{r['emoji']} دورك: {r['name']}", description=r['desc'], color=discord.Color.purple())
        e.add_field(name="✦ قدرتك", value=r['ability'], inline=False)
        e.add_field(name="🏠 الفريق", value="🐺 الذياب" if p.role == "wolf" else "🧑‍🌾 القرويين")
        if p.role == "wolf":
            fellow = [safe_name(w, eng) for w in eng.living_wolves if w != pid]
            if fellow:
                e.add_field(name="🐺 رفاقك", value=", ".join(fellow), inline=False)
        if r.get("image_url"):
            e.set_image(url=r["image_url"])
        await interaction.response.send_message(embed=e, ephemeral=True)

    async def on_timeout(self):
        self.stop()

# ─── Vote View ────────────────────────────────────────────────────────────────

class VoteView(discord.ui.View):
    def __init__(self, session: GameSession):
        super().__init__(timeout=VOTE_DURATION + 5)
        self.session = session
        self._voted = set()

    @discord.ui.button(label="صوت الآن", emoji="🗳️", style=discord.ButtonStyle.success, custom_id="vote_btn")
    async def vote_btn(self, interaction: discord.Interaction, btn: discord.ui.Button):
        eng = self.session.engine
        pid = interaction.user.id
        p = eng.get_player(pid)
        if not p or not p.alive:
            return await interaction.response.send_message("❌ لا يمكنك التصويت!", ephemeral=True)
        if pid in self._voted:
            return await interaction.response.send_message("❌ لقد صوت بالفعل!", ephemeral=True)
        if eng.state not in (GameState.DAY, GameState.VOTING):
            return await interaction.response.send_message("❌ ليس وقت التصويت!", ephemeral=True)

        targets = [eng.players[i] for i in eng.living_ids if i != pid]
        if not targets:
            return await interaction.response.send_message("❌ لا يوجد أحد للتصويت عليه!", ephemeral=True)

        main_view = discord.ui.View(timeout=VOTE_DURATION)
        select = discord.ui.Select(placeholder="🗳️ اختر من تصوت له", options=player_options(targets), min_values=1, max_values=1)
        async def vote_cb(inter: discord.Interaction):
            tid = int(select.values[0])
            eng.set_vote(pid, tid)
            self._voted.add(pid)
            w = 2 if p.role == "mayor" else 1
            await inter.response.send_message(f"🗳️ ✅ صوتك ({w}) سُجل!", ephemeral=True)
            select.disabled = True
            await inter.edit_original_response(view=main_view)
        select.callback = vote_cb
        main_view.add_item(select)

        if p.role == "king" and not p.king_used:
            king_btn = discord.ui.Button(label="👑 سلطة الملك", style=discord.ButtonStyle.danger)
            async def king_cb(inter: discord.Interaction):
                if p.king_used:
                    return await inter.response.send_message("❌ استخدمتها من قبل!", ephemeral=True)
                kt = [eng.players[i] for i in eng.living_ids if i != pid]
                if not kt:
                    return await inter.response.send_message("❌ لا يوجد هدف!", ephemeral=True)
                kv = discord.ui.View(timeout=30)
                ks = discord.ui.Select(placeholder="👑 اختر من تطرده", options=player_options(kt), min_values=1, max_values=1)
                async def kscb(kinter: discord.Interaction):
                    tid = int(ks.values[0])
                    eng.set_king_flip(pid, tid)
                    await kinter.response.send_message(f"👑 ✅ قلبت الأصوات على {eng.players[tid].name}!", ephemeral=True)
                    ks.disabled = True
                    await kinter.edit_original_response(view=kv)
                ks.callback = kscb
                kv.add_item(ks)
                await inter.response.send_message("👑 استخدم سلطتك:", view=kv, ephemeral=True)
            king_btn.callback = king_cb
            main_view.add_item(king_btn)

        await interaction.response.send_message("🗳️ اختر من تصوت له:", view=main_view, ephemeral=True)

    async def on_timeout(self):
        self.stop()

# ─── Game Flow ────────────────────────────────────────────────────────────────

async def check_night_done(session: GameSession):
    async with session.lock:
        eng = session.engine
        if eng.state == GameState.NIGHT and eng.all_night_actions_done():
            if session.current_view:
                session.current_view.stop()
            await resolve_night_phase(session)

async def lobby_countdown(session: GameSession):
    try:
        for remaining in range(LOBBY_COUNTDOWN, 0, -10):
            await asyncio.sleep(min(10, remaining))
            async with session.lock:
                if session.engine.state != GameState.LOBBY:
                    return
                if session.lobby_message:
                    try:
                        embed = build_lobby_embed(session, remaining)
                        await session.lobby_message.edit(embed=embed, view=session.current_view)
                    except discord.NotFound:
                        return

        async with session.lock:
            if session.engine.state != GameState.LOBBY:
                return
            if session.engine.player_count() < MIN_PLAYERS:
                embed = discord.Embed(title="❌ لم تبدأ اللعبة", description=f"ما فيه عدد كافٍ. اللاعبين: {session.engine.player_count()}/{MIN_PLAYERS}", color=discord.Color.red())
                if session.lobby_message:
                    try:
                        await session.lobby_message.edit(embed=embed, view=None)
                    except discord.NotFound:
                        pass
                games.pop(session.channel.id, None)
                return
            await start_game(session)
    except asyncio.CancelledError:
        pass

async def start_game(session: GameSession):
    eng = session.engine
    eng.assign_roles()
    eng.state = GameState.NIGHT
    eng.day_number = 1

    embed = discord.Embed(
        title="🐺 بدأت اللعبة!",
        description="تم توزيع الأدوار. لكل ذي قدرة، استخدم أزرار الليل بالأسفل.\n🧑‍🌾 القرويون: ناقشوا و حللوا في النهار.",
        color=discord.Color.green()
    )
    players_str = "\n".join(f"👤 {p.name}" for p in eng.players.values())
    embed.add_field(name="👥 اللاعبين", value=players_str, inline=False)
    embed.set_footer(text="تحفظ كل الحقوق لي Vale Community")
    if session.lobby_message:
        try:
            await session.lobby_message.edit(embed=embed, view=None)
        except discord.NotFound:
            pass

    await lock_channel(session)
    await run_night_phase(session)

async def lock_channel(session: GameSession):
    try:
        everyone = session.guild.default_role
        overwrite = session.channel.overwrites_for(everyone)
        session._original_perms = overwrite.send_messages
        await session.channel.set_permissions(everyone, send_messages=False)
    except Exception as e:
        log.warning(f"lock error: {e}")

async def unlock_channel(session: GameSession):
    try:
        everyone = session.guild.default_role
        await session.channel.set_permissions(everyone, send_messages=session._original_perms)
    except Exception as e:
        log.warning(f"unlock error: {e}")

async def run_night_phase(session: GameSession):
    eng = session.engine
    async with session.lock:
        eng.state = GameState.NIGHT
        eng.night_actions_done.clear()

        embed = discord.Embed(title=f"🌙 الليل {eng.day_number}", description="الجميع ناموا... الذين لديهم قدرات يتحركون في الظل.", color=discord.Color.from_rgb(10, 10, 40))
        embed.set_footer(text=f"🐺 {len(eng.living_wolves)} ذيب | 👥 {len(eng.living_ids)} أحياء — تحفظ كل الحقوق لي Vale Community")

        view = NightActView(session)
        session.current_view = view
        await session.channel.send(embed=embed, view=view)

    await asyncio.sleep(NIGHT_DURATION)

    async with session.lock:
        if eng.state != GameState.NIGHT:
            return
        if session.current_view:
            session.current_view.stop()
        await resolve_night_phase(session)

async def resolve_night_phase(session: GameSession):
    eng = session.engine
    if eng.state != GameState.NIGHT:
        return

    result = eng.resolve_night()
    eng.state = GameState.DAY

    if session.current_view:
        try:
            await session.lobby_message.edit(view=session.current_view)
        except Exception:
            pass

    await unlock_channel(session)

    morning_embed = discord.Embed(title=f"☀️ صباح اليوم {eng.day_number}", color=discord.Color.gold())
    if result.killed:
        killed_names = ", ".join(safe_name(t, eng) for t in result.killed)
        morning_embed.add_field(name="💀 القتلى", value=killed_names, inline=False)
    else:
        morning_embed.add_field(name="🌅", value="لا يوجد قتلى!", inline=False)

    if result.message:
        morning_embed.add_field(name="📋 أحداث الليلة", value=result.message, inline=False)
    if result.exposed_wolf:
        morning_embed.add_field(name="👵 أم فادي تكشف!", value=f"{safe_name(result.exposed_wolf, eng)} 🐺 ذيب!", inline=False)

    morning_embed.add_field(name="👥 المتبقون", value=f"{len(eng.living_ids)} لاعب", inline=False)
    morning_embed.set_footer(text="تحفظ كل الحقوق لي Vale Community")
    await session.channel.send(embed=morning_embed)

    if result.detective_result:
        det_id, tgt_id, is_wolf = result.detective_result
        d_embed = discord.Embed(title="🔍 نتيجة التحقيق", description=f"{safe_name(tgt_id, eng)} هو **{'🐺 ذيب' if is_wolf else '🧑‍🌾 قروي'}**", color=discord.Color.blue())
        member = session.guild.get_member(det_id)
        if member:
            try:
                await session.channel.send(f"{member.mention}", embed=d_embed, delete_after=15)
            except Exception:
                pass

    winner = eng.check_win()
    if winner:
        await end_game(session, winner)
        return

    discuss = discord.Embed(title="🗣️ وقت النقاش", description=f"ناقشوا {DISCUSS_DURATION} ثانية ثم التصويت.", color=discord.Color.orange())
    await session.channel.send(embed=discuss)
    await asyncio.sleep(DISCUSS_DURATION)

    async with session.lock:
        if eng.state == GameState.GAME_OVER:
            return
        await run_voting_phase(session)

async def run_voting_phase(session: GameSession):
    eng = session.engine
    eng.state = GameState.VOTING

    embed = discord.Embed(title="🗳️ التصويت مفتوح!", description="العمدة صوته بـ 2. للملك سلطة قلب الأصوات.", color=discord.Color.blurple())
    for pid in eng.living_ids:
        p = eng.players[pid]
        extra = "🏛️ (×2)" if p.role == "mayor" else ""
        extra += " 👑" if (p.role == "king" and not p.king_used) else ""
        embed.add_field(name=f"👤 {p.name}", value=extra or "—", inline=True)
    embed.set_footer(text=f"{len(eng.living_ids)} يصوتون | {VOTE_DURATION} ثانية — تحفظ كل الحقوق لي Vale Community")

    view = VoteView(session)
    session.current_view = view
    await session.channel.send(embed=embed, view=view)
    await asyncio.sleep(VOTE_DURATION)

    async with session.lock:
        if eng.state == GameState.GAME_OVER:
            return
        view.stop()
        await resolve_vote_phase(session)

async def resolve_vote_phase(session: GameSession):
    eng = session.engine
    if eng.state == GameState.GAME_OVER:
        return

    result = eng.resolve_voting()

    r_embed = discord.Embed(title="📊 نتيجة التصويت", color=discord.Color.dark_red())
    if result.vote_counts:
        votes_str = "\n".join(f"{safe_name(t, eng)}: {c} صوت" for t, c in sorted(result.vote_counts.items(), key=lambda x: -x[1]))
        r_embed.add_field(name="🗳️ الأصوات", value=votes_str, inline=False)
    r_embed.add_field(name="🚨 النتيجة", value=result.message, inline=False)
    await session.channel.send(embed=r_embed)

    winner = eng.check_win()
    if winner:
        await end_game(session, winner)
        return

    eng.day_number += 1
    eng.reset_night_state()
    await asyncio.sleep(5)
    await lock_channel(session)
    await run_night_phase(session)

async def end_game(session: GameSession, winner: str):
    eng = session.engine
    eng.state = GameState.GAME_OVER
    await unlock_channel(session)

    title = "🐺 انتصار الذيابة! 🐺" if winner == "wolf" else "🎉 انتصار القرويين! 🎉"
    embed = discord.Embed(title=title, color=discord.Color.red() if winner == "wolf" else discord.Color.green())
    roles_str = "\n".join(
        f"{'✅' if p.alive else '💀'} {p.name}: {ROLE_INFO.get(p.role, {}).get('emoji', '❓')} {ROLE_INFO.get(p.role, {}).get('name', p.role)}"
        for p in eng.players.values()
    )
    embed.add_field(name="📋 الأدوار النهائية", value=roles_str, inline=False)
    embed.add_field(name="👥 المتبقون", value=f"{len(eng.living_ids)} لاعب", inline=False)
    embed.set_footer(text="تحفظ كل الحقوق لي Vale Community")
    await session.channel.send(embed=embed)
    games.pop(session.channel.id, None)

# ─── Commands ─────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info(f"Bot logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} commands")
    except Exception as e:
        log.warning(f"Sync failed: {e}")

@bot.tree.command(name="start_wolf_game", description="🐺 ابدأ لعبة الذئب")
async def start_wolf_game(interaction: discord.Interaction):
    if not interaction.guild:
        return await interaction.response.send_message("❌ استخدم الأمر في سيرفر!", ephemeral=True)
    ch_id = interaction.channel_id
    if ch_id in games:
        return await interaction.response.send_message("❌ فيه لعبة شغالة بهالقناة!", ephemeral=True)

    session = GameSession(interaction.channel, interaction.guild)
    games[ch_id] = session
    embed = build_lobby_embed(session, LOBBY_COUNTDOWN)
    view = LobbyView(session)
    session.current_view = view
    await interaction.response.send_message(embed=embed, view=view)
    session.lobby_message = await interaction.original_response()
    session.phase_task = asyncio.create_task(lobby_countdown(session))

@bot.tree.command(name="end_wolf_game", description="✋ إنهاء اللعبة")
async def end_wolf_game(interaction: discord.Interaction):
    ch_id = interaction.channel_id
    session = games.get(ch_id)
    if not session:
        return await interaction.response.send_message("❌ ما فيه لعبة!", ephemeral=True)

    if session.phase_task:
        session.phase_task.cancel()
    session.engine.state = GameState.GAME_OVER
    await unlock_channel(session)
    games.pop(ch_id, None)
    await interaction.response.send_message("✅ تم إنهاء اللعبة!")

@bot.tree.command(name="wolf_status", description="📊 حالة اللعبة")
async def wolf_status(interaction: discord.Interaction):
    ch_id = interaction.channel_id
    session = games.get(ch_id)
    if not session:
        return await interaction.response.send_message("❌ ما فيه لعبة!", ephemeral=True)

    eng = session.engine
    embed = discord.Embed(title="📊 حالة اللعبة", color=discord.Color.blue())
    embed.add_field(name="🔄 الحالة", value=eng.state.value, inline=True)
    embed.add_field(name="📅 اليوم", value=eng.day_number, inline=True)
    embed.add_field(name="👥 الأحياء", value=len(eng.living_ids), inline=True)
    alive = "\n".join(f"👤 {eng.players[pid].name}" for pid in eng.living_ids) or "—"
    dead = "\n".join(f"💀 {eng.players[pid].name}" for pid in eng.dead_ids) or "—"
    embed.add_field(name="✅ أحياء", value=alive, inline=True)
    embed.add_field(name="💀 موتى", value=dead, inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="developer", description="ℹ️ معلومات المطور")
async def developer(interaction: discord.Interaction):
    embed = discord.Embed(
        title="ℹ️ معلومات المطور",
        description="تم تطوير هذا البوت بواسطة:",
        color=discord.Color.gold()
    )
    embed.add_field(name="👤 ديسكورد", value="**Laaw.q**", inline=False)
    embed.add_field(name="📸 إنستغرام", value="**i7_tp2**", inline=False)
    embed.set_footer(text="تحفظ كل الحقوق لي Vale Community")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    start_web()
    bot.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
