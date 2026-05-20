const logger = require('../../utils/logger');

class CooldownManager {
  constructor(options = {}) {
    this.cooldowns = new Map();
    this.defaultCooldown = options.defaultCooldown || 3000;
    this.cleanupInterval = options.cleanupInterval || 60000;
    this.maxEntries = options.maxEntries || 10000;

    this._startCleanup();
  }

  check(userId, key, cooldownMs) {
    const mapKey = `${userId}:${key}`;
    const entry = this.cooldowns.get(mapKey);

    if (entry) {
      const remaining = entry.expiresAt - Date.now();
      if (remaining > 0) {
        return { allowed: false, remaining };
      }
    }

    return { allowed: true, remaining: 0 };
  }

  set(userId, key, cooldownMs) {
    const mapKey = `${userId}:${key}`;
    const duration = cooldownMs || this.defaultCooldown;

    this.cooldowns.set(mapKey, {
      userId,
      key,
      expiresAt: Date.now() + duration,
      createdAt: Date.now(),
    });

    if (this.cooldowns.size > this.maxEntries) {
      this._enforceMax();
    }
  }

  consume(userId, key, cooldownMs) {
    const result = this.check(userId, key, cooldownMs);
    if (result.allowed) {
      this.set(userId, key, cooldownMs);
    }
    return result;
  }

  getRemaining(userId, key) {
    const result = this.check(userId, key);
    return result.allowed ? 0 : result.remaining;
  }

  isOnCooldown(userId, key) {
    return !this.check(userId, key).allowed;
  }

  reset(userId, key) {
    const mapKey = `${userId}:${key}`;
    this.cooldowns.delete(mapKey);
  }

  resetAll(userId) {
    for (const [mapKey] of this.cooldowns) {
      if (mapKey.startsWith(`${userId}:`)) {
        this.cooldowns.delete(mapKey);
      }
    }
  }

  _startCleanup() {
    this._cleanupTimer = setInterval(() => {
      const now = Date.now();
      let cleaned = 0;

      for (const [mapKey, entry] of this.cooldowns) {
        if (entry.expiresAt <= now) {
          this.cooldowns.delete(mapKey);
          cleaned++;
        }
      }

      if (cleaned > 0) {
        logger.debug(`🧹 Cooldown cleanup: ${cleaned} entries removed`);
      }
    }, this.cleanupInterval);
  }

  _enforceMax() {
    const entries = [...this.cooldowns.entries()]
      .sort((a, b) => a[1].expiresAt - b[1].expiresAt);

    const toRemove = entries.slice(0, entries.length - this.maxEntries);
    for (const [key] of toRemove) {
      this.cooldowns.delete(key);
    }
  }

  stop() {
    if (this._cleanupTimer) {
      clearInterval(this._cleanupTimer);
    }
    this.cooldowns.clear();
  }

  stats() {
    return {
      size: this.cooldowns.size,
      maxEntries: this.maxEntries,
    };
  }
}

module.exports = CooldownManager;
