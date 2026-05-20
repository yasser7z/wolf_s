const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

class Narrator {
  constructor(session) {
    this.session = session;
  }

  nightFall() {
    return gameEmbed(
      '🌙 الليل',
      `**الياب ${this.session.nightCount}**\n\nحل الظلام على قرية فالي...\nالكل نائمون إلا من له دور خاص...\n\n_الذئاب تتحرك في الظلام..._\n_العراف يقرأ الأبراج..._\n_الطبيب يتفقد مرضاه..._`,
      COLORS.NIGHT
    );
  }

  dawn(killed, healed) {
    let text = '🌅 **الفجر يشرق على قرية فالي...**\n\n';
    if (killed) {
      text += `💀 **لقد وجدتم جثة <@${killed.id}> هذا الصباح!**\n`;
      if (killed.role) {
        text += `📜 **دوره كان:** ${killed.role.emoji} **${killed.role.name}**\n`;
      }
    } else {
      const healMsg = healed && healed !== 'skip'
        ? `<@${healed}> تم إنقاذه بواسطة الطبيب!`
        : 'لم يصب أحد بأذى هذه الليلة!';
      text += `✅ **${healMsg}**\n`;
    }
    text += '\n_استعدوا للمناقشة!_';
    return gameEmbed('☀️ الفجر', text, COLORS.DAY);
  }

  dayStart(alivePlayers) {
    const list = alivePlayers.map(p => `<@${p.id}>`).join(', ');
    return gameEmbed(
      '☀️ النهار',
      `**الياب ${this.session.nightCount} - مرحلة المناقشة**\n\n**اللاعبون الأحياء (${alivePlayers.length}):**\n${list}\n\n🗣️ _ناقشوا واقنعوا بعضكم بمن هو الذئب!_`,
      COLORS.DAY
    );
  }

  voteResult(tally, skipCount, mostVoted, tie, totalVotes, alive) {
    let text = `📊 **نتائج التصويت (${totalVotes} صوت):**\n\n`;
    alive.forEach(p => {
      text += `<@${p.id}>: **${tally[p.id] || 0}** أصوات\n`;
    });
    text += `⏭️ تخطي: **${skipCount}**\n\n`;

    if (tie || !mostVoted) {
      text += '⚖️ **تعادل! لا أحد سيتم إعدامه اليوم.**';
    } else {
      const eliminated = this.session.players.find(p => p.id === mostVoted);
      if (eliminated) {
        text += `⚖️ **تم إعدام <@${mostVoted}>!**\n`;
        const info = eliminated.role?.getInfo();
        if (info) text += `📜 **دوره:** ${info.emoji} **${info.name}**\n`;
      }
    }
    return gameEmbed('⚖️ الإعدام', text, COLORS.ERROR);
  }

  gameEnd(winner, players) {
    const emoji = winner === 'القرية' ? '👤' : '🐺';
    const list = players.map(p => {
      const status = p.alive ? '🟢 حي' : '💀 ميت';
      const roleInfo = p.role ? `${p.role.emoji} ${p.role.name}` : '❓';
      return `<@${p.id}> | ${roleInfo} | ${status}`;
    }).join('\n');

    return gameEmbed(
      `${emoji} انتهت اللعبة!`,
      `**الفائزون: ${winner}** 🏆\n\n**اللاعبون:**\n${list}`,
      winner === 'القرية' ? COLORS.SUCCESS : COLORS.ERROR
    );
  }

  roleDM(player) {
    const info = player.role.getInfo();
    return gameEmbed(
      `${info.emoji} دورك: ${info.name}`,
      `**الفريق:** ${info.team}\n**قدرتك:** ${info.description}\n\n_تعاون مع فريقك!_`,
      COLORS.NIGHT
    ).setFooter({ text: 'قرية فالي تراقبك...' });
  }
}

module.exports = Narrator;
