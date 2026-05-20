const {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  EmbedBuilder,
} = require('discord.js');
const BasePhase = require('./base/BasePhase');
const LobbyPanel = require('../panels/LobbyPanel');
const logger = require('../../utils/logger');

const MIN_PLAYERS = 6;
const MAX_PLAYERS = 16;
const LOBBY_TIMEOUT = 60000;
const COUNTDOWN_INTERVAL = 5000;

class LobbyPhase extends BasePhase {
  constructor(session) {
    super(session, { name: 'lobby', duration: LOBBY_TIMEOUT });
    this.lobbyMessage = null;
    this.players = session.players;
    this.startedAt = Date.now();
    this.countdownTimer = null;
    this._isEnding = false;
  }

  async start() {
    this.startedAt = Date.now();
    this._isEnding = false;

    this.lobbyMessage = await this.send({
      ...LobbyPanel.buildEmbed(this.players, MAX_PLAYERS, MIN_PLAYERS, this.startedAt, this.session.fsm?.getState()),
      components: [this._buildRow()],
    });

    if (!this.lobbyMessage) {
      logger.error('❌ فشل إنشاء رسالة الصالة');
      return;
    }

    // No collector — interactions handled by RouteRegistry/router
    this.setTimeout(async () => {
      await this._onTimeout();
    }, LOBBY_TIMEOUT);

    this._startCountdown();
    logger.game(`🎮 فتحت صالة انتظار في ${this.session.guild.name}`);
  }

  async _onTimeout() {
    this._stopCountdown();
    if (!this._isEnding && this.session.fsm?.is('lobby') && this.players.length < MIN_PLAYERS) {
      await this.send({
        embeds: [
          new EmbedBuilder()
            .setColor(0xE74C3C)
            .setTitle('⏰ انتهى الوقت')
            .setDescription('> عدد اللاعبين غير كافٍ لبدء اللعبة.\n> استخدم `-ذيب` لفتح صالة جديدة.')
            .setFooter({ text: 'Vale Community' })
            .setTimestamp(),
        ],
      });
      await this.session.fsm.transition('idle');
    }
  }

  // ─── Route Handlers (called by RouteRegistry) ──────────

  async _handleJoin(interaction) {
    if (!this.session.fsm?.is('lobby')) {
      return this.reply(interaction, { content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const existing = this.players.find(p => p.id === interaction.user.id);
    if (existing) {
      return this.reply(interaction, { content: '❌ أنت بالفعل منضم!', ephemeral: true });
    }
    if (this.players.length >= MAX_PLAYERS) {
      return this.reply(interaction, { content: '❌ الصالة ممتلئة!', ephemeral: true });
    }

    this.players.push({
      id: interaction.user.id,
      username: interaction.user.username,
      alive: true,
      role: null,
      votedFor: null,
      hostId: this.session.hostId,
    });

    this.session.eventBus.emit('player.joined', {
      userId: interaction.user.id,
      username: interaction.user.username,
      playerCount: this.players.length,
      sessionId: this.session.id,
    });

    await this._updateMessage();
    await this.reply(interaction, { content: '✅ **انضممت إلى اللعبة!** 🐺', ephemeral: true });
  }

  async _handleLeave(interaction) {
    if (!this.session.fsm?.is('lobby')) {
      return this.reply(interaction, { content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const idx = this.players.findIndex(p => p.id === interaction.user.id);
    if (idx === -1) {
      return this.reply(interaction, { content: '❌ أنت لست منضماً!', ephemeral: true });
    }

    this.players.splice(idx, 1);
    this.session.eventBus.emit('player.left', { userId: interaction.user.id, playerCount: this.players.length });
    await this._updateMessage();
    await this.reply(interaction, { content: '✅ **غادرت اللعبة.**', ephemeral: true });
  }

  async _handleStart(interaction) {
    if (!this.session.fsm?.is('lobby')) {
      return this.reply(interaction, { content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    if (interaction.user.id !== this.session.hostId) {
      return this.reply(interaction, { content: '❌ فقط منشئ اللعبة يمكنه بدؤها!', ephemeral: true });
    }
    if (this.players.length < MIN_PLAYERS) {
      return this.reply(interaction, { content: `❌ يجب أن يكون على الأقل ${MIN_PLAYERS} لاعبين!`, ephemeral: true });
    }

    this._isEnding = true;
    this._stopCountdown();
    await this.reply(interaction, { content: '🎮 **جاري بدء اللعبة...**', ephemeral: true });
    this._clearTimeout();
    await this._updateMessage();
    await this.session.startGame();
  }

  async _handleExplain(interaction) {
    if (!this.session.fsm?.is('lobby')) {
      return this.reply(interaction, { content: '❌ انتهت صلاحية هذا التفاعل.', ephemeral: true });
    }
    const explanation = LobbyPanel.buildExplanation();
    await interaction.reply(explanation);
  }

  // ─── Internal ────────────────────────────────

  _startCountdown() {
    this.countdownTimer = setInterval(async () => {
      if (this._isEnding || !this.lobbyMessage) { this._stopCountdown(); return; }
      const elapsed = Date.now() - this.startedAt;
      if (elapsed >= LOBBY_TIMEOUT) { this._stopCountdown(); return; }
      await this._updateMessage();
    }, COUNTDOWN_INTERVAL);
  }

  _stopCountdown() {
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null; }
  }

  async _updateMessage() {
    if (!this.lobbyMessage || this._isEnding) return;
    try {
      await this.lobbyMessage.edit({
        ...LobbyPanel.buildEmbed(this.players, MAX_PLAYERS, MIN_PLAYERS, this.startedAt, this.session.fsm?.getState()),
        components: [this._buildRow()],
      });
    } catch { }
  }

  _buildRow() {
    const isHost = (uid) => uid === this.session.hostId;
    const canStart = this.players.length >= MIN_PLAYERS;

    return new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId('lobby:join')
        .setLabel(canStart && isHost ? '▶️ ابدأ اللعبة' : '🎮 العب')
        .setStyle(canStart && isHost ? ButtonStyle.Success : ButtonStyle.Primary),
      new ButtonBuilder()
        .setCustomId('lobby:leave')
        .setLabel('❌ اخرج')
        .setStyle(ButtonStyle.Danger),
      new ButtonBuilder()
        .setCustomId('lobby:explain')
        .setLabel('📖 شرح اللعبة')
        .setStyle(ButtonStyle.Secondary),
    );
  }

  async end() {
    this._isEnding = true;
    this._stopCountdown();
    this._clearTimeout();
    if (this.lobbyMessage) {
      try { await this.lobbyMessage.edit({ components: [] }); } catch { }
    }
    await super.end();
  }
}

module.exports = LobbyPhase;
