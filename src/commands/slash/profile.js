const { SlashCommandBuilder } = require('discord.js');
const UserModel = require('../../database/models/UserModel');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('حسابي')
    .setDescription('عرض معلومات حسابك في اللعبة')
    .addUserOption(option =>
      option.setName('المستخدم')
        .setDescription('المستخدم الذي تريد عرض معلوماته')
    ),
  async execute(interaction, client) {
    const target = interaction.options.getUser('المستخدم') || interaction.user;
    const user = await UserModel.getUser(target.id);

    const winRate = user.gamesPlayed > 0
      ? ((user.wins / user.gamesPlayed) * 100).toFixed(1)
      : '0.0';

    const embed = gameEmbed(
      `👤 حساب ${target.username}`,
      null,
      COLORS.PRIMARY
    );

    embed.setThumbnail(target.displayAvatarURL());
    embed.addFields(
      { name: '🏆 الانتصارات', value: `**${user.wins}**`, inline: true },
      { name: '💔 الهزائم', value: `**${user.losses}**`, inline: true },
      { name: '📊 نسبة الفوز', value: `**${winRate}%**`, inline: true },
      { name: '🎮 الألعاب', value: `**${user.gamesPlayed}**`, inline: true },
      { name: '⭐ المستوى', value: `**${user.level}**`, inline: true },
      { name: '✨ النقاط', value: `**${user.xp} XP**`, inline: true },
    );

    await interaction.reply({ embeds: [embed] });
  },
};
