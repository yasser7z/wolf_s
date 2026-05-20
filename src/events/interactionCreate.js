const { handleSlashCommand } = require('../handlers/commandHandler');
const logger = require('../utils/logger');

module.exports = {
  async execute(interaction, client) {
    const sessionManager = client.sessionManager;
    const router = client.interactionRouter;

    // Slash commands
    if (interaction.isCommand()) {
      if (sessionManager) {
        handleSlashCommand(interaction, client, sessionManager);
      }
      return;
    }

    // Component interactions (buttons, select menus) — route via InteractionRouter
    if (interaction.isButton() || interaction.isStringSelectMenu()) {
      if (router) {
        await router.resolve(interaction);
      }
      return;
    }

    // Modal/autocomplete — fallback
    if (interaction.isModalSubmit()) {
      if (router) {
        await router.resolve(interaction);
      }
    }
  },
};
