class VictoryChecker {
  constructor(session) {
    this.session = session;
  }

  check() {
    const alive = this.session.getAlivePlayers();
    const wolves = this.session.getAlivePlayersByRole('Werewolf');
    const villagers = alive.filter(p => p.role && p.role.team === 'القرية');

    if (wolves.length === 0) {
      return { winner: 'القرية', reason: 'تم القضاء على جميع الذئاب!' };
    }

    if (wolves.length >= villagers.length) {
      return { winner: 'الذئاب', reason: 'الذئاب تفوقت على القرويين!' };
    }

    return null;
  }

  static getWinCondition(team) {
    const conditions = {
      'القرية': 'اقضِ على جميع الذئاب.',
      'الذئاب': 'اقضِ على عدد كافٍ من القرويين حتى تتساوى الأعداد.',
    };
    return conditions[team] || 'حقق أهدافك الخاصة.';
  }
}

module.exports = VictoryChecker;
