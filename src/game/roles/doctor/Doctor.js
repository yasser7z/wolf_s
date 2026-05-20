const BaseRole = require('../base/BaseRole');

class Doctor extends BaseRole {
  constructor() {
    super({
      id: 'Doctor',
      name: 'طبيب',
      team: 'القرية',
      description: 'كل ليلة يمكنك إنقاذ أحد اللاعبين من الموت.',
      emoji: '💉',
      priority: 60,
      nightAction: true,
      canSelfTarget: true,
    });
  }

  onNightAction(actionQueue, player, targetId) {
    actionQueue.enqueue({
      type: 'DOCTOR_HEAL',
      playerId: player.id,
      targetId,
      priority: 60,
    });
  }
}

module.exports = Doctor;
