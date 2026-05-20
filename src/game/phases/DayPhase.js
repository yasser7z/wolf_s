const {
  ActionRowBuilder,
  StringSelectMenuBuilder,
  ButtonBuilder,
  ButtonStyle,
} = require('discord.js');
const BasePhase = require('./base/BasePhase');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');
const DayNarrator = require('../narrators/DayNarrator');

const VOTE_TIME = 30000;
const REVOTE_TIME = 15000;

class DayPhase extends BasePhase {
  constructor(session) {
    super(session, { name: 'day_voting' });
    this.votes = {};
    this.revoteMode = false;
    this.voteMsg = null;
    this._revoteMsg = null;
    this._tiedIds = [];
  }

  async startVoting() {
    this.votes = {};
    this.revoteMode = false;
    const alive = this.getAlive();

    const voteButton = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId('vote:menu')
        .setLabel('🗳️ صوت الآن')
        .setStyle(ButtonStyle.Success)
        .setEmoji('🗳️'),
    );

    const king = this.session.players.find(p => p.alive && p.role?.id === 'King' && !p.role.hasExecuted);
    const kingRow = king ? new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId('king:execute:menu')
        .setLabel('👑 إعدام ملكي')
        .setStyle(ButtonStyle.Danger)
        .setEmoji('⚔️'),
    ) : null;

    const components = kingRow ? [voteButton, kingRow] : [voteButton];

    this.voteMsg = await this.send({
      embeds: [gameEmbed(
        '🗳️ التصويت',
        `${DayNarrator.voteStart()}\n\n⏱️ **الوقت:** 30 ثانية\n━━━━━━━━━━━━━━━━\n_اضغط على 🗳️ للتصويت السري._`,
        COLORS.WARN
      ).setFooter({ text: 'Vale Community • صوتك سري' })],
      components,
    });

    if (!this.voteMsg) return;

    // Timeout triggers the end of voting
    this.setTimeout(() => this._finalize(), VOTE_TIME);
  }

  // ─── Route Handlers ─────────────────────────────

  async handleVoteMenu(interaction) {
    if (!this.session.fsm?.is('voting')) {
      return interaction.reply({ content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    if (this.revoteMode) return; // ignore during revote

    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }
    if (this.votes[player.id]) {
      return interaction.reply({ content: '❌ لقد صوّت بالفعل!', ephemeral: true });
    }

    const alive = this.getAlive();
    const options = [
      { label: '⏭️ تخطي التصويت', value: 'skip', emoji: '⏭️' },
      ...alive.map(p => ({ label: p.username, value: p.id })),
    ];

    const row = new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('vote:menu')
        .setPlaceholder('🗳️ اختر من تظن أنه ذئب...')
        .addOptions(options),
    );

    return interaction.reply({
      embeds: [gameEmbed('🗳️ اختر صوتك', 'اختر اللاعب الذي تعتقد أنه **ذئب**.', COLORS.WARN)],
      components: [row],
      ephemeral: true,
    });
  }

  async handleVoteCast(interaction, targetId) {
    if (!this.session.fsm?.is('voting')) {
      return interaction.reply({ content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    if (this.revoteMode) return;

    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }
    if (this.votes[player.id]) {
      return interaction.reply({ content: '❌ لقد صوّت بالفعل ولا يمكنك التعديل!', ephemeral: true });
    }

    this.votes[player.id] = targetId;
    this.session.eventBus.emit('vote.cast', { voterId: player.id, targetId });

    return interaction.reply({
      content: targetId === 'skip'
        ? '⏭️ **صوّتت بتخطي.**'
        : `🗳️ **صوّتت لـ <@${targetId}>**\n_صوتك مسجل ولا يمكن تغييره._`,
      ephemeral: true,
    });
  }

  async handleRevoteMenu(interaction) {
    if (!this.session.fsm?.is('voting') || !this.revoteMode) {
      return interaction.reply({ content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }
    if (this.votes[player.id]) {
      return interaction.reply({ content: '❌ لقد صوّت في الإعادة!', ephemeral: true });
    }

    const options = this._tiedIds.map(id => {
      const p = this.session.players.find(pl => pl.id === id);
      return p ? { label: p.username, value: p.id } : null;
    }).filter(Boolean);

    const row = new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('vote:revote:menu')
        .setPlaceholder('🔄 اختر أحد المتعادلين...')
        .addOptions(options),
    );

    return interaction.reply({
      embeds: [gameEmbed(
        '🔄 إعادة التصويت',
        `اختر أحد المتعادلين — لا يوجد تخطي.`,
        COLORS.WARN
      )],
      components: [row],
      ephemeral: true,
    });
  }

  async handleRevoteCast(interaction, targetId) {
    if (!this.session.fsm?.is('voting') || !this.revoteMode) {
      return interaction.reply({ content: '❌ انتهى وقت الإعادة.', ephemeral: true });
    }
    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }
    if (this.votes[player.id]) {
      return interaction.reply({ content: '❌ لقد صوّت في الإعادة!', ephemeral: true });
    }

    this.votes[player.id] = targetId;
    this.session.eventBus.emit('vote.cast', { voterId: player.id, targetId });

    return interaction.reply({
      content: `🔄 **صوّت لـ <@${targetId}> في الإعادة.**`,
      ephemeral: true,
    });
  }

  async handleKingMenu(interaction) {
    if (!this.session.fsm?.is('voting')) {
      return interaction.reply({ content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }
    if (player.role?.id !== 'King') {
      return interaction.reply({ content: '❌ هذا الزر للملك فقط!', ephemeral: true });
    }
    if (player.role.hasExecuted) {
      return interaction.reply({ content: '❌ لقد استخدمت صلاحية الإعدام مسبقاً!', ephemeral: true });
    }

    const alive = this.getAlive();
    const options = alive
      .filter(p => p.id !== player.id)
      .map(p => ({ label: p.username, value: p.id }));

    if (options.length === 0) {
      return interaction.reply({ content: '❌ لا يوجد لاعبين أحياء.', ephemeral: true });
    }

    const row = new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('king:execute:menu')
        .setPlaceholder('👑 اختر من تنفذ فيه حكم الإعدام...')
        .addOptions(options),
    );

    return interaction.reply({
      embeds: [gameEmbed('👑 الإعدام الملكي', 'اختر اللاعب للإعدام الفوري.', COLORS.ERROR)],
      components: [row],
      ephemeral: true,
    });
  }

  async handleKingExecute(interaction, targetId) {
    if (!this.session.fsm?.is('voting')) {
      return interaction.reply({ content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const player = this.session.players.find(p => p.id === interaction.user.id && p.alive);
    if (!player || player.role?.id !== 'King') {
      return interaction.reply({ content: '❌ هذا الأمر للملك فقط!', ephemeral: true });
    }
    if (player.role.hasExecuted) {
      return interaction.reply({ content: '❌ لقد استخدمت صلاحية الإعدام مسبقاً!', ephemeral: true });
    }

    const target = this.session.players.find(p => p.id === targetId);
    if (!target || !target.alive) {
      return interaction.reply({ content: '❌ اللاعب المختار ميت.', ephemeral: true });
    }

    target.alive = false;
    player.role.execute();

    await interaction.reply({
      content: `👑 **<@${player.id}> أمر بإعدام <@${targetId}>!**\n_حكم الملك لا يُرد._`,
      ephemeral: false,
    });

    this.session.checkWinCondition();
  }

  // ─── Tally ──────────────────────────────────────

  _computeTally(votes) {
    const tally = {};
    let skipCount = 0;
    Object.keys(votes).forEach(voterId => {
      const v = votes[voterId];
      if (v === 'skip') { skipCount++; return; }
      const voter = this.session.players.find(p => p.id === voterId);
      const weight = voter?.role?.id === 'Mayor' ? 2 : 1;
      tally[v] = (tally[v] || 0) + weight;
    });

    let maxVotes = 0, mostVoted = null, tie = false;
    const tiedIds = [];
    Object.entries(tally).forEach(([id, c]) => {
      if (c > maxVotes) { maxVotes = c; mostVoted = id; tie = false; tiedIds.length = 0; tiedIds.push(id); }
      else if (c === maxVotes) { tie = true; tiedIds.push(id); }
    });

    if (Object.keys(tally).length === 0) {
      return { tally, skipCount, mostVoted: null, tie: false, tiedIds: [] };
    }
    return { tally, skipCount, mostVoted, tie, tiedIds };
  }

  async _finalize() {
    const result = this._computeTally(this.votes);

    // Tie → revote
    if (result.tie && result.tiedIds.length >= 2 && !this.revoteMode) {
      await this._startRevote(result.tiedIds);
      return;
    }

    await this._announceResult(result);
  }

  async _startRevote(tiedIds) {
    this.revoteMode = true;
    this.votes = {};
    this._tiedIds = tiedIds;

    const mentions = tiedIds.map(id => `<@${id}>`).join(' و ');
    this._revoteMsg = await this.session.channel.send({
      embeds: [gameEmbed(
        '🔄 إعادة تصويت!',
        `⚖️ **تعادل بين:** ${mentions}\n\n_سيتم إعادة التصويت بينهم فقط._\n⏱️ **الوقت:** 15 ثانية`,
        COLORS.WARN
      )],
      components: [
        new ActionRowBuilder().addComponents(
          new ButtonBuilder()
            .setCustomId('vote:revote:menu')
            .setLabel('🔄 إعادة تصويت')
            .setStyle(ButtonStyle.Primary)
            .setEmoji('🗳️'),
        ),
      ],
    });

    // Clear the original VOTE_TIME timeout, set revote timeout
    this._clearTimeout();
    this.setTimeout(() => this._finalizeRevote(), REVOTE_TIME);
  }

  async _finalizeRevote() {
    const result = this._computeTally(this.votes);

    // Second tie → no execution
    if (result.tie && result.tiedIds.length >= 2) {
      result.mostVoted = null;
    }

    await this._announceResult(result);
  }

  async _announceResult({ tally, skipCount, mostVoted, tie }) {
    const alive = this.session.getAlivePlayers();
    const eliminated = tie || !mostVoted ? null : this.session.players.find(p => p.id === mostVoted);
    if (eliminated) eliminated.alive = false;

    let tallyText = '\n━━━━━━━━━━━━━━━━\n📊 **نتائج التصويت:**\n';
    alive.forEach(p => {
      const v = tally[p.id] || 0;
      if (v > 0) tallyText += `> <@${p.id}>: **${v}** صوت${v > 1 ? 'ين' : ''}\n`;
    });
    if (skipCount > 0) tallyText += `> ⏭️ تخطي: **${skipCount}** صوت\n`;
    tallyText += '━━━━━━━━━━━━━━━━\n';

    const roleReveal = eliminated?.role?.getInfo();
    let resultText = DayNarrator.voteResult(eliminated, tie);
    if (roleReveal) resultText += `\n\n📜 **دوره:** ${roleReveal.emoji} **${roleReveal.name}**`;

    await this.session.channel.send({
      embeds: [gameEmbed(
        '⚖️ الإعدام',
        tallyText + '\n' + resultText,
        tie || !mostVoted ? COLORS.WARN : COLORS.ERROR,
      )],
    });

    await this.end();
    await this.session.fsm.transition('process_votes');
  }

  async end() {
    this._clearTimeout();
    if (this.voteMsg) {
      try { await this.voteMsg.edit({ components: [] }); } catch { }
    }
    if (this._revoteMsg) {
      try { await this._revoteMsg.edit({ components: [] }); } catch { }
    }
    await super.end();
  }
}

module.exports = DayPhase;
