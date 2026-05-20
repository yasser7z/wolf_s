const BaseRole = require('../base/BaseRole');

class Mayor extends BaseRole {
  constructor() {
    super({
      id: 'Mayor',
      name: 'عمدة',
      team: 'القرية',
      description: 'صوتك يحسب كـ **صوتين** تلقائياً في جميع جلسات التصويت.',
      emoji: '🏛️',
      priority: 1,
      nightAction: false,
    });
  }
}

module.exports = Mayor;
