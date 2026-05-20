const BaseRole = require('../base/BaseRole');

class Detective extends BaseRole {
  constructor() {
    super({
      id: 'Detective',
      name: 'محقق',
      team: 'القرية',
      description: 'يمكنك التحقيق في هوية لاعب واحد **مرة واحدة** طوال اللعبة.',
      emoji: '🔍',
      priority: 80,
      maxUses: 1,
      nightAction: true,
    });
  }

  onNightAction(actionQueue, player, targetId) {
    actionQueue.enqueue({
      type: 'DETECTIVE_INVESTIGATE',
      playerId: player.id,
      targetId,
      priority: 80,
    });
    this.useAbility();
  }
}

module.exports = Detective;
