const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  name: 'مساعدة',
  aliases: ['help', 'h', 'اوامر'],
  description: 'عرض قائمة الأوامر المتاحة',
  async execute(message, args, client) {
    const prefix = '-';

    const embed = gameEmbed(
      '📖 قائمة الأوامر',
      `**البريفكس:** \`${prefix}\``,
      COLORS.PRIMARY
    );

    const prefixCmds = client.prefixCommands.map(cmd =>
      `\`${prefix}${cmd.name}\` - ${cmd.description || 'لا يوجد وصف'}`
    ).join('\n');

    const slashCmds = client.slashCommands.map(cmd =>
      `\`/${cmd.data.name}\` - ${cmd.data.description || 'لا يوجد وصف'}`
    ).join('\n');

    embed.addFields(
      { name: '🎮 أوامر البريفكس', value: prefixCmds || 'لا توجد أوامر', inline: false },
      { name: '⚡ أوامر السلاش', value: slashCmds || 'لا توجد أوامر', inline: false },
      {
        name: '🌙 عن اللعبة',
        value: 'Vale Community هي لعبة اجتماعية مستوحاة من Wolvesville.\n' +
               'تعاون مع فريقك واكتشف الذئاب قبل فوات الأوان!',
        inline: false,
      }
    );

    await message.reply({ embeds: [embed] });
  },
};
