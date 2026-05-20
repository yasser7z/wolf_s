const { EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle } = require('discord.js');

const NEON_CYAN = 0x00D4FF;
const NEON_PURPLE = 0xBB86FC;
const DARK_BG = 0x0D1117;

class LobbyPanel {
  static buildEmbed(players, maxPlayers, minPlayers, startedAt, phase) {
    const elapsed = Date.now() - startedAt;
    const remaining = Math.max(0, Math.ceil((60000 - elapsed) / 1000));
    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;
    const countdown = remaining > 0 ? `\`${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}\`` : '`00:00`';

    const list = players.length > 0
      ? players.map((p, i) => {
          const isHost = p.id === players[0]?.hostId;
          const crown = p.hostId ? '👑' : '';
          const num = String(i + 1).padStart(2, '0');
          return `\`#${num}\` ${crown} <@${p.id}>`;
        }).join('\n')
      : '> *لا يوجد لاعبون بعد...*';

    const progress = players.length >= minPlayers ? '🟢 **اكتمل**' : `🔴 **${minPlayers - players.length}** لاعبين متبقيين`;

    const embed = new EmbedBuilder()
      .setColor(NEON_CYAN)
      .setTitle('🐺 ذيب — Vale Community')
      .setDescription([
        '```ansi',
        '\u001b[1;36m╔══════════════════════════════╗',
        '\u001b[1;36m║     ⚔️  صَالَةُ الِانْتِظَارِ  ║',
        '\u001b[1;36m╚══════════════════════════════╝',
        '```',
      ].join('\n'))
      .addFields(
        {
          name: '📊 **حالة اللعبة**',
          value: [
            '```',
            `👥 اللاعبون   : ${players.length}/${maxPlayers}`,
            `⬇️ الأدنى      : ${minPlayers} لاعبين`,
            `⏱️ الوقت       : ${countdown}`,
            `🔄 الطور       : ${phase || 'صالة انتظار'}`,
            '```',
          ].join('\n'),
          inline: true,
        },
        {
          name: '📈 **التقدم**',
          value: `\n${progress}\n━━━━━━━━━\n${this._progressBar(players.length, minPlayers, maxPlayers)}`,
          inline: true,
        },
        {
          name: '👥 **قائمة اللاعبين**',
          value: list.length > 1024 ? list.slice(0, 1000) + '\n*...وغيرهم*' : list || '> *القائمة فارغة*',
          inline: false,
        },
        {
          name: '━━━━━━━━━━━━━━━━━━━━',
          value: [
            '> 🌙 **ليلة** — الذئاب تتحرك، العراف يكشف، الطبيب يعالج',
            '> ☀️ **نهار** — ناقش، صوّت، اكشف الذئاب قبل فوات الأوان',
          ].join('\n'),
          inline: false,
        },
      )
      .setFooter({
        text: 'Vale Community • انضم الآن وكن جزءاً من القرية',
        iconURL: 'https://cdn.discordapp.com/emojis/1014392487706435694.webp',
      })
      .setTimestamp();

    return { embeds: [embed] };
  }

  static buildRow(channelId, isInGame, isHost, canStart) {
    const playLabel = isInGame && isHost && canStart ? '▶️ ابدأ اللعبة' : '🎮 العب';
    const playStyle = isInGame && isHost && canStart ? ButtonStyle.Success : ButtonStyle.Primary;
    const playDisabled = isInGame && !(isHost && canStart);

    return new ActionRowBuilder().addComponents(
      new ButtonBuilder()
        .setCustomId(`play_${channelId}`)
        .setLabel(playLabel)
        .setStyle(playStyle)
        .setDisabled(false),
      new ButtonBuilder()
        .setCustomId(`leave_${channelId}`)
        .setLabel('❌ اخرج')
        .setStyle(ButtonStyle.Danger)
        .setDisabled(!isInGame),
      new ButtonBuilder()
        .setCustomId(`explain_${channelId}`)
        .setLabel('📖 شرح اللعبة')
        .setStyle(ButtonStyle.Secondary),
    );
  }

  static _progressBar(current, min, max) {
    const total = 10;
    const filled = Math.round((current / max) * total);
    const minPos = Math.round((min / max) * total);
    const bar = [];
    for (let i = 0; i < total; i++) {
      if (i < filled) {
        if (current >= min && i >= minPos) bar.push('🟢');
        else bar.push('🔵');
      } else {
        bar.push('⬛');
      }
    }
    bar[minPos] = current >= min ? '🟢' : '🔴';
    return bar.join('');
  }

  static buildExplanation() {
    return {
      embeds: [
        new EmbedBuilder()
          .setColor(0xBB86FC)
          .setTitle('📖 شرح لعبة Vale Community')
          .setDescription([
            '```ansi',
            '\u001b[1;35m╔══════════════════════════════════════╗',
            '\u001b[1;35m║     🌙  وَلْكُمْ فِي قَرْيَةِ فَالِي  ║',
            '\u001b[1;35m╚══════════════════════════════════════╝',
            '```',
          ].join('\n'))
          .addFields(
            {
              name: '🎯 **الهدف من اللعبة**',
              value: '> لعبة اجتماعية خصم مقسمة إلى **فريقين**:\n> • **👤 القرية** — تخلصوا من جميع الذئاب\n> • **🐺 الذئاب** — اقضوا على القرويين\n> • **🧙 المحايد** — حسّن فرصك للفوز بمفردك',
              inline: false,
            },
            {
              name: '🌙 **الليل**',
              value: [
                '```md',
                '# في الظلام...',
                '🐺 الذئاب    → تختار ضحية',
                '🔮 العراف    → يكشف حقيقة أحدهم',
                '💉 الطبيب    → ينقذ لاعباً من الموت',
                '🕵️ الجاسوس   → يتجسس على الذئاب',
                '🧙 المشعوذة  → تستخدم جرعاتها',
                '```',
              ].join('\n'),
              inline: true,
            },
            {
              name: '☀️ **النهار**',
              value: [
                '```md',
                '# في الضوء...',
                '🗣️ المناقشة  → تبادل الاتهامات',
                '🗳️ التصويت   → اختر من تظنه ذئباً',
                '⚖️ الإعدام   → يتم إعدام الأكثر تصويتاً',
                '📜 الكشف     → يظهر دور المنعدم',
                '```',
              ].join('\n'),
              inline: true,
            },
            {
              name: '👤 **الأدوار**',
              value: [
                '> **👤 مدني** — ليس لديك قدرة خاصة، ثق بحدسك',
                '> **🐺 ذئب** — كل ليلة اختر ضحية',
                '> **🔮 عراف** — اكتشف حقيقة لاعب كل ليلة',
                '> **💉 طبيب** — أنقذ لاعباً من الموت كل ليلة',
                '> **🕵️ جاسوس** — تعرف على الذئاب',
                '> **🏹 صياد** — إذا مت، خذ أحدهم معك',
                '> **🧙 مشعوذة** — جرعة شفاء وجرعة سم',
              ].join('\n'),
              inline: false,
            },
            {
              name: '🏆 **شروط الفوز**',
              value: [
                '```fix',
                '👤 القرية  : اقضِ على جميع الذئاب',
                '🐺 الذئاب  : تفوق عدداً على القرويين',
                '🧙 محايد   : كن آخر من يبقى',
                '```',
              ].join('\n'),
              inline: false,
            },
            {
              name: '━━━━━━━━━━━━━━━━━━━━',
              value: '> ⚡ **نصائح:** استخدم المنطق، راقب السلوك، تعاون مع فريقك!\n> 🔍 **حاول اكتشاف:** من يتجنب الحديث؟ من يرمي التهم جزافاً؟',
              inline: false,
            },
          )
          .setFooter({
            text: 'Vale Community • Developed by Laaw.q',
            iconURL: 'https://cdn.discordapp.com/emojis/1014392487706435694.webp',
          })
          .setTimestamp()
          .setColor(0x00D4FF),
      ],
      ephemeral: true,
    };
  }
}

module.exports = LobbyPanel;
