const logger = require('../utils/logger');

module.exports = {
  async execute(member, client) {
    const sessionManager = client.sessionManager;
    if (!sessionManager) return;

    const session = sessionManager.getSessionInGuild(member.guild.id);
    if (!session) return;

    const player = session.players.find(p => p.id === member.id);
    if (!player || !player.alive) return;

    player.alive = false;

    await session.channel.send({
      content: `💀 **<@${member.id}>** غادر السيرفر وتم إعداده كميت.\n_اللعبة مستمرة._`,
    });

    logger.game(`💀 ${member.user.username} غادر السيرفر — تم القتل التلقائي`);

    session.checkWinCondition();
  },
};
