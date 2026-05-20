const BaseRole = require('../base/BaseRole');

class UmmZaki extends BaseRole {
  constructor() {
    super({
      id: 'UmmZaki',
      name: 'أم زكي',
      team: 'القرية',
      description: 'إذا قتلك الذئاب، يتم كشف أحد الذئاب عشوائياً لجميع اللاعبين قبل موتك.',
      emoji: '👵',
      priority: 5,
      nightAction: false,
    });
    this._revealedWolf = null;
  }

  onKilled(killer) {
    const aliveWolves = this._getAliveWolves();
    if (aliveWolves.length > 0) {
      const random = aliveWolves[Math.floor(Math.random() * aliveWolves.length)];
      this._revealedWolf = random.id;
    }
    return true;
  }

  getRevealedWolf() {
    return this._revealedWolf;
  }

  _getAliveWolves() {
    if (!this._owner) return [];
    const session = this._owner._session;
    if (!session) return [];
    return session.players.filter(p => p.alive && p.role?.name === 'ذئب');
  }
}

module.exports = UmmZaki;
