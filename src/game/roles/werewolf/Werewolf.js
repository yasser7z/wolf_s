const BaseRole = require('../base/BaseRole');

class Werewolf extends BaseRole {
  constructor() {
    super({
      id: 'Werewolf',
      name: 'ذئب',
      team: 'الذئاب',
      description: 'أنت ذئب متوحش. كل ليلة يمكنك مهاجمة أحد سكان القرية.',
      emoji: '🐺',
      priority: 100,
      nightAction: true,
    });
  }

  onNightAction(actionQueue, player, targetId) {
    actionQueue.enqueue({
      type: 'WEREWOLF_KILL',
      playerId: player.id,
      targetId,
      priority: 100,
    });
  }
}

module.exports = Werewolf;
