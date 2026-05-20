const { EmbedBuilder } = require('discord.js');
const logger = require('../utils/logger');

class DiscordService {
  constructor(client) {
    this.client = client;
  }

  async sendDM(userId, content) {
    try {
      const user = await this.client.users.fetch(userId);
      const dm = await user.createDM();
      return await dm.send(content);
    } catch (err) {
      logger.warn(`⚠️ فشل إرسال DM إلى ${userId}:`, err.message);
      return null;
    }
  }

  async sendMessage(channelId, content) {
    try {
      const channel = await this.client.channels.fetch(channelId);
      return await channel.send(content);
    } catch (err) {
      logger.error(`❌ فشل إرسال رسالة إلى ${channelId}:`, err.message);
      return null;
    }
  }

  async editMessage(channelId, messageId, content) {
    try {
      const channel = await this.client.channels.fetch(channelId);
      const msg = await channel.messages.fetch(messageId);
      return await msg.edit(content);
    } catch { return null; }
  }

  async fetchMember(guildId, userId) {
    try {
      const guild = await this.client.guilds.fetch(guildId);
      return await guild.members.fetch(userId);
    } catch { return null; }
  }

  static createEmbed(options) {
    return new EmbedBuilder()
      .setColor(options.color || 0x9B59B6)
      .setTitle(options.title || '')
      .setDescription(options.description || '')
      .setTimestamp()
      .setFooter({ text: options.footer || 'Vale Community' });
  }

  static safeReply(interaction, content) {
    try {
      if (interaction.replied || interaction.deferred) {
        return interaction.followUp(content);
      }
      return interaction.reply(content);
    } catch { return null; }
  }
}

module.exports = DiscordService;
