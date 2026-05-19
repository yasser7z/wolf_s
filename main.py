"""
main.py — Werewolf Bot v3.0
============================
Entry point.  Starts a Flask web server (for Render health-check)
and then runs the discord.py bot with prefix commands (-ذئب / -ايقاف).

Architecture overview:
  • Prefix commands → spawn a GameSession per channel
  • GameSession owns a GameEngine (pure logic) + async lock
  • Phase transitions are driven by asyncio tasks + View timeouts
  • All role interactions are ephemeral; no DMs are ever sent
"""

import asyncio
import logging
import os
import random
import threading
from typing import Dict, List, Optional

import discord
from discord.ext import commands
from flask import Flask

from config import (
    BOT_PREFIX, DEV_DISCORD, DEV_INSTAGRAM, DISCUSS_DURATION,
    FOOTER_TEXT, LOBBY_COUNTDOWN, MAX_PLAYERS, MIN_PLAYERS,
    NIGHT_DURATION, PHASE_IMAGES, ROLE_INFO, TOKEN, VOTE_DURATION,
    build_rules_embed, random_death_roast, random_night_comment,
    random_village_win, random_vote_comment, random_wolf_win,
)
from game_engine import GameEngine, GameState

# ═══════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("werewolf")

# ═══════════════════════════════════════════════════════════════
# WEB SERVER  — Render health-check keeps the dyno alive
# ═══════════════════════════════════════════════════════════════

_flask = Flask(__name__)

@_flask.route("/")
@_flask.route("/health")
def _health():
    return "OK", 200


def _run_web():
    port = int(os.environ.get("PORT", 8080))
    _flask.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def start_web():
    t = threading.Thread(target=_run_web, daemon=True)
    t.start()
    log.info("Web server thread started")

# ═══════════════════════════════════════════════════════════════
# DISCORD BOT SETUP
# ═══════════════════════════════════════════════════════════════

if not TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents, help_command=None)

# ═══════════════════════════════════════════════════════════════
# GAME SESSION MANAGER
# ═══════════════════════════════════════════════════════════════

class GameSession:
    """Wraps a GameEngine with discord-specific runtime state."""

    def __init__(self, channel: discord.TextChannel, guild: discord.Guild):
        self.channel          = channel
        self.guild            = guild
        self.engine           = GameEngine()
        self.lobby_message:   Optional[discord.Message] = None
        self.phase_task:      Optional[asyncio.Task] = None
        self.current_view:    Optional[discord.ui.View] = None
        self.lock             = asyncio.Lock()
        self._original_perms  = None  # saved @everyone send_messages state

# Global registry: channel_id → GameSession
games: Dict[int, GameSession] = {}

# ═══════════════════════════════════════════════════════════════
# SHARED HELPERS
# ═══════════════════════════════════════════════════════════════

def player_options(players: list) -> List[discord.SelectOption]:
    """Build a list of SelectOption from a list of PlayerData objects."""
    return [
        discord.SelectOption(label=p.name[:80], value=str(p.id), emoji="👤")
        for p in players
    ]


def safe_name(pid: int, eng: GameEngine) -> str:
    p = eng.get_player(pid)
    return p.name if p else "غير معروف"


def build_role_embed(
    role_name: str,
    player_name: str = None,
    eng: GameEngine = None,
    pid: int = None,
) -> discord.Embed:
    """Create a rich embed that shows a player their role, faction, and image."""
    r = ROLE_INFO[role_name]
    title = f"{r['emoji']} دورك: {r['name']}"
    if player_name:
        title = f"{r['emoji']} {player_name} ← {r['name']}"

    e = discord.Embed(title=title, description=r['desc'], color=discord.Color.purple())
    e.add_field(name="✦ قدرتك", value=r['ability'], inline=False)
    e.add_field(
        name="🏠 الفريق",
        value="🐺 الذياب" if role_name == "wolf" else "🧑‍🌾 القرويين",
    )

    if role_name == "wolf" and eng and pid:
        fellow = [safe_name(w, eng) for w in eng.living_wolves if w != pid]
        if fellow:
            e.add_field(name="🐺 رفاقك الذيابة", value=", ".join(fellow), inline=False)

    if r.get("image_url"):
        e.set_image(url=r["image_url"])

    return e


def build_dev_embed() -> discord.Embed:
    """Developer credit embed (used by the 🛠️ button)."""
    e = discord.Embed(title="🛠️ معلومات المطور", color=discord.Color.gold())
    e.add_field(name="👤 ديسكورد", value=f"**{DEV_DISCORD}**", inline=False)
    e.add_field(name="📸 إنستغرام", value=f"**{DEV_INSTAGRAM}**", inline=False)
    e.set_footer(text=FOOTER_TEXT)
    return e

# ═══════════════════════════════════════════════════════════════
# LOBBY VIEW   (Join / Leave / Rules / Developer)
# ═══════════════════════════════════════════════════════════════

class LobbyView(discord.ui.View):
    """Four buttons: join, leave, game rules, developer info."""

    def __init__(self, session: GameSession):
        super().__init__(timeout=LOBBY_COUNTDOWN + 15)
        self.session = session

    # ── Row 0: Join / Leave ──────────────────────────────────────────────

    @discord.ui.button(label="انضمام", emoji="➕", style=discord.ButtonStyle.success, row=0)
    async def join_btn(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        if self.session.engine.state != GameState.LOBBY:
            return await interaction.response.send_message("❌ اللوبي انتهى!", ephemeral=True)
        ok = self.session.engine.add_player(interaction.user.id, interaction.user.display_name)
        if not ok:
            return await interaction.response.send_message("❌ أنت موجود بالفعل!", ephemeral=True)
        await interaction.response.send_message("✅ انضممت للعبة!", ephemeral=True)
        await self._refresh()

    @discord.ui.button(label="مغادرة", emoji="❌", style=discord.ButtonStyle.danger, row=0)
    async def leave_btn(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        ok = self.session.engine.remove_player(interaction.user.id)
        if not ok:
            return await interaction.response.send_message("❌ لست في اللعبة!", ephemeral=True)
        await interaction.response.send_message("✅ غادرت اللعبة!", ephemeral=True)
        await self._refresh()

    # ── Row 1: Rules / Developer ─────────────────────────────────────────

    @discord.ui.button(label="شرح اللعبة", emoji="📖", style=discord.ButtonStyle.secondary, row=1)
    async def rules_btn(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        embed = build_rules_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="مطور البوت", emoji="🛠️", style=discord.ButtonStyle.secondary, row=1)
    async def dev_btn(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        await interaction.response.send_message(embed=build_dev_embed(), ephemeral=True)

    # ── Internal ─────────────────────────────────────────────────────────

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
    """Render the lobby embed with player roster and countdown."""
    eng = session.engine
    embed = discord.Embed(
        title="🐺 لعبة الذئب — اللوبي",
        description="اضغط **➕ انضمام** للدخول أو **❌ مغادرة** للخروج.",
        color=discord.Color.gold(),
    )
    embed.set_image(url=PHASE_IMAGES["lobby"])

    roster = "\n".join(
        f"{i+1}. 👤 {p.name}"
        for i, (_, p) in enumerate(eng.players.items())
    ) or "⚠️ لا يوجد لاعبين بعد..."

    embed.add_field(name=f"👥 اللاعبين ({eng.player_count()}/{MAX_PLAYERS})", value=roster, inline=False)

    if eng.player_count() < MIN_PLAYERS:
        status = f"⏳ العدد: {eng.player_count()} / المطلوب: {MIN_PLAYERS}"
        embed.color = discord.Color.red()
    else:
        status = f"✅ العدد اكتمل! تبدأ اللعبة بعد {remaining} ثانية"
        embed.color = discord.Color.green()
    embed.add_field(name="📊 الحالة", value=status, inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    return embed

# ═══════════════════════════════════════════════════════════════
# NIGHT ACTION VIEW   (role-specific buttons + integrated select)
# ═══════════════════════════════════════════════════════════════

class NightActView(discord.ui.View):
    """
    Only players whose role has a night ability see a usable button.
    Clicking the button shows the role embed (with character image)
    and a select-menu to pick the target — all in one ephemeral message.
    """

    def __init__(self, session: GameSession):
        super().__init__(timeout=NIGHT_DURATION + 5)
        self.session = session
        self._build()

    def _build(self):
        eng = self.session.engine
        present = {p.role for p in eng.players.values() if p.alive}

        # Row 0 — primary roles
        for rname, lbl, style, emoji in [
            ("wolf",       "صيد",   discord.ButtonStyle.danger,  "🐺"),
            ("detective",  "تحقق",  discord.ButtonStyle.primary, "🔍"),
            ("doctor",     "عالج",  discord.ButtonStyle.success, "⚕️"),
        ]:
            if rname in present:
                btn = discord.ui.Button(label=lbl, emoji=emoji, style=style, row=0)
                btn.callback = self._role_cb(rname)
                self.add_item(btn)

        # Row 1 — secondary roles
        for rname, lbl, style, emoji in [
            ("guardian",   "احم",   discord.ButtonStyle.success,  "🛡️"),
            ("seductress", "اغوي",  discord.ButtonStyle.secondary,"💃"),
        ]:
            if rname in present:
                btn = discord.ui.Button(label=lbl, emoji=emoji, style=style, row=1)
                btn.callback = self._role_cb(rname)
                self.add_item(btn)

        # Row 2 — developer button
        dev = discord.ui.Button(label="مطور البوت", emoji="🛠️", style=discord.ButtonStyle.gray, row=2)
        dev.callback = self._dev_cb
        self.add_item(dev)

    # ── Role-press callback factory ───────────────────────────────────────

    def _role_cb(self, role_name: str):
        async def cb(interaction: discord.Interaction):
            eng = self.session.engine
            pid = interaction.user.id
            p  = eng.get_player(pid)

            # Guard: dead
            if not p or not p.alive:
                return await interaction.response.send_message("❌ أنت ميت!", ephemeral=True)
            # Guard: wrong role
            if p.role != role_name:
                r = ROLE_INFO[role_name]
                return await interaction.response.send_message(
                    f"❌ هذا الزر للـ {r['emoji']} {r['name']}!",
                    ephemeral=True,
                )
            # Guard: already acted this night
            if pid in eng.night_actions_done:
                return await interaction.response.send_message("✅ أديت واجبك الليلة!", ephemeral=True)
            # Guard: one-time ability already used
            if role_name == "detective" and p.detective_used:
                return await interaction.response.send_message("🔍 استخدمت قدرتك من قبل!", ephemeral=True)
            if role_name == "guardian" and p.guardian_used:
                return await interaction.response.send_message("🛡️ استخدمت قدرتك من قبل!", ephemeral=True)

            # Build role embed
            embed = build_role_embed(role_name, player_name=p.name, eng=eng, pid=pid)

            living    = [eng.players[i] for i in eng.living_ids if i != pid]
            all_living = [eng.players[i] for i in eng.living_ids]
            view      = discord.ui.View(timeout=NIGHT_DURATION)
            sel       = None

            # Build the appropriate select menu for this role

            if role_name == "wolf":
                if not living:
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                sel = discord.ui.Select(
                    placeholder="🐺 اختر ضحيتك",
                    options=player_options(living), min_values=1, max_values=1,
                )
                async def _wolf(inter):
                    eng.set_wolf_vote(pid, int(sel.values[0]))
                    await inter.response.send_message("🐺 ✅ تم!", ephemeral=True)
                    sel.disabled = True
                    await inter.edit_original_response(view=view)
                    await _check_night_done(self.session)
                sel.callback = _wolf

            elif role_name == "doctor":
                sel = discord.ui.Select(
                    placeholder="⚕️ اختر من تعالجه",
                    options=player_options(all_living), min_values=1, max_values=1,
                )
                async def _doc(inter):
                    eng.set_doctor_target(pid, int(sel.values[0]))
                    await inter.response.send_message("⚕️ ✅ تم!", ephemeral=True)
                    sel.disabled = True
                    await inter.edit_original_response(view=view)
                    await _check_night_done(self.session)
                sel.callback = _doc

            elif role_name == "seductress":
                if not living:
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                sel = discord.ui.Select(
                    placeholder="💃 اختري هدفك",
                    options=player_options(living), min_values=1, max_values=1,
                )
                async def _sed(inter):
                    eng.set_seductress_target(pid, int(sel.values[0]))
                    await inter.response.send_message("💃 ✅ تم!", ephemeral=True)
                    sel.disabled = True
                    await inter.edit_original_response(view=view)
                    await _check_night_done(self.session)
                sel.callback = _sed

            elif role_name == "detective":
                if not living:
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                sel = discord.ui.Select(
                    placeholder="🔍 اختر من تحقق منه",
                    options=player_options(living), min_values=1, max_values=1,
                )
                async def _det(inter):
                    eng.set_detective_target(pid, int(sel.values[0]))
                    await inter.response.send_message("🔍 ✅ تم!", ephemeral=True)
                    sel.disabled = True
                    await inter.edit_original_response(view=view)
                    await _check_night_done(self.session)
                sel.callback = _det

            elif role_name == "guardian":
                if not living:
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                sel = discord.ui.Select(
                    placeholder="🛡️ اختر من تحميه",
                    options=player_options(living), min_values=1, max_values=1,
                )
                async def _gua(inter):
                    eng.set_guardian_target(pid, int(sel.values[0]))
                    await inter.response.send_message("🛡️ ✅ تم!", ephemeral=True)
                    sel.disabled = True
                    await inter.edit_original_response(view=view)
                    await _check_night_done(self.session)
                sel.callback = _gua

            if sel is None:
                return await interaction.response.send_message(embed=embed, ephemeral=True)

            view.add_item(sel)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        return cb

    # ── Developer button callback ────────────────────────────────────────

    async def _dev_cb(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=build_dev_embed(), ephemeral=True)

    async def on_timeout(self):
        self.stop()

# ═══════════════════════════════════════════════════════════════
# VOTE VIEW   (one button + optional king power)
# ═══════════════════════════════════════════════════════════════

class VoteView(discord.ui.View):
    """
    One "🗳️ صوت الآن" button for all living players.
    First click → ephemeral select menu with living targets.
    King also sees a "👑 سلطة الملك" button to flip all votes.
    """

    def __init__(self, session: GameSession):
        super().__init__(timeout=VOTE_DURATION + 5)
        self.session = session
        self._voted: set = set()

    @discord.ui.button(label="صوت الآن", emoji="🗳️", style=discord.ButtonStyle.success)
    async def vote_btn(self, interaction: discord.Interaction, _btn: discord.ui.Button):
        eng = self.session.engine
        pid = interaction.user.id
        p   = eng.get_player(pid)

        if not p or not p.alive:
            return await interaction.response.send_message("❌ لا يمكنك التصويت!", ephemeral=True)
        if pid in self._voted:
            return await interaction.response.send_message("❌ صوتيت من قبل!", ephemeral=True)
        if eng.state not in (GameState.DAY, GameState.VOTING):
            return await interaction.response.send_message("❌ ليس وقت التصويت!", ephemeral=True)

        targets = [eng.players[i] for i in eng.living_ids if i != pid]
        if not targets:
            return await interaction.response.send_message("❌ ما فيه أحد للتصويت!", ephemeral=True)

        mv = discord.ui.View(timeout=VOTE_DURATION)
        sel = discord.ui.Select(
            placeholder="🗳️ اختر من تصوت له",
            options=player_options(targets), min_values=1, max_values=1,
        )

        async def vote_cb(inter: discord.Interaction):
            tid = int(sel.values[0])
            eng.set_vote(pid, tid)
            self._voted.add(pid)
            w = 2 if p.role == "mayor" else 1
            await inter.response.send_message(f"🗳️ ✅ صوتك ({w}) سُجل!", ephemeral=True)
            sel.disabled = True
            await inter.edit_original_response(view=mv)

        sel.callback = vote_cb
        mv.add_item(sel)

        # King power button
        if p.role == "king" and not p.king_used:
            king_btn = discord.ui.Button(label="👑 سلطة الملك", style=discord.ButtonStyle.danger)

            async def king_cb(inter: discord.Interaction):
                if p.king_used:
                    return await inter.response.send_message("❌ استخدمتها من قبل!", ephemeral=True)
                kt = [eng.players[i] for i in eng.living_ids if i != pid]
                if not kt:
                    return await inter.response.send_message("❌ لا يوجد هدف!", ephemeral=True)

                kv = discord.ui.View(timeout=30)
                ks = discord.ui.Select(
                    placeholder="👑 اختر من تطرده فوراً",
                    options=player_options(kt), min_values=1, max_values=1,
                )

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
            mv.add_item(king_btn)

        await interaction.response.send_message("🗳️ اختر من تصوت له:", view=mv, ephemeral=True)

    async def on_timeout(self):
        self.stop()

# ═══════════════════════════════════════════════════════════════
# GAME FLOW  (all async phase transitions)
# ═══════════════════════════════════════════════════════════════

async def _check_night_done(session: GameSession):
    """If all required night actions are in, resolve early."""
    async with session.lock:
        eng = session.engine
        if eng.state == GameState.NIGHT and eng.all_night_actions_done():
            if session.current_view:
                session.current_view.stop()
            await _resolve_night(session)


async def _lobby_loop(session: GameSession):
    """
    Background task that updates the lobby embed every 10 s.
    After LOBBY_COUNTDOWN seconds, starts the game (or cancels).
    """
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
                embed = discord.Embed(
                    title="❌ لم تبدأ اللعبة",
                    description=f"مافيه عدد كافي. اللاعبين: {session.engine.player_count()}/{MIN_PLAYERS}",
                    color=discord.Color.red(),
                )
                embed.set_footer(text=FOOTER_TEXT)
                if session.lobby_message:
                    try:
                        await session.lobby_message.edit(embed=embed, view=None)
                    except discord.NotFound:
                        pass
                games.pop(session.channel.id, None)
                return

            await _start_game(session)
    except asyncio.CancelledError:
        pass


async def _start_game(session: GameSession):
    """Assign roles, lock channel, and dive straight into night."""
    eng = session.engine
    eng.assign_roles()
    eng.state   = GameState.NIGHT
    eng.day_number = 1

    embed = discord.Embed(
        title="🐺 بدأت اللعبة!",
        description="تم توزيع الأدوار تلقائياً.\n"
                    "• لكل ذي قدرة: استخدم الأزرار أدناه.\n"
                    "• القرويون: انتظروا النهار للمناقشة والتصويت.",
        color=discord.Color.green(),
    )
    embed.set_image(url=PHASE_IMAGES["night"])
    embed.add_field(
        name="👥 اللاعبين",
        value="\n".join(f"👤 {p.name}" for p in eng.players.values()),
        inline=False,
    )
    embed.set_footer(text=FOOTER_TEXT)

    if session.lobby_message:
        try:
            await session.lobby_message.edit(embed=embed, view=None)
        except discord.NotFound:
            pass

    await _lock(session)
    await _night_phase(session)


async def _lock(session: GameSession):
    """Lock @everyone from sending messages in the game channel."""
    try:
        everyone = session.guild.default_role
        ow = session.channel.overwrites_for(everyone)
        session._original_perms = ow.send_messages
        await session.channel.set_permissions(everyone, send_messages=False)
    except Exception as e:
        log.warning(f"Lock channel failed: {e}")


async def _unlock(session: GameSession):
    """Restore the original send_messages permission."""
    try:
        everyone = session.guild.default_role
        await session.channel.set_permissions(everyone, send_messages=session._original_perms)
    except Exception as e:
        log.warning(f"Unlock channel failed: {e}")


async def _night_phase(session: GameSession):
    """Send the night banner and wait NIGHT_DURATION seconds."""
    eng = session.engine
    async with session.lock:
        eng.state = GameState.NIGHT
        eng.night_actions_done.clear()

        embed = discord.Embed(
            title=f"🌙 الليل {eng.day_number}",
            description="الجميع ناموا… الذين لديهم قدرات يتحركون في الظل.\n"
                        "اضغط زر قدرتك لاختيار هدفك.",
            color=discord.Color.from_rgb(10, 10, 40),
        )
        embed.set_image(url=PHASE_IMAGES["night"])
        embed.set_footer(
            text=f"🐺 {len(eng.living_wolves)} ذيب | 👥 {len(eng.living_ids)} أحياء — {FOOTER_TEXT}"
        )

        view = NightActView(session)
        session.current_view = view
        await session.channel.send(embed=embed, view=view)

    await asyncio.sleep(NIGHT_DURATION)

    async with session.lock:
        if eng.state != GameState.NIGHT:
            return
        if session.current_view:
            session.current_view.stop()
        await _resolve_night(session)


async def _resolve_night(session: GameSession):
    """
    Resolve night actions, announce results (with social commentary),
    deliver detective result, check win, then start discussion + vote.
    """
    eng = session.engine
    if eng.state != GameState.NIGHT:
        return

    result = eng.resolve_night()
    eng.state = GameState.DAY
    await _unlock(session)

    # ── Morning embed ────────────────────────────────────────────────

    morning = discord.Embed(
        title=f"☀️ صباح اليوم {eng.day_number}",
        color=discord.Color.gold(),
    )
    morning.set_image(url=PHASE_IMAGES["day"])

    if result.killed:
        killed_names = ", ".join(safe_name(t, eng) for t in result.killed)
        morning.add_field(name="💀 القتلى", value=killed_names, inline=False)
        for tid in result.killed:
            morning.add_field(
                name="😂 تعزية ساخرة",
                value=random_death_roast(safe_name(tid, eng)),
                inline=False,
            )
    else:
        morning.add_field(name="🌅 صباح الخير", value="لا يوجد قتلى! الجميع بأمان.", inline=False)
        morning.add_field(name="😂 تعليق", value=random_night_comment(killed=False), inline=False)

    if result.message:
        morning.add_field(name="📋 أحداث الليلة", value=result.message, inline=False)
    if result.exposed_wolf:
        morning.add_field(
            name="👵 أم فادي تكشف!",
            value=f"🎯 {safe_name(result.exposed_wolf, eng)} 🐺 ذيب مكشوف!",
            inline=False,
        )
    morning.add_field(name="👥 المتبقون", value=f"{len(eng.living_ids)} لاعب على قيد الحياة", inline=False)
    morning.set_footer(text=FOOTER_TEXT)
    await session.channel.send(embed=morning)

    # ── Detective result (ephemeral-ish — tag + delete_after) ─────────

    if result.detective_result:
        det_id, tgt_id, is_wolf = result.detective_result
        d_embed = discord.Embed(title="🔍 نتيجة التحقيق", color=discord.Color.blue())
        d_embed.add_field(
            name="النتيجة",
            value=f"{safe_name(tgt_id, eng)} هو **{'🐺 ذيب' if is_wolf else '🧑‍🌾 قروي'}**",
        )
        d_embed.set_footer(text=FOOTER_TEXT)
        member = session.guild.get_member(det_id)
        if member:
            try:
                await session.channel.send(
                    f"{member.mention}",
                    embed=d_embed,
                    delete_after=15,
                )
            except Exception:
                pass

    # ── Win check ────────────────────────────────────────────────────

    winner = eng.check_win()
    if winner:
        await _end_game(session, winner)
        return

    # ── Discussion period ────────────────────────────────────────────

    discuss = discord.Embed(
        title="🗣️ وقت النقاش",
        description=f"ناقشوا من تشكون فيه! التصويت يبدأ بعد {DISCUSS_DURATION} ثانية.",
        color=discord.Color.orange(),
    )
    discuss.set_footer(text=FOOTER_TEXT)
    await session.channel.send(embed=discuss)
    await asyncio.sleep(DISCUSS_DURATION)

    async with session.lock:
        if eng.state == GameState.GAME_OVER:
            return
        await _vote_phase(session)


async def _vote_phase(session: GameSession):
    """Open voting with a banner and the VoteView."""
    eng = session.engine
    eng.state = GameState.VOTING

    embed = discord.Embed(
        title="🗳️ التصويت مفتوح!",
        description="العمدة صوته بـ 2.\nالملك يستطيع قلب الأصوات كلها على لاعب واحد.",
        color=discord.Color.blurple(),
    )
    embed.set_image(url=PHASE_IMAGES["voting"])

    for pid in eng.living_ids:
        p = eng.players[pid]
        extra = "🏛️ (×2)" if p.role == "mayor" else ""
        extra += " 👑" if (p.role == "king" and not p.king_used) else ""
        embed.add_field(name=f"👤 {p.name}", value=extra or "—", inline=True)

    embed.add_field(name="😂 لحظة", value=random_vote_comment(), inline=False)
    embed.set_footer(text=f"{len(eng.living_ids)} يصوتون | {VOTE_DURATION} ثانية — {FOOTER_TEXT}")

    view = VoteView(session)
    session.current_view = view
    await session.channel.send(embed=embed, view=view)
    await asyncio.sleep(VOTE_DURATION)

    async with session.lock:
        if eng.state == GameState.GAME_OVER:
            return
        view.stop()
        await _resolve_vote(session)


async def _resolve_vote(session: GameSession):
    """Tally votes, announce result, check win, loop back to night."""
    eng = session.engine
    if eng.state == GameState.GAME_OVER:
        return

    result = eng.resolve_voting()

    r_embed = discord.Embed(title="📊 نتيجة التصويت", color=discord.Color.dark_red())
    if result.vote_counts:
        r_embed.add_field(
            name="🗳️ الأصوات",
            value="\n".join(
                f"{safe_name(t, eng)}: {c}"
                for t, c in sorted(result.vote_counts.items(), key=lambda x: -x[1])
            ),
            inline=False,
        )
    r_embed.add_field(name="🚨 النتيجة", value=result.message, inline=False)
    r_embed.set_footer(text=FOOTER_TEXT)
    await session.channel.send(embed=r_embed)

    winner = eng.check_win()
    if winner:
        await _end_game(session, winner)
        return

    eng.day_number += 1
    eng.reset_night_state()
    await asyncio.sleep(4)
    await _lock(session)
    await _night_phase(session)


async def _end_game(session: GameSession, winner: str):
    """Dramatic game-over screen with social roasting."""
    eng = session.engine
    eng.state = GameState.GAME_OVER
    await _unlock(session)

    if winner == "wolf":
        title = "🐺 انتصار الذيابة! 🐺"
        roast = random_wolf_win()
        color = discord.Color.red()
    else:
        title = "🎉 انتصار القرويين! 🎉"
        roast = random_village_win()
        color = discord.Color.green()

    embed = discord.Embed(title=title, description=roast, color=color)
    embed.set_image(url=PHASE_IMAGES["gameover"])

    roles_str = "\n".join(
        f"{'✅' if p.alive else '💀'} {p.name}: "
        f"{ROLE_INFO.get(p.role, {}).get('emoji', '❓')} "
        f"{ROLE_INFO.get(p.role, {}).get('name', p.role)}"
        for p in eng.players.values()
    )
    embed.add_field(name="📋 الأدوار النهائية", value=roles_str, inline=False)
    embed.add_field(name="👥 المتبقون", value=f"{len(eng.living_ids)} لاعب", inline=False)
    embed.set_footer(text=FOOTER_TEXT)
    await session.channel.send(embed=embed)

    games.pop(session.channel.id, None)

# ═══════════════════════════════════════════════════════════════
# PREFIX COMMANDS
# ═══════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    log.info(f"✅ Bot online as {bot.user}")
    try:
        await bot.tree.sync()
    except Exception:
        pass


@bot.command(name="ذئب", aliases=["start", "werewolf"])
async def cmd_start(ctx: commands.Context):
    """-ذئب : افتح لوبي لعبة الذئب في هذي القناة."""
    if not ctx.guild:
        return await ctx.send("❌ استخدم الأمر في سيرفر!")

    ch_id = ctx.channel.id
    if ch_id in games:
        return await ctx.send("❌ فيه لعبة شغالة في هذي القناة! استخدم -ايقاف لايقافها.")

    session = GameSession(ctx.channel, ctx.guild)
    games[ch_id] = session

    embed = build_lobby_embed(session, LOBBY_COUNTDOWN)
    view  = LobbyView(session)
    session.current_view = view
    msg   = await ctx.send(embed=embed, view=view)
    session.lobby_message = msg
    session.phase_task = asyncio.create_task(_lobby_loop(session))


@bot.command(name="ايقاف", aliases=["end", "stop"])
async def cmd_stop(ctx: commands.Context):
    """-ايقاف : إنهاء اللعبة الحالية فوراً."""
    ch_id = ctx.channel.id
    session = games.get(ch_id)
    if not session:
        return await ctx.send("❌ ما فيه لعبة شغالة في هذي القناة!")

    if session.phase_task:
        session.phase_task.cancel()
    session.engine.state = GameState.GAME_OVER
    await _unlock(session)
    games.pop(ch_id, None)
    await ctx.send("✅ تم إنهاء اللعبة وتصفير الذاكرة!")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    start_web()
    bot.run(TOKEN, log_handler=None)

if __name__ == "__main__":
    main()
