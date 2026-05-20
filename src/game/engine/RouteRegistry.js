const CustomIdParser = require('./CustomIdParser');
const SecurityGuard = require('./SecurityGuard');
const logger = require('../../utils/logger');

/**
 * Central route registry. All component interactions go through here.
 * Phase classes no longer create collectors.
 */
class RouteRegistry {
  /**
   * Register all routes on the interaction router.
   */
  static register(router, sessionManager) {
    const h = (handler) => RouteRegistry._wrap(sessionManager, handler);

    // ── LOBBY ──────────────────────────────────
    router.register('lobby:join', h((i, s) => s?.currentPhase?._handleJoin?.(i)));
    router.register('lobby:leave', h((i, s) => s?.currentPhase?._handleLeave?.(i)));
    router.register('lobby:start', h((i, s) => s?.currentPhase?._handleStart?.(i)));
    router.register('lobby:explain', h((i, s) => s?.currentPhase?._handleExplain?.(i)));

    // ── NIGHT PANEL ────────────────────────────
    router.register('night:panel', h(async (i, s) => {
      await s?.currentPhase?.handlePanelOpen?.(i);
    }));

    // ── NIGHT ACTIONS ──────────────────────────
    // All night action selects: the targetId is in interaction.values[0]
    router.register('night:wolf:kill', h(async (i, s) => {
      await s?.currentPhase?.handleWolfKill?.(i, i.values?.[0]);
    }));
    router.register('night:detective:inspect', h(async (i, s) => {
      await s?.currentPhase?.handleDetectiveInspect?.(i, i.values?.[0]);
    }));
    router.register('night:doctor:heal', h(async (i, s) => {
      await s?.currentPhase?.handleDoctorHeal?.(i, i.values?.[0]);
    }));
    router.register('night:guard:protect', h(async (i, s) => {
      await s?.currentPhase?.handleGuardProtect?.(i, i.values?.[0]);
    }));
    router.register('night:seductress:visit', h(async (i, s) => {
      await s?.currentPhase?.handleSeductressVisit?.(i, i.values?.[0]);
    }));

    // ── VOTE ───────────────────────────────────
    router.register('vote:menu', h(async (i, s) => {
      // Button click → open ephemeral menu
      if (i.isButton()) await s?.currentPhase?.handleVoteMenu?.(i);
      // Select menu submission → cast vote
      else if (i.isStringSelectMenu()) await s?.currentPhase?.handleVoteCast?.(i, i.values?.[0]);
    }));
    router.register('vote:revote:menu', h(async (i, s) => {
      if (i.isButton()) await s?.currentPhase?.handleRevoteMenu?.(i);
      else if (i.isStringSelectMenu()) await s?.currentPhase?.handleRevoteCast?.(i, i.values?.[0]);
    }));

    // ── KING ───────────────────────────────────
    router.register('king:execute:menu', h(async (i, s) => {
      if (i.isButton()) await s?.currentPhase?.handleKingMenu?.(i);
      else if (i.isStringSelectMenu()) await s?.currentPhase?.handleKingExecute?.(i, i.values?.[0]);
    }));

    // ── PANEL ──────────────────────────────────
    router.register('panel:open', h(async (i, s) => {
      const ControlPanel = require('../panels/ControlPanel');
      const access = await ControlPanel.validateAccess(s, i.user.id);
      if (!access.allowed) {
        return i.reply({ content: `❌ ${access.reason}`, ephemeral: true });
      }
      const panel = new ControlPanel(s, access.player);
      const content = panel.build();
      await i.reply({ ...content, ephemeral: true });
    }));

    logger.success('✅ تم تسجيل جميع مسارات التفاعلات');
  }

  /**
   * Safely reply to an interaction, handling all edge cases.
   */
  static async _safeReply(interaction, content) {
    try {
      if (interaction.replied || interaction.deferred) {
        const { ephemeral, ...safeContent } = content;
        await interaction.editReply(safeContent);
      } else {
        await interaction.reply(content);
      }
    } catch { }
  }

  /**
   * Wrap a handler with session lookup + security + error handling.
   */
  static _wrap(sessionManager, handler) {
    return async (interaction) => {
      // Safety defer: auto-acknowledge after 2s to prevent Discord 3s timeout
      const safeDefer = setTimeout(async () => {
        if (!interaction.replied && !interaction.deferred) {
          await interaction.deferReply({ ephemeral: true }).catch(() => {});
        }
      }, 2000);

      try {
        if (!sessionManager) {
          await RouteRegistry._safeReply(interaction, { content: '❌ مدير الجلسات غير متاح.', ephemeral: true });
          return;
        }

        // Session lookup
        const session = sessionManager.getSessionInGuild(interaction.guildId);
        if (!session) {
          await RouteRegistry._safeReply(interaction, { content: '❌ لا توجد جلسة نشطة.', ephemeral: true });
          logger.warn(`⚠️ [Route] لا توجد جلسة في السيرفر ${interaction.guildId} للتفاعل ${interaction.customId}`);
          return;
        }

        // Session health check
        const health = SecurityGuard.validateSessionHealth(session);
        if (!health.valid) {
          await RouteRegistry._safeReply(interaction, { content: `❌ ${health.reason}`, ephemeral: true });
          return;
        }

        // User ownership check for private actions
        const player = session.players.find(p => p.id === interaction.user.id);
        if (!player && !['lobby:join', 'lobby:explain'].includes(interaction.customId)) {
          await RouteRegistry._safeReply(interaction, { content: '❌ أنت لست في هذه اللعبة.', ephemeral: true });
          return;
        }

        // Dead player check for game actions
        if (player && !player.alive) {
          await RouteRegistry._safeReply(interaction, { content: '💀 أنت ميت.', ephemeral: true });
          return;
        }

        await handler(interaction, session);
      } catch (err) {
        logger.error(`❌ [Route] ${interaction.customId} (user: ${interaction.user?.id}):`, err.stack || err.message);
        await RouteRegistry._safeReply(interaction, { content: '❌ حدث خطأ.', ephemeral: true });
      } finally {
        clearTimeout(safeDefer);
      }
    };
  }
}

module.exports = RouteRegistry;
