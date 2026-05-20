const { handlePrefixCommand } = require('../handlers/commandHandler');
const logger = require('../utils/logger');

module.exports = {
  async execute(message, client) {
    if (message.author.bot || !message.guild) return;

    const sessionManager = client.sessionManager;
    if (sessionManager) {
      handlePrefixCommand(message, client, sessionManager);
    }
  },
};
