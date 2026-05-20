const { SlashCommandBuilder } = require('discord.js');
const UserModel = require('../../database/models/UserModel');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('المتصدرين')
    .setDescription('عرض قائمة أفضل اللاعبين'),
  async execute(interaction, client) {
    const leaders = await UserModel.getLeaderboard(10);

    if (leaders.length === 0) {
      return interaction.reply({
        embeds: [gameEmbed('🏆 المتصدرين', 'لا يوجد لاعبون بعد... ابدأ اللعب الآن!', COLORS.WARN)],
      });
    }

    const medals = ['🥇', '🥈', '🥉'];
    const list = leaders.map((user, i) => {
      const medal = medals[i] || `${i + 1}.`;
      return `${medal} <@${user.id}> | 🏆 ${user.wins} فوز | ⭐ ليفل ${user.level} | ✨ ${user.xp} XP`;
    }).join('\n');

    await interaction.reply({
      embeds: [gameEmbed('🏆 قائمة المتصدرين', list, COLORS.PRIMARY)],
    });
  },
};
