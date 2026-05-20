const logger = require('../../utils/logger');

class MemoryManager {
  constructor(options = {}) {
    this.cleanupInterval = options.cleanupInterval || 300000;
    this.sessionTimeout = options.sessionTimeout || 3600000;
    this.inactivityTimeout = options.inactivityTimeout || 600000;
    this.watchers = new Map();
    this.metrics = {
      cleanedSessions: 0,
      cleanedIntervals: 0,
      lastCleanup: null,
    };

    this._startCleanup();
  }

  watch(id, data, timeout) {
    this.watchers.set(id, {
      data,
      expiresAt: Date.now() + (timeout || this.inactivityTimeout),
      createdAt: Date.now(),
      lastAccess: Date.now(),
    });
  }

  refresh(id) {
    const entry = this.watchers.get(id);
    if (entry) {
      entry.lastAccess = Date.now();
      entry.expiresAt = Date.now() + this.inactivityTimeout;
      return entry.data;
    }
    return null;
  }

  unwatch(id) {
    return this.watchers.delete(id);
  }

  get(id) {
    const entry = this.watchers.get(id);
    if (entry) {
      entry.lastAccess = Date.now();
      return entry.data;
    }
    return null;
  }

  _startCleanup() {
    this._cleanupTimer = setInterval(() => {
      this._runCleanup();
    }, this.cleanupInterval);

    logger.success(`✅ MemoryManager: cleanup every ${this.cleanupInterval / 1000}s`);
  }

  _runCleanup() {
    const now = Date.now();
    let cleaned = 0;

    for (const [id, entry] of this.watchers) {
      if (entry.expiresAt <= now) {
        this.watchers.delete(id);
        cleaned++;

        if (entry.data && typeof entry.data.cleanup === 'function') {
          try {
            entry.data.cleanup();
          } catch (err) {
            logger.error(`❌ MemoryManager cleanup error for ${id}:`, err.message);
          }
        }
      }
    }

    if (cleaned > 0) {
      this.metrics.cleanedSessions += cleaned;
      this.metrics.lastCleanup = now;
      logger.debug(`🧹 MemoryManager: تم تنظيف ${cleaned} جلسة منتهية`);
    }
  }

  getActiveCount() {
    return this.watchers.size;
  }

  getMetrics() {
    return {
      ...this.metrics,
      activeEntries: this.watchers.size,
    };
  }

  getExpired() {
    const now = Date.now();
    const expired = [];
    for (const [id, entry] of this.watchers) {
      if (entry.expiresAt <= now) {
        expired.push(id);
      }
    }
    return expired;
  }

  stop() {
    if (this._cleanupTimer) {
      clearInterval(this._cleanupTimer);
    }

    for (const [id, entry] of this.watchers) {
      if (entry.data && typeof entry.data.cleanup === 'function') {
        try {
          entry.data.cleanup();
        } catch (err) {
          logger.error(`❌ MemoryManager final cleanup ${id}:`, err.message);
        }
      }
    }

    this.watchers.clear();
    logger.info('🧹 MemoryManager تم إيقاف التنظيف التلقائي');
  }
}

module.exports = MemoryManager;
