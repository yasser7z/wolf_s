const { SlashCommandBuilder } = require('discord.js');
const { errorEmbed } = require('../../utils/embedBuilder');
const ControlPanel = require('../../game/panels/ControlPanel');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('لوحة_التحكم')
    .setDescription('فتح لوحة التحكم الخاصة بك — عرض دورك، حالتك، وقدراتك'),
  async execute(interaction, client, sessionManager) {
    if (!sessionManager) {
      return interaction.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')], ephemeral: true });
    }

    const session = sessionManager.getSessionInGuild(interaction.guildId);
    const access = await ControlPanel.validateAccess(session, interaction.user.id);

    if (!access.allowed) {
      return interaction.reply({ embeds: [errorEmbed(`❌ ${access.reason}`)], ephemeral: true });
    }

    const panel = new ControlPanel(session, access.player);
    const content = panel.build();

    await interaction.reply({ ...content, ephemeral: true });
  },
};
