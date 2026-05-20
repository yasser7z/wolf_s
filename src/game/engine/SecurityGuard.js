const logger = require('../../utils/logger');

class SecurityGuard {
  /**
   * Validate that the interaction belongs to the expected user.
   */
  static validateOwnership(interaction, expectedUserId) {
    if (!interaction || !interaction.user) {
      return { valid: false, reason: 'تفاعل غير صالح' };
    }
    if (interaction.user.id !== expectedUserId) {
      return { valid: false, reason: 'هذا التفاعل ليس ملكك!' };
    }
    return { valid: true };
  }

  /**
   * Prevent processing the same interaction twice.
   */
  static preventDuplicate(interaction, processedSet) {
    if (!processedSet) return { valid: true };
    const id = interaction.id || `${interaction.user.id}:${interaction.customId}:${Date.now()}`;
    if (processedSet.has(id)) {
      return { valid: false, reason: 'تمت معالجة هذا التفاعل مسبقاً.' };
    }
    processedSet.add(id);
    return { valid: true };
  }

  /**
   * Anti-spam: check cooldown before allowing an action.
   */
  static checkAntiSpam(cooldownManager, userId, actionKey, cooldownMs = 2000) {
    if (!cooldownManager) return { allowed: true };
    return cooldownManager.consume(userId, actionKey, cooldownMs);
  }

  /**
   * Multi-click prevention: disable the component and edit the message.
   */
  static async preventDoubleClick(interaction) {
    try {
      if (interaction.isButton() && interaction.component?.disabled === false) {
        const disabledRow = interaction.message.components.map(row => {
          const newRow = { ...row };
          newRow.components = row.components.map(comp => {
            if (comp.customId === interaction.customId) {
              return { ...comp, disabled: true };
            }
            return comp;
          });
          return newRow;
        });
        await interaction.message.edit({ components: disabledRow });
      }
    } catch { /* message may already be edited */ }
  }

  /**
   * Validate session health before operations.
   */
  static validateSessionHealth(session) {
    if (!session) return { valid: false, reason: 'الجلسة غير موجودة.' };
    if (!session.fsm) return { valid: false, reason: 'حالة اللعبة تالفة (FSM مفقود).' };
    if (!session.channel) return { valid: false, reason: 'قناة الجلسة غير متاحة.' };
    if (!Array.isArray(session.players)) return { valid: false, reason: 'قائمة اللاعبين تالفة.' };
    return { valid: true };
  }

  /**
   * Create a protected collector with automatic cleanup and ownership checks.
   */
  static createProtectedCollector(message, { filter, options, ownerId, onCollect, onEnd }) {
    if (!message) return null;

    const processedIds = new Set();
    const wrappedFilter = (i) => {
      // Ownership check
      if (ownerId && i.user.id !== ownerId) {
        i.reply({ content: '❌ هذا التفاعل ليس ملكك!', ephemeral: true }).catch(() => {});
        return false;
      }
      // Duplicate prevention
      if (processedIds.has(i.id)) return false;
      processedIds.add(i.id);
      // User-provided filter
      return filter ? filter(i) : true;
    };

    const collector = message.createMessageComponentCollector({ ...options, filter: wrappedFilter });

    collector.on('collect', async (interaction) => {
      try {
        await onCollect(interaction);
      } catch (err) {
        logger.error(`❌ [Collector] ${err.message}`);
        try {
          await interaction.reply({ content: '❌ حدث خطأ.', ephemeral: true });
        } catch {}
      }
    });

    if (onEnd) {
      collector.on('end', onEnd);
    }

    return collector;
  }

  /**
   * Wrap an async handler with try-catch and error reply.
   */
  static wrapHandler(handler) {
    return async (interaction) => {
      try {
        await handler(interaction);
      } catch (err) {
        logger.error(`❌ [Handler] ${err.message}`);
        try {
          const reply = interaction.deferred
            ? interaction.editReply.bind(interaction)
            : interaction.reply.bind(interaction);
          await reply({ content: '❌ حدث خطأ غير متوقع.', ephemeral: true });
        } catch {}
      }
    };
  }

  /**
   * Middleware factory for InteractionRouter: validates owner & session.
   */
  static createInteractionMiddleware(sessionManager) {
    return async (interaction) => {
      if (!interaction) return false;

      // Check if interaction has a guild
      if (!interaction.guildId) return true; // DM interactions pass through

      // Session health check (if applicable)
      if (sessionManager) {
        const session = sessionManager.getSessionInGuild(interaction.guildId);
        if (session) {
          const health = SecurityGuard.validateSessionHealth(session);
          if (!health.valid) {
            logger.warn(`⚠️ جلسة تالفة: ${health.reason}`);
          }
        }
      }

      return true; // Allow all through (route-level checks handle specifics)
    };
  }
}

module.exports = SecurityGuard;
