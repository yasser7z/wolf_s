const { ActionRowBuilder, StringSelectMenuBuilder } = require('discord.js');

class NightPanel {
  static wolfPanel(targets) {
    return new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('wolves_kill')
        .setPlaceholder('اختر ضحية لهذه الليلة...')
        .addOptions(targets.map(t => ({
          label: t.username,
          value: t.id,
          emoji: '🐺',
        })))
    );
  }

  static seerPanel(targets) {
    return new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('seer_see')
        .setPlaceholder('اختر لاعباً لكشف حقيقته...')
        .addOptions(targets.map(t => ({
          label: t.username,
          value: t.id,
          emoji: '🔮',
        })))
    );
  }

  static doctorPanel(targets) {
    const options = [
      { label: 'تخطي', value: 'skip', emoji: '⏭️' },
      ...targets.map(t => ({
        label: t.username,
        value: t.id,
        emoji: '💉',
      })),
    ];

    return new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('doctor_heal')
        .setPlaceholder('اختر من تنقذ هذه الليلة...')
        .addOptions(options)
    );
  }
}

module.exports = NightPanel;
