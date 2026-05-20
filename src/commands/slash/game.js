const { SlashCommandBuilder } = require('discord.js');
const { gameEmbed, errorEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('ذيب')
    .setDescription('فتح صالة انتظار لعبة جديدة في القرية'),
  async execute(interaction, client, sessionManager) {
    if (!sessionManager) {
      return interaction.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')], ephemeral: true });
    }

    if (sessionManager.hasSessionInGuild(interaction.guildId)) {
      return interaction.reply({ embeds: [errorEmbed('❌ توجد لعبة نشطة في هذا السيرفر! أنهِها أولاً بـ /هش')], ephemeral: true });
    }

    const session = sessionManager.createSession(interaction.channelId, interaction.guildId, interaction.user.id);
    if (!session) {
      return interaction.reply({ embeds: [errorEmbed('❌ تعذر إنشاء اللعبة!')], ephemeral: true });
    }

    await interaction.reply({
      embeds: [gameEmbed(
        '🐺 ذيب - Vale Community',
        `🏠 **تم فتح صالة انتظار جديدة!**\n\n` +
        `👑 **المضيف:** ${interaction.user}\n` +
        `⏱️ **مدة الانضمام:** 60 ثانية\n` +
        `👤 **الحد الأدنى:** 6 لاعبين\n\n` +
        `_انضموا الآن بالضغط على الأزرار!_`,
        COLORS.LOBBY
      )],
    });

    await session.startLobby();
  },
};
