const logger = require('./logger');

function antiCrash() {
  process.on('unhandledRejection', (reason, promise) => {
    logger.error('❌ Unhandled Rejection at:', promise);
    logger.error('📄 Reason:', reason?.stack || reason);
  });

  process.on('uncaughtException', (err) => {
    logger.error('❌ Uncaught Exception:', err);
    logger.error('📄 Stack:', err.stack);
  });

  process.on('uncaughtExceptionMonitor', (err, origin) => {
    logger.error('❌ Uncaught Exception Monitor:', err, origin);
  });

  process.on('warning', (warning) => {
    logger.warn('⚠️ Warning:', warning.name);
    logger.warn('📄 Message:', warning.message);
    logger.warn('📄 Stack:', warning.stack);
  });

  logger.success('✅ تم تفعيل نظام الحماية من الأعطال');
}

module.exports = antiCrash;
