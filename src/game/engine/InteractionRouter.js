const logger = require('../../utils/logger');

class InteractionRouter {
  constructor(eventBus) {
    this.eventBus = eventBus;
    this.routes = new Map();
    this.globalMiddleware = [];
    this.cooldowns = new Map();
  }

  register(route, handler, options = {}) {
    const entry = {
      route,
      handler,
      cooldown: options.cooldown || 0,
      requiredRole: options.requiredRole || null,
      validate: options.validate || null,
    };

    if (!this.routes.has(route)) {
      this.routes.set(route, []);
    }
    this.routes.get(route).push(entry);

    logger.info(`🔀 تم تسجيل مسار: ${route}`);
  }

  use(middleware) {
    this.globalMiddleware.push(middleware);
  }

  async resolve(interaction) {
    const customId = interaction.customId || '';
    const start = Date.now();

    for (const mw of this.globalMiddleware) {
      try {
        const result = await mw(interaction);
        if (result === false) return;
      } catch (err) {
        logger.error(`❌ Global middleware error:`, err.message);
        return;
      }
    }

    const matchedRoutes = this._matchRoute(customId);

    for (const entry of matchedRoutes) {
      if (entry.cooldown > 0) {
        const remaining = this._checkCooldown(interaction.user.id, entry.route);
        if (remaining > 0) {
          try {
            await interaction.reply({
              content: `⏳ انتظر ${Math.ceil(remaining / 1000)} ثانية قبل استخدام هذا الزر.`,
              ephemeral: true,
            });
          } catch { }
          return;
        }
      }

      if (entry.validate) {
        const valid = await entry.validate(interaction);
        if (!valid) continue;
      }

      try {
        await entry.handler(interaction);
        this._setCooldown(interaction.user.id, entry.route, entry.cooldown);

        const duration = Date.now() - start;
        this.eventBus.emit('interaction.processed', {
          userId: interaction.user.id,
          route: entry.route,
          duration,
        });
      } catch (err) {
        logger.error(`❌ Interaction route ${entry.route}:`, err.message);
        try {
          await interaction.reply({
            content: '❌ حدث خطأ أثناء معالجة التفاعل.',
            ephemeral: true,
          });
        } catch { }
      }

      return;
    }
  }

  _matchRoute(customId) {
    for (const [route] of this.routes) {
      if (customId.startsWith(route) || customId === route) {
        return this.routes.get(route);
      }
    }
    return [];
  }

  _checkCooldown(userId, route) {
    const key = `${userId}:${route}`;
    const expiry = this.cooldowns.get(key);
    if (!expiry) return 0;
    return Math.max(0, expiry - Date.now());
  }

  _setCooldown(userId, route, ms) {
    if (ms <= 0) return;
    const key = `${userId}:${route}`;
    this.cooldowns.set(key, Date.now() + ms);
  }

  cleanup() {
    const now = Date.now();
    for (const [key, expiry] of this.cooldowns) {
      if (expiry <= now) this.cooldowns.delete(key);
    }
  }
}

module.exports = InteractionRouter;
