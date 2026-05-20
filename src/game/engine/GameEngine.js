const FSM = require('./FSM');
const ActionQueue = require('../queue/ActionQueue');
const Validator = require('./Validator');
const logger = require('../../utils/logger');
const { RoleRegistry } = require('../roles/RoleRegistry');

const STATES = ['idle', 'lobby', 'starting', 'night', 'process_night', 'day', 'voting', 'process_votes', 'check_win', 'ended'];
const TRANSITIONS = [
  ['idle', 'lobby'], ['lobby', 'idle'], ['lobby', 'starting'],
  ['starting', 'night'], ['night', 'process_night'], ['process_night', 'day'],
  ['process_night', 'check_win'], ['day', 'voting'], ['voting', 'process_votes'],
  ['process_votes', 'check_win'], ['check_win', 'night'], ['check_win', 'ended'], ['ended', 'idle'],
];
const MIN_PLAYERS = 6;
const AUTO_SAVE_INTERVAL = 5000;

class GameEngine {
  constructor(session) {
    this.session = session;
    this.id = session.id;
    this.players = [];
    this.nightCount = 0;
    this.currentPhase = null;

    this.fsm = new FSM(this, STATES, TRANSITIONS, 'idle');
    this.actionQueue = new ActionQueue(this.id);
    this._validate = new Validator();

    this._autoSaveTimer = null;
    this._phaseTimeouts = [];
    this._discussionJokeTimer = null;
    this._dayTimeout = null;
    this._nightEffects = {};

    this._registerFSMListeners();
    this._registerActionHandlers();
  }

  // ─── Forwarding properties to GameSession ───────

  get channel() { return this.session.channel; }
  get client() { return this.session.client; }
  get hostId() { return this.session.hostId; }
  get eventBus() { return this.session.eventBus; }
  get guild() { return this.session.guild; }
  get manager() { return this.session.manager; }

  // ─── Lazy requires (avoid circular deps) ─────────

  _req(mod) { return require(mod); }

  // ─── FSM Listener Registration ────────────────────

  _registerFSMListeners() {
    const states = ['lobby', 'starting', 'night', 'process_night', 'day', 'voting', 'process_votes', 'check_win', 'ended', 'idle'];
    states.forEach(s => this.fsm.on(`enter:${s}`, () => this[`_onEnter${s.charAt(0).toUpperCase() + s.slice(1)}`]()));
  }

  _registerActionHandlers() {
    const handlers = {
      GUARD_PROTECT: (a) => { this._nightEffects.protected = a.targetId; },
      DOCTOR_HEAL: (a) => { this._nightEffects.healed = a.targetId; },
      SEDUCTRESS_VISIT: (a) => {
        const target = this.players.find(p => p.id === a.targetId);
        if (!target) return;
        target.role?.name === 'ذئب'
          ? (this._nightEffects.seductressWolfDeath = { seductressId: a.playerId, wolfId: a.targetId })
          : (this._nightEffects.seductressVisit = a.targetId);
      },
      WEREWOLF_KILL: (a) => { this._nightEffects.wolfTarget = a.targetId; },
      SPECIAL_DEATH: (a) => {
        this._nightEffects.specialDeaths = this._nightEffects.specialDeaths || [];
        this._nightEffects.specialDeaths.push(a.targetId);
      },
      UMMZAKI_REVEAL: (a) => {
        const target = this.players.find(p => p.id === a.targetId);
        if (target?.alive && target.role?.id === 'UmmZaki' && this._nightEffects.wolfTarget === target.id) {
          const revealed = target.role.getRevealedWolf();
          if (revealed) this._nightEffects.umZakiRevealed = revealed;
        }
      },
      VOTE: (a) => { this.session.eventBus.emit('vote.cast', { voterId: a.playerId, targetId: a.targetId }); },
      DETECTIVE_INVESTIGATE: (a) => {
        const target = this.players.find(p => p.id === a.targetId);
        if (target?.role) {
          const isWolf = target.role.name === 'ذئب';
          this.session.eventBus.emit('detective.result', { playerId: a.playerId, targetId: a.targetId, isWolf });
        }
      },
      KING_EXECUTE: (a) => {
        const target = this.players.find(p => p.id === a.targetId);
        if (target?.alive) { target.alive = false; this.session.eventBus.emit('player.killed', { playerId: target.id, killerId: a.playerId, reason: 'تنفيذ' }); }
      },
    };
    Object.entries(handlers).forEach(([type, fn]) => this.actionQueue.setHandler(type, fn));
  }

  // ─── Phase Enter Handlers ──────────────────────────

  async _onEnterLobby() {
    const LobbyPhase = this._req('../phases/LobbyPhase');
    this.currentPhase = new LobbyPhase(this);
    await this.currentPhase.start();
    this._startAutoSave();
  }

  async _onEnterStarting() {
    const { shuffle, sleep } = this._req('../../utils/helpers');
    const { gameEmbed, COLORS } = this._req('../../utils/embedBuilder');

    const distribution = this._getRoleDistribution();
    if (!distribution) {
      await this.session.channel.send('❌ عدد اللاعبين غير مناسب.');
      this.fsm.transition('idle');
      return;
    }

    await this.session.channel.send({
      embeds: [gameEmbed('📜 توزيع الأدوار', 'يتم الآن توزيع الأدوار...\n\n_تحقق من رسائلك الخاصة!_', COLORS.PRIMARY)],
    });

    const shuffled = shuffle(distribution);
    for (let i = 0; i < this.players.length; i++) {
      const Cls = RoleRegistry.getClass(shuffled[i]);
      this.players[i].role = new Cls();
      try {
        const dm = await this.session.client.users.createDM(this.players[i].id);
        const info = this.players[i].role.getInfo();
        await dm.send({
          embeds: [gameEmbed(
            `${info.emoji} دورك: ${info.name}`,
            `**الفريق:** ${info.team}\n**قدرتك:** ${info.description}\n\n_تعاون مع فريقك!_`,
            COLORS.NIGHT
          ).setFooter({ text: 'قرية فالي تراقبك...' })],
        });
      } catch { }
    }

    await sleep(3000);
    this.fsm.transition('night');
  }

  async _onEnterNight() {
    this.nightCount++;
    this.actionQueue.clear();
    const NightPhase = this._req('../phases/NightPhase');
    this.currentPhase = new NightPhase(this);
    await this.currentPhase.start();
  }

  async _onEnterProcessNight() {
    if (!this.currentPhase) { await this.fsm.transition('check_win'); return; }
    this._nightEffects = {};
    await this.actionQueue.processNext();
    const killed = await this._processDeaths();
    this.session.eventBus.emit('night.processed', { killed: killed?.id });

    const { gameEmbed, COLORS } = this._req('../../utils/embedBuilder');
    const DayNarrator = this._req('../narrators/DayNarrator');
    let text = '🌅 **الفجر يشرق على قرية فالي...**\n\n';
    if (killed) {
      text += `💀 **لقد وجدتم جثة <@${killed.id}> هذا الصباح!**\n`;
      if (killed.role) text += `📜 **دوره كان:** ${killed.role.emoji} **${killed.role.name}**\n`;
    } else {
      text += `✅ **${DayNarrator.noDeath()}**\n`;
    }
    text += '\n_استعدوا للمناقشة!_';
    await this.session.channel.send({ embeds: [gameEmbed('☀️ الفجر', text, COLORS.DAY)] });
    await this.fsm.transition('check_win');
  }

  async _processDeaths() {
    const fx = this._nightEffects || {};
    let killedPlayer = null;

    if (fx.seductressWolfDeath) {
      const wolf = this.players.find(p => p.id === fx.seductressWolfDeath.wolfId);
      const sed = this.players.find(p => p.id === fx.seductressWolfDeath.seductressId);
      if (wolf) { wolf.alive = false; killedPlayer = wolf; }
      if (sed) sed.alive = false;
    }

    if (fx.wolfTarget) {
      const immune = fx.protected === fx.wolfTarget || fx.healed === fx.wolfTarget || fx.seductressVisit === fx.wolfTarget;
      if (!immune) {
        killedPlayer = this.players.find(p => p.id === fx.wolfTarget);
        if (killedPlayer) {
          killedPlayer.alive = false;
          if (killedPlayer.role?.id === 'UmmZaki') {
            const revealed = killedPlayer.role.getRevealedWolf();
            if (revealed) {
              const { gameEmbed } = this._req('../../utils/embedBuilder');
              await this.session.channel.send({
                embeds: [gameEmbed('👵 أم زكي', `قبل أن تفارق الحياة، كشفت <@${killedPlayer.id}> هوية **أحد الذئاب**: <@${revealed}>!`, 0xFF4444)],
              });
            }
          }
        }
      }
    }

    if (fx.specialDeaths) {
      fx.specialDeaths.forEach(pid => {
        const p = this.players.find(pl => pl.id === pid);
        if (p?.alive) p.alive = false;
      });
    }

    return killedPlayer;
  }

  async _onEnterDay() {
    const { gameEmbed, COLORS } = this._req('../../utils/embedBuilder');
    const DayNarrator = this._req('../narrators/DayNarrator');
    const alive = this.getAlivePlayers();

    const list = alive.map((p, i) => `\`#${String(i + 1).padStart(2, '0')}\` <@${p.id}>`).join('\n');
    const text = `${DayNarrator.dayStart(alive.length)}\n\n👥 **الأحياء (${alive.length}/${this.players.length}):**\n${list}`;
    await this.session.channel.send({
      embeds: [gameEmbed('☀️ النهار', text, COLORS.DAY).setFooter({ text: `Vale Community • اليوم ${this.nightCount}` })],
    });

    this._discussionJokeTimer = setTimeout(async () => {
      if (!this.fsm?.is('day')) return;
      await this.session.channel.send(`> 💬 _${DayNarrator.discussion()}_`);
    }, 10000);

    this._dayTimeout = setTimeout(async () => {
      if (!this.fsm?.is('day')) return;
      await this.session.channel.send({
        embeds: [gameEmbed('🗳️ حان وقت التصويت!', DayNarrator.voteStart(), COLORS.WARN)],
      });
      await this.fsm.transition('voting');
    }, 45000);
  }

  async _onEnterVoting() {
    const DayPhase = this._req('../phases/DayPhase');
    this.currentPhase = new DayPhase(this);
    await this.currentPhase.startVoting();
  }

  async _onEnterProcessVotes() {
    await this.fsm.transition('check_win');
  }

  async _onEnterCheckWin() {
    const winner = this._evaluateWinCondition();
    if (winner) {
      await this.session.endGame(winner);
    } else {
      await this.startNight();
    }
  }

  async _onEnterEnded() {
    this._stopAutoSave();
    const SessionStore = this._req('../managers/SessionStore');
    await SessionStore.deleteGameSession(this.id);
    this.actionQueue.clear();
  }

  async _onEnterIdle() {
    await this.cleanup();
  }

  // ─── Lifecycle ──────────────────────────────────────

  async startLobby() {
    const v = this._validate.validatePhaseTransition(this, 'lobby');
    if (!v.valid) return false;
    await this.fsm.transition('lobby');
    return true;
  }

  async startGame() {
    const v = this._validate.validatePhaseTransition(this, 'starting');
    if (!v.valid) return false;
    await this.fsm.transition('starting');
    return true;
  }

  async startNight() {
    const v = this._validate.validatePhaseTransition(this, 'night');
    if (!v.valid) return false;
    this.session.eventBus.emit('phase.night', { sessionId: this.id, nightCount: this.nightCount });
    await this.fsm.transition('night');
    return true;
  }

  getAlivePlayers() { return this.players.filter(p => p.alive); }

  getAlivePlayersByRole(name) {
    return this.players.filter(p => p.alive && p.role && p.role.constructor.name === name);
  }

  getPlayersByTeam(team) {
    return this.players.filter(p => p.role && p.role.team === team);
  }

  _evaluateWinCondition() {
    const VictoryChecker = this._req('../victory/VictoryChecker');
    const r = new VictoryChecker(this).check();
    return r ? r.winner : null;
  }

  checkWinCondition() {
    const w = this._evaluateWinCondition();
    if (w) { this.session.endGame(w); return true; }
    return false;
  }

  _getRoleDistribution() {
    const count = this.players.length;
    if (count < MIN_PLAYERS) return null;
    const { DISTRIBUTION_POOLS } = this._req('../../config/roles');
    if (DISTRIBUTION_POOLS[count]) return [...DISTRIBUTION_POOLS[count]];
    if (count > 16) {
      const base = ['Villager', 'Villager', 'Villager', 'Doctor', 'Detective', 'Guard', 'Mayor', 'Seductress'];
      const wolves = ['Werewolf', 'Werewolf', 'Werewolf'];
      let rem = count - base.length - wolves.length;
      while (rem > 0) { base.push('Villager'); rem--; }
      return [...base, ...wolves];
    }
    return null;
  }

  // ─── Auto-Save ──────────────────────────────────────

  _startAutoSave() {
    if (this._autoSaveTimer) return;
    const SessionStore = this._req('../managers/SessionStore');
    this._autoSaveTimer = setInterval(async () => {
      try {
        await SessionStore.saveGameSession(this.id, {
          id: this.id,
          guildId: this.session.guild?.id,
          channelId: this.session.channel?.id,
          hostId: this.session.hostId,
          phase: this.fsm?.getState(),
          nightCount: this.nightCount,
          players: this.players,
          fsm: this.fsm,
        });
      } catch (err) { logger.error('❌ فشل الحفظ التلقائي:', err.message); }
    }, AUTO_SAVE_INTERVAL);
  }

  _stopAutoSave() {
    if (this._autoSaveTimer) { clearInterval(this._autoSaveTimer); this._autoSaveTimer = null; }
  }

  // ─── Cleanup ────────────────────────────────────────

  async cleanup() {
    this._stopAutoSave();
    this.actionQueue.clear();
    this._phaseTimeouts.forEach(t => clearTimeout(t));
    this._phaseTimeouts = [];
    if (this._discussionJokeTimer) clearTimeout(this._discussionJokeTimer);
    if (this._dayTimeout) clearTimeout(this._dayTimeout);
    if (this.fsm) this.fsm.removeAllListeners();
    this.currentPhase = null;
    this.players = [];
    this.session.eventBus.emit('session.cleanup.completed', { sessionId: this.id });
  }

  async _resumePhase(state) {
    try {
      if (state === 'night') {
        const NightPhase = this._req('../phases/NightPhase');
        const p = new NightPhase(this);
        p._nightStartTime = Date.now(); p.actions = {}; p.submittedPlayers = new Set();
        return p;
      }
      if (state === 'day' || state === 'voting') {
        const DayPhase = this._req('../phases/DayPhase');
        const p = new DayPhase(this);
        p.votes = {};
        return p;
      }
      return null;
    } catch (err) { logger.error(`❌ فشل استعادة الطور ${state}:`, err.message); return null; }
  }
}

module.exports = GameEngine;
