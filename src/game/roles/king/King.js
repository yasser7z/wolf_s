const BaseRole = require('../base/BaseRole');

class King extends BaseRole {
  constructor() {
    super({
      id: 'King',
      name: 'ملك',
      team: 'القرية',
      description: 'يمكنك إعدام أي لاعب فوراً **مرة واحدة** خلال النهار. استخدم السلاش `/إعدام`.',
      emoji: '👑',
      priority: 10,
      maxUses: 1,
      nightAction: false,
    });
    this.hasExecuted = false;
  }

  canExecute() {
    return !this.hasExecuted;
  }

  execute() {
    this.hasExecuted = true;
    this.useAbility();
  }

  onDayAction(actionQueue, player, targetId) {
    if (!this.canExecute()) return;
    this.execute();
  }

  getInfo() {
    return {
      ...super.getInfo(),
      hasExecuted: this.hasExecuted,
    };
  }
}

module.exports = King;
