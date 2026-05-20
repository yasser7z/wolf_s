const fs = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

class PhaseRegistry {
  constructor() {
    this.phases = new Map();
  }

  register(name, phaseClass) {
    if (this.phases.has(name)) {
      logger.warn(`⚠️ الطور ${name} مسجل مسبقاً`);
    }
    this.phases.set(name, phaseClass);
    logger.info(`🔄 تم تسجيل الطور: ${name}`);
  }

  create(name, session) {
    const PhaseClass = this.phases.get(name);
    if (!PhaseClass) {
      throw new Error(`الطور ${name} غير موجود`);
    }
    return new PhaseClass(session);
  }

  loadFromDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) return;

    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isFile() && entry.name.endsWith('.js') && entry.name !== 'BasePhase.js') {
        try {
          const PhaseClass = require(path.join(dirPath, entry.name));
          const name = entry.name.replace('.js', '').toLowerCase();
          this.register(name, PhaseClass);
        } catch (err) {
          logger.error(`❌ فشل تحميل الطور ${entry.name}:`, err.message);
        }
      }
    }
  }

  has(name) {
    return this.phases.has(name);
  }

  getAll() {
    return [...this.phases.keys()];
  }
}

const registry = new PhaseRegistry();
module.exports = { PhaseRegistry: registry };
