const { successEmbed, errorEmbed } = require('../../utils/embedBuilder');

module.exports = {
  name: 'هش',
  aliases: ['stop', 'end', 'قف', 'إلغاء'],
  description: 'إنهاء اللعبة الحالية强制 وإعادة تعيين كل شيء بأمان',
  cooldown: 3000,
  async execute(message, args, client, sessionManager) {
    if (!sessionManager) {
      return message.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')] });
    }

    if (!sessionManager.hasSessionInGuild(message.guild.id)) {
      return message.reply({ embeds: [errorEmbed('❌ لا توجد لعبة نشطة في هذا السيرفر!')] });
    }

    const count = await sessionManager.endGuildSessions(message.guild.id);

    await message.reply({
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
