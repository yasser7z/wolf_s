const fs = require('fs');
const path = require('path');
const logger = require('../../utils/logger');

class RoleRegistry {
  constructor() {
    this.roles = new Map();
    this.categories = new Map();
  }

  register(roleClass) {
    const instance = new roleClass();
    const id = instance.id || instance.name;

    if (this.roles.has(id)) {
      logger.warn(`⚠️ الدور ${id} مسجل مسبقاً، سيتم استبداله`);
    }

    this.roles.set(id, roleClass);

    const category = path.dirname(roleClass.name);
    if (!this.categories.has(instance.team)) {
      this.categories.set(instance.team, []);
    }
    this.categories.get(instance.team).push(id);

    logger.info(`📜 تم تسجيل الدور: ${instance.emoji} ${instance.name} (${instance.team})`);
  }

  getClass(roleId) {
    return this.roles.get(roleId);
  }

  createInstance(roleId) {
    const RoleClass = this.roles.get(roleId);
    if (!RoleClass) return null;
    return new RoleClass();
  }

  getByName(name) {
    for (const [, RoleClass] of this.roles) {
      const instance = new RoleClass();
      if (instance.name === name) return RoleClass;
    }
    return null;
  }

  getByTeam(teamName) {
    return this.categories.get(teamName) || [];
  }

  getAll() {
    const result = [];
    for (const [id, RoleClass] of this.roles) {
      result.push({ id, role: new RoleClass() });
    }
    return result;
  }

  getCount() {
    return this.roles.size;
  }

  loadFromDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) return;

    const entries = fs.readdirSync(dirPath, { withFileTypes: true });
    for (const entry of entries) {
      if (entry.isDirectory()) {
        this.loadFromDirectory(path.join(dirPath, entry.name));
      } else if (entry.isFile() && entry.name.endsWith('.js') && entry.name !== 'BaseRole.js') {
        try {
          const RoleClass = require(path.join(dirPath, entry.name));
          if (RoleClass.prototype?.constructor) {
            this.register(RoleClass);
          }
        } catch (err) {
          logger.error(`❌ فشل تحميل الدور ${entry.name}:`, err.message);
        }
      }
    }
  }

  reset() {
    this.roles.clear();
    this.categories.clear();
  }
}

const registry = new RoleRegistry();
module.exports = { RoleRegistry: registry };
