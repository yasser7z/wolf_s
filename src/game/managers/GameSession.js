const GameEngine = require('../engine/GameEngine');
const SessionStore = require('./SessionStore');
const UserModel = require('../../database/models/UserModel');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');
const logger = require('../../utils/logger');

class GameSession {
  constructor({ client, channel, guild, hostId, eventBus, manager }) {
    this.id = `${channel.id}-${Date.now()}`;
    this.client = client;
    this.channel = channel;
    this.guild = guild;
    this.hostId = hostId;
    this.eventBus = eventBus;
    this.manager = manager;

    this.engine = new GameEngine(this);

    eventBus.emit('session.initialized', { sessionId: this.id });
  }

  // ─── Property Delegation to GameEngine ─────────────

  get players() { return this.engine.players; }
  set players(v) { this.engine.players = v; }
  get fsm() { return this.engine.fsm; }
  get actionQueue() { return this.engine.actionQueue; }
  get nightCount() { return this.engine.nightCount; }
  set nightCount(v) { this.engine.nightCount = v; }
  get currentPhase() { return this.engine.currentPhase; }
  set currentPhase(v) { this.engine.currentPhase = v; }
  get _nightEffects() { return this.engine._nightEffects; }
  set _nightEffects(v) { this.engine._nightEffects = v; }
  get _autoSaveTimer() { return this.engine._autoSaveTimer; }
  set _autoSaveTimer(v) { this.engine._autoSaveTimer = v; }
  get _phaseTimeouts() { return this.engine._phaseTimeouts; }
  get _discussionJokeTimer() { return this.engine._discussionJokeTimer; }
  set _discussionJokeTimer(v) { this.engine._discussionJokeTimer = v; }
  get _dayTimeout() { return this.engine._dayTimeout; }
  set _dayTimeout(v) { this.engine._dayTimeout = v; }
  get _validate() { return this.engine._validate; }

  // ─── Method Delegation ─────────────────────────────

  getAlivePlayers() { return this.engine.getAlivePlayers(); }
  getAlivePlayersByRole(name) { return this.engine.getAlivePlayersByRole(name); }
  getPlayersByTeam(team) { return this.engine.getPlayersByTeam(team); }
  checkWinCondition() { return this.engine.checkWinCondition(); }
  _evaluateWinCondition() { return this.engine._evaluateWinCondition(); }

  async startLobby() { return this.engine.startLobby(); }
  async startGame() { return this.engine.startGame(); }
  async startNight() { return this.engine.startNight(); }

  async endGame(winner) {
    await this.fsm.transition('ended');
    await this._announceWinner(winner);
    await this._updatePlayerStats(winner);
  }

  async cleanup() {
    await this.engine.cleanup();
    this.eventBus.emit('session.cleanup.completed', { sessionId: this.id });
    logger.game(`🧹 تم تنظيف الجلسة ${this.id}`);
  }

  // ─── Discord-Specific Methods ──────────────────────

  async _announceWinner(winner) {
    const emoji = winner === 'القرية' ? '👤' : '🐺';
    const playersList = this.players.map(p => {
      const status = p.alive ? '🟢 حي' : '💀 ميت';
      const roleInfo = p.role ? `${p.role.emoji} ${p.role.name}` : '❓';
      return `<@${p.id}> | ${roleInfo} | ${status}`;
    }).join('\n');

    await this.channel.send({
      embeds: [gameEmbed(
        `${emoji} انتهت اللعبة!`,
        `**الفائزون: ${winner}** 🏆\n\n**اللاعبون:**\n${playersList}`,
        winner === 'القرية' ? COLORS.SUCCESS : COLORS.ERROR
      )],
    });

    this.manager.stats.totalEnded++;
  }

  async _updatePlayerStats(winner) {
    for (const player of this.players) {
      try {
        const roleId = player.role?.id || null;
        const isVillageWinner = winner === 'القرية' && player.role && player.role.team === 'القرية';
        const isWolfWinner = winner === 'الذئاب' && player.role && player.role.team === 'الذئاب';

        if (isVillageWinner || isWolfWinner) {
          await UserModel.addWin(player.id, roleId);
        } else {
          await UserModel.addLoss(player.id, roleId);
        }
      } catch (err) {
        logger.error(`خطأ في تحديث إحصائيات ${player.username}:`, err.message);
      }
    }
  }

  // ─── Static Restore (crash recovery) ───────────────

  static async restore(data, client, manager) {
    try {
      const channel = client.channels.cache.get(data.channelId);
      if (!channel) return null;

      const session = new GameSession({
        client,
        channel,
        guild: channel.guild,
        hostId: data.hostId,
        eventBus: manager.eventBus,
        manager,
      });

      // Override engine with stored state
      session.engine.players = (data.players || []).map(sp => {
        const Player = require('../../structures/Player');
        const p = new Player(client, { id: sp.id, username: sp.username });
        p.alive = sp.alive;
        if (sp.role) {
          try {
            const Cls = require('../../game/roles/RoleRegistry').RoleRegistry.getClass(sp.role.id || sp.role.name);
            p.role = new Cls();
          } catch { p.role = null; }
        }
        return p;
      });
      session.engine.nightCount = data.nightCount || 1;

      const storedState = data.state || data.phase || 'idle';
      const validStates = ['idle', 'lobby', 'starting', 'night', 'process_night', 'day', 'voting', 'process_votes', 'check_win', 'ended'];

      if (validStates.includes(storedState) && session.fsm.states?.has(storedState)) {
        session.fsm.currentState = storedState;
        const resumePhase = await session.engine._resumePhase(storedState);
        if (resumePhase) {
          session.currentPhase = resumePhase;
        }
        session.engine._startAutoSave();
      }

      manager.stats.activeNow = manager.sessions?.size || 0;
      logger.game(`🔄 تم استعادة الجلسة ${session.id} في الحالة ${storedState}`);
      return session;
    } catch (err) {
      logger.error(`❌ فشل استعادة الجلسة ${data.id}:`, err.message);
      return null;
    }
  }
}

module.exports = GameSession;
