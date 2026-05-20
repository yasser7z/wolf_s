const { ActionRowBuilder, StringSelectMenuBuilder } = require('discord.js');

class VotePanel {
  static buildEmbed(alivePlayers, votes) {
    const tally = {};
    Object.values(votes).forEach(v => { tally[v] = (tally[v] || 0) + 1; });

    let voteList = alivePlayers.map(p =>
      `<@${p.id}>: **${tally[p.id] || 0}** صوت`
    ).join('\n');

    return {
      embeds: [{
        title: '🗳️ التصويت',
        description: `**صوتوا الآن!**\nاختر اللاعب الذي تعتقد أنه **ذئب**.\n_كل لاعب يمكنه التصويت مرة واحدة._\n\n**الأصوات الحالية:**\n${voteList}\n\n⏭️ تخطي: **${tally['skip'] || 0}**`,
        color: 0xF39C12,
        footer: { text: 'Vale Community' },
        timestamp: new Date(),
      }],
    };
  }

  static buildVoteRow(alivePlayers) {
    const options = [
      { label: 'تخطي التصويت', value: 'skip', emoji: '⏭️' },
      ...alivePlayers.map(p => ({
        label: p.username,
        value: p.id,
      })),
    ];

    return new ActionRowBuilder().addComponents(
      new StringSelectMenuBuilder()
        .setCustomId('day_vote')
        .setPlaceholder('صوت على من تظن أنه ذئب...')
        .addOptions(options)
    );
  }
}

module.exports = VotePanel;
