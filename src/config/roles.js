const ROLE_WEIGHTS = {
  Villager: 1,
  Werewolf: 3,
  Doctor: 2,
  Detective: 2,
  Guard: 2,
  King: 1,
  Mayor: 1,
  Seductress: 2,
  UmmZaki: 1,
};

const ROLE_TEAMS = {
  Villager: 'القرية',
  Werewolf: 'الذئاب',
  Doctor: 'القرية',
  Detective: 'القرية',
  Guard: 'القرية',
  King: 'القرية',
  Mayor: 'القرية',
  Seductress: 'القرية',
  UmmZaki: 'القرية',
};

const DISTRIBUTION_POOLS = {
  6:  ['Villager', 'Villager', 'Werewolf', 'Werewolf', 'Doctor', 'Detective'],
  7:  ['Villager', 'Villager', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard'],
  8:  ['Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Mayor'],
  9:  ['Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard'],
  10: ['Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor'],
  11: ['Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King'],
  12: ['Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King', 'Seductress'],
  13: ['Villager', 'Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King', 'Seductress'],
  14: ['Villager', 'Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King', 'Seductress', 'UmmZaki'],
  15: ['Villager', 'Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King', 'Seductress', 'UmmZaki'],
  16: ['Villager', 'Villager', 'Villager', 'Villager', 'Werewolf', 'Werewolf', 'Werewolf', 'Werewolf', 'Doctor', 'Detective', 'Guard', 'Mayor', 'King', 'Seductress', 'UmmZaki'],
};

const DEFAULT_SETTINGS = {
  minPlayers: 6,
  maxPlayers: 16,
  discussionTime: 45000,
  voteTime: 30000,
  nightTime: 30000,
  lobbyTimeout: 120000,
  autoSaveInterval: 30000,
};

module.exports = {
  ROLE_WEIGHTS,
  ROLE_TEAMS,
  DISTRIBUTION_POOLS,
  DEFAULT_SETTINGS,
};
