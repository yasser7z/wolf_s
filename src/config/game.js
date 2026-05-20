const gameConfig = {
  name: 'Vale Community',
  version: '1.0.0',
  description: 'لعبة اجتماعية خصم مستوحاة من Wolvesville و Town of Salem',
  defaultPrefix: '-',
  language: 'ar',
  botStatus: 'Vale Community',

  fsm: {
    states: ['idle', 'lobby', 'starting', 'night', 'day_discussion', 'day_voting', 'day_resolution', 'ended'],
    initialState: 'idle',
  },

  timings: {
    lobbyTimeout: 120000,
    discussionTime: 45000,
    voteTime: 30000,
    nightActionTime: 30000,
    autoSaveInterval: 30000,
    memoryCleanupInterval: 300000,
    sessionTimeout: 3600000,
    inactivityTimeout: 600000,
    cooldownCleanupInterval: 60000,
    defaultCooldown: 3000,
    activityRotation: 10000,
  },

  limits: {
    minPlayers: 6,
    maxPlayers: 16,
    maxCooldownEntries: 10000,
    maxActionRetries: 3,
    leaderboardLimit: 10,
  },

  database: {
    dir: 'data',
    file: 'database.json',
  },
};

module.exports = gameConfig;
