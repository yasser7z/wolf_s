const logger = require('../../../utils/logger');

class BasePhase {
  constructor(session, config = {}) {
    this.session = session;
    this.name = config.name || 'unknown';
    this.duration = config.duration || 60000;
    this.timeout = null;
    this.collector = null;
    this.messages = [];
  }

  async start() {
    throw new Error(`الدالة start() يجب أن تكون معرفة في ${this.name}`);
  }

  async end() {
    this._clearTimeout();
    this._destroyCollector();
    this._cleanupMessages();
  }

  setTimeout(callback, ms) {
    // Clear existing timeout first to prevent duplicates
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }
    this.timeout = setTimeout(async () => {
      this.timeout = null;
      try {
        await callback();
      } catch (err) {
        logger.error(`❌ Phase timeout [${this.name}]:`, err.message);
      }
    }, ms);

    if (this.session && this.session._phaseTimeouts) {
      this.session._phaseTimeouts.push(this.timeout);
    }
  }

  _clearTimeout() {
    if (this.timeout) {
      clearTimeout(this.timeout);
      this.timeout = null;
    }
  }

  _destroyCollector() {
    if (this.collector) {
      this.collector.stop();
      this.collector = null;
    }
  }

  _cleanupMessages() {
    this.messages = [];
  }

  async send(content) {
    const msg = await this.session.channel.send(content).catch(() => null);
    if (msg) this.messages.push(msg);
    return msg;
  }

  async reply(interaction, content) {
    try {
      if (interaction.replied || interaction.deferred) {
        const { ephemeral, ...safeContent } = content;
        await interaction.editReply(safeContent);
      } else {
        await interaction.reply(content);
      }
    } catch { }
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getAlive() {
    return this.session.getAlivePlayers();
  }

  getAliveByRole(roleName) {
    return this.session.getAlivePlayersByRole(roleName);
  }
}

module.exports = BasePhase;
