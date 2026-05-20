const { gameEmbed, errorEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  name: 'ذيب',
  aliases: ['game', 'play', 'لعبة', 'ابدأ', 'wolf'],
  description: 'فتح صالة انتظار لعبة جديدة في القرية',
  cooldown: 5000,
  async execute(message, args, client, sessionManager) {
    if (!sessionManager) {
      return message.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')] });
    }

    if (sessionManager.hasSessionInGuild(message.guild.id)) {
      return message.reply({ embeds: [errorEmbed('❌ توجد لعبة نشطة بالفعل في هذا السيرفر! أنهِها أولاً بـ \`-هش\`')] });
    }

    if (sessionManager.hasSession(message.channel.id)) {
      return message.reply({ embeds: [errorEmbed('❌ توجد لعبة بالفعل في هذه القناة!')] });
    }

    const session = sessionManager.createSession(message.channel.id, message.guild.id, message.author.id);
    if (!session) {
      return message.reply({ embeds: [errorEmbed('❌ تعذر إنشاء اللعبة!')] });
    }

    await message.reply({
      embeds: [gameEmbed(
        '🐺 ذيب - Vale Community',
        `🏠 **تم فتح صالة انتظار جديدة!**\n\n` +
        `👑 **المضيف:** <@${message.author.id}>\n` +
        `⏱️ **مدة الانضمام:** 60 ثانية\n` +
        `👤 **الحد الأدنى:** 6 لاعبين\n\n` +
        `_انضموا الآن بالضغط على الأزرار أدناه!_`,
        COLORS.LOBBY
      )],
    });

    await session.startLobby();
  },
};
