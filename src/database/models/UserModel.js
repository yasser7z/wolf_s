const { db } = require('../db');

class UserModel {
  static async getUser(userId) {
    let user = await db.get(`users.${userId}`);
    if (!user) {
      user = {
        id: userId,
        wins: 0,
        losses: 0,
        gamesPlayed: 0,
        winRate: 0,
        xp: 0,
        level: 1,
        roleStats: {},
        lastDaily: null,
        createdAt: Date.now(),
      };
      await db.set(`users.${userId}`, user);
    }
    return user;
  }

  static async updateUser(userId, data) {
    const user = await this.getUser(userId);
    Object.assign(user, data);
    await db.set(`users.${userId}`, user);
    return user;
  }

  static async addWin(userId, roleId = null) {
    const user = await this.getUser(userId);
    user.wins += 1;
    user.gamesPlayed += 1;
    user.winRate = user.gamesPlayed > 0 ? Math.round((user.wins / user.gamesPlayed) * 100) : 0;
    user.xp += 50;
    user.level = Math.floor(user.xp / 200) + 1;

    if (roleId) {
      if (!user.roleStats[roleId]) user.roleStats[roleId] = { gamesPlayed: 0, wins: 0, losses: 0 };
      user.roleStats[roleId].gamesPlayed += 1;
      user.roleStats[roleId].wins += 1;
    }

    await db.set(`users.${userId}`, user);
    return user;
  }

  static async addLoss(userId, roleId = null) {
    const user = await this.getUser(userId);
    user.losses += 1;
    user.gamesPlayed += 1;
    user.winRate = user.gamesPlayed > 0 ? Math.round((user.wins / user.gamesPlayed) * 100) : 0;
    user.xp += 10;
    user.level = Math.floor(user.xp / 200) + 1;

    if (roleId) {
      if (!user.roleStats[roleId]) user.roleStats[roleId] = { gamesPlayed: 0, wins: 0, losses: 0 };
      user.roleStats[roleId].gamesPlayed += 1;
      user.roleStats[roleId].losses += 1;
    }

    await db.set(`users.${userId}`, user);
    return user;
  }

  static async addGamePlayed(userId) {
    const user = await this.getUser(userId);
    user.gamesPlayed += 1;
    await db.set(`users.${userId}`, user);
    return user;
  }

  static async getLeaderboard(limit = 10) {
    const all = await db.get('users');
    if (!all) return [];
    return Object.values(all)
      .sort((a, b) => b.wins - a.wins || b.xp - a.xp)
      .slice(0, limit);
  }

  static async getRoleLeaderboard(roleId, limit = 10) {
    const all = await db.get('users');
    if (!all) return [];
    return Object.values(all)
      .filter(u => u.roleStats && u.roleStats[roleId] && u.roleStats[roleId].gamesPlayed > 0)
      .sort((a, b) => (b.roleStats[roleId]?.wins || 0) - (a.roleStats[roleId]?.wins || 0))
      .slice(0, limit);
  }
}

module.exports = UserModel;
