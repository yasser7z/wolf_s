const { gameEmbed, COLORS } = require('../../utils/embedBuilder');

module.exports = {
  name: 'انسحاب',
  description: 'الانسحاب من اللعبة الحالية — يتم معاملتك كميت.',
  async execute(message, args, client, sessionManager) {
    if (!sessionManager) {
      return message.channel.send('❌ مدير الجلسات غير متاح.');
    }

    const session = sessionManager.getSessionInGuild(message.guild.id);
    if (!session) {
      return message.channel.send('❌ لا توجد جلسة نشطة.');
    }

    const player = session.players.find(p => p.id === message.author.id);
    if (!player) {
      return message.channel.send('❌ أنت لست في اللعبة.');
    }

    if (!player.alive) {
      return message.channel.send('💀 أنت ميت بالفعل.');
    }

    const fsm = session.fsm;
    if (!fsm || fsm.is('idle') || fsm.is('ended') || fsm.is('lobby')) {
      return message.channel.send('❌ يمكنك الانسحاب فقط خلال اللعبة النشطة.');
    }

    player.alive = false;

    await message.channel.send({
      embeds: [gameEmbed(
        '💀 انسحاب',
        `<@${message.author.id}> **انسحب من اللعبة!**\n_تم إعداده كميت._`,
        COLORS.ERROR
      )],
    });

    session.checkWinCondition();
  },
};
