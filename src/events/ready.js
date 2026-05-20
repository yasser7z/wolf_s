const logger = require('../utils/logger');
const { registerSlashCommands } = require('../handlers/commandHandler');
const { RoleRegistry } = require('../game/roles/RoleRegistry');
const { PhaseRegistry } = require('../game/phases/PhaseRegistry');
const path = require('path');

module.exports = {
  once: true,
  async execute(client) {
    logger.success(`✅ ${client.user.tag} جاهز للعمل!`);
    logger.info(`👥 السيرفرات: ${client.guilds.cache.size}`);

    const rolesDir = path.join(__dirname, '../game/roles');
    RoleRegistry.loadFromDirectory(rolesDir);
    logger.info(`📜 تم تسجيل ${RoleRegistry.getCount()} دور`);

    const phasesDir = path.join(__dirname, '../game/phases');
    PhaseRegistry.loadFromDirectory(phasesDir);
    logger.info(`🔄 الأطوار المتاحة: ${PhaseRegistry.getAll().join(', ')}`);

    await registerSlashCommands(client);

    const activities = ['-مساعدة | Vale Community', '🐺 قرية فالي', `${client.guilds.cache.size} سيرفر`, '-انضم للعبة'];
    let i = 0;
    setInterval(() => {
      client.user.setActivity(activities[i]);
      i = (i + 1) % activities.length;
    }, 10000);
  },
};
