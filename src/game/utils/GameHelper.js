const { shuffle, sleep, randomItem, getRoleEmoji, formatTime } = require('../../utils/helpers');

class GameHelper {
  static shuffle = shuffle;
  static sleep = sleep;
  static randomItem = randomItem;
  static getRoleEmoji = getRoleEmoji;
  static formatTime = formatTime;

  static calculateXp(won, survived, nightActions) {
    let xp = 10;
    if (won) xp += 40;
    if (survived) xp += 20;
    xp += nightActions * 5;
    return xp;
  }

  static calculateLevel(xp) {
    return Math.floor(xp / 200) + 1;
  }

  static getNextLevelXp(currentLevel) {
    return currentLevel * 200;
  }

  static formatPlayerList(players) {
    return players.map((p, i) => `**${i + 1}.** <@${p.id}>`).join('\n');
  }

  static getAliveCount(players) {
    return players.filter(p => p.alive).length;
  }

  static getDeadCount(players) {
    return players.filter(p => !p.alive).length;
  }
}

module.exports = GameHelper;
