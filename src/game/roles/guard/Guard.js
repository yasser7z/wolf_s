const BaseRole = require('../base/BaseRole');

class Guard extends BaseRole {
  constructor() {
    super({
      id: 'Guard',
      name: 'حارس',
      team: 'القرية',
      description: 'يمكنك حماية لاعب واحد **مرة واحدة** طوال اللعبة من الذئاب.',
      emoji: '🛡️',
      priority: 60,
      maxUses: 1,
      nightAction: true,
      canSelfTarget: true,
    });
  }

  onNightAction(actionQueue, player, targetId) {
    actionQueue.enqueue({
      type: 'GUARD_PROTECT',
      playerId: player.id,
      targetId,
      priority: 60,
    });
    this.useAbility();
  }
}

module.exports = Guard;
