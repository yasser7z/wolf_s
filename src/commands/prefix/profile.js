const UserModel = require('../../database/models/UserModel');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  name: 'حسابي',
  aliases: ['profile', 'pro', 'انا'],
  description: 'عرض معلومات حسابك في اللعبة',
  async execute(message, args, client) {
    const targetId = message.mentions.users.first()?.id || message.author.id;
    const user = await UserModel.getUser(targetId);
    const member = await message.guild.members.fetch(targetId).catch(() => null);

    const winRate = user.gamesPlayed > 0
      ? ((user.wins / user.gamesPlayed) * 100).toFixed(1)
      : '0.0';

    const embed = gameEmbed(
      `👤 حساب ${member?.displayName || 'المستخدم'}`,
      null,
      COLORS.PRIMARY
    );

    embed.setThumbnail(member?.user.displayAvatarURL() || null);
    embed.addFields(
      { name: '🏆 الانتصارات', value: `**${user.wins}**`, inline: true },
      { name: '💔 الهزائم', value: `**${user.losses}**`, inline: true },
      { name: '📊 نسبة الفوز', value: `**${winRate}%**`, inline: true },
      { name: '🎮 الألعاب', value: `**${user.gamesPlayed}**`, inline: true },
      { name: '⭐ المستوى', value: `**${user.level}**`, inline: true },
      { name: '✨ النقاط', value: `**${user.xp} XP**`, inline: true },
    );

    await message.reply({ embeds: [embed] });
  },
};
