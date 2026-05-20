require('dotenv').config();

const { Client, GatewayIntentBits, Partials } = require('discord.js');
const antiCrash = require('./utils/antiCrash');
const logger = require('./utils/logger');
const { initDatabase, ensureTable } = require('./database/db');
const { loadPrefixCommands, loadSlashCommands, initCooldowns } = require('./handlers/commandHandler');
const { loadEvents } = require('./handlers/eventHandler');
const { startServer } = require('../server/keepAlive');
const SessionManager = require('./game/managers/SessionManager');
const EventBus = require('./game/engine/EventBus');
const InteractionRouter = require('./game/engine/InteractionRouter');
const SecurityGuard = require('./game/engine/SecurityGuard');
const RouteRegistry = require('./game/engine/RouteRegistry');
const SessionStore = require('./game/managers/SessionStore');

async function start() {
  logger.info('🚀 جاري تشغيل Vale Community Bot...');

  antiCrash();

  await initDatabase();
  await ensureTable('users', {});
  await ensureTable('guilds', {});
  await ensureTable('activeSessions', {});

  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.GuildMembers,
      GatewayIntentBits.DirectMessages,
    ],
    partials: [
      Partials.Channel,
      Partials.Message,
      Partials.User,
    ],
  });

  const sessionManager = new SessionManager(client);
  const globalEventBus = new EventBus();
  const interactionRouter = new InteractionRouter(globalEventBus);
  const cooldownManager = initCooldowns();

  client.sessionManager = sessionManager;
  client.eventBus = globalEventBus;
  client.interactionRouter = interactionRouter;
  client.cooldownManager = cooldownManager;

  globalEventBus.use((event) => {
    logger.debug(`📡 Event: ${event.event}`);
  });

  // Security middleware for all interactions
  interactionRouter.use(SecurityGuard.createInteractionMiddleware(sessionManager));

  // Register all component interaction routes
  RouteRegistry.register(interactionRouter, sessionManager);

  globalEventBus.on('session.created', async (data) => {
    logger.game(`🏠 جلسة جديدة: ${data.channelId}`);
  });

  globalEventBus.on('session.ended', async (data) => {
    logger.game(`🏁 جلسة منتهية: ${data.channelId}`);
  });

  globalEventBus.on('player.joined', async (data) => {
    logger.game(`👤 انضم لاعب: ${data.username} (${data.playerCount} لاعب)`);
  });

  globalEventBus.on('error', async (data) => {
    logger.error(`❌ ${data.message}`);
  });

  await loadPrefixCommands(client);
  await loadSlashCommands(client);
  await loadEvents(client);

  await SessionStore.cleanupStaleSessions();

  startServer();

  try {
    await client.login(process.env.DISCORD_TOKEN);
    logger.success('✅ تم تسجيل الدخول إلى Discord بنجاح');

    await sessionManager.recoverSessions();

    logger.info(`📊 إحصائيات: ${sessionManager.getStats().activeNow} جلسة نشطة`);

    process.on('SIGINT', async () => {
      logger.warn('🛑 جاري إيقاف البوت...');
      sessionManager.cleanup();
      process.exit(0);
    });

    process.on('SIGTERM', async () => {
      logger.warn('🛑 جاري إيقاف البوت...');
      sessionManager.cleanup();
      process.exit(0);
    });
  } catch (err) {
    logger.error('❌ فشل تسجيل الدخول:', err.message);
    process.exit(1);
  }
}

start();
