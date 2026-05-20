const { Collection } = require('discord.js');
const GameSession = require('./GameSession');
const SessionStore = require('./SessionStore');
const EventBus = require('../engine/EventBus');
const MemoryManager = require('../systems/MemoryManager');
const logger = require('../../utils/logger');

class SessionManager {
  constructor(client) {
    this.client = client;
    this.sessions = new Collection();
    this.eventBus = new EventBus();
    this.memory = new MemoryManager();
    this.stats = {
      totalCreated: 0,
      totalEnded: 0,
      activeNow: 0,
    };

    this._registerSystemListeners();
  }

  createSession(channelId, guildId, hostId) {
    if (this.sessions.has(channelId)) {
      return null;
    }

    const channel = this.client.channels.cache.get(channelId);
    if (!channel) return null;

    const session = new GameSession({
      client: this.client,
      channel,
      guild: channel.guild,
      hostId,
      eventBus: this.eventBus,
      manager: this,
    });

    this.sessions.set(channelId, session);
    this.stats.totalCreated++;
    this.stats.activeNow = this.sessions.size;

    this.memory.watch(channelId, session, 3600000);

    this.eventBus.emit('session.created', {
      channelId,
      guildId,
      hostId,
      sessionId: session.id,
    });

    logger.game(`🏠 تم إنشاء جلسة جديدة في ${channel.guild.name}#${channel.name}`);
    return session;
  }

  getSession(channelId) {
    const session = this.sessions.get(channelId);
    if (session) {
      this.memory.refresh(channelId);
    }
    return session;
  }

  getSessionById(sessionId) {
    for (const [, session] of this.sessions) {
      if (session.id === sessionId) return session;
    }
    return null;
  }

  async endSession(channelId) {
    const session = this.sessions.get(channelId);
    if (!session) return false;

    await session.cleanup();
    this.sessions.delete(channelId);
    this.memory.unwatch(channelId);
    this.stats.totalEnded++;
    this.stats.activeNow = this.sessions.size;

    await SessionStore.deleteGameSession(session.id);

    this.eventBus.emit('session.ended', { channelId, sessionId: session.id });
    logger.game(`🏁 تم إنهاء الجلسة في ${channelId}`);
    return true;
  }

  hasSession(channelId) {
    return this.sessions.has(channelId);
  }

  hasSessionInGuild(guildId) {
    for (const [, session] of this.sessions) {
      if (session.guild?.id === guildId) return true;
    }
    return false;
  }

  getSessionInGuild(guildId) {
    for (const [, session] of this.sessions) {
      if (session.guild?.id === guildId) return session;
    }
    return null;
  }

  async endGuildSessions(guildId) {
    const toEnd = [];
    for (const [channelId, session] of this.sessions) {
      if (session.guild?.id === guildId) {
        toEnd.push(channelId);
      }
    }
    for (const channelId of toEnd) {
      await this.endSession(channelId);
    }
    return toEnd.length;
  }

  async recoverSessions() {
    const stored = await SessionStore.getAllStoredSessions();
    let recovered = 0;

    for (const data of stored) {
      const channel = this.client.channels.cache.get(data.channelId);
      if (!channel) {
        await SessionStore.deleteGameSession(data.id);
        continue;
      }

      // Restore the session from stored snapshot
      const session = await GameSession.restore(data, this.client, this);
      if (session) {
        this.sessions.set(data.channelId, session);
        this.stats.totalCreated++;
        this.stats.activeNow = this.sessions.size;

        this.memory.watch(data.channelId, session, 3600000);
        this.eventBus.emit('session.recovered', { sessionId: session.id, channelId: data.channelId });
        recovered++;

        // Notify channel that the game is restored
        try {
          await channel.send('🔄 **تم استعادة الجلسة بعد إعادة التشغيل!**\n_اللعبة مستمرة من حيث توقفت._');
        } catch {}
      } else {
        await SessionStore.deleteGameSession(data.id);
      }
    }

    if (recovered > 0) {
      logger.success(`✅ تم استعادة ${recovered} جلسة بنجاح`);
    }
    logger.info(`📋 تم فحص ${stored.length} جلسة مخزنة`);
    return recovered;
  }

  getStats() {
    return {
      ...this.stats,
      memoryStats: this.memory.getMetrics(),
    };
  }

  listSessions() {
    return this.sessions.map(s => ({
      id: s.id,
      channelId: s.channel.id,
      guildName: s.guild?.name,
      phase: s.fsm?.getState(),
      players: s.players.length,
      alive: s.getAlivePlayers().length,
    }));
  }

  _registerSystemListeners() {
    this.eventBus.on('session.cleanup', async (data) => {
      if (data.channelId) {
        await this.endSession(data.channelId);
      }
    });

    this.eventBus.on('error', (data) => {
      logger.error(`❌ [SessionManager] ${data.message}`);
    });
  }

  cleanup() {
    for (const [channelId] of this.sessions) {
      this.endSession(channelId);
    }
    this.memory.stop();
    logger.info('🧹 تم تنظيف جميع الجلسات');
  }
}

module.exports = SessionManager;
