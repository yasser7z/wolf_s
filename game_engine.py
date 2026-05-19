import discord
import asyncio
import random
from config import *


class GameData:
    def __init__(self, guild_id, channel, creator):
        self.guild_id = guild_id
        self.channel = channel
        self.creator = creator
        self.players = {}
        self.roles = {}
        self.alive = set()
        self.phase = 'lobby'
        self.night_count = 0
        self.day_count = 0
        self.lobby_message = None
        self.starting = False

        self.night_votes = {}
        self.attacked_player = None
        self.detective_used = False
        self.detective_target = None
        self.bodyguard_used = False
        self.bodyguard_target = None
        self.king_used = False
        self.king_target = None
        self.doctor_last_target = None
        self.doctor_target = None
        self.seducer_target = None
        self.night_actors = set()

        self.day_votes = {}

        self.all_werewolves_voted = asyncio.Event()
        self.night_actions_done = asyncio.Event()
        self.vote_event = asyncio.Event()
        self.king_event = asyncio.Event()


class GameManager:
    def __init__(self):
        self.games = {}

    def get_game(self, guild_id):
        return self.games.get(guild_id)

    def create_game(self, guild_id, channel, creator):
        game = GameData(guild_id, channel, creator)
        self.games[guild_id] = game
        return game

    def end_game(self, guild_id):
        if guild_id in self.games:
            self.games[guild_id].phase = 'ended'
            del self.games[guild_id]

    def _get_role_counts(self, game):
        wc = vc = 0
        for pid in game.alive:
            if game.roles[pid] == 'werewolf':
                wc += 1
            else:
                vc += 1
        return wc, vc

    def _check_win(self, game):
        wc, vc = self._get_role_counts(game)
        if wc == 0:
            return 'village'
        if wc >= vc:
            return 'werewolf'
        return None

    def _distribute_roles(self, game):
        pids = list(game.players.keys())
        random.shuffle(pids)
        num = len(pids)
        nw = 2 if num <= 7 else 3
        pool_map = {
            6:  ['mayor', 'detective', 'doctor', 'bodyguard'],
            7:  ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress'],
            8:  ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress'],
            9:  ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress', 'om_zaki'],
            10: ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress', 'om_zaki', 'king'],
            11: ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress', 'om_zaki', 'king'],
            12: ['mayor', 'detective', 'doctor', 'bodyguard', 'seductress', 'om_zaki', 'king'],
        }
        selected = pool_map[num]
        roles = ['werewolf'] * nw + selected + ['villager'] * (num - nw - len(selected))
        random.shuffle(roles)
        game.roles = {}
        game.alive = set()
        for i, pid in enumerate(pids):
            game.roles[pid] = roles[i]
            game.alive.add(pid)

    def _check_werewolf_done(self, game):
        alive_ww = [pid for pid in game.alive if game.roles[pid] == 'werewolf']
        if all(w in game.night_votes for w in alive_ww):
            game.all_werewolves_voted.set()

    def _check_night_done(self, game):
        det_expected = any(game.roles[p] == 'detective' and not game.detective_used for p in game.alive)
        doc_expected = any(game.roles[p] == 'doctor' for p in game.alive)
        bg_expected  = any(game.roles[p] == 'bodyguard' and not game.bodyguard_used for p in game.alive)
        sed_expected = any(game.roles[p] == 'seductress' for p in game.alive)

        det_done = not det_expected or game.detective_used
        doc_done = not doc_expected or game.doctor_target is not None
        bg_done  = not bg_expected  or game.bodyguard_used
        sed_done = not sed_expected or game.seducer_target is not None

        if det_done and doc_done and bg_done and sed_done:
            game.night_actions_done.set()

    def _active_roles_alive(self, game):
        result = []
        for pid in game.alive:
            r = game.roles[pid]
            if r in NIGHT_ROLES_ACTION:
                if r == 'detective' and game.detective_used:
                    continue
                if r == 'bodyguard' and game.bodyguard_used:
                    continue
                result.append(pid)
        return result

    async def start_game(self, guild_id):
        game = self.games.get(guild_id)
        if not game or game.phase == 'ended':
            return
        game.phase = 'starting'
        self._distribute_roles(game)
        if game.lobby_message and game.lobby_message.view:
            for child in game.lobby_message.view.children:
                child.disabled = True
            await game.lobby_message.edit(view=game.lobby_message.view)
        embed = discord.Embed(
            title="🎭 تم توزيع الأدوار!",
            description="اضغط على الزر أدناه لرؤية دورك 👇",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=FOOTER)
        view = RoleRevealView(game)
        await game.channel.send(embed=embed, view=view)
        await asyncio.sleep(15)
        await self._run_night_phase(game)

    def _reset_phase(self, game):
        game.night_votes = {}
        game.attacked_player = None
        game.detective_target = None
        game.bodyguard_target = None
        game.doctor_target = None
        game.seducer_target = None
        game.king_target = None
        game.day_votes = {}
        game.night_actors = set()
        game.all_werewolves_voted = asyncio.Event()
        game.night_actions_done = asyncio.Event()
        game.vote_event = asyncio.Event()
        game.king_event = asyncio.Event()

    async def _run_night_phase(self, game):
        game.phase = 'night'
        game.night_count += 1
        ch = game.channel
        alive_ww = [pid for pid in game.alive if game.roles[pid] == 'werewolf']

        emb = discord.Embed(
            title=f"🌙 الليلة {game.night_count}",
            description="حل الظلام على القرية.. الذئاب تخرج من جحورها 👀\nأصحاب القدرات الخاصة، تحضروا!",
            color=COLOR_NIGHT
        )
        emb.set_image(url=GAME_GRAPHICS["night_phase"])
        emb.set_footer(text=FOOTER)
        await ch.send(embed=emb)
        await asyncio.sleep(3)

        if alive_ww:
            emb_w = discord.Embed(
                title="🐺 الذئاب تتشاور",
                description="الذئاب تبحث عن فريسة الليلة. اضغط الزر للتصويت على الضحية!",
                color=COLOR_NIGHT
            )
            emb_w.set_footer(text=FOOTER)
            wv = WerewolfVoteView(game)
            msg_w = await ch.send(embed=emb_w, view=wv)
            try:
                await asyncio.wait_for(game.all_werewolves_voted.wait(), timeout=WEREWOLF_VOTE_TIME)
            except asyncio.TimeoutError:
                pass
            if game.night_votes:
                vc = {}
                for t in game.night_votes.values():
                    vc[t] = vc.get(t, 0) + 1
                mv = max(vc.values())
                top = [t for t, c in vc.items() if c == mv]
                game.attacked_player = random.choice(top)
            wv.disable_all()
            await msg_w.edit(view=wv)

        if self._active_roles_alive(game):
            emb_n = discord.Embed(
                title="🌙 أصحاب القدرات",
                description="الليل وقت الفعل! أصحاب القدرات يتحركون في الظلام 👤",
                color=COLOR_NIGHT
            )
            emb_n.set_footer(text=FOOTER)
            nv = NightActionView(game)
            msg_n = await ch.send(embed=emb_n, view=nv)
            try:
                await asyncio.wait_for(game.night_actions_done.wait(), timeout=NIGHT_ACTIONS_TIME)
            except asyncio.TimeoutError:
                pass
            nv.disable_all()
            await msg_n.edit(view=nv)

        await self._resolve_night(game)

    async def _resolve_night(self, game):
        ch = game.channel
        deaths = []
        attacked = game.attacked_player
        saved = False

        if attacked and attacked in game.alive:
            if game.seducer_target == attacked:
                if game.roles[attacked] != 'werewolf':
                    saved = True
                    from_id = next((p for p, r in game.roles.items() if r == 'seductress' and p in game.alive), None)
                    if from_id:
                        sm = random.choice(SEDUCER_SAVE_MESSAGES)
                        sm = sm.replace("{seducer}", game.players[from_id].display_name).replace("{target}", game.players[attacked].display_name)
                        await ch.send(embed=discord.Embed(description=sm, color=COLOR_SUCCESS).set_footer(text=FOOTER))

            if not saved and game.bodyguard_used and game.bodyguard_target == attacked:
                saved = True
                bm = random.choice(BODYGUARD_SAVE_MSGS).replace("{player}", game.players[attacked].display_name)
                await ch.send(embed=discord.Embed(description=bm, color=COLOR_SUCCESS).set_footer(text=FOOTER))

            if not saved and game.doctor_target == attacked:
                saved = True
                dm = random.choice(DOCTOR_HEAL_MSGS).replace("{player}", game.players[attacked].display_name)
                await ch.send(embed=discord.Embed(description=dm, color=COLOR_SUCCESS).set_footer(text=FOOTER))

            if not saved:
                deaths.append(attacked)

        seducer_pid = next((p for p, r in game.roles.items() if r == 'seductress' and p in game.alive), None)
        if seducer_pid and game.seducer_target:
            if game.roles.get(game.seducer_target) == 'werewolf' and game.seducer_target in game.alive:
                if seducer_pid not in deaths:
                    deaths.append(seducer_pid)
                if game.seducer_target not in deaths:
                    deaths.append(game.seducer_target)
                sm = random.choice(SEDUCER_DEATH_MESSAGES)
                sm = sm.replace("{seducer}", game.players[seducer_pid].display_name).replace("{target}", game.players[game.seducer_target].display_name)
                await ch.send(embed=discord.Embed(description=sm, color=COLOR_DANGER).set_footer(text=FOOTER))

        deaths = list(set(deaths))
        om_zaki_exposed = False
        for pid in deaths:
            if pid in game.alive:
                game.alive.discard(pid)
                member = game.players[pid]
                dm = random.choice(DEATH_MESSAGES).replace("{player}", member.display_name)
                emb = discord.Embed(title="💀 انذبح واحد!", description=dm, color=COLOR_DANGER)
                emb.set_footer(text=FOOTER)
                await ch.send(embed=emb)
                await asyncio.sleep(1)

            if game.roles.get(pid) == 'om_zaki' and pid == attacked and not saved:
                om_zaki_exposed = True

        if om_zaki_exposed:
            alive_wolves = [p for p in game.alive if game.roles.get(p) == 'werewolf']
            if alive_wolves:
                exposed = random.choice(alive_wolves)
                em = random.choice(OM_ZAKI_EXPOSE_MESSAGES).replace("{werewolf}", game.players[exposed].display_name)
                await ch.send(embed=discord.Embed(description=em, color=COLOR_DANGER).set_footer(text=FOOTER))

        if not deaths and not om_zaki_exposed:
            emb = discord.Embed(
                title="☀️ الصباح الجميل",
                description="لا أحد مات الليلة! الكل بخير ☀️😊",
                color=COLOR_DAY
            )
            emb.set_footer(text=FOOTER)
            await ch.send(embed=emb)

        await asyncio.sleep(2)
        winner = self._check_win(game)
        if winner:
            await self._end_game_with_winner(game, winner)
            return
        self._reset_phase(game)
        await self._run_day_phase(game)

    async def _run_day_phase(self, game):
        game.phase = 'day'
        game.day_count += 1
        ch = game.channel
        alive_list = "\n".join([f"👤 {game.players[pid].display_name}" for pid in game.alive])
        emb = discord.Embed(
            title=f"☀️ النهار {game.day_count}",
            description=(
                f"طلعت الشمس! القرية صحت من النوم 🐓\n\n"
                f"**اللاعبون الأحياء ({len(game.alive)}):**\n{alive_list}\n\n"
                f"🗳️ التصويت مفتوح! صوت على الشخص اللي تشك فيه..."
            ),
            color=COLOR_DAY
        )
        emb.set_image(url=GAME_GRAPHICS["day_phase"])
        emb.set_footer(text=FOOTER)
        await ch.send(embed=emb)
        await asyncio.sleep(3)

        king_pid = next((p for p, r in game.roles.items() if r == 'king' and p in game.alive), None)
        if king_pid and not game.king_used:
            emb_k = discord.Embed(
                title="👑 الملك يتربع على عرشه",
                description="الملك يقدر يستخدم سلطته ويطرد أي لاعب بدون تصويت! (مرة وحدة بالقيم)",
                color=COLOR_DAY
            )
            emb_k.set_footer(text=FOOTER)
            kv = KingActionView(game, king_pid)
            msg_k = await ch.send(embed=emb_k, view=kv)
            try:
                await asyncio.wait_for(game.king_event.wait(), timeout=KING_ACTION_TIME)
            except asyncio.TimeoutError:
                pass
            kv.disable_all()
            await msg_k.edit(view=kv)

            if game.king_used and game.king_target:
                eliminated = game.king_target
                game.alive.discard(eliminated)
                member = game.players[eliminated]
                km = random.choice(KING_DECREE_MSGS).replace("{player}", member.display_name)
                emb_kd = discord.Embed(title="👑 أمر ملكي!", description=km, color=COLOR_DANGER)
                emb_kd.set_footer(text=FOOTER)
                await ch.send(embed=emb_kd)
                role_key = game.roles.get(eliminated, 'unknown')
                ri = ROLES_CONFIG.get(role_key, {})
                await ch.send(f"🎭 **{member.display_name}** كانوا **{ri.get('emoji', '')} {ri.get('name', 'مجهول')}**")
                await asyncio.sleep(2)
                winner = self._check_win(game)
                if winner:
                    await self._end_game_with_winner(game, winner)
                    return
                self._reset_phase(game)
                await self._run_night_phase(game)
                return

        emb_v = discord.Embed(
            title="🗳️ التصويت",
            description="كل واحد عنده صوت واحد. اختر الشخص اللي تبي تطرده!",
            color=COLOR_DAY
        )
        emb_v.set_footer(text=FOOTER)
        view = DayVoteView(game)
        msg_v = await ch.send(embed=emb_v, view=view)
        try:
            await asyncio.wait_for(self._wait_all_votes(game), timeout=DAY_VOTE_TIME)
        except asyncio.TimeoutError:
            pass
        view.disable_all()
        await msg_v.edit(view=view)
        await self._process_day_votes(game)

    async def _wait_all_votes(self, game):
        while True:
            if game.vote_event.is_set():
                if game.day_votes and len(game.day_votes) >= len(game.alive):
                    return
            await asyncio.sleep(0.5)

    async def _process_day_votes(self, game):
        ch = game.channel
        mayor_pid = next((p for p, r in game.roles.items() if r == 'mayor' and p in game.alive), None)

        if not game.day_votes:
            emb = discord.Embed(title="📊 لا يوجد تصويت", description="ما حدا صوت! يمكن الكل نايم 😂", color=COLOR_DAY)
            emb.set_footer(text=FOOTER)
            await ch.send(embed=emb)
        else:
            vc = {}
            for voter_id, tid in game.day_votes.items():
                weight = 2 if voter_id == mayor_pid else 1
                vc[tid] = vc.get(tid, 0) + weight

            mv = max(vc.values())
            top = [t for t, c in vc.items() if c == mv]

            if mayor_pid and mayor_pid in game.day_votes:
                mn = game.players[mayor_pid].display_name
                await ch.send(MAYOR_VOTE_NOTIFY.format(player=mn, votes=2))

            rt = "**عدد الأصوات:**\n"
            for tid, c in sorted(vc.items(), key=lambda x: -x[1]):
                name = game.players[tid].display_name
                bar = "█" * c + "░" * (mv - c) if mv > c else "█" * c
                rt += f"**{name}**: {bar} {c} صوت\n"

            emb = discord.Embed(title="📊 نتائج التصويت", description=rt, color=COLOR_DAY)
            emb.set_footer(text=FOOTER)
            await ch.send(embed=emb)
            await asyncio.sleep(3)

            if len(top) > 1:
                emb_t = discord.Embed(
                    title="⚖️ تعادل!",
                    description="في تعادل! ولا أحد يطرد اليوم. الذئاب حظها حلو 😤",
                    color=COLOR_DAY
                )
                emb_t.set_footer(text=FOOTER)
                await ch.send(embed=emb_t)
            else:
                eliminated = top[0]
                game.alive.discard(eliminated)
                member = game.players[eliminated]
                dm = random.choice(DEATH_MESSAGES).replace("{player}", member.display_name)
                emb_e = discord.Embed(title=f"🚨 طرد!", description=dm, color=COLOR_DANGER)
                emb_e.set_footer(text=FOOTER)
                await ch.send(embed=emb_e)
                role_key = game.roles.get(eliminated, 'unknown')
                ri = ROLES_CONFIG.get(role_key, {})
                await ch.send(f"🎭 **{member.display_name}** كانوا **{ri.get('emoji', '')} {ri.get('name', 'مجهول')}**")

        await asyncio.sleep(2)
        winner = self._check_win(game)
        if winner:
            await self._end_game_with_winner(game, winner)
            return
        self._reset_phase(game)
        await self._run_night_phase(game)

    async def _end_game_with_winner(self, game, winner):
        ch = game.channel
        if winner == 'werewolf':
            msg = random.choice(WEREWOLF_WIN_MESSAGES)
            color = COLOR_DANGER
            title = "🐺 **انتهت اللعبة! فوز الذئاب!** 🌕"
            img = GAME_GRAPHICS["werewolf_victory"]
        else:
            msg = random.choice(VILLAGER_WIN_MESSAGES)
            color = COLOR_SUCCESS
            title = "🏆 **انتهت اللعبة! فوز القرية!** 🎉"
            img = GAME_GRAPHICS["villager_victory"]
        all_players = "\n".join([
            f"{ROLES_CONFIG[game.roles[pid]]['emoji']} {game.players[pid].display_name} - {ROLES_CONFIG[game.roles[pid]]['name']}"
            for pid in game.players
        ])
        emb = discord.Embed(title=title, description=msg, color=color)
        emb.set_image(url=img)
        emb.add_field(name="📋 اللاعبون:", value=all_players, inline=False)
        emb.set_footer(text=FOOTER)
        await ch.send(embed=emb)
        game.phase = 'ended'
        self.end_game(game.guild_id)


manager = GameManager()


def create_role_embed(rk):
    r = ROLES_CONFIG[rk]
    emb = discord.Embed(title=f"{r['emoji']} {r['name']}", description=r['description'], color=COLOR_PRIMARY)
    emb.set_image(url=r['image'])
    emb.set_footer(text=FOOTER)
    return emb


def create_lobby_embed(game):
    pl = "\n".join([f"**{i+1}.** 👤 {m.display_name}" for i, m in enumerate(game.players.values())])
    c = len(game.players)
    st = f"✅ **{c}/{MAX_PLAYERS}** لاعب"
    if c >= MIN_PLAYERS:
        st += "\n⏳ جارٍ بدء اللعبة قريباً..."
    emb = discord.Embed(
        title="🐺 **لعبة الذئب - اللوبي**",
        description=f"{st}\n\n**قائمة اللاعبين:**\n{pl if pl else 'لا يوجد لاعبين بعد'}",
        color=COLOR_LOBBY
    )
    emb.set_footer(text=FOOTER)
    return emb


class LobbyView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game

    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.green, emoji="➕")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.game.players:
            return await interaction.response.send_message("🖐️ أنت منضم بالفعل!", ephemeral=True)
        if len(self.game.players) >= MAX_PLAYERS:
            return await interaction.response.send_message("❌ اللوبي ممتلئ!", ephemeral=True)
        if self.game.phase != 'lobby':
            return await interaction.response.send_message("❌ اللعبة بدأت بالفعل!", ephemeral=True)
        self.game.players[interaction.user.id] = interaction.user
        await interaction.response.send_message("✅ تم الانضمام بنجاح!", ephemeral=True)
        await self._update()
        if len(self.game.players) >= MIN_PLAYERS and not self.game.starting:
            self.game.starting = True
            asyncio.create_task(self._auto_start())

    @discord.ui.button(label="مغادرة", style=discord.ButtonStyle.red, emoji="❌")
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.players:
            return await interaction.response.send_message("🖐️ أنت لست منضم!", ephemeral=True)
        if self.game.phase != 'lobby':
            return await interaction.response.send_message("❌ اللعبة بدأت بالفعل!", ephemeral=True)
        del self.game.players[interaction.user.id]
        await interaction.response.send_message("✅ تمت المغادرة!", ephemeral=True)
        await self._update()

    @discord.ui.button(label="شرح اللعبة", style=discord.ButtonStyle.blurple, emoji="📖")
    async def guide_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="📖 دليل لعبة الذئب", description=LOBBY_GUIDE_TEXT, color=COLOR_PRIMARY)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @discord.ui.button(label="مطور البوت", style=discord.ButtonStyle.grey, emoji="🛠️")
    async def dev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        emb = discord.Embed(title="🛠️ مطور البوت", description=DEVELOPER_INFO, color=COLOR_PRIMARY)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    async def _update(self):
        emb = create_lobby_embed(self.game)
        await self.game.lobby_message.edit(embed=emb, view=self)

    async def _auto_start(self):
        await asyncio.sleep(10)
        game = self.game
        if game.phase != 'lobby':
            return
        if len(game.players) < MIN_PLAYERS:
            game.starting = False
            game.phase = 'lobby'
            emb = create_lobby_embed(game)
            emb.description += "\n\n❌ لم يكتمل العدد، تم إلغاء البداية التلقائية"
            await game.lobby_message.edit(embed=emb)
            return
        await manager.start_game(game.guild_id)


class RoleRevealView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=60)
        self.game = game

    @discord.ui.button(label="🎭 اعرض دوري", style=discord.ButtonStyle.primary, emoji="🎭")
    async def reveal(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.roles:
            return await interaction.response.send_message("❌ أنت لست في اللعبة!", ephemeral=True)
        emb = create_role_embed(self.game.roles[interaction.user.id])
        await interaction.response.send_message(embed=emb, ephemeral=True)


class WerewolfVoteView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=WEREWOLF_VOTE_TIME)
        self.game = game

    @discord.ui.button(label="🐺 تصويت الذئاب", style=discord.ButtonStyle.danger, emoji="🐺")
    async def ww_vote(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.game.roles:
            return await interaction.response.send_message("❌ أنت لست في اللعبة!", ephemeral=True)
        if uid not in self.game.alive:
            return await interaction.response.send_message("💀 أنت ميت!", ephemeral=True)
        if self.game.roles[uid] != 'werewolf':
            return await interaction.response.send_message("💤 ما عندك قدرة ليلية! نام نوووم 🌙", ephemeral=True)
        if uid in self.game.night_votes:
            return await interaction.response.send_message("✅你已经 صوّت!", ephemeral=True)
        ww_ids = {pid for pid, r in self.game.roles.items() if r == 'werewolf'}
        opts = []
        for mid in self.game.alive:
            if mid in ww_ids:
                continue
            opts.append(discord.SelectOption(label=self.game.players[mid].display_name, value=str(mid), emoji="👤"))
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد أهداف!", ephemeral=True)
        sel = WerewolfSelect(self.game, uid, opts)
        v = discord.ui.View(timeout=WEREWOLF_VOTE_TIME)
        v.add_item(sel)
        await interaction.response.send_message("🎯 اختر ضحيتك:", view=v, ephemeral=True)

    def disable_all(self):
        for child in self.children:
            child.disabled = True


class WerewolfSelect(discord.ui.Select):
    def __init__(self, game, voter_id, options):
        super().__init__(placeholder="اختر الهدف...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.voter_id = voter_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.voter_id:
            return await interaction.response.send_message("❌ هذا ليس تصويتك!", ephemeral=True)
        target_id = int(self.values[0])
        self.game.night_votes[self.voter_id] = target_id
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم التصويت!", view=self.view)
        manager._check_werewolf_done(self.game)


class NightActionView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=NIGHT_ACTIONS_TIME)
        self.game = game

    @discord.ui.button(label="🌙 فعل القدرة الليلية", style=discord.ButtonStyle.secondary, emoji="🌙")
    async def action(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.game.roles:
            return await interaction.response.send_message("❌ أنت لست في اللعبة!", ephemeral=True)
        if uid not in self.game.alive:
            return await interaction.response.send_message("💀 أنت ميت!", ephemeral=True)

        role = self.game.roles[uid]
        if role not in NIGHT_ROLES_ACTION:
            return await interaction.response.send_message("💤 ما عندك قدرة ليلية! نام نوووم 🌙", ephemeral=True)

        if role == 'detective' and self.game.detective_used:
            return await interaction.response.send_message("🔍 استخدمت قدرتك مسبقاً!", ephemeral=True)
        if role == 'bodyguard' and self.game.bodyguard_used:
            return await interaction.response.send_message("🛡️ استخدمت قدرتك مسبقاً!", ephemeral=True)
        if uid in self.game.night_actors:
            return await interaction.response.send_message("✅ تصرفت هذه الليلة!", ephemeral=True)

        if role == 'detective':
            await self._detective_action(interaction)
        elif role == 'doctor':
            await self._doctor_action(interaction)
        elif role == 'bodyguard':
            await self._bodyguard_action(interaction)
        elif role == 'seductress':
            await self._seductress_action(interaction)

    async def _detective_action(self, interaction):
        g = self.game
        opts = [discord.SelectOption(label=g.players[mid].display_name, value=str(mid), emoji="👤") for mid in g.alive]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = DetectiveSelect(g, interaction.user.id, opts)
        v = discord.ui.View(timeout=NIGHT_ACTIONS_TIME)
        v.add_item(sel)
        emb = discord.Embed(title="🔍 المحقق", description="اختر شخصاً لكشف حقيقته:", color=COLOR_NIGHT)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, view=v, ephemeral=True)

    async def _doctor_action(self, interaction):
        g = self.game
        opts = [discord.SelectOption(label=g.players[mid].display_name, value=str(mid), emoji="👤") for mid in g.alive]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = DoctorSelect(g, interaction.user.id, opts)
        v = discord.ui.View(timeout=NIGHT_ACTIONS_TIME)
        v.add_item(sel)
        emb = discord.Embed(title="⚕️ الطبيب", description="اختر من تبي تحميه هذه الليلة:", color=COLOR_NIGHT)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, view=v, ephemeral=True)

    async def _bodyguard_action(self, interaction):
        g = self.game
        opts = [discord.SelectOption(label=g.players[mid].display_name, value=str(mid), emoji="👤") for mid in g.alive]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = BodyguardSelect(g, interaction.user.id, opts)
        v = discord.ui.View(timeout=NIGHT_ACTIONS_TIME)
        v.add_item(sel)
        emb = discord.Embed(title="🛡️ الحارس", description="اختر من تعطيه درع الحماية (مرة واحدة):", color=COLOR_NIGHT)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, view=v, ephemeral=True)

    async def _seductress_action(self, interaction):
        g = self.game
        opts = [discord.SelectOption(label=g.players[mid].display_name, value=str(mid), emoji="👤") for mid in g.alive if mid != interaction.user.id]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = SeductressSelect(g, interaction.user.id, opts)
        v = discord.ui.View(timeout=NIGHT_ACTIONS_TIME)
        v.add_item(sel)
        emb = discord.Embed(title="💃 المغرية", description="اختاري من تزورين هذه الليلة:", color=COLOR_NIGHT)
        emb.set_footer(text=FOOTER)
        await interaction.response.send_message(embed=emb, view=v, ephemeral=True)

    def disable_all(self):
        for child in self.children:
            child.disabled = True


class DetectiveSelect(discord.ui.Select):
    def __init__(self, game, pid, options):
        super().__init__(placeholder="اختر المشتبه به...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.pid = pid

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.pid:
            return await interaction.response.send_message("❌ هذا ليس اختيارك!", ephemeral=True)
        target_id = int(self.values[0])
        target_role = self.game.roles[target_id]
        ri = ROLES_CONFIG[target_role]
        self.game.detective_target = target_id
        self.game.detective_used = True
        self.game.night_actors.add(self.pid)
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم الكشف!", view=self.view)
        rm = random.choice(DETECTIVE_REVEAL_PHRASES)
        rm = rm.replace("{target}", self.game.players[target_id].display_name).replace("{emoji}", ri['emoji']).replace("{role}", ri['name'])
        await interaction.followup.send(embed=discord.Embed(description=rm, color=COLOR_PRIMARY).set_footer(text=FOOTER), ephemeral=True)
        manager._check_night_done(self.game)


class DoctorSelect(discord.ui.Select):
    def __init__(self, game, pid, options):
        super().__init__(placeholder="اختر من تعالجه...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.pid = pid

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.pid:
            return await interaction.response.send_message("❌ هذا ليس اختيارك!", ephemeral=True)
        target_id = int(self.values[0])
        if target_id == self.game.doctor_last_target:
            return await interaction.response.send_message("❌ ما تقدر تحمي نفس الشخص مرتين متتاليتين!", ephemeral=True)
        self.game.doctor_target = target_id
        self.game.doctor_last_target = target_id
        self.game.night_actors.add(self.pid)
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم اختيار المريض!", view=self.view)
        manager._check_night_done(self.game)


class BodyguardSelect(discord.ui.Select):
    def __init__(self, game, pid, options):
        super().__init__(placeholder="اختر من تحميه...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.pid = pid

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.pid:
            return await interaction.response.send_message("❌ هذا ليس اختيارك!", ephemeral=True)
        target_id = int(self.values[0])
        self.game.bodyguard_target = target_id
        self.game.bodyguard_used = True
        self.game.night_actors.add(self.pid)
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم منح الدرع!", view=self.view)
        manager._check_night_done(self.game)


class SeductressSelect(discord.ui.Select):
    def __init__(self, game, pid, options):
        super().__init__(placeholder="اختاري من تزورين...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.pid = pid

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.pid:
            return await interaction.response.send_message("❌ هذا ليس اختيارك!", ephemeral=True)
        target_id = int(self.values[0])
        self.game.seducer_target = target_id
        self.game.night_actors.add(self.pid)
        self.disabled = True
        await interaction.response.edit_message(content="✅ تمت الزيارة!", view=self.view)
        manager._check_night_done(self.game)


class DayVoteView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=DAY_VOTE_TIME)
        self.game = game

    @discord.ui.button(label="🗳️ تصويت", style=discord.ButtonStyle.primary, emoji="🗳️")
    async def vote_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        uid = interaction.user.id
        if uid not in self.game.roles:
            return await interaction.response.send_message("❌ أنت لست في اللعبة!", ephemeral=True)
        if uid not in self.game.alive:
            return await interaction.response.send_message("💀 أنت ميت! ما تقدر تصوت", ephemeral=True)
        if uid in self.game.day_votes:
            return await interaction.response.send_message("✅你已经 صوّت!", ephemeral=True)
        opts = [discord.SelectOption(label=self.game.players[mid].display_name, value=str(mid), emoji="👤") for mid in self.game.alive]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = DayVoteSelect(self.game, uid, opts)
        v = discord.ui.View(timeout=DAY_VOTE_TIME)
        v.add_item(sel)
        await interaction.response.send_message("🗳️ اختر من تبي تطرده:", view=v, ephemeral=True)

    def disable_all(self):
        for child in self.children:
            child.disabled = True


class DayVoteSelect(discord.ui.Select):
    def __init__(self, game, voter_id, options):
        super().__init__(placeholder="اختر المشتبه به...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.voter_id = voter_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.voter_id:
            return await interaction.response.send_message("❌ هذا ليس تصويتك!", ephemeral=True)
        target_id = int(self.values[0])
        self.game.day_votes[self.voter_id] = target_id
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم التصويت!", view=self.view)
        if len(self.game.day_votes) >= len(self.game.alive):
            self.game.vote_event.set()


class KingActionView(discord.ui.View):
    def __init__(self, game, king_id):
        super().__init__(timeout=KING_ACTION_TIME)
        self.game = game
        self.king_id = king_id

    @discord.ui.button(label="👑 أمر ملكي", style=discord.ButtonStyle.danger, emoji="👑")
    async def king_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.king_id:
            return await interaction.response.send_message("❌ هذا ليس دورك!", ephemeral=True)
        opts = [discord.SelectOption(label=self.game.players[mid].display_name, value=str(mid), emoji="👤") for mid in self.game.alive if mid != self.king_id]
        if not opts:
            return await interaction.response.send_message("❌ لا يوجد لاعبين!", ephemeral=True)
        sel = KingSelect(self.game, self.king_id, opts)
        v = discord.ui.View(timeout=KING_ACTION_TIME)
        v.add_item(sel)
        await interaction.response.send_message("👑 اختر من تطرد بأمر ملكي:", view=v, ephemeral=True)

    def disable_all(self):
        for child in self.children:
            child.disabled = True


class KingSelect(discord.ui.Select):
    def __init__(self, game, king_id, options):
        super().__init__(placeholder="اختر الضحية الملكية...", options=options[:25], min_values=1, max_values=1)
        self.game = game
        self.king_id = king_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.king_id:
            return
        target_id = int(self.values[0])
        self.game.king_target = target_id
        self.game.king_used = True
        self.disabled = True
        await interaction.response.edit_message(content="✅ تم إصدار الأمر!", view=self.view)
        self.game.king_event.set()
