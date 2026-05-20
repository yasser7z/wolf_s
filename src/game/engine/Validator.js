const logger = require('../../utils/logger');

class Validator {
  static validateInteraction(interaction) {
    const errors = [];

    if (!interaction) {
      return { valid: false, errors: ['التفاعل فارغ'] };
    }

    if (!interaction.user) {
      errors.push('لا يوجد مستخدم في التفاعل');
    }

    if (!interaction.channel) {
      errors.push('لا يوجد رابط في التفاعل');
    }

    if (!interaction.guild) {
      errors.push('لا يوجد سيرفر في التفاعل');
    }

    return { valid: errors.length === 0, errors };
  }

  static validatePlayer(player) {
    const errors = [];

    if (!player) return { valid: false, errors: ['اللاعب فارغ'] };
    if (!player.id) errors.push('لا يوجد آيدي للاعب');
    if (typeof player.alive !== 'boolean') errors.push('حالة اللاعب غير محددة');

    return { valid: errors.length === 0, errors };
  }

  static validateGameState(session) {
    const errors = [];

    if (!session) return { valid: false, errors: ['الجلسة فارغة'] };
    if (!session.fsm) errors.push('FSM غير موجود');
    if (!session.eventBus) errors.push('EventBus غير موجود');
    if (!Array.isArray(session.players)) errors.push('اللاعبون ليسوا مصفوفة');

    return { valid: errors.length === 0, errors };
  }

  static validatePhaseTransition(session, targetState) {
    if (!session.fsm) {
      return { valid: false, errors: ['FSM غير موجود'] };
    }

    const canTransition = session.fsm.canTransitionTo(targetState);
    return {
      valid: canTransition,
      errors: canTransition ? [] : [`لا يمكن الانتقال من ${session.fsm.getState()} إلى ${targetState}`],
    };
  }

  static validatePlayerAlive(player) {
    if (!player) return { valid: false, errors: ['اللاعب فارغ'] };
    if (!player.alive) return { valid: false, errors: ['اللاعب ميت ولا يمكنه تنفيذ إجراءات'] };
    return { valid: true, errors: [] };
  }

  static validateAction(action) {
    const errors = [];

    if (!action) return { valid: false, errors: ['الإجراء فارغ'] };
    if (!action.type) errors.push('نوع الإجراء مطلوب');
    if (!action.playerId) errors.push('آيدي اللاعب مطلوب');

    return { valid: errors.length === 0, errors };
  }

  static validateComponent(customId, validPrefixes) {
    if (!customId) {
      return { valid: false, errors: ['customId فارغ'] };
    }

    const matched = validPrefixes.some(prefix => customId.startsWith(prefix));
    return {
      valid: matched,
      errors: matched ? [] : [`customId "${customId}" لا يبدأ بأي بادئة معروفة`],
    };
  }

  static sanitizeInput(input) {
    if (typeof input !== 'string') return input;
    return input.replace(/[<@!&#>]/g, '').trim();
  }

  static rateLimitCheck(lastAction, minInterval) {
    const now = Date.now();
    if (!lastAction) return { allowed: true, remaining: 0 };
    const elapsed = now - lastAction;
    return {
      allowed: elapsed >= minInterval,
      remaining: Math.max(0, minInterval - elapsed),
    };
  }
}

module.exports = Validator;
