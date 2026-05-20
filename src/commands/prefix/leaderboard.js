const UserModel = require('../../database/models/UserModel');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  name: 'المتصدرين',
  aliases: ['leaderboard', 'lb', 'top'],
  description: 'عرض قائمة أفضل اللاعبين',
  async execute(message, args, client) {
    const leaders = await UserModel.getLeaderboard(10);

    if (leaders.length === 0) {
      return message.reply({
        embeds: [gameEmbed('🏆 المتصدرين', 'لا يوجد لاعبون بعد... ابدأ اللعب الآن!', COLORS.WARN)],
      });
    }

    const medals = ['🥇', '🥈', '🥉'];
    const list = leaders.map((user, i) => {
      const medal = medals[i] || `${i + 1}.`;
      return `${medal} <@${user.id}> | 🏆 ${user.wins} فوز | ⭐ ليفل ${user.level} | ✨ ${user.xp} XP`;
    }).join('\n');

    const embed = gameEmbed(
      '🏆 قائمة المتصدرين',
      list,
      COLORS.PRIMARY
    );

    await message.reply({ embeds: [embed] });
  },
};
