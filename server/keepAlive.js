const express = require('express');
const logger = require('../src/utils/logger');

function startServer() {
  const app = express();
  const PORT = process.env.PORT || 3000;

  app.get('/', (req, res) => {
    res.json({
      status: '🟢 متصل',
      name: 'Vale Community Bot',
      version: '1.0.0',
      uptime: process.uptime(),
      timestamp: Date.now(),
    });
  });

  app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
  });

  app.listen(PORT, () => {
    logger.success(`✅ سيرفر Express يعمل على المنفذ ${PORT}`);
    logger.info(`🌐 الرابط: http://localhost:${PORT}`);
  });
}

module.exports = { startServer };
