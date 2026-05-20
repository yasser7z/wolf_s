const { SlashCommandBuilder } = require('discord.js');
const { successEmbed, errorEmbed } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('هش')
    .setDescription('إنهاء اللعبة الحالية وإعادة تعيين النظام'),
  async execute(interaction, client, sessionManager) {
    if (!sessionManager) {
      return interaction.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')], ephemeral: true });
    }

    if (!sessionManager.hasSessionInGuild(interaction.guildId)) {
      return interaction.reply({ embeds: [errorEmbed('❌ لا توجد لعبة نشطة في هذا السيرفر!')], ephemeral: true });
    }

    const count = await sessionManager.endGuildSessions(interaction.guildId);

    await interaction.reply({
      embeds: [successEmbed(
        `🛑 **تم إنهاء ${count} لعبة بنجاح!**\n\n` +
        `🧹 تم مسح جميع الجلسات\n` +
        `⏱️ تم إلغاء جميع المؤقتات\n` +
        `🔇 تم إيقاف جميع المستمعين\n` +
        `🗑️ تم حذف ذاكرة اللعبة المؤقتة\n` +
        `✅ أعيد تعيين النظام بأمان`
      )],
    });
  },
};
