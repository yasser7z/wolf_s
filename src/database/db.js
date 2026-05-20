const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

const DATA_DIR = path.join(__dirname, '../../data');

class JsonDB {
  constructor() {
    this.cache = {};
    this.filePath = path.join(DATA_DIR, 'database.json');
  }

  async init() {
    if (!fs.existsSync(DATA_DIR)) {
      fs.mkdirSync(DATA_DIR, { recursive: true });
    }
    if (fs.existsSync(this.filePath)) {
      try {
        this.cache = JSON.parse(fs.readFileSync(this.filePath, 'utf8'));
      } catch {
        this.cache = {};
      }
    } else {
      this.cache = {};
      this._save();
    }
    logger.success('✅ تم تهيئة قاعدة البيانات (JSON)');
  }

  _save() {
    try {
      fs.writeFileSync(this.filePath, JSON.stringify(this.cache, null, 2));
    } catch (err) {
      logger.error('❌ فشل حفظ قاعدة البيانات:', err.message);
    }
  }

  _resolvePath(key) {
    const parts = key.split('.');
    let current = this.cache;
    for (let i = 0; i < parts.length - 1; i++) {
      if (current[parts[i]] === undefined) {
        current[parts[i]] = {};
      }
      current = current[parts[i]];
    }
    return { parent: current, key: parts[parts.length - 1] };
  }

  async get(key) {
    const { parent, key: prop } = this._resolvePath(key);
    return parent[prop] !== undefined ? parent[prop] : null;
  }

  async set(key, value) {
    const { parent, key: prop } = this._resolvePath(key);
    parent[prop] = value;
    this._save();
  }

  async delete(key) {
    const { parent, key: prop } = this._resolvePath(key);
    delete parent[prop];
    this._save();
  }

  async has(key) {
    const { parent, key: prop } = this._resolvePath(key);
    return parent[prop] !== undefined;
  }

  async push(key, value) {
    const existing = await this.get(key) || [];
    if (!Array.isArray(existing)) throw new Error('القيمة موجودة وليست مصفوفة');
    existing.push(value);
    await this.set(key, existing);
  }

  async all() {
    return this.cache;
  }
}

const db = new JsonDB();

async function initDatabase() {
  await db.init();
  return db;
}

async function ensureTable(table, defaults = {}) {
  const exists = await db.has(table);
  if (!exists) {
    await db.set(table, defaults);
    logger.info(`📦 تم إنشاء جدول ${table}`);
  }
}

module.exports = { db, initDatabase, ensureTable };
