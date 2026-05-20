const { EmbedBuilder } = require('discord.js');

module.exports = {
  name: 'م',
  aliases: ['dev', 'developer', 'مطور', 'المطور'],
  description: 'عرض معلومات المطور',
  cooldown: 10000,
  async execute(message) {
    const embed = new EmbedBuilder()
      .setColor(0x00D4FF)
      .setTitle('⚡ Vale Community')
      .setDescription('**بوت لعبة اجتماعية خصم** مستوحى من Wolvesville و Town of Salem')
      .addFields(
        {
          name: '👤 **المطور**',
          value: '```yaml\nLaaw.q\n```',
          inline: true,
        },
        {
          name: '📸 **إنستغرام**',
          value: '[i7_tp2](https://instagram.com/i7_tp2)',
          inline: true,
        },
        {
          name: '💬 **ديسكورد**',
          value: '```\nLaaw.q\n```',
          inline: true,
        },
        {
          name: '🛠️ **الإصدار**',
          value: '```\nv1.0.0\n```',
          inline: true,
        },
        {
          name: '🌙 **عن البوت**',
          value: '> *Vale Community هي قرية صغيرة تختبئ فيها الذئاب بين الأبرياء...*\n> *استخدم عقلك، اكتشف الخونة، وابقَ على قيد الحياة!*',
          inline: false,
        },
      )
      .setFooter({
        text: 'Vale Community | Made with 💙 by Laaw.q',
        iconURL: message.guild?.iconURL() || undefined,
      })
      .setTimestamp()
      .setThumbnail(message.client.user?.displayAvatarURL() || null);

    await message.reply({ embeds: [embed] });
  },
};
