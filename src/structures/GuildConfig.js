class GuildConfig {
  constructor(data = {}) {
    this.id = data.id || null;
    this.prefix = data.prefix || '-';
    this.gameChannel = data.gameChannel || null;
    this.lobbyChannel = data.lobbyChannel || null;
    this.enabled = data.enabled ?? true;
    this.language = data.language || 'ar';
    this.minPlayers = data.minPlayers || 6;
    this.maxPlayers = data.maxPlayers || 16;
    this.discussionTime = data.discussionTime || 45000;
    this.voteTime = data.voteTime || 30000;
    this.nightTime = data.nightTime || 30000;
    this.createdAt = data.createdAt || Date.now();
  }

  toJSON() {
    return {
      id: this.id,
      prefix: this.prefix,
      gameChannel: this.gameChannel,
      lobbyChannel: this.lobbyChannel,
      enabled: this.enabled,
      language: this.language,
      minPlayers: this.minPlayers,
      maxPlayers: this.maxPlayers,
      discussionTime: this.discussionTime,
      voteTime: this.voteTime,
      nightTime: this.nightTime,
    };
  }

  static fromDB(data) {
    return new GuildConfig(data);
  }
}

module.exports = GuildConfig;
