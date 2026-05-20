const { SlashCommandBuilder } = require('discord.js');
const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('مساعدة')
    .setDescription('عرض قائمة الأوامر المتاحة'),
  async execute(interaction, client) {
    const embed = gameEmbed(
      '📖 قائمة الأوامر',
      '**Vale Community - لعبة اجتماعية خصم**',
      COLORS.PRIMARY
    );

    const prefixCmds = client.prefixCommands.map(cmd =>
      `\`-${cmd.name}\` - ${cmd.description || 'لا يوجد وصف'}`
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

    await interaction.reply({ embeds: [embed] });
  },
};
