const { db } = require('../../database/db');
const logger = require('../../utils/logger');

class SessionStore {
  async saveGameSession(sessionId, data) {
    const key = `activeSessions.${sessionId}`;
    const snapshot = {
      id: sessionId,
      guildId: data.guildId,
      channelId: data.channelId,
      hostId: data.hostId,
      phase: data.phase,
      nightCount: data.nightCount,
      players: data.players.map(p => ({
        id: p.id,
        username: p.username,
        alive: p.alive,
        role: p.role ? { name: p.role.name, team: p.role.team } : null,
      })),
      state: data.fsm ? data.fsm.getState() : 'unknown',
      savedAt: Date.now(),
    };

    await db.set(key, snapshot);
    logger.debug(`💾 تم حفظ حالة الجلسة ${sessionId}`);
    return snapshot;
  }

  async loadGameSession(sessionId) {
    const key = `activeSessions.${sessionId}`;
    const data = await db.get(key);

    if (!data) {
      return null;
    }

    const age = Date.now() - data.savedAt;
    if (age > 3600000) {
      await this.deleteGameSession(sessionId);
      logger.warn(`🗑️ تم حذف جلسة قديمة: ${sessionId} (${Math.round(age / 60000)} دقيقة)`);
      return null;
    }

    logger.game(`📂 تم استعادة الجلسة ${sessionId} من التخزين`);
    return data;
  }

  async deleteGameSession(sessionId) {
    const key = `activeSessions.${sessionId}`;
    await db.delete(key);
    logger.debug(`🗑️ تم حذف الجلسة ${sessionId} من التخزين`);
  }

  async getAllStoredSessions() {
    const all = await db.get('activeSessions');
    if (!all) return [];
    return Object.values(all);
  }

  async cleanupStaleSessions(maxAge = 3600000) {
    const sessions = await this.getAllStoredSessions();
    const now = Date.now();
    let cleaned = 0;

    for (const session of sessions) {
      if (now - session.savedAt > maxAge) {
        await this.deleteGameSession(session.id);
        cleaned++;
      }
    }

    if (cleaned > 0) {
      logger.info(`🧹 تم تنظيف ${cleaned} جلسة منتهية من التخزين`);
    }

    return cleaned;
  }
}

module.exports = new SessionStore();
