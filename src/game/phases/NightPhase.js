const {
  ActionRowBuilder,
  StringSelectMenuBuilder,
  ButtonBuilder,
  ButtonStyle,
  EmbedBuilder,
} = require('discord.js');
const BasePhase = require('./base/BasePhase');
const logger = require('../../utils/logger');

const NIGHT_TIMEOUT = 30000;
const NEON_PURPLE = 0xBB86FC;

class NightPhase extends BasePhase {
  constructor(session) {
    super(session, { name: 'night', duration: NIGHT_TIMEOUT });
    this.actions = {};
    this.submittedPlayers = new Set();
    this.publicMsg = null;
    this._countdownTimer = null;
    this._nightStartTime = Date.now();
  }

  async start() {
    this.actions = {};
    this.submittedPlayers = new Set();
    this._nightStartTime = Date.now();

    const { embed, row } = this._buildNightMessage(30);
    this.publicMsg = await this.send({ embeds: [embed], components: [row] });
    if (!this.publicMsg) return;

    this._startCountdown();
    this.setTimeout(() => this._finishNight(), NIGHT_TIMEOUT);

    logger.game(`🌙 الليل بدأ في ${this.session.guild.name}`);
  }

  // ─── Public message ──────────────────────────

  _buildNightMessage(remaining) {
    const secs = String(remaining).padStart(2, '0');
    const embed = new EmbedBuilder()
      .setColor(NEON_PURPLE)
      .setTitle('🌙 حل الليل على القرية...')
      .setDescription([
        '```ansi',
        '\u001b[1;35m╔════════════════════════╗',
        '\u001b[1;35m║    اللَّيْلُ قَدْ حَلَّ    ║',
        '\u001b[1;35m╚════════════════════════╝',
        '```',
        '',
        '> الظلام يغطي قرية فالي...',
        '> أصحاب القدرات الخاصة يستعدون...',
        '> الذئاب تتحرك بين الأزقة...',
        '',
        `⏱️ **الوقت المتبقي:** \`00:${secs}\``,
        '',
        '_اضغط على الزر أدناه لفتح لوحة التحكم الخاصة بك_\n_قم بإجراءك قبل فوات الأوان!_',
      ].join('\n'))
      .setFooter({ text: `Vale Community • ${remaining}s متبقي` })
      .setTimestamp();

    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId('night:panel')
        .setLabel('👁️ فتح لوحة التحكم الخاصة بك')
        .setStyle(ButtonStyle.Primary)
        .setEmoji('🌙'),
    );

    return { embed, row };
  }

  _startCountdown() {
    const start = Date.now();
    this._countdownTimer = setInterval(async () => {
      if (!this.session.fsm?.is('night') || !this.publicMsg) {
        clearInterval(this._countdownTimer);
        return;
      }
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, Math.ceil((NIGHT_TIMEOUT - elapsed) / 1000));
      const { embed, row } = this._buildNightMessage(remaining);
      try {
        await this.publicMsg.edit({
          embeds: [embed],
          components: remaining > 0 ? [row] : [],
        });
      } catch { }
    }, 5000);
  }

  // ─── Route Handlers (called by RouteRegistry) ──────────

  async handlePanelOpen(interaction) {
    if (!this.session.fsm?.is('night')) {
      return interaction.reply({ content: '❌ انتهى وقت الليل.', ephemeral: true });
    }

    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!player || !player.alive) {
      return interaction.reply({ content: '💀 أنت ميت.', ephemeral: true });
    }

    const ControlPanel = require('../panels/ControlPanel');
    const panel = new ControlPanel(this.session, player);
    const panelContent = panel.build();
    const role = player.role;

    if (!role) {
      return interaction.reply({ content: '❌ ليس لديك دور.', ephemeral: true });
    }

    const done = this.submittedPlayers.has(player.id);
    const hasNightAction = ['ذئب', 'محقق', 'حارس', 'طبيب', 'مغوية'].includes(role.name);

    if (done || !hasNightAction) {
      if (!done && !hasNightAction) this.submittedPlayers.add(player.id);
      return interaction.reply({ ...panelContent, ephemeral: true });
    }

    const controls = this._buildNightControls(player, role);
    if (!controls) {
      this.submittedPlayers.add(player.id);
      return interaction.reply({ ...panelContent, ephemeral: true });
    }

    await interaction.reply({ ...panelContent, components: controls, ephemeral: true });
  }

  async handleWolfKill(interaction, targetId) {
    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!this._guard(player, interaction)) return;

    this.actions.wolfKill = targetId;
    player.role.onNightAction(this.session.actionQueue, player, targetId);
    this.submittedPlayers.add(player.id);
    await interaction.reply({
      embeds: [new EmbedBuilder()
        .setColor(0xE74C3C)
        .setDescription(`🐺 **اخترت:** <@${targetId}>\n> الذئاب تتربص بضحيتها...`)
        .setFooter({ text: 'انتظر حتى الصباح' }),
      ], ephemeral: true,
    });
  }

  async handleDetectiveInspect(interaction, targetId) {
    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!this._guard(player, interaction)) return;

    const target = this.session.players.find(p => p.id === targetId);
    const isWolf = target?.role?.name === 'ذئب';
    this.actions.detectiveTarget = targetId;
    player.role.onNightAction(this.session.actionQueue, player, targetId);
    this.submittedPlayers.add(player.id);
    await interaction.reply({
      embeds: [new EmbedBuilder()
        .setColor(0x9B59B6)
        .setDescription(`🔍 **نتيجة التحقيق:** <@${targetId}> هو **${isWolf ? '🐺 ذئب!' : '👤 ليس ذئباً.'}**`)
        .setFooter({ text: 'استخدم هذه المعلومة بحكمة' }),
      ], ephemeral: true,
    });
  }

  async handleDoctorHeal(interaction, targetOrSkip) {
    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!this._guard(player, interaction)) return;

    this.actions.doctorHeal = targetOrSkip;
    player.role.onNightAction(this.session.actionQueue, player, targetOrSkip);
    this.submittedPlayers.add(player.id);
    await interaction.reply({
      embeds: [new EmbedBuilder()
        .setColor(0x2ECC71)
        .setDescription(targetOrSkip === 'skip' ? '💉 **لن تنقذ أحداً.**' : `💉 **اخترت:** <@${targetOrSkip}>`)
        .setFooter({ text: 'سيشرق الفجر قريباً' }),
      ], ephemeral: true,
    });
  }

  async handleGuardProtect(interaction, targetId) {
    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!this._guard(player, interaction)) return;

    this.actions.guardProtect = targetId;
    player.role.onNightAction(this.session.actionQueue, player, targetId);
    this.submittedPlayers.add(player.id);
    await interaction.reply({
      embeds: [new EmbedBuilder()
        .setColor(0x3498DB)
        .setDescription(`🛡️ **حميتَ:** <@${targetId}>\n> لن يصاب بأذى هذه الليلة!`)
        .setFooter({ text: 'درب الأمان' }),
      ], ephemeral: true,
    });
  }

  async handleSeductressVisit(interaction, targetId) {
    const player = this.session.players.find(p => p.id === interaction.user.id);
    if (!this._guard(player, interaction)) return;

    const target = this.session.players.find(p => p.id === targetId);
    const isWolf = target?.role?.name === 'ذئب';
    this.actions.seductressTarget = targetId;
    player.role.onNightAction(this.session.actionQueue, player, targetId);
    this.submittedPlayers.add(player.id);

    const msg = isWolf
      ? '💃 **اكتشفتِ أنه ذئب!** ستموتان معاً هذه الليلة...'
      : `💃 **زرتِ:** <@${targetId}>`;
    await interaction.reply({
      embeds: [new EmbedBuilder()
        .setColor(0xE91E63)
        .setDescription(msg)
        .setFooter({ text: 'ليلة خطيرة' }),
      ], ephemeral: true,
    });
  }

  // ─── Controls builder ─────────────────────────

  _buildNightControls(player, role) {
    const rows = [];
    const alive = this.session.getAlivePlayers();
    const roleName = role.name;

    const makeSelect = (prefix, placeholder, options) =>
      new ActionRowBuilder().addComponents(
        new StringSelectMenuBuilder()
          .setCustomId(`${prefix}:${player.id}`)
          .setPlaceholder(placeholder)
          .addOptions(options),
      );

    switch (roleName) {
      case 'ذئب': {
        const targets = alive.filter(p => p.id !== player.id);
        if (targets.length === 0) return null;
        return [makeSelect('night:wolf:kill', '🐺 اختر ضحية...', targets.map(t => ({
          label: t.username, value: t.id, emoji: '🎯',
        })))];
      }
      case 'محقق': {
        if (role.uses >= role.maxUses) return null;
        const targets = alive.filter(p => p.id !== player.id);
        if (targets.length === 0) return null;
        return [makeSelect('night:detective:inspect', '🔍 اختر لاعباً...', targets.map(t => ({
          label: t.username, value: t.id, emoji: '🔍',
        })))];
      }
      case 'طبيب': {
        return [makeSelect('night:doctor:heal', '💉 اختر من تنقذ...', [
          { label: '⏭️ تخطي', value: 'skip', emoji: '⏭️' },
          ...alive.map(t => ({ label: t.username, value: t.id, emoji: '💊' })),
        ])];
      }
      case 'حارس': {
        if (role.uses >= role.maxUses) return null;
        const targets = alive.filter(p => p.id !== player.id);
        if (targets.length === 0) return null;
        return [makeSelect('night:guard:protect', '🛡️ اختر من تحمي...', targets.map(t => ({
          label: t.username, value: t.id, emoji: '🛡️',
        })))];
      }
      case 'مغوية': {
        const targets = alive.filter(p => p.id !== player.id);
        if (targets.length === 0) return null;
        return [makeSelect('night:seductress:visit', '💃 اختر من تزورين...', targets.map(t => ({
          label: t.username, value: t.id, emoji: '💃',
        })))];
      }
      default:
        return null;
    }
  }

  // ─── Auto-resolve ────────────────────────────

  _autoResolve(player, role) {
    if (this.submittedPlayers.has(player.id)) return;
    this.submittedPlayers.add(player.id);
    if (role.name === 'ذئب') {
      const targets = this.session.getAlivePlayers().filter(p => p.id !== player.id);
      if (targets.length > 0) {
        const random = targets[Math.floor(Math.random() * targets.length)];
        this.actions.wolfKill = random.id;
        role.onNightAction(this.session.actionQueue, player, random.id);
      }
    }
  }

  // ─── Guard ────────────────────────────────────

  _guard(player, interaction) {
    if (!this.session.fsm?.is('night') || !player || !player.alive) {
      interaction.reply({ content: '❌ لا يمكنك القيام بهذا الإجراء.', ephemeral: true }).catch(() => {});
      return false;
    }
    return true;
  }

  // ─── Finish ──────────────────────────────────

  async _finishNight() {
    // Auto-resolve any unsubmitted players with night actions
    this.session.players.forEach(p => {
      if (p.alive && p.role && ['ذئب', 'محقق', 'حارس', 'طبيب', 'مغوية'].includes(p.role.name)) {
        this._autoResolve(p, p.role);
      }
    });

    if (this.publicMsg) {
      try { await this.publicMsg.edit({ components: [] }); } catch { }
    }
    this.session.eventBus.emit('night.resolved', { actions: this.actions });
    await this.end();
    await this.session.fsm.transition('process_night');
  }

  async end() {
    if (this._countdownTimer) {
      clearInterval(this._countdownTimer);
      this._countdownTimer = null;
    }
    this._clearTimeout();
    if (this.publicMsg) {
      try { await this.publicMsg.edit({ components: [] }); } catch { }
    }
    await super.end();
  }
}

module.exports = NightPhase;
