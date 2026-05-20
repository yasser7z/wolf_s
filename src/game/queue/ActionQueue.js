const logger = require('../../utils/logger');
const EventEmitter = require('events');

class ActionQueue extends EventEmitter {
  constructor(sessionId) {
    super();
    this.sessionId = sessionId;
    this.queue = [];
    this.processing = false;
    this.priorityMap = {
      GUARD_PROTECT: 600,
      DOCTOR_HEAL: 500,
      SEDUCTRESS_VISIT: 400,
      WEREWOLF_KILL: 300,
      SPECIAL_DEATH: 200,
      UMMZAKI_REVEAL: 100,
      DETECTIVE_INVESTIGATE: 90,
      KING_EXECUTE: 80,
      VOTE: 10,
      DEFAULT: 0,
    };
  }

  enqueue(action) {
    const entry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      type: action.type || 'DEFAULT',
      priority: this.priorityMap[action.type] ?? this.priorityMap.DEFAULT,
      playerId: action.playerId,
      targetId: action.targetId,
      data: action.data || {},
      timestamp: Date.now(),
      status: 'pending',
      retries: 0,
      maxRetries: action.maxRetries || 3,
    };

    this.queue.push(entry);
    this.queue.sort((a, b) => b.priority - a.priority || a.timestamp - b.timestamp);

    this.emit('queued', entry);
    logger.game(`📥 [${this.sessionId}] تمت إضافة إجراء: ${entry.type} من ${entry.playerId}`);

    if (!this.processing) {
      this.processNext();
    }

    return entry.id;
  }

  async processNext() {
    if (this.queue.length === 0 || this.processing) return;

    this.processing = true;
    const action = this.queue.shift();

    try {
      action.status = 'processing';
      this.emit('processing', action);

      await this._executeAction(action);

      action.status = 'completed';
      this.emit('completed', action);
      logger.game(`✅ [${this.sessionId}] تم تنفيذ: ${action.type}`);
    } catch (err) {
      action.status = 'failed';
      action.retries += 1;
      this.emit('failed', action, err);
      logger.error(`❌ [${this.sessionId}] فشل إجراء ${action.type}:`, err.message);

      if (action.retries < action.maxRetries) {
        this.queue.unshift(action);
        logger.game(`🔄 [${this.sessionId}] إعادة محاولة ${action.type} (${action.retries}/${action.maxRetries})`);
      }
    }

    this.processing = false;

    if (this.queue.length > 0) {
      this.processNext();
    } else {
      this.emit('drained');
    }
  }

  async _executeAction(action) {
    const handler = this._getHandler(action.type);
    if (handler) {
      await handler(action);
    }
  }

  _getHandler(type) {
    return this.handlers?.get(type);
  }

  setHandler(type, handler) {
    if (!this.handlers) this.handlers = new Map();
    this.handlers.set(type, handler);
  }

  findAction(type) {
    return this.queue.find(a => a.type === type && a.status === 'pending');
  }

  removeAction(type) {
    const before = this.queue.length;
    this.queue = this.queue.filter(a => !(a.type === type && a.status === 'pending'));
    return before - this.queue.length;
  }

  getPending() {
    return this.queue.filter(a => a.status === 'pending');
  }

  getCompleted() {
    return this.queue.filter(a => a.status === 'completed');
  }

  getFailed() {
    return this.queue.filter(a => a.status === 'failed');
  }

  cancel(playerId) {
    const before = this.queue.length;
    this.queue = this.queue.filter(a => a.playerId !== playerId && a.status === 'pending');
    const removed = before - this.queue.length;
    if (removed > 0) {
      logger.game(`🗑️ [${this.sessionId}] تم إلغاء ${removed} إجراء للاعب ${playerId}`);
    }
    return removed;
  }

  clear() {
    this.queue = [];
    this.processing = false;
    this.emit('cleared');
    logger.game(`🧹 [${this.sessionId}] تم مسح قائمة الإجراءات`);
  }

  size() {
    return this.queue.length;
  }

  toJSON() {
    return {
      sessionId: this.sessionId,
      queue: this.queue.map(a => ({ ...a, handlers: undefined })),
      processing: this.processing,
    };
  }
}

module.exports = ActionQueue;
