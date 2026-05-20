const BaseRole = require('../base/BaseRole');

class Villager extends BaseRole {
  constructor() {
    super({
      id: 'Villager',
      name: 'قروي',
      team: 'القرية',
      description: 'أنت قروي عادي. ليس لديك قدرة خاصة، لكن صوتك مهم في التصويت.',
      emoji: '🧑‍🌾',
      priority: 0,
      nightAction: false,
    });
  }
}

module.exports = Villager;
