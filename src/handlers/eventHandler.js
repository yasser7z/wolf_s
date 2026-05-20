const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

async function loadEvents(client) {
  const eventsPath = path.join(__dirname, '../events');
  const files = fs.readdirSync(eventsPath).filter(f => f.endsWith('.js'));

  for (const file of files) {
    try {
      const event = require(path.join(eventsPath, file));
      const eventName = file.replace('.js', '');

      if (event.once) {
        client.once(eventName, (...args) => event.execute(...args, client));
      } else {
        client.on(eventName, (...args) => event.execute(...args, client));
      }

      logger.info(`📡 تم تحميل حدث: ${eventName}`);
    } catch (err) {
      logger.error(`❌ خطأ في تحميل الحدث ${file}:`, err.message);
    }
  }

  logger.success(`✅ تم تحميل ${files.length} حدث`);
}

module.exports = { loadEvents };
