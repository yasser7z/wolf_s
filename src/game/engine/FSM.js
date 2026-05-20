const logger = require('../../utils/logger');

class FiniteStateMachine {
  constructor(owner, states, transitions, initialState) {
    this.owner = owner;
    this.states = new Set(states);
    this.transitions = new Map();
    this.currentState = initialState;
    this.listeners = new Map();
    this.history = [];

    for (const [from, to, condition] of transitions) {
      const key = `${from}->${to}`;
      this.transitions.set(key, { from, to, condition });
    }

    logger.game(`🏗️ FSM initialized for ${owner.constructor.name}: ${initialState}`);
  }

  canTransitionTo(targetState) {
    for (const [, transition] of this.transitions) {
      if (transition.from === this.currentState && transition.to === targetState) {
        if (typeof transition.condition === 'function') {
          return transition.condition(this.owner);
        }
        return true;
      }
    }
    return false;
  }

  async transition(targetState, payload = {}) {
    if (!this.states.has(targetState)) {
      throw new Error(`حالة غير معروفة: ${targetState}`);
    }

    if (!this.canTransitionTo(targetState)) {
      logger.warn(`⚠️ انتقال غير مسموح: ${this.currentState} -> ${targetState}`);
      return false;
    }

    const from = this.currentState;
    this.currentState = targetState;
    this.history.push({ from, to: targetState, timestamp: Date.now(), payload });

    logger.game(`🔄 FSM: ${from} → ${targetState}`);
    this.emit('stateChange', { from, to: targetState, payload });
    this.emit(`enter:${targetState}`, payload);
    this.emit(`exit:${from}`, payload);

    return true;
  }

  getState() {
    return this.currentState;
  }

  is(state) {
    return this.currentState === state;
  }

  on(event, handler) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(handler);
  }

  emit(event, data) {
    const handlers = this.listeners.get(event) || [];
    for (const handler of handlers) {
      try {
        handler(data);
      } catch (err) {
        logger.error(`❌ FSM listener error [${event}]:`, err.message);
      }
    }
  }

  getHistory(limit = 10) {
    return this.history.slice(-limit);
  }

  reset(initialState) {
    this.currentState = initialState;
    this.history = [];
    logger.game(`🔄 FSM reset to ${initialState}`);
  }

  /** Remove all registered event listeners */
  removeAllListeners() {
    this.listeners.clear();
  }
}

module.exports = FiniteStateMachine;
