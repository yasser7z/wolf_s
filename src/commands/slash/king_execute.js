const { SlashCommandBuilder } = require('discord.js');
const { errorEmbed, gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  data: new SlashCommandBuilder()
    .setName('إعدام')
    .setDescription('👑 إعدام لاعب فوراً — استخدم مرة واحدة فقط في اللعبة (الملك فقط)')
    .addUserOption(o => o.setName('لاعب').setDescription('اللاعب الذي تريد إعدامه').setRequired(true)),
  async execute(interaction, client, sessionManager) {
    if (!sessionManager) {
      return interaction.reply({ embeds: [errorEmbed('❌ مدير الجلسات غير متاح!')], ephemeral: true });
    }

    const session = sessionManager.getSessionInGuild(interaction.guildId);
    if (!session) {
      return interaction.reply({ embeds: [errorEmbed('❌ لا توجد جلسة نشطة!')], ephemeral: true });
    }

    const fsm = session.fsm;
    if (!fsm?.is('day')) {
      return interaction.reply({ embeds: [errorEmbed('❌ يمكنك الإعدام فقط خلال مرحلة النهار!')], ephemeral: true });
    }

    const player = session.players.find(p => p.id === interaction.user.id);
    if (!player || !player.alive) {
      return interaction.reply({ embeds: [errorEmbed('💀 أنت ميت ولا يمكنك استخدام هذا الأمر.')], ephemeral: true });
    }

    if (!player.role || player.role.id !== 'King') {
      return interaction.reply({ embeds: [errorEmbed('❌ هذا الأمر مخصص للملك فقط!')], ephemeral: true });
    }

    if (player.role.hasExecuted) {
      return interaction.reply({ embeds: [errorEmbed('❌ لقد استخدمت صلاحية الإعدام مسبقاً!')], ephemeral: true });
    }

    const target = interaction.options.getUser('لاعب');
    const targetPlayer = session.players.find(p => p.id === target.id);

    if (!targetPlayer || !targetPlayer.alive) {
      return interaction.reply({ embeds: [errorEmbed('❌ اللاعب المختار ميت أو غير موجود!')], ephemeral: true });
    }

    if (target.id === player.id) {
      return interaction.reply({ embeds: [errorEmbed('❌ لا يمكنك إعدام نفسك!')], ephemeral: true });
    }

    targetPlayer.alive = false;
    player.role.execute();

    const info = targetPlayer.role?.getInfo();

    await interaction.reply({
      embeds: [gameEmbed(
        '👑 أمر ملكي!',
        `**<@${interaction.user.id}>** أمر بإعدام **<@${target.id}>**!\n📜 **دوره:** ${info ? `${info.emoji} ${info.name}` : '❓'}\n\n_حكم الملك لا يُرد._`,
        COLORS.ERROR
      )],
    });

    // Check win after execution
    session.checkWinCondition();
  },
};
