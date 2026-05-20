const { db } = require('../db');

class GuildModel {
  static async getGuild(guildId) {
    let guild = await db.get(`guilds.${guildId}`);
    if (!guild) {
      guild = {
        id: guildId,
        prefix: '-',
        gameChannel: null,
        lobbyChannel: null,
        enabled: true,
        createdAt: Date.now(),
      };
      await db.set(`guilds.${guildId}`, guild);
    }
    return guild;
  }

  static async updateGuild(guildId, data) {
    const guild = await this.getGuild(guildId);
    Object.assign(guild, data);
    await db.set(`guilds.${guildId}`, guild);
    return guild;
  }

  static async setPrefix(guildId, prefix) {
    return this.updateGuild(guildId, { prefix });
  }
}

module.exports = GuildModel;
