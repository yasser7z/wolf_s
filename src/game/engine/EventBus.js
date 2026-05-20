const logger = require('../../utils/logger');

class EventBus {
  constructor() {
    this.listeners = new Map();
    this.globalListeners = new Map();
    this.middlewares = [];
    this._idCounter = 0;
  }

  on(event, handler, options = {}) {
    const id = ++this._idCounter;
    const entry = { id, handler, once: options.once || false, priority: options.priority || 0 };

    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }

    const listeners = this.listeners.get(event);
    listeners.push(entry);
    listeners.sort((a, b) => b.priority - a.priority);

    return id;
  }

  once(event, handler) {
    return this.on(event, handler, { once: true });
  }

  off(event, handlerId) {
    const listeners = this.listeners.get(event);
    if (!listeners) return;

    const idx = listeners.findIndex(l => l.id === handlerId);
    if (idx !== -1) {
      listeners.splice(idx, 1);
    }
  }

  use(middleware) {
    this.middlewares.push(middleware);
  }

  async emit(event, data = {}) {
    const enriched = { event, timestamp: Date.now(), ...data };

    for (const mw of this.middlewares) {
      try {
        mw(enriched);
      } catch (err) {
        logger.error(`❌ EventBus middleware error:`, err.message);
      }
    }

    const handlers = [...(this.listeners.get(event) || [])];
    const globalHandlers = [...(this.globalListeners.get('*') || [])];

    const allHandlers = [...handlers, ...globalHandlers];

    for (const entry of allHandlers) {
      try {
        await entry.handler(enriched);
      } catch (err) {
        logger.error(`❌ EventBus handler [${event}]:`, err.message);
      }

      if (entry.once) {
        this.off(event, entry.id);
      }
    }

    return enriched;
  }

  onAny(handler) {
    return this.on('*', handler);
  }

  removeAll(event) {
    this.listeners.delete(event);
  }

  listenerCount(event) {
    return (this.listeners.get(event) || []).length;
  }

  /** Remove all listeners for a given event by handler reference */
  offByRef(event, handler) {
    const listeners = this.listeners.get(event);
    if (!listeners) return;
    const filtered = listeners.filter(l => l.handler !== handler);
    if (filtered.length === 0) this.listeners.delete(event);
    else this.listeners.set(event, filtered);
  }

  /** Remove ALL listeners across all events */
  clear() {
    this.listeners.clear();
    this.globalListeners.clear();
    this.middlewares = [];
  }

}

module.exports = EventBus;
