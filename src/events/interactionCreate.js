const { handleSlashCommand } = require('../handlers/commandHandler');
const logger = require('../utils/logger');

module.exports = {
  async execute(interaction, client) {
    const sessionManager = client.sessionManager;
    const router = client.interactionRouter;

    try {
      // Slash commands
      if (interaction.isCommand()) {
        if (sessionManager) {
          await handleSlashCommand(interaction, client, sessionManager);
        }
        return;
      }

      // Component interactions (buttons, select menus) — route via InteractionRouter
      if (interaction.isButton() || interaction.isStringSelectMenu()) {
        if (router) {
          await router.resolve(interaction);
        } else {
          logger.warn(`⚠️ لا يوجد موجه تفاعلات: ${interaction.customId}`);
          if (!interaction.replied && !interaction.deferred) {
            try {
              await interaction.reply({ content: '❌ نظام التفاعلات غير متاح.', ephemeral: true });
            } catch { }
          }
        }
        return;
      }

      // Modal/autocomplete — fallback
      if (interaction.isModalSubmit()) {
        if (router) {
          await router.resolve(interaction);
        }
      }
    } catch (err) {
      logger.error(`❌ [interactionCreate] ${interaction.customId || interaction.commandName}:`, err.stack);
      if (!interaction.replied && !interaction.deferred) {
        try {
          await interaction.reply({ content: '❌ حدث خطأ.', ephemeral: true });
        } catch { }
      }
    }
  },
};
