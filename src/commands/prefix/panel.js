const { errorEmbed } = require('../../utils/embedBuilder');
const ControlPanel = require('../../game/panels/ControlPanel');

module.exports = {
  name: 'لوحة التحكم',
  aliases: ['panel', 'my', 'control', 'حسابي'],
  description: 'فتح لوحة التحكم الخاصة بك لعرض حالتك ودورك وقدراتك',
  cooldown: 3000,
  async execute(message, args, client, sessionManager) {
    if (!sessionManager) {
      return message.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')] });
    }

    const session = sessionManager.getSessionInGuild(message.guild.id);
    const access = await ControlPanel.validateAccess(session, message.author.id);

    if (!access.allowed) {
      return message.reply({ embeds: [errorEmbed(`❌ ${access.reason}`)] });
    }

    const panel = new ControlPanel(session, access.player);
    const content = panel.build();

    await message.reply({ ...content, ephemeral: false });
  },
};
