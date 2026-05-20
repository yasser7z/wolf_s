const BaseRole = require('../base/BaseRole');

class Seductress extends BaseRole {
  constructor() {
    super({
      id: 'Seductress',
      name: 'مغوية',
      team: 'القرية',
      description: 'تزورين لاعباً كل ليلة. إن كان ذئباً → يموت الاثنان. إن كان قروياً تتعرض له الذئاب → ينجو.',
      emoji: '💃',
      priority: 70,
      nightAction: true,
      maxUses: 1,
    });
  }

  onNightAction(actionQueue, player, targetId) {
    actionQueue.enqueue({
      type: 'SEDUCTRESS_VISIT',
      playerId: player.id,
      targetId,
      priority: 70,
    });
    this.useAbility();
  }
}

module.exports = Seductress;
